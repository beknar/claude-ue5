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
	/** the slashes on her found weapons, each with its weapon's item: Things carries a slash as a thing of its own beside the
	 *  weapon (as it drops at a death), so it goes back on a weapon of that item (by name: a weapon the level cannot give back
	 *  must not move the others' slashes) */
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<FName> SlashWeapons;
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<FName> SlashNames;
	/** her summons standing: each one's summoning (its spell) and its share of hit points */
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<FName> Summons;
	UPROPERTY(SaveGame, BlueprintReadOnly) TArray<float> SummonShares;
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
	/** where she comes into the town: "" the town square (a new game), "castle" the castle's door (back from the castle),
	 *  "portal" before the Mistgate (tests) */
	UPROPERTY(BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") FString Arrive;
	/** the Mistward Hall's guards she killed this game (they do not come back) */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<int32> GuardsDead;
	/** her things lying where she fell when she left a level (each pile's things, wear and worn shield; its Hero is the
	 *  level it lay in, "castle" or "town"): laid again where she comes into that level the next time */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<FRDCarry> HerPiles;
	/** the town's time of day (hours, 0-24; -1: a new game, the town starts its day at TownStartHour) and which day it is:
	 *  kept while she is in the castle (the castle is indoors: its clock stands still there) */
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") float TownHour = -1.f;
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") int32 TownDay = 1;
	/** the list of 2026-11-04: the gardens she harvested (town seed and garden packed, "<seed>:<garden>") and the day of it; the
	 *  tables' food she took ("<seed>:<table>") */
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TMap<FString, int32> GardensHarvested;
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<FString> FoodTaken;
	/** the portcullis raised (it stays as she left it) */
	UPROPERTY(SaveGame, BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") bool bPortcullisUp = false;
	/** the showcase's command line read (once a game) */
	bool bShow7Read = false;
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
