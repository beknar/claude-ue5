// The user's list of 2026-11-22 (docs/improvements16.txt, "the city of heaven"; the plan docs/improvements16_plan.md), its twentieth
// phase, Heaven's storeys:
// - every home, office block and wide trade of two storeys or more gets floors between its storeys, a stair core at a back corner and
//   a lift (a platform she rides) to each floor and the roof;
// - the core: three strips of four tiles from the back wall (the two stair strips, the lift's strip), the flights switching back from
//   strip to strip, a landing tile at each end, the slab above each flight open with rails round it; the lift's shaft at the corner of
//   its strip, glass on its two inner sides, an invisible gate at each floor's entry while the platform is not there;
// - each upper storey furnished as its building's kind (desks and shelves in an office, a flat's bed, sofa, table, kitchen and media
//   wall in a home, shelves and tables in a trade), batched as the building's interior (hidden unless seen, the seventh phase);
// - its own random streams (each building's seed): the plan's streams and what is placed from them are unchanged.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDHeaven20, Log, All);

static const FIntPoint RDH20Dir4[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };
static const FName RDLiftTag20(TEXT("HeavenLift20"));

// (the storeys' surfaces over the section's floor: the ground's Modern.Floor at 2 has its top at 4; a slab at 2 + 300 k, its top at
// 4 + 300 k, its underside at 300 k - 28; the roof at 2 + 300 N, 24 thick)
static float RDH20Floor(int32 K) { return 4.f + 300.f * K; }
static float RDH20Roof(int32 N) { return 26.f + 300.f * N; }

// ------------------------------------------------------------------------------------------------ the core's place
bool ARDSection::HeavenCorePlan20(int32 BI)
{
	const FTownBld& B = TownBlds[BI];
	const float M = Generator->TileSize;
	const int32 Nx = B.DoorSide < 2 ? B.Max.X - B.Min.X : B.Max.Y - B.Min.Y;
	const int32 Ny = B.DoorSide < 2 ? B.Max.Y - B.Min.Y : B.Max.X - B.Min.X;
	const bool bKind = B.Kind == TK_Home || B.Kind == TK_Office || (B.Kind != TK_SkyTower && B.Kind != TK_Shop && B.Kind != TK_Research && Ny >= 8);
	if (!bKind || B.Storeys < 2 || B.State != 0 || Nx < 4 || Ny < 4 || !Generator->Piece(TEXT("Heaven.Stair20"))) return false;
	const float Hx = Nx * M * 0.5f, Hy = Ny * M * 0.5f;
	const int32 DoorCell = B.DoorSide < 2 ? B.DoorTile.Y - B.Min.Y : B.DoorTile.X - B.Min.X;
	const FVector Yw = FRotator(0, TownBldYaw(B), 0).RotateVector(FVector(0, 1, 0));
	const bool bYUp = (B.DoorSide < 2 ? Yw.Y : Yw.X) > 0.f;
	const int32 DoorK = bYUp ? DoorCell : Ny - 1 - DoorCell;
	const float DoorY = (DoorK + 0.5f) * M - Hy;
	// (the back corner away from the door's column first)
	for (const float Sgn : { DoorY >= 0.f ? 1.f : -1.f, DoorY >= 0.f ? -1.f : 1.f })
	{
		FCore20 C; C.Bld = BI; C.N = B.Storeys; C.Sgn = Sgn; C.X0 = -Hx; C.Y0 = Sgn > 0.f ? -Hy : Hy;
		bool bOk = true;
		TArray<FIntPoint> Tiles;
		for (int32 S = 0; S < 3 && bOk; ++S)
			for (int32 T = 0; T < 4 && bOk; ++T)
			{
				const FIntPoint Tl = WorldToLocal(CorePoint20(C, S, T, 0.f));
				if (!In(Tl) || Tl == B.DoorTile || Type[Idx(Tl)] != 1 || !B.Rooms.Contains(Owner[Idx(Tl)])) bOk = false;
				// (no room-to-room doorway through it)
				for (int32 D = 0; D < 4 && bOk; ++D) if (DoorEdges.Contains(EdgeKey(Tl, Tl + RDH20Dir4[D]))) bOk = false;
				Tiles.Add(Tl);
			}
		// (and a tile of the ground floor in front of the lift's strip to come in by: the core must not fill the building)
		if (!bOk || Nx * Ny - 12 < 4) continue;
		Cores20.Add(BI, C);
		for (const FIntPoint& Tl : Tiles) Blocked[Idx(Tl)] = 1;          // (the townsfolk's ways keep off it)
		return true;
	}
	return false;
}

FVector ARDSection::CorePoint20(const FCore20& C, float Strip, float Tile, float Z) const
{
	// (a strip's (0, 1 the stairs, 2 the lift's) tile's (0 to 3 from the corner) middle; fractions for its edges)
	const FTownBld& B = TownBlds[C.Bld];
	const float M = Generator->TileSize;
	return TownBldPoint(B, C.X0 + (Strip + 0.5f) * M, C.Y0 + C.Sgn * (Tile + 0.5f) * M, Z);
}

bool ARDSection::CoreOpenAt20(int32 BI, int32 Storey, const FVector& W) const
{
	// (the slab at Storey (1 to N, N the roof) is open over the flight that comes up through it and over the lift's shaft)
	const FCore20* C = Cores20.Find(BI);
	if (!C || Storey < 1) return false;
	const FIntPoint T = WorldToLocal(W);
	if (T == WorldToLocal(CorePoint20(*C, 2, 0, 0.f))) return true;
	const int32 S = (Storey - 1) % 2;
	return T == WorldToLocal(CorePoint20(*C, S, 1, 0.f)) || T == WorldToLocal(CorePoint20(*C, S, 2, 0.f));
}

// ------------------------------------------------------------------------------------------------ the floors, stairs, rails and lift
void ARDSection::HeavenStoreys20(int32 BI)
{
	if (!HeavenCorePlan20(BI)) return;
	FTownBld& B = TownBlds[BI];
	const FCore20& C = Cores20[BI];
	const float M = Generator->TileSize;
	const int32 Nx = B.DoorSide < 2 ? B.Max.X - B.Min.X : B.Max.Y - B.Min.Y;
	const int32 Ny = B.DoorSide < 2 ? B.Max.Y - B.Min.Y : B.Max.X - B.Min.X;
	const float Hx = Nx * M * 0.5f, Hy = Ny * M * 0.5f;
	const float Yaw0 = TownBldYaw(B);
	const FVector Along = FRotator(0, Yaw0, 0).RotateVector(FVector(0, C.Sgn, 0)), Across = FRotator(0, Yaw0, 0).RotateVector(FVector(1, 0, 0));
	int32 Slabs = 0, Flights = 0, Rails = 0;
	// ---- the floors between the storeys, open over the core's flight and shaft
	for (int32 K = 1; K < B.Storeys; ++K)
		for (int32 I = 0; I < Nx; ++I)
			for (int32 J = 0; J < Ny; ++J)
			{
				const FVector P = TownBldPoint(B, (I + 0.5f) * M - Hx, (J + 0.5f) * M - Hy, 2.f + 300.f * K);
				if (CoreOpenAt20(BI, K, P)) continue;
				AddPiece(TownPiece(B, TEXT("Floor")), FTransform(FRotator(0, Yaw0, 0), P));
				++Slabs;
			}
	// ---- the flights: flight k from storey k's floor up to k + 1's (the last to the roof); even ones up strip 0 toward the far tile,
	// odd ones up strip 1 back toward the corner
	for (int32 K = 0; K < B.Storeys; ++K)
	{
		const int32 S = K % 2;
		const bool bOut = S == 0;
		const float Z0 = RDH20Floor(K), Rise = (K == B.Storeys - 1 ? RDH20Roof(B.Storeys) : RDH20Floor(K + 1)) - Z0;
		const FVector Low = CorePoint20(C, S, bOut ? 0.5f : 2.5f, Z0);
		const FVector Way = bOut ? Along : -Along;
		AddPiece(TEXT("Heaven.Stair20"), FTransform(Way.Rotation(), Low, FVector(1.f, 1.f, Rise / 300.f)));
		++Flights;
		// (rails round the opening the flight comes up through: along both its long sides (none on the back wall's) and across its low end)
		const float Top = Z0 + Rise;
		// (a rail runs along its own Y: turned a quarter from the way it runs along; set on the floor the flight comes up to)
		auto Rail = [&](const FVector& At, const FVector& Dir) { AddPiece(TEXT("Heaven.Rail20"), FTransform(FRotator(0, Dir.Rotation().Yaw + 90.f, 0), At + FVector(0, 0, Rise))); ++Rails; };
		for (int32 T = 1; T <= 2; ++T)
		{
			const FVector Mid = CorePoint20(C, S, T, Z0);
			if (S == 1) Rail(Mid + Across * (M * 0.5f), Along);          // (strip 1's side toward the lift's strip)
			Rail(Mid + Across * (S == 0 ? M * 0.5f : -M * 0.5f), Along);          // (between the two stair strips)
		}
		Rail(CorePoint20(C, S, bOut ? 0.5f : 2.5f, Z0), Across);
	}
	// ---- the lift: its shaft at the corner of its strip, glass on its two inner sides storey by storey, its platform, a gate at each
	// floor's entry (toward its strip's next tile)
	const FVector Shaft = CorePoint20(C, 2, 0, 0.f);
	const FVector Entry = Shaft + Along * (M * 0.5f);
	const float RoofZ = RDH20Roof(B.Storeys);
	for (int32 K = 0; K <= B.Storeys; ++K)
	{
		const float Z = K < B.Storeys ? RDH20Floor(K) : RoofZ;
		const float Hh = K < B.Storeys ? 300.f : 120.f;
		for (const FVector& Side : { -Across, Across })
			AddPiece(TEXT("Heaven.LiftWall20"), FTransform(Side.Rotation(), Shaft + Side * (M * 0.5f) + FVector(0, 0, Z), FVector(1.f, 1.f, Hh / 300.f)));
		if (K == B.Storeys) AddPiece(TEXT("Heaven.LiftWall20"), FTransform(Along.Rotation(), Shaft - Along * (M * 0.5f) + FVector(0, 0, Z), FVector(1.f, 1.f, Hh / 300.f)));
	}
	if (bBuildStatic)
	{
		FLift20 L; L.Bld = BI; L.Shaft = Shaft; L.Entry = Along;
		for (int32 K = 0; K < B.Storeys; ++K) L.Floors.Add(GetActorLocation().Z + RDH20Floor(K));
		L.Floors.Add(GetActorLocation().Z + RoofZ);
		L.Z = L.Floors[0];
		if (const FRDPiece* Pp = Generator->Piece(TEXT("Heaven.LiftPlatform20")); Pp && Pp->Mesh)
		{
			UStaticMeshComponent* P = AddMesh(RootComponent, Pp->Mesh, FTransform::Identity, true);
			if (P)
			{
				if (Pp->Material) P->SetMaterial(0, Pp->Material);
				P->ComponentTags.Add(RDLiftTag20); P->ComponentTags.Add(FName(*FString::Printf(TEXT("Lift20_%d"), BI)));
				P->SetWorldLocationAndRotation(FVector(Shaft.X, Shaft.Y, L.Z), FRotator(0, Yaw0, 0));
				P->SetCanEverAffectNavigation(false);
				L.Platform = P;
			}
		}
		for (int32 K = 0; K < L.Floors.Num(); ++K)
		{
			UBoxComponent* G = NewObject<UBoxComponent>(this, NAME_None, RF_Transactional);
			G->SetupAttachment(RootComponent);
			G->SetBoxExtent(FVector(6.f, M * 0.5f - 10.f, 130.f));
			G->SetCollisionProfileName(TEXT("BlockAll"));
			G->SetHiddenInGame(true);
			G->ComponentTags.Add(RDLiftTag20); G->ComponentTags.Add(FName(*FString::Printf(TEXT("Lift20_%d"), BI)));
			G->RegisterComponent();
			G->SetWorldLocationAndRotation(FVector(Entry.X, Entry.Y, L.Floors[K] + 132.f), Along.Rotation());
			AddInstanceComponent(G);
			L.Gates.Add(G);
		}
		Lifts20.Add(L);
		UpdateLiftGates20(Lifts20.Last());
	}
	else
	{
		// (a replan with static building off (RestartPlay): the platform and gates built before, found again by their building's tag)
		FLift20 L; L.Bld = BI; L.Shaft = Shaft; L.Entry = Along;
		for (int32 K = 0; K < B.Storeys; ++K) L.Floors.Add(GetActorLocation().Z + RDH20Floor(K));
		L.Floors.Add(GetActorLocation().Z + RoofZ);
		const FName Tg(*FString::Printf(TEXT("Lift20_%d"), BI));
		for (UActorComponent* Cp : GetComponentsByTag(UPrimitiveComponent::StaticClass(), Tg))
		{
			if (UStaticMeshComponent* Sm = Cast<UStaticMeshComponent>(Cp)) L.Platform = Sm;
			else if (UPrimitiveComponent* Pc = Cast<UPrimitiveComponent>(Cp)) L.Gates.Add(Pc);
		}
		L.Gates.Sort([](const TWeakObjectPtr<UPrimitiveComponent>& A, const TWeakObjectPtr<UPrimitiveComponent>& Bb) { return A.Get() && Bb.Get() && A->GetComponentLocation().Z < Bb->GetComponentLocation().Z; });
		if (const UStaticMeshComponent* P = L.Platform.Get())
		{
			L.Z = P->GetComponentLocation().Z;
			for (int32 K = 0; K < L.Floors.Num(); ++K) if (FMath::Abs(L.Floors[K] - L.Z) < 5.f) { L.At = L.Target = K; }
		}
		Lifts20.Add(L);
	}
	Storeys20.Add(FString::Printf(TEXT("core|%d|%s|%d|%.0f|%.0f|%d|%d|%d"), BI, *TownKindName(B.Kind), B.Storeys, Shaft.X, Shaft.Y, Slabs, Flights, Rails));
	// (the way up for the tests: in at the lift's strip, round to the first flight's foot, and up flight by flight to the roof)
	auto Rt = [&](float S, float T, float Z) { const FVector P = CorePoint20(C, S, T, Z); Storeys20.Add(FString::Printf(TEXT("route|%d|%.0f|%.0f|%.0f"), BI, P.X, P.Y, P.Z)); };
	Rt(2.f, 2.f, RDH20Floor(0)); Rt(1.f, 1.f, RDH20Floor(0)); Rt(1.f, 0.f, RDH20Floor(0)); Rt(0.f, 0.f, RDH20Floor(0));
	for (int32 K = 0; K < B.Storeys; ++K)
	{
		const bool bOut = K % 2 == 0;
		const float Zt = K == B.Storeys - 1 ? RDH20Roof(B.Storeys) : RDH20Floor(K + 1);
		Rt(bOut ? 0.f : 1.f, bOut ? 3.f : 0.f, Zt);          // (the flight's top: its landing)
		if (K < B.Storeys - 1) Rt(bOut ? 1.f : 0.f, bOut ? 3.f : 0.f, Zt);          // (across to the next flight's foot)
	}
}

// ------------------------------------------------------------------------------------------------ the core kept free on the ground floor
void ARDSection::AddCoreFeet20(int32 RI)
{
	for (const TPair<int32, FCore20>& Kv : Cores20)
	{
		const FTownBld& B = TownBlds[Kv.Key];
		if (!B.Rooms.Contains(RI)) continue;
		const FVector Ctr = CorePoint20(Kv.Value, 1.f, 1.5f, 0.f);
		AddFoot(Ctr, TownBldYaw(B), FVector2D(3.f * Generator->TileSize, 4.f * Generator->TileSize), false, TEXT("Core20"));
	}
}

// ------------------------------------------------------------------------------------------------ the upper storeys furnished
void ARDSection::FurnishStoreys20(int32 BI)
{
	const FCore20* C = Cores20.Find(BI);
	if (!C) return;
	const FTownBld& B = TownBlds[BI];
	FRandomStream R((int32)(B.Seed ^ 0x570E7u));
	const float M = Generator->TileSize;
	const int32 Nx = B.DoorSide < 2 ? B.Max.X - B.Min.X : B.Max.Y - B.Min.Y;
	const int32 Ny = B.DoorSide < 2 ? B.Max.Y - B.Min.Y : B.Max.X - B.Min.X;
	const float Hx = Nx * M * 0.5f, Hy = Ny * M * 0.5f;
	const float Yaw0 = TownBldYaw(B);
	TSet<FIntPoint> CoreT;
	for (int32 S = 0; S < 3; ++S) for (int32 T = 0; T < 4; ++T) CoreT.Add(WorldToLocal(CorePoint20(*C, S, T, 0.f)));
	int32 Placed = 0;
	for (int32 K = 1; K < B.Storeys; ++K)
	{
		const float Z = RDH20Floor(K);
		for (int32 I = 0; I < Nx; ++I)
			for (int32 J = 0; J < Ny; ++J)
			{
				const float X = (I + 0.5f) * M - Hx, Y = (J + 0.5f) * M - Hy;
				const FVector P = TownBldPoint(B, X, Y, Z);
				const FIntPoint T = WorldToLocal(P);
				if (CoreT.Contains(T)) continue;
				// (a ceiling light on every other tile: the storey seen lit through its windows)
				if ((I + J) % 2 == 0) AddPiece(TEXT("Heaven.CeilingPanel20"), FTransform(FRotator(0, Yaw0, 0), TownBldPoint(B, X, Y, 300.f * K + 272.f - 4.f)), true);
				// (the edge tiles: something against the wall, facing in; the inner ones: something free-standing; one tile in three left clear)
				const bool bEdgeX = I == 0 || I == Nx - 1, bEdgeY = J == 0 || J == Ny - 1;
				const float U = R.FRand(), V = R.FRand();
				if (U < 0.33f) continue;
				// (a wall's piece's back to that wall: its front +X turned inward)
				const float InYaw = bEdgeX ? (I == 0 ? 0.f : 180.f) : bEdgeY ? (J == 0 ? 90.f : -90.f) : 90.f * R.RandRange(0, 3);
				const float Yaw = Yaw0 + InYaw;
				const FVector Back = FRotator(0, Yaw, 0).RotateVector(FVector(-1, 0, 0));
				FName Nm;
				if (bEdgeX || bEdgeY)
				{
					if (B.Kind == TK_Office) Nm = V < 0.5f ? FName(TEXT("Heaven.Bookshelf2")) : V < 0.8f ? FName(TEXT("Heaven.ShelfRack")) : FName(TEXT("Heaven.CandleStand"));
					// (a flat's bed under the town's own name: a town bed its residents are given (the cores took ground-floor room: 57 sleepers
					// in bed fell to 49); they are laid in it from where they stand, upstairs as down)
					else if (B.Kind == TK_Home) Nm = V < 0.3f ? FName(TEXT("Bed")) : V < 0.5f ? FName(TEXT("Heaven.Fireplace")) : V < 0.65f ? FName(TEXT("Heaven.PrepTable")) : V < 0.8f ? FName(TEXT("Heaven.BreadOven")) : FName(TEXT("Heaven.Bookshelf2"));
					else Nm = V < 0.6f ? FName(TEXT("Heaven.ShelfRack")) : FName(TEXT("Heaven.Bookshelf2"));
					const FRDPiece* Pp = Pc(Nm);
					const float Off = Pp ? M * 0.5f - Pp->Size.X * 0.5f - 25.f : 0.f;
					AddPiece(Nm, FTransform(FRotator(0, Yaw, 0), P + Back * Off));
				}
				else
				{
					if (B.Kind == TK_Office) { AddPiece(TEXT("Heaven.Desk"), FTransform(FRotator(0, Yaw, 0), P)); AddPiece(TEXT("Heaven.Chair"), FTransform(FRotator(0, Yaw + 180.f, 0), P - FRotator(0, Yaw, 0).RotateVector(FVector(95.f, 0, 0)))); }
					else if (B.Kind == TK_Home) { if (V < 0.5f) { AddPiece(TEXT("Heaven.TableSmall"), FTransform(FRotator(0, Yaw, 0), P)); AddPiece(TEXT("Heaven.Bench"), FTransform(FRotator(0, Yaw + 180.f, 0), P + FRotator(0, Yaw, 0).RotateVector(FVector(-95.f, 0, 0)))); } else AddPiece(TEXT("Heaven.TableLong"), FTransform(FRotator(0, Yaw, 0), P)); }
					else AddPiece(TEXT("Heaven.TableLong"), FTransform(FRotator(0, Yaw, 0), P));
				}
				++Placed;
			}
	}
	Storeys20.Add(FString::Printf(TEXT("furnished|%d|%d"), BI, Placed));
}

// ------------------------------------------------------------------------------------------------ the lift at play
void ARDSection::UpdateLiftGates20(FLift20& L)
{
	// (a floor's gate shut unless the platform stands there)
	for (int32 K = 0; K < L.Gates.Num(); ++K)
		if (UPrimitiveComponent* G = L.Gates[K].Get())
		{
			const bool bOpen = !L.bMoving && L.At == K;
			G->SetCollisionEnabled(bOpen ? ECollisionEnabled::NoCollision : ECollisionEnabled::QueryAndPhysics);
		}
}

void ARDSection::TickLifts20(float Dt)
{
	for (FLift20& L : Lifts20)
	{
		if (!L.Floors.IsValidIndex(L.Target)) continue;
		const float Want = L.Floors[L.Target];
		if (FMath::Abs(L.Z - Want) < 0.5f) { if (L.bMoving) { L.bMoving = false; L.At = L.Target; L.Z = Want; UpdateLiftGates20(L); } continue; }
		if (!L.bMoving) { L.bMoving = true; UpdateLiftGates20(L); }
		L.Z = FMath::FInterpConstantTo(L.Z, Want, Dt, Generator->LiftSpeed20);
		if (UStaticMeshComponent* P = L.Platform.Get()) P->SetWorldLocation(FVector(L.Shaft.X, L.Shaft.Y, L.Z));
	}
}

int32 ARDSection::LiftNear20(const FVector& From, int32& OutFloor, bool& bOnIt) const
{
	// (on its platform: within its square and a body's height over it; at its door: before its entry, at a floor's height)
	OutFloor = -1; bOnIt = false;
	for (int32 I = 0; I < Lifts20.Num(); ++I)
	{
		const FLift20& L = Lifts20[I];
		const FVector D = From - L.Shaft;
		if (FMath::Abs(D.X) < 160.f && FMath::Abs(D.Y) < 160.f && FMath::Abs(From.Z - L.Z - 92.f) < 80.f) { bOnIt = true; OutFloor = L.At; return I; }
		const FVector E = L.Shaft + L.Entry * 300.f;
		if (FVector::Dist2D(From, E) < 220.f)
			for (int32 K = 0; K < L.Floors.Num(); ++K) if (FMath::Abs(From.Z - L.Floors[K] - 92.f) < 80.f) { OutFloor = K; return I; }
	}
	return -1;
}

FString ARDSection::LiftFloorName20(const FLift20& L, int32 K) const
{
	return K == 0 ? FString(TEXT("the street")) : K == L.Floors.Num() - 1 ? FString(TEXT("the roof")) : FString::Printf(TEXT("floor %d"), K);
}

FString ARDSection::LiftDescribe20(const FVector& From) const
{
	int32 F; bool bOn;
	const int32 I = LiftNear20(From, F, bOn);
	if (I < 0) return FString();
	const FLift20& L = Lifts20[I];
	if (L.bMoving) return TEXT("the lift is moving");
	if (bOn) { const int32 Next = L.At + 1 < L.Floors.Num() ? L.At + 1 : 0; return FString::Printf(TEXT("ride the lift to %s"), *LiftFloorName20(L, Next)); }
	return L.At == F ? FString(TEXT("the lift is here: step on")) : FString(TEXT("call the lift"));
}

FString ARDSection::LiftUse20(const FVector& From)
{
	int32 F; bool bOn;
	const int32 I = LiftNear20(From, F, bOn);
	if (I < 0) return FString();
	FLift20& L = Lifts20[I];
	if (L.bMoving) return TEXT("lift moving");
	if (bOn) { L.Target = L.At + 1 < L.Floors.Num() ? L.At + 1 : 0; UE_LOG(LogRDHeaven20, Log, TEXT("RDHEAVEN20 lift %d: up from %d to %d"), L.Bld, L.At, L.Target); return TEXT("lift ride"); }
	if (L.At == F) return TEXT("lift here");
	L.Target = F;
	UE_LOG(LogRDHeaven20, Log, TEXT("RDHEAVEN20 lift %d called to floor %d (from %d)"), L.Bld, F, L.At);
	return TEXT("lift called");
}

TArray<FString> ARDSection::GetStoreys20() const
{
	// (for the tests: the cores, routes and furnishing, then "lift|<i>|<building>|<x>|<y>|<floors>|<at>|<target>|<z>|<moving>|<gates shut>"
	// and "liftfloor|<i>|<k>|<z>")
	TArray<FString> Out = Storeys20;
	for (int32 I = 0; I < Lifts20.Num(); ++I)
	{
		const FLift20& L = Lifts20[I];
		int32 Shut = 0;
		for (const TWeakObjectPtr<UPrimitiveComponent>& G : L.Gates) if (const UPrimitiveComponent* Gp = G.Get(); Gp && Gp->GetCollisionEnabled() != ECollisionEnabled::NoCollision) ++Shut;
		Out.Add(FString::Printf(TEXT("lift|%d|%d|%.0f|%.0f|%d|%d|%d|%.1f|%d|%d|%d"), I, L.Bld, L.Shaft.X, L.Shaft.Y, L.Floors.Num(), L.At, L.Target, L.Z, L.bMoving ? 1 : 0, Shut, L.Platform.IsValid() ? 1 : 0));
		for (int32 K = 0; K < L.Floors.Num(); ++K) Out.Add(FString::Printf(TEXT("liftfloor|%d|%d|%.0f"), I, K, L.Floors[K]));
	}
	return Out;
}

void ARDDungeonGenerator::TickLifts20(float Dt)
{
	if (TownPlan != 5) return;
	if (ARDSection* S = GetSection(FIntPoint::ZeroValue); S && !S->IsBuilding()) S->TickLifts20(Dt);
}
