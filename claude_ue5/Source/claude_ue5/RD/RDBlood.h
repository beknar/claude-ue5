// random_dungeoncombat_level: blood. The dungeon generator (bCombat, with a BloodDropMesh) makes one of these on itself
// when play begins; the fighting code calls Burst where a blow lands. A burst is
//   drops    small stretched spheres (one instanced mesh for all of them) thrown out of the wound on ballistic paths;
//            each is traced against the dungeon and leaves a decal where it lands (floor, wall, furniture)
//   spray    a few camera-facing sprites that swell and fade in a third of a second (the mist of the splash)
// Pool puts a slowly spreading pool under a body. Decals fade after the generator's BloodDecalSeconds; the oldest go
// first when there are more than MaxBloodDecals. The component has its own random stream: blood never changes how a
// fight goes, and Clear() (the generator's RestartPlay) makes a demo reel's splashes repeat.
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "RDBlood.generated.h"

class ARDDungeonGenerator;
class UInstancedStaticMeshComponent;
class UDecalComponent;
class UMaterialInterface;

UCLASS(ClassGroup = (RandomDungeon))
class CLAUDE_UE5_API URDBloodComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	URDBloodComponent();
	void Init(ARDDungeonGenerator* InGenerator);

	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Gore") int32 Bursts = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Gore") int32 DropsSpawned = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Gore") int32 DecalsSpawned = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Gore") int32 PoolsSpawned = 0;
	/** where the last burst was, and when (tests, the demo reel's record) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Gore") FVector LastBurstAt = FVector::ZeroVector;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Gore") float LastBurstTime = -100.f;

	/** blood bursts out of At along Dir; Strength (0..1) scales the number of drops, their speed and the spray */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Gore") void Burst(FVector At, FVector Dir, float Strength);
	/** a pool that spreads on the floor under At */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Gore") void Pool(FVector At, float Size);
	/** a drop falling from At (a wounded monster on the move) */
	void Drip(const FVector& At);
	/** everything gone, the counters at 0, the random stream at its start */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Gore") void Clear();
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Gore") int32 GetActiveDrops() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Gore") int32 GetActiveSprays() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Gore") int32 GetActiveDecals() const;

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	struct FDrop { FVector P = FVector::ZeroVector, V = FVector::ZeroVector; float Size = 1.f, Age = 0.f, Life = 0.f; bool bAlive = false; };
	struct FSpray { FVector P = FVector::ZeroVector, V = FVector::ZeroVector; float Size0 = 10.f, Size1 = 50.f, Age = 0.f, Life = 0.f, Roll = 0.f; bool bAlive = false; };
	struct FPool { TWeakObjectPtr<UDecalComponent> Decal; float Age = 0.f; };
	static constexpr int32 MaxDrops = 360;
	static constexpr int32 MaxSprays = 28;
	UPROPERTY(Transient) TObjectPtr<ARDDungeonGenerator> Generator;
	UPROPERTY(Transient) TObjectPtr<UInstancedStaticMeshComponent> DropMesh;
	UPROPERTY(Transient) TObjectPtr<UInstancedStaticMeshComponent> SprayMesh;
	UPROPERTY(Transient) TArray<TObjectPtr<UDecalComponent>> Decals;
	TArray<FDrop> Drops;
	TArray<FSpray> Sprays;
	TArray<FPool> Pools;
	TArray<FTransform> DropXf, SprayXf;
	FRandomStream R;
	int32 NextDrop = 0, NextSpray = 0;
	bool bDropsDirty = false, bSpraysDirty = false;
	float DropRadius = 50.f, SprayHalf = 50.f;
	void AddDrop(const FVector& P, const FVector& V, float Size, float Life);
	UDecalComponent* AddDecal(UMaterialInterface* Material, const FVector& At, const FVector& Normal, float Size, float Depth);
};
