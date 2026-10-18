#include "RD/RDHeroSelect.h"
#include "RD/RDDungeonGenerator.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "InputKeyEventArgs.h"
#include "Kismet/GameplayStatics.h"

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
			bViewSet = true;
		}
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

// ------------------------------------------------------------------------------------------------ the menu's HUD
static const FLinearColor RDHSInk(0.93f, 0.88f, 0.76f, 1.f);
static const FLinearColor RDHSDim(0.68f, 0.66f, 0.60f, 1.f);
static const FLinearColor RDHSLine(0.75f, 0.65f, 0.45f, 0.9f);

void ARDHeroSelectHUD::NotifyHitBoxClick(FName BoxName)
{
	Super::NotifyHitBoxClick(BoxName);
	if (!Sel) return;
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
	if (!Sel || !Sel->Heroes.IsValidIndex(Sel->GetIndex())) return;
	const FRDHeroDef& H = Sel->Heroes[Sel->GetIndex()];
	const float Sc = Canvas->ClipY / 1080.f, Now = GetWorld()->GetTimeSeconds();
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
	DrawText(TEXT("RANDOM DUNGEON"), RDHSDim, 80.f * Sc, 44.f * Sc, Small, Sc * 1.3f);
	DrawText(TEXT("CHOOSE YOUR HERO"), RDHSInk, 78.f * Sc, 68.f * Sc, Medium, Sc * 2.1f);
	// ---- her card (left)
	const float Fade = FMath::Clamp((Now - Sel->ShownTime) / 0.35f, 0.f, 1.f);
	const FLinearColor Ac(H.Accent.R, H.Accent.G, H.Accent.B, Fade);
	auto Ink = [&](const FLinearColor& C) { return FLinearColor(C.R, C.G, C.B, C.A * Fade); };
	const FVector2D A(80.f * Sc, 160.f * Sc);
	const float X = A.X + 34.f * Sc, Wd = 720.f * Sc - X - 30.f * Sc;
	float Y = 0.f;
	// (laid out twice: once to measure how tall the card is, then drawn on it)
	bool bDraw = false;
	auto Text = [&](const FString& T, const FLinearColor& C, float Tx, float Ty, UFont* F, float K) { if (bDraw) DrawText(T, C, Tx, Ty, F, K); };
	auto Fill = [&](const FVector2D& P0, const FVector2D& P1, const FLinearColor& C) { if (bDraw) Rect(P0, P1, C); };
	auto Card = [&]()
	{
	Y = A.Y + 22.f * Sc;
	Text(H.Name.ToString().ToUpper(), Ac, X, Y, Medium, Sc * 2.6f);
	Y += 74.f * Sc;
	// hit points and mana, as bars against the strongest of the heroes
	float MaxHp = 1.f, MaxMp = 1.f;
	for (const FRDHeroDef& O : Sel->Heroes) { MaxHp = FMath::Max(MaxHp, O.MaxHealth); MaxMp = FMath::Max(MaxMp, O.MaxMana); }
	auto Bar = [&](const TCHAR* Label, float V, float Max, const FLinearColor& C, const FString& Note)
	{
		Text(Label, Ink(RDHSDim), X, Y, Small, Sc * 1.1f);
		const FVector2D B0(X + 130.f * Sc, Y + 2.f * Sc), B1(X + Wd - 90.f * Sc, Y + 20.f * Sc);
		Fill(B0, B1, FLinearColor(0.08f, 0.08f, 0.1f, 0.9f * Fade));
		Fill(B0, FVector2D(B0.X + (B1.X - B0.X) * FMath::Clamp(V / Max, 0.f, 1.f), B1.Y), FLinearColor(C.R, C.G, C.B, Fade));
		Text(Note, Ink(RDHSInk), B1.X + 12.f * Sc, Y, Small, Sc * 1.1f);
		Y += 32.f * Sc;
	};
	Bar(TEXT("HIT POINTS"), H.MaxHealth, MaxHp, FLinearColor(0.25f, 0.75f, 0.3f), FString::Printf(TEXT("%.0f"), H.MaxHealth));
	Bar(TEXT("MANA"), H.MaxMana, MaxMp, FLinearColor(0.2f, 0.42f, 0.95f), H.MaxMana > 0.f ? FString::Printf(TEXT("%.0f"), H.MaxMana) : FString(TEXT("none")));
	Y += 14.f * Sc;
	auto Section = [&](const TCHAR* Head)
	{
		Text(Head, Ac, X, Y, Small, Sc * 1.05f);
		Y += 24.f * Sc;
		Fill(FVector2D(X, Y - 3.f * Sc), FVector2D(X + Wd, Y - 2.f * Sc), FLinearColor(0.75f, 0.65f, 0.45f, 0.35f * Fade));
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
			GetTextSize(Try, Tw, Th, Small, Sc * 1.2f);
			if (Tw > Wd - Indent && !Cur.IsEmpty()) { Text(Cur, C, X + Indent, Y, Small, Sc * 1.2f); Y += Th + 2.f * Sc; Cur = W; }
			else Cur = Try;
		}
		if (!Cur.IsEmpty()) { GetTextSize(Cur, Tw, Th, Small, Sc * 1.2f); Text(Cur, C, X + Indent, Y, Small, Sc * 1.2f); Y += Th + 6.f * Sc; }
	};
	Section(TEXT("MAIN ABILITIES"));
	for (const FString& L : H.Abilities)
	{
		Fill(FVector2D(X + 4.f * Sc, Y + 9.f * Sc), FVector2D(X + 11.f * Sc, Y + 16.f * Sc), Ac);
		Wrapped(L, 24.f * Sc, Ink(RDHSInk));
	}
	Y += 10.f * Sc;
	if (!H.Armour.IsEmpty()) { Section(TEXT("ARMOUR")); Wrapped(H.Armour, 0.f, Ink(RDHSInk)); Y += 10.f * Sc; }
	if (!H.StartsWith.IsEmpty()) { Section(TEXT("STARTS WITH")); Wrapped(H.StartsWith, 0.f, Ink(RDHSInk)); }
	};
	Card();
	const FVector2D B(720.f * Sc, FMath::Min(Y + 18.f * Sc, Canvas->ClipY - 170.f * Sc));
	Rect(A, B, FLinearColor(0.03f, 0.035f, 0.05f, 0.82f));
	Frame(A, B, RDHSLine, 2.f * Sc);
	Rect(A, FVector2D(A.X + 6.f * Sc, B.Y), Ac);
	bDraw = true;
	Card();
	// ---- the heroes along the bottom (a click shows one), the arrows, START
	const int32 N = Sel->Heroes.Num();
	const float Tb = 210.f * Sc, Tg = 14.f * Sc, Ty = Canvas->ClipY - 130.f * Sc, Tbh = 52.f * Sc;
	const float T0 = (Canvas->ClipX - (N * Tb + (N - 1) * Tg)) * 0.5f;
	for (int32 I = 0; I < N; ++I)
	{
		const FRDHeroDef& O = Sel->Heroes[I];
		const bool bOn = I == Sel->GetIndex();
		const FVector2D P0(T0 + I * (Tb + Tg), Ty), P1 = P0 + FVector2D(Tb, Tbh);
		Rect(P0, P1, bOn ? FLinearColor(O.Accent.R * 0.35f, O.Accent.G * 0.35f, O.Accent.B * 0.35f, 0.95f) : FLinearColor(0.04f, 0.045f, 0.06f, 0.85f));
		Frame(P0, P1, bOn ? O.Accent : FLinearColor(0.40f, 0.38f, 0.34f), (bOn ? 3.f : 1.f) * Sc);
		const FString Nm = O.Name.ToString().ToUpper();
		GetTextSize(Nm, Tw, Th, Medium, Sc * 1.1f);
		DrawText(Nm, bOn ? FLinearColor::White : RDHSDim, (P0.X + P1.X - Tw) * 0.5f, (P0.Y + P1.Y - Th) * 0.5f, Medium, Sc * 1.1f);
		AddHitBox(P0, P1 - P0, FName(*FString::Printf(TEXT("Hero_%d"), I)), true);
	}
	// the arrows either side
	{
		const float Ax0 = T0 - Tg - 56.f * Sc, Ax1 = T0 + N * Tb + (N - 1) * Tg + Tg;
		for (int32 K = 0; K < 2; ++K)
		{
			const FVector2D P0(K == 0 ? Ax0 : Ax1, Ty), P1 = P0 + FVector2D(56.f * Sc, Tbh);
			Rect(P0, P1, FLinearColor(0.04f, 0.045f, 0.06f, 0.85f)); Frame(P0, P1, RDHSLine, 1.5f * Sc);
			const TCHAR* G = K == 0 ? TEXT("<") : TEXT(">");
			GetTextSize(G, Tw, Th, Medium, Sc * 1.4f);
			DrawText(G, RDHSInk, (P0.X + P1.X - Tw) * 0.5f, (P0.Y + P1.Y - Th) * 0.5f, Medium, Sc * 1.4f);
			AddHitBox(P0, P1 - P0, K == 0 ? FName(TEXT("Prev")) : FName(TEXT("Next")), true);
		}
	}
	// START (bottom right)
	{
		const FString St = FString::Printf(TEXT("START AS %s"), *H.Name.ToString().ToUpper());
		GetTextSize(St, Tw, Th, Medium, Sc * 1.3f);
		const float Pulse = 0.75f + 0.25f * FMath::Sin(Now * 3.f);
		const FVector2D P1(Canvas->ClipX - 80.f * Sc, Canvas->ClipY - 170.f * Sc), P0 = P1 - FVector2D(Tw + 60.f * Sc, Th + 30.f * Sc);
		Rect(P0, P1, FLinearColor(H.Accent.R * 0.45f * Pulse, H.Accent.G * 0.45f * Pulse, H.Accent.B * 0.45f * Pulse, 0.95f));
		Frame(P0, P1, H.Accent, 3.f * Sc);
		DrawText(St, FLinearColor::White, P0.X + 30.f * Sc, P0.Y + 15.f * Sc, Medium, Sc * 1.3f);
		AddHitBox(P0, P1 - P0, TEXT("Start"), true);
	}
	// the keys
	const FString Keys = bPad ? TEXT("D-pad, left stick or LB / RB  another hero      A  start")
	                          : TEXT("A / D, arrows or wheel  another hero      Enter or Space  start      or click");
	GetTextSize(Keys, Tw, Th, Small, Sc * 1.1f);
	Rect(FVector2D((Canvas->ClipX - Tw) * 0.5f - 16.f * Sc, Canvas->ClipY - 62.f * Sc), FVector2D((Canvas->ClipX + Tw) * 0.5f + 16.f * Sc, Canvas->ClipY - 50.f * Sc + Th), FLinearColor(0.03f, 0.035f, 0.05f, 0.75f));
	DrawText(Keys, RDHSInk, (Canvas->ClipX - Tw) * 0.5f, Canvas->ClipY - 56.f * Sc, Small, Sc * 1.1f);
}
