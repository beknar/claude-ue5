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
	const double Wu = Fbm(X, Y, 1.0 / 70000.0, 3, Seed + 31u) * 0.10, Wv = Fbm(X, Y, 1.0 / 70000.0, 3, Seed + 32u) * 0.10;
	const double U = Y / H + Wu, V = (X - Mx) / H + Wv;
	const double D = FMath::Pow(FMath::Pow(FMath::Abs(U), 4.0) + FMath::Pow(FMath::Abs(V), 4.0), 0.25);
	float C = 0.86f - (float)D + Fbm(X, Y, 1.0 / 42000.0, 4, Seed + 1u) * 0.15f + Fbm(X, Y, 1.0 / 9000.0, 3, Seed + 2u) * 0.025f;
	// (the towns' land: Brokenspire and Ashenreach well inland; Vel Morrath near its coast but on land)
	C += 0.22f * FMath::Exp(-(float)((X * X + Y * Y) / (30000.0 * 30000.0)));
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
	T = 1.06f - 1.16f * Lt + Fbm(X, Y, 1.0 / 90000.0, 3, Seed + 41u) * 0.14f;
	const float C = Continent(X, Y);
	M = 0.5f + Fbm(X, Y, 1.0 / 65000.0, 4, Seed + 42u) * 0.62f + 0.22f * (1.f - RDWSmooth(0.f, 0.14f, C));
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
			const float R = Ridged(Site.X, Site.Y, 1.0 / 150000.0, 3, Seed + 7u) * 0.75f + 0.25f * (0.5f + 0.5f * Fbm(Site.X, Site.Y, 1.0 / 40000.0, 2, Seed + 8u));
			const float V = Fbm(Site.X, Site.Y, 1.0 / 90000.0, 2, Seed + 9u);
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
			CellSite[K] = T.Site + FVector2D(5000.0, 0.0);
			if (I + 1 < CellsX) { CellBiome[(I + 1) * CellsY + J] = BiomeIndex[T.Biome]; CellSite[(I + 1) * CellsY + J] = T.Site + FVector2D(16000.0, 2000.0); }
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
			const float Sc = FMath::Square(T - P.T) * 4.f + FMath::Square(M - P.M) * 2.f + (float)(FVector2D::Distance(S, FVector2D::ZeroVector) / 400000.0);
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
	const double Wx = X + Fbm(X, Y, 1.0 / 13000.0, 4, Seed + 61u) * 6500.0 + Fbm(X, Y, 1.0 / 2600.0, 2, Seed + 63u) * 900.0
	                    + Fbm(X, Y, 1.0 / 700.0, 2, Seed + 65u) * 320.0 + Fbm(X, Y, 1.0 / 180.0, 2, Seed + 67u) * 70.0;
	const double Wy = Y + Fbm(X, Y, 1.0 / 13000.0, 4, Seed + 62u) * 6500.0 + Fbm(X, Y, 1.0 / 2600.0, 2, Seed + 64u) * 900.0
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
	constexpr double Tau = 2400.0;
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
		if (Biomes[Bi[Q]].Shape == ERDWShape::RockyCoast) Rocky += W[Q];
		if (Bi[Q] == FarmsBiome) Farm += W[Q];
	}
	if (OutFarm) *OutFarm = Farm;
	H += LandRelief(X, Y, bDetail, Bi, W, N);
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
	O.Kind = Pr < 0.60f ? 1 : Pr < 0.80f ? 2 : Pr < 0.94f ? 3 : 0;
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
			if (Pr < 0.60f || Pr >= 0.80f) continue;
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
	float Water = -1e9f; int32 Kind = 0; float Road = 0.f;
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
	// rivers and roads: the nearest segment of each
	double Rd = 1e18, Rt = 0; int32 Ri = -1, Rs = -1;
	double Dd = 1e18, Dt = 0; int32 Di = -1, Ds = -1;
	for (auto It = SegHash.CreateConstKeyIterator(Hc); It; ++It)
	{
		const uint32 V = It.Value();
		const bool bRoad = (V >> 31) != 0; const int32 I = (V >> 16) & 0x7FFF, Sg = V & 0xFFFF;
		const TArray<FVector2D>& Pts = bRoad ? Roads[I].P : Rivers[I].P;
		double T; const double D = RDWSegDist(P, Pts[Sg], Pts[Sg + 1], T);
		if (bRoad) { if (D < Dd) { Dd = D; Dt = T; Di = I; Ds = Sg; } }
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
	if (Di >= 0)
	{
		const FRoad& R = Roads[Di];
		const float Z = FMath::Lerp(R.Z[Ds], R.Z[Ds + 1], (float)Dt);
		const float D = (float)Dd;
		// (the road a cart and a half wide, its edges ragged: 2.3 to 3 m from its middle (it was 1.5 to 2.9, under the 2 m
		// mesh's spacing); its bed levelled out to 12 m. Over a dip or through a rise its bank widens with the height it makes
		// up, 2.5 m a metre, to RDWRoadBankM: eased in over 9 m whatever the height, a bed 10 m over the ground stood on a bank
		// of 60 degrees (the user's of 2026-11-08, found by RDWildProbe))
		const float Wt = 1.f - RDWSmooth(3.2f, FMath::Min(12.f + 2.5f * FMath::Abs(Z - H), (float)RDWRoadBankM), D);
		H = FMath::Lerp(H, Z, Wt);
		Road = 1.f - RDWSmooth(2.3f + 0.7f * Perlin(X / 9.0, Y / 9.0, Seed + 71u), 3.9f, D);
		if (Road > 0.4f && Kind == 3) { Water = -1e9f; Kind = 0; }           // a ford: the road crosses dry
	}
	// the towns: their ground flat (their whole section and a margin), their region round them eased into it
	for (const FRDWildTown& T : Towns)
	{
		// (since the list of 2026-11-04 eased in over 400 to 1150 m, not 480 to 1700: the land before the gate was flat for
		// more than a kilometre)
		const double D = FVector2D::Distance(P, T.Site);
		if (D > 1150.0) continue;
		float F = 1.f - RDWSmooth(400.f, 1150.f, (float)D);
		if (H < 2.f && D > 400.0) F *= 1.f - RDWSmooth(400.f, 470.f, (float)D);
		H = FMath::Lerp(H, T.H, F);
		// (the road runs on up to the town's own ground, which draws it from the gate: its section is 360 to 504 m across)
		if (D < 400.0) { Water = -1e9f; Kind = 0; }
		if (D < 170.0) Road = 0.f;
	}
	if (Out) { Out->Water = Water; Out->WaterKind = Kind; Out->Road = Road; }
	return H;
}

float FRDWildWorld::BareHeight(double X, double Y) const
{
	// (the ground with no farm on it: the land, its water, roads and towns (the farms' ridges are measured against it))
	return Feature(X, Y, LandHeight(X, Y, true), nullptr);
}

float FRDWildWorld::Height(double X, double Y) const
{
	// (the farms' weight from the same blend as the land's height (PR #30's review: a second Blend on every call))
	float Fw = 0.f;
	const float H = LandHeight(X, Y, true, nullptr, nullptr, nullptr, nullptr, &Fw);
	FRDWSample Fs;
	const float Hf = Feature(X, Y, H, &Fs);
	// (the farms' ridge-and-furrow, as Sample adds it: what she walks on and what the places' props stand on)
	if (Fw <= 0.2f || Fs.WaterKind != 0 || Fs.Road >= 0.1f || Hf < 0.5f) return Hf;
	FRDWFarm Fm; FarmAt(X, Y, Fw, Fm);
	return Hf + Fm.Ridge * (1.f - RDWSmooth(0.02f, 0.1f, Fs.Road));
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
	for (int32 Q = 0; Q < N; ++Q)
	{
		const FRDWildBiome& B = Biomes[Bi[Q]];
		const float Wq = W[Q];
		H += Wq * ShapeHeight(Bi[Q], X, Y, Si[Q], bDetail);
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
	if (C < 0.f && H < 0.f && Kind == 0) { Water = 0.f; Kind = 1; }
	if (Kind == 0 && H < 0.f && C < 0.02f) { Water = 0.f; Kind = 1; }
	// farms: the great fields (FarmAt): open fields of strips, crofts, pasture
	float Field = 0.f;
	O.FieldCell = FIntPoint(MIN_int32, MIN_int32); O.FieldCrop = -1; O.FieldAng = 0.f; O.FarmKind = 0; O.StripW = 0.f; O.StripOff = 0.f;
	if (Farm > 0.2f && Fs.Road < 0.1f && Fs.WaterKind == 0 && H >= 0.5f)
	{
		FRDWFarm Fm; FarmAt(X, Y, Farm, Fm);
		// (ridge-and-furrow: "ploughing left each strip as a raised ridge" (Height adds the same: what she walks on))
		H += Fm.Ridge * (1.f - RDWSmooth(0.02f, 0.1f, Fs.Road));
		O.FarmKind = Fm.Kind;
		const FRDWildBiome* Fb = Biomes.IsValidIndex(FarmsBiome) ? &Biomes[FarmsBiome] : nullptr;
		if (Fb && Fb->Crops.IsValidIndex(Fm.Crop) && Fm.Field > 0.f)
		{
			// (seen from far, a pixel spans fields: their own colours fade into the region's (the list of 2026-11-07: a field
			// eases in from its edge, its colour its crop's (soil with its leaves over a share of it) drawn half way toward the
			// region's own ground, its rows the ground material's))
			Field = Fm.Field * (1.f - RDWSmooth(25.f, 110.f, PixelM));
			const FRDWildCrop& Cr = Fb->Crops[Fm.Crop];
			FLinearColor Cc = FMath::Lerp(Cr.Soil, Cr.Leaf, FMath::Clamp(Cr.Cover, 0.f, 1.f));
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
	if (Lava > 0.f) G = FMath::Lerp(G, FLinearColor(0.35f, 0.07f, 0.02f), FMath::Clamp(Lava, 0.f, 1.f));
	if (Snow > 0.f) G = FMath::Lerp(G, FLinearColor(0.78f, 0.80f, 0.84f), FMath::Clamp(Snow, 0.f, 1.f));
	if (Fs.Road > 0.f) G = FMath::Lerp(G, FLinearColor(0.31f, 0.25f, 0.17f), Fs.Road);
	if (Kind != 0)
	{
		const float Dp = FMath::Clamp((Water - H) / 6.f, 0.f, 1.f);
		const FLinearColor Wc = Kind == 6 ? FLinearColor(0.10f, 0.42f, 0.44f) : (Kind == 1 ? FLinearColor(0.05f, 0.13f, 0.20f) : FLinearColor(0.06f, 0.16f, 0.19f));
		G = FMath::Lerp(G * 0.8f, Wc, 0.45f + 0.5f * Dp);
	}
	O.H = H; O.Water = Water; O.WaterKind = Kind; O.Color = G; O.RockColor = RockCol;
	O.Rock = FMath::Clamp(Rock, 0.f, 1.f); O.Snow = FMath::Clamp(Snow, 0.f, 1.f); O.Sand = FMath::Clamp(Sand, 0.f, 1.f); O.Mud = FMath::Clamp(Mud, 0.f, 1.f);
	O.Road = Fs.Road; O.Field = Field; O.Lava = FMath::Clamp(Lava, 0.f, 1.f);
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
	// (the coasts are found where the land measure falls below 0, walking out from inland)
	auto Walk = [this](FVector2D From, FVector2D Dir) { FVector2D P = From; for (int32 I = 0; I < 3000; ++I) { if (Continent(P.X, P.Y) < 0.f) return P; P += Dir * 100.0; } return P; };
	const FVector2D NorthCoast = Walk(FVector2D(Mx + 60000.0, 0.0), FVector2D(1, 0));
	// (the port (the user's of 2026-11-07, docs/graymourne.txt): Brokenspire's size, its harbour along its northern wall, so it
	// stands nearer the coast: its sea wall about 150 m from it (until then a small town 650 m inland))
	G.Tiles = 168; G.Plan = 3;
	G.Site = NorthCoast - FVector2D(400.0, 0.0);
	for (int32 I = 0; I < 40 && Continent(G.Site.X, G.Site.Y) < 0.0005f; ++I) G.Site.X -= 100.0;     // (on land, a few hundred metres from the sea)
	// (Vel Morrath, the user's of 2026-11-06: "to the east, but not on the coast. north east of Brokenspire": 55 km north, and
	// east toward the coast but 35 km or more inside it (until then 9 km inside it, due east))
	const FVector2D NeCoast = Walk(FVector2D(55000.0, 30000.0), FVector2D(0, 1));
	V.Site = FVector2D(55000.0, FMath::Min(75000.0, NeCoast.Y - 35000.0));
	for (int32 I = 0; I < 60 && Continent(V.Site.X, V.Site.Y) < 0.08f; ++I) V.Site.Y -= 500.0;
	Towns.Add(A); Towns.Add(G); Towns.Add(V);
}

void FRDWildWorld::MakeRivers()
{
	Rivers.Reset();
	auto TownNear = [this](const FVector2D& P, double R) { for (const FRDWildTown& T : Towns) if (FVector2D::Distance(P, T.Site) < R) return true; return false; };
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
		Sources.Add(S + FVector2D((Rand01(K, 8, Seed + 92u) - 0.5) * 6000.0, (Rand01(K, 9, Seed + 93u) - 0.5) * 6000.0));
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
		FLake L; L.C = S + FVector2D((Rand01(K, 22, Seed) - 0.5) * 7000.0, (Rand01(K, 23, Seed) - 0.5) * 7000.0);
		L.R = 450.f + 1900.f * Rand01(K, 24, Seed); L.Kind = 2; L.Shape = Hash(K, 25, Seed);
		Lakes.Add(L);
	}
	TArray<FLake> Kept;
	for (FLake& L : Lakes)
	{
		bool bBad = Continent(L.C.X, L.C.Y) < 0.04f;
		for (const FRDWildTown& T : Towns) if (FVector2D::Distance(T.Site, L.C) < L.R + 2600.0) bBad = true;
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
	const double Cx = Xs + (Cell.X + 0.5) * PlaceCellM, Cy = Yw + (Cell.Y + 0.5) * PlaceCellM;
	if (Cx < Xs || Cx > Xn || Cy < Yw || Cy > Ye) return;
	const int32 B = BiomeAt(Cx, Cy);
	if (!Biomes.IsValidIndex(B)) return;
	const FRDWildBiome& Bi = Biomes[B];
	const int32 Nponds = FMath::FloorToInt(Bi.Ponds + Rand01(Cell.X, Cell.Y, Seed + 101u));
	const int32 Nsteam = Bi.Steam > 0.f ? FMath::FloorToInt(Bi.Steam + Rand01(Cell.X, Cell.Y, Seed + 102u)) : 0;
	for (int32 I = 0; I < Nponds + Nsteam; ++I)
	{
		FLake L; L.Kind = I < Nponds ? 4 : 6;
		L.C = FVector2D(Cx + (Rand01(Cell.X * 7 + I, Cell.Y, Seed + 103u) - 0.5) * PlaceCellM * 0.9, Cy + (Rand01(Cell.X, Cell.Y * 7 + I, Seed + 104u) - 0.5) * PlaceCellM * 0.9);
		L.R = L.Kind == 6 ? 14.f + 26.f * Rand01(Cell.X + I, Cell.Y, Seed + 105u) : 22.f + 90.f * Rand01(Cell.X + I, Cell.Y, Seed + 105u);
		L.Shape = Hash(Cell.X * 31 + I, Cell.Y, Seed + 106u);
		bool bBad = Continent(L.C.X, L.C.Y) < 0.03f;
		for (const FRDWildTown& T : Towns) if (FVector2D::Distance(T.Site, L.C) < 1900.0) bBad = true;
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
			for (const FRDWildTown& T : Towns) { const double D = FVector2D::Distance(R.P[I], T.Site); if (D < 1150.0) R.Z[I] = FMath::Lerp(R.Z[I], T.H, 1.f - RDWSmooth(400.f, 1150.f, (float)D)); }
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
	const double T0 = FPlatformTime::Seconds();
	Seed = InSeed; Biomes = InBiomes;
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
	MakeRivers();
	MakeLakes();
	// the ponds and hot springs of every 4 km cell, once
	Ponds.Reset(); PondHash.Reset();
	for (int32 I = 0; I * PlaceCellM < Xn - Xs; ++I)
		for (int32 J = 0; J * PlaceCellM < Ye - Yw; ++J) PondsIn(FIntPoint(I, J), Ponds);
	for (int32 K = 0; K < Ponds.Num(); ++K)
	{
		const FLake& P = Ponds[K]; const double Pad = P.R * 1.3 + RDWPondBankM + 10.0;
		for (int32 I = FMath::FloorToInt((P.C.X - Pad) / HashM); I <= FMath::FloorToInt((P.C.X + Pad) / HashM); ++I)
			for (int32 J = FMath::FloorToInt((P.C.Y - Pad) / HashM); J <= FMath::FloorToInt((P.C.Y + Pad) / HashM); ++J) PondHash.Add(FIntPoint(I, J), K);
	}
	HashSegments();
	MakeRoads();
	HashSegments();
	BaseH = Towns[0].H;
	MakeQuestPlaces();
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
	if (At.Num() < 2) return FMath::Clamp(1 + (int32)(FVector2D(X, Y).Size() / 25000.0), 1, 5);
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
	for (int32 K = 0; K < UE_ARRAY_COUNT(RDWTierNames); ++K)
		for (const FRDWildTown& T : Towns) if (T.Name == RDWTierNames[K]) { TierSites.Add(T.Site); TierValues.Add(RDWTierOf[K]); break; }
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
	const float R = Rand01(Cell.X, Cell.Y, Seed + 121u);
	if (R > 0.48f) return;
	const FVector2D At(X0 + (0.2 + 0.6 * Rand01(Cell.X, Cell.Y, Seed + 122u)) * PlaceCellM, Y0 + (0.2 + 0.6 * Rand01(Cell.X, Cell.Y, Seed + 123u)) * PlaceCellM);
	double Dt; NearestTown(At.X, At.Y, Dt);
	if (Dt < 2600.0) return;
	// (none on top of a quest's place)
	for (const FRDWildPlace& Q : QuestPlaces) if (FVector2D::Distance(Q.At, At) < 600.0) return;
	FRDWSample S; Sample(At.X, At.Y, S, false);
	if (S.WaterKind != 0 || S.H < 2.f || S.Road > 0.1f) return;
	const FString Bn = Biomes[S.Biome].Name;
	// the kinds a region holds, weighted
	float Wt[8] = { 1.f, 1.f, 1.2f, 1.f, 1.f, 0.7f, 0.6f, 0.8f };
	const bool bOpen = Bn == TEXT("plains") || Bn == TEXT("grasslands") || Bn == TEXT("meadows") || Bn == TEXT("farms") || Bn == TEXT("coastal regions") || Bn == TEXT("savannahs");
	const bool bHigh = Bn.Contains(TEXT("mountain")) || Bn == TEXT("hills") || Bn == TEXT("mesas") || Bn.Contains(TEXT("canyon")) || Bn == TEXT("rocky coastal") || Bn == TEXT("glacial");
	const bool bWild = Bn.Contains(TEXT("forest")) || Bn == TEXT("taigas") || Bn == TEXT("marshes") || Bn == TEXT("wetlands") || Bn.Contains(TEXT("volcan")) || Bn == TEXT("geothermal caldera");
	if (bOpen) { Wt[0] = 1.6f; Wt[2] = 2.f; Wt[6] = 0.1f; }
	if (!bOpen) Wt[0] = 0.15f;
	if (bHigh) { Wt[6] = 2.5f; Wt[7] = 1.4f; Wt[2] = 0.4f; Wt[4] = 1.4f; }
	if (bWild) { Wt[7] = 2.f; Wt[3] = 1.6f; Wt[1] = 1.4f; }
	if (Bn == TEXT("highland moorland") || Bn == TEXT("tundras") || Bn == TEXT("cold steppes")) Wt[5] = 2.2f;
	if (Bn == TEXT("arctic regions") || Bn == TEXT("glacial")) { Wt[0] = 0.f; Wt[2] = 0.2f; }
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

bool FRDWildWorld::FindPlace(int32 Id, FRDWildPlace& Out) const
{
	TArray<FRDWildPlace> Ps;
	if (Id >= QuestIdBase && Id < TownIdBase)
	{
		if (!QuestPlaces.IsValidIndex(Id - QuestIdBase)) return false;
		Out = QuestPlaces[Id - QuestIdBase]; return true;
	}
	if (Id >= TownIdBase) { const int32 Ti = Id - TownIdBase; if (!Towns.IsValidIndex(Ti)) return false; PlacesIn(PlaceCellOf(Towns[Ti].Site.X, Towns[Ti].Site.Y), Ps); }
	else PlacesIn(FIntPoint((Id >> 14) & 0x3FF, (Id >> 4) & 0x3FF), Ps);
	for (const FRDWildPlace& P : Ps) if (P.Id == Id) { Out = P; return true; }
	return false;
}
