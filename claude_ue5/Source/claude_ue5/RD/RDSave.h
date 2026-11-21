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
	/** the world it was made in (apart from the save's own format, Version: PR #89's review); 1 in every save made before it */
	UPROPERTY() int32 WorldVer = 1;
	/** the wilderness's version (the list of 2026-11-16's world phases: each that moves the wilds' places raises it); a save of an
	 *  older one loads with its wild state dropped, in Brokenspire's square (DropOldWorld) */
	static constexpr int32 WorldVersion = 6;          // (6: the villages' terraces and their 8 to 15 houses, the list of 2026-11-20; 2: the 150 km continent; 3: the cities' regions and easing; 4: the density's cells and ids; 5: the roads (PR #92's review: merged major roads, minor roads, wider beds move places))
	/** an older world's save: what the wilds held dropped (her found places, her map's fog, her wild kills and quests' states, her
	 *  place out there and a way back from a city's dungeon); her hero, things, gold and the towns kept */
	static void DropOldWorld(class URDGameInstance* GI, int32 FromVersion);
	UPROPERTY() FDateTime SavedAt;
	/** the level's package ("/Game/RandomDungeon/Maps/brokenspire") */
	UPROPERTY() FString Level;
	UPROPERTY() FName Hero;
	UPROPERTY() FVector At = FVector::ZeroVector;
	UPROPERTY() float Yaw = 0.f;
	UPROPERTY() FString Why;
	/** the name she gave it (the list of 2026-11-04; "" an autosave or an older save) */
	UPROPERTY() FString Name;
	/** where, in words ("Brokenspire", "the wilds: temperate aspen near Ashenreach") */
	UPROPERTY() FString Place;
	/** made in a town (Brokenspire's level): she is put back at At when it loads. A castle's save puts her at the castle's
	 *  own start (nothing in the castle reads At: the flag left set once put her at the castle's coordinates in the wilds) */
	UPROPERTY() bool bInTown = false;
	/** the game instance's SaveGame properties, serialized */
	UPROPERTY() TArray<uint8> Game;

	/** the game instance filled from the slot and the level opened (she is put where she was when it has loaded) */
	static bool LoadAndOpen(UObject* Ctx, const FString& Slot);
	/** "<date>|<level>|<place>|<hero>|<why>|<name>" of a slot, or "" (read again only when the slot's file changes) */
	static FString Info(const FString& Slot);
	/** the slots on disk ("autosave", "save", "save_<name>"...), newest first */
	static TArray<FString> AllSlots();
	/** the slot with the newest save, or "" (from the same cached reads) */
	static FString Latest();
	/** a slot's info and time, read from the file once per change of its timestamp */
	static bool ReadHead(const FString& Slot, FString& OutInfo, FDateTime& OutSavedAt);
};
