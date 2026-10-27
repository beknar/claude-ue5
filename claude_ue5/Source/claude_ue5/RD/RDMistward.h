// mistward_castle (docs/improvements.txt, pipeline/unreal/863-): the things the rules of 2026-10-26 put in the dungeon.
//   ARDLootPile    what she carried, dropped where she fell: a picture of each thing over it (the interface's icons,
//                  on camera-facing billboards) and a Loot Drops Vol. 2 effect; F takes it all up again
//   ARDTeleporter  a teleporter pad (the first tier's in the great hall, one in each tier's first set of rooms with that
//                  tier's teleport ring lying on it until she takes it)
//   ARDPrisoner    someone locked in a prison cell (the NPC packs): idle until she opens the cell, then thanks her, gives
//                  her something, walks out and is gone
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RDTypes.h"
#include "RDMistward.generated.h"

class ARDDungeonGenerator;
class ARDSection;
class UStaticMeshComponent;
class USkeletalMeshComponent;
class UMaterialBillboardComponent;
class UFXSystemComponent;
class UFXSystemAsset;
class UNiagaraComponent;
class UPointLightComponent;

/** an effect at a place or on a component (a Niagara system or a Cascade one); bUserScale: the magic packs' User.Scale.
 *  The castle's effects (traps, the torch, piles, pads); a spell's go through URDCombatComponent::SpawnSpellFx (its colours). */
CLAUDE_UE5_API UFXSystemComponent* RDMSpawnFx(UObject* Ctx, UFXSystemAsset* Asset, const FVector& At, const FRotator& Rot, float Scale, USceneComponent* AttachTo, bool bUserScale, bool bAutoDestroy);
/** the live particles of a Niagara component (0 with no system instance): the tests' "is the effect alive" */
CLAUDE_UE5_API int32 RDNiagaraParticles(const UNiagaraComponent* C);

UCLASS()
class CLAUDE_UE5_API ARDLootPile : public AActor
{
	GENERATED_BODY()
public:
	ARDLootPile();
	/** what is in it (the generator's Items by name; repeated for counts) and, for each, what is left of its durability
	 *  (-1: none) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") TArray<FName> Things;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") TArray<float> Wear;
	/** pictures drawn over it (tests) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") int32 Pictures = 0;
	/** her own things (she fell here); false: something the rules laid on the floor (a guarded ring in a room whose containers
	 *  she had all opened) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") bool bHers = true;
	void Init(ARDDungeonGenerator* InGenerator, const TArray<FName>& InThings, const TArray<float>& InWear);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") int32 GetNumThings() const { return Things.Num(); }
	/** the effect on it is alive (particles a frame old, tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") int32 GetEffectParticles() const;
	/** where picture I hangs over the pile at time T (rings of twelve) */
	FVector IconPlace(int32 I, float T) const;
protected:
	virtual void Tick(float Dt) override;
private:
	UPROPERTY() TObjectPtr<USceneComponent> Root;
	UPROPERTY() TObjectPtr<UFXSystemComponent> Fx;
	UPROPERTY() TArray<TObjectPtr<UMaterialBillboardComponent>> Icons;
	UPROPERTY() TObjectPtr<UPointLightComponent> Light;
	float Age = 0.f;
};

UCLASS()
class CLAUDE_UE5_API ARDTeleporter : public AActor
{
	GENERATED_BODY()
public:
	ARDTeleporter();
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") int32 Tier = 1;
	void Init(ARDDungeonGenerator* InGenerator, int32 InTier, bool bWithRing);
	/** the tier's ring lies on it (until she takes it) */
	void ShowRing(bool bShow);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool HasRing() const { return bRing; }
protected:
	virtual void Tick(float Dt) override;
private:
	UPROPERTY() TObjectPtr<USceneComponent> Root;
	UPROPERTY() TObjectPtr<UStaticMeshComponent> Pad;
	UPROPERTY() TObjectPtr<UStaticMeshComponent> Ring;
	UPROPERTY() TObjectPtr<UFXSystemComponent> Fx;
	UPROPERTY() TObjectPtr<UPointLightComponent> Light;
	bool bRing = false;
	float Age = 0.f;
};

UCLASS()
class CLAUDE_UE5_API ARDPrisoner : public AActor
{
	GENERATED_BODY()
public:
	ARDPrisoner();
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") FString Title;
	/** 0 waiting in the cell, 1 thanking her, 2 walking out, 3 fading, 4 gone */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") int32 State = 0;
	void Init(const FRDPrisonerDef& Def, const FVector& Doorway, const FVector& Exit, const FVector& Away);
	/** the cell is opened: thanks, then out and away */
	void Free();
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") bool IsFreed() const { return State > 0; }
	USkeletalMeshComponent* GetBody() const { return Body; }
protected:
	virtual void Tick(float Dt) override;
private:
	UPROPERTY() TObjectPtr<USceneComponent> Root;
	UPROPERTY() TObjectPtr<USkeletalMeshComponent> Body;
	UPROPERTY(Transient) TObjectPtr<UAnimationAsset> IdleAnim;
	UPROPERTY(Transient) TObjectPtr<UAnimationAsset> WalkAnim;
	UPROPERTY(Transient) TObjectPtr<UAnimationAsset> ThanksAnim;
	FVector DoorAt = FVector::ZeroVector, ExitAt = FVector::ZeroVector, AwayAt = FVector::ZeroVector;
	int32 Leg = 0;
	float Speed = 120.f, ClipSpeed = 120.f, StateTime = 0.f;
};
