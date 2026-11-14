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
class UFXSystemComponent;
class UStaticMesh;

/** a clip's length (s; 1 for none or not a sequence) */
float RDClipLength(const UAnimationAsset* A);

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
	/** the wilderness: its place id * 16 + its number in the group (-1 elsewhere), recorded when it dies */
	int64 WildKey = -1;
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
	/** new hit points' top and blow, its share of hit points kept, and with another tier its speed, blows' pace and ability as
	 *  that tier's (a summon grown as a tier opens); false if nothing changed */
	bool SetStrength(int32 InTier, float InMaxHealth, float InDamage);
	/** its hit points as a share of its top (a summon brought from the other level as hurt as it was) */
	void SetHealthShare(float Share) { if (!bDead) Health = FMath::Max(1.f, FMath::RoundToFloat(MaxHealth * FMath::Clamp(Share, 0.f, 1.f))); }
	/** the list of 2026-11-08b's sixth phase: an ally healed (the Summoner's healing, her soul harvest); its pace of blows (her
	 *  frenzy: its wait between blows divided by it) and a boost on its blows until a time (her soul harvest).
	 *  The list of 2026-11-11: a heal on a monster under Withering Brand is its share less (RDList11c.cpp) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|List11") void HealBy(float Amount);
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") float AllyPace = 1.f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") float AllyBoost = 1.f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") float AllyBoostUntil = -100.f;
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
	/** the list of 2026-11-12's seventh phase (the Rogue's arts, RDRogue12.cpp): it has lost her (the smoke: no foe of hers for
	 *  Seconds); marked (it takes Share more from her); exposed (its armour eaten: it takes Share more from everyone) */
	void LoseHerFor(float Seconds);
	void MarkFor(float Share, float Seconds);
	void ExposeFor(float Share, float Seconds);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool HasLostHer() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetMarkShare() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetExposedShare() const;
	float LostHerUntil = -100.f, MarkUntil = -100.f, MarkShare = 0.f, ExposedUntil = -100.f, ExposedShare = 0.f;
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

	// ---- the list of 2026-11-11 (RDList11c.cpp): the Warlock's curses and two slashes' marks on it
	/** one of the curses for Seconds: Amount its share (Rot: hit points a second), Element Ruin's, Group Kinship's binding */
	void Curse11(ERDCurseEffect E, float Seconds, float Amount, FName Element = NAME_None, int32 Group = -1);
	bool HasCurse11(ERDCurseEffect E) const;
	float CurseLeft11(ERDCurseEffect E) const;
	float CurseAmount11(ERDCurseEffect E) const;
	void EndCurse11(ERDCurseEffect E);
	/** tests: "<curse>|<seconds left>|<amount>|<more>" for each curse on it */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List11") TArray<FString> GetCurseLines() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List11") bool IsAfraid() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List11") bool IsSilenced() const;
	/** the Sunder and Weaken slashes: it takes Share more for Seconds; its blows Share weaker for Seconds */
	void SunderFor(float Share, float Seconds);
	void WeakenFor(float Share, float Seconds);
	/** its blow's factor (a curse, a weakening) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|List11") float BlowMul() const;
	/** a hold from her slashes and curses (the Quake Slash, Brittle Bones' knock-down) that keeps the final boss's poise: within
	 *  FinalBossPoise of his last flinch he shrugs it off (PR #48's review); whether it held */
	bool HoldFor11(float Seconds);
	/** any of the thirteen curses on it now (the HUD's mark, every frame: no lines built) */
	bool HasAnyCurse11() const;
	/** an elite (hell's, or past its tier's hit points by a quarter) or a boss */
	bool IsEliteOrBoss() const;
	/** tests: what its curses did (doubled blows, knockdowns, hit points given to her, hurt shared, doom's burst, executed) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List11") int32 CritsTaken = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List11") int32 KnockedDown = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List11") float LeechGiven = 0.f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List11") float KinShared = 0.f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List11") float DoomBurst = 0.f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List11") bool bDoomExecuted = false;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List11") int32 SilencedRefusals = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|List11") int32 CursesSpread = 0;
	/** the damage it takes, its curses' share in it (and what they do with it); after it, what follows from it */
	float CurseDamageIn(float Amount, AActor* From);
	void CurseAfterHit(float Amount);
	void CurseOnDeath();
	void TickCurses11(float Dt);
	/** afraid: a step away from her (true: the frame is taken) */
	bool TickFear(float Dt);
private:
	float C11Until[(int32)ERDCurseEffect::Count] = {};
	float C11Amount[(int32)ERDCurseEffect::Count] = {};
	FName RuinElement = NAME_None;
	int32 KinGroup = -1, CritRolls = 0;
	/** Curse of Rot: when each of its (up to) three poisons ends; a stack is free again once its poison has run out */
	float RotEnds[3] = { -100.f, -100.f, -100.f };
	int32 RotStacksNow() const;
	float DoomTaken = 0.f, DreadTaken = 0.f, SunderUntil = -100.f, SunderShare = 0.f, WeakenUntil = -100.f, WeakenShare = 0.f;
public:

	// ---- mistward_castle
	/** as strong as a monster of tier InTier, times the multipliers, bigger by ScaleMul; its bar's name (a boss, a guard) */
	void Empower(int32 InTier, float HealthMul, float DamageMul, float ScaleMul, const FString& InTitle);
	/** the list of 2026-11-11: the Escape menu's difficulty on its hit points and blows (Setup and Empower call it) */
	void ApplyDifficulty();
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") bool bHellElite = false;
	bool bDifficultyCounted = false;
	/** the factors the difficulty (and hell's elite) put on its hit points and blow (Raise Dead takes them off) */
	float DiffHealthMul = 1.f, DiffDamageMul = 1.f;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") bool bBoss = false;
	/** Brokenspire: the room of its section it keeps to (-1: none). It wanders only there, and takes no foe outside it: she
	 *  fights it in the room or walks out (the Mistward Hall's guards) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") int32 HomeRoom = -1;
	/** the wilderness (RDWildPlaces.cpp): no tile grid out here; it wanders round HomeAt, notices her by distance and
	 *  height alone, chases her straight, and gives up beyond WildLeash of its home */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") bool bOpenGround = false;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") FVector HomeAt = FVector::ZeroVector;
	/** the list of 2026-11-12's fourth phase (a lair hidden behind something): the cover's radius round HomeAt (cm; 0 none), in which
	 *  it wanders, and its way out (a point just outside its opening), through which it goes after her and comes home */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") float CoverR = 0.f;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") FVector CoverExit = FVector::ZeroVector;
	/** the cover's outer radius (cm: its farthest piece's reach), inside which it keeps to its opening */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") float CoverOutR = 0.f;
	/** the way round a lair's cover, outside its walls, from From's side to To's (none when they are on the same side) */
	void CoverRound(const FVector& From, const FVector& To, TArray<FVector>& Out) const;
	/** the list of 2026-11-10: an ambush's: it hunts her until HuntUntil (game seconds), from any distance under 150 m */
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "RandomDungeon") bool bHunting = false;
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "RandomDungeon") float HuntUntil = 0.f;
	float WildLeash = 6000.f;
	/** Brokenspire: the guard of the Mistward Hall it is (the game remembers which she killed) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") int32 GuardIndex = -1;
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

	// ---- mistward_castle's final boss (RDAurorim.cpp): levitating, a beam of light from above, wind round its fists
	/** the mesh's height over where it would stand (cm, its bob in), its beams called down, its fists' effects made, and the
	 *  effects round its fists now (tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetHoverNow() const { return HoverNow; }
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") int32 BeamsCast = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") int32 FistFxMade = 0;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") TArray<FString> GetFistFxLines() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool CanCallBeam() const { return bSkyBeam; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") float GetBeamWaitLeft() const { return BeamWaitLeft; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool IsCallingBeam() const { return AttackTime >= 0.f && bBeamSwing; }
	/** the final boss of its castle (the generator's FinalBossKind, set by it) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") bool bFinalBoss = false;
	/** made the final boss: its lance's and light's waits times WaitScale (the generator's FinalBossWaitScale) */
	void MakeFinalBoss(float WaitScale);
	/** his tactics (the generator's FinalBossHold...): seconds he held back circling her while his band fought, seconds he
	 *  stepped round her between his blows (tests, the showcase's done file) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") float HoldSeconds = 0.f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") float CircleSeconds = 0.f;
	/** what its fight did this tick (swing, reach, circle, beam, shoot, hold, chase, door, nopath, unseen, lost, home, stun, none):
	 *  tests read it when a monster stands still */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") FName CombatBranch;
	/** the final boss's poise: blows that would have made him flinch and did not (the generator's FinalBossPoise) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") int32 FlinchesShrugged = 0;
	float LastFlinchTime = -100.f;

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
	// the final boss (FRDMonsterDef's Hover*, RangedMesh*, Beam*, Fist*)
	float HoverHeight = 0.f, HoverBob = 0.f, HoverPeriod = 1.6f, HoverNow = 0.f, HoverTime = 0.f, BaseMeshZ = 0.f;
	UPROPERTY(Transient) TObjectPtr<UStaticMesh> RangedMesh;
	float RangedMeshScale = 1.f; FRotator RangedMeshRot = FRotator::ZeroRotator;
	bool bSkyBeam = false, bBeamSwing = false;
	float BeamMin = 400.f, BeamMax = 1400.f, BeamShare = 0.9f, BeamRadius = 220.f, BeamDelay = 0.9f, BeamWait = 6.f, BeamWaitLeft = 0.f, BeamRelease = 0.6f;
	float BeamFxScale = 1.f, BeamMarkScale = 1.f;
	bool bBeamFxUser = false, bBeamMarkUser = false, bBeamHitUser = false;
	TArray<bool> FistFxUser;
	UPROPERTY(Transient) TObjectPtr<UAnimationAsset> BeamClip;
	UPROPERTY(Transient) TObjectPtr<UFXSystemAsset> BeamFx;
	UPROPERTY(Transient) TObjectPtr<UFXSystemAsset> BeamMarkFx;
	UPROPERTY(Transient) TObjectPtr<UFXSystemAsset> BeamHitFx;
	UPROPERTY(Transient) TArray<TObjectPtr<UFXSystemAsset>> FistFx;
	TArray<float> FistFxScale; TArray<FName> FistBones;
	TArray<TWeakObjectPtr<UFXSystemComponent>> FistFxLive;
	void SetupBoss(const FRDMonsterDef& Def);
	/** the mesh raised over its capsule and bobbing (down on the floor once dead) */
	void TickHover(float Dt);
	/** a beam begun at its foe (P), in its range: true when it stands to call it down */
	bool TrySkyBeam(AActor* P, const FVector& D, float Dist, float Dz, float Gap, float Dt);
	void ReleaseBeam(AActor* P);
	void StartFistFx();
	void EndFistFx();
	/** the final boss holding back from its foe (P) while its band fights: circling at the generator's FinalBossHold, out of
	 *  its reach; true when it did (false: the chase brings it in) */
	bool TickFinalHold(AActor* P, const FVector& D, float Dist, float Dz, float Dt);
	/** a step round its foe between its blows (in reach) */
	void CircleStep(const FVector& D, float Gap, float Dt);
	/** the way round that is clear of walls and furniture (Dir's side flipped when not); false: neither is */
	bool CircleClear(FVector& Dir, const FVector& Fw, float In);
	/** the way round (1, -1), when it turns next, and this tick it steps sideways (its turn then not to where it moves) */
	float CircleSign = 1.f, CircleFlip = 0.f;
	bool bCircling = false;
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
