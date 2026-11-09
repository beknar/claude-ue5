// The game's own console (the user's of 2026-11-08: "create a console for the shipping game"). A Shipping game has no console:
// the engine compiles UConsole's window out of it (ALLOW_CONSOLE is 0), and turning it back on (bUseConsoleInShipping) needs a
// target with its own build environment, which an installed engine refuses ("Targets with a unique build environment cannot be
// built with an installed engine"). Commands and console variables still run in a Shipping game (UE_ALLOW_EXEC_COMMANDS is 1
// there; UEngine::Exec hands the console variables to the console manager): only the window to type them in is missing.
//
// This is that window: a Slate overlay on the game's view, opened and closed with the console key (` by default: the input
// settings' ConsoleKeys), the line run as the engine's console runs it (APlayerController::ConsoleCommand) and what it prints
// shown above. Up / Down recall the lines typed before, Tab completes a command's name, PageUp / PageDown scroll, Escape closes.
// "help" lists the game's own commands (rd.*), "clear" empties it. While it is open nothing typed reaches the game under it.
// On in a Shipping game; elsewhere the engine's console has the key, and rd.GameConsole 1 (or -RDConsole) puts this one on it
// for testing. -RDConsoleTest=<file> runs its self-test in a packaged game (pipeline/package_mistward.ps1's console run).
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "InputCoreTypes.h"
#include "Containers/Ticker.h"
#include "RDConsole.generated.h"

class SWidget;
class SEditableTextBox;
class FRDConsoleKeys;
struct FKeyEvent;

UCLASS()
class CLAUDE_UE5_API URDConsole : public UGameInstanceSubsystem
{
	GENERATED_BODY()
public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	static URDConsole* Of(const UObject* Ctx);
	/** the console of the game Ctx is in (Python has no subsystem lookup here) */
	UFUNCTION(BlueprintPure, Category = "RandomDungeon|Console", meta = (WorldContext = "Ctx")) static URDConsole* GetConsole(const UObject* Ctx) { return Of(Ctx); }

	/** on: a Shipping game always; elsewhere with rd.GameConsole 1 or -RDConsole on the command line */
	UFUNCTION(BlueprintPure, Category = "RandomDungeon|Console") bool IsEnabled() const;
	UFUNCTION(BlueprintPure, Category = "RandomDungeon|Console") bool IsOpen() const { return bOpen; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Console") void Open();
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Console") void Close();
	/** a line run as if typed and Enter pressed; what it printed */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Console") FString Run(const FString& Line);
	/** what it shows: the lines typed ("> " before them) and what they printed */
	UFUNCTION(BlueprintPure, Category = "RandomDungeon|Console") TArray<FString> GetLines() const { return Lines; }
	/** the line being typed */
	UFUNCTION(BlueprintPure, Category = "RandomDungeon|Console") FString GetInputText() const;
	/** whether the line being typed has the keyboard's focus */
	UFUNCTION(BlueprintPure, Category = "RandomDungeon|Console") bool HasKeyboardFocus() const;

	// (tests: input sent into Slate as a keyboard sends it, to whatever has the focus)
	/** each character as typed: its key down, the character, its key up */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Console") FString SendChars(const FString& Text);
	/** a key down and up (Enter, Tab, Up, Escape, the console key ...) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Console") FString SendKey(FKey Key);
	/** the game's view as drawn, the console over it, saved as a PNG; "" when saved, else why not */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Console") FString Shoot(const FString& File);
	/** the self-test: opens it with the console key, types, runs, recalls, completes, holds W under it, closes it; written to
	 *  File (and GetSelfTestResult) as "check|<name>|ok/FAILED|<what was measured>" lines and a last "result|ok/FAILED" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Console") void StartSelfTest(const FString& File);
	UFUNCTION(BlueprintPure, Category = "RandomDungeon|Console") FString GetSelfTestResult() const { return TestResult; }

	// (from the input processor and the widget)
	bool HandleKeyDown(const FKeyEvent& E);
	void Commit(const FString& Text);
	bool OnBoxKey(const FKeyEvent& E);
	bool SwallowChar(TCHAR C);
	FString RowText(int32 Row) const;
	bool RowIsTyped(int32 Row) const;
	static constexpr int32 Rows = 16;

private:
	bool Tick(float Dt);
	void Add(const FString& Text);
	void Complete();
	void Recall(int32 Dir);
	bool IsConsoleKey(const FKey& Key) const;
	UWorld* PlayWorld() const;
	APawn* PlayPawn() const;
	void TickSelfTest();
	void Check(const FString& Name, bool bOk, const FString& What);

	TSharedPtr<FRDConsoleKeys> Keys;
	TSharedPtr<SWidget> Root;
	TSharedPtr<SEditableTextBox> Box;
	FTSTicker::FDelegateHandle TickHandle;
	TArray<FString> Lines;
	TArray<FString> History;
	int32 HistoryAt = -1;
	int32 Back = 0;
	bool bOpen = false;
	bool bSwallowChar = false;

	FString TestFile, TestResult;
	int32 TestStep = -1;
	double TestAt = 0.0;
	double TestReady = 0.0;
	FVector TestFrom = FVector::ZeroVector;
	float TestSpeedWas = 1.f;
	TArray<FString> TestLines;
	bool bTestOk = true;
};
