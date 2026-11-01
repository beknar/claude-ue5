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
#include "RDDungeonGenerator.generated.h"

class ARDSection;
class ARDMonster;
class URDCombatComponent;
class URDBloodComponent;
class UStaticMesh;
class USoundAttenuation;
class UAudioComponent;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class UPostProcessComponent;
class UNiagaraSystem;

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
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Tiers") FName SealPiece = TEXT("CellFrame");
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Tiers") FName EndPiece = TEXT("Wall_Corr");
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Tiers") int32 TierOf(FIntPoint Section) const { return FMath::Max(FMath::Abs(Section.X), FMath::Abs(Section.Y)) + 1; }
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
	/** a hero of BlockHeroes holds the right mouse button or LT to block with the shield in her hand: BlockShare more of a blow
	 *  taken, BlockSlow of her speed lost, the shield worn BlockWear times as fast */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") bool bShieldBlock = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") TArray<FName> BlockHeroes;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") float BlockShare = 0.3f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Mistward2") float BlockSlow = 0.5f;
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
	/** the Escape menu's page (0 the main one, 1 Options) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward4") int32 GetMenuPage() const { return MenuPage; }
	/** the resolutions the Options page offers (the common ones no larger than the screen), "1920x1080" each */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward4") TArray<FString> GetResolutionChoices() const;
	/** the display settings chosen on the page (not applied yet) and what Apply did ("applied", or why not) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward4") FIntPoint PendingResolution = FIntPoint::ZeroValue;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward4") int32 PendingWindowMode = 1;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward4") FString LastApplied;
	/** Apply: the chosen resolution and display mode into the game's user settings, applied and saved (in the editor saved
	 *  only: play in the editor does not own its window) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward4") bool ApplyDisplaySettings();
	/** a spot for a new ally of Radius near From: in front of Facing first, then round her; clear of walls (a trace from
	 *  her) and of every ally standing (their capsules and RD4AllyGap); false: none clear, OutAt the roomiest */
	bool FindAllySpot(const FVector& From, const FVector& Facing, float Radius, const AActor* Ignore, FVector& OutAt) const;

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
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Menu") int32 GetMenuCursor() const { return MenuCursor; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Menu") void MoveMenuCursor(int32 Step);
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
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") void CenterMap() { MapPan = FVector2D::ZeroVector; }

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
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") void SetMapOpen(bool bOpen) { if (bOpen && !bMapOpen) MapPan = FVector2D::ZeroVector; bMapOpen = bOpen; }
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
	void PlaceBoss(int32 Tier);
	void PlaceRingGuard(int32 Tier);
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
};
