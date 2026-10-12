// random_isometric_village_level: isometric camera + 8-direction movement. Moving never turns the view: the camera keeps
// the generator's IsoPitch and its view yaw and only follows (and zooms). Movement is screen-relative and snapped to 8
// directions: W/A/S/D or the arrow keys, an Xbox controller's left stick or D-pad. Q / E (LB / RB) turn the view left /
// right in 45 degree steps (the map and the cutaway turn with it). F / A / X interacts (doors, containers), M / Y / View
// toggles the big map, mouse wheel / right stick zoom (down to a close view of her), Shift / left trigger walks.
// The character blueprint's own input mappings (third-person template: camera-relative move + mouse look) are removed.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "IVPlayerController.generated.h"

class AIVVillageGenerator;
class ACameraActor;

UCLASS()
class CLAUDE_UE5_API AIVPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	AIVPlayerController();

	/** orthographic view width (cm): zoom */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Camera") float OrthoWidth = 2500.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Camera") float MinOrthoWidth = 600.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Camera") float MaxOrthoWidth = 5600.f;
	/** camera distance from the focus point (orthographic: only clipping depends on it) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Camera") float CameraDistance = 12000.f;
	/** how fast the camera catches up with her (1/s; 0 = rigid) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Camera") float FollowSpeed = 7.f;
	/** camera looks at this height above her capsule centre */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Camera") float FocusHeight = 20.f;
	/** one press of Q / E turns the view this far (degrees), at RotateSpeed degrees a second */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Camera") float RotateStep = 45.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Camera") float RotateSpeed = 240.f;
	/** movement input scale while walking (her walk speed / run speed) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Input") float WalkScale = 0.3128f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Input") float StickDeadZone = 0.3f;
	/** stick deflection below this walks, above it runs */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Input") float StickRunThreshold = 0.8f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Input") float InteractDistance = 260.f;

	/** screen-relative input (x right, y up) -> world direction on the ground, snapped to the nearest of 8 directions */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "IsoVillage") FVector ScreenToWorldDirection(FVector2D Screen, bool bSnap = true) const;
	/** last movement input: 0..7 = direction index (0 = screen up, clockwise), -1 = none (tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "IsoVillage") int32 GetMoveDirectionIndex() const { return MoveDirIndex; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "IsoVillage") bool IsUsingGamepad() const { return bGamepad; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "IsoVillage") ACameraActor* GetIsoCamera() const { return IsoCam; }
	/** scripted input for tests: screen-relative direction held until cleared with (0, 0) */
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") void SetScriptedMove(FVector2D Screen, bool bWalk = false) { ScriptedMove = Screen; bScriptedWalk = bWalk; }
	/** scripted left-stick deflection for tests (goes through the same dead zone, 8-way snap and walk / run threshold
	 *  as a real controller); (0, 0) hands the stick back */
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") void SetScriptedStick(FVector2D Stick) { ScriptedStick = Stick; }
	/** input scale of the last movement (1 = run, WalkScale = walk) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "IsoVillage") float GetMoveScale() const { return MoveScale; }
	/** turn the view by Steps * RotateStep (what Q does for +1 and E for -1: +1 turns the camera clockwise seen from
	 *  above, so the village turns to the left on screen) */
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") void RotateView(int32 Steps) { TargetYawOffset += Steps * RotateStep; }
	/** camera yaw now / once the turn in progress is finished */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "IsoVillage") float GetViewYaw() const { return IsoYaw(); }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "IsoVillage") bool IsViewTurning() const { return !FMath::IsNearlyEqual(YawOffset, TargetYawOffset, 0.01f); }

protected:
	virtual void BeginPlay() override;
	virtual void OnPossess(APawn* InPawn) override;
	virtual void PlayerTick(float DeltaSeconds) override;

private:
	UPROPERTY(Transient) TObjectPtr<ACameraActor> IsoCam;
	UPROPERTY(Transient) TObjectPtr<AIVVillageGenerator> Gen;
	FVector Focus = FVector::ZeroVector;
	bool bFocusValid = false;
	bool bGamepad = false;
	int32 MoveDirIndex = -1;
	FVector2D ScriptedMove = FVector2D::ZeroVector, ScriptedStick = FVector2D::ZeroVector;
	float MoveScale = 0.f;
	bool bScriptedWalk = false;
	float ClearMappingsUntil = 0.f;
	float YawOffset = 0.f, TargetYawOffset = 0.f, TurnHold = 0.f;

	void FindGenerator();
	void EnsureCamera();
	void UpdateCamera(float Dt, bool bSnap);
	float IsoYaw() const;
	float IsoPitch() const;
};
