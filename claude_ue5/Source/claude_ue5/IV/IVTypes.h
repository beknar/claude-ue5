// random_isometric_village_level: shared data types (pieces filled by pipeline/unreal/780_iv_level.py).
#pragma once

#include "CoreMinimal.h"
#include "IVTypes.generated.h"

class UStaticMesh;
class USkeletalMesh;
class UAnimationAsset;

/** A placeable mesh normalised by Adjust to the village frame: origin at the footprint centre on the floor, front toward
 *  +X (furniture faces +X; wall pieces run along Y with their outside face toward +X; floor tiles centred, top at z = 0).
 *  Size = footprint (X depth, Y width) and height after Adjust. */
USTRUCT(BlueprintType)
struct FIVPiece
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UStaticMesh> Mesh = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FTransform Adjust;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FVector Size = FVector(100);
	UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bCollision = true;
	/** collision only (invisible blockers) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bHidden = false;
	/** door leaves: hinge in the piece frame (the leaf spans +Y from it); containers: lid hinge (piece frame) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FVector Hinge = FVector::ZeroVector;
	/** containers: the lid / door part that moves (same Adjust as Mesh) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UStaticMesh> Moving = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UStaticMesh> Moving2 = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FVector Hinge2 = FVector::ZeroVector;
	/** prefab: an actor blueprint spawned instead of an instanced mesh; Adjust applies */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TSubclassOf<AActor> ActorClass;
};

/** A villager model: a whole-body skeletal mesh with idle / walk clips on its own skeleton (780 fills the generator's list). */
USTRUCT(BlueprintType)
struct FIVVillagerDef
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Name;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<USkeletalMesh> Mesh = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimationAsset> Idle = nullptr;
	/** in-place walk cycle */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimationAsset> Walk = nullptr;
	/** ground speed the walk clip is drawn for at play rate 1 and scale 1 (cm/s) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float WalkClipSpeed = 237.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Scale = 1.f;
	/** turns the mesh's front to the actor's +X */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float MeshYaw = -90.f;
	/** how often this model is picked */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Weight = 1.f;
};

UENUM(BlueprintType)
enum class EIVBuildingKind : uint8
{
	Cottage, Farmhouse, Tavern, Smithy, Bakery, Store, Workshop, Barn, Storehouse, Church, Manor
};

/** building style = which wall / roof set of the house kit */
UENUM(BlueprintType)
enum class EIVStyle : uint8 { Thatch, Timber, Stone };

/** map data of one building (the HUD draws it as a small block with its roof) */
USTRUCT(BlueprintType)
struct FIVMapBuilding
{
	GENERATED_BODY()
	UPROPERTY(BlueprintReadOnly) FVector2D Center = FVector2D::ZeroVector;
	/** half footprint in the building frame (x = depth: front is +X, y = width) */
	UPROPERTY(BlueprintReadOnly) FVector2D Half = FVector2D(400, 400);
	UPROPERTY(BlueprintReadOnly) float Yaw = 0.f;
	UPROPERTY(BlueprintReadOnly) float WallHeight = 300.f;
	UPROPERTY(BlueprintReadOnly) float RoofHeight = 300.f;
	/** ridge along the building's Y axis (else X) */
	UPROPERTY(BlueprintReadOnly) bool bRidgeAlongY = true;
	/** tower (church): height above the ground of its roof base, 0 = none; it stands on the front (+X) end */
	UPROPERTY(BlueprintReadOnly) float TowerHeight = 0.f;
	UPROPERTY(BlueprintReadOnly) EIVStyle Style = EIVStyle::Timber;
	UPROPERTY(BlueprintReadOnly) EIVBuildingKind Kind = EIVBuildingKind::Cottage;
	/** main door (world XY) */
	UPROPERTY(BlueprintReadOnly) FVector2D Door = FVector2D::ZeroVector;
	UPROPERTY(BlueprintReadOnly) bool bVisited = false;
};

/** a road centre line inside one section (0 lane, 1 main road, 2 ring street) */
USTRUCT(BlueprintType)
struct FIVMapRoad
{
	GENERATED_BODY()
	UPROPERTY(BlueprintReadOnly) TArray<FVector2D> Points;
	UPROPERTY(BlueprintReadOnly) float HalfWidth = 200.f;
	UPROPERTY(BlueprintReadOnly) uint8 Type = 0;
};

/** a ground patch (convex polygon): 0 cobbled square, 1 field, 2 garden, 3 green, 4 pond, 5 churchyard */
USTRUCT(BlueprintType)
struct FIVMapPatch
{
	GENERATED_BODY()
	UPROPERTY(BlueprintReadOnly) TArray<FVector2D> Points;
	UPROPERTY(BlueprintReadOnly) uint8 Type = 0;
};

/** 0 broadleaf, 1 conifer, 2 fruit tree, 3 bush */
USTRUCT(BlueprintType)
struct FIVMapTree
{
	GENERATED_BODY()
	UPROPERTY(BlueprintReadOnly) FVector2D P = FVector2D::ZeroVector;
	UPROPERTY(BlueprintReadOnly) float Radius = 200.f;
	UPROPERTY(BlueprintReadOnly) float Height = 600.f;
	UPROPERTY(BlueprintReadOnly) uint8 Type = 0;
};

/** small landmark: 0 well, 1 market stall, 2 cart, 3 haystack, 4 statue / cross, 5 tent, 6 gravestone */
USTRUCT(BlueprintType)
struct FIVMapProp
{
	GENERATED_BODY()
	UPROPERTY(BlueprintReadOnly) FVector2D P = FVector2D::ZeroVector;
	UPROPERTY(BlueprintReadOnly) float Yaw = 0.f;
	UPROPERTY(BlueprintReadOnly) uint8 Type = 0;
};

/** map data of one section: kept for the whole session (also after the section is unloaded) */
USTRUCT(BlueprintType)
struct FIVSectionMap
{
	GENERATED_BODY()
	UPROPERTY(BlueprintReadOnly) FIntPoint Coord = FIntPoint::ZeroValue;
	UPROPERTY(BlueprintReadOnly) TArray<FIVMapBuilding> Buildings;
	UPROPERTY(BlueprintReadOnly) TArray<FIVMapRoad> Roads;
	UPROPERTY(BlueprintReadOnly) TArray<FIVMapPatch> Patches;
	UPROPERTY(BlueprintReadOnly) TArray<FIVMapTree> Trees;
	UPROPERTY(BlueprintReadOnly) TArray<FIVMapProp> Props;
	UPROPERTY(BlueprintReadOnly) float GeneratedTime = -1.f;
	UPROPERTY(BlueprintReadOnly) bool bStart = false;
};

/** one building site of the village plan (pure function of the plan seeds) */
struct FIVLot
{
	FVector2D Center = FVector2D::ZeroVector;
	/** building frame: +X = front (toward its road) */
	float Yaw = 0.f;
	/** footprint in kit cells: X = depth (front to back), Y = width along the road */
	int32 CellsX = 2, CellsY = 2;
	int32 Band = 0, Sector = 0, Row = 0, Index = 0;
	/** landmark assigned by the plan (square row), else -1: chosen by the section from its own seed */
	int32 FixedKind = -1;
	/** distance of the lot centre from the village centre */
	float Radius = 0.f;
	/** stable id of the lot (seeding its content) */
	uint32 Id = 0;
};
