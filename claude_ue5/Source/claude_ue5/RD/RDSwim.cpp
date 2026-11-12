// Swimming (the user's of 2026-11-12: "create swimming animations for all current playable classes that are found in the choose a
// hero menu. create a splash sound for when a player falls into the water or is swimming. have water displacement and a wake for
// when the player moves through the water"):
//   - she swims where the water is deep: her feet more than SwimDepth under its face (the wilds' floor under deep water lies
//     145 cm down: RDWildChunk.cpp; Graymourne's harbour's 140 cm: RDTownPlan.cpp); her body held at the face (her pelvis
//     SwimPelvisMove under it swimming along, her head SwimHeadIdle over it treading), her speed a share of her walk's, no jump, no blow, block, roll, dash, chi, stealth or ability;
//   - her clips: the "92 Animations For Warrior" pack's treading idle and swim loop retargeted onto her rig (921 clips), on her
//     slot as the rider's are (RDHorse.cpp), the loop's rate by her speed;
//   - a stroke's sound as she swims (Player.Swim; the splash where she comes in is TickWild11's, Player.Splash);
//   - the water's displacement: ripples from up to 8 sources (where she came in, her wake as she swims or wades, rings as she
//     stands) in a material parameter collection the water's material reads (887's M_RD_WildWater), and her own bulge.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDCombat.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"
#include "Engine/World.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDSwim, Log, All);

namespace
{
	const FName RDSwimSlot(TEXT("DefaultSlot"));          // (the rider's slot: her attacks and death use it too, and none come while she swims)
	constexpr int32 RDSwimRipples = 8;
}

void ARDDungeonGenerator::TickSwim(float Dt, ACharacter* C, bool bIn, float Fz)
{
	if (!C || !PlayerCombat) return;
	// (another pawn than the one that began swimming (a switch of hero, a restart): that swim is over, nothing of it put back on
	// this one)
	if (bSwimming && SwimPawn.Get() != C) { bSwimming = false; SwimClipNow = NAME_None; SwimMontage = nullptr; PlayerCombat->SwimFactor = 1.f; PlayerCombat->RefreshWalkSpeed(); }
	USkeletalMeshComponent* M = C->GetMesh();
	const float Half = C->GetCapsuleComponent() ? C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() : 90.f;
	const float Feet = C->GetActorLocation().Z - Half;
	// (in once her feet are SwimDepth under the face, out once they are 15 cm higher than that: the swim floor's edge, where it
	// rises to the wading floor, is not crossed back and forth)
	const bool bDeep = bIn && Feet < Fz - (bSwimming ? SwimDepth - 15.f : SwimDepth);
	const bool bWant = bDeep && !bMounted && !PlayerCombat->IsDead();
	if (!bWant) { if (bSwimming) EndSwim(C); return; }
	UCharacterMovementComponent* CM = C->GetCharacterMovement();
	if (!bSwimming)
	{
		bSwimming = true; ++SwimsBegun; SwimPawn = C;
		SwimMeshWas = M->GetRelativeLocation();
		SwimJumpWas = CM->JumpZVelocity; CM->JumpZVelocity = 0.f;
		// (a block, a swing, a roll or a dash under way ends: none goes on in the water (the swing's blow landed from it until PR
		// #53's review))
		PlayerCombat->BreakOffMoves();
		bSwimMoving = false;
		PlayerCombat->SwimFactor = FMath::Clamp(SwimSpeedMul, 0.1f, 1.f); PlayerCombat->RefreshWalkSpeed();
		SwimClipNow = NAME_None; SwimStrokeClock = 0.f;
		UE_LOG(LogRDSwim, Log, TEXT("RDSWIM %s swims (feet %.0f cm under the face)"), *CurrentHero.ToString(), Fz - Feet);
	}
	// (her clip: the treading idle, or the swim loop at a rate by her speed against her swimming top speed)
	const float Sp = C->GetVelocity().Size2D();
	const FRDSwimClips* SC = SwimClips.Find(CurrentHero);
	// (swimming along from SwimMoveFrom, treading again only under 60 % of it: one line flipped the clip and the bone she is
	// held by every frame about it (PR #53's review))
	bSwimMoving = Sp > (bSwimMoving ? SwimMoveFrom * 0.6f : SwimMoveFrom);
	const bool bMove = bSwimMoving;
	UAnimSequenceBase* Clip = SC ? (bMove ? SC->Swim.Get() : SC->Idle.Get()) : nullptr;
	if (UAnimInstance* AI = M->GetAnimInstance(); AI && Clip)
	{
		const FName Want = Clip->GetFName();
		const float Top = FMath::Max(CM->MaxWalkSpeed, 1.f);
		const float Rate = bMove ? FMath::Clamp(Sp / Top, 0.6f, 1.6f) : 1.f;
		if (Want != SwimClipNow || !AI->IsSlotActive(RDSwimSlot))
		{
			SwimMontage = AI->PlaySlotAnimationAsDynamicMontage(Clip, RDSwimSlot, 0.3f, 0.3f, Rate, 10000);
			SwimClipNow = Want;
		}
		else if (SwimMontage) AI->Montage_SetPlayRate(SwimMontage, Rate);
	}
	// (her body at the face: swimming along, by her pelvis just under it, her back at the face (held 22 cm down, the whole of her
	// lay under the opaque face, the first test's picture; by her head 10 cm over it, some rigs' flat bodies lay on the water, not
	// in it, the third's); treading, upright, by her head over it. The mesh moved, eased; the capsule stays on the floor)
	{
		const float BoneZ = M->GetSocketLocation(bMove ? FName(TEXT("pelvis")) : FName(TEXT("head"))).Z;
		const float Want = Fz + (bMove ? -SwimPelvisMove : SwimHeadIdle);
		FVector R = M->GetRelativeLocation();
		// (eased slowly: the body bobs with each stroke, and a quick chase moved it against the stroke (the second test's head 7 cm
		// under at its median); the flat swim loop needs up to about 1.2 m of lift)
		R.Z += FMath::Clamp(Want - BoneZ, -40.f, 40.f) * FMath::Min(1.f, Dt * 3.f);
		R.Z = FMath::Clamp(R.Z, SwimMeshWas.Z - 20.f, SwimMeshWas.Z + 200.f);
		M->SetRelativeLocation(FVector(SwimMeshWas.X, SwimMeshWas.Y, R.Z));
	}
	// (a stroke's sound as she swims along: one every SwimStrokeEvery of the loop's time)
	if (bMove)
	{
		SwimStrokeClock -= Dt * FMath::Clamp(Sp / FMath::Max(CM->MaxWalkSpeed, 1.f), 0.6f, 1.6f);
		if (SwimStrokeClock <= 0.f)
		{
			SwimStrokeClock = SwimStrokeEvery;
			PlaySoundAt(TEXT("Player.Swim"), FVector(C->GetActorLocation().X, C->GetActorLocation().Y, Fz));
			++SwimStrokes;
		}
	}
	else SwimStrokeClock = FMath::Min(SwimStrokeClock, 0.2f);
}

void ARDDungeonGenerator::EndSwim(ACharacter* C)
{
	if (!bSwimming) return;
	bSwimming = false;
	if (C)
	{
		C->GetMesh()->SetRelativeLocation(SwimMeshWas);
		C->GetCharacterMovement()->JumpZVelocity = SwimJumpWas;
		// (her swim clip off, but not a death's: it plays on the same slot (the rider's lesson))
		if (UAnimInstance* AI = C->GetMesh()->GetAnimInstance(); AI && !(PlayerCombat && PlayerCombat->IsDead())) AI->StopSlotAnimation(0.25f, RDSwimSlot);
	}
	if (PlayerCombat) { PlayerCombat->SwimFactor = 1.f; PlayerCombat->RefreshWalkSpeed(); }
	SwimClipNow = NAME_None; SwimMontage = nullptr; bSwimMoving = false;
	UE_LOG(LogRDSwim, Log, TEXT("RDSWIM out of the deep water"));
}

void ARDDungeonGenerator::AddWaterRipple(const FVector& At, float Strength)
{
	if (!WaterRipples) return;
	// (a source: its place, the time it began (the collection's own clock, Now) and its strength, written round-robin)
	const float Now = GetWorld()->GetTimeSeconds();
	UKismetMaterialLibrary::SetVectorParameterValue(this, WaterRipples, FName(*FString::Printf(TEXT("Src%d"), RippleNext)), FLinearColor(At.X, At.Y, Now, Strength));
	RippleNext = (RippleNext + 1) % RDSwimRipples;
	++RipplesMade;
}

void ARDDungeonGenerator::TickWaterRipples(const FVector& Her, bool bIn, float Fz, float Speed)
{
	if (!WaterRipples) return;
	// (the clock the sources are timed by, and her own: where she is in the water, how strongly she pushes it (by her speed),
	// 0 out of it)
	const float Now = GetWorld()->GetTimeSeconds();
	UKismetMaterialLibrary::SetScalarParameterValue(this, WaterRipples, TEXT("Now"), Now);
	const float Push = bIn ? FMath::Clamp(0.35f + Speed / 400.f, 0.f, 1.f) : 0.f;
	UKismetMaterialLibrary::SetVectorParameterValue(this, WaterRipples, TEXT("Her"), FLinearColor(Her.X, Her.Y, Fz, Push));
}

FString ARDDungeonGenerator::GetSwimLine() const
{
	const ACharacter* C = Cast<ACharacter>(PlayerCombat ? PlayerCombat->GetOwner() : nullptr);
	float Under = 0.f, Pel = 0.f, Sp = 0.f, Top = 0.f;
	if (C)
	{
		float Fz = 0.f;
		if (WaterFaceAt(C->GetActorLocation(), Fz))
		{
			Under = C->GetMesh()->GetSocketLocation(TEXT("head")).Z - Fz;          // (her head over the face)
			Pel = C->GetMesh()->GetSocketLocation(TEXT("pelvis")).Z - Fz;          // (her pelvis over it)
		}
		Sp = C->GetVelocity().Size2D(); Top = C->GetCharacterMovement()->MaxWalkSpeed;
	}
	return FString::Printf(TEXT("swim|%d|%s|%.1f|%.0f|%.0f|%d|%d|%d|%.1f"), bSwimming ? 1 : 0, *SwimClipNow.ToString(), Under, Sp, Top, SwimStrokes, SwimsBegun, RipplesMade, Pel);
}
