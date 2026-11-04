// The game saved to disk (the user's choice of 2026-11-03: "autosave + a Save / Load menu"): what the game instance keeps
// between the levels (its SaveGame properties: her things, gold, storage, quests, the towns' seeds and what she opened, the
// castle's tiers, the day, the wilderness's seed, the map she revealed, the places she found), the level she was in and
// where. Two slots: "autosave" (written when she finds a place, comes into a town, before and after fast travel, before
// she goes through the Mistgate, on Quit, and every two minutes the map grows) and "save" (the Escape menu's Save game).
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "RDSave.generated.h"

UCLASS()
class CLAUDE_UE5_API URDSaveGame : public USaveGame
{
	GENERATED_BODY()
public:
	UPROPERTY() int32 Version = 1;
	UPROPERTY() FDateTime SavedAt;
	/** the level's package ("/Game/RandomDungeon/Maps/brokenspire") */
	UPROPERTY() FString Level;
	UPROPERTY() FName Hero;
	UPROPERTY() FVector At = FVector::ZeroVector;
	UPROPERTY() float Yaw = 0.f;
	UPROPERTY() FString Why;
	/** where, in words ("Brokenspire", "the wilds: temperate aspen near Ashenreach") */
	UPROPERTY() FString Place;
	/** the game instance's SaveGame properties, serialized */
	UPROPERTY() TArray<uint8> Game;

	/** the game instance filled from the slot and the level opened (she is put where she was when it has loaded) */
	static bool LoadAndOpen(UObject* Ctx, const FString& Slot);
	/** "<date>|<level>|<place>|<hero>|<why>" of a slot, or "" */
	static FString Info(const FString& Slot);
	/** the slot with the newest save, or "" */
	static FString Latest();
};
