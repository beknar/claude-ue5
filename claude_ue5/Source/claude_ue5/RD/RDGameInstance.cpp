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
	TownLooted.Reset(); CastleTiers.Reset(); CastleStartLooted.Reset(); GuardsDead.Reset();
	Arrive.Reset();
	UE_LOG(LogTemp, Log, TEXT("RDGAME new game %d for %s"), GamesStarted, *Hero.ToString());
}
