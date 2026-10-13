// starship_level HUD: the nose crosshair and the mouse aim point, target brackets with range, the locked target with
// its lead mark for the cannons, a scope of what is around the fighter (ahead in the middle, behind at the rim), speed /
// throttle / hull / missiles, the score, the edge-of-arena warning and the controls. Also the game mode that puts the
// controller and this HUD in (the fighter is placed in the level and possesses itself).
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/HUD.h"
#include "SSHUD.generated.h"

UCLASS()
class CLAUDE_UE5_API ASSHUD : public AHUD
{
	GENERATED_BODY()

public:
	virtual void DrawHUD() override;
	/** the controls are shown for this long at the start (H shows them again) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship") float HelpSeconds = 16.f;
	/** what the last frame drew (tests) */
	UPROPERTY(BlueprintReadOnly, Category = "Starship") int32 LastBrackets = 0;
	UPROPERTY(BlueprintReadOnly, Category = "Starship") bool bLastLeadMark = false;

private:
	void Ring(const FVector2D& C, float Radius, const FLinearColor& Col, float Thickness, int32 Sides = 24);
	void Bracket(const FVector2D& C, float Half, const FLinearColor& Col, float Thickness);
	void Bar(float X, float Y, float W, float H, float Fraction, const FLinearColor& Col, const FString& Label, const FString& Value);
};

UCLASS()
class CLAUDE_UE5_API ASSGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ASSGameMode();
};
