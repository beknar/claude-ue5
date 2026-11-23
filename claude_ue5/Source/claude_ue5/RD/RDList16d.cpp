// The user's list of 2026-11-22 (docs/improvements16.txt; the plan docs/improvements16_plan.md), its sixth phase: the cities' lights,
// people and Heaven's dome by their distance from the camera (four times a second, TickTownLod16):
//   - a town's point lights drawn to 45 m, fading out from 35 m (they were drawn to 90 m), but the street lamps (tagged
//     RDStreetLamp16: Heaven's) kept to 90 m: an avenue is not black beyond 45 m; a light built to cast shadows casts them only within
//     18 m of the camera (20 m to let go: no flicker on the line);
//   - the townsfolk and the town's animals animated at full rate under 15 m, every second frame to 40 m, every fourth to 80 m, every
//     eighth to 110 m, and beyond 110 m not drawn, their logic ticked once a second (their day goes on: never frozen);
//   - Heaven's shield dome drawn only while the camera is outside it.
// rd.TownLod 0 puts everything back as it was (the tests' and the measures' comparison).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Camera/PlayerCameraManager.h"
#include "HAL/IConsoleManager.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList16d, Log, All);

namespace
{
	TAutoConsoleVariable<int32> CVarRDTownLod(TEXT("rd.TownLod"), 1, TEXT("The towns' lights, people and dome by distance (1), or all drawn and ticked at full rate as before (0)"));
	const FName RDStreetLampTag16(TEXT("RDStreetLamp16"));
	const FName RDHeavenDomeTag16(TEXT("HeavenDome"));
}

FName ARDDungeonGenerator::StreetLampTag16() { return RDStreetLampTag16; }

void ARDDungeonGenerator::TickTownLod16(float Dt)
{
	TownLodTimer16 -= Dt;
	if (TownLodTimer16 > 0.f) return;
	TownLodTimer16 = 0.25f;
	const bool bOn = CVarRDTownLod.GetValueOnGameThread() != 0;
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	if (!PC || !PC->PlayerCameraManager) return;
	const FVector Cam = PC->PlayerCameraManager->GetCameraLocation();
	// ---- the town's lights, gathered once per section once it is built (the saved Brokenspire's too: what they were built with is read
	// from them); gathered while a wilderness city was still being built, they missed nearly all its lights (884 dist16's first run)
	if (S && S->IsBuilding()) return;
	int32 NowLights = 0;
	if (S) { TArray<UPointLightComponent*> Ls0; S->GetComponents<UPointLightComponent>(Ls0); NowLights = Ls0.Num(); }
	if (S != TownLodFor16.Get() || NowLights != TownLodLightsSeen16)
	{
		TownLodLightsSeen16 = NowLights;
		// (those changed before are put back first: a light gathered again keeps what it was built with)
		for (FTownLight16& Tl : TownLights16) if (UPointLightComponent* L = Tl.L.Get()) { L->MaxDrawDistance = Tl.Draw0; L->MaxDistanceFadeRange = Tl.Fade0; if (L->CastShadows != Tl.bShadows) L->SetCastShadows(Tl.bShadows); }
		TownLodFor16 = S; TownLights16.Reset(); TownDome16 = nullptr;
		if (S)
		{
			TArray<UPointLightComponent*> Ls; S->GetComponents<UPointLightComponent>(Ls);
			for (UPointLightComponent* L : Ls)
			{
				FTownLight16 Tl; Tl.L = L; Tl.bShadows = L->CastShadows; Tl.bLamp = L->ComponentHasTag(RDStreetLampTag16); Tl.Draw0 = L->MaxDrawDistance; Tl.Fade0 = L->MaxDistanceFadeRange;
				TownLights16.Add(Tl);
			}
			TArray<UStaticMeshComponent*> Ms; S->GetComponents<UStaticMeshComponent>(Ms);
			for (UStaticMeshComponent* M : Ms) if (M->ComponentHasTag(RDHeavenDomeTag16)) { TownDome16 = M; break; }
		}
		bTownLodApplied16 = !bOn;          // (applied below)
	}
	if (bOn != bTownLodApplied16)
	{
		for (FTownLight16& Tl : TownLights16)
		{
			UPointLightComponent* L = Tl.L.Get(); if (!L) continue;
			if (bOn && !Tl.bLamp) { L->MaxDrawDistance = 4500.f; L->MaxDistanceFadeRange = 1000.f; }
			else { L->MaxDrawDistance = Tl.Draw0; L->MaxDistanceFadeRange = Tl.Fade0; }
			if (!bOn && L->CastShadows != Tl.bShadows) L->SetCastShadows(Tl.bShadows);
			L->MarkRenderStateDirty();
		}
		bTownLodApplied16 = bOn;
	}
	TownShadowing16 = 0;
	if (bOn)
		for (FTownLight16& Tl : TownLights16)
		{
			UPointLightComponent* L = Tl.L.Get(); if (!L || !Tl.bShadows) continue;
			const float D = FVector::Dist(L->GetComponentLocation(), Cam);
			const bool bWant = D < (L->CastShadows ? 2000.f : 1800.f);
			if (bWant != L->CastShadows) L->SetCastShadows(bWant);
			if (bWant) ++TownShadowing16;
		}
	// ---- the people and animals
	auto Band = [&](AActor* A, const TArray<USkeletalMeshComponent*>& Ms)
	{
		const float D = FVector::Dist(A->GetActorLocation(), Cam);
		const int32 B = !bOn ? 0 : D < 1500.f ? 0 : D < 4000.f ? 1 : D < 8000.f ? 2 : D < 11000.f ? 3 : 4;
		static const float Rate[5] = { 0.f, 1.f / 30.f, 1.f / 15.f, 1.f / 7.5f, 1.f };
		for (USkeletalMeshComponent* M : Ms)
		{
			if (!M) continue;
			if (!FMath::IsNearlyEqual(M->PrimaryComponentTick.TickInterval, Rate[B])) M->SetComponentTickInterval(Rate[B]);
			const bool bDraw = B < 4;
			if (M->IsVisible() != bDraw && !A->IsHidden()) M->SetVisibility(bDraw);
		}
		A->SetActorTickInterval(B == 4 ? 1.f : 0.f);
		++TownBands16[B];
	};
	for (int32& N : TownBands16) N = 0;
	for (ARDTownsfolk* T : TownPeople)
	{
		if (!IsValid(T)) continue;
		TArray<USkeletalMeshComponent*> Ms; T->GetComponents<USkeletalMeshComponent>(Ms);
		Band(T, Ms);
	}
	for (ARDTownAnimal* A : TownAnimalActors)
	{
		if (!IsValid(A)) continue;
		TArray<USkeletalMeshComponent*> Ms; A->GetComponents<USkeletalMeshComponent>(Ms);
		Band(A, Ms);
	}
	// ---- the dome from outside only
	if (UStaticMeshComponent* Dm = TownDome16.Get(); Dm && S)
	{
		const bool bOutside = !bOn || FVector::Dist(Cam, Dm->GetComponentLocation()) > S->HeavenDomeRadius;
		if (Dm->IsVisible() != bOutside) Dm->SetVisibility(bOutside);
	}
}

FString ARDDungeonGenerator::GetTownLod16() const
{
	// (tests: "<on>|<lights>|<built to shadow>|<shadowing now>|<street lamps>|<people and animals by band: full|half|quarter|eighth|not drawn>|<dome drawn>")
	int32 Sh = 0, La = 0;
	for (const FTownLight16& Tl : TownLights16) { if (Tl.bShadows) ++Sh; if (Tl.bLamp) ++La; }
	const UStaticMeshComponent* Dm = TownDome16.Get();
	return FString::Printf(TEXT("%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d"), CVarRDTownLod.GetValueOnGameThread(), TownLights16.Num(), Sh, TownShadowing16, La,
		TownBands16[0], TownBands16[1], TownBands16[2], TownBands16[3], TownBands16[4], Dm ? (Dm->IsVisible() ? 1 : 0) : -1);
}

TArray<FString> ARDDungeonGenerator::GetTownLodLines16() const
{
	// (tests: a line a townsperson or animal: "<name>|<distance from the camera cm>|<its body's tick interval>|<drawn>|<x>|<y>")
	TArray<FString> Out;
	const APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	if (!PC || !PC->PlayerCameraManager) return Out;
	const FVector Cam = PC->PlayerCameraManager->GetCameraLocation();
	auto Add = [&](const AActor* A, const USkeletalMeshComponent* M)
	{
		if (!IsValid(A) || !M) return;
		const FVector L = A->GetActorLocation();
		Out.Add(FString::Printf(TEXT("%s|%.0f|%.4f|%d|%.0f|%.0f"), *A->GetName(), FVector::Dist(L, Cam), M->PrimaryComponentTick.TickInterval, M->IsVisible() && !A->IsHidden() ? 1 : 0, L.X, L.Y));
	};
	for (const ARDTownsfolk* T : TownPeople) if (IsValid(T)) Add(T, T->GetBody());
	for (const ARDTownAnimal* A : TownAnimalActors) if (IsValid(A)) Add(A, A->GetBody());
	return Out;
}
