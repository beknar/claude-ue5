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
	if (Ix < 0) return 0.f;
	// (the list of 2026-11-10: a shield worn out takes half its share, as armour does, until it is mended (the start shield never wears))
	const bool bWorn = Generator->Items[Ix].Durability > 0.f && GetShieldWear(WornShield) <= 0.f && !(Generator->bKeepStartGear && WornShield == StartShieldOf());
	return Generator->Items[Ix].Amount * (bWorn ? 0.5f : 1.f);
}

void URDCombatComponent::UpdateLeftHand()
{
	if (!Generator || !LeftComp) return;
	USkeletalMeshComponent* M = Body();
	const FRDWeaponFit* Fit = nullptr;
	if (bTorchHeld && !TorchItem.IsNone() && GetItemCount(TorchItem) > 0) Fit = FitOf(TorchItem);
	else if (IsShieldInHand()) Fit = FitOf(WornShield);
	// (what her drawn weapon has in the other hand gives way to the shield or the torch)
	// (the list of 2026-11-11: "when the warrior puts on a shield in inventory, then takes it off, her default appears on her arm
	// again": a found sword's fit still carried the old built-in shield (SM_Shield_1) in its off hand. Where shields are things
	// she finds and wears, a weapon's own shield is never shown: 918 noshield11 also takes them off the data)
	if (OffHandComp)
	{
		const FRDWeaponDef* W = Weapon();
		bool bOwnShield = W && W->OffHandMesh && W->OffHandMesh->GetName().Contains(TEXT("Shield"));
		if (bOwnShield) bOwnShield = Generator->Items.ContainsByPredicate([](const FRDItemDef& It) { return It.Kind == ERDItemKind::Shield; });
		OffHandComp->SetVisibility(!Fit && W && W->OffHandMesh != nullptr && !bOwnShield);
	}
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
	// (the list of 2026-11-10: the ankh's light is pale and has no flame)
	const bool bAnkh = bTorch && IsAnkhHeld();
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
		TorchLight->SetRelativeLocation(bAnkh ? Generator->AnkhGlowAt : Generator->TorchFlame + FVector(0, 0, 15));
		TorchLight->SetIntensity(bAnkh ? Generator->AnkhLight : Generator->TorchLight);
		TorchLight->SetLightColor(bAnkh ? Generator->AnkhColor : FLinearColor(1.f, 0.56f, 0.24f));
		TorchLight->SetAttenuationRadius(bAnkh ? Generator->AnkhLightRadius : 1600.f);
		TorchLight->SetVisibility(true);
		if (bAnkh && TorchFlame) { TorchFlame->DeactivateImmediate(); TorchFlame->DestroyComponent(); TorchFlame = nullptr; }
		if (!bAnkh && !TorchFlame && Generator->TorchFx) TorchFlame = RDMSpawnFx(GetOwner(), Generator->TorchFx, Generator->TorchFlame, FRotator::ZeroRotator, Generator->TorchFxScale, LeftComp, false, false);
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
		if (!FitOf(TorchItem)) { SetMessage(FString::Printf(TEXT("The %s cannot hold the %s"), *Generator->PlayerTitle.ToLower(), *TorchItem.ToString().ToLower())); return false; }
	}
	bTorchHeld = bHold;
	UpdateLeftHand(); UpdateWalkSpeed();
	const int32 Ti = Generator->FindItem(TorchItem);
	if (Ti >= 0 && Generator->Items[Ti].Kind == ERDItemKind::Light)
		SetMessage(bHold ? FString::Printf(TEXT("You raise the %s: its light shows the traps and the unlooted chests near you"), *TorchItem.ToString().ToLower()) : FString::Printf(TEXT("You lower the %s"), *TorchItem.ToString().ToLower()));
	else SetMessage(bHold ? FString(TEXT("You light the torch: it lights your way (your left hand is busy)")) : FString(TEXT("You put out the torch")));
	Generator->PlaySoundAt(bHold ? FName(TEXT("Env.Torch")) : FName(TEXT("Player.Inventory")), GetOwner()->GetActorLocation());
	return true;
}

void URDCombatComponent::WearDownShield(float Took)
{
	if (WornShield.IsNone() || Took <= 0.f) return;
	// (the third list, bKeepStartGear: the shield her hero starts with never breaks: "these they always have")
	if (Generator && Generator->bKeepStartGear && WornShield == StartShieldOf()) return;
	float& W = ArmourWear.FindOrAdd(WornShield);
	const bool bWasWhole = W > 0.f;
	W = FMath::Max(0.f, W - Took);
	if (W > 0.f || !bWasWhole) return;
	// (the list of 2026-11-10: it no longer breaks: worn out, it stays on her arm and takes half its share of a blow until it is
	// mended at an anvil or with a repair item, as armour does; said once, as it wears out. With a whole one of the same in her
	// pack she takes that up and the worn one goes in her pack (PR #38's review: spares had always taken a broken one's place))
	++ShieldsBroken;
	if (TArray<float>* Sp = Spares.Find(WornShield); Sp && Sp->Num() > 0)
	{
		Sp->Sort(TGreater<float>());          // (the whole ones first: a breakdown takes the most worn, the last)
		if ((*Sp)[0] > 0.f)
		{
			W = (*Sp)[0]; (*Sp)[0] = 0.f; Sp->Sort(TGreater<float>());
			SetMessage(FString::Printf(TEXT("Your %s is worn out: you take up a whole one (the worn one goes in your pack)"), *WornShield.ToString().ToLower()));
			if (Generator && GetOwner()) Generator->PlaySoundAt(TEXT("Player.Draw"), GetOwner()->GetActorLocation());
			UE_LOG(LogTemp, Log, TEXT("RDSHIELD %s worn out: a spare taken up"), *WornShield.ToString());
			return;
		}
	}
	SetMessage(FString::Printf(TEXT("Your %s is worn out: it takes half as much of a blow until it is mended"), *WornShield.ToString().ToLower()));
	if (Generator && GetOwner()) Generator->PlaySoundAt(TEXT("Player.Break"), GetOwner()->GetActorLocation());
	UE_LOG(LogTemp, Log, TEXT("RDSHIELD %s worn out"), *WornShield.ToString());
}

// ------------------------------------------------------------------------------------------------ what she drops, takes back, breaks down
void URDCombatComponent::GatherDroppable(TArray<FName>& Things, TArray<float>& WearOut, bool bDeath) const
{
	Things.Reset(); WearOut.Reset();
	if (!Generator) return;
	// (the weapons she found, each with what is left of it; her hero's own are not things of the item table (her hands, her
	// spells): they stay hers)
	for (int32 I = 0; I < Generator->Weapons.Num(); ++I)
		if (!Generator->Weapons[I].Item.IsNone())
		{
			Things.Add(Generator->Weapons[I].Item); WearOut.Add(GetWeaponWear(I));
			// (the third list: a found weapon's slash drops beside it, a thing of its own)
			if (!Generator->Weapons[I].Slash.IsNone()) { Things.Add(Generator->Weapons[I].Slash); WearOut.Add(-1.f); }
		}
	// (everything she carries, the shield she started with too: "all of her equipment drops" (the list's words; until
	// 2026-10-27 one copy of that shield stayed with her). The third list: with bKeepStartGear one copy of it stays: "these
	// they always have")
	const FName Keep = Generator->bKeepStartGear ? StartShieldOf() : NAME_None;
	for (const FName& N : CarriedOrder)
	{
		// (a dungeon's key or map stays hers: the way it opens is not lost at a death (the list of 2026-11-08b))
		if (bDeath && Generator->IsDungeonChainItem(N)) continue;
		const int32 Cnt = GetItemCount(N) - (N == Keep ? 1 : 0);
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
	// (the third list, bKeepStartGear: her starting shield stayed on her arm; the one she wore when she fell goes back on in its place)
	const bool bFree = WornShield.IsNone() || (Generator->bKeepStartGear && WornShield == StartShieldOf() && Rewear != WornShield);
	if (bHers && bFree && !Rewear.IsNone() && GetItemCount(Rewear) > 0) WearShield(Rewear);
	if (bHers) SetMessage(FString::Printf(TEXT("You take up your things again (%d)"), Got));
	else SetMessage(Things.Num() == 1 ? FString::Printf(TEXT("You take the %s"), *Things[0].ToString().ToLower()) : FString::Printf(TEXT("You take up what lies here (%d)"), Got));
	InventoryCursor = FMath::Clamp(InventoryCursor, 0, FMath::Max(0, GetInventoryLines().Num() - 1));
}

bool URDCombatComponent::BreakDownGear(FName Item)
{
	const int32 Ix = Generator && !bDead ? Generator->FindItem(Item) : -1;
	if (Ix < 0 || GetItemCount(Item) <= 0) return false;
	const FRDItemDef& It = Generator->Items[Ix];
	// (the list of 2026-10-30, bBreakAnyGear: a ring and the torch too)
	const bool bAny = Generator->bBreakAnyGear && (It.Kind == ERDItemKind::Ring || It.Kind == ERDItemKind::Torch);
	if (It.Kind != ERDItemKind::Shield && !(It.Kind == ERDItemKind::Armour && Generator->bArmourStacks) && !bAny) return false;
	const FString Lb = Item.ToString().ToLower();
	// (the one she wears goes only when it is the last, and then she takes it off first)
	const bool bOn = Item == WornArmour || Item == WornShield || (It.Kind == ERDItemKind::Ring && GetWornRing(It.RingKind) == Item) || (It.Kind == ERDItemKind::Torch && bTorchHeld && TorchItem == Item);
	if (bOn && GetItemCount(Item) <= 1)
	{
		SetMessage(It.Kind == ERDItemKind::Torch ? FString::Printf(TEXT("The %s burns in your hand: put it out first"), *Lb) : FString::Printf(TEXT("You wear the %s: take it off first"), *Lb));
		return false;
	}
	const FString Gives = BreakdownText(Item, It.WeaponType);
	if (Gives.IsEmpty()) return false;
	// (the list of 2026-11-10: the most worn copy goes (PR #38's review: a spare was taken first, a whole one thrown away while the
	// worn one stayed on her arm): spares whole first, and the copy in use changes places with the last spare when that is less worn)
	if (TArray<float>* Sp = Spares.Find(Item); Sp && Sp->Num() > 0)
	{
		Sp->Sort(TGreater<float>());
		float& Use = ArmourWear.FindOrAdd(Item);
		if (Sp->Last() > Use) Swap(Sp->Last(), Use);
		Sp->Sort(TGreater<float>());
	}
	RemoveCarried(Item, 1);
	TArray<FString> Ps; Gives.ParseIntoArray(Ps, TEXT(";"));
	TArray<FString> Got;
	for (const FString& P : Ps) { FString N, C; if (P.Split(TEXT(":"), &N, &C)) { AddItem(FName(*N), FCString::Atoi(*C)); Got.Add(FString::Printf(TEXT("%s %s"), *C, *N.ToLower())); } }
	++GearBrokenDown; ++WeaponsBrokenDown;
	SetMessage(FString::Printf(TEXT("You break down the %s:  %s   (%d left)"), *Lb, *FString::Join(Got, TEXT(", ")), GetItemCount(Item)));
	PlayUiSound(TEXT("Player.Craft"), TEXT("Player.Loot"));
	UE_LOG(LogTemp, Log, TEXT("RDBREAKDOWN %s -> %s"), *Item.ToString(), *Gives);
	return true;
}
