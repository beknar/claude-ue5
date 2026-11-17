// The user's list of 2026-11-16 (docs/improvements14.txt; the plan docs/improvements14_plan.md), its seventh phase's first part:
// "the NPCs at farms should sleep at night" (item 16). A farmstead's family has no town section, so the town's day (TickDay) passed
// them by: they stood at their work all night. Their own: home at evening (to the farmhouse's door, then in), asleep at night in a
// bed of the house (its own and the ones laid where the room has room, WildKitBuilding), out to their work in the morning.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDTown.h"
#include "Engine/World.h"

void ARDDungeonGenerator::SetWildFarmFolkHome14(ARDTownsfolk* T, const FRDWildFarmRec& Rec, const FVector& DoorOut, const FVector& HouseIn, int32 K)
{
	if (!T) return;
	// (each its own place inside, side by side across the door's way: two of a household at one spot stood in each other)
	const FVector Out = (DoorOut - HouseIn).GetSafeNormal2D(), Side(-Out.Y, Out.X, 0.f);
	const FVector In = HouseIn + Side * ((K % 4) - 1.5f) * 55.f;
	T->SetWildFarmHome(FVector(DoorOut.X, DoorOut.Y, DoorOut.Z + 94.f), FVector(In.X, In.Y, In.Z + 92.f));
	if (!Rec.Beds14.IsValidIndex(K)) return;
	// (its bed's top under where it lies, traced (the mattress), its middle a little toward the foot (the town's AssignTownBeds))
	const FTransform& B = Rec.Beds14[K];
	const FVector Lie = B.GetLocation() + B.GetRotation().GetForwardVector() * 15.f;
	float Top = B.GetLocation().Z + 55.f;
	FHitResult Hit;
	FCollisionQueryParams Qp(SCENE_QUERY_STAT(RDFarmBed14), false); Qp.AddIgnoredActor(T);
	if (GetWorld()->LineTraceSingleByChannel(Hit, Lie + FVector(0, 0, 200.f), Lie - FVector(0, 0, 20.f), ECC_Visibility, Qp)) Top = Hit.Location.Z;
	T->SetBed(FVector(Lie.X, Lie.Y, Top), B.Rotator().Yaw);
}

bool ARDTownsfolk::TickWildFarmDay(float Now)
{
	// (the town's hours, a farm's earlier: home from half past eight, asleep from nine to half past five, out at six; the way to the
	// door straight over the ground (no tiles out here), tried again every 3 s, then put inside at the door as the town puts a
	// sleeper in who could not get home)
	if (!Gen || !Gen->bDayNight) return false;
	const float H = Gen->GetTownHour();
	const bool bHome = H >= 20.5f || H < 6.f, bNight = H >= 21.f || H < 5.5f;
	const FVector L = bInBed ? PreBed : GetActorLocation();
	if (bHome != bWentHome)
	{
		if (Act != 0) EndWork();
		bWentHome = bHome; HomeFails = 0; HomeRetryAt = Now + 3.f;
		Path.Reset();
		if (bHome) Path.Add(WildDoorOut);
		else
		{
			// (the morning: out of its door, then to its work)
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
