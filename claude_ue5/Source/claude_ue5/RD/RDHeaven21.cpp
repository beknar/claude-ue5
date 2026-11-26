// The user's list of 2026-11-22 (docs/improvements16.txt, "the city of heaven"; the plan docs/improvements16_plan.md), its twenty-first
// phase, Heaven's shops, services and containers:
// - "the insides of shops in Heaven should look like typical shops with rows and shelves full of food and other things that can be
//   purchased from the sales person manning that shop": each shop (and the market, the trader's store) rows of gondola shelves full of
//   goods, a checkout by its door with its clerk behind it; the clerk sells the shop's own stock (a grocery's food, a pharmacy's
//   potions, a hardware store's repair kits and torches; the market all of it);
// - the modern services: the market (the trader), the clinic (the healer), the gear shop (the smith), the bank (the storehouse) and the
//   hotel (the inn: a room for the night until seven, waking whole), their words and their pieces;
// - "the containers in heaven should be modern ones": a fridge, a filing cabinet, a tool chest, a bin, a safe and a locker for the
//   medieval barrels, crates, chests and wardrobes, and the yards' dumpsters, each a body and a moving part (a door or a lid) of
//   Heaven's kit (946 shops), with its own word.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "RD/RDCombat.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDHeaven21, Log, All);

static const FIntPoint RDH21Dir4[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };

// ------------------------------------------------------------------------------------------------ a shop's kind and side
int32 ARDSection::ShopKind21(int32 BI) const
{
	// (0 a grocery, 1 a pharmacy, 2 a hardware store; the market (the trader's store) -1: everything)
	if (!TownBlds.IsValidIndex(BI)) return -1;
	const FTownBld& B = TownBlds[BI];
	// (the list of 2026-11-26: nine kinds, in the order the shops stand, so each is there among the twelve)
	extern bool RDShops17On();
	if (B.Kind == TK_Shop && RDShops17On()) return ShopOrder17(BI) % 9;
	return B.Kind == TK_Shop ? (int32)((B.Seed >> 3) % 3u) : -1;
}

FString ARDSection::ShopWord21(int32 BI) const
{
	return ARDDungeonGenerator::ShopWord17(ShopKind21(BI));          // (the list of 2026-11-26: nine kinds' words)
}

float ARDSection::ShopSide21(int32 BI) const
{
	// (the clerk and the checkout on the side of the door with more room across the building)
	const FTownBld& B = TownBlds[BI];
	const FIntPoint In(-RDH21Dir4[B.DoorSide].X, -RDH21Dir4[B.DoorSide].Y);
	const FIntPoint Ac(In.Y, -In.X);
	const FIntRect Rc(B.Min, B.Max);
	int32 Room[2] = { 0, 0 };
	for (int32 S = 0; S < 2; ++S)
		for (FIntPoint T = B.DoorTile + Ac * (S == 0 ? 1 : -1); Rc.Contains(T); T += Ac * (S == 0 ? 1 : -1)) ++Room[S];
	return Room[0] >= Room[1] ? 1.f : -1.f;
}

// ------------------------------------------------------------------------------------------------ a shop's floor: checkout and rows of shelves
FTransform ARDSection::ShopFurnish21(int32 BI)
{
	const FTownBld& B = TownBlds[BI];
	const float M = Generator->TileSize;
	FurnRoom = B.Rooms.Num() > 0 ? B.Rooms[0] : -1; Feet.Reset();
	ON_SCOPE_EXIT { FurnRoom = -1; };
	const FVector In_ = -FVector(RDH21Dir4[B.DoorSide].X, RDH21Dir4[B.DoorSide].Y, 0.f);
	const FVector Across(In_.Y, -In_.X, 0.f);
	const float Side = ShopSide21(BI);
	const FVector DoorWall = TileWorld(B.DoorTile) - In_ * (M * 0.5f);
	const FVector Inside = TileWorld(B.DoorTile) + In_ * 260.f;
	const int32 Kind = ShopKind21(BI);
	// ---- the checkout: its long side along the way in, the clerk's side toward the clerk (230 cm aside from the door's line)
	const FVector Ck = Inside + Across * (Side * 130.f);
	const float CkYaw = In_.Rotation().Yaw + (Side > 0.f ? 180.f : 0.f);
	AddPiece(TEXT("Heaven.Checkout21"), FTransform(FRotator(0, CkYaw, 0), Ck));
	MarkBlocked(Ck, CkYaw, FVector2D(180.f, 70.f));
	// ---- the rows: gondolas along the building's width, 6.45 m in from the door's wall and every 2.7 m, aisles of 1.5 m at the walls
	FVector2D Lo(1e9, 1e9), Hi(-1e9, -1e9);
	const FVector C0 = TileWorld(B.Min) - FVector(M * 0.5f, M * 0.5f, 0.f), C1 = TileWorld(B.Max - FIntPoint(1, 1)) + FVector(M * 0.5f, M * 0.5f, 0.f);
	for (const FVector& Cc : { FVector(C0.X, C0.Y, 0.f), FVector(C1.X, C0.Y, 0.f), FVector(C0.X, C1.Y, 0.f), FVector(C1.X, C1.Y, 0.f) })
	{
		const float A = FVector::DotProduct(Cc, Across), D = FVector::DotProduct(Cc - DoorWall, In_);
		Lo = FVector2D(FMath::Min(Lo.X, A), FMath::Min(Lo.Y, D)); Hi = FVector2D(FMath::Max(Hi.X, A), FMath::Max(Hi.Y, D));
	}
	const float Depth = Hi.Y;
	const float GyYaw = (-In_).Rotation().Yaw;
	int32 Gondolas = 0, Row = 0;
	for (float D = 645.f; D + 45.f <= Depth - 120.f; D += 270.f, ++Row)
	{
		const FVector Base = DoorWall + In_ * D - Across * FVector::DotProduct(DoorWall, Across);
		const float A0 = Lo.X + 150.f + 60.f, A1 = Hi.X - 150.f - 60.f;
		const int32 Slots = FMath::Max(0, FMath::FloorToInt((A1 - A0) / 125.f) + 1);
		for (int32 K = 0; K < Slots; ++K)
		{
			if (Slots >= 5 && K == Slots / 2) continue;          // (a cross aisle half way along a long row)
			const float A = A0 + K * 125.f + ((A1 - A0) - (Slots - 1) * 125.f) * 0.5f;
			const int32 Gk = Kind >= 0 ? GondolaOf17(Kind) : (Row + K) % 3;
			const FVector Gp = Base + Across * A;
			if (AddPiece(FName(*FString::Printf(TEXT("Heaven.Gondola21_%d"), Gk)), FTransform(FRotator(0, GyYaw, 0), Gp)))
			{
				++Gondolas;
				MarkBlocked(Gp, GyYaw, FVector2D(90.f, 120.f));          // (tile paths keep off the shelves (PR #128's review))
			}
		}
	}
	// ---- its ceiling's light panels, every other tile under its roof (the market's hall is two storeys high: under its roof, not half way
	// up (PR #128's review)), and its lights: the room's own were laid by the furnishing not laid here; one a 5 m square, steady, no shadow
	const float Ceil = 2.f + 300.f * FMath::Max(1, B.Storeys) - 6.f;
	for (int32 X = B.Min.X; X < B.Max.X; ++X)
		for (int32 Y = B.Min.Y; Y < B.Max.Y; ++Y)
		{
			if ((X + Y) % 2 == 0) AddPiece(TEXT("Heaven.CeilingPanel20"), FTransform(FRotator(0, GyYaw, 0), TileWorld(FIntPoint(X, Y), Ceil)), true);
			if ((X - B.Min.X) % 2 == 1 && (Y - B.Min.Y) % 2 == 1) AddLight(TileWorld(FIntPoint(X, Y), FMath::Min(Ceil - 40.f, 260.f)), FLinearColor(0.96f, 0.97f, 1.f), 70.f, 700.f, false, 0.f);
		}
	Shops21.Add(FString::Printf(TEXT("shop|%d|%d|%d|%.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%.0f"), BI, Kind, Gondolas, Ck.X, Ck.Y, C0.X, C0.Y, C1.X, C1.Y,
		(Inside + Across * (Side * 230.f)).X, (Inside + Across * (Side * 230.f)).Y, (Ck - Across * (Side * 140.f)).X, (Ck - Across * (Side * 140.f)).Y));
	Shops21.Last() += FString::Printf(TEXT("|%.0f|%.0f|%.3f|%.3f|%.1f"), DoorWall.X, DoorWall.Y, In_.X, In_.Y, GyYaw);
	return FTransform(FRotator(0, CkYaw, 0), Ck);
}

TArray<FString> ARDSection::GetShops21() const { return Shops21; }

// ------------------------------------------------------------------------------------------------ containers' words and states
FString ARDSection::GetContainerWord(int32 I) const
{
	if (!Containers.IsValidIndex(I)) return FString();
	return Containers[I].Word.IsEmpty() ? Containers[I].Kind : Containers[I].Word;
}

TArray<FString> ARDSection::GetContainerLines21() const
{
	// (for the tests: "c|<i>|<kind>|<word>|<x>|<y>|<z>|<yaw>|<target>|<alpha>|<the moving part's turn from shut, degrees>|<body mesh>")
	TArray<FString> Out;
	for (int32 I = 0; I < Containers.Num(); ++I)
	{
		const FMover& Mv = Containers[I];
		const USceneComponent* Base = Mv.Pivot ? Mv.Pivot->GetAttachParent() : nullptr;
		if (!Base) continue;
		const float Ang = FMath::RadiansToDegrees(Mv.Pivot->GetRelativeRotation().Quaternion().AngularDistance(Mv.Closed));
		FString Body = TEXT("-");
		for (USceneComponent* Ch : Base->GetAttachChildren()) if (const UStaticMeshComponent* Sm = Cast<UStaticMeshComponent>(Ch); Sm && Sm->GetStaticMesh()) { Body = Sm->GetStaticMesh()->GetName(); break; }
		const FVector L = Base->GetComponentLocation();
		const FVector Pm = Mv.Parts.Num() > 0 && Mv.Parts[0] ? Mv.Parts[0]->Bounds.Origin : FVector::ZeroVector;
		Out.Add(FString::Printf(TEXT("c|%d|%s|%s|%.0f|%.0f|%.0f|%.0f|%.2f|%.2f|%.1f|%s|%.1f|%.1f|%.1f"), I, *Mv.Kind, *GetContainerWord(I), L.X, L.Y, L.Z, Base->GetComponentRotation().Yaw, Mv.Target, Mv.Alpha, Ang, *Body, Pm.X, Pm.Y, Pm.Z));
	}
	return Out;
}

// ------------------------------------------------------------------------------------------------ the services at play
int32 ARDDungeonGenerator::ShopKindOfWho21() const
{
	// (the kind of the shop whose clerk opened the store: -1 the market or any other town's trader, everything)
	// (the building the store was opened at: its checkout's spot or its clerk (the first test: F reached the checkout, not the clerk
	// behind it))
	if (!InHeaven21()) return -1;
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	return S ? S->ShopKind21(StoreBld21) : -1;
}

bool ARDDungeonGenerator::InHeaven21() const
{
	// (Heaven's town stands round her now: its section there under its theme (TownPlan stays 5 after it is unloaded: PR #128's review,
	// the wilds' trader was "The market" after Heaven))
	const ARDSection* S = TownPlan == 5 ? GetSection(FIntPoint::ZeroValue) : nullptr;
	return S && S->Theme == FName(TEXT("Heaven"));
}

bool ARDDungeonGenerator::ShopSells21(int32 Kind, FName Item) const
{
	if (Kind < 0) return true;
	const int32 Ix = FindItem(Item);
	if (Ix < 0) return false;
	// (the list of 2026-11-26: a kind sells its trades' things (the grocery's food, the pharmacy's potions...); rd.Shops17 0 as before)
	extern bool RDShops17On();
	if (!RDShops17On())
	{
		const ERDItemKind K = Items[Ix].Kind;
		switch (Kind)
		{
		case 0: return K == ERDItemKind::Food;
		case 1: return K == ERDItemKind::Healing || K == ERDItemKind::Mana || K == ERDItemKind::Speed;
		case 2: return K == ERDItemKind::Repair || K == ERDItemKind::Torch;
		default: return true;
		}
	}
	for (const int32 T : StoreTrades17(-1, Kind)) if (StallSells17(T, Items[Ix])) return true;
	return false;
}

bool ARDDungeonGenerator::HotelRent21()
{
	// (a room for the night: she sleeps until seven and wakes whole, her afflictions gone)
	if (!PlayerCombat) return false;
	const int32 Cost = HotelPrice21();
	if (GetGold() < Cost) { SetTownNote(TEXT("You have too little gold")); return false; }
	AddGold(-Cost, TEXT("the hotel"));
	PlayerCombat->SetHealth(PlayerCombat->GetMaxHealth()); PlayerCombat->SetMana(PlayerCombat->GetMaxMana());
	PlayerCombat->ClearAfflictions();
	// (to the next morning: a day on when it is seven or later (PR #128's review: the clock went back 15 hours to the same day's
	// seven), and saved as the camp's rest is)
	const int32 Day0 = TownDay;
	if (bDayNight) { if (TownHour >= 7.f) ++TownDay; SetTownHour(7.f); }
	TownCount(TEXT("hotel"));
	SetTownNote(bDayNight ? FString::Printf(TEXT("You sleep in a quiet room until seven: day %d (%d gold)"), TownDay, Cost) : FString::Printf(TEXT("You rest in a quiet room (%d gold)"), Cost));
	if (bWild) WildAutosave(TEXT("found"));
	UE_LOG(LogRDHeaven21, Log, TEXT("RDHEAVEN21 a night at the hotel: %d gold, day %d -> %d, hour %.1f"), Cost, Day0, TownDay, TownHour);
	return true;
}
