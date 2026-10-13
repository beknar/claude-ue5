#include "RD/RDCombat.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDMonster.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequenceBase.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"

static const FName RDCombatSlot(TEXT("DefaultSlot"));

URDCombatComponent::URDCombatComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

const FRDWeaponDef* URDCombatComponent::Weapon() const
{
	return Generator && Generator->Weapons.IsValidIndex(WeaponIndex) ? &Generator->Weapons[WeaponIndex] : nullptr;
}

USkeletalMeshComponent* URDCombatComponent::Body() const
{
	const ACharacter* C = Cast<ACharacter>(GetOwner());
	return C ? C->GetMesh() : nullptr;
}

FName URDCombatComponent::GetWeaponName() const { const FRDWeaponDef* W = Weapon(); return W ? W->Name : NAME_None; }
float URDCombatComponent::GetWeaponDamage() const { const FRDWeaponDef* W = Weapon(); return W ? W->Damage : 0.f; }
float URDCombatComponent::GetWeaponReach() const { const FRDWeaponDef* W = Weapon(); return W ? W->Reach : 0.f; }

void URDCombatComponent::Init(ARDDungeonGenerator* InGenerator)
{
	Generator = InGenerator;
	MaxHealth = Health = Generator ? Generator->PlayerMaxHealth : 100.f;
	USkeletalMeshComponent* M = Body();
	auto Make = [&](const TCHAR* Name)
	{
		UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(GetOwner(), Name);
		C->SetMobility(EComponentMobility::Movable);
		C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		C->SetGenerateOverlapEvents(false);
		C->SetCanEverAffectNavigation(false);
		if (M) C->SetupAttachment(M);
		C->RegisterComponent();
		return C;
	};
	WeaponComp = Make(TEXT("RDWeapon")); OffHandComp = Make(TEXT("RDOffHand"));
	SelectWeapon(0);
}

void URDCombatComponent::SelectWeapon(int32 Index)
{
	if (!Generator || !Generator->Weapons.IsValidIndex(Index) || Index == WeaponIndex || bDead) return;
	if (AttackTime >= 0.f) EndAttack();
	WeaponIndex = Index; NextAttack = 0;
	const FRDWeaponDef& W = Generator->Weapons[Index];
	USkeletalMeshComponent* M = Body();
	auto Hold = [&](UStaticMeshComponent* C, UStaticMesh* Mesh, FName Bone, const FTransform& Grip)
	{
		if (!C) return;
		C->SetStaticMesh(Mesh);
		C->SetVisibility(Mesh != nullptr);
		if (M && Mesh)
		{
			C->AttachToComponent(M, FAttachmentTransformRules::SnapToTargetNotIncludingScale, Bone);
			C->SetRelativeTransform(Grip);
		}
	};
	Hold(WeaponComp, W.Mesh, W.HandBone, W.Grip);
	Hold(OffHandComp, W.OffHandMesh, W.OffHandBone, W.OffHandGrip);
}

void URDCombatComponent::SetSlowed(bool bSlow)
{
	ACharacter* C = Cast<ACharacter>(GetOwner());
	if (!C || bSlow == bSlowed) return;
	UCharacterMovementComponent* CM = C->GetCharacterMovement();
	if (bSlow) { SavedWalkSpeed = CM->MaxWalkSpeed; CM->MaxWalkSpeed = SavedWalkSpeed * 0.12f; }
	else CM->MaxWalkSpeed = SavedWalkSpeed;
	bSlowed = bSlow;
}

bool URDCombatComponent::StartAttack()
{
	const FRDWeaponDef* W = Weapon();
	USkeletalMeshComponent* M = Body();
	if (!W || !M || bDead || AttackTime >= 0.f || W->Attacks.Num() == 0) return false;
	UAnimInstance* AI = M->GetAnimInstance();
	UAnimSequenceBase* Clip = W->Attacks[NextAttack % W->Attacks.Num()];
	if (!AI || !Clip) return false;
	const float Rate = FMath::Max(W->PlayRate, 0.1f);
	const float T0 = W->AttackStarts.IsValidIndex(NextAttack % W->Attacks.Num()) ? W->AttackStarts[NextAttack % W->Attacks.Num()] : 0.f;
	const float T1 = W->AttackEnds.IsValidIndex(NextAttack % W->Attacks.Num()) && W->AttackEnds[NextAttack % W->Attacks.Num()] > T0 ? W->AttackEnds[NextAttack % W->Attacks.Num()] : Clip->GetPlayLength();
	const float Hit = W->HitTimes.IsValidIndex(NextAttack % W->Attacks.Num()) ? W->HitTimes[NextAttack % W->Attacks.Num()] : (T0 + T1) * 0.5f;
	// she turns to the nearest monster in front of her that the weapon could reach in a step (no need to line up by hand)
	if (AActor* O = GetOwner())
	{
		const FVector L = O->GetActorLocation(), Fw = O->GetActorForwardVector();
		const ARDMonster* Best = nullptr; float BestD = W->Reach + 160.f;
		for (const ARDMonster* Mo : Generator->GetMonsters())
		{
			if (!Mo || Mo->IsDead()) continue;
			const FVector D = (Mo->GetActorLocation() - L) * FVector(1, 1, 0);
			const float Dist = D.Size() - Mo->GetCapsuleComponent()->GetScaledCapsuleRadius();
			if (Dist < BestD && FMath::Abs(Mo->GetActorLocation().Z - L.Z) < 260.f && FVector::DotProduct(D.GetSafeNormal(), Fw) > -0.2f) { BestD = Dist; Best = Mo; }
		}
		if (Best) O->SetActorRotation(FRotator(0.f, ((Best->GetActorLocation() - L) * FVector(1, 1, 0)).Rotation().Yaw, 0.f));
	}
	AI->PlaySlotAnimationAsDynamicMontage(Clip, RDCombatSlot, 0.1f, 0.18f, Rate, 1, -1.f, T0);
	AttackTime = 0.f; AttackLen = (T1 - T0) / Rate; AttackHit = FMath::Clamp((Hit - T0) / Rate, 0.05f, AttackLen); bHitDone = false;
	++NextAttack; ++AttacksMade;
	SetSlowed(true);
	return true;
}

void URDCombatComponent::Strike()
{
	const FRDWeaponDef* W = Weapon();
	AActor* O = GetOwner();
	if (!W || !O || !Generator) return;
	const FVector L = O->GetActorLocation(), Fw = O->GetActorForwardVector();
	const float MinCos = FMath::Cos(FMath::DegreesToRadians(W->Arc * 0.5f));
	bool bAny = false;
	for (ARDMonster* Mo : Generator->GetMonsters())
	{
		if (!Mo || Mo->IsDead()) continue;
		const FVector D = (Mo->GetActorLocation() - L) * FVector(1, 1, 0);
		const float Rad = Mo->GetCapsuleComponent()->GetScaledCapsuleRadius();
		const float Dist = D.Size() - Rad;
		if (Dist > W->Reach || FMath::Abs(Mo->GetActorLocation().Z - L.Z) > 260.f) continue;
		// (a big monster right against her is in the arc whatever the angle to its middle)
		if (Dist > 40.f && FVector::DotProduct(D.GetSafeNormal(), Fw) < MinCos) continue;
		const bool bKilled = Mo->ApplyDamage(W->Damage, O);
		Generator->AddHitText(Mo->GetActorLocation() + FVector(0, 0, Mo->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()), W->Damage, false);
		DamageDealt += W->Damage; ++HitsLanded; bAny = true;
		if (bKilled) ++Kills;
	}
	if (bAny) LastHitTime = GetWorld()->GetTimeSeconds();
}

void URDCombatComponent::EndAttack()
{
	AttackTime = -1.f;
	SetSlowed(false);
}

void URDCombatComponent::ApplyDamage(float Amount, AActor* From)
{
	if (bDead || Amount <= 0.f) return;
	const float Now = GetWorld()->GetTimeSeconds();
	Health = FMath::Max(0.f, Health - Amount);
	DamageTaken += Amount; ++HitsTaken; LastHurtTime = Now;
	AActor* O = GetOwner();
	if (Generator && O) Generator->AddHitText(O->GetActorLocation() + FVector(0, 0, 90.f), Amount, true);
	USkeletalMeshComponent* M = Body();
	UAnimInstance* AI = M ? M->GetAnimInstance() : nullptr;
	const FRDWeaponDef* W = Weapon();
	if (Health <= 0.f)
	{
		bDead = true; ++Deaths; DeathTime = Now;
		EndAttack();
		if (ACharacter* C = Cast<ACharacter>(O)) C->GetCharacterMovement()->StopMovementImmediately();
		if (AI && W && W->Death)
			if (UAnimMontage* Mo = AI->PlaySlotAnimationAsDynamicMontage(W->Death, RDCombatSlot, 0.12f, 0.2f, 1.f, 1, -1.f, 0.f)) Mo->bEnableAutoBlendOut = false;      // (she stays down)
		return;
	}
	// a flinch, unless she is in the middle of a swing or flinched a moment ago
	if (AI && W && W->GetHit && AttackTime < 0.f && Now > StaggerUntil)
	{
		AI->PlaySlotAnimationAsDynamicMontage(W->GetHit, RDCombatSlot, 0.08f, 0.2f, 1.4f, 1, -1.f, 0.f);
		StaggerUntil = Now + 1.2f;
	}
}

void URDCombatComponent::Revive(bool bToStart)
{
	AActor* O = GetOwner();
	bDead = false; Health = MaxHealth; AttackTime = -1.f; SetSlowed(false); StaggerUntil = -100.f;
	if (USkeletalMeshComponent* M = Body()) if (UAnimInstance* AI = M->GetAnimInstance()) AI->StopSlotAnimation(0.2f, RDCombatSlot);
	if (bToStart && O && Generator)
	{
		O->SetActorLocation(Generator->GetStartRoomCenter() + FVector(0, 0, 100.f), false, nullptr, ETeleportType::TeleportPhysics);
		if (ACharacter* C = Cast<ACharacter>(O)) C->GetCharacterMovement()->StopMovementImmediately();
	}
}

void URDCombatComponent::TickComponent(float Dt, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(Dt, TickType, ThisTickFunction);
	if (!Generator) return;
	const float Now = GetWorld()->GetTimeSeconds();
	if (bDead)
	{
		if (Now - DeathTime > Generator->RespawnSeconds) Revive(true);
		return;
	}
	if (!bScriptedOnly && !Generator->bMapOpen)
		if (const APawn* P = Cast<APawn>(GetOwner()))
			if (const APlayerController* PC = Cast<APlayerController>(P->GetController()))
			{
				if (PC->WasInputKeyJustPressed(EKeys::One) || PC->WasInputKeyJustPressed(EKeys::Gamepad_DPad_Left)) SelectWeapon(0);
				if (PC->WasInputKeyJustPressed(EKeys::Two) || PC->WasInputKeyJustPressed(EKeys::Gamepad_DPad_Up)) SelectWeapon(1);
				if (PC->WasInputKeyJustPressed(EKeys::Three) || PC->WasInputKeyJustPressed(EKeys::Gamepad_DPad_Right)) SelectWeapon(2);
				if (PC->IsInputKeyDown(EKeys::LeftMouseButton) || PC->IsInputKeyDown(EKeys::Gamepad_FaceButton_Left) || PC->GetInputAnalogKeyState(EKeys::Gamepad_RightTriggerAxis) > 0.5f) StartAttack();
			}
	if (AttackTime >= 0.f)
	{
		AttackTime += Dt;
		if (!bHitDone && AttackTime >= AttackHit) { bHitDone = true; Strike(); }
		if (AttackTime >= AttackLen) EndAttack();
	}
	// out of a fight the hit points come back
	if (Health < MaxHealth && Now - LastHurtTime > Generator->RegenDelay) Health = FMath::Min(MaxHealth, Health + Generator->RegenPerSecond * Dt);
}
