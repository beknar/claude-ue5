// random_level: one 250 m x 250 m town cell: terrain mesh (with collision), cobbled streets every 50 m, 5 x 5 blocks
// (houses facing the streets, one tavern per cell, market squares, gardens with Sherwood cabins, greens), yard props and
// foliage as instanced meshes. Everything is derived from (cell, seed), so a cell regenerates identically.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RTTypes.h"
#include "RTCell.generated.h"

class ARTTownGenerator;
class ARTBuilding;
class UProceduralMeshComponent;
class UHierarchicalInstancedStaticMeshComponent;
class UMaterialInterface;

/** flattened building lot: XY box and height */
USTRUCT()
struct FRTPad
{
	GENERATED_BODY()
	UPROPERTY() FVector2D Min = FVector2D::ZeroVector;
	UPROPERTY() FVector2D Max = FVector2D::ZeroVector;
	UPROPERTY() float Z = 0.f;
};

UCLASS()
class CLAUDE_UE5_API ARTCell : public AActor
{
	GENERATED_BODY()

public:
	ARTCell();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomTown") TObjectPtr<UProceduralMeshComponent> Ground;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomTown") FIntPoint Coord = FIntPoint::ZeroValue;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomTown") int32 Seed = 0;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomTown") bool bEditorBuilt = false;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomTown") TObjectPtr<ARTTownGenerator> Generator;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomTown") TArray<TObjectPtr<ARTBuilding>> Buildings;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomTown") TArray<TObjectPtr<AActor>> OtherActors;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomTown") int32 NumInstances = 0;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomTown") TArray<FString> BlockTypes;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomTown") float GenerateMs = 0.f;
	UPROPERTY() TArray<FRTPad> Pads;

	void Generate(ARTTownGenerator* InGenerator, FIntPoint InCoord, int32 InSeed, bool bEditorBuild);
	/** ground height including the flattened lots */
	UFUNCTION(BlueprintCallable, Category = "RandomTown") float SurfaceHeight(float X, float Y) const;
	UFUNCTION(BlueprintCallable, Category = "RandomTown") FVector2D GetCellMin() const;
	UFUNCTION(BlueprintCallable, Category = "RandomTown") int32 GetNumBuildings() const { return Buildings.Num(); }
	/** generation indicator: translucent walls on the cell border (UV.y 0 at the ground, 1 at the top), removed after Lifetime */
	void ShowCurtain(UMaterialInterface* Material, float StartTime, float Height, float Lifetime);

protected:
	virtual void BeginPlay() override;
	virtual void Destroyed() override;

private:
	struct FCircle { FVector2D C; float R; };
	TArray<FBox2D> Solid;      // building footprints, stalls
	TArray<FBox2D> KeepClear;  // entrance paths
	TArray<FCircle> Circles;   // solid props / trees
	TMap<UStaticMesh*, UHierarchicalInstancedStaticMeshComponent*> Hisms;
	TMap<UStaticMesh*, TArray<FTransform>> PendingInstances;
	bool bEditor = false;

	void BuildGround();
	void LayoutBlock(FRandomStream& R, int32 Bx, int32 By, const FString& Type);
	bool PlaceBuilding(FRandomStream& R, const FBox2D& Slot, int32 Axis, float Sign, float StreetLine, const TArray<FName>& Purposes);
	void ScatterIn(FRandomStream& R, const FBox2D& Area, const TArray<FRTScatterItem>& Items, int32 Count, bool bSolid, float Clearance = 60.f);
	bool IsFree(const FVector2D& P, float Radius, bool bIgnoreCircles = false) const;
	float StreetDistance(const FVector2D& P) const;
	const FRTScatterItem* Pick(FRandomStream& R, const TArray<FRTScatterItem>& Items) const;
	void AddInstance(const FRTScatterItem& It, const FVector2D& P, float Yaw, float Scale);
	void FlushInstances();
	static float ItemRadius(const FRTScatterItem& It, float Scale);
};
