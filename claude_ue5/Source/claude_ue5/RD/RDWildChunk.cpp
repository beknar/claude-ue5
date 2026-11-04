// The wilderness's chunks (RDWild.h): what a worker thread computes for one (the ground's vertices, its water, the plants
// and rocks scattered by the biomes' tables, the places in it) and how the game thread makes the actor from it.
#include "RD/RDWild.h"
#include "RD/RDWildChunkData.h"
#include "ProceduralMeshComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"

ARDWildChunk::ARDWildChunk()
{
	PrimaryActorTick.bCanEverTick = false;
	Ground = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("Ground"));
	RootComponent = Ground;
	Ground->bUseAsyncCooking = true;
	Ground->SetCollisionProfileName(TEXT("BlockAll"));
	Ground->SetCastShadow(true);
	WaterMesh = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("Water"));
	WaterMesh->SetupAttachment(Ground);
	WaterMesh->bUseAsyncCooking = true;
	WaterMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	WaterMesh->SetCastShadow(false);
}

void ARDWildChunk::Destroyed()
{
	for (AActor* A : Props) if (IsValid(A)) A->Destroy();
	Props.Reset();
	Super::Destroyed();
}

namespace
{
	FORCEINLINE float RDWCSmooth(float A, float B, float X) { const float T = FMath::Clamp((X - A) / (B - A), 0.f, 1.f); return T * T * (3.f - 2.f * T); }
}

void RDWildComputeChunk(const FRDWildWorld& W, FRDWChunkData& D)
{
	const double T0 = FPlatformTime::Seconds();
	const double Cm = D.ChunkM, St = D.StepM;
	const int32 Nv = FMath::RoundToInt(Cm / St) + 1, Nb = Nv + 2;
	const double X0 = D.Coord.X * Cm, Y0 = D.Coord.Y * Cm;
	D.Nv = Nv;
	// ---- the samples (with a border of one for the normals)
	TArray<FRDWSample> S; S.SetNum(Nb * Nb);
	for (int32 I = 0; I < Nb; ++I)
		for (int32 J = 0; J < Nb; ++J)
			W.Sample(X0 + (I - 1) * St, Y0 + (J - 1) * St, S[I * Nb + J], true);
	// (a loaded town's section: the ground there is the town's own, drawn over this one: sink it under, rising to the town's
	// z 0 at the section's edge)
	TArray<float> Z; Z.SetNum(Nb * Nb);
	for (int32 I = 0; I < Nb; ++I)
		for (int32 J = 0; J < Nb; ++J)
		{
			float Zc = W.ToZ(S[I * Nb + J].H);
			if (D.bTownHole)
			{
				const double X = X0 + (I - 1) * St, Y = Y0 + (J - 1) * St;
				const double Ex = D.TownHalfM - FMath::Abs(X - D.TownAt.X), Ey = D.TownHalfM - FMath::Abs(Y - D.TownAt.Y);
				const double In = FMath::Min(Ex, Ey);
				if (In >= 0.0) Zc = FMath::Lerp(0.f, -60.f, RDWCSmooth(0.f, 3.f, (float)In));
			}
			Z[I * Nb + J] = Zc;
		}
	auto Zat = [&](int32 I, int32 J) { return Z[(I + 1) * Nb + (J + 1)]; };
	auto Sat = [&](int32 I, int32 J) -> const FRDWSample& { return S[(I + 1) * Nb + (J + 1)]; };
	// ---- the ground's mesh
	D.V.SetNumUninitialized(Nv * Nv); D.N.SetNumUninitialized(Nv * Nv); D.C.SetNumUninitialized(Nv * Nv);
	D.UV0.SetNumUninitialized(Nv * Nv); D.UV1.SetNumUninitialized(Nv * Nv); D.UV2.SetNumUninitialized(Nv * Nv);
	D.Slope.SetNumUninitialized(Nv * Nv); D.Tan.SetNumUninitialized(Nv * Nv);
	const double U0 = (X0 - W.Xs) / 4.0, V0 = (Y0 - W.Yw) / 4.0;      // (the detail textures: one repeat every 4 m, from the continent's corner)
	for (int32 I = 0; I < Nv; ++I)
		for (int32 J = 0; J < Nv; ++J)
		{
			const int32 K = I * Nv + J;
			const FRDWSample& Q = Sat(I, J);
			const float Zc = Zat(I, J);
			D.V[K] = FVector(I * St * 100.0, J * St * 100.0, Zc);
			const float Dx = (Zat(I + 1, J) - Zat(I - 1, J)) / (float)(2.0 * St * 100.0), Dy = (Zat(I, J + 1) - Zat(I, J - 1)) / (float)(2.0 * St * 100.0);
			const FVector Nr = FVector(-Dx, -Dy, 1.f).GetSafeNormal();
			D.N[K] = Nr;
			// (the detail textures' U runs along X: the tangent is X made square to the normal)
			D.Tan[K] = FProcMeshTangent((FVector(1, 0, 0) - Nr * Nr.X).GetSafeNormal(), false);
			const float Slope = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp((float)Nr.Z, 0.f, 1.f)));
			D.Slope[K] = Slope;
			// rock where it is steep, snow sliding off the steepest
			const float Rk = FMath::Max(Q.Rock, RDWCSmooth(31.f, 46.f, Slope)) * (Q.WaterKind ? 0.3f : 1.f);
			const float Sn = Q.Snow * (1.f - RDWCSmooth(38.f, 58.f, Slope));
			FLinearColor C = Q.Color;
			if (Rk > Q.Rock && Q.WaterKind == 0) C = FMath::Lerp(C, Q.RockColor, (Rk - Q.Rock) * 0.85f);
			if (Sn < Q.Snow && Q.WaterKind == 0) C = FMath::Lerp(C, Q.RockColor, (Q.Snow - Sn) * 0.7f);
			C.A = Q.Lava;
			D.C[K] = C;
			D.UV0[K] = FVector2D(U0 + I * St / 4.0, V0 + J * St / 4.0);
			D.UV1[K] = FVector2D(Rk, Sn);
			D.UV2[K] = FVector2D(Q.Sand, FMath::Max(Q.Mud, Q.Road * 0.8f));
		}
	D.T.Reserve((Nv - 1) * (Nv - 1) * 6);
	for (int32 I = 0; I + 1 < Nv; ++I)
		for (int32 J = 0; J + 1 < Nv; ++J)
		{
			const int32 A = I * Nv + J, B = (I + 1) * Nv + J, C = I * Nv + J + 1, E = (I + 1) * Nv + J + 1;
			// (UE's procedural mesh faces up when cross(V1 - V0, V2 - V0) points down: wound accordingly)
			D.T.Add(A); D.T.Add(C); D.T.Add(B);
			D.T.Add(B); D.T.Add(C); D.T.Add(E);
		}
	// ---- water: a surface over every quad under water (fresh, sea, hot spring), lava over the lava; a floor to wade on
	// under deep water and a barrier where the sea is deep
	for (int32 I = 0; I + 1 < Nv; ++I)
		for (int32 J = 0; J + 1 < Nv; ++J)
		{
			const FRDWSample* Qs[4] = { &Sat(I, J), &Sat(I + 1, J), &Sat(I, J + 1), &Sat(I + 1, J + 1) };
			int32 Kind = 0; float Lv = -1e9f; float Deep = 0.f;
			for (const FRDWSample* Q : Qs) if (Q->WaterKind) { Kind = Q->WaterKind; Lv = FMath::Max(Lv, Q->Water); Deep = FMath::Max(Deep, Q->Water - Q->H); }
			const float LavaQ = FMath::Max(FMath::Max(Qs[0]->Lava, Qs[1]->Lava), FMath::Max(Qs[2]->Lava, Qs[3]->Lava));
			if (!Kind && LavaQ < 0.45f) continue;
			const int32 Sec = !Kind ? 3 : (Kind == 1 ? 1 : (Kind == 6 ? 2 : 0));
			FRDWChunkData::FWater& Wt = D.Water[Sec];
			const int32 Base = Wt.V.Num();
			const int32 Ij[4][2] = { { I, J }, { I + 1, J }, { I, J + 1 }, { I + 1, J + 1 } };
			for (int32 Q = 0; Q < 4; ++Q)
			{
				const FRDWSample& Sq = *Qs[Q];
				const float Hv = Kind ? (Sq.WaterKind ? Sq.Water : Lv) : Sq.H;
				const float Zw = Kind ? W.ToZ(Hv) + (Kind == 1 ? 0.f : 2.f) : Zat(Ij[Q][0], Ij[Q][1]) + 6.f;
				Wt.V.Add(FVector(Ij[Q][0] * St * 100.0, Ij[Q][1] * St * 100.0, Zw));
				Wt.UV.Add(FVector2D(U0 / 4.0 + Ij[Q][0] * St / 16.0, V0 / 4.0 + Ij[Q][1] * St / 16.0));
				Wt.C.Add(FLinearColor(FMath::Clamp((Sq.Water - Sq.H) / 8.f, 0.f, 1.f), Sq.Lava, 0.f, 1.f));
			}
			Wt.T.Add(Base); Wt.T.Add(Base + 2); Wt.T.Add(Base + 1);
			Wt.T.Add(Base + 1); Wt.T.Add(Base + 2); Wt.T.Add(Base + 3);
			if (Kind && Deep > 0.9f)
			{
				// (she wades no deeper than 90 cm; past the sea's shelf a wall)
				const bool bWall = Kind == 1 && Deep > 8.f;
				const int32 Bb = D.Block.Num();
				for (int32 Q = 0; Q < 4; ++Q) D.Block.Add(FVector(Ij[Q][0] * St * 100.0, Ij[Q][1] * St * 100.0, W.ToZ(Lv) + (bWall ? 300.f : -90.f)));
				D.BlockT.Add(Bb); D.BlockT.Add(Bb + 2); D.BlockT.Add(Bb + 1);
				D.BlockT.Add(Bb + 1); D.BlockT.Add(Bb + 2); D.BlockT.Add(Bb + 3);
			}
		}
	// ---- the near-water mask (within ~10 m of water, for reeds), by dilation over the vertices
	TArray<uint8> Wet; Wet.SetNumZeroed(Nv * Nv);
	for (int32 K = 0; K < Nv * Nv; ++K) if (Sat(K / Nv, K % Nv).WaterKind) Wet[K] = 1;
	for (int32 Pass = 0; Pass < 5; ++Pass)
	{
		TArray<uint8> Nw = Wet;
		for (int32 I = 1; I + 1 < Nv; ++I)
			for (int32 J = 1; J + 1 < Nv; ++J)
				if (!Wet[I * Nv + J] && (Wet[(I - 1) * Nv + J] || Wet[(I + 1) * Nv + J] || Wet[I * Nv + J - 1] || Wet[I * Nv + J + 1])) Nw[I * Nv + J] = (uint8)(Pass + 2);
		Wet = MoveTemp(Nw);
	}
	// ---- the plants and rocks: each biome present scatters its table's kinds on a jittered grid, kept where it is that
	// biome (its blend weight), its forest is close (the canopy), the ground not too steep, not under water or on a road
	TMap<int32, int32> Present;
	for (int32 K = 0; K < Nv * Nv; K += 7) { const FRDWSample& Q = Sat(K / Nv, K % Nv); Present.FindOrAdd(Q.Biome)++; if (Q.W1 < 0.9f) Present.FindOrAdd(Q.Biome2)++; }
	auto Nearest = [&](double Lx, double Ly, int32& I, int32& J) { I = FMath::Clamp(FMath::RoundToInt(Lx / St), 0, Nv - 1); J = FMath::Clamp(FMath::RoundToInt(Ly / St), 0, Nv - 1); };
	for (const auto& Kv : Present)
	{
		const int32 Bi = Kv.Key;
		if (!W.Biomes.IsValidIndex(Bi)) continue;
		const FRDWildBiome& B = W.Biomes[Bi];
		for (int32 Fi = 0; Fi < B.Foliage.Num(); ++Fi)
		{
			const FRDWildFoliage& F = B.Foliage[Fi];
			if (F.Density <= 0.f) continue;
			const double Sp = 100.0 / FMath::Sqrt(F.Density);
			const int32 Ng = FMath::Max(1, FMath::FloorToInt(Cm / Sp));
			FRDWChunkData::FInst Ins; Ins.Biome = Bi; Ins.Foliage = Fi; Ins.bNear = F.bNearOnly;
			const bool bTree = F.Kind == TEXT("tree");
			const bool bCrop = F.Kind == TEXT("crop");
			for (int32 Gi = 0; Gi < Ng; ++Gi)
				for (int32 Gj = 0; Gj < Ng; ++Gj)
				{
					const int32 Wx = D.Coord.X * Ng + Gi, Wy = D.Coord.Y * Ng + Gj;
					const uint32 Hs = (uint32)(Bi * 131 + Fi * 7919);
					const double Lx = (Gi + FRDWildWorld::Rand01(Wx, Wy, Hs + 1u)) * Sp, Ly = (Gj + FRDWildWorld::Rand01(Wx, Wy, Hs + 2u)) * Sp;
					int32 I, J; Nearest(Lx, Ly, I, J);
					const FRDWSample& Q = Sat(I, J);
					float Wb = Q.Biome == Bi ? Q.W1 : (Q.Biome2 == Bi ? 1.f - Q.W1 : 0.f);
					if (Wb <= 0.f) continue;
					// (a forest's trees follow its canopy; an open biome's few trees stand anywhere: its canopy is 0, and the
					// factor took every one of them, the savannah's acacias too)
					if (bTree && B.Canopy > 0.05f) Wb *= FMath::Clamp(Q.Canopy / B.Canopy, 0.f, 1.2f);
					if (F.Clump > 0.f) Wb *= RDWCSmooth(-0.1f, 0.35f, FRDWildWorld::Fbm(X0 + Lx, Y0 + Ly, 1.0 / 60.0, 2, Hs + 3u)) * F.Clump + (1.f - F.Clump);
					if (Q.Road > 0.15f || (Q.Snow > 0.85f && !bTree && F.Kind != TEXT("rock") && F.Kind != TEXT("ice"))) continue;
					if (bCrop ? Q.Field < 0.5f : (Q.Field > 0.3f && F.Kind != TEXT("rock"))) continue;
					if (F.NearWater < 0.f) { if (!Q.WaterKind || Q.WaterKind == 1) continue; }
					else if (Q.WaterKind) continue;
					else if (F.NearWater > 0.f && !Wet[I * Nv + J]) continue;
					if (D.Slope[I * Nv + J] > F.SlopeMax) continue;
					if (D.bTownHole && FMath::Abs(X0 + Lx - D.TownAt.X) < D.TownHalfM + 6.0 && FMath::Abs(Y0 + Ly - D.TownAt.Y) < D.TownHalfM + 6.0) continue;
					if (FRDWildWorld::Rand01(Wx, Wy, Hs + 4u) > Wb) continue;
					// (its height: the ground's, from the quad's corners)
					const int32 I0 = FMath::Clamp(FMath::FloorToInt(Lx / St), 0, Nv - 2), J0 = FMath::Clamp(FMath::FloorToInt(Ly / St), 0, Nv - 2);
					const float Fx = (float)(Lx / St - I0), Fy = (float)(Ly / St - J0);
					float Zc = FMath::Lerp(FMath::Lerp(Zat(I0, J0), Zat(I0 + 1, J0), Fx), FMath::Lerp(Zat(I0, J0 + 1), Zat(I0 + 1, J0 + 1), Fx), Fy);
					if (F.NearWater < 0.f) Zc = W.ToZ(Q.Water) + 3.f;
					const float Sc = FMath::Lerp(F.ScaleMin, F.ScaleMax, FRDWildWorld::Rand01(Wx, Wy, Hs + 5u));
					const float Yaw = FRDWildWorld::Rand01(Wx, Wy, Hs + 6u) * 360.f;
					FQuat Rq = FQuat(FVector::UpVector, FMath::DegreesToRadians(Yaw));
					if (F.bAlign) Rq = FQuat::FindBetweenNormals(FVector::UpVector, D.N[I * Nv + J]) * Rq;
					Ins.X.Add(FTransform(Rq, FVector(Lx * 100.0, Ly * 100.0, Zc - F.Sink * Sc), FVector(Sc)));
				}
			if (Ins.X.Num() > 0) D.Inst.Add(MoveTemp(Ins));
		}
	}
	// ---- the places whose middle is in it
	{
		TArray<FRDWildPlace> Ps;
		const FIntPoint C0 = W.PlaceCellOf(X0, Y0), C1 = W.PlaceCellOf(X0 + Cm, Y0 + Cm);
		for (int32 Ci = C0.X; Ci <= C1.X; ++Ci) for (int32 Cj = C0.Y; Cj <= C1.Y; ++Cj) W.PlacesIn(FIntPoint(Ci, Cj), Ps);
		for (const FRDWildPlace& P : Ps) if (P.At.X >= X0 && P.At.X < X0 + Cm && P.At.Y >= Y0 && P.At.Y < Y0 + Cm && P.Town < 0) D.Places.Add(P);
	}
	D.Ms = (FPlatformTime::Seconds() - T0) * 1000.0;
}
