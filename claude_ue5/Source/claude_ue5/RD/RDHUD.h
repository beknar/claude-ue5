// random_dungeon_level HUD: minimap (top right; generated rooms dim, discovered rooms lit, the player, nearby monsters,
// new sections flashing as they generate), the full map on M (everything discovered), and a prompt next to a door or
// container ("F  open door").
// random_dungeoncombat_level adds (the generator's bStylizedMap / bCombat): both maps drawn as a miniature of the dungeon
// (stone floors coloured by room, walls with a lit and a shaded edge, paving joints, doors, chests, flickering torches;
// every room named on the full map), a status panel in the bottom right corner (hit points, the three weapons with
// their damage, kills), a bar over each monster in the fight, the damage numbers, a red flash when she is hurt.
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
	/** the stylised minimap shows less of the dungeon, larger (metres across) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon") float StylizedMinimapMeters = 84.f;

	virtual void DrawHUD() override;

private:
	UPROPERTY(Transient) TObjectPtr<ARDDungeonGenerator> Gen;
	static FString KindCode(ERDRoomKind Kind);
	void DrawPlayerArrow(const FVector2D& P, float Yaw, float Size);
	void Box(const FVector2D& A, const FVector2D& B, const FLinearColor& C);
	void Frame(const FVector2D& A, const FVector2D& B, const FLinearColor& C, float T);
	/** the miniature: ToS maps world XY to the screen, everything is clipped to S0..S1 */
	void DrawDungeon(const FVector2D& S0, const FVector2D& S1, TFunctionRef<FVector2D(const FVector2D&)> ToS, float PixelsPerTile, bool bOnlyDiscovered, bool bLabels, float Sc);
	void DrawCombat(float Sc);
};
