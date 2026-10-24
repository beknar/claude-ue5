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

bool ARDHUD::Board(FName Name, const FVector2D& A, const FVector2D& B, float Sc, float Ext)
{
	const FRDUIArt* Ar = UI.Find(Name);
	if (!Ar) return false;
	// (its frame 1.6 Ext thick on the screen, whatever the picture's size: it reaches 0.6 Ext over what is in it)
	const float Fp = FMath::Max((float)Ar->Border.X * Ar->Texture->GetSizeX(), 1.f);
	return UI.Nine(Name, A - FVector2D(Ext), B + FVector2D(Ext), Ext * 1.6f / Fp);
}

bool ARDHUD::Strip(FName Name, const FVector2D& A, const FVector2D& B, const FLinearColor& Tint)
{
	const FRDUIArt* Ar = UI.Find(Name);
	return Ar && UI.Nine(Name, A, B, (float)(B.Y - A.Y) / FMath::Max((float)Ar->Texture->GetSizeY(), 1.f), Tint);
}

FName ARDHUD::WeaponIcon(int32 I) const
{
	return Gen && Gen->Weapons.IsValidIndex(I) ? Gen->Weapons[I].Icon : NAME_None;
}

FName ARDHUD::ItemIcon(FName Item) const
{
	const int32 Ix = Gen ? Gen->FindItem(Item) : -1;
	return Ix >= 0 ? Gen->Items[Ix].Icon : NAME_None;
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
				float Tw, Th; UI.TextSize(N, Tw, Th, Small, Sc * 0.95f);
				if (Tw >= Hi.X - Lo.X - 6.f) { N = KindCode(R.Kind); UI.TextSize(N, Tw, Th, Small, Sc * 0.95f); }
				if (Tw >= Hi.X - Lo.X - 2.f || Th >= Hi.Y - Lo.Y) continue;
				const FVector2D P((Lo.X + Hi.X - Tw) * 0.5f, (Lo.Y + Hi.Y - Th) * 0.5f);
				Box(P - FVector2D(4.f * Sc, 1.f * Sc), P + FVector2D(Tw + 4.f * Sc, Th + 1.f * Sc), FLinearColor(0.04f, 0.035f, 0.03f, 0.62f));
				UI.Text(N, FLinearColor(1.f, 0.94f, 0.78f), P.X, P.Y, Small, Sc * 0.95f);
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
		// (level 5: the gallery's name; cursed, slowed or burning: a mark after it)
		const FString Nm = Mo->Title.IsEmpty() ? Mo->MonsterName.ToString().Replace(TEXT("_"), TEXT(" ")) : Mo->Title;
		FString Marks;
		if (Mo->GetCurseShare() > 0.f) Marks += TEXT("  CURSED");
		if (Mo->GetSlowShare() > 0.f) Marks += TEXT("  SLOWED");
		if (Mo->IsBurning()) Marks += TEXT("  BURNING");
		const FString N = FString::Printf(TEXT("%s  %.0f%s"), *Nm.ToUpper(), Mo->GetHealth(), *Marks);
		float Tw, Th; UI.TextSize(N, Tw, Th, Small, Sc, ERDType::Label);
		UI.Text(N, RDInk, S.X - Tw * 0.5f, A.Y - Th - 3.f * Sc, Small, Sc, ERDType::Label);
	}
	// ---- level 5: her allies (green bars, the time they have left)
	for (const ARDMonster* Mo : Gen->GetAllies())
	{
		if (FVector::Dist2D(Mo->GetActorLocation(), L) > 2400.f) continue;
		const FVector S = Project(Mo->GetActorLocation() + FVector(0, 0, Mo->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 34.f), false);
		if (S.Z <= 0.f || S.X < 0.f || S.Y < 0.f || S.X > Canvas->ClipX || S.Y > Canvas->ClipY) continue;
		const float W = 96.f * Sc, H = 8.f * Sc, F = Mo->GetHealth() / FMath::Max(Mo->GetMaxHealth(), 1.f);
		const FVector2D A(S.X - W * 0.5f, S.Y - H);
		Box(A - FVector2D(2.f), A + FVector2D(W + 2.f, H + 2.f), FLinearColor(0.02f, 0.02f, 0.02f, 0.8f));
		Box(A, A + FVector2D(W * F, H), FLinearColor(0.25f, 0.85f, 0.35f));
		const FString Nm = Mo->Title.IsEmpty() ? Mo->MonsterName.ToString().Replace(TEXT("_"), TEXT(" ")) : Mo->Title;
		const FString N = Mo->GetAllyTimeLeft() > 0.f ? FString::Printf(TEXT("ALLY  %s  %.0fs"), *Nm.ToUpper(), FMath::CeilToFloat(Mo->GetAllyTimeLeft())) : FString::Printf(TEXT("ALLY  %s"), *Nm.ToUpper());
		float Tw, Th; UI.TextSize(N, Tw, Th, Small, Sc, ERDType::Label);
		UI.Text(N, FLinearColor(0.6f, 1.f, 0.65f), S.X - Tw * 0.5f, A.Y - Th - 3.f * Sc, Small, Sc, ERDType::Label);
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
		float Tw, Th; UI.TextSize(N, Tw, Th, Medium, K, ERDType::Title);
		const float Al = FMath::Clamp(1.6f - Age * 1.5f, 0.f, 1.f);
		UI.Text(N, FLinearColor(0.f, 0.f, 0.f, Al * 0.8f), S.X - Tw * 0.5f + 2.f, S.Y - Th + 2.f, Medium, K, ERDType::Title);
		UI.Text(N, T.bOnPlayer ? FLinearColor(1.f, 0.25f, 0.2f, Al) : FLinearColor(1.f, 0.9f, 0.35f, Al), S.X - Tw * 0.5f, S.Y - Th, Medium, K, ERDType::Title);
	}
	// ---- status panel (bottom right): hit points (and mana), the weapons with their damage, kills
	{
		const bool bMana = Cb->GetMaxMana() > 0.f;
		// (level 4's painted bars are framed: taller rows; its board reaches beyond the panel, so the panel sits further in)
		const bool bArtBars = UI.Has(TEXT("bar_health"));
		const float Bh = 44.f * Sc;                       // (a painted bar's height)
		const float Mb = bMana ? (bArtBars ? Bh + 2.f * Sc : 30.f * Sc) : 0.f;   // (the mana bar's room)
		const float Hx = bArtBars ? Bh - 30.f * Sc : 0.f;    // (the hit points bar's extra room)
		const float Ext = UI.Has(TEXT("panel_wide")) ? 28.f * Sc : 0.f;
		const float W = 400.f * Sc, H = 176.f * Sc + Mb + Hx, Mg = 24.f * Sc + Ext, Pd = 14.f * Sc;
		const FVector2D A(Canvas->ClipX - Mg - W, Canvas->ClipY - Mg - H), B = A + FVector2D(W, H);
		// what is on her (potions, food): a chip each over the panel, with the seconds left
		{
			float X = B.X;
			const TArray<URDCombatComponent::FEffect>& Ef = Cb->GetEffects();
			for (int32 I = Ef.Num() - 1; I >= 0; --I)
			{
				const URDCombatComponent::FEffect& E = Ef[I];
				const bool bSpeed = E.Kind == ERDItemKind::Speed;
				const FString T = bSpeed ? FString::Printf(TEXT("SPEED +%.0f%%  %.0fs"), E.Amount * 100.f, FMath::CeilToFloat(E.Left))
				                         : FString::Printf(TEXT("REGEN +%.1f/s  %.0fs"), E.Amount * Cb->GetMaxHealth(), FMath::CeilToFloat(E.Left));
				const FName Ic = bSpeed ? FName(TEXT("chip_speed")) : FName(TEXT("chip_regen"));
				float Tw, Th; UI.TextSize(T, Tw, Th, Small, Sc, ERDType::Label);
				const float Iw = UI.Has(Ic) ? Th + 14.f * Sc : 0.f;           // (its picture before the text)
				const float Up = Ext * 1.6f;
				const FVector2D C1(X, A.Y - 8.f * Sc - Up), C0(X - Tw - 16.f * Sc - Iw, A.Y - 8.f * Sc - Th - 8.f * Sc - Up);
				Box(C0, C1, bSpeed ? FLinearColor(0.10f, 0.22f, 0.30f, 0.85f) : FLinearColor(0.12f, 0.26f, 0.12f, 0.85f));
				Frame(C0, C1, bSpeed ? RDCyan : FLinearColor(0.45f, 0.9f, 0.45f), 1.f * Sc);
				if (Iw > 0.f) UI.Fit(Ic, C0 + FVector2D(4.f * Sc, -6.f * Sc), FVector2D(C0.X + Iw, C1.Y + 6.f * Sc));
				UI.Text(T, FLinearColor::White, C0.X + 8.f * Sc + Iw, C0.Y + 4.f * Sc, Small, Sc, ERDType::Label);
				X = C0.X - 8.f * Sc;
			}
			// (level 5: her spells on her, and what the monsters did to her: a chip each, a row above the potions')
			const TArray<FString> Buffs = Cb->GetBuffLines();
			float Bx = B.X;
			const float Up = Ext * 1.6f + (Ef.Num() > 0 ? 40.f * Sc : 0.f);
			for (const FString& Bl : Buffs)
			{
				TArray<FString> Q; Bl.ParseIntoArray(Q, TEXT("|"));
				if (Q.Num() < 3) continue;
				const bool bGood = Q[2] == TEXT("1");
				const FString T = FString::Printf(TEXT("%s  %.0fs"), *Q[0], FMath::CeilToFloat(FCString::Atof(*Q[1])));
				float Tw, Th; UI.TextSize(T, Tw, Th, Small, Sc, ERDType::Label);
				const FVector2D C1(Bx, A.Y - 8.f * Sc - Up), C0(Bx - Tw - 16.f * Sc, A.Y - 8.f * Sc - Th - 8.f * Sc - Up);
				Box(C0, C1, bGood ? FLinearColor(0.16f, 0.12f, 0.30f, 0.85f) : FLinearColor(0.32f, 0.08f, 0.08f, 0.85f));
				Frame(C0, C1, bGood ? FLinearColor(0.75f, 0.6f, 1.f) : FLinearColor(1.f, 0.4f, 0.3f), 1.f * Sc);
				UI.Text(T, FLinearColor::White, C0.X + 8.f * Sc, C0.Y + 4.f * Sc, Small, Sc, ERDType::Label);
				Bx = C0.X - 8.f * Sc;
			}
		}
		if (!Board(TEXT("panel_wide"), A, B, Sc, Ext))
		{
			Box(A, B, FLinearColor(0.04f, 0.05f, 0.07f, 0.78f));
			Frame(A, B, FLinearColor(0.75f, 0.65f, 0.45f, 0.9f), 2.f * Sc);
		}
		const float In = Ext > 0.f ? 18.f * Sc : 0.f;      // (clear of the board's corner ornaments)
		UI.Text(Gen->PlayerTitle, RDInk, A.X + Pd + In, A.Y + 9.f * Sc, Small, Sc * 1.1f, ERDType::Title);
		const FString Kl = FString::Printf(TEXT("KILLS  %d"), Cb->Kills);
		float Tw, Th; UI.TextSize(Kl, Tw, Th, Small, Sc * 1.1f, ERDType::Label);
		UI.Text(Kl, RDInk, B.X - Pd - In - Tw, A.Y + 9.f * Sc, Small, Sc * 1.1f, ERDType::Label);
		// (a painted bar: its frame Bh tall, its fill inside; the text goes in its open part)
		auto ArtBar = [&](FName Fr0, FName Fill, float Y0, float F, const FLinearColor& FillTint, const FLinearColor& FrameTint, FVector2D& I0, FVector2D& I1)
		{
			const FRDUIArt* Ar = UI.Find(Fr0);
			const FVector2D F0(A.X + Pd - 6.f * Sc, Y0), F1(B.X - Pd + 6.f * Sc, Y0 + Bh);
			const float Px = Bh / FMath::Max((float)Ar->Texture->GetSizeY(), 1.f);
			UI.Bar(Fr0, Fill, F0, F1, Px, F, FillTint, FrameTint);
			UI.InnerBox(Fr0, F0, F1, Px, I0, I1);
		};
		// hit points
		const float Fr = Cb->GetHealth() / FMath::Max(Cb->GetMaxHealth(), 1.f);
		FVector2D H0(A.X + Pd, A.Y + 36.f * Sc), H1(B.X - Pd, A.Y + 64.f * Sc);
		if (bArtBars)
		{
			// (low: the fill pulses)
			const float Lo = Fr < 0.25f ? 0.75f + 0.25f * FMath::Sin(Now * 8.f) : 1.f;
			ArtBar(TEXT("bar_health"), TEXT("fill_health"), A.Y + 30.f * Sc, Fr, FLinearColor(Lo, Lo, Lo), FLinearColor::White, H0, H1);
		}
		else
		{
			Box(H0, H1, FLinearColor(0.10f, 0.03f, 0.03f, 0.95f));
			const FLinearColor Hc = Fr > 0.5f ? FLinearColor(0.20f, 0.72f, 0.26f) : Fr > 0.25f ? FLinearColor(0.90f, 0.62f, 0.12f) : FLinearColor(0.88f, 0.16f, 0.12f);
			Box(H0 + FVector2D(2.f), FVector2D(H0.X + 2.f + (H1.X - H0.X - 4.f) * Fr, H1.Y - 2.f), Hc);
			Frame(H0, H1, FLinearColor(0.75f, 0.65f, 0.45f, 0.9f), 1.5f * Sc);
		}
		const FString Hp = FString::Printf(TEXT("HP  %.0f / %.0f"), FMath::CeilToFloat(Cb->GetHealth()), Cb->GetMaxHealth());
		UI.TextSize(Hp, Tw, Th, Small, Sc * 1.2f, ERDType::Label);
		if (bArtBars) UI.Text(Hp, FLinearColor(0.f, 0.f, 0.f, 0.8f), (H0.X + H1.X - Tw) * 0.5f + 1.5f * Sc, (H0.Y + H1.Y - Th) * 0.5f + 1.5f * Sc, Small, Sc * 1.2f, ERDType::Label);
		UI.Text(Hp, FLinearColor::White, (H0.X + H1.X - Tw) * 0.5f, (H0.Y + H1.Y - Th) * 0.5f, Small, Sc * 1.2f, ERDType::Label);
		// mana (blue; it flashes when a cast was refused for want of it)
		if (bMana)
		{
			const float Mf = Cb->GetMana() / FMath::Max(Cb->GetMaxMana(), 1.f);
			FVector2D M0(A.X + Pd, A.Y + 70.f * Sc), M1(B.X - Pd, A.Y + 92.f * Sc);
			const float Flash = FMath::Clamp(1.f - (Now - Cb->NoManaTime) / 0.6f, 0.f, 1.f);
			if (bArtBars && UI.Has(TEXT("bar_mana")))
				ArtBar(TEXT("bar_mana"), TEXT("fill_mana"), A.Y + 30.f * Sc + Bh + 2.f * Sc, Mf, FLinearColor::White,
				       FLinearColor(1.f, 1.f - 0.7f * Flash, 1.f - 0.75f * Flash), M0, M1);
			else
			{
				Box(M0, M1, FLinearColor(0.03f + 0.3f * Flash, 0.04f, 0.12f, 0.95f));
				Box(M0 + FVector2D(2.f), FVector2D(M0.X + 2.f + (M1.X - M0.X - 4.f) * Mf, M1.Y - 2.f), FLinearColor(0.18f, 0.40f, 0.95f));
				Frame(M0, M1, Flash > 0.f ? FLinearColor(1.f, 0.3f, 0.25f) : FLinearColor(0.75f, 0.65f, 0.45f, 0.9f), 1.5f * Sc);
			}
			if (bArtBars && Flash > 0.f) Frame(M0, M1, FLinearColor(1.f, 0.3f, 0.25f, Flash), 2.f * Sc);
			const FString Mt = FString::Printf(TEXT("MANA  %.0f / %.0f"), FMath::FloorToFloat(Cb->GetMana()), Cb->GetMaxMana());
			UI.TextSize(Mt, Tw, Th, Small, Sc * 1.05f, ERDType::Label);
			if (bArtBars) UI.Text(Mt, FLinearColor(0.f, 0.f, 0.f, 0.8f), (M0.X + M1.X - Tw) * 0.5f + 1.5f * Sc, (M0.Y + M1.Y - Th) * 0.5f + 1.5f * Sc, Small, Sc * 1.05f, ERDType::Label);
			UI.Text(Mt, FLinearColor::White, (M0.X + M1.X - Tw) * 0.5f, (M0.Y + M1.Y - Th) * 0.5f, Small, Sc * 1.05f, ERDType::Label);
		}
		// the weapons (level 5: with the ones she found there may be many: four slots at most, round the one in her hands)
		const int32 Total = Gen->Weapons.Num(), MaxSlots = 3;
		const int32 Num = FMath::Min(Total, MaxSlots);
		const int32 First = Total > MaxSlots ? FMath::Clamp(Cb->GetWeaponIndex() - 1, 0, Total - MaxSlots) : 0;
		const float Gp = 8.f * Sc, Sw = Num > 0 ? (W - Pd * 2.f - Gp * (Num - 1)) / Num : 0.f;
		if (Total > MaxSlots)
		{
			const FString Mo = FString::Printf(TEXT("%d of %d weapons  ·  %d before, %d after  (wheel)"), Num, Total, First, Total - First - Num);
			UI.TextSize(Mo, Tw, Th, Small, Sc * 0.9f);
			UI.Text(Mo, FLinearColor(0.72f, 0.70f, 0.66f), B.X - Pd - Tw, A.Y + 76.f * Sc + Mb + Hx + 68.f * Sc, Small, Sc * 0.9f);
		}
		for (int32 J = 0; J < Num; ++J)
		{
			const int32 I = First + J;
			const FRDWeaponDef& Wp = Gen->Weapons[I];
			const bool bOn = Wp.bAlongside ? Cb->GetAttackIndex() == I : I == Cb->GetWeaponIndex();
			const FVector2D S0(A.X + Pd + J * (Sw + Gp), A.Y + 76.f * Sc + Mb + Hx), S1 = S0 + FVector2D(Sw, 66.f * Sc);
			// (a found weapon: what is left of its durability)
			const FString Dur = Wp.Durability > 0.f ? FString::Printf(TEXT("%.0f / %.0f"), Cb->GetWeaponWear(I), Wp.Durability) : FString();
			// (painted: the slot's stone and iron, lit when it is the one in use, the weapon's picture on its left)
			const FName Ic = WeaponIcon(I);
			// (the picture only where the name and damage still have room beside it: not in three slots)
			const bool bSlot = UI.Has(TEXT("slot")), bIcon = UI.Has(Ic) && Sw - ((66.f - 8.f) * Sc) - 16.f * Sc >= 80.f * Sc;
			if (bSlot)
			{
				const FRDUIArt* Sa = UI.Find(TEXT("slot"));
				UI.Nine(TEXT("slot"), S0, S1, 18.f * Sc / FMath::Max((float)Sa->Border.X * Sa->Texture->GetSizeX(), 1.f),
				        bOn ? FLinearColor(1.15f, 1.05f, 0.85f) : FLinearColor(0.62f, 0.62f, 0.62f));
				if (bOn) Frame(S0 + FVector2D(1.f), S1 - FVector2D(1.f), FLinearColor(1.f, 0.82f, 0.35f, 0.85f), 2.f * Sc);
			}
			else
			{
				Box(S0, S1, bOn ? FLinearColor(0.36f, 0.27f, 0.10f, 0.95f) : FLinearColor(0.10f, 0.10f, 0.12f, 0.9f));
				Frame(S0, S1, bOn ? FLinearColor(1.f, 0.82f, 0.35f) : FLinearColor(0.40f, 0.38f, 0.34f), (bOn ? 2.5f : 1.f) * Sc);
			}
			const float Iw = bIcon ? (S1.Y - S0.Y) - 8.f * Sc : 0.f;        // (the picture's square)
			if (bIcon) UI.Fit(Ic, S0 + FVector2D(10.f * Sc, 8.f * Sc), FVector2D(S0.X + 6.f * Sc + Iw, S1.Y - 8.f * Sc), bOn ? FLinearColor::White : FLinearColor(0.7f, 0.7f, 0.7f));
			const FLinearColor Tc = bOn ? FLinearColor::White : FLinearColor(0.72f, 0.70f, 0.66f);
			// (its key: the one that draws it, or casts it when it is cast alongside; on the gamepad the button it is used with)
			FString Key = Wp.bAlongside ? FString(TEXT("RMB / E")) : I < 3 ? FString::Printf(TEXT("%d"), I + 1) : FString(TEXT("wheel"));
			if (bPad) Key = Wp.bAlongside ? FString(TEXT("LB")) : (Wp.bSpell && Cb->GetAlongsideSpell() < 0) ? FString(TEXT("LB / RB")) : FString(TEXT("RB"));
			if (bPad && Gen->bRogueControls) Key = bOn ? FString(TEXT("RB")) : FString(TEXT("Y"));      // (the rogue: Y draws it, RB uses it)
			UI.Text(Key, bOn ? FLinearColor(1.f, 0.82f, 0.35f) : Tc, S0.X + 7.f * Sc, S0.Y + 4.f * Sc, Small, Sc, ERDType::Title);
			const FString N = Wp.Name.ToString().ToUpper();
			if (bIcon)
			{
				// (beside the picture: the name, the damage, the mana a cast takes, a line each)
				const float Cx0 = S0.X + Iw + 10.f * Sc, Cx1 = S1.X - 6.f * Sc;
				UI.TextSize(N, Tw, Th, Small, Sc * 1.05f, ERDType::Label);
				UI.Text(N, Tc, (Cx0 + Cx1 - Tw) * 0.5f, S0.Y + 9.f * Sc, Small, Sc * 1.05f, ERDType::Label);
				const FString D = FString::Printf(TEXT("%.0f damage"), Cb->GetDamageOf(I));
				UI.TextSize(D, Tw, Th, Small, Sc * 0.95f);
				UI.Text(D, bOn ? FLinearColor(1.f, 0.9f, 0.6f) : Tc, (Cx0 + Cx1 - Tw) * 0.5f, S0.Y + 29.f * Sc, Small, Sc * 0.95f);
				if (Wp.ManaCost > 0.f)
				{
					const FString Mc = FString::Printf(TEXT("%.0f mana"), Wp.ManaCost);
					UI.TextSize(Mc, Tw, Th, Small, Sc * 0.95f);
					UI.Text(Mc, FLinearColor(0.55f, 0.7f, 1.f), (Cx0 + Cx1 - Tw) * 0.5f, S0.Y + 45.f * Sc, Small, Sc * 0.95f);
				}
				else if (!Dur.IsEmpty())
				{
					UI.TextSize(Dur, Tw, Th, Small, Sc * 0.95f);
					UI.Text(Dur, Cb->GetWeaponWear(I) < Wp.Durability * 0.2f ? FLinearColor(1.f, 0.45f, 0.3f) : FLinearColor(0.75f, 0.85f, 0.7f), (Cx0 + Cx1 - Tw) * 0.5f, S0.Y + 45.f * Sc, Small, Sc * 0.95f);
				}
				continue;
			}
			// (a name too wide for its slot goes on two lines, split at the space nearest its middle, and is written smaller
			// if a line is still too wide: three slots of a found weapon's long name)
			const float Room = Sw - 10.f * Sc;
			float Kn = Sc * 1.15f;
			UI.TextSize(N, Tw, Th, Small, Kn, ERDType::Label);
			TArray<FString> NL = { N };
			if (Tw > Room)
			{
				int32 Cut = INDEX_NONE;
				for (int32 C = 0; C < N.Len(); ++C) if (N[C] == TEXT(' ') && (Cut == INDEX_NONE || FMath::Abs(C - N.Len() / 2) < FMath::Abs(Cut - N.Len() / 2))) Cut = C;
				if (Cut != INDEX_NONE) NL = { N.Left(Cut), N.Mid(Cut + 1) };
			}
			float Wmax = 0.f;
			for (const FString& Ln : NL) { UI.TextSize(Ln, Tw, Th, Small, Kn, ERDType::Label); Wmax = FMath::Max(Wmax, Tw); }
			if (Wmax > Room) Kn *= FMath::Max(0.55f, Room / Wmax);
			for (int32 Li = 0; Li < NL.Num(); ++Li)
			{
				UI.TextSize(NL[Li], Tw, Th, Small, Kn, ERDType::Label);
				UI.Text(NL[Li], Tc, (S0.X + S1.X - Tw) * 0.5f, S0.Y + (NL.Num() > 1 ? 13.f + 14.f * Li : 16.f) * Sc, Small, Kn, ERDType::Label);
			}
			FString D = Wp.ManaCost > 0.f ? FString::Printf(TEXT("%.0f damage  ·  %.0f mana"), Cb->GetDamageOf(I), Wp.ManaCost) : FString::Printf(TEXT("%.0f damage"), Cb->GetDamageOf(I));
			if (!Dur.IsEmpty()) D = Total > 3 ? FString::Printf(TEXT("%.0f  ·  %s"), Cb->GetDamageOf(I), *Dur) : D + TEXT("  ·  ") + Dur;
			float Kd = Sc;
			UI.TextSize(D, Tw, Th, Small, Kd);
			if (Tw > Sw - 8.f * Sc) { Kd *= FMath::Max(0.6f, (Sw - 8.f * Sc) / Tw); UI.TextSize(D, Tw, Th, Small, Kd); }
			UI.Text(D, bOn ? FLinearColor(1.f, 0.9f, 0.6f) : Tc, (S0.X + S1.X - Tw) * 0.5f, S0.Y + (NL.Num() > 1 ? 44.f : 40.f) * Sc, Small, Kd);
		}
		if (!Gen->ControlsHint.IsEmpty()) UI.Text(Gen->ControlsHint, FLinearColor(0.7f, 0.68f, 0.62f), A.X + Pd, B.Y - 26.f * Sc, Small, Sc);
	}
	// ---- the controls (upper left, the magic levels): those of the device in use, and whether she walks or runs
	const TArray<FString>& Lines = bPad ? Gen->ControlsPad : Gen->ControlsKeys;
	if (Gen->bCasterControls && Lines.Num() > 0)
	{
		const float Ext = UI.Has(TEXT("panel_wide")) ? 20.f * Sc : 0.f;
		const float In = Ext > 0.f ? 16.f * Sc : 0.f, Dn = Ext > 0.f ? 6.f * Sc : 0.f;      // (level 4: clear of the board's frame and corner ornaments)
		const float Mg = 24.f * Sc + Ext, Pd = 14.f * Sc, Lh = 23.f * Sc, K = Sc * 1.05f;
		TArray<FString> Keys, Whats;
		float Kw = 0.f, Ww = 0.f, Tw, Th;
		for (const FString& S : Lines)
		{
			FString Kt, Wt;
			if (!S.Split(TEXT("|"), &Kt, &Wt)) { Kt = S; Wt = FString(); }
			Keys.Add(Kt); Whats.Add(Wt);
			UI.TextSize(Kt, Tw, Th, Small, K, ERDType::Label); Kw = FMath::Max(Kw, Tw);
			UI.TextSize(Wt, Tw, Th, Small, K); Ww = FMath::Max(Ww, Tw);
		}
		const FString Title = bPad ? TEXT("CONTROLS  -  GAMEPAD") : TEXT("CONTROLS  -  KEYBOARD & MOUSE");
		const FString Mode = Cb->IsRunMode() ? TEXT("RUNNING") : TEXT("WALKING");
		float Tiw, Mw;
		UI.TextSize(Title, Tiw, Th, Small, Sc * 1.1f, ERDType::Title); UI.TextSize(Mode, Mw, Th, Small, Sc * 1.1f, ERDType::Label);
		const float W = FMath::Max(Kw + 18.f * Sc + Ww, Tiw + 24.f * Sc + Mw) + Pd * 2.f + In * 2.f;
		const FVector2D A(Mg, Mg), B(Mg + W, Mg + 40.f * Sc + Lh * Lines.Num() + 8.f * Sc + Dn * 2.f);
		if (!Board(TEXT("panel_wide"), A, B, Sc, Ext))
		{
			Box(A, B, FLinearColor(0.04f, 0.05f, 0.07f, 0.72f));
			Frame(A, B, FLinearColor(0.75f, 0.65f, 0.45f, 0.9f), 2.f * Sc);
		}
		UI.Text(Title, RDInk, A.X + Pd + In, A.Y + 9.f * Sc + Dn, Small, Sc * 1.1f, ERDType::Title);
		UI.Text(Mode, Cb->IsRunMode() ? FLinearColor(1.f, 0.62f, 0.25f) : RDCyan, B.X - Pd - In - Mw, A.Y + 9.f * Sc + Dn, Small, Sc * 1.1f, ERDType::Label);
		for (int32 I = 0; I < Keys.Num(); ++I)
		{
			const float Y = A.Y + 40.f * Sc + Dn * 1.5f + Lh * I;
			UI.Text(Keys[I], FLinearColor(1.f, 0.82f, 0.35f), A.X + Pd + In, Y, Small, K, ERDType::Label);
			UI.Text(Whats[I], FLinearColor(0.86f, 0.84f, 0.78f), A.X + Pd + In + Kw + 18.f * Sc, Y, Small, K);
		}
	}
	// ---- she is down
	if (Cb->IsDead())
	{
		Box(FVector2D(0, 0), FVector2D(Canvas->ClipX, Canvas->ClipY), FLinearColor(0.10f, 0.f, 0.f, FMath::Clamp((Now - Cb->DeathTime) / 1.2f, 0.f, 0.55f)));
		const FString T = TEXT("YOU HAVE FALLEN");
		float Tw, Th; UI.TextSize(T, Tw, Th, Medium, Sc * 2.6f, ERDType::Title);
		UI.Text(T, FLinearColor(0.95f, 0.2f, 0.15f), (Canvas->ClipX - Tw) * 0.5f, Canvas->ClipY * 0.4f, Medium, Sc * 2.6f, ERDType::Title);
		const FString U = TEXT("back to the middle of the dungeon...");
		UI.TextSize(U, Tw, Th, Small, Sc * 1.3f);
		UI.Text(U, RDInk, (Canvas->ClipX - Tw) * 0.5f, Canvas->ClipY * 0.4f + 62.f * Sc, Small, Sc * 1.3f);
	}
}

void ARDHUD::DrawHUD()
{
	Super::DrawHUD();
	if (!Canvas) return;
	if (!Gen) for (TActorIterator<ARDDungeonGenerator> It(GetWorld()); It; ++It) { Gen = *It; break; }
	if (!Gen) return;
	// (play began without a hero: the menu is being opened, the dungeon is not shown)
	if (Gen->bOpeningMenu) { Box(FVector2D(0, 0), FVector2D(Canvas->ClipX, Canvas->ClipY), FLinearColor::Black); return; }
	ArtDrawn.Reset(); StarsDrawn.Reset(); AnvilsDrawn.Reset(); MiniTierLabels.Reset();
	UI.Hud = this; UI.Art = &Gen->UIArt; UI.Drawn = &ArtDrawn; UI.Fonts = &Gen->UIFonts; UI.FontCache = &FontCache;
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
	if (Gen->bCombat && !bBigMap && Gen->Spells.Num() > 0) DrawHotbar(Sc);
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
		UI.Text(TEXT("DUNGEON"), RDInk, S0.X, S0.Y - 28.f * Sc, Small, Sc * 1.1f);
		const FString Cnt = FString::Printf(TEXT("%d / %d rooms"), Disc, All);
		float Tw, Th; UI.TextSize(Cnt, Tw, Th, Small, Sc * 1.1f);
		UI.Text(Cnt, RDInk, S1.X - Tw, S0.Y - 28.f * Sc, Small, Sc * 1.1f);
		UI.Text(TEXT("N"), RDInk, (S0.X + S1.X) * 0.5f - 4.f * Sc, S0.Y + 2.f * Sc, Small, Sc);
		UI.Text(bPadMap ? TEXT("Back  map") : TEXT("M  map"), FLinearColor(0.7f, 0.68f, 0.62f), S0.X, S1.Y + 6.f * Sc, Small, Sc);
	}

	// ---- new section banner
	if (Now - Gen->LastRevealTime < 3.5f)
	{
		const float A = FMath::Clamp(FMath::Min((Now - Gen->LastRevealTime) / 0.3f, (3.5f - (Now - Gen->LastRevealTime)) / 0.8f), 0.f, 1.f);
		const FString T = UI.HasFonts() ? FString(TEXT("NEW DUNGEON SECTION GENERATED")) : FString(TEXT("▲ NEW DUNGEON SECTION GENERATED"));
		float Tw, Th; UI.TextSize(T, Tw, Th, Medium, Sc * 1.4f, ERDType::Title);
		UI.Text(T, FLinearColor(RDCyan.R, RDCyan.G, RDCyan.B, A), (Canvas->ClipX - Tw) * 0.5f, 90.f * Sc, Medium, Sc * 1.4f, ERDType::Title);
	}

	// ---- level 5: a set cleared, a tier opened
	if (!Gen->TierNotice.IsEmpty() && Now - Gen->TierNoticeTime < 4.5f && Now >= Gen->TierNoticeTime)
	{
		const float Ag = Now - Gen->TierNoticeTime;
		const float A = FMath::Clamp(FMath::Min(Ag / 0.3f, (4.5f - Ag) / 0.8f), 0.f, 1.f);
		float Tw, Th; UI.TextSize(Gen->TierNotice, Tw, Th, Medium, Sc * 1.5f, ERDType::Title);
		UI.Text(Gen->TierNotice, FLinearColor(0.f, 0.f, 0.f, 0.8f * A), (Canvas->ClipX - Tw) * 0.5f + 2.f * Sc, 140.f * Sc + 2.f * Sc, Medium, Sc * 1.5f, ERDType::Title);
		UI.Text(Gen->TierNotice, FLinearColor(1.f, 0.82f, 0.35f, A), (Canvas->ClipX - Tw) * 0.5f, 140.f * Sc, Medium, Sc * 1.5f, ERDType::Title);
	}

	// ---- interaction prompt (level 5: or what a sealed passage says)
	const FString What = Gen->DescribeNearest(L);
	const FString SealSays = What.IsEmpty() && !bBigMap ? Gen->DescribeSealNear(L) : FString();
	if (!SealSays.IsEmpty())
	{
		float Tw, Th; UI.TextSize(SealSays, Tw, Th, Medium, Sc * 1.05f);
		const float X = (Canvas->ClipX - Tw) * 0.5f, Y = Canvas->ClipY * 0.72f;
		Box(FVector2D(X - 14.f * Sc, Y - 8.f * Sc), FVector2D(X + Tw + 14.f * Sc, Y + Th + 8.f * Sc), FLinearColor(0.10f, 0.02f, 0.02f, 0.7f));
		UI.Text(SealSays, FLinearColor(1.f, 0.75f, 0.65f), X, Y, Medium, Sc * 1.05f);
	}
	if (!What.IsEmpty() && !bBigMap)
	{
		const URDCombatComponent* Cb = Gen->GetPlayerCombat();
		const FString T = FString::Printf(TEXT("[%s]  %s"), (Gen->bCasterControls && Cb && Cb->IsUsingGamepad()) ? TEXT("X") : TEXT("F"), *What);
		float Tw, Th; UI.TextSize(T, Tw, Th, Medium, Sc * 1.2f);
		const float X = (Canvas->ClipX - Tw) * 0.5f, Y = Canvas->ClipY * 0.72f;
		Box(FVector2D(X - 14.f * Sc, Y - 8.f * Sc), FVector2D(X + Tw + 14.f * Sc, Y + Th + 8.f * Sc), FLinearColor(0.03f, 0.03f, 0.04f, 0.6f));
		UI.Text(T, FLinearColor(0.95f, 0.9f, 0.78f), X, Y, Medium, Sc * 1.2f);
	}

	// ---- random_dungeonmagic_level4: what she found, what the inventory did, the inventory itself
	if (Gen->Heroes.Num() > 0 && Gen->GetPlayerCombat())
	{
		if (!bBigMap) DrawNotices(Sc);
		if (Gen->GetPlayerCombat()->IsInventoryOpen()) DrawInventory(Sc);
		if (Gen->GetPlayerCombat()->IsCraftingOpen()) DrawCrafting(Sc);
	}
	// ---- level 5: the Escape menu, over everything
	if (Gen->IsMenuOpen()) DrawMenu(Sc);
	else { Gen->MenuRowBoxes.Reset(); Gen->MenuTrackBoxes.Reset(); }

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
					float Tw, Th; UI.TextSize(N, Tw, Th, Small, Sc * 0.9f);
					if (Tw >= Hi.X - Lo.X - 4.f) { N = KindCode(R.Kind); UI.TextSize(N, Tw, Th, Small, Sc * 0.85f); }
					if (Tw < Hi.X - Lo.X - 2.f && Th < Hi.Y - Lo.Y) UI.Text(N, FLinearColor(0.22f, 0.15f, 0.08f), (Lo.X + Hi.X - Tw) * 0.5f, (Lo.Y + Hi.Y - Th) * 0.5f, Small, Sc * 0.85f);
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
		UI.Text(TEXT("DUNGEON MAP"), RDInk, 80.f * Sc, 40.f * Sc, Medium, Sc * 1.6f);
		const FString Sub = FString::Printf(TEXT("%d rooms discovered of %d generated  ·  %d sections  ·  %s  close"), Disc, All, Gen->MapData.Num(), bPadMap ? TEXT("Back") : TEXT("M"));
		UI.Text(Sub, FLinearColor(0.75f, 0.72f, 0.65f), 82.f * Sc, 78.f * Sc, Small, Sc * 1.1f);
		// legend: room codes
		float Y = Canvas->ClipY - 64.f * Sc, X = 82.f * Sc;
		for (int32 Kd = (int32)ERDRoomKind::Hall; Kd < (int32)ERDRoomKind::Junction; ++Kd)
		{
			const FString E = FString::Printf(TEXT("%s %s"), *KindCode((ERDRoomKind)Kd), *ARDDungeonGenerator::KindName((ERDRoomKind)Kd));
			float Tw, Th; UI.TextSize(E, Tw, Th, Small, Sc);
			if (X + Tw > Canvas->ClipX - 80.f * Sc) { X = 82.f * Sc; Y += 22.f * Sc; }
			if (bStyle) Box(FVector2D(X - 16.f * Sc, Y + 3.f * Sc), FVector2D(X - 4.f * Sc, Y + 15.f * Sc), RDFloor((ERDRoomKind)Kd, false));
			UI.Text(E, FLinearColor(0.75f, 0.72f, 0.65f), X, Y, Small, Sc);
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

void ARDHUD::SealMark(const FVector2D& P, float R)
{
	// a sealed passage: a red cross on a dark spot
	SoftDot(P, R * 1.7f, FLinearColor(0.f, 0.f, 0.f, 0.55f));
	const FLinearColor C(1.f, 0.22f, 0.16f, 1.f);
	DrawLine(P.X - R, P.Y - R, P.X + R, P.Y + R, C, FMath::Max(R * 0.38f, 1.5f));
	DrawLine(P.X - R, P.Y + R, P.X + R, P.Y - R, C, FMath::Max(R * 0.38f, 1.5f));
}

void ARDHUD::AnvilMark(const FVector2D& P, float R)
{
	// a small anvil: the painted one (map_anvil) on a dark spot, else drawn (horn to the left, its face, waist and foot)
	SoftDot(P, R * 1.5f, FLinearColor(0.f, 0.f, 0.f, 0.5f));
	// (the painted anvil is dark iron: on the dark map it stands on a bright warm disc, a forge's glow)
	SoftDot(P, R * 1.25f, FLinearColor(1.f, 0.62f, 0.25f, 0.95f));
	if (UI.Fit(TEXT("map_anvil"), P - FVector2D(R * 0.95f), P + FVector2D(R * 0.95f))) return;
	static const FVector2D Shape[] = { { -1.0f, -0.32f }, { -0.45f, -0.52f }, { 0.85f, -0.52f }, { 0.85f, -0.14f }, { 0.35f, -0.08f }, { 0.22f, 0.22f },
	                                   { 0.55f, 0.42f }, { 0.55f, 0.58f }, { -0.55f, 0.58f }, { -0.55f, 0.42f }, { -0.22f, 0.22f }, { -0.32f, -0.08f }, { -0.62f, -0.12f } };
	TArray<FVector2D> V;
	for (const FVector2D& Q : Shape) V.Add(P + Q * R);
	RDFan(this, P + FVector2D(0.f, -0.1f * R), V, FLinearColor(0.80f, 0.82f, 0.88f, 1.f), FLinearColor(0.12f, 0.12f, 0.14f, 1.f));
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
			// (the objectives: chests and trunks not looted yet, open or shut; the barrels, crates and wardrobes that line the
			// storerooms would bury the map in stars)
			const FString Kd = S->GetContainerKind(I);
			if (S->IsContainerLooted(I) || (Kd != TEXT("chest") && Kd != TEXT("trunk"))) continue;
			const FVector P = S->GetContainerLocation(I);
			if (Discovered(P)) Out.Add({ FVector2D(P), 2 });
		}
		// (level 5: the anvils she has seen, where repair items are made)
		if (Gen->Recipes.Num() > 0)
			for (const FVector& A : S->GetAnvilPoints()) if (Discovered(A)) Out.Add({ FVector2D(A), 6 });
		// a hallway end on the section's border that leads where she has not been: the next section is not generated, or
		// nothing of it is discovered (it is generated as she nears it, so "not generated" alone was hardly ever seen)
		const FVector2D Mid = (FVector2D(Gen->SectionMinTile(S->Coord)) + FVector2D(Gen->SectionTiles * 0.5f)) * TS;
		for (const FVector& P : S->GetPortalPoints())
		{
			const FVector2D D = FVector2D(P) - Mid;
			const FIntPoint Next = S->Coord + (FMath::Abs(D.X) > FMath::Abs(D.Y) ? FIntPoint(D.X > 0 ? 1 : -1, 0) : FIntPoint(0, D.Y > 0 ? 1 : -1));
			// (level 5: a passage into a tier not open yet, or past the last one, is sealed)
			if (Gen->GetSealKind(S->Coord, Next) > 0) { if (Discovered(P)) Out.Add({ FVector2D(P), 5 }); continue; }
			const FRDSectionMap* M = Gen->MapData.Find(Next);
			if (!M || !M->Rects.ContainsByPredicate([](const FRDMapRect& R) { return R.bDiscovered; })) Out.Add({ FVector2D(P), 3 });
		}
	}
}

void ARDHUD::DrawTacticalMinimap(float Sc, const FVector& L, float Yaw)
{
	UFont* Small = GEngine->GetSmallFont();
	const float R = MinimapPixels * Sc * 0.5f, Mg = 24.f * Sc;
	// (level 4: a painted ring round it, its open inside the size of the map; the map moves in to make room for it)
	const FRDUIArt* Ra = UI.Find(TEXT("minimap_ring"));
	const float Ring = Ra ? R * 1.03f / FMath::Max((float)(Ra->Inner.Z - Ra->Inner.X), 0.2f) : R;
	const FVector2D C(Canvas->ClipX - Mg - Ring, Mg + (Ra ? 0.f : 14.f * Sc) + Ring);
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
		if (Pi.Kind == 2) { Star(S, 6.5f * Sc, RDTacGold); StarsDrawn.Add(Pi.W); }
		else if (Pi.Kind == 3) Diamond(S, 5.5f * Sc, RDTacExit);
		else if (Pi.Kind == 5) SealMark(S, 5.f * Sc);
		else if (Pi.Kind == 6) { AnvilMark(S, 10.f * Sc); AnvilsDrawn.Add(Pi.W); }
	}
	// (level 5: the tier of each room she has found, small, in its middle)
	if (Gen->MaxTier > 0)
	{
		const FLinearColor TierInk(0.95f, 0.80f, 0.45f, 1.f);
		for (const auto& KV : Gen->MapData)
			for (const FRDMapRect& Rr : KV.Value.Rects)
			{
				if (!Rr.bDiscovered || Rr.bCorridor || Rr.Kind == ERDRoomKind::Junction) continue;
				const FVector2D M = ToS((FVector2D(Rr.Min) + FVector2D(Rr.Max)) * 0.5f * TS);
				const float A = Fade(M);
				if (FVector2D::Distance(M, C) > R * 0.86f || A < 0.3f) continue;
				const FString Tt = FString::Printf(TEXT("T%d"), Gen->TierOf(KV.Key));
				float Tw2, Th2; UI.TextSize(Tt, Tw2, Th2, Small, Sc * 0.95f, ERDType::Label);
				UI.Text(Tt, FLinearColor(0.f, 0.f, 0.f, 0.8f * A), M.X - Tw2 * 0.5f + 1.f * Sc, M.Y - Th2 * 0.5f + 1.f * Sc, Small, Sc * 0.95f, ERDType::Label);
				UI.Text(Tt, FLinearColor(TierInk.R, TierInk.G, TierInk.B, A), M.X - Tw2 * 0.5f, M.Y - Th2 * 0.5f, Small, Sc * 0.95f, ERDType::Label);
				MiniTierLabels.Add(FString::Printf(TEXT("%s|%d"), *ARDDungeonGenerator::KindName(Rr.Kind), Gen->TierOf(KV.Key)));
			}
	}
	for (const FRDPoi& Pi : Pois)
	{
		const FVector2D S = ToS(Pi.W);
		if (FVector2D::Distance(S, C) > R * 0.94f) continue;
		if (Pi.Kind == 0) { SoftDot(S, 9.f * Sc, RDTacA(RDTacRed, 0.35f)); SoftDot(S, 4.6f * Sc, RDTacRed); }
		else if (Pi.Kind == 1) { SoftDot(S, 11.f * Sc, RDTacA(RDTacElite, 0.35f)); Triangle(S, 7.f * Sc, RDTacElite); }
	}
	DrawPlayerArrow(C, Yaw - 90.f, 9.f * Sc);
	if (Ra) UI.Fit(TEXT("minimap_ring"), C - FVector2D(Ring), C + FVector2D(Ring));
	int32 Disc = 0, All = 0; Gen->GetDiscoveryStats(Disc, All);
	const FLinearColor Ink(0.75f, 0.77f, 0.8f, 0.85f);
	float Tw = 0.f, Th = 0.f;
	UI.Text(TEXT("N"), Ink, C.X - 4.f * Sc, C.Y - R * 0.98f, Small, Sc, ERDType::Title);
	const bool bPad = Gen->bCasterControls && Gen->GetPlayerCombat() && Gen->GetPlayerCombat()->IsUsingGamepad();
	const FString Under = FString::Printf(TEXT("%d / %d rooms    %s  map"), Disc, All, bPad ? TEXT("Back") : TEXT("M"));
	UI.TextSize(Under, Tw, Th, Small, Sc);
	UI.Text(Under, Ink, C.X - Tw * 0.5f, C.Y + (Ra ? Ring + 4.f * Sc : R * 0.96f), Small, Sc);
	if (Gen->MaxTier > 0) DrawTiers(Sc, FVector2D(C.X, C.Y + (Ra ? Ring + 4.f * Sc : R * 0.96f) + Th + 8.f * Sc));
}

void ARDHUD::DrawTiers(float Sc, const FVector2D& At)
{
	const APawn* P = GetOwningPawn();
	if (!P) return;
	UFont* Small = GEngine->GetSmallFont();
	const FIntPoint S = Gen->WorldToSection(P->GetActorLocation());
	const int32 T = Gen->TierOf(S), Open = Gen->GetOpenTiers();
	FRDSectionProgress Pr;
	const bool bHave = Gen->GetSectionProgress(S, Pr);
	TArray<TPair<FString, FLinearColor>> Ls;
	Ls.Add({ FString::Printf(TEXT("TIER %d  ·  SETS CLEARED %d / %d"), T, Gen->GetTierCleared(T), Gen->TierSize(T)), FLinearColor(1.f, 0.82f, 0.35f) });
	if (bHave)
		Ls.Add({ Pr.bCleared ? FString(TEXT("this set of rooms is cleared"))
		                     : FString::Printf(TEXT("rooms %d/%d   chests %d/%d   monsters %d/%d"), Pr.RoomsExplored, Pr.Rooms, Pr.ChestsLooted, Pr.Chests.Num(), Pr.Killed.Num(), Pr.Monsters),
		         Pr.bCleared ? FLinearColor(0.45f, 0.95f, 0.5f) : FLinearColor(0.86f, 0.84f, 0.78f) });
	Ls.Add({ Open < Gen->MaxTier ? FString::Printf(TEXT("tier %d opens when all of tier %d is cleared"), Open + 1, Open) : FString::Printf(TEXT("all %d tiers are open"), Gen->MaxTier),
	         FLinearColor(0.7f, 0.72f, 0.75f) });
	float Y = At.Y, Wmax = 0.f, Tw = 0.f, Th = 0.f;
	for (const auto& Lp : Ls) { UI.TextSize(Lp.Key, Tw, Th, Small, Sc, ERDType::Label); Wmax = FMath::Max(Wmax, Tw); }
	Box(FVector2D(At.X - Wmax * 0.5f - 10.f * Sc, Y - 4.f * Sc), FVector2D(At.X + Wmax * 0.5f + 10.f * Sc, Y + (Th + 4.f * Sc) * Ls.Num() + 4.f * Sc), FLinearColor(0.02f, 0.02f, 0.03f, 0.55f));
	for (const auto& Lp : Ls)
	{
		UI.TextSize(Lp.Key, Tw, Th, Small, Sc, ERDType::Label);
		UI.Text(Lp.Key, Lp.Value, At.X - Tw * 0.5f, Y, Small, Sc, ERDType::Label);
		Y += Th + 4.f * Sc;
	}
}

void ARDHUD::DrawPaintedMap(float Sc, const FVector& L, float Yaw)
{
	UFont* Small = GEngine->GetSmallFont(); UFont* Medium = GEngine->GetMediumFont();
	// the map's area in the middle of the view, between the controls (upper left) and her status panel (lower right); the
	// board's frame sits round it
	const FVector2D Cs(Canvas->ClipX * 0.5f, Canvas->ClipY * 0.5f);
	const FVector2D A(Cs.X - 450.f * Sc, 104.f * Sc), B(Cs.X + 450.f * Sc, Canvas->ClipY - 96.f * Sc);
	const FVector2D C = (A + B) * 0.5f, Hf = (B - A) * 0.5f;
	Board(TEXT("panel_wide"), A, B, Sc, 40.f * Sc);
	// the vignette: the minimap's feathered dark disc stretched over the area (the board's leather shows in its corners)
	if (UTexture2D* T = GetSoftDisc()) DrawTexture(T, C.X - Hf.X * 1.12f, C.Y - Hf.Y * 1.12f, Hf.X * 2.24f, Hf.Y * 2.24f, 0.f, 0.f, 1.f, 1.f, FLinearColor(0.004f, 0.005f, 0.007f, 0.9f), BLEND_Translucent);
	const float K = (B.Y - A.Y) / (TacticalMapMeters * 100.f), TS = Gen->TileSize;
	// (its middle: her, or where the arrow keys scrolled it)
	const FVector Vw = L + FVector(Gen->MapPan.X, Gen->MapPan.Y, 0.f);
	MapView = FVector2D(Vw.X, Vw.Y);
	auto ToS = [&](const FVector2D& W) { return C + FVector2D(W.Y - Vw.Y, -(W.X - Vw.X)) * K; };
	// (everything fades out toward the board as the minimap's terrain does toward its rim: by the distance from the middle
	// in shares of the area's half sizes)
	auto Fade = [&](const FVector2D& S) { const FVector2D D = (S - C) / Hf; return FMath::Clamp((1.f - D.Size()) / 0.24f, 0.f, 1.f); };
	auto Inside = [&](const FVector2D& S) { return S.X >= A.X && S.Y >= A.Y && S.X <= B.X && S.Y <= B.Y; };
	CacheTiles();
	const float Now = GetWorld()->GetTimeSeconds();
	TSet<FIntPoint> Fresh;
	for (const auto& KV : Gen->MapData) if (KV.Value.GeneratedTime >= 0.f && Now - KV.Value.GeneratedTime < 4.f) Fresh.Add(KV.Key);
	const float HX = Hf.Y / K + TS, HY = Hf.X / K + TS;          // (world half extents shown: screen up = world X)
	const int32 X0 = FMath::FloorToInt((Vw.X - HX) / TS), X1 = FMath::FloorToInt((Vw.X + HX) / TS);
	const int32 Y0 = FMath::FloorToInt((Vw.Y - HY) / TS), Y1 = FMath::FloorToInt((Vw.Y + HY) / TS);
	// the minimap's terrain: floors dark, hallways darker, what she has not seen darker still; a lit line where a floor
	// she has seen meets no floor
	const FLinearColor Room(0.15f, 0.16f, 0.17f, 0.95f), Hall(0.115f, 0.12f, 0.13f, 0.95f), Unknown(0.055f, 0.058f, 0.064f, 0.7f), Wall(0.36f, 0.385f, 0.41f, 0.9f);
	for (int32 X = X0; X <= X1; ++X)
		for (int32 Y = Y0; Y <= Y1; ++Y)
		{
			const uint8* V = Tiles.Find(FIntPoint(X, Y));
			if (!V) continue;
			const FVector2D S = ToS(FVector2D((X + 0.5f) * TS, (Y + 0.5f) * TS));
			const float Al = Fade(S);
			if (Al <= 0.f) continue;
			FLinearColor Col = (*V & 2) ? ((*V & 4) ? Hall : Room) : Unknown;
			if (Fresh.Num() && Fresh.Contains(Gen->WorldToSection(FVector((X + 0.5f) * TS, (Y + 0.5f) * TS, 0.f)))) Col = FLinearColor(0.16f, 0.32f, 0.36f, Col.A);
			const FVector2D W0(X * TS, Y * TS), W1((X + 1) * TS, (Y + 1) * TS);
			// (on whole pixels, so that neighbouring tiles meet without overlapping: an overlap of see-through tiles draws a grid)
			const FVector2D Qa = ToS(W0), Qb = ToS(W1);
			Box(FVector2D(FMath::RoundToFloat(FMath::Min(Qa.X, Qb.X)), FMath::RoundToFloat(FMath::Min(Qa.Y, Qb.Y))),
			    FVector2D(FMath::RoundToFloat(FMath::Max(Qa.X, Qb.X)), FMath::RoundToFloat(FMath::Max(Qa.Y, Qb.Y))), RDTacA(Col, Al));
			if (!(*V & 2)) continue;
			auto Edge = [&](const FVector2D& A_, const FVector2D& B_) { const FVector2D P = ToS(A_), Q = ToS(B_); DrawLine(P.X, P.Y, Q.X, Q.Y, RDTacA(Wall, Al), 1.6f * Sc); };
			if (!Tiles.Contains(FIntPoint(X + 1, Y))) Edge(FVector2D(W1.X, W0.Y), FVector2D(W1.X, W1.Y));
			if (!Tiles.Contains(FIntPoint(X - 1, Y))) Edge(FVector2D(W0.X, W0.Y), FVector2D(W0.X, W1.Y));
			if (!Tiles.Contains(FIntPoint(X, Y + 1))) Edge(FVector2D(W0.X, W1.Y), FVector2D(W1.X, W1.Y));
			if (!Tiles.Contains(FIntPoint(X, Y - 1))) Edge(FVector2D(W0.X, W0.Y), FVector2D(W1.X, W0.Y));
		}
	// doorways of the rooms she has found: a warm bar across the gap
	for (const auto& KV : Gen->MapData)
		for (const FVector2D& D : KV.Value.Doors)
		{
			const FVector2D Q = ToS(D);
			const float Al = Fade(Q);
			if (Al <= 0.f) continue;
			const uint8* Va = Tiles.Find(FIntPoint(FMath::FloorToInt((D.X + 30.f) / TS), FMath::FloorToInt((D.Y + 30.f) / TS)));
			const uint8* Vb = Tiles.Find(FIntPoint(FMath::FloorToInt((D.X - 30.f) / TS), FMath::FloorToInt((D.Y - 30.f) / TS)));
			if (!((Va && (*Va & 2)) || (Vb && (*Vb & 2)))) continue;
			const bool bOnX = FMath::Abs(D.X / TS - FMath::RoundToFloat(D.X / TS)) < FMath::Abs(D.Y / TS - FMath::RoundToFloat(D.Y / TS));
			const FVector2D Half = bOnX ? FVector2D(0.f, TS * 0.36f) : FVector2D(TS * 0.36f, 0.f);
			const FVector2D P0 = ToS(D - Half), P1 = ToS(D + Half);
			DrawLine(P0.X, P0.Y, P1.X, P1.Y, RDTacA(RDTacDoor, 0.9f * Al), 2.5f * Sc);
		}
	// the names of the rooms she has found, in the labels' small capitals ("GREAT HALL" is written "Great Hall"), in the
	// middle of each room: on two lines when one is too wide, smaller when that is too, left out when nothing fits; faded
	// out toward the board as the tiles are
	RoomLabels.Reset(); MapTierLabels.Reset();
	{
		const FLinearColor RoomInk(0.90f, 0.82f, 0.62f, 1.f), TierInk(1.f, 0.78f, 0.38f, 1.f);
		for (const auto& KV : Gen->MapData)
			for (const FRDMapRect& R : KV.Value.Rects)
			{
				if (!R.bDiscovered || R.bCorridor || R.Kind == ERDRoomKind::Junction) continue;
				const FVector2D Pa = ToS(FVector2D(R.Min) * TS), Pb = ToS(FVector2D(R.Max) * TS);
				const FVector2D Lo(FMath::Min(Pa.X, Pb.X), FMath::Min(Pa.Y, Pb.Y)), Hi(FMath::Max(Pa.X, Pb.X), FMath::Max(Pa.Y, Pb.Y)), Mid = (Lo + Hi) * 0.5f;
				const float Al = Fade(Mid);
				if (!Inside(Mid) || Al < 0.25f) continue;
				const FString Name = ARDDungeonGenerator::KindName(R.Kind);
				FString First = Name.ToUpper(), Second;
				const float RoomW = Hi.X - Lo.X - 10.f * Sc, RoomH = Hi.Y - Lo.Y - 6.f * Sc;
				// (level 5: a line under the name with the room's tier, a little smaller)
				const int32 Tier = Gen->MaxTier > 0 ? Gen->TierOf(KV.Key) : 0;
				const FString TierS = Tier > 0 ? FString::Printf(TEXT("TIER %d"), Tier) : FString();
				float Ks = Sc * 1.3f, W1 = 0.f, H1 = 0.f, W2 = 0.f, H2 = 0.f, W3 = 0.f, H3 = 0.f;
				UI.TextSize(First, W1, H1, Small, Ks, ERDType::Label);
				if (W1 > RoomW) First.Split(TEXT(" "), &First, &Second);
				for (int32 Try = 0; Try < 6; ++Try)
				{
					UI.TextSize(First, W1, H1, Small, Ks, ERDType::Label);
					if (!Second.IsEmpty()) UI.TextSize(Second, W2, H2, Small, Ks, ERDType::Label);
					if (Tier > 0) UI.TextSize(TierS, W3, H3, Small, Ks * 0.8f, ERDType::Label);
					if (FMath::Max3(W1, W2, W3) <= RoomW && H1 + H2 + H3 <= RoomH) break;
					Ks *= 0.88f;
				}
				if (FMath::Max3(W1, W2, W3) > RoomW || H1 + H2 + H3 > RoomH) continue;
				const float Lh = H1 * 0.86f, Ty0 = Mid.Y - ((Second.IsEmpty() ? H1 : Lh + H2) + (Tier > 0 ? H3 * 0.9f : 0.f)) * 0.5f;
				auto Line = [&](const FString& S, float Tw, float Y, float K_, const FLinearColor& Ink_)
				{
					UI.Text(S, FLinearColor(0.f, 0.f, 0.f, 0.85f * Al), Mid.X - Tw * 0.5f + 1.5f * Sc, Y + 1.5f * Sc, Small, K_, ERDType::Label);
					UI.Text(S, FLinearColor(Ink_.R, Ink_.G, Ink_.B, Al), Mid.X - Tw * 0.5f, Y, Small, K_, ERDType::Label);
				};
				Line(First, W1, Ty0, Ks, RoomInk);
				if (!Second.IsEmpty()) Line(Second, W2, Ty0 + Lh, Ks, RoomInk);
				if (Tier > 0)
				{
					Line(TierS, W3, Ty0 + (Second.IsEmpty() ? Lh : Lh + H2 * 0.86f), Ks * 0.8f, TierInk);
					MapTierLabels.Add(FString::Printf(TEXT("%s|%d"), *Name, Tier));
				}
				RoomLabels.Add(Name);
			}
	}
	// the markers, bright over the dark ground (as on the minimap, a little larger)
	TArray<FRDPoi> Pois; GatherPois(Pois, L, 2500.f);
	for (const FRDPoi& Pi : Pois)
	{
		const FVector2D S = ToS(Pi.W);
		if (!Inside(S) || Fade(S) < 0.3f) continue;
		if (Pi.Kind == 2) { Star(S, 8.5f * Sc, RDTacGold); StarsDrawn.Add(Pi.W); }
		else if (Pi.Kind == 3) Diamond(S, 7.5f * Sc, RDTacExit);
		else if (Pi.Kind == 5) SealMark(S, 7.f * Sc);
		else if (Pi.Kind == 6) { AnvilMark(S, 13.f * Sc); AnvilsDrawn.Add(Pi.W); }
	}
	for (const FRDPoi& Pi : Pois)
	{
		const FVector2D S = ToS(Pi.W);
		if (!Inside(S) || Fade(S) < 0.3f) continue;
		if (Pi.Kind == 0) { SoftDot(S, 11.f * Sc, RDTacA(RDTacRed, 0.35f)); SoftDot(S, 5.5f * Sc, RDTacRed); }
		else if (Pi.Kind == 1) { SoftDot(S, 13.f * Sc, RDTacA(RDTacElite, 0.35f)); Triangle(S, 8.5f * Sc, RDTacElite); }
	}
	// her arrow where she is (scrolled away from her, it may be out of view)
	MapArrow = ToS(FVector2D(L.X, L.Y)); bMapArrow = Inside(MapArrow) && Fade(MapArrow) > 0.05f;
	if (bMapArrow) DrawPlayerArrow(MapArrow, Yaw - 90.f, 12.f * Sc);
	// the plaque at the top, the compass in the upper right corner, the key in the lower left, the rooms and the key that
	// closes it at the bottom
	const FLinearColor Gold(1.f, 0.84f, 0.45f, 1.f), Ink(0.86f, 0.82f, 0.72f, 0.95f);
	float Tw, Th;
	const FString Title = TEXT("DUNGEON MAP");
	UI.TextSize(Title, Tw, Th, Medium, Sc * 1.25f, ERDType::Title);
	const float Ph = 58.f * Sc;
	const FVector2D T0(C.X - Tw * 0.5f - 90.f * Sc, A.Y + 6.f * Sc), T1(C.X + Tw * 0.5f + 90.f * Sc, A.Y + 6.f * Sc + Ph);
	if (const FRDUIArt* Pa = UI.Find(TEXT("banner"))) UI.Nine(TEXT("banner"), T0, T1, Ph / FMath::Max((float)Pa->Texture->GetSizeY(), 1.f));
	UI.Text(Title, FLinearColor(0.f, 0.f, 0.f, 0.8f), C.X - Tw * 0.5f + 2.f * Sc, (T0.Y + T1.Y - Th) * 0.5f + 2.f * Sc, Medium, Sc * 1.25f, ERDType::Title);
	UI.Text(Title, Gold, C.X - Tw * 0.5f, (T0.Y + T1.Y - Th) * 0.5f, Medium, Sc * 1.25f, ERDType::Title);
	const float Cz = 118.f * Sc;
	// (north is up: an N over the compass's gem)
	if (UI.Fit(TEXT("compass"), FVector2D(B.X - 40.f * Sc - Cz, A.Y + 46.f * Sc), FVector2D(B.X - 40.f * Sc, A.Y + 46.f * Sc + Cz)))
	{
		UI.TextSize(TEXT("N"), Tw, Th, Small, Sc * 1.2f, ERDType::Title);
		UI.Text(TEXT("N"), Gold, B.X - 40.f * Sc - Cz * 0.5f - Tw * 0.5f, A.Y + 46.f * Sc - Th - 1.f * Sc, Small, Sc * 1.2f, ERDType::Title);
	}
	{
		// (level 5: a line more, the sealed passages; another, the anvils)
		float Y = B.Y - ((Gen->MaxTier > 0 ? 189.f : 166.f) + (Gen->Recipes.Num() > 0 ? 23.f : 0.f)) * Sc; const float X = A.X + 44.f * Sc;
		UI.Text(TEXT("KEY"), Gold, X - 6.f * Sc, Y - 30.f * Sc, Small, Sc * 1.05f, ERDType::Label);
		UI.Fit(TEXT("divider"), FVector2D(X - 14.f * Sc, Y - 14.f * Sc), FVector2D(X + 200.f * Sc, Y + 2.f * Sc));
		auto Key = [&](int32 Kind, const TCHAR* What)
		{
			const FVector2D P(X + 6.f * Sc, Y + 8.f * Sc);
			if (Kind == 0) SoftDot(P, 5.5f * Sc, RDTacRed); else if (Kind == 1) Triangle(P, 7.5f * Sc, RDTacElite); else if (Kind == 2) Star(P, 7.5f * Sc, RDTacGold);
			else if (Kind == 3) Diamond(P, 6.5f * Sc, RDTacExit); else if (Kind == 5) SealMark(P, 6.f * Sc); else if (Kind == 6) AnvilMark(P, 9.f * Sc);
			else DrawLine(P.X - 7.f * Sc, P.Y, P.X + 7.f * Sc, P.Y, RDTacDoor, 2.5f * Sc);
			UI.Text(What, Ink, X + 24.f * Sc, Y, Small, Sc);
			Y += 23.f * Sc;
		};
		Key(0, TEXT("monster")); Key(1, TEXT("elite")); Key(2, TEXT("unlooted chest or trunk")); Key(3, TEXT("unexplored passage")); Key(4, TEXT("door"));
		if (Gen->MaxTier > 0) Key(5, TEXT("sealed passage"));
		if (Gen->Recipes.Num() > 0) Key(6, TEXT("anvil: make repair items"));
	}
	int32 Disc = 0, All = 0; Gen->GetDiscoveryStats(Disc, All);
	const bool bPad = Gen->bCasterControls && Gen->GetPlayerCombat() && Gen->GetPlayerCombat()->IsUsingGamepad();
	const FString Under = FString::Printf(TEXT("%d / %d rooms found      %s  scroll      %s  centre      %s  close"), Disc, All, bPad ? TEXT("D-pad") : TEXT("Arrows"),
	                                      bPad ? TEXT("R3") : TEXT("C"), bPad ? TEXT("Back") : TEXT("M"));
	UI.TextSize(Under, Tw, Th, Small, Sc * 1.1f);
	UI.Text(Under, Ink, C.X - Tw * 0.5f, B.Y - 34.f * Sc, Small, Sc * 1.1f);
}

void ARDHUD::DrawTacticalMap(float Sc, const FVector& L, float Yaw)
{
	// (level 4: in the minimap's painted style)
	if (UI.Has(TEXT("panel_wide"))) { DrawPaintedMap(Sc, L, Yaw); return; }
	UFont* Small = GEngine->GetSmallFont(); UFont* Medium = GEngine->GetMediumFont();
	const FVector2D C(Canvas->ClipX * 0.5f, Canvas->ClipY * 0.5f);
	const float K = Canvas->ClipY / (TacticalMapMeters * 100.f), TS = Gen->TileSize;
	const FVector Vw = L + FVector(Gen->MapPan.X, Gen->MapPan.Y, 0.f);       // (her, or where the arrow keys scrolled it)
	MapView = FVector2D(Vw.X, Vw.Y);
	auto ToS = [&](const FVector2D& W) { return C + FVector2D(W.Y - Vw.Y, -(W.X - Vw.X)) * K; };
	// a light veil only: the game shows through
	Box(FVector2D(0, 0), FVector2D(Canvas->ClipX, Canvas->ClipY), FLinearColor(0.f, 0.012f, 0.02f, 0.28f));
	CacheTiles();
	const float HX = C.Y / K + TS, HY = C.X / K + TS;          // (world half extents shown: screen up = world X)
	const int32 X0 = FMath::FloorToInt((Vw.X - HX) / TS), X1 = FMath::FloorToInt((Vw.X + HX) / TS);
	const int32 Y0 = FMath::FloorToInt((Vw.Y - HY) / TS), Y1 = FMath::FloorToInt((Vw.Y + HY) / TS);
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
		else if (Pi.Kind == 2) { Star(S, 10.f * Sc, RDTacGold); StarsDrawn.Add(Pi.W); }
		else if (Pi.Kind == 5) SealMark(S, 8.f * Sc);
		else Diamond(S, 9.f * Sc, RDTacExit);
	}
	MapArrow = ToS(FVector2D(L.X, L.Y));
	bMapArrow = MapArrow.X >= 0.f && MapArrow.Y >= 0.f && MapArrow.X <= Canvas->ClipX && MapArrow.Y <= Canvas->ClipY;
	if (bMapArrow) DrawPlayerArrow(MapArrow, Yaw - 90.f, 13.f * Sc);
	// title, compass and key
	const bool bPad = Gen->bCasterControls && Gen->GetPlayerCombat() && Gen->GetPlayerCombat()->IsUsingGamepad();
	float Tw, Th;
	const FString Title = TEXT("MAP");
	UI.TextSize(Title, Tw, Th, Medium, Sc * 1.3f);
	UI.Text(Title, RDTacA(RDTacWire, 0.95f), C.X - Tw * 0.5f, 30.f * Sc, Medium, Sc * 1.3f);
	const FString Sub = FString::Printf(TEXT("N up   ·   %s  scroll   ·   %s  centre   ·   %s  close"), bPad ? TEXT("D-pad") : TEXT("Arrows"), bPad ? TEXT("R3") : TEXT("C"), bPad ? TEXT("Back") : TEXT("M"));
	UI.TextSize(Sub, Tw, Th, Small, Sc);
	UI.Text(Sub, FLinearColor(0.8f, 0.92f, 0.95f, 0.85f), C.X - Tw * 0.5f, 30.f * Sc + 36.f * Sc, Small, Sc);
	float Y = Canvas->ClipY - 150.f * Sc; const float X = 40.f * Sc;
	auto Key = [&](int32 Kind, const TCHAR* What)
	{
		const FVector2D P(X, Y + 8.f * Sc);
		if (Kind == 0) SoftDot(P, 6.f * Sc, RDTacRed); else if (Kind == 1) Triangle(P, 8.f * Sc, RDTacElite); else if (Kind == 2) Star(P, 8.f * Sc, RDTacGold);
		else if (Kind == 3) Diamond(P, 7.f * Sc, RDTacExit); else if (Kind == 5) SealMark(P, 7.f * Sc); else DrawLine(P.X - 8.f * Sc, P.Y, P.X + 8.f * Sc, P.Y, RDTacDoor, 3.f * Sc);
		UI.Text(What, FLinearColor(0.85f, 0.92f, 0.95f, 0.9f), X + 18.f * Sc, Y, Small, Sc);
		Y += 24.f * Sc;
	};
	if (Gen->MaxTier > 0) Y -= 24.f * Sc;
	Key(0, TEXT("monster")); Key(1, TEXT("elite")); Key(2, TEXT("unlooted chest or trunk")); Key(3, TEXT("unexplored passage")); Key(4, TEXT("door"));
	if (Gen->MaxTier > 0) Key(5, TEXT("sealed passage"));
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

// ------------------------------------------------------------------------------------------------ random_dungeonmagic_level4
FString ARDHUD::DescribeItem(const FRDItemDef& It) const
{
	const URDCombatComponent* Cb = Gen ? Gen->GetPlayerCombat() : nullptr;
	const float Hp = Cb ? Cb->GetMaxHealth() : 100.f, Mp = Cb ? Cb->GetMaxMana() : 0.f;
	switch (It.Kind)
	{
	case ERDItemKind::Healing: return FString::Printf(TEXT("Restores %.0f%% of your hit points  (%.0f HP)"), It.Amount * 100.f, It.Amount * Hp);
	case ERDItemKind::Mana: return Mp > 0.f ? FString::Printf(TEXT("Restores %.0f%% of your mana  (%.0f)"), It.Amount * 100.f, It.Amount * Mp) : FString(TEXT("No use to you: you have no mana"));
	case ERDItemKind::Speed: return FString::Printf(TEXT("You move %.0f%% faster for %.0f seconds"), It.Amount * 100.f, It.Seconds);
	case ERDItemKind::Food: return FString::Printf(TEXT("Restores %.0f%% of your hit points a second for %.0f s  (%.1f HP/s)"), It.Amount * 100.f, It.Seconds, It.Amount * Hp);
	case ERDItemKind::Armour:
	{
		static const TCHAR* WeightName[3] = { TEXT("Light"), TEXT("Medium"), TEXT("Heavy") };
		FString S = FString::Printf(TEXT("%s armour"), WeightName[(int32)It.ArmourWeight]);
		if (!It.ArmourType.IsEmpty()) S += FString::Printf(TEXT(" (%s)"), *It.ArmourType);
		S += TEXT(".  ");
		if (!It.Looks.IsEmpty()) S += It.Looks.Left(1).ToUpper() + It.Looks.Mid(1) + TEXT(".  ");
		if (It.DamageRating > 0) S += FString::Printf(TEXT("Damage reduction %d / 10, speed %d / 10.  "), It.DamageRating, It.SpeedRating);
		S += FString::Printf(TEXT("Worn, each blow on you takes %.0f%% less"), It.Amount * 100.f);
		S += It.Slower > 0.f ? FString::Printf(TEXT(" and you move %.0f%% slower."), It.Slower * 100.f) : FString(TEXT("."));
		if (It.Durability > 0.f)
		{
			const float Left = Cb ? Cb->GetArmourWear(It.Name) : It.Durability;
			S += FString::Printf(TEXT("  Durability %.0f / %.0f: each blow that reaches you takes 1 off; at 0 it takes off half as much."), Left, It.Durability);
			if (Left <= 0.f) S += TEXT("  It is worn out: mend it with a repair item.");
		}
		const FString No = Gen ? Gen->ArmourRefusal(It, It.Name.ToString().ToLower()) : FString();
		if (!No.IsEmpty()) S += TEXT("  ") + No + TEXT(".");
		return S;
	}
	case ERDItemKind::Repair:
		return FString::Printf(TEXT("Mends %.0f%% of a set of armour's or a found weapon's full durability, up to full.  Enter, then choose what it mends."), It.Amount * 100.f);
	case ERDItemKind::Component:
	{
		// (the repair items that take it)
		TArray<FString> Uses;
		if (Gen)
			for (const FRDRecipe& Rc : Gen->Recipes)
				if (Rc.Parts.ContainsByPredicate([&It](const FRDRecipePart& Pt) { return Pt.AnyOf.Contains(It.Name); })) Uses.Add(Rc.Item.ToString().ToLower());
		FString S = TEXT("A crafting material: an anvil makes repair items from it (F at an anvil; anvils are on the maps).");
		if (Uses.Num() > 0) S += TEXT("  It goes into: ") + FString::Join(Uses, TEXT(", ")) + TEXT(".");
		return S;
	}
	case ERDItemKind::Ring:
	{
		static const TCHAR* What[3] = { TEXT("mana"), TEXT("hit points"), TEXT("ranged weapons' damage") };
		static const TCHAR* Who[3] = { TEXT("spellcasters"), TEXT("the Warrior and the Warlock"), TEXT("the Rogue") };
		FString S = FString::Printf(TEXT("+%.0f%% %s while you wear it (%s; one ring of each kind at a time, rings of a kind do not add up)."),
			It.Amount * 100.f, What[(int32)It.RingKind], Who[(int32)It.RingKind]);
		if (Gen && !Gen->HeroWearsRing(It.RingKind)) S += FString::Printf(TEXT("  The %s cannot wear it."), *Gen->PlayerTitle.ToLower());
		return S;
	}
	case ERDItemKind::Tome:
	{
		const int32 Si = Gen ? Gen->FindSpell(It.Spell) : -1;
		if (Si < 0) return TEXT("A spell tome");
		const FRDSpellDef& Sp = Gen->Spells[Si];
		static const TCHAR* TypeName[4] = { TEXT("offense"), TEXT("protection"), TEXT("curse"), TEXT("summoning") };
		FString S = FString::Printf(TEXT("Teaches %s (%s): %s.  %.0f mana"), *Sp.Name.ToString(), TypeName[(int32)Sp.Type], *Sp.Effect, Sp.Mana);
		if (Sp.Cooldown > 0.f) S += FString::Printf(TEXT(", cooldown %.0f s"), Sp.Cooldown);
		S += TEXT(".");
		if (Gen && !Gen->HeroLearns(Sp.Type)) S += FString::Printf(TEXT("  The %s cannot learn it."), *Gen->PlayerTitle.ToLower());
		return S;
	}
	case ERDItemKind::Weapon:
	{
		// (level 5: Looks holds its type and ratings)
		const bool bFits = Gen && It.WeaponFits.ContainsByPredicate([this](const FRDWeaponFit& F) { return F.Hero == Gen->CurrentHero; });
		FString S = It.Looks.IsEmpty() ? FString() : It.Looks.Left(1).ToUpper() + It.Looks.Mid(1) + TEXT(".  ");
		S += FString::Printf(TEXT("Durability %.0f."), It.Amount);
		if (!bFits) S += FString::Printf(TEXT("  The %s cannot wield it."), Gen ? *Gen->PlayerTitle.ToLower() : TEXT("hero"));
		return S;
	}
	}
	return FString();
}

void ARDHUD::DrawNotices(float Sc)
{
	const URDCombatComponent* Cb = Gen->GetPlayerCombat();
	UFont* Small = GEngine->GetSmallFont();
	UFont* Medium = GEngine->GetMediumFont();
	const float Now = GetWorld()->GetTimeSeconds();
	const bool bPad = Cb->IsUsingGamepad();
	// what she just found: a moment under the middle of the view
	const float Fa = Now - Gen->LastFoundTime;
	if (Fa >= 0.f && Fa < 3.2f && !Gen->LastFound.IsNone())
	{
		const float Al = FMath::Clamp(FMath::Min(Fa / 0.25f, (3.2f - Fa) / 0.6f), 0.f, 1.f);
		// (level 5: a container may hold up to six things: the first by name, the others counted)
		const int32 More = FMath::Max(Gen->LastFoundList.Num() - 1, 0);
		const FString N = Gen->LastFound.ToString() + (More > 0 ? FString::Printf(TEXT("  and %d more"), More) : FString());
		const FString Hint = bPad ? TEXT("Start  inventory") : TEXT("I  inventory");
		float Nw, Nh, Lw, Lh, Hw, Hh;
		UI.TextSize(N, Nw, Nh, Medium, Sc * 1.35f, ERDType::Title); UI.TextSize(TEXT("FOUND"), Lw, Lh, Small, Sc * 1.1f, ERDType::Label); UI.TextSize(Hint, Hw, Hh, Small, Sc);
		// (level 4: on the painted plaque, with the item's picture on its left)
		const FName Ic = ItemIcon(Gen->LastFound);
		const bool bPlaque = UI.Has(TEXT("banner"));
		const float Ih = UI.Has(Ic) ? Lh + Nh + Hh + 26.f * Sc : 0.f;
		const FRDUIArt* Pa = UI.Find(TEXT("banner"));
		const float Bh = Lh + Nh + Hh + 32.f * Sc + 28.f * Sc;                     // (the plaque's height)
		const float Ppx = Pa ? Bh / FMath::Max((float)Pa->Texture->GetSizeY(), 1.f) : 0.f;
		const float Ends = Pa ? (float)Pa->Border.X * Pa->Texture->GetSizeX() * Ppx : 0.f;   // (its iron end caps)
		const float Y = Canvas->ClipY * 0.60f, Tw0 = FMath::Max(Nw, FMath::Max(Lw, Hw)), Bw = Tw0 + 48.f * Sc + Ih + Ends * 2.f;
		const FVector2D A((Canvas->ClipX - Bw) * 0.5f, Y - 10.f * Sc), B((Canvas->ClipX + Bw) * 0.5f, Y + Lh + Nh + Hh + 22.f * Sc);
		if (bPlaque)
			UI.Nine(TEXT("banner"), A - FVector2D(0.f, 14.f * Sc), B + FVector2D(0.f, 14.f * Sc), Ppx, FLinearColor(1.f, 1.f, 1.f, Al));
		else
		{
			Box(A, B, FLinearColor(0.05f, 0.04f, 0.02f, 0.78f * Al));
			Frame(A, B, FLinearColor(1.f, 0.82f, 0.3f, 0.95f * Al), 2.f * Sc);
		}
		const float Cx = (A.X + B.X + Ih) * 0.5f;          // (the text's middle: right of the picture)
		if (Ih > 0.f) UI.Fit(Ic, FVector2D(A.X + Ends + 12.f * Sc, A.Y + 2.f * Sc), FVector2D(A.X + Ends + 12.f * Sc + Ih - 8.f * Sc, B.Y - 2.f * Sc), FLinearColor(1.f, 1.f, 1.f, Al));
		UI.Text(TEXT("FOUND"), FLinearColor(1.f, 0.82f, 0.3f, Al), Cx - Lw * 0.5f, Y, Small, Sc * 1.1f, ERDType::Label);
		UI.Text(N, FLinearColor(1.f, 0.97f, 0.88f, Al), Cx - Nw * 0.5f, Y + Lh + 4.f * Sc, Medium, Sc * 1.35f, ERDType::Title);
		UI.Text(Hint, FLinearColor(0.75f, 0.72f, 0.65f, Al), Cx - Hw * 0.5f, Y + Lh + Nh + 10.f * Sc, Small, Sc);
	}
	// what the inventory did, or a cast refused (not over the open inventory or crafting panel: they show it themselves)
	const float Ma = Now - Cb->MessageTime;
	if (!Cb->IsInventoryOpen() && !Cb->IsCraftingOpen() && Ma >= 0.f && Ma < 2.6f && !Cb->Message.IsEmpty())
	{
		const float Al = FMath::Clamp((2.6f - Ma) / 0.5f, 0.f, 1.f);
		float Tw, Th; UI.TextSize(Cb->Message, Tw, Th, Small, Sc * 1.3f);
		const float X = (Canvas->ClipX - Tw) * 0.5f, Y = Canvas->ClipY * 0.30f;
		if (const FRDUIArt* Pa = UI.Find(TEXT("banner")))
		{
			const float Bh = Th + 40.f * Sc, Px = Bh / FMath::Max((float)Pa->Texture->GetSizeY(), 1.f);
			const float Ends = (float)Pa->Border.X * Pa->Texture->GetSizeX() * Px + 14.f * Sc;
			UI.Nine(TEXT("banner"), FVector2D(X - Ends, Y - 20.f * Sc), FVector2D(X + Tw + Ends, Y + Th + 20.f * Sc), Px, FLinearColor(1.f, 1.f, 1.f, Al));
		}
		else Box(FVector2D(X - 14.f * Sc, Y - 7.f * Sc), FVector2D(X + Tw + 14.f * Sc, Y + Th + 7.f * Sc), FLinearColor(0.03f, 0.03f, 0.04f, 0.65f * Al));
		UI.Text(Cb->Message, FLinearColor(0.95f, 0.92f, 0.82f, Al), X, Y, Small, Sc * 1.3f);
	}
}

void ARDHUD::DrawInventory(float Sc)
{
	URDCombatComponent* Cb = Gen->GetPlayerCombat();
	UFont* Small = GEngine->GetSmallFont();
	UFont* Medium = GEngine->GetMediumFont();
	const bool bPad = Cb->IsUsingGamepad();
	// (level 5: choosing what a repair item mends: its list in place of the inventory's)
	const bool bRepair = Cb->IsPickingRepair();
	const TArray<FString> Lines = bRepair ? Cb->GetRepairLines() : Cb->GetInventoryLines();
	const int32 Cur = bRepair ? Cb->GetRepairCursor() : Cb->GetInventoryCursor();
	const FLinearColor Gold(1.f, 0.82f, 0.35f), Dim(0.70f, 0.68f, 0.62f), Line(0.75f, 0.65f, 0.45f, 0.9f), Worn(1.f, 0.45f, 0.35f);
	// the game stands still under it
	Box(FVector2D(0, 0), FVector2D(Canvas->ClipX, Canvas->ClipY), FLinearColor(0.f, 0.f, 0.01f, 0.55f));
	// the list's sections in order: each line's kind (its first field), the heading over it, shown empty or not
	struct FSec { FString Kind; FString Head; bool bAlways; };
	TArray<FSec> Secs;
	if (bRepair)
	{
		const int32 Ri = Gen->FindItem(Cb->GetRepairItem());
		Secs.Add({ TEXT("armour"), FString::Printf(TEXT("MEND WITH THE %s  (+%.0f%%)"), *Cb->GetRepairItem().ToString().ToUpper(), Ri >= 0 ? Gen->Items[Ri].Amount * 100.f : 0.f), false });
		Secs.Add({ TEXT("weapon"), TEXT("WEAPONS YOU FOUND"), false });
	}
	else
	{
		Secs.Add({ TEXT("weapon"), TEXT("WEAPONS AND SPELLS"), true });
		Secs.Add({ TEXT("item"), TEXT("POTIONS AND FOOD"), true });
		Secs.Add({ TEXT("repair"), TEXT("REPAIR ITEMS"), false });
		Secs.Add({ TEXT("armour"), TEXT("ARMOUR"), false });
		Secs.Add({ TEXT("ring"), TEXT("RINGS"), false });
		Secs.Add({ TEXT("tome"), FString::Printf(TEXT("TOMES THE %s CANNOT LEARN"), *Gen->PlayerTitle.ToUpper()), false });
		Secs.Add({ TEXT("component"), TEXT("MATERIALS"), false });
		Secs.Add({ TEXT("carried"), FString::Printf(TEXT("WEAPONS THE %s CANNOT WIELD"), *Gen->PlayerTitle.ToUpper()), false });
	}
	TArray<int32> SecOf; TArray<int32> SecCount; SecCount.Init(0, Secs.Num());
	for (const FString& L : Lines)
	{
		int32 K = Secs.IndexOfByPredicate([&L](const FSec& S) { return L.StartsWith(S.Kind + TEXT("|")); });
		if (K < 0) K = 0;
		SecOf.Add(K); ++SecCount[K];
	}
	const float Rh = 34.f * Sc, W = 1000.f * Sc, Pd = 22.f * Sc, HeadH = 58.f * Sc;
	// (a long list: only the rows that fit on the screen, scrolled with the cursor; a heading only over rows shown)
	auto Heads = [&](int32 F0, int32 F1)
	{
		int32 N = 0;
		for (int32 K = 0; K < Secs.Num(); ++K)
		{
			bool bShown = Secs[K].bAlways && SecCount[K] == 0;
			for (int32 I = F0; I < F1 && !bShown; ++I) bShown = SecOf[I] == K;
			N += bShown ? 1 : 0;
		}
		return N;
	};
	const float Room = Canvas->ClipY - 80.f * Sc - 150.f * Sc - 30.f * Sc;
	int32 Fit = Lines.Num(), First = 0;
	for (int32 Pass = 0; Pass < 3; ++Pass)
	{
		const int32 Nh = Heads(First, First + Fit);
		const float Empty = (Secs.Num() > 1 && Secs[1].bAlways && SecCount[1] == 0) ? Rh : 0.f;
		if (HeadH * Nh + Empty + Rh * Lines.Num() <= Room) { Fit = Lines.Num(); First = 0; break; }
		Fit = FMath::Clamp(FMath::FloorToInt32((Room - HeadH * Nh - Empty) / Rh), 4, Lines.Num());
		First = FMath::Clamp(Cur - Fit / 2, 0, FMath::Max(0, Lines.Num() - Fit));
	}
	auto Shown = [&](int32 I) { return I >= First && I < First + Fit; };
	const int32 NhShown = Heads(First, First + Fit);
	const float ListH = 46.f * Sc + HeadH * NhShown + Rh * Fit + (Fit < Lines.Num() ? 30.f * Sc : 0.f) + ((Secs.Num() > 1 && Secs[1].bAlways && SecCount[1] == 0) ? Rh : 0.f);
	const float H = FMath::Max(ListH, (UI.Has(TEXT("slot")) ? 400.f : 330.f) * Sc) + 150.f * Sc;     // (the picture of the chosen one takes room)
	const FVector2D A((Canvas->ClipX - W) * 0.5f, FMath::Max(40.f * Sc, (Canvas->ClipY - H) * 0.5f)), B = A + FVector2D(W, H);
	// (level 4: the painted board, a divider under each heading, a picture in each row, a lit plate under the chosen row)
	if (!Board(TEXT("panel_wide"), A, B, Sc, 44.f * Sc))
	{
		Box(A, B, FLinearColor(0.035f, 0.04f, 0.055f, 0.94f));
		Frame(A, B, Line, 2.f * Sc);
	}
	const bool bDivider = UI.Has(TEXT("divider")), bPlate = UI.Has(TEXT("button"));
	const float Tin = UI.Has(TEXT("panel_wide")) ? 24.f * Sc : 0.f;      // (the title row clear of the board's corner ornaments)
	UI.Text(bRepair ? TEXT("REPAIR") : TEXT("INVENTORY"), RDInk, A.X + Pd + Tin, A.Y + 16.f * Sc, Medium, Sc * 1.5f, ERDType::Title);
	float Tw, Th;
	UI.TextSize(Gen->PlayerTitle, Tw, Th, Small, Sc * 1.2f, ERDType::Title);
	UI.Text(Gen->PlayerTitle, Gold, B.X - Pd - Tin - Tw, A.Y + 18.f * Sc, Small, Sc * 1.2f, ERDType::Title);
	if (Cb->bInventoryPausesGame) { float Pw, Ph; UI.TextSize(TEXT("the game is paused"), Pw, Ph, Small, Sc * 0.95f); UI.Text(TEXT("the game is paused"), Dim, B.X - Pd - Tin - Pw, A.Y + 42.f * Sc, Small, Sc * 0.95f); }
	// ---- the list (left)
	const float Lx = A.X + Pd, Lw = W * 0.5f - Pd;
	float Y = A.Y + 76.f * Sc;
	auto Header = [&](const FString& T)
	{
		UI.Text(T, Dim, Lx, Y, Small, Sc * 1.05f, ERDType::Label); Y += 26.f * Sc;
		if (bDivider) UI.Fit(TEXT("divider"), FVector2D(Lx - 8.f * Sc, Y - 18.f * Sc), FVector2D(Lx + Lw + 8.f * Sc, Y + 12.f * Sc));
		else Box(FVector2D(Lx, Y - 4.f * Sc), FVector2D(Lx + Lw, Y - 3.f * Sc), FLinearColor(0.75f, 0.65f, 0.45f, 0.4f));
		Y += 4.f * Sc;
	};
	auto Row = [&](int32 I, const FString& Name, const FString& Tag, const FLinearColor& TagC, FName Icon)
	{
		if (!Shown(I)) return;
		const bool bOn = I == Cur;
		const FVector2D R0(Lx, Y), R1(Lx + Lw, Y + Rh - 4.f * Sc);
		if (bOn)
		{
			const FRDUIArt* Pl = UI.Find(TEXT("button"));
			if (bPlate) UI.Nine(TEXT("button"), R0 - FVector2D(4.f * Sc), R1 + FVector2D(4.f * Sc), (Rh + 4.f * Sc) / FMath::Max((float)Pl->Texture->GetSizeY(), 1.f), FLinearColor(1.25f, 1.05f, 0.7f));
			else Box(R0, R1, FLinearColor(0.36f, 0.27f, 0.10f, 0.95f));
			Frame(R0, R1, Gold, 2.f * Sc);
		}
		float Ix = 0.f;
		if (UI.Has(Icon)) { Ix = Rh; UI.Fit(Icon, FVector2D(R0.X + 8.f * Sc, R0.Y - 2.f * Sc), FVector2D(R0.X + 4.f * Sc + Rh, R1.Y + 2.f * Sc)); }
		float Gw = 0.f, Gh = 0.f;
		if (!Tag.IsEmpty()) UI.TextSize(Tag, Gw, Gh, Small, Sc, ERDType::Label);
		// (a name too long beside its tag is drawn smaller)
		float Nw, Nh, Nk = Sc * 1.15f;
		UI.TextSize(Name, Nw, Nh, Small, Nk);
		const float Avail = Lw - 24.f * Sc - Ix - (Gw > 0.f ? Gw + 14.f * Sc : 0.f);
		if (Nw > Avail && Nw > 0.f) Nk *= FMath::Max(Avail / Nw, 0.7f);
		UI.Text(Name, bOn ? FLinearColor::White : FLinearColor(0.86f, 0.84f, 0.78f), R0.X + 12.f * Sc + Ix, R0.Y + 6.f * Sc, Small, Nk);
		if (!Tag.IsEmpty()) UI.Text(Tag, TagC, R1.X - 12.f * Sc - Gw, R0.Y + 8.f * Sc, Small, Sc, ERDType::Label);
		Y += Rh;
	};
	int32 LastSec = -1;
	auto Open = [&](int32 K)
	{
		// (the headings from the last one drawn up to this section: the always-shown empty ones between say so)
		for (int32 J = LastSec + 1; J <= K; ++J)
		{
			const bool bRows = SecCount[J] > 0;
			if (!bRows && !Secs[J].bAlways) continue;
			if (bRows && J < K) continue;           // (a section with rows gets its heading with its first row shown)
			if (LastSec >= 0 || J > 0) Y += 12.f * Sc;
			Header(Secs[J].Head);
			if (!bRows) { UI.Text(TEXT("nothing yet: the chests, trunks and barrels hold some"), Dim, Lx + 12.f * Sc, Y + 6.f * Sc, Small, Sc); Y += Rh; }
		}
		LastSec = K;
	};
	for (int32 I = 0; I < Lines.Num(); ++I)
	{
		if (!Shown(I)) continue;
		if (SecOf[I] != LastSec) Open(SecOf[I]);
		TArray<FString> P; Lines[I].ParseIntoArray(P, TEXT("|"));
		const FString& Kd = P.Num() > 0 ? P[0] : FString();
		if (bRepair)
		{
			// "armour|<set>|<left>|<full>|<after>", "weapon|<index>|<name>|<left>|<full>|<after>"
			const bool bArm = Kd == TEXT("armour");
			if (P.Num() < (bArm ? 5 : 6)) continue;
			const FString Nm = bArm ? P[1] : P[2];
			const float Left = FCString::Atof(*P[bArm ? 2 : 3]), Full = FCString::Atof(*P[bArm ? 3 : 4]), After = FCString::Atof(*P[bArm ? 4 : 5]);
			const FString Tag = Left >= Full ? FString::Printf(TEXT("%.0f / %.0f  WHOLE"), Left, Full) : FString::Printf(TEXT("%.0f  TO  %.0f / %.0f"), Left, After, Full);
			Row(I, Nm, Tag, Left >= Full ? Dim : Gold, bArm ? ItemIcon(FName(*Nm)) : WeaponIcon(FCString::Atoi(*P[1])));
			continue;
		}
		if (Kd == TEXT("weapon"))
		{
			const FRDWeaponDef& Wp = Gen->Weapons[I];
			FString Tag = Wp.bAlongside ? TEXT("ALWAYS AT HAND") : I == Cb->GetWeaponIndex() ? TEXT("IN YOUR HANDS") : TEXT("");
			// (level 5: a found weapon's durability left)
			if (Wp.Durability > 0.f) Tag = (Tag.IsEmpty() ? FString() : Tag + TEXT("   ")) + FString::Printf(TEXT("%.0f / %.0f"), Cb->GetWeaponWear(I), Wp.Durability);
			Row(I, Wp.Name.ToString(), Tag, Wp.bAlongside ? RDCyan : Gold, Wp.Icon);
		}
		else if (Kd == TEXT("armour") && P.Num() >= 3)
		{
			// (level 5: WORN on the set she has on; what is left of its durability)
			const float Left = P.Num() >= 5 ? FCString::Atof(*P[3]) : 0.f, Full = P.Num() >= 5 ? FCString::Atof(*P[4]) : 0.f;
			FString Tag = P[2] == TEXT("1") ? TEXT("WORN") : TEXT("");
			if (Full > 0.f) Tag = (Tag.IsEmpty() ? FString() : Tag + TEXT("   ")) + (Left <= 0.f ? FString(TEXT("WORN OUT")) : FString::Printf(TEXT("%.0f / %.0f"), Left, Full));
			Row(I, P[1], Tag, Full > 0.f && Left <= 0.f ? Worn : RDCyan, ItemIcon(FName(*P[1])));
		}
		else if (Kd == TEXT("ring") && P.Num() >= 4)
		{
			// (level 5: WORN on the one of its kind she has on)
			const FString Tag = P[2] == TEXT("1") ? FString(TEXT("WORN")) : (P[3] != TEXT("1") ? FString::Printf(TEXT("x %s"), *P[3]) : FString());
			Row(I, P[1], Tag, RDCyan, ItemIcon(FName(*P[1])));
		}
		else if (P.Num() >= 3) Row(I, P[1], FString::Printf(TEXT("x %s"), *P[2]), (Kd == TEXT("carried") || Kd == TEXT("component") || Kd == TEXT("tome")) ? Dim : Gold, ItemIcon(FName(*P[1])));
	}
	if (Lines.Num() == 0 || LastSec < Secs.Num() - 1) Open(Secs.Num() - 1);       // (the empty always-shown sections after the last row)
	if (Fit < Lines.Num())
	{
		const FString More = FString::Printf(TEXT("%d more above,  %d more below"), First, Lines.Num() - First - Fit);
		UI.Text(More, Dim, Lx + 12.f * Sc, Y + 6.f * Sc, Small, Sc * 0.95f);
		Y += 30.f * Sc;
	}
	// ---- the one under the cursor (right): what it does; then hers
	const float Rx = A.X + W * 0.5f + Pd, Rw = W * 0.5f - Pd * 2.f;
	float Ry = A.Y + 76.f * Sc;
	Box(FVector2D(Rx - Pd * 0.5f, Ry), FVector2D(Rx - Pd * 0.5f + 1.f, B.Y - 110.f * Sc), FLinearColor(0.75f, 0.65f, 0.45f, 0.4f));
	TArray<FString> Sel;
	if (Lines.IsValidIndex(Cur)) Lines[Cur].ParseIntoArray(Sel, TEXT("|"));
	auto Para = [&](const FString& T, const FLinearColor& C, float K)
	{
		// (wrapped at the column's width, word by word)
		TArray<FString> Words; T.ParseIntoArray(Words, TEXT(" "));
		FString Cur2;
		for (const FString& Wd : Words)
		{
			const FString Try = Cur2.IsEmpty() ? Wd : Cur2 + TEXT(" ") + Wd;
			UI.TextSize(Try, Tw, Th, Small, K);
			if (Tw > Rw && !Cur2.IsEmpty()) { UI.Text(Cur2, C, Rx, Ry, Small, K); Ry += Th + 4.f * Sc; Cur2 = Wd; }
			else Cur2 = Try;
		}
		if (!Cur2.IsEmpty()) { UI.TextSize(Cur2, Tw, Th, Small, K); UI.Text(Cur2, C, Rx, Ry, Small, K); Ry += Th + 4.f * Sc; }
	};
	auto Picture = [&](FName Ic, const FString& Title)
	{
		// (level 4: its picture large, in a slot, beside its name)
		if (UI.Has(Ic))
		{
			const float Sz = 104.f * Sc;
			UI.Fit(TEXT("slot"), FVector2D(Rx, Ry), FVector2D(Rx + Sz, Ry + Sz));
			UI.Fit(Ic, FVector2D(Rx + 16.f * Sc, Ry + 14.f * Sc), FVector2D(Rx + Sz - 16.f * Sc, Ry + Sz - 14.f * Sc));
			float Nw, Nh, Nk = Sc * 1.15f;
			UI.TextSize(Title.ToUpper(), Nw, Nh, Medium, Nk, ERDType::Title);
			if (Nw > Rw - Sz - 20.f * Sc) Nk *= FMath::Max((Rw - Sz - 20.f * Sc) / Nw, 0.6f);
			UI.Text(Title.ToUpper(), FLinearColor::White, Rx + Sz + 16.f * Sc, Ry + Sz * 0.5f - 16.f * Sc, Medium, Nk, ERDType::Title);
			Ry += Sz + 12.f * Sc;
		}
		else { UI.Text(Title.ToUpper(), FLinearColor::White, Rx, Ry, Medium, Sc * 1.15f, ERDType::Title); Ry += 40.f * Sc; }
	};
	if (bRepair && Sel.Num() >= 5)
	{
		const bool bArm = Sel[0] == TEXT("armour");
		const FString Nm = bArm ? Sel[1] : (Sel.Num() >= 6 ? Sel[2] : FString());
		const float Left = FCString::Atof(*Sel[bArm ? 2 : 3]), Full = FCString::Atof(*Sel[bArm ? 3 : 4]), After = Sel.Num() > (bArm ? 4 : 5) ? FCString::Atof(*Sel[bArm ? 4 : 5]) : Left;
		Picture(bArm ? ItemIcon(FName(*Nm)) : WeaponIcon(FCString::Atoi(*Sel[1])), Nm);
		Para(FString::Printf(TEXT("Durability now %.0f / %.0f"), Left, Full), RDInk, Sc * 1.1f);
		if (Left >= Full) Para(TEXT("It is whole: nothing to mend"), Dim, Sc * 1.05f);
		else
		{
			Para(FString::Printf(TEXT("The %s gives it back %.0f:  %.0f / %.0f after"), *Cb->GetRepairItem().ToString().ToLower(), After - Left, After, Full), FLinearColor(0.6f, 0.95f, 0.6f), Sc * 1.1f);
			if (bArm && Left <= 0.f) Para(TEXT("Worn out now: mended, it takes off its whole share again"), RDCyan, Sc * 1.05f);
		}
		Ry += 6.f * Sc;
		Para(FString::Printf(TEXT("%s  mend it      %s  back"), bPad ? TEXT("A") : TEXT("Enter"), bPad ? TEXT("B") : TEXT("Backspace")), Gold, Sc * 1.05f);
		Para(FString::Printf(TEXT("%d %s left"), Cb->GetItemCount(Cb->GetRepairItem()), *Cb->GetRepairItem().ToString().ToLower()), Dim, Sc);
	}
	else if (!bRepair && Sel.Num() >= 2)
	{
		Picture(Sel[0] == TEXT("weapon") ? WeaponIcon(Cur) : ItemIcon(FName(*Sel[1])), Sel[1]);
		if (Sel[0] == TEXT("weapon") && Gen->Weapons.IsValidIndex(Cur))
		{
			const FRDWeaponDef& Wp = Gen->Weapons[Cur];
			const bool bRanged = Wp.bSpell && Wp.BoltMesh, bMagic = Wp.bSpell && !Wp.BoltMesh;
			const float Bonus = !Wp.bSpell ? Gen->MeleeBonus : bRanged ? Gen->RangedBonus : 0.f;
			// (level 5: a spell of the table: its line, its type, its cooldown and how long it lasts)
			const FRDSpellDef* Sp = Gen->Spells.IsValidIndex(Wp.SpellIndex) ? &Gen->Spells[Wp.SpellIndex] : nullptr;
			if (Sp)
			{
				static const TCHAR* TypeName[4] = { TEXT("Offense"), TEXT("Protection"), TEXT("Curse"), TEXT("Summoning") };
				Para(FString::Printf(TEXT("%s spell:  %s"), TypeName[(int32)Sp->Type], *Sp->Effect), RDInk, Sc * 1.05f);
				FString Num;
				if (Sp->Cooldown > 0.f) Num += FString::Printf(TEXT("cooldown %.0f s"), Sp->Cooldown);
				if (Sp->Duration > 0.f) Num += (Num.IsEmpty() ? FString() : FString(TEXT("  ·  "))) + FString::Printf(TEXT("lasts %.0f s"), Sp->Duration);
				if (!Num.IsEmpty()) Para(Num, Dim, Sc * 1.0f);
				if (Cb->GetCooldownLeft(Cur) > 0.f) Para(FString::Printf(TEXT("Ready in %.0f s"), FMath::CeilToFloat(Cb->GetCooldownLeft(Cur))), FLinearColor(1.f, 0.6f, 0.4f), Sc);
			}
			else
			Para(bMagic ? TEXT("A spell: a bolt flies after the monster you face") : bRanged ? TEXT("A ranged weapon: its bolts fly straight at the monster you face") : TEXT("A melee weapon"), Dim, Sc * 1.05f);
			// (level 5: a found weapon's type, its ratings out of 10, what is left of it)
			if (Wp.SpeedRating > 0)
			{
				Para(FString::Printf(TEXT("%s%s  ·  speed %d / 10  ·  damage %d / 10"), *Wp.WeaponType.Left(1).ToUpper(), *Wp.WeaponType.Mid(1), Wp.SpeedRating, Wp.DamageRating), RDInk, Sc * 1.05f);
				Para(FString::Printf(TEXT("Durability %.0f / %.0f: a hit takes 1 off, at 0 it breaks; a repair item mends it"), Cb->GetWeaponWear(Cur), Wp.Durability), FLinearColor(0.75f, 0.85f, 0.7f), Sc * 1.05f);
			}
			Para(FString::Printf(TEXT("%.0f damage%s"), Cb->GetDamageOf(Cur), Bonus > 0.f ? *FString::Printf(TEXT("  (%.0f, +%.0f%% your %s bonus)"), Wp.Damage, Bonus * 100.f, bRanged ? TEXT("ranged") : TEXT("melee")) : TEXT("")), RDInk, Sc * 1.1f);
			if (Wp.ManaCost > 0.f) Para(FString::Printf(TEXT("%.0f mana a cast"), Wp.ManaCost), FLinearColor(0.55f, 0.7f, 1.f), Sc * 1.1f);
			Ry += 6.f * Sc;
			Para(Wp.bAlongside ? TEXT("Cast with RMB or E (LB) while your weapon stays drawn") : Cur == Cb->GetWeaponIndex() ? TEXT("In your hands") : (bPad ? TEXT("A  wield it") : TEXT("Enter  wield it")), Gold, Sc * 1.05f);
		}
		else
		{
			const int32 Ix = Gen->FindItem(FName(*Sel[1]));
			if (Ix >= 0) Para(DescribeItem(Gen->Items[Ix]), RDInk, Sc * 1.1f);
			Ry += 6.f * Sc;
			const FString Use = bPad ? TEXT("A") : TEXT("Enter");
			if (Sel[0] == TEXT("item")) Para(Use + TEXT("  use it"), Gold, Sc * 1.05f);
			else if (Sel[0] == TEXT("repair")) Para(Use + TEXT("  choose what it mends"), Gold, Sc * 1.05f);
			else if (Sel[0] == TEXT("armour") || Sel[0] == TEXT("ring")) Para(Use + (Sel.Num() >= 3 && Sel[2] == TEXT("1") ? TEXT("  take it off") : TEXT("  put it on")), Gold, Sc * 1.05f);
		}
	}
	// her state
	Ry = FMath::Max(Ry + 18.f * Sc, A.Y + 250.f * Sc);
	Para(FString::Printf(TEXT("Hit points  %.0f / %.0f"), FMath::CeilToFloat(Cb->GetHealth()), Cb->GetMaxHealth()), FLinearColor(0.5f, 0.9f, 0.55f), Sc * 1.05f);
	if (Cb->GetMaxMana() > 0.f) Para(FString::Printf(TEXT("Mana  %.0f / %.0f"), FMath::FloorToFloat(Cb->GetMana()), Cb->GetMaxMana()), FLinearColor(0.55f, 0.7f, 1.f), Sc * 1.05f);
	if (!Cb->GetWornArmour().IsNone())
	{
		const FName Wa = Cb->GetWornArmour();
		FString S = FString::Printf(TEXT("Armour  %s,  blows %.0f%% less"), *Wa.ToString(), Cb->GetArmour() * 100.f);
		if (Cb->GetArmourSlow() > 0.f) S += FString::Printf(TEXT(",  %.0f%% slower"), Cb->GetArmourSlow() * 100.f);
		if (Cb->GetArmourDurability(Wa) > 0.f) S += FString::Printf(TEXT(",  durability %.0f / %.0f"), Cb->GetArmourWear(Wa), Cb->GetArmourDurability(Wa));
		Para(S, RDCyan, Sc * 1.05f);
	}
	for (const URDCombatComponent::FEffect& E : Cb->GetEffects())
		Para(E.Kind == ERDItemKind::Speed ? FString::Printf(TEXT("Speed +%.0f%%: %.0f s left"), E.Amount * 100.f, FMath::CeilToFloat(E.Left))
		                                 : FString::Printf(TEXT("Regenerating %.1f HP/s: %.0f s left"), E.Amount * Cb->GetMaxHealth(), FMath::CeilToFloat(E.Left)), RDCyan, Sc);
	// ---- the keys, and what was done last
	const float Fy = B.Y - 92.f * Sc;
	if (bDivider) UI.Fit(TEXT("divider"), FVector2D(A.X + Pd, Fy - 20.f * Sc), FVector2D(B.X - Pd, Fy + 20.f * Sc));
	else Box(FVector2D(A.X + Pd, Fy), FVector2D(B.X - Pd, Fy + 1.f), FLinearColor(0.75f, 0.65f, 0.45f, 0.4f));
	if (Cb->MessageTime > -50.f && !Cb->Message.IsEmpty()) UI.Text(Cb->Message, FLinearColor(1.f, 0.93f, 0.75f), A.X + Pd + Tin, Fy + 14.f * Sc, Small, Sc * 1.15f);
	const FString Keys = bRepair ? (bPad ? TEXT("D-pad / left stick  select      A  mend it      B  back      Start  close")
	                                     : TEXT("W S / arrows / wheel  select      Enter or E  mend it      Backspace  back      I or Tab  close"))
	                             : (bPad ? TEXT("D-pad / left stick  select      A  wield or use      Start or B  close")
	                                     : TEXT("W S / arrows / wheel  select      Enter or E  wield or use      I or Tab  close"));
	UI.Text(Keys, Dim, A.X + Pd + Tin, Fy + 50.f * Sc, Small, Sc * 1.05f);
}

void ARDHUD::DrawCrafting(float Sc)
{
	// the anvil's panel: the recipes on the left (CAN MAKE on those she has everything for), the chosen one on the right:
	// its picture, what it mends, and each part with what she carries of it against what it takes
	URDCombatComponent* Cb = Gen->GetPlayerCombat();
	UFont* Small = GEngine->GetSmallFont();
	UFont* Medium = GEngine->GetMediumFont();
	const bool bPad = Cb->IsUsingGamepad();
	const TArray<FString> Lines = Cb->GetCraftLines();
	const int32 Cur = Cb->GetCraftCursor();
	const FLinearColor Gold(1.f, 0.82f, 0.35f), Dim(0.70f, 0.68f, 0.62f), Have(0.55f, 0.95f, 0.55f), Lack(1.f, 0.5f, 0.4f);
	Box(FVector2D(0, 0), FVector2D(Canvas->ClipX, Canvas->ClipY), FLinearColor(0.f, 0.f, 0.01f, 0.55f));
	const float Rh = 40.f * Sc, W = 1000.f * Sc, Pd = 22.f * Sc, H = 700.f * Sc;
	const FVector2D A((Canvas->ClipX - W) * 0.5f, FMath::Max(40.f * Sc, (Canvas->ClipY - H) * 0.5f)), B = A + FVector2D(W, H);
	if (!Board(TEXT("panel_wide"), A, B, Sc, 44.f * Sc))
	{
		Box(A, B, FLinearColor(0.035f, 0.04f, 0.055f, 0.94f));
		Frame(A, B, FLinearColor(0.75f, 0.65f, 0.45f, 0.9f), 2.f * Sc);
	}
	const bool bDivider = UI.Has(TEXT("divider")), bPlate = UI.Has(TEXT("button"));
	const float Tin = UI.Has(TEXT("panel_wide")) ? 24.f * Sc : 0.f;
	UI.Text(TEXT("THE ANVIL"), RDInk, A.X + Pd + Tin, A.Y + 16.f * Sc, Medium, Sc * 1.5f, ERDType::Title);
	float Tw, Th;
	const FString Sub = TEXT("make repair items  ·  break down the weapons you found");
	UI.TextSize(Sub, Tw, Th, Small, Sc * 1.05f);
	UI.Text(Sub, Gold, B.X - Pd - Tin - Tw, A.Y + 22.f * Sc, Small, Sc * 1.05f);
	if (Cb->bInventoryPausesGame) { float Pw, Ph; UI.TextSize(TEXT("the game is paused"), Pw, Ph, Small, Sc * 0.95f); UI.Text(TEXT("the game is paused"), Dim, B.X - Pd - Tin - Pw, A.Y + 46.f * Sc, Small, Sc * 0.95f); }
	const float Lx = A.X + Pd, Lw = W * 0.42f - Pd;
	float Y = A.Y + 80.f * Sc;
	UI.Text(TEXT("RECIPES"), Dim, Lx, Y, Small, Sc * 1.05f, ERDType::Label); Y += 26.f * Sc;
	if (bDivider) UI.Fit(TEXT("divider"), FVector2D(Lx - 8.f * Sc, Y - 18.f * Sc), FVector2D(Lx + Lw + 8.f * Sc, Y + 12.f * Sc));
	Y += 4.f * Sc;
	TArray<TArray<FString>> Parsed;
	// (level 5: the weapons to break down follow the recipes; a long list scrolls with the cursor)
	const int32 Fit = FMath::Max(4, FMath::FloorToInt32((H - 80.f * Sc - 30.f * Sc - 40.f * Sc - 120.f * Sc) / Rh));
	const int32 First = Lines.Num() > Fit ? FMath::Clamp(Cur - Fit / 2, 0, Lines.Num() - Fit) : 0;
	bool bBreakHead = false;
	for (int32 I = 0; I < Lines.Num(); ++I)
	{
		TArray<FString> P; Lines[I].ParseIntoArray(P, TEXT("|"), false);
		Parsed.Add(P);
		if (P.Num() < 3 || I < First || I >= First + Fit) continue;
		if (P[0] == TEXT("breakdown"))
		{
			if (!bBreakHead)
			{
				bBreakHead = true;
				Y += 8.f * Sc;
				UI.Text(TEXT("BREAK DOWN"), Dim, Lx, Y, Small, Sc * 1.05f, ERDType::Label); Y += 26.f * Sc;
				if (bDivider) UI.Fit(TEXT("divider"), FVector2D(Lx - 8.f * Sc, Y - 18.f * Sc), FVector2D(Lx + Lw + 8.f * Sc, Y + 12.f * Sc));
				Y += 4.f * Sc;
			}
			const bool bOn = I == Cur, bDrawn = P.Num() > 3 && P[3] == TEXT("1");
			const FVector2D R0(Lx, Y), R1(Lx + Lw, Y + Rh - 4.f * Sc);
			if (bOn)
			{
				const FRDUIArt* Pl = UI.Find(TEXT("button"));
				if (bPlate) UI.Nine(TEXT("button"), R0 - FVector2D(4.f * Sc), R1 + FVector2D(4.f * Sc), (Rh + 4.f * Sc) / FMath::Max((float)Pl->Texture->GetSizeY(), 1.f), FLinearColor(1.25f, 1.05f, 0.7f));
				else Box(R0, R1, FLinearColor(0.36f, 0.27f, 0.10f, 0.95f));
				Frame(R0, R1, Gold, 2.f * Sc);
			}
			float Ix = 0.f;
			const FName Ic = P[2].StartsWith(TEXT("w")) ? WeaponIcon(FCString::Atoi(*P[2].Mid(1))) : ItemIcon(FName(*P[2].Mid(1)));
			if (UI.Has(Ic)) { Ix = Rh; UI.Fit(Ic, FVector2D(R0.X + 8.f * Sc, R0.Y - 2.f * Sc), FVector2D(R0.X + 4.f * Sc + Rh, R1.Y + 2.f * Sc)); }
			float Nw, Nh, Nk = Sc * 1.1f;
			UI.TextSize(P[1], Nw, Nh, Small, Nk);
			if (Nw > Lw - Ix - 150.f * Sc) Nk *= FMath::Max((Lw - Ix - 150.f * Sc) / Nw, 0.7f);
			UI.Text(P[1], bOn ? FLinearColor::White : FLinearColor(0.86f, 0.84f, 0.78f), R0.X + 12.f * Sc + Ix, R0.Y + 8.f * Sc, Small, Nk);
			const FString Tag = bDrawn ? TEXT("IN YOUR HANDS") : TEXT("BREAK DOWN");
			UI.TextSize(Tag, Tw, Th, Small, Sc, ERDType::Label);
			UI.Text(Tag, bDrawn ? Dim : Gold, R1.X - 12.f * Sc - Tw, R0.Y + 10.f * Sc, Small, Sc, ERDType::Label);
			Y += Rh;
			continue;
		}
		const bool bOn = I == Cur, bCan = P[2] == TEXT("1");
		const FVector2D R0(Lx, Y), R1(Lx + Lw, Y + Rh - 4.f * Sc);
		if (bOn)
		{
			const FRDUIArt* Pl = UI.Find(TEXT("button"));
			if (bPlate) UI.Nine(TEXT("button"), R0 - FVector2D(4.f * Sc), R1 + FVector2D(4.f * Sc), (Rh + 4.f * Sc) / FMath::Max((float)Pl->Texture->GetSizeY(), 1.f), FLinearColor(1.25f, 1.05f, 0.7f));
			else Box(R0, R1, FLinearColor(0.36f, 0.27f, 0.10f, 0.95f));
			Frame(R0, R1, Gold, 2.f * Sc);
		}
		float Ix = 0.f;
		const FName Ic = ItemIcon(FName(*P[1]));
		if (UI.Has(Ic)) { Ix = Rh; UI.Fit(Ic, FVector2D(R0.X + 8.f * Sc, R0.Y - 2.f * Sc), FVector2D(R0.X + 4.f * Sc + Rh, R1.Y + 2.f * Sc)); }
		UI.Text(P[1], bOn ? FLinearColor::White : FLinearColor(0.86f, 0.84f, 0.78f), R0.X + 12.f * Sc + Ix, R0.Y + 8.f * Sc, Small, Sc * 1.15f);
		const FString Tag = bCan ? TEXT("CAN MAKE") : FString::Printf(TEXT("x %d"), Cb->GetItemCount(FName(*P[1])));
		UI.TextSize(Tag, Tw, Th, Small, Sc, ERDType::Label);
		UI.Text(Tag, bCan ? Have : Dim, R1.X - 12.f * Sc - Tw, R0.Y + 10.f * Sc, Small, Sc, ERDType::Label);
		Y += Rh;
	}
	// ---- the chosen recipe
	const float Rx = A.X + W * 0.42f + Pd, Rw = W * 0.58f - Pd * 2.f;
	float Ry = A.Y + 80.f * Sc;
	Box(FVector2D(Rx - Pd * 0.5f, Ry), FVector2D(Rx - Pd * 0.5f + 1.f, B.Y - 110.f * Sc), FLinearColor(0.75f, 0.65f, 0.45f, 0.4f));
	if (Lines.Num() > Fit)
		UI.Text(FString::Printf(TEXT("%d more above,  %d more below"), First, Lines.Num() - First - Fit), Dim, Lx + 12.f * Sc, Y + 6.f * Sc, Small, Sc * 0.95f);
	if (Parsed.IsValidIndex(Cur) && Parsed[Cur].Num() >= 5 && Parsed[Cur][0] == TEXT("breakdown"))
	{
		// (level 5: a weapon to break down: what it gives, against what she carries)
		const TArray<FString>& P = Parsed[Cur];
		const FName Ic = P[2].StartsWith(TEXT("w")) ? WeaponIcon(FCString::Atoi(*P[2].Mid(1))) : ItemIcon(FName(*P[2].Mid(1)));
		if (UI.Has(Ic))
		{
			const float Sz = 104.f * Sc;
			UI.Fit(TEXT("slot"), FVector2D(Rx, Ry), FVector2D(Rx + Sz, Ry + Sz));
			UI.Fit(Ic, FVector2D(Rx + 16.f * Sc, Ry + 14.f * Sc), FVector2D(Rx + Sz - 16.f * Sc, Ry + Sz - 14.f * Sc));
			float Nw, Nh, Nk = Sc * 1.1f;
			UI.TextSize(P[1].ToUpper(), Nw, Nh, Medium, Nk, ERDType::Title);
			if (Nw > Rw - Sz - 20.f * Sc) Nk *= FMath::Max((Rw - Sz - 20.f * Sc) / Nw, 0.55f);
			UI.Text(P[1].ToUpper(), FLinearColor::White, Rx + Sz + 16.f * Sc, Ry + Sz * 0.5f - 16.f * Sc, Medium, Nk, ERDType::Title);
			Ry += Sz + 12.f * Sc;
		}
		else { UI.Text(P[1].ToUpper(), FLinearColor::White, Rx, Ry, Medium, Sc * 1.1f, ERDType::Title); Ry += 40.f * Sc; }
		UI.Text(TEXT("IT BREAKS DOWN INTO"), Dim, Rx, Ry, Small, Sc, ERDType::Label); Ry += 24.f * Sc;
		TArray<FString> Gives; P[4].ParseIntoArray(Gives, TEXT(";"));
		for (const FString& G : Gives)
		{
			FString Nm, Ct;
			if (!G.Split(TEXT(":"), &Nm, &Ct)) continue;
			UI.Text(FString::Printf(TEXT("%s  x %s"), *Nm, *Ct), FLinearColor(0.86f, 0.84f, 0.78f), Rx, Ry, Small, Sc);
			const FString Hv = FString::Printf(TEXT("you have %d"), Cb->GetItemCount(FName(*Nm)));
			UI.TextSize(Hv, Tw, Th, Small, Sc * 0.95f);
			UI.Text(Hv, Dim, Rx + Rw - 16.f * Sc - Tw, Ry + 1.f * Sc, Small, Sc * 0.95f);
			Ry += 27.f * Sc;
		}
		Ry += 12.f * Sc;
		const bool bDrawn = P[3] == TEXT("1");
		UI.Text(bDrawn ? TEXT("It is in your hands: draw another weapon first") : (bPad ? TEXT("A  break it down (it is gone)") : TEXT("Enter  break it down (it is gone)")),
		        bDrawn ? Dim : Gold, Rx, Ry, Small, Sc * 1.05f);
	}
	else if (Parsed.IsValidIndex(Cur) && Parsed[Cur].Num() >= 3)
	{
		const TArray<FString>& P = Parsed[Cur];
		const FName Item(*P[1]);
		const FName Ic = ItemIcon(Item);
		if (UI.Has(Ic))
		{
			const float Sz = 104.f * Sc;
			UI.Fit(TEXT("slot"), FVector2D(Rx, Ry), FVector2D(Rx + Sz, Ry + Sz));
			UI.Fit(Ic, FVector2D(Rx + 16.f * Sc, Ry + 14.f * Sc), FVector2D(Rx + Sz - 16.f * Sc, Ry + Sz - 14.f * Sc));
			UI.Text(P[1].ToUpper(), FLinearColor::White, Rx + Sz + 16.f * Sc, Ry + Sz * 0.5f - 16.f * Sc, Medium, Sc * 1.15f, ERDType::Title);
			Ry += Sz + 12.f * Sc;
		}
		else { UI.Text(P[1].ToUpper(), FLinearColor::White, Rx, Ry, Medium, Sc * 1.15f, ERDType::Title); Ry += 40.f * Sc; }
		const int32 Ix = Gen->FindItem(Item);
		if (Ix >= 0) { UI.Text(FString::Printf(TEXT("Mends %.0f%% of a set of armour's or a found weapon's durability"), Gen->Items[Ix].Amount * 100.f), RDInk, Rx, Ry, Small, Sc * 1.05f); Ry += 30.f * Sc; }
		UI.Text(TEXT("IT TAKES"), Dim, Rx, Ry, Small, Sc, ERDType::Label); Ry += 24.f * Sc;
		TArray<FString> Parts; if (P.Num() >= 4) P[3].ParseIntoArray(Parts, TEXT(";"));
		// (two columns of parts: label, what she has / what it takes, green when she has enough)
		const float Cw = Rw * 0.5f;
		for (int32 K = 0; K < Parts.Num(); ++K)
		{
			TArray<FString> Q; Parts[K].ParseIntoArray(Q, TEXT(":"), false);
			if (Q.Num() < 3) continue;
			const int32 Hv = FCString::Atoi(*Q[1]), Nd = FCString::Atoi(*Q[2]);
			const float Px = Rx + (K % 2) * Cw, Py = Ry + (K / 2) * 27.f * Sc;
			UI.Text(Q[0], FLinearColor(0.86f, 0.84f, 0.78f), Px, Py, Small, Sc * 1.0f);
			const FString N = FString::Printf(TEXT("%d / %d"), Hv, Nd);
			UI.TextSize(N, Tw, Th, Small, Sc, ERDType::Label);
			UI.Text(N, Hv >= Nd ? Have : Lack, Px + Cw - 16.f * Sc - Tw, Py + 1.f * Sc, Small, Sc, ERDType::Label);
		}
		Ry += ((Parts.Num() + 1) / 2) * 27.f * Sc + 14.f * Sc;
		UI.Text(P[2] == TEXT("1") ? (bPad ? TEXT("A  make it") : TEXT("Enter  make it")) : TEXT("You lack some of what it takes: the containers hold materials"),
		        P[2] == TEXT("1") ? Gold : Dim, Rx, Ry, Small, Sc * 1.05f);
	}
	const float Fy = B.Y - 92.f * Sc;
	if (bDivider) UI.Fit(TEXT("divider"), FVector2D(A.X + Pd, Fy - 20.f * Sc), FVector2D(B.X - Pd, Fy + 20.f * Sc));
	if (Cb->MessageTime > -50.f && !Cb->Message.IsEmpty()) UI.Text(Cb->Message, FLinearColor(1.f, 0.93f, 0.75f), A.X + Pd + Tin, Fy + 14.f * Sc, Small, Sc * 1.15f);
	const FString Keys = bPad ? TEXT("D-pad / left stick  select      A  make it / break it down      B or X  close")
	                          : TEXT("W S / arrows / wheel  select      Enter or E  make it / break it down      F, Backspace or Tab  close");
	UI.Text(Keys, Dim, A.X + Pd + Tin, Fy + 50.f * Sc, Small, Sc * 1.05f);
}

// ------------------------------------------------------------------------------------------------ level 5: the bar, the menu
void ARDHUD::DrawHotbar(float Sc)
{
	URDCombatComponent* Cb = Gen->GetPlayerCombat();
	if (!Cb || Cb->IsInventoryOpen() || Cb->IsCraftingOpen()) return;
	UFont* Small = GEngine->GetSmallFont();
	const int32 N = FMath::Min(Gen->Weapons.Num(), 10);
	if (N <= 0) return;
	const float S = 64.f * Sc, Gp = 8.f * Sc, W = N * S + (N - 1) * Gp;
	const float X0 = (Canvas->ClipX - W) * 0.5f, Y0 = Canvas->ClipY - S - 26.f * Sc;
	const bool bSlot = UI.Has(TEXT("slot"));
	float Tw, Th;
	for (int32 I = 0; I < N; ++I)
	{
		const FRDWeaponDef& Wp = Gen->Weapons[I];
		const bool bOn = Wp.bAlongside ? Cb->GetAttackIndex() == I : I == Cb->GetWeaponIndex();
		const FVector2D A(X0 + I * (S + Gp), Y0), B = A + FVector2D(S);
		const float Cd = Cb->GetCooldownLeft(I);
		const bool bNoMana = Wp.ManaCost > 0.f && Cb->GetMana() < Wp.ManaCost;
		if (bSlot)
		{
			const FRDUIArt* Sa = UI.Find(TEXT("slot"));
			UI.Nine(TEXT("slot"), A, B, 12.f * Sc / FMath::Max((float)Sa->Border.X * Sa->Texture->GetSizeX(), 1.f), bOn ? FLinearColor(1.15f, 1.05f, 0.85f) : FLinearColor(0.62f, 0.62f, 0.62f));
		}
		else Box(A, B, FLinearColor(0.06f, 0.06f, 0.08f, 0.85f));
		const FName Ic = WeaponIcon(I);
		const FLinearColor Tint = bNoMana ? FLinearColor(1.f, 0.45f, 0.4f) : (bOn ? FLinearColor::White : FLinearColor(0.75f, 0.75f, 0.75f));
		if (UI.Has(Ic)) UI.Fit(Ic, A + FVector2D(8.f * Sc), B - FVector2D(8.f * Sc), Tint);
		else
		{
			// (no picture: the first letters of its name)
			TArray<FString> Ws; Wp.Name.ToString().ParseIntoArray(Ws, TEXT(" "));
			FString Ab; for (const FString& Wd : Ws) if (Wd.Len() > 0 && Ab.Len() < 3) Ab += Wd.Left(1).ToUpper();
			UI.TextSize(Ab, Tw, Th, Small, Sc * 1.4f, ERDType::Title);
			UI.Text(Ab, Tint, (A.X + B.X - Tw) * 0.5f, (A.Y + B.Y - Th) * 0.5f, Small, Sc * 1.4f, ERDType::Title);
		}
		// (a cooldown: the slot darkened from the top by the share still to wait, and the seconds)
		if (Cd > 0.f && Wp.Cooldown > 0.f)
		{
			const float F = FMath::Clamp(Cd / Wp.Cooldown, 0.f, 1.f);
			Box(A, FVector2D(B.X, A.Y + (B.Y - A.Y) * F), FLinearColor(0.f, 0.f, 0.f, 0.62f));
			const FString T = FString::Printf(TEXT("%.0f"), FMath::CeilToFloat(Cd));
			UI.TextSize(T, Tw, Th, Small, Sc * 1.3f, ERDType::Title);
			UI.Text(T, FLinearColor(1.f, 0.9f, 0.6f), (A.X + B.X - Tw) * 0.5f, (A.Y + B.Y - Th) * 0.5f, Small, Sc * 1.3f, ERDType::Title);
		}
		if (bOn) Frame(A + FVector2D(1.f), B - FVector2D(1.f), FLinearColor(1.f, 0.82f, 0.35f, 0.95f), 2.5f * Sc);
		const FString Key = Wp.bAlongside ? FString(TEXT("E")) : FString::Printf(TEXT("%d"), (I + 1) % 10);
		UI.Text(Key, FLinearColor(1.f, 0.82f, 0.35f), A.X + 5.f * Sc, A.Y + 2.f * Sc, Small, Sc * 0.95f, ERDType::Title);
		if (Wp.ManaCost > 0.f)
		{
			const FString Mc = FString::Printf(TEXT("%.0f"), Wp.ManaCost);
			UI.TextSize(Mc, Tw, Th, Small, Sc * 0.85f);
			UI.Text(Mc, bNoMana ? FLinearColor(1.f, 0.4f, 0.35f) : FLinearColor(0.6f, 0.75f, 1.f), B.X - Tw - 5.f * Sc, B.Y - Th - 2.f * Sc, Small, Sc * 0.85f);
		}
	}
	// (the one in her hands, by name over the bar; how many more the wheel reaches)
	if (Gen->Weapons.IsValidIndex(Cb->GetWeaponIndex()))
	{
		FString T = Gen->Weapons[Cb->GetWeaponIndex()].Name.ToString().ToUpper();
		if (Gen->Weapons.Num() > 10) T += FString::Printf(TEXT("    (%d more: the wheel)"), Gen->Weapons.Num() - 10);
		UI.TextSize(T, Tw, Th, Small, Sc * 1.05f, ERDType::Label);
		UI.Text(T, RDInk, (Canvas->ClipX - Tw) * 0.5f, Y0 - Th - 4.f * Sc, Small, Sc * 1.05f, ERDType::Label);
	}
}

void ARDHUD::DrawMenu(float Sc)
{
	UFont* Small = GEngine->GetSmallFont();
	UFont* Medium = GEngine->GetMediumFont();
	const FLinearColor Gold(1.f, 0.82f, 0.35f), Dim(0.70f, 0.68f, 0.62f);
	Box(FVector2D(0, 0), FVector2D(Canvas->ClipX, Canvas->ClipY), FLinearColor(0.f, 0.f, 0.01f, 0.62f));
	const TArray<FString> Lines = Gen->GetMenuLines();
	const float W = 760.f * Sc, Rh = 58.f * Sc, Pd = 34.f * Sc;
	const float H = 120.f * Sc + Rh * Lines.Num() + 26.f * Sc + 70.f * Sc;
	const FVector2D A((Canvas->ClipX - W) * 0.5f, (Canvas->ClipY - H) * 0.5f), B = A + FVector2D(W, H);
	if (!Board(TEXT("panel_wide"), A, B, Sc, 44.f * Sc))
	{
		Box(A, B, FLinearColor(0.035f, 0.04f, 0.055f, 0.95f));
		Frame(A, B, FLinearColor(0.75f, 0.65f, 0.45f, 0.9f), 2.f * Sc);
	}
	float Tw, Th;
	UI.TextSize(TEXT("PAUSED"), Tw, Th, Medium, Sc * 1.6f, ERDType::Title);
	UI.Text(TEXT("PAUSED"), RDInk, (A.X + B.X - Tw) * 0.5f, A.Y + 22.f * Sc, Medium, Sc * 1.6f, ERDType::Title);
	Gen->MenuRowBoxes.Reset(); Gen->MenuTrackBoxes.Reset();
	const bool bPlate = UI.Has(TEXT("button"));
	float Y = A.Y + 100.f * Sc;
	for (int32 I = 0; I < Lines.Num(); ++I)
	{
		TArray<FString> P; Lines[I].ParseIntoArray(P, TEXT("|"));
		if (P.Num() < 2) continue;
		const bool bOn = I == Gen->GetMenuCursor();
		if (I == 4) Y += 26.f * Sc;           // (the buttons below the sliders)
		const FVector2D R0(A.X + Pd, Y), R1(B.X - Pd, Y + Rh - 10.f * Sc);
		Gen->MenuRowBoxes.Add(FBox2D(R0, R1));
		if (bOn)
		{
			const FRDUIArt* Pl = UI.Find(TEXT("button"));
			if (bPlate) UI.Nine(TEXT("button"), R0 - FVector2D(4.f * Sc), R1 + FVector2D(4.f * Sc), (R1.Y - R0.Y + 8.f * Sc) / FMath::Max((float)Pl->Texture->GetSizeY(), 1.f), FLinearColor(1.25f, 1.05f, 0.7f));
			else Box(R0, R1, FLinearColor(0.36f, 0.27f, 0.10f, 0.95f));
			Frame(R0, R1, Gold, 2.f * Sc);
		}
		if (P[0] == TEXT("volume") && P.Num() >= 3)
		{
			// a slider: its label, the track, the knob, the value
			const float V = FCString::Atof(*P[2]);
			UI.Text(P[1], bOn ? FLinearColor::White : FLinearColor(0.86f, 0.84f, 0.78f), R0.X + 14.f * Sc, R0.Y + 12.f * Sc, Small, Sc * 1.2f);
			const FVector2D T0(R0.X + 300.f * Sc, (R0.Y + R1.Y) * 0.5f - 4.f * Sc), T1(R1.X - 90.f * Sc, (R0.Y + R1.Y) * 0.5f + 4.f * Sc);
			Gen->MenuTrackBoxes.Add(FBox2D(T0, T1));
			Box(T0, T1, FLinearColor(0.08f, 0.08f, 0.10f, 0.95f));
			Box(T0, FVector2D(FMath::Lerp(T0.X, T1.X, V), T1.Y), FLinearColor(0.85f, 0.62f, 0.25f));
			Frame(T0, T1, FLinearColor(0.75f, 0.65f, 0.45f, 0.9f), 1.f * Sc);
			const float Kx = FMath::Lerp(T0.X, T1.X, V);
			Box(FVector2D(Kx - 7.f * Sc, T0.Y - 9.f * Sc), FVector2D(Kx + 7.f * Sc, T1.Y + 9.f * Sc), bOn ? Gold : FLinearColor(0.85f, 0.82f, 0.75f));
			const FString Pc = FString::Printf(TEXT("%.0f%%"), V * 100.f);
			UI.TextSize(Pc, Tw, Th, Small, Sc * 1.15f, ERDType::Label);
			UI.Text(Pc, bOn ? Gold : Dim, R1.X - 14.f * Sc - Tw, R0.Y + 13.f * Sc, Small, Sc * 1.15f, ERDType::Label);
		}
		else
		{
			Gen->MenuTrackBoxes.Add(FBox2D(ForceInit));
			const FString T = P[1].ToUpper();
			UI.TextSize(T, Tw, Th, Small, Sc * 1.3f, ERDType::Title);
			UI.Text(T, bOn ? FLinearColor::White : FLinearColor(0.86f, 0.84f, 0.78f), (R0.X + R1.X - Tw) * 0.5f, R0.Y + 11.f * Sc, Small, Sc * 1.3f, ERDType::Title);
		}
		Y += Rh;
	}
	const FString Keys = TEXT("W S  choose      A D  volume      Enter  press      mouse  click or drag      Esc  back to the game");
	UI.TextSize(Keys, Tw, Th, Small, Sc);
	UI.Text(Keys, Dim, (A.X + B.X - Tw) * 0.5f, B.Y - 48.f * Sc, Small, Sc);
}
