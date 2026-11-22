// The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), its seventeenth phase: preparing for regions
// (docs/wilderness_ideas.md's idea 7).
//   - The cold (the list of 2026-11-14's tenth phase, RDWildScenery13.cpp) builds up more slowly in warm gear (ClimateGear15: an armour set's
//     warmth) and with a warm meal's buff ("warm": ERDItemKind::Warmth), at the rate 1 - their sum (a tenth at least).
//   - The heat: in WildHeatBiomes15 by day (HeatFrom15 to HeatTo15), away from shade (something over her head), water (wading) and a town,
//     she grows hot as she grows cold in the cold, more slowly with cool gear and a cool drink's buff ("cool": ERDItemKind::Cooling), faster
//     in heavy plate; past HeatSeconds15 the heat saps her every 15 s until she is out of it.
//   - The regions' herbs (ClimateHerbs15: Frostleaf in the cold regions, Sandroot in the hot ones) come in their resource points' piles; the
//     oven cooks them with game into the warm stew and the cool drink (943's items and recipes).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDCombat.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList15p, Log, All);

void ARDDungeonGenerator::GearClimate15(float& Warm, float& Cool) const
{
	// (the armour she wears: its warmth against the cold and its coolness in the heat (heavy plate's below 0: hotter); the table parsed once
	// (PR #109's review: every look split its twenty lines))
	Warm = Cool = 0.f;
	if (!PlayerCombat) return;
	if (ClimateGearFor15 != ClimateGear15.Num())
	{
		ClimateGearFor15 = ClimateGear15.Num();
		ClimateGearMap15.Reset();
		for (const FString& L : ClimateGear15)
		{
			TArray<FString> F; L.ParseIntoArray(F, TEXT("|"), false);
			if (F.Num() >= 3) ClimateGearMap15.Add(FName(*F[0]), FVector2D(FCString::Atof(*F[1]), FCString::Atof(*F[2])));
		}
	}
	if (const FVector2D* G = ClimateGearMap15.Find(PlayerCombat->GetWornArmour())) { Warm = (float)G->X; Cool = (float)G->Y; }
}

float ARDDungeonGenerator::ColdRate15() const
{
	float Warm, Cool; GearClimate15(Warm, Cool);
	const float Buff = PlayerCombat ? PlayerCombat->GetClimateBuff15(ERDItemKind::Warmth) : 0.f;
	return FMath::Clamp(1.f - Warm - Buff, 0.1f, 1.5f);
}

float ARDDungeonGenerator::HeatRate15() const
{
	float Warm, Cool; GearClimate15(Warm, Cool);
	const float Buff = PlayerCombat ? PlayerCombat->GetClimateBuff15(ERDItemKind::Cooling) : 0.f;
	return FMath::Clamp(1.f - Cool - Buff, 0.1f, 1.5f);
}

void ARDDungeonGenerator::StepClimateMeter15(FClimateMeter15& M, bool bIn, bool bSay, float Step, float Rate, float Seconds, float Now, const TCHAR* Start, const TCHAR* Bite, const TCHAR* End)
{
	// (the cold's and the heat's one meter: in it, it rises by Step x Rate (to 60 s past Seconds), told once past Seconds, a bite every 15 s
	// after; out of it, it falls four times as fast, and its told state ends only after 2 s out (PR #109's review: an arch's shade or a
	// flickering bank of a stream every half second said both lines and put the bite off for good); a line at most every 10 s)
	if (!PlayerCombat) return;
	auto Say = [&](const TCHAR* T) { if (Now - M.SaidAt >= 10.f) { PlayerCombat->ShowMessage(T); M.SaidAt = Now; } };
	if (bIn)
	{
		M.OutSince = -1.f;
		M.V = FMath::Min(M.V + Step * Rate, Seconds + 60.f);
		if (M.V > Seconds && !M.bTold) { M.bTold = true; M.BiteAt = Now + 15.f; Say(Start); }
		if (M.bTold && M.V > Seconds && Now >= M.BiteAt && !PlayerCombat->IsDead())
		{
			M.BiteAt = Now + 15.f;
			PlayerCombat->HurtByTrap(0.03f, 0.2f, 1.f, Bite);
			++M.Bites;
		}
		return;
	}
	M.V = FMath::Max(0.f, M.V - 4.f * Step);
	if (M.OutSince < 0.f) M.OutSince = Now;
	if (M.bTold && Now - M.OutSince >= 2.f) { M.bTold = false; if (bSay) Say(End); }
}

void ARDDungeonGenerator::StepHeat15(const FRDWSample& Qs, bool bInTown, const FVector& Her, float Now)
{
	// (the heat, from the cold's look's sample: in the hot regions by day, away from a town, water over the ground (not a hot spring: PR #109's
	// review: a dry bank's sample named the river under it) and shade)
	if (WildHeatBiomes15.Num() == 0) return;
	const UWorld* W = GetWorld();
	const bool bHotLand = WildHeatBiomes15.Contains(Wild->BiomeName(Qs.Biome));
	const bool bDay = TownHour >= HeatFrom15 && TownHour < HeatTo15;
	WildHeatWhy15.Reset();
	if (!bHotLand) WildHeatWhy15 = TEXT("not here");
	else if (!bDay) WildHeatWhy15 = TEXT("night");
	else if (bInTown) WildHeatWhy15 = TEXT("town");
	else if (Qs.WaterKind != 0 && Qs.WaterKind != 6 && Qs.Water > Qs.H) WildHeatWhy15 = TEXT("water");
	else
	{
		// (shade: something solid over her head within 30 m (a rock, an arch, a roof, a ruin's wall leaning over))
		FHitResult Hit; FCollisionQueryParams Qp(SCENE_QUERY_STAT(RDHeatShade), false);
		if (const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0)) Qp.AddIgnoredActor(P);
		if (W && W->LineTraceSingleByChannel(Hit, Her + FVector(0, 0, 90.f), Her + FVector(0, 0, 3000.f), ECC_Visibility, Qp)) WildHeatWhy15 = TEXT("shade");
	}
	bWildHotNow15 = WildHeatWhy15.IsEmpty();
	StepClimateMeter15(WildHeatMeter15, bWildHotNow15, bHotLand, 0.5f, HeatRate15(), HeatSeconds15, Now, TEXT("The sun beats down. Find shade or water"),
		TEXT("The heat saps you. Your head swims"), TEXT("You cool off"));
}

void ARDDungeonGenerator::AddClimateHerb15(const FRDWildPlace& P, TArray<FName>& Got) const
{
	// (a resource point of a region with a herb of its own: one more in its pile; no draw of its stream)
	const FString Bn = Wild->BiomeName(P.Biome);
	for (const FString& L : ClimateHerbs15)
	{
		FString It, Bs;
		if (!L.Split(TEXT("|"), &It, &Bs)) continue;
		TArray<FString> B; Bs.ParseIntoArray(B, TEXT(";"), true);
		if (B.Contains(Bn) && FindItem(FName(*It)) >= 0) { Got.Add(FName(*It)); return; }
	}
}

FString ARDDungeonGenerator::GetWildClimate15() const
{
	// (tests: "cold|<cold s>|<cold now>|<cold rate>|<warm gear>|<warm buff>|heat|<heat s>|<hot now>|<heat rate>|<cool gear>|<cool buff>|<why>|<bites>")
	float Warm, Cool; GearClimate15(Warm, Cool);
	return FString::Printf(TEXT("cold|%.2f|%d|%.2f|%.2f|%.2f|heat|%.2f|%d|%.2f|%.2f|%.2f|%s|%d"), WildCold, bWildColdNow ? 1 : 0, ColdRate15(), Warm,
		PlayerCombat ? PlayerCombat->GetClimateBuff15(ERDItemKind::Warmth) : 0.f, WildHeatMeter15.V, bWildHotNow15 ? 1 : 0, HeatRate15(), Cool,
		PlayerCombat ? PlayerCombat->GetClimateBuff15(ERDItemKind::Cooling) : 0.f, *WildHeatWhy15, WildHeatMeter15.Bites);
}

void ARDDungeonGenerator::ResetClimate15()
{
	// (tests: the cold and the heat from nothing)
	WildColdMeter15 = FClimateMeter15(); WildHeatMeter15 = FClimateMeter15(); WildCold = 0.f; bWildColdTold = false;
}

float URDCombatComponent::GetClimateBuff15(ERDItemKind K) const
{
	// (the strongest of the kind on her: two stews do not add up)
	float B = 0.f;
	for (const FEffect& E : Effects) if (E.Kind == K) B = FMath::Max(B, E.Amount);
	return FMath::Min(B, 0.8f);
}
