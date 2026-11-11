// Brokenspire's and the wilderness's sky and weather (the user's list of 2026-11-04, docs/improvements7.txt: "the sky is
// uniformly grey. there should be clouds of different sizes and types, ... the sun if it's daytime, the moon if it's night
// time, stars if it's night if there's no cloud cover"; "when it's night time, there is no moonlight or starlight"; "there is
// no wind of weather effects"). The generator's bSky7 (890 sets it and the assets):
//   - the height fog no longer covers the sky (its cutoff distance: the level's fog drew every sky pixel at 94 % grey); the
//     sun's disc is the sky atmosphere's own, seen once the fog is off it
//   - clouds: a volumetric cloud layer (the engine's simple cloud material; its coverage and its storm look from the weather)
//   - the stars: a dome far off round her camera, their brightness the night's and the clear sky's; the moon: a disc in the
//     moon light's direction, as bright as the night and the clouds let it be; the moonlight and the night's sky light raised
//     (890's MoonLux, NightSkyShare, NightExposureBias)
//   - the weather (clear, fair, cloudy, overcast, rain, storm, snow, fog), a new one every 4 to 9 minutes from a stream of its
//     own (the session's seed: never the play's): the clouds' cover, the sun's and sky light's dimming, the fog's thickening,
//     rain or snow (cold places snow) round her camera, wind (blowing leaves, the grass's sway: WindCollection's Strength),
//     the rain's and the wind's sounds
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDSection.h"
#include "RD/RDCombat.h"
#include "Components/VolumetricCloudComponent.h"
#include "HAL/IConsoleManager.h"
#include "Components/StaticMeshComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/AudioComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialParameterCollection.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "Camera/PlayerCameraManager.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Sound/SoundBase.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDSky, Log, All);

namespace
{
	float RDSkySmooth(float A, float B, float X) { const float T = FMath::Clamp((X - A) / (B - A), 0.f, 1.f); return T * T * (3.f - 2.f * T); }
	// (per weather: the clouds' cover, rain, wind, fog)
	struct FRDWeatherLook { float Cover, Rain, Wind, Fog; };
	const FRDWeatherLook RDWeatherLooks[9] = {
		{ 0.04f, 0.f, 0.12f, 0.f },     // clear
		{ 0.32f, 0.f, 0.25f, 0.f },     // fair
		{ 0.62f, 0.f, 0.40f, 0.05f },   // cloudy
		{ 0.90f, 0.f, 0.45f, 0.20f },   // overcast
		{ 0.96f, 0.7f, 0.55f, 0.35f },  // rain
		{ 1.00f, 1.f, 1.00f, 0.45f },   // storm
		{ 0.94f, 0.8f, 0.45f, 0.45f },  // snow
		{ 0.70f, 0.f, 0.04f, 1.00f },   // fog
		{ 0.f, 0.f, 0.08f, 0.f } };     // cloudless (rd.Weather only: the rotation never picks it)
	/** (2026-11-10: "truly clear weather ... separate from the current clear": clear's clouds never go below the cover range's
	 *  0.05 and pile up along the horizon as a white band (884 sky10's pictures); cloudless draws no cloud layer at all) */
	constexpr int32 RDWeatherCloudless = 8;
}

FString ARDDungeonGenerator::WeatherName(int32 K)
{
	static const TCHAR* N[] = { TEXT("clear"), TEXT("fair"), TEXT("cloudy"), TEXT("overcast"), TEXT("rain"), TEXT("storm"), TEXT("snow"), TEXT("fog"), TEXT("cloudless") };
	return K >= 0 && K < 9 ? FString(N[K]) : FString(TEXT("?"));
}

void ARDDungeonGenerator::BeginSky7()
{
	if (!bSky7 || !bTown) return;
	UWorld* W = GetWorld();
	if (!W) return;
	if (DayFog)
	{
		DayFogDensity = DayFog->FogDensity;
		DayFogStart = DayFog->StartDistance;
		DayFog->SetFogCutoffDistance(FogSkyCutoff);
	}
	DaySkyLightBase = DaySky ? DaySky->Intensity : 1.f;
	// (the clouds: a layer from 1.6 to 5.6 km over the ground)
	if (SkyCloudMaterial && !IsValid(SkyClouds))
	{
		SkyClouds = NewObject<UVolumetricCloudComponent>(this, TEXT("RDSkyClouds"));
		SkyClouds->SetupAttachment(RootComponent);
		SkyClouds->RegisterComponent();
		SkyCloudMID = UMaterialInstanceDynamic::Create(SkyCloudMaterial, this);
		SkyClouds->SetMaterial(SkyCloudMID);
		SkyClouds->SetLayerBottomAltitude(1.6f);
		SkyClouds->SetLayerHeight(4.f);
		SkyClouds->SetTracingMaxDistance(SkyCloudTraceKm);          // (the list of 2026-11-10: out to the horizon)
	}
	// (the list of 2026-11-08b: "when looking up at the sky, there is a blue outline against any object ... whenever there is
	// any blue sky"; "when there is no blue sky, there is a grey shimmering border around objects on the ground". The clouds
	// were traced at a quarter of the view's size and put back at half (the volumetric render target's mode 0): along every
	// edge against the sky they bled a fringe of the sky's colour 2 to 4 pixels wide (pictures of 2026-11-08b, roofs at noon,
	// fair and overcast). Mode 1 (traced at half size, upsampled) draws none and still lets the clouds meet the mountains;
	// mode 2 also drew none but cannot meet opaque ground, and the wilds' peaks reach into the layer)
	// (the setting is the whole process's: what it was is kept and put back when play here ends (EndPlay; PR #29's review), so
	// levels without these clouds, the editor's views and later plays keep their own)
	if (SkyClouds)
		if (IConsoleVariable* V = IConsoleManager::Get().FindConsoleVariable(TEXT("r.VolumetricRenderTarget.Mode")))
		{
			if (VrtModeWas < 0) VrtModeWas = V->GetInt();
			V->Set(1, ECVF_SetByCode);
		}
	auto Dome = [&](UStaticMesh* Mesh, UMaterialInterface* Mat, const TCHAR* Name, TObjectPtr<UStaticMeshComponent>& Out, TObjectPtr<UMaterialInstanceDynamic>& Mid)
	{
		if (!Mesh || !Mat || IsValid(Out)) return;
		Out = NewObject<UStaticMeshComponent>(this, Name);
		Out->SetupAttachment(RootComponent);
		Out->SetMobility(EComponentMobility::Movable);
		Out->SetStaticMesh(Mesh);
		Out->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Out->SetCastShadow(false);
		Out->bAffectDistanceFieldLighting = false;
		Out->SetVisibleInRayTracing(false);
		Out->SetUsingAbsoluteLocation(true); Out->SetUsingAbsoluteRotation(true); Out->SetUsingAbsoluteScale(true);
		Out->BoundsScale = 10.f;
		Out->RegisterComponent();
		Mid = UMaterialInstanceDynamic::Create(Mat, this);
		Out->SetMaterial(0, Mid);
	};
	Dome(SkyDomeMesh, SkyStarsMaterial, TEXT("RDSkyStars"), SkyStars, SkyStarsMID);
	if (SkyStars && SkyDomeMesh) { const float Sr = FMath::Max(SkyDomeMesh->GetBounds().SphereRadius, 1.f); SkyStars->SetWorldScale3D(FVector(4.0e6f / Sr)); }
	Dome(SkyDomeMesh, SkyHighCloudMaterial, TEXT("RDSkyHigh"), SkyHigh, SkyHighMID);
	if (SkyHigh && SkyDomeMesh) { const float Sr = FMath::Max(SkyDomeMesh->GetBounds().SphereRadius, 1.f); SkyHigh->SetWorldScale3D(FVector(3.6e6f / Sr)); }
	// (the high clouds drift the way the volumetric clouds do: along their CloudWind, else +X)
	if (SkyHighMID)
	{
		FLinearColor Cw(1.f, 0.f, 0.f, 1.f);
		if (SkyCloudMID) SkyCloudMID->GetVectorParameterValue(FName(TEXT("CloudWind")), Cw);
		const FVector2D Wd(Cw.R, Cw.G);
		SkyHighWindDir = Wd.SizeSquared() > 1e-8f ? Wd.GetSafeNormal() : FVector2D(1.f, 0.f);
		SkyHighMID->SetScalarParameterValue(TEXT("Height"), SkyHighHeight);
		SkyHighMID->SetScalarParameterValue(TEXT("TileCm"), FMath::Max(SkyHighTileCm, 1.f));
		SkyHighMID->SetVectorParameterValue(TEXT("WindDir"), FLinearColor(SkyHighWindDir.X, SkyHighWindDir.Y, 0.f, 0.f));
	}
	Dome(SkyQuadMesh, SkyMoonMaterial, TEXT("RDSkyMoon"), SkyMoon, SkyMoonMID);
	// (the weather of the start: fair; the next in a while)
	if (WeatherUntil <= 0.f)
	{
		Weather = 1; WeatherChanges = 0;
		const uint32 H = HashCombine((uint32)SessionSeed ^ 0x5EA7u, 17u);
		WeatherUntil = W->GetTimeSeconds() + FMath::Lerp(WeatherSeconds.X, WeatherSeconds.Y, (H % 1000u) / 999.f);
		const FRDWeatherLook& Lk = RDWeatherLooks[Weather];
		SkyCover = SkyCoverWant = Lk.Cover; SkyRain = SkyRainWant = Lk.Rain; SkyWind = SkyWindWant = Lk.Wind; SkyFog = SkyFogWant = Lk.Fog;
	}
	ApplySky7();
	UE_LOG(LogRDSky, Log, TEXT("RDSKY begun: clouds %d, stars %d, moon %d, fog off the sky beyond %.0f m, weather %s"), SkyClouds ? 1 : 0, SkyStars ? 1 : 0, SkyMoon ? 1 : 0, FogSkyCutoff / 100.f, *WeatherName(Weather));
}

void ARDDungeonGenerator::SetWeather(int32 Kind, bool bAtOnce)
{
	Weather = FMath::Clamp(Kind, 0, RDWeatherCloudless);
	const FRDWeatherLook& Lk = RDWeatherLooks[Weather];
	SkyCoverWant = Lk.Cover; SkyRainWant = Lk.Rain; SkyWindWant = Lk.Wind; SkyFogWant = Lk.Fog;
	if (bAtOnce) { SkyCover = SkyCoverWant; SkyRain = SkyRainWant; SkyWind = SkyWindWant; SkyFog = SkyFogWant; }
	if (const UWorld* W = GetWorld()) WeatherUntil = W->GetTimeSeconds() + WeatherSeconds.Y;
	++WeatherChanges;
	ApplySky7();
	UE_LOG(LogRDSky, Log, TEXT("RDSKY the weather: %s%s"), *WeatherName(Weather), bAtOnce ? TEXT(" (at once)") : TEXT(""));
}

void ARDDungeonGenerator::TickSky7(float Dt, APlayerController* PC)
{
	if (!bSky7 || !bTown || Dt <= 0.f) return;
	UWorld* W = GetWorld();
	if (!W || W->IsPaused()) return;
	if (!DaySun) return;
	const float Now = W->GetTimeSeconds();
	SkyTime += Dt;
	// ---- where she is: cold (snow for rain), dry (less rain)
	const APawn* Her = PC ? PC->GetPawn() : nullptr;
	const FVector L = Her ? Her->GetActorLocation() : FVector::ZeroVector;
	bool bDry = false;
	bSkyCold = false;
	if (bWild && IsWildReady() && Her)
	{
		FRDWSample S; Wild->Sample(L.X / 100.0, L.Y / 100.0, S, false);
		float T = 0.5f, M = 0.5f; Wild->Climate(L.X / 100.0, L.Y / 100.0, T, M);
		bSkyCold = S.Snow > 0.3f || T < 0.18f;
		bDry = M < 0.25f;
	}
	// ---- the next weather, when its time comes
	if (Now >= WeatherUntil && !bWeatherHeld)          // (the list of 2026-11-10: rd.Weather holds it)
	{
		++WeatherChanges;
		const uint32 H = HashCombine((uint32)SessionSeed ^ 0x5EA7u, (uint32)WeatherChanges * 2654435761u);
		const float Wt[8] = { 2.f, 3.f, 2.5f, 1.5f, bDry ? 0.3f : 1.5f, bDry ? 0.15f : 0.6f, 0.f, 0.6f };
		float Sum = 0.f; for (const float X : Wt) Sum += X;
		float Pick = ((H >> 4) % 10000u) / 10000.f * Sum;
		int32 K = 0;
		for (; K < 7; ++K) { if (Pick < Wt[K]) break; Pick -= Wt[K]; }
		if (K == Weather) K = (K + 1) % 8 == 6 ? 7 : (K + 1) % 8;
		if (bSkyCold && (K == 4 || K == 5)) K = 6;
		Weather = K;
		const FRDWeatherLook& Lk = RDWeatherLooks[Weather];
		SkyCoverWant = Lk.Cover; SkyRainWant = Lk.Rain; SkyWindWant = Lk.Wind; SkyFogWant = Lk.Fog;
		WeatherUntil = Now + FMath::Lerp(WeatherSeconds.X, WeatherSeconds.Y, (H % 1000u) / 999.f);
		UE_LOG(LogRDSky, Log, TEXT("RDSKY the weather turns %s (for %.0f s)%s"), *WeatherName(Weather), WeatherUntil - Now, bSkyCold ? TEXT(", cold") : TEXT(""));
	}
	// ---- easing toward it: the clouds over a minute and a half, the rain in twenty seconds
	SkyCover = FMath::FInterpConstantTo(SkyCover, SkyCoverWant, Dt, 1.f / 90.f);
	SkyRain = FMath::FInterpConstantTo(SkyRain, SkyRainWant, Dt, 1.f / 20.f);
	SkyWind = FMath::FInterpConstantTo(SkyWind, SkyWindWant, Dt, 1.f / 30.f);
	SkyFog = FMath::FInterpConstantTo(SkyFog, SkyFogWant, Dt, 1.f / 60.f);
	bSkySnowing = bSkyCold || Weather == 6;
	// ---- what follows her camera every frame: the dome, the moon, the rain or snow
	FVector Cam = L;
	if (PC && PC->PlayerCameraManager) Cam = PC->PlayerCameraManager->GetCameraLocation();
	TickFarLand(Cam);          // (the list of 2026-11-10: the far land to the horizon)
	if (SkyStars) SkyStars->SetWorldLocationAndRotation(Cam, FRotator(0.f, SkyTime * 0.15f, 0.f));
	// (the high clouds' dome only carries their layer round her camera: turned about the zenith at 0.6 degrees a second, with its
	// texture also panned round it, it read as a disc spinning overhead faster than the clouds near the horizon (the shipping
	// game, 2026-11-10). The layer is flat in its material now and moves in a straight line: the drift along the wind)
	if (SkyHigh)
	{
		SkyHigh->SetWorldLocationAndRotation(Cam, FRotator::ZeroRotator);
		if (SkyHighMID)
		{
			SkyHighDrift = FMath::Fmod(SkyHighDrift + double(SkyHighSpeed) * (0.4 + SkyWind) * Dt, double(FMath::Max(SkyHighTileCm, 1.f)));
			SkyHighMID->SetScalarParameterValue(TEXT("Drift"), float(SkyHighDrift));
		}
	}
	if (SkyMoon && DayMoon)
	{
		const FVector Md = -DayMoon->GetForwardVector();
		const float D = 3.5e6f;
		// (a 100 cm plane facing +Z, turned to face her: 2.4 degrees of sky across, a little larger than the real moon)
		const float Size = 2.f * D * FMath::Tan(FMath::DegreesToRadians(1.2f));
		SkyMoon->SetWorldLocationAndRotation(Cam + Md * D, FRotationMatrix::MakeFromZ(-Md).Rotator());
		SkyMoon->SetWorldScale3D(FVector(Size / 100.f));
	}
	// rain or snow round the camera, the wind's leaves round her
	auto Fx = [&](TObjectPtr<UNiagaraComponent>& C, UNiagaraSystem* Sys, bool bOn, const FVector& At)
	{
		if (!Sys) return;
		if (bOn && !IsValid(C)) C = UNiagaraFunctionLibrary::SpawnSystemAtLocation(W, Sys, At, FRotator::ZeroRotator, FVector(1.f), false, true, ENCPoolMethod::None);
		if (!IsValid(C)) return;
		C->SetWorldLocation(At);
		if (!bOn && C->IsActive()) C->Deactivate();
		else if (bOn && !C->IsActive()) C->Activate(true);
	};
	const bool bInside = bTown && GetSection(FIntPoint::ZeroValue) && GetSection(FIntPoint::ZeroValue)->TownBuildingAt(L) >= 0;
	// (the drops of our own: made once, 4500 streaks or 2500 flakes (each two crossed planes) in a 36 x 36 x 18 m field; the
	// field kept round the camera, the material moving them down through it)
	auto Drops = [&](TObjectPtr<UHierarchicalInstancedStaticMeshComponent>& H, TObjectPtr<UMaterialInstanceDynamic>& Mid, UMaterialInterface* Mat, int32 Count, const FVector& Scale, uint32 Sd, float Amount)
	{
		if (!DropMesh || !Mat) return;
		if (!IsValid(H))
		{
			H = NewObject<UHierarchicalInstancedStaticMeshComponent>(this);
			H->SetStaticMesh(DropMesh);
			H->SetMobility(EComponentMobility::Movable);
			H->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			H->SetCastShadow(false);
			H->SetUsingAbsoluteLocation(true); H->SetUsingAbsoluteRotation(true);
			H->SetupAttachment(RootComponent);
			H->RegisterComponent();
			Mid = UMaterialInstanceDynamic::Create(Mat, this);
			H->SetMaterial(0, Mid);
			FRandomStream Rd((int32)Sd);
			TArray<FTransform> Xs; Xs.Reserve(Count);
			// (the list of 2026-11-07: "the rain does not look like raindrops, instead they look like white rods": each drop was
			// the engine's plane pitched up with its 60 cm across and its 1.6 cm up (a falling bar), turned any way (some side on).
			// Now the plane's X (pitched up) is the streak's length and its Y its width, every drop facing the field's +X, and the
			// field turned each frame to face the camera; the material makes each a soft streak, thin at its ends)
			// (PR #27's review: turned with the camera's yaw, the drops turned with the view and stood still on the screen as she
			// looked round. Each drop is now two such planes crossed, one facing the field's +X and one its +Y, so from any way
			// one faces the camera and the two read as one streak; the field keeps the world's axes)
			for (int32 K = 0; K < Count; ++K)
			{
				const FVector At(Rd.FRandRange(-1800.f, 1800.f), Rd.FRandRange(-1800.f, 1800.f), Rd.FRandRange(0.f, 1800.f));
				const FVector Sc = Scale * FVector(Rd.FRandRange(0.8f, 1.25f), 1.f, 1.f);
				Xs.Add(FTransform(FRotator(90.f, 0.f, 0.f), At, Sc));
				Xs.Add(FTransform(FRotator(90.f, 90.f, 0.f), At, Sc));
			}
			H->AddInstances(Xs, false, false, false);
			// (the field is far larger than its instances' boxes once they move: never culled away)
			H->BoundsScale = 20.f;
			H->SetVisibility(false);
		}
		const bool bOn = Amount > 0.03f && !bInside;
		H->SetVisibility(bOn);
		if (!bOn) return;
		H->SetWorldLocationAndRotation(FVector(Cam.X, Cam.Y, Cam.Z - 600.f), FRotator::ZeroRotator);
		Mid->SetScalarParameterValue(TEXT("Amount"), FMath::Clamp(Amount, 0.f, 1.f));
		Mid->SetVectorParameterValue(TEXT("Origin"), FLinearColor(Cam.X, Cam.Y, Cam.Z - 600.f, 0.f));
		Mid->SetScalarParameterValue(TEXT("Wind"), FMath::Clamp(SkyWind, 0.f, 1.2f));
		Mid->SetScalarParameterValue(TEXT("Bright"), FMath::Lerp(0.07f, 1.f, DayLight));
	};
	// (a rain streak 26 cm long and 0.9 cm wide (a drop's fall over about a 30th of a second); a snow flake 4 cm)
	Drops(RainDrops, RainDropMID, RainDropMaterial, 4500, FVector(RainStreak.X, RainStreak.Y, 1.f), 0xA11Bu, bSkySnowing ? 0.f : SkyRain);
	Drops(SnowDrops, SnowDropMID, SnowDropMaterial, 2500, FVector(0.04f, 0.04f, 1.f), 0x5E0Au, bSkySnowing ? SkyRain : 0.f);
	Fx(WeatherRain, RainFx, SkyRain > 0.3f && !bSkySnowing && !bInside, Cam + FVector(0, 0, 400.f));
	Fx(WeatherSnow, SnowFx, SkyRain > 0.3f && bSkySnowing && !bInside, Cam + FVector(0, 0, 400.f));
	Fx(WeatherWind, WindFx, SkyWind > 0.42f && !bSkySnowing && !bInside, L + FVector(0, 0, 150.f));
	SkyApplyT += Dt;
	if (SkyApplyT >= 0.25f) { SkyApplyT = 0.f; ApplySky7(); }
}

void ARDDungeonGenerator::ApplySky7()
{
	if (!bSky7) return;
	const float Night = 1.f - DayLight;
	// (gusts on the wind)
	const float Gust = 0.75f + 0.25f * FMath::PerlinNoise1D(SkyTime * 0.11f) + 0.15f * FMath::PerlinNoise1D(SkyTime * 0.47f + 3.f);
	const float Wind = FMath::Clamp(SkyWind * Gust, 0.f, 1.2f);
	// (cloudless: the cloud layer hidden, set only when the weather turns to or from it, so a test that hides the sky's parts
	// itself is not undone four times a second)
	const bool bCloudless = Weather == RDWeatherCloudless;
	if (SkyClouds && bCloudless != bSkyCloudless) { SkyClouds->SetVisibility(!bCloudless); bSkyCloudless = bCloudless; }
	if (SkyCloudMID)
	{
		SkyCloudMID->SetScalarParameterValue(TEXT("Cloud_GlobalCoverage"), FMath::Lerp(SkyCoverRange.X, SkyCoverRange.Y, SkyCover));
		SkyCloudMID->SetScalarParameterValue(TEXT("StormClouds"), RDSkySmooth(0.85f, 1.f, SkyCover) * FMath::Clamp(SkyRain, 0.f, 1.f));
	}
	if (SkyStarsMID)
	{
		// (after the dusk: none while the sky still glows)
		const float Clear = FMath::Pow(FMath::Clamp(1.f - SkyCover, 0.f, 1.f), 1.6f) * (1.f - SkyFog);
		SkyStarsMID->SetScalarParameterValue(TEXT("Bright"), (1.f - RDSkySmooth(0.02f, 0.3f, DayLight)) * Clear);
	}
	if (SkyHighMID)
	{
		SkyHighMID->SetScalarParameterValue(TEXT("Bright"), FMath::Lerp(0.05f, 1.f, DayLight) * FMath::Lerp(0.35f, 1.f, SkyCover));
		// (the high clouds are drawn over the volumetric ones, which lie below them: thinned as the cover closes, none overcast)
		SkyHighMID->SetScalarParameterValue(TEXT("Amount"), bCloudless ? 0.f : 1.f - RDSkySmooth(0.45f, 0.85f, SkyCover));
	}
	if (SkyMoonMID && DayMoon)
	{
		const float Up = RDSkySmooth(-0.03f, 0.05f, -DayMoon->GetForwardVector().Z);
		SkyMoonMID->SetScalarParameterValue(TEXT("Bright"), Up * FMath::Lerp(0.25f, 1.f, Night) * FMath::Lerp(1.f, 0.12f, RDSkySmooth(0.5f, 0.95f, SkyCover)));
	}
	// (fog and rain thicken the haze; the clouds' dimming of the sun, the moon and the sky light is ApplyDayNight's)
	// (Graymourne, "a fog bound port" (the user's of 2026-11-07): its own fog round it, eased in from 1.6 km off and whole within
	// 700 m of its middle, a step a call)
	{
		const bool bPortNear = bWild && WildTownIdx >= 0 && TownPlan == 3;
		const float Want = bPortNear ? 1.f - FMath::Clamp((LoadedTownDistM - 700.f) / 900.f, 0.f, 1.f) : 0.f;
		PortFog = FMath::FInterpConstantTo(PortFog, Want, 1.f, 0.04f);
	}
	// (the haze over the far land: the fog's opacity capped low in clear air, up to the level's own as the weather's and the port's
	// fog thicken; set only when it differs, a render-thread update otherwise four times a second)
	if (DayFog)
	{
		if (DayFogMax < 0.f) DayFogMax = DayFog->FogMaxOpacity;          // (the level's, read once)
		const float Fogness = FMath::Clamp(FMath::Max(SkyFog, PortFog), 0.f, 1.f);
		const float Cap = FogMaxOpacityWant >= 0.f ? FogMaxOpacityWant
			: (bWild && FogClearMaxOpacity >= 0.f ? FMath::Lerp(FMath::Min(FogClearMaxOpacity, DayFogMax), DayFogMax, Fogness) : DayFogMax);
		if (!FMath::IsNearlyEqual(DayFog->FogMaxOpacity, Cap, 0.002f)) DayFog->SetFogMaxOpacity(Cap);
	}
	if (DayFog)
	{
		DayFog->SetFogDensity(DayFogDensity * (1.f + 3.5f * SkyFog + 0.6f * SkyRain + PortFogBoost * PortFog));
		// (the port's fog reaches the town itself: the wilds' fog starts 250 m out, so at density x 9 the whole town stayed clear
		// (884 gm1's pictures: the wall 80 m off sharp))
		DayFog->SetStartDistance(FMath::Lerp(DayFogStart, FMath::Min(PortFogStart, DayFogStart), PortFog));
	}
	if (WindCollection) UKismetMaterialLibrary::SetScalarParameterValue(this, WindCollection, TEXT("Strength"), Wind);
	// (the rain's and the wind's sounds: loops, not placed)
	auto Loop = [&](TObjectPtr<UAudioComponent>& A, const TCHAR* Key, float Vol)
	{
		const FRDSoundSet* Set = Sounds.Find(FName(Key));
		if (!Set || Set->Sounds.Num() == 0 || !Set->Sounds[0]) return;
		if (!IsValid(A))
		{
			A = NewObject<UAudioComponent>(this);
			A->bAutoActivate = false; A->bAutoDestroy = false; A->bAllowSpatialization = false; A->bIsUISound = false;
			A->SetupAttachment(RootComponent); A->RegisterComponent();
			A->SetSound(Set->Sounds[0]);
		}
		const float V = Vol * Set->Volume * UserVolumeOf(FName(Key));
		if (V > 0.01f) { if (!A->IsPlaying()) A->Play(FMath::FRand() * 5.f); A->SetVolumeMultiplier(V); }
		else if (A->IsPlaying()) A->Stop();
	};
	Loop(WeatherRainSound, TEXT("Weather.Rain"), bSkySnowing ? 0.f : FMath::Clamp(SkyRain, 0.f, 1.f));
	Loop(WeatherWindSound, TEXT("Weather.Wind"), FMath::Clamp(0.08f + Wind * 0.8f, 0.f, 1.f) * (bWild ? 1.f : 0.5f));
}

FString ARDDungeonGenerator::GetHazeState() const
{
	const FLinearColor C = DayFog ? DayFog->FogInscatteringLuminance : FLinearColor::Black;
	return FString::Printf(TEXT("%.3f|%.4f,%.4f,%.4f|%.3f"), DayFog ? DayFog->FogMaxOpacity : -1.f, C.R, C.G, C.B, DayFogMax);
}

FString ARDDungeonGenerator::GetSkyState() const
{
	// "<weather>|<cover>|<rain>|<wind>|<fog>|<snowing>|<changes>|<seconds to the next>|<clouds>|<stars bright>|<moon bright>|<fog cutoff m>
	//  |<rain on>|<snow on>|<wind fx>|<high clouds' drift cm>|<high dome's yaw>|<their wind x>|<their wind y>"
	float Sb = -1.f, Mb = -1.f;
	if (SkyStarsMID) SkyStarsMID->GetScalarParameterValue(FName(TEXT("Bright")), Sb);
	if (SkyMoonMID) SkyMoonMID->GetScalarParameterValue(FName(TEXT("Bright")), Mb);
	const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	return FString::Printf(TEXT("%s|%.2f|%.2f|%.2f|%.2f|%d|%d|%.0f|%d|%.3f|%.3f|%.0f|%d|%d|%d|%.0f|%.3f|%.3f|%.3f"), *WeatherName(Weather), SkyCover, SkyRain, SkyWind, SkyFog, bSkySnowing ? 1 : 0, WeatherChanges,
		WeatherUntil - Now, SkyClouds ? 1 : 0, Sb, Mb, DayFog ? DayFog->FogCutoffDistance / 100.f : -1.f,
		(IsValid(WeatherRain) && WeatherRain->IsActive()) || (IsValid(RainDrops) && RainDrops->IsVisible()) ? 1 : 0,
		(IsValid(WeatherSnow) && WeatherSnow->IsActive()) || (IsValid(SnowDrops) && SnowDrops->IsVisible()) ? 1 : 0, IsValid(WeatherWind) && WeatherWind->IsActive() ? 1 : 0,
		SkyHighDrift, SkyHigh ? SkyHigh->GetComponentRotation().Yaw : 0.f, SkyHighWindDir.X, SkyHighWindDir.Y);
}
