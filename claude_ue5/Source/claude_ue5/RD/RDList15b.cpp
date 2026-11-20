// The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), its third phase: summons and the
// Summoner's hands. Item 4, "if the summoner summons another minion, it should replace a damaged minion; if there are no damaged
// minions or if there are maximum number of minions, the spell is refused" (read so she can still summon her first: below the cap a
// cast adds one; at the cap it takes the place of the most hurt; at the cap with none hurt it is refused before its mana is taken).
// Item 18, "the summoner should be able to pick from 5 different types of the appropriate Tier minions to summon. leave the current
// default creatures": each summoning's kinds (FRDSpellDef::SummonKinds, 934 summons), the one she chose kept in the save and carried;
// Enter (A) on the summoning in her hands steps to the next. Item 13, "summoner cannot unwield the dagger": her bare hands, an entry
// of her weapons (bUnarmed15, 934 hands), and Enter on the found weapon in her hands puts it away.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDMonster.h"
#include "RD/RDSection.h"
#include "RD/RDCombat.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList15b, Log, All);

// ================================================================================================ item 18: five kinds
FName URDCombatComponent::GetSummonKind15(FName Spell) const
{
	const FRDSpellDef* S = Generator ? Generator->Spells.FindByPredicate([Spell](const FRDSpellDef& D) { return D.Name == Spell; }) : nullptr;
	if (!S) return NAME_None;
	// (her choice while it is one of this map's kinds for it and the map has the kind; else the summoning's own)
	if (const FName* P = SummonPick15.Find(Spell); P && S->SummonKinds.Contains(*P)
		&& Generator->Monsters.ContainsByPredicate([P](const FRDMonsterDef& D) { return D.Name == *P && D.Mesh; })) return *P;
	return S->SummonKind;
}

bool URDCombatComponent::CycleSummonKind15(FName Spell, int32 Step)
{
	const FRDSpellDef* S = Generator ? Generator->Spells.FindByPredicate([Spell](const FRDSpellDef& D) { return D.Name == Spell; }) : nullptr;
	if (!S) return false;
	const TArray<FName> Ks = GetSummonKindsHere15(Spell);
	if (Ks.Num() < 2) { SetMessage(FString::Printf(TEXT("%s calls %s alone"), *Spell.ToString(), *Generator->KindTitle15(S->SummonKind))); return false; }
	const int32 At = FMath::Max(0, Ks.IndexOfByKey(GetSummonKind15(Spell)));
	const FName Next = Ks[((At + Step) % Ks.Num() + Ks.Num()) % Ks.Num()];
	SummonPick15.Add(Spell, Next);
	SetMessage(FString::Printf(TEXT("%s now calls %s  (%d of %d)"), *Spell.ToString(), *Generator->KindTitle15(Next), Ks.IndexOfByKey(Next) + 1, Ks.Num()));
	return true;
}

TArray<FName> URDCombatComponent::GetSummonKindsHere15(FName Spell) const
{
	// (the kinds this map has with a mesh: the cycle, the inventory's count and its list read the same ones (PR #95's review))
	TArray<FName> Ks;
	const FRDSpellDef* S = Generator ? Generator->Spells.FindByPredicate([Spell](const FRDSpellDef& D) { return D.Name == Spell; }) : nullptr;
	if (!S) return Ks;
	for (const FName& K : S->SummonKinds)
		if (Generator->Monsters.ContainsByPredicate([&K](const FRDMonsterDef& D) { return D.Name == K && D.Mesh; })) Ks.AddUnique(K);
	return Ks;
}

bool URDCombatComponent::SetSummonKind15(FName Spell, FName Kind)
{
	const FRDSpellDef* S = Generator ? Generator->Spells.FindByPredicate([Spell](const FRDSpellDef& D) { return D.Name == Spell; }) : nullptr;
	if (!S || !(S->SummonKinds.Contains(Kind) || S->SummonKind == Kind)) return false;
	SummonPick15.Add(Spell, Kind);
	return true;
}

FString ARDDungeonGenerator::StandingTitles15(FName Spell) const
{
	// (the kinds of a summoning's minions standing, each once; none standing: the kind she would call)
	TArray<FString> T;
	for (const ARDMonster* A : Allies)
		if (IsValid(A) && !A->IsDead() && A->SummonSpell == Spell) T.AddUnique(A->Title.IsEmpty() ? A->MonsterName.ToString() : A->Title);
	if (T.Num() > 0) return FString::Join(T, TEXT(", "));
	const FRDSpellDef* S = Spells.FindByPredicate([Spell](const FRDSpellDef& D) { return D.Name == Spell; });
	return S ? SummonTitleOf(*S) : Spell.ToString();
}

FString ARDDungeonGenerator::KindTitle15(FName Kind) const
{
	const FRDMonsterDef* D = Monsters.FindByPredicate([Kind](const FRDMonsterDef& M) { return M.Name == Kind; });
	return D && !D->Title.IsEmpty() ? D->Title : Kind.ToString();
}

// ================================================================================================ item 4: a hurt one replaced
ARDMonster* ARDDungeonGenerator::MostHurtSummon15(FName Spell) const
{
	ARDMonster* Best = nullptr; float BestShare = 0.999f;
	for (ARDMonster* A : Allies)
	{
		if (!IsValid(A) || A->IsDead() || A->SummonSpell != Spell || A->GetMaxHealth() <= 0.f) continue;
		const float Share = A->GetHealth() / A->GetMaxHealth();
		if (Share < BestShare) { BestShare = Share; Best = A; }
	}
	return Best;
}

void ARDDungeonGenerator::DismissAlly15(ARDMonster* A)
{
	if (!IsValid(A)) return;
	Allies.Remove(A);
	if (A->Section) A->Section->SpawnedMonsters.Remove(A);
	A->Destroy();
}

// ================================================================================================ item 13: her bare hands
int32 URDCombatComponent::GetUnarmedIndex15() const
{
	return Generator ? Generator->Weapons.IndexOfByPredicate([](const FRDWeaponDef& W) { return W.bUnarmed15; }) : INDEX_NONE;
}

bool URDCombatComponent::PutWeaponAway15()
{
	const int32 U = GetUnarmedIndex15();
	if (U < 0 || WeaponIndex == U || !Generator->Weapons.IsValidIndex(WeaponIndex)) return false;
	const FName Was = Generator->Weapons[WeaponIndex].Name;
	SelectWeapon(U);
	if (WeaponIndex != U) return false;
	SetMessage(FString::Printf(TEXT("You put the %s away: your hands are free"), *Was.ToString().ToLower()));
	return true;
}
