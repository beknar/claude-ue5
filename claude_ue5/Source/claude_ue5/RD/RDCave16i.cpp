// The user's list of 2026-11-22 (docs/improvements16.txt, "gold and trade goods"; the plan docs/improvements16_plan.md), its seventeenth
// phase: raw gems and old coins of a dead kingdom, found in the caves (each a draw of its own besides a container's things), which every
// trader buys at their worth and a collector in one city (CollectorTown16) at double; dragonglass and blackstone, found the same way,
// which only one city's smith each works (SmithWorks16) into a blade and a set of plate of the band of the game's tier, giving her a
// reason to travel there.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDCombat.h"
#include "RD/RDGameInstance.h"
#include "RD/RDWild.h"
#include "RD/RDMistward.h"
#include "Kismet/GameplayStatics.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDCave16i, Log, All);

// ================================================================================================ the caves' things besides
void ARDDungeonGenerator::CaveBesidesOf16(FIntPoint Section, int32 Index, TArray<FName>& Out) const
{
	// ("<item>|<share>": each on a stream of its own (its name's hash), so neither the container's draw nor another's moves)
	if (!bCave16) return;
	for (const FString& L : CaveBesides16)
	{
		FString N, Sh;
		if (!L.Split(TEXT("|"), &N, &Sh)) continue;
		const FName It(*N);
		if (FindItem(It) < 0) continue;
		// (a CRC of the session's seed, the thing's name, the set and the container: a stream's first number from seeds that differ in a few
		// bits came out correlated (five of seven shares half their want over twelve session seeds, the first measure))
		const uint32 Data[5] = { (uint32)SessionSeed, GetTypeHash(N), (uint32)Section.X, (uint32)Section.Y, (uint32)Index };
		const uint32 Hc = FCrc::MemCrc32(Data, sizeof(Data), 0xB5167u);
		if ((float)(Hc & 0xFFFFFFu) / 16777216.f < FCString::Atof(*Sh)) Out.Add(It);
	}
}

// ================================================================================================ the trade goods and the collector
bool ARDDungeonGenerator::IsCollectorTown16() const
{
	// (the loaded town is his city and she stands in it (PR #124's review: the town stays loaded to 2 km, where a camp's trader could stand))
	if (!(bWild && Wild && Wild->Towns.IsValidIndex(WildTownIdx) && !CollectorTown16.IsEmpty() && Wild->Towns[WildTownIdx].Name == CollectorTown16)) return false;
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	return Her && FVector2D::Distance(FVector2D(Her->GetActorLocation()) / 100.0, Wild->Towns[WildTownIdx].Site) < CollectorReachM16;
}

int32 ARDDungeonGenerator::TradeValue16(FName Item) const
{
	// (a trade good's worth when sold: its price by the game's tier (a quarter more a tier, as the cave chests' gold), the collector's double)
	for (const FString& L : TradeGoods16)
	{
		FString N, P;
		if (!L.Split(TEXT("|"), &N, &P) || N != Item.ToString()) continue;
		const int32 T = FMath::Clamp(GetGameTier(), 1, GameTierMax);
		const float V = FCString::Atof(*P) * (1.f + 0.25f * (T - 1)) * (IsCollectorTown16() ? CollectorMul16 : 1.f);
		return FMath::Max(1, FMath::RoundToInt(V));
	}
	return -1;
}

// ================================================================================================ the smiths who work them
FName ARDDungeonGenerator::SmithWorkOf16(const FString& Result) const
{
	return SmithBandAt16(Result, FMath::Clamp(GetGameTier(), 1, GameTierMax));
}

FName ARDDungeonGenerator::SmithBandAt16(const FString& Result, int32 Tier) const
{
	// (the band of the game's tier by its place among the bands (tiers 1-5 the plain, 6-10 Fine, ... 26-30 Divine), the nearest band
	// below where a map has not that one (PR #124's review: an exact match of the copies' tiers (the like's tier plus 5 a band) found
	// nothing at four tiers of five, and the plain copy came at a higher price))
	static const TCHAR* Bands[] = { TEXT(""), TEXT("Fine "), TEXT("Masterwork "), TEXT("Exalted "), TEXT("Celestial "), TEXT("Divine ") };
	for (int32 B = FMath::Clamp((Tier - 1) / 5, 0, 5); B >= 0; --B)
	{
		const FName Nm(*(FString(Bands[B]) + Result));
		if (FindItem(Nm) >= 0) return Nm;
	}
	return NAME_None;
}

FString ARDDungeonGenerator::SmithRefusal16(FName Made) const
{
	// (what her hero cannot use is not offered (PR #124's review; PR #104's rule)): a weapon with no fit for her hero, armour she does not wear
	const int32 Ix = FindItem(Made);
	if (Ix < 0) return TEXT("no such work");
	const FRDItemDef& It = Items[Ix];
	if (It.Kind == ERDItemKind::Weapon && !It.WeaponFits.ContainsByPredicate([this](const FRDWeaponFit& F) { return F.Hero == CurrentHero; }))
		return FString::Printf(TEXT("The %s is no weapon for a %s"), *Made.ToString(), *HeroTitle16());
	if (It.Kind == ERDItemKind::Armour) return ArmourRefusal(It, Made.ToString());
	return FString();
}

FString ARDDungeonGenerator::HeroTitle16() const
{
	const FRDHeroDef* Hd = FindHero(CurrentHero);
	return Hd && !Hd->Title.IsEmpty() ? Hd->Title.ToLower() : CurrentHero.ToString().ToLower();
}

void ARDDungeonGenerator::AddSmithWorks16(TFunctionRef<void(const FString& Act, const FString& Label, const FString& Tag, const FString& Detail, bool bOn, const FString& Arg)> Add) const
{
	// ("<result>|<material>|<count>|<city>|<gold>": in its city the smith forges it; elsewhere, while she carries the material, the smith
	// says who works it)
	const FString Here = bWild && Wild && Wild->Towns.IsValidIndex(WildTownIdx) ? Wild->Towns[WildTownIdx].Name : FString();
	const int32 Gold = GetGold();
	for (const FString& L : SmithWorks16)
	{
		TArray<FString> F; L.ParseIntoArray(F, TEXT("|"), false);
		if (F.Num() < 5) continue;
		const FName Mat(*F[1]);
		const int32 Need = FCString::Atoi(*F[2]), Cost = FMath::RoundToInt(FCString::Atoi(*F[4]) * (1.f + 0.25f * (FMath::Clamp(GetGameTier(), 1, GameTierMax) - 1)));
		const int32 Have = PlayerCombat ? PlayerCombat->GetItemCount(Mat) : 0;
		if (Here == F[3])
		{
			const FName Made = SmithWorkOf16(F[0]);
			if (Made.IsNone()) continue;
			const FString No = SmithRefusal16(Made);
			Add(TEXT("forge16"), FString::Printf(TEXT("Forge a %s from %d %s"), *Made.ToString(), Need, *F[1]), FString::Printf(TEXT("%d g"), Cost),
				No.IsEmpty() ? FString::Printf(TEXT("Only the smith of %s works %s. You carry %d."), *F[3], *F[1].ToLower(), Have) : No + TEXT("."),
				No.IsEmpty() && Have >= Need && Gold >= Cost, F[0]);
		}
		else if (Have > 0)
			Add(TEXT("none"), FString::Printf(TEXT("%s: only the smith of %s works it"), *F[1], *F[3]), FString(),
				FString::Printf(TEXT("The smith turns the %s over and hands it back: \"Not this. Take it to %s.\""), *F[1].ToLower(), *F[3]), false, FString());
	}
}

bool ARDDungeonGenerator::TownForge16(const FString& Result)
{
	const FString Here = bWild && Wild && Wild->Towns.IsValidIndex(WildTownIdx) ? Wild->Towns[WildTownIdx].Name : FString();
	for (const FString& L : SmithWorks16)
	{
		TArray<FString> F; L.ParseIntoArray(F, TEXT("|"), false);
		if (F.Num() < 5 || F[0] != Result) continue;
		if (Here != F[3]) { SetTownNote(FString::Printf(TEXT("Only the smith of %s works %s"), *F[3], *F[1].ToLower())); return false; }
		const FName Mat(*F[1]), Made = SmithWorkOf16(F[0]);
		const int32 Need = FCString::Atoi(*F[2]), Cost = FMath::RoundToInt(FCString::Atoi(*F[4]) * (1.f + 0.25f * (FMath::Clamp(GetGameTier(), 1, GameTierMax) - 1)));
		if (!PlayerCombat || Made.IsNone() || PlayerCombat->GetItemCount(Mat) < Need) { SetTownNote(FString::Printf(TEXT("The smith needs %d %s"), Need, *F[1].ToLower())); return false; }
		if (const FString No = SmithRefusal16(Made); !No.IsEmpty()) { SetTownNote(No); return false; }
		if (GetGold() < Cost) { SetTownNote(TEXT("You have too little gold")); return false; }
		PlayerCombat->RemoveItem(Mat, Need);
		AddGold(-Cost, TEXT("the smith's forging"));
		PlayerCombat->AddItem(Made, 1);
		Forged16.Add(Made);
		SetTownNote(FString::Printf(TEXT("The smith of %s forges you a %s"), *F[3], *Made.ToString()));
		TownCount(TEXT("smith_forged16"));
		UE_LOG(LogRDCave16i, Log, TEXT("RDCAVE16 the smith of %s forged %s from %d %s for %d gold"), *F[3], *Made.ToString(), Need, *F[1], Cost);
		return true;
	}
	return false;
}

TArray<FString> ARDDungeonGenerator::GetTrade16() const
{
	// (for the tests: "town|<name>|<collector 1/0>", "value|<item>|<gold>" for each trade good, "work|<result>|<band made>")
	TArray<FString> Out;
	const FString Here = bWild && Wild && Wild->Towns.IsValidIndex(WildTownIdx) ? Wild->Towns[WildTownIdx].Name : FString();
	Out.Add(FString::Printf(TEXT("town|%s|%d"), *Here, IsCollectorTown16() ? 1 : 0));
	for (const FString& L : TradeGoods16) { FString N, P; if (L.Split(TEXT("|"), &N, &P)) Out.Add(FString::Printf(TEXT("value|%s|%d"), *N, TradeValue16(FName(*N)))); }
	for (const FString& L : SmithWorks16) { FString N, R; if (L.Split(TEXT("|"), &N, &R)) Out.Add(FString::Printf(TEXT("work|%s|%s"), *N, *SmithWorkOf16(N).ToString())); }
	return Out;
}

FString ARDDungeonGenerator::DebugSmithBand16(const FString& Result, int32 Tier) const
{
	return SmithBandAt16(Result, Tier).ToString();
}

int32 ARDDungeonGenerator::ForgetForged16()
{
	// (for the tests: what the smiths forged this session taken off her again (a weapon from her weapons, armour from her pack), and its
	// record of things looted)
	URDGameInstance* GI = URDGameInstance::Of(this);
	int32 N = 0;
	for (const FName& Made : Forged16)
	{
		if (!PlayerCombat) break;
		bool bDone = false;
		for (int32 I = Weapons.Num() - 1; I >= 0 && !bDone; --I)
			if (Weapons[I].Item == Made)
			{
				const int32 P0 = LootPiles.Num();
				PlayerCombat->DropWeaponAt(I);
				for (int32 K = LootPiles.Num() - 1; K >= P0; --K) if (ARDLootPile* Pl = LootPiles[K]) { Pl->Destroy(); LootPiles.RemoveAt(K); }
				bDone = true;
			}
		if (!bDone && PlayerCombat->GetItemCount(Made) > 0) { PlayerCombat->RemoveItem(Made, 1); bDone = true; }
		if (bDone) ++N;
		if (GI) GI->LootedItems.Remove(Made);
	}
	Forged16.Reset();
	return N;
}

TArray<FString> ARDDungeonGenerator::DebugPickups16(FIntPoint Section, int32 N) const
{
	TArray<FString> Out;
	for (int32 I = 0; I < N; ++I) Out.Add(PickupItemFor(Section, I).ToString());
	return Out;
}
