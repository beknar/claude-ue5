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
#include "CanvasItem.h"
#include "RenderUtils.h"
#include "Engine/TextureRenderTarget2D.h"
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
	case TK_Cathedral: return TEXT("mapicon_temple");          // (Vel Morrath's: the temple's and the chapel's pictures)
	case TK_Monastery: return TEXT("mapicon_chapel");
	case TK_Foundry: return TEXT("mapicon_castle");             // (Ashenreach's: the castle's and the smithy's pictures)
	case TK_Workshop: return TEXT("mapicon_smithy");
	case TK_SluiceHouse: return TEXT("mapicon_storehouse");     // (Graymourne's: the storehouse's picture)
	case TK_Warehouse: return TEXT("mapicon_storehouse");
	case TK_Spire: return TEXT("mapicon_castle");               // (Kethrys Spire's: the castle's and the witch's pictures)
	case TK_Library: return TEXT("mapicon_witch");
	case TK_Laboratory: return TEXT("mapicon_witch");
	case TK_Study: return TEXT("mapicon_witch");
	case TK_Meditation: return TEXT("mapicon_witch");
	case TK_Research: return TEXT("mapicon_castle");            // (Heaven's: the castle's, the barracks' and the store's pictures)
	case TK_SkyTower: return TEXT("mapicon_barracks");
	case TK_Office: return TEXT("mapicon_storehouse");
	case TK_Shop: return TEXT("mapicon_store");
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
	case TK_Cathedral: return TEXT("CATHEDRAL · the stair down");
	case TK_Monastery: return TEXT("MONASTERY");
	case TK_Foundry: return TEXT("THE GREAT FOUNDRY · into The War Engine");
	case TK_Workshop: return TEXT("WORKSHOP");
	case TK_SluiceHouse: return TEXT("THE SLUICE HOUSE · into the sewers");
	case TK_Warehouse: return TEXT("WAREHOUSE");
	case TK_Spire: return TEXT("THE BLACK TOWER · sealed for a century");
	case TK_Library: return TEXT("LIBRARY");
	case TK_Laboratory: return TEXT("LABORATORY");
	case TK_Study: return TEXT("STUDY");
	case TK_Meditation: return TEXT("MEDITATION");
	case TK_Research: return TEXT("KRATOS AURORIM RESEARCH, LLC · the facility");
	case TK_SkyTower: return TEXT("TOWER");
	case TK_Office: return TEXT("OFFICES");
	case TK_Shop: return TEXT("SHOP");
	default: return FString();
	}
}

/** a townsperson's quest mark from the quest lines: "?" one is ready to turn in to them, "!" they offer one, "" none */
static FString RDTQuestMark(const TArray<FString>& QuestLines, const FString& RoleName)
{
	FString Mark;
	for (const FString& Q : QuestLines)
	{
		TArray<FString> P_; Q.ParseIntoArray(P_, TEXT("|"), false);
		if (P_.Num() < 4 || P_[1] != RoleName) continue;
		if (P_[3] == TEXT("ready")) return TEXT("?");
		if (P_[3] == TEXT("offered")) Mark = TEXT("!");
	}
	return Mark;
}

void ARDHUD::PlaceTownMapLabels(const TArray<FRDTMapLabel>& Pending, TArray<FBox2D>& Taken, float Sc, const FLinearColor& Halo)
{
	// (each label where it covers no picture taken and no label before it: under its picture, over it, beside it, or further
	// down; the trades round the square stood so close that theirs covered each other)
	UFont* Small = GEngine->GetSmallFont();
	for (const FRDTMapLabel& Lb : Pending)
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
		Box(C - Half, C + Half, Halo);
		UI.Text(Lb.Text, Lb.Color, C.X - Tw * 0.5f, C.Y - Th * 0.5f, Small, Sc * Lb.K, Lb.Type);
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
	const TArray<FString> Ql = Gen->GetQuestLinesHere();
	for (const ARDTownsfolk* T : Gen->TownPeople)
	{
		if (!IsValid(T)) continue;
		const FString RoleName = StaticEnum<ERDTownRole>()->GetNameStringByValue((int64)T->TownRole);
		const FString Mark = RDTQuestMark(Ql, RoleName);
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
	// (the town's hour when its day and night run: "day 1 · 14:30")
	const FString Clock = Gen->bDayNight ? FString::Printf(TEXT("    day %d · %s"), Gen->GetTownDay(), *Gen->GetTownClock()) : FString();
	const FString Under = FString::Printf(TEXT("%s%s    %s  map"), *Where, *Clock, bPad ? TEXT("Back") : TEXT("M"));
	float Tw, Th; UI.TextSize(Under, Tw, Th, Small, Sc);
	UI.Text(Under, Ink, C.X - Tw * 0.5f, C.Y + (Ra ? Ring + 4.f * Sc : R * 0.96f), Small, Sc);
}

// ------------------------------------------------------------------------------------------------ the papyrus map
void ARDHUD::DrawTownMap(float Sc, const FVector& L, float Yaw)
{
	// (the painted map in colour, the Fairhill reference's look (the user's of 2026-11-02), when its pictures are there)
	if (Gen->HasTownSatellite() || (UI.Has(TEXT("mapc_grass")) && UI.Has(TEXT("mapc_parchment")))) { DrawTownMapColour(Sc, L, Yaw); return; }
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
	TArray<FRDTMapLabel> Pending;
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
		case TS_Gate: Icon(TEXT("mapicon_gate"), Sp.At, 26.f * Sc, Gen->bWild ? TEXT("GATE · the wilds") : TEXT("GATE · barred")); break;
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
	const TArray<FString> Ql = Gen->GetQuestLinesHere();
	for (const ARDTownsfolk* T : Gen->TownPeople)
	{
		if (!IsValid(T)) continue;
		const FString RoleName = StaticEnum<ERDTownRole>()->GetNameStringByValue((int64)T->TownRole);
		if (RoleName != TEXT("Elder") && RoleName != TEXT("Scholar") && RoleName != TEXT("Captain")) continue;
		FString Mark = RDTQuestMark(Ql, RoleName);
		if (Mark.IsEmpty()) Mark = TEXT("·");
		const FVector2D P = ToM(FVector2D(T->GetActorLocation()));
		SoftDot(P, 10.f * Sc, FLinearColor(0.75f, 0.1f, 0.05f, 0.5f));
		float Tw, Th; UI.TextSize(Mark, Tw, Th, Medium, Sc * 0.9f, ERDType::Title);
		UI.Text(Mark, FLinearColor(1.f, 0.9f, 0.6f, 1.f), P.X - Tw * 0.5f, P.Y - Th * 0.5f, Medium, Sc * 0.9f, ERDType::Title);
		Pending.Add({ T->Title, P, 9.f * Sc, FLinearColor(0.5f, 0.08f, 0.04f, 1.f), ERDType::Text, 0.85f });
	}
	PlaceTownMapLabels(Pending, Taken, Sc, FLinearColor(0.93f, 0.86f, 0.70f, 0.55f));
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

// ------------------------------------------------------------------------------------------------ the painted map in colour
// (the user's reference, ai models/fairhill village.jpg: a storybook village map in full colour. Painted grass inside the wall
// fading into the parchment, earth and cobbled roads, every building a painted picture on its own footprint, the trees and
// bushes where they stand (TownGreens), a grey stone wall with its towers and gate, the watch's patrol along the lane as a
// gold dashed line, a gold title and a compass rose; the labels as on the ink map. SourceArt/brokenspire/map_art_colour.json)
bool ARDHUD::TownTiled(FName Name, const FVector2D& A, const FVector2D& B, const FVector2D& W0, const FVector2D& W1, float Repeat, const FLinearColor& Tint)
{
	const FRDUIArt* Art = UI.Find(Name);
	if (!Art || !Art->Texture) return false;
	// (the picture's u runs with the world's Y (the map's right), v against its X (the map's down))
	const float U0 = FMath::Min(W0.Y, W1.Y) / Repeat, V0 = -FMath::Max(W0.X, W1.X) / Repeat;
	const float Uw = FMath::Abs(W1.Y - W0.Y) / Repeat, Vh = FMath::Abs(W1.X - W0.X) / Repeat;
	const FVector2D P(FMath::Min(A.X, B.X), FMath::Min(A.Y, B.Y)), Q(FMath::Max(A.X, B.X), FMath::Max(A.Y, B.Y));
	DrawTexture(Art->Texture, P.X, P.Y, Q.X - P.X, Q.Y - P.Y, U0, V0, Uw, Vh, Tint, BLEND_Translucent);
	if (UI.Drawn) UI.Drawn->AddUnique(Name);
	return true;
}

void ARDHUD::TownTris(FName Name, const TArray<FVector2D>& Screen, const TArray<FVector2D>& World, const TArray<int32>& Ix, float Repeat, const FLinearColor& Tint)
{
	const FRDUIArt* Art = UI.Find(Name);
	if (!Canvas || Screen.Num() != World.Num()) return;
	// (its picture missing (883 not run): a plain colour of its kind, as the old map's boxes were (the PR review's find))
	const bool bPlain = !Art || !Art->Texture;
	FLinearColor C = Tint;
	if (bPlain)
	{
		const FString N = Name.ToString();
		const FLinearColor Base = N.Contains(TEXT("wall")) ? FLinearColor(0.42f, 0.41f, 0.39f) : N.Contains(TEXT("grass")) ? FLinearColor(0.36f, 0.5f, 0.24f) : N.Contains(TEXT("cobble")) ? FLinearColor(0.55f, 0.52f, 0.47f) : FLinearColor(0.62f, 0.5f, 0.33f);
		C = FLinearColor(Base.R * Tint.R, Base.G * Tint.G, Base.B * Tint.B, Tint.A);
	}
	// (a painted texture over triangles, its picture anchored to the world as TownTiled's: u with the world's Y, v against X)
	TArray<FCanvasUVTri> Tris;
	auto Uv = [&](const FVector2D& W) { return FVector2D(W.Y / Repeat, -W.X / Repeat); };
	for (int32 I = 0; I + 2 < Ix.Num(); I += 3)
	{
		FCanvasUVTri Tr;
		Tr.V0_Pos = Screen[Ix[I]]; Tr.V1_Pos = Screen[Ix[I + 1]]; Tr.V2_Pos = Screen[Ix[I + 2]];
		Tr.V0_UV = Uv(World[Ix[I]]); Tr.V1_UV = Uv(World[Ix[I + 1]]); Tr.V2_UV = Uv(World[Ix[I + 2]]);
		Tr.V0_Color = C; Tr.V1_Color = C; Tr.V2_Color = C;
		Tris.Add(Tr);
	}
	FCanvasTriangleItem Item(Tris, bPlain ? GWhiteTexture : Art->Texture->GetResource());
	Item.BlendMode = SE_BLEND_Translucent;
	Canvas->DrawItem(Item);
	if (UI.Drawn && !bPlain) UI.Drawn->AddUnique(Name);
}

void ARDHUD::DrawTownMapColour(float Sc, const FVector& L, float Yaw)
{
	UFont* Small = GEngine->GetSmallFont(); UFont* Medium = GEngine->GetMediumFont();
	const ARDSection* S = Gen->GetSection(FIntPoint::ZeroValue);
	if (!S) return;
	TownLabels.Reset();
	Box(FVector2D(0, 0), FVector2D(Canvas->ClipX, Canvas->ClipY), FLinearColor(0.f, 0.f, 0.01f, 0.6f));
	const float Ms = FMath::Min(Canvas->ClipY * 0.92f, Canvas->ClipX * 0.64f);
	const FVector2D A((Canvas->ClipX - Ms) * 0.5f, (Canvas->ClipY - Ms) * 0.5f), B = A + FVector2D(Ms);
	// the sheet: an old scroll, its edges frayed and unravelling (the user's of 2026-11-02: "the edges of the town overhead map
	// should be frayed and unraveling, like an ancient scroll": mapc_scroll, made from the parchment by bs_scroll.py); else the
	// parchment with a dark rule and a gold one inside it
	// (since 2026-11-03 (the user's: "a semi-realistic top down representation of the terrain features, much like what you would
	// see from a satellite or google earth, with labels on important or functional buildings and quest markers on NPCs"): the
	// town's own picture from above (the generator's TownSatellitePicture, RDTownSat.cpp) on a dark sheet with a gold rule, under
	// the labels and the seals; the painted map until it is taken)
	const bool bSat = Gen->HasTownSatellite();
	if (bSat)
	{
		Box(A - FVector2D(Ms * 0.03f), B + FVector2D(Ms * 0.03f), FLinearColor(0.035f, 0.035f, 0.04f, 0.97f));
	}
	else if (UI.Has(TEXT("mapc_scroll"))) UI.Fit(TEXT("mapc_scroll"), A - FVector2D(Ms * 0.03f), B + FVector2D(Ms * 0.03f));
	else
	{
		if (!UI.Fit(TEXT("mapc_parchment"), A, B)) Box(A, B, FLinearColor(0.86f, 0.77f, 0.58f, 1.f));
		Frame(A, B, FLinearColor(0.30f, 0.20f, 0.10f, 0.95f), 3.f * Sc);
		Frame(A + FVector2D(7.f * Sc), B - FVector2D(7.f * Sc), FLinearColor(0.78f, 0.6f, 0.26f, 0.9f), 1.5f * Sc);
	}
	// the town (north up: world +X up, +Y right), the wall a little inside the sheet's margin
	const float TS = Gen->TileSize;
	const FVector In0 = S->LocalToWorld(S->TownInner.Min) - FVector(TS * 0.5f, TS * 0.5f, 0), In1 = S->LocalToWorld(S->TownInner.Max - FIntPoint(1, 1)) + FVector(TS * 0.5f, TS * 0.5f, 0);
	const float Span = FMath::Max(In1.X - In0.X, In1.Y - In0.Y);
	// (the third list of 2026-11-02: "you should be able to zoom the overhead map in and out and then move it around": the
	// generator's MapZoom (1 the whole town) and MapPan (world cm from the town's middle) move the view over the sheet)
	const float Zm = FMath::Clamp(Gen->MapZoom, 1.f, 8.f);
	const float Pad = Ms * 0.1f, K = (Ms - Pad * 2.f) / Span * Zm;
	const FVector2D Mid0((In0.X + In1.X) * 0.5f, (In0.Y + In1.Y) * 0.5f), Cm = (A + B) * 0.5f + FVector2D(0.f, Ms * 0.02f);
	const FVector2D Mid = Mid0 + Gen->MapPan;
	TownMapSpan = Span; Gen->TownMapPxPerCm = K;
	const bool bZoomed = Zm > 1.01f || !Gen->MapPan.IsNearlyZero(1.f);
	auto ToM = [&](const FVector2D& W) { return Cm + FVector2D(W.Y - Mid.Y, -(W.X - Mid.X)) * K; };
	auto W2 = [](const FVector& V) { return FVector2D(V.X, V.Y); };
	// (a tile rectangle's world corners)
	auto TileW = [&](const FIntRect& R, FVector2D& W0, FVector2D& W1)
	{
		W0 = W2(S->LocalToWorld(R.Min) - FVector(TS * 0.5f, TS * 0.5f, 0)); W1 = W2(S->LocalToWorld(R.Max - FIntPoint(1, 1)) + FVector(TS * 0.5f, TS * 0.5f, 0));
	};
	const float Rep = 6000.f;                      // (a texture's picture covers 60 m of the town)
	// the wall's outline (since 2026-11-02 irregular; its corners in order round the town) and its middle
	TArray<FVector2D> Ol = S->TownBorder;
	if (Ol.Num() < 3) { const FVector2D W0 = W2(In0), W1 = W2(In1); Ol = { W0, FVector2D(W1.X, W0.Y), W1, FVector2D(W0.X, W1.Y) }; }
	FVector2D Bc = FVector2D::ZeroVector;
	for (const FVector2D& P : Ol) Bc += P;
	Bc /= Ol.Num();
	if (bSat)
	{
		// the picture: its square of the world (its middle, its half width) where the map puts that square; the picture's up
		// is the world's +X, its right +Y, as the map's
		const FVector2D Sc0 = Gen->TownSatCenter; const float Hs = Gen->TownSatHalf;
		const FVector2D Tl = ToM(FVector2D(Sc0.X + Hs, Sc0.Y - Hs)), Br = ToM(FVector2D(Sc0.X - Hs, Sc0.Y + Hs));
		DrawTexture(Gen->TownSatellitePicture, Tl.X, Tl.Y, Br.X - Tl.X, Br.Y - Tl.Y, 0.f, 0.f, 1.f, 1.f, FLinearColor::White, BLEND_Opaque);
		// (a little brighter: the picture added again at a share; a tint over 1 is clamped)
		const float Bt = FMath::Clamp(Gen->TownSatelliteBrighten, 0.f, 1.f);
		if (Bt > 0.f) DrawTexture(Gen->TownSatellitePicture, Tl.X, Tl.Y, Br.X - Tl.X, Br.Y - Tl.Y, 0.f, 0.f, 1.f, 1.f, FLinearColor(Bt, Bt, Bt, 1.f), BLEND_Additive);
		if (UI.Drawn) UI.Drawn->AddUnique(TEXT("town_satellite"));
	}
	else
	{
	// the grass: the walled ground, feathered into the parchment round it (one picture over the whole town: repeated, its
	// mirrored seams showed as bands); a fan of triangles from the middle, the outline grown for the feather
	{
		const float GRep = Span * 1.05f;
		auto Fan = [&](float Grow, const FLinearColor& Tint)
		{
			TArray<FVector2D> Wp, Sp; TArray<int32> Ix;
			Wp.Add(Bc); Sp.Add(ToM(Bc));
			for (const FVector2D& P : Ol) { const FVector2D Q = P + (P - Bc).GetSafeNormal() * Grow; Wp.Add(Q); Sp.Add(ToM(Q)); }
			for (int32 I = 1; I <= Ol.Num(); ++I) Ix.Append({ 0, I, I % Ol.Num() + 1 });
			TownTris(TEXT("mapc_grass"), Sp, Wp, Ix, GRep, Tint);
		};
		for (int32 F = 8; F >= 1; --F) Fan(F * 380.f, FLinearColor(1.f, 1.f, 1.f, 0.11f));
		Fan(0.f, FLinearColor::White);
		// the lane inside the wall: trodden earth, two tiles along every edge
		TArray<FVector2D> Inner;
		for (const FVector2D& P : Ol) Inner.Add(P + (Bc - P).GetSafeNormal() * TS * 2.f);
		for (int32 I = 0, J = Ol.Num() - 1; I < Ol.Num(); J = I++)
			TownTris(TEXT("mapc_dirt"), { ToM(Ol[J]), ToM(Ol[I]), ToM(Inner[I]), ToM(Inner[J]) }, { Ol[J], Ol[I], Inner[I], Inner[J] }, { 0, 1, 2, 0, 2, 3 }, Rep * 0.5f, FLinearColor(1.f, 1.f, 1.f, 0.6f));
	}
	// the winding earth roads: a dark verge, then the earth, each a strip along its middle
	for (int32 Pass = 0; Pass < 2; ++Pass)
		for (const ARDSection::FTownPath& Pth : S->TownPaths)
			for (int32 I = 1; I < Pth.Pts.Num(); ++I)
			{
				const FVector2D Pa = Pth.Pts[I - 1], Pb = Pth.Pts[I];
				const FVector2D Dn = (Pb - Pa).GetSafeNormal(), Nn(-Dn.Y, Dn.X);
				const float Hw = Pth.HalfWidth * (Pass == 0 ? 1.25f : 1.f);
				// (each piece a little longer than its step: the bends stay closed)
				const FVector2D A0 = Pa - Dn * Hw * 0.35f, B0 = Pb + Dn * Hw * 0.35f;
				const TArray<FVector2D> Wq = { A0 + Nn * Hw, B0 + Nn * Hw, B0 - Nn * Hw, A0 - Nn * Hw };
				TArray<FVector2D> Sq; for (const FVector2D& Q : Wq) Sq.Add(ToM(Q));
				if (Pass == 0) TownTris(TEXT("mapc_dirt"), Sq, Wq, { 0, 1, 2, 0, 2, 3 }, Rep * 0.5f, FLinearColor(0.35f, 0.25f, 0.12f, 0.5f));
				else TownTris(TEXT("mapc_dirt"), Sq, Wq, { 0, 1, 2, 0, 2, 3 }, Rep * 0.5f, FLinearColor(0.95f, 0.82f, 0.62f, 1.f));
			}
	// the roads: a dark verge under every road first, then the cobbles, so that crossings stay clean (every street, the square
	// and the stair turret's path are cobbled in the town (TownGround); the lane by the wall is earth, drawn above. Until the
	// PR review the side streets were drawn as earth)
	TArray<TPair<FVector2D, FVector2D>> Roads; TArray<bool> Cobbled;
	for (int32 I = 0; I < S->TownRoads.Num(); ++I)
	{
		FVector2D W0, W1; TileW(S->TownRoads[I], W0, W1);
		Roads.Add({ W0, W1 }); Cobbled.Add(true);
	}
	{
		FVector2D W0, W1; TileW(S->TownSquare, W0, W1);
		Roads.Add({ W0, W1 }); Cobbled.Add(true);
	}
	for (const auto& Rr : Roads)
	{
		const FVector2D P = ToM(Rr.Key), Q = ToM(Rr.Value);
		Box(FVector2D(FMath::Min(P.X, Q.X), FMath::Min(P.Y, Q.Y)) - FVector2D(1.6f * Sc), FVector2D(FMath::Max(P.X, Q.X), FMath::Max(P.Y, Q.Y)) + FVector2D(1.6f * Sc), FLinearColor(0.32f, 0.24f, 0.12f, 0.45f));
	}
	for (int32 I = 0; I < Roads.Num(); ++I)
		if (!TownTiled(Cobbled[I] ? FName(TEXT("mapc_cobble")) : FName(TEXT("mapc_dirt")), ToM(Roads[I].Key), ToM(Roads[I].Value), Roads[I].Key, Roads[I].Value, Cobbled[I] ? Rep * 0.25f : Rep * 0.5f,
			Cobbled[I] ? FLinearColor::White : FLinearColor(0.95f, 0.82f, 0.62f, 1.f)))
		{
			const FVector2D P = ToM(Roads[I].Key), Q = ToM(Roads[I].Value);
			Box(FVector2D(FMath::Min(P.X, Q.X), FMath::Min(P.Y, Q.Y)), FVector2D(FMath::Max(P.X, Q.X), FMath::Max(P.Y, Q.Y)), FLinearColor(0.72f, 0.58f, 0.38f, 1.f));
		}
	// the wall: grey stone along its outline's edges, a dark edge each side
	for (int32 Pass = 0; Pass < 2; ++Pass)
		for (int32 I = 0, J = Ol.Num() - 1; I < Ol.Num(); J = I++)
		{
			const FVector2D Dn = (Ol[I] - Ol[J]).GetSafeNormal(), Nn(-Dn.Y, Dn.X);
			const float Wt = Pass == 0 ? 330.f : 260.f;
			const TArray<FVector2D> Wq = { Ol[J] - Dn * Wt + Nn * Wt, Ol[I] + Dn * Wt + Nn * Wt, Ol[I] + Dn * Wt - Nn * Wt, Ol[J] - Dn * Wt - Nn * Wt };
			TArray<FVector2D> Sq; for (const FVector2D& Q : Wq) Sq.Add(ToM(Q));
			TownTris(TEXT("mapc_wallstone"), Sq, Wq, { 0, 1, 2, 0, 2, 3 }, Rep * 0.15f, Pass == 0 ? FLinearColor(0.16f, 0.15f, 0.14f, 0.9f) : FLinearColor::White);
		}
	// the gardens (dark soil, rows of green) and the pens (trodden earth in a fence) by the homes (the third list)
	auto RectW = [&](const FVector& C, const FVector2D& H, float Yw)
	{
		const FVector2D Ax(FMath::Cos(FMath::DegreesToRadians(Yw)), FMath::Sin(FMath::DegreesToRadians(Yw))), Ay(-Ax.Y, Ax.X), C2(C.X, C.Y);
		return TArray<FVector2D>{ C2 - Ax * H.X - Ay * H.Y, C2 + Ax * H.X - Ay * H.Y, C2 + Ax * H.X + Ay * H.Y, C2 - Ax * H.X + Ay * H.Y };
	};
	for (const ARDSection::FTownGarden& Gd : S->TownGardens)
	{
		const TArray<FVector2D> Wq = RectW(Gd.At, Gd.Half, Gd.Yaw);
		TArray<FVector2D> Sq; for (const FVector2D& Q : Wq) Sq.Add(ToM(Q));
		TownTris(TEXT("mapc_dirt"), Sq, Wq, { 0, 1, 2, 0, 2, 3 }, Rep * 0.3f, FLinearColor(0.42f, 0.28f, 0.14f, 1.f));
		const FVector2D Ax = (Wq[1] - Wq[0]) / 6.f, Ay = (Wq[3] - Wq[0]);
		for (int32 Rw = 0; Rw < 3; ++Rw) for (int32 Cl = 0; Cl < 6; ++Cl)
			SoftDot(ToM(Wq[0] + Ax * (Cl + 0.5f) + Ay * ((Rw + 0.5f) / 3.f)), FMath::Max(1.5f, 45.f * K), FLinearColor(0.22f, 0.45f, 0.12f, 0.95f));
	}
	for (const ARDSection::FTownPen& Pn : S->TownPens)
	{
		const TArray<FVector2D> Wq = RectW(Pn.At, Pn.Half, Pn.Yaw);
		TArray<FVector2D> Sq; for (const FVector2D& Q : Wq) Sq.Add(ToM(Q));
		TownTris(TEXT("mapc_dirt"), Sq, Wq, { 0, 1, 2, 0, 2, 3 }, Rep * 0.5f, FLinearColor(0.85f, 0.72f, 0.52f, 1.f));
		for (int32 I = 0; I < 4; ++I) DrawLine(Sq[I].X, Sq[I].Y, Sq[(I + 1) % 4].X, Sq[(I + 1) % 4].Y, FLinearColor(0.35f, 0.22f, 0.1f, 1.f), FMath::Max(1.f, 1.4f * Sc));
	}
	// the watch's patrol: a gold dashed line along the lane (the militia walk it), a tile in from the wall
	{
		const float Dash = 7.f * Sc, Gap = 6.f * Sc;
		for (int32 I = 0, J = Ol.Num() - 1; I < Ol.Num(); J = I++)
		{
			const FVector2D Da = ToM(Ol[J] + (Bc - Ol[J]).GetSafeNormal() * TS), Db = ToM(Ol[I] + (Bc - Ol[I]).GetSafeNormal() * TS);
			const float Len = FVector2D::Distance(Da, Db);
			const FVector2D Dir = (Db - Da) / FMath::Max(Len, 1.f);
			for (float T = 0.f; T < Len; T += Dash + Gap)
			{
				const FVector2D Pa = Da + Dir * T, Pb = Da + Dir * FMath::Min(T + Dash, Len);
				DrawLine(Pa.X, Pa.Y, Pb.X, Pb.Y, FLinearColor(0.35f, 0.2f, 0.02f, 0.6f), 3.6f * Sc);
				DrawLine(Pa.X, Pa.Y, Pb.X, Pb.Y, FLinearColor(1.f, 0.78f, 0.18f, 1.f), 2.2f * Sc);
			}
		}
	}
	}
	// what stands on the map, drawn from the top of the sheet down (the nearer covers the farther, as in the painting)
	struct FMapPic { FName Name; FVector2D A, B; bool bFlip; bool bShadow; };
	TArray<FMapPic> Pics;
	TArray<FRDTMapLabel> Pending;
	TArray<FBox2D> Taken;
	// (on the picture from above the buildings are themselves: no painted pictures over them; the labels light on a dark halo)
	const FLinearColor Ink = bSat ? FLinearColor(0.99f, 0.95f, 0.84f, 1.f) : FLinearColor(0.18f, 0.10f, 0.04f, 1.f);
	auto Pic = [&](FName Name, const FVector2D& Ctr, float HalfW, float HalfH, bool bFlip, bool bShadow)
	{
		if (bSat) return;
		Pics.Add({ Name, Ctr - FVector2D(HalfW, HalfH), Ctr + FVector2D(HalfW, HalfH), bFlip, bShadow });
	};
	auto Label = [&](const FString& Text, const FVector2D& P, float Size, const FString& Key)
	{
		if (Text.IsEmpty()) return;
		Pending.Add({ Text, P, Size, Ink, ERDType::Label, 0.92f });
		TownLabels.Add(FString::Printf(TEXT("%s|%s"), *Key, *Text));
	};
	// (the buildings: each its picture on its footprint, a little larger (a roof's eaves); homes by their style)
	for (const ARDSection::FTownBld& Bd : S->TownBlds)
	{
		FVector2D W0, W1; TileW(FIntRect(Bd.Min, Bd.Max), W0, W1);
		const FVector2D P = ToM(W0), Q = ToM(W1), Ctr = (P + Q) * 0.5f;
		const float Hw = FMath::Abs(Q.X - P.X) * 0.5f, Hh = FMath::Abs(Q.Y - P.Y) * 0.5f;
		FName Nm;
		switch (Bd.Kind)
		{
		case TK_Castle: Nm = TEXT("mapc_castle"); break;
		case TK_Smithy: Nm = TEXT("mapc_smithy"); break;
		case TK_Store: Nm = TEXT("mapc_store"); break;
		case TK_Healer: Nm = TEXT("mapc_healer"); break;
		case TK_Temple: Nm = TEXT("mapc_temple"); break;
		case TK_Storehouse: Nm = TEXT("mapc_storehouse"); break;
		case TK_Tavern: Nm = TEXT("mapc_tavern"); break;
		case TK_Chapel: Nm = TEXT("mapc_chapel"); break;
		case TK_Barracks: Nm = TEXT("mapc_barracks"); break;
		case TK_Witch: Nm = TEXT("mapc_witch"); break;
		case TK_Cathedral: Nm = TEXT("mapc_temple"); break;
		case TK_Monastery: Nm = TEXT("mapc_chapel"); break;
		case TK_Foundry: Nm = TEXT("mapc_castle"); break;
		case TK_Workshop: Nm = TEXT("mapc_smithy"); break;
		case TK_SluiceHouse: case TK_Warehouse: Nm = TEXT("mapc_storehouse"); break;
		case TK_Spire: Nm = TEXT("mapc_castle"); break;
		case TK_Library: case TK_Laboratory: case TK_Study: case TK_Meditation: Nm = TEXT("mapc_witch"); break;
		case TK_Research: Nm = TEXT("mapc_castle"); break;
		case TK_SkyTower: Nm = TEXT("mapc_barracks"); break;
		case TK_Office: Nm = TEXT("mapc_storehouse"); break;
		case TK_Shop: Nm = TEXT("mapc_store"); break;
		default: Nm = Bd.State == 1 ? FName(TEXT("mapc_burned")) : Bd.State == 2 ? FName(TEXT("mapc_boarded")) : Bd.Style == 1 ? FName(TEXT("mapc_home3")) : Bd.Style == 2 ? FName(TEXT("mapc_home1")) : FName(TEXT("mapc_home2")); break;
		}
		const float Grow = Bd.Kind == TK_Castle ? 1.12f : Bd.Kind == TK_Home ? 1.3f : 1.22f;
		Pic(Nm, Ctr, FMath::Max(Hw, Hh * 0.8f) * Grow, FMath::Max(Hh, Hw * 0.8f) * Grow, (Bd.Seed & 1u) != 0u && Bd.Kind != TK_Castle, true);
		if (Bd.Kind != TK_Home) Taken.Add(FBox2D(Ctr - FVector2D(Hw, Hh) * 0.9f, Ctr + FVector2D(Hw, Hh) * 0.9f));
		Label(RDTLabelOf(Bd.Kind), Ctr, FMath::Max(Hw, Hh), Nm.ToString());
	}
	// (the castle's round towers)
	for (const FVector& Tw : S->CastleTowers) Pic(TEXT("mapc_tower"), ToM(W2(Tw)), 380.f * K, 380.f * K, false, true);
	// (the wall's towers, the gate; the outdoors)
	FVector2D Stalls = FVector2D::ZeroVector; int32 NStalls = 0;
	for (const ARDSection::FTownSpot& Sp : S->TownSpots)
	{
		const FVector2D P = ToM(W2(Sp.At));
		auto One = [&](const TCHAR* Nm, float Cm_, const TCHAR* Lb) { Pic(Nm, P, Cm_ * K, Cm_ * K, false, true); if (Lb) { Taken.Add(FBox2D(P - FVector2D(Cm_ * K * 0.7f), P + FVector2D(Cm_ * K * 0.7f))); Label(Lb, P, Cm_ * K, Nm); } };
		switch (Sp.Kind)
		{
		case TS_Tower: One(TEXT("mapc_tower"), 420.f, nullptr); break;
		case TS_Gate: One(TEXT("mapc_gate"), 650.f, Gen->bWild ? TEXT("GATE · the wilds") : TEXT("GATE · barred")); break;
		case TS_Well: One(TEXT("mapc_well"), 330.f, TEXT("WELL")); break;
		case TS_Board: One(TEXT("mapc_board"), 330.f, TEXT("QUEST BOARD · bounties")); break;
		case TS_Circle: One(TEXT("mapc_circle"), 760.f, TEXT("TELEPORT CIRCLE")); break;
		case TS_Graveyard: One(TEXT("mapc_graveyard"), 1500.f, TEXT("GRAVEYARD")); break;
		case TS_Mill: One(TEXT("mapc_mill"), 1050.f, TEXT("MILL")); break;
		case TS_Still: One(TEXT("mapc_still"), 330.f, TEXT("STILL")); break;
		case TS_Tent: One(TEXT("mapc_tent"), 300.f, nullptr); break;
		case TS_Stall: Stalls += W2(Sp.At); ++NStalls; break;
		default: break;
		}
	}
	if (NStalls > 0)
	{
		const FVector2D P = ToM(Stalls / NStalls);
		Pic(TEXT("mapc_market"), P, 900.f * K, 900.f * K, false, true);
		Label(TEXT("MARKET"), P, 900.f * K, TEXT("mapc_market"));
	}
	// (the trees and bushes where they stand)
	for (const FVector& Gr : S->TownGreens)
	{
		const int32 Kd = FMath::RoundToInt(Gr.Z);
		const FName Nm = Kd == 4 ? FName(TEXT("mapc_bush")) : FName(*FString::Printf(TEXT("mapc_tree%d"), FMath::Clamp(Kd, 1, 3)));
		// (drawn larger than their crowns, as the painting's trees are)
		const float R = Kd == 4 ? 300.f : Kd == 3 ? 520.f : 700.f;
		Pic(Nm, ToM(FVector2D(Gr.X, Gr.Y)), R * K, R * K, ((int32)Gr.X ^ (int32)Gr.Y) & 1, true);
	}
	Pics.StableSort([](const FMapPic& X, const FMapPic& Y) { return X.B.Y < Y.B.Y; });
	for (const FMapPic& Pc : Pics)
	{
		// (a soft shadow under it, down and to the right, as the painting's light falls)
		const FVector2D C = (Pc.A + Pc.B) * 0.5f, Hs = (Pc.B - Pc.A) * 0.5f;
		if (Pc.bShadow) SoftDot(C + FVector2D(Hs.X * 0.18f, Hs.Y * 0.42f), FMath::Max(Hs.X, Hs.Y) * 0.75f, FLinearColor(0.05f, 0.08f, 0.02f, 0.28f));
		if (!UI.Fit(Pc.Name, Pc.A, Pc.B, FLinearColor::White, Pc.bFlip))
		{
			const FName Old = Pc.Name.ToString().StartsWith(TEXT("mapc_tree")) || Pc.Name == FName(TEXT("mapc_bush")) ? NAME_None : FName(*Pc.Name.ToString().Replace(TEXT("mapc_"), TEXT("mapicon_")));
			if (Old.IsNone() || !UI.Fit(Old, Pc.A, Pc.B)) SoftDot(C, FMath::Max(Hs.X, Hs.Y) * 0.5f, FLinearColor(0.25f, 0.45f, 0.15f, 0.8f));
		}
	}
	{
		FVector Sq; Gen->GetTownPlace(TEXT("square"), Sq);
		const FVector2D P = ToM(W2(Sq));
		Pending.Insert({ TEXT("TOWN SQUARE"), P, 4.f * Sc, bSat ? Ink : FLinearColor(0.18f, 0.10f, 0.04f, 0.95f), ERDType::Title, 0.95f }, 0);
		TownLabels.Add(TEXT("square|TOWN SQUARE"));
	}
	// (the watch's patrol, written once on the lane; not on the picture from above, which draws no patrol)
	if (!bSat)
	{
		const FVector2D P = ToM(Ol[Ol.Num() / 3] + (Bc - Ol[Ol.Num() / 3]).GetSafeNormal() * TS * 1.5f);
		Pending.Add({ TEXT("Watch patrol"), P, 2.f * Sc, FLinearColor(0.45f, 0.28f, 0.04f, 1.f), ERDType::Text, 0.9f });
	}
	// the people who give quests (the third list of 2026-11-02: "it is not necessary to have all the quest giver names on the
	// overhead map, but there should be some kind of symbol for where they are"): every giver of the town's quests marked by a
	// wax seal in a gold ring, with "!" when one is offered to her, "?" when one is ready to turn in, else a quill's dot; their
	// names only when the map is zoomed in 2.5 times or more. The quest board's seal is on the board.
	const TArray<FString> Ql = Gen->GetQuestLinesHere();
	TSet<FString> Givers;
	for (const FRDQuestDef& Q : Gen->Quests) if (Gen->IsQuestHere(Q)) Givers.Add(Q.Giver.ToString());          // (this town's givers only)
	TownQuestSeals = 0;
	auto Seal = [&](const FVector2D& P, const FString& Mark0)
	{
		const FString Mark = Mark0.IsEmpty() ? FString(TEXT("·")) : Mark0;
		SoftDot(P + FVector2D(1.5f, 2.f) * Sc, 14.f * Sc, FLinearColor(0.05f, 0.03f, 0.01f, 0.45f));
		SoftDot(P, 13.f * Sc, FLinearColor(0.95f, 0.72f, 0.25f, 1.f));
		SoftDot(P, 10.f * Sc, FLinearColor(0.58f, 0.07f, 0.04f, 1.f));
		float Tw, Th; UI.TextSize(Mark, Tw, Th, Medium, Sc * 0.95f, ERDType::Title);
		UI.Text(Mark, FLinearColor(1.f, 0.9f, 0.55f, 1.f), P.X - Tw * 0.5f, P.Y - Th * 0.5f, Medium, Sc * 0.95f, ERDType::Title);
		Taken.Add(FBox2D(P - FVector2D(14.f * Sc), P + FVector2D(14.f * Sc)));
		++TownQuestSeals;
	};
	for (const ARDTownsfolk* T : Gen->TownPeople)
	{
		if (!IsValid(T)) continue;
		const FString RoleName = StaticEnum<ERDTownRole>()->GetNameStringByValue((int64)T->TownRole);
		if (!Givers.Contains(RoleName)) continue;
		const FVector2D P = ToM(FVector2D(T->GetActorLocation()));
		Seal(P, RDTQuestMark(Ql, RoleName));
		TownLabels.Add(FString::Printf(TEXT("seal|%s"), *RoleName));
		if (Zm >= 2.5f) Pending.Add({ T->Title, P, 13.f * Sc, bSat ? FLinearColor(1.f, 0.84f, 0.62f, 1.f) : FLinearColor(0.5f, 0.06f, 0.03f, 1.f), ERDType::Text, 0.85f });
	}
	if (Givers.Contains(TEXT("Board")))
		for (const ARDSection::FTownSpot& Sp : S->TownSpots)
			if (Sp.Kind == TS_Board) { Seal(ToM(W2(Sp.At)) + FVector2D(0.f, -16.f * Sc), RDTQuestMark(Ql, TEXT("Board"))); TownLabels.Add(TEXT("seal|Board")); break; }
	// the labels: each where it covers no picture of a trade and no label before it, on a halo of the parchment's colour
	PlaceTownMapLabels(Pending, Taken, Sc, bSat ? FLinearColor(0.02f, 0.02f, 0.025f, 0.62f) : FLinearColor(0.95f, 0.89f, 0.74f, 0.62f));
	if (!S->MistgateAt.IsZero()) MistMark(10, ToM(W2(S->MistgateAt)), 7.f * Sc);
	{
		const FVector2D P = ToM(FVector2D(L.X, L.Y));
		SoftDot(P, 16.f * Sc, FLinearColor(0.8f, 0.05f, 0.03f, 0.4f));
		DrawPlayerArrow(P, Yaw - 90.f, 11.f * Sc);
		MapArrow = P; bMapArrow = true;
	}
	// (zoomed or moved, the map spills past the sheet: dark outside it, and the scroll's torn edge and rolls drawn over the
	// map's edge again (mapc_scroll_edge, bs_scroll.py); the canvas has no clip of its own)
	if (bZoomed)
	{
		// (the picture from above stops at its gold frame; the scroll's torn edge stands a little out from the sheet)
		const FVector2D Sa = bSat ? A : A - FVector2D(Ms * 0.03f), Sb = bSat ? B : B + FVector2D(Ms * 0.03f);
		const FLinearColor Dk(0.015f, 0.012f, 0.01f, 1.f);
		Box(FVector2D(0, 0), FVector2D(Canvas->ClipX, Sa.Y + 2.f), Dk);
		Box(FVector2D(0, Sb.Y - 2.f), FVector2D(Canvas->ClipX, Canvas->ClipY), Dk);
		Box(FVector2D(0, Sa.Y), FVector2D(Sa.X + 2.f, Sb.Y), Dk);
		Box(FVector2D(Sb.X - 2.f, Sa.Y), FVector2D(Canvas->ClipX, Sb.Y), Dk);
		if (bSat || !UI.Fit(TEXT("mapc_scroll_edge"), Sa, Sb)) Frame(A, B, FLinearColor(0.30f, 0.20f, 0.10f, 0.95f), 6.f * Sc);
	}
	// (the picture from above framed in gold, as the dungeon's maps; a dark band under the title and over the key)
	if (bSat)
	{
		Frame(A, B, FLinearColor(0.85f, 0.66f, 0.28f, 0.95f), 2.f * Sc);
		Box(FVector2D(A.X, A.Y), FVector2D(B.X, A.Y + Ms * 0.075f), FLinearColor(0.02f, 0.02f, 0.025f, 0.72f));
		Box(FVector2D(A.X, B.Y - Ms * 0.07f), FVector2D(B.X, B.Y), FLinearColor(0.02f, 0.02f, 0.025f, 0.72f));
	}
	// the title in gold over a dark shadow, a gold rule under it; the compass rose; the key
	const FString Title = Gen->TownName.ToUpper();
	const float TK = Sc * 2.8f;
	float Tw, Th; UI.TextSize(Title, Tw, Th, Medium, TK, ERDType::Title);
	const FVector2D Tp(A.X + Ms * 0.04f, A.Y + Ms * 0.015f);
	for (const FVector2D& O : { FVector2D(2.f, 2.5f), FVector2D(-1.f, 1.f), FVector2D(1.f, -1.f) })
		UI.Text(Title, FLinearColor(0.2f, 0.11f, 0.03f, 0.85f), Tp.X + O.X * Sc, Tp.Y + O.Y * Sc, Medium, TK, ERDType::Title);
	UI.Text(Title, FLinearColor(0.98f, 0.78f, 0.32f, 1.f), Tp.X, Tp.Y, Medium, TK, ERDType::Title);
	DrawLine(Tp.X, Tp.Y + Th + 4.f * Sc, Tp.X + Tw, Tp.Y + Th + 4.f * Sc, FLinearColor(0.85f, 0.65f, 0.25f, 0.95f), 1.6f * Sc);
	SoftDot(FVector2D(Tp.X + Tw * 0.5f, Tp.Y + Th + 4.f * Sc), 4.f * Sc, FLinearColor(0.95f, 0.75f, 0.3f, 1.f));
	{
		const float Cr = Ms * 0.062f;
		const FVector2D Cc(B.X - Ms * 0.06f, B.Y - Ms * 0.085f);
		if (!UI.Fit(TEXT("mapc_compass"), Cc - FVector2D(Cr), Cc + FVector2D(Cr)))
			DrawLine(Cc.X, Cc.Y + Cr, Cc.X, Cc.Y - Cr, FLinearColor(0.25f, 0.13f, 0.05f, 1.f), 2.f * Sc);
		float Nw, Nh; UI.TextSize(TEXT("N"), Nw, Nh, Medium, Sc * 1.2f, ERDType::Title);
		UI.Text(TEXT("N"), bSat ? Ink : FLinearColor(0.2f, 0.11f, 0.03f, 1.f), Cc.X - Nw * 0.5f, Cc.Y - Cr - Nh - 2.f * Sc, Medium, Sc * 1.2f, ERDType::Title);
	}
	const bool bPad = Gen->bCasterControls && Gen->GetPlayerCombat() && Gen->GetPlayerCombat()->IsUsingGamepad();
	const FString Clock = Gen->bDayNight ? FString::Printf(TEXT("      day %d · %s"), Gen->GetTownDay(), *Gen->GetTownClock()) : FString();
	const FString Key = FString::Printf(TEXT("%s close the map      seal  a quest giver:  !  a quest for you   ?  to turn in%s"), bPad ? TEXT("Back") : TEXT("M"), *Clock);
	const FString Key2 = bPad ? FString::Printf(TEXT("right stick zoom (%.1fx)      D-pad move      R3 back to the whole town"), Zm)
	                          : FString::Printf(TEXT("wheel or + / -  zoom (%.1fx)      drag or arrow keys  move      C  the whole town"), Zm);
	UI.TextSize(Key, Tw, Th, Small, Sc);
	UI.Text(Key, bSat ? Ink : FLinearColor(0.2f, 0.11f, 0.03f, 1.f), Cm.X - Tw * 0.5f, B.Y - Ms * 0.055f, Small, Sc);
	UI.TextSize(Key2, Tw, Th, Small, Sc);
	UI.Text(Key2, bSat ? Ink : FLinearColor(0.2f, 0.11f, 0.03f, 1.f), Cm.X - Tw * 0.5f, B.Y - Ms * 0.055f + Th * 1.15f, Small, Sc);
	MapView = Mid;
	TownMapZoomDrawn = Zm;
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
	const TArray<FString> Ql = Gen->GetQuestLinesHere();
	for (const ARDTownsfolk* T : Gen->TownPeople)
	{
		if (!IsValid(T)) continue;
		const FVector Head = T->GetActorLocation() + FVector(0, 0, 115.f);
		const float D = FVector::Dist(Head, Me->GetActorLocation());
		if (D > 1400.f || FVector::DotProduct(Head - Cam, Fw) < 50.f) continue;
		const FString RoleName = StaticEnum<ERDTownRole>()->GetNameStringByValue((int64)T->TownRole);
		const FString Mark = RDTQuestMark(Ql, RoleName);
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
			else if (Ln.Act == TEXT("withdraw"))
			{
				// (a stacked line's label carries its count: the thing is the stored one its line takes back)
				const URDGameInstance* Gi = URDGameInstance::Of(Gen);
				const int32 Si = FCString::Atoi(*Ln.Arg);
				Item = Gi && Gi->StashThings.IsValidIndex(Si) ? Gi->StashThings[Si] : FName(*Ln.Label);
			}
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
