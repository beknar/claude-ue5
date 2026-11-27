// The user's list of 2026-11-27 (docs/improvements18.txt; the plan docs/improvements18_plan.md), its second phase: "on hills and mountain
// sides, there is red scrub that appears to be floating in the air". The red scrub is the bearberry, a mat 35 cm high: it and every bush stood
// upright on slopes up to 30 degrees, sunk 3 cm, its height a bilinear blend of its 2 m quad's corners, so its downhill side hung over the
// ground. With rd.Scrub18 1 (the default) a bush lower than half its width lies along its slope, an upright bush is sunk by its footprint's
// radius times the slope (its downhill edge at the ground), and every plant's height on its quad follows the drawn triangle's split
// (RDWildChunk.cpp). rd.Scrub18 0 lays them as before (the test's comparison). GetWildFoliageGaps18 measures the plants' footprints against
// the drawn ground under them. (Plants on far chunks drawn on 4 m or 8 m still stand on the 2 m ground, over the coarse chord of a convex
// slope: the bearberry grows near her only; the other bushes' far gap is in TODO.md.)
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDWildChunkData.h"
#include "ProceduralMeshComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "HAL/IConsoleManager.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList18, Log, All);

namespace
{
	TAutoConsoleVariable<int32> CVarRDScrub18(TEXT("rd.Scrub18"), 1, TEXT("The wilds' bushes sunk by their footprint on a slope and every plant's height by the drawn triangle (1), or laid as before the list of 2026-11-27 (0); chunks made after the change"));

	// (the drawn surface's height at a point of a chunk, as RDList16c.cpp's RDWildDrawnZ16: its grid of every DrawEvery-th vertex, each
	// cell's two triangles split from (a+1, b) to (a, b+1))
	bool RDL18DrawnZ(const ARDWildChunk* C, int32 Nv, double StCm, double Lx, double Ly, float& Z)
	{
		if (!C || !C->Ground) return false;
		const FProcMeshSection* S = C->Ground->GetProcMeshSection(0);
		if (!S) return false;
		TArray<int32> Ix;
		const int32 Ev = FMath::Max(1, C->DrawEvery16);
		for (int32 I = 0; I < Nv; I += Ev) Ix.Add(I);
		if (Ix.Last() != Nv - 1) Ix.Add(Nv - 1);
		const int32 M = Ix.Num();
		if (S->ProcVertexBuffer.Num() < M * M) return false;
		auto Cell = [&](double L, int32& A, double& F)
		{
			const double G = L / StCm;
			A = 0; while (A + 2 < M && Ix[A + 1] <= G) ++A;
			F = FMath::Clamp((G - Ix[A]) / FMath::Max(1, Ix[A + 1] - Ix[A]), 0.0, 1.0);
		};
		// (a point past the chunk's edge is not measured against its edge (PR #147's review))
		if (Lx < 0.0 || Ly < 0.0 || Lx > (Nv - 1) * StCm || Ly > (Nv - 1) * StCm) return false;
		int32 A, B; double Fa, Fb; Cell(Lx, A, Fa); Cell(Ly, B, Fb);
		auto Pz = [&](int32 a, int32 b) { return S->ProcVertexBuffer[a * M + b].Position.Z; };
		const float Z00 = Pz(A, B), Z10 = Pz(A + 1, B), Z01 = Pz(A, B + 1), Z11 = Pz(A + 1, B + 1);
		Z = Fa + Fb <= 1.0 ? (float)(Z00 + (Z10 - Z00) * Fa + (Z01 - Z00) * Fb) : (float)(Z11 + (Z01 - Z11) * (1.0 - Fa) + (Z10 - Z11) * (1.0 - Fb));
		return true;
	}
}

bool RDScrub18On() { return CVarRDScrub18.GetValueOnAnyThread() != 0; }

float RDScrub18ExtraSink(const FRDWildFoliage& F, float Sc, const FVector& N)
{
	// (a bush's footprint: its mesh's box across, a little in from its corners (a bush's crown is round); its downhill edge brought to the
	// ground by the slope's rise over that radius, never more than a third of its height)
	if (!RDScrub18On() || F.bAlign || F.Kind != TEXT("bush") || F.Radius18 <= 0.f || RDScrub18Align(F)) return 0.f;
	const float R = F.Radius18 * Sc;
	const float Nz = FMath::Clamp((float)N.Z, 0.2f, 1.f);
	const float Tan = FMath::Sqrt(FMath::Max(0.f, 1.f - Nz * Nz)) / Nz;
	return FMath::Min(R * Tan, F.Height18 * Sc / 3.f);
}

bool RDScrub18Align(const FRDWildFoliage& F)
{
	// (a mat lower than half its width (Radius18 is half the box's width: the bearberry, 35 cm over a metre and more) lies along the slope as
	// the ground cover it is)
	return RDScrub18On() && !F.bAlign && F.Kind == TEXT("bush") && F.Height18 > 0.f && F.Height18 < F.Radius18;
}

FString ARDDungeonGenerator::GetWildFoliageGaps18(float MaxM, float MinSlopeDeg) const
{
	// (tests: every plant instance within MaxM of her on ground steeper than MinSlopeDeg, by mesh: its mesh's box's four bottom corners turned
	// and scaled with it, each against the drawn surface under it; an instance's gap is its highest corner's height over the ground there
	// (the downhill side hanging), "whole" when even its lowest corner is over it. Lines "<mesh>|<kind>|<instances>|<largest gap cm>|<95th
	// percentile cm>|<over 10 cm>|<whole over 5 cm>|<largest at step 1>|<at 2>|<at 4>", joined by ";")
	if (!IsWildReady()) return FString();
	const APawn* P = GetWorld() ? GetWorld()->GetFirstPlayerController() ? GetWorld()->GetFirstPlayerController()->GetPawn() : nullptr : nullptr;
	if (!P) return FString();
	const FVector At = P->GetActorLocation();
	const int32 Nv = FMath::RoundToInt(WildChunkM / WildStepM) + 1;
	const double StCm = WildStepM * 100.0;
	const float CosMin = FMath::Cos(FMath::DegreesToRadians(MinSlopeDeg));
	struct FAcc { FString Kind; TArray<float> Gaps; int32 Over10 = 0, Whole5 = 0; float ByStep[3] = { -1e9f, -1e9f, -1e9f }; };
	TMap<FString, FAcc> By;
	TMap<const UStaticMesh*, FString> KindOf;
	for (const FRDWildBiome& B : WildBiomes) for (const FRDWildFoliage& F : B.Foliage) if (F.Mesh) KindOf.Add(F.Mesh, F.Kind);
	for (const auto& Kv : WildChunks)
	{
		const ARDWildChunk* C = Kv.Value;
		if (!IsValid(C) || C->bMaking) continue;
		const FVector O = C->GetActorLocation();
		const int32 Si = C->DrawEvery16 <= 1 ? 0 : C->DrawEvery16 == 2 ? 1 : 2;
		for (const TArray<TObjectPtr<UHierarchicalInstancedStaticMeshComponent>>* L : { &C->Foliage, &C->NearFoliage })
			for (const UHierarchicalInstancedStaticMeshComponent* H : *L)
			{
				if (!H || !H->GetStaticMesh()) continue;
				const UStaticMesh* Ms = H->GetStaticMesh();
				const FBox Bx = Ms->GetBoundingBox();
				const FString* Kd = KindOf.Find(Ms);
				FAcc& A = By.FindOrAdd(Ms->GetName());
				if (Kd) A.Kind = *Kd;
				for (int32 I = 0; I < H->GetInstanceCount(); ++I)
				{
					FTransform X; H->GetInstanceTransform(I, X, true);
					if (FVector::Dist2D(X.GetLocation(), At) > MaxM * 100.0) continue;
					float Zc; const FVector L0 = X.GetLocation() - O;
					if (!RDL18DrawnZ(C, Nv, StCm, L0.X, L0.Y, Zc)) continue;
					// (the slope under it: the drawn surface 1 m each way)
					float Zx, Zy;
					if (!RDL18DrawnZ(C, Nv, StCm, L0.X + 100.0, L0.Y, Zx) || !RDL18DrawnZ(C, Nv, StCm, L0.X, L0.Y + 100.0, Zy)) continue;
					const FVector Nn = FVector(-(Zx - Zc) / 100.f, -(Zy - Zc) / 100.f, 1.f).GetSafeNormal();
					if (Nn.Z > CosMin) continue;
					float Hi = -1e9f, Lo = 1e9f; bool bAll = true;
					for (int32 Cn = 0; Cn < 4; ++Cn)
					{
						// (the footprint: the box's bottom corners drawn in to 0.7 of its half widths, a crown's round edge rather than the
						// empty corners of its box)
						const FVector Mc = Bx.GetCenter();
						const FVector Lc(Mc.X + 0.7 * (((Cn & 1) ? Bx.Max.X : Bx.Min.X) - Mc.X), Mc.Y + 0.7 * (((Cn & 2) ? Bx.Max.Y : Bx.Min.Y) - Mc.Y), Bx.Min.Z);
						const FVector Wc = X.TransformPosition(Lc) - O;
						float Zg; if (!RDL18DrawnZ(C, Nv, StCm, Wc.X, Wc.Y, Zg)) { bAll = false; break; }
						Hi = FMath::Max(Hi, (float)Wc.Z - Zg); Lo = FMath::Min(Lo, (float)Wc.Z - Zg);
					}
					if (!bAll) continue;
					A.Gaps.Add(Hi);
					if (Hi > 10.f) ++A.Over10;
					if (Lo > 5.f) ++A.Whole5;
					A.ByStep[Si] = FMath::Max(A.ByStep[Si], Hi);
				}
			}
	}
	TArray<FString> Out;
	for (auto& Kv : By)
	{
		FAcc& A = Kv.Value;
		if (A.Gaps.Num() == 0) continue;
		A.Gaps.Sort();
		Out.Add(FString::Printf(TEXT("%s|%s|%d|%.1f|%.1f|%d|%d|%.1f|%.1f|%.1f"), *Kv.Key, *A.Kind, A.Gaps.Num(), A.Gaps.Last(),
			A.Gaps[FMath::Clamp(FMath::FloorToInt(A.Gaps.Num() * 0.95f), 0, A.Gaps.Num() - 1)], A.Over10, A.Whole5, A.ByStep[0], A.ByStep[1], A.ByStep[2]));
	}
	return FString::Join(Out, TEXT(";"));
}
