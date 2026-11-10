// The ridable horse (the user's list of 2026-11-08b, docs/improvements9.txt, its eighth phase: "make a rideable horse for a player
// to buy and ride with increased speed across the wilderness"; RDHorse.cpp, 913). The horse is built in Blender as the farm animals
// are (farm_animals.py's horse: Idle, Walk and a Run (a gallop), a `saddle` bone); it plays its clip by the speed it goes at.
#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RD/RDTypes.h"
#include "RDHorse.generated.h"

UCLASS()
class CLAUDE_UE5_API ARDHorse : public AActor
{
	GENERATED_BODY()
public:
	ARDHorse();
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") TObjectPtr<USkeletalMeshComponent> Body;
	/** the list of 2026-11-10 ("the player can walk through the horse"): a box round its body that stops pawns while it stands
	 *  unridden; off while she rides it (her capsule is what moves then) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") TObjectPtr<class UBoxComponent> Blocker;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") void SetBlocking(bool bOn);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool IsBlocking() const;
	/** hers (bought), or the stable's own standing by the stable to be bought */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") bool bHers = false;
	/** the clip it plays now ("idle", "walk", "run") and at what rate (tests) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") FName ClipNow;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") float RateNow = 1.f;
	void Init(const FRDHorseDef& InDef, bool bSecondColouring);
	/** its clip for a speed (cm/s): idle still, the walk, the gallop, at the rate its soles keep to the ground */
	void PlayFor(float Speed);
	/** where the rider's root goes: its saddle bone */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") FVector GetSaddleLocation() const;
private:
	FRDHorseDef Def;
};
