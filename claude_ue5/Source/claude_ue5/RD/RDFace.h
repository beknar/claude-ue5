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
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "GameFramework/Actor.h"
#include "RDFace.generated.h"

/** an expression channel: at full weight, each morph target's weight and each material parameter's value */
USTRUCT(BlueprintType)
struct FRDFaceChannel
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Name;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TMap<FName, float> Morphs;
	UPROPERTY(EditAnywhere, BlueprintReadWrite) TMap<FName, float> Params;
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

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
	/** one step (also from the editor's tick of a puppet) */
	void Step(float Dt);

private:
	struct FPlaying { FName Occasion; FRDFaceCue Cue; float Age = 0.f; };
	TArray<FPlaying> Playing;
	TMap<FName, float> Manual, Held, Weights, ParamValues;
	TMap<FName, int32> CueCounts;
	UPROPERTY(Transient) TArray<TObjectPtr<class UMaterialInstanceDynamic>> MIDs;
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
	virtual void Tick(float DeltaSeconds) override;
	virtual bool ShouldTickIfViewportsOnly() const override { return true; }
};
