// random_dungeon_level: procedural dungeon. The world is a grid of 252 m sections (84 x 84 tiles of 3 m, the dungeon kits'
// module); each section holds 7 x 7 blocks, one room (or a hallway junction) per block, joined by 3 m hallways along the
// block centre lines (a random spanning tree plus loops: every room is reachable). Hallways leave each section edge at
// fixed rows (block rows 1, 3, 5), so neighbouring sections always join up. The start section (centred on the origin, the
// great hall in its middle) is built in the editor with a fixed seed and saved with the level; in play, when the player
// comes near the edge of the generated dungeon heading outward, the next section is generated (fresh seed each session,
// never saved) with the same reveal effect as random_level (post-process scan wave + border curtain). Doors and containers
// open with F, M shows the full map (the HUD draws a minimap of generated / discovered rooms), monsters wander between rooms.
// random_dungeoncombat_level is the same dungeon with bCombat on: the player gets a URDCombatComponent (hit points, the
// melee weapons of Weapons), the monsters fight. A monster's hit points and damage are the player's hit points and her
// average damage a blow, times the tier of its section (StartMonster* in the start section, RuntimeMonster* in every
// section generated in play) and its kind's factors. bStylizedMap draws the maps as a miniature of the dungeon.
// Blood (URDBloodComponent, made here in play), the monsters' wounds (WoundMaterial) and sound are data on the
// generator too: Sounds maps an occasion to its sound files; everything but the player's own flat sounds is played
// where it happens and fades with its distance to her (the listener's attenuation point is the pawn, not the camera
// behind her); the fires nearest to her get the looping voices (UpdateFireLoops).
// Music and atmosphere (TickMusic) are four flat stereo layers: while she wanders, a track of "Music.Explore" over
// "Atmos.Explore"; when a fight is on (a monster near her is after her, or blows fell a moment ago) they fade out and
// a track of "Music.Combat" comes in from its start over "Atmos.Combat"; CombatMusicHold seconds after the fight the
// wandering pair comes back where it left off. Each fight takes the next battle track.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RDTypes.h"
#include "RDFace.h"
#include "RDWild.h"
#include "RDDungeonGenerator.generated.h"

class ARDSection;
class ARDMonster;
struct FCollisionQueryParams;
class URDCombatComponent;
class URDBloodComponent;
class UFXSystemComponent;
class UStaticMesh;
class USoundAttenuation;
class UAudioComponent;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class UPostProcessComponent;
class UNiagaraSystem;
class UHierarchicalInstancedStaticMeshComponent;

UCLASS()
class CLAUDE_UE5_API ARDDungeonGenerator : public AActor
{
	GENERATED_BODY()

public:
	ARDDungeonGenerator();

	// ---- layout
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") float TileSize = 300.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") int32 SectionTiles = 84;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") int32 BlockTiles = 12;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") float RoomHeight = 600.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") float CorridorHeight = 400.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") int32 StartSeed = 20261011;
	/** generate the next section once the player is this close to the edge of the generated dungeon (moving toward it) */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") float TriggerDistance = 4500.f;
	/** any missing section closer than this is generated whatever her direction */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") float SafetyDistance = 1800.f;
	/** runtime sections farther than this many sections are removed (0 = keep all); the map remembers them */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") int32 UnloadSectionDistance = 2;
	/** session seed for runtime sections (0 = random each play) */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") int32 FixedSessionSeed = 0;
	/** runtime sections are furnished over several frames: time budget per frame */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") float FrameBudgetMs = 6.f;
	/** share of rooms with a wandering monster */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") float MonsterCoverage = 0.4f;
	/** generation follows this actor instead of the player pawn when set */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Layout") TObjectPtr<AActor> TrackedActor;
	/** cinematics: doors open by themselves for the tracked actor within this distance (0 = off; the player uses F) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Layout") float TrackedAutoDoorDistance = 0.f;
	/** a safety net: the player that drops this far below the floor (through a gap in the dungeon) is put back where she
	 *  last stood on the ground (0 = off) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Layout") float FallResetDepth = 400.f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Layout") int32 FallResets = 0;
	/** monsters block pawns (off for cinematics: a monster never stalls the scripted walk) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Layout") bool bMonstersBlockPawns = true;

	// ---- fighting (random_dungeoncombat_level)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") bool bCombat = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float PlayerMaxHealth = 100.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") TArray<FRDWeaponDef> Weapons;
	/** the average monster of the start section against the player: hit points (x hers) and damage (x her average blow) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float StartMonsterHealth = 0.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float StartMonsterDamage = 0.45f;
	/** the same for the sections generated in play: on a par with her */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float RuntimeMonsterHealth = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float RuntimeMonsterDamage = 1.f;
	/** a monster notices her within this distance (cm) when there is a way to her, and gives up beyond the other */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float AggroDistance = 1000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float LoseDistance = 2200.f;
	/** a chasing monster moves at its walking speed times this, at most MaxChaseSpeed (she runs at 377 cm/s) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float ChaseSpeedScale = 1.6f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float MaxChaseSpeed = 290.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float CorpseSeconds = 8.f;
	/** random_dungeonmagic_level5: the dead stay where they fell (no sinking away; a section generated again lays its
	 *  corpses where they lay) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") bool bKeepCorpses = false;
	/** random_dungeonmagic_level5: per tier of rooms (index 0: tier 1), what the average monster's hit points and damage are
	 *  against MonsterReferenceHealth / Blow, its speed and the time between its attacks against its kind's own, and how
	 *  strong its ability is (empty: the start / runtime factors) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") TArray<float> TierHealth;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") TArray<float> TierDamage;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") TArray<float> TierSpeed;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") TArray<float> TierAttackInterval;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") TArray<float> TierAbility;
	/** a tier's value of one of those lists (Def when the list has none) */
	static float TierValue(const TArray<float>& List, int32 Tier, float Def) { return List.Num() > 0 ? List[FMath::Clamp(Tier - 1, 0, List.Num() - 1)] : Def; }
	/** the monster kinds a section spawns: those of its tier (with MaxTier and kinds that have tiers), else all */
	void MonsterKindsFor(FIntPoint Section, TArray<int32>& Out) const;
	/** her hit points come back at RegenPerSecond once she has not been hurt for RegenDelay seconds */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float RegenDelay = 6.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float RegenPerSecond = 4.f;
	/** at 0 hit points she lies this long, then stands in the middle of the start section again */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float RespawnSeconds = 3.5f;
	/** the maps as a miniature of the dungeon (floors by room, walls, doors, chests, torches) instead of plain rectangles */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") bool bStylizedMap = false;
	/** the maps as tactical maps (ARDHUD): the minimap is dark monochrome terrain with feathered edges under bright
	 *  markers (monsters red, the strongest orange, unopened chests and trunks gold stars, hallway exits into sections not yet generated cyan diamonds); the big map is a see-through
	 *  wireframe of the walls, doorways and passages centred on her, over the game, which goes on under it */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon") bool bTacticalMaps = false;
	/** the HUD's status panel: her name over it, the keys under it */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") FString PlayerTitle = TEXT("JRPG-FEM5");
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") FString ControlsHint = TEXT("left mouse  attack      1  2  3  weapon");
	/** the magic levels' controls (URDCombatComponent): gamepad RB the weapon in her hand, LB the spell, LT (R) walk / run,
	 *  X opens (as F does), Back (View) opens and closes the big map (as M does); the HUD shows ControlsKeys or ControlsPad, whichever device is in use, in the upper left */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") bool bCasterControls = false;
	/** the HUD's controls panel, a line each: "key|what it does" (keyboard and mouse; gamepad) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") TArray<FString> ControlsKeys;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") TArray<FString> ControlsPad;
	/** random_dungeonmagic_level3 (with bCasterControls): she switches between her weapons (1 / 2, the mouse wheel, the
	 *  gamepad's Y) and the left mouse button (RB) uses the one in her hands, spell or not; B (the gamepad's B) rolls */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") bool bRogueControls = false;
	/** the roll: her clip (in place: the roll moves her) toward the way she is moving, or RollBackClip backward when she
	 *  stands; how far it takes her (cm), the pause after one before the next (s), and the part of it (shares of its
	 *  length) in which blows miss her */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") TObjectPtr<UAnimSequenceBase> RollClip = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") TObjectPtr<UAnimSequenceBase> RollBackClip = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float RollDistance = 420.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float RollCooldown = 0.25f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") FVector2D RollDodge = FVector2D(0.05f, 0.75f);
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 MonstersKilled = 0;
	/** a monster's hit points and damage scale with these instead of her hit points and her average blow (0: hers). With
	 *  heroes to choose (random_dungeonmagic_level4) the monsters stay the same whoever she is, so the Warrior's hit
	 *  points and blows and the Mage's frailty count. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float MonsterReferenceHealth = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float MonsterReferenceBlow = 0.f;

	// ---- random_dungeonmagic_level4: the characters to choose from (the menu level, ARDHeroSelect, opens the level with
	// ?Hero=<Name>; ARDHeroGameMode spawns her pawn). When play begins the chosen one's weapons, hit points, mana, bonuses,
	// controls and roll become the generator's own (Weapons, PlayerMaxHealth, ...): the rest of the game reads those.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Heroes") TArray<FRDHeroDef> Heroes;
	/** the one played when the level is opened without ?Hero= and without its menu (MenuLevel, rd.HeroMenu 0) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Heroes") FName DefaultHero;
	/** the menu that chooses the hero: the level played without ?Hero= (Play in the editor) opens it first, and it opens the
	 *  level again with ?Hero=<her name>. Empty: no menu. The console variable rd.HeroMenu 0 skips it (the scripted tests and
	 *  the reel's renders play the DefaultHero or switch heroes themselves). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Heroes") FString MenuLevel;
	/** play began without a hero and the menu is being opened: the dungeon does not start */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Heroes") bool bOpeningMenu = false;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Heroes") FName CurrentHero;
	/** hers (ApplyHero): mana, mana a second, the share more a melee blow / a ranged bolt does */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Heroes") float PlayerMaxMana = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Heroes") float ManaPerSecond = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Heroes") float MeleeBonus = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Heroes") float RangedBonus = 0.f;
	const FRDHeroDef* FindHero(FName Name) const;
	// ---- the Martial Artist (the user's of 2026-10-28; RD/RDMartial.cpp)
	/** hers (ApplyHero): the dash's clip; how far it carries her (at most: it stops short of the monster ahead), the way
	 *  ahead a monster is looked for to dash at, the pause after one */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Martial") TObjectPtr<UAnimSequenceBase> DashClip = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Martial") float DashDistance = 500.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Martial") float DashSeek = 900.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Martial") float DashCooldown = 0.8f;
	/** martial_arts: every locked weapon of her hero (her chi attacks) is hers from the start */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Martial") bool bUnlockAll = false;
	/** martial_arts (the user's of 2026-10-28, to try her moves): no mana is ever taken (her pool stays full) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Martial") bool bInfiniteMana = false;
	/** martial_arts: a chi attack with no monster within its range is made all the same (its bolt flies straight ahead and
	 *  bursts at the end of its range); off, it is refused and costs nothing */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Martial") bool bChiWithoutTarget = false;
	/** the list of 2026-11-11: her chi attacks are hers to make with no monster near, at no mana (on every map; the castle
	 *  refused them until then): one with a monster within its range takes its mana as before */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Martial") bool bChiFreeWithoutTarget = true;
	/** tests: chi attacks made with no monster in range (no mana taken) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Martial") int32 ChiFreeMade = 0;
	// ---- the list of 2026-11-11 (RDList11.cpp): the town's guards fight a monster that comes into the town
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List11") bool bTownGuardsFight = true;
	/** their blows (918 guards: the Dwarf pack's warrior attacks on the NPC packs' Manny skeleton) and each one's hit time (s) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List11") TArray<TObjectPtr<UAnimSequenceBase>> TownGuardStrikes;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List11") TArray<float> TownGuardHitTimes;
	/** how far a guard sees a monster in its town (cm), how far from its post it follows one, how fast it runs, how fast its
	 *  blows play, its blow as a share of the monster's whole health (so a few guards bring down a monster of any tier), its
	 *  health as so many of the monster's blows, and how long a beaten guard rests at its post */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List11") float TownGuardSight = 2500.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List11") float TownGuardLeash = 6000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List11") float TownGuardRunSpeed = 380.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List11") float TownGuardStrikeRate = 1.4f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List11") float TownGuardBlowShare = 0.12f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List11") float TownGuardBlowsToBeat = 14.f;
	/** a guard that sees another fighting this near joins it (cm) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List11") float TownGuardCall = 4000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List11") float TownGuardRest = 20.f;
	/** the guards fighting now (the monsters may take one of them for their foe) */
	TArray<TWeakObjectPtr<class ARDTownsfolk>> FightingGuards;
	/** what the HUD shows for her weapon Index (its Label or its Name: FRDWeaponDef::Shown, which the HUD draws) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List11") FString GetWeaponShown(int32 Index) const { return Weapons.IsValidIndex(Index) ? Weapons[Index].Shown() : FString(); }
	/** tests: the guards fighting now, and every guard's "<title>|<role>|<fighting 0/1>|<fights>|<strikes>|<hits>|<damage>|<blows
	 *  taken>|<health>|<sword drawn 0/1>|<x>|<y>|<z>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List11") int32 CountFightingGuards() const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List11") TArray<FString> GetGuardLines() const;
	/** tests: a monster of the wilds' kinds put at a place (in a town too), hunting her as an ambush's does; -> it */
	/** (the third phase's test: bHunt false spawns it not hunting, to see whether it notices her by itself) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List11") class ARDMonster* SpawnTestAmbusher(FVector At, int32 Tier = 1, bool bHunt = true);
	// ---- the list of 2026-11-11's third phase (RDList11c.cpp): the Warlock's curses
	/** Mark of the Hunted's one monster (the HUD marks it through walls) */
	TWeakObjectPtr<class ARDMonster> HuntedMark;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List11") class ARDMonster* GetHuntedMark() const;
	/** tests: a hit on a monster from her of a kind ("weapon", a spell's element, or none: a burn's tick), as the game lands it;
	 *  what it took */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List11") float TestHit11(class ARDMonster* M, float Amount, FName Element);
	/** the element of the spell whose hurt is being dealt now (none: a weapon's blow, a slash, a burn); Brittle Bones and
	 *  Elemental Ruin read it */
	FName HitElement = NAME_None;
	int32 KinGroupNext = 0;
	/** a crit's chance on Mark of the Hunted and Brittle Bones (the game has no crits otherwise): her blows twice as hard */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List11") float CurseCritChance = 0.1f;
	/** tests: Curse of Greed's gold more and things given */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List11") int32 GreedGold = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List11") int32 GreedThings = 0;
	/** whether her hero learns the spell: its type on her card, and it is no other hero's own (OnlyHeroes) */
	bool HeroCanLearnSpell(const FRDSpellDef& S) const;
	// ---- the list of 2026-11-11: the Escape menu's Gameplay page (kept in GameUserSettings.ini's [RandomDungeon.Options])
	/** her things at her death: kept on her (true), or left in a pile where she fell (bDropOnDeath, the game's way until now) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List11") bool bKeepItemsOnDeath = false;
	/** 0 easy, 1 fair (the game as it was), 2 difficult, 3 hell: the monsters' hit points and blows times DifficultyScale (the
	 *  user's 0.6 / 1 / 1.5 / 2.5); in hell HellCountMul as many and HellEliteShare of them elites (EliteHealthMul, EliteDamageMul:
	 *  the HUD's elite mark is 1.25 times its tier's hit points). For the monsters met from the change on */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List11") int32 Difficulty = 1;
	static constexpr int32 NumDifficulties = 4;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List11") TArray<float> DifficultyScale = { 0.6f, 1.f, 1.5f, 2.5f };
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List11") float HellCountMul = 1.25f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List11") float HellEliteShare = 0.2f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List11") float EliteHealthMul = 1.6f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List11") float EliteDamageMul = 1.25f;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List11") void SetKeepItemsOnDeath(bool bKeep);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List11") void SetDifficulty(int32 InDifficulty);
	static FString DifficultyName(int32 D);
	/** the difficulty's factor on a monster's hit points and blows, and on how many come */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List11") float DifficultyMul() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List11") float DifficultyCountMul() const;
	/** a count of monsters by the difficulty (hell: a quarter more, rounded up) */
	int32 DifficultyCount(int32 N) const { return N <= 0 ? N : FMath::CeilToInt(N * DifficultyCountMul() - 1e-3f); }
	/** while a summon or another ally of hers is made: the difficulty is not put on it */
	bool bSpawningAlly = false;
	/** tests: the monsters made elites by hell, and those the difficulty scaled */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List11") int32 ElitesMade = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List11") int32 DifficultyScaled = 0;
	// ---- the list of 2026-11-11's console commands (RDConsoleCmds.cpp, RDList11.cpp)
	/** rd.Tier: her tier set by hand (GrowthTier; her slashes, chi attacks, later abilities and learned spells to that tier);
	 *  0: the game's own. Kept in the game instance for the levels she goes to */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List11") FString ConsoleSetTier(int32 N);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List11") int32 ConsoleTierNow() const;
	/** rd.Pois: every place of the map shown on it (found or not) and listed, the small points of interest within ConsolePoiKm
	 *  of her too; rd.Pois hide: the map back to what she has found herself. -> how many listed */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List11") int32 ConsoleShowPlaces(bool bShow);
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List11") bool bWildShowAllPlaces = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List11") float ConsolePoiKm = 3.f;
	TArray<FRDWildPlace> ConsolePlaces;
	/** "<n>|<name>|<kind>|<x m>|<y m>|<found 0/1>|<km from her>" (the last listing) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List11") TArray<FString> GetConsolePlaceLines() const;
	/** tests: how many places she has found (rd.Pois must not change it) and how many the maps draw now */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List11") int32 GetWildFoundCount() const { return WildFound.Num(); }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List11") int32 GetWildKnownPlaceCount() const { TArray<FRDWildPlace> P; WildKnownPlaces(P); return P.Num(); }
	/** rd.GoToPoi <number | name>: to a place of the listing (a town by fast travel) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List11") bool ConsoleGoToPlace(const FString& What);
	/** rd.RevealMap: the whole map drawn as seen (the wilds' fog, the dungeons' tactical maps); rd.RevealMap off: as she has
	 *  seen it. What she has seen is not changed (nor saved) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List11") void SetMapRevealAll(bool bAll);
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List11") bool bMapRevealAll = false;
	/** the locked weapons gained so far (her hero's LockedWeapons, in order) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Martial") int32 WeaponsUnlocked = 0;
	/** her hero's weapons at the start (her card's, and with bUnlockAll all her locked ones) */
	void StartWeaponsOf(const FRDHeroDef& H, TArray<FRDWeaponDef>& Out) const;
	/** the next Count of her hero's locked weapons join hers (a tier's boss slain; tests): how many did */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Martial") int32 UnlockHeroWeapons(int32 Count);
	/** the share more a weapon type does in her hands (TypeBonus), and whether a Dexterity ring adds to it */
	float TypeBonusOf(const FString& Type) const;
	bool DexterityBoosts(const FString& Type) const;
	/** martial_arts: one room only. The start section plans its great hall alone, OneRoomTiles a side, with no doors, no
	 *  hallways and no other section; OneRoomMonsters of tier 1 stand in it, one more OneRoomRespawn seconds after one falls */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Martial") bool bOneRoom = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Martial") int32 OneRoomTiles = 8;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Martial") int32 OneRoomMonsters = 3;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Martial") float OneRoomRespawn = 4.f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Martial") int32 OneRoomSpawned = 0;
	void TickOneRoom(float Dt);
	TArray<TWeakObjectPtr<ARDMonster>> OneRoomLive;
	float OneRoomNext = 0.f;
	/** why the hero in play cannot wear that armour ("" when she can): its weight is not one she wears (the hero's Wears),
	 *  or no fit was made for her. Label: the item's name as the messages write it. */
	FString ArmourRefusal(const FRDItemDef& It, const FString& Label) const;
	/** the hero of this play: ?Hero= of the level's URL, else DefaultHero, else the first */
	FName ChosenHero() const;
	/** puts a hero's data into the generator's fields (her pawn must be hers: see SwitchHero) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Heroes") bool ApplyHero(FName Name);
	/** tests: in play, another hero takes her place (her pawn is replaced where she stands, with full hit points) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Heroes") bool SwitchHero(FName Name);

	// ---- random_dungeonmagic_level4: potions and food in the containers
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Items") TArray<FRDItemDef> Items;
	/** a container of the start section (the first tier of rooms) holds one item, picked by the items' weights, found when
	 *  she opens it the first time; the sections generated in play hold none yet. The pick comes from the session seed,
	 *  the section and the container (a stream of its own: the play's streams are not touched). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Items") bool bStartLoot = false;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Items") int32 FindItem(FName Name) const;
	/** a container was opened (by her): its item goes into her inventory */
	void OnContainerOpened(ARDSection* Section, int32 Index, const FVector& At);
	/** what she found last (HUD) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Items") FName LastFound;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Items") int32 ItemsFound = 0;
	TSet<FIntVector> LootedContainers;
	float LastFoundTime = -100.f;
	/** the first item a container of a section holds (NAME_None: none) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Items") FName LootOf(FIntPoint Section, int32 Index) const;
	/** random_dungeonmagic_level5: how many items a container may hold (each holds 1 to this many, picked by the
	 *  weights; level 4: 1) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Items") int32 MaxItemsPerContainer = 1;
	/** random_dungeonmagic_level5: items put in the containers of the start room (the great hall she starts in), one to
	 *  each container in turn (more to one when there are more items than containers); they come first in a container
	 *  and count toward MaxItemsPerContainer */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Items") TArray<FName> StartRoomItems;
	/** everything a container holds, in the order found */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Items") TArray<FName> LootListOf(FIntPoint Section, int32 Index) const;
	/** the containers of the start room (start section indices, in their order; tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Items") TArray<int32> GetStartRoomContainers() const;
	/** everything the last container she opened held (HUD) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Items") TArray<FName> LastFoundList;
	/** the containers looted this run (section, container key): a container gives what it holds once, whatever happens to
	 *  its section afterwards; RestartPlay empties it (a new run) */
	void MarkContainerLooted(FIntPoint Section, int32 Key) { LootedContainers.Add(FIntVector(Section.X, Section.Y, Key)); UpdateProgress(Section); }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Items") bool IsContainerLooted(FIntPoint Section, int32 Key) const { return LootedContainers.Contains(FIntVector(Section.X, Section.Y, Key)); }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Items") int32 GetNumLooted() const { return LootedContainers.Num(); }
	/** tests: drop a generated section and queue it again (as when she walks far away and comes back) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") bool ReloadSection(FIntPoint Coord);
	/** random_dungeonmagic_level5: the containers of every section hold items, not only the start section's: each picked by
	 *  the items' weights among those whose Tiers have the section's tier */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Items") bool bLootAllSections = false;
	/** how many of an item a container gives (1 to the item's FoundMax; a hash of the container and the pick, no stream) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Items") int32 LootCountOf(FIntPoint Section, int32 Index, int32 Pick) const;
	/** the same, given the container's list (LootListOf) already made */
	int32 LootCountIn(const TArray<FName>& List, FIntPoint Section, int32 Index, int32 Pick) const;
	/** random_dungeonmagic_level5: the chance that a container holds anything (then it holds 1 to MaxItemsPerContainer);
	 *  the start room's StartRoomItems are there whatever it says. A hash of the container decides (no stream). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Items") float ContainerLootChance = 1.f;
	/** containers opened that held nothing (each says so: "Empty: nothing inside") */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Items") int32 ContainersEmpty = 0;
	/** whether a container's draw came up (tests: the share of containers that hold something) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Items") bool ContainerHoldsLoot(FIntPoint Section, int32 Index) const;

	// ---- random_dungeonmagic_level5: the spell table, tomes and rings (pipeline/unreal/858)
	/** every spell a tome may teach (the hero's own spells point into it too: FRDWeaponDef::Spell) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Spells") TArray<FRDSpellDef> Spells;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Spells") int32 FindSpell(FName Name) const;
	/** the spell a tome of a container teaches, picked by the spells' drop chances among those of the section's tier (a
	 *  hash of the container and the pick: the container's other picks stay as they were) */
	FName TomeSpellOf(FIntPoint Section, int32 Index, int32 Pick) const;
	/** the item a found tome is in her inventory under ("Tome of <spell>") */
	static FName TomeItemName(FName Spell) { return FName(*FString::Printf(TEXT("Tome of %s"), *Spell.ToString())); }
	/** the spell's weapon for the hero in play: her cast clips (those of her first spell) with the spell's numbers */
	bool MakeSpellWeapon(int32 SpellIndex, FRDWeaponDef& Out) const;
	/** a hero learns spells of this type (her card's Learns) */
	bool HeroLearns(ERDSpellType Type) const;
	bool HeroWearsRing(ERDRingKind Kind) const;
	/** a monster kind that comes to her side for the Summon Abyssal Knight spell (the Monsters' name) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Spells") FName KnightMonster;
	/** its hit points and damage against a monster of the last tier */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Spells") float KnightStrength = 0.6f;

	// ---- random_dungeonmagic_level5: found weapons broken down at an anvil into crafting materials
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Crafting") TArray<FRDBreakdown> Breakdowns;
	/** what a weapon of this type and tier breaks into (false: none) */
	bool BreakdownOf(const FString& Type, int32 Tier, TArray<FName>& Items, TArray<int32>& Counts) const;

	// ---- random_dungeonmagic_level5: her allies (raised corpses, the summoned champion): monsters that fight on her side
	UPROPERTY(Transient, BlueprintReadOnly, Category = "RandomDungeon|Spells") TArray<TObjectPtr<ARDMonster>> Allies;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Spells") TArray<ARDMonster*> GetAllies() const;
	/** corpses (dead monsters of the generated sections) within Radius of At, nearest first */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Spells") TArray<ARDMonster*> GetCorpsesNear(FVector At, float Radius) const;
	/** a corpse is gone for good (burst, or risen and fallen again): it is not laid again when its section is */
	void ConsumeCorpse(ARDMonster* Corpse);
	/** a dead monster rises on her side for Seconds (0: until it falls) with HealthShare of its hit points */
	bool RaiseAlly(ARDMonster* Corpse, float Seconds, float HealthShare);
	/** a monster of the named kind on her side, near her (the Knight spell; one at a time: casting again heals it) */
	ARDMonster* SummonAlly(FName Kind, FVector At, float Strength);

	// ---- random_dungeonmagic_level5: crafting at anvils. The furniture's anvils (AnvilPiece: a forge's, an armory's, and
	// one more in every section that has none when bAnvilEverySection is on); F (X) at one opens her crafting panel
	// (URDCombatComponent::SetCraftingOpen), which makes the Recipes' items from what she carries.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Crafting") TArray<FRDRecipe> Recipes;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Crafting") bool bAnvilEverySection = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Crafting") FName AnvilPiece = TEXT("Anvil");
	/** how near (cm) she must stand to use an anvil */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Crafting") float AnvilReach = 260.f;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Crafting") int32 FindRecipe(FName Item) const;
	/** the nearest anvil within MaxDistance in the room From is in (false: none) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Crafting") bool FindNearestAnvil(FVector From, float MaxDistance, FVector& At) const;
	/** every anvil of the generated sections (tests, the reel) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Crafting") TArray<FVector> GetAllAnvils() const;

	// ---- random_dungeonmagic_level5: tiers of rooms. A section's tier is its ring round the start section plus one (the
	// start section 1, the 8 round it 2, the 16 round those 3...). A tier T > 1 is generated only once every section of
	// tier T - 1 is cleared (every room explored, every chest and trunk looted, every monster spawned there killed): tier 2
	// once the start section is. Nothing beyond MaxTier is generated. A hallway that leads to a section not to be generated is
	// sealed where it leaves its section: a grating (SealPiece, twice across the hallway) while the tier is shut, a wall
	// (EndPiece) at the end of the dungeon, both with a blocker as tall as the hallway.
	/** the last tier (0: no tiers, the dungeon goes on for ever) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Tiers") int32 MaxTier = 0;
	/** (the rebalance to tier 25, the list of 2026-11-08b's fifth phase) this level's tiers in the game's: its tier T is the game's
	 *  DungeonTierBase + T, at most DungeonTierCap (0: none): Mistward Castle 0 (1-5), Vel Morrath 5, The War Engine 10, the Sewers 15,
	 *  Kethrys Spire 20 (21-25), Heaven 25 (26-30: the list of 2026-11-12's sixth phase; 24 capped at 25 before). The monsters'
	 *  strength, the loot's tiers and the hero's growth go by it */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Tiers") int32 DungeonTierBase = 0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Tiers") int32 DungeonTierCap = 0;
	/** the game's last tier (Heaven's last: the list of 2026-11-12's sixth phase; 25 before), the town's prices and gold run to it */
	static constexpr int32 GameTierMax = RDGameTierMax;
	/** past the game's tier 5: the hero's hit points and mana grow by TierGrowthHealth a tier, her power (spells, her own weapons,
	 *  chi, summons) by TierGrowthPower, as the monsters' (TierHealth / TierDamage past 5, 910) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Tiers") float TierGrowthHealth = 1.09f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Tiers") float TierGrowthPower = 1.12f;
	/** the game's tier of this level's tier T */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Tiers") int32 GlobalTier(int32 Tier) const;
	/** the deepest game's tier opened in any dungeon of the chain (or this level's): the town's and the wilds' prices and growth */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Tiers") int32 GameGlobalTier() const;
	/** the tier the hero grows by: this level's open tier in the game's tiers, at least the deepest she has opened anywhere */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Tiers") int32 GrowthTier() const;
	/** a container whose loot the rules put first (a guarded ring, a vault's or a gauntlet's things, a vault's key): its index as
	 *  LootListOf takes it (the tests tell the random draw from it) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Tiers") bool HasForcedLoot(FIntPoint Section, int32 Index) const;
	// ---- the secondary abilities (the list of 2026-11-08b's sixth phase; RDSecondary.cpp; 911 from SourceArt/balance/secondary.json)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Secondary") TArray<FRDSecondaryDef> Secondaries;
	/** the Angel Token (an item of kind Token) and the wilderness's two materials it is made from: the feathers the wilds'
	 *  monsters drop (that share of the time), the stones at the wild places of those kinds (one each, once a game) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Secondary") FName AngelTokenItem;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Secondary") FName SeraphFeatherItem;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Secondary") float SeraphFeatherChance = 0.45f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Secondary") FName HallowedStoneItem;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Secondary") TArray<FString> HallowedKinds;
	const FRDSecondaryDef* FindSecondary(FName Name) const { return Secondaries.FindByPredicate([Name](const FRDSecondaryDef& D) { return D.Name == Name; }); }
	/** the list of 2026-11-12's seventh phase: the Rogue's arts' props in the world (the monsters' decoys among them) and the shared
	 *  meshes they lay (a disc for the acid's pool, a plane for a crosshair, a cylinder for the hook's rope, its material), 925 */
	TArray<TWeakObjectPtr<class ARDArtProp>> ArtProps;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Rogue12") TObjectPtr<UStaticMesh> ArtDisc = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Rogue12") TObjectPtr<UStaticMesh> ArtPlane = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Rogue12") TObjectPtr<UStaticMesh> ArtCylinder = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Rogue12") TObjectPtr<UMaterialInterface> ArtRopeMaterial = nullptr;
	/** the item that teaches a spell or an art (a tome, or the Rogue's manual: an item of kind Tome whose Spell it is) */
	FName TomeItemOf(FName Spell) const;
	/** tests: the arts' props in the world: "<kind>|<art>|<x>|<y>|<z>|<reached>|<decoy>|<seconds left>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Rogue12") TArray<FString> GetArtPropLines() const;
	/** every art's prop taken away (a restart; tests between trials) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Rogue12") void ClearArtProps();
	/** her rank's number of a secondary ability (1 when not learned: the Summoner's multipliers) */
	float SecondaryMul(FName Ability, int32 Which = 0) const;
	/** her summons' strength again (a rank of her minions' health, damage or frenzy raised) */
	void RefreshSummonsSecondary();
	/** the soul harvest at a monster's death near her */
	void SecondaryOnKill(ARDMonster* Monster);
	/** the wilderness's water at a point: its surface's height (cm); false: no water there */
	bool WildWaterZAt(FVector At, float& OutZ) const;
	/** a wild place's Hallowed Stone laid (its kind among HallowedKinds, not taken yet this game) */
	void LayHallowedStone(class ARDWildChunk* C, const struct FRDWildPlace& P);
	/** a tier table's value at this level's tier T (the game's tier: GlobalTier) */
	float TierValueAt(const TArray<float>& List, int32 Tier, float Def) const { return TierValue(List, GlobalTier(Tier), Def); }
	/** a growth by tier: 1 + PerTier a tier up to tier 5, times Past5 a tier beyond it */
	static float GrowthAt(float PerTier, int32 Tier, float Past5) { return (1.f + PerTier * (FMath::Min(Tier, 5) - 1)) * FMath::Pow(Past5, (float)FMath::Max(Tier - 5, 0)); }
	/** the hero's abilities earned in the later dungeons whose last boss has fallen (FRDHeroDef::LaterWeapons), into her weapons;
	 *  with Announce a message for each new one. Returns how many were added */
	int32 GrantLaterWeapons(bool bAnnounce);
	/** this level's place in the chain of dungeons (0 Mistward Castle; -1 none) */
	int32 ChainIndexHere() const;
	/** a level's tier T in the game's tiers by a base and a cap (0: none): GlobalTier's and the chain's (GameGlobalTier) one rule */
	static int32 MapTier(int32 Tier, int32 Base, int32 Cap) { return Cap > 0 ? FMath::Min(Tier + Base, Cap) : Tier + Base; }
	/** the level's tier that maps to a game's tier (at least 1): a summon grown to the game's tier is spawned at it */
	int32 LevelTierOf(int32 GameTier) const { return FMath::Max(1, GameTier - DungeonTierBase); }
	/** an item found in this level's tier T: no tiers, or the game's tier of T among them (every reader of an item's Tiers) */
	bool ItemOfTier(const FRDItemDef& It, int32 Tier) const { return It.Tiers.Num() == 0 || It.Tiers.Contains(GlobalTier(Tier)); }
	/** the kinds the wilds meet at a game's tier (their wild bands): their factors' plain mean (the wilds pick a kind evenly);
	 *  false when no kind has a band holding it */
	bool MeanWildFactors(float& Health, float& Damage, int32 Tier) const;
	/** GameGlobalTier kept for the frame it was read in while the tiers opened here stay as many (it walks the chain and the game
	 *  instance's dungeons; growth reads it at every blow and every redraw; a tier opening reads it in the same frame) */
	mutable int32 CachedGameTier = 0, CachedGameTierOpened = -1;
	mutable uint64 CachedGameTierFrame = MAX_uint64;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Tiers") FName SealPiece = TEXT("CellFrame");
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Tiers") FName EndPiece = TEXT("Wall_Corr");
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Tiers") int32 TierOf(FIntPoint Section) const { return FMath::Max(FMath::Abs(Section.X), FMath::Abs(Section.Y)) + 1; }
	/** Vel Morrath's catacombs (the user's of 2026-11-06: "each tier is a floor below the last, reached by stairs down from the
	 *  floor above"): every tier's sets of rooms TierFloorDepth lower than the tier before's, and each hallway across the border
	 *  from a shallower tier a stair up to it over its StairTiles nearest the border (the set's edge rooms kept that far in) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Catacombs") bool bTierFloors = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Catacombs") float TierFloorDepth = 450.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Catacombs") int32 StairTiles = 4;
	/** a set of rooms' floor height (0, or its tier's depth with bTierFloors) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Catacombs") float SectionFloorZ(FIntPoint Section) const { return bTierFloors ? -TierFloorDepth * (TierOf(Section) - 1) : 0.f; }
	/** sections in a tier: 1, 8, 16, 24... */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Tiers") int32 TierSize(int32 Tier) const { return Tier <= 1 ? 1 : 8 * (Tier - 1); }
	/** its sections may be generated (tier 1 always; another once the tier before it is cleared; none past MaxTier) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Tiers") bool IsTierOpen(int32 Tier) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Tiers") bool IsSectionAllowed(FIntPoint Section) const;
	/** sections of a tier cleared */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Tiers") int32 GetTierCleared(int32 Tier) const;
	/** the highest tier open now */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Tiers") int32 GetOpenTiers() const;
	/** what she did in a section (false: it was never generated) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Tiers") bool GetSectionProgress(FIntPoint Section, FRDSectionProgress& Out) const;
	/** tests and the reel: a generated section as if cleared (its rooms explored, its chests and trunks looted, its
	 *  monsters killed), but for the LeaveMonsters monsters nearest to Near (left alive: the section is not cleared then) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Tiers") bool DebugClearSection(FIntPoint Section, int32 LeaveMonsters = 0, FVector Near = FVector::ZeroVector);
	/** a hallway end of Section toward its neighbour Next is sealed (0: open, 1: a shut tier, 2: the end of the dungeon) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Tiers") int32 GetSealKind(FIntPoint Section, FIntPoint Next) const;
	/** what a seal near her says ("" none near) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Tiers") FString DescribeSealNear(FVector From, float MaxDistance = 450.f) const;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Tiers") TMap<FIntPoint, FRDSectionProgress> Progress;
	/** a section was generated (or activated): its rooms, chests and trunks, monsters are recorded the first time */
	void RecordSection(ARDSection* S);
	bool IsMonsterKilled(FIntPoint Section, int32 SpawnIndex) const;
	/** where a monster she killed lies (none: no corpse kept, or it is gone for good) */
	const FTransform* CorpseOf(FIntPoint S, int32 I) const { const FRDSectionProgress* P = Progress.Find(S); return P && !P->Consumed.Contains(I) ? P->Corpses.Find(I) : nullptr; }
	/** counts what she did in a section again, and announces a set cleared or a tier opened */
	void UpdateProgress(FIntPoint Section);
	/** "SET CLEARED" / "TIER 3 IS OPEN" (HUD) and when */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Tiers") FString TierNotice;
	float TierNoticeTime = -100.f;
	/** seals on every generated section as the tiers are now */
	void RefreshSeals();

	// ---- mistward_castle (pipeline/unreal/863-): the rules of 2026-10-26 (docs/improvements.txt). Every one is a switch of
	// its own here, off on the other levels.
	/** the dungeon's name (the minimap's label, the notices) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") FString DungeonTitle;
	/** frames a second in the upper left, over the controls */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") bool bShowFps = false;
	/** the anvil's lists in alphabetical order */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") bool bAlphabeticalCrafting = false;
	/** a key held in the inventory, the crafting panel or the repair list walks it (after 0.35 s, a line every 0.08 s) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") bool bKeyRepeat = false;
	/** the mouse in the inventory and the repair list (the user's of 2026-10-27): the pointer is shown while it is open, the
	 *  row under it is chosen when it moves, a click on the chosen row (or a double click) uses it, the wheel scrolls the list */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") bool bMouseUI = false;
	/** the player controller this ticks after (bMouseUI) */
	TWeakObjectPtr<APlayerController> TickAfterController;
	/** tests: input sent the way a keyboard, mouse or gamepad sends it (into Slate, then the viewport: RDInputSim); "" when
	 *  sent, else why not. A pixel is the HUD canvas's. */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward") FString SlateKey(FKey Key, bool bDown);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward") FString SlateMouseMove(FVector2D Pixel);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward") FString SlateMouseButton(FVector2D Pixel, FKey Button, bool bDown);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward") FString SlateWheel(FVector2D Pixel, float Delta);
	/** tests: the editor's windows over the game's view hidden while a test sends it input (their titles), and shown again */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward") FString SlateClearView();
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward") int32 SlateRestoreView();
	/** the same with no play world (the test's driver after play stops): RDDungeonGenerator.slate_restore_any_view() */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward") static int32 SlateRestoreAnyView();
	/** tests: the live particles of every Niagara effect in this world within Radius of At (a trap's effects are spawned in
	 *  the world, not on their set of rooms) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward") int32 GetParticlesNear(FVector At, float Radius) const;
	/** the tiers' rings to guard, put once the frame's container has given what it held (a ring found as the tier opened is no duplicate) */
	TArray<int32> PendingRingTiers;
	/** Brokenspire: tiers open from an earlier visit to the castle whose boss / guarded ring wait for a room of the tier
	 *  before she has seen (tried once a second) */
	TArray<int32> RestoredBossTiers, RestoredRingTiers;
	float RestoredTryAt = 0.f;
	/** a container once opened stays open (and is built open when its section is generated again) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") bool bContainersStayOpen = false;
	/** furniture never overlaps (beds, chests), and nothing stands in front of a container */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") bool bTidyFurniture = false;
	/** rooms of other shapes (round, octagonal, polygonal, triangular, L, T, U) and heights (a dome, a stepped pyramid, a
	 *  high hall); the share of the rooms that get one */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") bool bShapedRooms = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") float ShapedRoomShare = 0.6f;
	/** the look of each tier (index 0: tier 1): a theme's pieces are the Pieces "<Theme>.<Name>" (the others the plain
	 *  ones); "Mixed": each set of rooms one of MixedThemes, by a hash of where it is */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") TArray<FName> TierThemes;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") TArray<FName> MixedThemes;
	/** the theme of a set of rooms (NAME_None: the plain pieces) */
	FName ThemeOf(FIntPoint Section) const;
	/** tests: ThemeOf as text ("None": the plain pieces) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward") FString GetThemeName(FIntPoint Section) const { return ThemeOf(Section).ToString(); }
	/** a tier opens when the one before it has this share of its rooms explored, of its monsters killed and of its chests
	 *  and trunks looted, each over all of its sets of rooms (1: every set cleared, the rule of 2026-10-24) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") float TierOpenShare = 1.f;
	/** what there is to do in a tier: rooms (explored / all), monsters (killed / all), chests and trunks (looted / all);
	 *  false while a set of it has not been counted yet */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward") bool GetTierTally(int32 Tier, FIntVector& Done, FIntVector& All) const;
	/** found armour is kept set by set (several of one kind), and an anvil breaks armour down as it does weapons */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") bool bArmourStacks = false;
	/** what she starts with in her left hand (an item of kind Shield; her hero must have its fit), worn when play begins */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") TMap<FName, FName> StartShield;
	/** the torch in her hand: its flame, its light */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") TObjectPtr<UFXSystemAsset> TorchFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") float TorchFxScale = 0.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") FVector TorchFlame = FVector(0, 0, 60);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") float TorchLight = 120.f;
	/** when she falls everything she found drops where she fell, a pile she can take up again (F) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") bool bDropOnDeath = false;
	/** the pile: its effect (Loot Drops Vol. 2), the material its pictures are drawn with (a texture parameter "Icon") */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") TObjectPtr<UFXSystemAsset> LootPileFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") float LootPileFxScale = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") TObjectPtr<UMaterialInterface> IconMaterial = nullptr;
	UPROPERTY(Transient, BlueprintReadOnly, Category = "RandomDungeon|Mistward") TArray<TObjectPtr<class ARDLootPile>> LootPiles;
	/** her things where she fell (the loot pile) */
	ARDLootPile* DropLoot(const FVector& At, const TArray<FName>& Things, const TArray<float>& Wear);
	/** takes up the pile nearest to her within Reach (false: none) */
	bool TakeLootNear(const FVector& From, float Reach);
	/** a tier opens (2 to 5): if she found neither potency ring of the tier before (her kind of ring), one is put in a
	 *  container of a room she explored there, marked on the map and guarded by GuardCount monsters of the new tier */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") bool bRingGuards = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") int32 GuardCount = 4;
	/** a tier opens: a boss and 3 to 6 monsters of the new tier wait in a room she explored (not the one she is in) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") bool bBossEncounters = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") FIntPoint BossMinions = FIntPoint(3, 6);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") float BossHealth = 3.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") float BossDamage = 1.6f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") float BossScale = 1.35f;
	/** a monster of a kind (the Monsters' index) at a place, as strong as tier Tier's times the multipliers; it belongs to the
	 *  set of rooms it stands in but is not one of its planned monsters (no SpawnIndex) */
	ARDMonster* SpawnMonsterKind(int32 Kind, const FVector& At, int32 Tier, float HealthMul = 1.f, float DamageMul = 1.f, float ScaleMul = 1.f, const FString& Title = FString());
	/** tests: the same by the kind's name */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward") ARDMonster* SpawnMonsterNamed(FName Kind, FVector At, int32 Tier, float HealthMul = 1.f, float DamageMul = 1.f, float ScaleMul = 1.f);
	/** what a tier's opening set waiting for her: "<kind>|<x>|<y>|<z>|<label>|<alive>" (boss, guard), the forced ring */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward") TArray<FString> GetEncounterLines() const;
	/** the tiers opened so far (2 to 5), in order */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward") TArray<int32> TiersOpened;
	/** a container's items put there by the rules (the guarded ring): (section, key) -> items */
	TMap<FIntVector, TArray<FName>> ForcedLoot;
	/** traps (RDTraps.cpp): their kinds, the share of rooms and hallway stretches with one, how far the Rogue sees them */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") TArray<FRDTrapDef> Traps;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") float TrapRoomShare = 0.3f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") float TrapHallShare = 0.12f;
	/** the heroes who see traps (within TrapSenseRange) and can disarm them (F, DisarmSeconds; DisarmChance it works) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") TArray<FName> TrapFinders;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") float TrapSenseRange = 800.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") float DisarmSeconds = 1.6f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") float DisarmChance = 0.85f;
	bool HeroFindsTraps() const { return TrapFinders.Contains(CurrentHero); }
	/** traps set off, struck her, disarmed (tests, the reel) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward") int32 TrapsTriggered = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward") int32 TrapsDisarmed = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward") int32 TrapHits = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward") FString LastTrap;
	/** tests: log what the traps' tick sees (her section, the sets ticked, the nearest trap and why it does not go off) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") bool bLogTraps = false;
	float TrapLogTime = -100.f;
	/** the traps of the generated sets: "<section x>|<y>|<index>|<name>|<kind>|<x>|<y>|<z>|<state>|<seen>" (state 0 set,
	 *  1 going off, 2 spent, 3 disarmed) (tests, HUD) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward") TArray<FString> GetTrapLines() const;
	/** tests: a trap set off now (as if she stepped on it) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward") bool TriggerTrap(FIntPoint Section, int32 Index);
	/** the disarming going on (0..1; -1 none) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward") float GetDisarmProgress() const;
	/** teleporters: the pad (mesh, effect) in the great hall and in each tier's first set of rooms with its ring on it */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") bool bTeleporters = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") TObjectPtr<UStaticMesh> PadMesh = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") FTransform PadTransform;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") TObjectPtr<UFXSystemAsset> PadFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") float PadFxScale = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") TObjectPtr<UFXSystemAsset> TeleportFx = nullptr;
	/** the ring that lies on a pad */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") TObjectPtr<UStaticMesh> TeleportRingMesh = nullptr;
	/** where each tier's pad is: tier -> its set of rooms */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward") TMap<int32, FIntPoint> PadSections;
	/** the first tier's pad: the tier F takes her to (G picks another) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward") int32 PadChoice = 0;
	/** what F does at a pad near her (taking the ring, teleporting); "" none */
	FString UsePadNear(const FVector& From);
	FString DescribePadNear(const FVector& From) const;
	/** the pads: tier -> where (world, on the floor); a tier's ring lies on its pad until she takes it */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward") TMap<int32, FVector> Pads;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward") TArray<int32> PadRingsTaken;
	UPROPERTY(Transient) TMap<int32, TObjectPtr<class ARDTeleporter>> PadActors;
	/** a tier's teleport ring item (by TeleportTier) */
	FName TeleportRingOf(int32 Tier) const;
	/** she is carried to a tier's pad (generating its set of rooms first) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward") bool TeleportToTier(int32 Tier);
	/** the pad nearest her within Reach (0: none) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward") int32 PadNear(FVector From, float Reach = 220.f) const;
	/** the first tier's pad: the tiers it can take her to (their rings in her pack), and the one chosen (cycles with F) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward") TArray<int32> GetPadDestinations() const;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward") int32 Teleports = 0;
	/** prison cells with someone in them: who (PrisonerDefs), the share of cells taken, the share of those a monster; what a
	 *  prisoner set free gives (an item of these, by the tier) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") TArray<FRDPrisonerDef> PrisonerDefs;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") float CellOccupied = 0.6f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") float CellMonsterShare = 0.35f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward") TArray<FName> PrisonerRewards;
	/** cells she opened (section, cell) and what came of it (tests): prisoners freed, cell monsters that broke out */
	TSet<FIntVector> CellsOpened;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward") int32 PrisonersFreed = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward") int32 CellBreakouts = 0;
	/** the frame rate the HUD shows (smoothed) */
	float FpsSmoothed = 0.f;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward") float GetFps() const { return FpsSmoothed; }
	/** monsters' height: each kind's lowest drawn point against the floor as it stands now (tests, the fix stage) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward") TArray<FString> MeasureMonsterHeights();

	// ---- the user's third list (docs/improvements2.txt, 2026-10-27): mistward_castle and random_dungeonmagic_level5. Every rule
	// a switch of its own, off on the other levels (RDMistward2.cpp)
	/** a trap she has seen (the Rogue) shows a red outline: its plate or rune outlined, a red ring on the floor at its reach */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") bool bTrapOutline = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") TObjectPtr<UMaterialInterface> TrapOutlineMaterial = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") TObjectPtr<UStaticMesh> TrapRingMesh = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") TObjectPtr<UMaterialInterface> TrapRingMaterial = nullptr;
	/** a seen trap's red glow (candelas; 0: none) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") float TrapGlowCandelas = 60.f;
	/** the inventory in tabs (weapons, armour, potions and food, crafting, magic: Q / E, LB / RB, or a click on a tab), copies of a
	 *  found weapon with the same durability (and slash) on one line, the anvil's break-down list says how many are left */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") bool bInventoryTabs = false;
	/** ten quick slots on the bar: 1 to 0 draw one, the D-pad left / right step through them; in the inventory a weapon or
	 *  spell goes into a slot with its number (the gamepad: Y into the slot the D-pad left / right chose; the mouse: right click) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") bool bQuickSlots = false;
	/** H (or the inventory's armour tab) shows or hides the worn set's helmet: the sections of its mesh her head bone moves */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") bool bHelmetToggle = false;
	/** a hero of BlockHeroes holds the right mouse button or LB to block with the shield in her hand: BlockShare more of a blow
	 *  taken, BlockSlow of her speed lost, the shield worn BlockWear times as fast */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") bool bShieldBlock = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") TArray<FName> BlockHeroes;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") float BlockShare = 0.3f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") float BlockSlow = 0.5f;
	/** the list of 2026-11-07 (docs/improvements8.txt): over 0, while she blocks she walks only ahead or back, at this speed
	 *  (cm/s) whether she walks or runs (BlockSlow then unused), back at BlockBackShare of it; the stick's side turns her at
	 *  BlockTurnRate (deg/s). 0: the third list's block (BlockSlow off her speed, any way) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") float BlockMoveSpeed = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") float BlockBackShare = 0.8f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") float BlockTurnRate = 120.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") float BlockWear = 5.f;
	/** a clip and the moment of it held while she blocks (her shield raised; none: no pose) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") TMap<FName, TObjectPtr<UAnimSequenceBase>> BlockClip;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") TMap<FName, float> BlockClipTime;
	bool HeroBlocks() const { return bShieldBlock && BlockHeroes.Contains(CurrentHero); }
	/** what her hero starts with is hers for good: the weapons she starts with and the shield of StartShield never break and stay
	 *  with her when she falls */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") bool bKeepStartGear = false;
	/** the armories' weapon tables carry weapons and shields of the room's tier: F takes one up, and it is gone from the table */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") bool bWeaponPickups = false;
	/** pickups taken (section, index): they stay gone */
	TSet<FIntVector> TakenPickups;
	/** what an armory table's place holds: a weapon or shield found in the set's tier, by a hash of the set and the place */
	FName PickupItemFor(FIntPoint Section, int32 Index) const;
	/** a pickup item's mesh (its first fit's weapon, or a shield's off-hand mesh) */
	UStaticMesh* PickupMeshOf(FName Item) const;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward2") int32 PickupsTaken = 0;
	/** the special rooms (ERDRoomKind::Shrine ...): a share of the rooms of a set (not the great hall, a prison, a junction),
	 *  from a stream of their own; their effects and how long a blessing or a fountain's draught lasts */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") bool bSpecialRooms = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") float SpecialRoomShare = 0.2f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") TObjectPtr<UFXSystemAsset> ShrineFx = nullptr;
	/** each fountain's glow while it has water: healing, speed, mana */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") TObjectPtr<UFXSystemAsset> HealFountainFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") TObjectPtr<UFXSystemAsset> SpeedFountainFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") TObjectPtr<UFXSystemAsset> ManaFountainFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") TObjectPtr<UFXSystemAsset> BlessFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") float BlessSeconds = 90.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") float FountainSpeed = 0.3f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") float FountainSpeedSeconds = 45.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") float FountainHeal = 0.6f;
	/** the arena's waves (each 2 + its tier monsters of the tier, Waves of them) and the vault's key (an item of kind Key) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") int32 ArenaWaves = 3;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") FName VaultKeyItem = TEXT("Vault Key");
	/** fixtures used (section, room): a shrine's blessing, a fountain's draught (once each); arenas won; vaults opened */
	TSet<FIntVector> UsedFixtures, ArenasWon, VaultsOpened;
	/** the arena going on: its set, its room, the wave, its monsters; -1 none */
	FIntPoint ArenaSection = FIntPoint::ZeroValue;
	int32 ArenaRoom = -1, ArenaWave = 0;
	TArray<TWeakObjectPtr<ARDMonster>> ArenaMonsters;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward2") int32 ArenaWavesBeaten = 0;
	/** what she has from the special rooms (tests): blessings, draughts, arenas won, vaults opened, usurpers slain */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward2") TMap<FString, int32> RoomUses;
	void TickArena(float Dt);
	/** a room of a set is shut to her (an arena fighting, a vault she has no key for) */
	bool IsRoomLocked(FIntPoint Section, int32 Room) const;
	/** the special rooms of the generated sets: "<section x>|<y>|<room>|<kind>|<x>|<y>|<z>|<used / won / opened>" (tests, the reel) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") TArray<FString> GetSpecialRoomLines() const;
	/** the pickups of the generated sets: "<section x>|<y>|<index>|<item>|<x>|<y>|<z>|<taken>" (tests, the reel) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") TArray<FString> GetPickupLines() const;
	/** F at a fixture (a shrine, a fountain), a pickup or a vault's door near her: what it did ("" none near) */
	FString UseSpecialNear(const FVector& From);
	FString DescribeSpecialNear(const FVector& From) const;
	/** tests: the arena of a room begun now (as if she stepped in) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward2") bool StartArena(FIntPoint Section, int32 Room);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") int32 GetArenaWave() const { return ArenaRoom >= 0 ? ArenaWave : -1; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") int32 GetArenaLeft() const;
	/** slashes (the boss's reward): the table, the heroes who put them on weapons, the pack's effects warmed up in the editor */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") bool bBossSlashes = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") TArray<FRDSlashDef> Slashes;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") TArray<FName> SlashHeroes;
	int32 FindSlash(FName Name) const { for (int32 I = 0; I < Slashes.Num(); ++I) if (Slashes[I].Name == Name) return I; return -1; }
	bool HeroSlashes() const { return bBossSlashes && SlashHeroes.Contains(CurrentHero); }
	/** a boss slain: a slash of its tier, chosen from the session's own stream (the one given, when her hero takes slashes) */
	FName GiveBossSlash(int32 Tier, const FVector& At);
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward2") TArray<FName> SlashesGiven;
	FRandomStream SlashR;

	// ---- mistward_castle, the user's list of 2026-10-30 (docs/improvements3.txt, pipeline/unreal/875; RD/RDMistward3.cpp)
	/** monsters are harvested when they die: parts float over the corpse (a loot pile, bHarvest) until she takes them (F).
	 *  Each kill: one essence of the tiers up to its own (its own tier's EssenceOwnTier of the time, else one of the tiers
	 *  below, evenly), its family's part HarvestPartChance of the time (when the family has one in its tier), one of HarvestAny
	 *  HarvestAnyChance of the time; a boss or a usurper BossEssences essences and BossParts parts, an arena won the same.
	 *  The draws are hashes of the session seed and the count of harvests (no stream of the play's) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward3") bool bHarvest = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward3") TArray<FName> Essences;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward3") float EssenceOwnTier = 0.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward3") TArray<FRDHarvestPart> HarvestParts;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward3") float HarvestPartChance = 0.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward3") TArray<FName> HarvestAny;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward3") float HarvestAnyChance = 0.4f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward3") int32 BossEssences = 3;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward3") int32 BossParts = 2;
	/** the pile's light by the tier of the monster (1 to 5) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward3") TArray<FLinearColor> HarvestTints;
	/** piles harvested, and the draws made (the next harvest's hash) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward3") int32 Harvests = 0;
	int32 HarvestRolls = 0;
	/** what a monster of this kind and tier gives (Big: a boss, a usurper, an arena won), draw number Roll (tests: the
	 *  recipes a tier's monsters make possible) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward3") TArray<FName> HarvestOf(FName Kind, int32 Tier, bool bBig, int32 Roll) const;
	/** a harvest laid where a monster fell (or an arena's middle): a pile of its things, its light by the tier */
	ARDLootPile* DropHarvest(const FVector& At, const TArray<FName>& Things, int32 Tier);
	void HarvestKill(ARDMonster* Monster, bool bBig);
	/** the anvil offers a recipe only once its tier is open; a scroll's only to a hero who reads scrolls of its spell's type */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward3") bool bRecipeTiers = false;
	/** the list of 2026-11-10: the heroes who brew healing and mana potions at the anvil (empty: everyone; 914 sets the Mage and the
	 *  Martial Artist on every map of the game) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") TArray<FName> PotionBrewers;
	/** the highest tier open (1 before any other opens; MaxTier 0: every recipe's) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward3") int32 GetHighestOpenTier() const;
	/** why the anvil does not offer it ("" when it does) */
	FString RecipeRefusal(const FRDRecipe& Rc) const;
	/** a hero reads scrolls of this type (her card's ScrollTypes) */
	bool HeroReadsScroll(ERDSpellType Type) const;
	/** rings and the torch break down at an anvil too (the breakdown table's "ring" and "torch") */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward3") bool bBreakAnyGear = false;
	/** the Summoner's summons: one of Kind at her side, as strong as a monster of its own tier, tagged with the spell */
	ARDMonster* SummonKindAlly(FName Kind, FVector At, FName Spell);
	/** her allies brought by this spell, alive */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward3") int32 CountSummoned(FName Spell) const;
	/** the name of the monster a Summon spell calls, as the HUD writes it (its gallery title) */
	FString SummonTitleOf(const FRDSpellDef& S) const;
	/** the list of 2026-11-20 (item 4): of a summoning's minions standing, the one with the least share of its hit points under its
	 *  whole (none: nullptr); taken away (no corpse, no kill) */
	ARDMonster* MostHurtSummon15(FName Spell) const;
	void DismissAlly15(ARDMonster* A);
	/** a kind's title (the table's, else its name) */
	FString KindTitle15(FName Kind) const;
	/** the kinds of a summoning's minions standing (each once); none: the kind she would call */
	FString StandingTitles15(FName Spell) const;
	/** tests and reels (a card says so): tiers 2 to UpTo open now, as if each tier before had reached its share (with
	 *  bEncounters each one's boss and guarded ring are set too); how many opened */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward3") int32 DebugOpenTiers(int32 UpTo, bool bEncounters);

	// ---- mistward_castle, the user's list of 2026-10-31 (RDMistward4.cpp; pipeline/unreal/878): each a switch, off on the
	// other levels (random_dungeonmagic_level5 keeps its Escape menu, maps and HUD as they were)
	/** the Escape menu in two pages: Resume, Options, Choose another hero, Quit; Options holds the volumes, the controls hint
	 *  on or off, a resolution and a display mode (applied by Apply, kept in the game's user settings) and Back */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward4") bool bOptionsMenu = false;
	/** her allies keep apart: a summon is called to a spot nobody stands on, and they step away from each other (and from
	 *  her) as they follow her, wait and fight */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward4") bool bAllySpacing = false;
	/** the HUD lists her summoned allies by kind: how many of how many she may lead, each one's hit points */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward4") bool bSummonPanel = false;
	/** her allies are marked on the minimap and the big map (a green ring) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward4") bool bAllyMarkers = false;
	/** the upper left controls panel is shown (the Options page's switch; kept in the game's user settings) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward4") bool IsControlsHintShown() const { return bControlsShown; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward4") void SetControlsHintShown(bool bShow);
	/** the list of 2026-11-10: the quest window (her quests taken and ready, with their progress), on or off from the Options page */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List10") bool IsQuestWindowShown() const { return bQuestWindowShown; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List10") void SetQuestWindowShown(bool bShow);
	bool bQuestWindowShown = true;
	/** the list of 2026-11-10: the Save page's drop-down: the save to save over (empty: a new one by its name), and a save's name */
	UPROPERTY(BlueprintReadWrite, Category = "RandomDungeon|List10") FString SaveOverSlot;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List10") FString SaveNameOf(const FString& Slot) const;
	/** the Escape menu's page (0 the main one, 1 Options) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward4") int32 GetMenuPage() const { return MenuPage; }
	/** the resolutions the Options page offers (the common ones no larger than the screen), "1920x1080" each */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward4") TArray<FString> GetResolutionChoices() const;	/** the display settings chosen on the page (not applied yet) and what Apply did ("applied", or why not) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward4") FIntPoint PendingResolution = FIntPoint::ZeroValue;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward4") int32 PendingWindowMode = 1;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward4") FString LastApplied;
	/** Apply: the chosen resolution and display mode into the game's user settings, applied and saved (in the editor saved
	 *  only: play in the editor does not own its window) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward4") bool ApplyDisplaySettings();
	/** a spot for a new ally of Radius near From: along Facing first, then round her (of each pair of ways the one toward
	 *  Prefer first, those behind Prefer last); clear of walls (a sweep from her) and of every ally standing (their capsules
	 *  and RD4AllyGap); false: none clear, OutAt the roomiest */
	bool FindAllySpot(const FVector& From, const FVector& Facing, float Radius, const AActor* Ignore, FVector& OutAt, const FVector& Prefer = FVector::ZeroVector) const;
	// ---- the list of 2026-11-20's second phase (items 2, 3, 9, 30; RDList15.cpp)
	// (each off by default, set on the maps she summons on by 934 allies (PR #94's review: the other levels, level 5's raised dead
	// among them, stay as they were))
	/** her allies stop her (and she them); they still pass each other and the monsters */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bAllySolid15 = false;
	/** an ally she presses toward steps aside */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bAllyYield15 = false;
	/** the arena's doors shut: her allies outside the room come in beside her */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bArenaAllies15 = false;
	/** the wilds: her summons answer out there (the wilds' section, open ground) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bWildSummons15 = false;
	/** the list of 2026-11-20 (item 14): a scroll her hero can read goes on the quick bar, read by it (934 quick) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bQuickScrolls15 = false;
	// ---- the list of 2026-11-20's fourth phase (items 5, 6, 7, 8, 11; RDList15c.cpp), each set on the game's maps by 934 dungeon
	/** a bread oven in the start set's great hall, by its anvil (item 5) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bStartOven15 = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") FName OvenPiece15 = TEXT("BreadOven");
	/** the ovens, the alchemist's and librarian's tables and the forges marked on the dungeon's maps and their key (item 6) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bStationMarks15 = false;
	/** the big map zooms (item 8): the wheel, + and -, the right stick's up and down, between these */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bMapZoom15 = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float MapZoomMin15 = 0.4f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float MapZoomMax15 = 4.f;
	/** a library's bookshelves have doors, open once searched (item 7): the leaves (934 shelves), their hinges in the piece's frame
	 *  (x in front of its middle, y each side), how far they swing */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bShelfDoors15 = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TObjectPtr<UStaticMesh> ShelfDoorL15;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TObjectPtr<UStaticMesh> ShelfDoorR15;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") FVector2D ShelfDoorHinge15 = FVector2D(18.58f, 66.f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float ShelfDoorOpenDeg15 = 105.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float ShelfDoorSwingSeconds15 = 0.7f;
	/** the zoom a big map's keys ask for this frame (the wheel, + and -, the right stick's up and down): its factor (1 none); the
	 *  town's and the dungeon's maps both read it */
	float ReadMapZoomInput15(APlayerController* PC, float Dt) const;
	/** a test's: "<n>|<i>:<at x>:<at y>:<yaw>:<searched>:<left yaw>:<right yaw>|..." the shelves of a set and their doors */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List15") FString GetShelfDoors15(FIntPoint Section) const;
	/** a test's: the pews of a set's chapels: "<room>|<altar x>|<altar y>|<pew x>:<pew y>:<yaw>;..." per chapel */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List15") TArray<FString> GetChapelPews15(FIntPoint Section) const;
	/** a test's: the big map as last drawn: its pixels a cm, the view's middle (x, y) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") FVector GetMapScale15() const { return FVector(MapXK, MapXVw.X, MapXVw.Y); }
	// ---- the list of 2026-11-20's fifth phase (items 10, 12, 15, 16, 17, 19; RDList15d.cpp), set by 934 items
	/** blessed rune stones (item 12): a share of rooms gets one, from a stream of its own after the other traps (their places kept) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bBlessedStones15 = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float BlessedShare15 = 0.08f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float BlessedSeconds15 = 60.f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List15") int32 BlessedTouched15 = 0;
	/** what she takes that is not a potion sounds as gear (Player.Loot.Gear: a thud), potions as before (item 15) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bGearThud15 = false;
	/** the sound set her last taking played (a test's) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List15") FName LastLootSound15;
	/** the ankh shows only the chests and trunks not looted (item 16: not the traps) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bAnkhChestsOnly15 = false;
	/** the torch and the ankh burn down while held lit (their Durability, seconds) and the repair items restore them (item 17) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bLightBurn15 = false;
	/** at a teleporter the pad's right stick pressed (R3) does what G does (item 19); the prompts name the device's key */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bPadTripButton15 = false;
	/** the sound set for taking these things: gear's unless every one is a potion */
	FName LootSound15(const TArray<FName>& Things) const;
	/** G, or R3 on the pad, pressed this frame (a teleporter's choice); the key's name as the prompt shows it */
	bool TripKeyPressed15(const APlayerController* PC) const;
	FString TripKeyName15() const;
	/** a test's: a pile of these things dropped at At (F takes it) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List15") bool DebugDropLoot15(FVector At, const TArray<FName>& Things);
	// ---- the list of 2026-11-20's sixth phase (items 1, 20, 21, 22; RDList15e.cpp), set on brokenspire by 934 town
	/** a pen's animals keep apart (item 1: the cows walked through each other); each pen's animals, by the pen's middle */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bPenApart15 = false;
	TMap<FIntPoint, TArray<TWeakObjectPtr<class ARDTownAnimal>>> PenMates15;
	uint32 PenPrune15 = 0;
	/** a quest's "boss" goal counts Mistward Castle's tiers whose boss she has slain (item 20: one slain before the quest was taken
	 *  counts) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bBossGoalCastle15 = false;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") int32 CastleBossesSlain15() const;
	/** a test's: a counter of the game set; a quest's state taken off (back to offered) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List15") void DebugSetCounter15(const FString& Key, int32 Value);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List15") void DebugForgetQuest15(FName Id);
	/** the town maps show the functional buildings' symbols and a key, not their words (item 21) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bTownSymbols15 = false;
	/** the hearths burn (item 22: the kit's fireplace had flat flame cards that never moved, and its effect, P_TorchFire, drew nothing
	 *  there): HearthFx15 at each hearth's floor (once a place), the cards hidden (934 town points "Fireplace" at a copy without them;
	 *  a saved section's old ones take HearthHideMat15 in their flame slot in play) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bHearth15 = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TObjectPtr<class UNiagaraSystem> HearthFx15 = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TObjectPtr<class UMaterialInterface> HearthHideMat15 = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float HearthFxScale15 = 1.f;
	/** a hearth's fire at its floor (At), made once a place (a section laid again and a saved one's pass ask twice); the component */
	class UNiagaraComponent* SpawnHearth15(USceneComponent* Parent, const FVector& At);
	/** a test's: the hearth fires made ("x|y|z|active") within Range of At */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List15") TArray<FString> GetHearthFires15(FVector At, float Range) const;
	TArray<TWeakObjectPtr<class UNiagaraComponent>> HearthFires15;
	uint32 HearthPrune15 = 0;
	/** the wilds' hearths crackle (item 22: their fire was seen, never heard) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bWildHearthSound15 = false;
	/** a test's: the hearths of the chunks within Range of At ("x|y|z" each) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List15") TArray<FString> GetWildHearths15(FVector At, float Range) const;
	/** allies brought into an arena (a test's count) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List15") int32 ArenaAlliesBrought15 = 0;
	/** the arena's allies brought in beside her; the count */
	int32 GatherAlliesInRoom15(ARDSection* S, int32 Room);
	/** an ally's section where it stands: a set of rooms, else the wilds' (open ground); in the wilds, the ground under a spot */
	void PlaceAllySection15(ARDMonster* A);
	bool WildGroundAt15(const FVector& At, float FeetZ, float Rad, float Half, FVector& OutGround) const;
	/** her allies added to a query's ignored actors (a sweep of hers that passes them: the ride's, the flash's) */
	void IgnoreAllies15(FCollisionQueryParams& Q) const;
	/** a test's: "<n>|<i>:<name>:<x>:<y>:<z>:<yields>:<open>:<foe>|..." her allies now */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List15") FString GetAllies15() const;
	/** a display setting asked on the command line (-RDApplyDisplay=<width>x<height>x<mode>, mode 0 fullscreen, 1 windowed
	 *  fullscreen, 2 windowed): set and applied as Apply does (the packaged game's check of Apply); and -RDMarkFile=<path>:
	 *  "castle|<map>|<hero>" written there (a packaged game's test knows it reached the castle) */
	void ApplyDisplayFromCommandLine();
	/** the list of 2026-11-11: the smallest the game's window may be dragged to (a packaged game's): 960 x 540 of the screen's
	 *  pixels inside, its frame added; set by the castle's and the menu's start, after Apply, and whenever its scaling changes */
	static void ApplyWindowLimits();
	/** set it again when the window's scaling, frame or window changed (checked once a second; the menu's and the levels' ticks) */
	static void KeepWindowLimits();
	/** -RDMarkFile=<path>: where a packaged game's test reads where the game got ("castle|<map>|<hero>", "town|<name>|<hero>") */
	void WriteTestMark(const FString& Kind, const FString& Where) const;
	/** the list of 2026-11-20's eighteenth phase: the packaged game's runs of the wilds (-RDTownGo=horse, village, cavetower) */
	void TickGo15(APawn* P);
	/** the nearest landmark tower's site within Ring of the 6 km squares round a point (metres): the landmark laid, the treasure maps' landmark, the package's run */
	bool NearestTowerSite15(const FVector2D& FromM, int32 Ring, FVector2D& SiteM, double& DistM) const;
	/** the list of 2026-11-22's first phase (RDList16.cpp): -RDPerf=<file>: the frame rate measured in every city (its square and a
	 *  street) and every biome (its nearest site to Brokenspire), each settled 20 s and measured 15 s, one line a place */
	void TickPerf16(APawn* P);
	struct FPerf16Place { FString Kind, Name; FVector2D SiteM = FVector2D::ZeroVector; TArray<FVector2D> Alts; float Hour = 12.f; bool bFixed = false; FVector At = FVector::ZeroVector; float Yaw = 0.f; };
	TArray<FPerf16Place> Perf16Places;
	/** -RDPerfPlaces=<file>: an earlier run's "place|..." lines, replayed exactly (kind|name|hour as the key) */
	TMap<FString, FPerf16Place> Perf16Replay;
	FString Perf16File, Perf16Shots;
	int32 Perf16Index = -1, Perf16Stage = 0;
	float Perf16T = 0.f, Perf16Ready = 0.f;
	bool bPerf16Read = false;
	TArray<float> Perf16Frames;
	double Perf16Game = 0.0, Perf16Draw = 0.0, Perf16Rhi = 0.0, Perf16Gpu = 0.0;
	FVector Perf16From = FVector::ZeroVector, Perf16Last = FVector::ZeroVector, Perf16SecPos = FVector::ZeroVector;
	float Perf16SecT = 0.f, Perf16Turned = -10.f;
	FString Perf16Broken;
	/** the list of 2026-11-22's second phase (RDList16b.cpp): the loading cover over the game's view after a level opens, a fast travel, the map's
	 *  teleport or a respawn, until the world round her is built and the textures streamed in (at most Cover16Cap s once it is built);
	 *  rd.LoadingCover 0 turns it off (tests that picture the first seconds) */
	void ShowCover16(const FString& Why);
	void TickCover16(float Dt);
	void HideCover16(const FString& How);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List16") bool IsCoverUp16() const { return bCover16; }
	/** tests: every cover so far, "<why>|<seconds up>|<seconds after the world was built>|<how it lifted>|<textures still wanting>|<her x cm>|<her y cm>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List16") TArray<FString> GetCoverLines16() const { return Cover16Lines; }
	/** tests: the map's travel to a town by name, as the package's -RDTownGo=town: does (found first, the refusal for enemies near passed) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List16") bool TravelToTown16(const FString& Name);
	/** (a plain member, not a UPROPERTY: the maps hold the generator, and a package staged on an earlier cook reads its saved properties
	 *  unversioned (the reel of 2026-11-18's lesson)) */
	float Cover16Cap = 8.f;
	bool bCover16 = false;
	FString Cover16Why;
	double Cover16Start = 0.0, Cover16ReadyAt = -1.0;
	int32 Cover16Steady = 0, Cover16Frames = 0;
	double Cover16FrameSum = 0.0;
	float Cover16Health = -1.f;
	TSharedPtr<class SWidget> Cover16Widget;
	TArray<FString> Cover16Lines;

	// ---- mistward_castle, the list of 2026-10-31b (docs/improvements5.txt; RDMistward5.cpp, pipeline/unreal/879): each a
	// switch, off on the other levels
	/** the kinds whose def says bShoots shoot from afar (FRDMonsterDef's Ranged*): their shots fly here, strike her, her
	 *  allies (or, an ally's, the monsters) and walls */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward5") bool bMonsterRanged = false;
	/** a monster's bar shows its name and its bar only (no hit points, no marks); an arena's monsters keep their names */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward5") bool bNameOnlyBars = false;
	/** while an arena is fought there is no way out: its doors stay locked (and say so), the teleport ring and the pads do
	 *  not carry her, and she is put back inside if she leaves the room by any way */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward5") bool bArenaLock = false;
	/** an audience in the arena: townsfolk appear along its walls as it begins, the first wave comes CrowdLead seconds after,
	 *  they cheer when a wave comes and clap and cheer when a monster falls; they leave when it is won or lost */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward5") bool bArenaCrowd = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward5") TArray<TObjectPtr<USkeletalMesh>> CrowdMeshes;
	/** each crowd body's own head and hair (the list of 2026-11-10: "some of the NPC crowd in the Arena have no heads") */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward5") TArray<FRDCrowdParts> CrowdParts;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward5") TObjectPtr<UAnimationAsset> CrowdIdle = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward5") TArray<TObjectPtr<UAnimationAsset>> CrowdClaps;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward5") TArray<TObjectPtr<UAnimationAsset>> CrowdCheers;
	/** the puff they appear and leave in */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward5") TObjectPtr<UFXSystemAsset> CrowdAppearFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward5") float CrowdAppearFxScale = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward5") int32 CrowdMax = 18;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward5") float CrowdLead = 3.f;
	/** how far in from the wall they stand, and apart (cm) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward5") float CrowdInset = 70.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward5") float CrowdSpacing = 160.f;
	/** the audience now (tests): who stands, what each does ("idle", "clap", "cheer"), cheers and claps begun */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward5") TArray<FString> GetCrowdLines() const;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward5") int32 CrowdCheersMade = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward5") int32 CrowdClapsMade = 0;
	/** ways out of an arena refused (the ring, a pad, a door) and times she was put back */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward5") int32 ArenaEscapesRefused = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward5") int32 ArenaPutBack = 0;
	/** an arena holds her now (bArenaLock and one is fought) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward5") bool IsArenaHolding() const { return bArenaLock && ArenaRoom >= 0; }
	/** world time the first wave is due (the audience's lead; -1 none pending) */
	float ArenaWaveDue = -1.f;
	bool bArenaSheInside = false;
	int32 CrowdLastLeft = 0;
	UPROPERTY(Transient) TArray<TObjectPtr<class ARDSpectator>> Crowd;
	void CrowdAppear(ARDSection* S, int32 Room);
	void CrowdReact(bool bCheer, float Share);
	void CrowdLeave();
	/** the arena's doors say they are barred; ring and pads refuse (the message said); true when refused */
	bool RefuseArenaExit(const TCHAR* How);
	/** what F says at a door of the arena being fought ("" none near) */
	FString ArenaDoorNear(const FVector& From) const;
	void TickArenaHold(float Dt);

	/** shots in the air: from whom, where, its speed, what it does, its effect */
	struct FMonsterShot
	{
		TWeakObjectPtr<ARDMonster> From; bool bAlly = false; FVector At = FVector::ZeroVector, Vel = FVector::ZeroVector;
		float Damage = 0.f, Life = 0.f; TWeakObjectPtr<UFXSystemComponent> Fx; TObjectPtr<UFXSystemAsset> HitFx = nullptr; float FxScale = 1.f;
		FName Kind; FString Theme;
		/** the final boss's lance: a mesh flying along the shot's way (its rotation from the way's, then MeshRot) */
		TWeakObjectPtr<AActor> Mesh; FQuat MeshRot = FQuat::Identity; FVector MeshPivot = FVector::ZeroVector;
	};
	TArray<FMonsterShot> MonsterShots;
	/** effects ending (a shot's trail fades, then goes) */
	TArray<TPair<TWeakObjectPtr<UFXSystemComponent>, float>> ShotFxEnding;
	void FireMonsterShot(ARDMonster* From, const FVector& Muzzle, const FVector& Aim, float Speed, float Damage, float Range, UFXSystemAsset* Fx, UFXSystemAsset* HitFx, float FxScale, const FString& Theme);
	void TickMonsterShots(float Dt);
	/** RestartPlay: the shots in the air, the audience and autoplay ended */
	void ResetMistward5();
	/** shots fired, landed on her, on her allies, on monsters (an ally's), on walls, faded at their range (tests) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward5") TMap<FString, int32> ShotStats;
	/** the last shot that struck her: its kind, its damage, the blow's damage of its kind (tests: weaker than the blow) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward5") FString LastShotOnHer;
	/** shots in the air now: "<kind>|<x>|<y>|<z>|<speed>" (tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward5") TArray<FString> GetShotLines() const;

	/** autoplay: the game plays her hero for Seconds (0: until a key of the player's): it seeks monsters and fights them
	 *  with her weapons, spells, chi and summons, drinks when hurt, opens chests, harvests, walks on to new rooms and sets;
	 *  a key, a click or a stick of the player's hands her back. From the command line (-Autoplay=<seconds>, with
	 *  -RDStartHero=<hero>) the game quits when the time is up; from the menu's AUTOPLAY it hands her back */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward5") bool bAutoplayMode = false;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward5") void StartAutoplay(float Seconds, bool bQuitAtEnd = false);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward5") void StopAutoplay(const FString& Why);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward5") bool IsAutoplaying() const { return bAutoplay; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward5") float GetAutoplayLeft() const;
	/** what the pilot does now ("fight Plague Rat", "walk to room 7", "open chest", ...) and its tallies (tests, the HUD) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward5") FString AutoplayDoing;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward5") TMap<FString, int32> AutoplayStats;
	/** tests: the player's keys do not take over (a test's own simulated keys would) */
	UPROPERTY(BlueprintReadWrite, Category = "RandomDungeon|Mistward5") bool bAutoplayIgnorePlayer = false;
	bool bAutoplay = false, bAutoplayQuit = false;
	float AutoplaySeconds = 0.f, AutoplayStart = 0.f, AutoplayThink = 0.f, AutoplayStuck = 0.f, AutoplayNextAct = 0.f, AutoplayUseNext = 0.f;
	/** what she heads for: 0 nothing, 1 a chest, 2 a monster (AutoplayPrey), 3 a room, 4 a way out to the next set; its key
	 *  in AutoplayRoomsBlocked (given up when she sticks on the way, a chest once reached) */
	int32 AutoplayGoalKind = 0, AutoplayGoalKey = 0;
	TWeakObjectPtr<ARDMonster> AutoplayPrey;
	FVector AutoplayLastPos = FVector::ZeroVector, AutoplayWalkFrom = FVector::ZeroVector;
	float AutoplayWalked = 0.f, AutoplayHuntNext = 0.f, AutoplayChordUntil = 0.f;
	bool bAutoplayHunting = false;
	/** monsters she found no way to (caged behind a wall, in a closed vault...): not hunted again this run */
	TSet<TWeakObjectPtr<ARDMonster>> AutoplayPreyBlocked;
	/** while any of these lives, autoplay fights only them, sees them across 40 m and takes no chest (the final boss's showcase:
	 *  him and his band; the first recording hunted another set's monsters for 80 s) */
	TArray<TWeakObjectPtr<ARDMonster>> AutoplayOnly;
	TArray<FVector> AutoplayPath;
	TWeakObjectPtr<ARDMonster> AutoplayFoe;
	TSet<FIntVector> AutoplayRoomsSeen;
	TSet<int32> AutoplayRoomsBlocked;
	FVector AutoplayGoal = FVector::ZeroVector;
	int32 AutoplayWeaponTurn = 0;
	FRandomStream AutoplayR;
	void TickAutoplay(float Dt);
	void ReadAutoplayOption();
	bool bAutoplayOptionRead = false;

	/** ceilings of more shapes and sizes: a rectangular room's ceiling is flat, raised, beamed, a sail dome, a groin vault
	 *  with ribs, a barrel vault with ribs, a cloister vault or hipped (its own stream: the layout is what it was) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward5") bool bCeilingStyles = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward5") float CeilingStyleShare = 0.8f;
	/** the ribs' and beams' materials (none: the room's wall's / ceiling's own) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward5") TObjectPtr<UMaterialInterface> CeilingRibMaterial = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward5") TObjectPtr<UMaterialInterface> CeilingBeamMaterial = nullptr;
	/** the highest a vault rises over its springing (cm) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward5") float CeilingMaxRise = 900.f;

	// ---- mistward_castle, the list of 2026-11-01 (docs/improvements6.txt; RDMistward6.cpp, pipeline/unreal/880): each a
	// switch, on the castle only
	/** the Rogue's stealth (a hero whose DexEnergy is over 0): Q, the gamepad's LB or its quick slot hides her for her
	 *  StealthSeconds at StealthCost of her dexterity energy (back DexPerSecond); monsters lose her and no trap goes off under
	 *  her; her first blow or bolt out of it does AmbushBonus more and ends it; a speed potion fills the energy */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward6") bool bStealth = false;
	/** the heroes grow as the tiers open (the hero's HealthPerTier, SpellPowerPerTier, UnarmedPowerPerTier for each tier open
	 *  past the first), and her mana comes back as a share of her pool (ManaRegenShare) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward6") bool bTierGrowth = false;
	/** a growing summon's strength (her hero's bSummonsGrow): a monster of the open tier's hit points and blows, times this by
	 *  the tier of the summoning (1 to 5; none: 1), whatever its kind: a higher summoning stays the stronger (raised to the open
	 *  tier by its kind's own factor, a tier-1 Soldier outdid a tier-5 Spider). The factors must not fall from tier 1 to 5, or a
	 *  low summoning grown to the open tier outdoes a high one. 880 sets balance6.json's 0.8 to 1.0 (2026-11-06; at 1.2 to 1.4
	 *  she beat everything): a tier-1 Soldier at tier 1 has 40 hit points and 9 a blow, a tier-5 Spider 340 and 55 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward6") TArray<float> SummonTierStrength;

	// ---- the final boss (the user's spec of 2026-11-03; RDAurorim.cpp, pipeline/unreal/889): when the last tier reaches the
	// tiers' share (TierOpenShare of its rooms explored, monsters killed, chests looted), FinalBossKind waits in a room of it she
	// has explored with FinalBossMinions of its kinds, scaled as the tier's boss; beside it a door to Brokenspire, sealed while it
	// lives. Its death: its loot (the best of the last tier's things she can use), FinalBossGold, the victory, the door open
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Final") bool bFinalBossOn = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Final") FName FinalBossKind = NAME_None;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Final") FIntPoint FinalBossMinions = FIntPoint(6, 10);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Final") int32 FinalBossGold = 2500;
	/** its size against its kind's (its health and blows are the tier's boss's: BossHealth, BossDamage, times FinalBossHealth,
	 *  FinalBossDamage) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Final") float FinalBossScale = 1.f;
	/** the dungeon boss above a tier's (the user's of 2026-11-04: "a little more challenging"): its hit points and blows over a
	 *  tier's boss's, and its lance's and light's waits (shorter under 1) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Final") float FinalBossHealth = 1.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Final") float FinalBossDamage = 1.25f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Final") float FinalBossWaitScale = 0.75f;
	/** his tactics: while more than FinalBossCloseBand of his band are within 25 m of him, he keeps FinalBossHold (cm, nearest
	 *  and farthest) from her, circling her, with his lance and his light (his band fights her); struck within FinalBossStruckHold
	 *  seconds, or his band down, he comes in to his fists, and steps round her between his blows */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Final") FVector2D FinalBossHold = FVector2D(900.f, 1300.f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Final") int32 FinalBossCloseBand = 0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Final") float FinalBossStruckHold = 4.f;
	/** his poise: a blow makes him flinch (his punch lost, a moment's stun) at most once in this many seconds (0: every blow) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Final") float FinalBossPoise = 3.f;
	/** his band alive within 25 m of him now (TickFinal) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Final") int32 GetFinalBandNear() const { return FinalBandNear; }
	/** the balance trials (868 balance): Aurorim and his band set in room Room of set Set as the game sets him (his encounter,
	 *  his tactics, his door), whatever the tiers' share; false if he is placed already or could not be */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Final") bool DebugPlaceFinalBoss(FIntPoint Set, int32 Room);
	/** autoplay fights only him and his band (as the showcase's go: seen across 40 m, no chests); how many of them live */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Final") int32 DebugAutoplayOnlyFinal();
	/** he holds back now: his band near enough and he not struck lately (his tactics; autoplay leaves him for his band then) */
	bool FinalBossHolds(const ARDMonster* Boss) const;
	int32 FinalBandNear = 0;
	/** any of his band after her now (he notices her from farther then) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Final") bool bFinalBandFighting = false;
	/** the door: an arch (FinalDoorFrame), a grating in it while sealed (FinalDoorGate, sinking into the floor when it opens),
	 *  a light in it once open (FinalDoorFx); scaled to stand FinalDoorHeight tall */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Final") TObjectPtr<UStaticMesh> FinalDoorFrame = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Final") TObjectPtr<UStaticMesh> FinalDoorGate = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Final") TObjectPtr<UFXSystemAsset> FinalDoorFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Final") float FinalDoorHeight = 380.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Final") float FinalDoorFxScale = 0.5f;
	/** placed, slain (for the game: a counter), the door open, the reward given ("<item>|<gold>") */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Final") bool bFinalBossPlaced = false;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Final") bool bFinalBossSlain = false;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Final") FString FinalReward;
	UPROPERTY(Transient) TObjectPtr<class ARDFinalDoor> FinalDoor = nullptr;
	/** "<placed>|<slain>|<door open>|<section x>|<section y>|<room>|<band>|<boss alive>|<boss hp>|<reward>|<share done/all>" (tests) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Final") FString GetFinalBossState() const;
	/** the last tier's share now: "<rooms done>/<all>|<killed>/<all>|<looted>/<all>|<complete>" (tests) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Final") FString GetTierShareLine(int32 Tier) const;
	/** the final boss's monster (none: not placed, or gone) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Final") ARDMonster* GetFinalBoss() const;
	/** the door's actor (none before the boss is placed) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Final") class ARDFinalDoor* GetFinalDoor() const { return FinalDoor; }
	/** the light from above in the air: "<x>|<y>|<z>|<seconds left>|<radius>|<damage>", and those that fell, struck her (tests) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Final") TArray<FString> GetSkyBeamLines() const;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Final") TMap<FString, int32> SkyBeamStats;
	void CheckFinalBoss();
	bool PlaceFinalBoss();
	void OnFinalBossKilled(ARDMonster* Boss);
	void TickFinal(float Dt);
	void ResetFinal();
	/** the best of the last tier's things her hero can use: a weapon she wields, else armour she wears, else a ring */
	FName PickFinalReward() const;
	/** a beam called down: a mark at At now, the light BeamDelay seconds after */
	void QueueSkyBeam(ARDMonster* From, const FVector& At, float Delay, float Radius, float Damage, UFXSystemAsset* Fx, UFXSystemAsset* MarkFx, UFXSystemAsset* HitFx, float FxScale, float MarkScale, bool bFxUser, bool bMarkUser, bool bHitUser);
	struct FSkyBeam
	{
		TWeakObjectPtr<ARDMonster> From; FVector At = FVector::ZeroVector; float Left = 0.f, Radius = 200.f, Damage = 0.f, FxScale = 1.f; bool bFxUser = false, bHitUser = false;
		TObjectPtr<UFXSystemAsset> Fx = nullptr; TObjectPtr<UFXSystemAsset> HitFx = nullptr; TWeakObjectPtr<UFXSystemComponent> Mark;
	};
	TArray<FSkyBeam> SkyBeams;
	/** the final boss set again on the way back into the castle (placed, not slain, before she left): once a room of the tier
	 *  is seen */
	bool bFinalRestorePending = false;
	float FinalRestoreTry = 0.f;
	// ---- the final boss's showcase (a reel of the fight: RDAurorim.cpp). In the town: into the castle. In the castle: every tier
	// open (her growth), the best of everything her hero can use on her (armour, weapon, shield, a ring of each kind, the slash
	// table's last slash on the weapon, healing potions), a set of the last tier, him and his band there; once the go file is
	// there (the recording begun), autoplay fights; a while after his death (or hers) the done file is written
	/** begins it here (tests, a rehearsal in the editor: Go and Done as the command line's) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Final") void StartFinalShow(const FString& Go, const FString& Done);
	/** "<phase>|<seconds in it>|<fight seconds>|<her hp>|<her max>|<boss hp>|<band alive>|<result>|<kit>" (tests, the recorder) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Final") FString GetFinalShowState() const;
	void TickFinalShow(float RealDt);
	bool bFinalShowOn = false, bFinalShowCmdRead = false;
	int32 FinalShowPhase = 0;
	float FinalShowT = 0.f, FinalShowFightT = 0.f, FinalShowCheck = 0.f, FinalShowAggro = 0.f, FinalShowLose = 0.f;
	FIntPoint FinalShowSet = FIntPoint::ZeroValue;
	/** the showcase's room for him (the set's largest: room for his lance before his light and his fists); -1 none */
	int32 FinalShowRoom = -1;
	FString FinalShowGo, FinalShowDone, FinalShowReady, FinalShowResult, FinalShowKit, FinalShowGoLine;
	/** the fight's order and moves for the done file: her first blow on him (fight seconds, -1 none) and his band alive then,
	 *  the band's last death, her lowest hit points */
	float FinalShowFirstHitT = -1.f, FinalShowBandDoneT = -1.f, FinalShowMinHp = 0.f, FinalShowHoldS = 0.f, FinalShowBossCircleS = 0.f, FinalShowBossMaxHp = 0.f;
	int32 FinalShowBandAtHit = -1;
	/** the highest tier open (1 at the start) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward6") int32 GetOpenTier() const;
	/** what the tiers opened give her hero now: her hit points' factor, a spell's and her fists' damage factors */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward6") float TierHealthMul() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward6") float TierSpellMul() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward6") float TierOwnWeaponMul() const;
	/** her mana's factor from the tiers opened (her hero's ManaPerTier) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward6") float TierManaMul() const;
	/** her hero's summons grow with the tiers opened (bTierGrowth and the hero's bSummonsGrow) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward6") bool SummonsGrow() const;
	/** a growing summon's hit points and blow for its summoning now (SummonTierStrength at the open tier), and the tier it is
	 *  then (the open tier, or its summoning's if higher: its speed, pace and ability are that tier's) */
	void SummonStrength(FName Spell, float& OutHealth, float& OutDamage, int32& OutTier) const;
	/** a weapon's damage factor from the tiers opened (a spell or chi: TierSpellMul; one of her own: TierOwnWeaponMul; a
	 *  found one 1: its damage carries its own tier) */
	float TierPowerOf(const FRDWeaponDef& W) const;
	/** mana back a second with her pool at MaxMana */
	float GetManaRegen(float MaxMana) const;
	/** a tier opened: she grows (her hit points' new top, the message) */
	void OnTierGrowth(int32 Tier);
	/** the autoplay pilot steps back from a monster close in while she fights from afar (casters, a crossbow); her next try
	 *  at stealth */
	bool bAutoplayKiting = false, bAutoplayStealthFlee = false;
	float AutoplayStealthNext = 0.f, AutoplayKiteEnd = 0.f, AutoplayKiteNext = 0.f;
	/** the final boss's fight (2026-11-04): she steps round him between her blows (the way round, when it turns), and out of
	 *  his light's mark before it falls */
	float AutoplayCircleSign = 1.f, AutoplayCircleFlip = 0.f, AutoplayCircleSeconds = 0.f;
	bool bAutoplayWasAttacking = false, bAutoplayDodging = false;

	// ---- Brokenspire (docs/brokenspire.txt; RD/RDTown*.cpp, pipeline/unreal/881-884): the starting town and the castle's
	// side of it. Each a switch: bTown on the town's map (its start section is the town: ARDSection::PlanTown), bTownLink on
	// Mistward Castle (and the town): gold, her things and the purse kept between the two (URDGameInstance), the quests'
	// counters, the way back to the town. Off on every other level.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") bool bTown = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") bool bTownLink = false;
	/** the town's name (the minimap's title, the map's plaque) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") FString TownName = TEXT("Brokenspire");
	/** where the Mistgate leads (the town's) and the way back (the castle's): maps opened with ?Hero= */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") FString CastleLevel;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") FString TownLevel;
	/** Vel Morrath (2026-11-06): the catacombs' level the holy city's cathedral opens (the town's); this dungeon level's key (a
	 *  dungeon's: empty for Mistward Castle, "vel_morrath" for the catacombs: its tiers, counters and her piles kept apart; its
	 *  name for the player is DungeonTitle) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") FString CatacombsLevel;
	/** a dungeon's own props set by its rooms' walls after their furniture (2026-11-07: The War Engine's gears, chains, ore
	 *  carts; piece names in Pieces), every ThemePropSpacing cm of wall with ThemePropChance; none: none */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") TArray<FName> ThemeProps;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float ThemePropSpacing = 450.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float ThemePropChance = 0.35f;
	/** each wilderness town's own dungeon level by the town's name (2026-11-07: Ashenreach's War Engine, Graymourne's sewers;
	 *  each city's script sets its own); Vel Morrath's is CatacombsLevel when it is not here */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") TMap<FString, FString> TownDungeons;
	/** Kethrys Spire's black tower: how high its round tower rises over the town's ground (cm; RDMage.cpp) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float SpireTowerTop = 5500.f;
	/** a dungeon's own light: every light of its sets drawn this share toward this colour (0: the torches' own; 907 sets the
	 *  Black Tower's cold violet) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") FLinearColor DungeonLightTint = FLinearColor::White;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float DungeonLightTintShare = 0.f;
	// ---- the dungeons' keys in order (the list of 2026-11-08b's third phase, RDKeys.cpp): "<dungeon key>|<level>|<town>|<title>|
	// <key item>|<map item>" from Mistward Castle (its key empty, no key or map) to Heaven; each dungeon's boss drops the next's key
	// and map, and the way into a town's dungeon is refused without its key. 905 writes it on every map (SourceArt/dungeons/chain.json)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Keys") TArray<FString> DungeonChain;
	struct FRDChainLink { FString Key, Level, Short, Town, Title; FName KeyItem, MapItem; int32 TierBase = 0, TierCap = 0; };
	/** the chain parsed (once, again when its text changes) */
	const TArray<FRDChainLink>& Chain() const;
	mutable TArray<FRDChainLink> ChainCache;
	mutable uint32 ChainHash = 0;
	int32 ChainIndexOfLevel(const FString& Level) const;
	int32 ChainIndexOfKey(const FString& Key) const;
	/** she may go down into a level: Mistward Castle and a level not in the chain always; another with its key held or once held */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Keys") bool HasDungeonKey(const FString& Level) const;
	/** what she is told at a locked way down ("" when it is not locked) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Keys") FString DungeonLockedLine(const FString& Level) const;
	/** a dungeon's key or map (kept at her death) */
	bool IsDungeonChainItem(FName Item) const;
	/** this dungeon's boss fell at At: the next dungeon's key and map lie there (once a game) */
	void DropNextDungeonKey(const FVector& At);
	/** once a second: a key or map she carries kept in the counters; out in the wilds a map's road revealed */
	void TickDungeonKeys();
	float DungeonKeysNextTick = 0.f, DungeonLockedSaidAt = -100.f;
	/** the road from one town to another and the land round the second revealed on her map; the cells revealed */
	int32 RevealRoute(const FString& From, const FString& To);
	/** the key dropped here this play ("" none; tests) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Keys") FString DungeonKeyDropped;
	/** the last way down refused for want of its key (tests) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Keys") FString DungeonLockedLevel;
	/** every way open (tests and the packaged game's runs: -RDAllKeys) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Keys") void DebugAllDungeonKeys(bool bOn);
	/** "<index>|<key>|<level>|<town>|<key item>|<open 0/1>|<key had>|<map had>|<map shown>" (tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Keys") TArray<FString> GetDungeonKeyLines() const;
	/** this level's boss fell at At (cm): the next dungeon's key and map dropped as the boss's death drops them (tests) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Keys") void DebugDropNextDungeonKey(FVector At) { DropNextDungeonKey(At); }
	/** the wilderness's tier at a point (metres; 0 with no wilds) (tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Keys") int32 GetWildTierAt(float Xm, float Ym) const;
	/** the town she is in's dungeon level (empty: none; Brokenspire's is the castle, through the Mistgate) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") FString CurrentDungeonLevel() const;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") FString DungeonKey;
	/** a counter of this dungeon's ("bossdone:2", "tier", "prisoners"): Mistward Castle's as they were, another's under its key */
	FString DungeonCounterName(const FString& N) const;
	/** the town the way out leads to, as the player reads it (the catacombs': the town she came down from) */
	FString WayBackName() const;
	/** a quest of the town she is in (Brokenspire's have no town set); the quest lines of those only, for the givers' marks */
	bool IsQuestHere(const FRDQuestDef& Q) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") TArray<FString> GetQuestLinesHere() const;
	/** the deepest tier open in one dungeon (empty key: Mistward Castle), from the state itself */
	int32 DungeonTierReached(const FString& Key) const;
	/** the town's side of a trip down into a dungeon (the autosave, her state carried, the town's state put away, the level
	 *  opened); Why is the autosave's reason and the game instance's Arrive */
	void TravelToDungeon(const FString& Level, const FString& Why);
	/** a city's way into its dungeon (Vel Morrath's cathedral stair, Ashenreach's foundry gate, Graymourne's sewer entrance):
	 *  walked into, its level opens (a test's dry run only says so) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Brokenspire") bool EnterCatacombs();
	/** the town she is in has a dungeon of its own (not Brokenspire, whose castle is the Mistgate's) */
	bool HasTownDungeon() const { return bTown && !bTownHome && !CurrentDungeonLevel().IsEmpty(); }
	/** the way down into a dungeon (Level, or the town's own when empty), she coming back at ReturnAt facing ReturnYaw (the
	 *  landmark's door; -RDTownGo: where she stands); a test's dry run only says so */
	bool DescendToCatacombs(const FVector& ReturnAt, float ReturnYaw, const FString& Level = FString());
	/** the town's people and its quests (pipeline/unreal/882 from SourceArt/brokenspire/town.json) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") TArray<FRDTownsfolkDef> Townsfolk;
	// ---- the town's life (the third list, 2026-11-02; RDTownLife.cpp; 886 fills these)
	/** the pens' animals, their kinds in turn pen by pen */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") TArray<FRDTownAnimalDef> TownAnimals;
	/** what the townsfolk hold at their work, by name ("Ladle", "Tray", "Mug", "Bowl", "Hammer") */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") TMap<FName, FRDTownProp> TownProps;
	/** how far a worker's feet stand from the thing worked, by the work's clip name (the clips' own numbers, 886) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") TMap<FName, float> TownWorkReach;
	/** a cooking pot's base over its fire, a spit's rod over the ground (cm) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float TownPotHeight = 12.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float TownSpitHeight = 75.f;
	/** the spit's rod and its meat (play: turned while its crank is turned) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") TObjectPtr<UStaticMesh> TownSpitRod = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") TObjectPtr<UStaticMesh> TownSpitMeat = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") TObjectPtr<class UMaterialInterface> TownSpitRodMaterial = nullptr;
	/** a round of work's time at each place (s; each townsperson draws its own range from these) and the customers a tavern
	 *  gets for its seats */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") FVector2D TownWorkSeconds = FVector2D(14.f, 40.f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float TownPatronShare = 0.7f;
	/** whose a place of work is now (claimed while it is gone to and worked), the town's animals and spits (play) */
	TArray<TWeakObjectPtr<class ARDTownsfolk>> TownWorkBy;
	UPROPERTY(Transient) TArray<TObjectPtr<class ARDTownAnimal>> TownAnimalActors;
	UPROPERTY(Transient) TArray<TObjectPtr<USceneComponent>> TownSpitTurners;
	UPROPERTY(Transient) TArray<TObjectPtr<USceneComponent>> TownSpitParts;
	TArray<int32> TownSpitCrank;
	bool ClaimTownWork(int32 Work, class ARDTownsfolk* T);
	void ReleaseTownWork(int32 Work, const class ARDTownsfolk* T);
	bool IsTownWorkFree(int32 Work, const class ARDTownsfolk* T) const;
	void SpawnTownAnimals();
	void SpawnTownSpits();
	/** who does what (after SpawnTownPeople): the rounds of work, the tavern's customers and server, the animals, the spits */
	void SpawnTownLife();
	void TickTownLife(float Dt);
	/** the town's life for tests: "work|<i>|<kind>|<group>|<x>|<y>|<by>" each place, "folk|<i>|<role>|<state>|<work>|<kinds done>|<jobs>|<min s>|<max s>",
	 *  "animal|<i>|<kind>|<x>|<y>|<pen>|<state>", "spit|<i>|<turns>|<worked>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") TArray<FString> GetTownLifeLines() const;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") TArray<FRDQuestDef> Quests;
	/** the ground's material (the village's: grass, trodden earth, cobbles, lush grass by vertex colour) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") TObjectPtr<UMaterialInterface> TownGroundMaterial = nullptr;
	/** a new game's town from a seed of its own (off: the saved one, StartSeed's) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") bool bTownNewSeed = true;
	/** the Mistward Hall's guards: how many (a random number between), of tier 1 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") int32 TownGuardsMin = 5;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") int32 TownGuardsMax = 10;
	/** gold: a kill gives Min..Max times its tier, a boss BossGold times its tier more; a container holds gold one time in
	 *  ContainerGoldChance, Min..Max times its tier */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") FVector2D KillGold = FVector2D(1.f, 4.f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float BossGold = 40.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float ContainerGoldChance = 0.45f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") FVector2D ContainerGold = FVector2D(3.f, 12.f);
	/** what the trader pays for a thing, a share of what it costs */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float SellShare = 0.35f;
	/** the price of an item (its kind's base by the first tier it is found in) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") int32 PriceOf(FName Item) const;
	/** her purse (the game's: kept between the levels) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") int32 GetGold() const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Brokenspire") void AddGold(int32 Amount, const FString& Why = FString());
	/** the highest castle tier she has opened this game (the trader's stock and the services' prices follow it) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") int32 GetGameTier() const;
	/** her things into the game instance (before another level opens) and back (when her combat component is made) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Brokenspire") void SaveCarry();
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Brokenspire") bool RestoreCarry();
	/** her state as she came into this level (her combat component's GetStateLines just after RestoreCarry; empty: nothing
	 *  carried), to set against what she left the other level with (the game instance's CarryLeftLines) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") TArray<FString> GetCarryArrivedLines() const { return CarryArrivedLines; }
	/** the summons she brought that are not at her side yet (called once she stands in the level) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") int32 GetCarrySummonsWaiting() const { return CarrySummons.Num(); }
	// (her state carried (RDCarry.cpp): the lines as she came in; her summons waiting to be called to her side, from when, until
	// when: set by her combat component's RestoreState)
	TArray<FString> CarryArrivedLines;
	TArray<FName> CarrySummons;
	TArray<float> CarrySummonShares;
	TArray<FName> CarrySummonKinds15;          // (the list of 2026-11-20: each one's kind, beside its summoning)
	float CarrySummonFrom = -1.f, CarrySummonUntil = -1.f;
	void TickCarrySummons();
	/** through the Mistgate (the town's) / back to the town (the castle's); a test's dry run only says where it would go */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Brokenspire") bool EnterCastle();
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Brokenspire") bool ReturnToTown();
	/** the showcase tour (a reel, a recording; -RDTownTour=<castle autoplay seconds> [-RDTourGo=<file>: it waits for the file]):
	 *  before the elder, his panel (a question asked), the papyrus map, a run over the town's ground to the castle and into
	 *  the Mistgate; in the castle autoplay for the seconds (the game quits after) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Brokenspire") void StartTownTour(float CastleAutoplaySeconds, const FString& GoFile = TEXT(""));
	/** "<phase>|<seconds in the phase's clock>|<path points left>|<to the Mistgate, m>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") FString GetTownTourState() const;
	UPROPERTY(BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") bool bTravelDryRun = false;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") FString LastTravel;
	/** tests and the reels: the town built again from Seed (0: a new one), the townspeople and guards with it, her in the square */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Brokenspire") void RebuildTown(int32 Seed);
	/** the town (tests): "<index>|<kind>|<label>|<state 0 lived, 1 burned, 2 boarded>|<x>|<y>|<door x>|<door y>|<rooms>|<boarded now>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") TArray<FString> GetTownBuildingLines() const;
	/** what stands outdoors and the services: "<kind>|<x>|<y>|<z>|<building>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") TArray<FString> GetTownSpotLines() const;
	/** the townspeople: "<index>|<role>|<name>|<title>|<x>|<y>|<z>|<walks>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") TArray<FString> GetTownsfolkLines() const;
	/** a named place of the town (world): "square", "gate", "mistgate", "castle door", "circle", "board", a spot or a building
	 *  kind ("smithy", "stash"...); false: none */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") bool GetTownPlace(const FString& What, FVector& At) const;
	/** the Mistward Hall's guards alive now */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") TArray<ARDMonster*> GetTownGuards() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") int32 GetTownGuardsPlanned() const { return TownGuardsPlanned; }
	/** the quests: "<id>|<giver>|<title>|<state: offered, taken, ready, done, later>|<progress>|<count>|<hint>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") TArray<FString> GetQuestLines() const;
	/** a quest's progress now (its counter less where it stood when taken; "tier": the highest whole) */
	int32 QuestProgress(const FRDQuestDef& Q) const;
	/** the town's panel (it pauses the game): "talk" (someone of the town: ask, quests), "store" (buy, sell), "smith" (repairs,
	 *  the anvil), "healer", "temple", "stash" (her storage), "circle" (the teleport circle), "board" (the quest board) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Brokenspire") bool OpenTownPanel(FName Kind, int32 Who = -1);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Brokenspire") void CloseTownPanel();
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") bool IsTownPanelOpen() const { return !TownPanel.IsNone(); }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") FName GetTownPanel() const { return TownPanel; }
	/** the panel's lines: "<action>|<label>|<tag>|<1 can be done>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") TArray<FString> GetTownPanelLines() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") FString GetTownPanelText() const { return TownBody; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") FString GetTownNote() const { return TownNote; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") int32 GetTownCursor() const { return TownCursor; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") int32 GetTownTab() const { return TownTab; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Brokenspire") void MoveTownCursor(int32 Step);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Brokenspire") void SetTownTab(int32 Tab);
	/** does the line under the cursor (or Line): false when it cannot be done (its note says why) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Brokenspire") bool ActivateTownEntry(int32 Line = -1);
	/** the nearest townsperson of a role (tests; -1 none) and F at them */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") int32 FindTownsfolk(ERDTownRole InRole) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") class ARDTownsfolk* GetTownsfolk(int32 Index) const { return TownPeople.IsValidIndex(Index) ? TownPeople[Index].Get() : nullptr; }
	/** what she heard last from someone of the town (who|line) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") FString LastBark;
	/** F passing over the townsfolk asleep who only talk (PR #41's review: one asleep by the smithy's forge took F from it) */
	mutable bool bTownSkipSleepers = false;
	/** the town panel's rows as the HUD drew them (the mouse reads them) */
	TArray<FBox2D> TownRowBoxes;
	TArray<FBox2D> TownTabBoxes;
	/** the town panel's cursor held down (W / S, the D-pad, the left stick): its way and when it steps next (real time) */
	int32 TownRepeatDir = 0;
	double TownRepeatAt = 0.0;
	/** the list of 2026-11-08b: the storage's use held down stores (or takes back) the same thing again: what (its act and the
	 *  thing's name, empty when nothing is held) and when next (real time) */
	FName TownHoldAct;
	FString TownHoldThing;
	double TownHoldAt = 0.0;
	/** the thing a storage line stores or takes back ("" for a found weapon, which does not stack) */
	FString TownLineThing(int32 Line) const;
	/** what decides which stored things stack on one line: the thing's name, and its wear where it wears ("" out of range) */
	FString StashKey(int32 Index) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") int32 GetTownHoldUses() const { return TownHoldUses; }
	int32 TownHoldUses = 0;
	/** the list of 2026-11-07 (RDTown8.cpp): her blow meets the barracks' dummies in its reach and arc (they rock; the sound and
	 *  the blow's number over them); a bolt's trace that hit one's mesh. TownDummyHits counts them (tests) */
	int32 HitTownDummiesInArc(const FVector& L, const FVector& Fw, float Reach, float MinCos, float Strength, FName Sound, float Dmg);
	bool HitTownDummyByComponent(const class UPrimitiveComponent* C, const FVector& From, float Strength, FName Sound, float Dmg);
	/** every town section's dummies (kind|x|y|z|hits|lean deg|radius|height) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") TArray<FString> GetTownDummyLines() const;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") int32 TownDummyHits = 0;
	/** her talk's partner (the townsperson's index) */
	int32 TownWho = -1;
	struct FTownLine { FString Label, Tag, Detail; FName Act; FString Arg; bool bOn = true; };
	TArray<FTownLine> TownLines;
	FString TownTitle, TownSub, TownBody, TownNote;
	float TownNoteTime = -100.f;

	// ---- Brokenspire's day and night (RDTownDay.cpp; the user's of 2026-11-02): a full day in DayLengthSeconds of play in the
	// town; the sun (the level's atmosphere sun) and a moon made in play cross the sky, the sky light, the fog's light and the
	// exposure follow the daylight
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") bool bDayNight = false;
	/** damage from a fall (the third list of 2026-11-02; 886 sets it on Brokenspire and the castle): none up to FallSafeHeight
	 *  (cm, the top of the fall to where she lands), then a share of her hit points, all of them at FallLethalHeight */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") bool bFallDamage = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float FallSafeHeight = 450.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float FallLethalHeight = 1500.f;
	// (an hour since the third list of 2026-11-02: "the day/night cycle should last one hour, not half an hour"; 886 sets it)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float DayLengthSeconds = 3600.f;
	/** a new game's first hour in the town (-RDTownHour=<h> another, for a reel) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float TownStartHour = 8.f;
	/** the sun's height at noon (degrees) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float DayMaxSunElevation = 62.f;
	/** the moon's light (lux), the sky light's share at night, the exposure's bias added at night (stops) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float MoonLux = 0.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float NightSkyShare = 0.08f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float NightExposureBias = -1.2f;
	/** the town's hour (0-24) and day; set it (tests, reels) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") float GetTownHour() const { return TownHour; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") int32 GetTownDay() const { return TownDay; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Brokenspire") void SetTownHour(float Hour);
	/** "HH:MM" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") FString GetTownClock() const;
	/** "<day>|<hour>|<sun elevation>|<daylight 0-1>|<sun lux>|<moon lux>|<sky light>|<exposure bias>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") FString GetDayNightState() const;
	float TownHour = 8.f, DayLight = 1.f;
	int32 TownDay = 1;
	void BeginDayNight();
	void TickDayNight(float Dt);
	/** the list of 2026-11-08b: rd.GameSpeed put on the world when it changes (every level); what was put last */
	void TickGameSpeed();
	float GameSpeedApplied = 1.f;
	void ApplyDayNight();
	UPROPERTY(Transient) TObjectPtr<class UDirectionalLightComponent> DaySun;
	UPROPERTY(Transient) TObjectPtr<class UDirectionalLightComponent> DayMoon;
	UPROPERTY(Transient) TObjectPtr<class USkyLightComponent> DaySky;
	UPROPERTY(Transient) TObjectPtr<class UExponentialHeightFogComponent> DayFog;
	UPROPERTY(Transient) TObjectPtr<class APostProcessVolume> DayPost;
	float DaySunLux = 7.5f, DaySkyLight = 1.f, DayBias = 0.f, DayApplyT = 0.f;
	bool bDayBaseRead = false;
	UPROPERTY(Transient) TObjectPtr<class UDirectionalLightComponent> DayMoonKept;
	FLinearColor DaySunColor = FLinearColor::White, DayFogLight = FLinearColor::White;

	// ---- the user's list of 2026-11-04 (docs/improvements7.txt; RDTown7.cpp, RDSky.cpp, RDWildLife.cpp; 890 sets them)
	/** the town: a street's cobbles half as wide as this (cm: "at most 3 people wide"), the open ground's rise and fall (cm), how
	 *  far the portcullis lifts (cm), what a garden's crops give (by the crop's kind: Town.Crop1..6), the reach of F at a
	 *  garden, an oven, a table's food */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire7") float TownCobbleHalfWidth = 130.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire7") float TownLiftAmp = 140.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire7") float TownPortcullisLift = 275.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire7") TArray<FName> TownCropItems;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire7") float TownThingReach = 230.f;
	/** a garden harvested grows again after this many of the town's days */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire7") int32 GardenRegrowDays = 1;
	/** the sky: clouds (a volumetric cloud material of the engine's, its coverage from the weather), the stars (a dome), the
	 *  moon (a disc far off), the height fog kept off the sky beyond this distance (cm: it had covered the whole sky in grey) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") bool bSky7 = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") TObjectPtr<UMaterialInterface> SkyCloudMaterial = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") TObjectPtr<UMaterialInterface> SkyHighCloudMaterial = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") TObjectPtr<UMaterialInterface> SkyStarsMaterial = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") TObjectPtr<UMaterialInterface> SkyMoonMaterial = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") TObjectPtr<UStaticMesh> SkyDomeMesh = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") TObjectPtr<UStaticMesh> SkyQuadMesh = nullptr;
	/** what is farther than this (cm) gets no height fog: the sky itself (the fog's colour hid it, 2026-11-04). The list of
	 *  2026-11-07: at 6 km the clouds overhead (1.6 km up) were fogged and those past 6 km, below 15 degrees, were not: "a
	 *  giant circle of white ... not continuous with the rest of the sky". 1000 km: every cloud and the land fogged by their
	 *  distance, the sky's own pixels (at no distance) left clear */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") float FogSkyCutoff = 1.0e8f;
	/** the cloud material's Cloud_GlobalCoverage at a clear sky and at an overcast one */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") FVector2D SkyCoverRange = FVector2D(0.1f, 1.f);
	/** weather: rain and snow round her camera, wind (blowing leaves, the grass's sway through WindCollection's "Strength"),
	 *  how long a weather lasts (s) */
	/** the rain and snow of our own (the packs' rain did not show): a field of thin planes round her camera, falling in their
	 *  material (890's M_RD_Drops: the drops move by its world position offset, wrapped in the field's height) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") TObjectPtr<UStaticMesh> DropMesh = nullptr;
	/** the list of 2026-11-07: a rain streak's length and width as the drop plane's scale (100 cm a unit) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") FVector2D RainStreak = FVector2D(0.26f, 0.009f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") TObjectPtr<UMaterialInterface> RainDropMaterial = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") TObjectPtr<UMaterialInterface> SnowDropMaterial = nullptr;
	UPROPERTY(Transient) TObjectPtr<class UHierarchicalInstancedStaticMeshComponent> RainDrops;
	UPROPERTY(Transient) TObjectPtr<class UHierarchicalInstancedStaticMeshComponent> SnowDrops;
	UPROPERTY(Transient) TObjectPtr<class UMaterialInstanceDynamic> RainDropMID;
	UPROPERTY(Transient) TObjectPtr<class UMaterialInstanceDynamic> SnowDropMID;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") TObjectPtr<UNiagaraSystem> RainFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") TObjectPtr<UNiagaraSystem> SnowFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") TObjectPtr<UNiagaraSystem> WindFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") TObjectPtr<class UMaterialParameterCollection> WindCollection = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") FVector2D WeatherSeconds = FVector2D(240.f, 540.f);
	/** the birds in the sky and the insects round her (the list's "birds of different sizes and types", "animals and insects
	 *  that are appropriate for that biome") and the wild animals that flee */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") TArray<FRDWildSwarm> WildSwarms;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") TArray<FRDWildFauna> WildFauna;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") int32 WildAnimalsMax = 10;
	/** music: a new track after a while of its own (s; the list's "after 5-10 minutes, the music should change to another
	 *  appropriate song for the scene"); the scene's set: Music.Town, Music.TownNight, Music.Wild, Music.WildNight (else
	 *  Music.Explore) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sound") FVector2D MusicRotateSeconds = FVector2D(300.f, 600.f);
	// the sky and weather's state (RDSky.cpp)
	void BeginSky7();
	/** the high clouds' height, tile and wind (the volumetric clouds' CloudWind, else +X) into their material */
	void ApplySkyHighLayer();
	void TickSky7(float Dt, APlayerController* PC);
	/** the weathers' turn's weights where she is (the regions' own: the cold lands' whiteout, the dry lands' dust, the moors' fog) */
	void WeatherWeights(bool bDry, bool bWhiteLand, bool bDustLand, bool bMoorLand, float* Wt) const;
	bool SkyMoorLand = false, SkyDryLand = false, SkyWhiteLand = false, SkyDustLand = false;
	/** the turn's next weather from a hash (TickSky7; CountWeatherPicksHere runs it for the test) */
	int32 PickWeather(uint32 H, int32 Current, bool bDry, bool bWhiteLand, bool bDustLand, bool bMoorLand) const;
	/** (the fourth phase's test) "clear:412|fair:...": N turns of the weather's own pick where she stands, how often each came */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild13") FString CountWeatherPicksHere(int32 N) const;
	void ApplySky7();
	UPROPERTY(Transient) TObjectPtr<class UVolumetricCloudComponent> SkyClouds;
	UPROPERTY(Transient) TObjectPtr<class UMaterialInstanceDynamic> SkyCloudMID;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> SkyHigh;
	UPROPERTY(Transient) TObjectPtr<class UMaterialInstanceDynamic> SkyHighMID;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> SkyStars;
	UPROPERTY(Transient) TObjectPtr<class UMaterialInstanceDynamic> SkyStarsMID;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> SkyMoon;
	UPROPERTY(Transient) TObjectPtr<class UMaterialInstanceDynamic> SkyMoonMID;
	UPROPERTY(Transient) TObjectPtr<class UNiagaraComponent> WeatherRain;
	UPROPERTY(Transient) TObjectPtr<class UNiagaraComponent> WeatherSnow;
	UPROPERTY(Transient) TObjectPtr<class UNiagaraComponent> WeatherWind;
	UPROPERTY(Transient) TObjectPtr<class UAudioComponent> WeatherRainSound;
	UPROPERTY(Transient) TObjectPtr<class UAudioComponent> WeatherWindSound;
	/** 0 clear, 1 fair, 2 cloudy, 3 overcast, 4 rain, 5 storm, 6 snow, 7 fog, 8 cloudless (no cloud layer at all: rd.Weather
	 *  only, the rotation never picks it) */
	int32 Weather = 1, WeatherChanges = 0;
	/** the cloud layer hidden for cloudless weather (its visibility is set only when this changes) */
	bool bSkyCloudless = false;
	float WeatherUntil = 0.f, SkyCover = 0.25f, SkyCoverWant = 0.25f, SkyRain = 0.f, SkyRainWant = 0.f, SkyWind = 0.2f, SkyWindWant = 0.2f, SkyFog = 0.f, SkyFogWant = 0.f, SkyApplyT = 0.f, SkyTime = 0.f;
	bool bSkyCold = false, bSkySnowing = false;
	float DayFogDensity = 0.02f, DayFogStart = 0.f, DaySkyLightBase = 1.f;
	/** Graymourne's fog (2026-11-07): 0 away from it, 1 within 700 m of its middle; the day's fog density is raised by
	 *  PortFogBoost times it, and its start (the wilds' 250 m, which left the whole town clear) drawn in to PortFogStart (cm) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Wild") float PortFog = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float PortFogBoost = 8.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float PortFogStart = 500.f;
	/** the weather now (tests, reels) and a weather set (tests): see Weather */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Sky") FString GetSkyState() const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Sky") void SetWeather(int32 Kind, bool bAtOnce);
	static FString WeatherName(int32 Kind);
	/** the weathers (RDSky.cpp's looks and names): the rotation picks among the first NumRotationWeathers; cloudless, the last,
	 *  only by rd.Weather (one count for every table and the console, PR #45's review) */
	static constexpr int32 NumWeathers = 11;
	static constexpr int32 NumRotationWeathers = 10;
	static constexpr int32 WeatherCloudless = 10;
	/** the list of 2026-11-14: a whiteout (snow so thick the world goes white: the cold steppes, the tundra, the arctic, the glaciers,
	 *  the peaks) and a dust storm (the savannahs, the cold steppes, the burned plain, the canyons and mesas), chosen by her region */
	static constexpr int32 WeatherWhiteout = 8;
	static constexpr int32 WeatherDust = 9;
	/** the fog's tint, eased toward the weather's (a whiteout's white, a dust storm's brown) */
	FLinearColor SkyFogTint = FLinearColor::White, SkyFogTintWant = FLinearColor::White;
	/** the list of 2026-11-10 (RDSkyFar.cpp): the far land round her in the wilds, a ring from 0.85 to 80 km of the world model's
	 *  heights and colours under the fog (the horizon's dark strip, 884 sky10); its material (914), how far she goes before it is
	 *  made again (m), how far under the ground it sits (cm), the water's colour; tests: GetFarLandState "made|shown|x|y|ms|builds" */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") TObjectPtr<UMaterialInterface> FarLandMaterial;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") float FarLandRebuildM = 150.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") float FarLandSink = 400.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") FLinearColor FarWaterColor = FLinearColor(0.035f, 0.06f, 0.08f);
	/** (2026-11-10: "if it's distant land, it should be textured the same way it would be textured when approached and
	 *  generated") the far land drawn as the chunks draw the ground: WildGroundMaterial with the chunks' vertex data (the colour
	 *  with rock and snow by its slope, the fields, sand, mud, roads), its normals from its heights, its water in the
	 *  chunks' water materials (its lava only the ground's colour: a far quad is kilometres across); off: FarLandMaterial's flat colour as before. Its forests have no trees: their ground is darkened
	 *  toward FarForestColor by the canopy (times FarForestShare), as a forest's crowns read from afar */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") bool bFarLandAsGround = true;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") FLinearColor FarForestColor = FLinearColor(0.022f, 0.045f, 0.018f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") float FarForestShare = 0.7f;
	int32 FarLandWaterQuads = 0;
	/** the haze over the far land (2026-11-10: the far land 20 to 80 km off took the height fog's own colour, a fixed daylight
	 *  grey, and read as a white strip under the sky, brightest at sunset; 884 horizonprobe measured the land against the sky
	 *  over it). In the wilds' clear air the fog's opacity is capped at FogClearMaxOpacity (the sky atmosphere's own aerial
	 *  perspective, which follows the hour, is the distance's haze), rising to the level's own cap as the weather's fog and
	 *  the port's thicken; FogMaxOpacityWant >= 0 sets it outright (tests). With the sun low the fog's colour dims toward
	 *  FogLowSunShare of the sun's low colour, as the sky by the horizon does (noon's and night's are unchanged) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") float FogClearMaxOpacity = 0.12f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") float FogLowSunShare = 0.35f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") float FogMaxOpacityWant = -1.f;
	float DayFogMax = -1.f;
	/** what the haze is now (tests): "<fog max opacity>|<fog colour r,g,b>|<the level's own cap>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Sky") FString GetHazeState() const;
	/** how far the volumetric clouds are traced (km; the engine's 50 left them ending short of the horizon) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") float SkyCloudTraceKm = 160.f;
	/** the high clouds (2026-11-10, the shipping game: "a disc in the sky that rotates faster than the sky closer to the horizon"):
	 *  no longer a dome turned about the zenith but a flat layer this high (cm), drifting in a straight line along the volumetric
	 *  clouds' wind (their CloudWind) at this speed (cm/s, times 0.4 + the wind), its texture repeating across this (cm: the
	 *  drift is wrapped at it: 890's noise repeats there) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") float SkyHighHeight = 900000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") float SkyHighSpeed = 2500.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sky") float SkyHighTileCm = 2.4e7f;
	double SkyHighDrift = 0.0;
	FVector2D SkyHighWindDir = FVector2D(1.f, 0.f);
	/** the list of 2026-11-10: the castle's inside stair as a stone stair against a wall (E:\temp\stonestairway.jpg): a solid block
	 *  for each step on a coursed wall stepping up under them (RDTownPlan.cpp's CastleStairBuild); the blocks' and the wall's materials
	 *  (914's; none: the stretched wall pieces of before), each one's centimetres a texture repeat */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Town") TObjectPtr<UMaterialInterface> StairBlockMaterial;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Town") TObjectPtr<UMaterialInterface> StairWallMaterial;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Town") float StairBlockUVCm = 120.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Town") float StairWallUVCm = 330.f;
	UPROPERTY(Transient) TObjectPtr<class UProceduralMeshComponent> FarLand;
	FVector2D FarLandAt = FVector2D::ZeroVector;
	int32 FarLandBuilds = 0; float FarLandBuildMs = 0.f;
	void TickFarLand(const FVector& Cam);
	/** the list of 2026-11-22's third phase: the far land computed on a worker (its samples and arrays), only swapped in on the game
	 *  thread (FarLandBuildMs is the swap's time now, FarLandComputeMs the worker's) */
	TSharedPtr<struct FRDFarLandJob, ESPMode::ThreadSafe> FarJob16;
	float FarLandComputeMs = 0.f;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Sky") FString GetFarLandState() const;
	/** the list of 2026-11-10 (RDConsoleCmds.cpp): the weather now (0-7), and whether rd.Weather holds it (no change by itself) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Sky") int32 GetWeather() const { return Weather; }
	UPROPERTY(BlueprintReadWrite, Category = "RandomDungeon|Sky") bool bWeatherHeld = false;
	/** rd.GoTo: out to a major city (the wilds' fast travel at once; from a dungeon back to Brokenspire first) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") bool ConsoleGoTo(const FString& City);
	/** a fast travel that nothing refuses (rd.GoTo, for testing) */
	bool bTravelForced = false;
	/** tests: the wilderness's next encounter is of this kind (a roaming kind's name), at the director's next second, whatever is near */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") void ForceWildEncounter(FName Kind) { ForcedEncounterKind = Kind; }
	FName ForcedEncounterKind;
	// the showcase pilot of the list of 2026-11-04 (RDShow7.cpp): -RDShow7 in the game, StartShow7 in play (a rehearsal; Go
	// empty: at once)
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Show7") void StartShow7(const FString& Go, const FString& Done);
	/** "<on>|<beat>|<time in it>|<log>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Show7") FString GetShow7State() const;
	void TickShow7(float RealDt, APlayerController* PC);
	FString Show7Go, Show7Done, Show7Ready;
	TArray<FString> Show7Log;
	int32 Show7Beat = -1, Show7Step = 0;
	float Show7T = 0.f, Show7Aggro = 0.f, Show7Yaw = 0.f;
	bool bShow7On = false, bShow7Going = false;
	FVector Show7A = FVector::ZeroVector, Show7B = FVector::ZeroVector;
	/** the showcase's save's slot, and a save of that name the player had (put back at the end) */
	FString Show7SaveSlot;
	UPROPERTY(Transient) TObjectPtr<class USaveGame> Show7KeptSave;
	// the reel of 2026-11-18 (RDReel15.cpp): the six towns, a hero each; each hero at tier 3 in the castle; each in an encounter
	// in the wilds. -RDReel15 in the game, StartReel15 in play (a rehearsal; Go empty: at once; bShots: a picture a scene)
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Reel15") void StartReel15(const FString& Go, const FString& Done, bool bShots, int32 FromStage = 0);
	/** "<on>|<stage>|<step>|<time in it>|<rescues>|<the timeline's last line>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Reel15") FString GetReel15State() const;
	void TickReel15(float RealDt);
	void Reel15Mark(const FString& What);
	void Reel15Scene(const FString& Name, const FString& Title, const FString& Line, const FString& Say);
	void Reel15End();
	void Reel15Shot(const FString& Name);
	void Reel15Switch(int32 K);
	FString Reel15Kit(int32 K, int32 Part);
	void Reel15Camera(float Dt, float Pitch);
	/** the scene's caption, drawn at the top of the screen (ARDHUD::DrawReelCaption); no UPROPERTY: a package staged on an
	 *  earlier cook (-SkipCook) reads the generator's properties unversioned, and a new one made it crash at its start) */
	FString ReelCaptionTitle, ReelCaptionLine;
	int32 Reel15Sub = 0;
	float Reel15T = 0.f, Reel15Ready = 0.f, Reel15Aggro = -1.f, Reel15Lose = -1.f, Reel15Down = -1.f, Reel15Yaw = 0.f;
	bool bReel15Travel = false, bReel15Set = false;
	FVector Reel15A = FVector::ZeroVector, Reel15B = FVector::ZeroVector;
	TArray<FVector> Reel15Path;
	TArray<int32> Reel15Rooms;
	TArray<TWeakObjectPtr<ARDMonster>> Reel15Foes;
	FString Reel15SceneName;
	TSet<FString> Reel15Biomes;
	// the swarms and birds round her, the wild animals (RDWildLife.cpp)
	void TickWildLife(float Dt, const FVector& Her);
	struct FRDSwarmInst { int32 Def = -1; TWeakObjectPtr<class UNiagaraComponent> C; FVector At = FVector::ZeroVector; };
	TArray<FRDSwarmInst> SwarmInsts;
	UPROPERTY(Transient) TArray<TObjectPtr<class ARDWildAnimal>> WildAnimals;
	float WildLifeT = 0.f;
	int32 AnimalsSpawned = 0, AnimalsFled = 0, SwarmsSpawned = 0;
	/** "animal|<kind>|<x>|<y>|<z>|<state>|<flee cm>|<fled times>", "swarm|<name>|<x>|<y>|<z>|<layer>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild") TArray<FString> GetWildLifeLines() const;
	/** tests: an animal of a kind put at a point (it stands there) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") class ARDWildAnimal* SpawnWildAnimalAt(FName Kind, FVector At);
	/** the list of 2026-11-07 (RDWildLife.cpp): an animal killed (its things dropped as a harvest, its kind's place kept empty
	 *  WildAnimalRespawnSeconds before another comes, the body gone after WildCorpseSeconds); her blow's animals in its reach
	 *  and arc; the first animal on a bolt's way this frame (its share of the way, where it met it) */
	void OnWildAnimalKilled(class ARDWildAnimal* A);
	int32 HitWildAnimalsInArc(const FVector& L, const FVector& Fw, float Reach, float MinCos, float Dmg, FName Sound);
	class ARDWildAnimal* WildAnimalOnSegment(const FVector& A, const FVector& B, float Pad, float& OutT, FVector& OutAt) const;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float WildAnimalRespawnSeconds = 120.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float WildCorpseSeconds = 90.f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Wild") int32 AnimalsKilled = 0;
	/** a killed kind's place empty until then (its WildFauna index, the game time it may come again) */
	TArray<TPair<int32, float>> AnimalRespawns;
	/** what the last killed animal gave (tests) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Wild") TArray<FName> LastAnimalDrops;
	/** the town's list (RDTown7.cpp): a garden harvested, the oven's crafting, a table's food taken */
	bool TownHarvestGarden(ARDSection* S, int32 Garden);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire7") bool IsGardenRipe(int32 Garden) const;
	/** music's scene (RDDungeonGenerator.cpp): the set the wandering music plays now, when it changes next */
	FName MusicSceneKey;
	float MusicRotateAt = -1.f, MusicPendingAt = -1.f;
	int32 MusicRotations = 0;
	FName MusicSceneFor() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Sound") FString GetMusicScene() const { return FString::Printf(TEXT("%s|%d|%.0f"), *MusicSceneKey.ToString(), MusicRotations, MusicRotateAt); }
	/** tests: the next track at once (as its time would) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Sound") void RotateMusicNow() { MusicRotateAt = 0.f; }

	// ---- the town's lit buildings (the user's of 2026-11-02: "when a building has someone in it, it should have a torch lit,
	// unless the NPC is sleeping"): each building's torches and their flames burn while someone awake is inside it (the
	// castle's always); checked once a second
	void TickTownLights(float Dt);
	/** "<building>|<kind>|<lit 0/1>|<lights>|<awake inside>|<asleep inside>" for every building with lights */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") TArray<FString> GetTownLightLines() const;
	TMap<int32, TArray<TWeakObjectPtr<USceneComponent>>> TownBldLights;
	TMap<int32, bool> TownBldLit;
	TMap<int32, FIntPoint> TownBldPeople;                 // (awake, asleep inside: as last counted)
	TWeakObjectPtr<ARDSection> TownLightsFor;
	float TownLightsT = 0.f;

	// ---- Brokenspire's runtime (RDTownGame.cpp)
	void BeginTownPlay();
	void AfterTownBuilt();
	void TickTown(float Dt, APlayerController* PC);
	void TickTownPanel(APlayerController* PC);
	void BuildTownLines();
	/** F in the town: someone near, a service, the gate, a boarded door (""; nothing of the town's) */
	FString TownInteract(const FVector& From);
	FString TownDescribe(const FVector& From) const;
	/** the list of 2026-11-04's things of the town (RDTown7.cpp): a table's food, a garden, an oven, the gate's levers */
	FString TownThingInteract(const FVector& From);
	FString TownThingDescribe(const FVector& From) const;
	/** the list of 2026-11-10: food on the prep tables of the castle and the game's other dungeons (914 sets it with the bare table
	 *  and the town's food pieces): laid in every set as in a town, taken with F into her pack */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") bool bTableFood = false;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List10") int32 TableFoodTaken = 0;
	const ARDSection* TableFoodNear(const FVector& From, int32& OutIndex) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List10") FString TableFoodDescribe(const FVector& From) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List10") FString TableFoodTake(const FVector& From);
	/** where the food not yet taken lies on the tables of every set built (tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List10") TArray<FVector> GetTableFoodPoints() const;
	// ---- the list of 2026-11-10's second phase (RD/RDList10b.cpp)
	/** "when the tier boss appears, a teleporter back to the first dungeon room or to brokenspire should spawn there with him": a pad
	 *  in his room as he is set (PlaceBoss); F takes her to the first room, [G] turns it to the town (a level with a way back) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") bool bBossPorts = false;
	TMap<int32, FVector> BossPorts;
	UPROPERTY(Transient) TMap<int32, TObjectPtr<class ARDTeleporter>> BossPortActors;
	UPROPERTY(BlueprintReadWrite, Category = "RandomDungeon|List10") int32 BossPortChoice = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List10") int32 BossPortUses = 0;
	void PlaceBossPort(int32 Tier, class ARDSection* S, int32 Room, const TArray<FVector>& Free, const TArray<FVector>& Spots);
	int32 BossPortNear(const FVector& From, float Reach = 170.f) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List10") FString BossPortDescribe(const FVector& From) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List10") FString BossPortUse(const FVector& From);
	/** tests: "tier|x|y|z" of every boss's teleporter */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List10") TArray<FString> GetBossPortLines() const;
	bool CanBossPortToTown() const;
	void ClearBossPorts();
	/** "a library's bookshelves should contain either scrolls of that tier or below or crafting components for scrolls of that tier or
	 *  below, could also contain tomes": a library's shelves are searched with F (each once: ShelvesSearched by set and shelf) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") bool bLibraryShelves = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") float ShelfLootChance = 0.7f;
	TSet<FIntVector> ShelvesSearched;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List10") int32 ShelvesSearchedCount = 0;
	const ARDSection* ShelfNear(const FVector& From, int32& OutIndex) const;
	/** what a set's shelf holds (the rules: scrolls, the scrolls' recipe parts and tomes, of its tier or below) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List10") TArray<FName> ShelfLootOf(FIntPoint Section, int32 Index) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List10") FString ShelfDescribe(const FVector& From) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List10") FString ShelfSearch(const FVector& From);
	/** tests: "sx|sy|index|x|y|z|room|searched" of every library shelf of the sets built */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List10") TArray<FString> GetShelfLines() const;
	/** "if the player walks under a structure that blocks sight of her, make the structure see-through": the town's instanced pieces
	 *  between her and the camera (or where its boom would put it), but what she stands on, are hidden while they stand there
	 *  (their collision kept by a hidden copy that only the camera passes through) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") bool bSeeThrough = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") float SeeThroughHold = 0.5f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List10") int32 SeeThroughTotal = 0;
	struct FSeeHidden { TWeakObjectPtr<class UInstancedStaticMeshComponent> C; int32 I = -1; FTransform T; float Until = 0.f; TWeakObjectPtr<class UInstancedStaticMeshComponent> Proxy; int32 ProxyI = -1; };
	TArray<FSeeHidden> SeeHidden;
	TMap<TWeakObjectPtr<class UInstancedStaticMeshComponent>, TWeakObjectPtr<class UInstancedStaticMeshComponent>> SeeProxies;
	TMap<TWeakObjectPtr<class UInstancedStaticMeshComponent>, TArray<int32>> SeeProxyFree;
	/** a set's instanced pieces by their boxes on a 4 m grid, made once a set (a town's roofs have no collision: no trace finds them) */
	struct FSeeRef { TWeakObjectPtr<class UInstancedStaticMeshComponent> C; int32 I = -1; FBox B; };
	struct FSeeGrid { TMap<FIntPoint, TArray<int32>> Cells; TArray<FSeeRef> Refs; };
	TMap<TWeakObjectPtr<class ARDSection>, FSeeGrid> SeeGrids;
	FSeeGrid& SeeGridOf(class ARDSection* S);
	void HideSeeThrough(class UInstancedStaticMeshComponent* C, int32 Inst);
	float SeeThroughClock = 0.f, SeeThroughNext = 0.f;
	void TickSeeThrough(float Dt);
	void ClearSeeThrough();
	/** tests: how many pieces are hidden now, and each "mesh|x|y|z" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List10") TArray<FString> GetSeeThroughLines() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List10") int32 GetSeeThroughCount() const { return SeeHidden.Num(); }
	// ---- the list of 2026-11-10's fourth phase (RD/RDList10d.cpp)
	/** what each role says (914 lines: SourceArt/brokenspire/role_lines_*.json, SourceArt/heaven/role_lines.json) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") TArray<FRDRoleLines> RoleLines;
	/** a townsperson's pool of lines: its def's and its role's for the town she is in */
	void TownLinePool(int32 InDef, ERDTownRole InRole, TArray<FString>& Out) const;
	/** "if an NPC is supposed to be sleeping at night, have them sleep in their beds": every sleeper given a bed of its building
	 *  (the town's beds where they stand; one put on a free tile where there are fewer than its sleepers), lying in it at night on
	 *  its def's work clip "Sleep" (914 sleep) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") bool bTownBeds = false;
	void AssignTownBeds(class ARDSection* S);
	/** "there should be more children in town, and they are supposed to be asleep at night" and "the town should be 25% more
	 *  populated with more children as the population increases. leave the number of buildings the same": a lived-in home with a
	 *  resident has a second grown-up one time in HomeSecondShare and a child one time in HomeChildShare, the children at home (they
	 *  go in at evening and sleep); the square's three children are left out when homes have children */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") bool bMorePeople = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") float HomeSecondShare = 0.2f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") float HomeChildShare = 0.33f;
	/** tests: "posts|<n>" "adults2|<n>" "homekids|<n>" "squarekids|<dropped>" "beds|<recorded>|<made>|<sleepers>|<given>" and per
	 *  townsperson "folk|<i>|<role>|<asleep>|<in bed>|<bed x>|<y>|<z>|<clip>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List10") TArray<FString> GetTownSleepLines() const;
	// ---- the list of 2026-11-10's sixth phase (RD/RDWild10.cpp)
	/** "the buildings in the wilderness do not have an interior and there is no way to get inside": the wilds' houses laid as the
	 *  village houses' open copies (WildPieces' "house" and "farmhouse" entries, 916), at WildHouseScale, each with its doors on
	 *  their hinges (F), a floor over the ground, its furniture, a lamp, its plants cleared and a plinth where the ground falls */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") bool bWildHouseInsides = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") TArray<FRDWildHouse> WildHouses;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") TObjectPtr<UMaterialInterface> WildPlinthMaterial = nullptr;
	/** a house with its door, floor and furniture; false if the mesh is not a wild house's */
	bool FitWildHouse(ARDWildChunk* C, UStaticMeshComponent* Sm, uint32 Salt);
	// ---- the list of 2026-11-20's seventh phase (RDList15f.cpp): the villages' terraces
	/** a village's houses and square on level pads cut into the slope, its retaining walls and buttresses; 8 to 15 houses (the
	 *  world's: FRDWildWorld::bTerraces15, a new world's version) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bVillageTerraces15 = false;
	UPROPERTY(Transient) TObjectPtr<UStaticMesh> TerraceCube15 = nullptr;
	void LayTerraceWalls15(ARDWildChunk* C, const struct FRDWTerraces& T);
	int32 TerraceWalls15 = 0, TerraceButtresses15 = 0;
	// ---- the list of 2026-11-20's eighth phase (RDList15g.cpp): the villages lived in
	/** each village house a household of 2 to 5 (items 27, 28: "the small villages are not inhabited"): their beds, their day (the farm
	 *  folk's: work, home, asleep), their lines; dormant beyond 250 m */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bVillageFolk15 = false;
	/** the villagers' lines, "<role>|<line>" (villager, villagewoman, child, any; {village} its name), from SourceArt/wilderness/village15.json */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TArray<FString> WildVillageLines15;
	TArray<TWeakObjectPtr<class ARDTownsfolk>> WildVillageFolk15;
	float VillageFolkCheckAt15 = 0.f;
	/** the households waiting to be laid, one a frame after the village's pieces (PR #100's review: a village's 30 to 75 people in one
	 *  frame were a hitch, and the square's props, laid after them, came down on them) */
	struct FVillageHouseQ15 { TWeakObjectPtr<ARDWildChunk> Chunk; FRDWildPlace P; int32 HouseK = 0; FVector RoomC = FVector::ZeroVector; };
	TArray<FVillageHouseQ15> VillageHouseQueue15;
	void LayVillageHousehold15(ARDWildChunk* C, const FRDWildPlace& P, int32 HouseK, int32 HouseIdx);
	/** once a second: a wild person (a farm's, a village's, a traveller, a structure's) beyond 250 m of her stops its day (its body still
	 *  posed when seen); one a frame from the households' queue */
	void TickVillageFolk15();
	/** a test's: the villagers of the village named, "title|house|x|y|z|asleep|in bed|indoors|dormant|beds of the house" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List15") TArray<FString> GetVillageFolk15(const FString& Village) const;
	/** the walls laid, "village|x|y|z bottom|z top|pad z|land z|land x|land y" (cm; the land read 1.2 m out from the pad's edge) */
	TArray<FString> TerraceWallLines15;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") TArray<FString> GetTerraceWallLines15() const { return TerraceWallLines15; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") TArray<FString> GetVillageTerraces15(FVector2D AtM) const;
	// ---- the list of 2026-11-20's ninth phase (RDList15h.cpp): the caves under the landmark towers (item 23)
	/** the cave level (935): every landmark tower's cave is this one level, its key ("cave:<i>_<j>", the tower's 6 km cell) and its
	 *  tier (the region's, FRDWildWorld::TierAt at the tower) read from the game instance as play begins; all its tiers are that one
	 *  game tier (DungeonTierBase tier - 1, DungeonTierCap tier); no key chain, final boss, arena, cells or bosses' unique rewards */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bCave15 = false;
	/** the cave's monsters: the wilds' kinds of its game tier whose names hold none of these parts (people with firearms, machines) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TArray<FString> CaveExclude15;
	/** a test's or a play from the editor's: the tier when no tower sent her (0: 1) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") int32 CaveDefaultTier15 = 1;
	/** the wilds (brokenspire): the cave level, the mouth laid at every landmark tower's foot (a rock arch and its dark inside) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") FString CaveLevel15;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TObjectPtr<UStaticMesh> CaveMouthMesh15 = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") FVector CaveMouthScale15 = FVector(1.f);
	/** the mouth's frame: at the tower's foot (CaveFootRadius15 out from its middle, between two buttresses at CaveGapDeg15 of the
	 *  tower's own frame), its X out from the tower; the arch's place and turn in it, the dark slab's place and scale (a cube's) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float CaveFootRadius15 = 1870.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float CaveGapDeg15 = 36.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") FVector CaveMouthOffset15 = FVector::ZeroVector;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float CaveMouthYaw15 = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") FVector CaveDarkOffset15 = FVector::ZeroVector;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") FVector CaveDarkScale15 = FVector(0.2f, 3.f, 4.f);
	/** the arch is half an arch (the pack's is a quarter round): its mirror across the mouth's middle closes it; the dark piece's turn
	 *  (a cylinder stood on its side across the mouth: pitch 90) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bCaveMouthMirror15 = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") FRotator CaveDarkTurn15 = FRotator::ZeroRotator;
	// ---- the list of 2026-11-22's caves (RDCave16.cpp, 945): laid by a planner of their own and drawn with the Hyper kit
	/** the cave level: every set a cave of the kit's rooms joined by winding tunnels on the tile grid, not the dungeon's rooms and
	 *  hallways (Plan, the shell, the furnishing and the seals take the cave's ways) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") bool bCave16 = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FRDCaveRoom16> CaveRooms16;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FRDCaveTunnel16> CaveTunnels16;
	/** the kit's cap: an opening no tunnel uses, a tunnel's dead end, a set's way into a shut tier */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TObjectPtr<UStaticMesh> CaveCap16 = nullptr;
	/** rooms a set (the start set: its first the large room at the middle), by the tier's depth: X at tier 1 to Y at tier 5 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") FIntPoint CaveRoomsPerSet16 = FIntPoint(4, 7);
	/** the share of the rooms' joins beyond the tree that makes every room reachable (loops) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") float CaveLoopShare16 = 0.2f;
	/** how far a room's floor may lie below the set's (cm; a level of the set: the stairs join two, else a tunnel slopes) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") float CaveLevelDrop16 = 428.f;
	/** a fill light over each room (phase 8's: the kit's torches and god rays come with the dressing) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") float CaveRoomLight16 = 3000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") FLinearColor CaveLightColor16 = FLinearColor(0.75f, 0.85f, 1.f);
	// ---- phase 9: the caves dressed (RDCave16.cpp)
	/** the kit's PCG dressing as measured (945 dressing, level), scattered by the game in play over each set (traced onto its floors and
	 *  roofs) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FRDCaveDress16> CaveDress16;
	/** the kit's wall torch: its mesh, its fire's effect and the fire's and light's places on it (BP_WallTorch's), the light's candelas;
	 *  a torch on every wall-light point of a room and one on a tunnel's wall every CaveTunnelTorchEvery16 cm, sides taken in turn */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TObjectPtr<UStaticMesh> CaveTorchMesh16 = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TObjectPtr<UNiagaraSystem> CaveTorchFire16 = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") FVector CaveTorchFireAt16 = FVector(0, -29, 109);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") FVector CaveTorchLightAt16 = FVector(0, -45, 80);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") float CaveTorchCandelas16 = 250.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") FLinearColor CaveTorchColor16 = FLinearColor(1.f, 0.62f, 0.3f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") float CaveTunnelTorchEvery16 = 2000.f;
	/** the kit's god ray (its plane and animated material) under each room's roof hole, turned as the example's sun; a cool light down
	 *  the shaft */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TObjectPtr<UStaticMesh> CaveGodRayMesh16 = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TObjectPtr<UMaterialInterface> CaveGodRayMaterial16 = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") FRotator CaveGodRayTurn16 = FRotator(-48.f, -36.f, 0.f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") FVector CaveGodRayScale16 = FVector(1.f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") float CaveGodRayCandelas16 = 1500.f;
	/** containers a room by its walls (the castle's chest, barrel and crate pieces): X to Y */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") FIntPoint CaveContainers16 = FIntPoint(1, 3);
	// ---- phase 10: the caves' treasures (RDCave16b.cpp; 945 items, treasure16.json)
	/** the caves' own items (on every map): drawn by a container only in a cave, and there a cave's gear, rings, tomes and scrolls come
	 *  from these alone (its potions, food, repair items and materials as anywhere) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FName> CaveItems16;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FRDCaveRegion16> CaveRegions16;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FRDCaveNode16> CaveNodes16;
	/** the darksight's light on her (candelas) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") float CaveDarksightCandelas16 = 60.f;
	/** items made at the anvil whatever their kind (the caves' linings: a buff's vehicle of kind Healing, not the alchemist's) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FName> AnvilMade16;
	/** for the tests: "<station>|<refusal>" of an item's recipe as the game reads it now ("none|..." without a recipe) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") FString GetCaveCraft16(FName Item) const;
	/** for the tests: what a store of this level sells now */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") TArray<FName> GetTownStock16() const { return TownStock(); }
	/** phase 11: the socket stones (item -> its bonus); a weapon or a set of armour holds one (URDCombatComponent::SetSocket16) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TMap<FName, FRDSocket16> SocketStones16;
	// ---- phase 12: the caves' weapons (RDCave16d.cpp)
	/** a found weapon's own look (its item -> a material on every slot of its mesh: the shard blade's crystal, the bones' dark) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TMap<FName, TObjectPtr<UMaterialInterface>> WeaponLooks16;
	/** a found weapon mended only by its things (no repair item mends it) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TMap<FName, FRDMend16> MendOnly16;
	/** the lightless bow: its shot leaves her stealth on and its hit turns no monster toward her while she is hidden */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FName> Lightless16;
	/** the rubble across a set's side tunnel: broken by one blow of these weapons (the miner's pick), or RubbleHeroHits16 blows of
	 *  RubbleHero16's (the Warrior) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FName> RubbleBreakers16;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") FName RubbleHero16 = TEXT("Warrior");
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") int32 RubbleHeroHits16 = 3;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<TObjectPtr<UStaticMesh>> RubbleMeshes16;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") FVector2D RubbleScale16 = FVector2D(0.35f, 0.5f);
	/** the share of the sets with a side tunnel that get its rubble and the cache behind it */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") float RubbleShare16 = 1.f;
	/** the lost adventurers' blades (each cave picks one by its key) and the skeleton they lie by */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FName> LostBlades16;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TObjectPtr<UStaticMesh> LostSkeleton16 = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") FRotator LostSkeletonTurn16 = FRotator::ZeroRotator;
	/** the rubble broken this run (a set's coord and its rubble's index), the lost blade laid this run */
	TSet<FIntVector> RubbleCleared16;
	bool bLostBladeLaid16 = false;
	/** set while the lightless bow's arrow strikes with her hidden: the monster takes the blow and is not roused */
	bool bQuietHit16 = false;
	// ---- phase 13: the caves' armour, breath and the flooded side tunnel (RDCave16e.cpp)
	/** what a set does while worn (its item, every band) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TMap<FName, FRDArmourPerk16> ArmourPerks16;
	/** her breath under water (s), the share of her hit points the water takes a second once it is gone, her speed under it */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") float Breath16 = 15.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") float DrownShare16 = 0.08f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") float UnderwaterSpeed16 = 0.6f;
	/** the share of the side tunnels to nowhere flooded (the others closed by rubble), the water's material */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") float FloodShare16 = 0.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TObjectPtr<UMaterialInterface> FloodWater16 = nullptr;
	/** the drowned knight's four pieces (each cave holds one, by its key, in its flooded tunnel's dry end) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FName> DrownedPieces16;
	/** whether a point (her head) is under a flooded tunnel's water */
	bool UnderWater16(const FVector& Head) const;
	FName DrownedPieceOf16() const;
	// ---- phase 14: the charm slot, the Echo, the lucky stone, the cursed relics (RDCave16f.cpp)
	/** a charm's good and cost (its item, a ring of kind Charm) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TMap<FName, FRDCharm16> Charms16;
	bool IsRelicLifted16(FName Relic) const;
	int32 LiftPrice16(FName Relic) const;
	/** a temple's lines: "lift|<relic>|<price>" for each cursed relic she carries not lifted yet */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") TArray<FString> GetLiftLines16() const;
	/** a temple's lifting: the relic's cost gone for good, for its price */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") bool TownLiftCurse16(const FString& Arg);
	/** the Echo's pings: monsters beyond the maps' own sensing and within the ring's metres */
	void EchoPings16(const FVector& Her, float SenseCm, TArray<FVector2D>& Out) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") int32 GetEchoPings16(FVector Her) const { TArray<FVector2D> P; EchoPings16(Her, 2500.f, P); return P.Num(); }
	// ---- phase 15: rewards that last (RDCave16g.cpp)
	/** the cave painting's decal, the share of the sets that hold one */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TObjectPtr<UMaterialInterface> PaintingDecal16 = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") float PaintingShare16 = 0.35f;
	/** the most caves one painting marks (the region's nearest the painted one) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") int32 PaintingCaves16 = 12;
	/** the fossil sets: "<region>|<fossil>|<fossil>|<fossil>"; amber may stand in for one; a set's lasting hit points or mana */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FString> FossilSets16;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") FName FossilAmber16;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") int32 FossilGain16 = 15;
	bool PaintingNear16(const FVector& From, float Reach, FVector* OutAt = nullptr) const;
	/** a painting within F's reach (Reach) and nearer than everything else F reaches: the nearest door or container (OtherD), every
	 *  pile, anvil and station; the prompt and F both ask it */
	bool PaintingFirst16(const FVector& From, float Reach, float OtherD) const;
	FString StudyPainting16(const FVector& From, float Reach);
	/** for the tests: "studied|<cave>|<region>|applied/waiting", "cave|<i>|<j>" known, "painting|<set x>|<y>|<x>|<y>|<z>" laid */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") TArray<FString> GetPaintings16() const;
	void ApplyPaintings16();
	/** for the tests: a painting as if studied in the cave under the tower nearest (Xm, Ym) (metres): "cave:<i>_<j>|<region>|<biome>" or "" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") FString DebugPaintingNear16(float Xm, float Ym);
	/** for the tests: the map's marks the paintings made this session taken off again (the paintings' lists are the test's to put back) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") int32 ForgetPaintingMarks16();
	TArray<int32> PaintingMarked16;
	void DrawKnownCaves16(TFunctionRef<void(const FVector2D&)> Draw) const;
	int32 PaintedApplied16 = 0;
	/** the share of a cave's containers with loot that hold an ancient tablet (a recipe or a spell the old people cut in stone) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") float TabletShare16 = 0.12f;
	FName CaveTablet16(FIntPoint Section, int32 Index) const;
	// ---- phase 16: the caves and the wilds (RDCave16h.cpp)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") FName CaveMapItem16;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") FName CaveFragmentItem16;
	/** the share of a cave's containers with loot that hold a map besides, a fragment besides; a set beyond the first with a lost traveller */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") float CaveMapShare16 = 0.05f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") float CaveFragmentShare16 = 0.04f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") float TravellerShare16 = 0.25f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FString> TravellerNames16;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FString> TravellerLines16;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") int32 RescueGold16 = 120;
	/** a map's place within this of its tower; a contract's lair within this of a tower flees into its cave */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") float CaveMapKm16 = 6.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") float ContractCaveKm16 = 5.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") float TowerRevealM16 = 3000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") int32 TowerChestItems16 = 3;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") int32 TowerChestGold16 = 150;
	static constexpr int32 CaveMouthIdBase16 = (1 << 29) + (1 << 28) + (1 << 27) + (1 << 26);
	static int32 CaveMouthIdOf16(FIntPoint Cell);
	int32 UseCaveThing16(FName Item);
	FName CaveLinkThing16(FIntPoint Section, int32 Index) const;
	class ARDPrisoner* TravellerNear16(const FVector& From, float Reach, ARDSection** OutS = nullptr) const;
	bool TravellerFirst16(const FVector& From, float Reach, float OtherD) const;
	FString FreeTraveller16(const FVector& From, float Reach);
	void TickCaveContract16();
	void OnCaveContractKilled16(ARDMonster* Monster, bool bHers);
	void CaveBossKey16();
	bool CaveMouthPlace16(int32 Id, FRDWildPlace& Out) const;
	void AddCaveMouths16(TArray<FRDWildPlace>& Out) const;
	void TickCaveLinks16(float Dt, const FVector& Her);
	void AddRescuedSettlers16(int32 CampId, const FVector2D& Fire, float Yaw, TArray<TWeakObjectPtr<AActor>>& Folk);
	void TickTowerLift16(const FVector2D& H2);
	bool LayTowerTop16();
	void DropTowerTop16();
	FString TowerDescribe16(const FVector& From, float Reach) const;
	FString TowerInteract16(const FVector& From, float Reach);
	/** for the tests: "map|", "contract|", "traveller|", "mouth|", "key|", "climbed|", "towerchest|" records, "door|", "top|", "chest|",
	 *  "beast|", "lost|<set x>|<y>|<x>|<y>|<z>|<name>|<freed>" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") TArray<FString> GetCaveLinks16() const;
	/** for the tests: the broken tower nearest (Xm, Ym) (metres): "<i>|<j>|<x>|<y>|<metres off>", or "" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") FString DebugNearestTower16(float Xm, float Ym) const;
	// ---- phase 17: gold and trade goods (RDCave16i.cpp)
	/** the caves' things besides a container's draw: "<item>|<share>" each on a stream of its own */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FString> CaveBesides16;
	/** the trade goods' worth when sold ("<item>|<gold>", a quarter more a game tier); the city whose collector pays CollectorMul16 times */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FString> TradeGoods16;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") FString CollectorTown16;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") float CollectorMul16 = 2.f;
	/** "<result>|<material>|<count>|<city>|<gold>": what one city's smith alone forges from a cave's material */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FString> SmithWorks16;
	void CaveBesidesOf16(FIntPoint Section, int32 Index, TArray<FName>& Out) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Cave16") bool IsCollectorTown16() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Cave16") int32 TradeValue16(FName Item) const;
	FName SmithWorkOf16(const FString& Result) const;
	void AddSmithWorks16(TFunctionRef<void(const FString& Act, const FString& Label, const FString& Tag, const FString& Detail, bool bOn, const FString& Arg)> Add) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") bool TownForge16(const FString& Result);
	/** for the tests: "town|<name>|<collector>", "value|<item>|<gold>", "work|<result>|<band made>" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") TArray<FString> GetTrade16() const;
	/** for the tests: the marks and found ids the cave links made this session taken off again */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") int32 ForgetCaveLinkMarks16();
	TArray<int32> CaveLinkMarked16;
	bool bTowerSaveDue16 = false;
	void GatherPlacesAndSites16(const FVector2D& At, double RadiusM, TArray<FRDWildPlace>& Out) const;
	bool CaveMapSpot16(const FRDWildPlace& P, FVector2D& Spot) const;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Cave16") int32 TowerMarked16 = 0;
	float CaveLinkLook16 = 0.f;
	bool bCaveContractLaid16 = false;
	TWeakObjectPtr<ARDMonster> CaveContractBeast16;
	int32 CaveContractId16 = -1;
	FVector TowerDoorAt16 = FVector::ZeroVector, TowerDoorOut16 = FVector::ForwardVector;
	FIntPoint TowerDoorCell16 = FIntPoint(INT32_MAX, INT32_MAX), TowerTopCell16 = FIntPoint(INT32_MAX, INT32_MAX);
	float TowerTopZ16 = 0.f, TowerTopRadius16 = 0.f;
	TArray<TWeakObjectPtr<USceneComponent>> TowerComps16;
	int32 TowerChestId16 = -1; FVector TowerChestAt16 = FVector::ZeroVector; TWeakObjectPtr<UStaticMeshComponent> TowerChestMesh16;
	FString LastTowerChest16;
	/** the Angel Tokens a cave's last boss left this run (for the tests) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Cave16") int32 CaveTokens16 = 0;
	/** "fossil|<region>|<1: whole>|<n of m>" for each set she carries a piece of */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") TArray<FString> GetFossilLines16() const;
	/** a temple's trade of a fossil set: "<region>|hp", "|mana" or "|token" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") bool TownFossilTrade16(const FString& Arg);
	void AddFossilTrades16(TFunctionRef<void(const FString& Act, const FString& Label, const FString& Tag, const FString& Detail, bool bOn, const FString& Arg)> Add) const;
	/** gold she finds (more with a gilded relic), as AddGold */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") void AddFoundGold16(int32 Amount, const FString& Why = TEXT(""));
	/** a harvest's things more by the lucky stone */
	void LuckyHarvest16(TArray<FName>& Things) const;
	/** the sets whose drowned knight's piece is laid this run; whether one is laid at all this run */
	TSet<FIntPoint> DrownedLaid16;
	bool bDrownedLaid16 = false;
	/** her blow from From along Fw with a weapon (its gear key) of Reach: rubble in front of her struck */
	void StrikeRubble16(const FVector& From, const FVector& Fw, float Reach, FName Gear);
	/** the lost blade this cave picks */
	FName LostBladeOf16() const;
	/** a pile taken: a lost blade among its things is recorded for the cave she is in (laid there no more) */
	void NoteLostBladeTaken16(const TArray<FName>& Things);
	/** a found weapon nothing but its own things mend (the anvil, the smith and the repair items pass it by) */
	bool IsMendOnly16(FName WeaponItem) const { return !WeaponItem.IsNone() && MendOnly16.Contains(WeaponItem); }
	/** for the tests: "rubble|<i>|<x>|<y>|<z>|<cleared 0/1>|<hits>|<cache x>|<y>|<z>" of a set; "lost|<blade>|<x>|<y>|<z>" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") TArray<FString> GetCaveRubble16(FIntPoint Section) const;
	/** for the tests: whether the tile under a point is walkable (its set's tiles, the blocked ones not) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") bool IsWalkableAt16(FVector At) const;
	/** whether a container may hold it here (the caves' own items, their regions' items) */
	bool CaveItemAllowed16(const FRDItemDef& It) const;
	/** the cave's region (by the tower's biome the game instance keeps; -1: none known) and its name for a test */
	int32 CaveRegion16() const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") FString GetCaveRegion16() const;
	/** the veins and growths laid this session ((set x, set y, n): a set built again lays none twice) */
	TSet<FIntVector> CaveNodesLaid16;
	/** a test's: a set's veins and growths, "node|<item>|x|y|z|<on the wall>" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") TArray<FString> GetCaveNodes16(FIntPoint Section) const;
	/** a test's: whether a container's draw at this tier would hold the item here (its kind, the cave's rules) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") bool CaveMayDraw16(FName Item) const;
	/** a test's: the set at the start sets the region as the game instance would (a tower's biome) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") void SetCaveBiome16(const FString& Biome);
	/** a test's: the set's dressing, "torches|<n>", "godrays|<n>", "dress|<mesh>|<instances>", "containers|<n>" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") TArray<FString> GetCaveDressing16(FIntPoint Section) const;
	/** a test's: where a tier's boss would stand now ("<section x>|<section y>|<room>|<floor z>|<her distance>") and the rooms it was chosen
	 *  from (same lines after "cand|"); the caves take the deepest room (its floor lowest, then the farthest from her) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") TArray<FString> GetBossRoomPick16(int32 Tier) const;
	/** a test's: the set's pieces, "room|<index>|<kind>|x|y|z|yaw|<tiles>", "tunnel|<kind>|<its room index>|<from>|<to>|<length cm>|<pieces>|
	 *  x,y,z;x,y,z;..." (the tunnel's centreline every 2 m on its floor; from / to a room's index, a portal's -1 - its index) and
	 *  "cap|x|y|z|yaw" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") TArray<FString> GetCavePieces16(FIntPoint Section) const;
	/** a test's: the tiles of a set she can stand on, "x|y|z|owner" (world cm, the floor's height; the owner: its Rooms index, a
	 *  tunnel's its own Junction entry, as GetCavePieces16's tunnel lines say) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") TArray<FString> GetCaveTiles16(FIntPoint Section) const;
	/** a test's: the set seen from above (an orthographic capture Height cm over its floor looking down, the kit's colours unlit:
	 *  the roofs over the camera are not drawn), written to a PNG; false if it could not be */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Cave16") bool CaptureAbove16(FIntPoint Section, const FString& Folder, const FString& File, float Height = 700.f, int32 Pixels = 2048);
	TWeakObjectPtr<class UStaticMeshComponent> CaveMouthB15;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TObjectPtr<UStaticMesh> CaveDarkMesh15 = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TObjectPtr<UMaterialInterface> CaveDarkMaterial15 = nullptr;
	TWeakObjectPtr<class UStaticMeshComponent> CaveMouth15, CaveDark15;
	/** the mouth's place, its way out (unit, cm) and its tower's cell; set with the landmark */
	FVector CaveMouthAt15 = FVector::ZeroVector, CaveMouthOut15 = FVector::ForwardVector;
	FIntPoint CaveCell15 = FIntPoint(INT32_MAX, INT32_MAX);
	void LayCaveMouth15(class UStaticMeshComponent* Tower, const FVector2D& SiteM);
	bool CaveMouthNear15(const FVector& From, float Reach = 450.f) const;
	/** the mouth takes F: within reach and nearer than every other wild thing F reaches (PR #101's review) */
	bool CaveMouthFirst15(const FVector& From, float Reach = 450.f) const;
	/** into the tower's cave: her way back before its mouth, its key and tier into the game instance (DescendToCatacombs) */
	bool EnterCave15();
	/** the cave level's key and tier from the game instance (BeginPlay, before anything reads them) */
	void ApplyCave15();
	/** the cave's kinds at a game tier: the wilds' kinds whose band holds it (else the nearest tier below with any), none excluded */
	void CaveKinds15(int32 GameTier, TArray<int32>& Out) const;
	mutable int32 CaveKindsTier15 = -1;
	mutable TArray<int32> CaveKindsCache15;
	/** the landmarks' cell (one tower in each square of this side, m): the towers' placing and the caves' keys */
	static constexpr double WildLandmarkCellM = 6000.0;
	/** tests: "on|x|y|z|out x|out y|key|tier" of the mouth standing, or "off" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") FString GetCaveMouth15() const;
	/** tests: into the cave of the tower standing, as F at its mouth does (false: none, or refused) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List15") bool DebugEnterCave15() { return EnterCave15(); }
	// ---- the list of 2026-11-20's tenth phase (RDList15i.cpp): landmarks and lookouts (ideas 1 and 2)
	/** the lookouts' tops laid (their place id -> middle x, y and the second storey's top z, cm), those she has climbed, and the places
	 *  their tops marked on her map (seen, not found: drawn at half strength, no travel), the last two kept with the game */
	TMap<int32, FVector> WildLookoutTops15;
	TSet<int32> LookoutsClimbed15, WildMarked15;
	/** the marked places as places, looked up once when the marks change (PR #102's review: WildKnownPlaces looked each up every frame) */
	mutable TArray<FRDWildPlace> WildMarkedCache15;
	mutable int32 WildMarkedCacheFor15 = -1;
	float LookoutLook15 = 0.f;
	int32 LastLookoutMarked15 = 0;
	void NoteLookoutTop15(const struct FRDWildPlace& P, const FVector& Mid, float TopZ);
	void TickLookouts15(float Dt, const FVector& Her);
	int32 ClimbLookout15(const struct FRDWildPlace& L);
	void LoadLookouts15();
	/** tests: the lookouts within Km of her, "id|name|x m|y m|top z cm (-1: not laid)|climbed|found|cell x|cell y|tier" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") TArray<FString> GetLookouts15(float Km) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") bool IsWildMarked15(int32 Id) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") TArray<int32> GetWildMarked15() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") int32 GetLastLookoutMarked15() const { return LastLookoutMarked15; }
	/** tests: the marked places, "id|kind|name|x m|y m|region cell x|cell y|found"; the ids the map draws (WildKnownPlaces) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") TArray<FString> GetWildMarkedLines15() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") TArray<int32> GetWildKnownIds15() const;
	/** the regions' landmarks: lines "kind|biomes;...|main mesh|main height m|extra mesh|extra height m|extra width m|extra by night
	 *  only (0/1)|extra material|main sink m" (indices into the two lists; -1 none), from SourceArt/wilderness/landmarks15.json (936) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TArray<FString> RegionLandmarkLines15;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TArray<TObjectPtr<UStaticMesh>> RegionLandmarkMeshes15;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TArray<TObjectPtr<UMaterialInterface>> RegionLandmarkMats15;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float RegionLandmarkKm15 = 22.f;
	struct FRegionLandmark15 { int32 Line = -1; FVector2D At = FVector2D::ZeroVector; float Z = 0.f, TopZ = 0.f, Yaw = 0.f; bool bExtraNight = false;
		TWeakObjectPtr<class UStaticMeshComponent> Main, Extra; };
	TMap<FIntVector, FRegionLandmark15> RegionLandmarks15;
	mutable TMap<FIntVector, FRegionLandmark15> RegionLandmarkSites15;
	/** the 6 km squares' tower sites, worked out once (x, y m; z 1 when it has one) */
	mutable TMap<FIntPoint, FVector> WildTowerSites13;
	/** the open lands' far towers (a 6 km square's -> its tower, laid as seen from afar; the nearest is WildLandmark) */
	TMap<FIntPoint, TWeakObjectPtr<class UStaticMeshComponent>> FarTowers15;
	/** a 6 km square's broken tower's spot (TickWildLandmark13's rule, shared): false where it has none */
	bool WildTowerSite13(int32 I, int32 J, FVector2D& S) const;
	float RegionLandmarkLook15 = 0.f;
	bool RegionLandmarkOf15(FIntPoint Cell, int32 Slot, FRegionLandmark15& Out) const;
	void LayRegionLandmark15(FRegionLandmark15& Lm);
	void TickRegionLandmarks15(float Dt, const FVector& Her);
	/** the landmark lines parsed once (PR #102's review), and each cell's and slot's landmark worked out once (pure functions of the seed) */
	struct FRegionLandmarkKind15 { FString Name; TArray<FString> Biomes; int32 Main = -1, Extra = -1, Mat = -1; float Height = 100.f, ExtraHeight = 100.f, ExtraWidth = 10.f, Sink = 2.f; bool bNight = false; };
	mutable TArray<FRegionLandmarkKind15> RegionLandmarkParsed15;
	mutable int32 RegionLandmarkParsedFor15 = -1;
	void ParseRegionLandmarks15() const;
	/** one night for the phase's rules (the sky's: 20:00 to 5:30), and the houses' lights' hours (dusk to bed, and before dawn) */
	bool IsWildNight15() const;
	bool IsHouseLightHour15() const;
	/** tests: the landmarks laid round her, "kind|x m|y m|ground z|top z (cm)|main laid|extra (0 none, 1 hidden, 2 shown)" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") TArray<FString> GetRegionLandmarks15() const;
	/** the travellers' camps' smoke (a column over the fire, its width and height in m as X and Z) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TObjectPtr<UStaticMesh> CampSmokeMesh15 = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TObjectPtr<UMaterialInterface> CampSmokeMat15 = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") FVector CampSmokeSize15 = FVector(3.f, 3.f, 40.f);
	/** the villages' houses lit by night (from dusk to the household's bed, and before dawn) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bHouseLights15 = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float HouseLightCandelas15 = 60.f;
	TArray<TWeakObjectPtr<class UPointLightComponent>> HouseLights15;
	float HouseLightLook15 = 0.f;
	class UPointLightComponent* AddHouseLight15(ARDWildChunk* C, const FVector& RoomC, const FVector& DoorOut, bool bDoor);
	void TickHouseLights15(float Dt, const FVector& Her);
	/** tests: the houses' lights within RadiusM of a point (m), "x|y|z|on|candelas" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") TArray<FString> GetHouseLights15(FVector2D AtM, float RadiusM) const;
	// ---- the list of 2026-11-20's eleventh phase (RDList15j.cpp): named roaming monsters and the map's danger (ideas 3 and 9)
	/** a cell's roamer: its id ((cell x << 10) | cell y), name, kind (an index into Monsters; -1 none), tiers, its round (middle m, radius m,
	 *  phase), when it is out (0 always, 1 by night, 2 in storms) and its ring */
	struct FRoamer15 { int32 Id = 0; FString Name; int32 Kind = -1, Tier = 1, RegionTier = 1; FVector2D C = FVector2D::ZeroVector; float Radius = 500.f, Phase = 0.f; uint8 When = 0; FName Ring; };
	mutable TMap<FIntPoint, FRoamer15> RoamerCache15;
	TMap<int32, TWeakObjectPtr<class ARDMonster>> Roamers15;
	float RoamerLook15 = 0.f;
	/** the roamers' data (937 from SourceArt/wilderness/roamers15.json): their names and epithets, their rings (items of weight 0 on every
	 *  map), the share of the regions' cells with one, how far over the region's tier, their hit points' factor, the round's time, and how
	 *  near she must be for one to be laid */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TArray<FString> RoamerNames15;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TArray<FString> RoamerEpithets15;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TArray<FName> RoamerRings15;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float RoamerChance15 = 0.6f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") int32 RoamerTierUp15 = 4;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float RoamerHp15 = 2.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float RoamerRoundSeconds15 = 900.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float RoamerReachM15 = 900.f;
	/** idea 9: the major roads drawn in their tier's colour on the big map, with a key (937 data) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bRoadTiers15 = false;
	bool RoamerOf15(FIntPoint Cell, FRoamer15& Out) const;
	FVector2D RoamerAt15(const FRoamer15& R) const;
	double RoamerAngle15(const FRoamer15& R) const;
	/** a laid roamer's place on its round (its angle), walked on at its own pace */
	TMap<int32, double> RoamerAngles15;
	bool RoamerOut15(const FRoamer15& R) const;
	void TickRoamers15(float Dt, const FVector& Her);
	/** a roamer's death: kept for the game, its ring dropped once; false when it was no roamer */
	bool OnRoamerKilled15(class ARDMonster* Monster, bool bHers);
	void DrawRoamerMarks15(TFunctionRef<void(const FVector2D& AtM, const FString& Name)> Each) const;
	/** tests: the roamers of the cells within Km, "id|name|kind|tier|region tier|when|round x|y|radius|now x|y|laid|seen|slain|ring|monster x|y (cm)|out now" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") TArray<FString> GetRoamers15(float Km) const;
	/** the major roads' colour by tier (a band of five tiers a colour), and tests' read of what the map draws */
	static FLinearColor RoadTierColor15(int32 Tier);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") TArray<FString> GetRoadTiers15(float Km) const;
	// ---- the list of 2026-11-20's twelfth phase (RDList15k.cpp): rewards that last (idea 4)
	/** the collectibles' kinds, "item|biome;biome...|r,g,b" (938 from SourceArt/wilderness/rewards15.json), the share of the 500 m grid's
	 *  cells with one, and how many of a kind a temple takes for 10 hit points, 10 mana or an Angel Token */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TArray<FString> CollectibleKinds15;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float CollectibleChance15 = 0.3f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") int32 CollectibleTradeN15 = 5;
	/** the ruins' loose treasure maps (the share of ruins with one), the buried chest's things and gold, its mesh; the glow of what lies
	 *  to be taken (a mesh and a material with a "Color") */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float TreasureMapChance15 = 0.4f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") int32 TreasureChestItems15 = 3;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float TreasureChestGold15 = 60.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TObjectPtr<UStaticMesh> TreasureChestMesh15 = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TObjectPtr<UStaticMesh> RewardGlowMesh15 = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TObjectPtr<UMaterialInterface> RewardGlowMat15 = nullptr;
	/** each kind of structure's named item, "kind|item" (items of weight 0 on every map) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TArray<FString> PlaceItems15;
	struct FCollectible15 { int32 Id = 0, Kind = -1; FVector2D At = FVector2D::ZeroVector; FName Item; FLinearColor Color = FLinearColor::White; };
	struct FRewardLaid15 { int32 Id = 0; float TopZ = 0.f; FVector At = FVector::ZeroVector; FName Item; TWeakObjectPtr<class UStaticMeshComponent> Mesh, Lid; TWeakObjectPtr<class UPointLightComponent> Light; };
	struct FTreasurePicture15 { int32 Id = 0; TObjectPtr<class UTextureRenderTarget2D> Rt = nullptr; FString Landmark; };
	mutable TMap<FIntPoint, FCollectible15> CollectibleCache15;
	/** a ruin's treasure spot: where to dig, the landmark's name, and the landmark itself (a region's: its cell and slot; a broken tower:
	 *  its site) so the picture can lay it when it is not standing */
	struct FTreasureSpot15 { FVector2D Spot = FVector2D::ZeroVector; FString Landmark; FVector2D LmAt = FVector2D::ZeroVector; bool bTower = false; FIntPoint Cell = FIntPoint::ZeroValue; int32 Slot = 0; };
	mutable TMap<int32, FTreasureSpot15> TreasureSpots15;
	const FTreasureSpot15* TreasureSpot15(int32 RuinId, const FVector2D& RuinAt) const;
	bool RuinHasMap15(const struct FRDWildPlace& P) const;
	TMap<int32, FRewardLaid15> CollectiblesLaid15, MapsLaid15, ChestsLaid15;
	UPROPERTY(Transient) TArray<TObjectPtr<class UTextureRenderTarget2D>> TreasureTargets15;
	TArray<FTreasurePicture15> TreasurePictures15;
	float RewardLook15 = 0.f, WildReadySince15 = -1.f;
	FString LastChestDug15;
	bool CollectibleOf15(FIntPoint Cell, FCollectible15& Out) const;
	bool TreasureSpotOf15(int32 RuinId, const FVector2D& RuinAt, FVector2D& Spot, FString& Landmark) const;
	void TickRewards15(float Dt, const FVector& Her);
	bool RewardFirst15(const FVector& From, int32& Kind, int32& Id) const;
	FString RewardDescribe15(const FVector& From) const;
	FString RewardInteract15(const FVector& From);
	void DrawTreasureMap15(int32 Id, const FVector2D& Spot, const FString& Landmark);
	class UTextureRenderTarget2D* TreasurePictureToShow15(FString& Caption) const;
	void AddCollectibleTrades15(TFunctionRef<void(const FString& Act, const FString& Label, const FString& Tag, const FString& Detail, bool bOn, const FString& Arg)> Add) const;
	bool TownCollectTrade15(const FString& Arg);
	/** the hit points and mana a temple's trades added for good (the game instance's), for her maxima */
	float LastingHealth15() const;
	float LastingMana15() const;
	void AddPlaceItem15(const FVector& BoxAt, int64 BoxKey, TArray<FName>& Got);
	// ---- the list of 2026-11-20's seventeenth phase (RDList15p.cpp): preparing for regions (idea 7), from SourceArt/wilderness/climate15.json (943)
	/** the armour sets' warmth against the cold and coolness in the heat ("set|warm|cool"; cool below 0: hotter), the hot regions and the
	 *  hours their heat comes on, how long it takes to sap her, the regions' herbs ("item|biome;biome") in their resource points' piles */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TArray<FString> ClimateGear15;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TArray<FString> WildHeatBiomes15;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float HeatFrom15 = 10.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float HeatTo15 = 17.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float HeatSeconds15 = 90.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TArray<FString> ClimateHerbs15;
	struct FClimateMeter15 { float V = 0.f, BiteAt = 0.f, OutSince = -1.f, SaidAt = -100.f; bool bTold = false; int32 Bites = 0; };
	FClimateMeter15 WildColdMeter15, WildHeatMeter15;
	bool bWildHotNow15 = false;
	FString WildHeatWhy15;
	mutable TMap<FName, FVector2D> ClimateGearMap15;
	mutable int32 ClimateGearFor15 = -1;
	void GearClimate15(float& Warm, float& Cool) const;
	float ColdRate15() const;
	float HeatRate15() const;
	void StepClimateMeter15(FClimateMeter15& M, bool bIn, bool bSay, float Step, float Rate, float Seconds, float Now, const TCHAR* Start, const TCHAR* Bite, const TCHAR* End);
	void StepHeat15(const struct FRDWSample& Qs, bool bInTown, const FVector& Her, float Now);
	void AddClimateHerb15(const struct FRDWildPlace& P, TArray<FName>& Got) const;
	/** tests: the cold and the heat (see RDList15p.cpp); both from nothing */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") FString GetWildClimate15() const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List15") void ResetClimate15();
	// ---- the list of 2026-11-20's sixteenth phase (RDList15o.cpp, RDList14k.cpp): waystones and crossroads posts (idea 9 in part)
	/** the waystones (the world's, one a region's cell) and the crossroads posts laid in play (941... 942 sets them), the stone's height (m) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bWaystones15 = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bCrossPosts15 = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float WaystoneHeight15 = 2.6f;
	struct FSignArm14 { FString Name; float M = 0.f; float Yaw = 0.f; };
	struct FCrossArm15 { FString Name; float M = 0.f; FVector2D Dir = FVector2D(1, 0); };
	struct FCrossPost15 { FVector2D At = FVector2D::ZeroVector; bool bPlaced = false; TArray<FCrossArm15> Arms; };
	TMap<int32, FRewardLaid15> WaystonesLaid15;
	mutable TMap<int32, FCrossPost15> CrossPosts15;
	TMap<int32, TWeakObjectPtr<AActor>> CrossPostActors15;
	float WaystoneLook15 = 0.f, CrossLook15 = 0.f;
	AActor* SpawnSignPost14(const FVector2D& AtM, float PostYaw, const TArray<FSignArm14>& Arms, const FString& Tag);
	bool IsWaystoneLit15(int32 Id) const;
	void TickWaystones15(float Dt, const FVector& Her);
	void LayWaystone15(const struct FRDWildPlace& P);
	void GlowWaystone15(int32 Id);
	bool WaystoneFirst15(const FVector& From, float& Best, int32& Kind, int32& Id) const;
	FString LightWaystone15(int32 Id);
	FString WaystoneDescribe15(int32 Id) const;
	bool CrossPostOf15(int32 Ci, FCrossPost15& Out) const;
	void TickCrossPosts15(float Dt, const FVector& Her);
	/** tests: the waystones within Km "id|name|x|y|found|lit|laid"; the crossroads posts within Km (see RDList15o.cpp) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") TArray<FString> GetWaystones15(float Km) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") TArray<FString> GetCrossPosts15(float Km) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List15") void ForgetWaystones15(const TArray<int32>& Ids);
	void DropWaystonesAndPosts15();
	void EnsureWaystoneVeto15() const;
	void CrossroadsNear15(const FVector2D& P, double R, TArray<int32>& Out) const;
	mutable TMultiMap<FIntPoint, int32> CrossHash15;
	mutable int32 CrossHashFor15 = -1;
	// ---- the list of 2026-11-20's fifteenth phase (RDList15n.cpp): story encounters (idea 8), from SourceArt/wilderness/stories15.json (941)
	/** the courier's letters ("{hero}" her hero's name), who a letter is from when she has met no one, the pursuers of one chased, the
	 *  cart's tilt off its wheel, her rival (name, body, lines met first and again, said when it wins and when she does), how far beyond
	 *  the place the rival starts (times her distance) and how near the place she must come first (cm) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TArray<FString> StoryLetters15;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") FString StoryDefaultSender15 = TEXT("the elder of Brokenspire");
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") int32 StoryPursuers15 = 3;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float StoryCartTilt15 = 14.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") FString StoryRivalName15 = TEXT("Varka the Swift");
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") FString StoryRivalDef15;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") FString StoryRivalHello15;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") FString StoryRivalAgain15;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") FString StoryRivalWon15;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") FString StoryRivalLost15;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float StoryRivalLead15 = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float StoryRivalReachCm15 = 800.f;
	struct FStory15 { FName Kind; int32 Id = 0, PoiId = -1; FVector At = FVector::ZeroVector; float Since = 0.f, CartYaw = 0.f; FString Title, Detail, State;
		TWeakObjectPtr<class ARDTownsfolk> Person; TArray<TWeakObjectPtr<class ARDMonster>> Pursuers; TArray<bool> PursuerKilled; TWeakObjectPtr<class UStaticMeshComponent> Cart; };
	TArray<FStory15> Stories15;
	TArray<FString> StoryLog15;
	int32 StoriesMade15 = 0;
	void RecordMet15(const FString& Who);
	class ARDTownsfolk* SpawnWildRoamFolk15(const FString& Def, const FVector2D& AtCm, float Yaw, uint32 Seed, const FString& Title, const TArray<FString>& Lines, bool bFallback);
	TArray<int64> StoryUsedKeys15;
	int32 MakeStory15(const FRDWildPoiKind& K, const FVector2D& At, FRandomStream& Rs);
	void TickStories15(float Dt, const FVector& Her);
	bool StoryCartFirst15(const FVector& From, float& Best, int32& Kind, int32& Id) const;
	FString MendStoryCart15(int32 Id);
	void MarkWildPoiUsed15(int32 Id);
	/** tests: the stories going and their log (see RDList15n.cpp), and one chased's pursuer */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") TArray<FString> GetStories15() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") class ARDMonster* GetStoryPursuer15(int32 Id, int32 N) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List15") void ForgetStories15();
	// ---- the list of 2026-11-20's fourteenth phase (RDList15m.cpp): camps cleared that change the world (idea 6)
	/** the days after a camp is cleared before its nearest ruin within ReclaimRuinKm15 is resettled (0: off), the waypoint's trader's body
	 *  (a townsfolk def's name's start) and lines, the settlers' lines (940 from SourceArt/wilderness/reclaim15.json) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float ReclaimDays15 = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float ReclaimRuinKm15 = 3.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") FString ReclaimTraderDef15 = TEXT("Townsman");
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TArray<FString> ReclaimTraderLines15;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TArray<FString> ReclaimSettlerLines15;
	struct FReclaimLaid15 { FVector2D At2 = FVector2D::ZeroVector, FireAt = FVector2D::ZeroVector; FVector TentAt = FVector::ZeroVector, TraderAt = FVector::ZeroVector; TArray<TWeakObjectPtr<USceneComponent>> Comps; TArray<TWeakObjectPtr<AActor>> Folk; TWeakObjectPtr<class ARDTownsfolk> Trader; };
	TArray<TWeakObjectPtr<class ARDTownsfolk>> WildReclaimFolk15;
	mutable TArray<TPair<FVector2D, FString>> ReclaimMarks15;
	mutable int32 ReclaimMarksFor15 = -1;
	static void DropReclaim15(FReclaimLaid15& L);
	int32 WildPlaceDraws15(const struct FRDWildPlace& P, FRandomStream& R, int32 KindsNum, int32& KindPick) const;
	TMap<int32, FReclaimLaid15> CampsLaid15, RuinsLaid15;
	mutable TMap<FIntPoint, int32> ReclaimShareCache15;
	float ReclaimLook15 = 0.f;
	int32 SettlerTalks15 = 0;
	bool IsClearableCamp15(const struct FRDWildPlace& P) const;
	int32 WildPlaceMonsterCount15(const struct FRDWildPlace& P) const;
	bool CampCleared15(const struct FRDWildPlace& P) const;
	int32 CampClearedDay15(int32 Id) const;
	void TickReclaim15(float Dt, const FVector& Her);
	void LayCampWaypoint15(const struct FRDWildPlace& P);
	void LayRuinFolk15(const struct FRDWildPlace& P);
	class ARDTownsfolk* SpawnReclaimFolk15(const FVector2D& At, float Yaw, uint32 Seed, const FString& Def, const FString& Title, const TArray<FString>& Lines);
	bool ReclaimFirst15(const FVector& From, float& Best, int32& Kind, int32& Id) const;
	FString RestAtCamp15(int32 Id);
	FString TalkSettler15(int32 Key);
	void DrawReclaimShares15(TFunctionRef<void(const FVector2D& AtM, const FString& Text)> Each) const;
	int32 ReclaimCampsInCell15(FIntPoint Cell) const;
	/** tests: the days passed at once; the camps within Km and the resettled ruins (see RDList15m.cpp) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List15") void SkipDays15(int32 Days);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List15") void ForgetReclaim15(const TArray<int32>& CampIds);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") TArray<FString> GetReclaim15(float Km) const;
	// ---- the list of 2026-11-20's thirteenth phase (RDList15l.cpp): monster contracts (idea 5)
	/** the beasts, "name|kind|hp|tier up|weakness|offer|sign~sign~sign" (939 from SourceArt/wilderness/contracts15.json), how many a
	 *  board posts, the share more her blows do once its signs are read, the bounty's gold at tier 1 (35 % more a tier) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") TArray<FString> Contracts15;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") int32 ContractsPerBoard15 = 2;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float ContractWeakShare15 = 0.75f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List15") float ContractGold15 = 80.f;
	struct FContractKind15 { FString Name, Weak, Offer; FName Kind; float Hp = 2.f; int32 TierUp = 2, Monster = -1; TArray<FString> Signs; };
	struct FContract15 { int32 Id = -1, Town = -1, Line = -1, Tier = 1; FVector2D Lair = FVector2D::ZeroVector; FVector2D Sign[3]; };
	mutable TArray<FContractKind15> ContractKinds15;
	mutable bool bContractsParsed15 = false;
	mutable TMap<int32, FContract15> ContractCache15;
	TMap<int32, FRewardLaid15> ContractSignsLaid15;
	TMap<int32, TWeakObjectPtr<class ARDMonster>> ContractBeasts15;
	float ContractLook15 = 0.f;
	void ParseContracts15() const;
	int32 ContractTownHere15() const;
	bool ContractOf15(int32 Id, FContract15& Out) const;
	int32 ContractSignsRead15(int32 Id) const;
	int32 ContractGoldOf15(const FContract15& C) const;
	int32 AddContractLines15(TFunctionRef<void(const FString& Act, const FString& Label, const FString& Tag, const FString& Detail, bool bOn, const FString& Arg)> Add) const;
	bool TownContract15(FName Act, const FString& Arg);
	void TickContracts15(float Dt, const FVector& Her);
	static void DropReward15(FRewardLaid15& R);          // (a laid reward's mesh, lid and light, the rewards' and the contracts')
	void MakeGlow15(FRewardLaid15& R, const FVector& At, const FLinearColor& Col, float Scale);
	FString ReadContractSign15(int32 Key);
	bool OnContractKilled15(class ARDMonster* Monster, bool bHers);
	void DrawContractMarks15(TFunctionRef<void(const FVector2D& AtM, const FString& Name)> Each) const;
	/** tests: every board's contracts (see RDList15l.cpp), and a contract's beast while it is out */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") TArray<FString> GetContracts15() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") class ARDMonster* GetContractBeast15(int32 Id) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List15") void ForgetContract15(int32 Id);
	/** tests: the collectibles, the ruins' maps and the buried chests within Km (see RDList15k.cpp); the last chest dug "id|tier|gold|things" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") TArray<FString> GetRewards15(float Km) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") FString GetLastChestDug15() const { return LastChestDug15; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") bool HasTreasurePicture15() const { FString C; return TreasurePictureToShow15(C) != nullptr; }
	/** tests: the cave level's "key|tier|base|cap|title" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") FString GetCave15() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List15") FIntPoint GetTerraceWalls15() const { return FIntPoint(TerraceWalls15, TerraceButtresses15); }
	/** the Old Watchtower climbed: its doorway open (hidden boxes round its ring, not its quarters' collision), a spiral stair up to
	 *  a floor at the second storey's top */
	void FitWildTower(ARDWildChunk* C, const FVector& Mid, float Z0, float Hs, float DoorYaw, float KeptYaw = -1e6f, int32 Storeys = 2);
	/** the nearest wild door within Reach of a point (its chunk and index), F's */
	ARDWildChunk* WildDoorNear(const FVector& From, float Reach, int32& Index) const;
	FString WildDoorDescribe(const FVector& From) const;
	FString WildDoorInteract(const FVector& From);
	void TickWildDoors(float Dt);
	/** "the house|<chunk x>|<y>|<x>|<y>|<z>|<doors>|<furniture>|<lit>|<floor z>|<what it is>" of every wild house laid, and "door|<x>|<y>|<z>|<open
	 *  0..1>|<to>" of every door (tests) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List10") TArray<FString> GetWildHouseLines() const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List10") TArray<FString> GetWildTowerLines() const;
	TArray<FString> WildTowerLines;
	/** the farmsteads on the map: found as places are (within WildDiscoverM), drawn with wmap_farmstead */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") bool bWildFarmsOnMap = false;
	/** the liveliness ideas built ("what can be done to make the town / the wilderness more lively?"): travellers on the wilds' roads,
	 *  walking from town to town by day and camped round a fire beside the road at night (WildTravellerGroups at most, within
	 *  WildTravellerM of her); hens loose in a town's square, running from her (TownHens); the town's watch with lanterns at night */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") bool bWildTravellers = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") int32 WildTravellerGroups = 3;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") float WildTravellerM = 450.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") TArray<FName> WildTravellerRoles;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") int32 TownHens = 0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") bool bNightLanterns = false;
	struct FTraveller { TArray<TWeakObjectPtr<class ARDTownsfolk>> Folk; int32 Road = -1; int32 Seg = 0; int32 Dir = 1; bool bCamped = false; FVector Camp = FVector::ZeroVector;
		TArray<TWeakObjectPtr<UActorComponent>> CampBits; uint32 Seed = 0; FString Name; };
	TArray<FTraveller> WildTravellers;
	int32 WildTravellersMade = 0;
	/** the farmsteads round her great field cell (the map's: searched once a cell, PR #43's review: four times a second it was) */
	FIntPoint WildFarmCell = FIntPoint(MAX_int32, MAX_int32);
	TArray<FRDWildPlace> WildFarmNear;
	float TravellerClock = 0.f, LanternClock = 0.f;
	void TickWild10(float Dt, const FVector& Her);
	void TickWildTravellers(const FVector& Her);
	void CampTravellers(FTraveller& T);
	void SpawnTownHens();
	void TickNightLanterns();
	/** "group|<i>|<x>|<y>|<z>|<folk>|<camped 0/1>|<walking>|<road>|<name>" (tests); a group sent at her for a test */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List10") TArray<FString> GetWildTravellerLines() const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List10") bool ForceWildTravellers();
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List10") TArray<FString> GetTownHenLines() const;
	// ---- the list of 2026-11-10's third phase (RD/RDList10c.cpp)
	/** "the fighter and only the fighter should be able to craft basic weapons and armor she has already looted at a forge - a forge
	 *  is a new crafting station": a forge (ForgePieces wherever they stand, the town smithy's forge, one by the anvil of a set with no
	 *  forge) opens the crafting panel on its own recipes (Station "Forge", 914's); only ForgeHeroes work it, and a recipe shows only
	 *  for what she has looted (HasLooted: the game instance's LootedItems, every weapon, shield and armour that went into her pack) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") bool bForge = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") TArray<FName> ForgeHeroes;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") TArray<FName> ForgePieces;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") FName ForgeStationPiece = TEXT("Forge");
	bool FindNearestForge(const FVector& From, float MaxDistance, FVector& At) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List10") TArray<FVector> GetAllForges() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List10") bool HasLooted(FName Item) const;
	void NoteLooted(FName Item);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List10") TArray<FName> GetLootedItems() const;
	FString ForgeRefusal() const;
	/** heroes by their titles in a sentence ("the Mage and the Martial Artist"): the potions' and the forge's refusals */
	FString HeroesInWords(const TArray<FName>& Names) const;
	/** "everyone should be able to craft food items from food components at an oven": the dungeons' kitchens' bread ovens are ovens too
	 *  (bDungeonOvens: their recipes the town's, 914's) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") bool bDungeonOvens = false;
	bool FindNearestOven(const FVector& From, float MaxDistance, FVector& At) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List10") TArray<FVector> GetAllOvens() const;
	/** F at a forge or a dungeon's oven (nearer than the anvil and any door or container): "" if none */
	FString StationInteract(const FVector& From, float DoorD);
	FString StationDescribe(const FVector& From, float DoorD) const;
	/** "new type of item that can be held in the left hand and put in the quick slot: revealing light, looks like an ankh, found on
	 *  Tier 2 monsters or in containers" (the user's choice: it lights the way as the torch does and within AnkhRevealRange shows the
	 *  traps (outlined, as the Rogue sees them) and the chests and trunks not looted (on the map)): an item of kind Light held as the
	 *  torch is (its fit's mesh in her left hand), its light pale */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") float AnkhLight = 40.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") float AnkhLightRadius = 1400.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") FLinearColor AnkhColor = FLinearColor(0.8f, 0.88f, 1.f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") FVector AnkhGlowAt = FVector(0.f, 0.f, 25.f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") float AnkhRevealRange = 1000.f;
	/** a tier-2 monster's chance to drop one (when she has none) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List10") float AnkhDropChance = 0.06f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List10") int32 AnkhTrapsShown = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List10") int32 AnkhCachesShown = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List10") int32 AnkhDrops = 0;
	/** the chests and trunks it has shown (set and container key) */
	TSet<FIntVector> AnkhRevealed;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List10") FName GetAnkhItem() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List10") bool IsContainerRevealed(FIntPoint Section, int32 Key) const { return AnkhRevealed.Contains(FIntVector(Section.X, Section.Y, Key)); }
	float AnkhClock = 0.f, AnkhNext = 0.f;
	void TickAnkh(float Dt);
	/** a killed monster of the game's tier 2 may drop the ankh (a pile of its own) */
	void AnkhDropFor(class ARDMonster* Monster);
	/** the castle's way back to the town (an arch in the great hall): F there */
	FVector CastleWayBack = FVector::ZeroVector;
	UPROPERTY(Transient) TObjectPtr<AActor> CastleWayBackActor;
	/** a monster killed, a container opened, a prisoner freed, a tier opened: the purse and the quests' counters */
	void TownOnKill(ARDMonster* Monster, bool bBossKill);
	void TownOnContainer(ARDSection* Section, int32 Key, const FVector& At);
	void TownCount(const FString& Key, int32 Amount = 1);
	void TownCountMax(const FString& Key, int32 Value);
	UPROPERTY(Transient) TArray<TObjectPtr<class ARDTownsfolk>> TownPeople;
	UPROPERTY(Transient) TArray<TObjectPtr<ARDMonster>> TownGuards;
	UPROPERTY(Transient) TObjectPtr<AActor> MistgateFx;
	UPROPERTY(Transient) TObjectPtr<AActor> CircleFx;
	FName TownPanel;
	int32 TownTab = 0, TownCursor = 0, TownGuardsPlanned = 0;
	/** the panel's lines were made with the wilds ready (BuildTownLines); TickTownPanel makes them again once they are */
	bool bTownLinesWildReady = true;
	/** tests: a dry run's Quit writes its autosave too (884 autosave13; off: a dry run writes nothing) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Menu") bool bMenuDryRunAutosave = false;
	bool bTownTraveling = false, bTownPlaced = false;
	uint64 TownPanelClosedFrame = 0;
	// (the showcase tour)
	void TickTownTour(float RealDt);
	void EndTownTour(const FString& Why);
	bool bTourOn = false, bTourCmdRead = false, bTourJumped = false;
	int32 TourPhase = 0, TourStuckN = 0;
	float TourT = 0.f, TourCastleSeconds = 0.f, TourCheckT = 0.f, TourDodgeUntil = -1.f, TourDodgeSign = 1.f;
	/** the tour's look at the town's life (the third list): the places being worked it shows, in turn */
	TArray<int32> TourLife;
	int32 TourLifeI = -1;
	/** how far before the Mistgate the run starts (m; the map hides the move: -RDTourRun=<m>, 0 the whole way) */
	UPROPERTY(BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float TourRunMeters = 100.f;
	/** a run longer than this (s) goes through the Mistgate at once (said in the log and the tour's state) */
	UPROPERTY(BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float TourRunTimeout = 60.f;
	/** how the tour ended when it did not reach the Mistgate ("" while it runs or when it did) */
	FString TourResult;
	FString TourGo;
	TArray<FVector> TourPath;
	FVector TourCheckAt = FVector::ZeroVector;
	void SpawnTownPeople();
	void SpawnTownGuards();
	/** the services */
	bool TownBuy(FName Item);
	bool TownSell(const FString& Ref);
	bool TownHeal();
	int32 TownHealCost() const;
	bool TownRepair(const FString& Ref);
	int32 RepairCost(const FString& Ref) const;
	bool TownBless();
	bool TownDeposit(const FString& Ref);
	bool TownWithdraw(int32 Index);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Brokenspire") bool TownQuestAction(FName Act, FName Id);
	void SetTownNote(const FString& Text);
	/** what the trader has for sale now (the open tier's potions, food, repair items, scrolls) */
	TArray<FName> TownStock() const;

	/** random_dungeonmagic_level4: the painted interface (panels, bar frames and fills, slots, icons...; pipeline/unreal/830).
	 *  The HUD draws a piece where it has one and its plain boxes where it has not (the other dungeon levels have none). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Interface") TMap<FName, FRDUIArt> UIArt;
	/** random_dungeonmagic_level4: its lettering by role ("title", "text", "label"; pipeline/unreal/830). Without it the HUD
	 *  writes in the engine's font. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Interface") TMap<FName, FRDUIFont> UIFonts;
	/** random_dungeonmagic_level5 (the Summoner): her face's expression channels and the occasions that show them (834).
	 *  With them the generator gives her pawn a URDFaceComponent in play (its blinks seeded from the session seed). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Face") TArray<FRDFaceChannel> FaceChannels;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Face") TMap<FName, FRDFaceCue> FaceCues;
	/** a MetaHuman face on her (840: MHC_Summoner's face mesh, its brows and lashes, her body's cut-away material); its
	 *  channels' Curves drive it. Empty: her own face (the shapes and the painted patches) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Face") FRDMetaFace FaceMeta;

	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") URDCombatComponent* GetPlayerCombat() const { return PlayerCombat; }
	/** her average damage a blow over the weapons */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetAverageWeaponDamage() const;
	/** hit points / damage of the average monster of a section */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetMonsterHealth(FIntPoint Section) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetMonsterDamage(FIntPoint Section) const;
	/** weighted means of the monster kinds' factors (a monster's values are divided by them; with tiers, of the kinds of
	 *  that section's tier) */
	void MeanMonsterFactors(float& Health, float& Damage, FIntPoint Section = FIntPoint(0, 0)) const;
	void OnMonsterKilled(ARDMonster* Monster);
	/** a number that floats up where a blow landed (HUD) */
	struct FHitText { FVector At; float Amount; float Time; bool bOnPlayer; };
	TArray<FHitText> HitTexts;
	void AddHitText(const FVector& At, float Amount, bool bOnPlayer);
	/** demo reels and tests: the dungeon as it is when play begins (the start section's doors, containers and monsters
	 *  rebuilt from its seed, the sections generated in play removed, the map and the counters cleared, her at the start).
	 *  Seed (not 0) becomes the session seed: the sections generated from then on are the same every time. */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void RestartPlay(int32 Seed = 0);
	/** runtime sections are furnished within this many milliseconds a frame (a reel sets it high: built in one frame) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") void SetFrameBudget(float Milliseconds) { FrameBudgetMs = Milliseconds; }

	// ---- blood and wounds (random_dungeoncombat_level; filled by pipeline/unreal/798)
	/** a blow throws drops of this mesh (one instanced mesh for all of them) and a spray of camera-facing sprites */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Gore") TObjectPtr<UStaticMesh> BloodDropMesh;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Gore") TObjectPtr<UMaterialInterface> BloodDropMaterial;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Gore") TObjectPtr<UStaticMesh> BloodSprayMesh;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Gore") TObjectPtr<UMaterialInterface> BloodSprayMaterial;
	/** decals left where a drop lands, and the pools under a body */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Gore") TArray<TObjectPtr<UMaterialInterface>> BloodDecals;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Gore") TArray<TObjectPtr<UMaterialInterface>> BloodPools;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Gore") float BloodDecalSeconds = 45.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Gore") int32 MaxBloodDecals = 140;
	/** scales the number of drops of a burst */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Gore") float BloodAmount = 1.f;
	/** overlay material of a wounded monster (parameters Wound0..Wound9: the wounds in the mesh's reference pose, and
	 *  Bleed); every monster gets an instance of its own with its first wound */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Gore") TObjectPtr<UMaterialInterface> WoundMaterial;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Gore") URDBloodComponent* GetBlood() const { return Blood; }

	// ---- sound (filled by pipeline/unreal/797)
	/** "Player.Step", "Monster.Troll.Roar", "Env.DoorOpen", "Env.Torch"... (an occasion without an entry is silent) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sound") TMap<FName, FRDSoundSet> Sounds;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sound") float SoundVolume = 1.f;
	/** fires (Env.Torch / Env.Brazier / Env.Hearth loops) heard at once: the nearest ones to her get a voice */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sound") int32 FireLoopVoices = 6;
	/** placed sounds are also heard from their direction (stereo). Play begins without it when the editor runs with
	 *  -deterministicaudio: the engine's non-realtime audio device, which the Movie Render Queue records, loses every
	 *  spatialised source (measured: a mono source panned by the built-in panner is missing from its two-channel output,
	 *  from any direction; the same source without spatialisation is there). A render then has them centred, with the
	 *  distance falloff only. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sound") bool bSpatializeSounds = true;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Sound") bool AreSoundsSpatialized() const { return bSpatializeNow; }
	/** on the music and atmosphere sets (SoundVolume is for the sounds of the world) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sound") float MusicVolume = 1.f;
	/** a fight is on while a monster within this distance is after her; the battle music stays this long after the fight */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sound") float CombatMusicDistance = 2600.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Sound") float CombatMusicHold = 3.5f;
	/** times the music went from wandering to battle or back */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Sound") int32 MusicShifts = 0;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Sound") bool IsCombatMusic() const { return bCombatMusic; }
	/** the track playing now, and the atmosphere under it (asset names; "" none) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Sound") FString GetMusicTrack() const { return MusicLayerName(bCombatMusic ? 1 : 0); }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Sound") FString GetAtmosphereTrack() const { return MusicLayerName(bCombatMusic ? 3 : 2); }
	/** seconds into its track the playing music is */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Sound") float GetMusicPosition() const { return MusicPos[bCombatMusic ? 1 : 0]; }
	/** plays one of the sounds of Key at a place (or flat, for a 2D set); false when there is no such sound */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Sound") bool PlaySoundAt(FName Key, FVector At, float VolumeScale = 1.f, float PitchScale = 1.f);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Sound") bool HasSound(FName Key) const;
	/** tests: record what the audio device puts out (the main submix), then write it as <Dir>/<Name>.wav (Python cannot
	 *  reach the engine's AudioMixerBlueprintLibrary here) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Sound") void StartRecordingOutput(float Seconds);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Sound") void StopRecordingOutput(const FString& Dir, const FString& Name);
	/** how often each key was played since play began (tests, the demo reel's record) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Sound") int32 GetSoundCount(FName Key) const { const int32* N = SoundCounts.Find(Key); return N ? *N : 0; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Sound") TMap<FName, int32> GetSoundCounts() const { return SoundCounts; }
	/** the fires that have a voice now: where they are */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Sound") TArray<FVector> GetFireLoops() const;
	/** the level a sound of Key has at a distance from her, against its level beside her (0..1) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Sound") float GetSoundLevelAt(FName Key, float Distance) const;
	USoundAttenuation* GetAttenuation(const FRDSoundSet& Set);
	/** tests: where the audio device has the listener and its attenuation point now */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Sound") FString DescribeListener() const;
	/** tests: how loud the game is while its window does not have the focus (the engine's default is silent) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Sound") static void SetUnfocusedVolume(float Multiplier);

	// ---- random_dungeonmagic_level5: the player's volumes (the Escape menu's sliders), kept in the game's user settings:
	// overall, action (her, the monsters, the fighting, the spells), environment (fires, doors, containers, the dungeon's
	// own sounds and the atmosphere layers), music. 0..1 each; a sound plays at overall x its category.
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Menu") float GetUserVolume(int32 Category) const { return UserVolumes[FMath::Clamp(Category, 0, 3)]; }
	/** sets one (0 overall, 1 action, 2 environment, 3 music), applies it to what is playing and saves it */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Menu") void SetUserVolume(int32 Category, float Value);
	/** the category a sound occasion belongs to (1 action, 2 environment, 3 music) */
	static int32 SoundCategory(FName Key);
	/** overall x the category of an occasion */
	float UserVolumeOf(FName Key) const { return UserVolumes[0] * UserVolumes[SoundCategory(Key)]; }

	// ---- random_dungeonmagic_level5: the Escape menu (Escape opens and closes it; it pauses the game). Its lines: the four
	// volumes, then RESUME, CHOOSE ANOTHER HERO (the menu level), QUIT (ends play in the editor, quits the game).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Menu") bool bEscapeMenu = false;
	/** the open menu pauses the game (off for a reel: the Movie Render Queue renders a world that goes on) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Menu") bool bMenuPausesGame = true;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Menu") void SetMenuOpen(bool bOpen);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Menu") bool IsMenuOpen() const { return bMenuOpen; }
	/** the list of 2026-11-08b: since when the gamepad's Start has been held with nothing open (-1: not), and how often its hold
	 *  opened the menu (tests) */
	double StartHeldSince = -1.0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Menu") int32 MenuOpensByStart = 0;
	/** the gamepad's Start as the device sends it (a Slate input processor, before any widget, the focus or the input mode): a
	 *  press and a release of its own. The player controller's state cannot be trusted for a hold: closing the inventory
	 *  changes the input mode, a change of focus flushes the held keys with simulated releases, and a Start held through it
	 *  read as let go (PR #29's review; test_b9a). A test's SimulateKey reaches only the controller: used when the device has
	 *  sent no Start this play */
	TSharedPtr<class IInputProcessor> StartKeys;
	double RawStartDownAt = -1.0, RawStartHandledAt = -1.0;
	bool bRawStartDown = false, bRawStartSeen = false;
	/** the hold and the tap forgotten (the menu or a town panel opened or shut: a Start pressed before is not acted on after) */
	void ResetStartHold();
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;
	/** r.VolumetricRenderTarget.Mode before this level's sky set it (RDSky.cpp), put back at EndPlay; -1 not set */
	int32 VrtModeWas = -1;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Menu") int32 GetMenuCursor() const { return MenuCursor; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Menu") void MoveMenuCursor(int32 Step);
	/** the list of 2026-11-12 ("pick from a screen of choices instead of scrolling choices"): the Load page and the Save page's
	 *  saves to save over are cards, RDMenuGridCols a row, Back under them; the keys move by a card or a row */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Menu") void MoveMenuGrid(int32 Dx, int32 Dy);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Menu") bool IsMenuGridPage() const { return bOptionsMenu && (MenuPage == 2 || MenuPage == 4); }
	static constexpr int32 RDMenuGridCols = 3;
	static constexpr int32 RDMenuGridMax = 18;          // (cards on the screen: six rows)
	/** a slider under the cursor one step (Step: -1 / 1) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Menu") void StepMenuValue(int32 Step);
	/** the line under the cursor (or Line): a button is pressed; false on a slider */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Menu") bool ActivateMenuLine(int32 Line = -1);
	/** the menu's lines: "volume|<label>|<value>" and "button|<label>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Menu") TArray<FString> GetMenuLines() const;
	/** the HUD's last drawing of the menu: each line's box on the screen and a slider's track (the mouse reads them) */
	TArray<FBox2D> MenuRowBoxes, MenuTrackBoxes;
	/** what the last button did ("quit", "hero", "resume"; tests) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Menu") FString LastMenuAction;
	/** a test does not leave or quit: the button only says what it would do */
	UPROPERTY(BlueprintReadWrite, Category = "RandomDungeon|Menu") bool bMenuDryRun = false;
	/** the editor's own key for stopping play (Escape) is moved to Shift+Escape, so that Escape reaches the game in
	 *  play-in-editor (pipeline/unreal/858; it is saved in the project's editor key bindings) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Menu") static FString MoveEditorStopKey(bool bShift);

	// ---- generation indicator (same materials as random_level: M_RT_RevealPP / M_RT_RevealCurtain)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Reveal") bool bRevealEffect = true;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Reveal") TObjectPtr<UMaterialInterface> RevealPostMaterial;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Reveal") TObjectPtr<UMaterialInterface> RevealCurtainMaterial;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Reveal") float RevealDuration = 7.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Reveal") float RevealCurtainHeight = 700.f;
	static constexpr int32 RevealSlots = 6;

	// ---- content
	/** named pieces (Floor_*, Ceil_*, Wall_*, Door_*, furniture, lights...) normalised to the dungeon frame */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Content") TMap<FName, FRDPiece> Pieces;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Content") TMap<FName, TObjectPtr<UNiagaraSystem>> Effects;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Content") TArray<FRDMonsterDef> Monsters;

	// ---- state
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") TMap<FIntPoint, TObjectPtr<ARDSection>> Sections;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") TMap<FIntPoint, FRDSectionMap> MapData;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") int32 SessionSeed = 0;
	/** tests and the reels: the session seed alone (what the containers hold follows it; nothing is rebuilt: RestartPlay
	 *  for that). A reel looks for a seed whose containers hold what it wants to show. */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") void SetSessionSeed(int32 Seed) { SessionSeed = Seed; }
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") int32 SectionsGenerated = 0;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") int32 SectionsRemoved = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") bool bMapOpen = false;
	/** the tactical big map's scroll, world cm from her (X north, Y east): the arrow keys (the D-pad on the gamepad) scroll
	 *  it while it is open, C (the right stick pressed) brings it back over her; it opens over her */
	UPROPERTY(BlueprintReadWrite, Category = "RandomDungeon") FVector2D MapPan = FVector2D::ZeroVector;
	/** how fast it scrolls (cm of the dungeon a second) and how far from her it may go */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon") float MapPanSpeed = 4000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon") float MapPanMax = 40000.f;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") void CenterMap() { MapPan = FVector2D::ZeroVector; MapZoom = 1.f; }
	/** Brokenspire's map (the third list, 2026-11-02: zoomed and moved): 1 the whole town, up to MapZoomMax; MapPan is then
	 *  the view's middle from the town's. The wheel, + and - and the right stick zoom; a drag with the left mouse button, the
	 *  arrow keys and the D-pad move it (as fast on the screen at every zoom); C or R3 shows the whole town again */
	UPROPERTY(BlueprintReadWrite, Category = "RandomDungeon") float MapZoom = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon") float MapZoomMax = 6.f;
	// ---- Brokenspire's map from above (RDTownSat.cpp; the user's of 2026-11-03: "a semi-realistic top down representation of
	// the terrain features, much like what you would see from a satellite"): one picture of the town straight down, taken a
	// few seconds after it is in place, lit at TownSatelliteHour, a fixed exposure (EV bias)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") bool bTownSatellite = true;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") int32 TownSatelliteSize = 4096;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float TownSatelliteDelay = 4.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float TownSatelliteHour = 12.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float TownSatelliteExposure = 0.f;
	/** the sun's shadows in the picture (an orthographic capture's shadow maps can cover nothing: everything in shadow) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") bool bTownSatelliteShadows = false;
	/** the picture's colours: 0 lit (the final colour), 1 the materials' own colours (base colour, unlit), 2 the lit picture
	 *  with the base colour mixed in by TownSatelliteMix; Lumen's light kept or not */
	// (1 since the first pictures (2026-11-03): lit, the town's dark shingle and slate roofs came out near black beside the
	// bright grass at every exposure; the materials' own colours read as a noon satellite picture does, and need no light)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") int32 TownSatelliteSource = 1;
	/** how much brighter the map draws the picture (an added pass: the canvas clamps a tint at 1) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float TownSatelliteBrighten = 0.25f;
	/** Lumen's light in the lit picture (never for the base colour: it has no light; a first frame has no Lumen history) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") bool bTownSatelliteLumen = true;
	UPROPERTY(Transient, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TObjectPtr<class UTextureRenderTarget2D> TownSatellitePicture;
	UPROPERTY(Transient, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TObjectPtr<class USceneCaptureComponent2D> TownSatCap;
	/** the picture's middle (world XY) and half its width (cm) */
	FVector2D TownSatCenter = FVector2D::ZeroVector;
	float TownSatHalf = 0.f;
	int32 TownSatStep = 0, TownSatCaptures = 0;
	bool bTownSatLit = false;
	float TownSatWait = 0.f, TownSatHourWas = 0.f;
	double TownSatMs = 0.0;
	TArray<TPair<TWeakObjectPtr<class UInstancedStaticMeshComponent>, FIntPoint>> TownSatCulls;
	int32 TownSatHidden = 0;
	void TickTownSatellite(float Dt);
	/** the hour and the plants' fading held for a capture under way put back (a capture begun again or a town rebuilt) */
	void ReleaseTownSatHold();
	/** the map draws the picture: one taken of this town and finished (the painted map while a new one is taken) */
	bool HasTownSatellite() const { return TownSatellitePicture && TownSatCaptures > 0 && TownSatStep >= 3 && !bTownSatHidden15; }
	/** a test's: the town map drawn painted though its picture from above is there (the list of 2026-11-20's symbols in both modes) */
	UPROPERTY(Transient, BlueprintReadWrite, Category = "RandomDungeon|List15") bool bTownSatHidden15 = false;
	/** the picture taken again (tests, a reel): from the next frame on */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Brokenspire") void RecaptureTownSatellite() { ReleaseTownSatHold(); TownSatStep = 0; TownSatWait = TownSatelliteDelay; }
	/** "<step: 3 done>|<size px>|<middle x>|<middle y>|<half width cm>|<capture ms>|<captures>|<components hidden>|<mips>|<camera z>|<culls held>" (tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") FString GetTownSatelliteState() const;
	/** the town map's input, a frame (TickTown's part; tests call it with keys sent) */
	void TickTownMapInput(APlayerController* PC, float Dt);
	/** the town map's screen pixels per cm of the town at zoom 1 (the HUD sets it as it draws) and screen pixels a unit of
	 *  the mouse's delta */
	float TownMapPxPerCm = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon") float TownMapDragPx = 1.f;

	/** (editor) clear everything and build the start section with StartSeed; saved with the level */
	UFUNCTION(CallInEditor, BlueprintCallable, Category = "RandomDungeon") void BuildStartSection();
	UFUNCTION(CallInEditor, BlueprintCallable, Category = "RandomDungeon") void ClearAll();

	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") FIntPoint WorldToSection(FVector Location) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") FIntPoint WorldToTile(FVector Location) const;
	/** first global tile of a section */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") FIntPoint SectionMinTile(FIntPoint Section) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") FVector TileCenter(FIntPoint Tile) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") bool IsSectionGenerated(FIntPoint Section) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") ARDSection* GetSection(FIntPoint Section) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") TArray<FIntPoint> GetSectionCoords() const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") bool GenerateSectionNow(FIntPoint Section);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") int32 GetQueueLength() const { return Queue.Num(); }
	/** centre of the start section's great hall (player spawn) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") FVector GetStartRoomCenter() const;
	/** toggles the nearest door or container within MaxDistance of From (what F does); returns a description or "" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") FString InteractNearest(FVector From, float MaxDistance = 260.f);
	/** what F would do here ("open door", "close chest"...) or "" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") FString DescribeNearest(FVector From, float MaxDistance = 260.f) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") int32 GetNumMonsters() const;
	/** what M does (scripts / tests) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") void SetMapOpen(bool bOpen) { if (bOpen && !bMapOpen) { MapPan = FVector2D::ZeroVector; MapZoom = 1.f; if (IsWildMapShown()) OpenWildMap(); } bMapOpen = bOpen; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") TArray<ARDMonster*> GetMonsters() const;
	/** discovered rooms / all rooms (generated) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") void GetDiscoveryStats(int32& DiscoveredRooms, int32& GeneratedRooms) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") static FString KindName(ERDRoomKind Kind);

	bool IsStartSection(FIntPoint S) const { return S == FIntPoint::ZeroValue; }
	int32 SectionSeed(FIntPoint S) const;
	/** block rows / columns with a hallway across each section edge */
	static bool IsPortalBlock(int32 B) { return B == 1 || B == 3 || B == 5; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") AActor* GetTrackedActor() const;
	const FRDPiece* Piece(FName Name) const { const FRDPiece* P = Pieces.Find(Name); return (P && (P->Mesh || P->ActorClass)) ? P : nullptr; }
	/** world time of the last section reveal (HUD flash) */
	float LastRevealTime = -100.f;
	FIntPoint LastRevealSection = FIntPoint::ZeroValue;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

public:
	// ---- mistward_castle: what the tiers' openings set waiting (a boss and its band, a guarded ring)
	struct FEncounter
	{
		int32 Tier = 2; bool bBoss = false; FIntPoint Section = FIntPoint::ZeroValue; int32 Room = -1; FVector At = FVector::ZeroVector;
		TArray<int32> Kinds; TArray<FVector> Spots; TArray<bool> Dead; TArray<TWeakObjectPtr<ARDMonster>> Live;
		FName Ring = NAME_None; FIntVector RingKey = FIntVector(0, 0, -1); FString Label;
		/** the third list: a throne room's usurper (its room, not a tier's opening) */
		bool bThrone = false;
		/** the castle's final boss (RDAurorim.cpp): tier 5 at its share, the door to Brokenspire beside it */
		bool bFinal = false;
	};
	TArray<FEncounter> Encounters;
	/** a set of rooms is generated (again): the encounters in it come back (the living ones) */
	void RespawnEncounters(ARDSection* S);
	/** the traps already spent or disarmed (section, index): they stay so */
	TMap<FIntVector, uint8> SpentTraps;
	/** the trap she is disarming (section, index), when she began, where she stood */
	FIntVector DisarmKey = FIntVector(0, 0, -1);
	float DisarmStart = -100.f;
	FVector DisarmFrom = FVector::ZeroVector;
	FRandomStream TrapR;
	void TickTraps(float Dt);
	bool BeginDisarmNear(const FVector& From);
	FString DescribeTrapNear(const FVector& From) const;

private:
	// ---- mistward_castle
	/** what a set of rooms she has not reached holds (rooms, chests and trunks, monsters): counted once, a few a frame */
	mutable TMap<FIntPoint, FIntVector> CensusCache;
	mutable TArray<FIntPoint> CensusQueue;
	float CensusLookTime = -100.f;
	void TickCensus();
	void CheckTierOpenings();
	void OnTierOpened(int32 Tier);
	/** false: no room of the tier before seen yet to set it in (nothing placed) */
	bool PlaceBoss(int32 Tier);
	bool PlaceRingGuard(int32 Tier);
	/** an explored room of a tier to set something in (not the one she is in, generated now); false: none */
	/** a room a tier's boss or guards may stand in (explored, not hers, room to stand): its set, its index, her distance, its floor's
	 *  height in the world */
	struct FExploredRoom { ARDSection* S = nullptr; int32 Room = -1; float D = 0.f; float Z = 0.f; };
	void ExploredRooms(int32 Tier, TArray<FExploredRoom>& Out) const;
	bool PickExploredRoom(int32 Tier, int32 Salt, ARDSection*& OutSection, int32& OutRoom) const;
	UPROPERTY(VisibleAnywhere, Category = "RandomDungeon|Reveal") TObjectPtr<UPostProcessComponent> RevealPost;
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> RevealMID;
	UPROPERTY(Transient) TObjectPtr<ARDSection> Building;
	/** while the big map is open: an input context over the pawn's own that takes the arrow keys (the project's move action
	 *  has them too: scrolling walked her) */
	UPROPERTY(Transient) TObjectPtr<class UInputMappingContext> MapScrollContext;
	UPROPERTY(Transient) TObjectPtr<class UInputAction> MapScrollAction;
	bool bMapScrollInput = false;
	/** the list of 2026-11-12: the mouse kept off the camera over a dungeon's map with the pointer up (rd.MapTeleport) */
	UPROPERTY(Transient) TObjectPtr<class UInputMappingContext> MapMouseContext;
	bool bMapMouseInput = false;
	void UpdateMapScrollInput(APlayerController* PC);
	UPROPERTY(Transient) TObjectPtr<URDCombatComponent> PlayerCombat;
	UPROPERTY(Transient) TObjectPtr<URDBloodComponent> Blood;
	/** the fall safety net: where the player last stood on the ground */
	FVector LastSafeSpot = FVector::ZeroVector;
	bool bHasSafeSpot = false;
	UPROPERTY(Transient) TMap<int32, TObjectPtr<USoundAttenuation>> Attenuations;
	UPROPERTY(Transient) TArray<TObjectPtr<UAudioComponent>> FireComps;
	float UserVolumes[4] = { 1.f, 1.f, 1.f, 1.f };
	bool bMenuOpen = false;
	// (mistward4: the Escape menu's page, the controls hint, the menu's items by name on the page shown)
	int32 MenuPage = 0;
	bool bControlsShown = true;
	TArray<FName> MenuItems() const;
	/** from the Options or Load page back to the main page, the cursor on the line that opened it */
	void BackToMainMenu();
	void LoadOptions();
	void OpenOptionsPage();
	int32 MenuCursor = 0;
	float MenuRepeat = 0.f;
	bool bMenuDragging = false;
	void LoadUserVolumes();
	void ApplyUserVolumes();
	void TickMenu(APlayerController* PC);
	void TickAllies(float Dt);
	/** wandering music, battle music, wandering atmosphere, battle atmosphere */
	UPROPERTY(Transient) TArray<TObjectPtr<UAudioComponent>> MusicComps;
	float MusicPos[4] = { 0.f, 0.f, 0.f, 0.f };
	int32 MusicIndex[4] = { 0, 0, 0, 0 };
	bool bMusicOn = false, bCombatMusic = false;
	float LastFightTime = -100.f;
	void TickMusic(float Dt);
	void StartMusicLayer(int32 Layer, float FadeSeconds, bool bFromStart);
	void StopMusic();
	FString MusicLayerName(int32 Layer) const;
	struct FFireVoice { FVector At = FVector::ZeroVector; uint8 Kind = 0; bool bOn = false; };
	TArray<FFireVoice> FireVoices;
	TMap<FName, int32> SoundCounts, LastSoundPick;
	FRandomStream SoundR;
	float FireTimer = 0.f;
	bool bSpatializeNow = true;
	// sound self test (-RDSoundTest=<dir>: records the game's output while sounds are played at known places, then quits)
	FString SoundTestDir;
	float SoundTestTime = 0.f;
	double SoundTestClock = 0.0;
	int32 SoundTestStep = -1;
	TArray<FString> SoundTestLog;
	void TickSoundTest(float Dt);
	void UpdateFireLoops(const FVector& Listener);
	int32 NextRevealSlot = 0;
	TArray<FIntPoint> Queue;
	ARDSection* SpawnSection(FIntPoint S, bool bEditorBuild, bool bReveal = false);
	void StartReveal(ARDSection* Section);
	void Enqueue(FIntPoint S);
	void UpdateDiscovery(const FVector& L);

public:
	// ---- the wilderness (RDWild*.cpp; the user's spec of 2026-11-03, docs/wilderness.txt): a continent of 300 x 300 km made
	// from one seed as she comes to it, in chunks round her (a 2 km square of them at most), the towns loaded as she nears
	// them and dropped 2 km off, its map revealed where she has been
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") bool bWild = false;
	/** the user's terrain templates (887 from SourceArt/wilderness/biomes.json) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") TArray<FRDWildBiome> WildBiomes;
	/** the world's seed for tests (0: the game's own, new for each new game, kept in the save) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") int32 WildSeedFixed = 0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float WildChunkM = 250.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float WildStepM = 2.f;
	/** half the active square: a chunk is made when its middle is within this of her on both axes (the spec's 2 km square) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float WildActiveM = 1000.f;
	/** and dropped when its middle is farther than this on an axis */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float WildDropM = 1125.f;
	/** the chunks within this of her have their grass and their trees' collision */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float WildNearM = 140.f;
	/** a town is loaded when she comes within this of its middle, dropped when farther than WildTownDropM (the spec's 2 km) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float WildTownLoadM = 1600.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float WildTownDropM = 2000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") int32 WildMaxInFlight = 8;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float WildBuildBudgetMs = 5.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") TObjectPtr<UMaterialInterface> WildGroundMaterial = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") TObjectPtr<UMaterialInterface> WildWaterMaterial = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") TObjectPtr<UMaterialInterface> WildSeaMaterial = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") TObjectPtr<UMaterialInterface> WildSpringMaterial = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") TObjectPtr<UMaterialInterface> WildLavaMaterial = nullptr;
	/** the places' props by name ("house1", "tent2", "stone3", "bones1", ...: RDWildPlaces.cpp takes them by prefix) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") TMap<FName, TObjectPtr<UStaticMesh>> WildPieces;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") TObjectPtr<UNiagaraSystem> WildSteamFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") TObjectPtr<UNiagaraSystem> WildFireFx = nullptr;
	/** she reveals the map this far round her; finds a place this near it (a town within its section) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float WildRevealM = 500.f;          // (the list of 2026-11-16: the maps uncovered out to 500 m round her; 300 m before)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float WildDiscoverM = 500.f;          // (the list of 2026-11-16: "increase the discovery of a point of interest on the mini map and large map out to 500m"; 90 m before)
	/** the wilderness's monsters notice her this far (cm; the halls' AggroDistance is 10 m) and give up at 1.8 times it */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float WildAggroDistance = 2500.f;
	UPROPERTY(Transient, BlueprintReadOnly, Category = "RandomDungeon|Wild") TMap<FIntPoint, TObjectPtr<ARDWildChunk>> WildChunks;
	TSharedPtr<FRDWildWorld, ESPMode::ThreadSafe> Wild;
	TSharedPtr<struct FRDWStream, ESPMode::ThreadSafe> WildStream;
	TMap<FIntPoint, TSharedPtr<struct FRDWChunkData, ESPMode::ThreadSafe>> WildKept;     // (a built chunk's near plants and places)
	TSet<FIntPoint> WildInFlight;
	int32 WildTicket = 0, WildBuilt = 0, WildDropped = 0, WildMaxActive = 0, WildTicks = 0, GenTicks = 0;
	double WildComputeMs = 0.0, WildBuildMsMax = 0.0, WildBuildMsLast = 0.0;
	float WildLookTimer = 0.f;
	/** the map's fog: 50 m cells revealed, in blocks of 32 x 32 (a bit each) */
	TMap<FIntPoint, TArray<uint64>> WildRevealed;
	int32 WildRevealedCells = 0;
	int32 WildRevealVersion = 0;
	/** the places she has found (their ids) */
	TSet<int32> WildFound;
	FString WildLastFound;
	void StartWild();
	void TickWild(float Dt, APlayerController* PC);
	/** a chunk made from its computed data all at once (she is put on it; or streamed, with bWildBuildSteps off: bStreamed
	 *  counts it in the making's measures) */
	void BuildWildChunk(const TSharedPtr<struct FRDWChunkData, ESPMode::ThreadSafe>& D, bool bStreamed = false);
	/** the chunks being made over frames (2026-11-07: one chunk's making took 45 to 72 ms in a frame): each step is one
	 *  part (the ground with its collision, the water, the wading floor, one plant mesh's instances, the places), as many
	 *  as fit the frame's WildBuildBudgetMs */
	struct FWildBuild
	{
		TSharedPtr<struct FRDWChunkData, ESPMode::ThreadSafe> D;
		TWeakObjectPtr<ARDWildChunk> C;
		int32 Step = 0, Inst = 0;
		/** how many of the plant entry Inst's instances are added (a big entry goes in parts) */
		int32 InstAt = 0;
		double Ms = 0.0;
		TMap<UStaticMesh*, UHierarchicalInstancedStaticMeshComponent*> ByMesh;
	};
	TArray<FWildBuild> WildBuilding;
	/** one step of a chunk's making; true when it is whole */
	bool StepWildBuild(FWildBuild& B);
	/** chunks made in steps (true), or each in one go (the old way, for the test's comparison) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") bool bWildBuildSteps = true;
	/** the making's measures on the game thread (streamed chunks only; a chunk she is put on is made at once): the longest
	 *  step, the longest frame's share of making, the whole of a chunk (its steps summed), per part's longest ms */
	double WildStepMsMax = 0.0, WildFrameBuildMsMax = 0.0, WildChunkMsMax = 0.0;
	TMap<FString, double> WildPartMsMax;
	int32 WildStreamBuilt = 0, WildMakeFrames = 0;
	/** "streamed|step max ms|frame max ms|chunk max ms|building now|part=ms,...|frames with making|trims|dropped|trim stage"
	 *  |game ms|render ms|RHI ms|GPU ms (tests: the counts since play began, the trim's stage (0 none, 1 its collection
	 *  asked, 2 waiting to trim) and the last frame's threads (stat unit's) tell a long frame's cause); bReset clears the maxima */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") FString GetWildBuildStats(bool bReset = false);
	void SetWildNear(ARDWildChunk* C, bool bNear);
	void RevealWild(const FVector2D& AtM, float RadiusM);
	bool IsWildRevealed(double Xm, double Ym) const;
	/** the ground's z (cm) under a world point in the wilderness (the town's 0 inside a loaded town) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") float WildGroundZ(FVector At) const;
	/** the list of 2026-11-07 (RDWild8.cpp): her run speed in the wilderness for testing (rd.WildRunSpeed, -RDWildRunSpeed=):
	 *  one of 1, 5, 10, 15, 20, 30, 40 (the nearest); what is applied now (1 in a town's walls); how often she was held on the
	 *  world's height where the ground was not made yet */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") void SetWildRunSpeed(float Factor);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild") float GetWildRunSpeed() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild") float GetWildRunApplied() const { return WildRunApplied; }
	static float WildRunSpeedChoice(float Asked);
	void TickWildRunSpeed(APawn* P);
	float WildRunApplied = 1.f, WildRunBaseAccel = 1200.f, WildRunBaseBrake = 1000.f, WildRunLogged = 1.f;
	/** the movement the run speed was applied to (a new pawn's is applied again from its own base) */
	TWeakObjectPtr<UObject> WildRunMove;
	bool bWildRunCmdRead = false;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Wild") int32 WildRunHeld = 0;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") bool IsWildReady() const;
	/** "ready|seed|init s|chunks|in flight|built|dropped|max active|compute ms avg|build ms max|revealed cells|found|towns" (tests) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") FString GetWildState() const;
	/** one line per chunk: "x|y|instances|triangles|near|collision" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") TArray<FString> GetWildChunkLines() const;
	/** what the world has at a point (world cm): "h m|z cm|biome|biome2|w1|water kind|water m|rock|snow|sand|road|field|canopy|lava|tier" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") FString GetWildSampleAt(FVector At) const;
	/** "name|kind|x m|y m|h m|style" per town */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") TArray<FString> GetWildTownLines() const;
	/** per biome "name|cells|nearest site x m|y m|distance km" (the templates' census) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") TArray<FString> GetWildBiomeLines() const;
	/** rivers, lakes and roads: "river|points|length km|width m", "lake|x|y|r|level", "road|from|to|length km" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") TArray<FString> GetWildFeatureLines() const;
	/** the places of the 4 km cells round a world point (cm), within RadiusM: "id|kind|name|x m|y m|h m|tier|found" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") TArray<FString> GetWildPlacesNear(FVector At, float RadiusM) const;
	/** a picture of the world from above (colours and relief), metres, to a PNG (tests, the docs) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") bool WildDebugMap(const FString& Path, int32 Px, float X0m, float Y0m, float X1m, float Y1m, bool bFog = false);
	/** her put at a world point (metres) on the ground there, the chunks round it made first (tests) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") bool WildPutHer(float Xm, float Ym);
	/** the process's memory in use, MB (tests: what the chunks and towns cost and give back) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") float GetMemoryMB(bool bCommitted = false) const { const FPlatformMemoryStats St = FPlatformMemory::GetStats(); return (float)((bCommitted ? St.UsedVirtual : St.UsedPhysical) / (1024.0 * 1024.0)); }
	/** the memory of dropped chunks and towns given back to the system: a collection asked for, then the allocator trimmed
	 *  (the allocator kept what was freed: the editor's committed memory grew 12 GB over a test and the machine ran out) */
	void WildAskTrim() { bWildTrimPending = true; WildTrimAt = -1.0; }
	bool bWildTrimPending = false;
	double WildTrimAt = -1.0, WildLastTrim = 0.0;
	int32 WildDroppedAtTrim = 0, WildTrims = 0;
	/** a point of the map revealed (metres) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") bool WildRevealedAt(float Xm, float Ym) const { return IsWildRevealed(Xm, Ym); }
	/** every chunk dropped (tests: the memory back) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") void WildDropAll();
	/** a piece's scale (WildPieces' meshes by their asset name) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") TMap<FName, float> WildPieceScale;
	/** a small town's section, tiles (Brokenspire's is its SectionTiles) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") int32 WildSmallTownTiles = 120;
	/** the tile grid's origin: the loaded town's middle (cm; z 0). Every town is section (0, 0) of it */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Wild") FVector GridOrigin = FVector::ZeroVector;
	/** the wilderness's monsters' section (no tiles: they live on open ground) */
	UPROPERTY(Transient) TObjectPtr<ARDSection> WildSection;
	/** the loaded town is Brokenspire (its castle and Mistgate, its quests and guards) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Wild") bool bTownHome = true;
	int32 HomeSectionTiles = 168, HomeTownSeed = 0;
	FString HomeTownName;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Wild") int32 WildTownIdx = -1;
	/** the town section's plan (FRDWildTown::Plan): 0 Brokenspire's, 1 the holy city (Vel Morrath: RDHoly.cpp) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Wild") int32 TownPlan = 0;
	bool bTownLoading = false, bInTownWalls = true;
	double TownLoadStart = 0.0;
	float TownLoadSeconds = 0.f, LoadedTownDistM = 0.f;
	int32 WildTownsLoaded = 0, WildTownsDropped = 0, WildMonstersSpawned = 0;
	TSet<FIntPoint> WildStale;
	uint32 WildGameSeed() const;
	void AskWildChunk(FIntPoint C);
	void WildTownHole(struct FRDWChunkData& D) const;
	void TickWildPlaces(const FVector2D& AtM);
	void TickWildTowns(const FVector2D& AtM);
	void SpawnWildPlaces(ARDWildChunk* C, const TArray<FRDWildPlace>& Places);
	void WildPiecesOf(const FString& Prefix, TArray<UStaticMesh*>& Out) const;
	// ---- the farmsteads (the list of 2026-11-08b, RDWildFarm.cpp): a farmhouse, a barn, a fenced paddock with its animals
	// (the town's farm animals, ARDTownAnimal on the wild ground), a well, hay, a cart; the farm's family at their work, who
	// say a line of their own when she speaks to them (F)
	void SpawnWildFarm(ARDWildChunk* C, const FRDWildPlace& P);
	/** the farmsteads of chunks made, laid one a frame (TickWildFarms) */
	TArray<TPair<TWeakObjectPtr<ARDWildChunk>, FRDWildPlace>> WildFarmQueue;
	void TickWildFarms();
	/** the farm folk's lines, "<who>|<line>" (who: farmer, farmwife, farmhand, child, or any: every one's); 899 farms writes
	 *  them from SourceArt/wilderness/farms.json */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") TArray<FString> WildFarmLines;
	/** how many animals a paddock holds, at most (each kind's PenMin to PenMax, kept to this) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") int32 WildFarmAnimalsMax = 6;
	struct FRDWildFarmRec
	{
		int32 Id = 0; FString Name; FVector2D At = FVector2D::ZeroVector; float Yaw = 0.f;
		FVector PenAt = FVector::ZeroVector; FVector2D PenHalf = FVector2D::ZeroVector; float PenYaw = 0.f;
		int32 Props = 0, FenceGap = 0;
		TWeakObjectPtr<ARDWildChunk> Chunk;
		TArray<TWeakObjectPtr<ARDTownAnimal>> Animals;
		/** each animal's own pen: its middle (cm) and half sizes (cm, along and across the farm's way) */
		TArray<FVector4> AnimalPens;
		TArray<TWeakObjectPtr<ARDTownsfolk>> Folk;
		/** the list of 2026-11-11's fourth phase: its design (FarmDesigns' index; -1 the old fixed layout), its buildings, the
		 *  containers and gardens in it; what it made (its components, and its doors', houses' and clears' ranges in its chunk), so
		 *  a test's farm can be taken away again */
		int32 Design = -1, Buildings = 0, Boxes = 0;
		TArray<TWeakObjectPtr<UActorComponent>> Comps;
		int32 Door0 = 0, Door1 = 0, House0 = 0, House1 = 0, Clear0 = 0, Clear1 = 0;
		/** the list of 2026-11-16's seventh phase: its farmhouse's beds (each bed's middle on the floor and its yaw: the foot +X) and the
		 *  house's floor height */
		TArray<FTransform> Beds14; float HouseFloor14 = 0.f;

		/** each animal's pen's yaw (a barn's stall turns with its barn; AnimalPens' half sizes are along and across it) */
		TArray<float> AnimalPenYaws;
		/** its pieces as instances, one component a mesh, material and collision (PR #49's review: a component a piece was several
		 *  hundred in one frame) */
		TMap<FString, TWeakObjectPtr<class UInstancedStaticMeshComponent>> Batch;
	};
	/** one piece of a farm as an instance of its batch (world transform) */
	class UInstancedStaticMeshComponent* WildFarmInstance(ARDWildChunk* C, FRDWildFarmRec& Rec, UStaticMesh* M, const FTransform& World, bool bCollide, UMaterialInterface* Mat, bool bUnseen = false);
	TArray<FRDWildFarmRec> WildFarms;
	/** the list of 2026-11-16's seventh phase (RDList14f.cpp): a farm's family member given its home in the farmhouse and its own bed (the K-th) if there is one */
	void SetWildFarmFolkHome14(class ARDTownsfolk* T, const FRDWildFarmRec& Rec, const FVector& DoorOut, const FVector& HouseIn, int32 K);
	/** the list of 2026-11-20: a wild household member's home (its door outside, its place inside side by side with the others, its K-th
	 *  bed if there is one), a farm's or a village's */
	void SetWildFolkHome15(class ARDTownsfolk* T, const TArray<FTransform>& Beds, const FVector& DoorOut, const FVector& HouseIn, int32 K);
	/** the wilds' townsfolk bodies by kind: grown men, grown women, children (the defs with a mesh and no town of their own) */
	void WildBodyPools15(TArray<int32>& Men, TArray<int32>& Women, TArray<int32>& Kids) const;
	/** the seventh phase's second part (RDList14g.cpp): a farm animal's kill key (from its farm's id and its place in the farm's
	 *  plan), whether it was killed in this game, and the farm animals her blows and bolts reach */
	int64 FarmAnimalKey14(const FRDWildFarmRec& Rec, int32 Slot, int32 K) const;
	bool IsFarmAnimalKilled14(int64 Key) const;
	/** the farm animals killed in this game, read once for each farm laid (WildKilled holds every kept kill, container and use) */
	TSet<int64> FarmKilled14; int32 FarmKilledFor14 = MIN_int32;
	void ReadFarmKilled14(int32 FarmId);
	void OnFarmAnimalKilled14(class ARDTownAnimal* A);
	/** "Item|min|max|chance" lines drawn from a hash: the wild animals' and the farms' things */
	TArray<FName> RollDropLines(const TArray<FString>& Lines, uint32 H0) const;
	int32 HitFarmAnimalsInArc14(const FVector& L, const FVector& Fw, float Reach, float MinCos, float Dmg, FName Sound);
	/** the list of 2026-11-16's eighth phase (RDList14h.cpp, 930): the wilds' people struck, killed and looted; a wild monster takes a
	 *  person nearer than her within WildFolkPreyCm14 for its foe */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") bool bWildFolkHurt14 = false;
	/** "who|health|gold min|gold max|Item|min|max|chance;..." by a whole word of a person's title, its role, or "default" (the table's
	 *  order first); health and gold grow with the wilds' tier */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") TArray<FString> WildFolkLoot14;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") float WildFolkPreyCm14 = 2000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") float WildFolkRunSpeed14 = 260.f;
	/** a monster takes a person for its foe only within this of her (cm): what happens far from her is not played out */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") float WildFolkNearHerCm14 = 15000.f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List14") int32 WildFolkKilled14 = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List14") TArray<FName> LastWildFolkDrops14;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List14") int32 LastWildFolkGold14 = 0;
	/** every person of the wilds' lists (the farms', the structures' and scenery's, the director's, the travellers') */
	const TArray<class ARDTownsfolk*>& WildPeople14() const;
	mutable TArray<class ARDTownsfolk*> WildPeopleCache14; mutable uint64 WildPeopleFrame14 = MAX_uint64, WildPeopleGC14 = MAX_uint64;
	/** the garbage collections so far (the frame's lists of plain pointers are gathered again after one: the package of 2026-11-22) */
	static uint64 WildGCCycle14();
	/** a person a wild monster at From may take for its foe: it can die, it is out in the open, in sight, within WildFolkNearHerCm14 of her */
	bool IsWildPrey14(const class ARDTownsfolk* T, const FVector& From) const;
	FString WildFolkLootOf14(const class ARDTownsfolk* T, float& Health, int32& GoldLo, int32& GoldHi) const;
	int32 HitWildFolkInArc14(const FVector& L, const FVector& Fw, float Reach, float MinCos, float Dmg, FName Sound, AActor* Her);
	class ARDTownsfolk* WildFolkOnSegment14(const FVector& A, const FVector& B, float Pad, float& OutT, FVector& OutAt) const;
	void OnWildFolkKilled14(class ARDTownsfolk* T, AActor* By);
	static int64 WildFolkKey14(int32 Kind, int64 Id, int32 N);
	bool IsWildFolkDead14(int64 Key) const;
	/** a person laid with its chunk given its key, and laid dead when it was killed in this game */
	void KeepWildFolk14(class ARDTownsfolk* T, int64 Key);
	/** the ninth phase (RDList14i.cpp): locks and who notices; WildKilled as a set (read again when it changes) */
	bool IsWildKeyKept14(int64 Key) const;
	mutable TSet<int64> WildKept14; mutable int32 WildKeptRead14 = -1; mutable int64 WildKeptLast14 = 0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") bool bWildLocks14 = false;
	/** the share of the wild containers (not the gardens) locked, by a hash of each one's key */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") float WildLockShare14 = 0.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") float WildPickSeconds14 = 2.f;
	/** a lock picked or broken: heard within this (cm), seen within that with a clear line to her */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") float WildHearCm14 = 3000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") float WildSeeCm14 = 4000.f;
	/** a hostile person's blow (grown with the wilds' tier) and how far she must go for it to calm down (cm) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") float WildFolkBlow14 = 6.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") float WildCalmCm14 = 8000.f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List14") int32 WildLocksPicked14 = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List14") int32 WildLocksBroken14 = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List14") int32 WildLocksRefused14 = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List14") int32 LastWildAlertHeard14 = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List14") int32 LastWildAlertSeen14 = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List14") int32 WildFolkBlowsOnHer14 = 0;
	bool IsWildBoxLocked14(FName Kind, int64 Key) const;
	FString WildLockDescribe14(FName Kind) const;
	FString WildLockInteract14(class ARDWildChunk* C, int32 Index);
	void TickWildPick14();
	/** everyone who hears or sees a lock picked or broken at At turns on her; how many */
	int32 AlertWildFolk14(const FVector& At);
	/** whether one with its eyes at Eye sees her (the rule a lock's witnesses are taken by; tests) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List14") bool WildSeesHer14(FVector Eye) const;
	/** the world's static and dynamic pieces between A and B (a line, or a ball of Radius swept), people, animals, pawns and piles
	 *  passed over: the wilds' sight lines and the people's steps */
	bool WildWayBlocked14(const FVector& A, const FVector& B, float Radius, const AActor* Skip) const;
	mutable TArray<AActor*> WildPass14; mutable uint64 WildPassFrame14 = MAX_uint64, WildPassGC14 = MAX_uint64;
	/** the floor under a person's step at At (its feet at FeetZ): a farmhouse's over the ground, else the ground */
	float WildFloorZ14(const FVector& At, float FeetZ) const;
	/** the heroes who pick a wild lock and who break one (931 from locks14.json); a hostile person calms down after she has been
	 *  hidden this long */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") TArray<FName> LockPickers;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") TArray<FName> LockBreakers;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") float WildLostCalmSeconds14 = 6.f;
	/** tests: every person calmed, a pick under way dropped */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List14") void CalmWildFolk14();
	/** the list of 2026-11-16's eleventh phase: an older world's save loaded (RDSave.cpp's DropOldWorld): the line she is told, and how
	 *  many of the captain's wild quests were given back (tests) */
	FString WildOldWorldNotice;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List14") int32 WildOldWorldQuestsBack = -1;
	int32 GiveBackWildQuests14();
	/** tests: an older world's save's drop, here and now; the captain's wild quests given back */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List14") int32 DebugOldWorld14();
	/** tests: whether a road between towns passes within Rm metres of (Xm, Ym) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List14") bool IsNearTownRoad14(float Xm, float Ym, float Rm) const;
	/** the fourteenth phase: the roads' signs laid within this of her (m) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") bool bWildSigns14 = true;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") float WildSignShowM14 = 300.f;
	/** tests: the signs within RadiusM of At (cm): "index|kind|x|y|yaw|A|Am|B|Bm|road" (metres) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List14") TArray<FString> GetWildSigns14(FVector At, float RadiusM) const;
	/** tests: the signs laid: "index|x|y|z (cm)|meshes|texts|each text;" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List14") TArray<FString> GetWildSignActors14() const;
	/** tests: a road's points (x, y metres; z its bed's height over the sea) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List14") TArray<FVector> GetWildRoadPoints14(int32 Road) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List14") FString GetWildRoadInfo14(int32 Road) const;
	/** tests: the minor road that leads to a place (its id), else -1 */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List14") int32 FindWildRoadTo14(int32 PlaceId) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List14") FString GetWildMinorStats14() const;
	/** the list of 2026-11-16's tenth phase (RDList14j.cpp, 932): storms by strength (0 light, 1 moderate, 2 strong, 3 violent), drawn
	 *  with each weather that carries rain, snow or dust; lightning in a storm of moderate strength or more */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") bool bLightning14 = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") TArray<float> StormStrengthWeights14 = { 0.f, 0.45f, 0.35f, 0.2f };
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") TArray<float> RainStrengthWeights14 = { 0.4f, 0.35f, 0.18f, 0.07f };
	/** in dry land the strong and violent strengths weigh this share of theirs */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") float DryStrongShare14 = 0.5f;
	/** rain and wind times this by strength (the cover by its root) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") TArray<float> StrengthScale14 = { 0.65f, 0.85f, 1.f, 1.15f };
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") TArray<float> StrikesPerMinute14 = { 0.f, 2.f, 5.f, 10.f };
	/** a strike on her: this share of her hit points; on anyone else this blow (grown with the wilds' tier) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") TArray<float> StrikeHurtShare14 = { 0.f, 0.15f, 0.25f, 0.35f };
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") TArray<float> LightningDamage14 = { 0.f, 40.f, 70.f, 110.f };
	/** the share of strikes aimed at someone in the open within StrikeNearCm14 of her; the rest fall anywhere out to StrikeFarCm14; a
	 *  strike hurts within StrikeRadiusCm14 of where it lands; its thunder is the near set within ThunderNearCm14 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") float StrikeNearShare14 = 0.2f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") float StrikeNearCm14 = 6000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") float StrikeFarCm14 = 150000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") float StrikeRadiusCm14 = 400.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") float ThunderNearCm14 = 150000.f;
	/** the sky light's flash: its intensity times 1 + this at a strike's full flash */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") float LightningSkyBoost14 = 5.f;
	/** tests: a bolt held lit this long for its picture (0: it flickers and is gone in 0.35 s) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") float LightningHoldSeconds14 = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") TObjectPtr<UStaticMesh> LightningMesh14;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") TObjectPtr<UMaterialInterface> LightningMaterial14;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List14") int32 WeatherStrength14 = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List14") int32 LightningStrikes14 = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List14") int32 LightningOnHer14 = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List14") int32 LightningOnOthers14 = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List14") int32 LightningThunders14 = 0;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List14") void SetWeatherStrength14(int32 S);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List14") int32 GetWeatherStrength14() const { return WeatherStrength14; }
	/** tests: the game's own pick of a strength for weather W, N times: "light:n|moderate:n|strong:n|violent:n" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List14") FString CountWeatherStrengths14(int32 W, int32 N, bool bDry) const;
	/** tests: a strike at At now (how many it struck) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List14") int32 ForceLightning14(FVector At);
	/** under a roof: a house's box, a town's building, or anything over it */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List14") bool IsSheltered14(const FVector& At, const AActor* Skip) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List14") TArray<FString> GetStormLines14() const;
	static FString StrengthName14(int32 S);
	int32 PickStrength14(int32 W, uint32 H, bool bDry) const;
	void ApplyStrength14();
	void SetWeatherWants14(bool bAtOnce);
	/** the look of weather W (RDSky.cpp's table) */
	static void WeatherLookOf(int32 W, float& Cover, float& Rain, float& Wind, float& Fog, FLinearColor& Tint);
	/** a blow or death that is no doing of hers (lightning): it wakes no monster and pays her nothing */
	bool bNotHerKill14 = false;
	FName LastThunderSet14;
	int32 Strike14(const FVector& Aim);
	void TickLightning14(float Dt);
	// ---- the list of 2026-11-16's fourteenth phase (RDList14k.cpp): the roads' signs laid where she goes
	TMap<int32, TWeakObjectPtr<AActor>> WildSignActors14;
	float NextSignTick14 = -1.f;
	bool bSignMeshMissing14 = false;
	UPROPERTY(Transient) TObjectPtr<class UStaticMesh> SignPost14;
	UPROPERTY(Transient) TObjectPtr<class UStaticMesh> SignArm14;
	UPROPERTY(Transient) TObjectPtr<class UStaticMesh> SignCube14;
	AActor* SpawnWildSign14(int32 K);
	void TickWildSigns14();
	void DropWildSigns14();
	struct FBolt14 { TArray<TWeakObjectPtr<UStaticMeshComponent>> Segs; TWeakObjectPtr<class UPointLightComponent> Light; float Born = 0.f; };
	struct FThunder14 { float When = 0.f; float Dist = 0.f; };
	TArray<FBolt14> Bolts14; TArray<FThunder14> Thunders14;
	FRandomStream LightningR14;
	float LightningFlash14 = 0.f, NextStrikeAt14 = -1.f, LastStrikeTime14 = -1.f, LastThunderTime14 = -1.f;
	FVector LastStrikeAt14 = FVector::ZeroVector;
	TWeakObjectPtr<class ARDWildChunk> WildPickChunk14; int32 WildPickIndex14 = -1; int64 WildPickKey14 = -1; float WildPickUntil14 = -1.f; FVector WildPickAt14 = FVector::ZeroVector;
	/** tests: "i|title|role|x|y|z|health|dead|protected|fleeing|key|hits|flees|killed by|hurt", and the person of that index */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List14") TArray<FString> GetWildFolkLines14() const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List14") class ARDTownsfolk* GetWildPerson14(int32 I) const;
	class ARDTownAnimal* FarmAnimalOnSegment14(const FVector& A, const FVector& B, float Pad, float& OutT, FVector& OutAt) const;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List14") int32 FarmAnimalsKilled14 = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List14") TArray<FName> LastFarmAnimalDrops14;
	/** the list of 2026-11-11's fourth phase (RD/RDWildFarm11.cpp, 919 farms): the farmsteads' designs (SourceArt/wilderness/
	 *  farm_designs.json), one picked by each farmstead's id; empty: the old fixed layout */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Farm11") TArray<FRDFarmDesign> FarmDesigns;
	/** what a wild container gives by its kind ("chest", "barrel", "crate", "wardrobe", "barn", "granary", "coop", "shed"):
	 *  "Item|min|max|chance" entries joined by ";" (RollWildThings; one roll at least gives its first entry's item) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Farm11") TMap<FName, FString> FarmLoot;
	/** a farmstead of a design: its buildings of the town's kit, pens, gardens and yard; its family (SpawnWildFarm with designs) */
	void SpawnWildFarm11(ARDWildChunk* C, const FRDWildPlace& P, int32 Design);
	/** a building of the town's kit in a farm's frame: floor over its highest ground, a plinth down to the lowest, walls, its
	 *  door on its hinge (F), roof and gables, its inside by its kind; its record in the chunk's Houses */
	void WildKitBuilding(ARDWildChunk* C, const FRDWildPlace& P, const FRDFarmPart& Pt, int32 PartIx, FRDWildFarmRec& Rec);
	/** a container of the dungeon's pieces in the wilds (a body, its lid or doors on their hinges) that F opens and loots once
	 *  (Key, kept in the game instance's WildKilled): a chunk door with bBox; a garden's harvest is one with no moving part */
	bool AddWildBox(ARDWildChunk* C, FName Piece, const FTransform& At, FName Kind, int64 Key, const FString& Loot, FRDWildFarmRec* Rec = nullptr, const FVector* FrontAt = nullptr);
	/** F at a wild container: its loot to her, the game remembering it */
	void OpenWildBox(ARDWildChunk* C, int32 Index);
	/** a rectangle of a chunk kept clear of plants (a building's inside, a garden) */
	void WildClearRect(ARDWildChunk* C, const FVector& Mid, float Yaw, const FVector2D& Half, FRDWildFarmRec* Rec = nullptr);
	/** tests (888 farms11): a farm of a design built at a point (m) of a loaded chunk, as a farmstead is; its id (0: none) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Farm11") int32 SpawnFarmDesignAt(int32 Design, float Xm, float Ym, float Yaw);
	/** tests: a farm built by SpawnFarmDesignAt taken away again (its components, doors, houses, animals and folk) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Farm11") bool RemoveWildFarm(int32 Id);
	/** the wild containers of the near chunks: "box|<kind>|<x>|<y>|<z>|<alpha>|<looted 0/1>|<key>"; the farms' buildings:
	 *  "fbld|<farm id>|<kind>|<x>|<y>|<z floor>|<nx>|<ny>|<yaw>|<door x>|<door y>|<furniture>|<boxes>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Farm11") TArray<FString> GetWildBoxLines() const;
	/** tests: containers looted in the wilds, their things (counted as they are given) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Farm11") int32 WildBoxesOpened = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Farm11") int32 WildBoxThings = 0;
	/** the farm buildings' lines (GetWildBoxLines' "fbld"), kept as they are built */
	TArray<FString> WildFarmBldLines;
	/** the farm folk within reach of a point (cm), nearest first (null: none) */
	ARDTownsfolk* NearestWildFolk(const FVector& From, float Reach = 240.f, bool bAwake = false) const;
	/** the list of 2026-11-16's seventh phase: a farm's sleeper within F's reach (named asleep when nothing else is there) */
	ARDTownsfolk* WildSleeperNear14(const FVector& From) const;
	/** the farm folk F talks to: within 2 m, unless a door or container of a loaded town is nearer (as the town's people) */
	ARDTownsfolk* WildFolkForF(const FVector& From) const;
	/** the farmsteads of the chunks made: "farm|<id>|<name>|<x m>|<y m>|<z cm>|<yaw>|<props>|<animals>|<folk>|<pen x cm>|<pen y
	 *  cm>|<pen half x>|<pen half y>|<pen yaw>", then each of its "animal|<id>|<kind>|<x>|<y>|<z cm>|<in the pen 0/1>|<state>|
	 *  <ground z cm>" and "folk|<id>|<title>|<x>|<y>|<z cm>|<clip>|<ground z cm>|<def name>" (tests) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") TArray<FString> GetWildFarmLines() const;          // ("folk|<farm>|<title>|x|y|z|<clip>|<ground z>|<def>|<asleep>|<in bed>|<indoors>|<has a bed>|<bed x>|<bed y>|<bed top>")
	/** the farms' layout at a point (metres): "<kind>|<great x>,<great y>|<plot x>,<plot y>|<crop>|<field>|<ang>|<strip w>|
	 *  <strip off>|<strip>|<furrow>|<ridge m>|<height m>|<the height with no farm m>" (kind: 0 none, 1 open field, 2 crofts, 3 pasture, 4 yard) (tests) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") FString GetWildFarmAt(float Xm, float Ym) const;
	/** the farmsteads whose middle is within R metres of a point (metres): "<id>|<name>|<x>|<y>|<yaw>" (tests: where to go) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") TArray<FString> FindWildFarmsteads(float Xm, float Ym, float Rm) const;
	ARDSection* EnsureWildSection();
	void SpawnWildMonsters(ARDWildChunk* C, const FRDWildPlace& P);
	// ---- the list of 2026-11-12's third phase: twenty kinds of ruins (RDWildRuin12.cpp, 924)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild12") TArray<FRDWildRuinKind> WildRuinKinds;
	/** the kind a place of kind "ruins" is (an index into WildRuinKinds, -1: none fits or no table): from its id, its biome and the
	 *  water round it; a pure function of the world */
	int32 WildRuinKindOf(const FRDWildPlace& P) const;
	/** where its parts are laid from (the place's point, or moved into the water for a kind that wants it) and its shore */
	FVector2D WildRuinCentre(const FRDWildPlace& P, FVector2D* Shore = nullptr) const;
	/** a place's kind, middle and shore, worked out once (the scan for water is the costly part) */
	struct FRuinPick { int32 Kind = -1; FVector2D Centre = FVector2D::ZeroVector; FVector2D Shore = FVector2D::ZeroVector; };
	mutable TMap<int32, FRuinPick> WildRuinPicks;
	const FRuinPick& WildRuinPickOf(const FRDWildPlace& P) const;
	void LayWildRuin(ARDWildChunk* C, const FRDWildPlace& P, const FRDWildRuinKind& K);
	/** a piece laid by its box: its bottom on the lowest ground under it (less Sink cm), scaled to H metres high or by S */
	UStaticMeshComponent* LayRuinPiece(ARDWildChunk* C, UStaticMesh* M, const FVector& At, const FRotator& Rot, const FVector& Scale, float Sink, bool bCollide);
	/** the ruins laid (tests, the message as she comes): id, kind, its centre, how many pieces and containers */
	struct FRuinLaid { int32 Id = 0; int32 Kind = -1; FVector2D At = FVector2D::ZeroVector; int32 Pieces = 0; int32 Boxes = 0; int32 Guards = 0; FString Name; float Yaw = 0.f; TArray<TWeakObjectPtr<UPrimitiveComponent>> Comps; TArray<float> Lifts; FVector2D Exit = FVector2D::ZeroVector; float OutR = 0.f;
		/** the list of 2026-11-14: its effects (fx= parts) and the hours each shows at ("" always, day, night, dusk) */
		TArray<TWeakObjectPtr<class UNiagaraComponent>> Fx; TArray<FString> FxHours; };
	/** a kind of a table (the ruins' kinds, the lairs' covers) for a place: by its biome and the kinds' weights, from a hash of its
	 *  id and Salt; the water kinds only when bWet */
	int32 PickWildKind(const TArray<FRDWildRuinKind>& T, const FRDWildPlace& P, uint32 Salt, bool bWet) const;
	/** the nearest of the world's places within MaxKm of a point that Match takes (it sets the point measured from) */
	bool FindNearestWildPlace(float X, float Y, float MaxKm, TFunctionRef<bool(const FRDWildPlace&, FVector2D&)> Match, FRDWildPlace& Out, FVector2D& OutAt) const;
	/** a capsule at L (its middle) overlaps one of a laid ruin's colliding pieces */
	bool WildRuinInPiece(const FRuinLaid& X, const FVector& L, float Radius, float HalfHeight) const;
	/** a kind's parts laid round O in the frame of Yaw (the layout language of RDWildRuin12.cpp), its containers kept looted under
	 *  KeyBase + id x 8 + n, into Rec (the ruins' and the lairs' covers) */
	void LayWildParts(ARDWildChunk* C, const FRDWildPlace& P, const FRDWildRuinKind& K, const FVector2D& O, const FVector2D& Shore, float Yaw, FRandomStream& R, int64 KeyBase, FRuinLaid& Rec);
	/** an earth bank laid as the ground is drawn (the ground's material and vertex data from the world): a ring of middle radius
	 *  Rm and width Wm (metres), Hm high, open over GapDeg about the way GapYaw (world degrees), its ends sloping down */
	class UProceduralMeshComponent* LayWildBerm(ARDWildChunk* C, const FVector2D& O, float Rm, float Wm, float Hm, float GapYaw, float GapDeg);
	/** the list of 2026-11-14: a rise of the land laid as the ground is drawn (as the berm): "mound" a dome of radius Rm, "cone" a cone
	 *  with a crater of Crater's share of it at the top, "ridge" a long bank Rm wide each side and R2m long each way along Yaw; Hm high */
	/** (phase 2: Tint's alpha over 0 colours the ground under it that colour, bare of sand, mud, rock and snow: a salt pan's crust) */
	/** (the fourth phase: Poly, an outline in the landform's frame (-1 to 1 of its reach), keeps only the quads inside it: a chalk figure
	 *  cut into a slope) */
	/** (the sixth phase: "mesa" a butte (a flat top, sheer sides, a talus apron); Bands its colour in layers by height, the foot's first;
	 *  the seventh: Lava its glow, 0-1, the ground material's lava) */
	class UProceduralMeshComponent* LayWildLandform(ARDWildChunk* C, const FVector2D& O, const FString& Type, float Rm, float R2m, float Hm, float Yaw, float Crater, FLinearColor Tint = FLinearColor::Transparent, const TArray<FVector2D>* Poly = nullptr, const TArray<FLinearColor>* Bands = nullptr, float Lava = 0.f);
	/** the rises a kind's parts have laid so far (LayWildParts clears them as it begins; LayWildScenery after its uses and hazards), and
	 *  the ground with them: what is laid after a mound stands on it */
	struct FWildLand { FVector2D At = FVector2D::ZeroVector; FString Type; float R = 1.f, R2 = 1.f, H = 0.f, Yaw = 0.f, Crater = 0.f; };
	TArray<FWildLand> WildPartsLand;
	float WildPartsGroundZ(const FVector& L) const;
	// ---- the list of 2026-11-12's fifth phase: the structures of the wilds (RDWildSite12.cpp, 924 sites) and their quests
	/** the structures' kinds (924 sites, from SourceArt/wilderness/sites12.json): the world's SitesIn places them, a chunk lays
	 *  them (LayWildSite) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild12") TArray<FRDWildSiteKind> WildSiteKinds;
	/** the share of the 2.5 km grid's cells that hold one */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild12") float WildSiteFill = 0.5f;
	FIntPoint WildSiteCell = FIntPoint(MIN_int32, MIN_int32);
	TArray<FRDWildPlace> WildSiteNear;
	void LayWildSite(ARDWildChunk* C, const FRDWildPlace& P);
	/** what a laid structure holds beyond its pieces: its prisoners (townsfolk in cages), its traps (where, their keys) */
	struct FSiteTrap { FVector At = FVector::ZeroVector; int64 Key = 0; float ReadyAt = 0.f; int32 SiteId = 0; };
	TArray<FSiteTrap> WildSiteTraps;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Wild12") int32 WildTrapsSprung = 0;
	/** the living beast's back's creature (924 sites: the Animals pack's fantasy elephant with its howdah): its mesh, walk, scale, its
	 *  speed (cm/s) and the radius of its slow round (m) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild12") TObjectPtr<class USkeletalMesh> WildBeastMesh = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild12") TObjectPtr<class UAnimSequence> WildBeastWalk = nullptr;
	/** what it carries on its back (the pack's war platform, a mesh of its own on the beast's bones: it follows the body's pose) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild12") TObjectPtr<class USkeletalMesh> WildBeastBuild = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild12") float WildBeastScale = 2.6f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild12") float WildBeastSpeed = 110.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild12") float WildBeastRadius = 45.f;
	struct FWildBeast { TWeakObjectPtr<class USkeletalMeshComponent> Comp; FVector2D Centre = FVector2D::ZeroVector; float Angle = 0.f; int32 SiteId = 0; };
	TArray<FWildBeast> WildBeasts;
	/** tests: the beasts walking: "beast|<site>|<x>|<y>|<z>|<yaw>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild12") TArray<FString> GetWildBeastLines() const;
	TArray<TWeakObjectPtr<ARDTownsfolk>> WildSiteFolk;
	TArray<FRuinLaid> WildSitesLaid;
	void TickWildSites12(float Dt, const FVector& Her);
	// ---- the list of 2026-11-14 (docs/improvements13.txt): the biomes' scenery (RDWildScenery13.cpp, 926 from SourceArt/wilderness/
	// scenery13.json): the world places them (FRDWildWorld::SceneryIn), a chunk lays each (LayWildScenery) by the ruins' layout language
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") TArray<FRDWildSceneryKind> WildSceneryKinds;
	/** the share of the 600 m grid's cells that hold one */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") float WildSceneryFill = 0.6f;
	/** the dry channels' kinds (FRDWildWorld::ChannelRules: "biomes=..;n=..;len=..;w=..;d=..;wall=..;turn=..;name=..") */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") TArray<FString> WildChannelRules;
	/** the effects a part may lay ("fx=<name>": "f13_<name>") */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") TMap<FName, TObjectPtr<class UNiagaraSystem>> WildSceneryFx;
	/** the far sights ("distant storm cells or tornadoes visible for miles", "smoke from grass fires on the horizon"): one at a time */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") TArray<FRDWildFarSight> WildFarSights;
	/** materials a part may lay its piece in ("mat=<name>": "m13_<name>", the burned plain's charred timber) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") TMap<FName, TObjectPtr<class UMaterialInterface>> WildSceneryMats;
	/** the third phase ("a soft floor of needles that muffles footsteps, good for stealth"): the biomes whose floor is quiet, and how far
	 *  the wilds' monsters notice her there against elsewhere; WildQuietScale is that factor where she stands now (1 elsewhere) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") TArray<FString> WildQuietBiomes;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") float WildQuietNotice = 0.65f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Wild13") float WildQuietScale = 1.f;
	float WildQuietAt = -1.f;
	/** the fifth phase ("thin air that drains stamina and makes the player dizzy"): the biomes high enough, and her slow there */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") TArray<FString> WildThinAirBiomes;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") float WildThinAirSlow = 0.15f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Wild13") bool bWildThinAir = false;
	/** a hazard's burst of a looping effect (a rockfall's dust): put out at Off, taken away at Kill (game seconds) */
	struct FSceneryBurst { TWeakObjectPtr<class UNiagaraComponent> Comp; float Off = 0.f, Kill = 0.f; };
	TArray<FSceneryBurst> WildSceneryBursts;
	/** the sixth phase: what calls back from a canyon's echo (its time, its line), and how many answered (tests) */
	TArray<TPair<float, FString>> WildSceneryEchoes;
	/** the eighth phase ("auroras over black lava and white snow"): at night in these regions a curtain of light hangs WildAuroraKm
	 *  north of her, WildAuroraUpM up (the kit's Aurora, emissive and see-through) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") TArray<FString> WildAuroraBiomes;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") TObjectPtr<class UStaticMesh> WildAuroraMesh = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") float WildAuroraKm = 4.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") float WildAuroraUpM = 1200.f;
	TWeakObjectPtr<class UStaticMeshComponent> WildAurora;
	float WildAuroraLook = 0.f, WildAuroraFootZ = 0.f;
	void TickWildAurora13(float Dt, const FVector& Her);
	void TickWildAuroraLook(const FVector& Her);
	/** the ninth phase ("the tide as a clock: paths open and close"): the sea's tide, 0 low to 1 high, on a cycle of WildTidePeriod
	 *  seconds; the skins of the land laid with tide=<m> rise and fall with it (tidal flats, salt-marsh creeks) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") float WildTidePeriod = 600.f;
	/** tests: a tide held at this level (0-1), or the clock's (under 0) */
	float WildTideForce = -1.f;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild13") void ForceWildTide(float Level) { WildTideForce = Level; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild13") float GetWildTide() const;
	struct FTideSkin { TWeakObjectPtr<class UPrimitiveComponent> Comp; float Amp = 0.f; FVector Base = FVector::ZeroVector; float LastZ = -1e9f; };
	TArray<FTideSkin> WildTideSkins;
	/** the tenth phase ("survival gameplay: cold, food and shelter give the player constant reasons to keep moving"): in these regions
	 *  she grows cold away from warmth (a fire within 8 m, a town, a shelter used); past WildColdSeconds of it the cold bites, a hurt
	 *  every 15 s, until she is warm again */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") TArray<FString> WildColdBiomes;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") float WildColdSeconds = 90.f;
	UPROPERTY(BlueprintReadWrite, Category = "RandomDungeon|Wild13") float WildCold = 0.f;
	float WildWarmUntil = -1.f, WildColdBiteAt = 0.f; bool bWildColdTold = false, bWildColdNow = false;
	/** tests: a shelter's warmth for this long, as a heal use gives */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild13") void WarmWildFor(float Seconds);
	/** tests: "<cold seconds>|<warm 0/1>|<why>" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild13") FString GetWildColdState() const;
	FString WildWarmWhy;
	/** the tenth phase ("footing: mud, rock and water change speed"): in these regions, where the ground is mud, she is slowed */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") TArray<FString> WildMudBiomes;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") float WildMudSlow = 0.15f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Wild13") bool bWildMud = false;
	/** the tenth phase ("sound and fog"): the regions whose fog comes three times as often (the moors' since the fourth phase) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") TArray<FString> WildFogBiomes;
	/** the tenth phase ("a landmark always in view"; PR #74's review: a passing far sight was no landmark): a broken tower at a fixed
	 *  place in each 6 km square of the open lands, on dry ground away from the roads and towns, solid; the nearest within WildLandmarkKm
	 *  is laid and kept while she stays within that reach */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") TArray<FString> WildLandmarkBiomes;
	/** the list of 2026-11-16 (927): the last 20 messages kept and shown (L, D-pad down); a potion or food on the quick bar
	 *  used by the attack button, food allowed on the bar */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") bool bMessageLog14 = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") bool bQuickUse14 = false;
	/** the list of 2026-11-16's third phase (927 horse): her horse called by a key (J, the D-pad up) from anywhere but a dungeon,
	 *  shown on the maps, the rider seated by the horse's measured seat with the reins, her weapons put away (RDList14b.cpp) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") bool bHorseCall14 = false;
	/** the list of 2026-11-16's fifth phase (927 tables, RDList14c.cpp): potions are made at the alchemist's table, scrolls at the
	 *  librarian's (the recipes' own Station when they have one, else by the item's kind: RecipeStation); the tables (AlchemistPiece,
	 *  LibrarianPiece) stand in the towns' healers, laboratories and witches' huts and their temples, libraries and studies, and by
	 *  the dungeons' anvils (the alchemist's; the librarian's too where bLibrarianInDungeon14: the maps with no town) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") bool bTables14 = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") bool bLibrarianInDungeon14 = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") FName AlchemistPiece = TEXT("Table14.Alchemist");
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") FName LibrarianPiece = TEXT("Table14.Librarian");
	/** where a recipe is made: its Station ("Oven", "Forge"), or with bTables14 "Alchemist" for a potion and "Librarian" for a
	 *  scroll; none: the anvil */
	FName RecipeStation(const FRDRecipe& Rc) const;
	/** the same with its item's index already found (FindItem; -1 none) */
	FName RecipeStationOf(const FRDRecipe& Rc, int32 ItemIx) const;
	bool FindNearestTable14(FName Station, const FVector& From, float MaxDistance, FVector& At) const;
	/** "Alchemist" or "Librarian" when that table is within MaxDistance and nearer than Than (cm), else none */
	FName NearestTable14(const FVector& From, float MaxDistance, float Than) const;
	/** the distance to the nearest of the anvil (AnvilD), a forge that would take F and a dungeon's oven, within Lim */
	float StationsNearest(const FVector& From, float Lim, float AnvilD, bool bAnvil) const;
	/** tests: every table of the kind ("Alchemist", "Librarian") in the sections built */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List14") TArray<FVector> GetAllTables14(FName Station) const;
	/** tests: the recipes the station offers her now ("Alchemist", "Librarian", "Oven", "Forge", none the anvil), refused ones left out */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List14") TArray<FName> GetStationRecipes14(FName Station) const;
	/** the list of 2026-11-16's sixth phase (928, RDList14e.cpp): recipes found. A recipe that a recipe item teaches is refused until
	 *  she has read one (KnownRecipes, kept for the game); recipes are found in the dungeons' chests and shelves by tier, in the wilds'
	 *  ruins' and structures' chests ("@recipe" in their loot: one of the box's tier), and sold by the traders */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") bool bRecipes14 = false;
	/** the chance a dungeon's container and a library's shelf hold a recipe besides (of its tier or below; a stream of its own) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") float RecipeLootChance14 = 0.04f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") float RecipeShelfChance14 = 0.12f;
	/** where a station's things are made, in words ("an oven", "an alchemist's table", ..., "an anvil") */
	static FString StationPlace14(const FName& Station);
	/** tests: a wild container's loot line by its key (empty if none is laid) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List14") FString GetWildBoxLoot14(int64 Key) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List14") bool IsLockedRecipe14(FName Item) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List14") bool KnowsRecipe14(FName Item) const;
	bool LearnRecipe14(FName Item);
	/** tests: the recipes learned, and forgetting them (the game instance's list emptied) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List14") TArray<FName> GetKnownRecipes14() const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List14") void ForgetRecipes14();
	/** the recipe item that teaches Item (none if none does) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List14") FName RecipeItemFor14(FName Item) const;
	/** a wild container's loot lines with "@recipe|min|max|chance" made a recipe of the land's tier where it stands, drawn from a stream
	 *  of its own by its key (its other things keep their draws); and the same for a test ("<line>;<line>" given and returned) */
	void ResolveWildLoot14(TArray<FString>& Lines, const FVector& At, int64 Key) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List14") FString GetWildLootResolved14(const FString& Loot, FVector At, int64 Key) const;
	/** a recipe item of the game's tier or below (its lowest tier), drawn with R (none if none) */
	FName RecipeOfTier14(int32 GameTier, FRandomStream& R) const;
	/** the items the recipe items teach, made once for the table's size */
	mutable TSet<FName> TaughtRecipes14; mutable int32 TaughtRecipesOf14 = -1;
	/** the fifth phase's second part (RDList14d.cpp): the tables of the wilds' places (a village one in two, a camp one in three, a
	 *  witch's hut, a shrine, the abbey's and temple's ruins) and the farmsteads' ovens, used by F as the towns' are */
	TArray<FName> WildTablesOf14(const struct FRDWildPlace& P) const;
	void LayWildTables14(class ARDWildChunk* C, const struct FRDWildPlace& P);
	bool WildFootLevel14(const FVector& Mid, float Yaw, float Hx, float Hy, float MaxStep, float& Zmin, float& Zmax) const;
	bool WildSpotFree14(const class ARDWildChunk* C, const FVector& Center, float Yaw, const FVector& Half) const;
	bool WildStationNear14(const FVector& From, FVector& At, FName& Kind) const;
	/** a wild station within reach and nearer than every other thing F reaches out there (a scenery's use, a point of interest, a
	 *  door or container, a person) */
	bool WildStationFirst14(const FVector& From, FName& Kind) const;
	/** a station's prompt, and its panel opened (the towns', dungeons' and wilds' alike) */
	static FString StationWords14(const FName& Kind);
	FString OpenStation14(const FName& Kind);
	/** tests: "<kind>|<x>|<y>|<z>|<yaw>|<owner>" for every station of the chunks made */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List14") TArray<FString> GetWildStations14() const;
	/** tests: "<id>|<kind>|<name>|<x m>|<y m>|<tables>" for the places within RadiusM (metres) the rule gives tables */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List14") TArray<FString> GetWildTablePlaces14(FVector Near, float RadiusM) const;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List14") int32 HorseCalls14 = 0;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List14") bool CallHorseByKey();
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List14") bool GetHorseMapAt(FVector& At) const;
	/** "<pelvis from the seat along, across, up (cm)>|<left hand from its grip>|<right hand>|<hands empty 1/0>", or "not riding" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List14") FString GetRiderLine() const;
	FTransform HorseSeatFrame() const;
	FVector HorseSeatPoint() const;
	FVector HorseReinPoint(int32 Side) const;
	FVector HorseBitPoint(int32 Side) const;
	void TickReins14();
	TWeakObjectPtr<class UStaticMeshComponent> Reins14[2];
	/** the reins' mesh and material (927 horse: the engine's cylinder and its tintable shape material) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") TObjectPtr<class UStaticMesh> ReinsMesh = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|List14") TObjectPtr<class UMaterialInterface> ReinsMaterial = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") TObjectPtr<class UStaticMesh> WildLandmarkMesh = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild13") float WildLandmarkKm = 8.f;
	TWeakObjectPtr<class UStaticMeshComponent> WildLandmark;
	FVector2D WildLandmarkAt = FVector2D(1e12, 1e12);
	float WildLandmarkLook = 0.f;
	void TickWildLandmark13(float Dt, const FVector& Her);
	/** tests: "on|x|y|z" (cm) or "off" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild13") FString GetWildLandmark() const;
	/** tests: "on|x|y|z" (cm) or "off" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild13") FString GetWildAurora() const;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Wild13") int32 WildEchoesHeard = 0;
	/** the fourth phase: how deep she stands in a scenery's mist (0-1: the sky thickens the world's fog with it, as the port's), and each
	 *  kind's mist reach (its "L=mist;r=" part, read once; 0: none) */
	float WildMistWant = 0.f;
	TMap<int32, float> WildSceneryMistR;
	void LayWildScenery(ARDWildChunk* C, const FRDWildPlace& P);
	void TickWildScenery13(float Dt, const FVector& Her);
	/** a laid scenery's things: what F does (its uses), what hurts (its hazards), the effects its hours show, its herd */
	struct FSceneryUse { int32 Id = 0; int32 Kind = -1; int32 Use = 0; FVector At = FVector::ZeroVector; float Reach = 250.f; float Reuse = 0.f; TWeakObjectPtr<ARDWildChunk> Chunk; };
	struct FSceneryHazard
	{
		int32 Id = 0; FName Kind; FVector At = FVector::ZeroVector; float R = 500.f; float P = 1.f; float ReadyAt = 0.f; int32 Sprung = 0; float In = 0.f; TWeakObjectPtr<ARDWildChunk> Chunk;
		// (the second phase: what it names (a monster's name part, a piece's mesh name part), the piece it moves (a snag that falls, a
		// scarecrow that wakes) and its fall's start; the beasts a waterhole's hunt is between)
		FString Who, Hide, Named, Msg; int32 Count = 1; TWeakObjectPtr<UPrimitiveComponent> Comp; FQuat Rot0 = FQuat::Identity; FVector Pivot = FVector::ZeroVector, Loc0 = FVector::ZeroVector; FVector2D FallDir = FVector2D(1, 0);
		float Start = -1.f, Length = 0.f; TArray<TWeakObjectPtr<ARDWildAnimal>> Hunters; TWeakObjectPtr<ARDWildAnimal> Prey; int32 Kills = 0;
		/** (PR #66's review) every laid piece Hide names: a fall takes the one nearest her as it springs */
		TArray<TWeakObjectPtr<UPrimitiveComponent>> Cands;
		/** (the seventh phase) a geyser's cycle, seconds (PR #71's review: kept in Length, a hidden piece's height overwrote it) */
		float Every = 0.f;
		/** (the ninth phase) when she was last in it: an entry is one after 2 s out (the tide, the surge) */
		float LastIn = 0.f;
	};
	struct FSceneryFx { TWeakObjectPtr<class UNiagaraComponent> Comp; FString Hours; };
	struct FSceneryHerd { int32 Id = 0; TArray<TWeakObjectPtr<ARDWildAnimal>> Animals; FVector2D Home = FVector2D::ZeroVector; FVector2D Way = FVector2D(1, 0); float Phase = 0.f, Pen = 0.f; bool bMigrate = false, bStampede = false; float StampedeUntil = -1.f, NextHit = 0.f; int32 Stampedes = 0, Hits = 0; };
	TArray<FSceneryUse> WildSceneryUses;
	TArray<FSceneryHazard> WildSceneryHazards;
	TArray<FSceneryFx> WildSceneryFxOn;
	TArray<FSceneryHerd> WildSceneryHerds;
	TArray<FRuinLaid> WildSceneryLaid;
	TSet<int32> WildSceneryTold, WildScenerySprung;
	TMap<int32, float> WildSceneryReadyAt;
	float WildSceneryLook = 0.f;
	/** F at a scenery's use within reach: what it says ("" none) */
	FString WildSceneryDescribe(const FVector& From) const;
	FString WildSceneryInteract(const FVector& From);
	const FSceneryUse* WildSceneryUseNear(const FVector& From) const;
	/** a scenery's use within reach is nearer than any point of interest F could use (then it takes F) */
	bool WildSceneryFirst(const FVector& From) const;
	/** when each was told (its line as she came): a stampede waits 3 s after it, or its line would hide the first (one HUD line) */
	TMap<int32, float> WildSceneryToldAt;
	/** (PR #66's review) set while a scenery's predator kills a herd beast: no kill of hers (not counted, not kept, nothing dropped) */
	bool bWildPredatorKill = false;
	bool IsWildSceneryUsed(const FSceneryUse& U) const;
	/** monsters of a scenery's own (a hazard's, a use's): N of the kinds whose name has one of Who's parts in it ("Rat+Pangolin", case
	 *  kept: "Rat" is not "Pirate"; else the tier's), round At (1 to 3.5 m for several; Ring cm out, facing it, when given), hunting her
	 *  for Hunt seconds, gone with the chunk */
	void SpawnSceneryMonsters(ARDWildChunk* C, const FString& Who, int32 N, const FString& Named, const FVector& At, uint32 Salt, float Ring = 0.f, float Hp = 1.f, float Hunt = 60.f);
	/** the far storm about (its middle, way, its parts) */
	TWeakObjectPtr<class UStaticMeshComponent> WildStormCloud; int32 WildFarSightOn = -1;
	FVector2D WildStormAt = FVector2D::ZeroVector, WildStormWay = FVector2D(1, 0); float WildStormLook = 0.f; float WildStormUntil = -1.f;
	/** tests: a far sight of its name brought Km off now (Km 0 sends whatever is about away) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild13") void ForceWildFarSight(FName Name, float Km);
	void TickWildStorm13(float Dt, const FVector& Her);
	/** tests: "scen|<id>|<kind>|<title>|<x>|<y>|<pieces>|<boxes>|<guards standing>|<uses>|<hazards>|<fx>|<fx on>|<herd>|<yaw>|<name>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild13") TArray<FString> GetWildSceneryLines() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild13") TArray<FString> GetWildSceneryPieceLines(int32 Id) const;
	/** tests: a laid scenery's uses ("use|<i>|<do>|<x>|<y>|<z>|<used>"), hazards ("haz|<kind>|<x>|<y>|<z>|<r cm>|<sprung>") and herd
	 *  ("herd|<animals>|<stampedes>|<hits>" then "ani|<x>|<y>|<state>") */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild13") TArray<FString> GetWildSceneryThingLines(int32 Id) const;
	/** tests: the nearest scenery of a kind within MaxKm: "id|x|y|yaw|name" or "" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild13") FString FindWildScenery(FName Kind, float X, float Y, float MaxKm) const;
	/** tests: every kind's count within MaxKm: "<kind>|<count>" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild13") TArray<FString> CountWildScenery(float X, float Y, float MaxKm) const;
	/** tests: the dry channels of a kind near a point: "chan|<index>|<kind name>|<x>|<y> of its middle point|<width>|<depth>|<points>"
	 *  (the nearest MaxN within MaxKm), and the ground across one: "<offset m>|<height m>" every metre at its point I */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild13") TArray<FString> FindWildChannels(FString Kind, float X, float Y, float MaxKm, int32 MaxN) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild13") TArray<FString> GetWildChannelProfile(int32 Index, int32 Point, float HalfM) const;
	/** tests: the crossroads within MaxKm: "<x>|<y>" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild13") TArray<FString> FindWildCrossroads(float X, float Y, float MaxKm) const;
	/** tests: a storm brought now (Km off, its way) or sent away (Km 0); the far sight about: "<name>|<x>|<y>|<km from her>|<on>" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild13") void ForceWildStorm(float Km);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild13") FString GetWildStormLine() const;
	/** tests: a herd of a laid scenery set off (its stampede), as her coming does */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild13") bool StartWildStampede(int32 Id);
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Wild13") int32 WildSceneryUsed = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Wild13") int32 WildHazardsSprung = 0;
	/** F on a structure's person (a prisoner freed, a quest's giver): what it did ("" when nothing) */
	FString WildSiteTalk(ARDTownsfolk* T);
	/** tests: "site|<id>|<kind>|<title>|<x>|<y>|<pieces>|<boxes>|<guards standing>|<inside a piece>|<prisoners>|<freed>|<traps>|<name>|<yaw>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild12") TArray<FString> GetWildSiteLines() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild12") TArray<FString> GetWildSitePieceLines(int32 Id) const;
	/** tests: the nearest structure of a kind (or, Quest set, one that holds that quest) within MaxKm: "id|x|y|yaw|name" or "" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild12") FString FindWildSite(FName Kind, FName Quest, float X, float Y, float MaxKm) const;
	/** tests: every kind's count among the structures within MaxKm: "<kind>|<count>" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild12") TArray<FString> CountWildSites(float X, float Y, float MaxKm) const;
	/** tests: a structure's prisoners and traps: "prisoner|<x>|<y>|<freed>" and "trap|<x>|<y>|<ready>" lines */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild12") TArray<FString> GetWildSiteThingLines(int32 Id) const;
	/** the quest a structure holds (one of its kind's Quests, from its id), none when it has none */
	FName WildSiteQuestOf(const FRDWildPlace& P) const;
	// (the quests, RDWildQuest12.cpp: 924 quests from SourceArt/wilderness/quests12.json)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild12") TArray<FRDWildQuestDef> WildQuests;
	struct FQuestThing { FVector At = FVector::ZeroVector; TWeakObjectPtr<UStaticMeshComponent> Mesh; FName Item; bool bTaken = false; };
	struct FQuestRun
	{
		int32 Site = 0; FRDWildPlace P; int32 Quest = -1; int32 Stage = 0, Progress = 0, Choice = 0; float StageAt = 0.f; bool bBegun = false;
		TArray<TWeakObjectPtr<ARDMonster>> Mons; TArray<TWeakObjectPtr<ARDTownsfolk>> Folk; TArray<FQuestThing> Things;
		TWeakObjectPtr<ARDTownsfolk> Kept; TWeakObjectPtr<AActor> Horse; FVector2D Point = FVector2D::ZeroVector;
		float Deadline = 0.f, NextWave = 0.f; int32 Waves = 0; bool bAmbushed = false, bStrandedAway = false; int32 GoldGiven = 0;
		// (PR #58's review: the stage's spec parsed once and its point found once while it waits (MStage, PtStage: the stage they
		// are for); the storm held by this run (let go when its actors are cleared); its last look's time (a pause counted whole))
		int32 MStage = -1; TMap<FString, FString> M; int32 PtStage = -1; FVector2D PtWait = FVector2D::ZeroVector;
		bool bHeldWeather = false; float LastLook = -1.f;
	};
	TMap<int32, FQuestRun> WildQuestRuns;
	/** the stranded's shore, she put there at the next quest tick (PR #58's review: WildPutHer lays chunks, and a structure's
	 *  chunk adds its run to WildQuestRuns: done while a run was held by reference it wrote into freed memory) */
	bool bWildStrandPending = false; FVector2D WildStrandTo = FVector2D::ZeroVector;
	/** the run's stage spec (parsed when its stage changes) */
	const TMap<FString, FString>& QuestStageSpec(FQuestRun& Run);
	/** a wild monster of a kind on open ground at a ground point (its capsule over it), set up and empowered on the wild
	 *  section: the quests', the director's and the tests' (PR #58's review: one helper) */
	ARDMonster* SpawnWildMonsterAt(const FRDMonsterDef& Def, const FVector& Ground, float Yaw, int32 Seed, int32 Tier, float Hp, const FString& Named);
	float WildQuestLook = 0.f;
	int32 WildQuestStage(int32 Site) const;
	void SetWildQuestStage(FQuestRun& Run, int32 Stage);
	const FRDWildQuestDef* QuestOfRun(const FQuestRun& Run) const;
	void ClearQuestStageActors(FQuestRun& Run);
	FVector2D QuestPoint(const FQuestRun& Run, const FString& Spec, int32 Salt) const;
	ARDTownsfolk* SpawnQuestFolk(FQuestRun& Run, FName QRole, const FString& Title, const FString& Def, const TArray<FString>& Lines, const FVector2D& At);
	void SpawnQuestThing(FQuestRun& Run, const FString& Prefix, const FVector2D& At, float HeightM, FName Item);
	void SpawnQuestMonsters(FQuestRun& Run, int32 N, const FString& KindSpec, const FString& Named, float Hp, const FVector2D& At, float Ring);
	void QuestSiteLaid(const FRDWildPlace& P);
	FString WildQuestTalk(ARDTownsfolk* T);
	/** F on a quest's thing within reach (a clue, a flower, the stones), a beaten-down beast bound, a wild horse calmed */
	FString WildQuestInteract(const FVector& From);
	void AdvanceWildQuest(FQuestRun& Run);
	void FinishWildQuest(FQuestRun& Run, bool bWon);
	void BeginWildQuestStage(FQuestRun& Run, const TMap<FString, FString>& M);
	void TickWildQuests12(float Dt, const FVector& Her);
	void TameWildHorse(FQuestRun& Run);
	void SetWeatherNamed(const FString& Name, bool bHold);
	/** tests: "wq|<site>|<quest>|<stage>|<do>|<progress>|<n>|<choice>|<point x>|<point y>|<monsters>|<alive>|<things left>|<gold given>|<hint>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild12") TArray<FString> GetWildQuestRunLines() const;
	/** tests: a quest's people: "<role>|<title>|<x>|<y>|<z>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild12") TArray<FString> GetWildQuestFolkLines(int32 Site) const;
	/** tests: a quest's things and monsters: "thing|x|y|z|taken", "monster|x|y|z|dead|hp|max", "horse|x|y|z|0" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild12") TArray<FString> GetWildQuestThingLines(int32 Site) const;
	// ---- the list of 2026-11-12's fourth phase: the lairs hidden behind something (RDWildLair12.cpp, 924 lairs)
	/** "monster lairs do not have any special structure around them. they should be hiding behind something, a stand of trees, a
	 *  ruin, a cave, an abandoned house, an earth berm": a lair's cover (a ruin kind's fields: its parts laid round the lair, its
	 *  biomes and weight; HideR the circle its monsters keep to, GapYaw its opening's way in its frame) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild12") TArray<FRDWildRuinKind> WildLairCovers;
	/** the cover a lair has (an index into WildLairCovers, -1: none), from its id and its biome */
	int32 WildLairCoverOf(const FRDWildPlace& P) const;
	mutable TMap<int32, int32> WildLairPicks;
	void LayWildLair(ARDWildChunk* C, const FRDWildPlace& P, const FRDWildRuinKind& K);
	/** a lair's den: its place, or where the land rises or falls more than 2.5 m within 8 m of it, the dry ground of the least
	 *  relief within 40 m */
	FVector2D WildLairMiddle(const FRDWildPlace& P) const;
	mutable TMap<int32, FVector2D> WildLairDens;
	/** the most the land rises or falls 8 m from a point, eight ways (metres) */
	float WildLairRelief(const FVector2D& A) const;
	TArray<FRuinLaid> WildLairsLaid;
	/** tests: "lair|<id>|<cover>|<x>|<y>|<pieces>|<exit x>|<exit y>|<name>|<yaw>|<reach m>" for each lair laid in the chunks made */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild12") TArray<FString> GetWildLairLines() const;
	/** tests: the nearest lair of a cover to a point (metres) within MaxKm: "id|x|y|yaw|name" or "" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild12") FString FindWildLair(FName Cover, float X, float Y, float MaxKm, float MaxReliefM = 1000.f) const;
	/** tests: every cover's count among the world's lairs within MaxKm of a point: "<cover>|<count>" (and "none|<count>") */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild12") TArray<FString> CountWildLairs(float X, float Y, float MaxKm) const;
	/** tests: how hidden a laid lair's monsters are: sight lines from an eye 1.7 m over the ground at Ways points DistM round its
	 *  middle to each living monster within its cover (its feet + 0.5, 1.1 and 1.7 m), traced against the cover's own pieces
	 *  (complex collision: leaves count): "<blocked>|<lines>|<monsters>|<blocked by something else>" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild12") FString WildLairSight(int32 Id, float DistM, int32 Ways) const;
	/** tests: a laid lair's pieces, as GetWildRuinPieceLines */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild12") TArray<FString> GetWildLairPieceLines(int32 Id) const;
	/** the piece lines of one laid record (ruin or lair) */
	TArray<FString> PieceLinesOf(const FRuinLaid* X) const;
	/** tests: a laid ruin's pieces: "<mesh>|<x>|<y>|<bottom z>|<top z>|<ground z under its middle>|<solid>|<lift>" (cm; solid 1 it
	 *  stops her, 0 its collision is on with nothing in it to stop her, - off; lift how far its part raised it, -1 laid otherwise) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild12") TArray<FString> GetWildRuinPieceLines(int32 Id) const;
	TArray<FRuinLaid> WildRuinsLaid;
	TSet<int32> WildRuinsTold;
	float WildRuinLook = 0.f;
	void TickWildRuins12(float Dt, const FVector& Her);
	/** tests: "ruin|<id>|<kind>|<title>|<x>|<y>|<pieces>|<boxes>|<guards>|<name>|<yaw>|<guards standing>|<inside a piece>" (its front
	 *  is its yaw's way) for each ruin laid in the chunks made */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild12") TArray<FString> GetWildRuinLines() const;
	/** tests: the nearest ruin of a kind to a point (metres), searched over the world's places within MaxKm: "id|x|y|yaw|name" or "" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild12") FString FindWildRuin(FName Kind, float X, float Y, float MaxKm) const;
	/** tests: every kind's count among the world's ruins within MaxKm of a point: "<kind>|<count>" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild12") TArray<FString> CountWildRuins(float X, float Y, float MaxKm) const;
	// ---- the seventh phase: the small points of interest and the encounter director (RDWildPoi.cpp; 912 from poi.json)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") TArray<FRDWildPoiKind> WildPoiKinds;
	/** the share of the 120 m grid's cells that hold one */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float WildPoiFill = 0.8f;
	/** the director: an encounter on her way once this long has gone by with nothing to do within WildEngageM (cm) of her */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float WildEncounterGap = 25.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float WildEngageM = 4500.f;
	struct FRDWildPoiLive { int32 Id = 0; int32 Kind = -1; FVector At = FVector::ZeroVector; TWeakObjectPtr<ARDWildChunk> Chunk; };
	TArray<FRDWildPoiLive> WildPoiLive;
	/** the list of 2026-11-10: the placed ambushes already sprung this play (their ids) */
	TSet<int32> WildAmbushSprung;
	TMap<int32, float> WildPoiReadyAt;
	TArray<TWeakObjectPtr<ARDMonster>> WildRoamers;
	TArray<FString> WildEngagements;
	float WildLastEngaged = -1.f, WildEncounterTick = 0.f, WildLastNearSaid = -100.f;
	FString WildLastNear;
	int32 WildPoisLaid = 0, WildPoisUsed = 0, WildEncountersMade = 0;
	bool IsWildPoiUsed(int32 Id) const;
	/** one of the wilds' pieces (by its prefix) laid in a chunk at a point (metres), turned, scaled, sunk; a landmark's drawn far */
	UStaticMeshComponent* LayWildPiece(ARDWildChunk* C, const FString& Prefix, const FVector2D& At, float Yaw, float Scale, float Sink, bool bCollide, bool bFar, FRandomStream& R);
	/** "Item|min|max|chance" lines rolled */
	TArray<FName> RollWildThings(const TArray<FString>& Things, FRandomStream& R) const;
	/** the monster kinds the wilds meet at a tier */
	void WildKindsForTier(int32 Tier, TArray<int32>& Kinds) const;
	/** the director's lost satchels (gone with her far off, as its roamers) */
	TArray<TWeakObjectPtr<ARDLootPile>> WildRoamPiles;
	/** the list of 2026-11-11's fifth phase (RD/RDWild11.cpp): what the director met her with besides monsters and piles: the people
	 *  on the way (they talk and give), the herds; gone once she is 250 m away, as the roamers */
	TArray<TWeakObjectPtr<ARDTownsfolk>> WildRoamFolk;
	TArray<TWeakObjectPtr<class ARDWildAnimal>> WildRoamHerd;
	int32 WildDirectorPlaces = 0;
	/** the director's new kinds: a point of interest laid ahead of her, a herd, a person on the way; what it made */
	int32 MakeWildEncounter11(const FRDWildPoiKind& K, const FVector2D& At, FRandomStream& Rs);
	/** one met on the way gives her their gift (and gold) the first time she speaks to them */
	bool GiveWildGift(ARDTownsfolk* T);
	/** a sum of gold at a place of the wilds, grown with its tier as a kill's (RDTierGold) */
	int32 WildGoldAt(int32 Base, const FVector& At) const;
	/** the fifth phase's tick in the wilds: the leaves blowing round her in the meadows and woods, the splash and wake as she
	 *  goes in water */
	void TickWild11(float Dt, const FVector& Her);
	/** the leaves blown round her (a Niagara system before the camera) where she is in one of WildLeavesBiomes, out of towns */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild11") TObjectPtr<UNiagaraSystem> WildLeavesFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild11") TArray<FString> WildLeavesBiomes;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild11") float WildLeavesAhead = 700.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild11") float WildLeavesScale = 1.f;
	UPROPERTY(Transient) TObjectPtr<class UNiagaraComponent> WildLeavesComp = nullptr;
	/** tests (888 meadows11's screening): the leaves' system changed now (the one blowing taken away, the new one made where she
	 *  is) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild11") void SetWildLeavesFx(UNiagaraSystem* Fx);
	FString WildLeavesBiome;
	float WildLeavesClock = 0.f;
	/** the list of 2026-11-11 (Graymourne: "the terrain should be shoreline, with the water extending out into an ocean. the player
	 *  should be able to fall into the water, but be able to walk out via ramps. the docks should not be surrounded by walls"):
	 *  the port on its coast with the sea lifted to its harbour's water round it (FRDWildWorld::bPortSea), no blockers along the
	 *  harbour's edges but ramps up out of it (Port.Ramp), no wall along the harbour */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild11") bool bPortWaterOpen = false;
	/** "when the player goes in the water, there should be displacement, a splash and a wake": a splash where she comes into water
	 *  (falling or running in), rings on its face round her while she stands in it, a wake behind her as she wades */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild11") TObjectPtr<UNiagaraSystem> WaterSplashFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild11") TObjectPtr<UNiagaraSystem> WaterRingFx = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild11") float WaterSplashScale = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild11") float WaterRingScale = 1.f;
	/** where the water's face is under her (cm): the wilds' water or the harbour's; false: none */
	bool WaterFaceAt(const FVector& At, float& Z) const;
	bool bInWater = false;
	float WaterWakeClock = 0.f, LastSplashTime = -100.f;
	// ---- swimming (the user's of 2026-11-12: "create swimming animations for all current playable classes that are found in
	// the choose a hero menu. create a splash sound for when a player falls into the water or is swimming. have water
	// displacement and a wake for when the player moves through the water"; RD/RDSwim.cpp, 921)
	/** each hero's swimming clips (921 clips), by hero name as RiderClips */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Swim") TMap<FName, FRDSwimClips> SwimClips;
	/** she swims once her feet are this far under the water's face (cm; the swim floor under deep water is 145 cm down) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Swim") float SwimDepth = FRDWildWorld::SwimDepthCm;
	/** her speed swimming, a share of her walk's */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Swim") float SwimSpeedMul = 0.55f;
	/** her pelvis this far under the water's face while she swims along (her back at the face), her head this far over it while
	 *  she treads (cm; the rest of her follows the clip) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Swim") float SwimPelvisMove = 6.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Swim") float SwimHeadIdle = 18.f;
	/** the swim loop from this speed (cm/s), the treading idle below it */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Swim") float SwimMoveFrom = 40.f;
	/** a stroke's sound every this many seconds of the swim loop, as she moves */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Swim") float SwimStrokeEvery = 0.67f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Swim") bool bSwimming = false;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Swim") bool IsSwimming() const { return bSwimming; }
	/** on the horse or swimming: no blow, block, roll, dash, chi, stealth or ability (one gate for them all: PR #53's review) */
	bool IsRidingOrSwimming() const { return bMounted || bSwimming; }
	/** tests: strokes sounded, swims begun */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Swim") int32 SwimStrokes = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Swim") int32 SwimsBegun = 0;
	/** tests: "swim|<on>|<clip>|<her head over the face cm>|<speed>|<max walk>|<strokes>|<begun>|<ripples>|<her pelvis over it>" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Swim") FString GetSwimLine() const;
	void TickSwim(float Dt, class ACharacter* C, bool bIn, float Fz);
	void EndSwim(class ACharacter* C);
	FName SwimClipNow;
	bool bSwimMoving = false;          // (swimming along, not treading: on from SwimMoveFrom, off under 60 % of it)
	TWeakObjectPtr<ACharacter> SwimPawn;
	UPROPERTY(Transient) TObjectPtr<UAnimMontage> SwimMontage = nullptr;
	FVector SwimMeshWas = FVector::ZeroVector;
	float SwimJumpWas = 0.f, SwimStrokeClock = 0.f, WadeClock = 0.f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Swim") int32 WadeSteps = 0;
	// ---- the water's displacement (the water's material reads the ripples from a parameter collection: 8 sources, each a place,
	// the time it began and its strength, rings spreading from each over the face's normal; her own a bulge where she is)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Swim") TObjectPtr<class UMaterialParameterCollection> WaterRipples = nullptr;
	int32 RippleNext = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Swim") int32 RipplesMade = 0;
	void AddWaterRipple(const FVector& At, float Strength);
	void TickWaterRipples(const FVector& Her, bool bIn, float Fz, float Speed);
	/** the rings on the water's face, our own (no pack's ripple showed on the harbour's water by day: 920 port's screening): a
	 *  flat ring (WaterRingMesh, a plane, in WaterRingMaterial: its Fade parameter) growing from a radius to another and fading
	 *  over its life; a big one where she comes in */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild11") TObjectPtr<UMaterialInterface> WaterRingMaterial = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild11") TObjectPtr<UStaticMesh> WaterRingMesh = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild11") FVector2D WaterRingRadius = FVector2D(35.f, 190.f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild11") float WaterRingLife = 1.6f;
	struct FWaterRing { TWeakObjectPtr<UStaticMeshComponent> C; TWeakObjectPtr<UMaterialInstanceDynamic> M; float Age = 0.f, Life = 1.f, From = 30.f, To = 200.f, Strength = 1.f; };
	TArray<FWaterRing> WaterRingsLive;
	void MakeWaterRing(const FVector& At, float From, float To, float Life, float Strength);
	void TickWaterRings(float Dt);
	/** tests: the rings on the water now */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild11") int32 GetWaterRingsLive() const { return WaterRingsLive.Num(); }
	/** the splashes and rings made, each ended after WaterFxLife s (a pack's ripple can loop for ever) */
	TArray<TPair<TWeakObjectPtr<UNiagaraComponent>, float>> WaterFxMade;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild11") float WaterFxLife = 2.5f;
	/** tests: splashes and wake rings made, the last splash's place */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Wild11") int32 WaterSplashes = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Wild11") int32 WaterRings = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Wild11") FVector LastSplashAt = FVector::ZeroVector;
	/** tests: whether she is in water now, and its face's height (cm; -1e9 none) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild11") float GetWaterFaceUnderHer() const;
	/** the loaded chunk a point (cm) is in (null: none) */
	class ARDWildChunk* WildChunkAtCm(const FVector2D& At) const;
	/** tests: "leaves|<on 0/1>|<biome>|<particles>|<x>|<y>|<z>"; "folk|<title>|<x>|<y>|<given 0/1>" for the director's people; "herd|<kind>|<n>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild11") TArray<FString> GetWild11Lines() const;
	void SpawnWildPoi(ARDWildChunk* C, const FRDWildPlace& P);
	const FRDWildPoiLive* WildPoiNear(const FVector& From, float Reach) const;
	FString WildPoiDescribe(const FVector& From) const;
	FString WildPoiInteract(const FVector& From);
	void TickWildEncounters(float Dt, const FVector& Her);
	/** what met her (tests): "<time>|near|<what>|", "<time>|met|<kind>|<x>|<y>", "<time>|used|<kind>|<what it said>", and last
	 *  "state|<laid>|<used>|<encounters asked>|<roamers>|<last engaged>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild") TArray<FString> GetWildEncounterLines() const;
	// ---- the eighth phase: the ridable horse (RDHorse.cpp; 913)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Horse") FRDHorseDef HorseDef;
	/** each hero's rider clips, by her name */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Horse") TMap<FName, FRDRiderClips> RiderClips;
	UPROPERTY(Transient, BlueprintReadOnly, Category = "RandomDungeon|Horse") TObjectPtr<class ARDHorse> Horse;
	UPROPERTY(Transient, BlueprintReadOnly, Category = "RandomDungeon|Horse") TObjectPtr<class ARDHorse> StableHorse;
	bool bMounted = false;
	FVector MountMeshWas = FVector::ZeroVector, BoomOffsetWas = FVector::ZeroVector;
	float BoomArmWas = 0.f;
	FName RiderClipNow;
	float JumpWas = 0.f, StableLookIn = 0.f;
	UPROPERTY(Transient) TObjectPtr<class UAnimMontage> RiderMontage;
	/** the rider clip playing (the list of 2026-11-12: two gaits share one) */
	UPROPERTY(Transient) TObjectPtr<class UAnimSequenceBase> RiderClipAsset;
	FVector HorseSpotBeside(const APawn* Her) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Horse") bool HasHorse() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Horse") bool IsMounted() const { return bMounted; }
	/** the stable's price now (HorseDef.Price x the tier's price) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Horse") int32 HorsePriceNow() const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Horse") bool BuyHorse();
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Horse") bool CallHorse();
	/** the list of 2026-11-12: with a bought horse and a tamed one, the other one saddled (at the stable; not while riding) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Horse") bool SwapHorse();
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Horse") bool MountHorse();
	/** bNow: off at once, no clip (a death, a test); else the pack's horse stops first and she climbs down beside it */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Horse") bool DismountHorse(bool bNow = false);
	/** tests: "<owned>|<spawned>|<mounted>|<x>|<y>|<z>|<its clip>|<its rate>|<her speed>|<saddle z>|<her pelvis z>|<her rider clip>|<the stable's horse>|<her pelvis from the saddle, flat (cm)>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Horse") FString GetHorseState() const;
	/** Coat: -1 by whose it is (the stable's grey, her bay), 0 the bay, 1 the grey (a tamed horse) */
	class ARDHorse* SpawnHorseAt(const FVector& At, float Yaw, bool bHers, int32 Coat = -1);
	void TickHorse(float Dt);
	// ---- the user's of 2026-11-18 (RDHorse15.cpp; 933): the Ultimate Horse Pack's horse (HorseDef.bPack): the ride with momentum
	// (speeding up, slowing, turning by the speed, backing, a sudden stop), getting on and off by the pack's clips, a jump and a
	// rear, the hooves heard by the ground and dust thrown up, swimming, a hit taken
	enum class ERide15 : uint8 { None, Mounting, Riding, Dismounting };
	struct FRide15
	{
		ERide15 Phase = ERide15::None;
		float T = 0.f, Len = 0.f;          // (the getting on's or off's clip: its time, its length)
		bool bLeft = true;                 // (from the horse's left)
		float Yaw = 0.f, Speed = 0.f;      // (the horse's heading (deg) and its speed along it (cm/s; under 0 backing))
		bool bBack = false, bAir = false, bSwim = false, bRear = false, bStop = false, bWantOff = false, bJumped = false;
		float ActT = 0.f;                  // (the rear's, the landing's, the hit's, the sudden stop's time left)
		float HitT = 0.f, IdleT = 0.f, SnortT = 8.f, Pitch = 0.f, Lift = 0.f, LastHealth = -1.f;
		FVector OffAt = FVector::ZeroVector; bool bOffPlaced = false;
		FName Gait;                        // (the gait clip the horse plays: "idle", "walk", "run", "back", "swim", "swimidle")
		FString Surface;
		// (the movement's own, given back when she gets down)
		float MaxAccelWas = 0.f, BrakeWas = 0.f, FrictionWas = 0.f, BrakeFrictionWas = 0.f; bool bSepBrakeWas = false, bOrientWas = false;
		FRotator MeshRotWas = FRotator::ZeroRotator;
		// (tests)
		int32 Jumps = 0, Rears = 0, Hits = 0, Stops = 0, Swims = 0, Falls = 0, Dust = 0, Mounts = 0, Dismounts = 0, Blocked = 0;
		TMap<FString, int32> FallsOn;
	};
	FRide15 Ride15;
	bool MountHorse15(class ACharacter* C);
	bool DismountHorse15(class ACharacter* C, bool bNow);
	void FinishDismount15(class ACharacter* C);
	void TickRide15(float Dt, class ACharacter* C);
	/** where the rider's mesh goes this frame: the horse's rider socket's move from its rest, RiderFrameUp over the horse's origin */
	FTransform RiderFrame15() const;
	void PlayRider15(class ACharacter* C, class UAnimSequenceBase* Clip, bool bLoop, float Rate, float Blend);
	/** the hooves' ground: "Grass", "Dirt" or "Hard" (a town's streets, the cobbles, rock) */
	FString HoofSurface15(const FVector& At) const;
	/** the attack's button in the saddle rears the horse (standing or walking; not in the air, the water or a getting on or off) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Horse") bool RearHorse();
	/** tests: "<phase>|<speed>|<yaw>|<gait>|<rate>|<loops a second>|<pitch>|<swim>|<air>|<rear>|<jumps>|<rears>|<hits>|<stops>|
	 *  <swims>|<hoof falls>|<dust>|<last ground>|<her pelvis off its seat (cm)>|<left hand off the left rein>|<right ...>|<backing>|
	 *  <mounts>|<dismounts>|<blocked>|<falls on grass>|<on dirt>|<on hard ground>|<the horse's lift>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Horse") FString GetRideLine15() const;
	// ---- the horse's reel (the user's of 2026-11-19, RDReel16.cpp): -RDReel16 in the game, StartReel16 in play (a rehearsal)
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Reel16") void StartReel16(const FString& Go, const FString& Done, bool bShots);
	/** "<on>|<scene>|<sub>|<its time>|<the timeline's last line>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Reel16") FString GetReel16State() const;
	void TickReel16(float RealDt);
	bool Reel16FindSpots();
	bool bReel16 = false, bReel16Read = false, bReel16Going = false, bReel16Shots = false, bReel16Lake = false;
	int32 Reel16Stage = -1, Reel16Sub = 0;
	float Reel16T = 0.f, Reel16Yaw = 0.f, Reel16SwimYaw = 0.f, Reel16Base = 0.f, Reel16Aggro = 0.f, Reel16Lose = 0.f, Reel16Dry = 0.f, Reel16Swam = 0.f;
	bool Reel16Back = false;
	FVector2D Reel16Plains = FVector2D::ZeroVector, Reel16Shore = FVector2D::ZeroVector, Reel16Water = FVector2D::ZeroVector;
	// ---- the captain's two wilderness quests (2026-11-07, RDWildQuest.cpp): "wild:wolves" (the Mill Road Den's pack killed,
	// every one: read from the kills kept, WildKilled), "wild:patrol" (the lost patrol's remains found at the old watchtower)
	/** how many monsters a quest's place has (its kills' keys are its id x 16 + 0..N-1) */
	int32 WildQuestMonsters(const FRDWildPlace& P) const { return P.Quest == TEXT("wolves") ? 4 : 3; }
	/** where the patrol's remains lie (metres): before the watchtower's doorway, toward the road */
	FVector2D WildQuestRemainsAt(const FRDWildPlace& P) const;
	/** a wild quest's state from the world: 1 done (the pack dead, the remains found), else 0 */
	int32 WildQuestProgress(const FString& Goal) const;
	void WildQuestOnKill(const class ARDMonster* M);
	void TickWildQuests(const FVector2D& AtM);
	/** a quest's place is on the map while its quest is taken and not turned in (named, not found: no travel there) */
	bool IsWildQuestShown(int32 PlaceId) const;
	/** "goal|place id|name|x m|y m|kind|monsters|killed|progress|remains x m|remains y m|yaw|on the map" per wild quest (tests) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") TArray<FString> GetWildQuestLines() const;
	bool IsInLoadedTown(const FVector& At) const;
	/** inside the loaded town's wall (its maps are the town's) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") bool IsInTownWalls(const FVector& At) const;
	void DropWildChunksNear(const FVector2D& AtM, double HalfM);
	void SaveTownState();
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") void UnloadWildTown();
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") void LoadWildTown(int32 Ti, bool bNow);
	void FinishWildTownLoad();
	/** "town index|name|loading|section|her distance m|build s|loaded|dropped|in its walls|origin x|origin y|home" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") FString GetWildTownState() const;
	/** the map shown is the wilderness's (she is outside a town's walls) */
	bool IsWildMapShown() const { return bWild && !bInTownWalls; }
	// ---- the wilderness's map (RDWildMap.cpp, RDWildHUD.cpp)
	UPROPERTY(Transient) TMap<FIntVector, TObjectPtr<UTexture2D>> WildMapTex;
	TMap<FIntVector, double> WildMapUsed;
	TSet<FIntVector> WildMapPending;
	TMap<FIntVector, TArray<FColor>> WildMapCpu;
	TSharedPtr<struct FRDWMapStream, ESPMode::ThreadSafe> WildMapStream;
	UPROPERTY(Transient) TObjectPtr<UTexture2D> WildFogTex;
	UPROPERTY(Transient) TObjectPtr<UTexture2D> WildMiniTex;
	/** the map's view: its middle (world metres) and metres a screen pixel */
	FVector2D WildMapCenter = FVector2D::ZeroVector;
	double WildMapMpp = 25.0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float WildMapOpenMpp = 5.f;
	double WildMapMinMpp = 0.9, WildMapMaxMpp = 380.0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") int32 WildMapMaxTiles = 360;
	int32 WildMapMaxLevel = 9, WildMapMaxInFlight = 16, WildMiniLevel = 8;          // (the list of 2026-11-16: 10 and 9 at 300 km; a tile's span is the frame's over 2^level, so one lower keeps their detail at 150 km)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float WildMiniRadiusM = 280.f;
	FVector4 WildFogFor = FVector4(0, 0, 0, 0);
	int32 WildFogVersion = -1;
	double WildFogMpp = 0.0;
	/** how often the fog picture was made (the test: not once a frame while the map is dragged) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Wild") int32 WildFogBuilds = 0;
	double WildMiniTime = 0.0;
	FVector2D WildMiniFor = FVector2D::ZeroVector;
	/** the found place under the map's middle (its id, -1 none) */
	int32 WildMapHover = -1;
	FString WildMapHoverName, WildTravelRefusal, WildLastTravel;
	bool bWildDrag = false;
	FVector2D WildDragFrom = FVector2D::ZeroVector;
	int32 WildMapTilesMade = 0, WildTravels = 0;
	float WildMapWarmTimer = 0.f;
	bool bWildMadeLogged = false;
	/** the den's pack fell back to the place's own kind: said once a play (RDWildPlaces.cpp) */
	bool bWildWolvesWarned = false;
	double WildMapTileMs = 0.0;
	/** cells revealed in each 1.6 km block (the map's fog at its coarse zooms) */
	TMap<FIntPoint, int32> WildRevealCount;
	int32 WildMapLevelFor(double Mpp) const;
	double WildMapTileSpan(int32 L) const;
	UTexture2D* WildMapTile(int32 L, int32 I, int32 J, bool bAsk);
	void TickWildMap(float Dt);
	float WildRevealedShare(double Xm, double Ym, double Radius) const;
	/** the fog over the map: a picture over twice the view, and the part of it the view shows (UV0 to UV1) */
	UTexture2D* WildFog(const FVector2D& Mid, double Mpp, const FVector2D& SizePx, FVector2D& OutUV0, FVector2D& OutUV1);
	UTexture2D* WildMini(const FVector2D& At);
	void WildKnownPlaces(TArray<FRDWildPlace>& Out) const;
	/** a monster is after her near (fast travel is refused) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") bool IsWildCombat() const;
	void OpenWildMap();
	void TickWildMapInput(APlayerController* PC, float Dt);
	/** to a place she has found (its id), not while a monster is after her (the reason in WildTravelRefusal) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") bool WildFastTravel(int32 PlaceId);
	/** -RDTownGo=town:<name>: the wilderness town of that name (case and spaces ignored) found and travelled to as the map's
	 *  fast travel does (the reason in WildTravelRefusal) */
	bool WildTravelToTown(const FString& Key);
	/** "middle x|middle y|m a pixel|level|tiles|tiles asked|tile ms|hovered id|hovered name|tiles made|refusal|last travel" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") FString GetWildMapState() const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") void SetWildMapView(float Xm, float Ym, float Mpp);
	// ---- the list of 2026-11-12 (docs/improvements12.txt), its first phase (RD/RDList12.cpp): the mouse on the big map, a click
	// to teleport there (the console's rd.MapTeleport, once the map is revealed)
	/** the pointer is up over the big map: the town's and the wilds' always, any map while rd.MapTeleport is on */
	bool WantsMapPointer() const { return bMapOpen && bTacticalMaps && (bTown || (bMapClickTeleport && bMapRevealAll)); }
	/** the pointer leads the wilds' map's pick (it moved or clicked since the keys or the pad last moved the map): else the cross
	 *  does, as before (PR #54's review: the pad's A travelled to the place under a resting pointer) */
	bool bMapPointerLead = false;
	FVector2D MapPointerLast = FVector2D(-1.f, -1.f);
	/** rd.MapTeleport: a click on the big map teleports her there, once the map is revealed (rd.RevealMap) */
	UPROPERTY(BlueprintReadWrite, Category = "RandomDungeon|Map") bool bMapClickTeleport = false;
	/** the big map as last drawn (the HUD writes it): a world point W (cm) is on the screen at C + (W.Y - Vw.Y, Vw.X - W.X) x K; the
	 *  sheet the map is drawn on; 0 none drawn, 1 the wilds', 2 the town's, 3 a dungeon's */
	FVector2D MapXC = FVector2D::ZeroVector, MapXVw = FVector2D::ZeroVector;
	float MapXK = 0.f;
	FBox2D MapXSheet = FBox2D(ForceInit);
	int32 MapXKind = 0;
	/** the screen point over the big map as a world point (cm, its z 0); false off the sheet or with no map drawn */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Map") bool MapScreenToWorld(FVector2D Screen, FVector& Out) const;
	/** a click on the big map at this screen point, as the mouse makes it: with rd.MapTeleport on, there (once revealed); on the
	 *  wilds' map, to the found place under it; the outcome in LastMapClick; true when it moved her */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Map") bool ClickMapAt(FVector2D Screen);
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Map") FString LastMapClick;
	/** tests: "kind|C.x|C.y|Vw.x|Vw.y|K|sheet min x|min y|max x|max y" of the big map as last drawn; the Escape menu's line boxes as
	 *  "min x|min y|max x|max y" (the cards on a grid page) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Map") FString GetMapFrame() const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Menu") TArray<FString> GetMenuBoxes() const;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Map") int32 MapTeleports = 0;
	/** tests: clicks the big map took (a press the real mouse dragged away is none: the test tries again) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Map") int32 MapClicks = 0;
	/** the pointer over the wilds' map: the found place under it (the HUD's pick) */
	FVector2D MapPressAt = FVector2D::ZeroVector;
	bool bMapPress = false, bMapPointerUp = false;
	void TickMapPointer(APlayerController* PC);
	bool MapTeleportTo(const FVector& World);
	/** the wilds: the nearest dry ground she can stand on within MaxM of Wm (metres; Wm moved there), false if none */
	bool WildStandableNear(FVector2D& Wm, double MaxM) const;
	/** the wilds: put her down on dry ground within 200 m of Wm (metres), a town far behind her let go; never a town's travel */
	bool WildPutDownNear(FVector2D Wm);
	// ---- the list of 2026-11-22's seventh phase (RDList16e.cpp): the towns' interiors batched by building and hidden unless seen
	static bool InteriorBatch16();
	void TickTownInteriors16(float Dt);
	/** tests: "<hide on>|<batch on>|<buildings>|<shown>|<hidden>|<people hidden>|<windows>|<interior batches>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List16") FString GetInteriors16() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List16") TArray<FString> GetInteriorLines16() const;
	struct FTownInterior16
	{
		bool bNever = false, bShown = true, bSet = false;
		uint8 Why = 1; int32 WhyWin = -1;
		FVector2D A = FVector2D::ZeroVector, B = FVector2D::ZeroVector;
		TArray<TWeakObjectPtr<class UInstancedStaticMeshComponent>> Ism;
		struct FProp { TWeakObjectPtr<class USceneComponent> C; bool bHidden0 = false; };
		TArray<FProp> Props;
		TArray<TWeakObjectPtr<class USceneComponent>> Hearths;
		TArray<int32> Doors, Windows;
	};
	TArray<FTownInterior16> TownInt16;
	TWeakObjectPtr<class ARDSection> TownInteriorsFor16;
	float TownInteriorTimer16 = 0.f;
	int32 TownIntShown16 = 0, TownIntHidden16 = 0, TownIntPeopleHidden16 = 0;
	// ---- the list of 2026-11-22's sixth phase (RDList16d.cpp): the towns' lights, people and Heaven's dome by distance
	void TickTownLod16(float Dt);
	static FName StreetLampTag16();
	/** tests: "<on>|<lights>|<built to shadow>|<shadowing now>|<street lamps>|<people and animals: full|half|quarter|eighth|not drawn>|<dome drawn, -1 none>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List16") FString GetTownLod16() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List16") TArray<FString> GetTownLodLines16() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List16") TArray<FString> GetTownLightLines16() const;
	/** one actor hidden by the distance rule or an interior's (by the reason's tag), shown again only if these rules hid it */
	static void SetHidden16(AActor* A, FName Why, bool bHide);
	struct FTownLight16 { TWeakObjectPtr<class UPointLightComponent> L; bool bShadows = false, bLamp = false; float Draw0 = 0.f, Fade0 = 0.f; };
	TArray<FTownLight16> TownLights16;
	TWeakObjectPtr<class ARDSection> TownLodFor16;
	TWeakObjectPtr<class UStaticMeshComponent> TownDome16;
	float TownLodTimer16 = 0.f;
	int32 TownShadowing16 = 0;
	int32 TownBands16[5] = { 0, 0, 0, 0, 0 };
	bool bTownLodApplied16 = false;
	int32 TownLodLightsSeen16 = -1;
	// ---- the list of 2026-11-22's third phase (RDList16c.cpp): the wilds' ground in levels of detail, collision near her only
	bool IsWildLod16() const;
	double WildChunkNearM16(const FIntPoint& C, const FVector2D& At) const;
	int32 WildDrawEveryFor16(double NearM, int32 Cur) const;
	bool WildCollisionFor16(double NearM, bool bHas) const;
	void AskWildRegrid16(ARDWildChunk* C, int32 Every, bool bCollision, bool bNow);
	void ApplyWildRegrid16(struct FRDWChunkData& D);
	void MakeWildCollision16(ARDWildChunk* C, const TArray<FVector>& V, const TArray<int32>& T, bool bSync);
	void TickWildLod16(const FVector2D& At);
	/** tests: "<ground-only jobs>|<in flight>|<longest swap ms>|<on>|<chunks drawn at 2 m>|<at 4 m>|<at 8 m>|<with collision>|<triangles>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List16") FString GetWildLod16() const;
	/** tests: the seams between chunks of two steps measured on their meshes; the trees' and rocks' feet on coarse chunks; every mover of
	 *  the wilds on a chunk with collision (RDList16c.cpp) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List16") FString GetWildSeams16() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List16") FString GetWildFootGaps16() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List16") FString GetWildMoversOffGround16() const;
	double WildLod1M16 = 250.0, WildLod2M16 = 500.0;
	int32 WildRegridMax16 = 4, WildRegridInFlight16 = 0, WildRegrids16 = 0;
	double WildRegridMsMax16 = 0.0;
	TArray<TSharedPtr<struct FRDWChunkData, ESPMode::ThreadSafe>> WildRegridDone16;
	void WildAutosave(const FString& Why);
	// ---- the game saved to disk (RDSave.cpp)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") bool bAutosave = true;
	float LastSaveTime = -1000.f;
	double LastSaveRealTime = 0.0;
	mutable TMap<FString, TPair<double, FString>> SaveInfoCache;
	int32 LastSaveReveal = -1, SavesWritten = 0, LoadsArrived = 0;
	FString LastSaveSlot, LastSaveWhy;
	/** the game written to a slot ("autosave", "save", a named one "save_<name>"), the name she gave it */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") bool SaveGameNow(const FString& Slot, const FString& Why, const FString& Name = TEXT(""));
	/** the list of 2026-11-04 ("there is no way to name your own save"): the Escape menu's Save page, the name typed there; the
	 *  saves on disk, newest first ("<slot>|<name>|<date>|<place>|<hero>") */
	FString SaveNameText;
	/** Backspace held on the Save page: when it takes the next letter (real time; 0 when not held) */
	double SaveBackAt = 0.0;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") void SetSaveNameText(const FString& Text) { SaveNameText = Text.Left(40); }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild") FString GetSaveNameText() const { return SaveNameText; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Wild") TArray<FString> GetSaveSlots() const;
	/** a name's slot ("save_" and its letters and digits) */
	static FString SlotForName(const FString& Name);
	void TickSaveNameKeys(APlayerController* PC);
	mutable TArray<FString> SaveSlotsCache;
	mutable double SaveSlotsAt = -10.0;
	/** the game read from a slot and its level opened */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") bool LoadGameFrom(const FString& Slot);
	/** "<date>|<level>|<place>|<hero>|<why>" or "" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") FString GetSaveInfo(const FString& Slot) const;
	/** "<saves written>|<last slot>|<last why>|<loads arrived>" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") FString GetSaveState() const { return FString::Printf(TEXT("%d|%s|%s|%d"), SavesWritten, *LastSaveSlot, *LastSaveWhy, LoadsArrived); }
	void TickWildLoad();
	/** where she comes back to life in the wilderness: the square of the nearest town she has found (loaded now) */
	FVector WildRespawnAt();
	/** the packaged game out in the wilds (RDWildSelfTest.cpp, -RDWildTest=<file>): the town, out of the gate, a journey, a save
	 *  loaded, a long walk with its memory; each stage written to the file */
	struct FRDWildTest
	{
		bool bRead = false, bOn = false, bLoadPending = false, bFailed = false, bJourney = false, bWasDead = false;
		FString File;
		int32 Stage = 0, Sub = 0, Turns = 0, Deaths = 0;
		float WalkMinutes = 20.f, T0 = 0.f, LastMoveAt = 0.f, MemAt = 0.f;
		FVector SavedAt = FVector::ZeroVector, LastAt = FVector::ZeroVector, WalkFrom = FVector::ZeroVector, Heading = FVector(1, 0, 0);
		double Mem0 = 0.0, MemMax = 0.0, FramesAt = 0.0;
		int32 Frames = 0, Stuck = 0, Puts = 0, Pushes = 0;
		double PathCm = 0.0, Commit0 = 0.0, CommitMax = 0.0;
		/** the HUD's last lines and her hit points as they fell (a death's cause, written with it: the package of 2026-11-16 died once
		 *  and nothing said why) */
		TArray<FString> Said; float LastHp = -1.f; FString Hurts;
		/** the walk is a memory walk, not a fight (the package of 2026-11-16: the roaming ambushers killed her twice and the respawn
		 *  built a town into the walk's memory): from her put 3 km out to its end the monsters do not notice her (the generator's
		 *  AggroDistance and LoseDistance 0, as 888's quiet; put back after), and a death ends the walk as a failure with its cause */
		float AggroWas = -1.f, LoseWas = 0.f, LastMsgAt = -1000.f, HurtTotal = 0.f; double DamageSeen = -1.0;
		float NextCheckAt = 0.f, SubAt = 0.f;
		FVector LeverAt = FVector::ZeroVector, LeverPos = FVector::ZeroVector;
		FString GateWhat, GateOther;
		bool bCollected = false;
		FVector Gate = FVector::ZeroVector, GateOut = FVector(1, 0, 0);
	} WildTest;
	void TickWildSelfTest(APawn* P);
	void WildSelfTestLine(const FString& Line);
};
