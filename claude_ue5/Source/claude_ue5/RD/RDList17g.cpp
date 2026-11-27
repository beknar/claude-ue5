// The user's list of 2026-11-26 (docs/improvements17.txt; the plan docs/improvements17_plan.md), its ninth phase: the packaged game's run of
// Closed Structures (-RDTownGo=closed, with -RDStructures=closed): in Brokenspire once it is built round her, she stands before the general
// store's door, F (the game's own way, BuildingDoorUse17) takes her in, and once the building's level is laid round her the run writes its
// mark ("closed|<label>|<pieces laid>|<panes>|<hero>") and leaves by the door.
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
		// (the town built round her, Closed: the general store, else any enterable building with its record)
		if (!S || S->IsBuilding() || !bTownPlaced || bTownLoading || IsCoverUp16()) return;
		if (!S->BldClosed17) { UE_LOG(LogRDList17g, Warning, TEXT("RDGO17 the town is not closed (-RDStructures=closed?)")); Go17Stage = -1; return; }
		int32 Bi = -1;
		for (int32 I = 0; I < S->TownBlds.Num(); ++I) if (S->HasRecord17(I) && S->TownBlds[I].Kind == TK_Store && S->TownBlds[I].Door >= 0) { Bi = I; break; }
		for (int32 I = 0; I < S->TownBlds.Num() && Bi < 0; ++I) if (S->HasRecord17(I) && S->TownBlds[I].Door >= 0) Bi = I;
		if (Bi < 0) { UE_LOG(LogRDList17g, Warning, TEXT("RDGO17 no closed building with a door")); Go17Stage = -1; return; }
		const ARDSection::FTownBld& B = S->TownBlds[Bi];
		const FVector Out(RDL17gDir4[B.DoorSide].X, RDL17gDir4[B.DoorSide].Y, 0.f);
		const FVector At = S->LocalToWorld(B.DoorTile) + Out * (TileSize * 0.5f + 150.f);
		Her->SetActorLocation(FVector(At.X, At.Y, Her->GetActorLocation().Z), false, nullptr, ETeleportType::TeleportPhysics);
		if (ACharacter* Ch = Cast<ACharacter>(Her)) Ch->GetCharacterMovement()->StopMovementImmediately();
		Her->SetActorRotation(FRotator(0.f, (-Out).Rotation().Yaw, 0.f));
		Go17Bld = Bi; Go17At = Now; Go17Stage = 1;
		UE_LOG(LogRDList17g, Log, TEXT("RDGO17 before %s's door"), *RDTTheLabel17(S, Bi));
		return;
	}
	case 1:
	{
		if (Now - Go17At < 1.5f) return;
		const FString R = BuildingDoorUse17(Her->GetActorLocation(), 1e9f, nullptr, false, -1);
		UE_LOG(LogRDList17g, Log, TEXT("RDGO17 F at the door: %s"), R.IsEmpty() ? TEXT("nothing") : *R);
		if (R.IsEmpty()) { if (Now - Go17At > 20.f) Go17Stage = -1; return; }
		Go17At = Now; Go17Stage = 2;
		return;
	}
	case 2:
	{
		if (InBuilding17 != Go17Bld || IsCoverUp16()) { if (Now - Go17At > 30.f) { UE_LOG(LogRDList17g, Warning, TEXT("RDGO17 never inside")); Go17Stage = -1; } return; }
		if (Now - Go17At < 1.0f) return;
		WriteTestMark(TEXT("closed"), FString::Printf(TEXT("%s|%d|%d"), S ? *RDTTheLabel17(S, Go17Bld) : TEXT("?"), Building17Pieces, Building17Panes));
		UE_LOG(LogRDList17g, Log, TEXT("RDGO17 inside: %d pieces, %d panes"), Building17Pieces, Building17Panes);
		LeaveBuilding17();
		Go17Stage = -1;
		return;
	}
	default: Go17Stage = -1;
	}
}
