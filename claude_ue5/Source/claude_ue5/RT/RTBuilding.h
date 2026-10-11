// random_level: one placed building (a streamed docks building level or a Sherwood house prefab) with working doors and
// containers. Doors swing open away from the player as she comes near and close behind her; containers (bed chests,
// wardrobes, crates) toggle with F when she stands next to them (or from script: ToggleContainer).
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RTTypes.h"
#include "RTBuilding.generated.h"

class ARTTownGenerator;
class ULevelStreamingDynamic;
class UStaticMeshComponent;

UCLASS()
class CLAUDE_UE5_API ARTBuilding : public AActor
{
	GENERATED_BODY()

public:
	ARTBuilding();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomTown") int32 TemplateIndex = -1;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomTown") TObjectPtr<ARTTownGenerator> Generator;
	/** start-square buildings: level instance actor placed in the editor (saved with the level) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomTown") TObjectPtr<AActor> EditorLevelInstance;
	/** Sherwood prefab house actor */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomTown") TObjectPtr<AActor> PrefabActor;
	/** street centre in front of the entrance */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomTown") FVector StreetPoint = FVector::ZeroVector;

	/** place the building: editor build = saved level instance; runtime = streamed level instance */
	void Init(ARTTownGenerator* InGenerator, int32 InTemplate, bool bEditorBuild);

	UFUNCTION(BlueprintCallable, Category = "RandomTown") bool IsInteriorReady() const { return bProcessed; }
	UFUNCTION(BlueprintCallable, Category = "RandomTown") FName GetPurpose() const;
	UFUNCTION(BlueprintCallable, Category = "RandomTown") FName GetTemplateName() const;
	/** street point, 2.5 m outside the entrance, 1 m inside it (world) */
	UFUNCTION(BlueprintCallable, Category = "RandomTown") void GetEntry(FVector& Street, FVector& Outside, FVector& Inside) const;
	UFUNCTION(BlueprintCallable, Category = "RandomTown") int32 GetNumInteriorPaths() const;
	UFUNCTION(BlueprintCallable, Category = "RandomTown") TArray<FVector> GetInteriorPath(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "RandomTown") int32 GetNumDoors() const { return Doors.Num(); }
	UFUNCTION(BlueprintCallable, Category = "RandomTown") float GetDoorOpenAlpha(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "RandomTown") FVector GetDoorLocation(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "RandomTown") int32 GetNumContainers() const { return Containers.Num(); }
	UFUNCTION(BlueprintCallable, Category = "RandomTown") bool IsContainerOpen(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "RandomTown") float GetContainerOpenAlpha(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "RandomTown") FVector GetContainerLocation(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "RandomTown") FString GetContainerKind(int32 Index) const;
	UFUNCTION(BlueprintCallable, Category = "RandomTown") bool ToggleContainer(int32 Index);
	/** toggles the nearest container within MaxDistance of From; returns its index or -1 */
	UFUNCTION(BlueprintCallable, Category = "RandomTown") int32 ToggleNearestContainer(FVector From, float MaxDistance = 220.f);
	UFUNCTION(BlueprintCallable, Category = "RandomTown") int32 GetNumHiddenOriginals() const { return HiddenOriginals; }

	const FRTBuildingTemplate* GetTemplate() const;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;
	virtual void Destroyed() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	struct FMover
	{
		USceneComponent* Pivot = nullptr;
		TArray<UStaticMeshComponent*> Parts;   // moving parts (collision off while open)
		FQuat Closed = FQuat::Identity;
		FVector Axis = FVector::UpVector;       // local rotation axis (pivot frame)
		float OpenAngle = 95.f;                 // degrees, signed
		float Alpha = 0.f, Target = 0.f;
		bool bDoor = false;
		bool bDoor01Side = true;                // door leaf extends along local +X (else -X)
		FString Kind;
		FVector Center = FVector::ZeroVector;   // world (interaction / proximity)
		FVector Normal = FVector::ZeroVector;   // doors: world leaf normal when closed
	};
	TArray<FMover> Doors;
	TArray<FMover> Containers;
	bool bProcessed = false;
	bool bInitialized = false;
	float WaitTime = 0.f;
	int32 HiddenOriginals = 0;
	UPROPERTY(Transient) TObjectPtr<ULevelStreamingDynamic> Streamed;

	void CreateInteractive();
	void ClearInteractive();
	bool TryProcessInterior();
	UStaticMeshComponent* AddMesh(USceneComponent* Parent, UStaticMesh* Mesh, const FTransform& Rel, bool bCollision);
	USceneComponent* AddPivot(USceneComponent* Parent, const FTransform& Rel);
	void AddLidContainer(UStaticMesh* Body, UStaticMesh* Lid, const FVector& Loc, float Yaw, float HingeY, float BodyH, const FString& Kind);
};
