// starship_level: shared data types. The fighter is a kitbash of pack meshes (FSSPart, filled by pipeline/unreal/800);
// asteroid fields, patrol volumes and drone types are data on the arena.
#pragma once

#include "CoreMinimal.h"
#include "SSTypes.generated.h"

class UStaticMesh;
class UMaterialInterface;

CLAUDE_UE5_API DECLARE_LOG_CATEGORY_EXTERN(LogStarship, Log, All);

UENUM(BlueprintType)
enum class ESSTargetKind : uint8 { Asteroid, Drone, Container, Debris };

/** one mesh of a kitbashed ship, in the ship frame (+X forward, +Y right, +Z up) */
USTRUCT(BlueprintType)
struct FSSPart
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") TObjectPtr<UStaticMesh> Mesh;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") FTransform Transform;
	/** replaces every material slot when set */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") TObjectPtr<UMaterialInterface> Material;
	/** engine flame: its length (the mesh's own Y axis, as Spaceship_Kit's SM_reactor_FX) follows the throttle */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") bool bFlame = false;
	/** a missile on its rail (index into the fighter's MissileRails): hidden while that rail reloads; -1 = always shown */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") int32 Rail = -1;
};

USTRUCT(BlueprintType)
struct FSSSphere
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") FVector Center = FVector::ZeroVector;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") float Radius = 10000.f;
};

/** a cluster of destructible targets the arena spawns in play (asteroids or cargo containers) */
USTRUCT(BlueprintType)
struct FSSField
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") FVector Center = FVector::ZeroVector;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") float Radius = 50000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") int32 Count = 40;
	/** target size: bounding radius in cm, picked between the two (more small ones than big ones) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") float MinSize = 250.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") float MaxSize = 1800.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") ESSTargetKind Kind = ESSTargetKind::Asteroid;
};

/** a target drone type: one pack mesh flying patrol circles */
USTRUCT(BlueprintType)
struct FSSDroneDef
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") FName Name;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") TObjectPtr<UStaticMesh> Mesh;
	/** turns the mesh so that its nose is +X */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") FRotator MeshRotation = FRotator::ZeroRotator;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") float Scale = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") float Health = 70.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") float Speed = 9000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") int32 Points = 100;
	/** where its engine trail starts, in the drone frame (after MeshRotation and Scale) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") FVector TrailOffset = FVector(-500.f, 0.f, 0.f);
};
