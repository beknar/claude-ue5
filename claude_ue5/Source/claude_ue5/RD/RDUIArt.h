// random_dungeonmagic_level4: drawing the painted interface (FRDUIArt) on a HUD's canvas. Both HUDs (the dungeon's
// ARDHUD and the menu's ARDHeroSelectHUD) look a piece up by name in their UIArt map and fall back to their plain boxes
// when it is not there. Every piece drawn is noted (Drawn) for the tests.
#pragma once

#include "CoreMinimal.h"
#include "RDTypes.h"

class AHUD;

struct FRDUIDraw
{
	AHUD* Hud = nullptr;
	const TMap<FName, FRDUIArt>* Art = nullptr;
	TArray<FName>* Drawn = nullptr;

	const FRDUIArt* Find(FName Name) const;
	bool Has(FName Name) const { return Find(Name) != nullptr; }
	/** stretched into A..B; its border (Art.Border, shares of the picture) is drawn at Px screen pixels a picture pixel
	 *  (the corners keep their shape, the edges and the middle stretch). False when there is no such piece. */
	bool Nine(FName Name, const FVector2D& A, const FVector2D& B, float Px, const FLinearColor& Tint = FLinearColor::White) const;
	/** fitted into A..B without changing its shape (centred); bFlipX mirrors it */
	bool Fit(FName Name, const FVector2D& A, const FVector2D& B, const FLinearColor& Tint = FLinearColor::White, bool bFlipX = false) const;
	/** the screen box of a piece fitted into A..B (as Fit draws it) */
	bool FitBox(FName Name, const FVector2D& A, const FVector2D& B, FVector2D& OutA, FVector2D& OutB) const;
	/** a hollow frame (a bar's) stretched to A..B as Nine, with Fill's picture inside its open part (Art.Inner) up to
	 *  Fraction of the way along; FillTint tints the fill. Returns false when the frame is missing. */
	bool Bar(FName Frame, FName Fill, const FVector2D& A, const FVector2D& B, float Px, float Fraction, const FLinearColor& FillTint = FLinearColor::White, const FLinearColor& FrameTint = FLinearColor::White) const;
	/** where a frame's open inside is when it is stretched to A..B as Nine draws it */
	void InnerBox(FName Frame, const FVector2D& A, const FVector2D& B, float Px, FVector2D& OutA, FVector2D& OutB) const;
private:
	void Tile(class UTexture2D* T, float X, float Y, float W, float H, float U, float V, float UW, float VH, const FLinearColor& Tint) const;
	void Note(FName Name) const { if (Drawn) Drawn->AddUnique(Name); }
};
