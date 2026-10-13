#include "SS/SSPlayerController.h"
#include "SS/SSFighter.h"
#include "SS/SSArena.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/PlayerInput.h"
#include "InputCoreTypes.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "UnrealClient.h"

ASSPlayerController::ASSPlayerController()
{
	PrimaryActorTick.bCanEverTick = true;
	bShowMouseCursor = false;
}

void ASSPlayerController::BeginPlay()
{
	Super::BeginPlay();
	SetInputMode(FInputModeGameOnly());
	SetIgnoreLookInput(true);
	if (FParse::Value(FCommandLine::Get(), TEXT("SSSelfTest="), SelfTestSeconds) && SelfTestSeconds > 0.f)
	{
		bScriptedOnly = true;
		if (!FParse::Value(FCommandLine::Get(), TEXT("SSSelfTestOut="), SelfTestDir)) SelfTestDir = FPaths::ProjectSavedDir() / TEXT("SelfTest");
		SelfTestDir = FPaths::ConvertRelativePathToFull(SelfTestDir);
	}
}

void ASSPlayerController::TickSelfTest(ASSFighter* F, float Dt)
{
	SelfTestTime += Dt; ++SelfTestFrames;
	// straight on from the start goes through the first two gates: throttle up, then the cannons
	KeyW = SelfTestTime > 1.f; BtnLeft = SelfTestTime > 2.f;
	if (SelfTestStage == 0 && SelfTestTime >= SelfTestSeconds)
	{
		SelfTestStage = 1;
		const ASSArena* A = F->GetArena();
		FVector2D View(0.f, 0.f);
		if (GEngine && GEngine->GameViewport) GEngine->GameViewport->GetViewportSize(View);
		const FVector L = F->GetActorLocation();
		FString R = FString::Printf(TEXT("level %s\nseconds %.2f\nframes %d\nfps %.1f\nview %.0f x %.0f\nfighter %.0f %.0f %.0f\nspeed %.0f\nthrottle %.2f\nhull %.0f\nshots %d\nhits %d\ncollisions %d\n"),
			*GetWorld()->GetMapName(), SelfTestTime, SelfTestFrames, SelfTestFrames / FMath::Max(SelfTestTime, 0.001f), View.X, View.Y, L.X, L.Y, L.Z, F->GetSpeed(), F->GetThrottle(), F->GetHull(),
			F->ShotsFired, F->ShotsHit, F->Collisions);
		if (A) R += FString::Printf(TEXT("asteroids %d\ndrones %d\ncontainers %d\nscore %d\n"), A->CountTargets(ESSTargetKind::Asteroid), A->CountTargets(ESSTargetKind::Drone), A->CountTargets(ESSTargetKind::Container), A->Score);
		else R += TEXT("arena missing\n");
		FFileHelper::SaveStringToFile(R, *(SelfTestDir / TEXT("selftest.txt")));
		FScreenshotRequest::RequestScreenshot(SelfTestDir / TEXT("selftest.png"), true, false);
	}
	if (SelfTestStage == 1 && SelfTestTime >= SelfTestSeconds + 2.f) { SelfTestStage = 2; FPlatformMisc::RequestExit(false); }
}

void ASSPlayerController::ClearScripted()
{
	KeyW = KeyS = KeyA = KeyD = KeyShift = BtnLeft = BtnRight = PadA = false;
	ScriptedMouse = ScriptedCounts = PadLeft = PadRight = FVector2D::ZeroVector;
	PadLT = PadRT = 0.f;
}

float ASSPlayerController::Stick(float V) const
{
	// dead zone, then a curve that leaves fine control near the middle
	const float A = FMath::Abs(V);
	if (A <= StickDeadZone) return 0.f;
	const float U = (A - StickDeadZone) / (1.f - StickDeadZone);
	return FMath::Sign(V) * U * (0.45f + 0.55f * U);
}

void ASSPlayerController::PlayerTick(float Dt)
{
	Super::PlayerTick(Dt);
	ASSFighter* F = Cast<ASSFighter>(GetPawn());
	if (!F) return;
	if (SelfTestSeconds > 0.f) TickSelfTest(F, Dt);

	// ---- keyboard and mouse
	float Thr = 0.f, Roll = 0.f;
	if (KeyW || Down(EKeys::W) || Down(EKeys::Up)) Thr += 1.f;
	if (KeyS || Down(EKeys::S) || Down(EKeys::Down)) Thr -= 1.f;
	if (KeyD || Down(EKeys::D) || Down(EKeys::Right)) Roll += 1.f;
	if (KeyA || Down(EKeys::A) || Down(EKeys::Left)) Roll -= 1.f;
	bool bBoost = KeyShift || Down(EKeys::LeftShift) || Down(EKeys::RightShift);
	bool bFire = BtnLeft || Down(EKeys::LeftMouseButton) || Down(EKeys::SpaceBar);
	bool bMissile = BtnRight || Down(EKeys::RightMouseButton) || Down(EKeys::LeftControl) || Down(EKeys::RightControl);
	float Mx = 0.f, My = 0.f;
	// (raw counts, not GetInputMouseDelta: that is scaled by the axis sensitivity and by the field of view)
	if (!bScriptedOnly && PlayerInput) { Mx = PlayerInput->GetRawKeyValue(EKeys::MouseX); My = PlayerInput->GetRawKeyValue(EKeys::MouseY); }
	Mx += ScriptedMouse.X * Dt + ScriptedCounts.X; My += ScriptedMouse.Y * Dt + ScriptedCounts.Y;
	ScriptedCounts = FVector2D::ZeroVector;
	const bool bKeys = Thr != 0.f || Roll != 0.f || bBoost || bFire || bMissile || Mx != 0.f || My != 0.f;

	// ---- Xbox controller: the same layout on the sticks
	const FVector2D Ls(Stick(PadLeft.X + Axis(EKeys::Gamepad_LeftX)), Stick(PadLeft.Y + Axis(EKeys::Gamepad_LeftY)));
	const FVector2D Rs(Stick(PadRight.X + Axis(EKeys::Gamepad_RightX)), Stick(PadRight.Y + Axis(EKeys::Gamepad_RightY)));
	const float Lt = FMath::Max(PadLT, Axis(EKeys::Gamepad_LeftTriggerAxis)), Rt = FMath::Max(PadRT, Axis(EKeys::Gamepad_RightTriggerAxis));
	const bool bPadBoost = PadA || Down(EKeys::Gamepad_FaceButton_Bottom) || Down(EKeys::Gamepad_LeftThumbstick);
	const bool bPadMissile = Lt > 0.5f || Down(EKeys::Gamepad_RightShoulder);
	const bool bPad = !Ls.IsNearlyZero() || !Rs.IsNearlyZero() || Lt > 0.3f || Rt > 0.3f || bPadBoost || bPadMissile || Down(EKeys::Gamepad_FaceButton_Top)
		|| Down(EKeys::Gamepad_DPad_Up) || Down(EKeys::Gamepad_DPad_Down);
	if (bPad) bGamepad = true; else if (bKeys) bGamepad = false;
	Thr = FMath::Clamp(Thr + Ls.Y, -1.f, 1.f);
	Roll = FMath::Clamp(Roll + Ls.X, -1.f, 1.f);
	bBoost |= bPadBoost; bFire |= Rt > 0.3f; bMissile |= bPadMissile;

	const float Inv = bInvertPitch ? -1.f : 1.f;
	F->SetFlightInput(Thr, Roll, bBoost);
	F->SetTurnInput(Rs.Y * Inv, Rs.X);
	if (Mx != 0.f || My != 0.f) F->AddAim(Mx * MouseSensitivity * MouseScale, My * MouseSensitivity * MouseScale * Inv);
	F->SetFiring(bFire);
	if (bMissile) F->FireMissile();          // (held: one missile every MissileInterval)

	// ---- the rest
	if (Pressed(EKeys::Tab) || Pressed(EKeys::T) || Pressed(EKeys::Gamepad_FaceButton_Top)) F->CycleTarget();
	float Zoom = 0.f;
	if (Pressed(EKeys::MouseScrollUp)) Zoom -= 1.f;
	if (Pressed(EKeys::MouseScrollDown)) Zoom += 1.f;
	if (Down(EKeys::Gamepad_DPad_Up)) Zoom -= Dt * 4.f;
	if (Down(EKeys::Gamepad_DPad_Down)) Zoom += Dt * 4.f;
	if (Zoom != 0.f) F->ZoomCamera(Zoom);
	const float Sens = (Pressed(EKeys::RightBracket) ? 1.f : 0.f) - (Pressed(EKeys::LeftBracket) ? 1.f : 0.f);
	if (Sens != 0.f)
	{
		MouseScale = FMath::Clamp(MouseScale * FMath::Pow(1.2f, Sens), MouseScaleRange.X, MouseScaleRange.Y);
		MouseNoteUntil = GetWorld()->GetTimeSeconds() + 2.f;
	}
	if (Pressed(EKeys::Escape)) UKismetSystemLibrary::QuitGame(this, this, EQuitPreference::Quit, false);
	if (Pressed(EKeys::I)) bInvertPitch = !bInvertPitch;
	if (Pressed(EKeys::H) || Pressed(EKeys::F1) || Pressed(EKeys::Gamepad_Special_Right)) bShowHelp = !bShowHelp;
	if ((Pressed(EKeys::R) || Pressed(EKeys::Gamepad_Special_Left)) && !F->IsDestroyed()) F->Respawn();
}
