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

/** a container's moving part opens 100 degrees about Axis, the way that swings its middle (Tip, from the hinge) toward Want: the
 *  sign of that turn (the dungeon's containers and the wilds' (AddWildBox) alike) */
inline float RDContainerSign(const FVector& Axis, const FVector& Tip, const FVector& Want)
{
	const FVector P = FQuat(Axis, FMath::DegreesToRadians(60.f)).RotateVector(Tip);
	return FVector::DotProduct(P - Tip, Want) >= 0.f ? 1.f : -1.f;
}

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

	// ---- mistward_castle
	/** the set's theme (its pieces "<Theme>.<Name>") */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") FName Theme;
	/** a room's shape ("rect", "circle", "octagon", "hexagon", "triangle", "L", "T", "U", "dome", "pyramid", "tall") */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") FString GetRoomShape(int32 Index) const;
	/** mistward5: a room's ceiling ("flat", "raised", "beamed", "sail dome", "groin vault", "barrel vault", "cloister vault",
	 *  "hipped"), where its vault springs and how high it rises (cm over the floor; 0 for a flat one) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") FString GetRoomCeiling(int32 Index, float& Spring, float& Rise) const;
	/** the ceiling's height over the floor at a world point of a room (its vault, else its tile's) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetCeilingHeightAt(FVector Location) const;
	/** procedural vault meshes built (tests) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") int32 VaultMeshes = 0;
	/** a room's floor tiles (world, tile centres) and the height of the ceiling over each */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") TArray<FVector> GetRoomTiles(int32 Index, TArray<float>& Heights) const;
	/** furniture that collides, as placed (tests): each footprint's middle, half size (x, y) and yaw; the containers'
	 *  ways in (the space before their fronts) as the same */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") TArray<FVector> GetFootprints(TArray<FVector>& HalfYaw, TArray<FString>& Names) const;
	/** counts what a set of rooms would hold without building it: rooms (not the hallway junctions), chests and trunks, the
	 *  monsters its spawning plans (the tiers' share rule for sets she has not reached) */
	static bool Census(ARDDungeonGenerator* InGenerator, FIntPoint InCoord, int32 InSeed, int32& OutRooms, int32& OutChests, int32& OutMonsters);
	/** its traps: their kind, where, whether set off, spent, disarmed, seen by her (RDTraps.cpp) */
	struct FTrapInst
	{
		int32 Def = 0; FVector At = FVector::ZeroVector; float Yaw = 0.f; int32 Room = -1; bool bHall = false;
		uint8 State = 0;          // 0 set, 1 going off, 2 spent, 3 disarmed
		bool bSeen = false;
		float Time = 0.f, Next = 0.f, Stay = 0.f; int32 Step = 0;
		FVector Goal = FVector::ZeroVector;
		TArray<TWeakObjectPtr<USceneComponent>> Comps;
		TWeakObjectPtr<UStaticMeshComponent> Moving;
		TArray<TWeakObjectPtr<class UFXSystemComponent>> Fx;
	};
	TArray<FTrapInst> TrapList;
	/** what a trap throws or drops, on its way: darts, stones, the crusher's block */
	struct FTrapShot { TWeakObjectPtr<UStaticMeshComponent> C; FVector Vel = FVector::ZeroVector; FVector Goal = FVector::ZeroVector; int32 Trap = -1; uint8 Kind = 0; bool bDone = false; float Life = 0.f; };
	TArray<FTrapShot> TrapShots;
	void TickTraps(float Dt, class APawn* Her, class URDCombatComponent* Pc);
	/** a trap's strike on her (its share of her hit points) if she is within Radius of At */
	void TrapStrike(int32 Index, const FVector& At, float Radius, float Share);
	void TrapShoot(int32 Index, uint8 Kind, const FVector& From, const FVector& To, float Speed);
	/** tests: a trap of a kind added where she stands (it goes off at once) */
	int32 AddTrapAt(int32 Def, const FVector& At, uint8 State);
	/** where a teleport or a spring plate puts her: three monsters of the set's tier round At, or four glyphs going off one
	 *  after the other round her (by H); the message names the trap (How). Adds to TrapList: hold no reference into it. */
	void TrapAmbush(const FVector& At, uint32 H, const TCHAR* How);
	/** tests: what the last ambush was ("monsters" / "glyphs") and where */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") FString LastAmbush;
	bool FireTrap(int32 Index);
	void SpendTrap(int32 Index, uint8 State);
	/** the prison cells and who is in each (0 nobody, 1 a prisoner, 2 a monster), the cell door's index */
	struct FCell { FTransform Frame; int32 Door = -1; uint8 Occupant = 0; int32 Def = 0; TWeakObjectPtr<AActor> Who; bool bOpened = false; };
	TArray<FCell> Cells;
	/** the cell whose door this is (-1: none) */
	int32 CellOfDoor(int32 Door) const;
	/** what F at a cell door does (mistward: a locked cell with someone in it); "" not a cell of these */
	FString DescribeCell(int32 Door) const;
	bool OpenCell(int32 Door);
	void TickCells(float Dt, class APawn* Her);
	/** the cells (tests): "<cell>|<door>|<occupant 0 none, 1 prisoner, 2 monster>|<opened>|<x>|<y>|<z>|<who there>|<who x>|<y>|<z>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward") TArray<FString> GetCellLines() const;
	/** the room with this section's teleporter pad (-1: none) */
	int32 PadRoom = -1;

	// ---- the third list (docs/improvements2.txt; RDMistward2.cpp)
	/** a trap she has seen: its outline and its ring on the floor (the generator's bTrapOutline) */
	void OutlineTrap(int32 Index);
	/** an armory table's weapon or shield to take up (the generator's bWeaponPickups): the item, where, its mesh */
	struct FPickup { FName Item; FVector At = FVector::ZeroVector; TWeakObjectPtr<UStaticMeshComponent> Mesh; };
	TArray<FPickup> Pickups;
	/** a special room's fixture (a shrine's statue, a fountain), what it is and its glow */
	struct FFixture { ERDRoomKind Kind = ERDRoomKind::Shrine; FVector At = FVector::ZeroVector; int32 Room = -1;
		TWeakObjectPtr<class UPointLightComponent> Light; TWeakObjectPtr<class UFXSystemComponent> Fx; };
	TArray<FFixture> Fixtures;
	/** the special rooms laid out (the generator's bSpecialRooms), from a stream of their own after the plan's rooms */
	void AssignSpecialRooms();
	/** their play part (after the furniture, in play): fixtures' glows, the vault's key and chests, the throne's usurper */
	void PlaceSpecial();
	/** the special rooms' containers whose loot the rules set (the vault's chests, the gauntlet's chest): their keys */
	TArray<int32> SpecialChests;
	/** a fixture used: its glow dimmed */
	void DimFixture(int32 Index);
	/** a room's doors shut (an arena beginning) */
	void ShutRoomDoors(int32 Room);
	/** the room a door leads into or out of (-1: a hallway's or a cell's) */
	int32 DoorRoom(int32 Door) const;
	/** a room's doors (both leaves of each doorway; tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") TArray<int32> GetRoomDoors(int32 Room) const
	{
		TArray<int32> Out;
		for (int32 I = 0; I < Doors.Num(); ++I) if (DoorRoom(I) == Room) Out.Add(I);
		return Out;
	}
	/** a weapon or shield laid flat on a table at P (its longest side across the table, turned Yaw) */
	void AddPickup(FName Item, const FVector& P, float Yaw);
	ERDRoomKind GetRoomKindEnum(int32 Index) const { return Rooms.IsValidIndex(Index) ? Rooms[Index].Kind : ERDRoomKind::Junction; }
	/** free tiles of a room in the order of their distance from its middle (the arena's spawns) */
	TArray<FVector> GetRoomFreeTilesNear(int32 Index, const FVector& From) const;

	// ---- Brokenspire (the generator's bTown; RDTownPlan.cpp): the start section is the town. Its tiles: the walkable ground
	// is one hallway (Corrs[0], owner 1000), each building's rooms are rooms; the town wall's ring and what stands outside it
	// are void. Buildings are House Forge's modules (the village's pieces, "Town.<style>_<part>"), the castle the dungeon's
	// Castle theme turned out and in; doors are single leaves on the building's doorway.
	/** a building of the town: its kind (RDTownKinds), its rectangle (local tiles, max exclusive), its door (side 0 -X, 1 +X,
	 *  2 -Y, 3 +Y; the tile inside it), its state (0 lived in, 1 burned, 2 boarded), style, its rooms */
	struct FTownBld
	{
		uint8 Kind = 0; FIntPoint Min = FIntPoint::ZeroValue, Max = FIntPoint::ZeroValue;
		int32 DoorSide = 0; FIntPoint DoorTile = FIntPoint::ZeroValue; uint8 State = 0; uint8 Style = 0; int32 Storeys = 2;
		TArray<int32> Rooms; int32 Door = -1; bool bBoarded = false; uint32 Seed = 0; FString Label;
	};
	TArray<FTownBld> TownBlds;
	/** what stands outside: its kind (RDTownSpots), where, its yaw (and the building it belongs to, -1) */
	struct FTownSpot { uint8 Kind = 0; FVector At = FVector::ZeroVector; float Yaw = 0.f; int32 Bld = -1; };
	TArray<FTownSpot> TownSpots;
	/** the straight cobbled roads, the forecourt and the stair turret's path (local tile rectangles, max exclusive) */
	TArray<FIntRect> TownRoads;
	/** the winding earth roads (since 2026-11-02): their middles (world XY) and half their width (cm) */
	struct FTownPath { TArray<FVector2D> Pts; float HalfWidth = 300.f; };
	TArray<FTownPath> TownPaths;
	/** the wall's outline (world XY, in order round the town; since 2026-11-02 it is irregular) */
	TArray<FVector2D> TownBorder;
	/** the watchtowers' doors from the town (x, y: the door's middle; z: the spiral's start angle, world yaw) and their middles */
	TArray<FVector> TownTowerDoors, TownTowerMids;
	/** a tile's road: 0 none, 1 cobbles, 2 an earth road, 3 the lane inside the wall */
	TArray<uint8> TownRoadMask;
	bool InsideTownBorder(const FVector2D& World) const;
	float TownBorderDist(const FVector2D& World) const;
	/** a trade's sign's words, painted on both faces of its board (SignT: the sign piece's transform) */
	void AddSignText(const FTransform& SignT, const FString& Text);
	/** a hidden box over a piece's whole mesh bounds as placed (a window's sill its own collision leaves out) */
	void AddMeshBoundsCollider(FName Piece, const FTransform& T);
	/** each earth road's wander (tests): the farthest its middle goes from the straight line between its ends, m */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") TArray<float> GetTownPathWander() const;
	/** the town's outline and earth roads for tests: "border|x|y" a corner, "path|<n points>|<half width>", "roads|<cobble tiles>|<earth tiles>|<lane tiles>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") TArray<FString> GetTownShapeLines() const;
	FIntRect TownSquare;
	/** inside the town wall (local tiles, max exclusive) */
	FIntRect TownInner;
	/** a tile's ground: 0 void (outside the wall, a tower), 1 ground, 2 a room (Type) */
	uint8 TownTileType(FIntPoint Local) const { return In(Local) && Type.Num() == N * N ? Type[Idx(Local)] : 0; }
	int32 GetTownTiles() const { return N; }
	/** the gate (its tiles' middle, world; the way out) and the Mistgate (the castle hall's back wall: walking into it opens
	 *  Mistward Castle); the castle hall's room */
	FVector TownGate = FVector::ZeroVector, TownGateOut = FVector::ZeroVector, MistgateAt = FVector::ZeroVector, MistgateNormal = FVector::ZeroVector;
	/** Kethrys Spire's black tower: the top of its round tower (cm over the town's ground; 0 none) (tests) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Town") float TowerTopZ = 0.f;
	/** Heaven: its tallest tower's top (cm over the town's ground) and its shield's radius (cm; 0 none) (tests) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Town") float HeavenTallestZ = 0.f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Town") float HeavenDomeRadius = 0.f;
	/** Heaven's traffic: a car driving one street's lane, turning back into the other lane at the street's end */
	struct FRDHeavenCar
	{
		TWeakObjectPtr<USceneComponent> C;
		FVector L0 = FVector::ZeroVector, L1 = FVector::ZeroVector;      // (the street's middle line, its ends)
		float Lane = 220.f, S = 0.f, Speed = 900.f;
		int32 Street = 0;          // (its street: a car checks only the cars of its street ahead of it)
		bool bFwd = true;
	};
	TArray<FRDHeavenCar> HeavenCars;
	int32 CastleHallRoom = -1, CastleBld = -1;
	/** the castle's round corner towers (the user's of 2026-11-02: medieval walls, not the dungeon's arches): their middles
	 *  (world, z 0), which of them holds the stair up to the wall walk (-1 none), its ground door and its door onto the walk */
	TArray<FVector> CastleTowers;
	int32 CastleStairTower = -1;
	FVector CastleStairDoor = FVector::ZeroVector, CastleWalkDoor = FVector::ZeroVector;
	/** the wall walk's height (the roof's top over the castle; world z above the section) */
	float CastleWalkZ = 0.f;
	/** the trees, bushes and grass of the town as placed (x, y, kind: 1-3 a tree, 4 a bush): the papyrus map draws them */
	TArray<FVector> TownGreens;
	/** the town's work (the third list, 2026-11-02: "the town should look more lively"): a place where a townsperson does a
	 *  kind of work, its clip's name ("Stir" at a cooking pot, "Crank" at a spit, "Tend" in a garden, "Scatter" at a pen,
	 *  "SitDrink" / "SitTalk" on a tavern's seat, "CarryIdle" serving at a tavern's table, "Talk" at the well, the bar or a
	 *  camp, "Hammer" / "Forge" in the smithy), where its feet go (world) and which way it faces; its group (RDTownWorkGroup:
	 *  the kinds of place a round of work is made of), its building (-1 outdoors) and the thing it holds (a prop's name) */
	struct FTownWork { FName Kind; FVector At = FVector::ZeroVector; float Yaw = 0.f; uint8 Group = 0; int32 Bld = -1; FName Prop; int32 Thing = -1; };
	TArray<FTownWork> TownWorks;
	/** the pens (world: middle, half size along and across its yaw) and the animal kind in each (the generator's TownAnimals) */
	struct FTownPen { FVector At = FVector::ZeroVector; FVector2D Half = FVector2D(300.f, 300.f); float Yaw = 0.f; int32 Animal = 0; };
	TArray<FTownPen> TownPens;
	/** the gardens (world: middle, half size, yaw) and how many plants grow in each */
	struct FTownGarden { FVector At = FVector::ZeroVector; FVector2D Half = FVector2D(300.f, 150.f); float Yaw = 0.f; int32 Plants = 0; TArray<uint8> Crops; };
	TArray<FTownGarden> TownGardens;
	// ---- the user's list of 2026-11-04 (docs/improvements7.txt; RDTownPlan.cpp, RDTown7.cpp)
	/** the bread ovens of the town's kitchens (world): F at one bakes the oven's recipes */
	TArray<FVector> TownOvens;
	/** food set out on a table (bread, cheese, apples): F takes it (its items), its meshes go */
	struct FTownFood { FVector At = FVector::ZeroVector; TArray<FName> Items; TArray<TWeakObjectPtr<UStaticMeshComponent>> Comps; bool bTaken = false; };
	TArray<FTownFood> TownFoods;
	/** the gate's portcullis (a door that lifts) and the levers that raise it, the pens' gates (all indices into the doors) */
	int32 TownPortcullis = -1;
	TArray<int32> TownLevers, TownPenGates;
	// ---- the list of 2026-11-07 (docs/improvements8.txt; RDTown8.cpp)
	/** the barracks' training dummies and targets: a mesh of their own on a pivot at their foot (play only, never instanced), rocked
	 *  away from a blow or a bolt that meets them (a swing that dies away) */
	struct FTownDummy
	{
		TWeakObjectPtr<USceneComponent> Pivot; TWeakObjectPtr<UStaticMeshComponent> Mesh;
		/** its body for bolts: a capsule round it on its pivot (query only, Visibility): a bolt's trace is simple, and the dummy's
		 *  simple collision is its post alone, so bolts flew through its straw body (the TODO sweep, 884 dummies) */
		TWeakObjectPtr<UPrimitiveComponent> Body;
		FVector At = FVector::ZeroVector; FQuat Rest = FQuat::Identity; FName Kind;
		float Radius = 40.f, Height = 180.f;
		FVector Axis = FVector(0, 1, 0); float HitAt = -100.f, Amp = 0.f; int32 Hits = 0;
	};
	TArray<FTownDummy> TownDummies;
	void AddTownDummy(FName Kind, const struct FRDPiece* P, const FTransform& T, float Lift);
	/** rocks dummy I away from From (Strength 1 a full blow) */
	void HitTownDummy(int32 I, const FVector& From, float Strength);
	void TickTownDummies(float Now);
	/** the dummy whose mesh is C (a bolt's trace hit it), -1 none */
	int32 TownDummyOf(const UPrimitiveComponent* C) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") TArray<FString> GetTownDummyLines() const;
	/** the ground's rise and fall (the list's "terrain above and below the ground level"): a weight per tile (0 flat where
	 *  anything stands or is walked to, 1 open ground), the height there is TownLiftAt */
	TArray<float> TownLiftW;
	bool bTownLiftOn = false;
	/** the ground's height (cm, from the section's z) at a world point: 0 where buildings, roads, gardens, pens and the
	 *  square are, rising and falling up to TownLiftAmp over open ground */
	float TownLiftAt(const FVector2D& World) const;
	/** tests: the ground's height at a point (cm over the section) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") float GetTownLiftAt(FVector Location) const { return TownLiftAt(FVector2D(Location)); }
	/** tests: "gate|<door>|<open target>|<alpha>|<x>|<y>|<z>", "lever|<door>|<x>|<y>|<z>", "pengate|<door>|<open>|<x>|<y>|<z>",
	 *  "oven|<x>|<y>|<z>", "food|<i>|<taken>|<x>|<y>|<z>|<items, comma>", "garden|<i>|<crops, comma>|<x>|<y>", "lift|<max cm>|<min cm>|<under buildings max |cm|>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") TArray<FString> GetTownImproveLines() const;
	/** what F reaches of the list's things at From: "food", "oven", "garden", "lever", or "" (index set) */
	FString FindTownThing(const FVector& From, float Reach, int32& OutIndex) const;
	/** the portcullis's state kept by the game (Brokenspire's own: it stays as she left it) */
	void RecordPortcullis(bool bUp);
	/** the food of a table taken (its meshes hidden) */
	bool TakeTownFood(int32 Index);
	/** a door's index for the town's levers and gates (tests): the door at the lever pushed as F does */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Brokenspire") bool PullTownLever(int32 Lever, FVector Opener);
	/** the portcullis up (or on its way up) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") bool IsPortcullisUp() const { return Doors.IsValidIndex(TownPortcullis) && Doors[TownPortcullis].Target > 0.5f; }
	/** tests: the drawn ground's layers at a point (R trodden floor, G cobbles, A earth; -1 none) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") FLinearColor GetTownGroundColorAt(FVector Location) const;
	/** a door's kind ("door", "gate" (a pen's), "lever", "portcullis") */
	FString GetDoorKind(int32 Index) const { return Doors.IsValidIndex(Index) ? Doors[Index].Kind : FString(); }
	/** the spits (world: the rod's middle, its yaw): the generator turns their meat in play while someone turns the crank */
	TArray<FVector4> TownSpits;
	/** the short grass's clumps and the small bushes placed (tests) */
	int32 TownGrassClumps = 0, TownSmallBushes = 0;
	/** the castle's stair inside (the third list: "there should be a way down from the battlements to the floor of the
	 *  castle"): its foot and its top (world), and the tiles left open over it (no ceiling, no roof: the stairwell) */
	FVector CastleStairFoot = FVector::ZeroVector, CastleStairTop = FVector::ZeroVector;
	TArray<FIntPoint> CastleStairwell;
	int32 CastleStairRoom = -1;
	/** a library's bookshelves (the list of 2026-11-10: searched with F for scrolls, their parts and tomes): where each stands (its
	 *  middle), its yaw (its front toward the room, +X), its depth, its room */
	struct FShelf { FVector At = FVector::ZeroVector; float Yaw = 0.f; float Depth = 50.f; int32 Room = -1;
		/** the list of 2026-11-20: its door leaves' hinges (interactive parts: none without bShelfDoors15), how far open (0 to 1) */
		TWeakObjectPtr<USceneComponent> DoorL, DoorR; float Open15 = 0.f; };
	/** the list of 2026-11-20 (RDList15c.cpp): a shelf's doors hung (open at once if it was searched); a shelf's doors opened (swung
	 *  over ShelfSwing15's time, or at once) */
	void MakeShelfDoors15(int32 I);
	void OpenShelfDoors15(int32 I, bool bNow = false);
	TArray<int32> ShelfSwing15;
	/** the list of 2026-11-20 (item 22, bHearth15): the kit fireplace's flame cards (its slot 4) hidden on this section's saved pieces */
	void HideHearthCards15();
	void TickShelfDoors15(float Dt);
	/** a piece on a free tile off a room's lanes whose four neighbours are free, the nearest such to Anchor, its front toward the lane
	 *  (no random draw; its tile blocked; added to Points): the alchemist's and librarian's tables', the oven's rule */
	bool PlaceNearAnchor15(FName Piece, int32 RI, const FVector& Anchor, TArray<FVector>& Points);
	/** a bread oven by the start set's great hall's anvil */
	void EnsureOven15();
	/** a test's: the chapels' altars and pews as laid (by Furnish) */
	struct FChapel15 { int32 Room = -1; FVector Altar = FVector::ZeroVector; TArray<FTransform> Pews; };
	TArray<FChapel15> Chapels15;
	/** the forges of the set (the list of 2026-11-10: the generator's ForgePieces where they stand) and the one put by the anvil */
	TArray<FVector> ForgePoints;
	void EnsureForge();
	/** the list of 2026-11-16's fifth phase: the alchemist's and librarian's tables where they stand (recorded by AddPiece, in play
	 *  too for the saved start section); a dungeon's put by its anvil; a town building's after its furnishing */
	TArray<FVector> AlchemistPoints;
	TArray<FVector> LibrarianPoints;
	void EnsureTables14();
	void TownTables14(int32 BI);
	/** the list of 2026-11-10's fourth phase: the town's beds (where each stands, its yaw (its foot toward +X), its building, who
	 *  has it); the ones put in play for sleepers who had none (their meshes); the households' extra people planned */
	/** a made bed's tiles it blocked (freed with it: the townsfolk spawned again lay theirs afresh) */
	struct FTownBed { FVector At = FVector::ZeroVector; float Yaw = 0.f; int32 Bld = -1; int32 Taken = -1; bool bMade = false; TArray<int32> Blocks; };
	/** the made beds taken away: their meshes, footprints and blocked tiles (before the townsfolk are spawned again) */
	void ClearMadeTownBeds();
	TArray<FTownBed> TownBeds;
	UPROPERTY(Transient) TArray<TObjectPtr<class UStaticMeshComponent>> TownBedMeshes;
	int32 TownAdults2 = 0, TownHomeKids = 0, TownSquareKidsDropped = 0;
	/** a bed put in a building on a free tile of its rooms (no random draw); its index, -1 none */
	int32 AddTownBed(int32 Bld);
	/** the households' second grown-ups and children (bMorePeople) */
	void PlanHouseholds();
	/** a piece FurnishWalls placed: where (its middle), its yaw, its size */
	struct FPlacedPiece { FVector At = FVector::ZeroVector; float Yaw = 0.f; FVector Size = FVector::ZeroVector; };
	TArray<FShelf> Shelves;
	/** the stair's mesh of blocks and wall (the list of 2026-11-10; tagged RDCastleStair), for the tests */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TObjectPtr<class UProceduralMeshComponent> CastleStairMesh;
	/** the castle's towers and stair (tests; world): "tower|<x>|<y>|<stair 0/1>", "stairdoor|<x>|<y>|<z>", "walkdoor|<x>|<y>|<z>",
	 *  "stairmid|<x>|<y>|<z>", "spiral|<start angle in the castle's frame>|<quarter turns>", "walk|<z>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") TArray<FString> GetCastleShapeLines() const;
	/** the containers' building (-1 none) and where each townsperson stands or walks (role, the point, the building, wander
	 *  radius cm) */
	struct FTownPost { ERDTownRole Role = ERDTownRole::Townsfolk; FVector At = FVector::ZeroVector; float Yaw = 0.f; int32 Bld = -1; float Wander = 0.f; int32 Index = 0; };
	TArray<FTownPost> TownPosts;
	/** the building a world point is in (-1: outdoors) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") int32 TownBuildingAt(FVector Location) const;
	/** the building's kind name ("smithy", "home"...) */
	static FString TownKindName(uint8 Kind);
	/** a boarded house's boards are pried loose (F at its door): its door opens from then on */
	bool PryBoards(int32 Bld);
	/** the door of a boarded house that is still boarded (-1: none) */
	int32 BoardedDoorBld(int32 Door) const;
	/** a walk from L along Dir (Reach on): the door on the edge to the next tile, if closed, is opened (Opener L): -1 none in the
	 *  way (or open), 0 being opened (wait for it), 1 boarded (it never opens). The townsfolk's walks and the showcase tour */
	int32 OpenDoorAhead(const FVector& L, const FVector& Dir, float Reach, bool bByMonster);
	/** a door's index on the edge between two tiles (the town's walk test) */
	TArray<FVector> GetTownDoorPoints() const;

	// ---- interaction (doors, containers)
	/** nearest door / container within MaxDistance: returns distance (or 1e9) */
	float FindNearestInteractive(const FVector& From, float MaxDistance, bool& bDoor, int32& Index) const;
	/** opener: who is pushing (the door swings away) */
	void ToggleDoor(int32 Index, const FVector& Opener, bool bByMonster = false);
	/** tests: a door pushed by her from Opener, as F does (a locked room's door stays as it is) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") void PushDoor(int32 Index, FVector Opener) { if (Doors.IsValidIndex(Index)) ToggleDoor(Index, Opener); }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") void ToggleContainer(int32 Index);
	bool IsDoorOpenIndex(int32 Index) const;
	/** open or opening (target) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool IsTargetOpen(bool bDoor, int32 Index) const;

	// ---- the list of 2026-11-22's caves (RDCave16.cpp): a test's lines of the set's kit pieces and walkable tiles (the generator's
	// GetCavePieces16 / GetCaveTiles16 say what they hold)
	TArray<FString> CavePieces16() const;
	TArray<FString> CaveTiles16() const;
	/** the floor's height over the set's at a tile (the kit's rooms are uneven, its tunnels climb; 0 off the cave) */
	float CaveFloorAt16(FIntPoint Local) const { return In(Local) && CaveZ16.IsValidIndex(Idx(Local)) ? CaveZ16[Idx(Local)] : 0.f; }
	/** the floor near a tile she may stand on off the tiles (FloorZAt's, the safety net's) */
	float CaveFloorNear16(FIntPoint Local) const;
	/** how long the set's plan took (ms; the planner runs in one frame) */
	double PlanMs16 = 0.0, PlanStepMs16 = 0.0;

	// ---- monsters (tile pathing)
	FIntPoint WorldToLocal(const FVector& L) const;
	FVector LocalToWorld(FIntPoint T) const;
	bool IsWalkable(FIntPoint Local) const;
	/** door index on the edge between two adjacent local tiles (-1 if none) */
	int32 DoorBetween(FIntPoint A, FIntPoint B) const;
	bool FindPath(FIntPoint From, FIntPoint To, TArray<FIntPoint>& Out) const;
	FIntPoint RandomRoomTile(FRandomStream& R, int32 NotRoom = -1) const;
	int32 RoomAtLocal(FIntPoint Local) const;
	/** the catacombs: a local tile's floor over the set's (a stair's rise there; 0 off the stairs) */
	float StairRiseAt(FIntPoint Local) const { return IsStairTile(Local) ? StairZ[Idx(Local)] : 0.f; }
	/** the floor's height in the world under a point of the set (its own floor, or the stair's ramp there) */
	float FloorZAt(const FVector& P) const;

	// ---- map
	FRDSectionMap BuildMapData() const;

	/** the port's harbour (the list of 2026-11-11: the water under her, the ramps' lines for the tests) */
	bool HasHarbour() const { return TownHarbour.Area() > 0; }
	bool IsHarbourWaterTile(const FIntPoint& Local) const { return InHarbourWater(Local); }
	const TArray<FVector>& GetRampFeet() const { return TownRampFeet; }
	const TArray<FVector>& GetRampTops() const { return TownRampTops; }

	/** the list of 2026-11-22's seventh phase (RDList16e.cpp): a town building's interior (what TownFurnish lays in it) in instanced
	 *  components of its own, keyed by building, mesh (or a piece's own material) and collision, so the engine's occlusion culling
	 *  hides what its walls hide and the game's own rule can hide it whole; culled from 40 m (its small clutter from 25 m); its
	 *  windows (their middle on the wall, their way out) for the rule's sight lines */
	int32 Bld16 = -1;
	TMap<FString, UInstancedStaticMeshComponent*> HismsBld16;
	TMap<FString, TArray<FTransform>> PendingBld16;
	TMap<int32, TArray<TWeakObjectPtr<UInstancedStaticMeshComponent>>> TownBldIsm16;
	struct FTownWin16 { int32 Bld = -1; FVector At = FVector::ZeroVector, Out = FVector::ForwardVector; };
	TArray<FTownWin16> TownWindows16;

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
		uint8 Shape = 0;          // mistward: 0 rect (see RDShapeName)
		uint8 Ceil = 0;           // mistward5: its ceiling's style (RDCeilNames), how high a vault rises (cm)
		float CeilRise = 0.f;
	};
	/** mistward5: each room's ceiling style (its own stream after the plan) */
	void StyleCeilings();
	/** mistward5: the vaults, ribs and beams of the styled rooms (static build), from where their walls end */
	void ShellVaults();
	/** the top of each room's walls as stacked (a vault springs from there) */
	TArray<float> RoomWallTop;
	/** a vault's height over the floor at P in room RI (-1: the room has none) */
	float VaultHeightAt(int32 RI, const FVector& P) const;
	/** the vault's shape at (U, V) in -1..1 across the room: 0 at its walls, 1 at its crown */
	static float VaultShape(uint8 Style, float U, float V, bool bAlongX);
	/** mistward: a room tile's ceiling height (0: the room's or hallway's own) */
	TArray<float> CeilH;
	float CeilAt(FIntPoint T) const;
	/** the catacombs (the generator's bTierFloors, 2026-11-06): a hallway's stair up to the shallower set beyond the border, its
	 *  tiles' floor over the set's (the tile's middle) and the side of the tile it rises toward (255: no stair) */
	TArray<float> StairZ;
	TArray<uint8> StairSide;
	/** the stair's length in tiles and its rise over one tile, as the plan laid it (the ramp, the safety net and the tile
	 *  heights all read these) */
	int32 StairLen = 4;
	float StairRise = 0.f;
	bool IsStairTile(FIntPoint T) const { return In(T) && StairSide.IsValidIndex(Idx(T)) && StairSide[Idx(T)] != 255; }
	/** mistward: the room's shape cut out of its rectangle (tiles outside it void), the ceiling heights of the shapes that rise */
	void ShapeRoom(FRandomStream& R, int32 RI);
	/** mistward: a piece of the set's theme ("<Theme>.<Name>") or else the plain one, and the name that resolves to */
	const FRDPiece* Pc(FName Name) const;
	FName PcName(FName Name) const;
	/** PcName's answers for the theme they were found for (a name formatted and looked up once per piece name, not per piece) */
	mutable TMap<FName, FName> ThemeNames;
	mutable FName ThemeNamesOf;
	/** mistward (bTidyFurniture): footprints placed in the room being furnished; a container's way in */
	struct FFoot { FVector2D C; FVector2D H; float Yaw = 0.f; bool bAccess = false; FName Name; };
	TArray<FFoot> Feet;
	/** the town's every footprint and container's way in, kept past each room's furnishing (the list of 2026-11-10: a bed put
	 *  for a sleeper goes on none of them: PR #41's review) */
	TArray<FFoot> TownFeet;
	int32 FurnRoom = -1;
	bool FootFree(const FVector& Loc, float Yaw, const FVector2D& Size, bool bAccess) const;
	/** on the room's own floor (every tile under it is the room's) */
	bool OnRoomFloor(const FVector& Loc, float Yaw, const FVector2D& Size, int32 RI) const;
	void AddFoot(const FVector& Loc, float Yaw, const FVector2D& Size, bool bAccess, FName Name);
	/** a piece's footprint as built: its nominal size, or its mesh's box where that is bigger (a table's top, a wardrobe's
	 *  cornice), centred where the box is; and how far its front (+X) reaches from where it is placed */
	void FootOf(const struct FRDPiece* P, const FTransform& T, FVector& OutCenter, FVector2D& OutSize, float& OutFront) const;
	bool bCensus = false;
	int32 CensusChests = 0;
	void BuildShellCensus(FRandomStream& R);
	/** mistward: actors of its own (prisoners, the teleporter pad), gone with it */
	UPROPERTY(Transient) TArray<TObjectPtr<AActor>> MistActors;
	/** mistward: its traps, prisoners and pad (after the furniture, from streams of their own) */
	void PlaceTraps();
	void PlaceCellOccupants();
	void PlacePad();
	void BuildTrapVisual(int32 Index);
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
		/** improvements7: a part that slides up instead of turning (the town gate's portcullis): LiftZ cm at open, from where
		 *  its pivot was closed */
		bool bLift = false;
		float LiftZ = 0.f;
		FVector ClosedLoc = FVector::ZeroVector;
		/** improvements7: a lever's mover: pulling it moves this other door (the portcullis) the same way */
		int32 Link = -1;
		/** the list of 2026-11-22's phase 21: what she is told it is ("fridge"), where it is not its kind's word */
		FString Word;
	};
	struct FFlicker { UPointLightComponent* Light; float Base; float Phase; float Amount; };
	// ---- Brokenspire (RDTownPlan.cpp)
	void PlanTown(FRandomStream& R);
	/** the town's static part, a building / the outdoors at a time (static build): NextRoom counts buildings, NextCorr the
	 *  outdoor steps */
	void TownShellBuilding(int32 BI);
	/** the castle's outside (RDTownPlan.cpp): its towers' places, the void under them and the path to the stair turret (the
	 *  plan; no draws), an outer wall segment (Castle Forge's: slits, windows, the walk's strip, the battlements), the towers */
	void CastleTowersPlan();
	float CastleWalkTop() const;
	void CastleOuterFace(const FVector& Edge, const FVector& OutW, float Yaw, float T, float Z0, float Z1, const FIntPoint& Tl, int32 Side, bool bOverDoor);
	void CastleTowersBuild(const FTownBld& B);
	/** the castle's stair from its wing up to the wall walk, its stairwell's balustrade on the walk (the third list) */
	void CastleStairPlan();
	void CastleStairBuild();
	/** Vel Morrath's holy city (RDHoly.cpp, 2026-11-06): the cathedral's shell (its rooms' walls of their heights, the outer
	 *  stone and its tall windows, the vaults, the gabled roofs, the bell towers and their spires, the arch of the stair down);
	 *  a gabled roof of a style's pieces over a rectangle of tiles */
	void CathedralShell(int32 BI);
	void HolyGable(const FIntRect& Rc, float Top, const TCHAR* Style);
	/** Ashenreach's forge city (2026-11-07, RDForge.cpp): the besieged foundry's shell, and what stands on its square: the
	 *  guild's great anvil, an open forge (its fire, sparks, smoke and the work at it), an ore cart on its rails, a stretch of
	 *  the barricade before the foundry */
	/** Graymourne's port (2026-11-07, RDPort.cpp): its inner harbour (local tiles; empty: none) and its piers, the harbour's
	 *  water and the blockers along the quay and the piers, the things on the harbour's spots, the sewer gate in the sluice house */
	FIntRect TownHarbour;
	TArray<FIntRect> TownPiers;
	void HarbourBuild();
	void PortSpotBuild(const FTownSpot& Sp);
	void SewerGateBuild(int32 BI);
	bool InHarbourWater(const FIntPoint& T) const;
	/** the list of 2026-11-11: whether the harbour is open to the sea (the generator's bPortWaterOpen) and a world point is within
	 *  Reach cm of its rectangle (no town wall or tower stands there) */
	bool NearOpenHarbour(const FVector& W, float Reach) const;
	/** the harbour's walked floor under its water (cm, the section's): 1.7 m under the quay, 2.5 m with the harbour open to the
	 *  sea, where she swims (the user's of 2026-11-12: 140 cm of water, deeper than her swimming's 120) */
	float HarbourFloorZ() const;
	/** tests: the ramps up out of the harbour (world: foot in the water, top on the quay) */
	TArray<FVector> TownRampFeet, TownRampTops;
	void FoundryShell(int32 BI);
	/** Kethrys Spire's mage city (the list of 2026-11-08b, RDMage.cpp): the black tower (its gatehouse and hall, the round tower
	 *  over the hall, its cap, the sealed gate), a rune circle or a crystal pylon outdoors, a laboratory's cauldrons and tables */
	void SpireShell(int32 BI);
	void MageSpotBuild(const FTownSpot& Sp);
	void MageLabBuild(int32 BI);
	/** Heaven's modern city (the list of 2026-11-08b, RDHeaven.cpp): the research facility, a flat roof (a tower's floors over
	 *  its lobby), the streets' asphalt and paving, a street light or a street's furniture, the shield and the traffic */
	void ResearchShell(int32 BI);
	void ModernRoof(int32 BI, float Top);
	void HeavenStreets();
	void HeavenSpotBuild(const FTownSpot& Sp);
	void HeavenWorks();
	void TickHeavenCars(float Dt, const FVector& Her);
	void ForgeAnvilBuild(const FTownSpot& Sp);
	void OpenForgeBuild(const FTownSpot& Sp, bool bWork = true);
	void OreCartBuild(const FTownSpot& Sp);
	void BarricadeBuild(const FTownSpot& Sp);
	void TownOutdoors(FRandomStream& R, int32 Step);
	/** the town's life (the third list): gardens, pens, cooking fires with a pot or a spit, by the homes; the places of work */
	void TownLife(FRandomStream& R);
	/** the short grass and the small bushes on the free ground */
	void TownGrass(FRandomStream& R);
	static constexpr int32 TownOutdoorSteps = 8;
	void TownFurnish(FRandomStream& R, int32 BI);
	void TownDoors();
	void TownGround();
	/** the list of 2026-11-04 (RDTown7.cpp): the ground's lift field from what stands where (after the town's life, before the
	 *  trees and the grass, which then stand on it) */
	void TownLiftPlan();
	/** the gate's portcullis as a door that lifts, a lever each side of it (interactive build) */
	void TownGateWorks();
	/** food set out on a table's top at Top (bread, cheese, apples: the kit's), taken with F */
	void TownFoodOn(FRandomStream& R, const FVector& Top, float Yaw);
	/** a swinging gate in a pen's fence: a fence segment hinged at its end (interactive build) */
	void TownPenGate(const FVector& HingeW, float Yaw, float Len);
	/** a single door leaf on a building's doorway (the kit's door piece, its hinge) */
	void AddTownDoor(int32 BI, FIntPoint RoomTile, FIntPoint OutTile, FName Piece, int32 Room);
	/** the pieces of a building's style ("Town.<Style>_<Part>") */
	FName TownPiece(const FTownBld& B, const TCHAR* Part) const;
	/** House Forge's kit at a building's frame: a point in it (x along its door's outward way, y across), its yaw */
	FVector TownBldPoint(const FTownBld& B, float X, float Y, float Z) const;
	float TownBldYaw(const FTownBld& B) const;
	/** boarded houses' planks (their components, hidden when pried loose) */
	TMap<int32, TArray<TWeakObjectPtr<UStaticMeshComponent>>> TownBoards;
	/** pieces drawn in a material of their own (the burned houses): one instanced component per piece name */
	TMap<FName, UInstancedStaticMeshComponent*> HismsMat;
	TMap<FName, TArray<FTransform>> PendingMat;

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
	// ---- the caves (RDCave16.cpp): the set laid by the cave planner instead of Plan's rooms and hallways
	/** a kit room laid in the set: its kit entry, the tile its mesh's pivot stands on, its quarter turns, its pivot's height over
	 *  the set's floor, which of its openings a tunnel took */
	struct FCavePlace16 { int32 Kit = -1; FIntPoint At = FIntPoint::ZeroValue; int32 Turn = 0; float Z = 0.f; TArray<bool> Used; TArray<FVector> JAt; TArray<FVector2D> JOut; };
	/** a tunnel: its kit entry, its spline's points on the floor (the set's frame, cm), the places it joins (room index, or -1 - the
	 *  portal's index) */
	struct FCaveRun16 { int32 Kit = 0; TArray<FVector> Points; int32 From = -1, To = -1; float Length = 0.f; int32 Room = -1; };
	TArray<FCavePlace16> CavePlaced16;          // (in step with Rooms: a tunnel's entry has no kit, Kit -1)
	TArray<FCaveRun16> CaveRuns16;              // (each run's Room: its Rooms entry, its tiles' owner)
	TArray<FTransform> CaveCaps16;
	TArray<float> CaveZ16;
	void PlanCave16(FRandomStream& R);
	/** one try of the plan: the rooms cut off (no tunnel reached them) */
	int32 PlanCaveOnce16(FRandomStream& R, int32 Try);
	/** a try laid from its own stream (CaveBase16 + 7919 * Try): its score (-1000 a room cut off, +10 a portal) */
	int32 CaveTryOnce16(int32 Try);
	/** the plan's next step (a try, or the best laid again at the end): false when the plan is done */
	bool CaveStep16();
	int32 CaveBase16 = 0, CaveTry16 = 0, CaveBestTry16 = 0, CaveBestScore16 = 0, CaveLastTry16 = -1;
	/** in play: the plan's tries a frame each (ContinueGenerate), not all in BeginGenerate */
	bool bCaveSpread16 = false;
	/** the kit's meshes for the set laid (in play: a set saved in the level keeps none, its shell is never saved) */
	void CaveShell16();
	/** the tunnels' pieces from where the last call stopped, within Budget seconds: true when all are laid */
	bool CaveShellPieces16(double Budget);
	int32 CaveShellRun16 = 0, CaveShellPiece16 = 0;
	/** a set made in play: CaveShell16 lays the rooms and caps, ContinueGenerate the tunnels' pieces a budget a frame */
	bool bShellSpread16 = false;
	/** a cave room's light (the dressing's torches, god rays and containers are phase 9's) */
	void CaveFurnish16(FRandomStream& R, int32 RI);
	/** the kit's cap across a portal's tunnel into a shut tier, and its blocker */
	void CaveSeal16(const FVector& Border, const FVector& Out, int32 Kind);
	UPROPERTY(Transient) TArray<TObjectPtr<USceneComponent>> CaveComps16;
	/** phase 9: the torches by the rooms' wall-light points and on the tunnels' walls, the god rays, then the kit's dressing scattered over
	 *  the set's floors and roofs (traced: after the tunnels' pieces) */
	void CaveDressSet16();
	void CaveDressBegin16();
	bool CaveDressStep16(double Budget);
	FRandomStream CaveDressR16;
	int32 CaveDressStage16 = 0, CaveDressI16 = 0, CaveDressJ16 = 0, CaveDressTorches16 = 0;
	TMap<TObjectPtr<UStaticMesh>, TObjectPtr<UInstancedStaticMeshComponent>> CaveDressIsm16;
	TMap<FString, int32> CaveDressLaid16;
	TArray<TArray<FIntPoint>> CaveRoomTiles16;
	/** phase 10: the veins and growths of the set's kit rooms, after the dressing */
	void CaveNodesSet16();
public:
	TArray<FString> CaveNodeLines16;
	/** phase 12: the rubble across a side tunnel (its tiles blocked till it is broken) and the cache behind it; the lost blade */
	struct FCaveRubble16 { FVector At = FVector::ZeroVector; FVector Dir = FVector::ForwardVector; int32 Index = 0, Hits = 0; TArray<FIntPoint> Tiles; TArray<TObjectPtr<UPrimitiveComponent>> Comps; FVector Cache = FVector::ZeroVector; };
	TArray<FCaveRubble16> CaveRubble16;
	/** a side tunnel to nowhere's far end (its run's To) */
	static constexpr int32 CaveSpurTo16 = -1000;
	FString CaveLostLine16;
	void CaveRubbleSet16();
	/** phase 15: a cave painting on a set's wall (a decal), studied by F */
	struct FCavePainting16 { FVector At = FVector::ZeroVector, Normal = FVector::ForwardVector; };
	TArray<FCavePainting16> CavePaintings16;
	void CavePaintingSet16();
	/** phase 16: a lost traveller in the set's deepest room (a set beyond the first, by its seed's hash), freed by F */
	void CaveTravellerSet16();
	/** the list of 2026-11-22: a Heaven street lamp's light and glowing head */
	void HeavenLamp16(const FVector& At, float Yaw);
	// ---- the list of 2026-11-22's nineteenth phase: Heaven's streets (RDHeaven19.cpp)
	struct FSignal19 { FVector At = FVector::ZeroVector; float Offset = 0.f; int32 First = -1; uint8 Shown = 255; };
	/** a stretch of a street between its crossings: its road, along X or Y, its tiles along [S, E), across [C0, C1); its ends at a
	 *  crossing (and which, -1 a road beyond its end) */
	struct FRun19 { int32 Road = -1; bool bX = true; int32 S = 0, E = 0, C0 = 0, C1 = 0; bool bStartJ = false, bEndJ = false; int32 StartJ = -1, EndJ = -1; };
	struct FJunction19 { FIntPoint Min = FIntPoint::ZeroValue, Max = FIntPoint::ZeroValue; FVector Mid = FVector::ZeroVector; bool bPlaza = false; int32 Signal = -1; FString NameX, NameY; };
	struct FPark19 { int32 Run = -1; int32 Side = 1; int32 A = 0, B = 0; bool bLot = false; };
	/** a stop line: its lane's middle, the way its lane drives, the crossing's signal (-1: a stop sign or none), the road's axis */
	struct FStop19 { FVector At = FVector::ZeroVector; FVector Way = FVector::ZeroVector; int32 Signal = -1; bool bAlongX = true; };
	TArray<FSignal19> Signals19;
	TWeakObjectPtr<class UInstancedStaticMeshComponent> SignalLenses19;
	TArray<FRun19> Runs19;
	TArray<int32> JGroup19;
	TArray<FJunction19> Junctions19;
	TSet<int32> ParkTiles19;
	TArray<FPark19> Parks19;
	TArray<FStop19> StopLines19;
	TArray<FString> Streets19;
	/** Heaven's yard things by the homes (a trailer, a parked car, a dumpster, pallets, a bin): "yard|<x>|<y>|<yaw>|<length>|<width>" */
	TArray<FString> YardLines19;
	// ---- the list of 2026-11-22's twenty-first phase: Heaven's shops, services and containers (RDHeaven21.cpp)
	int32 ShopKind21(int32 BI) const;
	FString ShopWord21(int32 BI) const;
	float ShopSide21(int32 BI) const;
	FTransform ShopFurnish21(int32 BI);
	TArray<FString> Shops21;
	/** for the tests: "shop|<building>|<kind>|<gondolas>|<checkout x>|<y>|<rect x0>|<y0>|<x1>|<y1>|<clerk x>|<y>|<customer x>|<y>" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Heaven21") TArray<FString> GetShops21() const;
	/** a container's word for her: its Word, else its kind */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Heaven21") FString GetContainerWord(int32 I) const;
	/** for the tests: every container's kind, word, place, state and its moving part's turn from shut */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Heaven21") TArray<FString> GetContainerLines21() const;
	// ---- the list of 2026-11-22's twenty-second phase: Heaven's life (RDHeaven22.cpp)
	/** the pavements, made from the streets' runs once: 1 a pavement's tile beside a street (a walk's goal), 2 a zebra's tile across a
	 *  street, 3 other open ground walked between them (the square, a second row), 0 not walked (the asphalt, the lay-bys) */
	mutable TArray<uint8> Pave22;
	mutable TArray<FIntPoint> PaveTiles22;
	void MakePave22() const;
	uint8 PaveAt22(const FVector& W) const;
	/** a pedestrian's way between two points over the pavements and the zebras only (false: none within 200 tiles) */
	bool FindPavePath22(const FVector& From, const FVector& To, TArray<FVector>& Out) const;
	FVector PaveTileWorld22(int32 K) const { return PaveTiles22.IsValidIndex(K) ? TileWorld(PaveTiles22[K]) : FVector::ZeroVector; }
	/** the pedestrians on the street (a zebra, the asphalt): the cars wait for them as for her */
	TArray<FVector> CarYield22;
	/** a shop's, the market's, the hotel's, the clinic's or the gear shop's front: its neon over the door */
	void HeavenFront22(int32 BI, float Hx, float Hy, int32 DoorK, float Yaw0);
	/** a billboard on a roof by the street (by the building's seed) */
	void HeavenBillboard22(int32 BI, float Top, float Hx, float Hy, float Yaw0);
	TWeakObjectPtr<class UInstancedStaticMeshComponent> Neon22;
	/** for the tests: "front|<building>|<kind>|<tubes>|<r>|<g>|<b>|<x>|<y>|<z>", "board|<building>|<x>|<y>|<z>|<yaw>|<face>" */
	TArray<FString> Fronts22;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Heaven22") TArray<FString> GetFronts22() const { return Fronts22; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Heaven22") TArray<FString> GetPave22Lines() const;
	// ---- the list of 2026-11-22's twenty-third phase: Heaven's traffic (RDHeaven23.cpp)
	/** a lane: one way along a street's run between its crossings, on the right; from A (past the last crossing's zebra) to B (its
	 *  stop line, or a street's end); the crossing it ends at, its signal or stop sign, the lane the other way */
	struct FLane23 { int32 Run = -1; int32 Dir = 1; FVector A = FVector::ZeroVector, B = FVector::ZeroVector, Way = FVector::ZeroVector; float Len = 0.f;
		int32 FromJ = -1, ToJ = -1, Reverse = -1, Signal = -1; bool bStopSign = false, bAlongX = true; };
	TArray<FLane23> Lanes23;
	TMap<int32, TArray<int32>> LanesOut23;
	/** a free parking bay (a lay-by or a lot's bay with no parked car): its lane and place along it, where it is, its heading, its car */
	struct FBay23 { int32 Lane = -1; float S = 0.f; FVector At = FVector::ZeroVector; float Yaw = 0.f; int32 Car = -1; };
	TArray<FBay23> Bays23;
	struct FStop23 { int32 Lane = -1; float S = 0.f; FVector At = FVector::ZeroVector; float Yaw = 0.f; int32 Boarded = 0, Alighted = 0; };
	TArray<FStop23> BusStops23;
	TArray<TArray<int32>> BusRoutes23;
	/** a car: its pivot, body, driver and riders; its lane and place, speed; its state (0 along its lane, 1 across a crossing, 2 into
	 *  its bay, 3 parked, 4 out of it); the curve across; its goals (0 home, 1 work, 2 lunch, 3 errand, 4 a bus's stop) and route */
	struct FCar23
	{
		TWeakObjectPtr<USceneComponent> C; TWeakObjectPtr<UStaticMeshComponent> Body; TWeakObjectPtr<class USkeletalMeshComponent> Driver;
		TArray<TWeakObjectPtr<class USkeletalMeshComponent>> Riders;
		int32 Lane = -1, Next = -1, Goal = -1, GoalLane = -1, Bay = -1, Home = -1, Work = -1, Lunch = -1, Errand = -1, BusRoute = -1, BusNext = 0, Passengers = 0, DriverDef = -1;
		float S = 0.f, V = 0.f, VMax = 1000.f, Len = 450.f, Wid = 200.f, T = 0.f, CrossLen = 0.f, StopAt = -1.f, Until = 0.f, GoalS = 0.f, Yaw = 0.f;
		uint8 State = 0; bool bBus = false, bStoppedHere = false, bShown = true, bDriverShown = true, bCol = true; uint32 Seed = 0; float Rethink = 0.f;
		/** what held it last (0 nothing, 1 the car ahead, 2 her, 3 a pedestrian, 4 a red or amber light, 5 a stop sign, 6 a left turn's
		 *  yield, 7 its curve not clear, 8 a car coming into its lane, 9 its bay or stop) and since when it has stood */
		uint8 Why = 0; float StillSince = -1.f, Entered = 0.f; bool bCommitted = false;
		FVector P0 = FVector::ZeroVector, P1 = FVector::ZeroVector, P2 = FVector::ZeroVector, Pos = FVector::ZeroVector;
		TArray<int32> Route;
	};
	TArray<FCar23> Cars23;
	int32 RedRuns23 = 0, StopSignStops23 = 0, StopSignRolls23 = 0, Boarded23 = 0, Alighted23 = 0, Parks23 = 0, Arrivals23 = 0, BusStops23Made = 0;
	float MinGap23 = 1e9f, FarClock23 = 0.f;
	bool bTraffic23Due = false;
	FString MinGapWhat23;
	FVector LanePoint23(int32 L, float S) const;
	void BuildRoads23();
	TArray<int32> NextLanes23(int32 L) const;
	bool Route23(int32 From, int32 To, TArray<int32>& Out) const;
	int32 AddressLane23(int32 Bld, float& OutS) const;
	int32 GoalOf23(const FCar23& Cr, float Hour) const;
	int32 GoalBuilding23(const FCar23& Cr, int32 Goal) const;
	void SetGoal23(int32 Ci, float Hour);
	class USkeletalMeshComponent* SeatPerson23(USceneComponent* Pv, int32 Def, const FVector& At, FName Clip, bool bDriver);
	void HeavenTraffic23();
	void PlaceCar23(FCar23& Cr);
	void TickTraffic23(float Dt, const FVector& Her);
	void BusArrive23(int32 Ci);
	bool CurveClear23(int32 I, const FVector& P0, const FVector& P1, const FVector& P2, float T0, float T1, float Margin, bool bStillTight = false) const;
	void CurveOf23(int32 L, int32 Nx, FVector& P0, FVector& P1, FVector& P2) const;
	/** for the tests: "traffic|<lanes>|<bays>|<stops>|<cars>|<buses>|<drivers>|<red runs>|<stop sign stops>|<rolled stops>|<boarded>|
	 *  <alighted>|<parked>|<arrived>|<least gap cm>|<bus loops>", "car|...", "lane|...", "busstop|..." */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Heaven23") TArray<FString> GetTraffic23Lines() const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Heaven23") void ResetTrafficCounts23() { RedRuns23 = StopSignStops23 = StopSignRolls23 = Boarded23 = Alighted23 = Parks23 = Arrivals23 = 0; MinGap23 = 1e9f; MinGapWhat23.Reset(); }
	// ---- the list of 2026-11-22's twentieth phase: Heaven's storeys (RDHeaven20.cpp)
	/** a building's stair and lift core: three strips of four tiles from its back wall (X0, its local X), from a back corner (Y0) along Sgn */
	struct FCore20 { int32 Bld = -1; int32 N = 0; float Sgn = 1.f; float X0 = 0.f, Y0 = 0.f; };
	/** a lift: its shaft's middle (z 0), the way out of its door, each floor's height (the roof's last), where it stands and goes */
	struct FLift20 { int32 Bld = -1; FVector Shaft = FVector::ZeroVector, Entry = FVector::ZeroVector; TArray<float> Floors; int32 At = 0, Target = 0; float Z = 0.f; bool bMoving = false;
		TWeakObjectPtr<class UStaticMeshComponent> Platform; TArray<TWeakObjectPtr<class UPrimitiveComponent>> Gates; };
	TMap<int32, FCore20> Cores20;
	TArray<FLift20> Lifts20;
	TArray<FString> Storeys20;
	bool HeavenCorePlan20(int32 BI);
	FVector CorePoint20(const FCore20& C, float Strip, float Tile, float Z) const;
	bool CoreOpenAt20(int32 BI, int32 Storey, const FVector& W) const;
	void HeavenStoreys20(int32 BI);
	void AddCoreFeet20(int32 RI);
	void FurnishStoreys20(int32 BI);
	void UpdateLiftGates20(FLift20& L);
	void TickLifts20(float Dt);
	int32 LiftNear20(const FVector& From, int32& OutFloor, bool& bOnIt) const;
	FString LiftFloorName20(const FLift20& L, int32 K) const;
	float LiftDist20(const FVector& From) const;
	FString LiftDescribe20(const FVector& From, float NearerThan = 1e9f) const;
	FString LiftUse20(const FVector& From, float NearerThan = 1e9f);
	TSet<FIntPoint> CoreTiles20;
	/** a point over a stair and lift core's tiles (a lamp, a hung piece or a kitchen's fire kept out of it) */
	bool InCore20(const FVector& P) const;
	/** for the tests: "core|<building>|<kind>|<storeys>|<x>|<y>|<slabs>|<flights>|<rails>", "route|<building>|<x>|<y>|<z>" (the way up),
	 *  "furnished|<building>|<pieces>", "lift|...", "liftfloor|<i>|<k>|<z>" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Heaven20") TArray<FString> GetStoreys20() const;
	void HeavenSignal19(const FTownSpot& Sp);
	void TickSignals19(float Now);
	void HeavenRuns19();
	bool ParkFree19(const FIntPoint& T) const;
	void HeavenStreets19Plan();
	void HeavenStreets19Build();
	void AddText19(const FString& Text, const FTransform& T, float MaxW, float MaxH, const FColor& Col);
	FString StreetName19(int32 Road) const;
	/** for the tests: "signals|<n>|<time>", "sig|<i>|<x>|<y>|<x phase>|<y phase>|<lenses lit>|<which>" (phase 2 green, 1 amber, 0 red) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Heaven19") TArray<FString> GetSignals19() const;
	/** for the tests: "streets|<runs>|<dashes>|<edges>|<zebra bars>|<stop lines>|<stop signs>|<name signs>|<districts>|<crossings>|
	 *  <signalled>|<parked>|<bays>|<lots>|<signals>", "road|...", "junction|...", "stopline|...", "stopsign|...", "namesign|...",
	 *  "district|...", "car|<x>|<y>|<yaw>|<lot>" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Heaven19") TArray<FString> GetHeavenStreets19() const;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") float HeavenResearchTopZ16 = 0.f;
	/** the kit's room with the lowest floor at least 15 m from Away: its walkable tile nearest its middle, on the floor */
	bool CaveDeepSpot16(const FVector& Away, FVector& Out) const;
	TWeakObjectPtr<class ARDPrisoner> CaveTraveller16;
	FString CaveTravellerName16;
	/** phase 13: a flooded side tunnel (its stretch under water, the water's face) */
	struct FCaveFlood16 { TArray<FVector> Pts; float Half = 300.f, WaterZ = 0.f; TArray<TObjectPtr<UPrimitiveComponent>> Comps; };
	TArray<FCaveFlood16> CaveFloods16;
	bool CaveFloodSet16(const FCaveRun16& Run, float Half, float F0, float F1);
	void CaveLostBlade16();
	/** broken: its pieces gone, its tiles open */
	void ClearRubble16(int32 K);
private:
	void CaveTorch16(const FTransform& At);
	TArray<FString> CaveDressLines16;
	int32 CaveContainers16 = 0;
public:
	TArray<FString> CaveDressing16() const;
	float CaveRoomFloor16(int32 RI) const { return CavePlaced16.IsValidIndex(RI) && CavePlaced16[RI].Kit >= 0 ? CavePlaced16[RI].Z : 0.f; }
private:
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
	/** false: not placed (no such piece; mistward: it would overlap other furniture or stand where a container is opened) */
	bool AddPiece(FName Name, const FTransform& T, bool bForceNoCollision = false);
	bool AddPieceAt(FName Name, const FVector& Loc, float Yaw, float Scale = 1.f, bool bForceNoCollision = false);
	UPointLightComponent* AddLight(const FVector& Loc, const FLinearColor& Color, float Candelas, float Radius, bool bShadows, float Flicker);
	void AddEffect(FName Name, const FVector& Loc, float Scale = 1.f);
	void AddTorch(const FVector& WallPoint, float InYaw, float Candelas, bool bLit = true);
	void AddDoor(FIntPoint RoomTile, FIntPoint OutTile, int32 RoomIndex);
	void AddCellDoor(const FVector& HingeWorld, float Yaw, float Width);
	bool AddContainer(FName Name, const FVector& Loc, float Yaw, const FString& Kind);
	void MarkBlocked(const FVector& Loc, float Yaw, const FVector2D& Size, bool bLaneToo = false);
	USceneComponent* AddPivot(USceneComponent* Parent, const FTransform& Rel);
	UStaticMeshComponent* AddMesh(USceneComponent* Parent, UStaticMesh* Mesh, const FTransform& Rel, bool bCollision);

	// furnishing helpers: room-local geometry
	FBox2D RoomBox(const FRoom& Rm, float Inset = 0.f) const;
	/** points along the inside of a wall (side 0..3), every Spacing, keeping Clear cm from the lane door lines */
	TArray<FVector> WallSlots(const FRoom& Rm, int32 Side, float Spacing, float Clear, float Margin) const;
	static float InwardYaw(int32 Side);
	bool LaneFree(const FRoom& Rm, const FVector& P, float Radius) const;
	void FurnishWalls(FRandomStream& R, const FRoom& Rm, const TArray<FName>& Names, float Spacing, float Chance, bool bContainers = false, TArray<FPlacedPiece>* Placed = nullptr);
	void LightRoom(FRandomStream& R, const FRoom& Rm, int32 RoomIndex);
};
