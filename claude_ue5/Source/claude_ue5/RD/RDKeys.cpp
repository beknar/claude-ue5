// The dungeons' keys in order (the user's list of 2026-11-08b, docs/improvements9.txt, its third phase: "the defeat of the
// dungeon boss at Mistward Castle drops not just a reward, it drops a key and a map to vell morrath, that will be the key to
// opening its dungeon. this key will not open any of the other dungeons. the dungeons are opened in order, with Heaven being the
// last. Each town's dungeon drops a key to the next one").
//   - the chain (DungeonChain, 905 from SourceArt/dungeons/chain.json): Mistward Castle, then each town's dungeon in order,
//     each with its key and its map (items of kind Key, known by name: not sold, not stored, kept at her death)
//   - the way down into a town's dungeon is refused without its key (DescendToCatacombs; the castle is always open)
//   - a dungeon's boss (Mistward's final boss; another dungeon's last tier's boss) drops the next dungeon's key and map
//   - what she has had is kept in the game's counters ("dkey:<dungeon>", "dmap:<town>"): saved, and a key sold or lost would
//     still open its way
//   - the map, out in the wilds: the road from the town before to its town and the land round it revealed on her map
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

bool ARDDungeonGenerator::ChainLink(int32 I, FRDChainLink& Out) const
{
	if (!DungeonChain.IsValidIndex(I)) return false;
	TArray<FString> P; DungeonChain[I].ParseIntoArray(P, TEXT("|"), false);
	if (P.Num() < 6) return false;
	Out.Key = P[0]; Out.Level = P[1]; Out.Town = P[2]; Out.Title = P[3]; Out.KeyItem = FName(*P[4]); Out.MapItem = FName(*P[5]);
	if (P[4].IsEmpty()) Out.KeyItem = NAME_None;
	if (P[5].IsEmpty()) Out.MapItem = NAME_None;
	return true;
}

int32 ARDDungeonGenerator::ChainIndexOfLevel(const FString& Level) const
{
	const FString Want = RDKShort(Level);
	FRDChainLink L;
	for (int32 I = 0; I < DungeonChain.Num(); ++I) if (ChainLink(I, L) && RDKShort(L.Level) == Want) return I;
	return -1;
}

int32 ARDDungeonGenerator::ChainIndexOfKey(const FString& Key) const
{
	FRDChainLink L;
	for (int32 I = 0; I < DungeonChain.Num(); ++I) if (ChainLink(I, L) && L.Key == Key) return I;
	return -1;
}

bool ARDDungeonGenerator::HasDungeonKey(const FString& Level) const
{
	// (the first of the chain (Mistward Castle) and a level not in it need none)
	const int32 I = ChainIndexOfLevel(Level);
	FRDChainLink L;
	if (I <= 0 || !ChainLink(I, L)) return true;
	if (const URDGameInstance* GI = URDGameInstance::Of(this))
		if (GI->GetCounter(TEXT("dkey:all")) > 0 || GI->GetCounter(TEXT("dkey:") + L.Key) > 0) return true;
	// (-RDAllKeys: the packaged game's runs go down by -RDTownGo in the town's first ticks, before TickDungeonKeys has read it)
	if (FParse::Param(FCommandLine::Get(), TEXT("RDAllKeys"))) return true;
	return PlayerCombat && !L.KeyItem.IsNone() && PlayerCombat->GetItemCount(L.KeyItem) > 0;
}

FString ARDDungeonGenerator::DungeonLockedLine(const FString& Level) const
{
	const int32 I = ChainIndexOfLevel(Level);
	FRDChainLink L, Prev;
	if (I <= 0 || !ChainLink(I, L) || !ChainLink(I - 1, Prev)) return FString();
	return FString::Printf(TEXT("The way into %s is locked. Its key, the %s, is held by the master of %s."), *L.Title, *L.KeyItem.ToString(), *Prev.Title);
}

bool ARDDungeonGenerator::IsDungeonChainItem(FName Item) const
{
	if (Item.IsNone()) return false;
	FRDChainLink L;
	for (int32 I = 0; I < DungeonChain.Num(); ++I) if (ChainLink(I, L) && (L.KeyItem == Item || L.MapItem == Item)) return true;
	return false;
}

void ARDDungeonGenerator::DropNextDungeonKey(const FVector& At)
{
	// (this dungeon's place in the chain: its key (Mistward Castle's is empty); the next one's key and map lie where its boss fell)
	const int32 I = ChainIndexOfKey(DungeonKey);
	FRDChainLink Next;
	if (I < 0 || !ChainLink(I + 1, Next)) return;
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (GI && GI->GetCounter(TEXT("dkey:") + Next.Key) > 0) { UE_LOG(LogRDKeys, Log, TEXT("RDKEY %s's key taken already: none dropped"), *Next.Title); return; }
	TArray<FName> Things;
	for (const FName& N : { Next.KeyItem, Next.MapItem }) if (!N.IsNone() && FindItem(N) >= 0) Things.Add(N);
	if (Things.Num() == 0) { UE_LOG(LogRDKeys, Warning, TEXT("RDKEY %s's key and map are not items of this level (905)"), *Next.Title); return; }
	TArray<float> Wear; Wear.Init(-1.f, Things.Num());
	if (ARDLootPile* P = DropLoot(At + FVector(0, 0, 100.f), Things, Wear)) P->bHers = false;
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
	// (-RDAllKeys: every way open, read once a game instance (the packaged game's runs go down into each dungeon))
	if (!GI->bAllKeysRead) { GI->bAllKeysRead = true; if (FParse::Param(FCommandLine::Get(), TEXT("RDAllKeys"))) GI->Counters.Add(TEXT("dkey:all"), 1); }
	FRDChainLink L;
	for (int32 I = 1; I < DungeonChain.Num(); ++I)
	{
		if (!ChainLink(I, L)) continue;
		// (what she has had stays hers in the game's counters)
		if (!L.KeyItem.IsNone() && PlayerCombat->GetItemCount(L.KeyItem) > 0 && GI->GetCounter(TEXT("dkey:") + L.Key) == 0)
		{
			GI->CountMax(TEXT("dkey:") + L.Key, 1);
			UE_LOG(LogRDKeys, Log, TEXT("RDKEY taken: %s (opens %s)"), *L.KeyItem.ToString(), *L.Title);
		}
		if (!L.MapItem.IsNone() && PlayerCombat->GetItemCount(L.MapItem) > 0 && GI->GetCounter(TEXT("dmap:") + L.Town) == 0)
			GI->CountMax(TEXT("dmap:") + L.Town, 1);
		// (out in the wilds: a map taken shows its road and its town's land, once)
		if (bWild && IsWildReady() && GI->GetCounter(TEXT("dmap:") + L.Town) > 0 && GI->GetCounter(TEXT("dmapshown:") + L.Town) == 0)
		{
			FRDChainLink Prev;
			const int32 Cells = RevealRoute(ChainLink(I - 1, Prev) ? Prev.Town : FString(TEXT("Brokenspire")), L.Town);
			GI->CountMax(TEXT("dmapshown:") + L.Town, 1);
			if (Cells > 0) PlayerCombat->ShowMessage(FString::Printf(TEXT("Your map shows the way to %s."), *L.Town));
		}
	}
}

int32 ARDDungeonGenerator::RevealRoute(const FString& From, const FString& To)
{
	if (!IsWildReady()) return 0;
	int32 A = -1, B = -1;
	for (int32 T = 0; T < Wild->Towns.Num(); ++T)
	{
		if (Wild->Towns[T].Name == From) A = T;
		if (Wild->Towns[T].Name == To) B = T;
	}
	if (B < 0) { UE_LOG(LogRDKeys, Log, TEXT("RDKEY no town %s in this world: its map shows nothing yet"), *To); return 0; }
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
	if (URDGameInstance* GI = URDGameInstance::Of(this)) GI->Counters.Add(TEXT("dkey:all"), bOn ? 1 : 0);
}

TArray<FString> ARDDungeonGenerator::GetDungeonKeyLines() const
{
	TArray<FString> Out;
	const URDGameInstance* GI = URDGameInstance::Of(this);
	FRDChainLink L;
	for (int32 I = 0; I < DungeonChain.Num(); ++I)
		if (ChainLink(I, L))
			Out.Add(FString::Printf(TEXT("%d|%s|%s|%s|%s|%d|%d|%d|%d"), I, *L.Key, *L.Level, *L.Town, *L.KeyItem.ToString(), HasDungeonKey(L.Level) ? 1 : 0,
				GI ? GI->GetCounter(TEXT("dkey:") + L.Key) : 0, GI ? GI->GetCounter(TEXT("dmap:") + L.Town) : 0, GI ? GI->GetCounter(TEXT("dmapshown:") + L.Town) : 0));
	return Out;
}

int32 ARDDungeonGenerator::GetWildTierAt(float Xm, float Ym) const
{
	return IsWildReady() ? Wild->TierAt(Xm, Ym) : 0;
}
