// The user's list of 2026-11-04 (docs/improvements7.txt) in the town (Brokenspire and the wilderness's small towns, which
// are built by the same code):
//   - the open ground rises and falls (TownLiftPlan / TownLiftAt): a weight per tile, 0 where anything stands or is walked to
//     (buildings and a tile round them, the roads, the square, the gardens, pens, fires, the spots outdoors), rising to 1 over
//     three tiles of open ground; the height there a smooth noise of the section's seed (no draws from the plan's stream);
//     the trees and the grass placed after it stand on it, the drawn ground and the walked ground follow it
//   - the gate's portcullis a door that lifts, a lever each side of the gate that raises and lowers it (it stays as she left
//     it: the game instance); the pens' gates swing on a hinge
//   - food set out on the tavern's tables and the kitchens' prep tables, taken with F; a garden harvested for its crops (they
//     grow again the next day); the kitchens' bread ovens bake the gardens' ingredients (the crafting panel, its oven recipes)
#include "RD/RDSection.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDTown.h"
#include "RD/RDCombat.h"
#include "RD/RDGameInstance.h"
#include "Components/StaticMeshComponent.h"
#include "ProceduralMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDTown7, Log, All);

namespace
{
	/** smooth value noise in [0, 1] */
	float RD7Noise(float X, float Y, uint32 Seed)
	{
		const int32 Xi = FMath::FloorToInt(X), Yi = FMath::FloorToInt(Y);
		const float Fx = X - Xi, Fy = Y - Yi, Sx = Fx * Fx * (3.f - 2.f * Fx), Sy = Fy * Fy * (3.f - 2.f * Fy);
		auto H = [Seed](int32 A, int32 B) { return (HashCombine(HashCombine((uint32)A * 73856093u, (uint32)B * 19349663u), Seed) & 0xffffu) / 65535.f; };
		return FMath::Lerp(FMath::Lerp(H(Xi, Yi), H(Xi + 1, Yi), Sx), FMath::Lerp(H(Xi, Yi + 1), H(Xi + 1, Yi + 1), Sx), Sy);
	}
	float RD7Smooth(float A, float B, float X) { const float T = FMath::Clamp((X - A) / (B - A), 0.f, 1.f); return T * T * (3.f - 2.f * T); }
	const FIntPoint RD7Dir4[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };
	FString RD7Key(int32 Seed, int32 I) { return FString::Printf(TEXT("%d:%d"), Seed, I); }
}

// ------------------------------------------------------------------------------------------------ the ground's rise and fall
void ARDSection::TownLiftPlan()
{
	TownLiftW.Init(0.f, N * N);
	if (!Generator || Type.Num() != N * N || Generator->TownLiftAmp <= 0.f) return;
	const float M = Generator->TileSize;
	TArray<uint8> Flat; Flat.Init(0, N * N);
	auto MarkR = [&](const FIntPoint& T, int32 Rr) { for (int32 Dx = -Rr; Dx <= Rr; ++Dx) for (int32 Dy = -Rr; Dy <= Rr; ++Dy) { const FIntPoint Q = T + FIntPoint(Dx, Dy); if (In(Q)) Flat[Idx(Q)] = 1; } };
	// (anything but open ground: rooms, the void under the towers, what stands on a tile, every road; outside the wall the
	// land is open too, but for a strip along the wall and the section's edge, where the wilderness's ground meets it)
	for (int32 X = 0; X < N; ++X)
		for (int32 Y = 0; Y < N; ++Y)
		{
			const FIntPoint T(X, Y);
			const int32 I = Idx(T);
			if (Type[I] == 0)
			{
				const FVector2D W(TileWorld(T));
				const bool bOut = TownBorder.Num() >= 3 && !InsideTownBorder(W) && TownBorderDist(W) > 3.5f * M;
				const bool bEdge = X < 3 || Y < 3 || X >= N - 3 || Y >= N - 3;
				if (!bOut || bEdge) Flat[I] = 1;
				continue;
			}
			if (Type[I] != 2 || (Blocked.IsValidIndex(I) && Blocked[I]) || (TownRoadMask.IsValidIndex(I) && TownRoadMask[I])) Flat[I] = 1;
			if (Type[I] == 1) MarkR(T, 1);        // (a building and a tile round it)
		}
	for (int32 X = TownSquare.Min.X; X < TownSquare.Max.X; ++X) for (int32 Y = TownSquare.Min.Y; Y < TownSquare.Max.Y; ++Y) MarkR(FIntPoint(X, Y), 1);
	for (const FIntRect& Rr : TownRoads) for (int32 X = Rr.Min.X; X < Rr.Max.X; ++X) for (int32 Y = Rr.Min.Y; Y < Rr.Max.Y; ++Y) MarkR(FIntPoint(X, Y), 1);
	for (const FTownBld& B : TownBlds) for (int32 K = 1; K <= 2; ++K) MarkR(B.DoorTile + RD7Dir4[B.DoorSide] * K, 0);
	for (const FTownSpot& Sp : TownSpots)
	{
		const int32 Rr = Sp.Kind == TS_Circle ? 4 : Sp.Kind == TS_Mill ? 5 : Sp.Kind == TS_Gate ? 4 : (Sp.Kind == TS_Tent || Sp.Kind == TS_Tower || Sp.Kind == TS_Graveyard) ? 3 : 1;
		MarkR(WorldToLocal(Sp.At), Rr);
	}
	for (const FTownWork& W : TownWorks) MarkR(WorldToLocal(W.At), 0);
	auto MarkBox = [&](const FVector& C, const FVector2D& H)
	{
		const FIntPoint A = WorldToLocal(C - FVector(H.X, H.Y, 0.f)), B = WorldToLocal(C + FVector(H.X, H.Y, 0.f));
		for (int32 X = A.X; X <= B.X; ++X) for (int32 Y = A.Y; Y <= B.Y; ++Y) MarkR(FIntPoint(X, Y), 1);
	};
	for (const FTownGarden& G : TownGardens) MarkBox(G.At, G.Half);
	for (const FTownPen& P : TownPens) MarkBox(P.At, P.Half);
	if (!TownGate.IsNearlyZero()) MarkR(WorldToLocal(TownGate), 4);
	// (the tiles' distance from the flat ones, by steps across tiles; the weight rises over three tiles from a tile and a half)
	TArray<int32> D; D.Init(MAX_int32, N * N);
	TArray<FIntPoint> Q; Q.Reserve(N * N);
	for (int32 I = 0; I < N * N; ++I) if (Flat[I]) { D[I] = 0; Q.Add(FIntPoint(I % N, I / N)); }
	for (int32 H = 0; H < Q.Num(); ++H)
	{
		const FIntPoint T = Q[H];
		for (int32 K = 0; K < 4; ++K)
		{
			const FIntPoint Nb = T + RD7Dir4[K];
			if (!In(Nb) || D[Idx(Nb)] != MAX_int32) continue;
			D[Idx(Nb)] = D[Idx(T)] + 1; Q.Add(Nb);
		}
	}
	int32 Open = 0;
	for (int32 I = 0; I < N * N; ++I)
	{
		// (level where anything is; rising from the next tile on, whole three tiles out)
		TownLiftW[I] = D[I] == MAX_int32 ? 1.f : RD7Smooth(0.5f, 3.f, (float)D[I]);
		Open += TownLiftW[I] > 0.5f;
	}
	(void)M;
	UE_LOG(LogRDTown7, Log, TEXT("RDTOWN7 the ground's rise and fall: %d of %d tiles open ground (%.0f cm at most)"), Open, N * N, Generator->TownLiftAmp);
}

float ARDSection::TownLiftAt(const FVector2D& World) const
{
	if (!Generator || TownLiftW.Num() != N * N || N <= 0) return 0.f;
	const float M = Generator->TileSize;
	const FVector L = GetActorLocation();
	const float Lx = World.X - L.X, Ly = World.Y - L.Y;
	const float U = Lx / M - 0.5f, V = Ly / M - 0.5f;
	const int32 I0 = FMath::FloorToInt(U), J0 = FMath::FloorToInt(V);
	const float Fx = U - I0, Fy = V - J0;
	auto Wt = [&](int32 I, int32 J) { return (I < 0 || J < 0 || I >= N || J >= N) ? 0.f : TownLiftW[J * N + I]; };
	const float W = FMath::Lerp(FMath::Lerp(Wt(I0, J0), Wt(I0 + 1, J0), Fx), FMath::Lerp(Wt(I0, J0 + 1), Wt(I0 + 1, J0 + 1), Fx), Fy);
	if (W <= 0.001f) return 0.f;
	// (hills and hollows some 25 m across, smaller swells on them)
	const uint32 Sd = (uint32)Seed ^ 0x11F7u;
	const float Nn = 0.62f * RD7Noise(Lx / 2800.f, Ly / 2800.f, Sd) + 0.28f * RD7Noise(Lx / 1150.f, Ly / 1150.f, Sd + 7u) + 0.10f * RD7Noise(Lx / 520.f, Ly / 520.f, Sd + 13u);
	const float H = FMath::Clamp((Nn - 0.5f) * 2.8f, -1.f, 1.f);
	return W * Generator->TownLiftAmp * H;
}

// ------------------------------------------------------------------------------------------------ the gate, its levers, the pens
void ARDSection::TownGateWorks()
{
	if (!bBuildInteractive || !Generator) return;
	const FRDPiece* G = Generator->Piece(TEXT("Town.Gate"));
	if (!G || !G->Mesh) return;
	const float GYaw = TownGateOut.Rotation().Yaw;
	const FRotator Rt(0, GYaw, 0);
	const URDGameInstance* GI = URDGameInstance::Of(this);
	// (Brokenspire's stays as she left it (shut at a new game); the small towns' stand open: she comes to them from outside)
	const bool bUp = !Generator->bTownHome || (GI && GI->bPortcullisUp);
	USceneComponent* Pv = AddPivot(RootComponent, FTransform(Rt, TownGate - GetActorLocation()));
	UStaticMeshComponent* Pc = AddMesh(Pv, G->Mesh, G->Adjust, true);
	FMover Mv; Mv.Pivot = Pv; Mv.Parts = { Pc }; Mv.bDoor = true; Mv.bLift = true; Mv.LiftZ = Generator->TownPortcullisLift;
	Mv.ClosedLoc = Pv->GetRelativeLocation(); Mv.Closed = Pv->GetRelativeRotation().Quaternion(); Mv.Kind = TEXT("portcullis");
	Mv.Center = TownGate + FVector(0, 0, 120.f); Mv.Normal = TownGateOut;
	if (bUp) { Mv.Alpha = Mv.Target = 1.f; Pv->SetRelativeLocation(Mv.ClosedLoc + FVector(0, 0, Mv.LiftZ)); Pc->SetCollisionEnabled(ECollisionEnabled::NoCollision); }
	TownPortcullis = Doors.Add(Mv);
	// (a lever each side, 3.2 m along the wall from the gate's middle: a post, its arm thrown from leaning out to leaning in)
	const FRDPiece* Post = Generator->Piece(TEXT("Town.LeverPost"));
	const FRDPiece* Arm = Generator->Piece(TEXT("Town.LeverArm"));
	if (!Post || !Post->Mesh || !Arm || !Arm->Mesh) return;
	const FVector Across = Rt.RotateVector(FVector(0, 1, 0));
	for (int32 Side = -1; Side <= 1; Side += 2)
	{
		const FVector Base = TownGate + Across * 320.f + TownGateOut * (Side * 105.f);
		AddMesh(RootComponent, Post->Mesh, Post->Adjust * FTransform(Rt, Base - GetActorLocation()), true);
		const float PostH = FMath::Max((float)Post->Size.Z, 40.f);
		USceneComponent* Ap = AddPivot(RootComponent, FTransform(Rt, Base + FVector(0, 0, PostH - 8.f) - GetActorLocation()));
		AddMesh(Ap, Arm->Mesh, Arm->Adjust, false);
		FMover Lv; Lv.Pivot = Ap; Lv.bDoor = true; Lv.Kind = TEXT("lever"); Lv.Link = TownPortcullis;
		// (about the gate's way across: from 40 degrees one way to 40 the other)
		Lv.Axis = FVector(0, 1, 0); Lv.OpenAngle = 80.f;
		Lv.Closed = Rt.Quaternion() * FQuat(FVector(0, 1, 0), FMath::DegreesToRadians(-40.f));
		Lv.Center = Base + FVector(0, 0, 100.f); Lv.Normal = TownGateOut;
		Ap->SetRelativeRotation(Lv.Closed);
		if (bUp) { Lv.Alpha = Lv.Target = 1.f; Ap->SetRelativeRotation(Lv.Closed * FQuat(Lv.Axis, FMath::DegreesToRadians(Lv.OpenAngle))); }
		TownLevers.Add(Doors.Add(Lv));
	}
}

void ARDSection::TownPenGate(const FVector& HingeW, float Yaw, float Len)
{
	if (!bBuildInteractive || !Generator) return;
	const FRDPiece* P = Generator->Piece(TEXT("Town.PenFence"));
	if (!P || !P->Mesh) return;
	const float Fl = FMath::Max((float)P->Size.Y, 60.f);
	const FRotator Rt(0, Yaw, 0);
	USceneComponent* Pv = AddPivot(RootComponent, FTransform(Rt, HingeW - GetActorLocation()));
	// (the fence piece runs along its +Y, centred on where it is put: the leaf from the hinge along +Y)
	UStaticMeshComponent* Leaf = AddMesh(Pv, P->Mesh, P->Adjust * FTransform(FRotator::ZeroRotator, FVector(0, Len * 0.5f, 0), FVector(1.f, Len / Fl * 0.97f, 1.f)), true);
	FMover Mv; Mv.Pivot = Pv; Mv.Parts = { Leaf }; Mv.Closed = Pv->GetRelativeRotation().Quaternion(); Mv.bDoor = true; Mv.Kind = TEXT("gate");
	Mv.LeafSign = 1.f;
	Mv.Center = HingeW + Rt.RotateVector(FVector(0, Len * 0.5f, 0)) + FVector(0, 0, 60.f);
	Mv.Normal = Rt.RotateVector(FVector(1, 0, 0));
	TownPenGates.Add(Doors.Add(Mv));
}

bool ARDSection::PullTownLever(int32 Lever, FVector Opener)
{
	if (!TownLevers.IsValidIndex(Lever)) return false;
	ToggleDoor(TownLevers[Lever], Opener);          // (it records the portcullis: RecordPortcullis)
	return true;
}

void ARDSection::RecordPortcullis(bool bUp)
{
	if (URDGameInstance* GI = URDGameInstance::Of(this); GI && Generator && Generator->bTownHome) GI->bPortcullisUp = bUp;
}

// ------------------------------------------------------------------------------------------------ food, gardens, ovens
void ARDSection::TownFoodOn(FRandomStream& Rf, const FVector& Top, float Yaw)
{
	if (!bBuildInteractive || !Generator) return;
	static const TCHAR* Kinds[] = { TEXT("Town.FoodBread"), TEXT("Town.FoodBreadRound"), TEXT("Town.FoodCheese"), TEXT("Town.FoodApples") };
	static const TCHAR* Gives[] = { TEXT("Bread"), TEXT("Bread"), TEXT("Cheese"), TEXT("Fruit") };
	const URDGameInstance* GI = URDGameInstance::Of(this);
	FTownFood F; F.At = Top;
	const int32 Ix = TownFoods.Num();
	F.bTaken = GI && GI->FoodTaken.Contains(RD7Key(Seed, Ix));
	const FRotator Rt(0, Yaw, 0);
	const int32 Count = Rf.RandRange(1, 3);
	for (int32 K = 0; K < Count; ++K)
	{
		const int32 Kd = Rf.RandRange(0, 3);
		const FVector Off = Rt.RotateVector(FVector(Rf.FRandRange(-14.f, 14.f), (K - (Count - 1) * 0.5f) * 30.f + Rf.FRandRange(-4.f, 4.f), 0.f));
		const float Ty = Rf.FRandRange(0.f, 360.f);
		const FRDPiece* P = Generator->Piece(Kinds[Kd]);
		if (!P || !P->Mesh) continue;
		F.Items.Add(Gives[Kd]);
		if (Kd == 3) F.Items.Add(Gives[Kd]);
		if (!F.bTaken) F.Comps.Add(AddMesh(RootComponent, P->Mesh, P->Adjust * FTransform(FRotator(0, Ty, 0), Top + Off - GetActorLocation()), false));
	}
	if (F.Items.Num() > 0) TownFoods.Add(F);
}

bool ARDSection::TakeTownFood(int32 Index)
{
	if (!TownFoods.IsValidIndex(Index) || TownFoods[Index].bTaken) return false;
	FTownFood& F = TownFoods[Index];
	F.bTaken = true;
	for (const TWeakObjectPtr<UStaticMeshComponent>& C : F.Comps) if (UStaticMeshComponent* Cp = C.Get()) { Cp->SetVisibility(false); Cp->SetHiddenInGame(true); }
	if (URDGameInstance* GI = URDGameInstance::Of(this)) GI->FoodTaken.AddUnique(RD7Key(Seed, Index));
	return true;
}

FString ARDSection::FindTownThing(const FVector& From, float Reach, int32& OutIndex) const
{
	OutIndex = -1;
	FString Kind; float Best = Reach;
	for (int32 I = 0; I < TownFoods.Num(); ++I)
	{
		const FTownFood& F = TownFoods[I];
		if (F.bTaken || FMath::Abs(F.At.Z - From.Z) > 160.f) continue;
		const float D = FVector::Dist2D(F.At, From);
		if (D < Best) { Best = D; Kind = TEXT("food"); OutIndex = I; }
	}
	for (int32 I = 0; I < TownLevers.Num(); ++I)
		if (Doors.IsValidIndex(TownLevers[I]))
		{
			const float D = FVector::Dist2D(Doors[TownLevers[I]].Center, From);
			if (D < Best) { Best = D; Kind = TEXT("lever"); OutIndex = I; }
		}
	for (int32 I = 0; I < TownOvens.Num(); ++I)
	{
		if (FMath::Abs(TownOvens[I].Z - From.Z) > 200.f) continue;
		const float D = FVector::Dist2D(TownOvens[I], From) - 60.f;
		if (D < Best) { Best = D; Kind = TEXT("oven"); OutIndex = I; }
	}
	// (a garden: from its fence's edge, or inside it)
	for (int32 I = 0; I < TownGardens.Num(); ++I)
	{
		const FTownGarden& G = TownGardens[I];
		const float Dx = FMath::Max(FMath::Abs(From.X - G.At.X) - G.Half.X, 0.f), Dy = FMath::Max(FMath::Abs(From.Y - G.At.Y) - G.Half.Y, 0.f);
		const float D = FMath::Sqrt(Dx * Dx + Dy * Dy) + 30.f;
		if (D < Best && Dx < 110.f && Dy < 110.f) { Best = D; Kind = TEXT("garden"); OutIndex = I; }
	}
	// (a door or a container nearer than it is what F does, as with the townsfolk (the PR review's find: an oven or a garden
	// took F from a cupboard or a chest beside it for good); a lever is a door itself)
	if (!Kind.IsEmpty())
	{
		bool bD = false; int32 Di = -1;
		const float Dd = FindNearestInteractive(From, Best, bD, Di);
		if (Dd < Best && !(bD && TownLevers.Contains(Di))) { OutIndex = -1; return FString(); }
	}
	return Kind;
}

TArray<FString> ARDSection::GetTownImproveLines() const
{
	TArray<FString> Out;
	if (Doors.IsValidIndex(TownPortcullis))
	{
		const FMover& Pm = Doors[TownPortcullis];
		const FVector P = Pm.Pivot ? Pm.Pivot->GetComponentLocation() : Pm.Center;
		Out.Add(FString::Printf(TEXT("gate|%d|%d|%.2f|%.0f|%.0f|%.0f"), TownPortcullis, Pm.Target > 0.5f ? 1 : 0, Pm.Alpha, P.X, P.Y, P.Z));
	}
	for (int32 I = 0; I < TownLevers.Num(); ++I) if (Doors.IsValidIndex(TownLevers[I])) { const FVector C = Doors[TownLevers[I]].Center; Out.Add(FString::Printf(TEXT("lever|%d|%.0f|%.0f|%.0f"), TownLevers[I], C.X, C.Y, C.Z)); }
	for (const int32 Gi : TownPenGates) if (Doors.IsValidIndex(Gi)) { const FVector C = Doors[Gi].Center; Out.Add(FString::Printf(TEXT("pengate|%d|%d|%.0f|%.0f|%.0f"), Gi, Doors[Gi].Target > 0.5f ? 1 : 0, C.X, C.Y, C.Z)); }
	for (const FVector& O : TownOvens) Out.Add(FString::Printf(TEXT("oven|%.0f|%.0f|%.0f"), O.X, O.Y, O.Z));
	for (int32 I = 0; I < TownFoods.Num(); ++I)
	{
		TArray<FString> It; for (const FName& N_ : TownFoods[I].Items) It.Add(N_.ToString());
		Out.Add(FString::Printf(TEXT("food|%d|%d|%.0f|%.0f|%.0f|%s"), I, TownFoods[I].bTaken ? 1 : 0, TownFoods[I].At.X, TownFoods[I].At.Y, TownFoods[I].At.Z, *FString::Join(It, TEXT(","))));
	}
	for (int32 I = 0; I < TownGardens.Num(); ++I)
	{
		TArray<FString> Cs; for (const uint8 C : TownGardens[I].Crops) Cs.Add(FString::FromInt(C));
		Out.Add(FString::Printf(TEXT("garden|%d|%s|%.0f|%.0f"), I, *FString::Join(Cs, TEXT(",")), TownGardens[I].At.X, TownGardens[I].At.Y));
	}
	// (the rise and fall: its highest and lowest at the tiles' middles, and the most under any building)
	float Hi = -1e9f, Lo = 1e9f, Bld = 0.f;
	for (int32 X = 0; X < N; ++X)
		for (int32 Y = 0; Y < N; ++Y)
		{
			const FVector C = TileWorld(FIntPoint(X, Y));
			const float H = TownLiftAt(FVector2D(C));
			Hi = FMath::Max(Hi, H); Lo = FMath::Min(Lo, H);
			if (Type.IsValidIndex(Idx(FIntPoint(X, Y))) && Type[Idx(FIntPoint(X, Y))] == 1) Bld = FMath::Max(Bld, FMath::Abs(H));
		}
	Out.Add(FString::Printf(TEXT("lift|%.1f|%.1f|%.2f"), Hi, Lo, Bld));
	return Out;
}

FLinearColor ARDSection::GetTownGroundColorAt(FVector Location) const
{
	// (the drawn ground's layers at its vertex nearest a point: R trodden floor, G cobbles, A earth (TownGround, a vertex a metre))
	const UProceduralMeshComponent* Gm = nullptr;
	TInlineComponentArray<UProceduralMeshComponent*> Cs(this);
	for (const UProceduralMeshComponent* C : Cs) if (C && C->GetName() == TEXT("TownGround")) { Gm = C; break; }
	if (!Gm || !Generator || Gm->GetNumSections() == 0) return FLinearColor(-1, -1, -1, -1);
	const FProcMeshSection* Sec = const_cast<UProceduralMeshComponent*>(Gm)->GetProcMeshSection(0);
	if (!Sec) return FLinearColor(-1, -1, -1, -1);
	const float St = Generator->TileSize / 3.f;
	const int32 Nv = N * 3 + 1;
	const FVector L = Location - GetActorLocation();
	const int32 I = FMath::Clamp(FMath::RoundToInt(L.X / St), 0, Nv - 1), J = FMath::Clamp(FMath::RoundToInt(L.Y / St), 0, Nv - 1);
	const int32 K = I * Nv + J;
	if (!Sec->ProcVertexBuffer.IsValidIndex(K)) return FLinearColor(-1, -1, -1, -1);
	const FColor C = Sec->ProcVertexBuffer[K].Color;
	return FLinearColor(C.R / 255.f, C.G / 255.f, C.B / 255.f, C.A / 255.f);
}

// ================================================================================================ the generator's side
bool ARDDungeonGenerator::IsGardenRipe(int32 Garden) const
{
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (!S || !S->TownGardens.IsValidIndex(Garden)) return false;
	const int32* Day = GI ? GI->GardensHarvested.Find(RD7Key(S->Seed, Garden)) : nullptr;
	return !Day || TownDay - *Day >= FMath::Max(GardenRegrowDays, 1);
}

bool ARDDungeonGenerator::TownHarvestGarden(ARDSection* S, int32 Garden)
{
	if (!S || !PlayerCombat || !S->TownGardens.IsValidIndex(Garden)) return false;
	if (!IsGardenRipe(Garden)) { PlayerCombat->ShowMessage(TEXT("This garden has been harvested: it grows again by tomorrow")); return false; }
	const ARDSection::FTownGarden& G = S->TownGardens[Garden];
	TArray<FString> Got;
	for (int32 K = 0; K < G.Crops.Num(); ++K)
	{
		const int32 Ck = G.Crops[K];
		if (!TownCropItems.IsValidIndex(Ck) || TownCropItems[Ck].IsNone() || FindItem(TownCropItems[Ck]) < 0) continue;
		const uint32 H = HashCombine(HashCombine((uint32)S->Seed, (uint32)Garden * 7919u), (uint32)(K + 1) * 2654435761u ^ (uint32)TownDay);
		const int32 N = 2 + (int32)(H % 2u);
		PlayerCombat->AddItem(TownCropItems[Ck], N);
		Got.Add(FString::Printf(TEXT("%d %s"), N, *TownCropItems[Ck].ToString().ToLower()));
	}
	if (Got.Num() == 0) return false;
	if (URDGameInstance* GI = URDGameInstance::Of(this)) GI->GardensHarvested.Add(RD7Key(S->Seed, Garden), TownDay);
	TownCount(TEXT("harvests"));
	PlayerCombat->ShowMessage(FString::Printf(TEXT("You harvest the garden:  %s"), *FString::Join(Got, TEXT(", "))));
	PlaySoundAt(TEXT("Player.Loot"), G.At);
	UE_LOG(LogRDTown7, Log, TEXT("RDTOWN7 garden %d harvested: %s"), Garden, *FString::Join(Got, TEXT(", ")));
	return true;
}

FString ARDDungeonGenerator::TownThingDescribe(const FVector& From) const
{
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S) return FString();
	int32 I = -1;
	const FString K = S->FindTownThing(From, TownThingReach, I);
	if (K == TEXT("food"))
	{
		TArray<FString> It; for (const FName& N_ : S->TownFoods[I].Items) It.AddUnique(N_.ToString().ToLower());
		return FString::Printf(TEXT("take the food (%s)"), *FString::Join(It, TEXT(", ")));
	}
	if (K == TEXT("garden")) return IsGardenRipe(I) ? FString(TEXT("harvest the garden")) : FString(TEXT("the garden (harvested: it grows again tomorrow)"));
	if (K == TEXT("oven")) return TEXT("bake at the oven");
	if (K == TEXT("lever")) return S->IsPortcullisUp() ? FString(TEXT("pull the lever (lower the portcullis)")) : FString(TEXT("pull the lever (raise the portcullis)"));
	return FString();
}

FString ARDDungeonGenerator::TownThingInteract(const FVector& From)
{
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S || !PlayerCombat) return FString();
	int32 I = -1;
	const FString K = S->FindTownThing(From, TownThingReach, I);
	if (K == TEXT("food"))
	{
		const TArray<FName> It = S->TownFoods[I].Items;
		if (!S->TakeTownFood(I)) return FString();
		TMap<FName, int32> Cnt; for (const FName& N_ : It) Cnt.FindOrAdd(N_)++;
		TArray<FString> Got;
		for (const TPair<FName, int32>& C : Cnt) { if (FindItem(C.Key) < 0) continue; PlayerCombat->AddItem(C.Key, C.Value); Got.Add(FString::Printf(TEXT("%d %s"), C.Value, *C.Key.ToString().ToLower())); }
		PlayerCombat->ShowMessage(FString::Printf(TEXT("You take the food from the table:  %s"), *FString::Join(Got, TEXT(", "))));
		PlaySoundAt(TEXT("Player.Loot"), From);
		TownCount(TEXT("food"));
		return TEXT("food");
	}
	if (K == TEXT("garden")) { TownHarvestGarden(S, I); return TEXT("garden"); }
	if (K == TEXT("oven"))
	{
		PlayerCombat->SetCraftStation(TEXT("Oven"));
		PlayerCombat->SetCraftingOpen(true);
		return TEXT("oven");
	}
	if (K == TEXT("lever"))
	{
		S->PullTownLever(I, From);
		PlayerCombat->ShowMessage(S->IsPortcullisUp() ? TEXT("The portcullis rises") : TEXT("The portcullis comes down"));
		return TEXT("lever");
	}
	return FString();
}
