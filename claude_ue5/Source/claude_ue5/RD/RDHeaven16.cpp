// The user's list of 2026-11-22 (docs/improvements16.txt, "the city of heaven"; the plan docs/improvements16_plan.md), its eighteenth
// phase, Heaven's first fixes:
// - "the street lights in heaven do not provide light": every street light lit under its lamp head (measured on the mesh by 946 lamps),
//   its head glowing, at night only (one pole in three had a 220 cd light 7.4 m up, day and night);
// - the buildings' signs modern (RDTownPlan.cpp: a lit panel, modern words; the faces painted by bs_signs.py --modern, 946 signs);
// - the town map's symbols modern (RDTownHUD.cpp: the 19 pictograms of SourceArt/heaven/art16/map, 946 symbols);
// - the sleepers on their mattresses (RDList10d.cpp: the bed's mesh traced, not its simple collision);
// - Kratos Aurorim Research a tower one and a half times the city's tallest and more (RDHeaven.cpp's ResearchShell).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDGameInstance.h"
#include "RD/RDTown.h"
#include "Components/PointLightComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDHeaven16, Log, All);

static TAutoConsoleVariable<int32> CVarRDStreetLamps(TEXT("rd.StreetLamps"), 1, TEXT("Heaven's street lamps: 1 by the hour (lit at night), 0 never lit (tests: the street without them)"));

bool ARDDungeonGenerator::IsStreetNight16() const
{
	// (the street lights burn from dusk to dawn: from 19:00 to 6:30; a town without the day's clock is lit as at night)
	if (!bDayNight) return true;
	return TownHour >= HeavenLampsOn16 || TownHour < HeavenLampsOff16;
}

void ARDDungeonGenerator::TickStreetLamps16(float Dt)
{
	// (twice a second: Heaven's street lamps and their glowing heads on at night, off by day; gathered again when the town's count changes)
	StreetLampLook16 -= Dt;
	if (StreetLampLook16 > 0.f) return;
	StreetLampLook16 = 0.5f;
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (TownPlan != 5 || !S || S->IsBuilding())
	{
		StreetLamps16.Reset(); StreetLampGlows16.Reset(); return;
	}
	if (StreetLampsOf16 != S)
	{
		StreetLamps16.Reset(); StreetLampGlows16.Reset();
		TArray<UActorComponent*> Ls = S->GetComponentsByTag(UPointLightComponent::StaticClass(), StreetLampTag16());
		for (UActorComponent* C : Ls) if (UPointLightComponent* L = Cast<UPointLightComponent>(C)) StreetLamps16.Add(L);
		TArray<UInstancedStaticMeshComponent*> Is; S->GetComponents(Is);
		const FRDPiece* Gp = Piece(TEXT("Heaven.LampGlow"));
		for (UInstancedStaticMeshComponent* I : Is) if (Gp && I->GetStaticMesh() == Gp->Mesh) StreetLampGlows16.Add(I);
		StreetLampsOf16 = S; StreetLampNight16 = -1;
	}
	const int32 Night = IsStreetNight16() && CVarRDStreetLamps.GetValueOnGameThread() != 0 ? 1 : 0;
	if (Night == StreetLampNight16) return;
	StreetLampNight16 = Night;
	for (const TWeakObjectPtr<UPointLightComponent>& L : StreetLamps16) if (UPointLightComponent* P = L.Get()) P->SetVisibility(Night == 1);
	for (const TWeakObjectPtr<UInstancedStaticMeshComponent>& G : StreetLampGlows16) if (UInstancedStaticMeshComponent* P = G.Get()) P->SetVisibility(Night == 1);
	UE_LOG(LogRDHeaven16, Log, TEXT("RDHEAVEN16 street lamps %s: %d lights, %d glows (%.1f h)"), Night ? TEXT("on") : TEXT("off"), StreetLamps16.Num(), StreetLampGlows16.Num(), TownHour);
}

TArray<FString> ARDDungeonGenerator::GetStreetLamps16() const
{
	// (for the tests: "lamps|<n>|<on>|<night>", "lamp|<x>|<y>|<z>|<cd>|<radius>|<visible>" for each)
	TArray<FString> Out;
	int32 On = 0;
	for (const TWeakObjectPtr<UPointLightComponent>& L : StreetLamps16) if (const UPointLightComponent* P = L.Get(); P && P->IsVisible()) ++On;
	Out.Add(FString::Printf(TEXT("lamps|%d|%d|%d"), StreetLamps16.Num(), On, IsStreetNight16() ? 1 : 0));
	for (const TWeakObjectPtr<UPointLightComponent>& L : StreetLamps16)
		if (const UPointLightComponent* P = L.Get())
			Out.Add(FString::Printf(TEXT("lamp|%.0f|%.0f|%.0f|%.0f|%.0f|%d"), P->GetComponentLocation().X, P->GetComponentLocation().Y, P->GetComponentLocation().Z, P->Intensity, P->AttenuationRadius, P->IsVisible() ? 1 : 0));
	return Out;
}

void ARDSection::HeavenLamp16(const FVector& At, float Yaw)
{
	// (the light under the lamp head as 946 measured it on the mesh (its arm's end, the head's underside), the head's glow there)
	const FVector Head = Generator->HeavenLampHead16.IsNearlyZero() ? FVector(260.f, 0.f, 740.f) : Generator->HeavenLampHead16;
	const FVector P = At + FRotator(0, Yaw, 0).RotateVector(Head);
	if (UPointLightComponent* L = AddLight(P - FVector(0, 0, 25.f), FLinearColor(1.f, 0.88f, 0.70f), Generator->HeavenLampCd16, Generator->HeavenLampRadius16, false, 0.f))
	{
		L->ComponentTags.Add(ARDDungeonGenerator::StreetLampTag16());          // (the list of 2026-11-22: a street lamp keeps its own draw distance)
		// (its light near her only, the glowing head seen from afar: 154 lamps' lights drawn to 90 m at 24 m each dropped the frame rate from
		// 20.1 to 4.4 a second at midnight (PR #125's review measured it); no indirect light (Lumen's cost), none on the see-through)
		L->MaxDrawDistance = Generator->HeavenLampDraw16; L->MaxDistanceFadeRange = 1000.f;
		L->SetIndirectLightingIntensity(0.f); L->bAffectTranslucentLighting = false;
	}
	if (Generator->Piece(TEXT("Heaven.LampGlow"))) AddPieceAt(TEXT("Heaven.LampGlow"), P, Yaw, 1.f, true);
}

FName ARDDungeonGenerator::HeavenMapSymbol16(uint8 Kind)
{
	switch (Kind)
	{
	case TK_Research: return TEXT("hvmap_research_lab");
	case TK_SkyTower: return TEXT("hvmap_skyscraper");
	case TK_Office: return TEXT("hvmap_office");
	case TK_Shop: return TEXT("hvmap_shop");
	case TK_Store: return TEXT("hvmap_grocery");
	case TK_Smithy: case TK_Workshop: return TEXT("hvmap_gear_shop");
	case TK_Healer: return TEXT("hvmap_clinic");
	case TK_Temple: case TK_Chapel: return TEXT("hvmap_chapel");
	case TK_Storehouse: case TK_Warehouse: return TEXT("hvmap_storage");
	case TK_Tavern: return TEXT("hvmap_bar");
	case TK_Barracks: return TEXT("hvmap_security");
	case TK_Home: return TEXT("hvmap_apartment");
	default: return NAME_None;
	}
}

FString ARDDungeonGenerator::HeavenMapMeaning16(uint8 Kind)
{
	switch (Kind)
	{
	case TK_Research: return TEXT("Kratos Aurorim Research: the way into the fortress");
	case TK_SkyTower: return TEXT("skyscraper");
	case TK_Office: return TEXT("offices");
	case TK_Shop: return TEXT("shop: buy and sell");
	case TK_Store: return TEXT("grocery: buy and sell");
	case TK_Smithy: case TK_Workshop: return TEXT("gear shop: repairs, the anvil");
	case TK_Healer: return TEXT("clinic: healing");
	case TK_Temple: case TK_Chapel: return TEXT("chapel: blessings");
	case TK_Storehouse: case TK_Warehouse: return TEXT("storage: your storage");
	case TK_Tavern: return TEXT("bar: food and drink");
	case TK_Barracks: return TEXT("security: the city's guard");
	case TK_Home: return TEXT("apartments");
	default: return FString();
	}
}

float ARDDungeonGenerator::HeavenSkyMaxZ16() const
{
	// (the tallest a skyscraper of the plan can stand: a lobby of one storey (2 + 300 cm), 30 cm, ten floors of its piece's step, its
	// rooftop: as ModernRoof stacks them)
	const FRDPiece* Mid = Piece(TEXT("Heaven.TowerMid"));
	const FRDPiece* TopP = Piece(TEXT("Heaven.TowerTop"));
	if (!Mid) return 10100.f;
	const float Step = FMath::Max((float)Mid->Size.Z - 22.f, 100.f);
	return 2.f + 300.f + 30.f + 10.f * Step + (TopP ? (float)TopP->Size.Z : 0.f);
}
