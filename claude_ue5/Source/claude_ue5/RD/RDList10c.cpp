// The user's list of 2026-11-10 (docs/improvements10.txt), its third phase's rules that are the generator's:
//   - "the fighter and only the fighter should be able to craft basic weapons and armor she has already looted at a forge - a forge
//     is a new crafting station": the forges (ForgePieces where they stand: the dungeons' forge rooms; the town smithy's forge; one
//     put by the anvil of a set that has none) open the crafting panel on the Station "Forge" recipes (914 forge: every weapon,
//     shield and set of armour of the game's tier 1, its cost what breaking it down gives and half again); only ForgeHeroes work
//     it, and a recipe is offered only for what she has looted (the game instance's LootedItems, kept in the save);
//   - "everyone should be able to craft food items from food components at an oven": the dungeons' kitchens' bread ovens open the
//     oven's recipes as the town's do (bDungeonOvens);
//   - the ankh ("new type of item that can be held in the left hand and put in the quick slot: revealing light, looks like an
//     ankh, found on Tier 2 monsters or in containers"; the user's choice: it lights the way and within about 10 m shows the traps,
//     what hides and the hidden caches): held as the torch is (RDGear.cpp), its pale light; while it is raised the traps within
//     AnkhRevealRange are seen and outlined for every hero, and the chests and trunks not looted are marked on the map; a monster
//     of the game's tier 2 may drop one. Nothing in the game hides from her yet (no monster is stealthed or invisible) and there
//     are no hidden caches but the containers themselves.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "RD/RDCombat.h"
#include "RD/RDMonster.h"
#include "RD/RDMistward.h"
#include "RD/RDGameInstance.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDList10c, Log, All);

// ================================================================================================ what she has looted
bool ARDDungeonGenerator::HasLooted(FName Item) const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	return GI && GI->LootedItems.Contains(Item);
}

void ARDDungeonGenerator::NoteLooted(FName Item)
{
	if (URDGameInstance* GI = URDGameInstance::Of(this); GI && !GI->LootedItems.Contains(Item))
	{
		GI->LootedItems.Add(Item);
		UE_LOG(LogRDList10c, Log, TEXT("RDFORGE looted %s (%d so far)"), *Item.ToString(), GI->LootedItems.Num());
	}
}

TArray<FName> ARDDungeonGenerator::GetLootedItems() const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	return GI ? GI->LootedItems : TArray<FName>();
}

// ================================================================================================ the forge and the dungeons' ovens
FString ARDDungeonGenerator::ForgeRefusal() const
{
	if (ForgeHeroes.Num() == 0 || ForgeHeroes.Contains(CurrentHero)) return FString();
	// (who works it, by the heroes' titles in words, as the potions' refusal says it)
	TArray<FString> Who;
	for (const FName& Hb : ForgeHeroes)
	{
		const FRDHeroDef* H = Heroes.FindByPredicate([&Hb](const FRDHeroDef& D) { return D.Name == Hb; });
		FString Ti = H && !H->Title.IsEmpty() ? H->Title : Hb.ToString();
		if (Ti == Ti.ToUpper()) { Ti = Ti.ToLower(); for (int32 C = 0; C < Ti.Len(); ++C) if (C == 0 || Ti[C - 1] == TEXT(' ')) Ti[C] = FChar::ToUpper(Ti[C]); }
		Who.Add(TEXT("the ") + Ti);
	}
	return FString::Printf(TEXT("Only %s works the forge"), *FString::Join(Who, TEXT(" and ")));
}

bool ARDDungeonGenerator::FindNearestForge(const FVector& From, float MaxDistance, FVector& At) const
{
	bool bFound = false; float Bd = MaxDistance;
	const ARDSection* S = GetSection(WorldToSection(From));
	if (!S) return false;
	// (a forge of the room she is in, as an anvil: not one behind a wall)
	const int32 Room = S->RoomAt(From);
	for (const FVector& F : S->ForgePoints)
	{
		const float D = FVector::Dist2D(F, From);
		if (D < Bd && FMath::Abs(F.Z - From.Z) < 250.f && (Room < 0 || S->RoomAt(F) == Room)) { Bd = D; At = F; bFound = true; }
	}
	// (the town: the smithy's forge)
	if (bTown)
		for (const ARDSection::FTownSpot& Sp : S->TownSpots)
			if (Sp.Kind == TS_Forge) { const float D = FVector::Dist2D(Sp.At, From); if (D < Bd && FMath::Abs(Sp.At.Z - From.Z) < 250.f) { Bd = D; At = Sp.At; bFound = true; } }
	return bFound;
}

TArray<FVector> ARDDungeonGenerator::GetAllForges() const
{
	TArray<FVector> Out;
	for (const TPair<FIntPoint, TObjectPtr<ARDSection>>& Kv : Sections)
		if (const ARDSection* S = Kv.Value; IsValid(S))
		{
			Out.Append(S->ForgePoints);
			if (bTown) for (const ARDSection::FTownSpot& Sp : S->TownSpots) if (Sp.Kind == TS_Forge) Out.Add(Sp.At);
		}
	return Out;
}

bool ARDDungeonGenerator::FindNearestOven(const FVector& From, float MaxDistance, FVector& At) const
{
	bool bFound = false; float Bd = MaxDistance;
	const ARDSection* S = GetSection(WorldToSection(From));
	if (!S) return false;
	const int32 Room = S->RoomAt(From);
	for (const FVector& O : S->TownOvens)
	{
		const float D = FVector::Dist2D(O, From);
		if (D < Bd && FMath::Abs(O.Z - From.Z) < 250.f && (Room < 0 || S->RoomAt(O) == Room)) { Bd = D; At = O; bFound = true; }
	}
	return bFound;
}

TArray<FVector> ARDDungeonGenerator::GetAllOvens() const
{
	TArray<FVector> Out;
	for (const TPair<FIntPoint, TObjectPtr<ARDSection>>& Kv : Sections) if (const ARDSection* S = Kv.Value; IsValid(S)) Out.Append(S->TownOvens);
	return Out;
}

FString ARDDungeonGenerator::StationDescribe(const FVector& From, float DoorD) const
{
	if (Recipes.Num() == 0) return FString();
	const float Lim = FMath::Min(DoorD, AnvilReach);
	FVector An, At; const float Ad = FindNearestAnvil(From, Lim, An) ? FVector::Dist2D(An, From) : 1e9f;
	if (bForge && FindNearestForge(From, Lim, At) && FVector::Dist2D(At, From) < Ad) return ForgeRefusal().IsEmpty() ? FString(TEXT("use the forge")) : FString(TEXT("the forge (the Warrior's)"));
	// (the town's ovens are the town's things: TownThingDescribe)
	if (bDungeonOvens && !bTown && FindNearestOven(From, Lim, At) && FVector::Dist2D(At, From) < Ad) return TEXT("bake at the oven");
	return FString();
}

FString ARDDungeonGenerator::StationInteract(const FVector& From, float DoorD)
{
	if (!PlayerCombat || Recipes.Num() == 0) return FString();
	const float Lim = FMath::Min(DoorD, AnvilReach);
	FVector An, At; const float Ad = FindNearestAnvil(From, Lim, An) ? FVector::Dist2D(An, From) : 1e9f;
	if (bForge && FindNearestForge(From, Lim, At) && FVector::Dist2D(At, From) < Ad)
	{
		if (const FString Fr = ForgeRefusal(); !Fr.IsEmpty()) { PlayerCombat->ShowMessage(Fr); return TEXT("forge refused"); }
		PlayerCombat->SetCraftStation(TEXT("Forge"));
		PlayerCombat->SetCraftingOpen(true);
		return TEXT("forge");
	}
	if (bDungeonOvens && !bTown && FindNearestOven(From, Lim, At) && FVector::Dist2D(At, From) < Ad)
	{
		PlayerCombat->SetCraftStation(TEXT("Oven"));
		PlayerCombat->SetCraftingOpen(true);
		return TEXT("oven");
	}
	return FString();
}

void ARDSection::EnsureForge()
{
	// (an anvil's room with no forge gets one, on a free tile off the lanes whose four neighbours are free, the nearest such to the
	// anvil; no random stream is drawn. By the room, not the set: the start set has forge rooms, and the great hall none (868
	// list10c: the nearest forge 77 m from it))
	if (!Generator || !Generator->bForge || AnvilRoom < 0 || !Rooms.IsValidIndex(AnvilRoom) || AnvilPoints.Num() == 0) return;
	if (ForgePoints.ContainsByPredicate([this](const FVector& F) { return RoomAt(F) == AnvilRoom; })) return;
	const FRDPiece* P = Pc(Generator->ForgeStationPiece);
	if (!P) return;
	const FRoom& Rm = Rooms[AnvilRoom];
	const int32 RI = AnvilRoom;
	auto Free = [&](FIntPoint T) { return In(T) && Type[Idx(T)] == 1 && !Blocked[Idx(T)] && RoomAtLocal(T) == RI; };
	const FVector An = AnvilPoints.Last();
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
	if (Pick.X < 0) return;
	const FVector At = TileWorld(Pick);
	const float Yaw = FMath::Abs(Pick.X - Rm.Lane.X) > FMath::Abs(Pick.Y - Rm.Lane.Y) ? 90.f : 0.f;
	AddPieceAt(Generator->ForgeStationPiece, At, Yaw);
	if (P->bCollision) MarkBlocked(At, Yaw, FVector2D(P->Size.X, P->Size.Y));
	// (AddPiece records it when the piece is one of ForgePieces; put by name here, it is a forge whatever the list says)
	if (!ForgePoints.ContainsByPredicate([&At](const FVector& F) { return FVector::Dist2D(F, At) < 10.f; })) ForgePoints.Add(At);
}

// ================================================================================================ the ankh
bool URDCombatComponent::IsAnkhHeld() const
{
	if (!bTorchHeld || TorchItem.IsNone() || !Generator) return false;
	const int32 Ix = Generator->FindItem(TorchItem);
	return Ix >= 0 && Generator->Items[Ix].Kind == ERDItemKind::Light && GetItemCount(TorchItem) > 0;
}

FName ARDDungeonGenerator::GetAnkhItem() const
{
	for (const FRDItemDef& It : Items) if (It.Kind == ERDItemKind::Light) return It.Name;
	return NAME_None;
}

void ARDDungeonGenerator::TickAnkh(float Dt)
{
	AnkhClock += Dt;
	if (AnkhClock < AnkhNext || !PlayerCombat || !PlayerCombat->IsAnkhHeld()) return;
	AnkhNext = AnkhClock + 0.25f;
	const APawn* Her = Cast<APawn>(PlayerCombat->GetOwner());
	if (!Her) return;
	const FVector L = Her->GetActorLocation();
	const FIntPoint Here = WorldToSection(L);
	for (int32 Dx = -1; Dx <= 1; ++Dx)
		for (int32 Dy = -1; Dy <= 1; ++Dy)
		{
			ARDSection* S = GetSection(Here + FIntPoint(Dx, Dy));
			if (!S) continue;
			// (the traps within its reach: seen and outlined, as the Rogue sees them; read by index, OutlineTrap may add to the list)
			for (int32 I = 0; I < S->TrapList.Num(); ++I)
			{
				if (S->TrapList[I].bSeen || S->TrapList[I].State != 0) continue;
				const FVector At = S->TrapList[I].At;
				if (FVector::Dist2D(At, L) > AnkhRevealRange || FMath::Abs(At.Z - L.Z) > 300.f) continue;
				S->TrapList[I].bSeen = true; ++AnkhTrapsShown;
				const int32 Def = S->TrapList[I].Def;
				if (bTrapOutline) S->OutlineTrap(I);
				PlayerCombat->ShowMessage(FString::Printf(TEXT("The ankh's light shows a trap: %s%s"), Traps.IsValidIndex(Def) ? *Traps[Def].Label : TEXT("a trap"), HeroFindsTraps() ? TEXT(" (F to disarm)") : TEXT(" (go round it)")));
			}
			// (the chests and trunks not looted within its reach: marked on the map, seen or not)
			for (int32 I = 0; I < S->GetNumContainers(); ++I)
			{
				const FString Kd = S->GetContainerKind(I);
				if (S->IsContainerLooted(I) || (Kd != TEXT("chest") && Kd != TEXT("trunk"))) continue;
				const FVector At = S->GetContainerLocation(I);
				if (FVector::Dist2D(At, L) > AnkhRevealRange || FMath::Abs(At.Z - L.Z) > 300.f) continue;
				bool bNew = false; AnkhRevealed.Add(FIntVector(S->Coord.X, S->Coord.Y, S->ContainerKey(I)), &bNew);
				if (bNew) ++AnkhCachesShown;
			}
		}
}

void ARDDungeonGenerator::AnkhDropFor(ARDMonster* Monster)
{
	const FName Ankh = GetAnkhItem();
	if (Ankh.IsNone() || !Monster || !PlayerCombat || Monster->IsAlly() || AnkhDropChance <= 0.f) return;
	// (of the game's tier 2: the castle's tier 2, or a dungeon whose second band is tier 2)
	if (GlobalTier(TierOf(WorldToSection(Monster->GetActorLocation()))) != 2) return;
	if (PlayerCombat->GetItemCount(Ankh) > 0) return;
	// (a draw of its own: the play's streams are not touched)
	const FVector At = Monster->GetActorLocation();
	const uint32 H = HashCombine(HashCombine((uint32)SessionSeed ^ 0xA2C4u, GetTypeHash(FIntPoint(FMath::FloorToInt(At.X / 50.f), FMath::FloorToInt(At.Y / 50.f)))), GetTypeHash(Monster->SpawnIndex));
	if ((float)(H % 100000u) / 100000.f >= AnkhDropChance) return;
	TArray<float> W; W.Init(-1.f, 1);
	if (ARDLootPile* P = DropLoot(At, { Ankh }, W)) { P->bHers = false; ++AnkhDrops; UE_LOG(LogRDList10c, Log, TEXT("RDANKH dropped by %s at (%.0f, %.0f)"), *Monster->MonsterName.ToString(), At.X, At.Y); }
}
