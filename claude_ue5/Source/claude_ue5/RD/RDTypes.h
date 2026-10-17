// random_dungeon_level: shared data types (filled by pipeline/unreal/772_rd_level.py).
#pragma once

#include "CoreMinimal.h"
#include "RDTypes.generated.h"

class UStaticMesh;
class USkeletalMesh;
class UAnimationAsset;
class UAnimSequenceBase;
class UNiagaraSystem;
class USoundBase;
class UFXSystemAsset;

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
	/** its voice and footsteps: the generator's Sounds "Monster.<SoundSet>.Step / Hurt / Roar / Attack / Death / Idle" */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName SoundSet;
	/** ground covered between two footstep sounds (cm) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float StepLength = 80.f;
};

/** Sounds for one occasion ("Player.Hurt", "Env.DoorOpen", "Monster.Troll.Roar"...): one of them is played each time,
 *  at Volume and Pitch (+- PitchVariation). Unless b2D it is played where it happens and fades with the distance to the
 *  player: full volume within InnerRadius, silent FalloffDistance beyond that. */
USTRUCT(BlueprintType)
struct FRDSoundSet
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<TObjectPtr<USoundBase>> Sounds;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Volume = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Pitch = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float PitchVariation = 0.05f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float InnerRadius = 200.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float FalloffDistance = 2500.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) bool b2D = false;
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
	// ---- a spell (random_dungeonmagic_level): at the hit time a bolt leaves her hand instead of a blow landing. It flies
	// at BoltSpeed after the monster she turned to (steering at most BoltTurnRate degrees a second), at most Reach cm,
	// and bursts on the first monster or wall it meets: that monster takes Damage, every other one within BoltSplash cm
	// of the burst half of it. Arc is not used.
	UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bSpell = false;
	/** a spell cast with keys of its own (right mouse button or E; Y or the left trigger) while the weapon she has drawn
	 *  stays in her hand (random_dungeonmagic_level2: the fire from her left hand, the sword in her right); the number
	 *  keys do not draw it */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bAlongside = false;
	/** where the bolt leaves her (and the charge burns while she gathers it) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName SpellBone = TEXT("hand_r");
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float BoltSpeed = 1600.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float BoltTurnRate = 220.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float BoltSplash = 170.f;
	/** effects (a Niagara system or a Cascade particle system): on her hand from the start of the cast to the release,
	 *  on the bolt, and where it bursts; each with its scale. When the charge is the same system as the bolt, the charge
	 *  itself leaves her hand as the bolt (a system that takes a while to build up is full grown when it flies). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UFXSystemAsset> ChargeEffect = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float ChargeEffectScale = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UFXSystemAsset> BoltEffect = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float BoltEffectScale = 1.f;
	/** a second system on the bolt (its core, under the flames) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UFXSystemAsset> BoltCoreEffect = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float BoltCoreEffectScale = 1.f;
	/** the burst: a one-shot system, and flames that burn on where it burst for BurstFlameSeconds (a looping system is
	 *  stopped then and its particles die away) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UFXSystemAsset> BurstEffect = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float BurstEffectScale = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UFXSystemAsset> BurstFlameEffect = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float BurstFlameEffectScale = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float BurstFlameSeconds = 0.6f;
	/** the bolt lights what it passes (a point light that goes with it; brighter for a moment where it bursts) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FLinearColor SpellLightColor = FLinearColor(1.f, 0.45f, 0.12f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float SpellLightIntensity = 0.f;
	// ---- a crossbow (random_dungeonmagic_level3): a spell whose bolt is a mesh, shot from the weapon (BoltTurnRate 0:
	// it flies straight at the monster she turned to)
	/** the flying bolt's mesh, placed by BoltMeshTransform in the bolt's frame (+X the way it flies, its point at the origin) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UStaticMesh> BoltMesh = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FTransform BoltMeshTransform;
	/** the bolt leaves from BoltMuzzle, a point of the weapon's mesh (its own space), instead of SpellBone */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bBoltFromWeapon = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FVector BoltMuzzle = FVector::ZeroVector;
	/** the next bolt lies on the weapon (LoadedBoltTransform: the bolt mesh relative to the weapon's mesh), gone from the
	 *  shot until the attack is over (she has loaded it again) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bShowLoadedBolt = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FTransform LoadedBoltTransform;
	/** seconds a bolt stays stuck where it struck a wall, a door or the floor */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float BoltStickSeconds = 0.f;
	// ---- where the weapon is carried while another one is drawn (none: out of sight), and its off-hand mesh
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName HolsterBone = NAME_None;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FTransform HolsterGrip;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName OffHandHolsterBone = NAME_None;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FTransform OffHandHolsterGrip;
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
