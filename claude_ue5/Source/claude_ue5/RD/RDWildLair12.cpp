// The list of 2026-11-12's fourth phase: the lairs hidden ("monster lairs do not have any special structure around them. they
// should be hiding behind something, a stand of trees, a ruin, a cave, an abandoned house, an earth berm, something that can hide
// them from sight so that they're not just out in the open"). A wild place of kind "lair" gets a cover of WildLairCovers (924
// lairs, from SourceArt/wilderness/lairs12.json) chosen from its id among the covers of its biome, laid round it by the ruins'
// layout language (RDWildRuin12.cpp's LayWildParts: groves, thickets, walls, a cave's mouth, a roofless house, an earth bank);
// its monsters stand and wander inside it (ARDMonster::CoverR) and come out through its opening (CoverExit) after her.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDMonster.h"
#include "RD/RDSection.h"
#include "Components/StaticMeshComponent.h"
#include "ProceduralMeshComponent.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDLair12, Log, All);

int32 ARDDungeonGenerator::WildLairCoverOf(const FRDWildPlace& P) const
{
	if (!Wild || P.Kind != TEXT("lair") || !P.Quest.IsEmpty() || WildLairCovers.Num() == 0) return -1;
	// (once a place, as the ruins' kinds: the one pick by biome and weight they share (PR #57's review))
	if (const int32* Got = WildLairPicks.Find(P.Id)) return *Got;
	return WildLairPicks.Add(P.Id, PickWildKind(WildLairCovers, P, 0x1215, false));
}

FVector2D ARDDungeonGenerator::WildLairMiddle(const FRDWildPlace& P) const
{
	if (!Wild) return P.At;
	// (the den's ground by its relief: the most the land rises or falls 8 m from it, eight ways (metres): a slope read 3 m round a
	// point missed the canyons' terraces, where a lair's boulders stood a storey apart)
	auto Dry = [&](const FVector2D& A) { FRDWSample S; Wild->Sample(A.X, A.Y, S, false); return S.WaterKind == 0 || S.Water <= S.H; };
	if (const FVector2D* Got = WildLairDens.Find(P.Id)) return *Got;
	const float R0 = WildLairRelief(P.At);
	if (R0 <= 2.5f) return WildLairDens.Add(P.Id, P.At);
	// (rings every 5 m out to 40, eight ways: the dry point of the least relief)
	FVector2D Best = P.At; float BestR = R0;
	for (float Rr = 5.f; Rr <= 40.f; Rr += 5.f)
		for (int32 I = 0; I < 8; ++I)
		{
			const FVector2D A = P.At + FVector2D(FMath::Cos(I * PI / 4.f), FMath::Sin(I * PI / 4.f)) * Rr;
			if (!Dry(A)) continue;
			const float Rl = WildLairRelief(A);
			if (Rl < BestR - 0.2f) { BestR = Rl; Best = A; }
		}
	return WildLairDens.Add(P.Id, Best);
}

float ARDDungeonGenerator::WildLairRelief(const FVector2D& A) const
{
	if (!Wild) return 0.f;
	FRDWSample S0; Wild->Sample(A.X, A.Y, S0, false);
	float M = 0.f;
	for (int32 I = 0; I < 8; ++I)
	{
		FRDWSample S; Wild->Sample(A.X + FMath::Cos(I * PI / 4.f) * 8.0, A.Y + FMath::Sin(I * PI / 4.f) * 8.0, S, false);
		M = FMath::Max(M, FMath::Abs(S.H - S0.H));
	}
	return M;
}

void ARDDungeonGenerator::LayWildLair(ARDWildChunk* C, const FRDWildPlace& P, const FRDWildRuinKind& K)
{
	if (!C || !Wild) return;
	FRandomStream R((int32)FRDWildWorld::Hash(P.Id, 0x1214, Wild->Seed));
	// (its den on ground she and its monsters can stand on: on a mountain's face (a harpy lair's boulders 13 m apart in height) its
	// monsters slid out of the cover; the world is not reshaped, so the den moves to the gentlest ground within 40 m)
	const FVector2D O = WildLairMiddle(P);
	FRuinLaid Rec; Rec.Id = P.Id; Rec.Yaw = P.Yaw; Rec.At = O; Rec.Name = P.Name;
	Rec.Kind = WildLairCovers.IndexOfByPredicate([&](const FRDWildRuinKind& X) { return X.Name == K.Name; });
	LayWildParts(C, P, K, O, O, P.Yaw, R, (4LL << 40), Rec);
	// (its reach: the farthest of the pieces that stop her, by their boxes' middles and their thin half (1 m at most: a tree's box
	// is its crown, its trunk is what stops her); an earth bank's whole half; its way out 2.5 m past that, on its opening's way (every cover opens at its
	// frame's 0 degrees: its arcs are centred on 180))
	Rec.OutR = K.HideR;
	for (const TWeakObjectPtr<UPrimitiveComponent>& W : Rec.Comps)
		if (const UPrimitiveComponent* Pc = W.Get())
		{
			if (Pc->GetCollisionEnabled() != ECollisionEnabled::QueryAndPhysics || Pc->GetCollisionResponseToChannel(ECC_Pawn) != ECR_Block) continue;
			const FBox B = Pc->Bounds.GetBox();
			const FVector E = B.GetExtent();
			const float Half = Pc->IsA<UStaticMeshComponent>() ? FMath::Min3((float)E.X, (float)E.Y, 100.f) : FMath::Min((float)E.X, (float)E.Y);
			Rec.OutR = FMath::Max(Rec.OutR, (float)(FVector2D::Distance(FVector2D(B.GetCenter().X, B.GetCenter().Y) / 100.0, O) + Half / 100.0));
		}
	const float Gy = FMath::DegreesToRadians(P.Yaw + K.GapYaw);
	Rec.Exit = O + FVector2D(FMath::Cos(Gy), FMath::Sin(Gy)) * (Rec.OutR + 2.5f);
	WildLairsLaid.RemoveAll([&](const FRuinLaid& X) { return X.Id == P.Id; });
	WildLairsLaid.Add(Rec);
	UE_LOG(LogRDLair12, Log, TEXT("RDLAIR %s (%s): %d pieces at (%.0f, %.0f)"), *P.Name, *K.Name.ToString(), Rec.Pieces, P.At.X, P.At.Y);
}

TArray<FString> ARDDungeonGenerator::GetWildLairLines() const
{
	TArray<FString> Out;
	for (const FRuinLaid& X : WildLairsLaid)
		Out.Add(FString::Printf(TEXT("lair|%d|%s|%.1f|%.1f|%d|%.1f|%.1f|%s|%.1f|%.1f"), X.Id, WildLairCovers.IsValidIndex(X.Kind) ? *WildLairCovers[X.Kind].Name.ToString() : TEXT("?"),
			X.At.X, X.At.Y, X.Pieces, X.Exit.X, X.Exit.Y, *X.Name, X.Yaw, X.OutR));
	return Out;
}

TArray<FString> ARDDungeonGenerator::GetWildLairPieceLines(int32 Id) const
{
	return PieceLinesOf(WildLairsLaid.FindByPredicate([&](const FRuinLaid& R) { return R.Id == Id; }));
}

FString ARDDungeonGenerator::FindWildLair(FName Cover, float X, float Y, float MaxKm, float MaxReliefM) const
{
	if (!Wild) return FString();
	const int32 Want = WildLairCovers.IndexOfByPredicate([&](const FRDWildRuinKind& K) { return K.Name == Cover; });
	if (Want < 0) return FString();
	FRDWildPlace Got; FVector2D At;
	// (MaxReliefM: only one whose den's ground rises or falls no more than that within 8 m)
	if (!FindNearestWildPlace(X, Y, MaxKm, [&](const FRDWildPlace& P, FVector2D& A) { A = P.At; return P.Kind == TEXT("lair") && WildLairCoverOf(P) == Want && (MaxReliefM >= 999.f || WildLairRelief(WildLairMiddle(P)) <= MaxReliefM); }, Got, At)) return FString();
	return FString::Printf(TEXT("%d|%.1f|%.1f|%.1f|%s"), Got.Id, At.X, At.Y, Got.Yaw, *Got.Name);
}

TArray<FString> ARDDungeonGenerator::CountWildLairs(float X, float Y, float MaxKm) const
{
	TArray<FString> Out;
	if (!Wild) return Out;
	TArray<int32> N; N.SetNumZeroed(WildLairCovers.Num() + 1);
	const FIntPoint C0 = Wild->PlaceCellOf(X, Y);
	const int32 Rmax = FMath::CeilToInt(MaxKm * 1000.0 / FRDWildWorld::PlaceCellM);
	for (int32 I = -Rmax; I <= Rmax; ++I)
		for (int32 J = -Rmax; J <= Rmax; ++J)
		{
			TArray<FRDWildPlace> Ps; Wild->PlacesIn(C0 + FIntPoint(I, J), Ps);
			for (const FRDWildPlace& P : Ps) if (P.Kind == TEXT("lair") && P.Quest.IsEmpty()) { const int32 K = WildLairCoverOf(P); N[K >= 0 ? K : WildLairCovers.Num()]++; }
		}
	for (int32 K = 0; K < WildLairCovers.Num(); ++K) Out.Add(FString::Printf(TEXT("%s|%d"), *WildLairCovers[K].Name.ToString(), N[K]));
	Out.Add(FString::Printf(TEXT("none|%d"), N.Last()));
	return Out;
}

FString ARDDungeonGenerator::WildLairSight(int32 Id, float DistM, int32 Ways) const
{
	const FRuinLaid* X = WildLairsLaid.FindByPredicate([&](const FRuinLaid& Rr) { return Rr.Id == Id; });
	if (!X || !WildLairCovers.IsValidIndex(X->Kind) || !WildSection) return TEXT("0|0|0|0");
	const float HideCm = (WildLairCovers[X->Kind].HideR + 2.f) * 100.f;
	const FVector Mid(X->At.X * 100.0, X->At.Y * 100.0, 0.0);
	TArray<const ARDMonster*> Ms;
	TArray<const AActor*> Ignore;
	for (const TObjectPtr<ARDMonster>& M : WildSection->SpawnedMonsters)
	{
		if (!IsValid(M) || M->IsDead()) continue;
		Ignore.Add(M);
		if (FVector::Dist2D(M->GetActorLocation(), Mid) < HideCm) Ms.Add(M);
	}
	if (const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0)) Ignore.Add(Her);
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDLairSight), true);
	for (const AActor* A : Ignore) Q.AddIgnoredActor(A);
	int32 Lines = 0, Blocked = 0, Other = 0;
	Ways = FMath::Clamp(Ways, 1, 64);
	for (int32 W = 0; W < Ways; ++W)
	{
		const float A = 2.f * PI * W / Ways;
		FVector Eye = Mid + FVector(FMath::Cos(A), FMath::Sin(A), 0.0) * DistM * 100.f;
		Eye.Z = WildGroundZ(Eye) + 170.f;
		for (const ARDMonster* M : Ms)
		{
			const FVector L = M->GetActorLocation();
			const float Feet = L.Z - M->GetSimpleCollisionHalfHeight();
			for (const float Up : { 50.f, 110.f, 170.f })
			{
				const FVector T(L.X, L.Y, Feet + Up);
				++Lines;
				bool bCover = false;
				for (const TWeakObjectPtr<UPrimitiveComponent>& Wc : X->Comps)
				{
					UPrimitiveComponent* Pc = Wc.Get();
					FHitResult H;
					if (Pc && Pc->LineTraceComponent(H, Eye, T, Q)) { bCover = true; break; }
				}
				if (bCover) { ++Blocked; continue; }
				FHitResult H;
				if (GetWorld()->LineTraceSingleByChannel(H, Eye, T, ECC_Visibility, Q)) ++Other;
			}
		}
	}
	return FString::Printf(TEXT("%d|%d|%d|%d"), Blocked, Lines, Ms.Num(), Other);
}
