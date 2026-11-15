// The packaged game out in the wilds (the TODO sweep of 2026-11-14: "a walk out of the gate, a journey, a save and load, and its
// memory over a long walk have not been run in it"): -RDWildTest=<file> [-RDWildTestMinutes=<n>]. The game plays itself from
// Brokenspire's square and writes each stage as it ends ("stage|<name>|ok/FAILED|<measured>"), the memory every 30 s of the
// walk ("mem|<seconds>|<MB used>|<km from the start>|<chunks>|<fps>|walked <km>"; the walk starts 3 km out of the town, on dry
// ground, and must walk 1 km), the last line "result|ok" or "result|FAILED". The load opens the
// level again: the stages done are read back from the file, and the one waiting for the load ("pending|load|<x>|<y>") checked.
// Only with the switch: nothing else changes.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDCombat.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "HAL/PlatformMemory.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Engine/World.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDWildSelfTest, Log, All);

namespace
{
	double RDWSTMemMB() { return FPlatformMemory::GetStats().UsedPhysical / (1024.0 * 1024.0); }
}

void ARDDungeonGenerator::WildSelfTestLine(const FString& Line)
{
	FFileHelper::SaveStringToFile(Line + TEXT("\n"), *WildTest.File, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM, &IFileManager::Get(), FILEWRITE_Append);
	UE_LOG(LogRDWildSelfTest, Log, TEXT("RDWILDTEST %s"), *Line);
}

void ARDDungeonGenerator::TickWildSelfTest(APawn* P)
{
	if (!WildTest.bRead)
	{
		WildTest.bRead = true;
		WildTest.bOn = FParse::Value(FCommandLine::Get(), TEXT("RDWildTest="), WildTest.File) && !WildTest.File.IsEmpty();
		if (!WildTest.bOn) return;
		FParse::Value(FCommandLine::Get(), TEXT("RDWildTestMinutes="), WildTest.WalkMinutes);
		// (what was done before a load opened the level again)
		TArray<FString> Lines;
		FFileHelper::LoadFileToStringArray(Lines, *WildTest.File);
		for (const FString& L : Lines)
		{
			if (L.StartsWith(TEXT("stage|"))) ++WildTest.Stage;
			if (L.StartsWith(TEXT("pending|load|")))
			{
				TArray<FString> Pp; L.ParseIntoArray(Pp, TEXT("|"));
				if (Pp.Num() >= 4) { WildTest.SavedAt = FVector(FCString::Atod(*Pp[2]), FCString::Atod(*Pp[3]), 0.0); WildTest.bLoadPending = true; }
			}
			if (L.StartsWith(TEXT("stage|")) && L.Contains(TEXT("|FAILED|"))) WildTest.bFailed = true;
			if (L.StartsWith(TEXT("result|"))) WildTest.Stage = 99;
		}
		if (WildTest.bLoadPending && WildTest.Stage != 3) WildTest.bLoadPending = false;
		if (Lines.Num() == 0) WildSelfTestLine(FString::Printf(TEXT("begin|%.0f MB"), RDWSTMemMB()));
		WildTest.T0 = GetWorld()->GetTimeSeconds();
	}
	if (!WildTest.bOn || WildTest.Stage >= 99 || !P) return;
	const float Now = GetWorld()->GetTimeSeconds();
	const FVector L = P->GetActorLocation();
	auto Pass = [&](const TCHAR* Name, bool bOk, const FString& What)
	{
		WildSelfTestLine(FString::Printf(TEXT("stage|%s|%s|%s"), Name, bOk ? TEXT("ok") : TEXT("FAILED"), *What));
		if (!bOk) WildTest.bFailed = true;
		++WildTest.Stage; WildTest.T0 = Now; WildTest.Sub = 0;
	};
	auto Town = [this]() { TArray<FString> S; GetWildTownState().ParseIntoArray(S, TEXT("|"), false); return S; };
	auto Walk = [&](const FVector& To)
	{
		FVector D = (To - L) * FVector(1, 1, 0);
		if (D.Normalize()) P->AddMovementInput(D, 1.f);
	};
	switch (WildTest.Stage)
	{
	case 0:
	{
		// (the town built round her in its square)
		const TArray<FString> S = Town();
		if (S.Num() > 3 && S[2] == TEXT("0") && S[3] == TEXT("1") && IsInTownWalls(L) && Now - WildTest.T0 > 8.f)
			Pass(TEXT("town"), true, FString::Printf(TEXT("%s, in its walls, %.0f MB"), *S[1], RDWSTMemMB()));
		else if (Now - WildTest.T0 > 240.f) Pass(TEXT("town"), false, TEXT("no town built round her in 240 s"));
		break;
	}
	case 1:
	{
		// (walked out of the gate: to the gate, then 120 m on along the way out)
		FVector Gate, Sq;
		if (!GetTownPlace(TEXT("gate"), Gate) || !GetTownPlace(TEXT("square"), Sq)) { Pass(TEXT("gate"), false, TEXT("no gate or square")); break; }
		FVector Out = (Gate - Sq) * FVector(1, 1, 0); Out.Normalize();
		const FVector Beyond = Gate + Out * 12000.f;
		if (WildTest.Sub == 0) { if (FVector::Dist2D(L, Gate) < 300.f) WildTest.Sub = 1; else Walk(Gate); }
		else Walk(Beyond);
		// (stuck: put a little way along, as a player would step round)
		if (Now - WildTest.LastMoveAt > 4.f) { WildTest.LastMoveAt = Now; if (FVector::Dist2D(L, WildTest.LastAt) < 100.f) P->SetActorLocation(L + FVector(0, 0, 60.f) + (WildTest.Sub ? Out : (Gate - L).GetSafeNormal2D()) * 200.f); WildTest.LastAt = L; }
		if (WildTest.Sub == 1 && !IsInTownWalls(L) && FVector::Dist2D(L, Gate) > 6000.f)
			Pass(TEXT("gate"), true, FString::Printf(TEXT("out of the walls %.0f m past the gate after %.0f s, %.0f MB"), FVector::Dist2D(L, Gate) / 100.f, Now - WildTest.T0, RDWSTMemMB()));
		else if (Now - WildTest.T0 > 180.f) Pass(TEXT("gate"), false, FString::Printf(TEXT("still %s %.0f m from the gate"), IsInTownWalls(L) ? TEXT("inside,") : TEXT("outside,"), FVector::Dist2D(L, Gate) / 100.f));
		break;
	}
	case 2:
	{
		// (a journey: rd.GoTo's way to Vel Morrath, the town built round her)
		if (WildTest.Sub == 0) { WildTest.Sub = 1; WildTest.bJourney = ConsoleGoTo(TEXT("Vel Morrath")); }
		const TArray<FString> S = Town();
		if (S.Num() > 3 && S[1] == TEXT("Vel Morrath") && S[2] == TEXT("0") && S[3] == TEXT("1") && Now - WildTest.T0 > 5.f)
			Pass(TEXT("journey"), true, FString::Printf(TEXT("Vel Morrath built round her after %.0f s, %.0f MB"), Now - WildTest.T0, RDWSTMemMB()));
		else if (Now - WildTest.T0 > 200.f) Pass(TEXT("journey"), false, FString::Printf(TEXT("asked %d, the town %s"), WildTest.bJourney ? 1 : 0, S.Num() > 1 ? *S[1] : TEXT("?")));
		break;
	}
	case 3:
	{
		// (saved where she stands, moved 300 m off, loaded: back where she saved)
		if (WildTest.bLoadPending)
		{
			if (LoadsArrived < 1 && Now - WildTest.T0 < 200.f) break;
			if (Now - WildTest.T0 < 4.f) break;
			const float Off = FVector::Dist2D(L, WildTest.SavedAt) / 100.f;
			WildTest.bLoadPending = false;
			Pass(TEXT("load"), LoadsArrived >= 1 && Off < 10.f, FString::Printf(TEXT("the level opened again, she is %.1f m from where she saved, %.0f MB"), Off, RDWSTMemMB()));
			break;
		}
		if (Now - WildTest.T0 < 3.f) break;
		const bool bSaved = SaveGameNow(TEXT("save_rdwildtest"), TEXT("test"), TEXT("Wild Test"));
		WildSelfTestLine(FString::Printf(TEXT("pending|load|%.0f|%.0f|saved %d"), L.X, L.Y, bSaved ? 1 : 0));
		WildPutHer(L.X / 100.f + 300.f, L.Y / 100.f);
		if (!bSaved || !LoadGameFrom(TEXT("save_rdwildtest"))) Pass(TEXT("load"), false, TEXT("not saved or not loaded"));
		WildTest.Stage = 100;          // (waiting for the level to open again: the next generator reads the file)
		break;
	}
	case 4:
	{
		// (the long walk across the wilds, turned when held up; memory every 30 s. The first run walked from inside Vel Morrath and
		// stayed boxed in its streets: 0.16 km in 20 min, 181 turns. She is put down on dry ground 3 km out of the town first (the
		// map's teleport: the town let go behind her), and stepped 200 m on along her way when 15 s of turning got her nowhere)
		auto PutAhead = [&](const FVector& From, float Cm)
		{
			const int32 K = MapXKind; MapXKind = 1;
			const bool bOk = MapTeleportTo(From + WildTest.Heading * Cm);
			MapXKind = K;
			return bOk;
		};
		if (WildTest.Sub == 0)
		{
			WildTest.Heading = FVector(0.6f, -0.8f, 0.f);
			FVector From = L;
			if (bWild && Wild && WildTownIdx >= 0 && Wild->Towns.IsValidIndex(WildTownIdx))
				From = FVector(Wild->Towns[WildTownIdx].Site.X * 100.0, Wild->Towns[WildTownIdx].Site.Y * 100.0, L.Z);
			const bool bOut = PutAhead(From, 300000.f);
			WildSelfTestLine(FString::Printf(TEXT("note|walk|put 3 km out of the town %d"), bOut ? 1 : 0));
			WildTest.Sub = 1; WildTest.T0 = Now;
			break;
		}
		if (WildTest.Sub == 1)
		{
			if (Now - WildTest.T0 < 3.f) break;
			WildTest.Sub = 2; WildTest.T0 = Now; WildTest.WalkFrom = L; WildTest.MemAt = Now - 30.f; WildTest.Mem0 = RDWSTMemMB(); WildTest.LastAt = L; WildTest.LastMoveAt = Now;
			WildTest.PathCm = 0.0; WildTest.Stuck = 0; WildTest.Puts = 0;
		}
		if (WildTest.Sub == 3) { WildTest.Sub = 2; WildTest.LastAt = L; WildTest.LastMoveAt = Now; }
		{
			const bool bDead = PlayerCombat && PlayerCombat->IsDead();
			if (bDead && !WildTest.bWasDead) ++WildTest.Deaths;
			if (!bDead && WildTest.bWasDead) { WildTest.LastAt = L; WildTest.LastMoveAt = Now; }      // (back in a town: not walked)
			WildTest.bWasDead = bDead;
			if (bDead) break;
		}
		P->AddMovementInput(WildTest.Heading, 1.f);
		++WildTest.Frames;
		if (Now - WildTest.LastMoveAt > 5.f)
		{
			const float Moved = FVector::Dist2D(L, WildTest.LastAt);
			if (Moved < 300.f)
			{
				WildTest.Heading = WildTest.Heading.RotateAngleAxis(75.f, FVector::UpVector); ++WildTest.Turns;
				// (where she was put is read at the next tick: Sub 3 takes it as the next check's start, not walked ground)
				if (++WildTest.Stuck >= 3 && PutAhead(L, 20000.f)) { ++WildTest.Puts; WildTest.Stuck = 0; WildTest.Sub = 3; WildTest.LastMoveAt = Now; break; }
			}
			else { WildTest.Stuck = 0; WildTest.PathCm += Moved; }
			WildTest.LastAt = L; WildTest.LastMoveAt = Now;
		}
		if (Now - WildTest.MemAt >= 30.f)
		{
			// (the frames a second over the last 30 s of real time, the game's ticks counted (the frame rate the TODO asks of the
			// packaged game out there))
			const double Rn = FPlatformTime::Seconds(); const double Fps = WildTest.FramesAt > 0.0 ? WildTest.Frames / FMath::Max(Rn - WildTest.FramesAt, 0.001) : 0.0;
			WildTest.Frames = 0; WildTest.FramesAt = Rn;
			WildTest.MemAt = Now; const double M = RDWSTMemMB(); WildTest.MemMax = FMath::Max(WildTest.MemMax, M);
			WildSelfTestLine(FString::Printf(TEXT("mem|%.0f|%.0f|%.2f|%d|%.1f fps|walked %.2f km"), Now - WildTest.T0, M, FVector::Dist2D(L, WildTest.WalkFrom) / 100000.f, WildChunks.Num(), Fps, WildTest.PathCm / 100000.0));
		}
		if (Now - WildTest.T0 >= WildTest.WalkMinutes * 60.f)
		{
			// (a walk: at least 1 km walked (not put) over the minutes, and the memory grown by less than 1.5 GB)
			const double M1 = RDWSTMemMB();
			Pass(TEXT("walk"), M1 - WildTest.Mem0 < 1500.0 && WildTest.PathCm >= 100000.0,
				FString::Printf(TEXT("%.1f min, %.2f km walked, %.2f km from its start, memory %.0f -> %.0f MB (most %.0f), %d turns, %d steps on, %d deaths"),
				(Now - WildTest.T0) / 60.f, WildTest.PathCm / 100000.0, FVector::Dist2D(L, WildTest.WalkFrom) / 100000.f, WildTest.Mem0, M1, WildTest.MemMax, WildTest.Turns, WildTest.Puts, WildTest.Deaths));
		}
		break;
	}
	default:
		if (WildTest.Stage == 5) { WildSelfTestLine(WildTest.bFailed ? TEXT("result|FAILED") : TEXT("result|ok")); WildTest.Stage = 99; }
		break;
	}
}
