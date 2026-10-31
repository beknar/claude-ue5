// mistward_castle, the user's list of 2026-10-30 (docs/improvements3.txt; pipeline/unreal/875). Each rule a switch on the
// generator ("Mistward3" category), off on the other levels:
//   harvests       a monster that dies leaves its parts floating over it (a loot pile, bHarvest): an essence of the tiers up
//                  to its own, its family's part, now and then a material; a boss, a usurper and an arena won give more
//   recipes        the anvil offers a recipe once its tier is open, a scroll's only to a hero who reads its type
//   scrolls        a scroll read casts its spell once at no mana, through a spell weapon that stands after hers for the cast
//   gear           rings and the torch break down at an anvil too (bBreakAnyGear: RDGear.cpp, RDCombat.cpp's lists)
//   summons        the Summoner's: one of a kind at her side, as strong as a monster of its tier, Count of them at most
#include "RD/RDCombat.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDMonster.h"
#include "RD/RDMistward.h"
#include "RD/RDSection.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDMistward3, Log, All);

static const TCHAR* RDM3TypeName(ERDSpellType T) { return RDSpellTypeName(T); }

FString ARDDungeonGenerator::SummonTitleOf(const FRDSpellDef& S) const
{
	const int32 Mk = Monsters.IndexOfByPredicate([&S](const FRDMonsterDef& D) { return D.Name == S.SummonKind; });
	return Mk >= 0 && !Monsters[Mk].Title.IsEmpty() ? Monsters[Mk].Title : S.SummonKind.ToString();
}

// ================================================================================================ harvests
TArray<FName> ARDDungeonGenerator::HarvestOf(FName Kind, int32 Tier, bool bBig, int32 Roll) const
{
	TArray<FName> Out;
	const int32 T = FMath::Clamp(Tier, 1, FMath::Max(Essences.Num(), 1));
	// (each draw a hash of the session seed, the harvest's number and the draw's own salt: no stream of the play's)
	const uint32 H0 = HashCombine((uint32)SessionSeed ^ 0x4A2Bu, (uint32)Roll * 2654435761u + 17u);
	auto U = [H0](uint32 Salt) { return (float)(HashCombine(H0, Salt * 7919u + 3u) % 100003u) / 100003.f; };
	auto Pick = [H0](uint32 Salt, int32 N) { return (int32)(HashCombine(H0, Salt * 104729u + 11u) % (uint32)FMath::Max(N, 1)); };
	// (an essence of the tiers up to its own: its own tier's most of the time, else one of those below, evenly)
	const int32 NE = bBig ? FMath::Max(BossEssences, 1) : 1;
	for (int32 K = 0; K < NE && Essences.Num() > 0; ++K)
	{
		const float R = U(10 + K);
		int32 E = T - 1;
		if (T > 1 && R >= EssenceOwnTier) E = FMath::Clamp((int32)((R - EssenceOwnTier) / FMath::Max(1.f - EssenceOwnTier, 1e-3f) * (T - 1)), 0, T - 2);
		Out.Add(Essences[FMath::Clamp(E, 0, Essences.Num() - 1)]);
	}
	// (an ordinary kill: its family's part, and only where the table gives the family one in this tier (none else: the PR
	// review's find, a Dog of tier 1 gave Mutant Ichor); a big harvest (a boss's, an arena's): its family's first, then parts
	// of the tier it has not given yet (tier 1's are nearly all spiders: with its family alone the tier gave too little Mutant
	// Ichor for its Medium Healing Potion, 868's harvest step), any part of the tier once each has been given)
	const FRDMonsterDef* Def = Kind.IsNone() ? nullptr : Monsters.FindByPredicate([Kind](const FRDMonsterDef& D) { return D.Name == Kind; });
	TArray<FName> Fam, OfTier;
	for (const FRDHarvestPart& P : HarvestParts)
		if (P.Tiers.Num() == 0 || P.Tiers.Contains(T)) { OfTier.Add(P.Part); if (Def && P.Family == Def->SoundSet) Fam.Add(P.Part); }
	const int32 NP = bBig ? FMath::Max(BossParts, 0) : (U(20) < HarvestPartChance ? 1 : 0);
	TArray<FName> Given;
	for (int32 K = 0; K < NP; ++K)
	{
		TArray<FName> From;
		if (!bBig) From = Fam;
		else if (K == 0 && Fam.Num() > 0) From = Fam;
		else
		{
			for (const FName& P : OfTier) if (!Given.Contains(P)) From.Add(P);
			if (From.Num() == 0) From = OfTier;
		}
		if (From.Num() > 0) { const FName P = From[Pick(30 + K, From.Num())]; Out.Add(P); Given.AddUnique(P); }
	}
	// (now and then a material of any tier: hides, leathers, glues, oils)
	if (HarvestAny.Num() > 0 && U(40) < HarvestAnyChance) Out.Add(HarvestAny[Pick(41, HarvestAny.Num())]);
	return Out;
}

ARDLootPile* ARDDungeonGenerator::DropHarvest(const FVector& At, const TArray<FName>& Things, int32 Tier)
{
	if (Things.Num() == 0) return nullptr;
	TArray<float> W; W.Init(-1.f, Things.Num());
	ARDLootPile* P = DropLoot(At, Things, W);
	if (!P) return nullptr;
	P->bHers = false; P->bHarvest = true; P->Tier = Tier;
	if (HarvestTints.IsValidIndex(Tier - 1)) P->SetTint(HarvestTints[Tier - 1]);
	++Harvests;
	UE_LOG(LogRDMistward3, Log, TEXT("RDHARVEST tier %d: %s at (%.0f, %.0f)"), Tier, *FString::JoinBy(Things, TEXT(", "), [](const FName& N) { return N.ToString(); }), At.X, At.Y);
	return P;
}

void ARDDungeonGenerator::HarvestKill(ARDMonster* Monster, bool bBig)
{
	if (!Monster) return;
	DropHarvest(Monster->GetActorLocation(), HarvestOf(Monster->MonsterName, Monster->Tier, bBig, HarvestRolls++), FMath::Max(Monster->Tier, 1));
}

void URDCombatComponent::TakeHarvest(const TArray<FName>& Things)
{
	// ("You harvest: 2 faint essence, 1 mutant ichor")
	TMap<FName, int32> N; TArray<FName> Order;
	for (const FName& T : Things) { if (!N.Contains(T)) Order.Add(T); N.FindOrAdd(T)++; }
	TArray<FString> Got;
	for (const FName& T : Order) { AddItem(T, N[T]); Got.Add(FString::Printf(TEXT("%d %s"), N[T], *T.ToString().ToLower())); }
	++HarvestsTaken;
	SetMessage(TEXT("You harvest:  ") + FString::Join(Got, TEXT(", ")));
	InventoryCursor = FMath::Clamp(InventoryCursor, 0, FMath::Max(0, GetInventoryLines().Num() - 1));
	UE_LOG(LogRDMistward3, Log, TEXT("RDHARVEST taken: %s"), *FString::Join(Got, TEXT(", ")));
}

// ================================================================================================ the anvil's recipes by tier
int32 ARDDungeonGenerator::GetHighestOpenTier() const
{
	if (MaxTier <= 0) return 5;
	for (int32 T = MaxTier; T > 1; --T) if (IsTierOpen(T)) return T;
	return 1;
}

bool ARDDungeonGenerator::HeroReadsScroll(ERDSpellType Type) const
{
	const FRDHeroDef* H = FindHero(CurrentHero);
	return H && H->ScrollTypes.Contains(Type);
}

FString ARDDungeonGenerator::RecipeRefusal(const FRDRecipe& Rc) const
{
	if (!bRecipeTiers) return FString();
	const int32 Ix = FindItem(Rc.Item);
	if (Ix >= 0 && Items[Ix].Kind == ERDItemKind::Scroll)
	{
		const int32 Si = FindSpell(Items[Ix].Spell);
		if (Si >= 0 && !HeroReadsScroll(Spells[Si].Type))
			return FString::Printf(TEXT("The %s cannot read the %s (%s)"), *PlayerTitle.ToLower(), *Rc.Item.ToString().ToLower(), RDM3TypeName(Spells[Si].Type));
	}
	if (Rc.Tier > 0 && Rc.Tier > GetHighestOpenTier())
		return FString::Printf(TEXT("The %s is of tier %d: the anvil makes it once tier %d is open"), *Rc.Item.ToString().ToLower(), Rc.Tier, Rc.Tier);
	return FString();
}

// ================================================================================================ scrolls
int32 URDCombatComponent::GetScrollWeapon() const
{
	if (!Generator) return -1;
	for (int32 I = Generator->Weapons.Num() - 1; I >= 0; --I) if (Generator->Weapons[I].bScroll) return I;
	return -1;
}

bool URDCombatComponent::ReadScroll(FName Item)
{
	const int32 Ix = Generator && !bDead ? Generator->FindItem(Item) : -1;
	if (Ix < 0 || Generator->Items[Ix].Kind != ERDItemKind::Scroll || GetItemCount(Item) <= 0) return false;
	const int32 Si = Generator->FindSpell(Generator->Items[Ix].Spell);
	if (Si < 0) return false;
	const FRDSpellDef& S = Generator->Spells[Si];
	const FString Lb = Item.ToString().ToLower();
	if (!Generator->HeroReadsScroll(S.Type)) { SetMessage(FString::Printf(TEXT("The %s cannot read the %s (%s)"), *Generator->PlayerTitle.ToLower(), *Lb, RDM3TypeName(S.Type))); return false; }
	if (AttackTime >= 0.f || RollTime >= 0.f) { SetMessage(TEXT("Finish your move first")); return false; }
	// (said before the inventory closes: closed with nothing cast and nothing said looked like the key was lost (the PR review's find))
	if (bBlocking) { SetMessage(TEXT("Lower your shield first")); return false; }
	if (bCraftOpen) { SetMessage(TEXT("Step away from the anvil first")); return false; }
	// (the spell's weapon with her cast clips (as a tome's), at no mana; named as the spell, so its cooldown is the spell's)
	FRDWeaponDef W;
	if (!Generator->MakeSpellWeapon(Si, W)) { SetMessage(FString::Printf(TEXT("The %s cannot cast from the %s"), *Generator->PlayerTitle.ToLower(), *Lb)); return false; }
	W.ManaCost = 0.f; W.ManaShare = 0.f; W.bScroll = true; W.Slash = NAME_None; W.HolsterBone = NAME_None; W.OffHandHolsterBone = NAME_None;
	int32 Wi = GetScrollWeapon();
	if (Wi >= 0 && Bolts.ContainsByPredicate([Wi](const FBolt& B) { return B.Weapon == Wi; })) { SetMessage(TEXT("Your last scroll's spell is still on its way")); return false; }
	if (Wi < 0) { Generator->Weapons.Add(W); Wi = Generator->Weapons.Num() - 1; }
	else Generator->Weapons[Wi] = W;
	SyncWear();
	if (bInventoryOpen) SetInventoryOpen(false);
	// (refused (its cooldown, a summon she leads enough of, no monster for it): the scroll is kept; its weapon goes next tick)
	const float Said = MessageTime;
	if (!StartAttackWith(Wi))
	{
		if (MessageTime == Said) SetMessage(FString::Printf(TEXT("The %s does not take: try again"), *Lb));
		return false;
	}
	RemoveCarried(Item, 1);
	++ScrollsRead;
	SetMessage(FString::Printf(TEXT("You read the %s:  %s, no mana"), *Lb, *S.Name.ToString()));
	UE_LOG(LogRDMistward3, Log, TEXT("RDSCROLL %s read (%s; %d read)"), *Item.ToString(), *S.Name.ToString(), ScrollsRead);
	return true;
}

void URDCombatComponent::TickScrollWeapon()
{
	const int32 Wi = GetScrollWeapon();
	if (Wi < 0 || (AttackTime >= 0.f && AttackIndex == Wi)) return;
	if (Bolts.ContainsByPredicate([Wi](const FBolt& B) { return B.Weapon == Wi; })) return;
	DropWeaponAt(Wi);
}

void URDCombatComponent::DropWeaponAt(int32 Index)
{
	if (!Generator || !Generator->Weapons.IsValidIndex(Index)) return;
	if (AttackTime >= 0.f && AttackIndex == Index) EndAttack();
	Generator->Weapons.RemoveAt(Index);
	if (Wear.IsValidIndex(Index)) Wear.RemoveAt(Index);
	if (NextOf.IsValidIndex(Index)) NextOf.RemoveAt(Index);
	Bolts.RemoveAll([Index](const FBolt& B) { return B.Weapon == Index; });
	for (FBolt& B : Bolts) if (B.Weapon > Index) --B.Weapon;
	for (int32& P : PendingBreak) if (P > Index) --P;
	PendingBreak.Remove(Index);
	if (AttackIndex > Index) --AttackIndex;
	if (WeaponIndex > Index) --WeaponIndex;
}

// ================================================================================================ the Summoner's summons
void URDCombatComponent::UpdateManaShares()
{
	if (!Generator) return;
	for (FRDWeaponDef& W : Generator->Weapons) if (W.ManaShare > 0.f) W.ManaCost = FMath::RoundToFloat(FMath::Max(MaxMana, 1.f) * W.ManaShare);
}

ARDMonster* ARDDungeonGenerator::SummonKindAlly(FName Kind, FVector At, FName Spell)
{
	const int32 K = Monsters.IndexOfByPredicate([Kind](const FRDMonsterDef& D) { return D.Name == Kind && D.Mesh; });
	if (K < 0) { UE_LOG(LogRDMistward3, Warning, TEXT("RDSUMMON no monster kind %s"), *Kind.ToString()); return nullptr; }
	const int32 T = FMath::Clamp(Monsters[K].Tier > 0 ? Monsters[K].Tier : 1, 1, 5);
	const FString Title = Monsters[K].Title.IsEmpty() ? Kind.ToString() : Monsters[K].Title;
	ARDMonster* M = SpawnMonsterKind(K, At, T, 1.f, 1.f, 1.f, Title);
	if (!M) return nullptr;
	// (hers: out of its set's monsters (her blows and spells pass it by), among her allies until it falls)
	if (M->Section) M->Section->SpawnedMonsters.Remove(M);
	M->BecomeAlly(0.f, M->GetMaxHealth(), M->GetDamage());
	M->SummonSpell = Spell;
	Allies.Add(M);
	UE_LOG(LogRDMistward3, Log, TEXT("RDSUMMON %s for %s: tier %d, %.0f hit points, %.0f damage (%d of them)"), *Kind.ToString(), *Spell.ToString(), T, M->GetMaxHealth(), M->GetDamage(), CountSummoned(Spell));
	return M;
}

int32 ARDDungeonGenerator::DebugOpenTiers(int32 UpTo, bool bEncounters)
{
	int32 N = 0;
	for (int32 T = 2; T <= FMath::Min(UpTo, MaxTier); ++T)
	{
		if (TiersOpened.Contains(T)) continue;
		TiersOpened.Add(T); ++N;
		if (bEncounters) OnTierOpened(T);
		UE_LOG(LogRDMistward3, Log, TEXT("RDTIER tier %d opened by the debug shortcut"), T);
	}
	if (N > 0)
	{
		RefreshSeals();
		TierNotice = FString::Printf(TEXT("TIERS 2 TO %d ARE OPEN"), FMath::Min(UpTo, MaxTier)); TierNoticeTime = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	}
	return N;
}

int32 ARDDungeonGenerator::CountSummoned(FName Spell) const
{
	int32 N = 0;
	for (const ARDMonster* A : Allies) if (IsValid(A) && !A->IsDead() && A->SummonSpell == Spell) ++N;
	return N;
}
