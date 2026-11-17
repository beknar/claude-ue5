// The user's list of 2026-11-16 (docs/improvements14.txt; the plan docs/improvements14_plan.md), its second phase: the last 20
// messages (item 8) and a potion or food on the quick bar used by the attack (item 20). Every rule is behind the generator's
// bMessageLog14 / bQuickUse14, which 927 sets on the game's maps.
#include "RD/RDCombat.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDHUD.h"
#include "GameFramework/PlayerController.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"

static constexpr int32 RDL14LogMax = 20;

void URDCombatComponent::PushMessageLog(const FString& Text)
{
	// (item 8: "enable the ability to see the last 20 game messages": every line the HUD is given, kept with its game time; the
	// same line given again within a second is one line (a hazard's line renewed each look))
	// (PR #78's review: a line said again right after itself is one line with its count, however long between (a locked gate's
	// line every 5 s filled the log); its age the real time the player lived, not the game's (sped up, or stopped in a panel))
	if (Text.IsEmpty()) return;
	const double Now = FPlatformTime::Seconds();
	if (MessageLogText.Num() > 0 && MessageLogText.Last() == Text) { MessageLogAt.Last() = Now; ++MessageLogTimes.Last(); return; }
	MessageLogText.Add(Text); MessageLogAt.Add(Now); MessageLogTimes.Add(1);
	while (MessageLogText.Num() > RDL14LogMax) { MessageLogText.RemoveAt(0); MessageLogAt.RemoveAt(0); MessageLogTimes.RemoveAt(0); }
}

TArray<FString> URDCombatComponent::GetMessageLog() const
{
	// (newest first: "<seconds ago>|<text>", the text with " (x<n>)" when said n times in a row)
	TArray<FString> Out;
	const double Now = FPlatformTime::Seconds();
	for (int32 I = MessageLogText.Num() - 1; I >= 0; --I)
		Out.Add(FString::Printf(TEXT("%.0f|%s%s"), Now - MessageLogAt[I], *MessageLogText[I], MessageLogTimes[I] > 1 ? *FString::Printf(TEXT(" (x%d)"), MessageLogTimes[I]) : TEXT("")));
	return Out;
}

void URDCombatComponent::SetMessageLogOpen(bool bOpen)
{
	bMessageLogOpen = bOpen && Generator && Generator->bMessageLog14;
}

void URDCombatComponent::TickList14Input(const APlayerController* PC)
{
	// (L, or the pad's D-pad down where the quick bar leaves it free and the map is shut, opens and shuts the messages)
	if (!PC || !Generator) return;
	if (!Generator->bMessageLog14) { if (Generator->bHorseCall14 && (PC->WasInputKeyJustPressed(EKeys::J) || (Generator->bQuickSlots && !Generator->bMapOpen && PC->WasInputKeyJustPressed(EKeys::Gamepad_DPad_Up)))) Generator->CallHorseByKey(); return; }
	// (the D-pad down is no one else's in play, quick bar or not (PR #78's review))
	const bool bPad = !Generator->bMapOpen && PC->WasInputKeyJustPressed(EKeys::Gamepad_DPad_Down);
	if (PC->WasInputKeyJustPressed(EKeys::L) || bPad) SetMessageLogOpen(!bMessageLogOpen);
	// (the third phase, item 7: J, or the pad's D-pad up where the quick bar leaves it free, calls her horse)
	if (Generator->bHorseCall14 && (PC->WasInputKeyJustPressed(EKeys::J) || (Generator->bQuickSlots && !Generator->bMapOpen && PC->WasInputKeyJustPressed(EKeys::Gamepad_DPad_Up))))
		Generator->CallHorseByKey();
}

bool URDCombatComponent::QuickItemAttack(const APlayerController* PC)
{
	// (item 20: "when a potion or food is in a quick bar, the attack action should consume it": an item made ready on the bar
	// (the D-pad) is used by the attack button, in every hero's controls; the press that used it makes no blow until let go)
	// (the attack keys only: a spell key still casts with an item ready (PR #78's review: the casters' spells were held too); an
	// item ready with none left, or whose use is refused, is no longer ready, so the attack strikes again)
	if (!PC || !Generator || !Generator->bQuickUse14) return false;
	const bool bAtkDown = PC->IsInputKeyDown(EKeys::LeftMouseButton) || PC->IsInputKeyDown(EKeys::Gamepad_RightShoulder);
	if (!bAtkDown) bAbilityPressHeld = false;
	if (!ReadyAbility.IsNone() && IsQuickItem(ReadyAbility))
	{
		if (GetItemCount(QuickItemOf(ReadyAbility)) <= 0) { ReadyAbility = NAME_None; return bAbilityPressHeld; }
		if (PC->WasInputKeyJustPressed(EKeys::LeftMouseButton) || PC->WasInputKeyJustPressed(EKeys::Gamepad_RightShoulder))
		{
			if (!UseAbility(ReadyAbility)) ReadyAbility = NAME_None;
			bAbilityPressHeld = true;
		}
		return true;
	}
	return bAbilityPressHeld;
}

void ARDHUD::DrawMessageLog(float Sc)
{
	URDCombatComponent* Cb = Gen ? Gen->GetPlayerCombat() : nullptr;
	if (!Cb) return;
	UFont* Small = GEngine->GetSmallFont();
	const TArray<FString> Lines = Cb->GetMessageLog();
	const FVector2D A(Canvas->ClipX * 0.27f, Canvas->ClipY * 0.16f), B(Canvas->ClipX * 0.73f, Canvas->ClipY * 0.80f);
	if (!Board(TEXT("panel"), A, B, Sc, 0.f))
	{
		Box(A, B, FLinearColor(0.04f, 0.035f, 0.03f, 0.88f));
		Frame(A, B, FLinearColor(1.f, 0.82f, 0.3f, 0.9f), 2.f * Sc);
	}
	const float Pad = 34.f * Sc;
	float Tw, Th;
	const FString Title = FString::Printf(TEXT("The last %d messages"), Lines.Num());
	UI.TextSize(Title, Tw, Th, Small, Sc * 1.25f, ERDType::Label);
	UI.Text(Title, FLinearColor(1.f, 0.82f, 0.3f), (A.X + B.X - Tw) * 0.5f, A.Y + Pad, Small, Sc * 1.25f, ERDType::Label);
	const FString Close(TEXT("L or D-pad down: close"));
	float Cw, Ch; UI.TextSize(Close, Cw, Ch, Small, Sc * 0.95f);
	UI.Text(Close, FLinearColor(0.7f, 0.67f, 0.6f), (A.X + B.X - Cw) * 0.5f, B.Y - Pad - Ch, Small, Sc * 0.95f);
	float Y = A.Y + Pad + Th + 14.f * Sc;
	const float Wd = B.X - A.X - Pad * 2.f, AgeW = 92.f * Sc;
	if (Lines.Num() == 0) UI.Text(TEXT("Nothing yet."), FLinearColor(0.8f, 0.77f, 0.7f), A.X + Pad, Y, Small, Sc * 1.05f);
	for (const FString& L : Lines)
	{
		if (Y > B.Y - Pad - Ch - 30.f * Sc) break;
		FString Ago, Text; L.Split(TEXT("|"), &Ago, &Text);
		const int32 S = FCString::Atoi(*Ago);
		const FString When = S < 60 ? FString::Printf(TEXT("%d s ago"), S) : S < 3600 ? FString::Printf(TEXT("%d min ago"), S / 60) : FString::Printf(TEXT("%d h ago"), S / 3600);
		UI.Text(When, FLinearColor(0.68f, 0.64f, 0.56f), A.X + Pad, Y, Small, Sc * 0.95f);
		// (a long line cut to the panel's width with an ellipsis: the longest that fits found by halving, a few measures a line
		// (PR #78's review: two letters a measure was hundreds a frame))
		FString Shown = Text; float Lw, Lh; UI.TextSize(Shown, Lw, Lh, Small, Sc * 1.05f);
		if (Lw > Wd - AgeW)
		{
			int32 Lo = 0, Hi = Text.Len();
			while (Lo < Hi)
			{
				const int32 Mid = (Lo + Hi + 1) / 2; float Mw, Mh;
				UI.TextSize(Text.Left(Mid) + TEXT("..."), Mw, Mh, Small, Sc * 1.05f);
				if (Mw <= Wd - AgeW) Lo = Mid; else Hi = Mid - 1;
			}
			Shown = Text.Left(Lo) + TEXT("...");
		}
		UI.Text(Shown, FLinearColor(0.96f, 0.93f, 0.84f), A.X + Pad + AgeW, Y, Small, Sc * 1.05f);
		Y += FMath::Max(Lh, Th * 0.8f) + 7.f * Sc;
	}
}
