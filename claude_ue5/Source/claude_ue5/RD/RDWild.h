// The wilderness around Brokenspire (the user's spec of 2026-11-03, docs/wilderness.txt): a continent of 300 x 300 km
// generated from one seed as she comes to it. FRDWildWorld is the world's model: pure functions of the seed (the
// continent's coast, the biome regions and their blending, the heights, the ground's colours, rivers, lakes, ponds,
// marsh pools, roads, towns and places), safe to call from worker threads once Init has run. The chunks (ARDWildChunk,
// RDWildChunk.cpp) and the map's tiles (RDWildMap.cpp) are made from it; nothing of the terrain is stored but what she
// has revealed and found (the save game, RDSave.cpp).
//
// Frames: the world is in metres (double) in the game's axes, X north and Y east, Brokenspire's middle at (0, 0). A
// height h is metres above the sea; the game's Z is (h - BaseH) * 100 cm, so that Brokenspire's ground is at z 0.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RD/RDTypes.h"
#include "RDWild.generated.h"

class UStaticMesh;
class UMaterialInterface;
class UNiagaraSystem;
class UProceduralMeshComponent;
class UHierarchicalInstancedStaticMeshComponent;
class ARDDungeonGenerator;
class ARDMonster;

/** a kind of plant, rock or prop a biome scatters */
USTRUCT(BlueprintType)
struct FRDWildFoliage
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UStaticMesh> Mesh = nullptr;
	/** "tree", "bush", "grass", "flower", "reed", "rock", "ice", "crop", "log" (the map draws trees and rocks) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Kind;
	/** how many a hectare where the biome is whole */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Density = 10.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float ScaleMin = 0.8f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float ScaleMax = 1.2f;
	/** the steepest ground it grows on, degrees */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float SlopeMax = 30.f;
	/** sunk into the ground, cm (a rock's foot, a trunk's flare) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Sink = 5.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float CullDistance = 60000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bCollision = false;
	/** leans with the slope (rocks, grass) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bAlign = false;
	/** only in the chunks round her (grass, flowers: dense and short-sighted) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bNearOnly = false;
	/** clumped: grows in patches (a noise mask) rather than evenly */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Clump = 0.f;
	/** grows only near water (reeds, lily pads: < 0 on the water itself) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float NearWater = 0.f;
	/** the list of 2026-11-04: its materials instead of its mesh's (by slot; the grass's and bushes' that sway in the wind) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<TObjectPtr<UMaterialInterface>> Materials;
	/** the list of 2026-11-07: a field crop (its biome's Crops index): planted in its field's rows, StepM apart along them
	 *  (Density then weighs it against the crop's other kinds); -1 scattered as before */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 Crop = -1;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float StepM = 0.8f;
};

/** the list of 2026-11-07 ("the farm terrain should have regular lines of crops, like corn, cabbages, potatoes, pumpkins"): a
 *  field's crop, its rows RowM apart; seen from afar its ground is Soil with Leaf over Cover of it, and the ground material
 *  draws its rows (ToRows: the field's way and crop in the ground mesh's UV0, its weight in UV3's V) */
USTRUCT(BlueprintType)
struct FRDWildCrop
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Name;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FLinearColor Soil = FLinearColor(0.20f, 0.14f, 0.08f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FLinearColor Leaf = FLinearColor(0.16f, 0.27f, 0.07f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Cover = 0.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float RowM = 1.f;
	/** how often a field grows it, against the others' (the list of 2026-11-08b: the commonest medieval crops first) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Weight = 1.f;
};

/** one of the user's terrain templates (docs/wilderness.txt), as data: 887 writes the table from biomes.json */
USTRUCT(BlueprintType)
struct FRDWildBiome
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Name;
	/** the shape of its ground (ERDWShape) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 Shape = 0;
	/** its ground's height above the sea and how much it varies, metres */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Base = 60.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Amp = 20.f;
	/** its ground seen from above: two colours mixed by a noise, the rock of its slopes */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FLinearColor ColorA = FLinearColor(0.25f, 0.33f, 0.12f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FLinearColor ColorB = FLinearColor(0.32f, 0.36f, 0.16f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FLinearColor Rock = FLinearColor(0.32f, 0.31f, 0.29f);
	/** snow on it whatever its height (0 none, 1 all of it) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Snow = 0.f;
	/** its forest's canopy (0 open, 1 closed): how dark and grainy the map draws it, how many trees */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Canopy = 0.f;
	/** ponds a 4 km cell (and marsh pools for the marsh shapes) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Ponds = 0.f;
	/** steam vents a 4 km cell (the caldera's hot springs) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Steam = 0.f;
	/** the ground's layers for the terrain material (0-1 each): rock, snow, sand, mud; the rest is grass or soil */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FVector4 Layers = FVector4(0, 0, 0, 0);
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FRDWildFoliage> Foliage;
	/** its fields' crops (the farms'; none elsewhere) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FRDWildCrop> Crops;
};

/** a town of the continent (Brokenspire and the three the spec places) */
USTRUCT(BlueprintType)
struct FRDWildTown
{
	GENERATED_BODY()
	UPROPERTY(BlueprintReadOnly) FString Name;
	/** world metres */
	UPROPERTY(BlueprintReadOnly) FVector2D Site = FVector2D::ZeroVector;
	/** its ground above the sea, metres */
	UPROPERTY(BlueprintReadOnly) float H = 0.f;
	UPROPERTY(BlueprintReadOnly) int32 Seed = 0;
	/** 0 Brokenspire (the castle, the quests), 1 a small town */
	UPROPERTY(BlueprintReadOnly) int32 Style = 1;
	/** the place's symbol: "town" or "city" */
	UPROPERTY(BlueprintReadOnly) FString Kind = TEXT("town");
	/** its size in tiles (0: the generator's small town, WildSmallTownTiles) */
	UPROPERTY(BlueprintReadOnly) int32 Tiles = 0;
	/** its plan (the generator's TownPlan): 0 Brokenspire's (the gate, the square, a castle at the far wall), 1 a holy city
	 *  (Vel Morrath, the user's of 2026-11-06: the cathedral at its middle over the catacombs) */
	UPROPERTY(BlueprintReadOnly) int32 Plan = 0;
	/** the region it stands at the edge of, when the spec names one (Ashenreach's "burned plain", 2026-11-07): that biome over
	 *  its cell, the region's middle 5 km north of the town, and over the cell north of it; empty: the region by its kind */
	UPROPERTY(BlueprintReadOnly) FString Biome;
};

/** a point of interest: its kind, place, name; its id is its cell's and kind's */
USTRUCT(BlueprintType)
struct FRDWildPlace
{
	GENERATED_BODY()
	UPROPERTY(BlueprintReadOnly) int32 Id = 0;
	/** village, camp, house, spawn, ruins, ritual, cave, lair, town, city */
	UPROPERTY(BlueprintReadOnly) FString Kind;
	UPROPERTY(BlueprintReadOnly) FString Name;
	UPROPERTY(BlueprintReadOnly) FVector2D At = FVector2D::ZeroVector;
	UPROPERTY(BlueprintReadOnly) float H = 0.f;
	UPROPERTY(BlueprintReadOnly) int32 Tier = 1;
	UPROPERTY(BlueprintReadOnly) int32 Biome = 0;
	/** a town's index into the world's towns, else -1 */
	UPROPERTY(BlueprintReadOnly) int32 Town = -1;
	/** its yaw (degrees): the props face the way to her approach */
	UPROPERTY(BlueprintReadOnly) float Yaw = 0.f;
	/** a quest's place (the captain's of Brokenspire, 2026-11-07): "wolves" (the den on the mill road), "patrol" (the old
	 *  watchtower); empty for the others */
	UPROPERTY(BlueprintReadOnly) FString Quest;
	/** the seventh phase: a small point of interest's kind (its index into PoiKinds; -1: a place) */
	UPROPERTY(BlueprintReadOnly) int32 Poi = -1;
};

/** the shapes of ground a biome can have */
namespace ERDWShape
{
	enum Type : int32 { Plains = 0, Rolling, Hills, Moor, Mountains, Peaks, Glacial, Mesa, Canyon, CanyonNet, Volcano, Caldera, LavaField, Marsh, Coastal, RockyCoast, Steppe, Dunes, Count };
}

/** everything the world knows of one point */
struct FRDWSample
{
	float H = 0.f;              // metres above the sea, the ground's surface
	float Water = -1e9f;        // the water's surface there (metres) when it is under water, else -1e9
	int32 WaterKind = 0;        // 0 none, 1 sea, 2 lake, 3 river, 4 pond, 5 marsh pool, 6 hot spring
	FLinearColor Color;         // the ground seen from above (linear)
	FLinearColor RockColor;     // its regions' rock (the steep slopes)
	float Rock = 0.f, Snow = 0.f, Sand = 0.f, Mud = 0.f, Road = 0.f, Field = 0.f, Lava = 0.f;
	float Canopy = 0.f;         // the forest's closeness there (0-1)
	int32 Biome = 0;            // the biome with the most weight
	int32 Biome2 = 0;           // the second (for the transitions)
	float W1 = 1.f;             // the first's weight (0.5-1)
	float SlopeHint = 0.f;      // set by callers that know the slope
	// (the list of 2026-11-07: the field it is in, when Field > 0: its cell, its crop (the farms biome's Crops), its rows' way)
	FIntPoint FieldCell = FIntPoint(MIN_int32, MIN_int32);
	int32 FieldCrop = -1;
	float FieldAng = 0.f;
	// (the list of 2026-11-08b's medieval farms: the great field's kind there (FRDWFarm::Kind; 4 a farmstead's yard), and an
	// open field's strips: their width across FieldAng's way and where they start (metres), 0 where it has none)
	uint8 FarmKind = 0;
	float StripW = 0.f, StripOff = 0.f;
};

/** the farms' layout at a point (the list of 2026-11-08b: "make the farms in the wilderness look more like medieval farms, with
 *  different sizes of farms, from the croft to the strip"): the farms are great fields (a warped Voronoi about 420 m across),
 *  each an open field of unfenced strips (one crop the whole field, its furlongs each their own way, the strips divided by
 *  furrows and ploughed into ridges), a farmstead's crofts (small plots round its yard, each its own crop or grass) or
 *  pasture (grass over old ridges) */
struct FRDWFarm
{
	/** 0 none, 1 open field, 2 crofts, 3 pasture, 4 a farmstead's yard */
	uint8 Kind = 0;
	FIntPoint Great = FIntPoint::ZeroValue;   // the great field's cell
	FIntPoint Plot = FIntPoint::ZeroValue;    // the furlong's (open field) or the plot's (crofts)
	FVector2D Site = FVector2D::ZeroVector;   // the great field's point (a croft field's farmstead stands there)
	int32 Crop = -1;                          // -1 grass
	float Field = 0.f;                        // how much the crop's ground it is (0-1: the edges, the headlands and furrows less)
	float Fade = 0.f;                         // the great field's own fade (the farms' edge, its own edge)
	float Ang = 0.f;                          // its rows' and strips' way (radians, 0-PI)
	float StripW = 0.f, StripOff = 0.f;       // the strips' width and start (metres, along the way across)
	int32 Strip = 0;                          // which strip
	float Furrow = 0.f;                       // 1 in the furrow between two strips
	float Ridge = 0.f;                        // metres over the ground (ridge-and-furrow)
	float Shade = 1.f;                        // the strip's own shade (each strip ploughed and sown by another hand)
};

/** the world's model (see the file's head) */
class CLAUDE_UE5_API FRDWildWorld
{
public:
	// ---- the continent's frame (metres)
	double Xs = -80000.0, Xn = 220000.0, Yw = -150000.0, Ye = 150000.0;
	double CellM = 14000.0;      // a biome region's cell
	float SeaDepth = 60.f;

	uint32 Seed = 1;
	bool bReady = false;
	TArray<FRDWildBiome> Biomes;     // the table (names, shapes, colours; meshes are read on the game thread only)
	TMap<FString, int32> BiomeIndex;
	int32 FarmsBiome = -1;           // the farms' (its fields' crops), -1 none
	TArray<float> CropCum;           // the farms' crops' weights as running sums (Init)
	/** the most crops the ground's rows can tell apart: the chunk packs a field's crop in UV0's v as (crop + 0.5) / MaxCrops and
	 *  887's ground material reads floor(v x MaxCrops) (887 and Init check the farms' table against it) */
	static constexpr int32 MaxCrops = 16;
	/** a sample's field's crop's name ("" outside a field, or at a field's edge under MinField of its weight) */
	FString CropName(const FRDWSample& S, float MinField = 0.f) const;
	/** the farms' layout at a point given the farms' weight there (FRDWFarm) */
	void FarmAt(double X, double Y, float FarmW, FRDWFarm& Out) const;
	/** the farms biome's weight at a point (Blend's) */
	float FarmWeight(double X, double Y) const;
	/** a crop drawn by the crops' weights from a hash (-1 with none) */
	int32 PickCrop(int32 A, int32 B, uint32 S) const;
	/** the farmsteads whose middle is in a box (world metres): one at each croft field's point that is dry, off the roads and
	 *  level; places of kind "farmstead", ids FarmIdBase + (great cell x & 1023) << 10 | (y & 1023) (none on the map) */
	void FarmsteadsIn(double X0, double Y0, double X1, double Y1, TArray<FRDWildPlace>& Out) const;
	static constexpr double GreatFieldM = 420.0;
	static constexpr int32 FarmIdBase = 1 << 28;
	TArray<FRDWildTown> Towns;
	float BaseH = 0.f;               // Brokenspire's ground (the game's z 0)
	/** where a town's roads leave it (world metres, just outside its section), when its gate is known before Init */
	TMap<int32, FVector2D> GateOut;

	// ---- made by Init
	int32 CellsX = 0, CellsY = 0;
	TArray<int32> CellBiome;         // per cell
	TArray<FVector2D> CellSite;      // per cell, world metres
	struct FRiver { TArray<FVector2D> P; TArray<float> S; TArray<float> W; FBox2D Box; };   // points, water surface, width
	TArray<FRiver> Rivers;
	struct FLake { FVector2D C; float R = 300.f; float Level = 0.f; float Depth = 6.f; int32 Kind = 2; uint32 Shape = 0; };
	TArray<FLake> Lakes;             // lakes made at Init (ponds are found per cell, by Ponds())
	struct FRoad { TArray<FVector2D> P; TArray<float> Z; FBox2D Box; int32 From = -1, To = -1; };
	TArray<FRoad> Roads;
	/** a spatial hash of river and road segments: (2 km cell) -> (kind << 30 | index << 16 | segment) */
	TMultiMap<FIntPoint, uint32> SegHash;
	TMultiMap<FIntPoint, int32> LakeHash;
	TArray<FLake> Ponds;             // every 4 km cell's ponds and hot springs (Init)
	TMultiMap<FIntPoint, int32> PondHash;
	double HashM = 2000.0;
	double InitSeconds = 0.0;

	void Init(uint32 InSeed, const TArray<FRDWildBiome>& InBiomes);

	// ---- queries (any thread once bReady)
	/** the land's measure: > 0 land, < 0 sea; about 0.06 a 9 km */
	float Continent(double X, double Y) const;
	void Climate(double X, double Y, float& T, float& M) const;
	/** the biome regions' weights at a point: up to 4 (index, weight, its cell's site) */
	int32 Blend(double X, double Y, int32* Idx, float* W, FVector2D* Site) const;
	/** the ground before rivers, lakes, ponds, roads and towns */
	float BaseHeight(double X, double Y) const;
	/** the ground as she walks it (metres above the sea) */
	float Height(double X, double Y) const;
	/** the same ground with no farm on it (no ridge-and-furrow: tests) */
	float BareHeight(double X, double Y) const;
	/** everything at a point (the chunk's vertices, the map's pixels); bDetail: the fine noise too */
	void Sample(double X, double Y, FRDWSample& Out, bool bDetail = true, float PixelM = 0.f) const;
	/** the game's z (cm) of a height in metres, and back */
	float ToZ(float H) const { return (H - BaseH) * 100.f; }
	float FromZ(float Z) const { return Z / 100.f + BaseH; }
	FString BiomeName(int32 B) const { return Biomes.IsValidIndex(B) ? Biomes[B].Name : FString(); }
	int32 BiomeAt(double X, double Y) const;
	/** the places of interest in a 4 km cell (deterministic); towns are places too */
	void PlacesIn(FIntPoint Cell, TArray<FRDWildPlace>& Out) const;
	static constexpr double PlaceCellM = 4000.0;
	FIntPoint PlaceCellOf(double X, double Y) const { return FIntPoint(FMath::FloorToInt((X - Xs) / PlaceCellM), FMath::FloorToInt((Y - Yw) / PlaceCellM)); }
	bool FindPlace(int32 Id, FRDWildPlace& Out) const;
	/** the ponds (and hot springs) of a 4 km cell */
	void PondsIn(FIntPoint Cell, TArray<FLake>& Out) const;
	/** the nearest town and its distance (metres) */
	int32 NearestTown(double X, double Y, double& Dist) const;
	/** the place's tier (the monsters' strength): along the chain of towns (TierChain), from the tier of the town a leg leaves to
	 *  the next one's, on the leg nearest the point (the list of 2026-11-08b: Brokenspire 1, Vel Morrath 5, Ashenreach 10,
	 *  Graymourne 15, Kethrys Spire 20, Heaven 25; towns not in this world are left out of the chain) */
	int32 TierAt(double X, double Y) const;
	/** the chain's towns this world has (their sites) and their tiers, in order (Init) */
	TArray<FVector2D> TierSites;
	TArray<float> TierValues;
	void MakeTierChain();
	/** a name for a place */
	FString NameFor(const FString& Kind, uint32 H) const;
	/** a town's place id is TownIdBase + its index: far above any other place's ((cell x << 14) | (cell y << 4) | k, under
	 *  2^24; the 1000000 it was first collided with the places of the northern cells, x 62 and on) */
	static constexpr int32 TownIdBase = 1 << 30;
	/** the quests' places (Brokenspire's captain: the wolves' den, the old watchtower): QuestIdBase + their index, between
	 *  the places' ids (under 2^24) and the towns' */
	static constexpr int32 QuestIdBase = 1 << 29;
	/** the seventh phase's small points of interest (PoisIn): a 120 m grid, one in most of its cells, of the kinds of the
	 *  region (PoiKinds, set after Init from the generator's WildPoiKinds); their ids PoiIdBase + (cell x << 11 | cell y), in the
	 *  free range under the farms' 2^28 */
	static constexpr int32 PoiIdBase = 1 << 24;
	static constexpr double PoiCellM = 120.0;
	TArray<FRDWildPoiKind> PoiKinds;
	float PoiFill = 0.8f;
	FIntPoint PoiCellOf(double X, double Y) const { return FIntPoint(FMath::FloorToInt((X - Xs) / PoiCellM), FMath::FloorToInt((Y - Yw) / PoiCellM)); }
	void PoisIn(FIntPoint Cell, TArray<FRDWildPlace>& Out) const;
	TArray<FRDWildPlace> QuestPlaces;
	/** a quest goal's place ("wild:wolves" -> the den), or null */
	const FRDWildPlace* QuestPlaceFor(const FString& Goal) const;

	// ---- the noise (public for the map and the chunks)
	static float Perlin(double X, double Y, uint32 S);
	static float Fbm(double X, double Y, double Freq, int32 Oct, uint32 S, float Gain = 0.5f);
	static float Ridged(double X, double Y, double Freq, int32 Oct, uint32 S);
	static uint32 Hash(int32 X, int32 Y, uint32 S);
	static float Rand01(int32 X, int32 Y, uint32 S) { return (Hash(X, Y, S) & 0xFFFFFF) / 16777216.f; }

private:
	float ShapeHeight(int32 B, double X, double Y, const FVector2D& Site, bool bDetail) const;
	float LandRelief(double X, double Y, bool bDetail, const int32* Bi, const float* W, int32 N) const;
	float LandHeight(double X, double Y, bool bDetail, int32* OutB = nullptr, int32* OutB2 = nullptr, float* OutW = nullptr, float* OutC = nullptr, float* OutFarm = nullptr) const;
	void AssignBiomes();
	void PlaceTowns();
	void MakeRivers();
	void MakeLakes();
	void MakeRoads();
	void MakeQuestPlaces();
	void HashSegments();
	float Feature(double X, double Y, float H, FRDWSample* S) const;   // rivers, lakes, ponds, roads, towns on H
	int32 Biome(const TCHAR* Name) const { const int32* I = BiomeIndex.Find(Name); return I ? *I : 0; }
};

/** a wild animal (the user's list of 2026-11-04; RDWildLife.cpp): the generator's WildFauna kind on its clips, no controller.
 *  It stands, grazes and walks about where it was put; when she comes within its own flee distance (1-3 m) it runs off
 *  away from her for a while, then calms and grazes again. It keeps to the ground (the world's height) and to dry land. */
UCLASS()
class CLAUDE_UE5_API ARDWildAnimal : public AActor
{
	GENERATED_BODY()
public:
	ARDWildAnimal();
	void Init(ARDDungeonGenerator* InGenerator, int32 InDef, uint32 InSeed);
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Wild") int32 Def = -1;
	/** 0 standing, 1 grazing, 2 walking, 3 fleeing */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild") int32 GetState() const { return State; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild") float GetFleeDistance() const { return FleeR; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild") int32 GetTimesFled() const { return Fled; }
	FVector Home = FVector::ZeroVector;
	// ---- the list of 2026-11-07: "player should be able to kill the animals wandering in the wilderness and get appropriate
	// crafting materials from them": her blows and bolts hurt it (its kind's Health), struck it runs off; at 0 it falls on its
	// side where it stood and its things lie by it (its kind's Drops, taken with F as a harvest); the body goes after a while
	/** a blow or bolt of Dmg from From: true when it kills */
	bool TakeHit(float Dmg, const FVector& From);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild") bool IsDead() const { return bDead; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild") float GetHealth() const { return Health; }
	/** its body's middle (world) and how far round it a blow or a bolt meets it */
	FVector BodyCenter() const;
	float BodyRadius() const;
	float Health = 1.f, DeadAt = -1.f, FallYaw = 0.f;
	bool bDead = false;
protected:
	virtual void Tick(float Dt) override;
private:
	UPROPERTY() TObjectPtr<USceneComponent> Root;
	UPROPERTY() TObjectPtr<class USkeletalMeshComponent> Body;
	UPROPERTY(Transient) TObjectPtr<ARDDungeonGenerator> Gen;
	FRandomStream R;
	int32 State = 0, Fled = 0;
	float Until = 0.f, FleeR = 200.f;
	FVector To = FVector::ZeroVector;
	UAnimationAsset* CurAnim = nullptr;
	void SetState(int32 S, float Now, const FVector& Away = FVector::ZeroVector);
	void Play(UAnimationAsset* A, float Rate);
};

/** one chunk of the wilderness: its ground (a procedural mesh with collision), its water, its plants and rocks, its places'
 *  props. Made by ARDDungeonGenerator::TickWild from data a worker thread computed, destroyed when she is far. */
UCLASS()
class CLAUDE_UE5_API ARDWildChunk : public AActor
{
	GENERATED_BODY()
public:
	ARDWildChunk();
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UProceduralMeshComponent> Ground;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UProceduralMeshComponent> WaterMesh;
	/** the plants and rocks, one component per mesh */
	UPROPERTY() TArray<TObjectPtr<UHierarchicalInstancedStaticMeshComponent>> Foliage;
	/** those that are only round her (grass): made and dropped as she comes and goes */
	UPROPERTY() TArray<TObjectPtr<UHierarchicalInstancedStaticMeshComponent>> NearFoliage;
	/** the places' monsters (destroyed with it) */
	UPROPERTY() TArray<TObjectPtr<AActor>> Props;
	/** the places' props (its components) */
	UPROPERTY() TArray<TObjectPtr<class UStaticMeshComponent>> PlaceProps;
	UPROPERTY(BlueprintReadOnly) FIntPoint Coord = FIntPoint::ZeroValue;
	UPROPERTY(BlueprintReadOnly) int32 Instances = 0;
	/** of those, the trees (the test checks every biome whose table has trees has some) */
	UPROPERTY(BlueprintReadOnly) int32 Trees = 0;
	UPROPERTY(BlueprintReadOnly) int32 Triangles = 0;
	UPROPERTY(BlueprintReadOnly) bool bNear = false;
	UPROPERTY(BlueprintReadOnly) bool bCollisionOn = false;
	/** still being made over frames (the generator's WildBuilding): its near plants wait */
	UPROPERTY(BlueprintReadOnly) bool bMaking = false;
	/** the ground's collision (hidden, BlockAll); cooked on a worker unless she was running fast when it was asked */
	UPROPERTY() TObjectPtr<UProceduralMeshComponent> GroundCollision = nullptr;
	virtual void Destroyed() override;
};
