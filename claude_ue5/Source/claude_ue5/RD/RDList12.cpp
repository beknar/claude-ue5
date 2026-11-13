// The user's list of 2026-11-12 (docs/improvements12.txt), its first phase:
//   - "enable mouse on the big wilderness map": the pointer is up while the big map is open in the towns and the wilds (its
//     wheel and drag were there, but the game kept the mouse captured and hidden); the place under the pointer is the one picked
//     (the HUD's), a click on it travels there; the wheel zooms about the pointer
//   - "in the console, enable click to teleport on a point on the map, when the map has been revealed": rd.MapTeleport; with it
//     on, a click on any big map (the wilds', a town's, a dungeon's) teleports her to that point once rd.RevealMap shows it all
// The HUD writes the map's screen frame as it draws it (MapXC, MapXVw, MapXK, MapXSheet, MapXKind).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDCombat.h"
#include "RD/RDWild.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Components/CapsuleComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDList12, Log, All);

namespace
{
	constexpr float RD12ClickSlopPx = 6.f;          // (a press that moved less than this before it was let go is a click, not a drag)
}

bool ARDDungeonGenerator::MapScreenToWorld(FVector2D Screen, FVector& Out) const
{
	if (MapXKind == 0 || MapXK <= 0.f || !MapXSheet.bIsValid || !MapXSheet.IsInside(Screen)) return false;
	// (the HUD's ToS: S = C + (W.Y - Vw.Y, -(W.X - Vw.X)) x K)
	const FVector2D D = (Screen - MapXC) / MapXK;
	Out = FVector(MapXVw.X - D.Y, MapXVw.Y + D.X, 0.0);
	return true;
}

bool ARDDungeonGenerator::MapTeleportTo(const FVector& World)
{
	APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Her) return false;
	if (MapXKind == 1 && bWild && IsWildReady())
	{
		// (the wilds: into a town's ground by that town's own travel (its gate, the town built round her); else put down there,
		// the chunks made at once, a town far behind her let go as the map's travel does)
		const FVector2D Wm(World.X / 100.0, World.Y / 100.0);
		for (int32 Ti = 0; Ti < Wild->Towns.Num(); ++Ti)
			if (FVector2D::Distance(Wm, Wild->Towns[Ti].Site) < 262.0)
			{
				bTravelForced = true;
				const bool bOk = WildTravelToTown(Wild->Towns[Ti].Name);
				bTravelForced = false;
				return bOk;
			}
		if (WildTownIdx >= 0 && Wild->Towns.IsValidIndex(WildTownIdx) && FVector2D::Distance(Wm, Wild->Towns[WildTownIdx].Site) > WildTownDropM) UnloadWildTown();
		return WildPutHer((float)Wm.X, (float)Wm.Y);
	}
	// (a town's map or a dungeon's: onto what is there, traced down from well over it; refused where nothing is)
	FHitResult Hit;
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RD12Teleport), false, Her);
	const FVector From(World.X, World.Y, Her->GetActorLocation().Z + 3000.0), To(World.X, World.Y, Her->GetActorLocation().Z - 6000.0);
	if (!GetWorld()->LineTraceSingleByChannel(Hit, From, To, ECC_Visibility, Q)) return false;
	const ACharacter* Ch = Cast<ACharacter>(Her);
	const float Half = Ch && Ch->GetCapsuleComponent() ? Ch->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() : 90.f;
	// (under a roof or a vault the trace meets the roof first: from just over the floor she stood on, down)
	FVector At = Hit.ImpactPoint;
	if (At.Z > Her->GetActorLocation().Z + 400.f)
	{
		FHitResult H2;
		if (GetWorld()->LineTraceSingleByChannel(H2, FVector(World.X, World.Y, Her->GetActorLocation().Z + 150.f), To, ECC_Visibility, Q)) At = H2.ImpactPoint;
	}
	Her->SetActorLocation(At + FVector(0, 0, Half + 5.f), false, nullptr, ETeleportType::TeleportPhysics);
	if (ACharacter* C = Cast<ACharacter>(Her)) C->GetCharacterMovement()->StopMovementImmediately();
	return true;
}

bool ARDDungeonGenerator::ClickMapAt(FVector2D Screen)
{
	LastMapClick.Reset();
	FVector W = FVector::ZeroVector;
	if (!MapScreenToWorld(Screen, W)) { LastMapClick = TEXT("off the map"); return false; }
	if (bMapClickTeleport)
	{
		if (!bMapRevealAll)
		{
			LastMapClick = TEXT("refused: reveal the map first (rd.RevealMap)");
			if (PlayerCombat) PlayerCombat->ShowMessage(TEXT("rd.MapTeleport: reveal the map first (rd.RevealMap)"));
			return false;
		}
		const bool bOk = MapTeleportTo(W);
		LastMapClick = FString::Printf(TEXT("%s %.0f %.0f"), bOk ? TEXT("teleported") : TEXT("refused: nothing to stand on at"), W.X, W.Y);
		if (bOk)
		{
			++MapTeleports;
			if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("Teleported (%.0f, %.0f m)"), W.X / 100.0, W.Y / 100.0));
			SetMapOpen(false);
		}
		UE_LOG(LogRDList12, Log, TEXT("RDMAPCLICK %s"), *LastMapClick);
		return bOk;
	}
	// (the wilds' map: the place under the pointer, if found, by the map's travel)
	if (MapXKind == 1 && WildMapHover >= 0)
	{
		const bool bOk = WildFastTravel(WildMapHover);
		LastMapClick = bOk ? FString::Printf(TEXT("travelled %s"), *WildLastTravel) : FString::Printf(TEXT("refused: %s"), *WildTravelRefusal);
		return bOk;
	}
	LastMapClick = TEXT("nothing there");
	return false;
}

FString ARDDungeonGenerator::GetMapFrame() const
{
	return FString::Printf(TEXT("%d|%.2f|%.2f|%.1f|%.1f|%.8f|%.1f|%.1f|%.1f|%.1f"), MapXKind, MapXC.X, MapXC.Y, MapXVw.X, MapXVw.Y, MapXK,
		MapXSheet.Min.X, MapXSheet.Min.Y, MapXSheet.Max.X, MapXSheet.Max.Y);
}

TArray<FString> ARDDungeonGenerator::GetMenuBoxes() const
{
	TArray<FString> Out;
	for (const FBox2D& B : MenuRowBoxes) Out.Add(FString::Printf(TEXT("%.1f|%.1f|%.1f|%.1f"), B.Min.X, B.Min.Y, B.Max.X, B.Max.Y));
	return Out;
}

void ARDDungeonGenerator::TickMapPointer(APlayerController* PC)
{
	if (!PC || !PlayerCombat) return;
	// (the pointer up while the big map wants it, whoever put it down (the Escape menu sets the cursor itself); down again when
	// the map closes, unless a list or the menu has it)
	const bool bWant = WantsMapPointer() && !bMenuOpen;
	if (bWant && !PC->ShouldShowMouseCursor()) { PlayerCombat->SetPointerShown(true); bMapPointerUp = true; }
	else if (!bWant && bMapPointerUp)
	{
		bMapPointerUp = false;
		if (!bMenuOpen && !PlayerCombat->IsInventoryOpen() && !PlayerCombat->IsCraftingOpen() && !IsTownPanelOpen()) PlayerCombat->SetPointerShown(false);
	}
	if (!bWant) { bMapPress = false; return; }
	// a click (a press let go within a few pixels of where it began: a drag moves the map instead)
	float Mx = 0.f, My = 0.f;
	if (!PC->GetMousePosition(Mx, My)) return;
	const FVector2D M(Mx, My);
	const bool bPressed = PC->WasInputKeyJustPressed(EKeys::LeftMouseButton), bReleased = PC->WasInputKeyJustReleased(EKeys::LeftMouseButton);
	if (bPressed || bReleased) UE_LOG(LogRDList12, Log, TEXT("RDMAPPOINTER %s%s at (%.0f, %.0f), pressed at (%.0f, %.0f), map %d"), bPressed ? TEXT("press ") : TEXT(""), bReleased ? TEXT("release") : TEXT(""), M.X, M.Y, MapPressAt.X, MapPressAt.Y, MapXKind);
	if (bPressed) { bMapPress = true; MapPressAt = M; }
	if (bMapPress && PC->IsInputKeyDown(EKeys::LeftMouseButton) && FVector2D::Distance(M, MapPressAt) > RD12ClickSlopPx) { bMapPress = false; UE_LOG(LogRDList12, Log, TEXT("RDMAPPOINTER a drag, not a click (%.0f, %.0f)"), M.X, M.Y); }
	if (bMapPress && bReleased) { bMapPress = false; ClickMapAt(MapPressAt); }
}
