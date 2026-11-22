// The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), its eighteenth phase: the Shipping
// package's runs of the wilds (package_mistward.ps1's horse, village and cavetower): -RDTownGo=horse (3 km out, her horse called, mounted
// and ridden 15 s ahead: "horse|<metres>|<still mounted>"), -RDTownGo=village (to the nearest village by the map's travel, its households
// standing: "village|<name>|<people>"), -RDTownGo=cavetower (by the nearest broken tower, into its cave by its mouth as F takes her: the
// caves level's own mark). Each plays the game's own ways (the call, the mount, her input, the map's travel, F at the mouth).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDGameInstance.h"
#include "RD/RDTown.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/Character.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList15q, Log, All);

static bool RDQ15DrySpot(const FRDWildWorld& W, const FVector2D& Near, FVector2D& Out)
{
	// (dry, gentle ground off the roads near a point: rings out from it)
	for (int32 R = 0; R < 12; ++R)
		for (int32 K = 0; K < 12; ++K)
		{
			const FVector2D Q = Near + FVector2D(FMath::Cos(K * PI / 6.0), FMath::Sin(K * PI / 6.0)) * (R * 40.0);
			FRDWSample S; W.Sample(Q.X, Q.Y, S, false);
			if (S.WaterKind != 0 || S.Road > 0.05f || S.Lava > 0.02f || S.Field > 0.3f) continue;
			const double H0 = W.Height(Q.X, Q.Y);
			bool bSteep = false;
			for (int32 J = 0; J < 4 && !bSteep; ++J) bSteep = FMath::Abs(W.Height(Q.X + 5.0 * FMath::Cos(J * PI / 2.0), Q.Y + 5.0 * FMath::Sin(J * PI / 2.0)) - H0) > 1.2;
			if (!bSteep) { Out = Q; return true; }
		}
	return false;
}

void ARDDungeonGenerator::TickGo15(APawn* P)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || GI->Go15.IsEmpty() || !P || !IsWildReady() || !GetWorld()) return;
	const float Now = GetWorld()->GetTimeSeconds();
	if (Now < GI->Go15At) return;
	const FVector2D Home = Wild->Towns.IsValidIndex(0) ? Wild->Towns[0].Site : FVector2D::ZeroVector;
	auto Fail = [&](const TCHAR* Why) { UE_LOG(LogRDList15q, Warning, TEXT("RDGO15 %s refused: %s"), *GI->Go15, Why); GI->Go15.Reset(); };
	if (GI->Go15 == TEXT("horse"))
	{
		switch (GI->Go15Stage)
		{
		case 0:
		{
			FVector2D At;
			if (!RDQ15DrySpot(*Wild, Home + FVector2D(3000.0, 0.0), At)) { Fail(TEXT("no dry ground 3 km out")); return; }
			GI->bHorseOwned = true;          // (the stable's purchase: the run tests the ride, not the shop)
			WildPutHer(At.X, At.Y);
			GI->Go15Stage = 1; GI->Go15At = Now + 4.f;
			return;
		}
		case 1: if (!CallHorse()) { Fail(TEXT("the horse was not called")); return; } GI->Go15Stage = 2; GI->Go15At = Now + 2.f; return;
		case 2: if (!MountHorse()) { Fail(TEXT("not mounted")); return; } GI->Go15Stage = 3; GI->Go15At = Now + 3.f; return;
		case 3: GI->Go15From = P->GetActorLocation(); GI->Go15T0 = Now; GI->Go15Stage = 4; return;
		case 4:
			if (Now - GI->Go15T0 < 15.f) { P->AddMovementInput(FRotator(0.f, P->GetActorRotation().Yaw, 0.f).Vector(), 1.f); return; }
			{
				const float M = FVector::Dist2D(P->GetActorLocation(), GI->Go15From) / 100.f;
				WriteTestMark(TEXT("horse"), FString::Printf(TEXT("%.0f|%d"), M, IsRidingOrSwimming() ? 1 : 0));
				UE_LOG(LogRDList15q, Log, TEXT("RDGO15 horse ridden %.0f m in 15 s"), M);
				GI->Go15.Reset();
			}
			return;
		}
	}
	else if (GI->Go15 == TEXT("village"))
	{
		switch (GI->Go15Stage)
		{
		case 0:
		{
			FRDWildPlace V; FVector2D At;
			if (!FindNearestWildPlace(Home.X, Home.Y, 12.f, [](const FRDWildPlace& Pl, FVector2D& A) { if (Pl.Kind != TEXT("village")) return false; A = Pl.At; return true; }, V, At)) { Fail(TEXT("no village within 12 km")); return; }
			WildFound.Add(V.Id);
			bTravelForced = true;
			const bool bOk = WildFastTravel(V.Id);
			bTravelForced = false;
			if (!bOk) { Fail(*WildTravelRefusal); return; }
			GI->Go15Name = V.Name; GI->Go15From = FVector(V.At.X * 100.0, V.At.Y * 100.0, 0.0); GI->Go15T0 = Now;
			GI->Go15Stage = 1; GI->Go15At = Now + 2.f;
			return;
		}
		case 1:
		{
			// (its households standing within 300 m of its middle: the run's proof it was laid, as she sees it)
			int32 N = 0;
			for (const TWeakObjectPtr<ARDTownsfolk>& W : WildVillageFolk15) if (const ARDTownsfolk* T = W.Get(); IsValid(T) && FVector::Dist2D(T->GetActorLocation(), GI->Go15From) < 30000.f) ++N;
			if (N > 0) { WriteTestMark(TEXT("village"), FString::Printf(TEXT("%s|%d"), *GI->Go15Name, N)); UE_LOG(LogRDList15q, Log, TEXT("RDGO15 village %s: %d people"), *GI->Go15Name, N); GI->Go15.Reset(); return; }
			if (Now - GI->Go15T0 > 60.f) { Fail(TEXT("no household stood in 60 s")); return; }
			GI->Go15At = Now + 1.f;
			return;
		}
		}
	}
	else if (GI->Go15 == TEXT("cavetower"))
	{
		switch (GI->Go15Stage)
		{
		case 0:
		{
			// (the nearest broken tower's site to Brokenspire, she put 40 m off it on dry ground)
			FVector2D Best(0, 0); double Bd = 1e12;
			const int32 Ci = FMath::FloorToInt(Home.X / WildLandmarkCellM), Cj = FMath::FloorToInt(Home.Y / WildLandmarkCellM);
			for (int32 I = Ci - 3; I <= Ci + 3; ++I) for (int32 J = Cj - 3; J <= Cj + 3; ++J) { FVector2D S; if (WildTowerSite13(I, J, S) && FVector2D::Distance(S, Home) < Bd) { Bd = FVector2D::Distance(S, Home); Best = S; } }
			FVector2D At;
			if (Bd > 1e11 || !RDQ15DrySpot(*Wild, Best + FVector2D(40.0, 0.0), At)) { Fail(TEXT("no broken tower near")); return; }
			GI->Go15From = FVector(Best.X * 100.0, Best.Y * 100.0, 0.0);
			WildPutHer(At.X, At.Y);
			GI->Go15Stage = 1; GI->Go15At = Now + 4.f; GI->Go15T0 = Now;
			return;
		}
		case 1:
		{
			// (its mouth laid with the tower: she stands before it and F takes her in, as a player's press)
			if (CaveMouthAt15.IsZero() || FVector::Dist2D(CaveMouthAt15, GI->Go15From) > 3000.f)
			{
				if (Now - GI->Go15T0 > 60.f) Fail(TEXT("the tower's mouth was not laid"));
				else GI->Go15At = Now + 1.f;
				return;
			}
			const FVector Stand = CaveMouthAt15 + CaveMouthOut15 * 150.f + FVector(0, 0, 100.f);
			P->SetActorLocation(Stand, false, nullptr, ETeleportType::TeleportPhysics);
			GI->Go15Stage = 2; GI->Go15At = Now + 1.f;
			return;
		}
		case 2:
		{
			const FString F = InteractNearest(P->GetActorLocation());
			UE_LOG(LogRDList15q, Log, TEXT("RDGO15 cavetower: F at the mouth -> %s"), *F);
			if (F != TEXT("cave")) Fail(*FString::Printf(TEXT("F took %s, not the cave"), *F));
			else GI->Go15.Reset();          // (the caves level's own mark says it opened)
			return;
		}
		}
	}
}
