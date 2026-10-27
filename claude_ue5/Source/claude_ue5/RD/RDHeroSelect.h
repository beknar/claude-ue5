// random_dungeonmagic_level4: choosing the hero before the dungeon loads.
// The menu level (random_dungeonmagic_level4_select, built by pipeline/unreal/826) is a lit studio with a turntable: the
// hero shown turns on it with her weapons in her hands, and the HUD (ARDHeroSelectHUD) lists what she can do. Left /
// right (A / D, the arrows, the D-pad, the left stick, the mouse wheel; or a click on her name) shows the next one;
// Enter, Space, the gamepad's A or a click on START opens the dungeon level with ?Hero=<her name>. There
// ARDHeroGameMode spawns that hero's pawn and the generator takes her data (ARDDungeonGenerator::ApplyHero).
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/HUD.h"
#include "RDTypes.h"
#include "RDHeroSelect.generated.h"

/** the dungeon's game mode: her pawn is the one of the hero in ?Hero= (else the generator's DefaultHero) */
UCLASS()
class CLAUDE_UE5_API ARDHeroGameMode : public AGameModeBase
{
	GENERATED_BODY()
public:
	virtual UClass* GetDefaultPawnClassForController_Implementation(AController* InController) override;
};

/** the menu's game mode: no pawn (the view is the studio's camera), the menu's HUD */
UCLASS()
class CLAUDE_UE5_API ARDHeroSelectGameMode : public AGameModeBase
{
	GENERATED_BODY()
public:
	ARDHeroSelectGameMode();
};

/** the turntable and the choice (placed in the menu level, filled by pipeline/unreal/826) */
UCLASS()
class CLAUDE_UE5_API ARDHeroSelect : public AActor
{
	GENERATED_BODY()
public:
	ARDHeroSelect();
	/** the heroes, in the order shown (names, titles, what they can do, their stats) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Heroes") TArray<FRDHeroDef> Heroes;
	/** per hero: the figure that stands on the turntable (its weapons are actors attached to it); the others are hidden */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Heroes") TArray<TObjectPtr<AActor>> Figures;
	/** turned with the figure */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Heroes") TObjectPtr<AActor> Turntable;
	/** the view */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Heroes") TObjectPtr<AActor> Camera;
	/** what START opens (with ?Hero=<name>) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Heroes") FString TargetLevel = TEXT("/Game/RandomDungeon/Maps/random_dungeonmagic_level4");
	/** the line over "CHOOSE YOUR HERO" (mistward_castle: its name) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Heroes") FString GameTitle = TEXT("RANDOM DUNGEON");
	/** degrees a second */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Heroes") float TurnRate = 28.f;
	/** the turntable's yaw when a hero is first shown (her face to the camera) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Heroes") float FrontYaw = 0.f;

	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Heroes") void Show(int32 Index);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Heroes") void Step(int32 Delta) { Show(Index + Delta); }
	/** opens the dungeon with the hero shown; false when it cannot (no target) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Heroes") bool Confirm();
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Heroes") int32 GetIndex() const { return Index; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Heroes") FName GetHeroName() const { return Heroes.IsValidIndex(Index) ? Heroes[Index].Name : NAME_None; }
	/** how far the turntable has turned since play began (degrees; tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Heroes") float GetTurned() const { return Turned; }
	/** tests: a key pressed (or let go) as if on the keyboard or the gamepad, through the player controller (as
	 *  URDCombatComponent::SimulateKey); the menu reads it as a real press */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Heroes") bool SimulateKey(FKey Key, bool bDown);
	/** tests: the figure of that hero is seen (not hidden in the game), with every weapon attached to it */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Heroes") bool IsFigureShown(int32 I) const;
	/** the URL START opened ("" before; tests) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Heroes") FString Opened;
	/** the demo reel: START is pressed (Opened and ConfirmTime say so, the HUD's button lights) but the menu stays (a
	 *  Movie Render Queue render cannot follow the game into another level; the reel shows the dungeon from renders of its own) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Heroes") bool bStayOnConfirm = false;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Heroes") float ConfirmTime = -100.f;
	/** mistward (the user's of 2026-10-27): the mouse chooses. The pointer stays shown and free (the game's own mode hid it
	 *  and captured it on a click); a click on a hero's name shows her, on the name of the one shown or on START starts; the
	 *  arrows step. (Without it the HUD's hit boxes do the same through the engine's click events.) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Heroes") bool bMouseUI = false;
	/** tests: input the way the devices send it (RDInputSim); "" when sent, else why not. A pixel is the HUD canvas's. */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Heroes") FString SlateKey(FKey Key, bool bDown);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Heroes") FString SlateMouseMove(FVector2D Pixel);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Heroes") FString SlateMouseButton(FVector2D Pixel, FKey Button, bool bDown);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Heroes") FString SlateClearView();
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Heroes") int32 SlateRestoreView();
	/** the HUD's buttons as drawn last frame: "<name>|<x0>|<y0>|<x1>|<y1>" (Hero_<i>, Prev, Next, Start) (tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Heroes") TArray<FString> GetButtons() const;
	TArray<TPair<FName, FBox2D>> Buttons;
	/** a button the pointer is over (the HUD lights it) */
	FName Hovered;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Heroes") int32 Clicks = 0;
	/** the last input came from a gamepad (the HUD shows its keys) */
	bool bUsingGamepad = false;
	/** world time the hero shown changed (the HUD fades the card in) */
	float ShownTime = -100.f;
	/** the painted interface (as the dungeon generator's UIArt; pipeline/unreal/830): the card, the names, the arrows, START */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Interface") TMap<FName, FRDUIArt> UIArt;
	/** its lettering by role, as the dungeon generator's UIFonts */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Interface") TMap<FName, FRDUIFont> UIFonts;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	int32 Index = 0;
	float Yaw = 0.f, Turned = 0.f, StickRepeat = 0.f;
	bool bViewSet = false;
	void TickPointer(APlayerController* PC);
	void SetFigureShown(AActor* Figure, bool bShown);
};

/** the menu's HUD: the hero's card (name, role, hit points, mana, what she can do, what she wears and carries), the four
 *  names along the bottom (clickable), the keys */
UCLASS()
class CLAUDE_UE5_API ARDHeroSelectHUD : public AHUD
{
	GENERATED_BODY()
public:
	virtual void DrawHUD() override;
	virtual void NotifyHitBoxClick(FName BoxName) override;
	/** tests: the painted pieces drawn in the last frame */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Interface") TArray<FName> GetArtDrawn() const { return ArtDrawn; }
private:
	UPROPERTY(Transient) TObjectPtr<ARDHeroSelect> Sel;
	TArray<FName> ArtDrawn;
	/** the lettering's fonts made in play, one per role and size (FRDUIDraw::Text) */
	UPROPERTY(Transient) TMap<int32, TObjectPtr<class UFont>> FontCache;
};
