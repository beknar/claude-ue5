// The user's list of 2026-11-16 (docs/improvements14.txt; the plan docs/improvements14_plan.md), its seventh phase's second part:
// "in the wilderness, enable the ability to kill farm animals and loot them - crafting items, food, can be found" (item 12). A
// farmstead's animal (its def's Health over 0, 929) takes her blows and bolts, starts away when struck, falls on its side when
// killed, and leaves its def's things; its key in the game's WildKilled keeps it dead when its farm is laid again.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDTown.h"
#include "RD/RDGameInstance.h"
#include "RD/RDWild.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/BoxComponent.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDFarmAnimal14, Log, All);

// (a range of WildKilled's own: (10 << 40) + the farm's place among the farms (its id less FarmIdBase) x 131072 + its pen's place
// in the farm (a yard pen's 0-2047, a stall's 2048 on) x 32 + its index in the pen; the ranges below are the farms' containers (1),
// houses' (2), ruins' (3), lairs' (4), sites' (5, 6), scenery's (7, 8), herds' (9))
static constexpr int64 RDFarmAnimalKeys14 = 10LL << 40;

int64 ARDDungeonGenerator::FarmAnimalKey14(const FRDWildFarmRec& Rec, int32 Slot, int32 K) const
{
	return RDFarmAnimalKeys14 + (int64)(uint32)(Rec.Id - FRDWildWorld::FarmIdBase) * 131072 + (int64)(Slot & 4095) * 32 + (K & 31);
}

void ARDDungeonGenerator::ReadFarmKilled14(int32 FarmId)
{
	// (one pass over the game's kept kills for a farm about to be laid, its own range only (PR #85's review: a search of the whole
	// list for each animal))
	FarmKilled14.Reset(); FarmKilledFor14 = FarmId;
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return;
	const int64 Lo = RDFarmAnimalKeys14 + (int64)(uint32)(FarmId - FRDWildWorld::FarmIdBase) * 131072, Hi = Lo + 131072;
	for (const int64 K : GI->WildKilled) if (K >= Lo && K < Hi) FarmKilled14.Add(K);
}

bool ARDDungeonGenerator::IsFarmAnimalKilled14(int64 Key) const
{
	return FarmKilled14.Contains(Key);
}

bool ARDTownAnimal::CanBeHurt14() const
{
	return !bDead14 && bWildGround && FarmKey14 >= 0 && Health14 > 0.f;
}

FVector ARDTownAnimal::BodyCenter14() const
{
	return Collider ? Collider->GetComponentLocation() : GetActorLocation() + FVector(0, 0, 40.f);
}

float ARDTownAnimal::BodyRadius14() const
{
	return Collider ? (float)FMath::Max(Collider->GetScaledBoxExtent().X, Collider->GetScaledBoxExtent().Y) : 40.f;
}

bool ARDTownAnimal::TakeHit14(float Dmg, FVector From)
{
	if (!CanBeHurt14() || !Gen || !GetWorld()) return false;
	const float Now = GetWorld()->GetTimeSeconds();
	Health14 -= FMath::Max(Dmg, 0.f);
	if (Health14 > 0.f)
	{
		// (struck and alive: it starts away from her, quick, within its pen (as a loose hen runs from her))
		FVector Aw = GetActorLocation() - From; Aw.Z = 0.f;
		SetState(2, Now);
		const FVector L = GetActorLocation();
		const FVector Lp = FRotator(0.f, -PenYaw, 0.f).RotateVector((L + Aw.GetSafeNormal() * 180.f) - PenAt);
		// (kept its body's half length off the fence, as its walks (SetState): PR #85's review, clamped to the pen's own half it ran into the fence)
		const float Hb = Gen->TownAnimals.IsValidIndex(Def) ? Gen->TownAnimals[Def].HalfSize.X : 40.f;
		const FVector2D Hm = (PenHalf - FVector2D(Hb, Hb)).ComponentMax(FVector2D(5.f, 5.f));
		const FVector Cl(FMath::Clamp(Lp.X, -Hm.X, Hm.X), FMath::Clamp(Lp.Y, -Hm.Y, Hm.Y), 0.f);
		To = PenAt + FRotator(0.f, PenYaw, 0.f).RotateVector(Cl); To.Z = L.Z;
		Until = Now + 3.f; FleeUntil = Now + 1.2f; ++Flees;
		Body->SetPlayRate(2.5f);
		return false;
	}
	// (killed: its pose held, it falls on its side over half a second, its things by it; it no longer stops her)
	bDead14 = true; DeadAt14 = Now; Health14 = 0.f;
	FallYaw14 = R.RandBool() ? 90.f : -90.f;
	Body->bPauseAnims = true;
	if (Collider) Collider->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Gen->OnFarmAnimalKilled14(this);
	return true;
}

void ARDTownAnimal::TickDead14(float Now)
{
	if (!Gen || !Gen->TownAnimals.IsValidIndex(Def)) return;
	const FRDTownAnimalDef& D = Gen->TownAnimals[Def];
	const float T = FMath::Clamp((Now - DeadAt14) / 0.5f, 0.f, 1.f);
	const float E = T * T * (3.f - 2.f * T);
	// (rolled about its facing (the actor's X), after the mesh's own yaw (the wild animals' rule, PR #27's review))
	Body->SetRelativeRotation(FQuat(FVector(1, 0, 0), FMath::DegreesToRadians(FallYaw14 * E)) * FRotator(0.f, D.MeshYaw, 0.f).Quaternion());
	// (lying, its middle comes down to about a third of its height: its box's half height)
	const float Hh = Collider ? (float)Collider->GetUnscaledBoxExtent().Z : 30.f;
	Body->SetRelativeLocation(FVector(0, 0, Hh * 0.5f * E));
}

void ARDDungeonGenerator::OnFarmAnimalKilled14(ARDTownAnimal* A)
{
	if (!A || !TownAnimals.IsValidIndex(A->Def)) return;
	const FRDTownAnimalDef& D = TownAnimals[A->Def];
	++FarmAnimalsKilled14;
	// (killed by no doing of hers (lightning: bWildPredatorKill, as the wild animals'): not kept, no things)
	if (bWildPredatorKill) { LastFarmAnimalDrops14.Reset(); return; }
	if (URDGameInstance* GI = URDGameInstance::Of(this); GI && A->FarmKey14 >= 0) GI->WildKilled.AddUnique(A->FarmKey14);
	// (its things: each "Item|min|max|chance", drawn from a hash of its key (no stream of the play's): the same farm's same animal
	// leaves the same)
	TArray<FString> Lines; D.Drops.ParseIntoArray(Lines, TEXT(";"), true);
	const TArray<FName> Got = RollDropLines(Lines, HashCombine(GetTypeHash(A->FarmKey14), 0xFA4Du ^ (uint32)(IsWildReady() ? Wild->Seed : 0u)));
	LastFarmAnimalDrops14 = Got;
	if (Got.Num() > 0) DropHarvest(A->GetActorLocation() + FVector(0, 0, 10.f), Got, 1);
	UE_LOG(LogRDFarmAnimal14, Log, TEXT("RDFARMANIMAL %s killed (%lld): %s"), *D.Name.ToString(), A->FarmKey14,
		Got.Num() ? *FString::JoinBy(Got, TEXT(", "), [](const FName& N) { return N.ToString(); }) : TEXT("nothing"));
}

int32 ARDDungeonGenerator::HitFarmAnimalsInArc14(const FVector& L, const FVector& Fw, float Reach, float MinCos, float Dmg, FName Sound)
{
	// (as the wild animals' (HitWildAnimalsInArc): within her weapon's reach and its arc, or close)
	int32 N = 0;
	for (const FRDWildFarmRec& F : WildFarms)
		for (const TWeakObjectPtr<ARDTownAnimal>& W : F.Animals)
		{
			ARDTownAnimal* A = W.Get();
			if (!IsValid(A) || !A->CanBeHurt14()) continue;
			const FVector C = A->BodyCenter14();
			const FVector D = (C - L) * FVector(1, 1, 0);
			const float Dist = D.Size() - A->BodyRadius14();
			if (Dist > Reach || FMath::Abs(C.Z - L.Z) > 220.f) continue;
			if (Dist > 40.f && FVector::DotProduct(D.GetSafeNormal(), Fw) < MinCos) continue;
			if (!Sound.IsNone()) PlaySoundAt(Sound, C);
			AddHitText(C + FVector(0, 0, 40.f), Dmg, false);
			A->TakeHit14(Dmg, L);
			++N;
		}
	return N;
}

ARDTownAnimal* ARDDungeonGenerator::FarmAnimalOnSegment14(const FVector& A, const FVector& B, float Pad, float& OutT, FVector& OutAt) const
{
	ARDTownAnimal* Best = nullptr; OutT = 2.f;
	const FVector Ab = B - A;
	const float L2 = Ab.SizeSquared();
	for (const FRDWildFarmRec& F : WildFarms)
		for (const TWeakObjectPtr<ARDTownAnimal>& W : F.Animals)
		{
			ARDTownAnimal* An = W.Get();
			if (!IsValid(An) || !An->CanBeHurt14()) continue;
			const FVector C = An->BodyCenter14();
			const float T = L2 > 1e-4f ? FMath::Clamp(FVector::DotProduct(C - A, Ab) / L2, 0.f, 1.f) : 0.f;
			const FVector P = A + Ab * T;
			if (FVector::Dist(P, C) > An->BodyRadius14() + Pad || T >= OutT) continue;
			OutT = T; Best = An; OutAt = P;
		}
	return Best;
}

TArray<FName> ARDDungeonGenerator::RollDropLines(const TArray<FString>& Lines, uint32 H0) const
{
	// ("Item|min|max|chance" each, drawn from a hash (no stream of the play's): one roll for the wild animals' and the farms' things
	// (PR #85's review))
	TArray<FName> Got;
	for (int32 K = 0; K < Lines.Num(); ++K)
	{
		TArray<FString> P; Lines[K].ParseIntoArray(P, TEXT("|"), false);
		if (P.Num() < 1 || P[0].IsEmpty() || FindItem(FName(*P[0])) < 0) continue;
		const int32 Lo = P.Num() > 1 ? FCString::Atoi(*P[1]) : 1, Hi = P.Num() > 2 ? FCString::Atoi(*P[2]) : Lo;
		const float Ch = P.Num() > 3 ? FCString::Atof(*P[3]) : 1.f;
		const float U = (HashCombine(H0, (uint32)K * 7919u + 1u) % 100003u) / 100003.f;
		if (U >= Ch) continue;
		const int32 N = Lo + (int32)(HashCombine(H0, (uint32)K * 104729u + 2u) % (uint32)FMath::Max(Hi - Lo + 1, 1));
		for (int32 I = 0; I < N; ++I) Got.Add(FName(*P[0]));
	}
	return Got;
}
