// The user's list of 2026-11-16 (docs/improvements14.txt; the plan docs/improvements14_plan.md), its sixth phase: "recipes can be
// found to make more advanced food, more advanced potions, more advanced scrolls" (item 4). A recipe item teaches a recipe that is
// refused until it is read; the advanced potions' and foods' buffs. Behind the generator's bRecipes14 (928).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDCombat.h"
#include "RD/RDGameInstance.h"
#include "RD/RDWild.h"

bool ARDDungeonGenerator::IsLockedRecipe14(FName Item) const
{
	if (!bRecipes14) return false;
	if (TaughtRecipesOf14 != Items.Num())
	{
		TaughtRecipes14.Reset();
		for (const FRDItemDef& It : Items) if (It.Kind == ERDItemKind::Recipe && !It.Teaches.IsNone()) TaughtRecipes14.Add(It.Teaches);
		TaughtRecipesOf14 = Items.Num();
	}
	return TaughtRecipes14.Contains(Item);
}

bool ARDDungeonGenerator::KnowsRecipe14(FName Item) const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	return GI && GI->KnownRecipes.Contains(Item);
}

bool ARDDungeonGenerator::LearnRecipe14(FName Item)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || Item.IsNone() || GI->KnownRecipes.Contains(Item)) return false;
	GI->KnownRecipes.Add(Item);
	return true;
}

TArray<FName> ARDDungeonGenerator::GetKnownRecipes14() const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	return GI ? GI->KnownRecipes : TArray<FName>();
}

void ARDDungeonGenerator::ForgetRecipes14()
{
	if (URDGameInstance* GI = URDGameInstance::Of(this)) GI->KnownRecipes.Reset();
}

FName ARDDungeonGenerator::RecipeItemFor14(FName Item) const
{
	for (const FRDItemDef& It : Items) if (It.Kind == ERDItemKind::Recipe && It.Teaches == Item) return It.Name;
	return NAME_None;
}

FName ARDDungeonGenerator::RecipeOfTier14(int32 GameTier, FRandomStream& R) const
{
	// (a recipe item whose lowest tier is the game's tier or below, by the items' weights)
	float Sum = 0.f;
	// (the list of 2026-11-22's caves: the caves' tablets are drawn in a cave alone (CaveTablet16); out of the sums here)
	auto Ok = [this, GameTier](const FRDItemDef& It)
	{
		if (It.Kind != ERDItemKind::Recipe || CaveItems16.Contains(It.Name)) return false;
		int32 Lo = MAX_int32; for (const int32 T : It.Tiers) Lo = FMath::Min(Lo, T);
		return It.Tiers.Num() == 0 || Lo <= GameTier;
	};
	for (const FRDItemDef& It : Items) if (Ok(It)) Sum += FMath::Max(It.Weight, 0.1f);
	if (Sum <= 0.f) return NAME_None;
	float U = R.FRand() * Sum;
	FName Got;
	for (const FRDItemDef& It : Items) { if (!Ok(It)) continue; Got = It.Name; U -= FMath::Max(It.Weight, 0.1f); if (U < 0.f) break; }
	return Got;
}

// ================================================================================================ the buffs
// (each a timed effect on her, in the Effects she has (carried between the levels with them, RDCarry.cpp): speed as a speed potion's,
// regeneration as food's, and two of their own kinds: blows on her taken less (ERDItemKind::Armour) and her blows more (Weapon))
static ERDItemKind RDBuffKind14(FName B, bool& bOk)
{
	bOk = true;
	if (B == TEXT("resist")) return ERDItemKind::Armour;
	if (B == TEXT("might")) return ERDItemKind::Weapon;
	if (B == TEXT("speed")) return ERDItemKind::Speed;
	if (B == TEXT("regen")) return ERDItemKind::Food;
	if (B == TEXT("warm")) return ERDItemKind::Warmth;          // (the list of 2026-11-20's seventeenth phase)
	if (B == TEXT("cool")) return ERDItemKind::Cooling;
	if (B == TEXT("darksight")) return ERDItemKind::Darksight;          // (the list of 2026-11-22's caves)
	if (B == TEXT("poisonres")) return ERDItemKind::PoisonGuard;
	if (B == TEXT("oil")) return ERDItemKind::LampOil;
	bOk = false; return ERDItemKind::Food;
}

FString URDCombatComponent::BuffWords15(FName Kind, float Amount, float MaxHealth)
{
	// (what a buff does, in words: the item's text, the message on using it (PR #109's review: four chains of these kept apart))
	const float P = Amount * 100.f;
	if (Kind == TEXT("resist")) return FString::Printf(TEXT("blows on you %.0f%% less"), P);
	if (Kind == TEXT("might")) return FString::Printf(TEXT("your blows %.0f%% more"), P);
	if (Kind == TEXT("speed")) return FString::Printf(TEXT("you move %.0f%% faster"), P);
	if (Kind == TEXT("warm")) return FString::Printf(TEXT("the cold comes on %.0f%% slower"), P);
	if (Kind == TEXT("cool")) return FString::Printf(TEXT("the heat comes on %.0f%% slower"), P);
	if (Kind == TEXT("darksight")) return FString::Printf(TEXT("you see %.0f m without a torch"), Amount);
	if (Kind == TEXT("poisonres")) return FString::Printf(TEXT("poison hurts you %.0f%% less"), P);
	if (Kind == TEXT("oil")) return FString::Printf(TEXT("your torch and ankh burn %.0f times as long"), 1.f + Amount);
	return FString::Printf(TEXT("%.1f HP a second"), Amount * MaxHealth);
}

FString URDCombatComponent::EffectWords15(const FEffect& E, float MaxHealth, bool bChip)
{
	// (an effect on her: the status panel's chip (short, capitals) or the inventory's line)
	const float L = FMath::CeilToFloat(E.Left), P = E.Amount * 100.f;
	switch (E.Kind)
	{
	case ERDItemKind::Speed: return bChip ? FString::Printf(TEXT("SPEED +%.0f%%  %.0fs"), P, L) : FString::Printf(TEXT("Speed +%.0f%%: %.0f s left"), P, L);
	case ERDItemKind::Armour: return bChip ? FString::Printf(TEXT("RESIST +%.0f%%  %.0fs"), P, L) : FString::Printf(TEXT("Blows on you %.0f%% less: %.0f s left"), P, L);
	case ERDItemKind::Weapon: return bChip ? FString::Printf(TEXT("MIGHT +%.0f%%  %.0fs"), P, L) : FString::Printf(TEXT("Your blows %.0f%% more: %.0f s left"), P, L);
	case ERDItemKind::Warmth: return bChip ? FString::Printf(TEXT("WARM %.0f%%  %.0fs"), P, L) : FString::Printf(TEXT("Warm: the cold %.0f%% slower: %.0f s left"), P, L);
	case ERDItemKind::Cooling: return bChip ? FString::Printf(TEXT("COOL %.0f%%  %.0fs"), P, L) : FString::Printf(TEXT("Cool: the heat %.0f%% slower: %.0f s left"), P, L);
	case ERDItemKind::Darksight: return bChip ? FString::Printf(TEXT("DARKSIGHT %.0fm  %.0fs"), E.Amount, L) : FString::Printf(TEXT("Darksight: you see %.0f m without a torch: %.0f s left"), E.Amount, L);
	case ERDItemKind::PoisonGuard: return bChip ? FString::Printf(TEXT("ANTIVENOM %.0f%%  %.0fs"), P, L) : FString::Printf(TEXT("Poison hurts you %.0f%% less: %.0f s left"), P, L);
	case ERDItemKind::LampOil: return bChip ? FString::Printf(TEXT("OIL x%.0f  %.0fs"), 1.f + E.Amount, L) : FString::Printf(TEXT("Oiled: your torch and ankh burn %.0f times as long: %.0f s left"), 1.f + E.Amount, L);
	default: return bChip ? FString::Printf(TEXT("REGEN +%.1f/s  %.0fs"), E.Amount * MaxHealth, L) : FString::Printf(TEXT("Regenerating %.1f HP/s: %.0f s left"), E.Amount * MaxHealth, L);
	}
}

FName URDCombatComponent::EffectIcon15(const FEffect& E) const
{
	// (the chip's picture: the kind's own, a warm or cool buff its meal's (PR #109's review: they fell to the regeneration's))
	switch (E.Kind)
	{
	case ERDItemKind::Speed: return TEXT("chip_speed");
	case ERDItemKind::Armour: return TEXT("elixir_ironhide");
	case ERDItemKind::Weapon: return TEXT("elixir_might");
	case ERDItemKind::Warmth: case ERDItemKind::Cooling: case ERDItemKind::Darksight: case ERDItemKind::PoisonGuard: case ERDItemKind::LampOil:
		if (Generator) { const int32 Ix = Generator->FindItem(E.Item); if (Ix >= 0 && !Generator->Items[Ix].Icon.IsNone()) return Generator->Items[Ix].Icon; }
		return TEXT("chip_regen");
	default: return TEXT("chip_regen");
	}
}

bool URDCombatComponent::AddBuff14(const FRDItemDef& It)
{
	if (It.BuffKind.IsNone() || It.BuffAmount <= 0.f || It.BuffSeconds <= 0.f) return false;
	bool bOk = false; const ERDItemKind K = RDBuffKind14(It.BuffKind, bOk);
	if (!bOk) return false;
	// (the same item's buff again renews it, it does not stack; a food's own regeneration is not its buff)
	if (!(K == ERDItemKind::Food && It.Kind == ERDItemKind::Food)) Effects.RemoveAll([&It, K](const FEffect& E) { return E.Kind == K && E.Item == It.Name; });
	Effects.Add({ K, It.BuffAmount, It.BuffSeconds, It.Name });
	if (K == ERDItemKind::Speed) UpdateWalkSpeed();
	return true;
}

float URDCombatComponent::GetResistBuff14() const
{
	// (the strongest: two elixirs of the same do not add up)
	float B = 0.f;
	for (const FEffect& E : Effects) if (E.Kind == ERDItemKind::Armour) B = FMath::Max(B, E.Amount);
	return FMath::Min(B, 0.5f);
}

float URDCombatComponent::GetMightBuff14() const
{
	float B = 0.f;
	for (const FEffect& E : Effects) if (E.Kind == ERDItemKind::Weapon) B = FMath::Max(B, E.Amount);
	return FMath::Min(B, 1.f);
}

void ARDDungeonGenerator::ResolveWildLoot14(TArray<FString>& Lines, const FVector& At, int64 Key) const
{
	if (!bRecipes14 || !IsWildReady()) return;
	for (FString& L : Lines)
		if (L.StartsWith(TEXT("@recipe")))
		{
			FRandomStream Rr((int32)HashCombine(GetTypeHash(Key), 0x4EC1u ^ (uint32)Wild->Seed));
			const FName Got = RecipeOfTier14(FMath::Clamp(Wild->TierAt(At.X / 100.0, At.Y / 100.0), 1, GameTierMax), Rr);
			FString Rest; L.Split(TEXT("|"), nullptr, &Rest);
			L = Got.IsNone() ? FString() : Got.ToString() + TEXT("|") + Rest;
		}
}

FString ARDDungeonGenerator::GetWildLootResolved14(const FString& Loot, FVector At, int64 Key) const
{
	TArray<FString> Lines; Loot.ParseIntoArray(Lines, TEXT(";"), true);
	ResolveWildLoot14(Lines, At, Key);
	return FString::Join(Lines, TEXT(";"));
}

FString ARDDungeonGenerator::StationPlace14(const FName& St)
{
	return St == TEXT("Oven") ? FString(TEXT("an oven")) : St == TEXT("Alchemist") ? FString(TEXT("an alchemist's table"))
	     : St == TEXT("Librarian") ? FString(TEXT("a librarian's table")) : St == TEXT("Forge") ? FString(TEXT("a forge")) : FString(TEXT("an anvil"));
}

FString ARDDungeonGenerator::GetWildBoxLoot14(int64 Key) const
{
	for (const auto& Kv : WildChunks)
		if (const ARDWildChunk* C = Kv.Value; IsValid(C))
			for (const ARDWildChunk::FDoor& D : C->Doors) if (D.bBox && D.Key == Key) return D.Loot;
	return FString();
}
