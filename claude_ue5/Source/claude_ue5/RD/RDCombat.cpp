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
#include "Engine/SkeletalMesh.h"
#include "Rendering/SkeletalMeshLODRenderData.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "Rendering/SkinWeightVertexBuffer.h"
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
	LeftComp = Make(TEXT("RDLeftHand")); LeftComp->SetVisibility(false);          // (mistward: her shield or her torch)
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
	SyncWear();
	SelectWeapon(0);
	// (level 5: the spells' own stream: a veil's misses; never the play's)
	SpellR.Initialize(Generator ? (int32)HashCombine((uint32)Generator->SessionSeed, 0x5E11u) : 7);
}

// ------------------------------------------------------------------------------------------------ found weapons (level 5)
void URDCombatComponent::SyncWear()
{
	if (!Generator) return;
	// (a weapon the list has more of than the wear array: full durability; the list's own order otherwise)
	while (Wear.Num() < Generator->Weapons.Num()) Wear.Add(Generator->Weapons[Wear.Num()].Durability);
	Wear.SetNum(Generator->Weapons.Num());
}

float URDCombatComponent::GetWeaponDurability(int32 Index) const
{
	return Generator && Generator->Weapons.IsValidIndex(Index) ? Generator->Weapons[Index].Durability : 0.f;
}

void URDCombatComponent::WearOut(int32 Index)
{
	if (!Generator || !Generator->Weapons.IsValidIndex(Index) || Generator->Weapons[Index].Durability <= 0.f) return;
	SyncWear();
	if (Wear[Index] <= 0.f) return;
	Wear[Index] = FMath::Max(0.f, Wear[Index] - 1.f);
	if (Wear[Index] <= 0.f) PendingBreak.AddUnique(Index);
}

void URDCombatComponent::BreakWeapon(int32 Index)
{
	if (!Generator || !Generator->Weapons.IsValidIndex(Index)) return;
	const FRDWeaponDef W = Generator->Weapons[Index];
	if (AttackTime >= 0.f && AttackIndex == Index) EndAttack();
	const bool bDrawn = Index == WeaponIndex;
	Generator->Weapons.RemoveAt(Index);
	if (Wear.IsValidIndex(Index)) Wear.RemoveAt(Index);
	if (NextOf.IsValidIndex(Index)) NextOf.RemoveAt(Index);
	// (the bolts still on their way: theirs is gone, the others' indices move down)
	Bolts.RemoveAll([Index](const FBolt& B) { return B.Weapon == Index; });
	for (FBolt& B : Bolts) if (B.Weapon > Index) --B.Weapon;
	for (int32& P : PendingBreak) if (P > Index) --P;
	if (AttackIndex > Index) --AttackIndex;
	++WeaponsBroken; LastBroken = W.Name;
	SetMessage(FString::Printf(TEXT("Your %s broke"), *W.Name.ToString().ToLower()));
	if (AActor* O = GetOwner()) Generator->PlaySoundAt(TEXT("Player.Break"), O->GetActorLocation());
	UE_LOG(LogTemp, Log, TEXT("RDWEAPON %s broke (%d weapons left)"), *W.Name.ToString(), Generator->Weapons.Num());
	if (bDrawn)
	{
		// (she draws the first of her weapons that is not cast alongside: one she started with)
		WeaponIndex = -1;
		for (int32 I = 0; I < Generator->Weapons.Num(); ++I) if (!Generator->Weapons[I].bAlongside) { SelectWeapon(I); break; }
	}
	else if (WeaponIndex > Index) --WeaponIndex;
	InventoryCursor = FMath::Clamp(InventoryCursor, 0, FMath::Max(0, GetInventoryLines().Num() - 1));
}

bool URDCombatComponent::TakeWeapon(FName Item)
{
	const int32 Ix = Generator ? Generator->FindItem(Item) : -1;
	if (Ix < 0 || Generator->Items[Ix].Kind != ERDItemKind::Weapon) return false;
	const FRDItemDef& It = Generator->Items[Ix];
	const FRDWeaponFit* Fit = It.WeaponFits.FindByPredicate([this](const FRDWeaponFit& F) { return F.Hero == Generator->CurrentHero; });
	if (!Fit) return false;
	SyncWear();
	FRDWeaponDef W = Fit->Weapon;
	W.Item = Item;
	if (W.Durability <= 0.f) W.Durability = It.Amount;
	Generator->Weapons.Add(W);
	Wear.Add(W.Durability);
	++WeaponsTaken;
	return true;
}

void URDCombatComponent::ResetWeapons()
{
	if (AttackTime >= 0.f) EndAttack();
	Bolts.Reset(); PendingBreak.Reset(); NextOf.Reset(); Wear.Reset();
	WeaponIndex = -1;
	WeaponsBroken = WeaponsTaken = 0; LastBroken = NAME_None;
	SyncWear();
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
	UpdateLeftHand();          // (mistward: a shield or a torch in her left hand instead)
	UpdateWalkSpeed();
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
	// her own top speed while nothing changes it; slowed in an attack, faster under a speed potion, slower in armour
	// (mistward: slower with a shield in her hand by its speed rating; held fast by a snare or a pit)
	float ShieldSlow = 0.f;
	if (IsShieldInHand()) { const int32 Si = Generator->FindItem(WornShield); if (Si >= 0) ShieldSlow = Generator->Items[Si].Slower; }
	const float K = (bSlowed ? 0.12f : 1.f) * (1.f + GetSpeedBonus()) * (1.f - FMath::Clamp(GetArmourSlow(), 0.f, 0.9f)) * (1.f - GetSlowness())
		* (1.f - FMath::Clamp(ShieldSlow, 0.f, 0.9f)) * (bHeldOn ? 0.f : 1.f);
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
	// (a melee weapon: no bolt; a ranged one: a spell whose bolt is a mesh, the crossbow; magic has no bonus; level 5: a
	// dexterity ring adds to the ranged bonus, a monster's weakening takes off)
	const float Bonus = !W.bSpell ? Generator->MeleeBonus : W.BoltMesh ? Generator->RangedBonus + GetRingBonus(ERDRingKind::Dexterity) : 0.f;
	return W.Damage * (1.f + Bonus) * WeakMul();
}

bool URDCombatComponent::StartAttack()
{
	return StartAttackWith(WeaponIndex);
}

bool URDCombatComponent::StartAttackWith(int32 Index)
{
	const FRDWeaponDef* W = Generator && Generator->Weapons.IsValidIndex(Index) ? &Generator->Weapons[Index] : nullptr;
	USkeletalMeshComponent* M = Body();
	if (!W || !M || bDead || AttackTime >= 0.f || RollTime >= 0.f || W->Attacks.Num() == 0 || bInventoryOpen || bCraftOpen) return false;
	// (a spell that costs more mana than she has is not cast)
	if (W->ManaCost > 0.f && Mana < W->ManaCost)
	{
		const float Now = GetWorld()->GetTimeSeconds();
		if (Now - NoManaTime > 0.6f)
		{
			++CastsRefused;
			SetMessage(W->ManaCost > MaxMana ? FString::Printf(TEXT("%s takes %.0f mana: more than you have (%.0f)"), *W->Name.ToString(), W->ManaCost, MaxMana)
			                                 : FString::Printf(TEXT("Not enough mana for %s"), *W->Name.ToString()));
			Generator->PlaySoundAt(TEXT("Player.NoMana"), GetOwner()->GetActorLocation());
		}
		NoManaTime = Now;
		return false;
	}
	// (level 5: a spell with a cooldown waits for it)
	if (W->Cooldown > 0.f)
	{
		const float Left = GetCooldownLeft(Index);
		if (Left > 0.f)
		{
			const float Now = GetWorld()->GetTimeSeconds();
			if (Now - NoManaTime > 0.6f) { ++CooldownRefusals; SetMessage(FString::Printf(TEXT("%s is not ready:  %.0f s"), *W->Name.ToString(), FMath::CeilToFloat(Left))); }
			NoManaTime = Now;
			return false;
		}
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
		Generator->PlaySoundAt(FName(*FString::Printf(TEXT("Player.Charge.%s"), *WeaponSound(*W).ToString())), GetOwner()->GetActorLocation());
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
	if (W->Cooldown > 0.f) ReadyAt.Add(W->Name, GetWorld()->GetTimeSeconds() + W->Cooldown);
	VeilUntil = FMath::Min(VeilUntil, GetWorld()->GetTimeSeconds());      // (an attack ends her veil: they see her again)
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
		Generator->PlaySoundAt(FName(*FString::Printf(TEXT("Player.Hit.%s"), *WeaponSound(*W).ToString())), Mo->GetActorLocation());
		const float Dmg = GetDamageOf(AttackIndex);         // (with her melee bonus)
		const bool bKilled = Mo->ApplyDamage(Dmg, O);
		Generator->AddHitText(Mo->GetActorLocation() + FVector(0, 0, Mo->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()), Dmg, false);
		DamageDealt += Dmg; ++HitsLanded; bAny = true;
		if (bKilled) ++Kills;
	}
	if (bAny) { LastHitTime = GetWorld()->GetTimeSeconds(); WearOut(AttackIndex); }      // (a blow that landed wears the weapon)
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
	AActor* O = GetOwner();
	// (level 5: her spells take their part first: a sanctum takes it all, a veil lets it miss, a ward takes it, a mirror
	// turns it back, a rune takes a share)
	if (O && Now < SanctumUntil && FVector::Dist2D(O->GetActorLocation(), SanctumAt) <= SanctumRadius) { ++ZoneBlocks; return; }
	if (Now < VeilUntil && SpellR.FRand() < VeilEvade) { ++Evaded; return; }
	if (Now < WardUntil)
	{
		if (WardPool > 0.f)
		{
			const float T = FMath::Min(WardPool, Amount);
			WardPool -= T; Amount -= T; ++WardBlocks;
			if (WardPool <= 0.f) { WardUntil = Now; SetAura(ERDSpellKind::Ward, nullptr, false); }
			if (Amount <= 0.f) return;
		}
		else if (WardHits > 0)
		{
			++WardBlocks;
			if (--WardHits <= 0) { WardUntil = Now; SetAura(ERDSpellKind::Ward, nullptr, false); }
			return;
		}
	}
	if (Now < MirrorUntil && MirrorShare > 0.f)
		if (ARDMonster* Mo = Cast<ARDMonster>(From); Mo && !Mo->IsDead())
		{
			const float Back = Amount * MirrorShare;
			SpellHurt(Mo, Back, Mo->GetActorLocation() + FVector(0, 0, 40.f), true);
			Amount -= Back; ++Reflected;
			if (Amount <= 0.f) return;
		}
	if (O && Now < RuneUntil && FVector::Dist2D(O->GetActorLocation(), RuneAt) <= RuneRadius) { Amount *= 1.f - RuneShare; ++ZoneBlocks; }
	// (her armour takes its share off; Iron Skin adds to it)
	LastBlowBefore = Amount;
	Amount *= 1.f - FMath::Clamp(GetArmour() + GetSkinBonus(), 0.f, 0.95f);
	// (mistward: her shield takes its share of what is left, and wears by what it took)
	LastShieldTook = 0.f;
	if (IsShieldInHand())
	{
		const float Took = Amount * FMath::Clamp(GetShieldShare(), 0.f, 0.9f);
		Amount -= Took; LastShieldTook = Took;
		if (Took > 0.f) { ++ShieldBlocks; WearDownShield(Took); }
	}
	LastBlowTaken = Amount;
	WearDownArmour();             // (level 5: the blow reached her: her armour loses 1 of its durability)
	Health = FMath::Max(0.f, Health - Amount);
	// (level 5: a pact cheats death once)
	if (Health <= 0.f && Now < PactUntil) { Health = FMath::Max(1.f, MaxHealth * PactShare); PactUntil = Now; ++PactSaves; SetAura(ERDSpellKind::Pact, nullptr, false); SetMessage(TEXT("Your pact holds: you rise again")); }
	DamageTaken += Amount; ++HitsTaken; LastHurtTime = Now;
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
	if (Health <= 0.f) { Fall(); return; }
	// a flinch, unless she is in the middle of a swing or flinched a moment ago
	if (AI && W && W->GetHit && AttackTime < 0.f && Now > StaggerUntil)
	{
		AI->PlaySlotAnimationAsDynamicMontage(W->GetHit, RDCombatSlot, 0.08f, 0.2f, 1.4f, 1, -1.f, 0.f);
		StaggerUntil = Now + 1.2f;
	}
}

void URDCombatComponent::Fall()
{
	const float Now = GetWorld()->GetTimeSeconds();
	AActor* O = GetOwner();
	USkeletalMeshComponent* M = Body();
	UAnimInstance* AI = M ? M->GetAnimInstance() : nullptr;
	const FRDWeaponDef* W = Weapon();
	Health = 0.f;
	EndAttack(); EndRoll();
	// (mistward: everything she found drops where she falls; she comes back with what her hero started with)
	if (Generator && Generator->bDropOnDeath && O)
	{
		TArray<FName> Things; TArray<float> ThingWear;
		GatherDroppable(Things, ThingWear);
		if (Things.Num() > 0)
		{
			Generator->DropLoot(O->GetActorLocation(), Things, ThingWear);
			if (bInventoryOpen) SetInventoryOpen(false);
			if (bCraftOpen) SetCraftingOpen(false);
			// (her hero's own shield stays hers, as it was)
			const FName* OwnP = Generator->StartShield.Find(Generator->CurrentHero);
			const FName Own = OwnP && GetItemCount(*OwnP) > 0 ? *OwnP : NAME_None;
			const float OwnWear = Own.IsNone() ? 0.f : GetArmourWear(Own);
			const bool bOwnWorn = !Own.IsNone() && WornShield == Own;
			TakeOffArmour(); WornShield = NAME_None; bTorchHeld = false; TorchItem = NAME_None;
			WornRings.Reset(); Spares.Reset(); Carried.Reset(); CarriedOrder.Reset(); ArmourWear.Reset();
			if (!Own.IsNone()) { AddItem(Own, 1); ArmourWear.Add(Own, OwnWear); if (bOwnWorn) WornShield = Own; }
			UpdateMaxima();
			if (const FRDHeroDef* H = Generator->FindHero(Generator->CurrentHero)) Generator->Weapons = H->Weapons;
			// (her spells learned from tomes stay: they are in her head; the found weapons go)
			const int32 Keep = WeaponIndex;
			Wear.Reset(); NextOf.Reset(); PendingBreak.Reset(); Bolts.Reset();
			SyncWear();
			WeaponIndex = -1;
			SelectWeapon(Generator->Weapons.IsValidIndex(Keep) && !Generator->Weapons[Keep].bAlongside ? Keep : 0);
			UpdateLeftHand();
			SetMessage(FString::Printf(TEXT("Your things (%d) lie where you fell: go back for them (F)"), Things.Num()));
		}
	}
	bDead = true; ++Deaths; DeathTime = Now; bFallDone = false;
	if (ACharacter* C = Cast<ACharacter>(O)) C->GetCharacterMovement()->StopMovementImmediately();
	if (AI && W && W->Death)
		if (UAnimMontage* Mo = AI->PlaySlotAnimationAsDynamicMontage(W->Death, RDCombatSlot, 0.12f, 0.2f, 1.f, 1, -1.f, 0.f)) Mo->bEnableAutoBlendOut = false;      // (she stays down)
}

void URDCombatComponent::Revive(bool bToStart)
{
	AActor* O = GetOwner();
	// (level 5: what was on her is gone: her spells, poison, weakness, slowness, the areas she left, the channel)
	WardUntil = SkinUntil = VeilUntil = MirrorUntil = PactUntil = DispelUntil = RuneUntil = SanctumUntil = DrainUntil = -100.f;
	WardHits = 0; WardPool = 0.f; DrainTarget = nullptr;
	ClearAfflictions();
	for (FArea& Ar : Areas) if (UFXSystemComponent* F = Ar.Fx.Get()) F->Deactivate();
	Areas.Reset();
	for (const TPair<uint8, TWeakObjectPtr<UFXSystemComponent>>& Au : Auras) if (UFXSystemComponent* F = Au.Value.Get()) F->Deactivate();
	Auras.Reset();
	UpdateMaxima();
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
	// (weapons worn out last tick break now, the last in the list first: the indices before it stay as they are)
	if (PendingBreak.Num() > 0)
	{
		TArray<int32> Br = PendingBreak; PendingBreak.Reset();
		Br.Sort([](int32 A, int32 B) { return A > B; });
		for (const int32 I : Br) BreakWeapon(I);
	}
	const float Now = GetWorld()->GetTimeSeconds();
	TickSounds(Dt, Now);
	TickBolts(Dt);
	TickSpells(Dt, Now);
	if (bHeldOn && Now >= HeldUntil) { bHeldOn = false; UpdateWalkSpeed(); }       // (mistward: the snare lets go)
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
					if (PC->WasInputKeyJustPressed(EKeys::One) || (!Generator->bMapOpen && PC->WasInputKeyJustPressed(EKeys::Gamepad_DPad_Left))) SelectWeapon(0);
					if (PC->WasInputKeyJustPressed(EKeys::Two) || (!Generator->bMapOpen && PC->WasInputKeyJustPressed(EKeys::Gamepad_DPad_Up))) SelectWeapon(1);
					if (PC->WasInputKeyJustPressed(EKeys::Three) || (!Generator->bMapOpen && PC->WasInputKeyJustPressed(EKeys::Gamepad_DPad_Right))) SelectWeapon(2);
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
		if (!bHitDone && AttackTime >= AttackHit)
		{
			bHitDone = true;
			// (level 5: a spell of the table that does not fly does what its kind says)
			const FRDSpellDef* S = bSpell ? SpellOf(AttackIndex) : nullptr;
			if (S && S->Kind != ERDSpellKind::Bolt) ReleaseSpell(AttackIndex);
			else if (bSpell) LaunchBolt();
			else Strike();
		}
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
	// (a weapon made for her hero joins her weapons, each with its own durability; one not for her stays an item)
	const int32 Ix = Generator ? Generator->FindItem(Name) : -1;
	if (Ix >= 0 && Generator->Items[Ix].Kind == ERDItemKind::Weapon)
	{
		int32 Left = Count;
		while (Left > 0 && TakeWeapon(Name)) --Left;
		if (Left < Count) InventoryCursor = FMath::Clamp(InventoryCursor, 0, FMath::Max(0, GetInventoryLines().Num() - 1));
		Count = Left;
		if (Count <= 0) return;
	}
	// (level 5: a tome teaches its spell at once to a hero who learns its type; one she knows already is no use; one her
	// hero cannot learn is carried)
	if (Ix >= 0 && Generator->Items[Ix].Kind == ERDItemKind::Tome)
	{
		const FName Sp = Generator->Items[Ix].Spell;
		if (KnowsSpell(Sp)) { SetMessage(FString::Printf(TEXT("You know %s already"), *Sp.ToString())); return; }
		if (LearnSpell(Sp)) return;
	}
	// (mistward: armour (bArmourStacks) and shields are kept copy by copy, each with its own durability)
	const bool bStacks = Ix >= 0 && (Generator->Items[Ix].Kind == ERDItemKind::Shield || (Generator->bArmourStacks && Generator->Items[Ix].Kind == ERDItemKind::Armour));
	if (bStacks)
	{
		const float Full = Generator->Items[Ix].Durability;
		for (int32 K = 0; K < Count; ++K)
		{
			if (GetItemCount(Name) + K == 0) ArmourWear.Add(Name, Full);
			else Spares.FindOrAdd(Name).Add(Full);
		}
	}
	// (level 5: a set of armour is carried once, with its durability; one found again mends hers to full)
	else if (Ix >= 0 && Generator->Items[Ix].Kind == ERDItemKind::Armour)
	{
		const float Full = Generator->Items[Ix].Durability;
		if (GetItemCount(Name) > 0) { if (Full > 0.f) ArmourWear.Add(Name, Full); return; }
		ArmourWear.Add(Name, Full);
		Count = 1;
	}
	// (mistward: one teleport ring of a tier is enough)
	if (Ix >= 0 && Generator->Items[Ix].Kind == ERDItemKind::Teleport && GetItemCount(Name) > 0) return;
	int32& N = Carried.FindOrAdd(Name);
	if (N == 0) CarriedOrder.AddUnique(Name);
	N += Count;
}

void URDCombatComponent::ClearItems()
{
	TakeOffArmour();
	WornRings.Reset(); UpdateMaxima();
	ReadyAt.Reset(); SpellsLearned = WeaponsBrokenDown = 0;
	Carried.Reset(); CarriedOrder.Reset(); ArmourWear.Reset();
	Spares.Reset(); WornShield = NAME_None; bTorchHeld = false; TorchItem = NAME_None; ShieldBlocks = ShieldsBroken = GearBrokenDown = 0; HeldUntil = -100.f; bHeldOn = false;
	UpdateLeftHand();
	RepairWith = NAME_None; RepairCursor = 0;
	if (bCraftOpen) SetCraftingOpen(false);
	CraftCursor = 0;
	InventoryCursor = 0;
	ArmourWornOut = ItemsRepaired = ItemsCrafted = 0;
	UpdateWalkSpeed();
}

void URDCombatComponent::RemoveCarried(FName Name, int32 Count)
{
	int32* N = Carried.Find(Name);
	if (!N || Count <= 0) return;
	// (mistward: a spare copy goes first)
	for (int32 K = 0; K < Count; ++K) if (TArray<float>* Sp = Spares.Find(Name); Sp && Sp->Num() > 0) Sp->Pop();
	*N -= Count;
	if (*N <= 0)
	{
		Carried.Remove(Name); CarriedOrder.Remove(Name); ArmourWear.Remove(Name); Spares.Remove(Name);
		// (a ring she no longer has is not on her)
		for (auto It = WornRings.CreateIterator(); It; ++It) if (It->Value == Name) { It.RemoveCurrent(); UpdateMaxima(); break; }
		// (mistward: nor a set, a shield or a torch)
		if (WornArmour == Name) TakeOffArmour();
		if (WornShield == Name) { WornShield = NAME_None; UpdateLeftHand(); UpdateWalkSpeed(); }
		if (TorchItem == Name) { bTorchHeld = false; TorchItem = NAME_None; UpdateLeftHand(); }
	}
}

void URDCombatComponent::PlayUiSound(FName Key, FName Fallback)
{
	if (!Generator || !GetOwner()) return;
	Generator->PlaySoundAt(Generator->HasSound(Key) ? Key : Fallback, GetOwner()->GetActorLocation());
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
	if (It.Kind == ERDItemKind::Armour) return WearArmour(Name);          // (worn, not used up)
	// (mistward: a shield to her left hand, the torch lit or put out, a teleport ring used)
	if (It.Kind == ERDItemKind::Shield) return WearShield(Name);
	if (It.Kind == ERDItemKind::Torch) { TorchItem = Name; return HoldTorch(!bTorchHeld); }
	if (It.Kind == ERDItemKind::Teleport)
	{
		if (bInventoryOpen) SetInventoryOpen(false);
		if (!Generator->TeleportTo(1)) { SetMessage(TEXT("The ring is cold: the first tier's teleporter is gone")); return false; }
		return true;
	}
	if (It.Kind == ERDItemKind::Repair) return BeginRepair(Name);         // (then she chooses what it mends)
	if (It.Kind == ERDItemKind::Ring) return WearRing(Name);              // (level 5: worn, one of each kind)
	if (It.Kind == ERDItemKind::Tome)
	{
		if (KnowsSpell(It.Spell)) { SetMessage(FString::Printf(TEXT("You know %s already"), *It.Spell.ToString())); return false; }
		if (!LearnSpell(It.Spell)) return false;
		RemoveCarried(Name, 1);
		return true;
	}
	if (It.Kind == ERDItemKind::Component)
	{
		SetMessage(FString::Printf(TEXT("The %s is a crafting material: an anvil makes repair items from it (F at an anvil)"), *Lb));
		return false;
	}
	if (It.Kind == ERDItemKind::Weapon)
	{
		// (one she carries is not made for her hero: had it been, it would be among her weapons)
		SetMessage(FString::Printf(TEXT("The %s cannot wield the %s"), *Generator->PlayerTitle.ToLower(), *Lb));
		return false;
	}
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
		for (int32 I = 0; I < Generator->Weapons.Num(); ++I)
		{
			// (a found weapon: what is left of its durability, and its full durability)
			const FRDWeaponDef& W = Generator->Weapons[I];
			Out.Add(W.Durability > 0.f ? FString::Printf(TEXT("weapon|%s|%.0f|%.0f"), *W.Name.ToString(), GetWeaponWear(I), W.Durability) : FString::Printf(TEXT("weapon|%s"), *W.Name.ToString()));
		}
	auto KindOf = [this](FName N) { const int32 Ix = Generator ? Generator->FindItem(N) : -1; return Ix >= 0 ? Generator->Items[Ix].Kind : ERDItemKind::Healing; };
	auto Usable = [](ERDItemKind K) { return K == ERDItemKind::Healing || K == ERDItemKind::Mana || K == ERDItemKind::Speed || K == ERDItemKind::Food; };
	for (const FName& N : CarriedOrder) if (Usable(KindOf(N))) Out.Add(FString::Printf(TEXT("item|%s|%d"), *N.ToString(), GetItemCount(N)));
	for (const FName& N : CarriedOrder) if (KindOf(N) == ERDItemKind::Repair) Out.Add(FString::Printf(TEXT("repair|%s|%d"), *N.ToString(), GetItemCount(N)));
	for (const FName& N : CarriedOrder)
		if (KindOf(N) == ERDItemKind::Armour)
		{
			// (mistward: how many copies she carries, when more than one)
			const int32 Cnt = GetItemCount(N);
			Out.Add(Cnt > 1 ? FString::Printf(TEXT("armour|%s|%d|%.0f|%.0f|%d"), *N.ToString(), N == WornArmour ? 1 : 0, GetArmourWear(N), GetArmourDurability(N), Cnt)
			                : FString::Printf(TEXT("armour|%s|%d|%.0f|%.0f"), *N.ToString(), N == WornArmour ? 1 : 0, GetArmourWear(N), GetArmourDurability(N)));
		}
	// (mistward: shields "shield|<name>|<1 in her hand>|<left>|<full>|<count>", the torch "torch|<name>|<1 lit>|<count>",
	// teleport rings "teleport|<name>|<tier>")
	for (const FName& N : CarriedOrder)
		if (KindOf(N) == ERDItemKind::Shield)
		{
			const int32 Ix = Generator->FindItem(N);
			Out.Add(FString::Printf(TEXT("shield|%s|%d|%.0f|%.0f|%d"), *N.ToString(), N == WornShield ? 1 : 0, GetShieldWear(N), Ix >= 0 ? Generator->Items[Ix].Durability : 0.f, GetItemCount(N)));
		}
	for (const FName& N : CarriedOrder) if (KindOf(N) == ERDItemKind::Torch) Out.Add(FString::Printf(TEXT("torch|%s|%d|%d"), *N.ToString(), bTorchHeld && TorchItem == N ? 1 : 0, GetItemCount(N)));
	for (const FName& N : CarriedOrder)
		if (KindOf(N) == ERDItemKind::Teleport) { const int32 Ix = Generator->FindItem(N); Out.Add(FString::Printf(TEXT("teleport|%s|%d"), *N.ToString(), Ix >= 0 ? Generator->Items[Ix].TeleportTier : 0)); }
	// (level 5: her rings, worn or not; tomes her hero cannot learn)
	for (const FName& N : CarriedOrder)
		if (KindOf(N) == ERDItemKind::Ring)
		{
			bool bOn = false;
			for (const TPair<uint8, FName>& R : WornRings) bOn |= R.Value == N;
			Out.Add(FString::Printf(TEXT("ring|%s|%d|%d"), *N.ToString(), bOn ? 1 : 0, GetItemCount(N)));
		}
	for (const FName& N : CarriedOrder) if (KindOf(N) == ERDItemKind::Tome) Out.Add(FString::Printf(TEXT("tome|%s|%d"), *N.ToString(), GetItemCount(N)));
	for (const FName& N : CarriedOrder) if (KindOf(N) == ERDItemKind::Component) Out.Add(FString::Printf(TEXT("component|%s|%d"), *N.ToString(), GetItemCount(N)));
	// (level 5: weapons she found that her hero cannot wield)
	for (const FName& N : CarriedOrder) if (KindOf(N) == ERDItemKind::Weapon) Out.Add(FString::Printf(TEXT("carried|%s|%d"), *N.ToString(), GetItemCount(N)));
	return Out;
}

// ------------------------------------------------------------------------------------------------ armour (level 5)
float URDCombatComponent::GetArmour() const
{
	if (WornArmour.IsNone() || !Generator) return 0.f;
	const int32 Ix = Generator->FindItem(WornArmour);
	if (Ix < 0) return 0.f;
	// (worn out, its durability at 0: half its share)
	const FRDItemDef& It = Generator->Items[Ix];
	return It.Amount * (It.Durability > 0.f && GetArmourWear(WornArmour) <= 0.f ? 0.5f : 1.f);
}

float URDCombatComponent::GetArmourSlow() const
{
	if (WornArmour.IsNone() || !Generator) return 0.f;
	const int32 Ix = Generator->FindItem(WornArmour);
	return Ix >= 0 ? Generator->Items[Ix].Slower : 0.f;
}

float URDCombatComponent::GetArmourDurability(FName Item) const
{
	const int32 Ix = Generator ? Generator->FindItem(Item) : -1;
	return Ix >= 0 && Generator->Items[Ix].Kind == ERDItemKind::Armour ? Generator->Items[Ix].Durability : 0.f;
}

void URDCombatComponent::SetArmourWear(FName Item, float Value)
{
	if (GetItemCount(Item) <= 0 || GetArmourDurability(Item) <= 0.f) return;
	ArmourWear.Add(Item, FMath::Clamp(Value, 0.f, GetArmourDurability(Item)));
}

void URDCombatComponent::WearDownArmour()
{
	if (WornArmour.IsNone() || GetArmourDurability(WornArmour) <= 0.f) return;
	float& W = ArmourWear.FindOrAdd(WornArmour);
	if (W <= 0.f) return;
	W = FMath::Max(0.f, W - 1.f);
	if (W > 0.f) return;
	++ArmourWornOut;
	SetMessage(FString::Printf(TEXT("Your %s is worn out: blows take only %.0f%% less until it is mended"), *WornArmour.ToString().ToLower(), GetArmour() * 100.f));
	if (Generator && GetOwner()) Generator->PlaySoundAt(TEXT("Player.Break"), GetOwner()->GetActorLocation());
	UE_LOG(LogTemp, Log, TEXT("RDARMOUR %s worn out"), *WornArmour.ToString());
}

// ------------------------------------------------------------------------------------------------ repairs (level 5)
bool URDCombatComponent::BeginRepair(FName Item)
{
	const int32 Ix = Generator ? Generator->FindItem(Item) : -1;
	if (Ix < 0 || Generator->Items[Ix].Kind != ERDItemKind::Repair || GetItemCount(Item) <= 0 || bDead) return false;
	RepairWith = Item;
	if (GetRepairLines().Num() == 0)
	{
		RepairWith = NAME_None;
		SetMessage(FString::Printf(TEXT("Nothing to mend: the %s mends armour and the weapons you found"), *Item.ToString().ToLower()));
		return false;
	}
	RepairCursor = 0;
	SetMessage(FString::Printf(TEXT("Choose what to mend with the %s"), *Item.ToString().ToLower()));
	PlayUiSound(TEXT("Player.Inventory"), TEXT("Player.Inventory"));
	return true;
}

void URDCombatComponent::CancelRepair()
{
	RepairWith = NAME_None; RepairCursor = 0;
}

TArray<FString> URDCombatComponent::GetRepairLines() const
{
	TArray<FString> Out;
	const int32 Ix = Generator && !RepairWith.IsNone() ? Generator->FindItem(RepairWith) : -1;
	if (Ix < 0) return Out;
	const float Share = Generator->Items[Ix].Amount;
	for (const FName& N : CarriedOrder)
	{
		const float Full = GetArmourDurability(N);
		if (Full <= 0.f) continue;
		const float Left = GetArmourWear(N);
		Out.Add(FString::Printf(TEXT("armour|%s|%.0f|%.0f|%.0f"), *N.ToString(), Left, Full, FMath::Min(Full, Left + Full * Share)));
	}
	for (int32 I = 0; I < Generator->Weapons.Num(); ++I)
	{
		const FRDWeaponDef& W = Generator->Weapons[I];
		if (W.Durability <= 0.f) continue;
		const float Left = GetWeaponWear(I);
		Out.Add(FString::Printf(TEXT("weapon|%d|%s|%.0f|%.0f|%.0f"), I, *W.Name.ToString(), Left, W.Durability, FMath::Min(W.Durability, Left + W.Durability * Share)));
	}
	return Out;
}

void URDCombatComponent::MoveRepairCursor(int32 Step)
{
	const int32 N = GetRepairLines().Num();
	if (N > 0) RepairCursor = ((RepairCursor + Step) % N + N) % N;
}

bool URDCombatComponent::RepairEntry(int32 Line)
{
	const TArray<FString> L = GetRepairLines();
	const int32 I = Line >= 0 ? Line : RepairCursor;
	if (!L.IsValidIndex(I) || !Generator) return false;
	TArray<FString> P; L[I].ParseIntoArray(P, TEXT("|"));
	const bool bArmour = P[0] == TEXT("armour");
	if (P.Num() < (bArmour ? 5 : 6)) return false;
	// (the line names what is mended; its numbers are the real wear, not the line's rounded text)
	const FString Name = bArmour ? P[1] : P[2];
	const int32 Ri = Generator->FindItem(RepairWith);
	const float Share = Ri >= 0 ? Generator->Items[Ri].Amount : 0.f;
	const int32 Wi = bArmour ? -1 : FCString::Atoi(*P[1]);
	if (!bArmour) { SyncWear(); if (!Wear.IsValidIndex(Wi) || !Generator->Weapons.IsValidIndex(Wi)) return false; }
	const float Left = bArmour ? GetArmourWear(FName(*Name)) : Wear[Wi];
	const float Full = bArmour ? GetArmourDurability(FName(*Name)) : Generator->Weapons[Wi].Durability;
	const float After = FMath::Min(Full, Left + Full * Share);
	const FString Kit = RepairWith.ToString().ToLower();
	if (Left >= Full) { SetMessage(FString::Printf(TEXT("Your %s is whole already"), *Name.ToLower())); return false; }
	if (bArmour) ArmourWear.Add(FName(*Name), After);
	else { Wear[Wi] = After; PendingBreak.Remove(Wi); }
	const FName Used = RepairWith;
	RemoveCarried(Used, 1);
	++ItemsRepaired;
	SetMessage(FString::Printf(TEXT("Mended with the %s: your %s,  %.0f to %.0f of %.0f"), *Kit, *Name.ToLower(), Left, After, Full));
	PlayUiSound(TEXT("Player.Repair"), TEXT("Player.Inventory"));
	UE_LOG(LogTemp, Log, TEXT("RDREPAIR %s mended %s %.0f -> %.0f / %.0f"), *Used.ToString(), *Name, Left, After, Full);
	if (GetItemCount(Used) <= 0) CancelRepair();
	if (bArmour && FName(*Name) == WornArmour) UpdateWalkSpeed();
	InventoryCursor = FMath::Clamp(InventoryCursor, 0, FMath::Max(0, GetInventoryLines().Num() - 1));
	return true;
}

// ------------------------------------------------------------------------------------------------ crafting (level 5)
void URDCombatComponent::SetCraftingOpen(bool bOpen)
{
	if (bOpen == bCraftOpen || (bOpen && (bDead || !Generator || Generator->Recipes.Num() == 0))) return;
	if (bOpen && bInventoryOpen) SetInventoryOpen(false);
	KeyRepeatDir = 0;
	bCraftOpen = bOpen;
	if (bOpen) { if (AttackTime >= 0.f) EndAttack(); CraftCursor = FMath::Clamp(CraftCursor, 0, FMath::Max(0, GetCraftLines().Num() - 1)); }
	else CraftClosedFrame = GFrameCounter;
	if (bInventoryPausesGame || !bOpen) UGameplayStatics::SetGamePaused(this, bOpen);
	PlayUiSound(bOpen ? FName(TEXT("Player.Anvil")) : FName(TEXT("Player.Inventory")), TEXT("Player.Inventory"));
}

void URDCombatComponent::MoveCraftCursor(int32 Step)
{
	const int32 N = GetCraftLines().Num();
	if (N > 0) CraftCursor = ((CraftCursor + Step) % N + N) % N;
}

int32 URDCombatComponent::PartHave(const FRDRecipePart& Part) const
{
	int32 N = 0;
	for (const FName& K : Part.AnyOf) N += GetItemCount(K);
	return N;
}

TArray<FString> URDCombatComponent::GetCraftLines() const
{
	TArray<FString> Out;
	if (!Generator) return Out;
	// (mistward: in alphabetical order, the recipes first, then what she can break down)
	auto ByName = [](const FString& A, const FString& B)
	{
		TArray<FString> Pa, Pb; A.ParseIntoArray(Pa, TEXT("|")); B.ParseIntoArray(Pb, TEXT("|"));
		return (Pa.Num() > 1 ? Pa[1] : A) < (Pb.Num() > 1 ? Pb[1] : B);
	};
	for (const FRDRecipe& Rc : Generator->Recipes)
	{
		TArray<FString> Ps;
		for (const FRDRecipePart& Pt : Rc.Parts) Ps.Add(FString::Printf(TEXT("%s:%d:%d"), *Pt.Label, PartHave(Pt), Pt.Count));
		Out.Add(FString::Printf(TEXT("recipe|%s|%d|%s"), *Rc.Item.ToString(), CanCraft(Rc.Item) ? 1 : 0, *FString::Join(Ps, TEXT(";"))));
	}
	if (Generator->bAlphabeticalCrafting) Out.Sort(ByName);
	const int32 NumRecipes = Out.Num();
	// (mistward: armour (bArmourStacks) and shields she carries break down too: "breakdown|<name>|g<name>|<1 worn>|...")
	for (const FName& N : CarriedOrder)
	{
		const int32 Ix = Generator->FindItem(N);
		if (Ix < 0) continue;
		const ERDItemKind K = Generator->Items[Ix].Kind;
		if (!(K == ERDItemKind::Shield || (K == ERDItemKind::Armour && Generator->bArmourStacks))) continue;
		const FString Gives = BreakdownText(N, Generator->Items[Ix].WeaponType);
		if (!Gives.IsEmpty()) Out.Add(FString::Printf(TEXT("breakdown|%s|g%s|%d|%s"), *N.ToString(), *N.ToString(), (N == WornArmour || N == WornShield) ? 1 : 0, *Gives));
	}
	// (level 5: the weapons she found, to break down: "breakdown|<name>|w<weapon index> or i<item>|<1 drawn>|<item>:<count>;...")
	if (Generator->Breakdowns.Num() > 0)
	{
		for (int32 I = 0; I < Generator->Weapons.Num(); ++I)
		{
			const FRDWeaponDef& W = Generator->Weapons[I];
			if (W.Item.IsNone()) continue;
			const FString Gives = BreakdownText(W.Item, W.WeaponType);
			if (!Gives.IsEmpty()) Out.Add(FString::Printf(TEXT("breakdown|%s|w%d|%d|%s"), *W.Name.ToString(), I, I == WeaponIndex ? 1 : 0, *Gives));
		}
		for (const FName& N : CarriedOrder)
		{
			const int32 Ix = Generator->FindItem(N);
			if (Ix < 0 || Generator->Items[Ix].Kind != ERDItemKind::Weapon) continue;
			const FString Gives = BreakdownText(N, Generator->Items[Ix].WeaponType);
			if (!Gives.IsEmpty()) Out.Add(FString::Printf(TEXT("breakdown|%s|i%s|0|%s"), *N.ToString(), *N.ToString(), *Gives));
		}
	}
	if (Generator->bAlphabeticalCrafting && Out.Num() > NumRecipes)
	{
		TArray<FString> Tail(Out.GetData() + NumRecipes, Out.Num() - NumRecipes);
		Tail.Sort(ByName);
		for (int32 I = 0; I < Tail.Num(); ++I) Out[NumRecipes + I] = Tail[I];
	}
	return Out;
}

FString URDCombatComponent::BreakdownText(FName Item, const FString& Type) const
{
	const int32 Ix = Generator ? Generator->FindItem(Item) : -1;
	// (the item's own type first: the table's "ranged" is a bow or a crossbow there)
	const FString T = Ix >= 0 && !Generator->Items[Ix].WeaponType.IsEmpty() ? Generator->Items[Ix].WeaponType : Type;
	int32 Tier = 1;
	if (Ix >= 0 && Generator->Items[Ix].Tiers.Num() > 0) { Tier = Generator->Items[Ix].Tiers[0]; for (const int32 Ti : Generator->Items[Ix].Tiers) Tier = FMath::Min(Tier, Ti); }
	TArray<FName> Gives; TArray<int32> Counts;
	if (T.IsEmpty() || !Generator->BreakdownOf(T, Tier, Gives, Counts)) return FString();
	TArray<FString> Ps;
	for (int32 K = 0; K < Gives.Num(); ++K) Ps.Add(FString::Printf(TEXT("%s:%d"), *Gives[K].ToString(), Counts[K]));
	return FString::Join(Ps, TEXT(";"));
}

bool URDCombatComponent::BreakDownWeapon(int32 Index)
{
	if (!Generator || bDead || !Generator->Weapons.IsValidIndex(Index)) return false;
	const FRDWeaponDef W = Generator->Weapons[Index];
	if (W.Item.IsNone()) { SetMessage(FString::Printf(TEXT("Your own %s is not to be broken"), *W.Name.ToString().ToLower())); return false; }
	if (Index == WeaponIndex) { SetMessage(FString::Printf(TEXT("The %s is in your hands: draw another first"), *W.Name.ToString().ToLower())); return false; }
	const FString Gives = BreakdownText(W.Item, W.WeaponType);
	if (Gives.IsEmpty()) return false;
	// (it is gone from her weapons as a broken one would be, without the breaking's message)
	if (AttackTime >= 0.f && AttackIndex == Index) EndAttack();
	Generator->Weapons.RemoveAt(Index);
	if (Wear.IsValidIndex(Index)) Wear.RemoveAt(Index);
	if (NextOf.IsValidIndex(Index)) NextOf.RemoveAt(Index);
	Bolts.RemoveAll([Index](const FBolt& B) { return B.Weapon == Index; });
	for (FBolt& B : Bolts) if (B.Weapon > Index) --B.Weapon;
	for (int32& P : PendingBreak) if (P > Index) --P;
	PendingBreak.Remove(Index);
	if (WeaponIndex > Index) --WeaponIndex;
	TArray<FString> Ps; Gives.ParseIntoArray(Ps, TEXT(";"));
	TArray<FString> Got;
	for (const FString& P : Ps) { FString N, C; if (P.Split(TEXT(":"), &N, &C)) { AddItem(FName(*N), FCString::Atoi(*C)); Got.Add(FString::Printf(TEXT("%s %s"), *C, *N.ToLower())); } }
	++WeaponsBrokenDown;
	SetMessage(FString::Printf(TEXT("You break down the %s:  %s"), *W.Name.ToString().ToLower(), *FString::Join(Got, TEXT(", "))));
	PlayUiSound(TEXT("Player.Craft"), TEXT("Player.Loot"));
	UE_LOG(LogTemp, Log, TEXT("RDBREAKDOWN %s -> %s"), *W.Name.ToString(), *Gives);
	return true;
}

bool URDCombatComponent::BreakDownItem(FName Item)
{
	const int32 Ix = Generator && !bDead ? Generator->FindItem(Item) : -1;
	if (Ix < 0 || Generator->Items[Ix].Kind != ERDItemKind::Weapon || GetItemCount(Item) <= 0) return false;
	const FString Gives = BreakdownText(Item, Generator->Items[Ix].WeaponType);
	if (Gives.IsEmpty()) return false;
	RemoveCarried(Item, 1);
	TArray<FString> Ps; Gives.ParseIntoArray(Ps, TEXT(";"));
	TArray<FString> Got;
	for (const FString& P : Ps) { FString N, C; if (P.Split(TEXT(":"), &N, &C)) { AddItem(FName(*N), FCString::Atoi(*C)); Got.Add(FString::Printf(TEXT("%s %s"), *C, *N.ToLower())); } }
	++WeaponsBrokenDown;
	SetMessage(FString::Printf(TEXT("You break down the %s:  %s"), *Item.ToString().ToLower(), *FString::Join(Got, TEXT(", "))));
	PlayUiSound(TEXT("Player.Craft"), TEXT("Player.Loot"));
	UE_LOG(LogTemp, Log, TEXT("RDBREAKDOWN %s -> %s"), *Item.ToString(), *Gives);
	return true;
}

bool URDCombatComponent::CanCraft(FName Item) const
{
	const int32 R = Generator ? Generator->FindRecipe(Item) : -1;
	if (R < 0) return false;
	TMap<FName, int32> Take;
	return PlanCraft(Generator->Recipes[R], Take);
}

bool URDCombatComponent::PlanCraft(const FRDRecipe& Rc, TMap<FName, int32>& Take) const
{
	// what making it takes of each kind, the parts drawn from one running count (for each part the kinds she has most of
	// left go first); false when a part cannot be met
	Take.Reset();
	auto Left = [&](const FName& K) { const int32* T = Take.Find(K); return GetItemCount(K) - (T ? *T : 0); };
	for (const FRDRecipePart& Pt : Rc.Parts)
	{
		TArray<FName> Kinds = Pt.AnyOf;
		Kinds.Sort([&](const FName& A, const FName& B) { return Left(A) > Left(B); });
		int32 Need = Pt.Count;
		for (const FName& K : Kinds)
		{
			const int32 N = FMath::Min(Need, Left(K));
			if (N > 0) { Take.FindOrAdd(K) += N; Need -= N; }
			if (Need <= 0) break;
		}
		if (Need > 0) return false;
	}
	return true;
}

bool URDCombatComponent::Craft(FName Item)
{
	const int32 R = Generator && !bDead ? Generator->FindRecipe(Item) : -1;
	if (R < 0) return false;
	const FRDRecipe Rc = Generator->Recipes[R];
	TArray<FString> Missing;
	for (const FRDRecipePart& Pt : Rc.Parts)
		if (PartHave(Pt) < Pt.Count) Missing.Add(FString::Printf(TEXT("%d %s"), Pt.Count - PartHave(Pt), *Pt.Label));
	// ("a whetstone", "an ...", "leather strips")
	const FString Lb = Item.ToString().ToLower();
	const FString One = Lb.EndsWith(TEXT("s")) ? Lb : FString::Printf(TEXT("%s %s"), FCString::Strchr(TEXT("aeiou"), Lb.Len() ? Lb[0] : 'x') ? TEXT("an") : TEXT("a"), *Lb);
	TMap<FName, int32> Take;
	if (Missing.Num() > 0 || !PlanCraft(Rc, Take))
	{
		// (parts whose kinds overlap can each be there on their own and not all together)
		SetMessage(Missing.Num() > 0 ? FString::Printf(TEXT("For %s you need %s more"), *One, *FString::Join(Missing, TEXT(", ")))
		                             : FString::Printf(TEXT("For %s you need more materials"), *One));
		return false;
	}
	for (const TPair<FName, int32>& T : Take) RemoveCarried(T.Key, T.Value);
	AddItem(Item, 1);
	++ItemsCrafted;
	SetMessage(FString::Printf(TEXT("You make %s at the anvil"), *One));
	PlayUiSound(TEXT("Player.Craft"), TEXT("Player.Loot"));
	UE_LOG(LogTemp, Log, TEXT("RDCRAFT %s made (%d crafted)"), *Item.ToString(), ItemsCrafted);
	return true;
}

bool URDCombatComponent::CraftEntry()
{
	if (!Generator) return false;
	// (the line under the cursor says what it is: a recipe, or a weapon, set of armour or shield to break down)
	const TArray<FString> L = GetCraftLines();
	if (!L.IsValidIndex(CraftCursor)) return false;
	TArray<FString> P; L[CraftCursor].ParseIntoArray(P, TEXT("|"));
	if (P.Num() >= 2 && P[0] == TEXT("recipe")) return Craft(FName(*P[1]));
	if (P.Num() < 3 || P[0] != TEXT("breakdown")) return false;
	const bool bOk = P[2].StartsWith(TEXT("w")) ? BreakDownWeapon(FCString::Atoi(*P[2].Mid(1)))
	               : P[2].StartsWith(TEXT("g")) ? BreakDownGear(FName(*P[2].Mid(1))) : BreakDownItem(FName(*P[2].Mid(1)));
	CraftCursor = FMath::Clamp(CraftCursor, 0, FMath::Max(0, GetCraftLines().Num() - 1));
	return bOk;
}

TArray<USkeletalMeshComponent*> URDCombatComponent::GetArmourMeshes() const
{
	TArray<USkeletalMeshComponent*> Out;
	for (USkeletalMeshComponent* C : ArmourComps) if (C) Out.Add(C);
	return Out;
}

namespace
{
	struct FRDCSkin { TArray<FVector> Posed; TArray<FVector> Rest; TArray<int32> Bone; TArray<float> BoneWeight; };
	// a spread of a skinned mesh's vertices (every one with Want 0): where it draws them now (world) and in its reference pose
	bool RDCSkinSample(USkinnedMeshComponent* M, int32 Want, FRDCSkin& Out)
	{
		if (!M) return false;
		const FSkeletalMeshRenderData* RD = M->GetSkeletalMeshRenderData();
		if (!RD || RD->LODRenderData.Num() == 0) return false;
		const int32 LODIdx = FMath::Clamp(RD->GetPendingFirstLODIdx(0), 0, RD->LODRenderData.Num() - 1);
		const FSkeletalMeshLODRenderData& LOD = RD->LODRenderData[LODIdx];
		const FPositionVertexBuffer& PB = LOD.StaticVertexBuffers.PositionVertexBuffer;
		FSkinWeightVertexBuffer* SW = M->GetSkinWeightBuffer(LODIdx);
		const int32 Num = PB.GetNumVertices();
		if (Num <= 0 || !PB.GetVertexData() || !SW || !SW->GetNeedsCPUAccess() || (int32)SW->GetNumVertices() != Num) return false;
		TArray<FMatrix44f> RefToLocals;
		M->CacheRefToLocalMatrices(RefToLocals);             // (a follower's come from its leader's bones)
		const FTransform Xf = M->GetComponentTransform();
		const int32 Step = Want > 0 ? FMath::Max(1, Num / Want) : 1;
		for (int32 V = 0; V < Num; V += Step)
		{
			Out.Posed.Add(Xf.TransformPosition(FVector(USkinnedMeshComponent::GetSkinnedVertexPosition(M, V, LOD, *SW, RefToLocals))));
			Out.Rest.Add(FVector(PB.VertexPosition(V)));
			// (the bone that moves it most, as a bone of the mesh's skeleton, and its share)
			int32 Sec = 0, SecV = 0;
			LOD.GetSectionFromVertexIndex(V, Sec, SecV);
			const FSkinWeightInfo Wi = SW->GetVertexSkinWeights(V);
			int32 BestB = INDEX_NONE; float BestW = 0.f, Tot = 0.f;
			for (int32 K = 0; K < MAX_TOTAL_INFLUENCES; ++K)
			{
				const float Wk = (float)Wi.InfluenceWeights[K];
				Tot += Wk;
				if (Wk > BestW && LOD.RenderSections.IsValidIndex(Sec) && LOD.RenderSections[Sec].BoneMap.IsValidIndex(Wi.InfluenceBones[K]))
				{ BestW = Wk; BestB = LOD.RenderSections[Sec].BoneMap[Wi.InfluenceBones[K]]; }
			}
			Out.Bone.Add(BestB); Out.BoneWeight.Add(Tot > 0.f ? BestW / Tot : 0.f);
		}
		return true;
	}
}

TArray<float> URDCombatComponent::MeasureArmourFollow(int32 Samples)
{
	TArray<float> Out;
	USkeletalMeshComponent* M = Body();
	FRDCSkin B;
	if (!M || ArmourComps.Num() == 0 || !RDCSkinSample(M, 0, B)) return Out;
	TArray<float> Change, Rigid, RigidStill;
	for (USkeletalMeshComponent* C : ArmourComps)
	{
		FRDCSkin A;
		USkeletalMesh* AM = C ? C->GetSkeletalMeshAsset() : nullptr;
		if (!AM || !RDCSkinSample(C, FMath::Max(1, Samples / ArmourComps.Num()), A)) return TArray<float>();
		const TArray<FMatrix44f>& Inv = AM->GetRefBasesInvMatrix();
		const FReferenceSkeleton& RS = AM->GetRefSkeleton();
		const FTransform CX = C->GetComponentTransform();
		for (int32 i = 0; i < A.Rest.Num(); ++i)
		{
			// her skin: the nearest vertex of her body in the reference pose, and how their distance changed
			int32 Best = 0; double BD = MAX_dbl;
			for (int32 j = 0; j < B.Rest.Num(); ++j) { const double D = FVector::DistSquared(A.Rest[i], B.Rest[j]); if (D < BD) { BD = D; Best = j; } }
			Change.Add((float)FMath::Abs(FVector::Dist(A.Posed[i], B.Posed[Best]) - FMath::Sqrt(BD)));
			// her bones: a vertex moved by one bone alone is where her bone of that name puts it (its place on the bone in
			// the reference pose, carried by her bone as it is now); left in its reference pose it would not be
			const int32 Bn = A.Bone[i];
			if (A.BoneWeight[i] < 0.98f || !Inv.IsValidIndex(Bn) || !RS.IsValidIndex(Bn)) continue;
			const int32 HerB = M->GetBoneIndex(RS.GetBoneName(Bn));
			if (HerB == INDEX_NONE) continue;
			const FVector OnBone = FVector(Inv[Bn].TransformPosition(FVector3f(A.Rest[i])));
			const FVector Want = M->GetBoneTransform(HerB).TransformPosition(OnBone);
			Rigid.Add((float)FVector::Dist(Want, A.Posed[i]));
			RigidStill.Add((float)FVector::Dist(Want, CX.TransformPosition(A.Rest[i])));
		}
	}
	if (Change.Num() == 0 || Rigid.Num() == 0) return Out;
	Change.Sort(); Rigid.Sort(); RigidStill.Sort();
	auto Q = [](const TArray<float>& S, float F) { return S[FMath::Clamp(FMath::FloorToInt32(F * (S.Num() - 1)), 0, S.Num() - 1)]; };
	Out = { (float)Change.Num(), Q(Change, 0.5f), Q(Change, 0.95f), (float)Rigid.Num(), Q(Rigid, 0.95f), Rigid.Last(), Q(RigidStill, 0.95f) };
	return Out;
}

void URDCombatComponent::TakeOffArmour()
{
	for (USkeletalMeshComponent* C : ArmourComps) if (C) C->DestroyComponent();
	ArmourComps.Reset();
	WornArmour = NAME_None;
	UpdateWalkSpeed();           // (her armour's weight is off her)
}

bool URDCombatComponent::WearArmour(FName Item)
{
	if (!Generator || bDead || GetItemCount(Item) <= 0) return false;
	const int32 Ix = Generator->FindItem(Item);
	if (Ix < 0 || Generator->Items[Ix].Kind != ERDItemKind::Armour) return false;
	const FRDItemDef& It = Generator->Items[Ix];
	const FString Lb = RDItemLabel(Item);
	if (WornArmour == Item)
	{
		TakeOffArmour(); ++ArmourChanges;
		SetMessage(FString::Printf(TEXT("You take off the %s"), *Lb));
		if (AActor* O = GetOwner()) Generator->PlaySoundAt(TEXT("Player.Inventory"), O->GetActorLocation());
		return true;
	}
	// (her hero must wear armour of its weight, and a fit must have been made for her)
	const FString No = Generator->ArmourRefusal(It, Lb);
	const FRDArmourFit* Fit = It.Fits.FindByPredicate([this](const FRDArmourFit& F) { return F.Hero == Generator->CurrentHero; });
	USkeletalMeshComponent* M = Body();
	if (!No.IsEmpty() || !Fit || Fit->Meshes.Num() == 0 || !M)
	{
		SetMessage(No.IsEmpty() ? FString::Printf(TEXT("The %s was not made for the %s"), *Lb, *Generator->PlayerTitle.ToLower()) : No);
		return false;
	}
	TakeOffArmour();
	AActor* O = GetOwner();
	for (USkeletalMesh* Mesh : Fit->Meshes)
	{
		if (!Mesh) continue;
		USkeletalMeshComponent* C = NewObject<USkeletalMeshComponent>(O, NAME_None, RF_Transient);
		C->SetSkeletalMeshAsset(Mesh);
		C->SetupAttachment(M);
		C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		C->SetCastShadow(true);
		C->RegisterComponent();
		C->SetLeaderPoseComponent(M);              // (her bones move it: it was made on her skeleton, in her rest pose)
		ArmourComps.Add(C);
	}
	WornArmour = Item; ++ArmourChanges;
	UpdateWalkSpeed();
	SetMessage(It.Slower > 0.f ? FString::Printf(TEXT("You put on the %s:  blows take %.0f%% less,  you move %.0f%% slower"), *Lb, GetArmour() * 100.f, It.Slower * 100.f)
	                           : FString::Printf(TEXT("You put on the %s:  blows take %.0f%% less"), *Lb, GetArmour() * 100.f));
	if (O) Generator->PlaySoundAt(TEXT("Player.Inventory"), O->GetActorLocation());
	return true;
}

void URDCombatComponent::SetInventoryOpen(bool bOpen)
{
	if (bOpen == bInventoryOpen || (bOpen && bDead)) return;
	if (bOpen && bCraftOpen) SetCraftingOpen(false);
	KeyRepeatDir = 0;
	if (!bOpen) CancelRepair();
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
	if (P.Num() >= 2 && (P[0] == TEXT("item") || P[0] == TEXT("armour") || P[0] == TEXT("carried") || P[0] == TEXT("repair") || P[0] == TEXT("component")
		|| P[0] == TEXT("ring") || P[0] == TEXT("tome") || P[0] == TEXT("shield") || P[0] == TEXT("torch") || P[0] == TEXT("teleport")))
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
	// a list's cursor: the keys and the wheel step it; the left stick a step when it is pushed, then one every 0.22 s held
	auto Steer = [&](TFunctionRef<void(int32)> Move)
	{
		if (Pressed({ EKeys::W, EKeys::Up, EKeys::MouseScrollUp, EKeys::Gamepad_DPad_Up })) Move(-1);
		if (Pressed({ EKeys::S, EKeys::Down, EKeys::MouseScrollDown, EKeys::Gamepad_DPad_Down })) Move(1);
		// (a key held down: the cursor goes on after a moment, a step every 80 ms, as long as it is held; the user's of 2026-10-26)
		if (Generator && Generator->bKeyRepeat)
		{
			// (armed only by a key pressed while the list is open: one held from before (W walking her) does not run it)
			auto Down = [PC](std::initializer_list<FKey> Keys) { for (const FKey& K : Keys) if (PC->IsInputKeyDown(K)) return true; return false; };
			const int32 Dir = Down({ EKeys::W, EKeys::Up, EKeys::Gamepad_DPad_Up }) ? -1 : Down({ EKeys::S, EKeys::Down, EKeys::Gamepad_DPad_Down }) ? 1 : 0;
			const bool bJust = Dir < 0 ? Pressed({ EKeys::W, EKeys::Up, EKeys::Gamepad_DPad_Up }) : Dir > 0 ? Pressed({ EKeys::S, EKeys::Down, EKeys::Gamepad_DPad_Down }) : false;
			const double Now = FPlatformTime::Seconds();
			if (Dir == 0) KeyRepeatDir = 0;
			else if (bJust) { KeyRepeatDir = Dir; KeyRepeatAt = Now + 0.35; }
			else if (Dir == KeyRepeatDir && Now >= KeyRepeatAt) { Move(Dir); KeyRepeatAt = Now + 0.08; }
		}
		const float Sy = PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftY);
		if (FMath::Abs(Sy) > 0.6f)
		{
			const float Now = FPlatformTime::Seconds();
			if (Now > InventoryRepeat) { Move(Sy > 0.f ? -1 : 1); InventoryRepeat = Now + (InventoryRepeat > 0.f ? 0.22f : 0.4f); }
		}
		else InventoryRepeat = 0.f;
	};
	const bool bUse = Pressed({ EKeys::Enter, EKeys::SpaceBar, EKeys::E, EKeys::LeftMouseButton, EKeys::Gamepad_FaceButton_Bottom });
	const bool bToggle = Pressed({ EKeys::I, EKeys::Tab, EKeys::Gamepad_Special_Right });
	// (level 5: the anvil's crafting panel, opened by the generator's F)
	if (bCraftOpen)
	{
		if (bToggle || Pressed({ EKeys::F, EKeys::BackSpace, EKeys::Gamepad_FaceButton_Right, EKeys::Gamepad_FaceButton_Left })) { SetCraftingOpen(false); return; }
		Steer([this](int32 S) { MoveCraftCursor(S); });
		if (bUse) CraftEntry();
		return;
	}
	if (!bInventoryOpen) { if (bToggle && !bDead) SetInventoryOpen(true); return; }
	// (level 5: choosing what a repair item mends; Backspace or B back to the inventory)
	if (IsPickingRepair())
	{
		if (bToggle) { SetInventoryOpen(false); return; }
		if (Pressed({ EKeys::BackSpace, EKeys::Gamepad_FaceButton_Right })) { CancelRepair(); return; }
		Steer([this](int32 S) { MoveRepairCursor(S); });
		if (bUse) RepairEntry();
		return;
	}
	if (bToggle || Pressed({ EKeys::Gamepad_FaceButton_Right })) { SetInventoryOpen(false); return; }
	Steer([this](int32 S) { MoveInventoryCursor(S); });
	if (bUse) UseInventoryEntry();
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
	if (PC->WasInputKeyJustPressed(EKeys::One) || (!Generator->bMapOpen && PC->WasInputKeyJustPressed(EKeys::Gamepad_DPad_Left))) SelectWeapon(0);
	if (PC->WasInputKeyJustPressed(EKeys::Two) || (!Generator->bMapOpen && PC->WasInputKeyJustPressed(EKeys::Gamepad_DPad_Up))) SelectWeapon(1);
	if (PC->WasInputKeyJustPressed(EKeys::Three) || (!Generator->bMapOpen && PC->WasInputKeyJustPressed(EKeys::Gamepad_DPad_Right))) SelectWeapon(2);
	// (level 5: with spells learned there may be many: 4 to 0 draw the fourth to the tenth)
	{
		static const FKey More[] = { EKeys::Four, EKeys::Five, EKeys::Six, EKeys::Seven, EKeys::Eight, EKeys::Nine, EKeys::Zero };
		for (int32 K = 0; K < UE_ARRAY_COUNT(More); ++K) if (PC->WasInputKeyJustPressed(More[K])) SelectWeapon(3 + K);
	}
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
	// (level 5: a spell of the table: its bolt pierces, jumps, carries its colours)
	const FRDSpellDef* S = SpellOf(AttackIndex);
	if (S) { B.Spell = W->SpellIndex; B.bPierce = S->bPierce; B.ChainLeft = S->Count > 0 && S->Radius > 0.f ? S->Count : 0; }
	if (Grown) { Grown->SetWorldLocationAndRotation(B.At, R); B.Fx = Grown; }
	else if (W->BoltEffect) B.Fx = S ? SpawnSpellFx(W->BoltEffect, B.At, R, W->BoltEffectScale, S) : SpawnFx(W->BoltEffect, B.At, R, W->BoltEffectScale);
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
	Generator->PlaySoundAt(FName(*FString::Printf(TEXT("Player.Cast.%s"), *WeaponSound(*W).ToString())), B.At);
}

void URDCombatComponent::PlaceBoltMesh(UStaticMeshComponent* C, const FRDWeaponDef& W, const FVector& At, const FVector& Dir) const
{
	if (C) C->SetWorldTransform(W.BoltMeshTransform * FTransform(Dir.Rotation(), At));
}

void URDCombatComponent::Burst(FBolt& B, const FVector& At, ARDMonster* Direct)
{
	if (B.Spell >= 0) { SpellBurst(B, At, Direct); return; }      // (level 5: a spell of the table)
	if (!Generator->Weapons.IsValidIndex(B.Weapon)) return;
	const FRDWeaponDef& W = Generator->Weapons[B.Weapon];
	AActor* O = GetOwner();
	if (W.BurstEffect) SpawnFx(W.BurstEffect, At, B.Vel.Rotation(), W.BurstEffectScale);
	if (W.BurstFlameEffect)
		if (UFXSystemComponent* Fl = SpawnFx(W.BurstFlameEffect, At, FRotator::ZeroRotator, W.BurstFlameEffectScale)) TimedFx.Add({ Fl, W.BurstFlameSeconds });
	Generator->PlaySoundAt(FName(*FString::Printf(TEXT("Player.Hit.%s"), *WeaponSound(W).ToString())), At);
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
	if (bAny) { LastHitTime = GetWorld()->GetTimeSeconds(); WearOut(B.Weapon); }       // (a bolt that hit wears its weapon)
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
		if (UFXSystemComponent* F = TimedFx[I].Fx.Get()) { if (TimedFx[I].bKill) { F->DeactivateImmediate(); F->DestroyComponent(); } else F->Deactivate(); }
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
		// (level 5: a spell's bolt may outlive its weapon (a chain's jump, a meteor): the spell's numbers then)
		const FRDSpellDef* Sp = B.Spell >= 0 && Generator->Spells.IsValidIndex(B.Spell) ? &Generator->Spells[B.Spell] : nullptr;
		const bool bWeapon = Generator->Weapons.IsValidIndex(B.Weapon) && (B.Spell < 0 || Generator->Weapons[B.Weapon].SpellIndex == B.Spell);
		if (!bWeapon && !Sp) { Bolts.RemoveAt(I); continue; }
		FRDWeaponDef SpellW;
		if (!bWeapon) { SpellW.Reach = Sp->Reach; SpellW.BoltTurnRate = 260.f; }
		const FRDWeaponDef& W = bWeapon ? Generator->Weapons[B.Weapon] : SpellW;
		// (a meteor falls to its point, a drain's wisp flies back to her hand)
		if (B.bGoal)
		{
			if (B.bWisp && O) B.Goal = O->GetActorLocation() + FVector(0, 0, 40.f);
			const FVector To = B.Goal - B.At;
			const float Step = B.Vel.Size() * Dt;
			if (To.Size() <= FMath::Max(Step, 20.f))
			{
				if (!B.bWisp) SpellBurst(B, B.Goal, nullptr);
				else { if (UFXSystemComponent* F = B.Fx.Get()) F->Deactivate(); if (UPointLightComponent* L = B.Light.Get()) L->DestroyComponent(); }
				Bolts.RemoveAt(I); continue;
			}
			B.Vel = To.GetSafeNormal() * B.Vel.Size(); B.At += B.Vel * Dt; B.Flown += Step;
			if (UFXSystemComponent* F = B.Fx.Get()) F->SetWorldLocationAndRotation(B.At, B.Vel.Rotation());
			if (UPointLightComponent* L = B.Light.Get()) L->SetWorldLocation(B.At);
			continue;
		}
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
			if (B.Done.Contains(Mo)) continue;           // (one it passed through, or jumped from)
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
		if (HitMo && B.bPierce)
		{
			// (level 5: a piercing bolt hurts it and flies on)
			SpellPierce(B, HitMo, HitAt);
			B.Done.Add(HitMo);
			B.Target = nullptr;
		}
		else if (HitMo)
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
