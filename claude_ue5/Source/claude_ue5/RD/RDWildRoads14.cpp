// The list of 2026-11-16's fourteenth phase (docs/improvements14.txt items 21, 22): "minor roads that are dirt roads that lead to
// villages, farmsteads, etc, with signs on them at regular intervals showing where they lead to and how far"; "the major roads should
// have signs that say where they lead to and how far that city is at regular intervals". The world's model (RDWild.h): made once at
// Init, after the major roads and the quests' places; nothing here touches the engine's objects.
#include "RD/RDWild.h"
#include "HAL/PlatformTime.h"
#include "Async/ParallelFor.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDWildRoads, Log, All);

namespace
{
	FORCEINLINE double RDR14SegDist(const FVector2D& P, const FVector2D& A, const FVector2D& B, double& T)
	{
		const FVector2D Ab = B - A; const double L2 = Ab.SizeSquared();
		T = L2 > 1e-6 ? FMath::Clamp(FVector2D::DotProduct(P - A, Ab) / L2, 0.0, 1.0) : 0.0;
		return FVector2D::Distance(P, A + Ab * T);
	}
	/** a sign's figure: metres to 50 under a kilometre, a tenth of a km under ten, whole km beyond */
	FString RDR14Dist(double M)
	{
		if (M < 950.0) return FString::Printf(TEXT("%d m"), FMath::Max(50, FMath::RoundToInt(M / 50.0) * 50));
		if (M < 9950.0) return FString::Printf(TEXT("%.1f km"), M / 1000.0);
		return FString::Printf(TEXT("%d km"), FMath::RoundToInt(M / 1000.0));
	}
	/** a way found for a minor road: its points from the place's end to the join, and what its signs name */
	struct FRDR14Link
	{
		TArray<FVector2D> P;
		FString Dest, DestKind, Up;
		int32 DestId = -1, Join = -1, JoinSeg = -1, Parent = -1;
		double JoinT = 0.0, UpM = 0.0;
		bool bOk = false;
	};
	/** the places a way keeps clear of (their middles, 60 m): 500 m cells */
	FORCEINLINE FIntPoint RDR14DotKey(const FVector2D& P) { return FIntPoint(FMath::FloorToInt(P.X / 500.0), FMath::FloorToInt(P.Y / 500.0)); }
}

FString FRDWildWorld::SignDistText(double M) { return RDR14Dist(M); }

double FRDWildWorld::RoadAlong(int32 Ri, int32 Seg, double T) const
{
	if (!Roads.IsValidIndex(Ri)) return 0.0;
	const FRoad& R = Roads[Ri];
	double S = 0.0;
	for (int32 I = 0; I < Seg && I + 1 < R.P.Num(); ++I) S += FVector2D::Distance(R.P[I], R.P[I + 1]);
	if (R.P.IsValidIndex(Seg + 1)) S += FVector2D::Distance(R.P[Seg], R.P[Seg + 1]) * T;
	return S;
}

double FRDWildWorld::RoadLength(int32 Ri) const
{
	if (!Roads.IsValidIndex(Ri)) return 0.0;
	double S = 0.0;
	for (int32 I = 0; I + 1 < Roads[Ri].P.Num(); ++I) S += FVector2D::Distance(Roads[Ri].P[I], Roads[Ri].P[I + 1]);
	return S;
}

bool FRDWildWorld::NearestRoadPoint(const FVector2D& P, double R, bool bMajorOnly, int32& OutRoad, int32& OutSeg, double& OutT, FVector2D& OutAt, const TBitArray<>* Allowed) const
{
	double Best = R; OutRoad = -1; OutSeg = -1; OutT = 0.0;
	const int32 I0 = FMath::FloorToInt((P.X - R) / HashM), I1 = FMath::FloorToInt((P.X + R) / HashM);
	const int32 J0 = FMath::FloorToInt((P.Y - R) / HashM), J1 = FMath::FloorToInt((P.Y + R) / HashM);
	for (int32 I = I0; I <= I1; ++I)
		for (int32 J = J0; J <= J1; ++J)
			for (auto It = SegHash.CreateConstKeyIterator(FIntPoint(I, J)); It; ++It)
			{
				const uint32 V = It.Value();
				if ((V >> 31) == 0) continue;
				const int32 Ri = (V >> 16) & 0x7FFF, Sg = V & 0xFFFF;
				if (!Roads.IsValidIndex(Ri) || (bMajorOnly && Roads[Ri].bTrack) || !Roads[Ri].P.IsValidIndex(Sg + 1)) continue;
				if (Allowed && (!Allowed->IsValidIndex(Ri) || !(*Allowed)[Ri])) continue;
				double T; const double D = RDR14SegDist(P, Roads[Ri].P[Sg], Roads[Ri].P[Sg + 1], T);
				if (D < Best) { Best = D; OutRoad = Ri; OutSeg = Sg; OutT = T; OutAt = FMath::Lerp(Roads[Ri].P[Sg], Roads[Ri].P[Sg + 1], T); }
			}
	return OutRoad >= 0;
}

void FRDWildWorld::RoadUp(int32 Ri, int32 Seg, double T, FString& OutName, double& OutM) const
{
	// (where a way joins a road: the way on along it to its end's name. A major road's nearer town; a minor road's own end (the
	// village it leads to, or on to the major road it joins and its town))
	OutName.Reset(); OutM = 0.0;
	if (!Roads.IsValidIndex(Ri)) return;
	const FRoad& R = Roads[Ri];
	const double S = RoadAlong(Ri, Seg, T), L = RoadLength(Ri);
	if (!R.bTrack)
	{
		const bool bFrom = S < L - S;
		const int32 Ti = bFrom ? R.From : R.To;
		if (Towns.IsValidIndex(Ti)) { OutName = Towns[Ti].Name; OutM = bFrom ? S : L - S; }
		return;
	}
	OutName = R.Up; OutM = (L - S) + R.UpM;
}

bool FRDWildWorld::MinorPath(const FVector2D& A, const FVector2D& B, uint32 Sk, const TMultiMap<FIntPoint, FVector2D>& Dots, const FVector2D& OwnA, const FVector2D& OwnB, TArray<FVector2D>& Out) const
{
	// (a way from A to B: straight, then bent a quarter and a half of its length to either side; 25 m steps wandering 15 m off the line
	// (none at the ends). Refused over the sea, a lake, a pond, a marsh pool, a hot spring or lava, within 1.1 km of a town, or within
	// 60 m of another place's middle (its own place and the village it leads to are named, OwnA / OwnB: PR #92's review, an end's 50 m
	// excused a farmstead by a lane's join, whose yard the lane then crossed and which play then refused); a river it fords)
	const double L = FVector2D::Distance(A, B);
	if (L < 30.0) return false;
	const FVector2D D = (B - A) / L, Pp(-D.Y, D.X);
	static const double Bends[5] = { 0.0, 0.25, -0.25, 0.5, -0.5 };
	for (const double Bd : Bends)
	{
		const FVector2D M = (A + B) * 0.5 + Pp * (Bd * L);
		const double Lc = FVector2D::Distance(A, M) + FVector2D::Distance(M, B);
		const int32 N = FMath::Max(2, FMath::CeilToInt(Lc / 25.0));
		Out.Reset();
		bool bBad = false;
		for (int32 K = 0; K <= N && !bBad; ++K)
		{
			const double T = (double)K / N;
			FVector2D Q = A * FMath::Square(1.0 - T) + M * (2.0 * T * (1.0 - T)) + B * (T * T);
			const double Ends = FMath::Min(1.0, FMath::Min(T * Lc, (1.0 - T) * Lc) / 150.0);
			const FVector2D Td = (B - A) * (2.0 * T) + (M - A) * (2.0 * (1.0 - 2.0 * T));
			const FVector2D Tn = Td.GetSafeNormal();
			Q += FVector2D(-Tn.Y, Tn.X) * (15.0 * Perlin(K * 0.08, (Sk % 997) * 0.37, Seed + 1601u) * Ends);
			if (K > 0 && K < N)
			{
				if (Continent(Q.X, Q.Y) < 0.02f) { bBad = true; break; }
				double Dt; NearestTown(Q.X, Q.Y, Dt);
				if (Dt < 1100.0) { bBad = true; break; }
				FRDWSample S; Sample(Q.X, Q.Y, S, false);
				if ((S.WaterKind != 0 && S.WaterKind != 3) || S.H < 0.5f || S.Lava > 0.3f) { bBad = true; break; }
				const FIntPoint Kc = RDR14DotKey(Q);
				for (int32 Di = -1; Di <= 1 && !bBad; ++Di)
					for (int32 Dj = -1; Dj <= 1 && !bBad; ++Dj)
						for (auto It = Dots.CreateConstKeyIterator(Kc + FIntPoint(Di, Dj)); It; ++It)
						{
							const FVector2D& O = It.Value();
							if (FVector2D::DistSquared(O, OwnA) < 1.0 || FVector2D::DistSquared(O, OwnB) < 1.0) continue;
							if (FVector2D::DistSquared(O, Q) < 60.0 * 60.0) { bBad = true; break; }
						}
			}
			Out.Add(Q);
		}
		if (!bBad) return true;
	}
	Out.Reset();
	return false;
}

void FRDWildWorld::MergeMajorRoads()
{
	int32 NMoved = 0;
	for (int32 Ri = 1; Ri < Roads.Num(); ++Ri)
	{
		if (Roads[Ri].bTrack) continue;
		TBitArray<> Earlier(false, Roads.Num());
		for (int32 J = 0; J < Ri; ++J) Earlier[J] = !Roads[J].bTrack;
		FRoad& R = Roads[Ri];
		for (int32 I = 0; I < R.P.Num(); ++I)
		{
			int32 Rr, Sg; double Tt; FVector2D At;
			if (!NearestRoadPoint(R.P[I], 60.0, true, Rr, Sg, Tt, At, &Earlier)) continue;
			const double D = FVector2D::Distance(R.P[I], At);
			const double U = FMath::Clamp((D - 30.0) / 30.0, 0.0, 1.0);
			const double W = 1.0 - U * U * (3.0 - 2.0 * U);
			if (W <= 0.0) continue;
			const float Zo = FMath::Lerp(Roads[Rr].Z[Sg], Roads[Rr].Z[Sg + 1], (float)Tt);
			R.P[I] = FMath::Lerp(R.P[I], At, W);
			if (R.Z.IsValidIndex(I)) R.Z[I] = FMath::Lerp(R.Z[I], Zo, (float)W);
			++NMoved;
		}
		R.Box = FBox2D(R.P);
	}
	UE_LOG(LogRDWildRoads, Log, TEXT("RDWILD the major roads merged where they ran together: %d points moved"), NMoved);
}

void FRDWildWorld::MakeMinorRoads()
{
	const double T0 = FPlatformTime::Seconds();
	const int32 NI = FMath::CeilToInt((Xn - Xs) / PlaceCellM), NJ = FMath::CeilToInt((Ye - Yw) / PlaceCellM);
	// ---- every place cell's places, every structure and every farmstead, once, before any way (the places' and structures' caches
	// keep them; a farmstead is made again where she goes, so no way passes within 60 m of one: it stands as it did here)
	TArray<TArray<FRDWildPlace>> CellPl; CellPl.SetNum(NI * NJ);
	ParallelFor(NI * NJ, [&](int32 K) { PlacesIn(FIntPoint(K / NJ, K % NJ), CellPl[K]); });
	const int32 SI = FMath::CeilToInt((Xn - Xs) / SiteCellM), SJ = FMath::CeilToInt((Ye - Yw) / SiteCellM);
	TArray<TArray<FRDWildPlace>> CellSt; CellSt.SetNum(SI * SJ);
	ParallelFor(SI * SJ, [&](int32 K) { SitesIn(FIntPoint(K / SJ, K % SJ), CellSt[K]); });
	const int32 FI0 = FMath::FloorToInt(Xs / GreatFieldM), FI1 = FMath::FloorToInt(Xn / GreatFieldM);
	TArray<TArray<FRDWildPlace>> RowFm; RowFm.SetNum(FI1 - FI0 + 1);
	ParallelFor(RowFm.Num(), [&](int32 K) { const double X0 = (FI0 + K) * GreatFieldM; FarmsteadsIn(X0, Yw, X0 + GreatFieldM, Ye, RowFm[K]); });
	TArray<FRDWildPlace> Villages, Others, Sites, Farms;
	TArray<FIntPoint> VCell;
	TArray<int32> CellVillage; CellVillage.Init(-1, NI * NJ);
	for (int32 K = 0; K < CellPl.Num(); ++K)
		for (const FRDWildPlace& P : CellPl[K])
		{
			if (P.Town >= 0 || !P.Quest.IsEmpty() || P.Kind == TEXT("lair") || P.Kind == TEXT("spawn")) continue;
			if (P.Kind == TEXT("village")) { CellVillage[K] = Villages.Num(); Villages.Add(P); VCell.Add(FIntPoint(K / NJ, K % NJ)); }
			else Others.Add(P);
		}
	for (const TArray<FRDWildPlace>& A : CellSt) Sites.Append(A);
	for (const TArray<FRDWildPlace>& A : RowFm) Farms.Append(A);
	TMultiMap<FIntPoint, FVector2D> Dots;
	for (const TArray<FRDWildPlace>* L : { &Villages, &Others, &Sites, &Farms }) for (const FRDWildPlace& P : *L) Dots.Add(RDR14DotKey(P.At), P.At);
	// ---- how far each place cell is from a major road (in cells: a chamfer from the cells the roads pass through)
	TArray<float> Dg; Dg.Init(1e9f, NI * NJ);
	for (const FRoad& R : Roads)
		if (!R.bTrack)
			for (const FVector2D& Q : R.P)
			{
				const FIntPoint C = PlaceCellOf(Q.X, Q.Y);
				if (C.X >= 0 && C.Y >= 0 && C.X < NI && C.Y < NJ) Dg[C.X * NJ + C.Y] = 0.f;
			}
	for (int32 Pass = 0; Pass < 2; ++Pass)
	{
		const int32 St = Pass == 0 ? 1 : -1;
		for (int32 I = Pass == 0 ? 0 : NI - 1; I >= 0 && I < NI; I += St)
			for (int32 J = Pass == 0 ? 0 : NJ - 1; J >= 0 && J < NJ; J += St)
			{
				float& V = Dg[I * NJ + J];
				const int32 Ii[4] = { I - St, I - St, I - St, I }, Jj[4] = { J - St, J, J + St, J - St };
				for (int32 Q = 0; Q < 4; ++Q)
					if (Ii[Q] >= 0 && Ii[Q] < NI && Jj[Q] >= 0 && Jj[Q] < NJ) V = FMath::Min(V, Dg[Ii[Q] * NJ + Jj[Q]] + (Jj[Q] != J && Ii[Q] != I ? 1.4142f : 1.f));
			}
	}
	auto TownOk = [this](const FVector2D& At) { double Dt; NearestTown(At.X, At.Y, Dt); return Dt >= 1300.0; };
	const FVector2D NoPt(1e18, 1e18);
	// ---- the villages: each to a major road within 4 km where its cell is near one, else to the nearest village nearer the roads
	// (its cell half a cell or more nearer: the ways run downhill to the roads and close no ring)
	TArray<FRDR14Link> VL; VL.SetNum(Villages.Num());
	ParallelFor(Villages.Num(), [&](int32 K)
	{
		const FRDWildPlace& V = Villages[K]; FRDR14Link& L = VL[K];
		L.Dest = V.Name; L.DestKind = V.Kind; L.DestId = V.Id;
		const float D0 = Dg[VCell[K].X * NJ + VCell[K].Y];
		int32 Rr, Sg; double Tt; FVector2D At;
		if (D0 <= 1.5f && NearestRoadPoint(V.At, 4000.0, true, Rr, Sg, Tt, At) && TownOk(At))
		{
			const FVector2D Dir = (At - V.At).GetSafeNormal();
			if (MinorPath(V.At + Dir * 45.0, At, (uint32)V.Id, Dots, V.At, NoPt, L.P)) { L.Join = Rr; L.JoinSeg = Sg; L.JoinT = Tt; L.bOk = true; return; }
		}
		TArray<TPair<double, int32>> Cand;
		for (int32 Di = -2; Di <= 2; ++Di)
			for (int32 Dj = -2; Dj <= 2; ++Dj)
			{
				const int32 I = VCell[K].X + Di, J = VCell[K].Y + Dj;
				if ((Di == 0 && Dj == 0) || I < 0 || J < 0 || I >= NI || J >= NJ) continue;
				const int32 Q = CellVillage[I * NJ + J];
				if (Q < 0 || Dg[I * NJ + J] > D0 - 0.4f) continue;
				Cand.Add(TPair<double, int32>(FVector2D::Distance(Villages[Q].At, V.At), Q));
			}
		Cand.Sort([](const TPair<double, int32>& A, const TPair<double, int32>& B) { return A.Key < B.Key; });
		for (int32 C = 0; C < FMath::Min(4, Cand.Num()); ++C)
		{
			const FRDWildPlace& Q = Villages[Cand[C].Value];
			const FVector2D Dir = (Q.At - V.At).GetSafeNormal();
			if (MinorPath(V.At + Dir * 45.0, Q.At - Dir * 45.0, (uint32)V.Id, Dots, V.At, Q.At, L.P)) { L.Parent = Cand[C].Value; L.Up = Q.Name; L.UpM = 45.0; L.bOk = true; return; }
		}
	});
	auto AddLink = [this](FRDR14Link& L) -> int32
	{
		if (Roads.Num() >= 0x7FFF) return -1;          // (the segments' hash holds a road's index in 15 bits)
		FRoad R; R.bTrack = true; R.bMinor = true; R.P = MoveTemp(L.P);
		R.Dest = L.Dest; R.DestKind = L.DestKind; R.DestId = L.DestId; R.Join = L.Join; R.JoinSeg = L.JoinSeg; R.JoinT = L.JoinT;
		// (its bed the land's height smoothed along it, its end on the road it joins)
		for (const FVector2D& Q : R.P) R.Z.Add(LandHeight(Q.X, Q.Y, false));
		for (int32 Pass = 0; Pass < 4; ++Pass)
		{
			TArray<float> Z = R.Z;
			for (int32 I = 1; I + 1 < Z.Num(); ++I) R.Z[I] = (Z[I - 1] + Z[I] * 2.f + Z[I + 1]) * 0.25f;
		}
		if (Roads.IsValidIndex(L.Join) && Roads[L.Join].Z.IsValidIndex(L.JoinSeg + 1))
			R.Z.Last() = FMath::Lerp(Roads[L.Join].Z[L.JoinSeg], Roads[L.Join].Z[L.JoinSeg + 1], (float)L.JoinT);
		for (float& Z : R.Z) Z = FMath::Max(Z, 1.2f);
		R.Box = FBox2D(R.P);
		return Roads.Add(MoveTemp(R));
	};
	int32 NV = 0, NVfail = 0, NVcut = 0, NVjoined = 0;
	for (FRDR14Link& L : VL)
	{
		if (!L.bOk) { ++NVfail; continue; }
		if (L.Join >= 0) RoadUp(L.Join, L.JoinSeg, L.JoinT, L.Up, L.UpM);
		const int32 Ri = AddLink(L);
		if (Ri >= 0) { Roads[Ri].Up = L.Up; Roads[Ri].UpM = L.UpM; Roads[Ri].ParentVillage = L.Parent >= 0 ? Villages[L.Parent].Id : -1; ++NV; }
	}
	// (a village's way to a village: what lies beyond is that village's own way on: its Up names the village, the sign's other arm)
	HashSegments();
	// ---- the villages cut off (no way of their own, or a way to a village that has none on to a major road: 46 of 91 round
	// Brokenspire in the first run): each joined to the nearest road that reaches a major road, within 5 km
	{
		TMap<int32, int32> VRoad;          // (a village's id -> its way)
		for (int32 Ri = 0; Ri < Roads.Num(); ++Ri) if (Roads[Ri].bMinor && Roads[Ri].DestKind == TEXT("village")) VRoad.Add(Roads[Ri].DestId, Ri);
		TArray<int8> Reach; Reach.Init(-1, Roads.Num());
		TFunction<bool(int32, int32)> Reaches = [&](int32 Ri, int32 Depth) -> bool
		{
			if (!Roads.IsValidIndex(Ri)) return false;
			if (!Roads[Ri].bTrack) return true;
			if (Reach[Ri] >= 0) return Reach[Ri] != 0;
			bool B = false;
			if (Depth < 200)
			{
				const FRoad& R = Roads[Ri];
				if (R.Join >= 0) B = Reaches(R.Join, Depth + 1);
				else if (const int32* Pv = VRoad.Find(R.ParentVillage)) B = Reaches(*Pv, Depth + 1);
			}
			Reach[Ri] = B ? 1 : 0;
			return B;
		};
		TBitArray<> Allowed(false, Roads.Num());
		for (int32 Ri = 0; Ri < Roads.Num(); ++Ri) Allowed[Ri] = Reaches(Ri, 0);
		TArray<int32> Cut;
		for (int32 K = 0; K < Villages.Num(); ++K) { const int32* Vr = VRoad.Find(Villages[K].Id); if (!Vr || !Allowed[*Vr]) Cut.Add(K); }
		TArray<FRDR14Link> CL; CL.SetNum(Cut.Num());
		ParallelFor(Cut.Num(), [&](int32 C)
		{
			const FRDWildPlace& V = Villages[Cut[C]]; FRDR14Link& L = CL[C];
			L.Dest = V.Name; L.DestKind = V.Kind; L.DestId = V.Id;
			int32 Rr, Sg; double Tt; FVector2D At;
			if (!NearestRoadPoint(V.At, 5000.0, false, Rr, Sg, Tt, At, &Allowed) || !TownOk(At)) return;
			const FVector2D Dir = (At - V.At).GetSafeNormal();
			if (MinorPath(V.At + Dir * 45.0, At, (uint32)V.Id * 13u + 5u, Dots, V.At, NoPt, L.P)) { L.Join = Rr; L.JoinSeg = Sg; L.JoinT = Tt; L.bOk = true; }
		});
		int32 NC = 0;
		for (FRDR14Link& L : CL)
		{
			if (!L.bOk) continue;
			RoadUp(L.Join, L.JoinSeg, L.JoinT, L.Up, L.UpM);
			const int32 Ri = AddLink(L);
			if (Ri >= 0) { Roads[Ri].Up = L.Up; Roads[Ri].UpM = L.UpM; ++NC; }
		}
		NVcut = Cut.Num(); NVjoined = NC;
		HashSegments();
	}
	// ---- the lanes: each other place, structure (1.5 km) and farmstead (800 m) to the nearest road, major or minor, away from the towns
	auto Lanes = [&](const TArray<FRDWildPlace>& Ps, double Reach, double Off, int32& NOk, int32& NFar)
	{
		TArray<FRDR14Link> LL; LL.SetNum(Ps.Num());
		ParallelFor(Ps.Num(), [&](int32 K)
		{
			const FRDWildPlace& P = Ps[K]; FRDR14Link& L = LL[K];
			L.Dest = P.Name; L.DestKind = P.Kind; L.DestId = P.Id;
			int32 Rr, Sg; double Tt; FVector2D At;
			if (!NearestRoadPoint(P.At, Reach, false, Rr, Sg, Tt, At) || !TownOk(At)) return;
			const FVector2D Dir = (At - P.At).GetSafeNormal();
			if (FVector2D::Distance(P.At, At) < Off + 40.0) return;          // (the road at its door: no lane)
			if (MinorPath(P.At + Dir * Off, At, (uint32)P.Id * 7u + 3u, Dots, P.At, NoPt, L.P)) { L.Join = Rr; L.JoinSeg = Sg; L.JoinT = Tt; L.bOk = true; }
		});
		for (FRDR14Link& L : LL)
		{
			if (!L.bOk) { ++NFar; continue; }
			RoadUp(L.Join, L.JoinSeg, L.JoinT, L.Up, L.UpM);
			const int32 Ri = AddLink(L);
			if (Ri >= 0) { Roads[Ri].Up = L.Up; Roads[Ri].UpM = L.UpM; ++NOk; }
		}
		HashSegments();
	};
	int32 NO = 0, NOfar = 0, NS = 0, NSfar = 0, NF = 0, NFfar = 0;
	Lanes(Others, 1500.0, 30.0, NO, NOfar);
	Lanes(Sites, 1500.0, 40.0, NS, NSfar);
	Lanes(Farms, 800.0, 45.0, NF, NFfar);
	MinorStats = FString::Printf(TEXT("villages %d (%d ways, %d without, %d cut off, %d of them joined on), places %d (%d lanes), structures %d (%d lanes), farmsteads %d (%d lanes), roads %d"),
		Villages.Num(), NV, NVfail, NVcut, NVjoined, Others.Num(), NO, Sites.Num(), NS, Farms.Num(), NF, Roads.Num());
	UE_LOG(LogRDWildRoads, Log, TEXT("RDWILD the minor roads in %.2f s: %s"), FPlatformTime::Seconds() - T0, *MinorStats);
}

void FRDWildWorld::MakeSigns()
{
	// (every 2 km of a major road, a post 7 m off its middle naming its two towns and how far each is along it; every 1 km of a minor
	// road, a post 4 m off naming the place it leads to one way and what it joins the other; at every minor road's join, a post on it
	// 14 m from the road it leaves, naming its place)
	Signs.Reset(); SignHash.Reset(); MajorRoadIdx.Reset();
	int32 Skipped = 0;
	for (int32 Ri = 0; Ri < Roads.Num(); ++Ri) if (!Roads[Ri].bTrack) MajorRoadIdx.Add(Ri);
	auto Yaw = [](const FVector2D& D) { return (float)FMath::RadiansToDegrees(FMath::Atan2(-D.X, D.Y)); };          // (the post's +Y along D)
	auto At = [this](int32 Ri, double S, FVector2D& OutP, FVector2D& OutD)
	{
		const FRoad& R = Roads[Ri];
		double Acc = 0.0;
		for (int32 I = 0; I + 1 < R.P.Num(); ++I)
		{
			const double L = FVector2D::Distance(R.P[I], R.P[I + 1]);
			if (Acc + L >= S || I + 2 == R.P.Num()) { const double T = L > 1e-6 ? FMath::Clamp((S - Acc) / L, 0.0, 1.0) : 0.0; OutP = FMath::Lerp(R.P[I], R.P[I + 1], T); OutD = (R.P[I + 1] - R.P[I]).GetSafeNormal(); return; }
			Acc += L;
		}
		OutP = R.P.Num() ? R.P[0] : FVector2D::ZeroVector; OutD = FVector2D(1, 0);
	};
	// (PR #92's review: where two major roads lie on one line (merged) or close, a post would stand on the other's cobbles or beside
	// another's: none within 9 m of another major road's middle, and a major road's none within 60 m of one already laid)
	auto Clear = [&](uint8 Kind, int32 Ri, const FVector2D& P, const FVector2D& Base) -> int32          // (0 clear, 1 beside another road, 2 by another post)
	{
		const FIntPoint Hc(FMath::FloorToInt(P.X / HashM), FMath::FloorToInt(P.Y / HashM));
		for (auto It = SegHash.CreateConstKeyIterator(Hc); It; ++It)
		{
			const uint32 V = It.Value();
			if ((V >> 31) == 0) continue;
			const int32 J = (V >> 16) & 0x7FFF, Sg = V & 0xFFFF;
			if (J == Ri || Roads[J].bTrack || !Roads[J].P.IsValidIndex(Sg + 1)) continue;
			// (a road on this one's line (merged) is no other road: its posts are kept apart by the 60 m below)
			double T, Tb;
			if (RDR14SegDist(P, Roads[J].P[Sg], Roads[J].P[Sg + 1], T) < 9.0 && RDR14SegDist(Base, Roads[J].P[Sg], Roads[J].P[Sg + 1], Tb) > 2.0) return 1;
		}
		if (Kind == 0)
		{
			TArray<int32> Near; SignsNear(P, 60.0, Near);
			for (const int32 K : Near) if (Signs[K].Kind == 0) return 2;
		}
		return 0;
	};
	auto Add = [&](uint8 Kind, int32 Ri, const FVector2D& Base, const FVector2D& P, const FVector2D& Dir, const FString& A, double Am, const FString& B, double Bm) -> int32
	{
		if (const int32 Why = Clear(Kind, Ri, P, Base)) return Why;
		FRDWildSign S; S.Kind = Kind; S.Road = Ri; S.At = P; S.Yaw = Yaw(Dir); S.A = A; S.Am = (float)Am; S.B = B; S.Bm = (float)Bm;
		const int32 K = Signs.Add(S);
		SignHash.Add(FIntPoint(FMath::FloorToInt(P.X / 500.0), FMath::FloorToInt(P.Y / 500.0)), K);
		return 0;
	};
	for (int32 Ri = 0; Ri < Roads.Num(); ++Ri)
	{
		const FRoad& R = Roads[Ri];
		const double L = RoadLength(Ri);
		if (!R.bTrack)
		{
			if (!Towns.IsValidIndex(R.From) || !Towns.IsValidIndex(R.To)) continue;
			for (double S = 2000.0; S < L - 1000.0; S += 2000.0)
			{
				FVector2D P, D; At(Ri, S, P, D);
				// (arm A toward the road's end (its To), arm B back toward its From)
				// (beside another road on its right, it tries its left, then 12 m out (the merge's easing bands: PR #92's review's fix had
				// left 6 km gaps); by another post it is that post's place)
				int32 Why = 1;
				for (const double Off : { 7.0, -7.0, 12.0, -12.0 }) { Why = Add(0, Ri, P, P + FVector2D(D.Y, -D.X) * Off, D, Towns[R.To].Name, L - S, Towns[R.From].Name, S); if (Why != 1) break; }
				if (Why == 1) ++Skipped;
			}
			continue;
		}
		if (!R.bMinor) continue;
		// (a minor road runs from its place to its join: arm A back to the place, arm B on toward what it joins)
		for (double S = 1000.0; S < L - 200.0; S += 1000.0)
		{
			FVector2D P, D; At(Ri, S, P, D);
			if (Add(1, Ri, P, P + FVector2D(D.Y, -D.X) * 4.0, -D, R.Dest, S, R.Up, (L - S) + R.UpM)) ++Skipped;
		}
		if (R.Join >= 0 && L > 40.0)
		{
			FVector2D P, D; At(Ri, L - 14.0, P, D);
			if (Add(2, Ri, P, P + FVector2D(D.Y, -D.X) * 4.0, -D, R.Dest, L - 14.0, FString(), 0.0)) ++Skipped;
		}
	}
	UE_LOG(LogRDWildRoads, Log, TEXT("RDWILD %d signs (%d not laid: beside another major road on both sides)"), Signs.Num(), Skipped);
}

void FRDWildWorld::RoadsIn(const FBox2D& B, bool bMinor, TArray<int32>& Out) const
{
	if (!bMinor) { for (const int32 Ri : MajorRoadIdx) if (Roads[Ri].Box.Intersect(B)) Out.Add(Ri); return; }
	const int32 I0 = FMath::FloorToInt(B.Min.X / HashM), I1 = FMath::FloorToInt(B.Max.X / HashM);
	const int32 J0 = FMath::FloorToInt(B.Min.Y / HashM), J1 = FMath::FloorToInt(B.Max.Y / HashM);
	TSet<int32> Seen;
	if ((int64)(I1 - I0 + 1) * (J1 - J0 + 1) > 2500)
	{
		for (int32 Ri = 0; Ri < Roads.Num(); ++Ri) if (Roads[Ri].bTrack && Roads[Ri].Box.Intersect(B)) Out.Add(Ri);
		return;
	}
	for (int32 I = I0; I <= I1; ++I)
		for (int32 J = J0; J <= J1; ++J)
			for (auto It = SegHash.CreateConstKeyIterator(FIntPoint(I, J)); It; ++It)
			{
				const uint32 V = It.Value();
				if ((V >> 31) == 0) continue;
				const int32 Ri = (V >> 16) & 0x7FFF;
				if (Roads.IsValidIndex(Ri) && Roads[Ri].bTrack && !Seen.Contains(Ri)) { Seen.Add(Ri); Out.Add(Ri); }
			}
}

void FRDWildWorld::SignsNear(const FVector2D& P, double R, TArray<int32>& Out) const
{
	const int32 I0 = FMath::FloorToInt((P.X - R) / 500.0), I1 = FMath::FloorToInt((P.X + R) / 500.0);
	const int32 J0 = FMath::FloorToInt((P.Y - R) / 500.0), J1 = FMath::FloorToInt((P.Y + R) / 500.0);
	for (int32 I = I0; I <= I1; ++I)
		for (int32 J = J0; J <= J1; ++J)
			for (auto It = SignHash.CreateConstKeyIterator(FIntPoint(I, J)); It; ++It)
				if (FVector2D::DistSquared(Signs[It.Value()].At, P) <= R * R) Out.Add(It.Value());
}
