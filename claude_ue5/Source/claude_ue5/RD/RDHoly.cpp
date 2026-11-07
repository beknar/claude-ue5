// Vel Morrath (the user's spec of 2026-11-06, docs/vel_morrath.txt): "cathedral city built over catacombs that go deeper than
// anyone has mapped ... the dungeon with the entrance from the central cathedral ... this should look like a holy city". The
// city is one of the wilderness's towns (the generator's TownPlan 1, RDTownPlan.cpp's bHoly: the cathedral at the town's
// middle, its plaza before it, the monastery, more chapels, statues, a fountain, wayside shrines, houses of white stone,
// pilgrims, monks, beggars, templars). This file builds the cathedral itself:
//   - its rooms (the plan's): the narthex between the two bell towers' bases, the nave, the choir whose far wall holds the stair
//     down into the catacombs, an aisle down each side;
//   - each room's walls inward to its height (nave, narthex and choir 15 m, the aisles 9 m, the towers 27 m), the outer stone
//     outward a wall's thickness out with tall blind windows, and the clerestory over the aisles' roofs;
//   - a vault over every tile, gabled roofs of the city's stone over the nave and over each aisle, a spire on each tower;
//   - the arch of the stair down (walked into, it opens the catacombs: RDTownGame.cpp), chandeliers' light down the nave.
// The pieces are "Cathedral.*" and "Town.Holy_*" in the generator's table (pipeline/unreal/892 sets them).
#include "RD/RDSection.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDTown.h"
#include "RD/RDGameInstance.h"
#include "RD/RDCombat.h"
#include "Components/PointLightComponent.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDHoly, Log, All);

static const FIntPoint RDHolyDir4[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };

void ARDSection::HolyGable(const FIntRect& Rc, float Top, const TCHAR* Style)
{
	// (as a house's roof (TownShellBuilding): its ridge along the rectangle's longer side, each tile's piece sloping down and
	// out from it a tile's height a tile, a trim along the eaves, the gables' triangles at the two ends)
	// (Style "Holy": the city's white stone, "Holy.<part>"; "Forge": the forge city's soot-dark stone, "Forge.<part>" (2026-11-07);
	// another: the town's "Town.<style>_<part>")
	const bool bOwn = FCString::Strcmp(Style, TEXT("Holy")) == 0 || FCString::Strcmp(Style, TEXT("Forge")) == 0;
	auto Pn = [Style, bOwn](const TCHAR* Part) { return bOwn ? FName(*FString::Printf(TEXT("%s.%s"), Style, Part)) : FName(*FString::Printf(TEXT("Town.%s_%s"), Style, Part)); };
	const float M = Generator->TileSize;
	const int32 Nx = Rc.Max.X - Rc.Min.X, Ny = Rc.Max.Y - Rc.Min.Y;
	if (Nx <= 0 || Ny <= 0) return;
	const bool bRidgeY = Ny >= Nx;
	const FVector A = bRidgeY ? FVector(0, 1, 0) : FVector(1, 0, 0), C = bRidgeY ? FVector(1, 0, 0) : FVector(0, 1, 0);
	const int32 NAlong = bRidgeY ? Ny : Nx, Span = bRidgeY ? Nx : Ny;
	const FVector Ctr = (TileWorld(Rc.Min) + TileWorld(Rc.Max - FIntPoint(1, 1))) * 0.5f;
	const float HAlong = NAlong * M * 0.5f, HAcross = Span * M * 0.5f;
	auto Tr = [&](const FVector& P, const FVector& Out, float Z) { return FTransform(FRotator(0, Out.Rotation().Yaw, 0), FVector(Ctr.X + P.X, Ctr.Y + P.Y, Ctr.Z + Z)); };
	for (int32 Al = 0; Al < NAlong; ++Al)
		for (int32 Ac = 0; Ac < Span; ++Ac)
		{
			const bool bLow = Ac < Span / 2;
			const int32 Level = bLow ? Ac : Span - 1 - Ac;
			const FVector Out = C * (bLow ? -1.f : 1.f);
			const FVector P = A * ((Al + 0.5f) * M - HAlong) + C * ((Ac + 0.5f) * M - HAcross);
			const FTransform T = Tr(P, Out, Top + Level * M);
			if (Span % 2 == 1 && Ac == Span / 2) { AddPiece(Pn(TEXT("Roof")), Tr(P, C * -1.f, Top + Level * M)); AddPiece(Pn(TEXT("Roof")), Tr(P, C, Top + Level * M)); continue; }
			AddPiece(Pn(TEXT("Roof")), T);
			if (Level == 0) AddPiece(Pn(TEXT("RoofTrim")), T);
			const FVector Yp(-Out.Y, Out.X, 0.f);
			const float Dy = FVector::DotProduct(Yp, A);
			if (Al == NAlong - 1) AddPiece(Pn(Dy > 0.f ? TEXT("RoofEndL") : TEXT("RoofEndR")), T);
			if (Al == 0) AddPiece(Pn(Dy > 0.f ? TEXT("RoofEndR") : TEXT("RoofEndL")), T);
		}
	for (int32 End = 0; End < 2; ++End)
	{
		const FVector Out = A * (End == 0 ? -1.f : 1.f);
		const FVector Yp(-Out.Y, Out.X, 0.f);
		const FVector P0 = A * ((End == 0 ? 0 : NAlong) * M - HAlong);
		for (int32 Lv = 0; Lv < Span / 2; ++Lv)
		{
			const float Half = (Span * 0.5f - Lv) * M;
			AddPiece(Pn(TEXT("GableNeg")), Tr(P0 + Yp * (-Half + M * 0.5f), Out, Top + Lv * M));
			AddPiece(Pn(TEXT("GablePos")), Tr(P0 + Yp * (Half - M * 0.5f), Out, Top + Lv * M));
			for (float Yv = -Half + M; Yv < Half - M + 1.f; Yv += M) AddPiece(Pn(TEXT("Wall")), Tr(P0 + Yp * Yv, Out, Top + Lv * M));
		}
	}
}

void ARDSection::CathedralShell(int32 BI)
{
	FTownBld& B = TownBlds[BI];
	FRandomStream R((int32)(B.Seed ^ 0x2468ACEu));
	const float M = Generator->TileSize;
	const FName Wall(TEXT("Cathedral.Wall")), WallOut(TEXT("Cathedral.WallOut")), WinOut(TEXT("Cathedral.WindowOut")), Floor(TEXT("Cathedral.Floor")), Ceil(TEXT("Cathedral.Ceil"));
	const FRDPiece* Wp = Generator->Piece(Wall);
	const FRDPiece* Op = Generator->Piece(WallOut);
	const FRDPiece* Dp = Generator->Piece(TEXT("Doorway"));
	const float T = Wp ? FMath::Clamp((float)Wp->Size.X, 20.f, 120.f) : 60.f;
	const float WZ = Wp ? FMath::Max((float)Wp->Size.Z - 2.f, 50.f) : 300.f;
	const float OZ = Op ? FMath::Max((float)Op->Size.Z - 2.f, 50.f) : WZ;
	// (the plan's rooms in order: the narthex, the nave, the choir, the left and right aisles, the two bell towers)
	auto HeightOf = [&](int32 K) { return K <= 2 ? 1500.f : K <= 4 ? 900.f : 2700.f; };
	// a stack of a piece from Z0 to Z1, its last one cut to fit
	auto Stack = [&](FName Nm, float Step, const FVector& At, float Yaw, float Z0, float Z1)
	{
		for (float Z = Z0; Z < Z1 - 5.f; Z += Step)
			AddPiece(Nm, FTransform(FRotator(0, Yaw, 0), At + FVector(0, 0, Z), FVector(1.f, 1.f, FMath::Min(1.f, (Z1 + 2.f - Z) / (Step + 2.f)))));
	};
	for (int32 K = 0; K < B.Rooms.Num(); ++K)
	{
		const int32 RI = B.Rooms[K];
		const FRoom& Rm = Rooms[RI];
		const float H = HeightOf(K);
		for (int32 X = Rm.Min.X; X < Rm.Max.X; ++X)
			for (int32 Y = Rm.Min.Y; Y < Rm.Max.Y; ++Y)
			{
				const FIntPoint Tl(X, Y);
				const FVector C = TileWorld(Tl);
				AddPieceAt(Floor, C, 90.f * R.RandRange(0, 3));
				AddPieceAt(Ceil, C + FVector(0, 0, H), 90.f * R.RandRange(0, 1));
				for (int32 Side = 0; Side < 4; ++Side)
				{
					const FIntPoint Nb = Tl + RDHolyDir4[Side];
					const int32 On = In(Nb) ? Owner[Idx(Nb)] : -1;
					if (On == RI) continue;
					const int32 Kn = B.Rooms.IndexOfByKey(On);
					const bool bOut = Kn == INDEX_NONE;
					const bool bDoor = DoorEdges.Contains(EdgeKey(Tl, Nb));
					const FVector Edge = C + FVector(RDHolyDir4[Side].X, RDHolyDir4[Side].Y, 0) * (M * 0.5f);
					const float Yaw = InwardYaw(Side);
					const FVector OutW = FRotator(0, Yaw, 0).RotateVector(FVector(-1, 0, 0));
					// (between two of its rooms each has its own wall, half a thickness into its room: their backs meet)
					const FVector At = bOut ? Edge : Edge - OutW * (T * 0.5f);
					// (the neighbour's height: above a lower room's roof this wall is the outside (the clerestory over the aisles))
					const float Hn = bOut ? 0.f : HeightOf(Kn);
					const FVector AtOut = Edge + OutW * (bOut ? T : T * 0.5f);
					const bool bWindowCol = ((X + Y) & 1) == 0;
					auto OuterFace = [&](float Z0)
					{
						// (the outer stone: tall blind windows every other bay above the ground storey, plain stone below and at the top)
						for (float Z = Z0; Z < H - 5.f; Z += OZ)
						{
							const bool bWin = bWindowCol && Z >= 290.f && Z + OZ <= H - 150.f && Generator->Piece(WinOut);
							AddPiece(bWin ? WinOut : WallOut, FTransform(FRotator(0, Yaw + 180.f, 0), AtOut + FVector(0, 0, Z), FVector(1.f, 1.f, FMath::Min(1.f, (H + 2.f - Z) / (OZ + 2.f)))));
						}
					};
					if (bDoor)
					{
						AddPieceAt(TEXT("Doorway"), At, Yaw);
						Stack(Wall, WZ, At, Yaw, Dp ? Dp->Size.Z - 2.f : 300.f, H);
						if (bOut)
						{
							// (the great door: the doorway turned out, the outer stone over it, the rose window high over it)
							AddPieceAt(TEXT("Doorway"), Edge + OutW * T, Yaw + 180.f);
							OuterFace(Dp ? Dp->Size.Z - 2.f : 300.f);
							AddPieceAt(TEXT("Cathedral.Rose"), AtOut + OutW * 20.f + FVector(0, 0, H * 0.62f), Yaw + 180.f, 1.f, true);
						}
						else if (Hn < H) OuterFace(Hn);
						continue;
					}
					Stack(Wall, WZ, At, Yaw, 0.f, H);
					if (bOut) OuterFace(0.f);
					else if (Hn < H) OuterFace(Hn);
				}
			}
	}
	// ---- the roofs: a gable of the city's stone over the narthex, nave and choir together, one over each aisle
	auto Bounds = [&](int32 K0, int32 K1)
	{
		FIntRect U(FIntPoint(MAX_int32, MAX_int32), FIntPoint(MIN_int32, MIN_int32));
		for (int32 K = K0; K <= K1 && K < B.Rooms.Num(); ++K) { const FRoom& Rm = Rooms[B.Rooms[K]]; U.Min = U.Min.ComponentMin(Rm.Min); U.Max = U.Max.ComponentMax(Rm.Max); }
		return U;
	};
	if (B.Rooms.Num() >= 7)
	{
		HolyGable(Bounds(0, 2), HeightOf(0), TEXT("Holy"));
		HolyGable(Bounds(3, 3), HeightOf(3), TEXT("Holy"));
		HolyGable(Bounds(4, 4), HeightOf(4), TEXT("Holy"));
		// ---- the bell towers: a flat stone top and a spire over each
		for (int32 K = 5; K <= 6; ++K)
		{
			const FRoom& Rm = Rooms[B.Rooms[K]];
			const FVector Tc = (TileWorld(Rm.Min) + TileWorld(Rm.Max - FIntPoint(1, 1))) * 0.5f;
			for (int32 X = Rm.Min.X; X < Rm.Max.X; ++X) for (int32 Y = Rm.Min.Y; Y < Rm.Max.Y; ++Y) AddPieceAt(TEXT("Town.CastleRoof"), TileWorld(FIntPoint(X, Y)) + FVector(0, 0, HeightOf(K) + 40.f), 0.f, 1.f, true);
			AddPieceAt(TEXT("Cathedral.Spire"), Tc + FVector(0, 0, HeightOf(K) + 40.f), TownBldYaw(B), 1.f, true);
		}
	}
	// ---- the stair down into the catacombs: its arch in the choir's far wall (walked into: RDTownGame.cpp); candles before it
	AddPieceAt(TEXT("Holy.CryptArch"), MistgateAt - MistgateNormal * 30.f, MistgateNormal.Rotation().Yaw, 1.f, true);
	AddLight(MistgateAt + MistgateNormal * 220.f + FVector(0, 0, 260.f), FLinearColor(1.f, 0.72f, 0.45f), 160.f, 900.f, false, 0.10f);
	// ---- the nave's chandeliers: hung down its middle, their light
	if (B.Rooms.Num() > 1)
	{
		const FRoom& Nv = Rooms[B.Rooms[1]];
		const bool bAlongX = (Nv.Max.X - Nv.Min.X) >= (Nv.Max.Y - Nv.Min.Y);
		const int32 L0 = bAlongX ? Nv.Min.X : Nv.Min.Y, L1 = bAlongX ? Nv.Max.X : Nv.Max.Y;
		const int32 Mid = bAlongX ? (Nv.Min.Y + Nv.Max.Y) / 2 : (Nv.Min.X + Nv.Max.X) / 2;
		for (int32 L = L0 + 2; L < L1 - 1; L += 4)
		{
			const FVector P = TileWorld(bAlongX ? FIntPoint(L, Mid) : FIntPoint(Mid, L));
			AddPieceAt(TEXT("Cathedral.Chandelier"), P + FVector(0, 0, 900.f), 0.f, 1.f, true);
			AddLight(P + FVector(0, 0, 820.f), FLinearColor(1.f, 0.78f, 0.52f), 520.f, 2200.f, false, 0.06f);
		}
	}
	B.Style = 4;
	UE_LOG(LogRDHoly, Log, TEXT("RDHOLY the cathedral built: %d rooms, the stair down at (%.0f, %.0f)"), B.Rooms.Num(), MistgateAt.X, MistgateAt.Y);
}

// ================================================================================================ down into the catacombs
FString ARDDungeonGenerator::WayBackName() const
{
	if (!DungeonKey.IsEmpty())
		if (const URDGameInstance* GI = URDGameInstance::Of(this); GI && !GI->ReturnTown.IsEmpty()) return GI->ReturnTown;
	return TownName;
}

FString ARDDungeonGenerator::DungeonCounterName(const FString& N) const
{
	return URDGameInstance::DungeonCounter(DungeonKey, N);          // (one key format, the game instance's)
}

int32 ARDDungeonGenerator::DungeonTierReached(const FString& Key) const
{
	// (the deepest tier open in one dungeon: Mistward Castle's (empty key) or another's; this level's own as well when it is
	// that dungeon)
	int32 T = 1;
	if (!bTown && DungeonKey == Key) for (const int32 O : TiersOpened) T = FMath::Max(T, O);
	if (const URDGameInstance* GI = URDGameInstance::Of(this))
	{
		if (Key.IsEmpty()) { for (const int32 O : GI->CastleTiers) T = FMath::Max(T, O); }
		else if (const FRDDungeonSave* D = GI->Dungeons.Find(Key)) { for (const int32 O : D->Tiers) T = FMath::Max(T, O); }
	}
	return FMath::Clamp(T, 1, 5);
}

FString ARDDungeonGenerator::CurrentDungeonLevel() const
{
	if (bTownHome) return FString();
	if (const FString* L = TownDungeons.Find(TownName)) return *L;
	return TownPlan == 1 ? CatacombsLevel : FString();
}

bool ARDDungeonGenerator::EnterCatacombs()
{
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!HasTownDungeon() || !S) return false;
	// (where she comes back: 7 m before the cathedral's door, facing out over the plaza; the plan comes from the town's seed
	// alone, so the place is the same when the town is built again)
	FVector At = FVector::ZeroVector; float Yaw = 0.f;
	if (S->TownBlds.IsValidIndex(S->CastleBld))
	{
		const ARDSection::FTownBld& C = S->TownBlds[S->CastleBld];
		const FVector Out(RDHolyDir4[C.DoorSide].X, RDHolyDir4[C.DoorSide].Y, 0.f);
		At = S->LocalToWorld(C.DoorTile) + Out * 700.f + FVector(0, 0, 100.f);
		Yaw = Out.Rotation().Yaw;
	}
	return DescendToCatacombs(At, Yaw);
}

bool ARDDungeonGenerator::DescendToCatacombs(const FVector& At, float Yaw, const FString& InLevel)
{
	// (the level asked for, else the town's own; from Brokenspire (-RDTownGo=catacombs) Vel Morrath's catacombs as before)
	const FString Level = !InLevel.IsEmpty() ? InLevel : HasTownDungeon() ? CurrentDungeonLevel() : CatacombsLevel;
	if (!bTown || Level.IsEmpty() || bTownTraveling) return false;
	LastTravel = TEXT("catacombs");
	if (bTravelDryRun) return true;
	if (URDGameInstance* GI = URDGameInstance::Of(this))
	{
		if (!At.IsZero()) { GI->ReturnAt = At; GI->ReturnYaw = Yaw; }
		GI->ReturnTown = TownName;
	}
	TravelToDungeon(Level, TEXT("catacombs"));
	return true;
}
