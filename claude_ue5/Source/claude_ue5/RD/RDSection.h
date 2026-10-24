// random_dungeon_level: one 252 m x 252 m dungeon section (84 x 84 tiles of 3 m). Plan() lays out the rooms and hallways
// from (section, seed) alone; the static part (floors, walls, ceilings, furniture as instanced meshes, lights, fire
// effects) is built once (saved with the level for the editor-built start section) and the interactive part (doors,
// containers, monsters, map data) is rebuilt for play.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RDTypes.h"
#include "RDSection.generated.h"

class ARDDungeonGenerator;
class ARDMonster;
class UInstancedStaticMeshComponent;
class UStaticMeshComponent;
class UPointLightComponent;
class UMaterialInterface;

/** a fire that is heard in play: 0 torch, 1 brazier / cooking fire, 2 hearth */
struct FRDFirePoint { FVector At; uint8 Kind; };

UCLASS()
class CLAUDE_UE5_API ARDSection : public AActor
{
	GENERATED_BODY()

public:
	ARDSection();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") FIntPoint Coord = FIntPoint::ZeroValue;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") int32 Seed = 0;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") bool bEditorBuilt = false;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") TObjectPtr<ARDDungeonGenerator> Generator;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") int32 NumInstances = 0;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") int32 NumLights = 0;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") float GenerateMs = 0.f;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") TArray<TObjectPtr<ARDMonster>> SpawnedMonsters;
	/** the section's fires (play only; also of the saved start section): the generator gives the nearest a looping voice */
	TArray<FRDFirePoint> FirePoints;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") int32 GetNumFirePoints() const { return FirePoints.Num(); }
	/** flame and smoke particles alive now in this section's effects within Radius of Location (tests: a light without a
	    flame counts 0; far effects are asleep and count 0 too) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") int32 GetEffectParticlesNear(FVector Location, float Radius) const;
	/** effect components within Radius of Location */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") int32 GetNumEffectsNear(FVector Location, float Radius) const;
	/** how many of this section's wall segments use each wall piece (tests: the variants of a broken wall) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") TMap<FName, int32> GetWallPieceCounts() const { return WallCounts; }
	/** wall segments that got the same piece as the segment before them along the wall or below them, among walls with variants */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") int32 GetWallRepeats() const { return WallRepeats; }
	/** the wall segments that got a backing or a seal (a wall piece "<name>_Back" / "<name>_Seal" in the generator's Pieces:
	 *  the broken walls): each segment's frame (wall line, room face toward +X) and its piece. Tests. */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") TArray<FTransform> GetBackedWallSegments(TArray<FName>& Names) const { Names = WallSegmentNames; return WallSegments; }
	/** the prison cells: each cell's frame (its middle on the floor, toward the room = +X) and where its hay pile stands;
	 *  how many cell sides got bars. Tests. */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") TArray<FTransform> GetPrisonCells(TArray<FVector>& Hay) const { Hay = CellHay; return CellFrames; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") int32 GetPrisonCellSides() const { return CellSides; }
	/** random_dungeonmagic_level5: where its anvils stand (the furniture's AnvilPiece; play also for the saved start section) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") TArray<FVector> GetAnvilPoints() const { return AnvilPoints; }
	/** the room the anvil added by EnsureAnvil stands in (-1: none was added) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") int32 AnvilRoom = -1;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") FVector GetFirePoint(int32 Index) const { return FirePoints.IsValidIndex(Index) ? FirePoints[Index].At : FVector::ZeroVector; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") int32 GetFireKind(int32 Index) const { return FirePoints.IsValidIndex(Index) ? FirePoints[Index].Kind : -1; }
	/** prefab actors (bookshelves, candle stands...) owned by the section */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") TArray<TObjectPtr<AActor>> OtherActors;

	/** editor build or runtime generation: plan + static + interactive (+ monsters and map data in play) */
	void Generate(ARDDungeonGenerator* InGenerator, FIntPoint InCoord, int32 InSeed, bool bEditorBuild);
	/** runtime generation spread over frames: BeginGenerate builds the shell and doors (and registers the map),
	 *  ContinueGenerate furnishes rooms / hallways within a time budget; true once finished (monsters spawned) */
	void BeginGenerate(ARDDungeonGenerator* InGenerator, FIntPoint InCoord, int32 InSeed, bool bEditorBuild);
	bool ContinueGenerate(double BudgetSeconds);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") bool IsBuilding() const { return bBuilding; }
	/** saved (editor-built) section at the start of play: plan again, rebuild the interactive part, monsters, map data */
	void ActivateForPlay();
	/** generation indicator: translucent walls on the section border (UV.y 0 at the floor, 1 at the top) */
	void ShowCurtain(UMaterialInterface* Material, float StartTime, float Height, float Lifetime);

	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") FVector2D GetSectionMin() const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") int32 GetNumRooms() const { return Rooms.Num(); }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") int32 GetNumDoors() const { return Doors.Num(); }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") int32 GetNumContainers() const { return Containers.Num(); }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") FVector GetDoorLocation(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") float GetDoorOpenAlpha(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") bool IsDoorCell(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") FVector GetContainerLocation(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") float GetContainerOpenAlpha(int32 Index) const;
	/** it was opened once: what it held was found (a wardrobe's two doors are one container). Kept by the generator, so a
	 *  section dropped and generated again has its looted containers looted still; it never fills again */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool IsContainerLooted(int32 Index) const;
	/** the index a container's loot is kept under (a wardrobe's two doors: the lower) */
	int32 ContainerKey(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") FString GetContainerKind(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") FString GetRoomKind(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") FVector GetRoomCenter(int32 Index) const;
	/** room rectangle (world XY min / max) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") void GetRoomBounds(int32 Index, FVector2D& Min, FVector2D& Max) const;
	/** walkable tile centres of a room (walk test) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") TArray<FVector> GetRoomFreeTiles(int32 Index) const;
	/** room index at a world location (-1: none / hallway) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") int32 RoomAt(FVector Location) const;
	/** tile path between two world points over walkable tiles (tile centres, world); empty if none */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") TArray<FVector> FindPathWorld(FVector From, FVector To) const;
	/** number of rooms reachable from the first room over walkable tiles and doorways (connectivity check) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") int32 CountReachableRooms() const;
	/** world points of the hallway ends on this section's border (walk test) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") TArray<FVector> GetPortalPoints() const;
	/** the section a hallway end leads into; Border: where the hallway meets the section's border (world, on the floor),
	 *  Outward: the way out of this section */
	FIntPoint PortalNeighbour(int32 Portal, FVector& Border, FVector& Outward) const;
	int32 GetNumPortals() const { return Portals.Num(); }

	// ---- random_dungeonmagic_level5: tiers
	/** monsters its spawning order planned (the killed ones too) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") int32 MonstersPlanned = 0;
	/** its chests and trunks, by container key (what the tiers count as its loot) */
	TArray<int32> GetChestKeys() const;
	/** a grating across each hallway end into a section the generator will not generate yet, a wall at the end of the
	 *  dungeon (GetSealKind), each with a blocker as tall as the hallway; rebuilt as the tiers open */
	void UpdateSeals();
	/** hallway ends sealed now (Kind 1: a grating, 2: a wall; 0: both) and where (world, on the border) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") int32 GetNumSeals(int32 Kind = 0) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") TArray<FVector> GetSealPoints(TArray<int32>& Kinds) const { Kinds = SealKinds; return SealAt; }

	// ---- interaction (doors, containers)
	/** nearest door / container within MaxDistance: returns distance (or 1e9) */
	float FindNearestInteractive(const FVector& From, float MaxDistance, bool& bDoor, int32& Index) const;
	/** opener: who is pushing (the door swings away) */
	void ToggleDoor(int32 Index, const FVector& Opener, bool bByMonster = false);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") void ToggleContainer(int32 Index);
	bool IsDoorOpenIndex(int32 Index) const;
	/** open or opening (target) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool IsTargetOpen(bool bDoor, int32 Index) const;

	// ---- monsters (tile pathing)
	FIntPoint WorldToLocal(const FVector& L) const;
	FVector LocalToWorld(FIntPoint T) const;
	bool IsWalkable(FIntPoint Local) const;
	/** door index on the edge between two adjacent local tiles (-1 if none) */
	int32 DoorBetween(FIntPoint A, FIntPoint B) const;
	bool FindPath(FIntPoint From, FIntPoint To, TArray<FIntPoint>& Out) const;
	FIntPoint RandomRoomTile(FRandomStream& R, int32 NotRoom = -1) const;
	int32 RoomAtLocal(FIntPoint Local) const;

	// ---- map
	FRDSectionMap BuildMapData() const;

protected:
	virtual void BeginPlay() override;
	virtual void Destroyed() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	struct FRoom
	{
		FIntPoint Min, Max;       // local tiles, max exclusive
		ERDRoomKind Kind = ERDRoomKind::Junction;
		int32 Block = 0;
		FIntPoint Lane;           // local tile: centre row (Y) and centre column (X) kept free (door lines)
		bool bDoorSide[4] = { false, false, false, false };    // -X, +X, -Y, +Y
	};
	struct FCorr { FIntPoint Min, Max; bool bHoriz = true; int32 Theme = 0; };
	struct FMover
	{
		USceneComponent* Pivot = nullptr;
		TArray<UStaticMeshComponent*> Parts;
		FQuat Closed = FQuat::Identity;
		FVector Axis = FVector::UpVector;
		float OpenAngle = 95.f;
		float Alpha = 0.f, Target = 0.f;
		bool bDoor = false, bCell = false;
		bool bByMonster = false;
		float MonsterCloseTimer = 0.f;
		FString Kind;
		FVector Center = FVector::ZeroVector;
		FVector Normal = FVector::ZeroVector;   // doors: leaf normal (world) when closed
		float LeafSign = 1.f;                    // doors: +1 when the leaf extends along +Y of its pivot
		FIntPoint TileA = FIntPoint(-1), TileB = FIntPoint(-1);
		int32 Partner = -1;                      // double door / wardrobe partner
		bool bLooted = false;                    // containers: opened once (what it held was found)
	};
	struct FFlicker { UPointLightComponent* Light; float Base; float Phase; float Amount; };

	// plan (pure function of Coord + Seed)
	int32 N = 84;
	TArray<FRoom> Rooms;
	TArray<FCorr> Corrs;
	TArray<uint8> Type;        // 0 void, 1 room, 2 hallway
	TArray<int16> Owner;       // room index, or 1000 + hallway index
	TArray<uint8> Blocked;     // furniture on the tile (monster pathing)
	TMap<int64, int32> DoorEdges;
	TArray<FIntPoint> Portals; // local tiles of hallway ends on the border

	// build state
	bool bBuildStatic = true, bBuildInteractive = true;
	bool bNoBlock = false;          // hallway decoration: never blocks a tile (1-tile passages)
	bool bBuilding = false;
	int32 NextRoom = 0, NextCorr = 0;
	FRandomStream GenR;
	double GenStart = 0.0, ShellMs = 0.0, FurnishMs = 0.0;
	int32 GenTicks = 0;
	TArray<FBox2D> QuadBoxes;       // furnishing: the current room's quadrants (between the lanes and the walls)
	TMap<UStaticMesh*, UInstancedStaticMeshComponent*> Hisms;
	TMap<UStaticMesh*, UInstancedStaticMeshComponent*> HismsNoCol;
	TMap<UStaticMesh*, TArray<FTransform>> Pending, PendingNoCol, PendingHidden;
	TMap<UStaticMesh*, UInstancedStaticMeshComponent*> HismsHidden;
	TArray<FMover> Doors;
	TArray<FMover> Containers;
	TArray<FFlicker> Flickers;
	TArray<FTransform> MonsterSpawns;
	UPROPERTY(Transient) TArray<TObjectPtr<USceneComponent>> SealComps;
	TArray<FVector> SealAt;
	TArray<int32> SealKinds;

	int32 Idx(FIntPoint T) const { return T.Y * N + T.X; }
	bool In(FIntPoint T) const { return T.X >= 0 && T.Y >= 0 && T.X < N && T.Y < N; }
	static int64 EdgeKey(FIntPoint A, FIntPoint B);

	void Plan(FRandomStream& R);
	void BuildShell(FRandomStream& R);
	void ShellPrepare(FRandomStream& R);
	void ShellColumn(FRandomStream& R, int32 X);
	void ShellCorners();
	TArray<FName> ShellFloor, ShellWall;
	// a wall piece's variants ("Wall_Rough", "Wall_Rough_2", ...) and which one each segment got (key: tile, side, layer)
	TMap<FName, TArray<FName>> WallVariants;
	TMap<uint32, uint8> WallPicks;
	UPROPERTY() TMap<FName, int32> WallCounts;
	UPROPERTY() int32 WallRepeats = 0;
	UPROPERTY() TArray<FTransform> WallSegments;
	UPROPERTY() TArray<FName> WallSegmentNames;
	UPROPERTY() TArray<FTransform> CellFrames;
	UPROPERTY() TArray<FVector> CellHay;
	UPROPERTY() int32 CellSides = 0;
	FName WallVariant(FName Name, const FIntPoint& T, int32 Side, int32 Layer);
	int32 ShellX = 0;
	void Furnish(FRandomStream& R, int32 RoomIndex);
	/** level 5 (generator bAnvilEverySection): an anvil for a section whose furniture brought none */
	void EnsureAnvil();
	TArray<FVector> AnvilPoints;
	void DecorateCorridor(FRandomStream& R, int32 CorrIndex);
	void ClearInteractive();
	void SpawnMonsters(FRandomStream& R);
	void FlushInstances();
	void RegisterMap();
	void CollectFlicker();
	void AddDoors();

	// placement helpers (world space)
	FVector TileWorld(FIntPoint Local, float Z = 0.f) const;
	void AddPiece(FName Name, const FTransform& T, bool bForceNoCollision = false);
	void AddPieceAt(FName Name, const FVector& Loc, float Yaw, float Scale = 1.f, bool bForceNoCollision = false);
	UPointLightComponent* AddLight(const FVector& Loc, const FLinearColor& Color, float Candelas, float Radius, bool bShadows, float Flicker);
	void AddEffect(FName Name, const FVector& Loc, float Scale = 1.f);
	void AddTorch(const FVector& WallPoint, float InYaw, float Candelas, bool bLit = true);
	void AddDoor(FIntPoint RoomTile, FIntPoint OutTile, int32 RoomIndex);
	void AddCellDoor(const FVector& HingeWorld, float Yaw, float Width);
	void AddContainer(FName Name, const FVector& Loc, float Yaw, const FString& Kind);
	void MarkBlocked(const FVector& Loc, float Yaw, const FVector2D& Size, bool bLaneToo = false);
	USceneComponent* AddPivot(USceneComponent* Parent, const FTransform& Rel);
	UStaticMeshComponent* AddMesh(USceneComponent* Parent, UStaticMesh* Mesh, const FTransform& Rel, bool bCollision);

	// furnishing helpers: room-local geometry
	FBox2D RoomBox(const FRoom& Rm, float Inset = 0.f) const;
	/** points along the inside of a wall (side 0..3), every Spacing, keeping Clear cm from the lane door lines */
	TArray<FVector> WallSlots(const FRoom& Rm, int32 Side, float Spacing, float Clear, float Margin) const;
	static float InwardYaw(int32 Side);
	bool LaneFree(const FRoom& Rm, const FVector& P, float Radius) const;
	void FurnishWalls(FRandomStream& R, const FRoom& Rm, const TArray<FName>& Names, float Spacing, float Chance, bool bContainers = false);
	void LightRoom(FRandomStream& R, const FRoom& Rm, int32 RoomIndex);
};
