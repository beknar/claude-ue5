// The user's list of 2026-11-26 (docs/improvements17.txt; the plan docs/improvements17_plan.md), its second phase.
//   - "The loading screen needs to show some animation and movement": the cover's widget (the movie player's loading screen while a map loads, and the
//     cover over the view after it) is a widget of our own that paints itself from real time: a ring of runes turning round a breathing emblem, a bar
//     of light running under "Loading", and a tip that changes every few seconds. It reads nothing but the clock and constant text, so it may paint on
//     the movie player's own thread while the game thread is in LoadMap.
//   - "In full screen 1080p, the mini-map's building outlines shimmer when the character is moving": the minimaps placed every point at the centre plus
//     (world - her place) x scale, her raw place in it, so every line slid by fractions of a pixel as she walked; Canvas lines are not smoothed, and a
//     1.6 px line covered one row of pixels, then two. The map's base (where the world's origin lands) is rounded to whole pixels: every point is that
//     base plus its own fixed fraction, so the drawing moves a whole pixel at a time and keeps its shape; the lines are whole pixels thick.
#include "RD/RDHUD.h"
#include "RD/RDDungeonGenerator.h"
#include "Engine/Canvas.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformTime.h"
#include "Widgets/SLeafWidget.h"
#include "Rendering/DrawElements.h"
#include "Framework/Application/SlateApplication.h"
#include "Fonts/FontMeasure.h"
#include "Styling/CoreStyle.h"
#include <atomic>

namespace
{
	TAutoConsoleVariable<int32> CVarRDMinimapSnap(TEXT("rd.MinimapSnap"), 1, TEXT("The minimaps drawn on whole pixels (1, the list of 2026-11-26) or at her exact place (0, the old drawing: its lines shimmer as she moves)"));

	// (the widget's counters for the tests: it paints on the movie player's thread too)
	std::atomic<int32> GRDLoading17Paints{ 0 };
	std::atomic<double> GRDLoading17First{ 0.0 }, GRDLoading17Last{ 0.0 };
	// (the ring's phases painted since a map's load began, in 64 buckets, and the paints then: the package's log says how it moved during LoadMap)
	std::atomic<uint64> GRDLoading17Mask{ 0 };
	std::atomic<int32> GRDLoading17PaintsAtLoad{ 0 };

	const TCHAR* const RDLoadingTips17[] = {
		TEXT("F opens doors, chests and the people you stand nearest to."),
		TEXT("A torch burns down; blind-fish oil makes it last twice as long."),
		TEXT("The market's stands each sell their own trade, at the town's tier."),
		TEXT("Rest at an inn or a camp to move the day on."),
		TEXT("Monster contracts are posted on the wild towns' boards."),
		TEXT("Each city's dungeon opens with the key of the one before it."),
		TEXT("Warming meals and warm gear keep the cold of the north away."),
		TEXT("Call your horse with J, or up on the D-pad."),
		TEXT("Landmark towers hide caves at their feet."),
		TEXT("The Options page chooses Immersive Interiors or Closed Structures."),
		TEXT("Locked chests can be picked or broken, if nobody sees you."),
		TEXT("Waystones remember the way; the map's fast travel takes you to any town you have found."),
	};
	constexpr int32 RDLoadingTipCount17 = UE_ARRAY_COUNT(RDLoadingTips17);
	constexpr double RDLoadingTipSeconds17 = 4.5;
	constexpr double RDLoadingTurnSeconds17 = 6.0;

	// (the colours of the old cover: the dark board and the gold letters)
	const FLinearColor RDL17Board(0.035f, 0.03f, 0.028f, 1.f), RDL17Gold(0.88f, 0.80f, 0.62f, 1.f);

	TArray<FVector2f> RDL17F(const TArray<FVector2D>& In) { TArray<FVector2f> O; O.Reserve(In.Num()); for (const FVector2D& V : In) O.Add(FVector2f(V)); return O; }

	class SRDLoading17 : public SLeafWidget
	{
	public:
		SLATE_BEGIN_ARGS(SRDLoading17) {}
		SLATE_END_ARGS()

		void Construct(const FArguments&)
		{
			// (an active timer keeps Slate ticking and painting it every frame, also where nothing else is invalidated)
			RegisterActiveTimer(0.f, FWidgetActiveTimerDelegate::CreateLambda([](double, float) { return EActiveTimerReturnType::Continue; }));
		}

		virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(64.f, 64.f); }
		virtual bool ComputeVolatility() const override { return true; }

		virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& G, const FSlateRect& Cull, FSlateWindowElementList& Out, int32 Layer, const FWidgetStyle& Style, bool bParentEnabled) const override
		{
			const double Now = FPlatformTime::Seconds();
			double First = GRDLoading17First.load();
			if (First <= 0.0) { GRDLoading17First.store(Now); First = Now; }
			GRDLoading17Last.store(Now);
			GRDLoading17Paints.fetch_add(1);
			const double T = Now - First;
			const FVector2D Sz = G.GetLocalSize();
			const float U = FMath::Max(Sz.Y / 1080.f, 0.25f);
			const FSlateBrush* White = FCoreStyle::Get().GetBrush("WhiteBrush");
			// the board
			FSlateDrawElement::MakeBox(Out, Layer, G.ToPaintGeometry(), White, ESlateDrawEffect::None, RDL17Board);
			const FVector2D Mid(Sz.X * 0.5f, Sz.Y * 0.44f);
			// the emblem: a diamond breathing in and out
			{
				const float Breath = 0.5f + 0.5f * FMath::Sin((float)(T * 2.0 * PI / 2.6));
				const float Rd = (22.f + 6.f * Breath) * U;
				TArray<FVector2D> P = { Mid + FVector2D(0, -Rd), Mid + FVector2D(Rd, 0), Mid + FVector2D(0, Rd), Mid + FVector2D(-Rd, 0), Mid + FVector2D(0, -Rd) };
				FSlateDrawElement::MakeLines(Out, Layer + 1, G.ToPaintGeometry(), RDL17F(P), ESlateDrawEffect::None, RDL17Gold * FLinearColor(1, 1, 1, 0.55f + 0.45f * Breath), true, 2.5f * U);
				const float Ri = Rd * 0.45f;
				TArray<FVector2D> Q = { Mid + FVector2D(0, -Ri), Mid + FVector2D(Ri, 0), Mid + FVector2D(0, Ri), Mid + FVector2D(-Ri, 0), Mid + FVector2D(0, -Ri) };
				FSlateDrawElement::MakeLines(Out, Layer + 1, G.ToPaintGeometry(), RDL17F(Q), ESlateDrawEffect::None, RDL17Gold * FLinearColor(1, 1, 1, 0.8f), true, 2.f * U);
			}
			// the ring of runes: twelve marks turning, the leading one brightest
			{
				const float Turn = (float)FMath::Fmod(T / RDLoadingTurnSeconds17, 1.0);
				GRDLoading17Mask.fetch_or(uint64(1) << FMath::Clamp((int32)(Turn * 64.f), 0, 63));
				const float Rr = 74.f * U;
				for (int32 I = 0; I < 12; ++I)
				{
					const float A = (I / 12.f + Turn) * 2.f * PI;
					const FVector2D Dir(FMath::Cos(A), FMath::Sin(A)), Side(-Dir.Y, Dir.X);
					const float Lead = FMath::Fmod(12.f - I + 12.f * FMath::Fmod(T * 1.5, 1.0), 12.f) / 12.f;
					const FLinearColor Cl = RDL17Gold * FLinearColor(1, 1, 1, 0.25f + 0.75f * (1.f - Lead));
					const FVector2D P0 = Mid + Dir * Rr;
					// (each rune a small branching stroke: a stem along the ring's radius and a twig)
					TArray<FVector2D> Stem = { P0 - Dir * 9.f * U, P0 + Dir * 9.f * U };
					TArray<FVector2D> Twig = { P0, P0 + (Side * (I % 2 ? 1.f : -1.f) + Dir) * 5.f * U };
					FSlateDrawElement::MakeLines(Out, Layer + 1, G.ToPaintGeometry(), RDL17F(Stem), ESlateDrawEffect::None, Cl, true, 2.f * U);
					FSlateDrawElement::MakeLines(Out, Layer + 1, G.ToPaintGeometry(), RDL17F(Twig), ESlateDrawEffect::None, Cl, true, 1.6f * U);
				}
			}
			const TSharedRef<FSlateFontMeasure> Fm = FSlateApplication::Get().GetRenderer()->GetFontMeasureService();
			// the word
			const FSlateFontInfo Big = FCoreStyle::GetDefaultFontStyle("Regular", FMath::RoundToInt(30.f * U));
			const FString Word = TEXT("Loading");
			const FVector2D Ws = Fm->Measure(Word, Big);
			const float Wy = Mid.Y + 110.f * U;
			FSlateDrawElement::MakeText(Out, Layer + 2, G.ToPaintGeometry(Ws, FSlateLayoutTransform(FVector2D(Mid.X - Ws.X * 0.5f, Wy))), Word, Big, ESlateDrawEffect::None, RDL17Gold);
			// the bar of light under it: a bright stretch running along a dim line
			{
				const float Bw = 260.f * U, By = Wy + Ws.Y + 14.f * U, X0 = Mid.X - Bw * 0.5f;
				FSlateDrawElement::MakeBox(Out, Layer + 1, G.ToPaintGeometry(FVector2D(Bw, 2.f * U), FSlateLayoutTransform(FVector2D(X0, By))), White, ESlateDrawEffect::None, RDL17Gold * FLinearColor(1, 1, 1, 0.18f));
				const float Ph = (float)FMath::Fmod(T / 1.6, 1.0), Lw = 70.f * U;
				const float Lx = X0 - Lw + (Bw + Lw) * Ph;
				const float A0 = FMath::Max(Lx, X0), A1 = FMath::Min(Lx + Lw, X0 + Bw);
				if (A1 > A0) FSlateDrawElement::MakeBox(Out, Layer + 2, G.ToPaintGeometry(FVector2D(A1 - A0, 3.f * U), FSlateLayoutTransform(FVector2D(A0, By - 0.5f * U))), White, ESlateDrawEffect::None, RDL17Gold);
			}
			// the tip, fading in and out with each change
			{
				const int32 Ti = (int32)(T / RDLoadingTipSeconds17) % RDLoadingTipCount17;
				const float In = (float)FMath::Fmod(T, RDLoadingTipSeconds17);
				const float Fade = FMath::Clamp(FMath::Min(In / 0.5f, (RDLoadingTipSeconds17 - In) / 0.5f), 0.f, 1.f);
				const FSlateFontInfo Small = FCoreStyle::GetDefaultFontStyle("Regular", FMath::RoundToInt(15.f * U));
				const FString Tip = RDLoadingTips17[Ti];
				const FVector2D Ts = Fm->Measure(Tip, Small);
				FSlateDrawElement::MakeText(Out, Layer + 2, G.ToPaintGeometry(Ts, FSlateLayoutTransform(FVector2D(Mid.X - Ts.X * 0.5f, Sz.Y * 0.86f))), Tip, Small, ESlateDrawEffect::None, FLinearColor(0.75f, 0.72f, 0.64f, 0.9f * Fade));
			}
			return Layer + 2;
		}
	};
}

// (RDList16b.cpp's map-load hooks: the paints and the distinct phases of the ring between the start of a load and its end, "<paints>|<phases of 64>")
void RDLoadingBegin17() { GRDLoading17Mask.store(0); GRDLoading17PaintsAtLoad.store(GRDLoading17Paints.load()); }
FString RDLoadingEnd17() { return FString::Printf(TEXT("%d|%d"), GRDLoading17Paints.load() - GRDLoading17PaintsAtLoad.load(), FMath::CountBits(GRDLoading17Mask.load())); }

// (RDList16b.cpp's cover takes this widget for both of its paths)
TSharedRef<SWidget> RDLoadingWidget17()
{
	return SNew(SRDLoading17);
}

FString ARDDungeonGenerator::GetLoadingState17()
{
	const double First = GRDLoading17First.load(), Last = GRDLoading17Last.load();
	const double T = First > 0.0 ? Last - First : 0.0;
	return FString::Printf(TEXT("%d|%.4f|%d|%.3f"), GRDLoading17Paints.load(), FMath::Fmod(T / RDLoadingTurnSeconds17, 1.0), (int32)(T / RDLoadingTipSeconds17) % RDLoadingTipCount17, T);
}

// ================================================================================================ the minimaps on whole pixels
FVector2D ARDHUD::MapBase17(const TCHAR* Kind, const FVector2D& C, const FVector2D& L, double K, float WallPx)
{
	// (the screen's x is the world's y and its y the world's -x, as every minimap draws it)
	const bool bSnap = CVarRDMinimapSnap.GetValueOnGameThread() != 0;
	FVector2D B = C + FVector2D(-L.Y, L.X) * K;
	if (bSnap) B = FVector2D(FMath::RoundToDouble(B.X), FMath::RoundToDouble(B.Y));
	MiniLines17.Reset();
	MinimapState17 = FString::Printf(TEXT("%s|%.3f|%.3f|%d|%.2f|%.0f|%.2f|%.2f"), Kind, B.X, B.Y, bSnap ? 1 : 0, WallPx, Canvas ? Canvas->ClipY : 0.f, C.X, C.Y);
	return B;
}

float ARDHUD::LinePx17(float Px)
{
	return CVarRDMinimapSnap.GetValueOnGameThread() != 0 ? FMath::Max(1.f, FMath::RoundToFloat(Px)) : Px;
}
