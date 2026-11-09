// The game's own console (RDConsole.h says why a Shipping game needs one of its own).
#include "RD/RDConsole.h"
#include "RD/RDInputSim.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/InputSettings.h"
#include "Framework/Application/SlateApplication.h"
#include "Framework/Application/IInputProcessor.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/SOverlay.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SViewport.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Styling/CoreStyle.h"
#include "HAL/IConsoleManager.h"
#include "HAL/FileManager.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "ImageCore.h"
#include "ImageUtils.h"

// (on in a Shipping game, which has no engine console; elsewhere the engine's console has the key)
static TAutoConsoleVariable<int32> CVarRDGameConsole(TEXT("rd.GameConsole"), ALLOW_CONSOLE ? 0 : 1,
	TEXT("The game's own console, opened with the console key (`): 1 on, 0 off. On in a Shipping game, which has no engine console; elsewhere the engine's console has the key and this is for testing."));

static const TCHAR* const RDConHelp = TEXT("` or Esc closes   Tab completes a name   Up / Down the lines before   PageUp / PageDown scroll   help lists the game's commands");

/** what a command prints, line by line */
class FRDConsoleOut : public FOutputDevice
{
public:
	FString Text;
	virtual void Serialize(const TCHAR* V, ELogVerbosity::Type, const FName&) override { Text += V; Text += TEXT("\n"); }
};

/** the console key and Escape, seen before any widget gets them */
class FRDConsoleKeys : public IInputProcessor
{
public:
	TWeakObjectPtr<URDConsole> Owner;
	virtual void Tick(const float, FSlateApplication&, TSharedRef<ICursor>) override {}
	virtual bool HandleKeyDownEvent(FSlateApplication&, const FKeyEvent& E) override { URDConsole* C = Owner.Get(); return C && C->HandleKeyDown(E); }
	virtual const TCHAR* GetDebugName() const override { return TEXT("RDConsole"); }
};

/** the overlay: the lines above, the line being typed under them; over the whole view, so that nothing typed or clicked while
 *  it is open reaches the game under it (a key the line does not use bubbles up to the view's widget otherwise: W walked her) */
class SRDConsoleView : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SRDConsoleView) : _Owner(nullptr) {}
		SLATE_ARGUMENT(URDConsole*, Owner)
	SLATE_END_ARGS()

	TSharedPtr<SEditableTextBox> Box;

	void Construct(const FArguments& A)
	{
		const TWeakObjectPtr<URDConsole> W = A._Owner;
		const FSlateFontInfo Mono = FCoreStyle::GetDefaultFontStyle("Mono", 11);
		const FSlateFontInfo Typed = FCoreStyle::GetDefaultFontStyle("Mono", 12);
		const FLinearColor Gold(1.f, 0.78f, 0.36f), Pale(0.86f, 0.87f, 0.84f);
		TSharedRef<SVerticalBox> Rows = SNew(SVerticalBox);
		for (int32 i = 0; i < URDConsole::Rows; ++i)
		{
			Rows->AddSlot().AutoHeight()
			[
				SNew(STextBlock).Font(Mono)
				.Text_Lambda([W, i]() { const URDConsole* C = W.Get(); return C ? FText::FromString(C->RowText(i)) : FText::GetEmpty(); })
				.ColorAndOpacity_Lambda([W, i, Gold, Pale]() { const URDConsole* C = W.Get(); return FSlateColor(C && C->RowIsTyped(i) ? Gold : Pale); })
			];
		}
		ChildSlot
		[
			SNew(SOverlay)
			+ SOverlay::Slot()
			[
				SNew(SBorder).BorderImage(FStyleDefaults::GetNoBrush()).Visibility(EVisibility::Visible)
			]
			+ SOverlay::Slot().VAlign(VAlign_Top).HAlign(HAlign_Fill)
			[
				SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(FLinearColor(0.01f, 0.012f, 0.02f, 0.94f))
				.Padding(FMargin(14.f, 10.f))
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot().AutoHeight() [ Rows ]
					+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f, 0.f, 0.f)
					[
						SNew(SHorizontalBox)
						+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 6.f, 0.f)
						[
							SNew(STextBlock).Font(Typed).Text(FText::FromString(TEXT(">"))).ColorAndOpacity(FSlateColor(Gold))
						]
						+ SHorizontalBox::Slot().FillWidth(1.f)
						[
							SAssignNew(Box, SEditableTextBox).Font(Typed)
							.ClearKeyboardFocusOnCommit(false).RevertTextOnEscape(false).SelectAllTextWhenFocused(false)
							.BackgroundColor(FLinearColor(0.f, 0.f, 0.f, 0.65f)).ForegroundColor(FLinearColor(0.96f, 0.95f, 0.9f))
							.OnTextCommitted_Lambda([W](const FText& T, ETextCommit::Type How) { if (How == ETextCommit::OnEnter) if (URDConsole* C = W.Get()) C->Commit(T.ToString()); })
							.OnKeyDownHandler_Lambda([W](const FGeometry&, const FKeyEvent& E) { URDConsole* C = W.Get(); return C && C->OnBoxKey(E) ? FReply::Handled() : FReply::Unhandled(); })
							.OnKeyCharHandler_Lambda([W](const FGeometry&, const FCharacterEvent& E) { URDConsole* C = W.Get(); return C && C->SwallowChar(E.GetCharacter()) ? FReply::Handled() : FReply::Unhandled(); })
						]
					]
					+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 5.f, 0.f, 0.f)
					[
						SNew(STextBlock).Font(FCoreStyle::GetDefaultFontStyle("Regular", 9)).Text(FText::FromString(RDConHelp)).ColorAndOpacity(FSlateColor(FLinearColor(0.55f, 0.56f, 0.55f)))
					]
				]
			]
		];
	}

	virtual FReply OnKeyDown(const FGeometry&, const FKeyEvent&) override { return FReply::Handled(); }
	virtual FReply OnKeyUp(const FGeometry&, const FKeyEvent&) override { return FReply::Handled(); }
	virtual FReply OnAnalogValueChanged(const FGeometry&, const FAnalogInputEvent&) override { return FReply::Handled(); }
	virtual FReply OnMouseMove(const FGeometry&, const FPointerEvent&) override { return FReply::Handled(); }
	virtual FReply OnMouseButtonDown(const FGeometry&, const FPointerEvent&) override
	{
		return Box.IsValid() ? FReply::Handled().SetUserFocus(Box.ToSharedRef(), EFocusCause::Mouse) : FReply::Handled();
	}
	virtual FReply OnMouseButtonUp(const FGeometry&, const FPointerEvent&) override { return FReply::Handled(); }
	virtual FReply OnMouseWheel(const FGeometry&, const FPointerEvent&) override { return FReply::Handled(); }
};

URDConsole* URDConsole::Of(const UObject* Ctx)
{
	UWorld* W = GEngine && Ctx ? GEngine->GetWorldFromContextObject(Ctx, EGetWorldErrorMode::ReturnNull) : nullptr;
	UGameInstance* GI = W ? W->GetGameInstance() : nullptr;
	return GI ? GI->GetSubsystem<URDConsole>() : nullptr;
}

void URDConsole::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	if (FParse::Param(FCommandLine::Get(), TEXT("RDConsole"))) CVarRDGameConsole->Set(1, ECVF_SetByCommandline);
	if (FSlateApplication::IsInitialized())
	{
		Keys = MakeShared<FRDConsoleKeys>();
		Keys->Owner = this;
		FSlateApplication::Get().RegisterInputPreProcessor(Keys, 0);
	}
	TickHandle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateUObject(this, &URDConsole::Tick));
	FString File;
	if (FParse::Value(FCommandLine::Get(), TEXT("RDConsoleTest="), File) && !File.IsEmpty()) StartSelfTest(File);
}

void URDConsole::Deinitialize()
{
	Close();
	if (Keys.IsValid() && FSlateApplication::IsInitialized()) FSlateApplication::Get().UnregisterInputPreProcessor(Keys);
	Keys.Reset(); Root.Reset(); Box.Reset();
	FTSTicker::GetCoreTicker().RemoveTicker(TickHandle);
	Super::Deinitialize();
}

bool URDConsole::IsEnabled() const { return CVarRDGameConsole.GetValueOnGameThread() != 0; }

UWorld* URDConsole::PlayWorld() const { const UGameInstance* GI = GetGameInstance(); return GI ? GI->GetWorld() : nullptr; }

APawn* URDConsole::PlayPawn() const
{
	const UGameInstance* GI = GetGameInstance();
	const APlayerController* PC = GI ? GI->GetFirstLocalPlayerController(PlayWorld()) : nullptr;
	return PC ? PC->GetPawn() : nullptr;
}

bool URDConsole::IsConsoleKey(const FKey& Key) const
{
	const UInputSettings* S = GetDefault<UInputSettings>();
	return Key == EKeys::Tilde || (S && S->ConsoleKeys.Contains(Key));
}

bool URDConsole::HandleKeyDown(const FKeyEvent& E)
{
	if (!IsEnabled()) return false;
	const FKey K = E.GetKey();
	if (bOpen)
	{
		// (in the editor only while the line has the focus: the editor's other panels keep their keys)
		if (GIsEditor && !(Root.IsValid() && Root->HasAnyUserFocusOrFocusedDescendants())) return false;
		if (!IsConsoleKey(K) && K != EKeys::Escape) return false;
		if (!E.IsRepeat()) Close();
		return true;
	}
	if (!IsConsoleKey(K) || E.IsRepeat()) return false;
	const UGameInstance* GI = GetGameInstance();
	UGameViewportClient* VC = GI ? GI->GetGameViewportClient() : nullptr;
	if (!VC) return false;
	// (in the editor only from this game's own view)
	if (GIsEditor)
	{
		const TSharedPtr<SWidget> F = FSlateApplication::Get().GetUserFocusedWidget(0);
		const TSharedPtr<SViewport> VW = VC->GetGameViewportWidget();
		if (!F.IsValid() || !VW.IsValid() || F != StaticCastSharedPtr<SWidget>(VW)) return false;
	}
	Open();
	bSwallowChar = bOpen;          // (the key's own character comes after it: not typed)
	return bOpen;
}

void URDConsole::Open()
{
	if (bOpen || !FSlateApplication::IsInitialized()) return;
	UGameInstance* GI = GetGameInstance();
	UGameViewportClient* VC = GI ? GI->GetGameViewportClient() : nullptr;
	if (!VC) return;
	if (!Root.IsValid())
	{
		const TSharedRef<SRDConsoleView> V = SNew(SRDConsoleView).Owner(this);
		Box = V->Box; Root = V;
	}
	VC->RemoveViewportWidgetContent(Root.ToSharedRef());
	VC->AddViewportWidgetContent(Root.ToSharedRef(), 1000);
	bOpen = true; Back = 0; HistoryAt = -1;
	if (Lines.Num() == 0) Add(TEXT("The game's console. Type a command and Enter; help lists the game's own."));
	// (keys held as it opens would stay held in the game until pressed again: their releases come to the console)
	if (APlayerController* PC = GI->GetFirstLocalPlayerController(PlayWorld())) PC->FlushPressedKeys();
	FSlateApplication::Get().ReleaseAllPointerCapture();
	FSlateApplication::Get().SetAllUserFocus(Box, EFocusCause::SetDirectly);
}

void URDConsole::Close()
{
	if (!bOpen) return;
	bOpen = false;
	UGameInstance* GI = GetGameInstance();
	if (UGameViewportClient* VC = GI ? GI->GetGameViewportClient() : nullptr) if (Root.IsValid()) VC->RemoveViewportWidgetContent(Root.ToSharedRef());
	if (Box.IsValid()) Box->SetText(FText::GetEmpty());
	if (FSlateApplication::IsInitialized()) FSlateApplication::Get().SetAllUserFocusToGameViewport();
	if (APlayerController* PC = GI ? GI->GetFirstLocalPlayerController(PlayWorld()) : nullptr) PC->FlushPressedKeys();
}

bool URDConsole::Tick(float)
{
	bSwallowChar = false;
	if (bOpen && FSlateApplication::IsInitialized())
	{
		// (a level's load empties the view's widgets: the console is shut with them)
		if (!Root.IsValid() || !Root->IsParentValid()) { bOpen = false; FSlateApplication::Get().SetAllUserFocusToGameViewport(); }
		else if (Box.IsValid() && !Box->HasAnyUserFocusOrFocusedDescendants())
		{
			// (the game gave its view the focus back (an input mode set as the pointer shows or hides): the line takes it again)
			const UGameInstance* GI = GetGameInstance();
			const UGameViewportClient* VC = GI ? GI->GetGameViewportClient() : nullptr;
			const TSharedPtr<SWidget> F = FSlateApplication::Get().GetUserFocusedWidget(0);
			if (VC && (!F.IsValid() || F == StaticCastSharedPtr<SWidget>(VC->GetGameViewportWidget()))) FSlateApplication::Get().SetAllUserFocus(Box, EFocusCause::SetDirectly);
		}
	}
	TickSelfTest();
	return true;
}

void URDConsole::Add(const FString& Text)
{
	Lines.Add(Text);
	if (Lines.Num() > 400) Lines.RemoveAt(0, Lines.Num() - 400);
}

FString URDConsole::RowText(int32 Row) const
{
	const int32 I = Lines.Num() - Back - Rows + Row;
	return Lines.IsValidIndex(I) ? Lines[I] : FString();
}

bool URDConsole::RowIsTyped(int32 Row) const { return RowText(Row).StartsWith(TEXT("> ")); }

FString URDConsole::GetInputText() const { return Box.IsValid() ? Box->GetText().ToString() : FString(); }

bool URDConsole::HasKeyboardFocus() const { return bOpen && Box.IsValid() && Box->HasAnyUserFocusOrFocusedDescendants(); }

bool URDConsole::SwallowChar(TCHAR C)
{
	if (bSwallowChar) { bSwallowChar = false; return true; }
	return C == TEXT('`');
}

void URDConsole::Commit(const FString& Text)
{
	Run(Text);
	if (Box.IsValid()) Box->SetText(FText::GetEmpty());
}

bool URDConsole::OnBoxKey(const FKeyEvent& E)
{
	const FKey K = E.GetKey();
	if (K == EKeys::Up) { Recall(1); return true; }
	if (K == EKeys::Down) { Recall(-1); return true; }
	if (K == EKeys::Tab) { Complete(); return true; }
	if (K == EKeys::PageUp) { Back = FMath::Clamp(Back + Rows / 2, 0, FMath::Max(0, Lines.Num() - Rows)); return true; }
	if (K == EKeys::PageDown) { Back = FMath::Max(0, Back - Rows / 2); return true; }
	return false;
}

void URDConsole::Recall(int32 Dir)
{
	if (History.Num() == 0 || !Box.IsValid()) return;
	if (Dir > 0) HistoryAt = HistoryAt < 0 ? History.Num() - 1 : FMath::Max(0, HistoryAt - 1);
	else
	{
		if (HistoryAt < 0) return;
		if (++HistoryAt >= History.Num()) { HistoryAt = -1; Box->SetText(FText::GetEmpty()); return; }
	}
	Box->SetText(FText::FromString(History[HistoryAt]));
	Box->GoTo(ETextLocation::EndOfDocument);
}

void URDConsole::Complete()
{
	if (!Box.IsValid()) return;
	const FString Typed = GetInputText().TrimStart();
	if (Typed.IsEmpty() || Typed.Contains(TEXT(" "))) return;
	TArray<FString> Names;
	IConsoleManager::Get().ForEachConsoleObjectThatStartsWith(FConsoleObjectVisitor::CreateLambda([&Names](const TCHAR* Name, IConsoleObject* Obj)
	{
		if (Obj && !Obj->TestFlags(ECVF_Unregistered)) Names.Add(Name);
	}), *Typed);
	for (const TCHAR* Own : { TEXT("help"), TEXT("clear") }) if (FString(Own).StartsWith(Typed, ESearchCase::IgnoreCase)) Names.Add(Own);
	if (Names.Num() == 0) return;
	Names.Sort();
	// (the longest start they share, the case as the names have it)
	FString Common = Names[0];
	for (const FString& N : Names)
	{
		int32 L = 0;
		while (L < Common.Len() && L < N.Len() && FChar::ToLower(Common[L]) == FChar::ToLower(N[L])) ++L;
		Common.LeftInline(L);
	}
	if (Names.Num() == 1) Common += TEXT(" ");
	if (Common.Len() >= Typed.Len()) { Box->SetText(FText::FromString(Common)); Box->GoTo(ETextLocation::EndOfDocument); }
	if (Names.Num() > 1)
	{
		Add(FString::Printf(TEXT("%d names begin with %s:"), Names.Num(), *Typed));
		for (int32 i = 0; i < FMath::Min(Names.Num(), 12); ++i) Add(TEXT("  ") + Names[i]);
		if (Names.Num() > 12) Add(FString::Printf(TEXT("  ... and %d more"), Names.Num() - 12));
	}
}

FString URDConsole::Run(const FString& InLine)
{
	const FString Line = InLine.TrimStartAndEnd();
	if (Line.IsEmpty()) return FString();
	Add(TEXT("> ") + Line);
	if (History.Num() == 0 || History.Last() != Line) History.Add(Line);
	if (History.Num() > 50) History.RemoveAt(0);
	HistoryAt = -1; Back = 0;
	FString Out;
	if (Line.Equals(TEXT("clear"), ESearchCase::IgnoreCase) || Line.Equals(TEXT("cls"), ESearchCase::IgnoreCase)) { Lines.Reset(); return Out; }
	if (Line.Equals(TEXT("help"), ESearchCase::IgnoreCase) || Line == TEXT("?"))
	{
		TArray<FString> Own;
		IConsoleManager::Get().ForEachConsoleObjectThatStartsWith(FConsoleObjectVisitor::CreateLambda([&Own](const TCHAR* Name, IConsoleObject* Obj)
		{
			if (!Obj || Obj->TestFlags(ECVF_Unregistered)) return;
			// (its first sentence: the rows do not wrap)
			FString Help = Obj->GetHelp(); int32 Nl; if (Help.FindChar(TEXT('\n'), Nl)) Help.LeftInline(Nl);
			const int32 Dot = Help.Find(TEXT(". ")); if (Dot > 0) Help.LeftInline(Dot + 1);
			const IConsoleVariable* V = Obj->AsVariable();
			Own.Add(V ? FString::Printf(TEXT("  %s = %s    %s"), Name, *V->GetString(), *Help) : FString::Printf(TEXT("  %s    %s"), Name, *Help));
		}), TEXT("rd."));
		Own.Sort();
		Out = TEXT("The game's commands (a name alone shows its value, a name and a value sets it):\n") + FString::Join(Own, TEXT("\n"))
			+ TEXT("\n  help, clear    this list; empty the console\nThe engine's console variables are read and set the same way (t.MaxFPS 60).");
	}
	else
	{
		UGameInstance* GI = GetGameInstance();
		UWorld* W = PlayWorld();
		if (APlayerController* PC = GI ? GI->GetFirstLocalPlayerController(W) : nullptr) Out = PC->ConsoleCommand(Line, false);
		else if (GEngine)
		{
			FRDConsoleOut O;
			if (!GEngine->Exec(W, *Line, O)) O.Logf(TEXT("Command not recognized: %s"), *Line);
			Out = O.Text;
		}
	}
	TArray<FString> Parts;
	Out.ParseIntoArrayLines(Parts, true);
	for (const FString& P : Parts) Add(P);
	return Out;
}

FString URDConsole::SendChars(const FString& Text)
{
	if (!FSlateApplication::IsInitialized()) return TEXT("no Slate");
	FSlateApplication& S = FSlateApplication::Get();
	for (const TCHAR Ch : Text)
	{
		const uint32 Code = FChar::IsAlnum(Ch) ? (uint32)FChar::ToUpper(Ch) : (Ch == TEXT(' ') ? 32u : 0u);
		const FKey K = FInputKeyManager::Get().GetKeyFromCodes(Code, Ch);
		const FKeyEvent Ev(K, S.GetModifierKeys(), 0, false, Ch, Code);
		S.ProcessKeyDownEvent(Ev);
		S.ProcessKeyCharEvent(FCharacterEvent(Ch, S.GetModifierKeys(), 0, false));
		S.ProcessKeyUpEvent(Ev);
	}
	return FString();
}

FString URDConsole::SendKey(FKey Key)
{
	if (!FSlateApplication::IsInitialized()) return TEXT("no Slate");
	FSlateApplication& S = FSlateApplication::Get();
	const FKeyEvent Ev(Key, S.GetModifierKeys(), 0, false, 0, 0);
	S.ProcessKeyDownEvent(Ev);
	S.ProcessKeyUpEvent(Ev);
	return FString();
}

FString URDConsole::Shoot(const FString& File)
{
	if (!FSlateApplication::IsInitialized()) return TEXT("no Slate");
	const UGameInstance* GI = GetGameInstance();
	const UGameViewportClient* VC = GI ? GI->GetGameViewportClient() : nullptr;
	const TSharedPtr<SViewport> W = VC ? VC->GetGameViewportWidget() : nullptr;
	if (!W.IsValid()) return TEXT("no game view");
	TArray<FColor> Px; FIntVector Size;
	if (!FSlateApplication::Get().TakeScreenshot(W.ToSharedRef(), Px, Size) || Px.Num() == 0 || Size.X <= 0 || Size.Y <= 0) return TEXT("no picture taken");
	for (FColor& C : Px) C.A = 255;
	IFileManager::Get().MakeDirectory(*FPaths::GetPath(File), true);
	return FImageUtils::SaveImageByExtension(*File, FImageView(Px.GetData(), Size.X, Size.Y)) ? FString() : TEXT("not saved");
}

void URDConsole::StartSelfTest(const FString& File)
{
	TestFile = File; TestResult.Reset(); TestLines.Reset(); bTestOk = true;
	TestStep = 0; TestAt = 0.0; TestReady = 0.0;
}

void URDConsole::Check(const FString& Name, bool bOk, const FString& What)
{
	TestLines.Add(FString::Printf(TEXT("check|%s|%s|%s"), *Name, bOk ? TEXT("ok") : TEXT("FAILED"), *What));
	bTestOk = bTestOk && bOk;
}

void URDConsole::TickSelfTest()
{
	if (TestStep < 0) return;
	const double Now = FPlatformTime::Seconds();
	if (Now < TestAt || !FSlateApplication::IsInitialized()) return;
	FSlateApplication& S = FSlateApplication::Get();
	UWorld* W = PlayWorld();
	APawn* P = PlayPawn();
	UGameInstance* GI = GetGameInstance();
	APlayerController* PC = GI ? GI->GetFirstLocalPlayerController(W) : nullptr;
	const UGameViewportClient* VC = GI ? GI->GetGameViewportClient() : nullptr;
	IConsoleVariable* Speed = IConsoleManager::Get().FindConsoleVariable(TEXT("rd.WildRunSpeed"));
	auto Next = [this, Now](double Wait) { ++TestStep; TestAt = Now + Wait; };
	auto LineAfter = [this](const FString& Typed, const FString& Starts) -> FString
	{
		// (the first line printed after the last time Typed was run that starts so)
		const int32 At = Lines.FindLastByPredicate([&Typed](const FString& L) { return L == TEXT("> ") + Typed; });
		// (FString's StartsWith("") is false: no prefix takes the first line)
		for (int32 i = At + 1; At >= 0 && i < Lines.Num(); ++i) if (Starts.IsEmpty() || Lines[i].StartsWith(Starts)) return Lines[i];
		return FString();
	};
	switch (TestStep)
	{
	case 0:
	{
		// (her in a level of play (not the hero menu), 5 s after she came)
		if (!W || !P || !PC || W->GetMapName().EndsWith(TEXT("_select"))) { TestReady = 0.0; TestAt = Now + 0.5; return; }
		if (TestReady == 0.0) TestReady = Now;
		if (Now - TestReady < 5.0) { TestAt = Now + 0.5; return; }
		if (bOpen) Close();
		TestSpeedWas = Speed ? Speed->GetFloat() : 1.f;
		Check(TEXT("enabled"), IsEnabled(), FString::Printf(TEXT("rd.GameConsole %d in %s (%s)"), CVarRDGameConsole.GetValueOnGameThread(), *W->GetMapName(),
			UE_BUILD_SHIPPING ? TEXT("Shipping") : GIsEditor ? TEXT("editor") : TEXT("Development")));
		Next(0.1);
		return;
	}
	case 1:
	{
		// (the console key pressed in the game's view as a keyboard sends it: its key down, its character, its key up)
		const FString Why = RDInputSim::Key(W, EKeys::Tilde, true);
		S.ProcessKeyCharEvent(FCharacterEvent(TEXT('`'), S.GetModifierKeys(), 0, false));
		S.ProcessKeyUpEvent(FKeyEvent(EKeys::Tilde, S.GetModifierKeys(), 0, false, 0, 0));
		TestLines.Add(FString::Printf(TEXT("note|key|%s"), Why.IsEmpty() ? TEXT("sent") : *Why));
		Next(0.3);
		return;
	}
	case 2:
	{
		Check(TEXT("opens"), bOpen && HasKeyboardFocus() && GetInputText().IsEmpty(),
			FString::Printf(TEXT("open %d, the line has the keyboard %d, the line \"%s\" (the key's ` not typed)"), bOpen, HasKeyboardFocus(), *GetInputText()));
		SendChars(TEXT("rd.WildRunSpeed 10"));
		const FString Typed = GetInputText();
		SendKey(EKeys::Enter);
		const float Got = Speed ? Speed->GetFloat() : -1.f;
		Check(TEXT("runs"), Typed == TEXT("rd.WildRunSpeed 10") && FMath::IsNearlyEqual(Got, 10.f) && GetInputText().IsEmpty() && bOpen && HasKeyboardFocus(),
			FString::Printf(TEXT("typed \"%s\", Enter: rd.WildRunSpeed %.1f, the line emptied %d, still open with the keyboard %d; printed: \"%s\""),
				*Typed, Got, GetInputText().IsEmpty(), bOpen && HasKeyboardFocus(), *LineAfter(TEXT("rd.WildRunSpeed 10"), TEXT(""))));
		Next(0.3);
		return;
	}
	case 3:
	{
		SendChars(TEXT("rd.WildRunSpeed")); SendKey(EKeys::Enter);
		const FString Val = LineAfter(TEXT("rd.WildRunSpeed"), TEXT("rd.WildRunSpeed = "));
		SendChars(TEXT("t.MaxFPS")); SendKey(EKeys::Enter);
		const FString Fps = LineAfter(TEXT("t.MaxFPS"), TEXT("t.MaxFPS = "));
		Check(TEXT("reads"), Val.Contains(TEXT("10")) && !Fps.IsEmpty(), FString::Printf(TEXT("rd.WildRunSpeed printed \"%s\"; t.MaxFPS printed \"%s\""), *Val, *Fps));
		Next(0.3);
		return;
	}
	case 4:
	{
		SendKey(EKeys::Up); const FString A = GetInputText();
		SendKey(EKeys::Up); const FString B = GetInputText();
		SendKey(EKeys::Down); const FString C = GetInputText();
		if (Box.IsValid()) Box->SetText(FText::GetEmpty());
		SendChars(TEXT("rd.Wild")); SendKey(EKeys::Tab); const FString D = GetInputText();
		if (Box.IsValid()) Box->SetText(FText::GetEmpty());
		Check(TEXT("recalls"), A == TEXT("t.MaxFPS") && B == TEXT("rd.WildRunSpeed") && C == TEXT("t.MaxFPS"), FString::Printf(TEXT("Up \"%s\", Up \"%s\", Down \"%s\""), *A, *B, *C));
		Check(TEXT("completes"), D == TEXT("rd.WildRunSpeed "), FString::Printf(TEXT("rd.Wild and Tab: \"%s\""), *D));
		SendChars(TEXT("nosuchcommand")); SendKey(EKeys::Enter);
		const FString No = LineAfter(TEXT("nosuchcommand"), TEXT(""));
		Check(TEXT("unknown"), No.Contains(TEXT("not recognized")), FString::Printf(TEXT("printed \"%s\""), *No));
		SendChars(TEXT("help")); SendKey(EKeys::Enter);
		const FString H1 = LineAfter(TEXT("help"), TEXT("  rd.WildRunSpeed")), H2 = LineAfter(TEXT("help"), TEXT("  rd.GameConsole"));
		Check(TEXT("help"), !H1.IsEmpty() && !H2.IsEmpty(), FString::Printf(TEXT("\"%s\" / \"%s\""), *H1.TrimStartAndEnd(), *H2.TrimStartAndEnd()));
		Next(0.5);
		return;
	}
	case 5:
	{
		const FString Png = FPaths::ChangeExtension(TestFile, TEXT("png"));
		const FString Why = TestFile.IsEmpty() ? FString(TEXT("no file")) : Shoot(Png);
		Check(TEXT("picture"), Why.IsEmpty(), Why.IsEmpty() ? Png : Why);
		// (W held under it 1.2 s: nothing reaches the game)
		TestFrom = P ? P->GetActorLocation() : FVector::ZeroVector;
		S.ProcessKeyDownEvent(FKeyEvent(EKeys::W, S.GetModifierKeys(), 0, false, 'w', 'W'));
		Next(1.2);
		return;
	}
	case 6:
	{
		const bool bDown = PC && PC->IsInputKeyDown(EKeys::W);
		S.ProcessKeyUpEvent(FKeyEvent(EKeys::W, S.GetModifierKeys(), 0, false, 'w', 'W'));
		const double Moved = P ? FVector::Dist2D(P->GetActorLocation(), TestFrom) : -1.0;
		Check(TEXT("game_untouched"), P && !bDown && Moved < 10.0, FString::Printf(TEXT("W held 1.2 s under it: the game saw it down %d, she moved %.0f cm"), bDown, Moved));
		SendKey(EKeys::Escape);
		const TSharedPtr<SWidget> F = S.GetUserFocusedWidget(0);
		const bool bView = VC && F.IsValid() && F == StaticCastSharedPtr<SWidget>(VC->GetGameViewportWidget());
		Check(TEXT("escape"), !bOpen && bView, FString::Printf(TEXT("Escape: open %d, the game's view has the keyboard %d"), bOpen, bView));
		Next(0.3);
		return;
	}
	case 7:
	{
		RDInputSim::Key(W, EKeys::Tilde, true);
		S.ProcessKeyUpEvent(FKeyEvent(EKeys::Tilde, S.GetModifierKeys(), 0, false, 0, 0));
		const bool bOpened = bOpen && HasKeyboardFocus();
		SendKey(EKeys::Tilde);
		Check(TEXT("toggles"), bOpened && !bOpen, FString::Printf(TEXT("` opened it %d, ` again shut it %d"), bOpened, !bOpen));
		// (W held in the game's view: the game has its keys back)
		TestFrom = P ? P->GetActorLocation() : FVector::ZeroVector;
		RDInputSim::Key(W, EKeys::W, true);
		Next(1.0);
		return;
	}
	default:
	{
		const bool bDown = PC && PC->IsInputKeyDown(EKeys::W);
		RDInputSim::Key(W, EKeys::W, false);
		const double Moved = P ? FVector::Dist2D(P->GetActorLocation(), TestFrom) : -1.0;
		Check(TEXT("game_back"), bDown, FString::Printf(TEXT("W held 1 s with it shut: the game saw it down %d, she moved %.0f cm"), bDown, Moved));
		if (Speed) Speed->Set(TestSpeedWas, ECVF_SetByConsole);
		TestLines.Add(FString::Printf(TEXT("result|%s"), bTestOk ? TEXT("ok") : TEXT("FAILED")));
		TestResult = FString::Join(TestLines, TEXT("\n"));
		if (!TestFile.IsEmpty()) FFileHelper::SaveStringToFile(TestResult + TEXT("\n"), *TestFile, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
		TestStep = -1;
		return;
	}
	}
}
