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
	auto Ok = [GameTier](const FRDItemDef& It)
	{
		if (It.Kind != ERDItemKind::Recipe) return false;
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
	bOk = false; return ERDItemKind::Food;
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
