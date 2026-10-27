// mistward_castle: her left hand (a shield or a torch), armour and shields kept copy by copy, what she drops when she falls,
// traps that hold her. URDCombatComponent's (RDCombat.h).
#include "RD/RDCombat.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDMistward.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "NiagaraComponent.h"
#include "Particles/ParticleSystemComponent.h"

// ------------------------------------------------------------------------------------------------ held by a trap
void URDCombatComponent::HoldFor(float Seconds)
{
	if (bDead || Seconds <= 0.f || !GetWorld()) return;
	HeldUntil = FMath::Max(HeldUntil, GetWorld()->GetTimeSeconds() + Seconds);
	if (!bHeldOn) { bHeldOn = true; UpdateWalkSpeed(); }
	if (ACharacter* C = Cast<ACharacter>(GetOwner())) C->GetCharacterMovement()->StopMovementImmediately();
}

bool URDCombatComponent::IsHeld() const { return bHeldOn && GetWorld() && GetWorld()->GetTimeSeconds() < HeldUntil; }

// ------------------------------------------------------------------------------------------------ her left hand
const FRDWeaponFit* URDCombatComponent::FitOf(FName Item) const
{
	const int32 Ix = Generator ? Generator->FindItem(Item) : -1;
	if (Ix < 0) return nullptr;
	return Generator->Items[Ix].WeaponFits.FindByPredicate([this](const FRDWeaponFit& F) { return F.Hero == Generator->CurrentHero && F.Weapon.OffHandMesh != nullptr; });
}

bool URDCombatComponent::IsShieldInHand() const
{
	if (WornShield.IsNone() || bTorchHeld || !Generator || !FitOf(WornShield)) return false;
	// (a shield goes with a weapon held in one hand: not with a spell, a bow or a crossbow, or a two-handed sword)
	const FRDWeaponDef* W = Weapon();
	if (!W || W->bSpell) return false;
	const FString T = W->WeaponType.ToLower();
	return !T.Contains(TEXT("two handed")) && !T.Contains(TEXT("bow"));
}

float URDCombatComponent::GetShieldShare() const
{
	if (!IsShieldInHand()) return 0.f;
	const int32 Ix = Generator->FindItem(WornShield);
	return Ix >= 0 ? Generator->Items[Ix].Amount : 0.f;
}

void URDCombatComponent::UpdateLeftHand()
{
	if (!Generator || !LeftComp) return;
	USkeletalMeshComponent* M = Body();
	const FRDWeaponFit* Fit = nullptr;
	if (bTorchHeld && !TorchItem.IsNone() && GetItemCount(TorchItem) > 0) Fit = FitOf(TorchItem);
	else if (IsShieldInHand()) Fit = FitOf(WornShield);
	// (what her drawn weapon has in the other hand gives way to the shield or the torch)
	if (OffHandComp) { const FRDWeaponDef* W = Weapon(); OffHandComp->SetVisibility(!Fit && W && W->OffHandMesh != nullptr); }
	if (!Fit || !M)
	{
		LeftComp->SetVisibility(false);
		if (TorchLight) TorchLight->SetVisibility(false);
		if (TorchFlame) { TorchFlame->DeactivateImmediate(); TorchFlame->DestroyComponent(); TorchFlame = nullptr; }
		return;
	}
	LeftComp->SetStaticMesh(Fit->Weapon.OffHandMesh);
	LeftComp->AttachToComponent(M, FAttachmentTransformRules::SnapToTargetNotIncludingScale, Fit->Weapon.OffHandBone);
	LeftComp->SetRelativeTransform(Fit->Weapon.OffHandGrip);
	LeftComp->SetVisibility(true);
	const bool bTorch = bTorchHeld;
	if (bTorch)
	{
		// (the flame at the torch's head, a warm light that goes with it)
		if (!TorchLight)
		{
			TorchLight = NewObject<UPointLightComponent>(GetOwner(), TEXT("RDTorchLight"));
			TorchLight->SetMobility(EComponentMobility::Movable);
			TorchLight->SetIntensityUnits(ELightUnits::Candelas);
			TorchLight->SetLightColor(FLinearColor(1.f, 0.56f, 0.24f));
			TorchLight->SetAttenuationRadius(1600.f);
			TorchLight->SetSourceRadius(4.f);
			TorchLight->SetCastShadows(true);
			TorchLight->RegisterComponent();
		}
		TorchLight->AttachToComponent(LeftComp, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
		TorchLight->SetRelativeLocation(Generator->TorchFlame + FVector(0, 0, 15));
		TorchLight->SetIntensity(Generator->TorchLight);
		TorchLight->SetVisibility(true);
		if (!TorchFlame && Generator->TorchFx) TorchFlame = RDMSpawnFx(GetOwner(), Generator->TorchFx, Generator->TorchFlame, FRotator::ZeroRotator, Generator->TorchFxScale, LeftComp, false, false);
	}
	else
	{
		if (TorchLight) TorchLight->SetVisibility(false);
		if (TorchFlame) { TorchFlame->DeactivateImmediate(); TorchFlame->DestroyComponent(); TorchFlame = nullptr; }
	}
}

bool URDCombatComponent::WearShield(FName Item)
{
	if (!Generator || bDead || GetItemCount(Item) <= 0) return false;
	const int32 Ix = Generator->FindItem(Item);
	if (Ix < 0 || Generator->Items[Ix].Kind != ERDItemKind::Shield) return false;
	const FString Lb = Item.ToString().ToLower();
	if (WornShield == Item && !bTorchHeld)
	{
		WornShield = NAME_None;
		UpdateLeftHand(); UpdateWalkSpeed();
		SetMessage(FString::Printf(TEXT("You put away the %s"), *Lb));
		Generator->PlaySoundAt(TEXT("Player.Inventory"), GetOwner()->GetActorLocation());
		return true;
	}
	if (!FitOf(Item)) { SetMessage(FString::Printf(TEXT("The %s carries no shield"), *Generator->PlayerTitle.ToLower())); return false; }
	WornShield = Item;
	if (bTorchHeld) { bTorchHeld = false; }          // (the shield takes her left hand from the torch)
	UpdateLeftHand(); UpdateWalkSpeed();
	const FRDItemDef& It = Generator->Items[Ix];
	const FRDWeaponDef* W = Weapon();
	SetMessage(IsShieldInHand() ? FString::Printf(TEXT("You take up the %s:  blows take %.0f%% less,  you move %.0f%% slower"), *Lb, It.Amount * 100.f, It.Slower * 100.f)
	                            : FString::Printf(TEXT("You sling the %s: it goes on your arm with a one-handed weapon (not the %s)"), *Lb, W ? *W->Name.ToString().ToLower() : TEXT("spell")));
	Generator->PlaySoundAt(TEXT("Player.Draw"), GetOwner()->GetActorLocation());
	return true;
}

bool URDCombatComponent::HoldTorch(bool bHold)
{
	if (!Generator || bDead) return false;
	if (bHold)
	{
		// (the torch named, or the first she carries)
		if (TorchItem.IsNone() || GetItemCount(TorchItem) <= 0)
		{
			TorchItem = NAME_None;
			for (const FName& N : CarriedOrder) { const int32 Ix = Generator->FindItem(N); if (Ix >= 0 && Generator->Items[Ix].Kind == ERDItemKind::Torch) { TorchItem = N; break; } }
		}
		if (TorchItem.IsNone()) { SetMessage(TEXT("You have no torch: an anvil makes one")); return false; }
		if (!FitOf(TorchItem)) { SetMessage(FString::Printf(TEXT("The %s cannot hold the torch"), *Generator->PlayerTitle.ToLower())); return false; }
	}
	bTorchHeld = bHold;
	UpdateLeftHand(); UpdateWalkSpeed();
	SetMessage(bHold ? FString(TEXT("You light the torch: it lights your way (your left hand is busy)")) : FString(TEXT("You put out the torch")));
	Generator->PlaySoundAt(bHold ? FName(TEXT("Env.Torch")) : FName(TEXT("Player.Inventory")), GetOwner()->GetActorLocation());
	return true;
}

void URDCombatComponent::WearDownShield(float Took)
{
	if (WornShield.IsNone() || Took <= 0.f) return;
	float& W = ArmourWear.FindOrAdd(WornShield);
	W = FMath::Max(0.f, W - Took);
	if (W > 0.f) return;
	// (it breaks: a spare one of the same takes its place, or it is gone)
	const FName Gone = WornShield;
	++ShieldsBroken;
	if (TArray<float>* Sp = Spares.Find(Gone); Sp && Sp->Num() > 0)
	{
		W = Sp->Pop();
		int32* N = Carried.Find(Gone); if (N) --*N;
		SetMessage(FString::Printf(TEXT("Your %s broke: you take up the next one"), *Gone.ToString().ToLower()));
	}
	else
	{
		RemoveCarried(Gone, 1);
		WornShield = NAME_None;
		SetMessage(FString::Printf(TEXT("Your %s broke"), *Gone.ToString().ToLower()));
	}
	if (Generator && GetOwner()) Generator->PlaySoundAt(TEXT("Player.Break"), GetOwner()->GetActorLocation());
	UpdateLeftHand(); UpdateWalkSpeed();
	UE_LOG(LogTemp, Log, TEXT("RDSHIELD %s broke"), *Gone.ToString());
}

// ------------------------------------------------------------------------------------------------ what she drops, takes back, breaks down
void URDCombatComponent::GatherDroppable(TArray<FName>& Things, TArray<float>& WearOut) const
{
	Things.Reset(); WearOut.Reset();
	if (!Generator) return;
	// (the weapons she found, each with what is left of it; her hero's own are not things of the item table (her hands, her
	// spells): they stay hers)
	for (int32 I = 0; I < Generator->Weapons.Num(); ++I)
		if (!Generator->Weapons[I].Item.IsNone()) { Things.Add(Generator->Weapons[I].Item); WearOut.Add(GetWeaponWear(I)); }
	// (everything she carries, the shield she started with too: "all of her equipment drops" (the list's words; until
	// 2026-10-27 one copy of that shield stayed with her))
	for (const FName& N : CarriedOrder)
	{
		const int32 Cnt = GetItemCount(N);
		const int32 Ix = Generator->FindItem(N);
		const bool bKept = Ix >= 0 && (Generator->Items[Ix].Kind == ERDItemKind::Armour || Generator->Items[Ix].Kind == ERDItemKind::Shield);
		const TArray<float>* Sp = Spares.Find(N);
		for (int32 K = 0; K < Cnt; ++K)
		{
			Things.Add(N);
			WearOut.Add(!bKept ? -1.f : K == 0 ? GetArmourWear(N) : (Sp && Sp->IsValidIndex(K - 1) ? (*Sp)[K - 1] : -1.f));
		}
	}
}

void URDCombatComponent::TakeBack(const TArray<FName>& Things, const TArray<float>& WearIn, bool bHers, FName Rewear)
{
	if (!Generator) return;
	int32 Got = 0;
	for (int32 I = 0; I < Things.Num(); ++I)
	{
		const FName N = Things[I];
		const float W = WearIn.IsValidIndex(I) ? WearIn[I] : -1.f;
		const int32 Ix = Generator->FindItem(N);
		if (Ix < 0) continue;
		const ERDItemKind K = Generator->Items[Ix].Kind;
		const int32 WeaponsBefore = Generator->Weapons.Num();
		const int32 Before = GetItemCount(N);
		AddItem(N, 1);
		++Got;
		// (each comes back as worn as it was)
		if (W < 0.f) continue;
		if (K == ERDItemKind::Weapon && Generator->Weapons.Num() > WeaponsBefore) { SyncWear(); Wear[Generator->Weapons.Num() - 1] = W; }
		else if (K == ERDItemKind::Armour || K == ERDItemKind::Shield)
		{
			if (Before == 0) ArmourWear.Add(N, W);
			else if (TArray<float>* Sp = Spares.Find(N); Sp && Sp->Num() > 0) Sp->Last() = W;
			// (kept once (bArmourStacks off): AddItem mended hers to full, as a set found again does; the copy taken up does
			// not wear it down again)
			else { float& Cur = ArmourWear.FindOrAdd(N); Cur = FMath::Max(Cur, W); }
		}
	}
	// (her own pile: the shield that was on her arm when she fell goes back on (a found one, or none if she wore none))
	if (bHers && WornShield.IsNone() && !Rewear.IsNone() && GetItemCount(Rewear) > 0) WearShield(Rewear);
	if (bHers) SetMessage(FString::Printf(TEXT("You take up your things again (%d)"), Got));
	else SetMessage(Things.Num() == 1 ? FString::Printf(TEXT("You take the %s"), *Things[0].ToString().ToLower()) : FString::Printf(TEXT("You take up what lies here (%d)"), Got));
	InventoryCursor = FMath::Clamp(InventoryCursor, 0, FMath::Max(0, GetInventoryLines().Num() - 1));
}

bool URDCombatComponent::BreakDownGear(FName Item)
{
	const int32 Ix = Generator && !bDead ? Generator->FindItem(Item) : -1;
	if (Ix < 0 || GetItemCount(Item) <= 0) return false;
	const FRDItemDef& It = Generator->Items[Ix];
	if (It.Kind != ERDItemKind::Shield && !(It.Kind == ERDItemKind::Armour && Generator->bArmourStacks)) return false;
	const FString Lb = Item.ToString().ToLower();
	// (the one she wears goes only when it is the last, and then she takes it off first)
	if ((Item == WornArmour || Item == WornShield) && GetItemCount(Item) <= 1)
	{
		SetMessage(FString::Printf(TEXT("You wear the %s: take it off first"), *Lb));
		return false;
	}
	const FString Gives = BreakdownText(Item, It.WeaponType);
	if (Gives.IsEmpty()) return false;
	RemoveCarried(Item, 1);
	TArray<FString> Ps; Gives.ParseIntoArray(Ps, TEXT(";"));
	TArray<FString> Got;
	for (const FString& P : Ps) { FString N, C; if (P.Split(TEXT(":"), &N, &C)) { AddItem(FName(*N), FCString::Atoi(*C)); Got.Add(FString::Printf(TEXT("%s %s"), *C, *N.ToLower())); } }
	++GearBrokenDown; ++WeaponsBrokenDown;
	SetMessage(FString::Printf(TEXT("You break down the %s:  %s"), *Lb, *FString::Join(Got, TEXT(", "))));
	PlayUiSound(TEXT("Player.Craft"), TEXT("Player.Loot"));
	UE_LOG(LogTemp, Log, TEXT("RDBREAKDOWN %s -> %s"), *Item.ToString(), *Gives);
	return true;
}
