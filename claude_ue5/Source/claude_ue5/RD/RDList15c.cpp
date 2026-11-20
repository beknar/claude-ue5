// The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), its fourth phase: the dungeon.
// Item 5, "there should be an oven in the starting room in a dungeon": a bread oven by the great hall's anvil, as the forge and the
// alchemist's table are put there (no random draw). Item 7, "bookshelf doors should open when searched": the Gothic bookshelf has no
// doors, and stood with its back panel to the room (its pieces' Adjust turned it the wrong way, 934 shelves); the doors are that
// panel's own mesh cut in two (blender_numpy/shelf_doors15.py), hung on hinges across its open front, swung open once it is searched.
// Item 11, the chapels' pews (RDSection.cpp's Furnish). Items 6 and 8 are the HUD's (RDHUD.cpp) and the map's input
// (RDDungeonGenerator.cpp).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDCombat.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList15c, Log, All);

// ================================================================================================ item 7: the shelves' doors
void ARDSection::MakeShelfDoors15(int32 I)
{
	if (!Generator || !Generator->bShelfDoors15 || !Shelves.IsValidIndex(I) || !Generator->ShelfDoorL15 || !Generator->ShelfDoorR15) return;
	// (only on the Gothic bookshelf the leaves were cut from: a themed shelf (Heaven's) is another mesh)
	const FRDPiece* P = Pc(TEXT("Bookshelf"));
	if (!P || !P->ActorClass) return;
	FShelf& Sh = Shelves[I];
	const FRotator Yr(0.f, Sh.Yaw, 0.f);
	const FVector2D H = Generator->ShelfDoorHinge15;
	auto Leaf = [&](UStaticMesh* M, float Side) -> UStaticMeshComponent*
	{
		UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
		C->SetMobility(EComponentMobility::Movable);
		C->SetStaticMesh(M);
		C->SetCollisionEnabled(ECollisionEnabled::NoCollision);          // (the cabinet itself stops her; a swung leaf must not)
		C->SetCanEverAffectNavigation(false);
		C->SetupAttachment(GetRootComponent());
		C->RegisterComponent();
		C->SetWorldLocationAndRotation(Sh.At + Yr.RotateVector(FVector(H.X, Side * H.Y, 0.f)), Yr);
		return C;
	};
	Sh.DoorL = Leaf(Generator->ShelfDoorL15, 1.f);
	Sh.DoorR = Leaf(Generator->ShelfDoorR15, -1.f);
	// (one searched before this set was made again stands open)
	if (Generator->ShelvesSearched.Contains(FIntVector(Coord.X, Coord.Y, I))) OpenShelfDoors15(I);
}

void ARDSection::OpenShelfDoors15(int32 I)
{
	if (!Generator || !Shelves.IsValidIndex(I)) return;
	FShelf& Sh = Shelves[I];
	// (each leaf turns about its hinge out toward the room: the left (hinged at +Y, running along -Y) by +, the right by -)
	const float A = Generator->ShelfDoorOpenDeg15;
	if (Sh.DoorL.IsValid()) Sh.DoorL->SetWorldRotation(FRotator(0.f, Sh.Yaw + A, 0.f));
	if (Sh.DoorR.IsValid()) Sh.DoorR->SetWorldRotation(FRotator(0.f, Sh.Yaw - A, 0.f));
}

FString ARDDungeonGenerator::GetShelfDoors15(FIntPoint Section) const
{
	const ARDSection* S = GetSection(Section);
	if (!S) return TEXT("0|");
	TArray<FString> P;
	for (int32 I = 0; I < S->Shelves.Num(); ++I)
	{
		const ARDSection::FShelf& Sh = S->Shelves[I];
		P.Add(FString::Printf(TEXT("%d:%.0f:%.0f:%.1f:%d:%.1f:%.1f"), I, Sh.At.X, Sh.At.Y, Sh.Yaw, ShelvesSearched.Contains(FIntVector(Section.X, Section.Y, I)) ? 1 : 0,
			Sh.DoorL.IsValid() ? Sh.DoorL->GetComponentRotation().Yaw : -999.f, Sh.DoorR.IsValid() ? Sh.DoorR->GetComponentRotation().Yaw : -999.f));
	}
	return FString::Printf(TEXT("%d|%s"), S->Shelves.Num(), *FString::Join(P, TEXT("|")));
}

// ================================================================================================ item 8: the wheel on the map
bool URDCombatComponent::MapWheel15() const
{
	return Generator && Generator->bMapZoom15 && Generator->bMapOpen && Generator->bTacticalMaps && !Generator->bTown;
}

// ================================================================================================ item 11: the pews (a test's)
TArray<FString> ARDDungeonGenerator::GetChapelPews15(FIntPoint Section) const
{
	TArray<FString> Out;
	const ARDSection* S = GetSection(Section);
	if (!S) return Out;
	for (const ARDSection::FChapel15& Ch : S->Chapels15)
	{
		TArray<FString> Pw;
		for (const FTransform& T : Ch.Pews) Pw.Add(FString::Printf(TEXT("%.0f:%.0f:%.1f"), T.GetLocation().X, T.GetLocation().Y, T.Rotator().Yaw));
		Out.Add(FString::Printf(TEXT("%d|%.0f|%.0f|%s"), Ch.Room, Ch.Altar.X, Ch.Altar.Y, *FString::Join(Pw, TEXT(";"))));
	}
	return Out;
}

// ================================================================================================ item 5: the great hall's oven
void ARDSection::EnsureOven15()
{
	// (the start set's great hall (the room at the origin tile, as EnsureAnvil finds it) gets a bread oven on a free tile off the
	// lanes whose four neighbours are free, the nearest such to its anvil; no random stream is drawn. Recorded as the kitchens' are
	// (TownOvens, AddPiece's "BreadOven" under bDungeonOvens), so F at it bakes)
	if (!Generator || !Generator->bStartOven15 || TownBlds.Num() > 0 || !Generator->IsStartSection(Coord)) return;
	const int32 RI = RoomAt(FVector(Generator->TileSize * 0.5f, Generator->TileSize * 0.5f, 0.f));
	if (!Rooms.IsValidIndex(RI)) return;
	if (TownOvens.ContainsByPredicate([this, RI](const FVector& O) { return RoomAt(O) == RI; })) return;
	const FRDPiece* P = Pc(Generator->OvenPiece15);
	if (!P) { UE_LOG(LogRDList15c, Warning, TEXT("RDOVEN15 no piece %s"), *Generator->OvenPiece15.ToString()); return; }
	const FRoom& Rm = Rooms[RI];
	auto Free = [&](FIntPoint T) { return In(T) && Type[Idx(T)] == 1 && !Blocked[Idx(T)] && RoomAtLocal(T) == RI; };
	const FVector An = AnvilPoints.ContainsByPredicate([this, RI](const FVector& A) { return RoomAt(A) == RI; })
		? *AnvilPoints.FindByPredicate([this, RI](const FVector& A) { return RoomAt(A) == RI; }) : GetRoomCenter(RI);
	FIntPoint Pick(-1, -1); float PickD = MAX_flt;
	for (int32 X = Rm.Min.X + 1; X < Rm.Max.X - 1; ++X)
		for (int32 Y = Rm.Min.Y + 1; Y < Rm.Max.Y - 1; ++Y)
		{
			if (X == Rm.Lane.X || Y == Rm.Lane.Y) continue;
			const FIntPoint T(X, Y);
			if (!Free(T) || !Free(T + FIntPoint(1, 0)) || !Free(T + FIntPoint(-1, 0)) || !Free(T + FIntPoint(0, 1)) || !Free(T + FIntPoint(0, -1))) continue;
			const float D = FVector::DistSquared2D(TileWorld(T), An);
			if (D < PickD) { PickD = D; Pick = T; }
		}
	if (Pick.X < 0) { UE_LOG(LogRDList15c, Warning, TEXT("RDOVEN15 no room for the oven in the great hall")); return; }
	const FVector At = TileWorld(Pick);
	// (its mouth, its front, toward the room's lane: where she stands to bake)
	const FVector ToLane = FMath::Abs(Pick.X - Rm.Lane.X) > FMath::Abs(Pick.Y - Rm.Lane.Y) ? FVector(FMath::Sign((float)(Rm.Lane.X - Pick.X)), 0.f, 0.f) : FVector(0.f, FMath::Sign((float)(Rm.Lane.Y - Pick.Y)), 0.f);
	const float Yaw = ToLane.Rotation().Yaw;
	AddPieceAt(Generator->OvenPiece15, At, Yaw);
	MarkBlocked(At, Yaw, FVector2D(P->Size.X, P->Size.Y));
	if (!TownOvens.ContainsByPredicate([&At](const FVector& O) { return FVector::Dist2D(O, At) < 10.f; })) TownOvens.Add(At);
	UE_LOG(LogRDList15c, Log, TEXT("RDOVEN15 an oven in the great hall at (%.0f, %.0f), %.0f m from its anvil"), At.X, At.Y, FMath::Sqrt(PickD) / 100.f);
}
