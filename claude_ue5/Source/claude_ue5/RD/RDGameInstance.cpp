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
	Arrive.Reset();
	TownHour = -1.f; TownDay = 1;
	GardensHarvested.Reset(); FoodTaken.Reset(); bPortcullisUp = false;
	// (a new continent each game: the seed from the clock)
	WildSeed = (int32)(FDateTime::Now().GetTicks() % 1999999999) + 1;
	WildRevealKeys.Reset(); WildRevealBits.Reset(); WildFound.Reset(); WildKilled.Reset(); TownStore.Reset();
	CurrentTown = TEXT("Brokenspire");
	UE_LOG(LogTemp, Log, TEXT("RDGAME new game %d for %s"), GamesStarted, *Hero.ToString());
}
