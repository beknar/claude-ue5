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
#include "Components/TextRenderComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Materials/MaterialInterface.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDTown, Log, All);

// the town's building kinds and the things that stand outside (RDTown.h names them for the generator and the HUD)
#include "RD/RDTown.h"

static const FIntPoint RDTDir4[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };

/** what a trade's sign says (two lines at most) */
static FString RDTSignText(uint8 Kind)
{
	switch (Kind)
	{
	case TK_Smithy: return TEXT("SMITHY");
	case TK_Store: return TEXT("GENERAL\nGOODS");
	case TK_Healer: return TEXT("HEALER");
	case TK_Temple: return TEXT("TEMPLE");
	case TK_Storehouse: return TEXT("STORE\nHOUSE");
	case TK_Tavern: return TEXT("TAVERN");
	case TK_Chapel: return TEXT("CHAPEL");
	case TK_Barracks: return TEXT("BARRACKS");
	case TK_Witch: return TEXT("HEDGE\nWITCH");
	case TK_Monastery: return TEXT("MONASTERY");
	case TK_Workshop: return TEXT("WORKSHOP");
	case TK_Warehouse: return TEXT("WARE\nHOUSE");
	case TK_SluiceHouse: return TEXT("SLUICE\nHOUSE");
	default: return FString();
	}
}

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
		/** a point of the frame (continuous: tile (U, V) covers [U, U + 1) x [V, V + 1)) in the section's local tile units (tile
		 *  (X, Y) covers [X, X + 1) x [Y, Y + 1)) */
		FVector2D LocalF(float U, float V) const
		{
			switch (G)
			{
			case 1: return FVector2D(O + S - U, O + S - V);
			case 2: return FVector2D(O + S - V, O + U);
			case 3: return FVector2D(O + V, O + S - U);
			default: return FVector2D(O + U, O + V);
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
	// (Vel Morrath's holy city (the user's of 2026-11-06, the generator's TownPlan 1): the cathedral at the town's middle with
	// its plaza before it, over the catacombs; every rule of it behind bHoly, so Brokenspire's plan and draws stay as they were)
	const bool bHoly = Generator->TownPlan == 1;
	// (Ashenreach's forge city (the user's of 2026-11-07, docs/ashenreach.txt; TownPlan 2, RDForge.cpp): the besieged foundry at
	// the town's middle where the cathedral stands in the holy city, its square before it, the guild's workshops; bMid the rules
	// the two share: a landmark at the town's middle over a dungeon of its own)
	const bool bForge = Generator->TownPlan == 2;
	// (Graymourne's port (the user's of 2026-11-07, docs/graymourne.txt; TownPlan 3, RDPort.cpp): the sluice house over the sewers
	// at the town's middle, an inner harbour along its sea wall (the frame's far side, turned to the north: the coast), its quay,
	// piers, moored ships, warehouses, the drowned dead)
	const bool bPort = Generator->TownPlan == 3;
	const bool bMid = bHoly || bForge || bPort;
	if (bPort) F.G = 0;
	// ---- the ground inside the wall: one hallway (its rectangle the town's bounds; only the tiles inside the wall's outline
	// are ground, below)
	FCorr Ground; Ground.Min = FIntPoint(F.O, F.O); Ground.Max = FIntPoint(F.O + S, F.O + S); Ground.bHoriz = true; Ground.Theme = 0;
	Corrs.Add(Ground);
	TownInner = FIntRect(Ground.Min, Ground.Max);
	TownBorder.Reset(); TownPaths.Reset(); TownRoadMask.Init(0, N * N); TownTowerDoors.Reset(); TownTowerMids.Reset();
	TownWorks.Reset(); TownPens.Reset(); TownGardens.Reset(); TownSpits.Reset(); TownGrassClumps = 0; TownSmallBushes = 0;
	TownOvens.Reset(); TownFoods.Reset(); TownPortcullis = -1; TownLevers.Reset(); TownPenGates.Reset(); TownLiftW.Reset(); bTownLiftOn = false;
	CastleStairwell.Reset(); CastleStairRoom = -1; CastleStairFoot = CastleStairTop = FVector::ZeroVector;
	// (a frame grid of what each tile is taken by: 0 free, 1 road, 2 square, 3 building or its margin, 4 kept clear, 9 outside)
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
	// (the holy city's cathedral: 27 tiles deep (81 m: the narthex, the nave, the choir), 19 wide (the nave and its aisles))
	// (the foundry: 25 deep (75 m: its gatehouse, the casting hall, the furnace hall), 21 wide (the halls and a workshop wing
	// down each side))
	// (the port's sluice house: a stone hall of 9 x 9 tiles over the sewers' mouth)
	const int32 CD = bHoly ? 27 : bForge ? 25 : bPort ? 9 : 17, CW = bHoly ? 19 : bPort ? 9 : 21;
	// (the port's harbour in the frame: from 26 tiles before the far wall to it, 24 tiles in from each side; its quay the 4 rows
	// before it)
	const int32 Hu0 = S - 26, Hv0 = 24, Hv1 = S - 24;
	// (a tile of ground and the lane behind the castle: its round corner towers stand 5 m out from its corners; the cathedral (or
	// the foundry) a little past the town's middle, the plaza before it)
	const int32 Cu0 = bMid ? S / 2 - CD / 2 + 4 : S - 3 - CD, Cv0 = Vc - CW / 2;
	const int32 Us = bMid ? Cu0 - 19 : 50 + R.RandRange(-4, 4);           // (the square's near edge)
	// (the castle's (or the cathedral's) ground with a margin: the castle reaches the far wall, the cathedral has ground behind)
	auto InCastleZone = [&](float U, float V, float Mg) { return U >= Cu0 - Mg && (!bMid || U <= Cu0 + CD + Mg) && V >= Cv0 - Mg && V <= Cv0 + CW + Mg; };
	const int32 SqU0 = Us, SqU1 = Us + 14, SqV0 = Vc - 7, SqV1 = Vc + 8;
	// ---- the wall's outline (the user's of 2026-11-02: "the town borders should also be irregularly shaped with the town walls
	// following the shape of the town"): about twenty corners round the town's middle at radii from the plan's stream; a
	// straight stretch for the gate across the main road; behind the castle out to the square's edge. In the frame's units.
	TArray<FVector2D> Pg;
	int32 GateU = 0;
	{
		const FVector2D Cc(S * 0.5f, S * 0.5f);
		const float Rb = S * 0.5f - 1.f, Ph1 = R.FRandRange(0.f, 2.f * PI), Ph2 = R.FRandRange(0.f, 2.f * PI);
		auto RMax = [&](const FVector2D& D)
		{
			// (out to the square [0.5, S - 0.5] along D)
			float T = 1e9f;
			if (D.X > 1e-4f) T = FMath::Min(T, (S - 0.5f - Cc.X) / D.X); if (D.X < -1e-4f) T = FMath::Min(T, (0.5f - Cc.X) / D.X);
			if (D.Y > 1e-4f) T = FMath::Min(T, (S - 0.5f - Cc.Y) / D.Y); if (D.Y < -1e-4f) T = FMath::Min(T, (0.5f - Cc.Y) / D.Y);
			return T;
		};
		// (the castle's ground with its towers and the lane behind it: the angles its corners make from the middle)
		float CaMin = 1e9f, CaMax = -1e9f;
		for (const FVector2D& Q : { FVector2D(Cu0 - 4.f, Cv0 - 4.f), FVector2D(Cu0 - 4.f, Cv0 + CW + 4.f), FVector2D((float)S, Cv0 - 4.f), FVector2D((float)S, Cv0 + CW + 4.f) })
		{
			const float A = FMath::Atan2(Q.Y - Cc.Y, Q.X - Cc.X); CaMin = FMath::Min(CaMin, A); CaMax = FMath::Max(CaMax, A);
		}
		const int32 KV = 20;
		const float Step = 2.f * PI / KV;
		TArray<TPair<float, FVector2D>> Vs;
		for (int32 I = 0; I < KV; ++I)
		{
			const float Th = -PI + Step * (I + 0.5f) + R.FRandRange(-0.07f, 0.07f);
			if (FMath::Abs(FMath::FindDeltaAngleRadians(Th, PI)) < 0.32f) continue;      // (the gate's stretch)
			const FVector2D D(FMath::Cos(Th), FMath::Sin(Th));
			float Rr = Rb * (0.84f + 0.08f * FMath::Sin(2.f * Th + Ph1) + 0.06f * FMath::Sin(3.f * Th + Ph2) + R.FRandRange(-0.035f, 0.035f));
			if (!bMid && Th > CaMin - Step && Th < CaMax + Step) Rr = 1e9f;                             // (behind the castle: the square's edge)
			if (bPort && FMath::Abs(Th) < 1.15f) Rr = 1e9f;                                             // (the port's sea wall: straight, at the far edge)
			Vs.Add({ Th, Cc + D * FMath::Min(Rr, RMax(D)) });
		}
		// (the gate's stretch: across the main road, 4 tiles each side of it (its two towers), as far out as the corners beside it)
		const float Rg = Rb * (0.86f + R.FRandRange(-0.04f, 0.04f));
		GateU = FMath::Clamp(FMath::RoundToInt(Cc.X - Rg), 1, 20);
		const float Vm = Vc + 0.5f;
		Vs.Add({ FMath::Atan2(Vm + 4.f - Cc.Y, GateU - Cc.X), FVector2D((float)GateU, Vm + 4.f) });
		Vs.Add({ FMath::Atan2(Vm - 4.f - Cc.Y, GateU - Cc.X), FVector2D((float)GateU, Vm - 4.f) });
		Vs.Sort([](const TPair<float, FVector2D>& A, const TPair<float, FVector2D>& B) { return A.Key < B.Key; });
		for (const auto& Vv : Vs) Pg.Add(Vv.Value);
	}
	auto InsidePg = [&](float U, float V)
	{
		bool bIn = false;
		for (int32 I = 0, J = Pg.Num() - 1; I < Pg.Num(); J = I++)
			if (((Pg[I].Y > V) != (Pg[J].Y > V)) && (U < (Pg[J].X - Pg[I].X) * (V - Pg[I].Y) / (Pg[J].Y - Pg[I].Y) + Pg[I].X)) bIn = !bIn;
		return bIn;
	};
	auto BorderDistPg = [&](float U, float V)
	{
		float Dm = 1e9f;
		for (int32 I = 0, J = Pg.Num() - 1; I < Pg.Num(); J = I++)
			Dm = FMath::Min(Dm, (float)FMath::PointDistToSegment(FVector(U, V, 0), FVector(Pg[J].X, Pg[J].Y, 0), FVector(Pg[I].X, Pg[I].Y, 0)));
		return Dm;
	};
	// (the outline in the world: the wall and the maps follow it)
	for (const FVector2D& P : Pg)
	{
		const FVector2D Lf = F.LocalF(P.X, P.Y);
		TownBorder.Add(FVector2D(GetActorLocation().X + Lf.X * Generator->TileSize, GetActorLocation().Y + Lf.Y * Generator->TileSize));
	}
	// the ground: the tiles inside the outline; outside it nothing is built; the lane: two tiles inside the wall
	for (int32 U = 0; U < S; ++U)
		for (int32 V = 0; V < S; ++V)
		{
			const FIntPoint T = F.Tile(U, V);
			if (!InsidePg(U + 0.5f, V + 0.5f)) { Use[U * S + V] = 9; continue; }
			Type[Idx(T)] = 2; Owner[Idx(T)] = 1000;
			if (BorderDistPg(U + 0.5f, V + 0.5f) < 2.f) { Use[U * S + V] = 1; TownRoadMask[Idx(T)] = 3; }
		}
	// (the port's harbour: no ground (nothing is built or walked there but on its piers); five piers 2 tiles wide out from the
	// quay, 16 tiles into the water)
	TownHarbour = FIntRect(); TownPiers.Reset();
	if (bPort)
	{
		for (int32 U = Hu0; U < S; ++U)
			for (int32 V = Hv0; V < Hv1; ++V)
			{
				const FIntPoint T = F.Tile(U, V);
				Use[U * S + V] = 9; Type[Idx(T)] = 0; Owner[Idx(T)] = -1; TownRoadMask[Idx(T)] = 0;
			}
		TownHarbour = F.Rect(Hu0, Hv0, S, Hv1);
		for (int32 K = 0; K < 5; ++K)
		{
			const int32 Pv = Hv0 + 10 + K * ((Hv1 - Hv0 - 22) / 4);
			for (int32 U = Hu0; U < Hu0 + 16; ++U)
				for (int32 V = Pv; V < Pv + 2; ++V) { const FIntPoint T = F.Tile(U, V); Use[U * S + V] = 4; Type[Idx(T)] = 2; Owner[Idx(T)] = 1000; }
			TownPiers.Add(F.Rect(Hu0, Pv, Hu0 + 16, Pv + 2));
		}
	}
	// a straight cobbled road, cut to the outline's inside less the lane (along U when bAlongU, its long side)
	auto RoadIn = [&](int32 U0, int32 V0, int32 U1, int32 V1, bool bAlongU)
	{
		const float Mid = bAlongU ? (V0 + V1) * 0.5f : (U0 + U1) * 0.5f;
		int32 A0 = bAlongU ? U0 : V0, A1 = bAlongU ? U1 : V1;
		auto Ok = [&](int32 A) { const float U = bAlongU ? A + 0.5f : Mid, V = bAlongU ? Mid : A + 0.5f; return InsidePg(U, V) && BorderDistPg(U, V) >= 2.f; };
		while (A0 < A1 && !Ok(A0)) ++A0;
		while (A1 > A0 && !Ok(A1 - 1)) --A1;
		if (A1 - A0 < 3) return;
		if (bAlongU) Road(A0, V0, A1, V1); else Road(U0, A0, U1, A1);
	};
	// a winding earth road along frame points (U, V): its tiles road for the plots' doors and earth for the ground and the
	// trees; cut where it leaves the outline less the lane, or crosses the castle's ground
	auto PaintPath = [&](const TArray<FVector2D>& Fp, float HalfTiles)
	{
		FTownPath Path; Path.HalfWidth = Generator->TileSize * (HalfTiles - 0.05f);
		const float Reach = HalfTiles + 0.1f;
		const int32 Ri = FMath::CeilToInt(Reach) + 1;
		for (const FVector2D& Q : Fp)
		{
			const float U = Q.X, V = Q.Y;
			const bool bCastle = InCastleZone(U, V, 3.f);
			if (!InsidePg(U, V) || BorderDistPg(U, V) < 1.5f || bCastle) { if (Path.Pts.Num() >= 6) TownPaths.Add(Path); Path.Pts.Reset(); continue; }
			const FVector2D Lf = F.LocalF(U, V);
			Path.Pts.Add(FVector2D(GetActorLocation().X + Lf.X * Generator->TileSize, GetActorLocation().Y + Lf.Y * Generator->TileSize));
			for (int32 Du = -Ri; Du <= Ri; ++Du)
				for (int32 Dv = -Ri; Dv <= Ri; ++Dv)
				{
					const int32 Tu = FMath::FloorToInt(U) + Du, Tv = FMath::FloorToInt(V) + Dv;
					if (Tu < 0 || Tv < 0 || Tu >= S || Tv >= S || FVector2D::Distance(FVector2D(Tu + 0.5f, Tv + 0.5f), FVector2D(U, V)) > Reach) continue;
					if (Use[Tu * S + Tv] == 0) Use[Tu * S + Tv] = 1;
					const FIntPoint T = F.Tile(Tu, Tv);
					if (TownRoadMask[Idx(T)] == 0) TownRoadMask[Idx(T)] = 2;
				}
		}
		if (Path.Pts.Num() >= 6) TownPaths.Add(Path);
	};
	// a wandering way from A to B (the user's of 2026-11-02, the third list: "they still form a regular grid. they should
	// meander around the town in a semi-random manner"): it sets off up to 35 degrees from the straight way, its heading drifts
	// with two slow waves of its own, turning at most 7 degrees a half tile, and straightens as it comes near; it bends away
	// from the castle's ground and the wall's lane
	auto Wander = [&](const FVector2D& A, const FVector2D& B)
	{
		TArray<FVector2D> Out;
		FVector2D P = A;
		float Hd = FMath::Atan2(B.Y - A.Y, B.X - A.X) + R.FRandRange(-0.6f, 0.6f);
		const float Ph1 = R.FRandRange(0.f, 2.f * PI), Ph2 = R.FRandRange(0.f, 2.f * PI), Am = R.FRandRange(0.55f, 0.95f);
		const float W1 = R.FRandRange(7.f, 12.f), W2 = R.FRandRange(3.5f, 5.5f);
		float Sd = 0.f;
		Out.Add(P);
		for (int32 I = 0; I < 900; ++I)
		{
			const FVector2D To = B - P; const float D = To.Size();
			if (D < 0.8f) break;
			float Want = FMath::Atan2(To.Y, To.X) + (Am * FMath::Sin(Sd / W1 + Ph1) + 0.45f * FMath::Sin(Sd / W2 + Ph2)) * FMath::Clamp((D - 3.f) / 14.f, 0.f, 1.f);
			const FVector2D Ahead = P + FVector2D(FMath::Cos(Hd), FMath::Sin(Hd)) * 3.f;
			// (the castle's ground and the lane ahead: turn toward the town's middle)
			const bool bCastle = InCastleZone(Ahead.X, Ahead.Y, 5.f);
			if (bCastle || !InsidePg(Ahead.X, Ahead.Y) || BorderDistPg(Ahead.X, Ahead.Y) < 4.f)
				Want = FMath::Atan2(S * 0.5f - P.Y, S * 0.45f - P.X);
			const float Turn = D < 4.f ? 0.5f : 0.12f;
			Hd += FMath::Clamp(FMath::FindDeltaAngleRadians(Hd, Want), -Turn, Turn);
			P += FVector2D(FMath::Cos(Hd), FMath::Sin(Hd)) * 0.5f; Sd += 0.5f;
			Out.Add(P);
		}
		Out.Add(B);
		return Out;
	};
	// ---- the main road, the castle's forecourt, the square, the cross road: straight and cobbled
	Road(GateU, Vc - 1, Cu0, Vc + 2);                                         // (from the gate itself)
	Mark(Cu0 - 6, Vc - 5, Cu0, Vc + 6, 1);                                    // (the castle's forecourt)
	TownRoads.Add(F.Rect(Cu0 - 6, Vc - 5, Cu0, Vc + 6));
	Mark(SqU0, SqV0, SqU1, SqV1, 2);
	TownSquare = F.Rect(SqU0, SqV0, SqU1, SqV1);
	const int32 Xu = Us + 6;
	RoadIn(Xu, 0, Xu + 3, S, false);
	// (the holy city: the main road on past the cathedral's flank to a second cross road behind its choir, the processional way
	// round it; the forge city's the same round its foundry)
	if (bMid)
	{
		RoadIn(Cu0 + CD + 4, 0, Cu0 + CD + 7, S, false);
		Road(Cu0 - 6, Cv0 - 4, Cu0 + CD + 4, Cv0 - 2);
		Road(Cu0 - 6, Cv0 + CW + 2, Cu0 + CD + 4, Cv0 + CW + 4);
	}
	// (the port: the quay along the harbour's edge, the main road on from the cross road behind the sluice house down to it)
	if (bPort)
	{
		Road(Hu0 - 4, Hv0, Hu0, Hv1);
		Road(Cu0 + CD + 7, Vc - 1, Hu0 - 4, Vc + 2);
	}
	for (const FIntRect& Rr : TownRoads) for (int32 X = Rr.Min.X; X < Rr.Max.X; ++X) for (int32 Y = Rr.Min.Y; Y < Rr.Max.Y; ++Y) if (In(FIntPoint(X, Y))) TownRoadMask[Idx(FIntPoint(X, Y))] = 1;
	for (int32 X = TownSquare.Min.X; X < TownSquare.Max.X; ++X) for (int32 Y = TownSquare.Min.Y; Y < TownSquare.Max.Y; ++Y) if (In(FIntPoint(X, Y))) TownRoadMask[Idx(FIntPoint(X, Y))] = 1;
	// ---- the earth roads (the third list of 2026-11-02: no grid): places scattered over the town (at least 15 tiles apart,
	// clear of the square, the castle and the lane), joined to the cobbled roads and to each other by the shortest tree
	// (Prim's: the cobbles' points are in it from the start) and a few loops besides; each join a wandering way. The trunk
	// ways (from the cobbles and the tree) are a road wide; the loops narrower lanes.
	{
		TArray<FVector2D> Nodes; int32 NAnchor = 0;
		for (int32 U = GateU + 8; U < Cu0 - 9; U += 13) Nodes.Add(FVector2D(U + 0.5f, Vc + 0.5f));
		for (int32 V = 6; V < S - 6; V += 13) if (InsidePg(Xu + 1.5f, V + 0.5f) && BorderDistPg(Xu + 1.5f, V + 0.5f) > 6.f && (V < SqV0 - 3 || V > SqV1 + 3)) Nodes.Add(FVector2D(Xu + 1.5f, V + 0.5f));
		NAnchor = Nodes.Num();
		// (about fifty places: with thirty, 12 tiles or more apart, the homes found frontage for 94, against 170 on the old grid)
		for (int32 T = 0; T < 2400 && Nodes.Num() < NAnchor + 52; ++T)
		{
			const FVector2D Q(R.FRandRange(5.f, S - 5.f), R.FRandRange(5.f, S - 5.f));
			if (!InsidePg(Q.X, Q.Y) || BorderDistPg(Q.X, Q.Y) < 7.f) continue;
			if (Q.X >= Cu0 - 10 && (!bMid || Q.X <= Cu0 + CD + 8) && Q.Y >= Cv0 - 8 && Q.Y <= Cv0 + CW + 8) continue;
			if (Q.X > SqU0 - 4 && Q.X < SqU1 + 4 && Q.Y > SqV0 - 4 && Q.Y < SqV1 + 4) continue;
			if (bPort && Q.X > Hu0 - 8) continue;                                          // (not on the quay or in the harbour)
			bool bNear = false;
			for (int32 K = 0; K < Nodes.Num() && !bNear; ++K) bNear = FVector2D::Distance(Nodes[K], Q) < (K < NAnchor ? 8.f : 12.f);
			if (!bNear) Nodes.Add(Q);
		}
		// (the tree: every place joins the nearest point already joined)
		TArray<bool> InTree; InTree.Init(false, Nodes.Num());
		for (int32 K = 0; K < NAnchor; ++K) InTree[K] = true;
		TArray<TPair<int32, int32>> Edges;
		for (int32 Added = NAnchor; Added < Nodes.Num(); ++Added)
		{
			int32 Ba = -1, Bb = -1; float Bd = MAX_flt;
			for (int32 A = 0; A < Nodes.Num(); ++A) if (InTree[A]) for (int32 B = 0; B < Nodes.Num(); ++B) if (!InTree[B])
			{
				const float D = FVector2D::Distance(Nodes[A], Nodes[B]);
				if (D < Bd) { Bd = D; Ba = A; Bb = B; }
			}
			if (Bb < 0) break;
			InTree[Bb] = true; Edges.Add({ Ba, Bb });
		}
		const int32 NTree = Edges.Num();
		// (the loops: a place's second nearest other place, when it is not already joined to it and not far)
		for (int32 A = NAnchor; A < Nodes.Num() && Edges.Num() < NTree + 16; ++A)
		{
			TArray<TPair<float, int32>> Near;
			for (int32 B = 0; B < Nodes.Num(); ++B) if (B != A) Near.Add({ FVector2D::Distance(Nodes[A], Nodes[B]), B });
			Near.Sort([](const TPair<float, int32>& X, const TPair<float, int32>& Y) { return X.Key < Y.Key; });
			for (int32 K = 1; K < FMath::Min(3, Near.Num()); ++K)
			{
				const int32 B = Near[K].Value;
				if (Near[K].Key > 34.f || Edges.ContainsByPredicate([&](const TPair<int32, int32>& E) { return (E.Key == A && E.Value == B) || (E.Key == B && E.Value == A); })) continue;
				if (R.FRand() < 0.6f) { Edges.Add({ A, B }); break; }
			}
		}
		for (int32 E = 0; E < Edges.Num(); ++E) PaintPath(Wander(Nodes[Edges[E].Key], Nodes[Edges[E].Value]), E < NTree ? 1.05f : 0.8f);
		UE_LOG(LogRDTown, Log, TEXT("RDTOWN earth roads: %d places (%d on the cobbles), %d ways (%d loops), %d strips"), Nodes.Num(), NAnchor, Edges.Num(), Edges.Num() - NTree, TownPaths.Num());
	}
	// the castle and the square's ground are taken; the gate's mouth kept clear
	Mark(Cu0 - 2, Cv0 - 2, bMid ? Cu0 + CD + 2 : S, Cv0 + CW + 2, 3);
	Mark(GateU, Vc - 4, GateU + 6, Vc + 5, 4);
	// (a rectangle wholly inside the outline, 2.5 tiles from the wall, on free ground)
	auto FitsIn = [&](int32 U0, int32 V0, int32 U1, int32 V1)
	{
		for (int32 U = U0; U < U1; ++U) for (int32 V = V0; V < V1; ++V)
		{
			if (U < 0 || V < 0 || U >= S || V >= S || Use[U * S + V] != 0) return false;
			if (BorderDistPg(U + 0.5f, V + 0.5f) < 2.5f) return false;
		}
		return true;
	};
	// (from a wanted corner toward the town's middle until it fits)
	auto PlaceRect = [&](int32& U0, int32& V0, int32 W, int32 H)
	{
		const int32 Su = U0 < S / 2 ? 1 : -1, Sv = V0 < S / 2 ? 1 : -1;
		for (int32 K = 0; K < 60; ++K)
			for (int32 J = 0; J <= K; ++J)
			{
				const int32 Uu = U0 + Su * (K - J), Vv = V0 + Sv * J;
				if (FitsIn(Uu, Vv, Uu + W, Vv + H)) { U0 = Uu; V0 = Vv; return true; }
			}
		return false;
	};
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
	// (in the corner wanted, moved in until it lies inside the wall's outline on free ground)
	// (the holy city's: a larger one behind the cathedral's choir, its chapel beside it)
	const int32 GyW = bHoly ? 16 : 12, GyH = bHoly ? 14 : 11;
	// (the forge city's behind its foundry the same, of the town's size)
	int32 GyU0 = bMid ? Cu0 + CD + 9 : S - 4 - 14 - CD - 6, GyV0 = bMid ? (bGraveLow ? Vc - 18 : Vc + 3) : bGraveLow ? 3 : S - 3 - 11;
	PlaceRect(GyU0, GyV0, GyW, GyH);
	Mark(GyU0, GyV0, GyU0 + GyW, GyV0 + GyH, 4);
	const FIntRect Gy = F.Rect(GyU0 + 1, GyV0 + 1, GyU0 + GyW - 1, GyV0 + GyH - 1);
	// (the mill in the other corner by the castle side, on open ground)
	int32 MlU0 = S - 4 - 14 - CD - 4, MlV0 = bGraveLow ? S - 3 - 7 : 3;
	PlaceRect(MlU0, MlV0, 7, 7);
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
	const FVector2D SqMid((SqU0 + SqU1) * 0.5f, (SqV0 + SqV1) * 0.5f), GateMid(GateU + 2.f, Vc + 0.5f);
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
	if (bHoly)
	{
		// (the holy city: the monastery by the cathedral's flank, two more chapels on the plaza's sides; no hedge witch)
		const FVector2D Flank((float)(Cu0 + CD / 2), (float)(Cv0 + CW + 9));
		if (Place(TK_Monastery, 12, 14, 8, 10, Near(Flank), 900, P)) Commit(TK_Monastery, P, 0, 2);
		for (int32 K = 0; K < 2; ++K)
			if (Place(TK_Chapel, 6, 7, 5, 6, Near(FVector2D(SqMid.X, SqMid.Y + (K ? 14.f : -14.f))), 900, P)) Commit(TK_Chapel, P, 0, 2);
	}
	else if (bForge)
	{
		// (the forge city: the guild's workshops (an armourer's, a weaponsmith's, a gearwright's, a smelter) down the main road
		// and round the square, its trade; no hedge witch)
		for (int32 K = 0; K < 4; ++K)
		{
			const FVector2D Want = K < 2 ? FVector2D(GateU + 18.f + 12.f * K, Vc + (K ? 9.f : -9.f)) : FVector2D(SqMid.X, SqMid.Y + (K == 2 ? 15.f : -15.f));
			if (Place(TK_Workshop, 7, 9, 6, 7, Near(Want), 900, P)) Commit(TK_Workshop, P, 0, 2);
		}
	}
	else if (bPort)
	{
		// (the port: warehouses along the quay, their doors to it; no hedge witch)
		for (int32 K = 0; K < 4; ++K)
			if (Place(TK_Warehouse, 8, 10, 6, 7, Near(FVector2D(Hu0 - 9.f, Hv0 + 14.f + K * ((Hv1 - Hv0 - 28) / 3.f))), 900, P)) Commit(TK_Warehouse, P, 0, 2);
	}
	else if (Place(TK_Witch, 4, 4, 4, 4, [&](const FVector2D& Q) { return -(float)FVector2D::Distance(Q, SqMid); }, 900, P)) Commit(TK_Witch, P, 0, 1);
	// the homes: as many as fit; their state by chance (the user's: burned down, boarded up, or lived in)
	// (400 tries a home: a try is a rectangle anywhere in the town, and few land beside a winding road; at 80 the town had 94
	// homes once the earth roads wandered (the third list), 170 on the old grid)
	for (int32 H = 0; H < 170; ++H)
	{
		if (!Place(TK_Home, 4, 6, 4, 5, [&](const FVector2D& Q) { return R.FRand(); }, 400, P)) continue;
		const float U = R.FRand();
		// (the holy city is kept: few homes burned or boarded; the forge city fewer than Brokenspire, the siege is the foundry's)
		// (the port: many shut up, few burned: the tide's dead empty the houses)
		Commit(TK_Home, P, bHoly ? (U < 0.04f ? 1 : U < 0.10f ? 2 : 0) : bForge ? (U < 0.08f ? 1 : U < 0.18f ? 2 : 0) : bPort ? (U < 0.05f ? 1 : U < 0.25f ? 2 : 0) : (U < 0.2f ? 1 : U < 0.42f ? 2 : 0), 2);
	}
	// ---- the castle (its own frame: front toward -u, the main road's middle Vc); the holy city's cathedral
	{
		FTownBld B; B.Kind = bHoly ? TK_Cathedral : bForge ? TK_Foundry : bPort ? TK_SluiceHouse : TK_Castle; B.Seed = (uint32)R.RandHelper(0x7fffffff); B.Storeys = 2;
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
		if (B.Kind == TK_Cathedral)
		{
			// the holy city's cathedral (RDHoly.cpp builds it): the narthex at its front between the two bell towers' bases, the
			// nave, the choir behind it whose far wall holds the stair down into the catacombs, an aisle down each side
			const int32 Ew = 11, Ed = 4, Cd = 6;
			const int32 W0 = Vc - Ew / 2;
			const int32 RE = AddRoomRect(BI, F.Rect(Cu0, W0, Cu0 + Ed, W0 + Ew), ERDRoomKind::Shrine, F.Tile(Cu0 + 2, Vc));
			const int32 RN = AddRoomRect(BI, F.Rect(Cu0 + Ed, W0, Cu0 + CD - Cd, W0 + Ew), ERDRoomKind::Chapel, F.Tile(Cu0 + Ed + (CD - Cd - Ed) / 2, Vc));
			const int32 RC = AddRoomRect(BI, F.Rect(Cu0 + CD - Cd, W0, Cu0 + CD, W0 + Ew), ERDRoomKind::Crypt, F.Tile(Cu0 + CD - Cd / 2, Vc));
			const int32 RL = AddRoomRect(BI, F.Rect(Cu0 + Ed, Cv0, Cu0 + CD, W0), ERDRoomKind::Library, F.Tile(Cu0 + Ed + (CD - Ed) / 2, (Cv0 + W0) / 2));
			const int32 RR = AddRoomRect(BI, F.Rect(Cu0 + Ed, W0 + Ew, Cu0 + CD, Cv0 + CW), ERDRoomKind::Treasury, F.Tile(Cu0 + Ed + (CD - Ed) / 2, (W0 + Ew + Cv0 + CW) / 2));
			const int32 TL = AddRoomRect(BI, F.Rect(Cu0, Cv0, Cu0 + Ed, W0), ERDRoomKind::Storeroom, F.Tile(Cu0 + 2, (Cv0 + W0) / 2));
			const int32 TR = AddRoomRect(BI, F.Rect(Cu0, W0 + Ew, Cu0 + Ed, Cv0 + CW), ERDRoomKind::Storeroom, F.Tile(Cu0 + 2, (W0 + Ew + Cv0 + CW) / 2));
			CastleHallRoom = RC;
			const int32 Front = F.Side(-1, 0), Back = F.Side(1, 0), Left = F.Side(0, -1), Right = F.Side(0, 1);
			Rooms[RE].bDoorSide[Front] = true;
			AddEdge(B.DoorTile, Out);
			AddEdge(F.Tile(Cu0 + Ed - 1, Vc), F.Tile(Cu0 + Ed, Vc)); Rooms[RE].bDoorSide[Back] = true; Rooms[RN].bDoorSide[Front] = true;
			AddEdge(F.Tile(Cu0 + CD - Cd - 1, Vc), F.Tile(Cu0 + CD - Cd, Vc)); Rooms[RN].bDoorSide[Back] = true; Rooms[RC].bDoorSide[Front] = true;
			// (the aisles from the nave, two doors each; the bell towers from the narthex)
			for (const int32 Ua : { Cu0 + Ed + 3, Cu0 + CD - Cd - 3 })
			{
				AddEdge(F.Tile(Ua, W0), F.Tile(Ua, W0 - 1)); AddEdge(F.Tile(Ua, W0 + Ew - 1), F.Tile(Ua, W0 + Ew));
			}
			Rooms[RN].bDoorSide[Left] = Rooms[RN].bDoorSide[Right] = true; Rooms[RL].bDoorSide[Right] = true; Rooms[RR].bDoorSide[Left] = true;
			AddEdge(F.Tile(Cu0 + 2, W0), F.Tile(Cu0 + 2, W0 - 1)); AddEdge(F.Tile(Cu0 + 2, W0 + Ew - 1), F.Tile(Cu0 + 2, W0 + Ew));
			Rooms[RE].bDoorSide[Left] = Rooms[RE].bDoorSide[Right] = true; Rooms[TL].bDoorSide[Right] = true; Rooms[TR].bDoorSide[Left] = true;
			// (the choir's far wall: the stair down into the catacombs (the Mistgate's part: walked into, it opens them))
			Rooms[RC].bDoorSide[Back] = true;
			const FVector Far = TileWorld(F.Tile(Cu0 + CD - 1, Vc));
			const FVector Fw = FVector(RDTDir4[Back].X, RDTDir4[Back].Y, 0.f);
			MistgateAt = Far + Fw * (Generator->TileSize * 0.5f);
			MistgateNormal = -Fw;
			B.Label = FString::Printf(TEXT("The Cathedral of %s"), *Generator->TownName);
			continue;
		}
		if (B.Kind == TK_Foundry)
		{
			// the forge city's foundry (RDForge.cpp builds it): the gatehouse at its front between the two chimney stacks' bases
			// (barricaded: the siege), the casting hall, the furnace hall behind it whose far wall holds the gate down into The War
			// Engine, a workshop wing down each side (the armoury's racks, the stores of ore and gear)
			const int32 Ew = 11, Ed = 4, Cd = 7;
			const int32 W0 = Vc - Ew / 2;
			const int32 RE = AddRoomRect(BI, F.Rect(Cu0, W0, Cu0 + Ed, W0 + Ew), ERDRoomKind::GuardRoom, F.Tile(Cu0 + 2, Vc));
			const int32 RN = AddRoomRect(BI, F.Rect(Cu0 + Ed, W0, Cu0 + CD - Cd, W0 + Ew), ERDRoomKind::Forge, F.Tile(Cu0 + Ed + (CD - Cd - Ed) / 2, Vc));
			const int32 RC = AddRoomRect(BI, F.Rect(Cu0 + CD - Cd, W0, Cu0 + CD, W0 + Ew), ERDRoomKind::Forge, F.Tile(Cu0 + CD - Cd / 2, Vc));
			const int32 RL = AddRoomRect(BI, F.Rect(Cu0 + Ed, Cv0, Cu0 + CD, W0), ERDRoomKind::Armory, F.Tile(Cu0 + Ed + (CD - Ed) / 2, (Cv0 + W0) / 2));
			const int32 RR = AddRoomRect(BI, F.Rect(Cu0 + Ed, W0 + Ew, Cu0 + CD, Cv0 + CW), ERDRoomKind::Storeroom, F.Tile(Cu0 + Ed + (CD - Ed) / 2, (W0 + Ew + Cv0 + CW) / 2));
			const int32 TL = AddRoomRect(BI, F.Rect(Cu0, Cv0, Cu0 + Ed, W0), ERDRoomKind::Storeroom, F.Tile(Cu0 + 2, (Cv0 + W0) / 2));
			const int32 TR = AddRoomRect(BI, F.Rect(Cu0, W0 + Ew, Cu0 + Ed, Cv0 + CW), ERDRoomKind::Storeroom, F.Tile(Cu0 + 2, (W0 + Ew + Cv0 + CW) / 2));
			CastleHallRoom = RC;
			const int32 Front = F.Side(-1, 0), Back = F.Side(1, 0), Left = F.Side(0, -1), Right = F.Side(0, 1);
			Rooms[RE].bDoorSide[Front] = true;
			AddEdge(B.DoorTile, Out);
			AddEdge(F.Tile(Cu0 + Ed - 1, Vc), F.Tile(Cu0 + Ed, Vc)); Rooms[RE].bDoorSide[Back] = true; Rooms[RN].bDoorSide[Front] = true;
			AddEdge(F.Tile(Cu0 + CD - Cd - 1, Vc), F.Tile(Cu0 + CD - Cd, Vc)); Rooms[RN].bDoorSide[Back] = true; Rooms[RC].bDoorSide[Front] = true;
			// (the wings from the casting hall, two doors each; the stacks' bases from the gatehouse)
			for (const int32 Ua : { Cu0 + Ed + 3, Cu0 + CD - Cd - 3 })
			{
				AddEdge(F.Tile(Ua, W0), F.Tile(Ua, W0 - 1)); AddEdge(F.Tile(Ua, W0 + Ew - 1), F.Tile(Ua, W0 + Ew));
			}
			Rooms[RN].bDoorSide[Left] = Rooms[RN].bDoorSide[Right] = true; Rooms[RL].bDoorSide[Right] = true; Rooms[RR].bDoorSide[Left] = true;
			AddEdge(F.Tile(Cu0 + 2, W0), F.Tile(Cu0 + 2, W0 - 1)); AddEdge(F.Tile(Cu0 + 2, W0 + Ew - 1), F.Tile(Cu0 + 2, W0 + Ew));
			Rooms[RE].bDoorSide[Left] = Rooms[RE].bDoorSide[Right] = true; Rooms[TL].bDoorSide[Right] = true; Rooms[TR].bDoorSide[Left] = true;
			// (the furnace hall's far wall: the iron gate down into The War Engine (the Mistgate's part: walked into, it opens it))
			Rooms[RC].bDoorSide[Back] = true;
			const FVector Far = TileWorld(F.Tile(Cu0 + CD - 1, Vc));
			const FVector Fw = FVector(RDTDir4[Back].X, RDTDir4[Back].Y, 0.f);
			MistgateAt = Far + Fw * (Generator->TileSize * 0.5f);
			MistgateNormal = -Fw;
			B.Label = FString::Printf(TEXT("The Great Foundry of %s"), *Generator->TownName);
			continue;
		}
		if (B.Kind == TK_SluiceHouse)
		{
			// the port's sluice house (RDPort.cpp furnishes it): one stone hall, the grated way down into the sewers at its far
			// wall (the Mistgate's part: walked into, it opens them)
			const int32 RI = AddRoomRect(BI, F.Rect(Cu0, Cv0, Cu0 + CD, Cv0 + CW), ERDRoomKind::Crypt, F.Tile(Cu0 + CD / 2, Vc));
			Rooms[RI].bDoorSide[B.DoorSide] = true;
			AddEdge(B.DoorTile, Out);
			const int32 Back = F.Side(1, 0);
			Rooms[RI].bDoorSide[Back] = true;
			const FVector Far = TileWorld(F.Tile(Cu0 + CD - 1, Vc));
			const FVector Fw = FVector(RDTDir4[Back].X, RDTDir4[Back].Y, 0.f);
			MistgateAt = Far + Fw * (Generator->TileSize * 0.5f);
			MistgateNormal = -Fw;
			CastleHallRoom = RI;
			B.Label = TEXT("The Sluice House");
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
		case TK_Workshop: K = ERDRoomKind::Forge; break;
		case TK_Warehouse: K = ERDRoomKind::Storeroom; break;
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
	// ---- the castle's round towers, its stair turret and the path to it (no draws: the plan's stream is untouched); the
	// cathedral's bell towers are its own (RDHoly.cpp)
	if (!bMid) CastleTowersPlan();
	// ---- the wall's towers (2 x 2 tiles astride the wall at its corners, beside the gate and every 15 tiles or so): void
	// (since 2026-11-02 at the corners of the wall's outline, the gate's stretch's two among them; a long straight stretch gets
	// one more half way)
	for (int32 I = 0, J = TownBorder.Num() - 1; I < TownBorder.Num(); J = I++)
	{
		FTownSpot Sp; Sp.Kind = TS_Tower; Sp.At = FVector(TownBorder[I].X, TownBorder[I].Y, GetActorLocation().Z);
		TownSpots.Add(Sp);
		if (FVector2D::Distance(TownBorder[I], TownBorder[J]) > 34.f * Generator->TileSize)
		{
			FTownSpot Sm; Sm.Kind = TS_Tower; const FVector2D Mm = (TownBorder[I] + TownBorder[J]) * 0.5f; Sm.At = FVector(Mm.X, Mm.Y, GetActorLocation().Z);
			TownSpots.Add(Sm);
		}
	}
	// ---- the gate (on the gate's stretch, across the main road), outside it the way on
	{
		const FVector Out = FVector(RDTDir4[F.Side(-1, 0)].X, RDTDir4[F.Side(-1, 0)].Y, 0.f);
		const FVector2D Gl = F.LocalF((float)GateU, Vc + 0.5f);
		TownGate = FVector(GetActorLocation().X + Gl.X * Generator->TileSize, GetActorLocation().Y + Gl.Y * Generator->TileSize, GetActorLocation().Z);
		TownGateOut = Out;
		FTownSpot Sp; Sp.Kind = TS_Gate; Sp.At = TownGate; Sp.Yaw = Out.Rotation().Yaw;
		TownSpots.Add(Sp);
	}
	// ---- what stands on the square and outdoors: the well, the quest board, the stalls, the lamps; the graves; the still
	{
		const FIntRect Sq = TownSquare;
		const FVector Mid = (TileWorld(Sq.Min) + TileWorld(Sq.Max - FIntPoint(1, 1))) * 0.5f;
		const FVector Ua = FVector(RDTDir4[F.Side(1, 0)].X, RDTDir4[F.Side(1, 0)].Y, 0.f), Va = FVector(RDTDir4[F.Side(0, 1)].X, RDTDir4[F.Side(0, 1)].Y, 0.f);
		// (the holy city's plaza: a fountain where the well would be, a wayside shrine in each of its corners, a statue on each side)
		FTownSpot W; W.Kind = bHoly ? TS_Fountain : TS_Well; W.At = Mid + Va * 600.f; TownSpots.Add(W);
		if (bHoly)
		{
			for (const FVector& C : { Mid + Ua * 1900.f + Va * 1900.f, Mid + Ua * 1900.f - Va * 1900.f, Mid - Ua * 1900.f + Va * 1900.f, Mid - Ua * 1900.f - Va * 1900.f })
			{
				FTownSpot Sh; Sh.Kind = TS_Shrine; Sh.At = C; Sh.Yaw = (Mid - C).Rotation().Yaw; TownSpots.Add(Sh);
			}
			for (const float Sd : { -1.f, 1.f })
			{
				FTownSpot St; St.Kind = TS_Statue; St.At = Mid + Va * Sd * 2050.f; St.Yaw = (-Va * Sd).Rotation().Yaw; TownSpots.Add(St);
			}
		}
		if (bForge)
		{
			// (the forge city's square: the guild's great anvil across from the well, an open forge in each of its corners, its
			// smoke and sparks; ore carts on their rails along the main road toward the foundry; a crane beside the foundry's door)
			FTownSpot An; An.Kind = TS_Anvil; An.At = Mid - Va * 600.f; An.Yaw = (-Ua).Rotation().Yaw; TownSpots.Add(An);
			for (const FVector& C : { Mid + Ua * 1900.f + Va * 1900.f, Mid + Ua * 1900.f - Va * 1900.f, Mid - Ua * 1900.f + Va * 1900.f, Mid - Ua * 1900.f - Va * 1900.f })
			{
				FTownSpot Fg; Fg.Kind = TS_Forge; Fg.At = C; Fg.Yaw = (Mid - C).Rotation().Yaw; TownSpots.Add(Fg);
			}
			for (int32 K = 0; K < 3; ++K)
			{
				// (on the forecourt's sides, clear of the main road's three tiles and of the foundry's front at 12 tiles)
				FTownSpot Ct; Ct.Kind = TS_Cart; Ct.At = Mid + Ua * (1900.f + 550.f * K) + Va * 780.f * (K % 2 ? 1.f : -1.f); Ct.Yaw = Ua.Rotation().Yaw; TownSpots.Add(Ct);
			}
		}
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
		// (the holy city's elder is its archbishop, before the cathedral's door: below)
		FTownPost Pe; Pe.Role = ERDTownRole::Elder; Pe.At = Bd.At + Ua * -220.f + Va * 160.f; Pe.Yaw = Bd.Yaw + 180.f; if (!bMid) TownPosts.Add(Pe);
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
			// (on the lane: a tile in from one of the wall's corners, a quarter of the way round each)
			const FVector2D Bc = TownBorder.Num() ? TownBorder[(K * TownBorder.Num() / 4 + 1) % TownBorder.Num()] : FVector2D::ZeroVector;
			const FVector Mid_ = TileWorld(F.Tile(S / 2, S / 2));
			Mi.At = FVector(Bc.X, Bc.Y, Mid_.Z) + (Mid_ - FVector(Bc.X, Bc.Y, Mid_.Z)).GetSafeNormal2D() * (Generator->TileSize * 1.6f);
			TownPosts.Add(Mi);
		}
		for (int32 K = 0; K < 4; ++K)
		{
			// (the holy city: pilgrims come in at the gate where Brokenspire's refugees camp)
			FTownPost Rf; Rf.Role = bHoly ? ERDTownRole::Pilgrim : ERDTownRole::Refugee; Rf.Index = K; Rf.Wander = bHoly ? 2500.f : 300.f;
			Rf.At = GateIn + Ua * 500.f + Va * ((K % 2 ? 1.f : -1.f) * (650.f + 120.f * K)); Rf.Yaw = R.FRandRange(0, 360);
			TownPosts.Add(Rf);
		}
		// (a camp of the refugees: tents by the wall near the gate; the holy city's pilgrims' tents the same)
		for (int32 K = 0; K < 3; ++K)
		{
			FTownSpot T; T.Kind = TS_Tent; T.At = GateIn + Ua * (900.f + 350.f * K) + Va * (K % 2 ? 1300.f : -1300.f); T.Yaw = Va.Rotation().Yaw + (K % 2 ? 180.f : 0.f);
			TownSpots.Add(T);
		}
		if (bHoly)
		{
			// the holy city's people before the cathedral: the archbishop (its elder: talk, quests) and the templars at its door,
			// beggars on its steps, pilgrims about the plaza, a second preacher; statues flanking its door
			const FVector Pz = (TileWorld(TownSquare.Min) + TileWorld(TownSquare.Max - FIntPoint(1, 1))) * 0.5f;
			FTownPost Ab; Ab.Role = ERDTownRole::Elder; Ab.At = CDoor - Ua * 350.f - Va * 420.f; Ab.Yaw = (-Ua).Rotation().Yaw; TownPosts.Add(Ab);
			for (int32 K = 0; K < 2; ++K) { FTownPost Tp; Tp.Role = ERDTownRole::Templar; Tp.At = CDoor - Ua * 150.f + Va * (K ? 650.f : -650.f); Tp.Yaw = (-Ua).Rotation().Yaw; Tp.Index = K; TownPosts.Add(Tp); }
			for (int32 K = 0; K < 3; ++K) { FTownPost Bg; Bg.Role = ERDTownRole::Beggar; Bg.At = CDoor - Ua * 900.f + Va * ((K - 1) * 800.f + 300.f); Bg.Yaw = Ua.Rotation().Yaw; Bg.Wander = 150.f; Bg.Index = K; TownPosts.Add(Bg); }
			for (int32 K = 0; K < 6; ++K) { FTownPost Pl; Pl.Role = ERDTownRole::Pilgrim; Pl.At = Pz + Va * ((K % 3 - 1) * 900.f) + Ua * ((K / 3) * 900.f - 450.f); Pl.Wander = 2200.f; Pl.Index = 4 + K; TownPosts.Add(Pl); }
			FTownPost Pp2; Pp2.Role = ERDTownRole::Preacher; Pp2.At = Pz + Ua * 600.f - Va * 1300.f; Pp2.Yaw = Va.Rotation().Yaw; Pp2.Wander = 250.f; TownPosts.Add(Pp2);
			for (const float Sd : { -1.f, 1.f })
			{
				FTownSpot St; St.Kind = TS_Statue; St.At = CDoor - Ua * 100.f + Va * Sd * 1050.f; St.Yaw = (-Ua).Rotation().Yaw; TownSpots.Add(St);
			}
		}
		if (bForge)
		{
			// the forge city's siege of its own foundry (its machines woke: The War Engine): a barricade across the forecourt facing
			// the foundry's door, a gap in its middle for the way in; the guild's soldiers behind it, braziers at its ends; the
			// guildmaster (its elder: talk, quests) by the barricade; the workers at the square's open forges
			const float Bar = 900.f;
			for (int32 K = -2; K <= 2; ++K)
			{
				if (K == 0) continue;
				FTownSpot Bk; Bk.Kind = TS_Barricade; Bk.At = CDoor - Ua * Bar + Va * (K * 330.f + (K > 0 ? 80.f : -80.f)); Bk.Yaw = Ua.Rotation().Yaw; TownSpots.Add(Bk);
			}
			for (const float Sd : { -1.f, 1.f }) { FTownSpot L; L.Kind = TS_Lamp; L.At = CDoor - Ua * (Bar + 120.f) + Va * Sd * 1050.f; TownSpots.Add(L); }
			for (int32 K = 0; K < 4; ++K) { FTownPost Sd_; Sd_.Role = ERDTownRole::Soldier; Sd_.At = CDoor - Ua * (Bar + 260.f) + Va * ((K - 1.5f) * 420.f); Sd_.Yaw = Ua.Rotation().Yaw; Sd_.Index = 3 + K; TownPosts.Add(Sd_); }
			FTownPost Gm; Gm.Role = ERDTownRole::Elder; Gm.At = CDoor - Ua * (Bar + 380.f) - Va * 1350.f; Gm.Yaw = (-Va).Rotation().Yaw + 90.f; TownPosts.Add(Gm);
			int32 Wk = 0;
			for (const FTownSpot& Sp : TownSpots)
				if (Sp.Kind == TS_Forge) { FTownPost W; W.Role = ERDTownRole::Worker; W.At = Sp.At + FRotator(0, Sp.Yaw, 0).RotateVector(FVector(160.f, 120.f, 0)); W.Yaw = Sp.Yaw + 180.f; W.Index = Wk++; TownPosts.Add(W); }
		}
		if (bPort)
		{
			// the port's harbour (RDPort.cpp builds it): each pier (its deck, posts, the blockers along its sides), a ship moored
			// down one side of it and a rowboat by the other, two wrecks in the harbour's corners; on the quay the drowned dead the
			// tide brought in, gibbets, the fishers' racks, nets and crates; the harbourmaster (its elder: talk, quests) on the quay
			// by the road down, sailors on the piers, fishers at the racks, mourners by the dead
			const float Mt = Generator->TileSize;
			auto Wp = [&](float U, float V) { const FVector2D L = F.LocalF(U, V); return FVector(GetActorLocation().X + L.X * Mt, GetActorLocation().Y + L.Y * Mt, GetActorLocation().Z); };
			const float AlongU = Ua.Rotation().Yaw;
			FRandomStream RP((int32)(R.GetInitialSeed() ^ 0x5EA9u));
			int32 Sl = 0;
			for (int32 K = 0; K < TownPiers.Num(); ++K)
			{
				const int32 Pv = Hv0 + 10 + K * ((Hv1 - Hv0 - 22) / 4);
				FTownSpot Pr; Pr.Kind = TS_Pier; Pr.At = Wp(Hu0, Pv + 1.f); Pr.Yaw = AlongU; Pr.Bld = K; TownSpots.Add(Pr);
				const bool bLeft = (K % 2) == 0;
				FTownSpot Sh; Sh.Kind = TS_Ship; Sh.At = Wp(Hu0 + 8.f + RP.FRandRange(-1.5f, 1.5f), bLeft ? Pv - 2.6f : Pv + 4.6f); Sh.Yaw = AlongU + (RP.RandBool() ? 0.f : 180.f); TownSpots.Add(Sh);
				FTownSpot Bt; Bt.Kind = TS_Boat; Bt.At = Wp(Hu0 + 3.f + RP.FRandRange(0.f, 6.f), bLeft ? Pv + 3.3f : Pv - 1.3f); Bt.Yaw = AlongU + RP.FRandRange(-25.f, 25.f); TownSpots.Add(Bt);
				for (int32 J = 0; J < 2; ++J) { FTownPost Sa; Sa.Role = ERDTownRole::Sailor; Sa.At = Wp(Hu0 + 4.f + J * 8.f, Pv + 1.f); Sa.Yaw = AlongU + (J ? 0.f : 180.f); Sa.Wander = 400.f; Sa.Index = Sl++; TownPosts.Add(Sa); }
			}
			for (const float Vw : { Hv0 + 3.f, Hv1 - 3.f }) { FTownSpot Wr; Wr.Kind = TS_Wreck; Wr.At = Wp(S - 6.f, Vw); Wr.Yaw = AlongU + RP.FRandRange(60.f, 120.f); TownSpots.Add(Wr); }
			// (on the quay: the drowned dead in twos and threes at the water's edge, the mourners by them; gibbets with their
			// cages; the fishers' racks with nets and crates between the piers' roots)
			int32 Mo = 0;
			for (int32 K = 0; K < 6; ++K)
			{
				const float Vb = Hv0 + 6.f + K * ((Hv1 - Hv0 - 12) / 5.f) + RP.FRandRange(-2.f, 2.f);
				for (int32 J = 0; J < 1 + RP.RandRange(1, 2); ++J) { FTownSpot Bd_; Bd_.Kind = TS_Body; Bd_.At = Wp(Hu0 - 1.2f + RP.FRandRange(-0.4f, 0.3f), Vb + J * 1.1f); Bd_.Yaw = RP.FRandRange(0.f, 360.f); TownSpots.Add(Bd_); }
				if (K % 2 == 0) { FTownPost Mn; Mn.Role = ERDTownRole::Mourner; Mn.At = Wp(Hu0 - 2.6f, Vb + 0.5f); Mn.Yaw = AlongU; Mn.Index = 1 + Mo++; TownPosts.Add(Mn); }
			}
			for (int32 K = 0; K < 3; ++K) { FTownSpot Gb; Gb.Kind = TS_Gibbet; Gb.At = Wp(Hu0 - 3.5f, Hv0 + 20.f + K * ((Hv1 - Hv0 - 40) / 2.f)); Gb.Yaw = AlongU; TownSpots.Add(Gb); }
			int32 Fi = 0;
			for (int32 K = 0; K < 4; ++K)
			{
				const int32 Pv = Hv0 + 10 + K * ((Hv1 - Hv0 - 22) / 4) + 11;
				FTownSpot Dp_; Dp_.Kind = TS_DockProps; Dp_.At = Wp(Hu0 - 2.f, Pv); Dp_.Yaw = AlongU + 180.f; TownSpots.Add(Dp_);
				FTownPost Fs; Fs.Role = ERDTownRole::Fisher; Fs.At = Wp(Hu0 - 2.f, Pv + 2.2f); Fs.Yaw = AlongU; Fs.Wander = 300.f; Fs.Index = Fi++; TownPosts.Add(Fs);
			}
			FTownPost Hm; Hm.Role = ERDTownRole::Elder; Hm.At = Wp(Hu0 - 3.f, Vc - 3.f); Hm.Yaw = AlongU; TownPosts.Add(Hm);
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
			// (the holy city: monks in the monastery and walking out from it; a preacher in the cathedral's nave, a monk at prayer)
			// (the forge city's workshops: a worker at the anvil inside, another walking out to the square's forges)
			case TK_Workshop: Post(ERDTownRole::Worker, Ctr, 250.f, 10 + BI); Post(ERDTownRole::Worker, TileWorld(B.DoorTile) - In_ * 300.f, 3000.f, 30 + BI); break;
			// (the port's warehouses: a dockhand inside among the crates, another on the quay outside)
			case TK_Warehouse: Post(ERDTownRole::Dockhand, Ctr, 300.f, 10 + BI); Post(ERDTownRole::Dockhand, TileWorld(B.DoorTile) - In_ * 300.f, 2500.f, 30 + BI); break;
			case TK_Monastery: Post(ERDTownRole::Monk, Inside, 0.f, 0); Post(ERDTownRole::Monk, Ctr, 600.f, 1); Post(ERDTownRole::Monk, TileWorld(B.DoorTile) - In_ * 300.f, 3500.f, 2); Post(ERDTownRole::Monk, TileWorld(B.DoorTile) - In_ * 300.f, 3500.f, 3); break;
			case TK_Cathedral:
				if (B.Rooms.Num() > 1)
				{
					const FRoom& Nv = Rooms[B.Rooms[1]];
					const FVector Nc = (TileWorld(Nv.Min) + TileWorld(Nv.Max - FIntPoint(1, 1))) * 0.5f;
					// (the preacher at the nave's far end facing the door (the posts face out), a monk among the pews)
					Post(ERDTownRole::Preacher, Nc + In_ * 900.f, 0.f, 9); Post(ERDTownRole::Monk, Nc - In_ * 300.f, 400.f, 4);
				}
				break;
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
	// (the holy city's white stone: "Holy.<part>", 892's pieces (882 rewrites the "Town." ones))
	if (B.Style == 4) return FName(*FString::Printf(TEXT("Holy.%s"), Part));
	// (the forge city's soot-dark stone: "Forge.<part>", 894's pieces)
	if (B.Style == 5) return FName(*FString::Printf(TEXT("Forge.%s"), Part));
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
					const int32 YawC = R.RandRange(0, 3), YawR = R.RandRange(0, 3);
					// (over the stair's upper steps the stairwell: no ceiling, no roof)
					if (!CastleStairwell.Contains(Tl))
					{
						AddPieceAt(TEXT("Castle.Ceil_Room"), C + FVector(0, 0, H), 90.f * YawC);
						// the roof over it (a flat stone floor seen from above): the wall walk, walked on
						AddPieceAt(TEXT("Town.CastleRoof"), C + FVector(0, 0, H + 40.f), 90.f * YawR);
					}
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
		CastleStairBuild();
		// the Mistgate: an arch in the hall's back wall, its glow (play: the generator's)
		AddPieceAt(TEXT("Town.MistArch"), MistgateAt - MistgateNormal * 30.f, MistgateNormal.Rotation().Yaw, 1.f, true);
		return;
	}
	if (B.Kind == TK_Cathedral) { CathedralShell(BI); return; }
	if (B.Kind == TK_Foundry) { FoundryShell(BI); return; }
	// (the holy city: its houses of white stone (Town.Holy_*), a burned one's timbers as anywhere; the forge city's of soot-dark
	// stone (Forge.*, 2026-11-07))
	if (Generator->TownPlan == 1) B.Style = B.State == 1 ? 3 : 4;
	else if (Generator->TownPlan == 2) B.Style = B.State == 1 ? 3 : 5;
	else
	B.Style = B.State == 1 ? 3 : (B.Kind == TK_Temple || B.Kind == TK_Smithy || B.Kind == TK_Barracks || B.Kind == TK_Chapel || B.Kind == TK_SluiceHouse) ? 1
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
			// (a burned house: how many storeys of this segment still stand, from the ground up: a storey stands only on the one
			// under it (the user's of 2026-11-02: upper walls stood on nothing where the fire had taken the lower ones); the
			// doorway's segment keeps its doorway)
			int32 Standing = B.Storeys;
			if (bBurnt)
			{
				const float U = R.FRand();
				const bool bDoorCol = Si == 0 && K == DoorK;
				Standing = U < (bDoorCol ? 0.f : 0.22f) ? 0 : U < 0.6f ? 1 : B.Storeys;
			}
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
				// (a burned house: the fire took this storey and all above it)
				if (St >= Standing) break;
				AddPiece(Nm, WallT(P, Sd.Out, Z));
				// (a window's sill stands out of the wall where its collision does not reach: a hidden box over the piece's
				// whole bounds (the user's of 2026-11-02: she walked through the ledges))
				if (Nm != TownPiece(B, TEXT("Wall")) && !bDoor) AddMeshBoundsCollider(Nm, WallT(P, Sd.Out, Z));
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
			// (a burned house has no roof left: the pieces that stayed hung over nothing (the user's of 2026-11-02); its charred
			// beams lie inside)
			if (bBurnt) continue;
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
	// (a torch inside beside the door of every building someone can be in: the store and the storehouse had none of the
	// dungeon furnishing's, and their keepers stood in the dark; the town's lights burn while someone awake is inside)
	if (!bBurnt && !bBoarded)
		AddTorch(TownBldPoint(B, Hx - 24.f, (DoorK + 0.5f) * M - Hy - 115.f, 235.f), Yaw0 + 180.f, 110.f);
	// a burned house: rubble and charred beams inside
	if (bBurnt)
		for (int32 K = 0; K < 3 + Nx * Ny / 6; ++K)
			AddPieceAt(R.RandBool() ? FName(TEXT("Debris")) : FName(TEXT("Town.CharredBeam")), TownBldPoint(B, R.FRandRange(-Hx + 80.f, Hx - 80.f), R.FRandRange(-Hy + 80.f, Hy - 80.f), 2.f), R.FRandRange(0, 360), 1.f, true);
	// its sign over the door (the trades'), with what it is painted on both faces of its board (the user's of 2026-11-02: "if a
	// building in Brokenspire has a purpose, there should be a sign outside the door saying what the building is")
	if (B.Kind != TK_Home)
	{
		// (its bracket against the wall's face: 25 cm off the wall's line it hung in the air (the list of 2026-11-04: "the signs
		// outside buildings look like they're floating"))
		const FTransform Sg = WallT(FVector2D(Hx + 9.f, (DoorK + 0.5f) * M - Hy + 140.f), FVector2D(1, 0), 262.f);
		AddPiece(TEXT("Town.Sign"), Sg, true);
		AddSignText(Sg, RDTSignText(B.Kind));
	}
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
	case TK_Smithy: case TK_Workshop:
	{
		// (the forge city's workshops (2026-11-07): the smithy's round for their workers, no service)
		if (B.Kind == TK_Smithy) Service(TS_Smith, NAME_None, TileWorld(B.DoorTile) + In_ * 450.f, FaceDoor);
		// (the smith's round (the third list): hammering at his anvil, at the forge's fire, and by his door for her)
		const FBox2D Rb(FVector2D(TileWorld(Rm.Min)) - FVector2D(150.f), FVector2D(TileWorld(Rm.Max - FIntPoint(1, 1))) + FVector2D(150.f));
		auto Inside = [&](const FVector& P) { return Rb.IsInside(FVector2D(P)); };
		auto Wk = [&](const TCHAR* Kind, const FVector& At, float Yaw, const TCHAR* Prop)
		{
			FTownWork W; W.Kind = Kind; W.At = At; W.Yaw = Yaw; W.Group = TW_Smithy; W.Bld = BI; W.Prop = Prop ? FName(Prop) : NAME_None;
			TownWorks.Add(W);
		};
		const float* RHam = Generator->TownWorkReach.Find(TEXT("Hammer"));
		bool bAnvil = false;
		for (const FVector& Av : AnvilPoints)
			if (Inside(Av))
			{
				const FVector Tc = (Ctr - Av).GetSafeNormal2D();
				Wk(TEXT("Hammer"), Av + Tc * (RHam ? *RHam : 85.f), (-Tc).Rotation().Yaw, TEXT("Hammer"));
				bAnvil = true; break;
			}
		if (!bAnvil) Wk(TEXT("Hammer"), Back - In_ * 180.f, In_.Rotation().Yaw, TEXT("Hammer"));
		bool bForge = false;
		for (const FRDFirePoint& Fp : FirePoints)
			if (Inside(Fp.At))
			{
				const FVector Tc = (Ctr - Fp.At).GetSafeNormal2D();
				Wk(TEXT("Forge"), FVector(Fp.At.X, Fp.At.Y, GetActorLocation().Z) + Tc * 130.f, (-Tc).Rotation().Yaw, nullptr);
				bForge = true; break;
			}
		if (!bForge) Wk(TEXT("Forge"), Ctr + Along * 250.f, (-Along).Rotation().Yaw, nullptr);
		if (B.Kind == TK_Smithy) Wk(TEXT("Talk"), TileWorld(B.DoorTile) + In_ * 450.f, FaceDoor, nullptr);
		break;
	}
	case TK_Tavern:
	{
		Service(TS_Bar, TEXT("TableLong"), Back, FaceDoor + 90.f);
		// (the third list: "taverns with customers in them being served by villagers": up to six small tables, a stool each
		// side; each stool a seat (its customer's feet before it, facing the table), each table a place to serve it from; the
		// bar's front a place to stand and talk and to take a tray from)
		const FVector Ac(In_.Y, -In_.X, 0);
		const float* RSit = Generator->TownWorkReach.Find(TEXT("SitDrink"));
		const float* RServe = Generator->TownWorkReach.Find(TEXT("CarryIdle"));
		int32 Tables = 0, Seat = 0;
		for (const FVector& Q : { Ctr + Ac * 380.f, Ctr - Ac * 380.f, Ctr + Ac * 380.f - In_ * 320.f, Ctr - Ac * 380.f - In_ * 320.f, Ctr + Ac * 380.f + In_ * 320.f, Ctr - Ac * 380.f + In_ * 320.f })
		{
			if (Tables >= 6) break;
			FurnRoom = RI;
			const bool bT = AddPieceAt(TEXT("TableSmall"), Q, Ac.Rotation().Yaw);
			if (bT)
			{
				MarkBlocked(Q, 0.f, FVector2D(120, 120));
				for (int32 K = 0; K < 2; ++K)
				{
					// (the stool where the sitting clips' seat is: the table's edge 26 cm before her (the table 75 cm deep), the
					// seat 45 cm high (the stool is 48: set 3 cm into the floor))
					const FVector Sd = Ac * (K ? 1.f : -1.f);
					const FVector St = Q + Sd * 64.f;
					AddPieceAt(TEXT("Stool"), St - FVector(0, 0, 3.f), (-Sd).Rotation().Yaw);
					// (her feet a little out from the stool's middle toward the table: the clip's seat is behind her root)
					FTownWork W; W.Kind = (Seat++ % 2) ? TEXT("SitTalk") : TEXT("SitDrink"); W.At = St - Sd * (RSit ? *RSit : 0.f); W.Yaw = (-Sd).Rotation().Yaw;
					W.Group = TW_Seat; W.Bld = BI; W.Prop = W.Kind == TEXT("SitDrink") ? FName(TEXT("Mug")) : NAME_None;
					TownWorks.Add(W);
				}
				FTownWork Sv; Sv.Kind = TEXT("CarryIdle"); Sv.At = Q - In_ * (RServe ? *RServe : 85.f); Sv.Yaw = In_.Rotation().Yaw; Sv.Group = TW_Serve; Sv.Bld = BI; Sv.Prop = TEXT("Tray");
				TownWorks.Add(Sv);
				// (the list of 2026-11-04: "inside the inns, it is often too dark where the customers are sitting": a candle on
				// every table, its light over the table, food set out on some (taken with F); no draws from the plan's stream)
				const FRDPiece* Tp = Generator->Piece(TEXT("TableSmall"));
				const float Tz = Tp ? (float)Tp->Size.Z : 76.f;
				AddPieceAt(TEXT("Candles"), Q + Ac * 30.f + FVector(0, 0, Tz), 25.f * Tables, 1.f, true);
				AddEffect(TEXT("CandleFire"), Q + Ac * 30.f + FVector(0, 0, Tz + 18.f), 1.f);
				AddLight(Q + FVector(0, 0, Tz + 95.f), FLinearColor(1.f, 0.64f, 0.34f), 95.f, 720.f, false, 0.12f);
				{
					FRandomStream Rf((int32)HashCombine(GetTypeHash(FIntPoint(FMath::RoundToInt(Q.X), FMath::RoundToInt(Q.Y))), 0x7AB1u));
					if (Rf.FRand() < 0.65f) TownFoodOn(Rf, Q - Ac * 22.f + FVector(0, 0, Tz), Ac.Rotation().Yaw);
				}
				++Tables;
			}
			FurnRoom = -1;
		}
		// (lamps hung over the seating, a side each: the room's torches by the walls left its middle dark)
		for (int32 K = -1; K <= 1; K += 2) AddLight(Ctr + Ac * (K * 380.f) + FVector(0, 0, 255.f), FLinearColor(1.f, 0.6f, 0.3f), 170.f, 1000.f, false, 0.08f);
		// (the bar's front: the server takes a tray there; customers stand and talk)
		for (const FTownSpot& Sp : TownSpots)
			if (Sp.Kind == TS_Bar && Sp.Bld == BI)
			{
				FTownWork Tk; Tk.Kind = TEXT("CarryIdle"); Tk.At = Sp.At - In_ * 120.f; Tk.Yaw = In_.Rotation().Yaw; Tk.Group = TW_Bar; Tk.Bld = BI; Tk.Prop = TEXT("Tray");
				TownWorks.Add(Tk);
				for (int32 K = -1; K <= 1; K += 2) { FTownWork Tl; Tl.Kind = TEXT("Talk"); Tl.At = Sp.At - In_ * 120.f + Ac * (K * 160.f); Tl.Yaw = In_.Rotation().Yaw; Tl.Group = TW_Bar; Tl.Bld = BI; TownWorks.Add(Tl); }
			}
		break;
	}
	case TK_Witch: FurnRoom = RI; AddPieceAt(TEXT("Cauldron"), Ctr, 0.f); FurnRoom = -1; break;
	// (the port's sluice house: the sewer's mouth at its far wall (RDPort.cpp))
	case TK_SluiceHouse: SewerGateBuild(BI); break;
	case TK_Cathedral:
	{
		// (the holy city's cathedral, after its rooms' own furnishing: pews down the nave either side of its aisle, facing the
		// choir; the high altar in the choir before the stair down, candles on it. Each piece where it fits)
		if (B.Rooms.Num() < 3) break;
		const int32 RN = B.Rooms[1];
		const FRoom& Nv = Rooms[RN];
		const FVector L0 = TileWorld(Nv.Lane);
		float A0 = MAX_flt, A1 = -MAX_flt;
		for (const FIntPoint& Cn : { Nv.Min, Nv.Max - FIntPoint(1, 1) }) { const float A = FVector::DotProduct(TileWorld(Cn) - L0, In_); A0 = FMath::Min(A0, A); A1 = FMath::Max(A1, A); }
		const float PewYaw = In_.Rotation().Yaw;
		int32 Pews = 0;
		FurnRoom = RN;
		for (float A = A0 + 300.f; A <= A1 - 300.f; A += 230.f)
			for (const float Sd : { -1.f, 1.f })
			{
				const FVector P = L0 + In_ * A + Along * Sd * 450.f;
				if (AddPieceAt(TEXT("Cathedral.Pew"), P, PewYaw)) { MarkBlocked(P, PewYaw, FVector2D(110.f, 480.f), true); ++Pews; }
			}
		FurnRoom = -1;
		if (!MistgateAt.IsZero())
		{
			const FVector Altar = MistgateAt + MistgateNormal * 780.f;
			FurnRoom = B.Rooms[2];
			if (AddPieceAt(TEXT("Cathedral.Altar"), Altar, (-MistgateNormal).Rotation().Yaw))
			{
				MarkBlocked(Altar, MistgateNormal.Rotation().Yaw, FVector2D(200.f, 360.f), true);
				const FRDPiece* Ap = Generator->Piece(TEXT("Cathedral.Altar"));
				const float Az = Ap ? (float)Ap->Size.Z : 110.f;
				for (int32 K = -1; K <= 1; K += 2) AddEffect(TEXT("CandleFire"), Altar + FVector(MistgateNormal.Y, -MistgateNormal.X, 0.f) * (K * 110.f) + FVector(0, 0, Az + 10.f), 1.f);
				AddLight(Altar + FVector(0, 0, Az + 120.f), FLinearColor(1.f, 0.7f, 0.42f), 180.f, 900.f, false, 0.10f);
			}
			FurnRoom = -1;
		}
		UE_LOG(LogRDTown, Log, TEXT("RDHOLY the cathedral furnished: %d pews"), Pews);
		break;
	}
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
		const FRDPiece* Wp = Generator->Piece(TEXT("Town.CityWall"));
		const float Wh = Wp ? Wp->Size.Z - 4.f : 300.f, Wl = Wp ? FMath::Max((float)Wp->Size.Y, 100.f) : 300.f;
		const float Z0 = GetActorLocation().Z;
		// the wall along the outline's edges (since 2026-11-02: it follows the town's shape), each edge's pieces stretched to
		// fill it, none in the gate's gap or inside a tower; facing in, toward the outline's middle
		FVector2D Mid2 = FVector2D::ZeroVector;
		for (const FVector2D& P : TownBorder) Mid2 += P;
		Mid2 /= FMath::Max(1, TownBorder.Num());
		for (int32 I = 0, J = TownBorder.Num() - 1; I < TownBorder.Num(); J = I++)
		{
			const FVector2D A = TownBorder[J], B = TownBorder[I];
			const float Le = FVector2D::Distance(A, B);
			if (Le < 10.f) continue;
			const FVector2D Dir = (B - A) / Le;
			FVector2D Nin(-Dir.Y, Dir.X);
			if (FVector2D::DotProduct(Mid2 - (A + B) * 0.5f, Nin) < 0.f) Nin = -Nin;
			const float InYaw = FMath::RadiansToDegrees(FMath::Atan2(Nin.Y, Nin.X));
			// (the user's list of 2026-11-04: "there are gaps on either side of" the portcullis: the gate's edge was laid in 3 m
			// pieces and every one whose middle was within 1.6 m of the gate left out, a 6 m hole for a 4 m portcullis. The edge
			// with the gate is laid in two runs, each stretched to meet the portcullis's sides)
			const float GHalf = 202.f;
			TArray<FVector2D, TInlineAllocator<2>> Runs;
			{
				double Tg = 0.0;
				const double Dg = FMath::PointDistToSegment(FVector(TownGate.X, TownGate.Y, 0), FVector(A, 0.f), FVector(B, 0.f));
				Tg = FVector2D::DotProduct(FVector2D(TownGate.X, TownGate.Y) - A, Dir);
				if (Dg < 120.0 && Tg > GHalf && Tg < Le - GHalf) { Runs.Add(FVector2D(0.f, (float)Tg - GHalf)); Runs.Add(FVector2D((float)Tg + GHalf, Le)); }
				else Runs.Add(FVector2D(0.f, Le));
			}
			for (const FVector2D& Run : Runs)
			{
				const float RunL = Run.Y - Run.X;
				if (RunL < 20.f) continue;
				const int32 Np = FMath::Max(1, FMath::RoundToInt(RunL / Wl));
				const float Seg = RunL / Np;
				for (int32 K = 0; K < Np; ++K)
				{
					const FVector2D P2 = A + Dir * (Run.X + Seg * (K + 0.5f));
					const FVector P(P2.X, P2.Y, Z0);
					bool bInTower = false;
					for (const FTownSpot& Sp : TownSpots) if (Sp.Kind == TS_Tower && FVector::Dist2D(Sp.At, P) < 300.f + Seg * 0.5f - 40.f) { bInTower = true; break; }
					if (bInTower) continue;                                           // (the tower's own faces close it)
					// (a wall piece runs along its +Y, its face toward +X: the parapet's the same; plain stone below, an arrow slit in
					// one upper segment of three, by a hash of the place: until 2026-11-02 every piece was one with an arched doorway)
					const uint32 Hh = HashCombine(GetTypeHash(FIntPoint(FMath::RoundToInt(P.X), FMath::RoundToInt(P.Y))), 0x5117u);
					const FVector Sc(1.f, (Seg + 12.f) / Wl, 1.f);
					AddPiece(TEXT("Town.CityWall"), FTransform(FRotator(0, InYaw, 0), P, Sc));
					AddPiece(Hh % 3 == 0 && Generator->Piece(TEXT("Town.CityWallSlit")) ? FName(TEXT("Town.CityWallSlit")) : FName(TEXT("Town.CityWall")), FTransform(FRotator(0, InYaw, 0), P + FVector(0, 0, Wh), Sc));
					AddPiece(TEXT("Town.Parapet"), FTransform(FRotator(0, InYaw, 0), P + FVector(0, 0, 2 * Wh), Sc), true);
				}
			}
			// (over the portcullis: the wall's upper part and its parapet across the gate, the portcullis rising into it)
			if (Runs.Num() == 2 && Generator->bWild)
			{
				const FVector2D Pg2 = A + Dir * ((Runs[0].Y + Runs[1].X) * 0.5f);
				const FVector Pg3(Pg2.X, Pg2.Y, Z0);
				const float Lz = 530.f, Hz = FMath::Max(2.f * Wh - Lz, 20.f);
				const FVector Sc(1.f, (2.f * GHalf + 14.f) / Wl, Hz / FMath::Max(Wh + 4.f, 1.f));
				AddPiece(TEXT("Town.CityWall"), FTransform(FRotator(0, InYaw, 0), Pg3 + FVector(0, 0, Lz), Sc));
				AddPiece(TEXT("Town.Parapet"), FTransform(FRotator(0, InYaw, 0), Pg3 + FVector(0, 0, 2 * Wh), FVector(1.f, (2.f * GHalf + 14.f) / Wl, 1.f)), true);
			}
		}
		// the gate: its frame across the gap, two leaves shut, a beam barring them, a blocker; open (frame only) when the
		// wilderness is beyond it (the user's spec of 2026-11-03)
		const float GYaw = TownGateOut.Rotation().Yaw;
		// (its pieces run across the gap along their +Y, their faces outward; with the wilderness beyond it (the list of
		// 2026-11-04: "the portcullis ... can be walked through ... there should be a way to open the portcullis like a lever")
		// the portcullis is a door that lifts, with a lever on each side of the gate)
		if (Generator->bWild) TownGateWorks();
		else AddPieceAt(TEXT("Town.Gate"), TownGate, GYaw, 1.f, true);
		if (!Generator->bWild)
		{
			AddPieceAt(TEXT("Town.GateLeaves"), TownGate - TownGateOut * 20.f, GYaw, 1.f, true);
			AddPieceAt(TEXT("Town.GateBar"), TownGate - TownGateOut * 45.f + FVector(0, 0, 150.f), GYaw, 1.f, true);
		}
		if (bBuildStatic && !Generator->bWild)
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
			// parapets round its top. Since 2026-11-02 it is walked into from the town (the user's: "there's no way to get into
			// the watchtowers from the inside of town"): an arched door in its face toward the town, a spiral stair up to a
			// landing under its roof, which stands on four posts over the parapet)
			const FVector ToTown = FVector(Mid2.X - Sp.At.X, Mid2.Y - Sp.At.Y, 0.f).GetSafeNormal();
			int32 DoorK = 0; float BestDot = -2.f;
			for (int32 K = 0; K < 4; ++K)
			{
				const FVector Outw = FRotator(0, 90.f * K, 0).RotateVector(FVector(-1.f, 0, 0));
				if (FVector::DotProduct(Outw, ToTown) > BestDot) { BestDot = FVector::DotProduct(Outw, ToTown); DoorK = K; }
			}
			const bool bStairs = Generator->Piece(TEXT("Town.Spiral")) && Generator->Piece(TEXT("Town.CityWallDoor"));
			for (int32 K = 0; K < 4; ++K)
			{
				const float Yw = 90.f * K;
				const FRotator Rt(0, Yw, 0);
				for (int32 Sg = -1; Sg <= 1; Sg += 2)
				{
					const FVector Fc = Sp.At + Rt.RotateVector(FVector(-300.f, 150.f * Sg, 0));
					// (plain below, an arrow slit, a small window at the top; the door: the town face's +Y segment's foot)
					for (int32 H = 0; H < 3; ++H)
					{
						FName Nm(TEXT("Town.CityWall"));
						if (H == 1 && Sg < 0 && Generator->Piece(TEXT("Town.CityWallSlit"))) Nm = TEXT("Town.CityWallSlit");
						if (H == 2 && Sg > 0 && Generator->Piece(TEXT("Town.CityWallWin"))) Nm = TEXT("Town.CityWallWin");
						if (bStairs && H == 0 && K == DoorK && Sg > 0)
						{
							// (the doorway's own collision closes its foot, as the castle's towers' did: none on the piece, boxes
							// beside the opening (112 cm wide, 240 high, centred) and over it)
							AddPieceAt(TEXT("Town.CityWallDoor"), Fc, Yw + 180.f, 1.f, true);
							const FRotator Ry(0, Yw + 180.f, 0);
							for (int32 Sd = -1; Sd <= 1; Sd += 2)
								AddPiece(TEXT("Town.Collider"), FTransform(Ry, Fc + Ry.RotateVector(FVector(0, Sd * 105.f, 0)), FVector(1.15f, 0.98f, Wh / 100.f)));
							AddPiece(TEXT("Town.Collider"), FTransform(Ry, Fc + FVector(0, 0, 245.f), FVector(1.15f, 1.12f, (Wh - 245.f) / 100.f)));
							continue;
						}
						// (a little taller than its storey: set edge to edge, the torch inside lit the seams)
						AddPiece(Nm, FTransform(FRotator(0, Yw + 180.f, 0), Fc + FVector(0, 0, H * Wh), FVector(1.f, 1.f, 1.04f)));
					}
					AddPieceAt(TEXT("Town.Parapet"), Fc + FVector(0, 0, 3 * Wh), Yw + 180.f, 1.f, true);
				}
			}
			const float Top = 3 * Wh;
			if (bStairs)
			{
				// the spiral: twelve quarter turns climbing clockwise from just past the door to the top; a landing over the
				// quarter it ends beside (the quarters before it pass under that landing 2.3 m lower: room for her head)
				const FVector DoorAt = Sp.At + FRotator(0, 90.f * DoorK, 0).RotateVector(FVector(-300.f, 150.f, 0));
				const float Sa = FMath::RadiansToDegrees(FMath::Atan2(DoorAt.Y - Sp.At.Y, DoorAt.X - Sp.At.X)) - 22.f;
				TownTowerDoors.Add(FVector(DoorAt.X, DoorAt.Y, Sa)); TownTowerMids.Add(Sp.At);
				const FRDPiece* Spp = Generator->Piece(TEXT("Town.Spiral"));
				const float SpZ = FMath::Max((float)Spp->Size.Z, 50.f), Qn = 12.f, Qh = Top / Qn;
				for (int32 K = 0; K < (int32)Qn; ++K)
					AddPiece(TEXT("Town.Spiral"), FTransform(FRotator(0, Sa - 90.f * K, 0), Sp.At + FVector(0, 0, Qh * K), FVector(1.f, 1.f, Qh / SpZ)));
				if (const FRDPiece* Rf = Generator->Piece(TEXT("Town.CastleRoof")))
				{
					// the floor at the top (the third list of 2026-11-02: "the circular stairway just ends, there is no
					// platform or floor"): stone over the whole tower but the stairwell, the circle the steps turn in (2.15 m
					// from the post) over its last three quarter turns, where she needs the room for her head; the quarter she
					// steps off onto is floored (the landing). A metre-high balustrade round the stairwell's open part and along
					// the landing's edge over it.
					const float RfX = FMath::Max((float)Rf->Size.X, 50.f), Fz = Top - Rf->Size.Z, Rw = 215.f, In = 280.f;
					auto Plate = [&](float X0, float Y0, float X1, float Y1, float Yw)
					{
						const FRotator Ry(0, Yw, 0);
						AddPiece(TEXT("Town.CastleRoof"), FTransform(Ry, Sp.At + Ry.RotateVector(FVector((X0 + X1) * 0.5f, (Y0 + Y1) * 0.5f, 0.f)) + FVector(0, 0, Fz),
							FVector((X1 - X0) / RfX, (Y1 - Y0) / RfX, 1.f)));
					};
					// (outside the circle: a strip along each wall and the corners)
					for (int32 K = 0; K < 4; ++K) Plate(Rw, -In, In, In, 90.f * K);
					for (int32 K = 0; K < 4; ++K) Plate(150.f, 150.f, In, In, 90.f * K);
					// (the landing: the quadrant from the post between Sa - 90 and Sa)
					Plate(0.f, -Rw, Rw, 0.f, Sa);
					// (the balustrade: segments round the circle from Sa to Sa + 270 and along the landing's edge at Sa - 90)
					const FRDPiece* Cw = Generator->Piece(TEXT("Town.CWall"));
					if (Cw)
					{
						const float Th = FMath::Max((float)Cw->Size.X, 40.f), Ln = FMath::Max((float)Cw->Size.Y, 100.f), Hh = FMath::Max((float)Cw->Size.Z, 100.f);
						const float Rr = Rw + 12.f;
						for (int32 J = 0; J < 9; ++J)
						{
							const float A0 = Sa + 30.f * J + 4.f, A1 = Sa + 30.f * (J + 1);
							const FVector P0 = Sp.At + FRotator(0, A0, 0).RotateVector(FVector(Rr, 0, 0)), P1 = Sp.At + FRotator(0, A1, 0).RotateVector(FVector(Rr, 0, 0));
							const FVector D = P1 - P0;
							AddPiece(TEXT("Town.CWall"), FTransform(FRotator(0, D.Rotation().Yaw - 90.f, 0), (P0 + P1) * 0.5f + FVector(0, 0, Top), FVector(22.f / Th, (D.Size2D() + 14.f) / Ln, 100.f / Hh)));
						}
						const FVector E1 = Sp.At + FRotator(0, Sa - 90.f, 0).RotateVector(FVector(Rr, 0, 0));
						AddPiece(TEXT("Town.CWall"), FTransform(FRotator(0, Sa - 90.f - 90.f, 0), (Sp.At + E1) * 0.5f + FVector(0, 0, Top), FVector(22.f / Th, Rr / Ln, 100.f / Hh)));
					}
				}
				// (the roof on four posts at the parapet's corners, over the landing)
				for (int32 K = 0; K < 4; ++K)
					AddPieceAt(TEXT("Town.CircleStone"), Sp.At + FRotator(0, 45.f + 90.f * K, 0).RotateVector(FVector(300.f, 0, 0)) + FVector(0, 0, Top), 0.f, 1.f);
				AddPieceAt(TEXT("Town.TowerRoof"), Sp.At + FVector(0, 0, Top + 270.f), 0.f, 1.f, true);
				// (a torch inside, by the door)
				AddTorch(Sp.At + FRotator(0, 90.f * DoorK + 60.f, 0).RotateVector(FVector(-240.f, 0, 0)) + FVector(0, 0, 260.f), 90.f * DoorK + 60.f, 90.f);
			}
			else AddPieceAt(TEXT("Town.TowerRoof"), Sp.At + FVector(0, 0, Top + 20.f), 0.f, 1.f, true);
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
		// ---- the port's harbour: its water, its quay's wall, the blockers along its edges (RDPort.cpp)
		HarbourBuild();
		// ---- the square: the well, the quest board, the stalls, the lamps; the teleport circle's stones
		for (const FTownSpot& Sp : TownSpots)
		{
			switch (Sp.Kind)
			{
			case TS_Well: AddPieceAt(TEXT("Town.Well"), Sp.At, Sp.Yaw); AddPieceAt(TEXT("Town.WellTop"), Sp.At, Sp.Yaw); break;
			case TS_Board:
			{
				AddPieceAt(TEXT("Town.Board"), Sp.At, Sp.Yaw); AddPieceAt(TEXT("Town.BoardNotes"), Sp.At, Sp.Yaw, 1.f, true);
				// (its papers: a notice for each of the three bounties and an older one, pinned to each of its faces (it stands
				// in the square, read from both sides), a little askew (the user's of 2026-11-02: the board had no papers))
				const FVector Pins[4] = { FVector(11.5f, -62.f, 150.f), FVector(11.8f, 2.f, 128.f), FVector(11.5f, 64.f, 152.f), FVector(11.2f, -28.f, 88.f) };
				const float Tilt[4] = { -4.f, 3.f, -2.f, 7.f };
				for (int32 Face = 0; Face < 2; ++Face)
				{
					const FRotator Ry(0, Sp.Yaw + Face * 180.f, 0);
					for (int32 K = 0; K < 4; ++K) AddPiece(TEXT("Town.Notice"), FTransform(Ry + FRotator(0, 0, Tilt[K]), Sp.At + Ry.RotateVector(Pins[K])), true);
				}
				break;
			}
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
			case TS_Mill:
				// (the list of 2026-11-04: "the windmill is embedded in the ground while the arms of the windmill turns, hitting
				// into the ground": the pack's BP_windmill is its sails, shaft and millstones only, its root at the hub (the stones
				// 14 m under it); it stood on the ground with no mill round it. Now the pack's mill house, the sails where the
				// pack's own level puts them on it: (23, 318, 1526) in the house's frame, turned half round)
				if (Generator->Piece(TEXT("Town.MillHouse")))
				{
					AddPieceAt(TEXT("Town.MillHouse"), Sp.At, Sp.Yaw);
					AddPieceAt(TEXT("Town.Mill"), Sp.At + FRotator(0, Sp.Yaw, 0).RotateVector(FVector(23.f, 318.f, 1526.f)), Sp.Yaw + 180.f);
				}
				else AddPieceAt(TEXT("Town.Mill"), Sp.At, Sp.Yaw);
				break;
			case TS_Tent: AddPieceAt(TEXT("Town.Tent"), Sp.At, Sp.Yaw); AddPieceAt(TEXT("Town.Firepit"), Sp.At + FRotator(0, Sp.Yaw, 0).RotateVector(FVector(330.f, 0, 0)), 0.f); break;
			// (the holy city's: a statue on its plinth, the plaza's fountain, a wayside shrine with its candles)
			case TS_Statue:
			{
				// (on its plinth, standing on the plinth's top)
				const FRDPiece* Pl = Generator->Piece(TEXT("Holy.StatuePlinth"));
				AddPieceAt(TEXT("Holy.StatuePlinth"), Sp.At, Sp.Yaw);
				AddPieceAt(FName(*FString::Printf(TEXT("Holy.Statue%d"), 1 + R.RandRange(0, 2))), Sp.At + FVector(0, 0, Pl ? (float)Pl->Size.Z - 2.f : 120.f), Sp.Yaw);
				break;
			}
			case TS_Fountain: AddPieceAt(TEXT("Holy.Fountain"), Sp.At, Sp.Yaw); break;
			case TS_Shrine:
				AddPieceAt(TEXT("Holy.Shrine"), Sp.At, Sp.Yaw);
				AddEffect(TEXT("CandleFire"), Sp.At + FRotator(0, Sp.Yaw, 0).RotateVector(FVector(40.f, 0, 120.f)), 1.f);
				break;
			// (the forge city's (2026-11-07, RDForge.cpp): the guild's great anvil on its plinth, an open forge with its anvil, fire,
			// sparks and smoke and the work at it, an ore cart on its rails, a stretch of the barricade)
			case TS_Anvil: ForgeAnvilBuild(Sp); break;
			case TS_Forge: OpenForgeBuild(Sp); break;
			case TS_Cart: OreCartBuild(Sp); break;
			case TS_Barricade: BarricadeBuild(Sp); break;
			// (the port's harbour (2026-11-07, RDPort.cpp): piers, ships, boats, wrecks, the drowned dead, gibbets, dock props)
			case TS_Pier: case TS_Ship: case TS_Boat: case TS_Wreck: case TS_Body: case TS_Gibbet: case TS_DockProps: PortSpotBuild(Sp); break;
			default: break;
			}
			if (Sp.Kind == TS_Gibbet || Sp.Kind == TS_DockProps) MarkBlocked(Sp.At, Sp.Yaw, FVector2D(260.f, Sp.Kind == TS_DockProps ? 900.f : 260.f), true);
			// (what stands outdoors blocks the tiles under it for whoever walks the paths)
			if (Sp.Kind == TS_Well || Sp.Kind == TS_Board || Sp.Kind == TS_Stall || Sp.Kind == TS_Still || Sp.Kind == TS_Tent || Sp.Kind == TS_Statue || Sp.Kind == TS_Shrine
				|| Sp.Kind == TS_Anvil || Sp.Kind == TS_Forge)
				MarkBlocked(Sp.At, Sp.Yaw, FVector2D(260.f, 260.f), true);
			if (Sp.Kind == TS_Cart) MarkBlocked(Sp.At, Sp.Yaw, FVector2D(320.f, 160.f), true);
			if (Sp.Kind == TS_Barricade) MarkBlocked(Sp.At, Sp.Yaw, FVector2D(140.f, 330.f), true);
			if (Sp.Kind == TS_Fountain) MarkBlocked(Sp.At, 0.f, FVector2D(600.f, 600.f), true);
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
		// ---- the town's life (the third list): gardens, pens, cooking fires by the homes; before the trees, which keep off them
		TownLife(R);
		break;
	case 5:
	{
		// (the list of 2026-11-04: the open ground rises and falls; what is placed from here on stands on it)
		TownLiftPlan();
		bTownLiftOn = true;
		// ---- trees and bushes on the free ground away from the roads (never on a road, a doorway's front or the square)
		TArray<uint8> Road; Road.Init(0, N * N);
		for (const FIntRect& Rr : TownRoads) for (int32 X = Rr.Min.X; X < Rr.Max.X; ++X) for (int32 Y = Rr.Min.Y; Y < Rr.Max.Y; ++Y) if (In(FIntPoint(X, Y))) Road[Idx(FIntPoint(X, Y))] = 1;
		for (int32 X = TownSquare.Min.X; X < TownSquare.Max.X; ++X) for (int32 Y = TownSquare.Min.Y; Y < TownSquare.Max.Y; ++Y) Road[Idx(FIntPoint(X, Y))] = 1;
		// (the earth roads and the lane too)
		for (int32 I = 0; I < TownRoadMask.Num() && I < Road.Num(); ++I) if (TownRoadMask[I]) Road[I] = 1;
		for (int32 K = 0; K < 1800; ++K)
		{
			const FIntPoint T(R.RandRange(0, N - 1), R.RandRange(0, N - 1));
			const bool bInside = In(T) && Type[Idx(T)] == 2;
			// (outside the wall's outline, clear of the wall: the outline leaves room all round since 2026-11-02)
			const FVector Tw = TileWorld(T);
			const bool bOutside = In(T) && Type[Idx(T)] == 0 && !InsideTownBorder(FVector2D(Tw.X, Tw.Y)) && TownBorderDist(FVector2D(Tw.X, Tw.Y)) > 2.5f * M;
			if (!bInside && !bOutside) continue;
			if (TownHarbour.Area() > 0 && TownHarbour.Contains(T)) continue;
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
		bTownLiftOn = false;
		break;
	}
	case 6:
		// ---- the short grass and the small bushes (the third list: "short grass in more places where there aren't any roads,
		// more small bushes")
		if (TownLiftW.Num() == 0) TownLiftPlan();
		bTownLiftOn = true;
		TownGrass(R);
		bTownLiftOn = false;
		break;
	case 7:
		// ---- the ground itself
		if (TownLiftW.Num() == 0) TownLiftPlan();
		bTownLiftOn = false;
		TownGround();
		break;
	default: break;
	}
	(void)R0;
}

// ------------------------------------------------------------------------------------------------ the town's life (third list)
void ARDSection::TownLife(FRandomStream& R)
{
	// (the user's of 2026-11-02, the third list: "the town should look more lively. ... small gardens with plants. ... small
	// animals like chickens, rabbits, goats, cows and pigs in pens, cooking fires with pots on them being tended by a villager,
	// cooking fires with meat on spits being turned by a villager". By the lived-in homes, in a shuffled order: a garden (a
	// low fence with a way in, rows of plants), a pen (a fence all round, a trough and hay; its animals are play's), a cooking
	// fire (a fire pit with a pot on a tripod, or a spit on two posts). Each leaves a place of work (TownWorks) where a
	// townsperson stands to do it, outside the thing worked, on walkable ground. Also the well's, the stalls' and the refugees'
	// camp's places.)
	const float M = Generator->TileSize;
	auto Reach = [&](const TCHAR* Kind, float Def) { const float* V = Generator->TownWorkReach.Find(FName(Kind)); return V ? *V : Def; };
	auto Work = [&](const TCHAR* Kind, const FVector& At, float Yaw, uint8 Group, int32 Bld, const TCHAR* Prop = nullptr, int32 Thing = -1)
	{
		FTownWork W; W.Kind = Kind; W.At = At; W.Yaw = Yaw; W.Group = Group; W.Bld = Bld; W.Prop = Prop ? FName(Prop) : NAME_None; W.Thing = Thing;
		TownWorks.Add(W);
	};
	TArray<uint8> Road; Road.Init(0, N * N);
	for (const FIntRect& Rr : TownRoads) for (int32 X = Rr.Min.X; X < Rr.Max.X; ++X) for (int32 Y = Rr.Min.Y; Y < Rr.Max.Y; ++Y) if (In(FIntPoint(X, Y))) Road[Idx(FIntPoint(X, Y))] = 1;
	for (int32 X = TownSquare.Min.X; X < TownSquare.Max.X; ++X) for (int32 Y = TownSquare.Min.Y; Y < TownSquare.Max.Y; ++Y) if (In(FIntPoint(X, Y))) Road[Idx(FIntPoint(X, Y))] = 1;
	for (int32 I = 0; I < TownRoadMask.Num() && I < Road.Num(); ++I) if (TownRoadMask[I]) Road[I] = 1;
	TSet<FIntPoint> DoorFront;
	for (const FTownBld& B : TownBlds) for (int32 K = 1; K <= 2; ++K) DoorFront.Add(B.DoorTile + RDTDir4[B.DoorSide] * K);
	auto TileOk = [&](const FIntPoint& T) { return In(T) && Type[Idx(T)] == 2 && !Road[Idx(T)] && !Blocked[Idx(T)] && !DoorFront.Contains(T); };
	auto Walkable = [&](const FIntPoint& T) { return In(T) && Type[Idx(T)] == 2 && !Blocked[Idx(T)]; };
	auto RectOk = [&](const FIntPoint& T0, int32 W, int32 H)
	{
		for (int32 X = 0; X < W; ++X) for (int32 Y = 0; Y < H; ++Y) if (!TileOk(T0 + FIntPoint(X, Y))) return false;
		return true;
	};
	// (a W x H rectangle of tiles beside a building: within three tiles of its walls, a tile from them)
	auto FindBy = [&](const FTownBld& B, int32 W, int32 H, FIntPoint& Out, int32& Ow, int32& Oh)
	{
		TArray<FIntVector> Cands;
		for (int32 Rot = 0; Rot < 2; ++Rot)
		{
			const int32 w = Rot ? H : W, h = Rot ? W : H;
			for (int32 X = B.Min.X - 3 - w; X <= B.Max.X + 3; ++X)
				for (int32 Y = B.Min.Y - 3 - h; Y <= B.Max.Y + 3; ++Y)
				{
					// (not on the building's tiles or its margin)
					if (X < B.Max.X + 1 && X + w > B.Min.X - 1 && Y < B.Max.Y + 1 && Y + h > B.Min.Y - 1) continue;
					if (RectOk(FIntPoint(X, Y), w, h)) Cands.Add(FIntVector(X, Y, Rot));
				}
		}
		if (Cands.Num() == 0) return false;
		const FIntVector C = Cands[R.RandRange(0, Cands.Num() - 1)];
		Out = FIntPoint(C.X, C.Y); Ow = C.Z ? H : W; Oh = C.Z ? W : H;
		return true;
	};
	auto RectWorld = [&](const FIntPoint& T0, int32 W, int32 H, FVector& Ctr, FVector2D& Half)
	{
		const FVector A = TileWorld(T0), B = TileWorld(T0 + FIntPoint(W - 1, H - 1));
		Ctr = (A + B) * 0.5f; Half = FVector2D(FMath::Abs(B.X - A.X) + M, FMath::Abs(B.Y - A.Y) + M) * 0.5f;
	};
	// (a fence along a world rectangle's edges (axis aligned), with a gap of GapW in the middle of edge GapSide (-1 none): 0 -X, 1
	// +X, 2 -Y, 3 +Y)
	auto FenceRect = [&](const FVector& C, const FVector2D& H, FName Piece, int32 GapSide, float GapW, bool bGate)
	{
		const FRDPiece* Fp = Generator->Piece(Piece);
		if (!Fp) return;
		const float Fl = FMath::Max((float)Fp->Size.Y, 60.f);
		const FVector2D Cn[4] = { FVector2D(C.X - H.X, C.Y - H.Y), FVector2D(C.X + H.X, C.Y - H.Y), FVector2D(C.X + H.X, C.Y + H.Y), FVector2D(C.X - H.X, C.Y + H.Y) };
		// (edges in order: -Y (side 2), +X (1), +Y (3), -X (0))
		const int32 SideOf[4] = { 2, 1, 3, 0 };
		for (int32 K = 0; K < 4; ++K)
		{
			const FVector2D P0 = Cn[K], P1 = Cn[(K + 1) % 4];
			const FVector2D D = (P1 - P0).GetSafeNormal();
			const float Len = FVector2D::Distance(P0, P1);
			const int32 Nseg = FMath::Max(1, FMath::RoundToInt(Len / Fl));
			const float Sl = Len / Nseg;
			const float FYaw = FMath::RadiansToDegrees(FMath::Atan2(D.Y, D.X)) - 90.f;
			float Gu0 = 1e9f, Gu1 = -1e9f;
			for (int32 J = 0; J < Nseg; ++J)
			{
				const float U = (J + 0.5f) * Sl;
				if (SideOf[K] == GapSide && FMath::Abs(U - Len * 0.5f) < GapW * 0.5f + Sl * 0.25f) { Gu0 = FMath::Min(Gu0, U - Sl * 0.5f); Gu1 = FMath::Max(Gu1, U + Sl * 0.5f); continue; }
				const FVector2D Q = P0 + D * U;
				AddPiece(Piece, FTransform(FRotator(0, FYaw, 0), FVector(Q.X, Q.Y, C.Z), FVector(1.f, Sl / Fl * 1.02f, 1.f)));
			}
			// (the list of 2026-11-04: "there should be a door for the animal pens that can be opened and closed": the gap's
			// fence segment on a hinge at its end)
			if (bGate && Gu1 > Gu0)
			{
				const FVector2D Hg = P0 + D * Gu0;
				TownPenGate(FVector(Hg.X, Hg.Y, C.Z), FYaw, Gu1 - Gu0);
			}
		}
	};
	auto BlockRect = [&](const FIntPoint& T0, int32 W, int32 H) { for (int32 X = 0; X < W; ++X) for (int32 Y = 0; Y < H; ++Y) if (In(T0 + FIntPoint(X, Y))) Blocked[Idx(T0 + FIntPoint(X, Y))] = 1; };
	// (the side of a rectangle whose outside is walkable, nearest the building: the way in)
	auto WaySide = [&](const FIntPoint& T0, int32 W, int32 H, const FTownBld& B) -> int32
	{
		const FVector2D Bc((B.Min.X + B.Max.X) * 0.5f, (B.Min.Y + B.Max.Y) * 0.5f), Rc(T0.X + W * 0.5f, T0.Y + H * 0.5f);
		int32 Best = -1; float Bd = MAX_flt;
		for (int32 Sd = 0; Sd < 4; ++Sd)
		{
			const FIntPoint Mid = Sd == 0 ? FIntPoint(T0.X - 1, T0.Y + H / 2) : Sd == 1 ? FIntPoint(T0.X + W, T0.Y + H / 2) : Sd == 2 ? FIntPoint(T0.X + W / 2, T0.Y - 1) : FIntPoint(T0.X + W / 2, T0.Y + H);
			if (!Walkable(Mid)) continue;
			const float D = FVector2D::Distance(FVector2D(Mid.X + 0.5f, Mid.Y + 0.5f), Bc);
			if (D < Bd) { Bd = D; Best = Sd; }
		}
		return Best;
	};
	auto SideDir = [](int32 Sd) { return FVector(RDTDir4[Sd].X, RDTDir4[Sd].Y, 0.f); };
	const int32 NAnimals = Generator->TownAnimals.Num();
	int32 Gardens = 0, Pens = 0, Pots = 0, Spits = 0;
	TArray<int32> Order;
	for (int32 BI = 0; BI < TownBlds.Num(); ++BI) if (TownBlds[BI].Kind == TK_Home && TownBlds[BI].State == 0) Order.Add(BI);
	for (int32 I = Order.Num() - 1; I > 0; --I) Order.Swap(I, R.RandRange(0, I));
	static const TCHAR* Crops[] = { TEXT("Town.Crop1"), TEXT("Town.Crop2"), TEXT("Town.Crop3"), TEXT("Town.Crop4"), TEXT("Town.Crop5"), TEXT("Town.Crop6") };
	for (const int32 BI : Order)
	{
		const FTownBld& B = TownBlds[BI];
		int32 Made = 0;
		// ---- a garden: 2 x 1 or 2 x 2 tiles, a low fence with a way in on the side toward the house, rows of plants (three or
		// four kinds), the place to tend it just inside the way in
		if (Gardens < 18 && R.FRand() < 0.5f)
		{
			FIntPoint T0; int32 W = 2, H = R.RandBool() ? 1 : 2, Ow, Oh;
			if (FindBy(B, W, H, T0, Ow, Oh))
			{
				const int32 Ws = WaySide(T0, Ow, Oh, B);
				if (Ws >= 0)
				{
					FVector C; FVector2D Hf; RectWorld(T0, Ow, Oh, C, Hf);
					const FVector2D Bed = Hf - FVector2D(25.f, 25.f);
					FenceRect(C, Bed, TEXT("Town.GardenFence"), Ws, 150.f, false);
					const FVector In_ = -SideDir(Ws), Al(In_.Y, -In_.X, 0.f);
					const float Depth = (Ws < 2 ? Bed.X : Bed.Y) * 2.f, Width = (Ws < 2 ? Bed.Y : Bed.X) * 2.f;
					const FVector Edge = C - In_ * (Depth * 0.5f);
					// (rows across the way in: from 95 cm in, every 60 cm, the back row the tall plants (sunflowers))
					const int32 K1 = R.RandRange(0, 5), K2 = R.RandRange(0, 5), K3 = R.RandRange(0, 5);
					int32 Plants = 0;
					for (float Dp = 95.f; Dp < Depth - 30.f; Dp += 60.f)
					{
						const int32 Rn = (int32)((Dp - 95.f) / 60.f);
						const int32 RowK = Dp > Depth - 90.f && Depth > 300.f ? 3 : (Rn % 3 == 0 ? K1 : Rn % 3 == 1 ? K2 : K3);
						for (float Wd = -Width * 0.5f + 35.f; Wd < Width * 0.5f - 25.f; Wd += 48.f)
						{
							const FVector P = Edge + In_ * Dp + Al * Wd + FVector(R.FRandRange(-8.f, 8.f), R.FRandRange(-8.f, 8.f), 0.f);
							AddPiece(Crops[RowK], FTransform(FRotator(0, R.FRandRange(0.f, 360.f), 0), P, FVector(R.FRandRange(0.85f, 1.15f))), true);
							++Plants;
						}
					}
					FTownGarden Gd; Gd.At = C; Gd.Half = Bed; Gd.Yaw = 0.f; Gd.Plants = Plants;
					// (what grows in it: harvested with F (the list of 2026-11-04: "gardens can be lootable with ingredients"))
					for (const int32 Kc : { K1, K2, K3 }) Gd.Crops.AddUnique((uint8)Kc);
					if (Depth > 300.f) Gd.Crops.AddUnique(3);
					TownGardens.Add(Gd);
					BlockRect(T0, Ow, Oh);
					// (kneeling on the path just inside the way in, the first row before her)
					Work(TEXT("Tend"), Edge + In_ * FMath::Max(15.f, 95.f - Reach(TEXT("Tend"), 45.f)), In_.Rotation().Yaw, TW_Garden, BI);
					++Gardens; ++Made;
				}
			}
		}
		// ---- a pen: 2 x 2 tiles (the hens, the rabbits, the goats, the pigs), 3 x 2 for the cows; a fence all round, a trough
		// along one side, hay in a corner; the animals' kinds in turn; the place to feed them outside the fence, toward the house
		if (Pens < 12 && NAnimals > 0 && Made < 2 && R.FRand() < 0.3f)
		{
			const int32 Kind = Pens % NAnimals;
			const bool bBig = Generator->TownAnimals[Kind].HalfSize.X > 80.f;
			FIntPoint T0; int32 Ow, Oh;
			if (FindBy(B, bBig ? 3 : 2, 2, T0, Ow, Oh))
			{
				const int32 Ws = WaySide(T0, Ow, Oh, B);
				if (Ws >= 0)
				{
					FVector C; FVector2D Hf; RectWorld(T0, Ow, Oh, C, Hf);
					const FVector2D In2 = Hf - FVector2D(30.f, 30.f);
					FenceRect(C, In2, TEXT("Town.PenFence"), Ws, 100.f, true);
					const FVector Out = SideDir(Ws), Al(Out.Y, -Out.X, 0.f);
					const float Half = Ws < 2 ? In2.X : In2.Y, HalfW = Ws < 2 ? In2.Y : In2.X;
					AddPieceAt(TEXT("Town.Trough"), C + Out * (Half - 60.f) + Al * (HalfW * 0.35f), Out.Rotation().Yaw + 90.f);
					AddPieceAt(TEXT("Town.HayPile"), C - Out * (Half - 70.f) - Al * (HalfW - 70.f), R.FRandRange(0.f, 360.f));
					FTownPen Pn; Pn.At = C; Pn.Half = In2 - FVector2D(20.f, 20.f); Pn.Yaw = 0.f; Pn.Animal = Kind;
					TownPens.Add(Pn);
					BlockRect(T0, Ow, Oh);
					Work(TEXT("Scatter"), C + Out * (Half + Reach(TEXT("Scatter"), 70.f)) - Al * (HalfW * 0.2f), (-Out).Rotation().Yaw, TW_Pen, BI, TEXT("Bowl"));
					++Pens; ++Made;
				}
			}
		}
		// ---- a cooking fire: two tiles, the fire on one, its cook on the other; a pot on a tripod, or a spit with its meat on
		// two posts (the rod and the meat are play's, turned while the crank is turned)
		if ((Pots < 8 || Spits < 6) && Made < 2 && R.FRand() < 0.32f)
		{
			FIntPoint T0; int32 Ow, Oh;
			if (FindBy(B, 2, 1, T0, Ow, Oh))
			{
				// (the fire on the tile nearer the house's door side is not wanted in its way: the farther one)
				const FIntPoint Ta = T0, Tb = T0 + (Ow == 2 ? FIntPoint(1, 0) : FIntPoint(0, 1));
				const FVector Pa = TileWorld(Ta), Pb = TileWorld(Tb);
				const FVector Dir = (Pb - Pa).GetSafeNormal2D(), Al(Dir.Y, -Dir.X, 0.f);
				const bool bPot = Spits >= 6 || (Pots < 8 && R.FRand() < 0.55f);
				AddPieceAt(Generator->Piece(TEXT("Town.Campfire")) ? FName(TEXT("Town.Campfire")) : FName(TEXT("Town.Firepit")), Pa, R.FRandRange(0.f, 360.f), 1.f, true);
				AddPieceAt(TEXT("Town.Firewood"), Pa + Al * 130.f, Dir.Rotation().Yaw + 90.f);
				AddEffect(TEXT("BrazierFire"), Pa + FVector(0, 0, 18.f), 0.7f);
				AddLight(Pa + FVector(0, 0, 70.f), FLinearColor(1.f, 0.52f, 0.22f), 120.f, 900.f, false, 0.25f);
				MarkBlocked(Pa, 0.f, FVector2D(150.f, 150.f), true);
				if (bPot)
				{
					AddPieceAt(TEXT("Town.Tripod"), Pa, Dir.Rotation().Yaw);
					AddPieceAt(TEXT("Town.Pot"), Pa + FVector(0, 0, Generator->TownPotHeight), Dir.Rotation().Yaw);
					Work(TEXT("Stir"), Pa + Dir * Reach(TEXT("Stir"), 70.f), (-Dir).Rotation().Yaw, TW_Pot, BI, TEXT("Ladle"));
					++Pots;
				}
				else
				{
					// (the rod along the two tiles' way, its posts at its ends; the cook at the end toward the second tile, facing
					// along it, the crank before her)
					for (int32 Sg = -1; Sg <= 1; Sg += 2) AddPieceAt(TEXT("Town.SpitPost"), Pa + Dir * (Sg * 95.f), Dir.Rotation().Yaw);
					TownSpits.Add(FVector4(Pa.X, Pa.Y, Pa.Z + Generator->TownSpitHeight, Dir.Rotation().Yaw));
					// (the Crank clip's hand goes round a circle 40 cm before her and 17 to her right: that circle on the rod's end)
					const FVector Fw = -Dir, Rt(-Fw.Y, Fw.X, 0.f);
					Work(TEXT("Crank"), Pa + Dir * 105.f - Fw * Reach(TEXT("Crank"), 40.f) - Rt * 17.f, Fw.Rotation().Yaw, TW_Spit, BI, nullptr, TownSpits.Num() - 1);
					++Spits;
				}
				++Made;
			}
		}
		// (a home with something to do by it has someone living in it: a resident by its door if the plan put none there)
		if (Made > 0 && !TownPosts.ContainsByPredicate([&](const FTownPost& P) { return P.Bld == BI && P.Role == ERDTownRole::Townsfolk; }))
		{
			const FVector In_ = -FVector(RDTDir4[B.DoorSide].X, RDTDir4[B.DoorSide].Y, 0.f);
			FTownPost P_; P_.Role = ERDTownRole::Townsfolk; P_.At = TileWorld(B.DoorTile) - In_ * 260.f + FVector(In_.Y, -In_.X, 0) * 230.f; P_.Bld = BI; P_.Wander = 350.f; P_.Index = BI; P_.Yaw = (-In_).Rotation().Yaw;
			TownPosts.Add(P_);
		}
	}
	// ---- the well (three about it, chatting), the market's stalls (a buyer before each)
	for (const FTownSpot& Sp : TownSpots)
	{
		if (Sp.Kind == TS_Well)
			for (int32 K = 0; K < 3; ++K)
			{
				const FVector D = FRotator(0, 40.f + 120.f * K, 0).RotateVector(FVector(1, 0, 0));
				Work(TEXT("Talk"), Sp.At + D * 190.f, (-D).Rotation().Yaw, TW_Chat, -1);
			}
		if (Sp.Kind == TS_Stall)
		{
			const FVector F_ = FRotator(0, Sp.Yaw, 0).RotateVector(FVector(1, 0, 0));
			Work(TEXT("Talk"), Sp.At + F_ * 230.f, (-F_).Rotation().Yaw, TW_Chat, -1);
		}
	}
	// ---- the refugees' camp: a pot over the first tent's fire, a spit over the second's, the third's a fire to talk by
	{
		int32 Tk = 0;
		for (const FTownSpot& Sp : TownSpots)
		{
			if (Sp.Kind != TS_Tent) continue;
			const FVector F_ = FRotator(0, Sp.Yaw, 0).RotateVector(FVector(1, 0, 0)), Al(F_.Y, -F_.X, 0.f);
			const FVector Fp = Sp.At + F_ * 330.f;
			if (Tk == 0)
			{
				AddPieceAt(TEXT("Town.Tripod"), Fp, Sp.Yaw);
				AddPieceAt(TEXT("Town.Pot"), Fp + FVector(0, 0, Generator->TownPotHeight), Sp.Yaw);
				Work(TEXT("Stir"), Fp + Al * Reach(TEXT("Stir"), 70.f), (-Al).Rotation().Yaw, TW_Camp, -1, TEXT("Ladle"));
			}
			else if (Tk == 1)
			{
				for (int32 Sg = -1; Sg <= 1; Sg += 2) AddPieceAt(TEXT("Town.SpitPost"), Fp + Al * (Sg * 95.f), Al.Rotation().Yaw);
				TownSpits.Add(FVector4(Fp.X, Fp.Y, Fp.Z + Generator->TownSpitHeight, Al.Rotation().Yaw));
				const FVector Fw = -Al, Rt(-Fw.Y, Fw.X, 0.f);
				Work(TEXT("Crank"), Fp + Al * 105.f - Fw * Reach(TEXT("Crank"), 40.f) - Rt * 17.f, Fw.Rotation().Yaw, TW_Camp, -1, nullptr, TownSpits.Num() - 1);
			}
			else
				for (int32 Sg = -1; Sg <= 1; Sg += 2) Work(TEXT("Talk"), Fp + Al * (Sg * 170.f), (-Al * (float)Sg).Rotation().Yaw, TW_Camp, -1);
			++Tk;
		}
	}
	UE_LOG(LogRDTown, Log, TEXT("RDTOWN life: %d gardens, %d pens, %d pots, %d spits, %d places of work so far"), Gardens, Pens, Pots, Spits, TownWorks.Num());
}

void ARDSection::TownGrass(FRandomStream& R)
{
	// the short grass (the third list: "there should be short grass in more places where there aren't any roads, there should
	// be more small bushes"): clumps on every free tile of ground inside the wall (none on a road, a door's front, the square or
	// anything placed), two to four a tile; a small bush on about one tile in six, a few flowers among them. They fade out
	// from 45 m (their pieces' CullDistance) and cast no shadow.
	const float M = Generator->TileSize;
	TArray<uint8> Road; Road.Init(0, N * N);
	for (const FIntRect& Rr : TownRoads) for (int32 X = Rr.Min.X; X < Rr.Max.X; ++X) for (int32 Y = Rr.Min.Y; Y < Rr.Max.Y; ++Y) if (In(FIntPoint(X, Y))) Road[Idx(FIntPoint(X, Y))] = 1;
	for (int32 X = TownSquare.Min.X; X < TownSquare.Max.X; ++X) for (int32 Y = TownSquare.Min.Y; Y < TownSquare.Max.Y; ++Y) if (In(FIntPoint(X, Y))) Road[Idx(FIntPoint(X, Y))] = 1;
	for (int32 I = 0; I < TownRoadMask.Num() && I < Road.Num(); ++I) if (TownRoadMask[I]) Road[I] = 1;
	TSet<FIntPoint> DoorFront;
	for (const FTownBld& B : TownBlds) for (int32 K = 1; K <= 2; ++K) DoorFront.Add(B.DoorTile + RDTDir4[B.DoorSide] * K);
	static const TCHAR* Grass[] = { TEXT("Town.GrassShort1"), TEXT("Town.GrassShort2"), TEXT("Town.GrassShort3"), TEXT("Town.GrassShort4") };
	static const TCHAR* Bush[] = { TEXT("Town.BushSmall1"), TEXT("Town.BushSmall2"), TEXT("Town.BushSmall3"), TEXT("Town.BushSmall4") };
	static const TCHAR* Flower[] = { TEXT("Town.Flowers1"), TEXT("Town.Flowers2") };
	for (int32 X = 0; X < N; ++X)
		for (int32 Y = 0; Y < N; ++Y)
		{
			const FIntPoint T(X, Y);
			if (Type[Idx(T)] != 2 || Road[Idx(T)] || Blocked[Idx(T)] || DoorFront.Contains(T)) continue;
			// (the port's harbour grows nothing: its piers are decks over the water; 884 gm1's picture had grass on them)
			if (TownHarbour.Area() > 0 && TownHarbour.Contains(T)) continue;
			// (a road's edge tile keeps its grass back from the road)
			bool bByRoad = false;
			for (int32 D = 0; D < 4 && !bByRoad; ++D) { const FIntPoint Q = T + RDTDir4[D]; bByRoad = In(Q) && Road[Idx(Q)]; }
			const FVector C = TileWorld(T);
			const int32 Nc = bByRoad ? R.RandRange(1, 2) : R.RandRange(2, 4);
			for (int32 K = 0; K < Nc; ++K)
			{
				const float Sp = bByRoad ? 80.f : 135.f;
				AddPiece(Grass[R.RandRange(0, 3)], FTransform(FRotator(0, R.FRandRange(0.f, 360.f), 0), C + FVector(R.FRandRange(-Sp, Sp), R.FRandRange(-Sp, Sp), 0.f), FVector(R.FRandRange(0.7f, 1.25f))), true);
				++TownGrassClumps;
			}
			const float U = R.FRand();
			if (U < 0.16f && !bByRoad)
			{
				const FVector P = C + FVector(R.FRandRange(-100.f, 100.f), R.FRandRange(-100.f, 100.f), 0.f);
				AddPiece(Bush[R.RandRange(0, 3)], FTransform(FRotator(0, R.FRandRange(0.f, 360.f), 0), P, FVector(R.FRandRange(0.6f, 1.1f))), true);
				++TownSmallBushes;
			}
			else if (U < 0.24f)
				AddPiece(Flower[R.RandRange(0, 1)], FTransform(FRotator(0, R.FRandRange(0.f, 360.f), 0), C + FVector(R.FRandRange(-120.f, 120.f), R.FRandRange(-120.f, 120.f), 0.f), FVector(R.FRandRange(0.7f, 1.1f))), true);
		}
	(void)M;
	UE_LOG(LogRDTown, Log, TEXT("RDTOWN grass: %d clumps, %d small bushes"), TownGrassClumps, TownSmallBushes);
}

namespace
{
	/** smooth value noise in [0, 1] (a lattice of hashed values, eased between) and three octaves of it */
	float RDTNoise(float X, float Y, uint32 Seed)
	{
		const int32 Xi = FMath::FloorToInt(X), Yi = FMath::FloorToInt(Y);
		const float Fx = X - Xi, Fy = Y - Yi, Sx = Fx * Fx * (3.f - 2.f * Fx), Sy = Fy * Fy * (3.f - 2.f * Fy);
		auto H = [Seed](int32 A, int32 B) { return (HashCombine(HashCombine((uint32)A * 73856093u, (uint32)B * 19349663u), Seed) & 0xffffu) / 65535.f; };
		return FMath::Lerp(FMath::Lerp(H(Xi, Yi), H(Xi + 1, Yi), Sx), FMath::Lerp(H(Xi, Yi + 1), H(Xi + 1, Yi + 1), Sx), Sy);
	}
	float RDTFbm(float X, float Y, uint32 Seed) { return 0.6f * RDTNoise(X, Y, Seed) + 0.3f * RDTNoise(X * 2.03f, Y * 2.03f, Seed + 17u) + 0.1f * RDTNoise(X * 4.1f, Y * 4.1f, Seed + 31u); }
}

bool ARDSection::InsideTownBorder(const FVector2D& W) const
{
	bool bIn = false;
	for (int32 I = 0, J = TownBorder.Num() - 1; I < TownBorder.Num(); J = I++)
		if (((TownBorder[I].Y > W.Y) != (TownBorder[J].Y > W.Y)) && (W.X < (TownBorder[J].X - TownBorder[I].X) * (W.Y - TownBorder[I].Y) / (TownBorder[J].Y - TownBorder[I].Y) + TownBorder[I].X)) bIn = !bIn;
	return bIn;
}

float ARDSection::TownBorderDist(const FVector2D& W) const
{
	float Dm = 1e9f;
	for (int32 I = 0, J = TownBorder.Num() - 1; I < TownBorder.Num(); J = I++)
		Dm = FMath::Min(Dm, (float)FMath::PointDistToSegment(FVector(W, 0.f), FVector(TownBorder[J], 0.f), FVector(TownBorder[I], 0.f)));
	return Dm;
}

// (the tiles a walked-ground vertex touches: one inside a tile, two on its edge, four at a corner; a vertex on an edge read the
// tile on its +X / +Y side alone, so the harbour's drop to the water fell inside the walked quay on two of its four ways (PR #25's
// review). The drawn ground's harbour is a rectangle and needs no tiles; UnderFloor has its own sampling for the buildings)
static void RDTPTouching(const FVector2D& P, float M, int32 N, TArray<FIntPoint, TInlineAllocator<4>>& Out)
{
	Out.Reset();
	const int32 Xr = FMath::RoundToInt(P.X / M), Yr = FMath::RoundToInt(P.Y / M);
	const bool bEx = FMath::Abs(P.X - Xr * M) < 0.5f, bEy = FMath::Abs(P.Y - Yr * M) < 0.5f;
	const int32 X0 = bEx ? Xr - 1 : FMath::FloorToInt(P.X / M), X1 = bEx ? Xr : X0;
	const int32 Y0 = bEy ? Yr - 1 : FMath::FloorToInt(P.Y / M), Y1 = bEy ? Yr : Y0;
	for (int32 X = X0; X <= X1; ++X)
		for (int32 Y = Y0; Y <= Y1; ++Y)
			Out.AddUnique(FIntPoint(FMath::Clamp(X, 0, N - 1), FMath::Clamp(Y, 0, N - 1)));
}

void ARDSection::TownGround()
{
	TArray<FIntPoint, TInlineAllocator<4>> Tt;
	if (!bBuildStatic) return;
	// one procedural mesh over the whole section: grass, cobbles on the straight roads and the square, earth on the winding
	// streets, the lane and round the doors (the village's ground material by vertex colour: R a dark trodden floor, G cobbles,
	// A a tan earth (its comments called it lush: measured in pictures, it is Hive Sherwood's tan ground)). Since 2026-11-02 (the user's: the roads should show up better against the grass, be irregularly
	// shaped and textured, bumpy and uneven): a vertex a metre (it was one a tile), the earth roads drawn along their winding
	// middles, every road's edge ragged by noise, soil patches in the earth, a little lusher grass along the earth's edges, and
	// the roads' surfaces raised and sunk a few cm (seen only: everyone walks on the flat floor), their normals from the heights
	UMaterialInterface* Mat = Generator->TownGroundMaterial;
	const float M = Generator->TileSize;
	const float TownCobbleHalfWidth = Generator->TownCobbleHalfWidth;
	const int32 Sub = 3;                          // vertices a tile
	const int32 Nv = N * Sub + 1;
	const float St = M / Sub;
	const FVector2D O2(GetActorLocation().X, GetActorLocation().Y);
	const uint32 Sd = (uint32)Seed;
	TArray<FVector> V; TArray<int32> Tri; TArray<FVector> Nrm; TArray<FVector2D> UV; TArray<FLinearColor> Col; TArray<FProcMeshTangent> Tan;
	V.SetNumUninitialized(Nv * Nv); Col.SetNumUninitialized(Nv * Nv); UV.SetNumUninitialized(Nv * Nv); Nrm.SetNumUninitialized(Nv * Nv);
	TArray<uint8> Sunk; Sunk.Init(0, Nv * Nv);
	// (the earth roads' segments, local cm, in buckets by tile; the road on out of the gate among them)
	struct FSeg { FVector2D A, B; float Hw; };
	TArray<FSeg> Segs;
	for (const FTownPath& Pth : TownPaths)
		for (int32 I = 1; I < Pth.Pts.Num(); ++I) Segs.Add({ Pth.Pts[I - 1] - O2, Pth.Pts[I] - O2, Pth.HalfWidth });
	{
		const FVector2D G0 = FVector2D(TownGate.X, TownGate.Y) - O2, Go(TownGateOut.X, TownGateOut.Y);
		for (int32 K = 0; K < 10; ++K)
		{
			const float Wob = 120.f * FMath::Sin(K * 0.9f);
			Segs.Add({ G0 + Go * (K * 300.f) + FVector2D(-Go.Y, Go.X) * Wob, G0 + Go * ((K + 1) * 300.f) + FVector2D(-Go.Y, Go.X) * 120.f * FMath::Sin((K + 1) * 0.9f), M * 1.1f });
		}
	}
	TArray<TArray<int32>> Bk; Bk.SetNum(N * N);
	for (int32 Si = 0; Si < Segs.Num(); ++Si)
	{
		const FSeg& S_ = Segs[Si];
		const float Rr = S_.Hw + 200.f;
		const int32 X0 = FMath::Max(0, FMath::FloorToInt((FMath::Min(S_.A.X, S_.B.X) - Rr) / M)), X1 = FMath::Min(N - 1, FMath::FloorToInt((FMath::Max(S_.A.X, S_.B.X) + Rr) / M));
		const int32 Y0 = FMath::Max(0, FMath::FloorToInt((FMath::Min(S_.A.Y, S_.B.Y) - Rr) / M)), Y1 = FMath::Min(N - 1, FMath::FloorToInt((FMath::Max(S_.A.Y, S_.B.Y) + Rr) / M));
		for (int32 X = X0; X <= X1; ++X) for (int32 Y = Y0; Y <= Y1; ++Y) Bk[Idx(FIntPoint(X, Y))].Add(Si);
	}
	// (the cobbled rectangles, local cm. The list of 2026-11-04: "the cobblestone streets should be at most 3 people wide": a
	// street (a road three tiles across or less: the main road, the cross road) is cobbled in a strip 2.6 m wide down its middle,
	// the rest of its tiles trodden earth; the square and the castle's forecourt are paved whole)
	TArray<FBox2D> Cob, StreetEarth;
	for (const FIntRect& Rr : TownRoads)
	{
		const FBox2D Bx(FVector2D(Rr.Min.X * M, Rr.Min.Y * M), FVector2D(Rr.Max.X * M, Rr.Max.Y * M));
		const FVector2D Sz = Bx.GetSize();
		if (FMath::Min(Sz.X, Sz.Y) <= 3.f * M + 1.f)
		{
			const FVector2D Ct = Bx.GetCenter();
			const FVector2D Hf = Sz.X >= Sz.Y ? FVector2D(Sz.X * 0.5f, TownCobbleHalfWidth) : FVector2D(TownCobbleHalfWidth, Sz.Y * 0.5f);
			Cob.Add(FBox2D(Ct - Hf, Ct + Hf));
			StreetEarth.Add(Bx);
		}
		else Cob.Add(Bx);
	}
	Cob.Add(FBox2D(FVector2D(TownSquare.Min.X * M, TownSquare.Min.Y * M), FVector2D(TownSquare.Max.X * M, TownSquare.Max.Y * M)));
	// (the doors' aprons: the tile out of each door and the one past it)
	TArray<FVector2D> Aprons;
	for (const FTownBld& B : TownBlds)
		for (int32 K = 1; K <= 2; ++K) { const FIntPoint T = B.DoorTile + RDTDir4[B.DoorSide] * K; Aprons.Add(FVector2D((T.X + 0.5f) * M, (T.Y + 0.5f) * M)); }
	// (the gardens' beds dark soil, the pens trodden earth (the third list); local cm, axis aligned)
	struct FPatch { FVector2D C, H; bool bSoil; };
	TArray<FPatch> Patches;
	for (const FTownGarden& Gd : TownGardens) Patches.Add({ FVector2D(Gd.At.X, Gd.At.Y) - O2, Gd.Half, true });
	for (const FTownPen& Pn : TownPens) Patches.Add({ FVector2D(Pn.At.X, Pn.At.Y) - O2, Pn.Half + FVector2D(20.f, 20.f), false });
	// (under a building's floor the ground sinks out of sight: a floor piece whose top is a little lower than its bounds (the
	// stone foundation's) showed the grass through it; at its walls it stays level)
	auto UnderFloor = [&](const FVector2D& P)
	{
		for (int32 Dx = -1; Dx <= 1; Dx += 2) for (int32 Dy = -1; Dy <= 1; Dy += 2)
		{
			const FIntPoint T(FMath::FloorToInt((P.X + Dx * 2.f) / M), FMath::FloorToInt((P.Y + Dy * 2.f) / M));
			if (!In(T) || Type[Idx(T)] != 1) return false;
		}
		return true;
	};
	for (int32 I = 0; I < Nv; ++I)
		for (int32 J = 0; J < Nv; ++J)
		{
			const FVector2D P(I * St, J * St);
			const FIntPoint T(FMath::Clamp(FMath::FloorToInt(P.X / M), 0, N - 1), FMath::Clamp(FMath::FloorToInt(P.Y / M), 0, N - 1));
			const FVector2D Wp = P + O2;
			const bool bInTown = TownBorder.Num() < 3 || InsideTownBorder(Wp);
			// (outside the wall: the town's grass; the A layer it had (named "lush") is the tan ground and read as bare earth over
			// the wide ground the irregular outline leaves)
			FLinearColor C(0, 0, 0, 0);
			// (ragged edges: a noise over a metre and a half moves every edge up to 60 cm in or out)
			const float Rag = (RDTFbm(P.X / 160.f, P.Y / 160.f, Sd) - 0.5f) * 120.f;
			// the earth roads
			float Dd = 1e9f;
			for (const int32 Si : Bk[Idx(T)])
			{
				const FSeg& S_ = Segs[Si];
				Dd = FMath::Min(Dd, (float)FMath::PointDistToSegment(FVector(P, 0.f), FVector(S_.A, 0.f), FVector(S_.B, 0.f)) - S_.Hw);
			}
			// the lane inside the wall: two tiles' earth
			if (bInTown && TownBorder.Num() >= 3) Dd = FMath::Min(Dd, TownBorderDist(Wp) - 2.f * M);
			for (const FVector2D& Ap : Aprons) if (FMath::Abs(Ap.X - P.X) < 250.f && FMath::Abs(Ap.Y - P.Y) < 250.f) Dd = FMath::Min(Dd, FVector2D::Distance(Ap, P) - 170.f);
			// (a street's tiles beside its cobbled strip: trodden earth)
			for (const FBox2D& Bx : StreetEarth)
			{
				const float Dx = FMath::Max(Bx.Min.X - P.X, P.X - Bx.Max.X), Dy = FMath::Max(Bx.Min.Y - P.Y, P.Y - Bx.Max.Y);
				if (Dx > 200.f || Dy > 200.f) continue;
				Dd = FMath::Min(Dd, (Dx > 0.f || Dy > 0.f) ? FMath::Sqrt(FMath::Square(FMath::Max(Dx, 0.f)) + FMath::Square(FMath::Max(Dy, 0.f))) : FMath::Max(Dx, Dy));
			}
			const float Earth = FMath::Clamp(0.5f - (Dd + Rag) / 60.f, 0.f, 1.f);
			// the cobbles: inside a rectangle, its edges ragged a little less
			float Dc = 1e9f;
			for (const FBox2D& Bx : Cob)
			{
				const float Dx = FMath::Max(Bx.Min.X - P.X, P.X - Bx.Max.X), Dy = FMath::Max(Bx.Min.Y - P.Y, P.Y - Bx.Max.Y);
				const float Sdist = (Dx > 0.f || Dy > 0.f) ? FMath::Sqrt(FMath::Square(FMath::Max(Dx, 0.f)) + FMath::Square(FMath::Max(Dy, 0.f))) : FMath::Max(Dx, Dy);
				Dc = FMath::Min(Dc, Sdist);
			}
			const float Cobble = FMath::Clamp(0.5f - (Dc + Rag * 0.55f) / 40.f, 0.f, 1.f);
			C.G = Cobble;
			// (the earth: the material's A layer, Hive Sherwood's tan ground, which stands out from the grass as the reference
			// map's roads do; its R layer, the darker trodden floor, worn into it in patches. On R alone the roads read as a dull
			// grey-green patch of the grass in the first pictures of 2026-11-02)
			const float Ear = Earth * (1.f - Cobble);
			C.A = FMath::Max(C.A, Ear);
			C.R = Ear * (0.15f + 0.35f * FMath::Clamp((RDTFbm(P.X / 110.f, P.Y / 110.f, Sd + 5u) - 0.35f) * 2.2f, 0.f, 1.f));
			C.B = 0.f;
			for (const FPatch& Pc : Patches)
			{
				const float Dx = FMath::Abs(P.X - Pc.C.X) - Pc.H.X, Dy = FMath::Abs(P.Y - Pc.C.Y) - Pc.H.Y;
				if (Dx > 60.f || Dy > 60.f) continue;
				const float Sdist = FMath::Max(Dx, Dy);
				const float Sv = FMath::Clamp(0.5f - (Sdist + Rag * 0.35f) / 30.f, 0.f, 1.f) * (1.f - Cobble);
				if (Pc.bSoil) { C.R = FMath::Max(C.R, 0.9f * Sv); C.A = FMath::Max(C.A, 0.3f * Sv); }
				else { C.A = FMath::Max(C.A, 0.85f * Sv); C.R = FMath::Max(C.R, 0.4f * Sv); }
			}
			Col[I * Nv + J] = C;
			// the height: bumps and ruts in the earth (up to +-5 cm), worn stones in the cobbles (+-2.5 cm)
			float Z = UnderFloor(P) ? -40.f : 0.f;
			// (the port's harbour: its bed 2.6 m under the quay, under the harbour's own water (RDPort.cpp), the piers' tiles too:
			// they are decks on pilings; at the ground's height the grass showed between the planks)
			// (sunk strictly inside the harbour's rectangle, so the vertices on its edge stay at the quay's height as the walked ground
			// does. The drop is drawn behind the quay's stone face, under the wall: a vertex on the edge stands 10 cm back into the
			// land and the sunk vertex a step from it 5 cm back. Left on the grid the bed made a 1 m ramp out of the water in front
			// of the face and under the piers' roots (PR #26's review); dropped 5 cm in front of the line it hid the face's stone
			// behind a stretched cliff of the ground's own (884 gm8's edge pictures))
			FVector2D Pv = P;
			if (TownHarbour.Area() > 0)
			{
				const float Hx0 = TownHarbour.Min.X * M, Hx1 = TownHarbour.Max.X * M, Hy0 = TownHarbour.Min.Y * M, Hy1 = TownHarbour.Max.Y * M;
				const bool bSpanX = P.X > Hx0 - 0.5f && P.X < Hx1 + 0.5f, bSpanY = P.Y > Hy0 - 0.5f && P.Y < Hy1 + 0.5f;
				if (P.X > Hx0 + 0.5f && P.X < Hx1 - 0.5f && P.Y > Hy0 + 0.5f && P.Y < Hy1 - 0.5f)
				{
					Z = -260.f;
					if (P.X - St < Hx0 + 0.5f) Pv.X = Hx0 - 5.f; else if (P.X + St > Hx1 - 0.5f) Pv.X = Hx1 + 5.f;
					if (P.Y - St < Hy0 + 0.5f) Pv.Y = Hy0 - 5.f; else if (P.Y + St > Hy1 - 0.5f) Pv.Y = Hy1 + 5.f;
				}
				else if (bSpanX && bSpanY)
				{
					// (on the rectangle's edge: back into the land)
					if (FMath::Abs(P.X - Hx0) < 0.5f) Pv.X = Hx0 - 10.f; else if (FMath::Abs(P.X - Hx1) < 0.5f) Pv.X = Hx1 + 10.f;
					if (FMath::Abs(P.Y - Hy0) < 0.5f) Pv.Y = Hy0 - 10.f; else if (FMath::Abs(P.Y - Hy1) < 0.5f) Pv.Y = Hy1 + 10.f;
				}
			}
			Sunk[I * Nv + J] = Z < 0.f ? 1 : 0;
			if (Z == 0.f)
			{
				Z += C.R * ((RDTFbm(P.X / 70.f, P.Y / 70.f, Sd + 9u) - 0.5f) * 10.f - 1.5f);
				Z += C.G * (RDTNoise(P.X / 28.f, P.Y / 28.f, Sd + 13u) - 0.5f) * 5.f;
				// (the open ground's rise and fall: 0 where anything stands or is walked to)
				Z += TownLiftAt(Wp);
			}
			V[I * Nv + J] = FVector(Pv.X, Pv.Y, Z);
			UV[I * Nv + J] = FVector2D(Pv.X / 400.f, Pv.Y / 400.f);
		}
	// (normals from the heights: the bumps shade)
	for (int32 I = 0; I < Nv; ++I)
		for (int32 J = 0; J < Nv; ++J)
		{
			const float Zx0 = V[FMath::Max(I - 1, 0) * Nv + J].Z, Zx1 = V[FMath::Min(I + 1, Nv - 1) * Nv + J].Z;
			const float Zy0 = V[I * Nv + FMath::Max(J - 1, 0)].Z, Zy1 = V[I * Nv + FMath::Min(J + 1, Nv - 1)].Z;
			// (the sunk floors' steep sides are left flat-lit; the open ground's slopes shade)
			const bool bEdge = Sunk[FMath::Max(I - 1, 0) * Nv + J] != Sunk[FMath::Min(I + 1, Nv - 1) * Nv + J] || Sunk[I * Nv + FMath::Max(J - 1, 0)] != Sunk[I * Nv + FMath::Min(J + 1, Nv - 1)];
			if (bEdge) { Nrm[I * Nv + J] = FVector::UpVector; continue; }
			Nrm[I * Nv + J] = FVector(-(Zx1 - Zx0) / (2.f * St), -(Zy1 - Zy0) / (2.f * St), 1.f).GetSafeNormal();
		}
	Tri.Reserve((Nv - 1) * (Nv - 1) * 6);
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
	// (the drawn ground is seen only: under the buildings it is sunk, and their own floors stand on the walked ground. Until
	// 2026-11-04 everyone walked on a flat invisible floor at its level, as in the village; since the list of that day the
	// open ground rises and falls, and the walked ground is a mesh of its own following it, a vertex every 1.5 m, without the
	// cobbles' and ruts' few cm: TownLiftAt is smooth over metres)
	G->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	{
		const int32 SubW = 2, NvW = N * SubW + 1;
		const float StW = M / SubW;
		TArray<FVector> Vw; Vw.SetNumUninitialized(NvW * NvW);
		for (int32 I = 0; I < NvW; ++I)
			for (int32 J = 0; J < NvW; ++J)
			{
				const FVector2D P(I * StW, J * StW);
				// (the harbour's water walked 1.7 m down behind its blockers; a pier's deck flat at the quay's height. A vertex on a
				// tile's edge is water only if every tile it touches is: the drop to the water then falls behind the blocker on every
				// way (taking the tile on its +X / +Y side, the quay's last 1.5 m fell 1.4 m on two ways: 884 gm6, PR #25's review))
				float Zw = TownLiftAt(P + O2);
				// (only a vertex on the harbour's rectangle or in it can touch one of its tiles)
				if (TownHarbour.Area() > 0 && P.X > TownHarbour.Min.X * M - 0.5f && P.X < TownHarbour.Max.X * M + 0.5f && P.Y > TownHarbour.Min.Y * M - 0.5f && P.Y < TownHarbour.Max.Y * M + 0.5f)
				{
					RDTPTouching(P, M, N, Tt);
					bool bWater = true, bPier = false;
					for (const FIntPoint& Q : Tt) { bWater &= InHarbourWater(Q); bPier |= TownHarbour.Contains(Q) && !InHarbourWater(Q); }
					if (bWater) Zw = -170.f; else if (bPier) Zw = 0.f;
				}
				Vw[I * NvW + J] = FVector(P.X, P.Y, Zw);
			}
		TArray<int32> Tw; Tw.Reserve((NvW - 1) * (NvW - 1) * 6);
		for (int32 I = 0; I < NvW - 1; ++I)
			for (int32 J = 0; J < NvW - 1; ++J)
			{
				const int32 A = I * NvW + J, B = (I + 1) * NvW + J, C = (I + 1) * NvW + J + 1, D = I * NvW + J + 1;
				Tw.Append({ A, C, B, A, D, C });
			}
		UProceduralMeshComponent* Wk = NewObject<UProceduralMeshComponent>(this, TEXT("TownWalk"), RF_Transactional);
		Wk->SetupAttachment(RootComponent);
		Wk->SetMobility(EComponentMobility::Static);
		Wk->bUseComplexAsSimpleCollision = true;
		Wk->bUseAsyncCooking = false;
		Wk->RegisterComponent();
		AddInstanceComponent(Wk);
		Wk->CreateMeshSection_LinearColor(0, Vw, Tw, TArray<FVector>(), TArray<FVector2D>(), TArray<FLinearColor>(), TArray<FProcMeshTangent>(), true);
		Wk->SetCollisionProfileName(TEXT("BlockAll"));
		Wk->SetVisibility(false); Wk->SetHiddenInGame(true); Wk->SetCastShadow(false);
	}
	// (a floor far under it all, to catch a fall)
	UBoxComponent* Fl = NewObject<UBoxComponent>(this, TEXT("TownFloor"), RF_Transactional);
	Fl->SetupAttachment(RootComponent);
	Fl->SetMobility(EComponentMobility::Static);
	Fl->SetBoxExtent(FVector(N * M * 0.5f, N * M * 0.5f, 20.f));
	Fl->SetRelativeLocation(FVector(N * M * 0.5f, N * M * 0.5f, -620.f));
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
	constexpr float RDTCWalkDoor = 225.f;
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
	// (the third list of 2026-11-02: "one watch tower on the castle let the player pass through to the inside. that should not
	// happen. the player should only be able to get to the watch tower from the inside of the castle": no tower has a door at
	// its foot any more (the stair turret's at 315 degrees let her in from the forecourt and up onto the walk); each is entered
	// from the wall walk by a doorway toward the castle, and the walk is reached by the stair inside the castle)
	CastleStairDoor = FVector::ZeroVector;
	CastleWalkZ = GetActorLocation().Z + CastleWalkTop();
	CastleWalkDoor = CastleTowers[0] + Dir(RDTCWalkDoor) * (RDTCTowerR - 30.f) + FVector(0, 0, CastleWalkTop());
	// the ground under the towers is void (nobody walks into them, nothing grows there)
	for (const FVector& C : CastleTowers)
	{
		const FIntPoint Ct = WorldToLocal(C);
		for (int32 X = Ct.X - 3; X <= Ct.X + 3; ++X)
			for (int32 Y = Ct.Y - 3; Y <= Ct.Y + 3; ++Y)
			{
				const FIntPoint T(X, Y);
				if (!In(T) || Type[Idx(T)] != 2) continue;
				if (FVector::Dist2D(TileWorld(T), C) < RDTCTowerR + 70.f) { Type[Idx(T)] = 0; Owner[Idx(T)] = -1; }
			}
	}
	CastleStairPlan();
}

namespace
{
	/** the castle's inside stair: steps, their rise from the floor to the walk's top, their run and width (cm) */
	constexpr int32 RDTCSteps = 30;
	constexpr float RDTCStepRun = 30.f, RDTCStairWidth = 160.f;
	/** a tower's doorway from the walk: toward the castle's middle (the castle's frame) */
	float RDTCTowerInward(const FVector& Lc) { return FMath::RadiansToDegrees(FMath::Atan2(-Lc.Y, -Lc.X)); }
}

void ARDSection::CastleStairPlan()
{
	// the stair up to the wall walk (the third list: "there should be a way down from the battlements to the floor of the
	// castle, like stairs"): in the wing on the stair turret's side (the castle's +Y), against its outer wall, rising toward the
	// front over three tiles (30 steps of 22 cm, 30 cm deep, 1.6 m wide) from the fourth tile behind the front corner to the
	// corner's tile, whose roof is the walk; the two tiles over its upper steps have no ceiling and no roof (the stairwell). Its
	// tiles are kept from the furniture. The castle's frame: +X its front, +Y the turret's side (TownBldPoint).
	if (!TownBlds.IsValidIndex(CastleBld)) return;
	const FTownBld& B = TownBlds[CastleBld];
	const float M = Generator->TileSize;
	const int32 Nx = B.DoorSide < 2 ? B.Max.X - B.Min.X : B.Max.Y - B.Min.Y;
	const int32 Ny = B.DoorSide < 2 ? B.Max.Y - B.Min.Y : B.Max.X - B.Min.X;
	const float Hx = Nx * M * 0.5f, Hy = Ny * M * 0.5f;
	const float Run = RDTCSteps * RDTCStepRun;
	CastleStairFoot = TownBldPoint(B, Hx - M - Run, Hy - RDTCStairWidth * 0.5f - 10.f, 0.f);
	CastleStairTop = TownBldPoint(B, Hx - M, Hy - RDTCStairWidth * 0.5f - 10.f, CastleWalkTop());
	for (int32 K = 1; K <= 4; ++K)
	{
		const FIntPoint T = WorldToLocal(TownBldPoint(B, Hx - M * (K + 0.5f), Hy - M * 0.5f, 0.f));
		if (!In(T)) continue;
		if (K <= 3) Blocked[Idx(T)] = 1;
		if (K <= 2) CastleStairwell.Add(T);
		if (K == 1) CastleStairRoom = Owner[Idx(T)];
	}
	// (the tile at the stair's foot stays clear of furniture too)
	const FIntPoint Ft = WorldToLocal(TownBldPoint(B, Hx - M * 4.5f, Hy - M * 0.5f, 0.f));
	if (In(Ft)) Blocked[Idx(Ft)] = 1;
}

void ARDSection::CastleStairBuild()
{
	if (!TownBlds.IsValidIndex(CastleBld) || CastleStairwell.Num() == 0) return;
	const FTownBld& B = TownBlds[CastleBld];
	const FRDPiece* Cw = Generator->Piece(TEXT("Town.CWall"));
	if (!Cw) return;
	const float M = Generator->TileSize, Yaw0 = TownBldYaw(B), Top = CastleWalkTop();
	const int32 Nx = B.DoorSide < 2 ? B.Max.X - B.Min.X : B.Max.Y - B.Min.Y;
	const int32 Ny = B.DoorSide < 2 ? B.Max.Y - B.Min.Y : B.Max.X - B.Min.X;
	const float Hx = Nx * M * 0.5f, Hy = Ny * M * 0.5f;
	const float Th = FMath::Max((float)Cw->Size.X, 40.f), Len = FMath::Max((float)Cw->Size.Y, 100.f), Ht = FMath::Max((float)Cw->Size.Z, 100.f);
	const float Run = RDTCSteps * RDTCStepRun, Rise = Top / RDTCSteps;
	const float Yc = Hy - RDTCStairWidth * 0.5f - 10.f;
	// the steps: each a block of Castle Forge's stone from the floor to its tread (the stair one solid mass, as a stone stair
	// against a wall is), 2 cm over the next so that no seam shows
	for (int32 I = 0; I < RDTCSteps; ++I)
	{
		const float X = Hx - M - Run + (I + 0.5f) * RDTCStepRun, H = (I + 1) * Rise;
		AddPiece(TEXT("Town.CWall"), FTransform(FRotator(0, Yaw0, 0), TownBldPoint(B, X, Yc, 0.f), FVector((RDTCStepRun + 2.f) / Th, RDTCStairWidth / Len, H / Ht)));
	}
	// the stairwell's balustrade on the walk, a metre high round the opening but where the stair comes up: along its inner side,
	// its back end and the rest of its front end beside the stair's top
	auto Rail = [&](float X0, float Y0, float X1, float Y1)
	{
		const FVector2D D(X1 - X0, Y1 - Y0); const float L = D.Size();
		if (L < 20.f) return;
		const float Ya = Yaw0 + FMath::RadiansToDegrees(FMath::Atan2(D.Y, D.X)) - 90.f;
		AddPiece(TEXT("Town.CWall"), FTransform(FRotator(0, Ya, 0), TownBldPoint(B, (X0 + X1) * 0.5f, (Y0 + Y1) * 0.5f, Top), FVector(30.f / Th, (L + 20.f) / Len, 100.f / Ht)));
	};
	const float Xb = Hx - M * 3.f, Xf = Hx - M, Yi = Hy - M;
	Rail(Xb, Yi, Xf, Yi);
	Rail(Xb, Yi, Xb, Hy);
	Rail(Xf, Yi, Xf, Yc - RDTCStairWidth * 0.5f - 5.f);
	// (light: a torch on the outer wall over the stair's foot, one at its top)
	AddTorch(TownBldPoint(B, Hx - M - Run + 60.f, Hy - 25.f, 260.f), Yaw0 - 90.f, 110.f);
	AddTorch(TownBldPoint(B, Hx - M * 1.5f, Hy - 25.f, Top - 180.f), Yaw0 - 90.f, 90.f);
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
	for (int32 I = 0; I < CastleTowers.Num(); ++I)
	{
		const FVector C = CastleTowers[I];
		const FVector Lc = FRotator(0, -Yaw0, 0).RotateVector(C - TownBldPoint(B, 0.f, 0.f, 0.f));
		const float Out = FMath::RadiansToDegrees(FMath::Atan2(Lc.Y, Lc.X));      // (the way out from the castle's middle)
		// (its doorway from the wall walk: toward the castle's middle, where the walk's corner meets the ring)
		const float Inw = RDTCTowerInward(Lc);
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
				if (St == 2 && RDTCAngleDiff(Mid, Inw) < 10.f) V = TEXT('D');
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
			if (RDTCAngleDiff(A, Inw) < 11.25f) { Box(0.f, Top); Box(Top + 240.f, TowerTop); }
			else Box(0.f, TowerTop);
		}
		// (its floor at the walk's level, out to the ring all round; the corner of the castle's walls opens into it by the door)
		if (Rf) AddPiece(TEXT("Town.CastleRoof"), FTransform(FRotator(0, Yaw0, 0), C + FVector(0, 0, Top - RfZ), FVector(560.f / RfX, 560.f / RfX, 1.f)));
		// (a torch inside across from the door: it is seen lit from the walk)
		AddTorch(C + Dir(Inw + 180.f) * 250.f + FVector(0, 0, Top + 170.f), Yaw0 + Inw, 100.f);
	}
}

TArray<FString> ARDSection::GetCastleShapeLines() const
{
	TArray<FString> Out;
	for (int32 I = 0; I < CastleTowers.Num(); ++I) Out.Add(FString::Printf(TEXT("tower|%.0f|%.0f|%d"), CastleTowers[I].X, CastleTowers[I].Y, I == CastleStairTower ? 1 : 0));
	// (since the third list: each tower's doorway from the walk (world, the walk's height), the stair inside the castle (its foot
	// and top, world) and its stairwell's tiles; no tower has a door at its foot)
	if (TownBlds.IsValidIndex(CastleBld))
	{
		const FTownBld& B = TownBlds[CastleBld];
		const float Yaw0 = TownBldYaw(B);
		for (const FVector& C : CastleTowers)
		{
			const FVector Lc = FRotator(0, -Yaw0, 0).RotateVector(C - TownBldPoint(B, 0.f, 0.f, 0.f));
			const FVector D = FRotator(0, Yaw0 + RDTCTowerInward(Lc), 0).RotateVector(FVector(RDTCTowerMid, 0, 0));
			Out.Add(FString::Printf(TEXT("towerdoor|%.0f|%.0f|%.0f|%.0f|%.0f"), C.X + D.X, C.Y + D.Y, CastleWalkZ, C.X, C.Y));
		}
		Out.Add(FString::Printf(TEXT("stair|%.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%d|%d"), CastleStairFoot.X, CastleStairFoot.Y, CastleStairFoot.Z, CastleStairTop.X, CastleStairTop.Y, CastleStairTop.Z, CastleStairwell.Num(), CastleStairRoom));
	}
	Out.Add(FString::Printf(TEXT("walk|%.0f"), CastleWalkZ));
	return Out;
}
// ------------------------------------------------------------------------------------------------ helpers of 2026-11-02
void ARDSection::AddMeshBoundsCollider(FName Name, const FTransform& T)
{
	const FRDPiece* P = Generator->Piece(Name);
	if (!P || !P->Mesh || !Generator->Piece(TEXT("Town.Collider"))) return;
	// (the collider is a 1 m cube standing on its origin: put over the mesh's box as the piece places it)
	const FBox Bx = P->Mesh->GetBoundingBox();
	const FTransform W = P->Adjust * T;
	const FVector Ctr = Bx.GetCenter();
	AddPiece(TEXT("Town.Collider"), FTransform(W.GetRotation(), W.TransformPosition(FVector(Ctr.X, Ctr.Y, Bx.Min.Z)), W.GetScale3D() * (Bx.GetSize() / 100.f)));
}

TArray<FString> ARDSection::GetTownShapeLines() const
{
	TArray<FString> Out;
	for (const FVector2D& B : TownBorder) Out.Add(FString::Printf(TEXT("border|%.0f|%.0f"), B.X, B.Y));
	for (const FTownPath& P : TownPaths) Out.Add(FString::Printf(TEXT("path|%d|%.0f|%.0f|%.0f|%.0f|%.0f"), P.Pts.Num(), P.HalfWidth,
		P.Pts.Num() ? P.Pts[0].X : 0.f, P.Pts.Num() ? P.Pts[0].Y : 0.f, P.Pts.Num() ? P.Pts.Last().X : 0.f, P.Pts.Num() ? P.Pts.Last().Y : 0.f));
	int32 Nc = 0, Ne = 0, Nl = 0;
	for (const uint8 Mk : TownRoadMask) { Nc += Mk == 1; Ne += Mk == 2; Nl += Mk == 3; }
	Out.Add(FString::Printf(TEXT("roads|%d|%d|%d"), Nc, Ne, Nl));
	// (the earth roads' headings: the share of their length running within 12 degrees of the town's axes (a grid of streets:
	// nearly all; ways wandering at random: about a quarter), and their whole length in metres)
	{
		double OnAxis = 0.0, All = 0.0;
		for (const FTownPath& P : TownPaths)
			for (int32 I = 1; I < P.Pts.Num(); ++I)
			{
				const FVector2D D = P.Pts[I] - P.Pts[I - 1]; const double Ln = D.Size();
				if (Ln < 1.0) continue;
				const float A = FMath::Fmod(FMath::Abs(FMath::RadiansToDegrees(FMath::Atan2(D.Y, D.X))), 90.f);
				if (A < 12.f || A > 78.f) OnAxis += Ln;
				All += Ln;
			}
		Out.Add(FString::Printf(TEXT("headings|%.3f|%.0f"), All > 0.0 ? OnAxis / All : 0.0, All / 100.0));
	}
	for (const FTownWork& W : TownWorks) Out.Add(FString::Printf(TEXT("work|%s|%.0f|%.0f|%.0f|%.0f|%d|%d"), *W.Kind.ToString(), W.At.X, W.At.Y, W.At.Z, W.Yaw, W.Group, W.Bld));
	for (const FTownPen& P : TownPens) Out.Add(FString::Printf(TEXT("pen|%.0f|%.0f|%.0f|%.0f|%.0f|%d"), P.At.X, P.At.Y, P.Half.X, P.Half.Y, P.Yaw, P.Animal));
	for (const FTownGarden& G : TownGardens) Out.Add(FString::Printf(TEXT("garden|%.0f|%.0f|%.0f|%.0f|%.0f|%d"), G.At.X, G.At.Y, G.Half.X, G.Half.Y, G.Yaw, G.Plants));
	Out.Add(FString::Printf(TEXT("greens|%d|%d"), TownGrassClumps, TownSmallBushes));
	for (int32 I = 0; I < TownTowerDoors.Num() && I < TownTowerMids.Num(); ++I)
		Out.Add(FString::Printf(TEXT("watch|%.0f|%.0f|%.0f|%.0f|%.1f|%.0f"), TownTowerMids[I].X, TownTowerMids[I].Y, TownTowerDoors[I].X, TownTowerDoors[I].Y, TownTowerDoors[I].Z, TownTowerMids[I].Z));
	return Out;
}
void ARDSection::AddSignText(const FTransform& SignT, const FString& Text)
{
	if (!bBuildStatic || Text.IsEmpty()) return;
	// (the list of 2026-11-04: "they often fall outside of the sign's boundaries. the font should also be an appropriate medieval
	// one": the board measured (x 58.5 to 122.3, z -114.7 to -64.3, its faces 3.1 cm out of its middle), each trade's words
	// painted in Almendra by bs_signs.py to fit 58 x 42 cm on a plane against each face (890's "Town.SignFace_<WORDS>"))
	FString Key;
	for (const TCHAR Ch : Text) if (FChar::IsAlnum(Ch)) Key.AppendChar(Ch);
	const FName Face(*FString::Printf(TEXT("Town.SignFace_%s"), *Key));
	if (Generator->Piece(Face))
	{
		for (int32 Side = -1; Side <= 1; Side += 2)
			AddPiece(Face, FTransform(FRotator(0, Side > 0 ? 0.f : 180.f, 0), FVector(90.4f, Side * 3.35f, -89.5f)) * SignT, true);
		return;
	}
	// (the tavern sign's board hangs under its bracket: about x 30-146, z -115 to -20 in the piece's frame, 6 cm thick along y;
	// the letters on each face, gold paint on the dark wood)
	for (int32 Side = -1; Side <= 1; Side += 2)
	{
		UTextRenderComponent* Tx = NewObject<UTextRenderComponent>(this, NAME_None, RF_Transactional);
		Tx->SetupAttachment(RootComponent);
		Tx->SetMobility(EComponentMobility::Static);
		Tx->SetText(FText::FromString(Text));
		Tx->SetHorizontalAlignment(EHTA_Center);
		Tx->SetVerticalAlignment(EVRTA_TextCenter);
		Tx->SetWorldSize(Text.Contains(TEXT("\n")) ? 17.f : 19.f);
		Tx->SetTextRenderColor(FColor(255, 214, 120));
		Tx->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Tx->ComponentTags.Add(TEXT("TownSign"));
		// (a text faces its +X: turned to face the board's side)
		const FTransform Local(FRotator(0, Side * 90.f, 0), FVector(88.f, Side * 4.2f, -66.f));
		Tx->SetWorldTransform(Local * SignT);
		Tx->RegisterComponent();
		AddInstanceComponent(Tx);
	}
}
TArray<float> ARDSection::GetTownPathWander() const
{
	TArray<float> Out;
	for (const FTownPath& P : TownPaths)
	{
		if (P.Pts.Num() < 2) continue;
		const FVector A(P.Pts[0], 0.f), B(P.Pts.Last(), 0.f);
		float Dm = 0.f;
		for (const FVector2D& Q : P.Pts) Dm = FMath::Max(Dm, (float)FMath::PointDistToSegment(FVector(Q, 0.f), A, B));
		Out.Add(Dm / 100.f);
	}
	return Out;
}