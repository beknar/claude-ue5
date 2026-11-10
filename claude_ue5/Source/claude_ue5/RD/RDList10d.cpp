// The user's list of 2026-11-10 (docs/improvements10.txt), its fourth phase, the towns' life:
//   - "if an NPC is supposed to be sleeping at night, have them sleep in their beds with a new animation or clip in blender":
//     every sleeper (a resident, a home's child, a keeper, a soldier: whoever has a building) is given a bed of its building, the
//     town's beds where they stand (ARDSection::TownBeds, recorded as the furniture is laid) and, where a building has fewer than
//     its sleepers, one put on a free tile of its rooms (no random draw, so nothing else moves); asleep it lies in it on its def's
//     work clip "Sleep" (blender_numpy/town_work_clips.py's make_sleep; RDTownGame.cpp's tick);
//   - "there should be more children in town, and they are supposed to be asleep at night" and "the town should be 25% more
//     populated with more children as the population increases. leave the number of buildings the same": a lived-in home with
//     a resident has a second grown-up one time in HomeSecondShare and a child one time in HomeChildShare, each from a draw of its
//     own (the home's seed): the children live at home, in at evening and asleep at night; the square's three are left out when
//     homes have children.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDList10d, Log, All);

namespace
{
	const FIntPoint RDHouseDir4[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };
}

void ARDSection::PlanHouseholds()
{
	if (!Generator || !Generator->bMorePeople) return;
	TArray<FTownPost> More;
	for (int32 BI = 0; BI < TownBlds.Num(); ++BI)
	{
		const FTownBld& B = TownBlds[BI];
		if (B.Kind != TK_Home || B.State != 0) continue;
		if (!TownPosts.ContainsByPredicate([BI](const FTownPost& P) { return P.Bld == BI && P.Role == ERDTownRole::Townsfolk; })) continue;
		const FVector In_ = -FVector(RDHouseDir4[B.DoorSide].X, RDHouseDir4[B.DoorSide].Y, 0.f);
		const FVector Rt(In_.Y, -In_.X, 0.f);
		const FVector Door = TileWorld(B.DoorTile);
		// (a draw of the home's own: the plan's streams are not touched)
		FRandomStream Rh((int32)(B.Seed ^ 0x5E2Du));
		if (Rh.FRand() < Generator->HomeSecondShare)
		{
			// (the other side of the door from the first)
			FTownPost P_; P_.Role = ERDTownRole::Townsfolk; P_.At = Door - In_ * 260.f - Rt * 230.f; P_.Bld = BI; P_.Wander = 350.f; P_.Index = 2000 + BI; P_.Yaw = (-In_).Rotation().Yaw;
			More.Add(P_); ++TownAdults2;
		}
		if (Rh.FRand() < Generator->HomeChildShare)
		{
			FTownPost P_; P_.Role = ERDTownRole::Child; P_.At = Door - In_ * 430.f + Rt * 90.f; P_.Bld = BI; P_.Wander = 1500.f; P_.Index = 3000 + BI; P_.Yaw = (-In_).Rotation().Yaw;
			More.Add(P_); ++TownHomeKids;
		}
	}
	// (the square's children, who never went home: the homes have their own now)
	if (TownHomeKids > 0) TownSquareKidsDropped = TownPosts.RemoveAll([](const FTownPost& P) { return P.Role == ERDTownRole::Child && P.Bld < 0; });
	TownPosts.Append(More);
	UE_LOG(LogRDList10d, Log, TEXT("RDHOUSEHOLDS %d second grown-ups, %d children at home (%d of the square's left out): %d posts"), TownAdults2, TownHomeKids, TownSquareKidsDropped, TownPosts.Num());
}

int32 ARDSection::AddTownBed(int32 Bld)
{
	const FRDPiece* P = Pc(TEXT("Bed"));
	if (!P || !P->Mesh || !TownBlds.IsValidIndex(Bld)) return -1;
	const FTownBld& B = TownBlds[Bld];
	const float S = Generator->TileSize;
	// (a free tile of the building's rooms, not the door's nor beside it, nor by a bed: the one nearest a wall, then farthest from
	// the door; the bed's head against that wall)
	FIntPoint Pick(-1, -1); float PickScore = MAX_flt; int32 PickSide = 0;
	for (int32 X = B.Min.X; X < B.Max.X; ++X)
		for (int32 Y = B.Min.Y; Y < B.Max.Y; ++Y)
		{
			const FIntPoint T(X, Y);
			if (!In(T) || Type[Idx(T)] != 1 || Blocked[Idx(T)] || !B.Rooms.Contains(RoomAtLocal(T))) continue;
			if (FMath::Max(FMath::Abs(X - B.DoorTile.X), FMath::Abs(Y - B.DoorTile.Y)) <= 1) continue;
			const FVector W = TileWorld(T);
			if (TownBeds.ContainsByPredicate([&](const FTownBed& Bd) { return FVector::Dist2D(Bd.At, W) < 200.f; })) continue;
			const int32 E[4] = { X - B.Min.X, B.Max.X - 1 - X, Y - B.Min.Y, B.Max.Y - 1 - Y };
			int32 Side = 0; for (int32 K = 1; K < 4; ++K) if (E[K] < E[Side]) Side = K;
			const float Score = E[Side] * 1000.f - FVector::Dist2D(W, TileWorld(B.DoorTile));
			if (Score < PickScore) { PickScore = Score; Pick = T; PickSide = Side; }
		}
	if (Pick.X < 0) return -1;
	// (its foot into the room: away from the wall it lies against; its middle moved toward that wall, its head against it)
	static const float RDBedYaw[4] = { 0.f, 180.f, 90.f, -90.f };
	const float Yaw = RDBedYaw[PickSide];
	const FVector Fwd = FRotator(0.f, Yaw, 0.f).Vector();
	const FVector At = TileWorld(Pick) - Fwd * FMath::Max(0.f, (S - P->Size.X) * 0.5f - 15.f);
	const FTransform World = P->Adjust * FTransform(FRotator(0.f, Yaw, 0.f), At);
	UStaticMeshComponent* M = AddMesh(RootComponent, P->Mesh, World.GetRelativeTransform(GetActorTransform()), true);
	if (!M) return -1;
	if (P->Material) M->SetMaterial(0, P->Material);
	TownBedMeshes.Add(M);
	MarkBlocked(At, Yaw, FVector2D(P->Size.X, P->Size.Y));
	FTownBed Bd; Bd.At = At; Bd.Yaw = Yaw; Bd.Bld = Bld; Bd.bMade = true;
	return TownBeds.Add(Bd);
}

void ARDDungeonGenerator::AssignTownBeds(ARDSection* S)
{
	if (!S || !GetWorld()) return;
	int32 Sleepers = 0, Given = 0, Made = 0;
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDTownBed), false);
	for (ARDTownsfolk* T : TownPeople) if (IsValid(T)) Q.AddIgnoredActor(T);
	for (int32 I = 0; I < TownPeople.Num(); ++I)
	{
		ARDTownsfolk* T = TownPeople[I];
		if (!IsValid(T) || T->GetHomeBuilding() < 0) continue;
		const int32 Hb = T->GetHomeBuilding();
		// (a resident sleeps at home; a keeper where it works if its post is inside (the trader at a stall outside never goes in))
		if (!T->IsResident() && S->TownBuildingAt(T->Post) != Hb) continue;
		// (one with no Sleep clip (the drunk's and the Dwarf smith's skeletons are not the clip's) sleeps where it stands, as before:
		// put in a bed it stood upright on it)
		if (!Townsfolk.IsValidIndex(T->Def) || !Townsfolk[T->Def].WorkClips.Contains(TEXT("Sleep"))) continue;
		++Sleepers;
		int32 Bi = S->TownBeds.IndexOfByPredicate([Hb](const ARDSection::FTownBed& Bd) { return Bd.Bld == Hb && Bd.Taken < 0; });
		if (Bi < 0) { Bi = S->AddTownBed(Hb); if (Bi >= 0) ++Made; }
		if (Bi < 0) continue;
		ARDSection::FTownBed& Bd = S->TownBeds[Bi];
		Bd.Taken = I;
		// (the bed's top under its middle, traced: the mattress, not its frame's foot)
		FHitResult Hit;
		float Top = Bd.At.Z + 55.f;
		if (GetWorld()->LineTraceSingleByChannel(Hit, Bd.At + FVector(0, 0, 200.f), Bd.At - FVector(0, 0, 20.f), ECC_Visibility, Q)) Top = Hit.ImpactPoint.Z;
		const FVector Fwd = FRotator(0.f, Bd.Yaw, 0.f).Vector();
		// (her hips a little toward the foot: the head lies on the pillow, the feet in the bed)
		const FVector Lie = Bd.At + Fwd * 15.f;
		T->SetBed(FVector(Lie.X, Lie.Y, Top), Bd.Yaw);
		++Given;
	}
	UE_LOG(LogRDList10d, Log, TEXT("RDTOWNBEDS %d sleepers, %d given beds (%d of the town's beds, %d put for them)"), Sleepers, Given, S->TownBeds.Num() - Made, Made);
}

TArray<FString> ARDDungeonGenerator::GetTownSleepLines() const
{
	TArray<FString> Out;
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S) return Out;
	int32 Made = 0, Given = 0, Sleepers = 0;
	for (const ARDSection::FTownBed& Bd : S->TownBeds) { if (Bd.bMade) ++Made; if (Bd.Taken >= 0) ++Given; }
	for (const ARDTownsfolk* T : TownPeople) if (IsValid(T) && T->HasBed()) ++Sleepers;
	Out.Add(FString::Printf(TEXT("posts|%d"), S->TownPosts.Num()));
	Out.Add(FString::Printf(TEXT("adults2|%d"), S->TownAdults2));
	Out.Add(FString::Printf(TEXT("homekids|%d"), S->TownHomeKids));
	Out.Add(FString::Printf(TEXT("squarekids|%d"), S->TownSquareKidsDropped));
	Out.Add(FString::Printf(TEXT("beds|%d|%d|%d|%d"), S->TownBeds.Num() - Made, Made, Sleepers, Given));
	for (int32 I = 0; I < TownPeople.Num(); ++I)
	{
		const ARDTownsfolk* T = TownPeople[I];
		if (!IsValid(T)) continue;
		const FVector B = T->GetBedAt();
		Out.Add(FString::Printf(TEXT("folk|%d|%s|%d|%d|%.0f|%.0f|%.0f|%s|%d|%d|%d|%d|%d"), I, *T->GetRoleName(), T->IsSleeping() ? 1 : 0, T->IsInBed() ? 1 : 0, B.X, B.Y, B.Z, *T->GetClipName(), T->GetHomeBuilding(),
			T->HasBed() ? 1 : 0, S->TownBuildingAt(T->GetActorLocation()), T->IsWalking() ? 1 : 0, T->Act));
	}
	return Out;
}
