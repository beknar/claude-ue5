// starship_level: flying the fighter (ASSFighter), read straight from the keys so the level needs no input assets.
//   W / S (or Up / Down)      throttle up / down            left stick up / down
//   A / D (or Left / Right)   roll left / right             left stick left / right
//   mouse                     where the nose points         right stick (turn rate)
//   left button / Space       cannons                       right trigger
//   right button / Ctrl       missile                       left trigger or RB
//   Shift                     afterburner                   A or left stick click
//   Tab / T                   next target                   Y
//   mouse wheel               chase camera closer / farther D-pad up / down
//   [ / ]                     mouse sensitivity down / up
//   I invert pitch, H help, R back to the start             (R: View button, help: Menu button)
// The mouse moves an aim point ahead of the nose (drawn by the HUD); the fighter turns toward it at its mouse turn
// rates (well above the stick's), so the nose follows the hand but a wild flick cannot spin it round. The mouse is
// read as raw counts: the engine's own mouse value is the counts scaled by the project's axis sensitivity (0.07) and
// by the field of view, which made the fighter about 40 times less responsive than the numbers here say. Tests drive
// the same code paths through the Scripted* inputs.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "SSPlayerController.generated.h"

class ASSFighter;

UCLASS()
class CLAUDE_UE5_API ASSPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	ASSPlayerController();

	/** degrees of aim per raw mouse count (an 800 dpi mouse moved 1 cm: 315 counts) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Input") float MouseSensitivity = 0.1f;
	/** the player's own setting on top of it ([ and ] in play) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Input") float MouseScale = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Input") FVector2D MouseScaleRange = FVector2D(0.2f, 5.f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Input") float StickDeadZone = 0.18f;
	/** pitch the other way round: mouse / stick back = nose up */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Input") bool bInvertPitch = false;
	UPROPERTY(BlueprintReadOnly, Category = "Starship|Input") bool bShowHelp = false;

	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") bool IsUsingGamepad() const { return bGamepad; }
	/** world time until which the HUD shows the mouse sensitivity (it was just changed) */
	float MouseNoteUntil = -1.f;
	// ---- scripted input for tests: each goes through the same code as the real device, and stays until cleared
	UFUNCTION(BlueprintCallable, Category = "Starship") void SetScriptedKeys(bool bW, bool bS, bool bA, bool bD, bool bShift) { KeyW = bW; KeyS = bS; KeyA = bA; KeyD = bD; KeyShift = bShift; }
	/** mouse movement in counts a second (x right, y up) */
	UFUNCTION(BlueprintCallable, Category = "Starship") void SetScriptedMouse(FVector2D CountsPerSecond) { ScriptedMouse = CountsPerSecond; }
	/** the mouse moved by this many counts (x right, y up): taken once, with the next tick, however long that tick is
	 *  (the Movie Render Queue steps the game unevenly: short steps while the shutter is open, a long one while it is shut) */
	UFUNCTION(BlueprintCallable, Category = "Starship") void AddScriptedMouseCounts(FVector2D Counts) { ScriptedCounts += Counts; }
	UFUNCTION(BlueprintCallable, Category = "Starship") void SetScriptedButtons(bool bLeft, bool bRight) { BtnLeft = bLeft; BtnRight = bRight; }
	UFUNCTION(BlueprintCallable, Category = "Starship") void SetScriptedPad(FVector2D LeftStick, FVector2D RightStick, float LeftTrigger, float RightTrigger, bool bA)
	{ PadLeft = LeftStick; PadRight = RightStick; PadLT = LeftTrigger; PadRT = RightTrigger; PadA = bA; }
	UFUNCTION(BlueprintCallable, Category = "Starship") void ClearScripted();
	/** tests: only the scripted inputs count (the real mouse, keyboard and controller are not read) */
	UFUNCTION(BlueprintCallable, Category = "Starship") void SetScriptedOnly(bool bOnly) { bScriptedOnly = bOnly; }

protected:
	virtual void BeginPlay() override;
	virtual void PlayerTick(float DeltaSeconds) override;

private:
	bool bGamepad = false, bScriptedOnly = false;
	bool Down(const FKey& K) const { return !bScriptedOnly && IsInputKeyDown(K); }
	bool Pressed(const FKey& K) const { return !bScriptedOnly && WasInputKeyJustPressed(K); }
	float Axis(const FKey& K) const { return bScriptedOnly ? 0.f : GetInputAnalogKeyState(K); }
	bool KeyW = false, KeyS = false, KeyA = false, KeyD = false, KeyShift = false, BtnLeft = false, BtnRight = false, PadA = false;
	FVector2D ScriptedMouse = FVector2D::ZeroVector, ScriptedCounts = FVector2D::ZeroVector, PadLeft = FVector2D::ZeroVector, PadRight = FVector2D::ZeroVector;
	float PadLT = 0.f, PadRT = 0.f;
	float Stick(float V) const;
};
