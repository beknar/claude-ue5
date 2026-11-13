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
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List11") class ARDMonster* SpawnTestAmbusher(FVector At, int32 Tier = 1);
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
	 *  Kethrys Spire 20 (21-25), Heaven 24 capped at 25. The monsters' strength, the loot's tiers and the hero's growth go by it */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Tiers") int32 DungeonTierBase = 0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Tiers") int32 DungeonTierCap = 0;
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
	static constexpr int32 NumWeathers = 9;
	static constexpr int32 NumRotationWeathers = 8;
	static constexpr int32 WeatherCloudless = 8;
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
	/** the Old Watchtower climbed: its doorway open (hidden boxes round its ring, not its quarters' collision), a spiral stair up to
	 *  a floor at the second storey's top */
	void FitWildTower(ARDWildChunk* C, const FVector& Mid, float Z0, float Hs, float DoorYaw, float KeptYaw = -1e6f);
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
	bool TownQuestAction(FName Act, FName Id);
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
	bool HasTownSatellite() const { return TownSatellitePicture && TownSatCaptures > 0 && TownSatStep >= 3; }
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
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float WildRevealM = 300.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Wild") float WildDiscoverM = 90.f;
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
		/** each animal's pen's yaw (a barn's stall turns with its barn; AnimalPens' half sizes are along and across it) */
		TArray<float> AnimalPenYaws;
		/** its pieces as instances, one component a mesh, material and collision (PR #49's review: a component a piece was several
		 *  hundred in one frame) */
		TMap<FString, TWeakObjectPtr<class UInstancedStaticMeshComponent>> Batch;
	};
	/** one piece of a farm as an instance of its batch (world transform) */
	void WildFarmInstance(ARDWildChunk* C, FRDWildFarmRec& Rec, UStaticMesh* M, const FTransform& World, bool bCollide, UMaterialInterface* Mat, bool bUnseen = false);
	TArray<FRDWildFarmRec> WildFarms;
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
	ARDTownsfolk* NearestWildFolk(const FVector& From, float Reach = 240.f) const;
	/** the farm folk F talks to: within 2 m, unless a door or container of a loaded town is nearer (as the town's people) */
	ARDTownsfolk* WildFolkForF(const FVector& From) const;
	/** the farmsteads of the chunks made: "farm|<id>|<name>|<x m>|<y m>|<z cm>|<yaw>|<props>|<animals>|<folk>|<pen x cm>|<pen y
	 *  cm>|<pen half x>|<pen half y>|<pen yaw>", then each of its "animal|<id>|<kind>|<x>|<y>|<z cm>|<in the pen 0/1>|<state>|
	 *  <ground z cm>" and "folk|<id>|<title>|<x>|<y>|<z cm>|<clip>|<ground z cm>|<def name>" (tests) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") TArray<FString> GetWildFarmLines() const;
	/** the farms' layout at a point (metres): "<kind>|<great x>,<great y>|<plot x>,<plot y>|<crop>|<field>|<ang>|<strip w>|
	 *  <strip off>|<strip>|<furrow>|<ridge m>|<height m>|<the height with no farm m>" (kind: 0 none, 1 open field, 2 crofts, 3 pasture, 4 yard) (tests) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") FString GetWildFarmAt(float Xm, float Ym) const;
	/** the farmsteads whose middle is within R metres of a point (metres): "<id>|<name>|<x>|<y>|<yaw>" (tests: where to go) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Wild") TArray<FString> FindWildFarmsteads(float Xm, float Ym, float Rm) const;
	ARDSection* EnsureWildSection();
	void SpawnWildMonsters(ARDWildChunk* C, const FRDWildPlace& P);
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
	FVector HorseSpotBeside(const APawn* Her) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Horse") bool HasHorse() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Horse") bool IsMounted() const { return bMounted; }
	/** the stable's price now (HorseDef.Price x the tier's price) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Horse") int32 HorsePriceNow() const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Horse") bool BuyHorse();
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Horse") bool CallHorse();
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Horse") bool MountHorse();
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Horse") bool DismountHorse();
	/** tests: "<owned>|<spawned>|<mounted>|<x>|<y>|<z>|<its clip>|<its rate>|<her speed>|<saddle z>|<her pelvis z>|<her rider clip>|<the stable's horse>|<her pelvis from the saddle, flat (cm)>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Horse") FString GetHorseState() const;
	class ARDHorse* SpawnHorseAt(const FVector& At, float Yaw, bool bHers);
	void TickHorse(float Dt);
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
	int32 WildMapMaxLevel = 10, WildMapMaxInFlight = 16, WildMiniLevel = 9;
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
};
