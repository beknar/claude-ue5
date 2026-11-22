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
	// (the armour she wears: its warmth against the cold and its coolness in the heat (heavy plate's below 0: hotter))
	Warm = Cool = 0.f;
	if (!PlayerCombat) return;
	const FString Worn = PlayerCombat->GetWornArmour().ToString();
	if (Worn.IsEmpty() || Worn == TEXT("None")) return;
	for (const FString& L : ClimateGear15)
	{
		TArray<FString> F; L.ParseIntoArray(F, TEXT("|"), false);
		if (F.Num() >= 3 && F[0] == Worn) { Warm = FCString::Atof(*F[1]); Cool = FCString::Atof(*F[2]); return; }
	}
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

void ARDDungeonGenerator::TickHeat15(float Dt, const FVector& Her)
{
	HeatLook15 -= Dt;
	if (HeatLook15 > 0.f || !IsWildReady() || !PlayerCombat || WildHeatBiomes15.Num() == 0) return;
	const float Step = 0.5f - HeatLook15;          // (the time since the last look)
	HeatLook15 = 0.5f;
	const UWorld* W = GetWorld();
	const float Now = W ? W->GetTimeSeconds() : 0.f;
	FRDWSample Qs; Wild->Sample(Her.X / 100.0, Her.Y / 100.0, Qs, false);
	const bool bHotLand = WildHeatBiomes15.Contains(Wild->BiomeName(Qs.Biome));
	const bool bDay = TownHour >= HeatFrom15 && TownHour < HeatTo15;
	WildHeatWhy15.Reset();
	if (!bHotLand) WildHeatWhy15 = TEXT("not here");
	else if (!bDay) WildHeatWhy15 = TEXT("night");
	else if (IsInLoadedTown(Her)) WildHeatWhy15 = TEXT("town");
	else if (Qs.WaterKind != 0) WildHeatWhy15 = TEXT("water");
	else
	{
		// (shade: something solid over her head within 30 m (a rock, an arch, a roof, a ruin's wall leaning over))
		FHitResult Hit; FCollisionQueryParams Qp(SCENE_QUERY_STAT(RDHeatShade), false);
		if (const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0)) Qp.AddIgnoredActor(P);
		if (W && W->LineTraceSingleByChannel(Hit, Her + FVector(0, 0, 90.f), Her + FVector(0, 0, 3000.f), ECC_Visibility, Qp)) WildHeatWhy15 = TEXT("shade");
	}
	bWildHotNow15 = WildHeatWhy15.IsEmpty();
	if (!bWildHotNow15)
	{
		if (bWildHeatTold15 && bHotLand) PlayerCombat->ShowMessage(TEXT("You cool off"));
		bWildHeatTold15 = false;
		WildHeat15 = FMath::Max(0.f, WildHeat15 - 4.f * Step);
		return;
	}
	WildHeat15 = FMath::Min(WildHeat15 + Step * HeatRate15(), HeatSeconds15 + 60.f);
	if (WildHeat15 > HeatSeconds15 && !bWildHeatTold15) { bWildHeatTold15 = true; WildHeatBiteAt15 = Now + 15.f; PlayerCombat->ShowMessage(TEXT("The sun beats down. Find shade or water")); }
	if (bWildHeatTold15 && WildHeat15 > HeatSeconds15 && Now >= WildHeatBiteAt15 && !PlayerCombat->IsDead())
	{
		WildHeatBiteAt15 = Now + 15.f;
		PlayerCombat->HurtByTrap(0.03f, 0.2f, 1.f, TEXT("The heat saps you. Your head swims"));
		++HeatBites15;
	}
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
		PlayerCombat ? PlayerCombat->GetClimateBuff15(ERDItemKind::Warmth) : 0.f, WildHeat15, bWildHotNow15 ? 1 : 0, HeatRate15(), Cool,
		PlayerCombat ? PlayerCombat->GetClimateBuff15(ERDItemKind::Cooling) : 0.f, *WildHeatWhy15, HeatBites15);
}

void ARDDungeonGenerator::ResetClimate15()
{
	// (tests: the cold and the heat from nothing)
	WildCold = 0.f; bWildColdTold = false; WildHeat15 = 0.f; bWildHeatTold15 = false; HeatBites15 = 0;
}

float URDCombatComponent::GetClimateBuff15(ERDItemKind K) const
{
	// (the strongest of the kind on her: two stews do not add up)
	float B = 0.f;
	for (const FEffect& E : Effects) if (E.Kind == K) B = FMath::Max(B, E.Amount);
	return FMath::Min(B, 0.8f);
}
