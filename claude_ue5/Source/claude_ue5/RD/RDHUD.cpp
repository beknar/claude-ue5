#include "RD/RDHUD.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDMonster.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"

static const FLinearColor RoomLit(0.80f, 0.69f, 0.50f, 0.95f);
static const FLinearColor RoomDim(0.30f, 0.32f, 0.36f, 0.55f);
static const FLinearColor HallLit(0.58f, 0.52f, 0.42f, 0.95f);
static const FLinearColor HallDim(0.24f, 0.26f, 0.29f, 0.50f);
static const FLinearColor Cyan(0.43f, 0.88f, 1.0f, 1.f);

void ARDHUD::Box(const FVector2D& A, const FVector2D& B, const FLinearColor& C)
{
	if (B.X <= A.X || B.Y <= A.Y) return;
	DrawRect(C, A.X, A.Y, B.X - A.X, B.Y - A.Y);
}

void ARDHUD::Frame(const FVector2D& A, const FVector2D& B, const FLinearColor& C, float T)
{
	DrawLine(A.X, A.Y, B.X, A.Y, C, T); DrawLine(B.X, A.Y, B.X, B.Y, C, T);
	DrawLine(B.X, B.Y, A.X, B.Y, C, T); DrawLine(A.X, B.Y, A.X, A.Y, C, T);
}

void ARDHUD::DrawPlayerArrow(const FVector2D& P, float Yaw, float Size)
{
	const float R = FMath::DegreesToRadians(Yaw);
	const FVector2D F(FMath::Cos(R), FMath::Sin(R)), Rt(-F.Y, F.X);
	const FVector2D Tip = P + F * Size, L = P - F * Size * 0.6f + Rt * Size * 0.6f, Rr = P - F * Size * 0.6f - Rt * Size * 0.6f;
	const FLinearColor C(1.f, 0.47f, 0.67f, 1.f);
	// filled by fanning lines, then outlined
	for (float U = 0.f; U <= 1.f; U += 0.08f) DrawLine(Tip.X, Tip.Y, FMath::Lerp(L.X, Rr.X, U), FMath::Lerp(L.Y, Rr.Y, U), C, 2.f);
	DrawLine(Tip.X, Tip.Y, L.X, L.Y, FLinearColor::White, 2.f); DrawLine(Tip.X, Tip.Y, Rr.X, Rr.Y, FLinearColor::White, 2.f);
	DrawLine(L.X, L.Y, Rr.X, Rr.Y, FLinearColor::White, 2.f);
}

void ARDHUD::DrawHUD()
{
	Super::DrawHUD();
	if (!Canvas) return;
	if (!Gen) for (TActorIterator<ARDDungeonGenerator> It(GetWorld()); It; ++It) { Gen = *It; break; }
	if (!Gen) return;
	APawn* P = GetOwningPawn();
	if (!P) return;
	const float Sc = Canvas->ClipY / 1080.f;
	const FVector L = P->GetActorLocation();
	const float Yaw = P->GetActorRotation().Yaw;
	UFont* Small = GEngine->GetSmallFont();
	UFont* Medium = GEngine->GetMediumFont();
	int32 Disc = 0, All = 0; Gen->GetDiscoveryStats(Disc, All);
	const float Now = GetWorld()->GetTimeSeconds();

	// ---- minimap (top right), north (+X) up: screen right = world +Y, screen up = world +X
	{
		const float Px = MinimapPixels * Sc, Mg = 24.f * Sc;
		const FVector2D S0(Canvas->ClipX - Mg - Px, Mg + 26.f * Sc), S1 = S0 + FVector2D(Px);
		Box(S0 - FVector2D(8.f * Sc, 34.f * Sc), S1 + FVector2D(8.f * Sc, 30.f * Sc), FLinearColor(0.04f, 0.05f, 0.07f, 0.72f));
		Box(S0, S1, FLinearColor(0.02f, 0.02f, 0.03f, 0.85f));
		const float Half = MinimapMeters * 50.f;
		// map frame: world X maps to screen -Y; draw in a rotated frame by swapping axes
		// (DrawMap works in an axis-aligned frame: we pass world (Y, -X) as the frame's (x, y))
		const FVector2D WMin(L.Y - Half, -L.X - Half), WMax(L.Y + Half, -L.X + Half);
		// temporarily remap the map data into the rotated frame by drawing with a helper generator view
		struct FRot { static FVector2D W(const FVector2D& V) { return FVector2D(V.Y, -V.X); } };
		{
			const float TS = Gen->TileSize;
			auto ToS = [&](const FVector2D& Wd) { const FVector2D Q = FRot::W(Wd); return S0 + (Q - WMin) / (WMax - WMin) * (S1 - S0); };
			auto Clip = [&](FVector2D A, FVector2D B, FVector2D& OA, FVector2D& OB)
			{
				const FVector2D Lo(FMath::Min(A.X, B.X), FMath::Min(A.Y, B.Y)), Hi(FMath::Max(A.X, B.X), FMath::Max(A.Y, B.Y));
				OA = FVector2D(FMath::Max(Lo.X, S0.X), FMath::Max(Lo.Y, S0.Y)); OB = FVector2D(FMath::Min(Hi.X, S1.X), FMath::Min(Hi.Y, S1.Y));
				return OB.X > OA.X && OB.Y > OA.Y;
			};
			for (const auto& KV : Gen->MapData)
			{
				const FRDSectionMap& M = KV.Value;
				for (const FRDMapRect& R : M.Rects)
				{
					FVector2D CA, CB;
					if (!Clip(ToS(FVector2D(R.Min) * TS), ToS(FVector2D(R.Max) * TS), CA, CB)) continue;
					Box(CA, CB, R.bCorridor ? (R.bDiscovered ? HallLit : HallDim) : (R.bDiscovered ? RoomLit : RoomDim));
				}
				for (const FVector2D& D : M.Doors)
				{
					const FVector2D Q = ToS(D);
					if (Q.X > S0.X && Q.Y > S0.Y && Q.X < S1.X && Q.Y < S1.Y) Box(Q - FVector2D(2.f * Sc), Q + FVector2D(2.f * Sc), FLinearColor(0.42f, 0.22f, 0.08f, 1.f));
				}
				const float Age = Now - M.GeneratedTime;
				if (M.GeneratedTime >= 0.f && Age < 4.f)
				{
					const FIntPoint T0 = Gen->SectionMinTile(M.Coord);
					FVector2D CA, CB;
					if (Clip(ToS(FVector2D(T0) * TS), ToS(FVector2D(T0 + FIntPoint(Gen->SectionTiles)) * TS), CA, CB))
					{
						const float Al = 1.f - Age / 4.f;
						Box(CA, CB, FLinearColor(Cyan.R, Cyan.G, Cyan.B, 0.22f * Al));
						Frame(CA, CB, FLinearColor(Cyan.R, Cyan.G, Cyan.B, Al), 2.f * Sc);
					}
				}
			}
			for (ARDMonster* Mo : Gen->GetMonsters())
			{
				const FVector Ml = Mo->GetActorLocation();
				if (FVector::Dist2D(Ml, L) > 2500.f) continue;     // sensed nearby
				const FVector2D Q = ToS(FVector2D(Ml.X, Ml.Y));
				if (Q.X > S0.X && Q.Y > S0.Y && Q.X < S1.X && Q.Y < S1.Y) Box(Q - FVector2D(3.f * Sc), Q + FVector2D(3.f * Sc), FLinearColor(0.95f, 0.15f, 0.12f, 1.f));
			}
		}
		Frame(S0, S1, FLinearColor(0.75f, 0.65f, 0.45f, 0.9f), 2.f * Sc);
		DrawPlayerArrow((S0 + S1) * 0.5f, Yaw - 90.f, 9.f * Sc);
		DrawText(TEXT("DUNGEON"), FLinearColor(0.92f, 0.86f, 0.72f), S0.X, S0.Y - 28.f * Sc, Small, Sc * 1.1f);
		const FString Cnt = FString::Printf(TEXT("%d / %d rooms"), Disc, All);
		float Tw, Th; GetTextSize(Cnt, Tw, Th, Small, Sc * 1.1f);
		DrawText(Cnt, FLinearColor(0.92f, 0.86f, 0.72f), S1.X - Tw, S0.Y - 28.f * Sc, Small, Sc * 1.1f);
		DrawText(TEXT("N"), FLinearColor(0.92f, 0.86f, 0.72f), (S0.X + S1.X) * 0.5f - 4.f * Sc, S0.Y + 2.f * Sc, Small, Sc);
		DrawText(TEXT("M  map"), FLinearColor(0.7f, 0.68f, 0.62f), S0.X, S1.Y + 6.f * Sc, Small, Sc);
	}

	// ---- new section banner
	if (Now - Gen->LastRevealTime < 3.5f)
	{
		const float A = FMath::Clamp(FMath::Min((Now - Gen->LastRevealTime) / 0.3f, (3.5f - (Now - Gen->LastRevealTime)) / 0.8f), 0.f, 1.f);
		const FString T = TEXT("▲ NEW DUNGEON SECTION GENERATED");
		float Tw, Th; GetTextSize(T, Tw, Th, Medium, Sc * 1.4f);
		DrawText(T, FLinearColor(Cyan.R, Cyan.G, Cyan.B, A), (Canvas->ClipX - Tw) * 0.5f, 90.f * Sc, Medium, Sc * 1.4f);
	}

	// ---- interaction prompt
	const FString What = Gen->DescribeNearest(L);
	if (!What.IsEmpty() && !Gen->bMapOpen)
	{
		const FString T = FString::Printf(TEXT("[F]  %s"), *What);
		float Tw, Th; GetTextSize(T, Tw, Th, Medium, Sc * 1.2f);
		const float X = (Canvas->ClipX - Tw) * 0.5f, Y = Canvas->ClipY * 0.72f;
		Box(FVector2D(X - 14.f * Sc, Y - 8.f * Sc), FVector2D(X + Tw + 14.f * Sc, Y + Th + 8.f * Sc), FLinearColor(0.03f, 0.03f, 0.04f, 0.6f));
		DrawText(T, FLinearColor(0.95f, 0.9f, 0.78f), X, Y, Medium, Sc * 1.2f);
	}

	// ---- full map (M): everything discovered, fitted to the screen, north up
	if (Gen->bMapOpen)
	{
		Box(FVector2D(0, 0), FVector2D(Canvas->ClipX, Canvas->ClipY), FLinearColor(0.02f, 0.02f, 0.03f, 0.96f));
		const float TS = Gen->TileSize;
		FBox2D Wb(ForceInit);
		Wb += FVector2D(L.Y, -L.X);
		for (const auto& KV : Gen->MapData)
			for (const FRDMapRect& R : KV.Value.Rects)
				if (R.bDiscovered) { Wb += FVector2D(R.Min.Y * TS, -R.Max.X * TS); Wb += FVector2D(R.Max.Y * TS, -R.Min.X * TS); }
		Wb = Wb.ExpandBy(1500.f);
		const FVector2D A0(80.f * Sc, 110.f * Sc), A1(Canvas->ClipX - 80.f * Sc, Canvas->ClipY - 90.f * Sc);
		const float K = FMath::Min((A1.X - A0.X) / Wb.GetSize().X, (A1.Y - A0.Y) / Wb.GetSize().Y);
		const FVector2D Off = (A0 + A1) * 0.5f - Wb.GetCenter() * K;
		auto ToS = [&](const FVector2D& Wd) { return FVector2D(Wd.Y, -Wd.X) * K + Off; };
		for (const auto& KV : Gen->MapData)
		{
			const FRDSectionMap& M = KV.Value;
			for (const FRDMapRect& R : M.Rects)
			{
				if (!R.bDiscovered) continue;
				const FVector2D P0 = ToS(FVector2D(R.Min) * TS), P1 = ToS(FVector2D(R.Max) * TS);
				const FVector2D Lo(FMath::Min(P0.X, P1.X), FMath::Min(P0.Y, P1.Y)), Hi(FMath::Max(P0.X, P1.X), FMath::Max(P0.Y, P1.Y));
				Box(Lo, Hi, R.bCorridor ? HallLit : RoomLit);
				if (!R.bCorridor) Frame(Lo, Hi, FLinearColor(0.32f, 0.24f, 0.14f, 0.95f), 1.5f);
				if (!R.bCorridor && R.Kind != ERDRoomKind::Junction)
				{
					// full name when it fits, else a short code (legend below)
					FString N = ARDDungeonGenerator::KindName(R.Kind);
					float Tw, Th; GetTextSize(N, Tw, Th, Small, Sc * 0.9f);
					if (Tw >= Hi.X - Lo.X - 4.f) { N = KindCode(R.Kind); GetTextSize(N, Tw, Th, Small, Sc * 0.85f); }
					if (Tw < Hi.X - Lo.X - 2.f && Th < Hi.Y - Lo.Y) DrawText(N, FLinearColor(0.22f, 0.15f, 0.08f), (Lo.X + Hi.X - Tw) * 0.5f, (Lo.Y + Hi.Y - Th) * 0.5f, Small, Sc * 0.85f);
				}
			}
			for (const FVector2D& D : M.Doors)
			{
				bool bShow = false;
				for (const FRDMapRect& R : M.Rects)
					if (R.bDiscovered && !R.bCorridor && D.X >= R.Min.X * TS - TS && D.Y >= R.Min.Y * TS - TS && D.X <= R.Max.X * TS + TS && D.Y <= R.Max.Y * TS + TS) { bShow = true; break; }
				if (bShow) { const FVector2D Q = ToS(D); Box(Q - FVector2D(2.5f * Sc), Q + FVector2D(2.5f * Sc), FLinearColor(0.45f, 0.25f, 0.1f, 1.f)); }
			}
		}
		DrawPlayerArrow(ToS(FVector2D(L.X, L.Y)), Yaw - 90.f, 12.f * Sc);
		DrawText(TEXT("DUNGEON MAP"), FLinearColor(0.92f, 0.86f, 0.72f), 80.f * Sc, 40.f * Sc, Medium, Sc * 1.6f);
		const FString Sub = FString::Printf(TEXT("%d rooms discovered of %d generated  ·  %d sections  ·  M  close"), Disc, All, Gen->MapData.Num());
		DrawText(Sub, FLinearColor(0.75f, 0.72f, 0.65f), 82.f * Sc, 78.f * Sc, Small, Sc * 1.1f);
		// legend: room codes
		float Y = Canvas->ClipY - 64.f * Sc, X = 82.f * Sc;
		for (int32 Kd = (int32)ERDRoomKind::Hall; Kd < (int32)ERDRoomKind::Junction; ++Kd)
		{
			const FString E = FString::Printf(TEXT("%s %s"), *KindCode((ERDRoomKind)Kd), *ARDDungeonGenerator::KindName((ERDRoomKind)Kd));
			float Tw, Th; GetTextSize(E, Tw, Th, Small, Sc);
			if (X + Tw > Canvas->ClipX - 80.f * Sc) { X = 82.f * Sc; Y += 22.f * Sc; }
			DrawText(E, FLinearColor(0.75f, 0.72f, 0.65f), X, Y, Small, Sc);
			X += Tw + 24.f * Sc;
		}
	}
}

FString ARDHUD::KindCode(ERDRoomKind K)
{
	switch (K)
	{
	case ERDRoomKind::Hall: return TEXT("H"); case ERDRoomKind::Barracks: return TEXT("Ba"); case ERDRoomKind::Prison: return TEXT("P");
	case ERDRoomKind::Torture: return TEXT("To"); case ERDRoomKind::Storeroom: return TEXT("St"); case ERDRoomKind::Armory: return TEXT("Ar");
	case ERDRoomKind::Kitchen: return TEXT("K"); case ERDRoomKind::Library: return TEXT("L"); case ERDRoomKind::Chapel: return TEXT("Ch");
	case ERDRoomKind::Crypt: return TEXT("Cr"); case ERDRoomKind::Treasury: return TEXT("Tr"); case ERDRoomKind::GuardRoom: return TEXT("G");
	case ERDRoomKind::Forge: return TEXT("F"); default: return TEXT("");
	}
}
