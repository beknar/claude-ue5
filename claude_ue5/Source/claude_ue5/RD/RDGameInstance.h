// Brokenspire (docs/brokenspire.txt): what a game keeps while she goes between the town and Mistward Castle. A level
// change makes everything of the level new (the generator, her pawn and its combat component); the game instance stays.
// The hero menu starts a new game (NewGame); the town and the castle each put her things here before they open the other
// (ARDDungeonGenerator::SaveCarry) and take them back when her combat component is made (RestoreCarry).
// DefaultEngine.ini names it the game's GameInstanceClass. Nothing here is saved to disk: a game lasts while the program runs.
#pragma once

#include "CoreMinimal.h"
#include "Engine/GameInstance.h"
#include "RDGameInstance.generated.h"

/** her things as she leaves a level: the found weapons and everything carried (each with what is left of it: the
 *  generator's GatherDroppable), what she wears, the spells she learned, her hit points and mana, a blessing on her */
USTRUCT(BlueprintType)
struct FRDCarry
{
	GENERATED_BODY()
	UPROPERTY(SaveGame, BlueprintReadOnly) bool bValid = false;
	UPROPERTY(SaveGame, BlueprintReadOnly) FName Hero;
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<FName> Things;
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<float> Wear;
	UPROPERTY(SaveGame, BlueprintReadOnly) FName WornArmour;
	UPROPERTY(SaveGame, BlueprintReadOnly) FName WornShield;
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<FName> WornRings;
	/** spells learned from tomes and chi attacks gained (spell weapons not on her card), by name */
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<FName> Learned;
	UPROPERTY(SaveGame, BlueprintReadOnly) int32 WeaponsUnlocked = 0;
	UPROPERTY(SaveGame, BlueprintReadOnly) float Health = -1.f;
	UPROPERTY(SaveGame, BlueprintReadOnly) float Mana = -1.f;
	UPROPERTY(SaveGame, BlueprintReadOnly) FString Blessing;
	UPROPERTY(SaveGame, BlueprintReadOnly) float BlessLeft = 0.f;
	UPROPERTY(SaveGame, BlueprintReadOnly) float BlessDamage = 0.f;
	UPROPERTY(SaveGame, BlueprintReadOnly) float BlessArmour = 0.f;
	/** the weapon in her hands (its name) */
	UPROPERTY(SaveGame, BlueprintReadOnly) FName Drawn;
	// ---- the rest of her state (the user's of 2026-11-06: "they should bring with them their current state ... this includes
	// statistics and all inventory items"; URDCombatComponent::GatherState / RestoreState, RDCarry.cpp)
	/** her statistics: the combat component's counters by name; each spell's casts; each slash's procs */
	UPROPERTY(SaveGame, BlueprintReadOnly) TMap<FName, float> Stats;
	UPROPERTY(SaveGame, BlueprintReadOnly) TMap<FName, int32> SpellCasts;
	UPROPERTY(SaveGame, BlueprintReadOnly) TMap<FString, int32> SlashProcs;
	/** what is on her, for how long: a timed state's seconds left ("<Name>Left") and its strength ("<Name>") */
	UPROPERTY(SaveGame, BlueprintReadOnly) TMap<FName, float> Timed;
	/** the potions and food working on her: each one's item, kind, amount and seconds left */
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<FName> EffectItems;
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<uint8> EffectKinds;
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<float> EffectAmounts;
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<float> EffectLeft;
	/** her weapons' and spells' cooldowns: the seconds left, by name */
	UPROPERTY(SaveGame, BlueprintReadOnly) TMap<FName, float> Cooldowns;
	/** the Rogue's dexterity energy (-1: none) */
	UPROPERTY(SaveGame, BlueprintReadOnly) float DexEnergy = -1.f;
	/** the quick bar: its slots, the entries taken off it, the first slot shown */
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<FName> QuickSlots;
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<FName> QuickOff;
	UPROPERTY(SaveGame, BlueprintReadOnly) int32 QuickFirst = 0;
	/** the torch lit in her hand (its item; none: not lit) */
	UPROPERTY(SaveGame, BlueprintReadOnly) FName TorchHeld;
	/** the list of 2026-11-22's caves, phase 11: the sockets filled (a gear and its stone, side by side) */
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<FName> SocketGear16;
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<FName> SocketStone16;
	/** the slashes on her found weapons, each with its weapon's item: Things carries a slash as a thing of its own beside the
	 *  weapon (as it drops at a death), so it goes back on a weapon of that item (by name: a weapon the level cannot give back
	 *  must not move the others' slashes) */
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<FName> SlashWeapons;
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<FName> SlashNames;
	/** her summons standing: each one's summoning (its spell) and its share of hit points */
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<FName> Summons;
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<float> SummonShares;
	/** the list of 2026-11-20 (item 18): each summon's kind (beside Summons), and the kind she chose for each summoning */
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<FName> SummonKinds15;
	UPROPERTY(SaveGame, BlueprintReadOnly) TMap<FName, FName> SummonPicks15;
	/** the list of 2026-11-08b's sixth phase: her secondary abilities' ranks and the spells her boosts raise */
	UPROPERTY(SaveGame, BlueprintReadOnly) TMap<FName, int32> SecondaryRanks;
	UPROPERTY(SaveGame, BlueprintReadOnly) TMap<FName, FName> BoostSpells;
};

/** a dungeon level other than Mistward Castle (Vel Morrath's catacombs, 2026-11-06): the tiers she opened there and the
 *  containers of its first set of rooms she opened (the castle's are the game instance's CastleTiers / CastleStartLooted) */
USTRUCT(BlueprintType)
struct FRDDungeonSave
{
	GENERATED_BODY()
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<int32> Tiers;
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<int32> StartLooted;
};

/** a town of the wilderness she is not in: its seed, the containers she opened there, its guards she killed */
USTRUCT(BlueprintType)
struct FRDTownSave
{
	GENERATED_BODY()
	UPROPERTY(SaveGame, BlueprintReadOnly) int32 Seed = 0;
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<int32> Looted;
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<int32> GuardsDead;
};

/** a quest she was given: 1 taken, 2 turned in; Base: its counter when taken (its progress is the counter less this) */
USTRUCT(BlueprintType)
struct FRDQuestState
{
	GENERATED_BODY()
	UPROPERTY(SaveGame, BlueprintReadOnly) FName Id;
	UPROPERTY(SaveGame, BlueprintReadOnly) uint8 State = 0;
	UPROPERTY(SaveGame, BlueprintReadOnly) int32 Base = 0;
};

UCLASS()
class CLAUDE_UE5_API URDGameInstance : public UGameInstance
{
	GENERATED_BODY()
public:
	/** the game instance of a world, or none (another game instance class: nothing is kept) */
	static URDGameInstance* Of(const UObject* Ctx);
	/** the list of 2026-11-22 (RDList16.cpp): a -RDPerf run (the packaged game's measures): its world and its towns from fixed seeds, so the
	 *  runs before and after the list's changes stand in the same places */
	static bool IsPerfRun16();
	static constexpr int32 PerfSeed16 = 16016;
	/** the list of 2026-11-22 (RDList16b.cpp): the engine's loading screen while a map loads (a packaged game's: the movie player) */
	virtual void Init() override;
	void BeginLoadingScreen16(const FString& Map);

	/** a new game for this hero: nothing carried, an empty purse and storage, no quests, a new town */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Brokenspire") void NewGame(FName Hero);
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") FName GameHero;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") int32 GamesStarted = 0;

	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") FRDCarry Carry;
	/** her state as she left the last level (her combat component's GetStateLines as SaveCarry took it: the tests set it
	 *  against the next level's GetCarryArrivedLines) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<FString> CarryLeftLines;
	/** her purse */
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") int32 Gold = 0;
	/** the town of this game (0: not made yet: the town picks one) */
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") int32 TownSeed = 0;
	/** what she keeps in the storehouse (things and what is left of each, as carried) */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<FName> StashThings;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<float> StashWear;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<FRDQuestState> Quests;
	/** what the quests count: see FRDQuestDef::Goal */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TMap<FString, int32> Counters;
	/** the teleport circles she has found (Brokenspire's is known from the start) */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<FName> CirclesFound;
	/** the town's containers she has opened (their keys): they stay looted for the game */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<int32> TownLooted;
	/** the castle's tiers she has opened (they stay open), the start set's containers she opened there */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<int32> CastleTiers;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<int32> CastleStartLooted;
	/** the other dungeon levels' (the generator's DungeonKey: "vel_morrath" the catacombs under Vel Morrath's cathedral) */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TMap<FString, FRDDungeonSave> Dungeons;
	/** a dungeon's tiers and first set's opened containers by its key (empty: Mistward Castle's own fields) */
	TArray<int32>& TiersOf(const FString& Key) { return Key.IsEmpty() ? CastleTiers : Dungeons.FindOrAdd(Key).Tiers; }
	TArray<int32>& StartLootedOf(const FString& Key) { return Key.IsEmpty() ? CastleStartLooted : Dungeons.FindOrAdd(Key).StartLooted; }
	/** a counter of a dungeon's ("bossdone:2", "enter"...): Mistward Castle's as they were, another's under its key
	 *  ("vel_morrath:bossdone:2") */
	static FString DungeonCounter(const FString& Key, const FString& Name) { return Key.IsEmpty() ? Name : Key + TEXT(":") + Name; }
	/** where she comes back to the wilderness from a dungeon entered from a town of it that is not Brokenspire (the cathedral of
	 *  Vel Morrath: before its door), facing which way; the town */
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") FVector ReturnAt = FVector::ZeroVector;
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float ReturnYaw = 0.f;
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") FString ReturnTown;
	/** the list of 2026-11-20's ninth phase: the cave she went down into (its key, "cave:<i>_<j>") and its game tier */
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|List15") FString CaveKey15;
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|List15") int32 CaveTier15 = 0;
	/** the list of 2026-11-22's caves: the biome at the cave's tower (its region: a geode's colour, the cold's or the heat's ores) */
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Cave16") FString CaveBiome16;
	/** the caves whose lost blade she has taken (their keys): laid no more */
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FString> LostBladeCaves16;
	/** the caves whose drowned knight's piece she has taken (their keys): laid no more */
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FString> DrownedCaves16;
	/** the cursed relics a temple has lifted (their items): their cost gone for good */
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FName> LiftedRelics16;
	/** phase 15: the cave paintings studied ("<cave key>|<region>"), those applied to the wilds' map, the caves they marked (tower squares) */
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FString> Paintings16;
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FString> PaintingsApplied16;
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FIntPoint> KnownCaves16;
	/** phase 16: the caves' maps read ("<cave key>|<n>|<target place id>", -1 not yet found, -2 none), the contract beasts fled into a cave
	 *  ("<id>|<cave key>|<kind>|<tier>|<hp>|<name>"), the travellers rescued ("<name>|<cave key>|<set>|<state>": 0 out, c<camp> settled,
	 *  2 waiting for a town, 3 brought home), the mouths attuned, the towers' keys, the towers climbed and their chests opened */
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FString> CaveMaps16;
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FString> ContractsInCave16;
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FString> RescuedTravellers16;
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FIntPoint> CaveMouthsAttuned16;
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FIntPoint> TowerKeys16;
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FIntPoint> TowersClimbed16;
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Cave16") TArray<FIntPoint> TowerChests16;
	/** the tenth phase: the places the lookouts' tops marked on her map, and the lookouts climbed */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|List15") TArray<int32> WildMarked15;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|List15") TArray<int32> WildLookoutsClimbed15;
	/** the eleventh phase: the roamers she has seen (their rounds on her map) and slain (dead for the game, their rings given) */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|List15") TArray<int32> RoamersSeen15;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|List15") TArray<int32> RoamersSlain15;
	/** the twelfth phase: the collectibles taken, the hit points and mana bought with them for good, the ruins' maps taken, the maps held
	 *  (their chests not dug), the chests dug, the structures' kinds whose named item was given */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|List15") TArray<int32> CollectiblesTaken15;
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|List15") int32 LastingHealth15 = 0;
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|List15") int32 LastingMana15 = 0;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|List15") TArray<int32> TreasureMapsTaken15;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|List15") TArray<int32> TreasureMaps15;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|List15") TArray<int32> TreasuresDug15;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|List15") TArray<FString> PlaceItemsGiven15;
	/** the thirteenth phase: the contracts taken, done (the beast killed by her) and paid (town x 16 + slot), the signs read (id x 4 + sign) */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|List15") TArray<int32> ContractsTaken15;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|List15") TArray<int32> ContractsDone15;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|List15") TArray<int32> ContractsPaid15;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|List15") TArray<int32> ContractSigns15;
	/** the fourteenth phase: the camps cleared and the day each was (side by side), the camps whose ruin was looked for, the ruins resettled */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|List15") TArray<int32> CampsCleared15;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|List15") TArray<int32> CampsClearedDay15;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|List15") TArray<int32> CampsResettledFrom15;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|List15") TArray<int32> RuinsResettled15;
	/** the kills' keys a resettling added (the ruin's guardians gone): only these a test's put-back takes out */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|List15") TArray<int64> ReclaimKeys15;
	/** the fifteenth phase: the people of the wilds she has met (who gave her something, whom she helped), the newest last: a courier's letter comes from one */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|List15") TArray<FString> MetPeople15;
	/** the sixteenth phase: the waystones she has lit (their ids) */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|List15") TArray<int32> WaystonesLit15;
	/** the eighteenth phase: a packaged game's run of the wilds (-RDTownGo=horse, village, cavetower; RDList15q.cpp): its way, its step, when
	 *  it goes on, and what it carries between its steps (not saved) */
	FString Go15, Go15Name;
	int32 Go15Stage = 0, Go15Try = 0, Go15Id = 0;
	float Go15At = 0.f, Go15T0 = 0.f;
	FVector Go15From = FVector::ZeroVector;
	/** where she comes into the town: "" the town square (a new game), "castle" the castle's door (back from the castle),
	 *  "portal" before the Mistgate (tests) */
	UPROPERTY(BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") FString Arrive;
	/** the Mistward Hall's guards she killed this game (they do not come back) */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<int32> GuardsDead;
	/** her things lying where she fell when she left a level (each pile's things, wear and worn shield; its Hero is the
	 *  level it lay in, "castle" or "town"): laid again where she comes into that level the next time */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<FRDCarry> HerPiles;
	/** the list of 2026-11-16: a save of an older world was loaded (URDSaveGame::DropOldWorld); the wilds give the captain's wild quests
	 *  back and tell her once (not saved) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List14") bool bOldWorld = false;
	/** the town's time of day (hours, 0-24; -1: a new game, the town starts its day at TownStartHour) and which day it is:
	 *  kept while she is in the castle (the castle is indoors: its clock stands still there) */
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float TownHour = -1.f;
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") int32 TownDay = 1;
	/** the list of 2026-11-11: rd.Tier's tier (0: none, the game's own): kept between the levels, not in a save (a test's) */
	UPROPERTY(BlueprintReadWrite, Category = "RandomDungeon|List11") int32 ConsoleTier = 0;
	/** the list of 2026-11-04: the gardens she harvested (town seed and garden packed, "<seed>:<garden>") and the day of it; the
	 *  tables' food she took ("<seed>:<table>") */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TMap<FString, int32> GardensHarvested;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<FString> FoodTaken;
	/** the list of 2026-11-10: every weapon, shield and set of armour that has gone into her pack (the forge makes those) */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<FName> LootedItems;
	/** the list of 2026-11-16's sixth phase: the recipes she has learned from found recipes (the items they make), for the game */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|List14") TArray<FName> KnownRecipes;
	/** the portcullis raised (it stays as she left it) */
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") bool bPortcullisUp = false;
	/** the eighth phase: she has bought a horse at a stable */
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") bool bHorseOwned = false;
	/** the list of 2026-11-12: the wild horses she has tamed (a quest's): each a mount of hers beside the one bought */
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") int32 HorsesTamed = 0;
	/** which of her two she has out: the tamed grey (true) or the bay she bought; the other waits at the stables */
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") bool bRideTamed = false;
	/** her only horse is one she tamed (none bought): the stable still sells her the bay */
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") bool bTamedOnly = false;
	/** the showcase's command line read (once a game) */
	bool bShow7Read = false;
	/** the reel of 2026-11-18 (RDReel15.cpp: -RDReel15): its stage and timeline, kept across the levels it goes through */
	bool bReelRead = false, bReel = false, bReelGoing = false, bReelShots = false;
	int32 ReelStage = 0, ReelRescues = 0;
	double ReelT0 = 0.0;
	FString ReelGo, ReelDone, ReelReady;
	TArray<FString> ReelLog;
	// ---- the wilderness (RDWild*.cpp): the world's seed, the map she revealed (50 m cells in blocks of 32 x 32: a block's
	// key and its 16 words), the places she found, the town she is in or nearest (whose state TownLooted and GuardsDead hold)
	// and the others' state
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Wild") int32 WildSeed = 0;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Wild") TArray<FIntPoint> WildRevealKeys;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Wild") TArray<int64> WildRevealBits;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Wild") TArray<int32> WildFound;
	/** the wilderness's monsters killed, by place and their number in its group (place id * 16 + n): a cleared lair stays
	 *  cleared when its chunk is made again (it was made again in full, gold and counters and all) */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Wild") TArray<int64> WildKilled;
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Wild") FString CurrentTown;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Wild") TMap<FString, FRDTownSave> TownStore;
	/** a game loaded from disk (RDSave.cpp): where she was, put back once the level has loaded */
	FVector LoadAt = FVector::ZeroVector;
	float LoadYaw = 0.f;
	bool bLoadPending = false;
	/** the final boss's showcase (a reel: -RDFinalShow [-RDShowGo=<file>] [-RDShowDone=<file>], RDAurorim.cpp): read once a game */
	bool bFinalShowRead = false, bFinalShow = false, bFinalShowEntered = false;
	FString FinalShowGo, FinalShowDone, FinalShowReady;
	/** -RDTownGo has been read (once a game instance) */
	bool bTownGoRead = false;
	/** -RDAllKeys (every dungeon's way open: the packaged game's runs) has been read (once a game instance) */
	bool bAllKeysRead = false;
	/** every dungeon's way open (-RDAllKeys, DebugAllDungeonKeys): never saved (PR #31's review: as a counter it went into the saves) */
	bool bAllDungeonKeys = false;
	/** -RDTownGo=town:<name>: the wilderness town she travels to once the wilds are ready (as given), and the one whose
	 *  building round her is still to be marked (-RDMarkFile; lower case, no spaces) */
	FString TownGoTown, TownGoMark;
	/** the showcase tour: the castle's autoplay seconds when it comes through the Mistgate (0: none) */
	float TourCastleSeconds = 0.f;
	bool bTourRead = false;

	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Brokenspire") void Count(const FString& Key, int32 Amount = 1) { Counters.FindOrAdd(Key) += Amount; }
	/** a counter that holds the highest value seen ("tier") */
	void CountMax(const FString& Key, int32 Value) { int32& V = Counters.FindOrAdd(Key); V = FMath::Max(V, Value); }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") int32 GetCounter(const FString& Key) const { const int32* V = Counters.Find(Key); return V ? *V : 0; }
	FRDQuestState* FindQuest(FName Id) { return Quests.FindByPredicate([Id](const FRDQuestState& Q) { return Q.Id == Id; }); }
	const FRDQuestState* FindQuest(FName Id) const { return Quests.FindByPredicate([Id](const FRDQuestState& Q) { return Q.Id == Id; }); }
};
