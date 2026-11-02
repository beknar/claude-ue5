// Brokenspire (docs/brokenspire.txt): the town's side of ARDHUD.
//   - the minimap: as the dungeon's (dark tiles under bright marks, a feathered rim): the ground, the streets lighter, the
//     buildings' floors with their walls lit, the trades' little pictures, the people with quests, the guards
//   - the big map (M): a sheet of papyrus with the town drawn on it in ink, every building as its picture (painted: the
//     generator's UIArt "mapicon_<kind>") and what the trades do written under them
//   - the town's panel (talk, the trader, the healer, the smith, the temple, the storage, the circle, the board)
//   - the names over the townspeople near her (a gold "!" over one with a quest for her, "?" when one is done)
//   - her purse and her quests on the right (the town and the castle)
#include "RD/RDHUD.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDCombat.h"
#include "RD/RDMonster.h"
#include "RD/RDTown.h"
#include "RD/RDGameInstance.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "GameFramework/PlayerController.h"
#include "Camera/PlayerCameraManager.h"

static const FLinearColor RDTInk(0.93f, 0.89f, 0.78f, 1.f);
static const FLinearColor RDTGold(1.f, 0.82f, 0.35f, 1.f);
static const FLinearColor RDTDim(0.70f, 0.68f, 0.62f, 1.f);
static const FLinearColor RDTSepia(0.30f, 0.19f, 0.09f, 1.f);
static FLinearColor RDTA(const FLinearColor& C, float A) { return FLinearColor(C.R, C.G, C.B, C.A * A); }

static FName RDTIconOf(uint8 Kind, uint8 State)
{
	switch (Kind)
	{
	case TK_Castle: return TEXT("mapicon_castle");
	case TK_Smithy: return TEXT("mapicon_smithy");
	case TK_Store: return TEXT("mapicon_store");
	case TK_Healer: return TEXT("mapicon_healer");
	case TK_Temple: return TEXT("mapicon_temple");
	case TK_Storehouse: return TEXT("mapicon_storehouse");
	case TK_Tavern: return TEXT("mapicon_tavern");
	case TK_Chapel: return TEXT("mapicon_chapel");
	case TK_Barracks: return TEXT("mapicon_barracks");
	case TK_Witch: return TEXT("mapicon_witch");
	default: return State == 1 ? FName(TEXT("mapicon_burned")) : State == 2 ? FName(TEXT("mapicon_boarded")) : FName(TEXT("mapicon_home"));
	}
}

/** what the map writes under a building's picture (empty: nothing, the homes) */
static FString RDTLabelOf(uint8 Kind)
{
	switch (Kind)
	{
	case TK_Castle: return TEXT("MISTWARD CASTLE · into the dungeon");
	case TK_Smithy: return TEXT("SMITHY · repairs, the anvil");
	case TK_Store: return TEXT("TRADER · buy and sell");
	case TK_Healer: return TEXT("HEALER · healing");
	case TK_Temple: return TEXT("TEMPLE · blessings");
	case TK_Storehouse: return TEXT("STOREHOUSE · your storage");
	case TK_Tavern: return TEXT("TAVERN");
	case TK_Chapel: return TEXT("CHAPEL");
	case TK_Barracks: return TEXT("BARRACKS");
	case TK_Witch: return TEXT("WITCH'S HUT");
	default: return FString();
	}
}

TArray<FString> ARDHUD::WrapText(const FString& S, float W, UFont* F, float K) const
{
	TArray<FString> Out;
	TArray<FString> Paras; S.ParseIntoArray(Paras, TEXT("\n"), false);
	for (const FString& P : Paras)
	{
		TArray<FString> Words; P.ParseIntoArray(Words, TEXT(" "), true);
		FString Line;
		for (const FString& Wd : Words)
		{
			const FString Try = Line.IsEmpty() ? Wd : Line + TEXT(" ") + Wd;
			float Tw, Th; UI.TextSize(Try, Tw, Th, F, K);
			if (Tw > W && !Line.IsEmpty()) { Out.Add(Line); Line = Wd; }
			else Line = Try;
		}
		Out.Add(Line);
	}
	return Out;
}

void ARDHUD::CacheTownGrid()
{
	const ARDSection* S = Gen->GetSection(FIntPoint::ZeroValue);
	if (!S) return;
	if (TownGridSeed == S->Seed && TownGrid.Num() > 0) return;
	const int32 N = S->GetTownTiles();
	TownGridN = N; TownGridSeed = S->Seed; TownGridMin = S->GetSectionMin();
	TownGrid.Init(-1, N * N);
	for (int32 X = 0; X < N; ++X) for (int32 Y = 0; Y < N; ++Y) if (S->TownTileType(FIntPoint(X, Y)) == 2) TownGrid[Y * N + X] = -2;
	for (const FIntRect& R : S->TownRoads) for (int32 X = R.Min.X; X < R.Max.X; ++X) for (int32 Y = R.Min.Y; Y < R.Max.Y; ++Y) if (X >= 0 && Y >= 0 && X < N && Y < N && TownGrid[Y * N + X] == -2) TownGrid[Y * N + X] = -3;
	for (int32 X = S->TownSquare.Min.X; X < S->TownSquare.Max.X; ++X) for (int32 Y = S->TownSquare.Min.Y; Y < S->TownSquare.Max.Y; ++Y) if (X >= 0 && Y >= 0 && X < N && Y < N && TownGrid[Y * N + X] == -2) TownGrid[Y * N + X] = -3;
	for (int32 BI = 0; BI < S->TownBlds.Num(); ++BI)
	{
		const ARDSection::FTownBld& B = S->TownBlds[BI];
		for (int32 X = B.Min.X; X < B.Max.X; ++X) for (int32 Y = B.Min.Y; Y < B.Max.Y; ++Y) if (X >= 0 && Y >= 0 && X < N && Y < N) TownGrid[Y * N + X] = (int16)BI;
	}
}

// ------------------------------------------------------------------------------------------------ the minimap
void ARDHUD::DrawTownMinimap(float Sc, const FVector& L, float Yaw)
{
	UFont* Small = GEngine->GetSmallFont();
	const ARDSection* S = Gen->GetSection(FIntPoint::ZeroValue);
	if (!S) return;
	CacheTownGrid();
	const float R = MinimapPixels * Sc * 0.5f, Mg = 24.f * Sc;
	const FRDUIArt* Ra = UI.Find(TEXT("minimap_ring"));
	const float Ring = Ra ? R * 1.03f / FMath::Max((float)(Ra->Inner.Z - Ra->Inner.X), 0.2f) : R;
	const FVector2D C(Canvas->ClipX - Mg - Ring, Mg + (Ra ? 0.f : 14.f * Sc) + Ring);
	const float Half = StylizedMinimapMeters * 50.f * 1.25f, K = R / Half, TS = Gen->TileSize, Tp = TS * K;
	auto ToS = [&](const FVector2D& W) { return C + FVector2D(W.Y - L.Y, -(W.X - L.X)) * K; };
	auto Fade = [&](const FVector2D& P) { return FMath::Clamp((1.f - FVector2D::Distance(P, C) / R) / 0.38f, 0.f, 1.f); };
	if (UTexture2D* T = GetSoftDisc()) DrawTexture(T, C.X - R * 1.3f, C.Y - R * 1.3f, R * 2.6f, R * 2.6f, 0.f, 0.f, 1.f, 1.f, FLinearColor(0.004f, 0.005f, 0.007f, 0.92f), BLEND_Translucent);
	{
		const FString Title = Gen->TownName.ToUpper();
		float Tw0, Th0; UI.TextSize(Title, Tw0, Th0, Small, Sc * 1.1f, ERDType::Title);
		UI.Text(Title, FLinearColor(0.f, 0.f, 0.f, 0.8f), C.X - Tw0 * 0.5f + 1.5f * Sc, C.Y - Ring - Th0 - 2.f * Sc + 1.5f * Sc, Small, Sc * 1.1f, ERDType::Title);
		UI.Text(Title, FLinearColor(1.f, 0.84f, 0.5f, 1.f), C.X - Tw0 * 0.5f, C.Y - Ring - Th0 - 2.f * Sc, Small, Sc * 1.1f, ERDType::Title);
	}
	const int32 N = TownGridN;
	auto At = [&](int32 X, int32 Y) -> int16 { return X >= 0 && Y >= 0 && X < N && Y < N ? TownGrid[Y * N + X] : -1; };
	const FIntPoint Here((int32)FMath::FloorToFloat((L.X - TownGridMin.X) / TS), (int32)FMath::FloorToFloat((L.Y - TownGridMin.Y) / TS));
	const int32 Rt = FMath::CeilToInt(Half / TS) + 1;
	const FLinearColor Ground(0.13f, 0.14f, 0.12f, 0.95f), Road(0.22f, 0.21f, 0.18f, 0.95f), Floor(0.075f, 0.07f, 0.065f, 0.95f), Wall(0.62f, 0.58f, 0.5f, 0.95f), Void(0.03f, 0.035f, 0.03f, 0.8f);
	for (int32 X = Here.X - Rt; X <= Here.X + Rt; ++X)
		for (int32 Y = Here.Y - Rt; Y <= Here.Y + Rt; ++Y)
		{
			const int16 V = At(X, Y);
			const FVector2D W0(TownGridMin.X + X * TS, TownGridMin.Y + Y * TS), W1 = W0 + FVector2D(TS);
			const FVector2D P = ToS((W0 + W1) * 0.5f);
			const float A = Fade(P);
			if (A <= 0.f) continue;
			const FLinearColor Col = V == -1 ? Void : V == -2 ? Ground : V == -3 ? Road : Floor;
			Box(P - FVector2D(Tp * 0.5f + 0.5f), P + FVector2D(Tp * 0.5f + 0.5f), RDTA(Col, A));
			if (V >= 0)
			{
				// (a building's walls: where its floor meets anything else; its doorway left open)
				auto Edge = [&](const FVector2D& A_, const FVector2D& B_) { const FVector2D Pa = ToS(A_), Pb = ToS(B_); DrawLine(Pa.X, Pa.Y, Pb.X, Pb.Y, RDTA(Wall, A), 1.6f * Sc); };
				if (At(X + 1, Y) != V) Edge(FVector2D(W1.X, W0.Y), FVector2D(W1.X, W1.Y));
				if (At(X - 1, Y) != V) Edge(FVector2D(W0.X, W0.Y), FVector2D(W0.X, W1.Y));
				if (At(X, Y + 1) != V) Edge(FVector2D(W0.X, W1.Y), FVector2D(W1.X, W1.Y));
				if (At(X, Y - 1) != V) Edge(FVector2D(W0.X, W0.Y), FVector2D(W1.X, W0.Y));
			}
			else if (V != -1 && At(X + 1, Y) == -1) { const FVector2D Pa = ToS(FVector2D(W1.X, W0.Y)), Pb = ToS(W1); DrawLine(Pa.X, Pa.Y, Pb.X, Pb.Y, RDTA(Wall, A), 2.2f * Sc); }
			else if (V != -1 && At(X - 1, Y) == -1) { const FVector2D Pa = ToS(W0), Pb = ToS(FVector2D(W0.X, W1.Y)); DrawLine(Pa.X, Pa.Y, Pb.X, Pb.Y, RDTA(Wall, A), 2.2f * Sc); }
			if (V != -1 && V < 0 && At(X, Y + 1) == -1) { const FVector2D Pa = ToS(FVector2D(W0.X, W1.Y)), Pb = ToS(W1); DrawLine(Pa.X, Pa.Y, Pb.X, Pb.Y, RDTA(Wall, A), 2.2f * Sc); }
			if (V != -1 && V < 0 && At(X, Y - 1) == -1) { const FVector2D Pa = ToS(W0), Pb = ToS(FVector2D(W1.X, W0.Y)); DrawLine(Pa.X, Pa.Y, Pb.X, Pb.Y, RDTA(Wall, A), 2.2f * Sc); }
		}
	// doors: a warm bar across each doorway
	for (const ARDSection::FTownBld& B : S->TownBlds)
	{
		if (B.Door < 0) continue;
		const FVector D = S->GetDoorLocation(B.Door);
		const FVector2D P = ToS(FVector2D(D.X, D.Y));
		if (FVector2D::Distance(P, C) > R * 0.92f) continue;
		Box(P - FVector2D(2.5f * Sc), P + FVector2D(2.5f * Sc), RDTA(FLinearColor(1.f, 0.7f, 0.3f), Fade(P)));
	}
	// the trades' pictures in their middles
	for (const ARDSection::FTownBld& B : S->TownBlds)
	{
		if (B.Kind == TK_Home) continue;
		const FVector Mid = (S->LocalToWorld(B.Min) + S->LocalToWorld(B.Max - FIntPoint(1, 1))) * 0.5f;
		const FVector2D P = ToS(FVector2D(Mid.X, Mid.Y));
		const float A = Fade(P);
		if (A < 0.35f || FVector2D::Distance(P, C) > R * 0.86f) continue;
		const float Ic = (B.Kind == TK_Castle ? 22.f : 15.f) * Sc;
		if (!UI.Fit(RDTIconOf(B.Kind, B.State), P - FVector2D(Ic), P + FVector2D(Ic), FLinearColor(1.f, 1.f, 1.f, A))) SoftDot(P, 5.f * Sc, RDTA(RDTGold, A));
	}
	// the circle, the board, the Mistgate
	for (const ARDSection::FTownSpot& Sp : S->TownSpots)
	{
		if (Sp.Kind != TS_Circle && Sp.Kind != TS_Board) continue;
		const FVector2D P = ToS(FVector2D(Sp.At.X, Sp.At.Y));
		if (FVector2D::Distance(P, C) > R * 0.86f) continue;
		const float Ic = 13.f * Sc;
		UI.Fit(Sp.Kind == TS_Circle ? FName(TEXT("mapicon_circle")) : FName(TEXT("mapicon_board")), P - FVector2D(Ic), P + FVector2D(Ic), FLinearColor(1.f, 1.f, 1.f, Fade(P)));
	}
	if (!S->MistgateAt.IsZero())
	{
		const FVector2D P = ToS(FVector2D(S->MistgateAt.X, S->MistgateAt.Y));
		if (FVector2D::Distance(P, C) < R * 0.94f) MistMark(10, P, 6.f * Sc);
	}
	// monsters (the Mistward Hall's guards) and the people with quests for her
	for (const ARDMonster* Mo : Gen->GetMonsters())
	{
		if (!Mo || Mo->IsDead() || Mo->IsAlly() || FVector::Dist2D(Mo->GetActorLocation(), L) > 2500.f) continue;
		const FVector2D P = ToS(FVector2D(Mo->GetActorLocation()));
		if (FVector2D::Distance(P, C) > R * 0.94f) continue;
		SoftDot(P, 9.f * Sc, FLinearColor(1.f, 0.16f, 0.1f, 0.35f)); SoftDot(P, 4.6f * Sc, FLinearColor(1.f, 0.16f, 0.1f, 1.f));
	}
	const TArray<FString> Ql = Gen->GetQuestLines();
	for (const ARDTownsfolk* T : Gen->TownPeople)
	{
		if (!IsValid(T)) continue;
		const FString RoleName = StaticEnum<ERDTownRole>()->GetNameStringByValue((int64)T->TownRole);
		FString Mark;
		for (const FString& Q : Ql)
		{
			TArray<FString> P_; Q.ParseIntoArray(P_, TEXT("|"), false);
			if (P_.Num() < 4 || P_[1] != RoleName) continue;
			if (P_[3] == TEXT("ready")) { Mark = TEXT("?"); break; }
			if (P_[3] == TEXT("offered") && Mark.IsEmpty()) Mark = TEXT("!");
		}
		const FVector2D P = ToS(FVector2D(T->GetActorLocation()));
		if (FVector2D::Distance(P, C) > R * 0.9f) continue;
		if (Mark.IsEmpty()) { SoftDot(P, 3.2f * Sc, FLinearColor(0.55f, 0.85f, 1.f, 0.85f)); continue; }
		SoftDot(P, 8.f * Sc, FLinearColor(1.f, 0.82f, 0.3f, 0.45f));
		float Tw, Th; UI.TextSize(Mark, Tw, Th, Small, Sc * 1.2f, ERDType::Title);
		UI.Text(Mark, RDTGold, P.X - Tw * 0.5f, P.Y - Th * 0.5f, Small, Sc * 1.2f, ERDType::Title);
	}
	DrawPlayerArrow(C, Yaw - 90.f, 9.f * Sc);
	if (Ra) UI.Fit(TEXT("minimap_ring"), C - FVector2D(Ring), C + FVector2D(Ring));
	const FLinearColor Ink(0.75f, 0.77f, 0.8f, 0.85f);
	UI.Text(TEXT("N"), Ink, C.X - 4.f * Sc, C.Y - R * 0.98f, Small, Sc, ERDType::Title);
	const bool bPad = Gen->bCasterControls && Gen->GetPlayerCombat() && Gen->GetPlayerCombat()->IsUsingGamepad();
	FString Where = TEXT("the streets");
	if (const int32 Bi = S->TownBuildingAt(L); Bi >= 0) Where = S->TownBlds[Bi].Kind == TK_Home ? FString(S->TownBlds[Bi].State == 1 ? TEXT("a burned house") : S->TownBlds[Bi].State == 2 ? TEXT("a boarded house") : TEXT("a home")) : S->TownBlds[Bi].Label;
	const FString Under = FString::Printf(TEXT("%s    %s  map"), *Where, bPad ? TEXT("Back") : TEXT("M"));
	float Tw, Th; UI.TextSize(Under, Tw, Th, Small, Sc);
	UI.Text(Under, Ink, C.X - Tw * 0.5f, C.Y + (Ra ? Ring + 4.f * Sc : R * 0.96f), Small, Sc);
}

// ------------------------------------------------------------------------------------------------ the papyrus map
void ARDHUD::DrawTownMap(float Sc, const FVector& L, float Yaw)
{
	UFont* Small = GEngine->GetSmallFont(); UFont* Medium = GEngine->GetMediumFont();
	const ARDSection* S = Gen->GetSection(FIntPoint::ZeroValue);
	if (!S) return;
	TownLabels.Reset();
	Box(FVector2D(0, 0), FVector2D(Canvas->ClipX, Canvas->ClipY), FLinearColor(0.f, 0.f, 0.01f, 0.6f));
	const float Ms = FMath::Min(Canvas->ClipY * 0.9f, Canvas->ClipX * 0.62f);
	const FVector2D A((Canvas->ClipX - Ms) * 0.5f, (Canvas->ClipY - Ms) * 0.5f), B = A + FVector2D(Ms);
	// the sheet (painted papyrus; else a parchment tone), its edge darkened
	if (!UI.Fit(TEXT("map_papyrus"), A, B)) Box(A, B, FLinearColor(0.80f, 0.70f, 0.50f, 1.f));
	Frame(A, B, FLinearColor(0.35f, 0.24f, 0.12f, 0.9f), 3.f * Sc);
	// the town inside its wall, drawn into the sheet with a margin (north up: world +X up, +Y right)
	const FVector In0 = S->LocalToWorld(S->TownInner.Min) - FVector(150.f, 150.f, 0), In1 = S->LocalToWorld(S->TownInner.Max - FIntPoint(1, 1)) + FVector(150.f, 150.f, 0);
	const float Span = FMath::Max(In1.X - In0.X, In1.Y - In0.Y);
	const float Pad = Ms * 0.09f, K = (Ms - Pad * 2.f) / Span;
	const FVector2D Mid((In0.X + In1.X) * 0.5f, (In0.Y + In1.Y) * 0.5f), Cm = (A + B) * 0.5f + FVector2D(0.f, Ms * 0.015f);
	auto ToM = [&](const FVector2D& W) { return Cm + FVector2D(W.Y - Mid.Y, -(W.X - Mid.X)) * K; };
	auto Rect = [&](const FVector& W0, const FVector& W1, const FLinearColor& Col)
	{
		const FVector2D P = ToM(FVector2D(W0.X, W0.Y)), Q = ToM(FVector2D(W1.X, W1.Y));
		Box(FVector2D(FMath::Min(P.X, Q.X), FMath::Min(P.Y, Q.Y)), FVector2D(FMath::Max(P.X, Q.X), FMath::Max(P.Y, Q.Y)), Col);
	};
	const float TS = Gen->TileSize;
	auto TileBox = [&](const FIntRect& R, const FLinearColor& Col) { Rect(S->LocalToWorld(R.Min) - FVector(TS * 0.5f, TS * 0.5f, 0), S->LocalToWorld(R.Max - FIntPoint(1, 1)) + FVector(TS * 0.5f, TS * 0.5f, 0), Col); };
	// the streets and the square (pale washes), the buildings (ink outlines over a sepia wash)
	for (const FIntRect& R : S->TownRoads) TileBox(R, FLinearColor(0.55f, 0.42f, 0.25f, 0.28f));
	TileBox(S->TownSquare, FLinearColor(0.55f, 0.42f, 0.25f, 0.4f));
	for (const ARDSection::FTownBld& Bd : S->TownBlds)
	{
		const FIntRect R(Bd.Min, Bd.Max);
		TileBox(R, Bd.State == 1 ? FLinearColor(0.15f, 0.1f, 0.06f, 0.55f) : FLinearColor(0.42f, 0.28f, 0.14f, 0.45f));
		const FVector2D P = ToM(FVector2D(S->LocalToWorld(Bd.Min) - FVector(TS * 0.5f, TS * 0.5f, 0))), Q = ToM(FVector2D(S->LocalToWorld(Bd.Max - FIntPoint(1, 1)) + FVector(TS * 0.5f, TS * 0.5f, 0)));
		Frame(FVector2D(FMath::Min(P.X, Q.X), FMath::Min(P.Y, Q.Y)), FVector2D(FMath::Max(P.X, Q.X), FMath::Max(P.Y, Q.Y)), RDTA(RDTSepia, 0.85f), 1.2f * Sc);
	}
	// the wall: a thick ink line round it, its towers
	{
		const FVector2D P = ToM(FVector2D(In0.X, In0.Y)), Q = ToM(FVector2D(In1.X, In1.Y));
		Frame(FVector2D(FMath::Min(P.X, Q.X), FMath::Min(P.Y, Q.Y)), FVector2D(FMath::Max(P.X, Q.X), FMath::Max(P.Y, Q.Y)), RDTA(RDTSepia, 0.95f), 4.f * Sc);
	}
	// (the labels are placed after every picture, each where it overlaps no picture and no label placed before it: under its
	// picture, over it, beside it, or further down; the trades round the square stood so close that theirs covered each other)
	struct FMapLabel { FString Text; FVector2D P; float Size; FLinearColor Color; ERDType Type; float K; };
	TArray<FMapLabel> Pending;
	TArray<FBox2D> Taken;
	auto Icon = [&](FName Name, const FVector& W, float Size, const FString& Label, const FLinearColor& Tint = FLinearColor::White)
	{
		const FVector2D P = ToM(FVector2D(W.X, W.Y));
		const bool bArt = UI.Fit(Name, P - FVector2D(Size), P + FVector2D(Size), Tint);
		if (!bArt) { SoftDot(P, Size * 0.5f, RDTA(RDTSepia, 0.8f)); }
		if (Size >= 14.f * Sc) Taken.Add(FBox2D(P - FVector2D(Size * 0.8f), P + FVector2D(Size * 0.8f)));
		if (Label.IsEmpty()) return;
		Pending.Add({ Label, P, Size, FLinearColor(0.22f, 0.12f, 0.05f, 1.f), ERDType::Label, 0.92f });
		TownLabels.Add(FString::Printf(TEXT("%s|%s"), *Name.ToString(), *Label));
	};
	for (const ARDSection::FTownSpot& Sp : S->TownSpots)
		if (Sp.Kind == TS_Tower) Icon(TEXT("mapicon_tower"), Sp.At, 11.f * Sc, FString());
	// homes small, the trades large with what they do written under them
	for (const ARDSection::FTownBld& Bd : S->TownBlds)
	{
		const FVector W = (S->LocalToWorld(Bd.Min) + S->LocalToWorld(Bd.Max - FIntPoint(1, 1))) * 0.5f;
		const bool bHome = Bd.Kind == TK_Home;
		Icon(RDTIconOf(Bd.Kind, Bd.State), W, (bHome ? 12.f : Bd.Kind == TK_Castle ? 40.f : 26.f) * Sc, RDTLabelOf(Bd.Kind));
	}
	// what stands outdoors: the square, the well, the market, the circle, the board, the graveyard, the mill, the still, the gate
	FVector2D Stalls = FVector2D::ZeroVector; int32 NStalls = 0;
	for (const ARDSection::FTownSpot& Sp : S->TownSpots)
	{
		switch (Sp.Kind)
		{
		case TS_Well: Icon(TEXT("mapicon_well"), Sp.At, 15.f * Sc, TEXT("WELL")); break;
		case TS_Board: Icon(TEXT("mapicon_board"), Sp.At, 20.f * Sc, TEXT("QUEST BOARD · bounties")); break;
		case TS_Circle: Icon(TEXT("mapicon_circle"), Sp.At, 22.f * Sc, TEXT("TELEPORT CIRCLE")); break;
		case TS_Graveyard: Icon(TEXT("mapicon_graveyard"), Sp.At, 24.f * Sc, TEXT("GRAVEYARD")); break;
		case TS_Mill: Icon(TEXT("mapicon_mill"), Sp.At, 24.f * Sc, TEXT("MILL")); break;
		case TS_Still: Icon(TEXT("mapicon_still"), Sp.At, 14.f * Sc, TEXT("STILL")); break;
		case TS_Gate: Icon(TEXT("mapicon_gate"), Sp.At, 26.f * Sc, TEXT("GATE · barred")); break;
		case TS_Stall: Stalls += FVector2D(Sp.At.X, Sp.At.Y); ++NStalls; break;
		default: break;
		}
	}
	if (NStalls > 0) Icon(TEXT("mapicon_market"), FVector(Stalls / NStalls, 0.f) + FVector(0, 0, 0), 18.f * Sc, TEXT("MARKET"));
	{
		FVector Sq; Gen->GetTownPlace(TEXT("square"), Sq);
		const FVector2D P = ToM(FVector2D(Sq.X, Sq.Y));
		Pending.Insert({ TEXT("TOWN SQUARE"), P, 4.f * Sc, FLinearColor(0.22f, 0.12f, 0.05f, 0.9f), ERDType::Title, 0.95f }, 0);
		TownLabels.Add(TEXT("square|TOWN SQUARE"));
	}
	// the people with quests for her, the Mistgate, her
	const TArray<FString> Ql = Gen->GetQuestLines();
	for (const ARDTownsfolk* T : Gen->TownPeople)
	{
		if (!IsValid(T)) continue;
		const FString RoleName = StaticEnum<ERDTownRole>()->GetNameStringByValue((int64)T->TownRole);
		if (RoleName != TEXT("Elder") && RoleName != TEXT("Scholar") && RoleName != TEXT("Captain")) continue;
		FString Mark = TEXT("·");
		for (const FString& Q : Ql)
		{
			TArray<FString> P_; Q.ParseIntoArray(P_, TEXT("|"), false);
			if (P_.Num() < 4 || P_[1] != RoleName) continue;
			if (P_[3] == TEXT("ready")) { Mark = TEXT("?"); break; }
			if (P_[3] == TEXT("offered")) Mark = TEXT("!");
		}
		const FVector2D P = ToM(FVector2D(T->GetActorLocation()));
		SoftDot(P, 10.f * Sc, FLinearColor(0.75f, 0.1f, 0.05f, 0.5f));
		float Tw, Th; UI.TextSize(Mark, Tw, Th, Medium, Sc * 0.9f, ERDType::Title);
		UI.Text(Mark, FLinearColor(1.f, 0.9f, 0.6f, 1.f), P.X - Tw * 0.5f, P.Y - Th * 0.5f, Medium, Sc * 0.9f, ERDType::Title);
		Pending.Add({ T->Title, P, 9.f * Sc, FLinearColor(0.5f, 0.08f, 0.04f, 1.f), ERDType::Text, 0.85f });
	}
	for (const FMapLabel& Lb : Pending)
	{
		float Tw, Th; UI.TextSize(Lb.Text, Tw, Th, Small, Sc * Lb.K, Lb.Type);
		const FVector2D Half(Tw * 0.5f + 3.f * Sc, Th * 0.5f + 1.f * Sc);
		const float Below = Lb.Size * 0.92f + Th * 0.5f, Side = Lb.Size + Tw * 0.5f + 4.f * Sc;
		const FVector2D Tries[] = { { 0.f, Below }, { 0.f, -Below }, { Side, 0.f }, { -Side, 0.f }, { 0.f, Below + Th * 1.1f }, { 0.f, -Below - Th * 1.1f },
		                            { Side, Th * 1.1f }, { -Side, Th * 1.1f }, { 0.f, Below + Th * 2.2f }, { 0.f, -Below - Th * 2.2f } };
		FVector2D C = Lb.P + Tries[0];
		for (const FVector2D& O : Tries)
		{
			const FBox2D Bx(Lb.P + O - Half, Lb.P + O + Half);
			if (!Taken.ContainsByPredicate([&](const FBox2D& Tb) { return Tb.Intersect(Bx); })) { C = Lb.P + O; break; }
		}
		Taken.Add(FBox2D(C - Half, C + Half));
		Box(C - Half, C + Half, FLinearColor(0.93f, 0.86f, 0.70f, 0.55f));
		UI.Text(Lb.Text, Lb.Color, C.X - Tw * 0.5f, C.Y - Th * 0.5f, Small, Sc * Lb.K, Lb.Type);
	}
	if (!S->MistgateAt.IsZero()) MistMark(10, ToM(FVector2D(S->MistgateAt.X, S->MistgateAt.Y)), 7.f * Sc);
	{
		const FVector2D P = ToM(FVector2D(L.X, L.Y));
		SoftDot(P, 16.f * Sc, FLinearColor(0.8f, 0.05f, 0.03f, 0.35f));
		DrawPlayerArrow(P, Yaw - 90.f, 11.f * Sc);
		MapArrow = P; bMapArrow = true;
	}
	// the plaque and the compass, the key
	const FString Title = Gen->TownName.ToUpper();
	float Tw, Th; UI.TextSize(Title, Tw, Th, Medium, Sc * 1.8f, ERDType::Title);
	UI.Text(Title, FLinearColor(0.25f, 0.13f, 0.05f, 1.f), Cm.X - Tw * 0.5f, A.Y + Ms * 0.022f, Medium, Sc * 1.8f, ERDType::Title);
	UI.Text(TEXT("N"), FLinearColor(0.25f, 0.13f, 0.05f, 1.f), B.X - Pad * 0.6f, A.Y + Pad * 0.45f, Medium, Sc * 1.2f, ERDType::Title);
	DrawLine(B.X - Pad * 0.6f + 6.f * Sc, A.Y + Pad * 0.45f + 34.f * Sc, B.X - Pad * 0.6f + 6.f * Sc, A.Y + Pad * 0.45f + 70.f * Sc, FLinearColor(0.25f, 0.13f, 0.05f, 1.f), 2.f * Sc);
	const bool bPad = Gen->bCasterControls && Gen->GetPlayerCombat() && Gen->GetPlayerCombat()->IsUsingGamepad();
	const FString Key = FString::Printf(TEXT("%s close the map      !  a quest for you      ?  a quest to turn in"), bPad ? TEXT("Back") : TEXT("M"));
	UI.TextSize(Key, Tw, Th, Small, Sc);
	UI.Text(Key, FLinearColor(0.25f, 0.13f, 0.05f, 1.f), Cm.X - Tw * 0.5f, B.Y - Ms * 0.045f, Small, Sc);
	MapView = Mid;
}

// ------------------------------------------------------------------------------------------------ names over the townspeople
void ARDHUD::DrawTownNames(float Sc)
{
	TownNamesDrawn.Reset();
	APlayerController* PC = GetOwningPlayerController();
	const APawn* Me = GetOwningPawn();
	if (!PC || !PC->PlayerCameraManager || !Me) return;
	UFont* Small = GEngine->GetSmallFont();
	const FVector Cam = PC->PlayerCameraManager->GetCameraLocation(), Fw = PC->PlayerCameraManager->GetCameraRotation().Vector();
	const TArray<FString> Ql = Gen->GetQuestLines();
	for (const ARDTownsfolk* T : Gen->TownPeople)
	{
		if (!IsValid(T)) continue;
		const FVector Head = T->GetActorLocation() + FVector(0, 0, 115.f);
		const float D = FVector::Dist(Head, Me->GetActorLocation());
		if (D > 1400.f || FVector::DotProduct(Head - Cam, Fw) < 50.f) continue;
		const FString RoleName = StaticEnum<ERDTownRole>()->GetNameStringByValue((int64)T->TownRole);
		FString Mark;
		for (const FString& Q : Ql)
		{
			TArray<FString> P_; Q.ParseIntoArray(P_, TEXT("|"), false);
			if (P_.Num() < 4 || P_[1] != RoleName) continue;
			if (P_[3] == TEXT("ready")) { Mark = TEXT("?"); break; }
			if (P_[3] == TEXT("offered") && Mark.IsEmpty()) Mark = TEXT("!");
		}
		const FVector Sp = Project(Head);
		const float A = FMath::Clamp((1400.f - D) / 400.f, 0.f, 1.f);
		const float K = Sc * FMath::Lerp(0.85f, 1.1f, FMath::Clamp((900.f - D) / 700.f, 0.f, 1.f));
		float Tw, Th; UI.TextSize(T->Title, Tw, Th, Small, K);
		UI.Text(T->Title, FLinearColor(0.f, 0.f, 0.f, 0.7f * A), Sp.X - Tw * 0.5f + 1.f, Sp.Y - Th + 1.f, Small, K);
		UI.Text(T->Title, FLinearColor(1.f, 0.93f, 0.78f, A), Sp.X - Tw * 0.5f, Sp.Y - Th, Small, K);
		if (!T->Calling.IsEmpty() && D < 900.f)
		{
			float Cw, Ch; UI.TextSize(T->Calling, Cw, Ch, Small, K * 0.85f);
			UI.Text(T->Calling, FLinearColor(0.8f, 0.78f, 0.7f, 0.85f * A), Sp.X - Cw * 0.5f, Sp.Y + 2.f * Sc, Small, K * 0.85f);
		}
		if (!Mark.IsEmpty())
		{
			float Mw, Mh; UI.TextSize(Mark, Mw, Mh, Small, K * 2.f, ERDType::Title);
			UI.Text(Mark, FLinearColor(0.f, 0.f, 0.f, 0.7f * A), Sp.X - Mw * 0.5f + 2.f, Sp.Y - Th - Mh - 2.f * Sc + 2.f, Small, K * 2.f, ERDType::Title);
			UI.Text(Mark, FLinearColor(RDTGold.R, RDTGold.G, RDTGold.B, A), Sp.X - Mw * 0.5f, Sp.Y - Th - Mh - 2.f * Sc, Small, K * 2.f, ERDType::Title);
		}
		TownNamesDrawn.Add(FString::Printf(TEXT("%s|%s"), *T->Title, *Mark));
	}
}

// ------------------------------------------------------------------------------------------------ her purse and quests
void ARDHUD::DrawTownTracker(float Sc)
{
	UFont* Small = GEngine->GetSmallFont();
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return;
	TArray<TPair<FString, FLinearColor>> Ls;
	Ls.Add({ FString::Printf(TEXT("GOLD  %d"), GI->Gold), RDTGold });
	for (const FString& Q : Gen->GetQuestLines())
	{
		TArray<FString> P; Q.ParseIntoArray(P, TEXT("|"), false);
		if (P.Num() < 7 || (P[3] != TEXT("taken") && P[3] != TEXT("ready"))) continue;
		const bool bReady = P[3] == TEXT("ready");
		Ls.Add({ bReady ? FString::Printf(TEXT("%s  -  done: back to the %s"), *P[2], *P[1].ToLower()) : FString::Printf(TEXT("%s  %s/%s"), *P[2], *P[4], *P[5]),
		         bReady ? FLinearColor(0.55f, 0.95f, 0.55f) : RDTInk });
		if (!bReady && !P[6].IsEmpty()) Ls.Add({ FString::Printf(TEXT("   %s"), *P[6]), RDTDim });
		if (Ls.Num() > 10) break;
	}
	float Wmax = 0.f, Tw, Th = 0.f;
	for (const auto& Lp : Ls) { UI.TextSize(Lp.Key, Tw, Th, Small, Sc, Lp.Key.StartsWith(TEXT("GOLD")) ? ERDType::Label : ERDType::Text); Wmax = FMath::Max(Wmax, Tw); }
	const float X1 = Canvas->ClipX - 24.f * Sc, Y0 = Canvas->ClipY * 0.47f;
	Box(FVector2D(X1 - Wmax - 20.f * Sc, Y0 - 6.f * Sc), FVector2D(X1 + 6.f * Sc, Y0 + (Th + 4.f * Sc) * Ls.Num() + 6.f * Sc), FLinearColor(0.02f, 0.02f, 0.03f, 0.5f));
	float Y = Y0;
	for (const auto& Lp : Ls)
	{
		const ERDType Ty = Lp.Key.StartsWith(TEXT("GOLD")) ? ERDType::Label : ERDType::Text;
		UI.TextSize(Lp.Key, Tw, Th, Small, Sc, Ty);
		UI.Text(Lp.Key, Lp.Value, X1 - Tw - 6.f * Sc, Y, Small, Sc, Ty);
		Y += Th + 4.f * Sc;
	}
}

// ------------------------------------------------------------------------------------------------ the town's panel
void ARDHUD::DrawTownPanel(float Sc)
{
	UFont* Small = GEngine->GetSmallFont(); UFont* Medium = GEngine->GetMediumFont();
	const URDCombatComponent* Cb = Gen->GetPlayerCombat();
	const bool bPad = Cb && Cb->IsUsingGamepad();
	Box(FVector2D(0, 0), FVector2D(Canvas->ClipX, Canvas->ClipY), FLinearColor(0.f, 0.f, 0.01f, 0.5f));
	const float W = 1100.f * Sc, H = 720.f * Sc, Pd = 22.f * Sc, Rh = 40.f * Sc;
	const FVector2D A((Canvas->ClipX - W) * 0.5f, FMath::Max(40.f * Sc, (Canvas->ClipY - H) * 0.5f)), B = A + FVector2D(W, H);
	if (!Board(TEXT("panel_wide"), A, B, Sc, 44.f * Sc)) { Box(A, B, FLinearColor(0.035f, 0.04f, 0.055f, 0.94f)); Frame(A, B, FLinearColor(0.75f, 0.65f, 0.45f, 0.9f), 2.f * Sc); }
	const float Tin = UI.Has(TEXT("panel_wide")) ? 24.f * Sc : 0.f;
	float Tw, Th;
	UI.Text(Gen->TownTitle.ToUpper(), RDTInk, A.X + Pd + Tin, A.Y + 16.f * Sc, Medium, Sc * 1.45f, ERDType::Title);
	UI.TextSize(Gen->TownSub, Tw, Th, Small, Sc * 1.05f);
	UI.Text(Gen->TownSub, RDTGold, B.X - Pd - Tin - Tw, A.Y + 22.f * Sc, Small, Sc * 1.05f);
	const FString Purse = FString::Printf(TEXT("GOLD  %d"), Gen->GetGold());
	UI.TextSize(Purse, Tw, Th, Small, Sc * 1.05f, ERDType::Label);
	UI.Text(Purse, RDTGold, B.X - Pd - Tin - Tw, A.Y + 48.f * Sc, Small, Sc * 1.05f, ERDType::Label);
	// tabs (the store, the storage)
	float Y = A.Y + 82.f * Sc;
	Gen->TownTabBoxes.Reset();
	const FName Kind = Gen->GetTownPanel();
	if (Kind == TEXT("store") || Kind == TEXT("stash"))
	{
		const TCHAR* Tabs[2] = { Kind == TEXT("store") ? TEXT("BUY") : TEXT("STORE A THING"), Kind == TEXT("store") ? TEXT("SELL") : TEXT("TAKE ONE BACK") };
		float X = A.X + Pd + Tin;
		for (int32 T = 0; T < 2; ++T)
		{
			UI.TextSize(Tabs[T], Tw, Th, Small, Sc * 1.1f, ERDType::Label);
			const FVector2D T0(X - 8.f * Sc, Y - 4.f * Sc), T1(X + Tw + 8.f * Sc, Y + Th + 4.f * Sc);
			const bool bOn = Gen->GetTownTab() == T;
			Box(T0, T1, bOn ? FLinearColor(0.36f, 0.27f, 0.10f, 0.95f) : FLinearColor(0.08f, 0.08f, 0.1f, 0.7f));
			if (bOn) Frame(T0, T1, RDTGold, 1.5f * Sc);
			UI.Text(Tabs[T], bOn ? FLinearColor::White : RDTDim, X, Y, Small, Sc * 1.1f, ERDType::Label);
			Gen->TownTabBoxes.Add(FBox2D(T0, T1));
			X = T1.X + 22.f * Sc;
		}
		Y += 40.f * Sc;
	}
	// the lines on the left
	const float Lx = A.X + Pd + Tin, Lw = W * 0.46f - Pd;
	const TArray<ARDDungeonGenerator::FTownLine>& Lines = Gen->TownLines;
	const int32 Cur = Gen->GetTownCursor();
	const int32 Fit = FMath::Max(4, FMath::FloorToInt32((B.Y - 120.f * Sc - Y) / Rh));
	const int32 First = Lines.Num() > Fit ? FMath::Clamp(Cur - Fit / 2, 0, Lines.Num() - Fit) : 0;
	Gen->TownRowBoxes.Reset();
	for (int32 I = 0; I < Lines.Num(); ++I) Gen->TownRowBoxes.Add(FBox2D(FVector2D(-1, -1), FVector2D(-1, -1)));
	for (int32 I = First; I < Lines.Num() && I < First + Fit; ++I)
	{
		const ARDDungeonGenerator::FTownLine& Ln = Lines[I];
		const bool bOn = I == Cur;
		const FVector2D R0(Lx, Y), R1(Lx + Lw, Y + Rh - 4.f * Sc);
		Gen->TownRowBoxes[I] = FBox2D(R0, R1);
		if (bOn)
		{
			const FRDUIArt* Pl = UI.Find(TEXT("button"));
			if (Pl && Pl->Texture) UI.Nine(TEXT("button"), R0 - FVector2D(4.f * Sc), R1 + FVector2D(4.f * Sc), (Rh + 4.f * Sc) / FMath::Max((float)Pl->Texture->GetSizeY(), 1.f), FLinearColor(1.25f, 1.05f, 0.7f));
			else Box(R0, R1, FLinearColor(0.36f, 0.27f, 0.10f, 0.95f));
			Frame(R0, R1, RDTGold, 2.f * Sc);
		}
		// (a thing's picture where it has one)
		float Ix = 0.f;
		if (Ln.Act == TEXT("buy") || Ln.Act == TEXT("sell") || Ln.Act == TEXT("deposit") || Ln.Act == TEXT("withdraw"))
		{
			FName Item = NAME_None;
			if (Ln.Act == TEXT("buy")) Item = FName(*Ln.Arg);
			else if (Ln.Arg.StartsWith(TEXT("i:"))) Item = FName(*Ln.Arg.Mid(2));
			else if (Ln.Arg.StartsWith(TEXT("w:"))) { const int32 Wi = FCString::Atoi(*Ln.Arg.Mid(2)); if (Gen->Weapons.IsValidIndex(Wi)) Item = Gen->Weapons[Wi].Item; }
			else if (Ln.Act == TEXT("withdraw")) Item = FName(*Ln.Label);
			const FName Ic = ItemIcon(Item);
			if (UI.Has(Ic)) { Ix = Rh; UI.Fit(Ic, FVector2D(R0.X + 6.f * Sc, R0.Y - 2.f * Sc), FVector2D(R0.X + 2.f * Sc + Rh, R1.Y + 2.f * Sc)); }
		}
		const FLinearColor Col = !Ln.bOn ? RDTDim : bOn ? FLinearColor::White : FLinearColor(0.86f, 0.84f, 0.78f);
		float Nk = Sc * 1.1f, Nw, Nh;
		UI.TextSize(Ln.Label, Nw, Nh, Small, Nk);
		if (Nw > Lw - Ix - 110.f * Sc) Nk *= FMath::Max((Lw - Ix - 110.f * Sc) / Nw, 0.65f);
		UI.Text(Ln.Label, Col, R0.X + 12.f * Sc + Ix, R0.Y + 8.f * Sc, Small, Nk);
		if (!Ln.Tag.IsEmpty())
		{
			UI.TextSize(Ln.Tag, Tw, Th, Small, Sc, ERDType::Label);
			const bool bGood = Ln.Tag.StartsWith(TEXT("+")) || Ln.Tag == TEXT("REWARD") || Ln.Tag == TEXT("NEW") || Ln.Tag == TEXT("FREE");
			UI.Text(Ln.Tag, !Ln.bOn ? RDTDim : bGood ? FLinearColor(0.55f, 0.95f, 0.55f) : RDTGold, R1.X - 12.f * Sc - Tw, R0.Y + 10.f * Sc, Small, Sc, ERDType::Label);
		}
		Y += Rh;
	}
	if (Lines.Num() > Fit) UI.Text(FString::Printf(TEXT("%d more above,  %d more below"), First, Lines.Num() - First - Fit), RDTDim, Lx + 12.f * Sc, Y + 6.f * Sc, Small, Sc * 0.95f);
	// the right side: what was said, then what the chosen line is
	const float Rx = A.X + W * 0.46f + Pd, Rw = W * 0.54f - Pd * 2.f - Tin;
	float Ry = A.Y + 82.f * Sc;
	Box(FVector2D(Rx - Pd * 0.5f, Ry), FVector2D(Rx - Pd * 0.5f + 1.f, B.Y - 110.f * Sc), FLinearColor(0.75f, 0.65f, 0.45f, 0.4f));
	if (!Gen->TownBody.IsEmpty())
	{
		for (const FString& Ln : WrapText(Gen->TownBody, Rw, Small, Sc * 1.12f)) { UI.Text(Ln, RDTInk, Rx, Ry, Small, Sc * 1.12f); Ry += 26.f * Sc; }
		Ry += 16.f * Sc;
	}
	if (Lines.IsValidIndex(Cur) && !Lines[Cur].Detail.IsEmpty() && Lines[Cur].Detail != Gen->TownBody && Lines[Cur].Act != TEXT("ask"))
	{
		UI.Text(Lines[Cur].Label.ToUpper(), RDTGold, Rx, Ry, Small, Sc * 1.0f, ERDType::Label); Ry += 26.f * Sc;
		for (const FString& Ln : WrapText(Lines[Cur].Detail, Rw, Small, Sc * 1.05f)) { UI.Text(Ln, FLinearColor(0.86f, 0.84f, 0.78f), Rx, Ry, Small, Sc * 1.05f); Ry += 24.f * Sc; }
	}
	// the note and the keys at the foot
	const float Fy = B.Y - 92.f * Sc;
	if (UI.Has(TEXT("divider"))) UI.Fit(TEXT("divider"), FVector2D(A.X + Pd, Fy - 20.f * Sc), FVector2D(B.X - Pd, Fy + 20.f * Sc));
	if (!Gen->GetTownNote().IsEmpty()) UI.Text(Gen->GetTownNote(), FLinearColor(1.f, 0.93f, 0.75f), A.X + Pd + Tin, Fy + 14.f * Sc, Small, Sc * 1.15f);
	const bool bTabs = Kind == TEXT("store") || Kind == TEXT("stash");
	const FString Keys = bPad ? (bTabs ? TEXT("D-pad  choose      LB / RB  the other list      A  do it      B  leave") : TEXT("D-pad  choose      A  do it      B  leave"))
	                          : (bTabs ? TEXT("W S / wheel  choose      A D  the other list      Enter or click  do it      Esc or F  leave") : TEXT("W S / wheel  choose      Enter or click  do it      Esc or F  leave"));
	UI.Text(Keys, RDTDim, A.X + Pd + Tin, Fy + 50.f * Sc, Small, Sc * 1.05f);
}
