// mistward_castle: traps (the generator's Traps, FRDTrapDef). A set of rooms lays its traps from a stream of its own when
// it is built for play: some rooms (TrapRoomShare) and some hallway stretches (TrapHallShare) get one, of a kind its tier
// allows. Each waits until she comes within its Radius; then it goes off as its kind says:
//   mechanical: Pit (the plate drops, she is hurt and held), Missiles (darts from the walls), Deadfall (stones from the
//   ceiling), Crusher (a block slams down), Snare (held fast)
//   magical: Glyph (a rune that bursts), Ward (a barrier that burns and throws her back; it sets itself again), Emanation (a
//   cloud that hurts and slows while she stays), Cursed (a skull on a plinth: touched, it weakens her)
//   complex: Chain (a snare, then the deadfall, then a glyph), Lingering (worse the longer she stays: darts, fire, stones)
//   Teleport: she is carried off to another room of the tier, to monsters or to a ring of glyphs
// The Rogue (the generator's TrapFinders) sees a trap within TrapSenseRange (the HUD marks it) and F disarms it (a moment
// standing still; it may fail and go off). A spent or disarmed trap stays so (the generator's SpentTraps).
#include "RD/RDSection.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDCombat.h"
#include "RD/RDMonster.h"
#include "RD/RDMistward.h"
#include "Components/StaticMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "NiagaraComponent.h"
#include "Particles/ParticleSystemComponent.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDTraps, Log, All);

static const FName RDTrapTag(TEXT("RDInteractive"));


// ------------------------------------------------------------------------------------------------ laying them
void ARDSection::PlaceTraps()
{
	UWorld* W = GetWorld();
	if (!Generator || Generator->Traps.Num() == 0 || bCensus || !W || !W->IsGameWorld()) return;
	for (FTrapInst& T : TrapList) { for (TWeakObjectPtr<USceneComponent>& C : T.Comps) if (C.IsValid()) C->DestroyComponent(); for (auto& F : T.Fx) if (F.IsValid()) F->DestroyComponent(); }
	for (FTrapShot& S : TrapShots) if (S.C.IsValid()) S.C->DestroyComponent();
	TrapList.Reset(); TrapShots.Reset();
	const int32 Tier = Generator->TierOf(Coord);
	TArray<int32> Kinds; float WSum = 0.f;
	for (int32 I = 0; I < Generator->Traps.Num(); ++I)
		if (Generator->Traps[I].MinTier <= Tier && Generator->Traps[I].Weight > 0.f) { Kinds.Add(I); WSum += Generator->Traps[I].Weight; }
	if (Kinds.Num() == 0) return;
	FRandomStream R((int32)HashCombine((uint32)Seed ^ 0x7A11u, 5u));
	auto PickKind = [&](float U, bool bDoorway, bool bRoomLane) -> int32
	{
		// (a ward goes across a way through: a doorway or a hallway; a spring plate on a room's way (it throws her along the
		// room); the others anywhere)
		auto Fits = [&](int32 K) { const ERDTrapKind Kd = Generator->Traps[K].Kind; return (bDoorway || Kd != ERDTrapKind::Ward) && (bRoomLane || Kd != ERDTrapKind::Push); };
		float Sum = 0.f;
		for (const int32 K : Kinds) if (Fits(K)) Sum += Generator->Traps[K].Weight;
		float V = U * Sum;
		for (const int32 K : Kinds)
		{
			if (!Fits(K)) continue;
			V -= Generator->Traps[K].Weight;
			if (V <= 0.f) return K;
		}
		// (rounding past the end: the last kind that fits here, not the list's last (a spring plate in a hallway); none fits: -1)
		for (int32 J = Kinds.Num() - 1; J >= 0; --J) if (Fits(Kinds[J])) return Kinds[J];
		return -1;
	};
	const int32 StartRoom = Generator->IsStartSection(Coord) ? RoomAt(FVector(Generator->TileSize * 0.5f, Generator->TileSize * 0.5f, 0.f)) : -1;
	for (int32 RI = 0; RI < Rooms.Num(); ++RI)
	{
		const FRoom& Rm = Rooms[RI];
		const float U = R.FRand(), K = R.FRand(), Where = R.FRand();
		const int32 Pick = R.RandRange(0, 1 << 20);
		if (Rm.Kind == ERDRoomKind::Junction || RI == StartRoom || U >= Generator->TrapRoomShare) continue;
		// (on the way through: the lane tiles between the doors, not the doorway itself; else a free tile)
		TArray<FIntPoint> Lane, Free;
		for (int32 X = Rm.Min.X + 1; X < Rm.Max.X - 1; ++X)
			for (int32 Y = Rm.Min.Y + 1; Y < Rm.Max.Y - 1; ++Y)
			{
				const FIntPoint T(X, Y);
				if (!IsWalkable(T) || Owner[Idx(T)] != RI) continue;
				((X == Rm.Lane.X || Y == Rm.Lane.Y) ? Lane : Free).Add(T);
			}
		const bool bOnLane = Where < 0.6f && Lane.Num() > 0;
		const TArray<FIntPoint>& From = bOnLane ? Lane : (Free.Num() > 0 ? Free : Lane);
		if (From.Num() == 0) continue;
		const FIntPoint T = From[Pick % From.Num()];
		FTrapInst Ti; Ti.Def = PickKind(K, bOnLane, bOnLane); Ti.At = TileWorld(T); Ti.Room = RI;
		if (Ti.Def < 0) continue;
		Ti.Yaw = (T.Y == Rm.Lane.Y) ? 0.f : 90.f;          // (a ward stands across the way)
		TrapList.Add(Ti);
	}
	for (int32 CI = 0; CI < Corrs.Num(); ++CI)
	{
		const FCorr& C = Corrs[CI];
		const float U = R.FRand(), K = R.FRand();
		const int32 Len = C.bHoriz ? C.Max.X - C.Min.X : C.Max.Y - C.Min.Y;
		if (Len < 5 || U >= Generator->TrapHallShare) continue;
		const FIntPoint T = C.bHoriz ? FIntPoint(C.Min.X + Len / 2, C.Min.Y) : FIntPoint(C.Min.X, C.Min.Y + Len / 2);
		if (!In(T) || Type[Idx(T)] != 2) continue;
		FTrapInst Ti; Ti.Def = PickKind(K, true, false); Ti.At = TileWorld(T); Ti.bHall = true; Ti.Yaw = C.bHoriz ? 0.f : 90.f;
		if (Ti.Def < 0) continue;
		TrapList.Add(Ti);
	}
	// (the third list: a trap gauntlet's run of traps along its lanes, every other tile, from a stream of its own after the
	// rest: the others keep their indices)
	if (Generator->bSpecialRooms)
	{
		FRandomStream RG((int32)HashCombine((uint32)Seed ^ 0x6A47u, 9u));
		for (int32 RI = 0; RI < Rooms.Num(); ++RI)
		{
			const FRoom& Rm = Rooms[RI];
			if (Rm.Kind != ERDRoomKind::TrapGauntlet) continue;
			int32 K = 0;
			for (int32 X = Rm.Min.X + 1; X < Rm.Max.X - 1; ++X)
				for (int32 Y = Rm.Min.Y + 1; Y < Rm.Max.Y - 1; ++Y)
				{
					const FIntPoint T(X, Y);
					const bool bLane = X == Rm.Lane.X || Y == Rm.Lane.Y;
					if (!IsWalkable(T) || Owner[Idx(T)] != RI || (X + Y) % 2 != 0 || (!bLane && RG.FRand() < 0.5f)) continue;
					FTrapInst Ti; Ti.Def = PickKind(RG.FRand(), bLane, bLane); Ti.At = TileWorld(T); Ti.Room = RI;
					if (Ti.Def < 0) continue;
					Ti.Yaw = (T.Y == Rm.Lane.Y) ? 0.f : 90.f;
					TrapList.Add(Ti); ++K;
				}
			UE_LOG(LogRDTraps, Log, TEXT("RDTRAP (%d,%d): a trap gauntlet in room %d, %d traps"), Coord.X, Coord.Y, RI, K);
		}
	}
	for (int32 I = 0; I < TrapList.Num(); ++I)
	{
		if (const uint8* St = Generator->SpentTraps.Find(FIntVector(Coord.X, Coord.Y, I))) TrapList[I].State = *St;
		BuildTrapVisual(I);
	}
	if (TrapList.Num() > 0) UE_LOG(LogRDTraps, Log, TEXT("RDTRAP (%d,%d): %d traps"), Coord.X, Coord.Y, TrapList.Num());
}

int32 ARDSection::AddTrapAt(int32 Def, const FVector& At, uint8 State)
{
	if (!Generator || !Generator->Traps.IsValidIndex(Def)) return -1;
	FTrapInst Ti; Ti.Def = Def; Ti.At = FVector(At.X, At.Y, 0.f); Ti.Room = RoomAt(At); Ti.State = State;
	const int32 I = TrapList.Add(Ti);
	BuildTrapVisual(I);
	return I;
}

void ARDSection::BuildTrapVisual(int32 I)
{
	FTrapInst& T = TrapList[I];
	const FRDTrapDef& D = Generator->Traps[T.Def];
	// (what is seen of it: a plate, a rune, a skull; mounted at its place, turned across the way)
	if (D.Mesh && !(D.Kind == ERDTrapKind::Cursed && T.State == 2))
	{
		UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
		C->ComponentTags.Add(RDTrapTag);
		C->SetMobility(EComponentMobility::Movable);
		C->SetStaticMesh(D.Mesh);
		C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		C->SetupAttachment(RootComponent);
		C->RegisterComponent();
		C->SetWorldTransform(D.MeshTransform * FTransform(FRotator(0, T.Yaw, 0), T.At + FVector(0, 0, 0.5f)));
		T.Comps.Add(C); T.Moving = C;
	}
	// (a magic trap glows while it waits; spent, it is dark)
	if (D.IdleFx && T.State == 0)
		if (UFXSystemComponent* F = RDMSpawnFx(this, D.IdleFx, T.At + FVector(0, 0, D.Kind == ERDTrapKind::Ward ? 0.f : 3.f), FRotator(0, T.Yaw, 0), D.IdleFxScale, RootComponent, true, false))
		{
			F->SetUsingAbsoluteLocation(true); F->SetUsingAbsoluteRotation(true);
			F->SetWorldLocationAndRotation(T.At + FVector(0, 0, 3.f), FRotator(0, T.Yaw, 0));
			F->ComponentTags.Add(RDTrapTag);
			T.Fx.Add(F);
		}
}

// ------------------------------------------------------------------------------------------------ going off
void ARDSection::SpendTrap(int32 I, uint8 State)
{
	if (!TrapList.IsValidIndex(I)) return;
	FTrapInst& T = TrapList[I];
	T.State = State;
	if (Generator) Generator->SpentTraps.Add(FIntVector(Coord.X, Coord.Y, I), State);
	for (TWeakObjectPtr<UFXSystemComponent>& F : T.Fx) if (F.IsValid()) { F->DeactivateImmediate(); F->DestroyComponent(); }
	T.Fx.Reset();
	// (the third list: its red outline and ring go with it)
	for (TWeakObjectPtr<USceneComponent>& C : T.Comps)
	{
		if (!C.IsValid()) continue;
		if (C->ComponentHasTag(TEXT("RDOutline"))) { C->DestroyComponent(); continue; }
		if (UStaticMeshComponent* M = Cast<UStaticMeshComponent>(C.Get())) M->SetOverlayMaterial(nullptr);
	}
	T.Comps.RemoveAll([](const TWeakObjectPtr<USceneComponent>& C) { return !C.IsValid() || C->IsBeingDestroyed(); });
	// (a ward sets itself again; the others are spent)
}

bool ARDSection::FireTrap(int32 I)
{
	if (!TrapList.IsValidIndex(I) || !Generator) return false;
	FTrapInst& T = TrapList[I];
	if (T.State != 0) return false;
	const FRDTrapDef& D = Generator->Traps[T.Def];
	T.State = 1; T.Time = 0.f; T.Next = 0.f; T.Step = 0; T.Stay = 0.f;
	// (spent from now on for the set's next generation: dropped while it is still going off, it must not come back armed; a ward
	// sets itself again)
	if (D.Kind != ERDTrapKind::Ward) Generator->SpentTraps.Add(FIntVector(Coord.X, Coord.Y, I), 2);
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	T.Goal = Her ? Her->GetActorLocation() : T.At;
	++Generator->TrapsTriggered; Generator->LastTrap = D.Label;
	if (D.TriggerFx) RDMSpawnFx(this, D.TriggerFx, T.At + FVector(0, 0, 10), FRotator(0, T.Yaw, 0), D.TriggerFxScale, nullptr, D.bMagic, true);
	const FName Snd = D.SoundKey.IsNone() ? FName(D.bMagic ? TEXT("Player.Cast.Fire") : TEXT("Env.DoorOpen")) : FName(*FString::Printf(TEXT("Trap.%s.Trigger"), *D.SoundKey.ToString()));
	Generator->PlaySoundAt(Generator->HasSound(Snd) ? Snd : FName(TEXT("Env.GenerateHit")), T.At + FVector(0, 0, 100));
	if (URDCombatComponent* Pc = Generator->GetPlayerCombat()) Pc->ShowMessage(FString::Printf(TEXT("A trap: %s!"), *D.Label));
	UE_LOG(LogRDTraps, Log, TEXT("RDTRAP %s (%d) goes off in (%d,%d) at (%.0f, %.0f)"), *D.Name.ToString(), I, Coord.X, Coord.Y, T.At.X, T.At.Y);
	return true;
}

void ARDSection::TrapStrike(int32 I, const FVector& At, float Radius, float Share)
{
	URDCombatComponent* Pc = Generator ? Generator->GetPlayerCombat() : nullptr;
	const AActor* Her = Pc ? Pc->GetOwner() : nullptr;
	if (!Her || Pc->IsDead() || !TrapList.IsValidIndex(I)) return;
	const FVector L = Her->GetActorLocation();
	if (FVector::Dist2D(L, At) > Radius || FMath::Abs(L.Z - At.Z) > 300.f) return;
	const FRDTrapDef& D = Generator->Traps[TrapList[I].Def];
	Pc->ApplyDamage(FMath::Max(1.f, Pc->GetMaxHealth() * Share), nullptr);
	++Generator->TrapHits;
	if (D.HitFx) RDMSpawnFx(this, D.HitFx, FVector(L.X, L.Y, At.Z + 40.f), FRotator::ZeroRotator, D.HitFxScale, nullptr, D.bMagic, true);
	const FName Snd = D.SoundKey.IsNone() ? FName(TEXT("Monster.Strike")) : FName(*FString::Printf(TEXT("Trap.%s.Hit"), *D.SoundKey.ToString()));
	Generator->PlaySoundAt(Generator->HasSound(Snd) ? Snd : FName(TEXT("Monster.Strike")), L);
}

void ARDSection::TrapShoot(int32 I, uint8 Kind, const FVector& From, const FVector& To, float Speed)
{
	// (Kind 0 a dart flying straight, 1 a stone falling, 2 the crusher's block)
	if (!TrapList.IsValidIndex(I)) return;
	const FRDTrapDef& D = Generator->Traps[TrapList[I].Def];
	UStaticMesh* Mesh = D.Missile ? D.Missile.Get() : D.Mesh.Get();
	if (!Mesh) return;
	UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
	C->ComponentTags.Add(RDTrapTag);
	C->SetMobility(EComponentMobility::Movable);
	C->SetStaticMesh(Mesh);
	C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	C->SetupAttachment(RootComponent);
	C->RegisterComponent();
	const FVector Dir = (To - From).GetSafeNormal();
	C->SetWorldTransform(D.MissileTransform * FTransform(Kind == 0 ? Dir.Rotation() : FRotator(0, FMath::FRandRange(0.f, 360.f), 0), From));
	FTrapShot S; S.C = C; S.Trap = I; S.Kind = Kind; S.Goal = To; S.Vel = Kind == 0 ? Dir * Speed : FVector(0, 0, -Speed); S.Life = 0.f;
	TrapShots.Add(S);
	TrapList[I].Comps.Add(C);
}

// ------------------------------------------------------------------------------------------------ every frame (her section and the ones round it)
void ARDSection::TickTraps(float Dt, APawn* Her, URDCombatComponent* Pc)
{
	if (!Generator || (TrapList.Num() == 0 && TrapShots.Num() == 0)) return;
	const FVector L = Her ? Her->GetActorLocation() : FVector(1e9f);
	const bool bFinder = Generator->HeroFindsTraps();
	// what is on its way
	for (int32 K = TrapShots.Num() - 1; K >= 0; --K)
	{
		FTrapShot& S = TrapShots[K];
		UStaticMeshComponent* C = S.C.Get();
		if (!C || S.bDone) { TrapShots.RemoveAt(K); continue; }
		S.Life += Dt;
		if (S.Kind == 1) S.Vel.Z -= 1800.f * Dt;
		const FVector P0 = C->GetComponentLocation();
		const FVector P = P0 + S.Vel * Dt;
		C->SetWorldLocation(P);
		const FRDTrapDef& D = Generator->Traps[TrapList.IsValidIndex(S.Trap) ? TrapList[S.Trap].Def : 0];
		if (S.Kind == 0)
		{
			// (a dart: it strikes her if it passes within reach of her body on its way this frame (it flies 26 m a second: 65 cm
			// a frame at 40 frames a second, more than her body is wide: its end point alone passed her by))
			if (Her && FMath::PointDistToSegment(L, P0, P) < 55.f) { TrapStrike(S.Trap, L, 1e6f, D.Damage * 0.35f); S.bDone = true; C->DestroyComponent(); continue; }
			if (FVector::DotProduct(S.Goal - P, S.Vel) < 0.f || S.Life > 2.f) { S.bDone = true; C->DestroyComponent(); }
		}
		else if (P.Z <= S.Goal.Z)
		{
			// (a stone or the block lands: what is under it is struck; the stones lie where they fell)
			C->SetWorldLocation(FVector(P.X, P.Y, S.Goal.Z));
			TrapStrike(S.Trap, S.Goal, S.Kind == 2 ? D.Radius : 110.f, S.Kind == 2 ? D.Damage : D.Damage * 0.4f);
			if (D.HitFx) RDMSpawnFx(this, D.HitFx, S.Goal + FVector(0, 0, 10), FRotator::ZeroRotator, D.HitFxScale, nullptr, false, true);
			Generator->PlaySoundAt(TEXT("Env.BodyFall"), S.Goal);
			S.bDone = true;
		}
	}
	for (int32 I = 0; I < TrapList.Num(); ++I)
	{
		FTrapInst& T = TrapList[I];
		const FRDTrapDef& D = Generator->Traps[T.Def];
		const float Dist = FVector::Dist2D(L, T.At);
		const bool bNear = Her && FMath::Abs(L.Z - T.At.Z) < 300.f;
		if (T.State == 0)
		{
			// (the Rogue sees it coming)
			if (bFinder && bNear && !T.bSeen && Dist < Generator->TrapSenseRange)
			{
				T.bSeen = true;
				if (Pc) Pc->ShowMessage(FString::Printf(TEXT("You spot a trap: %s (F to disarm)"), *D.Label));
				if (Generator->bTrapOutline) OutlineTrap(I);          // (the third list: much more visible once seen)
			}
			if (bNear && Dist < D.Radius && Pc && !Pc->IsDead() && !(Generator->DisarmKey == FIntVector(Coord.X, Coord.Y, I))) FireTrap(I);
			continue;
		}
		if (T.State != 1) continue;
		T.Time += Dt;
		// (mistward5: the ceiling over each shot as it is: a vault's height there, below a beamed room's beams; the tile's
		// height under a vault was the room's, and the stones came out of the air metres under it)
		auto Ceil = [this](const FVector& P) { const int32 Rm = RoomAt(P); return GetCeilingHeightAt(P) - (Rooms.IsValidIndex(Rm) && Rooms[Rm].Ceil == 2 ? 60.f : 0.f); };
		const float Share = D.Damage;
		switch (D.Kind)
		{
		case ERDTrapKind::Pit:
			if (T.Step == 0) { if (UStaticMeshComponent* M = T.Moving.Get()) M->AddWorldOffset(FVector(0, 0, -70.f)); if (Pc && Dist < D.Radius * 1.6f) Pc->HoldFor(D.Seconds); T.Step = 1; }
			if (T.Step == 1 && T.Time > 0.25f) { TrapStrike(I, T.At, D.Radius * 1.6f, Share); T.Step = 2; }
			if (T.Time > 1.2f) SpendTrap(I, 2);
			break;
		case ERDTrapKind::Missiles:
		{
			// (three darts from the wall beside the way, at her as she is when each is loosed)
			if (T.Time >= T.Next && T.Step < 3)
			{
				const FVector Side = FRotator(0, T.Yaw + 90.f, 0).Vector();
				const FVector From = T.At + Side * (Generator->TileSize * 0.5f - 25.f) * (T.Step % 2 ? -1.f : 1.f) + FVector(0, 0, 120.f);
				const FVector To = Her ? L + FVector(0, 0, 20.f) : T.At + FVector(0, 0, 100.f);
				TrapShoot(I, 0, From, To + (To - From).GetSafeNormal() * 400.f, 2600.f);
				Generator->PlaySoundAt(TEXT("Player.Whoosh"), From);
				++T.Step; T.Next = T.Time + 0.28f;
			}
			if (T.Time > 2.f) SpendTrap(I, 2);
			break;
		}
		case ERDTrapKind::Deadfall:
			if (T.Time >= T.Next && T.Step < 3)
			{
				const FVector Off(FMath::FRandRange(-90.f, 90.f), FMath::FRandRange(-90.f, 90.f), 0.f);
				const FVector Aim = (T.Step == 0 && Her ? FVector(L.X, L.Y, T.At.Z) : T.Goal * FVector(1, 1, 0) + FVector(0, 0, T.At.Z)) + Off;
				TrapShoot(I, 1, Aim + FVector(0, 0, Ceil(Aim) - 60.f), Aim, 200.f);
				++T.Step; T.Next = T.Time + 0.22f;
			}
			if (T.Time > 2.5f) SpendTrap(I, 2);
			break;
		case ERDTrapKind::Crusher:
			if (T.Step == 0) { TrapShoot(I, 2, T.At + FVector(0, 0, Ceil(T.At) - 80.f), T.At, 900.f); T.Step = 1; Generator->PlaySoundAt(TEXT("Env.Generate"), T.At); }
			if (T.Time > 2.2f) SpendTrap(I, 2);
			break;
		case ERDTrapKind::Snare:
			if (T.Step == 0) { if (Pc && Dist < D.Radius * 1.5f) { Pc->HoldFor(D.Seconds); TrapStrike(I, T.At, D.Radius * 1.5f, Share); } T.Step = 1; }
			if (T.Time > 0.5f) SpendTrap(I, 2);
			break;
		case ERDTrapKind::Glyph:
			if (T.Step == 0 && T.Time > 0.55f) { TrapStrike(I, T.At, D.Radius * 1.7f, Share); if (D.HitFx) RDMSpawnFx(this, D.HitFx, T.At + FVector(0, 0, 20), FRotator::ZeroRotator, D.HitFxScale, nullptr, true, true); T.Step = 1; }
			if (T.Time > 1.2f) SpendTrap(I, 2);
			break;
		case ERDTrapKind::Ward:
			if (T.Step == 0)
			{
				TrapStrike(I, T.At, D.Radius * 1.4f, Share);
				// (thrown back the way she came)
				if (ACharacter* Ch = Cast<ACharacter>(Her)) { FVector Back = (L - T.At) * FVector(1, 1, 0); Ch->LaunchCharacter(Back.GetSafeNormal(1e-3f, -Ch->GetActorForwardVector()) * 700.f + FVector(0, 0, 250.f), true, true); }
				T.Step = 1;
			}
			// (it sets itself again once she is clear of it)
			if (T.Time > 2.5f && Dist > D.Radius * 1.5f) { T.State = 0; T.Step = 0; }
			break;
		case ERDTrapKind::Emanation:
			if (T.Step == 0) { if (D.HitFx) T.Fx.Add(RDMSpawnFx(this, D.HitFx, T.At + FVector(0, 0, 10), FRotator::ZeroRotator, D.HitFxScale, nullptr, true, false)); T.Step = 1; }
			if (T.Time >= T.Next)
			{
				T.Next = T.Time + 0.5f;
				if (bNear && Dist < D.Radius * 2.f && Pc && !Pc->IsDead())
				{
					Pc->ApplyDamage(FMath::Max(1.f, Pc->GetMaxHealth() * Share * 0.12f), nullptr); ++Generator->TrapHits;
					Pc->ApplyMonsterAbility(ERDMonsterAbility::Slow, 2.f, 0.f);
				}
			}
			if (T.Time > D.Seconds) SpendTrap(I, 2);
			break;
		case ERDTrapKind::Cursed:
			if (T.Step == 0)
			{
				if (Pc) { Pc->ApplyMonsterAbility(ERDMonsterAbility::Weaken, 3.f, 0.f); Pc->ShowMessage(FString::Printf(TEXT("The %s curses you: your blows are weaker"), *D.Label)); }
				TrapStrike(I, T.At, D.Radius * 2.f, Share);
				if (UStaticMeshComponent* M = T.Moving.Get()) M->SetVisibility(false);
				T.Step = 1;
			}
			if (T.Time > 0.6f) SpendTrap(I, 2);
			break;
		case ERDTrapKind::Chain:
			// (a snare holds her; stones fall on her; a rune bursts under her)
			if (T.Step == 0) { if (Pc && Dist < D.Radius * 1.5f) Pc->HoldFor(2.4f); T.Step = 1; }
			if (T.Step == 1 && T.Time > 0.8f)
			{
				for (int32 K = 0; K < 3; ++K) { const FVector A = FVector(L.X, L.Y, T.At.Z) + FVector(FMath::FRandRange(-70.f, 70.f), FMath::FRandRange(-70.f, 70.f), 0.f); TrapShoot(I, 1, A + FVector(0, 0, Ceil(A) - 60.f - 40.f * K), A, 150.f); }
				T.Step = 2;
			}
			if (T.Step == 2 && T.Time > 2.0f)
			{
				if (D.HitFx) RDMSpawnFx(this, D.HitFx, FVector(L.X, L.Y, T.At.Z + 20.f), FRotator::ZeroRotator, D.HitFxScale, nullptr, true, true);
				TrapStrike(I, FVector(L.X, L.Y, T.At.Z), 200.f, Share * 0.6f);
				T.Step = 3;
			}
			if (T.Time > 2.8f) SpendTrap(I, 2);
			break;
		case ERDTrapKind::Lingering:
		{
			// (while she stays, every moment something worse; it ends once she is gone a while)
			const bool bIn = bNear && Dist < D.Radius * 2.4f;
			T.Stay = bIn ? 0.f : T.Stay + Dt;
			if (bIn && T.Time >= T.Next)
			{
				T.Next = T.Time + 1.3f;
				const int32 Stage = T.Step++ % 3;
				if (Stage == 0) for (int32 K = 0; K < 2; ++K) TrapShoot(I, 0, T.At + FRotator(0, T.Yaw + 90.f + 180.f * K, 0).Vector() * (Generator->TileSize * 0.5f - 25.f) + FVector(0, 0, 120.f), L + FVector(0, 0, 20.f) + (L - T.At).GetSafeNormal2D() * 300.f, 2600.f);
				else if (Stage == 1) { if (D.HitFx) RDMSpawnFx(this, D.HitFx, FVector(L.X, L.Y, T.At.Z + 20.f), FRotator::ZeroRotator, D.HitFxScale, nullptr, true, true); TrapStrike(I, FVector(L.X, L.Y, T.At.Z), 180.f, Share * (0.3f + 0.1f * T.Step)); }
				else { const FVector A(L.X, L.Y, T.At.Z); TrapShoot(I, 1, A + FVector(0, 0, Ceil(A) - 60.f), A, 250.f); }
			}
			if (T.Stay > 1.5f || T.Time > 25.f) SpendTrap(I, 2);
			break;
		}
		case ERDTrapKind::Teleport:
			if (T.Step == 0 && T.Time > 0.7f && Pc && Her && Dist < D.Radius * 2.f)
			{
				T.Step = 1;
				// (another room of this tier: one that is built now, not this one; half the time monsters wait there, else a
				// ring of glyphs closes on her)
				TArray<TPair<ARDSection*, FVector>> Rooms_;
				for (const FIntPoint& Sc : Generator->GetSectionCoords())
				{
					ARDSection* S = Generator->GetSection(Sc);
					if (!S || S->IsBuilding() || Generator->TierOf(Sc) != Generator->TierOf(Coord)) continue;
					for (int32 RI = 0; RI < S->GetNumRooms(); ++RI)
					{
						if (S == this && RI == T.Room) continue;
						const TArray<FVector> Fr = S->GetRoomFreeTiles(RI);
						if (Fr.Num() >= 9 && S->GetRoomKind(RI) != ARDDungeonGenerator::KindName(ERDRoomKind::Junction)) Rooms_.Add({ S, Fr[Fr.Num() / 2] });
					}
				}
				if (Rooms_.Num() > 0)
				{
					const uint32 H = HashCombine((uint32)Generator->SessionSeed, GetTypeHash(FIntVector(Coord.X, Coord.Y, I)));
					const TPair<ARDSection*, FVector> Dst = Rooms_[H % (uint32)Rooms_.Num()];
					ACharacter* Ch = Cast<ACharacter>(Her);
					const FVector To = Dst.Value + FVector(0, 0, Ch ? Ch->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 10.f : 100.f);
					if (D.TriggerFx) RDMSpawnFx(this, D.TriggerFx, L, FRotator::ZeroRotator, D.TriggerFxScale, nullptr, true, true);
					if (Ch) { Ch->SetActorLocation(To, false, nullptr, ETeleportType::TeleportPhysics); Ch->GetCharacterMovement()->StopMovementImmediately(); }
					if (D.TriggerFx) RDMSpawnFx(this, D.TriggerFx, To, FRotator::ZeroRotator, D.TriggerFxScale, nullptr, true, true);
					// (the room may be one of this set: the glyphs added can move this list, and T with it: T is not used after this)
					Dst.Key->TrapAmbush(Dst.Value, H, TEXT("A teleport trap carries you off"));
					UE_LOG(LogRDTraps, Log, TEXT("RDTRAP teleport to (%.0f, %.0f) in (%d,%d): %s"), To.X, To.Y, Dst.Key->Coord.X, Dst.Key->Coord.Y, *Dst.Key->LastAmbush);
				}
			}
			if (TrapList[I].Time > 1.5f) SpendTrap(I, 2);          // (TrapList[I], not T: see the glyphs above)
			break;
		case ERDTrapKind::Push:
		{
			// (directional: a spring plate on the room's way hurls her along it, away from the side she came by, to the room's far
			// end; there monsters wait or a ring of glyphs (TrapAmbush))
			ACharacter* Ch = Cast<ACharacter>(Her);
			if (T.Step == 0)
			{
				T.Step = 1;
				FVector Dir = FRotator(0, T.Yaw, 0).Vector();
				const FVector Came = Her ? (Her->GetVelocity().Size2D() > 60.f ? Her->GetVelocity() : (T.At - L)) : Dir;
				if (FVector::DotProduct(Dir, Came) < 0.f) Dir = -Dir;
				// the last free tile of the room along that way (her body clear of what stands there)
				const FIntPoint T0 = WorldToLocal(T.At);
				const FIntPoint Step(FMath::RoundToInt(Dir.X), FMath::RoundToInt(Dir.Y));
				FIntPoint Last = T0;
				for (FIntPoint P = T0 + Step; In(P) && Owner[Idx(P)] == T.Room && IsWalkable(P) && !Blocked[Idx(P)]; P += Step) Last = P;
				T.Goal = FVector(TileWorld(Last).X, TileWorld(Last).Y, T.At.Z);
				T.Next = (float)(FMath::Abs(Last.X - T0.X) + FMath::Abs(Last.Y - T0.Y));       // (tiles to go)
				if (Pc) { Pc->HoldFor(2.f); Pc->ShowMessage(FString::Printf(TEXT("A %s hurls you across the room!"), *D.Label)); }
				if (D.HitFx) RDMSpawnFx(this, D.HitFx, T.At + FVector(0, 0, 10), FRotator::ZeroRotator, D.HitFxScale, nullptr, false, true);
				Generator->PlaySoundAt(TEXT("Player.Whoosh"), T.At + FVector(0, 0, 100));
				T.Stay = 0.f;
			}
			if (T.Step == 1)
			{
				// (carried at 14 m/s, swept: what stands in the way stops her where it stands)
				// (she fell mid-flight, or is another pawn now: the throw ends where she is)
				bool bArrived = !Ch || T.Next < 1.f || !Pc || Pc->IsDead() || Pc->GetOwner() != Ch;
				if (Ch)
				{
					const FVector D2 = FVector(T.Goal.X - L.X, T.Goal.Y - L.Y, 0.f);
					const float Left = D2.Size();
					if (Left < 25.f || T.Time > 2.5f) bArrived = true;
					else
					{
						const FVector Before = Ch->GetActorLocation();
						Ch->SetActorLocation(Before + D2 / Left * FMath::Min(Left, 1400.f * Dt), true);
						T.Stay = FVector::Dist2D(Ch->GetActorLocation(), Before) < 1.f ? T.Stay + Dt : 0.f;
						if (T.Stay > 0.12f) bArrived = true;
					}
				}
				if (bArrived)
				{
					T.Step = 2;
					const FVector Landed = Ch ? Ch->GetActorLocation() : T.Goal;
					TrapStrike(I, FVector(Landed.X, Landed.Y, T.At.Z), 200.f, Share);
					Generator->PlaySoundAt(TEXT("Env.BodyFall"), Landed);
					const uint32 H = HashCombine((uint32)Generator->SessionSeed, GetTypeHash(FIntVector(Coord.X, Coord.Y, I)));
					TrapAmbush(FVector(Landed.X, Landed.Y, T.At.Z), H, *FString::Printf(TEXT("A %s hurls you across the room"), *D.Label));
					UE_LOG(LogRDTraps, Log, TEXT("RDTRAP push in (%d,%d) from (%.0f, %.0f) to (%.0f, %.0f): %s"), Coord.X, Coord.Y, TrapList[I].At.X, TrapList[I].At.Y, Landed.X, Landed.Y, *LastAmbush);
				}
			}
			// (TrapList[I], not T: the glyphs may have been added to this list)
			if (TrapList[I].Step == 2 && TrapList[I].Time > 0.3f) SpendTrap(I, 2);
			break;
		}
		}
	}
}

void ARDSection::TrapAmbush(const FVector& At, uint32 H, const TCHAR* How)
{
	if (!Generator) return;
	URDCombatComponent* Pc = Generator->GetPlayerCombat();
	const bool bMonsters = (H >> 8) % 2 == 0;
	if (bMonsters)
	{
		TArray<int32> Kinds; Generator->MonsterKindsFor(Coord, Kinds);
		const TArray<FVector> Fr = GetRoomFreeTiles(RoomAt(At));
		int32 Made = 0;
		for (int32 K = 0; K < 3 && Kinds.Num() > 0 && Fr.Num() > 0; ++K)
			if (Generator->SpawnMonsterKind(Kinds[(H + K * 7) % (uint32)Kinds.Num()], Fr[(H / 3 + K * 5) % (uint32)Fr.Num()], Generator->TierOf(Coord))) ++Made;
		LastAmbush = FString::Printf(TEXT("monsters|%d|%.0f|%.0f"), Made, At.X, At.Y);
		if (Pc) Pc->ShowMessage(FString::Printf(TEXT("%s: into a room of monsters"), How));
	}
	else
	{
		// (glyphs round her, going off one after the other: she must move)
		const int32 Glyph = Generator->Traps.IndexOfByPredicate([](const FRDTrapDef& G) { return G.Kind == ERDTrapKind::Glyph; });
		int32 Made = 0;
		for (int32 K = 0; K < 4 && Glyph >= 0; ++K)
		{
			const int32 Gi = AddTrapAt(Glyph, At + FRotator(0, 90.f * K + 45.f, 0).Vector() * 170.f, 1);
			if (TrapList.IsValidIndex(Gi)) { TrapList[Gi].Time = -0.6f * K - 0.8f; ++Made; }
		}
		LastAmbush = FString::Printf(TEXT("glyphs|%d|%.0f|%.0f"), Made, At.X, At.Y);
		if (Pc) Pc->ShowMessage(FString::Printf(TEXT("%s: into a ring of glyphs"), How));
	}
}

// ------------------------------------------------------------------------------------------------ the generator's side
void ARDDungeonGenerator::TickTraps(float Dt)
{
	APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Her) return;
	URDCombatComponent* Pc = GetPlayerCombat();
	const FIntPoint Here = WorldToSection(Her->GetActorLocation());
	FString Seen;
	for (int32 Dx = -1; Dx <= 1; ++Dx)
		for (int32 Dy = -1; Dy <= 1; ++Dy)
			if (ARDSection* S = GetSection(Here + FIntPoint(Dx, Dy)))
			{
				if (bLogTraps) Seen += FString::Printf(TEXT(" (%d,%d)%s%d"), S->Coord.X, S->Coord.Y, S->IsBuilding() ? TEXT("b") : TEXT(":"), S->TrapList.Num());
				if (!S->IsBuilding()) S->TickTraps(Dt, Her, Pc);
			}
	if (bLogTraps && GetWorld()->GetTimeSeconds() - TrapLogTime > 1.f)
	{
		TrapLogTime = GetWorld()->GetTimeSeconds();
		const FVector L = Her->GetActorLocation(); float Best = 1e9f; FString Near;
		for (const auto& KV : Sections)
			if (const ARDSection* S = KV.Value)
				for (int32 I = 0; I < S->TrapList.Num(); ++I)
				{
					const float D = FVector::Dist2D(S->TrapList[I].At, L);
					if (D < Best) { Best = D; Near = FString::Printf(TEXT("(%d,%d) %d %s state %d dist %.0f dz %.0f radius %.0f"), KV.Key.X, KV.Key.Y, I, *Traps[S->TrapList[I].Def].Name.ToString(), S->TrapList[I].State, D, L.Z - S->TrapList[I].At.Z, Traps[S->TrapList[I].Def].Radius); }
				}
		UE_LOG(LogRDTraps, Log, TEXT("RDTRAPTICK her (%.0f, %.0f, %.0f) in (%d,%d), sets ticked:%s | nearest: %s | dead %d"), L.X, L.Y, L.Z, Here.X, Here.Y, *Seen, *Near, Pc && Pc->IsDead() ? 1 : 0);
	}
	// (the Rogue disarming one: she stands still a moment; moved or struck, she stops)
	if (DisarmKey.Z >= 0)
	{
		ARDSection* S = GetSection(FIntPoint(DisarmKey.X, DisarmKey.Y));
		const float Now = GetWorld()->GetTimeSeconds();
		if (!S || !S->TrapList.IsValidIndex(DisarmKey.Z) || S->TrapList[DisarmKey.Z].State != 0) { DisarmKey.Z = -1; return; }
		if (FVector::Dist2D(Her->GetActorLocation(), DisarmFrom) > 90.f || (Pc && Pc->LastHurtTime > DisarmStart))
		{
			if (Pc) Pc->ShowMessage(TEXT("You stop disarming"));
			DisarmKey.Z = -1;
			return;
		}
		if (Now - DisarmStart >= DisarmSeconds)
		{
			const int32 I = DisarmKey.Z; DisarmKey.Z = -1;
			const FRDTrapDef& D = Traps[S->TrapList[I].Def];
			if (TrapR.FRand() < DisarmChance)
			{
				S->SpendTrap(I, 3);
				++TrapsDisarmed;
				if (Pc) Pc->ShowMessage(FString::Printf(TEXT("You disarm the %s"), *D.Label));
				PlaySoundAt(TEXT("Player.Repair"), Her->GetActorLocation());
				UE_LOG(LogRDTraps, Log, TEXT("RDTRAP %s (%d) disarmed in (%d,%d)"), *D.Name.ToString(), I, S->Coord.X, S->Coord.Y);
			}
			else
			{
				if (Pc) Pc->ShowMessage(FString::Printf(TEXT("You fumble: the %s goes off"), *D.Label));
				S->FireTrap(I);
			}
		}
	}
}

bool ARDDungeonGenerator::BeginDisarmNear(const FVector& From)
{
	if (!HeroFindsTraps() || DisarmKey.Z >= 0) return false;
	const FIntPoint Here = WorldToSection(From);
	float Best = 280.f; FIntVector Key(0, 0, -1);
	for (int32 Dx = -1; Dx <= 1; ++Dx)
		for (int32 Dy = -1; Dy <= 1; ++Dy)
			if (const ARDSection* S = GetSection(Here + FIntPoint(Dx, Dy)))
				for (int32 I = 0; I < S->TrapList.Num(); ++I)
				{
					const ARDSection::FTrapInst& T = S->TrapList[I];
					const float D = FVector::Dist2D(T.At, From);
					if (T.State == 0 && T.bSeen && D < Best) { Best = D; Key = FIntVector(S->Coord.X, S->Coord.Y, I); }
				}
	if (Key.Z < 0) return false;
	DisarmKey = Key; DisarmStart = GetWorld()->GetTimeSeconds(); DisarmFrom = From;
	if (TrapR.GetInitialSeed() == 0) TrapR.Initialize((int32)HashCombine((uint32)SessionSeed, 0x7D15u));      // (RestartPlay seeds it again)
	if (URDCombatComponent* Pc = GetPlayerCombat())
		if (const ARDSection* S = GetSection(FIntPoint(Key.X, Key.Y))) Pc->ShowMessage(FString::Printf(TEXT("Disarming the %s... hold still"), *Traps[S->TrapList[Key.Z].Def].Label));
	return true;
}

float ARDDungeonGenerator::GetDisarmProgress() const
{
	if (DisarmKey.Z < 0 || !GetWorld()) return -1.f;
	return FMath::Clamp((GetWorld()->GetTimeSeconds() - DisarmStart) / FMath::Max(DisarmSeconds, 0.1f), 0.f, 1.f);
}

FString ARDDungeonGenerator::DescribeTrapNear(const FVector& From) const
{
	if (!HeroFindsTraps()) return FString();
	if (DisarmKey.Z >= 0) return FString::Printf(TEXT("disarming...  %.0f%%"), GetDisarmProgress() * 100.f);
	const FIntPoint Here = WorldToSection(From);
	for (int32 Dx = -1; Dx <= 1; ++Dx)
		for (int32 Dy = -1; Dy <= 1; ++Dy)
			if (const ARDSection* S = GetSection(Here + FIntPoint(Dx, Dy)))
				for (const ARDSection::FTrapInst& T : S->TrapList)
					if (T.State == 0 && T.bSeen && FVector::Dist2D(T.At, From) < 280.f) return FString::Printf(TEXT("disarm the %s"), *Traps[T.Def].Label);
	return FString();
}

TArray<FString> ARDDungeonGenerator::GetTrapLines() const
{
	TArray<FString> Out;
	for (const auto& KV : Sections)
		if (const ARDSection* S = KV.Value)
			for (int32 I = 0; I < S->TrapList.Num(); ++I)
			{
				const ARDSection::FTrapInst& T = S->TrapList[I];
				const FRDTrapDef& D = Traps[T.Def];
				Out.Add(FString::Printf(TEXT("%d|%d|%d|%s|%d|%.0f|%.0f|%.0f|%d|%d|%d"), KV.Key.X, KV.Key.Y, I, *D.Name.ToString(), (int32)D.Kind, T.At.X, T.At.Y, T.At.Z, T.State, T.bSeen ? 1 : 0, T.Room));
			}
	return Out;
}

bool ARDDungeonGenerator::TriggerTrap(FIntPoint Section, int32 Index)
{
	ARDSection* S = GetSection(Section);
	return S && S->FireTrap(Index);
}
