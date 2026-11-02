// Brokenspire's day and night (the user's of 2026-11-02: "create a day night cycle where a full day can elapse within a half
// hour"). The town's clock runs DayLengthSeconds for 24 hours (1800 s by default) while play runs in the town (it stands
// still under a panel's pause and in the castle, which is indoors; the game instance keeps the hour between the levels). The
// sun (the level's atmosphere sun, 881's BS_Sun) rises in the east at 6, stands highest at noon and sets in the west at 18;
// a moon made in play (the atmosphere's second light, cold and dim, no shadows) crosses the sky opposite it. The sky light,
// the height fog's light and the exposure follow the daylight; the lamps and torches burn all day as they did.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDGameInstance.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/SkyLight.h"
#include "Engine/ExponentialHeightFog.h"
#include "Engine/PostProcessVolume.h"
#include "EngineUtils.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDTownDay, Log, All);

namespace
{
	/** the sun's height over the horizon (degrees) at an hour: 0 at 6 and 18, MaxElev at noon, below the horizon at night */
	float RDTDSunElevation(float Hour, float MaxElev) { return MaxElev * FMath::Sin((Hour - 6.f) / 12.f * PI); }
	/** its compass way (the yaw of the way to it): a half turn from its rising at 6 to its setting at 18 */
	float RDTDSunAzimuth(float Hour) { return 90.f + (Hour - 6.f) * 15.f; }
	/** a light's rotation that shines from a point in the sky at (elevation, azimuth) */
	FRotator RDTDLightFrom(float Elev, float Azim) { return FRotator(-Elev, Azim + 180.f, 0.f); }
	float RDTDSmooth(float A, float B, float X) { const float T = FMath::Clamp((X - A) / (B - A), 0.f, 1.f); return T * T * (3.f - 2.f * T); }
}

void ARDDungeonGenerator::BeginDayNight()
{
	DaySun = nullptr; DayMoon = nullptr; DaySky = nullptr; DayFog = nullptr; DayPost = nullptr;
	if (!bTown || !bDayNight) return;
	UWorld* W = GetWorld();
	for (TActorIterator<ADirectionalLight> It(W); It; ++It)
		if (UDirectionalLightComponent* L = Cast<UDirectionalLightComponent>(It->GetLightComponent()); L && L->IsUsedAsAtmosphereSunLight()) { DaySun = L; break; }
	for (TActorIterator<ASkyLight> It(W); It; ++It) { DaySky = It->GetLightComponent(); break; }
	for (TActorIterator<AExponentialHeightFog> It(W); It; ++It) { DayFog = It->GetComponent(); break; }
	for (TActorIterator<APostProcessVolume> It(W); It; ++It) if (It->bUnbound) { DayPost = *It; break; }
	if (!DaySun) { UE_LOG(LogRDTownDay, Warning, TEXT("RDDAY no atmosphere sun in the level: no day and night")); return; }
	// (what the level was saved with is the day's light: read once a play, before the clock has changed anything (the PR
	// review's find: begun again, the night's dimmed sun would have become the day's))
	if (!bDayBaseRead)
	{
		DaySunLux = DaySun->Intensity; DaySunColor = DaySun->GetLightColor();
		DaySkyLight = DaySky ? DaySky->Intensity : 1.f;
		DayFogLight = DayFog ? DayFog->FogInscatteringLuminance : FLinearColor(0.4f, 0.45f, 0.5f);
		DayBias = DayPost ? DayPost->Settings.AutoExposureBias : 0.f;
		bDayBaseRead = true;
	}
	// the moon: a second atmosphere light, dim and cold, without shadows (one: a moon made before is kept)
	if (!IsValid(DayMoonKept))
	{
		DayMoonKept = NewObject<UDirectionalLightComponent>(this, MakeUniqueObjectName(this, UDirectionalLightComponent::StaticClass(), TEXT("RDMoon")));
		DayMoonKept->SetupAttachment(RootComponent);
		DayMoonKept->SetMobility(EComponentMobility::Movable);
		DayMoonKept->SetAtmosphereSunLight(true);
		DayMoonKept->SetAtmosphereSunLightIndex(1);
		DayMoonKept->SetCastShadows(false);
		DayMoonKept->SetLightColor(FLinearColor(0.55f, 0.66f, 1.f));
		DayMoonKept->SetIntensity(0.f);
		DayMoonKept->RegisterComponent();
	}
	DayMoon = DayMoonKept;
	// the hour: the game's (back from the castle), else -RDTownHour=<h> (a reel), else the morning
	URDGameInstance* GI = URDGameInstance::Of(this);
	float H = TownStartHour;
	float Cmd = -1.f;
	if (FParse::Value(FCommandLine::Get(), TEXT("RDTownHour="), Cmd) && Cmd >= 0.f && (!GI || GI->TownHour < 0.f)) H = Cmd;
	if (GI && GI->TownHour >= 0.f) { H = GI->TownHour; TownDay = GI->TownDay; }
	TownHour = FMath::Fmod(H, 24.f);
	ApplyDayNight();
	UE_LOG(LogRDTownDay, Log, TEXT("RDDAY begun: day %d at %s (a day lasts %.0f s), sun %.1f lux, sky %.2f, exposure bias %.2f"), TownDay, *GetTownClock(), DayLengthSeconds, DaySunLux, DaySkyLight, DayBias);
}

void ARDDungeonGenerator::TickDayNight(float Dt)
{
	if (!DaySun || DayLengthSeconds <= 0.f || Dt <= 0.f || GetWorld()->IsPaused()) return;
	TownHour += Dt * 24.f / DayLengthSeconds;
	if (TownHour >= 24.f) { TownHour -= 24.f; ++TownDay; }
	if (URDGameInstance* GI = URDGameInstance::Of(this)) { GI->TownHour = TownHour; GI->TownDay = TownDay; }
	// (the lights four times a second: a quarter second is 1/7200 of the day, and every change sends the lights, the sky
	// light and the fog to the render thread again (the PR review's find: they were set every frame))
	DayApplyT += Dt;
	if (DayApplyT < 0.25f) return;
	DayApplyT = 0.f;
	ApplyDayNight();
}

void ARDDungeonGenerator::ApplyDayNight()
{
	if (!DaySun) return;
	const float Elev = RDTDSunElevation(TownHour, DayMaxSunElevation), Azim = RDTDSunAzimuth(TownHour);
	// (daylight: 0 at night (the sun 6 degrees under the horizon), 1 once it is 12 over it; the sun warmer near the horizon)
	DayLight = RDTDSmooth(-6.f, 12.f, Elev);
	const float SunUp = RDTDSmooth(-3.f, 4.f, Elev);
	DaySun->SetWorldRotation(RDTDLightFrom(FMath::Max(Elev, -10.f), Azim));
	DaySun->SetIntensity(DaySunLux * SunUp * FMath::Lerp(0.55f, 1.f, RDTDSmooth(0.f, 25.f, Elev)));
	const FLinearColor Low(1.f, 0.55f, 0.28f), High(1.f, 0.96f, 0.9f);
	DaySun->SetLightColor(FMath::Lerp(Low, High, RDTDSmooth(2.f, 30.f, Elev)) * DaySunColor);
	DaySun->SetCastShadows(SunUp > 0.01f);
	if (DayMoon)
	{
		const float Me = -Elev * 0.75f;      // (the moon opposite, not as high)
		DayMoon->SetWorldRotation(RDTDLightFrom(FMath::Max(Me, -10.f), Azim + 180.f));
		DayMoon->SetIntensity(MoonLux * RDTDSmooth(-2.f, 8.f, Me));
	}
	if (DaySky) DaySky->SetIntensity(DaySkyLight * FMath::Lerp(NightSkyShare, 1.f, DayLight));
	if (DayFog) DayFog->SetFogInscatteringColor(DayFogLight * FMath::Lerp(0.12f, 1.f, DayLight));
	if (DayPost)
	{
		DayPost->Settings.bOverride_AutoExposureBias = true;
		DayPost->Settings.AutoExposureBias = DayBias + NightExposureBias * (1.f - DayLight);
	}
}

void ARDDungeonGenerator::SetTownHour(float Hour)
{
	TownHour = FMath::Fmod(FMath::Max(0.f, Hour), 24.f);
	if (URDGameInstance* GI = URDGameInstance::Of(this)) { GI->TownHour = TownHour; GI->TownDay = TownDay; }
	ApplyDayNight();
}

FString ARDDungeonGenerator::GetTownClock() const
{
	const int32 Mins = FMath::FloorToInt(TownHour * 60.f);
	return FString::Printf(TEXT("%02d:%02d"), (Mins / 60) % 24, Mins % 60);
}

FString ARDDungeonGenerator::GetDayNightState() const
{
	const float Elev = RDTDSunElevation(TownHour, DayMaxSunElevation);
	return FString::Printf(TEXT("%d|%.3f|%.2f|%.3f|%.2f|%.3f|%.3f|%.2f"), TownDay, TownHour, Elev, DayLight, DaySun ? DaySun->Intensity : -1.f,
		DayMoon ? DayMoon->Intensity : -1.f, DaySky ? DaySky->Intensity : -1.f, DayPost ? DayPost->Settings.AutoExposureBias : 0.f);
}
