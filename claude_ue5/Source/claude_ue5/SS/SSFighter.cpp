#include "SS/SSFighter.h"
#include "SS/SSArena.h"
#include "SS/SSMissile.h"
#include "SS/SSTarget.h"
#include "Camera/CameraComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Camera/PlayerCameraManager.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Particles/ParticleSystem.h"
#include "Particles/ParticleSystemComponent.h"

static const FName SSPartTag(TEXT("SSPart"));

ASSFighter::ASSFighter()
{
	PrimaryActorTick.bCanEverTick = true;
	Hull = CreateDefaultSubobject<USphereComponent>(TEXT("Hull"));
	RootComponent = Hull;
	Hull->InitSphereRadius(330.f);
	// it finds what it flies into itself (a sweep against the detailed collision of the pack meshes)
	Hull->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Hull->SetGenerateOverlapEvents(false);
	Visual = CreateDefaultSubobject<USceneComponent>(TEXT("Visual"));
	Visual->SetupAttachment(Hull);
	Arm = CreateDefaultSubobject<USpringArmComponent>(TEXT("Arm"));
	Arm->SetupAttachment(Hull);
	Arm->bDoCollisionTest = false;
	Arm->bUsePawnControlRotation = false;
	Arm->bInheritPitch = Arm->bInheritYaw = Arm->bInheritRoll = true;
	Arm->bEnableCameraLag = true; Arm->CameraLagSpeed = 14.f; Arm->CameraLagMaxDistance = 650.f;
	Arm->bEnableCameraRotationLag = true; Arm->CameraRotationLagSpeed = CameraTurnLag;
	Arm->TargetArmLength = CameraDistance; Arm->SocketOffset = FVector(0.f, 0.f, CameraHeight);
	Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
	Camera->SetupAttachment(Arm, USpringArmComponent::SocketName);
	Camera->SetFieldOfView(BaseFOV);
	Bolts = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Bolts"));
	Bolts->SetupAttachment(Hull);
	Bolts->SetUsingAbsoluteLocation(true); Bolts->SetUsingAbsoluteRotation(true); Bolts->SetUsingAbsoluteScale(true);
	Bolts->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Bolts->SetCastShadow(false);
	Bolts->SetGenerateOverlapEvents(false);
	Dust = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Dust"));
	Dust->SetupAttachment(Hull);
	Dust->SetUsingAbsoluteLocation(true); Dust->SetUsingAbsoluteRotation(true); Dust->SetUsingAbsoluteScale(true);
	Dust->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Dust->SetCastShadow(false);
	Dust->SetGenerateOverlapEvents(false);
	EngineLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("EngineLight"));
	EngineLight->SetupAttachment(Visual);
	EngineLight->SetRelativeLocation(FVector(-560.f, 0.f, 40.f));
	EngineLight->SetCastShadows(false);
	EngineLight->SetIntensityUnits(ELightUnits::Candelas);
	EngineLight->SetLightColor(FLinearColor(0.35f, 0.62f, 1.f));
	EngineLight->SetAttenuationRadius(2600.f);
	MuzzleLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("MuzzleLight"));
	MuzzleLight->SetupAttachment(Visual);
	MuzzleLight->SetRelativeLocation(FVector(420.f, 0.f, 30.f));
	MuzzleLight->SetCastShadows(false);
	MuzzleLight->SetIntensityUnits(ELightUnits::Candelas);
	MuzzleLight->SetLightColor(FLinearColor(1.f, 0.45f, 0.2f));
	MuzzleLight->SetAttenuationRadius(2200.f);
	MuzzleLight->SetIntensity(0.f);
	AutoPossessPlayer = EAutoReceiveInput::Player0;
}

void ASSFighter::RebuildParts(bool bConstruction)
{
	TArray<UStaticMeshComponent*> Old;
	GetComponents(Old);
	for (UStaticMeshComponent* C : Old) if (C && C->ComponentHasTag(SSPartTag)) C->DestroyComponent();
	PartComps.Reset(); FlameScale.Reset();
	for (const FSSPart& P : Parts)
	{
		UStaticMeshComponent* C = nullptr;
		if (P.Mesh)
		{
			C = NewObject<UStaticMeshComponent>(this);
			C->ComponentTags.Add(SSPartTag);
			if (bConstruction) C->CreationMethod = EComponentCreationMethod::UserConstructionScript;
			C->SetMobility(EComponentMobility::Movable);
			C->SetupAttachment(Visual);
			C->SetStaticMesh(P.Mesh);
			C->SetRelativeTransform(P.Transform);
			C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			C->SetGenerateOverlapEvents(false);
			if (P.bFlame) C->SetCastShadow(false);
			if (P.Material) for (int32 I = 0; I < C->GetNumMaterials(); ++I) C->SetMaterial(I, P.Material);
			C->RegisterComponent();
		}
		PartComps.Add(C);
		FlameScale.Add(P.Transform.GetScale3D());
	}
}

void ASSFighter::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	Hull->SetSphereRadius(HullRadius);
	Arm->TargetArmLength = CameraDistance; Arm->SocketOffset = FVector(0.f, 0.f, CameraHeight);
	Camera->SetFieldOfView(BaseFOV);
	RebuildParts(true);
}

void ASSFighter::BeginPlay()
{
	Super::BeginPlay();
	for (TActorIterator<ASSArena> It(GetWorld()); It; ++It) { Arena = *It; break; }
	StartTransform = GetActorTransform();
	RebuildParts(false);
	RailReload.Init(0.f, MissileRails.Num());
	HullPoints = MaxHull;
	Throttle = StartThrottle;
	LaunchTime = GetWorld()->GetTimeSeconds();
	Velocity = GetActorForwardVector() * (Throttle * MaxSpeed);
	if (BoltMesh) Bolts->SetStaticMesh(BoltMesh);
	if (BoltMaterial) Bolts->SetMaterial(0, BoltMaterial);
	Bolts->SetWorldTransform(FTransform::Identity);
	Dust->SetWorldTransform(FTransform::Identity);
	DustPos.Reset();
	if (BoltMesh && BoltMaterial && DustCount > 0)
	{
		Dust->SetStaticMesh(BoltMesh);
		UMaterialInstanceDynamic* M = UMaterialInstanceDynamic::Create(BoltMaterial, this);
		M->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.55f, 0.66f, 0.85f));
		M->SetScalarParameterValue(TEXT("Glow"), 1.6f);
		Dust->SetMaterial(0, M);
		FRandomStream Rs(771);
		const FVector L0 = GetActorLocation();
		for (int32 I = 0; I < DustCount; ++I) DustPos.Add(L0 + FVector(Rs.FRandRange(-1.f, 1.f), Rs.FRandRange(-1.f, 1.f), Rs.FRandRange(-1.f, 1.f)) * DustRange);
	}
	Contrails.Reset();
	for (const FVector& T : Thrusters)
	{
		if (ThrusterFX)
			if (UNiagaraComponent* C = UNiagaraFunctionLibrary::SpawnSystemAttached(ThrusterFX, Visual, NAME_None, T, ThrusterFXRotation, ThrusterFXScale, EAttachLocation::KeepRelativeOffset, false,
				ENCPoolMethod::None, true))
				Contrails.Add(C);
		if (ThrusterPS)
			if (UParticleSystemComponent* C = UGameplayStatics::SpawnEmitterAttached(ThrusterPS, Visual, NAME_None, T, ThrusterFXRotation, ThrusterFXScale, EAttachLocation::KeepRelativeOffset, false))
				Contrails.Add(C);
	}
	UE_LOG(LogStarship, Log, TEXT("SSFIGHTER play: %d parts, %d cannons, %d missile rails, %d contrails, arena %s"), Parts.Num(), CannonMuzzles.Num(), MissileRails.Num(), Contrails.Num(),
		Arena ? TEXT("found") : TEXT("missing"));
}

void ASSFighter::SetFlightInput(float ThrottleAxis, float Roll, bool bBoost)
{
	InThrottle = FMath::Clamp(ThrottleAxis, -1.f, 1.f); InRoll = FMath::Clamp(Roll, -1.f, 1.f); bBoosting = bBoost;
}

void ASSFighter::SetTurnInput(float Pitch, float Yaw)
{
	InPitch = FMath::Clamp(Pitch, -1.f, 1.f); InYaw = FMath::Clamp(Yaw, -1.f, 1.f);
}

void ASSFighter::AddAim(float YawDegrees, float PitchDegrees)
{
	if (bReturning || DeadTime > 0.f) return;
	Aim += FVector2D(YawDegrees, PitchDegrees);
	const float L = Aim.Size();
	if (L > MaxAim) Aim *= MaxAim / L;
}

FVector ASSFighter::GetAimDirection() const
{
	return GetActorTransform().TransformVectorNoScale(FRotator(Aim.Y, Aim.X, 0.f).Vector());
}

FVector ASSFighter::GetLeadPoint() const
{
	const FVector L = GetActorLocation();
	const ASSTarget* T = Locked.Get();
	if (!T) return L + GetActorForwardVector() * Convergence;
	// (in the fighter's frame the bolts leave at BoltSpeed and the target moves at its velocity less the fighter's)
	const FVector Rel = T->GetVelocity() - Velocity;
	FVector P = T->GetActorLocation();
	for (int32 I = 0; I < 3; ++I) P = T->GetActorLocation() + Rel * (FVector::Dist(P, L) / FMath::Max(BoltSpeed, 1.f));
	return P;
}

int32 ASSFighter::GetMissilesReady() const
{
	int32 N = 0;
	for (float R : RailReload) if (R <= 0.f) ++N;
	return N;
}

float ASSFighter::GetMissileReloadLeft() const
{
	float Best = 0.f;
	for (float R : RailReload) if (R > 0.f && (Best <= 0.f || R < Best)) Best = R;
	return Best;
}

void ASSFighter::ZoomCamera(float Steps)
{
	CameraDistance = FMath::Clamp(CameraDistance * FMath::Pow(1.15f, Steps), CameraDistanceRange.X, CameraDistanceRange.Y);
}

void ASSFighter::SetChaseCamera(FRotator Orbit, float Distance, float Height)
{
	CameraOrbit = Orbit;
	if (Distance > 0.f) CameraDistance = Distance;
	if (Height > 0.f) CameraHeight = Height;
}

void ASSFighter::SetWatchCamera(bool bOn, FVector Point, float FOV, float Lead)
{
	if (bOn != bWatchCamera || (bOn && !Point.Equals(WatchPoint, 1.f))) bCameraCut = true;
	if (bWatchCamera && !bOn) bSnapCamera = true;
	bWatchCamera = bOn; WatchPoint = Point; WatchFOV = FOV; WatchLead = Lead;
}

void ASSFighter::CalcCamera(float DeltaTime, FMinimalViewInfo& OutResult)
{
	Super::CalcCamera(DeltaTime, OutResult);
	if (bWatchCamera)
	{
		OutResult.Location = WatchPoint;
		OutResult.Rotation = (GetActorLocation() + Velocity * WatchLead - WatchPoint).Rotation();
		OutResult.FOV = WatchFOV;
	}
}

void ASSFighter::CycleTarget()
{
	if (!Arena) return;
	if (ASSTarget* T = Arena->PickTarget(GetActorLocation(), GetActorForwardVector(), 50.f, LockRange, Locked.Get()))
	{
		Locked = T; bManualLock = true;
	}
}

bool ASSFighter::FireMissile()
{
	if (DeadTime > 0.f || MissileTimer > 0.f || MissileRails.Num() == 0 || RailReload.Num() != MissileRails.Num()) return false;
	int32 Rail = -1;
	for (int32 K = 0; K < MissileRails.Num(); ++K)
	{
		const int32 I = (NextRail + K) % MissileRails.Num();
		if (RailReload[I] <= 0.f) { Rail = I; break; }
	}
	if (Rail < 0) return false;
	NextRail = Rail + 1;
	const FTransform Tr = GetActorTransform();
	FActorSpawnParameters P; P.Owner = this; P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ASSMissile* M = GetWorld()->SpawnActor<ASSMissile>(ASSMissile::StaticClass(), FTransform(Tr.GetRotation(), Tr.TransformPositionNoScale(MissileRails[Rail])), P);
	if (!M) return false;
	if (MissileMesh) { M->Mesh->SetStaticMesh(MissileMesh); M->Mesh->SetRelativeTransform(MissileMeshTransform); }
	if (MissileFlameMesh) { M->Flame->SetStaticMesh(MissileFlameMesh); M->Flame->SetRelativeTransform(MissileFlameTransform); }
	if (MissileTrailFX) M->Trail->SetAsset(MissileTrailFX);
	if (MissileTrailPS) M->TrailPS->SetTemplate(MissileTrailPS);
	// it drops off the rail and lights up
	M->Launch(Arena, this, Locked.Get(), Velocity + Tr.GetUnitAxis(EAxis::X) * 2500.f - Tr.GetUnitAxis(EAxis::Z) * 500.f, MissileDamage, MissileBlastRadius);
	RailReload[Rail] = MissileReload;
	MissileTimer = MissileInterval;
	++MissilesFired;
	return true;
}

void ASSFighter::TakeHullDamage(float Damage, const FVector& At)
{
	const float Now = GetWorld()->GetTimeSeconds();
	if (Now - LastDamageTime < 0.25f || DeadTime > 0.f) return;
	LastDamageTime = Now;
	if (Now - LaunchTime < LaunchProtection) return;
	HullPoints -= Damage;
	Shake = 1.f;
	if (HullPoints <= 0.f) Explode();
}

void ASSFighter::Explode()
{
	HullPoints = 0.f;
	if (Arena) Arena->Blast(GetActorLocation(), 1500.f, FLinearColor(1.f, 0.6f, 0.25f));
	Visual->SetVisibility(false, true);
	for (UFXSystemComponent* C : Contrails) if (C) C->Deactivate();
	Velocity = FVector::ZeroVector;
	bFiring = false;
	DeadTime = 2.8f;
}

void ASSFighter::Respawn()
{
	SetActorTransform(StartTransform, false, nullptr, ETeleportType::TeleportPhysics);
	HullPoints = MaxHull;
	Throttle = StartThrottle;
	Velocity = GetActorForwardVector() * (Throttle * MaxSpeed);
	Aim = FVector2D::ZeroVector; RatePitch = RateYaw = RateRoll = 0.f; Bank = 0.f; Knock = 0.f; MouseFlight = 0.f;
	bReturning = false; DeadTime = 0.f;
	LaunchTime = GetWorld()->GetTimeSeconds();
	for (float& R : RailReload) R = 0.f;
	Visual->SetVisibility(true, true);
	for (UFXSystemComponent* C : Contrails) if (C) C->Activate(true);
	++Respawns;
}

void ASSFighter::Relaunch(float AtThrottle)
{
	Respawn();
	Throttle = FMath::Clamp(AtThrottle, 0.f, 1.f);
	Velocity = GetActorForwardVector() * (Throttle * MaxSpeed);
	BoltList.Reset(); Locked = nullptr; bManualLock = false;
	CannonTimer = MissileTimer = LockTimer = 0.f; NextMuzzle = NextRail = 0;
	ShotsFired = ShotsHit = MissilesFired = Collisions = Respawns = TurnBacks = 0;
	LastDamageTime = -100.f; Shake = MuzzleFlash = 0.f;
	InThrottle = InRoll = InPitch = InYaw = 0.f; bBoosting = bFiring = false;
}

void ASSFighter::Tick(float Dt)
{
	Super::Tick(Dt);
	if (DeadTime > 0.f)
	{
		DeadTime -= Dt;
		UpdateBolts(Dt);
		if (DeadTime <= 0.f) Respawn();
		return;
	}
	UpdateFlight(Dt);
	UpdateWeapons(Dt);
	UpdateBolts(Dt);
	UpdateLook(Dt);
}

void ASSFighter::UpdateFlight(float Dt)
{
	const FVector L = GetActorLocation();
	Throttle = FMath::Clamp(Throttle + InThrottle * ThrottleRate * Dt, 0.f, 1.f);

	// ---- where the nose goes
	float PitchCmd = 0.f, YawCmd = 0.f;
	if (Arena)
	{
		if (!bReturning && Arena->DistanceOutside(L) > 0.f) { bReturning = true; ++TurnBacks; Aim = FVector2D::ZeroVector; }
		else if (bReturning && Arena->IsInside(L, 8000.f) && FVector::DotProduct(GetActorForwardVector(), (Arena->GetActorLocation() - L).GetSafeNormal()) > 0.6f) bReturning = false;
	}
	if (bReturning)
	{
		// out of the arena: the nose is brought round to its middle
		const FVector Want = GetActorTransform().InverseTransformVectorNoScale((Arena->GetActorLocation() - L).GetSafeNormal());
		float YawErr = FMath::RadiansToDegrees(FMath::Atan2(Want.Y, Want.X));
		const float PitchErr = FMath::RadiansToDegrees(FMath::Atan2(Want.Z, FMath::Sqrt(Want.X * Want.X + Want.Y * Want.Y)));
		YawCmd = FMath::Clamp(YawErr * 3.f, -YawRate * 1.3f, YawRate * 1.3f);
		PitchCmd = FMath::Clamp(PitchErr * 3.f, -PitchRate * 1.3f, PitchRate * 1.3f);
		Throttle = FMath::Max(Throttle, 0.45f);
	}
	else
	{
		// the mouse's aim point is closed at the mouse rates, the stick asks for a fraction of its own
		const float MaxYaw = FMath::Max(YawRate, MouseYawRate), MaxPitch = FMath::Max(PitchRate, MousePitchRate);
		YawCmd = FMath::Clamp(FMath::Clamp(Aim.X * AimGain, -MouseYawRate, MouseYawRate) + InYaw * YawRate, -MaxYaw, MaxYaw);
		PitchCmd = FMath::Clamp(FMath::Clamp(Aim.Y * AimGain, -MousePitchRate, MousePitchRate) + InPitch * PitchRate, -MaxPitch, MaxPitch);
	}
	// flown by mouse while there is an aim point to close, and for a moment after
	MouseFlight = (!bReturning && Aim.SizeSquared() > 0.01f) ? 1.f : FMath::Max(0.f, MouseFlight - Dt * 2.5f);
	const float Response = FMath::Lerp(TurnResponse, MouseTurnResponse, MouseFlight);
	RateYaw = FMath::FInterpTo(RateYaw, YawCmd, Dt, Response);
	RatePitch = FMath::FInterpTo(RatePitch, PitchCmd, Dt, Response);
	RateRoll = FMath::FInterpTo(RateRoll, InRoll * RollRate, Dt, TurnResponse);
	// the nose closes on the aim point: the gap shrinks by what was turned
	if (Aim.X * RateYaw > 0.f) Aim.X -= FMath::Sign(Aim.X) * FMath::Min(FMath::Abs(Aim.X), FMath::Abs(RateYaw) * Dt);
	if (Aim.Y * RatePitch > 0.f) Aim.Y -= FMath::Sign(Aim.Y) * FMath::Min(FMath::Abs(Aim.Y), FMath::Abs(RatePitch) * Dt);
	AddActorLocalRotation(FRotator(RatePitch * Dt, RateYaw * Dt, RateRoll * Dt));
	if (Knock > 0.f)
	{
		// just bounced off something: the nose is thrown round to where the fighter is now going
		Knock -= Dt;
		if (!Velocity.IsNearlyZero(100.f))
		{
			const FQuat Want = FRotationMatrix::MakeFromXZ(Velocity.GetSafeNormal(), GetActorUpVector()).ToQuat();
			SetActorRotation(FQuat::Slerp(GetActorQuat(), Want, FMath::Min(1.f, 5.f * Dt)));
		}
	}

	// ---- speed toward the throttle setting, the velocity swinging round to the nose
	const FVector Fw = GetActorForwardVector();
	float Speed = Velocity.Size();
	const float WantSpeed = bBoosting ? BoostSpeed : Throttle * MaxSpeed;
	Speed = FMath::FInterpConstantTo(Speed, WantSpeed, Dt, Acceleration * (bBoosting || Speed > MaxSpeed ? 1.5f : 1.f));
	FVector Dir = Velocity.IsNearlyZero(1.f) ? Fw : Velocity.GetSafeNormal();
	Dir = (Dir + (Fw - Dir) * FMath::Min(1.f, FMath::Lerp(Grip, MouseGrip, MouseFlight) * Dt)).GetSafeNormal(UE_SMALL_NUMBER, Fw);
	Velocity = Dir * Speed;

	// ---- move; bounce off whatever is in the way
	const FVector Delta = Velocity * Dt;
	FVector New = L + Delta;
	if (!Delta.IsNearlyZero(0.01f))
	{
		FCollisionQueryParams Q(SCENE_QUERY_STAT(SSFighter), true, this);
		FHitResult Hit;
		if (GetWorld()->SweepSingleByChannel(Hit, L, New, FQuat::Identity, ECC_Visibility, FCollisionShape::MakeSphere(HullRadius), Q))
		{
			FVector N = Hit.bStartPenetrating ? Hit.Normal : Hit.ImpactNormal;
			if (N.IsNearlyZero() || Hit.bStartPenetrating)
			{
				// already inside something (it moved onto the fighter): out along the way from its middle
				const FVector From = Hit.GetActor() ? Hit.GetActor()->GetActorLocation() : L - Dir * 100.f;
				N = Hit.Normal.IsNearlyZero() ? (L - From).GetSafeNormal(UE_SMALL_NUMBER, -Dir) : Hit.Normal;
				New = L + N * (Hit.PenetrationDepth + 30.f);
			}
			else New = Hit.Location + N * 4.f;
			const float Closing = -FVector::DotProduct(Velocity, N);
			if (Closing > 0.f)
			{
				Velocity = (Velocity + N * (Closing * 1.45f)) * 0.6f;
				if (GetWorld()->GetTimeSeconds() - LastDamageTime >= 0.25f)
				{
					++Collisions;
					if (Arena) Arena->Sparks(Hit.ImpactPoint, N, 2.5f);
					if (ASSTarget* T = Cast<ASSTarget>(Hit.GetActor())) T->ApplyHit(Closing / 150.f, true);
					TakeHullDamage(FMath::Clamp(Closing / FMath::Max(CollisionDamageSpeed, 1.f), 2.f, MaxCollisionDamage), Hit.ImpactPoint);
				}
				Knock = 0.7f; Aim = FVector2D::ZeroVector;
			}
		}
	}
	if (DeadTime > 0.f) return;
	SetActorLocation(New, false, nullptr, ETeleportType::None);
	if (GetWorld()->GetTimeSeconds() - LastDamageTime > 4.f) HullPoints = FMath::Min(MaxHull, HullPoints + HullRegen * Dt);
}

void ASSFighter::UpdateWeapons(float Dt)
{
	const FVector L = GetActorLocation(), Fw = GetActorForwardVector();
	// ---- lock: the target nearest the nose line; a lock is kept while its target stays near the nose
	ASSTarget* Cur = Locked.Get();
	if (Cur && !Cur->IsAlive()) { Cur = nullptr; Locked = nullptr; bManualLock = false; }
	auto AngleTo = [&](const ASSTarget* T) { return FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(FVector::DotProduct((T->GetActorLocation() - L).GetSafeNormal(), Fw), -1.f, 1.f))); };
	if (Cur && (FVector::Dist(Cur->GetActorLocation(), L) > LockRange * 1.15f || AngleTo(Cur) > (bManualLock ? 75.f : LockAngle * 1.7f))) { Cur = nullptr; Locked = nullptr; bManualLock = false; }
	LockTimer -= Dt;
	if (Arena && !bManualLock && LockTimer <= 0.f)
	{
		LockTimer = 0.12f;
		ASSTarget* New = Arena->PickTarget(L, Fw, LockAngle, LockRange);
		if (New && (!Cur || (New != Cur && AngleTo(New) < AngleTo(Cur) - 3.5f))) Locked = New;
	}

	// ---- cannons: one bolt at a time, the muzzles in turn, all aimed at the convergence point on the nose line
	CannonTimer -= Dt;
	if (bFiring && CannonMuzzles.Num() > 0 && CannonRate > 0.f)
	{
		const FTransform Tr = GetActorTransform();
		int32 Guard = 0;
		while (CannonTimer <= 0.f && Guard++ < 8)
		{
			CannonTimer += 1.f / CannonRate;
			const FVector M = Tr.TransformPositionNoScale(CannonMuzzles[NextMuzzle++ % CannonMuzzles.Num()]);
			const FVector Dir = (L + Fw * Convergence - M).GetSafeNormal();
			BoltList.Add({ M, Dir * BoltSpeed + Velocity, BoltLife });
			++ShotsFired;
			MuzzleFlash = 1.f;
		}
	}
	else if (CannonTimer < 0.f) CannonTimer = 0.f;

	// ---- missiles
	MissileTimer = FMath::Max(0.f, MissileTimer - Dt);
	for (float& R : RailReload) R = FMath::Max(0.f, R - Dt);
}

void ASSFighter::UpdateBolts(float Dt)
{
	UWorld* W = GetWorld();
	FCollisionQueryParams Q(SCENE_QUERY_STAT(SSBolt), true, this);
	for (int32 I = BoltList.Num() - 1; I >= 0; --I)
	{
		FBolt& B = BoltList[I];
		const FVector New = B.P + B.V * Dt;
		FHitResult Hit;
		if (W->LineTraceSingleByChannel(Hit, B.P, New, ECC_Visibility, Q))
		{
			if (ASSTarget* T = Cast<ASSTarget>(Hit.GetActor())) { ++ShotsHit; T->ApplyHit(BoltDamage, true); }
			if (Arena) Arena->Sparks(Hit.ImpactPoint, Hit.ImpactNormal, 1.f);
			BoltList.RemoveAtSwap(I);
			continue;
		}
		B.P = New; B.Life -= Dt;
		if (B.Life <= 0.f || (Arena && Arena->DistanceOutside(New) > 60000.f)) BoltList.RemoveAtSwap(I);
	}
	// (few enough to rebuild every frame)
	Bolts->ClearInstances();
	if (BoltList.Num() > 0 && Bolts->GetStaticMesh())
	{
		TArray<FTransform> Xf; Xf.Reserve(BoltList.Num());
		const FVector Sc(BoltSize.Y / 100.f, BoltSize.Y / 100.f, BoltSize.X / 100.f);
		for (const FBolt& B : BoltList) Xf.Add(FTransform(FRotationMatrix::MakeFromZ(B.V.GetSafeNormal()).ToQuat(), B.P - B.V.GetSafeNormal() * (BoltSize.X * 0.5f), Sc));
		Bolts->AddInstances(Xf, false, true);
	}
}

void ASSFighter::UpdateLook(float Dt)
{
	const float Now = GetWorld()->GetTimeSeconds();
	const float Speed = Velocity.Size();
	const float BoostAlpha = FMath::Clamp((Speed - MaxSpeed) / FMath::Max(BoostSpeed - MaxSpeed, 1.f), 0.f, 1.f);
	// ---- engine flames follow the throttle; missiles show on loaded rails
	const float Burn = FMath::Lerp(0.22f, 1.f, Throttle) * (1.f + 0.6f * (bBoosting ? 1.f : BoostAlpha)) * (1.f + 0.07f * FMath::Sin(Now * 53.f) + 0.04f * FMath::Sin(Now * 91.f));
	for (int32 I = 0; I < PartComps.Num() && I < Parts.Num(); ++I)
	{
		UStaticMeshComponent* C = PartComps[I];
		if (!C) continue;
		if (Parts[I].bFlame)
		{
			const FVector S = FlameScale[I];
			const float Wd = FMath::Lerp(0.75f, 1.f, Throttle);
			C->SetRelativeScale3D(FVector(S.X * Wd, S.Y * Burn, S.Z * Wd));
		}
		if (Parts[I].Rail >= 0) C->SetVisibility(RailReload.IsValidIndex(Parts[I].Rail) && RailReload[Parts[I].Rail] <= 0.f);
	}
	EngineLight->SetIntensity(EngineLightIntensity * (0.15f + Throttle + 1.5f * BoostAlpha));
	MuzzleFlash = FMath::Max(0.f, MuzzleFlash - Dt * 16.f);
	MuzzleLight->SetIntensity(MuzzleFlash * MuzzleLightIntensity);
	// ---- dust: each speck stays where it is until the fighter has left it behind, then turns up ahead again
	if (DustPos.Num() > 0)
	{
		const FVector L = GetActorLocation();
		const FVector Dir = Speed > 100.f ? Velocity / Speed : GetActorForwardVector();
		const float Len = FMath::Clamp(Speed * 0.016f, DustSize, 900.f);
		const FQuat Q = FRotationMatrix::MakeFromZ(Dir).ToQuat();
		const FVector Sc(DustSize / 100.f, DustSize / 100.f, Len / 100.f);
		TArray<FTransform> Xf; Xf.Reserve(DustPos.Num());
		for (FVector& P : DustPos)
		{
			for (int32 A = 0; A < 3; ++A)
			{
				const double D = P[A] - L[A];
				if (D > DustRange) P[A] -= 2.0 * DustRange * FMath::CeilToDouble((D - DustRange) / (2.0 * DustRange));
				else if (D < -DustRange) P[A] += 2.0 * DustRange * FMath::CeilToDouble((-D - DustRange) / (2.0 * DustRange));
			}
			Xf.Add(FTransform(Q, P, Sc));
		}
		Dust->ClearInstances();
		Dust->AddInstances(Xf, false, true);
	}
	// ---- a little bank into yaw turns (the meshes only: the flight frame stays the player's)
	Bank = FMath::FInterpTo(Bank, FMath::Clamp(RateYaw / FMath::Max(YawRate, 1.f), -1.f, 1.f) * BankAngle, Dt, 5.f);
	Visual->SetRelativeRotation(FRotator(0.f, 0.f, Bank));
	// ---- chase camera: pulls back and widens with speed, shakes on a hit; in a fast turn it keeps up enough to hold
	// the fighter in view
	Arm->CameraRotationLagSpeed = FMath::Max(CameraTurnLag, FMath::Max(FMath::Abs(RateYaw), FMath::Abs(RatePitch)) / FMath::Max(CameraMaxTrail, 1.f));
	Arm->SetRelativeRotation(CameraOrbit);
	if (bLagOff) { Arm->bEnableCameraLag = Arm->bEnableCameraRotationLag = true; bLagOff = false; }
	if (bSnapCamera)
	{
		// (the arm updates after this tick: with its lags off for one frame it lands where it belongs)
		Arm->bEnableCameraLag = Arm->bEnableCameraRotationLag = false;
		Arm->TargetArmLength = CameraDistance * (1.f + 0.14f * BoostAlpha);
		bLagOff = bCameraCut = true; bSnapCamera = false;
	}
	if (bCameraCut)
	{
		if (const APlayerController* PC = Cast<APlayerController>(GetController())) if (PC->PlayerCameraManager) PC->PlayerCameraManager->SetGameCameraCutThisFrame();
		bCameraCut = false;
	}
	Shake = FMath::Max(0.f, Shake - Dt * 2.2f);
	const float Sh = Shake * Shake * 38.f;
	Arm->TargetArmLength = FMath::FInterpTo(Arm->TargetArmLength, CameraDistance * (1.f + 0.14f * BoostAlpha), Dt, 4.f);
	Arm->SocketOffset = FVector(0.f, FMath::Sin(Now * 61.f) * Sh, CameraHeight + FMath::Sin(Now * 47.f + 1.3f) * Sh);
	Camera->SetFieldOfView(FMath::FInterpTo(Camera->FieldOfView, FMath::Lerp(BaseFOV, BoostFOV, BoostAlpha), Dt, 5.f));
}
