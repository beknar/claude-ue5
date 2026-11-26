// The user's list of 2026-11-26 (docs/improvements17.txt; the plan docs/improvements17_plan.md), its fourth phase: the square's shops.
//   "The town squares in every city need 3x more stands and shops, each one different in what they offer. The town square shops and stands
//   need to offer items that are of the same Tier that the town is in."
//   - Every medieval city's one general store becomes three: the general store (potions, food, materials and repairs, torches and
//     recipes), an outfitter (weapons, armour, shields) and an apothecary (potions, scrolls, herbs and reagents), the two new ones placed
//     round the square as the trades are (with the plan's draws: after the homes no plot near the square was left), each with its trader,
//     counter and sign; the homes and their containers lay out anew once (rd.Shops17 0: the town of before).
//   - Heaven's shops take nine kinds where they had three, in the order its shops stand (each kind at least once among its twelve):
//     grocery, pharmacy, hardware, electronics, jeweller, bookshop, sporting goods, outdoor outfitter, herbalist; its market (the trader's
//     store) the general store's.
//   - Every store's stock is its trades' (the stands' twelve, RDList17b.cpp) at the town's tier, fit for her hero.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "HAL/IConsoleManager.h"

namespace
{
	TAutoConsoleVariable<int32> CVarRDShops17(TEXT("rd.Shops17"), 1, TEXT("Three stores in each medieval city and nine shop kinds in Heaven (1, the list of 2026-11-26) or one store and three kinds (0); read when a town is planned"));

	// (each store kind's trades, of the stands' twelve: 0 weapons 1 armour 2 shields 3 rings 4 potions 5 food 6 scrolls 7 tomes 8 reagents
	// 9 materials and repairs 10 torches and recipes 11 slashes)
	struct FRDShop17 { const TCHAR* Title; const TCHAR* Word; const TCHAR* Body; TArray<int32> Trades; };
	const TArray<FRDShop17>& RDMedievalStores17()
	{
		static const TArray<FRDShop17> T = {
			{ TEXT("The general store"), TEXT("GENERAL\nGOODS"), TEXT("Barrels, sacks and shelves to the rafters. \"If it's sold in this town, I've got it or I know who has.\""), { 4, 5, 9, 10 } },
			{ TEXT("The outfitter"), TEXT("OUTFITTER"), TEXT("Blades on the wall, mail on stands, shields stacked by the door. \"Try it on. It's your life it's saving.\""), { 0, 1, 2 } },
			{ TEXT("The apothecary"), TEXT("APOTHECARY"), TEXT("Jars of roots and powders, a still bubbling in the corner, scrolls in pigeonholes. The apothecary sniffs at you."), { 4, 6, 8 } } };
		return T;
	}
	const TArray<FRDShop17>& RDHeavenShops17()
	{
		static const TArray<FRDShop17> T = {
			{ TEXT("The grocery"), TEXT("GROCERY"), TEXT("Shelves of tins, bread in bags, fruit under misted glass. The clerk scans without looking up."), { 5 } },
			{ TEXT("The pharmacy"), TEXT("PHARMACY"), TEXT("Rows of little boxes, white and green, and a counter that smells of mint. \"Ask if you can't find it.\""), { 4 } },
			{ TEXT("The hardware store"), TEXT("HARDWARE"), TEXT("Kits, tape, lamps and tools on hooks to the ceiling. \"If it's broken, we've got the thing that fixes it.\""), { 9 } },
			{ TEXT("The electronics store"), TEXT("ELECTRONICS"), TEXT("Screens on every wall, lamps and torches in blister packs, a demo playing to nobody."), { 10 } },
			{ TEXT("The jeweller"), TEXT("JEWELLER"), TEXT("Glass cases under spotlights, rings on velvet. A guard by the door watches you come in."), { 3 } },
			{ TEXT("The bookshop"), TEXT("BOOKS"), TEXT("Tall shelves, a reading chair, the smell of paper. Some of these books are older than the city."), { 6, 7 } },
			{ TEXT("The sporting goods store"), TEXT("SPORTS"), TEXT("Racks of gear, bats and blades and things for hunting, a bench of strange kits at the back."), { 0, 11 } },
			{ TEXT("The outdoor outfitter"), TEXT("OUTDOOR"), TEXT("Jackets, packs and body armour on mannequins, shields hung like snowboards."), { 1, 2 } },
			{ TEXT("The herbalist"), TEXT("HERBS"), TEXT("Bins of dried leaves and roots under handwritten labels, a mortar on the counter."), { 8 } } };
		return T;
	}
	// (the gondola shelves each kind's floor takes, of 946's three: a grocery's, a pharmacy's, a hardware store's goods)
	const int32 RDGondola17[9] = { 0, 1, 2, 2, 1, 0, 2, 2, 1 };
}

bool RDShops17On() { return CVarRDShops17.GetValueOnGameThread() != 0; }

// ================================================================================================ a store's kind
int32 ARDSection::StoreKind17(int32 BI) const
{
	// (a medieval city's stores in the order they stand in the plan: 0 the general store, 1 the outfitter, 2 the apothecary; -1 not a store
	// or not one of them (Heaven's market: the general store's))
	if (!TownBlds.IsValidIndex(BI) || TownBlds[BI].Kind != TK_Store || Theme == FName(TEXT("Heaven"))) return -1;
	return TownBlds[BI].Store17;
}

int32 ARDSection::ShopOrder17(int32 BI) const
{
	int32 K = 0;
	for (int32 I = 0; I < BI; ++I) if (TownBlds[I].Kind == TK_Shop) ++K;
	return K;
}

FString ARDSection::StoreWord17(int32 BI) const
{
	const int32 K = StoreKind17(BI);
	return K >= 0 ? FString(RDMedievalStores17()[K].Word) : FString();
}

int32 ARDSection::GondolaOf17(int32 Kind) const
{
	return Kind >= 0 && Kind < 9 ? RDGondola17[Kind] : 0;
}

// ================================================================================================ what each sells
const TArray<int32>& ARDDungeonGenerator::StoreTrades17(int32 Medieval, int32 HeavenKind)
{
	static const TArray<int32> None;
	if (HeavenKind >= 0 && HeavenKind < RDHeavenShops17().Num()) return RDHeavenShops17()[HeavenKind].Trades;
	if (Medieval >= 0 && Medieval < RDMedievalStores17().Num()) return RDMedievalStores17()[Medieval].Trades;
	return RDMedievalStores17()[0].Trades;          // (a store of no kind: the general store's (Heaven's market, a panel opened from a test))
}

FString ARDDungeonGenerator::StoreTitle17(int32 Medieval, int32 HeavenKind, bool bHeaven, FString* Body)
{
	const FRDShop17* S = HeavenKind >= 0 && HeavenKind < RDHeavenShops17().Num() ? &RDHeavenShops17()[HeavenKind]
	                   : Medieval >= 0 && Medieval < RDMedievalStores17().Num() ? &RDMedievalStores17()[Medieval] : nullptr;
	if (!S)
	{
		if (Body) *Body = bHeaven ? TEXT("Aisle after aisle under white light, a hum of fridges, a till that beeps. \"Anything you need, it's here somewhere.\"") : RDMedievalStores17()[0].Body;
		return bHeaven ? TEXT("The market") : RDMedievalStores17()[0].Title;
	}
	if (Body) *Body = S->Body;
	return S->Title;
}

FString ARDDungeonGenerator::ShopWord17(int32 HeavenKind)
{
	return HeavenKind >= 0 && HeavenKind < RDHeavenShops17().Num() ? FString(RDHeavenShops17()[HeavenKind].Word) : FString(TEXT("MARKET"));
}

TArray<FName> ARDDungeonGenerator::StoreStock17(const TArray<int32>& Trades, bool* bAnyFit) const
{
	// (what fits her from each trade; when nothing of the whole store does, all of it (PR #140's review: a trade that fitted nothing gave
	// its whole band, every weapon to the Mage at the outfitter))
	TArray<FName> Out;
	for (const int32 T : Trades) for (const FName& N : StallStock17(T, nullptr, true)) Out.AddUnique(N);
	if (bAnyFit) *bAnyFit = Out.Num() > 0;
	if (Out.Num() == 0) for (const int32 T : Trades) for (const FName& N : StallStock17(T)) Out.AddUnique(N);
	return Out;
}

int32 ARDDungeonGenerator::StoreKindOpen17(int32& HeavenKind) const
{
	// (the store the panel was opened at: its building (the counter's or its trader's), a medieval store's kind or Heaven's shop's)
	HeavenKind = ShopKindOfWho21();
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	return S && HeavenKind < 0 ? S->StoreKind17(StoreBld21) : -1;
}

// ================================================================================================ the tests
TArray<FString> ARDDungeonGenerator::GetStores17() const
{
	// ("<building>|<kind word>|<medieval kind>|<Heaven kind>|<door x>|<door y>|<counter x>|<counter y>|<trades>")
	TArray<FString> Out;
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S) return Out;
	for (int32 BI = 0; BI < S->TownBlds.Num(); ++BI)
	{
		const ARDSection::FTownBld& B = S->TownBlds[BI];
		if (B.Kind != TK_Store && B.Kind != TK_Shop) continue;
		const int32 Mk = S->StoreKind17(BI), Hk = S->ShopKind21(BI);
		FVector Ck = FVector::ZeroVector;
		for (const ARDSection::FTownSpot& Sp : S->TownSpots) if (Sp.Kind == TS_Counter && Sp.Bld == BI) Ck = Sp.At;
		const FVector D = B.Door >= 0 ? S->GetDoorLocation(B.Door) : FVector::ZeroVector;
		FString Ts; for (const int32 T : StoreTrades17(Mk, Hk)) Ts += FString::Printf(TEXT("%s%d"), Ts.IsEmpty() ? TEXT("") : TEXT(","), T);
		Out.Add(FString::Printf(TEXT("%d|%s|%d|%d|%.0f|%.0f|%.0f|%.0f|%s"), BI, *(Hk >= 0 ? ShopWord17(Hk) : Mk >= 0 ? S->StoreWord17(BI).Replace(TEXT("\n"), TEXT(" ")) : FString(TEXT("MARKET"))), Mk, Hk, D.X, D.Y, Ck.X, Ck.Y, *Ts));
	}
	return Out;
}
