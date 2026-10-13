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
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "RDTypes.h"
#include "RDCombat.generated.h"

class ARDDungeonGenerator;
class ARDMonster;
class UStaticMeshComponent;
class USkeletalMeshComponent;

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
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void ApplyDamage(float Amount, AActor* From);
	/** full hit points, standing in the middle of the start section */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void Revive(bool bToStart = true);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void SetScriptedOnly(bool bOnly) { bScriptedOnly = bOnly; }
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
	/** world time she was last hurt / last hit something (HUD) */
	float LastHurtTime = -100.f, LastHitTime = -100.f, DeathTime = -100.f;

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	UPROPERTY(Transient) TObjectPtr<ARDDungeonGenerator> Generator;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> WeaponComp;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> OffHandComp;
	float Health = 100.f, MaxHealth = 100.f;
	int32 WeaponIndex = -1, NextAttack = 0;
	float AttackTime = -1.f, AttackLen = 0.f, AttackHit = 0.f, SavedWalkSpeed = 0.f;
	bool bHitDone = false, bDead = false, bScriptedOnly = false, bSlowed = false;
	float StaggerUntil = -100.f;
	const FRDWeaponDef* Weapon() const;
	USkeletalMeshComponent* Body() const;
	void Strike();
	void EndAttack();
	void SetSlowed(bool bSlow);
};
