// The wilderness's model (RDWild.h): the continent, its biome regions and their blending, heights, colours, rivers, lakes,
// ponds, marsh pools, roads, towns and places, all from one seed. Nothing here touches the engine's objects: the chunks and
// the map call it from worker threads.
#include "RD/RDWild.h"
#include "HAL/PlatformTime.h"
#include "Async/ParallelFor.h"
#include "Algo/BinarySearch.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDWildWorld, Log, All);

namespace
{
	// 16 gradient directions
	static const float RDWGX[16] = { 1.f, 0.9239f, 0.7071f, 0.3827f, 0.f, -0.3827f, -0.7071f, -0.9239f, -1.f, -0.9239f, -0.7071f, -0.3827f, 0.f, 0.3827f, 0.7071f, 0.9239f };
	static const float RDWGY[16] = { 0.f, 0.3827f, 0.7071f, 0.9239f, 1.f, 0.9239f, 0.7071f, 0.3827f, 0.f, -0.3827f, -0.7071f, -0.9239f, -1.f, -0.9239f, -0.7071f, -0.3827f };
	FORCEINLINE float RDWFade(float T) { return T * T * T * (T * (T * 6.f - 15.f) + 10.f); }
	FORCEINLINE float RDWSmooth(float A, float B, float X) { const float T = FMath::Clamp((X - A) / (B - A), 0.f, 1.f); return T * T * (3.f - 2.f * T); }
	// how far out a lake's and a pond's banks reach (metres past the water's edge): they ease the ground down to them
	constexpr double RDWLakeBankM = 400.0, RDWPondBankM = 150.0;
	// how far out a road's bank can reach (metres from its middle) where its bed is over or under the ground
	constexpr double RDWRoadBankM = 60.0;
	/** the port's harbour from the town's middle (m) for a section of Tiles tiles: its quay's line toward the sea (+X) and its half
	 *  width, from the port plan's own numbers (FRDWildWorld::PortHarbour*: 162 and 168 m for 168 tiles) */
	float RDWPortQuayM(int32 Tiles) { return (Tiles * 0.5f - FRDWildWorld::PortFrameMarginTiles - FRDWildWorld::PortHarbourDepthTiles) * FRDWildWorld::PortTileM; }
	float RDWPortHalfM(int32 Tiles) { return (Tiles * 0.5f - FRDWildWorld::PortFrameMarginTiles - FRDWildWorld::PortHarbourSideTiles) * FRDWildWorld::PortTileM; }
	FORCEINLINE double RDWSegDist(const FVector2D& P, const FVector2D& A, const FVector2D& B, double& T)
	{
		const FVector2D Ab = B - A; const double L2 = Ab.SizeSquared();
		T = L2 > 1e-6 ? FMath::Clamp(FVector2D::DotProduct(P - A, Ab) / L2, 0.0, 1.0) : 0.0;
		return FVector2D::Distance(P, A + Ab * T);
	}
	const TCHAR* RDWKinds[] = { TEXT("village"), TEXT("camp"), TEXT("house"), TEXT("spawn"), TEXT("ruins"), TEXT("ritual"), TEXT("cave"), TEXT("lair") };
	// a jittered grid's point for a cell (Cs metres, the point Jit to 1 - Jit across it)
	FORCEINLINE FVector2D RDWCellPoint(int32 I, int32 J, double Cs, double Jit, uint32 S)
	{
		return FVector2D((I + Jit + (1.0 - 2.0 * Jit) * FRDWildWorld::Rand01(I, J, S)) * Cs, (J + Jit + (1.0 - 2.0 * Jit) * FRDWildWorld::Rand01(I, J, S + 3u)) * Cs);
	}
	// the cell whose point is nearest (X, Y), half the gap to the second nearest (metres to the cell's edge) and the point
	FORCEINLINE void RDWVoronoi(double X, double Y, double Cs, double Jit, uint32 S, FIntPoint& Cell, double& Edge, FVector2D& Site)
	{
		const int32 Ci = FMath::FloorToInt(X / Cs), Cj = FMath::FloorToInt(Y / Cs);
		double D1 = 1e30, D2 = 1e30;
		for (int32 Di = -1; Di <= 1; ++Di)
			for (int32 Dj = -1; Dj <= 1; ++Dj)
			{
				const FVector2D P = RDWCellPoint(Ci + Di, Cj + Dj, Cs, Jit, S);
				const double Dd = FMath::Square(X - P.X) + FMath::Square(Y - P.Y);
				if (Dd < D1) { D2 = D1; D1 = Dd; Cell = FIntPoint(Ci + Di, Cj + Dj); Site = P; }
				else if (Dd < D2) D2 = Dd;
			}
		Edge = (FMath::Sqrt(D2) - FMath::Sqrt(D1)) * 0.5;
	}
}

uint32 FRDWildWorld::Hash(int32 X, int32 Y, uint32 S)
{
	uint32 H = S * 0x9E3779B1u + 0x7F4A7C15u;
	H ^= (uint32)X * 0x85EBCA77u; H = (H << 13) | (H >> 19); H *= 0xC2B2AE3Du;
	H ^= (uint32)Y * 0x27D4EB2Fu; H = (H << 11) | (H >> 21); H *= 0x165667B1u;
	H ^= H >> 15; H *= 0x85EBCA6Bu; H ^= H >> 13; H *= 0xC2B2AE35u; H ^= H >> 16;
	return H;
}

float FRDWildWorld::Perlin(double X, double Y, uint32 S)
{
	const double Fx = FMath::FloorToDouble(X), Fy = FMath::FloorToDouble(Y);
	const int32 Ix = (int32)Fx, Iy = (int32)Fy;
	const float Dx = (float)(X - Fx), Dy = (float)(Y - Fy);
	auto G = [S](int32 I, int32 J, float Ax, float Ay) { const uint32 H = Hash(I, J, S) & 15u; return RDWGX[H] * Ax + RDWGY[H] * Ay; };
	const float N00 = G(Ix, Iy, Dx, Dy), N10 = G(Ix + 1, Iy, Dx - 1.f, Dy), N01 = G(Ix, Iy + 1, Dx, Dy - 1.f), N11 = G(Ix + 1, Iy + 1, Dx - 1.f, Dy - 1.f);
	const float U = RDWFade(Dx), V = RDWFade(Dy);
	return 1.41f * FMath::Lerp(FMath::Lerp(N00, N10, U), FMath::Lerp(N01, N11, U), V);
}

float FRDWildWorld::PortFlatten(double X, double Y, float H) const
{
	// (the list of 2026-11-11: "near graymourne, it shifts abruptly to coastal regions. it should gradually turn into the coast
	// from the previous biome": the glacial uplands 22 km south stood 1300 m high and fell to the coast in under 3 km (42 degrees
	// between two samples, RDWildProbe). Round the port the land's height over the shore is scaled down: to 35 % within 9 km,
	// back to the whole by 30 km, so the uplands rise from the coast over kilometres)
	if (!bPortSea || H <= 1.f) return H;
	const float D = (float)FVector2D::Distance(FVector2D(X, Y), PortSite);
	const float K = (float)WorldK();
	if (D >= 30000.f * K) return H;
	return 1.f + (H - 1.f) * FMath::Lerp(0.35f, 1.f, RDWSmooth(9000.f * K, 30000.f * K, D));
}

float FRDWildWorld::PortLift(double X, double Y) const
{
	if (!bPortSea || PortLiftM <= 0.f) return 0.f;
	const float D = (float)FVector2D::Distance(FVector2D(X, Y), PortSite);
	// (whole within 2.5 km, eased out by 40 km: over 3.5 km the sea's own face sloped 2 to 3 % (PR #50's review); over 37.5 km
	// at most 0.3 %. No other town is within 40 km of the port)
	const float K = (float)WorldK();
	return D >= 40000.f * K ? 0.f : PortLiftM * (1.f - RDWSmooth(2500.f * K, 40000.f * K, D));
}

float FRDWildWorld::Grove(double X, double Y) const
{
	// (clusters: blobs of a slow noise over its upper part)
	const float Cl = RDWSmooth(0.12f, 0.30f, Fbm(X, Y, 1.0 / 170.0, 3, Seed + 301u));
	// (strips: the zero lines of a warped noise, about 15 m wide, broken by another)
	const double Wx = X + 90.0 * Fbm(X, Y, 1.0 / 650.0, 2, Seed + 302u);
	const float Ln = FMath::Abs(Fbm(Wx, Y, 1.0 / 520.0, 2, Seed + 303u));
	const float St = (1.f - RDWSmooth(0.012f, 0.03f, Ln)) * RDWSmooth(-0.15f, 0.05f, Fbm(X, Y, 1.0 / 300.0, 2, Seed + 304u));
	// (clearings: wide areas of none)
	const float Open = RDWSmooth(-0.22f, -0.06f, Fbm(X, Y, 1.0 / 900.0, 2, Seed + 305u));
	return FMath::Clamp(FMath::Max(Cl, St), 0.f, 1.f) * Open;
}

float FRDWildWorld::Fbm(double X, double Y, double Freq, int32 Oct, uint32 S, float Gain)
{
	float Sum = 0.f, Amp = 1.f, Norm = 0.f;
	for (int32 O = 0; O < Oct; ++O)
	{
		Sum += Amp * Perlin(X * Freq + O * 17.31, Y * Freq - O * 9.77, S + O * 1013u);
		Norm += Amp; Amp *= Gain; Freq *= 2.03;
	}
	return Sum / FMath::Max(Norm, 1e-4f);
}

float FRDWildWorld::Ridged(double X, double Y, double Freq, int32 Oct, uint32 S)
{
	// 0 (valleys) to 1 (the ridges' crests), each octave weighted by the one before (sharper crests)
	float Sum = 0.f, Amp = 1.f, Norm = 0.f, Wt = 1.f;
	for (int32 O = 0; O < Oct; ++O)
	{
		float R = 1.f - FMath::Abs(Perlin(X * Freq + O * 7.13, Y * Freq + O * 3.71, S + O * 2027u));
		R *= R; R *= Wt; Wt = FMath::Clamp(R * 1.6f, 0.f, 1.f);
		Sum += Amp * R; Norm += Amp; Amp *= 0.5f; Freq *= 2.07;
	}
	return Sum / FMath::Max(Norm, 1e-4f);
}

// ------------------------------------------------------------------------------------------------ the continent
float FRDWildWorld::Continent(double X, double Y) const
{
	// a rounded square (a superellipse) about the continent's middle, its coast pushed in and out by noise
	const double Mx = (Xs + Xn) * 0.5, H = (Xn - Xs) * 0.5;
	const double K = WorldK();
	const double Wu = Fbm(X, Y, 1.0 / (70000.0 * K), 3, Seed + 31u) * 0.10, Wv = Fbm(X, Y, 1.0 / (70000.0 * K), 3, Seed + 32u) * 0.10;
	const double U = Y / H + Wu, V = (X - Mx) / H + Wv;
	const double D = FMath::Pow(FMath::Pow(FMath::Abs(U), 4.0) + FMath::Pow(FMath::Abs(V), 4.0), 0.25);
	float C = 0.86f - (float)D + Fbm(X, Y, 1.0 / (42000.0 * K), 4, Seed + 1u) * 0.15f + Fbm(X, Y, 1.0 / 9000.0, 3, Seed + 2u) * 0.025f;
	// (the towns' land: Brokenspire and Ashenreach well inland; Vel Morrath near its coast but on land)
	C += 0.22f * FMath::Exp(-(float)((X * X + Y * Y) / FMath::Square(30000.0 * K)));
	for (const FRDWildTown& T : Towns)
	{
		if (T.Style == 0) continue;
		const float D2 = (float)FVector2D::DistSquared(FVector2D(X, Y), T.Site);
		if (T.Kind == TEXT("coast")) continue;
		C += 0.05f * FMath::Exp(-D2 / (5000.f * 5000.f));
	}
	return C;
}

void FRDWildWorld::Climate(double X, double Y, float& T, float& M) const
{
	// colder northward (the continent's south is warm, its north arctic) and with noise; wetter near the coasts
	const float Lt = (float)((X - Xs) / (Xn - Xs));
	T = 1.06f - 1.16f * Lt + Fbm(X, Y, 1.0 / (90000.0 * WorldK()), 3, Seed + 41u) * 0.14f;
	const float C = Continent(X, Y);
	M = 0.5f + Fbm(X, Y, 1.0 / (65000.0 * WorldK()), 4, Seed + 42u) * 0.62f + 0.22f * (1.f - RDWSmooth(0.f, 0.14f, C));
	M = FMath::Clamp(M, 0.f, 1.f);
}

void FRDWildWorld::AssignBiomes()
{
	CellsX = FMath::CeilToInt((Xn - Xs) / CellM) + 1;
	CellsY = FMath::CeilToInt((Ye - Yw) / CellM) + 1;
	CellBiome.SetNumZeroed(CellsX * CellsY);
	CellSite.SetNum(CellsX * CellsY);
	auto B = [this](const TCHAR* N) { return Biome(N); };
	for (int32 I = 0; I < CellsX; ++I)
		for (int32 J = 0; J < CellsY; ++J)
		{
			const int32 K = I * CellsY + J;
			const FVector2D Site(Xs + (I + 0.15 + 0.7 * Rand01(I, J, Seed + 51u)) * CellM, Yw + (J + 0.15 + 0.7 * Rand01(I, J, Seed + 52u)) * CellM);
			CellSite[K] = Site;
			float T, M; Climate(Site.X, Site.Y, T, M);
			const float C = Continent(Site.X, Site.Y);
			// relief: ranges along the ridges of a large ridged noise, and its peaks; volcanic areas, rare
			const float R = Ridged(Site.X, Site.Y, 1.0 / (150000.0 * WorldK()), 3, Seed + 7u) * 0.75f + 0.25f * (0.5f + 0.5f * Fbm(Site.X, Site.Y, 1.0 / (40000.0 * WorldK()), 2, Seed + 8u));
			const float V = Fbm(Site.X, Site.Y, 1.0 / (90000.0 * WorldK()), 2, Seed + 9u);
			const float Rn = Rand01(I, J, Seed + 53u);
			int32 Bi;
			if (C < 0.075f) Bi = (R > 0.5f || T < 0.32f || Rn < 0.35f) ? B(TEXT("rocky coastal")) : B(TEXT("coastal regions"));
			else if (V > 0.40f && C > 0.12f)
			{
				if (T < 0.32f) Bi = Rn < 0.6f ? B(TEXT("volcanic tundra")) : B(TEXT("geothermal caldera"));
				else Bi = Rn < 0.45f ? B(TEXT("volcanoes")) : (Rn < 0.75f ? B(TEXT("geothermal caldera")) : B(TEXT("volcanic tundra")));
			}
			else if (R > 0.62f) Bi = T < 0.30f ? B(TEXT("glacial")) : (R > 0.70f ? B(TEXT("mountains and peaks")) : B(TEXT("mountains")));
			else if (R > 0.52f)
			{
				if (T > 0.70f && M < 0.42f) Bi = Rn < 0.4f ? B(TEXT("canyons")) : (Rn < 0.7f ? B(TEXT("mesas")) : B(TEXT("canyon networks")));
				else if (M > 0.55f && T < 0.62f) Bi = B(TEXT("highland moorland"));
				else Bi = B(TEXT("hills"));
			}
			else if (T < 0.06f) Bi = M > 0.6f && Rn < 0.3f ? B(TEXT("glacial")) : B(TEXT("arctic regions"));
			else if (T < 0.18f) Bi = M > 0.55f ? B(TEXT("taigas")) : (M < 0.38f ? B(TEXT("cold steppes")) : B(TEXT("tundras")));
			else if (T < 0.34f) Bi = M > 0.62f ? B(TEXT("taigas")) : (M > 0.45f ? B(TEXT("boreal pine forest")) : (M < 0.32f ? B(TEXT("cold steppes")) : B(TEXT("tundras"))));
			else if (T < 0.50f)
			{
				if (M > 0.78f) Bi = B(TEXT("marshes"));
				else if (M > 0.58f) Bi = Rn < 0.55f ? B(TEXT("pine forests")) : B(TEXT("boreal pine forest"));
				else if (M > 0.42f) Bi = Rn < 0.5f ? B(TEXT("temperate aspen")) : B(TEXT("pine forests"));
				else Bi = M < 0.3f ? B(TEXT("cold steppes")) : B(TEXT("highland moorland"));
			}
			else if (T < 0.72f)
			{
				if (M > 0.80f) Bi = Rn < 0.5f ? B(TEXT("wetlands")) : B(TEXT("marshes"));
				else if (M > 0.62f) Bi = Rn < 0.6f ? B(TEXT("temperate autumn forests")) : B(TEXT("temperate aspen"));
				else if (M > 0.48f) Bi = Rn < 0.5f ? B(TEXT("meadows")) : B(TEXT("temperate autumn forests"));
				else if (M > 0.34f) Bi = Rn < 0.5f ? B(TEXT("grasslands")) : B(TEXT("plains"));
				else Bi = B(TEXT("plains"));
			}
			else
			{
				if (M > 0.78f) Bi = B(TEXT("wetlands"));
				else if (M > 0.55f) Bi = Rn < 0.5f ? B(TEXT("meadows")) : B(TEXT("grasslands"));
				else if (M > 0.38f) Bi = Rn < 0.5f ? B(TEXT("plains")) : B(TEXT("savannahs"));
				else Bi = Rn < 0.6f ? B(TEXT("savannahs")) : (Rn < 0.8f ? B(TEXT("mesas")) : B(TEXT("canyons")));
			}
			CellBiome[K] = Bi;
		}
	// the towns' own regions: Brokenspire among farms, the others as the spec has them
	for (const FRDWildTown& T : Towns)
	{
		const int32 I = FMath::FloorToInt((T.Site.X - Xs) / CellM), J = FMath::FloorToInt((T.Site.Y - Yw) / CellM);
		if (I < 0 || J < 0 || I >= CellsX || J >= CellsY) continue;
		const int32 K = I * CellsY + J;
		if (T.Style == 0) CellBiome[K] = B(TEXT("farms"));
		else if (T.Kind == TEXT("coast")) CellBiome[K] = B(TEXT("coastal regions"));
		else CellBiome[K] = (T.Name.Len() % 2) ? B(TEXT("farms")) : B(TEXT("meadows"));
		// (the cell's site on the town: its region is round it)
		CellSite[K] = T.Site + FVector2D(1500, -1200);
		// (a town at the edge of a region the spec names (Ashenreach's burned plain, 2026-11-07): the region's middle 5 km north
		// of it, the cell north of it the same; only when the table has that template (Biome() would give the first silently))
		if (!T.Biome.IsEmpty() && BiomeIndex.Contains(T.Biome))
		{
			CellBiome[K] = BiomeIndex[T.Biome];
			// (a volcano's cone is its region's site: there, 4.5 km off, the city stands on its lower flank, not under it)
			CellSite[K] = T.Site + FVector2D(T.BiomeSiteM > 0.f ? (double)T.BiomeSiteM : 5000.0 * WorldK(), 0.0);
			// (the cell north of it the same, but a volcano's: each volcano cell is a cone, and a second one 3.6 km from the first
			// would merge with it (PR #90's review))
			if (I + 1 < CellsX && T.Biome != TEXT("volcanoes")) { CellBiome[(I + 1) * CellsY + J] = BiomeIndex[T.Biome]; CellSite[(I + 1) * CellsY + J] = T.Site + FVector2D(16000.0, 2000.0) * WorldK(); }
		}
		// (Brokenspire's neighbours: open lowlands, never mountains next door)
		if (T.Style == 0)
			for (int32 Di = -1; Di <= 1; ++Di)
				for (int32 Dj = -1; Dj <= 1; ++Dj)
				{
					if (!Di && !Dj) continue;
					const int32 Kn = (I + Di) * CellsY + (J + Dj);
					if (!CellBiome.IsValidIndex(Kn)) continue;
					const FString& N = Biomes[CellBiome[Kn]].Name;
					if (N.Contains(TEXT("mountain")) || N == TEXT("glacial") || N.Contains(TEXT("volcan")) || N.Contains(TEXT("caldera")) || N.Contains(TEXT("canyon")) || N == TEXT("mesas"))
						CellBiome[Kn] = ((Di + Dj) & 1) ? B(TEXT("grasslands")) : B(TEXT("meadows"));
				}
	}
	// every template somewhere: one missing is given to the land cell nearest Brokenspire whose climate suits it best
	TSet<int32> Have; for (int32 Bi : CellBiome) Have.Add(Bi);
	struct FProto { const TCHAR* N; float T, M, R; };
	static const FProto Protos[] = {
		{ TEXT("grasslands"), 0.6f, 0.4f, 0.3f }, { TEXT("meadows"), 0.6f, 0.55f, 0.3f }, { TEXT("farms"), 0.7f, 0.45f, 0.2f }, { TEXT("savannahs"), 0.9f, 0.35f, 0.3f },
		{ TEXT("hills"), 0.5f, 0.45f, 0.56f }, { TEXT("mountains"), 0.4f, 0.5f, 0.65f }, { TEXT("tundras"), 0.15f, 0.45f, 0.3f }, { TEXT("plains"), 0.7f, 0.35f, 0.2f },
		{ TEXT("pine forests"), 0.45f, 0.62f, 0.3f }, { TEXT("temperate autumn forests"), 0.6f, 0.68f, 0.3f }, { TEXT("marshes"), 0.45f, 0.85f, 0.2f }, { TEXT("wetlands"), 0.65f, 0.85f, 0.2f },
		{ TEXT("mountains and peaks"), 0.4f, 0.5f, 0.75f }, { TEXT("volcanoes"), 0.6f, 0.4f, 0.5f }, { TEXT("coastal regions"), 0.6f, 0.6f, 0.2f }, { TEXT("arctic regions"), 0.02f, 0.5f, 0.3f },
		{ TEXT("canyons"), 0.85f, 0.3f, 0.56f }, { TEXT("mesas"), 0.85f, 0.25f, 0.55f }, { TEXT("canyon networks"), 0.85f, 0.3f, 0.57f }, { TEXT("cold steppes"), 0.25f, 0.28f, 0.3f },
		{ TEXT("highland moorland"), 0.45f, 0.62f, 0.56f }, { TEXT("boreal pine forest"), 0.28f, 0.55f, 0.3f }, { TEXT("temperate aspen"), 0.48f, 0.55f, 0.3f }, { TEXT("volcanic tundra"), 0.2f, 0.4f, 0.4f },
		{ TEXT("geothermal caldera"), 0.3f, 0.5f, 0.45f }, { TEXT("glacial"), 0.1f, 0.6f, 0.65f }, { TEXT("taigas"), 0.15f, 0.65f, 0.3f }, { TEXT("rocky coastal"), 0.3f, 0.5f, 0.5f } };
	for (const FProto& P : Protos)
	{
		const int32* Bi = BiomeIndex.Find(P.N);
		if (!Bi || Have.Contains(*Bi)) continue;
		const bool bCoast = FString(P.N).Contains(TEXT("coast"));
		int32 Best = -1; float BestS = 1e9f;
		for (int32 K = 0; K < CellBiome.Num(); ++K)
		{
			const FVector2D& S = CellSite[K];
			const float C = Continent(S.X, S.Y);
			if (bCoast ? (C < 0.f || C > 0.075f) : C < 0.1f) continue;
			bool bTown = false; for (const FRDWildTown& T : Towns) if (FVector2D::Distance(T.Site, S) < CellM * 1.6) bTown = true;
			if (bTown) continue;
			float T, M; Climate(S.X, S.Y, T, M);
			const float Sc = FMath::Square(T - P.T) * 4.f + FMath::Square(M - P.M) * 2.f + (float)(FVector2D::Distance(S, FVector2D::ZeroVector) / (400000.0 * WorldK()));
			// (a cell that is the only one of its own kind is kept)
			int32 Same = 0; for (int32 Bj : CellBiome) if (Bj == CellBiome[K]) ++Same;
			if (Same < 3) continue;
			if (Sc < BestS) { BestS = Sc; Best = K; }
		}
		if (Best >= 0) { CellBiome[Best] = *Bi; Have.Add(*Bi); }
	}
}

int32 FRDWildWorld::Blend(double X, double Y, int32* Idx, float* W, FVector2D* Site) const
{
	// the regions' borders wander (a warped Voronoi); weights fall off over ~2 km past the nearest site's distance. Since the
	// list of 2026-11-04 ("the transition between terrain types is too abrupt and looks like a straight line from above ... it
	// should look more natural and ragged and uneven") the warp has two finer scales too (700 m, 180 m) and the fall-off is
	// wider: a border wanders at every scale and the regions flow into each other over 3 to 6 km
	const double Wk = WorldK();          // (the borders' broad warp at the continent's scale, as its cells)
	const double Wx = X + Fbm(X, Y, 1.0 / (13000.0 * Wk), 4, Seed + 61u) * 6500.0 * Wk + Fbm(X, Y, 1.0 / 2600.0, 2, Seed + 63u) * 900.0
	                    + Fbm(X, Y, 1.0 / 700.0, 2, Seed + 65u) * 320.0 + Fbm(X, Y, 1.0 / 180.0, 2, Seed + 67u) * 70.0;
	const double Wy = Y + Fbm(X, Y, 1.0 / (13000.0 * Wk), 4, Seed + 62u) * 6500.0 * Wk + Fbm(X, Y, 1.0 / 2600.0, 2, Seed + 64u) * 900.0
	                    + Fbm(X, Y, 1.0 / 700.0, 2, Seed + 66u) * 320.0 + Fbm(X, Y, 1.0 / 180.0, 2, Seed + 68u) * 70.0;
	// (the user's of 2026-11-08: "a wall of earth that is a sheer drop that can't be climbed" 12 km from Brokenspire. The four
	// heaviest regions were kept at their whole weight and the rest dropped, and so were weights under 0.03: where a mountain
	// region took the fourth place from a farm's, or rose past 0.03, it came in at 2 to 9 % at once, and at its 650 to 3200 m
	// the ground stepped 26 to 125 m between two samples (RDWildProbe on the user's seed: walls 22 and 32 km long round the
	// town). Each region now counts by how much it is over the cut (the fifth heaviest's weight, at least 0.03), so a region
	// comes in from nothing as it gains its place. The 5 x 5 cells round the point: a town's region can have its site moved
	// 16 km, more than a cell, off its own cell, and a cell left out must weigh under the cut)
	const int32 Ic = FMath::Clamp(FMath::FloorToInt((Wx - Xs) / CellM), 0, CellsX - 1), Jc = FMath::Clamp(FMath::FloorToInt((Wy - Yw) / CellM), 0, CellsY - 1);
	constexpr int32 RDWBlendRad = 2, RDWBlendMax = (2 * RDWBlendRad + 1) * (2 * RDWBlendRad + 1);
	int32 Ci[RDWBlendMax]; double Cd[RDWBlendMax]; int32 N = 0; double Dmin = 1e18;
	for (int32 Di = -RDWBlendRad; Di <= RDWBlendRad; ++Di)
		for (int32 Dj = -RDWBlendRad; Dj <= RDWBlendRad; ++Dj)
		{
			const int32 I = Ic + Di, J = Jc + Dj;
			if (I < 0 || J < 0 || I >= CellsX || J >= CellsY) continue;
			const int32 K = I * CellsY + J;
			Ci[N] = K; Cd[N] = FVector2D::Distance(FVector2D(Wx, Wy), CellSite[K]); Dmin = FMath::Min(Dmin, Cd[N]); ++N;
		}
	// (the list of 2026-11-11: "near graymourne, it shifts abruptly to coastal regions. it should gradually turn into the coast
	// from the previous biome": the regions round the port flow into each other over 2.6 times the distance, eased back by 22 km)
	const double Tau = 2400.0 * (bPortSea ? 1.0 + 1.6 * (1.0 - RDWSmooth(9000.f * (float)WorldK(), 22000.f * (float)WorldK(), (float)FVector2D::Distance(FVector2D(X, Y), PortSite))) : 1.0);
	float Tw[RDWBlendMax];
	for (int32 Q = 0; Q < N; ++Q) Tw[Q] = (float)FMath::Exp(-(Cd[Q] - Dmin) / Tau);
	// the five heaviest, in order (a picked one marked -1)
	int32 Top[5]; float TopW[5]; int32 Nt = 0;
	for (int32 Pick = 0; Pick < 5; ++Pick)
	{
		int32 Bq = -1; float Bw = -0.5f;
		for (int32 Q = 0; Q < N; ++Q) if (Tw[Q] > Bw) { Bw = Tw[Q]; Bq = Q; }
		if (Bq < 0) break;
		Top[Nt] = Bq; TopW[Nt] = Bw; ++Nt; Tw[Bq] = -1.f;
	}
	const float Cut = FMath::Max(0.03f, Nt > 4 ? TopW[4] : 0.f);
	int32 M = 0; float Sum = 0.f;
	for (int32 P = 0; P < FMath::Min(Nt, 4); ++P)
	{
		const float Wq = TopW[P] - Cut;
		if (Wq <= 0.f) break;
		Idx[M] = CellBiome[Ci[Top[P]]]; W[M] = Wq; Site[M] = CellSite[Ci[Top[P]]]; Sum += Wq; ++M;
	}
	// (five regions at one distance: the nearest alone)
	if (M == 0 && Nt > 0) { Idx[0] = CellBiome[Ci[Top[0]]]; W[0] = 1.f; Site[0] = CellSite[Ci[Top[0]]]; Sum = 1.f; M = 1; }
	for (int32 Q = 0; Q < M; ++Q) W[Q] /= Sum;
	return M;
}

int32 FRDWildWorld::BiomeAt(double X, double Y) const
{
	int32 I[4]; float W[4]; FVector2D S[4];
	const int32 N = Blend(X, Y, I, W, S);
	return N > 0 ? I[0] : 0;
}

float FRDWildWorld::ShapeHeight(int32 B, double X, double Y, const FVector2D& Site, bool bDetail) const
{
	const FRDWildBiome& Bi = Biomes[B];
	const float Base = Bi.Base, A = Bi.Amp;
	const uint32 S = Seed + 100u;
	switch (Bi.Shape)
	{
	default:
	case ERDWShape::Plains: return Base + A * Fbm(X, Y, 1.0 / 3200.0, 3, S) + (bDetail ? A * 0.12f * Fbm(X, Y, 1.0 / 260.0, 2, S + 1) : 0.f);
	case ERDWShape::Rolling: return Base + A * Fbm(X, Y, 1.0 / 2300.0, 4, S + 2) + (bDetail ? A * 0.08f * Fbm(X, Y, 1.0 / 220.0, 2, S + 3) : 0.f);
	case ERDWShape::Hills: return Base + A * (0.7f * Fbm(X, Y, 1.0 / 2600.0, 4, S + 4) + 0.8f * (Ridged(X, Y, 1.0 / 1900.0, 3, S + 5) - 0.35f)) + (bDetail ? A * 0.04f * Fbm(X, Y, 1.0 / 180.0, 2, S + 6) : 0.f);
	case ERDWShape::Moor: return Base + A * Fbm(X, Y, 1.0 / 3600.0, 4, S + 7) + A * 0.25f * Fbm(X, Y, 1.0 / 650.0, 2, S + 8) + (bDetail ? A * 0.04f * Fbm(X, Y, 1.0 / 120.0, 2, S + 9) : 0.f);
	case ERDWShape::Steppe: return Base + A * Fbm(X, Y, 1.0 / 5200.0, 4, S + 10) + A * 0.18f * Fbm(X, Y, 1.0 / 850.0, 2, S + 11);
	case ERDWShape::Mountains:
	{
		const float R = Ridged(X, Y, 1.0 / 7500.0, bDetail ? 6 : 4, S + 12);
		return Base + A * FMath::Pow(R, 1.25f) + A * 0.08f * Fbm(X, Y, 1.0 / 1100.0, 3, S + 13);
	}
	case ERDWShape::Peaks:
	{
		const float R = Ridged(X, Y, 1.0 / 6200.0, bDetail ? 7 : 4, S + 14);
		return Base + A * FMath::Pow(R, 1.7f) + A * 0.06f * Fbm(X, Y, 1.0 / 800.0, 3, S + 15);
	}
	case ERDWShape::Glacial:
	{
		// broad U-shaped valleys between smooth ice-capped ridges
		const float R = Ridged(X, Y, 1.0 / 9500.0, 4, S + 16);
		return Base + A * FMath::Pow(R, 1.1f) + A * 0.03f * Fbm(X, Y, 1.0 / 900.0, 2, S + 17);
	}
	case ERDWShape::Mesa:
	{
		// flat-topped tables with steep edges, the slopes stepped in layers
		const float Mk = RDWSmooth(0.04f, 0.10f, Fbm(X, Y, 1.0 / 3400.0, 4, S + 18));
		float H = A * Mk;
		const float Step = 28.f, Q = H / Step, F = Q - FMath::FloorToFloat(Q);
		H = (FMath::FloorToFloat(Q) + RDWSmooth(0.55f, 0.95f, F)) * Step;
		return Base + H + 6.f * Fbm(X, Y, 1.0 / 900.0, 3, S + 19);
	}
	case ERDWShape::Canyon:
	case ERDWShape::CanyonNet:
	{
		// a plateau cut by channels: the zero lines of a warped noise (one set, or two crossing for the networks)
		const double Wx = X + 900.0 * Fbm(X, Y, 1.0 / 5000.0, 2, S + 20), Wy = Y + 900.0 * Fbm(X, Y, 1.0 / 5000.0, 2, S + 21);
		float Ch = 1.f - FMath::Abs(Perlin(Wx / 5200.0, Wy / 5200.0, S + 22));
		if (Bi.Shape == ERDWShape::CanyonNet)
		{
			Ch = FMath::Max(Ch, 1.f - FMath::Abs(Perlin(Wx / 2300.0, Wy / 2300.0, S + 23)));
			Ch = FMath::Max(Ch, 0.97f * (1.f - FMath::Abs(Perlin(Wx / 1400.0, Wy / 1400.0, S + 24))));
		}
		float Cut = RDWSmooth(0.88f, 0.975f, Ch);
		// (stepped walls)
		const float Q = Cut * 5.f; Cut = (FMath::FloorToFloat(Q) + RDWSmooth(0.35f, 0.9f, Q - FMath::FloorToFloat(Q))) / 5.f;
		return Base + 14.f * Fbm(X, Y, 1.0 / 2600.0, 3, S + 25) - A * Cut;
	}
	case ERDWShape::Volcano:
	{
		const float R = (float)FVector2D::Distance(FVector2D(X, Y), Site);
		const float Cone = FMath::Pow(FMath::Max(0.f, 1.f - R / 7800.f), 1.7f);
		float H = Base + A * Cone;
		if (R < 950.f) H -= A * 0.2f * FMath::Square(1.f - R / 950.f) * 2.2f;          // the crater
		H -= Cone * A * 0.06f * Ridged(X, Y, 1.0 / 700.0, 3, S + 26);                     // gullies down its flanks
		return H + 25.f * Fbm(X, Y, 1.0 / 2200.0, 3, S + 27);
	}
	case ERDWShape::Caldera:
	{
		const float R = (float)FVector2D::Distance(FVector2D(X, Y), Site);
		const float Ring = A * FMath::Exp(-FMath::Square((R - 4300.f) / 1250.f));
		const float Floor = R < 4300.f ? -A * 0.18f * (1.f - R / 4300.f) : 0.f;
		return Base + Ring + Floor + 18.f * Fbm(X, Y, 1.0 / 1500.0, 3, S + 28) + (bDetail ? 3.f * Fbm(X, Y, 1.0 / 160.0, 2, S + 29) : 0.f);
	}
	case ERDWShape::LavaField: return Base + A * Fbm(X, Y, 1.0 / 2600.0, 3, S + 30) + A * 0.35f * (Ridged(X, Y, 1.0 / 420.0, 3, S + 31) - 0.3f);
	case ERDWShape::Marsh: return Base + A * Fbm(X, Y, 1.0 / 2400.0, 3, S + 32) + (bDetail ? 0.25f * Fbm(X, Y, 1.0 / 90.0, 2, S + 33) : 0.f);
	case ERDWShape::Coastal: return Base + A * Fbm(X, Y, 1.0 / 2600.0, 3, S + 34) + (bDetail ? A * 0.08f * Fbm(X, Y, 1.0 / 200.0, 2, S + 35) : 0.f);
	case ERDWShape::RockyCoast: return Base + A * Ridged(X, Y, 1.0 / 1500.0, 4, S + 36) + (bDetail ? A * 0.05f * Fbm(X, Y, 1.0 / 150.0, 2, S + 37) : 0.f);
	case ERDWShape::Dunes:
	{
		const double U = X * 0.8 + Y * 0.6;
		return Base + A * (0.5f + 0.5f * FMath::Sin((float)(U / 140.0) + 3.f * Fbm(X, Y, 1.0 / 1500.0, 2, S + 38)));
	}
	}
}

float FRDWildWorld::LandHeight(double X, double Y, bool bDetail, int32* OutB, int32* OutB2, float* OutW, float* OutC, float* OutFarm) const
{
	int32 Bi[4]; float W[4]; FVector2D Si[4];
	const int32 N = Blend(X, Y, Bi, W, Si);
	float H = 0.f, Rocky = 0.f, Farm = 0.f;
	for (int32 Q = 0; Q < N; ++Q)
	{
		H += W[Q] * ShapeHeight(Bi[Q], X, Y, Si[Q], bDetail);
		// (the list of 2026-11-14: a biome's swales, low rises some 400 m apart, so a crest hides what lies beyond it ("rolling swales
		// that hide what's over the next rise"), weighed as its shape is: no seam where it meets another)
		if (Biomes[Bi[Q]].Swale > 0.f) H += W[Q] * Biomes[Bi[Q]].Swale * Fbm(X, Y, 1.0 / 420.0, 2, Seed + 141u);
		if (Biomes[Bi[Q]].Shape == ERDWShape::RockyCoast) Rocky += W[Q];
		if (Bi[Q] == FarmsBiome) Farm += W[Q];
	}
	if (OutFarm) *OutFarm = Farm;
	H += LandRelief(X, Y, bDetail, Bi, W, N);
	H = PortFlatten(X, Y, H);
	if (OutB) *OutB = N > 0 ? Bi[0] : 0;
	if (OutB2) *OutB2 = N > 1 ? Bi[1] : (N > 0 ? Bi[0] : 0);
	if (OutW) *OutW = N > 0 ? W[0] : 1.f;
	// the coast: the land falls to a beach (or, on a rocky coast, to cliffs) and the sea floor away from it
	const float C = Continent(X, Y);
	if (OutC) *OutC = C;
	if (C >= 0.f)
	{
		const float Kc = FMath::Lerp(0.05f, 0.007f, FMath::Clamp(Rocky, 0.f, 1.f));
		return 1.f + (H - 1.f) * RDWSmooth(0.f, Kc, C);
	}
	return 1.f - 2.5f * RDWSmooth(0.f, 0.004f, -C) - SeaDepth * RDWSmooth(0.004f, 0.05f, -C);
}

float FRDWildWorld::BaseHeight(double X, double Y) const { return LandHeight(X, Y, true); }

FString FRDWildWorld::CropName(const FRDWSample& S, float MinField) const
{
	const FRDWildBiome* Fb = Biomes.IsValidIndex(FarmsBiome) ? &Biomes[FarmsBiome] : nullptr;
	return Fb && Fb->Crops.IsValidIndex(S.FieldCrop) && S.Field > MinField ? Fb->Crops[S.FieldCrop].Name : FString();
}

// ------------------------------------------------------------------------------------------------ the farms (the list of 2026-11-08b)
int32 FRDWildWorld::PickCrop(int32 A, int32 B, uint32 S) const
{
	// (the crops' weights, biomes.json's "weight", the commonest first: their running sums are made once at Init)
	const FRDWildBiome* Fb = Biomes.IsValidIndex(FarmsBiome) ? &Biomes[FarmsBiome] : nullptr;
	if (!Fb || Fb->Crops.Num() == 0) return -1;
	if (CropCum.Num() != Fb->Crops.Num() || CropCum.Last() <= 0.f) return 0;
	const float Pick = Rand01(A, B, S) * CropCum.Last();
	return FMath::Min(Algo::UpperBound(CropCum, Pick), CropCum.Num() - 1);
}

float FRDWildWorld::FarmWeight(double X, double Y) const
{
	if (FarmsBiome < 0) return 0.f;
	int32 Bi[4]; float W[4]; FVector2D Si[4];
	const int32 N = Blend(X, Y, Bi, W, Si);
	float F = 0.f;
	for (int32 Q = 0; Q < N; ++Q) if (Bi[Q] == FarmsBiome) F += W[Q];
	return F;
}

/** a field's stage from a draw (the list of 2026-11-14): ripe a little over half, sprouting a fifth, fallow a sixth, burned one in 16 */
static uint8 RDWFieldStage(float U) { return U < 0.56f ? 0 : U < 0.78f ? 1 : U < 0.94f ? 2 : 3; }

void FRDWildWorld::FarmAt(double X, double Y, float FarmW, FRDWFarm& O) const
{
	O = FRDWFarm();
	if (FarmW <= 0.2f) return;
	// ---- the great field: the land nearest a point of a jittered 420 m grid, the land warped so its edges bend (the list of
	// 2026-11-04: "it should not be that regular or mechanical"); toward the farms' edge the great fields thin out, each at a
	// farm weight of its own, and each eases in over 4 to 14 m from its edge (a lane, a hedge bank, a stream's grass)
	const double Wx = X + Fbm(X, Y, 1.0 / 700.0, 2, Seed + 88u) * 45.0, Wy = Y + Fbm(X, Y, 1.0 / 700.0, 2, Seed + 89u) * 45.0;
	FIntPoint G; double Eg; FVector2D Site;
	RDWVoronoi(Wx, Wy, GreatFieldM, 0.15, Seed + 90u, G, Eg, Site);
	const float Need = 0.22f + 0.5f * Rand01(G.X, G.Y, Seed + 91u);
	const float Fade = RDWSmooth(Need, Need + 0.12f, FarmW) * RDWSmooth(4.f, 14.f, (float)Eg);
	if (Fade <= 0.f) return;
	const float Pr = Rand01(G.X, G.Y, Seed + 85u);
	// (the list of 2026-11-16's density: half the great fields crofts (a farmstead's yard among small plots), 20 % before)
	O.Kind = Pr < 0.40f ? 1 : Pr < 0.90f ? 2 : Pr < 0.97f ? 3 : 0;
	if (O.Kind == 0) return;
	O.Great = G; O.Site = Site; O.Fade = Fade;
	const float GAng = Rand01(G.X, G.Y, Seed + 92u) * PI;
	// (pasture: grass over the old ridges ("still visible in English pastures today"); a field's own, or a holding's beyond its
	// plots, or a holding by a town's wall: one way of making it (PR #30's review: three copies))
	auto Pasture = [&]()
	{
		O.Kind = 3;
		const double V = X * -FMath::Sin(GAng) + Y * FMath::Cos(GAng) + Rand01(G.X, G.Y, Seed + 106u) * 18.0;
		O.Ridge = 0.16f * FMath::Square(FMath::Sin(PI * (float)(V / 18.0 - FMath::FloorToDouble(V / 18.0)))) * Fade;
		O.Furrow = 0.f;
	};
	auto Strips = [&](float Ang, float Width, float Off)
	{
		// (ridge-and-furrow: each strip ploughed into a ridge, its edges the furrows between it and its neighbours)
		O.Ang = Ang; O.StripW = Width; O.StripOff = Off;
		const double V = X * -FMath::Sin(Ang) + Y * FMath::Cos(Ang) + Off;
		const double Sn = FMath::FloorToDouble(V / Width);
		const float F = (float)(V / Width - Sn);
		O.Strip = (int32)Sn;
		O.Furrow = 1.f - RDWSmooth(0.35f, 1.2f, FMath::Min(F, 1.f - F) * Width);
		return FMath::Square(FMath::Sin(PI * F));
	};
	if (O.Kind == 1)
	{
		// ---- an open field: one crop the whole field ("rotation was decided for each whole field"), its furlongs (a Voronoi
		// about 150 m across) each its strips' own way (the field's, or across it), headlands of grass between them where the
		// plough turned; the strips 15 to 24 m wide, unfenced, divided only by their furrows
		FIntPoint Fl; double Ef; FVector2D Fp;
		RDWVoronoi(Wx, Wy, 150.0, 0.1, Seed + 95u, Fl, Ef, Fp);
		const float Ang = FMath::Fmod(GAng + (Rand01(Fl.X, Fl.Y, Seed + 96u) < 0.5f ? 0.f : HALF_PI) + (Rand01(Fl.X, Fl.Y, Seed + 97u) - 0.5f) * 0.35f + 2.f * PI, PI);
		const float Wd = 15.f + 9.f * Rand01(Fl.X, Fl.Y, Seed + 98u);
		const float Rd = Strips(Ang, Wd, Rand01(Fl.X, Fl.Y, Seed + 99u) * Wd);
		O.Plot = Fl;
		O.Crop = PickCrop(G.X, G.Y, Seed + 141u);
		O.Stage = RDWFieldStage(Rand01(G.X, G.Y, Seed + 142u));
		if (O.Stage >= 2) O.Crop = -1;          // (fallow or burned: no crop to tend, harvest or plant (PR #66's review))
		O.Field = Fade * RDWSmooth(2.f, 4.5f, (float)Ef) * (1.f - 0.65f * O.Furrow);
		O.Ridge = (0.28f + 0.14f * Rand01(Fl.X, Fl.Y, Seed + 100u)) * Rd * Fade * RDWSmooth(1.f, 5.f, (float)Ef);
		O.Shade = 0.91f + 0.18f * Rand01(O.Strip, Fl.X * 7919 + Fl.Y, Seed + 101u);
		return;
	}
	if (O.Kind == 3) { Pasture(); return; }
	// ---- crofts: the farmstead's yard round the field's point, the small plots round it (30 to 60 m, a farm of its own size)
	// out to 120 to 190 m, each one of the holding's three crops or grass, grass baulks between them; the rest of the field the
	// holding's pasture (a first look drew plots of every crop over the whole 420 m field: confetti)
	const double Dsite = FVector2D::Distance(FVector2D(X, Y), Site);
	// (no holding beside a town's wall: its field is pasture (FarmsteadsIn would put no farmstead there, and an empty yard showed))
	for (const FRDWildTown& T : Towns) if (FVector2D::DistSquared(Site, T.Site) < FMath::Square(450.0)) { Pasture(); return; }
	if (Dsite < 34.0) { O.Kind = 4; return; }
	const double Reach = 120.0 + 70.0 * Rand01(G.X, G.Y, Seed + 109u) + 25.0 * Fbm(X, Y, 1.0 / 90.0, 2, Seed + 110u);
	if (Dsite > Reach) { Pasture(); return; }
	const double Pm = 30.0 + 30.0 * Rand01(G.X, G.Y, Seed + 107u);
	FIntPoint Pl; double Ep; FVector2D Pp;
	RDWVoronoi(Wx, Wy, Pm, 0.15, Seed + 102u, Pl, Ep, Pp);
	O.Plot = Pl;
	O.Ang = Rand01(Pl.X, Pl.Y, Seed + 104u) * PI;
	if (Rand01(Pl.X, Pl.Y, Seed + 103u) < 0.6f)
	{
		O.Crop = PickCrop(G.X * 3 + (int32)(Rand01(Pl.X, Pl.Y, Seed + 105u) * 3.f), G.Y, Seed + 111u);
		O.Stage = RDWFieldStage(Rand01(Pl.X, Pl.Y, Seed + 143u));
		if (O.Stage >= 2) O.Crop = -1;
		O.Field = Fade * RDWSmooth(1.2f, 3.5f, (float)Ep) * RDWSmooth(0.f, 6.f, (float)(Reach - Dsite));
		O.Shade = 0.94f + 0.12f * Rand01(Pl.X, Pl.Y, Seed + 108u);
	}
}

void FRDWildWorld::FarmsteadsIn(double X0, double Y0, double X1, double Y1, TArray<FRDWildPlace>& Out) const
{
	if (FarmsBiome < 0) return;
	// (a great field's point lies in its own cell: the cells the box covers (PR #30's review: a ring round them never passed))
	const int32 I0 = FMath::FloorToInt(X0 / GreatFieldM), I1 = FMath::FloorToInt(X1 / GreatFieldM);
	const int32 J0 = FMath::FloorToInt(Y0 / GreatFieldM), J1 = FMath::FloorToInt(Y1 / GreatFieldM);
	for (int32 Gi = I0; Gi <= I1; ++Gi)
		for (int32 Gj = J0; Gj <= J1; ++Gj)
		{
			const float Pr = Rand01(Gi, Gj, Seed + 85u);
			if (Pr < 0.40f || Pr >= 0.90f) continue;          // (the crofts, as FarmAt has them since the list of 2026-11-16's density)
			const FVector2D At = RDWCellPoint(Gi, Gj, GreatFieldM, 0.15, Seed + 90u);
			if (At.X < X0 || At.X >= X1 || At.Y < Y0 || At.Y >= Y1) continue;
			if (At.X < Xs || At.X > Xn || At.Y < Yw || At.Y > Ye) continue;
			// (well inside the farms, its own field round it, dry, off the roads, a way from the towns, on level ground)
			const float Fw = FarmWeight(At.X, At.Y);
			FRDWFarm Fm; FarmAt(At.X, At.Y, Fw, Fm);
			if (Fm.Kind != 4 || Fm.Great != FIntPoint(Gi, Gj) || Fm.Fade < 0.5f) continue;
			FRDWSample S; Sample(At.X, At.Y, S, false);
			if (S.WaterKind != 0 || S.Road > 0.02f || S.H < 1.f) continue;
			// (its whole ground dry, off the roads and level: the barn, the paddock and the cart stand 10 to 30 m out, the scarecrow
			// and the farmer up to 40 (PR #30's review: a road 12 m off lay under the barn, the point alone was looked at))
			float Lo = S.H, Hi = S.H; bool bBad = false;
			for (const double Rr : { 10.0, 22.0, 34.0 })
				for (int32 K = 0; K < 8 && !bBad; ++K)
				{
					const double A = K * PI / 4.0;
					FRDWSample Q; Sample(At.X + FMath::Cos(A) * Rr, At.Y + FMath::Sin(A) * Rr, Q, false);
					if (Q.WaterKind != 0 || Q.Road > 0.02f) bBad = true;
					Lo = FMath::Min(Lo, Q.H); Hi = FMath::Max(Hi, Q.H);
				}
			if (bBad || Hi - Lo > 4.5f) continue;
			// (nor on another place: a village, a camp, a lair, a quest's place, within 150 m (PR #30's review))
			{
				TArray<FRDWildPlace> Near;
				const FIntPoint Ca = PlaceCellOf(At.X - 150.0, At.Y - 150.0), Cb = PlaceCellOf(At.X + 150.0, At.Y + 150.0);
				for (int32 Ci = Ca.X; Ci <= Cb.X; ++Ci) for (int32 Cj = Ca.Y; Cj <= Cb.Y; ++Cj) PlacesIn(FIntPoint(Ci, Cj), Near);
				if (Near.ContainsByPredicate([&](const FRDWildPlace& Q) { return FVector2D::DistSquared(Q.At, At) < FMath::Square(150.0); })) continue;
			}
			FRDWildPlace P;
			P.Id = FarmIdBase + (((Gi & 0x3FF) << 10) | (Gj & 0x3FF));
			P.Kind = TEXT("farmstead"); P.At = At; P.H = S.H; P.Biome = S.Biome; P.Tier = TierAt(At.X, At.Y);
			P.Name = NameFor(P.Kind, Hash(Gi, Gj, Seed + 125u));
			// (square to its field's way, turned a quarter at a time)
			P.Yaw = FMath::RadiansToDegrees(Rand01(Gi, Gj, Seed + 92u) * PI) + 90.f * (int32)(Rand01(Gi, Gj, Seed + 126u) * 4.f);
			Out.Add(P);
		}
}

float FRDWildWorld::LandRelief(double X, double Y, bool bDetail, const int32* Bi, const float* W, int32 N) const
{
	// low ridges and hollows over every region but the flattest (marshes, beaches, the farms' fields), scaled by how rugged
	// the regions there are
	float Flat = 0.f;
	for (int32 Q = 0; Q < N; ++Q)
	{
		const int32 Sh = Biomes[Bi[Q]].Shape;
		if (Sh == ERDWShape::Marsh || Sh == ERDWShape::Coastal) Flat += W[Q];
		else if (Sh == ERDWShape::Plains) Flat += W[Q] * 0.55f;
	}
	const float K = 1.f - 0.85f * FMath::Clamp(Flat, 0.f, 1.f);
	const float R1 = (Ridged(X, Y, 1.0 / 3800.0, bDetail ? 4 : 3, Seed + 131u) - 0.32f) * 46.f;
	const float R2 = Fbm(X, Y, 1.0 / 1300.0, bDetail ? 3 : 2, Seed + 132u) * 13.f;
	const float R3 = (Ridged(X, Y, 1.0 / 9500.0, 3, Seed + 133u) - 0.3f) * 55.f;
	// (the list of 2026-11-04: "all of the ground terrain in the wilderness is uniformly flat. there should be natural hills,
	// dips, ridges, berms": the regions' shapes and the relief above vary over kilometres, and walked over a few hundred
	// metres the land was level. Hills and hollows of 150 to 500 m, ridges and berms of 60 to 250 m, swells of 25 m; the
	// flattest (marsh, beach) keep a little of it, a farm's fields most of it)
	// (measured by 888's ground7: the first try (7.5 m at 420 m, 4.2 at 240, 0.55 at 26) left a plain's 300 m within 2 m and
	// its swells under half a metre; the second (11 m, 6 m, K2 1 - 0.45 Flat) a plain's 300 m within 1.8 m, a farm's 3.7)
	const float K2 = 1.f - 0.3f * FMath::Clamp(Flat, 0.f, 1.f);
	const float L1 = Fbm(X, Y, 1.0 / 420.0, 3, Seed + 134u) * 20.f;
	const float L2 = (Ridged(X, Y, 1.0 / 240.0, 2, Seed + 135u) - 0.35f) * 8.5f;
	const float L4 = (Ridged(X, Y, 1.0 / 95.0, 2, Seed + 137u) - 0.4f) * 2.2f;
	const float L3 = bDetail ? Fbm(X, Y, 1.0 / 30.0, 2, Seed + 136u) * 1.1f : 0.f;
	return K * (R1 + R2 + R3) + K2 * (L1 + L2 + L3 + L4);
}

// ------------------------------------------------------------------------------------------------ rivers, lakes, roads, towns
float FRDWildWorld::Feature(double X, double Y, float H, FRDWSample* Out) const
{
	const FVector2D P(X, Y);
	float Water = -1e9f; int32 Kind = 0; float Road = 0.f; float Cobble = 0.f;
	const FIntPoint Hc(FMath::FloorToInt(X / HashM), FMath::FloorToInt(Y / HashM));
	// lakes made at Init
	for (auto It = LakeHash.CreateConstKeyIterator(Hc); It; ++It)
	{
		const FLake& L = Lakes[It.Value()];
		const double D = FVector2D::Distance(P, L.C);
		const float Ang = FMath::Atan2((float)(Y - L.C.Y), (float)(X - L.C.X));
		const float Rr = L.R * (0.78f + 0.36f * (0.5f + 0.5f * Perlin(FMath::Cos(Ang) * 1.7 + L.Shape % 97, FMath::Sin(Ang) * 1.7, L.Shape)));
		if (D > Rr + RDWLakeBankM) continue;
		if (D < Rr) { H = FMath::Min(H, L.Level - L.Depth * (1.f - FMath::Square((float)D / Rr)) - 0.4f); }
		else
		{
			// (the bank: 12 degrees up from the water, whole for 30 m, let go of by RDWLakeBankM. The user's of 2026-11-08 (a
			// sheer wall out in the wilds): held whole to 120 m and dropped there, a lake among hills or mountains stood in a
			// pit with walls of 20 to 160 m round it)
			const float Hb = L.Level - 0.4f + (float)(D - Rr) * 0.22f;
			if (H > Hb) H = FMath::Lerp(H, Hb, 1.f - RDWSmooth(Rr + 30.f, Rr + (float)RDWLakeBankM, (float)D));
		}
		if (D < Rr + 30.0 && H < L.Level) { Water = L.Level; Kind = L.Kind; }
	}
	// ponds and hot springs (made at Init, hashed as the lakes)
	for (auto It = PondHash.CreateConstKeyIterator(Hc); It; ++It)
	{
		const FLake& L = Ponds[It.Value()];
		{
			const double D = FVector2D::Distance(P, L.C);
			const float Rr = L.R * (0.8f + 0.3f * (0.5f + 0.5f * Perlin(X / 37.0, Y / 37.0, L.Shape)));
			if (D > Rr + RDWPondBankM) continue;
			if (D < Rr) H = FMath::Min(H, L.Level - L.Depth * (1.f - FMath::Square((float)D / Rr)) - 0.25f);
			else
			{
				// (as a lake's bank: whole for 6 m, let go of by RDWPondBankM; it was dropped at 40 m)
				const float Hb = L.Level - 0.25f + (float)(D - Rr) * 0.3f;
				if (H > Hb) H = FMath::Lerp(H, Hb, 1.f - RDWSmooth(Rr + 6.f, Rr + (float)RDWPondBankM, (float)D));
			}
			if (D < Rr + 6.0 && H < L.Level) { Water = L.Level; Kind = L.Kind; }
		}
	}
	// the dry channels (the list of 2026-11-14: "arroyos and dry creek beds that cut hidden paths below the horizon"): cut down into
	// the land by their depth, a flat bed to Wall's share of the half width, then the wall up to the ground; eased in over the first
	// and last 12 % of their length
	float Chan = 0.f; int32 ChanKind = -1;
	{
		double Cd = 0, Ca = 0;
		const int32 Ci = NearestChannel(X, Y, Cd, Ca);
		if (Ci >= 0)
		{
			const FChannel& Ch = Channels[Ci];
			const float T = (float)Cd / FMath::Max(Ch.W * 0.5f, 0.5f);
			if (T < 1.f)
			{
				const float F = 1.f - RDWSmooth(FMath::Clamp(Ch.Wall, 0.f, 1.f) * 0.8f, 1.f, T);
				const float Ta = RDWSmooth(0.f, 0.12f, (float)Ca) * RDWSmooth(0.f, 0.12f, 1.f - (float)Ca);
				H -= Ch.D * F * Ta;
				Chan = F * Ta; ChanKind = Ch.Kind;
			}
		}
	}
	// rivers and roads: the nearest segment of each
	double Rd = 1e18, Rt = 0; int32 Ri = -1, Rs = -1;
	// (the nearest minor road and the nearest major road apart (the fourteenth phase): where a minor road joins or runs by a major
	// one, the major one's bed and cobbles are laid over the minor one's, not lost to whichever middle is nearer)
	double Dd = 1e18, Dt = 0; int32 Di = -1, Ds = -1;
	double Md = 1e18, Mt = 0; int32 Mi = -1, Ms = -1;
	for (auto It = SegHash.CreateConstKeyIterator(Hc); It; ++It)
	{
		const uint32 V = It.Value();
		const bool bRoad = (V >> 31) != 0; const int32 I = (V >> 16) & 0x7FFF, Sg = V & 0xFFFF;
		const TArray<FVector2D>& Pts = bRoad ? Roads[I].P : Rivers[I].P;
		double T; const double D = RDWSegDist(P, Pts[Sg], Pts[Sg + 1], T);
		if (bRoad) { if (Roads[I].bTrack) { if (D < Dd) { Dd = D; Dt = T; Di = I; Ds = Sg; } } else if (D < Md) { Md = D; Mt = T; Mi = I; Ms = Sg; } }
		else if (D < Rd) { Rd = D; Rt = T; Ri = I; Rs = Sg; }
	}
	if (Ri >= 0)
	{
		const FRiver& R = Rivers[Ri];
		const float S = FMath::Lerp(R.S[Rs], R.S[Rs + 1], (float)Rt), Wd = FMath::Lerp(R.W[Rs], R.W[Rs + 1], (float)Rt);
		const float Half = Wd * 0.5f, Bank = Wd * 1.5f + 60.f;
		const float D = (float)Rd;
		if (D < Half) { H = FMath::Min(H, S - (1.2f + Wd * 0.05f) * (1.f - FMath::Square(D / Half)) - 0.3f); }
		else if (D < Half + Bank)
		{
			const float Hb = S + 0.35f + (D - Half) * 0.22f;
			if (H > Hb) H = FMath::Lerp(H, Hb, 1.f - RDWSmooth(Half, Half + Bank, D));
		}
		if (D < Half + 1.5f && H < S) { Water = S; Kind = 3; }
	}
	for (int32 Pass = 0; Pass < 2; ++Pass)
	{
		const int32 Ix = Pass == 0 ? Di : Mi, Sx = Pass == 0 ? Ds : Ms;
		if (Ix < 0) continue;
		const FRoad& R = Roads[Ix];
		const float Z = FMath::Lerp(R.Z[Sx], R.Z[Sx + 1], (float)(Pass == 0 ? Dt : Mt));
		const float D = (float)(Pass == 0 ? Dd : Md);
		if (R.bTrack)
		{
			// (a minor road (the list of 2026-11-16's fourteenth phase): dirt, a cart wide, 1.7 to 2.1 m from its middle, its edges
			// ragged; its bed eased over 8 m and the height it makes up, to 45 m)
			const float Wt = 1.f - RDWSmooth(2.2f, FMath::Min(8.f + 2.f * FMath::Abs(Z - H), (float)RDWRoadBankM * 0.75f), D);
			H = FMath::Lerp(H, Z, Wt);
			Road = FMath::Max(Road, 0.95f * (1.f - RDWSmooth(1.7f + 0.4f * Perlin(X / 7.0, Y / 7.0, Seed + 72u), 2.6f, D)));
		}
		else
		{
		// (a major road (the list of 2026-11-16's fourteenth phase: "raised cobblestone"): cobbles 3.5 m either side of its middle
		// within kerbs, raised 22 cm over its bed, a dirt shoulder to 4.3-4.9 m; its bed levelled out to 14 m. Over a dip or
		// through a rise its bank widens with the height it makes up, 2.5 m a metre, to RDWRoadBankM (the user's of 2026-11-08))
		const float Wt = 1.f - RDWSmooth(4.6f, FMath::Min(14.f + 2.5f * FMath::Abs(Z - H), (float)RDWRoadBankM), D);
		H = FMath::Lerp(H, Z, Wt);
		Road = FMath::Max(Road, 1.f - RDWSmooth(4.3f + 0.6f * Perlin(X / 9.0, Y / 9.0, Seed + 71u), 5.6f, D));
		Cobble = 1.f - RDWSmooth(3.45f, 3.75f, D);
		H += 0.22f * (1.f - RDWSmooth(3.55f, 4.15f, D));
		}
		if (Road > 0.4f && Kind == 3) { Water = -1e9f; Kind = 0; }           // a ford: the road crosses dry
	}
	// the towns: their ground flat (their whole section and a margin), their region round them eased into it
	for (const FRDWildTown& T : Towns)
	{
		// (since the list of 2026-11-04 eased in over 400 to 1150 m, not 480 to 1700: the land before the gate was flat for
		// more than a kilometre)
		const double D = FVector2D::Distance(P, T.Site);
		if (D > T.EaseM) continue;
		// (the list of 2026-11-11: the port on its coast, its harbour open to the sea: its square (its section, 504 m across, and a
		// little) flat and dry, the sea round it left as it is; the land eased as every town's. Its ground is lifted after the
		// features with the sea (PortLift): here it is the town's height less the lift)
		const bool bPortHere = bPortSea && FVector2D::Distance(T.Site, PortSite) < 1.0;
		const float Dsq = (float)FMath::Max(FMath::Abs(X - T.Site.X), FMath::Abs(Y - T.Site.Y));
		float F = 1.f - RDWSmooth(400.f, T.EaseM, (float)D);
		if (bPortHere) { if (Dsq < 262.f) F = 1.f; else if (H < 2.f) F *= 1.f - RDWSmooth(262.f, 330.f, Dsq); }
		else if (H < 2.f && D > 400.0) F *= 1.f - RDWSmooth(400.f, 470.f, (float)D);
		H = FMath::Lerp(H, T.H - PortLift(X, Y), F);
		// (the road runs on up to the town's own ground, which draws it from the gate: its section is 360 to 504 m across)
		if (bPortHere ? Dsq < 262.f : D < 400.0) { Water = -1e9f; Kind = 0; }
		// (the harbour's way out: north of its quay and across its width (the port plan's harbour, RDTownPlan.cpp: frame G 0, so
		// its +X is the town's sea side) the bed 10 cm under the harbour's swum floor at the section's edge, deepening out to
		// sea, the sea's water over it; its sides eased over 14 m. The sea here is 0 before the lift, the harbour's water after it)
		if (bPortHere && X - T.Site.X > RDWPortQuayM(T.Tiles))
		{
			const float Hm = RDWPortHalfM(T.Tiles);
			const float Ws = 1.f - RDWSmooth(Hm - 2.f, Hm + 12.f, (float)FMath::Abs(Y - T.Site.Y));
			if (Ws > 0.f)
			{
				// (SwimBedMouthCm under the sea at the section's edge, under the harbour's floor since she swims there (2026-11-12:
				// the wilds' swimming floor 145 cm under the face meets the harbour's 140 cm); 0.6 m until then)
				const float Bed = -FRDWildWorld::SwimBedMouthCm / 100.f - 9.f * RDWSmooth(255.f, 700.f, (float)(X - T.Site.X));
				H = FMath::Lerp(H, FMath::Min(H, Bed), Ws);
				if (H < -0.05f) { Water = 0.f; Kind = 1; }
			}
		}
		if (D < 170.0) { Road = 0.f; Cobble = 0.f; }
	}
	// (the list of 2026-11-20's seventh phase: the villages' terraces, level ground cut into the slope (RDList15f.cpp))
	float Terr = 0.f;
	if (bTerraces15 && bTerracesReady && !bTerraceGroundOff && !FRDWNoTerrace::On())
	{
		H = ApplyTerrace(X, Y, H, Terr);
		if (Terr >= 1.f) { Water = -1e9f; Kind = 0; }
	}
	if (Out) { Out->Terrace = Terr; Out->Water = Water; Out->WaterKind = Kind; Out->Road = Road; Out->Cobble = Cobble; Out->Chan = Road > 0.3f ? 0.f : Chan; Out->ChanKind = ChanKind; }
	return H;
}

// ------------------------------------------------------------------------------------------------ the list of 2026-11-14's channels
int32 FRDWildWorld::NearestChannel(double X, double Y, double& Dist, double& Along) const
{
	if (Channels.Num() == 0) return -1;
	const FIntPoint Hc(FMath::FloorToInt(X / HashM), FMath::FloorToInt(Y / HashM));
	const FVector2D P(X, Y);
	double Best = 1e18; int32 Bi = -1;
	for (auto It = ChanHash.CreateConstKeyIterator(Hc); It; ++It)
	{
		const uint32 V = It.Value();
		const int32 I = (V >> 16) & 0xFFFF, Sg = V & 0xFFFF;
		const FChannel& C = Channels[I];
		double T; const double D = RDWSegDist(P, C.P[Sg], C.P[Sg + 1], T);
		if (D < Best) { Best = D; Bi = I; Along = (Sg + T) / FMath::Max(1, C.P.Num() - 1); }
	}
	Dist = Best;
	return Bi;
}

void FRDWildWorld::MakeChannels()
{
	// (each rule's channels: n a region cell of its biomes (a fraction a chance), each a line wandering from a point within 5 km of
	// the cell's site in 20 m steps, its way turning by a noise; it stops at water, the sea's edge and a town's level ground)
	Channels.Reset(); ChanHash.Reset(); ChannelNames.Reset();
	auto Range = [](const TMap<FString, FString>& M, const TCHAR* K, float Lo, float Hi, float U)
	{
		const FString* V = M.Find(K); if (!V) return FMath::Lerp(Lo, Hi, U);
		FString A, B; if (V->Split(TEXT("-"), &A, &B) && !A.IsEmpty()) return FMath::Lerp(FCString::Atof(*A), FCString::Atof(*B), U);
		return FCString::Atof(**V);
	};
	for (int32 Ri = 0; Ri < ChannelRules.Num(); ++Ri)
	{
		TMap<FString, FString> M;
		{ TArray<FString> Kv; ChannelRules[Ri].ParseIntoArray(Kv, TEXT(";"), true); for (const FString& Q : Kv) { FString K, V; if (Q.Split(TEXT("="), &K, &V)) M.Add(K.TrimStartAndEnd(), V.TrimStartAndEnd()); } }
		ChannelNames.Add(M.FindRef(TEXT("name")));
		TArray<FString> Bs; M.FindRef(TEXT("biomes")).ParseIntoArray(Bs, TEXT(","), true);
		TSet<int32> Want; for (FString& B : Bs) { B.TrimStartAndEndInline(); if (const int32* Bi = BiomeIndex.Find(B)) Want.Add(*Bi); }
		const float Per = M.Contains(TEXT("n")) ? FCString::Atof(*M[TEXT("n")]) : 1.f;
		const float Turn = M.Contains(TEXT("turn")) ? FCString::Atof(*M[TEXT("turn")]) : 12.f;
		for (int32 Ci = 0; Ci < CellBiome.Num(); ++Ci)
		{
			if (!Want.Contains(CellBiome[Ci])) continue;
			const uint32 Hs = Hash(Ci, Ri, Seed + 1401u);
			int32 N = FMath::FloorToInt(Per); if (Rand01(Ci, Ri, Seed + 1402u) < Per - N) ++N;
			for (int32 K = 0; K < N; ++K)
			{
				const uint32 Sk = Hs + 977u * K;
				FChannel Ch; Ch.Kind = Ri;
				Ch.W = Range(M, TEXT("w"), 8.f, 14.f, Rand01(Sk, 1, Seed)); Ch.D = Range(M, TEXT("d"), 2.f, 3.5f, Rand01(Sk, 2, Seed));
				Ch.Wall = M.Contains(TEXT("wall")) ? FCString::Atof(*M[TEXT("wall")]) : 0.5f;
				const float Len = Range(M, TEXT("len"), 600.f, 1400.f, Rand01(Sk, 3, Seed));
				const FVector2D C0 = CellSite.IsValidIndex(Ci) ? CellSite[Ci] : FVector2D::ZeroVector;
				FVector2D P = C0 + FVector2D(Rand01(Sk, 4, Seed) - 0.5, Rand01(Sk, 5, Seed) - 0.5) * 10000.0 * WorldK();          // (within its cell: PR #89's review)
				double Ang = Rand01(Sk, 6, Seed) * 2.0 * PI;
				for (double L = 0.0; L <= Len; L += 20.0)
				{
					if (Continent(P.X, P.Y) < 0.03f) break;
					double Dt; NearestTown(P.X, P.Y, Dt);
					if (Dt < 1500.0) break;
					FRDWSample S; Sample(P.X, P.Y, S, false);
					if (S.WaterKind != 0 || S.H < 3.f || !Want.Contains(S.Biome)) break;
					Ch.P.Add(P);
					Ang += FMath::DegreesToRadians(Turn) * Perlin(L / 160.0 + Sk % 101, Sk % 37, Seed + 1403u) * 2.0;
					P += FVector2D(FMath::Cos(Ang), FMath::Sin(Ang)) * 20.0;
				}
				if (Ch.P.Num() < 12) continue;
				Ch.Box = FBox2D(Ch.P);
				const int32 Idx = Channels.Add(MoveTemp(Ch));
				const FChannel& C = Channels[Idx];
				if (Idx > 0xFFFF) break;
				for (int32 Sg = 0; Sg + 1 < C.P.Num(); ++Sg)
				{
					const FBox2D Bx = FBox2D(TArray<FVector2D>{ C.P[Sg], C.P[Sg + 1] }).ExpandBy(C.W + 4.0);
					for (int32 I = FMath::FloorToInt(Bx.Min.X / HashM); I <= FMath::FloorToInt(Bx.Max.X / HashM); ++I)
						for (int32 J = FMath::FloorToInt(Bx.Min.Y / HashM); J <= FMath::FloorToInt(Bx.Max.Y / HashM); ++J) ChanHash.Add(FIntPoint(I, J), ((uint32)Idx << 16) | (uint32)Sg);
				}
			}
		}
	}
}

float FRDWildWorld::BareHeight(double X, double Y) const
{
	// (the ground with no farm on it: the land, its water, roads and towns (the farms' ridges are measured against it); the port's
	// lift (the list of 2026-11-11) on all of it)
	return Feature(X, Y, LandHeight(X, Y, true), nullptr) + PortLift(X, Y);
}

float FRDWildWorld::Height(double X, double Y) const
{
	// (the farms' weight from the same blend as the land's height (PR #30's review: a second Blend on every call))
	float Fw = 0.f;
	const float H = LandHeight(X, Y, true, nullptr, nullptr, nullptr, nullptr, &Fw);
	FRDWSample Fs;
	const float Hf = Feature(X, Y, H, &Fs);
	const float Lf = PortLift(X, Y);
	// (the farms' ridge-and-furrow, as Sample adds it: what she walks on and what the places' props stand on)
	if (Fw <= 0.2f || Fs.WaterKind != 0 || Fs.Road >= 0.1f || Hf < 0.5f || Fs.Terrace > 0.f) return Hf + Lf;
	FRDWFarm Fm; FarmAt(X, Y, Fw, Fm);
	return Hf + Lf + Fm.Ridge * (1.f - RDWSmooth(0.02f, 0.1f, Fs.Road));
}

void FRDWildWorld::Sample(double X, double Y, FRDWSample& O, bool bDetail, float PixelM) const
{
	int32 Bi[4]; float W[4]; FVector2D Si[4];
	const int32 N = Blend(X, Y, Bi, W, Si);
	float H = 0.f, Rocky = 0.f;
	FLinearColor Col(0, 0, 0, 0); float Rock = 0.f, Snow = 0.f, Sand = 0.f, Mud = 0.f, Canopy = 0.f, Lava = 0.f, Farm = 0.f, Marsh = 0.f;
	const float Nc = FMath::Clamp(0.5f + 0.38f * Fbm(X, Y, 1.0 / 380.0, bDetail ? 3 : 2, Seed + 81u) + 0.35f * Fbm(X, Y, 1.0 / 3200.0, 3, Seed + 86u), 0.f, 1.f);
	const float Macro = 0.86f + 0.28f * (0.5f + 0.5f * Fbm(X, Y, 1.0 / 9000.0, 3, Seed + 87u));
	FLinearColor RockCol(0, 0, 0, 0);
	float Strata = 0.f;
	for (int32 Q = 0; Q < N; ++Q)
	{
		const FRDWildBiome& B = Biomes[Bi[Q]];
		const float Wq = W[Q];
		H += Wq * ShapeHeight(Bi[Q], X, Y, Si[Q], bDetail);
		if (B.Swale > 0.f) H += Wq * B.Swale * Fbm(X, Y, 1.0 / 420.0, 2, Seed + 141u);          // (as LandHeight: the swales)
		if (B.Shape == ERDWShape::Canyon || B.Shape == ERDWShape::CanyonNet || B.Shape == ERDWShape::Mesa) Strata += Wq;
		if (B.Shape == ERDWShape::RockyCoast) Rocky += Wq;
		if (B.Shape == ERDWShape::Marsh) Marsh += Wq;
		if (Q == N - 1) H += LandRelief(X, Y, bDetail, Bi, W, N);
		Col += FMath::Lerp(B.ColorA, B.ColorB, Nc) * Wq;
		RockCol += B.Rock * Wq;
		Rock += B.Layers.X * Wq; Snow += FMath::Max(B.Snow, (float)B.Layers.Y) * Wq; Sand += B.Layers.Z * Wq; Mud += B.Layers.W * Wq;
		Canopy += B.Canopy * Wq;
		if (B.Name == TEXT("farms")) Farm += Wq;
		if (B.Shape == ERDWShape::Volcano)
		{
			// lava down the cone's gullies near its top; dark basalt below
			const float R = (float)FVector2D::Distance(FVector2D(X, Y), Si[Q]);
			const float Lv = RDWSmooth(0.90f, 0.96f, Ridged(X, Y, 1.0 / 520.0, 2, Seed + 82u)) * (1.f - RDWSmooth(2500.f, 5200.f, R)) * (R > 700.f ? 1.f : 0.3f);
			Lava += Lv * Wq;
		}
	}
	Col *= Macro;
	H = PortFlatten(X, Y, H);              // (as LandHeight: what is drawn and what is walked are one height)
	// (the list of 2026-11-14's sixth phase: "banded cliff walls whose colored strata read like a timeline": in the canyons and mesas
	// the rock's colour goes by height, in layers 6 to 10 m thick (each its own colour from a hash of its number, its edge eased over
	// its last fifth, warped a little so a layer is not a ruler's line), the same layer at the same height across the region)
	if (Strata > 0.f)
	{
		static const FLinearColor RDWStrataCol[6] = { FLinearColor(0.62f, 0.30f, 0.17f), FLinearColor(0.78f, 0.58f, 0.40f), FLinearColor(0.52f, 0.22f, 0.14f),
			FLinearColor(0.70f, 0.42f, 0.24f), FLinearColor(0.84f, 0.72f, 0.56f), FLinearColor(0.44f, 0.26f, 0.21f) };
		const float Hb = H + 2.5f * Fbm(X, Y, 1.0 / 700.0, 2, Seed + 150u);
		// (each 40 m block holds five layers whose thicknesses, 6 to 10 parts each from a hash, add up to the block (PR #70's review: walked
		// in their own thicknesses from each block's foot, a layer ran over the block's top and the colour jumped there, uneased); a
		// layer's colour from a hash of its number, the next layer's at a block's top the next block's first)
		constexpr int32 RDWStrataPer = 5;
		const int32 Blk = FMath::FloorToInt(Hb / 40.f);
		float Wt[RDWStrataPer], Sum = 0.f;
		for (int32 I = 0; I < RDWStrataPer; ++I) { Wt[I] = 6.f + (Hash(Blk * RDWStrataPer + I, 77, Seed + 151u) % 5); Sum += Wt[I]; }
		auto ColOf = [&](int32 L) { return RDWStrataCol[(Hash(L, 78, Seed + 151u) >> 8) % 6]; };
		float Z = Blk * 40.f; int32 Li = 0;
		while (Li < RDWStrataPer - 1 && Z + Wt[Li] * 40.f / Sum <= Hb) { Z += Wt[Li] * 40.f / Sum; ++Li; }
		const float Th = Wt[Li] * 40.f / Sum;
		const int32 L = Blk * RDWStrataPer + Li;
		const FLinearColor Band = FMath::Lerp(ColOf(L), ColOf(L + 1), RDWSmooth(0.8f, 1.f, (Hb - Z) / FMath::Max(Th, 1.f)));
		RockCol = FMath::Lerp(RockCol, Band, FMath::Clamp(Strata, 0.f, 1.f) * 0.85f);
	}
	O.Biome = N > 0 ? Bi[0] : 0; O.Biome2 = N > 1 ? Bi[1] : O.Biome; O.W1 = N > 0 ? W[0] : 1.f;
	// the coast (as LandHeight)
	const float C = Continent(X, Y);
	if (C >= 0.f) { const float Kc = FMath::Lerp(0.05f, 0.007f, FMath::Clamp(Rocky, 0.f, 1.f)); H = 1.f + (H - 1.f) * RDWSmooth(0.f, Kc, C); }
	else H = 1.f - 2.5f * RDWSmooth(0.f, 0.004f, -C) - SeaDepth * RDWSmooth(0.004f, 0.05f, -C);
	// the forest's closeness varies in patches (glades)
	Canopy *= FMath::Clamp(0.35f + 0.9f * (0.5f + 0.5f * Fbm(X, Y, 1.0 / 900.0, 3, Seed + 83u)), 0.f, 1.f);
	// the snow line falls northward and with the cold; snow sits above it
	float T, M; Climate(X, Y, T, M);
	const float Line = 260.f + 2500.f * FMath::Clamp(T, 0.f, 1.2f);
	Snow = FMath::Max(Snow, RDWSmooth(Line - 80.f, Line + 120.f, H));
	// beaches: low land at the coast
	if (C > -0.01f && C < 0.03f && H < 4.f && Rocky < 0.5f) Sand = FMath::Max(Sand, 1.f - RDWSmooth(1.5f, 4.f, H));
	// marsh pools (the marsh shapes): water in a noise's low patches
	float Water = -1e9f; int32 Kind = 0;
	if (Marsh > 0.45f)
	{
		const float Pn = Fbm(X, Y, 1.0 / 170.0, 3, Seed + 84u);
		if (Pn < -0.12f)
		{
			const float Base = H;
			H -= 0.9f * RDWSmooth(-0.12f, -0.3f, Pn) * FMath::Clamp((Marsh - 0.45f) * 4.f, 0.f, 1.f);
			if (Pn < -0.16f) { Water = Base - 0.15f; Kind = 5; Mud = FMath::Max(Mud, 0.6f); }
		}
		Mud = FMath::Max(Mud, 0.35f * Marsh);
	}
	// the features (lakes, ponds, rivers, roads, towns)
	FRDWSample Fs;
	H = Feature(X, Y, H, &Fs);
	if (Fs.WaterKind != 0) { Water = Fs.Water; Kind = Fs.WaterKind; }
	else if (Kind == 5 && H >= Water) { Water = -1e9f; Kind = 0; }
	// (the list of 2026-11-14: a dry channel's bed, sand and gravel washed down it)
	O.Chan = Fs.Chan; O.ChanKind = Fs.ChanKind; O.Terrace = Fs.Terrace;
	if (Fs.Chan > 0.f) Sand = FMath::Max(Sand, Fs.Chan * 0.85f);
	if (C < 0.f && H < 0.f && Kind == 0) { Water = 0.f; Kind = 1; }
	if (Kind == 0 && H < 0.f && C < 0.02f) { Water = 0.f; Kind = 1; }
	// (the list of 2026-11-11: round the port the land, the sea floor and the sea lifted together, the sea to its harbour's water)
	const float Lift = PortLift(X, Y);
	if (Lift > 0.f) { H += Lift; if (Kind != 0) Water += Lift; }
	// farms: the great fields (FarmAt): open fields of strips, crofts, pasture
	float Field = 0.f;
	O.FieldCell = FIntPoint(MIN_int32, MIN_int32); O.FieldCrop = -1; O.FieldAng = 0.f; O.FarmKind = 0; O.StripW = 0.f; O.StripOff = 0.f; O.FieldStage = 0;
	// (the ground before the port's lift, as Height's test (PR #50's review: one was before the lift and one after))
	if (Farm > 0.2f && Fs.Road < 0.1f && Fs.WaterKind == 0 && H - Lift >= 0.5f && Fs.Terrace <= 0.f)
	{
		FRDWFarm Fm; FarmAt(X, Y, Farm, Fm);
		// (ridge-and-furrow: "ploughing left each strip as a raised ridge" (Height adds the same: what she walks on))
		H += Fm.Ridge * (1.f - RDWSmooth(0.02f, 0.1f, Fs.Road));
		O.FarmKind = Fm.Kind;
		const FRDWildBiome* Fb = Biomes.IsValidIndex(FarmsBiome) ? &Biomes[FarmsBiome] : nullptr;
		O.FieldStage = Fm.Stage;
		// (a fallow field (soil gone to weeds) or a burned one (charred stubble) grows no crop: the ground's own colour, no rows)
		if (Fm.Stage >= 2 && Fm.Field > 0.f)
		{
			const float Fsh = Fm.Field * (1.f - RDWSmooth(25.f, 110.f, PixelM));
			// (still a field to every other rule (PR #66's review: with no share the plants, the places and the scenery took a burned
			// field for open land))
			Field = Fsh;
			const FLinearColor Sc = Fm.Stage == 3 ? FLinearColor(0.055f, 0.05f, 0.045f) : FLinearColor(0.20f, 0.17f, 0.10f);
			const FLinearColor Wc = Fm.Stage == 3 ? FLinearColor(0.10f, 0.09f, 0.07f) : FLinearColor(0.20f, 0.27f, 0.09f);
			const float Mix = 0.5f + 0.5f * Fbm(X, Y, 1.0 / 7.0, 2, Seed + 144u);
			Col = FMath::Lerp(Col, FMath::Lerp(Sc, Wc, Fm.Stage == 3 ? Mix * 0.4f : Mix * 0.6f), Fsh * 0.85f);
		}
		else if (Fb && Fb->Crops.IsValidIndex(Fm.Crop) && Fm.Field > 0.f)
		{
			// (seen from far, a pixel spans fields: their own colours fade into the region's (the list of 2026-11-07: a field
			// eases in from its edge, its colour its crop's (soil with its leaves over a share of it) drawn half way toward the
			// region's own ground, its rows the ground material's))
			Field = Fm.Field * (1.f - RDWSmooth(25.f, 110.f, PixelM));
			const FRDWildCrop& Cr = Fb->Crops[Fm.Crop];
			// (a sprouting field: its soil with a little of its leaf over it)
			FLinearColor Cc = FMath::Lerp(Cr.Soil, Cr.Leaf, FMath::Clamp(Cr.Cover, 0.f, 1.f) * (Fm.Stage == 1 ? 0.3f : 1.f));
			// (the strips: each a shade of its own ("a few very large single-crop areas cut into thin stripes"), the furrows
			// between them bare soil; both faded out where a pixel spans several)
			Cc *= FMath::Lerp(Fm.Shade, 1.f, RDWSmooth(8.f, 30.f, PixelM));
			Cc = FMath::Lerp(Cc, Cr.Soil * 0.82f, Fm.Furrow * (1.f - RDWSmooth(1.5f, 6.f, PixelM)));
			Cc *= 0.95f + 0.1f * (0.5f + 0.5f * Fbm(X, Y, 1.0 / 60.0, 2, Seed + 94u));
			Col = FMath::Lerp(Col, FMath::Lerp(Col, Cc, 0.75f), Field);
			O.FieldCrop = Fm.Crop;
			// (the field the chunk plants together: a furlong or a plot, with its great field (a cell of each scale is unique
			// within a great field's reach))
			O.FieldCell = FIntPoint(Fm.Plot.X * 1024 + (Fm.Great.X & 1023), Fm.Plot.Y * 1024 + (Fm.Great.Y & 1023));
			O.FieldAng = Fm.Ang; O.StripW = Fm.StripW; O.StripOff = Fm.StripOff;
		}
	}	// the ground's colour: rock, snow, sand, mud, lava, roads mixed over the biomes' own
	FLinearColor G = Col;
	if (Sand > 0.f) G = FMath::Lerp(G, FLinearColor(0.56f, 0.50f, 0.37f), FMath::Clamp(Sand, 0.f, 1.f));
	if (Mud > 0.f) G = FMath::Lerp(G, FLinearColor(0.16f, 0.15f, 0.10f), FMath::Clamp(Mud * 0.7f, 0.f, 1.f));
	if (Rock > 0.f) G = FMath::Lerp(G, RockCol, FMath::Clamp(Rock, 0.f, 1.f));
	// (the list of 2026-11-16's twelfth phase: no lava on a city's ground or its first slope (2.5 km), nor on a road; taken out before its
	// colour is mixed (PR #90's review: the colour stayed), and no farther (a cone beside Heaven keeps its lava))
	if (Lava > 0.f)
	{
		for (const FRDWildTown& Tw : Towns) if (Tw.EaseM > 1150.f) Lava *= RDWSmooth(2500.f, 3500.f, (float)FVector2D::Distance(FVector2D(X, Y), Tw.Site));
		Lava *= 1.f - RDWSmooth(0.02f, 0.1f, Fs.Road);
	}
	if (Lava > 0.f) G = FMath::Lerp(G, FLinearColor(0.35f, 0.07f, 0.02f), FMath::Clamp(Lava, 0.f, 1.f));
	if (Snow > 0.f) G = FMath::Lerp(G, FLinearColor(0.78f, 0.80f, 0.84f), FMath::Clamp(Snow, 0.f, 1.f));
	if (Fs.Road > 0.f) G = FMath::Lerp(G, FLinearColor(0.31f, 0.25f, 0.17f), Fs.Road);
	if (Fs.Cobble > 0.f) G = FMath::Lerp(G, FLinearColor(0.34f, 0.32f, 0.29f), Fs.Cobble);          // (the major roads' grey stone)
	if (Kind != 0)
	{
		const float Dp = FMath::Clamp((Water - H) / 6.f, 0.f, 1.f);
		const FLinearColor Wc = Kind == 6 ? FLinearColor(0.10f, 0.42f, 0.44f) : (Kind == 1 ? FLinearColor(0.05f, 0.13f, 0.20f) : FLinearColor(0.06f, 0.16f, 0.19f));
		G = FMath::Lerp(G * 0.8f, Wc, 0.45f + 0.5f * Dp);
	}
	O.H = H; O.Water = Water; O.WaterKind = Kind; O.Color = G; O.RockColor = RockCol;
	O.Rock = FMath::Clamp(Rock, 0.f, 1.f); O.Snow = FMath::Clamp(Snow, 0.f, 1.f); O.Sand = FMath::Clamp(Sand, 0.f, 1.f); O.Mud = FMath::Clamp(Mud, 0.f, 1.f);
	O.Road = Fs.Road; O.Cobble = Fs.Cobble; O.Field = Field; O.Lava = FMath::Clamp(Lava, 0.f, 1.f);
	O.Canopy = (Kind == 0 && Fs.Road < 0.2f && Field < 0.2f) ? FMath::Clamp(Canopy, 0.f, 1.f) * (1.f - O.Snow * 0.4f) : 0.f;
}

void FRDWildWorld::PlaceTowns()
{
	// Brokenspire at the middle of the frame (mid-south: 80 km from the south edge); Ashenreach in the continent's middle,
	// north of it; Graymourne on the north coast, mid-way across; Vel Morrath east, near its coast but not on it
	Towns.Reset();
	FRDWildTown B; B.Name = TEXT("Brokenspire"); B.Site = FVector2D::ZeroVector; B.Style = 0; B.Seed = 0; B.Kind = TEXT("town");
	Towns.Add(B);
	const double Mx = (Xs + Xn) * 0.5;
	FRDWildTown A; A.Name = TEXT("Ashenreach"); A.Site = FVector2D(Mx, 0.0); A.Seed = (int32)(Hash(1, 0, Seed) & 0x3FFFFFFF); A.Kind = TEXT("city");
	FRDWildTown G; G.Name = TEXT("Graymourne"); G.Seed = (int32)(Hash(2, 0, Seed) & 0x3FFFFFFF); G.Kind = TEXT("coast");
	FRDWildTown V; V.Name = TEXT("Vel Morrath"); V.Seed = (int32)(Hash(3, 0, Seed) & 0x3FFFFFFF); V.Kind = TEXT("city");
	// (the holy city (the user's of 2026-11-06): Brokenspire's size, the cathedral at its middle over the catacombs)
	V.Tiles = 168; V.Plan = 1;
	// (the forge city (the user's of 2026-11-07, docs/ashenreach.txt): Brokenspire's size, the besieged foundry at its middle over
	// The War Engine, at the edge of a burned plain)
	A.Tiles = 168; A.Plan = 2; A.Biome = TEXT("burned plain");
	// (the list of 2026-11-16's twelfth phase: "put Vel Morrath in a mountain biome", "Kethrys in glacial", "Heaven in a volcano
	// biome": their regions named as Ashenreach's, their ground eased over 5 km so the edge is a slope)
	V.Biome = TEXT("mountains"); V.EaseM = 5000.f; V.BiomeSiteM = 3500.f;
	// (the coasts are found where the land measure falls below 0, walking out from inland)
	auto Walk = [this](FVector2D From, FVector2D Dir) { FVector2D P = From; for (int32 I = 0; I < 3000; ++I) { if (Continent(P.X, P.Y) < 0.f) return P; P += Dir * 100.0; } return P; };
	const double Wq = WorldK();          // (the list of 2026-11-16: the cities at the continent's scale (half their old distances))
	const FVector2D NorthCoast = Walk(FVector2D(Mx + 60000.0 * Wq, 0.0), FVector2D(1, 0));
	// (the port (the user's of 2026-11-07, docs/graymourne.txt): Brokenspire's size, its harbour along its northern wall, so it
	// stands nearer the coast: its sea wall about 150 m from it (until then a small town 650 m inland))
	G.Tiles = 168; G.Plan = 3;
	// (the list of 2026-11-11: with its harbour open to the sea, the coast crosses its harbour: the site 150 m inside it, the
	// section's last 100 m over the sea's edge)
	auto PortAt = [&](double In) { FVector2D S = NorthCoast - FVector2D(In, 0.0); for (int32 I = 0; I < 40 && Continent(S.X, S.Y) < 0.0005f; ++I) S.X -= 100.0; return S; };
	G.Site = PortAt(bPortSea ? 150.0 : 400.0);     // (on land, a few hundred metres from the sea)
	if (bPortSea) PortSite = G.Site;
	// (the cities placed from the port go from where it stood before the list of 2026-11-11, so the open sea moves no other town
	// or road: Kethrys Spire's and Heaven's saves keep their places (PR #50's review))
	const FVector2D GraySite0 = PortAt(400.0);
	// (Vel Morrath, the user's of 2026-11-06: "to the east, but not on the coast. north east of Brokenspire": 55 km north, and
	// east toward the coast but 35 km or more inside it (until then 9 km inside it, due east))
	const FVector2D NeCoast = Walk(FVector2D(55000.0 * Wq, 30000.0 * Wq), FVector2D(0, 1));
	V.Site = FVector2D(55000.0 * Wq, FMath::Min(75000.0 * Wq, NeCoast.Y - 35000.0 * Wq));
	for (int32 I = 0; I < 60 && Continent(V.Site.X, V.Site.Y) < 0.08f; ++I) V.Site.Y -= 500.0;
	Towns.Add(A); Towns.Add(G); Towns.Add(V);
	// (Kethrys Spire, the mage city round its black tower (the list of 2026-11-08b): the road's next town after Graymourne, tiers
	// 15 to 20: north-west, about 80 km from Graymourne and well inland; walked in from the coast until the land is solid)
	FRDWildTown K; K.Name = TEXT("Kethrys Spire"); K.Seed = (int32)(Hash(4, 0, Seed) & 0x3FFFFFFF); K.Kind = TEXT("city");
	K.Tiles = 168; K.Plan = 4;
	K.Biome = TEXT("glacial"); K.EaseM = 5000.f; K.BiomeSiteM = 3500.f;
	K.Site = FVector2D(GraySite0.X - 45000.0 * WorldK(), -70000.0 * WorldK());
	{
		const FVector2D Inland = (FVector2D(Mx, -20000.0 * WorldK()) - K.Site).GetSafeNormal();
		for (int32 I = 0; I < 80 && Continent(K.Site.X, K.Site.Y) < 0.08f; ++I) K.Site += Inland * 1000.0 * WorldK();
	}
	Towns.Add(K);
	// (Heaven, the modern city in its shield (the list of 2026-11-08b): the chain's last town, tiers 20 to 25: on past Kethrys
	// Spire to the south-west, about 65 km on and well inland; walked in from the coast as Kethrys Spire)
	FRDWildTown Hv; Hv.Name = TEXT("Heaven"); Hv.Seed = (int32)(Hash(5, 0, Seed) & 0x3FFFFFFF); Hv.Kind = TEXT("city");
	Hv.Tiles = 168; Hv.Plan = 5;
	Hv.Biome = TEXT("volcanoes"); Hv.EaseM = 5000.f; Hv.BiomeSiteM = 4500.f;
	Hv.Site = FVector2D(K.Site.X - 30000.0 * WorldK(), K.Site.Y - 58000.0 * WorldK());
	{
		const FVector2D Inland = (FVector2D(Mx, -20000.0 * WorldK()) - Hv.Site).GetSafeNormal();
		for (int32 I = 0; I < 120 && Continent(Hv.Site.X, Hv.Site.Y) < 0.08f; ++I) Hv.Site += Inland * 1000.0 * WorldK();
	}
	Towns.Add(Hv);
}

void FRDWildWorld::MakeRivers()
{
	Rivers.Reset();
	// (each town's own easing, or R: water inside a wide easing would stand over or under the ground eased round it (PR #90's review))
	auto TownNear = [this](const FVector2D& P, double R) { for (const FRDWildTown& T : Towns) if (FVector2D::Distance(P, T.Site) < FMath::Max(R, (double)T.EaseM + 500.0)) return true; return false; };
	// sources: high, wet regions' cells
	TArray<FVector2D> Sources;
	for (int32 K = 0; K < CellBiome.Num(); ++K)
	{
		const FString& N = Biomes[CellBiome[K]].Name;
		const bool bHigh = N.Contains(TEXT("mountain")) || N == TEXT("glacial") || N == TEXT("hills") || N == TEXT("highland moorland") || N.Contains(TEXT("pine")) || N == TEXT("taigas") || N.Contains(TEXT("forest"));
		if (!bHigh) continue;
		const FVector2D S = CellSite[K];
		float T, M; Climate(S.X, S.Y, T, M);
		if (M < 0.42f || Continent(S.X, S.Y) < 0.1f) continue;
		if (Rand01(K, 7, Seed + 91u) > 0.55f) continue;
		Sources.Add(S + FVector2D((Rand01(K, 8, Seed + 92u) - 0.5) * 6000.0, (Rand01(K, 9, Seed + 93u) - 0.5) * 6000.0) * WorldK());
	}
	const double Step = 300.0;
	for (int32 Si = 0; Si < Sources.Num() && Rivers.Num() < 60; ++Si)
	{
		FRiver R;
		FVector2D P = Sources[Si];
		float H = LandHeight(P.X, P.Y, false);
		float Ang = Rand01(Si, 3, Seed + 94u) * 2.f * PI;
		float S = H - 1.0f;
		bool bEnd = false; int32 Joined = -1; float Climb = 0.f;
		for (int32 I = 0; I < 900 && !bEnd; ++I)
		{
			R.P.Add(P); R.S.Add(S); R.W.Add(FMath::Min(5.f + I * 0.09f, 42.f));
			// the lowest of seven ways ahead (a little inertia), away from the towns
			float Bh = 1e9f, Ba = Ang; FVector2D Bp = P;
			for (int32 Q = -3; Q <= 3; ++Q)
			{
				const float A = Ang + Q * 0.35f;
				const FVector2D Qp = P + FVector2D(FMath::Cos(A), FMath::Sin(A)) * Step;
				float Qh = LandHeight(Qp.X, Qp.Y, false) + FMath::Abs(Q) * 0.6f + 160.f * Continent(Qp.X, Qp.Y);
				if (TownNear(Qp, 2200.0)) Qh += 400.f;
				if (Qh < Bh) { Bh = Qh; Ba = A; Bp = Qp; }
			}
			const float Hq = LandHeight(Bp.X, Bp.Y, false);
			Climb = Hq > H ? Climb + (Hq - H) : FMath::Max(0.f, Climb - (H - Hq) * 0.5f);
			if (Climb > 45.f && I > 6)
			{
				// a hollow: the river ends in a lake there (unless the sea is close)
				FLake L; L.C = P; L.R = 350.f + 900.f * Rand01(Si, 11, Seed + 95u); L.Kind = 2; L.Shape = Hash(Si, 12, Seed);
				Lakes.Add(L);
				bEnd = true; break;
			}
			Ang = Ba; P = Bp; H = Hq;
			// the water's surface only falls; never above the banks either side
			const FVector2D Sd(-FMath::Sin(Ang), FMath::Cos(Ang));
			const float Hl = LandHeight(P.X + Sd.X * 40.0, P.Y + Sd.Y * 40.0, false), Hr = LandHeight(P.X - Sd.X * 40.0, P.Y - Sd.Y * 40.0, false);
			S = FMath::Min3(S - 0.03f, H - 1.0f, FMath::Min(Hl, Hr) - 0.4f);
			if (Continent(P.X, P.Y) < -0.003f || S < -1.f) { R.P.Add(P); R.S.Add(FMath::Min(S, -0.5f)); R.W.Add(float(R.W.Last())); bEnd = true; break; }
			// meeting another river: join it and stop
			for (int32 Oi = 0; Oi < Rivers.Num() && Joined < 0; ++Oi)
			{
				const FRiver& O = Rivers[Oi];
				if (!O.Box.ExpandBy(300.0).IsInside(P)) continue;
				for (int32 Pi = 0; Pi < O.P.Num(); Pi += 2)
					if (FVector2D::DistSquared(O.P[Pi], P) < 280.0 * 280.0) { R.P.Add(O.P[Pi]); R.S.Add(FMath::Min(S, O.S[Pi])); R.W.Add(float(R.W.Last())); Joined = Oi; break; }
			}
			if (Joined >= 0) bEnd = true;
		}
		if (R.P.Num() < 25) continue;
		// smoothed (two Chaikin passes) and given meanders along its length
		for (int32 Pass = 0; Pass < 2; ++Pass)
		{
			FRiver Q; Q.P.Add(R.P[0]); Q.S.Add(R.S[0]); Q.W.Add(R.W[0]);
			for (int32 I = 0; I + 1 < R.P.Num(); ++I)
			{
				Q.P.Add(R.P[I] * 0.75 + R.P[I + 1] * 0.25); Q.S.Add(R.S[I] * 0.75f + R.S[I + 1] * 0.25f); Q.W.Add(R.W[I] * 0.75f + R.W[I + 1] * 0.25f);
				Q.P.Add(R.P[I] * 0.25 + R.P[I + 1] * 0.75); Q.S.Add(R.S[I] * 0.25f + R.S[I + 1] * 0.75f); Q.W.Add(R.W[I] * 0.25f + R.W[I + 1] * 0.75f);
			}
			Q.P.Add(R.P.Last()); Q.S.Add(R.S.Last()); Q.W.Add(R.W.Last());
			R = MoveTemp(Q);
		}
		for (int32 I = 1; I + 1 < R.P.Num(); ++I)
		{
			const FVector2D D = (R.P[I + 1] - R.P[I - 1]).GetSafeNormal();
			const float Off = 70.f * Perlin(I * 0.045, Si * 3.1, Seed + 96u) * FMath::Min(1.f, FMath::Min(I, R.P.Num() - 1 - I) / 12.f);
			R.P[I] += FVector2D(-D.Y, D.X) * Off;
		}
		R.Box = FBox2D(R.P);
		Rivers.Add(MoveTemp(R));
	}
}

void FRDWildWorld::MakeLakes()
{
	// lakes in wet, low regions (rivers' hollows add theirs): their level below every point of their rim
	for (int32 K = 0; K < CellBiome.Num(); ++K)
	{
		const FString& N = Biomes[CellBiome[K]].Name;
		const bool bLow = N == TEXT("plains") || N == TEXT("grasslands") || N == TEXT("meadows") || N.Contains(TEXT("forest")) || N == TEXT("tundras") || N == TEXT("taigas") || N == TEXT("highland moorland") || N == TEXT("wetlands") || N == TEXT("temperate aspen") || N == TEXT("glacial");
		if (!bLow) continue;
		const FVector2D S = CellSite[K];
		float T, M; Climate(S.X, S.Y, T, M);
		if (M < 0.5f || Rand01(K, 21, Seed + 97u) > 0.42f) continue;
		FLake L; L.C = S + FVector2D((Rand01(K, 22, Seed) - 0.5) * 7000.0, (Rand01(K, 23, Seed) - 0.5) * 7000.0) * WorldK();
		L.R = 450.f + 1900.f * Rand01(K, 24, Seed); L.Kind = 2; L.Shape = Hash(K, 25, Seed);
		Lakes.Add(L);
	}
	TArray<FLake> Kept;
	for (FLake& L : Lakes)
	{
		bool bBad = Continent(L.C.X, L.C.Y) < 0.04f;
		for (const FRDWildTown& T : Towns) if (FVector2D::Distance(T.Site, L.C) < L.R + FMath::Max(2600.0, (double)T.EaseM + 500.0)) bBad = true;
		for (const FLake& O : Kept) if (FVector2D::Distance(O.C, L.C) < O.R + L.R + 300.0) bBad = true;
		if (bBad) continue;
		float Rim = 1e9f;
		for (int32 A = 0; A < 24; ++A)
		{
			const float Ang = A * (2.f * PI / 24.f);
			Rim = FMath::Min(Rim, LandHeight(L.C.X + FMath::Cos(Ang) * L.R * 1.15, L.C.Y + FMath::Sin(Ang) * L.R * 1.15, false));
		}
		L.Level = Rim - 0.8f;
		if (L.Level < 2.f) continue;
		L.Depth = 4.f + L.R * 0.006f;
		Kept.Add(L);
	}
	Lakes = MoveTemp(Kept);
}

void FRDWildWorld::PondsIn(FIntPoint Cell, TArray<FLake>& Out) const
{
	const double Cx = Xs + (Cell.X + 0.5) * PondCellM, Cy = Yw + (Cell.Y + 0.5) * PondCellM;
	if (Cx < Xs || Cx > Xn || Cy < Yw || Cy > Ye) return;
	const int32 B = BiomeAt(Cx, Cy);
	if (!Biomes.IsValidIndex(B)) return;
	const FRDWildBiome& Bi = Biomes[B];
	const int32 Nponds = FMath::FloorToInt(Bi.Ponds + Rand01(Cell.X, Cell.Y, Seed + 101u));
	const int32 Nsteam = Bi.Steam > 0.f ? FMath::FloorToInt(Bi.Steam + Rand01(Cell.X, Cell.Y, Seed + 102u)) : 0;
	for (int32 I = 0; I < Nponds + Nsteam; ++I)
	{
		FLake L; L.Kind = I < Nponds ? 4 : 6;
		L.C = FVector2D(Cx + (Rand01(Cell.X * 7 + I, Cell.Y, Seed + 103u) - 0.5) * PondCellM * 0.9, Cy + (Rand01(Cell.X, Cell.Y * 7 + I, Seed + 104u) - 0.5) * PondCellM * 0.9);
		L.R = L.Kind == 6 ? 14.f + 26.f * Rand01(Cell.X + I, Cell.Y, Seed + 105u) : 22.f + 90.f * Rand01(Cell.X + I, Cell.Y, Seed + 105u);
		L.Shape = Hash(Cell.X * 31 + I, Cell.Y, Seed + 106u);
		bool bBad = Continent(L.C.X, L.C.Y) < 0.03f;
		for (const FRDWildTown& T : Towns) if (FVector2D::Distance(T.Site, L.C) < FMath::Max(1900.0, (double)T.EaseM + 300.0)) bBad = true;
		if (bBad) continue;
		float Rim = 1e9f;
		for (int32 A = 0; A < 8; ++A)
		{
			const float Ang = A * (2.f * PI / 8.f);
			Rim = FMath::Min(Rim, LandHeight(L.C.X + FMath::Cos(Ang) * L.R * 1.2, L.C.Y + FMath::Sin(Ang) * L.R * 1.2, false));
		}
		L.Level = Rim - 0.35f; L.Depth = 1.2f + L.R * 0.02f;
		if (L.Level < 1.5f) continue;
		Out.Add(L);
	}
}

void FRDWildWorld::MakeRoads()
{
	// the roads between the towns: shortest ways over a 1 km grid (slopes, heights, the sea and lakes cost), smoothed,
	// wandering a little, their surface the ground's smoothed along them
	Roads.Reset();
	const double G = 1000.0;
	const int32 Nx = FMath::CeilToInt((Xn - Xs) / G) + 1, Ny = FMath::CeilToInt((Ye - Yw) / G) + 1;
	TArray<float> Hg; Hg.SetNumUninitialized(Nx * Ny);
	TArray<uint8> Bad; Bad.SetNumZeroed(Nx * Ny);
	ParallelFor(Nx, [&](int32 I)
	{
		for (int32 J = 0; J < Ny; ++J)
		{
			const double X = Xs + I * G, Y = Yw + J * G;
			Hg[I * Ny + J] = LandHeight(X, Y, false);
			if (Continent(X, Y) < 0.01f) Bad[I * Ny + J] = 1;
		}
	});
	for (const FLake& L : Lakes)
		for (int32 I = FMath::Max(0, FMath::FloorToInt((L.C.X - L.R - Xs) / G)); I <= FMath::Min(Nx - 1, FMath::CeilToInt((L.C.X + L.R - Xs) / G)); ++I)
			for (int32 J = FMath::Max(0, FMath::FloorToInt((L.C.Y - L.R - Yw) / G)); J <= FMath::Min(Ny - 1, FMath::CeilToInt((L.C.Y + L.R - Yw) / G)); ++J)
				if (FVector2D::Distance(FVector2D(Xs + I * G, Yw + J * G), L.C) < L.R + 300.0) Bad[I * Ny + J] = 1;
	auto Node = [&](const FVector2D& P) { return FIntPoint(FMath::Clamp(FMath::RoundToInt((P.X - Xs) / G), 0, Nx - 1), FMath::Clamp(FMath::RoundToInt((P.Y - Yw) / G), 0, Ny - 1)); };
	auto AStar = [&](FIntPoint A, FIntPoint B, TArray<FIntPoint>& Path)
	{
		TArray<float> Cost; Cost.Init(1e30f, Nx * Ny);
		TArray<int32> From; From.Init(-1, Nx * Ny);
		struct FQ { float F; int32 K; bool operator<(const FQ& O) const { return F < O.F; } };
		TArray<FQ> Open;
		const int32 Ka = A.X * Ny + A.Y, Kb = B.X * Ny + B.Y;
		Cost[Ka] = 0.f; Open.HeapPush({ 0.f, Ka });
		static const int32 Dx[8] = { 1, -1, 0, 0, 1, 1, -1, -1 }, Dy[8] = { 0, 0, 1, -1, 1, -1, 1, -1 };
		int32 Iter = 0;
		while (Open.Num() && Iter++ < 400000)
		{
			FQ Q; Open.HeapPop(Q, EAllowShrinking::No);
			if (Q.K == Kb) break;
			const int32 I = Q.K / Ny, J = Q.K % Ny;
			for (int32 D = 0; D < 8; ++D)
			{
				const int32 I2 = I + Dx[D], J2 = J + Dy[D];
				if (I2 < 0 || J2 < 0 || I2 >= Nx || J2 >= Ny) continue;
				const int32 K2 = I2 * Ny + J2;
				if (Bad[K2] && K2 != Kb) continue;
				const float Len = (D < 4 ? 1.f : 1.4142f);
				const float Dh = FMath::Abs(Hg[K2] - Hg[Q.K]);
				const float C = Cost[Q.K] + Len * (1.f + 0.05f * Dh + FMath::Square(Dh / 60.f) + FMath::Max(0.f, Hg[K2] - 700.f) / 120.f);
				if (C < Cost[K2]) { Cost[K2] = C; From[K2] = Q.K; const float Hn = FMath::Sqrt((float)(FMath::Square(I2 - B.X) + FMath::Square(J2 - B.Y))); Open.HeapPush({ C + Hn, K2 }); }
			}
		}
		Path.Reset();
		for (int32 K = Kb; K >= 0; K = From[K]) { Path.Insert(FIntPoint(K / Ny, K % Ny), 0); if (K == Ka) break; }
		return Path.Num() > 1 && Path[0] == A;
	};
	auto MakeRoad = [&](FVector2D Pa, FVector2D Pb, int32 Ta, int32 Tb)
	{
		// (each end runs straight out of its town for 600 m first: from the 1 km grid's node nearest the gate (the town's own
		// middle) the road doubled back along the wall, and from the gate no road was seen ahead (the list of 2026-11-04's
		// showcase, measured on a ring round the gate))
		const FVector2D Da = (Pa - Towns[Ta].Site).GetSafeNormal(), Db = (Pb - Towns[Tb].Site).GetSafeNormal();
		const FVector2D Qa = Pa + Da * 600.0, Qb = Pb + Db * 600.0;
		TArray<FIntPoint> Path;
		if (!AStar(Node(Qa + Da * 400.0), Node(Qb + Db * 400.0), Path)) return;
		TArray<FVector2D> P; P.Add(Pa); P.Add(Pa + Da * 250.0); P.Add(Qa);
		for (int32 I = 1; I + 1 < Path.Num(); ++I) P.Add(FVector2D(Xs + Path[I].X * G, Yw + Path[I].Y * G));
		P.Add(Qb); P.Add(Pb + Db * 250.0); P.Add(Pb);
		for (int32 Pass = 0; Pass < 3; ++Pass)
		{
			TArray<FVector2D> Q; Q.Add(P[0]);
			for (int32 I = 0; I + 1 < P.Num(); ++I) { Q.Add(P[I] * 0.75 + P[I + 1] * 0.25); Q.Add(P[I] * 0.25 + P[I + 1] * 0.75); }
			Q.Add(P.Last()); P = MoveTemp(Q);
		}
		// resampled every 25 m and wandering (not near the ends)
		TArray<FVector2D> Rs; Rs.Add(P[0]);
		double Carry = 0.0;
		for (int32 I = 0; I + 1 < P.Num(); ++I)
		{
			const double L = FVector2D::Distance(P[I], P[I + 1]);
			double T = 25.0 - Carry;
			while (T <= L) { Rs.Add(FMath::Lerp(P[I], P[I + 1], T / L)); T += 25.0; }
			Carry = L - (T - 25.0);
		}
		Rs.Add(P.Last());
		for (int32 I = 1; I + 1 < Rs.Num(); ++I)
		{
			const FVector2D D = (Rs[I + 1] - Rs[I - 1]).GetSafeNormal();
			const float Ends = FMath::Min(1.f, FMath::Min(I, Rs.Num() - 1 - I) / 40.f);
			Rs[I] += FVector2D(-D.Y, D.X) * (35.f * Perlin(I * 0.03, Ta * 7.7 + Tb, Seed + 111u) * Ends);
		}
		FRoad R; R.P = MoveTemp(Rs); R.From = Ta; R.To = Tb;
		// its surface: the ground (with rivers and lakes) smoothed over ±200 m
		TArray<float> Raw; Raw.SetNum(R.P.Num());
		for (int32 I = 0; I < R.P.Num(); ++I) Raw[I] = LandHeight(R.P[I].X, R.P[I].Y, false);
		R.Z.SetNum(R.P.Num());
		for (int32 I = 0; I < R.P.Num(); ++I)
		{
			float S = 0.f; int32 C = 0;
			for (int32 K = FMath::Max(0, I - 8); K <= FMath::Min(R.P.Num() - 1, I + 8); ++K) { S += Raw[K]; ++C; }
			R.Z[I] = FMath::Max(S / C, 1.2f);
			// (eased to a town's height as its ground is (Feature: 400 to 1150 m); left at the old 480 to 1700 m when the ground's
			// was shortened, the road ran up to 12 m over or under the ground between 1.15 and 1.7 km from every town: the
			// user's of 2026-11-08, found by RDWildProbe)
			// (the target less the port's lift, as Feature's: round Graymourne the lift is added after the features, and a road eased
			// to the town's whole height stood 8 m over the ground 1 km out (the list of 2026-11-11, RDWildProbe and wild_seams.py))
			for (const FRDWildTown& T : Towns) { const double D = FVector2D::Distance(R.P[I], T.Site); if (D < 1150.0) R.Z[I] = FMath::Lerp(R.Z[I], T.H - PortLift(R.P[I].X, R.P[I].Y), 1.f - RDWSmooth(400.f, 1150.f, (float)D)); }
		}
		R.Box = FBox2D(R.P);
		Roads.Add(MoveTemp(R));
	};
	// from each town's way out (Brokenspire's gate when known, set before Init; the others' edges facing the next)
	auto Out = [&](int32 Ti, int32 To)
	{
		// (a town whose gate is known starts its roads there, just outside its section)
		if (const FVector2D* G = GateOut.Find(Ti)) return *G;
		const FVector2D D = (Towns[To].Site - Towns[Ti].Site).GetSafeNormal(); return Towns[Ti].Site + D * 300.0;
	};
	MakeRoad(Out(0, 1), Out(1, 0), 0, 1);       // Brokenspire - Ashenreach
	MakeRoad(Out(1, 2), Out(2, 1), 1, 2);       // Ashenreach - Graymourne
	MakeRoad(Out(0, 3), Out(3, 0), 0, 3);       // Brokenspire - Vel Morrath
	MakeRoad(Out(1, 3), Out(3, 1), 1, 3);       // Ashenreach - Vel Morrath
	if (Towns.Num() > 4) MakeRoad(Out(2, 4), Out(4, 2), 2, 4);       // Graymourne - Kethrys Spire (the list of 2026-11-08b)
	if (Towns.Num() > 5) MakeRoad(Out(4, 5), Out(5, 4), 4, 5);       // Kethrys Spire - Heaven
}

void FRDWildWorld::HashSegments()
{
	SegHash.Reset(); LakeHash.Reset();
	auto Add = [this](const FVector2D& A, const FVector2D& B, double Pad, uint32 V)
	{
		const int32 I0 = FMath::FloorToInt((FMath::Min(A.X, B.X) - Pad) / HashM), I1 = FMath::FloorToInt((FMath::Max(A.X, B.X) + Pad) / HashM);
		const int32 J0 = FMath::FloorToInt((FMath::Min(A.Y, B.Y) - Pad) / HashM), J1 = FMath::FloorToInt((FMath::Max(A.Y, B.Y) + Pad) / HashM);
		for (int32 I = I0; I <= I1; ++I) for (int32 J = J0; J <= J1; ++J) SegHash.Add(FIntPoint(I, J), V);
	};
	for (int32 R = 0; R < Rivers.Num(); ++R)
		for (int32 S = 0; S + 1 < Rivers[R].P.Num(); ++S) Add(Rivers[R].P[S], Rivers[R].P[S + 1], Rivers[R].W[S] * 2.0 + 70.0, ((uint32)R << 16) | (uint32)S);
	for (int32 R = 0; R < Roads.Num(); ++R)
		for (int32 S = 0; S + 1 < Roads[R].P.Num(); ++S) Add(Roads[R].P[S], Roads[R].P[S + 1], RDWRoadBankM + 2.0, 0x80000000u | ((uint32)R << 16) | (uint32)S);
	for (int32 L = 0; L < Lakes.Num(); ++L)
	{
		const FLake& K = Lakes[L]; const double Pad = K.R * 1.2 + RDWLakeBankM + 10.0;
		for (int32 I = FMath::FloorToInt((K.C.X - Pad) / HashM); I <= FMath::FloorToInt((K.C.X + Pad) / HashM); ++I)
			for (int32 J = FMath::FloorToInt((K.C.Y - Pad) / HashM); J <= FMath::FloorToInt((K.C.Y + Pad) / HashM); ++J) LakeHash.Add(FIntPoint(I, J), L);
	}
}

void FRDWildWorld::Init(uint32 InSeed, const TArray<FRDWildBiome>& InBiomes)
{
	CellM = 14000.0 * WorldK();          // (the regions' cell at the continent's scale: one size, the frame (PR #89's review))
	const double T0 = FPlatformTime::Seconds();
	Seed = InSeed; Biomes = InBiomes;
	{ FScopeLock Lk(&SiteCache->Lock); SiteCache->Cells.Reset(); }
	{ FScopeLock Lk(&PlaceCache2->Lock); PlaceCache2->Cells.Reset(); }
	{ FScopeLock Lk(&TerraceCache->Lock); TerraceCache->Cells.Reset(); }
	++TerraceGen;
	bTerracesReady = false;
	{ FScopeLock Lk(&SceneryCache->Lock); SceneryCache->Cells.Reset(); }
	{ FScopeLock Lk(&LookoutCache->Lock); LookoutCache->Cells.Reset(); }          // (the list of 2026-11-20's tenth phase)
	BiomeIndex.Reset();
	for (int32 I = 0; I < Biomes.Num(); ++I) BiomeIndex.Add(Biomes[I].Name, I);
	if (Biomes.Num() == 0) { FRDWildBiome B; B.Name = TEXT("grasslands"); Biomes.Add(B); BiomeIndex.Add(B.Name, 0); }
	{ const int32* Fi = BiomeIndex.Find(TEXT("farms")); FarmsBiome = Fi ? *Fi : -1; }
	// (the farms' crops' weights as running sums, for each field's draw; the ground's rows hold at most RDWMaxCrops crops)
	CropCum.Reset();
	if (Biomes.IsValidIndex(FarmsBiome))
	{
		float S = 0.f;
		for (const FRDWildCrop& C : Biomes[FarmsBiome].Crops) { S += FMath::Max(C.Weight, 0.f); CropCum.Add(S); }
		if (CropCum.Num() > FRDWildWorld::MaxCrops) UE_LOG(LogRDWildWorld, Error, TEXT("RDWILD %d crops in the farms: the ground's rows hold %d (the chunk's UV0 v is the crop / %d)"), CropCum.Num(), FRDWildWorld::MaxCrops, FRDWildWorld::MaxCrops);
	}
	Rivers.Reset(); Lakes.Reset(); Roads.Reset(); SegHash.Reset(); LakeHash.Reset();
	PlaceTowns();
	MakeTierChain();
	AssignBiomes();
	// the towns' ground: their region's, before the features
	// (every town's ground at Brokenspire's height above the sea: the game's z 0 for all of them, so the town code is the same
	// wherever a town stands; each one's region is eased to it over a couple of km)
	const float Hb = FMath::Clamp(LandHeight(Towns[0].Site.X, Towns[0].Site.Y, false), 12.f, 120.f);
	for (FRDWildTown& T : Towns) T.H = Hb;
	// (the list of 2026-11-11: the sea round the port at its harbour's water, 1.1 m under the town's ground)
	PortLiftM = bPortSea ? FMath::Max(0.f, Hb - 1.1f) : 0.f;
	MakeRivers();
	MakeLakes();
	// the ponds and hot springs of every 4 km cell, once
	Ponds.Reset(); PondHash.Reset();
	for (int32 I = 0; I * PondCellM < Xn - Xs; ++I)
		for (int32 J = 0; J * PondCellM < Ye - Yw; ++J) PondsIn(FIntPoint(I, J), Ponds);
	for (int32 K = 0; K < Ponds.Num(); ++K)
	{
		const FLake& P = Ponds[K]; const double Pad = P.R * 1.3 + RDWPondBankM + 10.0;
		for (int32 I = FMath::FloorToInt((P.C.X - Pad) / HashM); I <= FMath::FloorToInt((P.C.X + Pad) / HashM); ++I)
			for (int32 J = FMath::FloorToInt((P.C.Y - Pad) / HashM); J <= FMath::FloorToInt((P.C.Y + Pad) / HashM); ++J) PondHash.Add(FIntPoint(I, J), K);
	}
	// (the channels after the rivers and lakes are hashed: they stop at water (PR #65's review: cut before, they ran across rivers
	// and cut a lake's shore under its level, dry))
	HashSegments();
	MakeChannels();
	MakeRoads();
	HashSegments();
	MergeMajorRoads();
	HashSegments();
	BaseH = Towns[0].H;
	// (the quests' places before the minor roads: the villages keep 600 m from them, and every place is made once for its way)
	MakeQuestPlaces();
	MakeMinorRoads();
	MakeCrossroads();
	MakeSigns();
	bTerracesReady = true;          // (the list of 2026-11-20: the villages' terraces from here on)
	bReady = true;
	InitSeconds = FPlatformTime::Seconds() - T0;
}

// ------------------------------------------------------------------------------------------------ the quests' places
void FRDWildWorld::MakeQuestPlaces()
{
	// Brokenspire's captain's two quests (town.json): "Wolves on the Mill Road" (something killing the sheep along the mill
	// road beyond the wall: a den of ripper dogs beside the road to Ashenreach, 1.8 km or more out (as the crow flies: the road
	// leaves by the gate, whichever way that faces)) and "The Lost Patrol" (five
	// of the watch who went to the old watchtower: a ruined tower on a rise beside the road to Vel Morrath, 3 km or more out).
	// Each on dry ground that is flat enough round it; past the towns' level ground (1.15 km) and the roads' first 600 m.
	QuestPlaces.Reset();
	if (Towns.Num() == 0) return;
	const FVector2D Home = Towns[0].Site;
	auto RoadTo = [this](int32 To) -> const FRoad* { for (const FRoad& R : Roads) if (R.From == 0 && R.To == To && R.P.Num() > 2) return &R; return nullptr; };
	auto Flat = [this](const FVector2D& At, double Rm, float MaxDh)
	{
		const float H0 = Height(At.X, At.Y);
		for (int32 A = 0; A < 8; ++A)
		{
			const double Ang = A * PI / 4.0;
			const FVector2D Q = At + FVector2D(FMath::Cos(Ang), FMath::Sin(Ang)) * Rm;
			FRDWSample S; Sample(Q.X, Q.Y, S, false);
			if (S.WaterKind != 0 || FMath::Abs(S.H - H0) > MaxDh) return false;
		}
		FRDWSample S; Sample(At.X, At.Y, S, false);
		return S.WaterKind == 0 && S.H > 2.f && S.Road < 0.05f;
	};
	// a point beside a road from Brokenspire, from MinM out (as the crow flies), Off metres to a side; bHigh: the higher side
	auto Beside = [&](const FRoad* R, double MinM, double MaxM, const double* Offs, int32 NOff, double FlatR, float MaxDh, bool bHigh, FVector2D& Out, float& OutYaw)
	{
		if (!R) return false;
		for (int32 I = 1; I + 1 < R->P.Num(); ++I)
		{
			const double D = FVector2D::Distance(R->P[I], Home);
			if (D < MinM) continue;
			if (D > MaxM) break;
			const FVector2D Dir = (R->P[I + 1] - R->P[I - 1]).GetSafeNormal(), Side(-Dir.Y, Dir.X);
			float BestH = -1e9f; bool bAny = false;
			for (int32 K = 0; K < NOff; ++K)
			{
				const FVector2D Q = R->P[I] + Side * Offs[K];
				if (!Flat(Q, FlatR, MaxDh)) continue;
				const float H = Height(Q.X, Q.Y);
				if (!bAny || (bHigh && H > BestH)) { BestH = H; Out = Q; bAny = true; if (!bHigh) break; }
			}
			if (bAny && (!bHigh || BestH > Height(R->P[I].X, R->P[I].Y) + 3.f || D > MaxM - 300.0))
			{
				const FVector2D Back = R->P[I] - Out;
				OutYaw = FMath::RadiansToDegrees(FMath::Atan2(Back.Y, Back.X));      // (facing the road)
				return true;
			}
		}
		return false;
	};
	auto Add = [&](const TCHAR* Quest, const TCHAR* Kind, const TCHAR* Name, const FVector2D& At, float Yaw)
	{
		FRDWildPlace P; P.Id = QuestIdBase + QuestPlaces.Num(); P.Kind = Kind; P.Name = Name; P.Quest = Quest;
		P.At = At; P.H = Height(At.X, At.Y); P.Tier = 1; P.Biome = BiomeAt(At.X, At.Y); P.Yaw = Yaw;
		QuestPlaces.Add(P);
	};
	// (a road with no place beside it: a fixed point, held to the same ground (flat, dry, off the road: PR #25's review, the fixed
	// points had no check and could stand in a lake or on a slope), the nearest that is within 1.5 km of it and past MinD (the quest's own 1.8 / 3 km) from
	// Brokenspire (bHigh: the highest such, as the tower's rise beside its road); with none, the point as it is, logged. Facing
	// Brokenspire, the way she comes (PR #26's review: a fixed yaw faced anywhere once the point had moved)
	auto Fallback = [&](const TCHAR* Name, const FVector2D& P0, double MinD, double FlatR, float MaxDh, bool bHigh, FVector2D& Out, float& OutYaw)
	{
		Out = P0;
		// (the point itself only if it is as far out as the quest asks (PR #26's review: the search's minimum was under it); the
		// tower the highest within 600 m of the first good ground found, not anywhere in the 1.5 km)
		bool bFound = FVector2D::Distance(P0, Home) >= MinD && Flat(P0, FlatR, MaxDh);
		float BestH = bFound ? Height(P0.X, P0.Y) : -1e9f;
		double FirstR = bFound ? 0.0 : -1.0;
		for (double Rr = 100.0; Rr <= 1500.0 && (!bFound || (bHigh && Rr <= FirstR + 600.0)); Rr += 100.0)
			for (int32 A = 0; A < 16; ++A)
			{
				const double Ang = A * PI / 8.0;
				const FVector2D Q = P0 + FVector2D(FMath::Cos(Ang), FMath::Sin(Ang)) * Rr;
				if (FVector2D::Distance(Q, Home) < MinD || !Flat(Q, FlatR, MaxDh)) continue;
				const float H = Height(Q.X, Q.Y);
				if (!bFound || (bHigh && H > BestH)) { Out = Q; BestH = H; if (!bFound) FirstR = Rr; bFound = true; if (!bHigh) break; }
			}
		if (!bFound) UE_LOG(LogRDWildWorld, Warning, TEXT("RDWILD %s: no road beside, and no flat dry ground within 1.5 km of its fixed point (%.0f, %.0f): left there"), Name, P0.X, P0.Y);
		const FVector2D Back = Home - Out;
		OutYaw = FMath::RadiansToDegrees(FMath::Atan2(Back.Y, Back.X));
	};
	FVector2D At; float Yaw = 0.f;
	{
		static const double Offs[] = { 45.0, -45.0, 70.0, -70.0 };
		if (!Beside(RoadTo(1), 1800.0, 4500.0, Offs, 4, 12.0, 2.5f, false, At, Yaw)) Fallback(TEXT("The Mill Road Den"), Home + FVector2D(2000.0, 0.0), 1800.0, 12.0, 2.5f, false, At, Yaw);
		Add(TEXT("wolves"), TEXT("lair"), TEXT("The Mill Road Den"), At, Yaw);
	}
	{
		static const double Offs[] = { 180.0, -180.0, 240.0, -240.0, 120.0, -120.0 };
		if (!Beside(RoadTo(3), 3000.0, 6000.0, Offs, 6, 9.0, 2.f, true, At, Yaw)) Fallback(TEXT("The Old Watchtower"), Home + FVector2D(1900.0, 2500.0), 3000.0, 9.0, 2.f, true, At, Yaw);
		Add(TEXT("patrol"), TEXT("ruins"), TEXT("The Old Watchtower"), At, Yaw);
	}
}

const FRDWildPlace* FRDWildWorld::QuestPlaceFor(const FString& Goal) const
{
	if (!Goal.StartsWith(TEXT("wild:"))) return nullptr;
	const FString Q = Goal.Mid(5);
	for (const FRDWildPlace& P : QuestPlaces) if (P.Quest == Q) return &P;
	return nullptr;
}

// ------------------------------------------------------------------------------------------------ towns and places
int32 FRDWildWorld::NearestTown(double X, double Y, double& Dist) const
{
	int32 Best = -1; Dist = 1e18;
	for (int32 I = 0; I < Towns.Num(); ++I) { const double D = FVector2D::Distance(FVector2D(X, Y), Towns[I].Site); if (D < Dist) { Dist = D; Best = I; } }
	return Best;
}

int32 FRDWildWorld::TierAt(double X, double Y) const
{
	// (the list of 2026-11-08b: "between brokenspire and vell morrath, there should be monster encounters starting at Tier 1 to
	// Tier 5 the closer one gets to vell morrath ... from vell morrath to ashenreach ... Tier 5 - Tier 10, then from Ashenreach to
	// Graymourne ... Tier 10 Tier 15, then from Graymourne to Kethrys Spire ... Tier 15 - Tier 20, and from Kethrys Spire to
	// Heaven ... Tier 20 - Tier 25": the chain of towns and their tiers (TierChain, "<town>|<tier>"), a point's tier read along the
	// leg of the chain nearest it, from the tier of the town it leaves to the next one's. Until the list it was 1 to 5 by the
	// distance from Brokenspire, 25 km a tier. The chain's towns are found once, at Init (MakeTierChain: PR #31's review))
	const TArray<FVector2D>& At = TierSites; const TArray<float>& Ti = TierValues;
	if (At.Num() < 2) return FMath::Clamp(1 + (int32)(FVector2D(X, Y).Size() / (25000.0 * WorldK())), 1, 5);
	const FVector2D P(X, Y);
	double Best = 1e30; float Tier = Ti[0];
	for (int32 K = 0; K + 1 < At.Num(); ++K)
	{
		double T; const double D = RDWSegDist(P, At[K], At[K + 1], T);
		if (D < Best) { Best = D; Tier = FMath::Lerp(Ti[K], Ti[K + 1], (float)T); }
	}
	return FMath::Clamp(FMath::RoundToInt(Tier), 1, 99);
}

void FRDWildWorld::MakeTierChain()
{
	// (the towns of the chain that this world has, in order, with their tiers; Kethrys Spire and Heaven once they are placed)
	static const TCHAR* RDWTierNames[] = { TEXT("Brokenspire"), TEXT("Vel Morrath"), TEXT("Ashenreach"), TEXT("Graymourne"), TEXT("Kethrys Spire"), TEXT("Heaven") };
	static const float RDWTierOf[] = { 1.f, 5.f, 10.f, 15.f, 20.f, 25.f };
	TierSites.Reset(); TierValues.Reset();
	bool bHeaven = false;
	for (int32 K = 0; K < UE_ARRAY_COUNT(RDWTierNames); ++K)
		for (const FRDWildTown& T : Towns) if (T.Name == RDWTierNames[K]) { TierSites.Add(T.Site); TierValues.Add(RDWTierOf[K]); bHeaven = K == UE_ARRAY_COUNT(RDWTierNames) - 1; break; }
	// (the list of 2026-11-12's sixth phase, the game to tier 30: past Heaven the land goes on rising, from its tier at its gate to
	// the game's last (RDGameTierMax) some 40 km on; Heaven's defenders meet her there (their wild band 26-30). The way on is the
	// way from Kethrys Spire turned as little as it must for the whole leg to stay inside the continent and on its land (PR #59's
	// review: straight on it could end in the sea or past the continent's edge, where no place is laid), shorter if none does)
	if (bHeaven && TierSites.Num() >= 2)
	{
		const FVector2D H = TierSites.Last();
		const FVector2D W0 = (H - TierSites[TierSites.Num() - 2]).GetSafeNormal();
		auto LandAll = [&](const FVector2D& Way, double Len)
		{
			for (int32 I = 1; I <= 8; ++I)
			{
				const FVector2D Q = H + Way * (Len * I / 8.0);
				const double In = 4000.0 * WorldK();
				if (Q.X < Xs + In || Q.X > Xn - In || Q.Y < Yw + In || Q.Y > Ye - In || Continent(Q.X, Q.Y) < 0.08f) return false;
			}
			return true;
		};
		FVector2D Best = FVector2D::ZeroVector; double BestLen = 0.0;
		for (const double Len : { 40000.0 * WorldK(), 30000.0 * WorldK(), 20000.0 * WorldK() })
		{
			for (int32 K = 0; K <= 12 && BestLen == 0.0; ++K)
			{
				// (0, +15, -15, +30, -30 ... degrees off the way)
				const float A = FMath::DegreesToRadians(15.f * ((K + 1) / 2) * (K % 2 ? 1.f : -1.f));
				const FVector2D Way(W0.X * FMath::Cos(A) - W0.Y * FMath::Sin(A), W0.X * FMath::Sin(A) + W0.Y * FMath::Cos(A));
				if (LandAll(Way, Len)) { Best = Way; BestLen = Len; }
			}
			if (BestLen > 0.0) break;
		}
		if (BestLen > 0.0) { TierSites.Add(H + Best * BestLen); TierValues.Add((float)RDGameTierMax); }
	}
}

FString FRDWildWorld::NameFor(const FString& Kind, uint32 H) const
{
	static const TCHAR* A[] = { TEXT("Ash"), TEXT("Thorn"), TEXT("Elm"), TEXT("Raven"), TEXT("Stone"), TEXT("Mist"), TEXT("Wolf"), TEXT("Gray"), TEXT("Oak"), TEXT("Frost"), TEXT("Ember"), TEXT("Hollow"), TEXT("Briar"), TEXT("Marsh"), TEXT("Cold"), TEXT("Red"), TEXT("Iron"), TEXT("Wind"), TEXT("Barrow"), TEXT("Fen"), TEXT("Hawk"), TEXT("Moss"), TEXT("Black"), TEXT("Sun") };
	static const TCHAR* Sv[] = { TEXT("by"), TEXT("wick"), TEXT("ford"), TEXT("stead"), TEXT("ham"), TEXT("dale"), TEXT("mere"), TEXT("holt"), TEXT("ton"), TEXT("well") };
	static const TCHAR* Fam[] = { TEXT("Harlan"), TEXT("Odric"), TEXT("Maren"), TEXT("Tobin"), TEXT("Wynne"), TEXT("Garrick"), TEXT("Elsa"), TEXT("Brann"), TEXT("Ilse"), TEXT("Corwin") };
	static const TCHAR* Beast[] = { TEXT("Wolf"), TEXT("Troll"), TEXT("Spider"), TEXT("Wyrm"), TEXT("Bear"), TEXT("Ghoul"), TEXT("Boar"), TEXT("Harpy") };
	const FString Root = A[H % UE_ARRAY_COUNT(A)];
	const uint32 H2 = H / 31u;
	if (Kind == TEXT("village")) return Root + Sv[H2 % UE_ARRAY_COUNT(Sv)];
	if (Kind == TEXT("camp")) return Root + TEXT(" Camp");
	if (Kind == TEXT("house")) return FString(Fam[H2 % UE_ARRAY_COUNT(Fam)]) + ((H2 / 7) % 2 ? TEXT("'s Farmstead") : TEXT("'s Cottage"));
	if (Kind == TEXT("farmstead")) return FString(Fam[H2 % UE_ARRAY_COUNT(Fam)]) + ((H2 / 7) % 3 == 0 ? TEXT("'s Croft") : (H2 / 7) % 3 == 1 ? TEXT("'s Farm") : TEXT("'s Holding"));
	if (Kind == TEXT("spawn")) return Root + TEXT(" Hollow");
	if (Kind == TEXT("ruins")) return TEXT("Ruins of ") + Root + Sv[H2 % UE_ARRAY_COUNT(Sv)];
	if (Kind == TEXT("ritual")) return Root + ((H2 % 2) ? TEXT(" Stones") : TEXT(" Circle"));
	if (Kind == TEXT("cave")) return Root + TEXT(" Cave");
	if (Kind == TEXT("lair")) return FString(Beast[H2 % UE_ARRAY_COUNT(Beast)]) + TEXT(" Lair");
	return Root;
}

void FRDWildWorld::PlacesIn(FIntPoint Cell, TArray<FRDWildPlace>& Out) const
{
	// (made once a cell and kept (PR #91's review: every denser point, scenery and farmstead try made the cell's village and place again))
	{
		FScopeLock Lk(&PlaceCache2->Lock);
		if (const TArray<FRDWildPlace>* Got = PlaceCache2->Cells.Find(Cell)) { Out.Append(*Got); return; }
	}
	TArray<FRDWildPlace> Mine;
	PlacesInCell(Cell, Mine);
	Out.Append(Mine);
	FScopeLock Lk(&PlaceCache2->Lock);
	PlaceCache2->Cells.Add(Cell, MoveTemp(Mine));
}

int32 GRDW15Refused[3] = { 0, 0, 0 }; int32 GRDW15SlotHist[16] = {};          // (the list of 2026-11-20: the villages the terraces' rules refused, for the probe)
void FRDWildWorld::PlacesInCell(FIntPoint Cell, TArray<FRDWildPlace>& Out) const
{
	const FRDWNoTerrace NoTerrace;          // (the list of 2026-11-20: places are placed on the land without the villages' terraces)
	const double X0 = Xs + Cell.X * PlaceCellM, Y0 = Yw + Cell.Y * PlaceCellM;
	for (int32 Ti = 0; Ti < Towns.Num(); ++Ti)
	{
		const FRDWildTown& T = Towns[Ti];
		if (T.Site.X >= X0 && T.Site.X < X0 + PlaceCellM && T.Site.Y >= Y0 && T.Site.Y < Y0 + PlaceCellM)
		{
			FRDWildPlace P; P.Id = TownIdBase + Ti; P.Kind = T.Kind == TEXT("city") ? TEXT("city") : TEXT("town"); P.Name = T.Name; P.At = T.Site; P.H = T.H; P.Town = Ti; P.Tier = 1;
			Out.Add(P);
		}
	}
	for (const FRDWildPlace& Q : QuestPlaces)
		if (Q.At.X >= X0 && Q.At.X < X0 + PlaceCellM && Q.At.Y >= Y0 && Q.At.Y < Y0 + PlaceCellM) Out.Add(Q);
	if (X0 < Xs || X0 + PlaceCellM > Xn || Y0 < Yw || Y0 + PlaceCellM > Ye) return;
	// ---- the cell's village (the list of 2026-11-16: "villages can now be within 1km - 3km of each other ... a village can be near a
	// road"): in the cell's middle half (so its neighbours stand 1 to 3 km off), on all land but the arctic and the glaciers; on a road
	// it steps beside it (the road is no refusal, its middle is)
	FVector2D Village(1e18, 1e18);
	if (Rand01(Cell.X, Cell.Y, Seed + 131u) <= VillageChance)
	{
		FVector2D Va(X0 + (0.25 + 0.5 * Rand01(Cell.X, Cell.Y, Seed + 132u)) * PlaceCellM, Y0 + (0.25 + 0.5 * Rand01(Cell.X, Cell.Y, Seed + 133u)) * PlaceCellM);
		// (its houses stand on a ring 23 to 34 m out: the ring clear of the road, not only its middle (PR #91's review))
		// (the list of 2026-11-20: with terraces its houses stand on rings at 36 and 60 m, the outer reaching 68 m)
		auto RingOff = [this](const FVector2D& C)
		{
			const int32 Nq = bTerraces15 ? 12 : 8;
			for (const double Rr : bTerraces15 ? TArray<double>{ (double)VillageInnerRingM, (double)VillageOuterRingM } : TArray<double>{ 36.0 })
				for (int32 Q = 0; Q < Nq; ++Q) { FRDWSample Sr; Sample(C.X + FMath::Cos(Q * 2.0 * PI / Nq) * Rr, C.Y + FMath::Sin(Q * 2.0 * PI / Nq) * Rr, Sr, false); if (Sr.Road > 0.05f) return false; }
			return true;
		};
		// (one rule for a village's spot, the first one and any it steps to (PR #99's review: the terraces' search had copied it):
		// 2600 m from a town, 600 m from a quest's place, off a road with its ring clear of roads, dry, 2 m over the sea, off lava,
		// not in the arctic or on a glacier)
		auto Eligible = [&](const FVector2D& Q, const FRDWSample& S)
		{
			double Dq; NearestTown(Q.X, Q.Y, Dq);
			if (Dq < 2600.0 || S.Road > 0.1f || S.WaterKind != 0 || S.H < 2.f || S.Lava > 0.3f) return false;
			const FString Qb = Biomes[S.Biome].Name;
			if (Qb == TEXT("arctic regions") || Qb == TEXT("glacial")) return false;
			for (const FRDWildPlace& Qp : QuestPlaces) if (FVector2D::Distance(Qp.At, Q) < 600.0) return false;
			return RingOff(Q);
		};
		FRDWSample Sv; Sample(Va.X, Va.Y, Sv, false);
		if (Sv.Road > 0.1f || !RingOff(Va))
			for (const double Dd : { 70.0, 120.0 })
			{
				bool bMoved = false;
				for (int32 Tr = 0; Tr < 8 && !bMoved; ++Tr)
				{
					const FVector2D Q = Va + FVector2D(FMath::Cos(Tr * PI / 4.0), FMath::Sin(Tr * PI / 4.0)) * Dd;
					FRDWSample Sq; Sample(Q.X, Q.Y, Sq, false);
					if (Sq.Road <= 0.1f && RingOff(Q)) { Va = Q; Sv = Sq; bMoved = true; }
				}
				if (bMoved) break;
			}
		// (the towns and quests' distances after any step (PR #91's review))
		bool bOk = Eligible(Va, Sv);
		FRDWildPlace V;
		V.Id = ((Cell.X & 0x3FF) << 14) | ((Cell.Y & 0x3FF) << 4) | 0;
		V.Kind = RDWKinds[0]; V.At = Va;
		V.Name = NameFor(V.Kind, Hash(Cell.X, Cell.Y, Seed + 134u));
		V.Yaw = Rand01(Cell.X, Cell.Y, Seed + 135u) * 360.f;
		// (the list of 2026-11-20: on a slope its pads are cut into it. A slot whose pad would stand more than TerraceMaxStepM off the
		// land, or in water, has no house; where fewer than VillageHousesMin slots can be built it tries 70, 140 and 210 m round (8
		// ways), by the same rule, and is not placed only where none will do (refused outright, 809 of 2757 villages went). The pads
		// its test kept go into the world's record of its terraces)
		TArray<FRDWPad> Pads;
		if (bOk && bTerraces15 && VillageSlots(V, &Pads) < VillageHousesMin)
		{
			bool bFound = false;
			for (const double Dd : { 70.0, 140.0, 210.0 })
				for (int32 Tr = 0; Tr < 8 && !bFound; ++Tr)
				{
					const FVector2D Q = Va + FVector2D(FMath::Cos(Tr * PI / 4.0), FMath::Sin(Tr * PI / 4.0)) * Dd;
					FRDWSample Sq; Sample(Q.X, Q.Y, Sq, false);
					if (!Eligible(Q, Sq)) continue;
					FRDWildPlace Vq = V; Vq.At = Q;
					TArray<FRDWPad> Pq;
					if (VillageSlots(Vq, &Pq) >= VillageHousesMin) { Va = Q; Sv = Sq; V.At = Q; Pads = MoveTemp(Pq); bFound = true; }
				}
			if (!bFound) { bOk = false; FPlatformAtomics::InterlockedIncrement(&GRDW15Refused[2]); }
		}
		if (bOk)
		{
			V.H = Sv.H; V.Biome = Sv.Biome; V.Tier = TierAt(Va.X, Va.Y);
			Out.Add(V); Village = Va;
			if (bTerraces15) StoreTerraces(Cell, &V, &Pads);          // (the list of 2026-11-20: its pads as placed, in the same pass)
		}
	}
	if (bTerraces15 && Village.X > 1e17) StoreTerraces(Cell, nullptr, nullptr);          // (no village: none to hold)
	// ---- the cell's other place: 30 % of the cells (2.5 times the 4 km cells' 48 %), 48 % within 1 km of a road between towns ("add
	// more along the roads between the cities"); never a village (the village has its own draw), 400 m or more from it
	const FVector2D At(X0 + (0.2 + 0.6 * Rand01(Cell.X, Cell.Y, Seed + 122u)) * PlaceCellM, Y0 + (0.2 + 0.6 * Rand01(Cell.X, Cell.Y, Seed + 123u)) * PlaceCellM);
	const float R = Rand01(Cell.X, Cell.Y, Seed + 121u);
	if (R > PlaceChanceByRoad || (R > PlaceChance && !NearTownRoad(At, 1000.0))) return;
	if (FVector2D::Distance(At, Village) < 400.0) return;
	double Dt; NearestTown(At.X, At.Y, Dt);
	if (Dt < 2600.0) return;
	// (none on top of a quest's place)
	for (const FRDWildPlace& Q : QuestPlaces) if (FVector2D::Distance(Q.At, At) < 600.0) return;
	FRDWSample S; Sample(At.X, At.Y, S, false);
	if (S.WaterKind != 0 || S.H < 2.f || S.Road > 0.1f) return;
	const FString Bn = Biomes[S.Biome].Name;
	// the kinds a region holds, weighted
	float Wt[8] = { 0.f, 1.f, 1.2f, 1.f, 1.f, 0.7f, 0.6f, 0.8f };          // (no village: the villages have their own draw above)
	const bool bOpen = Bn == TEXT("plains") || Bn == TEXT("grasslands") || Bn == TEXT("meadows") || Bn == TEXT("farms") || Bn == TEXT("coastal regions") || Bn == TEXT("savannahs");
	const bool bHigh = Bn.Contains(TEXT("mountain")) || Bn == TEXT("hills") || Bn == TEXT("mesas") || Bn.Contains(TEXT("canyon")) || Bn == TEXT("rocky coastal") || Bn == TEXT("glacial");
	const bool bWild = Bn.Contains(TEXT("forest")) || Bn == TEXT("taigas") || Bn == TEXT("marshes") || Bn == TEXT("wetlands") || Bn.Contains(TEXT("volcan")) || Bn == TEXT("geothermal caldera");
	if (bOpen) { Wt[2] = 2.f; Wt[6] = 0.1f; }
	if (bHigh) { Wt[6] = 2.5f; Wt[7] = 1.4f; Wt[2] = 0.4f; Wt[4] = 1.4f; }
	if (bWild) { Wt[7] = 2.f; Wt[3] = 1.6f; Wt[1] = 1.4f; }
	if (Bn == TEXT("highland moorland") || Bn == TEXT("tundras") || Bn == TEXT("cold steppes")) Wt[5] = 2.2f;
	if (Bn == TEXT("arctic regions") || Bn == TEXT("glacial")) Wt[2] = 0.2f;
	float Sum = 0.f; for (float W : Wt) Sum += W;
	float Pick = Rand01(Cell.X, Cell.Y, Seed + 124u) * Sum;
	int32 K = 0; for (; K < 7; ++K) { if (Pick < Wt[K]) break; Pick -= Wt[K]; }
	FRDWildPlace P;
	P.Id = ((Cell.X & 0x3FF) << 14) | ((Cell.Y & 0x3FF) << 4) | K;
	P.Kind = RDWKinds[K]; P.At = At; P.H = S.H; P.Biome = S.Biome; P.Tier = TierAt(At.X, At.Y);
	P.Name = NameFor(P.Kind, Hash(Cell.X, Cell.Y, Seed + 125u));
	P.Yaw = Rand01(Cell.X, Cell.Y, Seed + 126u) * 360.f;
	Out.Add(P);
}

bool FRDWildWorld::NearTownRoad(const FVector2D& P, double R) const
{
	// (the road hash's cells over P +- R, the roads between towns only (not the tracks): a segment within R)
	const int32 I0 = FMath::FloorToInt((P.X - R) / HashM), I1 = FMath::FloorToInt((P.X + R) / HashM);
	const int32 J0 = FMath::FloorToInt((P.Y - R) / HashM), J1 = FMath::FloorToInt((P.Y + R) / HashM);
	TArray<uint32> Vals;
	for (int32 I = I0; I <= I1; ++I)
		for (int32 J = J0; J <= J1; ++J)
		{
			Vals.Reset(); SegHash.MultiFind(FIntPoint(I, J), Vals);
			for (const uint32 V : Vals)
			{
				if (!(V >> 31)) continue;
				const int32 Ri = (V >> 16) & 0x7FFF, Si = V & 0xFFFF;
				if (!Roads.IsValidIndex(Ri) || Roads[Ri].bTrack || !Roads[Ri].P.IsValidIndex(Si + 1)) continue;
				double T; if (RDWSegDist(P, Roads[Ri].P[Si], Roads[Ri].P[Si + 1], T) <= R) return true;
			}
		}
	return false;
}

bool FRDWildWorld::FindPlace(int32 Id, FRDWildPlace& Out) const
{
	TArray<FRDWildPlace> Ps;
	// (the list of 2026-11-20's tenth phase: a lookout, its region's cell from its id)
	if (Id >= LookoutIdBase && Id < TownIdBase) return LookoutOf(FIntPoint(((Id - LookoutIdBase) >> 10) & 0x3FF, (Id - LookoutIdBase) & 0x3FF), Out) && Out.Id == Id;
	if (Id >= QuestIdBase && Id < TownIdBase)
	{
		if (!QuestPlaces.IsValidIndex(Id - QuestIdBase)) return false;
		Out = QuestPlaces[Id - QuestIdBase]; return true;
	}
	if (Id >= TownIdBase) { const int32 Ti = Id - TownIdBase; if (!Towns.IsValidIndex(Ti)) return false; PlacesIn(PlaceCellOf(Towns[Ti].Site.X, Towns[Ti].Site.Y), Ps); }
	else if (Id >= FarmIdBase)
	{
		// (a farmstead's (the list of 2026-11-10: on the map): its great field's cell from its id, 10 bits a way, signed)
		int32 Gi = ((Id - FarmIdBase) >> 10) & 0x3FF, Gj = (Id - FarmIdBase) & 0x3FF;
		if (Gi >= 512) Gi -= 1024;
		if (Gj >= 512) Gj -= 1024;
		FarmsteadsIn(Gi * GreatFieldM, Gj * GreatFieldM, (Gi + 1) * GreatFieldM, (Gj + 1) * GreatFieldM, Ps);
	}
	else if (Id >= SiteIdBase) SitesIn(FIntPoint(((Id - SiteIdBase) >> 12) & 0xFFF, (Id - SiteIdBase) & 0xFFF), Ps);          // (a structure)
	else if (Id >= SceneryIdBase) SceneryIn(FIntPoint(((Id - SceneryIdBase) >> 10) & 0x3FF, (Id - SceneryIdBase) & 0x3FF), Ps);          // (a piece of scenery)
	else PlacesIn(FIntPoint((Id >> 14) & 0x3FF, (Id >> 4) & 0x3FF), Ps);
	for (const FRDWildPlace& P : Ps) if (P.Id == Id) { Out = P; return true; }
	return false;
}

// ================================================================================================ the list of 2026-11-12's structures
void FRDWildWorld::SitesIn(FIntPoint Cell, TArray<FRDWildPlace>& Out) const
{
	{
		FScopeLock Lk(&SiteCache->Lock);
		if (const TArray<FRDWildPlace>* Got = SiteCache->Cells.Find(Cell)) { Out.Append(*Got); return; }
	}
	TArray<FRDWildPlace> Mine;
	SitesInCell(Cell, Mine);
	Out.Append(Mine);
	FScopeLock Lk(&SiteCache->Lock);
	SiteCache->Cells.Add(Cell, MoveTemp(Mine));
}

void FRDWildWorld::SitesInCell(FIntPoint Cell, TArray<FRDWildPlace>& Out) const
{
	if (SiteKinds.Num() == 0 || Cell.X < 0 || Cell.Y < 0 || Cell.X > 0xFFF || Cell.Y > 0xFFF) return;
	const double X0 = Xs + Cell.X * SiteCellM, Y0 = Yw + Cell.Y * SiteCellM;
	if (X0 < Xs || X0 + SiteCellM > Xn || Y0 < Yw || Y0 + SiteCellM > Ye) return;
	if (Rand01(Cell.X, Cell.Y, Seed + 1201u) > SiteFill) return;
	// (up to six tries in the cell: dry, off the roads, fields and yards, 1.2 km from a town and 200 m from the captain's places,
	// and gentle: 4 m of rise over a 12 m ring at most)
	FVector2D At = FVector2D::ZeroVector; FRDWSample S; bool bOk = false;
	for (int32 Try = 0; Try < 6 && !bOk; ++Try)
	{
		At = FVector2D(X0 + (0.1 + 0.8 * Rand01(Cell.X, Cell.Y, Seed + 1202u + Try * 37u)) * SiteCellM, Y0 + (0.1 + 0.8 * Rand01(Cell.X, Cell.Y, Seed + 1203u + Try * 37u)) * SiteCellM);
		double Dt; NearestTown(At.X, At.Y, Dt);
		if (Dt < 1200.0) continue;
		bool bNear = false;
		for (const FRDWildPlace& Q : QuestPlaces) if (FVector2D::Distance(Q.At, At) < 200.0) bNear = true;
		if (bNear) continue;
		Sample(At.X, At.Y, S, false);
		if (S.WaterKind != 0 || S.H < 2.f || S.Lava > 0.3f || S.Field > 0.3f || S.FarmKind == 4 || S.Road > 0.05f) continue;
		float Lo = S.H, Hi = S.H;
		for (int32 K = 0; K < 8; ++K) { const double A = K * PI / 4.0; const float Hk = Height(At.X + FMath::Cos(A) * 12.0, At.Y + FMath::Sin(A) * 12.0); Lo = FMath::Min(Lo, Hk); Hi = FMath::Max(Hi, Hk); }
		if (Hi - Lo > 4.f) continue;
		bOk = true;
	}
	if (!bOk) return;
	// (none within 150 m of a place: its 4 km cell's and the next's near an edge)
	{
		const FIntPoint Pc = PlaceCellOf(At.X, At.Y);
		TArray<FRDWildPlace> Ps;
		for (int32 I = -1; I <= 1; ++I) for (int32 J = -1; J <= 1; ++J) PlacesIn(Pc + FIntPoint(I, J), Ps);
		for (const FRDWildPlace& P : Ps) if (FVector2D::Distance(P.At, At) < 150.0) return;
	}
	const FString Bn = Biomes.IsValidIndex(S.Biome) ? Biomes[S.Biome].Name : FString();
	auto Fits = [&](const FRDWildSiteKind& K) { return K.Biomes.Contains(TEXT("*")) || K.Biomes.Contains(Bn); };
	// (a kind of the region by weight; a water kind then looks for its water within 600 m (sixteen ways every 12 m: a river is a
	// few metres wide), its middle moved to that water's shore; with none it is a kind that wants no water (a second draw). Only
	// a water kind pays for the search: of the first version's 150 m round every spot none of the six water kinds was ever found)
	auto WaterOf = [](const FString& W) { return W == TEXT("sea") ? 1 : W == TEXT("lake") ? 2 : W == TEXT("river") ? 3 : W == TEXT("any") ? 0 : -1; };
	auto Pick = [&](bool bDryOnly, uint32 Salt)
	{
		TArray<float> Wt; float Sum = 0.f;
		for (const FRDWildSiteKind& K : SiteKinds) { const float W = Fits(K) && !(bDryOnly && WaterOf(K.NeedWater) >= 0) ? FMath::Max(K.Weight, 0.f) : 0.f; Wt.Add(W); Sum += W; }
		if (Sum <= 0.f) return -1;
		float U = Rand01(Cell.X, Cell.Y, Seed + Salt) * Sum;
		int32 Ki = 0;
		for (; Ki < Wt.Num() - 1; ++Ki) { if (Wt[Ki] > 0.f && U < Wt[Ki]) break; U -= Wt[Ki]; }
		while (Ki > 0 && Wt[Ki] <= 0.f) --Ki;
		return Wt[Ki] > 0.f ? Ki : -1;
	};
	int32 Ki = Pick(false, 1204u);
	if (Ki < 0) return;
	const FVector2D At0 = At; const FRDWSample S0 = S;
	if (const int32 Wk = WaterOf(SiteKinds[Ki].NeedWater); Wk >= 0)
	{
		double Best = 1e9; FVector2D Hit = At, Way(1, 0);
		for (int32 K = 0; K < 16; ++K)
		{
			const FVector2D D(FMath::Cos(K * PI / 8.0), FMath::Sin(K * PI / 8.0));
			for (double Rr = 12.0; Rr <= 600.0 && Rr < Best; Rr += 12.0)
			{
				const FVector2D Q = At + D * Rr;
				FRDWSample Sq; Sample(Q.X, Q.Y, Sq, false);
				if (Sq.WaterKind < 1 || Sq.WaterKind > 3 || Sq.Water < Sq.H + 0.5f || (Wk > 0 && Sq.WaterKind != Wk)) continue;
				Best = Rr; Hit = Q; Way = -D; break;
			}
		}
		// (a river or a lake the rays passed between: the nearest river line or lake within the cell's reach, from the world's own
		// hashes (sixteen rays 600 m long found a river for one site in 150 km, the dam for none))
		if (Best > 1e8 && (Wk == 0 || Wk >= 2))
		{
			const double Reach = SiteCellM * 0.5;
			const int32 I0 = FMath::FloorToInt((At.X - Reach) / HashM), I1 = FMath::FloorToInt((At.X + Reach) / HashM);
			const int32 J0 = FMath::FloorToInt((At.Y - Reach) / HashM), J1 = FMath::FloorToInt((At.Y + Reach) / HashM);
			double Nd = Reach; FVector2D Np = At; bool bFound = false;
			for (int32 I = I0; I <= I1; ++I)
				for (int32 J = J0; J <= J1; ++J)
				{
					if (Wk == 0 || Wk == 3)
						for (auto It = SegHash.CreateConstKeyIterator(FIntPoint(I, J)); It; ++It)
						{
							const uint32 V = It.Value();
							if ((V >> 31) != 0) continue;
							const int32 Ri = (V >> 16) & 0x7FFF, Sg = V & 0xFFFF;
							double T; const double D = RDWSegDist(At, Rivers[Ri].P[Sg], Rivers[Ri].P[Sg + 1], T);
							if (D < Nd) { Nd = D; Np = FMath::Lerp(Rivers[Ri].P[Sg], Rivers[Ri].P[Sg + 1], T); bFound = true; }
						}
					if (Wk == 0 || Wk == 2)
						for (auto It = LakeHash.CreateConstKeyIterator(FIntPoint(I, J)); It; ++It)
						{
							const FLake& L = Lakes[It.Value()];
							const double D = FMath::Max(0.0, FVector2D::Distance(At, L.C) - L.R * 0.6);
							// (inside its rim by 0.4 of its radius: a lake's edge wavers by its shape's noise)
							if (D < Nd) { Nd = D; Np = L.C + (At - L.C).GetSafeNormal() * L.R * 0.6; bFound = true; }
						}
				}
			if (bFound)
			{
				FRDWSample Sq; Sample(Np.X, Np.Y, Sq, false);
				if (Sq.WaterKind >= 1 && Sq.WaterKind <= 3 && Sq.Water >= Sq.H + 0.5f && (Wk == 0 || Sq.WaterKind == Wk))
				{
					Best = Nd; Hit = Np;
					Way = (At - Np).GetSafeNormal();
					if (Way.IsNearlyZero()) Way = FVector2D(FMath::Cos(Rand01(Cell.X, Cell.Y, Seed + 1207u) * 2.0 * PI), FMath::Sin(Rand01(Cell.X, Cell.Y, Seed + 1207u) * 2.0 * PI));
				}
			}
		}
		if (Best > 1e8) { Ki = Pick(true, 1206u); if (Ki < 0) return; }
		else
		{
			// (its middle on the shore: from the wet sample back toward the spot to the first ground with no water, 4 m on)
			FVector2D Q = Hit;
			for (int32 St = 0; St < 600; ++St)
			{
				Q += Way;
				FRDWSample Sq; Sample(Q.X, Q.Y, Sq, false);
				if (Sq.WaterKind == 0 || Sq.Water <= Sq.H) { At = Q + Way * 4.0; break; }
			}
			Sample(At.X, At.Y, S, false);
			// (the shore checked as the spot was: dry, off the roads and fields, clear of the towns and the places; else the spot
			// keeps a kind that wants no water)
			bool bShore = S.WaterKind == 0 && S.Lava <= 0.3f && S.Field <= 0.3f && S.FarmKind != 4 && S.Road <= 0.05f;
			if (bShore) { double Dt; NearestTown(At.X, At.Y, Dt); bShore = Dt >= 1200.0; }
			if (bShore) for (const FRDWildPlace& Qp : QuestPlaces) if (FVector2D::Distance(Qp.At, At) < 200.0) bShore = false;
			if (bShore)
			{
				const FIntPoint Pc = PlaceCellOf(At.X, At.Y);
				TArray<FRDWildPlace> Ps;
				for (int32 I = -1; I <= 1; ++I) for (int32 J = -1; J <= 1; ++J) PlacesIn(Pc + FIntPoint(I, J), Ps);
				for (const FRDWildPlace& Pq : Ps) if (FVector2D::Distance(Pq.At, At) < 150.0) bShore = false;
			}
			if (!bShore) { At = At0; S = S0; Ki = Pick(true, 1206u); if (Ki < 0) return; }
		}
	}
	FRDWildPlace P;
	P.Id = SiteIdBase + ((Cell.X & 0xFFF) << 12) + (Cell.Y & 0xFFF);
	P.Kind = TEXT("site"); P.Site = Ki; P.Name = SiteKinds[Ki].Title; P.At = At; P.H = S.H; P.Biome = S.Biome;
	P.Tier = TierAt(At.X, At.Y); P.Yaw = Rand01(Cell.X, Cell.Y, Seed + 1205u) * 360.f;
	Out.Add(P);
}

// ================================================================================================ the seventh phase's points of interest
void FRDWildWorld::PoisIn(FIntPoint Cell, TArray<FRDWildPlace>& Out) const
{
	if (PoiKinds.Num() == 0 || Cell.X < 0 || Cell.Y < 0 || Cell.X > 0xFFF || Cell.Y > 0xFFF) return;
	const double X0 = Xs + Cell.X * PoiCellM, Y0 = Yw + Cell.Y * PoiCellM;
	if (X0 < Xs || X0 + PoiCellM > Xn || Y0 < Yw || Y0 + PoiCellM > Ye) return;
	if (Rand01(Cell.X, Cell.Y, Seed + 911u) > PoiFill) return;
	// (none in or by a town, on a quest's place or a place)
	{
		double Dt; NearestTown(X0 + PoiCellM * 0.5, Y0 + PoiCellM * 0.5, Dt);
		if (Dt < 700.0) return;
	}
	// (up to four tries in the cell: the first spot on dry ground, off the fields and the farmsteads' yards, and flat enough)
	FVector2D At; FRDWSample S; bool bRoad = false, bOk = false;
	for (int32 Try = 0; Try < 4 && !bOk; ++Try)
	{
		At = FVector2D(X0 + (0.15 + 0.7 * Rand01(Cell.X, Cell.Y, Seed + 912u + Try * 31u)) * PoiCellM, Y0 + (0.15 + 0.7 * Rand01(Cell.X, Cell.Y, Seed + 913u + Try * 31u)) * PoiCellM);
		bool bNear = false;
		for (const FRDWildPlace& Q : QuestPlaces) if (FVector2D::Distance(Q.At, At) < 120.0) bNear = true;
		if (bNear) continue;
		Sample(At.X, At.Y, S, false);
		// (beside a road: stepped off it, its way down the road's falling value)
		bRoad = S.Road > 0.1f;
		if (bRoad)
		{
			float Best = S.Road; FVector2D To = At;
			for (int32 K = 0; K < 8; ++K)
			{
				const double A = K * PI / 4.0;
				const FVector2D Q = At + FVector2D(FMath::Cos(A), FMath::Sin(A)) * 12.0;
				FRDWSample Sq; Sample(Q.X, Q.Y, Sq, false);
				if (Sq.Road < Best && Sq.WaterKind == 0) { Best = Sq.Road; To = Q; }
			}
			if (Best > 0.05f) continue;
			At = To; Sample(At.X, At.Y, S, false);
		}
		if (S.WaterKind != 0 || S.H < 2.f || S.Lava > 0.3f || S.Field > 0.3f || S.FarmKind == 4) continue;
		// (flat enough to stand on: 8 m of rise over a 9 m ring at most: the mountains' slopes hold cairns and veins)
		float Lo = S.H, Hi = S.H;
		for (int32 K = 0; K < 4; ++K) { const double A = K * PI / 2.0; const float Hk = Height(At.X + FMath::Cos(A) * 9.0, At.Y + FMath::Sin(A) * 9.0); Lo = FMath::Min(Lo, Hk); Hi = FMath::Max(Hi, Hk); }
		if (Hi - Lo > 8.f) continue;
		bOk = true;
	}
	if (!bOk) return;
	// (none within 90 m of a place: its 4 km cell's and, near a cell's edge, the next's (PR #36's review))
	{
		const FIntPoint Pc = PlaceCellOf(At.X, At.Y);
		const double Cx0 = Xs + Pc.X * PlaceCellM, Cy0 = Yw + Pc.Y * PlaceCellM;
		// (the list of 2026-11-20 (PR #99's review): 120 m from a village with terraces (its outer pads and their ramps reach about 100 m))
		const double Keep = bTerraces15 ? 120.0 : 90.0;
		const int32 Dx0 = At.X - Cx0 < Keep ? -1 : 0, Dx1 = Cx0 + PlaceCellM - At.X < Keep ? 1 : 0;
		const int32 Dy0 = At.Y - Cy0 < Keep ? -1 : 0, Dy1 = Cy0 + PlaceCellM - At.Y < Keep ? 1 : 0;
		TArray<FRDWildPlace> Ps;
		for (int32 I = Dx0; I <= Dx1; ++I) for (int32 J = Dy0; J <= Dy1; ++J) PlacesIn(Pc + FIntPoint(I, J), Ps);
		for (const FRDWildPlace& P : Ps) if (FVector2D::Distance(P.At, At) < (P.Kind == TEXT("village") ? Keep : 90.0)) return;
	}
	// (the kinds of the region, beside the road or off it; landmarks in one cell in nine)
	const FString Bn = Biomes.IsValidIndex(S.Biome) ? Biomes[S.Biome].Name : FString();
	const uint32 H = Hash(Cell.X, Cell.Y, Seed + 914u);
	TArray<float> Wt; float Sum = 0.f;
	for (const FRDWildPoiKind& K : PoiKinds)
	{
		float W = 0.f;
		if (!K.bRoaming && K.bRoad == bRoad && (K.Layer < 2 || H % 9u == 0u))
			for (const FString& B : K.Biomes) if (B == TEXT("*") || B == Bn) { W = K.Weight; break; }
		Wt.Add(W); Sum += W;
	}
	if (Sum <= 0.f) return;
	float U = Rand01(Cell.X, Cell.Y, Seed + 915u) * Sum;
	int32 Ki = 0;
	for (; Ki < Wt.Num() - 1; ++Ki) { if (Wt[Ki] > 0.f && U < Wt[Ki]) break; U -= Wt[Ki]; }
	while (Ki > 0 && Wt[Ki] <= 0.f) --Ki;
	if (Wt[Ki] <= 0.f) return;
	FRDWildPlace P;
	P.Id = PoiIdBase + ((Cell.X & 0xFFF) << 12) + (Cell.Y & 0xFFF);          // (12 bits a cell: 2500 cells across)
	P.Kind = PoiKinds[Ki].Name.ToString(); P.Name = PoiKinds[Ki].Title; P.At = At; P.H = S.H; P.Biome = S.Biome; P.Poi = Ki;
	P.Tier = TierAt(At.X, At.Y); P.Yaw = Rand01(Cell.X, Cell.Y, Seed + 916u) * 360.f;
	Out.Add(P);
}

// ================================================================================================ the list of 2026-11-14's scenery
void FRDWildWorld::MakeCrossroads()
{
	// (where roads meet: a road point where another road's segment comes within 12 m and either crosses it (35 degrees or more) or
	// parts from it (400 m on or back along this road the other is 60 m off): the roads run between the towns and are smoothed, so
	// they cross rarely and part at narrow angles (the first rule, crossings only, found none within 50 km of Brokenspire). One a
	// 250 m)
	Crossroads.Reset();
	auto DistTo = [&](const FVector2D& P, int32 J)
	{
		double Best = 1e18;
		const FIntPoint Hc(FMath::FloorToInt(P.X / HashM), FMath::FloorToInt(P.Y / HashM));
		for (int32 Di = -1; Di <= 1; ++Di) for (int32 Dj = -1; Dj <= 1; ++Dj)
			for (auto It = SegHash.CreateConstKeyIterator(Hc + FIntPoint(Di, Dj)); It; ++It)
			{
				const uint32 V = It.Value();
				if ((V >> 31) == 0 || (int32)((V >> 16) & 0x7FFF) != J) continue;
				const int32 Sg = V & 0xFFFF; double T;
				Best = FMath::Min(Best, RDWSegDist(P, Roads[J].P[Sg], Roads[J].P[Sg + 1], T));
			}
		return Best;
	};
	for (int32 Ri = 0; Ri < Roads.Num(); ++Ri)
	{
		const FRoad& R = Roads[Ri];
		if (R.bTrack) continue;          // (the fourteenth phase: the crossroads stand on the major roads, where another road meets or leaves one)
		for (int32 I = 1; I + 1 < R.P.Num(); ++I)
		{
			const FVector2D P = R.P[I];
			const FVector2D Dir = (R.P[I + 1] - R.P[I - 1]).GetSafeNormal();
			const FIntPoint Hc(FMath::FloorToInt(P.X / HashM), FMath::FloorToInt(P.Y / HashM));
			bool bMeet = false;
			for (auto It = SegHash.CreateConstKeyIterator(Hc); It && !bMeet; ++It)
			{
				const uint32 V = It.Value();
				if ((V >> 31) == 0) continue;
				const int32 J = (V >> 16) & 0x7FFF, Sg = V & 0xFFFF;
				if (J == Ri) continue;
				// (PR #92's review: another major road, or a village's way that joins this one; the lanes to every place and farmstead
				// would make a crossroads every 250 m)
				if (Roads[J].bTrack && !(Roads[J].DestKind == TEXT("village") && Roads[J].Join == Ri)) continue;
				double T; const double D = RDWSegDist(P, Roads[J].P[Sg], Roads[J].P[Sg + 1], T);
				if (D > 12.0) continue;
				const FVector2D Od = (Roads[J].P[Sg + 1] - Roads[J].P[Sg]).GetSafeNormal();
				if (FMath::Abs(FVector2D::DotProduct(Dir, Od)) < FMath::Cos(FMath::DegreesToRadians(35.f))) { bMeet = true; break; }
				// (a fork: the two run together here and apart 400 m on or back (the points are 25 m apart))
				const int32 Ia = FMath::Max(0, I - 16), Ib = FMath::Min(R.P.Num() - 1, I + 16);
				if (DistTo(R.P[Ia], J) > 60.0 || DistTo(R.P[Ib], J) > 60.0) bMeet = true;
			}
			if (!bMeet) continue;
			// (a town's roads part 1.2 to 2 km from its middle (each leaves by the gate and runs 1 km out before its way is found):
			// kept from 1.1 km, past the town's level ground)
			double Dt; NearestTown(P.X, P.Y, Dt);
			if (Dt < 1100.0) continue;
			if (Crossroads.ContainsByPredicate([&](const FVector2D& Q) { return FVector2D::DistSquared(Q, P) < 1500.0 * 1500.0; })) continue;          // (1.5 km apart: the villages' ways join often)
			Crossroads.Add(P);
		}
	}
}


void FRDWildWorld::SceneryIn(FIntPoint Cell, TArray<FRDWildPlace>& Out) const
{
	{
		FScopeLock Lk(&SceneryCache->Lock);
		if (const TArray<FRDWildPlace>* Got = SceneryCache->Cells.Find(Cell)) { Out.Append(*Got); return; }
	}
	TArray<FRDWildPlace> Mine;
	SceneryInCell(Cell, Mine);
	Out.Append(Mine);
	FScopeLock Lk(&SceneryCache->Lock);
	SceneryCache->Cells.Add(Cell, MoveTemp(Mine));
}

void FRDWildWorld::SceneryInCell(FIntPoint Cell, TArray<FRDWildPlace>& Out) const
{
	if (SceneryKinds.Num() == 0 || Cell.X < 0 || Cell.Y < 0 || Cell.X > 0x3FF || Cell.Y > 0x3FF) return;
	const double X0 = Xs + Cell.X * SceneryCellM, Y0 = Yw + Cell.Y * SceneryCellM;
	if (X0 < Xs || X0 + SceneryCellM > Xn || Y0 < Yw || Y0 + SceneryCellM > Ye) return;
	if (Rand01(Cell.X, Cell.Y, Seed + 1301u) > SceneryFill) return;
	{
		double Dt; NearestTown(X0 + SceneryCellM * 0.5, Y0 + SceneryCellM * 0.5, Dt);
		if (Dt < 900.0) return;
	}
	// (its kind first, by the region at the cell's middle and the kinds' weights; a spot then as its kind asks; where none is found,
	// a kind of open ground)
	const int32 Bc = BiomeAt(X0 + SceneryCellM * 0.5, Y0 + SceneryCellM * 0.5);
	const FString Bn = BiomeName(Bc);
	// (the ponds (Want 4) and lakes (2) or both (0) whose middle lies in the cell, 60 m inside it: from every 2 km hash cell the
	// scenery cell covers (PR #66's review: the one under its middle missed a pond across a hash cell's edge))
	auto CellWaters = [&](int32 Want)
	{
		TArray<const FLake*> Ws;
		auto In = [&](const FLake& L) { return L.Kind != 6 && L.C.X >= X0 + 60.0 && L.C.X <= X0 + SceneryCellM - 60.0 && L.C.Y >= Y0 + 60.0 && L.C.Y <= Y0 + SceneryCellM - 60.0; };
		for (int32 I = FMath::FloorToInt(X0 / HashM); I <= FMath::FloorToInt((X0 + SceneryCellM) / HashM); ++I)
			for (int32 J = FMath::FloorToInt(Y0 / HashM); J <= FMath::FloorToInt((Y0 + SceneryCellM) / HashM); ++J)
			{
				if (Want != 2) for (auto It = PondHash.CreateConstKeyIterator(FIntPoint(I, J)); It; ++It) if (In(Ponds[It.Value()])) Ws.AddUnique(&Ponds[It.Value()]);
				if (Want != 4) for (auto It = LakeHash.CreateConstKeyIterator(FIntPoint(I, J)); It; ++It) if (In(Lakes[It.Value()])) Ws.AddUnique(&Lakes[It.Value()]);
			}
		return Ws;
	};
	// (the sixth phase: the dry channels' segments whose middle lies 60 m inside the cell, with their ways; found once, for the cell's
	// choice and its spot, and only where the region has a kind that stands in one)
	const bool bChanKinds = SceneryKinds.ContainsByPredicate([&](const FRDWildSceneryKind& K) { return K.Place == TEXT("channel") && (K.Biomes.Contains(TEXT("*")) || K.Biomes.Contains(Bn)); });
	TArray<TPair<FVector2D, FVector2D>> ChanCache; bool bChanCached = false;
	auto ChanPts = [&]() -> const TArray<TPair<FVector2D, FVector2D>>&
	{
		if (bChanCached) return ChanCache;
		bChanCached = true;
		for (int32 I = FMath::FloorToInt(X0 / HashM); I <= FMath::FloorToInt((X0 + SceneryCellM) / HashM); ++I)
			for (int32 J = FMath::FloorToInt(Y0 / HashM); J <= FMath::FloorToInt((Y0 + SceneryCellM) / HashM); ++J)
				for (auto It = ChanHash.CreateConstKeyIterator(FIntPoint(I, J)); It; ++It)
				{
					const FChannel& Ch = Channels[It.Value() >> 16]; const int32 Sg = It.Value() & 0xFFFF;
					if (!Ch.P.IsValidIndex(Sg + 1)) continue;
					const FVector2D M = (Ch.P[Sg] + Ch.P[Sg + 1]) * 0.5;
					if (M.X >= X0 + 60.0 && M.X < X0 + SceneryCellM - 60.0 && M.Y >= Y0 + 60.0 && M.Y < Y0 + SceneryCellM - 60.0) ChanCache.AddUnique({ M, (Ch.P[Sg + 1] - Ch.P[Sg]).GetSafeNormal() });
				}
		return ChanCache;
	};
	// (a cell that holds a crossroads takes a kind that stands at one four times in five, one a road crosses a roadside kind two in five:
	// drawn among all kinds, the 155 crossroads of a world held one of their kinds about one time in nine)
	FString Only;
	{
		bool bCross = false, bRoad = false;
		for (const FVector2D& Q : Crossroads) if (Q.X >= X0 && Q.X < X0 + SceneryCellM && Q.Y >= Y0 && Q.Y < Y0 + SceneryCellM) { bCross = true; break; }
		if (!bCross)
			for (int32 I = FMath::FloorToInt(X0 / HashM); I <= FMath::FloorToInt((X0 + SceneryCellM) / HashM) && !bRoad; ++I)
				for (int32 J = FMath::FloorToInt(Y0 / HashM); J <= FMath::FloorToInt((Y0 + SceneryCellM) / HashM) && !bRoad; ++J)
					for (auto It = SegHash.CreateConstKeyIterator(FIntPoint(I, J)); It; ++It)
					{
						const uint32 V = It.Value();
						if ((V >> 31) == 0 || Roads[(V >> 16) & 0x7FFF].bTrack) continue;          // (a major road's cell: the minor roads reach nearly every cell)
						const FVector2D M = Roads[(V >> 16) & 0x7FFF].P[V & 0xFFFF];
						if (M.X >= X0 && M.X < X0 + SceneryCellM && M.Y >= Y0 && M.Y < Y0 + SceneryCellM) { bRoad = true; break; }
					}
		// (phase 2: a cell that holds a pond's or a lake's middle takes a kind that stands by water three times in five: drawn among all
		// of a savannah's kinds, a waterhole met a pond nowhere within 150 km)
		const bool bWater = CellWaters(0).Num() > 0;
		// (the sixth phase: a cell a dry channel crosses takes a kind that stands in one three times in five (a slot canyon's); a region
		// with no such kind picks as before, and its cells do not look (PR #70's review: every cell walked the channels' hash); the same
		// segments as the spot takes (PR #70's review: a vertex in the cell whose segment's middle was not left no spot))
		const bool bChan = bChanKinds && ChanPts().Num() > 0;
		const float U = Rand01(Cell.X, Cell.Y, Seed + 1304u);
		if (bCross && U < 0.8f) Only = TEXT("crossroads");
		else if (bRoad && U < 0.4f) Only = TEXT("road");
		else if (bWater && U < 0.6f) Only = TEXT("water");
		else if (bChan && U < 0.6f) Only = TEXT("channel");
	}
	auto Pick = [&](bool bOpenOnly, uint32 Salt)
	{
		TArray<float> Wt; float Sum = 0.f;
		for (const FRDWildSceneryKind& K : SceneryKinds)
		{
			const bool bFit = (K.Biomes.Contains(TEXT("*")) || K.Biomes.Contains(Bn)) && !(bOpenOnly && (!K.Place.IsEmpty() || !K.NeedWater.IsEmpty()))
				&& (bOpenOnly || Only.IsEmpty() || (Only == TEXT("water") ? !K.NeedWater.IsEmpty() && K.NeedWater != TEXT("river") && K.NeedWater != TEXT("sea") : K.Place == Only));
			const float W = bFit ? FMath::Max(K.Weight, 0.f) : 0.f; Wt.Add(W); Sum += W;
		}
		if (Sum <= 0.f) return -1;
		float U = Rand01(Cell.X, Cell.Y, Seed + Salt) * Sum;
		for (int32 I = 0; I < Wt.Num(); ++I) { if (Wt[I] <= 0.f) continue; if (U < Wt[I]) return I; U -= Wt[I]; }
		for (int32 I = Wt.Num() - 1; I >= 0; --I) if (Wt[I] > 0.f) return I;
		return -1;
	};
	auto Fine = [&](const FVector2D& At, FRDWSample& S, float MaxRise, bool bRoadOk) -> bool
	{
		// (dry, on its region, off the fields, yards and lava, off a road unless it stands by one; gentle over a 10 m ring; clear of
		// the quests' places, the places (120 m) and the structures (150 m))
		Sample(At.X, At.Y, S, false);
		if (S.WaterKind != 0 || S.H < 2.f || S.Lava > 0.3f || S.Field > 0.3f || S.FarmKind == 4 || (!bRoadOk && S.Road > 0.05f)) return false;
		if (BiomeName(S.Biome) != Bn) return false;
		{ double Dt; NearestTown(At.X, At.Y, Dt); if (Dt < 1000.0) return false; }
		float Lo = S.H, Hi = S.H;
		for (int32 K = 0; K < 8; ++K) { const double A = K * PI / 4.0; const float Hk = Height(At.X + FMath::Cos(A) * 10.0, At.Y + FMath::Sin(A) * 10.0); Lo = FMath::Min(Lo, Hk); Hi = FMath::Max(Hi, Hk); }
		if (Hi - Lo > MaxRise) return false;
		for (const FRDWildPlace& Q : QuestPlaces) if (FVector2D::Distance(Q.At, At) < 150.0) return false;
		return true;
	};
	auto ClearOfPlaces = [&](const FVector2D& At) -> bool
	{
		const FIntPoint Pc = PlaceCellOf(At.X, At.Y);
		TArray<FRDWildPlace> Ps;
		for (int32 I = -1; I <= 1; ++I) for (int32 J = -1; J <= 1; ++J) PlacesIn(Pc + FIntPoint(I, J), Ps);
		for (const FRDWildPlace& P : Ps) if (FVector2D::Distance(P.At, At) < 120.0) return false;
		const FIntPoint Sc = SiteCellOf(At.X, At.Y);
		TArray<FRDWildPlace> Ss;
		for (int32 I = -1; I <= 1; ++I) for (int32 J = -1; J <= 1; ++J) SitesIn(Sc + FIntPoint(I, J), Ss);
		for (const FRDWildPlace& P : Ss) if (FVector2D::Distance(P.At, At) < 150.0) return false;
		// (PR #65's review: inside its own cell by 50 m, so a shore or roadside spot does not meet the next cell's scenery; 40 m from
		// the points of interest and 70 m from the farmsteads)
		if (At.X < X0 + 50.0 || At.X > X0 + SceneryCellM - 50.0 || At.Y < Y0 + 50.0 || At.Y > Y0 + SceneryCellM - 50.0) return false;
		const FIntPoint Qc = PoiCellOf(At.X, At.Y);
		TArray<FRDWildPlace> Qs;
		for (int32 I = -1; I <= 1; ++I) for (int32 J = -1; J <= 1; ++J) PoisIn(Qc + FIntPoint(I, J), Qs);
		for (const FRDWildPlace& P : Qs) if (FVector2D::Distance(P.At, At) < 40.0) return false;
		TArray<FRDWildPlace> Fs; FarmsteadsIn(At.X - 120.0, At.Y - 120.0, At.X + 120.0, At.Y + 120.0, Fs);
		for (const FRDWildPlace& P : Fs) if (FVector2D::Distance(P.At, At) < 70.0) return false;
		return true;
	};
	auto Spot = [&](int32 Ki, FVector2D& At, FRDWSample& S, float& Yaw) -> bool
	{
		const FRDWildSceneryKind& K = SceneryKinds[Ki];
		Yaw = Rand01(Cell.X, Cell.Y, Seed + 1305u) * 360.f;
		auto Try = [&](int32 T) { return FVector2D(X0 + (0.1 + 0.8 * Rand01(Cell.X, Cell.Y, Seed + 1306u + T * 41u)) * SceneryCellM, Y0 + (0.1 + 0.8 * Rand01(Cell.X, Cell.Y, Seed + 1307u + T * 41u)) * SceneryCellM); };
		if (K.Place == TEXT("crossroads"))
		{
			// (the crossroads in the cell, 9 m off the meeting, facing it)
			for (const FVector2D& Q : Crossroads)
			{
				if (Q.X < X0 || Q.X >= X0 + SceneryCellM || Q.Y < Y0 || Q.Y >= Y0 + SceneryCellM) continue;
				for (int32 A = 0; A < 8; ++A)
				{
					const double Ang = (A + 0.5) * PI / 4.0;
					const FVector2D C = Q + FVector2D(FMath::Cos(Ang), FMath::Sin(Ang)) * 9.0;
					if (!Fine(C, S, 3.f, true) || S.Road > 0.3f) continue;
					At = C; Yaw = FMath::RadiansToDegrees(Ang) + 180.f; return true;
				}
			}
			return false;
		}
		if (K.Place == TEXT("road"))
		{
			// (a point of a road through the cell, stepped 10 m off it to the side the hash picks, facing the road)
			const int32 I0 = FMath::FloorToInt(X0 / HashM), I1 = FMath::FloorToInt((X0 + SceneryCellM) / HashM);
			const int32 J0 = FMath::FloorToInt(Y0 / HashM), J1 = FMath::FloorToInt((Y0 + SceneryCellM) / HashM);
			TArray<TPair<FVector2D, FVector2D>> Pts;
			for (int32 I = I0; I <= I1; ++I)
				for (int32 J = J0; J <= J1; ++J)
					for (auto It = SegHash.CreateConstKeyIterator(FIntPoint(I, J)); It; ++It)
					{
						const uint32 V = It.Value();
						if ((V >> 31) == 0) continue;
						const FRoad& R = Roads[(V >> 16) & 0x7FFF]; const int32 Sg = V & 0xFFFF;
						const FVector2D M = (R.P[Sg] + R.P[Sg + 1]) * 0.5;
						if (M.X >= X0 && M.X < X0 + SceneryCellM && M.Y >= Y0 && M.Y < Y0 + SceneryCellM) Pts.Add({ M, (R.P[Sg + 1] - R.P[Sg]).GetSafeNormal() });
					}
			for (int32 T = 0; T < 6 && Pts.Num() > 0; ++T)
			{
				const auto& Pr = Pts[FMath::Min(Pts.Num() - 1, (int32)(Rand01(Cell.X, Cell.Y, Seed + 1308u + T * 13u) * Pts.Num()))];
				const FVector2D Side(-Pr.Value.Y, Pr.Value.X);
				const double Sd = Rand01(Cell.X, Cell.Y, Seed + 1309u + T) < 0.5 ? -1.0 : 1.0;
				const FVector2D C = Pr.Key + Side * Sd * 10.0;
				if (!Fine(C, S, 3.f, true) || S.Road > 0.2f) continue;
				At = C; Yaw = FMath::RadiansToDegrees(FMath::Atan2(-Side.Y * Sd, -Side.X * Sd)); return true;
			}
			return false;
		}
		// (the sixth phase: canyon country's places. "rim": level ground at a cliff's top, the drop 10 m or more within 22 to 35 m of it,
		// facing the drop (an overlook, a juniper on the edge, a bandits' lookout); "foot": level ground at a cliff's foot, the wall rising
		// 10 m or more within 18 to 30 m, facing the wall (petroglyphs, hanging gardens, a dwelling's alcove); the greatest of 16 tries.
		// "channel": on a dry channel's bed in the cell (a slot canyon's floor), facing along it)
		if (K.Place == TEXT("rim") || K.Place == TEXT("foot"))
		{
			const bool bRim = K.Place == TEXT("rim");
			float Best = 10.f; bool bGot = false;
			for (int32 T = 0; T < 16; ++T)
			{
				const FVector2D C = Try(T + 8);
				FRDWSample Sc;
				if (!Fine(C, Sc, 3.f, false)) continue;
				for (int32 A = 0; A < 8; ++A)
				{
					const double Ang = A * PI / 4.0;
					const FVector2D D(FMath::Cos(Ang), FMath::Sin(Ang));
					const float H1 = Height(C.X + D.X * (bRim ? 22.0 : 18.0), C.Y + D.Y * (bRim ? 22.0 : 18.0));
					const float H2 = Height(C.X + D.X * (bRim ? 35.0 : 30.0), C.Y + D.Y * (bRim ? 35.0 : 30.0));
					const float By = bRim ? Sc.H - FMath::Min(H1, H2) : FMath::Max(H1, H2) - Sc.H;
					if (By > Best) { Best = By; At = C; S = Sc; Yaw = FMath::RadiansToDegrees(Ang); bGot = true; }
				}
			}
			return bGot;
		}
		if (K.Place == TEXT("channel"))
		{
			// (a segment's middle in the cell, on its bed: the bed is no gentle ground, so Fine's other rules only: dry, on its region, off
			// the roads, fields, yards and lava and above the shore (PR #70's review: a slot canyon could be laid on a road), off the places)
			const TArray<TPair<FVector2D, FVector2D>>& Pts = ChanPts();
			// (every segment in the cell, from one the hash picks, each clear of the places there (the first test: six random tries, and
			// the places checked only after, left two channel kinds within 30 km))
			const int32 N0 = Pts.Num() > 0 ? (int32)(Rand01(Cell.X, Cell.Y, Seed + 1311u) * Pts.Num()) % Pts.Num() : 0;
			for (int32 T = 0; T < Pts.Num(); ++T)
			{
				const auto& Pr = Pts[(N0 + T) % Pts.Num()];
				FRDWSample Sc; Sample(Pr.Key.X, Pr.Key.Y, Sc, false);
				if (Sc.WaterKind != 0 || Sc.Chan <= 0.5f || BiomeName(Sc.Biome) != Bn) continue;
				if (Sc.H < 2.f || Sc.Lava > 0.3f || Sc.Field > 0.3f || Sc.FarmKind == 4 || Sc.Road > 0.05f) continue;
				{ double Dt; NearestTown(Pr.Key.X, Pr.Key.Y, Dt); if (Dt < 1000.0) continue; }
				if (QuestPlaces.ContainsByPredicate([&](const FRDWildPlace& Q) { return FVector2D::Distance(Q.At, Pr.Key) < 150.0; })) continue;
				if (!ClearOfPlaces(Pr.Key)) continue;
				At = Pr.Key; S = Sc; Yaw = FMath::RadiansToDegrees(FMath::Atan2(Pr.Value.Y, Pr.Value.X)); return true;
			}
			return false;
		}
		const FString& Wn = K.NeedWater;
		if (!Wn.IsEmpty())
		{
			// (water of its kind within 400 m of a spot (16 rays, 10 m steps; ponds and marsh pools too), its middle on the shore)
			const int32 Want = Wn == TEXT("sea") ? 1 : Wn == TEXT("lake") ? 2 : Wn == TEXT("river") ? 3 : Wn == TEXT("pond") ? 4 : 0;
			// (phase 2: the ponds and lakes whose middle lies in the cell first, walked out from their middle to the shore on 8 rays:
			// the rays from random spots found a waterhole nowhere within 150 km)
			if (Want == 0 || Want == 2 || Want == 4)
			{
				for (const FLake* L : CellWaters(Want))
				{
					FRDWSample Sm; Sample(L->C.X, L->C.Y, Sm, false);
					if (Sm.WaterKind == 0 || Sm.WaterKind == 6) continue;
					const int32 A0 = (int32)(Rand01(Cell.X, Cell.Y, Seed + 1310u) * 8.f);
					for (int32 A = 0; A < 8; ++A)
					{
						const double Ang = (A0 + A) * PI / 4.0;
						const FVector2D D(FMath::Cos(Ang), FMath::Sin(Ang));
						for (double Rr = 4.0; Rr <= L->R * 1.6 + 40.0; Rr += 2.0)
						{
							const FVector2D Q = L->C + D * Rr;
							FRDWSample Sb; Sample(Q.X, Q.Y, Sb, false);
							if (Sb.WaterKind != 0 && Sb.Water > Sb.H) continue;
							const FVector2D Sh = Q + D * 4.0;
							if (Fine(Sh, S, 3.5f, false)) { At = Sh; Yaw = FMath::RadiansToDegrees(FMath::Atan2(-D.Y, -D.X)); return true; }
							break;
						}
					}
				}
			}
			for (int32 T = 0; T < 3; ++T)
			{
				const FVector2D C = Try(T);
				for (int32 Ray = 0; Ray < 16; ++Ray)
				{
					const FVector2D D(FMath::Cos(Ray * PI / 8.0), FMath::Sin(Ray * PI / 8.0));
					for (double Rr = 10.0; Rr <= 400.0; Rr += 10.0)
					{
						FRDWSample Sq; Sample(C.X + D.X * Rr, C.Y + D.Y * Rr, Sq, false);
						if (Sq.WaterKind == 0) continue;
						if ((Want != 0 && Sq.WaterKind != Want && !(Want == 4 && Sq.WaterKind == 5)) || Sq.WaterKind == 6) break;
						// (the water's edge is shallow: step on to where it is 30 cm deep, not give the ray up there)
						if (Sq.Water < Sq.H + 0.3f) continue;
						// (back to the shore: the first dry ground, 4 m on)
						for (double Bk = Rr; Bk > 0.0; Bk -= 2.0)
						{
							const FVector2D Q = C + D * Bk;
							FRDWSample Sb; Sample(Q.X, Q.Y, Sb, false);
							if (Sb.WaterKind == 0 || Sb.Water <= Sb.H)
							{
								const FVector2D Sh = Q - D * 4.0;
								if (!Fine(Sh, S, 3.5f, false)) break;
								At = Sh; Yaw = FMath::RadiansToDegrees(FMath::Atan2(D.Y, D.X)); return true;
							}
						}
						break;
					}
				}
			}
			return false;
		}
		// (open ground: up to six tries; on a rise the highest of them, in a hollow the lowest)
		const bool bRise = K.Place == TEXT("rise"), bLow = K.Place == TEXT("low");
		bool bGot = false; float BestH = bLow ? 1e9f : -1e9f;
		for (int32 T = 0; T < 6; ++T)
		{
			const FVector2D C = Try(T);
			FRDWSample Sc;
			// (a hollow's kind wants it level, 1.5 m over its 10 m ring (phase 2: a hot spring's 0.5 m rim laid on 3 m of fall lay under
			// the uphill ground, its water unseen))
			if (!Fine(C, Sc, bRise ? 5.f : bLow ? 1.5f : 3.f, false)) continue;
			if (!bRise && !bLow) { At = C; S = Sc; return true; }
			if (bRise ? Sc.H > BestH : Sc.H < BestH) { BestH = Sc.H; At = C; S = Sc; bGot = true; }
		}
		return bGot;
	};
	int32 Ki = Pick(false, 1302u);
	if (Ki < 0 && !Only.IsEmpty()) { Only.Reset(); Ki = Pick(false, 1302u); }
	if (Ki < 0) return;
	FVector2D At = FVector2D::ZeroVector; FRDWSample S; float Yaw = 0.f;
	if (!Spot(Ki, At, S, Yaw) || !ClearOfPlaces(At))
	{
		Ki = Pick(true, 1303u);
		if (Ki < 0 || !Spot(Ki, At, S, Yaw) || !ClearOfPlaces(At)) return;
	}
	FRDWildPlace P;
	P.Id = SceneryIdBase + ((Cell.X & 0x3FF) << 10) + (Cell.Y & 0x3FF);
	P.Kind = TEXT("scenery"); P.Scenery = Ki; P.Name = SceneryKinds[Ki].Title; P.At = At; P.H = S.H; P.Biome = S.Biome;
	P.Tier = TierAt(At.X, At.Y); P.Yaw = Yaw;
	Out.Add(P);
}
