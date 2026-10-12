#include "IV/IVPlayerController.h"
#include "IV/IVVillageGenerator.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "EnhancedInputSubsystems.h"
#include "EnhancedPlayerInput.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Pawn.h"
#include "InputCoreTypes.h"

AIVPlayerController::AIVPlayerController()
{
	PrimaryActorTick.bCanEverTick = true;
	bAutoManageActiveCameraTarget = false;      // the view target is the isometric camera, never the pawn's own camera
	bShowMouseCursor = false;
}

void AIVPlayerController::FindGenerator()
{
	if (Gen) return;
	for (TActorIterator<AIVVillageGenerator> It(GetWorld()); It; ++It) { Gen = *It; break; }
}

float AIVPlayerController::IsoYaw() const { return (Gen ? Gen->IsoYaw : 45.f) + YawOffset; }
float AIVPlayerController::IsoPitch() const { return Gen ? Gen->IsoPitch : -35.264f; }

FVector AIVPlayerController::ScreenToWorldDirection(FVector2D S, bool bSnap) const
{
	if (S.IsNearlyZero()) return FVector::ZeroVector;
	float A = FMath::Atan2(S.X, S.Y);                              // 0 = screen up, clockwise
	if (bSnap) A = FMath::RoundToFloat(A / (PI / 4.f)) * (PI / 4.f);
	const float Y = FMath::DegreesToRadians(IsoYaw());
	const FVector Up(FMath::Cos(Y), FMath::Sin(Y), 0.f), Right(-FMath::Sin(Y), FMath::Cos(Y), 0.f);
	return (Up * FMath::Cos(A) + Right * FMath::Sin(A)).GetSafeNormal();
}

void AIVPlayerController::EnsureCamera()
{
	if (IsoCam) return;
	FActorSpawnParameters P; P.Owner = this; P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	IsoCam = GetWorld()->SpawnActor<ACameraActor>(ACameraActor::StaticClass(), FTransform::Identity, P);
	if (!IsoCam) return;
	UCameraComponent* C = IsoCam->GetCameraComponent();
	C->SetProjectionMode(ECameraProjectionMode::Orthographic);
	C->SetOrthoWidth(OrthoWidth);
	C->SetConstraintAspectRatio(false);
	C->bAutoCalculateOrthoPlanes = true;
	SetViewTarget(IsoCam);
}

void AIVPlayerController::UpdateCamera(float Dt, bool bSnap)
{
	EnsureCamera();
	if (!IsoCam) return;
	if (const APawn* P = GetPawn())
	{
		const FVector Want = P->GetActorLocation() + FVector(0, 0, FocusHeight);
		if (bSnap || !bFocusValid || FollowSpeed <= 0.f || FVector::DistSquared(Want, Focus) > FMath::Square(3000.f)) Focus = Want;
		else Focus = FMath::VInterpTo(Focus, Want, Dt, FollowSpeed);
		bFocusValid = true;
	}
	const FRotator R(IsoPitch(), IsoYaw(), 0.f);
	IsoCam->SetActorLocationAndRotation(Focus - R.Vector() * CameraDistance, R);
	IsoCam->GetCameraComponent()->SetOrthoWidth(OrthoWidth);
	if (GetViewTarget() != IsoCam) SetViewTarget(IsoCam);
}

void AIVPlayerController::BeginPlay()
{
	Super::BeginPlay();
	FindGenerator();
	SetIgnoreLookInput(true);
	SetControlRotation(FRotator(0.f, IsoYaw(), 0.f));
	UpdateCamera(0.f, true);
}

void AIVPlayerController::OnPossess(APawn* InPawn)
{
	Super::OnPossess(InPawn);
	FindGenerator();
	SetControlRotation(FRotator(0.f, IsoYaw(), 0.f));
	// her silhouette shows through whatever stands between her and the camera (custom depth + the level's silhouette post process)
	if (ACharacter* Ch = Cast<ACharacter>(InPawn))
		if (USkeletalMeshComponent* M = Ch->GetMesh()) { M->SetRenderCustomDepth(true); M->SetCustomDepthStencilValue(1); }
	ClearMappingsUntil = GetWorld()->GetTimeSeconds() + 2.f;
	bFocusValid = false;
	UpdateCamera(0.f, true);
}

void AIVPlayerController::PlayerTick(float Dt)
{
	Super::PlayerTick(Dt);
	FindGenerator();
	// the template's mapping contexts (camera-relative move, mouse look, jump) come from its own player controller
	// blueprint, which this controller replaces; should the pawn add one itself when possessed, drop it
	if (GetWorld()->GetTimeSeconds() < ClearMappingsUntil)
		if (ULocalPlayer* LP = GetLocalPlayer())
			if (UEnhancedInputLocalPlayerSubsystem* Sub = LP->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>()) Sub->ClearAllMappings();
	SetControlRotation(FRotator(0.f, IsoYaw(), 0.f));

	const bool bMap = Gen && Gen->bMapOpen;
	// ---- map / interact
	const bool bMapKey = WasInputKeyJustPressed(EKeys::M) || WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Top) || WasInputKeyJustPressed(EKeys::Gamepad_Special_Left);
	if (Gen && (bMapKey || (bMap && (WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Right) || WasInputKeyJustPressed(EKeys::Escape))))) Gen->SetMapOpen(!bMap);
	APawn* P = GetPawn();
	if (Gen && P && !bMap && (WasInputKeyJustPressed(EKeys::F) || WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Bottom) || WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Left)))
		Gen->InteractNearest(P->GetActorLocation(), InteractDistance);

	// ---- turning the view: Q / E (LB / RB), one step a press; held, it keeps turning
	{
		const bool bLeft = IsInputKeyDown(EKeys::Q) || IsInputKeyDown(EKeys::Gamepad_LeftShoulder), bRight = IsInputKeyDown(EKeys::E) || IsInputKeyDown(EKeys::Gamepad_RightShoulder);
		int32 Turn = 0;
		if (WasInputKeyJustPressed(EKeys::Q) || WasInputKeyJustPressed(EKeys::Gamepad_LeftShoulder)) ++Turn;
		if (WasInputKeyJustPressed(EKeys::E) || WasInputKeyJustPressed(EKeys::Gamepad_RightShoulder)) --Turn;
		if (bLeft != bRight)
		{
			TurnHold += Dt;
			if (Turn == 0 && TurnHold > 0.35f && !IsViewTurning()) Turn = bLeft ? 1 : -1;
		}
		else TurnHold = 0.f;
		if (Turn != 0) RotateView(Turn);
		YawOffset = FMath::FInterpConstantTo(YawOffset, TargetYawOffset, Dt, RotateSpeed);
		if (FMath::Abs(YawOffset) > 360.f && FMath::Abs(TargetYawOffset) > 360.f) { const float K = FMath::Sign(YawOffset) * 360.f; YawOffset -= K; TargetYawOffset -= K; }
		if (Gen) Gen->SetViewYawOffset(YawOffset);
		SetControlRotation(FRotator(0.f, IsoYaw(), 0.f));
	}

	// ---- zoom (the big map zooms instead while it is open)
	float Zoom = 0.f;
	if (WasInputKeyJustPressed(EKeys::MouseScrollUp) || WasInputKeyJustPressed(EKeys::Equals)) Zoom -= 1.f;
	if (WasInputKeyJustPressed(EKeys::MouseScrollDown) || WasInputKeyJustPressed(EKeys::Hyphen)) Zoom += 1.f;
	const float RY = GetInputAnalogKeyState(EKeys::Gamepad_RightY);
	if (FMath::Abs(RY) > 0.35f) Zoom -= RY * Dt * 4.f;
	if (Zoom != 0.f)
	{
		if (bMap) Gen->MapZoom = FMath::Clamp(Gen->MapZoom * FMath::Pow(1.18f, -Zoom), 0.4f, 6.f);
		else OrthoWidth = FMath::Clamp(OrthoWidth * FMath::Pow(1.12f, Zoom), MinOrthoWidth, MaxOrthoWidth);
	}

	// ---- movement: keyboard (8 directions by nature) or the left stick / D-pad (snapped to 8 directions)
	FVector2D Key(0, 0);
	if (IsInputKeyDown(EKeys::W) || IsInputKeyDown(EKeys::Up)) Key.Y += 1.f;
	if (IsInputKeyDown(EKeys::S) || IsInputKeyDown(EKeys::Down)) Key.Y -= 1.f;
	if (IsInputKeyDown(EKeys::D) || IsInputKeyDown(EKeys::Right)) Key.X += 1.f;
	if (IsInputKeyDown(EKeys::A) || IsInputKeyDown(EKeys::Left)) Key.X -= 1.f;
	FVector2D Pad(0, 0);
	if (IsInputKeyDown(EKeys::Gamepad_DPad_Up)) Pad.Y += 1.f;
	if (IsInputKeyDown(EKeys::Gamepad_DPad_Down)) Pad.Y -= 1.f;
	if (IsInputKeyDown(EKeys::Gamepad_DPad_Right)) Pad.X += 1.f;
	if (IsInputKeyDown(EKeys::Gamepad_DPad_Left)) Pad.X -= 1.f;
	const FVector2D Stick = ScriptedStick.IsNearlyZero() ? FVector2D(GetInputAnalogKeyState(EKeys::Gamepad_LeftX), GetInputAnalogKeyState(EKeys::Gamepad_LeftY)) : ScriptedStick;
	FVector2D Move(0, 0); float Scale = 1.f;
	const bool bWalkKey = IsInputKeyDown(EKeys::LeftShift) || IsInputKeyDown(EKeys::RightShift) || GetInputAnalogKeyState(EKeys::Gamepad_LeftTriggerAxis) > 0.5f;
	if (!ScriptedMove.IsNearlyZero()) { Move = ScriptedMove; Scale = bScriptedWalk ? WalkScale : 1.f; }
	else if (!Key.IsNearlyZero()) { Move = Key; Scale = bWalkKey ? WalkScale : 1.f; bGamepad = false; }
	else if (!Pad.IsNearlyZero()) { Move = Pad; Scale = bWalkKey ? WalkScale : 1.f; bGamepad = true; }
	else if (Stick.Size() > StickDeadZone) { Move = Stick; Scale = (bWalkKey || Stick.Size() < StickRunThreshold) ? WalkScale : 1.f; bGamepad = true; }
	if (IsInputKeyDown(EKeys::Gamepad_FaceButton_Bottom) || IsInputKeyDown(EKeys::Gamepad_FaceButton_Top) || IsInputKeyDown(EKeys::Gamepad_LeftShoulder) || IsInputKeyDown(EKeys::Gamepad_RightShoulder)
		|| FMath::Abs(RY) > 0.35f) bGamepad = true;
	else if (IsInputKeyDown(EKeys::Q) || IsInputKeyDown(EKeys::E)) bGamepad = false;
	MoveDirIndex = -1; MoveScale = 0.f;
	if (P && !bMap && !Move.IsNearlyZero())
	{
		const float A = FMath::Atan2(Move.X, Move.Y);
		MoveDirIndex = ((FMath::RoundToInt(A / (PI / 4.f)) % 8) + 8) % 8;
		MoveScale = Scale;
		P->AddMovementInput(ScreenToWorldDirection(Move, true), Scale);
	}
	UpdateCamera(Dt, false);
}
