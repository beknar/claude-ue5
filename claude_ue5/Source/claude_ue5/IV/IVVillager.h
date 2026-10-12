// random_isometric_village_level: a villager going about the village. Picks a spot in its own 250 m section (in front of
// a house, on a street, on the market square), walks there over the nav grid without entering houses, stands a while,
// repeats. No controller and no movement component: the village is flat, so it is moved along its path directly (many
// villagers cost next to nothing). It gives way to the player and steps aside when she walks into it.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IVTypes.h"
#include "IVVillager.generated.h"

class AIVSection;
class UCapsuleComponent;
class USkeletalMeshComponent;

UCLASS()
class CLAUDE_UE5_API AIVVillager : public AActor
{
	GENERATED_BODY()

public:
	AIVVillager();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage") TObjectPtr<UCapsuleComponent> Capsule;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage") TObjectPtr<USkeletalMeshComponent> Mesh;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage") TObjectPtr<AIVSection> Section;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage") FName VillagerName;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage") int32 TripsDone = 0;
	/** trips given up (the player or another villager in the way, no path) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage") int32 Repaths = 0;
	/** distance walked so far (cm) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage") float Walked = 0.f;

	void Setup(AIVSection* InSection, const FIVVillagerDef& Def, int32 InSeed);
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") bool IsWalking() const { return Path.Num() > 0 && WaitTime <= 0.f; }
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") FVector GetGoal() const { return Goal; }
	/** point on the ground under it */
	FVector2D Ground() const { const FVector L = GetActorLocation(); return FVector2D(L.X, L.Y); }

protected:
	virtual void Tick(float DeltaSeconds) override;

private:
	UPROPERTY(Transient) TObjectPtr<UAnimationAsset> IdleAnim;
	UPROPERTY(Transient) TObjectPtr<UAnimationAsset> WalkAnim;
	FRandomStream R;
	TArray<FVector> Path;      // world points on the ground
	FVector Goal = FVector::ZeroVector;
	float WalkSpeed = 140.f, ClipSpeed = 237.f, Speed = 0.f, HalfHeight = 88.f;
	float WaitTime = 1.f, BlockedTime = 0.f, YieldTime = 0.f;
	bool bWalkingAnim = false;
	void PickTrip();
	void SetWalkingAnim(bool bWalk);
	void StandStill(float Dt);
};
