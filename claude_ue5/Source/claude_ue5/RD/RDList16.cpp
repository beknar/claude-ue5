// The user's list of 2026-11-22 (docs/improvements16.txt; the plan docs/improvements16_plan.md), its first phase: the frame rate measured
// in the packaged game, before and after the list's changes (docs/performance.md, pipeline/perf_mistward.ps1).
// -RDPerf=<file>:
//   - in the wilds' level: each city by the map's travel, its square and a street about 100 m off it, at noon and at midnight; then each
//     biome at its nearest site to Brokenspire (put down on dry open ground by the map's put-down), at noon, standing, then running 30 s
//     from there (the frames while the ground streams in);
//   - in the castle's or a dungeon's level: its first hall.
//   Clear weather, her HUD hidden, facing the longest clear line from her eyes; each place settled 20 s after the world round her is built,
//   then measured until both 15 s and 300 frames have passed (at most 45 s); a picture of each place (<file>_shots/).
//   Lines: "perf|info|<WxH>|<GPU>|<when>|<quality>|<screen %>", "place|<kind>|<name>|<hour>|<x>|<y>|<z>|<yaw>" (where it stood: replayed by
//   -RDPerfPlaces=<file>), "perf|<kind>|<name>|<hour>|<fps>|<p95 ms>|<p99 ms>|<game ms>|<draw ms>|<rhi ms>|<gpu ms>|<frames>|<x m>|<y m>|
//   <biome there>|<metres run>", "perf|<kind>|<name>|<hour>|skipped|<why>", "perf|done" at the end; then the game quits.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDSection.h"
#include "RD/RDCombat.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/HUD.h"
#include "GameFramework/PlayerController.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformTime.h"
#include "HAL/IConsoleManager.h"
#include "RenderTimer.h"
#include "DynamicRHI.h"
#include "RHI.h"
#include "Scalability.h"
#include "UnrealClient.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList16, Log, All);

namespace
{
	const float RDPerf16Settle = 20.f, RDPerf16Measure = 15.f, RDPerf16MeasureMax = 45.f, RDPerf16Run = 30.f, RDPerf16Give = 240.f;
	const int32 RDPerf16Frames = 300;

	// (the yaw of the longest clear line from a point at eye height, of 16 ways, up to 300 m)
	float RDPerf16Yaw(const UWorld* W, const FVector& Eye, const AActor* Her)
	{
		float BestYaw = 0.f, Best = -1.f;
		FCollisionQueryParams Q(SCENE_QUERY_STAT(RDPerf16), false, Her);
		for (int32 K = 0; K < 16; ++K)
		{
			const float Yaw = K * 22.5f;
			const FVector To = Eye + FRotator(0.f, Yaw, 0.f).Vector() * 30000.f;
			FHitResult H;
			const float D = W && W->LineTraceSingleByChannel(H, Eye, To, ECC_Visibility, Q) ? H.Distance : 30000.f;
			if (D > Best) { Best = D; BestYaw = Yaw; }
		}
		return BestYaw;
	}

	FString RDPerf16Key(const FString& Kind, const FString& Name, float Hour) { return FString::Printf(TEXT("%s|%s|%.0f"), *Kind, *Name, Hour); }

	void RDPerf16Write(const FString& File, const FString& Line)
	{
		FFileHelper::SaveStringToFile(Line + TEXT("\n"), *File, FFileHelper::EEncodingOptions::AutoDetect, &IFileManager::Get(), FILEWRITE_Append);
	}
}

void ARDDungeonGenerator::TickPerf16(APawn* P)
{
	if (!bPerf16Read)
	{
		bPerf16Read = true;
		if (!FParse::Value(FCommandLine::Get(), TEXT("RDPerf="), Perf16File) || Perf16File.IsEmpty()) { Perf16File.Reset(); return; }
		// (the castle's and a dungeon's legs go on from the town by -RDTownGo: the town measures nothing then, the level it leads to does)
		FString Go;
		if (bTown && FParse::Value(FCommandLine::Get(), TEXT("RDTownGo="), Go) && !Go.IsEmpty()) { Perf16File.Reset(); return; }
		Perf16Shots = FPaths::GetPath(Perf16File) / (FPaths::GetBaseFilename(Perf16File) + TEXT("_shots"));
		// (an earlier run's places, replayed exactly: the later runs stand where BEFORE stood)
		FString Rp;
		if (FParse::Value(FCommandLine::Get(), TEXT("RDPerfPlaces="), Rp))
		{
			TArray<FString> Lines;
			FFileHelper::LoadFileToStringArray(Lines, *Rp);
			for (const FString& L : Lines)
			{
				TArray<FString> F; L.ParseIntoArray(F, TEXT("|"), false);
				if (F.Num() < 8 || F[0] != TEXT("place")) continue;
				FPerf16Place Pl; Pl.Kind = F[1]; Pl.Name = F[2]; Pl.Hour = FCString::Atof(*F[3]); Pl.bFixed = true;
				Pl.At = FVector(FCString::Atod(*F[4]), FCString::Atod(*F[5]), FCString::Atod(*F[6])); Pl.Yaw = FCString::Atof(*F[7]);
				Perf16Replay.Add(RDPerf16Key(Pl.Kind, Pl.Name, Pl.Hour), Pl);
			}
			UE_LOG(LogRDList16, Log, TEXT("RDPERF16 %d places to replay from %s"), Perf16Replay.Num(), *Rp);
		}
		const Scalability::FQualityLevels Q = Scalability::GetQualityLevels();
		const IConsoleVariable* Sp = IConsoleManager::Get().FindConsoleVariable(TEXT("r.ScreenPercentage"));
		RDPerf16Write(Perf16File, FString::Printf(TEXT("perf|info|%dx%d|%s|%s|%d|%.0f|%s"), GSystemResolution.ResX, GSystemResolution.ResY, *GRHIAdapterName,
			*FDateTime::Now().ToString(TEXT("%Y-%m-%d %H:%M")), Q.GetSingleQualityLevel(), Sp ? Sp->GetFloat() : -1.f, *GetWorld()->GetName()));
		UE_LOG(LogRDList16, Log, TEXT("RDPERF16 measuring into %s"), *Perf16File);
	}
	if (Perf16File.IsEmpty() || !P || !GetWorld()) return;
	if (bTown && !bTownPlaced) return;
	const float Dt = FApp::GetDeltaTime();
	Perf16T += Dt;
	if (bWild) WildLastEngaged = GetWorld()->GetTimeSeconds();          // (no encounter of the director's while it measures)
	APlayerController* PC = Cast<APlayerController>(P->GetController());
	if (PC && PC->MyHUD) PC->MyHUD->bShowHUD = false;
	if (PlayerCombat && !PlayerCombat->IsDead()) PlayerCombat->SetHealth(PlayerCombat->GetMaxHealth());          // (a roamer's blow or the cold must not end the run)
	if (bWild && !IsWildReady()) return;
	// (the places, once the world is known)
	if (Perf16Index < 0)
	{
		if (bWild)
		{
			for (const FRDWildTown& T : Wild->Towns)
				for (const TCHAR* K : { TEXT("square"), TEXT("street") })
					for (const float H : { 12.f, 0.f }) { FPerf16Place Pl; Pl.Kind = K; Pl.Name = T.Name; Pl.SiteM = T.Site; Pl.Hour = H; Perf16Places.Add(Pl); }
			for (int32 B = 0; B < Wild->Biomes.Num(); ++B)
			{
				double Best = 1e18; FVector2D Bs; bool bAny = false;
				for (int32 K = 0; K < Wild->CellBiome.Num(); ++K)
					if (Wild->CellBiome[K] == B) { const double D = Wild->CellSite[K].Size(); if (D < Best) { Best = D; Bs = Wild->CellSite[K]; bAny = true; } }
				if (!bAny) continue;
				FPerf16Place Pl; Pl.Kind = TEXT("biome"); Pl.Name = Wild->Biomes[B].Name; Pl.SiteM = Bs; Perf16Places.Add(Pl);
				Pl.Kind = TEXT("run"); Perf16Places.Add(Pl);
			}
		}
		else { FPerf16Place Pl; Pl.Kind = TEXT("hall"); Pl.Name = GetWorld()->GetName(); Perf16Places.Add(Pl); }
		for (FPerf16Place& Pl : Perf16Places) if (const FPerf16Place* R = Perf16Replay.Find(RDPerf16Key(Pl.Kind, Pl.Name, Pl.Hour))) { Pl.bFixed = true; Pl.At = R->At; Pl.Yaw = R->Yaw; }
		Perf16Index = 0; Perf16Stage = 0; Perf16T = 0.f;
	}
	if (!Perf16Places.IsValidIndex(Perf16Index))
	{
		RDPerf16Write(Perf16File, TEXT("perf|done"));
		UE_LOG(LogRDList16, Log, TEXT("RDPERF16 done"));
		Perf16File.Reset();
		FPlatformMisc::RequestExit(false);
		return;
	}
	const FPerf16Place Pl = Perf16Places[Perf16Index];
	auto Next = [&](const TCHAR* Why)
	{
		if (Why) RDPerf16Write(Perf16File, FString::Printf(TEXT("perf|%s|%s|%.0f|skipped|%s"), *Pl.Kind, *Pl.Name, Pl.Hour, Why));
		++Perf16Index; Perf16Stage = 0; Perf16T = 0.f; Perf16Ready = 0.f;
	};
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	const bool bCity = Pl.Kind == TEXT("square") || Pl.Kind == TEXT("street");
	const bool bRun = Pl.Kind == TEXT("run");
	switch (Perf16Stage)
	{
	case 0:
	{
		// (there: a city by the map's travel (forced: a run cannot wait out a fight), a biome by the map's put-down (the run goes on from
		// where the biome's stand was); the hour, clear weather, held)
		bool bOk = true;
		if (bCity) { if (TownName != Pl.Name) { bTravelForced = true; bOk = WildTravelToTown(Pl.Name); bTravelForced = false; } }
		else if (Pl.Kind == TEXT("biome")) bOk = WildPutDownNear(Pl.bFixed ? FVector2D(Pl.At.X / 100.0, Pl.At.Y / 100.0) : Pl.SiteM);
		if (!bOk) { Next(bCity ? TEXT("travel refused") : TEXT("no ground to stand on")); return; }
		if (bTown) { SetTownHour(Pl.Hour); SetWeather(0, true); }
		Perf16Stage = 1; Perf16T = 0.f; Perf16Ready = 0.f;
		return;
	}
	case 1:
	{
		// (the world round her built: the city (for a city's places), the chunks asked and made, the dungeon's set; then placed)
		// (out in the wilds there is no town section: the section is waited for only where there is one to build, a city's or a hall's)
		const bool bNeedS = bCity || !bWild;
		const bool bBusy = (bWild && (WildInFlight.Num() > 0 || WildBuilding.Num() > 0)) || bTownLoading || bTownTraveling || (bNeedS && (!S || S->IsBuilding())) || (S && S->IsBuilding())
			|| (bCity && TownName != Pl.Name);
		if (Perf16T > RDPerf16Give) { Next(TEXT("the world round her was not built in 240 s")); return; }
		if (bBusy) { Perf16Ready = 0.f; return; }
		Perf16Ready += Dt;
		if (Perf16Ready < 2.f) return;
		if (Pl.bFixed && !bRun)
		{
			P->SetActorLocation(Pl.At, false, nullptr, ETeleportType::TeleportPhysics);
		}
		else if (bCity)
		{
			const FIntPoint Sq((S->TownSquare.Min.X + S->TownSquare.Max.X) / 2, (S->TownSquare.Min.Y + S->TownSquare.Max.Y) / 2);
			FIntPoint T = Sq;
			if (Pl.Kind == TEXT("street"))
			{
				// (a road's tile nearest 100 m (33 tiles) from the square's middle)
				float Best = 1e9f;
				for (const FIntRect& R : S->TownRoads)
					for (int32 X = R.Min.X; X < R.Max.X; ++X) for (int32 Y = R.Min.Y; Y < R.Max.Y; ++Y)
					{
						const float D = FMath::Abs(FVector2D::Distance(FVector2D(X, Y), FVector2D(Sq)) - 33.f);
						if (D < Best) { Best = D; T = FIntPoint(X, Y); }
					}
			}
			P->SetActorLocation(S->LocalToWorld(T) + FVector(0, 0, 100.f), false, nullptr, ETeleportType::TeleportPhysics);
		}
		if (ACharacter* Ch = Cast<ACharacter>(P)) Ch->GetCharacterMovement()->StopMovementImmediately();
		const float Yaw = Pl.bFixed && !bRun ? Pl.Yaw : bRun ? P->GetActorRotation().Yaw : RDPerf16Yaw(GetWorld(), P->GetActorLocation() + FVector(0, 0, 70.f), P);
		P->SetActorRotation(FRotator(0.f, Yaw, 0.f));
		if (PC) PC->SetControlRotation(FRotator(-5.f, Yaw, 0.f));
		Perf16Stage = 2; Perf16T = 0.f;
		return;
	}
	case 2:
	{
		// (settled: what the place streams in after she stands there (textures, the near grass) comes in its first seconds; a run starts
		// at once from the stand it follows)
		if (!bRun && Perf16T < RDPerf16Settle) return;
		const FVector At = P->GetActorLocation();
		RDPerf16Write(Perf16File, FString::Printf(TEXT("place|%s|%s|%.0f|%.0f|%.0f|%.0f|%.1f"), *Pl.Kind, *Pl.Name, Pl.Hour, At.X, At.Y, At.Z, P->GetActorRotation().Yaw));
		if (!bRun)
		{
			IFileManager::Get().MakeDirectory(*Perf16Shots, true);
			FScreenshotRequest::RequestScreenshot(Perf16Shots / FString::Printf(TEXT("%s_%s_%02.0f.png"), *Pl.Kind, *Pl.Name.Replace(TEXT(" "), TEXT("_")), Pl.Hour), false, false);
		}
		if (bRun && PlayerCombat) PlayerCombat->SetRunMode(true);
		Perf16Stage = 3; Perf16T = 0.f; Perf16Frames.Reset(); Perf16Game = Perf16Draw = Perf16Rhi = Perf16Gpu = 0.0; Perf16From = At;
		return;
	}
	case 3:
	{
		if (bRun)
		{
			// (on along her way; blocked (under a metre a second over the last second), a quarter turn)
			P->AddMovementInput(FRotator(0.f, P->GetActorRotation().Yaw, 0.f).Vector(), 1.f);
			if (ACharacter* Ch = Cast<ACharacter>(P); Ch && Perf16T > 2.f && Ch->GetVelocity().Size2D() < 100.f)
			{
				const float Yaw = P->GetActorRotation().Yaw + 90.f;
				P->SetActorRotation(FRotator(0.f, Yaw, 0.f)); if (PC) PC->SetControlRotation(FRotator(-5.f, Yaw, 0.f));
			}
		}
		Perf16Frames.Add(Dt);
		Perf16Game += FPlatformTime::ToMilliseconds(GGameThreadTime); Perf16Draw += FPlatformTime::ToMilliseconds(GRenderThreadTime);
		Perf16Rhi += FPlatformTime::ToMilliseconds(GRHIThreadTime); Perf16Gpu += FPlatformTime::ToMilliseconds(RHIGetGPUFrameCycles(0));
		const int32 N = Perf16Frames.Num();
		if (bRun ? Perf16T < RDPerf16Run : (Perf16T < RDPerf16MeasureMax && (Perf16T < RDPerf16Measure || N < RDPerf16Frames))) return;
		if (bRun && PlayerCombat) PlayerCombat->SetRunMode(false);
		double Sum = 0.0; for (const float F : Perf16Frames) Sum += F;
		TArray<float> Sorted = Perf16Frames; Sorted.Sort();
		auto Pct = [&](float Q) { return 1000.f * Sorted[FMath::Clamp(FMath::FloorToInt(N * Q), 0, N - 1)]; };
		const FVector Her = P->GetActorLocation();
		FString Biome = TEXT("-");
		if (bWild) { FRDWSample Q; Wild->Sample(Her.X / 100.0, Her.Y / 100.0, Q, false); Biome = Wild->BiomeName(Q.Biome); }
		const FString L = FString::Printf(TEXT("perf|%s|%s|%.0f|%.1f|%.1f|%.1f|%.2f|%.2f|%.2f|%.2f|%d|%.0f|%.0f|%s|%.0f"), *Pl.Kind, *Pl.Name, Pl.Hour, N / FMath::Max(Sum, 1e-6), Pct(0.95f), Pct(0.99f),
			Perf16Game / N, Perf16Draw / N, Perf16Rhi / N, Perf16Gpu / N, N, Her.X / 100.0, Her.Y / 100.0, *Biome, bRun ? FVector::Dist2D(Her, Perf16From) / 100.0 : 0.0);
		RDPerf16Write(Perf16File, L);
		UE_LOG(LogRDList16, Log, TEXT("RDPERF16 %s"), *L);
		Next(nullptr);
		return;
	}
	}
}
