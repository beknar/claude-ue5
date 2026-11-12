// mistward_castle, the list of 2026-11-01 (docs/improvements6.txt; pipeline/unreal/880). Each rule a switch on the
// generator ("Mistward6" category), off on the other levels:
//   stealth       the Rogue hides for a while from a pool of dexterity energy (back slowly, like mana; a speed potion fills
//                 it): monsters lose her and no trap goes off under her; her first blow or bolt out of it is an ambush
//   tier growth   the heroes grow as the tiers open (hit points, spells and chi, fists: each hero her own shares), and mana
//                 comes back as a share of her pool
#include "RD/RDDungeonGenerator.h"
#include "RD/RDCombat.h"
#include "RD/RDMonster.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDMistward6, Log, All);

// (her stealth's look: the Shadow Veil's aura, kept apart from the veil's own (whose end would take it off): RDCombat.h's key)
static const ERDSpellKind RD6StealthAura = RDStealthAuraKind;

// ================================================================================================ the tiers' growth
int32 ARDDungeonGenerator::GetOpenTier() const
{
	int32 T = 1;
	for (const int32 O : TiersOpened) T = FMath::Max(T, O);
	return FMath::Clamp(T, 1, FMath::Max(MaxTier, 1));
}

float ARDDungeonGenerator::TierHealthMul() const
{
	const FRDHeroDef* H = bTierGrowth ? FindHero(CurrentHero) : nullptr;
	return H ? GrowthAt(H->HealthPerTier, GrowthTier(), TierGrowthHealth) : 1.f;
}

float ARDDungeonGenerator::TierSpellMul() const
{
	const FRDHeroDef* H = bTierGrowth ? FindHero(CurrentHero) : nullptr;
	return H ? GrowthAt(H->SpellPowerPerTier, GrowthTier(), TierGrowthPower) : 1.f;
}

float ARDDungeonGenerator::TierOwnWeaponMul() const
{
	const FRDHeroDef* H = bTierGrowth ? FindHero(CurrentHero) : nullptr;
	return H ? GrowthAt(H->OwnWeaponPowerPerTier, GrowthTier(), TierGrowthPower) : 1.f;
}

float ARDDungeonGenerator::TierManaMul() const
{
	const FRDHeroDef* H = bTierGrowth ? FindHero(CurrentHero) : nullptr;
	return H ? GrowthAt(H->ManaPerTier, GrowthTier(), TierGrowthHealth) : 1.f;
}

bool ARDDungeonGenerator::SummonsGrow() const
{
	const FRDHeroDef* H = bTierGrowth ? FindHero(CurrentHero) : nullptr;
	return H && H->bSummonsGrow;
}

void ARDDungeonGenerator::SummonStrength(FName Spell, float& OutHealth, float& OutDamage, int32& OutTier) const
{
	// (the Summoner's balance of 2026-11-05: her summons were monsters of their kind's own tier, so a tier-1 summoning stayed at
	// 60 hit points and 14 a blow at tier 5, and the first two died to one blow of the final boss each)
	const FRDSpellDef* S = Spells.FindByPredicate([Spell](const FRDSpellDef& D) { return D.Name == Spell; });
	// (the rebalance to tier 25: a summoning's own tier up to its table's (the later dungeons' summonings 6 on); the summons as
	// strong as the game's tier she has reached (GrowthTier), not this level's)
	const int32 St = FMath::Clamp(S ? S->Tier : 1, 1, FMath::Max(SummonTierStrength.Num(), 5));
	const int32 T = FMath::Max(GrowthTier(), St);
	OutTier = T;
	const float K = SummonTierStrength.IsValidIndex(St - 1) ? SummonTierStrength[St - 1] : 1.f;
	const float Ref = MonsterReferenceHealth > 0.f ? MonsterReferenceHealth : PlayerMaxHealth;
	const float Blow = MonsterReferenceBlow > 0.f ? MonsterReferenceBlow : GetAverageWeaponDamage();
	// (the sixth phase: her minions' health and damage (1 when not learned))
	OutHealth = FMath::Max(1.f, FMath::RoundToFloat(Ref * TierValue(TierHealth, T, 1.f) * K * SecondaryMul(TEXT("MinionHealth"))));
	OutDamage = FMath::Max(1.f, FMath::RoundToFloat(Blow * TierValue(TierDamage, T, 1.f) * K * SecondaryMul(TEXT("MinionDamage"))));
}

float ARDDungeonGenerator::TierPowerOf(const FRDWeaponDef& W) const
{
	if (!bTierGrowth) return 1.f;
	// (a spell, a chi attack or a scroll: magic; a bolt that is a mesh is a crossbow's, a weapon; one of her hero's own
	// weapons (no item: her fists, her starting blades and crossbow); a found one grows by its own tier (880's data))
	if (W.bSpell && !W.BoltMesh) return TierSpellMul();
	if (W.Item.IsNone()) return TierOwnWeaponMul();
	return 1.f;
}

float ARDDungeonGenerator::GetManaRegen(float Max) const
{
	const FRDHeroDef* H = bTierGrowth ? FindHero(CurrentHero) : nullptr;
	return H && H->ManaRegenShare > 0.f ? Max * H->ManaRegenShare : ManaPerSecond;
}

void ARDDungeonGenerator::OnTierGrowth(int32 Tier)
{
	if (!bTierGrowth || !PlayerCombat) return;
	const float OldH = PlayerCombat->GetMaxHealth(), OldM = PlayerCombat->GetMaxMana();
	PlayerCombat->RefreshMaxima();
	const FRDHeroDef* H = FindHero(CurrentHero);
	TArray<FString> What;
	if (PlayerCombat->GetMaxHealth() > OldH + 0.5f) What.Add(FString::Printf(TEXT("%.0f hit points"), PlayerCombat->GetMaxHealth()));
	if (PlayerCombat->GetMaxMana() > OldM + 0.5f) What.Add(FString::Printf(TEXT("%.0f mana"), PlayerCombat->GetMaxMana()));
	// (her summons standing grow with her, each keeping its share of hit points; one of a summoning above the open tier is at
	// its summoning's tier already and does not change, nor is it counted (the PR review's find))
	int32 Grown = 0;
	if (SummonsGrow())
		for (ARDMonster* A : Allies)
			if (IsValid(A) && !A->IsDead() && !A->SummonSpell.IsNone())
			{
				float Hp = 0.f, Dm = 0.f; int32 St = 0; SummonStrength(A->SummonSpell, Hp, Dm, St);
				if (A->SetStrength(St, Hp, Dm)) ++Grown;
			}
	if (Grown > 0) What.Add(Grown == 1 ? FString(TEXT("your summon")) : FString::Printf(TEXT("your %d summons"), Grown));
	if (H && H->SpellPowerPerTier > 0.f) What.Add(FString::Printf(TEXT("%s +%.0f%%"), H->Name == TEXT("MartialArtist") ? TEXT("chi") : TEXT("spells"), (TierSpellMul() - 1.f) * 100.f));
	if (H && H->OwnWeaponPowerPerTier > 0.f) What.Add(FString::Printf(TEXT("%s +%.0f%%"), H->Name == TEXT("MartialArtist") ? TEXT("fists") : TEXT("your own weapons"), (TierOwnWeaponMul() - 1.f) * 100.f));
	if (What.Num() > 0) PlayerCombat->ShowMessage(FString::Printf(TEXT("Tier %d opens: you grow stronger (%s)"), Tier, *FString::Join(What, TEXT(", "))));
	UE_LOG(LogRDMistward6, Log, TEXT("RDGROW tier %d: %s %.0f hit points (x%.2f), %.0f mana (x%.2f), spells x%.2f, own weapons x%.2f, %d summons grown"), Tier, *CurrentHero.ToString(),
		PlayerCombat->GetMaxHealth(), TierHealthMul(), PlayerCombat->GetMaxMana(), TierManaMul(), TierSpellMul(), TierOwnWeaponMul(), Grown);
}

// ================================================================================================ the Rogue's stealth
float URDCombatComponent::GetStealthCost() const
{
	const FRDHeroDef* H = Generator && Generator->bStealth ? Generator->FindHero(Generator->CurrentHero) : nullptr;
	return H && H->DexEnergy > 0.f ? H->StealthCost : 0.f;
}

bool URDCombatComponent::IsStealthed() const { return GetWorld() && GetWorld()->GetTimeSeconds() < StealthUntil; }

float URDCombatComponent::GetStealthLeft() const { return GetWorld() ? FMath::Max(0.f, StealthUntil - GetWorld()->GetTimeSeconds()) : 0.f; }

void URDCombatComponent::SetDexEnergy(float Value) { DexEnergy = FMath::Clamp(Value, 0.f, MaxDexEnergy); }

bool URDCombatComponent::StartStealth()
{
	if (Generator && (Generator->IsMounted() || Generator->IsSwimming())) return false;
	const FRDHeroDef* H = Generator && Generator->bStealth && !bDead ? Generator->FindHero(Generator->CurrentHero) : nullptr;
	if (!H || H->DexEnergy <= 0.f || MaxDexEnergy <= 0.f || !GetOwner()) return false;
	if (IsStealthed()) { EndStealth(TEXT("ended")); return true; }        // (again while in it: out of it, no energy back)
	// (not in a swing: its blow would land with her hidden and keep her so (the PR review's find))
	if (IsAttacking()) return false;
	const float Now = GetWorld()->GetTimeSeconds();
	if (DexEnergy < H->StealthCost)
	{
		++StealthRefusals;
		if (Now - NoManaTime > 0.6f)
		{
			SetMessage(FString::Printf(TEXT("Not enough dexterity energy for stealth (%.0f of %.0f)"), FMath::FloorToFloat(DexEnergy), H->StealthCost));
			Generator->PlaySoundAt(TEXT("Player.NoMana"), GetOwner()->GetActorLocation());
		}
		NoManaTime = Now;
		return false;
	}
	DexEnergy -= H->StealthCost;
	StealthUntil = Now + H->StealthSeconds; bAmbushArmed = false; StealthEndReason.Reset();
	++StealthUses;
	// (her look: the Shadow Veil's dark aura round her while it lasts)
	const int32 Vi = Generator->Spells.IndexOfByPredicate([](const FRDSpellDef& S) { return S.Kind == ERDSpellKind::Veil; });
	if (Vi >= 0) SetAura(RD6StealthAura, &Generator->Spells[Vi], true);
	Generator->PlaySoundAt(TEXT("Player.Whoosh"), GetOwner()->GetActorLocation());
	SetMessage(FString::Printf(TEXT("You slip into the shadows: unseen for %.0f s (your first blow strikes %.0f%% harder)"), H->StealthSeconds, H->AmbushBonus * 100.f));
	UE_LOG(LogRDMistward6, Log, TEXT("RDSTEALTH on for %.0f s: energy %.0f of %.0f left"), H->StealthSeconds, DexEnergy, MaxDexEnergy);
	return true;
}

void URDCombatComponent::EndStealth(const FString& Why)
{
	const bool bWas = StealthUntil > -50.f && GetWorld() && GetWorld()->GetTimeSeconds() < StealthUntil + 0.05f;
	StealthUntil = -100.f;
	SetAura(RD6StealthAura, nullptr, false);
	if (bWas)
	{
		StealthEndReason = Why;
		if (Why == TEXT("time")) SetMessage(TEXT("You step out of the shadows"));
		UE_LOG(LogRDMistward6, Log, TEXT("RDSTEALTH off (%s)"), *Why);
	}
}

void URDCombatComponent::TickStealth(float Dt, float Now)
{
	if (MaxDexEnergy <= 0.f) return;
	if (StealthUntil > -50.f && Now >= StealthUntil) EndStealth(TEXT("time"));
	const FRDHeroDef* H = Generator ? Generator->FindHero(Generator->CurrentHero) : nullptr;
	if (H && DexEnergy < MaxDexEnergy && !IsStealthed()) DexEnergy = FMath::Min(MaxDexEnergy, DexEnergy + H->DexPerSecond * Dt);      // (none back while in it)
}

void URDCombatComponent::ResetStealth(bool bFill)
{
	StealthUntil = -100.f; bAmbushArmed = false; StealthTraps.Reset();
	SetAura(RD6StealthAura, nullptr, false);
	const FRDHeroDef* H = Generator && Generator->bStealth ? Generator->FindHero(Generator->CurrentHero) : nullptr;
	MaxDexEnergy = H ? H->DexEnergy : 0.f;
	DexEnergy = bFill ? MaxDexEnergy : FMath::Min(DexEnergy, MaxDexEnergy);
}

void URDCombatComponent::NoteStealthTrap(uint32 Key)
{
	bool bHad = false; StealthTraps.Add(Key, &bHad);
	if (!bHad) ++StealthTrapsPassed;
}

float URDCombatComponent::AmbushMul(int32 Index) const
{
	// (only while the ambush's own blow, bolt or spell goes off: a bolt shot earlier that bursts in that window, or the HUD,
	// gets nothing)
	if (!bAmbushArmed || !bAmbushApplying || Index != AttackIndex || !Generator) return 1.f;
	const FRDHeroDef* H = Generator->FindHero(Generator->CurrentHero);
	return H ? 1.f + H->AmbushBonus : 1.f;
}
