// The user's list of 2026-11-26 (docs/improvements17.txt; the plan docs/improvements17_plan.md), its third phase: the square's stands.
//   "The town squares in every city need 3x more stands and shops, each one different in what they offer. The town square shops and stands
//   need to offer items that are of the same Tier that the town is in."
//   - Every city's square has 12 stands (it had 4, and Heaven none): the old four where they stood, eight more at places on the square kept
//     clear of everything already planned there, Heaven's twelve its own kiosks and carts. Each is a trade of its own (twelve, none shared on
//     a square), worked by a keeper behind it; F at the stand (or its keeper) opens its store.
//   - A stand offers its trade's things of the town's tier (Brokenspire 1, Vel Morrath 5, Ashenreach 10, Graymourne 15, Kethrys Spire 20,
//     Heaven 25: the roads' chain, one table by the town's name so the home town has its tier before the wilds are made): each thing's band
//     of five tiers holding the town's, or the nearest band below that holds any; only what her hero can use (her fits, her weights, her
//     spells, her scrolls), or, if none of the trade fits her, all of it.
//   - Prices are the town's as they were (`PriceOf`: gear by its own tier, used-up things by the game's): one price everywhere, so nothing
//     bought at one stand sells dearer at another.
//   - The draws: every new stand's mesh and every stand's trade come from a hash of the town's seed, never the plan's streams (the old four
//     stands still draw their meshes from step 1's, as before); rd.Stalls17 0 plans the town as before.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "RD/RDCombat.h"
#include "HAL/IConsoleManager.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList17b, Log, All);

namespace
{
	// (RDTownPlan.cpp's four ways, file-local there)
	const FIntPoint RDS17Dir4[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };
	TAutoConsoleVariable<int32> CVarRDStalls17(TEXT("rd.Stalls17"), 1, TEXT("The squares' twelve stands with their trades (1, the list of 2026-11-26) or the four stalls of before (0); read when a town is planned"));

	struct FRDTrade17 { const TCHAR* Name; const TCHAR* Modern; const TCHAR* Body; };
	const FRDTrade17 RDTrades17[12] = {
		{ TEXT("The weaponsmith's stand"), TEXT("The sporting goods kiosk"), TEXT("Blades on a cloth, hafts in a barrel, a whetstone turning.") },
		{ TEXT("The armourer's stand"), TEXT("The outdoor outfitter's cart"), TEXT("Mail on a frame, plates on a rail, a smell of oil and leather.") },
		{ TEXT("The shieldmaker's stand"), TEXT("The safety gear kiosk"), TEXT("Shields leaning in rows, painted and plain, a few still unfinished.") },
		{ TEXT("The jeweller's stand"), TEXT("The jeweller's kiosk"), TEXT("Rings on velvet under a glass lid; the jeweller watches your hands.") },
		{ TEXT("The potion seller's stand"), TEXT("The pharmacy kiosk"), TEXT("Little bottles in racks, red, blue and green, each with a wax seal.") },
		{ TEXT("The food stall"), TEXT("The food truck"), TEXT("Bread, cheese and something on a griddle; the smell alone draws a crowd.") },
		{ TEXT("The scribe's stand"), TEXT("The print shop kiosk"), TEXT("Scrolls tied with string, a pot of ink, a scribe who never looks up.") },
		{ TEXT("The bookseller's stand"), TEXT("The bookshop's cart"), TEXT("Old tomes stacked high, a few chained to the table.") },
		{ TEXT("The herbalist's stand"), TEXT("The herbalist's kiosk"), TEXT("Bundles of herbs hung to dry, jars of powders and roots.") },
		{ TEXT("The tinker's stand"), TEXT("The hardware cart"), TEXT("Rivets, straps, files and glue: whatever mends what you broke.") },
		{ TEXT("The chandler's stand"), TEXT("The electronics kiosk"), TEXT("Torches, lamps and oil, and recipes copied fair for a coin.") },
		{ TEXT("The enchanter's stand"), TEXT("The novelty kiosk"), TEXT("Strange edges for strange blades, sealed in little boxes.") },
	};
}

bool RDStalls17On() { return CVarRDStalls17.GetValueOnGameThread() != 0; }

// ================================================================================================ the town's tier
int32 ARDDungeonGenerator::TownTierOf17(const FString& Town)
{
	// (the roads' chain, FRDWildWorld::MakeTierChain: the tier at each city)
	static const TPair<const TCHAR*, int32> T[] = { { TEXT("Brokenspire"), 1 }, { TEXT("Vel Morrath"), 5 }, { TEXT("Ashenreach"), 10 }, { TEXT("Graymourne"), 15 },
		{ TEXT("Kethrys Spire"), 20 }, { TEXT("Heaven"), 25 } };
	for (const auto& P : T) if (Town.Equals(P.Key, ESearchCase::IgnoreCase)) return P.Value;
	return 0;
}

int32 ARDDungeonGenerator::TownTier17() const
{
	const int32 T = TownTierOf17(TownName.IsEmpty() ? FString(TEXT("Brokenspire")) : TownName);
	return T > 0 ? T : GetGameTier();
}

// ================================================================================================ what each trade sells
static bool RDS17Forged(ERDItemKind K)
{
	return K == ERDItemKind::Weapon || K == ERDItemKind::Armour || K == ERDItemKind::Shield || K == ERDItemKind::Repair || K == ERDItemKind::Ring || K == ERDItemKind::Slash
		|| K == ERDItemKind::Component || K == ERDItemKind::Torch || K == ERDItemKind::Light || K == ERDItemKind::Teleport || K == ERDItemKind::Key || K == ERDItemKind::Token;
}

bool ARDDungeonGenerator::IsReagent17(FName Part) const
{
	// (a material is a reagent when anything brewed, cooked or written is made of it (potions, meals, scrolls, the climate's and the
	// caves' brews: whatever is not forged), else a crafting material; the set made once per item and recipe table)
	if (Reagents17N != Items.Num() * 100003 + Recipes.Num())
	{
		Reagents17.Reset();
		for (const FRDRecipe& R : Recipes)
		{
			const int32 Ix = FindItem(R.Item);
			if (Ix < 0 || RDS17Forged(Items[Ix].Kind)) continue;
			for (const FRDRecipePart& P : R.Parts) for (const FName& N : P.AnyOf) Reagents17.Add(N);
		}
		Reagents17N = Items.Num() * 100003 + Recipes.Num();
	}
	return Reagents17.Contains(Part);
}

bool ARDDungeonGenerator::StallSells17(int32 Trade, const FRDItemDef& It) const
{
	switch (Trade)
	{
	case 0: return It.Kind == ERDItemKind::Weapon;
	case 1: return It.Kind == ERDItemKind::Armour;
	case 2: return It.Kind == ERDItemKind::Shield;
	case 3: return It.Kind == ERDItemKind::Ring && It.Weight > 0.f;          // (the named rings (weight 0) are found, never sold)
	case 4: return It.Kind == ERDItemKind::Healing || It.Kind == ERDItemKind::Mana || It.Kind == ERDItemKind::Speed;
	case 5: return It.Kind == ERDItemKind::Food;
	case 6: return It.Kind == ERDItemKind::Scroll;
	case 7: return It.Kind == ERDItemKind::Tome;
	case 8: return It.Kind == ERDItemKind::Component && IsReagent17(It.Name);
	case 9: return It.Kind == ERDItemKind::Repair || (It.Kind == ERDItemKind::Component && !IsReagent17(It.Name));
	case 10: return It.Kind == ERDItemKind::Torch || It.Kind == ERDItemKind::Recipe;
	case 11: return It.Kind == ERDItemKind::Slash;
	default: return false;
	}
}

bool ARDDungeonGenerator::StallFits17(const FRDItemDef& It) const
{
	const FRDHeroDef* H = FindHero(CurrentHero);
	switch (It.Kind)
	{
	case ERDItemKind::Weapon: case ERDItemKind::Shield:
		return It.WeaponFits.ContainsByPredicate([this](const FRDWeaponFit& F) { return F.Hero == CurrentHero; });
	case ERDItemKind::Armour: return ArmourRefusal(It, It.Name.ToString()).IsEmpty();
	case ERDItemKind::Tome:
	{
		if (const FRDSecondaryDef* Ad = FindSecondary(It.Spell); Ad && Ad->Slot > 0) return Ad->Hero == CurrentHero && !(PlayerCombat && PlayerCombat->GetSecondaryRank(It.Spell) > 0);
		const int32 Si = FindSpell(It.Spell);
		return Si >= 0 && HeroCanLearnSpell(Spells[Si]) && !(PlayerCombat && PlayerCombat->KnowsSpell(It.Spell));
	}
	case ERDItemKind::Scroll: { const int32 Si = FindSpell(It.Spell); return H && H->ScrollTypes.Num() > 0 && Si >= 0 && HeroReadsScroll(Spells[Si].Type); }
	case ERDItemKind::Recipe:
	{
		if (!bRecipes14 || KnowsRecipe14(It.Teaches)) return false;
		const int32 Tt = FindItem(It.Teaches);
		const int32 Si = Tt >= 0 && Items[Tt].Kind == ERDItemKind::Scroll ? FindSpell(Items[Tt].Spell) : -1;
		return !(Tt >= 0 && Items[Tt].Kind == ERDItemKind::Scroll && (Si < 0 || !HeroReadsScroll(Spells[Si].Type)));
	}
	default: return true;
	}
}

// (an item's highest tier at or under T (0: none); an item of no tiers is of every tier)
static int32 RDS17TierAt(const FRDItemDef& It, int32 T)
{
	if (It.Tiers.Num() == 0) return T;
	int32 Best = 0; for (const int32 X : It.Tiers) if (X <= T) Best = FMath::Max(Best, X);
	return Best;
}

TArray<FName> ARDDungeonGenerator::StallStock17(int32 Trade, bool* bAllFit) const
{
	const int32 Tt = TownTier17();
	TArray<const FRDItemDef*> Pool;
	for (const FRDItemDef& It : Items)
	{
		if (!StallSells17(Trade, It) || !CaveItemAllowed16(It) || PriceOf(It.Name) <= 0) continue;
		if (bRecipes14 && IsLockedRecipe14(It.Name)) continue;          // (what only a found recipe makes is not sold)
		Pool.Add(&It);
	}
	// (the town's own tier, else the nearest tier below that the trade holds any of: an item of the band copies (910's potions, food and
	// scrolls) is of each tier it lists)
	int32 Want = 0;
	for (const FRDItemDef* It : Pool) Want = FMath::Max(Want, RDS17TierAt(*It, Tt));
	TArray<const FRDItemDef*> Band;
	if (Want > 0) for (const FRDItemDef* It : Pool) if (RDS17TierAt(*It, Tt) == Want) Band.Add(It);
	TArray<const FRDItemDef*> Fit = Band.FilterByPredicate([this](const FRDItemDef* It) { return StallFits17(*It); });
	if (bAllFit) *bAllFit = Fit.Num() > 0;
	TArray<const FRDItemDef*>& Use = Fit.Num() > 0 ? Fit : Band;
	// (by kind, then the cheapest first: the panel scrolls (a cap at 16 dearest first left the potion seller without its small potions))
	TMap<const FRDItemDef*, int32> Price; for (const FRDItemDef* It : Use) Price.Add(It, PriceOf(It->Name));
	Use.Sort([&Price](const FRDItemDef& A, const FRDItemDef& B) { return A.Kind != B.Kind ? (uint8)A.Kind < (uint8)B.Kind : Price[&A] < Price[&B]; });
	TArray<FName> Out;
	for (const FRDItemDef* It : Use) Out.Add(HeavenGood22(It->Name));
	return Out;
}

FString ARDDungeonGenerator::StallName17(int32 Trade, bool bModern)
{
	return Trade >= 0 && Trade < 12 ? FString(bModern ? RDTrades17[Trade].Modern : RDTrades17[Trade].Name) : FString();
}

FString ARDDungeonGenerator::StallBody17(int32 Trade)
{
	return Trade >= 0 && Trade < 12 ? FString(RDTrades17[Trade].Body) : FString();
}

int32 ARDDungeonGenerator::StallAt17(const FVector& At, float R, FVector* Where) const
{
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S) return -1;
	int32 Best = -1; float Bd = R;
	for (const ARDSection::FTownSpot& Sp : S->TownSpots)
	{
		if (Sp.Kind != TS_Stall || Sp.Bld < 0) continue;
		const float D = FVector::Dist2D(Sp.At, At);
		if (D < Bd) { Bd = D; Best = Sp.Bld & 15; if (Where) *Where = Sp.At; }
	}
	return Best;
}

// ================================================================================================ the plan's stands
void ARDSection::PlanStalls17()
{
	if (!RDStalls17On()) return;
	const FVector Mid = Stall17Mid, Ua = Stall17Ua, Va = Stall17Va;
	// (the trades on this square: the twelve in an order of the town's own, by its seed)
	int32 Order[12]; for (int32 K = 0; K < 12; ++K) Order[K] = K;
	FRandomStream Hr(HashCombine((uint32)Seed, 0x5717u));
	for (int32 K = 11; K > 0; --K) { const int32 J = Hr.RandRange(0, K); Swap(Order[K], Order[J]); }
	// (the old four first, where they stood (Heaven had none: its twelve are all new))
	int32 Next = 0;
	TArray<int32> Old;
	for (int32 I = 0; I < TownSpots.Num(); ++I) if (TownSpots[I].Kind == TS_Stall) Old.Add(I);
	for (const int32 I : Old) TownSpots[I].Bld = Order[Next++ % 12];
	// (the new ones: places on the square in order of preference, each kept 4.2 m from every spot planned and off the main road's tiles;
	// their front faces the main road down the square's middle)
	struct FCand { float U, V; };
	static const FCand Cands[] = { { -1500.f, -650.f }, { -1500.f, 650.f }, { 1500.f, -650.f }, { 1500.f, 650.f },
		{ -1050.f, -650.f }, { -1050.f, 650.f }, { 1050.f, -650.f }, { 1050.f, 650.f },
		{ -1250.f, -1350.f }, { -1250.f, 1350.f }, { 1250.f, -1350.f }, { 1250.f, 1350.f },
		{ -600.f, -1350.f }, { -600.f, 1350.f }, { 600.f, -1350.f }, { 600.f, 1350.f },
		{ -1750.f, -1050.f }, { -1750.f, 1050.f }, { 1750.f, -1050.f }, { 1750.f, 1050.f },
		{ 0.f, -1400.f }, { 0.f, 1400.f }, { -1850.f, -400.f }, { 1850.f, 400.f } };
	auto Fits = [&](const FVector& At)
	{
		for (const float Du : { -130.f, 130.f })
			for (const float Dv : { -130.f, 130.f })
			{
				const FIntPoint T = WorldToLocal(At + Ua * Du + Va * Dv);
				if (!In(T) || Owner[Idx(T)] != 1000 || Type[Idx(T)] != 2 || !TownSquare.Contains(T)) return false;
			}
		for (const FTownBld& Tb : TownBlds)
		{
			const FIntPoint O = Tb.DoorTile + FIntPoint(RDS17Dir4[Tb.DoorSide].X, RDS17Dir4[Tb.DoorSide].Y), T = WorldToLocal(At);
			if (FMath::Max(FMath::Abs(O.X - T.X), FMath::Abs(O.Y - T.Y)) <= 1) return false;
		}
		for (const FTownSpot& Sp : TownSpots)
		{
			const float Need = Sp.Kind == TS_Fountain ? 620.f : Sp.Kind == TS_Rune ? 650.f : 420.f;
			if (FVector::Dist2D(Sp.At, At) < Need) return false;
		}
		return true;
	};
	const int32 Want = 12 - Old.Num();
	int32 Made = 0;
	for (const FCand& C : Cands)
	{
		if (Made >= Want) break;
		const FVector At = Mid + Ua * C.U + Va * C.V;
		if (!Fits(At)) continue;
		FTownSpot St; St.Kind = TS_Stall; St.At = At;
		// (its front (+X) toward the road down the middle)
		St.Yaw = (Va * (C.V > 0.f ? -1.f : 1.f)).Rotation().Yaw;
		St.Bld = Order[Next++ % 12] | 16;          // (16: a new stand, its mesh by a hash)
		TownSpots.Add(St);
		++Made;
	}
	UE_LOG(LogRDList17b, Log, TEXT("RDSTALLS17 %d stands (%d old, %d new of %d wanted)"), Old.Num() + Made, Old.Num(), Made, Want);
}

void ARDSection::PostStallKeepers17()
{
	// (a keeper behind each: a trader of the stand, 2 m behind its counter, spawned where posted (Index 4000 + the trade: the spawn moves
	// any other post off a blocked tile, and moved nine keepers of twelve to the first free tile it met, up to 12 m off; one tile back,
	// four of twelve still met a neighbour's); posted after every other post, so the town's own trader stays the first)
	for (const FTownSpot& Sp : TownSpots)
	{
		if (Sp.Kind != TS_Stall || Sp.Bld < 0) continue;
		const FVector F_ = FRotator(0, Sp.Yaw, 0).RotateVector(FVector(1, 0, 0));
		FTownPost P_; P_.Role = ERDTownRole::Trader; P_.At = Sp.At - F_ * 200.f; P_.Yaw = F_.Rotation().Yaw; P_.Bld = -1; P_.Wander = 0.f; P_.Index = 4000 + (Sp.Bld & 15);
		TownPosts.Add(P_);
	}
}

// ================================================================================================ the tests
TArray<FString> ARDDungeonGenerator::GetStalls17() const
{
	TArray<FString> Out;
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S) return Out;
	for (const ARDSection::FTownSpot& Sp : S->TownSpots)
		if (Sp.Kind == TS_Stall)
		{
			// (its keeper: the trader posted nearest behind it)
			int32 Keeper = -1;
			for (int32 I = 0; I < TownPeople.Num(); ++I)
				if (const ARDTownsfolk* T = TownPeople[I]; IsValid(T) && Sp.Bld >= 0 && T->Stall17 == (Sp.Bld & 15)) { Keeper = I; break; }
			Out.Add(FString::Printf(TEXT("%d|%s|%.0f|%.0f|%.0f|%.1f|%d|%d"), Sp.Bld < 0 ? -1 : (Sp.Bld & 15), Sp.Bld < 0 ? TEXT("") : *StallName17(Sp.Bld & 15, TownPlan == 5),
				Sp.At.X, Sp.At.Y, Sp.At.Z, Sp.Yaw, Sp.Bld >= 16 ? 1 : 0, Keeper));
		}
	return Out;
}

TArray<FString> ARDDungeonGenerator::GetStallStock17(int32 Trade) const
{
	TArray<FString> Out;
	bool bFit = false;
	for (const FName& N_ : StallStock17(Trade, &bFit))
	{
		const int32 Ix = FindItem(N_);
		if (Ix < 0) continue;
		const FRDItemDef& It = Items[Ix];
		FString Ts; for (const int32 X : It.Tiers) Ts += FString::Printf(TEXT("%s%d"), Ts.IsEmpty() ? TEXT("") : TEXT(","), X);
		Out.Add(FString::Printf(TEXT("%s|%d|%s|%d|%d|%d"), *N_.ToString(), (int32)It.Kind, *Ts, PriceOf(N_), StallFits17(It) ? 1 : 0, StallSells17(Trade, It) ? 1 : 0));
	}
	Out.Insert(FString::Printf(TEXT("tier|%d|%d"), TownTier17(), bFit ? 1 : 0), 0);
	return Out;
}
