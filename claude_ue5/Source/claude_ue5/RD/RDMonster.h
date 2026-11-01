// random_dungeon_level: a wandering monster. Picks a random room of its section, walks there over the section's tile grid
// (hallways, doorways, free floor; doors on the way are pushed open and close again behind it), idles a while, repeats.
// No controller: CharacterMovement runs without one, the clips (idle / walk) play directly on the mesh.
// random_dungeoncombat_level (the generator's bCombat): it has hit points and does damage. When the player comes near
// and there is a way to her it gives chase over the same tile grid, attacks when she is in reach (one of its attack
// clips; the blow lands at the clip's hit time if she is still there), flinches when hit and dies at 0 hit points (its
// death clip; the body stays a while and no longer blocks). Its hit points and damage are the player's, scaled by the
// tier of its section (weaker in the start section) and by its kind.
// A blow leaves a wound on this monster only: the mesh vertex nearest to the weapon (on the attacker's side) is found
// with the pose as it is, and its place in the reference pose goes into this monster's own instance of the generator's
// WoundMaterial, laid over its mesh (an overlay material: the pack's materials stay as they are); the wound stays on
// the skin as the monster moves, and blood runs down from it as its hit points go. Its voice and footsteps are the
// generator's Sounds "Monster.<SoundSet>.*", played where it is.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "RDTypes.h"
#include "RDMonster.generated.h"

class ARDSection;
class UMaterialInstanceDynamic;

UCLASS()
class CLAUDE_UE5_API ARDMonster : public ACharacter
{
	GENERATED_BODY()

public:
	ARDMonster();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") TObjectPtr<ARDSection> Section;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") FName MonsterName;
	/** its place in the order its section spawns monsters in (a section generated again skips the ones she killed) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") int32 SpawnIndex = -1;
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
	/** the same, struck at a known point (a spell's bolt): the wound goes there */
	bool ApplyDamageAt(float Amount, AActor* From, const FVector* At);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetHealth() const { return Health; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetMaxHealth() const { return MaxHealth; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetDamage() const { return Damage; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool IsDead() const { return bDead; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool IsAggro() const { return bAggro; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool IsAttacking() const { return AttackTime >= 0.f; }
	/** world time it was last hurt (HUD: its bar shows for a while) */
	float LastHurtTime = -100.f;
	/** the same as ApplyDamageAt; a burn or a cloud's hurt neither makes it flinch nor wounds it */
	bool ApplyDamageEx(float Amount, AActor* From, const FVector* At, bool bFlinch, bool bWound);

	// ---- random_dungeonmagic_level5
	/** the tier of rooms it was spawned in, its ability and how strong (the generator's TierAbility) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") int32 Tier = 1;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") ERDMonsterAbility Ability = ERDMonsterAbility::None;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") float AbilityPower = 0.f;
	/** the gallery's name (the HUD's bar) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") FString Title;
	/** a corpse that stays (the generator's bKeepCorpses): dead, lying where it fell */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool IsCorpse() const { return bDead && bCorpse; }
	/** a section generated again lays the one she killed there: dead at once, at the end of its death clip, silent */
	void LayDead();
	/** it fights on her side for Seconds (0: until it falls), with these hit points and damage (a corpse rises first) */
	void BecomeAlly(float Seconds, float InHealth, float InDamage);
	/** mistward4 (bAllySpacing): the way and strength (0 none; about 1 standing in another) her ally steps to keep clear of
	 *  her other allies and of her (RDMistward4.cpp) */
	FVector AllySpacingPush() const;
	/** the way to move along Dir with that push: its part against Dir taken out (an ally queuing behind another was turned
	 *  back from its foe, the PR review's find), the rest added; Dir itself when there is none */
	FVector AllySteer(const FVector& Dir) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool IsAlly() const { return bAlly; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetAllyTimeLeft() const { return AllySeconds > 0.f ? AllyLeft : 0.f; }
	void SetChampion(bool b) { bChampion = b; }
	/** mistward_castle (the Summoner): the Summon spell that brought it to her side (none: it was not summoned so) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") FName SummonSpell;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool IsChampion() const { return bChampion; }
	/** the spells' hold on it: slowed (a share of its speed) for Seconds, a burn (hit points a second, a share of it back to
	 *  her), a curse (it takes Share more and deals Share less), a push, a pull toward a point */
	void SlowFor(float Share, float Seconds);
	void AddBurn(float PerSecond, float Seconds, float DrainShare);
	void CurseFor(float Share, float Seconds);
	void Knock(const FVector& Velocity);
	void PullToward(const FVector& To, float Speed, float Dt);
	/** the third list's slashes: blinded (Share of its blows miss) for Seconds; held (stunned) for Seconds */
	void BlindFor(float Share, float Seconds);
	void StunFor(float Seconds);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetBlindShare() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool IsStunned() const { return Stun > 0.f && bStunHeld; }
	/** blows it swung that missed for its blindness (tests) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") int32 BlindMisses = 0;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetSlowShare() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetCurseShare() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool IsBurning() const { return Burns.Num() > 0; }
	/** walking speed now (its kind's, by its tier, slowed) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetWalkSpeed() const { return WalkSpeed; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetAttackInterval() const { return AttackInterval; }
	/** the one it fights now (none: nobody) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") AActor* GetFoe() const { return CurrentFoe.Get(); }

	// ---- mistward_castle
	/** as strong as a monster of tier InTier, times the multipliers, bigger by ScaleMul; its bar's name (a boss, a guard) */
	void Empower(int32 InTier, float HealthMul, float DamageMul, float ScaleMul, const FString& InTitle);
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") bool bBoss = false;
	/** locked in a prison cell: it waits there, unseen by the fight, until the cell is opened */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") bool bCaged = false;
	/** out of its cell: to Doorway (inside, in front of the door's gap), out to Exit (in front of the cell), then at her */
	void Release(const FVector& Doorway = FVector::ZeroVector, const FVector& Exit = FVector::ZeroVector);
	FVector CellDoorway = FVector::ZeroVector;
	FVector CellExit = FVector::ZeroVector;
	float ReleasedUntil = -1.f;
	/** the lowest point of its body as it is drawn now (its skinned vertices), against the bottom of its capsule (cm):
	 *  under 0 it is in the floor, over 0 it floats */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") float GetDrawnBottom(float Percentile = 0.01f, bool bBodyOnly = true) const;

	// ---- mistward5 (the list of 2026-10-31b; RDMistward5.cpp): a shot from afar
	/** its kind shoots (the generator's bMonsterRanged on) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool CanShoot() const { return bShoots; }
	/** shots it let fly, and its shot's damage now (its blow's times its kind's share, a curse taken off) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") int32 ShotsFired = 0;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetShotDamage() const;
	/** seconds between two shots, and before the next */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetShotWait() const { return RangedWait; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetShotWaitLeft() const { return RangedWaitLeft; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool IsShooting() const { return AttackTime >= 0.f && bRangedSwing; }
	/** the world time of its last shot's release (-100: none) */
	float LastShotTime = -100.f;

	// ---- wounds
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") int32 GetNumWounds() const { return Wounds.Num(); }
	/** where a wound is now (world), and its size (cm) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") FVector GetWoundLocation(int32 Index) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetWoundRadius(int32 Index) const { return Wounds.IsValidIndex(Index) ? Wounds[Index].Radius : 0.f; }
	/** true when the wound sits on a vertex of the mesh (false: only on its nearest bone) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool IsWoundOnSkin(int32 Index) const { return Wounds.IsValidIndex(Index) && Wounds[Index].Vertex >= 0; }
	/** this monster's own wound material (none until it is hit) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") UMaterialInstanceDynamic* GetWoundMaterial() const { return WoundMID; }

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
	// level 5: corpses, allies, the spells' hold
	bool bCorpse = false, bFrozen = false, bAlly = false, bChampion = false;
	float AllySeconds = 0.f, AllyLeft = 0.f, SpeedScale = 1.f, MaxChaseScale = 1.f;
	float SlowShare = 0.f, SlowUntil = -100.f, CurseShare = 0.f, CurseUntil = -100.f, BurnAcc = 0.f, BurnTick = 0.f, FreezeAt = 0.f;
	float BlindShare = 0.f, BlindUntil = -100.f;
	bool bStunHeld = false;
	int32 Swings = 0;
	// mistward5: its shot (FRDMonsterDef's Ranged*)
	bool bShoots = false, bRangedSwing = false;
	float RangedRange = 800.f, RangedMin = 300.f, RangedShare = 0.5f, RangedWait = 4.f, RangedWaitLeft = 0.f, RangedSpeed = 1500.f, RangedRelease = 0.5f, RangedFxScale = 1.f;
	UPROPERTY(Transient) TObjectPtr<UAnimationAsset> RangedClip;
	UPROPERTY(Transient) TObjectPtr<UFXSystemAsset> RangedFx;
	UPROPERTY(Transient) TObjectPtr<UFXSystemAsset> RangedMuzzleFx;
	UPROPERTY(Transient) TObjectPtr<UFXSystemAsset> RangedHitFx;
	FString RangedTheme;
	FVector ShotAim = FVector::ZeroVector;
	void SetupRanged(const FRDMonsterDef& Def);
	/** where its shot leaves it (in front of its chest) */
	FVector ShotMuzzle() const;
	/** a shot begun at its foe (P), out of reach of its blows and in its range with a sight line: true when it stands to shoot */
	bool TryShoot(AActor* P, const FVector& D, float Dist, float Dz, float Gap, float Dt);
	void ReleaseShot(AActor* P);
	struct FBurn { float PerSecond = 0.f; float Left = 0.f; float Drain = 0.f; };
	TArray<FBurn> Burns;
	TWeakObjectPtr<AActor> CurrentFoe;
	void TickStatus(float Dt);
	float SpeedMul() const { return 1.f - GetSlowShare(); }
	/** the one to fight: hers (her, or an ally of hers nearer), or for an ally of hers the nearest monster near her */
	AActor* PickFoe(class URDCombatComponent* Pc, bool& bFoePlayer) const;
	/** an ally with nobody to fight keeps near her */
	bool FollowPlayer(float Dt, class URDCombatComponent* Pc);
	void Freeze();
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
	// wounds
	struct FWound { FVector3f Ref = FVector3f::ZeroVector; float Radius = 10.f; int32 Vertex = -1; FName Bone; };
	static constexpr int32 MaxWounds = 10;
	TArray<FWound> Wounds;
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> WoundMID;
	/** a wound where the weapon (Strike, world) met it, on the side of From; Share = the blow's part of its hit points. Returns where it is. */
	FVector AddWound(const FVector& Strike, const FVector& From, float Share);
	void PushWounds();
	// sound
	FName SndStep, SndHurt, SndRoar, SndAttack, SndDeath, SndIdle;
	FRandomStream SR;        // (sound and blood only: never the play)
	float StepLength = 80.f, StepDist = 0.f, VoiceTimer = 4.f, RoarTime = -100.f, DripTimer = 0.f;
	FVector StepPos = FVector::ZeroVector;
	bool bBodyDown = false;
	void TickSounds(float Dt);
	void Roar();
};
