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
// (later the same day: "if it's distant land, it should be textured the same way it would be textured when approached and
// generated": with bFarLandAsGround it is drawn as the chunks draw the ground: WildGroundMaterial with their vertex data, its
// normals from its heights, its water in their water materials; the flat colour, fogged to the fog's pale colour from
// 20 km on, had read as a white strip under a cloudless sky)
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
	float RDFarSmooth(float A, float B, float X) { const float T = FMath::Clamp((X - A) / (B - A), 0.f, 1.f); return T * T * (3.f - 2.f * T); }
}

void ARDDungeonGenerator::TickFarLand(const FVector& Cam)
{
	// (the list of 2026-11-10 "textured the same way it would be textured when approached": the chunks' ground material)
	const bool bAsGround = bFarLandAsGround && WildGroundMaterial != nullptr;
	UMaterialInterface* LandMat = bAsGround ? WildGroundMaterial.Get() : FarLandMaterial.Get();
	const bool bOn = bWild && IsWildReady() && LandMat != nullptr;
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
	const int32 Nv = NR * RDFarSegs;
	TArray<FVector> V; TArray<int32> Tri; TArray<FVector> N; TArray<FVector2D> UV, UV1, UV2, UV3; TArray<FLinearColor> Col; TArray<FProcMeshTangent> Tg;
	TArray<FRDWSample> Smp; Smp.SetNum(Nv);
	TArray<FVector> Bare; Bare.SetNumUninitialized(Nv);       // (each point unsunk: the normals')
	TArray<float> SinkOf; SinkOf.SetNumUninitialized(Nv);
	V.Reserve(Nv); Col.Reserve(Nv); N.Reserve(Nv); UV.Reserve(Nv); Tg.Reserve(Nv);
	for (int32 R = 0; R < NR; ++R)
		for (int32 A = 0; A < RDFarSegs; ++A)
		{
			const int32 K = R * RDFarSegs + A;
			const double Ang = 2.0 * PI * A / RDFarSegs;
			const double X = Here.X + FMath::Cos(Ang) * RDFarRadii[R], Y = Here.Y + FMath::Sin(Ang) * RDFarRadii[R];
			FRDWSample& S = Smp[K]; Wild->Sample(X, Y, S, false);
			const bool bWater = S.WaterKind != 0;
			// (as ground the bed is drawn and the water over it, as the chunks do; the flat colour drew the water's surface)
			const float H = bWater && !bAsGround ? FMath::Max(S.H, S.Water) : S.H;
			// (under the real ground, so the chunks draw over it; deeper where it lies under the chunks, by the way to the next ring)
			const double Gap = R + 1 < NR ? RDFarRadii[R + 1] - RDFarRadii[R] : 0.0;
			const float Sink = FarLandSink + (RDFarRadii[R] < RDFarUnderChunksM ? (float)(Gap * 0.06 * 100.0) : 0.f);
			SinkOf[K] = Sink;
			Bare[K] = FVector(X * 100.0, Y * 100.0, Wild->ToZ(H));
			V.Add(Bare[K] - FVector(0.f, 0.f, Sink));
		}
	// (the chunks' vertex data, point by point: RDWildChunk.cpp's ground mesh)
	for (int32 R = 0; R < NR; ++R)
		for (int32 A = 0; A < RDFarSegs; ++A)
		{
			const int32 K = R * RDFarSegs + A;
			const FRDWSample& Q = Smp[K];
			if (!bAsGround)
			{
				Col.Add(Q.WaterKind ? FarWaterColor : Q.Color);
				N.Add(FVector::UpVector); UV.Add(FVector2D(Bare[K].X / 10000.0, Bare[K].Y / 10000.0)); Tg.Add(FProcMeshTangent(1.f, 0.f, 0.f));
				continue;
			}
			// (the normal from the neighbours: out along the ring's radius, round it anticlockwise)
			const int32 Ri = FMath::Min(R + 1, NR - 1), Ro = FMath::Max(R - 1, 0);
			const int32 Aa = (A + 1) % RDFarSegs, Ab = (A + RDFarSegs - 1) % RDFarSegs;
			FVector Nr = FVector::CrossProduct(Bare[Ri * RDFarSegs + A] - Bare[Ro * RDFarSegs + A], Bare[R * RDFarSegs + Aa] - Bare[R * RDFarSegs + Ab]).GetSafeNormal();
			if (Nr.Z < 0.f) Nr = -Nr;
			if (Nr.IsNearlyZero()) Nr = FVector::UpVector;
			N.Add(Nr);
			Tg.Add(FProcMeshTangent((FVector(1, 0, 0) - Nr * Nr.X).GetSafeNormal(), false));
			const float Slope = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp((float)Nr.Z, 0.f, 1.f)));
			const float Rk = FMath::Max(Q.Rock, RDFarSmooth(31.f, 46.f, Slope)) * (Q.WaterKind ? 0.3f : 1.f);
			const float Sn = Q.Snow * (1.f - RDFarSmooth(38.f, 58.f, Slope));
			FLinearColor C = Q.Color;
			// (the forest's crowns, which the far land does not grow)
			if (Q.WaterKind == 0) C = FMath::Lerp(C, FarForestColor, FMath::Clamp(Q.Canopy * FarForestShare, 0.f, 1.f));
			if (Rk > Q.Rock && Q.WaterKind == 0) C = FMath::Lerp(C, Q.RockColor, (Rk - Q.Rock) * 0.85f);
			if (Sn < Q.Snow && Q.WaterKind == 0) C = FMath::Lerp(C, Q.RockColor, (Q.Snow - Sn) * 0.7f);
			// (the ground material glows by the colour's alpha, the lava: across a far triangle kilometres wide one lava sample
			// smeared an orange glow over a whole hill (884 horizonprobe's pictures): the far land has none)
			C.A = 0.f;
			Col.Add(C);
			UV.Add(FVector2D(Q.FieldAng / PI, Q.FieldCrop >= 0 ? (Q.FieldCrop + 0.5) / double(FRDWildWorld::MaxCrops) : 0.0));
			UV1.Add(FVector2D(Rk, Sn));
			UV2.Add(FVector2D(Q.Sand, Q.Mud));
			UV3.Add(FVector2D(Q.Road, Q.FieldCrop >= 0 ? Q.Field * (1.f - Q.Road) : 0.f));
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
	if (bAsGround) FarLand->CreateMeshSection_LinearColor(0, V, Tri, N, UV, UV1, UV2, UV3, Col, Tg, false);
	else FarLand->CreateMeshSection_LinearColor(0, V, Tri, N, UV, Col, Tg, false);
	FarLand->SetMaterial(0, LandMat);
	// ---- water over the far land's quads, as the chunks lay them (RDWildChunk.cpp): a quad with water at a corner is a
	// flat sheet at its water's level (the land above it hides it past the shore); sunk with its ring, as the land is
	FarLandWaterQuads = 0;
	for (int32 Sec = 1; Sec <= 4; ++Sec) if (FarLand->GetNumSections() > Sec) FarLand->ClearMeshSection(Sec);
	if (bAsGround)
	{
		struct FRDFarWater { TArray<FVector> V; TArray<int32> T; TArray<FVector2D> UV; TArray<FLinearColor> C; };
		FRDFarWater Wt[4];
		for (int32 R = 0; R + 1 < NR; ++R)
			for (int32 A = 0; A < RDFarSegs; ++A)
			{
				const int32 A1 = (A + 1) % RDFarSegs;
				const int32 Ks[4] = { R * RDFarSegs + A, R * RDFarSegs + A1, (R + 1) * RDFarSegs + A, (R + 1) * RDFarSegs + A1 };
				int32 Kind = 0; float Lv = -1e9f;
				for (const int32 K : Ks) { const FRDWSample& Q = Smp[K]; if (Q.WaterKind) { Kind = Q.WaterKind; Lv = FMath::Max(Lv, Q.Water); } }
				// (water only: a far quad is up to 25 km across, and a lava sample at one corner spread a glowing sheet over a whole hill
				// (884 horizonprobe's pictures); the far lava is the ground's own colour)
				if (!Kind) continue;
				const int32 Sec = !Kind ? 3 : (Kind == 1 ? 1 : (Kind == 6 ? 2 : 0));
				FRDFarWater& W = Wt[Sec];
				const int32 Base = W.V.Num();
				for (const int32 K : Ks)
				{
					const FRDWSample& Q = Smp[K];
					// (at a dry corner the sheet goes down under its ground, not out at the water's level: a quad is up to 25 km across,
					// and a mountain lake's level held over the lowland at its other corners would float there)
					const float Hv = Kind ? (Q.WaterKind ? Q.Water : FMath::Min(Lv, Q.H - 1.f)) : Q.H;
					const float Zw = Kind ? Wild->ToZ(Hv) + (Kind == 1 ? 0.f : 2.f) : Bare[K].Z + 6.f;
					W.V.Add(FVector(Bare[K].X, Bare[K].Y, Zw - SinkOf[K]));
					// (one repeat every 16 m from the continent's corner, as the chunks' water)
					W.UV.Add(FVector2D((Bare[K].X / 100.0 - Wild->Xs) / 16.0, (Bare[K].Y / 100.0 - Wild->Yw) / 16.0));
					W.C.Add(FLinearColor(FMath::Clamp((Q.Water - Q.H) / 8.f, 0.f, 1.f), Q.Lava, 0.f, 1.f));
				}
				// (the land's winding: front up)
				W.T.Append({ Base, Base + 1, Base + 2 }); W.T.Append({ Base + 1, Base + 3, Base + 2 });
				++FarLandWaterQuads;
			}
		UMaterialInterface* Wm[4] = { WildWaterMaterial, WildSeaMaterial ? WildSeaMaterial.Get() : WildWaterMaterial.Get(), WildSpringMaterial ? WildSpringMaterial.Get() : WildWaterMaterial.Get(), WildLavaMaterial };
		for (int32 S = 0; S < 4; ++S)
		{
			if (Wt[S].V.Num() == 0 || !Wm[S]) continue;
			TArray<FVector> Up; Up.Init(FVector::UpVector, Wt[S].V.Num());
			FarLand->CreateMeshSection_LinearColor(1 + S, Wt[S].V, Wt[S].T, Up, Wt[S].UV, TArray<FVector2D>(), TArray<FVector2D>(), TArray<FVector2D>(), Wt[S].C, TArray<FProcMeshTangent>(), false);
			FarLand->SetMaterial(1 + S, Wm[S]);
		}
	}
	FarLand->SetVisibility(true);
	FarLandAt = Here; ++FarLandBuilds;
	FarLandBuildMs = (float)((FPlatformTime::Seconds() - T0) * 1000.0);
	UE_LOG(LogRDSkyFar, Log, TEXT("RDFARLAND made round (%.0f, %.0f) m: %d points, %.1f ms"), Here.X, Here.Y, V.Num(), FarLandBuildMs);
}

FString ARDDungeonGenerator::GetFarLandState() const
{
	// "made|shown|x|y|ms|builds|<its land's material>|<water quads>"
	const UMaterialInterface* M = IsValid(FarLand) ? FarLand->GetMaterial(0) : nullptr;
	return FString::Printf(TEXT("%d|%d|%.0f|%.0f|%.1f|%d|%s|%d"), IsValid(FarLand) ? 1 : 0, IsValid(FarLand) && FarLand->IsVisible() ? 1 : 0, FarLandAt.X, FarLandAt.Y, FarLandBuildMs, FarLandBuilds,
		M ? *M->GetName() : TEXT("none"), FarLandWaterQuads);
}
