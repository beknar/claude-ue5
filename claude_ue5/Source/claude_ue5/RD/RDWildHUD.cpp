// The wilderness's maps on the HUD (RDWildMap.cpp makes their pictures): the big map (the world from above in its tiles, the
// rivers and roads as lines, the fog over what she has not seen, the places' symbols and names, her arrow, a scroll's edge round
// it) and the minimap (the ground round her, the places near, the monsters after her). Inside a town's walls the town's own
// maps are drawn instead (ARDHUD::DrawHUD).
#include "Engine/TextureRenderTarget2D.h"
#include "RD/RDHUD.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDMonster.h"
#include "RD/RDCombat.h"
#include "Engine/Canvas.h"
#include "Engine/Font.h"
#include "Engine/Engine.h"
#include "Engine/Texture2D.h"
#include "GameFramework/PlayerController.h"

namespace
{
	FName RDWSymbolOf(const FString& Kind) { return FName(*(TEXT("wmap_") + Kind)); }
}

void ARDHUD::DrawWildMap(float Sc, const FVector& L, float Yaw)
{
	if (!Gen->IsWildReady()) return;
	const FRDWildWorld& W = *Gen->Wild;
	UFont* Small = GEngine->GetSmallFont();
	// the sheet: square as the town's, the scroll's torn edge round it, the keys under it
	const float Ms = FMath::Min(Canvas->ClipY * 0.84f, Canvas->ClipX * 0.62f);
	const FVector2D A0((Canvas->ClipX - Ms) * 0.5f, (Canvas->ClipY - Ms) * 0.44f), B0 = A0 + FVector2D(Ms);
	// (the scroll's edge is drawn over A0 - 3 % .. B0 + 3 % of the sheet. The list of 2026-11-12: "the wilderness map is a square
	// with a scroll overlay on it, with the square showing in the gaps of the irregular scroll edges. map square should not show up
	// outside of the scroll overlay": the map is drawn only inside the scroll, where every pixel of the edge's picture is its
	// parchment or its open middle: 11.07 % of the picture in from its sides and 5.08 % from its top and bottom
	// (mapc_scroll_edge measured: bs_scroll.py prints it), with a little to spare; outside it the backdrop shows in the gaps)
	const float Pic = Ms * 1.06f;
	const FVector2D A = A0 - FVector2D(Ms * 0.03f) + FVector2D(Pic * 0.115f, Pic * 0.054f), B = B0 + FVector2D(Ms * 0.03f) - FVector2D(Pic * 0.115f, Pic * 0.054f);
	const FVector2D Sz = B - A, Mid = (A + B) * 0.5f;
	Box(FVector2D(0, 0), FVector2D(Canvas->ClipX, Canvas->ClipY), FLinearColor(0.02f, 0.02f, 0.018f, 0.86f));
	const double Mpp = Gen->WildMapMpp;
	const FVector2D Cw = Gen->WildMapCenter;
	auto ToS = [&](const FVector2D& Wm) { return FVector2D(Mid.X + (Wm.Y - Cw.Y) / Mpp, Mid.Y - (Wm.X - Cw.X) / Mpp); };
	// (the list of 2026-11-12: the map's frame for the pointer and rd.MapTeleport's click: RDList12.cpp)
	Gen->MapXC = Mid; Gen->MapXVw = Cw * 100.0; Gen->MapXK = (float)(1.0 / (Mpp * 100.0)); Gen->MapXSheet = FBox2D(A, B); Gen->MapXKind = 1;
	// (the pointer over the sheet picks the place under it; else the cross at the view's middle does)
	FVector2D PickAt = Mid;
	{
		float Px = 0.f, Py = 0.f;
		APlayerController* PCp = GetOwningPlayerController();
		if (Gen->bMapPointerLead && PCp && PCp->ShouldShowMouseCursor() && PCp->GetMousePosition(Px, Py) && Gen->MapXSheet.IsInside(FVector2D(Px, Py))) PickAt = FVector2D(Px, Py);
	}
	// the world in its tiles (a coarser tile's part while the finer one is made)
	const int32 Lv = Gen->WildMapLevelFor(Mpp);
	const double X0 = Cw.X - Sz.Y * 0.5 * Mpp, X1 = Cw.X + Sz.Y * 0.5 * Mpp, Y0 = Cw.Y - Sz.X * 0.5 * Mpp, Y1 = Cw.Y + Sz.X * 0.5 * Mpp;
	const double Span = Gen->WildMapTileSpan(Lv);
	const int32 I0 = FMath::Max(0, FMath::FloorToInt((X0 - W.Xs) / Span)), I1 = FMath::Min((1 << Lv) - 1, FMath::FloorToInt((X1 - W.Xs) / Span));
	const int32 J0 = FMath::Max(0, FMath::FloorToInt((Y0 - W.Yw) / Span)), J1 = FMath::Min((1 << Lv) - 1, FMath::FloorToInt((Y1 - W.Yw) / Span));
	Box(A, B, FLinearColor(0.16f, 0.15f, 0.12f, 1.f));         // (a dark sheet where a tile is still being made)
	int32 Drawn = 0, Stand = 0;
	for (int32 I = I0; I <= I1; ++I)
		for (int32 J = J0; J <= J1; ++J)
		{
			const double Tx0 = W.Xs + I * Span, Ty0 = W.Yw + J * Span;
			UTexture2D* T = Gen->WildMapTile(Lv, I, J, true);
			double U0 = 0, V0 = 0, Us = 1, Vs = 1;
			if (!T)
			{
				// (an ancestor's quarter of a quarter...)
				for (int32 Up = 1; Up <= Lv && !T; ++Up)
				{
					const int32 Pi = I >> Up, Pj = J >> Up;
					T = Gen->WildMapTile(Lv - Up, Pi, Pj, Up <= 2);
					if (T)
					{
						const double Ps = Gen->WildMapTileSpan(Lv - Up);
						Us = Vs = Span / Ps;
						U0 = (Ty0 - (W.Yw + Pj * Ps)) / Ps;
						V0 = ((W.Xs + (Pi + 1) * Ps) - (Tx0 + Span)) / Ps;
						++Stand;
					}
				}
			}
			if (!T) continue;
			// the tile on the screen, cut to the sheet
			FVector2D P0 = ToS(FVector2D(Tx0 + Span, Ty0)), P1 = ToS(FVector2D(Tx0, Ty0 + Span));
			const FVector2D Q0(FMath::Max(P0.X, A.X), FMath::Max(P0.Y, A.Y)), Q1(FMath::Min(P1.X, B.X), FMath::Min(P1.Y, B.Y));
			if (Q1.X <= Q0.X || Q1.Y <= Q0.Y) continue;
			const FVector2D Ds = P1 - P0;
			const double Ua = U0 + Us * (Q0.X - P0.X) / Ds.X, Ub = U0 + Us * (Q1.X - P0.X) / Ds.X;
			const double Va = V0 + Vs * (Q0.Y - P0.Y) / Ds.Y, Vb = V0 + Vs * (Q1.Y - P0.Y) / Ds.Y;
			DrawTexture(T, Q0.X, Q0.Y, Q1.X - Q0.X, Q1.Y - Q0.Y, Ua, Va, Ub - Ua, Vb - Va, FLinearColor::White, BLEND_Opaque);
			++Drawn;
		}
	// rivers and roads as lines (thin features a pixel of the map cannot show); each segment's colour from a callback (the list of
	// 2026-11-20's eleventh phase: the major roads by their tier, one clipper for every line (PR #103's review))
	auto LinesBy = [&](const TArray<FVector2D>& P, TFunctionRef<FLinearColor(const FVector2D&, const FVector2D&)> Col, float Wpx, bool bRecord)
	{
		FVector2D Last(-1e9f, -1e9f), LastW(0, 0); bool bHave = false;
		for (int32 K = 0; K < P.Num(); ++K)
		{
			const FVector2D S = ToS(P[K]);
			if (bHave && FVector2D::DistSquared(S, Last) < 16.f && K + 1 < P.Num()) continue;
			const bool bIn = S.X > A.X && S.X < B.X && S.Y > A.Y && S.Y < B.Y;
			if (bHave && (bIn || (Last.X > A.X && Last.X < B.X && Last.Y > A.Y && Last.Y < B.Y)))
			{
				const FLinearColor C = Col(LastW, P[K]);
				DrawLine(Last.X, Last.Y, S.X, S.Y, C, Wpx);
				if (bRecord && RoadsDrawn15.Num() < 4000)
				{
					const FVector2D Mw = (LastW + P[K]) * 0.5;
					RoadsDrawn15.Add(FString::Printf(TEXT("%.0f|%.0f|%.3f|%.3f|%.3f"), Mw.X, Mw.Y, C.R, C.G, C.B));
				}
			}
			Last = S; LastW = P[K]; bHave = true;
		}
	};
	auto Lines = [&](const TArray<FVector2D>& P, const FLinearColor& C, float Wpx) { LinesBy(P, [&C](const FVector2D&, const FVector2D&) { return C; }, Wpx, false); };
	for (const FRDWildWorld::FRiver& R : W.Rivers)
		if (R.Box.Max.X > X0 && R.Box.Min.X < X1 && R.Box.Max.Y > Y0 && R.Box.Min.Y < Y1)
			Lines(R.P, FLinearColor(0.20f, 0.36f, 0.42f, 0.9f), FMath::Clamp((float)(R.W.Last() / Mpp), 1.2f, 4.f) * Sc);
	// (the list of 2026-11-16's fourteenth phase: "they should look different on the mini map and the large map": a major road a pale
	// stone line in a dark edge, a minor road a thin brown line, shown once the map is near enough (under 40 m a pixel))
	// (only the roads in view: the majors by their list, the minors through the segments' hash (PR #92's review: 5,500 roads a frame))
	RoadsDrawn15.Reset();
	{
		const FBox2D Vw(FVector2D(X0, Y0), FVector2D(X1, Y1));
		TArray<int32> In;
		if (Mpp < 40.0) { W.RoadsIn(Vw, true, In); for (const int32 Ri : In) Lines(W.Roads[Ri].P, FLinearColor(0.50f, 0.35f, 0.19f, 0.85f), FMath::Clamp((float)(4.0 / Mpp), 0.8f, 2.f) * Sc); }
		In.Reset(); W.RoadsIn(Vw, false, In);
		const float Wr = FMath::Clamp((float)(9.0 / Mpp), 2.f, 4.f) * Sc;
		for (const int32 Ri : In) Lines(W.Roads[Ri].P, FLinearColor(0.13f, 0.11f, 0.09f, 0.95f), Wr + 2.f * Sc);
		// (the eleventh phase (idea 9, "the danger shown on the map", bRoadTiers15): a major road in its tier's colour, segment by segment
		// (the tier read at each drawn segment's middle); its pale stone line when the switch is off)
		for (const int32 Ri : In)
			if (Gen->bRoadTiers15) LinesBy(W.Roads[Ri].P, [&W](const FVector2D& P0, const FVector2D& P1) { const FVector2D Mw = (P0 + P1) * 0.5; return ARDDungeonGenerator::RoadTierColor15(W.TierAt(Mw.X, Mw.Y)); }, Wr, true);
			else Lines(W.Roads[Ri].P, FLinearColor(0.80f, 0.76f, 0.66f, 1.f), Wr);
	}
	// the fog
	{
		FVector2D U0, U1;
		if (UTexture2D* F = Gen->WildFog(Cw, Mpp, Sz, U0, U1)) DrawTexture(F, A.X, A.Y, Sz.X, Sz.Y, U0.X, U0.Y, U1.X - U0.X, U1.Y - U0.Y, FLinearColor::White, BLEND_Translucent);
	}
	// the places she knows: the towns (always) and those she found; the one under the view's middle chosen for travel
	TArray<FRDWildPlace> Ps; Gen->WildKnownPlaces(Ps);
	int32 Pick = -1; float PickD = 34.f * Sc; FString PickName; double PickKm = 0;
	for (const FRDWildPlace& P : Ps)
	{
		const FVector2D S = ToS(P.At);
		if (S.X < A.X || S.X > B.X || S.Y < A.Y || S.Y > B.Y) continue;
		const bool bFound = Gen->WildFound.Contains(P.Id);
		const float D = FVector2D::Distance(S, PickAt);
		if (bFound && D < PickD) { PickD = D; Pick = P.Id; PickName = P.Name; PickKm = FVector2D::Distance(P.At, FVector2D(L.X / 100.0, L.Y / 100.0)) / 1000.0; }
	}
	Gen->WildMapHover = Pick; Gen->WildMapHoverName = PickName;
	for (const FRDWildPlace& P : Ps)
	{
		const FVector2D S = ToS(P.At);
		if (S.X < A.X || S.X > B.X || S.Y < A.Y || S.Y > B.Y) continue;
		const bool bFound = Gen->WildFound.Contains(P.Id), bTown = P.Town >= 0;
		const float Ic = (bTown ? 19.f : 13.f) * Sc;
		if (P.Id == Pick) UI.Fit(TEXT("wmap_select"), S - FVector2D(Ic * 1.9f), S + FVector2D(Ic * 1.9f), FLinearColor(1.f, 1.f, 1.f, 0.95f));
		if (!UI.Fit(RDWSymbolOf(P.Kind), S - FVector2D(Ic), S + FVector2D(Ic), FLinearColor(1.f, 1.f, 1.f, bFound ? 1.f : 0.55f))) SoftDot(S, 6.f * Sc, FLinearColor(0.95f, 0.9f, 0.78f, 1.f));
		// (a taken quest's place is named at every zoom: it is where she is sent)
		// (the list of 2026-11-11: rd.Pois' small points of interest are named only close in (a 3 km view of them was all names))
		const bool bSmall = P.Id >= FRDWildWorld::PoiIdBase && P.Id < FRDWildWorld::FarmIdBase;
		if (bTown || (Mpp < (bSmall ? 3.0 : 18.0)) || P.Id == Pick || Gen->IsWildQuestShown(P.Id))
		{
			const FString Nm = bTown ? P.Name.ToUpper() : P.Name;
			const float Ts = Sc * (bTown ? 1.15f : 0.9f);
			float Tw, Th; UI.TextSize(Nm, Tw, Th, Small, Ts, bTown ? ERDType::Title : ERDType::Label);
			const FVector2D Tp(S.X - Tw * 0.5f, S.Y + Ic + 2.f * Sc);
			UI.Text(Nm, FLinearColor(0.f, 0.f, 0.f, 0.75f), Tp.X + 1.5f * Sc, Tp.Y + 1.5f * Sc, Small, Ts, bTown ? ERDType::Title : ERDType::Label);
			UI.Text(Nm, bFound ? FLinearColor(0.98f, 0.94f, 0.84f, 1.f) : FLinearColor(0.85f, 0.82f, 0.74f, 0.8f), Tp.X, Tp.Y, Small, Ts, bTown ? ERDType::Title : ERDType::Label);
		}
	}
	// (a named mark: an icon and its name under it, shadowed; one helper for the roamers' and the contracts' (PR #105's review))
	auto NamedMark = [&](const FVector2D& AtM, const FString& Nm, float IconPx, const FLinearColor& IconCol, const FLinearColor& TextCol) -> bool
	{
		const FVector2D S = ToS(AtM);
		if (S.X < A.X || S.X > B.X || S.Y < A.Y || S.Y > B.Y) return false;
		const float Ic = IconPx * Sc;
		UI.Fit(TEXT("wmap_lair"), S - FVector2D(Ic), S + FVector2D(Ic), IconCol);
		float Tw, Th; UI.TextSize(Nm, Tw, Th, Small, Sc * 0.9f, ERDType::Label);
		UI.Text(Nm, FLinearColor(0.f, 0.f, 0.f, 0.75f), S.X - Tw * 0.5f + 1.5f * Sc, S.Y + Ic + 3.5f * Sc, Small, Sc * 0.9f, ERDType::Label);
		UI.Text(Nm, TextCol, S.X - Tw * 0.5f, S.Y + Ic + 2.f * Sc, Small, Sc * 0.9f, ERDType::Label);
		return true;
	};
	// (the list of 2026-11-20's eleventh phase: the roamers she has seen and not slain, a skull at their rounds, named)
	Gen->DrawRoamerMarks15([&](const FVector2D& AtM, const FString& Nm) { NamedMark(AtM, Nm, 15.f, FLinearColor(1.f, 0.35f, 0.30f, 1.f), FLinearColor(1.f, 0.55f, 0.48f, 1.f)); });
	// (the list of 2026-11-20's thirteenth phase: the contracts taken, the next sign or the lair, in gold)
	Gen->DrawContractMarks15([&](const FVector2D& AtM, const FString& Nm)
	{
		if (NamedMark(AtM, Nm, 14.f, FLinearColor(1.f, 0.82f, 0.30f, 1.f), FLinearColor(1.f, 0.86f, 0.45f, 1.f))) ContractMarksDrawn15.Add(FString::Printf(TEXT("%.0f|%.0f|%s"), AtM.X, AtM.Y, *Nm));
	});
	// (and the roads' key: the tiers' colours, in the sheet's bottom left (in its top left it lay over the map's title))
	if (Gen->bRoadTiers15)
	{
		const float Kw = 22.f * Sc, Kh = 8.f * Sc, Kx = A.X + 12.f * Sc, Ky = B.Y - 34.f * Sc - (6 * (Kh + 6.f * Sc) + 20.f * Sc);          // (its last row clear of the scroll's edge)
		Box(FVector2D(Kx - 6.f * Sc, Ky - 6.f * Sc), FVector2D(Kx + 132.f * Sc, Ky + 6 * (Kh + 6.f * Sc) + 20.f * Sc), FLinearColor(0.f, 0.f, 0.f, 0.45f));
		UI.Text(TEXT("ROADS BY TIER"), FLinearColor(0.98f, 0.94f, 0.84f, 1.f), Kx, Ky, Small, Sc * 0.8f, ERDType::Label);
		for (int32 Band = 0; Band < 6; ++Band)
		{
			const float Y = Ky + 18.f * Sc + Band * (Kh + 6.f * Sc);
			Box(FVector2D(Kx, Y), FVector2D(Kx + Kw, Y + Kh), ARDDungeonGenerator::RoadTierColor15(Band * 5 + 1));
			UI.Text(FString::Printf(TEXT("%d - %d"), Band * 5 + 1, Band * 5 + 5), FLinearColor(0.95f, 0.92f, 0.84f, 1.f), Kx + Kw + 8.f * Sc, Y - 3.f * Sc, Small, Sc * 0.75f, ERDType::Label);
		}
	}
	// (the list of 2026-11-20's twelfth phase: the treasure map she holds, its picture beside the sheet where there is room, else over its
	// bottom right)
	{
		FString Cap;
		if (UTextureRenderTarget2D* Rt = Gen->TreasurePictureToShow15(Cap))
		{
			const float Pw = FMath::Min(360.f * Sc, FMath::Max(Canvas->ClipX - B0.X - 40.f * Sc, 220.f * Sc)), Ph = Pw * 288.f / 512.f;
			const float Px = B0.X + 20.f * Sc + Pw < Canvas->ClipX ? B0.X + 20.f * Sc : B.X - Pw - 10.f * Sc, Py = B0.Y - Ph - 60.f * Sc;
			Box(FVector2D(Px - 6.f * Sc, Py - 6.f * Sc), FVector2D(Px + Pw + 6.f * Sc, Py + Ph + 34.f * Sc), FLinearColor(0.10f, 0.08f, 0.06f, 0.92f));
			DrawTexture(Rt, Px, Py, Pw, Ph, 0.f, 0.f, 1.f, 1.f, FLinearColor(1.f, 0.93f, 0.80f, 1.f), BLEND_Opaque);
			UI.Text(Cap, FLinearColor(0.98f, 0.94f, 0.84f, 1.f), Px, Py + Ph + 8.f * Sc, Small, Sc * 0.8f, ERDType::Label);
			TreasureShown15 = true;
		}
	}
	// (the list of 2026-11-16: her horse)
	{ FVector Ha; if (Gen->GetHorseMapAt(Ha)) { const FVector2D Hs = ToS(FVector2D(Ha.X / 100.0, Ha.Y / 100.0)); if (Hs.X > A.X && Hs.X < B.X && Hs.Y > A.Y && Hs.Y < B.Y) DrawHorseMark(Hs, Sc * 1.2f); } }
	// her arrow (pinned to the sheet's edge when she is off it), the view's middle
	{
		FVector2D S = ToS(FVector2D(L.X / 100.0, L.Y / 100.0));
		S.X = FMath::Clamp(S.X, A.X + 10.f * Sc, B.X - 10.f * Sc); S.Y = FMath::Clamp(S.Y, A.Y + 10.f * Sc, B.Y - 10.f * Sc);
		DrawPlayerArrow(S, Yaw - 90.f, 11.f * Sc);
		const FLinearColor Cr(1.f, 0.95f, 0.85f, 0.6f);
		DrawLine(Mid.X - 9.f * Sc, Mid.Y, Mid.X - 3.f * Sc, Mid.Y, Cr, 1.5f * Sc); DrawLine(Mid.X + 3.f * Sc, Mid.Y, Mid.X + 9.f * Sc, Mid.Y, Cr, 1.5f * Sc);
		DrawLine(Mid.X, Mid.Y - 9.f * Sc, Mid.X, Mid.Y - 3.f * Sc, Cr, 1.5f * Sc); DrawLine(Mid.X, Mid.Y + 3.f * Sc, Mid.X, Mid.Y + 9.f * Sc, Cr, 1.5f * Sc);
	}
	// the scroll's edge round it (the spec: "a papyrus or scroll look at the edges"), else a gold rule
	if (!UI.Fit(TEXT("mapc_scroll_edge"), A0 - FVector2D(Ms * 0.03f), B0 + FVector2D(Ms * 0.03f)))
	{
		const FLinearColor Gd(0.78f, 0.62f, 0.32f, 1.f);
		DrawLine(A.X, A.Y, B.X, A.Y, Gd, 2.f * Sc); DrawLine(B.X, A.Y, B.X, B.Y, Gd, 2.f * Sc); DrawLine(B.X, B.Y, A.X, B.Y, Gd, 2.f * Sc); DrawLine(A.X, B.Y, A.X, A.Y, Gd, 2.f * Sc);
	}
	UI.Fit(TEXT("mapc_compass"), FVector2D(B.X - 110.f * Sc, B.Y - 110.f * Sc), FVector2D(B.X - 22.f * Sc, B.Y - 22.f * Sc));
	// the title, the key
	{
		const FString T = TEXT("THE WILDS");
		float Tw, Th; UI.TextSize(T, Tw, Th, Small, Sc * 1.6f, ERDType::Title);
		UI.Text(T, FLinearColor(0.f, 0.f, 0.f, 0.8f), A.X + 42.f * Sc, A.Y + 34.f * Sc, Small, Sc * 1.6f, ERDType::Title);
		UI.Text(T, FLinearColor(1.f, 0.86f, 0.55f, 1.f), A.X + 40.f * Sc, A.Y + 32.f * Sc, Small, Sc * 1.6f, ERDType::Title);
		const double Across = Sz.X * Mpp / 1000.0;
		const FString K1 = FString::Printf(TEXT("M close the map     wheel or + / -  zoom (%.1f km across)     drag or arrows  move     C  back to you"), Across);
		const FString K2 = Gen->bMapClickTeleport ? FString(Gen->bMapRevealAll ? TEXT("rd.MapTeleport: click a point to teleport there") : TEXT("rd.MapTeleport: reveal the map first (rd.RevealMap)"))
		                 : Pick >= 0 ? FString::Printf(TEXT("click or F / Enter / A  travel to %s (%.0f km)"), *PickName, PickKm)
		                 : FString(TEXT("point at a place you have found (or put it under the cross) to travel there"));
		const FString K3 = Gen->WildTravelRefusal.IsEmpty() ? FString() : FString::Printf(TEXT("     %s"), *Gen->WildTravelRefusal);
		float W1, H1; UI.TextSize(K1, W1, H1, Small, Sc);
		UI.Text(K1, FLinearColor(0.86f, 0.84f, 0.78f, 0.95f), Mid.X - W1 * 0.5f, B0.Y + Ms * 0.03f + 10.f * Sc, Small, Sc);
		const FString K23 = K2 + K3;
		float W2, H2; UI.TextSize(K23, W2, H2, Small, Sc);
		UI.Text(K23, Pick >= 0 ? FLinearColor(1.f, 0.85f, 0.45f, 1.f) : FLinearColor(0.7f, 0.68f, 0.62f, 0.9f), Mid.X - W2 * 0.5f, B0.Y + Ms * 0.03f + 12.f * Sc + H1, Small, Sc);
	}
	WildMapTilesDrawn = Drawn; WildMapStandIns = Stand;
	if (UI.Drawn) UI.Drawn->AddUnique(TEXT("wild_map"));
}

void ARDHUD::DrawWildMinimap(float Sc, const FVector& L, float Yaw)
{
	if (!Gen->IsWildReady()) return;
	UFont* Small = GEngine->GetSmallFont();
	const float R = MinimapPixels * Sc * 0.5f, Mg = 24.f * Sc;
	const FRDUIArt* Ra = UI.Find(TEXT("minimap_ring"));
	const float Ring = Ra ? R * 1.03f / FMath::Max((float)(Ra->Inner.Z - Ra->Inner.X), 0.2f) : R;
	const FVector2D C(Canvas->ClipX - Mg - Ring, Mg + (Ra ? 0.f : 14.f * Sc) + Ring);
	const FVector2D Here(L.X / 100.0, L.Y / 100.0);
	const double Rm = Gen->WildMiniRadiusM;
	const float K = R / (float)Rm;
	auto ToS = [&](const FVector2D& Wm) { return C + FVector2D((float)(Wm.Y - Here.Y), -(float)(Wm.X - Here.X)) * K; };
	if (UTexture2D* T = GetSoftDisc()) DrawTexture(T, C.X - R * 1.3f, C.Y - R * 1.3f, R * 2.6f, R * 2.6f, 0.f, 0.f, 1.f, 1.f, FLinearColor(0.004f, 0.005f, 0.007f, 0.85f), BLEND_Translucent);
	if (UTexture2D* M = Gen->WildMini(Here)) DrawTexture(M, C.X - R, C.Y - R, R * 2.f, R * 2.f, 0, 0, 1, 1, FLinearColor::White, BLEND_Translucent);
	// the roads (the fourteenth phase): the major ones pale stone in a dark edge, the minor ones thin brown, inside the disc
	{
		const FBox2D Vb(Here - FVector2D(Rm), Here + FVector2D(Rm));
		auto Seg = [&](const FVector2D& Pa, const FVector2D& Pb, const FLinearColor& Cl, float Wp)
		{
			const FVector2D Sa = ToS(Pa), Sb = ToS(Pb);
			if (FVector2D::Distance(Sa, C) < R * 0.94f && FVector2D::Distance(Sb, C) < R * 0.94f) DrawLine(Sa.X, Sa.Y, Sb.X, Sb.Y, Cl, Wp);
		};
		TArray<int32> Mn, Mj; Gen->Wild->RoadsIn(Vb, true, Mn); Gen->Wild->RoadsIn(Vb, false, Mj);
		for (int32 Pass = 0; Pass < 3; ++Pass)
			for (const int32 Ri : (Pass < 2 ? Mj : Mn))
			{
				const FRDWildWorld::FRoad& Rd = Gen->Wild->Roads[Ri];
				const FLinearColor Cl = Rd.bTrack ? FLinearColor(0.50f, 0.35f, 0.19f, 0.9f) : (Pass == 0 ? FLinearColor(0.13f, 0.11f, 0.09f, 0.95f) : FLinearColor(0.80f, 0.76f, 0.66f, 1.f));
				const float Wp = Rd.bTrack ? FMath::Max(4.f * K, 1.2f * Sc) : FMath::Max(9.f * K, 3.f * Sc) + (Pass == 0 ? 2.f * Sc : 0.f);
				for (int32 I = 0; I + 1 < Rd.P.Num(); ++I)
					if (FVector2D::DistSquared(Rd.P[I], Here) < Rm * Rm * 1.1) Seg(Rd.P[I], Rd.P[I + 1], Cl, Wp);
			}
	}
	// the places near (towns and those found), the monsters after her
	TArray<FRDWildPlace> Ps; Gen->WildKnownPlaces(Ps);
	for (const FRDWildPlace& P : Ps)
	{
		const FVector2D S = ToS(P.At);
		if (FVector2D::Distance(S, C) > R * 0.86f) continue;
		const float Ic = 11.f * Sc;
		// (a small point of interest (rd.Pois) has no symbol: a dot)
		if (!UI.Fit(RDWSymbolOf(P.Kind), S - FVector2D(Ic), S + FVector2D(Ic), FLinearColor(1.f, 1.f, 1.f, Gen->WildFound.Contains(P.Id) ? 1.f : 0.6f)))
			SoftDot(S, 4.5f * Sc, FLinearColor(0.95f, 0.9f, 0.78f, 0.9f));
	}
	for (const ARDMonster* Mo : Gen->GetMonsters())
	{
		if (!Mo || Mo->IsDead() || Mo->IsAlly()) continue;
		const FVector2D S = ToS(FVector2D(Mo->GetActorLocation().X / 100.0, Mo->GetActorLocation().Y / 100.0));
		if (FVector2D::Distance(S, C) > R * 0.94f) continue;
		SoftDot(S, 8.f * Sc, FLinearColor(1.f, 0.16f, 0.1f, Mo->IsAggro() ? 0.45f : 0.2f)); SoftDot(S, 3.8f * Sc, FLinearColor(1.f, 0.16f, 0.1f, Mo->IsAggro() ? 1.f : 0.6f));
	}
	{ FVector Ha; if (Gen->GetHorseMapAt(Ha)) { const FVector2D Hs = ToS(FVector2D(Ha.X / 100.0, Ha.Y / 100.0)); if (FVector2D::Distance(Hs, C) < R * 0.9f) DrawHorseMark(Hs, Sc); } }
	DrawPlayerArrow(C, Yaw - 90.f, 9.f * Sc);
	if (Ra) UI.Fit(TEXT("minimap_ring"), C - FVector2D(Ring), C + FVector2D(Ring));
	const FLinearColor Ink(0.75f, 0.77f, 0.8f, 0.85f);
	UI.Text(TEXT("N"), Ink, C.X - 4.f * Sc, C.Y - R * 0.98f, Small, Sc, ERDType::Title);
	// under it (the list of 2026-11-04: "the biome's name should also be visible under the mini map once the player is in the
	// wilderness"; it was over it, at the screen's top edge): the region she is in and the weather, then the nearest town, the
	// hour and the key
	FRDWSample S; Gen->Wild->Sample(Here.X, Here.Y, S, false);
	const float Y0 = C.Y + (Ra ? Ring + 4.f * Sc : R * 0.96f);
	float Th0 = 0.f;
	{
		// (the list of 2026-11-08b: "have an indicator for what kind of crops there are at the farm terrain": in a field, its
		// crop beside the region's name)
		FString Region = Gen->Wild->BiomeName(S.Biome).ToUpper();
		CropLabelDrawn = Gen->Wild->CropName(S, 0.05f);
		if (!CropLabelDrawn.IsEmpty()) Region += FString::Printf(TEXT("  ·  A FIELD OF %s"), *CropLabelDrawn.ToUpper());
		const FString Title = Gen->bSky7 ? FString::Printf(TEXT("%s  ·  %s"), *Region, *ARDDungeonGenerator::WeatherName(Gen->Weather)) : Region;
		float Tw0; UI.TextSize(Title, Tw0, Th0, Small, Sc * 1.15f, ERDType::Title);
		UI.Text(Title, FLinearColor(0.f, 0.f, 0.f, 0.8f), C.X - Tw0 * 0.5f + 1.5f * Sc, Y0 + 1.5f * Sc, Small, Sc * 1.15f, ERDType::Title);
		UI.Text(Title, FLinearColor(1.f, 0.84f, 0.5f, 1.f), C.X - Tw0 * 0.5f, Y0, Small, Sc * 1.15f, ERDType::Title);
		BiomeLabelDrawn = Title;
	}
	const bool bPad = Gen->bCasterControls && Gen->GetPlayerCombat() && Gen->GetPlayerCombat()->IsUsingGamepad();
	double Dt; const int32 Ti = Gen->Wild->NearestTown(Here.X, Here.Y, Dt);
	const FString Near = Ti >= 0 ? FString::Printf(TEXT("%s %.1f km"), *Gen->Wild->Towns[Ti].Name, Dt / 1000.0) : FString();
	const FString Clock = Gen->bDayNight ? FString::Printf(TEXT("    day %d · %s"), Gen->GetTownDay(), *Gen->GetTownClock()) : FString();
	const FString Under = FString::Printf(TEXT("%s%s    %s  map"), *Near, *Clock, bPad ? TEXT("Back") : TEXT("M"));
	float Tw, Th; UI.TextSize(Under, Tw, Th, Small, Sc);
	UI.Text(Under, Ink, C.X - Tw * 0.5f, Y0 + Th0 + 3.f * Sc, Small, Sc);
	if (UI.Drawn) UI.Drawn->AddUnique(TEXT("wild_minimap"));
}
