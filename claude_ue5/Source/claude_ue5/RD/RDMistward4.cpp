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
	// (the common sizes, none larger than the screen: a window larger than it would hang off its edges)
	static const FIntPoint Common[5] = { { 1280, 720 }, { 1600, 900 }, { 1920, 1080 }, { 2560, 1440 }, { 3840, 2160 } };
	FIntPoint Desk(3840, 2160);
	if (const UGameUserSettings* Gs = GEngine ? GEngine->GetGameUserSettings() : nullptr) Desk = Gs->GetDesktopResolution();
	TArray<FString> Out;
	for (const FIntPoint& R : Common) if (Desk.X <= 0 || (R.X <= Desk.X && R.Y <= Desk.Y)) Out.Add(FString::Printf(TEXT("%dx%d"), R.X, R.Y));
	if (Out.Num() == 0) Out.Add(TEXT("1280x720"));
	return Out;
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
		// (play in the editor does not own its window: the choice is saved for the game, not applied here)
		Gs->ConfirmVideoMode(); Gs->SaveSettings();
		LastApplied = FString::Printf(TEXT("saved %dx%d mode %d (the editor's play window keeps its size)"), Res.X, Res.Y, (int32)Mode);
	}
	else
	{
		Gs->ApplySettings(false); Gs->ConfirmVideoMode(); Gs->SaveSettings();
		LastApplied = FString::Printf(TEXT("applied %dx%d mode %d"), Res.X, Res.Y, (int32)Mode);
	}
	UE_LOG(LogRDMistward4, Log, TEXT("RDOPTIONS %s"), *LastApplied);
	return true;
}

// ================================================================================================ her allies keep apart
bool ARDDungeonGenerator::FindAllySpot(const FVector& From, const FVector& Facing, float Radius, const AActor* Ignore, FVector& OutAt) const
{
	UWorld* W = GetWorld();
	if (!W) { OutAt = From + Facing * 230.f; return false; }
	FVector Fw = Facing; Fw.Z = 0.f; Fw = Fw.GetSafeNormal();
	if (Fw.IsNearlyZero()) Fw = FVector::ForwardVector;
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDAllySpot), false, Ignore);
	for (const ARDMonster* A : Allies) if (IsValid(A)) Q.AddIgnoredActor(A);
	static const float Angles[] = { 0.f, 35.f, -35.f, 70.f, -70.f, 110.f, -110.f, 150.f, -150.f, 180.f };
	float BestRoom = -1e9f; FVector Best = From + Fw * 230.f;
	for (const float Dist : { 230.f, 330.f })
		for (const float Ang : Angles)
		{
			const FVector Way = Fw.RotateAngleAxis(Ang, FVector::UpVector);
			const FVector P = From + Way * Dist;
			// (a wall on the way: the spot comes in, but no nearer than its radius and the gap to the wall)
			FHitResult H;
			const float Wall = W->SweepSingleByChannel(H, From, P, FQuat::Identity, ECC_Visibility, FCollisionShape::MakeSphere(Radius * 0.6f), Q) ? H.Distance : Dist + Radius;
			const float Reach = FMath::Min(Dist, Wall - Radius * 0.5f - RD4AllyGap);
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
