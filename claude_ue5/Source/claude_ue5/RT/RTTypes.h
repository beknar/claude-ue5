// random_level procedural town: shared data types (filled from SourceArt/random_level/templates.json by 753).
#pragma once

#include "CoreMinimal.h"
#include "RTTypes.generated.h"

class UStaticMesh;

/** A door leaf (pivot = hinge) inside a building template; ClosedYaw is the leaf yaw when shut (template frame). */
USTRUCT(BlueprintType)
struct FRTDoorDef
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UStaticMesh> Mesh = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FVector Location = FVector::ZeroVector;
	/** yaw of the leaf as placed in the source level (it may stand ajar): used to find and hide the original */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float SourceYaw = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float ClosedYaw = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FVector Scale = FVector::OneVector;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bExterior = false;
};

/** An existing lid (crate) inside a template that becomes openable: hidden in the level, replaced by a hinged copy. */
USTRUCT(BlueprintType)
struct FRTLidDef
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UStaticMesh> Mesh = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FTransform Transform;
};

UENUM(BlueprintType)
enum class ERTAddKind : uint8 { Chest, Trunk, Wardrobe, Washstand };

/** Furniture added to a template (bedroom chests, wardrobes / washstands): local location (floor) + yaw (front = +Y). */
USTRUCT(BlueprintType)
struct FRTAddition
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) ERTAddKind Kind = ERTAddKind::Chest;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FVector Location = FVector::ZeroVector;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Yaw = 0.f;
};

USTRUCT(BlueprintType)
struct FRTPath
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FVector2D> Points;
};

/** One building type: a level (docks building level instance) or an actor class (Sherwood house prefab). */
USTRUCT(BlueprintType)
struct FRTBuildingTemplate
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Name;
	/** tavern | home | store | workshop | cabin */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Purpose;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TSoftObjectPtr<UWorld> Level;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TSoftClassPtr<AActor> ActorClass;
	/** XY footprint in the template frame */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FVector2D BoundsMin = FVector2D::ZeroVector;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FVector2D BoundsMax = FVector2D::ZeroVector;
	/** entry floor height in the template frame (placed on the flattened lot) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float FloorZ = 0.f;
	/** main entrance: opening centre + outward direction (turned toward the street) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FVector2D EntryMid = FVector2D::ZeroVector;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FVector2D EntryOut = FVector2D(0, 1);
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Weight = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FRTDoorDef> Doors;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FRTLidDef> Lids;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FRTAddition> Additions;
	/** walk-test paths over the entry floor, from just inside the entrance (template frame) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FRTPath> Paths;
};

/** A scattered mesh (HISM): weight, uniform scale range, collision, cull distance (0 = none). */
USTRUCT(BlueprintType)
struct FRTScatterItem
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UStaticMesh> Mesh = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Weight = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FVector2D Scale = FVector2D(1, 1);
	UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bCollision = true;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float CullDistance = 0.f;
	/** keep this far (cm) from buildings / other solid props */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Radius = 100.f;
};
