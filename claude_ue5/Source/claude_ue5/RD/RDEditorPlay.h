// Play in the editor in a window of its own, for the tests on brokenspire (2026-11-08b: play in the editor's 4K viewport ran
// the 12 GB GPU out of memory four times; the editor's own play mode cannot be chosen from Python, its setting is protected).
// The view's size decides most of a frame's own GPU memory (the TSR history alone was 322 MB at the viewport's size): a
// window of WxH, with the level editor's viewports no longer drawn live while it plays. Editor only: in a game it does nothing.
#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "RDEditorPlay.generated.h"

UCLASS()
class URDEditorPlay : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()
public:
	/** asks the editor to play the open level in a new window of W x H (false: no editor, or play is on already) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Editor") static bool PlayInNewWindow(int32 W = 1280, int32 H = 720);
	/** the level editor's viewports drawn live or not (they are put back to live with true) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Editor") static int32 SetLevelViewportsRealtime(bool bOn);
};
