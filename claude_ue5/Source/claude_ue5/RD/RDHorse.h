// The ridable horse (the user's list of 2026-11-08b, docs/improvements9.txt, its eighth phase: "make a rideable horse for a player
// to buy and ride with increased speed across the wilderness"; RDHorse.cpp, 913). The horse is built in Blender as the farm animals
// are (farm_animals.py's horse: Idle, Walk and a Run (a gallop), a `saddle` bone); it plays its clip by the speed it goes at.
// The user's of 2026-11-18 (HorseDef.bPack: the Ultimate Horse Pack's realistic horse, its saddle and its own clips, crossfaded by
// URDHorseAnimInstance; the ride in RDHorse15.cpp, 933).
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
	/** the actor's origin at its feet, facing +X; the pivot under it pitches the horse to the ground's slope (RDHorse15.cpp) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") TObjectPtr<USceneComponent> Pivot;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") TObjectPtr<USkeletalMeshComponent> Body;
	/** the pack's saddle (HorseDef.SaddleMesh), posed by the body */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") TObjectPtr<USkeletalMeshComponent> Saddle;
	/** the list of 2026-11-10 ("the player can walk through the horse"): a box round its body that stops pawns while it stands
	 *  unridden; off while she rides it (her capsule is what moves then) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") TObjectPtr<class UBoxComponent> Blocker;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") void SetBlocking(bool bOn);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool IsBlocking() const;
	/** hers (bought), or the stable's own standing by the stable to be bought */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") bool bHers = false;
	/** the clip it plays now ("idle", "walk", "canter", "run"; the pack's horse also "back", "stop", "jump", "land", "rear", "swim",
	 *  "swimidle", "hit") and at what rate (tests) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") FName ClipNow;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") float RateNow = 1.f;
	/** the strides a second its clip takes at its rate now (her rider clip in step; tests: the list of 2026-11-12) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetStridesASecond() const;
	/** the pack's horse: the clip's share of its loop now (tests: the hooves' landings) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetClipPhase() const;
	void Init(const FRDHorseDef& InDef, bool bSecondColouring);
	/** its clip for a speed (cm/s): idle still, the walk, the canter, the gallop, at the rate its soles keep to the ground */
	void PlayFor(float Speed);
	/** the pack's horse: a named clip, crossfaded (RDHorse15.cpp picks them) */
	void PlayClip15(FName Name, UAnimSequenceBase* Clip, bool bLoop, float Rate, float Blend, float StartTime = -1.f);
	class URDHorseAnimInstance* GetAnim15() const;
	/** where the rider's root goes: its saddle bone (the pack's horse: its rider socket) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") FVector GetSaddleLocation() const;
	const FRDHorseDef& GetDef() const { return Def; }
private:
	FRDHorseDef Def;
	UPROPERTY() TObjectPtr<UAnimSequenceBase> ClipAsset;
};
