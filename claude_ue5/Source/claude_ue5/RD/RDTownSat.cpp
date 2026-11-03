// Brokenspire's map as seen from above (the user's of 2026-11-03: "draw the town's map as a semi-realistic top down
// representation of the terrain features, much like what you would see from a satellite or google earth, with labels on
// important or functional buildings and quest markers on NPCs that have them"). Once the town is built and in place, the
// generator takes one picture straight down with an orthographic scene capture (TownSatellitePicture, TownSatelliteSize
// pixels square over the town and its wall), in the materials' own colours (TownSatelliteSource 1; the lit picture, 0, is
// lit at TownSatelliteHour for that frame): the people, the animals, the guards, her allies, her and the loot piles left out
// (they are the map's marks), the grass and plants' fading held off, no fog or sky in the way. ARDHUD::DrawTownMapColour
// draws the picture under its labels and seals.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "RD/RDMonster.h"
#include "RD/RDMistward.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDTownSat, Log, All);

void ARDDungeonGenerator::TickTownSatellite(float Dt)
{
	if (!bTown || !bTownSatellite || !bTownPlaced || TownSatStep >= 3) return;
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S || S->IsBuilding()) return;
	switch (TownSatStep)
	{
	case 0:
	{
		// (a few seconds in, so that the textures have streamed in; then the picture's hour, applied this frame, seen the next)
		TownSatWait += Dt;
		if (TownSatWait < TownSatelliteDelay) return;
		TownSatHourWas = TownHour;
		// (the lit picture only: the materials' own colours need no light)
		bTownSatLit = TownSatelliteSource != 1 && DaySun;
		if (bTownSatLit) { TownHour = TownSatelliteHour; ApplyDayNight(); }
		// (the grass and the gardens' plants fade out from 45 m of the view: the camera is 50 m up, all of it far)
		TownSatCulls.Reset();
		TInlineComponentArray<UInstancedStaticMeshComponent*> Ic(S);
		for (UInstancedStaticMeshComponent* C : Ic)
			if (C && C->InstanceEndCullDistance > 0) { TownSatCulls.Add({ C, FIntPoint(C->InstanceStartCullDistance, C->InstanceEndCullDistance) }); C->SetCullDistances(0, 0); }
		TownSatStep = 1;
		return;
	}
	case 1:
	{
		// the town's square in the world: its inner bounds' middle, their span and a tenth more (the wall and its towers)
		const float TS = TileSize;
		const FVector In0 = S->LocalToWorld(S->TownInner.Min) - FVector(TS * 0.5f, TS * 0.5f, 0), In1 = S->LocalToWorld(S->TownInner.Max - FIntPoint(1, 1)) + FVector(TS * 0.5f, TS * 0.5f, 0);
		TownSatCenter = FVector2D((In0.X + In1.X) * 0.5f, (In0.Y + In1.Y) * 0.5f);
		TownSatHalf = FMath::Max(In1.X - In0.X, In1.Y - In0.Y) * 0.55f;
		if (!TownSatellitePicture || TownSatellitePicture->SizeX != TownSatelliteSize)
			// (with mips: the map draws it at a quarter of its size or less, and without them roofs and cobbles shimmered)
			TownSatellitePicture = UKismetRenderingLibrary::CreateRenderTarget2D(this, TownSatelliteSize, TownSatelliteSize, RTF_RGBA8_SRGB, FLinearColor::Black, true);
		if (!TownSatCap)
		{
			TownSatCap = NewObject<USceneCaptureComponent2D>(this, TEXT("RDTownSatellite"));
			TownSatCap->SetupAttachment(GetRootComponent());
			TownSatCap->bCaptureEveryFrame = false; TownSatCap->bCaptureOnMovement = false;
			TownSatCap->ProjectionType = ECameraProjectionMode::Orthographic;
			TownSatCap->CaptureSource = ESceneCaptureSource::SCS_FinalColorLDR;
			// (no fog, sky or clouds between the camera and the ground; no motion blur; a still)
			TownSatCap->ShowFlags.SetFog(false); TownSatCap->ShowFlags.SetVolumetricFog(false);
			TownSatCap->ShowFlags.SetCloud(false); TownSatCap->ShowFlags.SetMotionBlur(false);
			// (a fixed exposure: a single capture has no eye adaptation to settle; and no Lumen, which a first frame has no
			// history for)
			FPostProcessSettings& Pp = TownSatCap->PostProcessSettings;
			Pp.bOverride_AutoExposureMethod = true; Pp.AutoExposureMethod = EAutoExposureMethod::AEM_Manual;
			Pp.bOverride_AutoExposureApplyPhysicalCameraExposure = true; Pp.AutoExposureApplyPhysicalCameraExposure = false;
			Pp.bOverride_DynamicGlobalIlluminationMethod = true; Pp.DynamicGlobalIlluminationMethod = EDynamicGlobalIlluminationMethod::None;
			Pp.bOverride_ReflectionMethod = true; Pp.ReflectionMethod = EReflectionMethod::None;
			Pp.bOverride_MotionBlurAmount = true; Pp.MotionBlurAmount = 0.f;
			TownSatCap->RegisterComponent();
		}
		TownSatCap->ShowFlags.SetDynamicShadows(bTownSatelliteShadows);
		TownSatCap->CaptureSource = TownSatelliteSource == 1 ? ESceneCaptureSource::SCS_BaseColor : ESceneCaptureSource::SCS_FinalColorLDR;
		// (no Lumen for the base colour: nothing of its light reaches that picture)
		const bool bNoLumen = !bTownSatelliteLumen || TownSatelliteSource == 1;
		TownSatCap->PostProcessSettings.bOverride_DynamicGlobalIlluminationMethod = bNoLumen;
		TownSatCap->PostProcessSettings.bOverride_ReflectionMethod = bNoLumen;
		TownSatCap->PostProcessSettings.bOverride_AutoExposureBias = true;
		TownSatCap->PostProcessSettings.AutoExposureBias = TownSatelliteExposure;
		TownSatCap->TextureTarget = TownSatellitePicture;
		TownSatCap->OrthoWidth = TownSatHalf * 2.f;
		// (straight down from above everything the town has (its highest tower, 10 m more; 50 m at least): the picture's up
		// is the world's +X (north, the map's up), its right +Y)
		const FBox Bb = S->GetComponentsBoundingBox(true);
		const float CamZ = FMath::Max(S->GetActorLocation().Z + 5000.f, Bb.IsValid ? (float)Bb.Max.Z + 1000.f : 0.f);
		TownSatCap->SetWorldLocationAndRotation(FVector(TownSatCenter.X, TownSatCenter.Y, CamZ), FRotator(-90.f, 0.f, 0.f));
		// (everything that moves or comes and goes is a mark of the map's own, not baked into the picture)
		TownSatCap->ClearHiddenComponents();
		TownSatCap->HiddenActors.Reset();
		if (APawn* P = UGameplayStatics::GetPlayerPawn(this, 0)) TownSatCap->HideActorComponents(P);
		for (ARDTownsfolk* T : TownPeople) if (IsValid(T)) TownSatCap->HideActorComponents(T);
		for (ARDTownAnimal* A : TownAnimalActors) if (IsValid(A)) TownSatCap->HideActorComponents(A);
		for (ARDMonster* M : TownGuards) if (IsValid(M)) TownSatCap->HideActorComponents(M);
		for (ARDMonster* M : Allies) if (IsValid(M)) TownSatCap->HideActorComponents(M);
		for (ARDLootPile* Lp : LootPiles) if (IsValid(Lp)) TownSatCap->HideActorComponents(Lp);
		TownSatHidden = TownSatCap->HiddenComponents.Num();
		const double T0 = FPlatformTime::Seconds();
		TownSatCap->CaptureScene();
		TownSatMs = (FPlatformTime::Seconds() - T0) * 1000.0;
		TownSatStep = 2;
		return;
	}
	case 2:
	{
		ReleaseTownSatHold();
		++TownSatCaptures;
		TownSatStep = 3;
		UE_LOG(LogRDTownSat, Log, TEXT("RDTOWN the map's picture from above: %d px over %.0f m, at %.1f o'clock, captured in %.0f ms"), TownSatelliteSize, TownSatHalf * 2.f / 100.f, TownSatelliteHour, TownSatMs);
		return;
	}
	default: return;
	}
}

void ARDDungeonGenerator::ReleaseTownSatHold()
{
	// (the day's own light again, the plants' fading again: held only between steps 0 and 2. Begun again in between, step 0
	// would have read the held state as the day's: the plants never fading again, the clock at the picture's hour)
	if (TownSatStep != 1 && TownSatStep != 2) return;
	if (bTownSatLit) { TownHour = TownSatHourWas; ApplyDayNight(); }
	bTownSatLit = false;
	for (const auto& Kv : TownSatCulls) if (UInstancedStaticMeshComponent* C = Kv.Key.Get()) C->SetCullDistances(Kv.Value.X, Kv.Value.Y);
	TownSatCulls.Reset();
}

FString ARDDungeonGenerator::GetTownSatelliteState() const
{
	return FString::Printf(TEXT("%d|%d|%.0f|%.0f|%.0f|%.0f|%d|%d|%d|%.0f|%d"), TownSatStep, TownSatellitePicture ? TownSatellitePicture->SizeX : 0, TownSatCenter.X, TownSatCenter.Y, TownSatHalf, TownSatMs, TownSatCaptures,
		TownSatHidden, TownSatellitePicture && TownSatellitePicture->bAutoGenerateMips ? 1 : 0, TownSatCap ? TownSatCap->GetComponentLocation().Z : 0.0, TownSatCulls.Num());
}
