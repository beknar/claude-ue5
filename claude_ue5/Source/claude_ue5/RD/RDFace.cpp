#include "RD/RDFace.h"
#include "RD/RDCombat.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDMonster.h"
#include "Components/SkeletalMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/SkeletalMesh.h"
#include "GroomComponent.h"
#include "GroomAsset.h"
#include "GroomBindingAsset.h"
#include "EngineUtils.h"

// ------------------------------------------------------------------------------------------------ the MetaHuman face's animation
FAnimInstanceProxy* URDMetaFaceAnimInstance::CreateAnimInstanceProxy() { return new FRDMetaFaceProxy(this); }
void URDMetaFaceAnimInstance::DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy) { delete static_cast<FRDMetaFaceProxy*>(InProxy); }

static void RDFaceRefCS(const USkeletalMesh* M, TMap<FName, FTransform>& CS, TMap<FName, FName>* Parent, TMap<FName, int32>* Depth)
{
	CS.Reset();
	const FReferenceSkeleton& R = M->GetRefSkeleton();
	const TArray<FTransform>& L = R.GetRefBonePose();
	TArray<FTransform> C; C.SetNum(R.GetNum()); TArray<int32> D; D.SetNum(R.GetNum());
	for (int32 I = 0; I < R.GetNum(); ++I)
	{
		const int32 P = R.GetParentIndex(I);
		C[I] = P >= 0 ? L[I] * C[P] : L[I];
		D[I] = P >= 0 ? D[P] + 1 : 0;
		CS.Add(R.GetBoneName(I), C[I]);
		if (Parent) Parent->Add(R.GetBoneName(I), P >= 0 ? R.GetBoneName(P) : NAME_None);
		if (Depth) Depth->Add(R.GetBoneName(I), D[I]);
	}
}

void FRDMetaFaceProxy::PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds)
{
	FAnimInstanceProxy::PreUpdate(InAnimInstance, DeltaSeconds);
	URDMetaFaceAnimInstance* A = Cast<URDMetaFaceAnimInstance>(InAnimInstance);
	Moves.Reset(); CurveValues.Reset();
	if (!A) return;
	for (const auto& KV : A->Curves) CurveValues.Add({ KV.Key, KV.Value });
	const USkeletalMeshComponent* Face = A->GetSkelMeshComponent();
	const USkeletalMeshComponent* Body = A->Body.Get();
	const USkeletalMesh* FM = Face ? Face->GetSkeletalMeshAsset() : nullptr;
	const USkeletalMesh* BM = Body ? Body->GetSkeletalMeshAsset() : nullptr;
	if (!FM || !BM) return;
	if (CachedFace.Get() != FM) { RDFaceRefCS(FM, FaceRefCS, &FaceParent, &FaceDepth); CachedFace = FM; }
	if (CachedBody.Get() != BM) { RDFaceRefCS(BM, BodyRefCS, nullptr, nullptr); CachedBody = BM; }
	// each face bone b moves as its body bone s moved from its rest, seen in the face's space:
	// now(b) = ref(b) * Placement * [ref(s)^-1 * now(s)] * Placement^-1   (component spaces; UE's order: left applied first)
	const FTransform& Pl = A->Placement;
	const FTransform PlInv = Pl.Inverse();
	for (const auto& BS : A->Bones)
	{
		const FTransform* FR = FaceRefCS.Find(BS.Key); const FTransform* BR = BodyRefCS.Find(BS.Value);
		const int32 BI = Body->GetBoneIndex(BS.Value);
		if (!FR || !BR || BI == INDEX_NONE) continue;
		const FTransform Now = Body->GetBoneTransform(BI, FTransform::Identity);
		if (Now.GetScale3D().GetMin() < 0.01f) continue;          // (a body not evaluated yet: the face stays in its rest)
		const FTransform Delta = BR->Inverse() * Now;
		FBoneMove Mv;
		Mv.Bone = BS.Key; Mv.Parent = FaceParent.FindRef(BS.Key); Mv.Depth = FaceDepth.FindRef(BS.Key);
		Mv.RefCS = *FR; const FTransform* PR = FaceRefCS.Find(Mv.Parent); Mv.ParentRefCS = PR ? *PR : FTransform::Identity;
		Mv.Move = Pl * Delta * PlInv;
		Moves.Add(Mv);
	}
	Moves.Sort([](const FBoneMove& X, const FBoneMove& Y) { return X.Depth < Y.Depth; });
}

bool FRDMetaFaceProxy::Evaluate(FPoseContext& Output)
{
	Output.Pose.ResetToRefPose();
	const FBoneContainer& BC = Output.Pose.GetBoneContainer();
	TMap<FName, FTransform> NewCS;
	for (const FBoneMove& Mv : Moves)
	{
		const FTransform CS = Mv.RefCS * Mv.Move;
		NewCS.Add(Mv.Bone, CS);
		const FTransform* PN = NewCS.Find(Mv.Parent);
		const FTransform ParentCS = PN ? *PN : Mv.ParentRefCS;       // (the bones above the moved ones stay in their rest)
		const int32 MeshIdx = BC.GetPoseBoneIndexForBoneName(Mv.Bone);
		if (MeshIdx == INDEX_NONE) continue;
		const FCompactPoseBoneIndex CI = BC.MakeCompactPoseIndex(FMeshPoseBoneIndex(MeshIdx));
		if (CI == INDEX_NONE) continue;
		FTransform Local = CS.GetRelativeTransform(ParentCS); Local.NormalizeRotation();
		Output.Pose[CI] = Local;
	}
	for (const auto& KV : CurveValues) Output.Curve.Set(KV.Key, KV.Value);
	return true;
}

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

void URDFaceComponent::SetupMetaFace()
{
	if (FaceMesh || !Mesh || !MetaFace.Mesh || !GetOwner()) return;
	AActor* O = GetOwner();
	FaceMesh = NewObject<USkeletalMeshComponent>(O, NAME_None, RF_Transient);
	FaceMesh->SetSkeletalMeshAsset(MetaFace.Mesh);
	FaceMesh->SetupAttachment(Mesh);
	FaceMesh->SetRelativeTransform(MetaFace.Placement);
	FaceMesh->SetAnimationMode(EAnimationMode::AnimationBlueprint);
	FaceMesh->SetAnimInstanceClass(URDMetaFaceAnimInstance::StaticClass());
	FaceMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	FaceMesh->bCastDynamicShadow = true; FaceMesh->SetCastShadow(true);
	FaceMesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
	if (MetaFace.ForcedLOD >= 0) FaceMesh->SetForcedLOD(MetaFace.ForcedLOD + 1);
	FaceMesh->RegisterComponent();
	FaceMesh->AddTickPrerequisiteComponent(Mesh);           // (her pose first: the face follows it the same frame)
	if (URDMetaFaceAnimInstance* A = Cast<URDMetaFaceAnimInstance>(FaceMesh->GetAnimInstance()))
	{
		A->Body = Mesh; A->Placement = MetaFace.Placement;
		for (const auto& KV : MetaFace.Bones) A->Bones.Add({ KV.Key, KV.Value });
	}
	for (const FRDMetaFaceGroom& G : MetaFace.Grooms)
	{
		if (!G.Groom) continue;
		UGroomComponent* GC = NewObject<UGroomComponent>(O, NAME_None, RF_Transient);
		GC->SetupAttachment(FaceMesh);
		GC->SetGroomAsset(G.Groom, G.Binding);
		GC->RegisterComponent();
		if (MetaFace.ForcedLOD >= 0) GC->SetForcedLOD(MetaFace.ForcedLOD);   // (strands at every distance, not cards)
		if (G.Material)
			for (int32 I = 0; I < GC->GetNumMaterials(); ++I) GC->SetMaterial(I, G.Material);
		if (G.Scalars.Num() > 0)
			for (int32 I = 0; I < GC->GetNumMaterials(); ++I)
				if (UMaterialInstanceDynamic* D = GC->CreateDynamicMaterialInstance(I))
					for (const auto& S : G.Scalars) D->SetScalarParameterValue(S.Key, S.Value);
		FaceGrooms.Add(GC);
	}
	if (MetaFace.BodyMaterial)
		for (int32 I = 0; I < Mesh->GetNumMaterials(); ++I) Mesh->SetMaterial(I, MetaFace.BodyMaterial);
	for (USkeletalMesh* OM : MetaFace.Outfits)
	{
		if (!OM) continue;
		USkeletalMeshComponent* C = NewObject<USkeletalMeshComponent>(O, NAME_None, RF_Transient);
		C->SetSkeletalMeshAsset(OM);
		C->SetupAttachment(Mesh);
		C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		C->SetCastShadow(true);
		C->RegisterComponent();
		C->SetLeaderPoseComponent(Mesh);
		FaceOutfits.Add(C);
	}
}

void URDFaceComponent::TearDownMetaFace()
{
	for (UGroomComponent* G : FaceGrooms) if (G) G->DestroyComponent();
	FaceGrooms.Reset();
	for (USkeletalMeshComponent* C : FaceOutfits) if (C) C->DestroyComponent();
	FaceOutfits.Reset();
	if (FaceMesh) FaceMesh->DestroyComponent();
	FaceMesh = nullptr;
}

void URDFaceComponent::RebuildMetaFace() { TearDownMetaFace(); SetupMetaFace(); }

void URDFaceComponent::EvaluateFaceNow(float Dt)
{
	if (!FaceMesh) return;
	// (her body is left as it is: refreshed here in the editor with no animation, its bones collapsed to the origin and
	// the face followed them)
	FaceMesh->TickAnimation(Dt, false);
	FaceMesh->RefreshBoneTransforms();            // (no tick function: evaluated here, curves applied to the blend shapes)
	FaceMesh->MarkRenderDynamicDataDirty();
}

void URDFaceComponent::OnUnregister()
{
	TearDownMetaFace();
	Super::OnUnregister();
}

float URDFaceComponent::GetFaceAnimCurve(FName Curve) const
{
	const UAnimInstance* A = FaceMesh ? FaceMesh->GetAnimInstance() : nullptr;
	if (!A) return 0.f;
	float V = 0.f;
	if (const UAnimInstance* PP = FaceMesh->GetPostProcessInstance()) if (PP->GetCurveValue(Curve, V)) return V;
	A->GetCurveValue(Curve, V);
	return V;
}

FTransform URDFaceComponent::GetFaceBoneTransform(FName Bone) const
{
	return (FaceMesh && FaceMesh->GetBoneIndex(Bone) != INDEX_NONE) ? FaceMesh->GetSocketTransform(Bone) : FTransform::Identity;
}

void URDFaceComponent::Step(float Dt)
{
	if (!Mesh) Mesh = GetOwner() ? GetOwner()->FindComponentByClass<USkeletalMeshComponent>() : nullptr;
	if (!Mesh) return;
	if (MetaFace.Mesh && !FaceMesh) SetupMetaFace();
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
	TMap<FName, float> Morph, Param, Curve;
	for (const FRDFaceChannel& C : Channels)
	{
		const float Wc = Weights.FindRef(C.Name);
		for (const auto& M : C.Morphs) Morph.FindOrAdd(M.Key) += M.Value * Wc;
		for (const auto& P : C.Params) Param.FindOrAdd(P.Key) += P.Value * Wc;
		for (const auto& K : C.Curves) Curve.FindOrAdd(K.Key) += K.Value * Wc;
	}
	if (FaceMesh)
	{
		CurveValues.Reset();
		for (const auto& K : Curve) CurveValues.Add(K.Key, FMath::Clamp(K.Value, 0.f, 1.f));
		if (URDMetaFaceAnimInstance* A = Cast<URDMetaFaceAnimInstance>(FaceMesh->GetAnimInstance())) A->Curves = CurveValues;
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
	                                             { TEXT("Shout"), Shout }, { TEXT("Focus"), Focus }, { TEXT("Blink"), Blink }, { TEXT("Dead"), Dead },
	                                             { TEXT("Surprise"), Surprise }, { TEXT("Sad"), Sad }, { TEXT("Disgust"), Disgust }, { TEXT("Effort"), Effort },
	                                             { TEXT("LookRight"), FMath::Max(LookRight, 0.f) }, { TEXT("LookLeft"), FMath::Max(-LookRight, 0.f) },
	                                             { TEXT("LookUp"), FMath::Max(LookUp, 0.f) }, { TEXT("LookDown"), FMath::Max(-LookUp, 0.f) } };
	for (const auto& K : Keys) Face->SetManual(FName(K.Key), K.Value);
	// (in the editor the component does not tick and the face mesh's animation is not evaluated: do both here)
	if (!GetWorld() || !GetWorld()->IsGameWorld()) { Face->Step(DeltaSeconds); Face->EvaluateFaceNow(DeltaSeconds); }
}
