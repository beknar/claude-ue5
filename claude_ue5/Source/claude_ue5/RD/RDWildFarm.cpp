// The wilderness's farmsteads (the user's list of 2026-11-08b, docs/improvements9.txt: "on the farm terrain, there should also be
// farm houses, barns, fenced in animals, and farm families to go with the farms"). FRDWildWorld::FarmsteadsIn says where each
// stands (a croft field's yard); a chunk lays its farmsteads as it lays its places, each by one of the designs (since the list of
// 2026-11-11: RDWildFarm11.cpp, its buildings, pens, gardens and yard; the family at their work: the farmer tending a plot's edge,
// the farmwife by a pen's gate, a farmhand by the barn, a child by the well). F at one of them: they turn to her and say a line of
// their own (WildFarmLines). Everything is the chunk's (its components and Props): it goes with the chunk.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDTown.h"
#include "RD/RDCombat.h"
#include "RD/RDSection.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "ProceduralMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDWildFarm, Log, All);

void ARDDungeonGenerator::SpawnWildFarm(ARDWildChunk* C, const FRDWildPlace& P)
{
	if (!C || !IsWildReady()) return;
	// (the list of 2026-11-11's fourth phase: one of the designs, by the farmstead's id (RDWildFarm11.cpp); with none on the level
	// the default design, the one layout every farm had (PR #49's review: its own copy of the code here is gone))
	SpawnWildFarm11(C, P, FarmDesigns.Num() > 0 ? (int32)(FRDWildWorld::Hash(P.Id, 91, Wild->Seed) % (uint32)FarmDesigns.Num()) : -1);
}

void ARDDungeonGenerator::TickWildFarms()
{
	while (WildFarmQueue.Num() > 0)
	{
		const TPair<TWeakObjectPtr<ARDWildChunk>, FRDWildPlace> Q = WildFarmQueue[0];
		WildFarmQueue.RemoveAt(0);
		if (ARDWildChunk* C = Q.Key.Get(); IsValid(C)) { SpawnWildFarm(C, Q.Value); return; }    // (a chunk dropped before its turn: the next)
	}
}

ARDTownsfolk* ARDDungeonGenerator::WildFolkForF(const FVector& From) const
{
	// (as the town's people: within 2 m, and a door or a container of a loaded town nearer than them takes F (PR #30's review:
	// the farm folk took F before Brokenspire's rule))
	if (!bWild) return nullptr;
	ARDTownsfolk* T = NearestWildFolk(From, 200.f);
	if (!T) return nullptr;
	const float D = FVector::Dist2D(T->GetActorLocation(), From);
	if (const ARDSection* S0 = GetSection(FIntPoint::ZeroValue)) { bool bD0 = false; int32 I0 = -1; if (S0->FindNearestInteractive(From, D, bD0, I0) < D - 30.f) return nullptr; }
	return T;
}

ARDTownsfolk* ARDDungeonGenerator::NearestWildFolk(const FVector& From, float Reach) const
{
	ARDTownsfolk* Best = nullptr; float Bd = Reach;
	for (const FRDWildFarmRec& F : WildFarms)
		for (const TWeakObjectPtr<ARDTownsfolk>& W : F.Folk)
			if (ARDTownsfolk* T = W.Get(); IsValid(T))
			{
				const float D = FVector::Dist2D(T->GetActorLocation(), From);
				if (D < Bd && FMath::Abs(T->GetActorLocation().Z - From.Z) < 200.f) { Bd = D; Best = T; }
			}
	// (the list of 2026-11-11: the people the director met her with)
	for (const TWeakObjectPtr<ARDTownsfolk>& W : WildRoamFolk)
		if (ARDTownsfolk* T = W.Get(); IsValid(T))
		{
			const float D = FVector::Dist2D(T->GetActorLocation(), From);
			if (D < Bd && FMath::Abs(T->GetActorLocation().Z - From.Z) < 200.f) { Bd = D; Best = T; }
		}
	// (the list of 2026-11-10's sixth phase: the travellers on the roads)
	for (const FTraveller& G : WildTravellers)
		for (const TWeakObjectPtr<ARDTownsfolk>& W : G.Folk)
			if (ARDTownsfolk* T = W.Get(); IsValid(T))
			{
				const float D = FVector::Dist2D(T->GetActorLocation(), From);
				if (D < Bd && FMath::Abs(T->GetActorLocation().Z - From.Z) < 200.f) { Bd = D; Best = T; }
			}
	return Best;
}

TArray<FString> ARDDungeonGenerator::GetWildFarmLines() const
{
	TArray<FString> Out;
	if (!IsWildReady()) return Out;
	for (const FRDWildFarmRec& F : WildFarms)
	{
		if (!F.Chunk.IsValid()) continue;
		int32 Na = 0, Nf = 0;
		for (const TWeakObjectPtr<ARDTownAnimal>& A : F.Animals) if (A.IsValid()) ++Na;
		for (const TWeakObjectPtr<ARDTownsfolk>& T : F.Folk) if (T.IsValid()) ++Nf;
		Out.Add(FString::Printf(TEXT("farm|%d|%s|%.1f|%.1f|%.0f|%.1f|%d|%d|%d|%.0f|%.0f|%.0f|%.0f|%.1f"), F.Id, *F.Name, F.At.X, F.At.Y,
			WildGroundZ(FVector(F.At.X * 100.0, F.At.Y * 100.0, 0.0)), F.Yaw, F.Props, Na, Nf, F.PenAt.X, F.PenAt.Y, F.PenHalf.X, F.PenHalf.Y, F.PenYaw));
		for (int32 Ai = 0; Ai < F.Animals.Num(); ++Ai)
		{
			const ARDTownAnimal* A = F.Animals[Ai].Get();
			if (!A) continue;
			const FVector L = A->GetActorLocation();
			// (in the pen it was put in (the paddock or the hen run), its fence 30 cm out from the half sizes it keeps to)
			const FVector4 Pn = F.AnimalPens.IsValidIndex(Ai) ? F.AnimalPens[Ai] : FVector4(F.PenAt.X, F.PenAt.Y, F.PenHalf.X, F.PenHalf.Y);
			// (its own pen's turn: a barn's stall turns with the barn (PR #49's review))
			const float PenYaw = F.AnimalPenYaws.IsValidIndex(Ai) ? F.AnimalPenYaws[Ai] : F.PenYaw;
			const FVector Lp = FRotator(0.f, -PenYaw, 0.f).RotateVector(L - FVector(Pn.X, Pn.Y, L.Z));
			const bool bIn = FMath::Abs(Lp.X) <= Pn.Z + 30.f && FMath::Abs(Lp.Y) <= Pn.W + 30.f;
			Out.Add(FString::Printf(TEXT("animal|%d|%s|%.0f|%.0f|%.0f|%d|%d|%.0f"), F.Id, TownAnimals.IsValidIndex(A->Def) ? *TownAnimals[A->Def].Name.ToString() : TEXT("?"),
				L.X, L.Y, L.Z, bIn ? 1 : 0, A->GetState(), WildGroundZ(L)));
		}
		for (const TWeakObjectPtr<ARDTownsfolk>& Tw : F.Folk)
		{
			const ARDTownsfolk* T = Tw.Get();
			if (!T) continue;
			const FVector L = T->GetActorLocation();
			Out.Add(FString::Printf(TEXT("folk|%d|%s|%.0f|%.0f|%.0f|%s|%.0f|%s"), F.Id, *T->Title, L.X, L.Y, L.Z, *T->GetClipName(), WildGroundZ(L),
				Townsfolk.IsValidIndex(T->Def) ? *Townsfolk[T->Def].Name.ToString() : TEXT("?")));
		}
	}
	return Out;
}

FString ARDDungeonGenerator::GetWildFarmAt(float Xm, float Ym) const
{
	if (!IsWildReady()) return FString();
	FRDWFarm Fm; Wild->FarmAt(Xm, Ym, Wild->FarmWeight(Xm, Ym), Fm);
	return FString::Printf(TEXT("%d|%d,%d|%d,%d|%d|%.3f|%.4f|%.2f|%.2f|%d|%.3f|%.3f|%.3f|%.3f"), (int32)Fm.Kind, Fm.Great.X, Fm.Great.Y, Fm.Plot.X, Fm.Plot.Y, Fm.Crop, Fm.Field, Fm.Ang,
		Fm.StripW, Fm.StripOff, Fm.Strip, Fm.Furrow, Fm.Ridge, Wild->Height(Xm, Ym), Wild->BareHeight(Xm, Ym));
}

TArray<FString> ARDDungeonGenerator::FindWildFarmsteads(float Xm, float Ym, float Rm) const
{
	TArray<FString> Out;
	if (!IsWildReady()) return Out;
	TArray<FRDWildPlace> Ps;
	Wild->FarmsteadsIn(Xm - Rm, Ym - Rm, Xm + Rm, Ym + Rm, Ps);
	Ps.Sort([&](const FRDWildPlace& A, const FRDWildPlace& B) { return FVector2D::DistSquared(A.At, FVector2D(Xm, Ym)) < FVector2D::DistSquared(B.At, FVector2D(Xm, Ym)); });
	for (const FRDWildPlace& P : Ps)
		if (FVector2D::Distance(P.At, FVector2D(Xm, Ym)) <= Rm) Out.Add(FString::Printf(TEXT("%d|%s|%.1f|%.1f|%.1f"), P.Id, *P.Name, P.At.X, P.At.Y, P.Yaw));
	return Out;
}
