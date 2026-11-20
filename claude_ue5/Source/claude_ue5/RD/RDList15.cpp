// The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), its second phase: the Summoner's
// allies. Item 2, "the summoner should not be able to walk through her own summons": an ally's capsule is a Vehicle object, which
// her capsule blocks and which blocks her (its response to Pawn), while the monsters (whose capsules overlap Vehicle, Setup) and her
// other allies (Vehicle overlaps Vehicle) still pass it as before. Item 3, "if a summoner's minions are blocking the way and the
// summoner pushes on them, they should move away to make room": an ally ahead of her on her line while she presses toward it steps
// off it, to the side with room. Item 9: the arena's doors shut, her allies outside its room come in beside her. Item 30, "the
// summoner should be able to summon her minions in the wilderness": where no set of rooms stands under the spot, a summon is made
// in the wilds' section (open ground, no tile grid), and an ally's section follows where it stands.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDMonster.h"
#include "RD/RDSection.h"
#include "RD/RDCombat.h"
#include "RD/RDHorse.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList15, Log, All);

// ================================================================================================ item 2: solid to her
void ARDMonster::SetAllyCollision15(bool bSolid)
{
	UCapsuleComponent* C = GetCapsuleComponent();
	if (!C) return;
	if (!bSolid)
	{
		// (as before: she walks through her allies, and they through each other and the monsters)
		C->SetCollisionObjectType(ECC_Pawn);
		C->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
		return;
	}
	// (an object of the project's own channel (ECC_RDAlly, "RDAlly" in DefaultEngine.ini, blocked by default: PR #94's review, the
	// engine's Vehicle type was shared with the packs): her capsule blocks it by default; the monsters' overlap it (ARDMonster::Setup),
	// her other allies' too (below); its own response to Pawn blocks, so the pair with her blocks both ways and with a monster
	// resolves to the monster's overlap. What blocks only pawns (the horse's box, the pens' animals, the wilds' wade floor) blocks
	// RDAlly as well)
	C->SetCollisionObjectType(ECC_RDAlly);
	C->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
	C->SetCollisionResponseToChannel(ECC_RDAlly, ECR_Overlap);
}

void ARDMonster::ArriveAt15(const FVector& Feet)
{
	SetActorLocation(Feet + FVector(0, 0, GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 5.f), false, nullptr, ETeleportType::TeleportPhysics);
	Path.Reset();
	GetCharacterMovement()->Velocity = FVector::ZeroVector;
	// (its fight left where it was: a foe across a shut door kept it walking to the door (PR #94's review))
	CurrentFoe = nullptr; bAggro = false; AttackTime = -1.f; YieldUntil15 = -100.f;
}

// ================================================================================================ item 3: stepping aside
FVector ARDMonster::AllyYield15()
{
	const ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	if (!bAlly || bDead || !G || !G->bAllyYield15) return FVector::ZeroVector;
	const URDCombatComponent* Pc = G->GetPlayerCombat();
	const ACharacter* Her = Pc ? Cast<ACharacter>(Pc->GetOwner()) : nullptr;
	if (!Her || Pc->IsDead()) return FVector::ZeroVector;
	const float Now = GetWorld()->GetTimeSeconds();
	// (the way she presses: her movement's input (blocked by the ally her velocity is nothing), else where she is going)
	FVector Way = Her->GetCharacterMovement()->GetCurrentAcceleration(); Way.Z = 0.f;
	if (Way.SizeSquared() < 1.f) { Way = Her->GetVelocity(); Way.Z = 0.f; if (Way.Size() < 50.f) Way = FVector::ZeroVector; }
	const FVector L = GetActorLocation(), Hl = Her->GetActorLocation();
	const float R0 = GetCapsuleComponent()->GetScaledCapsuleRadius(), Rh = Her->GetCapsuleComponent()->GetScaledCapsuleRadius();
	bool bOnLine = false;
	FVector W = Way.GetSafeNormal();
	if (!W.IsNearlyZero() && FMath::Abs(L.Z - Hl.Z) < 200.f)
	{
		const FVector V = FVector(L.X - Hl.X, L.Y - Hl.Y, 0.f);
		const float Along = FVector::DotProduct(V, W), Across = FVector::CrossProduct(W, V).Z;
		// (within 1.2 m of her capsule ahead, and across her way by less than the two capsules and a margin: in her path)
		bOnLine = Along > 0.f && Along < 120.f + R0 + Rh && FMath::Abs(Across) < R0 + Rh + 30.f;
		if (bOnLine && Now >= YieldUntil15)
		{
			// (a new yield: to the side it already stands on, else the other, whichever has room; neither: on ahead of her. Its way is
			// fixed for the yield (PR #94's review: rebuilt from her way each frame, a turn of hers sent it into a wall))
			++Yields15; YieldStart15 = Now;
			const float Pref = Across >= 0.f ? 1.f : -1.f;
			const FVector Side = FVector(-W.Y, W.X, 0.f);
			YieldDir15 = W;
			for (const float S : { Pref, -Pref })
				if (!YieldBlocked15(Side * S, R0 + Rh + 90.f)) { YieldDir15 = (Side * S + W * 0.25f).GetSafeNormal(); break; }
		}
	}
	// (on while she keeps pressing, half a second after; never longer than 1.5 s a yield (with no room either side it went on ahead
	// of her down a whole hallway: PR #94's review), and ended where its way meets a wall)
	if (bOnLine && Now - YieldStart15 < 1.5f) YieldUntil15 = Now + 0.5f;
	if (Now >= YieldUntil15 || Now - YieldStart15 >= 1.5f) return FVector::ZeroVector;
	if (YieldBlocked15(YieldDir15, R0 + 30.f)) { YieldUntil15 = -100.f; return FVector::ZeroVector; }
	return YieldDir15;
}

bool ARDMonster::YieldBlocked15(const FVector& Way, float Len) const
{
	const ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDYield15), false, this);
	if (G) { G->IgnoreAllies15(Q); if (G->GetPlayerCombat()) Q.AddIgnoredActor(G->GetPlayerCombat()->GetOwner()); }
	FHitResult H; const FVector L = GetActorLocation();
	return GetWorld()->SweepSingleByChannel(H, L, L + Way.GetSafeNormal2D() * Len, FQuat::Identity, ECC_Visibility,
		FCollisionShape::MakeSphere(GetCapsuleComponent()->GetScaledCapsuleRadius() * 0.8f), Q);
}

// ================================================================================================ item 9: the arena
int32 ARDDungeonGenerator::GatherAlliesInRoom15(ARDSection* S, int32 Room)
{
	if (!bArenaAllies15 || !S || Room < 0 || !PlayerCombat || !PlayerCombat->GetOwner()) return 0;
	const FVector Hl = PlayerCombat->GetOwner()->GetActorLocation();
	// (only with her inside it: an arena begun from afar (a test's, a reel's) would shut her allies in without her (PR #94's review))
	if (S->RoomAt(Hl) != Room) return 0;
	// (the room's free tiles nearest her first; not on her, nor on one another)
	const TArray<FVector> Tiles = S->GetRoomFreeTilesNear(Room, Hl);
	TArray<FVector> Taken;
	for (const ARDMonster* A : Allies)
		if (IsValid(A) && !A->IsDead()) Taken.Add(A->GetActorLocation());
	int32 N = 0, Next = 0;
	for (ARDMonster* A : Allies)
	{
		if (!IsValid(A) || A->IsDead()) continue;
		const FVector L = A->GetActorLocation();
		// (in the room by its own tiles, not its rectangle: a shaped room's corners and its doorway are outside (PR #94's review))
		if (S->RoomAt(L) == Room && FMath::Abs(L.Z - Hl.Z) < 400.f) continue;
		for (; Next < Tiles.Num(); ++Next)
		{
			const FVector T = Tiles[Next];
			if (FVector::Dist2D(T, Hl) < 140.f) continue;
			if (Taken.ContainsByPredicate([&T](const FVector& O) { return FVector::Dist2D(O, T) < 120.f; })) continue;
			break;
		}
		if (Next >= Tiles.Num()) break;
		A->Section = S; A->bOpenGround = false;
		A->ArriveAt15(Tiles[Next]);
		Taken.Add(Tiles[Next]); ++Next; ++N;
	}
	ArenaAlliesBrought15 += N;
	if (N > 0) UE_LOG(LogRDList15, Log, TEXT("RDARENA15 %d allies brought into the arena beside her"), N);
	return N;
}

// ================================================================================================ item 30: the wilds
void ARDDungeonGenerator::IgnoreAllies15(FCollisionQueryParams& Q) const
{
	for (const ARDMonster* A : Allies) if (IsValid(A)) Q.AddIgnoredActor(A);
}

bool ARDDungeonGenerator::WildGroundAt15(const FVector& At, float FeetZ, float Rad, float Half, FVector& OutGround) const
{
	// (PR #94's review: the first hit down from over the spot was a farmhouse's roof, a floor above, a box or the horse's: the floors
	// under the point one after another, as the map's teleport takes them (RDList12.cpp); of those a capsule of its size fits on, the
	// one nearest FeetZ (her feet's height), within 2.5 m of it)
	UWorld* W = GetWorld();
	if (!W) return false;
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDWildGround15), false);
	if (PlayerCombat && PlayerCombat->GetOwner()) Q.AddIgnoredActor(PlayerCombat->GetOwner());
	IgnoreAllies15(Q);
	if (Horse) Q.AddIgnoredActor(Horse);
	FVector From(At.X, At.Y, FeetZ + 1500.f);
	const FVector To(At.X, At.Y, FeetZ - 1500.f);
	float BestD = 1e9f;
	for (int32 K = 0; K < 12; ++K)
	{
		FHitResult Hit;
		if (!W->LineTraceSingleByChannel(Hit, From, To, ECC_Visibility, Q)) break;
		const FVector C = Hit.ImpactPoint + FVector(0, 0, Half + 5.f);
		if (Hit.ImpactNormal.Z > 0.6f && !W->OverlapBlockingTestByChannel(C, FQuat::Identity, ECC_Pawn, FCollisionShape::MakeCapsule(Rad, Half), Q))
		{
			const float D = FMath::Abs(Hit.ImpactPoint.Z - FeetZ);
			if (D < 250.f && D < BestD) { BestD = D; OutGround = Hit.ImpactPoint; }
		}
		From = Hit.ImpactPoint - FVector(0, 0, 2.0);
	}
	return BestD < 1e8f;
}

void ARDDungeonGenerator::PlaceAllySection15(ARDMonster* A)
{
	if (!IsValid(A)) return;
	ARDSection* S = GetSection(WorldToSection(A->GetActorLocation()));
	if (S)
	{
		A->Section = S; A->bOpenGround = false;
		return;
	}
	// (out in the wilds, past every set of rooms: the wilds' section, open ground (straight at her and at its foe, no tiles))
	if (bWild && bWildSummons15)
	{
		if (ARDSection* Ws = EnsureWildSection()) { A->Section = Ws; A->bOpenGround = true; return; }
	}
	if (!IsValid(A->Section)) A->Section = GetSection(FIntPoint::ZeroValue);
}

FString ARDDungeonGenerator::GetAllies15() const
{
	TArray<FString> P;
	int32 N = 0;
	for (int32 I = 0; I < Allies.Num(); ++I)
	{
		const ARDMonster* A = Allies[I];
		if (!IsValid(A) || A->IsDead()) continue;
		++N;
		const FVector L = A->GetActorLocation();
		const AActor* F = A->GetCurrentFoe();
		P.Add(FString::Printf(TEXT("%d:%s:%.0f:%.0f:%.0f:%d:%d:%s"), I, *A->MonsterName.ToString(), L.X, L.Y, L.Z, A->Yields15, A->bOpenGround ? 1 : 0,
			F ? *F->GetClass()->GetName() : TEXT("-")));
	}
	return FString::Printf(TEXT("%d|%s"), N, *FString::Join(P, TEXT("|")));
}
