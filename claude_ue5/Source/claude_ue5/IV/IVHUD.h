// random_isometric_village_level HUD: a stylised miniature of the village drawn in the same isometric projection as the
// game view (ground, fields, roads and the square first, then houses with their roofs, trees and market stalls sorted
// back to front). Top right: the minimap around the player. M: the big map (centred on her, wheel / shoulder buttons
// zoom) with every building labelled. Also the F prompt next to a door or container, the new-section banner and a
// controls hint (keyboard or Xbox controller, whichever was used last).
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "IVTypes.h"
#include "IVHUD.generated.h"

class AIVVillageGenerator;
struct FCanvasUVTri;

UCLASS()
class CLAUDE_UE5_API AIVHUD : public AHUD
{
	GENERATED_BODY()

public:
	/** minimap: metres across (screen width of the panel) and its size at 1080p */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage") float MinimapMeters = 115.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage") float MinimapPixels = 320.f;
	/** big map: metres of ground (front to back) the panel shows at zoom 1 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage") float MapMeters = 240.f;

	virtual void DrawHUD() override;

	/** what the map draws around a point (tests): buildings in view */
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") int32 GetLastMapBuildingCount() const { return LastBuildings; }
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") int32 GetLastMapLabelCount() const { return LastLabels; }

private:
	UPROPERTY(Transient) TObjectPtr<AIVVillageGenerator> Gen;
	TArray<FCanvasUVTri> Tris;
	FBox2D ClipBox = FBox2D(ForceInit);
	// current map transform: screen = Origin + Scale * Project(world)
	FVector2D MapOrigin = FVector2D::ZeroVector;
	float MapScale = 0.01f;
	FVector2D IsoRight = FVector2D(-0.7071f, 0.7071f), IsoUp = FVector2D(0.7071f, 0.7071f);
	float IsoSin = 0.5774f, IsoCos = 0.8165f;
	int32 LastBuildings = 0, LastLabels = 0;

	FVector2D Project(const FVector& W) const;
	FVector2D ToScreen(const FVector& W) const { return MapOrigin + Project(W) * MapScale; }
	void Poly(const TArray<FVector2D>& Pts, const FLinearColor& C);
	void Quad(const FVector& A, const FVector& B, const FVector& Cc, const FVector& D, const FLinearColor& C);
	void Tri3(const FVector& A, const FVector& B, const FVector& Cc, const FLinearColor& C);
	void Disc(const FVector& Center, float Radius, const FLinearColor& C, int32 Sides = 8, float Squash = -1.f);
	void Rect(const FVector2D& A, const FVector2D& B, const FLinearColor& C);
	void Flush();
	void Frame(const FVector2D& A, const FVector2D& B, const FLinearColor& C, float T);
	void DrawRoad(const FIVMapRoad& R, bool bOutline);
	void DrawBuilding(const FIVMapBuilding& B, float Alpha);
	void DrawTree(const FIVMapTree& T);
	void DrawProp(const FIVMapProp& P);
	/** the miniature around Center (world), clipped to [A, B]; labels on the big map */
	void DrawVillage(const FVector2D& A, const FVector2D& B, const FVector& Center, float PixelsPerCm, bool bLabels, const FVector& Player, float PlayerYaw);
	void DrawPlayer(const FVector& Player, float Yaw, float Size);
};
