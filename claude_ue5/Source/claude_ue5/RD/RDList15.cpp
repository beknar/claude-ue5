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
	// (a Vehicle object (nothing else in the game is one): her capsule blocks Vehicle as a pawn does; the monsters' overlap it
	// (ARDMonster::Setup), her other allies' too (below); its own response to Pawn blocks, so the pair with her blocks both ways
	// and with a monster resolves to the monster's overlap)
	C->SetCollisionObjectType(ECC_Vehicle);
	C->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
	C->SetCollisionResponseToChannel(ECC_Vehicle, ECR_Overlap);
}

void ARDMonster::ArriveAt15(const FVector& Feet)
{
	SetActorLocation(Feet + FVector(0, 0, GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 5.f), false, nullptr, ETeleportType::TeleportPhysics);
	Path.Reset();
	GetCharacterMovement()->Velocity = FVector::ZeroVector;
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
			// (a new yield: to the side it already stands on, else the other, whichever has room; neither: on ahead of her)
			++Yields15;
			const float Pref = Across >= 0.f ? 1.f : -1.f;
			const FVector Side = FVector(-W.Y, W.X, 0.f);
			FCollisionQueryParams Q(SCENE_QUERY_STAT(RDYield15), false, this); Q.AddIgnoredActor(Her);
			for (const ARDMonster* A : G->GetAllies()) if (IsValid(A)) Q.AddIgnoredActor(A);
			YieldSide15 = 0.f;
			for (const float S : { Pref, -Pref })
			{
				FHitResult H;
				if (!GetWorld()->SweepSingleByChannel(H, L, L + Side * S * (R0 + Rh + 90.f), FQuat::Identity, ECC_Visibility, FCollisionShape::MakeSphere(R0 * 0.8f), Q)) { YieldSide15 = S; break; }
			}
		}
	}
	if (bOnLine) YieldUntil15 = Now + 0.5f;          // (and on while she keeps pressing, half a second after)
	if (Now >= YieldUntil15 || W.IsNearlyZero()) return FVector::ZeroVector;
	const FVector Side = FVector(-W.Y, W.X, 0.f);
	return YieldSide15 != 0.f ? (Side * YieldSide15 + W * 0.25f).GetSafeNormal() : W;
}

// ================================================================================================ item 9: the arena
int32 ARDDungeonGenerator::GatherAlliesInRoom15(ARDSection* S, int32 Room)
{
	if (!bArenaAllies15 || !S || Room < 0 || !PlayerCombat || !PlayerCombat->GetOwner()) return 0;
	const FVector Hl = PlayerCombat->GetOwner()->GetActorLocation();
	FVector2D Mn, Mx; S->GetRoomBounds(Room, Mn, Mx);
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
		const bool bIn = L.X > Mn.X + 20.f && L.X < Mx.X - 20.f && L.Y > Mn.Y + 20.f && L.Y < Mx.Y - 20.f && FMath::Abs(L.Z - Hl.Z) < 400.f;
		if (bIn) continue;
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
bool ARDDungeonGenerator::WildGroundAt15(const FVector& At, FVector& OutGround) const
{
	UWorld* W = GetWorld();
	if (!W) return false;
	FHitResult H; FCollisionQueryParams Q(SCENE_QUERY_STAT(RDWildGround15), false);
	if (PlayerCombat && PlayerCombat->GetOwner()) Q.AddIgnoredActor(PlayerCombat->GetOwner());
	for (const ARDMonster* A : Allies) if (IsValid(A)) Q.AddIgnoredActor(A);
	FCollisionObjectQueryParams O; O.AddObjectTypesToQuery(ECC_WorldStatic); O.AddObjectTypesToQuery(ECC_WorldDynamic);
	if (!W->LineTraceSingleByObjectType(H, At + FVector(0, 0, 400.f), At - FVector(0, 0, 1200.f), O, Q)) return false;
	OutGround = H.ImpactPoint;
	return true;
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
