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
	const FString Bn = Wild->Biomes.IsValidIndex(P.Biome) ? Wild->Biomes[P.Biome].Name : FString();
	float Sum = 0.f;
	TArray<float> W; W.SetNumZeroed(WildLairCovers.Num());
	for (int32 I = 0; I < WildLairCovers.Num(); ++I)
	{
		const FRDWildRuinKind& K = WildLairCovers[I];
		if (!K.Biomes.Contains(TEXT("*")) && !K.Biomes.Contains(Bn)) continue;
		W[I] = FMath::Max(K.Weight, 0.f); Sum += W[I];
	}
	if (Sum <= 0.f) return -1;
	float Pick = (FRDWildWorld::Hash(P.Id, 0x1215, Wild->Seed) & 0xFFFFFF) / float(0x1000000) * Sum;
	for (int32 I = 0; I < W.Num(); ++I) { if (W[I] <= 0.f) continue; if (Pick < W[I]) return I; Pick -= W[I]; }
	for (int32 I = W.Num() - 1; I >= 0; --I) if (W[I] > 0.f) return I;
	return -1;
}

void ARDDungeonGenerator::LayWildLair(ARDWildChunk* C, const FRDWildPlace& P, const FRDWildRuinKind& K)
{
	if (!C || !Wild) return;
	FRandomStream R((int32)FRDWildWorld::Hash(P.Id, 0x1214, Wild->Seed));
	FRuinLaid Rec; Rec.Id = P.Id; Rec.Yaw = P.Yaw; Rec.At = P.At; Rec.Name = P.Name;
	Rec.Kind = WildLairCovers.IndexOfByPredicate([&](const FRDWildRuinKind& X) { return X.Name == K.Name; });
	LayWildParts(C, P, K, P.At, P.At, P.Yaw, R, (4LL << 40), Rec);
	const float Gy = FMath::DegreesToRadians(P.Yaw + K.GapYaw);
	Rec.Exit = P.At + FVector2D(FMath::Cos(Gy), FMath::Sin(Gy)) * (K.HideR + 3.f);
	WildLairsLaid.RemoveAll([&](const FRuinLaid& X) { return X.Id == P.Id; });
	WildLairsLaid.Add(Rec);
	UE_LOG(LogRDLair12, Log, TEXT("RDLAIR %s (%s): %d pieces at (%.0f, %.0f)"), *P.Name, *K.Name.ToString(), Rec.Pieces, P.At.X, P.At.Y);
}

TArray<FString> ARDDungeonGenerator::GetWildLairLines() const
{
	TArray<FString> Out;
	for (const FRuinLaid& X : WildLairsLaid)
		Out.Add(FString::Printf(TEXT("lair|%d|%s|%.1f|%.1f|%d|%.1f|%.1f|%s|%.1f"), X.Id, WildLairCovers.IsValidIndex(X.Kind) ? *WildLairCovers[X.Kind].Name.ToString() : TEXT("?"),
			X.At.X, X.At.Y, X.Pieces, X.Exit.X, X.Exit.Y, *X.Name, X.Yaw));
	return Out;
}

TArray<FString> ARDDungeonGenerator::GetWildLairPieceLines(int32 Id) const
{
	return PieceLinesOf(WildLairsLaid.FindByPredicate([&](const FRuinLaid& R) { return R.Id == Id; }));
}

FString ARDDungeonGenerator::FindWildLair(FName Cover, float X, float Y, float MaxKm) const
{
	if (!Wild) return FString();
	const int32 Want = WildLairCovers.IndexOfByPredicate([&](const FRDWildRuinKind& K) { return K.Name == Cover; });
	if (Want < 0) return FString();
	const FIntPoint C0 = Wild->PlaceCellOf(X, Y);
	const int32 Rmax = FMath::CeilToInt(MaxKm * 1000.0 / FRDWildWorld::PlaceCellM);
	for (int32 Ring = 0; Ring <= Rmax; ++Ring)
	{
		float Best = 1e18f; FString Got;
		for (int32 I = -Ring; I <= Ring; ++I)
			for (int32 J = -Ring; J <= Ring; ++J)
			{
				if (FMath::Max(FMath::Abs(I), FMath::Abs(J)) != Ring) continue;
				TArray<FRDWildPlace> Ps; Wild->PlacesIn(C0 + FIntPoint(I, J), Ps);
				for (const FRDWildPlace& P : Ps)
				{
					if (P.Kind != TEXT("lair") || WildLairCoverOf(P) != Want) continue;
					const float D = FVector2D::DistSquared(P.At, FVector2D(X, Y));
					if (D < Best) { Best = D; Got = FString::Printf(TEXT("%d|%.1f|%.1f|%.1f|%s"), P.Id, P.At.X, P.At.Y, P.Yaw, *P.Name); }
				}
			}
		if (!Got.IsEmpty()) return Got;
	}
	return FString();
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
