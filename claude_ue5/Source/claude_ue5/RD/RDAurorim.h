// mistward_castle's final boss (the user's spec of 2026-11-03, docs/levels/mistward_castle.md): Aurorim, an angel of four
// wings, waits in a room of the last tier once it reaches the tiers' share; beside him the door back to Brokenspire,
// sealed while he lives. RDAurorim.cpp holds his levitating, his beam of light from above, the wind round his fists, the
// lance his shot carries, his placing, his reward and this door.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RDAurorim.generated.h"

class ARDDungeonGenerator;
class UStaticMeshComponent;
class UFXSystemComponent;
class UFXSystemAsset;

/** the door to Brokenspire: an arch with a grating in it while it is sealed; open, the grating sinks into the floor and a
 *  light fills the arch, and walking into it takes her back to Brokenspire (before the castle's door) */
UCLASS()
class CLAUDE_UE5_API ARDFinalDoor : public AActor
{
	GENERATED_BODY()
public:
	ARDFinalDoor();
	UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> Pivot;
	UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Frame;
	UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Gate;
	UPROPERTY(Transient) TObjectPtr<UFXSystemComponent> Glow;
	UPROPERTY(Transient) TObjectPtr<UFXSystemAsset> GlowFx;
	TWeakObjectPtr<ARDDungeonGenerator> Generator;
	/** the opening (cm): its width and height, in front of the door's plane */
	float OpenWidth = 200.f, OpenHeight = 300.f, GlowScale = 0.5f;
	UPROPERTY(BlueprintReadOnly) bool bOpen = false;
	UPROPERTY(BlueprintReadOnly) float OpenAlpha = 0.f;
	UPROPERTY(BlueprintReadOnly) bool bTravelled = false;
	/** set up: the arch, the grating fitted into its opening, scaled to stand Height tall */
	void Init(ARDDungeonGenerator* Gen, class UStaticMesh* FrameMesh, class UStaticMesh* GateMesh, UFXSystemAsset* Fx, float Height, float FxScale);
	UFUNCTION(BlueprintCallable) void Open();
	/** "<open>|<alpha>|<travelled>|<x>|<y>|<z>|<facing x>|<facing y>|<width>|<height>|<gate z>|<gate collides>|<light>|<its
	 *  particles>" (tests) */
	UFUNCTION(BlueprintCallable) FString GetDoorState() const;
	/** where she would stand to walk through it: in front of it, Out cm into the room */
	UFUNCTION(BlueprintCallable) FVector GetApproach(float Out = 150.f) const;
	virtual void Tick(float Dt) override;
private:
	float GateZ0 = 0.f;
	/** she has stood clear of the opening since it opened all the way: only then does walking into it take her (one fighting
	 *  him with her back to it is not sent off the moment he falls, before she takes his reward) */
	bool bArmed = false;
};
