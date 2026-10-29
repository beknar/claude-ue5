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
class APawn;
class UTexture2D;

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

/** random_dungeonmagic_level5: what a monster's blow does to her besides its damage */
UENUM(BlueprintType)
enum class ERDMonsterAbility : uint8
{
	None, Poison, Weaken, Slow
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
	// ---- random_dungeonmagic_level5: the monster gallery's tiers (docs/monsters.md, pipeline/unreal/859)
	/** the tier of rooms it lives in (0: any; with the generator's MaxTier a section spawns only the kinds of its tier) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 Tier = 0;
	/** what its blow does to her besides its damage (none, poison: hit points over a few seconds, weaken: her blows and
	 *  spells do less for a while, slow: she moves slower for a while); the generator's tier scales how strong */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) ERDMonsterAbility Ability = ERDMonsterAbility::None;
	/** parts that follow its body (on its skeleton: a head, a weapon made on the same skeleton) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<TObjectPtr<USkeletalMesh>> Parts;
	/** a weapon in its hand (a static mesh on HandBone, placed by WeaponGrip) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UStaticMesh> WeaponMesh = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName WeaponBone = NAME_None;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FTransform WeaponGrip;
	/** the gallery's name (the HUD's bar shows it) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Title;
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
	/** random_dungeonmagic_level4: the mana a cast takes (0: none; a cast is refused while she has less) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float ManaCost = 0.f;
	/** random_dungeonmagic_level4: its picture among the generator's UIArt (none: the HUD shows its name only) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Icon = NAME_None;
	// ---- random_dungeonmagic_level5: a weapon found in a container (an item of kind Weapon, made for her hero)
	/** its sounds are those of this name ("Player.Hit.<SoundKey>", "Player.Cast.<SoundKey>"...; none: its own Name) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName SoundKey = NAME_None;
	/** blows (or bolts) that land before it breaks (0: it never breaks: the weapons she starts with) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Durability = 0.f;
	/** the weapons table's ratings (1 the worst, 10 the best; 0: none) and its type, for the inventory */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 SpeedRating = 0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 DamageRating = 0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FString WeaponType;
	/** the item it came from (none: one she starts with) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Item = NAME_None;
	// ---- random_dungeonmagic_level5: the spell table (the generator's Spells)
	/** the spell of the generator's Spells it casts (-1: none, a weapon or a plain bolt); its release does what the spell's
	 *  Kind says, the bolt (for the spells that fly) with the spell's effects */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 SpellIndex = -1;
	/** seconds before it can be cast again (0: none) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Cooldown = 0.f;
	/** mistward_castle (docs/improvements2.txt): the slash put on it (the generator's Slashes by name; none: none). Its
	 *  effect plays on every swing (or shot) and its bonus and effect land with every hit */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Slash = NAME_None;
};

/** mistward_castle (docs/improvements2.txt): what a slash does with a hit, besides its bonus damage */
UENUM(BlueprintType)
enum class ERDSlashEffect : uint8
{
	/** Amount more of the hit over Seconds (fire) */
	Burn,
	/** the monster Amount slower for Seconds (frost) */
	Slow,
	/** Amount of hurt over Seconds (poison) */
	Poison,
	/** her speed Amount more for Seconds */
	Swift,
	/** Amount of the hit's damage back to her as hit points */
	Drain,
	/** the monster pushed Amount cm */
	Knockback,
	/** Amount hit points a second for Seconds */
	Regen,
	/** Amount of the blows on her miss for Seconds */
	Evade,
	/** her next blow taken is absorbed (at most once every Seconds) */
	Shield,
	/** Count more monsters within Radius take Amount of the hit */
	Chain,
	/** the monster's blows miss Amount of the time for Seconds */
	Blind,
	/** an arc in front of her: every monster in it slowed Amount for Seconds and pushed Radius cm */
	Tide,
	/** every monster within Radius takes the hit too, and burns Amount more of it over Seconds */
	Inferno,
	/** the hit ignores armour; the monster takes Amount more damage for Seconds */
	Curse,
	/** her attacks Amount faster for Seconds */
	Haste,
	/** Amount of the blows on her are turned back on the attacker for Seconds */
	Deflect,
	/** burning ground within Radius: Amount hurt a second for Seconds */
	Magma,
	/** monsters within Radius pulled to the one she hit and slowed Amount */
	Void,
	/** the monster held for Seconds (once every Radius seconds for each monster) */
	Stun,
	/** each hit one of Burn, Slow, Poison, Drain at random */
	Prismatic
};

/** mistward_castle (docs/improvements2.txt): a weapon flourish a boss gives (the Stylized Slashes pack's effects): it goes on
 *  any weapon her hero can put one on, comes off again and goes on another */
USTRUCT(BlueprintType)
struct FRDSlashDef
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Name;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 Tier = 1;
	/** the swing's effect and the hit's (NS_Slash_<x>, NS_SlashImpact_<x>) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UFXSystemAsset> Fx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UFXSystemAsset> ImpactFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float FxScale = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float ImpactFxScale = 1.f;
	/** its bonus damage on every hit, its damage type's name (the table's), what it does */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Bonus = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Type;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) ERDSlashEffect Effect = ERDSlashEffect::Burn;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Amount = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Seconds = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Radius = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 Count = 0;
	/** the table's line (the inventory shows it) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Text;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FLinearColor Color = FLinearColor(1.f, 0.5f, 0.2f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Icon = NAME_None;
};

/** random_dungeonmagic_level5: the spell table's types; a hero learns the types her card lists (FRDHeroDef::Learns) */
UENUM(BlueprintType)
enum class ERDSpellType : uint8
{
	Offense, Protection, Curse, Summon
};

/** random_dungeonmagic_level5: what a spell does when it is released (each is played by URDCombatComponent::ReleaseSpell) */
UENUM(BlueprintType)
enum class ERDSpellKind : uint8
{
	/** a bolt after the monster she faces: Damage, Splash (cm; a fireball's whole Damage within it), Pierce (on through
	 *  monsters), Slow (a share of their speed for Duration), Burn (Amount of Damage again over Duration, a share Drain
	 *  back to her), Count jumps to the next monster within Radius (chain lightning) */
	Bolt,
	/** an arc in front of her (Reach, Radius the arc in degrees): Damage and a push of Amount cm */
	Lash,
	/** a shield on her that takes the next Count blows whole (or Amount of her hit points, when Amount > 0) for Duration */
	Ward,
	/** her armour's share of a blow up by Amount for Duration */
	Skin,
	/** her poison, weakness and slowness end; none takes hold for Duration */
	Dispel,
	/** a channel for Duration: Damage a second to the monster she faces, Amount of it back to her as hit points */
	Drain,
	/** an area round the target (Radius) for Duration: Damage a second, Slow on the monsters in it */
	Cloud,
	/** monsters lose her for Duration (and do not see her); Amount of their blows miss her; it ends when she attacks */
	Veil,
	/** an area round the target (Radius): monsters take Amount more and deal Amount less for Duration */
	Curse,
	/** up to Count corpses within Reach rise as her allies for Duration */
	Raise,
	/** a zone at her feet (Radius) for Duration: blows on her inside it take Amount less */
	Rune,
	/** she spends Amount of her hit points: a ring of Damage round her (Radius) */
	Nova,
	/** for Duration blows on her are turned back on the attacker (Amount of them; she takes the rest) */
	Mirror,
	/** at once on the monster she faces: Damage */
	Rend,
	/** corpses within Reach of the target (Count at most) burst: Damage within Radius of each */
	Corpse,
	/** a column at the target: Damage within Radius at once, then burning ground (Damage a second) for Duration */
	Pillar,
	/** a rift at the target for Duration: monsters within Radius are pulled toward it, Damage a second */
	Rift,
	/** once within Duration, a blow that would kill her leaves her at Amount of her hit points instead */
	Pact,
	/** a champion fights for her until it falls (one at a time; casting again heals it) */
	Knight,
	/** Count strikes over Duration within Radius of the target, Damage within Splash of each */
	Meteors,
	/** a zone at her feet (Radius) for Duration: no blow hurts her (or her allies) inside it */
	Sanctum,
	/** every monster she can see within Reach: Damage */
	Apocalypse
};

/** random_dungeonmagic_level5: one entry of the spell table (SourceArt/random_dungeon_magic5/spells.json, pipeline/unreal/858).
 *  A tome found in a container teaches it to a hero whose card learns its type; it then joins her weapons as a spell
 *  (FRDWeaponDef::SpellIndex) cast with her own cast clips. */
USTRUCT(BlueprintType)
struct FRDSpellDef
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Name;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 Number = 0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) ERDSpellType Type = ERDSpellType::Offense;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) ERDSpellKind Kind = ERDSpellKind::Bolt;
	/** the table's line (the inventory shows it) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Effect;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Mana = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Cooldown = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Duration = 0.f;
	/** the table's drop chance (a share: the 30 add up to 1): how likely a tome is this spell among those of its tier */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float DropChance = 0.f;
	/** the tier of rooms whose tomes may teach it (by its mana) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 Tier = 1;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Damage = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Reach = 1400.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Radius = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Splash = 170.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Amount = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 Count = 0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Slow = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Burn = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Drain = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bPierce = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float BoltSpeed = 1700.f;
	/** effects (MagicProjectilesVol4 / 5, ToonExplosionVol1 / ToonExplosionsVol2, StylizedShieldsVol1): on her hand while
	 *  she casts, on the bolt, where it strikes (or where the spell lands), over its area while it lasts (fired again every
	 *  AreaEvery seconds when it plays once), on her while it lasts (a shield) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UFXSystemAsset> CastFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UFXSystemAsset> BoltFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UFXSystemAsset> ImpactFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UFXSystemAsset> AreaFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UFXSystemAsset> ShieldFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float CastFxScale = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float BoltFxScale = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float ImpactFxScale = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float AreaFxScale = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float ShieldFxScale = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float AreaEvery = 0.f;
	/** the projectile packs' colours (User.Color01..03), set when bUseColors */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bUseColors = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FLinearColor> Colors;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FLinearColor LightColor = FLinearColor(1.f, 0.45f, 0.12f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float LightIntensity = 0.f;
	/** its sounds: "Player.Charge.<SoundKey>", "Player.Cast.<SoundKey>", "Player.Hit.<SoundKey>" */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName SoundKey = TEXT("Fire");
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Icon = NAME_None;
};

/** random_dungeonmagic_level5: the rings' kinds */
UENUM(BlueprintType)
enum class ERDRingKind : uint8
{
	/** her mana: Amount more of it (spellcasters) */
	Magic,
	/** her hit points: Amount more of them */
	Health,
	/** her ranged weapons' damage: Amount more */
	Dexterity
};

/** random_dungeonmagic_level5: what an anvil breaks a found weapon of these types into (each part Count a tier of the
 *  weapon: the lowest tier its item is found in) */
USTRUCT(BlueprintType)
struct FRDBreakdown
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FString> Types;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FName> Gives;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<int32> PerTier;
};

/** random_dungeonmagic_level5: a found weapon as one hero wields it (her clips for its type, its mesh in her hand) */
USTRUCT(BlueprintType)
struct FRDWeaponFit
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Hero;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FRDWeaponDef Weapon;
};

/** random_dungeonmagic_level5: how far a section (a set of rooms) is from cleared. Its rooms (not the hallway junctions),
 *  its chests and trunks (container keys) and its monsters (by the order they were spawned in) are recorded when it is
 *  first generated; what she did there is kept when it is dropped and generated again. */
USTRUCT(BlueprintType)
struct FRDSectionProgress
{
	GENERATED_BODY()
	UPROPERTY(BlueprintReadOnly) FIntPoint Coord = FIntPoint::ZeroValue;
	UPROPERTY(BlueprintReadOnly) int32 Tier = 1;
	UPROPERTY(BlueprintReadOnly) int32 Rooms = 0;
	UPROPERTY(BlueprintReadOnly) int32 RoomsExplored = 0;
	UPROPERTY(BlueprintReadOnly) TArray<int32> Chests;
	UPROPERTY(BlueprintReadOnly) int32 ChestsLooted = 0;
	UPROPERTY(BlueprintReadOnly) int32 Monsters = 0;
	UPROPERTY(BlueprintReadOnly) TArray<int32> Killed;
	UPROPERTY(BlueprintReadOnly) bool bCleared = false;
	/** where each one she killed lies (by spawn index): a section generated again lays its corpse there */
	UPROPERTY(BlueprintReadOnly) TMap<int32, FTransform> Corpses;
	/** corpses gone for good (burst, or risen and fallen again) */
	UPROPERTY(BlueprintReadOnly) TArray<int32> Consumed;
};

/** random_dungeonmagic_level4: a painted piece of the interface (SourceArt/random_dungeon_magic4/ui_art.json, made on an
 *  image server and cut out by pipeline/blender_numpy/rdm4_ui_*.py, imported by pipeline/unreal/830). Border: how much
 *  of each side (left, top, right, bottom; shares of the picture) is the frame when the piece is stretched to another
 *  shape: the corners keep their size and the edges stretch. Inner: the open inside of a hollow frame (left, top, right,
 *  bottom shares): a bar's fill is drawn there. */
USTRUCT(BlueprintType)
struct FRDUIArt
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UTexture2D> Texture = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FVector4 Border = FVector4(0.0, 0.0, 0.0, 0.0);
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FVector4 Inner = FVector4(0.0, 0.0, 1.0, 1.0);
};

/** random_dungeonmagic_level4: a typeface of the painted interface's lettering (pipeline/blender_numpy/rdm4_fonts.py
 *  fetches it, pipeline/unreal/830 imports it). The HUDs keep it under a role: "title" (Cinzel), "text" (Alegreya),
 *  "label" (Alegreya SC). Size: against the engine's Roboto that the plain HUD draws with, so that the same scale gives
 *  letters as tall (Alegreya's are smaller at the same point size). Lift: how much higher it is drawn (shares of the
 *  engine font's em at that scale) so that its capitals start where Roboto's would: its line has more room above the
 *  capitals than Roboto's, and the HUD's layouts were made for Roboto (the line height reported is Roboto's too). */
USTRUCT(BlueprintType)
struct FRDUIFont
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<class UFontFace> Face = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Size = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Lift = 0.f;
};

/** random_dungeonmagic_level4: what a potion or a food does (random_dungeonmagic_level5: or a set of armour she wears) */
UENUM(BlueprintType)
enum class ERDItemKind : uint8
{
	Healing, Mana, Speed, Food, Armour, Weapon,
	/** random_dungeonmagic_level5: a crafting material (an anvil makes repair items from them) */
	Component,
	/** random_dungeonmagic_level5: mends Amount of an armour set's or a found weapon's full durability (up to full) */
	Repair,
	/** random_dungeonmagic_level5: a ring (RingKind: Amount more mana, hit points or ranged damage while she wears it; one
	 *  of each kind at a time) */
	Ring,
	/** random_dungeonmagic_level5: a tome that teaches its Spell to a hero who learns spells of its type */
	Tome,
	/** mistward_castle: a shield carried in the left hand (WeaponFits: its mesh on her left arm, OffHand fields); Amount
	 *  the share of a blow it takes, Slower the share of her speed, Durability the hurt it can take before it breaks */
	Shield,
	/** mistward_castle: a torch carried in the left hand (WeaponFits: its mesh in her hand); it lights her way */
	Torch,
	/** mistward_castle: a teleport ring (TeleportTier): used, it takes her to the first tier's teleporter, whose pad takes
	 *  her back to the teleporter of that tier */
	Teleport,
	/** mistward_castle (docs/improvements2.txt): a slash (the generator's Slashes by the item's name): used, she chooses the
	 *  weapon it goes on */
	Slash,
	/** mistward_castle (docs/improvements2.txt): a vault's key: F at the vault's door with it opens the vault (used up) */
	Key
};

/** random_dungeonmagic_level5: how heavy a set of armour is; each hero wears only some weights (FRDHeroDef::Wears) */
UENUM(BlueprintType)
enum class ERDArmourWeight : uint8
{
	Light, Medium, Heavy
};

/** random_dungeonmagic_level5: a set of armour made to fit one hero: its meshes, on her skeleton, follow her pose */
USTRUCT(BlueprintType)
struct FRDArmourFit
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Hero;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<TObjectPtr<USkeletalMesh>> Meshes;
};

/** random_dungeonmagic_level4: a potion or a food found in a container. Amount is a share: of her hit points at once
 *  (Healing), of her mana at once (Mana), of her speed for Seconds (Speed), of her hit points every second for Seconds
 *  (Food), of each blow she takes that it takes off while she wears it (Armour: worn, not used up; one set at a time).
 *  Weight: how likely a container holds it against the others (the item table's rarity; 0: only where it is put). */
USTRUCT(BlueprintType)
struct FRDItemDef
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Name;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) ERDItemKind Kind = ERDItemKind::Healing;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Amount = 0.1f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Seconds = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Weight = 1.f;
	/** its picture among the generator's UIArt (none: the HUD shows its name only) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Icon = NAME_None;
	/** armour: the heroes it fits (made for each: SourceArt/summoner3/armour.json, 849-851) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FRDArmourFit> Fits;
	/** armour: a line of what it is (the inventory shows it) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Looks;
	/** armour: light, medium or heavy (a hero wears only the weights her Wears lists) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) ERDArmourWeight ArmourWeight = ERDArmourWeight::Light;
	/** random_dungeonmagic_level5: the tiers of rooms whose containers may hold it (empty: every tier) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<int32> Tiers;
	/** a weapon (kind Weapon): how each hero who can wield it does (none for a hero: she carries it but cannot wield it).
	 *  Amount is its durability. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FRDWeaponFit> WeaponFits;
	/** armour: its full durability (each blow that reaches her takes 1 off; at 0 Amount counts half; 0: it never wears) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Durability = 0.f;
	/** armour: the share of her speed she loses while she wears it */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Slower = 0.f;
	/** armour: the table's ratings (1-10: damage reduction, the lowest to the best; speed, the most slowing to the least)
	 *  and its type (full plate, heavy, medium, light, partial, orc); the inventory shows them */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 DamageRating = 0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 SpeedRating = 0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FString ArmourType;
	/** a container that holds it gives 1 to this many of it (components come in bundles) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 FoundMax = 1;
	/** a ring: its kind */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) ERDRingKind RingKind = ERDRingKind::Magic;
	/** a tome: the spell it teaches (the generator's Spells by name) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Spell = NAME_None;
	/** a weapon: its type in the weapons table (what an anvil breaks it into; mistward_castle: armour and shields too, by
	 *  the breakdown table's types) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FString WeaponType;
	/** mistward_castle: a teleport ring's tier (2 to 5) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 TeleportTier = 0;
};

/** mistward_castle: the kinds of trap */
UENUM(BlueprintType)
enum class ERDTrapKind : uint8
{
	/** mechanical: the floor gives way (she falls in, hurt, held a moment) */
	Pit,
	/** mechanical: darts or arrows from the walls */
	Missiles,
	/** mechanical: stones fall from the ceiling */
	Deadfall,
	/** mechanical: a stone block slams down */
	Crusher,
	/** mechanical: a rope snare holds her */
	Snare,
	/** magical: a rune on the floor bursts */
	Glyph,
	/** magical: a barrier across the way burns and throws her back */
	Ward,
	/** magical: a cloud that hurts and slows her while she stays in it */
	Emanation,
	/** magical: a cursed object (a skull on a plinth): touched, it weakens her */
	Cursed,
	/** complex: a chain of traps one after the other (a snare, then the deadfall, then a glyph) */
	Chain,
	/** complex: the longer she stays the worse it gets (darts, then fire, then the ceiling) */
	Lingering,
	/** a teleport: she is carried off to a room with monsters, or a room of traps */
	Teleport,
	/** directional: a spring plate on a room's way hurls her along it to the room's far end, where monsters wait or a ring
	 *  of glyphs (the list's "directional ... traps", added 2026-10-27) */
	Push
};

/** mistward_castle: one kind of trap (the generator's Traps; pipeline/unreal/86x). Damage is a share of her hit points. */
USTRUCT(BlueprintType)
struct FRDTrapDef
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Name;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) ERDTrapKind Kind = ERDTrapKind::Pit;
	/** what the HUD calls it ("pit trap", "glyph of fire") */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Label;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bMagic = false;
	/** the share of her hit points a strike takes, the radius it is set off within (cm), how long it holds her, burns or
	 *  curses her (s) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Damage = 0.15f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Radius = 110.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Seconds = 2.f;
	/** the first tier of rooms it is set in, and how likely it is against the others */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 MinTier = 1;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Weight = 1.f;
	/** what is seen of it before it goes off (a pressure plate, a rune, a skull; none: nothing) and what it throws or drops
	 *  (a dart, a stone, the crusher's block) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UStaticMesh> Mesh = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FTransform MeshTransform;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UStaticMesh> Missile = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FTransform MissileTransform;
	/** effects: on it while it waits (a rune's glow), when it goes off, where it strikes */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UFXSystemAsset> IdleFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UFXSystemAsset> TriggerFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UFXSystemAsset> HitFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float IdleFxScale = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float TriggerFxScale = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float HitFxScale = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FLinearColor Color = FLinearColor(1.f, 0.4f, 0.1f);
	/** its sounds: "Trap.<SoundKey>.Trigger", "Trap.<SoundKey>.Hit" (none: the generator's Env sounds) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName SoundKey = NAME_None;
};

/** mistward_castle: someone locked in a prison cell (the NPC packs): a mesh and its clips (idle, walking out, thanks) */
USTRUCT(BlueprintType)
struct FRDPrisonerDef
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Name;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<USkeletalMesh> Mesh = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<TObjectPtr<USkeletalMesh>> Parts;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimationAsset> Idle = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimationAsset> Walk = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimationAsset> Thanks = nullptr;
	/** mesh relative to its feet (z) and turned so that it faces +X (yaw) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float MeshZ = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float MeshYaw = -90.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float WalkSpeed = 120.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float WalkClipSpeed = 120.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Title;
};

/** random_dungeonmagic_level5: what a recipe takes of one kind: Count of any of AnyOf together ("wood (any)": hardwood,
 *  timber and wood logs) */
USTRUCT(BlueprintType)
struct FRDRecipePart
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Label;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FName> AnyOf;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 Count = 1;
};

/** random_dungeonmagic_level5: an item an anvil makes, and what it takes */
USTRUCT(BlueprintType)
struct FRDRecipe
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Item;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FRDRecipePart> Parts;
};

/** random_dungeonmagic_level4: one of the characters to choose from (the menu level's ARDHeroSelect shows them; the
 *  dungeon's generator puts the one chosen into its own fields when play begins: ARDDungeonGenerator::ApplyHero). */
USTRUCT(BlueprintType)
struct FRDHeroDef
{
	GENERATED_BODY()
	/** Warrior, Mage, Warlock, Rogue: the menu opens the dungeon with ?Hero=<Name> */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Name;
	/** over the status panel and on the menu */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Title;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TSubclassOf<APawn> PawnClass;
	/** her inventory's weapons (and spells): the first one is drawn when play begins */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FRDWeaponDef> Weapons;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float MaxHealth = 100.f;
	/** mana (0: she has none) and how much comes back a second */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float MaxMana = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float ManaPerSecond = 0.f;
	/** a melee weapon's blows / a ranged weapon's bolts (a spell with a bolt mesh) do this share more */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float MeleeBonus = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float RangedBonus = 0.f;
	/** the Rogue's layout (the wheel or Y switch weapons, B dodges) and her roll; none for the others */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bRogueControls = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimSequenceBase> RollClip = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimSequenceBase> RollBackClip = nullptr;
	/** the HUD's controls panel ("key|what it does"), keyboard and mouse; gamepad */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FString> ControlsKeys;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FString> ControlsPad;
	/** the menu: a line each for her main abilities, what she can wear, the weapons she starts with, a colour of her own */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FString> Abilities;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Armour;
	/** the weights of armour she can wear (empty: none); a set of one of them is worn when a fit was made for her */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<ERDArmourWeight> Wears;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FString StartsWith;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FLinearColor Accent = FLinearColor(1.f, 0.8f, 0.4f);
	/** random_dungeonmagic_level5: the types of spell she learns from tomes (empty: none) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<ERDSpellType> Learns;
	/** random_dungeonmagic_level5: the kinds of ring she can wear */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<ERDRingKind> RingKinds;
	/** random_dungeonmagic_level5 and mistward_castle (the user's of 2026-10-28): a spell that, once she knows it, makes her
	 *  mana pool at least this much (rings no longer add past it): the Mage's Null Sanctum 220 and Apocalypse 300, which cost
	 *  more than the best ring gives (871) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TMap<FName, float> TomeMana;
	/** the Martial Artist (the user's of 2026-10-28, mistward_castle and martial_arts): the share more damage a weapon type
	 *  does in her hands (her knives and daggers: "short blades") */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TMap<FString, float> TypeBonus;
	/** the weapon types a Dexterity ring adds to besides a ranged weapon's bolts (hers: her fists, "unarmed", and her knives;
	 *  never a spell: her chi attacks are spells) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FString> DexterityTypes;
	/** her dash forward (V / the gamepad's X): the clip (in place: the dash carries her); none: no dash */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<UAnimSequenceBase> DashClip = nullptr;
	/** weapons (her chi attacks) she gains UnlockPerBoss at a time, in their order, each time she slays a tier's boss */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FRDWeaponDef> LockedWeapons;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 UnlockPerBoss = 2;
};

UENUM(BlueprintType)
enum class ERDRoomKind : uint8
{
	Hall, Barracks, Prison, Torture, Storeroom, Armory, Kitchen, Library, Chapel, Crypt, Treasury, GuardRoom, Forge, Junction,
	/** mistward_castle (docs/improvements2.txt, the generator's bSpecialRooms): a statue's blessing; fountains that heal, give
	 *  speed, give mana; an arena of waves; a hall of traps with a chest at its end; a vault its key opens; a throne room and
	 *  its usurper */
	Shrine, HealFountain, SpeedFountain, ManaFountain, Arena, TrapGauntlet, Vault, ThroneRoom
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
	/** mistward_castle: a room of another shape than its rectangle: its tiles, row by row (Y, then X), 1 where it has floor
	 *  (empty: the whole rectangle); its shape's name */
	UPROPERTY(BlueprintReadOnly) TArray<uint8> Mask;
	UPROPERTY(BlueprintReadOnly) FString Shape;
	/** a tile of the rectangle (global) is the room's */
	bool HasTile(const FIntPoint& T) const
	{
		if (T.X < Min.X || T.Y < Min.Y || T.X >= Max.X || T.Y >= Max.Y) return false;
		if (Mask.Num() == 0) return true;
		const int32 W = Max.X - Min.X, I = (T.Y - Min.Y) * W + (T.X - Min.X);
		return Mask.IsValidIndex(I) && Mask[I] != 0;
	}
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
