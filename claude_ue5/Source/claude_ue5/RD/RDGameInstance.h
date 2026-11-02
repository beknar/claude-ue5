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
	UPROPERTY(BlueprintReadOnly) bool bValid = false;
	UPROPERTY(BlueprintReadOnly) FName Hero;
	UPROPERTY(BlueprintReadOnly) TArray<FName> Things;
	UPROPERTY(BlueprintReadOnly) TArray<float> Wear;
	UPROPERTY(BlueprintReadOnly) FName WornArmour;
	UPROPERTY(BlueprintReadOnly) FName WornShield;
	UPROPERTY(BlueprintReadOnly) TArray<FName> WornRings;
	/** spells learned from tomes and chi attacks gained (spell weapons not on her card), by name */
	UPROPERTY(BlueprintReadOnly) TArray<FName> Learned;
	UPROPERTY(BlueprintReadOnly) int32 WeaponsUnlocked = 0;
	UPROPERTY(BlueprintReadOnly) float Health = -1.f;
	UPROPERTY(BlueprintReadOnly) float Mana = -1.f;
	UPROPERTY(BlueprintReadOnly) FString Blessing;
	UPROPERTY(BlueprintReadOnly) float BlessLeft = 0.f;
	UPROPERTY(BlueprintReadOnly) float BlessDamage = 0.f;
	UPROPERTY(BlueprintReadOnly) float BlessArmour = 0.f;
	/** the weapon in her hands (its name) */
	UPROPERTY(BlueprintReadOnly) FName Drawn;
};

/** a quest she was given: 1 taken, 2 turned in; Base: its counter when taken (its progress is the counter less this) */
USTRUCT(BlueprintType)
struct FRDQuestState
{
	GENERATED_BODY()
	UPROPERTY(BlueprintReadOnly) FName Id;
	UPROPERTY(BlueprintReadOnly) uint8 State = 0;
	UPROPERTY(BlueprintReadOnly) int32 Base = 0;
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
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") FName GameHero;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") int32 GamesStarted = 0;

	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") FRDCarry Carry;
	/** her purse */
	UPROPERTY(BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") int32 Gold = 0;
	/** the town of this game (0: not made yet: the town picks one) */
	UPROPERTY(BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") int32 TownSeed = 0;
	/** what she keeps in the storehouse (things and what is left of each, as carried) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<FName> StashThings;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<float> StashWear;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<FRDQuestState> Quests;
	/** what the quests count: see FRDQuestDef::Goal */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TMap<FString, int32> Counters;
	/** the teleport circles she has found (Brokenspire's is known from the start) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<FName> CirclesFound;
	/** the town's containers she has opened (their keys): they stay looted for the game */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<int32> TownLooted;
	/** the castle's tiers she has opened (they stay open), the start set's containers she opened there */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<int32> CastleTiers;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<int32> CastleStartLooted;
	/** where she comes into the town: "" the town square (a new game), "castle" the castle's door (back from the castle),
	 *  "portal" before the Mistgate (tests) */
	UPROPERTY(BlueprintReadWrite, Category = "RandomDungeon|Brokenspire") FString Arrive;
	/** the Mistward Hall's guards she killed this game (they do not come back) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") TArray<int32> GuardsDead;

	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Brokenspire") void Count(const FString& Key, int32 Amount = 1) { Counters.FindOrAdd(Key) += Amount; }
	/** a counter that holds the highest value seen ("tier") */
	void CountMax(const FString& Key, int32 Value) { int32& V = Counters.FindOrAdd(Key); V = FMath::Max(V, Value); }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") int32 GetCounter(const FString& Key) const { const int32* V = Counters.Find(Key); return V ? *V : 0; }
	FRDQuestState* FindQuest(FName Id) { return Quests.FindByPredicate([Id](const FRDQuestState& Q) { return Q.Id == Id; }); }
	const FRDQuestState* FindQuest(FName Id) const { return Quests.FindByPredicate([Id](const FRDQuestState& Q) { return Q.Id == Id; }); }
};
