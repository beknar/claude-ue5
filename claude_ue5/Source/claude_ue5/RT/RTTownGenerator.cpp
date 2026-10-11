#include "RT/RTTownGenerator.h"
#include "RT/RTCell.h"
#include "RT/RTBuilding.h"
#include "ProceduralMeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/DateTime.h"
#include "Components/PostProcessComponent.h"
#include "Materials/MaterialInstanceDynamic.h"

DEFINE_LOG_CATEGORY_STATIC(LogRandomTownGen, Log, All);

ARTTownGenerator::ARTTownGenerator()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.1f;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RevealPost = CreateDefaultSubobject<UPostProcessComponent>(TEXT("RevealPost"));
	RevealPost->SetupAttachment(RootComponent);
	RevealPost->bUnbound = true;
	RevealPost->Priority = 10.f;
}

AActor* ARTTownGenerator::GetTrackedActor() const
{
	return TrackedActor ? TrackedActor.Get() : UGameplayStatics::GetPlayerPawn(this, 0);
}

void ARTTownGenerator::StartReveal(ARTCell* Cell)
{
	UWorld* W = GetWorld();
	const float Now = W->GetTimeSeconds();
	const FVector2D Min = Cell->GetCellMin(), Max = Min + FVector2D(CellSize);
	const AActor* Who = GetTrackedActor();
	const FVector L = Who ? Who->GetActorLocation() : FVector((Min + Max) * 0.5, 0.0);
	// the wave starts on the cell border nearest her
	const FVector2D O(FMath::Clamp((float)L.X, (float)Min.X, (float)Max.X), FMath::Clamp((float)L.Y, (float)Min.Y, (float)Max.Y));
	if (RevealMID)
	{
		const int32 S = NextRevealSlot++ % RevealSlots;
		RevealMID->SetVectorParameterValue(*FString::Printf(TEXT("Rect%d"), S), FLinearColor(Min.X, Min.Y, Max.X, Max.Y));
		RevealMID->SetVectorParameterValue(*FString::Printf(TEXT("Info%d"), S), FLinearColor(O.X, O.Y, Now, 1.f));
	}
	if (RevealCurtainMaterial) Cell->ShowCurtain(RevealCurtainMaterial, Now, RevealCurtainHeight, RevealDuration + 0.5f);
	UE_LOG(LogRandomTownGen, Log, TEXT("RTGEN reveal (%d,%d) t=%.3f from (%.0f,%.0f) tracked (%.0f,%.0f): %d buildings, %d instances"),
		Cell->Coord.X, Cell->Coord.Y, Now, O.X, O.Y, L.X, L.Y, Cell->Buildings.Num(), Cell->NumInstances);
}

float ARTTownGenerator::TerrainHeight(float X, float Y)
{
	const float A = FMath::PerlinNoise2D(FVector2D(X / 26000.f + 13.17f, Y / 26000.f + 7.31f));
	const float B = FMath::PerlinNoise2D(FVector2D(X / 7000.f + 3.91f, Y / 7000.f + 11.23f));
	return 180.f * A + 45.f * B;
}

FIntPoint ARTTownGenerator::WorldToCell(FVector L) const
{
	return FIntPoint(FMath::FloorToInt(L.X / CellSize), FMath::FloorToInt(L.Y / CellSize));
}

bool ARTTownGenerator::IsStartCell(FIntPoint C) const
{
	return C.X >= -StartCells && C.X < StartCells && C.Y >= -StartCells && C.Y < StartCells;
}

int32 ARTTownGenerator::CellSeed(FIntPoint C) const
{
	const uint32 Base = IsStartCell(C) ? (uint32)StartSeed : (uint32)SessionSeed;
	return (int32)HashCombine(HashCombine(Base, GetTypeHash(C.X * 7919)), GetTypeHash(C.Y * 104729 + 17));
}

TArray<FIntPoint> ARTTownGenerator::GetCellCoords() const
{
	TArray<FIntPoint> Out; Cells.GetKeys(Out); return Out;
}

bool ARTTownGenerator::IsCellGenerated(FIntPoint C) const { return Cells.Contains(C) && Cells[C] != nullptr; }
ARTCell* ARTTownGenerator::GetCell(FIntPoint C) const { const TObjectPtr<ARTCell>* P = Cells.Find(C); return P ? P->Get() : nullptr; }

TArray<ARTBuilding*> ARTTownGenerator::GetBuildingsInCell(FIntPoint C) const
{
	TArray<ARTBuilding*> Out;
	if (ARTCell* Cell = GetCell(C)) for (ARTBuilding* B : Cell->Buildings) if (B) Out.Add(B);
	return Out;
}

ARTCell* ARTTownGenerator::SpawnCell(FIntPoint C, bool bEditorBuild, bool bReveal)
{
	UWorld* W = GetWorld();
	FActorSpawnParameters P; P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ARTCell* Cell = W->SpawnActor<ARTCell>(ARTCell::StaticClass(), FTransform(FVector(C.X * CellSize, C.Y * CellSize, 0.f)), P);
	if (!Cell) return nullptr;
#if WITH_EDITOR
	if (bEditorBuild) { Cell->SetActorLabel(FString::Printf(TEXT("RT_Cell_%d_%d"), C.X, C.Y)); Cell->SetFolderPath(TEXT("RandomTown/Cells")); }
#endif
	Cell->Generate(this, C, CellSeed(C), bEditorBuild);
	Cells.Add(C, Cell);
	++CellsGenerated;
	if (bReveal && bRevealEffect) StartReveal(Cell);
	return Cell;
}

void ARTTownGenerator::ClearAll()
{
	UWorld* W = GetWorld();
	for (auto& KV : Cells) if (KV.Value) KV.Value->Destroy();
	Cells.Reset();
	for (TActorIterator<ARTCell> It(W); It; ++It) It->Destroy();
	for (TActorIterator<ARTBuilding> It(W); It; ++It) It->Destroy();
	Queue.Reset();
	CellsGenerated = 0;
}

void ARTTownGenerator::BuildStartSquare()
{
	ClearAll();
	for (int32 X = -StartCells; X < StartCells; ++X)
		for (int32 Y = -StartCells; Y < StartCells; ++Y)
			SpawnCell(FIntPoint(X, Y), !GetWorld()->IsGameWorld());
	Modify();
	UE_LOG(LogRandomTownGen, Log, TEXT("RTGEN start square built: %d cells"), Cells.Num());
}

bool ARTTownGenerator::GenerateCellNow(FIntPoint C)
{
	if (IsCellGenerated(C)) return false;
	return SpawnCell(C, false, true) != nullptr;
}

void ARTTownGenerator::Enqueue(FIntPoint C)
{
	if (!IsCellGenerated(C) && !Queue.Contains(C)) Queue.Add(C);
}

float ARTTownGenerator::GroundHeightAt(float X, float Y) const
{
	if (ARTCell* Cell = GetCell(WorldToCell(FVector(X, Y, 0)))) return Cell->SurfaceHeight(X, Y);
	return TerrainHeight(X, Y);
}

void ARTTownGenerator::BeginPlay()
{
	Super::BeginPlay();
	SessionSeed = FixedSessionSeed != 0 ? FixedSessionSeed : (int32)(FDateTime::Now().GetTicks() & 0x7fffffff);
	if (bRevealEffect && RevealPostMaterial)
	{
		RevealMID = UMaterialInstanceDynamic::Create(RevealPostMaterial, this);
		for (int32 S = 0; S < RevealSlots; ++S) RevealMID->SetVectorParameterValue(*FString::Printf(TEXT("Info%d"), S), FLinearColor(0, 0, -1e6f, 0));
		RevealPost->Settings.WeightedBlendables.Array.Add(FWeightedBlendable(1.f, RevealMID));
	}
	// drop dead entries; if the start square was never built in the editor, build it now (same seed, same town)
	for (auto It = Cells.CreateIterator(); It; ++It) if (!It->Value) It.RemoveCurrent();
	if (Cells.Num() == 0)
		for (int32 X = -StartCells; X < StartCells; ++X)
			for (int32 Y = -StartCells; Y < StartCells; ++Y) SpawnCell(FIntPoint(X, Y), false);
	UE_LOG(LogRandomTownGen, Log, TEXT("RTGEN play: %d start cells, session seed %d"), Cells.Num(), SessionSeed);
}

void ARTTownGenerator::Tick(float Dt)
{
	Super::Tick(Dt);
	const AActor* Pawn = GetTrackedActor();
	if (Pawn)
	{
		const FVector L = Pawn->GetActorLocation(), V = Pawn->GetVelocity();
		// the cell TriggerDistance ahead of her along each axis she is moving on (plus its two neighbours across)
		for (int32 Axis = 0; Axis < 2; ++Axis)
		{
			const float Vx = Axis == 0 ? V.X : V.Y;
			if (FMath::Abs(Vx) < 30.f) continue;
			FVector A = L; (Axis == 0 ? A.X : A.Y) += FMath::Sign(Vx) * TriggerDistance;
			const FIntPoint C = WorldToCell(A);
			if (IsCellGenerated(C)) continue;
			Enqueue(C);
			Enqueue(Axis == 0 ? C + FIntPoint(0, 1) : C + FIntPoint(1, 0));
			Enqueue(Axis == 0 ? C - FIntPoint(0, 1) : C - FIntPoint(1, 0));
		}
		if (FMath::Abs(V.X) >= 30.f && FMath::Abs(V.Y) >= 30.f)
			Enqueue(WorldToCell(L + FVector(FMath::Sign(V.X), FMath::Sign(V.Y), 0) * TriggerDistance));
		// safety: a missing neighbour cell close to her is generated whatever her direction (walking along an edge street,
		// half of which belongs to the next cell, must never take her off the generated ground)
		const FIntPoint Here = WorldToCell(L);
		for (int32 Dx = -1; Dx <= 1; ++Dx)
			for (int32 Dy = -1; Dy <= 1; ++Dy)
			{
				const FIntPoint C = Here + FIntPoint(Dx, Dy);
				if (IsCellGenerated(C)) continue;
				const float Ex = FMath::Max3(C.X * CellSize - (float)L.X, 0.f, (float)L.X - (C.X + 1) * CellSize);
				const float Ey = FMath::Max3(C.Y * CellSize - (float)L.Y, 0.f, (float)L.Y - (C.Y + 1) * CellSize);
				if (FMath::Sqrt(Ex * Ex + Ey * Ey) < SafetyDistance) Enqueue(C);
			}
		// far runtime cells are dropped (they come back identical: same session seed)
		if (UnloadCellDistance > 0)
		{
			const FIntPoint PC = WorldToCell(L);
			for (auto It = Cells.CreateIterator(); It; ++It)
			{
				if (IsStartCell(It->Key) || !It->Value) continue;
				if (FMath::Max(FMath::Abs(It->Key.X - PC.X), FMath::Abs(It->Key.Y - PC.Y)) > UnloadCellDistance)
				{
					It->Value->Destroy(); It.RemoveCurrent(); ++CellsRemoved;
				}
			}
		}
	}
	// one new cell per tick (spreads the work)
	while (Queue.Num() > 0)
	{
		const FIntPoint C = Queue[0]; Queue.RemoveAt(0);
		if (IsCellGenerated(C)) continue;
		SpawnCell(C, false, true);
		break;
	}
}
