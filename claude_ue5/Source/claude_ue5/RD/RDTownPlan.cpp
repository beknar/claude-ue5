// Brokenspire (docs/brokenspire.txt; the generator's bTown): the town as the start section. ARDSection::PlanTown lays it out
// from the section's seed alone, so the saved build and play's rebuild of its doors and containers agree, and a new game's
// seed makes another town by the same rules:
//   - a square of 500 m (the section is 168 tiles of 3 m): a town wall round 160 x 160 tiles, a gate in one of its sides,
//     guard towers at its corners, beside the gate and along it;
//   - a cobbled main road from the gate to the Mistward Castle building against the far wall, the town square on it, a cross
//     road through the square, side streets and a lane inside the wall;
//   - buildings on plots facing the streets (each plot's door toward its street): the trades by the square (smithy, trader,
//     healer, temple, storehouse, tavern), the barracks by the gate, a chapel with the graveyard against the wall, the witch's
//     hut in the farthest corner, homes everywhere else (lived in, burned or boarded up); the square holds the well, the
//     quest board, the market stalls, and the teleport circle stands beside it; a mill and a still outside the houses;
//   - the castle: an entry hall, the Mistward Hall behind it (its back wall the Mistgate into Mistward Castle; its guards
//     stay in it) and two wings, built of the castle's own walls, outside and in.
// The tiles: the ground is one hallway (Corrs[0]) so that monsters and townsfolk path over it; buildings are rooms whose
// doors are the only way in; the wall's ring and what stands outside it are void.
#include "RD/RDSection.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDMonster.h"
#include "RD/RDMistward.h"
#include "ProceduralMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/BoxComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Materials/MaterialInterface.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDTown, Log, All);

// the town's building kinds and the things that stand outside (RDTown.h names them for the generator and the HUD)
#include "RD/RDTown.h"

static const FIntPoint RDTDir4[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };

FString ARDSection::TownKindName(uint8 Kind) { return RDTownKindName(Kind); }

// ------------------------------------------------------------------------------------------------ the plan
namespace
{
	/** the town laid out in its own frame: u from the gate (u 0) to the castle's wall (u S - 1), v across; mapped to the
	 *  section's tiles by the gate's side */
	struct FRDTFrame
	{
		int32 O = 4, S = 160, G = 0;
		FIntPoint Tile(int32 U, int32 V) const
		{
			switch (G)
			{
			case 1: return FIntPoint(O + S - 1 - U, O + S - 1 - V);
			case 2: return FIntPoint(O + S - 1 - V, O + U);
			case 3: return FIntPoint(O + V, O + S - 1 - U);
			default: return FIntPoint(O + U, O + V);
			}
		}
		/** a rectangle [U0, U1) x [V0, V1) as local tiles (max exclusive) */
		FIntRect Rect(int32 U0, int32 V0, int32 U1, int32 V1) const
		{
			const FIntPoint A = Tile(U0, V0), B = Tile(U1 - 1, V1 - 1);
			return FIntRect(FIntPoint(FMath::Min(A.X, B.X), FMath::Min(A.Y, B.Y)), FIntPoint(FMath::Max(A.X, B.X) + 1, FMath::Max(A.Y, B.Y) + 1));
		}
		/** the side (0 -X, 1 +X, 2 -Y, 3 +Y) a way of the frame (Du, Dv: one of them +-1) points to */
		int32 Side(int32 Du, int32 Dv) const
		{
			FIntPoint D;
			switch (G)
			{
			case 1: D = FIntPoint(-Du, -Dv); break;
			case 2: D = FIntPoint(-Dv, Du); break;
			case 3: D = FIntPoint(Dv, -Du); break;
			default: D = FIntPoint(Du, Dv); break;
			}
			return D.X < 0 ? 0 : D.X > 0 ? 1 : D.Y < 0 ? 2 : 3;
		}
	};
}

void ARDSection::PlanTown(FRandomStream& R)
{
	N = Generator->SectionTiles;
	Rooms.Reset(); Corrs.Reset(); DoorEdges.Reset(); Portals.Reset(); Cells.Reset(); Fixtures.Reset(); SpecialChests.Reset();
	Pickups.Reset();
	Type.Init(0, N * N); Owner.Init(-1, N * N); Blocked.Init(0, N * N); CeilH.Init(0.f, N * N);
	TownBlds.Reset(); TownSpots.Reset(); TownRoads.Reset(); TownPosts.Reset(); TownGreens.Reset();
	CastleHallRoom = -1; CastleBld = -1; CastleTowers.Reset(); CastleStairTower = -1;
	FRDTFrame F; F.O = FMath::Max(4, (N - 160) / 2); F.S = N - 2 * F.O; F.G = R.RandRange(0, 3);
	const int32 S = F.S;
	// ---- the ground inside the wall: one hallway
	FCorr Ground; Ground.Min = FIntPoint(F.O, F.O); Ground.Max = FIntPoint(F.O + S, F.O + S); Ground.bHoriz = true; Ground.Theme = 0;
	Corrs.Add(Ground);
	TownInner = FIntRect(Ground.Min, Ground.Max);
	for (int32 X = Ground.Min.X; X < Ground.Max.X; ++X)
		for (int32 Y = Ground.Min.Y; Y < Ground.Max.Y; ++Y) { Type[Idx(FIntPoint(X, Y))] = 2; Owner[Idx(FIntPoint(X, Y))] = 1000; }
	// (a frame grid of what each tile is taken by: 0 free, 1 road, 2 square, 3 building or its margin, 4 kept clear)
	TArray<uint8> Use; Use.Init(0, S * S);
	auto U_ = [&](int32 U, int32 V) -> uint8& { static uint8 Dummy; return (U >= 0 && V >= 0 && U < S && V < S) ? Use[U * S + V] : (Dummy = 9); };
	auto Mark = [&](int32 U0, int32 V0, int32 U1, int32 V1, uint8 What)
	{
		for (int32 U = FMath::Max(U0, 0); U < FMath::Min(U1, S); ++U) for (int32 V = FMath::Max(V0, 0); V < FMath::Min(V1, S); ++V) if (Use[U * S + V] < What || What == 0) Use[U * S + V] = What;
	};
	auto Road = [&](int32 U0, int32 V0, int32 U1, int32 V1)
	{
		Mark(U0, V0, U1, V1, 1);
		TownRoads.Add(F.Rect(FMath::Max(U0, 0), FMath::Max(V0, 0), FMath::Min(U1, S), FMath::Min(V1, S)));
	};
	// ---- the main road, the castle, the square, the cross roads
	const int32 Vc = S / 2 - 1 + R.RandRange(-6, 6);
	const int32 CD = 17, CW = 21;
	// (a tile of ground and the lane behind the castle: its round corner towers stand 5 m out from its corners)
	const int32 Cu0 = S - 3 - CD, Cv0 = Vc - CW / 2;
	const int32 Us = 50 + R.RandRange(-4, 4);           // (the square's near edge)
	const int32 SqU0 = Us, SqU1 = Us + 14, SqV0 = Vc - 7, SqV1 = Vc + 8;
	Road(0, Vc - 1, Cu0, Vc + 2);
	Mark(Cu0 - 6, Vc - 5, Cu0, Vc + 6, 1);                                    // (the castle's forecourt)
	TownRoads.Add(F.Rect(Cu0 - 6, Vc - 5, Cu0, Vc + 6));
	Mark(SqU0, SqV0, SqU1, SqV1, 2);
	TownSquare = F.Rect(SqU0, SqV0, SqU1, SqV1);
	const int32 Xu = Us + 6;
	Road(Xu, 3, Xu + 3, S - 3);
	const int32 Sv0 = Vc - 27 - R.RandRange(0, 4), Sv1 = Vc + 27 + R.RandRange(0, 4);
	Road(4, Sv0, Cu0 - 7, Sv0 + 2); Road(4, Sv1, Cu0 - 7, Sv1 + 2);
	const int32 Xu0 = FMath::Max(14, Us - 24 - R.RandRange(0, 4)), Xu1 = FMath::Min(Cu0 - 12, Us + 38 + R.RandRange(0, 6));
	Road(Xu0, 3, Xu0 + 2, S - 3); Road(Xu1, 3, Xu1 + 2, S - 3);
	// (more streets, nearer the wall: frontage for the homes; each from the plan's stream, so the town differs by its seed)
	const int32 Sv2 = Vc - 52 - R.RandRange(0, 4), Sv3 = Vc + 52 + R.RandRange(0, 4);
	if (Sv2 > 8) Road(6, Sv2, Cu0 - 7, Sv2 + 2);
	if (Sv3 < S - 10) Road(6, Sv3, Cu0 - 7, Sv3 + 2);
	const int32 Xu2 = Xu0 - 20 - R.RandRange(0, 3), Xu3 = Xu1 + 20 + R.RandRange(0, 3);
	if (Xu2 >= 10) Road(Xu2, 3, Xu2 + 2, S - 3);
	if (Xu3 < Cu0 - 8) Road(Xu3, 3, Xu3 + 2, S - 3);
	// the lane inside the wall (trodden, not cobbled)
	Mark(0, 0, S, 2, 1); Mark(0, S - 2, S, S, 1); Mark(0, 0, 2, S, 1); Mark(S - 2, 0, S, S, 1);
	// the castle and the square's ground are taken; the gate's mouth kept clear
	Mark(Cu0 - 2, Cv0 - 2, S, Cv0 + CW + 2, 3);
	Mark(0, Vc - 4, 6, Vc + 5, 4);
	// ---- the teleport circle beside the square (a 5 x 5 paved ring), the graveyard, the mill, the still's ground
	const bool bCircleLow = R.RandBool();
	const int32 CiV0 = bCircleLow ? SqV0 - 6 : SqV1 + 1, CiU0 = SqU0 + 2;
	Mark(CiU0, CiV0, CiU0 + 5, CiV0 + 5, 4);
	{
		const FIntRect Ci = F.Rect(CiU0, CiV0, CiU0 + 5, CiV0 + 5);
		FTownSpot Sp; Sp.Kind = TS_Circle; Sp.At = TileWorld(FIntPoint((Ci.Min.X + Ci.Max.X) / 2, (Ci.Min.Y + Ci.Max.Y) / 2)) + FVector(Ci.Width() % 2 ? 0.f : -150.f, Ci.Height() % 2 ? 0.f : -150.f, 0.f);
		TownSpots.Add(Sp);
	}
	// (the graveyard: a corner of the town away from the gate; its chapel takes the plot beside it)
	const bool bGraveLow = R.RandBool();
	const int32 GyU0 = S - 4 - 14 - CD - 6, GyV0 = bGraveLow ? 3 : S - 3 - 11;
	Mark(GyU0, GyV0, GyU0 + 12, GyV0 + 11, 4);
	const FIntRect Gy = F.Rect(GyU0 + 1, GyV0 + 1, GyU0 + 11, GyV0 + 10);
	// (the mill in the other corner by the castle side, on open ground)
	const int32 MlU0 = S - 4 - 14 - CD - 4, MlV0 = bGraveLow ? S - 3 - 7 : 3;
	Mark(MlU0, MlV0, MlU0 + 7, MlV0 + 7, 4);
	{
		const FIntRect M = F.Rect(MlU0, MlV0, MlU0 + 7, MlV0 + 7);
		FTownSpot Sp; Sp.Kind = TS_Mill; Sp.At = TileWorld(FIntPoint((M.Min.X + M.Max.X) / 2, (M.Min.Y + M.Max.Y) / 2)); Sp.Yaw = 90.f * R.RandRange(0, 3);
		TownSpots.Add(Sp);
	}
	// ---- the plots. Each building is a rectangle whose door side faces a road or the square across at most two tiles of
	// ground; buildings keep a tile of ground between them. The trades are placed first, nearest the square; the barracks
	// nearest the gate, the chapel by the graveyard, the witch's hut farthest from the square; then the homes.
	struct FPlotTry { int32 U0, V0, W, D; int32 DoorU, DoorV, Du, Dv; float Score; };
	auto FreeRect = [&](int32 U0, int32 V0, int32 U1, int32 V1)
	{
		if (U0 < 3 || V0 < 3 || U1 > S - 3 || V1 > S - 3) return false;
		for (int32 U = U0 - 1; U < U1 + 1; ++U) for (int32 V = V0 - 1; V < V1 + 1; ++V) if (U_(U, V) != 0) return false;
		return true;
	};
	// a door on one of the rectangle's sides whose next tile out is ground and a road / square is within two tiles
	auto FindDoor = [&](int32 U0, int32 V0, int32 U1, int32 V1, FPlotTry& T) -> bool
	{
		struct FS { int32 Du, Dv; };
		const FS Sides[4] = { { -1, 0 }, { 1, 0 }, { 0, -1 }, { 0, 1 } };
		int32 Best = -1; int32 BestDist = 99;
		for (int32 K = 0; K < 4; ++K)
		{
			const FS& Sd = Sides[K];
			const int32 Mu = (U0 + U1 - 1) / 2, Mv = (V0 + V1 - 1) / 2;
			const int32 Du_ = Sd.Du < 0 ? U0 : Sd.Du > 0 ? U1 - 1 : Mu, Dv_ = Sd.Dv < 0 ? V0 : Sd.Dv > 0 ? V1 - 1 : Mv;
			for (int32 Step = 1; Step <= 3; ++Step)
			{
				const uint8 W = U_(Du_ + Sd.Du * Step, Dv_ + Sd.Dv * Step);
				if (W == 1 || W == 2) { if (Step < BestDist) { BestDist = Step; Best = K; T.DoorU = Du_; T.DoorV = Dv_; T.Du = Sd.Du; T.Dv = Sd.Dv; } break; }
				if (W != 0) break;
			}
		}
		return Best >= 0;
	};
	const FVector2D SqMid((SqU0 + SqU1) * 0.5f, (SqV0 + SqV1) * 0.5f), GateMid(2.f, Vc + 0.5f);
	auto Place = [&](uint8 Kind, int32 WMin, int32 WMax, int32 DMin, int32 DMax, TFunctionRef<float(const FVector2D&)> Score, int32 Tries, FPlotTry& Out) -> bool
	{
		bool bFound = false; Out.Score = MAX_flt;
		for (int32 T = 0; T < Tries; ++T)
		{
			FPlotTry P; P.W = R.RandRange(WMin, WMax); P.D = R.RandRange(DMin, DMax);
			if (R.RandBool()) Swap(P.W, P.D);
			P.U0 = R.RandRange(3, S - 3 - P.D); P.V0 = R.RandRange(3, S - 3 - P.W);
			if (!FreeRect(P.U0, P.V0, P.U0 + P.D, P.V0 + P.W) || !FindDoor(P.U0, P.V0, P.U0 + P.D, P.V0 + P.W, P)) continue;
			P.Score = Score(FVector2D(P.U0 + P.D * 0.5f, P.V0 + P.W * 0.5f));
			if (P.Score < Out.Score) { Out = P; bFound = true; }
		}
		return bFound;
	};
	auto Commit = [&](uint8 Kind, const FPlotTry& P, uint8 State, int32 Storeys)
	{
		Mark(P.U0, P.V0, P.U0 + P.D, P.V0 + P.W, 3);
		FTownBld B; B.Kind = Kind; B.State = State; B.Storeys = Storeys; B.Seed = (uint32)R.RandHelper(0x7fffffff);
		const FIntRect Rc = F.Rect(P.U0, P.V0, P.U0 + P.D, P.V0 + P.W);
		B.Min = Rc.Min; B.Max = Rc.Max;
		B.DoorSide = F.Side(P.Du, P.Dv); B.DoorTile = F.Tile(P.DoorU, P.DoorV);
		// (the tile before the door is kept as ground: nothing is built on it)
		U_(P.DoorU + P.Du, P.DoorV + P.Dv) = FMath::Max<uint8>(U_(P.DoorU + P.Du, P.DoorV + P.Dv), 4);
		return TownBlds.Add(B);
	};
	auto Near = [](const FVector2D& To) { return [To](const FVector2D& P) { return (float)FVector2D::Distance(P, To); }; };
	FPlotTry P;
	// the trades round the square
	struct FTrade { uint8 Kind; int32 W0, W1, D0, D1; };
	const FTrade Trades[] = { { TK_Temple, 9, 11, 7, 9 }, { TK_Tavern, 7, 9, 6, 8 }, { TK_Smithy, 6, 7, 5, 6 }, { TK_Store, 6, 7, 5, 6 },
	                          { TK_Healer, 5, 6, 5, 6 }, { TK_Storehouse, 6, 8, 5, 6 } };
	for (const FTrade& T : Trades)
	{
		const float Jit = R.FRandRange(0.f, 6.f);
		if (Place(T.Kind, T.W0, T.W1, T.D0, T.D1, [&](const FVector2D& Q) { return (float)FVector2D::Distance(Q, SqMid) + Jit; }, 900, P))
			Commit(T.Kind, P, 0, 2);
	}
	// the barracks by the gate, the chapel by the graveyard, the witch's hut far from everyone
	if (Place(TK_Barracks, 9, 11, 6, 7, Near(GateMid + FVector2D(14.f, 0.f)), 900, P)) Commit(TK_Barracks, P, 0, 2);
	if (Place(TK_Chapel, 6, 7, 5, 6, Near(FVector2D(GyU0 + 6.f, GyV0 + 5.5f)), 900, P)) Commit(TK_Chapel, P, 0, 2);
	if (Place(TK_Witch, 4, 4, 4, 4, [&](const FVector2D& Q) { return -(float)FVector2D::Distance(Q, SqMid); }, 900, P)) Commit(TK_Witch, P, 0, 1);
	// the homes: as many as fit; their state by chance (the user's: burned down, boarded up, or lived in)
	for (int32 H = 0; H < 170; ++H)
	{
		if (!Place(TK_Home, 4, 6, 4, 5, [&](const FVector2D& Q) { return R.FRand(); }, 80, P)) continue;
		const float U = R.FRand();
		Commit(TK_Home, P, U < 0.2f ? 1 : U < 0.42f ? 2 : 0, 2);
	}
	// ---- the castle (its own frame: front toward -u, the main road's middle Vc)
	{
		FTownBld B; B.Kind = TK_Castle; B.Seed = (uint32)R.RandHelper(0x7fffffff); B.Storeys = 2;
		const FIntRect Rc = F.Rect(Cu0, Cv0, Cu0 + CD, Cv0 + CW);
		B.Min = Rc.Min; B.Max = Rc.Max;
		B.DoorSide = F.Side(-1, 0); B.DoorTile = F.Tile(Cu0, Vc);
		CastleBld = TownBlds.Add(B);
	}
	// ---- rooms: one for each building (the castle: four), its kind the dungeon's furnishing for what it is
	auto AddRoomRect = [&](int32 BI, const FIntRect& Rc, ERDRoomKind K, FIntPoint Lane) -> int32
	{
		FRoom Rm; Rm.Min = Rc.Min; Rm.Max = Rc.Max; Rm.Kind = K; Rm.Lane = Lane; Rm.Block = BI;
		const int32 RI = Rooms.Add(Rm);
		for (int32 X = Rc.Min.X; X < Rc.Max.X; ++X)
			for (int32 Y = Rc.Min.Y; Y < Rc.Max.Y; ++Y) { Type[Idx(FIntPoint(X, Y))] = 1; Owner[Idx(FIntPoint(X, Y))] = (int16)RI; }
		TownBlds[BI].Rooms.Add(RI);
		return RI;
	};
	int32 DoorNo = 0;
	auto AddEdge = [&](FIntPoint A, FIntPoint B) { DoorEdges.Add(EdgeKey(A, B), DoorNo++); };
	for (int32 BI = 0; BI < TownBlds.Num(); ++BI)
	{
		FTownBld& B = TownBlds[BI];
		const FIntPoint Out = B.DoorTile + RDTDir4[B.DoorSide];
		if (B.Kind == TK_Castle)
		{
			// entry hall (5 deep, 11 wide), the Mistward Hall behind it, two wings the castle's whole depth
			const int32 Ew = 11, Ed = 5;
			const int32 W0 = Vc - Ew / 2;
			const int32 RE = AddRoomRect(BI, F.Rect(Cu0, W0, Cu0 + Ed, W0 + Ew), ERDRoomKind::GuardRoom, F.Tile(Cu0 + 2, Vc));
			const int32 RH = AddRoomRect(BI, F.Rect(Cu0 + Ed, W0, Cu0 + CD, W0 + Ew), ERDRoomKind::Hall, F.Tile(Cu0 + Ed + (CD - Ed) / 2, Vc));
			const int32 RW = AddRoomRect(BI, F.Rect(Cu0, Cv0, Cu0 + CD, W0), ERDRoomKind::Armory, F.Tile(Cu0 + 2, (Cv0 + W0) / 2));
			const int32 REa = AddRoomRect(BI, F.Rect(Cu0, W0 + Ew, Cu0 + CD, Cv0 + CW), ERDRoomKind::Library, F.Tile(Cu0 + 2, (W0 + Ew + Cv0 + CW) / 2));
			CastleHallRoom = RH;
			// (lanes: each room's middle row and column are kept free (the furnishing's door lines); the doors lie on them)
			Rooms[RE].bDoorSide[B.DoorSide] = true;
			AddEdge(B.DoorTile, Out);
			const int32 Back = F.Side(1, 0), Left = F.Side(0, -1), Right = F.Side(0, 1);
			AddEdge(F.Tile(Cu0 + Ed - 1, Vc), F.Tile(Cu0 + Ed, Vc)); Rooms[RE].bDoorSide[Back] = true; Rooms[RH].bDoorSide[F.Side(-1, 0)] = true;
			AddEdge(F.Tile(Cu0 + 2, W0), F.Tile(Cu0 + 2, W0 - 1)); Rooms[RE].bDoorSide[Left] = true; Rooms[RW].bDoorSide[Right] = true;
			AddEdge(F.Tile(Cu0 + 2, W0 + Ew - 1), F.Tile(Cu0 + 2, W0 + Ew)); Rooms[RE].bDoorSide[Right] = true; Rooms[REa].bDoorSide[Left] = true;
			// (the hall's far wall is the Mistgate: no dais and throne against it)
			Rooms[RH].bDoorSide[Back] = true;
			const FVector Far = TileWorld(F.Tile(Cu0 + CD - 1, Vc));
			const FVector Fw = FVector(RDTDir4[Back].X, RDTDir4[Back].Y, 0.f);
			MistgateAt = Far + Fw * (Generator->TileSize * 0.5f) + (Ew % 2 ? FVector::ZeroVector : FVector::ZeroVector);
			MistgateNormal = -Fw;
			B.Label = TEXT("Mistward Castle");
			continue;
		}
		ERDRoomKind K = ERDRoomKind::Kitchen;
		switch (B.Kind)
		{
		case TK_Smithy: K = ERDRoomKind::Forge; break;
		case TK_Store: K = ERDRoomKind::Storeroom; break;
		case TK_Healer: K = ERDRoomKind::Barracks; break;
		case TK_Temple: case TK_Chapel: K = ERDRoomKind::Chapel; break;
		case TK_Storehouse: K = ERDRoomKind::Storeroom; break;
		case TK_Tavern: K = ERDRoomKind::Kitchen; break;
		case TK_Barracks: K = ERDRoomKind::Barracks; break;
		case TK_Witch: K = ERDRoomKind::Library; break;
		default: K = B.State == 2 ? ERDRoomKind::Storeroom : B.State == 1 ? ERDRoomKind::Crypt : (FRandomStream((int32)B.Seed).RandBool() ? ERDRoomKind::Kitchen : ERDRoomKind::GuardRoom); break;
		}
		// (the lane runs through the door)
		const FIntPoint Mid((B.Min.X + B.Max.X - 1) / 2, (B.Min.Y + B.Max.Y - 1) / 2);
		const FIntPoint Lane = B.DoorSide < 2 ? FIntPoint(Mid.X, B.DoorTile.Y) : FIntPoint(B.DoorTile.X, Mid.Y);
		const int32 RI = AddRoomRect(BI, FIntRect(B.Min, B.Max), K, Lane);
		Rooms[RI].bDoorSide[B.DoorSide] = true;
		AddEdge(B.DoorTile, Out);
		B.bBoarded = B.State == 2;
		B.Label = RDTownKindName(B.Kind);
	}
	// ---- the castle's round towers, its stair turret and the path to it (no draws: the plan's stream is untouched)
	CastleTowersPlan();
	// ---- the wall's towers (2 x 2 tiles astride the wall at its corners, beside the gate and every 15 tiles or so): void
	auto Tower = [&](int32 U, int32 V)
	{
		const FIntPoint T = F.Tile(U, V);
		FTownSpot Sp; Sp.Kind = TS_Tower; Sp.At = TileWorld(T);
		TownSpots.Add(Sp);
	};
	for (int32 K = 0; K <= 6; ++K)
	{
		const int32 A = FMath::Clamp(K * (S - 1) / 6, 0, S - 1);
		// (none in the gate's mouth: the gate's own frame is there)
		if (FMath::Abs(A - Vc) > 4) Tower(0, A);
		Tower(S - 1, A);
		if (K > 0 && K < 6) { Tower(A, 0); Tower(A, S - 1); }
	}
	// (the gate's towers: one on each side of it)
	Tower(0, Vc - 4); Tower(0, Vc + 5);
	// ---- the gate (the wall's gap at the main road), outside it the way on
	{
		const FIntPoint Gi = F.Tile(0, Vc);
		const FVector Out = FVector(RDTDir4[F.Side(-1, 0)].X, RDTDir4[F.Side(-1, 0)].Y, 0.f);
		TownGate = TileWorld(Gi) + Out * (Generator->TileSize * 0.5f);
		TownGateOut = Out;
		FTownSpot Sp; Sp.Kind = TS_Gate; Sp.At = TownGate; Sp.Yaw = Out.Rotation().Yaw;
		TownSpots.Add(Sp);
	}
	// ---- what stands on the square and outdoors: the well, the quest board, the stalls, the lamps; the graves; the still
	{
		const FIntRect Sq = TownSquare;
		const FVector Mid = (TileWorld(Sq.Min) + TileWorld(Sq.Max - FIntPoint(1, 1))) * 0.5f;
		const FVector Ua = FVector(RDTDir4[F.Side(1, 0)].X, RDTDir4[F.Side(1, 0)].Y, 0.f), Va = FVector(RDTDir4[F.Side(0, 1)].X, RDTDir4[F.Side(0, 1)].Y, 0.f);
		FTownSpot W; W.Kind = TS_Well; W.At = Mid + Va * 600.f; TownSpots.Add(W);
		FTownSpot Bd; Bd.Kind = TS_Board; Bd.At = Mid - Va * 700.f + Ua * 450.f; Bd.Yaw = (-Ua).Rotation().Yaw; TownSpots.Add(Bd);
		for (int32 K = 0; K < 4; ++K)
		{
			FTownSpot St; St.Kind = TS_Stall;
			const float Sd = K < 2 ? -1.f : 1.f;
			St.At = Mid + Ua * Sd * 1500.f + Va * ((K % 2) ? 650.f : -650.f);
			St.Yaw = (Ua * -Sd).Rotation().Yaw + 90.f;
			TownSpots.Add(St);
		}
		for (const FVector& C : { Mid + (Ua + Va) * 1700.f, Mid + (Ua - Va) * 1700.f, Mid + (-Ua + Va) * 1700.f, Mid + (-Ua - Va) * 1700.f })
		{
			FTownSpot L; L.Kind = TS_Lamp; L.At = C; TownSpots.Add(L);
		}
		// the elder by the board, the preacher, children and the town's idiot about the square
		FTownPost Pe; Pe.Role = ERDTownRole::Elder; Pe.At = Bd.At + Ua * -220.f + Va * 160.f; Pe.Yaw = Bd.Yaw + 180.f; TownPosts.Add(Pe);
		FTownPost Pp; Pp.Role = ERDTownRole::Preacher; Pp.At = Mid - Ua * 900.f + Va * 200.f; Pp.Yaw = Ua.Rotation().Yaw; Pp.Wander = 250.f; TownPosts.Add(Pp);
		for (int32 K = 0; K < 3; ++K) { FTownPost Pc_; Pc_.Role = ERDTownRole::Child; Pc_.At = Mid + Va * (K - 1) * 500.f + Ua * 300.f; Pc_.Wander = 1800.f; Pc_.Index = K; TownPosts.Add(Pc_); }
		FTownPost Pi; Pi.Role = ERDTownRole::Idiot; Pi.At = Mid - Ua * 2500.f; Pi.Wander = 3500.f; TownPosts.Add(Pi);
	}
	{
		// the graves in rows, a fence round them with its gate toward the town; the mourner among them
		FRandomStream RG((int32)(R.GetInitialSeed() ^ 0x6A7EB0u));
		for (int32 X = Gy.Min.X + 1; X < Gy.Max.X - 1; X += 2)
			for (int32 Y = Gy.Min.Y + 1; Y < Gy.Max.Y - 1; Y += 2)
			{
				FTownSpot G; G.Kind = TS_Grave; G.At = TileWorld(FIntPoint(X, Y)) + FVector(RG.FRandRange(-40, 40), RG.FRandRange(-40, 40), 0); G.Yaw = 90.f * RG.RandRange(0, 3) + RG.FRandRange(-8, 8);
				TownSpots.Add(G);
				Blocked[Idx(FIntPoint(X, Y))] = 1;
			}
		FTownSpot Gc; Gc.Kind = TS_Graveyard; Gc.At = (TileWorld(Gy.Min) + TileWorld(Gy.Max - FIntPoint(1, 1))) * 0.5f; TownSpots.Add(Gc);
		FTownPost Pm; Pm.Role = ERDTownRole::Mourner; Pm.At = Gc.At + FVector(150, 0, 0); Pm.Yaw = RG.FRandRange(0, 360); TownPosts.Add(Pm);
	}
	// ---- the posts at the buildings: the keepers inside by their service, the guards at the gate and the castle's door, the
	// captain before the castle, the militia on the lane inside the wall, the refugees by the gate, the residents
	{
		const FVector Ua = FVector(RDTDir4[F.Side(1, 0)].X, RDTDir4[F.Side(1, 0)].Y, 0.f), Va = FVector(RDTDir4[F.Side(0, 1)].X, RDTDir4[F.Side(0, 1)].Y, 0.f);
		const FVector GateIn = TownGate - TownGateOut * 450.f;
		for (int32 K = 0; K < 2; ++K) { FTownPost G; G.Role = ERDTownRole::Guard; G.At = GateIn + Va * (K ? 380.f : -380.f); G.Yaw = TownGateOut.Rotation().Yaw + 180.f; G.Index = K; TownPosts.Add(G); }
		const FTownBld& C = TownBlds[CastleBld];
		const FVector CDoor = TileWorld(C.DoorTile) + FVector(RDTDir4[C.DoorSide].X, RDTDir4[C.DoorSide].Y, 0.f) * 330.f;
		for (int32 K = 0; K < 2; ++K) { FTownPost G; G.Role = ERDTownRole::Guard; G.At = CDoor + Va * (K ? 300.f : -300.f); G.Yaw = (-Ua).Rotation().Yaw; G.Index = 2 + K; TownPosts.Add(G); }
		FTownPost Cp; Cp.Role = ERDTownRole::Captain; Cp.At = CDoor - Ua * 650.f + Va * 380.f; Cp.Yaw = (-Ua).Rotation().Yaw; TownPosts.Add(Cp);
		for (int32 K = 0; K < 4; ++K)
		{
			// (the militia walk the lane inside the wall, each its stretch)
			FTownPost Mi; Mi.Role = ERDTownRole::Militia; Mi.Index = K; Mi.Wander = 4000.f;
			const int32 A = 20 + K * 36;
			Mi.At = TileWorld(K % 2 ? F.Tile(A, 1) : F.Tile(A, S - 2));
			TownPosts.Add(Mi);
		}
		for (int32 K = 0; K < 4; ++K)
		{
			FTownPost Rf; Rf.Role = ERDTownRole::Refugee; Rf.Index = K; Rf.Wander = 300.f;
			Rf.At = GateIn + Ua * 500.f + Va * ((K % 2 ? 1.f : -1.f) * (650.f + 120.f * K)); Rf.Yaw = R.FRandRange(0, 360);
			TownPosts.Add(Rf);
		}
		// (a camp of the refugees: tents by the wall near the gate)
		for (int32 K = 0; K < 3; ++K)
		{
			FTownSpot T; T.Kind = TS_Tent; T.At = GateIn + Ua * (900.f + 350.f * K) + Va * (K % 2 ? 1300.f : -1300.f); T.Yaw = Va.Rotation().Yaw + (K % 2 ? 180.f : 0.f);
			TownSpots.Add(T);
		}
		for (int32 BI = 0; BI < TownBlds.Num(); ++BI)
		{
			const FTownBld& B = TownBlds[BI];
			if (B.Rooms.Num() == 0) continue;
			const FRoom& Rm = Rooms[B.Rooms[0]];
			const FVector Ctr = (TileWorld(Rm.Min) + TileWorld(Rm.Max - FIntPoint(1, 1))) * 0.5f;
			const FVector In_ = -FVector(RDTDir4[B.DoorSide].X, RDTDir4[B.DoorSide].Y, 0.f);
			auto Post = [&](ERDTownRole InRole, const FVector& At, float Wander = 0.f, int32 Index = 0)
			{
				FTownPost P_; P_.Role = InRole; P_.At = At; P_.Bld = BI; P_.Wander = Wander; P_.Index = Index; P_.Yaw = (-In_).Rotation().Yaw;
				TownPosts.Add(P_);
			};
			// (each keeper a little inside the door, facing it: furniture keeps to the walls and the lane is free there)
			const FVector Inside = TileWorld(B.DoorTile) + In_ * 260.f;
			switch (B.Kind)
			{
			case TK_Smithy: Post(ERDTownRole::Smith, Inside); break;
			case TK_Store: Post(ERDTownRole::Trader, Inside); break;
			case TK_Healer: Post(ERDTownRole::Healer, Inside); break;
			case TK_Temple: Post(ERDTownRole::Priest, Inside + In_ * 300.f); break;
			case TK_Storehouse: Post(ERDTownRole::Keeper, Inside); break;
			case TK_Tavern: Post(ERDTownRole::Innkeeper, Inside); Post(ERDTownRole::Drunk, Ctr + (Ctr - Inside).GetSafeNormal2D() * 120.f); Post(ERDTownRole::Scholar, Inside + In_ * 220.f + FVector(In_.Y, -In_.X, 0) * 220.f); break;
			case TK_Barracks: for (int32 K = 0; K < 3; ++K) Post(ERDTownRole::Soldier, Ctr + FVector(In_.Y, -In_.X, 0) * (K - 1) * 280.f, 0.f, K); break;
			// (outside, beside the door, not before it: F at the door must reach the door)
			case TK_Witch: Post(ERDTownRole::Witch, TileWorld(B.DoorTile) - In_ * 260.f + FVector(In_.Y, -In_.X, 0) * 230.f); break;
			case TK_Home: if (B.State == 0 && FRandomStream((int32)(B.Seed ^ 0x51u)).FRand() < 0.6f) Post(ERDTownRole::Townsfolk, TileWorld(B.DoorTile) - In_ * 260.f + FVector(In_.Y, -In_.X, 0) * 230.f, 350.f, BI); break;
			default: break;
			}
		}
	}
	// the still: copper pot and barrels beside the tavern's door side
	for (const FTownBld& B : TownBlds)
		if (B.Kind == TK_Tavern)
		{
			const FVector Out = FVector(RDTDir4[B.DoorSide].X, RDTDir4[B.DoorSide].Y, 0.f), Across(Out.Y, -Out.X, 0.f);
			FTownSpot St; St.Kind = TS_Still;
			const float Half = (B.DoorSide < 2 ? B.Max.Y - B.Min.Y : B.Max.X - B.Min.X) * Generator->TileSize * 0.5f;
			St.At = TileWorld(B.DoorTile) + Out * 360.f + Across * FMath::Min(Half - 150.f, 520.f); St.Yaw = Out.Rotation().Yaw;
			TownSpots.Add(St);
		}
	UE_LOG(LogRDTown, Log, TEXT("RDTOWN plan seed %d gate side %d: %d buildings (%d rooms), %d spots, %d posts"), R.GetInitialSeed(), F.G, TownBlds.Num(), Rooms.Num(), TownSpots.Num(), TownPosts.Num());
}

// ------------------------------------------------------------------------------------------------ the building's frame
FName ARDSection::TownPiece(const FTownBld& B, const TCHAR* Part) const
{
	static const TCHAR* Styles[] = { TEXT("Timber"), TEXT("Stone"), TEXT("Thatch"), TEXT("Burnt") };
	return FName(*FString::Printf(TEXT("Town.%s_%s"), Styles[FMath::Min<int32>(B.Style, 3)], Part));
}

float ARDSection::TownBldYaw(const FTownBld& B) const
{
	// (the building's +X is its door's way out)
	const FIntPoint D = RDTDir4[B.DoorSide];
	return FMath::RadiansToDegrees(FMath::Atan2((float)D.Y, (float)D.X));
}

FVector ARDSection::TownBldPoint(const FTownBld& B, float X, float Y, float Z) const
{
	const FVector C = (TileWorld(B.Min) + TileWorld(B.Max - FIntPoint(1, 1))) * 0.5f;
	return C + FRotator(0, TownBldYaw(B), 0).RotateVector(FVector(X, Y, 0)) + FVector(0, 0, Z);
}

int32 ARDSection::TownBuildingAt(FVector L) const
{
	const int32 RI = RoomAt(L);
	if (RI < 0) return -1;
	for (int32 BI = 0; BI < TownBlds.Num(); ++BI) if (TownBlds[BI].Rooms.Contains(RI)) return BI;
	return -1;
}

// ------------------------------------------------------------------------------------------------ the shells
void ARDSection::TownShellBuilding(int32 BI)
{
	FTownBld& B = TownBlds[BI];
	FRandomStream R((int32)(B.Seed ^ 0x13579bdfu));
	const float M = Generator->TileSize, WH = 300.f;
	// the style: stone for the temple, the smithy and the barracks; timber or thatch for the rest; a burned house's timbers
	if (B.Kind == TK_Castle)
	{
		// the dungeon's Castle theme: each room's own walls inward, the outside's walls outward a wall's thickness out, the
		// doorways through both; the floors the theme's; the roof flat stone with the castle kit's parapets along its edge
		const FName Wall(TEXT("Castle.Wall_Block")), Floor(TEXT("Castle.Floor_Stone"));
		const FRDPiece* Wp = Generator->Piece(Wall);
		const FRDPiece* Dp = Generator->Piece(TEXT("Doorway"));
		const float T = Wp ? FMath::Clamp((float)Wp->Size.X, 20.f, 120.f) : 60.f;
		const float H = Generator->RoomHeight;
		for (const int32 RI : B.Rooms)
		{
			const FRoom& Rm = Rooms[RI];
			for (int32 X = Rm.Min.X; X < Rm.Max.X; ++X)
				for (int32 Y = Rm.Min.Y; Y < Rm.Max.Y; ++Y)
				{
					const FIntPoint Tl(X, Y);
					const FVector C = TileWorld(Tl);
					AddPieceAt(Floor, C, 90.f * R.RandRange(0, 3));
					AddPieceAt(TEXT("Castle.Ceil_Room"), C + FVector(0, 0, H), 90.f * R.RandRange(0, 3));
					// the roof over it (a flat stone floor seen from above): the wall walk, walked on
					AddPieceAt(TEXT("Town.CastleRoof"), C + FVector(0, 0, H + 40.f), 90.f * R.RandRange(0, 3));
					for (int32 Side = 0; Side < 4; ++Side)
					{
						const FIntPoint Nb = Tl + RDTDir4[Side];
						const int32 On = In(Nb) ? Owner[Idx(Nb)] : -1;
						if (On == RI) continue;
						const bool bOut = !B.Rooms.Contains(On);
						const bool bDoor = DoorEdges.Contains(EdgeKey(Tl, Nb));
						const FVector Edge = C + FVector(RDTDir4[Side].X, RDTDir4[Side].Y, 0) * (M * 0.5f);
						const float Yaw = InwardYaw(Side);
						const FVector OutW = FRotator(0, Yaw, 0).RotateVector(FVector(-1, 0, 0));
						// (between two rooms each has its own wall, half a thickness into its room: their backs meet)
						const FVector At = bOut ? Edge : Edge - OutW * (T * 0.5f);
						if (bDoor)
						{
							AddPieceAt(TEXT("Doorway"), At, Yaw);
							// (the wall over the doorway up to the ceiling, not a whole piece's height: it stood 2.5 m through the
							// wall walk)
							for (float Z = Dp ? Dp->Size.Z - 2.f : 300.f; Z < H - 5.f; Z += Wp ? Wp->Size.Z - 2.f : 300.f)
							{
								const float Wz = Wp ? FMath::Max((float)Wp->Size.Z, 50.f) : 300.f;
								AddPiece(Wall, FTransform(FRotator(0, Yaw, 0), At + FVector(0, 0, Z), FVector(1.f, 1.f, FMath::Min(1.f, (H + 10.f - Z) / Wz))));
							}
							if (bOut)
							{
								// (the gate: the dungeon's doorway turned out, the outer face's stone over it to the wall walk)
								AddPieceAt(TEXT("Doorway"), Edge + OutW * T, Yaw + 180.f);
								const float Z0 = Dp ? Dp->Size.Z - 2.f : 300.f;
								CastleOuterFace(Edge, OutW, Yaw, T, Z0, CastleWalkTop(), Tl, Side, true);
							}
							continue;
						}
						for (float Z = 0.f; Z < H - 5.f; Z += Wp ? Wp->Size.Z - 2.f : 300.f) AddPieceAt(Wall, At + FVector(0, 0, Z), Yaw);
						// (the outside: Castle Forge's stone, arrow slits below, windows above, the walk and its battlements on top)
						if (bOut) CastleOuterFace(Edge, OutW, Yaw, T, 0.f, CastleWalkTop(), Tl, Side, false);
					}
				}
		}
		CastleTowersBuild(B);
		// the Mistgate: an arch in the hall's back wall, its glow (play: the generator's)
		AddPieceAt(TEXT("Town.MistArch"), MistgateAt - MistgateNormal * 30.f, MistgateNormal.Rotation().Yaw, 1.f, true);
		return;
	}
	B.Style = B.State == 1 ? 3 : (B.Kind == TK_Temple || B.Kind == TK_Smithy || B.Kind == TK_Barracks || B.Kind == TK_Chapel) ? 1
	        : B.Kind == TK_Witch ? 2 : (R.FRand() < 0.3f ? 2 : R.FRand() < 0.85f ? 0 : 1);
	const int32 Nx = B.DoorSide < 2 ? B.Max.X - B.Min.X : B.Max.Y - B.Min.Y;      // (depth along the door's way)
	const int32 Ny = B.DoorSide < 2 ? B.Max.Y - B.Min.Y : B.Max.X - B.Min.X;      // (width across)
	const float Hx = Nx * M * 0.5f, Hy = Ny * M * 0.5f;
	const float Yaw0 = TownBldYaw(B);
	const int32 DoorCell = B.DoorSide < 2 ? B.DoorTile.Y - B.Min.Y : B.DoorTile.X - B.Min.X;
	// (the building frame's +Y in tiles: which way the door's cell counts)
	const FVector Yw = FRotator(0, Yaw0, 0).RotateVector(FVector(0, 1, 0));
	const bool bYUp = (B.DoorSide < 2 ? Yw.Y : Yw.X) > 0.f;
	const int32 DoorK = bYUp ? DoorCell : Ny - 1 - DoorCell;
	auto WallT = [&](const FVector2D& P, const FVector2D& Out, float Z)
	{
		const FVector Ow = FRotator(0, Yaw0, 0).RotateVector(FVector(Out.X, Out.Y, 0));
		return FTransform(FRotator(0, Ow.Rotation().Yaw, 0), TownBldPoint(B, P.X, P.Y, Z));
	};
	const bool bBurnt = B.State == 1, bBoarded = B.State == 2;
	// ---- floor
	for (int32 I = 0; I < Nx; ++I)
		for (int32 J = 0; J < Ny; ++J)
			AddPieceAt(TownPiece(B, TEXT("Floor")), TownBldPoint(B, (I + 0.5f) * M - Hx, (J + 0.5f) * M - Hy, 2.f), Yaw0 + 90.f * R.RandRange(0, 3));
	// ---- walls, storey by storey (a burned house loses some, the upper storey most)
	struct FSide { FVector2D Out; int32 N; };
	const FSide Sides[4] = { { FVector2D(1, 0), Ny }, { FVector2D(-1, 0), Ny }, { FVector2D(0, 1), Nx }, { FVector2D(0, -1), Nx } };
	const FName Win2 = Generator->Piece(TownPiece(B, TEXT("WallWindow2"))) ? TownPiece(B, TEXT("WallWindow2")) : TownPiece(B, TEXT("WallWindow"));
	for (int32 Si = 0; Si < 4; ++Si)
	{
		const FSide& Sd = Sides[Si];
		for (int32 K = 0; K < Sd.N; ++K)
		{
			const FVector2D P = Si < 2 ? FVector2D(Sd.Out.X * Hx, (K + 0.5f) * M - Hy) : FVector2D((K + 0.5f) * M - Hx, Sd.Out.Y * Hy);
			for (int32 St = 0; St < B.Storeys; ++St)
			{
				const float Z = 2.f + St * WH;
				const bool bDoor = St == 0 && Si == 0 && K == DoorK;
				FName Nm = TownPiece(B, TEXT("Wall"));
				if (bDoor) Nm = TownPiece(B, TEXT("Doorway"));
				else
				{
					const float Chance = (B.Kind == TK_Temple || B.Kind == TK_Chapel) ? (St == 1 ? 0.85f : 0.3f) : B.Kind == TK_Storehouse ? 0.15f : Si == 0 ? 0.6f : 0.4f;
					if (R.FRand() < Chance) Nm = (B.Kind == TK_Temple || B.Kind == TK_Chapel || R.FRand() < 0.35f) ? Win2 : TownPiece(B, TEXT("WallWindow"));
				}
				// (a burned house: holes where the fire took the walls; never the doorway's)
				if (bBurnt && !bDoor && R.FRand() < (St == 0 ? 0.22f : 0.55f)) continue;
				AddPiece(Nm, WallT(P, Sd.Out, Z));
				// (a boarded house: planks across its lower windows (and the door, AddTownDoor))
				if (bBoarded && St == 0 && !bDoor && Nm != TownPiece(B, TEXT("Wall"))) AddPiece(TEXT("Town.Planks"), WallT(P + Sd.Out * 14.f, Sd.Out, Z + 120.f), true);
			}
		}
	}
	for (int32 Cx = -1; Cx <= 1; Cx += 2)
		for (int32 Cy = -1; Cy <= 1; Cy += 2)
			for (int32 St = 0; St < B.Storeys; ++St)
				AddPiece(TownPiece(B, TEXT("Pillar")), FTransform(FRotator(0, Yaw0, 0), TownBldPoint(B, Cx * Hx, Cy * Hy, 2.f + St * WH)));
	// ---- the roof: a gable along the building's longer side (none for a burned house: charred beams and a few rafters)
	const float Top = 2.f + B.Storeys * WH;
	const bool bRidgeY = Ny >= Nx;
	const FVector2D A = bRidgeY ? FVector2D(0, 1) : FVector2D(1, 0), C = bRidgeY ? FVector2D(1, 0) : FVector2D(0, 1);
	const int32 NAlong = bRidgeY ? Ny : Nx, Span = bRidgeY ? Nx : Ny;
	const float HAlong = NAlong * M * 0.5f, HAcross = Span * M * 0.5f;
	for (int32 Al = 0; Al < NAlong; ++Al)
		for (int32 Ac = 0; Ac < Span; ++Ac)
		{
			if (bBurnt && R.FRand() < 0.75f) continue;
			const bool bLow = Ac < Span / 2;
			const int32 Level = bLow ? Ac : Span - 1 - Ac;
			const FVector2D Out = C * (bLow ? -1.f : 1.f);
			const FVector2D P = A * ((Al + 0.5f) * M - HAlong) + C * ((Ac + 0.5f) * M - HAcross);
			const FTransform T = WallT(P, Out, Top + Level * M);
			// (an odd span's middle row is the ridge: the roof pieces of both sides meet over it)
			if (Span % 2 == 1 && Ac == Span / 2) { AddPiece(TownPiece(B, TEXT("Roof")), WallT(P, C * -1.f, Top + Level * M)); AddPiece(TownPiece(B, TEXT("Roof")), WallT(P, C, Top + Level * M)); continue; }
			AddPiece(TownPiece(B, TEXT("Roof")), T);
			if (Level == 0) AddPiece(TownPiece(B, TEXT("RoofTrim")), T);
			const FVector2D Yp(-Out.Y, Out.X);
			const float Dy = FVector2D::DotProduct(Yp, A);
			if (Al == NAlong - 1) AddPiece(TownPiece(B, Dy > 0.f ? TEXT("RoofEndL") : TEXT("RoofEndR")), T);
			if (Al == 0) AddPiece(TownPiece(B, Dy > 0.f ? TEXT("RoofEndR") : TEXT("RoofEndL")), T);
		}
	if (!bBurnt)
		for (int32 End = 0; End < 2; ++End)
		{
			const FVector2D Out = A * (End == 0 ? -1.f : 1.f);
			const FVector2D Yp(-Out.Y, Out.X);
			const FVector2D P0 = A * ((End == 0 ? 0 : NAlong) * M - HAlong);
			for (int32 Lv = 0; Lv < Span / 2; ++Lv)
			{
				// (each level of the gable: a triangle at its two ends, plain wall between them)
				const float Half = (Span * 0.5f - Lv) * M;
				AddPiece(TownPiece(B, TEXT("GableNeg")), WallT(P0 + Yp * (-Half + M * 0.5f), Out, Top + Lv * M));
				AddPiece(TownPiece(B, TEXT("GablePos")), WallT(P0 + Yp * (Half - M * 0.5f), Out, Top + Lv * M));
				for (float Yv = -Half + M; Yv < Half - M + 1.f; Yv += M) AddPiece(TownPiece(B, TEXT("Wall")), WallT(P0 + Yp * (Yv + 0.f), Out, Top + Lv * M));
			}
		}
	// a burned house: rubble and charred beams inside
	if (bBurnt)
		for (int32 K = 0; K < 3 + Nx * Ny / 6; ++K)
			AddPieceAt(R.RandBool() ? FName(TEXT("Debris")) : FName(TEXT("Town.CharredBeam")), TownBldPoint(B, R.FRandRange(-Hx + 80.f, Hx - 80.f), R.FRandRange(-Hy + 80.f, Hy - 80.f), 2.f), R.FRandRange(0, 360), 1.f, true);
	// its sign over the door (the trades')
	if (B.Kind != TK_Home)
		AddPiece(TEXT("Town.Sign"), WallT(FVector2D(Hx + 25.f, (DoorK + 0.5f) * M - Hy + 140.f), FVector2D(1, 0), 250.f), true);
}

// ------------------------------------------------------------------------------------------------ doors
void ARDSection::AddTownDoor(int32 BI, FIntPoint RoomTile, FIntPoint OutTile, FName Piece, int32 Room)
{
	if (!bBuildInteractive) return;
	const FRDPiece* P = Generator->Piece(Piece);
	if (!P || !P->Mesh) return;
	const FVector A = TileWorld(RoomTile), Bw = TileWorld(OutTile);
	const FVector Mid = (A + Bw) * 0.5f + FVector(0, 0, 2.f);
	const FVector Out = (Bw - A).GetSafeNormal();
	const float Yaw = Out.Rotation().Yaw;
	const FRotator Rot(0, Yaw, 0);
	// (the kit's frame: +X outward, the hinge at P->Hinge, the closed leaf running toward -Y from it; the leaf piece spans +Y
	// from its origin: its pivot is turned half round, so the pivot's +X points into the house (the village's doors))
	const FVector HingeW = Mid + Rot.RotateVector(FVector(P->Hinge.X, P->Hinge.Y, 0)) + FVector(0, 0, P->Hinge.Z);
	USceneComponent* Pv = AddPivot(RootComponent, FTransform(FRotator(0, Yaw + 180.f, 0), HingeW - GetActorLocation()));
	UStaticMeshComponent* Leaf = AddMesh(Pv, P->Mesh, P->Adjust, true);
	FMover Mv; Mv.Pivot = Pv; Mv.Parts = { Leaf }; Mv.Closed = Pv->GetRelativeRotation().Quaternion(); Mv.bDoor = true; Mv.Kind = TEXT("door");
	Mv.LeafSign = 1.f;
	Mv.Center = Mid + FVector(0, 0, 100);
	Mv.Normal = -Out;
	Mv.TileA = RoomTile; Mv.TileB = OutTile;
	const int32 DI = Doors.Add(Mv);
	if (TownBlds.IsValidIndex(BI) && TownBlds[BI].Door < 0) TownBlds[BI].Door = DI;
	// (a boarded house: planks nailed across its door until she pries them loose)
	if (TownBlds.IsValidIndex(BI) && TownBlds[BI].bBoarded)
		if (const FRDPiece* Pl = Generator->Piece(TEXT("Town.Planks")); Pl && Pl->Mesh)
		{
			TArray<TWeakObjectPtr<UStaticMeshComponent>>& L = TownBoards.FindOrAdd(BI);
			for (int32 K = 0; K < 2; ++K)
			{
				UStaticMeshComponent* C = AddMesh(RootComponent, Pl->Mesh, Pl->Adjust * FTransform(FRotator(0, Yaw, K ? 18.f : -18.f), Mid + Out * 22.f + FVector(0, 0, 90.f + 70.f * K) - GetActorLocation()), true);
				L.Add(C);
			}
		}
}

void ARDSection::TownDoors()
{
	for (int32 BI = 0; BI < TownBlds.Num(); ++BI) TownBlds[BI].Door = -1;
	TownBoards.Reset();
	for (const TPair<int64, int32>& E : DoorEdges) (void)E;
	// (the same order as the plan's edges: each building's doors in turn)
	TArray<TPair<int64, int32>> Edges;
	for (const TPair<int64, int32>& E : DoorEdges) Edges.Add(E);
	Edges.Sort([](const TPair<int64, int32>& A, const TPair<int64, int32>& B) { return A.Value < B.Value; });
	TMap<int64, int32> Remap;
	for (const TPair<int64, int32>& E : Edges)
	{
		// (the edge's two tiles back from its key)
		const int64 K = E.Key;
		const int32 Ax = (int32)((K >> 40) & 0xFFFFF) - 512, Ay = (int32)((K >> 20) & 0xFFFFF) - 512, Dd = (int32)(K & 0xFFFFF) - 4;
		const FIntPoint A(Ax, Ay), Bt = A + (Dd == 2 ? FIntPoint(1, 0) : FIntPoint(0, 1));
		const int32 Ra = RoomAtLocal(A), Rb = RoomAtLocal(Bt);
		const int32 Rm = Ra >= 0 ? Ra : Rb;
		const FIntPoint RoomT = Ra >= 0 ? A : Bt, OutT = Ra >= 0 ? Bt : A;
		int32 BI = -1;
		for (int32 I = 0; I < TownBlds.Num(); ++I) if (TownBlds[I].Rooms.Contains(Rm)) { BI = I; break; }
		const bool bCastle = BI == CastleBld;
		const int32 First = Doors.Num();
		if (bCastle)
		{
			// (the castle: the dungeon's double doors, both leaves)
			AddDoor(RoomT, OutT, Rm);
			if (Doors.Num() > First && TownBlds.IsValidIndex(BI) && TownBlds[BI].Door < 0) TownBlds[BI].Door = First;
		}
		else AddTownDoor(BI, RoomT, OutT, TownPiece(TownBlds[BI], TEXT("Door")), Rm);
		if (Doors.Num() > First) Remap.Add(K, First);
	}
	DoorEdges = Remap;
}

int32 ARDSection::BoardedDoorBld(int32 Door) const
{
	for (int32 BI = 0; BI < TownBlds.Num(); ++BI) if (TownBlds[BI].Door == Door && TownBlds[BI].bBoarded) return BI;
	return -1;
}

int32 ARDSection::OpenDoorAhead(const FVector& L, const FVector& Dir, float Reach, bool bByMonster)
{
	const FIntPoint Cur = WorldToLocal(L), Ahead = WorldToLocal(L + Dir.GetSafeNormal2D() * Reach);
	if (Ahead == Cur || FMath::Abs(Ahead.X - Cur.X) + FMath::Abs(Ahead.Y - Cur.Y) != 1) return -1;
	const int32 Dr = DoorBetween(Cur, Ahead);
	if (Dr < 0 || IsDoorOpenIndex(Dr)) return -1;
	if (BoardedDoorBld(Dr) >= 0) return 1;
	if (!IsTargetOpen(true, Dr)) ToggleDoor(Dr, L, bByMonster);
	return 0;
}

bool ARDSection::PryBoards(int32 BI)
{
	if (!TownBlds.IsValidIndex(BI) || !TownBlds[BI].bBoarded) return false;
	TownBlds[BI].bBoarded = false;
	if (TArray<TWeakObjectPtr<UStaticMeshComponent>>* L = TownBoards.Find(BI))
		for (const TWeakObjectPtr<UStaticMeshComponent>& C : *L) if (UStaticMeshComponent* Cp = C.Get()) { Cp->SetVisibility(false); Cp->SetCollisionEnabled(ECollisionEnabled::NoCollision); }
	return true;
}

TArray<FVector> ARDSection::GetTownDoorPoints() const
{
	TArray<FVector> Out;
	for (const FTownBld& B : TownBlds) if (Doors.IsValidIndex(B.Door)) Out.Add(Doors[B.Door].Center);
	return Out;
}

// ------------------------------------------------------------------------------------------------ inside
void ARDSection::TownFurnish(FRandomStream& R, int32 BI)
{
	const FTownBld& B = TownBlds[BI];
	for (const int32 RI : B.Rooms) Furnish(R, RI);
	if (B.Rooms.Num() == 0) return;
	// what the trades add to the dungeon's furnishing: their service's piece (a counter, a basin, the stash's chest) by the wall
	// across from the door, the tavern's tables, the witch's cauldron
	const int32 RI = B.Rooms[0];
	const FRoom& Rm = Rooms[RI];
	const FVector Ctr = (TileWorld(Rm.Min) + TileWorld(Rm.Max - FIntPoint(1, 1))) * 0.5f;
	const FVector In_ = -FVector(RDTDir4[B.DoorSide].X, RDTDir4[B.DoorSide].Y, 0.f);
	const float Depth = (B.DoorSide < 2 ? Rm.Max.X - Rm.Min.X : Rm.Max.Y - Rm.Min.Y) * Generator->TileSize;
	const FVector Back = TileWorld(B.DoorTile) + In_ * (Depth - Generator->TileSize * 0.5f - 90.f);
	// (after the furnishing, so that it keeps clear of what is there (the room's footprints are kept until the next room):
	// along the back wall from its middle out, the first place free; the service's place is where it went)
	const FVector Along(In_.Y, -In_.X, 0.f);
	auto Service = [&](uint8 Kind, FName Piece, const FVector& At, float Yaw)
	{
		FVector Put = At;
		if (!Piece.IsNone())
		{
			FurnRoom = RI;
			bool bPut = false;
			for (const float Off : { 0.f, 160.f, -160.f, 320.f, -320.f, 480.f, -480.f })
				if (AddPieceAt(Piece, At + Along * Off, Yaw)) { Put = At + Along * Off; bPut = true; break; }
			FurnRoom = -1;
			if (bPut) MarkBlocked(Put, Yaw, FVector2D(120.f, 120.f), true);
			else UE_LOG(LogRDTown, Warning, TEXT("RDTOWN no room for the %s's %s"), *RDTownKindName(B.Kind), *Piece.ToString());
		}
		FTownSpot Sp; Sp.Kind = Kind; Sp.At = Put; Sp.Yaw = Yaw; Sp.Bld = BI;
		TownSpots.Add(Sp);
	};
	const float FaceDoor = (-In_).Rotation().Yaw;
	switch (B.Kind)
	{
	case TK_Store: Service(TS_Counter, TEXT("TableLong"), Back, FaceDoor + 90.f); break;
	case TK_Healer: Service(TS_Basin, TEXT("Fountain"), Back, FaceDoor); break;
	case TK_Temple: Service(TS_Altar, NAME_None, Back, FaceDoor); break;
	case TK_Storehouse: Service(TS_Stash, TEXT("Town.StashChest"), Back, FaceDoor); break;
	case TK_Smithy: Service(TS_Smith, NAME_None, TileWorld(B.DoorTile) + In_ * 450.f, FaceDoor); break;
	case TK_Tavern:
		Service(TS_Bar, TEXT("TableLong"), Back, FaceDoor + 90.f);
		for (const FVector& Q : { Ctr + FVector(In_.Y, -In_.X, 0) * 380.f, Ctr - FVector(In_.Y, -In_.X, 0) * 380.f })
		{
			FurnRoom = RI;
			if (AddPieceAt(TEXT("TableSmall"), Q, 0.f)) { MarkBlocked(Q, 0.f, FVector2D(120, 120)); for (int32 K = 0; K < 2; ++K) AddPieceAt(TEXT("Stool"), Q + FVector(K ? 90.f : -90.f, 0, 0), K ? 180.f : 0.f); }
			FurnRoom = -1;
		}
		break;
	case TK_Witch: FurnRoom = RI; AddPieceAt(TEXT("Cauldron"), Ctr, 0.f); FurnRoom = -1; break;
	default: break;
	}
}

// ------------------------------------------------------------------------------------------------ outdoors
void ARDSection::TownOutdoors(FRandomStream& R0, int32 Step)
{
	FRandomStream R((int32)(Seed ^ (0x0D00 + Step * 7919)));
	const float M = Generator->TileSize;
	const FVector2D L(GetActorLocation().X, GetActorLocation().Y);
	auto Free = [&](const FIntPoint& T) { return In(T) && Type[Idx(T)] == 2 && !Blocked[Idx(T)]; };
	switch (Step)
	{
	case 0:
	{
		// ---- the town wall: on the ring's line, its walls facing out and in, a walkway's parapet on top; the gate's frame and
		// its barred leaves; the towers
		const int32 A0 = FMath::Max(4, (N - 160) / 2), A1 = N - A0;
		const FRDPiece* Wp = Generator->Piece(TEXT("Town.CityWall"));
		const float Wh = Wp ? Wp->Size.Z - 4.f : 300.f, Wl = Wp ? FMath::Max((float)Wp->Size.Y, 100.f) : 300.f;
		auto Along = [&](const FVector& From, const FVector& Dir, float Len, float InYaw)
		{
			for (float D = 0.f; D < Len - 1.f; D += Wl)
			{
				const FVector P = From + Dir * (D + Wl * 0.5f);
				if (FVector::Dist2D(P, TownGate) < 160.f) continue;            // (the gate's gap: its frame stands there)
				// (a wall piece runs along its +Y, its face toward +X: the parapet's the same; plain stone below, an arrow slit in
				// one upper segment of three, by a hash of the place: until 2026-11-02 every piece was one with an arched doorway)
				const uint32 Hh = HashCombine(GetTypeHash(FIntPoint(FMath::RoundToInt(P.X), FMath::RoundToInt(P.Y))), 0x5117u);
				AddPieceAt(TEXT("Town.CityWall"), P, InYaw);
				AddPieceAt(Hh % 3 == 0 && Generator->Piece(TEXT("Town.CityWallSlit")) ? FName(TEXT("Town.CityWallSlit")) : FName(TEXT("Town.CityWall")), P + FVector(0, 0, Wh), InYaw);
				AddPieceAt(TEXT("Town.Parapet"), P + FVector(0, 0, 2 * Wh), InYaw, 1.f, true);
			}
		};
		const FVector C0 = FVector(L.X + A0 * M, L.Y + A0 * M, 0), C1 = FVector(L.X + A1 * M, L.Y + A1 * M, 0);
		Along(FVector(C0.X, C0.Y, 0), FVector(0, 1, 0), (A1 - A0) * M, 0.f);          // (-X wall, facing in +X)
		Along(FVector(C1.X, C0.Y, 0), FVector(0, 1, 0), (A1 - A0) * M, 180.f);
		Along(FVector(C0.X, C0.Y, 0), FVector(1, 0, 0), (A1 - A0) * M, 90.f);
		Along(FVector(C0.X, C1.Y, 0), FVector(1, 0, 0), (A1 - A0) * M, -90.f);
		// the gate: its frame across the gap, two leaves shut, a beam barring them, a blocker (the wilderness is for later)
		const float GYaw = TownGateOut.Rotation().Yaw;
		// (its pieces run across the gap along their +Y, their faces outward)
		AddPieceAt(TEXT("Town.Gate"), TownGate, GYaw, 1.f, true);
		AddPieceAt(TEXT("Town.GateLeaves"), TownGate - TownGateOut * 20.f, GYaw, 1.f, true);
		AddPieceAt(TEXT("Town.GateBar"), TownGate - TownGateOut * 45.f + FVector(0, 0, 150.f), GYaw, 1.f, true);
		if (bBuildStatic)
		{
			UBoxComponent* Bx = NewObject<UBoxComponent>(this, NAME_None, RF_Transactional);
			Bx->SetupAttachment(RootComponent);
			Bx->SetBoxExtent(FVector(40.f, 330.f, 400.f));
			Bx->SetCollisionProfileName(TEXT("BlockAll"));
			Bx->SetHiddenInGame(true);
			Bx->RegisterComponent();
			Bx->SetWorldLocationAndRotation(TownGate + FVector(0, 0, 400.f), FRotator(0, GYaw, 0));
			AddInstanceComponent(Bx);
		}
		for (const FTownSpot& Sp : TownSpots)
		{
			if (Sp.Kind != TS_Tower) continue;
			// (a square tower two tiles a side: each face two wall segments 3 m from its middle, three high, facing out, and
			// parapets round its top)
			for (int32 K = 0; K < 4; ++K)
			{
				const float Yw = 90.f * K;
				const FRotator Rt(0, Yw, 0);
				for (int32 Sg = -1; Sg <= 1; Sg += 2)
				{
					const FVector Fc = Sp.At + Rt.RotateVector(FVector(-300.f, 150.f * Sg, 0));
					// (plain below, an arrow slit, a small window at the top)
					for (int32 H = 0; H < 3; ++H)
					{
						FName Nm(TEXT("Town.CityWall"));
						if (H == 1 && Sg < 0 && Generator->Piece(TEXT("Town.CityWallSlit"))) Nm = TEXT("Town.CityWallSlit");
						if (H == 2 && Sg > 0 && Generator->Piece(TEXT("Town.CityWallWin"))) Nm = TEXT("Town.CityWallWin");
						AddPieceAt(Nm, Fc + FVector(0, 0, H * Wh), Yw + 180.f);
					}
					AddPieceAt(TEXT("Town.Parapet"), Fc + FVector(0, 0, 3 * Wh), Yw + 180.f, 1.f, true);
				}
			}
			AddPieceAt(TEXT("Town.TowerRoof"), Sp.At + FVector(0, 0, 3 * Wh + 20.f), 0.f, 1.f, true);
			for (int32 Dx = -1; Dx <= 0; ++Dx) for (int32 Dy = -1; Dy <= 0; ++Dy)
			{
				const FIntPoint T = WorldToLocal(Sp.At + FVector(Dx * M + 10.f, Dy * M + 10.f, 0));
				if (In(T) && Type[Idx(T)] == 2) { Type[Idx(T)] = 0; Owner[Idx(T)] = -1; }
			}
			// (a torch on its town face)
			AddTorch(Sp.At + FVector(0, 0, 380.f) - (Sp.At - FVector(L.X + N * M * 0.5f, L.Y + N * M * 0.5f, 0)).GetSafeNormal2D() * 280.f,
				(FVector(L.X + N * M * 0.5f, L.Y + N * M * 0.5f, 0) - Sp.At).Rotation().Yaw, 140.f);
		}
		break;
	}
	case 1:
	{
		// ---- the square: the well, the quest board, the stalls, the lamps; the teleport circle's stones
		for (const FTownSpot& Sp : TownSpots)
		{
			switch (Sp.Kind)
			{
			case TS_Well: AddPieceAt(TEXT("Town.Well"), Sp.At, Sp.Yaw); AddPieceAt(TEXT("Town.WellTop"), Sp.At, Sp.Yaw); break;
			case TS_Board: AddPieceAt(TEXT("Town.Board"), Sp.At, Sp.Yaw); AddPieceAt(TEXT("Town.BoardNotes"), Sp.At, Sp.Yaw, 1.f, true); break;
			case TS_Stall: AddPieceAt(FName(*FString::Printf(TEXT("Town.Stall%d"), 1 + R.RandRange(0, 2))), Sp.At, Sp.Yaw); break;
			case TS_Lamp:
				AddPieceAt(TEXT("Town.Lamp"), Sp.At, R.FRandRange(0, 360));
				AddEffect(TEXT("BrazierFire"), Sp.At + FVector(0, 0, 105.f), 1.2f);
				AddLight(Sp.At + FVector(0, 0, 180.f), FLinearColor(1.f, 0.58f, 0.26f), 320.f, 2600.f, true, 0.18f);
				break;
			case TS_Circle:
				for (int32 K = 0; K < 8; ++K)
					AddPieceAt(TEXT("Town.CircleStone"), Sp.At + FRotator(0, K * 45.f, 0).RotateVector(FVector(560.f, 0, 0)), K * 45.f + 90.f);
				AddPieceAt(TEXT("Town.CircleFloor"), Sp.At, 0.f, 1.f, true);
				break;
			case TS_Still: AddPieceAt(TEXT("Town.StillPot"), Sp.At, Sp.Yaw); AddPieceAt(TEXT("Town.Keg"), Sp.At + FRotator(0, Sp.Yaw, 0).RotateVector(FVector(0, 150.f, 0)), Sp.Yaw); AddPieceAt(TEXT("Town.Keg"), Sp.At + FRotator(0, Sp.Yaw, 0).RotateVector(FVector(0, -150.f, 0)), Sp.Yaw + 30.f); break;
			case TS_Mill: AddPieceAt(TEXT("Town.Mill"), Sp.At, Sp.Yaw); break;
			case TS_Tent: AddPieceAt(TEXT("Town.Tent"), Sp.At, Sp.Yaw); AddPieceAt(TEXT("Town.Firepit"), Sp.At + FRotator(0, Sp.Yaw, 0).RotateVector(FVector(330.f, 0, 0)), 0.f); break;
			default: break;
			}
			// (what stands outdoors blocks the tiles under it for whoever walks the paths)
			if (Sp.Kind == TS_Well || Sp.Kind == TS_Board || Sp.Kind == TS_Stall || Sp.Kind == TS_Still || Sp.Kind == TS_Tent)
				MarkBlocked(Sp.At, Sp.Yaw, FVector2D(260.f, 260.f), true);
			if (Sp.Kind == TS_Mill) MarkBlocked(Sp.At, 0.f, FVector2D(900.f, 900.f), true);
		}
		break;
	}
	case 2:
	{
		// ---- the graveyard: its stones, a fence round it with a gate, a dead tree
		for (const FTownSpot& Sp : TownSpots)
		{
			if (Sp.Kind == TS_Grave) AddPieceAt(FName(*FString::Printf(TEXT("Town.Grave%d"), 1 + R.RandRange(0, 7))), Sp.At, Sp.Yaw);
			if (Sp.Kind != TS_Graveyard) continue;
			// (the fence on the graveyard's rectangle, found again from the graves' extent; its gate in the middle of the side
			// that faces the town's middle)
			FBox2D Bx(ForceInit);
			for (const FTownSpot& G : TownSpots) if (G.Kind == TS_Grave) Bx += FVector2D(G.At.X, G.At.Y);
			Bx = Bx.ExpandBy(260.f);
			const FRDPiece* Fp = Generator->Piece(TEXT("Town.Fence"));
			const float Fl = Fp ? FMath::Max((float)Fp->Size.Y, 100.f) : 200.f;
			const FVector2D Cn[4] = { Bx.Min, FVector2D(Bx.Max.X, Bx.Min.Y), Bx.Max, FVector2D(Bx.Min.X, Bx.Max.Y) };
			const FVector2D Mid = Bx.GetCenter(), Town(L.X + N * M * 0.5f, L.Y + N * M * 0.5f);
			int32 GateSide = 0; float GateDot = -MAX_flt;
			for (int32 K = 0; K < 4; ++K)
			{
				const float Dt = FVector2D::DotProduct(((Cn[K] + Cn[(K + 1) % 4]) * 0.5f - Mid).GetSafeNormal(), (Town - Mid).GetSafeNormal());
				if (Dt > GateDot) { GateDot = Dt; GateSide = K; }
			}
			for (int32 K = 0; K < 4; ++K)
			{
				const FVector2D P0 = Cn[K], P1 = Cn[(K + 1) % 4];
				const FVector2D D = (P1 - P0).GetSafeNormal();
				const float Len = FVector2D::Distance(P0, P1);
				const float FYaw = FMath::RadiansToDegrees(FMath::Atan2(D.Y, D.X)) - 90.f;
				for (float U = 0.f; U < Len - 10.f; U += Fl)
				{
					const FVector2D Q = P0 + D * (U + Fl * 0.5f);
					const bool bGate = K == GateSide && FMath::Abs(U + Fl * 0.5f - Len * 0.5f) < Fl * 0.6f;
					AddPieceAt(bGate ? FName(TEXT("Town.FenceGate")) : FName(TEXT("Town.Fence")), FVector(Q, 0.f), FYaw);
				}
			}
			AddPieceAt(TEXT("Town.DeadTree"), Sp.At + FVector(R.FRandRange(-300, 300), R.FRandRange(-300, 300), 0), R.FRandRange(0, 360));
		}
		break;
	}
	case 3:
	{
		// ---- the barracks' yard: training dummies, a target, a weapon stand before its door; carts, hay, sacks by the homes
		for (const FTownBld& B : TownBlds)
		{
			const FVector Out = FVector(RDTDir4[B.DoorSide].X, RDTDir4[B.DoorSide].Y, 0.f), Across(Out.Y, -Out.X, 0.f);
			const FVector Door = TileWorld(B.DoorTile) + Out * 450.f;
			if (B.Kind == TK_Barracks)
			{
				for (int32 K = -1; K <= 1; K += 2)
				{
					const FVector P = Door + Across * K * 560.f;
					if (Free(WorldToLocal(P))) { AddPieceAt(K < 0 ? FName(TEXT("Town.Dummy")) : FName(TEXT("Town.Target")), P, Out.Rotation().Yaw + 180.f); MarkBlocked(P, 0.f, FVector2D(150, 150), true); }
				}
				continue;
			}
			if (B.Kind != TK_Home || B.State == 1 || R.FRand() > 0.45f) continue;
			const FVector P = Door + Across * (R.RandBool() ? 1.f : -1.f) * 420.f;
			if (!Free(WorldToLocal(P))) continue;
			static const TCHAR* Yard[] = { TEXT("Town.Cart"), TEXT("Town.Hay"), TEXT("Town.Sacks"), TEXT("Town.Logs"), TEXT("Town.Cart2") };
			AddPieceAt(Yard[R.RandRange(0, 4)], P, R.FRandRange(0, 360));
			MarkBlocked(P, 0.f, FVector2D(200, 200), true);
		}
		break;
	}
	case 4:
	{
		// ---- trees and bushes on the free ground away from the roads (never on a road, a doorway's front or the square)
		TArray<uint8> Road; Road.Init(0, N * N);
		for (const FIntRect& Rr : TownRoads) for (int32 X = Rr.Min.X; X < Rr.Max.X; ++X) for (int32 Y = Rr.Min.Y; Y < Rr.Max.Y; ++Y) if (In(FIntPoint(X, Y))) Road[Idx(FIntPoint(X, Y))] = 1;
		for (int32 X = TownSquare.Min.X; X < TownSquare.Max.X; ++X) for (int32 Y = TownSquare.Min.Y; Y < TownSquare.Max.Y; ++Y) Road[Idx(FIntPoint(X, Y))] = 1;
		for (int32 K = 0; K < 1800; ++K)
		{
			const FIntPoint T(R.RandRange(0, N - 1), R.RandRange(0, N - 1));
			const bool bInside = In(T) && Type[Idx(T)] == 2;
			const bool bOutside = In(T) && Type[Idx(T)] == 0 && (T.X < 3 || T.Y < 3 || T.X > N - 4 || T.Y > N - 4);
			if (!bInside && !bOutside) continue;
			if (bInside)
			{
				bool bOk = !Road[Idx(T)] && !Blocked[Idx(T)];
				for (int32 Dx = -1; Dx <= 1 && bOk; ++Dx) for (int32 Dy = -1; Dy <= 1 && bOk; ++Dy)
				{
					const FIntPoint Q = T + FIntPoint(Dx, Dy);
					if (!In(Q) || Type[Idx(Q)] != 2 || Road[Idx(Q)]) bOk = false;
				}
				if (!bOk) continue;
			}
			// (no tree in a doorway's way: two tiles before every door clear)
			bool bDoorNear = false;
			for (const FTownBld& B : TownBlds) if (FMath::Abs(B.DoorTile.X - T.X) + FMath::Abs(B.DoorTile.Y - T.Y) <= 3) { bDoorNear = true; break; }
			if (bDoorNear) continue;
			const FVector P = TileWorld(T) + FVector(R.FRandRange(-90, 90), R.FRandRange(-90, 90), 0);
			const float U = R.FRand();
			const FName Nm = U < (bOutside ? 0.5f : 0.22f) ? FName(*FString::Printf(TEXT("Town.Tree%d"), 1 + R.RandRange(0, 2))) : U < 0.6f ? FName(TEXT("Town.Bush")) : FName(TEXT("Town.Grass"));
			AddPieceAt(Nm, P, R.FRandRange(0, 360), R.FRandRange(0.85f, 1.2f), !Nm.ToString().Contains(TEXT("Tree")));
			// (the papyrus map draws the trees and bushes where they stand)
			const FString Ns = Nm.ToString();
			if (Ns.StartsWith(TEXT("Town.Tree"))) TownGreens.Add(FVector(P.X, P.Y, (float)FCString::Atoi(*Ns.RightChop(9))));
			else if (Ns == TEXT("Town.Bush")) TownGreens.Add(FVector(P.X, P.Y, 4.f));
			if (bInside && Nm.ToString().Contains(TEXT("Tree"))) Blocked[Idx(T)] = 1;
		}
		break;
	}
	case 5:
		// ---- the ground itself
		TownGround();
		break;
	default: break;
	}
	(void)R0;
}

void ARDSection::TownGround()
{
	if (!bBuildStatic) return;
	// one procedural mesh over the whole section: grass, cobbles on the roads and the square, trodden earth on the lane and
	// round the doors, lush grass outside the wall (the village's ground material: R trodden, G cobbles, B soil, A lush)
	UMaterialInterface* Mat = Generator->TownGroundMaterial;
	const float M = Generator->TileSize;
	const int32 Sub = 1;                          // vertices a tile
	const int32 Nv = N * Sub + 1;
	TArray<FVector> V; TArray<int32> Tri; TArray<FVector> Nrm; TArray<FVector2D> UV; TArray<FLinearColor> Col; TArray<FProcMeshTangent> Tan;
	V.Reserve(Nv * Nv); Col.Reserve(Nv * Nv);
	TArray<FLinearColor> TileCol; TileCol.Init(FLinearColor(0, 0, 0, 0), N * N);
	for (int32 X = 0; X < N; ++X)
		for (int32 Y = 0; Y < N; ++Y)
		{
			const FIntPoint T(X, Y);
			FLinearColor& C = TileCol[Idx(T)];
			if (Type[Idx(T)] == 0) C.A = 1.f;
		}
	for (const FIntRect& Rr : TownRoads)
		for (int32 X = Rr.Min.X; X < Rr.Max.X; ++X) for (int32 Y = Rr.Min.Y; Y < Rr.Max.Y; ++Y)
			if (In(FIntPoint(X, Y)))
			{
				// (the lane by the wall is trodden earth, the streets cobbles)
				const bool bLane = X < 7 || Y < 7 || X > N - 8 || Y > N - 8;
				FLinearColor& C = TileCol[Idx(FIntPoint(X, Y))];
				if (bLane) C.R = 1.f; else C.G = 1.f;
			}
	for (int32 X = TownSquare.Min.X; X < TownSquare.Max.X; ++X) for (int32 Y = TownSquare.Min.Y; Y < TownSquare.Max.Y; ++Y) TileCol[Idx(FIntPoint(X, Y))].G = 1.f;
	for (const FTownBld& B : TownBlds)
		for (int32 K = 1; K <= 2; ++K)
		{
			const FIntPoint T = B.DoorTile + RDTDir4[B.DoorSide] * K;
			if (In(T)) TileCol[Idx(T)].R = FMath::Max(TileCol[Idx(T)].R, 0.8f);
		}
	// (the road on outside the gate, a few tiles into the wilds)
	{
		const FIntPoint G = WorldToLocal(TownGate + TownGateOut * 10.f);
		for (int32 K = 0; K < 8; ++K)
			for (int32 W = -1; W <= 1; ++W)
			{
				const FIntPoint T = G + FIntPoint(FMath::RoundToInt(TownGateOut.X), FMath::RoundToInt(TownGateOut.Y)) * K + FIntPoint(FMath::RoundToInt(TownGateOut.Y), FMath::RoundToInt(TownGateOut.X)) * W;
				if (In(T)) { TileCol[Idx(T)].R = 1.f; TileCol[Idx(T)].A = 0.f; }
			}
	}
	// (under a building's floor the ground sinks out of sight: a floor piece whose top is a little lower than its bounds (the
	// stone foundation's) showed the grass through it; at its walls it stays level)
	auto UnderFloor = [&](int32 I, int32 J)
	{
		for (int32 Dx = -1; Dx <= 0; ++Dx) for (int32 Dy = -1; Dy <= 0; ++Dy)
		{
			const FIntPoint T(I / Sub + Dx, J / Sub + Dy);
			if (!In(T) || Type[Idx(T)] != 1) return false;
		}
		return true;
	};
	for (int32 I = 0; I < Nv; ++I)
		for (int32 J = 0; J < Nv; ++J)
		{
			V.Add(FVector(I * M / Sub, J * M / Sub, UnderFloor(I, J) ? -40.f : 0.f));
			UV.Add(FVector2D(I * M / Sub / 400.f, J * M / Sub / 400.f));
			Nrm.Add(FVector::UpVector);
			// (a vertex's colour: the mean of the tiles round it, so the borders blend)
			FLinearColor C(0, 0, 0, 0); int32 Cnt = 0;
			for (int32 Dx = -1; Dx <= 0; ++Dx) for (int32 Dy = -1; Dy <= 0; ++Dy)
			{
				const FIntPoint T(I / Sub + Dx, J / Sub + Dy);
				if (!In(T)) continue;
				C += TileCol[Idx(T)]; ++Cnt;
			}
			Col.Add(Cnt ? C / (float)Cnt : FLinearColor(0, 0, 0, 1));
		}
	for (int32 I = 0; I < Nv - 1; ++I)
		for (int32 J = 0; J < Nv - 1; ++J)
		{
			const int32 A = I * Nv + J, B = (I + 1) * Nv + J, C = (I + 1) * Nv + J + 1, D = I * Nv + J + 1;
			// (front where cross(V1 - V0, V2 - V0) points away from the viewer: seen from above it points down)
			Tri.Append({ A, C, B, A, D, C });
		}
	UProceduralMeshComponent* G = NewObject<UProceduralMeshComponent>(this, TEXT("TownGround"), RF_Transactional);
	G->SetupAttachment(RootComponent);
	G->SetMobility(EComponentMobility::Static);
	G->bUseComplexAsSimpleCollision = true;
	G->RegisterComponent();
	AddInstanceComponent(G);
	G->CreateMeshSection_LinearColor(0, V, Tri, Nrm, UV, Col, Tan, false);
	if (Mat) G->SetMaterial(0, Mat);
	// (the ground is seen only: everyone walks on a flat invisible floor at its level, as in the village; under the buildings
	// the drawn ground is sunk, and their own floors stand on this one)
	G->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	UBoxComponent* Fl = NewObject<UBoxComponent>(this, TEXT("TownFloor"), RF_Transactional);
	Fl->SetupAttachment(RootComponent);
	Fl->SetMobility(EComponentMobility::Static);
	Fl->SetBoxExtent(FVector(N * M * 0.5f, N * M * 0.5f, 20.f));
	Fl->SetRelativeLocation(FVector(N * M * 0.5f, N * M * 0.5f, -20.f));
	Fl->SetCollisionProfileName(TEXT("BlockAll"));
	Fl->SetHiddenInGame(true);
	Fl->RegisterComponent();
	AddInstanceComponent(Fl);
}

// ------------------------------------------------------------------------------------------------ the castle's outside
// (the user's of 2026-11-02: "the castle's outer walls look strange being covered with arches; have them look a little more
// like medieval castle walls, with windows, arrowslits, towers, a way into the battlements". The inside keeps the dungeon's
// Castle theme; outside: Castle Forge's stone in two storeys to the wall walk (arrow slits below, windows above), the roof a
// walked wall walk behind crenellated battlements, a round tower at each corner (Castle Forge's tower quarters, a cone roof)
// and in the front one on the castle's +Y side a stair turret: a spiral stair from a door at its foot to a door onto the walk.)
namespace
{
	/** the castle's towers: their middles stand this far out from the castle's corners (each way), the ring's radius, the
	 *  angles (the castle's own frame: +X its front) of the stair turret's two doors, the spiral's quarters and its start */
	constexpr float RDTCTowerOut = 200.f, RDTCTowerR = 314.f, RDTCTowerMid = 284.f;
	constexpr float RDTCStairDoor = 315.f, RDTCWalkDoor = 225.f, RDTCSpiralStart = 305.f;
	constexpr int32 RDTCSpiralQuarters = 9;
	float RDTCAngleDiff(float A, float B) { return FMath::Abs(FMath::FindDeltaAngleDegrees(A, B)); }
}

float ARDSection::CastleWalkTop() const
{
	// (the roof's pieces lie 40 cm over the rooms' height: their top is the walk)
	const FRDPiece* Rf = Generator ? Generator->Piece(TEXT("Town.CastleRoof")) : nullptr;
	return (Generator ? Generator->RoomHeight : 600.f) + 40.f + (Rf ? (float)Rf->Size.Z : 21.f);
}

void ARDSection::CastleTowersPlan()
{
	CastleTowers.Reset(); CastleStairTower = -1;
	if (!TownBlds.IsValidIndex(CastleBld)) return;
	const FTownBld& B = TownBlds[CastleBld];
	const float M = Generator->TileSize;
	const int32 Nx = B.DoorSide < 2 ? B.Max.X - B.Min.X : B.Max.Y - B.Min.Y;
	const int32 Ny = B.DoorSide < 2 ? B.Max.Y - B.Min.Y : B.Max.X - B.Min.X;
	const float Hx = Nx * M * 0.5f, Hy = Ny * M * 0.5f, D = RDTCTowerOut;
	// (the first is the front corner on the castle's +Y side: the stair turret)
	for (const FIntPoint& Sg : { FIntPoint(1, 1), FIntPoint(1, -1), FIntPoint(-1, -1), FIntPoint(-1, 1) })
		CastleTowers.Add(TownBldPoint(B, Sg.X * (Hx + D), Sg.Y * (Hy + D), 0.f));
	CastleStairTower = 0;
	const float Yaw0 = TownBldYaw(B);
	auto Dir = [&](float A) { return FRotator(0, Yaw0 + A, 0).RotateVector(FVector(1, 0, 0)); };
	CastleStairDoor = CastleTowers[0] + Dir(RDTCStairDoor) * (RDTCTowerR + 30.f);
	CastleWalkZ = GetActorLocation().Z + CastleWalkTop();
	CastleWalkDoor = CastleTowers[0] + Dir(RDTCWalkDoor) * (RDTCTowerR - 30.f) + FVector(0, 0, CastleWalkTop());
	// the ground under the towers is void (nobody walks into them, nothing grows there); the stair door's tile stays ground
	const FIntPoint DoorT = WorldToLocal(CastleStairDoor + Dir(RDTCStairDoor) * 60.f);
	for (const FVector& C : CastleTowers)
	{
		const FIntPoint Ct = WorldToLocal(C);
		for (int32 X = Ct.X - 3; X <= Ct.X + 3; ++X)
			for (int32 Y = Ct.Y - 3; Y <= Ct.Y + 3; ++Y)
			{
				const FIntPoint T(X, Y);
				if (!In(T) || T == DoorT || Type[Idx(T)] != 2) continue;
				if (FVector::Dist2D(TileWorld(T), C) < RDTCTowerR + 70.f) { Type[Idx(T)] = 0; Owner[Idx(T)] = -1; }
			}
	}
	// a cobbled path from the stair door to the forecourt (across the castle's front, then toward its door)
	auto OnRoad = [&](const FIntPoint& T)
	{
		if (TownSquare.Contains(T)) return true;
		for (const FIntRect& Rr : TownRoads) if (Rr.Contains(T)) return true;
		return false;
	};
	const FIntPoint Tg = B.DoorTile + RDTDir4[B.DoorSide];
	FIntPoint T = DoorT;
	for (int32 K = 0; K < 24 && In(T) && !OnRoad(T); ++K)
	{
		TownRoads.Add(FIntRect(T, T + FIntPoint(1, 1)));
		const FIntPoint Dd = Tg - T;
		const bool bAcrossY = B.DoorSide < 2;
		const int32 Across = bAcrossY ? Dd.Y : Dd.X, Along = bAcrossY ? Dd.X : Dd.Y;
		if (Across != 0) T += bAcrossY ? FIntPoint(0, FMath::Sign(Across)) : FIntPoint(FMath::Sign(Across), 0);
		else if (Along != 0) T += bAcrossY ? FIntPoint(FMath::Sign(Along), 0) : FIntPoint(0, FMath::Sign(Along));
		else break;
	}
}

void ARDSection::CastleOuterFace(const FVector& Edge, const FVector& OutW, float Yaw, float T, float Z0, float Z1, const FIntPoint& Tl, int32 Side, bool bOverDoor)
{
	const FRDPiece* Cw = Generator->Piece(TEXT("Town.CWall"));
	const float M = Generator->TileSize, H = Generator->RoomHeight;
	if (!Cw)
	{
		// (no Castle Forge pieces: the theme's own wall, as before)
		for (float Z = Z0; Z < Z1 - 5.f; Z += 300.f) AddPieceAt(TEXT("Castle.Wall_Block"), Edge + OutW * T + FVector(0, 0, Z), Yaw + 180.f);
		return;
	}
	const float Th = FMath::Max((float)Cw->Size.X, 40.f), Len = FMath::Max((float)Cw->Size.Y, 100.f), Ht = FMath::Max((float)Cw->Size.Z, 100.f);
	const FVector P = Edge + OutW * (T * 0.5f + Th * 0.5f);
	const FRotator Ro(0, Yaw + 180.f, 0);
	const uint32 Hh = HashCombine(GetTypeHash(Tl), (uint32)Side * 2654435761u);
	auto Has = [&](const TCHAR* N) { return Generator->Piece(N) != nullptr; };
	// (pieces a little longer and taller than their slots: set edge to edge, the rooms' torchlight showed through the seams)
	const float Ls = (M + 14.f) / Len;
	if (bOverDoor) AddPiece(TEXT("Town.CWall"), FTransform(Ro, P + FVector(0, 0, Z0), FVector(1.f, Ls, (Z1 - Z0 + 4.f) / Ht)));
	else
	{
		const float Hs = (Z1 - Z0) * 0.5f;
		// (the ground storey: plain stone, an arrow slit in one segment of three)
		const FName G = (Hh % 3u == 0u && Has(TEXT("Town.CWallSlit"))) ? FName(TEXT("Town.CWallSlit")) : FName(TEXT("Town.CWall"));
		// (the upper storey: small windows most, now and then a tall one, a slit, plain stone)
		const uint32 U = (Hh >> 8) % 10u;
		FName Up = U < 3u ? FName(TEXT("Town.CWall")) : U < 5u ? FName(TEXT("Town.CWallWin1")) : U < 7u ? FName(TEXT("Town.CWallWin2")) : U < 8u ? FName(TEXT("Town.CWallWinL")) : FName(TEXT("Town.CWallSlit"));
		if (!Generator->Piece(Up)) Up = TEXT("Town.CWall");
		AddPiece(G, FTransform(Ro, P + FVector(0, 0, Z0), FVector(1.f, Ls, (Hs + 14.f) / Ht)));
		AddPiece(Up, FTransform(Ro, P + FVector(0, 0, Z0 + Hs), FVector(1.f, Ls, (Hs + 4.f) / Ht)));
	}
	// the walk's outer strip over the walls' tops, flush with the roof's top
	const FRDPiece* Rf = Generator->Piece(TEXT("Town.CastleRoof"));
	const float Sw = T * 0.5f + 15.f;
	if (Rf) AddPiece(TEXT("Town.CastleRoof"), FTransform(FRotator(0, Yaw, 0), Edge + OutW * (Sw * 0.5f) + FVector(0, 0, H + 40.f), FVector(Sw / FMath::Max((float)Rf->Size.X, 50.f), 1.f, 1.f)));
	// the battlements on the outer face, up to where a tower's ring crosses them: a segment the ring crosses is shortened to
	// its part outside the ring and 20 cm in (the PR review's find: a test of the segment's middle never caught one, and every
	// corner's ran 40 cm into its tower)
	const FRDPiece* Pp = Generator->Piece(TEXT("Town.Parapet"));
	const float Pt = Pp ? FMath::Max((float)Pp->Size.X, 40.f) : 110.f, Pl = Pp ? FMath::Max((float)Pp->Size.Y, 100.f) : 313.f;
	const FVector Pc = Edge + OutW * (T * 0.5f + Th - Pt * 0.5f);
	const FVector Along(-OutW.Y, OutW.X, 0.f);
	float T0 = -M * 0.5f, T1 = M * 0.5f;
	for (const FVector& C : CastleTowers)
	{
		// (where the segment's line Pc + Along t enters and leaves the ring's circle)
		const FVector2D D(Pc.X - C.X, Pc.Y - C.Y), Al(Along.X, Along.Y);
		const float B_ = FVector2D::DotProduct(D, Al), Cq = D.SizeSquared() - RDTCTowerR * RDTCTowerR, Disc = B_ * B_ - Cq;
		if (Disc <= 0.f) continue;
		const float Ta = -B_ - FMath::Sqrt(Disc), Tb = -B_ + FMath::Sqrt(Disc);
		if (Tb <= T0 || Ta >= T1) continue;
		// (keep the longer part outside, reaching 20 cm into the ring)
		if (Ta - T0 >= T1 - Tb) T1 = FMath::Min(T1, Ta + 20.f); else T0 = FMath::Max(T0, Tb - 20.f);
	}
	if (T1 - T0 < 30.f) return;
	AddPiece(TEXT("Town.Parapet"), FTransform(Ro, Pc + Along * ((T0 + T1) * 0.5f) + FVector(0, 0, Z1), FVector(1.f, (T1 - T0) / Pl, 1.f)), true);
}

void ARDSection::CastleTowersBuild(const FTownBld& B)
{
	const FRDPiece* Rp = Generator->Piece(TEXT("Town.TowerRingA"));
	if (!Rp || CastleTowers.Num() == 0) return;
	const float Yaw0 = TownBldYaw(B);
	// (each storey overlaps the one under it by 14 cm: set edge to edge, the torches inside lit the seams)
	const float Top = CastleWalkTop(), Hs = FMath::Max((float)Rp->Size.Z - 14.f, 100.f), TowerTop = Top + 2.f * Hs;
	auto Dir = [&](float A) { return FRotator(0, Yaw0 + A, 0).RotateVector(FVector(1, 0, 0)); };
	const FRDPiece* Rf = Generator->Piece(TEXT("Town.CastleRoof"));
	const float RfZ = Rf ? (float)Rf->Size.Z : 21.f, RfX = Rf ? FMath::Max((float)Rf->Size.X, 50.f) : 304.f;
	const FRDPiece* Sp = Generator->Piece(TEXT("Town.Spiral"));
	const float SpZ = Sp ? FMath::Max((float)Sp->Size.Z, 50.f) : 100.f;
	for (int32 I = 0; I < CastleTowers.Num(); ++I)
	{
		const FVector C = CastleTowers[I];
		const bool bStair = I == CastleStairTower && Sp;
		const FVector Lc = FRotator(0, -Yaw0, 0).RotateVector(C - TownBldPoint(B, 0.f, 0.f, 0.f));
		const float Out = FMath::RadiansToDegrees(FMath::Atan2(Lc.Y, Lc.X));      // (the way out from the castle's middle)
		// the ring: four storeys of four quarters (the second stretched to the walk's height), each quarter's look by where
		// it faces: arrow slits and windows outward, plain stone toward the castle; the stair turret's two doors
		const float Zs[4] = { 0.f, Hs, Top, Top + Hs };
		const float Rz = FMath::Max((float)Rp->Size.Z, 100.f);
		const float Sz[4] = { 1.f, (Top - Hs + 14.f) / Rz, 1.f, 1.f };
		for (int32 St = 0; St < 4; ++St)
			for (int32 K = 0; K < 4; ++K)
			{
				const float Q = 90.f * K, Mid = Q + 45.f, Rel = RDTCAngleDiff(Mid, Out);
				TCHAR V = TEXT('E');
				switch (St)
				{
				case 0: V = Rel < 10.f ? TEXT('A') : TEXT('E'); break;
				case 1: V = Rel < 10.f ? TEXT('B') : Rel < 100.f ? TEXT('A') : TEXT('E'); break;
				case 2: V = Rel < 10.f ? TEXT('A') : Rel < 100.f ? TEXT('B') : TEXT('E'); break;
				default: V = Rel < 10.f ? TEXT('C') : Rel < 100.f ? TEXT('A') : TEXT('B'); break;
				}
				if (bStair && St == 0 && RDTCAngleDiff(Mid, RDTCStairDoor) < 10.f) V = TEXT('D');
				if (bStair && St == 2 && RDTCAngleDiff(Mid, RDTCWalkDoor) < 10.f) V = TEXT('D');
				const FName Nm(*FString::Printf(TEXT("Town.TowerRing%c"), V));
				AddPiece(Generator->Piece(Nm) ? Nm : FName(TEXT("Town.TowerRingA")), FTransform(FRotator(0, Yaw0 + Q, 0), C + FVector(0, 0, Zs[St]), FVector(1.f, 1.f, Sz[St])), true);
			}
		for (int32 K = 0; K < 4; ++K) AddPieceAt(TEXT("Town.TowerCone"), C + FVector(0, 0, TowerTop), Yaw0 + 90.f * K, 1.f, true);
		// (its collision: the pack's quarters close their doorways' feet; 32 hidden boxes round the ring instead, the doors open)
		for (int32 J = 0; J < 32; ++J)
		{
			const float A = 5.625f + 11.25f * J;
			const FTransform Bx(FRotator(0, Yaw0 + A, 0), C + Dir(A) * RDTCTowerMid, FVector(0.6f, 0.62f, 1.f));
			auto Box = [&](float Za, float Zb)
			{
				if (Zb - Za < 5.f) return;
				FTransform T = Bx; T.AddToTranslation(FVector(0, 0, Za)); T.SetScale3D(FVector(0.6f, 0.62f, (Zb - Za) / 100.f));
				AddPiece(TEXT("Town.Collider"), T);
			};
			if (bStair && RDTCAngleDiff(A, RDTCStairDoor) < 11.25f) Box(240.f, TowerTop);
			else if (bStair && RDTCAngleDiff(A, RDTCWalkDoor) < 11.25f) { Box(0.f, Top); Box(Top + 240.f, TowerTop); }
			else Box(0.f, TowerTop);
		}
		if (!bStair)
		{
			// (a floor at the walk's level: the corner between the castle's walls opens into the tower)
			if (Rf) AddPiece(TEXT("Town.CastleRoof"), FTransform(FRotator(0, Yaw0, 0), C + FVector(0, 0, Top - RfZ), FVector(370.f / RfX, 370.f / RfX, 1.f)));
			continue;
		}
		// the spiral: quarter turns climbing clockwise (each piece from its own yaw down 90 degrees), from beside the foot's door
		// to the walk's door; a landing over the gap between the last step and the door; a torch
		const float Qh = Top / RDTCSpiralQuarters;
		for (int32 K = 0; K < RDTCSpiralQuarters; ++K)
			AddPiece(TEXT("Town.Spiral"), FTransform(FRotator(0, Yaw0 + RDTCSpiralStart - 90.f * K, 0), C + FVector(0, 0, Qh * K), FVector(1.f, 1.f, Qh / SpZ)));
		if (Rf) AddPiece(TEXT("Town.CastleRoof"), FTransform(FRotator(0, Yaw0 + RDTCWalkDoor, 0), C + Dir(RDTCWalkDoor) * 250.f + FVector(0, 0, Top - RfZ), FVector(130.f / RfX, 130.f / RfX, 1.f)));
		AddTorch(C + Dir(45.f) * 250.f + FVector(0, 0, 330.f), Yaw0 + 45.f + 180.f, 120.f);
		AddTorch(C + Dir(135.f) * 250.f + FVector(0, 0, Top + 150.f), Yaw0 + 135.f + 180.f, 90.f);
	}
}

TArray<FString> ARDSection::GetCastleShapeLines() const
{
	TArray<FString> Out;
	for (int32 I = 0; I < CastleTowers.Num(); ++I) Out.Add(FString::Printf(TEXT("tower|%.0f|%.0f|%d"), CastleTowers[I].X, CastleTowers[I].Y, I == CastleStairTower ? 1 : 0));
	if (CastleStairTower >= 0)
	{
		Out.Add(FString::Printf(TEXT("stairdoor|%.0f|%.0f|%.0f"), CastleStairDoor.X, CastleStairDoor.Y, GetActorLocation().Z));
		// (world heights: the towers' middles are TileWorld's (the section's z), the walk door's its own plus the walk's top)
		Out.Add(FString::Printf(TEXT("walkdoor|%.0f|%.0f|%.0f"), CastleWalkDoor.X, CastleWalkDoor.Y, CastleWalkDoor.Z));
		Out.Add(FString::Printf(TEXT("stairmid|%.0f|%.0f|%.0f"), CastleTowers[CastleStairTower].X, CastleTowers[CastleStairTower].Y, CastleTowers[CastleStairTower].Z));
		Out.Add(FString::Printf(TEXT("spiral|%.0f|%d"), (float)RDTCSpiralStart, RDTCSpiralQuarters));
	}
	Out.Add(FString::Printf(TEXT("walk|%.0f"), CastleWalkZ));
	return Out;
}