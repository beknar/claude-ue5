// The wilderness's ground measured without a game or a GPU: see RDWildProbe.h.
#include "RD/RDWildProbe.h"
#include "RD/RDWild.h"
#include "RD/RDDungeonGenerator.h"
#include "Engine/World.h"
#include "Engine/Level.h"
#include "UObject/Package.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/Parse.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformTime.h"
#include "Async/ParallelFor.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDWildProbe, Log, All);

URDWildProbeCommandlet::URDWildProbeCommandlet()
{
	IsClient = false; IsEditor = true; IsServer = false; LogToConsole = true;
}

namespace
{
	template <typename T> bool RDProbeWrite(const FString& Path, const TArray<T>& A)
	{
		return FFileHelper::SaveArrayToFile(TArrayView<const uint8>((const uint8*)A.GetData(), A.Num() * sizeof(T)), *Path);
	}
}

int32 URDWildProbeCommandlet::Main(const FString& Params)
{
	uint32 Seed = 0; double X = 0.0, Y = 0.0, Half = 2000.0, Step = 4.0;
	FString Out, Points, Map = TEXT("/Game/RandomDungeon/Maps/brokenspire");
	FParse::Value(*Params, TEXT("Seed="), Seed);
	FParse::Value(*Params, TEXT("X="), X); FParse::Value(*Params, TEXT("Y="), Y);
	FParse::Value(*Params, TEXT("Half="), Half); FParse::Value(*Params, TEXT("Step="), Step);
	FParse::Value(*Params, TEXT("Out="), Out); FParse::Value(*Params, TEXT("Points="), Points, false); FParse::Value(*Params, TEXT("Map="), Map);
	if (Out.IsEmpty() || Step <= 0.0) { UE_LOG(LogRDWildProbe, Error, TEXT("RDWILDPROBE needs -Out=<dir> and a Step over 0")); return 1; }
	IFileManager::Get().MakeDirectory(*Out, true);

	// (the level's biome table, as the game's generator has it)
	UPackage* Pkg = LoadPackage(nullptr, *Map, LOAD_None);
	UWorld* World = Pkg ? UWorld::FindWorldInPackage(Pkg) : nullptr;
	ARDDungeonGenerator* Gen = nullptr;
	if (World && World->PersistentLevel)
		for (AActor* A : World->PersistentLevel->Actors) if (ARDDungeonGenerator* G = Cast<ARDDungeonGenerator>(A)) { Gen = G; break; }
	if (!Gen || Gen->WildBiomes.Num() == 0) { UE_LOG(LogRDWildProbe, Error, TEXT("RDWILDPROBE no generator with a biome table in %s"), *Map); return 1; }
	if (Seed == 0) Seed = (uint32)(Gen->WildSeedFixed != 0 ? Gen->WildSeedFixed : Gen->StartSeed);

	FRDWildWorld W;
	W.Init(Seed, Gen->WildBiomes);
	UE_LOG(LogRDWildProbe, Display, TEXT("RDWILDPROBE the world made: seed %u, %d biomes, %d towns, %.2f s"), Seed, W.Biomes.Num(), W.Towns.Num(), W.InitSeconds);

	// (the grid)
	const int32 N = FMath::FloorToInt(2.0 * Half / Step) + 1;
	const double X0 = X - Half, Y0 = Y - Half;
	TArray<float> H, Water, W1, Hd; TArray<uint8> B, B2, Col, Fk, Crop;
	H.SetNumZeroed(N * N); Water.SetNumZeroed(N * N); W1.SetNumZeroed(N * N); B.SetNumZeroed(N * N); B2.SetNumZeroed(N * N);
	// (the list of 2026-11-08b: the ground's colour as the drawn ground has it (sRGB), the farms' kind and crop there, and how far
	// the walked height (Height) is from the drawn one (Sample: the ridges are added in both))
	Col.SetNumZeroed(N * N * 3); Fk.SetNumZeroed(N * N); Crop.SetNumZeroed(N * N); Hd.SetNumZeroed(N * N);
	const bool bHeights = FParse::Param(*Params, TEXT("Heights"));
	const double T0 = FPlatformTime::Seconds();
	ParallelFor(N, [&](int32 I)
	{
		for (int32 J = 0; J < N; ++J)
		{
			FRDWSample S;
			const double Px = X0 + I * Step, Py = Y0 + J * Step;
			W.Sample(Px, Py, S, true, (float)Step);
			const int32 K = I * N + J;
			H[K] = S.H; Water[K] = S.Water; W1[K] = S.W1; B[K] = (uint8)FMath::Clamp(S.Biome, 0, 255); B2[K] = (uint8)FMath::Clamp(S.Biome2, 0, 255);
			const FColor C = S.Color.ToFColor(true);
			Col[K * 3] = C.R; Col[K * 3 + 1] = C.G; Col[K * 3 + 2] = C.B;
			Fk[K] = S.FarmKind; Crop[K] = (uint8)(S.FieldCrop + 1);
			if (bHeights) Hd[K] = W.Height(Px, Py) - S.H;
		}
	});
	UE_LOG(LogRDWildProbe, Display, TEXT("RDWILDPROBE %d x %d samples, %.1f s"), N, N, FPlatformTime::Seconds() - T0);
	bool bOk = RDProbeWrite(Out / TEXT("h.bin"), H) && RDProbeWrite(Out / TEXT("water.bin"), Water) && RDProbeWrite(Out / TEXT("w1.bin"), W1)
		&& RDProbeWrite(Out / TEXT("b.bin"), B) && RDProbeWrite(Out / TEXT("b2.bin"), B2) && RDProbeWrite(Out / TEXT("col.bin"), Col)
		&& RDProbeWrite(Out / TEXT("farm.bin"), Fk) && RDProbeWrite(Out / TEXT("crop.bin"), Crop);
	if (bHeights) bOk &= RDProbeWrite(Out / TEXT("hdiff.bin"), Hd);

	FString Info = FString::Printf(TEXT("seed|%u\nmap|%s\ngrid|%d|%.3f|%.3f|%.3f\nbaseh|%.3f\n"), Seed, *Map, N, X0, Y0, Step, W.BaseH);
	for (int32 Q = 0; Q < W.Biomes.Num(); ++Q)
		Info += FString::Printf(TEXT("biome|%d|%s|%d|%.1f|%.1f\n"), Q, *W.Biomes[Q].Name, W.Biomes[Q].Shape, W.Biomes[Q].Base, W.Biomes[Q].Amp);
	for (const FRDWildTown& T : W.Towns) Info += FString::Printf(TEXT("town|%s|%.1f|%.1f|%.2f\n"), *T.Name, T.Site.X, T.Site.Y, T.H);
	{
		TArray<FRDWildPlace> Fs; W.FarmsteadsIn(X0, Y0, X0 + 2.0 * Half, Y0 + 2.0 * Half, Fs);
		for (const FRDWildPlace& P : Fs) Info += FString::Printf(TEXT("farmstead|%d|%s|%.1f|%.1f|%.1f\n"), P.Id, *P.Name, P.At.X, P.At.Y, P.Yaw);
	}
	if (W.FarmsBiome >= 0) for (const FRDWildCrop& Cr : W.Biomes[W.FarmsBiome].Crops) Info += FString::Printf(TEXT("crop|%s|%.1f\n"), *Cr.Name, Cr.Weight);
	bOk &= FFileHelper::SaveStringToFile(Info, *(Out / TEXT("info.txt")));

	// (-Places: every place of the continent as the game makes them, cell by cell (PlacesIn: the towns, the quests' places, the
	// villages, camps, houses, spawn points, ruins, ritual sites, caves and lairs), counted by kind and listed)
	if (FParse::Param(*Params, TEXT("Places")))
	{
		TMap<FString, int32> Count; FString Txt;
		const int32 Cx = FMath::CeilToInt((W.Xn - W.Xs) / FRDWildWorld::PlaceCellM), Cy = FMath::CeilToInt((W.Ye - W.Yw) / FRDWildWorld::PlaceCellM);
		for (int32 I = 0; I < Cx; ++I)
			for (int32 J = 0; J < Cy; ++J)
			{
				TArray<FRDWildPlace> Ps; W.PlacesIn(FIntPoint(I, J), Ps);
				for (const FRDWildPlace& P : Ps)
				{
					++Count.FindOrAdd(P.Kind);
					Txt += FString::Printf(TEXT("place|%s|%s|%.1f|%.1f|%d|%s\n"), *P.Kind, *P.Name, P.At.X, P.At.Y, P.Tier, *W.BiomeName(P.Biome));
				}
			}
		FString Head = FString::Printf(TEXT("seed|%u\ncells|%d|%d\n"), Seed, Cx, Cy);
		Count.KeySort(TLess<FString>());
		for (const TPair<FString, int32>& C : Count) { Head += FString::Printf(TEXT("count|%s|%d\n"), *C.Key, C.Value); UE_LOG(LogRDWildProbe, Display, TEXT("RDWILDPROBE places %s %d"), *C.Key, C.Value); }
		bOk &= FFileHelper::SaveStringToFile(Head + Txt, *(Out / TEXT("places.txt")));
	}

	// (the points: what each is made of)
	if (!Points.IsEmpty())
	{
		FString Txt;
		TArray<FString> Ps; Points.ParseIntoArray(Ps, TEXT(";"));
		for (const FString& P : Ps)
		{
			FString Sx, Sy; if (!P.Split(TEXT(","), &Sx, &Sy)) continue;
			const double Px = FCString::Atod(*Sx), Py = FCString::Atod(*Sy);
			int32 Bi[4]; float Wt[4]; FVector2D Si[4];
			const int32 M = W.Blend(Px, Py, Bi, Wt, Si);
			FRDWSample S; W.Sample(Px, Py, S, true, 2.f);
			Txt += FString::Printf(TEXT("point|%.2f|%.2f|base %.3f|height %.3f|sample %.3f|continent %.4f|regions %d"), Px, Py, W.BaseHeight(Px, Py), W.Height(Px, Py), S.H, W.Continent(Px, Py), M);
			for (int32 Q = 0; Q < M; ++Q) Txt += FString::Printf(TEXT("|%s %.4f at (%.0f, %.0f)"), *W.BiomeName(Bi[Q]), Wt[Q], Si[Q].X, Si[Q].Y);
			Txt += TEXT("\n");
		}
		bOk &= FFileHelper::SaveStringToFile(Txt, *(Out / TEXT("points.txt")));
	}
	UE_LOG(LogRDWildProbe, Display, TEXT("RDWILDPROBE written to %s: %s"), *Out, bOk ? TEXT("ok") : TEXT("FAILED"));
	return bOk ? 0 : 1;
}
