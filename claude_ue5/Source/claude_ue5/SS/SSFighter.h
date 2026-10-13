// starship_level: the player's space fighter. A kitbash of pack meshes (Parts, +X forward) flown with six degrees of
// freedom: the controller feeds a throttle change, a roll and where the nose should go (mouse: an aim point the nose
// chases at its mouse turn rates; stick: a fraction of the stick turn rates), the fighter keeps its speed toward throttle x MaxSpeed and its velocity
// swinging round to where the nose points. Two weapons: wing cannons (fast bolts, pooled as instances and traced each
// frame) and homing missiles (ASSMissile) that lock on to the target nearest the nose. Thrusters: flame meshes whose
// length follows the throttle and a Niagara contrail per engine. A chase camera on a lagging spring arm follows it.
// It bounces off whatever it flies into (hull damage; destroyed at 0: it reappears at its start) and is turned back at
// the edge of the arena.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "SS/SSTypes.h"
#include "SSFighter.generated.h"

class ASSArena;
class ASSTarget;
class UCameraComponent;
class UInstancedStaticMeshComponent;
class UNiagaraComponent;
class UNiagaraSystem;
class UFXSystemComponent;
class UParticleSystem;
class UPointLightComponent;
class USphereComponent;
class USpringArmComponent;
class UStaticMeshComponent;

UCLASS()
class CLAUDE_UE5_API ASSFighter : public APawn
{
	GENERATED_BODY()

public:
	ASSFighter();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Starship") TObjectPtr<USphereComponent> Hull;
	/** the meshes hang under this (it banks a little into turns; the flight frame is the actor's) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Starship") TObjectPtr<USceneComponent> Visual;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Starship") TObjectPtr<USpringArmComponent> Arm;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Starship") TObjectPtr<UCameraComponent> Camera;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Starship") TObjectPtr<UInstancedStaticMeshComponent> Bolts;
	/** specks of dust around the fighter that streak past with its speed (nothing else in space shows how fast it goes) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Starship") TObjectPtr<UInstancedStaticMeshComponent> Dust;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Starship") TObjectPtr<UPointLightComponent> EngineLight;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Starship") TObjectPtr<UPointLightComponent> MuzzleLight;

	// ---- the kitbash (ship frame: +X forward, +Y right, +Z up; cm)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Ship") TArray<FSSPart> Parts;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Ship") TArray<FVector> CannonMuzzles;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Ship") TArray<FVector> MissileRails;
	/** engine nozzles: a contrail starts at each */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Ship") TArray<FVector> Thrusters;
	/** the contrail effect: a Niagara system or a Cascade one (either, or both) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Ship") TObjectPtr<UNiagaraSystem> ThrusterFX;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Ship") TObjectPtr<UParticleSystem> ThrusterPS;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Ship") FVector ThrusterFXScale = FVector(1.f);
	/** turns the contrail effect so that it streams out along -X */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Ship") FRotator ThrusterFXRotation = FRotator::ZeroRotator;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Ship") float HullRadius = 330.f;
	/** candelas at full throttle (the level's exposure is fixed: a few hundred light the tail without washing it out) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Ship") float EngineLightIntensity = 220.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Ship") float MuzzleLightIntensity = 450.f;

	// ---- flight
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Flight") float MaxSpeed = 22000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Flight") float BoostSpeed = 42000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Flight") float Acceleration = 16000.f;
	/** throttle change per second with W / S held */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Flight") float ThrottleRate = 0.6f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Flight") float StartThrottle = 0.35f;
	/** degrees a second, nose up / down, left / right, and roll (the nose rates are the stick's; the mouse has its own) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Flight") float PitchRate = 95.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Flight") float YawRate = 75.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Flight") float RollRate = 150.f;
	/** how fast the turn rates follow the input (1/s) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Flight") float TurnResponse = 7.f;
	/** how fast the velocity swings round to where the nose points (1/s): lower = more drift */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Flight") float Grip = 3.2f;
	/** mouse aim: the aim point may lead the nose by at most this many degrees, and the nose closes that gap at
	 *  AimGain x gap degrees a second (up to the mouse turn rates) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Flight") float MaxAim = 32.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Flight") float AimGain = 10.f;
	/** flying by mouse: the nose turns this fast at most (degrees a second), the turn rates follow the hand this
	 *  quickly (1/s) and the velocity swings round to the nose this quickly (1/s). The stick keeps PitchRate, YawRate,
	 *  TurnResponse and Grip. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Flight") float MousePitchRate = 240.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Flight") float MouseYawRate = 220.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Flight") float MouseTurnResponse = 16.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Flight") float MouseGrip = 7.f;
	/** cosmetic bank into a yaw turn (degrees at full yaw rate) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Flight") float BankAngle = 22.f;

	// ---- weapons
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Weapons") float CannonRate = 14.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Weapons") float BoltSpeed = 160000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Weapons") float BoltLife = 2.2f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Weapons") float BoltDamage = 12.f;
	/** a cylinder along Z, 100 cm tall and across (the engine's basic shape), and an unlit glowing material */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Weapons") TObjectPtr<UStaticMesh> BoltMesh;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Weapons") TObjectPtr<UMaterialInterface> BoltMaterial;
	/** bolt size: length and thickness (cm) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Weapons") FVector2D BoltSize = FVector2D(1100.f, 26.f);
	/** the cannons' fire crosses on the nose line this far ahead */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Weapons") float Convergence = 90000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Weapons") TObjectPtr<UStaticMesh> MissileMesh;
	/** turns and scales the missile mesh so that its nose is +X */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Weapons") FTransform MissileMeshTransform;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Weapons") TObjectPtr<UNiagaraSystem> MissileTrailFX;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Weapons") TObjectPtr<UParticleSystem> MissileTrailPS;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Weapons") TObjectPtr<UStaticMesh> MissileFlameMesh;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Weapons") FTransform MissileFlameTransform;
	/** a rail has a new missile this many seconds after firing */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Weapons") float MissileReload = 6.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Weapons") float MissileInterval = 0.45f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Weapons") float MissileDamage = 140.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Weapons") float MissileBlastRadius = 2600.f;
	/** lock: the target nearest the nose line within this cone and range */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Weapons") float LockAngle = 11.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Weapons") float LockRange = 450000.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Camera") int32 DustCount = 170;
	/** the specks fill a cube of this half size (cm) around the fighter; thickness (cm) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Camera") float DustRange = 6500.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Camera") float DustSize = 7.f;

	// ---- chase camera
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Camera") float CameraDistance = 1750.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Camera") float CameraHeight = 420.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Camera") FVector2D CameraDistanceRange = FVector2D(1000.f, 4500.f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Camera") float BaseFOV = 78.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Camera") float BoostFOV = 96.f;
	/** how fast the camera turns after the fighter (1/s), and the most it may trail a fast turn (degrees): the mouse
	 *  turns the fighter faster than the plain lag could keep it in view */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Camera") float CameraTurnLag = 5.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Camera") float CameraMaxTrail = 17.5f;
	/** turns the chase camera round the fighter (demo reels: yaw 180 looks back at its nose) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Camera") FRotator CameraOrbit = FRotator::ZeroRotator;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Hull") float MaxHull = 100.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Hull") float HullRegen = 6.f;
	/** hull lost in a collision: closing speed (cm/s) / this, between 2 and MaxCollisionDamage */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Hull") float CollisionDamageSpeed = 600.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Hull") float MaxCollisionDamage = 60.f;
	/** nothing harms the fighter for this long after it is launched (again) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Starship|Hull") float LaunchProtection = 3.f;

	// ---- control (the player controller, tests)
	/** ThrottleAxis -1..1 changes the throttle; Roll -1..1 (+ = right wing down); bBoost = afterburner */
	UFUNCTION(BlueprintCallable, Category = "Starship") void SetFlightInput(float ThrottleAxis, float Roll, bool bBoost);
	/** turn rates as a fraction of PitchRate / YawRate (a stick): Pitch + = nose up, Yaw + = nose right */
	UFUNCTION(BlueprintCallable, Category = "Starship") void SetTurnInput(float Pitch, float Yaw);
	/** mouse: moves the aim point by degrees (Yaw + = right, Pitch + = up) */
	UFUNCTION(BlueprintCallable, Category = "Starship") void AddAim(float YawDegrees, float PitchDegrees);
	UFUNCTION(BlueprintCallable, Category = "Starship") void SetFiring(bool bCannons) { bFiring = bCannons; }
	/** fires one missile from the next loaded rail; false when none is ready */
	UFUNCTION(BlueprintCallable, Category = "Starship") bool FireMissile();
	UFUNCTION(BlueprintCallable, Category = "Starship") void CycleTarget();
	UFUNCTION(BlueprintCallable, Category = "Starship") void ZoomCamera(float Steps);
	// ---- camera work for demo reels (the pilot script of pipeline/unreal/805)
	/** the chase camera's place: turned round the fighter by Orbit, Distance behind and Height above (0 or less: as is) */
	UFUNCTION(BlueprintCallable, Category = "Starship") void SetChaseCamera(FRotator Orbit, float Distance = 0.f, float Height = 0.f);
	/** the view from a fixed point that turns to watch the fighter go by, instead of the chase camera; Lead (s) looks
	 *  that far ahead of it along its flight */
	UFUNCTION(BlueprintCallable, Category = "Starship") void SetWatchCamera(bool bOn, FVector Point, float FOV = 40.f, float Lead = 0.f);
	/** a cut: the chase camera jumps to its place instead of swinging there */
	UFUNCTION(BlueprintCallable, Category = "Starship") void SnapCamera() { bSnapCamera = true; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") bool IsWatchCamera() const { return bWatchCamera; }
	UFUNCTION(BlueprintCallable, Category = "Starship") void Respawn();
	/** back to the start as if play had just begun, at this throttle (0 = standing), every counter at 0 (demo reels) */
	UFUNCTION(BlueprintCallable, Category = "Starship") void Relaunch(float AtThrottle);

	// ---- state (HUD, tests)
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") float GetSpeed() const { return Velocity.Size(); }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") float GetThrottle() const { return Throttle; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") float GetHull() const { return HullPoints; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") bool IsBoosting() const { return bBoosting; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") bool IsDestroyed() const { return DeadTime > 0.f; }
	/** being turned back into the arena (the player has no say over the nose meanwhile) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") bool IsReturning() const { return bReturning; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") int32 GetMissilesReady() const;
	/** seconds until the next rail is loaded (0 when all are) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") float GetMissileReloadLeft() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") ASSTarget* GetLockedTarget() const { return Locked.Get(); }
	/** aim point ahead of the nose, degrees (x = right, y = up) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") FVector2D GetAim() const { return Aim; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") FVector GetAimDirection() const;
	/** 0 = flown by stick, 1 = flown by mouse (the mouse turn rates, response and grip apply) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") float GetMouseFlight() const { return MouseFlight; }
	/** nose turn rates now, degrees a second (x = yaw to the right, y = pitch up) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") FVector2D GetTurnRates() const { return FVector2D(RateYaw, RatePitch); }
	/** where to shoot to hit the locked target with the cannons (its position when no lead is needed) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") FVector GetLeadPoint() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") ASSArena* GetArena() const { return Arena; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") int32 GetNumBolts() const { return BoltList.Num(); }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Starship") int32 GetNumContrails() const { return Contrails.Num(); }
	UPROPERTY(BlueprintReadOnly, Category = "Starship") int32 ShotsFired = 0;
	UPROPERTY(BlueprintReadOnly, Category = "Starship") int32 ShotsHit = 0;
	UPROPERTY(BlueprintReadOnly, Category = "Starship") int32 MissilesFired = 0;
	UPROPERTY(BlueprintReadOnly, Category = "Starship") int32 Collisions = 0;
	UPROPERTY(BlueprintReadOnly, Category = "Starship") int32 Respawns = 0;
	UPROPERTY(BlueprintReadOnly, Category = "Starship") int32 TurnBacks = 0;
	virtual FVector GetVelocity() const override { return Velocity; }

	virtual void Tick(float Dt) override;
	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void CalcCamera(float DeltaTime, FMinimalViewInfo& OutResult) override;

protected:
	virtual void BeginPlay() override;

private:
	struct FBolt { FVector P; FVector V; float Life; };
	TArray<FBolt> BoltList;
	TArray<FVector> DustPos;
	UPROPERTY(Transient) TObjectPtr<ASSArena> Arena;
	UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> PartComps;
	UPROPERTY(Transient) TArray<TObjectPtr<UFXSystemComponent>> Contrails;
	TWeakObjectPtr<ASSTarget> Locked;
	TArray<FVector> FlameScale;                 // base relative scale of each part (flames are stretched from it)
	TArray<float> RailReload;                   // seconds until each rail has a missile again
	FVector Velocity = FVector::ZeroVector;
	FTransform StartTransform;
	float Throttle = 0.f, HullPoints = 100.f;
	float InThrottle = 0.f, InRoll = 0.f, InPitch = 0.f, InYaw = 0.f;
	FVector2D Aim = FVector2D::ZeroVector;
	float RatePitch = 0.f, RateYaw = 0.f, RateRoll = 0.f;      // degrees a second, smoothed
	float Bank = 0.f, MouseFlight = 0.f;
	bool bWatchCamera = false, bSnapCamera = false, bCameraCut = false, bLagOff = false;
	FVector WatchPoint = FVector::ZeroVector;
	float WatchFOV = 40.f, WatchLead = 0.f;
	bool bBoosting = false, bFiring = false, bReturning = false, bManualLock = false;
	float CannonTimer = 0.f, MissileTimer = 0.f, LockTimer = 0.f, ManualLockTime = 0.f;
	int32 NextMuzzle = 0, NextRail = 0;
	float LaunchTime = 0.f;
	float LastDamageTime = -100.f, DeadTime = 0.f, Shake = 0.f, MuzzleFlash = 0.f, Knock = 0.f;

	void RebuildParts(bool bConstruction);
	void UpdateFlight(float Dt);
	void UpdateWeapons(float Dt);
	void UpdateBolts(float Dt);
	void UpdateLook(float Dt);
	void TakeHullDamage(float Damage, const FVector& At);
	void Explode();
};
