// The horse's own animation: see RDHorseAnim.h.
#include "RD/RDHorseAnim.h"
#include "Animation/AnimSequenceBase.h"
#include "Animation/AnimationPoseData.h"
#include "AnimationRuntime.h"

namespace
{
	float RDHorseClipLen(const UAnimSequenceBase* C) { return C ? FMath::Max(C->GetPlayLength(), 0.001f) : 1.f; }

	// (a clip's time moved on by Dt at its rate and its own rate scale: looped round its length, or held at its ends)
	void RDHorseAdvance(FRDHorseClipPlay& P, float Dt)
	{
		if (!P.Clip) return;
		const float L = RDHorseClipLen(P.Clip);
		P.Time += Dt * P.Rate * P.Clip->RateScale;
		if (P.bLoop) { P.Time = FMath::Fmod(P.Time, L); if (P.Time < 0.f) P.Time += L; }
		else P.Time = FMath::Clamp(P.Time, 0.f, L);
	}
}

void URDHorseAnimInstance::PlayClip(UAnimSequenceBase* Clip, bool bLoop, float Rate, float Blend, float StartTime)
{
	if (!Clip) return;
	// (the same loop asked again (the gaits, every tick): only its rate; the same one-off asked again (a second hit, a landing on
	// a landing): played again from its start, or it stayed on its last frame (PR #93's review))
	if (Clip == Cur.Clip && bLoop == Cur.bLoop && (bLoop || StartTime < 0.f)) { Cur.Rate = Rate; return; }
	// (from the same share of the loop: every gait's loop is a stride, so the legs carry on from where they were)
	float T = StartTime;
	if (T < 0.f) T = Cur.Clip && Cur.bLoop ? GetPhase() * RDHorseClipLen(Clip) : 0.f;
	// (a reversed clip (a rate scale under 0: the pack's backing) starts at its end)
	if (StartTime == 0.f && Clip->RateScale * Rate < 0.f) T = RDHorseClipLen(Clip);
	if (Cur.Clip && Blend > 0.f) { Prev = Cur; BlendLen = Blend; BlendT = 0.f; }
	else { Prev = FRDHorseClipPlay(); BlendLen = 0.f; }
	Cur.Clip = Clip; Cur.Time = T; Cur.Rate = Rate; Cur.bLoop = bLoop;
	PhaseBefore = GetPhase();
	CurRef = Clip; PrevRef = Prev.Clip;
}

float URDHorseAnimInstance::GetPhase() const
{
	return Cur.Clip ? FMath::Clamp(Cur.Time / RDHorseClipLen(Cur.Clip), 0.f, 1.f) : 0.f;
}

bool URDHorseAnimInstance::IsClipDone() const
{
	if (!Cur.Clip || Cur.bLoop) return false;
	const float L = RDHorseClipLen(Cur.Clip);
	return Cur.Rate * Cur.Clip->RateScale >= 0.f ? Cur.Time >= L - 1e-3f : Cur.Time <= 1e-3f;
}

float URDHorseAnimInstance::GetLoopsASecond() const
{
	return Cur.Clip ? FMath::Abs(Cur.Rate * Cur.Clip->RateScale) / RDHorseClipLen(Cur.Clip) : 0.f;
}

void URDHorseAnimInstance::PreUpdateAnimation(float DeltaSeconds)
{
	// (the times moved on here, on the game thread, before the proxy copies them for this frame's pose)
	PhaseBefore = GetPhase();
	RDHorseAdvance(Cur, DeltaSeconds);
	if (Prev.Clip)
	{
		RDHorseAdvance(Prev, DeltaSeconds);
		BlendT += DeltaSeconds;
		if (BlendT >= BlendLen) { Prev = FRDHorseClipPlay(); PrevRef = nullptr; }
	}
	Super::PreUpdateAnimation(DeltaSeconds);
}

void FRDHorseAnimProxy::PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds)
{
	FAnimInstanceProxy::PreUpdate(InAnimInstance, DeltaSeconds);
	const URDHorseAnimInstance* I = CastChecked<URDHorseAnimInstance>(InAnimInstance);
	Cur = I->Cur; Prev = I->Prev;
	// (eased in: smooth at both ends of the blend)
	const float A = I->Prev.Clip && I->BlendLen > 0.f ? FMath::Clamp(I->BlendT / I->BlendLen, 0.f, 1.f) : 1.f;
	CurWeight = FMath::SmoothStep(0.f, 1.f, A);
}

bool FRDHorseAnimProxy::Evaluate(FPoseContext& Output)
{
	auto Pose = [](const FRDHorseClipPlay& P, FPoseContext& Into)
	{
		FAnimationPoseData Data(Into);
		const FAnimExtractContext Ctx(static_cast<double>(P.Time), false, FDeltaTimeRecord(), P.bLoop);
		P.Clip->GetAnimationPose(Data, Ctx);
	};
	if (!Cur.Clip) { Output.ResetToRefPose(); return true; }
	if (!Prev.Clip || CurWeight >= 0.999f) { Pose(Cur, Output); return true; }
	FPoseContext A(Output), B(Output);
	Pose(Cur, A); Pose(Prev, B);
	FAnimationPoseData DA(A), DB(B), DOut(Output);
	FAnimationRuntime::BlendTwoPosesTogether(DA, DB, CurWeight, DOut);
	return true;
}
