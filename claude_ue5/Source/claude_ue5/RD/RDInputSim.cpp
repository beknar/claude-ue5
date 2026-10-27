#include "RD/RDInputSim.h"
#include "Engine/World.h"
#include "Engine/GameViewportClient.h"
#include "Slate/SceneViewport.h"
#include "Framework/Application/SlateApplication.h"
#include "Widgets/SViewport.h"
#include "Widgets/SWindow.h"
#include "Layout/WidgetPath.h"

namespace RDInputSim
{
	static TSet<FKey> RDISButtons;          // (the mouse buttons the tests hold down)
	static FVector2D RDISLast = FVector2D::ZeroVector;

	static FString RDISViewport(UWorld* World, TSharedPtr<SViewport>& OutWidget, FSceneViewport*& OutViewport)
	{
		if (!FSlateApplication::IsInitialized()) return TEXT("no Slate");
		UGameViewportClient* VC = World ? World->GetGameViewport() : nullptr;
		if (!VC) return TEXT("no game viewport");
		OutWidget = VC->GetGameViewportWidget();
		OutViewport = VC->GetGameViewport();
		if (!OutWidget.IsValid() || !OutViewport) return TEXT("no viewport widget");
		return FString();
	}

	static FString RDISScreen(UWorld* World, const FVector2D& Pixel, FVector2D& OutScreen)
	{
		TSharedPtr<SViewport> W; FSceneViewport* SV = nullptr;
		const FString Why = RDISViewport(World, W, SV);
		if (!Why.IsEmpty()) return Why;
		const FGeometry& G = SV->GetCachedGeometry();
		const FIntPoint Px = SV->GetSizeXY();
		if (Px.X <= 0 || Px.Y <= 0) return TEXT("viewport has no size");
		const FVector2D Local = Pixel / FVector2D(Px) * FVector2D(G.GetLocalSize());
		OutScreen = FVector2D(G.LocalToAbsolute(Local));
		// (only over the game's view: a point anywhere else would click the editor)
		FSlateApplication& S = FSlateApplication::Get();
		const FWidgetPath Path = S.LocateWindowUnderMouse(OutScreen, S.GetInteractiveTopLevelWindows(), false, 0);
		if (!Path.IsValid() || !Path.ContainsWidget(W.Get())) return FString::Printf(TEXT("(%.0f, %.0f) is not over the game's viewport"), Pixel.X, Pixel.Y);
		return FString();
	}

	FString Key(UWorld* World, const FKey& InKey, bool bDown)
	{
		TSharedPtr<SViewport> W; FSceneViewport* SV = nullptr;
		const FString Why = RDISViewport(World, W, SV);
		if (!Why.IsEmpty()) return Why;
		FSlateApplication& S = FSlateApplication::Get();
		if (S.GetUserFocusedWidget(0) != W) S.SetAllUserFocusToGameViewport();
		if (S.GetUserFocusedWidget(0) != W) return TEXT("the game's viewport does not have the keyboard focus");
		const FKeyEvent Ev(InKey, S.GetModifierKeys(), 0, false, 0, 0);
		if (bDown) S.ProcessKeyDownEvent(Ev); else S.ProcessKeyUpEvent(Ev);
		return FString();
	}

	FString MouseMove(UWorld* World, const FVector2D& Pixel)
	{
		FVector2D Scr;
		const FString Why = RDISScreen(World, Pixel, Scr);
		if (!Why.IsEmpty()) return Why;
		const FPointerEvent Ev(0, 0, Scr, RDISLast, RDISButtons, EKeys::Invalid, 0.f, FSlateApplication::Get().GetModifierKeys());
		FSlateApplication::Get().ProcessMouseMoveEvent(Ev);
		RDISLast = Scr;
		return FString();
	}

	FString MouseButton(UWorld* World, const FVector2D& Pixel, const FKey& Button, bool bDown)
	{
		FVector2D Scr;
		const FString Why = RDISScreen(World, Pixel, Scr);
		if (!Why.IsEmpty()) return Why;
		if (bDown) RDISButtons.Add(Button); else RDISButtons.Remove(Button);
		const FPointerEvent Ev(0, 0, Scr, RDISLast, RDISButtons, Button, 0.f, FSlateApplication::Get().GetModifierKeys());
		if (bDown) FSlateApplication::Get().ProcessMouseButtonDownEvent(nullptr, Ev);
		else FSlateApplication::Get().ProcessMouseButtonUpEvent(Ev);
		RDISLast = Scr;
		return FString();
	}

	static TArray<TWeakPtr<SWindow>> RDISHidden;

	FString ClearView(UWorld* World)
	{
		TSharedPtr<SViewport> W; FSceneViewport* SV = nullptr;
		const FString Why = RDISViewport(World, W, SV);
		if (!Why.IsEmpty()) return TEXT("! ") + Why;
		FSlateApplication& S = FSlateApplication::Get();
		const TSharedPtr<SWindow> Own = S.FindWidgetWindow(W.ToSharedRef());
		const FGeometry& G = SV->GetCachedGeometry();
		const FSlateRect View(FVector2D(G.GetAbsolutePosition()), FVector2D(G.GetAbsolutePosition()) + FVector2D(G.GetAbsoluteSize()));
		// (every window, the child windows too (a floating tab's window is the main window's child), but the view's own and
		// the windows it lies in)
		TArray<TSharedRef<SWindow>> All;
		TArray<TSharedRef<SWindow>> Todo = S.GetInteractiveTopLevelWindows();
		while (Todo.Num() > 0) { TSharedRef<SWindow> Wn = Todo.Pop(); All.Add(Wn); Todo.Append(Wn->GetChildWindows()); }
		TArray<FString> Names;
		for (const TSharedRef<SWindow>& Wn : All)
		{
			if (Own.IsValid() && (Wn == Own || Own->IsDescendantOf(Wn))) continue;
			if (!Wn->IsVisible()) continue;
			const FSlateRect R(FVector2D(Wn->GetPositionInScreen()), FVector2D(Wn->GetPositionInScreen()) + FVector2D(Wn->GetSizeInScreen()));
			if (!FSlateRect::DoRectanglesIntersect(R, View)) continue;
			Wn->HideWindow();
			RDISHidden.Add(Wn);
			Names.Add(Wn->GetTitle().ToString().IsEmpty() ? FString(TEXT("(untitled)")) : Wn->GetTitle().ToString());
		}
		return FString::Join(Names, TEXT(", "));
	}

	int32 RestoreView()
	{
		int32 N = 0;
		for (const TWeakPtr<SWindow>& Wk : RDISHidden) if (const TSharedPtr<SWindow> Wn = Wk.Pin()) { Wn->ShowWindow(); ++N; }
		RDISHidden.Reset();
		return N;
	}

	FString Wheel(UWorld* World, const FVector2D& Pixel, float Delta)
	{
		FVector2D Scr;
		const FString Why = RDISScreen(World, Pixel, Scr);
		if (!Why.IsEmpty()) return Why;
		const FPointerEvent Ev(0, 0, Scr, RDISLast, RDISButtons, EKeys::Invalid, Delta, FSlateApplication::Get().GetModifierKeys());
		FSlateApplication::Get().ProcessMouseWheelOrGestureEvent(Ev, nullptr);
		RDISLast = Scr;
		return FString();
	}
}
