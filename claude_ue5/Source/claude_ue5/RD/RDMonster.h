// random_dungeon_level: a wandering monster. Picks a random room of its section, walks there over the section's tile grid
// (hallways, doorways, free floor; doors on the way are pushed open and close again behind it), idles a while, repeats.
// No controller: CharacterMovement runs without one, the clips (idle / walk) play directly on the mesh.
// random_dungeoncombat_level (the generator's bCombat): it has hit points and does damage. When the player comes near
// and there is a way to her it gives chase over the same tile grid, attacks when she is in reach (one of its attack
// clips; the blow lands at the clip's hit time if she is still there), flinches when hit and dies at 0 hit points (its
// death clip; the body stays a while and no longer blocks). Its hit points and damage are the player's, scaled by the
// tier of its section (weaker in the start section) and by its kind.
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
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") int32 AttacksMade = 0;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") int32 HitsLanded = 0;

	void Setup(ARDSection* InSection, const FRDMonsterDef& Def, int32 InSeed);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") bool IsWalking() const { return Path.Num() > 0 && WaitTime <= 0.f; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") FVector GetGoal() const { return Goal; }

	// ---- fighting
	/** true when this killed it */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") bool ApplyDamage(float Amount, AActor* From);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetHealth() const { return Health; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetMaxHealth() const { return MaxHealth; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetDamage() const { return Damage; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool IsDead() const { return bDead; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool IsAggro() const { return bAggro; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool IsAttacking() const { return AttackTime >= 0.f; }
	/** world time it was last hurt (HUD: its bar shows for a while) */
	float LastHurtTime = -100.f;

protected:
	virtual void Tick(float DeltaSeconds) override;

private:
	UPROPERTY(Transient) TObjectPtr<UAnimationAsset> IdleAnim;
	UPROPERTY(Transient) TObjectPtr<UAnimationAsset> WalkAnim;
	UPROPERTY(Transient) TArray<TObjectPtr<UAnimationAsset>> AttackAnims;
	UPROPERTY(Transient) TObjectPtr<UAnimationAsset> GetHitAnim;
	UPROPERTY(Transient) TObjectPtr<UAnimationAsset> DeathAnim;
	float WalkSpeed = 140.f, ClipSpeed = 140.f;
	FRandomStream R;
	TArray<FVector> Path;      // world points (tile centres)
	FVector Goal = FVector::ZeroVector;
	float WaitTime = 1.f;
	float StuckTime = 0.f;
	FVector LastPos = FVector::ZeroVector;
	bool bWalkingAnim = false;
	// fighting
	bool bCombat = false, bDead = false, bAggro = false, bHitDone = false;
	float Health = 1.f, MaxHealth = 1.f, Damage = 0.f, Reach = 110.f, AttackInterval = 1.6f;
	float AttackTime = -1.f, AttackLen = 0.f, AttackHit = 0.f, AttackCooldown = 0.f, Stun = 0.f, DeadTime = 0.f, ChaseTimer = 0.f;
	TArray<float> HitTimes;
	void PickTrip();
	void SetWalkingAnim(bool bWalk);
	void SetPathFromTiles(const TArray<FIntPoint>& Tiles);
	/** a closed door between here and the next waypoint: pushes it open; true while it has to wait */
	bool WaitForDoor(const FVector& L, const FVector& Dir2);
	FIntPoint WalkableTileAt(const FVector& L) const;
	/** true when the fight took this frame (the wandering is skipped) */
	bool TickCombat(float Dt);
	void Face(const FVector& Dir, float Dt);
	void Die();
};
