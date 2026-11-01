// mistward_castle, the user's list of 2026-10-31 (pipeline/unreal/878). Each rule a switch on the generator ("Mistward4"
// category), off on the other levels:
//   options        the Escape menu in two pages: Options holds the volumes, the controls hint on / off, a resolution and a
//                  display mode (applied by Apply, kept in the game's user settings)
//   ally spacing   her allies keep apart: a summon is called to a spot nobody stands on; they step away from each other
//   (the summons panel and the allies' map markers are drawn in RDHUD.cpp; the hero menu's QUIT in RDHeroSelect.cpp)
#include "RD/RDDungeonGenerator.h"
#include "RD/RDCombat.h"
#include "RD/RDMonster.h"
#include "RD/RDSection.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/GameUserSettings.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDMistward4, Log, All);

static const TCHAR* RD4OptionsSection = TEXT("RandomDungeon.Options");
static constexpr float RD4AllyGap = 25.f;          // (cm between two allies' capsules, and an ally's and hers)

// ================================================================================================ the Options page
void ARDDungeonGenerator::LoadOptions()
{
	bool B = true;
	if (GConfig && GConfig->GetBool(RD4OptionsSection, TEXT("ShowControls"), B, GGameUserSettingsIni)) bControlsShown = B;
}

void ARDDungeonGenerator::SetControlsHintShown(bool bShow)
{
	bControlsShown = bShow;
	if (GConfig) { GConfig->SetBool(RD4OptionsSection, TEXT("ShowControls"), bShow, GGameUserSettingsIni); GConfig->Flush(false, GGameUserSettingsIni); }
}

TArray<FString> ARDDungeonGenerator::GetResolutionChoices() const
{
	// (the common sizes, none larger than the screen: a window larger than it would hang off its edges. The sizes are the
	// screen's real pixels: the game handles the screen's scaling itself (DefaultEngine.ini's bAllowHighDPIInGameMode;
	// without it Windows stretched a 1600 x 900 window to 3200 x 1800 on a 200 % screen, blurred))
	static const FIntPoint Common[5] = { { 1280, 720 }, { 1600, 900 }, { 1920, 1080 }, { 2560, 1440 }, { 3840, 2160 } };
	FIntPoint Desk(3840, 2160);
	if (const UGameUserSettings* Gs = GEngine ? GEngine->GetGameUserSettings() : nullptr) Desk = Gs->GetDesktopResolution();
	TArray<FString> Out;
	for (const FIntPoint& R : Common) if (Desk.X <= 0 || (R.X <= Desk.X && R.Y <= Desk.Y)) Out.Add(FString::Printf(TEXT("%dx%d"), R.X, R.Y));
	if (Out.Num() == 0) Out.Add(TEXT("1280x720"));
	return Out;
}

void ARDDungeonGenerator::FitPendingResolution()
{
	// (the size chosen kept among the display mode's choices: the largest of them no larger than it)
	// (none no larger: the smallest of them)
	const TArray<FString> Ch = GetResolutionChoices();
	FIntPoint Best(0, 0), Smallest(MAX_int32, MAX_int32);
	for (const FString& C : Ch)
	{
		FString Xs, Ys; C.Split(TEXT("x"), &Xs, &Ys);
		const FIntPoint R(FCString::Atoi(*Xs), FCString::Atoi(*Ys));
		if (R.X <= PendingResolution.X && R.Y <= PendingResolution.Y && R.X > Best.X) Best = R;
		if (R.X < Smallest.X) Smallest = R;
	}
	if (Best.X > 0) PendingResolution = Best;
	else if (Smallest.X < MAX_int32) PendingResolution = Smallest;
}

void ARDDungeonGenerator::OpenOptionsPage()
{
	MenuPage = 1; MenuCursor = 0;
	// (what the game runs at now, as the choices start; a size not among them goes to the nearest one below)
	const UGameUserSettings* Gs = GEngine ? GEngine->GetGameUserSettings() : nullptr;
	PendingWindowMode = Gs ? FMath::Clamp((int32)Gs->GetFullscreenMode(), 0, 2) : 1;
	const FIntPoint Now = Gs ? Gs->GetScreenResolution() : FIntPoint(1920, 1080);
	const TArray<FString> Ch = GetResolutionChoices();
	PendingResolution = FIntPoint(1280, 720);
	for (const FString& C : Ch)
	{
		FString Xs, Ys; C.Split(TEXT("x"), &Xs, &Ys);
		const FIntPoint R(FCString::Atoi(*Xs), FCString::Atoi(*Ys));
		if (R.X <= Now.X && R.Y <= Now.Y) PendingResolution = R;
	}
}

bool ARDDungeonGenerator::ApplyDisplaySettings()
{
	UGameUserSettings* Gs = GEngine ? GEngine->GetGameUserSettings() : nullptr;
	if (!Gs) { LastApplied = TEXT("no user settings"); return false; }
	const EWindowMode::Type Mode = (EWindowMode::Type)FMath::Clamp(PendingWindowMode, 0, 2);
	// (windowed fullscreen: the screen's own size, which is what that window is anyway)
	const FIntPoint Res = Mode == EWindowMode::WindowedFullscreen ? Gs->GetDesktopResolution() : PendingResolution;
	Gs->SetFullscreenMode(Mode);
	Gs->SetScreenResolution(Res);
	if (GIsEditor)
	{
		// (play in the editor does not own its window: the choice goes to the editor's own user settings, not the packaged
		// game's (those are its own, in its Saved folder), and is not applied; the game is checked by package_mistward.ps1's
		// test with -RDApplyDisplay, its window measured)
		Gs->ConfirmVideoMode(); Gs->SaveSettings();
		LastApplied = FString::Printf(TEXT("saved %dx%d mode %d in the editor's user settings (the editor's play window keeps its size)"), Res.X, Res.Y, (int32)Mode);
	}
	else
	{
		Gs->ApplySettings(false); Gs->ConfirmVideoMode(); Gs->SaveSettings();
		LastApplied = FString::Printf(TEXT("applied %dx%d mode %d"), Res.X, Res.Y, (int32)Mode);
	}
	UE_LOG(LogRDMistward4, Log, TEXT("RDOPTIONS %s"), *LastApplied);
	return true;
}

void ARDDungeonGenerator::ApplyDisplayFromCommandLine()
{
	FString S;
	if (!FParse::Value(FCommandLine::Get(), TEXT("RDApplyDisplay="), S)) return;
	TArray<FString> P; S.ParseIntoArray(P, TEXT("x"));
	if (P.Num() < 3) { UE_LOG(LogRDMistward4, Warning, TEXT("RDOPTIONS -RDApplyDisplay=%s: want <width>x<height>x<mode>"), *S); return; }
	PendingResolution = FIntPoint(FCString::Atoi(*P[0]), FCString::Atoi(*P[1])); PendingWindowMode = FMath::Clamp(FCString::Atoi(*P[2]), 0, 2);
	FitPendingResolution();
	ApplyDisplaySettings();
}

// ================================================================================================ her allies keep apart
bool ARDDungeonGenerator::FindAllySpot(const FVector& From, const FVector& Facing, float Radius, const AActor* Ignore, FVector& OutAt, const FVector& Prefer) const
{
	UWorld* W = GetWorld();
	if (!W) { OutAt = From + Facing * 230.f; return false; }
	FVector Fw = Facing; Fw.Z = 0.f; Fw = Fw.GetSafeNormal();
	if (Fw.IsNearlyZero()) Fw = FVector::ForwardVector;
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDAllySpot), false, Ignore);
	for (const ARDMonster* A : Allies) if (IsValid(A)) Q.AddIgnoredActor(A);
	// (the ways round Facing, nearest first; of each pair the one toward Prefer (her front) first, and those behind her
	// (where her camera is: its boom stopped on allies there) only when nothing else is clear: the PR review's find)
	FVector Pf = Prefer; Pf.Z = 0.f; Pf = Pf.GetSafeNormal();
	TArray<FVector> Ways;
	for (const float A : { 0.f, 35.f, 70.f, 110.f, 150.f, 180.f })
	{
		FVector W1 = Fw.RotateAngleAxis(A, FVector::UpVector), W2 = Fw.RotateAngleAxis(-A, FVector::UpVector);
		if (!Pf.IsNearlyZero() && FVector::DotProduct(W2, Pf) > FVector::DotProduct(W1, Pf)) Swap(W1, W2);
		Ways.Add(W1); if (A > 0.f && A < 180.f) Ways.Add(W2);
	}
	if (!Pf.IsNearlyZero()) Ways.StableSort([&Pf](const FVector& X, const FVector& Y) { return (FVector::DotProduct(X, Pf) >= -0.5f) && !(FVector::DotProduct(Y, Pf) >= -0.5f); });
	float BestRoom = -1e9f; FVector Best = From + Fw * 230.f;
	for (const float Dist : { 230.f, 330.f })
		for (const FVector& Way : Ways)
		{
			const FVector P = From + Way * Dist;
			// (a wall on the way: the spot comes in, but no nearer than its radius and the gap to the wall; no wall: the whole
			// way (it was cut short by half a radius less the gap whatever there was, so no spot was ever clear for an ally
			// under 50 cm across: the PR review's find))
			FHitResult H;
			float Reach = Dist;
			if (W->SweepSingleByChannel(H, From, P, FQuat::Identity, ECC_Visibility, FCollisionShape::MakeSphere(Radius * 0.6f), Q))
				Reach = FMath::Min(Dist, H.Distance - Radius * 0.5f - RD4AllyGap);
			const FVector S = From + Way * FMath::Max(Reach, 0.f);
			// (the least room left round it: to the wall and to every ally standing, and to her)
			float Room = Reach - Dist;
			for (const ARDMonster* A : Allies)
			{
				if (!IsValid(A) || A->IsDead()) continue;
				const float Need = Radius + A->GetCapsuleComponent()->GetScaledCapsuleRadius() + RD4AllyGap;
				Room = FMath::Min(Room, FVector::Dist2D(S, A->GetActorLocation()) - Need);
			}
			Room = FMath::Min(Room, FVector::Dist2D(S, From) - (Radius + 34.f + RD4AllyGap));
			if (Room >= 0.f) { OutAt = S; return true; }
			if (Room > BestRoom) { BestRoom = Room; Best = S; }
		}
	OutAt = Best;
	return false;
}

FVector ARDMonster::AllySpacingPush() const
{
	// (each ally nearer than their two capsules and the gap pushes it away, the more the nearer; she does too: an ally
	// standing in her was the camera's trouble before)
	const ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	if (!bAlly || !G || !G->bAllySpacing) return FVector::ZeroVector;
	const FVector L = GetActorLocation();
	const float R0 = GetCapsuleComponent()->GetScaledCapsuleRadius();
	FVector Push = FVector::ZeroVector;
	auto Away = [&](const FVector& O, float Need, uint32 Salt)
	{
		FVector D = L - O; D.Z = 0.f;
		const float Dd = D.Size();
		if (Dd >= Need) return;
		// (exactly on each other: a way from their ids, so the two go opposite ways)
		const FVector U = Dd > 1.f ? D / Dd : FVector(1.f, 0.f, 0.f).RotateAngleAxis((float)((GetUniqueID() * 37u + Salt) % 360u), FVector::UpVector);
		Push += U * ((Need - Dd) / Need);
	};
	for (const ARDMonster* A : G->GetAllies())
		if (A && A != this && IsValid(A) && !A->IsDead())
			Away(A->GetActorLocation(), R0 + A->GetCapsuleComponent()->GetScaledCapsuleRadius() + RD4AllyGap, A->GetUniqueID());
	if (const URDCombatComponent* Pc = G->GetPlayerCombat(); Pc && Pc->GetOwner())
		Away(Pc->GetOwner()->GetActorLocation(), R0 + 34.f + RD4AllyGap, 7u);
	return Push;
}

FVector ARDMonster::AllySteer(const FVector& Dir) const
{
	const FVector Dn = FVector(Dir.X, Dir.Y, 0.f).GetSafeNormal();
	FVector P = AllySpacingPush();
	if (P.IsNearlyZero()) return Dn;
	const float Back = FVector::DotProduct(P, Dn);
	if (Back < 0.f) P -= Dn * Back;
	return (Dn + P * 1.5f).GetSafeNormal();
}
