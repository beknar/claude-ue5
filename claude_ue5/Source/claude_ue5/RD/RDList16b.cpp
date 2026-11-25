// The user's list of 2026-11-22 (docs/improvements16.txt; the plan docs/improvements16_plan.md), its second phase: quick fixes.
//   - Her summons on the wilds' and the towns' minimaps and big maps, as the dungeon maps draw them.
//   - The loading screen ("is there a way to load textures before the game is displayed?"): the engine's own while a map loads (the movie
//     player), then a cover over the game's view after a level opens, a fast travel, the map's teleport or a respawn, until the world round
//     her is built (the town, the 3 x 3 chunks under her, a pending load put down) and the texture streamer wants nothing more, or
//     Cover16Cap seconds once the world is built. Each cover is logged with its times and how it lifted. Coming back from a cave, the wilds'
//     level still plans Brokenspire (the world's roads leave by its gate) but under the cover: she is shown only by the tower's mouth.
#include "RD/RDHUD.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDGameInstance.h"
#include "RD/RDMonster.h"
#include "RD/RDCombat.h"
#include "RD/RDSection.h"
#include "RD/RDWild.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "ContentStreaming.h"
#include "MoviePlayer.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformTime.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Text/STextBlock.h"
#include "Styling/CoreStyle.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList16b, Log, All);

namespace
{
	TAutoConsoleVariable<int32> CVarRDLoadingCover(TEXT("rd.LoadingCover"), 1, TEXT("The loading cover over the view after a level opens, a travel or a respawn (1) or none (0)"));

	// (the cover: a dark board with the word, over everything the game draws)
	TSharedRef<SWidget> RDCover16Widget()
	{
		return SNew(SBorder)
			.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
			.BorderBackgroundColor(FLinearColor(0.035f, 0.03f, 0.028f, 1.f))
			.HAlign(HAlign_Center).VAlign(VAlign_Center)
			[
				SNew(STextBlock)
				.Text(FText::FromString(TEXT("Loading")))
				.Font(FCoreStyle::GetDefaultFontStyle("Regular", 30))
				.ColorAndOpacity(FLinearColor(0.88f, 0.80f, 0.62f, 1.f))
			];
	}
}

// ================================================================================================ her summons on the maps
void ARDHUD::DrawAllyMarks16(TFunctionRef<FVector2D(const FVector&)> ToScreen, TFunctionRef<bool(const FVector&, const FVector2D&)> Inside, float Size)
{
	// (her summoned and raised allies: the dungeon maps' own mark (a green ring with a green middle), each recorded where it is drawn for
	// the tests)
	if (!Gen) return;
	for (const ARDMonster* Al : Gen->GetAllies())
	{
		if (!IsValid(Al) || Al->IsDead()) continue;
		const FVector W = Al->GetActorLocation();
		const FVector2D S = ToScreen(W);
		if (!Inside(W, S)) continue;
		MistMark(12, S, Size);
		MarksDrawn.Add(FVector(W.X, W.Y, 12.f));
	}
}

// ================================================================================================ the loading screen
void URDGameInstance::Init()
{
	Super::Init();
	if (!IsRunningDedicatedServer()) FCoreUObjectDelegates::PreLoadMap.AddUObject(this, &URDGameInstance::BeginLoadingScreen16);
}

void URDGameInstance::BeginLoadingScreen16(const FString& Map)
{
	// (the movie player draws on its own thread while the map loads: a packaged game's; play in the editor has none)
	if (!IsMoviePlayerEnabled() || CVarRDLoadingCover.GetValueOnGameThread() == 0) return;
	FLoadingScreenAttributes A;
	A.bAutoCompleteWhenLoadingCompletes = true;
	A.MinimumLoadingScreenDisplayTime = 0.f;
	A.WidgetLoadingScreen = RDCover16Widget();
	GetMoviePlayer()->SetupLoadingScreen(A);
}

void ARDDungeonGenerator::ShowCover16(const FString& Why)
{
	if (CVarRDLoadingCover.GetValueOnGameThread() == 0) return;
	// (the reels' pilots record the screen: their scenes are not covered (PR #112's review))
	static const bool bNoCover = FParse::Param(FCommandLine::Get(), TEXT("RDNoCover")) || FParse::Param(FCommandLine::Get(), TEXT("RDReel15")) || FParse::Param(FCommandLine::Get(), TEXT("RDReel16")) || FParse::Param(FCommandLine::Get(), TEXT("RDShow7"));
	if (bNoCover) return;
	UWorld* W = GetWorld();
	UGameViewportClient* V = W ? W->GetGameViewport() : nullptr;
	if (!V) return;
	if (!bCover16)
	{
		Cover16Widget = RDCover16Widget();
		V->AddViewportWidgetContent(Cover16Widget.ToSharedRef(), 10000);
	}
	// (a second reason while it is up: the cover stays, timed from the first)
	if (!bCover16)
	{
		Cover16Start = FPlatformTime::Seconds();
		// (under the cover she neither moves nor turns, and nothing hurts her: she cannot see (PR #112's review))
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0)) { PC->SetIgnoreMoveInput(true); PC->SetIgnoreLookInput(true); }
		Cover16Health = PlayerCombat ? PlayerCombat->GetHealth() : -1.f;
	}
	Cover16Why = bCover16 ? Cover16Why + TEXT("+") + Why : Why;
	bCover16 = true; Cover16ReadyAt = -1.0;
	UE_LOG(LogRDList16b, Log, TEXT("RDCOVER16 up: %s"), *Cover16Why);
}

void ARDDungeonGenerator::HideCover16(const FString& How)
{
	if (!bCover16) return;
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0)) { PC->SetIgnoreMoveInput(false); PC->SetIgnoreLookInput(false); }
	if (UWorld* W = GetWorld()) if (UGameViewportClient* V = W->GetGameViewport(); V && Cover16Widget.IsValid()) V->RemoveViewportWidgetContent(Cover16Widget.ToSharedRef());
	Cover16Widget.Reset();
	bCover16 = false;
	const double Now = FPlatformTime::Seconds();
	// (and where she stands as she is first seen: the tests' "never shown in Brokenspire on the way from a cave")
	const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0);
	const FVector At = P ? P->GetActorLocation() : FVector::ZeroVector;
	// (and the frames under it since the world was built: how many, their mean time, the steady run at the lift)
	const FString L = FString::Printf(TEXT("%s|%.2f|%.2f|%s|%d|%.0f|%.0f|%d|%.1f|%d"), *Cover16Why, Now - Cover16Start, Cover16ReadyAt < 0.0 ? -1.0 : Now - Cover16ReadyAt, *How, IStreamingManager::Get().GetNumWantingResources(), At.X, At.Y,
		Cover16Frames, Cover16Frames > 0 ? 1000.0 * Cover16FrameSum / Cover16Frames : 0.0, Cover16Steady);
	Cover16Lines.Add(L);
	UE_LOG(LogRDList16b, Log, TEXT("RDCOVER16 lifted: %s"), *L);
}

bool ARDDungeonGenerator::TravelToTown16(const FString& Name)
{
	bTravelForced = true;
	const bool bOk = WildTravelToTown(Name);
	bTravelForced = false;
	return bOk;
}

void ARDDungeonGenerator::TickCover16(float Dt)
{
	if (!bCover16) return;
	const double Now = FPlatformTime::Seconds();
	// (nothing hurts her while she cannot see)
	if (PlayerCombat && Cover16Health > 0.f && !PlayerCombat->IsDead() && PlayerCombat->GetHealth() < Cover16Health) PlayerCombat->SetHealth(Cover16Health);
	// (never more than a minute, whatever waits)
	if (Now - Cover16Start > 60.0) { HideCover16(TEXT("timeout")); return; }
	// (the world round her: the town built (or none to build), a pending load put down, the chunks under her made)
	bool bBuilt = true;
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (bTown)
	{
		const URDGameInstance* GI = URDGameInstance::Of(this);
		bBuilt = !bTownLoading && !bTownTraveling && (!S || !S->IsBuilding()) && (!GI || !GI->bLoadPending) && bTownPlaced;
		if (bBuilt && bWild)
		{
			if (!IsWildReady()) bBuilt = false;
			else if (const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0))
			{
				const FVector L = P->GetActorLocation();
				const int32 Cx = FMath::FloorToInt(L.X / 100.0 / WildChunkM), Cy = FMath::FloorToInt(L.Y / 100.0 / WildChunkM);
				for (int32 I = -1; I <= 1 && bBuilt; ++I) for (int32 J = -1; J <= 1 && bBuilt; ++J)
				{
					const TObjectPtr<ARDWildChunk>* C = WildChunks.Find(FIntPoint(Cx + I, Cy + J));
					// (a chunk under a loaded town's square is dropped for the town's ground: not waited for)
					const bool bUnderTown = WildTownIdx >= 0 && IsInLoadedTown(FVector((Cx + I + 0.5) * WildChunkM * 100.0, (Cy + J + 0.5) * WildChunkM * 100.0, 0.0));
					if (!bUnderTown && (!C || !IsValid(*C) || (*C)->bMaking)) bBuilt = false;
				}
			}
		}
	}
	else bBuilt = bTower24 ? bTowerPlaced24 : (S && !S->IsBuilding());          // (the skyscrapers' level has no sets: the tower is built at play's start)
	if (!bBuilt) { Cover16ReadyAt = -1.0; Cover16Steady = 0; Cover16Frames = 0; Cover16FrameSum = 0.0; return; }
	if (Cover16ReadyAt < 0.0) Cover16ReadyAt = Now;
	++Cover16Frames; Cover16FrameSum += FApp::GetDeltaTime();
	// (then the frames steadied (ten in a row under 100 ms: the first frames after a town is built took 400 ms, its lights and the
	// global illumination still dark in the test's picture), a second at least for the town's lit rule and the lighting to come in,
	// and the textures: the streamer wanting nothing more; or the cap)
	Cover16Steady = FApp::GetDeltaTime() < 0.1 ? Cover16Steady + 1 : 0;
	const int32 Want = IStreamingManager::Get().GetNumWantingResources();
	if (Now - Cover16ReadyAt > 1.0 && Cover16Steady >= 10 && Want == 0) { HideCover16(TEXT("streamed")); return; }
	if (Now - Cover16ReadyAt > Cover16Cap) HideCover16(TEXT("cap"));
}
