#include "RD/RDBlood.h"
#include "RD/RDDungeonGenerator.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/DecalComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"

static const int32 RDBloodSeed = 73113;

URDBloodComponent::URDBloodComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void URDBloodComponent::Init(ARDDungeonGenerator* InGenerator)
{
	Generator = InGenerator;
	R.Initialize(RDBloodSeed);
	if (!Generator) return;
	const FVector Hide = Generator->GetActorLocation() + FVector(0, 0, -300.f);
	auto Make = [&](UStaticMesh* Mesh, UMaterialInterface* Mat, int32 Count, int32 CustomFloats, TArray<FTransform>& Xf) -> UInstancedStaticMeshComponent*
	{
		if (!Mesh) return nullptr;
		UInstancedStaticMeshComponent* C = NewObject<UInstancedStaticMeshComponent>(Generator);
		C->SetMobility(EComponentMobility::Movable);
		C->SetStaticMesh(Mesh);
		if (Mat) C->SetMaterial(0, Mat);
		C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		C->SetGenerateOverlapEvents(false);
		C->SetCanEverAffectNavigation(false);
		C->SetCastShadow(false);
		C->bReceivesDecals = false;
		C->SetNumCustomDataFloats(CustomFloats);
		C->SetupAttachment(Generator->GetRootComponent());
		C->RegisterComponent();
		// (a fixed set of instances; the ones not in use sit under the floor, too small to see)
		Xf.Init(FTransform(FQuat::Identity, Hide, FVector(0.0001f)), Count);
		C->AddInstances(Xf, false, true);
		return C;
	};
	DropMesh = Make(Generator->BloodDropMesh, Generator->BloodDropMaterial, MaxDrops, 0, DropXf);
	SprayMesh = Make(Generator->BloodSprayMesh, Generator->BloodSprayMaterial, MaxSprays, 2, SprayXf);
	if (Generator->BloodDropMesh) DropRadius = FMath::Max(1.f, (float)Generator->BloodDropMesh->GetBounds().BoxExtent.X);
	if (Generator->BloodSprayMesh) SprayHalf = FMath::Max(1.f, (float)Generator->BloodSprayMesh->GetBounds().BoxExtent.X);
	Drops.SetNum(MaxDrops); Sprays.SetNum(MaxSprays);
}

int32 URDBloodComponent::GetActiveDrops() const { int32 N = 0; for (const FDrop& D : Drops) if (D.bAlive) ++N; return N; }
int32 URDBloodComponent::GetActiveSprays() const { int32 N = 0; for (const FSpray& S : Sprays) if (S.bAlive) ++N; return N; }
int32 URDBloodComponent::GetActiveDecals() const { int32 N = 0; for (const UDecalComponent* D : Decals) if (IsValid(D)) ++N; return N; }

void URDBloodComponent::AddDrop(const FVector& P, const FVector& V, float Size, float Life)
{
	if (!DropMesh) return;
	FDrop& D = Drops[NextDrop]; NextDrop = (NextDrop + 1) % MaxDrops;
	D.P = P; D.V = V; D.Size = Size; D.Age = 0.f; D.Life = Life; D.bAlive = true;
	++DropsSpawned; bDropsDirty = true;
}

void URDBloodComponent::Burst(FVector At, FVector Dir, float Strength)
{
	if (!Generator) return;
	Strength = FMath::Clamp(Strength, 0.f, 1.f);
	Dir = Dir.GetSafeNormal();
	if (Dir.IsNearlyZero()) Dir = FVector::UpVector;
	const int32 Num = FMath::RoundToInt(FMath::Lerp(16.f, 44.f, Strength) * Generator->BloodAmount);
	for (int32 I = 0; I < Num; ++I)
	{
		// a cone around Dir, thrown a little upward; a few heavy drops among many small ones
		const FVector Side = R.VRand();
		const FVector D = (Dir + Side * R.FRandRange(0.15f, 0.75f) + FVector(0, 0, R.FRandRange(0.1f, 0.6f))).GetSafeNormal();
		const float Speed = R.FRandRange(140.f, 430.f) * (0.75f + 0.5f * Strength);
		const bool bHeavy = R.FRand() < 0.22f;
		AddDrop(At + Side * R.FRandRange(0.f, 5.f), D * Speed, bHeavy ? R.FRandRange(2.2f, 3.4f) : R.FRandRange(1.0f, 2.0f), 2.5f);
	}
	if (SprayMesh)
	{
		const int32 Ns = 2 + FMath::RoundToInt(Strength * 2.f);
		for (int32 I = 0; I < Ns; ++I)
		{
			FSpray& S = Sprays[NextSpray];
			S.P = At + Dir * R.FRandRange(4.f, 14.f) + R.VRand() * 6.f;
			S.V = (Dir + R.VRand() * 0.45f).GetSafeNormal() * R.FRandRange(70.f, 170.f) + FVector(0, 0, 30.f);
			S.Size0 = R.FRandRange(10.f, 18.f); S.Size1 = R.FRandRange(48.f, 70.f) * (0.7f + 0.5f * Strength);
			S.Age = 0.f; S.Life = R.FRandRange(0.28f, 0.42f); S.Roll = R.FRandRange(0.f, 2.f * PI); S.bAlive = true;
			SprayMesh->SetCustomDataValue(NextSpray, 1, R.FRand(), false);
			NextSpray = (NextSpray + 1) % MaxSprays;
		}
		bSpraysDirty = true;
	}
	++Bursts; LastBurstAt = At; LastBurstTime = GetWorld()->GetTimeSeconds();
}

void URDBloodComponent::Drip(const FVector& At)
{
	AddDrop(At, FVector(R.FRandRange(-25.f, 25.f), R.FRandRange(-25.f, 25.f), R.FRandRange(-40.f, 10.f)), R.FRandRange(1.4f, 2.4f), 2.5f);
}

UDecalComponent* URDBloodComponent::AddDecal(UMaterialInterface* Material, const FVector& At, const FVector& Normal, float Size, float Depth)
{
	if (!Material || !Generator) return nullptr;
	// the oldest make room
	Decals.RemoveAll([](const UDecalComponent* D) { return !IsValid(D); });
	while (Decals.Num() >= FMath::Max(1, Generator->MaxBloodDecals)) { Decals[0]->DestroyComponent(); Decals.RemoveAt(0); }
	UDecalComponent* D = NewObject<UDecalComponent>(Generator);
	D->SetDecalMaterial(Material);
	D->DecalSize = FVector(Depth, Size, Size);
	// (a decal projects along its X axis: into the surface; any turn about that axis)
	const FQuat Rot = FRotationMatrix::MakeFromX(-Normal).ToQuat() * FQuat(FVector::XAxisVector, R.FRandRange(0.f, 2.f * PI));
	D->SetWorldLocationAndRotation(At, Rot);
	D->SortOrder = DecalsSpawned;
	D->FadeScreenSize = 0.f;
	D->RegisterComponent();
	if (Generator->BloodDecalSeconds > 0.f) D->SetFadeOut(Generator->BloodDecalSeconds, 4.f, false);
	Decals.Add(D);
	++DecalsSpawned;
	return D;
}

void URDBloodComponent::Pool(FVector At, float Size)
{
	if (!Generator || Generator->BloodPools.Num() == 0) return;
	UMaterialInterface* M = Generator->BloodPools[R.RandRange(0, Generator->BloodPools.Num() - 1)];
	if (UDecalComponent* D = AddDecal(M, FVector(At.X, At.Y, Generator->GetActorLocation().Z), FVector::UpVector, Size * 0.5f, 14.f))
	{
		D->SetWorldScale3D(FVector(1.f, 0.2f, 0.2f));
		Pools.Add({ D, 0.f });
		++PoolsSpawned;
	}
}

void URDBloodComponent::Clear()
{
	for (UDecalComponent* D : Decals) if (IsValid(D)) D->DestroyComponent();
	Decals.Reset(); Pools.Reset();
	const FVector Hide = Generator ? Generator->GetActorLocation() + FVector(0, 0, -300.f) : FVector(0, 0, -300.f);
	for (int32 I = 0; I < Drops.Num(); ++I) { Drops[I].bAlive = false; DropXf[I] = FTransform(FQuat::Identity, Hide, FVector(0.0001f)); }
	for (int32 I = 0; I < Sprays.Num(); ++I) { Sprays[I].bAlive = false; SprayXf[I] = FTransform(FQuat::Identity, Hide, FVector(0.0001f)); }
	if (DropMesh) DropMesh->BatchUpdateInstancesTransforms(0, DropXf, true, true, true);
	if (SprayMesh) SprayMesh->BatchUpdateInstancesTransforms(0, SprayXf, true, true, true);
	NextDrop = NextSpray = 0; bDropsDirty = bSpraysDirty = false;
	Bursts = DropsSpawned = DecalsSpawned = PoolsSpawned = 0; LastBurstTime = -100.f;
	R.Initialize(RDBloodSeed);
}

void URDBloodComponent::TickComponent(float Dt, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(Dt, TickType, ThisTickFunction);
	UWorld* W = GetWorld();
	if (!Generator || !W || Dt <= 0.f) return;
	const float FloorZ = Generator->GetActorLocation().Z;
	if (DropMesh && bDropsDirty)
	{
		FCollisionQueryParams Q(SCENE_QUERY_STAT(RDBlood), false);
		if (const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0)) Q.AddIgnoredActor(P);
		bool bAny = false;
		for (int32 I = 0; I < MaxDrops; ++I)
		{
			FDrop& D = Drops[I];
			if (!D.bAlive) continue;
			D.Age += Dt;
			D.V.Z -= 980.f * Dt;
			D.V *= FMath::Max(0.f, 1.f - 0.5f * Dt);
			const FVector To = D.P + D.V * Dt;
			FHitResult H;
			if (D.Age > D.Life || To.Z < FloorZ - 60.f) D.bAlive = false;
			else if (W->LineTraceSingleByChannel(H, D.P, To, ECC_Visibility, Q) && !H.bStartPenetrating)
			{
				// it lands: the heavy drops always leave a mark, of the small ones every fifth
				D.bAlive = false;
				if (Generator->BloodDecals.Num() > 0 && (D.Size > 2.1f || R.FRand() < 0.2f))
					AddDecal(Generator->BloodDecals[R.RandRange(0, Generator->BloodDecals.Num() - 1)], H.ImpactPoint, H.ImpactNormal, D.Size * R.FRandRange(7.f, 12.f), 9.f);
			}
			else D.P = To;
			if (D.bAlive)
			{
				// stretched along its path
				const float Speed = D.V.Size();
				const float S = D.Size / DropRadius;
				DropXf[I] = FTransform(FRotationMatrix::MakeFromX(D.V.GetSafeNormal(1e-4f, FVector::UpVector)).ToQuat(), D.P, FVector(S * (1.f + FMath::Min(Speed / 160.f, 4.f)), S, S));
				bAny = true;
			}
			else DropXf[I] = FTransform(FQuat::Identity, FVector(D.P.X, D.P.Y, FloorZ - 300.f), FVector(0.0001f));
		}
		DropMesh->BatchUpdateInstancesTransforms(0, DropXf, true, true, false);
		bDropsDirty = bAny;
	}
	if (SprayMesh && bSpraysDirty)
	{
		FVector Cam = FVector(0, 0, 1e5f);
		if (const APlayerCameraManager* PCM = UGameplayStatics::GetPlayerCameraManager(this, 0)) Cam = PCM->GetCameraLocation();
		bool bAny = false;
		for (int32 I = 0; I < MaxSprays; ++I)
		{
			FSpray& S = Sprays[I];
			if (!S.bAlive) continue;
			S.Age += Dt;
			if (S.Age >= S.Life)
			{
				S.bAlive = false;
				SprayXf[I] = FTransform(FQuat::Identity, FVector(S.P.X, S.P.Y, FloorZ - 300.f), FVector(0.0001f));
				SprayMesh->SetCustomDataValue(I, 0, 0.f, false);
				continue;
			}
			S.P += S.V * Dt;
			S.V *= FMath::Max(0.f, 1.f - 3.f * Dt);
			S.V.Z -= 160.f * Dt;
			const float T = S.Age / S.Life;
			const float Size = FMath::Lerp(S.Size0, S.Size1, 1.f - FMath::Square(1.f - T));
			const float Fade = FMath::Pow(1.f - T, 1.5f) * FMath::Min(1.f, T * 14.f);
			// the sprite's plane faces the camera, turned about the view line
			const FVector ToCam = (Cam - S.P).GetSafeNormal(1e-4f, FVector::UpVector);
			const FQuat Face = FRotationMatrix::MakeFromZ(ToCam).ToQuat() * FQuat(FVector::ZAxisVector, S.Roll);
			SprayXf[I] = FTransform(Face, S.P, FVector(Size * 0.5f / SprayHalf));
			SprayMesh->SetCustomDataValue(I, 0, Fade, false);
			bAny = true;
		}
		SprayMesh->BatchUpdateInstancesTransforms(0, SprayXf, true, true, false);
		bSpraysDirty = bAny;
	}
	for (int32 I = Pools.Num() - 1; I >= 0; --I)
	{
		FPool& P = Pools[I];
		UDecalComponent* D = P.Decal.Get();
		if (!D) { Pools.RemoveAtSwap(I); continue; }
		P.Age += Dt;
		const float A = FMath::Clamp(P.Age / 3.f, 0.f, 1.f);
		const float S = FMath::Lerp(0.2f, 1.f, 1.f - FMath::Square(1.f - A));
		D->SetWorldScale3D(FVector(1.f, S, S));
		if (A >= 1.f) Pools.RemoveAtSwap(I);
	}
}
