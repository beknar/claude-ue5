#include "RD/RDGameInstance.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

URDGameInstance* URDGameInstance::Of(const UObject* Ctx)
{
	return Cast<URDGameInstance>(UGameplayStatics::GetGameInstance(Ctx));
}

void URDGameInstance::NewGame(FName Hero)
{
	GameHero = Hero; ++GamesStarted;
	Carry = FRDCarry();
	Gold = 0; TownSeed = 0;
	StashThings.Reset(); StashWear.Reset();
	Quests.Reset(); Counters.Reset();
	CirclesFound = { FName(TEXT("Brokenspire")) };
	TownLooted.Reset(); CastleTiers.Reset(); CastleStartLooted.Reset(); GuardsDead.Reset(); HerPiles.Reset();
	Dungeons.Reset(); ReturnAt = FVector::ZeroVector; ReturnYaw = 0.f; ReturnTown.Reset();
	CaveKey15.Reset(); CaveTier15 = 0; WildMarked15.Reset(); WildLookoutsClimbed15.Reset(); RoamersSeen15.Reset(); RoamersSlain15.Reset(); CollectiblesTaken15.Reset(); LastingHealth15 = LastingMana15 = 0; TreasureMapsTaken15.Reset(); TreasureMaps15.Reset(); TreasuresDug15.Reset(); PlaceItemsGiven15.Reset(); ContractsTaken15.Reset(); ContractsDone15.Reset(); ContractsPaid15.Reset(); ContractSigns15.Reset(); CampsCleared15.Reset(); CampsClearedDay15.Reset(); CampsResettledFrom15.Reset(); RuinsResettled15.Reset();          // (the list of 2026-11-20's ninth phase (PR #101's review): no cave carried into a new game)
	bOldWorld = false;          // (the list of 2026-11-16: an older save's give-back is not the new game's (PR #89's review))
	Arrive.Reset();
	TownHour = -1.f; TownDay = 1;
	GardensHarvested.Reset(); FoodTaken.Reset(); bPortcullisUp = false; bHorseOwned = false;
	HorsesTamed = 0; bRideTamed = false; bTamedOnly = false;          // (the list of 2026-11-12's tamed horse goes with the game)
	LootedItems.Reset();          // (the list of 2026-11-10: the forge makes what she has looted in this game (PR #40's review))
	KnownRecipes.Reset();          // (the list of 2026-11-16's sixth phase: a new game knows only the plain recipes)
	// (a new continent each game: the seed from the clock)
	WildSeed = (int32)(FDateTime::Now().GetTicks() % 1999999999) + 1;
	WildRevealKeys.Reset(); WildRevealBits.Reset(); WildFound.Reset(); WildKilled.Reset(); TownStore.Reset();
	CurrentTown = TEXT("Brokenspire");
	UE_LOG(LogTemp, Log, TEXT("RDGAME new game %d for %s"), GamesStarted, *Hero.ToString());
}
