#include "RD/RDSection.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDMonster.h"
#include "ProceduralMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/BoxComponent.h"
#include "Engine/CollisionProfile.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "NiagaraSystemInstance.h"
#include "NiagaraSystemInstanceController.h"
#include "NiagaraEmitterInstance.h"
#include "TimerManager.h"
#include "HAL/PlatformTime.h"
#include "Misc/ScopeExit.h"
#include "RD/RDMistward.h"

DEFINE_LOG_CATEGORY_STATIC(LogRandomDungeon, Log, All);

static const FName RDInteractiveTag(TEXT("RDInteractive"));
static const FName RDFlickerTag(TEXT("RDFlicker"));
// The flame effect is a torch's (scale 0.6 on a sconce). At that size it was a spark at the bottom of a brazier's bowl
// and in a hearth, and read as "light without a flame": the bigger fires scale it up.
// The flame is drawn round the effect's origin, not above it: scaled up, half of it hangs below, so a brazier's goes
// above the rim of its bowl (in the bowl it showed between the legs).
static const float RDBrazierFlame = 2.0f, RDBrazierFlameUp = 12.f, RDHearthFlame = 2.6f, RDForgeFlame = 2.0f;
static const FIntPoint Dir4[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };

ARDSection::ARDSection()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.f;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent->SetMobility(EComponentMobility::Static);
}

// ------------------------------------------------------------------------------------------------ coordinates
FVector2D ARDSection::GetSectionMin() const { const FVector L = GetActorLocation(); return FVector2D(L.X, L.Y); }

FVector ARDSection::TileWorld(FIntPoint T, float Z) const
{
	const float S = Generator->TileSize;
	const FVector L = GetActorLocation();
	return FVector(L.X + (T.X + 0.5f) * S, L.Y + (T.Y + 0.5f) * S, Z);
}

FIntPoint ARDSection::WorldToLocal(const FVector& W) const
{
	const float S = Generator ? Generator->TileSize : 300.f;
	const FVector L = GetActorLocation();
	return FIntPoint(FMath::FloorToInt((W.X - L.X) / S), FMath::FloorToInt((W.Y - L.Y) / S));
}

FVector ARDSection::LocalToWorld(FIntPoint T) const { return TileWorld(T, 0.f); }

int64 ARDSection::EdgeKey(FIntPoint A, FIntPoint B)
{
	if (B.X < A.X || (B.X == A.X && B.Y < A.Y)) Swap(A, B);
	return ((int64)(A.X + 512) << 40) | ((int64)(A.Y + 512) << 20) | (int64)((B.X - A.X) * 2 + (B.Y - A.Y) + 4);
}

int32 ARDSection::RoomAtLocal(FIntPoint T) const
{
	if (!In(T) || Owner.Num() != N * N) return -1;
	const int16 O = Owner[Idx(T)];
	return (O >= 0 && O < 1000) ? O : -1;
}

int32 ARDSection::RoomAt(FVector L) const { return RoomAtLocal(WorldToLocal(L)); }

bool ARDSection::IsWalkable(FIntPoint T) const
{
	return In(T) && Type.Num() == N * N && Type[Idx(T)] != 0 && !Blocked[Idx(T)];
}

int32 ARDSection::DoorBetween(FIntPoint A, FIntPoint B) const
{
	const int32* D = DoorEdges.Find(EdgeKey(A, B));
	return D ? *D : -1;
}

// ------------------------------------------------------------------------------------------------ plan
void ARDSection::Plan(FRandomStream& R)
{
	N = Generator->SectionTiles;
	const int32 B = Generator->BlockTiles, NB = N / B;
	Rooms.Reset(); Corrs.Reset(); DoorEdges.Reset(); Portals.Reset(); Cells.Reset();
	Fixtures.Reset(); SpecialChests.Reset();          // (the third list's: furnishing makes them again)
	for (FPickup& Pk : Pickups) if (Pk.Mesh.IsValid()) Pk.Mesh->DestroyComponent();
	Pickups.Reset();
	Type.Init(0, N * N); Owner.Init(-1, N * N); Blocked.Init(0, N * N); CeilH.Init(0.f, N * N);
	const bool bStart = Generator->IsStartSection(Coord);
	// (martial_arts: the great hall alone, OneRoomTiles a side round the middle block's lane: no doors, no hallways, no portals)
	if (Generator->bOneRoom && bStart)
	{
		FRoom Rm; Rm.Block = (NB / 2) * NB + NB / 2; Rm.Kind = ERDRoomKind::Hall;
		Rm.Lane = FIntPoint((NB / 2) * B + B / 2, (NB / 2) * B + B / 2);
		const int32 S = FMath::Clamp(Generator->OneRoomTiles, 4, B - 2);
		Rm.Min = Rm.Lane - FIntPoint(S / 2, S / 2); Rm.Max = Rm.Min + FIntPoint(S, S);
		const int32 RI = Rooms.Add(Rm);
		for (int32 X = Rm.Min.X; X < Rm.Max.X; ++X)
			for (int32 Y = Rm.Min.Y; Y < Rm.Max.Y; ++Y) { Type[Idx(FIntPoint(X, Y))] = 1; Owner[Idx(FIntPoint(X, Y))] = (int16)RI; }
		return;
	}
	// room kinds: weighted, a few per section capped
	struct FW { ERDRoomKind K; float W; int32 MinSize; int32 MaxSize; int32 Cap; };
	const FW Kinds[] = {
		{ ERDRoomKind::Barracks, 9, 6, 10, 6 }, { ERDRoomKind::Prison, 7, 7, 10, 5 }, { ERDRoomKind::Torture, 4, 5, 8, 3 },
		{ ERDRoomKind::Storeroom, 9, 5, 9, 7 }, { ERDRoomKind::Armory, 6, 5, 9, 4 }, { ERDRoomKind::Kitchen, 5, 6, 10, 3 },
		{ ERDRoomKind::Library, 5, 6, 10, 3 }, { ERDRoomKind::Chapel, 4, 7, 10, 2 }, { ERDRoomKind::Crypt, 6, 6, 10, 4 },
		{ ERDRoomKind::Treasury, 3, 5, 7, 2 }, { ERDRoomKind::GuardRoom, 8, 5, 7, 6 }, { ERDRoomKind::Forge, 4, 6, 9, 2 },
		{ ERDRoomKind::Hall, 2, 9, 10, 1 }, { ERDRoomKind::Junction, 10, 3, 3, 12 } };
	TMap<ERDRoomKind, int32> Used;
	// (mistward: rooms' sizes from a stream of their own (the user's list: "more variation in the sizes"))
	FRandomStream RZ(R.GetInitialSeed() ^ 0x2B1E5C07);
	for (int32 By = 0; By < NB; ++By)
		for (int32 Bx = 0; Bx < NB; ++Bx)
		{
			FRoom Rm; Rm.Block = By * NB + Bx;
			Rm.Lane = FIntPoint(Bx * B + B / 2, By * B + B / 2);
			int32 MinS = 5, MaxS = 10;
			if (bStart && Bx == NB / 2 && By == NB / 2) { Rm.Kind = ERDRoomKind::Hall; MinS = MaxS = 10; }
			else
			{
				float Sum = 0.f;
				for (const FW& K : Kinds) if (Used.FindRef(K.K) < K.Cap && !(bStart && K.K == ERDRoomKind::Hall)) Sum += K.W;
				float U = R.FRand() * Sum; const FW* Pick = &Kinds[0];
				for (const FW& K : Kinds)
				{
					if (Used.FindRef(K.K) >= K.Cap || (bStart && K.K == ERDRoomKind::Hall)) continue;
					U -= K.W; if (U <= 0.f) { Pick = &K; break; }
				}
				Rm.Kind = Pick->K; MinS = Pick->MinSize; MaxS = Pick->MaxSize;
			}
			Used.FindOrAdd(Rm.Kind)++;
			if (Rm.Kind == ERDRoomKind::Junction)
			{
				Rm.Min = Rm.Lane - FIntPoint(1, 1); Rm.Max = Rm.Lane + FIntPoint(2, 2);
			}
			else
			{
				int32 W = R.RandRange(MinS, MaxS), H = R.RandRange(MinS, MaxS);
				// (mistward: small chambers (3 or 4 tiles a side), long galleries (the block's length by 3 or 4), and more of the
				// block's largest; not the great hall nor a prison (its cells want room). Drawn for every room: one room's
				// size never moves another's)
				{
					const float U = RZ.FRand(); const int32 S1 = RZ.RandRange(3, 4), S2 = RZ.RandRange(3, 4); const bool bAlongX = RZ.RandBool();
					const int32 Long = B - 2;
					if (Generator->bShapedRooms && Rm.Kind != ERDRoomKind::Hall && Rm.Kind != ERDRoomKind::Prison)
					{
						if (U < 0.16f) { W = S1; H = S2; }
						else if (U < 0.32f) { W = bAlongX ? Long : S1; H = bAlongX ? S1 : Long; }
						else if (U < 0.42f) { W = H = Long; }
					}
				}
				const int32 X0 = R.RandRange(FMath::Max(1, B / 2 + 1 - W), FMath::Min(B / 2, B - 1 - W));
				const int32 Y0 = R.RandRange(FMath::Max(1, B / 2 + 1 - H), FMath::Min(B / 2, B - 1 - H));
				Rm.Min = FIntPoint(Bx * B + X0, By * B + Y0); Rm.Max = Rm.Min + FIntPoint(W, H);
			}
			const int32 RI = Rooms.Add(Rm);
			for (int32 X = Rm.Min.X; X < Rm.Max.X; ++X)
				for (int32 Y = Rm.Min.Y; Y < Rm.Max.Y; ++Y) { Type[Idx(FIntPoint(X, Y))] = 1; Owner[Idx(FIntPoint(X, Y))] = (int16)RI; }
		}
	// block graph: random spanning tree (Kruskal) + loops
	struct FE { int32 A, Bk; };
	TArray<FE> Edges;
	for (int32 By = 0; By < NB; ++By)
		for (int32 Bx = 0; Bx < NB; ++Bx)
		{
			if (Bx + 1 < NB) Edges.Add({ By * NB + Bx, By * NB + Bx + 1 });
			if (By + 1 < NB) Edges.Add({ By * NB + Bx, (By + 1) * NB + Bx });
		}
	for (int32 I = Edges.Num() - 1; I > 0; --I) Edges.Swap(I, R.RandRange(0, I));
	TArray<int32> Parent; Parent.SetNum(NB * NB); for (int32 I = 0; I < NB * NB; ++I) Parent[I] = I;
	auto Find = [&Parent](int32 X) { while (Parent[X] != X) { Parent[X] = Parent[Parent[X]]; X = Parent[X]; } return X; };
	TArray<FE> Keep;
	for (const FE& E : Edges)
	{
		const int32 A = Find(E.A), Bb = Find(E.Bk);
		if (A != Bb) { Parent[A] = Bb; Keep.Add(E); }
		else if (R.FRand() < 0.3f) Keep.Add(E);
	}
	auto AddCorr = [this, &R](FIntPoint A, FIntPoint Bt, bool bHoriz)
	{
		FCorr C; C.Min = FIntPoint(FMath::Min(A.X, Bt.X), FMath::Min(A.Y, Bt.Y)); C.Max = FIntPoint(FMath::Max(A.X, Bt.X) + 1, FMath::Max(A.Y, Bt.Y) + 1);
		C.bHoriz = bHoriz; C.Theme = R.RandRange(0, 2);
		if (C.Max.X <= C.Min.X || C.Max.Y <= C.Min.Y) return;
		const int32 CI = Corrs.Add(C);
		for (int32 X = C.Min.X; X < C.Max.X; ++X)
			for (int32 Y = C.Min.Y; Y < C.Max.Y; ++Y)
				if (Type[Idx(FIntPoint(X, Y))] == 0) { Type[Idx(FIntPoint(X, Y))] = 2; Owner[Idx(FIntPoint(X, Y))] = (int16)(1000 + CI); }
	};
	for (const FE& E : Keep)
	{
		FRoom& A = Rooms[E.A]; FRoom& Bm = Rooms[E.Bk];
		if (E.Bk == E.A + 1)    // east-west
		{
			AddCorr(FIntPoint(A.Max.X, A.Lane.Y), FIntPoint(Bm.Min.X - 1, A.Lane.Y), true);
			A.bDoorSide[1] = true; Bm.bDoorSide[0] = true;
		}
		else
		{
			AddCorr(FIntPoint(A.Lane.X, A.Max.Y), FIntPoint(A.Lane.X, Bm.Min.Y - 1), false);
			A.bDoorSide[3] = true; Bm.bDoorSide[2] = true;
		}
	}
	// hallways across the section edges (fixed block rows / columns: neighbours always match)
	for (int32 K = 0; K < NB; ++K)
	{
		if (!ARDDungeonGenerator::IsPortalBlock(K)) continue;
		FRoom& W = Rooms[K * NB + 0]; FRoom& E = Rooms[K * NB + NB - 1];
		FRoom& S = Rooms[0 * NB + K]; FRoom& Nn = Rooms[(NB - 1) * NB + K];
		AddCorr(FIntPoint(0, W.Lane.Y), FIntPoint(W.Min.X - 1, W.Lane.Y), true); W.bDoorSide[0] = true; Portals.Add(FIntPoint(0, W.Lane.Y));
		AddCorr(FIntPoint(E.Max.X, E.Lane.Y), FIntPoint(N - 1, E.Lane.Y), true); E.bDoorSide[1] = true; Portals.Add(FIntPoint(N - 1, E.Lane.Y));
		AddCorr(FIntPoint(S.Lane.X, 0), FIntPoint(S.Lane.X, S.Min.Y - 1), false); S.bDoorSide[2] = true; Portals.Add(FIntPoint(S.Lane.X, 0));
		AddCorr(FIntPoint(Nn.Lane.X, Nn.Max.Y), FIntPoint(Nn.Lane.X, N - 1), false); Nn.bDoorSide[3] = true; Portals.Add(FIntPoint(Nn.Lane.X, N - 1));
	}
	// doorways: every room (not junction) <-> hallway edge, in a fixed order (door index = mover index)
	int32 DI = 0;
	for (int32 RI = 0; RI < Rooms.Num(); ++RI)
	{
		const FRoom& Rm = Rooms[RI];
		if (Rm.Kind == ERDRoomKind::Junction) continue;
		for (int32 Side = 0; Side < 4; ++Side)
		{
			if (!Rm.bDoorSide[Side]) continue;
			FIntPoint In_ = Side == 0 ? FIntPoint(Rm.Min.X, Rm.Lane.Y) : Side == 1 ? FIntPoint(Rm.Max.X - 1, Rm.Lane.Y) : Side == 2 ? FIntPoint(Rm.Lane.X, Rm.Min.Y) : FIntPoint(Rm.Lane.X, Rm.Max.Y - 1);
			const FIntPoint Out = In_ + Dir4[Side];
			if (In(Out) && Type[Idx(Out)] == 2) DoorEdges.Add(EdgeKey(In_, Out), DI++);
		}
	}
	// (mistward: rooms of other shapes and heights; a stream of its own, so the layout above is what it was)
	if (Generator->bShapedRooms)
	{
		FRandomStream RS(R.GetInitialSeed() ^ 0x5A4E3D21);
		for (int32 RI = 0; RI < Rooms.Num(); ++RI) ShapeRoom(RS, RI);
	}
	// (the third list: shrines, fountains, an arena, a gauntlet, a vault, a throne room; a stream of their own as well)
	if (Generator->bSpecialRooms) AssignSpecialRooms();
}

// ------------------------------------------------------------------------------------------------ shapes (mistward)
static const TCHAR* RDShapeNames[] = { TEXT("rect"), TEXT("circle"), TEXT("octagon"), TEXT("hexagon"), TEXT("triangle"), TEXT("L"), TEXT("T"), TEXT("U"),
	TEXT("dome"), TEXT("pyramid"), TEXT("tall"), TEXT("diamond"), TEXT("step pyramid") };

FString ARDSection::GetRoomShape(int32 I) const
{
	if (!Rooms.IsValidIndex(I)) return FString();
	const int32 S = Rooms[I].Shape;
	return S < (int32)UE_ARRAY_COUNT(RDShapeNames) ? RDShapeNames[S] : TEXT("rect");
}

float ARDSection::CeilAt(FIntPoint T) const
{
	if (!In(T) || Type.Num() != N * N || !Generator) return 0.f;
	if (CeilH.Num() == N * N && CeilH[Idx(T)] > 0.f) return CeilH[Idx(T)];
	const int16 O = Owner[Idx(T)];
	const bool bLow = O >= 1000 || O < 0 || Rooms[O].Kind == ERDRoomKind::Junction;
	return bLow ? Generator->CorridorHeight : Generator->RoomHeight;
}

void ARDSection::ShapeRoom(FRandomStream& R, int32 RI)
{
	FRoom& Rm = Rooms[RI];
	const float Pick = R.FRand();                      // (drawn for every room: one room's choice never moves another's)
	const int32 Which = R.RandRange(1, 12);
	const float Tall = R.FRandRange(0.f, 1.f);
	if (Rm.Kind == ERDRoomKind::Junction || Rm.Kind == ERDRoomKind::Prison) return;
	if (Generator->IsStartSection(Coord) && Rm.Kind == ERDRoomKind::Hall) return;
	const int32 W = Rm.Max.X - Rm.Min.X, H = Rm.Max.Y - Rm.Min.Y;
	if (W < 6 || H < 6 || Pick >= Generator->ShapedRoomShare) return;
	Rm.Shape = (uint8)Which;
	const float Cx = (Rm.Min.X + Rm.Max.X) * 0.5f, Cy = (Rm.Min.Y + Rm.Max.Y) * 0.5f;
	const float RH = Generator->RoomHeight;
	// (the U's notch and the T's and L's cut corners on a side without a door, so the doors stay on the floor)
	int32 Free = -1;
	for (int32 S = 0; S < 4; ++S) if (!Rm.bDoorSide[S]) { Free = S; break; }
	if ((Rm.Shape == 7 || Rm.Shape == 6) && Free < 0) Rm.Shape = 2;
	auto Inside = [&](float U, float V) -> bool
	{
		// (U, V: the tile's middle, -1..1 across the rectangle; a side "down" is the free side for L, T and U)
		float A = U, B = V;
		if (Free == 0) { A = V; B = -U; } else if (Free == 1) { A = V; B = U; } else if (Free == 2) { A = U; B = -V; }
		switch (Rm.Shape)
		{
		case 1: case 8: return U * U + V * V <= 1.08f;                                         // circle, dome
		case 2: return FMath::Abs(U) + FMath::Abs(V) <= 1.5f;                                 // octagon
		case 3: return FMath::Abs(V) <= 0.95f && FMath::Abs(U) + 0.55f * FMath::Abs(V) <= 1.02f;     // hexagon
		case 4: case 12: return FMath::Abs(U) <= (V + 1.1f) * 0.5f;                           // triangle, its point at -V
		case 5: return !(U > 0.15f && V > 0.15f);                                              // L
		case 6: return !(B > 0.2f && FMath::Abs(A) > 0.38f);                                   // T: the free side's corners cut
		case 7: return !(B > 0.05f && FMath::Abs(A) < 0.36f);                                  // U: a notch in from the free side
		case 11: return FMath::Abs(U) + FMath::Abs(V) <= 1.12f;                               // diamond
		default: return true;                                                                  // pyramid, tall: the rectangle
		}
	};
	// the lane from each door to the lane's crossing stays (the doors open on floor)
	auto OnLane = [&](int32 X, int32 Y)
	{
		if (X == Rm.Lane.X && Y == Rm.Lane.Y) return true;
		if (Y == Rm.Lane.Y && ((Rm.bDoorSide[0] && X <= Rm.Lane.X) || (Rm.bDoorSide[1] && X >= Rm.Lane.X))) return true;
		if (X == Rm.Lane.X && ((Rm.bDoorSide[2] && Y <= Rm.Lane.Y) || (Rm.bDoorSide[3] && Y >= Rm.Lane.Y))) return true;
		return false;
	};
	TArray<FIntPoint> Keep;
	for (int32 X = Rm.Min.X; X < Rm.Max.X; ++X)
		for (int32 Y = Rm.Min.Y; Y < Rm.Max.Y; ++Y)
		{
			const float U = (X + 0.5f - Cx) / (W * 0.5f), V = (Y + 0.5f - Cy) / (H * 0.5f);
			if (Inside(U, V) || OnLane(X, Y)) Keep.Add(FIntPoint(X, Y));
			else { Type[Idx(FIntPoint(X, Y))] = 0; Owner[Idx(FIntPoint(X, Y))] = -1; }
		}
	// (what is not joined to the lane's crossing goes too: one floor)
	TSet<FIntPoint> Seen; TArray<FIntPoint> Q = { Rm.Lane }; Seen.Add(Rm.Lane);
	for (int32 H0 = 0; H0 < Q.Num(); ++H0)
		for (int32 D = 0; D < 4; ++D)
		{
			const FIntPoint Nb = Q[H0] + Dir4[D];
			if (!Seen.Contains(Nb) && In(Nb) && Owner[Idx(Nb)] == RI) { Seen.Add(Nb); Q.Add(Nb); }
		}
	for (const FIntPoint& T : Keep) if (!Seen.Contains(T)) { Type[Idx(T)] = 0; Owner[Idx(T)] = -1; }
	// heights: a dome rises round its middle, a pyramid in square steps, a step pyramid (the triangle) toward its far
	// end, a tall hall all over (100 cm steps: the walls stack on them)
	for (const FIntPoint& T : Seen)
	{
		const float U = (T.X + 0.5f - Cx) / (W * 0.5f), V = (T.Y + 0.5f - Cy) / (H * 0.5f);
		float Hh = 0.f;
		if (Rm.Shape == 8) Hh = RH + 700.f * FMath::Clamp(1.f - FMath::Sqrt(U * U + V * V), 0.f, 1.f);
		else if (Rm.Shape == 9) Hh = RH + 800.f * FMath::Clamp(1.f - FMath::Max(FMath::Abs(U), FMath::Abs(V)), 0.f, 1.f);
		else if (Rm.Shape == 12) Hh = RH + 500.f * FMath::Clamp((V + 1.f) * 0.5f, 0.f, 1.f);
		else if (Rm.Shape == 10) Hh = RH + 300.f + 300.f * FMath::RoundToFloat(Tall * 2.f);
		if (Hh > 0.f) CeilH[Idx(T)] = FMath::RoundToFloat(Hh / 100.f) * 100.f;
	}
}

// ------------------------------------------------------------------------------------------------ themes (mistward)
FName ARDSection::PcName(FName Name) const
{
	if (Theme.IsNone() || !Generator) return Name;
	if (ThemeNamesOf != Theme) { ThemeNames.Reset(); ThemeNamesOf = Theme; }
	if (const FName* Known = ThemeNames.Find(Name)) return *Known;
	const FName T(*FString::Printf(TEXT("%s.%s"), *Theme.ToString(), *Name.ToString()));
	const FName Out = Generator->Piece(T) ? T : Name;
	ThemeNames.Add(Name, Out);
	return Out;
}

const FRDPiece* ARDSection::Pc(FName Name) const { return Generator ? Generator->Piece(PcName(Name)) : nullptr; }

// ------------------------------------------------------------------------------------------------ tidy furniture (mistward)
namespace
{
	struct FRDObb { FVector2D C; FVector2D Ax[2]; FVector2D H; };
	FRDObb RDObb(const FVector2D& C, const FVector2D& H, float Yaw)
	{
		const float Rr = FMath::DegreesToRadians(Yaw);
		FRDObb O; O.C = C; O.H = H; O.Ax[0] = FVector2D(FMath::Cos(Rr), FMath::Sin(Rr)); O.Ax[1] = FVector2D(-FMath::Sin(Rr), FMath::Cos(Rr));
		return O;
	}
	bool RDOverlap(const FRDObb& A, const FRDObb& B)
	{
		const FVector2D D = B.C - A.C;
		for (const FRDObb* O : { &A, &B })
			for (int32 K = 0; K < 2; ++K)
			{
				const FVector2D L = O->Ax[K];
				const float Ra = A.H.X * FMath::Abs(FVector2D::DotProduct(A.Ax[0], L)) + A.H.Y * FMath::Abs(FVector2D::DotProduct(A.Ax[1], L));
				const float Rb = B.H.X * FMath::Abs(FVector2D::DotProduct(B.Ax[0], L)) + B.H.Y * FMath::Abs(FVector2D::DotProduct(B.Ax[1], L));
				if (FMath::Abs(FVector2D::DotProduct(D, L)) > Ra + Rb) return false;
			}
		return true;
	}
}

// (a hair under its size, so that pieces set side by side as their sizes say still fit. It was 3 cm a side: two pieces could
// stand 6 cm into each other, and a chest against a bed's foot board looked set into it (the user's of 2026-10-27))
static constexpr float RDFootSlack = 0.5f;

bool ARDSection::FootFree(const FVector& Loc, float Yaw, const FVector2D& Size, bool bAccess) const
{
	const FRDObb A = RDObb(FVector2D(Loc.X, Loc.Y), FVector2D(FMath::Max(Size.X * 0.5f - RDFootSlack, 1.f), FMath::Max(Size.Y * 0.5f - RDFootSlack, 1.f)), Yaw);
	for (const FFoot& F : Feet)
	{
		if (bAccess && F.bAccess) continue;              // (two ways in may share the floor)
		if (RDOverlap(A, RDObb(F.C, F.H, F.Yaw))) return false;
	}
	return true;
}

void ARDSection::AddFoot(const FVector& Loc, float Yaw, const FVector2D& Size, bool bAccess, FName Name)
{
	FFoot F; F.C = FVector2D(Loc.X, Loc.Y); F.H = FVector2D(FMath::Max(Size.X * 0.5f - RDFootSlack, 1.f), FMath::Max(Size.Y * 0.5f - RDFootSlack, 1.f)); F.Yaw = Yaw; F.bAccess = bAccess; F.Name = Name;
	Feet.Add(F);
}

bool ARDSection::OnRoomFloor(const FVector& Loc, float Yaw, const FVector2D& Size, int32 RI) const
{
	// the footprint's corners and middle stand on the room's tiles
	const FRotator Rt(0, Yaw, 0);
	const FVector2D Hh = Size * 0.5f - FVector2D(12.f);
	for (const FVector2D& C : { FVector2D(0, 0), FVector2D(-Hh.X, -Hh.Y), FVector2D(Hh.X, -Hh.Y), FVector2D(Hh.X, Hh.Y), FVector2D(-Hh.X, Hh.Y) })
	{
		const FIntPoint T = WorldToLocal(Loc + Rt.RotateVector(FVector(C.X, C.Y, 0)));
		if (!In(T) || Type[Idx(T)] != 1 || Owner[Idx(T)] != RI) return false;
	}
	return true;
}

void ARDSection::FootOf(const FRDPiece* P, const FTransform& T, FVector& OutCenter, FVector2D& OutSize, float& OutFront) const
{
	const FVector Sc = T.GetScale3D();
	FVector2D Half(P->Size.X * 0.5f, P->Size.Y * 0.5f);
	FVector2D Mid(0.f, 0.f);
	if (P->Mesh)
	{
		// (the mesh's box in the piece's frame (its Adjust): the larger of it and the nominal size, centred between them)
		const FBox B = P->Mesh->GetBoundingBox().TransformBy(P->Adjust);
		const float X0 = FMath::Min(-Half.X, (float)B.Min.X), X1 = FMath::Max(Half.X, (float)B.Max.X);
		const float Y0 = FMath::Min(-Half.Y, (float)B.Min.Y), Y1 = FMath::Max(Half.Y, (float)B.Max.Y);
		Half = FVector2D((X1 - X0) * 0.5f, (Y1 - Y0) * 0.5f); Mid = FVector2D((X0 + X1) * 0.5f, (Y0 + Y1) * 0.5f);
	}
	OutSize = FVector2D(Half.X * 2.f * Sc.X, Half.Y * 2.f * Sc.Y);
	OutCenter = T.GetLocation() + T.GetRotation().RotateVector(FVector(Mid.X * Sc.X, Mid.Y * Sc.Y, 0.f));
	OutFront = (Mid.X + Half.X) * Sc.X;
}

TArray<FVector> ARDSection::GetFootprints(TArray<FVector>& HalfYaw, TArray<FString>& Names) const
{
	TArray<FVector> Out; HalfYaw.Reset(); Names.Reset();
	for (const FFoot& F : Feet) { Out.Add(FVector(F.C, 0.f)); HalfYaw.Add(FVector(F.H, F.Yaw)); Names.Add(F.bAccess ? TEXT("access:") + F.Name.ToString() : F.Name.ToString()); }
	return Out;
}

TArray<FVector> ARDSection::GetRoomTiles(int32 I, TArray<float>& Heights) const
{
	TArray<FVector> Out; Heights.Reset();
	if (!Rooms.IsValidIndex(I)) return Out;
	const FRoom& Rm = Rooms[I];
	for (int32 X = Rm.Min.X; X < Rm.Max.X; ++X)
		for (int32 Y = Rm.Min.Y; Y < Rm.Max.Y; ++Y)
			if (Owner[Idx(FIntPoint(X, Y))] == I) { Out.Add(TileWorld(FIntPoint(X, Y))); Heights.Add(CeilAt(FIntPoint(X, Y))); }
	return Out;
}

// ------------------------------------------------------------------------------------------------ instancing helpers
bool ARDSection::AddPiece(FName Name, const FTransform& T, bool bForceNoCollision)
{
	const FRDPiece* P = Pc(Name);
	if (!P) return true;              // (false only for the castle's refusals below: callers go on as they did before)
	// (mistward: furniture stands on its room's floor (a shaped room has no floor outside its shape), never on another piece
	// and never where a container is opened; what hangs on a wall or from the ceiling is not on the floor)
	if (FurnRoom >= 0 && T.GetLocation().Z < 30.f && Rooms.IsValidIndex(FurnRoom))
	{
		FVector Fc; FVector2D Sz; float Front;
		FootOf(P, T, Fc, Sz, Front);
		const float Yaw = T.Rotator().Yaw;
		if (Generator->bShapedRooms && Rooms[FurnRoom].Shape != 0 && !OnRoomFloor(Fc, Yaw, Sz, FurnRoom)) return false;
		if (Generator->bTidyFurniture && P->bCollision && !bForceNoCollision)
		{
			if (!FootFree(Fc, Yaw, Sz, false)) return false;
			AddFoot(Fc, Yaw, Sz, false, Name);
		}
	}
	// (level 5: where the anvils stand, in play also for the saved start section, whose furniture is not built again)
	if (Generator && Name == Generator->AnvilPiece) AnvilPoints.Add(T.GetLocation());
	if (!bBuildStatic) return true;
	const FTransform W = P->Adjust * T;
	if (P->ActorClass)
	{
		FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		AActor* A = GetWorld()->SpawnActor<AActor>(P->ActorClass, W, Sp);
		if (A)
		{
			A->AttachToActor(this, FAttachmentTransformRules::KeepWorldTransform);
#if WITH_EDITOR
			if (bEditorBuilt) A->SetFolderPath(TEXT("RandomDungeon/Props"));
#endif
			OtherActors.Add(A);
		}
		return true;
	}
	if (!P->Mesh) return true;
	const bool bCol = (P->bCollision && !bForceNoCollision) || P->bHidden;
	(P->bHidden ? PendingHidden : bCol ? Pending : PendingNoCol).FindOrAdd(P->Mesh).Add(W);
	TMap<UStaticMesh*, UInstancedStaticMeshComponent*>& Map = P->bHidden ? HismsHidden : bCol ? Hisms : HismsNoCol;
	if (!Map.Contains(P->Mesh))
	{
		UInstancedStaticMeshComponent* H = NewObject<UInstancedStaticMeshComponent>(this, NAME_None, RF_Transactional);
		H->SetStaticMesh(P->Mesh);
		H->SetMobility(EComponentMobility::Static);
		H->SetupAttachment(RootComponent);
		H->SetCollisionProfileName(bCol ? TEXT("BlockAll") : TEXT("NoCollision"));
		if (P->bHidden) { H->SetVisibility(false); H->SetHiddenInGame(true); H->SetCastShadow(false); }
		if (!bCol) H->SetCanEverAffectNavigation(false);
		H->RegisterComponent();
		AddInstanceComponent(H);
		Map.Add(P->Mesh, H);
	}
	++NumInstances;
	return true;
}

bool ARDSection::AddPieceAt(FName Name, const FVector& Loc, float Yaw, float Scale, bool bForceNoCollision)
{
	return AddPiece(Name, FTransform(FRotator(0, Yaw, 0), Loc, FVector(Scale)), bForceNoCollision);
}

void ARDSection::FlushInstances()
{
	for (auto& KV : Pending) if (UInstancedStaticMeshComponent** H = Hisms.Find(KV.Key)) (*H)->AddInstances(KV.Value, false, true);
	for (auto& KV : PendingNoCol) if (UInstancedStaticMeshComponent** H = HismsNoCol.Find(KV.Key)) (*H)->AddInstances(KV.Value, false, true);
	for (auto& KV : PendingHidden) if (UInstancedStaticMeshComponent** H = HismsHidden.Find(KV.Key)) (*H)->AddInstances(KV.Value, false, true);
	Pending.Reset(); PendingNoCol.Reset(); PendingHidden.Reset();
}

UPointLightComponent* ARDSection::AddLight(const FVector& Loc, const FLinearColor& Color, float Candelas, float Radius, bool bShadows, float Flicker)
{
	if (!bBuildStatic) return nullptr;
	UPointLightComponent* L = NewObject<UPointLightComponent>(this, NAME_None, RF_Transactional);
	L->SetMobility(EComponentMobility::Movable);
	L->SetupAttachment(RootComponent);
	L->SetWorldLocation(Loc);
	L->SetIntensityUnits(ELightUnits::Candelas);
	L->SetIntensity(Candelas);
	L->SetLightColor(Color);
	L->SetAttenuationRadius(Radius);
	L->SetSourceRadius(6.f);
	L->SetCastShadows(bShadows);
	L->MaxDrawDistance = 9000.f;
	L->MaxDistanceFadeRange = 2000.f;
	if (Flicker > 0.f) { L->ComponentTags.Add(RDFlickerTag); L->ComponentTags.Add(FName(*FString::Printf(TEXT("F%.2f"), Flicker))); }
	L->RegisterComponent();
	AddInstanceComponent(L);
	++NumLights;
	return L;
}

void ARDSection::AddEffect(FName Name, const FVector& Loc, float Scale)
{
	// in play the fires are heard: where they are (also when the effect itself was saved with the start section)
	if (const UWorld* W = GetWorld(); W && W->IsGameWorld())
	{
		const int32 Kind = Name == TEXT("TorchFire") ? 0 : Name == TEXT("HearthFire") ? 2 : (Name == TEXT("BrazierFire") || Scale > 2.f) ? 1 : -1;
		if (Kind >= 0) FirePoints.Add({ Loc, (uint8)Kind });
	}
	if (!bBuildStatic) return;
	const TObjectPtr<UNiagaraSystem>* S = Generator->Effects.Find(Name);
	if (!S || !*S) return;
	UNiagaraComponent* C = NewObject<UNiagaraComponent>(this, NAME_None, RF_Transactional);
	C->SetAsset(*S);
	C->SetupAttachment(RootComponent);
	C->SetWorldLocation(Loc);
	C->SetWorldScale3D(FVector(Scale));
	C->SetAutoActivate(true);
	C->RegisterComponent();
	AddInstanceComponent(C);
}

int32 ARDSection::GetNumEffectsNear(FVector Location, float Radius) const
{
	int32 Num = 0;
	TInlineComponentArray<UNiagaraComponent*> Cs(this);
	for (const UNiagaraComponent* C : Cs) if (C && FVector::DistSquared(C->GetComponentLocation(), Location) <= Radius * Radius) ++Num;
	return Num;
}

int32 ARDSection::GetEffectParticlesNear(FVector Location, float Radius) const
{
	// (read on the game thread for a test: a count that is a frame old is good enough)
	int32 Num = 0;
	TInlineComponentArray<UNiagaraComponent*> Cs(this);
	for (const UNiagaraComponent* C : Cs)
	{
		if (!C || FVector::DistSquared(C->GetComponentLocation(), Location) > Radius * Radius) continue;
		Num += RDNiagaraParticles(C);
	}
	return Num;
}

void ARDSection::AddTorch(const FVector& WallPoint, float InYaw, float Candelas, bool bLit)
{
	// sconce on the wall (piece frame: back on the wall at x = 0, flame above its origin at FlameOffset = Hinge)
	const FRDPiece* P = this->Pc(TEXT("Torch"));
	AddPieceAt(TEXT("Torch"), WallPoint, InYaw, 1.f, true);
	if (!bLit || !P) return;
	const FVector Flame = WallPoint + FRotator(0, InYaw, 0).RotateVector(P->Hinge);
	AddEffect(TEXT("TorchFire"), Flame, 0.6f);
	AddLight(Flame + FRotator(0, InYaw, 0).RotateVector(FVector(25, 0, 10)), FLinearColor(1.f, 0.55f, 0.24f), Candelas, 1300.f, false, 0.18f);
}

USceneComponent* ARDSection::AddPivot(USceneComponent* Parent, const FTransform& Rel)
{
	USceneComponent* C = NewObject<USceneComponent>(this, NAME_None, RF_Transactional);
	C->ComponentTags.Add(RDInteractiveTag);
	C->SetMobility(EComponentMobility::Movable);
	C->SetupAttachment(Parent);
	C->SetRelativeTransform(Rel);
	C->RegisterComponent();
	AddInstanceComponent(C);
	return C;
}

UStaticMeshComponent* ARDSection::AddMesh(USceneComponent* Parent, UStaticMesh* Mesh, const FTransform& Rel, bool bCollision)
{
	UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this, NAME_None, RF_Transactional);
	C->ComponentTags.Add(RDInteractiveTag);
	C->SetMobility(EComponentMobility::Movable);
	C->SetStaticMesh(Mesh);
	C->SetupAttachment(Parent);
	C->SetRelativeTransform(Rel);
	C->SetCollisionProfileName(bCollision ? TEXT("BlockAllDynamic") : TEXT("NoCollision"));
	C->RegisterComponent();
	AddInstanceComponent(C);
	return C;
}

/** sign of an angle about Axis that swings Tip toward Want */
static float RDPickSign(const FVector& Axis, const FVector& Tip, const FVector& Want)
{
	const FVector P = FQuat(Axis, FMath::DegreesToRadians(60.f)).RotateVector(Tip);
	return FVector::DotProduct(P - Tip, Want) >= 0.f ? 1.f : -1.f;
}

void ARDSection::AddDoor(FIntPoint RoomTile, FIntPoint OutTile, int32 RoomIndex)
{
	if (!bBuildInteractive) return;
	// two leaves hinged on the doorway jambs (piece "DoorLeaf": leaf spans +Y from its origin, Hinge.Y = opening half width)
	const FRDPiece* P = this->Pc(TEXT("DoorLeaf"));
	if (!P) return;
	const FVector A = TileWorld(RoomTile), Bw = TileWorld(OutTile);
	const FVector Mid = (A + Bw) * 0.5f;
	const FVector Out = (Bw - A).GetSafeNormal();
	const float Yaw = FMath::RadiansToDegrees(FMath::Atan2(-Out.Y, -Out.X));      // +X into the room
	const FRotator Rot(0, Yaw, 0);
	const float Half = P->Hinge.Y, Inset = P->Hinge.X;
	const int32 First = Doors.Num();
	for (int32 Leaf = 0; Leaf < 2; ++Leaf)
	{
		const float S = Leaf == 0 ? -1.f : 1.f;          // hinge at -Half (leaf spans +Y) / +Half (leaf mirrored, spans -Y)
		const FVector HingeW = Mid + Rot.RotateVector(FVector(Inset, S * Half, 0));
		USceneComponent* Pv = AddPivot(RootComponent, FTransform(Rot, HingeW - GetActorLocation()));
		FTransform Rel = P->Adjust;
		if (Leaf == 1) Rel = Rel * FTransform(FRotator::ZeroRotator, FVector::ZeroVector, FVector(1, -1, 1));
		UStaticMeshComponent* M = AddMesh(Pv, P->Mesh, Rel, true);
		FMover Mv; Mv.Pivot = Pv; Mv.Parts = { M }; Mv.Closed = Pv->GetRelativeRotation().Quaternion(); Mv.bDoor = true; Mv.Kind = TEXT("door");
		Mv.LeafSign = -S;
		Mv.Center = Mid + FVector(0, 0, 100);
		Mv.Normal = Rot.RotateVector(FVector(1, 0, 0));
		Mv.TileA = RoomTile; Mv.TileB = OutTile;
		Mv.Partner = Leaf == 0 ? First + 1 : First;
		Doors.Add(Mv);
	}
}

void ARDSection::AddCellDoor(const FVector& HingeWorld, float Yaw, float Width)
{
	if (!bBuildInteractive) return;
	const FRDPiece* P = this->Pc(TEXT("CellDoor"));
	if (!P) return;
	USceneComponent* Pv = AddPivot(RootComponent, FTransform(FRotator(0, Yaw, 0), HingeWorld - GetActorLocation()));
	UStaticMeshComponent* M = AddMesh(Pv, P->Mesh, P->Adjust, true);
	FMover Mv; Mv.Pivot = Pv; Mv.Parts = { M }; Mv.Closed = Pv->GetRelativeRotation().Quaternion(); Mv.bDoor = true; Mv.bCell = true; Mv.Kind = TEXT("cell door");
	Mv.LeafSign = 1.f;
	Mv.Center = HingeWorld + FRotator(0, Yaw, 0).RotateVector(FVector(0, P->Size.Y * 0.5f, 100));
	Mv.Normal = FRotator(0, Yaw, 0).RotateVector(FVector(1, 0, 0));
	Doors.Add(Mv);
}

bool ARDSection::AddContainer(FName Name, const FVector& Loc, float Yaw, const FString& Kind)
{
	const FRDPiece* P = Pc(Name);
	if (!P) return true;              // (as AddPiece: false only for the castle's refusals)
	// (mistward: on its room's floor, on no other piece, and the space in front of it (where she stands to open it, the
	// lid's or doors' swing) clear of furniture and on the floor)
	if (FurnRoom >= 0 && Rooms.IsValidIndex(FurnRoom) && (Generator->bTidyFurniture || (Generator->bShapedRooms && Rooms[FurnRoom].Shape != 0)))
	{
		FVector Fc; FVector2D Sz; float Front;
		FootOf(P, FTransform(FRotator(0, Yaw, 0), Loc), Fc, Sz, Front);
		// (the way in at its whole size: FootFree takes its slack off each side (a shelf once stood 5 cm into a barrel's way))
		const FVector2D Way(95.f + 2.f * RDFootSlack, FMath::Max(Sz.Y, 90.f) + 2.f * RDFootSlack);
		const FVector WayAt = Loc + FRotator(0, Yaw, 0).RotateVector(FVector(Front + Way.X * 0.5f + 2.f, 0, 0));
		if (!OnRoomFloor(Fc, Yaw, Sz, FurnRoom) || !OnRoomFloor(WayAt, Yaw, Way, FurnRoom)) return false;
		if (Generator->bTidyFurniture)
		{
			if (!FootFree(Fc, Yaw, Sz, false) || !FootFree(WayAt, Yaw, Way, true)) return false;
			// (the way in on a lane is fine; on a tile already blocked it is not)
			const FIntPoint Wt = WorldToLocal(WayAt);
			if (In(Wt) && Blocked[Idx(Wt)]) return false;
			AddFoot(Fc, Yaw, Sz, false, Name);
			AddFoot(WayAt, Yaw, Way, true, Name);
		}
	}
	MarkBlocked(Loc, Yaw, FVector2D(P->Size.X, P->Size.Y));
	if (bCensus && P->Moving && (Kind == TEXT("chest") || Kind == TEXT("trunk"))) ++CensusChests;
	if (!bBuildInteractive || !P->Moving) return true;
	USceneComponent* Base = AddPivot(RootComponent, FTransform(FRotator(0, Yaw, 0), Loc - GetActorLocation()));
	AddMesh(Base, P->Mesh, P->Adjust, true);
	// moving part(s): a pivot at the hinge (piece frame)
	auto AddMoving = [&](UStaticMesh* Mesh, const FVector& Hinge, bool bVerticalAxis, int32 Partner)
	{
		USceneComponent* Hp = AddPivot(Base, FTransform(Hinge));
		// A moving part's mesh has its origin AT its hinge (a lid runs forward from it, a wardrobe door sideways), in the
		// body mesh's axes: on the hinge pivot it takes the piece's rotation and scale and no offset. (It used to get the
		// body's offset minus the hinge, as if it shared the body's origin: every lid lay on the floor inside its body and
		// every wardrobe door stood in the middle of the wardrobe.)
		FTransform Rel = P->Adjust; Rel.SetTranslation(FVector::ZeroVector);
		UStaticMeshComponent* M = AddMesh(Hp, Mesh, Rel, true);
		FMover Mv; Mv.Pivot = Hp; Mv.Parts = { M }; Mv.Kind = Kind; Mv.Partner = Partner;
		if (bVerticalAxis)
		{
			// wardrobe door: swings out toward the front (+X)
			Mv.Axis = FVector::UpVector;
			const FBox B = Mesh->GetBoundingBox().TransformBy(Rel);
			Mv.OpenAngle = 100.f * RDPickSign(Mv.Axis, FVector(0, B.GetCenter().Y, 0), FVector(1, 0, 0));
		}
		else
		{
			// lid: hinge axis along Y at the back, lifts up
			Mv.Axis = FVector::RightVector;
			const FBox B = Mesh->GetBoundingBox().TransformBy(Rel);
			Mv.OpenAngle = 100.f * RDPickSign(Mv.Axis, FVector(B.GetCenter().X, 0, 0), FVector::UpVector);
		}
		Mv.Center = Loc + FVector(0, 0, P->Size.Z * 0.6f);
		return Containers.Add(Mv);
	};
	const bool bWardrobe = Kind == TEXT("wardrobe");
	const int32 I0 = AddMoving(P->Moving, P->Hinge, bWardrobe, -1);
	if (P->Moving2)
	{
		const int32 I1 = AddMoving(P->Moving2, P->Hinge2, bWardrobe, I0);
		Containers[I0].Partner = I1;
	}
	// (mistward: one she has opened stays open, also when its set of rooms is generated again)
	if (Generator->bContainersStayOpen && Generator->IsContainerLooted(Coord, I0))
	{
		Containers[I0].Target = 1.f; Containers[I0].bLooted = true;
		if (Containers.IsValidIndex(Containers[I0].Partner)) { Containers[Containers[I0].Partner].Target = 1.f; Containers[Containers[I0].Partner].bLooted = true; }
	}
	return true;
}

void ARDSection::MarkBlocked(const FVector& Loc, float Yaw, const FVector2D& Size, bool bLaneToo)
{
	// conservative: the rotated footprint's bounding box (minus 15 cm) blocks the tiles it touches, never a lane tile
	if (bNoBlock) return;
	const FVector2D H = Size * 0.5f - FVector2D(15.f);
	if (H.X <= 0.f || H.Y <= 0.f) return;
	const FRotator Rt(0, Yaw, 0);
	FBox2D Bx(ForceInit);
	for (const FVector2D& C : { FVector2D(-H.X, -H.Y), FVector2D(H.X, -H.Y), FVector2D(H.X, H.Y), FVector2D(-H.X, H.Y) })
	{
		const FVector P = Loc + Rt.RotateVector(FVector(C.X, C.Y, 0)); Bx += FVector2D(P.X, P.Y);
	}
	const FIntPoint A = WorldToLocal(FVector(Bx.Min, 0)), Bt = WorldToLocal(FVector(Bx.Max, 0));
	for (int32 X = A.X; X <= Bt.X; ++X)
		for (int32 Y = A.Y; Y <= Bt.Y; ++Y)
		{
			const FIntPoint T(X, Y);
			if (!In(T)) continue;
			const int32 Rm = RoomAtLocal(T);
			if (!bLaneToo && Rm >= 0 && (T.X == Rooms[Rm].Lane.X || T.Y == Rooms[Rm].Lane.Y)) continue;
			Blocked[Idx(T)] = 1;
		}
}

// ------------------------------------------------------------------------------------------------ shell
static FName FloorFor(ERDRoomKind K, FRandomStream& R)
{
	switch (K)
	{
	case ERDRoomKind::Hall: case ERDRoomKind::Chapel: return TEXT("Floor_Stone");
	case ERDRoomKind::Barracks: case ERDRoomKind::Kitchen: case ERDRoomKind::GuardRoom: return R.RandBool() ? TEXT("Floor_Wood") : TEXT("Floor_Tiles");
	case ERDRoomKind::Library: case ERDRoomKind::Treasury: return TEXT("Floor_Tiles");
	case ERDRoomKind::Forge: case ERDRoomKind::Armory: return TEXT("Floor_Brick2");
	case ERDRoomKind::Junction: return TEXT("Floor_Corr");
	default: return R.RandBool() ? TEXT("Floor_Brick") : TEXT("Floor_Random");
	}
}

static FName WallFor(ERDRoomKind K, FRandomStream& R)
{
	switch (K)
	{
	case ERDRoomKind::Hall: case ERDRoomKind::Chapel: case ERDRoomKind::Library: return TEXT("Wall_Block");
	case ERDRoomKind::Prison: case ERDRoomKind::Torture: case ERDRoomKind::Crypt: return TEXT("Wall_Rough");
	case ERDRoomKind::Junction: return TEXT("Wall_Corr");
	default: return R.FRand() < 0.5f ? TEXT("Wall_Stone") : TEXT("Wall_Block");
	}
}

/** an integer hash that is the same in every session (FName hashes are not) */
static uint32 RDWallHash(uint32 A, uint32 B, uint32 C, uint32 D)
{
	uint32 H = A * 0x9E3779B1u ^ (B + 0x7F4A7C15u) * 0x85EBCA6Bu ^ (C + 0x165667B1u) * 0xC2B2AE35u ^ (D + 0x27D4EB2Fu) * 0x2545F491u;
	H ^= H >> 15; H *= 0x2C1B3C6Du; H ^= H >> 12; H *= 0x297A2D39u; H ^= H >> 15;
	return H;
}

FName ARDSection::WallVariant(FName Name, const FIntPoint& T, int32 Side, int32 Layer)
{
	// A wall piece may have variants in the generator's Pieces ("Wall_Rough_2", "Wall_Rough_3", ...): each segment takes
	// one of them, never the one of the segment before it along the wall nor of the one under it. One broken wall mesh
	// repeated along a room showed the same break every 3 m. The choice is a hash of where the segment is: it draws
	// nothing from the plan's random stream, so the dungeon is the same as before.
	TArray<FName>* V = WallVariants.Find(Name);
	if (!V)
	{
		V = &WallVariants.Add(Name);
		V->Add(Name);
		// (mistward: a theme's wall takes the theme's variants only)
		const bool bThemed = PcName(Name) != Name;
		for (int32 I = 2; I < 16; ++I)
		{
			const FName Nm(*FString::Printf(TEXT("%s_%d"), *Name.ToString(), I));
			if (!Pc(Nm) || (PcName(Nm) != Nm) != bThemed) break;
			V->Add(Nm);
		}
	}
	if (V->Num() < 2) { ++WallCounts.FindOrAdd(Name); return Name; }
	auto Key = [](const FIntPoint& P, int32 S, int32 L) { return (uint32)((P.X & 0x3ff) | ((P.Y & 0x3ff) << 10) | ((S & 3) << 20) | ((L & 0xff) << 22)); };
	// (the wall runs along Y on the -X / +X sides and along X on the -Y / +Y sides; tiles are visited in ascending X, then Y)
	const uint8* Before = WallPicks.Find(Key(T - (Side < 2 ? FIntPoint(0, 1) : FIntPoint(1, 0)), Side, Layer));
	const uint8* Below = Layer > 0 ? WallPicks.Find(Key(T, Side, Layer - 1)) : nullptr;
	TArray<uint8, TInlineAllocator<16>> Free;
	for (int32 I = 0; I < V->Num(); ++I) if (!(Before && *Before == I) && !(Below && *Below == I)) Free.Add((uint8)I);
	const uint32 H = RDWallHash((uint32)(Coord.X * 7919 + Coord.Y * 104729), (uint32)T.X, (uint32)T.Y, (uint32)(Side * 64 + Layer));
	const uint8 Pick = Free.Num() > 0 ? Free[H % Free.Num()] : (uint8)(H % V->Num());
	if ((Before && *Before == Pick) || (Below && *Below == Pick)) ++WallRepeats;
	WallPicks.Add(Key(T, Side, Layer), Pick);
	++WallCounts.FindOrAdd((*V)[Pick]);
	return (*V)[Pick];
}

float ARDSection::InwardYaw(int32 Side)
{
	// side: 0 -X wall (inward +X), 1 +X wall (inward -X), 2 -Y wall (inward +Y), 3 +Y wall (inward -Y)
	return Side == 0 ? 0.f : Side == 1 ? 180.f : Side == 2 ? 90.f : -90.f;
}

void ARDSection::BuildShell(FRandomStream& R)
{
	ShellPrepare(R);
	for (int32 X = 0; X < N; ++X) ShellColumn(R, X);
	ShellCorners();
}

void ARDSection::ShellPrepare(FRandomStream& R)
{
	ShellFloor.Reset(); ShellWall.Reset(); WallVariants.Reset(); WallPicks.Reset(); WallCounts.Reset(); WallRepeats = 0;
	WallSegments.Reset(); WallSegmentNames.Reset(); CellFrames.Reset(); CellHay.Reset(); CellSides = 0;
	for (const FRoom& Rm : Rooms) { ShellFloor.Add(FloorFor(Rm.Kind, R)); ShellWall.Add(WallFor(Rm.Kind, R)); }
}

void ARDSection::ShellColumn(FRandomStream& R, int32 X)
{
	const float S = Generator->TileSize;
	const TArray<FName>& RoomFloor = ShellFloor;
	const TArray<FName>& RoomWall = ShellWall;
	auto Stack = [this](FName Name, const FVector& Base, float Yaw, float Z0, float Z1, const FIntPoint& Tile, int32 Side)
	{
		const FRDPiece* P = Pc(Name);
		if (!P) return;
		const float H = FMath::Max(P->Size.Z - 2.f, 50.f);
		int32 Layer = Z0 > 1.f ? 1 : 0;
		// A broken wall has holes right through it: through them she saw the void behind and the backs of the rooms beyond,
		// and could climb into the bigger ones and fall out of the dungeon. A wall piece may have a backing ("<name>_Back": a
		// stone plate inside the wall's thickness, the back of a cavity seen through a hole) and a seal ("<name>_Seal": an
		// invisible box over the wall's face that keeps her out of the holes).
		const FName Back(*(Name.ToString() + TEXT("_Back"))), Seal(*(Name.ToString() + TEXT("_Seal")));
		// (mistward: a theme's wall has its own backing or none: the plain wall's would not fit it)
		const bool bThemed = PcName(Name) != Name;
		const bool bBack = Pc(Back) != nullptr && (PcName(Back) != Back) == bThemed, bSeal = Pc(Seal) != nullptr && (PcName(Seal) != Seal) == bThemed;
		for (float Z = Z0; Z < Z1 - 5.f; Z += H, ++Layer)
		{
			const FName Pick = WallVariant(Name, Tile, Side, Layer);
			const FVector At = Base + FVector(0, 0, Z);
			AddPieceAt(Pick, At, Yaw);
			if (!bBack && !bSeal) continue;
			if (bBack) AddPieceAt(Back, At, Yaw);
			if (bSeal) AddPieceAt(Seal, At, Yaw);
			WallSegments.Add(FTransform(FRotator(0, Yaw, 0), At)); WallSegmentNames.Add(Pick);
		}
	};
		for (int32 Y = 0; Y < N; ++Y)
		{
			const FIntPoint T(X, Y);
			const uint8 Ty = Type[Idx(T)];
			if (!Ty) continue;
			const int32 O = Owner[Idx(T)];
			const bool bRoom = O < 1000;
			const ERDRoomKind K = bRoom ? Rooms[O].Kind : ERDRoomKind::Junction;
			const bool bLow = !bRoom || K == ERDRoomKind::Junction;
			// (mistward: a dome's or a pyramid's tiles each have a ceiling of their own)
			const float Hgt = CeilAt(T) > 0.f ? CeilAt(T) : (bLow ? Generator->CorridorHeight : Generator->RoomHeight);
			const FVector C = TileWorld(T);
			// floor (occasional damaged / variant tiles), ceiling
			FName F = bRoom ? RoomFloor[O] : FName(TEXT("Floor_Corr"));
			if (R.FRand() < 0.12f && Pc(FName(*(F.ToString() + TEXT("_Alt"))))) F = FName(*(F.ToString() + TEXT("_Alt")));
			AddPieceAt(F, C, 90.f * R.RandRange(0, 3));
			AddPieceAt(bLow ? TEXT("Ceil_Corr") : TEXT("Ceil_Room"), C + FVector(0, 0, Hgt), 90.f * R.RandRange(0, 3));
			// walls
			for (int32 Side = 0; Side < 4; ++Side)
			{
				const FIntPoint Nb = T + Dir4[Side];
				const FVector Edge = C + FVector(Dir4[Side].X, Dir4[Side].Y, 0) * (S * 0.5f);
				const float Yaw = InwardYaw(Side);
				bool bWall = false, bDoorway = false;
				if (!In(Nb)) bWall = !Portals.Contains(T);
				else if (Type[Idx(Nb)] == 0) bWall = true;
				else if (Owner[Idx(Nb)] != O)
				{
					if (DoorEdges.Contains(EdgeKey(T, Nb))) bDoorway = bRoom && K != ERDRoomKind::Junction;
				}
				else if (bRoom && CeilAt(Nb) < Hgt - 5.f)
				{
					// (mistward: the step up to this tile's higher ceiling, seen from under it)
					Stack(RoomWall[O], Edge, Yaw, CeilAt(Nb), Hgt, T, Side);
				}
				if (bWall)
				{
					const FName WN = bRoom ? RoomWall[O] : FName(TEXT("Wall_Corr"));
					Stack(WN, Edge, Yaw, 0.f, Hgt, T, Side);
				}
				else if (bDoorway)
				{
					AddPieceAt(TEXT("Doorway"), Edge, Yaw);
					const FRDPiece* D = Pc(TEXT("Doorway"));
					Stack(RoomWall[O], Edge, Yaw, D ? D->Size.Z - 2.f : 300.f, Hgt, T, Side);
				}
			}
		}
}

void ARDSection::ShellCorners()
{
	const float S = Generator->TileSize;
	// room corners: columns hide the wall joints
	for (const FRoom& Rm : Rooms)
	{
		if (Rm.Kind == ERDRoomKind::Junction || Rm.Shape != 0) continue;       // (mistward: a shaped room's corners are elsewhere)
		const FVector A = TileWorld(Rm.Min) - FVector(S * 0.5f, S * 0.5f, 0), Bv = TileWorld(Rm.Max - FIntPoint(1, 1)) + FVector(S * 0.5f, S * 0.5f, 0);
		const FVector Cn[4] = { FVector(A.X, A.Y, 0), FVector(Bv.X, A.Y, 0), FVector(Bv.X, Bv.Y, 0), FVector(A.X, Bv.Y, 0) };
		for (int32 I = 0; I < 4; ++I)
		{
			const FVector In_ = ((A + Bv) * 0.5f - Cn[I]).GetSafeNormal2D();
			const FVector P = Cn[I] + In_ * 25.f;
			const FRDPiece* Pc = this->Pc(TEXT("CornerColumn"));
			if (!Pc) break;
			for (float Z = 0.f; Z < Generator->RoomHeight - 5.f; Z += Pc->Size.Z - 2.f) AddPieceAt(TEXT("CornerColumn"), P + FVector(0, 0, Z), 45.f + 90.f * I);
		}
	}
}

// ------------------------------------------------------------------------------------------------ furnishing
FBox2D ARDSection::RoomBox(const FRoom& Rm, float Inset) const
{
	const float S = Generator->TileSize;
	const FVector L = GetActorLocation();
	return FBox2D(FVector2D(L.X + Rm.Min.X * S + Inset, L.Y + Rm.Min.Y * S + Inset), FVector2D(L.X + Rm.Max.X * S - Inset, L.Y + Rm.Max.Y * S - Inset));
}

bool ARDSection::LaneFree(const FRoom& Rm, const FVector& P, float Radius) const
{
	// the lane tiles (door lines) plus 30 cm stay clear
	const float S = Generator->TileSize;
	const FVector Lc = TileWorld(Rm.Lane);
	const float Hw = S * 0.5f + 30.f + Radius;
	return FMath::Abs(P.X - Lc.X) > Hw && FMath::Abs(P.Y - Lc.Y) > Hw;
}

TArray<FVector> ARDSection::WallSlots(const FRoom& Rm, int32 Side, float Spacing, float Clear, float Margin) const
{
	TArray<FVector> Out;
	const FBox2D B = RoomBox(Rm, 0.f);
	const FVector Lc = TileWorld(Rm.Lane);
	const float S = Generator->TileSize;
	const bool bAlongY = Side < 2;
	const float A0 = (bAlongY ? B.Min.Y : B.Min.X) + Margin, A1 = (bAlongY ? B.Max.Y : B.Max.X) - Margin;
	const float Lane = bAlongY ? Lc.Y : Lc.X;
	const float Wl = Side == 0 ? B.Min.X : Side == 1 ? B.Max.X : Side == 2 ? B.Min.Y : B.Max.Y;
	const int32 Cnt = FMath::Max(1, FMath::FloorToInt((A1 - A0) / Spacing) + 1);
	const float Step = Cnt > 1 ? (A1 - A0) / (Cnt - 1) : 0.f;
	// (mistward: a shaped room has its rectangle's wall only where its floor reaches it)
	const int32 RI = (int32)(&Rm - Rooms.GetData());
	const bool bShaped = Rooms.IsValidIndex(RI) && Rm.Shape != 0;
	for (int32 I = 0; I < Cnt; ++I)
	{
		const float A = Cnt > 1 ? A0 + Step * I : (A0 + A1) * 0.5f;
		if (FMath::Abs(A - Lane) < S * 0.5f + Clear) continue;
		const FVector W = bAlongY ? FVector(Wl, A, 0) : FVector(A, Wl, 0);
		if (bShaped)
		{
			const FVector Inward = FRotator(0, InwardYaw(Side), 0).RotateVector(FVector(S * 0.5f, 0, 0));
			const FIntPoint T = WorldToLocal(W + Inward);
			if (!In(T) || Owner[Idx(T)] != RI) continue;
		}
		Out.Add(W);
	}
	return Out;
}

void ARDSection::FurnishWalls(FRandomStream& R, const FRoom& Rm, const TArray<FName>& Names, float Spacing, float Chance, bool bContainers)
{
	if (Names.Num() == 0) return;
	for (int32 Side = 0; Side < 4; ++Side)
		for (const FVector& W : WallSlots(Rm, Side, Spacing, 60.f, Spacing * 0.5f + 20.f))
		{
			if (R.FRand() > Chance) continue;
			const FName Nm = Names[R.RandRange(0, Names.Num() - 1)];
			const FRDPiece* P = this->Pc(Nm);
			if (!P) continue;
			const float Yaw = InwardYaw(Side);
			const FVector Pos = W + FRotator(0, Yaw, 0).RotateVector(FVector(P->Size.X * 0.5f + 32.f, 0, 0));
			if (!LaneFree(Rm, Pos, FMath::Max(P->Size.X, P->Size.Y) * 0.5f)) continue;
			if (bContainers && P->Moving) AddContainer(Nm, Pos, Yaw, Nm.ToString().ToLower());
			else if (AddPieceAt(Nm, Pos, Yaw)) MarkBlocked(Pos, Yaw, FVector2D(P->Size.X, P->Size.Y));
		}
}

void ARDSection::LightRoom(FRandomStream& R, const FRoom& Rm, int32 RoomIndex)
{
	const FBox2D B = RoomBox(Rm);
	const FVector Ctr(B.GetCenter(), 0);
	const FVector2D Sz = B.GetSize();
	const float Big = FMath::Max(Sz.X, Sz.Y);
	// wall torches: per kind brightness and spacing (cd); 0 = none
	float TorchCd = 0.f, Spacing = 900.f, Unlit = 0.f;
	FLinearColor Fill(1.f, 0.6f, 0.3f); float FillCd = 0.f;
	switch (Rm.Kind)
	{
	case ERDRoomKind::Hall: TorchCd = 160.f; Spacing = 600.f; FillCd = 0.f; break;
	case ERDRoomKind::Barracks: TorchCd = 90.f; Spacing = 900.f; break;
	case ERDRoomKind::Prison: TorchCd = 70.f; Spacing = 1200.f; Unlit = 0.25f; Fill = FLinearColor(0.55f, 0.65f, 1.f); FillCd = 10.f; break;
	case ERDRoomKind::Torture: TorchCd = 40.f; Spacing = 1500.f; Unlit = 0.3f; break;
	case ERDRoomKind::Storeroom: TorchCd = 70.f; Spacing = 1200.f; Unlit = 0.15f; break;
	case ERDRoomKind::Armory: TorchCd = 110.f; Spacing = 900.f; break;
	case ERDRoomKind::Kitchen: TorchCd = 80.f; Spacing = 1200.f; break;
	case ERDRoomKind::Library: TorchCd = 0.f; Fill = FLinearColor(1.f, 0.72f, 0.45f); FillCd = 8.f; break;
	case ERDRoomKind::Chapel: TorchCd = 0.f; Fill = FLinearColor(1.f, 0.78f, 0.55f); FillCd = 10.f; break;
	case ERDRoomKind::Crypt: TorchCd = 0.f; Fill = FLinearColor(0.45f, 0.75f, 0.7f); FillCd = 16.f; break;
	case ERDRoomKind::Treasury: TorchCd = 60.f; Spacing = 1200.f; break;
	case ERDRoomKind::GuardRoom: TorchCd = 110.f; Spacing = 900.f; break;
	case ERDRoomKind::Forge: TorchCd = 70.f; Spacing = 1200.f; break;
	default: TorchCd = 70.f; Spacing = 900.f; break;
	}
	if (TorchCd > 0.f)
		for (int32 Side = 0; Side < 4; ++Side)
			for (const FVector& W : WallSlots(Rm, Side, Spacing, 40.f, 140.f))
				AddTorch(W + FVector(0, 0, 250.f), InwardYaw(Side), TorchCd * R.FRandRange(0.8f, 1.2f), R.FRand() >= Unlit);
	if (FillCd > 0.f) AddLight(Ctr + FVector(0, 0, Generator->RoomHeight - 120.f), Fill, FillCd * Big / 900.f, Big * 0.9f, false, 0.f);
}

void ARDSection::EnsureAnvil()
{
	// (level 5: every set of rooms has an anvil; one with none from its forge or armory gets one in its start room or its
	// largest rooms, on a free tile off the lanes with free tiles all round it. No random stream is drawn: the layout stays)
	if (!Generator || !Generator->bAnvilEverySection) return;
	const FRDPiece* P = this->Pc(Generator->AnvilPiece);
	if (!P) return;
	// (the great hall: the start section's room at the origin tile, as GetStartRoomCenter finds it; this section may not be
	// among the generator's yet while it is built). The start section's great hall gets one whatever its forges have; any
	// other section one when it has none.
	const int32 Start = Generator->IsStartSection(Coord) ? RoomAt(FVector(Generator->TileSize * 0.5f, Generator->TileSize * 0.5f, 0.f)) : -1;
	if (Start >= 0 ? AnvilPoints.ContainsByPredicate([&](const FVector& A) { return RoomAt(A) == Start; }) : AnvilPoints.Num() > 0) return;
	TArray<int32> Order;
	for (int32 RI = 0; RI < Rooms.Num(); ++RI) if (Rooms[RI].Kind != ERDRoomKind::Junction && (Start < 0 || RI == Start || AnvilPoints.Num() == 0)) Order.Add(RI);
	auto Area = [this](int32 RI) { const FRoom& Rm = Rooms[RI]; return (Rm.Max.X - Rm.Min.X) * (Rm.Max.Y - Rm.Min.Y); };
	Order.Sort([&](int32 A, int32 B) { if ((A == Start) != (B == Start)) return A == Start; return Area(A) != Area(B) ? Area(A) > Area(B) : A < B; });
	for (const int32 RI : Order)
	{
		const FRoom& Rm = Rooms[RI];
		auto Free = [&](FIntPoint T) { return In(T) && Type[Idx(T)] == 1 && !Blocked[Idx(T)] && RoomAtLocal(T) == RI; };
		const FVector2D Mid((Rm.Min.X + Rm.Max.X) * 0.5f, (Rm.Min.Y + Rm.Max.Y) * 0.5f);
		// (a free tile off the lanes and off the walls' row, its four neighbours free; one not beside a lane before one
		// beside it, then the nearest the room's middle. The great hall's quadrant corners are full of furniture.)
		FIntPoint Pick(-1, -1); float PickD = MAX_flt;
		for (int32 X = Rm.Min.X + 1; X < Rm.Max.X - 1; ++X)
			for (int32 Y = Rm.Min.Y + 1; Y < Rm.Max.Y - 1; ++Y)
			{
				if (X == Rm.Lane.X || Y == Rm.Lane.Y) continue;
				const FIntPoint T(X, Y);
				if (!Free(T) || !Free(T + FIntPoint(1, 0)) || !Free(T + FIntPoint(-1, 0)) || !Free(T + FIntPoint(0, 1)) || !Free(T + FIntPoint(0, -1))) continue;
				const bool bBeside = FMath::Abs(X - Rm.Lane.X) <= 1 || FMath::Abs(Y - Rm.Lane.Y) <= 1;
				const float D = FVector2D::DistSquared(FVector2D(X + 0.5f, Y + 0.5f), Mid) + (bBeside ? 1e6f : 0.f);
				if (D < PickD) { PickD = D; Pick = T; }
			}
		if (Pick.X < 0) continue;
		const FVector At = TileWorld(Pick);
		const float Yaw = FMath::Abs(Pick.X - Rm.Lane.X) > FMath::Abs(Pick.Y - Rm.Lane.Y) ? 90.f : 0.f;
		AddPieceAt(Generator->AnvilPiece, At, Yaw);
		if (P->bCollision) MarkBlocked(At, Yaw, FVector2D(P->Size.X, P->Size.Y));
		AnvilRoom = RI;
		return;
	}
}

void ARDSection::Furnish(FRandomStream& R, int32 RI)
{
	const FRoom& Rm = Rooms[RI];
	const float S = Generator->TileSize, RH = Generator->RoomHeight;
	const FBox2D B = RoomBox(Rm);
	const FVector Ctr(B.GetCenter(), 0);
	const FVector Lc = TileWorld(Rm.Lane);
	const FVector2D Sz = B.GetSize();
	// quadrant centres (between the lanes and the walls)
	TArray<FVector> Quads;
	QuadBoxes.Reset();
	for (int32 Qx = 0; Qx < 2; ++Qx)
		for (int32 Qy = 0; Qy < 2; ++Qy)
		{
			const float X0 = Qx == 0 ? B.Min.X : Lc.X + S * 0.5f, X1 = Qx == 0 ? Lc.X - S * 0.5f : B.Max.X;
			const float Y0 = Qy == 0 ? B.Min.Y : Lc.Y + S * 0.5f, Y1 = Qy == 0 ? Lc.Y - S * 0.5f : B.Max.Y;
			if (X1 - X0 >= 280.f && Y1 - Y0 >= 280.f) { Quads.Add(FVector((X0 + X1) * 0.5f, (Y0 + Y1) * 0.5f, 0)); QuadBoxes.Add(FBox2D(FVector2D(X0, Y0), FVector2D(X1, Y1))); }
		}
	auto QuadSize = [&](const FVector& Q) { return FVector2D(FMath::Min(Q.X - B.Min.X, B.Max.X - Q.X) * 2.f - (FMath::Abs(Q.X - Lc.X) < 1 ? 0 : 0), FMath::Min(Q.Y - B.Min.Y, B.Max.Y - Q.Y) * 2.f); };
	// (mistward: the footprints placed in this room, so that nothing is set on anything else)
	FurnRoom = RI; Feet.Reset();
	ON_SCOPE_EXIT { FurnRoom = -1; };
	auto Center = [&](FName Nm, const FVector& P, float Yaw, bool bBlock = true, bool bLaneToo = false) -> bool
	{
		const FRDPiece* Pc = this->Pc(Nm);
		if (!Pc) return false;
		if (!AddPieceAt(Nm, P, Yaw)) return false;
		if (bBlock && Pc->bCollision) MarkBlocked(P, Yaw, FVector2D(Pc->Size.X, Pc->Size.Y), bLaneToo);
		return true;
	};
	auto Hang = [&](FName Nm, const FVector& P, float Yaw)   // from the ceiling (piece bottom at z 0: placed at ceiling - height)
	{
		const FRDPiece* Pc = this->Pc(Nm);
		// (mistward: under its own tile's ceiling: a dome's is higher; not over a tile cut out of a shaped room)
		const FIntPoint Tl = WorldToLocal(P);
		if (Rm.Shape != 0 && (!In(Tl) || Owner[Idx(Tl)] != RI)) return;
		const float Ch = Rm.Shape != 0 ? CeilAt(Tl) : RH;
		if (Pc) AddPieceAt(Nm, P + FVector(0, 0, Ch - Pc->Size.Z), Yaw, 1.f, true);
	};
	auto Candles = [&](const FVector& P, float Cd)
	{
		AddPieceAt(TEXT("Candles"), P, R.FRandRange(0, 360), 1.f, true);
		AddEffect(TEXT("CandleFire"), P + FVector(0, 0, 18), 1.f);
		AddLight(P + FVector(0, 0, 45), FLinearColor(1.f, 0.62f, 0.32f), Cd, 700.f, false, 0.12f);
	};
	auto TableSet = [&](const FVector& Q, float Yaw, FName Table, FName Seat, bool bCandles)
	{
		const FRDPiece* T = this->Pc(Table);
		if (!T) return;
		if (!Center(Table, Q, Yaw)) return;
		const FRotator Rt(0, Yaw, 0);
		const FRDPiece* St = this->Pc(Seat);
		if (St)
		{
			const float Off = T->Size.X * 0.5f + St->Size.X * 0.5f + 15.f;
			const int32 Cnt = FMath::Max(1, FMath::FloorToInt(T->Size.Y / FMath::Max(St->Size.Y + 20.f, 60.f)));
			for (int32 Sd = -1; Sd <= 1; Sd += 2)
				for (int32 I = 0; I < Cnt; ++I)
				{
					const float Yo = (I - (Cnt - 1) * 0.5f) * (T->Size.Y / Cnt);
					Center(Seat, Q + Rt.RotateVector(FVector(Sd * Off, Yo, 0)), Yaw + (Sd > 0 ? 180.f : 0.f), false);
				}
		}
		if (bCandles) Candles(Q + FVector(0, 0, T->Size.Z), 8.f);
	};
	switch (Rm.Kind)
	{
	case ERDRoomKind::Hall:
	{
		// colonnade, central carpet toward a throne dais, banners, chandeliers, braziers
		const bool bX = Sz.X >= Sz.Y;
		const float Ax = bX ? 0.f : 90.f;
		for (int32 Sd = -1; Sd <= 1; Sd += 2)
			for (float U = -0.3f; U <= 0.31f; U += 0.3f)
			{
				const FVector P = Ctr + (bX ? FVector(U * Sz.X, Sd * Sz.Y * 0.3f, 0) : FVector(Sd * Sz.X * 0.3f, U * Sz.Y, 0));
				if (!LaneFree(Rm, P, 80.f)) continue;
				Center(TEXT("Column"), P, 0.f);
			}
		AddPieceAt(TEXT("Carpet"), Ctr, Ax, 1.f, true);
		const FVector Dais = Ctr + (bX ? FVector(Sz.X * 0.5f - 260.f, 0, 0) : FVector(0, Sz.Y * 0.5f - 260.f, 0));
		const float DaisYaw = bX ? 180.f : -90.f;
		{
			// the dais sits on the far wall; it is off the lane only when that wall has no door
			const int32 Far = bX ? 1 : 3;
			if (!Rm.bDoorSide[Far]) { Center(TEXT("Dais"), Dais, DaisYaw, true, true); const FRDPiece* D = this->Pc(TEXT("Dais")); Center(TEXT("Throne"), Dais + FVector(0, 0, D ? D->Size.Z : 0), DaisYaw, true, true); }
		}
		for (int32 Side = 0; Side < 4; ++Side)
			for (const FVector& W : WallSlots(Rm, Side, 600.f, 120.f, 450.f))
				AddPieceAt(TEXT("Banner"), W + FRotator(0, InwardYaw(Side), 0).RotateVector(FVector(12, 0, 0)) + FVector(0, 0, RH - 40.f), InwardYaw(Side), 1.f, true);
		for (const FVector& Q : Quads)
		{
			Hang(TEXT("Chandelier"), Q, 0.f);
			AddLight(Q + FVector(0, 0, RH - 230.f), FLinearColor(1.f, 0.66f, 0.36f), 260.f, 2200.f, true, 0.06f);
		}
		for (const FVector& Cn : { FVector(B.Min.X + 150, B.Min.Y + 150, 0), FVector(B.Max.X - 150, B.Min.Y + 150, 0), FVector(B.Min.X + 150, B.Max.Y - 150, 0), FVector(B.Max.X - 150, B.Max.Y - 150, 0) })
		{
			Center(TEXT("Brazier"), Cn, 0.f);
			const FRDPiece* Bz = this->Pc(TEXT("Brazier"));
			const float Hz = Bz ? Bz->Size.Z : 110.f;
			AddEffect(TEXT("BrazierFire"), Cn + FVector(0, 0, Hz + RDBrazierFlameUp), RDBrazierFlame);
			AddLight(Cn + FVector(0, 0, Hz + 40.f), FLinearColor(1.f, 0.5f, 0.2f), 220.f, 1800.f, true, 0.2f);
		}
		FurnishWalls(R, Rm, { TEXT("Chest") }, 900.f, 0.35f, true);
		break;
	}
	case ERDRoomKind::Barracks:
	{
		// bunks along the walls, a footlocker at each, a table with stools in a quadrant
		for (int32 Side = 0; Side < 4; ++Side)
			for (const FVector& W : WallSlots(Rm, Side, 190.f, 110.f, 130.f))
			{
				const float Yaw = InwardYaw(Side);
				const FRDPiece* Bd = this->Pc(TEXT("Bed"));
				if (!Bd) break;
				const FVector P = W + FRotator(0, Yaw, 0).RotateVector(FVector(Bd->Size.X * 0.5f + 32.f, 0, 0));
				if (!LaneFree(Rm, P, Bd->Size.Y * 0.5f) || R.FRand() < 0.15f) continue;
				// (mistward: a bed that would lie in another (the corners, where two walls' rows meet) is not set, nor its chest)
				const bool bBed = Center(TEXT("Bed"), P, Yaw);
				if (!bBed && Generator->bTidyFurniture) continue;
				if (R.FRand() < 0.6f)
				{
					const FRDPiece* Ch = this->Pc(TEXT("Chest"));
					// (at the bed's foot, 10 cm clear of it: mistward measures both from their meshes (the bed's frame reaches past
					// its nominal size); the other levels keep the nominal sizes)
					float Off = Bd->Size.X * 0.5f + (Ch ? Ch->Size.X * 0.5f : 30.f) + 10.f;
					if (Generator->bTidyFurniture && Ch)
					{
						FVector Bc, Cc; FVector2D Bs, Cs; float BFront, CFront;
						FootOf(Bd, FTransform::Identity, Bc, Bs, BFront);
						FootOf(Ch, FTransform::Identity, Cc, Cs, CFront);
						Off = BFront + (Cs.X * 0.5f - Cc.X) + 10.f;       // (the bed's front, the chest's back from its origin)
					}
					const FVector Cp = P + FRotator(0, Yaw, 0).RotateVector(FVector(Off, 0, 0));
					if (LaneFree(Rm, Cp, 40.f)) AddContainer(TEXT("Chest"), Cp, Yaw, TEXT("chest"));
				}
			}
		if (Quads.Num()) TableSet(Quads[R.RandRange(0, Quads.Num() - 1)], R.RandBool() ? 0.f : 90.f, TEXT("TableLong"), TEXT("Stool"), true);
		break;
	}
	case ERDRoomKind::Prison:
	{
		// cells along the two walls parallel to one lane: grating front with a cell door, straw, a bucket, chains
		const bool bX = R.RandBool();
		for (int32 Side = bX ? 0 : 2; Side < (bX ? 2 : 4); ++Side)
		{
			if (Rm.bDoorSide[Side] && false) continue;
			const float Yaw = InwardYaw(Side);
			const FRotator Rt(0, Yaw, 0);
			const float Depth = S;   // one tile deep
			TArray<FVector> CellWalls;      // (the wall point of each cell built along this wall)
			for (const FVector& W : WallSlots(Rm, Side, S, 160.f, S * 0.5f))
			{
				// cell: the tile against the wall (W is the wall point at the tile middle)
				const FVector Front = W + Rt.RotateVector(FVector(Depth, 0, 0));
				const FVector Inner = W + Rt.RotateVector(FVector(Depth * 0.5f, 0, 0));
				if (!LaneFree(Rm, Inner, S * 0.5f - 10.f)) continue;
				// grating across the cell front (piece runs along Y), cell door in its middle as a separate leaf
				// (the bars have no usable collision of their own: invisible blockers stand in for them)
				// (mistward: the door's half of the front is the cell's right; at a row's end against the room's wall, that wall's
				// seal stood in the doorway and a released monster could not get out: such a cell is barred all across. The draw
				// stays, so the layout's stream does not move.)
				const FIntPoint NextT = WorldToLocal(Inner + Rt.RotateVector(FVector(0, S, 0)));
				const bool bDoorAtWall = Generator->bTidyFurniture && !(In(NextT) && Owner[Idx(NextT)] == RI);
				const bool bWithDoor = R.FRand() < 0.5f;
				if (bWithDoor && !bDoorAtWall)
				{
					AddPieceAt(TEXT("CellFrame"), Front, Yaw);
					AddPieceAt(TEXT("CellBlockHalf"), Front, Yaw);
					const FRDPiece* Cd = this->Pc(TEXT("CellDoor"));
					// (the half grating covers [-150, 0] of the front, the door the other half: hinged 5 cm in from the
					// corner, its leaf (3 cm past the hinge to 147 short of it) covers [-2, 148], overlapping the bars' blocker.
					// Hinged at +75 it covered [-72, 75] twice over and left a 75 cm gap at the corner.)
					const int32 DoorIdx = Doors.Num();
				if (Cd) AddCellDoor(Front + Rt.RotateVector(FVector(0, S * 0.5f - 5.f, 0)), Yaw + 180.f, Cd->Size.Y);
				// (mistward: a cell with a door may hold someone)
				if (Doors.Num() > DoorIdx) { FCell Cl; Cl.Frame = FTransform(Rt, Inner); Cl.Door = DoorIdx; Cells.Add(Cl); }
				}
				else { AddPieceAt(TEXT("Grating"), Front, Yaw); AddPieceAt(TEXT("CellBlock"), Front, Yaw); }
				// (the hay pile is a mound as tall as she is, which looked like rock: it blocks)
				// (mistward: on the barred half, out of the way to the door)
				const float HaySide = R.FRandRange(-60, 60);
				const FVector Hay = Inner + Rt.RotateVector(FVector(-30, Generator->bTidyFurniture ? -30.f - FMath::Abs(HaySide) : HaySide, 0));
				// (mistward: no mound: it read as a big rock taking half the cell (the user's of 2026-10-27); a cell holds a
				// prisoner, a monster or nothing. Its turn is still drawn: the stream stays where it was)
				const float HayYaw = R.FRandRange(0, 360);
				if (!Generator->bTidyFurniture) AddPieceAt(TEXT("HayPile"), Hay, HayYaw);
				if (R.FRand() < 0.5f) AddPieceAt(TEXT("Bones"), Inner + Rt.RotateVector(FVector(20, R.FRandRange(-80, 80), 0)), R.FRandRange(0, 360), 1.f, true);
				AddPieceAt(TEXT("Shackles"), W + Rt.RotateVector(FVector(6, 0, 160)), Yaw, 1.f, true);
				const FIntPoint T = WorldToLocal(Inner);
				if (In(T)) Blocked[Idx(T)] = 1;
				CellWalls.Add(W);
				CellFrames.Add(FTransform(Rt, Inner)); CellHay.Add(Hay);
			}
			// The cells' sides: only the front had bars, so a cell beside the lane (the slots near it stay empty) or at a
			// gap was open on that side, and two cells side by side were one. Bars (and their invisible blocker) on every
			// side the room's own wall does not close, once between two cells. Nothing drawn from R: the layout stays.
			const FBox2D Bx = RoomBox(Rm, 0.f);
			const bool bAlongY = Side < 2;
			const float Lo = bAlongY ? Bx.Min.Y : Bx.Min.X, Hi = bAlongY ? Bx.Max.Y : Bx.Max.X;
			auto Along = [bAlongY](const FVector& P) { return bAlongY ? P.Y : P.X; };
			for (int32 I = 0; I < CellWalls.Num(); ++I)
				for (int32 D = -1; D <= 1; D += 2)
				{
					const float Ed = Along(CellWalls[I]) + D * S * 0.5f;
					if (Ed < Lo + 10.f || Ed > Hi - 10.f) continue;       // the room's wall closes it
					const bool bNext = CellWalls.ContainsByPredicate([&](const FVector& Q) { return FMath::Abs(Along(Q) - (Along(CellWalls[I]) + D * S)) < 1.f; });
					if (bNext && D < 0) continue;                          // (between two cells: once)
					const FVector Mid = CellWalls[I] + FRotator(0, InwardYaw(Side), 0).RotateVector(FVector(Depth * 0.5f, 0, 0)) + (bAlongY ? FVector(0, 1, 0) : FVector(1, 0, 0)) * (D * S * 0.5f);
					AddPieceAt(TEXT("Grating"), Mid, InwardYaw(Side) + 90.f);
					AddPieceAt(TEXT("CellBlock"), Mid, InwardYaw(Side) + 90.f);
					++CellSides;
				}
		}
		for (const FVector& Q : Quads) if (R.FRand() < 0.5f) Hang(TEXT("Chain"), Q, R.FRandRange(0, 360));
		if (Quads.Num() && R.FRand() < 0.6f) TableSet(Quads[0], 0.f, TEXT("TableSmall"), TEXT("Stool"), true);
		break;
	}
	case ERDRoomKind::Torture:
	{
		for (int32 I = 0; I < Quads.Num(); ++I)
		{
			const FVector Q = Quads[I];
			const int32 Pk = (I + R.RandRange(0, 3)) % 4;
			if (Pk == 0) Center(TEXT("Gibbet"), Q, R.FRandRange(0, 360));
			else if (Pk == 1) Center(TEXT("CageLarge"), Q, R.FRandRange(0, 360));
			else if (Pk == 2) { Center(TEXT("PrepTable"), Q, R.RandBool() ? 0.f : 90.f); AddPieceAt(TEXT("Bones"), Q + FVector(60, 0, 0), 0.f, 1.f, true); }
			else Hang(TEXT("CageHanging"), Q, R.FRandRange(0, 360));
		}
		const FVector Bz = Quads.Num() ? (Quads[0] + Ctr) * 0.5f : Ctr;
		FurnishWalls(R, Rm, { TEXT("ToolBoard"), TEXT("PrepTable") }, 400.f, 0.5f);
		for (int32 Side = 0; Side < 4; ++Side)
			for (const FVector& W : WallSlots(Rm, Side, 260.f, 80.f, 200.f))
				if (R.FRand() < 0.5f) { AddPieceAt(TEXT("Shackles"), W + FVector(0, 0, 170.f), InwardYaw(Side), 1.f, true); AddPieceAt(TEXT("Shackles"), W + FVector(0, 0, 60.f), InwardYaw(Side), 1.f, true); }
		for (const FVector& Q : Quads)
		{
			const FVector P = (Q + Lc) * 0.5f;
			if (!LaneFree(Rm, P, 60.f)) continue;
			Center(TEXT("Brazier"), P, 0.f);
			const FRDPiece* Bp = this->Pc(TEXT("Brazier"));
			const float Hz = Bp ? Bp->Size.Z : 110.f;
			AddEffect(TEXT("BrazierFire"), P + FVector(0, 0, Hz + RDBrazierFlameUp), RDBrazierFlame);
			AddLight(P + FVector(0, 0, Hz + 40.f), FLinearColor(1.f, 0.32f, 0.12f), 140.f, 1500.f, true, 0.3f);
			break;
		}
		(void)Bz;
		break;
	}
	case ERDRoomKind::Storeroom:
	{
		// shelving and barrels / crates along the walls, rows of stock filling the quadrants (aisles left between rows)
		FurnishWalls(R, Rm, { TEXT("ShelfRack"), TEXT("Barrel"), TEXT("Barrel2"), TEXT("Crate"), TEXT("Crate2"), TEXT("ShelfRack") }, 140.f, 0.95f, true);
		for (const FBox2D& Qb : QuadBoxes)
		{
			const FBox2D In_ = Qb.ExpandBy(-150.f);
			if (In_.GetSize().X < 100.f || In_.GetSize().Y < 100.f) continue;
			const bool bRowsX = In_.GetSize().X >= In_.GetSize().Y;
			for (float A = 0.f; A <= (bRowsX ? In_.GetSize().Y : In_.GetSize().X) + 1.f; A += 240.f)        // rows 2.4 m apart
				for (float U = 0.f; U <= (bRowsX ? In_.GetSize().X : In_.GetSize().Y) + 1.f; U += 110.f)
				{
					const FVector P = bRowsX ? FVector(In_.Min.X + U, In_.Min.Y + A, 0) : FVector(In_.Min.X + A, In_.Min.Y + U, 0);
					if (R.FRand() < 0.2f || !LaneFree(Rm, P, 60.f)) continue;
					const int32 Pk = R.RandRange(0, 3);
					const FName Nm = Pk == 0 ? TEXT("Barrel") : Pk == 1 ? TEXT("Barrel2") : Pk == 2 ? TEXT("Crate") : TEXT("Crate2");
					AddContainer(Nm, P, 90.f * R.RandRange(0, 3), Pk < 2 ? TEXT("barrel") : TEXT("crate"));
				}
		}
		break;
	}
	case ERDRoomKind::Armory:
	{
		// weapons on the walls (shields high, swords / axes / spears on racks), trunks of gear, a work table
		for (int32 Side = 0; Side < 4; ++Side)
		{
			const float Yaw = InwardYaw(Side);
			const FRotator Rt(0, Yaw, 0);
			int32 K = 0;
			for (const FVector& W : WallSlots(Rm, Side, 160.f, 80.f, 120.f))
			{
				AddPieceAt(TEXT("Shield"), W + Rt.RotateVector(FVector(14, 0, 0)) + FVector(0, 0, 260.f), Yaw, 1.f, true);
				const FName Wpn = (K++ % 3) == 0 ? TEXT("Spear") : (K % 3) == 1 ? TEXT("Sword") : TEXT("Axe");
				AddPieceAt(Wpn, W + Rt.RotateVector(FVector(16, 0, 0)) + FVector(0, 0, 150.f), Yaw, 1.f, true);
			}
		}
		FurnishWalls(R, Rm, { TEXT("Trunk"), TEXT("Chest"), TEXT("Wardrobe") }, 300.f, 0.6f, true);
		// weapon tables: blades, axes and spears laid out on long tables; a grinding / repair corner with the anvil
		for (int32 I = 0; I < Quads.Num(); ++I)
		{
			const FVector Q = Quads[I];
			if (I == 1) { Center(TEXT("Anvil"), Q, R.FRandRange(0, 360)); Center(TEXT("QuenchTub"), Q + FVector(110, 0, 0), 0.f); continue; }
			const float Yaw = QuadBoxes[I].GetSize().X >= QuadBoxes[I].GetSize().Y ? 90.f : 0.f;
			Center(TEXT("TableLong"), Q, Yaw);
			const FRDPiece* T = this->Pc(TEXT("TableLong"));
			if (!T) continue;
			const FRotator Rt(0, Yaw, 0);
			for (int32 K = 0; K < 4; ++K)
			{
				const FName Wpn = K % 3 == 0 ? TEXT("SwordFlat") : K % 3 == 1 ? TEXT("AxeFlat") : TEXT("SpearFlat");
				const FVector P = Q + Rt.RotateVector(FVector(R.FRandRange(-15, 15), (K - 1.5f) * T->Size.Y * 0.22f, T->Size.Z));
				const float PYaw = Yaw + 90.f + R.FRandRange(-8, 8);
				// (the third list: the table's weapons are real ones of the room's tier, to take up; the draws stay as they were)
				if (Generator->bWeaponPickups)
				{
					const FName It = Generator->PickupItemFor(Coord, Pickups.Num());
					if (!It.IsNone()) { AddPickup(It, P, Yaw); continue; }
				}
				AddPieceAt(Wpn, P, PYaw, 1.f, true);
			}
		}
		break;
	}
	case ERDRoomKind::Kitchen:
	{
		// hearth on one wall, cauldron, prep tables, pot rack, long mess table with benches
		int32 HearthSide = -1;
		for (int32 Side = 0; Side < 4 && HearthSide < 0; ++Side) if (!Rm.bDoorSide[Side]) HearthSide = Side;
		const bool bHearthOnDoor = HearthSide < 0;
		if (HearthSide < 0) HearthSide = 0;
		{
			const float Yaw = InwardYaw(HearthSide);
			const FRotator Rt(0, Yaw, 0);
			const FBox2D Bx = B;
			FVector Wall = HearthSide == 0 ? FVector(Bx.Min.X, Lc.Y, 0) : HearthSide == 1 ? FVector(Bx.Max.X, Lc.Y, 0) : HearthSide == 2 ? FVector(Lc.X, Bx.Min.Y, 0) : FVector(Lc.X, Bx.Max.Y, 0);
			if (bHearthOnDoor) Wall += (HearthSide < 2 ? FVector(0, 1, 0) : FVector(1, 0, 0)) * 450.f;      // every wall has a door: off the doorway lane
			const FRDPiece* Fp = this->Pc(TEXT("Fireplace"));
			if (Fp)
			{
				const FVector P = Wall + Rt.RotateVector(FVector(Fp->Size.X * 0.5f + 30.f, 0, 0));
				Center(TEXT("Fireplace"), P, Yaw, true, true);      // (on the lane at a wall without a door: block it)
				AddEffect(TEXT("HearthFire"), P + Rt.RotateVector(FVector(0, 0, 0)) + FVector(0, 0, 42), RDHearthFlame);
				AddLight(P + Rt.RotateVector(FVector(80, 0, 0)) + FVector(0, 0, 90), FLinearColor(1.f, 0.48f, 0.18f), 260.f, 1800.f, true, 0.25f);
			}
		}
		FurnishWalls(R, Rm, { TEXT("PrepTable"), TEXT("BreadOven"), TEXT("ShelfRack"), TEXT("Barrel"), TEXT("Crate") }, 300.f, 0.7f, true);
		for (int32 I = 0; I < Quads.Num(); ++I)
		{
			if (I == 0) { Center(TEXT("Tripod"), Quads[I], 0.f); Center(TEXT("Cauldron"), Quads[I], 0.f, false); AddEffect(TEXT("CandleFire"), Quads[I] + FVector(0, 0, 10), 2.5f); AddLight(Quads[I] + FVector(0, 0, 60), FLinearColor(1.f, 0.5f, 0.2f), 60.f, 900.f, false, 0.3f); }
			else TableSet(Quads[I], R.RandBool() ? 0.f : 90.f, TEXT("TableLong"), TEXT("Bench"), I == 1);
		}
		for (const FVector& Q : Quads) { Hang(TEXT("PotRack"), Q + FVector(0, 0, -150), 0.f); break; }
		break;
	}
	case ERDRoomKind::Library:
	{
		FurnishWalls(R, Rm, { TEXT("Bookshelf"), TEXT("Bookshelf"), TEXT("Bookshelf2") }, 240.f, 0.9f);
		for (const FVector& Q : Quads)
		{
			const float Yaw = R.RandBool() ? 0.f : 90.f;
			Center(TEXT("Desk"), Q, Yaw);
			const FRDPiece* D = this->Pc(TEXT("Desk"));
			const float Hz = D ? D->Size.Z : 90.f;
			Center(TEXT("Chair"), Q + FRotator(0, Yaw, 0).RotateVector(FVector(-(D ? D->Size.X * 0.5f + 45.f : 90.f), 0, 0)), Yaw, false);
			AddPieceAt(TEXT("Books"), Q + FVector(R.FRandRange(-30, 30), R.FRandRange(-30, 30), Hz), R.FRandRange(0, 360), 1.f, true);
			Candles(Q + FRotator(0, Yaw, 0).RotateVector(FVector(0, D ? D->Size.Y * 0.35f : 40.f, Hz)), 18.f);
		}
		for (const FVector& Q : Quads) { const FVector P = (Q + Lc) * 0.5f; if (LaneFree(Rm, P, 60.f)) { Center(TEXT("CandleStand"), P, 0.f); AddLight(P + FVector(0, 0, 200), FLinearColor(1.f, 0.66f, 0.38f), 50.f, 1200.f, false, 0.1f); } }
		break;
	}
	case ERDRoomKind::Chapel:
	{
		// pews facing an altar on a wall without a door, candle stands, a carpet aisle, paintings
		int32 AltarSide = -1;
		for (int32 Side = 0; Side < 4 && AltarSide < 0; ++Side) if (!Rm.bDoorSide[Side]) AltarSide = Side;
		const bool bAltarOnDoor = AltarSide < 0;
		if (AltarSide < 0) AltarSide = 1;
		const float Yaw = InwardYaw(AltarSide);
		const FRotator Rt(0, Yaw, 0);
		const FVector Wall = (AltarSide == 0 ? FVector(B.Min.X, Lc.Y, 0) : AltarSide == 1 ? FVector(B.Max.X, Lc.Y, 0) : AltarSide == 2 ? FVector(Lc.X, B.Min.Y, 0) : FVector(Lc.X, B.Max.Y, 0))
			+ (bAltarOnDoor ? (AltarSide < 2 ? FVector(0, 1, 0) : FVector(1, 0, 0)) * 450.f : FVector::ZeroVector);
		const FVector Altar = Wall + Rt.RotateVector(FVector(160.f, 0, 0));
		Center(TEXT("Altar"), Altar, Yaw, true, true);
		const FRDPiece* Al = this->Pc(TEXT("Altar"));
		Candles(Altar + FVector(0, 0, Al ? Al->Size.Z : 100.f) + Rt.RotateVector(FVector(0, -50, 0)), 30.f);
		Candles(Altar + FVector(0, 0, Al ? Al->Size.Z : 100.f) + Rt.RotateVector(FVector(0, 50, 0)), 30.f);
		AddPieceAt(TEXT("Painting"), Wall + Rt.RotateVector(FVector(12, 0, 0)) + FVector(0, 0, 330.f), Yaw, 1.f, true);
		for (int32 Sd = -1; Sd <= 1; Sd += 2)
		{
			const FVector Cs = Altar + Rt.RotateVector(FVector(40.f, Sd * 260.f, 0));
			Center(TEXT("CandleStand"), Cs, Yaw);
			AddLight(Cs + FVector(0, 0, 230), FLinearColor(1.f, 0.7f, 0.42f), 70.f, 1500.f, true, 0.08f);
		}
		// pews: rows across the room on both sides of the aisle
		const float Len = (AltarSide < 2 ? Sz.X : Sz.Y);
		for (float D = 450.f; D < Len - 250.f; D += 200.f)
			for (int32 Sd = -1; Sd <= 1; Sd += 2)
			{
				const FVector P = Altar + Rt.RotateVector(FVector(D, Sd * 270.f, 0));
				if (!B.ExpandBy(-120.f).IsInside(FVector2D(P.X, P.Y)) || !LaneFree(Rm, P, 40.f)) continue;
				Center(TEXT("Pew"), P, Yaw + 180.f);
			}
		AddPieceAt(TEXT("CarpetLong"), (Altar + Ctr) * 0.5f + FVector(0, 0, 1), Yaw + 90.f, 1.f, true);
		// chandeliers over the nave, candle stands along the side walls
		for (const FVector& Q : Quads)
		{
			Hang(TEXT("Chandelier"), Q, 0.f);
			AddLight(Q + FVector(0, 0, RH - 230.f), FLinearColor(1.f, 0.7f, 0.42f), 110.f, 1800.f, false, 0.06f);
		}
		for (int32 Side = 0; Side < 4; ++Side)
		{
			if (Side == AltarSide || Side == (AltarSide ^ 1)) continue;
			for (const FVector& W : WallSlots(Rm, Side, 700.f, 120.f, 350.f))
			{
				const FVector P = W + FRotator(0, InwardYaw(Side), 0).RotateVector(FVector(70.f, 0, 0));
				if (!LaneFree(Rm, P, 50.f)) continue;
				Center(TEXT("CandleStand"), P, InwardYaw(Side));
				AddLight(P + FVector(0, 0, 210), FLinearColor(1.f, 0.68f, 0.4f), 35.f, 1000.f, false, 0.1f);
			}
		}
		break;
	}
	case ERDRoomKind::Crypt:
	{
		// rows of tombs, bone piles, candles on the floor (dim, green-grey)
		for (const FVector& Q : Quads)
		{
			const FVector2D Qs = QuadSize(Q);
			const bool bX = Qs.X > Qs.Y;
			for (int32 K = -1; K <= 1; K += 2)
			{
				const FVector P = Q + (bX ? FVector(K * 120.f, 0, 0) : FVector(0, K * 120.f, 0));
				if (!LaneFree(Rm, P, 60.f)) continue;
				const FName Tn = FName(*FString::Printf(TEXT("Tomb%d"), R.RandRange(1, 4)));
				Center(Tn, P, bX ? 0.f : 90.f);
			}
			Candles(Q + FVector(R.FRandRange(-40, 40), R.FRandRange(-40, 40), 0), 14.f);
			const FVector2D Qh = Qs * 0.35f;
			Candles(Q + FVector(R.RandBool() ? Qh.X : -Qh.X, R.RandBool() ? Qh.Y : -Qh.Y, 0), 10.f);
		}
		FurnishWalls(R, Rm, { TEXT("BonePile"), TEXT("BonePile2"), TEXT("Debris"), TEXT("Bones") }, 260.f, 0.6f);
		break;
	}
	case ERDRoomKind::Treasury:
	{
		FurnishWalls(R, Rm, { TEXT("Chest"), TEXT("Trunk"), TEXT("Chest") }, 160.f, 0.8f, true);
		for (const FVector& Q : Quads)
		{
			Center(TEXT("Pedestal"), Q, 0.f);
			const FRDPiece* Pd = this->Pc(TEXT("Pedestal"));
			const float Hz = Pd ? Pd->Size.Z : 100.f;
			AddPieceAt(TEXT("Crystal"), Q + FVector(0, 0, Hz), R.FRandRange(0, 360), 1.f, true);
			AddLight(Q + FVector(0, 0, Hz + 80.f), FLinearColor(0.55f, 0.6f, 1.f), 45.f, 900.f, false, 0.05f);
		}
		break;
	}
	case ERDRoomKind::GuardRoom:
	{
		if (Quads.Num()) TableSet(Quads[0], 0.f, TEXT("TableSmall"), TEXT("Stool"), true);
		FurnishWalls(R, Rm, { TEXT("Chest"), TEXT("Barrel"), TEXT("Wardrobe") }, 380.f, 0.6f, true);
		for (int32 Side = 0; Side < 4; ++Side)
			for (const FVector& W : WallSlots(Rm, Side, 500.f, 120.f, 200.f))
				if (R.FRand() < 0.4f) AddPieceAt(TEXT("Shield"), W + FRotator(0, InwardYaw(Side), 0).RotateVector(FVector(14, 0, 0)) + FVector(0, 0, 230.f), InwardYaw(Side), 1.f, true);
		if (Quads.Num() > 1) Center(TEXT("Bed"), Quads[1], 0.f);
		break;
	}
	case ERDRoomKind::Forge:
	{
		int32 Sd0 = -1;
		for (int32 Side = 0; Side < 4 && Sd0 < 0; ++Side) if (!Rm.bDoorSide[Side]) Sd0 = Side;
		const bool bForgeOnDoor = Sd0 < 0;
		if (Sd0 < 0) Sd0 = 0;
		const float Yaw = InwardYaw(Sd0);
		const FRotator Rt(0, Yaw, 0);
		const FVector Wall = (Sd0 == 0 ? FVector(B.Min.X, Lc.Y, 0) : Sd0 == 1 ? FVector(B.Max.X, Lc.Y, 0) : Sd0 == 2 ? FVector(Lc.X, B.Min.Y, 0) : FVector(Lc.X, B.Max.Y, 0))
			+ (bForgeOnDoor ? (Sd0 < 2 ? FVector(0, 1, 0) : FVector(1, 0, 0)) * 450.f : FVector::ZeroVector);
		const FRDPiece* Fg = this->Pc(TEXT("Forge"));
		if (Fg)
		{
			const FVector P = Wall + Rt.RotateVector(FVector(Fg->Size.X * 0.5f + 35.f, 0, 0));
			Center(TEXT("Forge"), P, Yaw, true, true);
			AddEffect(TEXT("BrazierFire"), P + FVector(0, 0, Fg->Size.Z * 0.55f), RDForgeFlame);
			AddLight(P + Rt.RotateVector(FVector(90, 0, 0)) + FVector(0, 0, 120), FLinearColor(1.f, 0.42f, 0.12f), 300.f, 1800.f, true, 0.25f);
		}
		for (int32 I = 0; I < Quads.Num(); ++I)
		{
			const FName Nm = I == 0 ? TEXT("Anvil") : I == 1 ? TEXT("QuenchTub") : TEXT("TableLong");
			Center(Nm, Quads[I], R.RandBool() ? 0.f : 90.f);
		}
		FurnishWalls(R, Rm, { TEXT("ToolBoard"), TEXT("Firewood"), TEXT("Barrel"), TEXT("Crate") }, 300.f, 0.6f, true);
		break;
	}
	// ---- the third list's special rooms (the generator's bSpecialRooms; AssignSpecialRooms chose them)
	case ERDRoomKind::Shrine: case ERDRoomKind::HealFountain: case ERDRoomKind::SpeedFountain: case ERDRoomKind::ManaFountain:
	{
		// (the statue or the fountain in a quadrant, off the lanes, facing the room's middle; candles, braziers, a carpet)
		const bool bShrine = Rm.Kind == ERDRoomKind::Shrine;
		const FName Main = bShrine ? TEXT("ShrineStatue") : TEXT("Fountain");
		TArray<FVector> Spots = Quads;
		Spots.Sort([&Ctr](const FVector& A, const FVector& Bq) { return FVector::DistSquared(A, Ctr) < FVector::DistSquared(Bq, Ctr); });
		for (const FVector& Q : Spots)
		{
			const float Yaw = ((Ctr - Q) * FVector(1, 1, 0)).Rotation().Yaw;
			// (a statue on a plinth when there is one, else standing on the floor as the fountain does)
			const FRDPiece* Pl = bShrine ? this->Pc(TEXT("ShrinePlinth")) : nullptr;
			if (Pl)
			{
				if (!Center(TEXT("ShrinePlinth"), Q, Yaw)) continue;
				AddPieceAt(Main, Q + FVector(0, 0, Pl->Size.Z), Yaw, 1.f, true);
			}
			else if (!Center(Main, Q, Yaw)) continue;
			const FRDPiece* Mp = this->Pc(Main);
			FFixture Fx; Fx.Kind = Rm.Kind; Fx.At = Q; Fx.Room = RI;
			Fixtures.Add(Fx);
			const FLinearColor Glow = bShrine ? FLinearColor(0.75f, 0.7f, 1.f) : Rm.Kind == ERDRoomKind::HealFountain ? FLinearColor(1.f, 0.35f, 0.3f)
				: Rm.Kind == ERDRoomKind::SpeedFountain ? FLinearColor(0.45f, 1.f, 0.4f) : FLinearColor(0.35f, 0.55f, 1.f);
			AddLight(Q + FVector(0, 0, FMath::Min((Mp ? Mp->Size.Z : 120.f) + 120.f, RH - 60.f)), Glow, 90.f, 900.f, false, 0.05f);
			break;
		}
		for (const FVector& Cn : { FVector(B.Min.X + 150, B.Min.Y + 150, 0), FVector(B.Max.X - 150, B.Max.Y - 150, 0) })
			if (LaneFree(Rm, Cn, 60.f)) Candles(Cn, 20.f);
		for (int32 Side = 0; Side < 4; ++Side)
			for (const FVector& W : WallSlots(Rm, Side, 600.f, 120.f, 300.f))
				AddPieceAt(TEXT("Banner"), W + FRotator(0, InwardYaw(Side), 0).RotateVector(FVector(12, 0, 0)) + FVector(0, 0, RH - 40.f), InwardYaw(Side), 1.f, true);
		break;
	}
	case ERDRoomKind::Arena:
	{
		// (the floor kept clear for the fight: braziers in the corners, weapons and shields on the walls, banners)
		for (const FVector& Cn : { FVector(B.Min.X + 150, B.Min.Y + 150, 0), FVector(B.Max.X - 150, B.Min.Y + 150, 0), FVector(B.Min.X + 150, B.Max.Y - 150, 0), FVector(B.Max.X - 150, B.Max.Y - 150, 0) })
		{
			if (!Center(TEXT("Brazier"), Cn, 0.f)) continue;
			const FRDPiece* Bz = this->Pc(TEXT("Brazier"));
			const float Hz = Bz ? Bz->Size.Z : 110.f;
			AddEffect(TEXT("BrazierFire"), Cn + FVector(0, 0, Hz + RDBrazierFlameUp), RDBrazierFlame);
			AddLight(Cn + FVector(0, 0, Hz + 40.f), FLinearColor(1.f, 0.5f, 0.2f), 200.f, 1800.f, true, 0.2f);
		}
		for (int32 Side = 0; Side < 4; ++Side)
		{
			const float Yaw = InwardYaw(Side);
			const FRotator Rt(0, Yaw, 0);
			int32 K = 0;
			for (const FVector& W : WallSlots(Rm, Side, 300.f, 120.f, 200.f))
			{
				AddPieceAt(TEXT("Shield"), W + Rt.RotateVector(FVector(14, 0, 0)) + FVector(0, 0, 250.f), Yaw, 1.f, true);
				AddPieceAt((K++ % 2) ? TEXT("Sword") : TEXT("Spear"), W + Rt.RotateVector(FVector(16, 0, 0)) + FVector(0, 0, 150.f), Yaw, 1.f, true);
			}
		}
		FFixture Fx; Fx.Kind = Rm.Kind; Fx.At = Ctr; Fx.Room = RI; Fixtures.Add(Fx);
		break;
	}
	case ERDRoomKind::TrapGauntlet:
	{
		// (bare stone, bones and debris along the walls; its chest at the far end from the first door: PlaceTraps lays the run
		// of traps on the lanes)
		FurnishWalls(R, Rm, { TEXT("BonePile"), TEXT("Debris"), TEXT("Bones") }, 300.f, 0.5f);
		int32 DoorSide = 0;
		for (int32 Side = 0; Side < 4; ++Side) if (Rm.bDoorSide[Side]) { DoorSide = Side; break; }
		const int32 Far = DoorSide ^ 1;
		const FVector Wall = Far == 0 ? FVector(B.Min.X, Lc.Y, 0) : Far == 1 ? FVector(B.Max.X, Lc.Y, 0) : Far == 2 ? FVector(Lc.X, B.Min.Y, 0) : FVector(Lc.X, B.Max.Y, 0);
		const float Yaw = InwardYaw(Far);
		// (beside the far wall's lane, out of its doorway)
		const FVector Side2 = (Far < 2 ? FVector(0, 1, 0) : FVector(1, 0, 0)) * (S * 1.f);
		const int32 Before = Containers.Num();
		if (!AddContainer(TEXT("Chest"), Wall + FRotator(0, Yaw, 0).RotateVector(FVector(60.f, 0, 0)) + Side2, Yaw, TEXT("chest")) || Containers.Num() == Before)
			AddContainer(TEXT("Chest"), Wall + FRotator(0, Yaw, 0).RotateVector(FVector(60.f, 0, 0)) - Side2, Yaw, TEXT("chest"));
		if (Containers.Num() > Before) SpecialChests.Add(ContainerKey(Before));
		FFixture Fx; Fx.Kind = Rm.Kind; Fx.At = Ctr; Fx.Room = RI; Fixtures.Add(Fx);
		break;
	}
	case ERDRoomKind::Vault:
	{
		// (chests and trunks along the walls, crystals on pedestals: its doors stay shut until her key opens them)
		const int32 Before = Containers.Num();
		FurnishWalls(R, Rm, { TEXT("Chest"), TEXT("Trunk"), TEXT("Chest") }, 220.f, 0.9f, true);
		for (int32 I = Before; I < Containers.Num(); ++I) SpecialChests.AddUnique(ContainerKey(I));
		for (const FVector& Q : Quads)
		{
			if (!Center(TEXT("Pedestal"), Q, 0.f)) continue;
			const FRDPiece* Pd = this->Pc(TEXT("Pedestal"));
			const float Hz = Pd ? Pd->Size.Z : 100.f;
			AddPieceAt(TEXT("Crystal"), Q + FVector(0, 0, Hz), R.FRandRange(0, 360), 1.f, true);
			AddLight(Q + FVector(0, 0, Hz + 80.f), FLinearColor(1.f, 0.82f, 0.4f), 60.f, 900.f, false, 0.05f);
		}
		FFixture Fx; Fx.Kind = Rm.Kind; Fx.At = Ctr; Fx.Room = RI; Fixtures.Add(Fx);
		break;
	}
	case ERDRoomKind::ThroneRoom:
	{
		// (the great hall's dais and throne on a wall without a door, a carpet up to it, columns, banners, braziers; the
		// usurper waits before the throne: PlaceSpecial)
		int32 Far = -1;
		for (int32 Side = 0; Side < 4 && Far < 0; ++Side) if (!Rm.bDoorSide[Side]) Far = Side;
		const bool bOnDoor = Far < 0;
		if (Far < 0) Far = 1;
		const float Yaw = InwardYaw(Far);
		const FRotator Rt(0, Yaw, 0);
		const FVector Wall = (Far == 0 ? FVector(B.Min.X, Lc.Y, 0) : Far == 1 ? FVector(B.Max.X, Lc.Y, 0) : Far == 2 ? FVector(Lc.X, B.Min.Y, 0) : FVector(Lc.X, B.Max.Y, 0))
			+ (bOnDoor ? (Far < 2 ? FVector(0, 1, 0) : FVector(1, 0, 0)) * 450.f : FVector::ZeroVector);
		const FVector Dais = Wall + Rt.RotateVector(FVector(220.f, 0, 0));
		const FRDPiece* D = this->Pc(TEXT("Dais"));
		if (Center(TEXT("Dais"), Dais, Yaw, true, true))
			AddPieceAt(this->Pc(TEXT("ThroneRoyal")) ? TEXT("ThroneRoyal") : TEXT("Throne"), Dais + FVector(0, 0, D ? D->Size.Z : 0), Yaw, 1.f, false);
		AddPieceAt(TEXT("CarpetLong"), (Dais + Ctr) * 0.5f + FVector(0, 0, 1), Yaw + 90.f, 1.f, true);
		for (int32 Sd = -1; Sd <= 1; Sd += 2)
		{
			const FVector Bz = Dais + Rt.RotateVector(FVector(60.f, Sd * 260.f, 0));
			if (Center(TEXT("Brazier"), Bz, 0.f))
			{
				const FRDPiece* Bp = this->Pc(TEXT("Brazier"));
				const float Hz = Bp ? Bp->Size.Z : 110.f;
				AddEffect(TEXT("BrazierFire"), Bz + FVector(0, 0, Hz + RDBrazierFlameUp), RDBrazierFlame);
				AddLight(Bz + FVector(0, 0, Hz + 40.f), FLinearColor(1.f, 0.5f, 0.2f), 200.f, 1600.f, true, 0.2f);
			}
		}
		for (int32 Side = 0; Side < 4; ++Side)
			for (const FVector& W : WallSlots(Rm, Side, 450.f, 120.f, 300.f))
				AddPieceAt(TEXT("Banner"), W + FRotator(0, InwardYaw(Side), 0).RotateVector(FVector(12, 0, 0)) + FVector(0, 0, RH - 40.f), InwardYaw(Side), 1.f, true);
		for (const FVector& Q : Quads) if (LaneFree(Rm, Q, 80.f)) Center(TEXT("Column"), Q, 0.f);
		FFixture Fx; Fx.Kind = Rm.Kind; Fx.At = Dais + Rt.RotateVector(FVector(180.f, 0, 0)); Fx.Room = RI; Fixtures.Add(Fx);
		break;
	}
	default: break;
	}
	// decoration everywhere: some floor clutter near the walls (no collision)
	if (Rm.Kind != ERDRoomKind::Junction && Rm.Kind != ERDRoomKind::Hall && Rm.Kind != ERDRoomKind::Chapel)
		for (int32 K = 0; K < 2; ++K)
		{
			const FVector P(R.FRandRange(B.Min.X + 80, B.Max.X - 80), R.FRandRange(B.Min.Y + 80, B.Max.Y - 80), 0);
			if (LaneFree(Rm, P, 40.f)) AddPieceAt(TEXT("Debris"), P, R.FRandRange(0, 360), 1.f, true);
		}
	LightRoom(R, Rm, RI);
}

void ARDSection::DecorateCorridor(FRandomStream& R, int32 CI)
{
	const FCorr& C = Corrs[CI];
	const int32 Len = C.bHoriz ? C.Max.X - C.Min.X : C.Max.Y - C.Min.Y;
	const float S = Generator->TileSize;
	// torches every 3 tiles alternating sides; theme 0 = well lit passage, 1 = dim (some sconces dark), 2 = old tunnel (candles)
	const float Cd = C.Theme == 0 ? 75.f : C.Theme == 1 ? 45.f : 0.f;
	for (int32 K = 1; K < Len; K += 3)
	{
		const FIntPoint T = C.bHoriz ? FIntPoint(C.Min.X + K, C.Min.Y) : FIntPoint(C.Min.X, C.Min.Y + K);
		if (!In(T) || Type[Idx(T)] != 2) continue;
		const int32 Side = C.bHoriz ? ((K / 3) % 2 ? 2 : 3) : ((K / 3) % 2 ? 0 : 1);
		const FIntPoint Nb = T + Dir4[Side];
		if (In(Nb) && Type[Idx(Nb)] != 0) continue;
		const FVector Wall = TileWorld(T) + FVector(Dir4[Side].X, Dir4[Side].Y, 0) * (S * 0.5f);
		if (C.Theme == 2)
		{
			const FVector P = Wall + FRotator(0, InwardYaw(Side), 0).RotateVector(FVector(40, 0, 0));
			AddPieceAt(TEXT("Candles"), P, R.FRandRange(0, 360), 1.f, true);
			AddEffect(TEXT("CandleFire"), P + FVector(0, 0, 18), 1.f);
			AddLight(P + FVector(0, 0, 50), FLinearColor(1.f, 0.6f, 0.3f), 10.f, 650.f, false, 0.15f);
		}
		else AddTorch(Wall + FVector(0, 0, 230.f), InwardYaw(Side), Cd * R.FRandRange(0.7f, 1.2f), C.Theme == 0 || R.FRand() < 0.6f);
	}
	// what the passage is for: 0 guard passage (benches, shields), 1 supply passage (barrels and crates stacked along a
	// wall, all openable), 2 catacomb tunnel (bones, shackles, chains); clutter hugs the walls and leaves the way clear
	for (int32 K = 1; K < Len - 1; ++K)
	{
		const FIntPoint T = C.bHoriz ? FIntPoint(C.Min.X + K, C.Min.Y) : FIntPoint(C.Min.X, C.Min.Y + K);
		if (!In(T) || Type[Idx(T)] != 2) continue;
		const float U = R.FRand();
		const int32 Side = C.bHoriz ? (R.RandBool() ? 2 : 3) : (R.RandBool() ? 0 : 1);
		const FIntPoint Nb = T + Dir4[Side];
		if (In(Nb) && Type[Idx(Nb)] != 0) continue;
		const FVector Wall = TileWorld(T) + FVector(Dir4[Side].X, Dir4[Side].Y, 0) * (S * 0.5f);
		const float Yaw = InwardYaw(Side);
		const FRotator Rt(0, Yaw, 0);
		auto Against = [&](FName Nm, float Along)
		{
			const FRDPiece* P = this->Pc(Nm);
			if (!P) return;
			const FVector Pos = Wall + Rt.RotateVector(FVector(P->Size.X * 0.5f + 32.f, Along, 0));
			if (P->Moving) AddContainer(Nm, Pos, Yaw, Nm.ToString().ToLower());
			else AddPieceAt(Nm, Pos, Yaw);
		};
		if (C.Theme == 0)
		{
			if (U < 0.10f) Against(TEXT("Bench"), 0.f);
			else if (U < 0.22f) AddPieceAt(TEXT("Shield"), Wall + FVector(0, 0, 230.f), Yaw, 1.f, true);
			else if (U < 0.28f) AddPieceAt(TEXT("Debris"), Wall + Rt.RotateVector(FVector(50, 0, 0)), R.FRandRange(0, 360), 1.f, true);
		}
		else if (C.Theme == 1)
		{
			if (U < 0.22f) { Against(R.RandBool() ? TEXT("Barrel") : TEXT("Barrel2"), -60.f); if (R.RandBool()) Against(R.RandBool() ? TEXT("Crate") : TEXT("Crate2"), 60.f); }
			else if (U < 0.3f) AddPieceAt(TEXT("Debris"), Wall + Rt.RotateVector(FVector(50, 0, 0)), R.FRandRange(0, 360), 1.f, true);
		}
		else
		{
			if (U < 0.12f) AddPieceAt(TEXT("BonePile2"), Wall + Rt.RotateVector(FVector(45, 0, 0)), R.FRandRange(0, 360), 1.f, true);
			else if (U < 0.22f) AddPieceAt(TEXT("Shackles"), Wall + FVector(0, 0, 150), Yaw, 1.f, true);
			else if (U < 0.3f) { const FRDPiece* Ch = this->Pc(TEXT("Chain")); if (Ch) AddPieceAt(TEXT("Chain"), TileWorld(T) + Rt.RotateVector(FVector(-90, 0, 0)) + FVector(0, 0, Generator->CorridorHeight - Ch->Size.Z), R.FRandRange(0, 360), 1.f, true); }
			else if (U < 0.38f) AddPieceAt(TEXT("Debris"), Wall + Rt.RotateVector(FVector(50, 0, 0)), R.FRandRange(0, 360), 1.f, true);
		}
	}
}

// ------------------------------------------------------------------------------------------------ build / play
void ARDSection::ClearInteractive()
{
	TArray<UActorComponent*> Comps;
	GetComponents(Comps);
	for (UActorComponent* C : Comps) if (C && C->ComponentHasTag(RDInteractiveTag)) C->DestroyComponent();
	Doors.Reset(); Containers.Reset();
}

void ARDSection::AddDoors()
{
	// one double door per doorway (same room / side order as the plan)
	for (int32 RI = 0; RI < Rooms.Num(); ++RI)
	{
		const FRoom& Rm = Rooms[RI];
		if (Rm.Kind == ERDRoomKind::Junction) continue;
		for (int32 Side = 0; Side < 4; ++Side)
		{
			if (!Rm.bDoorSide[Side]) continue;
			const FIntPoint In_ = Side == 0 ? FIntPoint(Rm.Min.X, Rm.Lane.Y) : Side == 1 ? FIntPoint(Rm.Max.X - 1, Rm.Lane.Y) : Side == 2 ? FIntPoint(Rm.Lane.X, Rm.Min.Y) : FIntPoint(Rm.Lane.X, Rm.Max.Y - 1);
			const FIntPoint Out = In_ + Dir4[Side];
			if (DoorEdges.Contains(EdgeKey(In_, Out))) AddDoor(In_, Out, RI);
		}
	}
	// door edge -> first leaf index (two leaves per doorway)
	TMap<int64, int32> Remap;
	for (int32 I = 0; I < Doors.Num(); ++I) if (Doors[I].TileA.X >= 0 && !Remap.Contains(EdgeKey(Doors[I].TileA, Doors[I].TileB))) Remap.Add(EdgeKey(Doors[I].TileA, Doors[I].TileB), I);
	if (Doors.Num() > 0) DoorEdges = Remap;
}

void ARDSection::BeginGenerate(ARDDungeonGenerator* InGenerator, FIntPoint InCoord, int32 InSeed, bool bEditorBuild)
{
	GenStart = FPlatformTime::Seconds();
	Generator = InGenerator; Coord = InCoord; Seed = InSeed; bEditorBuilt = bEditorBuild;
	bBuildStatic = true; bBuildInteractive = true;
	NumInstances = 0; NumLights = 0; NextRoom = 0; NextCorr = 0; GenTicks = 0; FurnishMs = 0.0; AnvilPoints.Reset(); AnvilRoom = -1;
	Theme = Generator->ThemeOf(Coord);
	ThemeNames.Reset(); ThemeNamesOf = Theme;
	GenR.Initialize(Seed);
	Plan(GenR);
	ShellPrepare(GenR);
	ShellX = 0;
	AddDoors();
	UWorld* W = GetWorld();
	if (W && W->IsGameWorld()) RegisterMap();
	ShellMs = (FPlatformTime::Seconds() - GenStart) * 1000.0;
	bBuilding = true;
}

bool ARDSection::ContinueGenerate(double Budget)
{
	if (!bBuilding) return true;
	const double T0 = FPlatformTime::Seconds();
	++GenTicks;
	// the shell first (floors, ceilings, walls), a few tile columns per frame, each frame's instances added at once
	if (ShellX <= N)
	{
		while (FPlatformTime::Seconds() - T0 < Budget && ShellX <= N)
		{
			if (ShellX < N) ShellColumn(GenR, ShellX);
			else ShellCorners();
			++ShellX;
		}
		FlushInstances();
		ShellMs += (FPlatformTime::Seconds() - T0) * 1000.0;
		return false;
	}
	while (FPlatformTime::Seconds() - T0 < Budget)
	{
		if (NextRoom < Rooms.Num()) { Furnish(GenR, NextRoom++); continue; }
		if (NextCorr < Corrs.Num()) { bNoBlock = true; DecorateCorridor(GenR, NextCorr++); bNoBlock = false; continue; }
		break;
	}
	FurnishMs += (FPlatformTime::Seconds() - T0) * 1000.0;
	if (NextRoom < Rooms.Num() || NextCorr < Corrs.Num()) return false;
	EnsureAnvil();
	// the instanced furniture goes in at once (one rebuild per mesh instead of one per frame)
	const double T1 = FPlatformTime::Seconds();
	FlushInstances();
	FurnishMs += (FPlatformTime::Seconds() - T1) * 1000.0;
	bBuilding = false;
	UWorld* W = GetWorld();
	if (W && W->IsGameWorld())
	{
		FRandomStream RM(Seed ^ 0x5f3759df);
		SpawnMonsters(RM);
		PlaceTraps(); PlaceCellOccupants(); PlacePad(); PlaceSpecial();          // (mistward; PlaceSpecial: the third list's rooms)
		CollectFlicker();
		RegisterMap();          // (again: the containers and lights are there now)
		Generator->RecordSection(this);
		UpdateSeals();
	}
	GenerateMs = ShellMs + FurnishMs;
	UE_LOG(LogRandomDungeon, Log, TEXT("RDSECTION (%d,%d) seed %d: %d rooms, %d hallways, %d doors, %d containers, %d instances, %d lights, %d monsters, shell %.0f ms + furnish %.0f ms over %d frames (%.1f s)%s"),
		Coord.X, Coord.Y, Seed, Rooms.Num(), Corrs.Num(), Doors.Num(), Containers.Num(), NumInstances, NumLights, SpawnedMonsters.Num(), ShellMs, FurnishMs, GenTicks,
		FPlatformTime::Seconds() - GenStart, bEditorBuilt ? TEXT(" [editor]") : TEXT(""));
	return true;
}

void ARDSection::Generate(ARDDungeonGenerator* InGenerator, FIntPoint InCoord, int32 InSeed, bool bEditorBuild)
{
	BeginGenerate(InGenerator, InCoord, InSeed, bEditorBuild);
	while (!ContinueGenerate(1e9)) {}
}

bool ARDSection::Census(ARDDungeonGenerator* InGenerator, FIntPoint InCoord, int32 InSeed, int32& OutRooms, int32& OutChests, int32& OutMonsters)
{
	OutRooms = OutChests = OutMonsters = 0;
	if (!InGenerator) return false;
	// (a section of nobody's world: planned and furnished in a count-only mode, nothing built, nothing spawned)
	ARDSection* S = NewObject<ARDSection>(GetTransientPackage());
	S->Generator = InGenerator; S->Coord = InCoord; S->Seed = InSeed; S->bEditorBuilt = false;
	S->bCensus = true; S->bBuildStatic = false; S->bBuildInteractive = false; S->CensusChests = 0;
	const FIntPoint T0 = InGenerator->SectionMinTile(InCoord);
	if (USceneComponent* Rt = S->GetRootComponent()) Rt->SetRelativeLocation(FVector(T0.X * InGenerator->TileSize, T0.Y * InGenerator->TileSize, 0.f));
	S->Theme = InGenerator->ThemeOf(InCoord);
	FRandomStream R(InSeed);
	S->Plan(R);
	S->BuildShellCensus(R);
	for (int32 RI = 0; RI < S->Rooms.Num(); ++RI) S->Furnish(R, RI);
	S->bNoBlock = true;
	for (int32 CI = 0; CI < S->Corrs.Num(); ++CI) S->DecorateCorridor(R, CI);
	S->bNoBlock = false;
	S->EnsureAnvil();
	for (const FRoom& Rm : S->Rooms) if (Rm.Kind != ERDRoomKind::Junction) ++OutRooms;
	OutChests = S->CensusChests;
	FRandomStream RM(InSeed ^ 0x5f3759df);
	S->SpawnMonsters(RM);
	OutMonsters = S->MonstersPlanned;
	S->MarkAsGarbage();
	return true;
}

void ARDSection::BuildShellCensus(FRandomStream& R)
{
	// (the shell draws from the stream too: the same draws as BuildShell, nothing placed)
	ShellPrepare(R);
	for (int32 X = 0; X < N; ++X) ShellColumn(R, X);
}

void ARDSection::ActivateForPlay()
{
	if (!Generator) return;
	// same plan as the editor build (same seed); only the interactive part is instantiated
	bBuildStatic = false; bBuildInteractive = true;
	ClearInteractive();
	FirePoints.Reset(); AnvilPoints.Reset(); AnvilRoom = -1;
	Theme = Generator->ThemeOf(Coord);
	ThemeNames.Reset(); ThemeNamesOf = Theme;
	const int32 Inst = NumInstances, Lights = NumLights;
	FRandomStream R(Seed);
	Plan(R);
	BuildShell(R);
	AddDoors();
	for (int32 RI = 0; RI < Rooms.Num(); ++RI) Furnish(R, RI);
	bNoBlock = true;
	for (int32 CI = 0; CI < Corrs.Num(); ++CI) DecorateCorridor(R, CI);
	bNoBlock = false;
	EnsureAnvil();
	NumInstances = Inst; NumLights = Lights;
	bBuildStatic = true;
	// (mistward: the monsters it had go first: RestartPlay activates the kept start set again, and every planned monster
	// stood there twice after one restart (28 of 14), three times after two; the tests' counts and the reels saw them)
	if (Generator->bTidyFurniture)
	{
		for (ARDMonster* M : SpawnedMonsters) if (IsValid(M)) M->Destroy();
		SpawnedMonsters.Reset();
	}
	FRandomStream RM(Seed ^ 0x5f3759df);
	SpawnMonsters(RM);
	PlaceTraps(); PlaceCellOccupants(); PlacePad(); PlaceSpecial();          // (mistward; PlaceSpecial: the third list's rooms)
	RegisterMap();
	CollectFlicker();
	Generator->RecordSection(this);
	UpdateSeals();
	UE_LOG(LogRandomDungeon, Log, TEXT("RDSECTION (%d,%d) activated for play: %d rooms, %d doors, %d containers, %d monsters"), Coord.X, Coord.Y, Rooms.Num(), Doors.Num(), Containers.Num(), SpawnedMonsters.Num());
}

void ARDSection::SpawnMonsters(FRandomStream& R)
{
	UWorld* W = GetWorld();
	if ((!bCensus && (!W || !W->IsGameWorld())) || Generator->Monsters.Num() == 0) return;
	// (level 5: the kinds of this section's tier of rooms)
	TArray<int32> Kinds; Generator->MonsterKindsFor(Coord, Kinds);
	float WSum = 0.f; for (const int32 K : Kinds) WSum += Generator->Monsters[K].Weight;
	if (WSum <= 0.f || Kinds.Num() == 0) return;
	const FVector Start = Generator->GetStartRoomCenter();
	// which rooms get a monster: a coin for each room, or (the combat dungeon) exactly the wanted share of the rooms,
	// taken in a shuffled order (a room without a free tile or next to the player's start is passed over for the next)
	TArray<int32> Order; int32 Want = MAX_int32;
	for (int32 RI = 0; RI < Rooms.Num(); ++RI) if (Rooms[RI].Kind != ERDRoomKind::Junction) Order.Add(RI);
	if (Generator->bCombat)
	{
		Want = FMath::RoundToInt(Order.Num() * Generator->MonsterCoverage);
		for (int32 I = Order.Num() - 1; I > 0; --I) Order.Swap(I, R.RandRange(0, I));
	}
	// (each one's place in this order is its SpawnIndex: one she killed is drawn as before and skipped, so a section
	// generated again has the others where they were and the dead stay dead)
	int32 Count = 0;
	for (const int32 RI : Order)
	{
		if (Count >= Want) break;
		const FRoom& Rm = Rooms[RI];
		if (!Generator->bCombat && R.FRand() >= Generator->MonsterCoverage) continue;
		// a free tile of the room (not where the player starts)
		TArray<FIntPoint> Free;
		for (int32 X = Rm.Min.X; X < Rm.Max.X; ++X) for (int32 Y = Rm.Min.Y; Y < Rm.Max.Y; ++Y) if (IsWalkable(FIntPoint(X, Y))) Free.Add(FIntPoint(X, Y));
		if (Free.Num() == 0) continue;
		const FIntPoint T = Free[R.RandRange(0, Free.Num() - 1)];
		const FVector P = TileWorld(T);
		if (FVector::Dist2D(P, Start) < 1500.f) continue;
		float U = R.FRand() * WSum; const FRDMonsterDef* Def = nullptr;
		for (const int32 K : Kinds) { U -= Generator->Monsters[K].Weight; if (U <= 0.f) { Def = &Generator->Monsters[K]; break; } }
		if (!Def) Def = &Generator->Monsters[Kinds.Last()];
		const int32 Index = Count++;
		const float Yaw = R.FRandRange(0, 360);
		const int32 MSeed = R.RandHelper(1 << 30);
		if (bCensus) continue;             // (mistward: only counted)
		FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
		if (Generator->IsMonsterKilled(Coord, Index))
		{
			// (level 5: the dead stay: its corpse where it lay)
			const FTransform* Xf = Generator->bKeepCorpses ? Generator->CorpseOf(Coord, Index) : nullptr;
			if (!Xf) continue;
			ARDMonster* C = W->SpawnActor<ARDMonster>(ARDMonster::StaticClass(), *Xf, Sp);
			if (!C) continue;
			C->SpawnIndex = Index;
			C->Setup(this, *Def, MSeed);
			C->LayDead();
			SpawnedMonsters.Add(C);
			continue;
		}
		ARDMonster* M = W->SpawnActor<ARDMonster>(ARDMonster::StaticClass(), FTransform(FRotator(0, Yaw, 0), P + FVector(0, 0, Def->CapsuleHalfHeight + 5.f)), Sp);
		if (!M) continue;
		M->SpawnIndex = Index;
		M->Setup(this, *Def, MSeed);
		SpawnedMonsters.Add(M);
	}
	MonstersPlanned = Count;
}

FRDSectionMap ARDSection::BuildMapData() const
{
	FRDSectionMap M; M.Coord = Coord; M.bStart = Generator && Generator->IsStartSection(Coord);
	const FIntPoint G0 = Generator ? Generator->SectionMinTile(Coord) : FIntPoint::ZeroValue;
	for (int32 RI = 0; RI < Rooms.Num(); ++RI)
	{
		const FRoom& Rm = Rooms[RI];
		FRDMapRect Rc; Rc.Min = G0 + Rm.Min; Rc.Max = G0 + Rm.Max; Rc.Kind = Rm.Kind; Rc.bCorridor = Rm.Kind == ERDRoomKind::Junction;
		// (mistward: a shaped room's tiles)
		if (Rm.Shape != 0)
		{
			Rc.Shape = GetRoomShape(RI);
			for (int32 Y = Rm.Min.Y; Y < Rm.Max.Y; ++Y)
				for (int32 X = Rm.Min.X; X < Rm.Max.X; ++X) Rc.Mask.Add(Owner[Idx(FIntPoint(X, Y))] == RI ? 1 : 0);
		}
		M.Rects.Add(Rc);
	}
	for (const FCorr& C : Corrs)
	{
		FRDMapRect Rc; Rc.Min = G0 + C.Min; Rc.Max = G0 + C.Max; Rc.bCorridor = true;
		M.Rects.Add(Rc);
	}
	for (int32 I = 0; I < Doors.Num(); I += 1)
		if (Doors[I].TileA.X >= 0 && (Doors[I].Partner < 0 || Doors[I].Partner > I)) M.Doors.Add(FVector2D(Doors[I].Center.X, Doors[I].Center.Y));
	for (int32 I = 0; I < Containers.Num(); ++I)
		if (Containers[I].Partner < 0 || Containers[I].Partner > I) M.Chests.Add(FVector2D(Containers[I].Center.X, Containers[I].Center.Y));
	TArray<UPointLightComponent*> Ls; GetComponents(Ls);
	for (const UPointLightComponent* L : Ls) if (L->ComponentHasTag(RDFlickerTag)) M.Torches.Add(FVector2D(L->GetComponentLocation().X, L->GetComponentLocation().Y));
	return M;
}

void ARDSection::RegisterMap()
{
	if (!Generator) return;
	FRDSectionMap M = BuildMapData();
	if (const FRDSectionMap* Old = Generator->MapData.Find(Coord))
	{
		// regenerated after an unload: keep what was discovered
		for (int32 I = 0; I < M.Rects.Num() && I < Old->Rects.Num(); ++I) M.Rects[I].bDiscovered = Old->Rects[I].bDiscovered;
		M.GeneratedTime = Old->GeneratedTime;
	}
	Generator->MapData.Add(Coord, M);
}

void ARDSection::CollectFlicker()
{
	// flicker: lights tagged at build time (saved ones too)
	Flickers.Reset();
	TArray<UPointLightComponent*> Ls; GetComponents(Ls);
	FRandomStream R(Seed + 99);
	for (UPointLightComponent* L : Ls)
	{
		if (!L->ComponentHasTag(RDFlickerTag)) continue;
		float Amt = 0.15f;
		for (const FName& Tg : L->ComponentTags) if (Tg.ToString().StartsWith(TEXT("F"))) { const FString V = Tg.ToString().Mid(1); if (V.IsNumeric()) Amt = FCString::Atof(*V); }
		Flickers.Add({ L, (float)L->Intensity, (float)R.FRandRange(0.f, 100.f), Amt });
	}
}

void ARDSection::BeginPlay()
{
	Super::BeginPlay();
}

void ARDSection::Destroyed()
{
	for (ARDMonster* M : SpawnedMonsters) if (M) M->Destroy();
	SpawnedMonsters.Reset();
	for (AActor* A : OtherActors) if (A) A->Destroy();
	OtherActors.Reset();
	for (AActor* A : MistActors) if (A) A->Destroy();
	MistActors.Reset();
	Super::Destroyed();
}

// ------------------------------------------------------------------------------------------------ interaction
float ARDSection::FindNearestInteractive(const FVector& From, float MaxDistance, bool& bDoor, int32& Index) const
{
	Index = -1; float Best = MaxDistance; bDoor = false;
	for (int32 I = 0; I < Doors.Num(); ++I)
	{
		const FVector D = Doors[I].Center - From;
		const float H = FVector2D(D.X, D.Y).Size();
		if (H < Best && FMath::Abs(D.Z) < 200.f) { Best = H; Index = I; bDoor = true; }
	}
	for (int32 I = 0; I < Containers.Num(); ++I)
	{
		// (mistward: an open container stays open: there is nothing more to do with it)
		if (Generator && Generator->bContainersStayOpen && Containers[I].Target > 0.5f) continue;
		const FVector D = Containers[I].Center - From;
		const float H = FVector2D(D.X, D.Y).Size() + 20.f;     // a door at the same distance wins
		if (H < Best && FMath::Abs(D.Z) < 200.f) { Best = H; Index = I; bDoor = false; }
	}
	return Index >= 0 ? Best : 1e9f;
}

void ARDSection::ToggleDoor(int32 I, const FVector& Opener, bool bByMonster)
{
	if (!Doors.IsValidIndex(I)) return;
	auto Set = [&](FMover& M, float Target)
	{
		if (Target > 0.5f && M.Target < 0.5f)
		{
			// swing away from whoever opens it: +yaw swings a +Y leaf toward -X (against the leaf normal)
			const FVector D = Opener - M.Center;
			const float Side = FVector::DotProduct(D, M.Normal) >= 0.f ? 1.f : -1.f;
			M.OpenAngle = 95.f * Side * M.LeafSign;
		}
		M.Target = Target; M.bByMonster = bByMonster && Target > 0.5f; M.MonsterCloseTimer = 0.f;
	};
	FMover& M = Doors[I];
	const float Target = M.Target > 0.5f ? 0.f : 1.f;
	// (the third list: a vault she has no key for, an arena while it is fought: its doors do not open, for her or a monster)
	if (Target > 0.5f && Generator && Generator->bSpecialRooms)
	{
		const int32 Rm = DoorRoom(I);
		if (Rm >= 0 && Generator->IsRoomLocked(Coord, Rm)) return;
	}
	Set(M, Target);
	if (Doors.IsValidIndex(M.Partner)) Set(Doors[M.Partner], Target);
	if (Generator) Generator->PlaySoundAt(Target > 0.5f ? (M.bCell ? TEXT("Env.CellOpen") : TEXT("Env.DoorOpen")) : (M.bCell ? TEXT("Env.CellClose") : TEXT("Env.DoorClose")), M.Center);
}

bool ARDSection::IsDoorOpenIndex(int32 I) const { return Doors.IsValidIndex(I) && Doors[I].Alpha > 0.8f && Doors[I].Target > 0.5f; }

bool ARDSection::IsTargetOpen(bool bDoor, int32 I) const
{
	const TArray<FMover>& A = bDoor ? Doors : Containers;
	return A.IsValidIndex(I) && A[I].Target > 0.5f;
}

void ARDSection::ToggleContainer(int32 I)
{
	if (!Containers.IsValidIndex(I)) return;
	FMover& M = Containers[I];
	if (Generator && Generator->bContainersStayOpen && M.Target > 0.5f) return;        // (mistward: it stays open)
	M.Target = M.Target > 0.5f ? 0.f : 1.f;
	if (Containers.IsValidIndex(M.Partner)) Containers[M.Partner].Target = M.Target;
	if (Generator) Generator->PlaySoundAt(M.Target > 0.5f ? TEXT("Env.ChestOpen") : TEXT("Env.ChestClose"), M.Center);
	// (what it holds is found the first time it is opened, and never again: the generator keeps which were looted, also
	// over a section dropped and generated again; a wardrobe's two doors are one container)
	const bool bFirst = M.Target > 0.5f && !IsContainerLooted(I);
	if (bFirst)
	{
		M.bLooted = true;
		const int32 Key = ContainerKey(I);
		if (Generator) { Generator->MarkContainerLooted(Coord, Key); Generator->OnContainerOpened(this, Key, M.Center); }
	}
}

int32 ARDSection::ContainerKey(int32 I) const
{
	return Containers.IsValidIndex(I) && Containers.IsValidIndex(Containers[I].Partner) ? FMath::Min(I, Containers[I].Partner) : I;
}

bool ARDSection::IsContainerLooted(int32 I) const
{
	if (!Containers.IsValidIndex(I)) return false;
	const FMover& M = Containers[I];
	if (M.bLooted || (Containers.IsValidIndex(M.Partner) && Containers[M.Partner].bLooted)) return true;
	return Generator && Generator->IsContainerLooted(Coord, ContainerKey(I));
}

FVector ARDSection::GetDoorLocation(int32 I) const { return Doors.IsValidIndex(I) ? Doors[I].Center : FVector::ZeroVector; }
float ARDSection::GetDoorOpenAlpha(int32 I) const { return Doors.IsValidIndex(I) ? Doors[I].Alpha : -1.f; }
bool ARDSection::IsDoorCell(int32 I) const { return Doors.IsValidIndex(I) && Doors[I].bCell; }
FVector ARDSection::GetContainerLocation(int32 I) const { return Containers.IsValidIndex(I) ? Containers[I].Center : FVector::ZeroVector; }
float ARDSection::GetContainerOpenAlpha(int32 I) const { return Containers.IsValidIndex(I) ? Containers[I].Alpha : -1.f; }
FString ARDSection::GetContainerKind(int32 I) const { return Containers.IsValidIndex(I) ? Containers[I].Kind : FString(); }
FString ARDSection::GetRoomKind(int32 I) const { return Rooms.IsValidIndex(I) ? ARDDungeonGenerator::KindName(Rooms[I].Kind) : FString(); }
FVector ARDSection::GetRoomCenter(int32 I) const
{
	if (!Rooms.IsValidIndex(I)) return FVector::ZeroVector;
	const FBox2D B = RoomBox(Rooms[I]);
	return FVector(B.GetCenter(), 0.f);
}
void ARDSection::GetRoomBounds(int32 I, FVector2D& Min, FVector2D& Max) const
{
	if (!Rooms.IsValidIndex(I)) { Min = Max = FVector2D::ZeroVector; return; }
	const FBox2D B = RoomBox(Rooms[I]); Min = B.Min; Max = B.Max;
}

TArray<FVector> ARDSection::GetRoomFreeTiles(int32 I) const
{
	TArray<FVector> Out;
	if (!Rooms.IsValidIndex(I)) return Out;
	const FRoom& Rm = Rooms[I];
	for (int32 X = Rm.Min.X; X < Rm.Max.X; ++X) for (int32 Y = Rm.Min.Y; Y < Rm.Max.Y; ++Y) if (IsWalkable(FIntPoint(X, Y))) Out.Add(TileWorld(FIntPoint(X, Y)));
	return Out;
}

TArray<FVector> ARDSection::GetPortalPoints() const
{
	TArray<FVector> Out;
	for (const FIntPoint& P : Portals) Out.Add(TileWorld(P));
	return Out;
}

FIntPoint ARDSection::PortalNeighbour(int32 Portal, FVector& Border, FVector& Outward) const
{
	const FIntPoint P = Portals.IsValidIndex(Portal) ? Portals[Portal] : FIntPoint::ZeroValue;
	// (a hallway end lies on the first or last row or column of tiles: it leaves the section that way)
	FIntPoint D(0, 0);
	if (P.X == 0) D.X = -1; else if (P.X == N - 1) D.X = 1; else if (P.Y == 0) D.Y = -1; else D.Y = 1;
	Outward = FVector(D.X, D.Y, 0.f);
	const float TS = Generator ? Generator->TileSize : 300.f;
	Border = TileWorld(P) + Outward * (TS * 0.5f);
	return Coord + D;
}

TArray<int32> ARDSection::GetChestKeys() const
{
	TArray<int32> Out;
	for (int32 I = 0; I < Containers.Num(); ++I)
		if (Containers[I].Kind == TEXT("chest") || Containers[I].Kind == TEXT("trunk")) Out.AddUnique(ContainerKey(I));
	return Out;
}

int32 ARDSection::GetNumSeals(int32 Kind) const
{
	int32 Num = 0;
	for (const int32 K : SealKinds) if (Kind == 0 || K == Kind) ++Num;
	return Num;
}

void ARDSection::UpdateSeals()
{
	for (USceneComponent* C : SealComps) if (C) C->DestroyComponent();
	SealComps.Reset(); SealAt.Reset(); SealKinds.Reset();
	UWorld* W = GetWorld();
	if (!Generator || Generator->MaxTier <= 0 || !W || !W->IsGameWorld()) return;
	const float TS = Generator->TileSize, Hh = Generator->CorridorHeight;
	for (int32 I = 0; I < Portals.Num(); ++I)
	{
		FVector Border, Out;
		const FIntPoint Next = PortalNeighbour(I, Border, Out);
		const int32 Kind = Generator->GetSealKind(Coord, Next);
		if (Kind == 0) continue;
		// the piece's front (+X) faces back into this section; it stands just inside the border, across the hallway
		const FRotator Yaw = (-Out).Rotation();
		const FVector Across = FVector::CrossProduct(FVector::UpVector, Out);
		auto Place = [&](FName Piece, const FVector& At)
		{
			const FRDPiece* P = this->Pc(Piece);
			if (!P || !P->Mesh) return;
			UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
			C->SetMobility(EComponentMobility::Movable);
			C->SetStaticMesh(P->Mesh);
			C->SetupAttachment(RootComponent);
			C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			C->RegisterComponent();
			C->SetWorldTransform(P->Adjust * FTransform(Yaw, At));
			SealComps.Add(C);
		};
		if (Kind == 2)
		{
			const FRDPiece* P = this->Pc(Generator->EndPiece);
			Place(Generator->EndPiece, Border - Out * ((P ? P->Size.X : 60.f) * 0.5f + 2.f));
		}
		else
		{
			// (the end wall at the border, the grating in front of it: the tier beyond is not generated, and through the bars
			// the void showed as flat sky; a wall past the border, out from under the hallway's ceiling, glowed in the sky
			// light. Both go when the tier opens)
			const FRDPiece* E = this->Pc(Generator->EndPiece);
			const float Back = E && E->Mesh ? E->Size.X + 6.f : 0.f;
			if (Back > 0.f) Place(Generator->EndPiece, Border - Out * (E->Size.X * 0.5f + 2.f));
			// (the grating is a half-width piece: two of them across the hallway)
			const FRDPiece* P = this->Pc(Generator->SealPiece);
			const float Half = P ? P->Size.Y * 0.5f : TS * 0.25f, Dp = Back + (P ? P->Size.X : 40.f) * 0.5f + 2.f;
			Place(Generator->SealPiece, Border - Out * Dp + Across * Half);
			Place(Generator->SealPiece, Border - Out * Dp - Across * Half);
		}
		// the blocker: the hallway's full width and height (nobody climbs over it), at the grating or the wall
		const FRDPiece* Ep = Kind == 1 ? this->Pc(Generator->EndPiece) : nullptr;
		const float Front = (Ep && Ep->Mesh) ? Ep->Size.X + 6.f : 0.f;
		UBoxComponent* B = NewObject<UBoxComponent>(this);
		B->SetMobility(EComponentMobility::Movable);
		B->SetupAttachment(RootComponent);
		B->SetBoxExtent(FVector(20.f, TS * 0.5f, Hh * 0.5f));
		B->SetCollisionProfileName(UCollisionProfile::BlockAll_ProfileName);
		B->SetHiddenInGame(true);
		B->RegisterComponent();
		B->SetWorldLocationAndRotation(Border - Out * (22.f + Front) + FVector(0, 0, Hh * 0.5f), Yaw);
		SealComps.Add(B);
		SealAt.Add(Border); SealKinds.Add(Kind);
	}
}

// ------------------------------------------------------------------------------------------------ pathing
bool ARDSection::FindPath(FIntPoint From, FIntPoint To, TArray<FIntPoint>& Out) const
{
	Out.Reset();
	// start / end next to furniture: snap to the nearest walkable tile
	auto Snap = [this](FIntPoint& T)
	{
		if (IsWalkable(T)) return true;
		const int16 O = In(T) ? Owner[Idx(T)] : -1;      // same room / hallway (not through a wall)
		for (int32 D = 1; D <= 2; ++D)
			for (int32 Dx = -D; Dx <= D; ++Dx)
				for (int32 Dy = -D; Dy <= D; ++Dy)
				{
					const FIntPoint C = T + FIntPoint(Dx, Dy);
					if (IsWalkable(C) && (O < 0 || Owner[Idx(C)] == O)) { T = C; return true; }
				}
		return false;
	};
	if (!Snap(From) || !Snap(To)) return false;
	TArray<int32> Prev; Prev.Init(-1, N * N);
	TArray<FIntPoint> Q; Q.Reserve(1024); Q.Add(From); Prev[Idx(From)] = Idx(From);
	for (int32 H = 0; H < Q.Num(); ++H)
	{
		const FIntPoint T = Q[H];
		if (T == To) break;
		for (int32 D = 0; D < 4; ++D)
		{
			const FIntPoint Nb = T + Dir4[D];
			if (!IsWalkable(Nb) || Prev[Idx(Nb)] != -1) continue;
			// different owners touch only at doorways and junction openings (walls elsewhere)
			const int16 Oa = Owner[Idx(T)], Ob = Owner[Idx(Nb)];
			if (Oa != Ob)
			{
				const bool bJunction = (Oa < 1000 && Rooms[Oa].Kind == ERDRoomKind::Junction) || (Ob < 1000 && Rooms[Ob].Kind == ERDRoomKind::Junction);
				if (!bJunction && !DoorEdges.Contains(EdgeKey(T, Nb))) continue;
			}
			Prev[Idx(Nb)] = Idx(T);
			Q.Add(Nb);
		}
	}
	if (Prev[Idx(To)] == -1) return false;
	for (int32 C = Idx(To); ; C = Prev[C])
	{
		Out.Insert(FIntPoint(C % N, C / N), 0);
		if (C == Idx(From)) break;
	}
	return true;
}

TArray<FVector> ARDSection::FindPathWorld(FVector From, FVector To) const
{
	TArray<FVector> Out; TArray<FIntPoint> P;
	if (FindPath(WorldToLocal(From), WorldToLocal(To), P)) for (const FIntPoint& T : P) Out.Add(TileWorld(T));
	return Out;
}

int32 ARDSection::CountReachableRooms() const
{
	if (Rooms.Num() == 0) return 0;
	TSet<int32> Seen;
	TArray<FIntPoint> Path;
	const FIntPoint From = Rooms[0].Lane;
	int32 Cnt = 0;
	for (int32 I = 0; I < Rooms.Num(); ++I) if (FindPath(From, Rooms[I].Lane, Path)) ++Cnt;
	return Cnt;
}

FIntPoint ARDSection::RandomRoomTile(FRandomStream& R, int32 NotRoom) const
{
	for (int32 Try = 0; Try < 20; ++Try)
	{
		const int32 RI = R.RandRange(0, Rooms.Num() - 1);
		if (RI == NotRoom) continue;
		const FRoom& Rm = Rooms[RI];
		const FIntPoint T(R.RandRange(Rm.Min.X, Rm.Max.X - 1), R.RandRange(Rm.Min.Y, Rm.Max.Y - 1));
		if (IsWalkable(T)) return T;
		if (IsWalkable(Rm.Lane)) return Rm.Lane;
	}
	return Rooms.Num() ? Rooms[0].Lane : FIntPoint::ZeroValue;
}

// ------------------------------------------------------------------------------------------------ curtain + tick
void ARDSection::ShowCurtain(UMaterialInterface* Material, float StartTime, float Height, float Lifetime)
{
	if (!Generator || !Material) return;
	UProceduralMeshComponent* C = NewObject<UProceduralMeshComponent>(this);
	C->SetupAttachment(RootComponent);
	C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	C->SetCastShadow(false);
	C->RegisterComponent();
	const float SS = Generator->SectionTiles * Generator->TileSize, Step = 500.f;
	const int32 Ns = FMath::RoundToInt(SS / Step);
	const FVector2D Corner[5] = { FVector2D(0, 0), FVector2D(SS, 0), FVector2D(SS, SS), FVector2D(0, SS), FVector2D(0, 0) };
	TArray<FVector> V; TArray<int32> Tri; TArray<FVector> Nrm; TArray<FVector2D> UV; TArray<FLinearColor> Col; TArray<FProcMeshTangent> Tan;
	float U = 0.f;
	for (int32 Side = 0; Side < 4; ++Side)
	{
		const FVector2D Dr = (Corner[Side + 1] - Corner[Side]).GetSafeNormal();
		const FVector Out = FVector(Dr.Y, -Dr.X, 0.f);
		for (int32 K = 0; K <= Ns; ++K)
		{
			const FVector2D P = Corner[Side] + (Corner[Side + 1] - Corner[Side]) * ((float)K / Ns);
			const int32 I0 = V.Num();
			V.Add(FVector(P.X, P.Y, -40.f)); V.Add(FVector(P.X, P.Y, -40.f + Height));
			UV.Add(FVector2D(U / 1000.f, 0.f)); UV.Add(FVector2D(U / 1000.f, 1.f));
			Nrm.Add(Out); Nrm.Add(Out);
			if (K > 0) Tri.Append({ I0 - 2, I0, I0 - 1, I0 - 1, I0, I0 + 1 });
			U += Step;
		}
	}
	C->CreateMeshSection_LinearColor(0, V, Tri, Nrm, UV, Col, Tan, false);
	UMaterialInstanceDynamic* M = UMaterialInstanceDynamic::Create(Material, C);
	M->SetScalarParameterValue(TEXT("StartTime"), StartTime);
	C->SetMaterial(0, M);
	FTimerHandle H;
	GetWorldTimerManager().SetTimer(H, FTimerDelegate::CreateWeakLambda(C, [C]() { C->DestroyComponent(); }), Lifetime, false);
}

void ARDSection::Tick(float Dt)
{
	Super::Tick(Dt);
	UWorld* W = GetWorld();
	if (!W || !W->IsGameWorld()) return;
	const float Now = W->GetTimeSeconds();
	const AActor* Pawn = Generator ? Generator->GetTrackedActor() : UGameplayStatics::GetPlayerPawn(this, 0);
	const FVector PL = Pawn ? Pawn->GetActorLocation() : FVector(1e9);
	// cinematics: doors open by themselves in front of the tracked actor
	if (Generator && Generator->TrackedActor && Generator->TrackedAutoDoorDistance > 0.f)
		for (int32 I = 0; I < Doors.Num(); ++I)
		{
			FMover& M = Doors[I];
			if (M.Target > 0.5f || M.bCell) continue;
			if (FVector::Dist2D(PL, M.Center) < Generator->TrackedAutoDoorDistance) ToggleDoor(I, PL);
		}
	// torch flicker near the player
	for (const FFlicker& F : Flickers)
	{
		if (!F.Light || FVector::DistSquared(F.Light->GetComponentLocation(), PL) > 4000.f * 4000.f) continue;
		const float Nz = FMath::PerlinNoise1D(Now * 7.f + F.Phase) * 0.6f + FMath::PerlinNoise1D(Now * 19.f + F.Phase * 2.f) * 0.4f;
		F.Light->SetIntensity(F.Base * (1.f + F.Amount * Nz * 1.6f));
	}
	// doors a monster opened close again once nobody is in the doorway
	for (int32 I = 0; I < Doors.Num(); ++I)
	{
		FMover& M = Doors[I];
		if (!M.bByMonster || M.Target < 0.5f) continue;
		bool bNear = FVector::Dist2D(PL, M.Center) < 300.f;
		for (ARDMonster* Mo : SpawnedMonsters) if (Mo && FVector::Dist2D(Mo->GetActorLocation(), M.Center) < 260.f) bNear = true;
		M.MonsterCloseTimer = bNear ? 0.f : M.MonsterCloseTimer + Dt;
		if (M.MonsterCloseTimer > 2.5f)
		{
			M.Target = 0.f; M.bByMonster = false;
			if (Generator && (M.Partner < 0 || M.Partner > I)) Generator->PlaySoundAt(M.bCell ? TEXT("Env.CellClose") : TEXT("Env.DoorClose"), M.Center);
		}
	}
	auto Animate = [Dt](FMover& M)
	{
		if (M.Alpha == M.Target) return;
		M.Alpha = FMath::FInterpConstantTo(M.Alpha, M.Target, Dt, M.bDoor ? 1.4f : 1.8f);
		const float E = M.Alpha * M.Alpha * (3.f - 2.f * M.Alpha);
		M.Pivot->SetRelativeRotation(M.Closed * FQuat(M.Axis, FMath::DegreesToRadians(M.OpenAngle * E)));
		// moving / open leaves and lids never push anyone (a wardrobe door swinging into her would wedge her)
		const bool bShut = M.Alpha < 0.02f;
		for (UStaticMeshComponent* C : M.Parts)
			C->SetCollisionEnabled(bShut ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
	};
	for (FMover& M : Doors) Animate(M);
	for (FMover& M : Containers) Animate(M);
}
