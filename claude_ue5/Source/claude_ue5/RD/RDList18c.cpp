// The user's list of 2026-11-27 (docs/improvements18.txt; the plan docs/improvements18_plan.md), its fourth phase: "in the cities, the vendor
// stands in the town square all have the same design. Have at least 20 different designs for vendor stands designs."
//   - 20 medieval and 20 modern (Heaven's) designs (SourceArt/list18/stalls18.json, 951 stalls): each a list of parts, every part a piece of
//     the generator's table (Stall18.<design>.<n>: a pack's mesh, a Blueprint, or the engine's cube in one of Heaven's materials) placed in
//     the stand's frame (its counter +X, the keeper behind at -X), all within the stands' 2.6 m square; each names the trades it suits.
//   - A square's twelve stands take twelve different designs suiting their trades, matched from a hash of the town's seed (StallDesigns18,
//     PickStalls18); the old four's draw from the outdoors stream is still drawn, so nothing after it moves. rd.Stalls18 0 lays the three
//     stands of before.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "HAL/IConsoleManager.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList18c, Log, All);

bool RDStalls17On();

namespace
{
	TAutoConsoleVariable<int32> CVarRDStalls18(TEXT("rd.Stalls18"), 1, TEXT("The squares' stands of twenty designs each style (1), or the three stands of before (0); a town planned after the change"));
	FIntPoint RDL18cKey(const FVector& At) { return FIntPoint(FMath::RoundToInt(At.X), FMath::RoundToInt(At.Y)); }
}

void ARDSection::PickStalls18()
{
	// (the stands in the plan's order, each a trade (Bld & 15); the designs of the town's style shuffled by the town's seed, and every stand
	// given one suiting its trade, all different: a matching by augmenting paths, so a trade with few designs still gets one)
	bStalls18Picked = true; Stalls18.Reset();
	if (!Generator) return;
	const TArray<FRDStallDesign18>& Ds = Generator->StallDesigns18;
	const bool bModern = Generator->TownPlan == 5;
	TArray<int32> Cand;
	for (int32 I = 0; I < Ds.Num(); ++I) if (Ds[I].bModern == bModern && Ds[I].Parts.Num() > 0) Cand.Add(I);
	FRandomStream R(HashCombine((uint32)Seed, 0x5718u));
	for (int32 I = Cand.Num() - 1; I > 0; --I) Cand.Swap(I, R.RandRange(0, I));
	TArray<const FTownSpot*> Spots;
	for (const FTownSpot& Sp : TownSpots) if (Sp.Kind == TS_Stall) Spots.Add(&Sp);
	auto Suits = [&](int32 Di, int32 Trade) { return Ds[Di].Trades.Num() == 0 || Ds[Di].Trades.Contains(Trade); };
	TArray<int32> OwnerOf; OwnerOf.Init(-1, Cand.Num());          // (a candidate's stand)
	TFunction<bool(int32, TArray<bool>&)> Try = [&](int32 Si, TArray<bool>& Seen) -> bool
	{
		const int32 Trade = Spots[Si]->Bld & 15;
		for (int32 C = 0; C < Cand.Num(); ++C)
		{
			if (Seen[C] || !Suits(Cand[C], Trade)) continue;
			Seen[C] = true;
			if (OwnerOf[C] < 0 || Try(OwnerOf[C], Seen)) { OwnerOf[C] = Si; return true; }
		}
		return false;
	};
	int32 Unmatched = 0;
	for (int32 Si = 0; Si < Spots.Num(); ++Si) { TArray<bool> Seen; Seen.Init(false, Cand.Num()); if (!Try(Si, Seen)) ++Unmatched; }
	for (int32 C = 0; C < Cand.Num(); ++C) if (OwnerOf[C] >= 0) Stalls18.Add(RDL18cKey(Spots[OwnerOf[C]]->At), Cand[C]);
	// (a stand no design could take (more stands than designs for its trades): any design not yet on the square, else any of its style)
	for (const FTownSpot* Sp : Spots)
	{
		if (Stalls18.Contains(RDL18cKey(Sp->At)) || Cand.Num() == 0) continue;
		TArray<int32> Used; Stalls18.GenerateValueArray(Used);
		const int32* Free = Cand.FindByPredicate([&](int32 Di) { return !Used.Contains(Di); });
		Stalls18.Add(RDL18cKey(Sp->At), Free ? *Free : Cand[0]);
	}
	UE_LOG(LogRDList18c, Log, TEXT("RDSTALLS18 %d stands, %d designs of the %s style, %d unmatched by trade"), Spots.Num(), Cand.Num(), bModern ? TEXT("modern") : TEXT("medieval"), Unmatched);
}

int32 ARDSection::StallDesign18At(const FVector& At) const
{
	const int32* D = Stalls18.Find(RDL18cKey(At));
	return D ? *D : -1;
}

bool ARDSection::LayStall18(const FTownSpot& Sp)
{
	// (with rd.Stalls17 0 the square keeps the four stands of before, as they were (PR #149's review))
	if (!Generator || CVarRDStalls18.GetValueOnGameThread() == 0 || !RDStalls17On() || Generator->StallDesigns18.Num() == 0) return false;
	if (!bStalls18Picked) PickStalls18();
	const int32* D = Stalls18.Find(RDL18cKey(Sp.At));
	if (!D || !Generator->StallDesigns18.IsValidIndex(*D)) return false;
	const FRDStallDesign18& Ds = Generator->StallDesigns18[*D];
	const FTransform St(FRotator(0, Sp.Yaw, 0), Sp.At);
	for (int32 K = 0; K < Ds.Parts.Num(); ++K) AddPiece(Ds.Parts[K], (Ds.PartXf.IsValidIndex(K) ? Ds.PartXf[K] : FTransform::Identity) * St);
	return true;
}

TArray<FString> ARDDungeonGenerator::GetStalls18() const
{
	// (tests: "<x>|<y>|<yaw>|<trade>|<design index>|<design id>|<parts>" a stand of the town's square)
	TArray<FString> Out;
	const ARDSection* S = const_cast<ARDDungeonGenerator*>(this)->GetSection(FIntPoint::ZeroValue);
	if (!S) return Out;
	for (const ARDSection::FTownSpot& Sp : S->TownSpots)
	{
		if (Sp.Kind != TS_Stall) continue;
		const int32 D = S->StallDesign18At(Sp.At);
		const bool bOk = StallDesigns18.IsValidIndex(D);
		Out.Add(FString::Printf(TEXT("%.0f|%.0f|%.1f|%d|%d|%s|%d"), Sp.At.X, Sp.At.Y, Sp.Yaw, Sp.Bld & 15, bOk ? D : -1,
			bOk ? *StallDesigns18[D].Id.ToString() : TEXT("-"), bOk ? StallDesigns18[D].Parts.Num() : 0));
	}
	return Out;
}
