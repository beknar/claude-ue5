#include "RD/RDSection.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDMonster.h"
#include "ProceduralMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "TimerManager.h"
#include "HAL/PlatformTime.h"

DEFINE_LOG_CATEGORY_STATIC(LogRandomDungeon, Log, All);

static const FName RDInteractiveTag(TEXT("RDInteractive"));
static const FName RDFlickerTag(TEXT("RDFlicker"));
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
	Rooms.Reset(); Corrs.Reset(); DoorEdges.Reset(); Portals.Reset();
	Type.Init(0, N * N); Owner.Init(-1, N * N); Blocked.Init(0, N * N);
	const bool bStart = Generator->IsStartSection(Coord);
	// room kinds: weighted, a few per section capped
	struct FW { ERDRoomKind K; float W; int32 MinSize; int32 MaxSize; int32 Cap; };
	const FW Kinds[] = {
		{ ERDRoomKind::Barracks, 9, 6, 10, 6 }, { ERDRoomKind::Prison, 7, 7, 10, 5 }, { ERDRoomKind::Torture, 4, 5, 8, 3 },
		{ ERDRoomKind::Storeroom, 9, 5, 9, 7 }, { ERDRoomKind::Armory, 6, 5, 9, 4 }, { ERDRoomKind::Kitchen, 5, 6, 10, 3 },
		{ ERDRoomKind::Library, 5, 6, 10, 3 }, { ERDRoomKind::Chapel, 4, 7, 10, 2 }, { ERDRoomKind::Crypt, 6, 6, 10, 4 },
		{ ERDRoomKind::Treasury, 3, 5, 7, 2 }, { ERDRoomKind::GuardRoom, 8, 5, 7, 6 }, { ERDRoomKind::Forge, 4, 6, 9, 2 },
		{ ERDRoomKind::Hall, 2, 9, 10, 1 }, { ERDRoomKind::Junction, 10, 3, 3, 12 } };
	TMap<ERDRoomKind, int32> Used;
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
				const int32 W = R.RandRange(MinS, MaxS), H = R.RandRange(MinS, MaxS);
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
}

// ------------------------------------------------------------------------------------------------ instancing helpers
void ARDSection::AddPiece(FName Name, const FTransform& T, bool bForceNoCollision)
{
	if (!bBuildStatic) return;
	const FRDPiece* P = Generator->Piece(Name);
	if (!P) return;
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
		return;
	}
	if (!P->Mesh) return;
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
}

void ARDSection::AddPieceAt(FName Name, const FVector& Loc, float Yaw, float Scale, bool bForceNoCollision)
{
	AddPiece(Name, FTransform(FRotator(0, Yaw, 0), Loc, FVector(Scale)), bForceNoCollision);
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

void ARDSection::AddTorch(const FVector& WallPoint, float InYaw, float Candelas, bool bLit)
{
	// sconce on the wall (piece frame: back on the wall at x = 0, flame above its origin at FlameOffset = Hinge)
	const FRDPiece* P = Generator->Piece(TEXT("Torch"));
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
static float PickSign(const FVector& Axis, const FVector& Tip, const FVector& Want)
{
	const FVector P = FQuat(Axis, FMath::DegreesToRadians(60.f)).RotateVector(Tip);
	return FVector::DotProduct(P - Tip, Want) >= 0.f ? 1.f : -1.f;
}

void ARDSection::AddDoor(FIntPoint RoomTile, FIntPoint OutTile, int32 RoomIndex)
{
	if (!bBuildInteractive) return;
	// two leaves hinged on the doorway jambs (piece "DoorLeaf": leaf spans +Y from its origin, Hinge.Y = opening half width)
	const FRDPiece* P = Generator->Piece(TEXT("DoorLeaf"));
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
	const FRDPiece* P = Generator->Piece(TEXT("CellDoor"));
	if (!P) return;
	USceneComponent* Pv = AddPivot(RootComponent, FTransform(FRotator(0, Yaw, 0), HingeWorld - GetActorLocation()));
	UStaticMeshComponent* M = AddMesh(Pv, P->Mesh, P->Adjust, true);
	FMover Mv; Mv.Pivot = Pv; Mv.Parts = { M }; Mv.Closed = Pv->GetRelativeRotation().Quaternion(); Mv.bDoor = true; Mv.bCell = true; Mv.Kind = TEXT("cell door");
	Mv.LeafSign = 1.f;
	Mv.Center = HingeWorld + FRotator(0, Yaw, 0).RotateVector(FVector(0, P->Size.Y * 0.5f, 100));
	Mv.Normal = FRotator(0, Yaw, 0).RotateVector(FVector(1, 0, 0));
	Doors.Add(Mv);
}

void ARDSection::AddContainer(FName Name, const FVector& Loc, float Yaw, const FString& Kind)
{
	const FRDPiece* P = Generator->Piece(Name);
	if (!P) return;
	MarkBlocked(Loc, Yaw, FVector2D(P->Size.X, P->Size.Y));
	if (!bBuildInteractive || !P->Moving) return;
	USceneComponent* Base = AddPivot(RootComponent, FTransform(FRotator(0, Yaw, 0), Loc - GetActorLocation()));
	AddMesh(Base, P->Mesh, P->Adjust, true);
	// moving part(s): pivot at the hinge (piece frame); the part keeps the piece Adjust relative to the hinge
	auto AddMoving = [&](UStaticMesh* Mesh, const FVector& Hinge, bool bVerticalAxis, int32 Partner)
	{
		USceneComponent* Hp = AddPivot(Base, FTransform(Hinge));
		FTransform Rel = P->Adjust; Rel.AddToTranslation(-Hinge);
		UStaticMeshComponent* M = AddMesh(Hp, Mesh, Rel, true);
		FMover Mv; Mv.Pivot = Hp; Mv.Parts = { M }; Mv.Kind = Kind; Mv.Partner = Partner;
		if (bVerticalAxis)
		{
			// wardrobe door: swings out toward the front (+X)
			Mv.Axis = FVector::UpVector;
			const FBox B = Mesh->GetBoundingBox().TransformBy(Rel);
			Mv.OpenAngle = 100.f * PickSign(Mv.Axis, FVector(0, B.GetCenter().Y, 0), FVector(1, 0, 0));
		}
		else
		{
			// lid: hinge axis along Y at the back, lifts up
			Mv.Axis = FVector::RightVector;
			const FBox B = Mesh->GetBoundingBox().TransformBy(Rel);
			Mv.OpenAngle = 100.f * PickSign(Mv.Axis, FVector(B.GetCenter().X, 0, 0), FVector::UpVector);
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
	ShellFloor.Reset(); ShellWall.Reset();
	for (const FRoom& Rm : Rooms) { ShellFloor.Add(FloorFor(Rm.Kind, R)); ShellWall.Add(WallFor(Rm.Kind, R)); }
}

void ARDSection::ShellColumn(FRandomStream& R, int32 X)
{
	const float S = Generator->TileSize;
	const TArray<FName>& RoomFloor = ShellFloor;
	const TArray<FName>& RoomWall = ShellWall;
	auto Stack = [this](FName Name, const FVector& Base, float Yaw, float Z0, float Z1)
	{
		const FRDPiece* P = Generator->Piece(Name);
		if (!P) return;
		const float H = FMath::Max(P->Size.Z - 2.f, 50.f);
		for (float Z = Z0; Z < Z1 - 5.f; Z += H) AddPieceAt(Name, Base + FVector(0, 0, Z), Yaw);
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
			const float Hgt = bLow ? Generator->CorridorHeight : Generator->RoomHeight;
			const FVector C = TileWorld(T);
			// floor (occasional damaged / variant tiles), ceiling
			FName F = bRoom ? RoomFloor[O] : FName(TEXT("Floor_Corr"));
			if (R.FRand() < 0.12f && Generator->Piece(FName(*(F.ToString() + TEXT("_Alt"))))) F = FName(*(F.ToString() + TEXT("_Alt")));
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
				if (bWall)
				{
					const FName WN = bRoom ? RoomWall[O] : FName(TEXT("Wall_Corr"));
					Stack(WN, Edge, Yaw, 0.f, Hgt);
				}
				else if (bDoorway)
				{
					AddPieceAt(TEXT("Doorway"), Edge, Yaw);
					const FRDPiece* D = Generator->Piece(TEXT("Doorway"));
					Stack(RoomWall[O], Edge, Yaw, D ? D->Size.Z - 2.f : 300.f, Hgt);
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
		if (Rm.Kind == ERDRoomKind::Junction) continue;
		const FVector A = TileWorld(Rm.Min) - FVector(S * 0.5f, S * 0.5f, 0), Bv = TileWorld(Rm.Max - FIntPoint(1, 1)) + FVector(S * 0.5f, S * 0.5f, 0);
		const FVector Cn[4] = { FVector(A.X, A.Y, 0), FVector(Bv.X, A.Y, 0), FVector(Bv.X, Bv.Y, 0), FVector(A.X, Bv.Y, 0) };
		for (int32 I = 0; I < 4; ++I)
		{
			const FVector In_ = ((A + Bv) * 0.5f - Cn[I]).GetSafeNormal2D();
			const FVector P = Cn[I] + In_ * 25.f;
			const FRDPiece* Pc = Generator->Piece(TEXT("CornerColumn"));
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
	for (int32 I = 0; I < Cnt; ++I)
	{
		const float A = Cnt > 1 ? A0 + Step * I : (A0 + A1) * 0.5f;
		if (FMath::Abs(A - Lane) < S * 0.5f + Clear) continue;
		Out.Add(bAlongY ? FVector(Wl, A, 0) : FVector(A, Wl, 0));
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
			const FRDPiece* P = Generator->Piece(Nm);
			if (!P) continue;
			const float Yaw = InwardYaw(Side);
			const FVector Pos = W + FRotator(0, Yaw, 0).RotateVector(FVector(P->Size.X * 0.5f + 32.f, 0, 0));
			if (!LaneFree(Rm, Pos, FMath::Max(P->Size.X, P->Size.Y) * 0.5f)) continue;
			if (bContainers && P->Moving) AddContainer(Nm, Pos, Yaw, Nm.ToString().ToLower());
			else { AddPieceAt(Nm, Pos, Yaw); MarkBlocked(Pos, Yaw, FVector2D(P->Size.X, P->Size.Y)); }
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
	auto Center = [&](FName Nm, const FVector& P, float Yaw, bool bBlock = true, bool bLaneToo = false)
	{
		const FRDPiece* Pc = Generator->Piece(Nm);
		if (!Pc) return;
		AddPieceAt(Nm, P, Yaw);
		if (bBlock && Pc->bCollision) MarkBlocked(P, Yaw, FVector2D(Pc->Size.X, Pc->Size.Y), bLaneToo);
	};
	auto Hang = [&](FName Nm, const FVector& P, float Yaw)   // from the ceiling (piece bottom at z 0: placed at ceiling - height)
	{
		const FRDPiece* Pc = Generator->Piece(Nm);
		if (Pc) AddPieceAt(Nm, P + FVector(0, 0, RH - Pc->Size.Z), Yaw, 1.f, true);
	};
	auto Candles = [&](const FVector& P, float Cd)
	{
		AddPieceAt(TEXT("Candles"), P, R.FRandRange(0, 360), 1.f, true);
		AddEffect(TEXT("CandleFire"), P + FVector(0, 0, 18), 1.f);
		AddLight(P + FVector(0, 0, 45), FLinearColor(1.f, 0.62f, 0.32f), Cd, 700.f, false, 0.12f);
	};
	auto TableSet = [&](const FVector& Q, float Yaw, FName Table, FName Seat, bool bCandles)
	{
		const FRDPiece* T = Generator->Piece(Table);
		if (!T) return;
		Center(Table, Q, Yaw);
		const FRotator Rt(0, Yaw, 0);
		const FRDPiece* St = Generator->Piece(Seat);
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
			if (!Rm.bDoorSide[Far]) { Center(TEXT("Dais"), Dais, DaisYaw, true, true); const FRDPiece* D = Generator->Piece(TEXT("Dais")); Center(TEXT("Throne"), Dais + FVector(0, 0, D ? D->Size.Z : 0), DaisYaw, true, true); }
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
			const FRDPiece* Bz = Generator->Piece(TEXT("Brazier"));
			const float Hz = Bz ? Bz->Size.Z : 110.f;
			AddEffect(TEXT("BrazierFire"), Cn + FVector(0, 0, Hz - 10.f), 1.f);
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
				const FRDPiece* Bd = Generator->Piece(TEXT("Bed"));
				if (!Bd) break;
				const FVector P = W + FRotator(0, Yaw, 0).RotateVector(FVector(Bd->Size.X * 0.5f + 32.f, 0, 0));
				if (!LaneFree(Rm, P, Bd->Size.Y * 0.5f) || R.FRand() < 0.15f) continue;
				Center(TEXT("Bed"), P, Yaw);
				if (R.FRand() < 0.6f)
				{
					const FRDPiece* Ch = Generator->Piece(TEXT("Chest"));
					const FVector Cp = P + FRotator(0, Yaw, 0).RotateVector(FVector(Bd->Size.X * 0.5f + (Ch ? Ch->Size.X * 0.5f : 30.f) + 10.f, 0, 0));
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
			for (const FVector& W : WallSlots(Rm, Side, S, 160.f, S * 0.5f))
			{
				// cell: the tile against the wall (W is the wall point at the tile middle)
				const FVector Front = W + Rt.RotateVector(FVector(Depth, 0, 0));
				const FVector Inner = W + Rt.RotateVector(FVector(Depth * 0.5f, 0, 0));
				if (!LaneFree(Rm, Inner, S * 0.5f - 10.f)) continue;
				// grating across the cell front (piece runs along Y), cell door in its middle as a separate leaf
				// (the bars have no usable collision of their own: invisible blockers stand in for them)
				if (R.FRand() < 0.5f)
				{
					AddPieceAt(TEXT("CellFrame"), Front, Yaw);
					AddPieceAt(TEXT("CellBlockHalf"), Front, Yaw);
					const FRDPiece* Cd = Generator->Piece(TEXT("CellDoor"));
					if (Cd) AddCellDoor(Front + Rt.RotateVector(FVector(0, Cd->Size.Y * 0.5f, 0)), Yaw + 180.f, Cd->Size.Y);
				}
				else { AddPieceAt(TEXT("Grating"), Front, Yaw); AddPieceAt(TEXT("CellBlock"), Front, Yaw); }
				AddPieceAt(TEXT("HayPile"), Inner + Rt.RotateVector(FVector(-30, R.FRandRange(-60, 60), 0)), R.FRandRange(0, 360), 1.f, true);
				if (R.FRand() < 0.5f) AddPieceAt(TEXT("Bones"), Inner + Rt.RotateVector(FVector(20, R.FRandRange(-80, 80), 0)), R.FRandRange(0, 360), 1.f, true);
				AddPieceAt(TEXT("Shackles"), W + Rt.RotateVector(FVector(6, 0, 160)), Yaw, 1.f, true);
				const FIntPoint T = WorldToLocal(Inner);
				if (In(T)) Blocked[Idx(T)] = 1;
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
			const FRDPiece* Bp = Generator->Piece(TEXT("Brazier"));
			const float Hz = Bp ? Bp->Size.Z : 110.f;
			AddEffect(TEXT("BrazierFire"), P + FVector(0, 0, Hz - 10.f), 1.f);
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
			const FRDPiece* T = Generator->Piece(TEXT("TableLong"));
			if (!T) continue;
			const FRotator Rt(0, Yaw, 0);
			for (int32 K = 0; K < 4; ++K)
			{
				const FName Wpn = K % 3 == 0 ? TEXT("SwordFlat") : K % 3 == 1 ? TEXT("AxeFlat") : TEXT("SpearFlat");
				const FVector P = Q + Rt.RotateVector(FVector(R.FRandRange(-15, 15), (K - 1.5f) * T->Size.Y * 0.22f, T->Size.Z));
				AddPieceAt(Wpn, P, Yaw + 90.f + R.FRandRange(-8, 8), 1.f, true);
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
			const FRDPiece* Fp = Generator->Piece(TEXT("Fireplace"));
			if (Fp)
			{
				const FVector P = Wall + Rt.RotateVector(FVector(Fp->Size.X * 0.5f + 30.f, 0, 0));
				Center(TEXT("Fireplace"), P, Yaw, true, true);      // (on the lane at a wall without a door: block it)
				AddEffect(TEXT("HearthFire"), P + Rt.RotateVector(FVector(0, 0, 0)) + FVector(0, 0, 30), 1.2f);
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
			const FRDPiece* D = Generator->Piece(TEXT("Desk"));
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
		const FRDPiece* Al = Generator->Piece(TEXT("Altar"));
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
			const FRDPiece* Pd = Generator->Piece(TEXT("Pedestal"));
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
		const FRDPiece* Fg = Generator->Piece(TEXT("Forge"));
		if (Fg)
		{
			const FVector P = Wall + Rt.RotateVector(FVector(Fg->Size.X * 0.5f + 35.f, 0, 0));
			Center(TEXT("Forge"), P, Yaw, true, true);
			AddEffect(TEXT("BrazierFire"), P + FVector(0, 0, Fg->Size.Z * 0.55f), 1.2f);
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
			const FRDPiece* P = Generator->Piece(Nm);
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
			else if (U < 0.3f) { const FRDPiece* Ch = Generator->Piece(TEXT("Chain")); if (Ch) AddPieceAt(TEXT("Chain"), TileWorld(T) + Rt.RotateVector(FVector(-90, 0, 0)) + FVector(0, 0, Generator->CorridorHeight - Ch->Size.Z), R.FRandRange(0, 360), 1.f, true); }
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
	NumInstances = 0; NumLights = 0; NextRoom = 0; NextCorr = 0; GenTicks = 0; FurnishMs = 0.0;
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
		CollectFlicker();
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

void ARDSection::ActivateForPlay()
{
	if (!Generator) return;
	// same plan as the editor build (same seed); only the interactive part is instantiated
	bBuildStatic = false; bBuildInteractive = true;
	ClearInteractive();
	const int32 Inst = NumInstances, Lights = NumLights;
	FRandomStream R(Seed);
	Plan(R);
	BuildShell(R);
	AddDoors();
	for (int32 RI = 0; RI < Rooms.Num(); ++RI) Furnish(R, RI);
	bNoBlock = true;
	for (int32 CI = 0; CI < Corrs.Num(); ++CI) DecorateCorridor(R, CI);
	bNoBlock = false;
	NumInstances = Inst; NumLights = Lights;
	bBuildStatic = true;
	FRandomStream RM(Seed ^ 0x5f3759df);
	SpawnMonsters(RM);
	RegisterMap();
	CollectFlicker();
	UE_LOG(LogRandomDungeon, Log, TEXT("RDSECTION (%d,%d) activated for play: %d rooms, %d doors, %d containers, %d monsters"), Coord.X, Coord.Y, Rooms.Num(), Doors.Num(), Containers.Num(), SpawnedMonsters.Num());
}

void ARDSection::SpawnMonsters(FRandomStream& R)
{
	UWorld* W = GetWorld();
	if (!W || !W->IsGameWorld() || Generator->Monsters.Num() == 0) return;
	float WSum = 0.f; for (const FRDMonsterDef& D : Generator->Monsters) if (D.Mesh) WSum += D.Weight;
	if (WSum <= 0.f) return;
	const FVector Start = Generator->GetStartRoomCenter();
	for (int32 RI = 0; RI < Rooms.Num(); ++RI)
	{
		const FRoom& Rm = Rooms[RI];
		if (Rm.Kind == ERDRoomKind::Junction || R.FRand() >= Generator->MonsterCoverage) continue;
		// a free tile of the room (not where the player starts)
		TArray<FIntPoint> Free;
		for (int32 X = Rm.Min.X; X < Rm.Max.X; ++X) for (int32 Y = Rm.Min.Y; Y < Rm.Max.Y; ++Y) if (IsWalkable(FIntPoint(X, Y))) Free.Add(FIntPoint(X, Y));
		if (Free.Num() == 0) continue;
		const FIntPoint T = Free[R.RandRange(0, Free.Num() - 1)];
		const FVector P = TileWorld(T);
		if (FVector::Dist2D(P, Start) < 1500.f) continue;
		float U = R.FRand() * WSum; const FRDMonsterDef* Def = nullptr;
		for (const FRDMonsterDef& D : Generator->Monsters) { if (!D.Mesh) continue; U -= D.Weight; if (U <= 0.f) { Def = &D; break; } }
		if (!Def) Def = &Generator->Monsters.Last();
		FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
		ARDMonster* M = W->SpawnActor<ARDMonster>(ARDMonster::StaticClass(), FTransform(FRotator(0, R.FRandRange(0, 360), 0), P + FVector(0, 0, Def->CapsuleHalfHeight + 5.f)), Sp);
		if (!M) continue;
		M->Setup(this, *Def, R.RandHelper(1 << 30));
		SpawnedMonsters.Add(M);
	}
}

FRDSectionMap ARDSection::BuildMapData() const
{
	FRDSectionMap M; M.Coord = Coord; M.bStart = Generator && Generator->IsStartSection(Coord);
	const FIntPoint G0 = Generator ? Generator->SectionMinTile(Coord) : FIntPoint::ZeroValue;
	for (const FRoom& Rm : Rooms)
	{
		FRDMapRect Rc; Rc.Min = G0 + Rm.Min; Rc.Max = G0 + Rm.Max; Rc.Kind = Rm.Kind; Rc.bCorridor = Rm.Kind == ERDRoomKind::Junction;
		M.Rects.Add(Rc);
	}
	for (const FCorr& C : Corrs)
	{
		FRDMapRect Rc; Rc.Min = G0 + C.Min; Rc.Max = G0 + C.Max; Rc.bCorridor = true;
		M.Rects.Add(Rc);
	}
	for (int32 I = 0; I < Doors.Num(); I += 1)
		if (Doors[I].TileA.X >= 0 && (Doors[I].Partner < 0 || Doors[I].Partner > I)) M.Doors.Add(FVector2D(Doors[I].Center.X, Doors[I].Center.Y));
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
	Set(M, Target);
	if (Doors.IsValidIndex(M.Partner)) Set(Doors[M.Partner], Target);
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
	M.Target = M.Target > 0.5f ? 0.f : 1.f;
	if (Containers.IsValidIndex(M.Partner)) Containers[M.Partner].Target = M.Target;
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
	APawn* Pawn = UGameplayStatics::GetPlayerPawn(this, 0);
	const FVector PL = Pawn ? Pawn->GetActorLocation() : FVector(1e9);
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
		if (M.MonsterCloseTimer > 2.5f) { M.Target = 0.f; M.bByMonster = false; }
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
