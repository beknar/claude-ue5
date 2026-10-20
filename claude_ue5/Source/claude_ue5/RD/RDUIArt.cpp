#include "RDUIArt.h"
#include "GameFramework/HUD.h"
#include "Engine/Texture2D.h"
#include "Engine/Font.h"
#include "Engine/FontFace.h"
#include "Fonts/CompositeFont.h"

// (a label in small capitals: each word of three letters or more that is written in capitals keeps its first and lowers
// the rest, which the small-capitals face draws as small capitals; "HP", "N" and the numbers stay as they are)
static FString RDUISmallCaps(const FString& S)
{
	FString O = S;
	int32 I = 0;
	while (I < O.Len())
	{
		int32 J = I;
		while (J < O.Len() && FChar::IsAlpha(O[J])) ++J;
		if (J - I >= 3)
		{
			bool bUpper = true;
			for (int32 K = I; K < J; ++K) bUpper &= FChar::IsUpper(O[K]);
			if (bUpper) for (int32 K = I + 1; K < J; ++K) O[K] = FChar::ToLower(O[K]);
		}
		I = FMath::Max(J, I + 1);
		while (I < O.Len() && !FChar::IsAlpha(O[I])) ++I;
	}
	return O;
}

UFont* FRDUIDraw::Pick(UFont* Engine, float K, ERDType Role, float& OutK, FString& InOutS, float& OutRaise) const
{
	OutK = K; OutRaise = 0.f;
	if (!Fonts || !FontCache || !Engine || !Hud) return Engine;
	static const FName Names[3] = { FName(TEXT("text")), FName(TEXT("label")), FName(TEXT("title")) };
	const FRDUIFont* F = Fonts->Find(Names[(int32)Role]);
	if (!F || !F->Face) return Engine;
	// (the tests read what was drawn: "font_title" and so on, as the pieces)
	static const FName Notes[3] = { FName(TEXT("font_text")), FName(TEXT("font_label")), FName(TEXT("font_title")) };
	Note(Notes[(int32)Role]);
	if (Role == ERDType::Label) InOutS = RDUISmallCaps(InOutS);
	// (the size the engine font would have at K, in this face's points)
	const float Want = (float)FMath::Max(Engine->LegacyFontSize, 1) * K * FMath::Max(F->Size, 0.1f);
	const int32 Pt = FMath::Clamp(FMath::RoundToInt(Want), 4, 160);
	TObjectPtr<UFont>& Ft = FontCache->FindOrAdd((int32)Role * 1000 + Pt);
	if (!Ft)
	{
		UFont* N = NewObject<UFont>(Hud);
		N->FontCacheType = EFontCacheType::Runtime;
		N->LegacyFontSize = Pt;
		FTypefaceEntry E(TEXT("Regular"));
		E.Font = FFontData(F->Face.Get());
		N->GetMutableInternalCompositeFont().DefaultTypeface.Fonts.Add(E);
		Ft = N;
	}
	OutK = Want / (float)Pt;
	// (the engine font's em in pixels at K: a font's points are pixels at 96 dots an inch)
	OutRaise = F->Lift * (float)FMath::Max(Engine->LegacyFontSize, 1) * K * (96.f / 72.f);
	return Ft;
}

void FRDUIDraw::Text(const FString& S, const FLinearColor& C, float X, float Y, UFont* Engine, float K, ERDType Role) const
{
	if (!Hud) return;
	FString T = S; float Kd, Up;
	UFont* F = Pick(Engine, K, Role, Kd, T, Up);
	Hud->DrawText(T, C, X, Y - Up, F, Kd);
}

void FRDUIDraw::TextSize(const FString& S, float& OutW, float& OutH, UFont* Engine, float K, ERDType Role) const
{
	OutW = OutH = 0.f;
	if (!Hud) return;
	FString T = S; float Kd, Up;
	UFont* F = Pick(Engine, K, Role, Kd, T, Up);
	Hud->GetTextSize(T, OutW, OutH, F, Kd);
	// (the line as tall as the engine font's: the layouts were made for it, and Lift puts the capitals where its are)
	if (F != Engine) { float Ew; Hud->GetTextSize(S, Ew, OutH, Engine, K); }
}

const FRDUIArt* FRDUIDraw::Find(FName Name) const
{
	if (!Art || Name.IsNone()) return nullptr;
	const FRDUIArt* A = Art->Find(Name);
	return A && A->Texture ? A : nullptr;
}

void FRDUIDraw::Tile(UTexture2D* T, float X, float Y, float W, float H, float U, float V, float UW, float VH, const FLinearColor& Tint) const
{
	if (W <= 0.f || H <= 0.f) return;
	Hud->DrawTexture(T, X, Y, W, H, U, V, UW, VH, Tint, BLEND_Translucent);
}

// (the border's screen sizes for a piece stretched to A..B: the picture's border at Px, shrunk if the box is too small)
static void RDUINineSizes(const FRDUIArt& Ar, const FVector2D& A, const FVector2D& B, float Px, float& L, float& T, float& R, float& Bo)
{
	const float Tw = Ar.Texture->GetSizeX(), Th = Ar.Texture->GetSizeY();
	L = (float)Ar.Border.X * Tw * Px; T = (float)Ar.Border.Y * Th * Px; R = (float)Ar.Border.Z * Tw * Px; Bo = (float)Ar.Border.W * Th * Px;
	const float W = (float)(B.X - A.X), H = (float)(B.Y - A.Y);
	if (L + R > W * 0.98f && L + R > 0.f) { const float K = W * 0.98f / (L + R); L *= K; R *= K; }
	if (T + Bo > H * 0.98f && T + Bo > 0.f) { const float K = H * 0.98f / (T + Bo); T *= K; Bo *= K; }
}

bool FRDUIDraw::Nine(FName Name, const FVector2D& A, const FVector2D& B, float Px, const FLinearColor& Tint) const
{
	const FRDUIArt* Ar = Find(Name);
	if (!Ar || B.X <= A.X || B.Y <= A.Y) return false;
	float L, T, R, Bo;
	RDUINineSizes(*Ar, A, B, Px, L, T, R, Bo);
	const float Xs[4] = { (float)A.X, (float)A.X + L, (float)B.X - R, (float)B.X };
	const float Ys[4] = { (float)A.Y, (float)A.Y + T, (float)B.Y - Bo, (float)B.Y };
	const float Us[4] = { 0.f, (float)Ar->Border.X, 1.f - (float)Ar->Border.Z, 1.f };
	const float Vs[4] = { 0.f, (float)Ar->Border.Y, 1.f - (float)Ar->Border.W, 1.f };
	for (int32 J = 0; J < 3; ++J)
		for (int32 I = 0; I < 3; ++I)
			Tile(Ar->Texture, Xs[I], Ys[J], Xs[I + 1] - Xs[I], Ys[J + 1] - Ys[J], Us[I], Vs[J], Us[I + 1] - Us[I], Vs[J + 1] - Vs[J], Tint);
	Note(Name);
	return true;
}

bool FRDUIDraw::FitBox(FName Name, const FVector2D& A, const FVector2D& B, FVector2D& OutA, FVector2D& OutB) const
{
	const FRDUIArt* Ar = Find(Name);
	if (!Ar) return false;
	const float Tw = Ar->Texture->GetSizeX(), Th = Ar->Texture->GetSizeY();
	const float W = (float)(B.X - A.X), H = (float)(B.Y - A.Y), K = FMath::Min(W / FMath::Max(Tw, 1.f), H / FMath::Max(Th, 1.f));
	const FVector2D S(Tw * K, Th * K), C = (A + B) * 0.5;
	OutA = C - S * 0.5f; OutB = C + S * 0.5f;
	return true;
}

bool FRDUIDraw::Fit(FName Name, const FVector2D& A, const FVector2D& B, const FLinearColor& Tint, bool bFlipX) const
{
	FVector2D P0, P1;
	if (!FitBox(Name, A, B, P0, P1)) return false;
	const FRDUIArt* Ar = Find(Name);
	Tile(Ar->Texture, (float)P0.X, (float)P0.Y, (float)(P1.X - P0.X), (float)(P1.Y - P0.Y), bFlipX ? 1.f : 0.f, 0.f, bFlipX ? -1.f : 1.f, 1.f, Tint);
	Note(Name);
	return true;
}

void FRDUIDraw::InnerBox(FName Frame, const FVector2D& A, const FVector2D& B, float Px, FVector2D& OutA, FVector2D& OutB) const
{
	OutA = A; OutB = B;
	const FRDUIArt* Ar = Find(Frame);
	if (!Ar) return;
	float L, T, R, Bo;
	RDUINineSizes(*Ar, A, B, Px, L, T, R, Bo);
	// a share of the picture to the screen, through the stretch (the borders at their size, the middle stretched)
	auto Map = [](float S, float S0, float S1, float P0, float P1, float N0, float N1)
	{
		if (S <= S0) return P0 + (S0 > 0.f ? S / S0 : 0.f) * N0;
		if (S >= 1.f - S1) return P1 - (S1 > 0.f ? (1.f - S) / S1 : 0.f) * N1;
		const float M = 1.f - S0 - S1;
		return (P0 + N0) + (M > 0.f ? (S - S0) / M : 0.f) * ((P1 - N1) - (P0 + N0));
	};
	const FVector4f In(Ar->Inner), Bd(Ar->Border);
	const float Ax = (float)A.X, Ay = (float)A.Y, Bx = (float)B.X, By = (float)B.Y;
	OutA = FVector2D(Map(In.X, Bd.X, Bd.Z, Ax, Bx, L, R), Map(In.Y, Bd.Y, Bd.W, Ay, By, T, Bo));
	OutB = FVector2D(Map(In.Z, Bd.X, Bd.Z, Ax, Bx, L, R), Map(In.W, Bd.Y, Bd.W, Ay, By, T, Bo));
}

bool FRDUIDraw::Bar(FName Frame, FName Fill, const FVector2D& A, const FVector2D& B, float Px, float Fraction, const FLinearColor& FillTint, const FLinearColor& FrameTint) const
{
	if (!Has(Frame)) return false;
	FVector2D I0, I1;
	InnerBox(Frame, A, B, Px, I0, I1);
	// the empty part dark, then the fill, then the frame over both
	const float X0 = (float)I0.X, Y0 = (float)I0.Y, W = (float)(I1.X - I0.X), H = (float)(I1.Y - I0.Y);
	Hud->DrawRect(FLinearColor(0.015f, 0.012f, 0.012f, 0.92f), X0, Y0, W, H);
	const float F = FMath::Clamp(Fraction, 0.f, 1.f);
	if (const FRDUIArt* Fa = Find(Fill))
	{
		Tile(Fa->Texture, X0, Y0, W * F, H, 0.f, 0.f, F, 1.f, FillTint);
		Note(Fill);
	}
	else if (F > 0.f) Hud->DrawRect(FillTint, X0, Y0, W * F, H);
	return Nine(Frame, A, B, Px, FrameTint);
}
