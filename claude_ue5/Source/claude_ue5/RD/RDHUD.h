// random_dungeon_level HUD: minimap (top right; generated rooms dim, discovered rooms lit, the player, nearby monsters,
// new sections flashing as they generate), the full map on M (everything discovered), and a prompt next to a door or
// container ("F  open door").
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "RDTypes.h"
#include "RDHUD.generated.h"

class ARDDungeonGenerator;

UCLASS()
class CLAUDE_UE5_API ARDHUD : public AHUD
{
	GENERATED_BODY()

public:
	/** minimap: metres across */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon") float MinimapMeters = 120.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon") float MinimapPixels = 300.f;

	virtual void DrawHUD() override;

private:
	UPROPERTY(Transient) TObjectPtr<ARDDungeonGenerator> Gen;
	static FString KindCode(ERDRoomKind Kind);
	void DrawPlayerArrow(const FVector2D& P, float Yaw, float Size);
	void Box(const FVector2D& A, const FVector2D& B, const FLinearColor& C);
	void Frame(const FVector2D& A, const FVector2D& B, const FLinearColor& C, float T);
};
