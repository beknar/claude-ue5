// The Rogue's arts (the user's list of 2026-11-12, docs/improvements12.txt, its seventh phase: sixteen abilities, each learned from
// a manual found at its place among the dungeons' tiers; SourceArt/balance/rogue12.json, 925; RD/RDRogue12.cpp). What an art
// leaves in the world while it works is an ARDArtProp: the caltrops on the floor, the smoke's cloud, the acid's pool, her double,
// the coin, a crosshair over a marked monster, the hook's rope, and the things that fly (a vial, the net, the knives, the bolt).
#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RD/RDTypes.h"
#include "RDRogue12.generated.h"

class ARDDungeonGenerator;
class ARDMonster;
class UStaticMeshComponent;
class UNiagaraComponent;
class UPoseableMeshComponent;
class UPointLightComponent;

/** what an art's prop is */
UENUM(BlueprintType)
enum class ERDArtProp : uint8
{
	/** caltrops on the floor: monsters crossing them slowed and bleeding */
	Caltrops,
	/** a cloud: monsters inside lose her */
	Smoke,
	/** a pool of acid: monsters in it take more and burn */
	Acid,
	/** her double: draws the monsters near it, then bursts */
	Double,
	/** a coin on the floor: draws the monsters near it */
	Coin,
	/** a crosshair over a marked monster, following it */
	Mark,
	/** the hook's rope from her hand to the hook */
	Rope,
	/** a thing in flight (a vial, the net, a knife, the bolt, the tossed coin): what it does where it lands is its art's */
	Flying,
	/** an afterimage of her (the Death Lotus): fades */
	Afterimage,
	/** a flash of light (the flashbang) */
	Flash
};

UCLASS()
class CLAUDE_UE5_API ARDArtProp : public AActor
{
	GENERATED_BODY()
public:
	ARDArtProp();
	virtual void Tick(float DeltaSeconds) override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") ERDArtProp Kind = ERDArtProp::Flying;
	/** the art it is of */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") FName Art;
	/** when it goes (game seconds) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") float Until = 0.f;
	/** how far it reaches (cm): the caltrops', the cloud's, the pool's, the double's and the coin's draw */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") float Radius = 0.f;
	/** its numbers: the slow's share, the bleed or burn a second, the share more taken, the burst's damage */
	float A = 0.f, B = 0.f, C = 0.f;
	/** it draws the monsters near it as their foe (her double, the coin) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") bool bDecoy = false;
	/** the monsters it has reached (tests: the caltrops' bled, the cloud's lost, the pool's burned, the decoys' drawn) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") int32 Reached = 0;
	/** a flight: from, to, its time and how long it takes; the monster it is for; what follows it (ricochet: the monsters after) */
	FVector From = FVector::ZeroVector, To = FVector::ZeroVector;
	float FlyT = 0.f, FlyTime = 0.3f, Arc = 0.f, Spin = 0.f;
	TWeakObjectPtr<ARDMonster> Target;
	TArray<TWeakObjectPtr<ARDMonster>> Next;
	/** what it follows (a crosshair its monster; the rope her hand's place) */
	TWeakObjectPtr<AActor> Follow;
	TWeakObjectPtr<ARDDungeonGenerator> Gen;
	UPROPERTY(Transient) TObjectPtr<USceneComponent> Root;
	UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> Meshes;
	UPROPERTY(Transient) TArray<TObjectPtr<UNiagaraComponent>> Fxs;
	UPROPERTY(Transient) TObjectPtr<UPoseableMeshComponent> Pose;
	UPROPERTY(Transient) TObjectPtr<UPointLightComponent> Light;
	/** a mesh of its own (scaled, with a material, no collision) */
	UStaticMeshComponent* AddMesh(UStaticMesh* M, const FTransform& Rel, UMaterialInterface* Mat = nullptr);
	/** an effect on it (a share of its scale, tinted when it takes a colour) */
	UNiagaraComponent* AddFx(UNiagaraSystem* S, const FVector& Rel, float Scale, const FLinearColor& Tint = FLinearColor::White, bool bTint = false);
	/** a copy of her body in her pose now, in a material of its own (her double, an afterimage) */
	void CopyPose(class USkeletalMeshComponent* From, UMaterialInterface* Mat);
private:
	float Look = 0.f;
	TSet<TWeakObjectPtr<ARDMonster>> Done;
	void Land();
};
