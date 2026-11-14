// The rebalance to tier 25 (the user's list of 2026-11-08b, docs/improvements9.txt, its fifth phase), carried to tier 30 by the
// list of 2026-11-12's sixth phase: the game's tiers 1-30 over the chain of dungeons (Mistward Castle 1-5, Vel Morrath 6-10,
// The War Engine 11-15, the Sewers 16-20, Kethrys Spire 21-25, Heaven 26-30), each level's own five tiers mapped into them
// (DungeonTierBase, DungeonTierCap; the chain's "|base|cap", 905):
//   GlobalTier       a level's tier in the game's tiers (the monsters' strength, the loot's tiers)
//   GameGlobalTier   the deepest game's tier opened in any dungeon (the town's prices, the hero's growth in the town and the wilds)
//   GrowthTier       the tier the hero grows by (at least the deepest she has opened anywhere: no fall back to tier 1 in a new
//                    dungeon)
//   GrantLaterWeapons  the Summoner's, the Rogue's and the Martial Artist's abilities earned in the later dungeons (one each)
#include "RD/RDDungeonGenerator.h"
#include "RD/RDCombat.h"
#include "RD/RDGameInstance.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDTier25, Log, All);

int32 ARDDungeonGenerator::GlobalTier(int32 Tier) const
{
	return MapTier(Tier, DungeonTierBase, DungeonTierCap);
}

bool ARDDungeonGenerator::MeanWildFactors(float& Health, float& Damage, int32 Tier) const
{
	float H = 0.f, D = 0.f; int32 N = 0;
	for (const FRDMonsterDef& M : Monsters)
		if (M.Mesh && M.WildTierMax > 0 && Tier >= M.WildTierMin && Tier <= M.WildTierMax) { H += M.HealthFactor; D += M.DamageFactor; ++N; }
	if (N == 0) return false;
	Health = H > 0.f ? H / N : 1.f; Damage = D > 0.f ? D / N : 1.f;
	return true;
}

int32 ARDDungeonGenerator::ChainIndexHere() const
{
	const int32 I = ChainIndexOfKey(DungeonKey);
	return I >= 0 ? I : (DungeonKey.IsEmpty() ? 0 : -1);
}

int32 ARDDungeonGenerator::GameGlobalTier() const
{
	if (CachedGameTierFrame == GFrameCounter && CachedGameTierOpened == TiersOpened.Num()) return CachedGameTier;
	int32 T = 1;
	if (!bTown) for (const int32 O : TiersOpened) T = FMath::Max(T, GlobalTier(O));
	if (const URDGameInstance* GI = URDGameInstance::Of(this))
	{
		// (every dungeon of the chain: its tiers opened, in the game's tiers by the chain's base and cap)
		const TArray<FRDChainLink>& C = Chain();
		for (const FRDChainLink& L : C)
		{
			const FRDDungeonSave* Ds = L.Key.IsEmpty() ? nullptr : GI->Dungeons.Find(L.Key);
			const TArray<int32>* Ts = L.Key.IsEmpty() ? &GI->CastleTiers : (Ds ? &Ds->Tiers : nullptr);
			if (!Ts) continue;
			for (const int32 O : *Ts) T = FMath::Max(T, MapTier(O, L.TierBase, L.TierCap));
		}
		// (no chain (an older level): the dungeons' own tiers, as before)
		if (C.Num() == 0)
		{
			for (const int32 O : GI->CastleTiers) T = FMath::Max(T, O);
			for (const TPair<FString, FRDDungeonSave>& D : GI->Dungeons) for (const int32 O : D.Value.Tiers) T = FMath::Max(T, O);
		}
	}
	// (the town's own tiers are the castle's)
	if (bTown) for (const int32 O : TiersOpened) T = FMath::Max(T, O);
	CachedGameTier = FMath::Clamp(T, 1, 99); CachedGameTierFrame = GFrameCounter; CachedGameTierOpened = TiersOpened.Num();
	return CachedGameTier;
}

int32 ARDDungeonGenerator::GrowthTier() const
{
	// (the list of 2026-11-11: rd.Tier's, while it is set)
	if (const int32 Ct = ConsoleTierNow(); Ct > 0) return Ct;
	return FMath::Max(bTown ? 1 : GlobalTier(GetOpenTier()), GameGlobalTier());
}

bool ARDDungeonGenerator::HasForcedLoot(FIntPoint Section, int32 Index) const
{
	return ForcedLoot.Contains(FIntVector(Section.X, Section.Y, Index));
}

int32 ARDDungeonGenerator::GrantLaterWeapons(bool bAnnounce)
{
	const FRDHeroDef* H = FindHero(CurrentHero);
	if (!H || H->LaterWeapons.Num() == 0) return 0;
	TArray<FRDWeaponDef> Earned; StartWeaponsOf(*H, Earned);
	int32 Added = 0;
	for (const FRDWeaponDef& W : H->LaterWeapons)
	{
		auto Same = [&W](const FRDWeaponDef& X) { return X.Name == W.Name; };
		if (!Earned.ContainsByPredicate(Same) || Weapons.ContainsByPredicate(Same)) continue;
		Weapons.Add(W); ++Added;
		UE_LOG(LogRDTier25, Log, TEXT("RDTIER25 %s earned %s"), *CurrentHero.ToString(), *W.Name.ToString());
		if (bAnnounce && PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("A new ability: %s"), *W.Name.ToString()));
	}
	if (Added > 0 && PlayerCombat) { PlayerCombat->SyncWear(); PlayerCombat->UpdateManaShares(); }
	return Added;
}
