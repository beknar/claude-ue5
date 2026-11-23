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
	/** the list of 2026-11-11 ("meadows should have clusters of trees, strips of trees and clearings free of trees"): how much the
	 *  world's grove pattern (FRDWildWorld::Grove: clusters, strips, clearings) decides where it grows (0 everywhere alike, 1 only
	 *  in the groves) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Grove = 0.f;
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
	/** the list of 2026-11-14 ("rolling swales that hide what's over the next rise"; "gentle verticality: small rises and dips control
	 *  what the player can see"): low rises a few hundred metres apart over its shape, metres high (0 none) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Swale = 0.f;
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
	/** the list of 2026-11-16's twelfth phase: how far its region is eased to its ground (m: a city among mountains, ice or a volcano
	 *  wider, its edge a slope, not a cliff) and how far its named region's site stands from it (m; 0: 5 km at 300 km's scale) */
	UPROPERTY(BlueprintReadOnly) float EaseM = 1150.f;
	UPROPERTY(BlueprintReadOnly) float BiomeSiteM = 0.f;
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
	/** the list of 2026-11-12's fifth phase: a structure's kind (its index into SiteKinds; -1: none) */
	UPROPERTY(BlueprintReadOnly) int32 Site = -1;
	/** the list of 2026-11-14: a piece of a biome's scenery (its index into SceneryKinds; -1: none) */
	UPROPERTY(BlueprintReadOnly) int32 Scenery = -1;
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
	float Cobble = 0.f;         // (the list of 2026-11-16's fourteenth phase) a major road's cobbles (0-1; Road holds its whole bed)
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
	uint8 FieldStage = 0;             // (the list of 2026-11-14: its field's stage (FRDWFarm::Stage))
	// (the list of 2026-11-14: a dry channel's bed there (an arroyo, a creek bed, a slot canyon): 0-1 toward its middle, its kind)
	float Chan = 0.f; int32 ChanKind = -1;
	// (the list of 2026-11-20's seventh phase: a village's terrace there: 1 on its level ground, falling to 0 over its edge's band)
	float Terrace = 0.f;
};

/** the list of 2026-11-20 (item 26, "cut flat ledges into the hillsides"): a village's level ground: a house's or its square's
 *  rectangle (its middle, its turn: +X its front, toward the square; its half sizes) held at H (the natural ground at its middle) */
struct FRDWPad { FVector2D C = FVector2D::ZeroVector; float Yaw = 0.f; FVector2D Half = FVector2D(8.f, 12.f); float H = 0.f; uint8 Kind = 0; };
struct FRDWTerraces { FVector2D Mid = FVector2D::ZeroVector; double R = 0.0; int32 VillageId = -1; TArray<FRDWPad> Pads; };
/** while one is in scope on a thread, the ground is the land without the villages' terraces (a village is placed on it, and its pads'
 *  heights read from it: no terrace may ask for itself) */
struct FRDWNoTerrace { FRDWNoTerrace(); ~FRDWNoTerrace(); static bool On(); };

/** a ground vertex as the ground material reads it: its colour (the lava in its alpha), UV0 the field rows' way and crop, UV1
 *  rock and snow, UV2 sand and mud, UV3 the road and the field's weight. One rule for the chunks (RDWildChunk.cpp) and the far
 *  land drawn as the ground (RDSkyFar.cpp: "textured the same way it would be textured when approached", PR #45's review) */
struct FRDWGroundVertex
{
	FLinearColor C;
	FVector2D UV0, UV1, UV2, UV3;
	float Slope = 0.f;          // degrees from level
};
/** the sample's ground vertex at a normal: rock where it is steep, the snow sliding off the steepest; with ForestShare the colour
 *  goes toward Forest by the canopy first (the far land, which grows no crowns) */
CLAUDE_UE5_API FRDWGroundVertex RDWildGroundVertex(const FRDWSample& Q, const FVector& Nr, const FLinearColor& Forest = FLinearColor::Black, float ForestShare = 0.f);

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
	/** the list of 2026-11-14 ("fields at different stages: fallow, sprouting, ripe, burned"): 0 ripe, 1 sprouting, 2 fallow, 3 burned */
	uint8 Stage = 0;
};

/** the world's model (see the file's head) */
class CLAUDE_UE5_API FRDWildWorld
{
public:
	// ---- the continent's frame (metres): 150 x 150 km since the list of 2026-11-16 ("reduce the size of the continent to 150km x
	// 150km"; 300 x 300 km before), Brokenspire 40 km from its south edge, mid-way across
	double Xs = -40000.0, Xn = 110000.0, Yw = -75000.0, Ye = 75000.0;
	double CellM = 14000.0 * (110000.0 + 40000.0) / 300000.0;      // a biome region's cell: 14 km times WorldK() (Init sets it so: as many regions, each a quarter of the ground)
	/** the continent's scale against the 300 km it was made at: every distance and wavelength of the continent's own (its coast, its
	 *  climate, its relief's ranges, the cities' places, the port's easing) is the 300 km world's times this; local scales (a hill, a
	 *  town's ground, a road's bed) are not */
	double WorldK() const { return (Xn - Xs) / 300000.0; }
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
	/** a major road between two towns (cobbled and raised since the list of 2026-11-16's fourteenth phase); or (bTrack, bMinor) a
	 *  minor road, dirt, from a place (its Dest, at P[0]) to what it joins (a major road, a village, another minor road: Join the road
	 *  joined, -1 a village), whose signs name Up (UpM metres past its end) the other way (From, To -1) */
	struct FRoad
	{
		TArray<FVector2D> P; TArray<float> Z; FBox2D Box; int32 From = -1, To = -1; bool bTrack = false; bool bMinor = false;
		FString Dest, DestKind, Up; int32 DestId = -1, Join = -1, JoinSeg = -1, ParentVillage = -1; double JoinT = 0.0; double UpM = 0.0;
	};
	TArray<FRoad> Roads;
	/** a sign post (the fourteenth phase): Kind 0 a major road's (every 2 km), 1 a minor road's (every 1 km), 2 at a minor road's
	 *  join; its +Y (Yaw) along the road toward A (Am metres), its second arm toward B (none when empty) */
	struct FRDWildSign { FVector2D At = FVector2D::ZeroVector; float Yaw = 0.f; FString A, B; float Am = 0.f, Bm = 0.f; uint8 Kind = 0; int32 Road = -1; };
	TArray<FRDWildSign> Signs;
	TMultiMap<FIntPoint, int32> SignHash;          // (500 m cells)
	FString MinorStats;
	void SignsNear(const FVector2D& P, double R, TArray<int32>& Out) const;
	/** the roads whose segments the hash holds in a box (bMinor: the minor ones, else the major ones) */
	void RoadsIn(const FBox2D& B, bool bMinor, TArray<int32>& Out) const;
	TArray<int32> MajorRoadIdx;
	static FString SignDistText(double M);
	double RoadAlong(int32 Ri, int32 Seg, double T) const;
	double RoadLength(int32 Ri) const;
	/** the nearest point within R of a road (bMajorOnly: of a road between towns) */
	bool NearestRoadPoint(const FVector2D& P, double R, bool bMajorOnly, int32& OutRoad, int32& OutSeg, double& OutT, FVector2D& OutAt, const TBitArray<>* Allowed = nullptr) const;
	/** what a way joining road Ri at (Seg, T) leads on to, and how far past the join */
	void RoadUp(int32 Ri, int32 Seg, double T, FString& OutName, double& OutM) const;
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
	// (the list of 2026-11-16's thirteenth phase: "2.5 times the density": the places' cells 2 km (4 km before; a village and another
	// place in each), the points', structures' and scenery's cells smaller by the root of 2.5)
	static constexpr double PlaceCellM = 2000.0;
	/** a cell's village and its chance (none on the arctic or glaciers); the other place's chance, more within 1 km of a road between towns */
	float VillageChance = 0.85f, PlaceChance = 0.30f, PlaceChanceByRoad = 0.48f;
	/** whether a road between towns (not a track) passes within R metres of P */
	bool NearTownRoad(const FVector2D& P, double R) const;
	FIntPoint PlaceCellOf(double X, double Y) const { return FIntPoint(FMath::FloorToInt((X - Xs) / PlaceCellM), FMath::FloorToInt((Y - Yw) / PlaceCellM)); }
	bool FindPlace(int32 Id, FRDWildPlace& Out) const;
	/** the ponds (and hot springs) of a 4 km cell */
	void PondsIn(FIntPoint Cell, TArray<FLake>& Out) const;
	/** the ponds' cells: 4 km, their own (the places' became 2 km with the list of 2026-11-16's density: the ponds stay as they were) */
	static constexpr double PondCellM = 4000.0;
	/** the places of a cell as made (PlacesIn caches them: the denser points, scenery and farmsteads ask for them at every try) */
	void PlacesInCell(FIntPoint Cell, TArray<FRDWildPlace>& Out) const;
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
	 *  region (PoiKinds, set after Init from the generator's WildPoiKinds); their ids PoiIdBase + (cell x << 12 | cell y) (the
	 *  continent is 2500 cells across), in the free range under the farms' 2^28 */
	static constexpr int32 PoiIdBase = 1 << 24;
	static constexpr double PoiCellM = 76.0;          // (120 m before the list of 2026-11-16's density)
	TArray<FRDWildPoiKind> PoiKinds;
	float PoiFill = 0.8f;
	FIntPoint PoiCellOf(double X, double Y) const { return FIntPoint(FMath::FloorToInt((X - Xs) / PoiCellM), FMath::FloorToInt((Y - Yw) / PoiCellM)); }
	void PoisIn(FIntPoint Cell, TArray<FRDWildPlace>& Out) const;
	/** the list of 2026-11-12's fifth phase: the structures of the wilds (SitesIn): a 2.5 km grid, one in half its cells, of the
	 *  kinds of the region (SiteKinds, set before Init from the generator's WildSiteKinds), a water kind on its water's shore;
	 *  places of kind "site", ids SiteIdBase + (cell x << 12 | cell y), in the free range between the points of interest's and
	 *  the farms' */
	static constexpr int32 SiteIdBase = 1 << 27;
	static constexpr double SiteCellM = 1580.0;          // (2500 m before the list of 2026-11-16's density)
	TArray<FRDWildSiteKind> SiteKinds;
	float SiteFill = 0.5f;
	FIntPoint SiteCellOf(double X, double Y) const { return FIntPoint(FMath::FloorToInt((X - Xs) / SiteCellM), FMath::FloorToInt((Y - Yw) / SiteCellM)); }
	void SitesIn(FIntPoint Cell, TArray<FRDWildPlace>& Out) const;
	/** each cell's structures, worked out once (a water kind's search is 800 samples, and a chunk asks the 3 x 3 cells round it):
	 *  shared by the worker threads behind a lock, emptied at Init */
	struct FSiteCache { FCriticalSection Lock; TMap<FIntPoint, TArray<FRDWildPlace>> Cells; };
	TSharedPtr<FSiteCache> SiteCache = MakeShared<FSiteCache>();
	TSharedPtr<FSiteCache> PlaceCache2 = MakeShared<FSiteCache>();
	void SitesInCell(FIntPoint Cell, TArray<FRDWildPlace>& Out) const;
	/** the list of 2026-11-14 (docs/improvements13.txt, the biomes' scenery): a 600 m grid, one in SceneryFill of its cells, of the
	 *  kinds of the region (SceneryKinds, set before Init from the generator's WildSceneryKinds), beside a road, at a crossroads, on a
	 *  rise or by water as its kind asks; places of kind "scenery", ids SceneryIdBase + (cell x << 10 | cell y) (500 cells across), in
	 *  the free range between the points of interest's (to 2^24 + 2^24) and the structures' (2^27) */
	static constexpr int32 SceneryIdBase = 1 << 26;
	static constexpr double SceneryCellM = 380.0;          // (600 m before the list of 2026-11-16's density)
	TArray<FRDWildSceneryKind> SceneryKinds;
	float SceneryFill = 0.6f;
	FIntPoint SceneryCellOf(double X, double Y) const { return FIntPoint(FMath::FloorToInt((X - Xs) / SceneryCellM), FMath::FloorToInt((Y - Yw) / SceneryCellM)); }
	void SceneryIn(FIntPoint Cell, TArray<FRDWildPlace>& Out) const;
	TSharedPtr<FSiteCache> SceneryCache = MakeShared<FSiteCache>();
	void SceneryInCell(FIntPoint Cell, TArray<FRDWildPlace>& Out) const;
	/** the list of 2026-11-20's tenth phase (idea 2, RDList15i.cpp): a lookout in each region's cell (CellM), a watchtower on dry, gentle
	 *  ground off the roads, fields and water, 1.5 km from a town and 150 m from every other place, structure, point of interest and
	 *  scenery (so nothing else moves); places of kind "lookout", ids LookoutIdBase + (cell x << 10 | cell y), in the quests' range above
	 *  their own; worked out once a cell, behind a lock (none: Id 0) */
	static constexpr int32 LookoutIdBase = (1 << 29) + (1 << 28);
	FIntPoint LookoutCellOf(double X, double Y) const { return FIntPoint(FMath::FloorToInt((X - Xs) / CellM), FMath::FloorToInt((Y - Yw) / CellM)); }
	bool LookoutOf(FIntPoint Cell, FRDWildPlace& Out) const;
	void LookoutsIn(double X0, double Y0, double X1, double Y1, TArray<FRDWildPlace>& Out) const;
	/** a point R metres from every place, structure, point of interest, scenery, farmstead and quest's place (and, asked, every lookout):
	 *  the layers of the list of 2026-11-20's tenth phase stand clear of all of them (PR #102's review) */
	bool ClearOfPlaces15(const FVector2D& S, double R, bool bLookouts) const;
	struct FLookoutCache { FCriticalSection Lock; TMap<FIntPoint, FRDWildPlace> Cells; };
	TSharedPtr<FLookoutCache> LookoutCache = MakeShared<FLookoutCache>();
	/** the list of 2026-11-20's sixteenth phase (RDList15o.cpp): a waystone beside the major road nearest each region's cell's middle, 12 m
	 *  off it, 1.5 km from a town and 80 m from every other place; places of kind "waystone", ids WaystoneIdBase + (cell x << 10 | cell y),
	 *  above the lookouts'; worked out once a cell (none: Id 0) */
	static constexpr int32 WaystoneIdBase = (1 << 29) + (1 << 28) + (1 << 27);
	bool WaystoneOf(FIntPoint Cell, FRDWildPlace& Out) const;
	TSharedPtr<FLookoutCache> WaystoneCache = MakeShared<FLookoutCache>();
	/** the generator's own layers a waystone keeps clear of (its region landmarks): set by it in play, asked on the game thread */
	TFunction<bool(const FVector2D&)> WaystoneVeto;
	/** where two roads meet (Init): the crossroads a scenery kind of Place "crossroads" stands at */
	TArray<FVector2D> Crossroads;
	/** the dry channels cut into the land (Init, from ChannelRules): arroyos and creek beds, slot canyons, crevasses, fissures; each a
	 *  line of points, its width and depth (metres) and its kind (ChannelRules' index); its segments hashed on their own (ChanHash:
	 *  2 km cell -> index << 16 | segment), apart from the rivers' (whatever reads SegHash takes a river for water) */
	struct FChannel { TArray<FVector2D> P; float W = 10.f; float D = 3.f; float Wall = 0.5f; int32 Kind = 0; FBox2D Box; };
	TArray<FChannel> Channels;
	TMultiMap<FIntPoint, uint32> ChanHash;
	/** the channel nearest a point within its reach: its index (-1 none), its distance from the middle line and how far along (0-1) */
	int32 NearestChannel(double X, double Y, double& Dist, double& Along) const;
	/** a kind of channel: "biomes=a,b;n=<per region cell>;len=lo-hi;w=lo-hi;d=lo-hi;wall=<0 a soft trough .. 1 sheer walls>;turn=<deg a
	 *  20 m step>;name=.." (set before Init from the generator's WildChannelRules) */
	TArray<FString> ChannelRules;
	TArray<FString> ChannelNames;
	void MakeChannels();
	TArray<FRDWildPlace> QuestPlaces;
	/** a quest goal's place ("wild:wolves" -> the den), or null */
	const FRDWildPlace* QuestPlaceFor(const FString& Goal) const;

	// ---- the noise (public for the map and the chunks)
	static float Perlin(double X, double Y, uint32 S);
	/** the list of 2026-11-11: the groves of an open land at a point (metres): 1 in a cluster of trees (60-150 m across) or a strip
	 *  of them (about 15 m wide, broken), 0 between them, and 0 over the clearings (large areas a few hundred metres across) */
	float Grove(double X, double Y) const;
	/** the list of 2026-11-11 ("in graymourne, the terrain should be shoreline, with the water extending out into an ocean"): set
	 *  before Init (the generator's bPortWaterOpen): the port stands on its coast, its harbour open to the sea, and the land and
	 *  sea round it are lifted so the sea is at the harbour's water (PortLift); its coast blends in wider (Blend) */
	bool bPortSea = false;
	// ---- the list of 2026-11-20's seventh phase (RDList15f.cpp): the villages' terraces (the generator's bVillageTerraces15), on only
	// once Init has made the world (its roads are made from heights before every place is final)
	bool bTerraces15 = false, bTerracesReady = false;
	bool bTerraceGroundOff = false;          // (the probe's -NoTerraces: the villages placed and laid out the same, the ground left as the land)
	/** how far from a village's middle its ways start (the list of 2026-11-20: past its outer ring of pads, 63 m, and the road bed's own
	 *  easing: a bed run through the pads, the land's coarse height smoothed, stood up to 58 m off a mountain village's terraces) */
	double VillageWayInsetM() const { return bTerraces15 ? 85.0 : 45.0; }
	TMultiMap<FIntPoint, FVector2D> VillageDots15;          // (the villages' middles while the minor roads are made: ways keep 100 m clear of them)
	static constexpr int32 VillageHousesMin = 8;
	static constexpr int32 VillageHousesMax = 15;
	static constexpr float TerraceMaxStepM = 7.f;
	static constexpr float TerraceRampRun = 3.f;
	static constexpr float VillageInnerRingM = 36.f;          // (the slots' rings round the square)
	static constexpr float VillageOuterRingM = 60.f;          // (an 8 m yard between the rings: at 55 m an outer house's door faced an inner house's back 3 m off, up 1.4 m in a metre)          // (a door side's earth ramp: metres along for a metre up)          // (a village whose pads would stand more than this off the land is not placed)
	/** a village's pads (no heights): its square, then 8 to 15 of its 15 slots (seven on a ring at 33 m, eight at 55 m, facing the
	 *  square) where a house can stand (the land within TerraceMaxStepM of the pad's middle over it, no water), in order; the number
	 *  of slots that can (from the place's own hash: its count and jitters drawn whatever the land) */
	int32 VillageSlots(const FRDWildPlace& V, TArray<FRDWPad>* Out) const;          // (Out: the square and the slots kept, their heights as tested)
	/** the terraces of the village of the place cell holding (X, Y), worked out once a cell (null where none) */
	TSharedPtr<const FRDWTerraces> TerracesAt(double X, double Y) const;
	/** the cell's village's terraces recorded where the village is placed (PlacesInCell), so the pads are those its placing tested:
	 *  the places are made during Init, before the minor roads whose beds change the ground (worked out afterwards, two of six
	 *  villages placed had no pads) */
	void StoreTerraces(FIntPoint Cell, const FRDWildPlace* V, const TArray<FRDWPad>* Pads) const;
	uint32 TerraceGen = 0;          // (counted up at each Init: a thread's last cell asked for is kept by it)
	/** the ground with no terraces, before the port's lift (Feature's frame) */
	float NaturalHeight(double X, double Y) const;
	/** where a pad's height is read: a house's front door's edge, the square's middle */
	static FVector2D PadRef(const FRDWPad& Pd);
	/** a sample's height with the terraces: H on a pad, eased to the land over its band (a door side's ramp, a long side's wall); Terrace 0-1 */
	float ApplyTerrace(double X, double Y, float H, float& Terrace) const;
	struct FTerraceCache { FCriticalSection Lock; TMap<FIntPoint, TSharedPtr<const FRDWTerraces>> Cells; };
	TSharedPtr<FTerraceCache> TerraceCache = MakeShared<FTerraceCache>();
	FVector2D PortSite = FVector2D(1e12, 1e12);
	float PortLiftM = 0.f;
	/** how much the land and the sea are lifted at a point (metres): PortLiftM within 2.5 km of the port, easing to 0 by 40 km */
	float PortLift(double X, double Y) const;
	/** the port plan's harbour (RDTownPlan.cpp's bPort) in its frame's tiles: from PortHarbourDepthTiles before the frame's far
	 *  edge to it, PortHarbourSideTiles in from each side; the frame PortFrameMarginTiles in from the section's edge, a tile
	 *  PortTileM; the frame's G 0 puts the sea at +X. The world's sea bed out of the harbour's mouth is cut by the same numbers */
	static constexpr int32 PortHarbourDepthTiles = 26;
	static constexpr int32 PortHarbourSideTiles = 24;
	static constexpr int32 PortFrameMarginTiles = 4;
	static constexpr float PortTileM = 3.f;
	/** the swimming's depths (cm), one set (2026-11-12; PR #53's review: they must change together): she swims once her feet are
	 *  SwimDepthCm under the face (the generator's SwimDepth's default), so every swum floor lies deeper than that and its 15 cm
	 *  way out: the wilds' floor under deep water down to SwimFloorWildCm (RDWildChunk.cpp), the open harbour's floor
	 *  SwimFloorHarbourCm under its water (RDPort.cpp's HarbourFloorZ), and the bed out of the harbour's mouth SwimBedMouthCm
	 *  under the sea at the section's edge (RDWildWorld.cpp), so the harbour's floor and the wilds' meet there */
	static constexpr float SwimDepthCm = 120.f;
	static constexpr float SwimFloorWildCm = 145.f;
	static constexpr float SwimFloorHarbourCm = 140.f;
	static constexpr float SwimBedMouthCm = 150.f;
	static_assert(SwimFloorWildCm > SwimDepthCm + 15.f && SwimFloorHarbourCm > SwimDepthCm + 15.f, "a swum floor deeper than the swim's start and its way out");
	static_assert(SwimBedMouthCm >= SwimFloorWildCm && SwimBedMouthCm >= SwimFloorHarbourCm, "the mouth's bed under both floors it joins");
	/** the land's height over the shore scaled down round the port (35 % within 9 km, the whole by 30 km): the uplands rise
	 *  from its coast over kilometres (LandHeight and Sample alike, before the coast) */
	float PortFlatten(double X, double Y, float H) const;
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
	void MakeCrossroads();
	/** the list of 2026-11-16's fourteenth phase (RDWildRoads14.cpp): the minor roads, dirt, to every village (down to the major roads),
	 *  place, structure and farmstead near a road; they took the tracks' place (the crossroads are where they leave a major road) */
	void MakeMinorRoads();
	bool MinorPath(const FVector2D& A, const FVector2D& B, uint32 Sk, const TMultiMap<FIntPoint, FVector2D>& Dots, const FVector2D& OwnA, const FVector2D& OwnB, TArray<FVector2D>& Out) const;
	void MakeSigns();
	/** where a major road runs within 30 m of an earlier one (two roads out of one gate: Brokenspire's to Ashenreach and to Vel Morrath ran
	 *  side by side 7 m apart for kilometres), it takes the earlier one's line and bed, eased in over 30 to 60 m */
	void MergeMajorRoads();
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
	/** the list of 2026-11-14 (a herd's migration, its stampede): walked or run toward To for Seconds, as its own wandering does; a herd's
	 *  beast (HerdId >= 0) keeps to its herd and is not dropped with the loose animals round her */
	void Drive(const FVector& To, bool bRun, float Seconds);
	int32 HerdId = -1, HerdIndex = -1;
	/** a herd's beast far from her rests: its tick and its body's off (TickWildScenery13) */
	void SetDormant(bool bDormant);
	bool bDormant = false;
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
	/** the list of 2026-11-20 (item 22): the hearths of its houses and farmhouses, heard crackling (Env.Hearth) as the dungeon's are */
	TArray<FVector> HearthPoints15;
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
	/** the ground's collision (hidden, BlockAll, the whole 2 m grid); cooked on a worker unless she was running fast when it was asked */
	UPROPERTY() TObjectPtr<UProceduralMeshComponent> GroundCollision = nullptr;
	/** the list of 2026-11-22's third phase: the drawn ground's every-n-th vertex (1, 2, 4), the ticket it was asked at (a ground-only job
	 *  for an older chunk of the same place is not applied), a ground-only job on its way */
	UPROPERTY(BlueprintReadOnly) int32 DrawEvery16 = 1;
	int32 Ticket16 = 0, RegridSeq16 = 0;
	bool bRegrid16 = false;
	/** the list of 2026-11-10: its houses' doors (a leaf on its hinge: F opens and shuts it) and its houses (their insides) */
	struct FDoor
	{
		TWeakObjectPtr<USceneComponent> Pivot; FVector At = FVector::ZeroVector; FVector Out = FVector::ForwardVector; float OutYaw = -90.f; float OpenYaw = -90.f; float Alpha = 0.f; float Target = 0.f;
		/** the list of 2026-11-11's fourth phase: a container (AddWildBox): its lid or doors turn about Axis from Closed by Angle
		 *  (a wardrobe's second door Pivot2); its kind, the key the game keeps it looted under, what it gives */
		bool bBox = false;
		TWeakObjectPtr<USceneComponent> Pivot2;
		FVector Axis = FVector::RightVector; FQuat Closed = FQuat::Identity, Closed2 = FQuat::Identity; float Angle = 0.f, Angle2 = 0.f;
		FName Kind; int64 Key = 0; FString Loot;
	};
	TArray<FDoor> Doors;
	struct FHouse { FVector C = FVector::ZeroVector; FVector2D H = FVector2D::ZeroVector; float Yaw = 0.f; int32 Doors = 0; int32 Furniture = 0; int32 PropsGone = 0; bool bLit = false; float FloorZ = 0.f; FString Of;
		// (the list of 2026-11-20's eighth phase: its beds (each bed's middle on the floor, its yaw: the foot +X) and its first door, outside
		// on the ground and inside on the floor, for a household (RDList15g.cpp))
		TArray<FTransform> Beds15; FVector DoorOut15 = FVector::ZeroVector, DoorIn15 = FVector::ZeroVector; bool bDoor15 = false;
	FVector RoomC15 = FVector::ZeroVector;          // (the room's middle, on the floor (PR #100's review: its mesh's origin is not it))
	};
	TArray<FHouse> Houses;
	/** ground kept clear of plants (a house's inside): its middle and half sizes (cm, the chunk's frame) and its yaw; the near grass
	 *  made as she comes leaves it out */
	struct FClear
	{
		FVector2D C = FVector2D::ZeroVector; FVector2D H = FVector2D::ZeroVector; float Yaw = 0.f;
		bool Contains(const FVector& L, float Pad = 0.f) const
		{
			const FVector2D D(L.X - C.X, L.Y - C.Y);
			const float S = FMath::Sin(FMath::DegreesToRadians(-Yaw)), Co = FMath::Cos(FMath::DegreesToRadians(-Yaw));
			return FMath::Abs(D.X * Co - D.Y * S) <= H.X + Pad && FMath::Abs(D.X * S + D.Y * Co) <= H.Y + Pad;
		}
	};
	TArray<FClear> Clears;
	bool IsClear(const FVector& Local) const;
	/** the list of 2026-11-16's fifth phase: its stations (the alchemist's and librarian's tables, a farmhouse's oven): where each
	 *  stands (world cm), its yaw, its kind ("Alchemist", "Librarian", "Oven") and its place's or farm's id (a farm taken away takes
	 *  its own) */
	struct FStation14 { FVector At = FVector::ZeroVector; float Yaw = 0.f; FName Kind; int32 Owner = -1; TWeakObjectPtr<class UPrimitiveComponent> Comp; };
	TArray<FStation14> Stations14;
	virtual void Destroyed() override;
};
