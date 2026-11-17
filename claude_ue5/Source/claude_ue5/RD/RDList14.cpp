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
	if (Text.IsEmpty()) return;
	const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	if (MessageLogText.Num() > 0 && MessageLogText.Last() == Text && Now - MessageLogAt.Last() < 1.f) { MessageLogAt.Last() = Now; return; }
	MessageLogText.Add(Text); MessageLogAt.Add(Now);
	while (MessageLogText.Num() > RDL14LogMax) { MessageLogText.RemoveAt(0); MessageLogAt.RemoveAt(0); }
}

TArray<FString> URDCombatComponent::GetMessageLog() const
{
	// (newest first: "<seconds ago>|<text>")
	TArray<FString> Out;
	const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	for (int32 I = MessageLogText.Num() - 1; I >= 0; --I) Out.Add(FString::Printf(TEXT("%.0f|%s"), Now - MessageLogAt[I], *MessageLogText[I]));
	return Out;
}

void URDCombatComponent::SetMessageLogOpen(bool bOpen)
{
	bMessageLogOpen = bOpen && Generator && Generator->bMessageLog14;
}

void URDCombatComponent::TickList14Input(const APlayerController* PC)
{
	// (L, or the pad's D-pad down where the quick bar leaves it free and the map is shut, opens and shuts the messages)
	if (!PC || !Generator || !Generator->bMessageLog14) return;
	const bool bPad = Generator->bQuickSlots && !Generator->bMapOpen && PC->WasInputKeyJustPressed(EKeys::Gamepad_DPad_Down);
	if (PC->WasInputKeyJustPressed(EKeys::L) || bPad) SetMessageLogOpen(!bMessageLogOpen);
}

bool URDCombatComponent::QuickItemAttack(const APlayerController* PC)
{
	// (item 20: "when a potion or food is in a quick bar, the attack action should consume it": an item made ready on the bar
	// (the D-pad) is used by the attack button, in every hero's controls; the press that used it makes no blow until let go)
	if (!PC || !Generator || !Generator->bQuickUse14) return false;
	const bool bAtkDown = PC->IsInputKeyDown(EKeys::LeftMouseButton) || PC->IsInputKeyDown(EKeys::Gamepad_RightShoulder);
	if (!bAtkDown) bAbilityPressHeld = false;
	if (!ReadyAbility.IsNone() && IsQuickItem(ReadyAbility))
	{
		if (PC->WasInputKeyJustPressed(EKeys::LeftMouseButton) || PC->WasInputKeyJustPressed(EKeys::Gamepad_RightShoulder)) { UseAbility(ReadyAbility); bAbilityPressHeld = true; }
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
		// (a long line cut to the panel's width with an ellipsis)
		FString Shown = Text; float Lw, Lh; UI.TextSize(Shown, Lw, Lh, Small, Sc * 1.05f);
		while (Lw > Wd - AgeW && Shown.Len() > 4) { Shown = Shown.LeftChop(2); UI.TextSize(Shown + TEXT("..."), Lw, Lh, Small, Sc * 1.05f); }
		if (Shown != Text) Shown += TEXT("...");
		UI.Text(Shown, FLinearColor(0.96f, 0.93f, 0.84f), A.X + Pad + AgeW, Y, Small, Sc * 1.05f);
		Y += FMath::Max(Lh, Th * 0.8f) + 7.f * Sc;
	}
}
