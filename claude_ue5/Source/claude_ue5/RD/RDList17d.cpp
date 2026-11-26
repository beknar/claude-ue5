// The user's list of 2026-11-26 (docs/improvements17.txt; the plan docs/improvements17_plan.md), its sixth phase: Closed Structures chosen.
//   "Put this game mode behind the Options button ... call the default mode 'Immersive Interiors' and the new mode 'Closed Structures'.
//   Describe both game modes."
//   - The Escape menu's Options page has a Structures line (Immersive Interiors / Closed Structures) and, under it, what the chosen mode is.
//     Kept with the other options in GameUserSettings.ini ([RandomDungeon.Options] Structures); -RDStructures=closed|immersive on the command
//     line wins over it for the session (read once into the game instance); rd.Structures17 0 / 1 over both (tests).
//   - A change made in a town is applied at once: out of a building she is in, the game saved to the autosave and loaded from it, so the town
//     is built again round her in the new mode where she stood. Elsewhere it waits for the next town.
//   - A save made inside a building is a save at its door outside: a load never puts her in a building's level.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDGameInstance.h"
#include "RD/RDCombat.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/ConfigCacheIni.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList17d, Log, All);

namespace
{
	const FIntPoint RDL17dDir4[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };
}

FString ARDDungeonGenerator::StructuresName17(int32 Mode)
{
	return Mode == 1 ? FString(TEXT("Closed Structures")) : FString(TEXT("Immersive Interiors"));
}

FString ARDDungeonGenerator::StructuresWords17(int32 Mode)
{
	return Mode == 1
		? FString(TEXT("Each building is a closed shell in the town; its door opens a level of its own for it. Its windows show pictures. Lighter to draw."))
		: FString(TEXT("Every building is built with its rooms in the town: walk in through its door, see in through its windows."));
}

int32 ARDDungeonGenerator::StructuresChoice17() const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	return GI ? FMath::Clamp(GI->Structures17, 0, 1) : 0;
}

void ARDDungeonGenerator::LoadStructures17()
{
	// (the option kept with the others; the command line's for the session wins over it, read once)
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return;
	if (!GI->bStructuresRead17)
	{
		GI->bStructuresRead17 = true;
		FString V;
		if (FParse::Value(FCommandLine::Get(), TEXT("RDStructures="), V)) GI->StructuresCmd17 = V.Equals(TEXT("closed"), ESearchCase::IgnoreCase) ? 1 : V.Equals(TEXT("immersive"), ESearchCase::IgnoreCase) ? 0 : -1;
	}
	int32 M = 0;
	if (GConfig) GConfig->GetInt(TEXT("RandomDungeon.Options"), TEXT("Structures"), M, GGameUserSettingsIni);
	GI->Structures17 = GI->StructuresCmd17 >= 0 ? GI->StructuresCmd17 : FMath::Clamp(M, 0, 1);
}

bool ARDDungeonGenerator::SetStructures17(int32 Mode, bool bApply)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return false;
	Mode = FMath::Clamp(Mode, 0, 1);
	GI->Structures17 = Mode; GI->StructuresCmd17 = -1;
	if (GConfig) { GConfig->SetInt(TEXT("RandomDungeon.Options"), TEXT("Structures"), Mode, GGameUserSettingsIni); GConfig->Flush(false, GGameUserSettingsIni); }
	UE_LOG(LogRDList17d, Log, TEXT("RDSTRUCTURES17 %s"), *StructuresName17(Mode));
	// (applied at once in a town whose build differs: the game saved and loaded where she stands, the town built again in the new mode)
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	// (against the town as it was built (PR #141's review: the live setting can differ from it))
	if (!bApply || !bTown || !S || S->BldClosed17 == Closed17() || (PlayerCombat && PlayerCombat->IsDead())) return true;
	if (InBuilding17 >= 0) LeaveBuilding17();
	if (bMenuDryRun) return true;
	SetMenuOpen(false);
	if (!SaveGameNow(TEXT("autosave"), TEXT("structures"), FString())) return false;
	return LoadGameFrom(TEXT("autosave"));
}

FVector ARDDungeonGenerator::SavePoint17(const FVector& Her) const
{
	// (inside a building's level: its door's outside, as she would leave it)
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (InBuilding17 < 0 || !S || !S->TownBlds.IsValidIndex(InBuilding17)) return Her;
	const ARDSection::FTownBld& B = S->TownBlds[InBuilding17];
	const FVector Out(RDL17dDir4[B.DoorSide].X, RDL17dDir4[B.DoorSide].Y, 0.f);
	const FVector At = S->LocalToWorld(B.DoorTile) + Out * (TileSize * 0.5f + 180.f);
	return FVector(At.X, At.Y, Her.Z);
}
