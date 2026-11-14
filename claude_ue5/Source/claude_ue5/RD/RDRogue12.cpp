// The Rogue's arts (the user's list of 2026-11-12, docs/improvements12.txt, its seventh phase: "implement the following abilities
// for the rogue, assign whether they use up dex, if they use damage, and assign VFX or new animations, or new models and textures
// if they need them, and scale their effectiveness from tiers 1-30"; SourceArt/balance/rogue12.json, 925). Each is a secondary
// ability of hers (FRDSecondaryDef with a Slot): learned from its manual, found at its place among the dungeons' tiers as the Mage
// finds a tome (TomeSpellOf: for her, the place's art until she knows it), made from the quick bar ("@<Name>") with a cooldown,
// paid in dexterity energy. Those that do damage take it from her own weapons (her blade's or her crossbow's blow, as her growth
// makes it: they grow as her weapons do); the control effects keep their numbers, as her stealth does. What they leave in the world
// are ARDArtProps (RDRogue12.h). The sixteen, by their places:
//   1 Caltrops (Mistward 1)        spikes over 3 m: monsters crossing them slowed 40 % and bleeding
//   3 Smoke Bomb (Mistward 3)      a 4 m cloud: monsters inside lose her for 4 s; no dexterity energy spent
//   5 Hamstring (Mistward 5)       a cut of her blade: its monster slowed 60 % for 5 s
//   7 Marked for Death (VM 2)      her monster takes 30 % more from her for 10 s, a red crosshair over its head
//   9 Grappling Hook (VM 4)        a hook to a wall or a monster within 20 m: she is pulled to it along its rope
//  11 Acid Flask (WE 1)            a thrown vial: a 3 m pool that eats armour (25 % more taken) and burns
//  13 Ricochet Bolt (WE 3)         a crossbow bolt bouncing between up to 4 monsters
//  14 Shadow Double (WE 4)         a smoky copy of her that draws the monsters near it for 6 s, then bursts
//  17 Net Shot (Sewers 2)          a net shot over one monster: rooted 4 s
//  19 Fan of Knives (Sewers 4)     8 knives thrown in a ring: everything within 6 m round her struck
//  21 Flashbang (Kethrys 1)        a white flash: monsters within 6 m blinded and stunned 3 s
//  23 Shadowstep (Kethrys 3)       to her monster's back in black ash, a backstab with her ambush bonus
//  26 Gilded Lure (Heaven 1)       a tossed coin: monsters within 15 m go after it for 5 s
//  27 Vanishing Act (Heaven 2)     12 s of stealth that her first three blows do not end, a heat-haze shimmer round her
//  28 Death Lotus (Heaven 3)       she spins: everything within 3 m struck three times, silver crescents and afterimages
//  29 Thousand Cuts (Heaven 4)     her last: every monster she sees within 20 m marked, time slowed, then she blinks from one to the
//                                  next and cuts each
#include "RD/RDRogue12.h"
#include "RD/RDCombat.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDMonster.h"
#include "RD/RDGameInstance.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PoseableMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "NiagaraFunctionLibrary.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/RootMotionSource.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/PlayerController.h"
#include "Camera/PlayerCameraManager.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "CollisionQueryParams.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDRogue12, Log, All);

namespace
{
	const FName RDArtCaltrops(TEXT("Caltrops")), RDArtSmoke(TEXT("SmokeBomb")), RDArtHamstring(TEXT("Hamstring")), RDArtMarked(TEXT("MarkedForDeath")),
		RDArtHook(TEXT("GrapplingHook")), RDArtAcid(TEXT("AcidFlask")), RDArtRicochet(TEXT("RicochetBolt")), RDArtDouble(TEXT("ShadowDouble")),
		RDArtNet(TEXT("NetShot")), RDArtFan(TEXT("FanOfKnives")), RDArtFlash(TEXT("Flashbang")), RDArtStep(TEXT("Shadowstep")),
		RDArtLure(TEXT("GildedLure")), RDArtVanish(TEXT("VanishingAct")), RDArtLotus(TEXT("DeathLotus")), RDArtCuts(TEXT("ThousandCuts"));
	/** an art's number (its first rank: an art has one) */
	float RDArtNum(const TArray<float>& A, float Default = 0.f) { return A.Num() > 0 ? A[0] : Default; }
	/** a stream of its own for where its pieces lie (never the play's) */
	uint32 RDArtHash(uint32 A, uint32 B) { return HashCombine(A * 2654435761u, B + 0x9E3779B9u); }
}

// ================================================================================================ the props
ARDArtProp::ARDArtProp()
{
	PrimaryActorTick.bCanEverTick = true;
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;
	SetActorEnableCollision(false);
}

UStaticMeshComponent* ARDArtProp::AddMesh(UStaticMesh* M, const FTransform& Rel, UMaterialInterface* Mat)
{
	if (!M) return nullptr;
	UStaticMeshComponent* Mc = NewObject<UStaticMeshComponent>(this);
	Mc->SetStaticMesh(M);
	Mc->SetupAttachment(Root);
	Mc->SetRelativeTransform(Rel);
	Mc->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mc->SetCastShadow(Kind != ERDArtProp::Acid && Kind != ERDArtProp::Mark);
	if (Mat) for (int32 I = 0; I < Mc->GetNumMaterials(); ++I) Mc->SetMaterial(I, Mat);
	Mc->RegisterComponent();
	Meshes.Add(Mc);
	return Mc;
}

UNiagaraComponent* ARDArtProp::AddFx(UNiagaraSystem* S, const FVector& Rel, float Scale, const FLinearColor& Tint, bool bTint)
{
	if (!S) return nullptr;
	// (what flies takes its effect along, attached; what lies on the ground has its effect spawned in the world where it lies (ShockWaves'
	// smoke attached to a prop drew nothing, spawned in the world it drew its cloud), taken away with the prop (EndPlay))
	UNiagaraComponent* Fc = Kind == ERDArtProp::Flying
		? UNiagaraFunctionLibrary::SpawnSystemAttached(S, Root, NAME_None, Rel, FRotator::ZeroRotator, FVector(1.f), EAttachLocation::KeepRelativeOffset, false, ENCPoolMethod::None, true, false)
		: UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, S, GetActorLocation() + GetActorRotation().RotateVector(Rel), GetActorRotation(), FVector(1.f), false, true, ENCPoolMethod::None, false);          // (no pre-cull: one spawned out of view at that moment (at her feet, under the camera) was culled for good)
	if (!Fc) return nullptr;
	if (!FMath::IsNearlyEqual(Scale, 1.f)) Fc->SetFloatParameter(TEXT("User.Scale"), Scale);
	if (bTint) { Fc->SetColorParameter(TEXT("User.Color"), Tint); Fc->SetColorParameter(TEXT("Color"), Tint); }
	Fc->Activate(true);
	Fxs.Add(Fc);
	return Fc;
}

void ARDArtProp::EndPlay(const EEndPlayReason::Type Reason)
{
	// (its effects spawned in the world go with it)
	for (UNiagaraComponent* F : Fxs) if (IsValid(F) && F->GetOwner() != this) F->DestroyComponent();
	Fxs.Reset();
	Super::EndPlay(Reason);
}

void ARDArtProp::CopyPose(USkeletalMeshComponent* Src, UMaterialInterface* Mat)
{
	if (!Src || !Src->GetSkeletalMeshAsset()) return;
	Pose = NewObject<UPoseableMeshComponent>(this);
	Pose->SetSkinnedAssetAndUpdate(Src->GetSkeletalMeshAsset());
	Pose->SetupAttachment(Root);
	Pose->SetWorldTransform(Src->GetComponentTransform());
	Pose->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Pose->RegisterComponent();
	Pose->SetWorldTransform(Src->GetComponentTransform());
	Pose->CopyPoseFromSkeletalComponent(Src);
	if (Mat) for (int32 I = 0; I < Pose->GetNumMaterials(); ++I) Pose->SetMaterial(I, Mat);
}

void ARDArtProp::Land()
{
	ARDDungeonGenerator* G = Gen.Get();
	URDCombatComponent* Pc = G ? G->GetPlayerCombat() : nullptr;
	const FRDSecondaryDef* D = G ? G->FindSecondary(Art) : nullptr;
	UWorld* W = GetWorld();
	if (!G || !Pc || !D || !W) { Destroy(); return; }
	const float Now = W->GetTimeSeconds();
	ARDMonster* Mo = Target.Get();
	if (Art == RDArtAcid)
	{
		// (the vial breaks: its glass, then a bubbling pool where it fell)
		if (D->Fx) Pc->SpawnFx(D->Fx, To, FRotator::ZeroRotator, D->FxScale);
		Pc->SpawnArtProp(*D, (uint8)ERDArtProp::Acid, To);
		Destroy(); return;
	}
	if (Art == RDArtNet)
	{
		// (over the monster: rooted where it stands, the net wrapped round it while it holds)
		if (Mo && !Mo->IsDead())
		{
			const float S = RDArtNum(D->Seconds, 4.f);
			Mo->SlowFor(1.f, S);
			++Reached;
			Kind = ERDArtProp::Mark; Follow = Mo; Until = Now + S; Spin = 0.f;
			const float R = Mo->GetCapsuleComponent()->GetScaledCapsuleRadius();
			for (UStaticMeshComponent* M : Meshes) if (M && M->GetStaticMesh()) M->SetRelativeScale3D(FVector(FMath::Max(R * 2.6f, 80.f) / FMath::Max((float)M->GetStaticMesh()->GetBoundingBox().GetSize().GetMax(), 1.f)));
			return;
		}
		Destroy(); return;
	}
	if (Art == RDArtLure)
	{
		// (the coin on the floor: the monsters near it go after it)
		Kind = ERDArtProp::Coin; bDecoy = true; Radius = (D->Share > 0.f ? D->Share : 15.f) * 100.f; Until = Now + RDArtNum(D->Seconds, 5.f);
		if (D->Fx2) AddFx(D->Fx2, FVector(0, 0, 12.f), D->FxScale);
		return;
	}
	if (Art == RDArtRicochet)
	{
		// (at its monster: struck, sparks; on to the next, else gone)
		if (Mo && !Mo->IsDead()) { Pc->ArtHit(Mo, A); ++Reached; if (D->Fx2) Pc->SpawnFx(D->Fx2, Mo->GetActorLocation(), FRotator::ZeroRotator, D->FxScale); }
		while (Next.Num() > 0 && (!Next[0].IsValid() || Next[0]->IsDead())) Next.RemoveAt(0);
		if (Next.Num() > 0)
		{
			Target = Next[0]; Next.RemoveAt(0);
			From = GetActorLocation(); To = Target->GetActorLocation(); FlyT = 0.f;
			FlyTime = FMath::Max(FVector::Dist(From, To) / 3500.f, 0.06f);
			SetActorRotation((To - From).Rotation());
			return;
		}
		Destroy(); return;
	}
	Destroy();
}

void ARDArtProp::Tick(float Dt)
{
	Super::Tick(Dt);
	UWorld* W = GetWorld();
	ARDDungeonGenerator* G = Gen.Get();
	if (!W || !G) { Destroy(); return; }
	const float Now = W->GetTimeSeconds();
	if (Kind == ERDArtProp::Flying)
	{
		// (along its way, an arc over it for a throw, turning as it flies; where it is going moves with its monster)
		if (ARDMonster* Mo = Target.Get(); Mo && !Mo->IsDead()) To = Mo->GetActorLocation();
		FlyT += Dt;
		const float U = FMath::Clamp(FlyT / FMath::Max(FlyTime, 0.01f), 0.f, 1.f);
		FVector P = FMath::Lerp(From, To, U); P.Z += Arc * 4.f * U * (1.f - U);
		SetActorLocation(P);
		if (Spin != 0.f) AddActorLocalRotation(FRotator(0.f, 0.f, Spin * Dt));
		else if (!(To - From).IsNearlyZero()) SetActorRotation((To - From).Rotation());
		if (U >= 1.f) Land();
		return;
	}
	if (Now > Until)
	{
		// (the double bursts as it goes: the monsters within its burst struck)
		if (Kind == ERDArtProp::Double)
			if (URDCombatComponent* Pc = G->GetPlayerCombat())
			{
				if (const FRDSecondaryDef* D = G->FindSecondary(Art); D && D->Fx2) Pc->SpawnFx(D->Fx2, GetActorLocation(), FRotator::ZeroRotator, D->FxScale);
				for (ARDMonster* Mo : G->GetMonsters())
					if (IsValid(Mo) && !Mo->IsDead() && !Mo->IsAlly() && FVector::Dist(Mo->GetActorLocation(), GetActorLocation()) < B) { Pc->ArtHit(Mo, A); ++Reached; }
			}
		Destroy(); return;
	}
	// (what follows a monster: a crosshair over its head turning; the net round it)
	if (Kind == ERDArtProp::Mark)
	{
		AActor* F = Follow.Get();
		ARDMonster* Mo = Cast<ARDMonster>(F);
		if (!F || (Mo && Mo->IsDead())) { Destroy(); return; }
		const float Hh = Mo ? Mo->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() : 90.f;
		SetActorLocation(F->GetActorLocation() + FVector(0, 0, Art == RDArtNet ? -Hh * 0.2f : Hh + 55.f));
		if (Art != RDArtNet)
		{
			Spin += 120.f * Dt;
			const APlayerCameraManager* Cm = UGameplayStatics::GetPlayerCameraManager(this, 0);
			const FVector ToCam = Cm ? (Cm->GetCameraLocation() - GetActorLocation()).GetSafeNormal() : FVector::UpVector;
			SetActorRotation(FRotationMatrix::MakeFromZ(ToCam).Rotator());
			AddActorLocalRotation(FRotator(0.f, Spin, 0.f));
		}
		return;
	}
	// (the rope: from her hand to the hook)
	if (Kind == ERDArtProp::Rope)
	{
		URDCombatComponent* Pc = G->GetPlayerCombat();
		const ACharacter* Her = Pc ? Cast<ACharacter>(Pc->GetOwner()) : nullptr;
		const USkeletalMeshComponent* Body = Her ? Her->GetMesh() : nullptr;
		const FVector Hand = Body ? Body->GetSocketLocation(TEXT("hand_l")) : GetActorLocation();
		const FVector Way = To - Hand; const float Len = Way.Size();
		SetActorLocationAndRotation(Hand, FRotationMatrix::MakeFromZ(Way.GetSafeNormal()).Rotator());
		if (Meshes.Num() > 0 && Meshes[0]) { Meshes[0]->SetRelativeLocation(FVector(0, 0, Len * 0.5f)); Meshes[0]->SetRelativeScale3D(FVector(0.025f, 0.025f, Len / 100.f)); }
		if (Meshes.Num() > 1 && Meshes[1]) Meshes[1]->SetRelativeLocation(FVector(0, 0, Len));
		return;
	}
	if (Kind == ERDArtProp::Afterimage)
	{
		// (fading: shrinking out of sight over its life)
		if (Pose) Pose->SetRelativeScale3D(FVector(FMath::Clamp((Until - Now) / 0.45f, 0.05f, 1.f) * 0.15f + 0.85f));
		return;
	}
	if (Kind == ERDArtProp::Flash)
	{
		if (Light) Light->SetIntensity(FMath::Square(FMath::Max(0.f, (Until - Now) / 0.5f)) * 6000.f);
		if (Meshes.Num() > 0 && Meshes[0]) Meshes[0]->SetRelativeScale3D(FVector(FMath::Lerp(0.5f, Radius * 2.f / 100.f, FMath::Clamp(1.f - (Until - Now) / 0.5f, 0.f, 1.f)), FMath::Lerp(0.5f, Radius * 2.f / 100.f, FMath::Clamp(1.f - (Until - Now) / 0.5f, 0.f, 1.f)), 1.f));
		return;
	}
	if (Kind == ERDArtProp::Coin) { if (Meshes.Num() > 0 && Meshes[0]) Meshes[0]->AddLocalRotation(FRotator(0.f, 360.f * Dt, 0.f)); }
	// (the cloud's puffs facing the camera, rising and swelling a little, shrinking away in its last second)
	if (Kind == ERDArtProp::Smoke && Meshes.Num() > 0)
	{
		const APlayerCameraManager* Cm = UGameplayStatics::GetPlayerCameraManager(this, 0);
		const float Fade = FMath::Clamp(Until - Now, 0.f, 1.f);
		for (UStaticMeshComponent* M : Meshes)
		{
			if (!M) continue;
			const FVector Wl = M->GetComponentLocation();
			const FVector ToCam = Cm ? (Cm->GetCameraLocation() - Wl).GetSafeNormal() : FVector::UpVector;
			M->SetWorldRotation(FRotationMatrix::MakeFromZ(ToCam).Rotator());
			M->AddRelativeLocation(FVector(0.f, 0.f, 18.f * Dt));
			const float S0 = M->GetRelativeScale3D().X;
			const float S1 = Fade < 1.f ? S0 * (1.f - 1.8f * Dt) : S0 * (1.f + 0.06f * Dt);
			M->SetRelativeScale3D(FVector(S1));
		}
	}
	// (the ground's arts on the monsters within them, five times a second)
	Look -= Dt;
	if (Look > 0.f) return;
	Look = 0.2f;
	if (Kind != ERDArtProp::Caltrops && Kind != ERDArtProp::Smoke && Kind != ERDArtProp::Acid) return;
	for (ARDMonster* Mo : G->GetMonsters())
	{
		if (!IsValid(Mo) || Mo->IsDead() || Mo->IsAlly()) continue;
		const FVector Ml = Mo->GetActorLocation();
		if (FVector::Dist2D(Ml, GetActorLocation()) > Radius || FMath::Abs(Ml.Z - GetActorLocation().Z) > 250.f) continue;
		const bool bNew = !Done.Contains(Mo);
		if (Kind == ERDArtProp::Caltrops)
		{
			// (slowed while on them; a bleed when it first crosses them)
			Mo->SlowFor(A, 0.6f);
			if (bNew) Mo->AddBurn(B, C, 0.f);
		}
		else if (Kind == ERDArtProp::Smoke) Mo->LoseHerFor(A);
		else { Mo->ExposeFor(A, 1.f); Mo->AddBurn(B, 0.2f, 0.f); }          // (one look's worth: renewed, never stacked (PR #60's review))
		if (bNew) { Done.Add(Mo); ++Reached; }
	}
}

// ================================================================================================ a monster's side
void ARDMonster::LoseHerFor(float Seconds)
{
	if (bDead) return;
	LostHerUntil = FMath::Max(LostHerUntil, GetWorld()->GetTimeSeconds() + Seconds);
}

void ARDMonster::MarkFor(float Share, float Seconds)
{
	if (bDead) return;
	const float Now = GetWorld()->GetTimeSeconds();
	MarkShare = Now < MarkUntil ? FMath::Max(MarkShare, Share) : Share;
	MarkUntil = FMath::Max(MarkUntil, Now + Seconds);
}

void ARDMonster::ExposeFor(float Share, float Seconds)
{
	if (bDead) return;
	const float Now = GetWorld()->GetTimeSeconds();
	ExposedShare = Now < ExposedUntil ? FMath::Max(ExposedShare, Share) : Share;
	ExposedUntil = FMath::Max(ExposedUntil, Now + Seconds);
}

bool ARDMonster::HasLostHer() const { return GetWorld() && GetWorld()->GetTimeSeconds() < LostHerUntil; }
float ARDMonster::GetMarkShare() const { return GetWorld() && GetWorld()->GetTimeSeconds() < MarkUntil ? MarkShare : 0.f; }
float ARDMonster::GetExposedShare() const { return GetWorld() && GetWorld()->GetTimeSeconds() < ExposedUntil ? ExposedShare : 0.f; }

// ================================================================================================ her side
ARDArtProp* URDCombatComponent::SpawnArtProp(const FRDSecondaryDef& D, uint8 KindIn, const FVector& At)
{
	const ERDArtProp Kind = (ERDArtProp)KindIn;
	UWorld* W = GetWorld();
	if (!W || !Generator) return nullptr;
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ARDArtProp* P = W->SpawnActor<ARDArtProp>(ARDArtProp::StaticClass(), FTransform(At), Sp);
	if (!P) return nullptr;
	P->Kind = Kind; P->Art = D.Name; P->Gen = Generator;
	const float Now = W->GetTimeSeconds();
	P->Until = Now + RDArtNum(D.Seconds, 5.f);
	P->Radius = D.Share * 100.f;
	const float Dag = ArtBlade(), Bolt = ArtBolt();
	if (Kind == ERDArtProp::Caltrops)
	{
		// (the spikes scattered over its round, each its own turn, by a stream of the cast's place)
		P->A = RDArtNum(D.Values, 0.4f); P->B = Dag * RDArtNum(D.Values2, 0.15f); P->C = 4.f;
		const uint32 H0 = RDArtHash((uint32)FMath::RoundToInt(At.X), (uint32)FMath::RoundToInt(At.Y));
		for (int32 I = 0; I < 18; ++I)
		{
			const uint32 H = RDArtHash(H0, I);
			const float Ang = (H % 3600u) / 3600.f * 2.f * PI, Rr = FMath::Sqrt(((H / 3600u) % 1000u) / 1000.f) * P->Radius * 0.9f;
			FVector Q = At + FVector(FMath::Cos(Ang) * Rr, FMath::Sin(Ang) * Rr, 0.f);
			FHitResult Hit; FCollisionQueryParams Qp(SCENE_QUERY_STAT(RDArtFloor), false, GetOwner());
			if (W->LineTraceSingleByChannel(Hit, Q + FVector(0, 0, 120.f), Q - FVector(0, 0, 300.f), ECC_Visibility, Qp)) Q = Hit.ImpactPoint;
			P->AddMesh(D.Mesh, FTransform(FRotator((H % 90u) - 45.f, (H / 7u) % 360u, (H / 11u) % 90u - 45.f), Q - At + FVector(0, 0, 3.f), FVector(D.MeshScale)), D.Material);
		}
	}
	else if (Kind == ERDArtProp::Smoke)
	{
		P->A = RDArtNum(D.Values, 4.f); P->AddFx(D.Fx, FVector(0, 0, 40.f), D.FxScale);
		if (D.Material && Generator->ArtPlane && P->Radius > 0.f)
		{
			const uint32 H0 = RDArtHash((uint32)FMath::RoundToInt(At.X) + 7u, (uint32)FMath::RoundToInt(At.Y));
			for (int32 I = 0; I < 14; ++I)
			{
				const uint32 H = RDArtHash(H0, I);
				const float Ang = (H % 3600u) / 3600.f * 2.f * PI, Rr = FMath::Sqrt(((H / 3600u) % 1000u) / 1000.f) * P->Radius * 0.75f;
				const FVector Q(FMath::Cos(Ang) * Rr, FMath::Sin(Ang) * Rr, 60.f + ((H / 7u) % 160u));
				P->AddMesh(Generator->ArtPlane, FTransform(FRotator::ZeroRotator, Q, FVector(2.2f + ((H / 13u) % 100u) / 60.f)), D.Material);
			}
		}
	}
	else if (Kind == ERDArtProp::Acid)
	{
		P->A = RDArtNum(D.Values, 0.25f); P->B = FMath::Max(Dag, Bolt) * RDArtNum(D.Values2, 0.2f);
		if (Generator->ArtDisc) P->AddMesh(Generator->ArtDisc, FTransform(FRotator::ZeroRotator, FVector(0, 0, 2.f), FVector(P->Radius / 50.f, P->Radius / 50.f, 0.02f)), D.Material);
		P->AddFx(D.Fx2, FVector(0, 0, 4.f), D.FxScale);
	}
	Generator->ArtProps.RemoveAll([](const TWeakObjectPtr<ARDArtProp>& X) { return !X.IsValid(); });
	Generator->ArtProps.Add(P);
	return P;
}

float URDCombatComponent::ArtBlade() const
{
	// (her blade's blow: the weapon in her hand if it is one, else her best; as her growth makes it)
	if (!Generator) return 0.f;
	float Best = 0.f;
	for (int32 I = 0; I < Generator->Weapons.Num(); ++I)
	{
		const FRDWeaponDef& W = Generator->Weapons[I];
		if (W.bSpell || W.bScroll) continue;
		const float D = GetDamageOf(I);
		if (I == WeaponIndex) return D;
		Best = FMath::Max(Best, D);
	}
	return Best;
}

float URDCombatComponent::ArtBolt() const
{
	// (her crossbow's: a spell weapon whose bolt is a mesh)
	if (!Generator) return 0.f;
	float Best = 0.f;
	for (int32 I = 0; I < Generator->Weapons.Num(); ++I)
		if (Generator->Weapons[I].bSpell && Generator->Weapons[I].BoltMesh && !Generator->Weapons[I].bScroll) Best = FMath::Max(Best, GetDamageOf(I));
	return Best;
}

void URDCombatComponent::ArtHit(ARDMonster* Mo, float Dmg)
{
	if (!IsValid(Mo) || Mo->IsDead() || Dmg <= 0.f || !Generator) return;
	CurrentSpellElement = NAME_None;
	if (Mo->ApplyDamage(Dmg, GetOwner())) ++Kills;
	DamageDealt += Dmg; ArtDamage += Dmg;
	Generator->AddHitText(Mo->GetActorLocation() + FVector(0, 0, Mo->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()), Dmg, false);
}

void URDCombatComponent::ArtStrikeFromHiding()
{
	// (a blow out of stealth, as an attack's: it ends it, unless the vanishing act still has blows to spare)
	if (!IsStealthed()) return;
	bAmbushArmed = true;
	if (VanishBlowsLeft > 0) --VanishBlowsLeft;
	else EndStealth(TEXT("attack"));
}

void URDCombatComponent::PlayArtClip(FName Which)
{
	USkeletalMeshComponent* M = Body();
	UAnimInstance* AI = M ? M->GetAnimInstance() : nullptr;
	if (!AI || !Generator || Which.IsNone()) return;
	const bool bBolt = Which == TEXT("crossbow");
	for (const FRDWeaponDef& W : Generator->Weapons)
	{
		if (W.bScroll || (bBolt ? !(W.bSpell && W.BoltMesh) : W.bSpell) || W.Attacks.Num() == 0 || !W.Attacks[0]) continue;
		AI->PlaySlotAnimationAsDynamicMontage(W.Attacks[0], FName(TEXT("DefaultSlot")), 0.08f, 0.16f, 1.25f, 1, -1.f, 0.f);
		return;
	}
}

bool URDCombatComponent::UseRogueArt(const FRDSecondaryDef& D)
{
	ACharacter* C = Cast<ACharacter>(GetOwner());
	UWorld* W = GetWorld();
	if (!C || !W || !Generator) return false;
	const float Now = W->GetTimeSeconds();
	const FName Key(*(TEXT("@") + D.Name.ToString()));
	if (const float* R = ReadyAt.Find(Key); R && *R > Now) { SetMessage(FString::Printf(TEXT("%s is not ready: %.0f s"), *D.Title, FMath::CeilToFloat(*R - Now))); return false; }
	if (DexEnergy + 0.01f < D.Dex)
	{
		SetMessage(FString::Printf(TEXT("Not enough dexterity energy for %s (%.0f of %.0f)"), *D.Title, FMath::FloorToFloat(DexEnergy), D.Dex));
		Generator->PlaySoundAt(TEXT("Player.NoMana"), C->GetActorLocation());
		return false;
	}
	if (IsAttacking() || ArtCutsLeft.Num() > 0 || ArtLotusLeft > 0 || bArtHooking) { SetMessage(FString::Printf(TEXT("%s: not in the middle of a move"), *D.Title)); return false; }
	const float V = RDArtNum(D.Values), V2 = RDArtNum(D.Values2, 1.f), S = RDArtNum(D.Seconds), Cd = RDArtNum(D.Cooldowns, 10.f);
	const FVector L = C->GetActorLocation();
	FVector Fw = C->GetActorForwardVector() * FVector(1, 1, 0); Fw = Fw.GetSafeNormal();
	const float Hh = C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight(), Rad = C->GetCapsuleComponent()->GetScaledCapsuleRadius();
	const FVector Feet = L - FVector(0, 0, Hh);
	const float Reach = D.Reach > 0.f ? D.Reach : 2000.f;
	const float Dag = ArtBlade(), Bolt = ArtBolt();
	USkeletalMeshComponent* Bd = Body();
	const FVector Hand = Bd ? Bd->GetSocketLocation(TEXT("hand_r")) : L;
	FString Refused; int32 Reached = 0; float Number = 0.f;
	auto NoTarget = [&](const TCHAR* What) { Refused = FString::Printf(TEXT("%s: %s"), *D.Title, What); };
	auto Fly = [&](ERDArtProp, const FVector& To, float Time, float ArcCm, ARDMonster* Mo) -> ARDArtProp*
	{
		FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		ARDArtProp* P = W->SpawnActor<ARDArtProp>(ARDArtProp::StaticClass(), FTransform((To - Hand).Rotation(), Hand), Sp);
		if (!P) return nullptr;
		P->Kind = ERDArtProp::Flying; P->Art = D.Name; P->Gen = Generator; P->From = Hand; P->To = To; P->FlyTime = Time; P->Arc = ArcCm; P->Target = Mo;
		Generator->ArtProps.Add(P);
		return P;
	};
	if (D.Name == RDArtCaltrops)
	{
		SpawnArtProp(D, (uint8)ERDArtProp::Caltrops, Feet + Fw * FMath::Max(D.Reach, 150.f));
		Reached = 1; Number = D.Share;
	}
	else if (D.Name == RDArtSmoke)
	{
		SpawnArtProp(D, (uint8)ERDArtProp::Smoke, Feet);
		// (the monsters in it now lose her at once, not at its first look)
		for (ARDMonster* Mo : SecTargetsAround(D.Share * 100.f, -2.f)) { Mo->LoseHerFor(V); ++Reached; }
		Number = V;
	}
	else if (D.Name == RDArtHamstring)
	{
		ARDMonster* Mo = SecTargetAhead(Reach, 0.5f);
		if (!Mo) NoTarget(TEXT("no enemy within reach before you"));
		else
		{
			ArtStrikeFromHiding();
			ArtHit(Mo, Dag * V2 * AmbushArtMul()); Mo->SlowFor(V, S);
			if (D.Fx && Bd) SpawnFx(D.Fx, Bd->GetSocketLocation(TEXT("hand_r")), FRotator::ZeroRotator, D.FxScale, Bd, TEXT("hand_r"));
			if (D.Fx2) SpawnFx(D.Fx2, Mo->GetActorLocation(), (Mo->GetActorLocation() - L).Rotation(), D.FxScale);
			Reached = 1; Number = Mo->GetSlowShare();
		}
	}
	else if (D.Name == RDArtMarked)
	{
		ARDMonster* Mo = SecTargetAhead(Reach, FMath::Cos(FMath::DegreesToRadians(25.f)));
		if (!Mo) NoTarget(TEXT("no enemy before you"));
		else
		{
			Mo->MarkFor(V, S);
			if (ARDArtProp* P = SpawnArtProp(D, (uint8)ERDArtProp::Mark, Mo->GetActorLocation()))
			{
				P->Follow = Mo;
				if (Generator->ArtPlane) P->AddMesh(Generator->ArtPlane, FTransform(FRotator::ZeroRotator, FVector::ZeroVector, FVector(0.7f)), D.Material);
			}
			Reached = 1; Number = V;
		}
	}
	else if (D.Name == RDArtHook)
	{
		// (a monster before her within its reach, else the wall her eye meets along her way)
		ARDMonster* Mo = SecTargetAhead(Reach, FMath::Cos(FMath::DegreesToRadians(20.f)));
		FVector Hook = FVector::ZeroVector, Stop = FVector::ZeroVector;
		if (Mo)
		{
			Hook = Mo->GetActorLocation();
			Stop = Hook - (Hook - L).GetSafeNormal2D() * (Rad + Mo->GetCapsuleComponent()->GetScaledCapsuleRadius() + 60.f);
		}
		else
		{
			FHitResult Hit; FCollisionQueryParams Q(SCENE_QUERY_STAT(RDArtHook), false, C);
			const FVector Eye = L + FVector(0, 0, Hh * 0.6f);
			if (W->LineTraceSingleByChannel(Hit, Eye, Eye + Fw * Reach, ECC_Visibility, Q) && Hit.Distance > 300.f) { Hook = Hit.ImpactPoint; Stop = Hit.ImpactPoint - Fw * (Rad + 40.f); Stop.Z = L.Z; }
		}
		if (Hook.IsZero()) NoTarget(TEXT("nothing to hook within reach"));
		else
		{
			// (pulled along her way to it: a force over the length, her move input off; the rope from her hand to the hook)
			const FVector Way = (Stop - L);
			const float Len = Way.Size2D(), Dur = FMath::Clamp(Len / 2400.f, 0.15f, 1.f);
			UCharacterMovementComponent* CM = C->GetCharacterMovement();
			ArtHookTo = FVector(Stop.X, Stop.Y, FMath::Max(Stop.Z, L.Z)); ArtHookUntil = Now + Dur * 1.5f + 0.2f; bArtHooking = true;
			CM->StopMovementImmediately(); CM->SetMovementMode(MOVE_Flying);
			if (ARDArtProp* P = SpawnArtProp(D, (uint8)ERDArtProp::Rope, Hand))
			{
				P->To = Hook; P->Until = Now + Dur * 1.5f + 0.2f;
				if (Generator->ArtCylinder) P->AddMesh(Generator->ArtCylinder, FTransform::Identity, Generator->ArtRopeMaterial);
				P->AddMesh(D.Mesh, FTransform(FRotator(0, 0, 0), FVector::ZeroVector, FVector(D.MeshScale)), nullptr);
			}
			LastMoveLength = 0.f; Reached = Mo ? 1 : 0; Number = Len / 100.f;
		}
	}
	else if (D.Name == RDArtAcid)
	{
		ARDMonster* Mo = SecTargetAhead(Reach, FMath::Cos(FMath::DegreesToRadians(30.f)));
		FVector To = Mo ? Mo->GetActorLocation() - FVector(0, 0, Mo->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()) : Feet + Fw * FMath::Min(Reach, 600.f);
		FHitResult Hit; FCollisionQueryParams Q(SCENE_QUERY_STAT(RDArtAcid), false, C);
		if (W->LineTraceSingleByChannel(Hit, To + FVector(0, 0, 150.f), To - FVector(0, 0, 400.f), ECC_Visibility, Q) && !Cast<ARDMonster>(Hit.GetActor())) To = Hit.ImpactPoint;
		if (ARDArtProp* P = Fly(ERDArtProp::Flying, To, FMath::Clamp(FVector::Dist(Hand, To) / 1400.f, 0.25f, 0.8f), 120.f, nullptr))
		{
			P->AddMesh(D.Mesh, FTransform(FRotator::ZeroRotator, FVector::ZeroVector, FVector(D.MeshScale)), nullptr); P->Spin = 720.f;
		}
		Reached = Mo ? 1 : 0; Number = D.Share;
	}
	else if (D.Name == RDArtRicochet)
	{
		ARDMonster* Mo = SecTargetAhead(Reach, FMath::Cos(FMath::DegreesToRadians(25.f)));
		if (!Mo) NoTarget(TEXT("no enemy before you"));
		else
		{
			// (the chain: from each monster the nearest not yet struck within its hop, up to its count)
			TArray<TWeakObjectPtr<ARDMonster>> Chain;
			ARDMonster* Last = Mo; TSet<ARDMonster*> Used; Used.Add(Mo);
			for (int32 K = 1; K < FMath::RoundToInt(FMath::Max(V, 1.f)); ++K)
			{
				ARDMonster* Best = nullptr; float BestD = D.Share * 100.f;
				for (ARDMonster* O : Generator->GetMonsters())
					if (IsValid(O) && !O->IsDead() && !O->IsAlly() && !Used.Contains(O)) { const float Dd = FVector::Dist(O->GetActorLocation(), Last->GetActorLocation()); if (Dd < BestD) { BestD = Dd; Best = O; } }
				if (!Best) break;
				Chain.Add(Best); Used.Add(Best); Last = Best;
			}
			ArtStrikeFromHiding();
			UStaticMesh* BoltM = D.Mesh;
			for (const FRDWeaponDef& Wd : Generator->Weapons) if (Wd.bSpell && Wd.BoltMesh && !Wd.bScroll) { BoltM = Wd.BoltMesh; break; }
			if (ARDArtProp* P = Fly(ERDArtProp::Flying, Mo->GetActorLocation(), FMath::Max(FVector::Dist(Hand, Mo->GetActorLocation()) / 3500.f, 0.06f), 0.f, Mo))
			{
				P->A = Bolt * V2 * AmbushArtMul(); P->Next = Chain;
				P->AddMesh(BoltM, FTransform(FRotator::ZeroRotator, FVector::ZeroVector, FVector(D.MeshScale)), nullptr);
				P->AddFx(D.Fx, FVector::ZeroVector, D.FxScale, D.Tint, true);
			}
			Reached = 1 + Chain.Num(); Number = Bolt * V2;
		}
	}
	else if (D.Name == RDArtDouble)
	{
		if (ARDArtProp* P = SpawnArtProp(D, (uint8)ERDArtProp::Double, L))
		{
			P->bDecoy = true; P->A = Dag * V2; P->B = V * 100.f;
			P->CopyPose(Bd, D.Material);
			P->AddFx(D.Fx, FVector(0, 0, -Hh * 0.5f), D.FxScale);
			Reached = 1; Number = S;
		}
	}
	else if (D.Name == RDArtNet)
	{
		ARDMonster* Mo = SecTargetAhead(Reach, FMath::Cos(FMath::DegreesToRadians(25.f)));
		if (!Mo) NoTarget(TEXT("no enemy before you"));
		else
		{
			if (ARDArtProp* P = Fly(ERDArtProp::Flying, Mo->GetActorLocation(), FMath::Clamp(FVector::Dist(Hand, Mo->GetActorLocation()) / 2200.f, 0.15f, 0.8f), 60.f, Mo))
			{
				P->AddMesh(D.Mesh, FTransform(FRotator::ZeroRotator, FVector::ZeroVector, FVector(D.MeshScale)), nullptr);
				P->Spin = 0.f;
			}
			Reached = 1; Number = S;
		}
	}
	else if (D.Name == RDArtFan)
	{
		// (every monster within its round struck by a knife; eight knives fly out round her)
		ArtStrikeFromHiding();
		const float Mul = AmbushArtMul();
		for (ARDMonster* Mo : SecTargetsAround(D.Share * 100.f, -2.f)) { ArtHit(Mo, Dag * V2 * Mul); ++Reached; }
		const int32 N = FMath::Max(1, FMath::RoundToInt(V));
		for (int32 K = 0; K < N; ++K)
		{
			const float Ang = K * 2.f * PI / N;
			const FVector Out(FMath::Cos(Ang), FMath::Sin(Ang), 0.f);
			if (ARDArtProp* P = Fly(ERDArtProp::Flying, L + Out * D.Share * 100.f, 0.3f, 0.f, nullptr))
			{
				P->SetActorLocation(L + Out * 40.f); P->From = L + Out * 40.f;
				P->AddMesh(D.Mesh, FTransform(FRotator(0.f, 0.f, 0.f), FVector::ZeroVector, FVector(D.MeshScale)), nullptr);
				P->Spin = 1440.f;
			}
		}
		Number = Dag * V2;
	}
	else if (D.Name == RDArtFlash)
	{
		for (ARDMonster* Mo : SecTargetsAround(D.Share * 100.f, -2.f)) { Mo->BlindFor(1.f, S); Mo->StunFor(S); ++Reached; }
		if (ARDArtProp* P = SpawnArtProp(D, (uint8)ERDArtProp::Flash, L + Fw * 60.f))
		{
			P->Until = Now + 0.5f;
			P->Light = NewObject<UPointLightComponent>(P); P->Light->SetupAttachment(P->Root);
			P->Light->SetIntensityUnits(ELightUnits::Candelas); P->Light->SetAttenuationRadius(D.Share * 100.f * 1.6f); P->Light->SetLightColor(FLinearColor::White);
			P->Light->SetCastShadows(false); P->Light->RegisterComponent(); P->Light->SetIntensity(6000.f);
			P->AddFx(D.Fx, FVector(0, 0, -Hh + 10.f), D.FxScale);
			// (its white ring on the floor, spreading out to its round)
			if (Generator->ArtPlane) P->AddMesh(Generator->ArtPlane, FTransform(FRotator::ZeroRotator, FVector(0, 0, -Hh + 6.f), FVector(0.5f)), D.Material);
		}
		Number = S;
	}
	else if (D.Name == RDArtStep)
	{
		ARDMonster* Mo = SecTargetAhead(Reach, FMath::Cos(FMath::DegreesToRadians(35.f)));
		FVector Spot = FVector::ZeroVector;
		if (!Mo) NoTarget(TEXT("no enemy before you"));
		else
		{
			// (behind it, by its own facing; else to its side; where her capsule stands and she can see it from)
			const FVector Ml = Mo->GetActorLocation();
			const float Off = Rad + Mo->GetCapsuleComponent()->GetScaledCapsuleRadius() + 40.f;
			const FVector Bk = -(Mo->GetActorForwardVector() * FVector(1, 1, 0)).GetSafeNormal();
			for (const FVector Way : { Bk, FVector(Bk.Y, -Bk.X, 0.f), FVector(-Bk.Y, Bk.X, 0.f) })
			{
				FVector Got;
				if (!SecFloorAt(Ml + Way * Off, Hh, Rad, Got)) continue;
				FHitResult Sh; FCollisionQueryParams Sq(SCENE_QUERY_STAT(RDArtStep), false, C); Sq.AddIgnoredActor(Mo);
				if (W->LineTraceSingleByChannel(Sh, Ml, Got, ECC_Visibility, Sq)) continue;
				Spot = Got; break;
			}
			if (Spot.IsZero()) NoTarget(TEXT("no room behind it"));
			else
			{
				auto Puff = [&](const FVector& At) { if (ARDArtProp* Pp = SpawnArtProp(D, (uint8)ERDArtProp::Smoke, At - FVector(0, 0, Hh))) { Pp->Until = Now + 1.6f; Pp->Radius = 0.f; } };
				Puff(L);
				C->SetActorLocation(Spot, false, nullptr, ETeleportType::TeleportPhysics);
				C->SetActorRotation(FRotator(0.f, (Ml - Spot).Rotation().Yaw, 0.f));
				if (APlayerController* Pcr = Cast<APlayerController>(C->GetController())) Pcr->SetControlRotation(FRotator(-10.f, (Ml - Spot).Rotation().Yaw, 0.f));
				C->GetCharacterMovement()->StopMovementImmediately();
				Puff(Spot);
				// (the backstab: her blade with her ambush bonus, as from hiding)
				const FRDHeroDef* H = Generator->FindHero(Generator->CurrentHero);
				if (IsStealthed()) ArtStrikeFromHiding();
				ArtHit(Mo, Dag * V2 * (1.f + (H ? H->AmbushBonus : 0.f)));
				if (D.Fx2) SpawnFx(D.Fx2, Ml, (Ml - Spot).Rotation(), D.FxScale);
				LastMoveLength = FVector::Dist2D(L, Spot); Reached = 1; Number = Dag * V2 * (1.f + (H ? H->AmbushBonus : 0.f));
			}
		}
	}
	else if (D.Name == RDArtLure)
	{
		FVector To = Feet + Fw * FMath::Min(Reach, 800.f);
		FHitResult Hit; FCollisionQueryParams Q(SCENE_QUERY_STAT(RDArtLure), false, C);
		if (W->LineTraceSingleByChannel(Hit, L, To + FVector(0, 0, Hh), ECC_Visibility, Q)) To = Hit.ImpactPoint - Fw * 40.f;
		if (W->LineTraceSingleByChannel(Hit, To + FVector(0, 0, 150.f), To - FVector(0, 0, 400.f), ECC_Visibility, Q)) To = Hit.ImpactPoint + FVector(0, 0, 4.f);
		if (ARDArtProp* P = Fly(ERDArtProp::Flying, To, 0.55f, 160.f, nullptr))
		{
			P->AddMesh(D.Mesh, FTransform(FRotator(90.f, 0.f, 0.f), FVector::ZeroVector, FVector(D.MeshScale)), D.Material); P->Spin = 900.f;
		}
		Reached = 1; Number = D.Share;
	}
	else if (D.Name == RDArtVanish)
	{
		// (stealth of its own: no energy but this one's, her first blows spare it; the shimmer over her body)
		StealthUntil = Now + S; bAmbushArmed = false; StealthEndReason.Reset();
		VanishBlowsLeft = FMath::RoundToInt(V);
		if (Bd && D.Material) { Bd->SetOverlayMaterial(D.Material); bVanishLook = true; }
		++StealthUses;
		Reached = VanishBlowsLeft; Number = S;
	}
	else if (D.Name == RDArtLotus)
	{
		ArtStrikeFromHiding();
		ArtLotusLeft = FMath::Max(1, FMath::RoundToInt(V)); ArtLotusNext = Now; ArtLotusDmg = Dag * V2 * AmbushArtMul(); ArtLotusArt = D.Name;
		Reached = ArtLotusLeft; Number = ArtLotusDmg;
	}
	else if (D.Name == RDArtCuts)
	{
		// (every monster she sees within its reach, the nearest first, up to its count: marked; time slowed a moment; then the cuts)
		TArray<ARDMonster*> Seen;
		for (ARDMonster* Mo : SecTargetsAround(D.Share * 100.f, -2.f))
		{
			FHitResult Sh; FCollisionQueryParams Sq(SCENE_QUERY_STAT(RDArtCuts), false, C); Sq.AddIgnoredActor(Mo);
			if (!W->LineTraceSingleByChannel(Sh, L + FVector(0, 0, Hh * 0.6f), Mo->GetActorLocation(), ECC_Visibility, Sq)) Seen.Add(Mo);
		}
		Seen.Sort([&L](const ARDMonster& A, const ARDMonster& B) { return FVector::DistSquared(A.GetActorLocation(), L) < FVector::DistSquared(B.GetActorLocation(), L); });
		if (Seen.Num() > FMath::RoundToInt(V)) Seen.SetNum(FMath::RoundToInt(V));
		if (Seen.Num() == 0) NoTarget(TEXT("no enemy in sight"));
		else
		{
			ArtStrikeFromHiding();
			ArtCutsLeft.Reset();
			for (ARDMonster* Mo : Seen)
			{
				ArtCutsLeft.Add(Mo);
				if (ARDArtProp* P = SpawnArtProp(D, (uint8)ERDArtProp::Mark, Mo->GetActorLocation()))
				{
					P->Follow = Mo; P->Until = Now + 3.f;
					if (Generator->ArtPlane) P->AddMesh(Generator->ArtPlane, FTransform(FRotator::ZeroRotator, FVector::ZeroVector, FVector(0.6f)), D.Material);
				}
			}
			ArtCutsDmg = Dag * V2 * AmbushArtMul(); ArtCutsArt = D.Name;
			ArtCutsDilationWas = UGameplayStatics::GetGlobalTimeDilation(W);
			UGameplayStatics::SetGlobalTimeDilation(W, 0.3f);
			ArtCutsRealStart = FPlatformTime::Seconds() + 0.45;
			ArtCutsNext = -1.f;
			Reached = Seen.Num(); Number = ArtCutsDmg;
		}
	}
	else { SetMessage(FString::Printf(TEXT("%s: not made yet"), *D.Title)); return false; }
	bAmbushArmed = false;          // (an art's strike from hiding used its ambush there and then (PR #60's review: left armed, her next ordinary blow took it))
	if (!Refused.IsEmpty()) { SetMessage(Refused); return false; }
	PlayArtClip(D.Clip);
	DexEnergy = FMath::Max(0.f, DexEnergy - D.Dex);
	ReadyAt.Add(Key, Now + Cd);
	++SecondaryUses; ++ArtUses;
	LastSecondary = FString::Printf(TEXT("%s|%d|%.2f"), *D.Name.ToString(), Reached, Number);
	SetMessage(D.Title);
	UE_LOG(LogRDRogue12, Log, TEXT("RDROGUEART %s: %d reached, %.2f, %.0f dexterity left"), *D.Name.ToString(), Reached, Number, DexEnergy);
	return true;
}

bool URDCombatComponent::LearnArt(FName Art, bool bSay)
{
	const FRDSecondaryDef* Ad = Generator ? Generator->FindSecondary(Art) : nullptr;
	if (!Ad || Ad->Slot <= 0) return false;
	if (Ad->Hero != Generator->CurrentHero) { if (bSay) SetMessage(FString::Printf(TEXT("The %s cannot learn %s"), *Generator->PlayerTitle.ToLower(), *Ad->Title)); return false; }
	if (GetSecondaryRank(Ad->Name) > 0) { if (bSay) SetMessage(FString::Printf(TEXT("You know %s already"), *Ad->Title)); return false; }
	SecondaryRanks.Add(Ad->Name, 1);
	if (Ad->Kind != ERDSecondaryKind::Passive) AddAbilityToQuickBar(Ad->Name);
	SetMessage(FString::Printf(TEXT("You learn %s: %s"), *Ad->Title, *Ad->Text));
	PlayUiSound(TEXT("Player.Inventory"), TEXT("Player.Inventory"));
	UE_LOG(LogRDRogue12, Log, TEXT("RDROGUEART learned %s"), *Ad->Name.ToString());
	return true;
}

void URDCombatComponent::ResetRogueArts()
{
	UWorld* W = GetWorld();
	if (bArtHooking)
		if (ACharacter* C = Cast<ACharacter>(GetOwner()); C && C->GetCharacterMovement()->MovementMode == MOVE_Flying) C->GetCharacterMovement()->SetMovementMode(MOVE_Falling);
	bArtHooking = false;
	ArtLotusLeft = 0; ArtCutsLeft.Reset();
	if (ArtCutsDilationWas > 0.f && W) UGameplayStatics::SetGlobalTimeDilation(W, ArtCutsDilationWas);
	ArtCutsDilationWas = -1.f;
	if (bVanishLook) if (USkeletalMeshComponent* Bd = Body()) Bd->SetOverlayMaterial(nullptr);
	bVanishLook = false; VanishBlowsLeft = 0;
}

void URDCombatComponent::EndPlay(const EEndPlayReason::Type Reason)
{
	ResetRogueArts();          // (the time the cuts slowed never left slowed for the next hero or level)
	Super::EndPlay(Reason);
}

float URDCombatComponent::AmbushArtMul() const
{
	// (a strike from hiding: her ambush bonus, as a blow's (armed when the strike ended or spent her stealth))
	if (!bAmbushArmed || !Generator) return 1.f;
	const FRDHeroDef* H = Generator->FindHero(Generator->CurrentHero);
	return H ? 1.f + H->AmbushBonus : 1.f;
}

void URDCombatComponent::TickRogueArts(float Dt)
{
	UWorld* W = GetWorld();
	ACharacter* C = Cast<ACharacter>(GetOwner());
	if (!W || !C || !Generator) return;
	const float Now = W->GetTimeSeconds();
	// (the hook's pull: toward its stop at its speed, swept; over when there, stopped by something, or out of time)
	if (bArtHooking)
	{
		UCharacterMovementComponent* CM = C->GetCharacterMovement();
		const FVector L = C->GetActorLocation(), Rest = ArtHookTo - L;
		const float Step = 2400.f * Dt;
		bool bEnd = Rest.Size() <= Step + 5.f || Now > ArtHookUntil || bDead;
		if (!bEnd)
		{
			FHitResult Hit;
			C->SetActorLocation(L + Rest.GetSafeNormal() * Step, true, &Hit);
			if (Hit.bBlockingHit && (C->GetActorLocation() - L).Size() < Step * 0.3f) bEnd = true;
			LastMoveLength += (C->GetActorLocation() - L).Size2D();
		}
		else if (Rest.Size() <= Step + 5.f) { C->SetActorLocation(ArtHookTo, true); }
		if (bEnd) { bArtHooking = false; if (CM->MovementMode == MOVE_Flying) CM->SetMovementMode(MOVE_Falling); CM->Velocity = FVector::ZeroVector; }
	}
	// (the vanishing act's shimmer off with the stealth)
	if (!IsStealthed() && (bVanishLook || VanishBlowsLeft > 0)) { if (bVanishLook) if (USkeletalMeshComponent* Bd = Body()) Bd->SetOverlayMaterial(nullptr); bVanishLook = false; VanishBlowsLeft = 0; }
	// (the death lotus: its strikes a third of a second apart, each with its crescent and an afterimage of her)
	if (ArtLotusLeft > 0 && Now >= ArtLotusNext)
	{
		const FRDSecondaryDef* D = Generator->FindSecondary(ArtLotusArt);
		if (!D || bDead) ArtLotusLeft = 0;
		else
		{
			const int32 K = FMath::RoundToInt(RDArtNum(D->Values, 3.f)) - ArtLotusLeft;
			for (ARDMonster* Mo : SecTargetsAround(D->Share * 100.f, -2.f)) { ArtHit(Mo, ArtLotusDmg); ++ArtLotusHits; }
			if (D->Fx) SpawnFx(D->Fx, C->GetActorLocation(), FRotator(0.f, C->GetActorRotation().Yaw + 120.f * K, 0.f), D->FxScale);
			if (ARDArtProp* P = SpawnArtProp(*D, (uint8)ERDArtProp::Afterimage, C->GetActorLocation()))
			{
				P->Until = Now + 0.45f; P->CopyPose(Body(), D->Material);
				P->SetActorRotation(FRotator(0.f, 120.f * (K + 1), 0.f));
			}
			C->AddActorWorldRotation(FRotator(0.f, 120.f, 0.f));
			--ArtLotusLeft; ArtLotusNext = Now + 0.3f;
		}
	}
	// (the thousand cuts: time slowed a moment, then back; she blinks to each marked one in turn, behind it, and cuts it)
	if (ArtCutsLeft.Num() > 0 || ArtCutsDilationWas > 0.f)
	{
		const FRDSecondaryDef* D = Generator->FindSecondary(ArtCutsArt);
		const bool bTimeBack = FPlatformTime::Seconds() >= ArtCutsRealStart || bDead;
		if (bTimeBack && ArtCutsDilationWas > 0.f) { UGameplayStatics::SetGlobalTimeDilation(W, ArtCutsDilationWas); ArtCutsDilationWas = -1.f; ArtCutsNext = Now; }
		if (bDead) ArtCutsLeft.Reset();
		if (bTimeBack && ArtCutsLeft.Num() > 0 && Now >= ArtCutsNext && D)
		{
			ARDMonster* Mo = ArtCutsLeft[0].Get();
			ArtCutsLeft.RemoveAt(0);
			if (Mo && !Mo->IsDead())
			{
				const float Hh = C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight(), Rad = C->GetCapsuleComponent()->GetScaledCapsuleRadius();
				const FVector Ml = Mo->GetActorLocation();
				const FVector Bk = -(Mo->GetActorForwardVector() * FVector(1, 1, 0)).GetSafeNormal();
				const float Off = Rad + Mo->GetCapsuleComponent()->GetScaledCapsuleRadius() + 40.f;
				for (const FVector Way : { Bk, FVector(Bk.Y, -Bk.X, 0.f), FVector(-Bk.Y, Bk.X, 0.f) })
				{
					// (in sight of its monster: never through a wall (PR #60's review))
					FVector Got;
					if (!SecFloorAt(Ml + Way * Off, Hh, Rad, Got)) continue;
					FHitResult Sh; FCollisionQueryParams Sq(SCENE_QUERY_STAT(RDArtCutsSpot), false, C); Sq.AddIgnoredActor(Mo);
					if (W->LineTraceSingleByChannel(Sh, Ml, Got, ECC_Visibility, Sq)) continue;
					C->SetActorLocation(Got, false, nullptr, ETeleportType::TeleportPhysics);
					C->SetActorRotation(FRotator(0.f, (Ml - Got).Rotation().Yaw, 0.f));
					break;
				}
				ArtHit(Mo, ArtCutsDmg); ++ArtCutsHits;
				if (D->Fx) SpawnFx(D->Fx, Ml, FRotator(0.f, (Ml - C->GetActorLocation()).Rotation().Yaw, 35.f * (ArtCutsHits % 2 ? 1.f : -1.f)), D->FxScale);
				PlayArtClip(D->Clip);
			}
			ArtCutsNext = Now + 0.15f;
		}
	}
}

// ================================================================================================ the generator's side
FName ARDDungeonGenerator::TomeItemOf(FName Spell) const
{
	// (a tome "Tome of <spell>", else the item of kind Tome that teaches it: the Rogue's "Manual of <art>")
	if (Spell.IsNone()) return NAME_None;
	const FName T = TomeItemName(Spell);
	if (FindItem(T) >= 0) return T;
	for (const FRDItemDef& It : Items) if (It.Kind == ERDItemKind::Tome && It.Spell == Spell) return It.Name;
	return NAME_None;
}

void ARDDungeonGenerator::ClearArtProps()
{
	for (const TWeakObjectPtr<ARDArtProp>& Wp : ArtProps) if (ARDArtProp* P = Wp.Get()) P->Destroy();
	ArtProps.Reset();
}

TArray<FString> ARDDungeonGenerator::GetArtPropLines() const
{
	TArray<FString> Out;
	const UWorld* W = GetWorld();
	const float Now = W ? W->GetTimeSeconds() : 0.f;
	for (const TWeakObjectPtr<ARDArtProp>& Wp : ArtProps)
		if (const ARDArtProp* P = Wp.Get())
		{
			const FVector L = P->GetActorLocation();
			// (its effects: their system, active or not, where)
			FString Fx;
			for (const UNiagaraComponent* F : P->Fxs)
				if (F) Fx += FString::Printf(TEXT("%s%s:%d@%.0f,%.0f,%.0f"), Fx.IsEmpty() ? TEXT("") : TEXT(";"), F->GetAsset() ? *F->GetAsset()->GetName() : TEXT("none"), F->IsActive() ? 1 : 0,
					F->GetComponentLocation().X, F->GetComponentLocation().Y, F->GetComponentLocation().Z);
			Out.Add(FString::Printf(TEXT("%s|%s|%.0f|%.0f|%.0f|%d|%d|%.2f|%s"), *StaticEnum<ERDArtProp>()->GetNameStringByValue((int64)P->Kind), *P->Art.ToString(), L.X, L.Y, L.Z, P->Reached, P->bDecoy ? 1 : 0, P->Until - Now, *Fx));
		}
	return Out;
}