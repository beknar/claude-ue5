#include "RD/RDCombat.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDMonster.h"
#include "RD/RDBlood.h"
#include "Sound/SoundBase.h"
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
#include "InputKeyEventArgs.h"
#include "Components/PointLightComponent.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "NiagaraSystemInstance.h"
#include "NiagaraSystemInstanceController.h"
#include "NiagaraEmitterInstance.h"
#include "Particles/ParticleSystem.h"
#include "Particles/ParticleSystemComponent.h"
#include "UObject/UnrealType.h"
#include "GameFramework/RootMotionSource.h"
#include "GameFramework/Controller.h"

static const FName RDCombatSlot(TEXT("DefaultSlot"));

URDCombatComponent::URDCombatComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

const FRDWeaponDef* URDCombatComponent::Weapon() const
{
	return Generator && Generator->Weapons.IsValidIndex(WeaponIndex) ? &Generator->Weapons[WeaponIndex] : nullptr;
}

const FRDWeaponDef* URDCombatComponent::AttackWeapon() const
{
	return AttackTime >= 0.f && Generator && Generator->Weapons.IsValidIndex(AttackIndex) ? &Generator->Weapons[AttackIndex] : Weapon();
}

int32 URDCombatComponent::GetAlongsideSpell() const
{
	if (Generator)
		for (int32 I = 0; I < Generator->Weapons.Num(); ++I)
			if (Generator->Weapons[I].bSpell && Generator->Weapons[I].bAlongside) return I;
	return -1;
}

bool URDCombatComponent::StartSpell()
{
	const int32 I = GetAlongsideSpell();
	return I >= 0 && StartAttackWith(I);
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
	MaxMana = Mana = Generator ? Generator->PlayerMaxMana : 0.f;
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
	// (the weapons carried on her body while another is drawn, the bolt lying on the crossbow)
	HolsterComps.Reset();
	if (Generator)
		for (int32 I = 0; I < Generator->Weapons.Num(); ++I)
		{
			const FRDWeaponDef& W = Generator->Weapons[I];
			for (int32 K = 0; K < 2; ++K)
			{
				const FName Bone = K == 0 ? W.HolsterBone : W.OffHandHolsterBone;
				UStaticMesh* Mesh = K == 0 ? W.Mesh.Get() : W.OffHandMesh.Get();
				UStaticMeshComponent* C = nullptr;
				if (!Bone.IsNone() && Mesh && M)
				{
					C = Make(*FString::Printf(TEXT("RDHolster%d_%d"), I, K));
					C->SetStaticMesh(Mesh);
					C->AttachToComponent(M, FAttachmentTransformRules::SnapToTargetNotIncludingScale, Bone);
					C->SetRelativeTransform(K == 0 ? W.HolsterGrip : W.OffHandHolsterGrip);
					C->SetVisibility(false);
				}
				HolsterComps.Add(C);
			}
		}
	LoadedBoltComp = Make(TEXT("RDLoadedBolt")); LoadedBoltComp->SetVisibility(false);
	SelectWeapon(0);
}

void URDCombatComponent::SelectWeapon(int32 Index)
{
	if (!Generator || !Generator->Weapons.IsValidIndex(Index) || Index == WeaponIndex || bDead || Generator->Weapons[Index].bAlongside) return;
	if (AttackTime >= 0.f) EndAttack();
	if (WeaponIndex >= 0 && GetOwner()) Generator->PlaySoundAt(TEXT("Player.Draw"), GetOwner()->GetActorLocation());
	WeaponIndex = Index;
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
	for (int32 I = 0; I < HolsterComps.Num(); ++I)
		if (UStaticMeshComponent* C = HolsterComps[I]) C->SetVisibility(I / 2 != Index);
	if (LoadedBoltComp)
	{
		LoadedBoltComp->SetStaticMesh(W.BoltMesh);
		if (WeaponComp && W.BoltMesh) { LoadedBoltComp->AttachToComponent(WeaponComp, FAttachmentTransformRules::SnapToTargetNotIncludingScale); LoadedBoltComp->SetRelativeTransform(W.LoadedBoltTransform); }
		ShowLoadedBolt(true);
	}
}

void URDCombatComponent::ShowLoadedBolt(bool bShow)
{
	const FRDWeaponDef* W = Weapon();
	if (LoadedBoltComp) LoadedBoltComp->SetVisibility(bShow && W && W->bShowLoadedBolt && W->BoltMesh != nullptr);
}

UStaticMeshComponent* URDCombatComponent::GetHolsterMesh(int32 Index, bool bOffHand) const
{
	const int32 I = Index * 2 + (bOffHand ? 1 : 0);
	return HolsterComps.IsValidIndex(I) ? HolsterComps[I].Get() : nullptr;
}

void URDCombatComponent::NextWeapon(int32 Step)
{
	if (!Generator) return;
	const int32 N = Generator->Weapons.Num();
	for (int32 K = 1; K <= N; ++K)
	{
		const int32 I = ((WeaponIndex + Step * K) % N + N) % N;
		if (!Generator->Weapons[I].bAlongside) { SelectWeapon(I); return; }
	}
}

void URDCombatComponent::SetSlowed(bool bSlow)
{
	if (bSlow == bSlowed) return;
	bSlowed = bSlow;
	UpdateWalkSpeed();
}

void URDCombatComponent::UpdateWalkSpeed()
{
	ACharacter* C = Cast<ACharacter>(GetOwner());
	if (!C) return;
	UCharacterMovementComponent* CM = C->GetCharacterMovement();
	// her own top speed while nothing changes it; slowed in an attack, faster under a speed potion
	const float K = (bSlowed ? 0.12f : 1.f) * (1.f + GetSpeedBonus());
	if (FMath::IsNearlyEqual(K, 1.f))
	{
		if (bSpeedOverride) { CM->MaxWalkSpeed = SavedWalkSpeed; bSpeedOverride = false; }
		return;
	}
	if (!bSpeedOverride) { SavedWalkSpeed = CM->MaxWalkSpeed; bSpeedOverride = true; }
	CM->MaxWalkSpeed = SavedWalkSpeed * K;
}

float URDCombatComponent::GetBaseWalkSpeed() const
{
	if (bSpeedOverride) return SavedWalkSpeed;
	const ACharacter* C = Cast<ACharacter>(GetOwner());
	return C ? C->GetCharacterMovement()->MaxWalkSpeed : 0.f;
}

float URDCombatComponent::GetDamageOf(int32 Index) const
{
	if (!Generator || !Generator->Weapons.IsValidIndex(Index)) return 0.f;
	const FRDWeaponDef& W = Generator->Weapons[Index];
	// (a melee weapon: no bolt; a ranged one: a spell whose bolt is a mesh, the crossbow; magic has no bonus)
	const float Bonus = !W.bSpell ? Generator->MeleeBonus : W.BoltMesh ? Generator->RangedBonus : 0.f;
	return W.Damage * (1.f + Bonus);
}

bool URDCombatComponent::StartAttack()
{
	return StartAttackWith(WeaponIndex);
}

bool URDCombatComponent::StartAttackWith(int32 Index)
{
	const FRDWeaponDef* W = Generator && Generator->Weapons.IsValidIndex(Index) ? &Generator->Weapons[Index] : nullptr;
	USkeletalMeshComponent* M = Body();
	if (!W || !M || bDead || AttackTime >= 0.f || RollTime >= 0.f || W->Attacks.Num() == 0 || bInventoryOpen) return false;
	// (a spell that costs more mana than she has is not cast)
	if (W->ManaCost > 0.f && Mana < W->ManaCost)
	{
		const float Now = GetWorld()->GetTimeSeconds();
		if (Now - NoManaTime > 0.6f) { ++CastsRefused; SetMessage(FString::Printf(TEXT("Not enough mana for %s"), *W->Name.ToString())); Generator->PlaySoundAt(TEXT("Player.NoMana"), GetOwner()->GetActorLocation()); }
		NoManaTime = Now;
		return false;
	}
	UAnimInstance* AI = M->GetAnimInstance();
	if (NextOf.Num() < Generator->Weapons.Num()) NextOf.SetNumZeroed(Generator->Weapons.Num());
	const int32 NextAttack = NextOf[Index], K = NextAttack % W->Attacks.Num();
	UAnimSequenceBase* Clip = W->Attacks[K];
	if (!AI || !Clip) return false;
	AttackIndex = Index;
	const float Rate = FMath::Max(W->PlayRate, 0.1f);
	const float T0 = W->AttackStarts.IsValidIndex(K) ? W->AttackStarts[K] : 0.f;
	const float T1 = W->AttackEnds.IsValidIndex(K) && W->AttackEnds[K] > T0 ? W->AttackEnds[K] : Clip->GetPlayLength();
	const float Hit = W->HitTimes.IsValidIndex(K) ? W->HitTimes[K] : (T0 + T1) * 0.5f;
	LastTarget = nullptr;
	if (W->bSpell)
	{
		// a spell: she turns to the nearest monster in front of her within its reach that she can see, and the charge
		// lights on her hand
		if (AActor* O = GetOwner())
			if (ARDMonster* Best = PickTarget(W->Reach, true))
			{
				LastTarget = Best;
				O->SetActorRotation(FRotator(0.f, ((Best->GetActorLocation() - O->GetActorLocation()) * FVector(1, 1, 0)).Rotation().Yaw, 0.f));
			}
		StopCharge();
		if (W->ChargeEffect) ChargeComp = SpawnFx(W->ChargeEffect, FVector::ZeroVector, FRotator::ZeroRotator, W->ChargeEffectScale, M, W->SpellBone);
		Generator->PlaySoundAt(FName(*FString::Printf(TEXT("Player.Charge.%s"), *W->Name.ToString())), GetOwner()->GetActorLocation());
	}
	// she turns to the nearest monster in front of her that the weapon could reach in a step (no need to line up by hand)
	else if (AActor* O = GetOwner())
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
	bWhooshDone = false;
	if (NextAttack % 2 == 0) Generator->PlaySoundAt(TEXT("Player.Attack"), GetOwner()->GetActorLocation());      // (her effort: every other swing)
	++NextOf[Index]; ++AttacksMade;
	if (W->ManaCost > 0.f) Mana = FMath::Max(0.f, Mana - W->ManaCost);
	SetSlowed(true);
	return true;
}

void URDCombatComponent::Strike()
{
	const FRDWeaponDef* W = AttackWeapon();
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
		Generator->PlaySoundAt(FName(*FString::Printf(TEXT("Player.Hit.%s"), *W->Name.ToString())), Mo->GetActorLocation());
		const float Dmg = GetDamageOf(AttackIndex);         // (with her melee bonus)
		const bool bKilled = Mo->ApplyDamage(Dmg, O);
		Generator->AddHitText(Mo->GetActorLocation() + FVector(0, 0, Mo->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()), Dmg, false);
		DamageDealt += Dmg; ++HitsLanded; bAny = true;
		if (bKilled) ++Kills;
	}
	if (bAny) LastHitTime = GetWorld()->GetTimeSeconds();
}

void URDCombatComponent::EndAttack()
{
	AttackTime = -1.f;
	SetSlowed(false);
	StopCharge();
	ShowLoadedBolt(true);
}

void URDCombatComponent::ApplyDamage(float Amount, AActor* From)
{
	if (bDead || Amount <= 0.f) return;
	if (IsDodging()) { ++DodgedHits; return; }
	const float Now = GetWorld()->GetTimeSeconds();
	Health = FMath::Max(0.f, Health - Amount);
	DamageTaken += Amount; ++HitsTaken; LastHurtTime = Now;
	AActor* O = GetOwner();
	if (Generator && O)
	{
		Generator->AddHitText(O->GetActorLocation() + FVector(0, 0, 90.f), Amount, true);
		// blood from where it caught her (toward the attacker, at a height that differs from blow to blow)
		const FVector L = O->GetActorLocation();
		const FVector To = From ? ((From->GetActorLocation() - L) * FVector(1, 1, 0)).GetSafeNormal(1e-4f, O->GetActorForwardVector()) : O->GetActorForwardVector();
		const FVector At = L + To * 16.f + FVector(0, 0, 14.f + 11.f * ((HitsTaken * 37) % 5));
		if (URDBloodComponent* B = Generator->GetBlood()) B->Burst(At, To * 0.7f + FVector(0, 0, 0.3f), FMath::Clamp(Amount / FMath::Max(MaxHealth, 1.f) * 3.f, 0.35f, 1.f));
		Generator->PlaySoundAt(TEXT("Monster.Strike"), At);
		Generator->PlaySoundAt(TEXT("Blood.Splat"), At);
		Generator->PlaySoundAt(Health <= 0.f ? TEXT("Player.Death") : TEXT("Player.Hurt"), L);
	}
	USkeletalMeshComponent* M = Body();
	UAnimInstance* AI = M ? M->GetAnimInstance() : nullptr;
	const FRDWeaponDef* W = Weapon();
	if (Health <= 0.f)
	{
		bDead = true; ++Deaths; DeathTime = Now; bFallDone = false;
		EndAttack(); EndRoll();
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
	bDead = false; Health = MaxHealth; Mana = MaxMana; AttackTime = -1.f; StaggerUntil = -100.f; StopCharge(); EndRoll(); ShowLoadedBolt(true);
	Effects.Reset(); SetSlowed(false); UpdateWalkSpeed();
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
	TickSounds(Dt, Now);
	TickBolts(Dt);
	if (bDead)
	{
		if (Now - DeathTime > Generator->RespawnSeconds) Revive(true);
		return;
	}
	if (Generator->bCasterControls)
		if (const APawn* P = Cast<APawn>(GetOwner()))
			if (const APlayerController* PC = Cast<APlayerController>(P->GetController())) TickDevice(PC);
	if (!bScriptedOnly && (!Generator->bMapOpen || Generator->bTacticalMaps))        // (the tactical map is an overlay: she fights on under it)
		if (const APawn* P = Cast<APawn>(GetOwner()))
			if (const APlayerController* PC = Cast<APlayerController>(P->GetController()))
			{
				if (Generator->bCasterControls) TickCasterInput(PC);      // (the magic levels' layout)
				else
				{
					if (PC->WasInputKeyJustPressed(EKeys::One) || PC->WasInputKeyJustPressed(EKeys::Gamepad_DPad_Left)) SelectWeapon(0);
					if (PC->WasInputKeyJustPressed(EKeys::Two) || PC->WasInputKeyJustPressed(EKeys::Gamepad_DPad_Up)) SelectWeapon(1);
					if (PC->WasInputKeyJustPressed(EKeys::Three) || PC->WasInputKeyJustPressed(EKeys::Gamepad_DPad_Right)) SelectWeapon(2);
					// the drawn weapon: left mouse (X, RT); E too when it is a spell. A spell cast alongside it: right mouse or E (Y, LT)
					const bool bDrawnSpell = Weapon() && Weapon()->bSpell;
					if (PC->IsInputKeyDown(EKeys::LeftMouseButton) || PC->IsInputKeyDown(EKeys::Gamepad_FaceButton_Left) || PC->GetInputAnalogKeyState(EKeys::Gamepad_RightTriggerAxis) > 0.5f
						|| (bDrawnSpell && PC->IsInputKeyDown(EKeys::E))) StartAttack();
					else if (GetAlongsideSpell() >= 0 && (PC->IsInputKeyDown(EKeys::RightMouseButton) || PC->IsInputKeyDown(EKeys::E) || PC->IsInputKeyDown(EKeys::Gamepad_FaceButton_Top)
						|| PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftTriggerAxis) > 0.5f)) StartSpell();
				}
			}
	if (RollTime >= 0.f)
	{
		RollTime += Dt;
		if (RollTime >= RollLen) EndRoll();
	}
	if (AttackTime >= 0.f)
	{
		AttackTime += Dt;
		const bool bSpell = IsSpell();
		if (!bWhooshDone && !bSpell && AttackTime >= AttackHit - 0.16f) { bWhooshDone = true; Generator->PlaySoundAt(TEXT("Player.Whoosh"), GetOwner()->GetActorLocation()); }
		if (!bHitDone && AttackTime >= AttackHit) { bHitDone = true; if (bSpell) LaunchBolt(); else Strike(); }
		if (AttackTime >= AttackLen) EndAttack();
	}
	// out of a fight the hit points come back (not in random_dungeonmagic_level4: RegenPerSecond 0); mana comes back slowly
	if (Health < MaxHealth && Generator->RegenPerSecond > 0.f && Now - LastHurtTime > Generator->RegenDelay) Health = FMath::Min(MaxHealth, Health + Generator->RegenPerSecond * Dt);
	if (Mana < MaxMana) Mana = FMath::Min(MaxMana, Mana + Generator->ManaPerSecond * Dt);
	TickEffects(Dt);
}

// ------------------------------------------------------------------------------------------------ items, the inventory
void URDCombatComponent::SetMessage(const FString& Text)
{
	Message = Text;
	MessageTime = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
}

void URDCombatComponent::AddItem(FName Name, int32 Count)
{
	if (Name.IsNone() || Count <= 0) return;
	int32& N = Carried.FindOrAdd(Name);
	if (N == 0) CarriedOrder.AddUnique(Name);
	N += Count;
}

int32 URDCombatComponent::GetItemCount(FName Name) const
{
	const int32* N = Carried.Find(Name);
	return N ? *N : 0;
}

static FString RDItemLabel(FName Name) { return Name.ToString().ToLower(); }

bool URDCombatComponent::UseItem(FName Name)
{
	if (!Generator || bDead || GetItemCount(Name) <= 0) return false;
	const int32 Ix = Generator->FindItem(Name);
	if (Ix < 0) return false;
	const FRDItemDef& It = Generator->Items[Ix];
	const FString Lb = RDItemLabel(Name);
	switch (It.Kind)
	{
	case ERDItemKind::Healing:
	{
		if (Health >= MaxHealth) { SetMessage(TEXT("Your hit points are full")); return false; }
		const float Before = Health;
		Health = FMath::Min(MaxHealth, Health + MaxHealth * It.Amount);
		SetMessage(FString::Printf(TEXT("Drank the %s:  +%.0f HP"), *Lb, Health - Before));
		break;
	}
	case ERDItemKind::Mana:
	{
		if (MaxMana <= 0.f) { SetMessage(FString::Printf(TEXT("%s has no mana to restore"), *Generator->PlayerTitle)); return false; }
		if (Mana >= MaxMana) { SetMessage(TEXT("Your mana is full")); return false; }
		const float Before = Mana;
		Mana = FMath::Min(MaxMana, Mana + MaxMana * It.Amount);
		SetMessage(FString::Printf(TEXT("Drank the %s:  +%.0f mana"), *Lb, Mana - Before));
		break;
	}
	case ERDItemKind::Speed:
		Effects.Add({ It.Kind, It.Amount, It.Seconds, Name });
		UpdateWalkSpeed();
		SetMessage(FString::Printf(TEXT("Drank the %s:  +%.0f%% speed for %.0f s"), *Lb, It.Amount * 100.f, It.Seconds));
		break;
	case ERDItemKind::Food:
		if (Health >= MaxHealth) { SetMessage(TEXT("Your hit points are full")); return false; }
		Effects.Add({ It.Kind, It.Amount, It.Seconds, Name });
		SetMessage(FString::Printf(TEXT("Ate the %s:  +%.0f HP a second for %.0f s"), *Lb, MaxHealth * It.Amount, It.Seconds));
		break;
	}
	int32& N = Carried.FindOrAdd(Name);
	if (--N <= 0) { Carried.Remove(Name); CarriedOrder.Remove(Name); }
	++ItemsUsed;
	if (AActor* O = GetOwner()) Generator->PlaySoundAt(It.Kind == ERDItemKind::Food ? TEXT("Player.Eat") : TEXT("Player.Drink"), O->GetActorLocation());
	return true;
}

float URDCombatComponent::GetSpeedBonus() const
{
	float B = 0.f;
	for (const FEffect& E : Effects) if (E.Kind == ERDItemKind::Speed) B = FMath::Max(B, E.Amount);       // (speed potions do not add up: the strongest counts)
	return B;
}

float URDCombatComponent::GetRegenPerSecond() const
{
	float R = 0.f;
	for (const FEffect& E : Effects) if (E.Kind == ERDItemKind::Food) R += E.Amount * MaxHealth;
	return R;
}

void URDCombatComponent::TickEffects(float Dt)
{
	if (Effects.Num() == 0) return;
	const float Regen = GetRegenPerSecond();
	if (Regen > 0.f) Health = FMath::Min(MaxHealth, Health + Regen * Dt);
	const float SpeedBefore = GetSpeedBonus();
	for (int32 I = Effects.Num() - 1; I >= 0; --I)
		if ((Effects[I].Left -= Dt) <= 0.f) Effects.RemoveAt(I);
	if (!FMath::IsNearlyEqual(SpeedBefore, GetSpeedBonus())) UpdateWalkSpeed();
}

TArray<FString> URDCombatComponent::GetInventoryLines() const
{
	TArray<FString> Out;
	if (Generator)
		for (const FRDWeaponDef& W : Generator->Weapons) Out.Add(FString::Printf(TEXT("weapon|%s"), *W.Name.ToString()));
	for (const FName& N : CarriedOrder) Out.Add(FString::Printf(TEXT("item|%s|%d"), *N.ToString(), GetItemCount(N)));
	return Out;
}

void URDCombatComponent::SetInventoryOpen(bool bOpen)
{
	if (bOpen == bInventoryOpen || (bOpen && bDead)) return;
	bInventoryOpen = bOpen;
	if (bOpen) { if (AttackTime >= 0.f) EndAttack(); InventoryCursor = FMath::Clamp(InventoryCursor, 0, FMath::Max(0, GetInventoryLines().Num() - 1)); }
	// (the game stands still while it is open; the generator, which ticks while paused, works the inventory)
	if (bInventoryPausesGame || !bOpen) UGameplayStatics::SetGamePaused(this, bOpen);
	if (Generator && GetOwner()) Generator->PlaySoundAt(TEXT("Player.Inventory"), GetOwner()->GetActorLocation());
}

void URDCombatComponent::MoveInventoryCursor(int32 Step)
{
	const int32 N = GetInventoryLines().Num();
	if (N > 0) InventoryCursor = ((InventoryCursor + Step) % N + N) % N;
}

bool URDCombatComponent::UseInventoryEntry()
{
	const TArray<FString> Lines = GetInventoryLines();
	if (!Lines.IsValidIndex(InventoryCursor) || !Generator) return false;
	TArray<FString> P;
	Lines[InventoryCursor].ParseIntoArray(P, TEXT("|"));
	if (P.Num() >= 2 && P[0] == TEXT("weapon"))
	{
		const int32 I = InventoryCursor;
		const FRDWeaponDef& W = Generator->Weapons[I];
		if (W.bAlongside) { SetMessage(FString::Printf(TEXT("%s is always at hand (RMB / E)"), *W.Name.ToString())); return false; }
		if (I == WeaponIndex) { SetMessage(FString::Printf(TEXT("%s is in your hands"), *W.Name.ToString())); return false; }
		SelectWeapon(I);
		SetMessage(FString::Printf(TEXT("You wield the %s"), *W.Name.ToString().ToLower()));
		return true;
	}
	if (P.Num() >= 2 && P[0] == TEXT("item"))
	{
		const bool bOk = UseItem(FName(*P[1]));
		InventoryCursor = FMath::Clamp(InventoryCursor, 0, FMath::Max(0, GetInventoryLines().Num() - 1));
		return bOk;
	}
	return false;
}

void URDCombatComponent::TickInventory(APlayerController* PC)
{
	if (!PC || bScriptedOnly) return;
	auto Pressed = [PC](std::initializer_list<FKey> Keys) { for (const FKey& K : Keys) if (PC->WasInputKeyJustPressed(K)) return true; return false; };
	const bool bToggle = Pressed({ EKeys::I, EKeys::Tab, EKeys::Gamepad_Special_Right });
	if (!bInventoryOpen) { if (bToggle && !bDead) SetInventoryOpen(true); return; }
	if (bToggle || Pressed({ EKeys::Gamepad_FaceButton_Right })) { SetInventoryOpen(false); return; }
	if (Pressed({ EKeys::W, EKeys::Up, EKeys::MouseScrollUp, EKeys::Gamepad_DPad_Up })) MoveInventoryCursor(-1);
	if (Pressed({ EKeys::S, EKeys::Down, EKeys::MouseScrollDown, EKeys::Gamepad_DPad_Down })) MoveInventoryCursor(1);
	// (the left stick: a step when it is pushed, then one every 0.22 s while it is held)
	const float Sy = PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftY);
	if (FMath::Abs(Sy) > 0.6f)
	{
		const float Now = FPlatformTime::Seconds();
		if (Now > InventoryRepeat) { MoveInventoryCursor(Sy > 0.f ? -1 : 1); InventoryRepeat = Now + (InventoryRepeat > 0.f ? 0.22f : 0.4f); }
	}
	else InventoryRepeat = 0.f;
	if (Pressed({ EKeys::Enter, EKeys::SpaceBar, EKeys::E, EKeys::LeftMouseButton, EKeys::Gamepad_FaceButton_Bottom })) UseInventoryEntry();
}

// ------------------------------------------------------------------------------------------------ sound
void URDCombatComponent::TickSounds(float Dt, float Now)
{
	const ACharacter* C = Cast<ACharacter>(GetOwner());
	if (!C) return;
	if (bDead)
	{
		if (!bFallDone && Now - DeathTime > 0.9f) { bFallDone = true; Generator->PlaySoundAt(TEXT("Env.BodyFall"), C->GetActorLocation()); }
		return;
	}
	const float Speed = C->GetVelocity().Size2D();
	const bool bGround = C->GetCharacterMovement()->IsMovingOnGround();
	const bool bRun = Speed > 250.f;
	// a footstep for every stride on the ground: running strides are longer and have their own sounds
	if (bGround && Speed > 20.f)
	{
		StepDist += Speed * Dt;
		const float Stride = bRun ? 128.f : 72.f;
		if (StepDist >= Stride)
		{
			StepDist = 0.f; ++StepsTaken;
			Generator->PlaySoundAt(bRun ? TEXT("Player.Run") : TEXT("Player.Step"), C->GetActorLocation() - FVector(0, 0, C->GetSimpleCollisionHalfHeight()));
		}
	}
	else StepDist = FMath::Min(StepDist, 40.f);
}

bool URDCombatComponent::SimulateKey(FKey Key, bool bDown)
{
	const APawn* P = Cast<APawn>(GetOwner());
	APlayerController* PC = P ? Cast<APlayerController>(P->GetController()) : nullptr;
	return PC && PC->InputKey(FInputKeyEventArgs::CreateSimulated(Key, bDown ? IE_Pressed : IE_Released, bDown ? 1.f : 0.f));
}

bool URDCombatComponent::SimulateAxis(FKey Key, float Value)
{
	const APawn* P = Cast<APawn>(GetOwner());
	APlayerController* PC = P ? Cast<APlayerController>(P->GetController()) : nullptr;
	return PC && PC->InputKey(FInputKeyEventArgs::CreateSimulated(Key, IE_Axis, Value, 1));
}

// ------------------------------------------------------------------------------------------------ the magic levels' controls
void URDCombatComponent::SetRunMode(bool bRun)
{
	bRunMode = bRun;
	// (her character's MoveScale picks the run speed while its RunMode is on: a Blueprint variable, set by name)
	if (AActor* O = GetOwner())
		if (FBoolProperty* Pr = FindFProperty<FBoolProperty>(O->GetClass(), TEXT("RunMode"))) Pr->SetPropertyValue_InContainer(O, bRun);
}

void URDCombatComponent::TickDevice(const APlayerController* PC)
{
	// a button or a stick of the gamepad makes it the device in use; a key or the mouse makes it the keyboard again
	static const FKey PadKeys[] = {
		EKeys::Gamepad_FaceButton_Bottom, EKeys::Gamepad_FaceButton_Right, EKeys::Gamepad_FaceButton_Left, EKeys::Gamepad_FaceButton_Top,
		EKeys::Gamepad_LeftShoulder, EKeys::Gamepad_RightShoulder, EKeys::Gamepad_LeftTrigger, EKeys::Gamepad_RightTrigger,
		EKeys::Gamepad_DPad_Up, EKeys::Gamepad_DPad_Down, EKeys::Gamepad_DPad_Left, EKeys::Gamepad_DPad_Right,
		EKeys::Gamepad_LeftThumbstick, EKeys::Gamepad_RightThumbstick, EKeys::Gamepad_Special_Left, EKeys::Gamepad_Special_Right };
	static const FKey PadAxes[] = { EKeys::Gamepad_LeftX, EKeys::Gamepad_LeftY, EKeys::Gamepad_RightX, EKeys::Gamepad_RightY,
		EKeys::Gamepad_LeftTriggerAxis, EKeys::Gamepad_RightTriggerAxis };
	static const FKey KeyboardKeys[] = {
		EKeys::W, EKeys::A, EKeys::S, EKeys::D, EKeys::Up, EKeys::Down, EKeys::Left, EKeys::Right, EKeys::SpaceBar, EKeys::LeftShift,
		EKeys::E, EKeys::R, EKeys::F, EKeys::M, EKeys::B, EKeys::One, EKeys::Two, EKeys::Three, EKeys::LeftMouseButton, EKeys::RightMouseButton };
	for (const FKey& K : PadKeys) if (PC->IsInputKeyDown(K)) { bUsingGamepad = true; return; }
	for (const FKey& K : PadAxes) if (FMath::Abs(PC->GetInputAnalogKeyState(K)) > 0.3f) { bUsingGamepad = true; return; }
	for (const FKey& K : KeyboardKeys) if (PC->IsInputKeyDown(K)) { bUsingGamepad = false; return; }
	float Mx = 0.f, My = 0.f;
	PC->GetInputMouseDelta(Mx, My);
	if (Mx != 0.f || My != 0.f) bUsingGamepad = false;
}

void URDCombatComponent::TickCasterInput(const APlayerController* PC)
{
	if (PC->WasInputKeyJustPressed(EKeys::One) || PC->WasInputKeyJustPressed(EKeys::Gamepad_DPad_Left)) SelectWeapon(0);
	if (PC->WasInputKeyJustPressed(EKeys::Two) || PC->WasInputKeyJustPressed(EKeys::Gamepad_DPad_Up)) SelectWeapon(1);
	if (PC->WasInputKeyJustPressed(EKeys::Three) || PC->WasInputKeyJustPressed(EKeys::Gamepad_DPad_Right)) SelectWeapon(2);
	if (Generator->bRogueControls)
	{
		// (the rogue: the wheel or Y switch weapons, the left mouse button or RB uses the one in her hands, B rolls)
		if (PC->WasInputKeyJustPressed(EKeys::MouseScrollUp)) NextWeapon(-1);
		if (PC->WasInputKeyJustPressed(EKeys::MouseScrollDown) || PC->WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Top)) NextWeapon(1);
		if (PC->WasInputKeyJustPressed(EKeys::B) || PC->WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Right)) StartRoll(FVector::ZeroVector);
		if (PC->IsInputKeyDown(EKeys::LeftMouseButton) || PC->IsInputKeyDown(EKeys::Gamepad_RightShoulder)) StartAttack();
		const bool bToggleR = PC->IsInputKeyDown(EKeys::R) || PC->IsInputKeyDown(EKeys::Gamepad_LeftTrigger) || PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftTriggerAxis) > 0.5f;
		if (bToggleR && !bRunToggleDown) SetRunMode(!bRunMode);
		bRunToggleDown = bToggleR;
		return;
	}
	// (with heroes to choose, random_dungeonmagic_level4: the wheel or Y switch between her weapons, as the Rogue's do)
	if (Generator->Heroes.Num() > 0)
	{
		if (PC->WasInputKeyJustPressed(EKeys::MouseScrollUp)) NextWeapon(-1);
		if (PC->WasInputKeyJustPressed(EKeys::MouseScrollDown) || PC->WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Top)) NextWeapon(1);
	}
	// the weapon in her hand: left mouse or RB. The spell: right mouse, E or LB: the one cast alongside the drawn weapon,
	// or the drawn weapon itself when it is a spell (then the left mouse and RB cast it too)
	const bool bDrawnSpell = Weapon() && Weapon()->bSpell;
	const bool bAlongside = GetAlongsideSpell() >= 0;
	const bool bSpellKey = PC->IsInputKeyDown(EKeys::RightMouseButton) || PC->IsInputKeyDown(EKeys::E) || PC->IsInputKeyDown(EKeys::Gamepad_LeftShoulder);
	if (PC->IsInputKeyDown(EKeys::LeftMouseButton) || PC->IsInputKeyDown(EKeys::Gamepad_RightShoulder) || (bDrawnSpell && !bAlongside && bSpellKey)) StartAttack();
	else if (bAlongside && bSpellKey) StartSpell();
	// walking / running: R, or the left trigger pulled (its button, or the axis past half way for a pad that sends none)
	const bool bToggle = PC->IsInputKeyDown(EKeys::R) || PC->IsInputKeyDown(EKeys::Gamepad_LeftTrigger) || PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftTriggerAxis) > 0.5f;
	if (bToggle && !bRunToggleDown) SetRunMode(!bRunMode);
	bRunToggleDown = bToggle;
}

// ------------------------------------------------------------------------------------------------ spells
bool URDCombatComponent::IsSpell() const { const FRDWeaponDef* W = AttackWeapon(); return W && W->bSpell; }

bool URDCombatComponent::IsCharging() const { return ChargeComp != nullptr && ChargeComp->IsActive(); }

TArray<FVector> URDCombatComponent::GetBolts() const
{
	TArray<FVector> Out;
	for (const FBolt& B : Bolts) Out.Add(B.At);
	return Out;
}

int32 URDCombatComponent::GetSpellParticles(FVector Location, float Radius, int32& Systems) const
{
	int32 Num = 0; Systems = 0;
	for (const USceneComponent* C : SpellComps)
	{
		if (!IsValid(C) || (Radius > 0.f && FVector::DistSquared(C->GetComponentLocation(), Location) > Radius * Radius)) continue;
		int32 N = 0;
		if (const UNiagaraComponent* Nc = Cast<UNiagaraComponent>(C))
		{
			const FNiagaraSystemInstanceControllerConstPtr Ctl = Nc->GetSystemInstanceController();
			if (Ctl.IsValid() && Ctl->IsValid())
				if (const FNiagaraSystemInstance* SI = Ctl->GetSystemInstance_Unsafe())
					for (const FNiagaraEmitterInstanceRef& E : SI->GetEmitters()) N += E->GetNumParticles();
		}
		else if (const UParticleSystemComponent* Pc = Cast<UParticleSystemComponent>(C)) N = Pc->GetNumActiveParticles();
		else continue;
		Num += N; if (N > 0) ++Systems;
	}
	return Num;
}

UFXSystemComponent* URDCombatComponent::SpawnFx(UFXSystemAsset* Asset, const FVector& At, const FRotator& Rot, float Scale, USceneComponent* AttachTo, FName Socket)
{
	UFXSystemComponent* C = nullptr;
	if (UNiagaraSystem* Ns = Cast<UNiagaraSystem>(Asset))
		C = AttachTo ? UNiagaraFunctionLibrary::SpawnSystemAttached(Ns, AttachTo, Socket, FVector::ZeroVector, FRotator::ZeroRotator, FVector(Scale), EAttachLocation::SnapToTarget, true, ENCPoolMethod::None)
		             : UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, Ns, At, Rot, FVector(Scale), true, true, ENCPoolMethod::None, false);
	else if (UParticleSystem* Ps = Cast<UParticleSystem>(Asset))
		C = AttachTo ? UGameplayStatics::SpawnEmitterAttached(Ps, AttachTo, Socket, FVector::ZeroVector, FRotator::ZeroRotator, FVector(Scale), EAttachLocation::SnapToTarget, true)
		             : UGameplayStatics::SpawnEmitterAtLocation(this, Ps, At, Rot, FVector(Scale), true);
	if (C) SpellComps.Add(C);
	return C;
}

UPointLightComponent* URDCombatComponent::MakeLight(const FVector& At, const FLinearColor& Color, float Intensity, float Radius)
{
	if (Intensity <= 0.f || !GetOwner()) return nullptr;
	UPointLightComponent* L = NewObject<UPointLightComponent>(GetOwner());
	L->SetMobility(EComponentMobility::Movable);
	L->SetUsingAbsoluteLocation(true); L->SetUsingAbsoluteRotation(true);
	L->SetIntensityUnits(ELightUnits::Candelas);
	L->SetIntensity(Intensity); L->SetLightColor(Color); L->SetAttenuationRadius(Radius);
	L->SetCastShadows(false);
	L->RegisterComponent();
	L->SetWorldLocation(At);
	SpellComps.Add(L);
	return L;
}

bool URDCombatComponent::CanSee(const FVector& From, const AActor* Target) const
{
	// walls and doors are in the way; the monsters and she herself are not
	// (seen when any of three points of it is: its middle, higher up, and a little to either side; a door frame or a
	// table between her hand and its middle alone does not hide it)
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDSpellSight), false, GetOwner());
	for (const ARDMonster* Mo : Generator->GetMonsters()) if (Mo) Q.AddIgnoredActor(Mo);
	const FVector C = Target->GetActorLocation(), Side = FVector::CrossProduct((C - From).GetSafeNormal2D(), FVector::UpVector) * 25.f;
	for (const FVector& P : { C, C + FVector(0, 0, 45.f), C + Side + FVector(0, 0, 20.f), C - Side + FVector(0, 0, 20.f) })
	{
		FHitResult H;
		if (!GetWorld()->LineTraceSingleByChannel(H, From, P, ECC_Visibility, Q)) return true;
	}
	return false;
}

ARDMonster* URDCombatComponent::PickTarget(float Reach, bool bNeedSight) const
{
	const AActor* O = GetOwner();
	if (!O || !Generator) return nullptr;
	const FVector L = O->GetActorLocation(), Fw = O->GetActorForwardVector();
	ARDMonster* Best = nullptr; float BestScore = 1e18f;
	for (ARDMonster* Mo : Generator->GetMonsters())
	{
		if (!Mo || Mo->IsDead()) continue;
		const FVector D = (Mo->GetActorLocation() - L) * FVector(1, 1, 0);
		const float Dist = D.Size() - Mo->GetCapsuleComponent()->GetScaledCapsuleRadius();
		const float Dot = FVector::DotProduct(D.GetSafeNormal(), Fw);
		if (Dist > Reach || FMath::Abs(Mo->GetActorLocation().Z - L.Z) > 300.f || Dot < -0.5f) continue;
		// (the nearest, but one in front of her before one to the side)
		const float Score = Dist * (Dot > 0.5f ? 1.f : 1.8f);
		if (Score >= BestScore || (bNeedSight && !CanSee(L + FVector(0, 0, 50.f), Mo))) continue;
		BestScore = Score; Best = Mo;
	}
	return Best;
}

void URDCombatComponent::StopCharge()
{
	if (ChargeComp) ChargeComp->Deactivate();
	ChargeComp = nullptr;
}

void URDCombatComponent::LaunchBolt()
{
	const FRDWeaponDef* W = AttackWeapon();
	USkeletalMeshComponent* M = Body();
	AActor* O = GetOwner();
	if (!W || !M || !O) return;
	// the charge is the bolt: it leaves her hand (otherwise it goes out and the bolt is a system of its own)
	UFXSystemComponent* Grown = (ChargeComp && W->ChargeEffect && W->ChargeEffect == W->BoltEffect) ? ChargeComp.Get() : nullptr;
	if (Grown) { ChargeComp = nullptr; Grown->DetachFromComponent(FDetachmentTransformRules::KeepWorldTransform); Grown->SetWorldScale3D(FVector(W->BoltEffectScale)); }
	else StopCharge();
	const FVector Fw = O->GetActorForwardVector();
	FBolt B;
	B.At = (W->bBoltFromWeapon && WeaponComp) ? WeaponComp->GetComponentTransform().TransformPosition(W->BoltMuzzle) : M->GetSocketLocation(W->SpellBone) + Fw * 12.f;
	B.Weapon = AttackIndex;
	ARDMonster* Tg = LastTarget.Get();
	if (Tg && !Tg->IsDead())
	{
		B.Target = Tg;
		B.Vel = (Tg->GetActorLocation() + FVector(0, 0, Tg->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() * 0.15f) - B.At).GetSafeNormal() * W->BoltSpeed;
	}
	else B.Vel = Fw * W->BoltSpeed;
	const FRotator R = B.Vel.Rotation();
	if (Grown) { Grown->SetWorldLocationAndRotation(B.At, R); B.Fx = Grown; }
	else if (W->BoltEffect) B.Fx = SpawnFx(W->BoltEffect, B.At, R, W->BoltEffectScale);
	if (W->BoltCoreEffect) B.Core = SpawnFx(W->BoltCoreEffect, B.At, R, W->BoltCoreEffectScale);
	B.Light = MakeLight(B.At, W->SpellLightColor, W->SpellLightIntensity, 900.f);
	if (W->BoltMesh)
	{
		UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(O);
		C->SetMobility(EComponentMobility::Movable);
		C->SetCollisionEnabled(ECollisionEnabled::NoCollision); C->SetGenerateOverlapEvents(false); C->SetCanEverAffectNavigation(false);
		C->SetUsingAbsoluteLocation(true); C->SetUsingAbsoluteRotation(true); C->SetUsingAbsoluteScale(true);
		C->SetStaticMesh(W->BoltMesh);
		C->RegisterComponent();
		PlaceBoltMesh(C, *W, B.At, B.Vel);
		SpellComps.Add(C); B.Mesh = C;
		ShowLoadedBolt(false);
	}
	Bolts.Add(B);
	++BoltsCast; LastBoltFrom = B.At;
	Generator->PlaySoundAt(FName(*FString::Printf(TEXT("Player.Cast.%s"), *W->Name.ToString())), B.At);
}

void URDCombatComponent::PlaceBoltMesh(UStaticMeshComponent* C, const FRDWeaponDef& W, const FVector& At, const FVector& Dir) const
{
	if (C) C->SetWorldTransform(W.BoltMeshTransform * FTransform(Dir.Rotation(), At));
}

void URDCombatComponent::Burst(FBolt& B, const FVector& At, ARDMonster* Direct)
{
	if (!Generator->Weapons.IsValidIndex(B.Weapon)) return;
	const FRDWeaponDef& W = Generator->Weapons[B.Weapon];
	AActor* O = GetOwner();
	if (W.BurstEffect) SpawnFx(W.BurstEffect, At, B.Vel.Rotation(), W.BurstEffectScale);
	if (W.BurstFlameEffect)
		if (UFXSystemComponent* Fl = SpawnFx(W.BurstFlameEffect, At, FRotator::ZeroRotator, W.BurstFlameEffectScale)) TimedFx.Add({ Fl, W.BurstFlameSeconds });
	Generator->PlaySoundAt(FName(*FString::Printf(TEXT("Player.Hit.%s"), *W.Name.ToString())), At);
	// the flames on the bolt die away where they are (their particles finish); its light flares and fades
	if (UFXSystemComponent* F = B.Fx.Get()) F->Deactivate();
	if (UFXSystemComponent* F = B.Core.Get()) F->Deactivate();
	if (UPointLightComponent* L = B.Light.Get()) { L->SetWorldLocation(At); Flashes.Add({ L, 0.f, W.SpellLightIntensity * 3.f }); }
	bool bAny = false;
	auto Hurt = [&](ARDMonster* Mo, float Amount, const FVector& Where)
	{
		const bool bKilled = Mo->ApplyDamageAt(Amount, O, &Where);
		Generator->AddHitText(Mo->GetActorLocation() + FVector(0, 0, Mo->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()), Amount, false);
		DamageDealt += Amount; ++HitsLanded; bAny = true;
		if (bKilled) ++Kills;
	};
	const float Dmg = GetDamageOf(B.Weapon);       // (with her ranged bonus for a crossbow's bolt)
	if (Direct && !Direct->IsDead()) Hurt(Direct, Dmg, At);
	for (ARDMonster* Mo : Generator->GetMonsters())
	{
		if (!Mo || Mo == Direct || Mo->IsDead()) continue;
		const FVector C = Mo->GetActorLocation();
		const float Gap = FVector::Dist(C * FVector(1, 1, 0), At * FVector(1, 1, 0)) - Mo->GetCapsuleComponent()->GetScaledCapsuleRadius();
		if (Gap > W.BoltSplash || FMath::Abs(C.Z - At.Z) > Mo->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 80.f) continue;
		Hurt(Mo, Dmg * 0.5f, C + ((At - C) * FVector(1, 1, 0)).GetSafeNormal() * Mo->GetCapsuleComponent()->GetScaledCapsuleRadius() * 0.8f);
	}
	if (bAny) LastHitTime = GetWorld()->GetTimeSeconds();
	(Direct ? BoltsOnMonsters : BoltsElsewhere)++;
	LastBurstAt = At; LastBoltFlown = B.Flown;
}

void URDCombatComponent::TickBolts(float Dt)
{
	// the bursts' light
	for (int32 I = Flashes.Num() - 1; I >= 0; --I)
	{
		FFlash& F = Flashes[I]; F.Age += Dt;
		UPointLightComponent* L = F.Light.Get();
		const float K = 1.f - F.Age / 0.45f;
		if (!L || K <= 0.f) { if (L) L->DestroyComponent(); Flashes.RemoveAt(I); continue; }
		L->SetIntensity(F.Peak * K * K);
	}
	for (int32 I = TimedFx.Num() - 1; I >= 0; --I)
	{
		TimedFx[I].Left -= Dt;
		if (TimedFx[I].Left > 0.f && TimedFx[I].Fx.IsValid()) continue;
		if (UFXSystemComponent* F = TimedFx[I].Fx.Get()) F->Deactivate();
		TimedFx.RemoveAt(I);
	}
	for (int32 I = Stuck.Num() - 1; I >= 0; --I)
	{
		Stuck[I].Left -= Dt;
		if (Stuck[I].Left > 0.f && Stuck[I].Mesh.IsValid()) continue;
		if (UStaticMeshComponent* C = Stuck[I].Mesh.Get()) C->DestroyComponent();
		Stuck.RemoveAt(I);
	}
	SpellComps.RemoveAll([](const TObjectPtr<USceneComponent>& C) { return !IsValid(C); });
	if (Bolts.Num() == 0 || !Generator) return;
	const AActor* O = GetOwner();
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDBolt), false, O);
	for (const ARDMonster* Mo : Generator->GetMonsters()) if (Mo) Q.AddIgnoredActor(Mo);
	for (int32 I = Bolts.Num() - 1; I >= 0; --I)
	{
		FBolt& B = Bolts[I];
		if (!Generator->Weapons.IsValidIndex(B.Weapon)) { Bolts.RemoveAt(I); continue; }
		const FRDWeaponDef& W = Generator->Weapons[B.Weapon];
		// it steers after its monster (as far as it can turn)
		const float Speed = B.Vel.Size();
		if (ARDMonster* Tg = B.Target.Get())
			if (!Tg->IsDead())
			{
				const FVector Want = (Tg->GetActorLocation() + FVector(0, 0, Tg->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() * 0.15f) - B.At).GetSafeNormal();
				const FVector Cur = B.Vel.GetSafeNormal();
				const float Ang = FMath::Acos(FMath::Clamp(FVector::DotProduct(Cur, Want), -1.f, 1.f)), MaxAng = FMath::DegreesToRadians(W.BoltTurnRate) * Dt;
				const FQuat Turn = FQuat::FindBetweenNormals(Cur, Want);
				B.Vel = (Ang <= MaxAng ? Want : FQuat::Slerp(FQuat::Identity, Turn, MaxAng / FMath::Max(Ang, 1e-4f)).RotateVector(Cur)) * Speed;
			}
		const FVector Next = B.At + B.Vel * Dt;
		// the first monster on the way (the bolt against each capsule's axis), then the first wall
		ARDMonster* HitMo = nullptr; float HitT = 2.f; FVector HitAt = Next;
		for (ARDMonster* Mo : Generator->GetMonsters())
		{
			if (!Mo || Mo->IsDead()) continue;
			const UCapsuleComponent* Cap = Mo->GetCapsuleComponent();
			const float R = Cap->GetScaledCapsuleRadius(), Hh = Cap->GetScaledCapsuleHalfHeight();
			const FVector C = Mo->GetActorLocation(), A0 = C - FVector(0, 0, Hh - R), A1 = C + FVector(0, 0, Hh - R);
			FVector P, Qp;
			FMath::SegmentDistToSegmentSafe(B.At, Next, A0, A1, P, Qp);
			if (FVector::Dist(P, Qp) > R + 14.f) continue;
			const float T = (Next - B.At).IsNearlyZero() ? 0.f : FVector::DotProduct(P - B.At, Next - B.At) / (Next - B.At).SizeSquared();
			if (T < HitT) { HitT = T; HitMo = Mo; HitAt = Qp + (P - Qp).GetSafeNormal() * R * 0.85f; }
		}
		FHitResult H;
		if (GetWorld()->LineTraceSingleByChannel(H, B.At, Next, ECC_Visibility, Q) && H.Time < HitT)
		{
			B.Flown += (H.ImpactPoint - B.At).Size();
			Burst(B, H.ImpactPoint + H.ImpactNormal * 10.f, nullptr);
			// (a bolt mesh stays stuck in the wall a while, its point a little way in)
			if (UStaticMeshComponent* C = B.Mesh.Get())
			{
				if (W.BoltStickSeconds > 0.f) { PlaceBoltMesh(C, W, H.ImpactPoint + B.Vel.GetSafeNormal() * 4.f, B.Vel); Stuck.Add({ C, W.BoltStickSeconds }); }
				else C->DestroyComponent();
			}
			Bolts.RemoveAt(I); continue;
		}
		if (HitMo)
		{
			B.Flown += (HitAt - B.At).Size();
			Burst(B, HitAt, HitMo);
			if (UStaticMeshComponent* C = B.Mesh.Get()) C->DestroyComponent();
			Bolts.RemoveAt(I); continue;
		}
		B.Flown += (Next - B.At).Size(); B.At = Next;
		if (B.Flown >= W.Reach + 150.f)
		{
			Burst(B, B.At, nullptr);
			if (UStaticMeshComponent* C = B.Mesh.Get()) C->DestroyComponent();
			Bolts.RemoveAt(I); continue;
		}
		if (UStaticMeshComponent* C = B.Mesh.Get()) PlaceBoltMesh(C, W, B.At, B.Vel);
		if (UFXSystemComponent* F = B.Fx.Get()) F->SetWorldLocationAndRotation(B.At, B.Vel.Rotation());
		if (UFXSystemComponent* F = B.Core.Get()) F->SetWorldLocationAndRotation(B.At, B.Vel.Rotation());
		if (UPointLightComponent* L = B.Light.Get()) L->SetWorldLocation(B.At);
	}
}

// ------------------------------------------------------------------------------------------------ the roll
bool URDCombatComponent::IsDodging() const
{
	if (RollTime < 0.f || RollLen <= 0.f || !Generator) return false;
	const float K = RollTime / RollLen;
	return K >= Generator->RollDodge.X && K <= Generator->RollDodge.Y;
}

bool URDCombatComponent::StartRoll(FVector Dir)
{
	ACharacter* C = Cast<ACharacter>(GetOwner());
	USkeletalMeshComponent* M = Body();
	UAnimInstance* AI = M ? M->GetAnimInstance() : nullptr;
	if (!C || !AI || !Generator || !Generator->RollClip || bDead || RollTime >= 0.f) return false;
	const float Now = GetWorld()->GetTimeSeconds();
	UCharacterMovementComponent* CM = C->GetCharacterMovement();
	if (Now < RollReadyAt || !CM->IsMovingOnGround()) return false;
	// the way: given, or the way she is being moved (the keys or the stick), or the way she is going; standing: backward
	Dir.Z = 0.f;
	if (Dir.IsNearlyZero()) Dir = CM->GetCurrentAcceleration() * FVector(1, 1, 0);
	if (Dir.IsNearlyZero() && C->GetVelocity().Size2D() > 150.f) Dir = C->GetVelocity() * FVector(1, 1, 0);
	// (a way behind her is a roll backward: she keeps facing the way she does, as when she stands)
	const FVector Fw = (C->GetActorForwardVector() * FVector(1, 1, 0)).GetSafeNormal();
	bRollBack = Dir.IsNearlyZero() || FVector::DotProduct(Dir.GetSafeNormal(), Fw) < -0.7f;
	Dir = Dir.IsNearlyZero() ? -Fw : Dir;
	Dir = Dir.GetSafeNormal();
	if (Dir.IsNearlyZero()) return false;
	if (AttackTime >= 0.f) EndAttack();                      // (a roll breaks off an attack)
	if (!bRollBack) C->SetActorRotation(FRotator(0.f, Dir.Rotation().Yaw, 0.f));
	UAnimSequenceBase* Clip = (bRollBack && Generator->RollBackClip) ? Generator->RollBackClip.Get() : Generator->RollClip.Get();
	AI->PlaySlotAnimationAsDynamicMontage(Clip, RDCombatSlot, 0.06f, 0.16f, 1.f, 1, -1.f, 0.f);
	RollLen = Clip->GetPlayLength(); RollTime = 0.f;
	// she is carried along the floor for most of the clip (her own fall and steps stay the movement's)
	TSharedPtr<FRootMotionSource_ConstantForce> F = MakeShared<FRootMotionSource_ConstantForce>();
	F->InstanceName = TEXT("RDRoll");
	F->AccumulateMode = ERootMotionAccumulateMode::Override;
	F->Settings.SetFlag(ERootMotionSourceSettingsFlags::IgnoreZAccumulate);
	F->Priority = 5;
	F->Duration = RollLen * 0.82f;
	F->Force = Dir * (Generator->RollDistance / F->Duration);
	F->FinishVelocityParams.Mode = ERootMotionFinishVelocityMode::ClampVelocity;
	F->FinishVelocityParams.ClampVelocity = 120.f;
	RollSourceId = CM->ApplyRootMotionSource(F);
	if (AController* Ctl = C->GetController()) { Ctl->SetIgnoreMoveInput(true); bRollIgnoringMove = true; }
	++Rolls;
	Generator->PlaySoundAt(TEXT("Player.Roll"), C->GetActorLocation());
	return true;
}

void URDCombatComponent::EndRoll()
{
	if (RollTime < 0.f) return;
	RollTime = -1.f;
	ACharacter* C = Cast<ACharacter>(GetOwner());
	if (C && RollSourceId) C->GetCharacterMovement()->RemoveRootMotionSourceByID(RollSourceId);
	RollSourceId = 0;
	if (bRollIgnoringMove && C && C->GetController()) C->GetController()->SetIgnoreMoveInput(false);
	bRollIgnoringMove = false;
	if (Generator) RollReadyAt = GetWorld()->GetTimeSeconds() + Generator->RollCooldown;
}
