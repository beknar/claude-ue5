// starship_level: things that can be shot. ASSTarget is an asteroid, a cargo container or a target drone (one pack
// mesh; drones fly patrol circles, the rest drift and tumble); big asteroids break into smaller ones. ASSBlast is the
// flash of an explosion (a light and a glowing sphere that fade), played together with the level's explosion effect.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SS/SSTypes.h"
#include "SSTarget.generated.h"

class ASSArena;
class UNiagaraComponent;
class UParticleSystemComponent;
class UPointLightComponent;
class UStaticMeshComponent;
class UMaterialInstanceDynamic;

UCLASS()
class CLAUDE_UE5_API ASSTarget : public AActor
{
	GENERATED_BODY()

public:
	ASSTarget();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Starship") TObjectPtr<USceneComponent> Root;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Starship") TObjectPtr<UStaticMeshComponent> Mesh;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Starship") TObjectPtr<UNiagaraComponent> Trail;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Starship") TObjectPtr<UParticleSystemComponent> TrailPS;

	UPROPERTY(BlueprintReadOnly, Category = "Starship") ESSTargetKind Kind = ESSTargetKind::Asteroid;
	UPROPERTY(BlueprintReadOnly, Category = "Starship") float Health = 50.f;
	UPROPERTY(BlueprintReadOnly, Category = "Starship") float MaxHealth = 50.f;
	UPROPERTY(BlueprintReadOnly, Category = "Starship") int32 Points = 10;
	/** how many more times it breaks into smaller pieces when destroyed (asteroids) */
	UPROPERTY(BlueprintReadOnly, Category = "Starship") int32 SplitsLeft = 0;
	UPROPERTY(BlueprintReadOnly, Category = "Starship") FName TypeName;

	void Setup(ASSArena* InArena, ESSTargetKind InKind, UStaticMesh* InMesh, const FRotator& MeshRotation, float Scale, float InHealth, int32 InPoints);
	void SetDrift(const FVector& InVelocity, const FRotator& InSpin) { Drift = InVelocity; Spin = InSpin; }
	void SetPatrol(const FVector& Center, float Radius, const FVector& Axis, float Speed, float Phase);
	/** debris: no collision, not a target, gone after Seconds (it shrinks away) */
	void SetLifetime(float Seconds) { Lifetime = LifeLeft = Seconds; }
	/** returns true when this hit destroyed it */
	UFUNCTION(BlueprintCallable, Category = "Starship") bool ApplyHit(float Damage, bool bByPlayer = true);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") float GetRadius() const { return Radius; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") bool IsAlive() const { return !bDead; }
	virtual FVector GetVelocity() const override { return Vel; }

	virtual void Tick(float Dt) override;

protected:
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;

private:
	UPROPERTY(Transient) TObjectPtr<ASSArena> Arena;
	FVector Drift = FVector::ZeroVector, Vel = FVector::ZeroVector;
	FRotator Spin = FRotator::ZeroRotator;
	float Radius = 300.f;
	bool bDead = false;
	// patrol (drones)
	bool bPatrol = false;
	FVector PCenter = FVector::ZeroVector, PU = FVector::ForwardVector, PV = FVector::RightVector, PN = FVector::UpVector;
	float PRadius = 20000.f, PSpeed = 8000.f, PAngle = 0.f, Alarm = 0.f, Wobble = 0.f;
	float Lifetime = 0.f, LifeLeft = 0.f;
	FVector BaseScale = FVector::OneVector;
};

UCLASS()
class CLAUDE_UE5_API ASSBlast : public AActor
{
	GENERATED_BODY()

public:
	ASSBlast();
	UPROPERTY(VisibleAnywhere, Category = "Starship") TObjectPtr<UPointLightComponent> Light;
	UPROPERTY(VisibleAnywhere, Category = "Starship") TObjectPtr<UStaticMeshComponent> Ball;
	/** Size: radius of the fireball in cm; Material: an unlit additive material with a scalar "Alpha" and a vector "Color" */
	void Start(float Size, UStaticMesh* BallMesh, UMaterialInterface* Material, const FLinearColor& Color, float Seconds);
	virtual void Tick(float Dt) override;

private:
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> MID;
	float Size = 1000.f, Age = 0.f, Life = 0.7f, Peak = 1.f;
};
