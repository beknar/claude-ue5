// The user's list of 2026-11-22 (docs/improvements16.txt: "the skyscrapers and very tall office buildings can have the front door or
// entrances transport them to a new level that holds only the skyscraper's floors ... office furniture and rooms that look like an
// office, as well as typical rooms that are in a modern building, like bathrooms, offices, cubicles, datacenter rooms, equipment closets,
// a cafeteria ... if the player looks out the window, she should see the layout of the city, but not be able to interact with it ...
// procedurally generated"; the plan docs/improvements16_plan.md), its twenty-fourth phase, the skyscrapers' level (heaven_tower, 948):
// - in Heaven, F at a tower's door: the city round it captured in three cube pictures (low, middle and high floors, at the hour she
//   enters, the tower itself taken out of them), kept by the game instance with the tower's seed, name and floors; then the trip into
//   the level as into a dungeon (her things carried, the way back before the door);
// - the level (a Save As copy of the castle with bTower24): no sets of rooms, no monsters; the tower built from its seed: a lobby, its
//   floors (a stair and lift core, a corridor round it, rooms along the windows: offices, cubicle farms, meeting rooms, bathrooms,
//   equipment closets, a cafeteria floor, a data centre floor, the executive floor at the top), glass all round with the city's picture
//   for its floor behind it; two lifts (one stopping at every floor, one express between the lobby and the top), the stairs; the
//   lobby's doors take her back to the street.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "RD/RDGameInstance.h"
#include "RD/RDCombat.h"
#include "Components/BoxComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "UObject/UObjectIterator.h"
#include "Components/PostProcessComponent.h"
#include "Components/SceneCaptureComponentCube.h"
#include "Engine/TextureRenderTargetCube.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Kismet/KismetRenderingLibrary.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDTower24, Log, All);

static const FIntPoint RDT24Dir4[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };
static const TCHAR* RDT24Names[12] = { TEXT("Meridian"), TEXT("Aurora"), TEXT("Summit"), TEXT("Halcyon"), TEXT("Zenith"), TEXT("Apex"), TEXT("Lumen"),
	TEXT("Vantage"), TEXT("Crestline"), TEXT("Solace"), TEXT("Beacon"), TEXT("Skyline") };

// ================================================================================================ Heaven: a tower's door
FString ARDDungeonGenerator::TowerName24(uint32 Seed)
{
	return FString::Printf(TEXT("%s Tower"), RDT24Names[(Seed >> 3) % 12u]);
}

int32 ARDDungeonGenerator::TowerFloors24(uint32 Seed)
{
	// (the lobby and the floors drawn over it in the city: RDHeaven.cpp's 4 + seed % 7)
	return 1 + 4 + (int32)(Seed % 7u);
}

int32 ARDDungeonGenerator::TowerDoorNear24(const FVector& From, FVector* OutDoor, FVector* OutOut) const
{
	if (!bTown || TownPlan != 5 || TowerLevel24.IsEmpty() || bTownTraveling) return -1;
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S || S->IsBuilding()) return -1;
	int32 Best = -1; float BestD = 260.f;
	for (int32 I = 0; I < S->TownBlds.Num(); ++I)
	{
		const ARDSection::FTownBld& B = S->TownBlds[I];
		if (B.Kind != TK_SkyTower || B.State != 0) continue;
		const FVector Out(RDT24Dir4[B.DoorSide].X, RDT24Dir4[B.DoorSide].Y, 0.f);
		const FVector Door = S->LocalToWorld(B.DoorTile) + Out * (TileSize * 0.5f);
		const float D = FVector::Dist2D(Door, From);
		if (D < BestD && FMath::Abs(From.Z - Door.Z) < 300.f) { BestD = D; Best = I; if (OutDoor) *OutDoor = Door; if (OutOut) *OutOut = Out; }
	}
	return Best;
}

FString ARDDungeonGenerator::TowerDescribe24(const FVector& From) const
{
	const int32 I = TowerDoorNear24(From);
	if (I < 0) return FString();
	const ARDSection::FTownBld& B = GetSection(FIntPoint::ZeroValue)->TownBlds[I];
	return FString::Printf(TEXT("enter %s (%d floors)"), *TowerName24(B.Seed), TowerFloors24(B.Seed));
}

FString ARDDungeonGenerator::TowerUse24(const FVector& From)
{
	FVector Door, Out;
	const int32 I = TowerDoorNear24(From, &Door, &Out);
	if (I < 0) return FString();
	return EnterTower24(I) ? FString(TEXT("tower")) : FString();
}

bool ARDDungeonGenerator::EnterTower24(int32 BI)
{
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S || !S->TownBlds.IsValidIndex(BI) || (PlayerCombat && PlayerCombat->IsDead())) return false;
	const ARDSection::FTownBld& B = S->TownBlds[BI];
	const FVector Out(RDT24Dir4[B.DoorSide].X, RDT24Dir4[B.DoorSide].Y, 0.f);
	const FVector Door = S->LocalToWorld(B.DoorTile) + Out * (TileSize * 0.5f);
	const FVector Back = Door + Out * 450.f + FVector(0, 0, 100.f);
	const int32 Floors = TowerFloors24(B.Seed);
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (GI && !bTravelDryRun)
	{
		GI->TowerSeed24 = (int32)(B.Seed & 0x7fffffff); GI->TowerFloors24 = Floors; GI->TowerName24 = TowerName24(B.Seed);
		// (the tower's frame in the city: its middle, and the way its door faces (the level's lobby doors face -Y))
		const FVector Ctr = S->TownBldPoint24(B, 0.f, 0.f, 0.f);
		GI->TowerAt24 = Ctr; GI->TowerYaw24 = Out.Rotation().Yaw;
		CaptureTowerViews24(BI);
	}
	LastTravel = TEXT("tower");
	if (bTravelDryRun) return true;
	if (!DescendToCatacombs(Back, Out.Rotation().Yaw, TowerLevel24)) return false;
	UE_LOG(LogRDTower24, Log, TEXT("RDTOWER24 into %s (seed %u, %d floors)"), *TowerName24(B.Seed), B.Seed, Floors);
	return true;
}

void ARDDungeonGenerator::TowerOutOfCity24(int32 BI, TArray<FTowerMoved24>& Moved, TArray<UPrimitiveComponent*>& Hidden, TArray<AActor*>& HiddenActors)
{
	// (the tower's pieces stand in the town's instanced components, shared with every other building: its own, those standing in its
	// footprint, moved far down for the moment; its other components and the people in it hidden from the capture)
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S || !S->TownBlds.IsValidIndex(BI)) return;
	const ARDSection::FTownBld& B = S->TownBlds[BI];
	FBox Foot(ForceInit);
	const float M = TileSize;
	const int32 Nx = B.DoorSide < 2 ? B.Max.X - B.Min.X : B.Max.Y - B.Min.Y, Ny = B.DoorSide < 2 ? B.Max.Y - B.Min.Y : B.Max.X - B.Min.X;
	for (const float Sx : { -0.5f, 0.5f }) for (const float Sy : { -0.5f, 0.5f }) Foot += S->TownBldPoint24(B, Sx * Nx * M, Sy * Ny * M, 0.f);
	Foot = Foot.ExpandBy(FVector(60.f, 60.f, 0.f));
	const float Z0 = S->GetActorLocation().Z;
	auto Inside = [&](const FVector& P) { return P.X > Foot.Min.X && P.X < Foot.Max.X && P.Y > Foot.Min.Y && P.Y < Foot.Max.Y && P.Z > Z0 - 80.f; };
	TArray<UActorComponent*> Comps; S->GetComponents(UPrimitiveComponent::StaticClass(), Comps);
	for (UActorComponent* Ac : Comps)
	{
		if (UInstancedStaticMeshComponent* Is = Cast<UInstancedStaticMeshComponent>(Ac))
		{
			bool bAny = false;
			for (int32 I = 0; I < Is->GetInstanceCount(); ++I)
			{
				FTransform T; Is->GetInstanceTransform(I, T, true);
				if (!Inside(T.GetLocation())) continue;
				Moved.Add({ Is, I, T }); bAny = true;
				FTransform Far = T; Far.SetLocation(T.GetLocation() - FVector(0, 0, 1e6f));
				Is->UpdateInstanceTransform(I, Far, true, false, true);
			}
			if (bAny) Is->MarkRenderStateDirty();
		}
		else if (UPrimitiveComponent* P = Cast<UPrimitiveComponent>(Ac); P && P->IsVisible() && Inside(P->Bounds.Origin)) Hidden.Add(P);
	}
	if (APawn* Pw = UGameplayStatics::GetPlayerPawn(this, 0)) HiddenActors.Add(Pw);
	for (ARDTownsfolk* Fp : TownPeople) if (Fp && Inside(Fp->GetActorLocation())) HiddenActors.Add(Fp);
}

void ARDDungeonGenerator::TowerBackInCity24(const TArray<FTowerMoved24>& Moved)
{
	TSet<UInstancedStaticMeshComponent*> Dirty;
	for (const FTowerMoved24& Mv : Moved) if (UInstancedStaticMeshComponent* Is = Mv.C.Get()) { Is->UpdateInstanceTransform(Mv.I, Mv.T, true, false, true); Dirty.Add(Is); }
	for (UInstancedStaticMeshComponent* Is : Dirty) Is->MarkRenderStateDirty();
}

void ARDDungeonGenerator::CaptureTowerViews24(int32 BI)
{
	// (the city round the tower from inside it, at three heights, the tower itself taken out)
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!S || !GI || !S->TownBlds.IsValidIndex(BI)) return;
	const ARDSection::FTownBld& B = S->TownBlds[BI];
	const double T0 = FPlatformTime::Seconds();
	TArray<FTowerMoved24> Moved; TArray<UPrimitiveComponent*> Hidden; TArray<AActor*> HiddenA;
	TowerOutOfCity24(BI, Moved, Hidden, HiddenA);
	USceneCaptureComponentCube* Cap = NewObject<USceneCaptureComponentCube>(this);
	Cap->bCaptureEveryFrame = false; Cap->bCaptureOnMovement = false; Cap->bCaptureRotation = false;
	Cap->CaptureSource = bTowerCaptureLDR24 ? ESceneCaptureSource::SCS_FinalColorLDR : ESceneCaptureSource::SCS_SceneColorHDR;
	Cap->RegisterComponent();
	for (UPrimitiveComponent* P : Hidden) Cap->HiddenComponents.Add(P);
	for (AActor* A : HiddenA) Cap->HiddenActors.Add(A);
	// (three heights: the share of the tower's storeys a capture stands for, its floor in the level)
	const int32 Floors = TowerFloors24(B.Seed);
	const float Height = FMath::Max(HeavenTowerHeight24(S, BI), 900.f);
	const float Z0 = S->GetActorLocation().Z;
	GI->TowerViews24.SetNum(3); GI->TowerViewFloors24.SetNum(3); GI->TowerViewAt24.SetNum(3);
	const float Shares[3] = { 0.12f, 0.5f, 0.88f };
	const FVector Ctr = S->TownBldPoint24(B, 0.f, 0.f, 0.f);
	for (int32 K = 0; K < 3; ++K)
	{
		TObjectPtr<UTextureRenderTargetCube>& Rt = GI->TowerViews24[K];
		if (!Rt) { Rt = NewObject<UTextureRenderTargetCube>(GI); Rt->Init(FMath::Clamp(TowerCaptureSize24, 128, 2048), PF_FloatRGBA); }
		Cap->TextureTarget = Rt;
		const float Z = Z0 + 160.f + Shares[K] * (Height - 300.f);
		Cap->SetWorldLocation(FVector(Ctr.X, Ctr.Y, Z));
		GI->TowerViewAt24[K] = FVector(Ctr.X, Ctr.Y, Z);
		// (twice: the first capture drew the tower's pieces where they stood before they were moved (the GPU's copy of the instances is
		// brought up to date with the first one): the north and west pictures showed its own floors from inside)
		Cap->CaptureScene(); Cap->CaptureScene();
		GI->TowerViewFloors24[K] = FMath::Clamp(FMath::RoundToInt(Shares[K] * (Floors - 1)), 0, Floors - 1);
	}
	Cap->DestroyComponent();
	TowerBackInCity24(Moved);
	GI->TowerViewHour24 = GetTownHour();
	UE_LOG(LogRDTower24, Log, TEXT("RDTOWER24 views of %s: 3 cubes of %d at %.1f h, %d pieces and %d components taken out, %.0f ms"),
		*TowerName24(B.Seed), TowerCaptureSize24, GI->TowerViewHour24, Moved.Num(), Hidden.Num(), (FPlatformTime::Seconds() - T0) * 1000.0);
}

bool ARDDungeonGenerator::CaptureCity24(int32 BI, FVector At, FRotator Rot, float Fov, int32 Width, int32 Height, const FString& Dir, const FString& File)
{
	TArray<FTowerMoved24> Moved; TArray<UPrimitiveComponent*> Hidden; TArray<AActor*> HiddenA;
	TowerOutOfCity24(BI, Moved, Hidden, HiddenA);
	USceneCaptureComponent2D* Cap = NewObject<USceneCaptureComponent2D>(this);
	UTextureRenderTarget2D* Rt = UKismetRenderingLibrary::CreateRenderTarget2D(this, FMath::Clamp(Width, 64, 4096), FMath::Clamp(Height, 64, 4096), RTF_RGBA8_SRGB);
	bool bOk = false;
	if (Cap && Rt)
	{
		Cap->bCaptureEveryFrame = false; Cap->bCaptureOnMovement = false; Cap->FOVAngle = Fov;
		Cap->CaptureSource = ESceneCaptureSource::SCS_FinalColorLDR;
		Cap->TextureTarget = Rt;
		Cap->RegisterComponent();
		for (UPrimitiveComponent* P : Hidden) Cap->HiddenComponents.Add(P);
		for (AActor* A : HiddenA) Cap->HiddenActors.Add(A);
		Cap->SetWorldLocationAndRotation(At, Rot);
		Cap->CaptureScene(); Cap->CaptureScene();
		UKismetRenderingLibrary::ExportRenderTarget(this, Rt, Dir, File);
		Cap->DestroyComponent();
		bOk = true;
	}
	TowerBackInCity24(Moved);
	return bOk;
}

float ARDDungeonGenerator::HeavenTowerHeight24(const ARDSection* S, int32 BI) const
{
	// (the tower's top over the street: its lobby and its floors as RDHeaven.cpp stacks them)
	const ARDSection::FTownBld& B = S->TownBlds[BI];
	const FRDPiece* Mid = Piece(TEXT("Heaven.TowerMid"));
	const float Step = Mid ? FMath::Max((float)Mid->Size.Z - 22.f, 100.f) : 400.f;
	return 330.f + 30.f + (4 + (int32)(B.Seed % 7u)) * Step;
}

TArray<FString> ARDDungeonGenerator::GetTowerDoors24() const
{
	// (for the tests: "door|<building>|<x>|<y>|<z>|<out x>|<out y>|<name>|<floors>" for every tower of Heaven)
	TArray<FString> Out;
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S || TownPlan != 5) return Out;
	for (int32 I = 0; I < S->TownBlds.Num(); ++I)
	{
		const ARDSection::FTownBld& B = S->TownBlds[I];
		if (B.Kind != TK_SkyTower || B.State != 0) continue;
		const FVector O(RDT24Dir4[B.DoorSide].X, RDT24Dir4[B.DoorSide].Y, 0.f);
		const FVector D = S->LocalToWorld(B.DoorTile) + O * (TileSize * 0.5f);
		Out.Add(FString::Printf(TEXT("door|%d|%.0f|%.0f|%.0f|%.0f|%.0f|%s|%d"), I, D.X, D.Y, D.Z, O.X, O.Y, *TowerName24(B.Seed), TowerFloors24(B.Seed)));
	}
	return Out;
}

// ================================================================================================ the tower level: its plan
namespace
{
	enum ERDT24Kind : uint8 { T24_Lobby = 1, T24_Office, T24_Cubicles, T24_Meeting, T24_Bath, T24_Closet, T24_Cafe, T24_Data, T24_Exec, T24_Board };
	const TCHAR* RDT24KindName(uint8 K)
	{
		switch (K)
		{
		case T24_Lobby: return TEXT("lobby"); case T24_Office: return TEXT("office"); case T24_Cubicles: return TEXT("cubicles");
		case T24_Meeting: return TEXT("meeting"); case T24_Bath: return TEXT("bathroom"); case T24_Closet: return TEXT("closet");
		case T24_Cafe: return TEXT("cafeteria"); case T24_Data: return TEXT("datacentre"); case T24_Exec: return TEXT("executive");
		case T24_Board: return TEXT("boardroom"); default: return TEXT("?");
		}
	}
}

void ARDDungeonGenerator::ApplyTower24()
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	TowerSeedNow24 = GI && GI->TowerSeed24 != 0 ? GI->TowerSeed24 : TowerDefaultSeed24;
	TowerFloorsNow24 = GI && GI->TowerFloors24 > 0 ? GI->TowerFloors24 : TowerFloors24((uint32)TowerSeedNow24);
	TowerNameNow24 = GI && !GI->TowerName24.IsEmpty() ? GI->TowerName24 : TowerName24((uint32)TowerSeedNow24);
	DungeonKey = FString::Printf(TEXT("tower:%d"), TowerSeedNow24);
	DungeonTitle = TowerNameNow24;
	bFinalBossOn = false;
	UE_LOG(LogRDTower24, Log, TEXT("RDTOWER24 the level: %s, seed %d, %d floors"), *TowerNameNow24, TowerSeedNow24, TowerFloorsNow24);
}

void ARDDungeonGenerator::PlanTower24()
{
	// (each floor a grid of 1.5 m cells: the core in the middle (4 x 4), a corridor ring round it, and four bands of rooms along the
	// windows, split by the floor's own stream; the floor's kind (lobby, cafeteria, data centre, executive, ordinary) by the tower's seed)
	const int32 N = TowerCells24, Nf = TowerFloorsNow24;
	TowerPlan24.SetNum(Nf);
	TowerRooms24.Reset();
	FRandomStream R0(TowerSeedNow24 ^ 0x70E4);
	const int32 Cafe = Nf > 3 ? 1 + R0.RandRange(0, FMath::Max(0, Nf - 4)) : -1;
	int32 Data = Nf > 4 ? 1 + R0.RandRange(0, FMath::Max(0, Nf - 4)) : -1;
	if (Data == Cafe) Data = Data + 1 < Nf - 1 ? Data + 1 : Data - 1;
	const int32 C0 = N / 2 - 2, C1 = N / 2 + 1;          // (the core's cells, inclusive)
	const int32 B0 = C0 - 2, B1 = C1 + 2;              // (the corridor ring's outer cells)
	for (int32 K = 0; K < Nf; ++K)
	{
		TArray<int32>& G = TowerPlan24[K];
		G.Init(0, N * N);
		auto At = [&](int32 I, int32 J) -> int32& { return G[J * N + I]; };
		FRandomStream R((TowerSeedNow24 * 31) ^ (K * 7919 + 17));
		for (int32 I = 0; I < N; ++I) for (int32 J = 0; J < N; ++J)
		{
			if (I >= C0 && I <= C1 && J >= C0 && J <= C1) At(I, J) = -2;          // (the core)
			else if (I >= B0 && I <= B1 && J >= B0 && J <= B1) At(I, J) = -1;     // (the corridor)
		}
		const uint8 FloorKind = K == 0 ? T24_Lobby : K == Nf - 1 ? T24_Exec : K == Cafe ? T24_Cafe : K == Data ? T24_Data : T24_Office;
		auto AddRoom = [&](int32 X0, int32 Y0, int32 X1, int32 Y1, uint8 Kind) -> int32
		{
			FRoom24 Rm; Rm.Floor = K; Rm.Min = FIntPoint(X0, Y0); Rm.Max = FIntPoint(X1, Y1); Rm.Kind = Kind;
			const int32 Id = TowerRooms24.Add(Rm);
			for (int32 I = X0; I <= X1; ++I) for (int32 J = Y0; J <= Y1; ++J) At(I, J) = Id + 1;
			return Id;
		};
		if (FloorKind == T24_Lobby)
		{
			// (the lobby: the whole floor round the core but two bathrooms and a closet in the east band)
			AddRoom(B1 + 1, B0, N - 1, B0 + 2, T24_Bath);
			AddRoom(B1 + 1, B0 + 3, N - 1, B0 + 4, T24_Bath);
			AddRoom(B1 + 1, B0 + 5, N - 1, B1, T24_Closet);
			const int32 L = TowerRooms24.Add(FRoom24{ K, FIntPoint(0, 0), FIntPoint(N - 1, N - 1), T24_Lobby });
			for (int32 I = 0; I < N; ++I) for (int32 J = 0; J < N; ++J) if (At(I, J) == 0 || At(I, J) == -1) At(I, J) = L + 1;
			continue;
		}
		// (the four bands: north and south across the whole width (the corners theirs), west and east between them)
		struct FBand { bool bAlongX; int32 Fixed0, Fixed1, Len0, Len1; };
		const FBand Bands[4] = { { true, B1 + 1, N - 1, 0, N - 1 }, { true, 0, B0 - 1, 0, N - 1 }, { false, 0, B0 - 1, B0, B1 }, { false, B1 + 1, N - 1, B0, B1 } };
		// (which band is what on this floor)
		uint8 Whole[4] = { 0, 0, 0, 0 };
		if (FloorKind == T24_Cafe) Whole[0] = T24_Cafe;
		else if (FloorKind == T24_Data) { Whole[0] = T24_Data; Whole[1] = T24_Data; }
		else if (FloorKind == T24_Exec) Whole[0] = T24_Board;
		else if (R.FRand() < 0.6f) Whole[R.RandRange(0, 1)] = T24_Cubicles;
		bool bBaths = false, bCloset = false;
		for (int32 Bi = 0; Bi < 4; ++Bi)
		{
			const FBand& Bd = Bands[Bi];
			auto Rect = [&](int32 A0, int32 A1, uint8 Kind)
			{
				if (Bd.bAlongX) return AddRoom(A0, Bd.Fixed0, A1, Bd.Fixed1, Kind);
				return AddRoom(Bd.Fixed0, A0, Bd.Fixed1, A1, Kind);
			};
			if (Whole[Bi]) { Rect(Bd.Len0, Bd.Len1, Whole[Bi]); continue; }
			// (split along its length: the across bands' end rooms reach past the corner into the corridor's span)
			TArray<int32> Cuts;
			int32 A = Bd.Len0;
			if (Bd.bAlongX)
			{
				const int32 E0 = B0 + R.RandRange(1, 2), E1 = B1 - R.RandRange(1, 2);          // (the end rooms' inner edges)
				Cuts = { E0 };
				if (E1 - E0 >= 5) Cuts.Add(E0 + (E1 - E0) / 2);
				Cuts.Add(E1);
			}
			else
			{
				for (int32 L = Bd.Len0 + R.RandRange(2, 3); L < Bd.Len1 - 1; L += R.RandRange(2, 4)) Cuts.Add(L);
			}
			TArray<FIntPoint> Spans;
			for (const int32 Cx : Cuts) { if (Cx > A) { Spans.Add(FIntPoint(A, Cx - 1)); A = Cx; } }
			Spans.Add(FIntPoint(A, Bd.Len1));
			for (const FIntPoint& Sp : Spans)
			{
				const int32 Len = Sp.Y - Sp.X + 1;
				uint8 Kind;
				// (every floor its two bathrooms and a closet, in the side bands; the rest offices and meeting rooms)
				if (!Bd.bAlongX && !bBaths && Len <= 3) { Kind = T24_Bath; bBaths = Rect(Sp.X, Sp.Y, Kind) >= 0; continue; }
				if (!Bd.bAlongX && !bCloset && Len <= 3 && bBaths) { Kind = T24_Closet; bCloset = true; Rect(Sp.X, Sp.Y, Kind); continue; }
				Kind = FloorKind == T24_Exec ? T24_Exec : (Len >= 4 && R.FRand() < 0.35f) ? T24_Meeting : T24_Office;
				Rect(Sp.X, Sp.Y, Kind);
			}
		}
		// (a floor that drew no bathroom or closet: the smallest offices become them)
		for (int32 Pass = 0; Pass < 2; ++Pass)
		{
			if (Pass == 0 ? bBaths : bCloset) continue;
			int32 Pick = -1, PickA = 1 << 30;
			for (int32 Ri = 0; Ri < TowerRooms24.Num(); ++Ri)
			{
				const FRoom24& Rm = TowerRooms24[Ri];
				const int32 Ar = (Rm.Max.X - Rm.Min.X + 1) * (Rm.Max.Y - Rm.Min.Y + 1);
				if (Rm.Floor == K && (Rm.Kind == T24_Office || Rm.Kind == T24_Exec) && Ar < PickA) { PickA = Ar; Pick = Ri; }
			}
			if (Pick >= 0) TowerRooms24[Pick].Kind = Pass == 0 ? T24_Bath : T24_Closet;
		}
	}
	// (each room's doorway: on its edge to the corridor (the lobby needs none), the middle cell of that edge)
	for (FRoom24& Rm : TowerRooms24)
	{
		if (Rm.Kind == T24_Lobby) continue;
		const TArray<int32>& G = TowerPlan24[Rm.Floor];
		TArray<TPair<FIntPoint, int32>> Edge;          // (a cell of the room and the way to the corridor or lobby)
		for (int32 I = Rm.Min.X; I <= Rm.Max.X; ++I) for (int32 J = Rm.Min.Y; J <= Rm.Max.Y; ++J)
			for (int32 D = 0; D < 4; ++D)
			{
				const FIntPoint Q(I + RDT24Dir4[D].X, J + RDT24Dir4[D].Y);
				if (Q.X < 0 || Q.Y < 0 || Q.X >= N || Q.Y >= N) continue;
				const int32 V = G[Q.Y * N + Q.X];
				const bool bOpen = V == -1 || (V > 0 && TowerRooms24[V - 1].Kind == T24_Lobby);
				if (bOpen) Edge.Add(TPair<FIntPoint, int32>(FIntPoint(I, J), D));
			}
		if (Edge.Num() > 0) { const TPair<FIntPoint, int32>& E = Edge[Edge.Num() / 2]; Rm.DoorCell = E.Key; Rm.DoorDir = E.Value; }
	}
}

// ================================================================================================ the tower level: its build
FVector ARDDungeonGenerator::TowerCell24(float I, float J, float Z) const
{
	const float C = TowerCellSize24, W = TowerCells24 * C;
	return FVector((I + 0.5f) * C - W * 0.5f, (J + 0.5f) * C - W * 0.5f, Z);
}

UInstancedStaticMeshComponent* ARDDungeonGenerator::TowerIsm24(UStaticMesh* Mesh, UMaterialInterface* Mat, bool bCollide)
{
	if (!Mesh) return nullptr;
	const FString Key = FString::Printf(TEXT("%s|%s|%d"), *GetNameSafe(Mesh), *GetNameSafe(Mat), bCollide ? 1 : 0);
	if (TObjectPtr<UInstancedStaticMeshComponent>* F = TowerIsms24.Find(Key)) return *F;
	UInstancedStaticMeshComponent* C = NewObject<UInstancedStaticMeshComponent>(this);
	C->SetStaticMesh(Mesh);
	if (Mat) for (int32 S = 0; S < FMath::Max(1, Mesh->GetStaticMaterials().Num()); ++S) C->SetMaterial(S, Mat);
	C->SetMobility(EComponentMobility::Static);
	C->SetCollisionEnabled(bCollide ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
	if (bCollide) C->SetCollisionProfileName(TEXT("BlockAll"));
	C->SetCanEverAffectNavigation(false);
	C->RegisterComponent();
	C->ComponentTags.Add(TEXT("Tower24"));
	TowerIsms24.Add(Key, C);
	return C;
}

void ARDDungeonGenerator::TowerBox24(const FVector& Min, const FVector& Max, UMaterialInterface* Mat, bool bCollide)
{
	// (an engine cube (100 cm, its middle at its origin) stretched over a box)
	UInstancedStaticMeshComponent* C = TowerIsm24(TowerCube24, Mat, bCollide);
	if (!C) return;
	const FVector Sz = (Max - Min).ComponentMax(FVector(0.5f));
	C->AddInstance(FTransform(FRotator::ZeroRotator, (Min + Max) * 0.5f, Sz / 100.f), true);
	++TowerBoxes24;
}

bool ARDDungeonGenerator::TowerPiece24(FName Name, const FVector& At, float Yaw, bool bCollide)
{
	// (a pack's piece by its table entry: its Adjust turns its front to +X and stands it centred on z 0 (948))
	const FRDPiece* P = TowerPieces24.Find(Name);
	if (!P || !P->Mesh) { TowerMissing24.Add(Name); return false; }
	UInstancedStaticMeshComponent* C = TowerIsm24(P->Mesh, P->Material, bCollide && P->bCollision);
	if (!C) return false;
	C->AddInstance(P->Adjust * FTransform(FRotator(0.f, Yaw, 0.f), At), true);
	++TowerProps24;
	return true;
}

FVector ARDDungeonGenerator::TowerPieceSize24(FName Name) const
{
	const FRDPiece* P = TowerPieces24.Find(Name);
	return P ? P->Size : FVector(100.f);
}

void ARDDungeonGenerator::BuildTower24()
{
	const double T0 = FPlatformTime::Seconds();
	for (TPair<FString, TObjectPtr<UInstancedStaticMeshComponent>>& Kv : TowerIsms24) if (Kv.Value) Kv.Value->DestroyComponent();
	TowerIsms24.Reset(); TowerBoxes24 = 0; TowerProps24 = 0; TowerMissing24.Reset(); TowerLines24.Reset();
	PlanTower24();
	const int32 N = TowerCells24, Nf = TowerFloorsNow24;
	const float C = TowerCellSize24, H = TowerStoreyH24, W = N * C, Hw = W * 0.5f;
	const int32 C0 = N / 2 - 2, C1 = N / 2 + 1;
	const float WallT = 12.f, Door = 225.f;
	auto RoomOf = [&](int32 K, int32 I, int32 J) -> int32 { if (I < 0 || J < 0 || I >= N || J >= N) return -3; return TowerPlan24[K][J * N + I]; };
	auto KindOf = [&](int32 V) -> uint8 { return V > 0 ? TowerRooms24[V - 1].Kind : 0; };
	auto FloorMat = [&](uint8 Kd) -> UMaterialInterface*
	{
		switch (Kd)
		{
		case T24_Lobby: return TowerLobbyFloorMat24; case T24_Bath: return TowerTileMat24; case T24_Data: case T24_Closet: return TowerConcreteMat24;
		case T24_Cafe: return TowerWoodMat24; default: return TowerFloorMat24;
		}
	};
	// ---- the stair core's cells: the stairwell (two columns, four rows: r0 the landing at each floor, r1-r2 the flights, r3 the half
	// landing), the two lift shafts
	const int32 Sc0 = C0, Sc1 = C0 + 1;            // (the stair's two columns)
	const int32 R0 = C1, R1 = C1 - 1, R2 = C1 - 2, R3 = C0;          // (its rows: the floor's landing at the north)
	const int32 Lx0 = C0 + 2, Lx1 = C1;            // (the lifts' columns)
	auto InStairOpen = [&](int32 I, int32 J) { return (I == Sc0 || I == Sc1) && (J == R1 || J == R2 || J == R3); };
	auto InShaft = [&](int32 I, int32 J) { return I >= Lx0 && I <= Lx1 && J >= C0 && J <= C1; };
	for (int32 K = 0; K <= Nf; ++K)
	{
		const float Z = K * H;
		const bool bRoof = K == Nf;
		// ---- the floor slab (its top at Z) and the ceiling under it (the storey below's)
		for (int32 I = 0; I < N; ++I)
			for (int32 J = 0; J < N; ++J)
			{
				const FVector P = TowerCell24(I, J, Z);
				const bool bOpen = !bRoof && K > 0 && (InStairOpen(I, J) || InShaft(I, J));
				const bool bShaft = InShaft(I, J);
				if (bOpen || (bShaft && !bRoof)) { /* (open: the flight's way through, the lift's shaft) */ }
				else
				{
					const uint8 Kd = bRoof ? 0 : KindOf(RoomOf(K, I, J));
					UMaterialInterface* Fm = bRoof ? TowerCeilMat24.Get() : RoomOf(K, I, J) == -1 ? TowerFloorMat24.Get() : RoomOf(K, I, J) == -2 ? TowerConcreteMat24.Get() : FloorMat(Kd);
					TowerBox24(P + FVector(-C * 0.5f, -C * 0.5f, -6.f), P + FVector(C * 0.5f, C * 0.5f, 0.f), Fm, true);
					if (K > 0) TowerBox24(P + FVector(-C * 0.5f, -C * 0.5f, -26.f), P + FVector(C * 0.5f, C * 0.5f, -6.f), TowerConcreteMat24, true);
				}
				// (the ceiling's face under the slab, and its lights on every other cell)
				if (K > 0 && !(bShaft && !bRoof) && !(K < Nf && InStairOpen(I, J)))
				{
					TowerBox24(P + FVector(-C * 0.5f, -C * 0.5f, -30.f), P + FVector(C * 0.5f, C * 0.5f, -26.f), TowerCeilMat24, false);
					if ((I + J) % 2 == 0 && RoomOf(K - 1, I, J) != -2) TowerPiece24(TEXT("Tower.CeilingLight"), P + FVector(0, 0, -38.f), 0.f, false);
				}
			}
		if (bRoof) break;
		const float Top = Z + H - 30.f;          // (the walls stand to the ceiling)
		// ---- the facade: glass a cell, a mullion at each cell's edge, a spandrel at the slab
		for (int32 Si = 0; Si < 4; ++Si)
			for (int32 T = 0; T < N; ++T)
			{
				const float A = (T + 0.5f) * C - Hw, A0 = T * C - Hw, A1 = (T + 1) * C - Hw;
				const float Fx = Si == 0 ? -Hw : Si == 1 ? Hw : A, Fy = Si == 2 ? -Hw : Si == 3 ? Hw : A;
				const bool bX = Si < 2;
				const FVector Mn = bX ? FVector(Fx - 4.f, A0, Z) : FVector(A0, Fy - 4.f, Z);
				const FVector Mx = bX ? FVector(Fx + 4.f, A1, Top) : FVector(A1, Fy + 4.f, Top);
				// (the lobby's doors: two cells of the south front, glass doors under a sign)
				const bool bEntry = K == 0 && Si == 2 && (T == N / 2 - 1 || T == N / 2);
				TowerBox24(Mn, Mx, bEntry ? TowerDoorGlassMat24 : TowerGlassMat24, true);
				const FVector M0 = bX ? FVector(Fx - 10.f, A0 - 5.f, Z) : FVector(A0 - 5.f, Fy - 10.f, Z);
				TowerBox24(M0, M0 + FVector(bX ? 20.f : 10.f, bX ? 10.f : 20.f, H), TowerMetalMat24, true);
				const FVector S0 = bX ? FVector(Fx - 8.f, A0, Z) : FVector(A0, Fy - 8.f, Z);
				TowerBox24(S0, S0 + FVector(bX ? 16.f : C, bX ? C : 16.f, 12.f), TowerMetalMat24, true);
			}
		if (K == 0)
		{
			const FVector Dm = TowerCell24(N * 0.5f - 0.5f, 0.f, 0.f);
			TowerExit24 = FVector(Dm.X, -Hw, 0.f);
			TowerPiece24(TEXT("Tower.ExitSign"), FVector(Dm.X, -Hw + 14.f, 260.f), 90.f, false);
		}
		// ---- the walls between rooms, the corridor and the core: on every cell edge between two kinds of space
		for (int32 I = 0; I < N; ++I)
			for (int32 J = 0; J < N; ++J)
				for (int32 D = 1; D <= 3; D += 2)          // (each edge once: +X and +Y)
				{
					const int32 I2 = I + RDT24Dir4[D].X, J2 = J + RDT24Dir4[D].Y;
					if (I2 >= N || J2 >= N) continue;
					const int32 A = RoomOf(K, I, J), B = RoomOf(K, I2, J2);
					if (A == B) continue;
					// (the core's own edges are built with the core)
					if (A == -2 || B == -2) continue;
					// (the lobby open to the corridor it surrounds)
					const uint8 Ka = KindOf(A), Kb = KindOf(B);
					if ((A == -1 && Kb == T24_Lobby) || (B == -1 && Ka == T24_Lobby)) continue;
					const bool bAlongY = D == 1;          // (an edge across +X runs along Y)
					const FVector Mid = TowerCell24(I + (bAlongY ? 0.5f : 0.f), J + (bAlongY ? 0.f : 0.5f), Z);
					// (a doorway: the room's own door cell and way)
					bool bDoor = false;
					for (const int32 V : { A, B })
						if (V > 0)
						{
							const FRoom24& Rm = TowerRooms24[V - 1];
							const FIntPoint Q = Rm.DoorCell + RDT24Dir4[Rm.DoorDir];
							if ((Rm.DoorCell == FIntPoint(I, J) && Q == FIntPoint(I2, J2)) || (Rm.DoorCell == FIntPoint(I2, J2) && Q == FIntPoint(I, J))) bDoor = true;
						}
					const bool bGlass = Ka == T24_Meeting || Kb == T24_Meeting || Ka == T24_Board || Kb == T24_Board;
					UMaterialInterface* Wm = bGlass && (A == -1 || B == -1) ? TowerInnerGlassMat24 : (Ka == T24_Bath || Kb == T24_Bath) ? TowerTileWallMat24 : TowerWallMat24;
					const FVector Ext = bAlongY ? FVector(WallT * 0.5f, C * 0.5f + WallT * 0.5f, 0.f) : FVector(C * 0.5f + WallT * 0.5f, WallT * 0.5f, 0.f);
					if (bDoor)
					{
						TowerBox24(Mid - Ext + FVector(0, 0, Door), Mid + Ext + FVector(0, 0, Top - Z), TowerWallMat24, true);          // (the lintel)
						const FVector Fr = bAlongY ? FVector(0, C * 0.5f - 4.f, 0) : FVector(C * 0.5f - 4.f, 0, 0);
						for (const float Sg : { -1.f, 1.f })
							TowerBox24(Mid + Fr * Sg - FVector(WallT, WallT, 0) * 0.6f, Mid + Fr * Sg + FVector(WallT, WallT, 0) * 0.6f + FVector(0, 0, Door), TowerMetalMat24, true);
					}
					else TowerBox24(Mid - Ext, Mid + Ext + FVector(0, 0, Top - Z), Wm, true);
				}
		// ---- the core: its outer walls (the stair's door on the north, the lifts' on the east), the walls between stair and lifts and
		// between the two lifts
		{
			const FVector Lo = TowerCell24(C0 - 0.5f, C0 - 0.5f, Z), Hi = TowerCell24(C1 + 0.5f, C1 + 0.5f, Z);
			const float T2 = 15.f;
			TowerBox24(FVector(Lo.X - T2, Lo.Y - T2, Z), FVector(Hi.X + T2, Lo.Y + T2, Top), TowerCoreMat24, true);          // (south)
			TowerBox24(FVector(Lo.X - T2, Lo.Y, Z), FVector(Lo.X + T2, Hi.Y, Top), TowerCoreMat24, true);                      // (west)
			// (north: the stair's door over its two columns, a wall over the lifts')
			const float Xs = TowerCell24(Sc1 + 0.5f, 0, 0).X;
			TowerBox24(FVector(Xs, Hi.Y - T2, Z), FVector(Hi.X + T2, Hi.Y + T2, Top), TowerCoreMat24, true);
			TowerBox24(FVector(Lo.X - T2, Hi.Y - T2, Z + Door + 20.f), FVector(Xs, Hi.Y + T2, Top), TowerCoreMat24, true);
			// (east: the lift doors at the middle rows, walls at the ends and above)
			const float Yl0 = TowerCell24(0, C0 + 0.5f, 0).Y, Yl1 = TowerCell24(0, C1 - 0.5f, 0).Y, Ym = TowerCell24(0, C0 + 1.5f, 0).Y;
			TowerBox24(FVector(Hi.X - T2, Lo.Y, Z), FVector(Hi.X + T2, Yl0, Top), TowerCoreMat24, true);
			TowerBox24(FVector(Hi.X - T2, Yl1, Z), FVector(Hi.X + T2, Hi.Y, Top), TowerCoreMat24, true);
			TowerBox24(FVector(Hi.X - T2, Ym - T2, Z), FVector(Hi.X + T2, Ym + T2, Top), TowerCoreMat24, true);
			TowerBox24(FVector(Hi.X - T2, Yl0, Z + Door + 20.f), FVector(Hi.X + T2, Yl1, Top), TowerCoreMat24, true);
			// (between the stair and the lifts; between the lifts)
			const float Xl = TowerCell24(Lx0 - 0.5f, 0, 0).X;
			TowerBox24(FVector(Xl - T2, Lo.Y, Z), FVector(Xl + T2, Hi.Y, Top + 30.f), TowerCoreMat24, true);
			TowerBox24(FVector(Xl, Ym - T2, Z), FVector(Hi.X, Ym + T2, Top + 30.f), TowerCoreMat24, true);
		}
		// ---- the stair: flight A up the west column from the landing to the half landing, flight B up the east column back to the next
		// floor's landing; thin treads (a solid flight stood in the head room of the one below), the wall between the flights
		if (K < Nf - 1)
		{
			const float Ya = TowerCell24(0, R1 + 0.5f, 0).Y;          // (the landing's edge)
			const float Yb = TowerCell24(0, R3 + 0.5f, 0).Y;          // (the half landing's edge)
			const float Run = (Ya - Yb) / 10.f, Rise = H * 0.5f / 10.f;
			const float XaL = TowerCell24(Sc0 - 0.5f, 0, 0).X + 2.f, XaR = TowerCell24(Sc0 + 0.5f, 0, 0).X - 6.f;
			const float XbL = TowerCell24(Sc1 - 0.5f, 0, 0).X + 6.f, XbR = TowerCell24(Sc1 + 0.5f, 0, 0).X - 2.f;
			for (int32 S = 0; S < 10; ++S)
			{
				const float Za = Z + (S + 1) * Rise;
				TowerBox24(FVector(XaL, Ya - (S + 1) * Run, Za - 30.f), FVector(XaR, Ya - S * Run, Za), TowerStairMat24, true);
				const float Zb = Z + H * 0.5f + (S + 1) * Rise;
				TowerBox24(FVector(XbL, Yb + S * Run, Zb - 30.f), FVector(XbR, Yb + (S + 1) * Run, Zb), TowerStairMat24, true);
			}
			const FVector Hl0 = TowerCell24(Sc0 - 0.5f, R3 - 0.5f, 0), Hl1 = TowerCell24(Sc1 + 0.5f, R3 + 0.5f, 0);
			TowerBox24(FVector(Hl0.X, Hl0.Y, Z + H * 0.5f - 20.f), FVector(Hl1.X, Hl1.Y, Z + H * 0.5f), TowerStairMat24, true);
			const float Xm = TowerCell24(Sc0 + 0.5f, 0, 0).X;
			TowerBox24(FVector(Xm - 6.f, Yb, Z), FVector(Xm + 6.f, Ya, Z + H), TowerCoreMat24, true);
			TowerStairs24.Add(FString::Printf(TEXT("stair|%d|%.0f|%.0f|%.0f|%.0f|%.0f|%.0f"), K, (XaL + XaR) * 0.5f, Ya + C * 0.5f, Z, (XbL + XbR) * 0.5f, Ya + C * 0.5f, Z + H));
		}
		else
		{
			// (the top floor: a rail across the foot of the flight that is not there)
			const float Ya = TowerCell24(0, R1 + 0.5f, 0).Y;
			TowerBox24(FVector(TowerCell24(Sc0 - 0.5f, 0, 0).X, Ya - 3.f, Z), FVector(TowerCell24(Sc0 + 0.5f, 0, 0).X, Ya + 3.f, Z + 105.f), TowerMetalMat24, true);
			const float Yb = TowerCell24(0, R3 + 0.5f, 0).Y, Xm = TowerCell24(Sc0 + 0.5f, 0, 0).X;
			TowerBox24(FVector(Xm - 6.f, Yb - C, Z), FVector(Xm + 6.f, Ya, Z + 105.f), TowerMetalMat24, true);
		}
	}
	// ---- the rooms furnished
	for (int32 Ri = 0; Ri < TowerRooms24.Num(); ++Ri) FurnishTower24(Ri);
	// ---- the lifts: A at the north shaft stopping at every floor, B at the south one between the lobby and the top
	TowerLifts24.Reset();
	for (int32 L = 0; L < 2; ++L)
	{
		FTowerLift24 Lf;
		Lf.bExpress = L == 1;
		Lf.Shaft = TowerCell24(Lx0 + 0.5f, L == 0 ? C1 - 0.5f : C0 + 0.5f, 0.f);
		Lf.Entry = FVector(1, 0, 0);
		// (its door: the row nearer the other lift (the core's east face is walled at its two ends))
		Lf.Door = FVector(TowerCell24(Lx1 + 0.5f, 0, 0).X, TowerCell24(0, L == 0 ? C0 + 2 : C0 + 1, 0).Y, 0.f);
		for (int32 K = 0; K < Nf; ++K) if (!Lf.bExpress || K == 0 || K == Nf - 1) Lf.Floors.Add(K * H);
		UStaticMeshComponent* P = NewObject<UStaticMeshComponent>(this);
		P->SetMobility(EComponentMobility::Movable);
		P->SetStaticMesh(TowerCube24);
		if (TowerLiftMat24) P->SetMaterial(0, TowerLiftMat24);
		P->SetCollisionProfileName(TEXT("BlockAllDynamic"));
		P->SetCastShadow(false);
		P->SetWorldScale3D(FVector((2.f * C - 20.f) / 100.f, (2.f * C - 20.f) / 100.f, 0.2f));
		P->RegisterComponent();
		P->SetWorldLocation(Lf.Shaft - FVector(0, 0, 10.f));
		P->ComponentTags.Add(TEXT("TowerLift24"));
		Lf.Platform = P;
		for (int32 K = 0; K < Lf.Floors.Num(); ++K)
		{
			UBoxComponent* G = NewObject<UBoxComponent>(this);
			G->SetBoxExtent(FVector(6.f, C * 0.5f - 10.f, 130.f));
			G->SetCollisionProfileName(TEXT("BlockAll"));
			G->SetHiddenInGame(true);
			G->RegisterComponent();
			G->SetWorldLocation(FVector(Lf.Door.X + 20.f, Lf.Door.Y, Lf.Floors[K] + 132.f));
			Lf.Gates.Add(G);
		}
		// (every other floor's opening barred for the express: a shut gate a floor it does not stop at)
		if (Lf.bExpress)
			for (int32 K = 1; K < Nf - 1; ++K)
			{
				UBoxComponent* G = NewObject<UBoxComponent>(this);
				G->SetBoxExtent(FVector(6.f, C * 0.5f - 10.f, 130.f));
				G->SetCollisionProfileName(TEXT("BlockAll"));
				G->SetHiddenInGame(true);
				G->RegisterComponent();
				G->SetWorldLocation(FVector(Lf.Door.X + 20.f, Lf.Door.Y, K * H + 132.f));
				Lf.Bars.Add(G);
			}
		Lf.Z = Lf.Floors[0];
		TowerLifts24.Add(Lf);
		UpdateTowerGates24(TowerLifts24.Last());
	}
	// ---- the city outside: a sphere round the tower drawn with the picture of its floor's height
	if (TowerSphere24 && TowerViewMat24)
	{
		UStaticMeshComponent* Sp = NewObject<UStaticMeshComponent>(this);
		Sp->SetMobility(EComponentMobility::Movable);
		Sp->SetStaticMesh(TowerSphere24);
		Sp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Sp->SetCastShadow(false);
		Sp->SetWorldScale3D(FVector(TowerViewRadius24 / 50.f));
		Sp->RegisterComponent();
		TowerViewMID24 = UMaterialInstanceDynamic::Create(TowerViewMat24, this);
		Sp->SetMaterial(0, TowerViewMID24);
		TowerSphereC24 = Sp;
		TowerViewIndex24 = -1;
	}
	// ---- the lights near her (made once, moved to her floor's rooms as she changes floor)
	for (TObjectPtr<UPointLightComponent>& L : TowerLights24) if (L) L->DestroyComponent();
	TowerLights24.Reset();
	for (int32 I = 0; I < TowerLightCount24; ++I)
	{
		UPointLightComponent* L = NewObject<UPointLightComponent>(this);
		L->SetMobility(EComponentMobility::Movable);
		L->SetIntensityUnits(ELightUnits::Candelas);
		L->SetIntensity(TowerLightCd24);
		L->SetAttenuationRadius(1100.f);
		L->SetCastShadows(false);
		L->SetLightColor(FLinearColor(1.f, 0.97f, 0.92f));
		L->RegisterComponent();
		L->SetVisibility(false);
		TowerLights24.Add(L);
	}
	TowerLightFloor24 = -1;
	// (her start: inside the lobby's doors, facing in)
	TowerStart24 = TowerCell24(N * 0.5f - 0.5f, 1.5f, 100.f);
	bTowerPlaced24 = false;
	TowerLines24.Add(FString::Printf(TEXT("tower|%s|%d|%d|%d|%.0f|%.0f"), *TowerNameNow24, TowerSeedNow24, Nf, N, C, H));
	for (int32 Ri = 0; Ri < TowerRooms24.Num(); ++Ri)
	{
		const FRoom24& Rm = TowerRooms24[Ri];
		const FVector A = TowerCell24(Rm.Min.X, Rm.Min.Y, Rm.Floor * H), B = TowerCell24(Rm.Max.X, Rm.Max.Y, Rm.Floor * H);
		const FVector Dc = TowerCell24(Rm.DoorCell.X, Rm.DoorCell.Y, Rm.Floor * H);
		TowerLines24.Add(FString::Printf(TEXT("room|%d|%d|%s|%.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%d|%d"), Ri, Rm.Floor, RDT24KindName(Rm.Kind), A.X, A.Y, B.X, B.Y, Dc.X, Dc.Y, Rm.DoorDir, Rm.Props));
	}
	for (const FString& S : TowerStairs24) TowerLines24.Add(S);
	TowerStairs24.Reset();
	UE_LOG(LogRDTower24, Log, TEXT("RDTOWER24 built %s: %d floors, %d rooms, %d boxes, %d props in %d components, %.0f ms%s"), *TowerNameNow24, Nf, TowerRooms24.Num(),
		TowerBoxes24, TowerProps24, TowerIsms24.Num(), (FPlatformTime::Seconds() - T0) * 1000.0, TowerMissing24.Num() ? *FString::Printf(TEXT(" (missing pieces: %d)"), TowerMissing24.Num()) : TEXT(""));
	for (const FName& Mn : TowerMissing24) UE_LOG(LogRDTower24, Warning, TEXT("RDTOWER24 no piece %s"), *Mn.ToString());
}

// ================================================================================================ the rooms' furniture
void ARDDungeonGenerator::FurnishTower24(int32 Ri)
{
	FRoom24& Rm = TowerRooms24[Ri];
	const float C = TowerCellSize24, H = TowerStoreyH24;
	const float Z = Rm.Floor * H;
	FRandomStream R((TowerSeedNow24 * 131) ^ (Ri * 977 + 3));
	const int32 Before = TowerProps24;
	const FVector Lo = TowerCell24(Rm.Min.X - 0.5f, Rm.Min.Y - 0.5f, Z), Hi = TowerCell24(Rm.Max.X + 0.5f, Rm.Max.Y + 0.5f, Z);
	const float Lx = Hi.X - Lo.X, Ly = Hi.Y - Lo.Y;
	const bool bLong = Lx >= Ly;          // (the room's long way)
	const FVector Ctr = (Lo + Hi) * 0.5f;
	const FVector DoorAt = TowerCell24(Rm.DoorCell.X, Rm.DoorCell.Y, Z);
	const FVector DoorOut(RDT24Dir4[Rm.DoorDir].X, RDT24Dir4[Rm.DoorDir].Y, 0.f);
	// (kept clear: the door's cell and the cell before it inside)
	auto NearDoor = [&](const FVector& P, float Rad) { return FVector::Dist2D(P, DoorAt) < Rad + C * 0.75f; };
	// (a piece against a wall: its back to the wall on the side Side (0 -X, 1 +X, 2 -Y, 3 +Y) at the share U along it)
	auto Against = [&](FName Nm, int32 Side, float U, bool bCollide = true) -> bool
	{
		const FVector Sz = TowerPieceSize24(Nm);
		const FVector In = -FVector(RDT24Dir4[Side].X, RDT24Dir4[Side].Y, 0.f);
		const float Yaw = In.Rotation().Yaw;
		const float Gap = 12.f + Sz.X * 0.5f;
		FVector P;
		if (Side < 2) P = FVector(Side == 0 ? Lo.X + Gap : Hi.X - Gap, FMath::Lerp(Lo.Y + Sz.Y * 0.5f + 15.f, Hi.Y - Sz.Y * 0.5f - 15.f, U), Z);
		else P = FVector(FMath::Lerp(Lo.X + Sz.Y * 0.5f + 15.f, Hi.X - Sz.Y * 0.5f - 15.f, U), Side == 2 ? Lo.Y + Gap : Hi.Y - Gap, Z);
		if (NearDoor(P, FMath::Max(Sz.X, Sz.Y) * 0.5f)) return false;
		return TowerPiece24(Nm, P, Yaw, bCollide);
	};
	// (the sides that are inner walls (not the facade, not the door's): the facade's sides are those at the floor's edge)
	const int32 N = TowerCells24;
	auto IsFacade = [&](int32 Side) { return (Side == 0 && Rm.Min.X == 0) || (Side == 1 && Rm.Max.X == N - 1) || (Side == 2 && Rm.Min.Y == 0) || (Side == 3 && Rm.Max.Y == N - 1); };
	const int32 DoorSide = Rm.DoorDir;          // (the side the door is on)
	auto WallSides = [&]() { TArray<int32> S; for (int32 Sd = 0; Sd < 4; ++Sd) if (!IsFacade(Sd) && Sd != DoorSide) S.Add(Sd); return S; };
	// (a solid wall: another room beyond it, not the corridor (a meeting room's corridor side is glass))
	auto SolidSide = [&](int32 Sd)
	{
		const FIntPoint Mid((Rm.Min.X + Rm.Max.X) / 2, (Rm.Min.Y + Rm.Max.Y) / 2);
		const FIntPoint Q = Sd == 0 ? FIntPoint(Rm.Min.X - 1, Mid.Y) : Sd == 1 ? FIntPoint(Rm.Max.X + 1, Mid.Y) : Sd == 2 ? FIntPoint(Mid.X, Rm.Min.Y - 1) : FIntPoint(Mid.X, Rm.Max.Y + 1);
		if (Q.X < 0 || Q.Y < 0 || Q.X >= N || Q.Y >= N) return false;
		return TowerPlan24[Rm.Floor][Q.Y * N + Q.X] > 0;
	};
	switch (Rm.Kind)
	{
	case T24_Lobby:
	{
		// (the reception desk before the core facing the doors, seats in the corners by the windows, planters, palms)
		TowerPiece24(TEXT("Tower.Reception"), TowerCell24(N * 0.5f - 0.5f, N * 0.5f - 3.6f, Z), -90.f);
		TowerPiece24(TEXT("Tower.OfficeChair"), TowerCell24(N * 0.5f - 0.5f, N * 0.5f - 2.9f, Z), -90.f);
		// (two seating groups by the front windows either side of the doors (the east band's bathrooms begin past the south band))
		for (const float Sx : { 2.5f, (float)N - 3.5f })
		{
			TowerPiece24(TEXT("Tower.SofaBig"), TowerCell24(Sx, 0.45f, Z), 90.f);
			TowerPiece24(TEXT("Tower.SofaTable"), TowerCell24(Sx, 1.35f, Z), 0.f);
			TowerPiece24(TEXT("Tower.SofaSmall"), TowerCell24(Sx, 2.3f, Z), -90.f);
			TowerPiece24(TEXT("Tower.Palm"), TowerCell24(Sx < N * 0.5f ? 0.5f : N - 1.5f, 0.6f, Z), 0.f, false);
		}
		for (int32 I = 2; I < N - 2; I += 3) TowerPiece24(TEXT("Tower.PlanterBox"), TowerCell24(I, N - 1.25f, Z), 180.f);
		TowerPiece24(TEXT("Tower.WaterDispenser"), TowerCell24(0.4f, N * 0.5f, Z), 0.f);
		TowerPiece24(TEXT("Tower.Planter"), TowerCell24(N * 0.5f - 3.2f, 0.6f, Z), 0.f);
		TowerPiece24(TEXT("Tower.Planter"), TowerCell24(N * 0.5f + 2.2f, 0.6f, Z), 0.f);
		break;
	}
	case T24_Office: case T24_Exec:
	{
		// (a desk a 3 m by 3 m of room, the chair behind it, the screen and computer on it; shelving and drawers against the walls; a
		// plant in a corner)
		const int32 Desks = FMath::Max(1, FMath::RoundToInt(Lx * Ly / (Rm.Kind == T24_Exec ? 2000000.f : 1100000.f)));
		const TArray<int32> Ws = WallSides();
		for (int32 D = 0; D < Desks; ++D)
		{
			const float U = (D + 0.5f) / Desks;
			const FVector P = bLong ? FVector(FMath::Lerp(Lo.X, Hi.X, U), Ctr.Y, Z) : FVector(Ctr.X, FMath::Lerp(Lo.Y, Hi.Y, U), Z);
			if (NearDoor(P, 120.f)) continue;
			// (the desk faces the door's side of the room: the one sitting at it looks at the door)
			const float Yaw = DoorOut.Rotation().Yaw;
			TowerPiece24(TEXT("Tower.Desk"), P, Yaw);
			const FVector F = FRotator(0, Yaw, 0).Vector();
			TowerPiece24(TEXT("Tower.OfficeChair"), P - F * 75.f, Yaw);
			const float Dh = TowerPieceSize24(TEXT("Tower.Desk")).Z;
			TowerPiece24(TEXT("Tower.Monitor"), P + F * 25.f + FVector(0, 0, Dh), Yaw + 180.f, false);
			TowerPiece24(TEXT("Tower.Keyboard"), P - F * 20.f + FVector(0, 0, Dh), Yaw + 180.f, false);
		}
		for (int32 K = 0; K < Ws.Num(); ++K)
		{
			const FName Nm = Rm.Kind == T24_Exec ? FName(TEXT("Tower.BookshelfLong")) : (R.FRand() < 0.5f ? FName(TEXT("Tower.Shelving")) : FName(TEXT("Tower.Drawers")));
			Against(Nm, Ws[K], R.FRandRange(0.2f, 0.8f));
			if (R.FRand() < 0.5f) Against(TEXT("Tower.CorkBoard"), Ws[K], R.FRandRange(0.1f, 0.9f), false);
		}
		Against(TEXT("Tower.Planter"), Ws.Num() ? Ws[0] : 0, R.FRand() < 0.5f ? 0.02f : 0.98f);
		if (Rm.Kind == T24_Exec && Ws.Num()) Against(TEXT("Tower.Painting"), Ws.Last(), 0.5f, false);
		break;
	}
	case T24_Cubicles:
	{
		// (pods of 3 m by 3 m along the window side, the aisle along the corridor's: a desk, a chair, a screen and computer, screens
		// between the pods and at their aisle's ends)
		const bool bAlongX = bLong;
		const float Depth = bAlongX ? Ly : Lx;
		const float AisleSide = bAlongX ? (DoorOut.Y > 0 ? 1.f : -1.f) : (DoorOut.X > 0 ? 1.f : -1.f);          // (the corridor's side)
		const int32 Pods = FMath::Max(1, FMath::FloorToInt((bAlongX ? Lx : Ly) / 300.f));
		const float PodDepth = FMath::Min(300.f, Depth - 140.f);
		for (int32 Pd = 0; Pd < Pods; ++Pd)
		{
			const float A0 = (bAlongX ? Lo.X : Lo.Y) + Pd * ((bAlongX ? Lx : Ly) / Pods), A1 = A0 + (bAlongX ? Lx : Ly) / Pods;
			const float Am = (A0 + A1) * 0.5f;
			// (the pod's middle across: the window's side of the room)
			const float Win = bAlongX ? (AisleSide > 0 ? Lo.Y : Hi.Y) : (AisleSide > 0 ? Lo.X : Hi.X);
			const float Cm = Win + AisleSide * (PodDepth * 0.5f);
			const FVector P = bAlongX ? FVector(Am, Cm, Z) : FVector(Cm, Am, Z);
			if (NearDoor(P, 100.f)) continue;
			const float Yaw = (bAlongX ? FVector(0, AisleSide, 0) : FVector(AisleSide, 0, 0)).Rotation().Yaw;          // (facing the aisle)
			const FVector F = FRotator(0, Yaw, 0).Vector();
			TowerPiece24(TEXT("Tower.Desk"), P - F * 30.f, Yaw);
			TowerPiece24(TEXT("Tower.OfficeChair"), P + F * 45.f, Yaw + 180.f);          // (the one sitting faces the window's way, at the desk)
			TowerPiece24(TEXT("Tower.Monitor"), P - F * 55.f + FVector(0, 0, TowerPieceSize24(TEXT("Tower.Desk")).Z), Yaw, false);
			TowerPiece24(TEXT("Tower.PcTower"), P - F * 60.f + FRotator(0, Yaw + 90.f, 0).Vector() * 70.f, Yaw);
			// (the screens: at the pod's far edge along, three panels across its depth)
			for (int32 Q = 0; Q < 3; ++Q)
			{
				const float Cq = Win + AisleSide * (50.f + Q * 100.f);
				if (AisleSide * (Cq - Win) > PodDepth) break;
				const FVector Sp = bAlongX ? FVector(A1, Cq, Z) : FVector(Cq, A1, Z);
				TowerPiece24(TEXT("Tower.Partition"), Sp, bAlongX ? 0.f : 90.f);          // (a panel runs along its own Y)
			}
		}
		const TArray<int32> Ws = WallSides();
		for (const int32 Sd : Ws) Against(TEXT("Tower.Printer"), Sd, 0.5f);
		break;
	}
	case T24_Meeting: case T24_Board:
	{
		// (the table along the room's length, chairs round it, a whiteboard on an inner wall)
		const bool bBig = (bLong ? Lx : Ly) >= 650.f;
		const FName Tb = bBig ? FName(TEXT("Tower.BoardTable")) : FName(TEXT("Tower.LunchTable"));
		const float Yaw = bLong ? 0.f : 90.f;
		TowerPiece24(Tb, Ctr, Yaw + (bBig ? 0.f : 90.f));
		const FVector Ts = TowerPieceSize24(Tb);
		const float Len = bBig ? Ts.X : Ts.Y, Wd = bBig ? Ts.Y : Ts.X;
		const FVector Al = FRotator(0, Yaw, 0).Vector(), Ac = FRotator(0, Yaw + 90.f, 0).Vector();
		const int32 Per = FMath::Max(2, FMath::FloorToInt(Len / 90.f));
		for (int32 Q = 0; Q < Per; ++Q)
		{
			const float U = (Q + 0.5f) / Per - 0.5f;
			for (const float Sg : { -1.f, 1.f }) TowerPiece24(TEXT("Tower.Chair"), Ctr + Al * (U * Len) + Ac * Sg * (Wd * 0.5f + 30.f), (Ac * -Sg).Rotation().Yaw);
		}
		const TArray<int32> Ws = WallSides();
		for (const int32 Sd : Ws) if (SolidSide(Sd)) { Against(TEXT("Tower.Whiteboard"), Sd, 0.5f, false); break; }
		break;
	}
	case T24_Bath:
	{
		// (toilets in stalls along the inner wall farthest from the door, sinks along the next one, a towel dispenser, a bin)
		TArray<int32> Ws = WallSides();
		const int32 Far = Ws.Num() ? Ws[0] : (DoorSide ^ 1);
		const bool bAlongY = Far < 2;
		const float Span = bAlongY ? Ly : Lx;
		const int32 Stalls = FMath::Clamp(FMath::FloorToInt((Span - 160.f) / 100.f), 1, 4);
		for (int32 S = 0; S < Stalls; ++S)
		{
			const float U = (S + 0.5f) / Stalls;
			const FVector In = -FVector(RDT24Dir4[Far].X, RDT24Dir4[Far].Y, 0.f);
			const FVector Wall = Far == 0 ? FVector(Lo.X, 0, Z) : Far == 1 ? FVector(Hi.X, 0, Z) : Far == 2 ? FVector(0, Lo.Y, Z) : FVector(0, Hi.Y, Z);
			const FVector Along = bAlongY ? FVector(Wall.X, FMath::Lerp(Lo.Y + 60.f, Hi.Y - 60.f, U), Z) : FVector(FMath::Lerp(Lo.X + 60.f, Hi.X - 60.f, U), Wall.Y, Z);
			const FVector P = Along + In * 45.f;
			if (NearDoor(P, 60.f)) continue;
			TowerPiece24(TEXT("Tower.Toilet"), P, In.Rotation().Yaw);
			// (the stall's sides: panels out from the wall between the toilets)
			const float Step = Span / Stalls;
			const FVector Sd = bAlongY ? FVector(0, Step * 0.5f, 0) : FVector(Step * 0.5f, 0, 0);
			for (const float Sg : { -1.f, 1.f }) TowerPiece24(TEXT("Tower.Partition"), Along + In * 55.f + Sd * Sg, (bAlongY ? 90.f : 0.f));
		}
		if (Ws.Num() > 1) { Against(TEXT("Tower.Sink"), Ws[1], 0.35f); Against(TEXT("Tower.Sink"), Ws[1], 0.7f); Against(TEXT("Tower.TowelDispenser"), Ws[1], 0.95f, false); }
		else
		{
			// (one inner wall: the sinks by the window's side)
			for (int32 Sd = 0; Sd < 4; ++Sd) if (IsFacade(Sd)) { Against(TEXT("Tower.Sink"), Sd, 0.5f); break; }
		}
		Against(TEXT("Tower.Bin"), Far, 0.02f);
		break;
	}
	case T24_Closet:
	{
		const TArray<int32> Ws = WallSides();
		for (int32 K = 0; K < Ws.Num(); ++K) Against(TEXT("Tower.StorageShelving"), Ws[K], 0.5f);
		const FVector P = Ctr;
		if (!NearDoor(P, 60.f)) TowerPiece24(R.FRand() < 0.5f ? FName(TEXT("Tower.CleaningCart")) : FName(TEXT("Tower.Generator")), P, R.FRandRange(0.f, 360.f));
		for (int32 Sd = 0; Sd < 4; ++Sd) if (IsFacade(Sd)) { Against(TEXT("Tower.Mop"), Sd, 0.15f, false); Against(TEXT("Tower.Archive"), Sd, 0.6f); break; }
		break;
	}
	case T24_Cafe:
	{
		// (the counter along an inner wall: kitchen units, a sink, the fridge; tables with chairs in rows by the windows)
		const TArray<int32> Ws = WallSides();
		if (Ws.Num())
		{
			Against(TEXT("Tower.Kitchen"), Ws[0], 0.25f); Against(TEXT("Tower.KitchenSink"), Ws[0], 0.45f); Against(TEXT("Tower.Kitchen"), Ws[0], 0.65f);
			Against(TEXT("Tower.Fridge"), Ws[0], 0.85f); Against(TEXT("Tower.WaterDispenser"), Ws[0], 0.05f);
		}
		const int32 Rows = FMath::Max(1, FMath::FloorToInt((bLong ? Lx : Ly) / 260.f));
		for (int32 Q = 0; Q < Rows; ++Q)
		{
			const float U = (Q + 0.5f) / Rows;
			const FVector P = bLong ? FVector(FMath::Lerp(Lo.X, Hi.X, U), Ctr.Y + (DoorOut.Y > 0 ? -60.f : 60.f), Z) : FVector(Ctr.X + (DoorOut.X > 0 ? -60.f : 60.f), FMath::Lerp(Lo.Y, Hi.Y, U), Z);
			if (NearDoor(P, 110.f)) continue;
			const float Yaw = bLong ? 90.f : 0.f;          // (the table's long way across the room)
			TowerPiece24(TEXT("Tower.LunchTable"), P, Yaw + 90.f);
			const FVector Ac = FRotator(0, Yaw + 90.f, 0).Vector();
			const FVector Al = FRotator(0, Yaw, 0).Vector();
			for (const float Sg : { -1.f, 1.f }) for (const float Uq : { -0.5f, 0.5f })
				TowerPiece24(TEXT("Tower.Chair"), P + Al * (Uq * 100.f) + Ac * Sg * 85.f, (Ac * -Sg).Rotation().Yaw);
		}
		break;
	}
	case T24_Data:
	{
		// (racks in two rows facing a cold aisle down the room's middle, a cooling unit at each end)
		const bool bAlongX = bLong;
		const float Len = bAlongX ? Lx : Ly;
		const int32 Racks = FMath::Max(1, FMath::FloorToInt((Len - 300.f) / 135.f));
		for (int32 Q = 0; Q < Racks; ++Q)
		{
			const float A = (bAlongX ? Lo.X : Lo.Y) + 150.f + (Q + 0.5f) * ((Len - 300.f) / Racks);
			for (const float Sg : { -1.f, 1.f })
			{
				const float Across = (bAlongX ? Ctr.Y : Ctr.X) + Sg * 120.f;
				const FVector P = bAlongX ? FVector(A, Across, Z) : FVector(Across, A, Z);
				if (NearDoor(P, 80.f)) continue;
				const FVector Face = bAlongX ? FVector(0, -Sg, 0) : FVector(-Sg, 0, 0);
				TowerPiece24(TEXT("Tower.ServerRack"), P, Face.Rotation().Yaw);
			}
		}
		for (const int32 Sd : WallSides()) Against(TEXT("Tower.Chiller"), Sd, 0.5f);
		break;
	}
	default: break;
	}
	Rm.Props = TowerProps24 - Before;
}

// ================================================================================================ play
void ARDDungeonGenerator::BeginTower24()
{
	// (the castle's saved sets go: the level is the tower alone)
	for (auto& KV : Sections) if (KV.Value) KV.Value->Destroy();
	Sections.Reset();
	MapData.Reset();
	// (the castle's height fog lay over the city's picture as a white haze (the picture's sphere 80 m out): no fog indoors)
	for (TObjectIterator<UExponentialHeightFogComponent> It; It; ++It) if (It->GetWorld() == GetWorld()) It->SetVisibility(false);
	// (nor bloom: the picture's sky, as bright as a real one, bloomed over the whole window as a white haze)
	if (!TowerPost24)
	{
		TowerPost24 = NewObject<UPostProcessComponent>(this);
		TowerPost24->bUnbound = true; TowerPost24->Priority = 1000.f;
		TowerPost24->Settings.bOverride_BloomIntensity = true; TowerPost24->Settings.BloomIntensity = 0.f;
		TowerPost24->Settings.bOverride_LensFlareIntensity = true; TowerPost24->Settings.LensFlareIntensity = 0.f;
		TowerPost24->RegisterComponent();
	}
	BuildTower24();
}

void ARDDungeonGenerator::UpdateTowerGates24(FTowerLift24& L)
{
	for (int32 K = 0; K < L.Gates.Num(); ++K)
		if (UPrimitiveComponent* G = L.Gates[K].Get())
			G->SetCollisionEnabled(!L.bMoving && L.At == K ? ECollisionEnabled::NoCollision : ECollisionEnabled::QueryAndPhysics);
}

void ARDDungeonGenerator::TickTower24(float Dt)
{
	APawn* Pw = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Pw) return;
	if (!bTowerPlaced24)
	{
		// (put inside the lobby's doors, facing in, once she stands in the level)
		bTowerPlaced24 = true;
		Pw->SetActorLocationAndRotation(TowerStart24, FRotator(0.f, 90.f, 0.f), false, nullptr, ETeleportType::TeleportPhysics);
		if (AController* Pc = Pw->GetController()) Pc->SetControlRotation(FRotator(-10.f, 90.f, 0.f));
		if (ACharacter* Ch = Cast<ACharacter>(Pw)) Ch->GetCharacterMovement()->StopMovementImmediately();
		if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("%s: %d floors"), *TowerNameNow24, TowerFloorsNow24));
		WriteTestMark(TEXT("tower"), TowerNameNow24);          // (-RDMarkFile: the packaged game's run got here, the tower built round her)
	}
	const FVector Her = Pw->GetActorLocation();
	// ---- the lifts
	for (FTowerLift24& L : TowerLifts24)
	{
		if (!L.Floors.IsValidIndex(L.Target)) continue;
		const float Want = L.Floors[L.Target];
		if (FMath::Abs(L.Z - Want) < 0.5f) { if (L.bMoving) { L.bMoving = false; L.At = L.Target; L.Z = Want; UpdateTowerGates24(L); } continue; }
		if (!L.bMoving) { L.bMoving = true; UpdateTowerGates24(L); }
		L.Z = FMath::FInterpConstantTo(L.Z, Want, Dt, TowerLiftSpeed24);
		if (UStaticMeshComponent* P = L.Platform.Get()) P->SetWorldLocation(FVector(L.Shaft.X, L.Shaft.Y, L.Z - 10.f));
	}
	// ---- the floor she is on: its lights, the city's picture for its height
	const int32 Floor = FMath::Clamp(FMath::FloorToInt((Her.Z - 40.f) / TowerStoreyH24 + 0.05f), 0, TowerFloorsNow24 - 1);
	TowerFloorNow24 = Floor;
	if (Floor != TowerLightFloor24)
	{
		TowerLightFloor24 = Floor;
		int32 Li = 0;
		const float Zc = Floor * TowerStoreyH24 + TowerStoreyH24 - 70.f;
		auto Put = [&](const FVector& P) { if (TowerLights24.IsValidIndex(Li)) { TowerLights24[Li]->SetWorldLocation(FVector(P.X, P.Y, Zc)); TowerLights24[Li]->SetVisibility(true); ++Li; } };
		for (const FRoom24& Rm : TowerRooms24)
		{
			if (Rm.Floor != Floor) continue;
			const FVector A = TowerCell24(Rm.Min.X, Rm.Min.Y, 0.f), B = TowerCell24(Rm.Max.X, Rm.Max.Y, 0.f);
			// (a big room (the lobby, a band) a light every 6 m along it)
			const int32 Nx = FMath::Max(1, FMath::RoundToInt((B.X - A.X) / 600.f)), Ny = FMath::Max(1, FMath::RoundToInt((B.Y - A.Y) / 600.f));
			for (int32 I = 0; I < Nx; ++I) for (int32 J = 0; J < Ny; ++J)
				Put(FVector(FMath::Lerp(A.X, B.X, Nx == 1 ? 0.5f : (float)I / (Nx - 1)), FMath::Lerp(A.Y, B.Y, Ny == 1 ? 0.5f : (float)J / (Ny - 1)), 0.f));
		}
		// (the corridor's four sides)
		const int32 N = TowerCells24, B0 = N / 2 - 4, B1 = N / 2 + 3;
		if (Floor > 0) { Put(TowerCell24(N * 0.5f - 0.5f, B0 + 0.5f, 0)); Put(TowerCell24(N * 0.5f - 0.5f, B1 - 0.5f, 0)); Put(TowerCell24(B0 + 0.5f, N * 0.5f - 0.5f, 0)); Put(TowerCell24(B1 - 0.5f, N * 0.5f - 0.5f, 0)); }
		for (; Li < TowerLights24.Num(); ++Li) TowerLights24[Li]->SetVisibility(false);
	}
	// ---- the city's picture: the capture nearest this floor; the sphere kept round her floor
	if (TowerViewMID24)
	{
		const URDGameInstance* GI = URDGameInstance::Of(this);
		int32 Best = -1, BestD = 1 << 30;
		if (GI) for (int32 K = 0; K < GI->TowerViews24.Num(); ++K) if (GI->TowerViews24[K] && GI->TowerViewFloors24.IsValidIndex(K) && FMath::Abs(GI->TowerViewFloors24[K] - Floor) < BestD) { BestD = FMath::Abs(GI->TowerViewFloors24[K] - Floor); Best = K; }
		if (Best != TowerViewIndex24)
		{
			TowerViewIndex24 = Best;
			if (Best >= 0) TowerViewMID24->SetTextureParameterValue(TEXT("View"), GI->TowerViews24[Best]);
			TowerViewMID24->SetScalarParameterValue(TEXT("Scale"), Best >= 0 ? TowerViewScale24 : TowerViewNoneScale24);
			// (the level's lobby doors face -Y; the tower's in Heaven face its own way: the picture turned so the street is before the doors)
			TowerViewMID24->SetScalarParameterValue(TEXT("Turn"), FMath::DegreesToRadians((GI ? GI->TowerYaw24 : -90.f) + 90.f));
		}
		if (UStaticMeshComponent* Sp = TowerSphereC24.Get()) Sp->SetWorldLocation(FVector(0.f, 0.f, Floor * TowerStoreyH24 + 160.f));
	}
}

FString ARDDungeonGenerator::TowerLiftNear24(const FVector& From, int32& OutLift, int32& OutFloor, bool& bOnIt) const
{
	OutLift = -1; OutFloor = -1; bOnIt = false;
	const float C = TowerCellSize24;
	for (int32 I = 0; I < TowerLifts24.Num(); ++I)
	{
		const FTowerLift24& L = TowerLifts24[I];
		const FVector D = From - L.Shaft;
		if (FMath::Abs(D.X) < C - 50.f && FMath::Abs(D.Y) < C - 50.f && FMath::Abs(From.Z - L.Z - 92.f) < 80.f) { bOnIt = true; OutLift = I; OutFloor = L.At; return FString(); }
		const FVector E = L.Door + FVector(90.f, 0.f, 0.f);
		if (FVector::Dist2D(From, E) < 170.f)
			for (int32 K = 0; K < L.Floors.Num(); ++K) if (FMath::Abs(From.Z - L.Floors[K] - 92.f) < 80.f) { OutLift = I; OutFloor = K; return FString(); }
	}
	return FString();
}

FString ARDDungeonGenerator::TowerFloorName24(const FTowerLift24& L, int32 K) const
{
	const int32 Storey = FMath::RoundToInt(L.Floors[K] / TowerStoreyH24);
	return Storey == 0 ? FString(TEXT("the lobby")) : FString::Printf(TEXT("floor %d"), Storey);
}

int32 ARDDungeonGenerator::TowerLiftNext24(const FTowerLift24& L) const
{
	return L.At + 1 < L.Floors.Num() ? L.At + 1 : 0;
}

FString ARDDungeonGenerator::TowerDescribeHere24(const FVector& From) const
{
	int32 Li, F; bool bOn;
	TowerLiftNear24(From, Li, F, bOn);
	if (Li >= 0)
	{
		const FTowerLift24& L = TowerLifts24[Li];
		if (L.bMoving) return TEXT("the lift is moving");
		if (bOn) return FString::Printf(TEXT("ride the %s to %s"), L.bExpress ? TEXT("express lift") : TEXT("lift"), *TowerFloorName24(L, TowerLiftNext24(L)));
		return L.At == F ? FString(TEXT("the lift is here: step on")) : FString::Printf(TEXT("call the %s"), L.bExpress ? TEXT("express lift") : TEXT("lift"));
	}
	if (FVector::Dist2D(From, TowerExit24) < 260.f && From.Z < TowerStoreyH24 * 0.5f + 100.f) return FString::Printf(TEXT("leave %s for the street"), *TowerNameNow24);
	return FString();
}

FString ARDDungeonGenerator::TowerUseHere24(const FVector& From)
{
	int32 Li, F; bool bOn;
	TowerLiftNear24(From, Li, F, bOn);
	if (Li >= 0)
	{
		FTowerLift24& L = TowerLifts24[Li];
		if (L.bMoving) return TEXT("lift moving");
		if (bOn) { L.Target = TowerLiftNext24(L); UE_LOG(LogRDTower24, Log, TEXT("RDTOWER24 lift %d: from %d to %d"), Li, L.At, L.Target); return TEXT("lift ride"); }
		if (L.At == F) return TEXT("lift here");
		L.Target = F;
		UE_LOG(LogRDTower24, Log, TEXT("RDTOWER24 lift %d called to %d (from %d)"), Li, F, L.At);
		return TEXT("lift called");
	}
	if (FVector::Dist2D(From, TowerExit24) < 260.f && From.Z < TowerStoreyH24 * 0.5f + 100.f)
	{
		UE_LOG(LogRDTower24, Log, TEXT("RDTOWER24 out of %s"), *TowerNameNow24);
		return ReturnToTown() ? FString(TEXT("street")) : FString();
	}
	return FString();
}

void ARDDungeonGenerator::SetTowerHidden24(bool bHide)
{
	for (TPair<FString, TObjectPtr<UInstancedStaticMeshComponent>>& Kv : TowerIsms24) if (Kv.Value) Kv.Value->SetVisibility(!bHide);
	for (FTowerLift24& L : TowerLifts24) if (UStaticMeshComponent* P = L.Platform.Get()) P->SetVisibility(!bHide);
}

bool ARDDungeonGenerator::CaptureView24(FVector At, FRotator Rot, float Fov, int32 Width, int32 Height, const FString& Dir, const FString& File)
{
	USceneCaptureComponent2D* Cap = NewObject<USceneCaptureComponent2D>(this);
	UTextureRenderTarget2D* Rt = UKismetRenderingLibrary::CreateRenderTarget2D(this, FMath::Clamp(Width, 64, 4096), FMath::Clamp(Height, 64, 4096), RTF_RGBA8_SRGB);
	if (!Cap || !Rt) return false;
	Cap->bCaptureEveryFrame = false; Cap->bCaptureOnMovement = false; Cap->FOVAngle = Fov;
	Cap->CaptureSource = ESceneCaptureSource::SCS_FinalColorLDR;
	Cap->TextureTarget = Rt;
	Cap->RegisterComponent();
	Cap->SetWorldLocationAndRotation(At, Rot);
	if (APawn* Pw = UGameplayStatics::GetPlayerPawn(this, 0)) Cap->HiddenActors.Add(Pw);
	Cap->CaptureScene(); Cap->CaptureScene();
	UKismetRenderingLibrary::ExportRenderTarget(this, Rt, Dir, File);
	Cap->DestroyComponent();
	return true;
}

TArray<FString> ARDDungeonGenerator::GetTower24() const
{
	// (for the tests: "tower|<name>|<seed>|<floors>|<cells>|<cell cm>|<storey cm>", "room|<i>|<floor>|<kind>|<x0>|<y0>|<x1>|<y1>|<door
	// x>|<door y>|<door way>|<props>", "stair|<floor>|<foot x>|<foot y>|<z>|<top x>|<top y>|<top z>", "lift|<i>|<express>|<x>|<y>|<floors>|
	// <at>|<target>|<z>|<moving>|<gates shut>", "liftfloor|<i>|<k>|<z>", "exit|<x>|<y>|<z>", "here|<floor>|<view>|<view floor>",
	// "count|<boxes>|<props>|<components>|<missing>")
	TArray<FString> Out = TowerLines24;
	for (int32 I = 0; I < TowerLifts24.Num(); ++I)
	{
		const FTowerLift24& L = TowerLifts24[I];
		int32 Shut = 0;
		for (const TWeakObjectPtr<UPrimitiveComponent>& G : L.Gates) if (const UPrimitiveComponent* Gp = G.Get(); Gp && Gp->GetCollisionEnabled() != ECollisionEnabled::NoCollision) ++Shut;
		Out.Add(FString::Printf(TEXT("lift|%d|%d|%.0f|%.0f|%d|%d|%d|%.1f|%d|%d|%.0f|%.0f"), I, L.bExpress ? 1 : 0, L.Shaft.X, L.Shaft.Y, L.Floors.Num(), L.At, L.Target, L.Z, L.bMoving ? 1 : 0, Shut, L.Door.X, L.Door.Y));
		for (int32 K = 0; K < L.Floors.Num(); ++K) Out.Add(FString::Printf(TEXT("liftfloor|%d|%d|%.0f"), I, K, L.Floors[K]));
	}
	Out.Add(FString::Printf(TEXT("exit|%.0f|%.0f|%.0f"), TowerExit24.X, TowerExit24.Y, TowerExit24.Z));
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (GI) for (int32 K = 0; K < GI->TowerViewAt24.Num(); ++K) Out.Add(FString::Printf(TEXT("view|%d|%d|%.0f|%.0f|%.0f|%.1f"), K, GI->TowerViewFloors24.IsValidIndex(K) ? GI->TowerViewFloors24[K] : -1, GI->TowerViewAt24[K].X, GI->TowerViewAt24[K].Y, GI->TowerViewAt24[K].Z, GI->TowerYaw24));
	Out.Add(FString::Printf(TEXT("here|%d|%d|%d|%.1f"), TowerFloorNow24, TowerViewIndex24, GI && GI->TowerViewFloors24.IsValidIndex(TowerViewIndex24) ? GI->TowerViewFloors24[TowerViewIndex24] : -1, GI ? GI->TowerViewHour24 : -1.f));
	Out.Add(FString::Printf(TEXT("count|%d|%d|%d|%d"), TowerBoxes24, TowerProps24, TowerIsms24.Num(), TowerMissing24.Num()));
	return Out;
}
