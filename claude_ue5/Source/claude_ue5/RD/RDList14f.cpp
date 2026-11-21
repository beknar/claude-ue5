// The user's list of 2026-11-16 (docs/improvements14.txt; the plan docs/improvements14_plan.md), its seventh phase's first part:
// "the NPCs at farms should sleep at night" (item 16). A farmstead's family has no town section, so the town's day (TickDay) passed
// them by: they stood at their work all night. Their own: home at evening (to the farmhouse's door, then in), asleep at night in a
// bed of the house (its own and the ones laid where the room has room, WildKitBuilding), out to their work in the morning.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDTown.h"
#include "Engine/World.h"

void ARDDungeonGenerator::SetWildFarmFolkHome14(ARDTownsfolk* T, const FRDWildFarmRec& Rec, const FVector& DoorOut, const FVector& HouseIn, int32 K)
{
	SetWildFolkHome15(T, Rec.Beds14, DoorOut, HouseIn, K);
}

void ARDDungeonGenerator::SetWildFolkHome15(ARDTownsfolk* T, const TArray<FTransform>& Beds, const FVector& DoorOut, const FVector& HouseIn, int32 K)
{
	// (one rule for a farm's family and a village's household (PR #100's review: the village's had copied it))
	if (!T) return;
	// (each its own place inside, side by side across the door's way: two of a household at one spot stood in each other)
	const FVector Out = (DoorOut - HouseIn).GetSafeNormal2D(), Side(-Out.Y, Out.X, 0.f);
	const FVector In = HouseIn + Side * ((K % 4) - 1.5f) * 55.f;
	T->SetWildFarmHome(FVector(DoorOut.X, DoorOut.Y, DoorOut.Z + 94.f), FVector(In.X, In.Y, In.Z + 92.f));
	if (!Beds.IsValidIndex(K)) return;
	// (its bed's top under where it lies, traced (the mattress), its middle a little toward the foot (the town's AssignTownBeds))
	const FTransform& B = Beds[K];
	const FVector Lie = B.GetLocation() + B.GetRotation().GetForwardVector() * 15.f;
	float Top = B.GetLocation().Z + 55.f;
	FHitResult Hit;
	FCollisionQueryParams Qp(SCENE_QUERY_STAT(RDFarmBed14), false); Qp.AddIgnoredActor(T);
	if (GetWorld()->LineTraceSingleByChannel(Hit, Lie + FVector(0, 0, 200.f), Lie - FVector(0, 0, 20.f), ECC_Visibility, Qp)) Top = Hit.Location.Z;
	T->SetBed(FVector(Lie.X, Lie.Y, Top), B.Rotator().Yaw);
}

// (a farm's hours, earlier than the town's resident's (19 home, 22 asleep, 6 up, 6.5 out): home from half past eight, asleep from
// nine to half past five, out at six)
static constexpr float RDFarmHomeFrom = 20.5f, RDFarmHomeTo = 6.f, RDFarmSleepFrom = 21.f, RDFarmSleepTo = 5.5f;

ARDTownsfolk* ARDDungeonGenerator::WildSleeperNear14(const FVector& From) const
{
	ARDTownsfolk* Best = nullptr; float Bd = 200.f;
	// (the farms' families and the villages' households (PR #100's review: a village's sleeper was never named))
	for (ARDTownsfolk* T : WildPeople14())
		if (IsValid(T) && T->IsSleeping())
		{
			const float D = FVector::Dist2D(T->GetActorLocation(), From);
			if (D < Bd && FMath::Abs(T->GetActorLocation().Z - From.Z) < 200.f) { Bd = D; Best = T; }
		}
	return Best;
}

bool ARDTownsfolk::TickWildFarmDay(float Now)
{
	// (the town's hours, a farm's earlier: home from half past eight, asleep from nine to half past five, out at six; the way to the
	// door straight over the ground (no tiles out here), tried again every 3 s, then put inside at the door as the town puts a
	// sleeper in who could not get home)
	if (!Gen) return false;
	// (no day and night: out of the house and at its work (PR #84's review: switched off at night they stayed inside for good))
	if (!Gen->bDayNight)
	{
		if (bInBed) { bInBed = false; SetClip(false); }
		if (bWildIndoors) { bWildIndoors = false; bWentHome = false; SetActorLocation(WildDoorOut); Path.Reset(); Path.Add(FVector(Post.X, Post.Y, Gen->WildGroundZ(Post) + 94.f)); }
		return Path.Num() > 0;
	}
	const float H = Gen->GetTownHour();
	const bool bHome = H >= RDFarmHomeFrom || H < RDFarmHomeTo, bNight = H >= RDFarmSleepFrom || H < RDFarmSleepTo;
	const FVector L = bInBed ? PreBed : GetActorLocation();
	if (bHome != bWentHome)
	{
		if (Act != 0) EndWork();
		bWentHome = bHome; HomeFails = 0; HomeRetryAt = Now + 3.f;
		Path.Reset();
		if (bHome) Path.Add(WildDoorOut);
		else
		{
			// (the morning: out of bed (not back to where it lay down from: the tick's way out of bed would have put it inside again,
			// PR #84's review), out of its door, then to its work)
			if (bInBed) { bInBed = false; SetClip(false); }
			if (bWildIndoors) { bWildIndoors = false; SetActorLocation(WildDoorOut); }
			Path.Add(FVector(Post.X, Post.Y, Gen->WildGroundZ(Post) + 94.f));
		}
	}
	if (Path.Num() == 0 && Now >= HomeRetryAt)
	{
		HomeRetryAt = Now + 3.f;
		if (bHome && !bWildIndoors)
		{
			// (at its door, or stopped on the way three times: in)
			if (FVector::Dist2D(L, WildDoorOut) < 150.f || ++HomeFails > 3) { SetActorLocation(WildIn); bWildIndoors = true; HomeFails = 0; }
			else Path.Add(WildDoorOut);
		}
		else if (!bHome && FVector::Dist2D(L, Post) > 120.f)
		{
			if (++HomeFails > 3) { SetActorLocation(FVector(Post.X, Post.Y, Gen->WildGroundZ(Post) + 92.f)); HomeFails = 0; }
			else Path.Add(FVector(Post.X, Post.Y, Gen->WildGroundZ(Post) + 94.f));
		}
	}
	bSleeping = bNight && bWildIndoors && Path.Num() == 0;
	return Path.Num() > 0;
}
