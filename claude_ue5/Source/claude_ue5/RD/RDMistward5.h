// mistward_castle, the list of 2026-10-31b (docs/improvements5.txt; pipeline/unreal/879): the arena's audience.
//   ARDSpectator   a townsperson (the NPC pack) standing along the arena's wall, facing its middle: idle, and clapping or
//                  cheering when the generator says so (a wave comes, a monster falls, the arena is won); it appears and
//                  leaves in a puff
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RDTypes.h"
#include "RDMistward5.generated.h"

class USkeletalMeshComponent;
class UAnimationAsset;
class USkeletalMesh;

UCLASS()
class CLAUDE_UE5_API ARDSpectator : public AActor
{
	GENERATED_BODY()
public:
	ARDSpectator();
	/** its body, its clips (claps and cheers: one is chosen each time), its seed (its own delays) */
	void Init(USkeletalMesh* Mesh, UAnimationAsset* InIdle, const TArray<UAnimationAsset*>& InClaps, const TArray<UAnimationAsset*>& InCheers, int32 Seed);
	/** after Delay seconds: a clap (or a cheer) once, then back to idle */
	void React(bool bCheer, float Delay);
	/** what it does now: "idle", "clap", "cheer", "leaving" (tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") FString GetDoing() const;
	/** reactions it made (tests) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") int32 Reactions = 0;
	/** leave after Delay (the generator puffs it away) */
	void LeaveAfter(float Delay) { LeaveAt = Age + Delay; }
	bool IsLeaving() const { return LeaveAt >= 0.f; }
	bool ShouldGo() const { return LeaveAt >= 0.f && Age >= LeaveAt; }
	USkeletalMeshComponent* GetBody() const { return Body; }
protected:
	virtual void Tick(float Dt) override;
private:
	UPROPERTY() TObjectPtr<USceneComponent> Root;
	UPROPERTY() TObjectPtr<USkeletalMeshComponent> Body;
	UPROPERTY(Transient) TObjectPtr<UAnimationAsset> IdleAnim;
	UPROPERTY(Transient) TArray<TObjectPtr<UAnimationAsset>> Claps;
	UPROPERTY(Transient) TArray<TObjectPtr<UAnimationAsset>> Cheers;
	FRandomStream R;
	float Age = 0.f, PendingAt = -1.f, BusyUntil = -1.f, LeaveAt = -1.f;
	bool bPendingCheer = false;
	uint8 Doing = 0;          // 0 idle, 1 clap, 2 cheer
	void PlayIdle();
};
