// The user's list of 2026-11-22 (docs/improvements16.txt; the plan docs/improvements16_plan.md), its eighth phase: the caves rebuilt
// with the Hyper Cave Building Toolkit, "not the same as the dungeon procedural generation, not a dungeon with cave textures". A cave
// set (the generator's bCave16) is laid by a planner of its own instead of Plan's rooms and hallways: the kit's rooms (their walkable
// tiles and floor heights traced on their meshes by 945) stand where they fit, turned by quarter turns, some a level lower; a tree of
// joins and a fifth more (loops) links them, and each join is a tunnel from one room's opening to the other's, routed over the tile
// grid round every room and every other tunnel and wound by a noise field, then bent along a smooth curve with the kit's tunnel mesh in
// overlapping pieces (as its BP_Cave_Spline_* lay them); two rooms of different levels are joined through the kit's stairs where they
// fit, else the tunnel climbs. An opening no tunnel uses gets the kit's cap. The set's portals (one or two a side, the same for both
// sets of a border) are tunnels to the border. Everything the game's systems read is filled as Plan fills it (Type, Owner, Rooms with
// their rectangles, the tiles' floor heights): the monsters' tile paths, the maps, the tiers' progress and the saves work as before;
// a tunnel is a Junction "room" whose tiles join anything (FindPath lets owners meet there).
#include "RD/RDSection.h"
#include "RD/RDDungeonGenerator.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SplineMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "Materials/MaterialInterface.h"
#include "Components/BoxComponent.h"
#include "Engine/CollisionProfile.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Misc/ScopeExit.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Kismet/KismetRenderingLibrary.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDCave16, Log, All);

namespace
{
	const FIntPoint RDC16Dir8[8] = { FIntPoint(1, 0), FIntPoint(-1, 0), FIntPoint(0, 1), FIntPoint(0, -1), FIntPoint(1, 1), FIntPoint(1, -1), FIntPoint(-1, 1), FIntPoint(-1, -1) };

	/** a quarter-turned offset (UE's yaw: +X toward +Y) */
	FIntPoint RDC16Turn(FIntPoint D, int32 K)
	{
		switch (K & 3) { case 1: return FIntPoint(-D.Y, D.X); case 2: return FIntPoint(-D.X, -D.Y); case 3: return FIntPoint(D.Y, -D.X); default: return D; }
	}
	FVector2D RDC16Turn(const FVector2D& V, int32 K)
	{
		switch (K & 3) { case 1: return FVector2D(-V.Y, V.X); case 2: return FVector2D(-V.X, -V.Y); case 3: return FVector2D(V.Y, -V.X); default: return V; }
	}

	/** a smooth value noise over the grid (cells of 6 tiles) from the set's seed: the tunnels' cost, so they wind */
	float RDC16Noise(int32 Seed, float X, float Y)
	{
		// (unsigned before multiplying: a signed overflow is undefined, and a build could fold it otherwise and lay other routes)
		auto H = [Seed](int32 I, int32 J) { uint32 h = (uint32)I * 73856093u ^ (uint32)J * 19349663u ^ (uint32)Seed * 83492791u; h ^= h >> 13; h *= 0x5bd1e995u; h ^= h >> 15; return (h & 0xffff) / 65535.f; };
		const float Fx = X / 6.f, Fy = Y / 6.f;
		const int32 I = FMath::FloorToInt(Fx), J = FMath::FloorToInt(Fy);
		const float U = FMath::SmoothStep(0.f, 1.f, Fx - I), V = FMath::SmoothStep(0.f, 1.f, Fy - J);
		return FMath::Lerp(FMath::Lerp(H(I, J), H(I + 1, J), U), FMath::Lerp(H(I, J + 1), H(I + 1, J + 1), U), V);
	}

	/** a polyline with its corners rounded: each corner's arc of Radius (less where its legs are short: at most 45 % of each),
	 *  sampled every Step cm; the ends kept. The kit's 17 m pieces bent round a tighter corner fold their inner wall into the way */
	void RDC16Round(const TArray<FVector2D>& C, float Radius, float Step, TArray<FVector2D>& Out)
	{
		Out.Reset();
		if (C.Num() < 3) { Out = C; return; }
		Out.Add(C[0]);
		for (int32 I = 1; I + 1 < C.Num(); ++I)
		{
			const FVector2D A = (C[I] - C[I - 1]), Bv = (C[I + 1] - C[I]);
			const float La = A.Size(), Lb = Bv.Size();
			if (La < 1.f || Lb < 1.f) continue;
			const FVector2D Da = A / La, Db = Bv / Lb;
			const float Th = FMath::Acos(FMath::Clamp(FVector2D::DotProduct(Da, Db), -1.f, 1.f));
			if (Th < FMath::DegreesToRadians(2.f)) { Out.Add(C[I]); continue; }
			const float T = FMath::Tan(Th * 0.5f);
			const float D = FMath::Min(Radius * T, 0.45f * FMath::Min(La, Lb));
			const float Rr = D / T;
			const FVector2D P1 = C[I] - Da * D;
			const float Side = FVector2D::CrossProduct(Da, Db) > 0.f ? 1.f : -1.f;
			const FVector2D Ctr = P1 + FVector2D(-Da.Y, Da.X) * Side * Rr;
			const float A0 = FMath::Atan2(P1.Y - Ctr.Y, P1.X - Ctr.X);
			const int32 M = FMath::Max(2, FMath::CeilToInt(Rr * Th / Step));
			for (int32 K = 0; K <= M; ++K) { const float Ang = A0 + Side * Th * K / M; Out.Add(Ctr + FVector2D(FMath::Cos(Ang), FMath::Sin(Ang)) * Rr); }
		}
		Out.Add(C.Last());
	}
}

// ------------------------------------------------------------------------------------------------ the plan
void ARDSection::PlanCave16(FRandomStream& R)
{
	// (a plan that leaves a room no tunnel reaches is laid again, each try from its own stream off the set's: the best (no room cut
	// off, then the most portals with a tunnel) is laid again at the end. In play the tries go one a frame (ContinueGenerate: the
	// whole plan took 70 to 710 ms); the census and the editor's build take them at once. Both draw the same streams: the same cave)
	CaveBase16 = R.RandHelper(1 << 30);
	CaveTry16 = 0; CaveBestTry16 = 0; CaveBestScore16 = INT_MIN; CaveLastTry16 = -1; PlanMs16 = 0.0; PlanStepMs16 = 0.0;
	if (bCaveSpread16) return;
	while (CaveStep16()) {}
}

int32 ARDSection::CaveTryOnce16(int32 Try)
{
	Rooms.Reset(); Portals.Reset(); DoorEdges.Reset();
	Type.Init(0, N * N); Owner.Init(-1, N * N); Blocked.Init(0, N * N); CeilH.Init(0.f, N * N);
	FRandomStream RT(CaveBase16 + 7919 * Try);
	const int32 Cut = PlanCaveOnce16(RT, Try);
	return -1000 * Cut + 10 * Portals.Num();
}

bool ARDSection::CaveStep16()
{
	const double T0 = FPlatformTime::Seconds();
	ON_SCOPE_EXIT { const double Ms = (FPlatformTime::Seconds() - T0) * 1000.0; PlanMs16 += Ms; PlanStepMs16 = FMath::Max(PlanStepMs16, Ms); };
	if (CaveTry16 < 8)
	{
		const int32 Sc = CaveTryOnce16(CaveTry16); CaveLastTry16 = CaveTry16;
		if (Sc > CaveBestScore16) { CaveBestScore16 = Sc; CaveBestTry16 = CaveTry16; }
		CaveTry16 = Sc >= 40 ? 8 : CaveTry16 + 1;          // (no room cut off and a portal on every side: done)
		return true;
	}
	if (CaveBestTry16 != CaveLastTry16) { CaveTryOnce16(CaveBestTry16); CaveLastTry16 = CaveBestTry16; }
	UE_LOG(LogRDCave16, Log, TEXT("RDCAVE16 (%d,%d) planned in %.1f ms (try %d kept; %s, the longest step %.1f ms)"), Coord.X, Coord.Y, PlanMs16 + (FPlatformTime::Seconds() - T0) * 1000.0, CaveBestTry16,
		bCaveSpread16 ? TEXT("a try a frame") : TEXT("at once"), PlanStepMs16);
	return false;
}

int32 ARDSection::PlanCaveOnce16(FRandomStream& R, int32 Try)
{
	ARDDungeonGenerator* G = Generator;
	const float S = G->TileSize;
	const int32 B = G->BlockTiles;
	CavePlaced16.Reset(); CaveRuns16.Reset(); CaveCaps16.Reset();
	CaveZ16.Init(0.f, N * N);
	if (G->CaveRooms16.Num() == 0 || G->CaveTunnels16.Num() == 0) { UE_LOG(LogRDCave16, Warning, TEXT("RDCAVE16 no kit on the generator (945 level)")); return 0; }
	const int32 Tier = G->TierOf(Coord);
	const bool bStart = G->IsStartSection(Coord);
	// (keep-out: a room's whole box (its mask's frame is the mesh's box and a tile round it); the tunnels' cost field)
	TArray<uint8> Box; Box.Init(0, N * N);           // 1: a room's box; 2: a tunnel's mesh
	TArray<int32> BoxRoom; BoxRoom.Init(-1, N * N);  // (a room box's tiles: which room)
	auto Kit = [G](int32 K) -> const FRDCaveRoom16& { return G->CaveRooms16[K]; };
	auto Footprint = [&](int32 K, FIntPoint At, int32 Turn, int32 Grow, TArray<FIntPoint>& Out)
	{
		const FRDCaveRoom16& E = Kit(K);
		Out.Reset();
		for (int32 J = -Grow; J < E.Size.Y + Grow; ++J)
			for (int32 I = -Grow; I < E.Size.X + Grow; ++I) Out.Add(At + RDC16Turn(FIntPoint(I, J) - E.Pivot, Turn));
	};
	auto Fits = [&](int32 K, FIntPoint At, int32 Turn, int32 Margin)
	{
		TArray<FIntPoint> F; Footprint(K, At, Turn, Margin, F);
		for (const FIntPoint& T : F)
		{
			if (T.X < 6 || T.Y < 6 || T.X >= N - 6 || T.Y >= N - 6) return false;          // (the border's strip: the portals' tunnels)
			if (Box[Idx(T)]) return false;
		}
		return true;
	};
	// an opening in the set's frame (cm, on the floor) and its way out of the room
	auto Joint = [&](int32 RI, int32 J, FVector& At, FVector2D& Out)
	{
		// (worked out once a room: its place, its way out, the room's floor by it (a scan of the room's tiles))
		if (CavePlaced16[RI].JAt.IsValidIndex(J)) { At = CavePlaced16[RI].JAt[J]; Out = CavePlaced16[RI].JOut[J]; return; }
		const FCavePlace16& Pl = CavePlaced16[RI];
		const FTransform& T = Kit(Pl.Kit).Joints[J];
		const FVector2D P = RDC16Turn(FVector2D(T.GetLocation().X, T.GetLocation().Y), Pl.Turn) + FVector2D((Pl.At.X + 0.5f) * S, (Pl.At.Y + 0.5f) * S);
		At = FVector(P, Pl.Z + T.GetLocation().Z);
		const float Yaw = FMath::DegreesToRadians(T.Rotator().Yaw + 90.f * Pl.Turn);
		Out = FVector2D(FMath::Cos(Yaw), FMath::Sin(Yaw));
		// (the tunnel starts at the room's own floor just inside the opening, not the arrow's height: the rim stood a step higher than
		// she can climb at the large room's openings)
		const FRDCaveRoom16& E = Kit(Pl.Kit);
		float BestD = FLT_MAX, Fz = 0.f;
		for (int32 J2 = 0; J2 < E.Size.Y; ++J2)
			for (int32 I2 = 0; I2 < E.Size.X; ++I2)
			{
				const int32 C = J2 * E.Size.X + I2;
				if (!E.Mask.IsValidIndex(C) || !E.Mask[C]) continue;
				const FIntPoint Tt = Pl.At + RDC16Turn(FIntPoint(I2, J2) - E.Pivot, Pl.Turn);
				const float D = FVector2D::Distance(FVector2D((Tt.X + 0.5f) * S, (Tt.Y + 0.5f) * S), P);
				if (D < BestD) { BestD = D; Fz = E.Floor.IsValidIndex(C) ? E.Floor[C] : 0.f; }
			}
		if (BestD < 3.f * S) At.Z = FMath::Max(At.Z, Pl.Z + Fz);
		if (CavePlaced16[RI].JAt.Num() == J) { CavePlaced16[RI].JAt.Add(At); CavePlaced16[RI].JOut.Add(Out); }
	};
	auto Lay = [&](int32 K, FIntPoint At, int32 Turn, float Z, ERDRoomKind Kind) -> int32
	{
		const FRDCaveRoom16& E = Kit(K);
		FCavePlace16 Pl; Pl.Kit = K; Pl.At = At; Pl.Turn = Turn; Pl.Z = Z; Pl.Used.Init(false, E.Joints.Num());
		FRoom Rm; Rm.Kind = Kind; Rm.Min = FIntPoint(N, N); Rm.Max = FIntPoint(-1, -1);
		const int32 RI = Rooms.Num();
		TArray<FIntPoint> F; Footprint(K, At, Turn, 0, F);
		for (const FIntPoint& T : F) if (In(T)) { Box[Idx(T)] = 1; BoxRoom[Idx(T)] = RI; }
		for (int32 J = 0; J < E.Size.Y; ++J)
			for (int32 I = 0; I < E.Size.X; ++I)
			{
				const int32 C = J * E.Size.X + I;
				if (!E.Mask.IsValidIndex(C) || !E.Mask[C]) continue;
				const FIntPoint T = At + RDC16Turn(FIntPoint(I, J) - E.Pivot, Turn);
				if (!In(T)) continue;
				Type[Idx(T)] = 1; Owner[Idx(T)] = (int16)RI; CaveZ16[Idx(T)] = Z + (E.Floor.IsValidIndex(C) ? E.Floor[C] : 0.f);
				Rm.Min = FIntPoint(FMath::Min(Rm.Min.X, T.X), FMath::Min(Rm.Min.Y, T.Y)); Rm.Max = FIntPoint(FMath::Max(Rm.Max.X, T.X + 1), FMath::Max(Rm.Max.Y, T.Y + 1));
			}
		Rm.Lane = At; Rm.Block = (At.Y / B) * (N / B) + At.X / B;
		Rooms.Add(Rm); CavePlaced16.Add(Pl);
		for (int32 J = 0; J < E.Joints.Num(); ++J) { FVector At2; FVector2D O2; Joint(RI, J, At2, O2); }
		return RI;
	};
	// ---- the rooms
	TArray<int32> Kinds; TArray<float> W; float Wsum = 0.f; int32 Stairs = -1;
	for (int32 K = 0; K < G->CaveRooms16.Num(); ++K)
	{
		if (G->CaveRooms16[K].Kind == FName(TEXT("stairs"))) { Stairs = K; continue; }
		if (G->CaveRooms16[K].Weight > 0.f) { Kinds.Add(K); W.Add(G->CaveRooms16[K].Weight); Wsum += G->CaveRooms16[K].Weight; }
	}
	auto Draw = [&]() { float U = R.FRand() * Wsum; for (int32 I = 0; I < Kinds.Num(); ++I) { U -= W[I]; if (U <= 0.f) return Kinds[I]; } return Kinds.Last(); };
	const int32 Want = FMath::Lerp(G->CaveRoomsPerSet16.X, G->CaveRoomsPerSet16.Y, FMath::Clamp((Tier - 1) / 4.f, 0.f, 1.f)) + R.RandRange(0, 1);
	if (bStart)
	{
		// (the start: the large room on the middle tile, where the level's player start and the way out stand)
		int32 Large = Kinds[0];
		for (int32 K : Kinds) if (G->CaveRooms16[K].Kind == FName(TEXT("large"))) Large = K;
		Lay(Large, FIntPoint(N / 2, N / 2), 0, 0.f, ERDRoomKind::Hall);
	}
	for (int32 Pick = 0; Pick < 400 && Rooms.Num() < Want; ++Pick)
	{
		const int32 K = Draw(), Turn = R.RandRange(0, 3);
		const FIntPoint At(R.RandRange(8, N - 9), R.RandRange(8, N - 9));
		const float Z = R.FRand() < 0.3f ? -G->CaveLevelDrop16 : 0.f;
		// (6 tiles round each box: a tunnel and its keep-out pass between two rooms; at 3 the rooms walled each other in)
		if (Fits(K, At, Turn, 6)) Lay(K, At, Turn, Z, ERDRoomKind::Crypt);
	}
	const int32 NumRooms = Rooms.Num();
	if (NumRooms == 0) { UE_LOG(LogRDCave16, Warning, TEXT("RDCAVE16 (%d,%d): no room fitted"), Coord.X, Coord.Y); return 0; }
	// ---- the joins: a tree over the rooms (nearest first), a fifth more as loops, then the portals
	struct FJoin { int32 A, Bn; bool bNeeded; };
	TArray<FJoin> Joins;
	{
		TArray<bool> In_; In_.Init(false, NumRooms); In_[0] = true;
		auto D2 = [&](int32 A, int32 Bn) { return (float)FIntPoint(CavePlaced16[A].At - CavePlaced16[Bn].At).SizeSquared(); };
		for (int32 Step = 1; Step < NumRooms; ++Step)
		{
			int32 BA = -1, BB = -1; float Best = FLT_MAX;
			for (int32 A = 0; A < NumRooms; ++A) if (In_[A]) for (int32 Bn = 0; Bn < NumRooms; ++Bn) if (!In_[Bn] && D2(A, Bn) < Best) { Best = D2(A, Bn); BA = A; BB = Bn; }
			In_[BB] = true; Joins.Add({ BA, BB, true });
		}
		TArray<TPair<float, FIntPoint>> Rest;
		for (int32 A = 0; A < NumRooms; ++A) for (int32 Bn = A + 1; Bn < NumRooms; ++Bn)
		{
			bool bTree = false; for (const FJoin& J : Joins) bTree |= (J.A == A && J.Bn == Bn) || (J.A == Bn && J.Bn == A);
			if (!bTree) Rest.Add(TPair<float, FIntPoint>(D2(A, Bn), FIntPoint(A, Bn)));
		}
		Rest.Sort([](const TPair<float, FIntPoint>& X, const TPair<float, FIntPoint>& Y) { return X.Key < Y.Key; });
		const int32 Loops = FMath::CeilToInt(G->CaveLoopShare16 * (NumRooms - 1));
		for (int32 I = 0; I < Loops && I < Rest.Num(); ++I) Joins.Add({ Rest[I].Value.X, Rest[I].Value.Y, false });
	}
	// (the portals: rows of the blocks 1, 3, 5 as the dungeon's, one a side by a hash of the border, so both sets agree)
	for (int32 Sd = 0; Sd < 4; ++Sd)
	{
		static const FIntPoint SideDir[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };
		const FIntPoint Other = Coord + SideDir[Sd];
		const FIntPoint Lo(FMath::Min(Coord.X, Other.X), FMath::Min(Coord.Y, Other.Y));
		const uint32 H = HashCombine(GetTypeHash(Lo), GetTypeHash(Sd < 2 ? 1 : 2)) ^ (uint32)G->StartSeed;
		// (one a side: four rooms have about 13 openings; two a side took 7 of them and left the rooms' own joins none, rooms cut off)
		const int32 Along = (1 + 2 * (H % 3)) * B + B / 2;
		const FIntPoint P = Sd == 0 ? FIntPoint(0, Along) : Sd == 1 ? FIntPoint(N - 1, Along) : Sd == 2 ? FIntPoint(Along, 0) : FIntPoint(Along, N - 1);
		if (!Portals.Contains(P)) Portals.Add(P);
	}
	// ---- the tunnels
	auto TunnelKit = [&](bool bPortal) -> int32
	{
		if (bPortal) { for (int32 K = 0; K < G->CaveTunnels16.Num(); ++K) if (G->CaveTunnels16[K].Kind == FName(TEXT("medium"))) return K; return 0; }
		float Ws = 0.f; for (const FRDCaveTunnel16& T : G->CaveTunnels16) Ws += T.Weight;
		float U = R.FRand() * Ws;
		for (int32 K = 0; K < G->CaveTunnels16.Num(); ++K) { U -= G->CaveTunnels16[K].Weight; if (U <= 0.f) return K; }
		return 0;
	};
	// (the kits by size: small 0, medium 1, large 2; a room's rank by its kind, the stairs' medium)
	auto KitRank = [&](int32 TK) { const FName K = G->CaveTunnels16[TK].Kind; return K == FName(TEXT("small")) ? 0 : K == FName(TEXT("medium")) ? 1 : 2; };
	// (the smallest kit the set draws: 945 gives the kit's small tunnel no weight (its walkable way 2 to 3 m wide closed up where it bent:
	// she stuck on its walls); every tunnel is at least that one)
	int32 SmallKit = -1;
	for (int32 K = 0; K < G->CaveTunnels16.Num(); ++K) if (G->CaveTunnels16[K].Weight > 0.f && (SmallKit < 0 || KitRank(K) < KitRank(SmallKit))) SmallKit = K;
	if (SmallKit < 0) SmallKit = 0;
	auto SizeRank = [&](int32 RI) { const FName K = G->CaveRooms16[CavePlaced16[RI].Kit].Kind; return K == FName(TEXT("small")) ? 0 : K == FName(TEXT("large")) ? 2 : 1; };
	auto CapKit = [&](int32 TK, int32 Rank)
	{
		Rank = FMath::Max(Rank, KitRank(SmallKit));
		if (KitRank(TK) <= Rank) return TK;
		int32 Best = SmallKit; for (int32 K = 0; K < G->CaveTunnels16.Num(); ++K) if (G->CaveTunnels16[K].Weight > 0.f && KitRank(K) <= Rank && KitRank(K) > KitRank(Best)) Best = K;
		return Best;
	};
	auto MeshHalf = [&](int32 TK) { const UStaticMesh* M = G->CaveTunnels16[TK].Mesh; return M ? (float)M->GetBoundingBox().GetExtent().Y : 600.f; };
	// the best free opening of a room toward a point (none free: the best taken one, if allowed)
	auto PickJoint = [&](int32 RI, const FVector2D& Toward, bool bReuse) -> int32
	{
		int32 Best = -1; float BestS = -FLT_MAX;
		for (int32 J = 0; J < CavePlaced16[RI].Used.Num(); ++J)
		{
			if (CavePlaced16[RI].Used[J] && !bReuse) continue;
			FVector At; FVector2D Out; Joint(RI, J, At, Out);
			const FVector2D D = (Toward - FVector2D(At)).GetSafeNormal();
			const float Sc = FVector2D::DotProduct(Out, D) - (CavePlaced16[RI].Used[J] ? 2.f : 0.f);
			if (Sc > BestS) { BestS = Sc; Best = J; }
		}
		return Best;
	};
	// a route over the tiles from A to Bt, round the rooms' boxes and the tunnels' meshes (grown by this tunnel's half-width)
	TArray<uint8> Block;          // (the last route's keep-out: the straightening's sight lines read it)
	TArray<int32> RunOf; RunOf.Init(-1, N * N);          // (a tunnel mesh's tiles: which run)
	TArray<FIntPoint> RunEnds;                            // (each run's two places, as Dig's From and To)
	int32 RouteFrom = -2, RouteTo = -2;                   // (the places of the tunnel being routed)
	auto Route = [&](FIntPoint A, FIntPoint Bt, int32 Grow, int32 GrowTunnel, TArray<FIntPoint>& Out) -> bool
	{
		Out.Reset();
		if (!In(A) || !In(Bt)) return false;
		// (the keep-out: every room's box and every tunnel's mesh grown by Grow tiles, by summed-area tables (a square's count in four
		// reads; growing each tile by hand was most of the plan's time). Only a tunnel from the same room may come near this one, and
		// only by that room: any other crossed it, and their meshes cut each other open to the void)
		TArray<uint8> M0, MA, MB, MAB; M0.Init(0, N * N); MA.Init(0, N * N); MB.Init(0, N * N); MAB.Init(0, N * N);
		for (int32 T = 0; T < N * N; ++T)
		{
			if (!Box[T]) continue;
			if (Box[T] == 2 && RunEnds.IsValidIndex(RunOf[T]))
			{
				const FIntPoint E2 = RunEnds[RunOf[T]];
				const bool bShareA = RouteFrom >= 0 && (E2.X == RouteFrom || E2.Y == RouteFrom), bShareB = RouteTo >= 0 && (E2.X == RouteTo || E2.Y == RouteTo);
				if (bShareA && bShareB) { MAB[T] = 1; continue; }
				if (bShareA) { MA[T] = 1; continue; }
				if (bShareB) { MB[T] = 1; continue; }
			}
			M0[T] = 1;
		}
		auto Grown = [&](const TArray<uint8>& Mk, int32 G2, TArray<uint8>& Out2)
		{
			TArray<int32> Sat; Sat.Init(0, (N + 1) * (N + 1));
			for (int32 Y = 0; Y < N; ++Y) for (int32 X = 0; X < N; ++X)
				Sat[(Y + 1) * (N + 1) + X + 1] = Mk[Y * N + X] + Sat[Y * (N + 1) + X + 1] + Sat[(Y + 1) * (N + 1) + X] - Sat[Y * (N + 1) + X];
			Out2.Init(0, N * N);
			for (int32 Y = 0; Y < N; ++Y) for (int32 X = 0; X < N; ++X)
			{
				const int32 X0 = FMath::Max(X - G2, 0), Y0 = FMath::Max(Y - G2, 0), X1 = FMath::Min(X + G2, N - 1) + 1, Y1 = FMath::Min(Y + G2, N - 1) + 1;
				Out2[Y * N + X] = (Sat[Y1 * (N + 1) + X1] - Sat[Y0 * (N + 1) + X1] - Sat[Y1 * (N + 1) + X0] + Sat[Y0 * (N + 1) + X0]) > 0;
			}
		};
		TArray<uint8> G0, GA, GB, GAB;
		Grown(M0, Grow, G0); Grown(MA, GrowTunnel, GA); Grown(MB, GrowTunnel, GB); Grown(MAB, GrowTunnel, GAB);
		Block.Init(0, N * N);
		for (int32 Y = 0; Y < N; ++Y) for (int32 X = 0; X < N; ++X)
		{
			const int32 T = Y * N + X;
			const bool bNearA = FIntPoint(FIntPoint(X, Y) - A).Size() <= Grow + 2, bNearB = FIntPoint(FIntPoint(X, Y) - Bt).Size() <= Grow + 2;
			Block[T] = G0[T] || (GA[T] && !bNearA) || (GB[T] && !bNearB) || (GAB[T] && !bNearA && !bNearB);
		}
		// (the ends stand clear of their own rooms by then; the border's strip is open only at the ends)
		Block[Idx(A)] = 0; Block[Idx(Bt)] = 0;
		TArray<float> Cost; Cost.Init(FLT_MAX, N * N); TArray<int32> Prev; Prev.Init(-1, N * N);
		typedef TPair<float, int32> FQ;
		TArray<FQ> Heap; Heap.HeapPush(FQ(0.f, Idx(A)), [](const FQ& X, const FQ& Y) { return X.Key < Y.Key; });
		Cost[Idx(A)] = 0.f;
		while (Heap.Num())
		{
			FQ Q; Heap.HeapPop(Q, [](const FQ& X, const FQ& Y) { return X.Key < Y.Key; });
			const FIntPoint T(Q.Value % N, Q.Value / N);
			if (T == Bt) break;
			const float Ct = Cost[Q.Value];
			for (int32 D = 0; D < 8; ++D)
			{
				const FIntPoint Nb = T + RDC16Dir8[D];
				if (!In(Nb) || Block[Idx(Nb)]) continue;
				if ((Nb.X < 2 || Nb.Y < 2 || Nb.X >= N - 2 || Nb.Y >= N - 2) && FIntPoint(Nb - Bt).Size() > 6 && FIntPoint(Nb - A).Size() > 6) continue;
				const float Step = (D < 4 ? 1.f : 1.4142f) * (1.f + 1.0f * RDC16Noise(Seed, Nb.X, Nb.Y));
				const float H = FVector2D::Distance(FVector2D(Nb), FVector2D(Bt));
				if (Ct + Step < Cost[Idx(Nb)]) { Cost[Idx(Nb)] = Ct + Step; Prev[Idx(Nb)] = Q.Value; Heap.HeapPush(FQ(Ct + Step + H, Idx(Nb)), [](const FQ& X, const FQ& Y) { return X.Key < Y.Key; }); }
			}
		}
		if (Prev[Idx(Bt)] < 0 && A != Bt) return false;
		for (int32 C = Idx(Bt); ; C = Prev[C]) { Out.Insert(FIntPoint(C % N, C / N), 0); if (C == Idx(A)) break; }
		return true;
	};
	int32 FailOut = 0, FailRoute = 0, FailJoint = 0, StairsTried = 0, StairsNoRoom = 0, FailCross = 0, FailBend = 0;
	// lay a tunnel: from an end (point, way into the tunnel) to the other (point, way into the tunnel); marks its mesh's tiles in Box
	bool bDry = false;          // (a dry run: every check made, nothing laid)
	auto Dig = [&](const FVector& PA, const FVector2D& OutA, const FVector& PB, const FVector2D& OutB, int32 TK, int32 From, int32 To, bool bEndA, bool bEndB) -> bool
	{
		const FRDCaveTunnel16& E = G->CaveTunnels16[TK];
		const float Half = MeshHalf(TK);
		const int32 Grow = FMath::CeilToInt(Half / S);
		// (out of each room straight along its opening until clear of its box by the tunnel's half-width)
		auto Clear = [&](const FVector& P, const FVector2D& Out, bool bRoom) -> FVector
		{
			if (!bRoom) return P + FVector(Out * S * 2.f, 0.f);
			FVector Q = P;
			for (int32 I = 0; I < 40; ++I)
			{
				Q += FVector(Out * S, 0.f);
				const FIntPoint T(FMath::FloorToInt(Q.X / S), FMath::FloorToInt(Q.Y / S));
				bool bFree = In(T);
				for (int32 Dy = -Grow; bFree && Dy <= Grow; ++Dy) for (int32 Dx = -Grow; bFree && Dx <= Grow; ++Dx) { const FIntPoint U(T.X + Dx, T.Y + Dy); bFree = !In(U) || Box[Idx(U)] != 1; }
				if (bFree) return Q;
			}
			return Q;
		};
		const FVector CA = Clear(PA, OutA, bEndA), CB = Clear(PB, OutB, bEndB);
		TArray<FIntPoint> Path;
		RouteFrom = From; RouteTo = To;
		// (the straight legs out of the openings must not run through another tunnel)
		auto LegClear = [&](const FVector& U, const FVector& V)
		{
			const int32 M = FMath::Max(1, FMath::CeilToInt(FVector2D::Distance(FVector2D(U), FVector2D(V)) / (S * 0.5f)));
			for (int32 K = 0; K <= M; ++K)
			{
				const FVector Q = FMath::Lerp(U, V, (float)K / M);
				const FIntPoint T(FMath::FloorToInt(Q.X / S), FMath::FloorToInt(Q.Y / S));
				if (In(T) && Box[Idx(T)] == 2 && RunEnds.IsValidIndex(RunOf[Idx(T)]))
				{
					const FIntPoint E2 = RunEnds[RunOf[Idx(T)]];
					if (E2.X != From && E2.Y != From && E2.X != To && E2.Y != To) return false;
				}
			}
			return true;
		};
		if (!LegClear(PA, CA) || !LegClear(PB, CB)) { ++FailRoute; return false; }
		if (!In(FIntPoint(FMath::FloorToInt(CA.X / S), FMath::FloorToInt(CA.Y / S))) || !In(FIntPoint(FMath::FloorToInt(CB.X / S), FMath::FloorToInt(CB.Y / S)))) { ++FailOut; return false; }
		// (never through another tunnel's keep-out: shrunk, a small tunnel ran 20 m inside a large one's walls and she stuck on them;
		// a crowded join is tried again with the small tunnel by its caller)
		if (!Route(FIntPoint(FMath::FloorToInt(CA.X / S), FMath::FloorToInt(CA.Y / S)), FIntPoint(FMath::FloorToInt(CB.X / S), FMath::FloorToInt(CB.Y / S)), Grow, Grow, Path)) { ++FailRoute; return false; }
		// the route pulled straight where it can see ahead (its tiles' sight lines clear of the keep-out), then its corners rounded
		// (a radius of 1.6 times the tunnel's half-width, 12 m at least); the opening, out of it, the corners, into the other, the
		// other opening; its height eased from one end's floor to the other's
		auto Sees = [&](FIntPoint U, FIntPoint V)
		{
			const FVector2D Du = FVector2D(V - U); const int32 M = FMath::Max(1, FMath::CeilToInt(Du.Size() * 4.f));
			for (int32 K = 1; K < M; ++K)
			{
				const FVector2D Q = FVector2D(U) + Du * ((float)K / M);
				const FIntPoint T(FMath::RoundToInt(Q.X), FMath::RoundToInt(Q.Y));
				if (!In(T) || Block[Idx(T)]) return false;
			}
			return true;
		};
		TArray<FVector2D> Corners; Corners.Add(FVector2D(PA)); Corners.Add(FVector2D(CA));
		for (int32 I = 0; I + 1 < Path.Num(); )
		{
			int32 J = Path.Num() - 1;
			while (J > I + 1 && !Sees(Path[I], Path[J])) --J;
			if (J < Path.Num() - 1) Corners.Add(FVector2D((Path[J].X + 0.5f) * S, (Path[J].Y + 0.5f) * S));
			I = J;
		}
		Corners.Add(FVector2D(CB)); Corners.Add(FVector2D(PB));
		TArray<FVector2D> Flat; RDC16Round(Corners, FMath::Max(2.f * Half, 1300.f), 50.f, Flat);
		// (a line that doubles back rounds to nothing a tunnel can follow (the first side tunnels to nowhere: a corner of 180 degrees gave
		// no number, and the sampling below grew without end until the editor ran out of memory))
		for (const FVector2D& Q : Flat) if (!FMath::IsFinite(Q.X) || !FMath::IsFinite(Q.Y) || FMath::Abs(Q.X) > 1e6f || FMath::Abs(Q.Y) > 1e6f) { ++FailBend; return false; }
		TArray<FVector> Line; Line.Reserve(Flat.Num());
		for (const FVector2D& Q : Flat) if (Line.Num() == 0 || FVector2D::Distance(FVector2D(Line.Last()), Q) > 1.f) Line.Add(FVector(Q, 0.f));
		// (straight runs sampled every 50 cm too: the tiles, the lights and the tests walk the line)
		{
			TArray<FVector> Dense;
			for (int32 I = 0; I + 1 < Line.Num(); ++I)
			{
				const int32 M = FMath::Max(1, FMath::CeilToInt(FVector::Dist(Line[I], Line[I + 1]) / 50.f));
				for (int32 K = 0; K < M; ++K) Dense.Add(FMath::Lerp(Line[I], Line[I + 1], (float)K / M));
			}
			if (Line.Num()) Dense.Add(Line.Last());
			Line = MoveTemp(Dense);
		}
		float L = 0.f; TArray<float> Acc; Acc.Add(0.f);
		for (int32 I = 1; I < Line.Num(); ++I) { L += FVector2D::Distance(FVector2D(Line[I]), FVector2D(Line[I - 1])); Acc.Add(L); }
		for (int32 I = 0; I < Line.Num(); ++I) Line[I].Z = FMath::Lerp(PA.Z, PB.Z, FMath::SmoothStep(0.f, 1.f, L > 0.f ? Acc[I] / L : 0.f));
		// (no bend tighter than the half-width: a corner whose legs were too short to round pinched the kit's walls shut)
		for (int32 I = 12; I + 12 < Line.Num(); I += 4)
		{
			const FVector2D A2(Line[I - 12]), B2(Line[I]), C2(Line[I + 12]);
			const float Ab = FVector2D::Distance(A2, B2), Bc = FVector2D::Distance(B2, C2), Ac = FVector2D::Distance(A2, C2);
			const float Area2 = FMath::Abs(FVector2D::CrossProduct(B2 - A2, C2 - A2));
			if (Area2 > 1.f && Ab * Bc * Ac / (2.f * Area2) < 1.f * Half) { ++FailBend; return false; }
		}
		// (nor through the ground a cap will take: an opening of any room no tunnel has taken gets the kit's cap, 10 m of rock out from
		// the wall, and a tunnel past it ran into it)
		for (int32 RI2 = 0; RI2 < CavePlaced16.Num(); ++RI2)
			for (int32 J2 = 0; CavePlaced16[RI2].Kit >= 0 && J2 < CavePlaced16[RI2].Used.Num(); ++J2)
			{
				if (CavePlaced16[RI2].Used[J2]) continue;
				FVector Jp; FVector2D Jo; Joint(RI2, J2, Jp, Jo);
				if (FVector2D::Distance(FVector2D(Jp), FVector2D(PA)) < 300.f || FVector2D::Distance(FVector2D(Jp), FVector2D(PB)) < 300.f) continue;
				const FVector2D Cc = FVector2D(Jp) + Jo * 500.f;
				for (int32 I = 0; I < Line.Num(); I += 4)
					if (FVector2D::Distance(FVector2D(Line[I]), Cc) < Half + 700.f) { ++FailCross; return false; }
			}
		// (the line as it will be laid, at its mesh's half-width, must stay off every other tunnel's mesh and every room's box but the
		// two it joins; near one of its rooms (15 m) a tunnel from that room may come close: the overhead picture showed tunnels
		// crossing whatever way the route came)
		for (int32 I = 0; I < Line.Num(); I += 2)
		{
			const FVector& P = Line[I];
			const bool bNearA = FVector2D::Distance(FVector2D(P), FVector2D(PA)) < 1500.f, bNearB = FVector2D::Distance(FVector2D(P), FVector2D(PB)) < 1500.f;
			const int32 R0 = FMath::CeilToInt(Half / S);
			const FIntPoint C(FMath::FloorToInt(P.X / S), FMath::FloorToInt(P.Y / S));
			for (int32 Dy = -R0; Dy <= R0; ++Dy) for (int32 Dx = -R0; Dx <= R0; ++Dx)
			{
				const FIntPoint T(C.X + Dx, C.Y + Dy);
				if (!In(T) || FVector2D::Distance(FVector2D((T.X + 0.5f) * S, (T.Y + 0.5f) * S), FVector2D(P)) > Half) continue;
				const int32 Ti = Idx(T);
				if (Box[Ti] == 1 && BoxRoom[Ti] != From && BoxRoom[Ti] != To) { ++FailCross; return false; }
				if (Box[Ti] == 2 && RunEnds.IsValidIndex(RunOf[Ti]))
				{
					const FIntPoint E2 = RunEnds[RunOf[Ti]];
					const bool bOk = (bNearA && From >= 0 && (E2.X == From || E2.Y == From)) || (bNearB && To >= 0 && (E2.X == To || E2.Y == To));
					if (!bOk) { ++FailCross; return false; }
				}
			}
		}
		if (bDry) return true;
		FCaveRun16 Run; Run.Kit = TK; Run.Points = Line; Run.From = From; Run.To = To; Run.Length = L;
		// (a tunnel is a room entry of its own (Junction), with an empty kit place beside it: Rooms and CavePlaced16 stay in step,
		// whatever stairs are laid after it)
		const int32 TI = Rooms.Num(); Run.Room = TI;
		FRoom Rm; Rm.Kind = ERDRoomKind::Junction; Rm.Min = FIntPoint(N, N); Rm.Max = FIntPoint(-1, -1);
		// (its walkable tiles: within the floor's half-width of the line, or 2.15 m, so the tiles stay joined along a diagonal; its
		// mesh's tiles go into the keep-out for the next tunnels)
		// (2.15 m whatever the tunnel: wider, the tile paths hugged the rocky feet of the walls on the bends; narrower, a diagonal's
		// tiles touched only at their corners)
		const float Walk = 215.f;
		for (int32 I = 0; I < Line.Num(); I += 2)
		{
			const FVector& P = Line[I];
			const int32 R0 = FMath::CeilToInt(Half / S) + 1;
			const FIntPoint C(FMath::FloorToInt(P.X / S), FMath::FloorToInt(P.Y / S));
			for (int32 Dy = -R0; Dy <= R0; ++Dy) for (int32 Dx = -R0; Dx <= R0; ++Dx)
			{
				const FIntPoint T(C.X + Dx, C.Y + Dy);
				if (!In(T)) continue;
				const float D = FVector2D::Distance(FVector2D((T.X + 0.5f) * S, (T.Y + 0.5f) * S), FVector2D(P));
				if (D <= Half && Box[Idx(T)] == 0) { Box[Idx(T)] = 2; RunOf[Idx(T)] = RunEnds.Num(); }
				// (a tunnel tile beside one of its rooms' floor tiles only at the opening: elsewhere the room's wall stands between them,
				// and a path crossing there held her on the wall's ledge beside the large room's opening)
				bool bBesideRoom = false;
				for (int32 Dd = 0; Dd < 4 && !bBesideRoom; ++Dd)
				{
					static const FIntPoint N4[4] = { FIntPoint(1, 0), FIntPoint(-1, 0), FIntPoint(0, 1), FIntPoint(0, -1) };
					const FIntPoint U = T + N4[Dd];
					bBesideRoom = In(U) && Owner[Idx(U)] >= 0 && (Owner[Idx(U)] == From || Owner[Idx(U)] == To);
				}
				const FVector2D Tc((T.X + 0.5f) * S, (T.Y + 0.5f) * S);
				// (by the opening they meet (4.5 m: the opening's point often lies on the room's own floor, its first tile out beside it);
				// where the room's floor stops short of the opening the bridge below joins them)
				// (in the opening's own way: within 1.6 m of the line out of it, at most 4.5 m along; 1.7 m off it she stood on the wall's
				// ledge)
				if (bBesideRoom) continue;          // (the openings' chains below join them)
				if (D <= Walk && Type[Idx(T)] == 0)
				{
					Type[Idx(T)] = 1; Owner[Idx(T)] = (int16)TI; CaveZ16[Idx(T)] = P.Z;
					Rm.Min = FIntPoint(FMath::Min(Rm.Min.X, T.X), FMath::Min(Rm.Min.Y, T.Y)); Rm.Max = FIntPoint(FMath::Max(Rm.Max.X, T.X + 1), FMath::Max(Rm.Max.Y, T.Y + 1));
				}
			}
		}
		// (each end at a room: the opening's own line, 6 m into the room to 6 m out, laid as a 4-joined chain of tiles: the one way
		// through the opening, where the tunnel's tiles and the room's meet; beside the opening they do not (the wall stands there))
		for (int32 End = 0; End < 2; ++End)
		{
			const int32 RoomI = End == 0 ? From : To; const FVector& P = End == 0 ? PA : PB; const FVector2D& O = End == 0 ? OutA : OutB;
			if (RoomI < 0 || !CavePlaced16.IsValidIndex(RoomI) || CavePlaced16[RoomI].Kit < 0) continue;
			FIntPoint Prev(INT_MIN, INT_MIN);
			for (float Al = -600.f; Al <= 600.f; Al += 25.f)
			{
				const FVector2D Q = FVector2D(P) + O * Al;
				const FIntPoint T(FMath::FloorToInt(Q.X / S), FMath::FloorToInt(Q.Y / S));
				if (T == Prev) continue;
				TArray<FIntPoint, TInlineAllocator<2>> Add;
				if (Prev.X != INT_MIN && Prev.X != T.X && Prev.Y != T.Y) Add.Add(FIntPoint(T.X, Prev.Y));          // (a diagonal step's corner)
				Add.Add(T);
				for (const FIntPoint& U : Add)
					if (In(U) && Type[Idx(U)] == 0)
					{
						Type[Idx(U)] = 1; Owner[Idx(U)] = (int16)TI; CaveZ16[Idx(U)] = P.Z;
						Rm.Min = FIntPoint(FMath::Min(Rm.Min.X, U.X), FMath::Min(Rm.Min.Y, U.Y)); Rm.Max = FIntPoint(FMath::Max(Rm.Max.X, U.X + 1), FMath::Max(Rm.Max.Y, U.Y + 1));
					}
				Prev = T;
			}
		}
		if (Rm.Max.X < 0) { Rm.Min = FIntPoint(FMath::FloorToInt(PA.X / S), FMath::FloorToInt(PA.Y / S)); Rm.Max = Rm.Min + FIntPoint(1, 1); }
		Rm.Lane = FIntPoint((Rm.Min.X + Rm.Max.X) / 2, (Rm.Min.Y + Rm.Max.Y) / 2);
		Rooms.Add(Rm); CavePlaced16.Add(FCavePlace16()); CaveRuns16.Add(Run); RunEnds.Add(FIntPoint(From, To));
		return true;
	};
	auto JoinRooms = [&](int32 A, int32 Bn, bool bNeeded, int32 ForceA = -1, int32 ForceB = -1) -> bool
	{
		const FVector2D Ca((CavePlaced16[A].At.X + 0.5f) * S, (CavePlaced16[A].At.Y + 0.5f) * S), Cb((CavePlaced16[Bn].At.X + 0.5f) * S, (CavePlaced16[Bn].At.Y + 0.5f) * S);
		const int32 JA = ForceA >= 0 ? ForceA : PickJoint(A, Cb, bNeeded), JB = ForceB >= 0 ? ForceB : PickJoint(Bn, Ca, bNeeded);
		if (JA < 0 || JB < 0) { ++FailJoint; return false; }
		FVector PA, PB; FVector2D OA, OB; Joint(A, JA, PA, OA); Joint(Bn, JB, PB, OB);
		// (no bigger than the smaller room it joins: a small room's openings are 12 m apart, two medium tunnels from them crossed)
		const int32 TK = CapKit(TunnelKit(false), FMath::Min(SizeRank(A), SizeRank(Bn)));
		// (two levels: the kit's stairs between them where they fit, its foot toward the lower room)
		if (Stairs >= 0 && FMath::Abs(CavePlaced16[A].Z - CavePlaced16[Bn].Z) > 1.f)
		{
			const int32 Lo = CavePlaced16[A].Z < CavePlaced16[Bn].Z ? A : Bn, Hi = Lo == A ? Bn : A;
			const FVector2D Way = FVector2D(CavePlaced16[Hi].At - CavePlaced16[Lo].At).GetSafeNormal();
			// (the stairs climb along their +Y: the turn that points it nearest the way up)
			int32 Turn = 0; float Bd = -2.f;
			for (int32 K = 0; K < 4; ++K) { const float D = FVector2D::DotProduct(RDC16Turn(FVector2D(0, 1), K), Way); if (D > Bd) { Bd = D; Turn = K; } }
			++StairsTried;
			for (int32 Try = 0; Try < 40; ++Try)
			{
				// (along the line between the two rooms, a little to either side of it)
				const FVector2D On = FMath::Lerp(FVector2D(CavePlaced16[Lo].At), FVector2D(CavePlaced16[Hi].At), R.FRandRange(0.25f, 0.75f));
				const FIntPoint At(FMath::RoundToInt(On.X) + R.RandRange(-6, 6), FMath::RoundToInt(On.Y) + R.RandRange(-6, 6));
				if (!Fits(Stairs, At, Turn, 1)) { ++StairsNoRoom; continue; }
				const int32 SI = Lay(Stairs, At, Turn, CavePlaced16[Lo].Z, ERDRoomKind::Junction);
				// (its two openings: the first at the foot, the second at the top)
				FVector Pf, Pt; FVector2D Of, Ot; Joint(SI, 0, Pf, Of); Joint(SI, 1, Pt, Ot);
				const int32 JL = Lo == A ? JA : JB, JH = Hi == A ? JA : JB;
				FVector PL, PH; FVector2D OL, OH; Joint(Lo, JL, PL, OL); Joint(Hi, JH, PH, OH);
				// (both its tunnels tried dry first: stairs whose tunnels then failed stayed as dead ends taking the set's room (a plan
				// had five); kept only when both are laid, else taken up again)
				bDry = true;
				const int32 K1 = Dig(PL, OL, Pf, Of, TK, Lo, SI, true, true) ? TK : (TK != SmallKit && Dig(PL, OL, Pf, Of, SmallKit, Lo, SI, true, true)) ? SmallKit : -1;
				const int32 K2 = Dig(Pt, Ot, PH, OH, TK, SI, Hi, true, true) ? TK : (TK != SmallKit && Dig(Pt, Ot, PH, OH, SmallKit, SI, Hi, true, true)) ? SmallKit : -1;
				bDry = false;
				if (K1 >= 0 && K2 >= 0 && Dig(PL, OL, Pf, Of, K1, Lo, SI, true, true))
				{
					// (the second checked again with the first laid (the dry runs saw neither): failed, the join is not made, the top's
					// opening is capped, and the caller tries the rooms another way)
					CavePlaced16[Lo].Used[JL] = true; CavePlaced16[SI].Used[0] = true;
					if (!Dig(Pt, Ot, PH, OH, K2, SI, Hi, true, true)) return false;
					CavePlaced16[Hi].Used[JH] = CavePlaced16[SI].Used[1] = true;
					return true;
				}
				// (taken up: the last room laid, its tiles cleared)
				for (int32 T = 0; T < N * N; ++T)
				{
					if (BoxRoom[T] == SI) { Box[T] = 0; BoxRoom[T] = -1; }
					if (Owner[T] == SI) { Type[T] = 0; Owner[T] = -1; CaveZ16[T] = 0.f; }
				}
				Rooms.Pop(); CavePlaced16.Pop();
			}
		}
		if (!Dig(PA, OA, PB, OB, TK, A, Bn, true, true) && (TK == SmallKit || !Dig(PA, OA, PB, OB, SmallKit, A, Bn, true, true))) return false;
		CavePlaced16[A].Used[JA] = CavePlaced16[Bn].Used[JB] = true;
		return true;
	};
	int32 Failed = 0;
	// (every room joined to the start's group: a tree join that found no way is replaced by the nearest other pair across the
	// two groups)
	TArray<int32> Group; for (int32 I = 0; I < NumRooms; ++I) Group.Add(I);
	auto Root = [&Group](int32 I) { while (Group[I] != I) I = Group[I] = Group[Group[I]]; return I; };
	for (const FJoin& J : Joins) if (J.bNeeded) { if (JoinRooms(J.A, J.Bn, true)) Group[Root(J.A)] = Root(J.Bn); else ++Failed; }
	for (int32 Pass = 0; Pass < NumRooms; ++Pass)
	{
		TArray<TPair<float, FIntPoint>> Cands;
		for (int32 A = 0; A < NumRooms; ++A) for (int32 Bn = 0; Bn < NumRooms; ++Bn)
			if (Root(A) == Root(0) && Root(Bn) != Root(0)) Cands.Add(TPair<float, FIntPoint>((float)FIntPoint(CavePlaced16[A].At - CavePlaced16[Bn].At).SizeSquared(), FIntPoint(A, Bn)));
		if (Cands.Num() == 0) break;
		Cands.Sort([](const TPair<float, FIntPoint>& X, const TPair<float, FIntPoint>& Y) { return X.Key < Y.Key; });
		bool bJoined = false;
		// (the nearest pairs first, each with its best openings, then every pair of openings of the nearest few)
		for (const TPair<float, FIntPoint>& C : Cands) if (JoinRooms(C.Value.X, C.Value.Y, true)) { Group[Root(C.Value.Y)] = Root(C.Value.X); bJoined = true; break; }
		for (int32 CI = 0; !bJoined && CI < FMath::Min(Cands.Num(), 4); ++CI)
		{
			const int32 A = Cands[CI].Value.X, Bn = Cands[CI].Value.Y;
			for (int32 JA = 0; !bJoined && JA < CavePlaced16[A].Used.Num(); ++JA)
				for (int32 JB = 0; !bJoined && JB < CavePlaced16[Bn].Used.Num(); ++JB)
					if (JoinRooms(A, Bn, true, JA, JB)) { Group[Root(Bn)] = Root(A); bJoined = true; }
		}
		if (!bJoined) break;
	}
	// (a room no way reaches is left out of the game: no tiles to walk, no monsters, not counted for the tier; its openings capped)
	int32 Cut = 0;
	for (int32 I = 0; I < NumRooms; ++I)
	{
		if (Root(I) == Root(0)) continue;
		++Cut; Rooms[I].Kind = ERDRoomKind::Junction;
		for (int32 T = 0; T < N * N; ++T) if (Owner[T] == I) { Type[T] = 0; Owner[T] = -1; }
	}
	// (and a tunnel or stairs between cut rooms: an island of tiles the paths, the map and the discovery would still have seen)
	for (const FCaveRun16& Run : CaveRuns16)
	{
		// (a room by its group; a stairs (laid after the rooms) by the room at its tunnels' other ends; a portal never)
		auto KeptRoom = [&](int32 E) { return E >= 0 && E < NumRooms && Root(E) == Root(0); };
		auto Kept = [&](int32 E)
		{
			if (E < NumRooms) return KeptRoom(E);
			for (const FCaveRun16& R2 : CaveRuns16) if ((R2.From == E && KeptRoom(R2.To)) || (R2.To == E && KeptRoom(R2.From))) return true;
			return false;
		};
		if (Kept(Run.From) || Kept(Run.To)) continue;
		for (int32 T = 0; T < N * N; ++T) if (Owner[T] == Run.Room) { Type[T] = 0; Owner[T] = -1; }
	}
	// (the portals after the rooms' joins: a tunnel is a wall, and four portal tunnels laid first cut the set into quarters the
	// joins could not cross)
	// the portals: a tunnel from the nearest room to the border, straight across it at the shallower set's floor
	for (int32 Pt = 0; Pt < Portals.Num(); ++Pt)
	{
		const FIntPoint P = Portals[Pt];
		FIntPoint D(0, 0); if (P.X == 0) D.X = -1; else if (P.X == N - 1) D.X = 1; else if (P.Y == 0) D.Y = -1; else D.Y = 1;
		const FVector2D Out(D.X, D.Y);
		const float Here = G->SectionFloorZ(Coord), There = G->SectionFloorZ(Coord + D);
		// (a metre past the border: the two sets' tunnels overlap there as the kit's pieces overlap each other, no seam)
		const FVector Border((P.X + 0.5f) * S + D.X * (S * 0.5f + 100.f), (P.Y + 0.5f) * S + D.Y * (S * 0.5f + 100.f), FMath::Max(Here, There) - Here);
		// (every reachable room, nearest first, each of its openings, the free ones and the best-facing first: a portal with no tunnel
		// is a border the cave cannot be left by)
		TArray<int32> Order;
		for (int32 RI = 0; RI < NumRooms; ++RI) if (Rooms[RI].Kind != ERDRoomKind::Junction) Order.Add(RI);
		Order.Sort([&](int32 X, int32 Y) { return FVector2D::Distance(FVector2D(CavePlaced16[X].At), FVector2D(P)) < FVector2D::Distance(FVector2D(CavePlaced16[Y].At), FVector2D(P)); });
		bool bDug = false;
		for (int32 Oi = 0; !bDug && Oi < FMath::Min(Order.Num(), 3); ++Oi)
		{
			const int32 RI = Order[Oi];
			TArray<TPair<float, int32>> Js;
			for (int32 J = 0; J < CavePlaced16[RI].Used.Num(); ++J)
			{
				FVector At; FVector2D Ou; Joint(RI, J, At, Ou);
				Js.Add(TPair<float, int32>(-FVector2D::DotProduct(Ou, (FVector2D(Border) - FVector2D(At)).GetSafeNormal()) + (CavePlaced16[RI].Used[J] ? 2.f : 0.f), J));
			}
			Js.Sort([](const TPair<float, int32>& X, const TPair<float, int32>& Y) { return X.Key < Y.Key; });
			for (const TPair<float, int32>& Jp : Js)
			{
				FVector PR; FVector2D OR_; Joint(RI, Jp.Value, PR, OR_);
				if (Dig(PR, OR_, Border, -Out, TunnelKit(true), RI, -1 - Pt, true, false)) { CavePlaced16[RI].Used[Jp.Value] = true; bDug = true; break; }
			}
		}
		if (!bDug)
		{
			// (no way to this border: the neighbour's tunnel ends here at the kit's cap (its open side toward the neighbour),
			// not at the void)
			++Failed;
			const FVector Edge((P.X + 0.5f) * S + D.X * S * 0.5f, (P.Y + 0.5f) * S + D.Y * S * 0.5f, Border.Z);
			CaveCaps16.Add(FTransform(FRotator(0.f, FMath::RadiansToDegrees(FMath::Atan2(-Out.Y, -Out.X)), 0.f), Edge));
			Portals.RemoveAt(Pt--);
		}
	}
	for (const FJoin& J : Joins) if (!J.bNeeded && Rooms[J.A].Kind != ERDRoomKind::Junction && Rooms[J.Bn].Kind != ERDRoomKind::Junction) JoinRooms(J.A, J.Bn, false);
	// (the list of 2026-11-22's caves, phase 12: a side tunnel to nowhere from a room's free opening, capped at its end, for the rubble
	// and the cache behind it (CaveRubbleSet16). Its own stream: the plan's draws stay where they were. The loops above are tried
	// after the portals and seldom route (1 set in 13 had one at a loop share of 0.6))
	if (G->RubbleMeshes16.Num() > 0)
	{
		FRandomStream SR(HashCombine((uint32)Seed, 0x5B0E16u + (uint32)Try * 7919u));
		if (SR.FRand() < G->RubbleShare16)
		{
			TArray<int32> Order;
			for (int32 RI = 0; RI < NumRooms; ++RI) if (Rooms[RI].Kind != ERDRoomKind::Junction && CavePlaced16[RI].Kit >= 0) Order.Add(RI);
			for (int32 I = Order.Num() - 1; I > 0; --I) Order.Swap(I, SR.RandRange(0, I));
			int32 MediumKit = TunnelKit(true);
			bool bSpur = false; int32 Digs = 0;          // (12 digs a try at most: each is a route's search, and the plan's tries go one a frame)
			for (int32 Oi = 0; !bSpur && Oi < Order.Num() && Digs < 12; ++Oi)
			{
				const int32 RI = Order[Oi];
				for (int32 J = 0; !bSpur && J < CavePlaced16[RI].Used.Num(); ++J)
				{
					if (CavePlaced16[RI].Used[J]) continue;
					FVector At; FVector2D Ou; Joint(RI, J, At, Ou);
					for (const float L : { 2200.f, 1700.f, 1200.f })
					{
						for (const float Ang : { 0.f, 30.f, -30.f, 55.f, -55.f })
						{
							const FVector2D Dir = FVector2D(FVector(Ou, 0.f).RotateAngleAxis(Ang, FVector::UpVector));
							const FVector PB = At + FVector(Dir * L, 0.f);
							// (its end well past the room's box: the way out of the opening runs straight until clear of the box, and an end short
							// of that turned the line back on itself)
							bool bFar = true;
							for (int32 K = 1; K <= 3 && bFar; ++K)
							{
								const FVector Q = PB - FVector(Dir * (S * K), 0.f);
								const FIntPoint Tq(FMath::FloorToInt(Q.X / S), FMath::FloorToInt(Q.Y / S));
								bFar = In(Tq) && Box[Idx(Tq)] == 0;
							}
							if (!bFar || Digs >= 12) continue;
							const FIntPoint Tb(FMath::FloorToInt(PB.X / S), FMath::FloorToInt(PB.Y / S));
							if (Tb.X < 8 || Tb.Y < 8 || Tb.X >= N - 8 || Tb.Y >= N - 8 || Box[Idx(Tb)] != 0) continue;
							++Digs;
							if (!Dig(At, Ou, PB, -Dir, MediumKit, RI, CaveSpurTo16, true, false)) continue;
							CavePlaced16[RI].Used[J] = true;
							// (the kit's cap a metre back from the end, its open side the tunnel's: as a portal's that found no way)
							CaveCaps16.Add(FTransform(FRotator(0.f, FMath::RadiansToDegrees(FMath::Atan2(Dir.Y, Dir.X)), 0.f), PB - FVector(Dir * 100.f, 0.f)));
							bSpur = true; break;
						}
						if (bSpur) break;
					}
				}
			}
		}
	}
	// the openings no tunnel took: the kit's cap
	for (int32 RI = 0; RI < CavePlaced16.Num(); ++RI)
		for (int32 J = 0; CavePlaced16[RI].Kit >= 0 && J < CavePlaced16[RI].Used.Num(); ++J)
			if (!CavePlaced16[RI].Used[J])
			{
				FVector At; FVector2D Out; Joint(RI, J, At, Out);
				CaveCaps16.Add(FTransform(FRotator(0.f, FMath::RadiansToDegrees(FMath::Atan2(Out.Y, Out.X)), 0.f), At));
			}
	UE_LOG(LogRDCave16, Log, TEXT("RDCAVE16 (%d,%d) try %d tier %d: %d rooms (%d stairs), %d tunnels, %d portals, %d caps, %d joins failed (%d out of the set, %d no route, %d no opening, %d crossings refused, %d bends refused), %d rooms cut off; stairs tried %d (%d places without room)"), Coord.X, Coord.Y, Try, Tier, NumRooms,
		CavePlaced16.Num() - NumRooms - CaveRuns16.Num(), CaveRuns16.Num(), Portals.Num(), CaveCaps16.Num(), Failed, FailOut, FailRoute, FailJoint, FailCross, FailBend, Cut, StairsTried, StairsNoRoom);
	return Cut;
}

// ------------------------------------------------------------------------------------------------ the shell
void ARDSection::CaveShell16()
{
	for (USceneComponent* C : CaveComps16) if (C) C->DestroyComponent();
	CaveComps16.Reset(); CaveDressLines16.Reset();
	UWorld* W = GetWorld();
	// (only in play: a set saved in the level (the start set) keeps none of it, so its shell is never saved twice)
	if (!Generator || !W || !W->IsGameWorld()) return;
	const float S = Generator->TileSize;
	const FVector O = GetActorLocation();
	auto Mesh = [&](UStaticMesh* M, const FTransform& T, bool bCollide)
	{
		if (!M) return (UStaticMeshComponent*)nullptr;
		UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
		C->SetMobility(EComponentMobility::Static);
		C->SetStaticMesh(M);
		C->SetupAttachment(RootComponent);
		// (its place as an offset from the set's corner, before it is registered: a world transform set before the attachment
		// became that offset (the first run's rooms 126 m from their tiles), and a static component cannot be moved once registered
		// in play (the second run's all stood at the corner))
		C->SetRelativeTransform(T.GetRelativeTransform(GetActorTransform()));
		C->SetCollisionProfileName(bCollide ? UCollisionProfile::BlockAll_ProfileName : UCollisionProfile::NoCollision_ProfileName);
		C->RegisterComponent();
		CaveComps16.Add(C);
		return C;
	};
	for (const FCavePlace16& Pl : CavePlaced16)
	{
		if (Pl.Kit < 0) continue;
		const FRDCaveRoom16& E = Generator->CaveRooms16[Pl.Kit];
		const FTransform T(FRotator(0.f, 90.f * Pl.Turn, 0.f), O + FVector((Pl.At.X + 0.5f) * S, (Pl.At.Y + 0.5f) * S, Pl.Z));
		Mesh(E.Mesh, T, true);
		for (int32 I = 0; I < E.Roof.Num(); ++I) Mesh(E.Roof[I], (E.RoofAt.IsValidIndex(I) ? E.RoofAt[I] : FTransform::Identity) * T, true);
	}
	for (const FTransform& T : CaveCaps16) Mesh(Generator->CaveCap16, FTransform(T.GetRotation(), O + T.GetLocation()), true);
	// (phase 9: a torch on each of the rooms' wall-light points; the god ray under each roof's hole with a cool light down it)
	int32 Torches = 0, Rays = 0;
	for (const FCavePlace16& Pl : CavePlaced16)
	{
		if (Pl.Kit < 0) continue;
		const FRDCaveRoom16& E = Generator->CaveRooms16[Pl.Kit];
		const FTransform T(FRotator(0.f, 90.f * Pl.Turn, 0.f), O + FVector((Pl.At.X + 0.5f) * S, (Pl.At.Y + 0.5f) * S, Pl.Z));
		for (const FTransform& Lt : E.Lights) { CaveTorch16(Lt * T); ++Torches; }
		if (!E.GodRay.IsNearlyZero() && E.Roof.Num() > 0 && Generator->CaveGodRayMesh16)
		{
			const FVector G = T.TransformPosition(E.GodRay);
			UStaticMeshComponent* C = Mesh(Generator->CaveGodRayMesh16, FTransform(Generator->CaveGodRayTurn16, G, Generator->CaveGodRayScale16), false);
			if (C && Generator->CaveGodRayMaterial16) C->SetMaterial(0, Generator->CaveGodRayMaterial16);
			if (C) { C->SetCastShadow(false); ++Rays; }
			USpotLightComponent* L = NewObject<USpotLightComponent>(this);
			L->SetMobility(EComponentMobility::Movable);
			L->SetupAttachment(RootComponent);
			L->SetRelativeTransform(FTransform(FRotator(-90.f, 0.f, 0.f), G - O));
			L->SetIntensityUnits(ELightUnits::Candelas);
			L->SetIntensity(Generator->CaveGodRayCandelas16);
			L->SetLightColor(FLinearColor(0.8f, 0.88f, 1.f));
			L->SetAttenuationRadius(E.GodRay.Z + 800.f);
			L->SetOuterConeAngle(32.f); L->SetInnerConeAngle(12.f);
			L->SetCastShadows(false);
			L->RegisterComponent();
			CaveComps16.Add(L);
		}
	}
	CaveDressLines16.Add(FString::Printf(TEXT("torches_rooms|%d"), Torches));
	CaveDressLines16.Add(FString::Printf(TEXT("godrays|%d"), Rays));
	CaveShellRun16 = 0; CaveShellPiece16 = 0;
	if (!bShellSpread16) { CaveShellPieces16(1e9); CaveDressSet16(); }
}

void ARDSection::CaveTorch16(const FTransform& At)
{
	// (the kit's wall torch: its mesh at the point, its fire and light where its Blueprint has them; the light flickers as the castle's
	// torches do (its tag), and the maps draw it)
	if (!Generator) return;
	const FVector O = GetActorLocation();
	auto Rel = [&](const FTransform& W) { return W.GetRelativeTransform(GetActorTransform()); };
	if (Generator->CaveTorchMesh16)
	{
		UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
		C->SetMobility(EComponentMobility::Static);
		C->SetStaticMesh(Generator->CaveTorchMesh16);
		C->SetupAttachment(RootComponent);
		C->SetRelativeTransform(Rel(At));
		C->SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);
		C->RegisterComponent();
		CaveComps16.Add(C);
	}
	if (Generator->CaveTorchFire16)
	{
		UNiagaraComponent* F = NewObject<UNiagaraComponent>(this);
		F->SetupAttachment(RootComponent);
		F->SetAsset(Generator->CaveTorchFire16);
		// (the castle's torch flame (945 level: the kit's own fire needs the NiagaraFluids plugin, not in the project: the package's cook
		// said so), at a sconce's scale, and heard as the castle's torches are)
		F->SetRelativeTransform(Rel(FTransform(At.GetRotation(), At.TransformPosition(Generator->CaveTorchFireAt16), FVector(0.6f))));
		F->RegisterComponent();
		FirePoints.Add({ At.TransformPosition(Generator->CaveTorchFireAt16), (uint8)0 });
		F->Activate(true);
		CaveComps16.Add(F);
	}
	UPointLightComponent* L = NewObject<UPointLightComponent>(this);
	L->SetMobility(EComponentMobility::Movable);
	L->SetupAttachment(RootComponent);
	L->SetRelativeLocation(At.TransformPosition(Generator->CaveTorchLightAt16) - O);
	L->SetIntensityUnits(ELightUnits::Candelas);
	L->SetIntensity(Generator->CaveTorchCandelas16);
	L->SetLightColor(Generator->DungeonLightTintShare > 0.f ? FMath::Lerp(Generator->CaveTorchColor16, Generator->DungeonLightTint, FMath::Clamp(Generator->DungeonLightTintShare, 0.f, 1.f)) : Generator->CaveTorchColor16);
	L->SetAttenuationRadius(1600.f);
	L->SetSourceRadius(6.f);
	L->SetCastShadows(false);
	L->MaxDrawDistance = 9000.f; L->MaxDistanceFadeRange = 2000.f;
	L->ComponentTags.Add(FName(TEXT("RDFlicker"))); L->ComponentTags.Add(FName(TEXT("F0.18")));
	L->RegisterComponent();
	CaveComps16.Add(L);
}

void ARDSection::CaveDressSet16()
{
	CaveDressBegin16();
	while (!CaveDressStep16(1e9)) {}
}

void ARDSection::CaveDressBegin16()
{
	// (the dressing's state: a stream of its own, its steps in a fixed order, so a set dressed over frames is the one dressed at once;
	// each room's walkable tiles gathered once)
	CaveDressR16.Initialize(Seed ^ 0x0CA7E16);
	CaveDressStage16 = 0; CaveDressI16 = 0; CaveDressJ16 = 0; CaveDressTorches16 = 0;
	CaveDressIsm16.Reset(); CaveDressLaid16.Reset();
	CaveRoomTiles16.SetNum(CavePlaced16.Num());
	for (TArray<FIntPoint>& T : CaveRoomTiles16) T.Reset();
	for (int32 T = 0; T < N * N; ++T) if (Owner.IsValidIndex(T) && CaveRoomTiles16.IsValidIndex(Owner[T])) CaveRoomTiles16[Owner[T]].Add(FIntPoint(T % N, T / N));
}

bool ARDSection::CaveDressStep16(double Budget)
{
	// (the torches on the tunnels' walls, then each dressing mesh over each tunnel and each room: a step at a time within Budget seconds
	// (all at once, a set's thousands of traces took one frame: PR #116's review); true when all is laid)
	UWorld* W = GetWorld();
	if (!Generator || !W || !W->IsGameWorld()) return true;
	const double T00 = FPlatformTime::Seconds();
	const FVector O = GetActorLocation();
	FRandomStream& R = CaveDressR16;
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDCave16Dress), true);
	auto Trace = [&](const FVector& A, const FVector& B, FHitResult& H) { return W->LineTraceSingleByChannel(H, A, B, ECC_Visibility, Q); };
	auto Put = [&](UStaticMesh* M, const FTransform& T)
	{
		TObjectPtr<UInstancedStaticMeshComponent>& C = CaveDressIsm16.FindOrAdd(M);
		if (!C)
		{
			C = NewObject<UInstancedStaticMeshComponent>(this);
			C->SetMobility(EComponentMobility::Static);
			C->SetStaticMesh(M);
			C->SetupAttachment(RootComponent);
			C->SetRelativeTransform(FTransform::Identity);
			C->SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);
			C->SetCullDistances(0, 6000);
			C->RegisterComponent();
			CaveComps16.Add(C);
		}
		C->AddInstance(T.GetRelativeTransform(GetActorTransform()), false);
	};
	auto RunOk = [&](const FCaveRun16& Run) { return Run.Points.Num() >= 2 && Generator->CaveTunnels16.IsValidIndex(Run.Kit); };
	while (FPlatformTime::Seconds() - T00 < Budget)
	{
		if (CaveDressStage16 == 0)
		{
			// (a torch on a tunnel's wall every CaveTunnelTorchEvery16 cm, the sides in turn: the wall found by a ray across from the line
			// 2 m over its floor, the torch facing back along the wall's normal)
			if (CaveDressI16 >= CaveRuns16.Num())
			{
				CaveDressLines16.Add(FString::Printf(TEXT("torches_tunnels|%d"), CaveDressTorches16));
				CaveDressStage16 = 1; CaveDressI16 = 0; CaveDressJ16 = 0;
				continue;
			}
			const FCaveRun16& Run = CaveRuns16[CaveDressI16++];
			if (!RunOk(Run)) continue;
			float Acc = 0.f, Next = Generator->CaveTunnelTorchEvery16 * 0.5f; int32 Side = 0;
			for (int32 I = 1; I < Run.Points.Num(); ++I)
			{
				Acc += FVector::Dist(Run.Points[I], Run.Points[I - 1]);
				if (Acc < Next) continue;
				Next += Generator->CaveTunnelTorchEvery16;
				const FVector D = (Run.Points[I] - Run.Points[I - 1]).GetSafeNormal2D();
				const FVector Sd = FVector(-D.Y, D.X, 0.f) * ((Side++ & 1) ? -1.f : 1.f);
				const FVector A = O + Run.Points[I] + FVector(0, 0, 200.f);
				FHitResult H;
				if (!Trace(A, A + Sd * 1200.f, H) || H.ImpactNormal.Z > 0.5f) continue;
				const FVector Nrm = FVector(H.ImpactNormal.X, H.ImpactNormal.Y, 0.f).GetSafeNormal();
				CaveTorch16(FTransform(FRotator(0.f, FMath::RadiansToDegrees(FMath::Atan2(Nrm.X, -Nrm.Y)), 0.f), H.ImpactPoint));
				++CaveDressTorches16;
			}
			continue;
		}
		// (stage 1: dressing entry I over unit J: the tunnels first (J < runs), then the rooms)
		if (CaveDressI16 >= Generator->CaveDress16.Num())
		{
			for (const TPair<FString, int32>& L : CaveDressLaid16) CaveDressLines16.Add(FString::Printf(TEXT("dress|%s|%d"), *L.Key, L.Value));
			CaveNodesSet16();          // (phase 10: the veins and growths, traced onto the laid shell)
			return true;
		}
		const FRDCaveDress16& Dr = Generator->CaveDress16[CaveDressI16];
		const int32 Units = Dr.bTunnel ? CaveRuns16.Num() : CavePlaced16.Num();
		if (!Dr.Mesh || Dr.PerUnit <= 0.f || CaveDressJ16 >= Units) { ++CaveDressI16; CaveDressJ16 = 0; continue; }
		const int32 J = CaveDressJ16++;
		int32& Laid = CaveDressLaid16.FindOrAdd(Dr.Mesh->GetName());
		if (Dr.bTunnel)
		{
			const FCaveRun16& Run = CaveRuns16[J];
			if (!RunOk(Run)) continue;
			const FRDCaveTunnel16& E = Generator->CaveTunnels16[Run.Kit];
			const float Half = E.Mesh ? (float)E.Mesh->GetBoundingBox().GetExtent().Y : 600.f;
			const int32 Want = FMath::RoundToInt(Dr.PerUnit * Run.Length / 100.f);
			for (int32 K = 0; K < Want; ++K)
			{
				const int32 I = R.RandRange(1, Run.Points.Num() - 1);
				const FVector D = (Run.Points[I] - Run.Points[I - 1]).GetSafeNormal2D();
				const FVector P = O + Run.Points[I] + FVector(-D.Y, D.X, 0.f) * (R.FRandRange(Dr.Lateral.X, Dr.Lateral.Y) * Half * (R.FRand() < 0.5f ? -1.f : 1.f));
				FHitResult H;
				const bool bHit = Dr.bRoof ? Trace(P + FVector(0, 0, 150.f), P + FVector(0, 0, 2000.f), H) : Trace(P + FVector(0, 0, 300.f), P - FVector(0, 0, 400.f), H);
				const float Sc = R.FRandRange(Dr.Scale.X, Dr.Scale.Y), Yw = R.FRandRange(0.f, 360.f);
				if (!bHit) continue;
				Put(Dr.Mesh, FTransform(FRotator(0.f, Yw, Dr.bRoof ? 180.f : 0.f), H.ImpactPoint, FVector(Sc)));
				++Laid;
			}
		}
		else
		{
			if (CavePlaced16[J].Kit < 0 || Rooms[J].Kind == ERDRoomKind::Junction || !CaveRoomTiles16.IsValidIndex(J)) continue;
			const TArray<FIntPoint>& Tiles = CaveRoomTiles16[J];
			const int32 Want = FMath::RoundToInt(Dr.PerUnit * Tiles.Num());
			for (int32 K = 0; K < Want && Tiles.Num(); ++K)
			{
				const FIntPoint Tl = Tiles[R.RandRange(0, Tiles.Num() - 1)];
				const FVector P = TileWorld(Tl, CaveFloorAt16(Tl)) + FVector(R.FRandRange(-140.f, 140.f), R.FRandRange(-140.f, 140.f), 0.f);
				const float Sc = R.FRandRange(Dr.Scale.X, Dr.Scale.Y), Yw = R.FRandRange(0.f, 360.f);
				FHitResult H;
				if (!Trace(P + FVector(0, 0, 300.f), P - FVector(0, 0, 400.f), H)) continue;
				Put(Dr.Mesh, FTransform(FRotator(0.f, Yw, 0.f), H.ImpactPoint, FVector(Sc)));
				++Laid;
			}
		}
	}
	return false;
}

TArray<FString> ARDSection::CaveDressing16() const
{
	TArray<FString> Out = CaveDressLines16;
	Out.Add(FString::Printf(TEXT("containers|%d"), CaveContainers16));
	return Out;
}

bool ARDSection::CaveShellPieces16(double Budget)
{
	// the tunnels: the kit's mesh along each curve in overlapping pieces, as its Blueprint lays them; a piece's collision is cooked as
	// it is made, so a set made in play lays them within the frame's budget (all at once a ring set's shell took 3 s in one frame)
	UWorld* W = GetWorld();
	if (!Generator || !W || !W->IsGameWorld()) return true;
	const double T00 = FPlatformTime::Seconds();
	for (; CaveShellRun16 < CaveRuns16.Num(); ++CaveShellRun16, CaveShellPiece16 = 0)
	{
		const FCaveRun16& Run = CaveRuns16[CaveShellRun16];
		if (Run.Points.Num() < 2 || !Generator->CaveTunnels16.IsValidIndex(Run.Kit)) continue;
		const FRDCaveTunnel16& E = Generator->CaveTunnels16[Run.Kit];
		if (!E.Mesh) continue;
		TArray<float> Acc; Acc.Add(0.f);
		for (int32 I = 1; I < Run.Points.Num(); ++I) Acc.Add(Acc.Last() + FVector::Dist(Run.Points[I], Run.Points[I - 1]));
		const float L = Acc.Last();
		auto At = [&](float D, FVector& P, FVector& Dir)
		{
			D = FMath::Clamp(D, 0.f, L);
			int32 I = 1; while (I < Acc.Num() - 1 && Acc[I] < D) ++I;
			const float A = (Acc[I] - Acc[I - 1]) > 0.f ? (D - Acc[I - 1]) / (Acc[I] - Acc[I - 1]) : 0.f;
			P = FMath::Lerp(Run.Points[I - 1], Run.Points[I], A);
			Dir = (Run.Points[I] - Run.Points[I - 1]).GetSafeNormal();
		};
		const float Advance = FMath::Max(E.Segment - E.Overlap, 400.f);
		const int32 Ns = FMath::Max(1, FMath::RoundToInt(L / Advance));
		const float Step = L / Ns;
		for (; CaveShellPiece16 < Ns; ++CaveShellPiece16)
		{
			if (FPlatformTime::Seconds() - T00 >= Budget) return false;
			const int32 K = CaveShellPiece16;
			const float D0 = K * Step - (K > 0 ? E.Overlap * 0.5f : 0.f), D1 = (K + 1) * Step + (K < Ns - 1 ? E.Overlap * 0.5f : 0.f);
			FVector P0, T0, P1, T1; At(D0, P0, T0); At(D1, P1, T1);
			const float Len = D1 - D0;
			USplineMeshComponent* C = NewObject<USplineMeshComponent>(this);
			C->SetMobility(EComponentMobility::Static);
			C->SetStaticMesh(E.Mesh);
			C->SetForwardAxis(ESplineMeshAxis::X, false);
			C->SetupAttachment(RootComponent);
			// (the spline at the mesh's pivot: its floor stands FloorZ over it; its points in the set's frame, the component at the
			// set's corner (its root))
			const FVector Lift(0.f, 0.f, -E.FloorZ);
			C->SetStartAndEnd(P0 + Lift, T0 * Len, P1 + Lift, T1 * Len, false);
			C->SetCollisionProfileName(UCollisionProfile::BlockAll_ProfileName);
			C->SetRelativeTransform(FTransform::Identity);
			C->RegisterComponent();
			C->UpdateMesh();
			CaveComps16.Add(C);
			// (its floor: the kit's strip along the same piece, its top on the plan's floor, wide enough to run under the walls)
			if (E.FloorMesh)
			{
				const FBox FB = E.FloorMesh->GetBoundingBox();
				const float Wd = FMath::Max(FB.GetSize().Y, 1.f);
				USplineMeshComponent* F = NewObject<USplineMeshComponent>(this);
				F->SetMobility(EComponentMobility::Static);
				F->SetStaticMesh(E.FloorMesh);
				F->SetForwardAxis(ESplineMeshAxis::X, false);
				F->SetupAttachment(RootComponent);
				const FVector Down(0.f, 0.f, -FB.Max.Z - 10.f);          // (10 cm under the tunnel's own floor: it fills the gaps in it)
				F->SetStartAndEnd(P0 + Down, T0 * Len, P1 + Down, T1 * Len, false);
				F->SetStartScale(FVector2D(E.FloorWidth / Wd, 1.f), false); F->SetEndScale(FVector2D(E.FloorWidth / Wd, 1.f), false);
				F->SetCollisionProfileName(UCollisionProfile::BlockAll_ProfileName);
				F->SetRelativeTransform(FTransform::Identity);
				F->RegisterComponent();
				F->UpdateMesh();
				CaveComps16.Add(F);
			}
		}
	}
	return true;
}

// ------------------------------------------------------------------------------------------------ the rooms' light
void ARDSection::CaveFurnish16(FRandomStream& R, int32 RI)
{
	// (phase 9: the lights are the shell's (torches, god rays: laid in play with it, never twice); a room gets the castle's containers
	// by its walls: on its floor's edge tiles, pushed 60 cm toward the wall, facing the room's middle)
	if (RI == 0) { CaveContainers16 = 0; CaveRubble16.Reset(); CaveLostLine16.Reset(); }
	// (phase 12: once a set, with its last room: the rubble across a side tunnel and its cache, the lost blade; the room's furnishing
	// goes on with its own footprints)
	if (RI == Rooms.Num() - 1) { Feet.Reset(); CaveRubbleSet16(); CaveLostBlade16(); Feet.Reset(); }
	if (!CavePlaced16.IsValidIndex(RI) || CavePlaced16[RI].Kit < 0 || !Generator || Rooms[RI].Kind == ERDRoomKind::Junction) return;
	// (this room's footprints only, as the castle's Furnish keeps them: never reset, every restart's containers stood on the last
	// one's footprints and fewer were laid each time (7, 8, 3, 2 in one session: PR #117's review run))
	FurnRoom = RI; Feet.Reset();
	static const FIntPoint N4[4] = { FIntPoint(1, 0), FIntPoint(-1, 0), FIntPoint(0, 1), FIntPoint(0, -1) };
	TArray<FIntPoint> Edge;
	for (int32 T = 0; T < N * N; ++T)
	{
		if (Owner[T] != RI) continue;
		const FIntPoint Tl(T % N, T / N);
		// (none within 2 tiles of a tunnel's tile: by an opening a container blocked the one way in, and no path reached the room)
		bool bByMouth = false;
		for (int32 Dy = -2; Dy <= 2 && !bByMouth; ++Dy) for (int32 Dx = -2; Dx <= 2 && !bByMouth; ++Dx)
		{ const FIntPoint U(Tl.X + Dx, Tl.Y + Dy); bByMouth = In(U) && Type[Idx(U)] != 0 && Owner[Idx(U)] != RI; }
		if (bByMouth) continue;
		for (const FIntPoint& D : N4) { const FIntPoint U = Tl + D; if (!In(U) || Type[Idx(U)] == 0) { Edge.Add(Tl); break; } }
	}
	if (Edge.Num() == 0) { FurnRoom = -1; return; }
	const FCavePlace16& Pl = CavePlaced16[RI];
	const float S = Generator->TileSize;
	const FVector Mid = GetActorLocation() + FVector((Pl.At.X + 0.5f) * S, (Pl.At.Y + 0.5f) * S, 0.f);
	const int32 Want = R.RandRange(Generator->CaveContainers16.X, FMath::Max(Generator->CaveContainers16.X, Generator->CaveContainers16.Y));
	int32 Laid = 0;
	for (int32 Try = 0; Try < 30 && Laid < Want; ++Try)
	{
		const FIntPoint Tl = Edge[R.RandRange(0, Edge.Num() - 1)];
		const FVector C = TileWorld(Tl, CaveFloorAt16(Tl));
		const FVector In2 = (Mid - C).GetSafeNormal2D();
		const float Yaw = FMath::RadiansToDegrees(FMath::Atan2(In2.Y, In2.X));
		const FName Piece = Laid == 0 ? FName(TEXT("Chest")) : (R.FRand() < 0.5f ? FName(TEXT("Barrel")) : FName(TEXT("Crate")));
		// (counted by what AddContainer took: in a census, or with no interactive build, it lays none and still says yes (PR #116's
		// review: counted by Containers, a census tried 30 chests a room and counted them all))
		const int32 Before = Containers.Num();
		if (AddContainer(Piece, C - In2 * 60.f, Yaw, Piece.ToString().ToLower())) { ++Laid; if (Containers.Num() > Before) ++CaveContainers16; }
	}
	FurnRoom = -1;
}

// ------------------------------------------------------------------------------------------------ a way into a shut tier
void ARDSection::CaveSeal16(const FVector& Border, const FVector& Out, int32 Kind)
{
	// the kit's cap across the tunnel, its open side (+X) toward the set, a step in from the border; a blocker over the tunnel's
	// whole mouth (the medium tunnel's: the portals' kind)
	const FIntPoint P = WorldToLocal(Border - Out * 10.f);
	const float Z = GetActorLocation().Z + CaveFloorAt16(P);
	const FVector At(Border.X - Out.X * 150.f, Border.Y - Out.Y * 150.f, Z);
	const FRotator Yaw = Out.Rotation();
	if (Generator->CaveCap16)
	{
		UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
		C->SetMobility(EComponentMobility::Movable);
		C->SetStaticMesh(Generator->CaveCap16);
		C->SetupAttachment(RootComponent);
		C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		C->RegisterComponent();
		C->SetWorldTransform(FTransform(Yaw, At));
		SealComps.Add(C);
	}
	UBoxComponent* Bx = NewObject<UBoxComponent>(this);
	Bx->SetMobility(EComponentMobility::Movable);
	Bx->SetupAttachment(RootComponent);
	Bx->SetBoxExtent(FVector(30.f, 900.f, 600.f));
	Bx->SetCollisionProfileName(UCollisionProfile::BlockAll_ProfileName);
	Bx->SetHiddenInGame(true);
	Bx->RegisterComponent();
	Bx->SetWorldLocationAndRotation(At + FVector(0, 0, 600.f), Yaw);
	SealComps.Add(Bx);
	SealAt.Add(Border); SealKinds.Add(Kind);
}

// ------------------------------------------------------------------------------------------------ the tests' lines
TArray<FString> ARDSection::CavePieces16() const
{
	TArray<FString> Out;
	if (!Generator) return Out;
	const float S = Generator->TileSize;
	const FVector O = GetActorLocation();
	for (int32 I = 0; I < CavePlaced16.Num(); ++I)
	{
		const FCavePlace16& Pl = CavePlaced16[I];
		if (Pl.Kit < 0) continue;
		int32 Tiles = 0; for (int32 T = 0; T < Owner.Num(); ++T) Tiles += Owner[T] == I;
		Out.Add(FString::Printf(TEXT("room|%d|%s|%.0f|%.0f|%.0f|%d|%d"), I, *Generator->CaveRooms16[Pl.Kit].Kind.ToString(), O.X + (Pl.At.X + 0.5f) * S, O.Y + (Pl.At.Y + 0.5f) * S, O.Z + Pl.Z, Pl.Turn * 90, Tiles));
	}
	for (const FCaveRun16& Run : CaveRuns16)
	{
		FString Pts; float Next = 0.f, Acc = 0.f;
		for (int32 I = 0; I < Run.Points.Num(); ++I)
		{
			if (I > 0) Acc += FVector::Dist(Run.Points[I], Run.Points[I - 1]);
			if (Acc + 0.5f >= Next || I == Run.Points.Num() - 1) { const FVector P = O + Run.Points[I]; Pts += FString::Printf(TEXT("%s%.0f,%.0f,%.0f"), Pts.IsEmpty() ? TEXT("") : TEXT(";"), P.X, P.Y, P.Z); Next += 200.f; }
		}
		const float Adv = FMath::Max(Generator->CaveTunnels16[Run.Kit].Segment - Generator->CaveTunnels16[Run.Kit].Overlap, 400.f);
		Out.Add(FString::Printf(TEXT("tunnel|%s|%d|%d|%d|%.0f|%d|%s"), *Generator->CaveTunnels16[Run.Kit].Kind.ToString(), Run.Room, Run.From, Run.To, Run.Length, FMath::Max(1, FMath::RoundToInt(Run.Length / Adv)), *Pts));
	}
	for (const FTransform& T : CaveCaps16) Out.Add(FString::Printf(TEXT("cap|%.0f|%.0f|%.0f|%.0f"), O.X + T.GetLocation().X, O.Y + T.GetLocation().Y, O.Z + T.GetLocation().Z, T.Rotator().Yaw));
	return Out;
}

TArray<FString> ARDSection::CaveTiles16() const
{
	TArray<FString> Out;
	if (!Generator || Type.Num() != N * N) return Out;
	for (int32 Y = 0; Y < N; ++Y)
		for (int32 X = 0; X < N; ++X)
		{
			const FIntPoint T(X, Y);
			if (!Type[Idx(T)]) continue;
			const FVector P = TileWorld(T, CaveFloorAt16(T));
			Out.Add(FString::Printf(TEXT("%.0f|%.0f|%.0f|%d"), P.X, P.Y, P.Z, (int32)Owner[Idx(T)]));
		}
	return Out;
}

TArray<FString> ARDDungeonGenerator::GetCavePieces16(FIntPoint Section) const
{
	const ARDSection* S = GetSection(Section);
	return S ? S->CavePieces16() : TArray<FString>();
}

TArray<FString> ARDDungeonGenerator::GetCaveTiles16(FIntPoint Section) const
{
	const ARDSection* S = GetSection(Section);
	return S ? S->CaveTiles16() : TArray<FString>();
}

bool ARDDungeonGenerator::CaptureAbove16(FIntPoint Section, const FString& Folder, const FString& File, float Height, int32 Pixels)
{
	const ARDSection* S = GetSection(Section);
	if (!S) return false;
	const float Half = SectionTiles * TileSize * 0.5f;
	USceneCaptureComponent2D* C = NewObject<USceneCaptureComponent2D>(this);
	C->SetupAttachment(GetRootComponent());
	C->ProjectionType = ECameraProjectionMode::Orthographic;
	C->OrthoWidth = Half * 2.f;
	C->CaptureSource = ESceneCaptureSource::SCS_BaseColor;
	C->bCaptureEveryFrame = false; C->bCaptureOnMovement = false;
	UTextureRenderTarget2D* RT = UKismetRenderingLibrary::CreateRenderTarget2D(this, Pixels, Pixels, RTF_RGBA8_SRGB);
	C->TextureTarget = RT;
	C->RegisterComponent();
	C->SetWorldLocationAndRotation(S->GetActorLocation() + FVector(Half, Half, Height), FRotator(-90.f, 0.f, 0.f));
	for (int32 I = 0; I < 3; ++I) C->CaptureScene();
	UKismetRenderingLibrary::ExportRenderTarget(this, RT, Folder, File);
	C->DestroyComponent();
	return true;
}

float ARDSection::CaveFloorNear16(FIntPoint T) const
{
	// (her floor where she stands off the tiles (a room's rim, a tunnel's floor strip under its walls): the lowest of the walkable
	// tiles within 4, else the set's lowest level: the safety net took the set's base and sent her back from a low room's edge)
	if (In(T) && Type.IsValidIndex(Idx(T)) && Type[Idx(T)] != 0) return CaveFloorAt16(T);
	float Lo = FLT_MAX;
	for (int32 Dy = -4; Dy <= 4; ++Dy) for (int32 Dx = -4; Dx <= 4; ++Dx)
	{
		const FIntPoint U(T.X + Dx, T.Y + Dy);
		if (In(U) && Type.IsValidIndex(Idx(U)) && Type[Idx(U)] != 0) Lo = FMath::Min(Lo, CaveFloorAt16(U));
	}
	return Lo < FLT_MAX ? Lo : -(Generator ? Generator->CaveLevelDrop16 : 428.f) - 300.f;
}

TArray<FString> ARDDungeonGenerator::GetCaveDressing16(FIntPoint Section) const
{
	const ARDSection* S = GetSection(Section);
	return S ? S->CaveDressing16() : TArray<FString>();
}

TArray<FString> ARDDungeonGenerator::GetBossRoomPick16(int32 Tier) const
{
	// (the pick for the tier's boss (salt 1) and the very list it chose from (ExploredRooms: PR #116's review), heights in the world)
	TArray<FString> Out;
	ARDSection* S = nullptr; int32 Room = -1;
	TArray<FExploredRoom> Cands; ExploredRooms(Tier, Cands);
	if (PickExploredRoom(Tier, 1, S, Room) && S)
		Out.Add(FString::Printf(TEXT("%d|%d|%d|%.0f"), S->Coord.X, S->Coord.Y, Room, S->GetActorLocation().Z + S->CaveRoomFloor16(Room)));
	for (const FExploredRoom& C : Cands) Out.Add(FString::Printf(TEXT("cand|%d|%d|%d|%.0f|%.0f"), C.S->Coord.X, C.S->Coord.Y, C.Room, C.Z, C.D));
	return Out;
}
