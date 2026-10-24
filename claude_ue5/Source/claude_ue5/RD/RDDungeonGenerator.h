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
	// start section 1, the 8 round it 2, the 16 round those 3...). Tier 2 is generated as she walks toward it; tier T > 2
	// only once every section of tier T - 1 is cleared (every room explored, every chest and trunk looted, every monster
	// spawned there killed). Nothing beyond MaxTier is generated. A hallway that leads to a section not to be generated is
	// sealed where it leaves its section: a grating (SealPiece, twice across the hallway) while the tier is shut, a wall
	// (EndPiece) at the end of the dungeon, both with a blocker as tall as the hallway.
	/** the last tier (0: no tiers, the dungeon goes on for ever) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Tiers") int32 MaxTier = 0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Tiers") FName SealPiece = TEXT("CellFrame");
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Tiers") FName EndPiece = TEXT("Wall_Corr");
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Tiers") int32 TierOf(FIntPoint Section) const { return FMath::Max(FMath::Abs(Section.X), FMath::Abs(Section.Y)) + 1; }
	/** sections in a tier: 1, 8, 16, 24... */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Tiers") int32 TierSize(int32 Tier) const { return Tier <= 1 ? 1 : 8 * (Tier - 1); }
	/** its sections may be generated (tiers 1 and 2 always; another once the tier before it is cleared; none past MaxTier) */
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
	/** counts what she did in a section again, and announces a set cleared or a tier opened */
	void UpdateProgress(FIntPoint Section);
	/** "SET CLEARED" / "TIER 3 IS OPEN" (HUD) and when */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Tiers") FString TierNotice;
	float TierNoticeTime = -100.f;
	/** seals on every generated section as the tiers are now */
	void RefreshSeals();

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
	/** weighted means of the monster kinds' factors (a monster's values are divided by them) */
	void MeanMonsterFactors(float& Health, float& Damage) const;
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

private:
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
