// The user's list of 2026-11-16 (docs/improvements14.txt; the plan docs/improvements14_plan.md), its fifth phase: the alchemist's
// table, where potions are made (item 2), and the librarian's table, where scrolls are made (item 3), in the towns' fitting buildings
// and the dungeons. Behind the generator's bTables14 (927 tables, which also makes the two tables' pieces).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "RD/RDCombat.h"
#include "Engine/StaticMesh.h"
#include "Misc/ScopeExit.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDTables14, Log, All);

FName ARDDungeonGenerator::RecipeStation(const FRDRecipe& Rc) const
{
	if (!Rc.Station.IsNone() || !bTables14) return Rc.Station;
	return RecipeStationOf(Rc, FindItem(Rc.Item));
}

FName ARDDungeonGenerator::RecipeStationOf(const FRDRecipe& Rc, int32 Ix) const
{
	if (!Rc.Station.IsNone() || !bTables14) return Rc.Station;
	if (!Items.IsValidIndex(Ix)) return NAME_None;
	switch (Items[Ix].Kind)
	{
	case ERDItemKind::Healing: case ERDItemKind::Mana: case ERDItemKind::Speed: return FName(TEXT("Alchemist"));
	case ERDItemKind::Scroll: return FName(TEXT("Librarian"));
	default: return NAME_None;
	}
}

bool ARDDungeonGenerator::FindNearestTable14(FName Station, const FVector& From, float MaxDistance, FVector& At) const
{
	if (!bTables14) return false;
	const ARDSection* S = GetSection(WorldToSection(From));
	if (!S) return false;
	bool bFound = false; float Bd = MaxDistance;
	// (a table of the room she is in, never one behind a wall: a table in a room is used from that room only (884 tables14's first
	// picture: the healer's table answered F from the street outside its wall, the open ground being no room))
	const int32 Room = S->RoomAt(From);
	for (const FVector& T : Station == TEXT("Alchemist") ? S->AlchemistPoints : S->LibrarianPoints)
	{
		const float D = FVector::Dist2D(T, From);
		const int32 Tr = S->RoomAt(T);
		if (D < Bd && FMath::Abs(T.Z - From.Z) < 250.f && (Tr < 0 ? Room < 0 : Tr == Room)) { Bd = D; At = T; bFound = true; }
	}
	return bFound;
}

FName ARDDungeonGenerator::NearestTable14(const FVector& From, float MaxDistance, float Than) const
{
	FVector A, L;
	const bool bA = FindNearestTable14(TEXT("Alchemist"), From, MaxDistance, A), bL = FindNearestTable14(TEXT("Librarian"), From, MaxDistance, L);
	const float Da = bA ? FVector::Dist2D(A, From) : 1e9f, Dl = bL ? FVector::Dist2D(L, From) : 1e9f;
	if (FMath::Min(Da, Dl) >= Than) return NAME_None;
	return Da <= Dl ? FName(TEXT("Alchemist")) : FName(TEXT("Librarian"));
}

TArray<FVector> ARDDungeonGenerator::GetAllTables14(FName Station) const
{
	TArray<FVector> Out;
	for (const TPair<FIntPoint, TObjectPtr<ARDSection>>& Kv : Sections)
		if (const ARDSection* S = Kv.Value; IsValid(S)) Out.Append(Station == TEXT("Alchemist") ? S->AlchemistPoints : S->LibrarianPoints);
	return Out;
}

TArray<FName> ARDDungeonGenerator::GetStationRecipes14(FName Station) const
{
	TArray<FName> Out;
	for (const FRDRecipe& Rc : Recipes) if (RecipeStation(Rc) == Station && RecipeRefusal(Rc).IsEmpty()) Out.Add(Rc.Item);
	return Out;
}

void ARDSection::EnsureTables14()
{
	// (a dungeon set's anvil room gets the alchemist's table (and on a map with no town the librarian's), each on a free tile off
	// the lanes whose four neighbours are free, the nearest such to the anvil, as the forge's (EnsureForge): no random stream is
	// drawn, so the rooms and their furniture stay; its tile is blocked, so in that one room a monster, trap or special thing placed
	// after it may stand on another tile than before (PR #81's review). A town's are its buildings' (TownTables14))
	if (!Generator || !Generator->bTables14 || TownBlds.Num() > 0 || AnvilRoom < 0 || !Rooms.IsValidIndex(AnvilRoom) || AnvilPoints.Num() == 0) return;
	const int32 RI = AnvilRoom;
	const FVector An = AnvilPoints.Last();
	// (the placement is ARDSection::PlaceNearAnchor15's, shared with the great hall's oven (RDList15c.cpp): the same rule as before)
	auto Put = [&](FName Piece, TArray<FVector>& Points)
	{
		if (Points.ContainsByPredicate([this, RI](const FVector& F) { return RoomAt(F) == RI; })) return;
		PlaceNearAnchor15(Piece, RI, An, Points);
	};
	Put(Generator->AlchemistPiece, AlchemistPoints);
	if (Generator->bLibrarianInDungeon14) Put(Generator->LibrarianPiece, LibrarianPoints);
}

void ARDSection::TownTables14(int32 BI)
{
	// (a town building's table, after its furnishing and its trade's pieces, among their footprints (FurnRoom: a piece that would
	// stand in another is refused): against a side wall or the back wall, its front toward the room, the first place free of a few.
	// The alchemist's in a healer's house, a laboratory and a witch's hut; the librarian's in a temple, a library and a study. None
	// in a burnt or boarded one)
	if (!Generator || !Generator->bTables14 || !TownBlds.IsValidIndex(BI)) return;
	const FTownBld& B = TownBlds[BI];
	if (B.State != 0 || B.Rooms.Num() == 0) return;
	FName Want;
	switch (B.Kind)
	{
	case TK_Healer: case TK_Laboratory: case TK_Witch: Want = Generator->AlchemistPiece; break;
	case TK_Temple: case TK_Library: case TK_Study: Want = Generator->LibrarianPiece; break;
	default: return;
	}
	const FRDPiece* P = Pc(Want);
	if (!P) return;
	FurnRoom = B.Rooms[0];
	ON_SCOPE_EXIT { FurnRoom = -1; };
	const float M = Generator->TileSize;
	const int32 Nx = B.DoorSide < 2 ? B.Max.X - B.Min.X : B.Max.Y - B.Min.Y;
	const int32 Ny = B.DoorSide < 2 ? B.Max.Y - B.Min.Y : B.Max.X - B.Min.X;
	const float Hx = Nx * M * 0.5f, Hy = Ny * M * 0.5f;
	const float Yaw0 = TownBldYaw(B);          // (the building's +X: its door's way out)
	const float Off = (float)P->Size.X * 0.5f + 55.f;
	struct FTry { float X, Y, Yaw; };
	TArray<FTry> Tries;
	for (const float Xf : { -0.3f, 0.1f, -0.6f, 0.35f })
		for (const float Sd : { 1.f, -1.f })
			Tries.Add({ Hx * Xf, Sd * (Hy - Off), Yaw0 + (Sd > 0.f ? -90.f : 90.f) });
	for (const float Yf : { 0.45f, -0.45f, 0.25f, -0.25f }) Tries.Add({ -Hx + Off, Hy * Yf, Yaw0 });
	for (const FTry& T : Tries)
	{
		const FVector At = TownBldPoint(B, T.X, T.Y, 0.f);
		if (RoomAt(At) != B.Rooms[0]) continue;
		// (its footprint against the room's own, whether the town tidies its furniture or not (PR #81's review: AddPiece checks
		// them only under bTidyFurniture), and added to them when AddPiece does not)
		FVector Fc; FVector2D Sz; float Front;
		FootOf(P, FTransform(FRotator(0.f, T.Yaw, 0.f), At), Fc, Sz, Front);
		if (!FootFree(Fc, T.Yaw, Sz, false)) continue;
		if (!AddPieceAt(Want, At, T.Yaw)) continue;
		if (!Generator->bTidyFurniture) AddFoot(Fc, T.Yaw, Sz, false, Want);
		MarkBlocked(At, T.Yaw, FVector2D((float)P->Size.X + 40.f, (float)P->Size.Y + 40.f), true);
		return;
	}
	UE_LOG(LogRDTables14, Warning, TEXT("RDTABLES14 no room for the %s in building %d"), *Want.ToString(), BI);
}
