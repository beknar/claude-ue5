#include "SS/SSArena.h"
#include "SS/SSTarget.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "Particles/ParticleSystem.h"
#include "Particles/ParticleSystemComponent.h"

DEFINE_LOG_CATEGORY(LogStarship);

ASSArena::ASSArena()
{
	PrimaryActorTick.bCanEverTick = true;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}

bool ASSArena::IsInside(const FVector& P, float Margin) const
{
	const FVector D = (P - GetActorLocation()).GetAbs();
	return D.GetMax() <= HalfExtent - Margin;
}

float ASSArena::DistanceOutside(const FVector& P) const
{
	const FVector D = (P - GetActorLocation()).GetAbs() - FVector(HalfExtent);
	return FVector(FMath::Max(D.X, 0.0), FMath::Max(D.Y, 0.0), FMath::Max(D.Z, 0.0)).Size();
}

float ASSArena::DistanceToEdge(const FVector& P) const
{
	return HalfExtent - (P - GetActorLocation()).GetAbs().GetMax();
}

TArray<ASSTarget*> ASSArena::GetTargets() const
{
	TArray<ASSTarget*> Out;
	for (ASSTarget* T : Targets) if (T && T->IsAlive()) Out.Add(T);
	return Out;
}

int32 ASSArena::CountTargets(ESSTargetKind Kind) const
{
	int32 N = 0;
	for (const ASSTarget* T : Targets) if (T && T->IsAlive() && T->Kind == Kind) ++N;
	return N;
}

ASSTarget* ASSArena::PickTarget(const FVector& Origin, const FVector& Dir, float MaxAngle, float MaxDist, const ASSTarget* Not, bool bDronesFirst) const
{
	ASSTarget* Best = nullptr; float BestScore = 1e9f;
	const float MinCos = FMath::Cos(FMath::DegreesToRadians(MaxAngle));
	for (ASSTarget* T : Targets)
	{
		if (!T || !T->IsAlive() || T == Not) continue;
		const FVector D = T->GetActorLocation() - Origin;
		const float Dist = D.Size();
		if (Dist > MaxDist + T->GetRadius() || Dist < 1.f) continue;
		// (a big target counts as on the line when the line passes through it)
		const float Ang = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(FVector::DotProduct(D / Dist, Dir), -1.f, 1.f)));
		const float Slack = FMath::RadiansToDegrees(FMath::Atan2(T->GetRadius(), Dist));
		if (Ang - Slack > MaxAngle) continue;
		float S = FMath::Max(0.f, Ang - Slack) + Dist / MaxDist * 3.f;
		if (bDronesFirst && T->Kind != ESSTargetKind::Drone) S += MaxAngle * 0.6f;
		if (S < BestScore) { BestScore = S; Best = T; }
	}
	return Best;
}

bool ASSArena::Blocked(const FVector& P, float Pad) const
{
	for (const FSSSphere& K : KeepOut) if (FVector::DistSquared(P, K.Center) < FMath::Square(K.Radius + Pad)) return true;
	return false;
}

ASSTarget* ASSArena::SpawnTarget(ESSTargetKind Kind, UStaticMesh* Mesh, const FVector& Loc, float Size, const FRotator& MeshRot)
{
	if (!Mesh) return nullptr;
	FActorSpawnParameters P; P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ASSTarget* T = GetWorld()->SpawnActor<ASSTarget>(ASSTarget::StaticClass(), FTransform(FRotator(R.FRandRange(-180.f, 180.f), R.FRandRange(-180.f, 180.f), R.FRandRange(-180.f, 180.f)), Loc), P);
	if (!T) return nullptr;
	const float MeshRadius = FMath::Max(Mesh->GetBounds().SphereRadius * 0.8f, 1.f);
	const float Scale = Size / MeshRadius;
	const float Hp = FMath::Max(12.f, Size / 100.f * HealthPerMeter) * (Kind == ESSTargetKind::Container ? 0.6f : 1.f);
	T->Setup(this, Kind, Mesh, MeshRot, Scale, Hp, Kind == ESSTargetKind::Container ? 25 : FMath::Clamp(FMath::RoundToInt(Size / 100.f) * 5, 5, 60));
#if WITH_EDITOR
	T->SetActorLabel(FString::Printf(TEXT("SS_%s_%d"), Kind == ESSTargetKind::Asteroid ? TEXT("Asteroid") : Kind == ESSTargetKind::Container ? TEXT("Container") : TEXT("Target"), Targets.Num()));
#endif
	return T;
}

void ASSArena::SpawnField(const FSSField& F)
{
	const TArray<TObjectPtr<UStaticMesh>>& Meshes = F.Kind == ESSTargetKind::Container ? ContainerMeshes : AsteroidMeshes;
	if (Meshes.Num() == 0) return;
	const FVector C0 = GetActorLocation();
	int32 Made = 0;
	for (int32 Try = 0; Try < F.Count * 6 && Made < F.Count; ++Try)
	{
		// denser toward the middle of the field
		const FVector P = F.Center + R.VRand() * (F.Radius * FMath::Pow(R.FRand(), 0.6f));
		const float Size = FMath::Lerp(F.MinSize, F.MaxSize, FMath::Pow(R.FRand(), 2.2f));
		if ((P - C0).GetAbs().GetMax() > HalfExtent - Size - 500.f || Blocked(P, Size)) continue;
		bool bFree = true;
		for (const ASSTarget* O : Targets)
			if (O && FVector::DistSquared(O->GetActorLocation(), P) < FMath::Square(O->GetRadius() + Size + 150.f)) { bFree = false; break; }
		if (!bFree) continue;
		ASSTarget* T = SpawnTarget(F.Kind, Meshes[R.RandRange(0, Meshes.Num() - 1)], P, Size);
		if (!T) continue;
		const float Slow = 1.f / FMath::Max(1.f, Size / 400.f);
		T->SetDrift(R.VRand() * R.FRandRange(0.f, 260.f) * Slow, FRotator(R.FRandRange(-14.f, 14.f), R.FRandRange(-14.f, 14.f), R.FRandRange(-14.f, 14.f)) * Slow);
		if (F.Kind == ESSTargetKind::Asteroid && Size >= SplitMinRadius) T->SplitsLeft = Size >= SplitMinRadius * 2.2f ? 2 : 1;
		++Made;
	}
}

ASSTarget* ASSArena::SpawnDrone()
{
	if (DroneTypes.Num() == 0 || Patrols.Num() == 0) return nullptr;
	const FSSDroneDef& D = DroneTypes[DroneSerial % DroneTypes.Num()];
	const FSSSphere& Pt = Patrols[R.RandRange(0, Patrols.Num() - 1)];
	if (!D.Mesh) { ++DroneSerial; return nullptr; }
	FActorSpawnParameters P; P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ASSTarget* T = GetWorld()->SpawnActor<ASSTarget>(ASSTarget::StaticClass(), FTransform(Pt.Center), P);
	if (!T) return nullptr;
	T->Setup(this, ESSTargetKind::Drone, D.Mesh, D.MeshRotation, D.Scale, D.Health, D.Points);
	T->TypeName = D.Name;
	// its own circle inside the patrol volume: any plane, a radius the drone can fly at its speed
	const float Rad = Pt.Radius * R.FRandRange(0.45f, 1.f);
	const FVector Axis = (FVector::UpVector + R.VRand() * 0.9f).GetSafeNormal();
	T->SetPatrol(Pt.Center + R.VRand() * (Pt.Radius * 0.25f), Rad, Axis, D.Speed * R.FRandRange(0.8f, 1.15f) * (R.FRand() < 0.5f ? 1.f : -1.f), R.FRandRange(0.f, 6.28f));
	if (DroneTrailFX)
	{
		T->Trail->SetAsset(DroneTrailFX);
		T->Trail->SetRelativeLocation(D.TrailOffset);
		T->Trail->Activate(true);
	}
	if (DroneTrailPS)
	{
		T->TrailPS->SetTemplate(DroneTrailPS);
		T->TrailPS->SetRelativeLocation(D.TrailOffset);
		T->TrailPS->Activate(true);
	}
#if WITH_EDITOR
	T->SetActorLabel(FString::Printf(TEXT("SS_Drone_%d_%s"), DroneSerial, *D.Name.ToString()));
#endif
	++DroneSerial;
	return T;
}

void ASSArena::BeginPlay()
{
	Super::BeginPlay();
	Populate();
}

void ASSArena::Restart()
{
	// (a destroyed target takes itself off the list: work on a copy)
	const TArray<TObjectPtr<ASSTarget>> Old = Targets;
	Targets.Reset();
	for (ASSTarget* T : Old) if (T) T->Destroy();
	DroneRespawns.Reset(); DroneSerial = 0;
	Populate();
}

void ASSArena::Populate()
{
	R.Initialize(Seed);
	Score = AsteroidsDestroyed = DronesDestroyed = ContainersDestroyed = 0;
	const double T0 = FPlatformTime::Seconds();
	for (const FSSField& F : Fields) SpawnField(F);
	const int32 Rocks = CountTargets(ESSTargetKind::Asteroid), Boxes = CountTargets(ESSTargetKind::Container);
	for (int32 I = 0; I < DroneCount; ++I) SpawnDrone();
	UE_LOG(LogStarship, Log, TEXT("SSARENA play: %d asteroids, %d containers, %d drones in %d fields, %.0f ms"), Rocks, Boxes, CountTargets(ESSTargetKind::Drone), Fields.Num(),
		(FPlatformTime::Seconds() - T0) * 1000.0);
}

void ASSArena::Tick(float Dt)
{
	Super::Tick(Dt);
	for (int32 I = DroneRespawns.Num() - 1; I >= 0; --I)
	{
		DroneRespawns[I] -= Dt;
		if (DroneRespawns[I] <= 0.f) { DroneRespawns.RemoveAtSwap(I); SpawnDrone(); }
	}
}

void ASSArena::OnTargetDestroyed(ASSTarget* T, bool bByPlayer)
{
	if (!T) return;
	const FVector L = T->GetActorLocation();
	const float Rad = T->GetRadius();
	if (bByPlayer) Score += T->Points;
	switch (T->Kind)
	{
	case ESSTargetKind::Asteroid: ++AsteroidsDestroyed; break;
	case ESSTargetKind::Drone: ++DronesDestroyed; DroneRespawns.Add(DroneRespawnDelay); break;
	case ESSTargetKind::Container: ++ContainersDestroyed; break;
	default: break;
	}
	Blast(L, FMath::Max(Rad * 1.6f, 500.f), T->Kind == ESSTargetKind::Asteroid ? FLinearColor(1.f, 0.72f, 0.42f) : FLinearColor(1.f, 0.5f, 0.16f));
	UStaticMesh* M = T->Mesh->GetStaticMesh();
	if (!M) return;
	const float MeshRadius = FMath::Max(M->GetBounds().SphereRadius * 0.8f, 1.f);
	if (T->Kind == ESSTargetKind::Asteroid && T->SplitsLeft > 0)
	{
		// breaks into smaller asteroids that fly apart
		const int32 N = R.RandRange(2, 3);
		for (int32 I = 0; I < N; ++I)
		{
			const FVector Dir = R.VRand();
			const float Size = Rad * R.FRandRange(0.38f, 0.52f);
			if (ASSTarget* C = SpawnTarget(ESSTargetKind::Asteroid, M, L + Dir * Rad * 0.55f, Size))
			{
				C->SplitsLeft = T->SplitsLeft - 1;
				C->SetDrift(T->GetVelocity() + Dir * R.FRandRange(500.f, 1500.f), FRotator(R.FRandRange(-60.f, 60.f), R.FRandRange(-60.f, 60.f), R.FRandRange(-60.f, 60.f)));
			}
		}
	}
	// short-lived fragments (no collision)
	const int32 Bits = T->Kind == ESSTargetKind::Drone ? 5 : 4;
	for (int32 I = 0; I < Bits; ++I)
	{
		FActorSpawnParameters P; P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		const FVector Dir = R.VRand();
		ASSTarget* D = GetWorld()->SpawnActor<ASSTarget>(ASSTarget::StaticClass(), FTransform(FRotator(R.FRandRange(-180.f, 180.f), R.FRandRange(-180.f, 180.f), 0.f), L + Dir * Rad * 0.4f), P);
		if (!D) continue;
		D->Setup(this, ESSTargetKind::Debris, M, FRotator::ZeroRotator, Rad * R.FRandRange(0.12f, 0.24f) / MeshRadius, 1.f, 0);
		D->SetDrift(T->GetVelocity() * 0.5f + Dir * R.FRandRange(900.f, 3200.f), FRotator(R.FRandRange(-200.f, 200.f), R.FRandRange(-200.f, 200.f), R.FRandRange(-200.f, 200.f)));
		D->SetLifetime(R.FRandRange(2.2f, 4.f));
	}
}

void ASSArena::Blast(const FVector& Location, float Radius, FLinearColor Color)
{
	UWorld* W = GetWorld();
	const float K = Radius / FMath::Max(ExplosionFXSize, 1.f);
	if (ExplosionFX) UNiagaraFunctionLibrary::SpawnSystemAtLocation(W, ExplosionFX, Location, FRotator::ZeroRotator, FVector(K), true, true, ENCPoolMethod::None, true);
	if (ExplosionPS) UGameplayStatics::SpawnEmitterAtLocation(W, ExplosionPS, FTransform(FRotator::ZeroRotator, Location, FVector(K)), true, EPSCPoolMethod::None, true);
	FActorSpawnParameters P; P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	if (ASSBlast* B = W->SpawnActor<ASSBlast>(ASSBlast::StaticClass(), FTransform(Location), P)) B->Start(Radius, BlastMesh, BlastMaterial, Color, FMath::Clamp(0.45f + Radius / 6000.f, 0.5f, 1.4f));
}

void ASSArena::Sparks(const FVector& Location, const FVector& Normal, float Scale)
{
	UWorld* W = GetWorld();
	const FRotator Rot = Normal.IsNearlyZero() ? FRotator::ZeroRotator : Normal.Rotation();
	if (ImpactFX) UNiagaraFunctionLibrary::SpawnSystemAtLocation(W, ImpactFX, Location, Rot, FVector(ImpactFXScale * Scale), true, true, ENCPoolMethod::None, true);
	if (ImpactPS) UGameplayStatics::SpawnEmitterAtLocation(W, ImpactPS, FTransform(Rot, Location, FVector(ImpactFXScale * Scale)), true, EPSCPoolMethod::None, true);
	FActorSpawnParameters P; P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	if (ASSBlast* B = W->SpawnActor<ASSBlast>(ASSBlast::StaticClass(), FTransform(Location), P)) B->Start(160.f * Scale, BlastMesh, BlastMaterial, FLinearColor(1.f, 0.8f, 0.45f), 0.18f);
}

int32 ASSArena::RadialDamage(const FVector& Location, float Radius, float Damage, bool bByPlayer)
{
	// (destroying a target changes the list: work on a copy)
	TArray<ASSTarget*> Hit;
	for (ASSTarget* T : Targets) if (T && T->IsAlive() && FVector::Dist(T->GetActorLocation(), Location) < Radius + T->GetRadius()) Hit.Add(T);
	int32 Killed = 0;
	for (ASSTarget* T : Hit)
	{
		const float D = FMath::Max(0.f, FVector::Dist(T->GetActorLocation(), Location) - T->GetRadius());
		if (T->ApplyHit(Damage * FMath::Lerp(1.f, 0.33f, FMath::Clamp(D / Radius, 0.f, 1.f)), bByPlayer)) ++Killed;
	}
	return Killed;
}
