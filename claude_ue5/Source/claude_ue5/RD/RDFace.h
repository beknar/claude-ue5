// A face that moves (docs/emotional-content.md; first on the Summoner, random_dungeonmagic_level5).
// URDFaceComponent sets a skeletal mesh's morph targets (shapes made in Blender: a smile, a frown, the brows...) and its
// materials' scalar parameters (painted patches blended in: eyes shut, an open mouth...) from expression channels. A channel
// (FRDFaceChannel, data) says how far each morph and each parameter goes at its full weight. What sets the channels:
//  - in play (bGameDriven): what happens to her, read from her combat component and the dungeon generator each tick: a
//    cue (FRDFaceCue: a channel coming in, staying and going) when she is hurt, casts or finds something; a state held
//    while it lasts (a fight near her, low hit points, death); blinks at random times from a stream of its own (the
//    play's streams are never drawn from: a reel must repeat);
//  - from outside: SetManual (tests, ARDFacePuppet's keyed properties in a sequence).
// A channel's weight is the largest of what sets it. Cues push the held states and the blinks down while they play.
//
// A MetaHuman face (FRDMetaFace; the Summoner's second face, 837-840): a MetaHuman's face mesh set on a body that is not
// a MetaHuman. The component makes it in play (or in the editor for a puppet): the face mesh attached to the body at
// Placement (her rest pose: its eyes on hers), its neck and head bones following the body's (URDMetaFaceAnimInstance: each
// face bone moves as the body bone it follows moved from its rest), its brows and lashes (grooms) on it, the body given a
// material that cuts her own face away. A channel's Curves are then the MetaHuman's control curves
// (CTRL_expressions_browDownL ...): RigLogic (the face mesh's post-process AnimBP) turns them into its joints, its blend
// shapes and its wrinkle maps.
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "GameFramework/Actor.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimInstanceProxy.h"
#include "RDFace.generated.h"

/** an expression channel: at full weight, each morph target's weight, each material parameter's value and each control
 *  curve's value (a MetaHuman face's) */
USTRUCT(BlueprintType)
struct FRDFaceChannel
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Name;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TMap<FName, float> Morphs;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TMap<FName, float> Params;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TMap<FName, float> Curves;
};

/** a groom on a MetaHuman face (hair, brows, lashes): its asset, its binding to the face mesh, a material for all its
 *  slots (none: the groom's own), scalar parameters for its material (hairMelanin: 0 blond ... 1 black) */
USTRUCT(BlueprintType)
struct FRDMetaFaceGroom
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<class UGroomAsset> Groom;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<class UGroomBindingAsset> Binding;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<class UMaterialInterface> Material;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TMap<FName, float> Scalars;
};

/** a MetaHuman's face on another body */
USTRUCT(BlueprintType)
struct FRDMetaFace
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<class USkeletalMesh> Mesh;
	/** the face mesh's place on the body mesh (component space; the body in its rest pose) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FTransform Placement;
	/** face bone -> the body bone it follows (spine_05 -> spine_04, neck_01 -> neck_01, head -> head ...) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TMap<FName, FName> Bones;
	/** given to every slot of the body (her own face cut away, her hair skull pushed over the MetaHuman's scalp) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TObjectPtr<class UMaterialInterface> BodyMaterial;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FRDMetaFaceGroom> Grooms;
	/** meshes on the body's skeleton that follow its pose (leader pose: Summoner2's bikini on her MetaHuman body) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<TObjectPtr<class USkeletalMesh>> Outfits;
	/** the face's LOD held, and its grooms' (-1: the engine's choice; 0: the full rig's blend shapes and the hair as
	 *  strands at every distance) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 ForcedLOD = 0;
};

/** the face mesh's animation: its neck and head bones following the body's, the control curves set by the face component
 *  (RigLogic, the mesh's post-process AnimBP, does the rest) */
UCLASS(Transient, NotBlueprintable)
class CLAUDE_UE5_API URDMetaFaceAnimInstance : public UAnimInstance
{
	GENERATED_BODY()
public:
	TWeakObjectPtr<class USkeletalMeshComponent> Body;
	FTransform Placement;
	TArray<TPair<FName, FName>> Bones;
	TMap<FName, float> Curves;
protected:
	virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
	virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy) override;
};

struct FRDMetaFaceProxy : public FAnimInstanceProxy
{
	FRDMetaFaceProxy() {}
	FRDMetaFaceProxy(UAnimInstance* I) : FAnimInstanceProxy(I) {}
	virtual void PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds) override;
	virtual bool Evaluate(FPoseContext& Output) override;
	// (copied on the game thread for the evaluation)
	struct FBoneMove { FName Bone; FName Parent; FTransform RefCS, ParentRefCS, Move; int32 Depth = 0; };
	TArray<FBoneMove> Moves;
	TArray<TPair<FName, float>> CurveValues;
	// (cached once: the rests)
	TWeakObjectPtr<const class USkeletalMesh> CachedFace, CachedBody;
	TMap<FName, FTransform> FaceRefCS, BodyRefCS;
	TMap<FName, FName> FaceParent;
	TMap<FName, int32> FaceDepth;
};

/** an occasion's expression: its channel, how strong, the seconds it takes to come in (FadeIn), stays (Hold), takes to go
 *  (FadeOut; names that stay plain words in Python: In would be its keyword in) (Hold < 0: held
 *  while the occasion lasts: a fight, low hit points, death) */
USTRUCT(BlueprintType)
struct FRDFaceCue
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Channel;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Weight = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float FadeIn = 0.1f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float Hold = 0.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) float FadeOut = 0.3f;
};

UCLASS(ClassGroup = (RandomDungeon), meta = (BlueprintSpawnableComponent))
class CLAUDE_UE5_API URDFaceComponent : public UActorComponent
{
	GENERATED_BODY()
public:
	URDFaceComponent();
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Face") TArray<FRDFaceChannel> Channels;
	/** by occasion: Hurt, Cast, Loot (cues); Fight, LowHealth, Death (held) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Face") TMap<FName, FRDFaceCue> Cues;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Face") FName BlinkChannel = TEXT("Blink");
	/** seconds between blinks (a random time between them) and a blink's shutting, staying shut and opening */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Face") FVector2D BlinkGap = FVector2D(2.2f, 5.5f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Face") FVector BlinkTimes = FVector(0.07f, 0.05f, 0.12f);
	/** below this share of her hit points LowHealth is held */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Face") float LowHealth = 0.3f;
	/** reacts to her combat component and the generator (off: only SetManual and the blinks) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Face") bool bGameDriven = true;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Face") bool bBlink = true;
	/** the blinks' random stream */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Face") int32 Seed = 7;

	/** a channel held at this weight from outside until set to 0 (tests, the puppet) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Face") void SetManual(FName Channel, float Weight);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Face") void ClearManual() { Manual.Reset(); }
	/** play an occasion's cue now */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Face") bool Cue(FName Occasion);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Face") float GetChannelWeight(FName Channel) const { const float* W = Weights.Find(Channel); return W ? *W : 0.f; }
	/** what was set on the mesh in the last tick */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Face") float GetMorphWeight(FName Morph) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Face") float GetParamValue(FName Param) const { const float* V = ParamValues.Find(Param); return V ? *V : 0.f; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Face") int32 GetBlinks() const { return Blinks; }
	/** how often each occasion played (tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Face") TMap<FName, int32> GetCueCounts() const { return CueCounts; }
	/** what the face shows now, by the channel with the largest weight (None: its rest) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Face") FName GetExpression() const;
	/** the mesh it moves (the owner's first skeletal mesh when not set) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Face") TObjectPtr<class USkeletalMeshComponent> Mesh;
	/** a MetaHuman face set on Mesh (made at the first step when MetaFace.Mesh is set) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Face") FRDMetaFace MetaFace;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Face") class USkeletalMeshComponent* GetFaceMesh() const { return FaceMesh; }
	/** the control curve's value given to the MetaHuman face in the last step */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Face") float GetCurveValue(FName Curve) const { const float* V = CurveValues.Find(Curve); return V ? *V : 0.f; }
	/** what the face mesh's animation evaluated for a curve (after RigLogic: 0 when the curve never reached it) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Face") float GetFaceAnimCurve(FName Curve) const;
	/** a bone of the MetaHuman face, in world space (tests: the jaw, the eyelids, the brows move) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Face") FTransform GetFaceBoneTransform(FName Bone) const;
	/** the MetaHuman face made again (a test that changed MetaFace) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Face") void RebuildMetaFace();
	/** the face mesh's animation evaluated now (its curves through RigLogic onto its joints and blend shapes): the editor
	 *  world does not tick animation, and a capture in the same Python call would see the last frame */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Face") void EvaluateFaceNow(float Dt = 0.f);
	/** one step now (tests and probes in the editor, where the component does not tick) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Face") void StepNow(float Dt) { Step(Dt); }

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
	/** one step (also from the editor's tick of a puppet) */
	void Step(float Dt);

private:
	struct FPlaying { FName Occasion; FRDFaceCue Cue; float Age = 0.f; };
	TArray<FPlaying> Playing;
	TMap<FName, float> Manual, Held, Weights, ParamValues, CurveValues;
	TMap<FName, int32> CueCounts;
	UPROPERTY(Transient) TArray<TObjectPtr<class UMaterialInstanceDynamic>> MIDs;
	UPROPERTY(Transient) TObjectPtr<class USkeletalMeshComponent> FaceMesh;
	UPROPERTY(Transient) TArray<TObjectPtr<class UGroomComponent>> FaceGrooms;
	UPROPERTY(Transient) TArray<TObjectPtr<class USkeletalMeshComponent>> FaceOutfits;
	void SetupMetaFace();
	void TearDownMetaFace();
	virtual void OnUnregister() override;
	FRandomStream Stream;
	float NextBlink = 2.f, BlinkAge = -1.f;
	int32 Blinks = 0;
	// what was seen last of her
	float SeenHurt = -100.f, SeenFound = -100.f;
	int32 SeenAttacks = -1;
	bool bStarted = false;
	void Watch(float Dt);
	void Apply();
	static float Envelope(const FRDFaceCue& C, float Age);
};

/** a skeletal mesh with a face for a sequence (the face reel): its expression channels as keyable properties, given to its
 *  face component every tick (in the editor too, to see a sequence while it is made) */
UCLASS()
class CLAUDE_UE5_API ARDFacePuppet : public AActor
{
	GENERATED_BODY()
public:
	ARDFacePuppet();
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Face") TObjectPtr<class USkeletalMeshComponent> Mesh;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Face") TObjectPtr<URDFaceComponent> Face;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "RandomDungeon|Face") float Joy = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "RandomDungeon|Face") float Anger = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "RandomDungeon|Face") float Pain = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "RandomDungeon|Face") float Fear = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "RandomDungeon|Face") float Shout = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "RandomDungeon|Face") float Focus = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "RandomDungeon|Face") float Blink = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "RandomDungeon|Face") float Dead = 0.f;
	// (more expressions for the MetaHuman face)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "RandomDungeon|Face") float Surprise = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "RandomDungeon|Face") float Sad = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "RandomDungeon|Face") float Disgust = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "RandomDungeon|Face") float Effort = 0.f;
	/** where the eyes look: +right / +up, -1..1 (the MetaHuman face's eyeLook curves) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "RandomDungeon|Face") float LookRight = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "RandomDungeon|Face") float LookUp = 0.f;
	virtual void Tick(float DeltaSeconds) override;
	virtual bool ShouldTickIfViewportsOnly() const override { return true; }
};
