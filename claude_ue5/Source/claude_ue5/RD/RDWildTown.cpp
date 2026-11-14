// The wilderness's towns (the user's spec of 2026-11-03: "if the player moves 2km away from Brokenspire, Brokenspire is
// deallocated from memory"; Vel Morrath, Ashenreach and Graymourne small walled towns of Brokenspire's generator with seeds
// of their own). One town at a time is a section: section (0, 0) of the generator's grid, the grid moved to the town's
// middle (GridOrigin). A town is built (over frames) when she comes within WildTownLoadM of its middle and dropped, with its
// people, guards, animals and lights, when she is more than WildTownDropM off; what she opened there and the guards she killed
// go into the game instance (TownStore) and come back with it. Every town's ground is at the game's z 0 (FRDWildWorld: their
// regions are eased to Brokenspire's height round them), so the town code is the same wherever the town stands.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDWildChunkData.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "RD/RDMonster.h"
#include "RD/RDGameInstance.h"
#include "RD/RDCombat.h"
#include "RD/RDMistward.h"
#include "Kismet/GameplayStatics.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDWildTown, Log, All);

uint32 ARDDungeonGenerator::WildGameSeed() const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	return GI ? (uint32)GI->WildSeed : 0u;
}

bool ARDDungeonGenerator::IsInLoadedTown(const FVector& At) const
{
	if (!GetSection(FIntPoint::ZeroValue)) return false;
	const double Half = SectionTiles * TileSize * 0.5;
	return FMath::Abs(At.X - GridOrigin.X) < Half && FMath::Abs(At.Y - GridOrigin.Y) < Half;
}

bool ARDDungeonGenerator::IsInTownWalls(const FVector& At) const
{
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S || S->IsBuilding()) return false;
	return S->InsideTownBorder(FVector2D(At.X, At.Y));
}

void ARDDungeonGenerator::WildTownHole(FRDWChunkData& D) const
{
	if (!GetSection(FIntPoint::ZeroValue)) return;
	D.bTownHole = true;
	D.TownAt = FVector2D(GridOrigin.X / 100.0, GridOrigin.Y / 100.0);
	D.TownHalfM = SectionTiles * TileSize / 200.0;
}

void ARDDungeonGenerator::DropWildChunksNear(const FVector2D& AtM, double HalfM)
{
	const double Cm = WildChunkM;
	for (auto It = WildChunks.CreateIterator(); It; ++It)
	{
		const double X0 = It->Key.X * Cm, Y0 = It->Key.Y * Cm;
		if (X0 > AtM.X + HalfM + 5.0 || X0 + Cm < AtM.X - HalfM - 5.0 || Y0 > AtM.Y + HalfM + 5.0 || Y0 + Cm < AtM.Y - HalfM - 5.0) continue;
		if (It->Value) It->Value->Destroy();
		WildKept.Remove(It->Key); It.RemoveCurrent(); ++WildDropped;
	}
	// (those being computed come back with or without the hole as it was asked: dropped when they arrive; those being made
	// over frames were computed so too: dropped, asked again)
	for (const FIntPoint& C : WildInFlight) WildStale.Add(C);
	WildBuilding.RemoveAll([&](const FWildBuild& B)
	{
		if (!B.D.IsValid()) return true;
		const double X0 = B.D->Coord.X * Cm, Y0 = B.D->Coord.Y * Cm;
		if (X0 > AtM.X + HalfM + 5.0 || X0 + Cm < AtM.X - HalfM - 5.0 || Y0 > AtM.Y + HalfM + 5.0 || Y0 + Cm < AtM.Y - HalfM - 5.0) return false;
		if (TObjectPtr<ARDWildChunk>* Old = WildChunks.Find(B.D->Coord)) { if (*Old) (*Old)->Destroy(); WildChunks.Remove(B.D->Coord); WildKept.Remove(B.D->Coord); ++WildDropped; }
		return true;
	});
}

void ARDDungeonGenerator::SaveTownState()
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return;
	for (const FIntVector& K : LootedContainers) if (K.X == 0 && K.Y == 0) GI->TownLooted.AddUnique(K.Z);
	FRDTownSave& Ts = GI->TownStore.FindOrAdd(TownName);
	Ts.Seed = StartSeed; Ts.Looted = GI->TownLooted; Ts.GuardsDead = GI->GuardsDead;
}

void ARDDungeonGenerator::UnloadWildTown()
{
	if (!GetSection(FIntPoint::ZeroValue) && !bTownLoading) return;
	SaveTownState();
	CloseTownPanel();
	if (bMapOpen && !IsWildMapShown()) SetMapOpen(false);
	for (ARDTownsfolk* P : TownPeople) if (IsValid(P)) P->Destroy();
	TownPeople.Reset();
	for (ARDMonster* M : TownGuards) if (IsValid(M)) M->Destroy();
	TownGuards.Reset();
	for (ARDTownAnimal* A : TownAnimalActors) if (IsValid(A)) A->Destroy();
	TownAnimalActors.Reset();
	for (USceneComponent* C : TownSpitParts) if (IsValid(C)) C->DestroyComponent();
	for (USceneComponent* C : TownSpitTurners) if (IsValid(C)) C->DestroyComponent();
	TownSpitParts.Reset(); TownSpitTurners.Reset(); TownSpitCrank.Reset(); TownWorkBy.Reset();
	TownBldLights.Reset(); TownBldLit.Reset(); TownBldPeople.Reset(); TownLightsFor = nullptr;
	if (MistgateFx) MistgateFx->Destroy();
	if (CircleFx) CircleFx->Destroy();
	MistgateFx = nullptr; CircleFx = nullptr;
	for (auto It = LootPiles.CreateIterator(); It; ++It) if (IsValid(*It) && IsInLoadedTown((*It)->GetActorLocation()) && !(*It)->bHers) { (*It)->Destroy(); It.RemoveCurrent(); }
	if (ARDSection* S = GetSection(FIntPoint::ZeroValue)) { if (Building == S) Building = nullptr; S->Destroy(); }
	Sections.Remove(FIntPoint::ZeroValue);
	MapData.Remove(FIntPoint::ZeroValue);
	LootedContainers.Reset();
	ReleaseTownSatHold(); TownSatStep = 0; TownSatWait = 0.f; TownSatCaptures = 0;
	bTownLoading = false;
	const FVector2D At(GridOrigin.X / 100.0, GridOrigin.Y / 100.0);
	DropWildChunksNear(At, SectionTiles * TileSize / 200.0);
	UE_LOG(LogRDWildTown, Log, TEXT("RDWILD %s dropped (she is %.0f m off)"), *TownName, LoadedTownDistM);
	++WildTownsDropped;
	WildTownIdx = -1;
	WildAskTrim();
}

void ARDDungeonGenerator::LoadWildTown(int32 Ti, bool bNow)
{
	if (!IsWildReady() || !Wild->Towns.IsValidIndex(Ti)) return;
	if (GetSection(FIntPoint::ZeroValue)) UnloadWildTown();
	const FRDWildTown& T = Wild->Towns[Ti];
	URDGameInstance* GI = URDGameInstance::Of(this);
	// (the town's state in the game instance's fields while it is the current town)
	if (GI)
	{
		const FRDTownSave* Ts = GI->TownStore.Find(T.Name);
		GI->TownLooted = Ts ? Ts->Looted : TArray<int32>();
		GI->GuardsDead = Ts ? Ts->GuardsDead : TArray<int32>();
		GI->CurrentTown = T.Name;
	}
	bTownHome = T.Style == 0;
	TownName = T.Name;
	// (each town its own size and plan: Vel Morrath a holy city of the home town's size, the user's of 2026-11-06)
	SectionTiles = bTownHome ? HomeSectionTiles : T.Tiles > 0 ? T.Tiles : WildSmallTownTiles;
	TownPlan = bTownHome ? 0 : T.Plan;
	StartSeed = bTownHome ? HomeTownSeed : T.Seed;
	GridOrigin = FVector(T.Site.X * 100.0, T.Site.Y * 100.0, 0.0);
	LootedContainers.Reset();
	if (GI) for (const int32 K : GI->TownLooted) LootedContainers.Add(FIntVector(0, 0, K));
	DropWildChunksNear(T.Site, SectionTiles * TileSize / 200.0);
	WildTownIdx = Ti;
	bTownLoading = true; TownLoadStart = FPlatformTime::Seconds();
	SpawnSection(FIntPoint::ZeroValue, false, !bNow);
	UE_LOG(LogRDWildTown, Log, TEXT("RDWILD %s asked for (seed %d, %d tiles, %s)"), *TownName, StartSeed, SectionTiles, bNow ? TEXT("now") : TEXT("over frames"));
	if (bNow || !Building) FinishWildTownLoad();
}

void ARDDungeonGenerator::FinishWildTownLoad()
{
	bTownLoading = false;
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S) return;
	const bool bPlaced = true;
	AfterTownBuilt();
	// (she is where she is: a town loaded as she comes does not put her in its square)
	bTownPlaced = bPlaced;
	TownLoadSeconds = FPlatformTime::Seconds() - TownLoadStart;
	++WildTownsLoaded;
	UE_LOG(LogRDWildTown, Log, TEXT("RDWILD %s built in %.1f s"), *TownName, TownLoadSeconds);
}

void ARDDungeonGenerator::TickWildTowns(const FVector2D& AtM)
{
	if (!IsWildReady()) return;
	// the loaded one: dropped when she is far
	if (WildTownIdx >= 0 && Wild->Towns.IsValidIndex(WildTownIdx))
	{
		LoadedTownDistM = (float)FVector2D::Distance(AtM, Wild->Towns[WildTownIdx].Site);
		if (LoadedTownDistM > WildTownDropM && !bTownLoading) UnloadWildTown();
	}
	if (bTownLoading && Building == nullptr) FinishWildTownLoad();
	// the nearest: built when she comes near (one at a time: they are tens of km apart)
	if (WildTownIdx < 0 && !bTownLoading)
	{
		double D; const int32 Ti = Wild->NearestTown(AtM.X, AtM.Y, D);
		if (Ti >= 0 && D < WildTownLoadM) LoadWildTown(Ti, false);
	}
	// she is in a town: its map and minimap are the town's (the spec's "when the hero enters a town")
	if (APawn* P = UGameplayStatics::GetPlayerPawn(this, 0))
	{
		const bool bIn = IsInTownWalls(P->GetActorLocation());
		if (bIn != bInTownWalls)
		{
			bInTownWalls = bIn;
			if (bMapOpen) SetMapOpen(false);
			if (PlayerCombat && WildTownIdx >= 0) PlayerCombat->ShowMessage(bIn ? TownName : FString::Printf(TEXT("Leaving %s"), *TownName));
			if (bIn) WildAutosave(TEXT("town"));
		}
	}
}

FVector ARDDungeonGenerator::WildRespawnAt()
{
	if (!IsWildReady()) return GetStartRoomCenter();
	const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0);
	const FVector2D At = P ? FVector2D(P->GetActorLocation().X / 100.0, P->GetActorLocation().Y / 100.0) : FVector2D::ZeroVector;
	int32 Best = 0; double Bd = 1e18;
	for (int32 Ti = 0; Ti < Wild->Towns.Num(); ++Ti)
	{
		if (Ti > 0 && !WildFound.Contains(FRDWildWorld::TownIdBase + Ti)) continue;
		const double D = FVector2D::Distance(At, Wild->Towns[Ti].Site);
		if (D < Bd) { Bd = D; Best = Ti; }
	}
	if (Best != WildTownIdx || !GetSection(FIntPoint::ZeroValue) || bTownLoading) { WildDropAll(); LoadWildTown(Best, true); }
	UE_LOG(LogRDWildTown, Log, TEXT("RDWILD she comes back to life in %s (%.1f km off)"), *TownName, Bd / 1000.0);
	return GetStartRoomCenter();
}

// ------------------------------------------------------------------------------------------------ found places
void ARDDungeonGenerator::TickWildPlaces(const FVector2D& AtM)
{
	const FIntPoint C = Wild->PlaceCellOf(AtM.X, AtM.Y);
	TArray<FRDWildPlace> Ps;
	for (int32 I = -1; I <= 1; ++I) for (int32 J = -1; J <= 1; ++J) Wild->PlacesIn(C + FIntPoint(I, J), Ps);
	// (the list of 2026-11-10: "the small farm holdings should be noted on the large map": the farmsteads found as places are)
	if (bWildFarmsOnMap)
	{
		// (searched again only when her great field cell changes: the 3 x 3 cells round her (PR #43's review))
		const FIntPoint Gc(FMath::FloorToInt(AtM.X / FRDWildWorld::GreatFieldM), FMath::FloorToInt(AtM.Y / FRDWildWorld::GreatFieldM));
		if (Gc != WildFarmCell)
		{
			WildFarmCell = Gc; WildFarmNear.Reset();
			Wild->FarmsteadsIn((Gc.X - 1) * FRDWildWorld::GreatFieldM, (Gc.Y - 1) * FRDWildWorld::GreatFieldM, (Gc.X + 2) * FRDWildWorld::GreatFieldM, (Gc.Y + 2) * FRDWildWorld::GreatFieldM, WildFarmNear);
		}
		Ps.Append(WildFarmNear);
	}
	// (the list of 2026-11-12: the structures, searched again only when her site cell changes: the 3 x 3 round her)
	{
		const FIntPoint Sc = Wild->SiteCellOf(AtM.X, AtM.Y);
		if (Sc != WildSiteCell)
		{
			WildSiteCell = Sc; WildSiteNear.Reset();
			for (int32 I = -1; I <= 1; ++I) for (int32 J = -1; J <= 1; ++J) Wild->SitesIn(Sc + FIntPoint(I, J), WildSiteNear);
		}
		Ps.Append(WildSiteNear);
	}
	for (const FRDWildPlace& P : Ps)
	{
		if (WildFound.Contains(P.Id)) continue;
		const double D = FVector2D::Distance(P.At, AtM);
		const double Need = P.Town >= 0 ? SectionTiles * TileSize / 200.0 + 60.0 : WildDiscoverM;
		if (D > Need) continue;
		WildFound.Add(P.Id);
		WildLastFound = P.Name;
		if (P.Town >= 0)
			if (URDGameInstance* GI = URDGameInstance::Of(this)) GI->CirclesFound.AddUnique(FName(*P.Name));
		// (the list of 2026-11-12: a ruin's kind is told with its discovery, one line: told apart, whichever came later hid the other.
		// Only where the ruin stands at its place: one moved into the water (up to 300 m off) is told as she comes to it
		// (TickWildRuins12), not where she found the place (PR #56's review))
		const int32 RuinK = WildRuinKindOf(P);
		if (PlayerCombat && RuinK >= 0 && FVector2D::Distance(WildRuinCentre(P), P.At) < 30.f)
		{
			WildRuinsTold.Add(P.Id);
			PlayerCombat->ShowMessage(FString::Printf(TEXT("Discovered: %s. %s: %s"), *P.Name, *WildRuinKinds[RuinK].Title, *WildRuinKinds[RuinK].Text));
		}
		else if (PlayerCombat && P.Site >= 0 && WildSiteKinds.IsValidIndex(P.Site))
			PlayerCombat->ShowMessage(FString::Printf(TEXT("Discovered: %s. %s"), *WildSiteKinds[P.Site].Title, *WildSiteKinds[P.Site].Text));
		else if (const int32 LairK = WildLairCoverOf(P); PlayerCombat && LairK >= 0)
			PlayerCombat->ShowMessage(FString::Printf(TEXT("Discovered: %s. %s: %s"), *P.Name, *WildLairCovers[LairK].Title, *WildLairCovers[LairK].Text));
		else if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("Discovered: %s"), *P.Name));
		UE_LOG(LogRDWildTown, Log, TEXT("RDWILD found %s (%s) at (%.0f, %.0f)"), *P.Name, *P.Kind, P.At.X, P.At.Y);
		WildAutosave(TEXT("found"));
	}
}

FString ARDDungeonGenerator::GetWildTownState() const
{
	return FString::Printf(TEXT("%d|%s|%d|%d|%.0f|%.1f|%d|%d|%d|%.0f|%.0f|%d"), WildTownIdx, *TownName, bTownLoading ? 1 : 0, GetSection(FIntPoint::ZeroValue) ? 1 : 0, LoadedTownDistM,
		TownLoadSeconds, WildTownsLoaded, WildTownsDropped, bInTownWalls ? 1 : 0, GridOrigin.X, GridOrigin.Y, bTownHome ? 1 : 0);
}
