// The horse's reel (the user's of 2026-11-19: "when done, make a demo reel of the new horse riding, use the windows game bar facility
// to do it"): the Ultimate Horse Pack's horse ridden (RDHorse15.cpp) on the plains round Brokenspire, a scene each: getting on, the
// walk, the gallop gathering speed, turning at speed, the sudden stop, backing, a jump, a rear, swimming in a lake, getting down.
// A caption each (the HUD's reel caption, as RDReel15.cpp's), its timeline as seconds from the go on the real clock (Reel15Mark), for
// pipeline/blender_numpy/reel15_cut.py. In the packaged game: -RDReel16 [-RDShowReady=<file>] [-RDShowGo=<file>] [-RDShowDone=<file>]
// (pipeline/record_mistward_autoplay.ps1 -Reel16); in play from Python: StartReel16 (a rehearsal: Go empty, at once; bShots: a
// picture a scene).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDGameInstance.h"
#include "RD/RDCombat.h"
#include "RD/RDHorse.h"
#include "RD/RDSection.h"
#include "RD/RDWild.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDReel16, Log, All);

namespace
{
	struct FRD16Scene { const TCHAR* Name; const TCHAR* Title; const TCHAR* Line; float Secs; };
	const FRD16Scene RD16Scenes[] = {
		{ TEXT("mount"), TEXT("The new horse"), TEXT("The Ultimate Horse Pack's horse and saddle; up from its left by the pack's own mounting clip, fitted to each hero"), 4.2f },
		{ TEXT("walk"), TEXT("The walk"), TEXT("Walk mode: a brisk walk of 2 m/s, each hoof heard as it lands on the grass"), 6.f },
		{ TEXT("gallop"), TEXT("The gallop"), TEXT("Run mode: it gathers speed over three seconds to a natural gallop of 12 m/s"), 9.f },
		{ TEXT("turns"), TEXT("Turning at speed"), TEXT("It turns more slowly the faster it goes: wide arcs at the gallop"), 7.f },
		{ TEXT("stop"), TEXT("A sudden stop"), TEXT("Let go at the gallop, it sits back on its haunches and throws up dust"), 3.6f },
		{ TEXT("back"), TEXT("Backing up"), TEXT("Held back with the camera behind it, it steps backwards"), 3.6f },
		{ TEXT("jump"), TEXT("A jump"), TEXT("The jump: the pack's take-off, flight and landing, for horse and rider alike"), 6.f },
		{ TEXT("rear"), TEXT("Rearing"), TEXT("Standing or walking, the attack's button rears it"), 9.f },
		{ TEXT("swim"), TEXT("Swimming"), TEXT("In deep water it swims, slower, the saddle above the water"), 25.f },
		{ TEXT("dismount"), TEXT("Down to its side"), TEXT("F: it stops, and she climbs down beside it"), 9.f },
	};
	constexpr int32 RD16Num = UE_ARRAY_COUNT(RD16Scenes);
}

void ARDDungeonGenerator::StartReel16(const FString& Go, const FString& Done, bool bShots)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return;
	bReel16 = true; bReel16Going = false; bReel16Shots = bShots; Reel16Stage = -1; Reel16Sub = 0; Reel16T = 0.f;
	GI->ReelGo = Go; GI->ReelDone = Done; GI->ReelLog.Reset();
	UE_LOG(LogRDReel16, Log, TEXT("RDREEL16 armed (go %s)"), Go.IsEmpty() ? TEXT("at once") : *Go);
}

FString ARDDungeonGenerator::GetReel16State() const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	return FString::Printf(TEXT("%d|%d|%d|%.1f|%s"), bReel16 ? 1 : 0, Reel16Stage, Reel16Sub, Reel16T, GI && GI->ReelLog.Num() > 0 ? *GI->ReelLog.Last() : TEXT(""));
}

bool ARDDungeonGenerator::Reel16FindSpots()
{
	// (the plains: open, dry, gentle ground 2.5 to 9 km out, 1.2 km clear of every town's easing, with 500 m of it ahead along one way
	// (no water, no field or yard, no forest, no road, within 6 m of its start's height); a lake, river or pond 2 m deep or more
	// within 25 km, its shore the nearest dry ground out along 16 rays, the start 30 m back from it on land)
	if (!IsWildReady()) return false;
	auto Clear = [this](double X, double Y)
	{
		for (const FRDWildTown& T : Wild->Towns) if (FVector2D::Distance(FVector2D(X, Y), FVector2D(T.Site.X, T.Site.Y)) < T.EaseM + 1200.0) return false;
		return true;
	};
	auto Open = [this](double X, double Y, float& H)
	{
		FRDWSample S; Wild->Sample(X, Y, S, false); H = S.H;
		return S.WaterKind == 0 && S.Field < 0.1f && S.FarmKind == 0 && S.Canopy < 0.08f && S.Rock < 0.3f && S.Road < 0.1f && S.Lava < 0.01f;
	};
	// (the wilds' places, structures and scenery round a point, within about 800 m: a route keeps 70 m from each (the third
	// rehearsal's turns ran the horse into a ruin's walls, which the ground's samples do not hold))
	TArray<FVector2D> Near;
	auto Gather = [this, &Near](double X, double Y)
	{
		Near.Reset(); TArray<FRDWildPlace> Ps;
		const FIntPoint Pc = Wild->PlaceCellOf(X, Y), Sc = Wild->SiteCellOf(X, Y), Nc = Wild->SceneryCellOf(X, Y);
		for (int32 Dx = -1; Dx <= 1; ++Dx) for (int32 Dy = -1; Dy <= 1; ++Dy) { Wild->PlacesIn(Pc + FIntPoint(Dx, Dy), Ps); Wild->SitesIn(Sc + FIntPoint(Dx, Dy), Ps); }
		for (int32 Dx = -3; Dx <= 3; ++Dx) for (int32 Dy = -3; Dy <= 3; ++Dy) Wild->SceneryIn(Nc + FIntPoint(Dx, Dy), Ps);
		for (const FRDWildPlace& P : Ps) if (FVector2D::Distance(P.At, FVector2D(X, Y)) < 900.0) Near.Add(P.At);
	};
	auto Free = [&Near](double X, double Y) { for (const FVector2D& P : Near) if (FVector2D::Distance(P, FVector2D(X, Y)) < 70.0) return false; return true; };
	bool bPlains = false;
	for (double R = 2500.0; R <= 9000.0 && !bPlains; R += 500.0)
		for (int32 A = 0; A < 24 && !bPlains; ++A)
		{
			const double An = A * PI / 12.0, X = R * FMath::Cos(An), Y = R * FMath::Sin(An);
			float H0 = 0.f;
			if (!Clear(X, Y) || !Open(X, Y, H0)) continue;
			Gather(X, Y);
			if (!Free(X, Y)) continue;
			for (int32 W = 0; W < 8 && !bPlains; ++W)
			{
				const double Wa = W * PI / 4.0; bool bOk = true;
				for (int32 K = 1; K <= 12 && bOk; ++K)
				{
					float H = 0.f;
					const double Px = X + FMath::Cos(Wa) * K * 42.0, Py = Y + FMath::Sin(Wa) * K * 42.0;
					bOk = Open(Px, Py, H) && FMath::Abs(H - H0) < 6.f && Clear(Px, Py) && Free(Px, Py)
						&& Free(Px - FMath::Sin(Wa) * 60.0, Py + FMath::Cos(Wa) * 60.0) && Free(Px + FMath::Sin(Wa) * 60.0, Py - FMath::Cos(Wa) * 60.0);
					// (and room to each side for the turns: 80 m)
					float Hs = 0.f;
					if (bOk && (K % 4) == 0) bOk = Open(Px - FMath::Sin(Wa) * 80.0, Py + FMath::Cos(Wa) * 80.0, Hs) && Open(Px + FMath::Sin(Wa) * 80.0, Py - FMath::Cos(Wa) * 80.0, Hs);
				}
				if (bOk) { Reel16Plains = FVector2D(X, Y); Reel16Yaw = FMath::RadiansToDegrees(Wa); bPlains = true; }
			}
		}
	if (!bPlains) { Reel15Mark(TEXT("note|no plains found")); return false; }
	bool bLake = false;
	for (double R = 400.0; R <= 25000.0 && !bLake; R += 300.0)
	{
		const int32 N = FMath::Max(8, (int32)(2.0 * PI * R / 300.0));
		for (int32 A = 0; A < N && !bLake; ++A)
		{
			const double An = 2.0 * PI * A / N, X = R * FMath::Cos(An), Y = R * FMath::Sin(An);
			FRDWSample S; Wild->Sample(X, Y, S, false);
			if (!(S.WaterKind >= 2 && S.WaterKind <= 4 && S.Water - S.H >= 2.f) || !Clear(X, Y)) continue;
			double Best = 1e9; FVector2D Shore, Out;
			for (int32 Ray = 0; Ray < 16; ++Ray)
			{
				const double Ra = Ray * PI / 8.0;
				for (double D = 20.0; D < 1500.0; D += 15.0)
				{
					FRDWSample Q; Wild->Sample(X + FMath::Cos(Ra) * D, Y + FMath::Sin(Ra) * D, Q, false);
					if (Q.WaterKind != 0) continue;
					if (D < Best)
					{
						float H = 0.f;
						const FVector2D P(X + FMath::Cos(Ra) * (D + 30.0), Y + FMath::Sin(Ra) * (D + 30.0));
						if (Open(P.X, P.Y, H)) { Best = D; Shore = P; Out = FVector2D(-FMath::Cos(Ra), -FMath::Sin(Ra)); }
					}
					break;
				}
			}
			if (Best < 400.0) { Reel16Shore = Shore; Reel16Water = FVector2D(X, Y); Reel16SwimYaw = FMath::RadiansToDegrees(FMath::Atan2(Out.Y, Out.X)); bLake = true; }
		}
	}
	Reel15Mark(FString::Printf(TEXT("note|plains (%.0f, %.0f) m way %.0f; lake %s"), Reel16Plains.X, Reel16Plains.Y, Reel16Yaw,
		bLake ? *FString::Printf(TEXT("(%.0f, %.0f) m, the shore (%.0f, %.0f)"), Reel16Water.X, Reel16Water.Y, Reel16Shore.X, Reel16Shore.Y) : TEXT("none")));
	bReel16Lake = bLake;
	return true;
}

void ARDDungeonGenerator::TickReel16(float RealDt)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return;
	if (!bReel16Read)
	{
		bReel16Read = true;
		if (FParse::Param(FCommandLine::Get(), TEXT("RDReel16")))
		{
			FString Go, Done, Ready;
			FParse::Value(FCommandLine::Get(), TEXT("RDShowGo="), Go); FParse::Value(FCommandLine::Get(), TEXT("RDShowDone="), Done); FParse::Value(FCommandLine::Get(), TEXT("RDShowReady="), Ready);
			StartReel16(Go, Done, false); GI->ReelReady = Ready;
		}
	}
	if (!bReel16) return;
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	ACharacter* Her = PC ? Cast<ACharacter>(PC->GetPawn()) : nullptr;
	if (!PC || !Her || !PlayerCombat) return;
	const float Dt = FMath::Min(RealDt, 0.1f);
	Reel16T += Dt;
	if (bWild && GetWorld()) WildLastEngaged = GetWorld()->GetTimeSeconds();          // (the encounter director sends nothing)
	// ---- the setup: her horse hers, the monsters quiet, the spots found; ready, then the go
	if (Reel16Stage < 0)
	{
		// (Brokenspire stood round her before she is put on the plains; out there the town is let go (the first rehearsal waited for
		// it for ten minutes): only the wilds then)
		const ARDSection* S0 = GetSection(FIntPoint::ZeroValue);
		const bool bReady = Reel16Sub == 0 ? (bTown && bWild && IsWildReady() && S0 && !S0->IsBuilding() && bTownPlaced) : (bWild && IsWildReady());
		if (!bReady) { Reel16T = 0.f; return; }
		if (Reel16Sub == 0)
		{
			if (Reel16T < 2.f) return;
			GI->bHorseOwned = true; GI->bTamedOnly = false; GI->bRideTamed = false;
			Reel16Aggro = AggroDistance; Reel16Lose = LoseDistance; AggroDistance = 0.f; LoseDistance = 1.f;
			GI->ReelT0 = FPlatformTime::Seconds();
			if (!Reel16FindSpots()) { bReel16 = false; return; }
			WildPutHer(Reel16Plains.X, Reel16Plains.Y);
			Reel16Sub = 1; Reel16T = 0.f; return;
		}
		if (Reel16Sub == 1)
		{
			// (the plains round her made, her horse come to her; then she stands at its left, facing along the way)
			if (Reel16T < 6.f || !Horse) return;
			if (bMounted) DismountHorse(true);
			const FRotator Way(0.f, Reel16Yaw, 0.f);
			const float Hh = Her->GetSimpleCollisionHalfHeight();
			const FVector Feet = Her->GetActorLocation() - FVector(0, 0, Hh);
			Horse->SetActorLocationAndRotation(Feet + Way.Vector() * 150.f, Way);
			Horse->PlayFor(0.f);
			Her->SetActorLocationAndRotation(Feet + Way.Vector() * 150.f - Way.RotateVector(FVector(0, 120.f, 0)) + FVector(0, 0, Hh + 5.f), FRotator(0.f, Reel16Yaw + 70.f, 0.f), false, nullptr, ETeleportType::TeleportPhysics);
			PC->SetControlRotation(FRotator(-10.f, Reel16Yaw - 120.f, 0.f));
			Reel16Sub = 2; Reel16T = 0.f; return;
		}
		if (Reel16T < 2.f) return;
		if (!GI->ReelReady.IsEmpty() && !FPaths::FileExists(GI->ReelReady)) FFileHelper::SaveStringToFile(TEXT("ready"), *GI->ReelReady);
		if (!GI->ReelGo.IsEmpty() && !FPaths::FileExists(GI->ReelGo)) return;
		GI->ReelT0 = FPlatformTime::Seconds(); GI->ReelLog.Reset();
		Reel15Mark(TEXT("note|go"));
		bReel16Going = true; Reel16Stage = 0; Reel16Sub = 0; Reel16T = 0.f;
	}
	// ---- the scenes
	if (Reel16Stage >= RD16Num)
	{
		Reel15End();
		bReel16 = false;
		AggroDistance = Reel16Aggro; LoseDistance = Reel16Lose;
		PlayerCombat->SetRunMode(false);
		Reel15Mark(TEXT("note|done"));
		if (!GI->ReelDone.IsEmpty()) FFileHelper::SaveStringToFile(FString::Join(GI->ReelLog, TEXT("\n")), *GI->ReelDone, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
		UE_LOG(LogRDReel16, Log, TEXT("RDREEL16 done"));
		return;
	}
	const FRD16Scene& Sc = RD16Scenes[Reel16Stage];
	const FName Name(Sc.Name);
	// (the camera eased to a yaw off the horse's heading)
	auto Cam = [&](float Off, float Pitch, float Speed)
	{
		const float Hy = bMounted ? Ride15.Yaw : Horse ? Horse->GetActorRotation().Yaw : Her->GetActorRotation().Yaw;
		const FRotator R = FMath::RInterpTo(PC->GetControlRotation(), FRotator(Pitch, Hy + Off, 0.f), Dt, Speed);
		PC->SetControlRotation(FRotator(R.Pitch, R.Yaw, 0.f));
	};
	auto Drive = [&](float YawWorld, float Scale, bool bRun)
	{
		PlayerCombat->SetRunMode(bRun);
		if (Scale > 0.f) Her->AddMovementInput(FRotator(0.f, YawWorld, 0.f).Vector(), Scale);
	};
	auto Next = [&]() { Reel15End(); ++Reel16Stage; Reel16Sub = 0; Reel16T = 0.f; };
	// (a scene's start: some need a place first, outside the cut (the lake))
	if (Reel16Sub == 0)
	{
		if (Name == TEXT("swim"))
		{
			if (!bReel16Lake) { Reel15Mark(TEXT("note|no lake: the swim left out")); ++Reel16Stage; Reel16T = 0.f; return; }
			if (Reel16T < 0.05f) { WildPutHer(Reel16Shore.X, Reel16Shore.Y); return; }
			if (Reel16T < 5.f) return;
			if (bMounted) DismountHorse(true);
			if (Horse) { Horse->SetActorLocation(Her->GetActorLocation() - FVector(0, 0, Her->GetSimpleCollisionHalfHeight())); }
			MountHorse(); Ride15.Phase = ERide15::Riding; Ride15.T = 0.f; Ride15.Yaw = Reel16SwimYaw; Her->SetActorRotation(FRotator(0.f, Reel16SwimYaw, 0.f));
			PC->SetControlRotation(FRotator(-10.f, Reel16SwimYaw + 75.f, 0.f));
			if (Reel16T < 7.5f) return;
		}
		Reel15Scene(Sc.Name, Sc.Title, Sc.Line, FString());
		Reel16Swam = 0.f; Reel16Dry = 0.f; Reel16Back = false;
		if (bReel16Shots) { UKismetSystemLibrary::ExecuteConsoleCommand(this, TEXT("HighResShot 1280x720"), PC); }
		Reel16Sub = 1; Reel16T = 0.f;
		if (Name == TEXT("mount")) MountHorse();
		Reel16Base = bMounted ? Ride15.Yaw : Reel16Yaw;
	}
	const float T = Reel16T;
	if (bReel16Shots && T >= 3.f && T - Dt < 3.f) UKismetSystemLibrary::ExecuteConsoleCommand(this, TEXT("HighResShot 1280x720"), PC);          // (a rehearsal: a second picture 3 s in)
	if (Name == TEXT("mount")) { Cam(-115.f, -10.f, 1.2f); }
	else if (Name == TEXT("walk")) { Cam(FMath::Lerp(-110.f, -35.f, FMath::Clamp(T / Sc.Secs, 0.f, 1.f)), -9.f, 1.5f); Drive(Reel16Base, 0.33f, false); }
	else if (Name == TEXT("gallop")) { Cam(T < 4.f ? -30.f : -78.f, -8.f, T < 4.f ? 2.f : 0.9f); Drive(Reel16Base, 1.f, true); }
	else if (Name == TEXT("turns")) { Cam(-60.f, -12.f, 2.f); Drive(Reel16Base + 75.f * FMath::Sin(T * 0.9f), 1.f, true); }
	else if (Name == TEXT("stop")) { Cam(-80.f, -8.f, 2.f); Drive(0.f, 0.f, true); }
	else if (Name == TEXT("back"))
	{
		Cam(0.f, -12.f, 4.f);
		if (T > 0.6f) Drive((bMounted ? Ride15.Yaw : Reel16Base) + 180.f, 0.5f, false);
	}
	else if (Name == TEXT("jump"))
	{
		Cam(-70.f, -6.f, 2.f); Drive(bMounted ? Ride15.Yaw : Reel16Base, 1.f, true);
		if (T > 2.6f && Reel16Sub == 1) { Her->Jump(); Reel16Sub = 2; }
		if (Reel16Sub == 2 && T > 2.9f) Her->StopJumping();
	}
	else if (Name == TEXT("rear"))
	{
		Cam(-125.f, -4.f, 2.f);
		if (T > 0.9f && Reel16Sub == 1 && FMath::Abs(Ride15.Speed) < 100.f) { RearHorse(); Reel16Sub = 2; }
		if (Reel16Sub == 2 && !Ride15.bRear) { Reel16Sub = 3; Reel16Dry = 0.f; }
		if (Reel16Sub == 3) { Reel16Dry += Dt; if (Reel16Dry > 0.8f) { Next(); return; } }
	}
	else if (Name == TEXT("swim"))
	{
		Cam(70.f, -10.f, 1.5f);
		// (into the water, a turn in it, and back out to the shore: the scene ends once it has stood on dry ground 1.5 s (the first
		// rehearsal's ended in the water, and she got down there))
		// (out until it has swum 4 s (14 s at most: the fourth rehearsal's lake lay further than 5 s from its shore, and the scene turned
		// back on the grass), then back)
		if (Ride15.bSwim) Reel16Swam += Dt;
		if (!Reel16Back && (Reel16Swam > 4.f || T > 14.f)) Reel16Back = true;
		const float Yw = Reel16Back ? Reel16SwimYaw + 180.f : Reel16SwimYaw;
		float Fz = 0.f;
		const bool bWet = Ride15.bSwim || Ride15.Lift > 5.f || (WaterFaceAt(Her->GetActorLocation(), Fz) && Her->GetActorLocation().Z - Her->GetSimpleCollisionHalfHeight() < Fz + 10.f);
		if (Reel16Back && !bWet) { Reel16Dry += Dt; } else Reel16Dry = 0.f;
		Drive(Yw, Reel16Dry > 0.6f ? 0.f : 1.f, Reel16Dry <= 0.f);
		if (Reel16Dry > 1.5f) { Next(); return; }
	}
	else if (Name == TEXT("dismount"))
	{
		Cam(-120.f, -10.f, 1.5f);
		if (Reel16Sub == 1 && T > 0.4f && FMath::Abs(Ride15.Speed) < 40.f) { DismountHorse(); Reel16Sub = 2; }
		if (Reel16Sub == 2 && !bMounted) { Reel16Sub = 3; Reel16Dry = 0.f; }
		if (Reel16Sub == 3) { Reel16Dry += Dt; if (Reel16Dry > 1.2f) { Next(); return; } }
	}
	if (T >= Sc.Secs) Next();
}
