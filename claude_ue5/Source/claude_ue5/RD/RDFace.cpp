#include "RD/RDFace.h"
#include "RD/RDCombat.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDMonster.h"
#include "Components/SkeletalMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "EngineUtils.h"

URDFaceComponent::URDFaceComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_PrePhysics;
}

void URDFaceComponent::BeginPlay()
{
	Super::BeginPlay();
	Stream.Initialize(Seed);
	NextBlink = Stream.FRandRange(BlinkGap.X, BlinkGap.Y);
}

void URDFaceComponent::SetManual(FName Channel, float Weight)
{
	if (Weight <= 0.f) Manual.Remove(Channel); else Manual.Add(Channel, FMath::Clamp(Weight, 0.f, 1.f));
}

bool URDFaceComponent::Cue(FName Occasion)
{
	const FRDFaceCue* C = Cues.Find(Occasion);
	if (!C || C->Hold < 0.f) return false;
	Playing.RemoveAll([&](const FPlaying& P) { return P.Occasion == Occasion; });     // (again from the start)
	Playing.Add({ Occasion, *C, 0.f });
	CueCounts.FindOrAdd(Occasion)++;
	return true;
}

float URDFaceComponent::Envelope(const FRDFaceCue& C, float Age)
{
	if (Age < 0.f) return 0.f;
	if (Age < C.FadeIn) return C.Weight * FMath::SmoothStep(0.f, 1.f, Age / FMath::Max(C.FadeIn, 1e-3f));
	if (Age < C.FadeIn + C.Hold) return C.Weight;
	const float T = (Age - C.FadeIn - C.Hold) / FMath::Max(C.FadeOut, 1e-3f);
	return T >= 1.f ? 0.f : C.Weight * (1.f - FMath::SmoothStep(0.f, 1.f, T));
}

float URDFaceComponent::GetMorphWeight(FName Morph) const
{
	return Mesh ? Mesh->GetMorphTarget(Morph) : 0.f;
}

FName URDFaceComponent::GetExpression() const
{
	FName Best = NAME_None; float W = 0.05f;
	for (const auto& KV : Weights) if (KV.Value > W) { W = KV.Value; Best = KV.Key; }
	return Best;
}

void URDFaceComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	Step(DeltaTime);
}

void URDFaceComponent::Watch(float Dt)
{
	const AActor* O = GetOwner();
	const URDCombatComponent* Cb = O ? O->FindComponentByClass<URDCombatComponent>() : nullptr;
	if (!Cb) return;
	// cues: she was hurt, she cast, she found something (each read as a change since the last tick)
	if (Cb->LastHurtTime > SeenHurt + 1e-3f) { if (bStarted && !Cb->IsDead()) Cue(TEXT("Hurt")); SeenHurt = Cb->LastHurtTime; }
	if (Cb->AttacksMade != SeenAttacks)
	{
		if (bStarted && SeenAttacks >= 0 && Cb->AttacksMade > SeenAttacks) Cue(TEXT("Cast"));
		SeenAttacks = Cb->AttacksMade;
	}
	ARDDungeonGenerator* G = nullptr;
	for (TActorIterator<ARDDungeonGenerator> It(GetWorld()); It; ++It) { G = *It; break; }
	if (G && G->LastFoundTime > SeenFound + 1e-3f) { if (bStarted) Cue(TEXT("Loot")); SeenFound = G->LastFoundTime; }
	bStarted = true;
	// held: a monster near her after her (the fight), low hit points, death
	bool bFight = false;
	if (G && O && !Cb->IsDead())
	{
		const float D2 = FMath::Square(G->CombatMusicDistance);
		for (const ARDMonster* M : G->GetMonsters())
			if (M && !M->IsDead() && M->IsAggro() && FVector::DistSquared(M->GetActorLocation(), O->GetActorLocation()) < D2) { bFight = true; break; }
	}
	const bool bLow = !Cb->IsDead() && Cb->GetHealth() < Cb->GetMaxHealth() * LowHealth;
	auto Hold = [&](FName Occ, bool bOn)
	{
		const FRDFaceCue* C = Cues.Find(Occ);
		if (!C) return;
		float& W = Held.FindOrAdd(C->Channel);
		const float Rate = bOn ? 1.f / FMath::Max(C->FadeIn, 1e-3f) : 1.f / FMath::Max(C->FadeOut, 1e-3f);
		W = FMath::FInterpConstantTo(W, bOn ? C->Weight : 0.f, Dt, Rate * C->Weight);
		if (bOn && W > 0.f) CueCounts.FindOrAdd(Occ) = FMath::Max(CueCounts.FindRef(Occ), 1);
	};
	Hold(TEXT("Fight"), bFight); Hold(TEXT("LowHealth"), bLow); Hold(TEXT("Death"), Cb->IsDead());
	if (Cb->IsDead()) Playing.Reset();
}

void URDFaceComponent::Step(float Dt)
{
	if (!Mesh) Mesh = GetOwner() ? GetOwner()->FindComponentByClass<USkeletalMeshComponent>() : nullptr;
	if (!Mesh) return;
	if (bGameDriven && GetWorld() && GetWorld()->IsGameWorld()) Watch(Dt);
	// the cues
	float CueTop = 0.f;
	TMap<FName, float> W;
	for (int32 I = Playing.Num() - 1; I >= 0; --I)
	{
		FPlaying& P = Playing[I];
		P.Age += Dt;
		const float E = Envelope(P.Cue, P.Age);
		if (P.Age > P.Cue.FadeIn + P.Cue.Hold + P.Cue.FadeOut) { Playing.RemoveAt(I); continue; }
		W.FindOrAdd(P.Cue.Channel) = FMath::Max(W.FindRef(P.Cue.Channel), E);
		CueTop = FMath::Max(CueTop, E);
	}
	// the held states, pushed down while a cue plays
	for (const auto& KV : Held) W.FindOrAdd(KV.Key) = FMath::Max(W.FindRef(KV.Key), KV.Value * (1.f - CueTop));
	for (const auto& KV : Manual) W.FindOrAdd(KV.Key) = FMath::Max(W.FindRef(KV.Key), KV.Value);
	// a blink now and then (not while the eyes show something else: a cue, a held state, death)
	float Busy = 0.f;
	for (const auto& KV : W) if (KV.Key != BlinkChannel) Busy = FMath::Max(Busy, KV.Value);
	if (bBlink)
	{
		if (BlinkAge >= 0.f)
		{
			BlinkAge += Dt;
			const float A = BlinkTimes.X, H = BlinkTimes.Y, B = BlinkTimes.Z;
			const float E = BlinkAge < A ? BlinkAge / A : BlinkAge < A + H ? 1.f : FMath::Max(0.f, 1.f - (BlinkAge - A - H) / B);
			if (BlinkAge > A + H + B) BlinkAge = -1.f;
			W.FindOrAdd(BlinkChannel) = FMath::Max(W.FindRef(BlinkChannel), E * (1.f - Busy));
		}
		else if ((NextBlink -= Dt) <= 0.f)
		{
			NextBlink = Stream.FRandRange(BlinkGap.X, BlinkGap.Y);
			if (Busy < 0.3f) { BlinkAge = 0.f; ++Blinks; }
		}
	}
	Weights = W;
	Apply();
}

void URDFaceComponent::Apply()
{
	TMap<FName, float> Morph, Param;
	for (const FRDFaceChannel& C : Channels)
	{
		const float Wc = Weights.FindRef(C.Name);
		for (const auto& M : C.Morphs) Morph.FindOrAdd(M.Key) += M.Value * Wc;
		for (const auto& P : C.Params) Param.FindOrAdd(P.Key) += P.Value * Wc;
	}
	for (const auto& M : Morph) Mesh->SetMorphTarget(M.Key, FMath::Clamp(M.Value, 0.f, 1.f), false);
	if (Param.Num() > 0)
	{
		if (MIDs.Num() == 0)
			for (int32 I = 0; I < Mesh->GetNumMaterials(); ++I)
				if (UMaterialInstanceDynamic* D = Mesh->CreateAndSetMaterialInstanceDynamic(I)) MIDs.Add(D);
		for (const auto& P : Param)
		{
			const float V = FMath::Clamp(P.Value, 0.f, 1.f);
			ParamValues.Add(P.Key, V);
			for (UMaterialInstanceDynamic* D : MIDs) if (D) D->SetScalarParameterValue(P.Key, V);
		}
	}
}

// ------------------------------------------------------------------------------------------------ the puppet
ARDFacePuppet::ARDFacePuppet()
{
	PrimaryActorTick.bCanEverTick = true;
	Mesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Mesh"));
	RootComponent = Mesh;
	Face = CreateDefaultSubobject<URDFaceComponent>(TEXT("Face"));
	Face->bGameDriven = false;
	Face->bBlink = false;          // (the sequence keys the blinks: a render repeats)
}

void ARDFacePuppet::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!Face) return;
	Face->Mesh = Mesh;
	const TPair<const TCHAR*, float> Keys[] = { { TEXT("Joy"), Joy }, { TEXT("Anger"), Anger }, { TEXT("Pain"), Pain }, { TEXT("Fear"), Fear },
	                                             { TEXT("Shout"), Shout }, { TEXT("Focus"), Focus }, { TEXT("Blink"), Blink }, { TEXT("Dead"), Dead } };
	for (const auto& K : Keys) Face->SetManual(FName(K.Key), K.Value);
	// (in the editor the component does not tick: step it here)
	if (!GetWorld() || !GetWorld()->IsGameWorld()) Face->Step(DeltaSeconds);
}
