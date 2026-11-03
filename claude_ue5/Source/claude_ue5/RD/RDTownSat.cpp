// Brokenspire's map as seen from above (the user's of 2026-11-03: "draw the town's map as a semi-realistic top down
// representation of the terrain features, much like what you would see from a satellite or google earth, with labels on
// important or functional buildings and quest markers on NPCs that have them"). Once the town is built and in place, the
// generator lights it at TownSatelliteHour for a moment and takes one picture straight down with an orthographic scene
// capture (TownSatellitePicture, TownSatelliteSize pixels square over the town and its wall): the people, the animals, the
// guards and her left out (they are the map's marks), the grass and plants' fading held off, no fog or sky in the way, a
// fixed exposure. The day's own light is put back the frame after. ARDHUD::DrawTownMapColour draws the picture under its
// labels and seals.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "RD/RDMonster.h"
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
			TownSatellitePicture = UKismetRenderingLibrary::CreateRenderTarget2D(this, TownSatelliteSize, TownSatelliteSize, RTF_RGBA8_SRGB, FLinearColor::Black, false);
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
		TownSatCap->PostProcessSettings.bOverride_DynamicGlobalIlluminationMethod = !bTownSatelliteLumen;
		TownSatCap->PostProcessSettings.bOverride_ReflectionMethod = !bTownSatelliteLumen;
		TownSatCap->PostProcessSettings.bOverride_AutoExposureBias = true;
		TownSatCap->PostProcessSettings.AutoExposureBias = TownSatelliteExposure;
		TownSatCap->TextureTarget = TownSatellitePicture;
		TownSatCap->OrthoWidth = TownSatHalf * 2.f;
		// (straight down from 50 m: the picture's up is the world's +X (north, the map's up), its right +Y)
		TownSatCap->SetWorldLocationAndRotation(FVector(TownSatCenter.X, TownSatCenter.Y, S->GetActorLocation().Z + 5000.f), FRotator(-90.f, 0.f, 0.f));
		TownSatCap->ClearHiddenComponents();
		TownSatCap->HiddenActors.Reset();
		if (APawn* P = UGameplayStatics::GetPlayerPawn(this, 0)) TownSatCap->HideActorComponents(P);
		for (ARDTownsfolk* T : TownPeople) if (IsValid(T)) TownSatCap->HideActorComponents(T);
		for (ARDTownAnimal* A : TownAnimalActors) if (IsValid(A)) TownSatCap->HideActorComponents(A);
		for (ARDMonster* M : TownGuards) if (IsValid(M)) TownSatCap->HideActorComponents(M);
		const double T0 = FPlatformTime::Seconds();
		TownSatCap->CaptureScene();
		TownSatMs = (FPlatformTime::Seconds() - T0) * 1000.0;
		TownSatStep = 2;
		return;
	}
	case 2:
	{
		// (the day's own light again, the plants' fading again)
		if (bTownSatLit) { TownHour = TownSatHourWas; ApplyDayNight(); }
		for (const auto& Kv : TownSatCulls) if (UInstancedStaticMeshComponent* C = Kv.Key.Get()) C->SetCullDistances(Kv.Value.X, Kv.Value.Y);
		TownSatCulls.Reset();
		++TownSatCaptures;
		TownSatStep = 3;
		UE_LOG(LogRDTownSat, Log, TEXT("RDTOWN the map's picture from above: %d px over %.0f m, at %.1f o'clock, captured in %.0f ms"), TownSatelliteSize, TownSatHalf * 2.f / 100.f, TownSatelliteHour, TownSatMs);
		return;
	}
	default: return;
	}
}

FString ARDDungeonGenerator::GetTownSatelliteState() const
{
	return FString::Printf(TEXT("%d|%d|%.0f|%.0f|%.0f|%.0f|%d"), TownSatStep, TownSatellitePicture ? TownSatellitePicture->SizeX : 0, TownSatCenter.X, TownSatCenter.Y, TownSatHalf, TownSatMs, TownSatCaptures);
}
