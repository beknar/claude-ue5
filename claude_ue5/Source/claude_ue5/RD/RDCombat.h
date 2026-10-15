// random_dungeoncombat_level: the player's side of the fighting. The dungeon generator (bCombat) puts this component on
// the player pawn when play begins. It carries the three melee weapons of the generator's Weapons list (a mesh in her
// right hand, for some a shield on her left arm), her hit points and what each weapon does:
//   1 / 2 / 3 (D-pad left / up / right)   draw that weapon
//   left mouse button (X or RT)           attack: one of the weapon's attack clips is played over her locomotion as a
//                                          dynamic montage; at the clip's hit time every monster within the weapon's
//                                          reach and arc in front of her takes the weapon's damage
// Monsters hit her through ApplyDamage. Out of a fight her hit points come back slowly; at 0 she falls, and stands up
// again in the middle of the start section with full hit points. Tests and the demo reel drive the same functions
// (SetScriptedOnly keeps the real keys out).
// What is heard of her comes from here too (the generator's Sounds "Player.*"): a footstep for every stride on the
// ground (walking and running have their own sets; nothing else is heard of her moving), the swing and her effort,
// the weapon landing, her voice when she is hurt or falls. A blow she takes throws
// blood from her (the generator's URDBloodComponent).
// A weapon may be a spell (FRDWeaponDef::bSpell, random_dungeonmagic_level): the cast clip plays the same way, a charge
// burns on her hand until the release, and at the hit time a bolt leaves the hand and flies after the monster she
// turned to (one in front of her within the spell's reach that she can see); it bursts on the first monster or wall it
// meets. E casts it too (the left hand stays on WASD). Sounds "Player.Charge.<spell>", "Player.Cast.<spell>",
// "Player.Hit.<spell>" (the burst).
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "RDTypes.h"
#include "RDCombat.generated.h"

class ARDDungeonGenerator;
class ARDMonster;
class UStaticMeshComponent;
class USkeletalMeshComponent;
class UFXSystemComponent;
class UFXSystemAsset;
class UPointLightComponent;

UCLASS(ClassGroup = (RandomDungeon))
class CLAUDE_UE5_API URDCombatComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	URDCombatComponent();
	void Init(ARDDungeonGenerator* InGenerator);

	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 Kills = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 AttacksMade = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 HitsLanded = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 HitsTaken = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 Deaths = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") float DamageDealt = 0.f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") float DamageTaken = 0.f;

	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void SelectWeapon(int32 Index);
	/** false while another attack is still going, or she is down */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") bool StartAttack();
	/** an attack with that weapon of the generator's list (the drawn one, or a spell cast alongside it) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") bool StartAttackWith(int32 Index);
	/** the spell cast alongside the drawn weapon (FRDWeaponDef::bAlongside): what the right mouse button and E do */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") bool StartSpell();
	/** the weapon of the attack going on (-1: none) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") int32 GetAttackIndex() const { return AttackTime >= 0.f ? AttackIndex : -1; }
	/** the generator's index of the spell cast alongside (-1: none) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") int32 GetAlongsideSpell() const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void ApplyDamage(float Amount, AActor* From);
	/** full hit points, standing in the middle of the start section */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void Revive(bool bToStart = true);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void SetScriptedOnly(bool bOnly) { bScriptedOnly = bOnly; }
	/** tests: a key pressed (or let go) as if on the keyboard, through her player controller: the input mapping, her
	 *  movement and the combat keys read it as a real press. It stays down until it is let go. */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") bool SimulateKey(FKey Key, bool bDown);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetHealth() const { return Health; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetMaxHealth() const { return MaxHealth; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") bool IsDead() const { return bDead; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") bool IsAttacking() const { return AttackTime >= 0.f; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") int32 GetWeaponIndex() const { return WeaponIndex; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") FName GetWeaponName() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetWeaponDamage() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetWeaponReach() const;
	/** seconds of the running attack (-1: none) and its length */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetAttackTime() const { return AttackTime; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetAttackLength() const { return AttackLen; }
	/** the weapon in her hand (and the shield), for tests */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") UStaticMeshComponent* GetWeaponMesh() const { return WeaponComp; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") UStaticMeshComponent* GetOffHandMesh() const { return OffHandComp; }
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 StepsTaken = 0;
	/** spells: bolts cast, bolts that burst (on a monster / on a wall or at the end of their reach) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 BoltsCast = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 BoltsOnMonsters = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 BoltsElsewhere = 0;
	/** where the last bolt left her hand and where it burst, how far it flew (cm) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") FVector LastBoltFrom = FVector::ZeroVector;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") FVector LastBurstAt = FVector::ZeroVector;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") float LastBoltFlown = 0.f;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") bool IsSpell() const;
	/** bolts in the air now, and where (tests, the reel's record) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") TArray<FVector> GetBolts() const;
	/** the monster she turned to for the last attack (none: nothing in reach) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") ARDMonster* GetLastTarget() const { return LastTarget.Get(); }
	/** particles alive now in the spells' effects (charge, bolts, bursts) within Radius of Location (0: anywhere), and in
	 *  how many systems: what is seen, for tests (a count a frame old) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") int32 GetSpellParticles(FVector Location, float Radius, int32& Systems) const;
	/** the charge on her hand burns now */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") bool IsCharging() const;
	/** world time she was last hurt / last hit something (HUD) */
	float LastHurtTime = -100.f, LastHitTime = -100.f, DeathTime = -100.f;

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	UPROPERTY(Transient) TObjectPtr<ARDDungeonGenerator> Generator;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> WeaponComp;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> OffHandComp;
	float Health = 100.f, MaxHealth = 100.f;
	int32 WeaponIndex = -1, AttackIndex = -1;
	/** per weapon: which of its attack clips comes next */
	TArray<int32> NextOf;
	float AttackTime = -1.f, AttackLen = 0.f, AttackHit = 0.f, SavedWalkSpeed = 0.f;
	bool bHitDone = false, bDead = false, bScriptedOnly = false, bSlowed = false;
	float StaggerUntil = -100.f;
	// sound
	float StepDist = 0.f;
	bool bWhooshDone = false, bFallDone = false;
	void TickSounds(float Dt, float Now);
	const FRDWeaponDef* Weapon() const;
	/** the weapon of the attack going on (the drawn one when there is none) */
	const FRDWeaponDef* AttackWeapon() const;
	USkeletalMeshComponent* Body() const;
	void Strike();
	void EndAttack();
	void SetSlowed(bool bSlow);
	// ---- spells
	struct FBolt
	{
		FVector At = FVector::ZeroVector, Vel = FVector::ZeroVector;
		TWeakObjectPtr<ARDMonster> Target;
		TWeakObjectPtr<UFXSystemComponent> Fx, Core;
		TWeakObjectPtr<UPointLightComponent> Light;
		float Flown = 0.f;
		int32 Weapon = 0;
	};
	TArray<FBolt> Bolts;
	TWeakObjectPtr<ARDMonster> LastTarget;
	UPROPERTY(Transient) TObjectPtr<UFXSystemComponent> ChargeComp;
	/** every effect / light component the spells made (kept from the garbage collector; finished ones are dropped) */
	UPROPERTY(Transient) TArray<TObjectPtr<USceneComponent>> SpellComps;
	struct FFlash { TWeakObjectPtr<UPointLightComponent> Light; float Age = 0.f; float Peak = 0.f; };
	TArray<FFlash> Flashes;
	/** effects to stop after a while (the burst's flames) */
	struct FTimedFx { TWeakObjectPtr<UFXSystemComponent> Fx; float Left = 0.f; };
	TArray<FTimedFx> TimedFx;
	UFXSystemComponent* SpawnFx(UFXSystemAsset* Asset, const FVector& At, const FRotator& Rot, float Scale, USceneComponent* AttachTo = nullptr, FName Socket = NAME_None);
	UPointLightComponent* MakeLight(const FVector& At, const FLinearColor& Color, float Intensity, float Radius);
	ARDMonster* PickTarget(float Reach, bool bNeedSight) const;
	bool CanSee(const FVector& From, const AActor* Target) const;
	void LaunchBolt();
	void TickBolts(float Dt);
	void Burst(FBolt& B, const FVector& At, ARDMonster* Direct);
	void StopCharge();
};
