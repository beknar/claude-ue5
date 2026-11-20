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
	// (interactive parts, as a door's leaves: made in play (bBuildInteractive), cleared with the others by ClearInteractive)
	if (!bBuildInteractive || !Generator || !Generator->bShelfDoors15 || !Shelves.IsValidIndex(I) || !Generator->ShelfDoorL15 || !Generator->ShelfDoorR15) return;
	// (only on the Gothic bookshelf the leaves were cut from: a themed shelf (Heaven's) is another mesh)
	const FRDPiece* P = Pc(TEXT("Bookshelf"));
	if (!P || !P->ActorClass) return;
	FShelf& Sh = Shelves[I];
	const FRotator Yr(0.f, Sh.Yaw, 0.f);
	const FVector2D H = Generator->ShelfDoorHinge15;
	const FTransform Root = GetRootComponent()->GetComponentTransform();
	auto Leaf = [&](UStaticMesh* M, float Side) -> USceneComponent*
	{
		const FTransform Hinge(Yr, Sh.At + Yr.RotateVector(FVector(H.X, Side * H.Y, 0.f)));
		USceneComponent* Pv = AddPivot(GetRootComponent(), Hinge.GetRelativeTransform(Root));
		AddMesh(Pv, M, FTransform::Identity, false);          // (the cabinet itself stops her; a swung leaf must not)
		return Pv;
	};
	Sh.DoorL = Leaf(Generator->ShelfDoorL15, 1.f);
	Sh.DoorR = Leaf(Generator->ShelfDoorR15, -1.f);
	Sh.Open15 = 0.f;
	// (one searched before this set was made again stands open)
	if (Generator->ShelvesSearched.Contains(FIntVector(Coord.X, Coord.Y, I))) OpenShelfDoors15(I, true);
}

void ARDSection::OpenShelfDoors15(int32 I, bool bNow)
{
	if (!Generator || !Shelves.IsValidIndex(I)) return;
	if (bNow) { Shelves[I].Open15 = 1.f; ShelfSwing15.Remove(I); }
	else ShelfSwing15.AddUnique(I);
	if (bNow) TickShelfDoors15(0.f);
}

void ARDSection::TickShelfDoors15(float Dt)
{
	// (each leaf turns about its hinge out toward the room, eased over ShelfDoorSwingSeconds15: the left (hinged at +Y, running
	// along -Y) by +, the right by -)
	const float A = Generator ? Generator->ShelfDoorOpenDeg15 : 105.f, Len = Generator ? FMath::Max(Generator->ShelfDoorSwingSeconds15, 0.05f) : 0.7f;
	auto Pose = [&](FShelf& Sh)
	{
		const float E = FMath::InterpEaseInOut(0.f, 1.f, FMath::Clamp(Sh.Open15, 0.f, 1.f), 2.f) * A;
		if (Sh.DoorL.IsValid()) Sh.DoorL->SetWorldRotation(FRotator(0.f, Sh.Yaw + E, 0.f));
		if (Sh.DoorR.IsValid()) Sh.DoorR->SetWorldRotation(FRotator(0.f, Sh.Yaw - E, 0.f));
	};
	for (int32 K = ShelfSwing15.Num() - 1; K >= 0; --K)
	{
		if (!Shelves.IsValidIndex(ShelfSwing15[K])) { ShelfSwing15.RemoveAt(K); continue; }
		FShelf& Sh = Shelves[ShelfSwing15[K]];
		Sh.Open15 = FMath::Min(1.f, Sh.Open15 + Dt / Len);
		Pose(Sh);
		if (Sh.Open15 >= 1.f) ShelfSwing15.RemoveAt(K);
	}
	if (Dt <= 0.f) for (FShelf& Sh : Shelves) if (Sh.Open15 >= 1.f) Pose(Sh);
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
	// (any big map that zooms by the wheel takes it: the dungeon's with bMapZoom15, the town's and the wilds' always (PR #96's review: on
	// brokenspire a notch zoomed the map and switched her weapon))
	return Generator && Generator->bMapOpen && Generator->bTacticalMaps && (Generator->bMapZoom15 || Generator->bTown || Generator->bWild);
}

float ARDDungeonGenerator::ReadMapZoomInput15(APlayerController* PC, float Dt) const
{
	if (!PC) return 1.f;
	const int32 Wheel = (PC->WasInputKeyJustPressed(EKeys::MouseScrollUp) ? 1 : 0) - (PC->WasInputKeyJustPressed(EKeys::MouseScrollDown) ? 1 : 0)
		+ (PC->WasInputKeyJustPressed(EKeys::Add) || PC->WasInputKeyJustPressed(EKeys::Equals) ? 1 : 0) - (PC->WasInputKeyJustPressed(EKeys::Subtract) || PC->WasInputKeyJustPressed(EKeys::Hyphen) ? 1 : 0);
	float F = Wheel != 0 ? FMath::Pow(1.25f, (float)Wheel) : 1.f;
	const float Rs = PC->GetInputAnalogKeyState(EKeys::Gamepad_RightY);
	if (FMath::Abs(Rs) > 0.2f) F *= FMath::Pow(2.2f, Rs * Dt);
	return F;
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
bool ARDSection::PlaceNearAnchor15(FName Piece, int32 RI, const FVector& Anchor, TArray<FVector>& Points)
{
	// (EnsureTables14's rule, shared by the tables and the oven (PR #96's review: a fourth copy of it))
	if (!Rooms.IsValidIndex(RI)) return false;
	const FRDPiece* P = Pc(Piece);
	if (!P) { UE_LOG(LogRDList15c, Warning, TEXT("RDPLACE15 no piece %s"), *Piece.ToString()); return false; }
	const FRoom& Rm = Rooms[RI];
	auto Free = [&](FIntPoint T) { return In(T) && Type[Idx(T)] == 1 && !Blocked[Idx(T)] && RoomAtLocal(T) == RI; };
	FIntPoint Pick(-1, -1); float PickD = MAX_flt;
	for (int32 X = Rm.Min.X + 1; X < Rm.Max.X - 1; ++X)
		for (int32 Y = Rm.Min.Y + 1; Y < Rm.Max.Y - 1; ++Y)
		{
			if (X == Rm.Lane.X || Y == Rm.Lane.Y) continue;
			const FIntPoint T(X, Y);
			if (!Free(T) || !Free(T + FIntPoint(1, 0)) || !Free(T + FIntPoint(-1, 0)) || !Free(T + FIntPoint(0, 1)) || !Free(T + FIntPoint(0, -1))) continue;
			const float D = FVector::DistSquared2D(TileWorld(T), Anchor);
			if (D < PickD) { PickD = D; Pick = T; }
		}
	if (Pick.X < 0) { UE_LOG(LogRDList15c, Warning, TEXT("RDPLACE15 no room for the %s in room %d (section %d,%d)"), *Piece.ToString(), RI, Coord.X, Coord.Y); return false; }
	const FVector At = TileWorld(Pick);
	// (its front, where she stands, toward the room's lane)
	const FVector ToLane = FMath::Abs(Pick.X - Rm.Lane.X) > FMath::Abs(Pick.Y - Rm.Lane.Y) ? FVector(FMath::Sign((float)(Rm.Lane.X - Pick.X)), 0.f, 0.f) : FVector(0.f, FMath::Sign((float)(Rm.Lane.Y - Pick.Y)), 0.f);
	const float Yaw = ToLane.Rotation().Yaw;
	AddPieceAt(Piece, At, Yaw);
	MarkBlocked(At, Yaw, FVector2D(P->Size.X, P->Size.Y));
	if (!Points.ContainsByPredicate([&At](const FVector& F) { return FVector::Dist2D(F, At) < 10.f; })) Points.Add(At);
	return true;
}

void ARDSection::EnsureOven15()
{
	// (the start set's great hall (the room at the origin tile, as EnsureAnvil finds it) gets a bread oven by its anvil, where ovens
	// bake (bDungeonOvens: PR #96's review, else it was marked and keyed and F did nothing); recorded as the kitchens' are
	// (TownOvens), so F at it bakes)
	if (!Generator || !Generator->bStartOven15 || !Generator->bDungeonOvens || TownBlds.Num() > 0 || !Generator->IsStartSection(Coord)) return;
	const int32 RI = RoomAt(FVector(Generator->TileSize * 0.5f, Generator->TileSize * 0.5f, 0.f));
	if (!Rooms.IsValidIndex(RI) || TownOvens.ContainsByPredicate([this, RI](const FVector& O) { return RoomAt(O) == RI; })) return;
	const FVector* An = AnvilPoints.FindByPredicate([this, RI](const FVector& A) { return RoomAt(A) == RI; });
	if (PlaceNearAnchor15(Generator->OvenPiece15, RI, An ? *An : GetRoomCenter(RI), TownOvens))
		UE_LOG(LogRDList15c, Log, TEXT("RDOVEN15 an oven in the great hall at (%.0f, %.0f)"), TownOvens.Last().X, TownOvens.Last().Y);
}
