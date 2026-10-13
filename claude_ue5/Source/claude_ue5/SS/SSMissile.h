// starship_level: the fighter's second weapon. A homing missile: it leaves the rail at the fighter's speed, accelerates,
// turns toward where its target will be and goes off on contact, next to the target or at the end of its fuel
// (blast damage to everything in range). Without a target it flies straight.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SSMissile.generated.h"

class ASSArena;
class ASSTarget;
class UNiagaraComponent;
class UNiagaraSystem;
class UParticleSystemComponent;
class UPointLightComponent;
class UStaticMeshComponent;

UCLASS()
class CLAUDE_UE5_API ASSMissile : public AActor
{
	GENERATED_BODY()

public:
	ASSMissile();

	UPROPERTY(VisibleAnywhere, Category = "Starship") TObjectPtr<USceneComponent> Root;
	UPROPERTY(VisibleAnywhere, Category = "Starship") TObjectPtr<UStaticMeshComponent> Mesh;
	UPROPERTY(VisibleAnywhere, Category = "Starship") TObjectPtr<UStaticMeshComponent> Flame;
	UPROPERTY(VisibleAnywhere, Category = "Starship") TObjectPtr<UNiagaraComponent> Trail;
	UPROPERTY(VisibleAnywhere, Category = "Starship") TObjectPtr<UParticleSystemComponent> TrailPS;
	UPROPERTY(VisibleAnywhere, Category = "Starship") TObjectPtr<UPointLightComponent> Glow;

	UPROPERTY(EditAnywhere, Category = "Starship") float MaxSpeed = 75000.f;
	UPROPERTY(EditAnywhere, Category = "Starship") float Acceleration = 70000.f;
	UPROPERTY(EditAnywhere, Category = "Starship") float TurnRate = 150.f;
	UPROPERTY(EditAnywhere, Category = "Starship") float Fuel = 9.f;
	/** it goes off this close to the surface of its target */
	UPROPERTY(EditAnywhere, Category = "Starship") float Proximity = 350.f;

	void Launch(ASSArena* InArena, AActor* InOwner, ASSTarget* InTarget, const FVector& InVelocity, float InDamage, float InBlastRadius);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") ASSTarget* GetTarget() const { return Target.Get(); }
	virtual FVector GetVelocity() const override { return Velocity; }
	virtual void Tick(float Dt) override;

private:
	UPROPERTY(Transient) TObjectPtr<ASSArena> Arena;
	TWeakObjectPtr<ASSTarget> Target;
	TWeakObjectPtr<AActor> Shooter;
	FVector Velocity = FVector::ZeroVector;
	float Age = 0.f, Damage = 100.f, BlastRadius = 2500.f;
	bool bDone = false;
	void Detonate(const FVector& At);
};
