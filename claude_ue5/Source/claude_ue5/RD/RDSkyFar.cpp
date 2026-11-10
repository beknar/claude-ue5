// The far land round her (the list of 2026-11-10: "in town, there is still a disc in the sky in the day time, there is a visible
// border between near the horizon and the rest of the sky. this also happens in the night time"). Pictures from 40 m over the
// town (884 sky10) showed the border: the drawn land ends with the chunks' 2 km square, and from there to the horizon nothing
// was drawn, a dark strip of the sky atmosphere's own ground under the horizon by day and by night. A ring of coarse land from
// 0.85 km to 80 km round her closes it: its heights and colours the world model's (the ground's colour, the water's), under the
// real ground so the chunks draw over it, fogged as the far land is; made again when she has gone 150 m from where it was made.
// The chunks reach 1.0 to 1.1 km round her: the ring starts at the nearer less the 150 m, so no gap opens behind her before it is made
// again (PR #39's review: from 1.1 km and every 400 m a strip up to 500 m wide opened behind a rider); where it lies under the
// chunks its near rings are dense (192 points round, 100 to 200 m apart) and sunk deeper (4 m and 6 % of the way to the next
// ring), so a valley between two of its points does not stand it over the real ground. Only in the wilds (bWild), only with a
// material (FarLandMaterial, 914's).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "ProceduralMeshComponent.h"
#include "Components/VolumetricCloudComponent.h"
#include "Engine/World.h"
#include "HAL/PlatformTime.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDSkyFar, Log, All);

namespace
{
	// (the rings' radii, metres: close near the chunks, wide far off)
	const double RDFarRadii[] = { 850.0, 950.0, 1050.0, 1150.0, 1300.0, 1500.0, 1800.0, 2400.0, 3200.0, 4400.0, 6000.0, 8500.0, 12000.0, 17000.0, 25000.0, 37000.0, 55000.0, 80000.0 };
	constexpr int32 RDFarSegs = 192;
	/** past this the ring is beyond every chunk: its plain sink */
	constexpr double RDFarUnderChunksM = 2000.0;
}

void ARDDungeonGenerator::TickFarLand(const FVector& Cam)
{
	const bool bOn = bWild && IsWildReady() && FarLandMaterial != nullptr;
	if (!bOn) { if (IsValid(FarLand)) FarLand->SetVisibility(false); return; }
	const FVector2D Here(Cam.X / 100.0, Cam.Y / 100.0);
	if (IsValid(FarLand) && FarLand->IsVisible() && FVector2D::Distance(Here, FarLandAt) < FarLandRebuildM) return;
	const double T0 = FPlatformTime::Seconds();
	if (!IsValid(FarLand))
	{
		FarLand = NewObject<UProceduralMeshComponent>(this, TEXT("RDFarLand"));
		FarLand->SetupAttachment(RootComponent);
		FarLand->SetUsingAbsoluteLocation(true); FarLand->SetUsingAbsoluteRotation(true); FarLand->SetUsingAbsoluteScale(true);
		FarLand->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		FarLand->SetCastShadow(false);
		FarLand->bUseAsyncCooking = true;
		FarLand->RegisterComponent();
		FarLand->SetWorldLocation(FVector::ZeroVector);
	}
	const int32 NR = UE_ARRAY_COUNT(RDFarRadii);
	TArray<FVector> V; TArray<int32> Tri; TArray<FVector> N; TArray<FVector2D> UV; TArray<FLinearColor> Col; TArray<FProcMeshTangent> Tg;
	V.Reserve(NR * RDFarSegs); Col.Reserve(NR * RDFarSegs);
	for (int32 R = 0; R < NR; ++R)
		for (int32 A = 0; A < RDFarSegs; ++A)
		{
			const double Ang = 2.0 * PI * A / RDFarSegs;
			const double X = Here.X + FMath::Cos(Ang) * RDFarRadii[R], Y = Here.Y + FMath::Sin(Ang) * RDFarRadii[R];
			FRDWSample S; Wild->Sample(X, Y, S, false);
			const bool bWater = S.WaterKind != 0;
			const float H = bWater ? FMath::Max(S.H, S.Water) : S.H;
			// (under the real ground, so the chunks draw over it; deeper where it lies under the chunks, by the way to the next ring)
			const double Gap = R + 1 < NR ? RDFarRadii[R + 1] - RDFarRadii[R] : 0.0;
			const float Sink = FarLandSink + (RDFarRadii[R] < RDFarUnderChunksM ? (float)(Gap * 0.06 * 100.0) : 0.f);
			V.Add(FVector(X * 100.0, Y * 100.0, Wild->ToZ(H) - Sink));
			Col.Add(bWater ? FarWaterColor : S.Color);
			N.Add(FVector::UpVector); UV.Add(FVector2D(X / 100.0, Y / 100.0)); Tg.Add(FProcMeshTangent(1.f, 0.f, 0.f));
		}
	// (the triangles' front up: UE's procedural mesh draws the side where cross(V1 - V0, V2 - V0) points away from the viewer, so
	// seen from above that cross points down (the ceilings' lesson, RDCeilings.cpp))
	for (int32 R = 0; R + 1 < NR; ++R)
		for (int32 A = 0; A < RDFarSegs; ++A)
		{
			const int32 A1 = (A + 1) % RDFarSegs;
			const int32 I00 = R * RDFarSegs + A, I01 = R * RDFarSegs + A1, I10 = (R + 1) * RDFarSegs + A, I11 = (R + 1) * RDFarSegs + A1;
			Tri.Append({ I00, I01, I10 }); Tri.Append({ I01, I11, I10 });
		}
	FarLand->CreateMeshSection_LinearColor(0, V, Tri, N, UV, Col, Tg, false);
	FarLand->SetMaterial(0, FarLandMaterial);
	FarLand->SetVisibility(true);
	FarLandAt = Here; ++FarLandBuilds;
	FarLandBuildMs = (float)((FPlatformTime::Seconds() - T0) * 1000.0);
	UE_LOG(LogRDSkyFar, Log, TEXT("RDFARLAND made round (%.0f, %.0f) m: %d points, %.1f ms"), Here.X, Here.Y, V.Num(), FarLandBuildMs);
}

FString ARDDungeonGenerator::GetFarLandState() const
{
	return FString::Printf(TEXT("%d|%d|%.0f|%.0f|%.1f|%d"), IsValid(FarLand) ? 1 : 0, IsValid(FarLand) && FarLand->IsVisible() ? 1 : 0, FarLandAt.X, FarLandAt.Y, FarLandBuildMs, FarLandBuilds);
}
