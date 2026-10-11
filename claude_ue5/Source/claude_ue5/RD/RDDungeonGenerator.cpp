#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDMonster.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/DateTime.h"
#include "Components/PostProcessComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "InputCoreTypes.h"

DEFINE_LOG_CATEGORY_STATIC(LogRandomDungeonGen, Log, All);

ARDDungeonGenerator::ARDDungeonGenerator()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.f;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RevealPost = CreateDefaultSubobject<UPostProcessComponent>(TEXT("RevealPost"));
	RevealPost->SetupAttachment(RootComponent);
	RevealPost->bUnbound = true;
	RevealPost->Priority = 10.f;
}

FString ARDDungeonGenerator::KindName(ERDRoomKind K)
{
	switch (K)
	{
	case ERDRoomKind::Hall: return TEXT("Great hall");
	case ERDRoomKind::Barracks: return TEXT("Barracks");
	case ERDRoomKind::Prison: return TEXT("Prison cells");
	case ERDRoomKind::Torture: return TEXT("Torture chamber");
	case ERDRoomKind::Storeroom: return TEXT("Storeroom");
	case ERDRoomKind::Armory: return TEXT("Armory");
	case ERDRoomKind::Kitchen: return TEXT("Kitchen");
	case ERDRoomKind::Library: return TEXT("Library");
	case ERDRoomKind::Chapel: return TEXT("Chapel");
	case ERDRoomKind::Crypt: return TEXT("Crypt");
	case ERDRoomKind::Treasury: return TEXT("Treasury");
	case ERDRoomKind::GuardRoom: return TEXT("Guard room");
	case ERDRoomKind::Forge: return TEXT("Forge");
	default: return TEXT("Hallway junction");
	}
}

AActor* ARDDungeonGenerator::GetTrackedActor() const
{
	return TrackedActor ? TrackedActor.Get() : UGameplayStatics::GetPlayerPawn(this, 0);
}

FIntPoint ARDDungeonGenerator::WorldToTile(FVector L) const
{
	return FIntPoint(FMath::FloorToInt(L.X / TileSize), FMath::FloorToInt(L.Y / TileSize));
}

FIntPoint ARDDungeonGenerator::SectionMinTile(FIntPoint S) const
{
	const int32 H = SectionTiles / 2;
	return FIntPoint(S.X * SectionTiles - H, S.Y * SectionTiles - H);
}

FIntPoint ARDDungeonGenerator::WorldToSection(FVector L) const
{
	const FIntPoint T = WorldToTile(L);
	const int32 H = SectionTiles / 2;
	return FIntPoint(FMath::FloorToInt((float)(T.X + H) / SectionTiles), FMath::FloorToInt((float)(T.Y + H) / SectionTiles));
}

FVector ARDDungeonGenerator::TileCenter(FIntPoint T) const
{
	return FVector((T.X + 0.5f) * TileSize, (T.Y + 0.5f) * TileSize, 0.f);
}

int32 ARDDungeonGenerator::SectionSeed(FIntPoint S) const
{
	const uint32 Base = IsStartSection(S) ? (uint32)StartSeed : (uint32)SessionSeed;
	return (int32)HashCombine(HashCombine(Base, GetTypeHash(S.X * 7919 + 3)), GetTypeHash(S.Y * 104729 + 17));
}

bool ARDDungeonGenerator::IsSectionGenerated(FIntPoint S) const { return Sections.Contains(S) && Sections[S] != nullptr; }
ARDSection* ARDDungeonGenerator::GetSection(FIntPoint S) const { const TObjectPtr<ARDSection>* P = Sections.Find(S); return P ? P->Get() : nullptr; }
TArray<FIntPoint> ARDDungeonGenerator::GetSectionCoords() const { TArray<FIntPoint> Out; Sections.GetKeys(Out); return Out; }

FVector ARDDungeonGenerator::GetStartRoomCenter() const
{
	// the great hall is the start section's centre block (3, 3): its lanes cross at the origin tile
	if (ARDSection* S = GetSection(FIntPoint::ZeroValue))
	{
		const int32 R = S->RoomAt(FVector(TileSize * 0.5f, TileSize * 0.5f, 0));
		if (R >= 0) return S->GetRoomCenter(R);
	}
	return FVector(0, 0, 0);
}

ARDSection* ARDDungeonGenerator::SpawnSection(FIntPoint S, bool bEditorBuild, bool bReveal)
{
	UWorld* W = GetWorld();
	FActorSpawnParameters P; P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	const FIntPoint T0 = SectionMinTile(S);
	ARDSection* Sec = W->SpawnActor<ARDSection>(ARDSection::StaticClass(), FTransform(FVector(T0.X * TileSize, T0.Y * TileSize, 0.f)), P);
	if (!Sec) return nullptr;
#if WITH_EDITOR
	if (bEditorBuild) { Sec->SetActorLabel(FString::Printf(TEXT("RD_Section_%d_%d"), S.X, S.Y)); Sec->SetFolderPath(TEXT("RandomDungeon/Sections")); }
#endif
	Sections.Add(S, Sec);
	if (bReveal && W->IsGameWorld() && !bEditorBuild)
	{
		// runtime: shell and doors now, the furnishing spread over the next frames (Tick)
		Sec->BeginGenerate(this, S, SectionSeed(S), false);
		Building = Sec;
	}
	else Sec->Generate(this, S, SectionSeed(S), bEditorBuild);
	++SectionsGenerated;
	if (bReveal && bRevealEffect) StartReveal(Sec);
	return Sec;
}

void ARDDungeonGenerator::StartReveal(ARDSection* Sec)
{
	UWorld* W = GetWorld();
	const float Now = W->GetTimeSeconds();
	const float SS = SectionTiles * TileSize;
	const FVector2D Min = Sec->GetSectionMin(), Max = Min + FVector2D(SS);
	const AActor* Who = GetTrackedActor();
	const FVector L = Who ? Who->GetActorLocation() : FVector((Min + Max) * 0.5, 0.0);
	const FVector2D O(FMath::Clamp((float)L.X, (float)Min.X, (float)Max.X), FMath::Clamp((float)L.Y, (float)Min.Y, (float)Max.Y));
	if (RevealMID)
	{
		const int32 Slot = NextRevealSlot++ % RevealSlots;
		RevealMID->SetVectorParameterValue(*FString::Printf(TEXT("Rect%d"), Slot), FLinearColor(Min.X, Min.Y, Max.X, Max.Y));
		RevealMID->SetVectorParameterValue(*FString::Printf(TEXT("Info%d"), Slot), FLinearColor(O.X, O.Y, Now, 1.f));
	}
	if (RevealCurtainMaterial) Sec->ShowCurtain(RevealCurtainMaterial, Now, RevealCurtainHeight, RevealDuration + 0.5f);
	LastRevealTime = Now; LastRevealSection = Sec->Coord;
	if (FRDSectionMap* M = MapData.Find(Sec->Coord)) M->GeneratedTime = Now;
	UE_LOG(LogRandomDungeonGen, Log, TEXT("RDGEN reveal (%d,%d) t=%.3f from (%.0f,%.0f) tracked (%.0f,%.0f): %d rooms, %d doors, %d containers, %d monsters, %d instances, %d lights, %.0f ms"),
		Sec->Coord.X, Sec->Coord.Y, Now, O.X, O.Y, L.X, L.Y, Sec->GetNumRooms(), Sec->GetNumDoors(), Sec->GetNumContainers(), Sec->SpawnedMonsters.Num(),
		Sec->NumInstances, Sec->NumLights, Sec->GenerateMs);
}

void ARDDungeonGenerator::ClearAll()
{
	UWorld* W = GetWorld();
	for (auto& KV : Sections) if (KV.Value) KV.Value->Destroy();
	Sections.Reset();
	for (TActorIterator<ARDSection> It(W); It; ++It) It->Destroy();
	for (TActorIterator<ARDMonster> It(W); It; ++It) It->Destroy();
	Queue.Reset(); MapData.Reset();
	Building = nullptr;
	SectionsGenerated = 0;
}

void ARDDungeonGenerator::BuildStartSection()
{
	ClearAll();
	SpawnSection(FIntPoint::ZeroValue, !GetWorld()->IsGameWorld());
	MapData.Reset();      // map data is play state (rebuilt by ActivateForPlay)
	Modify();
	UE_LOG(LogRandomDungeonGen, Log, TEXT("RDGEN start section built"));
}

bool ARDDungeonGenerator::GenerateSectionNow(FIntPoint S)
{
	if (IsSectionGenerated(S)) return false;
	ARDSection* Sec = SpawnSection(S, false, true);
	if (Sec && Building == Sec) { while (!Sec->ContinueGenerate(1e9)) {} Building = nullptr; }
	return Sec != nullptr;
}

void ARDDungeonGenerator::Enqueue(FIntPoint S)
{
	if (!IsSectionGenerated(S) && !Queue.Contains(S)) Queue.Add(S);
}

int32 ARDDungeonGenerator::GetNumMonsters() const { return GetMonsters().Num(); }

TArray<ARDMonster*> ARDDungeonGenerator::GetMonsters() const
{
	TArray<ARDMonster*> Out;
	for (const auto& KV : Sections) if (KV.Value) for (ARDMonster* M : KV.Value->SpawnedMonsters) if (M) Out.Add(M);
	return Out;
}

void ARDDungeonGenerator::GetDiscoveryStats(int32& Disc, int32& Gen) const
{
	Disc = Gen = 0;
	for (const auto& KV : MapData)
		for (const FRDMapRect& R : KV.Value.Rects) if (!R.bCorridor) { ++Gen; if (R.bDiscovered) ++Disc; }
}

FString ARDDungeonGenerator::InteractNearest(FVector From, float MaxDistance)
{
	ARDSection* Best = nullptr; bool bBestDoor = false; int32 BestI = -1; float BestD = MaxDistance;
	const FIntPoint Here = WorldToSection(From);
	for (int32 Dx = -1; Dx <= 1; ++Dx)
		for (int32 Dy = -1; Dy <= 1; ++Dy)
			if (ARDSection* S = GetSection(Here + FIntPoint(Dx, Dy)))
			{
				bool bDoor; int32 I;
				const float D = S->FindNearestInteractive(From, BestD, bDoor, I);
				if (I >= 0 && D < BestD) { BestD = D; Best = S; bBestDoor = bDoor; BestI = I; }
			}
	if (!Best) return FString();
	if (bBestDoor) { Best->ToggleDoor(BestI, From); return Best->IsDoorCell(BestI) ? TEXT("cell door") : TEXT("door"); }
	Best->ToggleContainer(BestI);
	return Best->GetContainerKind(BestI);
}

FString ARDDungeonGenerator::DescribeNearest(FVector From, float MaxDistance) const
{
	const ARDSection* Best = nullptr; bool bBestDoor = false; int32 BestI = -1; float BestD = MaxDistance;
	const FIntPoint Here = WorldToSection(From);
	for (int32 Dx = -1; Dx <= 1; ++Dx)
		for (int32 Dy = -1; Dy <= 1; ++Dy)
			if (const ARDSection* S = GetSection(Here + FIntPoint(Dx, Dy)))
			{
				bool bDoor; int32 I;
				const float D = S->FindNearestInteractive(From, BestD, bDoor, I);
				if (I >= 0 && D < BestD) { BestD = D; Best = S; bBestDoor = bDoor; BestI = I; }
			}
	if (!Best) return FString();
	FString What = bBestDoor ? (Best->IsDoorCell(BestI) ? TEXT("cell door") : TEXT("door")) : Best->GetContainerKind(BestI);
	What.ReplaceInline(TEXT("2"), TEXT(""));
	return FString::Printf(TEXT("%s %s"), Best->IsTargetOpen(bBestDoor, BestI) ? TEXT("close") : TEXT("open"), *What);
}

void ARDDungeonGenerator::UpdateDiscovery(const FVector& L)
{
	const FIntPoint T = WorldToTile(L);
	const FIntPoint S = WorldToSection(L);
	FRDSectionMap* M = MapData.Find(S);
	if (!M) return;
	for (FRDMapRect& R : M->Rects)
	{
		if (R.bDiscovered) continue;
		// rooms: once she is inside (or in their doorway); hallways: within 4 tiles of her along them
		const int32 Pad = R.bCorridor ? 4 : 0;
		if (T.X >= R.Min.X - Pad && T.Y >= R.Min.Y - Pad && T.X < R.Max.X + Pad && T.Y < R.Max.Y + Pad) R.bDiscovered = true;
	}
}

void ARDDungeonGenerator::BeginPlay()
{
	Super::BeginPlay();
	SessionSeed = FixedSessionSeed != 0 ? FixedSessionSeed : (int32)(FDateTime::Now().GetTicks() & 0x7fffffff);
	if (bRevealEffect && RevealPostMaterial)
	{
		RevealMID = UMaterialInstanceDynamic::Create(RevealPostMaterial, this);
		for (int32 Slot = 0; Slot < RevealSlots; ++Slot) RevealMID->SetVectorParameterValue(*FString::Printf(TEXT("Info%d"), Slot), FLinearColor(0, 0, -1e6f, 0));
		RevealPost->Settings.WeightedBlendables.Array.Add(FWeightedBlendable(1.f, RevealMID));
	}
	MapData.Reset();
	for (auto It = Sections.CreateIterator(); It; ++It) if (!It->Value) It.RemoveCurrent();
	if (Sections.Num() == 0) SpawnSection(FIntPoint::ZeroValue, false);
	else for (auto& KV : Sections) KV.Value->ActivateForPlay();
	UE_LOG(LogRandomDungeonGen, Log, TEXT("RDGEN play: %d start sections, session seed %d, %d monsters"), Sections.Num(), SessionSeed, GetNumMonsters());
}

void ARDDungeonGenerator::Tick(float Dt)
{
	Super::Tick(Dt);
	// input: F interacts, M toggles the map
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
	{
		APawn* P = PC->GetPawn();
		if (PC->WasInputKeyJustPressed(EKeys::F) && P) InteractNearest(P->GetActorLocation());
		if (PC->WasInputKeyJustPressed(EKeys::M)) bMapOpen = !bMapOpen;
	}
	const AActor* Pawn = GetTrackedActor();
	if (Pawn)
	{
		const FVector L = Pawn->GetActorLocation(), V = Pawn->GetVelocity();
		const float SS = SectionTiles * TileSize;
		// the section TriggerDistance ahead of her along each axis she is moving on
		for (int32 Axis = 0; Axis < 2; ++Axis)
		{
			const float Vx = Axis == 0 ? V.X : V.Y;
			if (FMath::Abs(Vx) < 30.f) continue;
			FVector A = L; (Axis == 0 ? A.X : A.Y) += FMath::Sign(Vx) * TriggerDistance;
			Enqueue(WorldToSection(A));
		}
		// safety: a missing neighbour close to her is generated whatever her direction
		const FIntPoint Here = WorldToSection(L);
		Enqueue(Here);
		for (int32 Dx = -1; Dx <= 1; ++Dx)
			for (int32 Dy = -1; Dy <= 1; ++Dy)
			{
				const FIntPoint C = Here + FIntPoint(Dx, Dy);
				if (IsSectionGenerated(C)) continue;
				const FIntPoint T0 = SectionMinTile(C);
				const float X0 = T0.X * TileSize, Y0 = T0.Y * TileSize;
				const float Ex = FMath::Max3(X0 - (float)L.X, 0.f, (float)L.X - (X0 + SS));
				const float Ey = FMath::Max3(Y0 - (float)L.Y, 0.f, (float)L.Y - (Y0 + SS));
				if (FMath::Sqrt(Ex * Ex + Ey * Ey) < SafetyDistance) Enqueue(C);
			}
		// far runtime sections are dropped (they come back identical: same session seed; the map keeps them)
		if (UnloadSectionDistance > 0)
		{
			for (auto It = Sections.CreateIterator(); It; ++It)
			{
				if (IsStartSection(It->Key) || !It->Value || It->Value == Building) continue;
				if (FMath::Max(FMath::Abs(It->Key.X - Here.X), FMath::Abs(It->Key.Y - Here.Y)) > UnloadSectionDistance)
				{
					It->Value->Destroy(); It.RemoveCurrent(); ++SectionsRemoved;
				}
			}
		}
		UpdateDiscovery(L);
	}
	// a section being built gets ~6 ms a frame; the next queued one starts when it is done
	if (Building)
	{
		if (Building->ContinueGenerate(FrameBudgetMs / 1000.0)) Building = nullptr;
		return;
	}
	while (Queue.Num() > 0)
	{
		const FIntPoint C = Queue[0]; Queue.RemoveAt(0);
		if (IsSectionGenerated(C)) continue;
		SpawnSection(C, false, true);
		break;
	}
}
