// The horse's own animation (the user's of 2026-11-18: the Ultimate Horse Pack's horse and its clips; RDHorse15.cpp): one clip at a
// time, crossfaded from the last over a blend (a gait into another at the same point of the stride, a jump, a rear, a hit), each with
// its own time and rate. A single-node instance cuts from clip to clip, and the pack's own AnimBP is driven by its own Blueprint
// horse; this is a native instance with no graph: its proxy evaluates the two clips and blends them.
#pragma once
#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimInstanceProxy.h"
#include "RDHorseAnim.generated.h"

class UAnimSequenceBase;

/** a clip playing: its time (seconds into it), its rate (its own rate scale in), looped or held at its end */
struct FRDHorseClipPlay
{
	UAnimSequenceBase* Clip = nullptr;
	float Time = 0.f;
	float Rate = 1.f;
	bool bLoop = true;
};

USTRUCT()
struct FRDHorseAnimProxy : public FAnimInstanceProxy
{
	GENERATED_BODY()
	FRDHorseAnimProxy() {}
	FRDHorseAnimProxy(UAnimInstance* In) : FAnimInstanceProxy(In) {}
	virtual void PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds) override;
	virtual bool Evaluate(FPoseContext& Output) override;
	FRDHorseClipPlay Cur, Prev;
	float CurWeight = 1.f;
};

UCLASS(Transient, NotBlueprintable)
class CLAUDE_UE5_API URDHorseAnimInstance : public UAnimInstance
{
	GENERATED_BODY()
public:
	/** play Clip from StartTime (< 0: from the same share of the loop as the clip playing now, so a gait carries on its stride),
	 *  crossfaded over Blend seconds; the same clip again only changes its rate */
	void PlayClip(UAnimSequenceBase* Clip, bool bLoop, float Rate, float Blend, float StartTime = 0.f);
	void SetClipRate(float Rate) { Cur.Rate = Rate; }
	UAnimSequenceBase* GetClip() const { return Cur.Clip; }
	float GetClipRate() const { return Cur.Rate; }
	/** the clip's share of its loop now (0-1), and its last frame's (the hooves' landings are read between them) */
	float GetPhase() const;
	float GetPhaseBefore() const { return PhaseBefore; }
	/** a clip that does not loop has reached its end */
	bool IsClipDone() const;
	/** loops a second of the clip now at its rate (its rate scale in) */
	float GetLoopsASecond() const;
protected:
	virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override { return new FRDHorseAnimProxy(this); }
	virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy) override { delete static_cast<FRDHorseAnimProxy*>(InProxy); }
	virtual void PreUpdateAnimation(float DeltaSeconds) override;
private:
	friend struct FRDHorseAnimProxy;
	FRDHorseClipPlay Cur, Prev;
	float BlendLen = 0.f, BlendT = 0.f, PhaseBefore = 0.f;
	/** the clips held from being collected while they play */
	UPROPERTY(Transient) TObjectPtr<UAnimSequenceBase> CurRef;
	UPROPERTY(Transient) TObjectPtr<UAnimSequenceBase> PrevRef;
};
