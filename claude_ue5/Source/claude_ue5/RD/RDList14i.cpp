// The user's list of 2026-11-16 (docs/improvements14.txt; the plan docs/improvements14_plan.md), its ninth phase: locks, who hears
// and who sees (items 13 and 14): "in the wilderness, containers should be locked. rogues can pick the locks of these locked
// containers and warriors can break the locks, but if they do, it alerts any nearby NPCs and makes them hostile"; "if someone breaks
// open a container or picks the lock within line of sight of an NPC, the NPC becomes hostile and starts attacking". About half of the
// wild containers (not the gardens) are locked, by a hash of their key (always the same ones); the Rogue picks a lock by staying by it
// a moment, the Warrior breaks it at once, the others are refused. A lock picked or broken is heard by every person of the wilds
// within WildHearCm14 and seen by one with a clear line to her within WildSeeCm14 (not while she is in stealth): they turn hostile,
// run at her and strike (the town guards' strikes, 918 guards); a child and a quest's people run from her instead; once she is far
// off they calm down.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDTown.h"
#include "RD/RDGameInstance.h"
#include "RD/RDCombat.h"
#include "RD/RDWild.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimSequenceBase.h"
#include "RD/RDMistward.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDLocks14, Log, All);

bool ARDDungeonGenerator::IsWildKeyKept14(int64 Key) const
{
	// (the game's kept keys in a set, read again only when the list has changed (a load, a new game: its length and last key))
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return false;
	const int64 Last = GI->WildKilled.Num() > 0 ? GI->WildKilled.Last() : 0;
	if (GI->WildKilled.Num() != WildKeptRead14 || Last != WildKeptLast14)
	{
		WildKeptRead14 = GI->WildKilled.Num(); WildKeptLast14 = Last;
		WildKept14.Reset(); WildKept14.Append(GI->WildKilled);
	}
	return WildKept14.Contains(Key);
}

bool ARDDungeonGenerator::IsWildBoxLocked14(FName Kind, int64 Key) const
{
	// (a garden has no lock; one opened in this game is open; else by a hash of its key and the world's seed)
	if (!bWildLocks14 || Kind == TEXT("garden") || IsWildKeyKept14(Key)) return false;
	const uint32 H = HashCombine(GetTypeHash(Key), 0x10C14u ^ (uint32)(IsWildReady() ? Wild->Seed : 0));
	return (H % 1000u) < (uint32)FMath::Clamp(WildLockShare14 * 1000.f, 0.f, 1000.f);
}

FString ARDDungeonGenerator::WildLockDescribe14(FName Kind) const
{
	if (CurrentHero == TEXT("Rogue")) return FString::Printf(TEXT("pick the lock of the %s"), *Kind.ToString());
	if (CurrentHero == TEXT("Warrior")) return FString::Printf(TEXT("break the lock of the %s"), *Kind.ToString());
	return FString::Printf(TEXT("the %s is locked"), *Kind.ToString());
}

FString ARDDungeonGenerator::WildLockInteract14(ARDWildChunk* C, int32 Index)
{
	if (!C || !C->Doors.IsValidIndex(Index) || !PlayerCombat || !GetWorld()) return FString();
	const ARDWildChunk::FDoor& D = C->Doors[Index];
	const FString What = D.Kind.ToString();
	if (CurrentHero == TEXT("Rogue"))
	{
		// (a pick: she stays by it WildPickSeconds14, then it opens (TickWildPick14))
		if (WildPickKey14 == D.Key && WildPickUntil14 > 0.f) return TEXT("picking");
		WildPickChunk14 = C; WildPickIndex14 = Index; WildPickKey14 = D.Key;
		WildPickUntil14 = GetWorld()->GetTimeSeconds() + WildPickSeconds14;
		WildPickAt14 = PlayerCombat->GetOwner() ? PlayerCombat->GetOwner()->GetActorLocation() : D.At;
		PlayerCombat->ShowMessage(FString::Printf(TEXT("Picking the lock of the %s..."), *What));
		PlaySoundAt(TEXT("Env.ChestOpen"), D.At);
		return TEXT("pick");
	}
	if (CurrentHero == TEXT("Warrior"))
	{
		++WildLocksBroken14;
		PlaySoundAt(TEXT("Player.Hit.Axe"), D.At);
		PlayerCombat->ShowMessage(FString::Printf(TEXT("You break the lock of the %s"), *What));
		const FVector At = D.At;
		OpenWildBox(C, Index);
		AlertWildFolk14(At);
		return TEXT("break");
	}
	++WildLocksRefused14;
	PlayerCombat->ShowMessage(FString::Printf(TEXT("The %s is locked: a Rogue could pick it, a Warrior break it"), *What));
	return TEXT("locked");
}

void ARDDungeonGenerator::TickWildPick14()
{
	if (WildPickUntil14 <= 0.f || !GetWorld() || !PlayerCombat) return;
	ARDWildChunk* C = WildPickChunk14.Get();
	const AActor* Her = PlayerCombat->GetOwner();
	// (she went from it, or the box went with its chunk: the pick slips)
	if (!C || !C->Doors.IsValidIndex(WildPickIndex14) || C->Doors[WildPickIndex14].Key != WildPickKey14 || !Her || PlayerCombat->IsDead()
		|| FVector::Dist2D(Her->GetActorLocation(), WildPickAt14) > 120.f)
	{
		if (C && Her) PlayerCombat->ShowMessage(TEXT("The pick slips: stay by the lock to pick it"));
		WildPickUntil14 = -1.f; WildPickKey14 = -1;
		return;
	}
	if (GetWorld()->GetTimeSeconds() < WildPickUntil14) return;
	WildPickUntil14 = -1.f; WildPickKey14 = -1;
	++WildLocksPicked14;
	const FVector At = C->Doors[WildPickIndex14].At;
	PlayerCombat->ShowMessage(FString::Printf(TEXT("You pick the lock of the %s"), *C->Doors[WildPickIndex14].Kind.ToString()));
	OpenWildBox(C, WildPickIndex14);
	AlertWildFolk14(At);
}

int32 ARDDungeonGenerator::AlertWildFolk14(const FVector& At)
{
	// (heard by everyone near; seen by one with a clear line to her (static pieces between hide her), not while she is in stealth)
	AActor* Her = PlayerCombat ? PlayerCombat->GetOwner() : nullptr;
	if (!Her || !GetWorld()) return 0;
	const FVector Hc = Her->GetActorLocation() + FVector(0, 0, 40.f);
	const bool bHerHidden = PlayerCombat->IsStealthed();
	int32 Heard = 0, Seen = 0;
	for (ARDTownsfolk* T : WildPeople14())
	{
		if (!IsValid(T) || T->IsWildDead14() || T->IsWildHostile14() || (T->WildSiteCage.IsValid() && !T->bWildGiven)) continue;
		const float D = FVector::Dist(T->GetActorLocation(), At);
		const float Dh = FVector::Dist(T->GetActorLocation(), Hc);
		const bool bHeard = D <= WildHearCm14;
		const bool bSeen = !bHeard && !bHerHidden && Dh <= WildSeeCm14 && !T->IsWildIndoors() && !T->IsInBed() && WildSeesHer14(T->GetActorLocation() + FVector(0, 0, 70.f));
		if (!bHeard && !bSeen) continue;
		T->MakeWildHostile14(Her, bSeen);
		bSeen ? ++Seen : ++Heard;
	}
	LastWildAlertHeard14 = Heard; LastWildAlertSeen14 = Seen;
	if (Heard + Seen > 0) PlayerCombat->ShowMessage(Heard + Seen == 1 ? FString(TEXT("Someone noticed you: they turn on you")) : FString::Printf(TEXT("%d people noticed you: they turn on you"), Heard + Seen));
	UE_LOG(LogRDLocks14, Log, TEXT("RDWILDALERT at (%.0f, %.0f): %d heard, %d saw%s"), At.X, At.Y, Heard, Seen, bHerHidden ? TEXT(" (she was hidden)") : TEXT(""));
	return Heard + Seen;
}

bool ARDDungeonGenerator::WildWayBlocked14(const FVector& A, const FVector& B, float Radius, const AActor* Skip) const
{
	// (the world's pieces between A and B, static and dynamic: the wilds' farms, houses and boxes are made in play and are dynamic
	// objects (888 locks14's probe: 46 of 46 pieces round a farmstead; a line by the static objects alone met none of their walls, and
	// no spot round a farmhouse was hidden from her inside it). People, animals and pawns are dynamic too and pass over: they hide
	// nothing and stop no one's way)
	if (!GetWorld()) return false;
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDWildWay14), false, Skip);
	FCollisionObjectQueryParams O; O.AddObjectTypesToQuery(ECC_WorldStatic); O.AddObjectTypesToQuery(ECC_WorldDynamic);
	TArray<FHitResult> Hits;
	if (Radius > 0.f) GetWorld()->SweepMultiByObjectType(Hits, A, B, FQuat::Identity, O, FCollisionShape::MakeSphere(Radius), Q);
	else GetWorld()->LineTraceMultiByObjectType(Hits, A, B, O, Q);
	for (const FHitResult& H : Hits)
	{
		const AActor* Ac = H.GetActor();
		if (Ac && (Ac->IsA<ARDTownsfolk>() || Ac->IsA<ARDTownAnimal>() || Ac->IsA<APawn>() || Ac->GetClass()->GetName().Contains(TEXT("WildAnimal")) || Ac->IsA<ARDLootPile>())) continue;
		return true;
	}
	return false;
}

bool ARDDungeonGenerator::WildSeesHer14(FVector Eye) const
{
	// (a clear line from the eye to her chest)
	const AActor* Her = PlayerCombat ? PlayerCombat->GetOwner() : nullptr;
	if (!Her) return false;
	return !WildWayBlocked14(Eye, Her->GetActorLocation() + FVector(0, 0, 40.f), 0.f, Her);
}

void ARDDungeonGenerator::CalmWildFolk14()
{
	for (ARDTownsfolk* T : WildPeople14()) if (IsValid(T)) T->CalmWild14();
	WildPickUntil14 = -1.f; WildPickKey14 = -1;
}

// ================================================================================================ the person turned

void ARDTownsfolk::MakeWildHostile14(AActor* Her, bool bSeen)
{
	if (!Gen || !CanBeHurt14() || bWildHostile14) return;
	bWildHostile14 = true; WildFoe14 = Her; WildTurnedBy14 = bSeen ? TEXT("seen") : TEXT("heard");
	WildSwingT14 = -1.f; WildNextSwing14 = GetWorld() ? GetWorld()->GetTimeSeconds() + 0.6f : 0.f;
	// (its blow grown with the wilds' tier where it stands, as its hit points)
	WildBlow14 = Gen->WildFolkBlow14 * FMath::Max((float)Gen->WildGoldAt(1000, GetActorLocation()) / 1000.f, 1.f);
	InterruptLife14();
	// (out of its house at once, at its door (a farm's family indoors at night: it heard)
	if (bWildIndoors) { bWildIndoors = false; bWentHome = false; SetActorLocation(WildDoorOut); }
	// (out of a traveller's way and work)
	RoadPath.Reset(); SetProp(NAME_None);
}

void ARDTownsfolk::CalmWild14()
{
	if (!bWildHostile14) return;
	bWildHostile14 = false; WildFoe14 = nullptr; WildSwingT14 = -1.f;
	if (Body && CurAnim) { CurAnim = nullptr; }
	SetClip(false);
}

bool ARDTownsfolk::StepOnGround14(const FVector& Dir, float Sp, float Dt)
{
	// (straight over the ground, or as near that way as a wall lets it: a ball at its chest's height swept against the world's static
	// pieces, then 30, 60 and 90 degrees to either side)
	const FVector L = GetActorLocation();
	for (int32 K = 0; K < 7; ++K)
	{
		const float Off = K == 0 ? 0.f : (K % 2 ? 1.f : -1.f) * 30.f * ((K + 1) / 2);
		const FVector Dd = FRotator(0.f, Off, 0.f).RotateVector(Dir);
		FVector N = L + Dd * Sp * Dt;
		N.Z = Gen->WildGroundZ(N) + HalfHeight + 2.f;
		if (Gen->WildWayBlocked14(L + FVector(0, 0, 40.f), N + Dd * 40.f + FVector(0, 0, 40.f), 28.f, this)) continue;
		SetActorLocation(N, false);
		SetActorRotation(FRotator(0.f, FMath::RInterpConstantTo(GetActorRotation(), Dd.Rotation(), Dt, 540.f).Yaw, 0.f));
		return true;
	}
	return false;
}

bool ARDTownsfolk::TickHostile14(float Dt, float Now)
{
	URDCombatComponent* Pc = Gen ? Gen->GetPlayerCombat() : nullptr;
	AActor* Her = WildFoe14.Get();
	if (!Her || !Pc || Pc->IsDead() || FVector::Dist2D(Her->GetActorLocation(), GetActorLocation()) > Gen->WildCalmCm14) { CalmWild14(); return false; }
	FVector D = Her->GetActorLocation() - GetActorLocation(); const float Dz = FMath::Abs(D.Z); D.Z = 0.f;
	const float Dist = D.Size();
	auto Face = [&]() { if (!D.IsNearlyZero(1.f)) SetActorRotation(FRotator(0.f, FMath::RInterpConstantTo(GetActorRotation(), D.Rotation(), Dt, 540.f).Yaw, 0.f)); };
	// (a swing: its blow lands at the clip's hit time if she is still in reach)
	if (WildSwingT14 >= 0.f)
	{
		WildSwingT14 += Dt; Face();
		if (!bWildSwingHit14 && WildSwingT14 >= WildSwingHit14)
		{
			bWildSwingHit14 = true;
			if (Dist < 200.f && Dz < 200.f)
			{
				Pc->ApplyDamage(WildBlow14, this);
				++WildBlowsLanded14; ++Gen->WildFolkBlowsOnHer14;
				Gen->PlaySoundAt(TEXT("Player.Hit.Daggers"), Her->GetActorLocation());
			}
		}
		if (WildSwingT14 >= WildSwingLen14) { WildSwingT14 = -1.f; WildNextSwing14 = Now + 1.2f; CurAnim = nullptr; }
		return true;
	}
	// (in reach: it strikes in its turn; else it runs at her)
	if (Dist < 150.f)
	{
		Face();
		if (Now >= WildNextSwing14)
		{
			const int32 N = Gen->TownGuardStrikes.Num();
			const int32 K = N > 0 ? R.RandRange(0, N - 1) : -1;
			UAnimationAsset* A = K >= 0 ? Gen->TownGuardStrikes[K].Get() : nullptr;
			const UAnimSequenceBase* S = Cast<UAnimSequenceBase>(A);
			WildSwingLen14 = S ? S->GetPlayLength() : 1.f;
			WildSwingHit14 = Gen->TownGuardHitTimes.IsValidIndex(K) ? Gen->TownGuardHitTimes[K] : WildSwingLen14 * 0.5f;
			if (A) { CurAnim = A; CurRate = 1.f; Body->PlayAnimation(A, false); Body->SetPlayRate(1.f); }
			WildSwingT14 = 0.f; bWildSwingHit14 = false; ++WildStrikes14;
		}
		else SetClip(false);
		return true;
	}
	StepOnGround14(D.GetSafeNormal(), FMath::Max(Gen->WildFolkRunSpeed14, 50.f), Dt);
	UAnimationAsset* Run = WorkClip(TEXT("Run"));
	if (Run) PlayAnim(Run, 1.f); else { bWalkClip = true; PlayAnim(WalkAnim, Gen->WildFolkRunSpeed14 / FMath::Max(ClipSpeed, 1.f)); }
	return true;
}
