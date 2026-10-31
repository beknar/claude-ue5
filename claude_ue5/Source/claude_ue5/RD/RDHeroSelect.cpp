#include "RD/RDHeroSelect.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDUIArt.h"
#include "RD/RDInputSim.h"
#include "Engine/Canvas.h"
#include "Engine/Texture2D.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "InputKeyEventArgs.h"
#include "Kismet/GameplayStatics.h"

/** a hero's name as the menu shows it: her title ("MARTIAL ARTIST"), else her name */
static FString RDHSShown(const FRDHeroDef& H) { return (H.Title.IsEmpty() ? H.Name.ToString() : H.Title).ToUpper(); }

DEFINE_LOG_CATEGORY_STATIC(LogRDHeroSelect, Log, All);

// ------------------------------------------------------------------------------------------------ game modes
UClass* ARDHeroGameMode::GetDefaultPawnClassForController_Implementation(AController* InController)
{
	// (the level's actors are there when the player is spawned: the generator says whose pawn it is)
	for (TActorIterator<ARDDungeonGenerator> It(GetWorld()); It; ++It)
		if (const FRDHeroDef* H = It->FindHero(It->ChosenHero()))
			if (H->PawnClass) return H->PawnClass;
	return Super::GetDefaultPawnClassForController_Implementation(InController);
}

ARDHeroSelectGameMode::ARDHeroSelectGameMode()
{
	DefaultPawnClass = nullptr;
	HUDClass = ARDHeroSelectHUD::StaticClass();
}

// ------------------------------------------------------------------------------------------------ the turntable
ARDHeroSelect::ARDHeroSelect()
{
	PrimaryActorTick.bCanEverTick = true;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}

void ARDHeroSelect::BeginPlay()
{
	Super::BeginPlay();
	// (the menu opened again from the dungeon shows the hero played last)
	int32 Start = 0;
	if (const AGameModeBase* GM = GetWorld()->GetAuthGameMode())
	{
		const FString Opt = UGameplayStatics::ParseOption(GM->OptionsString, TEXT("Hero"));
		for (int32 I = 0; I < Heroes.Num(); ++I) if (Heroes[I].Name.ToString() == Opt) Start = I;
	}
	Index = -1;
	Show(Start);
	UE_LOG(LogRDHeroSelect, Log, TEXT("RDSELECT %d heroes, showing %s"), Heroes.Num(), *GetHeroName().ToString());
}

void ARDHeroSelect::SetFigureShown(AActor* Figure, bool bShown)
{
	if (!Figure) return;
	Figure->SetActorHiddenInGame(!bShown);
	TArray<AActor*> Attached;
	Figure->GetAttachedActors(Attached, true, true);
	for (AActor* A : Attached) if (A) A->SetActorHiddenInGame(!bShown);
}

void ARDHeroSelect::Show(int32 I)
{
	const int32 N = Heroes.Num();
	if (N == 0) return;
	I = (I % N + N) % N;
	if (I == Index) return;
	Index = I;
	for (int32 K = 0; K < Figures.Num(); ++K) SetFigureShown(Figures[K], K == Index);
	// (each hero is first seen from the front, then turns)
	Yaw = 0.f;
	ShownTime = GetWorld()->GetTimeSeconds();
}

bool ARDHeroSelect::SimulateKey(FKey Key, bool bDown)
{
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	return PC && PC->InputKey(FInputKeyEventArgs::CreateSimulated(Key, bDown ? IE_Pressed : IE_Released, bDown ? 1.f : 0.f));
}

bool ARDHeroSelect::IsFigureShown(int32 I) const
{
	const AActor* F = Figures.IsValidIndex(I) ? Figures[I].Get() : nullptr;
	if (!F || F->IsHidden()) return false;
	TArray<AActor*> Attached;
	F->GetAttachedActors(Attached, true, true);
	for (const AActor* A : Attached) if (A && A->IsHidden()) return false;
	return true;
}

bool ARDHeroSelect::Confirm()
{
	if (TargetLevel.IsEmpty() || !Heroes.IsValidIndex(Index)) return false;
	const FString Options = FString::Printf(TEXT("Hero=%s"), *Heroes[Index].Name.ToString());
	Opened = FString::Printf(TEXT("%s?%s"), *TargetLevel, *Options);
	ConfirmTime = GetWorld()->GetTimeSeconds();
	UE_LOG(LogRDHeroSelect, Log, TEXT("RDSELECT start: %s%s"), *Opened, bStayOnConfirm ? TEXT(" (stays: the reel)") : TEXT(""));
	// (mistward: the game's own mode back before the dungeon: the menu's free pointer would stay on, and the camera would
	// turn only while a button is held)
	if (bMouseUI && !bStayOnConfirm)
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0)) { PC->SetShowMouseCursor(false); PC->SetInputMode(FInputModeGameOnly()); }
	if (!bStayOnConfirm) UGameplayStatics::OpenLevel(this, FName(*TargetLevel), true, Options);
	return true;
}

void ARDHeroSelect::Tick(float Dt)
{
	Super::Tick(Dt);
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
	{
		if (!bViewSet && Camera)
		{
			PC->SetViewTarget(Camera);
			PC->bShowMouseCursor = true; PC->bEnableClickEvents = true; PC->bEnableMouseOverEvents = true;
			// (mistward: the pointer stays shown and free: the game's mode hid it and captured it on the first click)
			if (bMouseUI)
			{
				AddTickPrerequisiteActor(PC);           // (a click read the frame after the controller took it in, every frame)
				FInputModeGameAndUI M;
				M.SetHideCursorDuringCapture(false);
				M.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
				PC->SetInputMode(M);
			}
			bViewSet = true;
		}
		if (bMouseUI) TickPointer(PC);
		auto Pressed = [PC](std::initializer_list<FKey> Keys) { for (const FKey& K : Keys) if (PC->WasInputKeyJustPressed(K)) return true; return false; };
		if (Pressed({ EKeys::A, EKeys::Left, EKeys::MouseScrollUp, EKeys::Gamepad_DPad_Left, EKeys::Gamepad_LeftShoulder })) Step(-1);
		if (Pressed({ EKeys::D, EKeys::Right, EKeys::MouseScrollDown, EKeys::Gamepad_DPad_Right, EKeys::Gamepad_RightShoulder })) Step(1);
		// (the left stick: a step when pushed, then one every 0.35 s while held)
		const float Sx = PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftX);
		if (FMath::Abs(Sx) > 0.6f)
		{
			const float Now = GetWorld()->GetTimeSeconds();
			if (Now > StickRepeat) { Step(Sx > 0.f ? 1 : -1); StickRepeat = Now + 0.35f; }
		}
		else StickRepeat = 0.f;
		if (Pressed({ EKeys::Enter, EKeys::SpaceBar, EKeys::Gamepad_FaceButton_Bottom, EKeys::Gamepad_Special_Right })) Confirm();
		// (which device the keys on the screen are for)
		static const FKey PadKeys[] = { EKeys::Gamepad_FaceButton_Bottom, EKeys::Gamepad_DPad_Left, EKeys::Gamepad_DPad_Right, EKeys::Gamepad_LeftShoulder,
			EKeys::Gamepad_RightShoulder, EKeys::Gamepad_Special_Right };
		static const FKey KeyKeys[] = { EKeys::A, EKeys::D, EKeys::Left, EKeys::Right, EKeys::Enter, EKeys::SpaceBar, EKeys::LeftMouseButton };
		for (const FKey& K : PadKeys) if (PC->IsInputKeyDown(K)) bUsingGamepad = true;
		if (FMath::Abs(Sx) > 0.3f) bUsingGamepad = true;
		for (const FKey& K : KeyKeys) if (PC->IsInputKeyDown(K)) bUsingGamepad = false;
	}
	// the turntable turns, and she with it
	Yaw += TurnRate * Dt; Turned += TurnRate * Dt;
	const FRotator R(0.f, FrontYaw + Yaw, 0.f);
	if (Turntable) Turntable->SetActorRotation(R);
	if (Figures.IsValidIndex(Index) && Figures[Index]) Figures[Index]->SetActorRotation(R);
}

void ARDHeroSelect::TickPointer(APlayerController* PC)
{
	float Mx = 0.f, My = 0.f;
	Hovered = NAME_None;
	if (!PC->GetMousePosition(Mx, My)) return;
	const FVector2D M(Mx, My);
	for (const TPair<FName, FBox2D>& B : Buttons) if (B.Value.IsInside(M)) { Hovered = B.Key; break; }
	if (Hovered.IsNone() || !PC->WasInputKeyJustPressed(EKeys::LeftMouseButton)) return;
	++Clicks;
	const FString B = Hovered.ToString();
	if (B == TEXT("Prev")) Step(-1);
	else if (B == TEXT("Next")) Step(1);
	else if (B == TEXT("Start")) Confirm();
	else if (B.StartsWith(TEXT("Hero_")))
	{
		// (her name again, once she is shown: start as her)
		const int32 I = FCString::Atoi(*B.RightChop(5));
		if (I == Index) Confirm(); else Show(I);
	}
}

TArray<FString> ARDHeroSelect::GetButtons() const
{
	TArray<FString> Out;
	for (const TPair<FName, FBox2D>& B : Buttons) Out.Add(FString::Printf(TEXT("%s|%.1f|%.1f|%.1f|%.1f"), *B.Key.ToString(), B.Value.Min.X, B.Value.Min.Y, B.Value.Max.X, B.Value.Max.Y));
	return Out;
}

FString ARDHeroSelect::SlateKey(FKey Key, bool bDown) { return RDInputSim::Key(GetWorld(), Key, bDown); }
FString ARDHeroSelect::SlateMouseMove(FVector2D Pixel) { return RDInputSim::MouseMove(GetWorld(), Pixel); }
FString ARDHeroSelect::SlateMouseButton(FVector2D Pixel, FKey Button, bool bDown) { return RDInputSim::MouseButton(GetWorld(), Pixel, Button, bDown); }
FString ARDHeroSelect::SlateClearView() { return RDInputSim::ClearView(GetWorld()); }
int32 ARDHeroSelect::SlateRestoreView() { return RDInputSim::RestoreView(); }

// ------------------------------------------------------------------------------------------------ the menu's HUD
static const FLinearColor RDHSInk(0.93f, 0.88f, 0.76f, 1.f);
static const FLinearColor RDHSDim(0.68f, 0.66f, 0.60f, 1.f);
static const FLinearColor RDHSLine(0.75f, 0.65f, 0.45f, 0.9f);

void ARDHeroSelectHUD::NotifyHitBoxClick(FName BoxName)
{
	Super::NotifyHitBoxClick(BoxName);
	if (!Sel || Sel->bMouseUI) return;          // (mistward: the menu's own pointer does it, ARDHeroSelect::TickPointer)
	const FString B = BoxName.ToString();
	if (B == TEXT("Prev")) Sel->Step(-1);
	else if (B == TEXT("Next")) Sel->Step(1);
	else if (B == TEXT("Start")) Sel->Confirm();
	else if (B.StartsWith(TEXT("Hero_"))) Sel->Show(FCString::Atoi(*B.RightChop(5)));
}

void ARDHeroSelectHUD::DrawHUD()
{
	Super::DrawHUD();
	if (!Canvas) return;
	if (!Sel) for (TActorIterator<ARDHeroSelect> It(GetWorld()); It; ++It) { Sel = *It; break; }
	if (Sel) Sel->Buttons.Reset();           // (a frame that draws none leaves none behind for the pointer)
	if (!Sel || !Sel->Heroes.IsValidIndex(Sel->GetIndex())) return;
	const FRDHeroDef& H = Sel->Heroes[Sel->GetIndex()];
	const float Sc = Canvas->ClipY / 1080.f, Now = GetWorld()->GetTimeSeconds();
	// (the painted interface where the menu has it: the card's board, framed bars, dividers, plates for the names and
	// START, the arrows)
	ArtDrawn.Reset();
	FRDUIDraw UI; UI.Hud = this; UI.Art = &Sel->UIArt; UI.Drawn = &ArtDrawn; UI.Fonts = &Sel->UIFonts; UI.FontCache = &FontCache;
	auto HeightPx = [&](FName Nm, float Hgt) { const FRDUIArt* Ar = UI.Find(Nm); return Ar ? Hgt / FMath::Max((float)Ar->Texture->GetSizeY(), 1.f) : 0.f; };
	UFont* Small = GEngine->GetSmallFont();
	UFont* Medium = GEngine->GetMediumFont();
	const bool bPad = Sel->bUsingGamepad;
	auto Rect = [&](const FVector2D& A, const FVector2D& B, const FLinearColor& C) { if (B.X > A.X && B.Y > A.Y) DrawRect(C, A.X, A.Y, B.X - A.X, B.Y - A.Y); };
	auto Frame = [&](const FVector2D& A, const FVector2D& B, const FLinearColor& C, float T)
	{
		DrawLine(A.X, A.Y, B.X, A.Y, C, T); DrawLine(B.X, A.Y, B.X, B.Y, C, T); DrawLine(B.X, B.Y, A.X, B.Y, C, T); DrawLine(A.X, B.Y, A.X, A.Y, C, T);
	};
	float Tw, Th;
	// ---- the title
	UI.Text(Sel && !Sel->GameTitle.IsEmpty() ? Sel->GameTitle.ToUpper() : FString(TEXT("RANDOM DUNGEON")), RDHSDim, 80.f * Sc, 44.f * Sc, Small, Sc * 1.3f, ERDType::Label);
	UI.Text(TEXT("CHOOSE YOUR HERO"), RDHSInk, 78.f * Sc, 68.f * Sc, Medium, Sc * 2.1f, ERDType::Title);
	// ---- her card (left)
	const float Fade = FMath::Clamp((Now - Sel->ShownTime) / 0.35f, 0.f, 1.f);
	const FLinearColor Ac(H.Accent.R, H.Accent.G, H.Accent.B, Fade);
	auto Ink = [&](const FLinearColor& C) { return FLinearColor(C.R, C.G, C.B, C.A * Fade); };
	const FVector2D A(80.f * Sc, 160.f * Sc);
	const float X = A.X + 34.f * Sc + (UI.Has(TEXT("panel")) ? 18.f * Sc : 0.f), Wd = 720.f * Sc - X - 30.f * Sc;     // (clear of the board's corner ornaments)
	float Y = 0.f;
	// (laid out twice: once to measure how tall the card is, then drawn on it)
	bool bDraw = false;
	auto Text = [&](const FString& T, const FLinearColor& C, float Tx, float Ty, UFont* F, float K, ERDType R = ERDType::Text) { if (bDraw) UI.Text(T, C, Tx, Ty, F, K, R); };
	auto Fill = [&](const FVector2D& P0, const FVector2D& P1, const FLinearColor& C) { if (bDraw) Rect(P0, P1, C); };
	auto Card = [&]()
	{
	Y = A.Y + 22.f * Sc;
	// (her title, not her name: "MARTIAL ARTIST", not "MARTIALARTIST")
	Text(RDHSShown(H), Ac, X, Y, Medium, Sc * 2.6f, ERDType::Title);
	Y += 74.f * Sc;
	// hit points and mana, as bars against the strongest of the heroes
	float MaxHp = 1.f, MaxMp = 1.f;
	for (const FRDHeroDef& O : Sel->Heroes) { MaxHp = FMath::Max(MaxHp, O.MaxHealth); MaxMp = FMath::Max(MaxMp, O.MaxMana); }
	auto Bar = [&](const TCHAR* Label, float V, float Max, const FLinearColor& C, const FString& Note, FName Frame0, FName Fill0)
	{
		if (UI.Has(Frame0))
		{
			// (the painted frame, its fill as far as she has against the strongest)
			const float Bh = 38.f * Sc;
			Text(Label, Ink(RDHSDim), X, Y + 4.f * Sc, Small, Sc * 1.1f, ERDType::Label);
			const FVector2D F0(X + 120.f * Sc, Y - 6.f * Sc), F1(X + Wd - 80.f * Sc, Y - 6.f * Sc + Bh);
			if (bDraw) UI.Bar(Frame0, Fill0, F0, F1, HeightPx(Frame0, Bh), FMath::Clamp(V / Max, 0.f, 1.f), FLinearColor(1.f, 1.f, 1.f, Fade), FLinearColor(1.f, 1.f, 1.f, Fade));
			Text(Note, Ink(RDHSInk), F1.X + 12.f * Sc, Y + 4.f * Sc, Small, Sc * 1.1f);
			Y += 44.f * Sc;
			return;
		}
		Text(Label, Ink(RDHSDim), X, Y, Small, Sc * 1.1f, ERDType::Label);
		const FVector2D B0(X + 130.f * Sc, Y + 2.f * Sc), B1(X + Wd - 90.f * Sc, Y + 20.f * Sc);
		Fill(B0, B1, FLinearColor(0.08f, 0.08f, 0.1f, 0.9f * Fade));
		Fill(B0, FVector2D(B0.X + (B1.X - B0.X) * FMath::Clamp(V / Max, 0.f, 1.f), B1.Y), FLinearColor(C.R, C.G, C.B, Fade));
		Text(Note, Ink(RDHSInk), B1.X + 12.f * Sc, Y, Small, Sc * 1.1f);
		Y += 32.f * Sc;
	};
	Bar(TEXT("HIT POINTS"), H.MaxHealth, MaxHp, FLinearColor(0.25f, 0.75f, 0.3f), FString::Printf(TEXT("%.0f"), H.MaxHealth), TEXT("bar_health"), TEXT("fill_health"));
	Bar(TEXT("MANA"), H.MaxMana, MaxMp, FLinearColor(0.2f, 0.42f, 0.95f), H.MaxMana > 0.f ? FString::Printf(TEXT("%.0f"), H.MaxMana) : FString(TEXT("none")), TEXT("bar_mana"), TEXT("fill_mana"));
	// her other numbers on one line: the mana that comes back, her bonuses, the roll
	{
		TArray<TPair<FString, FString>> St;
		if (H.MaxMana > 0.f) St.Add({ TEXT("MANA BACK"), FString::Printf(TEXT("%.1f a second"), H.ManaPerSecond) });
		if (H.MeleeBonus > 0.f) St.Add({ TEXT("MELEE"), FString::Printf(TEXT("+%.0f%% damage"), H.MeleeBonus * 100.f) });
		if (H.RangedBonus > 0.f) St.Add({ TEXT("RANGED"), FString::Printf(TEXT("+%.0f%% damage"), H.RangedBonus * 100.f) });
		// (the Martial Artist: her knives' bonus, her dash)
		for (const TPair<FString, float>& P : H.TypeBonus) if (P.Value > 0.f) St.Add({ P.Key.Equals(TEXT("short blades")) ? FString(TEXT("KNIVES")) : P.Key.ToUpper(), FString::Printf(TEXT("+%.0f%% damage"), P.Value * 100.f) });
		if (H.RollClip) St.Add({ TEXT("DODGE"), TEXT("roll") });
		if (H.DashClip) St.Add({ TEXT("DASH"), TEXT("forward") });
		float Sx = X;
		for (const TPair<FString, FString>& P : St)
		{
			Text(P.Key, Ink(RDHSDim), Sx, Y, Small, Sc * 1.05f, ERDType::Label); UI.TextSize(P.Key, Tw, Th, Small, Sc * 1.05f, ERDType::Label); Sx += Tw + 8.f * Sc;
			Text(P.Value, Ac, Sx, Y, Small, Sc * 1.05f); UI.TextSize(P.Value, Tw, Th, Small, Sc * 1.05f); Sx += Tw + 28.f * Sc;
		}
		if (St.Num()) Y += 28.f * Sc;
	}
	Y += 14.f * Sc;
	auto Section = [&](const TCHAR* Head)
	{
		Text(Head, Ac, X, Y, Small, Sc * 1.05f, ERDType::Label);
		Y += 24.f * Sc;
		if (UI.Has(TEXT("divider")))
		{
			// (at its own proportions: a stretch smears its middle gem)
			if (bDraw) UI.Fit(TEXT("divider"), FVector2D(X - 6.f * Sc, Y - 16.f * Sc), FVector2D(X + Wd + 6.f * Sc, Y + 12.f * Sc), FLinearColor(1.f, 1.f, 1.f, Fade));
		}
		else Fill(FVector2D(X, Y - 3.f * Sc), FVector2D(X + Wd, Y - 2.f * Sc), FLinearColor(0.75f, 0.65f, 0.45f, 0.35f * Fade));
		Y += 6.f * Sc;
	};
	// (a line wrapped at the card's width)
	auto Wrapped = [&](const FString& T, float Indent, const FLinearColor& C)
	{
		TArray<FString> Words; T.ParseIntoArray(Words, TEXT(" "));
		FString Cur;
		for (const FString& W : Words)
		{
			const FString Try = Cur.IsEmpty() ? W : Cur + TEXT(" ") + W;
			UI.TextSize(Try, Tw, Th, Small, Sc * 1.2f);
			if (Tw > Wd - Indent && !Cur.IsEmpty()) { Text(Cur, C, X + Indent, Y, Small, Sc * 1.2f); Y += Th + 2.f * Sc; Cur = W; }
			else Cur = Try;
		}
		if (!Cur.IsEmpty()) { UI.TextSize(Cur, Tw, Th, Small, Sc * 1.2f); Text(Cur, C, X + Indent, Y, Small, Sc * 1.2f); Y += Th + 6.f * Sc; }
	};
	Section(TEXT("MAIN ABILITIES"));
	for (const FString& L : H.Abilities)
	{
		Fill(FVector2D(X + 4.f * Sc, Y + 9.f * Sc), FVector2D(X + 11.f * Sc, Y + 16.f * Sc), Ac);
		Wrapped(L, 24.f * Sc, Ink(RDHSInk));
	}
	Y += 10.f * Sc;
	if (!H.Armour.IsEmpty()) { Section(TEXT("ARMOUR")); Wrapped(H.Armour, 0.f, Ink(RDHSInk)); Y += 10.f * Sc; }
	if (!H.StartsWith.IsEmpty() || H.Weapons.Num() > 0)
	{
		Section(TEXT("STARTS WITH"));
		if (!H.StartsWith.IsEmpty()) Wrapped(H.StartsWith, 0.f, Ink(RDHSInk));
		// each weapon and spell: its picture in a slot (painted interface), its name, what a blow or a cast does with her bonus
		const float Rh = 56.f * Sc;
		for (const FRDWeaponDef& W : H.Weapons)
		{
			float Tx = X;
			if (UI.Has(W.Icon))
			{
				if (bDraw)
				{
					const FVector2D S0(X, Y), S1(X + Rh, Y + Rh);
					if (!UI.Fit(TEXT("slot"), S0, S1, FLinearColor(1.f, 1.f, 1.f, Fade))) { Rect(S0, S1, FLinearColor(0.03f, 0.035f, 0.05f, 0.8f * Fade)); Frame(S0, S1, Ink(RDHSLine), 1.f * Sc); }
					UI.Fit(W.Icon, S0 + FVector2D(8.f * Sc), S1 - FVector2D(8.f * Sc), FLinearColor(1.f, 1.f, 1.f, Fade));
				}
				Tx = X + Rh + 14.f * Sc;
			}
			float Bonus = !W.bSpell ? H.MeleeBonus : (W.BoltMesh ? H.RangedBonus : 0.f);
			if (!W.bSpell || W.BoltMesh) if (const float* Tb = H.TypeBonus.Find(W.WeaponType)) Bonus += *Tb;
			FString What = !W.bSpell ? FString::Printf(TEXT("%.0f damage a blow, reach %.1f m"), W.Damage * (1.f + Bonus), W.Reach / 100.f)
			                         : FString::Printf(TEXT("%.0f damage a %s, flies %.0f m"), W.Damage * (1.f + Bonus), W.BoltMesh ? TEXT("bolt") : TEXT("cast"), W.Reach / 100.f);
			if (W.ManaCost > 0.f) What += FString::Printf(TEXT(", %.0f mana"), W.ManaCost);
			// (a summoning is no bolt: "0 damage a cast, flies 14 m" said nothing of what it does)
			if (W.ManaShare > 0.f)
				What = FMath::IsNearlyEqual(W.ManaShare, 0.5f) ? FString::Printf(TEXT("calls fighters to her side, half her mana (%.0f)"), W.ManaCost)
				                                               : FString::Printf(TEXT("calls fighters to her side, %.0f%% of her mana (%.0f)"), W.ManaShare * 100.f, W.ManaCost);
			Text(W.Name.ToString().ToUpper(), Ink(RDHSInk), Tx, Y + 6.f * Sc, Small, Sc * 1.25f, ERDType::Title);
			Text(What, Ink(RDHSDim), Tx, Y + 31.f * Sc, Small, Sc * 1.05f);
			Y += Rh + 8.f * Sc;
		}
	}
	};
	Card();
	const FVector2D B(720.f * Sc, FMath::Min(Y + 18.f * Sc, Canvas->ClipY - 170.f * Sc));
	if (const FRDUIArt* Pa = UI.Find(TEXT("panel")))
	{
		// (the painted board reaches beyond the card: its frame sits round the text)
		const float Ext = 32.f * Sc;
		UI.Nine(TEXT("panel"), A - FVector2D(Ext), B + FVector2D(Ext), Ext * 1.6f / FMath::Max((float)Pa->Border.X * Pa->Texture->GetSizeX(), 1.f));
	}
	else
	{
		Rect(A, B, FLinearColor(0.03f, 0.035f, 0.05f, 0.82f));
		Frame(A, B, RDHSLine, 2.f * Sc);
		Rect(A, FVector2D(A.X + 6.f * Sc, B.Y), Ac);
	}
	bDraw = true;
	Card();
	// ---- the heroes along the bottom (a click shows one), the arrows, START
	// (mistward: kept for the menu's own pointer, not as the engine's hit boxes: a hit box that takes a click keeps it from the
	// player controller's keys; the one the pointer is over gets a lit frame)
	auto Button = [&](const FVector2D& P0, const FVector2D& P1, FName Name)
	{
		if (!Sel->bMouseUI) { AddHitBox(P0, P1 - P0, Name, true); return; }
		Sel->Buttons.Add({ Name, FBox2D(P0, P1) });
		if (Sel->Hovered == Name) Frame(P0 - FVector2D(3.f * Sc), P1 + FVector2D(3.f * Sc), FLinearColor(1.f, 0.85f, 0.45f, 0.95f), 2.f * Sc);
	};
	const int32 N = Sel->Heroes.Num();
	const float Tb = 210.f * Sc, Tg = 14.f * Sc, Ty = Canvas->ClipY - 130.f * Sc, Tbh = 52.f * Sc;
	const float T0 = (Canvas->ClipX - (N * Tb + (N - 1) * Tg)) * 0.5f;
	for (int32 I = 0; I < N; ++I)
	{
		const FRDHeroDef& O = Sel->Heroes[I];
		const bool bOn = I == Sel->GetIndex();
		const FVector2D P0(T0 + I * (Tb + Tg), Ty), P1 = P0 + FVector2D(Tb, Tbh);
		if (UI.Has(TEXT("button")))
		{
			// (the plate, lit in her colour when she is the one shown)
			UI.Nine(TEXT("button"), P0, P1, HeightPx(TEXT("button"), Tbh),
			        bOn ? FLinearColor(0.75f + O.Accent.R * 0.5f, 0.75f + O.Accent.G * 0.5f, 0.75f + O.Accent.B * 0.5f) : FLinearColor(0.55f, 0.55f, 0.55f));
			if (bOn) Frame(P0 + FVector2D(2.f * Sc), P1 - FVector2D(2.f * Sc), O.Accent, 2.f * Sc);
		}
		else
		{
			Rect(P0, P1, bOn ? FLinearColor(O.Accent.R * 0.35f, O.Accent.G * 0.35f, O.Accent.B * 0.35f, 0.95f) : FLinearColor(0.04f, 0.045f, 0.06f, 0.85f));
			Frame(P0, P1, bOn ? O.Accent : FLinearColor(0.40f, 0.38f, 0.34f), (bOn ? 3.f : 1.f) * Sc);
		}
		const FString Nm = RDHSShown(O);
		UI.TextSize(Nm, Tw, Th, Medium, Sc * 1.1f, ERDType::Title);
		UI.Text(Nm, bOn ? FLinearColor::White : RDHSDim, (P0.X + P1.X - Tw) * 0.5f, (P0.Y + P1.Y - Th) * 0.5f, Medium, Sc * 1.1f, ERDType::Title);
		Button(P0, P1, FName(*FString::Printf(TEXT("Hero_%d"), I)));
	}
	// the arrows either side
	{
		const float Ax0 = T0 - Tg - 56.f * Sc, Ax1 = T0 + N * Tb + (N - 1) * Tg + Tg;
		for (int32 K = 0; K < 2; ++K)
		{
			const FVector2D P0(K == 0 ? Ax0 : Ax1, Ty), P1 = P0 + FVector2D(56.f * Sc, Tbh);
			// (the painted arrowhead points right: the left one is mirrored)
			if (!UI.Fit(TEXT("arrow"), P0 - FVector2D(4.f * Sc), P1 + FVector2D(4.f * Sc), FLinearColor::White, K == 0))
			{
				Rect(P0, P1, FLinearColor(0.04f, 0.045f, 0.06f, 0.85f)); Frame(P0, P1, RDHSLine, 1.5f * Sc);
				const TCHAR* G = K == 0 ? TEXT("<") : TEXT(">");
				UI.TextSize(G, Tw, Th, Medium, Sc * 1.4f);
				UI.Text(G, RDHSInk, (P0.X + P1.X - Tw) * 0.5f, (P0.Y + P1.Y - Th) * 0.5f, Medium, Sc * 1.4f);
			}
			Button(P0, P1, K == 0 ? FName(TEXT("Prev")) : FName(TEXT("Next")));
		}
	}
	// START (bottom right)
	{
		const FString St = FString::Printf(TEXT("START AS %s"), *RDHSShown(H));
		UI.TextSize(St, Tw, Th, Medium, Sc * 1.3f, ERDType::Title);
		const float Pulse = 0.75f + 0.25f * FMath::Sin(Now * 3.f);
		const float Wide = UI.Has(TEXT("button")) ? 50.f * Sc : 0.f;      // (the plate's rim and rivets want room)
		const FVector2D P1(Canvas->ClipX - 80.f * Sc + Wide * 0.5f, Canvas->ClipY - 170.f * Sc + Wide * 0.25f), P0 = P1 - FVector2D(Tw + 60.f * Sc + Wide, Th + 30.f * Sc + Wide * 0.5f);
		if (UI.Has(TEXT("button")))
		{
			UI.Nine(TEXT("button"), P0, P1, HeightPx(TEXT("button"), P1.Y - P0.Y),
			        FLinearColor(0.6f + H.Accent.R * 0.6f * Pulse, 0.6f + H.Accent.G * 0.6f * Pulse, 0.6f + H.Accent.B * 0.6f * Pulse));
			Frame(P0 + FVector2D(3.f * Sc), P1 - FVector2D(3.f * Sc), FLinearColor(H.Accent.R, H.Accent.G, H.Accent.B, 0.5f + 0.5f * Pulse), 2.f * Sc);
		}
		else
		{
			Rect(P0, P1, FLinearColor(H.Accent.R * 0.45f * Pulse, H.Accent.G * 0.45f * Pulse, H.Accent.B * 0.45f * Pulse, 0.95f));
			Frame(P0, P1, H.Accent, 3.f * Sc);
		}
		if (Wide > 0.f) UI.Text(St, FLinearColor(0.f, 0.f, 0.f, 0.8f), (P0.X + P1.X - Tw) * 0.5f + 2.f * Sc, (P0.Y + P1.Y - Th) * 0.5f + 2.f * Sc, Medium, Sc * 1.3f, ERDType::Title);
		UI.Text(St, FLinearColor::White, (P0.X + P1.X - Tw) * 0.5f, (P0.Y + P1.Y - Th) * 0.5f, Medium, Sc * 1.3f, ERDType::Title);
		Button(P0, P1, TEXT("Start"));
	}
	// the keys
	const FString Keys = bPad ? TEXT("D-pad, left stick or LB / RB  another hero      A  start")
	                          : Sel->bMouseUI ? TEXT("click a name  that hero      click START or her name again  start      A / D, arrows or wheel  another hero      Enter  start")
	                                          : TEXT("A / D, arrows or wheel  another hero      Enter or Space  start      or click");
	UI.TextSize(Keys, Tw, Th, Small, Sc * 1.1f);
	Rect(FVector2D((Canvas->ClipX - Tw) * 0.5f - 16.f * Sc, Canvas->ClipY - 62.f * Sc), FVector2D((Canvas->ClipX + Tw) * 0.5f + 16.f * Sc, Canvas->ClipY - 50.f * Sc + Th), FLinearColor(0.03f, 0.035f, 0.05f, 0.75f));
	UI.Text(Keys, RDHSInk, (Canvas->ClipX - Tw) * 0.5f, Canvas->ClipY - 56.f * Sc, Small, Sc * 1.1f);
}
