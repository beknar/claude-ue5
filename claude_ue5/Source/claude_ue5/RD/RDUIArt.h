// random_dungeonmagic_level4: drawing the painted interface (FRDUIArt) on a HUD's canvas. Both HUDs (the dungeon's
// ARDHUD and the menu's ARDHeroSelectHUD) look a piece up by name in their UIArt map and fall back to their plain boxes
// when it is not there. Every piece drawn is noted (Drawn) for the tests.
#pragma once

#include "CoreMinimal.h"
#include "RDTypes.h"

class AHUD;
class UFont;

/** what a piece of text is, for the lettering: a line of text (Alegreya), a label (Alegreya SC: "MANA BACK" is written
 *  "Mana Back", the rest of each word in small capitals), a title, a name, a key or a number standing alone (Cinzel) */
enum class ERDType : uint8 { Text, Label, Title };

struct FRDUIDraw
{
	AHUD* Hud = nullptr;
	const TMap<FName, FRDUIArt>* Art = nullptr;
	TArray<FName>* Drawn = nullptr;
	/** the lettering by role ("text", "label", "title"); none (or a role missing): the engine font given to Text */
	const TMap<FName, FRDUIFont>* Fonts = nullptr;
	/** where the fonts made for each role and size are kept (a UPROPERTY of the HUD: they must not be collected) */
	TMap<int32, TObjectPtr<UFont>>* FontCache = nullptr;

	/** AHUD::DrawText in the role's typeface, as tall as Engine would be at scale K (Engine itself without the lettering) */
	void Text(const FString& S, const FLinearColor& C, float X, float Y, UFont* Engine, float K, ERDType Role = ERDType::Text) const;
	/** AHUD::GetTextSize of what Text draws */
	void TextSize(const FString& S, float& OutW, float& OutH, UFont* Engine, float K, ERDType Role = ERDType::Text) const;
	/** the painted interface's lettering is there (else the engine font) */
	bool HasFonts() const { return Fonts && Fonts->Num() > 0; }

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
	/** the font a role is drawn in at the size Engine has at scale K, and the scale left over to draw it at (the glyphs are
	 *  rendered at about the size they are shown: a font scaled up from small glyphs is blurred) */
	UFont* Pick(UFont* Engine, float K, ERDType Role, float& OutK, FString& InOutS, float& OutRaise) const;
	void Tile(class UTexture2D* T, float X, float Y, float W, float H, float U, float V, float UW, float VH, const FLinearColor& Tint) const;
	void Note(FName Name) const { if (Drawn) Drawn->AddUnique(Name); }
};
