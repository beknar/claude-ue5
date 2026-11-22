// The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), its eighteenth phase: the Shipping
// package's runs of the wilds (package_mistward.ps1's horse, village and cavetower): -RDTownGo=horse (3 km out, her horse called by the
// key's call, mounted and ridden 15 s ahead: "horse|<metres>|<still mounted>"), -RDTownGo=village (put down 300 m off the nearest village,
// found by the map's own discovery, travelled to by the map: "village|<name>|<people>"), -RDTownGo=cavetower (by the nearest broken
// tower, put down before its laid mouth, into its cave as F takes her: the caves level's own mark). Each plays the game's own ways (the
// key's call, the mount, her input, the discovery, the map's travel, F at the mouth); every put-down is the map's (WildPutDownNear:
// dry ground she can stand on) and checked.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDGameInstance.h"
#include "RD/RDTown.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/Character.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList15q, Log, All);

bool ARDDungeonGenerator::NearestTowerSite15(const FVector2D& FromM, int32 Ring, FVector2D& SiteM, double& DistM) const
{
	// (the nearest landmark tower's site within Ring of the 6 km squares round a point: one scan for the landmark laid, the treasure
	// maps' landmark and the package's run (PR #110's review: three copies))
	const int32 Ci = FMath::FloorToInt(FromM.X / WildLandmarkCellM), Cj = FMath::FloorToInt(FromM.Y / WildLandmarkCellM);
	DistM = 1e12; bool bGot = false;
	for (int32 I = Ci - Ring; I <= Ci + Ring; ++I) for (int32 J = Cj - Ring; J <= Cj + Ring; ++J)
	{
		FVector2D S;
		if (!WildTowerSite13(I, J, S)) continue;
		const double D = FVector2D::Distance(S, FromM);
		if (D < DistM) { DistM = D; SiteM = S; bGot = true; }
	}
	return bGot;
}

void ARDDungeonGenerator::TickGo15(APawn* P)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || GI->Go15.IsEmpty() || !P || !IsWildReady() || !GetWorld()) return;
	const float Now = GetWorld()->GetTimeSeconds();
	if (Now < GI->Go15At) return;
	const FVector2D Home = Wild->Towns.IsValidIndex(0) ? Wild->Towns[0].Site : FVector2D::ZeroVector;
	auto Fail = [&](const FString& Why) { UE_LOG(LogRDList15q, Warning, TEXT("RDGO15 %s refused: %s"), *GI->Go15, *Why); WriteTestMark(TEXT("refused"), GI->Go15 + TEXT(": ") + Why); GI->Go15.Reset(); };
	if (GI->Go15 == TEXT("horse"))
	{
		switch (GI->Go15Stage)
		{
		case 0:
			// (3 km out, then 250 m further at each try the call refuses (a roof, no room beside her): the map's put-down)
			GI->bHorseOwned = true;          // (the stable's purchase: the run tests the call and the ride, not the shop)
			if (!WildPutDownNear(Home + FVector2D(3000.0 + 250.0 * GI->Go15Try, 0.0))) { Fail(TEXT("no ground to stand on 3 km out")); return; }
			GI->Go15Stage = 1; GI->Go15At = Now + 4.f;
			return;
		case 1:
			if (!CallHorseByKey())          // (the player's call, J: its refusals are the game's)
			{
				if (++GI->Go15Try < 4) { GI->Go15Stage = 0; return; }
				Fail(TEXT("the horse would not come to the call")); return;
			}
			GI->Go15Stage = 2; GI->Go15At = Now + 2.f; return;
		case 2: if (!MountHorse()) { Fail(TEXT("not mounted")); return; } GI->Go15Stage = 3; GI->Go15At = Now + 3.f; return;
		case 3: GI->Go15From = P->GetActorLocation(); GI->Go15T0 = Now; GI->Go15Stage = 4; return;
		case 4:
			if (Now - GI->Go15T0 < 15.f) { P->AddMovementInput(FRotator(0.f, P->GetActorRotation().Yaw, 0.f).Vector(), 1.f); return; }
			{
				// (still on the horse, not swimming beside it (PR #110's review: IsRidingOrSwimming read a rider thrown into a river as mounted))
				const float M = FVector::Dist2D(P->GetActorLocation(), GI->Go15From) / 100.f;
				WriteTestMark(TEXT("horse"), FString::Printf(TEXT("%.0f|%d"), M, IsMounted() ? 1 : 0));
				UE_LOG(LogRDList15q, Log, TEXT("RDGO15 horse ridden %.0f m in 15 s, mounted %d"), M, IsMounted() ? 1 : 0);
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
			// (put down 300 m off the nearest village, inside the map's discovery (WildDiscoverM 500 m): found as a player finds it)
			FRDWildPlace V; FVector2D At;
			if (!FindNearestWildPlace(Home.X, Home.Y, 12.f, [](const FRDWildPlace& Pl, FVector2D& A) { if (Pl.Kind != TEXT("village")) return false; A = Pl.At; return true; }, V, At)) { Fail(TEXT("no village within 12 km")); return; }
			if (WildFound.Contains(V.Id)) { Fail(TEXT("the village was found before the run")); return; }
			if (!WildPutDownNear(V.At + FVector2D(300.0, 0.0))) { Fail(TEXT("no ground to stand on by the village")); return; }
			GI->Go15Id = V.Id; GI->Go15Name = V.Name; GI->Go15From = FVector(V.At.X * 100.0, V.At.Y * 100.0, 0.0); GI->Go15T0 = Now;
			GI->Go15Stage = 1; GI->Go15At = Now + 1.f;
			return;
		}
		case 1:
			if (!WildFound.Contains(GI->Go15Id))
			{
				if (Now - GI->Go15T0 > 30.f) Fail(TEXT("not found in 30 s 300 m off it")); else GI->Go15At = Now + 1.f;
				return;
			}
			{
				// (the map's travel to it (bTravelForced only passes the refusal for enemies near: a run cannot wait out a fight))
				bTravelForced = true;
				const bool bOk = WildFastTravel(GI->Go15Id);
				bTravelForced = false;
				if (!bOk) { Fail(WildTravelRefusal); return; }
			}
			GI->Go15T0 = Now; GI->Go15Stage = 2; GI->Go15At = Now + 2.f;
			return;
		case 2:
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
			// (the nearest broken tower's site to Brokenspire, she put down 40 m off it by the map's put-down)
			FVector2D Site; double D;
			if (!NearestTowerSite15(Home, 3, Site, D)) { Fail(TEXT("no broken tower near")); return; }
			if (!WildPutDownNear(Site + FVector2D(40.0, 0.0))) { Fail(TEXT("no ground to stand on by the tower")); return; }
			GI->Go15From = FVector(Site.X * 100.0, Site.Y * 100.0, 0.0);
			GI->Go15Stage = 1; GI->Go15At = Now + 4.f; GI->Go15T0 = Now;
			return;
		}
		case 1:
		{
			// (its mouth laid with the tower (the mouth's own component, not its last place: PR #110's review): she is put down before it, on the
			// ground there, by the game's put-down)
			if (!CaveMouth15.IsValid() || FVector::Dist2D(CaveMouthAt15, GI->Go15From) > 3000.f)
			{
				if (Now - GI->Go15T0 > 60.f) Fail(TEXT("the tower's mouth was not laid"));
				else GI->Go15At = Now + 1.f;
				return;
			}
			const FVector Stand = CaveMouthAt15 + CaveMouthOut15 * 150.f;
			if (!WildPutHer((float)(Stand.X / 100.0), (float)(Stand.Y / 100.0))) { Fail(TEXT("not put down before the mouth")); return; }
			GI->Go15Stage = 2; GI->Go15At = Now + 1.f;
			return;
		}
		case 2:
		{
			if (!CaveMouthNear15(P->GetActorLocation())) { Fail(FString::Printf(TEXT("not before the mouth: %.0f cm off it"), FVector::Dist2D(P->GetActorLocation(), CaveMouthAt15))); return; }
			const FString F = InteractNearest(P->GetActorLocation());
			UE_LOG(LogRDList15q, Log, TEXT("RDGO15 cavetower: F at the mouth -> %s"), *F);
			if (F != TEXT("cave")) Fail(FString::Printf(TEXT("F took %s, not the cave"), *F));
			else GI->Go15.Reset();          // (the caves level's own mark says it opened)
			return;
		}
		}
	}
}
