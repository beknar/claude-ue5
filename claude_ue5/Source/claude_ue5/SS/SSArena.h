// starship_level: the combat area. A cube of HalfExtent around this actor (5 km x 5 km x 5 km); the fighter is turned
// back when it leaves it. In play the arena spawns the destructible targets (asteroid fields, cargo containers, target
// drones in waves) from its data, keeps the list the fighter locks on to, plays explosions and keeps the score. The
// station and the large clutter are ordinary level actors (pipeline/unreal/801).
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SS/SSTypes.h"
#include "SSArena.generated.h"

class ASSTarget;
class UNiagaraSystem;
class UParticleSystem;
class UMaterialInterface;
class UStaticMesh;

UCLASS()
class CLAUDE_UE5_API ASSArena : public AActor
{
	GENERATED_BODY()

public:
	ASSArena();

	/** half the side of the combat cube (cm) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Area") float HalfExtent = 250000.f;
	/** the HUD warns this far before the edge */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Area") float WarnMargin = 30000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Area") int32 Seed = 8402;

	// ---- destructible targets
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Targets") TArray<TObjectPtr<UStaticMesh>> AsteroidMeshes;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Targets") TArray<TObjectPtr<UStaticMesh>> ContainerMeshes;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Targets") TArray<FSSField> Fields;
	/** nothing is spawned inside these (the station, the large clutter, the start) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Targets") TArray<FSSSphere> KeepOut;
	/** asteroids of at least this radius break into smaller ones */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Targets") float SplitMinRadius = 700.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Targets") float HealthPerMeter = 9.f;

	// ---- target drones
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Drones") TArray<FSSDroneDef> DroneTypes;
	/** drones circle inside these volumes */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Drones") TArray<FSSSphere> Patrols;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Drones") int32 DroneCount = 12;
	/** a destroyed drone is replaced after this many seconds */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Drones") float DroneRespawnDelay = 10.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Drones") TObjectPtr<UNiagaraSystem> DroneTrailFX;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Drones") TObjectPtr<UParticleSystem> DroneTrailPS;

	// ---- effects
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Effects") TObjectPtr<UNiagaraSystem> ExplosionFX;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Effects") TObjectPtr<UParticleSystem> ExplosionPS;
	/** size (cm) the explosion effects were authored for: they are scaled by blast radius / this */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Effects") float ExplosionFXSize = 300.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Effects") TObjectPtr<UNiagaraSystem> ImpactFX;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Effects") TObjectPtr<UParticleSystem> ImpactPS;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Effects") float ImpactFXScale = 3.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Effects") TObjectPtr<UStaticMesh> BlastMesh;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Effects") TObjectPtr<UMaterialInterface> BlastMaterial;

	// ---- play state
	UPROPERTY(BlueprintReadOnly, Category = "Starship") int32 Score = 0;
	UPROPERTY(BlueprintReadOnly, Category = "Starship") int32 AsteroidsDestroyed = 0;
	UPROPERTY(BlueprintReadOnly, Category = "Starship") int32 DronesDestroyed = 0;
	UPROPERTY(BlueprintReadOnly, Category = "Starship") int32 ContainersDestroyed = 0;

	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") bool IsInside(const FVector& P, float Margin = 0.f) const;
	/** how far P is outside the cube (0 inside) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") float DistanceOutside(const FVector& P) const;
	/** distance from P to the nearest face, positive inside */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") float DistanceToEdge(const FVector& P) const;
	UFUNCTION(BlueprintCallable, Category = "Starship") TArray<ASSTarget*> GetTargets() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") int32 CountTargets(ESSTargetKind Kind) const;
	/** the live target closest to the line from Origin along Dir, within MaxAngle degrees and MaxDist; Not is skipped */
	UFUNCTION(BlueprintCallable, Category = "Starship") ASSTarget* PickTarget(const FVector& Origin, const FVector& Dir, float MaxAngle, float MaxDist, const ASSTarget* Not = nullptr, bool bDronesFirst = true) const;
	/** fireball, flash and the level's explosion effect; Radius in cm */
	UFUNCTION(BlueprintCallable, Category = "Starship") void Blast(const FVector& Location, float Radius, FLinearColor Color = FLinearColor(1.f, 0.55f, 0.2f, 1.f));
	UFUNCTION(BlueprintCallable, Category = "Starship") void Sparks(const FVector& Location, const FVector& Normal, float Scale = 1.f);
	/** damages every target within Radius (full damage at the centre, a third at the edge) */
	UFUNCTION(BlueprintCallable, Category = "Starship") int32 RadialDamage(const FVector& Location, float Radius, float Damage, bool bByPlayer = true);
	/** removes every target and spawns them all again from the seed, the score back to 0: the same start whenever it
	 *  is called (a demo reel's pilot calls it on the first frame, so that every render of the reel is the same flight) */
	UFUNCTION(BlueprintCallable, Category = "Starship") void Restart();
	/** spawn one more drone now (waves, tests) */
	UFUNCTION(BlueprintCallable, Category = "Starship") ASSTarget* SpawnDrone();

	void Register(ASSTarget* T) { Targets.AddUnique(T); }
	void Unregister(ASSTarget* T) { Targets.Remove(T); }
	void OnTargetDestroyed(ASSTarget* T, bool bByPlayer);
	const TArray<TObjectPtr<ASSTarget>>& AllTargets() const { return Targets; }

	virtual void Tick(float Dt) override;

protected:
	virtual void BeginPlay() override;

private:
	UPROPERTY(Transient) TArray<TObjectPtr<ASSTarget>> Targets;
	FRandomStream R;
	TArray<float> DroneRespawns;
	int32 DroneSerial = 0;

	ASSTarget* SpawnTarget(ESSTargetKind Kind, UStaticMesh* Mesh, const FVector& Loc, float Size, const FRotator& MeshRot = FRotator::ZeroRotator);
	void SpawnField(const FSSField& F);
	void Populate();
	bool Blocked(const FVector& P, float Pad) const;
};
