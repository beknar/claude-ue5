// The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), its tenth phase: landmarks and
// lookouts (docs/wilderness_ideas.md's ideas 1 and 2, the user's choice of "all the wild ideas but climbing").
//   - Lookouts: a watchtower in each region's cell (the world's CellM), the Old Watchtower's build (Brokenspire's round tower's
//     quarters, its spiral stair: RDWildPlaces.cpp, FitWildTower); reaching its top marks the region's places on her map as places
//     she has not been to (seen at half strength, no travel there), kept with the game.
//   - Regional landmarks: in each region's cell one tall thing of its own kind, by the region (a great tree, a smoking crater, a stone
//     with a beam of light by night, a lighthouse), drawn from far and never culled, the nearest within RegionLandmarkKm15 laid round
//     her; the open lands keep their broken towers (RDWildScenery13.cpp).
//   - At night: the travellers' camps a column of smoke over their fire, the villages' houses a light in their room until bed.
// Every one is placed on a stream of its own, after and clear of everything else, so no village, place, structure or scenery moves.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDGameInstance.h"
#include "RD/RDCombat.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/Character.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList15i, Log, All);

// ================================================================================================ the lookouts' places (the world's)
static const TCHAR* RDL15LookoutNames[] = { TEXT("Grey"), TEXT("Windy"), TEXT("Raven's"), TEXT("Hollow"), TEXT("Kestrel"), TEXT("Weathered"), TEXT("High"),
	TEXT("Lone"), TEXT("Watchman's"), TEXT("Ash"), TEXT("Crow's"), TEXT("Old Sentry's"), TEXT("Falcon"), TEXT("Thornwatch"), TEXT("Stormward"), TEXT("Beacon") };

bool FRDWildWorld::LookoutOf(FIntPoint Cell, FRDWildPlace& Out) const
{
	{
		FScopeLock Lk(&LookoutCache->Lock);
		if (const FRDWildPlace* Got = LookoutCache->Cells.Find(Cell)) { Out = *Got; return Got->Id != 0; }
	}
	FRDWildPlace L; L.Id = 0;
	const double X0 = Xs + Cell.X * CellM, Y0 = Yw + Cell.Y * CellM;
	if (Cell.X >= 0 && Cell.Y >= 0 && Cell.X < 1024 && Cell.Y < 1024 && X0 + CellM <= Xn && Y0 + CellM <= Ye)
		for (int32 Try = 0; Try < 10 && L.Id == 0; ++Try)
		{
			const FVector2D S(X0 + (0.2 + 0.6 * Rand01(Cell.X * 17 + Try, Cell.Y, Seed + 1501u)) * CellM, Y0 + (0.2 + 0.6 * Rand01(Cell.X, Cell.Y * 17 + Try, Seed + 1502u)) * CellM);
			FRDWSample Q; Sample(S.X, S.Y, Q, false);
			if (Q.WaterKind != 0 || Q.Road > 0.02f || Q.Lava > 0.02f || Q.Field > 0.05f || Q.FarmKind != 0 || Q.Chan > 0.f || Q.Terrace > 0.f) continue;
			double Dt = 1e12; NearestTown(S.X, S.Y, Dt);
			if (Dt < 1500.0) continue;
			// (gentle: the ground within 6 m of its middle within 2.5 m of it)
			const double H0 = Height(S.X, S.Y);
			bool bSteep = false;
			for (int32 K = 0; K < 8 && !bSteep; ++K) bSteep = FMath::Abs(Height(S.X + 6.0 * FMath::Cos(K * PI / 4.0), S.Y + 6.0 * FMath::Sin(K * PI / 4.0)) - H0) > 2.5;
			if (bSteep) continue;
			// (150 m from everything placed before it: the places and villages, the structures, the points of interest, the scenery, the
			// farmsteads, the quests' places (PR #102's review: the ring of cells is the whole 150 m, the points of interest's 76 m cells too))
			if (!ClearOfPlaces15(S, 150.0, false)) continue;
			L.Id = LookoutIdBase + ((Cell.X & 0x3FF) << 10 | (Cell.Y & 0x3FF));
			L.Kind = TEXT("lookout");
			L.Name = FString::Printf(TEXT("%s Lookout"), RDL15LookoutNames[Hash(Cell.X, Cell.Y, Seed + 1503u) % UE_ARRAY_COUNT(RDL15LookoutNames)]);
			L.At = S; L.H = (float)H0; L.Tier = TierAt(S.X, S.Y); L.Biome = Q.Biome;
			L.Yaw = (float)(Hash(Cell.X, Cell.Y, Seed + 1504u) % 360u);
		}
	FScopeLock Lk(&LookoutCache->Lock);
	LookoutCache->Cells.Add(Cell, L);
	Out = L;
	return L.Id != 0;
}

bool FRDWildWorld::ClearOfPlaces15(const FVector2D& S, double R, bool bLookouts) const
{
	TArray<FRDWildPlace> Near;
	auto Ring = [&](double CellSize) { return FMath::CeilToInt(R / CellSize); };
	const FIntPoint Pc = PlaceCellOf(S.X, S.Y), Sc = SiteCellOf(S.X, S.Y), Qc = PoiCellOf(S.X, S.Y), Ec = SceneryCellOf(S.X, S.Y);
	for (int32 N = Ring(PlaceCellM), I = -N; I <= N; ++I) for (int32 J = -N; J <= N; ++J) PlacesIn(Pc + FIntPoint(I, J), Near);
	for (int32 N = Ring(SiteCellM), I = -N; I <= N; ++I) for (int32 J = -N; J <= N; ++J) SitesIn(Sc + FIntPoint(I, J), Near);
	for (int32 N = Ring(PoiCellM), I = -N; I <= N; ++I) for (int32 J = -N; J <= N; ++J) PoisIn(Qc + FIntPoint(I, J), Near);
	for (int32 N = Ring(SceneryCellM), I = -N; I <= N; ++I) for (int32 J = -N; J <= N; ++J) SceneryIn(Ec + FIntPoint(I, J), Near);
	FarmsteadsIn(S.X - R - 60.0, S.Y - R - 60.0, S.X + R + 60.0, S.Y + R + 60.0, Near);
	Near.Append(QuestPlaces);
	if (bLookouts)
	{
		const FIntPoint Lc = LookoutCellOf(S.X, S.Y);
		for (int32 I = -1; I <= 1; ++I) for (int32 J = -1; J <= 1; ++J) { FRDWildPlace L; if (LookoutOf(Lc + FIntPoint(I, J), L)) Near.Add(L); }
	}
	return !Near.ContainsByPredicate([&](const FRDWildPlace& P) { return FVector2D::Distance(P.At, S) < R; });
}

void FRDWildWorld::LookoutsIn(double X0, double Y0, double X1, double Y1, TArray<FRDWildPlace>& Out) const
{
	const FIntPoint C0 = LookoutCellOf(X0, Y0), C1 = LookoutCellOf(X1, Y1);
	for (int32 I = C0.X; I <= C1.X; ++I) for (int32 J = C0.Y; J <= C1.Y; ++J)
	{
		FRDWildPlace L;
		if (LookoutOf(FIntPoint(I, J), L) && L.At.X >= X0 && L.At.X < X1 && L.At.Y >= Y0 && L.At.Y < Y1) Out.Add(L);
	}
}

// ================================================================================================ the lookouts in play
void ARDDungeonGenerator::NoteLookoutTop15(const FRDWildPlace& P, const FVector& Mid, float TopZ)
{
	WildLookoutTops15.Add(P.Id, FVector(Mid.X, Mid.Y, TopZ));
}

void ARDDungeonGenerator::TickLookouts15(float Dt, const FVector& Her)
{
	LookoutLook15 -= Dt;
	if (LookoutLook15 > 0.f || !IsWildReady()) return;
	LookoutLook15 = 0.5f;
	const FVector2D H2(Her.X / 100.0, Her.Y / 100.0);
	const FIntPoint Lc = Wild->LookoutCellOf(H2.X, H2.Y);
	for (int32 I = -1; I <= 1; ++I) for (int32 J = -1; J <= 1; ++J)
	{
		FRDWildPlace L;
		if (!Wild->LookoutOf(Lc + FIntPoint(I, J), L)) continue;
		const double D = FVector2D::Distance(L.At, H2);
		// (found as she comes within 120 m: a place of the map's (travel there once found))
		if (D < 120.0 && !WildFound.Contains(L.Id))
		{
			WildFound.Add(L.Id); WildLastFound = L.Name;
			if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("Discovered: %s (a lookout: climb it to see the land round it)"), *L.Name));
			WildAutosave(TEXT("found"));          // (as every other discovery (PR #102's review))
		}
		// (its top reached: her middle within 3.0 m of its middle (its floor's ring) and her feet over its top less 1.5 m)
		const FVector* Top = WildLookoutTops15.Find(L.Id);
		if (!Top || D > 3.0) continue;
		const ACharacter* Ch = Cast<ACharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
		const float Feet = Her.Z - (Ch && Ch->GetCapsuleComponent() ? Ch->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() : 90.f);
		if (Feet < Top->Z - 150.f) continue;
		ClimbLookout15(L);
	}
}

int32 ARDDungeonGenerator::ClimbLookout15(const FRDWildPlace& L)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (LookoutsClimbed15.Contains(L.Id)) return 0;
	LookoutsClimbed15.Add(L.Id);
	if (GI) GI->WildLookoutsClimbed15.AddUnique(L.Id);
	WildFound.Add(L.Id);
	// (the region: the lookout's cell; its places, villages, ruins, lairs and caves (PlacesIn) and its structures (SitesIn), not the
	// towns, farmsteads, small points of interest or scenery)
	const double X0 = Wild->Xs + Wild->LookoutCellOf(L.At.X, L.At.Y).X * Wild->CellM, Y0 = Wild->Yw + Wild->LookoutCellOf(L.At.X, L.At.Y).Y * Wild->CellM;
	const double X1 = X0 + Wild->CellM, Y1 = Y0 + Wild->CellM;
	TArray<FRDWildPlace> Ps;
	const FIntPoint P0 = Wild->PlaceCellOf(X0, Y0), P1 = Wild->PlaceCellOf(X1, Y1);
	for (int32 I = P0.X; I <= P1.X; ++I) for (int32 J = P0.Y; J <= P1.Y; ++J) Wild->PlacesIn(FIntPoint(I, J), Ps);
	const FIntPoint S0 = Wild->SiteCellOf(X0, Y0), S1 = Wild->SiteCellOf(X1, Y1);
	for (int32 I = S0.X; I <= S1.X; ++I) for (int32 J = S0.Y; J <= S1.Y; ++J) Wild->SitesIn(FIntPoint(I, J), Ps);
	int32 N = 0;
	for (const FRDWildPlace& P : Ps)
	{
		if (P.Town >= 0 || P.Kind == TEXT("farmstead") || P.At.X < X0 || P.At.X >= X1 || P.At.Y < Y0 || P.At.Y >= Y1) continue;
		if (WildFound.Contains(P.Id) || WildMarked15.Contains(P.Id)) continue;
		WildMarked15.Add(P.Id); ++N;
		if (GI) GI->WildMarked15.AddUnique(P.Id);
	}
	LastLookoutMarked15 = N;
	WildMarkedCacheFor15 = -1;          // (the map's list of them made again)
	WildAutosave(TEXT("found"));          // (the lookout and its marks kept at once (PR #102's review))
	if (PlayerCombat) PlayerCombat->ShowMessage(N > 0 ? FString::Printf(TEXT("From the top of %s you see the land round it: %d places marked on your map"), *L.Name, N)
		: FString::Printf(TEXT("From the top of %s you see the land round it: nothing you do not know already"), *L.Name));
	UE_LOG(LogRDList15i, Log, TEXT("RDLOOKOUT15 %s climbed (%d): %d places marked"), *L.Name, L.Id, N);
	return N;
}

TArray<FString> ARDDungeonGenerator::GetLookouts15(float Km) const
{
	TArray<FString> Out;
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Her || !IsWildReady()) return Out;
	const FVector2D H2(Her->GetActorLocation().X / 100.0, Her->GetActorLocation().Y / 100.0);
	const int32 R = FMath::CeilToInt(Km * 1000.0 / Wild->CellM);
	const FIntPoint Lc = Wild->LookoutCellOf(H2.X, H2.Y);
	for (int32 I = -R; I <= R; ++I) for (int32 J = -R; J <= R; ++J)
	{
		FRDWildPlace L;
		if (!Wild->LookoutOf(Lc + FIntPoint(I, J), L) || FVector2D::Distance(L.At, H2) > Km * 1000.0) continue;
		const FVector* Top = WildLookoutTops15.Find(L.Id);
		const FIntPoint C = Wild->LookoutCellOf(L.At.X, L.At.Y);
		Out.Add(FString::Printf(TEXT("%d|%s|%.1f|%.1f|%.0f|%d|%d|%d|%d|%d"), L.Id, *L.Name, L.At.X, L.At.Y, Top ? Top->Z : -1.f, LookoutsClimbed15.Contains(L.Id) ? 1 : 0,
			WildFound.Contains(L.Id) ? 1 : 0, C.X, C.Y, L.Tier));
	}
	return Out;
}

bool ARDDungeonGenerator::IsWildMarked15(int32 Id) const { return WildMarked15.Contains(Id); }

TArray<FString> ARDDungeonGenerator::GetWildMarkedLines15() const
{
	TArray<FString> Out;
	if (!IsWildReady()) return Out;
	for (const int32 Id : WildMarked15)
	{
		FRDWildPlace P;
		if (!Wild->FindPlace(Id, P)) { Out.Add(FString::Printf(TEXT("%d|?|?|0|0|0|0|%d"), Id, WildFound.Contains(Id) ? 1 : 0)); continue; }
		const FIntPoint C = Wild->LookoutCellOf(P.At.X, P.At.Y);
		Out.Add(FString::Printf(TEXT("%d|%s|%s|%.0f|%.0f|%d|%d|%d"), Id, *P.Kind, *P.Name, P.At.X, P.At.Y, C.X, C.Y, WildFound.Contains(Id) ? 1 : 0));
	}
	return Out;
}

TArray<int32> ARDDungeonGenerator::GetWildKnownIds15() const
{
	TArray<FRDWildPlace> Ps; WildKnownPlaces(Ps);
	TArray<int32> Out; for (const FRDWildPlace& P : Ps) Out.Add(P.Id);
	return Out;
}

TArray<int32> ARDDungeonGenerator::GetWildMarked15() const { return WildMarked15.Array(); }

void ARDDungeonGenerator::LoadLookouts15()
{
	WildMarked15.Reset(); LookoutsClimbed15.Reset(); WildMarkedCacheFor15 = -1;
	if (const URDGameInstance* GI = URDGameInstance::Of(this))
	{
		for (const int32 Id : GI->WildMarked15) WildMarked15.Add(Id);
		for (const int32 Id : GI->WildLookoutsClimbed15) LookoutsClimbed15.Add(Id);
	}
}

// ================================================================================================ the regions' landmarks
bool ARDDungeonGenerator::IsWildNight15() const
{
	// (one night for every rule of the phase: the sky's (the aurora's and the scenery's "night", 20:00 to 5:30))
	return TownHour >= 20.f || TownHour < 5.5f;
}

bool ARDDungeonGenerator::IsHouseLightHour15() const
{
	// (one rule for the houses' lights, made and looked at (PR #102's review): from dusk to the household's bed, and before dawn)
	return (TownHour >= 18.5f && TownHour < 21.f) || (TownHour >= 5.f && TownHour < 6.5f);
}

void ARDDungeonGenerator::ParseRegionLandmarks15() const
{
	// (the lines parsed once (PR #102's review: every landmark a parse of every line, every 2 s))
	if (RegionLandmarkParsedFor15 == RegionLandmarkLines15.Num()) return;
	RegionLandmarkParsed15.Reset();
	for (const FString& Ln : RegionLandmarkLines15)
	{
		TArray<FString> F; Ln.ParseIntoArray(F, TEXT("|"), false);
		FRegionLandmarkKind15 K;
		auto Num = [&](int32 I, float Def) { return F.IsValidIndex(I) && !F[I].IsEmpty() ? FCString::Atof(*F[I]) : Def; };
		K.Name = F.IsValidIndex(0) ? F[0] : FString(TEXT("?"));
		if (F.IsValidIndex(1)) F[1].ParseIntoArray(K.Biomes, TEXT(";"));
		K.Main = (int32)Num(2, -1.f); K.Height = Num(3, 100.f); K.Extra = (int32)Num(4, -1.f); K.ExtraHeight = Num(5, 100.f); K.ExtraWidth = Num(6, 10.f);
		K.bNight = Num(7, 0.f) > 0.5f; K.Mat = (int32)Num(8, -1.f); K.Sink = Num(9, 2.f);
		RegionLandmarkParsed15.Add(MoveTemp(K));
	}
	RegionLandmarkParsedFor15 = RegionLandmarkLines15.Num();
	RegionLandmarkSites15.Reset();
}

void ARDDungeonGenerator::TickRegionLandmarks15(float Dt, const FVector& Her)
{
	RegionLandmarkLook15 -= Dt;
	if (RegionLandmarkLook15 > 0.f || !IsWildReady() || RegionLandmarkLines15.Num() == 0) return;
	RegionLandmarkLook15 = 2.f;
	ParseRegionLandmarks15();
	const FVector2D H2(Her.X / 100.0, Her.Y / 100.0);
	const double Reach = RegionLandmarkKm15 * 1000.0;
	const int32 R = FMath::CeilToInt(Reach / Wild->CellM);
	const FIntPoint Lc = Wild->LookoutCellOf(H2.X, H2.Y);
	const bool bNight = IsWildNight15();
	TSet<FIntVector> Want;
	// (two in each region's cell ("one or two tall silhouettes"): from the first hilltops, ridges hid a cell's one in the mountains)
	for (int32 I = -R; I <= R; ++I) for (int32 J = -R; J <= R; ++J) for (int32 Slot = 0; Slot < 2; ++Slot)
	{
		const FIntVector Key(Lc.X + I, Lc.Y + J, Slot);
		FRegionLandmark15 Lm;
		if (!RegionLandmarkOf15(FIntPoint(Key.X, Key.Y), Slot, Lm) || FVector2D::Distance(Lm.At, H2) > Reach) continue;
		Want.Add(Key);
		// (laid once, when it comes within reach (PR #102's review: one whose main piece failed was laid again every 2 s, its extra each time))
		FRegionLandmark15* Have = RegionLandmarks15.Find(Key);
		if (!Have) { Have = &RegionLandmarks15.Add(Key, Lm); LayRegionLandmark15(*Have); }
		// (the night's part (a beam, a lighthouse's lamp) shown from dusk to dawn)
		if (UStaticMeshComponent* X = Have->Extra.Get(); X && Have->bExtraNight && X->IsVisible() != bNight) X->SetVisibility(bNight);
	}
	for (auto It = RegionLandmarks15.CreateIterator(); It; ++It)
		if (!Want.Contains(It.Key()))
		{
			if (UStaticMeshComponent* M = It.Value().Main.Get()) M->DestroyComponent();
			if (UStaticMeshComponent* X = It.Value().Extra.Get()) X->DestroyComponent();
			It.RemoveCurrent();
		}
	// (the open lands: every broken tower within reach stands, not only the nearest (TickWildLandmark13 lays that one whole, with its
	// cave's mouth); the others as they are seen from afar, solid; within WildLandmarkKm none is a silhouette (PR #102's review: she could
	// walk to a far tower with no mouth while the kept nearest one was another): the nearest is switched as she comes (TickWildLandmark13))
	TSet<FIntPoint> WantT;
	if (WildLandmarkMesh && WildLandmarkBiomes.Num() > 0)
	{
		const int32 Rt = FMath::CeilToInt(Reach / WildLandmarkCellM);
		const int32 Ci = FMath::FloorToInt(H2.X / WildLandmarkCellM), Cj = FMath::FloorToInt(H2.Y / WildLandmarkCellM);
		for (int32 I = Ci - Rt; I <= Ci + Rt; ++I) for (int32 J = Cj - Rt; J <= Cj + Rt; ++J)
		{
			FVector2D S;
			if (!WildTowerSite13(I, J, S) || FVector2D::Distance(S, H2) > Reach || FVector2D::Distance(S, WildLandmarkAt) < 1.0) continue;
			const FIntPoint K(I, J);
			WantT.Add(K);
			if (FarTowers15.Contains(K) && FarTowers15[K].IsValid()) continue;
			UStaticMeshComponent* Lm = NewObject<UStaticMeshComponent>(this);
			Lm->SetStaticMesh(WildLandmarkMesh);
			Lm->SetMobility(EComponentMobility::Movable); Lm->SetCullDistance(0.f); Lm->bNeverDistanceCull = true;
			Lm->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics); Lm->SetCollisionResponseToAllChannels(ECR_Block);
			Lm->RegisterComponent();
			Lm->SetWorldLocation(FVector(S.X * 100.0, S.Y * 100.0, Wild->ToZ(Wild->Height(S.X, S.Y)) - 200.f));
			Lm->SetWorldRotation(FRotator(0.f, (float)(FRDWildWorld::Hash((int32)S.X, (int32)S.Y, Wild->Seed) % 360u), 0.f));
			FarTowers15.Add(K, Lm);
		}
	}
	for (auto It = FarTowers15.CreateIterator(); It; ++It)
		if (!WantT.Contains(It.Key()) || !It.Value().IsValid())
		{
			if (UStaticMeshComponent* M = It.Value().Get()) M->DestroyComponent();
			It.RemoveCurrent();
		}
}

bool ARDDungeonGenerator::RegionLandmarkOf15(FIntPoint Cell, int32 Slot, FRegionLandmark15& Out) const
{
	// (one in each half of each region's cell, at a spot of its own stream, of the kind its region asks (a line's biomes), on dry ground off
	// the roads and fields, 2.5 km from a town and 160 m from every place, structure, point of interest, scenery, farmstead, quest's place
	// and lookout (PR #102's review: a 60 m crater could bury a village); worked out once a cell and slot (a pure function of the seed);
	// the open lands' kind is none: their broken towers stand in every 6 km square)
	const FIntVector Key(Cell.X, Cell.Y, Slot);
	if (const FRegionLandmark15* Got = RegionLandmarkSites15.Find(Key)) { Out = *Got; return Got->Line >= 0; }
	FRegionLandmark15 L;
	const FRDWildWorld& W = *Wild;
	const double X0 = W.Xs + Cell.X * W.CellM, Y0 = W.Yw + Cell.Y * W.CellM;
	if (X0 >= W.Xs && Y0 >= W.Yw && X0 + W.CellM <= W.Xn && Y0 + W.CellM <= W.Ye)
		for (int32 Try = 0; Try < 6 && L.Line < 0; ++Try)
		{
			// (each slot a half of the cell (west, east), so the two stand apart)
			const FVector2D S(X0 + (0.5 * Slot + 0.08 + 0.34 * FRDWildWorld::Rand01(Cell.X * 13 + Try, Cell.Y, W.Seed + 1601u + 7u * Slot)) * W.CellM, Y0 + (0.12 + 0.76 * FRDWildWorld::Rand01(Cell.X, Cell.Y * 13 + Try, W.Seed + 1602u + 7u * Slot)) * W.CellM);
			FRDWSample Q; W.Sample(S.X, S.Y, Q, false);
			const FString Bn = W.BiomeName(Q.Biome);
			const int32 Line = RegionLandmarkParsed15.IndexOfByPredicate([&](const FRegionLandmarkKind15& K) { return K.Biomes.Contains(Bn); });
			if (Line < 0) break;          // (a region with no kind of its own: the open lands)
			if (Q.WaterKind != 0 || Q.Lava > 0.05f || Q.Road > 0.02f || Q.Field > 0.05f) continue;
			// (its foot's ring clear of roads, water and fields too: the pieces are up to 110 m across)
			bool bRing = true;
			for (int32 K = 0; K < 8 && bRing; ++K)
			{
				FRDWSample Qr; W.Sample(S.X + 70.0 * FMath::Cos(K * PI / 4.0), S.Y + 70.0 * FMath::Sin(K * PI / 4.0), Qr, false);
				bRing = Qr.WaterKind == 0 && Qr.Road <= 0.02f && Qr.Field <= 0.05f;
			}
			if (!bRing) continue;
			double Dt = 1e12; W.NearestTown(S.X, S.Y, Dt);
			if (Dt < 2500.0 || !W.ClearOfPlaces15(S, 160.0, true)) continue;
			L.Line = Line; L.At = S; L.Z = W.ToZ(W.Height(S.X, S.Y));
			L.Yaw = (float)(FRDWildWorld::Hash(Cell.X, Cell.Y, W.Seed + 1603u + 7u * Slot) % 360u);
		}
	RegionLandmarkSites15.Add(Key, L);
	Out = L;
	return L.Line >= 0;
}

void ARDDungeonGenerator::LayRegionLandmark15(FRegionLandmark15& Lm)
{
	if (!RegionLandmarkParsed15.IsValidIndex(Lm.Line)) return;
	const FRegionLandmarkKind15& K = RegionLandmarkParsed15[Lm.Line];
	auto Make = [&](UStaticMesh* Mesh, UMaterialInterface* Mat, const FVector& At, float Yaw, const FVector& Scale, bool bCollide) -> UStaticMeshComponent*
	{
		if (!Mesh) return nullptr;
		UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
		C->SetStaticMesh(Mesh);
		if (Mat) for (int32 S = 0; S < Mesh->GetStaticMaterials().Num(); ++S) C->SetMaterial(S, Mat);
		C->SetMobility(EComponentMobility::Movable); C->SetCullDistance(0.f); C->bNeverDistanceCull = true;
		C->SetCollisionEnabled(bCollide ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
		if (bCollide) C->SetCollisionResponseToAllChannels(ECR_Block);
		C->SetCastShadow(bCollide);
		C->RegisterComponent();
		C->SetWorldTransform(FTransform(FRotator(0.f, Yaw, 0.f), At, Scale));
		return C;
	};
	UStaticMesh* Main = RegionLandmarkMeshes15.IsValidIndex(K.Main) ? RegionLandmarkMeshes15[K.Main].Get() : nullptr;
	if (Main)
	{
		// (the main piece by its box: its foot sunk into the ground, scaled to its height)
		const FBox B = Main->GetBoundingBox();
		const float Sc = K.Height * 100.f / FMath::Max(B.GetSize().Z, 1.f);
		const FVector At(Lm.At.X * 100.0, Lm.At.Y * 100.0, Lm.Z - B.Min.Z * Sc - K.Sink * 100.f);
		Lm.Main = Make(Main, nullptr, At, Lm.Yaw, FVector(Sc), true);
		Lm.TopZ = At.Z + B.Max.Z * Sc;
	}
	UStaticMesh* Extra = RegionLandmarkMeshes15.IsValidIndex(K.Extra) ? RegionLandmarkMeshes15[K.Extra].Get() : nullptr;
	if (Extra)
	{
		// (the extra over the main's top (a plume, a beam, a lamp's light): its box's foot at the top, scaled to its height and width)
		const FBox B = Extra->GetBoundingBox();
		const float Hz = K.ExtraHeight * 100.f / FMath::Max(B.GetSize().Z, 1.f), Wx = K.ExtraWidth * 100.f / FMath::Max(FMath::Max(B.GetSize().X, B.GetSize().Y), 1.f);
		const FVector At(Lm.At.X * 100.0, Lm.At.Y * 100.0, (Main ? Lm.TopZ - 300.f : Lm.Z) - B.Min.Z * Hz);
		Lm.Extra = Make(Extra, RegionLandmarkMats15.IsValidIndex(K.Mat) ? RegionLandmarkMats15[K.Mat].Get() : nullptr, At, Lm.Yaw, FVector(Wx, Wx, Hz), false);
		Lm.bExtraNight = K.bNight;
		if (UStaticMeshComponent* X = Lm.Extra.Get(); X && K.bNight) X->SetVisibility(IsWildNight15());
	}
	UE_LOG(LogRDList15i, Log, TEXT("RDLANDMARK15 %s at (%.0f, %.0f) m, top %.0f m over the ground"), *K.Name, Lm.At.X, Lm.At.Y, (Lm.TopZ - Lm.Z) / 100.f);
}

TArray<FString> ARDDungeonGenerator::GetRegionLandmarks15() const
{
	TArray<FString> Out;
	for (const auto& Kv : RegionLandmarks15)
	{
		const FRegionLandmark15& L = Kv.Value;
		ParseRegionLandmarks15();
		const FString Nm = RegionLandmarkParsed15.IsValidIndex(L.Line) ? RegionLandmarkParsed15[L.Line].Name : FString(TEXT("?"));
		const UStaticMeshComponent* X = L.Extra.Get();
		Out.Add(FString::Printf(TEXT("%s|%.1f|%.1f|%.0f|%.0f|%d|%d"), *Nm, L.At.X, L.At.Y, L.Z, L.TopZ, L.Main.IsValid() ? 1 : 0, X ? (X->IsVisible() ? 2 : 1) : 0));
	}
	// (the broken towers: the nearest, laid whole, and the far ones)
	auto Tower = [&](const UStaticMeshComponent* T)
	{
		if (!T || !T->GetStaticMesh()) return;
		const FVector P = T->GetComponentLocation();
		Out.Add(FString::Printf(TEXT("tower|%.1f|%.1f|%.0f|%.0f|1|0"), P.X / 100.0, P.Y / 100.0, P.Z + 200.f, P.Z + T->GetStaticMesh()->GetBoundingBox().Max.Z));
	};
	Tower(WildLandmark.Get());
	for (const auto& Kv : FarTowers15) Tower(Kv.Value.Get());
	return Out;
}

// ================================================================================================ the night's lights and smoke
void ARDDungeonGenerator::TickHouseLights15(float Dt, const FVector& Her)
{
	// (the villages' houses: a warm light in the room from dusk until their household's bed (21:00), and before dawn from 5:00; looked
	// at every 2 s; a house's light is made with it and kept on its chunk)
	HouseLightLook15 -= Dt;
	if (HouseLightLook15 > 0.f) return;
	HouseLightLook15 = 2.f;
	const bool bOn = IsHouseLightHour15();
	for (int32 I = HouseLights15.Num() - 1; I >= 0; --I)
	{
		UPointLightComponent* L = HouseLights15[I].Get();
		if (!L) { HouseLights15.RemoveAtSwap(I); continue; }
		if (L->IsVisible() != bOn) L->SetVisibility(bOn);
	}
}

UPointLightComponent* ARDDungeonGenerator::AddHouseLight15(ARDWildChunk* C, const FVector& RoomC, const FVector& DoorOut, bool bDoor)
{
	if (!C || !bHouseLights15) return nullptr;
	// (a warm light in its room, and a lamp over its door: with the doors shut the room's light was not seen from outside (the first
	// dusk picture); the door's lamp is what reads as a lived-in house from afar)
	const bool bOn = IsHouseLightHour15();
	auto Make = [&](const FVector& At, float Candelas, float Radius) -> UPointLightComponent*
	{
		UPointLightComponent* L = NewObject<UPointLightComponent>(C);
		L->SetupAttachment(C->GetRootComponent());
		L->SetMobility(EComponentMobility::Movable);
		L->SetIntensityUnits(ELightUnits::Candelas);
		L->SetIntensity(Candelas);
		L->SetLightColor(FLinearColor(1.f, 0.62f, 0.32f));
		L->SetAttenuationRadius(Radius);
		L->SetCastShadows(false);
		L->RegisterComponent();
		L->SetWorldLocation(At);
		L->SetVisibility(bOn);
		HouseLights15.Add(L);
		return L;
	};
	UPointLightComponent* Room = Make(RoomC + FVector(0, 0, 190.f), HouseLightCandelas15, 900.f);
	if (bDoor)
	{
		const FVector Out = (DoorOut - RoomC).GetSafeNormal2D();
		Make(DoorOut + Out * 40.f + FVector(0, 0, 230.f), HouseLightCandelas15 * 0.6f, 800.f);
	}
	return Room;
}

TArray<FString> ARDDungeonGenerator::GetHouseLights15(FVector2D AtM, float RadiusM) const
{
	TArray<FString> Out;
	for (const TWeakObjectPtr<UPointLightComponent>& W : HouseLights15)
		if (const UPointLightComponent* L = W.Get())
		{
			const FVector P = L->GetComponentLocation();
			if (FVector2D::Distance(FVector2D(P.X / 100.0, P.Y / 100.0), AtM) > RadiusM) continue;
			Out.Add(FString::Printf(TEXT("%.0f|%.0f|%.0f|%d|%.0f"), P.X, P.Y, P.Z, L->IsVisible() ? 1 : 0, L->Intensity));
		}
	return Out;
}
