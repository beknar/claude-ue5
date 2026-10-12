#include "IV/IVHUD.h"
#include "IV/IVVillageGenerator.h"
#include "IV/IVPlayerController.h"
#include "CanvasItem.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "RenderUtils.h"

static const FLinearColor Cyan(0.43f, 0.88f, 1.0f, 1.f);
static const FLinearColor Ink(0.93f, 0.89f, 0.78f, 1.f);

static FLinearColor Shade(const FLinearColor& C, float K, float A = 1.f) { return FLinearColor(C.R * K, C.G * K, C.B * K, C.A * A); }

FVector2D AIVHUD::Project(const FVector& W) const
{
	const FVector2D P(W.X, W.Y);
	return FVector2D(FVector2D::DotProduct(P, IsoRight), -(FVector2D::DotProduct(P, IsoUp) * IsoSin + W.Z * IsoCos));
}

void AIVHUD::Poly(const TArray<FVector2D>& In, const FLinearColor& C)
{
	if (In.Num() < 3 || C.A <= 0.003f) return;
	// Sutherland-Hodgman against the clip box (the polygons are convex)
	TArray<FVector2D, TInlineAllocator<16>> A, B;
	A.Append(In);
	for (int32 Edge = 0; Edge < 4 && A.Num() >= 3; ++Edge)
	{
		B.Reset();
		auto Inside = [&](const FVector2D& P) { return Edge == 0 ? P.X >= ClipBox.Min.X : Edge == 1 ? P.X <= ClipBox.Max.X : Edge == 2 ? P.Y >= ClipBox.Min.Y : P.Y <= ClipBox.Max.Y; };
		auto Cut = [&](const FVector2D& P, const FVector2D& Q)
		{
			float T;
			if (Edge < 2) { const float X = Edge == 0 ? ClipBox.Min.X : ClipBox.Max.X; T = (X - P.X) / (Q.X - P.X); }
			else { const float Y = Edge == 2 ? ClipBox.Min.Y : ClipBox.Max.Y; T = (Y - P.Y) / (Q.Y - P.Y); }
			return P + (Q - P) * T;
		};
		for (int32 I = 0; I < A.Num(); ++I)
		{
			const FVector2D& P = A[I]; const FVector2D& Q = A[(I + 1) % A.Num()];
			const bool Pi = Inside(P), Qi = Inside(Q);
			if (Pi) B.Add(P);
			if (Pi != Qi) B.Add(Cut(P, Q));
		}
		A = B;
	}
	for (int32 I = 1; I + 1 < A.Num(); ++I)
	{
		FCanvasUVTri T;
		T.V0_Pos = A[0]; T.V1_Pos = A[I]; T.V2_Pos = A[I + 1];
		T.V0_UV = T.V1_UV = T.V2_UV = FVector2D::ZeroVector;
		T.V0_Color = T.V1_Color = T.V2_Color = C;
		Tris.Add(T);
	}
}

void AIVHUD::Quad(const FVector& A, const FVector& B, const FVector& Cc, const FVector& D, const FLinearColor& C)
{
	Poly({ ToScreen(A), ToScreen(B), ToScreen(Cc), ToScreen(D) }, C);
}

void AIVHUD::Tri3(const FVector& A, const FVector& B, const FVector& Cc, const FLinearColor& C)
{
	Poly({ ToScreen(A), ToScreen(B), ToScreen(Cc) }, C);
}

void AIVHUD::Disc(const FVector& Center, float Radius, const FLinearColor& C, int32 Sides, float Squash)
{
	const FVector2D O = ToScreen(Center);
	const float Rx = Radius * MapScale, Ry = Rx * (Squash < 0.f ? 1.f : Squash);
	if (O.X + Rx < ClipBox.Min.X || O.X - Rx > ClipBox.Max.X || O.Y + Ry < ClipBox.Min.Y || O.Y - Ry > ClipBox.Max.Y) return;
	TArray<FVector2D> P; P.Reserve(Sides);
	for (int32 I = 0; I < Sides; ++I) { const float A = 2.f * PI * I / Sides; P.Add(O + FVector2D(FMath::Cos(A) * Rx, FMath::Sin(A) * Ry)); }
	Poly(P, C);
}

void AIVHUD::Rect(const FVector2D& A, const FVector2D& B, const FLinearColor& C)
{
	if (B.X <= A.X || B.Y <= A.Y) return;
	DrawRect(C, A.X, A.Y, B.X - A.X, B.Y - A.Y);
}

void AIVHUD::Flush()
{
	if (Tris.Num() > 0 && Canvas)
	{
		// one batch, alpha blended (shadows, fading new sections)
		FCanvasTriangleItem Item(FVector2D::ZeroVector, FVector2D::ZeroVector, FVector2D::ZeroVector, GWhiteTexture);
		Item.TriangleList = MoveTemp(Tris);
		Item.BlendMode = SE_BLEND_Translucent;
		Canvas->DrawItem(Item);
	}
	Tris.Reset();
}

void AIVHUD::Frame(const FVector2D& A, const FVector2D& B, const FLinearColor& C, float T)
{
	DrawLine(A.X, A.Y, B.X, A.Y, C, T); DrawLine(B.X, A.Y, B.X, B.Y, C, T);
	DrawLine(B.X, B.Y, A.X, B.Y, C, T); DrawLine(A.X, B.Y, A.X, A.Y, C, T);
}

void AIVHUD::DrawRoad(const FIVMapRoad& R, bool bOutline)
{
	static const FLinearColor Fill[4] = { FLinearColor(0.66f, 0.56f, 0.38f), FLinearColor(0.74f, 0.65f, 0.46f), FLinearColor(0.70f, 0.60f, 0.42f), FLinearColor(0.62f, 0.60f, 0.56f) };
	const FLinearColor C = bOutline ? FLinearColor(0.30f, 0.24f, 0.15f, 0.9f) : Fill[FMath::Min<int32>(R.Type, 3)];
	const float Hw = R.HalfWidth + (bOutline ? FMath::Max(40.f, 1.2f / MapScale) : 0.f);
	for (int32 I = 0; I + 1 < R.Points.Num(); ++I)
	{
		const FVector2D A = R.Points[I], B = R.Points[I + 1];
		const FVector2D N = FVector2D(-(B - A).Y, (B - A).X).GetSafeNormal() * Hw;
		Quad(FVector(A + N, 0), FVector(B + N, 0), FVector(B - N, 0), FVector(A - N, 0), C);
		Disc(FVector(B, 0), Hw, C, 8, IsoSin);
	}
}

void AIVHUD::DrawBuilding(const FIVMapBuilding& B, float Alpha)
{
	// style colours: walls, roof (lit slope / shaded slope)
	static const FLinearColor Wall[3] = { FLinearColor(0.80f, 0.74f, 0.60f), FLinearColor(0.60f, 0.44f, 0.29f), FLinearColor(0.68f, 0.68f, 0.66f) };
	static const FLinearColor Roof[3] = { FLinearColor(0.84f, 0.69f, 0.31f), FLinearColor(0.50f, 0.30f, 0.19f), FLinearColor(0.42f, 0.46f, 0.55f) };
	const int32 St = FMath::Min<int32>((int32)B.Style, 2);
	FLinearColor Wc = Wall[St], Rc = Roof[St];
	if (B.Kind == EIVBuildingKind::Church) { Wc = FLinearColor(0.74f, 0.73f, 0.70f); Rc = FLinearColor(0.33f, 0.40f, 0.55f); }
	else if (B.Kind == EIVBuildingKind::Tavern) Rc = FLinearColor(0.66f, 0.26f, 0.18f);
	else if (B.Kind == EIVBuildingKind::Manor) Rc = FLinearColor(0.55f, 0.22f, 0.26f);
	else if (B.Kind == EIVBuildingKind::Barn || B.Kind == EIVBuildingKind::Storehouse) Rc = Shade(Rc, 0.86f);
	Wc.A = Alpha; Rc.A = Alpha;
	const float Yr = FMath::DegreesToRadians(B.Yaw);
	const FVector2D Fx(FMath::Cos(Yr), FMath::Sin(Yr)), Fy(-FMath::Sin(Yr), FMath::Cos(Yr));
	const FVector2D ToCam = -IsoUp;
	auto Pt = [&](float X, float Y, float Z) { return FVector(B.Center + Fx * X + Fy * Y, Z); };
	const float Hx = B.Half.X, Hy = B.Half.Y, H = B.WallHeight, Rh = B.RoofHeight, Ov = 45.f;
	auto WallQuad = [&](const FVector2D& N, const FVector& A, const FVector& Bb, float Z0, float Z1)
	{
		if (FVector2D::DotProduct(N, ToCam) <= 0.02f) return;
		const float K = 0.80f + 0.20f * FMath::Max(0.f, FVector2D::DotProduct(N, IsoRight));
		Quad(FVector(A.X, A.Y, Z0), FVector(Bb.X, Bb.Y, Z0), FVector(Bb.X, Bb.Y, Z1), FVector(A.X, A.Y, Z1), Shade(Wc, K));
	};
	auto Box = [&](float X0, float X1, float Y0, float Y1, float Z0, float Z1)
	{
		WallQuad(Fx, Pt(X1, Y0, 0), Pt(X1, Y1, 0), Z0, Z1); WallQuad(-Fx, Pt(X0, Y1, 0), Pt(X0, Y0, 0), Z0, Z1);
		WallQuad(Fy, Pt(X1, Y1, 0), Pt(X0, Y1, 0), Z0, Z1); WallQuad(-Fy, Pt(X0, Y0, 0), Pt(X1, Y0, 0), Z0, Z1);
	};
	Box(-Hx, Hx, -Hy, Hy, 0.f, H);
	// gable roof: two slopes, the far one first; the gable end facing the camera
	const FVector2D Ax = B.bRidgeAlongY ? Fy : Fx;            // ridge direction
	const FVector2D Cr = B.bRidgeAlongY ? Fx : Fy;            // across the ridge
	const float La = (B.bRidgeAlongY ? Hy : Hx), Lc = (B.bRidgeAlongY ? Hx : Hy);
	auto Rp = [&](float Along, float Across, float Z) { return FVector(B.Center + Ax * Along + Cr * Across, Z); };
	for (int32 E = -1; E <= 1; E += 2)
		if (FVector2D::DotProduct(Ax * (float)E, ToCam) > 0.02f)
			Tri3(Rp(E * La, -Lc, H), Rp(E * La, Lc, H), Rp(E * La, 0, H + Rh), Shade(Wc, 0.80f + 0.20f * FMath::Max(0.f, FVector2D::DotProduct(Ax * (float)E, IsoRight))));
	const int32 FarSide = FVector2D::DotProduct(Cr, ToCam) > 0.f ? -1 : 1;
	for (int32 Pass = 0; Pass < 2; ++Pass)
	{
		const float Sd = (Pass == 0 ? FarSide : -FarSide);
		const float K = 0.78f + 0.30f * FMath::Max(0.f, FVector2D::DotProduct(Cr * Sd, IsoRight)) + (Pass == 1 ? 0.06f : 0.f);
		Quad(Rp(-La - Ov, Sd * (Lc + Ov), H - Ov * 0.6f), Rp(La + Ov, Sd * (Lc + Ov), H - Ov * 0.6f), Rp(La + Ov, 0, H + Rh), Rp(-La - Ov, 0, H + Rh), Shade(Rc, K));
	}
	if (B.TowerHeight > 0.f)
	{
		// church tower on the front (+X) end: a square shaft and a pyramid roof
		const float S = Hy, X1 = Hx, X0 = Hx - 2.f * S;
		Box(X0, X1, -S, S, 0.f, B.TowerHeight);
		const FVector Apex = Pt((X0 + X1) * 0.5f, 0, B.TowerHeight + S * 2.2f);
		const FVector Cn[4] = { Pt(X0 - Ov, -S - Ov, B.TowerHeight), Pt(X1 + Ov, -S - Ov, B.TowerHeight), Pt(X1 + Ov, S + Ov, B.TowerHeight), Pt(X0 - Ov, S + Ov, B.TowerHeight) };
		const FVector2D Ns[4] = { -Fy, Fx, Fy, -Fx };
		for (int32 Pass = 0; Pass < 2; ++Pass)
			for (int32 I = 0; I < 4; ++I)
			{
				const bool bNear = FVector2D::DotProduct(Ns[I], ToCam) > 0.f;
				if (bNear != (Pass == 1)) continue;
				Tri3(Cn[I], Cn[(I + 1) % 4], Apex, Shade(Rc, 0.8f + 0.3f * FMath::Max(0.f, FVector2D::DotProduct(Ns[I], IsoRight))));
			}
	}
}

void AIVHUD::DrawTree(const FIVMapTree& T)
{
	const FVector G(T.P, 0.f);
	Disc(G + FVector(IsoRight * (-T.Radius * 0.25f), 0.f), T.Radius * 0.95f, FLinearColor(0.10f, 0.18f, 0.08f, 0.45f), 8, IsoSin);
	if (T.Type == 1)
	{
		const FLinearColor C(0.16f, 0.36f, 0.22f);
		const FVector R3(IsoRight * T.Radius * 0.8f, 0.f);
		Tri3(G - R3 + FVector(0, 0, T.Height * 0.18f), G + R3 + FVector(0, 0, T.Height * 0.18f), G + FVector(0, 0, T.Height), C);
		Tri3(G + FVector(0, 0, T.Height * 0.18f), G + R3 + FVector(0, 0, T.Height * 0.18f), G + FVector(0, 0, T.Height), Shade(C, 1.25f));
		return;
	}
	const FLinearColor C = T.Type == 2 ? FLinearColor(0.42f, 0.62f, 0.24f) : T.Type == 3 ? FLinearColor(0.30f, 0.50f, 0.22f) : FLinearColor(0.22f, 0.46f, 0.20f);
	const FVector Top = G + FVector(0, 0, T.Type == 3 ? T.Radius * 0.6f : T.Height * 0.62f);
	if (T.Type != 3) Quad(G + FVector(IsoRight * -18.f, 0.f), G + FVector(IsoRight * 18.f, 0.f), Top + FVector(IsoRight * 18.f, 0.f), Top + FVector(IsoRight * -18.f, 0.f), FLinearColor(0.33f, 0.24f, 0.15f));
	Disc(Top, T.Radius, Shade(C, 0.8f), 9);
	Disc(Top + FVector(IsoRight * (T.Radius * 0.22f), T.Radius * 0.28f), T.Radius * 0.68f, Shade(C, 1.18f), 8);
}

void AIVHUD::DrawProp(const FIVMapProp& P)
{
	const FVector G(P.P, 0.f);
	const float Yr = FMath::DegreesToRadians(P.Yaw);
	const FVector Fx(FMath::Cos(Yr), FMath::Sin(Yr), 0.f), Fy(-FMath::Sin(Yr), FMath::Cos(Yr), 0.f);
	switch (P.Type)
	{
	case 0:      // well
		Disc(G + FVector(0, 0, 60), 130.f, FLinearColor(0.55f, 0.55f, 0.53f), 10, IsoSin);
		Disc(G + FVector(0, 0, 60), 80.f, FLinearColor(0.16f, 0.26f, 0.36f), 8, IsoSin);
		Quad(G + Fy * -120.f + FVector(0, 0, 260), G + Fy * 120.f + FVector(0, 0, 260), G + Fy * 120.f + Fx * 60.f + FVector(0, 0, 330), G + Fy * -120.f + Fx * 60.f + FVector(0, 0, 330), FLinearColor(0.45f, 0.28f, 0.17f));
		break;
	case 1:      // market stall: posts and a striped awning
	{
		const bool bRed = (FMath::RoundToInt(P.P.X * 0.013f + P.P.Y * 0.007f) & 1) != 0;
		const FLinearColor Aw = bRed ? FLinearColor(0.78f, 0.22f, 0.18f) : FLinearColor(0.90f, 0.84f, 0.66f);
		Quad(G - Fx * 110.f - Fy * 160.f, G + Fx * 110.f - Fy * 160.f, G + Fx * 110.f + Fy * 160.f, G - Fx * 110.f + Fy * 160.f, FLinearColor(0.42f, 0.30f, 0.19f));
		Quad(G - Fx * 130.f - Fy * 180.f + FVector(0, 0, 240), G + Fx * 130.f - Fy * 180.f + FVector(0, 0, 200), G + Fx * 130.f + Fy * 180.f + FVector(0, 0, 200), G - Fx * 130.f + Fy * 180.f + FVector(0, 0, 240), Aw);
		Quad(G - Fx * 130.f - Fy * 60.f + FVector(0, 0, 241), G + Fx * 130.f - Fy * 60.f + FVector(0, 0, 201), G + Fx * 130.f + Fy * 60.f + FVector(0, 0, 201), G - Fx * 130.f + Fy * 60.f + FVector(0, 0, 241), bRed ? FLinearColor(0.92f, 0.86f, 0.70f) : FLinearColor(0.30f, 0.44f, 0.66f));
		break;
	}
	case 2:      // cart
		Quad(G - Fx * 120.f - Fy * 60.f + FVector(0, 0, 70), G + Fx * 120.f - Fy * 60.f + FVector(0, 0, 70), G + Fx * 120.f + Fy * 60.f + FVector(0, 0, 70), G - Fx * 120.f + Fy * 60.f + FVector(0, 0, 70), FLinearColor(0.46f, 0.31f, 0.18f));
		break;
	case 3:      // haystack
		Disc(G + FVector(0, 0, 70), 120.f, FLinearColor(0.80f, 0.68f, 0.28f), 8);
		Disc(G + FVector(IsoRight * 25.f, 110.f), 75.f, FLinearColor(0.90f, 0.79f, 0.38f), 7);
		break;
	case 4:      // statue / cross
		Quad(G + FVector(IsoRight * -30.f, 0.f), G + FVector(IsoRight * 30.f, 0.f), G + FVector(IsoRight * 30.f, 260.f), G + FVector(IsoRight * -30.f, 260.f), FLinearColor(0.70f, 0.70f, 0.68f));
		Quad(G + FVector(IsoRight * -70.f, 170.f), G + FVector(IsoRight * 70.f, 170.f), G + FVector(IsoRight * 70.f, 205.f), G + FVector(IsoRight * -70.f, 205.f), FLinearColor(0.78f, 0.78f, 0.76f));
		break;
	case 5:      // tent
		Tri3(G + FVector(IsoRight * -170.f, 0.f), G + FVector(IsoRight * 170.f, 0.f), G + FVector(0, 0, 260), FLinearColor(0.86f, 0.80f, 0.64f));
		Tri3(G, G + FVector(IsoRight * 170.f, 0.f), G + FVector(0, 0, 260), FLinearColor(0.72f, 0.66f, 0.52f));
		break;
	default:     // gravestone
		Quad(G + FVector(IsoRight * -25.f, 0.f), G + FVector(IsoRight * 25.f, 0.f), G + FVector(IsoRight * 25.f, 85.f), G + FVector(IsoRight * -25.f, 85.f), FLinearColor(0.62f, 0.63f, 0.62f));
		break;
	}
}

void AIVHUD::DrawPlayer(const FVector& Player, float Yaw, float Size)
{
	// a ring on the ground and an arrow along her facing (drawn over everything: she is never hidden on the map)
	const float L = Size / MapScale;
	const FVector G(Player.X, Player.Y, 0.f);
	const float Pulse = 0.5f + 0.5f * FMath::Sin(GetWorld()->GetTimeSeconds() * 4.f);
	Disc(G, L * (1.25f + 0.25f * Pulse), FLinearColor(1.f, 1.f, 1.f, 0.30f), 14, IsoSin);
	const float Yr = FMath::DegreesToRadians(Yaw);
	const FVector F(FMath::Cos(Yr), FMath::Sin(Yr), 0.f), R(-F.Y, F.X, 0.f);
	const FVector Z(0, 0, 40.f);
	Tri3(G + F * L * 1.25f + Z, G - F * L * 0.85f + R * L * 0.85f + Z, G - F * L * 0.85f - R * L * 0.85f + Z, FLinearColor::White);
	Tri3(G + F * L * 0.95f + Z, G - F * L * 0.60f + R * L * 0.58f + Z, G - F * L * 0.60f - R * L * 0.58f + Z, FLinearColor(1.f, 0.42f, 0.66f));
}

void AIVHUD::DrawVillage(const FVector2D& A, const FVector2D& B, const FVector& Center, float PixelsPerCm, bool bLabels, const FVector& Player, float PlayerYaw)
{
	ClipBox = FBox2D(A, B);
	MapScale = PixelsPerCm;
	MapOrigin = (A + B) * 0.5f - Project(FVector(Center.X, Center.Y, 0.f)) * MapScale;
	Tris.Reset();
	const float Now = GetWorld()->GetTimeSeconds();
	const float SS = Gen->SectionSize;
	// world radius that can reach the panel (the projection squashes the depth axis, so be generous along it)
	const float Reach = FVector2D((B - A)).Size() * 0.5f / MapScale / IsoSin + 1500.f;
	auto Near = [&](const FVector2D& P, float Pad) { return FMath::Abs(P.X - Center.X) < Reach + Pad && FMath::Abs(P.Y - Center.Y) < Reach + Pad; };
	auto OnPanel = [&](const FVector& W, float PadPx) { const FVector2D S = ToScreen(W); return S.X > A.X - PadPx && S.X < B.X + PadPx && S.Y > A.Y - PadPx && S.Y < B.Y + PadPx; };
	// ---- ground of the generated sections
	for (const auto& KV : Gen->MapData)
	{
		const FVector2D Mn = Gen->SectionMin(KV.Key);
		if (!Near(Mn + FVector2D(SS * 0.5f), SS)) continue;
		const float Age = Now - KV.Value.GeneratedTime;
		FLinearColor Gc(0.36f, 0.50f, 0.25f, 0.96f);
		if (KV.Value.GeneratedTime >= 0.f && Age < 3.f) Gc = FMath::Lerp(FLinearColor(Cyan.R, Cyan.G, Cyan.B, 0.9f), Gc, FMath::Clamp(Age / 3.f, 0.f, 1.f));
		Quad(FVector(Mn.X, Mn.Y, 0), FVector(Mn.X + SS, Mn.Y, 0), FVector(Mn.X + SS, Mn.Y + SS, 0), FVector(Mn.X, Mn.Y + SS, 0), Gc);
	}
	// ---- patches (fields, gardens, the square), then roads: outlines first, fills over them
	static const FLinearColor PatchC[6] = { FLinearColor(0.62f, 0.60f, 0.56f), FLinearColor(0.76f, 0.66f, 0.30f), FLinearColor(0.44f, 0.36f, 0.22f), FLinearColor(0.45f, 0.62f, 0.30f),
		FLinearColor(0.28f, 0.48f, 0.66f), FLinearColor(0.33f, 0.46f, 0.28f) };
	for (const auto& KV : Gen->MapData)
	{
		if (!Near(Gen->SectionMin(KV.Key) + FVector2D(SS * 0.5f), SS)) continue;
		for (const FIVMapPatch& P : KV.Value.Patches)
		{
			if (P.Points.Num() < 3 || !Near(P.Points[0], 6000.f)) continue;
			FVector2D Cn(0, 0); for (const FVector2D& Q : P.Points) Cn += Q; Cn /= P.Points.Num();
			const FLinearColor C = PatchC[FMath::Min<int32>(P.Type, 5)];
			for (int32 I = 0; I < P.Points.Num(); ++I) Tri3(FVector(Cn, 0), FVector(P.Points[I], 0), FVector(P.Points[(I + 1) % P.Points.Num()], 0), C);
		}
	}
	for (int32 Pass = 0; Pass < 2; ++Pass)
		for (const auto& KV : Gen->MapData)
		{
			if (!Near(Gen->SectionMin(KV.Key) + FVector2D(SS * 0.5f), SS)) continue;
			for (const FIVMapRoad& R : KV.Value.Roads) if (R.Points.Num() > 1 && R.Type != 3) DrawRoad(R, Pass == 0);
		}
	// ---- everything that stands up, far to near
	struct FItem { float Key; uint8 What; const void* Ptr; float Alpha; };
	TArray<FItem> Items;
	LastBuildings = 0;
	for (const auto& KV : Gen->MapData)
	{
		if (!Near(Gen->SectionMin(KV.Key) + FVector2D(SS * 0.5f), SS)) continue;
		const float Age = Now - KV.Value.GeneratedTime;
		const float Al = (KV.Value.GeneratedTime >= 0.f && Age < 1.5f) ? FMath::Clamp(Age / 1.5f, 0.f, 1.f) : 1.f;
		for (const FIVMapBuilding& Bd : KV.Value.Buildings)
			if (OnPanel(FVector(Bd.Center, 0), (Bd.Half.Size() + Bd.WallHeight + Bd.RoofHeight + Bd.TowerHeight) * MapScale))
			{ Items.Add({ (float)FVector2D::DotProduct(Bd.Center, IsoUp), 0, &Bd, Al }); ++LastBuildings; }
		for (const FIVMapTree& T : KV.Value.Trees) if (OnPanel(FVector(T.P, 0), (T.Radius + T.Height) * MapScale)) Items.Add({ (float)FVector2D::DotProduct(T.P, IsoUp), 1, &T, Al });
		for (const FIVMapProp& P : KV.Value.Props) if (OnPanel(FVector(P.P, 0), 400.f * MapScale)) Items.Add({ (float)FVector2D::DotProduct(P.P, IsoUp), 2, &P, Al });
	}
	Items.Sort([](const FItem& X, const FItem& Y) { return X.Key > Y.Key; });
	for (const FItem& It : Items)
	{
		if (It.What == 0) DrawBuilding(*(const FIVMapBuilding*)It.Ptr, It.Alpha);
		else if (It.What == 1) DrawTree(*(const FIVMapTree*)It.Ptr);
		else DrawProp(*(const FIVMapProp*)It.Ptr);
	}
	DrawPlayer(Player, PlayerYaw, bLabels ? 11.f : 8.f);
	Flush();
	// ---- freshly generated sections: a cyan outline
	for (const auto& KV : Gen->MapData)
	{
		const float Age = Now - KV.Value.GeneratedTime;
		if (KV.Value.GeneratedTime < 0.f || Age > 5.f) continue;
		const FVector2D Mn = Gen->SectionMin(KV.Key);
		const FVector Cn[4] = { FVector(Mn.X, Mn.Y, 0), FVector(Mn.X + SS, Mn.Y, 0), FVector(Mn.X + SS, Mn.Y + SS, 0), FVector(Mn.X, Mn.Y + SS, 0) };
		for (int32 I = 0; I < 4; ++I)
		{
			// (clipped to the panel by hand: lines are not part of the triangle batch)
			FVector2D P = ToScreen(Cn[I]), Q = ToScreen(Cn[(I + 1) % 4]);
			bool bOk = true;
			for (int32 E = 0; E < 4 && bOk; ++E)
			{
				auto In = [&](const FVector2D& S) { return E == 0 ? S.X >= A.X : E == 1 ? S.X <= B.X : E == 2 ? S.Y >= A.Y : S.Y <= B.Y; };
				const bool Pi = In(P), Qi = In(Q);
				if (!Pi && !Qi) { bOk = false; break; }
				if (Pi == Qi) continue;
				float T;
				if (E < 2) { const float X = E == 0 ? A.X : B.X; T = (X - P.X) / (Q.X - P.X); } else { const float Y = E == 2 ? A.Y : B.Y; T = (Y - P.Y) / (Q.Y - P.Y); }
				const FVector2D C = P + (Q - P) * T;
				if (Pi) Q = C; else P = C;
			}
			if (bOk) DrawLine(P.X, P.Y, Q.X, Q.Y, FLinearColor(Cyan.R, Cyan.G, Cyan.B, 1.f - Age / 5.f), 2.5f);
		}
	}
	// ---- labels (big map): landmarks first, then the houses wherever there is room
	LastLabels = 0;
	if (bLabels)
	{
		UFont* Small = GEngine->GetSmallFont();
		const float Sc = Canvas->ClipY / 1080.f;
		struct FLab { const FIVMapBuilding* B; int32 Pri; float D; };
		TArray<FLab> Labs;
		for (const auto& KV : Gen->MapData)
			for (const FIVMapBuilding& Bd : KV.Value.Buildings)
			{
				if (!OnPanel(FVector(Bd.Center, 0), -12.f)) continue;
				const int32 Pri = Bd.Kind == EIVBuildingKind::Church ? 0 : (Bd.Kind == EIVBuildingKind::Cottage || Bd.Kind == EIVBuildingKind::Farmhouse) ? 3 : (Bd.Kind == EIVBuildingKind::Barn || Bd.Kind == EIVBuildingKind::Storehouse) ? 2 : 1;
				Labs.Add({ &Bd, Pri, (float)FVector2D::DistSquared(Bd.Center, FVector2D(Player.X, Player.Y)) });
			}
		Labs.Sort([](const FLab& X, const FLab& Y) { return X.Pri != Y.Pri ? X.Pri < Y.Pri : X.D < Y.D; });
		TArray<FBox2D> Used;
		for (const FLab& Lb : Labs)
		{
			const FString N = AIVVillageGenerator::KindName(Lb.B->Kind);
			const float Ts = Sc * (Lb.Pri == 0 ? 1.25f : Lb.Pri == 1 ? 1.05f : 0.92f);
			float Tw, Th; GetTextSize(N, Tw, Th, Small, Ts);
			const FVector2D Top = ToScreen(FVector(Lb.B->Center, Lb.B->WallHeight + Lb.B->RoofHeight + Lb.B->TowerHeight * 0.4f));
			const FVector2D P0(Top.X - Tw * 0.5f, Top.Y - Th - 3.f * Sc);
			const FBox2D Bx(P0 - FVector2D(3.f, 1.f), P0 + FVector2D(Tw + 3.f, Th + 1.f));
			if (Bx.Min.X < A.X || Bx.Max.X > B.X || Bx.Min.Y < A.Y || Bx.Max.Y > B.Y) continue;
			bool bFree = true;
			for (const FBox2D& U : Used) if (U.Intersect(Bx)) { bFree = false; break; }
			if (!bFree) continue;
			Used.Add(Bx);
			Rect(Bx.Min, Bx.Max, FLinearColor(0.05f, 0.05f, 0.04f, Lb.Pri <= 1 ? 0.62f : 0.42f));
			DrawText(N, Lb.Pri == 0 ? FLinearColor(1.f, 0.93f, 0.62f) : Lb.Pri == 1 ? FLinearColor(1.f, 0.97f, 0.88f) : FLinearColor(0.86f, 0.86f, 0.80f), P0.X, P0.Y, Small, Ts);
			++LastLabels;
		}
	}
}

void AIVHUD::DrawHUD()
{
	Super::DrawHUD();
	if (!Canvas) return;
	if (!Gen) for (TActorIterator<AIVVillageGenerator> It(GetWorld()); It; ++It) { Gen = *It; break; }
	if (!Gen) return;
	const AActor* P = GetOwningPawn();
	if (!P) P = Gen->GetTrackedActor();
	if (!P) return;
	const float Yr = FMath::DegreesToRadians(Gen->IsoYaw), Pr = FMath::DegreesToRadians(FMath::Abs(Gen->IsoPitch));
	IsoUp = FVector2D(FMath::Cos(Yr), FMath::Sin(Yr)); IsoRight = FVector2D(-FMath::Sin(Yr), FMath::Cos(Yr));
	IsoSin = FMath::Sin(Pr); IsoCos = FMath::Cos(Pr);
	const float Sc = Canvas->ClipY / 1080.f;
	const FVector L = P->GetActorLocation();
	const float Yaw = P->GetActorRotation().Yaw;
	UFont* Small = GEngine->GetSmallFont();
	UFont* Medium = GEngine->GetMediumFont();
	const float Now = GetWorld()->GetTimeSeconds();
	const AIVPlayerController* PC = Cast<AIVPlayerController>(GetOwningPlayerController());
	const bool bPad = PC && PC->IsUsingGamepad();
	int32 Nb = 0, Nv = 0, Ns = 0; Gen->GetVillageStats(Nb, Nv, Ns);

	if (!Gen->bMapOpen)
	{
		// ---- minimap (top right)
		const float Px = MinimapPixels * Sc, Mg = 24.f * Sc;
		const FVector2D S0(Canvas->ClipX - Mg - Px, Mg + 26.f * Sc), S1 = S0 + FVector2D(Px, Px * 0.8f);
		Rect(S0 - FVector2D(8.f * Sc, 34.f * Sc), S1 + FVector2D(8.f * Sc, 30.f * Sc), FLinearColor(0.05f, 0.045f, 0.035f, 0.78f));
		Rect(S0, S1, FLinearColor(0.10f, 0.13f, 0.09f, 0.95f));
		DrawVillage(S0, S1, L, Px / (MinimapMeters * 100.f), false, L, Yaw);
		Frame(S0, S1, FLinearColor(0.78f, 0.66f, 0.42f, 0.95f), 2.f * Sc);
		DrawText(TEXT("VILLAGE"), Ink, S0.X, S0.Y - 28.f * Sc, Small, Sc * 1.1f);
		const FString Cnt = FString::Printf(TEXT("%d buildings"), Nb);
		float Tw, Th; GetTextSize(Cnt, Tw, Th, Small, Sc * 1.1f);
		DrawText(Cnt, Ink, S1.X - Tw, S0.Y - 28.f * Sc, Small, Sc * 1.1f);
		// north (+X) points up-left in this view
		const FVector2D Nd = Project(FVector(1, 0, 0)).GetSafeNormal();
		const FVector2D Nc(S0.X + 22.f * Sc, S1.Y - 22.f * Sc);
		DrawLine(Nc.X - Nd.X * 9.f * Sc, Nc.Y - Nd.Y * 9.f * Sc, Nc.X + Nd.X * 11.f * Sc, Nc.Y + Nd.Y * 11.f * Sc, Ink, 2.f * Sc);
		DrawText(TEXT("N"), Ink, Nc.X + Nd.X * 16.f * Sc - 4.f * Sc, Nc.Y + Nd.Y * 16.f * Sc - 7.f * Sc, Small, Sc);
		DrawText(bPad ? TEXT("Y  map") : TEXT("M  map"), FLinearColor(0.72f, 0.69f, 0.60f), S0.X, S1.Y + 6.f * Sc, Small, Sc);
	}

	// ---- new section banner
	if (Now - Gen->LastRevealTime < 4.f)
	{
		const float Ag = Now - Gen->LastRevealTime;
		const float A = FMath::Clamp(FMath::Min(Ag / 0.3f, (4.f - Ag) / 0.8f), 0.f, 1.f);
		const FString T = TEXT("NEW PART OF THE VILLAGE GENERATED");
		float Tw, Th; GetTextSize(T, Tw, Th, Medium, Sc * 1.4f);
		const float X = (Canvas->ClipX - Tw) * 0.5f, Y = 86.f * Sc;
		Rect(FVector2D(X - 18.f * Sc, Y - 8.f * Sc), FVector2D(X + Tw + 18.f * Sc, Y + Th + 8.f * Sc), FLinearColor(0.02f, 0.05f, 0.07f, 0.55f * A));
		DrawText(T, FLinearColor(Cyan.R, Cyan.G, Cyan.B, A), X, Y, Medium, Sc * 1.4f);
	}

	// ---- interaction prompt
	const FString What = Gen->DescribeNearest(L, PC ? PC->InteractDistance : 260.f);
	if (!What.IsEmpty() && !Gen->bMapOpen)
	{
		const FString T = FString::Printf(TEXT("%s  %s"), bPad ? TEXT("(A)") : TEXT("[F]"), *What);
		float Tw, Th; GetTextSize(T, Tw, Th, Medium, Sc * 1.2f);
		const float X = (Canvas->ClipX - Tw) * 0.5f, Y = Canvas->ClipY * 0.74f;
		Rect(FVector2D(X - 14.f * Sc, Y - 8.f * Sc), FVector2D(X + Tw + 14.f * Sc, Y + Th + 8.f * Sc), FLinearColor(0.03f, 0.03f, 0.04f, 0.62f));
		DrawText(T, FLinearColor(0.97f, 0.92f, 0.80f), X, Y, Medium, Sc * 1.2f);
	}

	// ---- controls hint (first seconds of play)
	if (Now < 14.f && !Gen->bMapOpen)
	{
		const float A = FMath::Clamp((14.f - Now) / 1.5f, 0.f, 1.f);
		const FString T = bPad ? TEXT("Left stick / D-pad  move (8 directions)   ·   A  open / close   ·   Y  map   ·   LB / RB  zoom   ·   LT  walk")
			: TEXT("W A S D  move (8 directions)   ·   F  open / close   ·   M  map   ·   mouse wheel  zoom   ·   Shift  walk");
		float Tw, Th; GetTextSize(T, Tw, Th, Small, Sc * 1.15f);
		const float X = 28.f * Sc, Y = Canvas->ClipY - 46.f * Sc;
		Rect(FVector2D(X - 10.f * Sc, Y - 6.f * Sc), FVector2D(X + Tw + 10.f * Sc, Y + Th + 6.f * Sc), FLinearColor(0.03f, 0.03f, 0.04f, 0.55f * A));
		DrawText(T, FLinearColor(0.92f, 0.88f, 0.78f, A), X, Y, Small, Sc * 1.15f);
	}

	// ---- big map (M): the village around her, every building labelled
	if (Gen->bMapOpen)
	{
		Rect(FVector2D(0, 0), FVector2D(Canvas->ClipX, Canvas->ClipY), FLinearColor(0.05f, 0.045f, 0.035f, 0.90f));
		const FVector2D A0(60.f * Sc, 104.f * Sc), A1(Canvas->ClipX - 60.f * Sc, Canvas->ClipY - 64.f * Sc);
		Rect(A0, A1, FLinearColor(0.10f, 0.13f, 0.09f, 1.f));
		const float K = (A1.Y - A0.Y) / (MapMeters * 100.f * IsoSin) * Gen->MapZoom;
		DrawVillage(A0, A1, L, K, true, L, Yaw);
		Frame(A0, A1, FLinearColor(0.78f, 0.66f, 0.42f, 0.95f), 2.f * Sc);
		DrawText(TEXT("VILLAGE MAP"), Ink, 60.f * Sc, 34.f * Sc, Medium, Sc * 1.6f);
		const FString Sub = FString::Printf(TEXT("%d buildings in %d part%s of the village  ·  %d entered  ·  %s"), Nb, Ns, Ns == 1 ? TEXT("") : TEXT("s"), Nv,
			bPad ? TEXT("Y / B  close  ·  LB / RB  zoom") : TEXT("M  close  ·  mouse wheel  zoom"));
		DrawText(Sub, FLinearColor(0.75f, 0.72f, 0.64f), 62.f * Sc, 72.f * Sc, Small, Sc * 1.1f);
		// legend: roof colours
		struct FLeg { const TCHAR* N; FLinearColor C; };
		const FLeg Leg[] = { { TEXT("thatched"), FLinearColor(0.84f, 0.69f, 0.31f) }, { TEXT("timber"), FLinearColor(0.50f, 0.30f, 0.19f) }, { TEXT("stone"), FLinearColor(0.42f, 0.46f, 0.55f) },
			{ TEXT("tavern"), FLinearColor(0.66f, 0.26f, 0.18f) }, { TEXT("church"), FLinearColor(0.33f, 0.40f, 0.55f) }, { TEXT("road"), FLinearColor(0.70f, 0.60f, 0.42f) }, { TEXT("field"), FLinearColor(0.76f, 0.66f, 0.30f) } };
		float X = 62.f * Sc; const float Y = Canvas->ClipY - 44.f * Sc;
		for (const FLeg& E : Leg)
		{
			Rect(FVector2D(X, Y + 3.f * Sc), FVector2D(X + 14.f * Sc, Y + 15.f * Sc), E.C);
			float Tw, Th; GetTextSize(E.N, Tw, Th, Small, Sc);
			DrawText(E.N, FLinearColor(0.78f, 0.75f, 0.67f), X + 20.f * Sc, Y, Small, Sc);
			X += Tw + 44.f * Sc;
		}
	}
}
