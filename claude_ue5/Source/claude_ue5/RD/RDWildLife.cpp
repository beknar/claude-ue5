// The wilderness's animals, insects and the sky's birds (the user's list of 2026-11-04, docs/improvements7.txt: "there should
// be more animals and insects that are appropriate for that biome. those animals should flee from the player if the player
// gets too close (1-3 meters)"; "birds of different sizes and types"). Round her, from a stream of their own (the session's
// seed: never the play's):
//   - animals (the generator's WildFauna: Wildlands' deer, wolf and squirrel, the farm's rabbit as a hare): up to
//     WildAnimalsMax at 60 to 150 m, of the kinds that live in the biome where each is put, on dry walkable ground; dropped
//     past 230 m. Each its own flee distance (FleeMin to FleeMax): within it of her it runs off away from her.
//   - insects and birds (WildSwarms: the packs' Niagara butterflies, fireflies, flies, bird flocks, gulls, crows): insects at
//     12 to 45 m by the time of day and the biome (Brokenspire's walls count as "town"), birds 60 to 220 m off and tens of
//     metres up by day; dropped when far or out of their hour or place.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDSection.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimSequenceBase.h"
#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDWildLife, Log, All);

/** in a town's walls only the swarms and birds of the town or of everywhere (both the spawning and the keeping) */
static bool RDWLInTownOk(const FRDWildSwarm& Sw) { return Sw.Biomes.Contains(TEXT("town")) || Sw.Biomes.Contains(TEXT("*")); }

// ------------------------------------------------------------------------------------------------ an animal
ARDWildAnimal::ARDWildAnimal()
{
	PrimaryActorTick.bCanEverTick = true;
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;
	Body = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Body"));
	Body->SetupAttachment(Root);
	Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Body->SetAnimationMode(EAnimationMode::AnimationSingleNode);
	Body->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
	Body->bEnableUpdateRateOptimizations = true;
	Body->SetCastShadow(true);
}

void ARDWildAnimal::Init(ARDDungeonGenerator* InGenerator, int32 InDef, uint32 InSeed)
{
	Gen = InGenerator; Def = InDef; R.Initialize((int32)InSeed);
	if (!Gen || !Gen->WildFauna.IsValidIndex(Def)) return;
	const FRDWildFauna& F = Gen->WildFauna[Def];
	Body->SetSkeletalMeshAsset(F.Mesh);
	Body->SetRelativeLocationAndRotation(FVector(0, 0, F.MeshZ), FRotator(0, F.MeshYaw, 0));
	Body->SetRelativeScale3D(FVector(F.Scale));
	FleeR = R.FRandRange(F.FleeMin, FMath::Max(F.FleeMax, F.FleeMin));
	Home = GetActorLocation();
	SetState(R.RandRange(0, 1), GetWorld()->GetTimeSeconds());
}

void ARDWildAnimal::Play(UAnimationAsset* A, float Rate)
{
	if (!A) return;
	if (A != CurAnim) { Body->PlayAnimation(A, true); CurAnim = A; if (const UAnimSequenceBase* S = Cast<UAnimSequenceBase>(A)) Body->SetPosition(R.FRandRange(0.f, S->GetPlayLength())); }
	Body->SetPlayRate(Rate);
}

void ARDWildAnimal::SetState(int32 S, float Now, const FVector& Away)
{
	if (!Gen || !Gen->WildFauna.IsValidIndex(Def)) return;
	const FRDWildFauna& F = Gen->WildFauna[Def];
	State = S;
	const float Sc = FMath::Max(F.Scale, 0.1f);
	if (S == 3)
	{
		// (off away from her, a little to one side, for a few seconds at its run)
		const FVector Dir = FRotator(0, R.FRandRange(-30.f, 30.f), 0).RotateVector(Away.GetSafeNormal2D());
		To = GetActorLocation() + Dir * F.RunSpeed * R.FRandRange(3.5f, 6.f);
		Until = Now + 8.f;
		Play(F.Run ? F.Run.Get() : F.Walk.Get(), F.Run ? F.RunSpeed / FMath::Max(F.RunClipSpeed * Sc, 1.f) : 3.f);
		++Fled; ++Gen->AnimalsFled;
		return;
	}
	if (S == 2)
	{
		// (somewhere else near where it was put)
		To = Home + FVector(R.FRandRange(-1500.f, 1500.f), R.FRandRange(-1500.f, 1500.f), 0.f);
		Until = Now + 25.f;
		Play(F.Walk, F.WalkSpeed / FMath::Max(F.WalkClipSpeed * Sc, 1.f));
		return;
	}
	Until = Now + (S == 1 ? R.FRandRange(5.f, 12.f) : R.FRandRange(3.f, 7.f));
	Play(S == 1 && F.Eat ? F.Eat.Get() : F.Idle.Get(), 1.f);
}

void ARDWildAnimal::Tick(float Dt)
{
	Super::Tick(Dt);
	if (!Gen || !Gen->WildFauna.IsValidIndex(Def) || !Gen->IsWildReady()) return;
	const FRDWildFauna& F = Gen->WildFauna[Def];
	UWorld* W = GetWorld();
	const float Now = W->GetTimeSeconds();
	FVector L = GetActorLocation();
	// ---- she comes too near: off it runs (once running, it keeps on)
	if (const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0); Her && State != 3)
	{
		const FVector Hd = L - Her->GetActorLocation();
		if (Hd.Size2D() < FleeR && FMath::Abs(Hd.Z) < 300.f) { SetState(3, Now, Hd); }
	}
	if (State == 2 || State == 3)
	{
		FVector D = To - L; D.Z = 0.f;
		if (D.Size() < 30.f || Now >= Until) { SetState(State == 3 ? 0 : (R.FRand() < 0.6f ? 1 : 0), Now); return; }
		const FRotator Want = D.Rotation();
		SetActorRotation(FRotator(0.f, FMath::RInterpConstantTo(GetActorRotation(), Want, Dt, State == 3 ? 360.f : 120.f).Yaw, 0.f));
		if (FMath::Abs(FMath::FindDeltaAngleDegrees(GetActorRotation().Yaw, Want.Yaw)) < 50.f)
		{
			const float Sp = State == 3 ? F.RunSpeed : F.WalkSpeed;
			const FVector Nx = L + GetActorForwardVector() * FMath::Min(Sp * Dt, D.Size());
			// (on dry ground: water or a steep rise ahead turns it)
			FRDWSample S; Gen->Wild->Sample(Nx.X / 100.0, Nx.Y / 100.0, S, false);
			const float Zn = Gen->Wild->ToZ(Gen->Wild->Height(Nx.X / 100.0, Nx.Y / 100.0));
			if (S.WaterKind != 0 || FMath::Abs(Zn - L.Z) > Sp * Dt * 1.2f + 30.f || Gen->IsInTownWalls(Nx)) { To = L - (To - L); return; }
			L = FVector(Nx.X, Nx.Y, Zn);
			SetActorLocation(L);
		}
		return;
	}
	// (standing or grazing: kept on the ground)
	const float Z = Gen->Wild->ToZ(Gen->Wild->Height(L.X / 100.0, L.Y / 100.0));
	if (FMath::Abs(Z - L.Z) > 2.f) SetActorLocation(FVector(L.X, L.Y, Z));
	if (Now >= Until) SetState(R.FRand() < 0.4f ? 2 : State == 1 ? 0 : 1, Now);
}

// ------------------------------------------------------------------------------------------------ the generator's side
ARDWildAnimal* ARDDungeonGenerator::SpawnWildAnimalAt(FName Kind, FVector At)
{
	int32 Def = -1;
	for (int32 I = 0; I < WildFauna.Num(); ++I) if (WildFauna[I].Name == Kind) { Def = I; break; }
	if (Def < 0 || !WildFauna[Def].Mesh || !IsWildReady()) return nullptr;
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	const float Z = Wild->ToZ(Wild->Height(At.X / 100.0, At.Y / 100.0));
	ARDWildAnimal* A = GetWorld()->SpawnActor<ARDWildAnimal>(ARDWildAnimal::StaticClass(), FTransform(FRotator(0, (float)(HashCombine((uint32)At.X, (uint32)At.Y) % 360u), 0), FVector(At.X, At.Y, Z)), Sp);
	if (!A) return nullptr;
	A->Init(this, Def, HashCombine((uint32)SessionSeed, (uint32)AnimalsSpawned * 2654435761u));
	WildAnimals.Add(A); ++AnimalsSpawned;
	return A;
}

void ARDDungeonGenerator::TickWildLife(float Dt, const FVector& Her)
{
	WildLifeT -= Dt;
	if (WildLifeT > 0.f) return;
	WildLifeT = 0.5f;
	UWorld* W = GetWorld();
	if (!W) return;
	const bool bReady = bWild && IsWildReady();
	const bool bInTown = !bReady || IsInTownWalls(Her);
	const bool bDay = DayLight > 0.35f;
	FRandomStream Rr((int32)HashCombine((uint32)SessionSeed ^ 0x11FEu, (uint32)FMath::RoundToInt(W->GetTimeSeconds() * 2.f)));
	// ---- the animals: the far ones go, new ones come
	for (int32 I = WildAnimals.Num() - 1; I >= 0; --I)
	{
		ARDWildAnimal* A = WildAnimals[I];
		if (!IsValid(A)) { WildAnimals.RemoveAt(I); continue; }
		if (!bReady || FVector::Dist2D(A->GetActorLocation(), Her) > 23000.f) { A->Destroy(); WildAnimals.RemoveAt(I); }
	}
	if (bReady && !bInTown && WildAnimals.Num() < WildAnimalsMax && WildFauna.Num() > 0)
	{
		// (a try a half second: a point 60 to 150 m off, its biome's kinds weighed by how many live there a km²)
		const float Ang = Rr.FRandRange(0.f, 2.f * PI), Dd = Rr.FRandRange(6000.f, 15000.f);
		const FVector P = Her + FVector(FMath::Cos(Ang), FMath::Sin(Ang), 0.f) * Dd;
		FRDWSample S; Wild->Sample(P.X / 100.0, P.Y / 100.0, S, false);
		const FString Bn = Wild->BiomeName(S.Biome);
		TArray<int32> Ks; TArray<float> Ws; float Sum = 0.f;
		for (int32 K = 0; K < WildFauna.Num(); ++K)
		{
			const FRDWildFauna& F = WildFauna[K];
			if (!F.Mesh || !(F.Biomes.Contains(Bn) || F.Biomes.Contains(TEXT("*")))) continue;
			int32 Have = 0; for (const ARDWildAnimal* A : WildAnimals) if (IsValid(A) && A->Def == K) ++Have;
			// (as many as live in the 0.07 km² round her, one at least)
			if (Have >= FMath::Max(1, FMath::RoundToInt(F.PerKm2 * 0.07f))) continue;
			Ks.Add(K); Ws.Add(F.PerKm2); Sum += F.PerKm2;
		}
		const float Hx = Wild->Height(P.X / 100.0 + 2.0, P.Y / 100.0) - Wild->Height(P.X / 100.0 - 2.0, P.Y / 100.0);
		if (Ks.Num() > 0 && S.WaterKind == 0 && FMath::Abs(Hx) < 2.f && S.Road < 0.3f)
		{
			float Pk = Rr.FRand() * Sum; int32 Pick = Ks[0];
			for (int32 K = 0; K < Ks.Num(); ++K) { if (Pk < Ws[K]) { Pick = Ks[K]; break; } Pk -= Ws[K]; }
			SpawnWildAnimalAt(WildFauna[Pick].Name, P);
		}
	}
	// ---- the swarms and birds
	for (int32 I = SwarmInsts.Num() - 1; I >= 0; --I)
	{
		FRDSwarmInst& Si = SwarmInsts[I];
		UNiagaraComponent* C = Si.C.Get();
		bool bKeep = C != nullptr && WildSwarms.IsValidIndex(Si.Def);
		if (bKeep)
		{
			const FRDWildSwarm& Sw = WildSwarms[Si.Def];
			const float Far = Sw.Layer == 1 ? 40000.f : 8000.f;
			bKeep = FVector::Dist2D(Si.At, Her) < Far && (bDay ? Sw.bDay : Sw.bNight) && (!bInTown || RDWLInTownOk(Sw));
			// (no birds in rain, snow or fog)
			if (Sw.Layer == 1 && bSky7 && (SkyRain > 0.3f || SkyFog > 0.6f)) bKeep = false;
		}
		if (!bKeep) { if (C) { C->Deactivate(); C->DestroyComponent(); } SwarmInsts.RemoveAt(I); }
	}
	for (int32 K = 0; K < WildSwarms.Num(); ++K)
	{
		const FRDWildSwarm& Sw = WildSwarms[K];
		if (!Sw.System || !(bDay ? Sw.bDay : Sw.bNight)) continue;
		if (Sw.Layer == 1 && bSky7 && (SkyRain > 0.3f || SkyFog > 0.6f)) continue;
		int32 Have = 0; for (const FRDSwarmInst& Si : SwarmInsts) if (Si.Def == K) ++Have;
		if (Have >= Sw.Count) continue;
		const bool bBird = Sw.Layer == 1;
		// (in the town's walls only the town's swarms and birds, or those of everywhere: the same rule keeps them above)
		if (bInTown && !RDWLInTownOk(Sw)) continue;
		const float Ang = Rr.FRandRange(0.f, 2.f * PI), Dd = bBird ? Rr.FRandRange(6000.f, 22000.f) : Rr.FRandRange(1200.f, 4500.f);
		FVector P = Her + FVector(FMath::Cos(Ang), FMath::Sin(Ang), 0.f) * Dd;
		float Zg = 0.f;
		if (bReady && !(bInTown && Sw.Biomes.Contains(TEXT("town"))))
		{
			FRDWSample S; Wild->Sample(P.X / 100.0, P.Y / 100.0, S, false);
			const FString Bn = Wild->BiomeName(S.Biome);
			if (!bBird && !(Sw.Biomes.Contains(Bn) || Sw.Biomes.Contains(TEXT("*")))) continue;
			if (bBird && !(Sw.Biomes.Contains(Bn) || Sw.Biomes.Contains(TEXT("*")) || (bInTown && Sw.Biomes.Contains(TEXT("town"))))) continue;
			if (Sw.Coast != 2)
			{
				const bool bCoast = Wild->Continent(P.X / 100.0, P.Y / 100.0) < 0.03f;
				if ((Sw.Coast == 1) != bCoast) continue;
			}
			if (!bBird && S.WaterKind != 0 && !Sw.Biomes.Contains(TEXT("water"))) continue;
			Zg = Wild->ToZ(S.H);
		}
		else if (!Sw.Biomes.Contains(TEXT("town")) && !Sw.Biomes.Contains(TEXT("*"))) continue;
		else if (const ARDSection* Ts = GetSection(FIntPoint::ZeroValue)) Zg = Ts->GetActorLocation().Z + Ts->TownLiftAt(FVector2D(P));
		P.Z = Zg + Sw.Height * 100.f * (bBird ? Rr.FRandRange(0.7f, 1.4f) : 1.f);
		UNiagaraComponent* C = UNiagaraFunctionLibrary::SpawnSystemAtLocation(W, Sw.System, P, FRotator(0, Rr.FRandRange(0.f, 360.f), 0), FVector(Sw.Scale), false, true, ENCPoolMethod::None);
		if (!C) continue;
		FRDSwarmInst Si; Si.Def = K; Si.C = C; Si.At = P;
		SwarmInsts.Add(Si); ++SwarmsSpawned;
		break;          // (one new a half second)
	}
}

TArray<FString> ARDDungeonGenerator::GetWildLifeLines() const
{
	TArray<FString> Out;
	for (const ARDWildAnimal* A : WildAnimals)
		if (IsValid(A))
		{
			const FVector L = A->GetActorLocation();
			Out.Add(FString::Printf(TEXT("animal|%s|%.0f|%.0f|%.0f|%d|%.0f|%d"), WildFauna.IsValidIndex(A->Def) ? *WildFauna[A->Def].Name.ToString() : TEXT("?"), L.X, L.Y, L.Z, A->GetState(), A->GetFleeDistance(), A->GetTimesFled()));
		}
	for (const FRDSwarmInst& Si : SwarmInsts)
		if (WildSwarms.IsValidIndex(Si.Def) && Si.C.IsValid())
			Out.Add(FString::Printf(TEXT("swarm|%s|%.0f|%.0f|%.0f|%d|%d"), *WildSwarms[Si.Def].Name.ToString(), Si.At.X, Si.At.Y, Si.At.Z, WildSwarms[Si.Def].Layer, Si.C->IsActive() ? 1 : 0));
	Out.Add(FString::Printf(TEXT("counts|%d|%d|%d"), AnimalsSpawned, AnimalsFled, SwarmsSpawned));
	return Out;
}
