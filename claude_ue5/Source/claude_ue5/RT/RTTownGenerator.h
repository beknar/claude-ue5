// random_level: procedural medieval town. The world is a grid of 250 m cells (streets every 50 m). The start square
// (cells -1..0 on both axes = 500 m x 500 m around the origin crossroads) is built in the editor with a fixed seed and saved
// with the level. In play, whenever the player comes within TriggerDistance of the town's edge while moving toward it,
// the cells ahead of her (and their two neighbours) are generated: terrain, streets, buildings with interiors, props and
// foliage. Runtime cells use a fresh seed each session and are never saved, so every play session starts again from the
// start square alone.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RTTypes.h"
#include "RTTownGenerator.generated.h"

class ARTCell;
class ARTBuilding;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class UPostProcessComponent;
class UStaticMesh;

UCLASS()
class CLAUDE_UE5_API ARTTownGenerator : public AActor
{
	GENERATED_BODY()

public:
	ARTTownGenerator();

	// ---- layout
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomTown|Layout") float CellSize = 25000.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomTown|Layout") float BlockSize = 5000.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomTown|Layout") float StreetHalfWidth = 400.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomTown|Layout") float GroundSpacing = 200.f;
	/** start square: cells -StartCells..StartCells-1 on both axes */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomTown|Layout") int32 StartCells = 1;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomTown|Layout") int32 StartSeed = 20261011;
	/** generate ahead once the player is this close to the edge of the generated town (moving toward it) */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomTown|Layout") float TriggerDistance = 7000.f;
	/** any missing cell closer than this to the player is generated whatever her direction (edge-street safety) */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomTown|Layout") float SafetyDistance = 2500.f;
	/** runtime cells farther than this many cells from the player are removed (0 = keep all) */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomTown|Layout") int32 UnloadCellDistance = 4;
	/** session seed for runtime cells (0 = random each play) */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomTown|Layout") int32 FixedSessionSeed = 0;
	/** generation follows this actor instead of the player pawn when set (cinematics: Movie Render Queue has no player) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Layout") TObjectPtr<AActor> TrackedActor;

	// ---- generation indicator (runtime cells): a glowing curtain rises on the new cell's border and a scan wave sweeps
	// across the cell from the side nearest the player; ahead of the wave the new cell is drawn as a cyan ghost
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Reveal") bool bRevealEffect = true;
	/** post-process material (vector params Rect0..N-1 = min x, min y, max x, max y; Info0..N-1 = origin x, y, start time) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Reveal") TObjectPtr<UMaterialInterface> RevealPostMaterial;
	/** translucent curtain material (scalar param StartTime) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Reveal") TObjectPtr<UMaterialInterface> RevealCurtainMaterial;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Reveal") float RevealDuration = 5.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Reveal") float RevealCurtainHeight = 2500.f;
	static constexpr int32 RevealSlots = 6;

	// ---- content
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Content") TArray<FRTBuildingTemplate> Templates;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Content") TObjectPtr<UMaterialInterface> GroundMaterial;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Content") TArray<FRTScatterItem> Trees;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Content") TArray<FRTScatterItem> Bushes;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Content") TArray<FRTScatterItem> Grass;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Content") TArray<FRTScatterItem> Rocks;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Content") TArray<FRTScatterItem> YardProps;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Content") TArray<FRTScatterItem> MarketProps;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Content") TArray<FRTScatterItem> Tents;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Content") TArray<FRTScatterItem> Wells;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Content") TArray<TSoftClassPtr<AActor>> MarketStalls;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Content") TObjectPtr<UStaticMesh> ChestBody;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Content") TObjectPtr<UStaticMesh> ChestLid;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Content") TObjectPtr<UStaticMesh> TrunkBody;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Content") TObjectPtr<UStaticMesh> TrunkLid;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Content") TObjectPtr<UStaticMesh> WardrobeBody;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Content") TObjectPtr<UStaticMesh> WardrobeDoorL;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Content") TObjectPtr<UStaticMesh> WardrobeDoorR;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomTown|Content") TObjectPtr<UStaticMesh> Washstand;

	// ---- state
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomTown") TMap<FIntPoint, TObjectPtr<ARTCell>> Cells;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomTown") int32 SessionSeed = 0;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomTown") int32 CellsGenerated = 0;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomTown") int32 CellsRemoved = 0;

	/** (editor) clear everything and build the start square with StartSeed; saved with the level */
	UFUNCTION(CallInEditor, BlueprintCallable, Category = "RandomTown") void BuildStartSquare();
	UFUNCTION(CallInEditor, BlueprintCallable, Category = "RandomTown") void ClearAll();

	/** terrain height (same everywhere, every session: cells join seamlessly) before lot flattening */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomTown") static float TerrainHeight(float X, float Y);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomTown") FIntPoint WorldToCell(FVector Location) const;
	UFUNCTION(BlueprintCallable, Category = "RandomTown") TArray<FIntPoint> GetCellCoords() const;
	UFUNCTION(BlueprintCallable, Category = "RandomTown") int32 GetNumCells() const { return Cells.Num(); }
	UFUNCTION(BlueprintCallable, Category = "RandomTown") bool IsCellGenerated(FIntPoint Cell) const;
	UFUNCTION(BlueprintCallable, Category = "RandomTown") ARTCell* GetCell(FIntPoint Cell) const;
	UFUNCTION(BlueprintCallable, Category = "RandomTown") TArray<ARTBuilding*> GetBuildingsInCell(FIntPoint Cell) const;
	UFUNCTION(BlueprintCallable, Category = "RandomTown") bool IsStartCell(FIntPoint Cell) const;
	/** generate one cell now (if missing); returns true if it was created */
	UFUNCTION(BlueprintCallable, Category = "RandomTown") bool GenerateCellNow(FIntPoint Cell);
	/** pending cells in the generation queue */
	UFUNCTION(BlueprintCallable, Category = "RandomTown") int32 GetQueueLength() const { return Queue.Num(); }
	/** ground height at a point from the generated ground (line trace), or TerrainHeight if no cell there */
	UFUNCTION(BlueprintCallable, Category = "RandomTown") float GroundHeightAt(float X, float Y) const;

	int32 CellSeed(FIntPoint Cell) const;
	/** the actor generation follows: TrackedActor, else the player pawn */
	UFUNCTION(BlueprintCallable, Category = "RandomTown") AActor* GetTrackedActor() const;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	UPROPERTY(VisibleAnywhere, Category = "RandomTown|Reveal") TObjectPtr<UPostProcessComponent> RevealPost;
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> RevealMID;
	int32 NextRevealSlot = 0;
	TArray<FIntPoint> Queue;
	ARTCell* SpawnCell(FIntPoint Cell, bool bEditorBuild, bool bReveal = false);
	void StartReveal(ARTCell* Cell);
	void Enqueue(FIntPoint Cell);
};
