// random_dungeon_level: a wandering monster. Picks a random room of its section, walks there over the section's tile grid
// (hallways, doorways, free floor; doors on the way are pushed open and close again behind it), idles a while, repeats.
// No controller: CharacterMovement runs without one, the clips (idle / walk) play directly on the mesh.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "RDTypes.h"
#include "RDMonster.generated.h"

class ARDSection;

UCLASS()
class CLAUDE_UE5_API ARDMonster : public ACharacter
{
	GENERATED_BODY()

public:
	ARDMonster();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") TObjectPtr<ARDSection> Section;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") FName MonsterName;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") int32 TripsDone = 0;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") int32 Repaths = 0;

	void Setup(ARDSection* InSection, const FRDMonsterDef& Def, int32 InSeed);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") bool IsWalking() const { return Path.Num() > 0 && WaitTime <= 0.f; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") FVector GetGoal() const { return Goal; }

protected:
	virtual void Tick(float DeltaSeconds) override;

private:
	UPROPERTY(Transient) TObjectPtr<UAnimationAsset> IdleAnim;
	UPROPERTY(Transient) TObjectPtr<UAnimationAsset> WalkAnim;
	float WalkSpeed = 140.f, ClipSpeed = 140.f;
	FRandomStream R;
	TArray<FVector> Path;      // world points (tile centres)
	FVector Goal = FVector::ZeroVector;
	float WaitTime = 1.f;
	float StuckTime = 0.f;
	FVector LastPos = FVector::ZeroVector;
	bool bWalkingAnim = false;
	void PickTrip();
	void SetWalkingAnim(bool bWalk);
};
