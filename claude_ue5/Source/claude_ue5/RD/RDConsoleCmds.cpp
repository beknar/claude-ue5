// Console commands of the list of 2026-11-10 (docs/improvements10.txt): the weather set by hand, and a jump to each major city for
// testing. Typed at the editor's console or the game's own (RDConsole.cpp passes any line to the player controller).
//   rd.Weather <clear|fair|cloudy|overcast|rain|storm|snow|fog|cloudless|0-8>   the weather at once, held there; rd.Weather auto: it
//   changes again (cloudless, 2026-11-10: no cloud layer at all; the rotation never picks it)
//   rd.GoTo <brokenspire|ashenreach|graymourne|velmorrath|kethrys|heaven> out to that city, by the map's fast travel (from a dungeon
//   back to Brokenspire first); for testing: found or not, enemies near or not
// The list of 2026-11-11 (docs/improvements11.txt):
//   rd.Time <dawn|morning|noon|afternoon|evening|night|midnight|0-24>   the time of day
//   rd.Pois [hide]        every place of the map on it and listed (the small points of interest near her too); hide: only those found
//   rd.GoToPoi <n|name>   to a place of that listing
//   rd.Tier <1-30|0>      her tier, with its abilities, spells and slashes (a lower one takes them away); 0 the game's own
//   rd.RevealMap [off]    the whole map shown; off: as she has seen it
//   (rd.WildRunSpeed applies within the towns' walls too: RDWild8.cpp)
// The list of 2026-11-12 (docs/improvements12.txt):
//   rd.MapTeleport [off]  a click on the big map teleports her there once the map is revealed (RDList12.cpp)
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

	// ---- the list of 2026-11-11 (docs/improvements11.txt)
	void RDTimeCommand(const TArray<FString>& Args, UWorld* World)
	{
		// ("in console: need way to set the time of day: morning, noon, afternoon")
		ARDDungeonGenerator* G = RDCmdGenerator(World);
		if (!G) return;
		if (Args.Num() == 0) { RDCmdSay(G, FString::Printf(TEXT("rd.Time: %s (dawn, morning, noon, afternoon, evening, night, midnight, or an hour 0-24)"), *G->GetTownClock())); return; }
		static const TPair<const TCHAR*, float> Names[] = { { TEXT("dawn"), 6.f }, { TEXT("morning"), 8.f }, { TEXT("noon"), 12.f }, { TEXT("afternoon"), 15.f },
		                                                    { TEXT("evening"), 19.f }, { TEXT("night"), 22.f }, { TEXT("midnight"), 0.f } };
		const FString A = Args[0].ToLower();
		float H = -1.f;
		if (A.IsNumeric()) H = FCString::Atof(*A);
		else for (const auto& N : Names) if (A == N.Key) H = N.Value;
		if (H < 0.f || H > 24.f) { RDCmdSay(G, FString::Printf(TEXT("rd.Time: no time of day named %s"), *Args[0])); return; }
		G->SetTownHour(H);
		RDCmdSay(G, G->bTown ? FString::Printf(TEXT("rd.Time: %s"), *G->GetTownClock())
		                     : FString::Printf(TEXT("rd.Time: %s, kept for the towns and the wilds (this level is indoors)"), *G->GetTownClock()));
	}

	void RDPoisCommand(const TArray<FString>& Args, UWorld* World, FOutputDevice& Ar)
	{
		ARDDungeonGenerator* G = RDCmdGenerator(World);
		if (!G) return;
		const FString A0 = Args.Num() > 0 ? Args[0].ToLower() : FString();
		if (A0 == TEXT("hide") || A0 == TEXT("off"))
		{
			G->ConsoleShowPlaces(false);
			RDCmdSay(G, TEXT("rd.Pois: the map shows only what you have found again"));
			Ar.Log(TEXT("rd.Pois: the map shows only what you have found again"));
			return;
		}
		const int32 N = G->ConsoleShowPlaces(true);
		if (N == 0) { RDCmdSay(G, TEXT("rd.Pois: the places are the wilds' (go out of the dungeon first)")); Ar.Log(TEXT("rd.Pois: the places are the wilds'")); return; }
		// (the listing, the nearest first, to the console that ran it (PR #47's review: the game's own console shows what a command
		// writes to its output, and a Shipping game writes no log): the nearest 40, or every one with rd.Pois all; rd.GoToPoi
		// <number> goes to one)
		const bool bAll = A0 == TEXT("all");
		const TArray<FString> Lines = G->GetConsolePlaceLines();
		for (int32 I = 0; I < Lines.Num() && (bAll || I < 40); ++I)
		{
			TArray<FString> P; Lines[I].ParseIntoArray(P, TEXT("|"), false);
			if (P.Num() >= 7) Ar.Logf(TEXT("%4s  %s (%s)  %s km%s"), *P[0], *P[1], *P[2], *P[6], P[5] == TEXT("1") ? TEXT("  found") : TEXT(""));
		}
		const FString S = FString::Printf(TEXT("rd.Pois: %d places on the map%s (rd.GoToPoi <number or name>; rd.Pois all; rd.Pois hide)"), N, bAll || N <= 40 ? TEXT("") : TEXT(", the nearest 40 listed"));
		Ar.Log(S);
		RDCmdSay(G, S);
	}

	void RDGoToPoiCommand(const TArray<FString>& Args, UWorld* World)
	{
		ARDDungeonGenerator* G = RDCmdGenerator(World);
		if (!G) return;
		if (Args.Num() == 0) { RDCmdSay(G, TEXT("rd.GoToPoi <number from rd.Pois | a name>")); return; }
		const FString W = FString::Join(Args, TEXT(" "));
		RDCmdSay(G, G->ConsoleGoToPlace(W) ? FString::Printf(TEXT("rd.GoToPoi: to %s"), *W) : FString::Printf(TEXT("rd.GoToPoi: no place %s (rd.Pois lists them; in the wilds only)"), *W));
	}

	void RDTierCommand(const TArray<FString>& Args, UWorld* World)
	{
		ARDDungeonGenerator* G = RDCmdGenerator(World);
		if (!G) return;
		if (Args.Num() == 0 || !Args[0].IsNumeric()) { RDCmdSay(G, FString::Printf(TEXT("rd.Tier <1-30 | 0 the game's own>: now %d%s"), G->GrowthTier(), G->ConsoleTierNow() > 0 ? TEXT(" (set by hand)") : TEXT(""))); return; }
		RDCmdSay(G, TEXT("rd.Tier: ") + G->ConsoleSetTier(FCString::Atoi(*Args[0])));
	}

	void RDRevealMapCommand(const TArray<FString>& Args, UWorld* World)
	{
		ARDDungeonGenerator* G = RDCmdGenerator(World);
		if (!G) return;
		const bool bOff = Args.Num() > 0 && (Args[0].ToLower() == TEXT("off") || Args[0] == TEXT("0") || Args[0].ToLower() == TEXT("normal"));
		G->SetMapRevealAll(!bOff);
		RDCmdSay(G, bOff ? TEXT("rd.RevealMap: the map as you have seen it") : TEXT("rd.RevealMap: the whole map shown (rd.RevealMap off: as you have seen it)"));
	}

	// (the list of 2026-11-12: "in the console, enable click to teleport on a point on the map, when the map has been revealed")
	void RDMapTeleportCommand(const TArray<FString>& Args, UWorld* World)
	{
		ARDDungeonGenerator* G = RDCmdGenerator(World);
		if (!G) return;
		const bool bOff = Args.Num() > 0 && (Args[0].ToLower() == TEXT("off") || Args[0] == TEXT("0"));
		G->bMapClickTeleport = !bOff;
		RDCmdSay(G, bOff ? TEXT("rd.MapTeleport: off")
		                 : G->bMapRevealAll ? TEXT("rd.MapTeleport: click a point on the big map (M) to teleport there (rd.MapTeleport off: no more)")
		                                    : TEXT("rd.MapTeleport: on once the map is revealed: rd.RevealMap, then click a point on the big map (M)"));
	}

	FAutoConsoleCommandWithWorldAndArgs GRDTimeCmd(TEXT("rd.Time"), TEXT("The time of day: rd.Time <dawn|morning|noon|afternoon|evening|night|midnight|0-24>"),
		FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&RDTimeCommand));
	FAutoConsoleCommandWithWorldArgsAndOutputDevice GRDPoisCmd(TEXT("rd.Pois"), TEXT("Every place of the map shown on it and the nearest 40 listed (the small points of interest near her too); rd.Pois all: all listed; rd.Pois hide: only those found again"),
		FConsoleCommandWithWorldArgsAndOutputDeviceDelegate::CreateStatic(&RDPoisCommand));
	FAutoConsoleCommandWithWorldAndArgs GRDGoToPoiCmd(TEXT("rd.GoToPoi"), TEXT("To a place of rd.Pois' listing: rd.GoToPoi <number | name>"),
		FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&RDGoToPoiCommand));
	FAutoConsoleCommandWithWorldAndArgs GRDTierCmd(TEXT("rd.Tier"), TEXT("Her tier set by hand, with that tier's abilities, spells and slashes (a lower one takes them away): rd.Tier <1-30>; rd.Tier 0: the game's own"),
		FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&RDTierCommand));
	FAutoConsoleCommandWithWorldAndArgs GRDRevealMapCmd(TEXT("rd.RevealMap"), TEXT("The whole map shown (the wilds' and the dungeon's); rd.RevealMap off: as she has seen it"),
		FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&RDRevealMapCommand));
	FAutoConsoleCommandWithWorldAndArgs GRDMapTeleportCmd(TEXT("rd.MapTeleport"), TEXT("A click on the big map teleports her to that point, once the map is revealed (rd.RevealMap); rd.MapTeleport off: no more"),
		FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&RDMapTeleportCommand));

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
