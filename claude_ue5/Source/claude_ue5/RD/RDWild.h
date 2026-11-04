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
	/** the place's tier (the monsters' strength): 1 near Brokenspire, 5 far off */
	int32 TierAt(double X, double Y) const;
	/** a name for a place */
	FString NameFor(const FString& Kind, uint32 H) const;
	/** a town's place id is TownIdBase + its index: far above any other place's ((cell x << 14) | (cell y << 4) | k, under
	 *  2^24; the 1000000 it was first collided with the places of the northern cells, x 62 and on) */
	static constexpr int32 TownIdBase = 1 << 30;

	// ---- the noise (public for the map and the chunks)
	static float Perlin(double X, double Y, uint32 S);
	static float Fbm(double X, double Y, double Freq, int32 Oct, uint32 S, float Gain = 0.5f);
	static float Ridged(double X, double Y, double Freq, int32 Oct, uint32 S);
	static uint32 Hash(int32 X, int32 Y, uint32 S);
	static float Rand01(int32 X, int32 Y, uint32 S) { return (Hash(X, Y, S) & 0xFFFFFF) / 16777216.f; }

private:
	float ShapeHeight(int32 B, double X, double Y, const FVector2D& Site, bool bDetail) const;
	float LandRelief(double X, double Y, bool bDetail, const int32* Bi, const float* W, int32 N) const;
	float LandHeight(double X, double Y, bool bDetail, int32* OutB = nullptr, int32* OutB2 = nullptr, float* OutW = nullptr, float* OutC = nullptr) const;
	void AssignBiomes();
	void PlaceTowns();
	void MakeRivers();
	void MakeLakes();
	void MakeRoads();
	void HashSegments();
	float Feature(double X, double Y, float H, FRDWSample* S) const;   // rivers, lakes, ponds, roads, towns on H
	int32 Biome(const TCHAR* Name) const { const int32* I = BiomeIndex.Find(Name); return I ? *I : 0; }
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
	virtual void Destroyed() override;
};
