// The user's list of 2026-11-26 (docs/improvements17.txt; the plan docs/improvements17_plan.md), its ninth phase: the packaged game's run of
// Closed Structures (-RDTownGo=closed, with -RDStructures=closed): in Brokenspire once it is built round her, she stands before the general
// store's door, F (the game's own way, BuildingDoorUse17) takes her in, and once the building's level is laid round her the run writes its
// mark ("closed|<label>|<pieces laid>|<panes>|<hero>") and leaves by the door. A door F refuses (a townsperson standing at it) is given up
// after 8 s for the next closed building with a door; a level laid with no pieces writes no mark.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList17g, Log, All);

namespace
{
	const FIntPoint RDL17gDir4[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };
	/** the closed buildings with a door, the general store first */
	TArray<int32> RDL17gOrder(ARDSection* S)
	{
		TArray<int32> Out;
		for (int32 I = 0; I < S->TownBlds.Num(); ++I) if (S->HasRecord17(I) && S->TownBlds[I].Kind == TK_Store && S->TownBlds[I].Door >= 0) Out.Add(I);
		for (int32 I = 0; I < S->TownBlds.Num(); ++I) if (S->HasRecord17(I) && S->TownBlds[I].Kind != TK_Store && S->TownBlds[I].Door >= 0) Out.Add(I);
		return Out;
	}
}

void ARDDungeonGenerator::TickGo17(APawn* Her)
{
	if (Go17Stage < 0 || !Her) return;
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	const float Now = GetWorld()->GetRealTimeSeconds();
	switch (Go17Stage)
	{
	case 0:
	{
		// (the town built round her, Closed: the next closed building with a door, the general store first)
		if (!S || S->IsBuilding() || !bTownPlaced || bTownLoading || IsCoverUp16()) return;
		if (!S->BldClosed17) { UE_LOG(LogRDList17g, Warning, TEXT("RDGO17 the town is not closed (-RDStructures=closed?)")); Go17Stage = -1; return; }
		const TArray<int32> Order = RDL17gOrder(S);
		if (!Order.IsValidIndex(Go17Try)) { UE_LOG(LogRDList17g, Warning, TEXT("RDGO17 no closed building with a door took her in (%d tried)"), Go17Try); Go17Stage = -1; return; }
		const int32 Bi = Order[Go17Try];
		const ARDSection::FTownBld& B = S->TownBlds[Bi];
		const FVector Out(RDL17gDir4[B.DoorSide].X, RDL17gDir4[B.DoorSide].Y, 0.f);
		const FVector At = S->LocalToWorld(B.DoorTile) + Out * (TileSize * 0.5f + 150.f);
		Her->SetActorLocation(FVector(At.X, At.Y, Her->GetActorLocation().Z), false, nullptr, ETeleportType::TeleportPhysics);
		if (ACharacter* Ch = Cast<ACharacter>(Her)) Ch->GetCharacterMovement()->StopMovementImmediately();
		Her->SetActorRotation(FRotator(0.f, (-Out).Rotation().Yaw, 0.f));
		Go17Bld = Bi; Go17At = Now; Go17LogAt = 0.f; Go17Stage = 1;
		UE_LOG(LogRDList17g, Log, TEXT("RDGO17 before %s's door"), *RDTTheLabel17(S, Bi));
		return;
	}
	case 1:
	{
		if (Now - Go17At < 1.5f) return;
		const FString R = BuildingDoorUse17(Her->GetActorLocation(), 1e9f, nullptr, false, -1);
		if (R.IsEmpty())
		{
			// (refused: a townsperson at the door, say; logged once a second, the next building after 8 s)
			if (Now - Go17LogAt >= 1.f) { Go17LogAt = Now; UE_LOG(LogRDList17g, Log, TEXT("RDGO17 F at the door: nothing")); }
			if (Now - Go17At > 8.f) { UE_LOG(LogRDList17g, Warning, TEXT("RDGO17 %s's door refused F: the next building"), S ? *RDTTheLabel17(S, Go17Bld) : TEXT("?")); ++Go17Try; Go17Stage = 0; }
			return;
		}
		UE_LOG(LogRDList17g, Log, TEXT("RDGO17 F at the door: %s"), *R);
		Go17At = Now; Go17InAt = -1.f; Go17Stage = 2;
		return;
	}
	case 2:
	{
		// (inside once the level is laid and the cover down: at most a minute, as the cover's own limit; settled a second from then)
		if (InBuilding17 != Go17Bld || IsCoverUp16()) { Go17InAt = -1.f; if (Now - Go17At > 60.f) { UE_LOG(LogRDList17g, Warning, TEXT("RDGO17 never inside")); Go17Stage = -1; } return; }
		if (Go17InAt < 0.f) Go17InAt = Now;
		if (Now - Go17InAt < 1.0f) return;
		if (Building17Pieces <= 0) { UE_LOG(LogRDList17g, Warning, TEXT("RDGO17 inside, but the level laid no pieces: no mark")); }
		else WriteTestMark(TEXT("closed"), FString::Printf(TEXT("%s|%d|%d"), S ? *RDTTheLabel17(S, Go17Bld) : TEXT("?"), Building17Pieces, Building17Panes));
		UE_LOG(LogRDList17g, Log, TEXT("RDGO17 inside: %d pieces, %d panes"), Building17Pieces, Building17Panes);
		LeaveBuilding17();
		Go17Stage = -1;
		return;
	}
	default: Go17Stage = -1;
	}
}
