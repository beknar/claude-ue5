// The user's list of 2026-11-11 (docs/improvements11.txt), its fourth phase, the farmsteads:
//   - "not all the buildings at a farmhold have interiors nor can the doors be opened. example: Garrick's hold": every building
//     of a farmstead is raised from the town's kit (Town.<style>_<part>: floor, walls, a doorway with its door on its hinge, the
//     roof and gables) over a stone plinth, with its inside by its kind (WildKitBuilding); the open houses' doors on a side wall
//     open too (FitWildHouse, RDWild10.cpp);
//   - "all the farms use the exact same design. have at least 50 different designs for farms, and they should all have interiors.
//     they should have these types of buildings: the farmhouse, the barn, gardens, animals in pens with different configurations
//     for pens and the kinds of animals in them": the designs are data (919, SourceArt/wilderness/farm_designs.json, written by
//     blender_numpy/farm_designs.py): houses, barns, sheds, coops and granaries, gardens of the town's crops, pens of three shapes
//     (one, two side by side, round) and stalls in a barn, with the kinds of the town's farm animals; a farmstead takes one by its id;
//   - "farmholds should have some food in them to loot - none of the containers work": the chests, barrels, crates, wardrobes and
//     gardens open and give food (AddWildBox: a chunk door that is a container; FarmLoot by kind), kept looted in the game.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDTown.h"
#include "RD/RDCombat.h"
#include "RD/RDSection.h"
#include "RD/RDGameInstance.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "ProceduralMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDWildFarm11, Log, All);

namespace
{
	// the farm's frame: a point u metres along its way and v across it (metres)
	FVector2D RDWF11At(const FRDWildPlace& P, float U, float V)
	{
		const float A = FMath::DegreesToRadians(P.Yaw);
		const FVector2D Fw(FMath::Cos(A), FMath::Sin(A)), Sd(-Fw.Y, Fw.X);
		return P.At + Fw * U + Sd * V;
	}
	UStaticMesh* RDWF11Cube()
	{
		static TWeakObjectPtr<UStaticMesh> Cube;
		if (!Cube.IsValid()) Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
		return Cube.Get();
	}
	/** the key a farm's container n is kept looted under (above the kills' place x 16 + n and the points' negative keys) */
	int64 RDWF11Key(int32 FarmId, int32 N) { return (1LL << 40) + (int64)(uint32)FarmId * 64 + (N & 63); }
	/** "Kind:count, Kind:count" */
	TArray<TPair<FString, int32>> RDWF11Animals(const FString& S)
	{
		TArray<TPair<FString, int32>> Out;
		TArray<FString> Parts; S.ParseIntoArray(Parts, TEXT(","), true);
		for (const FString& P : Parts)
		{
			FString K, N;
			if (!P.Split(TEXT(":"), &K, &N)) { K = P; N = TEXT("3"); }
			Out.Add({ K.TrimStartAndEnd(), FMath::Max(1, FCString::Atoi(*N)) });
		}
		return Out;
	}
}

// ================================================================================================ a container in the wilds
bool ARDDungeonGenerator::AddWildBox(ARDWildChunk* C, FName PieceName, const FTransform& At, FName Kind, int64 Key, const FString& Loot, FRDWildFarmRec* Rec, const FVector* FrontAt)
{
	const FRDPiece* P = PieceName.IsNone() ? nullptr : Piece(PieceName);
	if (!C || !C->Ground || (!PieceName.IsNone() && (!P || !P->Mesh))) return false;
	auto Keep = [&](UActorComponent* X) { if (Rec && X) Rec->Comps.Add(X); };
	USceneComponent* Bs = NewObject<USceneComponent>(C);
	Bs->SetMobility(EComponentMobility::Movable);
	Bs->SetupAttachment(C->Ground);
	Bs->RegisterComponent();
	Bs->SetWorldTransform(At);
	Keep(Bs);
	ARDWildChunk::FDoor D;
	D.bBox = true; D.Kind = Kind; D.Key = Key; D.Loot = Loot;
	D.At = FrontAt ? *FrontAt : At.GetLocation();
	D.Out = At.GetRotation().GetForwardVector();
	if (P)
	{
		auto Comp = [&](USceneComponent* Parent, UStaticMesh* M, const FTransform& Rel) -> UStaticMeshComponent*
		{
			UStaticMeshComponent* Sm = NewObject<UStaticMeshComponent>(C);
			Sm->SetMobility(EComponentMobility::Movable);
			Sm->SetStaticMesh(M);
			Sm->SetupAttachment(Parent);
			Sm->SetRelativeTransform(Rel);
			if (P->Material) Sm->SetMaterial(0, P->Material);
			if (!P->bCollision) Sm->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Sm->RegisterComponent();
			C->PlaceProps.Add(Sm);
			Keep(Sm);
			return Sm;
		};
		Comp(Bs, P->Mesh, P->Adjust);
		// (its moving part(s) on a pivot at the hinge (the piece's frame), as the dungeon's containers (ARDSection::AddContainer): a
		// lid lifts about Y at its back, a wardrobe's doors swing out about the up axis)
		const bool bVert = PieceName == TEXT("Wardrobe");
		auto Moving = [&](UStaticMesh* Mesh, const FVector& Hinge, float& Angle, FQuat& Closed) -> USceneComponent*
		{
			if (!Mesh) return nullptr;
			USceneComponent* Hp = NewObject<USceneComponent>(C);
			Hp->SetMobility(EComponentMobility::Movable);
			Hp->SetupAttachment(Bs);
			Hp->SetRelativeTransform(FTransform(Hinge));
			Hp->RegisterComponent();
			Keep(Hp);
			FTransform Rel = P->Adjust; Rel.SetTranslation(FVector::ZeroVector);
			Comp(Hp, Mesh, Rel);
			const FBox B = Mesh->GetBoundingBox().TransformBy(Rel);
			D.Axis = bVert ? FVector::UpVector : FVector::RightVector;
			const FVector Tip = bVert ? FVector(0.f, B.GetCenter().Y, 0.f) : FVector(B.GetCenter().X, 0.f, 0.f);
			const FVector Want = bVert ? FVector(1.f, 0.f, 0.f) : FVector::UpVector;
			const FVector Pp = FQuat(D.Axis, FMath::DegreesToRadians(60.f)).RotateVector(Tip);
			Angle = 100.f * (FVector::DotProduct(Pp - Tip, Want) >= 0.f ? 1.f : -1.f);
			Closed = Hp->GetRelativeRotation().Quaternion();
			return Hp;
		};
		D.Pivot = Moving(P->Moving, P->Hinge, D.Angle, D.Closed);
		if (P->Moving2) D.Pivot2 = Moving(P->Moving2, P->Hinge2, D.Angle2, D.Closed2);
	}
	// (no moving part (a garden's harvest): its base, never turned)
	if (!D.Pivot.IsValid()) D.Pivot = Bs;
	// (looted before, in this game: built open and empty)
	if (const URDGameInstance* GI = URDGameInstance::Of(this); GI && GI->WildKilled.Contains(Key))
	{
		D.Alpha = D.Target = 1.f;
		if (D.Pivot.Get() != Bs) D.Pivot->SetRelativeRotation(D.Closed * FQuat(D.Axis, FMath::DegreesToRadians(D.Angle)));
		if (USceneComponent* P2 = D.Pivot2.Get()) P2->SetRelativeRotation(D.Closed2 * FQuat(D.Axis, FMath::DegreesToRadians(D.Angle2)));
	}
	C->Doors.Add(D);
	if (Rec) ++Rec->Boxes;
	return true;
}

void ARDDungeonGenerator::OpenWildBox(ARDWildChunk* C, int32 Index)
{
	if (!C || !C->Doors.IsValidIndex(Index) || !PlayerCombat) return;
	ARDWildChunk::FDoor& D = C->Doors[Index];
	if (!D.bBox || D.Target > 0.5f) return;
	D.Target = 1.f;
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (GI && GI->WildKilled.Contains(D.Key)) { PlayerCombat->ShowMessage(TEXT("Empty: nothing inside")); return; }
	if (GI) GI->WildKilled.AddUnique(D.Key);
	++WildBoxesOpened;
	// (its things: a roll of its kind's list by its key, never a stream the play draws from; one at least)
	TArray<FString> Lines; D.Loot.ParseIntoArray(Lines, TEXT(";"), true);
	FRandomStream R((int32)HashCombine(GetTypeHash(D.Key), 0xF00Du ^ (uint32)(IsWildReady() ? Wild->Seed : 0u)));
	TArray<FName> Got = RollWildThings(Lines, R);
	if (Got.Num() == 0)
		for (const FString& L : Lines)
		{
			FString Nm, Rest;
			if (!L.Split(TEXT("|"), &Nm, &Rest)) Nm = L;
			if (FindItem(FName(*Nm)) >= 0) { Got.Add(FName(*Nm)); break; }
		}
	if (Got.Num() == 0) { PlayerCombat->ShowMessage(TEXT("Empty: nothing inside")); return; }
	TArray<FName> Order; TMap<FName, int32> N;
	for (const FName& G : Got) { if (!N.Contains(G)) Order.Add(G); N.FindOrAdd(G)++; }
	for (const FName& G : Order) PlayerCombat->AddItem(G, N[G]);
	LastFound = Order[0]; LastFoundList = Order; LastFoundTime = GetWorld()->GetTimeSeconds(); ItemsFound += Order.Num();
	WildBoxThings += Got.Num();
	PlaySoundAt(TEXT("Player.Loot"), D.At);
	UE_LOG(LogRDWildFarm11, Log, TEXT("RDWILDBOX %s (%lld): %s"), *D.Kind.ToString(), D.Key, *FString::JoinBy(Got, TEXT(", "), [](const FName& X) { return X.ToString(); }));
}

void ARDDungeonGenerator::WildClearRect(ARDWildChunk* C, const FVector& Mid, float Yaw, const FVector2D& Half, FRDWildFarmRec* Rec)
{
	if (!C || !C->Ground) return;
	const FTransform Gt = C->Ground->GetComponentTransform();
	const FVector Lc = Gt.InverseTransformPosition(Mid);
	ARDWildChunk::FClear Cl; Cl.C = FVector2D(Lc.X, Lc.Y); Cl.H = Half; Cl.Yaw = Yaw - Gt.Rotator().Yaw;
	C->Clears.Add(Cl);
	// (the plants already in it taken out; the near grass to come leaves it out (IsClear))
	const float Rr = FMath::Max(Half.X, Half.Y) * 1.5f;
	const FBox Wb(Mid - FVector(Rr, Rr, 3000.f), Mid + FVector(Rr, Rr, 3000.f));
	auto Clean = [&](UHierarchicalInstancedStaticMeshComponent* Hm)
	{
		if (!Hm) return;
		TArray<int32> Out;
		for (const int32 I : Hm->GetInstancesOverlappingBox(Wb, true))
		{
			FTransform It; if (!Hm->GetInstanceTransform(I, It, true)) continue;
			if (Cl.Contains(Gt.InverseTransformPosition(It.GetLocation()))) Out.Add(I);
		}
		if (Out.Num() > 0) Hm->RemoveInstances(Out);
	};
	for (UHierarchicalInstancedStaticMeshComponent* Hm : C->Foliage) Clean(Hm);
	for (UHierarchicalInstancedStaticMeshComponent* Hm : C->NearFoliage) Clean(Hm);
}

// ================================================================================================ a building of the town's kit
void ARDDungeonGenerator::WildKitBuilding(ARDWildChunk* C, const FRDWildPlace& P, const FRDFarmPart& Pt, int32 PartIx, FRDWildFarmRec& Rec)
{
	if (!C || !C->Ground) return;
	FRandomStream R((int32)FRDWildWorld::Hash(P.Id, 500 + PartIx, Wild->Seed));
	const float M = TileSize, WH = 300.f;
	static const TCHAR* Styles[] = { TEXT("Timber"), TEXT("Stone"), TEXT("Thatch") };
	const FString St = Styles[FMath::Clamp(Pt.Style, 0, 2)];
	auto Pn = [&](const TCHAR* Part) { return FName(*FString::Printf(TEXT("Town.%s_%s"), *St, Part)); };
	const FName Kind = Pt.Kind;
	const int32 Nx = FMath::Clamp(Pt.Nx, 2, 6), Ny = FMath::Clamp(Pt.Ny, 2, 8);
	const float Hx = Nx * M * 0.5f, Hy = Ny * M * 0.5f;
	const float Yaw = P.Yaw + Pt.Yaw;
	const FVector2D C2 = RDWF11At(P, Pt.U, Pt.V);
	const FRotator Rot(0.f, Yaw, 0.f);
	// ---- the ground: the floor over its highest point under the walls, the plinth down to its lowest a little round them
	float Gmax = -1e9f, Gmin = 1e9f;
	for (int32 I = 0; I <= 4; ++I)
		for (int32 J = 0; J <= 4; ++J)
		{
			const FVector In = FVector(C2.X * 100.0, C2.Y * 100.0, 0.0) + Rot.RotateVector(FVector(-Hx + 2.f * Hx * I / 4.f, -Hy + 2.f * Hy * J / 4.f, 0.f));
			const FVector Ou = FVector(C2.X * 100.0, C2.Y * 100.0, 0.0) + Rot.RotateVector(FVector((-Hx - 60.f) + 2.f * (Hx + 60.f) * I / 4.f, (-Hy - 60.f) + 2.f * (Hy + 60.f) * J / 4.f, 0.f));
			Gmax = FMath::Max(Gmax, WildGroundZ(In));
			Gmin = FMath::Min(Gmin, WildGroundZ(Ou));
		}
	const float Base = Gmax + 4.f;
	const FVector O(C2.X * 100.0, C2.Y * 100.0, Base);
	auto At = [&](float X, float Y, float Z) { return O + Rot.RotateVector(FVector(X, Y, 0.f)) + FVector(0.f, 0.f, Z); };
	auto Keep = [&](UActorComponent* X) { if (X) Rec.Comps.Add(X); };
	auto Mesh = [&](UStaticMesh* Ms, const FTransform& W, bool bCollide, UMaterialInterface* Mat, bool bUnseen = false) -> UStaticMeshComponent*
	{
		if (!Ms) return nullptr;
		UStaticMeshComponent* Sm = NewObject<UStaticMeshComponent>(C);
		Sm->SetStaticMesh(Ms);
		Sm->SetupAttachment(C->Ground);
		if (Mat) Sm->SetMaterial(0, Mat);
		if (!bCollide) Sm->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		if (bUnseen) Sm->SetHiddenInGame(true);
		Sm->RegisterComponent();
		Sm->SetWorldTransform(W);
		C->PlaceProps.Add(Sm);
		Keep(Sm);
		++Rec.Props;
		return Sm;
	};
	auto Put = [&](FName Name, const FTransform& T) -> UStaticMeshComponent*
	{
		const FRDPiece* Pc = Piece(Name);
		return Pc && Pc->Mesh ? Mesh(Pc->Mesh, Pc->Adjust * T, Pc->bCollision, Pc->Material) : nullptr;
	};
	// (a hidden box over a piece's whole bounds: a window's sill stands out of the wall where its collision does not reach)
	auto BoundsCollider = [&](FName Name, const FTransform& T)
	{
		const FRDPiece* Pc = Piece(Name);
		if (!Pc || !Pc->Mesh) return;
		const FTransform L = Pc->Adjust * T;
		const FBox B = Pc->Mesh->GetBoundingBox();
		Mesh(RDWF11Cube(), FTransform(L.GetRotation(), L.TransformPosition(B.GetCenter()), B.GetSize() * L.GetScale3D() / 100.f), true, nullptr, true);
	};
	// a wall piece: its middle on the wall's line, its outside +X
	auto WallT = [&](const FVector2D& Pl, const FVector2D& Out, float Z)
	{
		return FTransform(FRotator(0.f, Yaw + FMath::RadiansToDegrees(FMath::Atan2(Out.Y, Out.X)), 0.f), At(Pl.X, Pl.Y, Z));
	};
	const int32 Box0 = Rec.Boxes;
	int32 Furniture = 0;
	// ---- the plinth: stone under the whole floor, from the floor down to the ground's lowest (the floor's collision)
	{
		const float Z0 = Gmin - 30.f;
		Mesh(RDWF11Cube(), FTransform(Rot, FVector(O.X, O.Y, (Base + Z0) * 0.5f), FVector((2.f * Hx + 10.f) / 100.f, (2.f * Hy + 10.f) / 100.f, (Base - Z0) / 100.f)), true, WildPlinthMaterial);
	}
	// ---- the floor
	for (int32 I = 0; I < Nx; ++I)
		for (int32 J = 0; J < Ny; ++J)
			Put(Pn(TEXT("Floor")), FTransform(FRotator(0.f, Yaw + 90.f * R.RandRange(0, 3), 0.f), At((I + 0.5f) * M - Hx, (J + 0.5f) * M - Hy, 2.f)));
	// ---- the walls: the doorway in the +X wall (on a barn, off the stall's half), windows in a house's
	const int32 DoorK = Kind == TEXT("barn") ? FMath::Max(0, (Ny - 1) / 2) : Ny / 2;
	const float DoorY = (DoorK + 0.5f) * M - Hy;
	const bool bWindows = Kind == TEXT("house");
	struct FSide { FVector2D Out; int32 N; };
	const FSide Sides[4] = { { FVector2D(1, 0), Ny }, { FVector2D(-1, 0), Ny }, { FVector2D(0, 1), Nx }, { FVector2D(0, -1), Nx } };
	for (int32 Si = 0; Si < 4; ++Si)
		for (int32 K = 0; K < Sides[Si].N; ++K)
		{
			const FSide& Sd = Sides[Si];
			const FVector2D Pl = Si < 2 ? FVector2D(Sd.Out.X * Hx, (K + 0.5f) * M - Hy) : FVector2D((K + 0.5f) * M - Hx, Sd.Out.Y * Hy);
			const bool bDoor = Si == 0 && K == DoorK;
			FName Nm = bDoor ? Pn(TEXT("Doorway")) : Pn(TEXT("Wall"));
			if (!bDoor && bWindows && R.FRand() < (Si == 0 ? 0.5f : 0.35f)) Nm = Pn(TEXT("WallWindow"));
			const FTransform T = WallT(Pl, Sd.Out, 2.f);
			Put(Nm, T);
			if (!bDoor && Nm != Pn(TEXT("Wall"))) BoundsCollider(Nm, T);
		}
	for (int32 Cx = -1; Cx <= 1; Cx += 2)
		for (int32 Cy = -1; Cy <= 1; Cy += 2)
			Put(Pn(TEXT("Pillar")), FTransform(Rot, At(Cx * Hx, Cy * Hy, 2.f)));
	// ---- the roof: a gable along the longer side (the town's)
	{
		const float Top = 2.f + WH;
		const bool bRidgeY = Ny >= Nx;
		const FVector2D A = bRidgeY ? FVector2D(0, 1) : FVector2D(1, 0), Cc = bRidgeY ? FVector2D(1, 0) : FVector2D(0, 1);
		const int32 NAlong = bRidgeY ? Ny : Nx, Span = bRidgeY ? Nx : Ny;
		const float HAlong = NAlong * M * 0.5f, HAcross = Span * M * 0.5f;
		for (int32 Al = 0; Al < NAlong; ++Al)
			for (int32 Ac = 0; Ac < Span; ++Ac)
			{
				const bool bLow = Ac < Span / 2;
				const int32 Level = bLow ? Ac : Span - 1 - Ac;
				const FVector2D Out = Cc * (bLow ? -1.f : 1.f);
				const FVector2D Pl = A * ((Al + 0.5f) * M - HAlong) + Cc * ((Ac + 0.5f) * M - HAcross);
				const FTransform T = WallT(Pl, Out, Top + Level * M);
				if (Span % 2 == 1 && Ac == Span / 2) { Put(Pn(TEXT("Roof")), WallT(Pl, Cc * -1.f, Top + Level * M)); Put(Pn(TEXT("Roof")), WallT(Pl, Cc, Top + Level * M)); continue; }
				Put(Pn(TEXT("Roof")), T);
				if (Level == 0) Put(Pn(TEXT("RoofTrim")), T);
				const FVector2D Yp(-Out.Y, Out.X);
				const float Dy = FVector2D::DotProduct(Yp, A);
				if (Al == NAlong - 1) Put(Pn(Dy > 0.f ? TEXT("RoofEndL") : TEXT("RoofEndR")), T);
				if (Al == 0) Put(Pn(Dy > 0.f ? TEXT("RoofEndR") : TEXT("RoofEndL")), T);
			}
		for (int32 End = 0; End < 2; ++End)
		{
			const FVector2D Out = A * (End == 0 ? -1.f : 1.f);
			const FVector2D Yp(-Out.Y, Out.X);
			const FVector2D P0 = A * ((End == 0 ? 0 : NAlong) * M - HAlong);
			for (int32 Lv = 0; Lv < Span / 2; ++Lv)
			{
				const float Half = (Span * 0.5f - Lv) * M;
				Put(Pn(TEXT("GableNeg")), WallT(P0 + Yp * (-Half + M * 0.5f), Out, Top + Lv * M));
				Put(Pn(TEXT("GablePos")), WallT(P0 + Yp * (Half - M * 0.5f), Out, Top + Lv * M));
				for (float Yv = -Half + M; Yv < Half - M + 1.f; Yv += M) Put(Pn(TEXT("Wall")), WallT(P0 + Yp * Yv, Out, Top + Lv * M));
			}
		}
	}
	// ---- its door: the kit's leaf on its hinge (the town's AddTownDoor: the leaf spans +Y from its pivot, the pivot turned half
	// round so its +X points into the building), a chunk door F opens
	const FVector Outw = Rot.RotateVector(FVector(1.f, 0.f, 0.f));
	const FVector DoorMid = At(Hx, DoorY, 0.f);
	if (const FRDPiece* Dp = Piece(Pn(TEXT("Door"))); Dp && Dp->Mesh)
	{
		const FVector HingeW = DoorMid + FVector(0.f, 0.f, 2.f) + Rot.RotateVector(FVector(Dp->Hinge.X, Dp->Hinge.Y, 0.f)) + FVector(0.f, 0.f, Dp->Hinge.Z);
		USceneComponent* Bd = NewObject<USceneComponent>(C);
		Bd->SetMobility(EComponentMobility::Movable);
		Bd->SetupAttachment(C->Ground);
		Bd->RegisterComponent();
		Bd->SetWorldTransform(FTransform(FRotator(0.f, Yaw + 180.f, 0.f), HingeW));
		USceneComponent* Pv = NewObject<USceneComponent>(C);
		Pv->SetMobility(EComponentMobility::Movable);
		Pv->SetupAttachment(Bd);
		Pv->RegisterComponent();
		UStaticMeshComponent* Leaf = NewObject<UStaticMeshComponent>(C);
		Leaf->SetMobility(EComponentMobility::Movable);
		Leaf->SetStaticMesh(Dp->Mesh);
		Leaf->SetupAttachment(Pv);
		Leaf->SetRelativeTransform(Dp->Adjust);
		if (Dp->Material) Leaf->SetMaterial(0, Dp->Material);
		Leaf->RegisterComponent();
		C->PlaceProps.Add(Leaf);
		Keep(Bd); Keep(Pv); Keep(Leaf);
		ARDWildChunk::FDoor Dr;
		Dr.Pivot = Pv; Dr.At = DoorMid; Dr.Out = Outw;
		// (in the pivot's frame the leaf runs +Y and the outside is -X: the quarter turn that lays it along the outward way)
		Dr.OutYaw = FVector::DotProduct(FRotator(0.f, 90.f, 0.f).RotateVector(FVector(0.f, 1.f, 0.f)), FVector(-1.f, 0.f, 0.f)) > 0.f ? 90.f : -90.f;
		Dr.OpenYaw = Dr.OutYaw;
		C->Doors.Add(Dr);
	}
	// (steps before the door where the ground outside lies lower than the sill)
	{
		const float Drop = Base - WildGroundZ(DoorMid + Outw * 70.f);
		if (Drop > 30.f)
			for (int32 K = 0, N = FMath::Min(FMath::CeilToInt(Drop / 28.f), 6); K < N; ++K)
			{
				const float Top = Base - Drop * K / N, Depth = 42.f;
				const FVector W = DoorMid + Outw * (Depth * (K + 0.5f) + 8.f);
				const float Z0 = WildGroundZ(W) - 20.f;
				Mesh(RDWF11Cube(), FTransform(Rot, FVector(W.X, W.Y, (Top + Z0) * 0.5f), FVector(Depth / 100.f, 2.f, FMath::Max(Top - Z0, 5.f) / 100.f)), true, WildPlinthMaterial);
			}
	}
	// ---- its inside, by its kind (the room inside the walls; the door's wall +X, the back wall -X; a piece's front is its +X)
	const FVector2D Mn(-Hx + 30.f, -Hy + 30.f), Mx(Hx - 30.f, Hy - 30.f);
	const float Wd = Mx.X - Mn.X;
	int32 BoxN = PartIx * 8;
	auto PutAt = [&](FName Name, float X, float Y, float YawL) -> bool
	{
		const FRDPiece* Pc = Piece(Name);
		if (!Pc || !Pc->Mesh) return false;
		if (Mesh(Pc->Mesh, Pc->Adjust * FTransform(FRotator(0.f, Yaw + YawL, 0.f), At(X, Y, 2.f)), Pc->bCollision, Pc->Material)) { ++Furniture; return true; }
		return false;
	};
	auto WildPiece = [&](const FString& Prefix, float X, float Y, float YawL, float Sink) -> bool
	{
		TArray<UStaticMesh*> Ms; WildPiecesOf(Prefix, Ms);
		if (Ms.Num() == 0) return false;
		UStaticMesh* Ms0 = Ms[R.RandRange(0, Ms.Num() - 1)];
		const float* Ks = WildPieceScale.Find(FName(*Ms0->GetName()));
		const float Sc = Ks ? *Ks : 1.f;
		const FQuat Q = FRotator(0.f, Yaw + YawL, 0.f).Quaternion();
		const FBox B = Ms0->GetBoundingBox();
		const FVector Off = Q.RotateVector(FVector(B.GetCenter().X, B.GetCenter().Y, 0.0) * Sc) + FVector(0.0, 0.0, B.Min.Z * Sc);
		if (Mesh(Ms0, FTransform(Q, At(X, Y, 2.f - Sink * Sc) - Off, FVector(Sc)), true, nullptr)) { ++Furniture; return true; }
		return false;
	};
	auto PutBox = [&](FName Name, float X, float Y, float YawL, const TCHAR* LootKind) -> bool
	{
		const FRDPiece* Pc = Piece(Name);
		if (!Pc || !Pc->Mesh) return false;
		const FString* L = FarmLoot.Find(FName(LootKind));
		const FName Kn = Name == TEXT("Wardrobe") ? FName(TEXT("wardrobe")) : Name == TEXT("Chest") ? FName(TEXT("chest")) : Name == TEXT("Barrel") ? FName(TEXT("barrel")) : FName(TEXT("crate"));
		if (AddWildBox(C, Name, FTransform(FRotator(0.f, Yaw + YawL, 0.f), At(X, Y, 1.f)), Kn, RDWF11Key(P.Id, BoxN++), L ? *L : FString(), &Rec)) { ++Furniture; return true; }
		return false;
	};
	auto Lamp = [&](float Candelas)
	{
		UPointLightComponent* Lt = NewObject<UPointLightComponent>(C);
		Lt->SetupAttachment(C->Ground);
		Lt->SetIntensityUnits(ELightUnits::Candelas);
		Lt->SetIntensity(Candelas);
		Lt->SetAttenuationRadius(FMath::Max(Hx, Hy) * 1.6f);
		Lt->SetLightColor(FLinearColor(1.f, 0.72f, 0.45f));
		Lt->SetCastShadows(false);
		Lt->RegisterComponent();
		Lt->SetWorldLocation(At(0.f, 0.f, 260.f));
		Keep(Lt);
	};
	if (Kind == TEXT("house"))
	{
		if (const FRDPiece* Fp = Piece(TEXT("Fireplace")))
		{
			PutAt(TEXT("Fireplace"), Mn.X + Fp->Size.X * 0.5f + 2.f, 0.f, 0.f);
			if (WildFireFx)
				if (UNiagaraComponent* Fx = UNiagaraFunctionLibrary::SpawnSystemAttached(WildFireFx, C->Ground, NAME_None, At(Mn.X + 45.f, 0.f, 22.f) - C->Ground->GetComponentLocation(), FRotator::ZeroRotator, FVector(0.7f), EAttachLocation::KeepRelativeOffset, true, ENCPoolMethod::None))
					Keep(Fx);
		}
		float BedY = Mx.Y - 70.f;
		if (const FRDPiece* Bp = Piece(TEXT("Bed")))
		{
			BedY = Mx.Y - Bp->Size.Y * 0.5f - 20.f;
			PutAt(TEXT("Bed"), Mn.X + Bp->Size.X * 0.5f + 6.f, BedY, 0.f);
			if (const FRDPiece* Cp = Piece(TEXT("Chest"))) PutBox(TEXT("Chest"), Mn.X + Bp->Size.X + 14.f + Cp->Size.X * 0.5f, BedY, 0.f, TEXT("chest"));
		}
		const float TableY = Mn.Y + (Mx.Y - Mn.Y) * 0.3f;
		PutAt(TEXT("TableLong"), Mn.X + Wd * 0.55f, TableY, 0.f);
		if (const FRDPiece* Tp = Piece(TEXT("TableLong")))
			for (const float Sd : { -1.f, 1.f }) PutAt(TEXT("Bench"), Mn.X + Wd * 0.55f + Sd * (Tp->Size.X * 0.5f + 30.f), TableY, 0.f);
		PutBox(TEXT("Barrel"), Mn.X + 45.f, Mn.Y + 45.f, R.FRandRange(0.f, 360.f), TEXT("barrel"));
		PutBox(TEXT("Crate"), Mn.X + 45.f, Mn.Y + 125.f, 0.f, TEXT("crate"));
		if (Hy >= 450.f) PutBox(TEXT("Wardrobe"), Mn.X + Wd * 0.62f, Mx.Y - 32.f, -90.f, TEXT("wardrobe"));
		Lamp(30.f);
	}
	else
	{
		// (a barn, a shed, a coop, a granary: hay along the back wall, its stores by the front corners, a lamp)
		const TCHAR* LootKind = Kind == TEXT("barn") ? TEXT("barn") : Kind == TEXT("granary") ? TEXT("granary") : Kind == TEXT("coop") ? TEXT("coop") : TEXT("shed");
		// (five things at least in each: the stores at the front and back corners of its -Y side, hay (sacks of it in a granary))
		// (a barn's hay along its back wall; a small building's in its back +Y corner, the middle kept free to walk (the first test
		// stood her on a coop's hay, 44 cm up))
		const bool bBarn = Kind == TEXT("barn");
		const int32 NHay = bBarn ? FMath::Max(1, Ny / 2) : 1;
		for (int32 K = 0; K < NHay; ++K)
			WildPiece(TEXT("hay"), Mn.X + 70.f, bBarn ? Mn.Y + 230.f + (K + 0.5f) * (Mx.Y - Mn.Y - 230.f) / NHay : Mx.Y - 80.f, R.FRandRange(0.f, 360.f), 5.f);
		PutBox(TEXT("Crate"), Mx.X - 60.f, Mn.Y + 50.f, 180.f, LootKind);
		PutBox(TEXT("Barrel"), Mx.X - 60.f, Mn.Y + 130.f, R.FRandRange(0.f, 360.f), LootKind);
		PutBox(TEXT("Barrel"), Mn.X + 55.f, Mn.Y + 55.f, R.FRandRange(0.f, 360.f), LootKind);
		PutBox(TEXT("Crate"), Mn.X + 55.f, Mn.Y + 140.f, 0.f, LootKind);
		if (Kind == TEXT("shed")) WildPiece(TEXT("woodpile"), Mn.X + 60.f, (Mn.Y + Mx.Y) * 0.5f, 90.f, 3.f);
		// (a trough by a barn's side wall; the yard's cart, scaled for the yard, filled a barn and held its hay up)
		else if (bBarn) WildPiece(TEXT("trough"), (Mn.X + Mx.X) * 0.5f, Mn.Y + 70.f, 0.f, 5.f);
		Lamp(Kind == TEXT("barn") ? 22.f : 14.f);
	}
	// ---- animals inside (a barn's stalls, a coop's hens): a fence across the far half, its gate by the front; the floor's height
	// for their ground
	const TArray<TPair<FString, int32>> In = RDWF11Animals(Pt.Animals);
	if (In.Num() > 0)
	{
		const float Ys = Kind == TEXT("barn") ? FMath::Max(DoorY + 110.f, 0.f) : Mn.Y;      // (the stall's near side, off the doorway)
		const float Xg = Mx.X - 140.f;                                                       // (its front fence, the way in kept before it)
		const FVector2D SMin(Mn.X + 20.f, Ys + 20.f), SMax(Xg - 20.f, Mx.Y - 20.f);
		if (SMax.X - SMin.X > 120.f && SMax.Y - SMin.Y > 120.f)
		{
			TArray<UStaticMesh*> Fm; WildPiecesOf(TEXT("paddock"), Fm);
			if (Fm.Num() == 0) WildPiecesOf(TEXT("fence"), Fm);
			UStaticMesh* F = Fm.Num() > 0 ? Fm[0] : nullptr;
			auto Line = [&](const FVector2D& A, const FVector2D& B)
			{
				if (!F) return;
				const double Len = FVector2D::Distance(A, B);
				const FBox Bx = F->GetBoundingBox();
				const bool bAlongY = Bx.GetSize().Y > Bx.GetSize().X;
				const float* Ks = WildPieceScale.Find(FName(*F->GetName()));
				const float Sc = (Ks ? *Ks : 1.f) * 0.8f;
				const double Piece_ = FMath::Max((bAlongY ? Bx.GetSize().Y : Bx.GetSize().X) * Sc, 50.0);
				const int32 N = FMath::Max(1, FMath::RoundToInt(Len / Piece_));
				const FVector2D Dir = (B - A).GetSafeNormal();
				const float Yl = FMath::RadiansToDegrees(FMath::Atan2(Dir.Y, Dir.X)) - (bAlongY ? 90.f : 0.f);
				const FVector Sc3 = bAlongY ? FVector(Sc, Sc * Len / (N * Piece_), Sc) : FVector(Sc * Len / (N * Piece_), Sc, Sc);
				const FQuat Q = FRotator(0.f, Yaw + Yl, 0.f).Quaternion();
				for (int32 K = 0; K < N; ++K)
				{
					const FVector2D Cp = A + Dir * ((K + 0.5) * Len / N);
					const FVector Off = Q.RotateVector(FVector(Bx.GetCenter().X, Bx.GetCenter().Y, 0.0) * Sc3) + FVector(0.0, 0.0, Bx.Min.Z * Sc3.Z);
					Mesh(F, FTransform(Q, At((float)Cp.X, (float)Cp.Y, 2.f) - Off, Sc3), true, nullptr);
				}
			};
			// (a barn's stall fenced off, its gate's gap of 1.3 m; a coop's hens keep to its back without a fence across its small
			// room (the first test's walk to a coop's middle met its fence))
			if (Kind == TEXT("barn"))
			{
				const float Gm = (Ys + Mx.Y) * 0.5f;
				Line(FVector2D(Mn.X, Ys), FVector2D(Xg, Ys));
				Line(FVector2D(Xg, Ys), FVector2D(Xg, Gm - 65.f)); Line(FVector2D(Xg, Gm + 65.f), FVector2D(Xg, Mx.Y));
			}
			const FVector2D Ctr = (SMin + SMax) * 0.5f, Half = (SMax - SMin) * 0.5f;
			const FVector PenAt = At(Ctr.X, Ctr.Y, 2.f);
			for (const TPair<FString, int32>& A : In)
			{
				int32 Kd = -1;
				for (int32 K = 0; K < TownAnimals.Num(); ++K) if (TownAnimals[K].Mesh && TownAnimals[K].Name.ToString().Equals(A.Key, ESearchCase::IgnoreCase)) { Kd = K; break; }
				if (Kd < 0) continue;
				const FVector2D H = (Half - FVector2D(TownAnimals[Kd].HalfSize.X, TownAnimals[Kd].HalfSize.X)).ComponentMax(FVector2D(5.f, 5.f));
				FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
				for (int32 K = 0, Nn = FMath::Min(A.Value, WildFarmAnimalsMax); K < Nn; ++K)
				{
					const FVector Av = PenAt + Rot.RotateVector(FVector(R.FRandRange(-H.X, H.X), R.FRandRange(-H.Y, H.Y), 0.f));
					ARDTownAnimal* An = GetWorld()->SpawnActor<ARDTownAnimal>(ARDTownAnimal::StaticClass(), FTransform(FRotator(0, R.FRandRange(0.f, 360.f), 0), Av), Sp);
					if (!An) continue;
					// (its ground the floor's height: a flat grid)
					An->bWildGround = true; An->PenYaw = Yaw;
					An->GroundGrid.Init(Base + 2.f, 4); An->GroundO = FVector2D(PenAt.X - 1000.f, PenAt.Y - 1000.f); An->GroundStep = 2000.f; An->GroundN = 2;
					An->Init(this, Kd, -1, PenAt, Half, HashCombine((uint32)P.Id, (uint32)(PartIx * 97 + K) * 2654435761u));
					C->Props.Add(An);
					Rec.Animals.Add(An);
					Rec.AnimalPens.Add(FVector4(PenAt.X, PenAt.Y, Half.X, Half.Y));
				}
			}
		}
	}
	// ---- its record: a house of the chunk (the houses' lines), its ground kept clear of plants
	ARDWildChunk::FHouse Hs; Hs.C = O; Hs.H = FVector2D(Hx - 30.f, Hy - 30.f); Hs.Yaw = Yaw; Hs.Doors = 1; Hs.Furniture = Furniture; Hs.bLit = true; Hs.FloorZ = Base + 2.f;
	Hs.Of = FString::Printf(TEXT("kit:%s"), *Kind.ToString());
	C->Houses.Add(Hs);
	WildClearRect(C, O, Yaw, FVector2D(Hx + 40.f, Hy + 40.f), &Rec);
	++Rec.Buildings;
	WildFarmBldLines.Add(FString::Printf(TEXT("fbld|%d|%s|%.0f|%.0f|%.0f|%d|%d|%.1f|%.0f|%.0f|%d|%d"), P.Id, *Kind.ToString(), O.X, O.Y, Base + 2.f, Nx, Ny, Yaw, DoorMid.X, DoorMid.Y, Furniture, Rec.Boxes - Box0));
}

// ================================================================================================ a farmstead of a design
void ARDDungeonGenerator::SpawnWildFarm11(ARDWildChunk* C, const FRDWildPlace& P, int32 Design)
{
	if (!C || !FarmDesigns.IsValidIndex(Design)) return;
	const FRDFarmDesign& Dz = FarmDesigns[Design];
	FRandomStream R((int32)FRDWildWorld::Hash(P.Id, 78, Wild->Seed));
	const FVector O = C->GetActorLocation();
	// (the buildings' lines of farms gone with their chunks, and of this one built before, dropped)
	{
		TSet<int32> Alive;
		for (const FRDWildFarmRec& F : WildFarms) if (F.Chunk.IsValid() && F.Id != P.Id) Alive.Add(F.Id);
		WildFarmBldLines.RemoveAll([&](const FString& L) { TArray<FString> F; L.ParseIntoArray(F, TEXT("|")); return F.Num() < 2 || !Alive.Contains(FCString::Atoi(*F[1])); });
	}
	FRDWildFarmRec Rec; Rec.Id = P.Id; Rec.Name = P.Name; Rec.At = P.At; Rec.Yaw = P.Yaw; Rec.Chunk = C; Rec.Design = Design;
	Rec.Door0 = C->Doors.Num(); Rec.House0 = C->Houses.Num(); Rec.Clear0 = C->Clears.Num();
	auto Keep = [&](UActorComponent* X) { if (X) Rec.Comps.Add(X); };
	auto ScaleOf = [&](const UStaticMesh* M) { const float* Ks = WildPieceScale.Find(FName(*M->GetName())); return Ks ? *Ks : 1.f; };
	auto Comp = [&](UStaticMesh* M, const FTransform& T, bool bCollide) -> UStaticMeshComponent*
	{
		UStaticMeshComponent* Sm = NewObject<UStaticMeshComponent>(C);
		Sm->SetStaticMesh(M);
		Sm->SetupAttachment(C->Ground);
		Sm->SetRelativeTransform(T);
		if (!bCollide) Sm->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Sm->RegisterComponent();
		C->PlaceProps.Add(Sm);
		Keep(Sm);
		++Rec.Props;
		return Sm;
	};
	auto Pick = [&](const FString& Prefix, const FString& Or) -> UStaticMesh*
	{
		TArray<UStaticMesh*> Ms; WildPiecesOf(Prefix, Ms);
		if (Ms.Num() == 0 && !Or.IsEmpty()) WildPiecesOf(Or, Ms);
		return Ms.Num() > 0 ? Ms[R.RandRange(0, Ms.Num() - 1)] : nullptr;
	};
	// one piece at a point of the farm's frame (metres): its box's middle and bottom on the point, sunk (cm at its scale)
	auto PutMesh = [&](UStaticMesh* M, float U, float V, float Yaw, float Sink = 10.f, bool bCollide = true) -> UStaticMeshComponent*
	{
		if (!M) return nullptr;
		const float Sc = ScaleOf(M);
		const FVector2D At = RDWF11At(P, U, V);
		const float Z = WildGroundZ(FVector(At.X * 100.0, At.Y * 100.0, 0.0));
		const FQuat Q = FRotator(0.f, P.Yaw + Yaw, 0.f).Quaternion();
		const FVector Mid = M->GetBoundingBox().GetCenter();
		const FVector Off = Q.RotateVector(FVector(Mid.X, Mid.Y, 0.0) * Sc) + FVector(0.0, 0.0, M->GetBoundingBox().Min.Z * Sc);
		return Comp(M, FTransform(Q, FVector(At.X * 100.0, At.Y * 100.0, Z - Sink * Sc) - Off - O, FVector(Sc)), bCollide);
	};
	// a fence from A to B (the farm's frame, metres) of one mesh, end to end, stretched a little to fill it
	auto Fence = [&](const FVector2D& A, const FVector2D& B, UStaticMesh* M, float ScMul = 1.f)
	{
		if (!M) return;
		const FVector2D Wa = RDWF11At(P, A.X, A.Y), Wb = RDWF11At(P, B.X, B.Y);
		const double Len = FVector2D::Distance(Wa, Wb) * 100.0;
		if (Len < 30.0) return;
		const FBox Bx = M->GetBoundingBox();
		const FVector Ext = Bx.GetSize(), Mid = Bx.GetCenter();
		const bool bAlongY = Ext.Y > Ext.X;
		const float Sc = ScaleOf(M) * ScMul;
		const double Piece_ = FMath::Max((bAlongY ? Ext.Y : Ext.X) * Sc, 50.0);
		const int32 N = FMath::Max(1, FMath::RoundToInt(Len / Piece_));
		const double Stretch = Len / (N * Piece_);
		const FVector2D Dir = (Wb - Wa).GetSafeNormal();
		const float Yaw = FMath::RadiansToDegrees(FMath::Atan2(Dir.Y, Dir.X)) - (bAlongY ? 90.f : 0.f);
		const FVector Sc3 = bAlongY ? FVector(Sc, Sc * Stretch, Sc) : FVector(Sc * Stretch, Sc, Sc);
		const FQuat Q = FRotator(0.f, Yaw, 0.f).Quaternion();
		for (int32 K = 0; K < N; ++K)
		{
			const FVector2D Cp = Wa + Dir * ((K + 0.5) * Len / N / 100.0);
			const float Z = WildGroundZ(FVector(Cp.X * 100.0, Cp.Y * 100.0, 0.0));
			const FVector Off = Q.RotateVector(FVector(Mid.X, Mid.Y, 0.0) * Sc3) + FVector(0.0, 0.0, Bx.Min.Z * Sc3.Z);
			Comp(M, FTransform(Q, FVector(Cp.X * 100.0, Cp.Y * 100.0, Z - 8.f * Sc) - Off - O, Sc3), true);
		}
	};
	// (the side of a rectangle that faces the farm's middle: its gate's; 0 -U, 1 +U, 2 -V, 3 +V)
	auto GateSide = [](float U, float V) { return FMath::Abs(U) > FMath::Abs(V) ? (U > 0.f ? 0 : 1) : (V > 0.f ? 2 : 3); };
	// a fenced rectangle (middle u, v; half sizes, metres); the sides in Mask drawn, a gate's gap in the side Gate
	auto PenRect = [&](float U, float V, float Hu, float Hv, float Gap, int32 Gate, uint32 Mask, UStaticMesh* M, float ScMul = 1.f)
	{
		const FVector2D A(U - Hu, V - Hv), B(U + Hu, V - Hv), Cc(U + Hu, V + Hv), D(U - Hu, V + Hv);
		const FVector2D Ends[4][2] = { { A, D }, { B, Cc }, { A, B }, { D, Cc } };
		for (int32 S = 0; S < 4; ++S)
		{
			if (!(Mask & (1u << S))) continue;
			const FVector2D S0 = Ends[S][0], S1 = Ends[S][1];
			if (S == Gate)
			{
				const FVector2D Mm = (S0 + S1) * 0.5f, Dd = (S1 - S0).GetSafeNormal();
				Fence(S0, Mm - Dd * (Gap * 0.5f), M, ScMul); Fence(Mm + Dd * (Gap * 0.5f), S1, M, ScMul);
				++Rec.FenceGap;
			}
			else Fence(S0, S1, M, ScMul);
		}
	};
	// a round pen: ten segments, the one facing the farm's middle its gate
	auto PenRound = [&](float U, float V, float Rr, UStaticMesh* M)
	{
		const float Face = FMath::RadiansToDegrees(FMath::Atan2(-V, -U));
		for (int32 K = 0; K < 10; ++K)
		{
			const float A0 = Face + 18.f + 36.f * K, A1 = A0 + 36.f;
			if (K == 9) { ++Rec.FenceGap; continue; }
			Fence(FVector2D(U + Rr * FMath::Cos(FMath::DegreesToRadians(A0)), V + Rr * FMath::Sin(FMath::DegreesToRadians(A0))),
			      FVector2D(U + Rr * FMath::Cos(FMath::DegreesToRadians(A1)), V + Rr * FMath::Sin(FMath::DegreesToRadians(A1))), M);
		}
	};
	// animals of one kind in a rectangle (the farm's frame), on the ground under it (a height grid taken once)
	auto Animals = [&](const FString& KindName, int32 Count, float U, float V, float Hu, float Hv, uint32 Salt)
	{
		int32 Kd = -1;
		for (int32 K = 0; K < TownAnimals.Num(); ++K) if (TownAnimals[K].Mesh && TownAnimals[K].Name.ToString().Equals(KindName, ESearchCase::IgnoreCase)) { Kd = K; break; }
		if (Kd < 0) return;
		const FRDTownAnimalDef& D = TownAnimals[Kd];
		const int32 N = FMath::Clamp(Count, 1, WildFarmAnimalsMax);
		const FVector2D Mid = RDWF11At(P, U, V);
		const FVector PenAt(Mid.X * 100.0, Mid.Y * 100.0, WildGroundZ(FVector(Mid.X * 100.0, Mid.Y * 100.0, 0.0)));
		const FVector2D Half(Hu * 100.f - 40.f, Hv * 100.f - 40.f);
		const FVector2D H = (Half - FVector2D(D.HalfSize.X, D.HalfSize.X)).ComponentMax(FVector2D(5.f, 5.f));
		if (Rec.PenHalf.IsZero()) { Rec.PenAt = PenAt; Rec.PenHalf = Half; Rec.PenYaw = P.Yaw; }
		const float Rg = FMath::Sqrt(FMath::Square(Hu) + FMath::Square(Hv)) * 100.f + 100.f;
		constexpr int32 Gn = 6;
		TArray<float> Grid; Grid.SetNumUninitialized(Gn * Gn);
		const FVector2D G0(PenAt.X - Rg, PenAt.Y - Rg); const float Gs = 2.f * Rg / (Gn - 1);
		for (int32 I = 0; I < Gn; ++I) for (int32 J = 0; J < Gn; ++J) Grid[I * Gn + J] = WildGroundZ(FVector(G0.X + I * Gs, G0.Y + J * Gs, 0.0));
		FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		for (int32 K = 0; K < N; ++K)
		{
			FVector At = PenAt + FRotator(0.f, P.Yaw, 0.f).RotateVector(FVector(R.FRandRange(-H.X, H.X), R.FRandRange(-H.Y, H.Y), 0.f));
			At.Z = WildGroundZ(At);
			ARDTownAnimal* A = GetWorld()->SpawnActor<ARDTownAnimal>(ARDTownAnimal::StaticClass(), FTransform(FRotator(0, R.FRandRange(0.f, 360.f), 0), At), Sp);
			if (!A) continue;
			A->bWildGround = true; A->PenYaw = P.Yaw;
			A->GroundGrid = Grid; A->GroundO = G0; A->GroundStep = Gs; A->GroundN = Gn;
			A->Init(this, Kd, -1, PenAt, Half, HashCombine((uint32)P.Id, Salt + (uint32)K * 2654435761u));
			C->Props.Add(A);
			Rec.Animals.Add(A);
			Rec.AnimalPens.Add(FVector4(PenAt.X, PenAt.Y, Half.X, Half.Y));
		}
	};
	// ---- the parts, in the design's order
	FVector2D PenGate = FVector2D(1e9f, 1e9f), WellAt = PenGate, HouseDoor = PenGate, BarnDoor = PenGate;
	float PenGateYaw = 0.f;
	for (int32 Pi = 0; Pi < Dz.Parts.Num(); ++Pi)
	{
		const FRDFarmPart& Pt = Dz.Parts[Pi];
		const FString K = Pt.Kind.ToString();
		if (K == TEXT("house") || K == TEXT("barn") || K == TEXT("shed") || K == TEXT("coop") || K == TEXT("granary"))
		{
			WildKitBuilding(C, P, Pt, Pi, Rec);
			// (where its door is, for the family's places)
			const float Hx = FMath::Clamp(Pt.Nx, 2, 6) * TileSize * 0.5f / 100.f;
			const FVector2D Door = FVector2D(Pt.U, Pt.V) + FVector2D(FMath::Cos(FMath::DegreesToRadians(Pt.Yaw)), FMath::Sin(FMath::DegreesToRadians(Pt.Yaw))) * (Hx + 1.8f);
			if (K == TEXT("house") && HouseDoor.X > 1e8f) HouseDoor = Door;
			if (K == TEXT("barn") && BarnDoor.X > 1e8f) BarnDoor = Door;
		}
		else if (K == TEXT("pen"))
		{
			UStaticMesh* M = Pick(TEXT("paddock"), TEXT("fence"));
			const TArray<TPair<FString, int32>> Ak = RDWF11Animals(Pt.Animals);
			if (Pt.Shape == 2)
			{
				// (round: the animals in the square inside it)
				PenRound(Pt.U, Pt.V, Pt.Hu, M);
				for (int32 J = 0; J < Ak.Num(); ++J) Animals(Ak[J].Key, Ak[J].Value, Pt.U, Pt.V, Pt.Hu * 0.68f, Pt.Hu * 0.68f, 11u + 31u * Pi + J);
			}
			else if (Pt.Shape == 1 && Ak.Num() >= 2)
			{
				// (two side by side along U, each its kind and its own gate; their middle fence once)
				const int32 G = GateSide(Pt.U, Pt.V);
				const int32 Gd = G < 2 ? 2 + (Pt.V > 0.f ? 0 : 1) : G;      // (a gate in each half's side toward the middle)
				PenRect(Pt.U - Pt.Hu * 0.5f, Pt.V, Pt.Hu * 0.5f, Pt.Hv, 2.2f, Gd, 0xF, M);
				PenRect(Pt.U + Pt.Hu * 0.5f, Pt.V, Pt.Hu * 0.5f, Pt.Hv, 2.2f, Gd, 0xF & ~1u, M);
				Animals(Ak[0].Key, Ak[0].Value, Pt.U - Pt.Hu * 0.5f, Pt.V, Pt.Hu * 0.5f, Pt.Hv, 11u + 31u * Pi);
				Animals(Ak[1].Key, Ak[1].Value, Pt.U + Pt.Hu * 0.5f, Pt.V, Pt.Hu * 0.5f, Pt.Hv, 12u + 31u * Pi);
			}
			else
			{
				PenRect(Pt.U, Pt.V, Pt.Hu, Pt.Hv, 2.4f, GateSide(Pt.U, Pt.V), 0xF, M);
				for (int32 J = 0; J < Ak.Num(); ++J) Animals(Ak[J].Key, Ak[J].Value, Pt.U, Pt.V, Pt.Hu, Pt.Hv, 11u + 31u * Pi + J);
			}
			if (PenGate.X > 1e8f)
			{
				const float Rr = Pt.Shape == 2 ? Pt.Hu : 0.f;
				const int32 G = GateSide(Pt.U, Pt.V);
				const FVector2D Gp = Pt.Shape == 2 ? FVector2D(Pt.U, Pt.V) - FVector2D(Pt.U, Pt.V).GetSafeNormal() * (Rr + 1.1f)
					: FVector2D(Pt.U, Pt.V) + (G == 0 ? FVector2D(-Pt.Hu - 1.1f, 0.f) : G == 1 ? FVector2D(Pt.Hu + 1.1f, 0.f) : G == 2 ? FVector2D(0.f, -Pt.Hv - 1.1f) : FVector2D(0.f, Pt.Hv + 1.1f));
				PenGate = Gp; PenGateYaw = FMath::RadiansToDegrees(FMath::Atan2(Pt.V - Gp.Y, Pt.U - Gp.X));
			}
		}
		else if (K == TEXT("garden"))
		{
			// (a low fence round beds of the town's crops (Town.CropN), its harvest by the gate (F))
			UStaticMesh* M = Pick(TEXT("paddock"), TEXT("fence"));
			const int32 G = GateSide(Pt.U, Pt.V);
			PenRect(Pt.U, Pt.V, Pt.Hu, Pt.Hv, 1.4f, G, 0xF, M, 0.7f);
			TArray<int32> Crops;
			for (const TCHAR Ch : Pt.Variant) if (Ch >= TEXT('1') && Ch <= TEXT('6')) Crops.AddUnique(Ch - TEXT('1'));
			if (Crops.Num() == 0) Crops.Add(0);
			FString Loot;
			const float Rows = FMath::Max(1, FMath::FloorToInt((Pt.Hv * 2.f - 0.8f) / 0.8f));
			for (int32 Ci = 0; Ci < Crops.Num(); ++Ci)
			{
				const FRDPiece* Cp = Piece(FName(*FString::Printf(TEXT("Town.Crop%d"), Crops[Ci] + 1)));
				if (!Cp || !Cp->Mesh) continue;
				UInstancedStaticMeshComponent* Is = NewObject<UInstancedStaticMeshComponent>(C);
				Is->SetStaticMesh(Cp->Mesh);
				if (Cp->Material) Is->SetMaterial(0, Cp->Material);
				Is->SetCollisionEnabled(ECollisionEnabled::NoCollision);
				Is->SetupAttachment(C->Ground);
				Is->RegisterComponent();
				Keep(Is);
				// (its rows: the bed's rows shared out among the crops)
				for (int32 Rw = 0; Rw < (int32)Rows; ++Rw)
				{
					if (Rw % Crops.Num() != Ci) continue;
					const float Vr = Pt.V - Pt.Hv + 0.6f + Rw * 0.8f;
					for (float Ur = Pt.U - Pt.Hu + 0.6f; Ur < Pt.U + Pt.Hu - 0.5f; Ur += 0.6f)
					{
						const FVector2D W = RDWF11At(P, Ur, Vr);
						const FVector Wp(W.X * 100.0, W.Y * 100.0, WildGroundZ(FVector(W.X * 100.0, W.Y * 100.0, 0.0)));
						Is->AddInstance(Cp->Adjust * FTransform(FRotator(0.f, R.FRandRange(0.f, 360.f), 0.f), Wp), true);
					}
				}
				if (TownCropItems.IsValidIndex(Crops[Ci]) && !TownCropItems[Crops[Ci]].IsNone())
					Loot += FString::Printf(TEXT("%s%s|2|3|1"), Loot.IsEmpty() ? TEXT("") : TEXT(";"), *TownCropItems[Crops[Ci]].ToString());
			}
			const FVector2D Mid = RDWF11At(P, Pt.U, Pt.V);
			WildClearRect(C, FVector(Mid.X * 100.0, Mid.Y * 100.0, WildGroundZ(FVector(Mid.X * 100.0, Mid.Y * 100.0, 0.0))), P.Yaw, FVector2D(Pt.Hu * 100.f, Pt.Hv * 100.f), &Rec);
			// (the harvest: F by the gate, outside it)
			const FVector2D Gp = FVector2D(Pt.U, Pt.V) + (G == 0 ? FVector2D(-Pt.Hu - 0.7f, 0.f) : G == 1 ? FVector2D(Pt.Hu + 0.7f, 0.f) : G == 2 ? FVector2D(0.f, -Pt.Hv - 0.7f) : FVector2D(0.f, Pt.Hv + 0.7f));
			const FVector2D Gw = RDWF11At(P, Gp.X, Gp.Y);
			const FVector GateW(Gw.X * 100.0, Gw.Y * 100.0, WildGroundZ(FVector(Gw.X * 100.0, Gw.Y * 100.0, 0.0)) + 40.f);
			AddWildBox(C, NAME_None, FTransform(FRotator(0.f, P.Yaw, 0.f), GateW), FName(TEXT("garden")), RDWF11Key(P.Id, 56 + (Pi & 7)), Loot, &Rec, &GateW);
		}
		else
		{
			// (a yard thing: the wild pieces of its name)
			const FString Or = K == TEXT("trough") ? FString(TEXT("hay")) : K == TEXT("woodpile") ? FString(TEXT("log")) : FString();
			const float Sink = K == TEXT("scarecrow") ? 15.f : K == TEXT("woodpile") ? 3.f : K == TEXT("trough") || K == TEXT("hay") ? 5.f : 10.f;
			if (PutMesh(Pick(K, Or), Pt.U, Pt.V, Pt.Yaw, Sink) && K == TEXT("well")) WellAt = FVector2D(Pt.U, Pt.V);
		}
	}
	Rec.Door1 = C->Doors.Num(); Rec.House1 = C->Houses.Num(); Rec.Clear1 = C->Clears.Num();
	// ---- the family (the old layout's): the farmer at a sown plot's edge, the farmwife at the first pen's gate, a farmhand before
	// the barn's door, a child by the well (or the house's door)
	TArray<int32> Men, Women, Kids;
	for (int32 I = 0; I < Townsfolk.Num(); ++I)
	{
		const FRDTownsfolkDef& Df = Townsfolk[I];
		if (!Df.Mesh || !Df.Town.IsEmpty()) continue;
		const FString Nm = Df.Name.ToString();
		if (Df.Role == ERDTownRole::Child) Kids.Add(I);
		else if (Df.Role == ERDTownRole::Townsfolk) (Nm.Contains(TEXT("woman")) ? Women : Men).Add(I);
	}
	FVector2D TendAt = RDWF11At(P, 36.f, 0.f); float TendYaw = P.Yaw;
	{
		const float Fw0 = Wild->FarmWeight(P.At.X, P.At.Y);
		for (int32 K = 0; K < 8; ++K)
		{
			const float A = FMath::DegreesToRadians(P.Yaw + 45.f * K);
			const FVector2D Dd(FMath::Cos(A), FMath::Sin(A));
			FRDWFarm Fm; Wild->FarmAt(P.At.X + Dd.X * 38.0, P.At.Y + Dd.Y * 38.0, Fw0, Fm);
			if (Fm.Kind == 2 && Fm.Crop >= 0 && Fm.Field > 0.6f) { TendAt = P.At + Dd * 35.5f; TendYaw = FMath::RadiansToDegrees(A); break; }
		}
	}
	auto Facing = [&](const FVector2D& From, const FVector2D& To) { return FMath::RadiansToDegrees(FMath::Atan2(To.Y - From.Y, To.X - From.X)); };
	const FVector2D Yard = RDWF11At(P, 0.f, 0.f);
	auto Local = [&](const FVector2D& UV, const FVector2D& Or) { return UV.X > 1e8f ? Or : RDWF11At(P, UV.X, UV.Y); };
	const FVector2D WifeAt = Local(PenGate, RDWF11At(P, -6.f, -6.f));
	const FVector2D HandAt = Local(BarnDoor, RDWF11At(P, 6.f, 6.f));
	const FVector2D KidAt = WellAt.X < 1e8f ? RDWF11At(P, WellAt.X + 1.4f, WellAt.Y + 1.2f) : Local(HouseDoor + FVector2D(1.5f, 1.5f), RDWF11At(P, 4.f, -4.f));
	struct FWho { const TCHAR* Role; int32 Body; FVector2D At; float Yaw; const TCHAR* Work; const TCHAR* Prop; };
	const FWho Family[] = {
		{ TEXT("farmer"), 0, TendAt, TendYaw, TEXT("Tend"), nullptr },
		{ TEXT("farmwife"), 1, WifeAt, PenGate.X < 1e8f ? P.Yaw + PenGateYaw : Facing(WifeAt, Yard), TEXT("Scatter"), TEXT("Bowl") },
		{ TEXT("farmhand"), 0, HandAt, Facing(HandAt, Yard), TEXT("Talk"), nullptr },
		{ TEXT("child"), 2, KidAt, Facing(KidAt, Yard), nullptr, nullptr } };
	const bool bHand = R.FRand() < 0.67f, bKid = R.FRand() < 0.5f;
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	for (int32 K = 0; K < UE_ARRAY_COUNT(Family); ++K)
	{
		const FWho& Wh = Family[K];
		if ((K == 2 && !bHand) || (K == 3 && !bKid)) continue;
		const TArray<int32>& Pool = Wh.Body == 2 ? Kids : Wh.Body == 1 ? Women : Men;
		if (Pool.Num() == 0) continue;
		const int32 D = Pool[(int32)(FRDWildWorld::Hash(P.Id, 300 + K, Wild->Seed) % (uint32)Pool.Num())];
		const FVector At(Wh.At.X * 100.0, Wh.At.Y * 100.0, WildGroundZ(FVector(Wh.At.X * 100.0, Wh.At.Y * 100.0, 0.0)) + 92.f);
		ARDTownsfolk* T = GetWorld()->SpawnActor<ARDTownsfolk>(ARDTownsfolk::StaticClass(), FTransform(FRotator(0, Wh.Yaw, 0), At), Sp);
		if (!T) continue;
		T->Init(this, nullptr, D, At, Wh.Yaw, 0.f, HashCombine((uint32)P.Id, (uint32)K * 7919u));
		T->SetTitle(FString::Printf(TEXT("%s of %s"), Wh.Role, *P.Name));
		if (Wh.Work) T->SetStandWork(Wh.Work, Wh.Prop ? FName(Wh.Prop) : NAME_None);
		for (const FString& L : WildFarmLines)
		{
			FString Who, Line;
			if (!L.Split(TEXT("|"), &Who, &Line)) continue;
			if (Who == Wh.Role || Who == TEXT("any")) T->OwnLines.Add(Line.Replace(TEXT("{farm}"), *P.Name));
		}
		C->Props.Add(T);
		Rec.Folk.Add(T);
	}
	WildFarms.RemoveAll([](const FRDWildFarmRec& F) { return !F.Chunk.IsValid(); });
	WildFarms.RemoveAll([&](const FRDWildFarmRec& F) { return F.Id == P.Id; });
	UE_LOG(LogRDWildFarm11, Log, TEXT("RDWILD farmstead %s (%d) design %d (%s): %d buildings, %d containers, %d props, %d animals, %d folk"), *P.Name, P.Id, Design, *Dz.Name.ToString(),
		Rec.Buildings, Rec.Boxes, Rec.Props, Rec.Animals.Num(), Rec.Folk.Num());
	WildFarms.Add(MoveTemp(Rec));
}

// ================================================================================================ tests
int32 ARDDungeonGenerator::SpawnFarmDesignAt(int32 Design, float Xm, float Ym, float Yaw)
{
	if (!IsWildReady() || !FarmDesigns.IsValidIndex(Design)) return 0;
	// (the loaded chunk the point is in)
	ARDWildChunk* C = nullptr;
	for (const auto& Kv : WildChunks)
	{
		ARDWildChunk* K = Kv.Value;
		if (!IsValid(K) || K->bMaking) continue;
		const FVector L = K->GetActorLocation();
		if (Xm * 100.f >= L.X && Xm * 100.f < L.X + WildChunkM * 100.f && Ym * 100.f >= L.Y && Ym * 100.f < L.Y + WildChunkM * 100.f) { C = K; break; }
	}
	if (!C) return 0;
	FRDWildPlace P; P.Id = FRDWildWorld::FarmIdBase + 0x0FFFFF - Design; P.Kind = TEXT("farmstead"); P.Name = FString::Printf(TEXT("Test Farm %d"), Design);
	P.At = FVector2D(Xm, Ym); P.Yaw = Yaw;
	RemoveWildFarm(P.Id);
	SpawnWildFarm11(C, P, Design);
	return P.Id;
}

bool ARDDungeonGenerator::RemoveWildFarm(int32 Id)
{
	const int32 I = WildFarms.IndexOfByPredicate([&](const FRDWildFarmRec& F) { return F.Id == Id; });
	if (I < 0) return false;
	FRDWildFarmRec& F = WildFarms[I];
	if (ARDWildChunk* C = F.Chunk.Get(); IsValid(C))
	{
		// (its ranges in the chunk's lists, last first: they were added together, nothing of another farm between them)
		if (F.Clear1 <= C->Clears.Num() && F.Clear0 < F.Clear1) C->Clears.RemoveAt(F.Clear0, F.Clear1 - F.Clear0);
		if (F.House1 <= C->Houses.Num() && F.House0 < F.House1) C->Houses.RemoveAt(F.House0, F.House1 - F.House0);
		if (F.Door1 <= C->Doors.Num() && F.Door0 < F.Door1) C->Doors.RemoveAt(F.Door0, F.Door1 - F.Door0);
		for (const TWeakObjectPtr<UActorComponent>& W : F.Comps) if (UActorComponent* X = W.Get()) X->DestroyComponent();
		C->PlaceProps.RemoveAll([](const TObjectPtr<UStaticMeshComponent>& S) { return !IsValid(S) || S->IsBeingDestroyed(); });
		for (const TWeakObjectPtr<ARDTownAnimal>& A : F.Animals) if (A.IsValid()) { C->Props.Remove(A.Get()); A->Destroy(); }
		for (const TWeakObjectPtr<ARDTownsfolk>& T : F.Folk) if (T.IsValid()) { C->Props.Remove(T.Get()); T->Destroy(); }
	}
	const FString Pre = FString::Printf(TEXT("fbld|%d|"), Id);
	WildFarmBldLines.RemoveAll([&](const FString& L) { return L.StartsWith(Pre); });
	WildFarms.RemoveAt(I);
	return true;
}

TArray<FString> ARDDungeonGenerator::GetWildBoxLines() const
{
	TArray<FString> Out;
	const URDGameInstance* GI = URDGameInstance::Of(this);
	for (const auto& Kv : WildChunks)
	{
		const ARDWildChunk* C = Kv.Value;
		if (!IsValid(C)) continue;
		for (const ARDWildChunk::FDoor& D : C->Doors)
			if (D.bBox) Out.Add(FString::Printf(TEXT("box|%s|%.0f|%.0f|%.0f|%.2f|%d|%lld"), *D.Kind.ToString(), D.At.X, D.At.Y, D.At.Z, D.Alpha, GI && GI->WildKilled.Contains(D.Key) ? 1 : 0, D.Key));
	}
	for (const FRDWildFarmRec& F : WildFarms) if (F.Chunk.IsValid()) Out.Add(FString::Printf(TEXT("farm11|%d|%d|%d|%d"), F.Id, F.Design, F.Buildings, F.Boxes));
	for (const FString& L : WildFarmBldLines) Out.Add(L);
	return Out;
}
