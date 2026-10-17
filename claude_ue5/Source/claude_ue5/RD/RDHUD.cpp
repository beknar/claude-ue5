#include "RD/RDHUD.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDMonster.h"
#include "RD/RDCombat.h"
#include "RD/RDSection.h"
#include "Engine/Texture2D.h"
#include "Components/CapsuleComponent.h"
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
static const FLinearColor RDCyan(0.43f, 0.88f, 1.0f, 1.f);
static const FLinearColor RDInk(0.92f, 0.86f, 0.72f, 1.f);

/** floor colour of a room in the miniature */
static FLinearColor RDFloor(ERDRoomKind K, bool bCorridor)
{
	if (bCorridor) return FLinearColor(0.33f, 0.31f, 0.29f);
	switch (K)
	{
	case ERDRoomKind::Hall: return FLinearColor(0.62f, 0.55f, 0.42f); case ERDRoomKind::Barracks: return FLinearColor(0.50f, 0.46f, 0.40f);
	case ERDRoomKind::Prison: return FLinearColor(0.38f, 0.40f, 0.45f); case ERDRoomKind::Torture: return FLinearColor(0.47f, 0.30f, 0.28f);
	case ERDRoomKind::Storeroom: return FLinearColor(0.52f, 0.44f, 0.32f); case ERDRoomKind::Armory: return FLinearColor(0.45f, 0.48f, 0.53f);
	case ERDRoomKind::Kitchen: return FLinearColor(0.58f, 0.48f, 0.36f); case ERDRoomKind::Library: return FLinearColor(0.49f, 0.38f, 0.30f);
	case ERDRoomKind::Chapel: return FLinearColor(0.61f, 0.59f, 0.51f); case ERDRoomKind::Crypt: return FLinearColor(0.36f, 0.39f, 0.37f);
	case ERDRoomKind::Treasury: return FLinearColor(0.66f, 0.56f, 0.27f); case ERDRoomKind::GuardRoom: return FLinearColor(0.48f, 0.44f, 0.38f);
	case ERDRoomKind::Forge: return FLinearColor(0.54f, 0.35f, 0.24f); default: return FLinearColor(0.40f, 0.38f, 0.35f);
	}
}

static FLinearColor RDShade(const FLinearColor& C, float K, float A = 1.f) { return FLinearColor(C.R * K, C.G * K, C.B * K, A); }

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

void ARDHUD::DrawDungeon(const FVector2D& S0, const FVector2D& S1, TFunctionRef<FVector2D(const FVector2D&)> ToS, float Tp, bool bOnlyDiscovered, bool bLabels, float Sc)
{
	const float TS = Gen->TileSize;
	const float Now = GetWorld()->GetTimeSeconds();
	UFont* Small = GEngine->GetSmallFont();
	// (a screen rectangle from two world corners, clipped to the map's frame)
	auto Rc = [&](const FVector2D& Wa, const FVector2D& Wb, float Grow, const FLinearColor& C)
	{
		const FVector2D A = ToS(Wa), B = ToS(Wb);
		const FVector2D Lo(FMath::Max(FMath::Min(A.X, B.X) - Grow, S0.X), FMath::Max(FMath::Min(A.Y, B.Y) - Grow, S0.Y));
		const FVector2D Hi(FMath::Min(FMath::Max(A.X, B.X) + Grow, S1.X), FMath::Min(FMath::Max(A.Y, B.Y) + Grow, S1.Y));
		Box(Lo, Hi, C);
	};
	auto Dot = [&](const FVector2D& W, float Half, const FLinearColor& C)
	{
		const FVector2D Q = ToS(W);
		Box(FVector2D(FMath::Max(Q.X - Half, S0.X), FMath::Max(Q.Y - Half, S0.Y)), FVector2D(FMath::Min(Q.X + Half, S1.X), FMath::Min(Q.Y + Half, S1.Y)), C);
	};
	auto Shown = [&](const FRDMapRect& R) { return R.bDiscovered || !bOnlyDiscovered; };
	const float Wall = FMath::Clamp(Tp * 0.24f, 1.5f, 7.f);
	// ---- walls: every room and hallway grown by the wall's thickness, under all the floors (so doorways stay open)
	for (const auto& KV : Gen->MapData)
		for (const FRDMapRect& R : KV.Value.Rects)
			if (Shown(R)) Rc(FVector2D(R.Min) * TS, FVector2D(R.Max) * TS, Wall, R.bDiscovered ? FLinearColor(0.10f, 0.09f, 0.08f, 1.f) : FLinearColor(0.09f, 0.10f, 0.12f, 0.8f));
	// ---- floors: hallways first, the rooms over them
	for (int32 Pass = 0; Pass < 2; ++Pass)
		for (const auto& KV : Gen->MapData)
			for (const FRDMapRect& R : KV.Value.Rects)
			{
				if (!Shown(R) || R.bCorridor != (Pass == 0)) continue;
				const FVector2D Wa = FVector2D(R.Min) * TS, Wb = FVector2D(R.Max) * TS;
				if (!R.bDiscovered) { Rc(Wa, Wb, 0.f, R.bCorridor ? FLinearColor(0.16f, 0.17f, 0.19f, 0.9f) : FLinearColor(0.20f, 0.21f, 0.24f, 0.9f)); continue; }
				const FLinearColor F = RDFloor(R.Kind, R.bCorridor);
				Rc(Wa, Wb, 0.f, F);
				// paving joints: one a tile
				if (Tp >= 6.f)
				{
					const FLinearColor J = RDShade(F, 0.72f, 0.55f);
					for (int32 X = R.Min.X + 1; X < R.Max.X; ++X) Rc(FVector2D(X * TS, R.Min.Y * TS), FVector2D(X * TS, R.Max.Y * TS), 0.5f, J);
					for (int32 Y = R.Min.Y + 1; Y < R.Max.Y; ++Y) Rc(FVector2D(R.Min.X * TS, Y * TS), FVector2D(R.Max.X * TS, Y * TS), 0.5f, J);
				}
				if (!R.bCorridor)
				{
					// light falls from the top left: a lit edge under the north and west walls, their shadow by the south and east ones
					const FVector2D A = ToS(Wa), B = ToS(Wb);
					const FVector2D Lo(FMath::Min(A.X, B.X), FMath::Min(A.Y, B.Y)), Hi(FMath::Max(A.X, B.X), FMath::Max(A.Y, B.Y));
					const float E = FMath::Max(1.5f, Wall * 0.6f);
					auto Clip = [&](FVector2D P0, FVector2D P1, const FLinearColor& C) { Box(FVector2D(FMath::Max(P0.X, S0.X), FMath::Max(P0.Y, S0.Y)), FVector2D(FMath::Min(P1.X, S1.X), FMath::Min(P1.Y, S1.Y)), C); };
					Clip(Lo, FVector2D(Hi.X, Lo.Y + E * 1.6f), RDShade(F, 0.55f, 0.75f)); Clip(Lo, FVector2D(Lo.X + E * 1.6f, Hi.Y), RDShade(F, 0.62f, 0.6f));
					Clip(FVector2D(Lo.X, Hi.Y - E), Hi, RDShade(F, 1.35f, 0.55f)); Clip(FVector2D(Hi.X - E, Lo.Y), Hi, RDShade(F, 1.25f, 0.45f));
				}
			}
	// ---- what stands in the rooms she has seen: torches, chests; the doors
	auto Seen = [&](const FRDSectionMap& M, const FVector2D& W, float Pad)
	{
		for (const FRDMapRect& R : M.Rects)
			if (R.bDiscovered && W.X >= R.Min.X * TS - Pad && W.Y >= R.Min.Y * TS - Pad && W.X <= R.Max.X * TS + Pad && W.Y <= R.Max.Y * TS + Pad) return true;
		return false;
	};
	for (const auto& KV : Gen->MapData)
	{
		const FRDSectionMap& M = KV.Value;
		if (Tp >= 4.f)
		{
			int32 I = 0;
			for (const FVector2D& T : M.Torches)
			{
				++I;
				if (!Seen(M, T, 30.f)) continue;
				const float Fl = 0.75f + 0.25f * FMath::Sin(Now * 9.f + I * 1.7f);
				Dot(T, Tp * 0.55f, FLinearColor(1.f, 0.55f, 0.15f, 0.13f * Fl)); Dot(T, Tp * 0.28f, FLinearColor(1.f, 0.62f, 0.2f, 0.22f * Fl));
				Dot(T, FMath::Max(1.2f, Tp * 0.09f), FLinearColor(1.f, 0.85f, 0.45f, 0.95f));
			}
			for (const FVector2D& C : M.Chests)
			{
				if (!Seen(M, C, 0.f)) continue;
				const float H = FMath::Max(1.6f, Tp * 0.17f);
				Dot(C, H + 1.f, FLinearColor(0.16f, 0.10f, 0.05f, 1.f)); Dot(C, H, FLinearColor(0.56f, 0.36f, 0.14f, 1.f)); Dot(C, FMath::Max(0.8f, H * 0.35f), FLinearColor(0.95f, 0.78f, 0.3f, 1.f));
			}
		}
		for (const FVector2D& D : M.Doors)
		{
			if (bOnlyDiscovered && !Seen(M, D, TS)) continue;
			const float H = FMath::Max(2.f, Tp * 0.26f);
			Dot(D, H + 1.f, FLinearColor(0.12f, 0.07f, 0.03f, 1.f)); Dot(D, H, FLinearColor(0.60f, 0.36f, 0.14f, 1.f));
		}
		// a section that was just generated
		const float Age = Now - M.GeneratedTime;
		if (M.GeneratedTime >= 0.f && Age < 4.f)
		{
			const FIntPoint T0 = Gen->SectionMinTile(M.Coord);
			Rc(FVector2D(T0) * TS, FVector2D(T0 + FIntPoint(Gen->SectionTiles)) * TS, 0.f, FLinearColor(RDCyan.R, RDCyan.G, RDCyan.B, 0.22f * (1.f - Age / 4.f)));
		}
	}
	// ---- the rooms' names
	if (bLabels)
		for (const auto& KV : Gen->MapData)
			for (const FRDMapRect& R : KV.Value.Rects)
			{
				if (!R.bDiscovered || R.bCorridor || R.Kind == ERDRoomKind::Junction) continue;
				const FVector2D A = ToS(FVector2D(R.Min) * TS), B = ToS(FVector2D(R.Max) * TS);
				const FVector2D Lo(FMath::Min(A.X, B.X), FMath::Min(A.Y, B.Y)), Hi(FMath::Max(A.X, B.X), FMath::Max(A.Y, B.Y));
				FString N = ARDDungeonGenerator::KindName(R.Kind);
				float Tw, Th; GetTextSize(N, Tw, Th, Small, Sc * 0.95f);
				if (Tw >= Hi.X - Lo.X - 6.f) { N = KindCode(R.Kind); GetTextSize(N, Tw, Th, Small, Sc * 0.95f); }
				if (Tw >= Hi.X - Lo.X - 2.f || Th >= Hi.Y - Lo.Y) continue;
				const FVector2D P((Lo.X + Hi.X - Tw) * 0.5f, (Lo.Y + Hi.Y - Th) * 0.5f);
				Box(P - FVector2D(4.f * Sc, 1.f * Sc), P + FVector2D(Tw + 4.f * Sc, Th + 1.f * Sc), FLinearColor(0.04f, 0.035f, 0.03f, 0.62f));
				DrawText(N, FLinearColor(1.f, 0.94f, 0.78f), P.X, P.Y, Small, Sc * 0.95f);
			}
}

void ARDHUD::DrawCombat(float Sc)
{
	URDCombatComponent* Cb = Gen->GetPlayerCombat();
	if (!Cb) return;
	UFont* Small = GEngine->GetSmallFont();
	UFont* Medium = GEngine->GetMediumFont();
	const float Now = GetWorld()->GetTimeSeconds();
	const APawn* P = GetOwningPawn();
	const FVector L = P ? P->GetActorLocation() : FVector::ZeroVector;
	const bool bPad = Gen->bCasterControls && Cb->IsUsingGamepad();
	// ---- she was just hurt: the edges of the view flash red
	const float Hurt = Now - Cb->LastHurtTime;
	if (Hurt < 0.5f)
	{
		const FLinearColor C(0.85f, 0.05f, 0.03f, 0.34f * (1.f - Hurt / 0.5f));
		const float E = 46.f * Sc;
		Box(FVector2D(0, 0), FVector2D(Canvas->ClipX, E), C); Box(FVector2D(0, Canvas->ClipY - E), FVector2D(Canvas->ClipX, Canvas->ClipY), C);
		Box(FVector2D(0, E), FVector2D(E, Canvas->ClipY - E), C); Box(FVector2D(Canvas->ClipX - E, E), FVector2D(Canvas->ClipX, Canvas->ClipY - E), C);
	}
	// ---- a bar over each monster in the fight
	for (const ARDMonster* Mo : Gen->GetMonsters())
	{
		if (!Mo || Mo->IsDead() || (!Mo->IsAggro() && Now - Mo->LastHurtTime > 6.f)) continue;
		if (FVector::Dist2D(Mo->GetActorLocation(), L) > 2400.f) continue;
		const FVector S = Project(Mo->GetActorLocation() + FVector(0, 0, Mo->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 34.f), false);
		if (S.Z <= 0.f || S.X < 0.f || S.Y < 0.f || S.X > Canvas->ClipX || S.Y > Canvas->ClipY) continue;
		const float W = 96.f * Sc, H = 8.f * Sc, F = Mo->GetHealth() / FMath::Max(Mo->GetMaxHealth(), 1.f);
		const FVector2D A(S.X - W * 0.5f, S.Y - H);
		Box(A - FVector2D(2.f), A + FVector2D(W + 2.f, H + 2.f), FLinearColor(0.02f, 0.02f, 0.02f, 0.8f));
		Box(A, A + FVector2D(W * F, H), F > 0.5f ? FLinearColor(0.85f, 0.2f, 0.14f) : FLinearColor(0.95f, 0.45f, 0.1f));
		const FString N = FString::Printf(TEXT("%s  %.0f"), *Mo->MonsterName.ToString().Replace(TEXT("_"), TEXT(" ")).ToUpper(), Mo->GetHealth());
		float Tw, Th; GetTextSize(N, Tw, Th, Small, Sc);
		DrawText(N, RDInk, S.X - Tw * 0.5f, A.Y - Th - 3.f * Sc, Small, Sc);
	}
	// ---- the damage numbers float up from where a blow landed
	for (const ARDDungeonGenerator::FHitText& T : Gen->HitTexts)
	{
		const float Age = Now - T.Time;
		if (Age < 0.f || Age > 1.1f) continue;
		const FVector S = Project(T.At + FVector(0, 0, 70.f * Age), false);
		if (S.Z <= 0.f) continue;
		const FString N = FString::Printf(TEXT("%s%.0f"), T.bOnPlayer ? TEXT("-") : TEXT(""), T.Amount);
		const float K = Sc * (T.bOnPlayer ? 1.7f : 1.9f);
		float Tw, Th; GetTextSize(N, Tw, Th, Medium, K);
		const float Al = FMath::Clamp(1.6f - Age * 1.5f, 0.f, 1.f);
		DrawText(N, FLinearColor(0.f, 0.f, 0.f, Al * 0.8f), S.X - Tw * 0.5f + 2.f, S.Y - Th + 2.f, Medium, K);
		DrawText(N, T.bOnPlayer ? FLinearColor(1.f, 0.25f, 0.2f, Al) : FLinearColor(1.f, 0.9f, 0.35f, Al), S.X - Tw * 0.5f, S.Y - Th, Medium, K);
	}
	// ---- status panel (bottom right): hit points, the weapons with their damage, kills
	{
		const float W = 400.f * Sc, H = 176.f * Sc, Mg = 24.f * Sc, Pd = 14.f * Sc;
		const FVector2D A(Canvas->ClipX - Mg - W, Canvas->ClipY - Mg - H), B = A + FVector2D(W, H);
		Box(A, B, FLinearColor(0.04f, 0.05f, 0.07f, 0.78f));
		Frame(A, B, FLinearColor(0.75f, 0.65f, 0.45f, 0.9f), 2.f * Sc);
		DrawText(Gen->PlayerTitle, RDInk, A.X + Pd, A.Y + 9.f * Sc, Small, Sc * 1.1f);
		const FString Kl = FString::Printf(TEXT("KILLS  %d"), Cb->Kills);
		float Tw, Th; GetTextSize(Kl, Tw, Th, Small, Sc * 1.1f);
		DrawText(Kl, RDInk, B.X - Pd - Tw, A.Y + 9.f * Sc, Small, Sc * 1.1f);
		// hit points
		const float Fr = Cb->GetHealth() / FMath::Max(Cb->GetMaxHealth(), 1.f);
		const FVector2D H0(A.X + Pd, A.Y + 36.f * Sc), H1(B.X - Pd, A.Y + 64.f * Sc);
		Box(H0, H1, FLinearColor(0.10f, 0.03f, 0.03f, 0.95f));
		const FLinearColor Hc = Fr > 0.5f ? FLinearColor(0.20f, 0.72f, 0.26f) : Fr > 0.25f ? FLinearColor(0.90f, 0.62f, 0.12f) : FLinearColor(0.88f, 0.16f, 0.12f);
		Box(H0 + FVector2D(2.f), FVector2D(H0.X + 2.f + (H1.X - H0.X - 4.f) * Fr, H1.Y - 2.f), Hc);
		Frame(H0, H1, FLinearColor(0.75f, 0.65f, 0.45f, 0.9f), 1.5f * Sc);
		const FString Hp = FString::Printf(TEXT("HP  %.0f / %.0f"), FMath::CeilToFloat(Cb->GetHealth()), Cb->GetMaxHealth());
		GetTextSize(Hp, Tw, Th, Small, Sc * 1.2f);
		DrawText(Hp, FLinearColor::White, (H0.X + H1.X - Tw) * 0.5f, (H0.Y + H1.Y - Th) * 0.5f, Small, Sc * 1.2f);
		// the weapons
		const int32 Num = Gen->Weapons.Num();
		const float Gp = 8.f * Sc, Sw = Num > 0 ? (W - Pd * 2.f - Gp * (Num - 1)) / Num : 0.f;
		for (int32 I = 0; I < Num; ++I)
		{
			const FRDWeaponDef& Wp = Gen->Weapons[I];
			const bool bOn = Wp.bAlongside ? Cb->GetAttackIndex() == I : I == Cb->GetWeaponIndex();
			const FVector2D S0(A.X + Pd + I * (Sw + Gp), A.Y + 76.f * Sc), S1 = S0 + FVector2D(Sw, 66.f * Sc);
			Box(S0, S1, bOn ? FLinearColor(0.36f, 0.27f, 0.10f, 0.95f) : FLinearColor(0.10f, 0.10f, 0.12f, 0.9f));
			Frame(S0, S1, bOn ? FLinearColor(1.f, 0.82f, 0.35f) : FLinearColor(0.40f, 0.38f, 0.34f), (bOn ? 2.5f : 1.f) * Sc);
			const FLinearColor Tc = bOn ? FLinearColor::White : FLinearColor(0.72f, 0.70f, 0.66f);
			// (its key: the one that draws it, or casts it when it is cast alongside; on the gamepad the button it is used with)
			FString Key = Wp.bAlongside ? FString(TEXT("RMB / E")) : FString::Printf(TEXT("%d"), I + 1);
			if (bPad) Key = Wp.bAlongside ? FString(TEXT("LB")) : (Wp.bSpell && Cb->GetAlongsideSpell() < 0) ? FString(TEXT("LB / RB")) : FString(TEXT("RB"));
			if (bPad && Gen->bRogueControls) Key = bOn ? FString(TEXT("RB")) : FString(TEXT("Y"));      // (the rogue: Y draws it, RB uses it)
			DrawText(Key, bOn ? FLinearColor(1.f, 0.82f, 0.35f) : Tc, S0.X + 7.f * Sc, S0.Y + 4.f * Sc, Small, Sc);
			const FString N = Wp.Name.ToString().ToUpper();
			GetTextSize(N, Tw, Th, Small, Sc * 1.15f);
			DrawText(N, Tc, (S0.X + S1.X - Tw) * 0.5f, S0.Y + 16.f * Sc, Small, Sc * 1.15f);
			const FString D = FString::Printf(TEXT("%.0f damage"), Wp.Damage);
			GetTextSize(D, Tw, Th, Small, Sc);
			DrawText(D, bOn ? FLinearColor(1.f, 0.9f, 0.6f) : Tc, (S0.X + S1.X - Tw) * 0.5f, S0.Y + 40.f * Sc, Small, Sc);
		}
		if (!Gen->ControlsHint.IsEmpty()) DrawText(Gen->ControlsHint, FLinearColor(0.7f, 0.68f, 0.62f), A.X + Pd, B.Y - 26.f * Sc, Small, Sc);
	}
	// ---- the controls (upper left, the magic levels): those of the device in use, and whether she walks or runs
	const TArray<FString>& Lines = bPad ? Gen->ControlsPad : Gen->ControlsKeys;
	if (Gen->bCasterControls && Lines.Num() > 0)
	{
		const float Mg = 24.f * Sc, Pd = 14.f * Sc, Lh = 23.f * Sc, K = Sc * 1.05f;
		TArray<FString> Keys, Whats;
		float Kw = 0.f, Ww = 0.f, Tw, Th;
		for (const FString& S : Lines)
		{
			FString Kt, Wt;
			if (!S.Split(TEXT("|"), &Kt, &Wt)) { Kt = S; Wt = FString(); }
			Keys.Add(Kt); Whats.Add(Wt);
			GetTextSize(Kt, Tw, Th, Small, K); Kw = FMath::Max(Kw, Tw);
			GetTextSize(Wt, Tw, Th, Small, K); Ww = FMath::Max(Ww, Tw);
		}
		const FString Title = bPad ? TEXT("CONTROLS  -  GAMEPAD") : TEXT("CONTROLS  -  KEYBOARD & MOUSE");
		const FString Mode = Cb->IsRunMode() ? TEXT("RUNNING") : TEXT("WALKING");
		float Tiw, Mw;
		GetTextSize(Title, Tiw, Th, Small, Sc * 1.1f); GetTextSize(Mode, Mw, Th, Small, Sc * 1.1f);
		const float W = FMath::Max(Kw + 18.f * Sc + Ww, Tiw + 24.f * Sc + Mw) + Pd * 2.f;
		const FVector2D A(Mg, Mg), B(Mg + W, Mg + 40.f * Sc + Lh * Lines.Num() + 8.f * Sc);
		Box(A, B, FLinearColor(0.04f, 0.05f, 0.07f, 0.72f));
		Frame(A, B, FLinearColor(0.75f, 0.65f, 0.45f, 0.9f), 2.f * Sc);
		DrawText(Title, RDInk, A.X + Pd, A.Y + 9.f * Sc, Small, Sc * 1.1f);
		DrawText(Mode, Cb->IsRunMode() ? FLinearColor(1.f, 0.62f, 0.25f) : RDCyan, B.X - Pd - Mw, A.Y + 9.f * Sc, Small, Sc * 1.1f);
		for (int32 I = 0; I < Keys.Num(); ++I)
		{
			const float Y = A.Y + 40.f * Sc + Lh * I;
			DrawText(Keys[I], FLinearColor(1.f, 0.82f, 0.35f), A.X + Pd, Y, Small, K);
			DrawText(Whats[I], FLinearColor(0.86f, 0.84f, 0.78f), A.X + Pd + Kw + 18.f * Sc, Y, Small, K);
		}
	}
	// ---- she is down
	if (Cb->IsDead())
	{
		Box(FVector2D(0, 0), FVector2D(Canvas->ClipX, Canvas->ClipY), FLinearColor(0.10f, 0.f, 0.f, FMath::Clamp((Now - Cb->DeathTime) / 1.2f, 0.f, 0.55f)));
		const FString T = TEXT("YOU HAVE FALLEN");
		float Tw, Th; GetTextSize(T, Tw, Th, Medium, Sc * 2.6f);
		DrawText(T, FLinearColor(0.95f, 0.2f, 0.15f), (Canvas->ClipX - Tw) * 0.5f, Canvas->ClipY * 0.4f, Medium, Sc * 2.6f);
		const FString U = TEXT("back to the middle of the dungeon...");
		GetTextSize(U, Tw, Th, Small, Sc * 1.3f);
		DrawText(U, RDInk, (Canvas->ClipX - Tw) * 0.5f, Canvas->ClipY * 0.4f + 62.f * Sc, Small, Sc * 1.3f);
	}
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
	const bool bStyle = Gen->bStylizedMap;
	// (the magic levels on the gamepad: Back opens and closes the map)
	const bool bPadMap = Gen->bCasterControls && Gen->GetPlayerCombat() && Gen->GetPlayerCombat()->IsUsingGamepad();

	// (the tactical big map is an overlay: the game, its panels and prompts go on under it)
	const bool bTac = Gen->bTacticalMaps;
	const bool bBigMap = Gen->bMapOpen && !bTac;
	if (bTac && Gen->bMapOpen) DrawTacticalMap(Sc, L, Yaw);
	if (Gen->bCombat && !bBigMap) DrawCombat(Sc);
	if (bTac && !Gen->bMapOpen) DrawTacticalMinimap(Sc, L, Yaw);

	// ---- minimap (top right), north (+X) up: screen right = world +Y, screen up = world +X
	if (!bTac)
	{
		const float Px = MinimapPixels * Sc, Mg = 24.f * Sc;
		const FVector2D S0(Canvas->ClipX - Mg - Px, Mg + 26.f * Sc), S1 = S0 + FVector2D(Px);
		Box(S0 - FVector2D(8.f * Sc, 34.f * Sc), S1 + FVector2D(8.f * Sc, 30.f * Sc), FLinearColor(0.04f, 0.05f, 0.07f, 0.72f));
		Box(S0, S1, FLinearColor(0.02f, 0.02f, 0.03f, 0.85f));
		const float Half = (bStyle ? StylizedMinimapMeters : MinimapMeters) * 50.f;
		// (the map frame: world (Y, -X) is the screen's (x, y))
		const FVector2D WMin(L.Y - Half, -L.X - Half), WMax(L.Y + Half, -L.X + Half);
		const float TS = Gen->TileSize;
		auto ToS = [&](const FVector2D& Wd) { const FVector2D Q(Wd.Y, -Wd.X); return S0 + (Q - WMin) / (WMax - WMin) * (S1 - S0); };
		auto Clip = [&](FVector2D A, FVector2D B, FVector2D& OA, FVector2D& OB)
		{
			const FVector2D Lo(FMath::Min(A.X, B.X), FMath::Min(A.Y, B.Y)), Hi(FMath::Max(A.X, B.X), FMath::Max(A.Y, B.Y));
			OA = FVector2D(FMath::Max(Lo.X, S0.X), FMath::Max(Lo.Y, S0.Y)); OB = FVector2D(FMath::Min(Hi.X, S1.X), FMath::Min(Hi.Y, S1.Y));
			return OB.X > OA.X && OB.Y > OA.Y;
		};
		if (bStyle) DrawDungeon(S0, S1, ToS, Px / (Half * 2.f) * TS, false, false, Sc);
		for (const auto& KV : Gen->MapData)
		{
			const FRDSectionMap& M = KV.Value;
			if (!bStyle)
			{
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
			}
			const float Age = Now - M.GeneratedTime;
			if (M.GeneratedTime >= 0.f && Age < 4.f)
			{
				const FIntPoint T0 = Gen->SectionMinTile(M.Coord);
				FVector2D CA, CB;
				if (Clip(ToS(FVector2D(T0) * TS), ToS(FVector2D(T0 + FIntPoint(Gen->SectionTiles)) * TS), CA, CB))
				{
					const float Al = 1.f - Age / 4.f;
					if (!bStyle) Box(CA, CB, FLinearColor(RDCyan.R, RDCyan.G, RDCyan.B, 0.22f * Al));
					Frame(CA, CB, FLinearColor(RDCyan.R, RDCyan.G, RDCyan.B, Al), 2.f * Sc);
				}
			}
		}
		for (ARDMonster* Mo : Gen->GetMonsters())
		{
			if (!Mo || Mo->IsDead()) continue;
			const FVector Ml = Mo->GetActorLocation();
			if (FVector::Dist2D(Ml, L) > 2500.f) continue;     // sensed nearby
			const FVector2D Q = ToS(FVector2D(Ml.X, Ml.Y));
			if (Q.X > S0.X + 4.f && Q.Y > S0.Y + 4.f && Q.X < S1.X - 4.f && Q.Y < S1.Y - 4.f)
			{
				const float H = (Mo->IsAggro() ? 4.5f : 3.f) * Sc;
				if (Mo->IsAggro()) Box(Q - FVector2D(H + 2.f * Sc), Q + FVector2D(H + 2.f * Sc), FLinearColor(1.f, 0.9f, 0.3f, 0.9f));
				Box(Q - FVector2D(H), Q + FVector2D(H), FLinearColor(0.95f, 0.15f, 0.12f, 1.f));
			}
		}
		Frame(S0, S1, FLinearColor(0.75f, 0.65f, 0.45f, 0.9f), 2.f * Sc);
		DrawPlayerArrow((S0 + S1) * 0.5f, Yaw - 90.f, 9.f * Sc);
		DrawText(TEXT("DUNGEON"), RDInk, S0.X, S0.Y - 28.f * Sc, Small, Sc * 1.1f);
		const FString Cnt = FString::Printf(TEXT("%d / %d rooms"), Disc, All);
		float Tw, Th; GetTextSize(Cnt, Tw, Th, Small, Sc * 1.1f);
		DrawText(Cnt, RDInk, S1.X - Tw, S0.Y - 28.f * Sc, Small, Sc * 1.1f);
		DrawText(TEXT("N"), RDInk, (S0.X + S1.X) * 0.5f - 4.f * Sc, S0.Y + 2.f * Sc, Small, Sc);
		DrawText(bPadMap ? TEXT("Back  map") : TEXT("M  map"), FLinearColor(0.7f, 0.68f, 0.62f), S0.X, S1.Y + 6.f * Sc, Small, Sc);
	}

	// ---- new section banner
	if (Now - Gen->LastRevealTime < 3.5f)
	{
		const float A = FMath::Clamp(FMath::Min((Now - Gen->LastRevealTime) / 0.3f, (3.5f - (Now - Gen->LastRevealTime)) / 0.8f), 0.f, 1.f);
		const FString T = TEXT("▲ NEW DUNGEON SECTION GENERATED");
		float Tw, Th; GetTextSize(T, Tw, Th, Medium, Sc * 1.4f);
		DrawText(T, FLinearColor(RDCyan.R, RDCyan.G, RDCyan.B, A), (Canvas->ClipX - Tw) * 0.5f, 90.f * Sc, Medium, Sc * 1.4f);
	}

	// ---- interaction prompt
	const FString What = Gen->DescribeNearest(L);
	if (!What.IsEmpty() && !bBigMap)
	{
		const URDCombatComponent* Cb = Gen->GetPlayerCombat();
		const FString T = FString::Printf(TEXT("[%s]  %s"), (Gen->bCasterControls && Cb && Cb->IsUsingGamepad()) ? TEXT("X") : TEXT("F"), *What);
		float Tw, Th; GetTextSize(T, Tw, Th, Medium, Sc * 1.2f);
		const float X = (Canvas->ClipX - Tw) * 0.5f, Y = Canvas->ClipY * 0.72f;
		Box(FVector2D(X - 14.f * Sc, Y - 8.f * Sc), FVector2D(X + Tw + 14.f * Sc, Y + Th + 8.f * Sc), FLinearColor(0.03f, 0.03f, 0.04f, 0.6f));
		DrawText(T, FLinearColor(0.95f, 0.9f, 0.78f), X, Y, Medium, Sc * 1.2f);
	}

	// ---- full map (M): everything discovered, fitted to the screen, north up
	if (bBigMap)
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
		if (bStyle) DrawDungeon(A0, A1, ToS, K * TS, true, true, Sc);
		else for (const auto& KV : Gen->MapData)
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
		if (bStyle)
			for (const ARDMonster* Mo : Gen->GetMonsters())
			{
				if (!Mo || Mo->IsDead() || FVector::Dist2D(Mo->GetActorLocation(), L) > 2500.f) continue;
				const FVector2D Q = ToS(FVector2D(Mo->GetActorLocation().X, Mo->GetActorLocation().Y));
				if (Q.X > A0.X && Q.Y > A0.Y && Q.X < A1.X && Q.Y < A1.Y) Box(Q - FVector2D(4.f * Sc), Q + FVector2D(4.f * Sc), FLinearColor(0.95f, 0.15f, 0.12f, 1.f));
			}
		DrawPlayerArrow(ToS(FVector2D(L.X, L.Y)), Yaw - 90.f, 12.f * Sc);
		DrawText(TEXT("DUNGEON MAP"), RDInk, 80.f * Sc, 40.f * Sc, Medium, Sc * 1.6f);
		const FString Sub = FString::Printf(TEXT("%d rooms discovered of %d generated  ·  %d sections  ·  %s  close"), Disc, All, Gen->MapData.Num(), bPadMap ? TEXT("Back") : TEXT("M"));
		DrawText(Sub, FLinearColor(0.75f, 0.72f, 0.65f), 82.f * Sc, 78.f * Sc, Small, Sc * 1.1f);
		// legend: room codes
		float Y = Canvas->ClipY - 64.f * Sc, X = 82.f * Sc;
		for (int32 Kd = (int32)ERDRoomKind::Hall; Kd < (int32)ERDRoomKind::Junction; ++Kd)
		{
			const FString E = FString::Printf(TEXT("%s %s"), *KindCode((ERDRoomKind)Kd), *ARDDungeonGenerator::KindName((ERDRoomKind)Kd));
			float Tw, Th; GetTextSize(E, Tw, Th, Small, Sc);
			if (X + Tw > Canvas->ClipX - 80.f * Sc) { X = 82.f * Sc; Y += 22.f * Sc; }
			if (bStyle) Box(FVector2D(X - 16.f * Sc, Y + 3.f * Sc), FVector2D(X - 4.f * Sc, Y + 15.f * Sc), RDFloor((ERDRoomKind)Kd, false));
			DrawText(E, FLinearColor(0.75f, 0.72f, 0.65f), X, Y, Small, Sc);
			X += Tw + (bStyle ? 40.f : 24.f) * Sc;
		}
	}
}

// ------------------------------------------------------------------------------------------------ tactical maps
// (generator bTacticalMaps) The minimap: dark monochrome terrain (floors, a lighter line where a wall is) fading out to
// a feathered rim, no frame, and bright markers over it. The big map: an overlay centred on her, north up, that moves
// as she does; only lines (walls and passage borders where a floor tile meets no floor, doorways as bars) over the game,
// and bright shapes for what matters.
static const FLinearColor RDTacRed(1.f, 0.16f, 0.10f, 1.f);
static const FLinearColor RDTacElite(1.f, 0.55f, 0.08f, 1.f);
static const FLinearColor RDTacGold(1.f, 0.82f, 0.22f, 1.f);
static const FLinearColor RDTacExit(0.25f, 0.95f, 1.f, 1.f);
static const FLinearColor RDTacWire(0.30f, 0.95f, 1.f, 1.f);
static const FLinearColor RDTacDoor(1.f, 0.90f, 0.50f, 1.f);
static FLinearColor RDTacA(const FLinearColor& C, float A) { return FLinearColor(C.R, C.G, C.B, C.A * A); }

UTexture2D* ARDHUD::GetSoftDisc()
{
	if (SoftDisc) return SoftDisc;
	const int32 N = 64;
	UTexture2D* T = UTexture2D::CreateTransient(N, N, PF_B8G8R8A8);
	if (!T || !T->GetPlatformData() || T->GetPlatformData()->Mips.Num() == 0) return nullptr;
	FTexture2DMipMap& Mip = T->GetPlatformData()->Mips[0];
	uint8* D = static_cast<uint8*>(Mip.BulkData.Lock(LOCK_READ_WRITE));
	for (int32 Y = 0; Y < N; ++Y)
		for (int32 X = 0; X < N; ++X)
		{
			const float R = FVector2D(X + 0.5f - N * 0.5f, Y + 0.5f - N * 0.5f).Size() / (N * 0.5f);
			const float A = FMath::Clamp(1.f - FMath::SmoothStep(0.4f, 1.f, R), 0.f, 1.f);
			uint8* Px = D + (Y * N + X) * 4; Px[0] = Px[1] = Px[2] = 255; Px[3] = (uint8)FMath::RoundToInt(A * 255.f);
		}
	Mip.BulkData.Unlock();
	T->Filter = TF_Bilinear;
	T->UpdateResource();
	SoftDisc = T;
	return T;
}

void ARDHUD::SoftDot(const FVector2D& P, float R, const FLinearColor& C)
{
	if (UTexture2D* T = GetSoftDisc()) DrawTexture(T, P.X - R, P.Y - R, R * 2.f, R * 2.f, 0.f, 0.f, 1.f, 1.f, C, BLEND_Translucent);
}

/** a filled polygon round P: lines fanned from P to every edge, then its outline */
static void RDFan(ARDHUD* H, const FVector2D& P, const TArray<FVector2D>& V, const FLinearColor& C, const FLinearColor& Edge)
{
	for (int32 I = 0; I < V.Num(); ++I)
	{
		const FVector2D A = V[I], B = V[(I + 1) % V.Num()];
		const int32 Steps = FMath::Max(2, FMath::CeilToInt(FVector2D::Distance(A, B) / 1.2f));
		for (int32 K = 0; K <= Steps; ++K) { const FVector2D Q = FMath::Lerp(A, B, K / float(Steps)); H->DrawLine(P.X, P.Y, Q.X, Q.Y, C, 1.6f); }
	}
	for (int32 I = 0; I < V.Num(); ++I) { const FVector2D A = V[I], B = V[(I + 1) % V.Num()]; H->DrawLine(A.X, A.Y, B.X, B.Y, Edge, 1.2f); }
}

void ARDHUD::Star(const FVector2D& P, float R, const FLinearColor& C)
{
	TArray<FVector2D> V;
	for (int32 K = 0; K < 10; ++K) { const float A = -PI * 0.5f + K * PI / 5.f, Rr = (K % 2) ? R * 0.45f : R; V.Add(P + FVector2D(FMath::Cos(A), FMath::Sin(A)) * Rr); }
	RDFan(this, P, V, C, FLinearColor(1.f, 0.97f, 0.8f, C.A));
}

void ARDHUD::Diamond(const FVector2D& P, float R, const FLinearColor& C)
{
	RDFan(this, P, { P + FVector2D(0, -R), P + FVector2D(R * 0.75f, 0), P + FVector2D(0, R), P + FVector2D(-R * 0.75f, 0) }, C, FLinearColor(0.85f, 1.f, 1.f, C.A));
}

void ARDHUD::Triangle(const FVector2D& P, float R, const FLinearColor& C)
{
	RDFan(this, P, { P + FVector2D(0, -R), P + FVector2D(R * 0.9f, R * 0.65f), P + FVector2D(-R * 0.9f, R * 0.65f) }, C, FLinearColor(1.f, 0.9f, 0.6f, C.A));
}

bool ARDHUD::IsElite(const ARDMonster* M) const
{
	if (!M || !M->Section || !Gen) return false;
	const float Avg = Gen->GetMonsterHealth(M->Section->Coord);
	return Avg > 0.f && M->GetMaxHealth() > Avg * 1.25f;
}

void ARDHUD::CacheTiles()
{
	int32 Sig = 17 + Gen->MapData.Num();
	for (const auto& KV : Gen->MapData)
		for (const FRDMapRect& R : KV.Value.Rects) Sig = Sig * 31 + (R.Min.X * 7 + R.Min.Y * 13 + R.Max.X * 3 + R.Max.Y) * 2 + (R.bDiscovered ? 1 : 0);
	if (Sig == TileSig && Tiles.Num() > 0) return;
	TileSig = Sig; Tiles.Reset();
	for (const auto& KV : Gen->MapData)
		for (const FRDMapRect& R : KV.Value.Rects)
			for (int32 X = R.Min.X; X < R.Max.X; ++X)
				for (int32 Y = R.Min.Y; Y < R.Max.Y; ++Y) Tiles.FindOrAdd(FIntPoint(X, Y)) |= 1 | (R.bDiscovered ? 2 : 0) | (R.bCorridor ? 4 : 0);
}

void ARDHUD::GatherPois(TArray<FRDPoi>& Out, const FVector& L, float SenseDistance)
{
	Out.Reset();
	const float TS = Gen->TileSize;
	auto Discovered = [&](const FVector& P) { const uint8* V = Tiles.Find(FIntPoint(FMath::FloorToInt(P.X / TS), FMath::FloorToInt(P.Y / TS))); return V && (*V & 2); };
	for (const ARDMonster* Mo : Gen->GetMonsters())
	{
		if (!Mo || Mo->IsDead() || FVector::Dist2D(Mo->GetActorLocation(), L) > SenseDistance) continue;      // (sensed nearby)
		Out.Add({ FVector2D(Mo->GetActorLocation()), IsElite(Mo) ? 1 : 0 });
	}
	for (const auto& KV : Gen->Sections)
	{
		const ARDSection* S = KV.Value;
		if (!S) continue;
		for (int32 I = 0; I < S->GetNumContainers(); ++I)
		{
			// (the objectives: chests and trunks; the barrels, crates and wardrobes that line the storerooms would bury the map in stars)
			const FString Kd = S->GetContainerKind(I);
			if (S->GetContainerOpenAlpha(I) > 0.05f || (Kd != TEXT("chest") && Kd != TEXT("trunk"))) continue;
			const FVector P = S->GetContainerLocation(I);
			if (Discovered(P)) Out.Add({ FVector2D(P), 2 });
		}
		// a hallway end on the section's border that leads where she has not been: the next section is not generated, or
		// nothing of it is discovered (it is generated as she nears it, so "not generated" alone was hardly ever seen)
		const FVector2D Mid = (FVector2D(Gen->SectionMinTile(S->Coord)) + FVector2D(Gen->SectionTiles * 0.5f)) * TS;
		for (const FVector& P : S->GetPortalPoints())
		{
			const FVector2D D = FVector2D(P) - Mid;
			const FIntPoint Next = S->Coord + (FMath::Abs(D.X) > FMath::Abs(D.Y) ? FIntPoint(D.X > 0 ? 1 : -1, 0) : FIntPoint(0, D.Y > 0 ? 1 : -1));
			const FRDSectionMap* M = Gen->MapData.Find(Next);
			if (!M || !M->Rects.ContainsByPredicate([](const FRDMapRect& R) { return R.bDiscovered; })) Out.Add({ FVector2D(P), 3 });
		}
	}
}

void ARDHUD::DrawTacticalMinimap(float Sc, const FVector& L, float Yaw)
{
	UFont* Small = GEngine->GetSmallFont();
	const float R = MinimapPixels * Sc * 0.5f, Mg = 24.f * Sc;
	const FVector2D C(Canvas->ClipX - Mg - R, Mg + 14.f * Sc + R);
	const float Half = StylizedMinimapMeters * 50.f, K = R / Half, TS = Gen->TileSize, Tp = TS * K;
	auto ToS = [&](const FVector2D& W) { return C + FVector2D(W.Y - L.Y, -(W.X - L.X)) * K; };
	auto Fade = [&](const FVector2D& S) { return FMath::Clamp((1.f - FVector2D::Distance(S, C) / R) / 0.38f, 0.f, 1.f); };
	// the feathered backdrop, no frame
	if (UTexture2D* T = GetSoftDisc()) DrawTexture(T, C.X - R * 1.3f, C.Y - R * 1.3f, R * 2.6f, R * 2.6f, 0.f, 0.f, 1.f, 1.f, FLinearColor(0.004f, 0.005f, 0.007f, 0.92f), BLEND_Translucent);
	CacheTiles();
	const float Now = GetWorld()->GetTimeSeconds();
	TSet<FIntPoint> Fresh;           // (sections generated in the last 4 s: their tiles tinted)
	for (const auto& KV : Gen->MapData) if (KV.Value.GeneratedTime >= 0.f && Now - KV.Value.GeneratedTime < 4.f) Fresh.Add(KV.Key);
	const int32 X0 = FMath::FloorToInt((L.X - Half) / TS), X1 = FMath::FloorToInt((L.X + Half) / TS);
	const int32 Y0 = FMath::FloorToInt((L.Y - Half) / TS), Y1 = FMath::FloorToInt((L.Y + Half) / TS);
	const FLinearColor Room(0.15f, 0.16f, 0.17f, 0.95f), Hall(0.115f, 0.12f, 0.13f, 0.95f), Unknown(0.055f, 0.058f, 0.064f, 0.7f), Wall(0.36f, 0.385f, 0.41f, 0.9f);
	for (int32 X = X0; X <= X1; ++X)
		for (int32 Y = Y0; Y <= Y1; ++Y)
		{
			const uint8* V = Tiles.Find(FIntPoint(X, Y));
			if (!V) continue;
			const FVector2D S = ToS(FVector2D((X + 0.5f) * TS, (Y + 0.5f) * TS));
			const float A = Fade(S);
			if (A <= 0.f) continue;
			FLinearColor Col = (*V & 2) ? ((*V & 4) ? Hall : Room) : Unknown;
			if (Fresh.Num() && Fresh.Contains(Gen->WorldToSection(FVector((X + 0.5f) * TS, (Y + 0.5f) * TS, 0.f)))) Col = FLinearColor(0.16f, 0.32f, 0.36f, Col.A);
			Box(S - FVector2D(Tp * 0.5f + 0.5f), S + FVector2D(Tp * 0.5f + 0.5f), RDTacA(Col, A));
			if (!(*V & 2)) continue;
			// a wall where this floor meets no floor (world +X is up on the screen, +Y right)
			const FVector2D W0(X * TS, Y * TS), W1((X + 1) * TS, (Y + 1) * TS);
			auto Edge = [&](const FVector2D& A_, const FVector2D& B_) { const FVector2D P = ToS(A_), Q = ToS(B_); DrawLine(P.X, P.Y, Q.X, Q.Y, RDTacA(Wall, A), 1.4f * Sc); };
			if (!Tiles.Contains(FIntPoint(X + 1, Y))) Edge(FVector2D(W1.X, W0.Y), FVector2D(W1.X, W1.Y));
			if (!Tiles.Contains(FIntPoint(X - 1, Y))) Edge(FVector2D(W0.X, W0.Y), FVector2D(W0.X, W1.Y));
			if (!Tiles.Contains(FIntPoint(X, Y + 1))) Edge(FVector2D(W0.X, W1.Y), FVector2D(W1.X, W1.Y));
			if (!Tiles.Contains(FIntPoint(X, Y - 1))) Edge(FVector2D(W0.X, W0.Y), FVector2D(W1.X, W0.Y));
		}
	// the markers, bright over the dark ground
	TArray<FRDPoi> Pois; GatherPois(Pois, L, 2500.f);
	for (const FRDPoi& Pi : Pois)
	{
		const FVector2D S = ToS(Pi.W);
		if (FVector2D::Distance(S, C) > R * 0.94f) continue;
		if (Pi.Kind == 2) Star(S, 6.5f * Sc, RDTacGold);
		else if (Pi.Kind == 3) Diamond(S, 5.5f * Sc, RDTacExit);
	}
	for (const FRDPoi& Pi : Pois)
	{
		const FVector2D S = ToS(Pi.W);
		if (FVector2D::Distance(S, C) > R * 0.94f) continue;
		if (Pi.Kind == 0) { SoftDot(S, 9.f * Sc, RDTacA(RDTacRed, 0.35f)); SoftDot(S, 4.6f * Sc, RDTacRed); }
		else if (Pi.Kind == 1) { SoftDot(S, 11.f * Sc, RDTacA(RDTacElite, 0.35f)); Triangle(S, 7.f * Sc, RDTacElite); }
	}
	DrawPlayerArrow(C, Yaw - 90.f, 9.f * Sc);
	int32 Disc = 0, All = 0; Gen->GetDiscoveryStats(Disc, All);
	const FLinearColor Ink(0.75f, 0.77f, 0.8f, 0.85f);
	float Tw, Th;
	DrawText(TEXT("N"), Ink, C.X - 4.f * Sc, C.Y - R * 0.98f, Small, Sc);
	const bool bPad = Gen->bCasterControls && Gen->GetPlayerCombat() && Gen->GetPlayerCombat()->IsUsingGamepad();
	const FString Under = FString::Printf(TEXT("%d / %d rooms    %s  map"), Disc, All, bPad ? TEXT("Back") : TEXT("M"));
	GetTextSize(Under, Tw, Th, Small, Sc);
	DrawText(Under, Ink, C.X - Tw * 0.5f, C.Y + R * 0.96f, Small, Sc);
}

void ARDHUD::DrawTacticalMap(float Sc, const FVector& L, float Yaw)
{
	UFont* Small = GEngine->GetSmallFont(); UFont* Medium = GEngine->GetMediumFont();
	const FVector2D C(Canvas->ClipX * 0.5f, Canvas->ClipY * 0.5f);
	const float K = Canvas->ClipY / (TacticalMapMeters * 100.f), TS = Gen->TileSize;
	auto ToS = [&](const FVector2D& W) { return C + FVector2D(W.Y - L.Y, -(W.X - L.X)) * K; };
	// a light veil only: the game shows through
	Box(FVector2D(0, 0), FVector2D(Canvas->ClipX, Canvas->ClipY), FLinearColor(0.f, 0.012f, 0.02f, 0.28f));
	CacheTiles();
	const float HX = C.Y / K + TS, HY = C.X / K + TS;          // (world half extents shown: screen up = world X)
	const int32 X0 = FMath::FloorToInt((L.X - HX) / TS), X1 = FMath::FloorToInt((L.X + HX) / TS);
	const int32 Y0 = FMath::FloorToInt((L.Y - HY) / TS), Y1 = FMath::FloorToInt((L.Y + HY) / TS);
	// the wireframe: where a discovered floor tile meets no floor, joined into runs along each grid line
	TMap<int32, TArray<int32>> AlongY, AlongX;      // (lines of constant world X, running along Y; lines of constant Y, along X)
	for (int32 X = X0; X <= X1; ++X)
		for (int32 Y = Y0; Y <= Y1; ++Y)
		{
			const uint8* V = Tiles.Find(FIntPoint(X, Y));
			if (!V || !(*V & 2)) continue;
			if (!Tiles.Contains(FIntPoint(X + 1, Y))) AlongY.FindOrAdd(X + 1).Add(Y);
			if (!Tiles.Contains(FIntPoint(X - 1, Y))) AlongY.FindOrAdd(X).Add(Y);
			if (!Tiles.Contains(FIntPoint(X, Y + 1))) AlongX.FindOrAdd(Y + 1).Add(X);
			if (!Tiles.Contains(FIntPoint(X, Y - 1))) AlongX.FindOrAdd(Y).Add(X);
		}
	auto Wire = [&](const FVector2D& A, const FVector2D& B)
	{
		const FVector2D P = ToS(A), Q = ToS(B);
		DrawLine(P.X, P.Y, Q.X, Q.Y, RDTacA(RDTacWire, 0.12f), 6.f * Sc);       // (glow)
		DrawLine(P.X, P.Y, Q.X, Q.Y, RDTacA(RDTacWire, 0.95f), 1.7f * Sc);
	};
	auto Runs = [&](TMap<int32, TArray<int32>>& Lines, bool bAlongY)
	{
		for (auto& KV : Lines)
		{
			TArray<int32>& Ts = KV.Value; Ts.Sort();
			int32 Start = Ts[0], Prev = Ts[0];
			for (int32 I = 1; I <= Ts.Num(); ++I)
			{
				if (I < Ts.Num() && Ts[I] == Prev + 1) { Prev = Ts[I]; continue; }
				if (I < Ts.Num() && Ts[I] == Prev) continue;
				const float Line = KV.Key * TS, A = Start * TS, B = (Prev + 1) * TS;
				if (bAlongY) Wire(FVector2D(Line, A), FVector2D(Line, B)); else Wire(FVector2D(A, Line), FVector2D(B, Line));
				if (I < Ts.Num()) { Start = Prev = Ts[I]; }
			}
		}
	};
	Runs(AlongY, true); Runs(AlongX, false);
	// doorways: a bright bar across the gap in the wall (a door stands on a grid line: the bar runs along it)
	for (const auto& KV : Gen->MapData)
		for (const FVector2D& D : KV.Value.Doors)
		{
			const FVector2D Q = ToS(D);
			if (Q.X < -20.f || Q.Y < -20.f || Q.X > Canvas->ClipX + 20.f || Q.Y > Canvas->ClipY + 20.f) continue;
			const uint8* Va = Tiles.Find(FIntPoint(FMath::FloorToInt((D.X + 30.f) / TS), FMath::FloorToInt((D.Y + 30.f) / TS)));
			const uint8* Vb = Tiles.Find(FIntPoint(FMath::FloorToInt((D.X - 30.f) / TS), FMath::FloorToInt((D.Y - 30.f) / TS)));
			if (!((Va && (*Va & 2)) || (Vb && (*Vb & 2)))) continue;          // (doors of rooms she has found)
			const bool bOnX = FMath::Abs(D.X / TS - FMath::RoundToFloat(D.X / TS)) < FMath::Abs(D.Y / TS - FMath::RoundToFloat(D.Y / TS));
			const FVector2D Half = bOnX ? FVector2D(0.f, TS * 0.36f) : FVector2D(TS * 0.36f, 0.f);
			const FVector2D P0 = ToS(D - Half), P1 = ToS(D + Half);
			DrawLine(P0.X, P0.Y, P1.X, P1.Y, RDTacA(RDTacDoor, 0.25f), 7.f * Sc);
			DrawLine(P0.X, P0.Y, P1.X, P1.Y, RDTacDoor, 3.f * Sc);
		}
	// what matters, as bright shapes
	TArray<FRDPoi> Pois; GatherPois(Pois, L, 2500.f);
	for (const FRDPoi& Pi : Pois)
	{
		const FVector2D S = ToS(Pi.W);
		if (S.X < 0.f || S.Y < 0.f || S.X > Canvas->ClipX || S.Y > Canvas->ClipY) continue;
		if (Pi.Kind == 0) { SoftDot(S, 13.f * Sc, RDTacA(RDTacRed, 0.35f)); SoftDot(S, 6.5f * Sc, RDTacRed); }
		else if (Pi.Kind == 1) { SoftDot(S, 16.f * Sc, RDTacA(RDTacElite, 0.35f)); Triangle(S, 10.f * Sc, RDTacElite); }
		else if (Pi.Kind == 2) Star(S, 10.f * Sc, RDTacGold);
		else Diamond(S, 9.f * Sc, RDTacExit);
	}
	DrawPlayerArrow(C, Yaw - 90.f, 13.f * Sc);
	// title, compass and key
	const bool bPad = Gen->bCasterControls && Gen->GetPlayerCombat() && Gen->GetPlayerCombat()->IsUsingGamepad();
	float Tw, Th;
	const FString Title = TEXT("MAP");
	GetTextSize(Title, Tw, Th, Medium, Sc * 1.3f);
	DrawText(Title, RDTacA(RDTacWire, 0.95f), C.X - Tw * 0.5f, 30.f * Sc, Medium, Sc * 1.3f);
	const FString Sub = FString::Printf(TEXT("N up   ·   %s  close"), bPad ? TEXT("Back") : TEXT("M"));
	GetTextSize(Sub, Tw, Th, Small, Sc);
	DrawText(Sub, FLinearColor(0.8f, 0.92f, 0.95f, 0.85f), C.X - Tw * 0.5f, 30.f * Sc + 36.f * Sc, Small, Sc);
	float Y = Canvas->ClipY - 150.f * Sc; const float X = 40.f * Sc;
	auto Key = [&](int32 Kind, const TCHAR* What)
	{
		const FVector2D P(X, Y + 8.f * Sc);
		if (Kind == 0) SoftDot(P, 6.f * Sc, RDTacRed); else if (Kind == 1) Triangle(P, 8.f * Sc, RDTacElite); else if (Kind == 2) Star(P, 8.f * Sc, RDTacGold);
		else if (Kind == 3) Diamond(P, 7.f * Sc, RDTacExit); else DrawLine(P.X - 8.f * Sc, P.Y, P.X + 8.f * Sc, P.Y, RDTacDoor, 3.f * Sc);
		DrawText(What, FLinearColor(0.85f, 0.92f, 0.95f, 0.9f), X + 18.f * Sc, Y, Small, Sc);
		Y += 24.f * Sc;
	};
	Key(0, TEXT("monster")); Key(1, TEXT("elite")); Key(2, TEXT("unopened chest or trunk")); Key(3, TEXT("unexplored passage")); Key(4, TEXT("door"));
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
