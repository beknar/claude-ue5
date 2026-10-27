// Tests' input sent the way a real keyboard, mouse or gamepad sends it: into Slate (FSlateApplication), which hands it to
// the play-in-editor viewport, which hands it to the player controller. URDCombatComponent::SimulateKey starts at the player
// controller and skips the viewport (its focus, the mouse's capture, where the pointer is): a real held key or a real click
// could behave otherwise than the tests said (the user's of 2026-10-27). These refuse rather than send input elsewhere: a key
// only when the game's viewport has the keyboard focus, a pointer only over the game's viewport.
#pragma once

#include "CoreMinimal.h"
#include "InputCoreTypes.h"

class UWorld;

namespace RDInputSim
{
	/** a key (keyboard or gamepad) down or up; "" when sent, else why not */
	CLAUDE_UE5_API FString Key(UWorld* World, const FKey& Key, bool bDown);
	/** the pointer to a pixel of the game's view (as the HUD's canvas counts them) */
	CLAUDE_UE5_API FString MouseMove(UWorld* World, const FVector2D& Pixel);
	/** a mouse button down or up at a pixel of the game's view */
	CLAUDE_UE5_API FString MouseButton(UWorld* World, const FVector2D& Pixel, const FKey& Button, bool bDown);
	/** a turn of the wheel at a pixel (+1 away from her: up) */
	CLAUDE_UE5_API FString Wheel(UWorld* World, const FVector2D& Pixel, float Delta);
	/** the editor's other windows that lie over the game's view (a floating Message Log covered it, and a click there would
	 *  go to the log) hidden while a test runs; their titles. RestoreView shows them again. */
	CLAUDE_UE5_API FString ClearView(UWorld* World);
	CLAUDE_UE5_API int32 RestoreView();
}
