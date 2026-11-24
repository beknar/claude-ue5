// The user's list of 2026-11-22 (docs/improvements16.txt, "gold and trade goods"; the plan docs/improvements16_plan.md), its seventeenth
// phase: raw gems and old coins of a dead kingdom, found in the caves (each a draw of its own besides a container's things), which every
// trader buys at their worth and a collector in one city (CollectorTown16) at double; dragonglass and blackstone, found the same way,
// which only one city's smith each works (SmithWorks16) into a blade and a set of plate of the band of the game's tier, giving her a
// reason to travel there.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDCombat.h"
#include "RD/RDGameInstance.h"
#include "RD/RDWild.h"
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
		FRandomStream R((int32)HashCombine(HashCombine((uint32)SessionSeed ^ GetTypeHash(N), GetTypeHash(Section)), GetTypeHash(Index * 7907 + 11)));
		if (R.FRand() < FCString::Atof(*Sh)) Out.Add(It);
	}
}

// ================================================================================================ the trade goods and the collector
bool ARDDungeonGenerator::IsCollectorTown16() const
{
	return bWild && Wild && Wild->Towns.IsValidIndex(WildTownIdx) && !CollectorTown16.IsEmpty() && Wild->Towns[WildTownIdx].Name == CollectorTown16;
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
	// (the band of the result made at the game's tier: the copy whose tiers hold it, else the plain one)
	const int32 T = FMath::Clamp(GetGameTier(), 1, GameTierMax);
	FName Plain;
	for (const FRDItemDef& It : Items)
	{
		const FString Nm = It.Name.ToString();
		if (!Nm.EndsWith(Result)) continue;
		if (Nm == Result) Plain = It.Name;
		if (It.Tiers.Contains(T)) return It.Name;
	}
	return Plain;
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
			Add(TEXT("forge16"), FString::Printf(TEXT("Forge a %s from %d %s"), *Made.ToString(), Need, *F[1]), FString::Printf(TEXT("%d g"), Cost),
				FString::Printf(TEXT("Only the smith of %s works %s. You carry %d."), *F[3], *F[1].ToLower(), Have), Have >= Need && Gold >= Cost, F[0]);
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
		if (GetGold() < Cost) { SetTownNote(TEXT("You have too little gold")); return false; }
		PlayerCombat->RemoveItem(Mat, Need);
		AddGold(-Cost, TEXT("the smith's forging"));
		PlayerCombat->AddItem(Made, 1);
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
