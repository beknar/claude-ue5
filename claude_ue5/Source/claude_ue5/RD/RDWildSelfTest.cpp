// The packaged game out in the wilds (the TODO sweep of 2026-11-14: "a walk out of the gate, a journey, a save and load, and its
// memory over a long walk have not been run in it"): -RDWildTest=<file> [-RDWildTestMinutes=<n>]. The game plays itself from
// Brokenspire's square and writes each stage as it ends ("stage|<name>|ok/FAILED|<measured>"), the memory every 30 s of the
// walk ("mem|<seconds>|<MB in use>|<km from the start>|<chunks>|<fps>|walked <km>|commit <MB>"; the walk starts 3 km out of the
// town, on dry ground, and must walk 1 km), the last line "result|ok" or "result|FAILED". The load opens the level again: the
// stages done are read back from the file (one "stage|" line each), and the one waiting for the load ("pending|load|<x>|<y>")
// checked. Only with the switch: nothing else changes.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDCombat.h"
#include "RD/RDSection.h"
#include "RD/RDMonster.h"
#include "RD/RDWild.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "HAL/PlatformMemory.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Engine/World.h"
#include "Engine/Engine.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDWildSelfTest, Log, All);

namespace
{
	// (PR #64's review: the working set alone can be trimmed by Windows while the commit keeps rising: both are read and both
	// are held to the walk's limit)
	double RDWSTMemMB() { return FPlatformMemory::GetStats().UsedPhysical / (1024.0 * 1024.0); }
	double RDWSTCommitMB() { return FPlatformMemory::GetStats().UsedVirtual / (1024.0 * 1024.0); }
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
	// (PR #64's review: the town's state is a string formatted and split; the stages that wait on it read it twice a second)
	auto Due = [&]() { if (Now < WildTest.NextCheckAt) return false; WildTest.NextCheckAt = Now + 0.5f; return true; };
	switch (WildTest.Stage)
	{
	case 0:
	{
		// (the town built round her in its square)
		if (!Due()) break;
		const TArray<FString> S = Town();
		if (S.Num() > 3 && S[2] == TEXT("0") && S[3] == TEXT("1") && IsInTownWalls(L) && Now - WildTest.T0 > 8.f)
			Pass(TEXT("town"), true, FString::Printf(TEXT("%s, in its walls, %.0f MB"), *S[1], RDWSTMemMB()));
		else if (Now - WildTest.T0 > 240.f) Pass(TEXT("town"), false, TEXT("no town built round her in 240 s"));
		break;
	}
	case 1:
	{
		// (walked out of the gate: the portcullis raised by its lever as a player raises it (walked to the lever, F), to the gate,
		// then 120 m on along the way out. The gate, the square, the way out and the lever are found once. PR #64's rerun: with
		// the steps round swept she stood at the lowered portcullis 180 s; the unswept steps of the first runs had put her
		// through it, so those passes were not a walk through the gate)
		ARDSection* TS = GetSection(FIntPoint(0, 0));
		if (WildTest.Sub == 0)
		{
			FVector Sq;
			if (!GetTownPlace(TEXT("gate"), WildTest.Gate) || !GetTownPlace(TEXT("square"), Sq)) { Pass(TEXT("gate"), false, TEXT("no gate or square")); break; }
			WildTest.GateOut = ((WildTest.Gate - Sq) * FVector(1, 1, 0)).GetSafeNormal();
			WildTest.Pushes = 0; WildTest.LastAt = L; WildTest.LastMoveAt = Now; WildTest.SubAt = Now; WildTest.Sub = 1;
			// (the lever nearest the gate's inside, and her place before it on the town's side)
			const FVector Inside = WildTest.Gate - WildTest.GateOut * 350.f;
			float Best = 1e9f; WildTest.LeverAt = FVector::ZeroVector;
			if (TS) for (const FString& Ln : TS->GetTownImproveLines())
			{
				TArray<FString> Q; Ln.ParseIntoArray(Q, TEXT("|"));
				if (Q.Num() < 5 || Q[0] != TEXT("lever")) continue;
				const FVector Lv(FCString::Atod(*Q[2]), FCString::Atod(*Q[3]), FCString::Atod(*Q[4]));
				if (FVector::Dist2D(Lv, Inside) < Best) { Best = FVector::Dist2D(Lv, Inside); WildTest.LeverPos = Lv; WildTest.LeverAt = Lv - WildTest.GateOut * 110.f; }
			}
			WildTest.GateWhat = TS && TS->IsPortcullisUp() ? TEXT("the portcullis up already") : TEXT("");
		}
		const FVector Gate = WildTest.Gate, Out = WildTest.GateOut;
		if (WildTest.Sub == 1)
		{
			// (to the lever while the portcullis is down; F once there, then the raise waited for)
			if (TS && TS->IsPortcullisUp()) { WildTest.Sub = 3; WildTest.SubAt = Now; }
			else if (WildTest.LeverAt.IsZero()) { Pass(TEXT("gate"), false, TEXT("the portcullis down and no lever found")); break; }
			else if (FVector::Dist2D(L, WildTest.LeverAt) < (WildTest.GateOther.IsEmpty() ? 120.f : 40.f))
			{
				// (F takes the nearest thing: a townsperson or a dog by the lever took it ("bark", the rerun of PR #64's review).
				// As a player reads the prompt, F is pressed only when it names the lever; else she steps on toward the lever
				// and waits for whoever stands there to move)
				if (!Due()) break;
				const FString Prompt = DescribeNearest(L);
				if (Prompt.Contains(TEXT("lever")))
				{
					WildTest.GateWhat = FString::Printf(TEXT("walked to the lever in %.0f s%s, F: %s"), Now - WildTest.SubAt,
						WildTest.GateOther.IsEmpty() ? TEXT("") : *FString::Printf(TEXT(" (F named \"%s\" first: stepped nearer and waited)"), *WildTest.GateOther), *InteractNearest(L));
					WildTest.Sub = 2; WildTest.SubAt = Now;
				}
				else if (WildTest.GateOther.IsEmpty())
				{
					WildTest.GateOther = Prompt.IsEmpty() ? FString(TEXT("nothing")) : Prompt;
					WildTest.LeverAt = WildTest.LeverPos - WildTest.GateOut * 55.f;      // (a step nearer; then she waits there)
				}
			}
			else Walk(WildTest.LeverAt);
		}
		else if (WildTest.Sub == 2)
		{
			if (TS && TS->IsPortcullisUp() && Now - WildTest.SubAt > 3.f) { WildTest.GateWhat += FString::Printf(TEXT(", up after %.0f s"), Now - WildTest.SubAt); WildTest.Sub = 3; WildTest.SubAt = Now; }
			else if (Now - WildTest.SubAt > 15.f) { Pass(TEXT("gate"), false, FString::Printf(TEXT("%s; the portcullis not up 15 s after"), *WildTest.GateWhat)); break; }
		}
		else if (WildTest.Sub == 3) { if (FVector::Dist2D(L, Gate) < 300.f) WildTest.Sub = 4; else Walk(Gate); }
		else Walk(Gate + Out * 12000.f);
		// (stuck: stepped 2 m on, as a player would step round; PR #64's review: swept, so never through a wall or a house, and
		// counted in the stage's line)
		if (Now - WildTest.LastMoveAt > 4.f)
		{
			WildTest.LastMoveAt = Now;
			if (WildTest.Sub != 2 && FVector::Dist2D(L, WildTest.LastAt) < 100.f)
			{
				const FVector Way = WildTest.Sub == 4 ? Out : ((WildTest.Sub == 1 ? WildTest.LeverAt : Gate) - L).GetSafeNormal2D();
				P->SetActorLocation(L + FVector(0, 0, 60.f), true);
				P->SetActorLocation(P->GetActorLocation() + Way * 200.f, true);
				++WildTest.Pushes;
			}
			WildTest.LastAt = L;
		}
		// (out through the gate: she reached the gateway (within 3 m of the gate's spot), then went on out of the walls)
		if (WildTest.Sub == 4 && !IsInTownWalls(L) && FVector::Dist2D(L, Gate) > 6000.f)
			Pass(TEXT("gate"), true, FString::Printf(TEXT("%s; through the gateway and out of the walls, %.0f m past the gate after %.0f s, %d steps round (2 m, swept), %.0f MB"),
				*WildTest.GateWhat, FVector::Dist2D(L, Gate) / 100.f, Now - WildTest.T0, WildTest.Pushes, RDWSTMemMB()));
		else if (Now - WildTest.T0 > 240.f)
			Pass(TEXT("gate"), false, FString::Printf(TEXT("%s; still %s %.0f m from the gate, %s, the portcullis %s, %d steps round"), *WildTest.GateWhat, IsInTownWalls(L) ? TEXT("inside,") : TEXT("outside,"),
				FVector::Dist2D(L, Gate) / 100.f, WildTest.Sub == 4 ? TEXT("the gateway reached") : WildTest.Sub == 1 ? TEXT("the lever not reached") : TEXT("the gateway not reached"),
				TS && TS->IsPortcullisUp() ? TEXT("up") : TEXT("down"), WildTest.Pushes));
		break;
	}
	case 2:
	{
		// (a journey: rd.GoTo's way to Vel Morrath, the town built round her)
		if (WildTest.Sub == 0) { WildTest.Sub = 1; WildTest.bJourney = ConsoleGoTo(TEXT("Vel Morrath")); }
		if (!Due()) break;
		const TArray<FString> S = Town();
		if (S.Num() > 3 && S[1] == TEXT("Vel Morrath") && S[2] == TEXT("0") && S[3] == TEXT("1") && Now - WildTest.T0 > 5.f)
			Pass(TEXT("journey"), true, FString::Printf(TEXT("Vel Morrath built round her after %.0f s, %.0f MB"), Now - WildTest.T0, RDWSTMemMB()));
		else if (Now - WildTest.T0 > 200.f) Pass(TEXT("journey"), false, FString::Printf(TEXT("asked %d, the town %s"), WildTest.bJourney ? 1 : 0, S.Num() > 1 ? *S[1] : TEXT("?")));
		break;
	}
	case 3:
	{
		// (saved where she stands, moved 300 m off (and that measured before the load), loaded: back where she saved)
		if (WildTest.bLoadPending)
		{
			if (LoadsArrived < 1 && Now - WildTest.T0 < 200.f) break;
			if (Now - WildTest.T0 < 4.f) break;
			const float Off = FVector::Dist2D(L, WildTest.SavedAt) / 100.f;
			WildTest.bLoadPending = false;
			Pass(TEXT("load"), LoadsArrived >= 1 && Off < 10.f, FString::Printf(TEXT("the level opened again, she is %.1f m from where she saved, %.0f MB"), Off, RDWSTMemMB()));
			break;
		}
		if (WildTest.Sub == 0)
		{
			if (Now - WildTest.T0 < 3.f) break;
			if (!SaveGameNow(TEXT("save_rdwildtest"), TEXT("test"), TEXT("Wild Test"))) { Pass(TEXT("load"), false, TEXT("not saved")); break; }
			WildTest.SavedAt = L;
			WildPutDownNear(FVector2D(L.X / 100.0 + 300.0, L.Y / 100.0));
			WildTest.Sub = 1; WildTest.LastMoveAt = Now;
			break;
		}
		// (the move read a moment after it, then the load asked; PR #64's review: a refused load is a failed stage and the test
		// goes on, not a wait for a level that never opens)
		if (Now - WildTest.LastMoveAt < 2.f) break;
		const float Moved = FVector::Dist2D(L, WildTest.SavedAt) / 100.f;
		if (Moved < 50.f) { Pass(TEXT("load"), false, FString::Printf(TEXT("not moved off before the load (%.0f m)"), Moved)); break; }
		WildSelfTestLine(FString::Printf(TEXT("pending|load|%.0f|%.0f|saved 1, moved %.0f m off"), WildTest.SavedAt.X, WildTest.SavedAt.Y, Moved));
		if (!LoadGameFrom(TEXT("save_rdwildtest"))) { Pass(TEXT("load"), false, TEXT("the load refused")); break; }
		WildTest.Stage = 100;          // (waiting for the level to open again: the next generator reads the file)
		break;
	}
	case 4:
	{
		// (the long walk across the wilds, turned when held up; memory every 30 s. The first run walked from inside Vel Morrath and
		// stayed boxed in its streets: 0.16 km in 20 min, 181 turns. She is put down on dry ground 3 km out of the town first, and
		// stepped 200 m on along her way when 15 s of turning got her nowhere: by WildPutDownNear, never a town's own travel)
		auto PutAhead = [&](const FVector& From, float Cm) { const FVector T = From + WildTest.Heading * Cm; return WildPutDownNear(FVector2D(T.X / 100.0, T.Y / 100.0)); };
		if (WildTest.Sub == 0)
		{
			FVector From = L;
			if (bWild && Wild && WildTownIdx >= 0 && Wild->Towns.IsValidIndex(WildTownIdx))
				From = FVector(Wild->Towns[WildTownIdx].Site.X * 100.0, Wild->Towns[WildTownIdx].Site.Y * 100.0, L.Z);
			// (PR #64's review: 3 km out along one way can be sea or a mountain's face: eight ways are tried, and none is a failure now)
			bool bOut = false;
			int32 Tries = 0;
			for (; Tries < 8 && !bOut; ++Tries)
			{
				WildTest.Heading = FVector(0.6f, -0.8f, 0.f).RotateAngleAxis(45.f * Tries, FVector::UpVector);
				bOut = PutAhead(From, 300000.f);
			}
			if (!bOut) { Pass(TEXT("walk"), false, TEXT("no dry ground 3 km out of the town on eight ways")); break; }
			WildSelfTestLine(FString::Printf(TEXT("note|walk|put 3 km out of the town on the %d. way tried"), Tries));
			WildTest.Sub = 1; WildTest.T0 = Now;
			break;
		}
		if (WildTest.Sub == 1)
		{
			// (PR #64's review: the town let go is still held until the garbage is collected: taken as the start it hid 800 MB
			// of growth. Collected, then read 10 s on)
			if (!WildTest.bCollected && Now - WildTest.T0 >= 3.f)
			{
				WildTest.bCollected = true;
				WildSelfTestLine(FString::Printf(TEXT("note|walk|before the garbage collected %.0f MB, commit %.0f MB"), RDWSTMemMB(), RDWSTCommitMB()));
				if (GEngine) GEngine->ForceGarbageCollection(true);
			}
			if (Now - WildTest.T0 < 13.f) break;
			WildTest.Sub = 2; WildTest.T0 = Now; WildTest.WalkFrom = L; WildTest.MemAt = Now - 30.f; WildTest.Mem0 = RDWSTMemMB(); WildTest.Commit0 = RDWSTCommitMB();
			WildTest.LastAt = L; WildTest.LastMoveAt = Now; WildTest.PathCm = 0.0; WildTest.Stuck = 0; WildTest.Puts = 0;
		}
		if (WildTest.Sub == 3) { WildTest.Sub = 2; WildTest.LastAt = L; WildTest.LastMoveAt = Now; }
		{
			const bool bDead = PlayerCombat && PlayerCombat->IsDead();
			if (PlayerCombat)
			{
				const FString& Ms = PlayerCombat->Message;
				if (!Ms.IsEmpty() && (WildTest.Said.Num() == 0 || WildTest.Said.Last() != Ms)) { WildTest.Said.Add(Ms); if (WildTest.Said.Num() > 4) WildTest.Said.RemoveAt(0); }
				const float Hp = PlayerCombat->GetHealth();
				if (WildTest.LastHp >= 0.f && Hp < WildTest.LastHp - 0.5f)
				{
					WildTest.HurtTotal += WildTest.LastHp - Hp;
					WildTest.Hurts += FString::Printf(TEXT("%.0f s -%.0f; "), Now - WildTest.T0, WildTest.LastHp - Hp);
					if (WildTest.Hurts.Len() > 400) WildTest.Hurts.RightChopInline(WildTest.Hurts.Len() - 400);
				}
				WildTest.LastHp = Hp;
				if (!bDead && Hp > 0.f && Hp < 0.6f * PlayerCombat->GetMaxHealth())
				{
					PlayerCombat->SetHealth(PlayerCombat->GetMaxHealth()); WildTest.LastHp = PlayerCombat->GetHealth(); ++WildTest.Heals;
					WildSelfTestLine(FString::Printf(TEXT("heal|%.0f|said: %s|hurt: %s"), Now - WildTest.T0, *FString::Join(WildTest.Said, TEXT(" / ")), *WildTest.Hurts));
					WildTest.Hurts.Reset();
				}
			}
			if (bDead && !WildTest.bWasDead)
			{
				++WildTest.Deaths;
				int32 Near = 0;
				for (TActorIterator<ARDMonster> It(GetWorld()); It; ++It) if (!It->IsDead() && FVector::Dist(It->GetActorLocation(), L) < 3000.f) ++Near;
				FRDWSample Ds; Wild->Sample(L.X / 100.0, L.Y / 100.0, Ds, true);
				WildSelfTestLine(FString::Printf(TEXT("death|%.0f|%.2f, %.2f km|%s|water %d|monsters within 30 m %d|said: %s|hurt: %s"), Now - WildTest.T0, L.X / 100000.0, L.Y / 100000.0,
					*Wild->BiomeName(Ds.Biome), Ds.WaterKind, Near, *FString::Join(WildTest.Said, TEXT(" / ")), *WildTest.Hurts));
				WildTest.Hurts.Reset();
			}
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
			WildTest.MemAt = Now; const double M = RDWSTMemMB(), C = RDWSTCommitMB();
			WildTest.MemMax = FMath::Max(WildTest.MemMax, M); WildTest.CommitMax = FMath::Max(WildTest.CommitMax, C);
			WildSelfTestLine(FString::Printf(TEXT("mem|%.0f|%.0f|%.2f|%d|%.1f fps|walked %.2f km|commit %.0f"), Now - WildTest.T0, M, FVector::Dist2D(L, WildTest.WalkFrom) / 100000.f,
				WildChunks.Num(), Fps, WildTest.PathCm / 100000.0, C));
		}
		if (Now - WildTest.T0 >= WildTest.WalkMinutes * 60.f)
		{
			// (a walk: at least 1 km walked (not put) over the minutes, and the memory in use and committed each grown by less
			// than 1.5 GB from the start taken after the garbage was collected)
			const double M1 = RDWSTMemMB(), C1 = RDWSTCommitMB();
			Pass(TEXT("walk"), M1 - WildTest.Mem0 < 1500.0 && C1 - WildTest.Commit0 < 1500.0 && WildTest.PathCm >= 100000.0,
				FString::Printf(TEXT("%.1f min, %.2f km walked, %.2f km from its start, in use %.0f -> %.0f MB (most %.0f), committed %.0f -> %.0f MB (most %.0f), %d turns, %d steps on, %d deaths, %d heals (%.0f hit points taken)"),
				(Now - WildTest.T0) / 60.f, WildTest.PathCm / 100000.0, FVector::Dist2D(L, WildTest.WalkFrom) / 100000.f, WildTest.Mem0, M1, WildTest.MemMax,
				WildTest.Commit0, C1, WildTest.CommitMax, WildTest.Turns, WildTest.Puts, WildTest.Deaths, WildTest.Heals, WildTest.HurtTotal));
		}
		break;
	}
	default:
		if (WildTest.Stage == 5) { WildSelfTestLine(WildTest.bFailed ? TEXT("result|FAILED") : TEXT("result|ok")); WildTest.Stage = 99; }
		break;
	}
}
