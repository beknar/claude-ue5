// random_dungeon_level: shared data types (filled by pipeline/unreal/772_rd_level.py).
#pragma once

#include "CoreMinimal.h"
#include "RDTypes.generated.h"

class UStaticMesh;
class USkeletalMesh;
class UAnimationAsset;
class UAnimSequenceBase;
class UNiagaraSystem;

/** A placeable mesh normalised by Adjust to the dungeon frame: origin at the footprint centre on the floor, front toward
 *  +X (furniture faces +X; wall pieces run along Y with their room face toward +X; floor tiles centred, top at z = 0;
 *  ceiling tiles centred, underside at z = 0). Size = footprint (X depth, Y width) and height after Adjust. */
USTRUCT(BlueprintType)
struct FRDPiece
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UStaticMesh> Mesh = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FTransform Adjust;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FVector Size = FVector(100);
	UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bCollision = true;
	/** collision only (invisible blockers, e.g. behind cell bars whose own collision is unusable) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bHidden = false;
	/** hinge (door leaves: piece frame, the leaf spans +Y from it) or lid hinge (containers: piece frame) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FVector Hinge = FVector::ZeroVector;
	/** containers: the lid / door part that moves (same Adjust as Mesh) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UStaticMesh> Moving = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UStaticMesh> Moving2 = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FVector Hinge2 = FVector::ZeroVector;
	/** prefab: an actor blueprint spawned instead of an instanced mesh (Mesh may stay empty); Adjust applies */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TSubclassOf<AActor> ActorClass;
};

/** A wandering monster type: its own skeletal mesh and idle / walk clips (played directly, no AnimBP). */
USTRUCT(BlueprintType)
struct FRDMonsterDef
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Name;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<USkeletalMesh> Mesh = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimationAsset> Idle = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimationAsset> Walk = nullptr;
	/** walking speed (cm/s) and the root speed of the walk clip at rate 1 (play rate = speed / this) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float WalkSpeed = 140.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float WalkClipSpeed = 140.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float CapsuleRadius = 40.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float CapsuleHalfHeight = 90.f;
	/** mesh relative transform: z (feet on the capsule bottom), yaw (mesh forward to +X), scale */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float MeshZ = -90.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float MeshYaw = -90.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Scale = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Weight = 1.f;
	// ---- fighting (random_dungeoncombat_level): clips played directly, like idle / walk
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<TObjectPtr<UAnimationAsset>> Attacks;
	/** seconds into each attack clip at which the blow lands */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<float> HitTimes;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimationAsset> GetHit = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimationAsset> Death = nullptr;
	/** this kind's hit points and damage against the average monster (the generator scales the average to the player) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float HealthFactor = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float DamageFactor = 1.f;
	/** how far beyond its own capsule a blow reaches (cm), and seconds between two attacks */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Reach = 110.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float AttackInterval = 1.6f;
};

/** One of the player's melee weapons: the mesh in her hand (and a shield on her other arm), what it does, and the
 *  clips she wields it with (retargeted to her skeleton by pipeline/unreal/790). */
USTRUCT(BlueprintType)
struct FRDWeaponDef
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Name;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UStaticMesh> Mesh = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName HandBone = TEXT("hand_r");
	/** the mesh relative to the hand bone */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FTransform Grip;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UStaticMesh> OffHandMesh = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName OffHandBone = TEXT("lowerarm_l");
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FTransform OffHandGrip;
	/** hit points a blow takes; how far it reaches from her to a monster's capsule (cm); the arc in front of her (degrees) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Damage = 20.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Reach = 170.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Arc = 120.f;
	/** attack clips, played in turn; of each the part played (seconds: start, end; 0 = the clip's end) and when the blow lands */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<TObjectPtr<UAnimSequenceBase>> Attacks;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<float> AttackStarts;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<float> AttackEnds;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<float> HitTimes;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float PlayRate = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimSequenceBase> GetHit = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimSequenceBase> Death = nullptr;
};

UENUM(BlueprintType)
enum class ERDRoomKind : uint8
{
	Hall, Barracks, Prison, Torture, Storeroom, Armory, Kitchen, Library, Chapel, Crypt, Treasury, GuardRoom, Forge, Junction
};

/** map data of one room or corridor (tile rectangle, global tile coords, max exclusive) */
USTRUCT(BlueprintType)
struct FRDMapRect
{
	GENERATED_BODY()
	UPROPERTY(BlueprintReadOnly) FIntPoint Min = FIntPoint::ZeroValue;
	UPROPERTY(BlueprintReadOnly) FIntPoint Max = FIntPoint::ZeroValue;
	UPROPERTY(BlueprintReadOnly) ERDRoomKind Kind = ERDRoomKind::Junction;
	/** room (false) or corridor (true) */
	UPROPERTY(BlueprintReadOnly) bool bCorridor = false;
	UPROPERTY(BlueprintReadOnly) bool bDiscovered = false;
};

/** map data of one section: kept for the whole session (also after the section is unloaded) */
USTRUCT(BlueprintType)
struct FRDSectionMap
{
	GENERATED_BODY()
	UPROPERTY(BlueprintReadOnly) FIntPoint Coord = FIntPoint::ZeroValue;
	UPROPERTY(BlueprintReadOnly) TArray<FRDMapRect> Rects;
	/** door positions (world XY) */
	UPROPERTY(BlueprintReadOnly) TArray<FVector2D> Doors;
	/** containers and lights (world XY): the stylised maps draw them */
	UPROPERTY(BlueprintReadOnly) TArray<FVector2D> Chests;
	UPROPERTY(BlueprintReadOnly) TArray<FVector2D> Torches;
	UPROPERTY(BlueprintReadOnly) float GeneratedTime = -1.f;
	UPROPERTY(BlueprintReadOnly) bool bStart = false;
};
