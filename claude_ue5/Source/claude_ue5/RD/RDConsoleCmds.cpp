// Console commands of the list of 2026-11-10 (docs/improvements10.txt): the weather set by hand, and a jump to each major city for
// testing. Typed at the editor's console or the game's own (RDConsole.cpp passes any line to the player controller).
//   rd.Weather <clear|fair|cloudy|overcast|rain|storm|snow|fog|cloudless|0-8>   the weather at once, held there; rd.Weather auto: it
//   changes again (cloudless, 2026-11-10: no cloud layer at all; the rotation never picks it)
//   rd.GoTo <brokenspire|ashenreach|graymourne|velmorrath|kethrys|heaven> out to that city, by the map's fast travel (from a dungeon
//   back to Brokenspire first); for testing: found or not, enemies near or not
#include "RD/RDDungeonGenerator.h"
#include "RD/RDGameInstance.h"
#include "RD/RDCombat.h"
#include "HAL/IConsoleManager.h"
#include "EngineUtils.h"
#include "Engine/World.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDConsoleCmds, Log, All);

namespace
{
	ARDDungeonGenerator* RDCmdGenerator(UWorld* World)
	{
		if (!World) return nullptr;
		for (TActorIterator<ARDDungeonGenerator> It(World); It; ++It) return *It;
		return nullptr;
	}

	void RDCmdSay(ARDDungeonGenerator* G, const FString& S)
	{
		UE_LOG(LogRDConsoleCmds, Display, TEXT("%s"), *S);
		if (G && G->GetPlayerCombat()) G->GetPlayerCombat()->ShowMessage(S);
	}

	void RDWeatherCommand(const TArray<FString>& Args, UWorld* World)
	{
		ARDDungeonGenerator* G = RDCmdGenerator(World);
		if (!G) { UE_LOG(LogRDConsoleCmds, Warning, TEXT("rd.Weather: no generator in this world")); return; }
		if (Args.Num() == 0)
		{
			RDCmdSay(G, FString::Printf(TEXT("rd.Weather: %s%s (clear, fair, cloudy, overcast, rain, storm, snow, fog, cloudless, or auto)"), *ARDDungeonGenerator::WeatherName(G->GetWeather()), G->bWeatherHeld ? TEXT(", held") : TEXT("")));
			return;
		}
		const FString A = Args[0].ToLower();
		if (A == TEXT("auto")) { G->bWeatherHeld = false; RDCmdSay(G, TEXT("rd.Weather: the weather changes by itself again")); return; }
		int32 K = -1;
		if (A.IsNumeric()) K = FCString::Atoi(*A);
		else for (int32 I = 0; I < ARDDungeonGenerator::NumWeathers; ++I) if (ARDDungeonGenerator::WeatherName(I) == A) K = I;
		if (K < 0 || K >= ARDDungeonGenerator::NumWeathers) { RDCmdSay(G, FString::Printf(TEXT("rd.Weather: no weather named %s"), *Args[0])); return; }
		if (!G->bSky7 || !G->bTown) { RDCmdSay(G, TEXT("rd.Weather: this level has no sky of its own (the towns and the wilderness have)")); return; }
		G->SetWeather(K, true);
		G->bWeatherHeld = true;
		RDCmdSay(G, FString::Printf(TEXT("rd.Weather: %s (held: rd.Weather auto lets it change)"), *ARDDungeonGenerator::WeatherName(K)));
	}

	void RDGoToCommand(const TArray<FString>& Args, UWorld* World)
	{
		ARDDungeonGenerator* G = RDCmdGenerator(World);
		if (!G) { UE_LOG(LogRDConsoleCmds, Warning, TEXT("rd.GoTo: no generator in this world")); return; }
		static const TCHAR* Cities[] = { TEXT("Brokenspire"), TEXT("Ashenreach"), TEXT("Graymourne"), TEXT("Vel Morrath"), TEXT("Kethrys Spire"), TEXT("Heaven") };
		if (Args.Num() == 0) { RDCmdSay(G, TEXT("rd.GoTo <brokenspire | velmorrath | ashenreach | graymourne | kethrys | heaven>")); return; }
		const FString Want = FString::Join(Args, TEXT("")).Replace(TEXT(" "), TEXT("")).ToLower();
		FString City;
		for (const TCHAR* C : Cities) { const FString K = FString(C).Replace(TEXT(" "), TEXT("")).ToLower(); if (K == Want || K.StartsWith(Want)) { City = C; break; } }
		if (City.IsEmpty()) { RDCmdSay(G, FString::Printf(TEXT("rd.GoTo: no city named %s"), *FString::Join(Args, TEXT(" ")))); return; }
		G->ConsoleGoTo(City);
	}

	FAutoConsoleCommandWithWorldAndArgs GRDWeatherCmd(TEXT("rd.Weather"),
		TEXT("The weather at once, held: rd.Weather <clear|fair|cloudy|overcast|rain|storm|snow|fog|cloudless|0-8>; cloudless: no clouds at all, not even on the horizon (never chosen by itself); rd.Weather auto lets it change again"),
		FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&RDWeatherCommand));
	FAutoConsoleCommandWithWorldAndArgs GRDGoToCmd(TEXT("rd.GoTo"),
		TEXT("For testing: out to a major city by fast travel (found or not): rd.GoTo <brokenspire|velmorrath|ashenreach|graymourne|kethrys|heaven>"),
		FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&RDGoToCommand));
}

bool ARDDungeonGenerator::ConsoleGoTo(const FString& City)
{
	// (in the wilds: the map's fast travel at once, refused for nothing; in a dungeon of the game: back to Brokenspire, and the
	// town's tick takes her on out to the city once the wilds are ready (the -RDTownGo=town: way))
	if (bWild && IsWildReady())
	{
		bTravelForced = true;
		const bool bOk = WildTravelToTown(City);
		bTravelForced = false;
		UE_LOG(LogRDConsoleCmds, Display, TEXT("rd.GoTo %s: %s"), *City, bOk ? TEXT("travelled") : *WildTravelRefusal);
		return bOk;
	}
	if (bTownLink && !bTown)
	{
		if (URDGameInstance* GI = URDGameInstance::Of(this)) GI->TownGoTown = City;
		const bool bOk = ReturnToTown();
		UE_LOG(LogRDConsoleCmds, Display, TEXT("rd.GoTo %s: %s"), *City, bOk ? TEXT("back to Brokenspire first") : TEXT("the way back refused it"));
		return bOk;
	}
	UE_LOG(LogRDConsoleCmds, Warning, TEXT("rd.GoTo %s: this level is not part of the game's world"), *City);
	if (PlayerCombat) PlayerCombat->ShowMessage(TEXT("rd.GoTo: this level is not part of the game's world"));
	return false;
}
