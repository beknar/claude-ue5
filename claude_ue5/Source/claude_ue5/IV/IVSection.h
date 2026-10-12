// random_isometric_village_level: one 250 m x 250 m part of the village. Plan() takes the building sites of the village
// plan that fall in this section and decides what stands on each (kind, style, door, furniture) from the section seed.
// The static part (ground, house shells, furniture and props as instanced meshes, lights) is built once - saved with the
// level for the editor-built start section - and the interactive part (door leaves, containers, the nav grid, map data)
// is rebuilt for play from the same plan. Every house keeps its roof and its camera-side walls in components of their
// own, so they can be hidden while the player is inside (they keep casting shadows and keep their collision).
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IVTypes.h"
#include "IVSection.generated.h"

class AIVVillageGenerator;
class UInstancedStaticMeshComponent;
class UStaticMeshComponent;
class UPointLightComponent;
class UProceduralMeshComponent;
class UMaterialInterface;

UCLASS()
class CLAUDE_UE5_API AIVSection : public AActor
{
	GENERATED_BODY()

public:
	AIVSection();

	/** nav grid cell (cm) and how far the grid reaches past the section (houses standing across the border) */
	static constexpr float NavCell = 50.f;
	static constexpr float NavMargin = 1500.f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage") FIntPoint Coord = FIntPoint::ZeroValue;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage") int32 Seed = 0;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage") bool bEditorBuilt = false;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage") TObjectPtr<AIVVillageGenerator> Generator;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage") TObjectPtr<UProceduralMeshComponent> Ground;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage") int32 NumInstances = 0;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage") int32 NumLights = 0;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage") float GenerateMs = 0.f;
	/** prefab actors (market stalls...) owned by the section */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage") TArray<TObjectPtr<AActor>> OtherActors;

	void Generate(AIVVillageGenerator* InGenerator, FIntPoint InCoord, int32 InSeed, bool bEditorBuild);
	/** runtime generation spread over frames; ContinueGenerate returns true once the section is complete */
	void BeginGenerate(AIVVillageGenerator* InGenerator, FIntPoint InCoord, int32 InSeed, bool bEditorBuild);
	bool ContinueGenerate(double BudgetSeconds);
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") bool IsBuilding() const { return bBuilding; }
	/** saved (editor-built) section at the start of play: plan again, rebuild the interactive part, nav grid, map data */
	void ActivateForPlay();
	void ShowCurtain(UMaterialInterface* Material, float StartTime, float Height, float Lifetime);

	UFUNCTION(BlueprintCallable, Category = "IsoVillage") FVector2D GetSectionMin() const;
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") int32 GetNumBuildings() const { return Blds.Num(); }
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") int32 GetNumDoors() const { return Doors.Num(); }
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") int32 GetNumContainers() const { return Containers.Num(); }
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") FString GetBuildingKind(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") FString GetBuildingStyle(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") FVector GetBuildingCenter(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") float GetBuildingYaw(int32 Index) const;
	/** footprint size (depth along its front axis, width) in cm */
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") FVector2D GetBuildingSize(int32 Index) const;
	/** main door: a point 1.3 m outside it and a point 1 m inside (world, on the ground / floor) */
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") void GetBuildingEntry(int32 Index, FVector& Outside, FVector& Inside) const;
	/** index of the door mover of a building (-1: none) */
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") int32 GetBuildingDoor(int32 Index) const;
	/** container movers standing in a building (indices into the section's containers) */
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") TArray<int32> GetBuildingContainers(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") bool IsBuildingCut(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") bool IsBuildingRoofHidden(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") FVector GetDoorLocation(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") float GetDoorOpenAlpha(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") FString GetDoorKind(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") FVector GetContainerLocation(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") float GetContainerOpenAlpha(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") FString GetContainerKind(int32 Index) const;
	/** building the container stands in (-1: outdoors) */
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") int32 GetContainerBuilding(int32 Index) const;
	/** a free spot next to a container to stand on while opening it (world) */
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") FVector GetContainerStandPoint(int32 Index) const;
	/** buildings whose main door cannot be reached from the given point over the nav grid (connectivity check) */
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") int32 CountUnreachableDoors(FVector From) const;

	// ---- interaction
	float FindNearestInteractive(const FVector& From, float MaxDistance, bool& bDoor, int32& Index) const;
	void ToggleDoor(int32 Index, const FVector& Opener);
	void ToggleContainer(int32 Index);
	bool IsTargetOpen(bool bDoor, int32 Index) const;

	// ---- cutaway
	/** building whose floor L stands on (-1: none); Current gets a wider margin (she stays "inside" in the doorway) */
	int32 BuildingAt(const FVector& L, int32 Current = -1) const;
	void SetBuildingCut(int32 Index, bool bRoof, bool bWalls);
	void ClearCutaway();
	/** she is inside this building: its roof and camera-side walls come off, its lights go on, the map marks it */
	void EnterBuilding(int32 Index);
	void GetBuildingFloorSamples(int32 Index, TArray<FVector>& Out) const;
	/** hide the roofs / walls of this section's buildings standing between the floor samples and the camera */
	void CutOccluders(const TArray<FVector>& Floor, const FVector& ToCamera, int32 SkipBuilding);

	// ---- nav grid (50 cm cells, reaching NavMargin past the section)
	/** 0 free, 1 blocked, 2 free house floor; -1 outside this section's grid */
	int32 NavAt(const FVector2D& World) const;
	bool IsBlockedWorld(const FVector2D& World) const { return NavAt(World) == 1; }
	void AppendPortals(TMultiMap<FIntPoint, FIntPoint>& Out) const;

	// ---- map
	FIVSectionMap BuildMapData() const;

protected:
	virtual void Destroyed() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	enum { GRoof = 0, GNear = 1, GFar = 2, GNum = 3 };
	struct FBld
	{
		FIVLot Lot;
		EIVBuildingKind Kind = EIVBuildingKind::Cottage;
		EIVStyle Style = EIVStyle::Timber;
		uint32 Seed = 0;
		FVector2D C = FVector2D::ZeroVector;
		float Yaw = 0.f;
		FVector2D Fx = FVector2D(1, 0), Fy = FVector2D(0, 1);
		int32 Nx = 2, Ny = 2;                    // cells: depth (front = +X), width
		int32 Storeys = 1;
		bool bRidgeY = true;
		int32 Span = 2;
		int32 TowerCells = 0;                    // church: tower over the front TowerCells x Ny cells
		int32 TowerStoreys = 0;
		int32 DoorCell = 0;                      // cell along Y of the door in the front wall
		int32 BackDoorCell = -1;                 // second door in the back wall (-1: none)
		float FloorZ = 0.f;
		TArray<UInstancedStaticMeshComponent*> Group[GNum];
		TArray<UPointLightComponent*> FillLights;
		int32 DoorIndex = -1, BackDoorIndex = -1;
		bool bCutRoof = false, bCutWalls = false, bVisited = false;
		// furnishing: occupied boxes in the building frame (min, max)
		TArray<FBox2D> Used;
	};
	struct FMover
	{
		USceneComponent* Pivot = nullptr;
		TArray<UStaticMeshComponent*> Parts;
		FQuat Closed = FQuat::Identity;
		FVector Axis = FVector::UpVector;
		float OpenAngle = 95.f;
		float Alpha = 0.f, Target = 0.f;
		bool bDoor = false;
		FString Kind;
		FVector Center = FVector::ZeroVector;
		FVector Normal = FVector::ZeroVector;   // doors: outward wall normal (world)
		float LeafSign = 1.f;
		int32 Partner = -1;
		int32 Building = -1;
		int32 Group = -1;                        // doors: the wall group they hide with
		FVector Stand = FVector::ZeroVector;    // containers: where to stand
	};
	struct FFlicker { UPointLightComponent* Light; float Base; float Phase; float Amount; };
	struct FPatch { TArray<FVector2D> Pts; uint8 Type; };

	// plan (pure function of Coord + Seed + the village plan)
	TArray<FBld> Blds;
	TArray<FIVLot> Vacant;                   // sites left unbuilt (gardens, greens)
	TArray<FIVLot> Foreign;                  // neighbours' sites reaching into this section (kept clear)
	TArray<FPatch> Patches;
	TArray<FIVMapTree> MapTrees;
	TArray<FIVMapProp> MapProps;
	TArray<FVector2D> KeepClear;             // outdoors: where she stands to open a container

	// build state
	bool bBuildStatic = true, bBuildInteractive = true;
	bool bBuilding = false;
	int32 Step = 0, SubStep = 0;
	FRandomStream GenR;
	double GenStart = 0.0, WorkMs = 0.0;
	int32 GenTicks = 0;
	int32 CurBld = -1;                       // building being furnished (containers / lights belong to it)
	int32 InsideBld = -1;                    // building the player is in (cutaway)
	FVector2D LastLocal = FVector2D::ZeroVector;      // where Place() put the last piece (building frame)
	float LastYaw = 0.f;
	TMap<UStaticMesh*, UInstancedStaticMeshComponent*> Isms, IsmsNoCol, IsmsHidden;
	TMap<UStaticMesh*, TArray<FTransform>> Pending, PendingNoCol, PendingHidden;
	TArray<FMover> Doors;
	TArray<FMover> Containers;
	TArray<FFlicker> Flickers;
	TArray<uint8> Nav;
	int32 NavN = 0;
	TArray<TPair<FIntPoint, FIntPoint>> Portals;      // global nav cells: outside, inside
	// ground mesh being assembled
	TArray<FVector> GV; TArray<FVector> GN; TArray<FVector2D> GUV; TArray<FLinearColor> GC;
	int32 GroundRow = 0;

	void Plan();
	void PlanBuilding(FBld& B, FRandomStream& R);
	bool GroundRows(double Budget, double T0);
	void FinishGround();
	void BuildShell(int32 BI);
	void AddDoorsFor(int32 BI);
	void Furnish(int32 BI);
	void BuildYard(int32 BI, FRandomStream& R);
	void BuildVacant(int32 VI, FRandomStream& R);
	void BuildHub(FRandomStream& R);
	void BuildChurchyard(const FBld& B, FRandomStream& R);
	void ScatterNature(FRandomStream& R);
	void ClearInteractive();
	void FlushInstances();
	void RegisterMap();
	void CollectFlicker();
	void RelinkGroups();
	void Finish();

	// placement helpers (world space)
	void AddPiece(FName Name, const FTransform& T, bool bForceNoCollision = false);
	void AddPieceAt(FName Name, const FVector& Loc, float Yaw, float Scale = 1.f, bool bForceNoCollision = false);
	void AddToGroup(FBld& B, int32 BI, int32 Group, FName Name, const FTransform& T);
	UPointLightComponent* AddLight(const FVector& Loc, const FLinearColor& Color, float Candelas, float Radius, float Flicker, FName Tag = NAME_None);
	void AddEffect(FName Name, const FVector& Loc, float Scale = 1.f);
	int32 AddContainer(FName Name, const FVector& Loc, float Yaw, const FString& Kind);
	USceneComponent* AddPivot(USceneComponent* Parent, const FTransform& Rel);
	UStaticMeshComponent* AddMesh(USceneComponent* Parent, UStaticMesh* Mesh, const FTransform& Rel, bool bCollision);

	// building frame
	FVector BldPoint(const FBld& B, float X, float Y, float Z = 0.f) const { return FVector(B.C + B.Fx * X + B.Fy * Y, Z); }
	FVector2D BldLocal(const FBld& B, const FVector2D& W) const { return FVector2D(FVector2D::DotProduct(W - B.C, B.Fx), FVector2D::DotProduct(W - B.C, B.Fy)); }
	static FName StyleName(EIVStyle S);
	FName KitPiece(const FBld& B, const TCHAR* Part) const;
	/** furniture in a house: Local = footprint centre in the building frame, LocalYaw = its front direction there.
	 *  Returns false (nothing placed) when it would overlap something or block the door. */
	bool Place(FBld& B, FName Name, const FVector2D& Local, float LocalYaw, bool bContainer = false, float Clear = 12.f, bool bBlocks = true, float Z = 0.f);
	/** against the inside of a wall (side 0 back -X, 1 front +X, 2 -Y, 3 +Y) at U = 0..1 along it */
	bool PlaceWall(FBld& B, FName Name, int32 Side, float U, bool bContainer = false, float Gap = 6.f);
	/** tries positions along the walls in turn; returns the side used or -1 */
	int32 PlaceAnyWall(FBld& B, FRandomStream& R, FName Name, bool bContainer = false, int32 PreferSide = -1);
	bool PlaceFree(FBld& B, FRandomStream& R, FName Name, bool bContainer = false, int32 Tries = 14);
	/** a small thing on top of a piece that was just placed (table top...): no collision, no footprint */
	void PlaceOn(FBld& B, FName Name, const FVector2D& Local, float Z, float LocalYaw, float Scale = 1.f);
	FVector2D InnerHalf(const FBld& B) const;
	/** can she still walk from the front door to every container of the house being furnished (and to ExtraStand) */
	bool InteriorOk(const FBld& B, FVector* ExtraStand) const;

	// outdoors
	bool IsFreeOutdoor(const FVector2D& P, float Radius) const;
	bool PlaceOutdoor(FName Name, const FVector2D& P, float Yaw, float Scale = 1.f, bool bSolid = true, float Radius = -1.f, bool bCheck = true);
	bool TreeAllowed(const FVector2D& P, float Height, float Radius) const;
	void AddFence(const FVector2D& A, const FVector2D& B, FRandomStream& R, float GapChance);
	void MapTree(const FVector2D& P, float Radius, float Height, uint8 Type) { FIVMapTree T; T.P = P; T.Radius = Radius; T.Height = Height; T.Type = Type; MapTrees.Add(T); }
	void MapProp(const FVector2D& P, float Yaw, uint8 Type) { FIVMapProp T; T.P = P; T.Yaw = Yaw; T.Type = Type; MapProps.Add(T); }

	// nav
	FIntPoint NavIndex(const FVector2D& W) const;
	void NavBox(const FVector2D& C, const FVector2D& Fx, const FVector2D& Fy, const FVector2D& Half, uint8 Value, float Grow = 0.f);
	void NavDisc(const FVector2D& C, float Radius, uint8 Value);
	void NavBuilding(const FBld& B);
	static FIntPoint GlobalCell(const FVector2D& W);
};
