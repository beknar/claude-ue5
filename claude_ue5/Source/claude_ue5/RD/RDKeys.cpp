// The dungeons' keys in order (the user's list of 2026-11-08b, docs/improvements9.txt, its third phase: "the defeat of the
// dungeon boss at Mistward Castle drops not just a reward, it drops a key and a map to vell morrath, that will be the key to
// opening its dungeon. this key will not open any of the other dungeons. the dungeons are opened in order, with Heaven being the
// last. Each town's dungeon drops a key to the next one").
//   - the chain (DungeonChain, 905 from SourceArt/dungeons/chain.json): Mistward Castle, then each town's dungeon in order,
//     each with its key and its map (items of kind Key, known by name: not sold, not stored, kept at her death)
//   - the way down into a town's dungeon is refused without its key (DescendToCatacombs; the castle is always open)
//   - a dungeon's boss (Mistward's final boss; another dungeon's last tier's boss) drops the next dungeon's key and map, once a
//     game; the way is hers from that moment (the game's counter "dkey:<dungeon>", saved): a pile left behind (a death, the
//     door taken at once, the level left) does not lock the rest of the chain (PR #31's review)
//   - a game saved before the keys gets the keys its progress implies: Mistward's final boss slain, a dungeon entered, a
//     dungeon's last tier's boss slain
//   - the map, out in the wilds: the road from the town before to its town and the land round it revealed on her map, once the
//     town is in the world
#include "RD/RDDungeonGenerator.h"
#include "RD/RDCombat.h"
#include "RD/RDGameInstance.h"
#include "RD/RDWild.h"
#include "RD/RDMistward.h"
#include "Engine/World.h"
#include "Misc/Parse.h"
#include "Misc/CommandLine.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDKeys, Log, All);

namespace
{
	FString RDKShort(const FString& Level)
	{
		// ("/Game/RandomDungeon/Maps/vel_morrath" or "vel_morrath" alike)
		FString S = Level; int32 I;
		if (S.FindLastChar(TEXT('/'), I)) S = S.Mid(I + 1);
		if (S.FindChar(TEXT('.'), I)) S = S.Left(I);
		return S.ToLower();
	}
}

const TArray<ARDDungeonGenerator::FRDChainLink>& ARDDungeonGenerator::Chain() const
{
	// (parsed once, again only if the chain's text changes: PR #31's review, every lookup parsed it)
	uint32 H = 0;
	for (const FString& S : DungeonChain) H = HashCombine(H, GetTypeHash(S));
	if (H == ChainHash && ChainCache.Num() > 0) return ChainCache;
	ChainCache.Reset(); ChainHash = H;
	for (const FString& S : DungeonChain)
	{
		TArray<FString> P; S.ParseIntoArray(P, TEXT("|"), false);
		if (P.Num() < 6) continue;
		FRDChainLink L;
		L.Key = P[0]; L.Level = P[1]; L.Short = RDKShort(P[1]); L.Town = P[2]; L.Title = P[3];
		L.KeyItem = P[4].IsEmpty() ? NAME_None : FName(*P[4]); L.MapItem = P[5].IsEmpty() ? NAME_None : FName(*P[5]);
		// (the rebalance to tier 25: the dungeon's tiers in the game's, "|base|cap" after its map (905 from chain.json))
		if (P.Num() >= 8) { L.TierBase = FCString::Atoi(*P[6]); L.TierCap = FCString::Atoi(*P[7]); }
		ChainCache.Add(L);
	}
	return ChainCache;
}

int32 ARDDungeonGenerator::ChainIndexOfLevel(const FString& Level) const
{
	const FString Want = RDKShort(Level);
	return Chain().IndexOfByPredicate([&](const FRDChainLink& L) { return L.Short == Want; });
}

int32 ARDDungeonGenerator::ChainIndexOfKey(const FString& Key) const
{
	return Chain().IndexOfByPredicate([&](const FRDChainLink& L) { return L.Key == Key; });
}

bool ARDDungeonGenerator::HasDungeonKey(const FString& Level) const
{
	// (the first of the chain (Mistward Castle) and a level not in it need none)
	const int32 I = ChainIndexOfLevel(Level);
	if (I <= 0) return true;
	const FRDChainLink& L = Chain()[I];
	if (const URDGameInstance* GI = URDGameInstance::Of(this))
	{
		// (every way open: tests and the packaged game's runs, never saved (PR #31's review: as a counter it went into the saves))
		if (GI->bAllDungeonKeys || GI->GetCounter(TEXT("dkey:") + L.Key) > 0) return true;
		// (-RDAllKeys read before TickDungeonKeys has: the packaged runs go down in the town's first ticks)
		if (!GI->bAllKeysRead && FParse::Param(FCommandLine::Get(), TEXT("RDAllKeys"))) return true;
	}
	return PlayerCombat && !L.KeyItem.IsNone() && PlayerCombat->GetItemCount(L.KeyItem) > 0;
}

FString ARDDungeonGenerator::DungeonLockedLine(const FString& Level) const
{
	const int32 I = ChainIndexOfLevel(Level);
	if (I <= 0) return FString();
	const FRDChainLink& L = Chain()[I];
	const FRDChainLink& Prev = Chain()[I - 1];
	return FString::Printf(TEXT("The way into %s is locked. Its key, the %s, is held by the master of %s."), *L.Title, *L.KeyItem.ToString(), *Prev.Title);
}

bool ARDDungeonGenerator::IsDungeonChainItem(FName Item) const
{
	if (Item.IsNone()) return false;
	return Chain().ContainsByPredicate([&](const FRDChainLink& L) { return L.KeyItem == Item || L.MapItem == Item; });
}

void ARDDungeonGenerator::DropNextDungeonKey(const FVector& At)
{
	// (this dungeon's place in the chain: its key (Mistward Castle's is empty); the next one's key and map lie where its boss fell)
	const int32 I = ChainIndexOfKey(DungeonKey);
	if (I < 0 || !Chain().IsValidIndex(I + 1)) return;
	const FRDChainLink& Next = Chain()[I + 1];
	URDGameInstance* GI = URDGameInstance::Of(this);
	// (once a game: the key given at the first drop (PR #31's review: two of the last tier's bosses killed before a pile was taken
	// dropped two keys))
	if (GI && GI->GetCounter(TEXT("dkey:") + Next.Key) > 0) { UE_LOG(LogRDKeys, Log, TEXT("RDKEY %s's key given already: none dropped"), *Next.Title); return; }
	TArray<FName> Things;
	for (const FName& N : { Next.KeyItem, Next.MapItem }) if (!N.IsNone() && FindItem(N) >= 0) Things.Add(N);
	if (Things.Num() == 0) { UE_LOG(LogRDKeys, Warning, TEXT("RDKEY %s's key and map are not items of this level (905)"), *Next.Title); return; }
	TArray<float> Wear; Wear.Init(-1.f, Things.Num());
	if (ARDLootPile* P = DropLoot(At + FVector(0, 0, 100.f), Things, Wear)) P->bHers = false;
	// (the way and the map are hers from now: the pile is what she sees and carries)
	if (GI) { GI->CountMax(TEXT("dkey:") + Next.Key, 1); GI->CountMax(TEXT("dmap:") + Next.Town, 1); }
	DungeonKeyDropped = Next.Key;
	if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("The %s and a map to %s lie where the master of %s fell."), *Next.KeyItem.ToString(), *Next.Town, *(DungeonTitle.IsEmpty() ? FString(TEXT("Mistward Castle")) : DungeonTitle)));
	UE_LOG(LogRDKeys, Log, TEXT("RDKEY dropped: %s and %s (the way into %s)"), *Next.KeyItem.ToString(), *Next.MapItem.ToString(), *Next.Title);
}

void ARDDungeonGenerator::TickDungeonKeys()
{
	if (DungeonChain.Num() == 0 || !PlayerCombat) return;
	const float Now = GetWorld()->GetTimeSeconds();
	if (Now < DungeonKeysNextTick) return;
	DungeonKeysNextTick = Now + 1.f;
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return;
	// (-RDAllKeys: every way open, read once a game instance; not saved)
	if (!GI->bAllKeysRead) { GI->bAllKeysRead = true; if (FParse::Param(FCommandLine::Get(), TEXT("RDAllKeys"))) GI->bAllDungeonKeys = true; }
	const TArray<FRDChainLink>& C = Chain();
	auto Give = [&](int32 I, const TCHAR* Why)
	{
		if (!C.IsValidIndex(I) || GI->GetCounter(TEXT("dkey:") + C[I].Key) > 0) return;
		GI->CountMax(TEXT("dkey:") + C[I].Key, 1);
		UE_LOG(LogRDKeys, Log, TEXT("RDKEY the way into %s is hers: %s"), *C[I].Title, Why);
	};
	for (int32 I = 1; I < C.Num(); ++I)
	{
		const FRDChainLink& L = C[I];
		// (what she carries is hers in the game's counters)
		if (!L.KeyItem.IsNone() && PlayerCombat->GetItemCount(L.KeyItem) > 0) Give(I, TEXT("its key carried"));
		if (!L.MapItem.IsNone() && PlayerCombat->GetItemCount(L.MapItem) > 0) GI->CountMax(TEXT("dmap:") + L.Town, 1);
		// (a game saved before the keys (PR #31's review): the way into a dungeon she has been in, and the next one's when this
		// dungeon's last tier's boss is dead; Mistward's final boss slain gives the first)
		if (GI->Dungeons.Contains(L.Key)) Give(I, TEXT("she has been there"));
		if (GI->GetCounter(URDGameInstance::DungeonCounter(L.Key, TEXT("bossdone:5"))) > 0) Give(I + 1, TEXT("the dungeon before it conquered"));
	}
	if (GI->GetCounter(TEXT("finalboss")) > 0) Give(1, TEXT("Mistward's master slain"));
	// (out in the wilds: a map taken shows its road and its town's land, once the town is in the world)
	if (bWild && IsWildReady())
		for (int32 I = 1; I < C.Num(); ++I)
		{
			const FRDChainLink& L = C[I];
			if (GI->GetCounter(TEXT("dmap:") + L.Town) == 0 || GI->GetCounter(TEXT("dmapshown:") + L.Town) > 0) continue;
			const int32 Cells = RevealRoute(C[I - 1].Town.IsEmpty() ? FString(TEXT("Brokenspire")) : C[I - 1].Town, L.Town);
			if (Cells < 0) continue;                 // (its town not in this world yet: shown when it is (PR #31's review))
			GI->CountMax(TEXT("dmapshown:") + L.Town, 1);
			if (Cells > 0) PlayerCombat->ShowMessage(FString::Printf(TEXT("Your map shows the way to %s."), *L.Town));
		}
}

int32 ARDDungeonGenerator::RevealRoute(const FString& From, const FString& To)
{
	if (!IsWildReady()) return -1;
	int32 A = -1, B = -1;
	for (int32 T = 0; T < Wild->Towns.Num(); ++T)
	{
		if (Wild->Towns[T].Name == From) A = T;
		if (Wild->Towns[T].Name == To) B = T;
	}
	if (B < 0) return -1;
	const int32 C0 = WildRevealedCells;
	// (the road between them, else the straight way; 700 m either side of it, 2.5 km round the town)
	TArray<FVector2D> Way;
	for (const FRDWildWorld::FRoad& R : Wild->Roads)
		if ((R.From == A && R.To == B) || (R.From == B && R.To == A)) { Way = R.P; break; }
	if (Way.Num() == 0 && A >= 0) Way = { Wild->Towns[A].Site, Wild->Towns[B].Site };
	for (int32 K = 0; K + 1 < Way.Num(); ++K)
	{
		const double Len = FVector2D::Distance(Way[K], Way[K + 1]);
		const int32 N = FMath::Max(1, FMath::CeilToInt(Len / 350.0));
		for (int32 S = 0; S <= N; ++S) RevealWild(FMath::Lerp(Way[K], Way[K + 1], (double)S / N), 700.f);
	}
	RevealWild(Wild->Towns[B].Site, 2500.f);
	UE_LOG(LogRDKeys, Log, TEXT("RDKEY the map to %s: %d cells shown (the road from %s: %d points)"), *To, WildRevealedCells - C0, *From, Way.Num());
	return WildRevealedCells - C0;
}

void ARDDungeonGenerator::DebugAllDungeonKeys(bool bOn)
{
	if (URDGameInstance* GI = URDGameInstance::Of(this)) { GI->bAllDungeonKeys = bOn; GI->bAllKeysRead = true; }
}

TArray<FString> ARDDungeonGenerator::GetDungeonKeyLines() const
{
	TArray<FString> Out;
	const URDGameInstance* GI = URDGameInstance::Of(this);
	const TArray<FRDChainLink>& C = Chain();
	for (int32 I = 0; I < C.Num(); ++I)
	{
		const FRDChainLink& L = C[I];
		Out.Add(FString::Printf(TEXT("%d|%s|%s|%s|%s|%d|%d|%d|%d"), I, *L.Key, *L.Level, *L.Town, *L.KeyItem.ToString(), HasDungeonKey(L.Level) ? 1 : 0,
			GI ? GI->GetCounter(TEXT("dkey:") + L.Key) : 0, GI ? GI->GetCounter(TEXT("dmap:") + L.Town) : 0, GI ? GI->GetCounter(TEXT("dmapshown:") + L.Town) : 0));
	}
	return Out;
}

int32 ARDDungeonGenerator::GetWildTierAt(float Xm, float Ym) const
{
	return IsWildReady() ? Wild->TierAt(Xm, Ym) : 0;
}
