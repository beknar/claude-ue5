#include "RD/RDMonster.h"
#include "RD/RDSection.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDCombat.h"
#include "RD/RDBlood.h"
#include "AnimationRuntime.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Rendering/SkeletalMeshLODRenderData.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "Rendering/SkinWeightVertexBuffer.h"
#include "Animation/AnimationAsset.h"
#include "Animation/AnimSequenceBase.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"

ARDMonster::ARDMonster()
{
	PrimaryActorTick.bCanEverTick = true;
	AutoPossessAI = EAutoPossessAI::Disabled;
	AIControllerClass = nullptr;
	bUseControllerRotationYaw = false;
	UCharacterMovementComponent* CM = GetCharacterMovement();
	CM->bRunPhysicsWithNoController = true;
	CM->bOrientRotationToMovement = true;
	CM->RotationRate = FRotator(0, 220, 0);
	CM->MaxWalkSpeed = 140.f;
	CM->MaxAcceleration = 600.f;
	CM->BrakingDecelerationWalking = 600.f;
	GetMesh()->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
	GetMesh()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	GetMesh()->SetAnimationMode(EAnimationMode::AnimationSingleNode);
}

static float RDClipLength(const UAnimationAsset* A)
{
	const UAnimSequenceBase* S = Cast<UAnimSequenceBase>(A);
	return S ? S->GetPlayLength() : 1.f;
}

void ARDMonster::Setup(ARDSection* InSection, const FRDMonsterDef& Def, int32 InSeed)
{
	Section = InSection; MonsterName = Def.Name;
	if (Section && Section->Generator && !Section->Generator->bMonstersBlockPawns)
		GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	R.Initialize(InSeed);
	GetCapsuleComponent()->SetCapsuleSize(Def.CapsuleRadius, Def.CapsuleHalfHeight);
	USkeletalMeshComponent* M = GetMesh();
	M->SetSkeletalMesh(Def.Mesh);
	M->SetRelativeLocationAndRotation(FVector(0, 0, Def.MeshZ), FRotator(0, Def.MeshYaw, 0));
	M->SetRelativeScale3D(FVector(Def.Scale));
	IdleAnim = Def.Idle; WalkAnim = Def.Walk;
	WalkSpeed = Def.WalkSpeed; ClipSpeed = FMath::Max(Def.WalkClipSpeed, 10.f);
	GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
	bWalkingAnim = true; SetWalkingAnim(false);
	M->SetPosition(R.FRandRange(0.f, 2.f));
	WaitTime = R.FRandRange(0.5f, 5.f);
	LastPos = StepPos = GetActorLocation();
	SR.Initialize(InSeed ^ 0x2545f491);
	if (!Def.SoundSet.IsNone())
	{
		auto Key = [&Def](const TCHAR* What) { return FName(*FString::Printf(TEXT("Monster.%s.%s"), *Def.SoundSet.ToString(), What)); };
		SndStep = Key(TEXT("Step")); SndHurt = Key(TEXT("Hurt")); SndRoar = Key(TEXT("Roar")); SndAttack = Key(TEXT("Attack")); SndDeath = Key(TEXT("Death")); SndIdle = Key(TEXT("Idle"));
		StepLength = FMath::Max(Def.StepLength, 15.f);
		VoiceTimer = SR.FRandRange(1.f, 9.f);
	}
	const ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	bCombat = G && G->bCombat;
	if (bCombat)
	{
		for (UAnimationAsset* A : Def.Attacks) if (A) { AttackAnims.Add(A); HitTimes.Add(Def.HitTimes.IsValidIndex(AttackAnims.Num() - 1) ? Def.HitTimes[AttackAnims.Num() - 1] : RDClipLength(A) * 0.45f); }
		GetHitAnim = Def.GetHit; DeathAnim = Def.Death;
		float MeanH = 1.f, MeanD = 1.f; G->MeanMonsterFactors(MeanH, MeanD);
		MaxHealth = Health = FMath::Max(1.f, FMath::RoundToFloat(G->GetMonsterHealth(Section->Coord) * Def.HealthFactor / MeanH));
		Damage = FMath::Max(1.f, FMath::RoundToFloat(G->GetMonsterDamage(Section->Coord) * Def.DamageFactor / MeanD));
		Reach = Def.Reach; AttackInterval = Def.AttackInterval;
		AttackCooldown = R.FRandRange(0.f, 0.6f);
		// (it must keep its pose up to date while she fights it at the edge of the view)
		M->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
	}
#if WITH_EDITOR
	SetActorLabel(FString::Printf(TEXT("RD_Monster_%s"), *Def.Name.ToString()));
	SetFolderPath(TEXT("RandomDungeon/Monsters"));
#endif
}

void ARDMonster::SetWalkingAnim(bool bWalk)
{
	if (bWalk == bWalkingAnim) return;
	bWalkingAnim = bWalk;
	UAnimationAsset* A = bWalk ? WalkAnim.Get() : IdleAnim.Get();
	if (!A) A = IdleAnim ? IdleAnim.Get() : WalkAnim.Get();
	if (A) GetMesh()->PlayAnimation(A, true);
}

FIntPoint ARDMonster::WalkableTileAt(const FVector& L) const
{
	FIntPoint T = Section->WorldToLocal(L);
	// pushed off the walkable tiles (next to furniture): the nearest walkable neighbour
	for (int32 D = 1; D <= 2 && !Section->IsWalkable(T); ++D)
		for (int32 Dx = -D; Dx <= D; ++Dx) for (int32 Dy = -D; Dy <= D; ++Dy)
			if (Section->IsWalkable(T + FIntPoint(Dx, Dy))) { T += FIntPoint(Dx, Dy); Dx = Dy = D + 1; }
	return T;
}

void ARDMonster::SetPathFromTiles(const TArray<FIntPoint>& Tiles)
{
	// straighten: skip tile centres while the straight line stays on walkable tiles of the same room / hallway
	auto Clear = [this](FIntPoint A, FIntPoint B)
	{
		const int32 Ra = Section->RoomAtLocal(A);
		if (Ra != Section->RoomAtLocal(B)) return false;
		if (Ra < 0) return false;
		const FVector Pa = Section->LocalToWorld(A), Pb = Section->LocalToWorld(B);
		const int32 Steps = FMath::CeilToInt(FVector::Dist2D(Pa, Pb) / 40.f);
		for (int32 K = 0; K <= Steps; ++K)
		{
			const FVector P = FMath::Lerp(Pa, Pb, (float)K / FMath::Max(Steps, 1));
			for (const FVector& O : { FVector(45, 45, 0), FVector(-45, 45, 0), FVector(45, -45, 0), FVector(-45, -45, 0) })
			{
				const FIntPoint T = Section->WorldToLocal(P + O);
				if (!Section->IsWalkable(T) || Section->RoomAtLocal(T) != Ra) return false;
			}
		}
		return true;
	};
	Path.Reset();
	int32 I = 0;
	while (I < Tiles.Num() - 1)
	{
		int32 J = Tiles.Num() - 1;
		while (J > I + 1 && !Clear(Tiles[I], Tiles[J])) --J;
		Path.Add(Section->LocalToWorld(Tiles[J]));
		I = J;
	}
}

void ARDMonster::PickTrip()
{
	Path.Reset();
	if (!Section) return;
	const FIntPoint From = WalkableTileAt(GetActorLocation());
	const FIntPoint To = Section->RandomRoomTile(R, Section->RoomAtLocal(From));
	TArray<FIntPoint> Tiles;
	if (!Section->FindPath(From, To, Tiles) || Tiles.Num() < 2) { WaitTime = R.FRandRange(1.f, 3.f); return; }
	SetPathFromTiles(Tiles);
	Goal = Path.Last();
	StuckTime = 0.f;
}

bool ARDMonster::WaitForDoor(const FVector& L, const FVector& Dir2)
{
	const FIntPoint Cur = Section->WorldToLocal(L);
	const FIntPoint Ahead = Section->WorldToLocal(L + Dir2.GetSafeNormal() * 160.f);
	if (Ahead != Cur && FMath::Abs(Ahead.X - Cur.X) + FMath::Abs(Ahead.Y - Cur.Y) == 1)
	{
		const int32 D = Section->DoorBetween(Cur, Ahead);
		if (D >= 0 && !Section->IsDoorOpenIndex(D))
		{
			// (asked by what the door is doing, not by how far it has got: at 240 ticks a second a leaf has not moved a
			// hundredth by the next tick, and the monster pushed and pulled it for ever)
			if (!Section->IsTargetOpen(true, D)) Section->ToggleDoor(D, L, true);
			SetWalkingAnim(false);
			return true;
		}
	}
	return false;
}

void ARDMonster::Face(const FVector& Dir, float Dt)
{
	if (Dir.IsNearlyZero(1.f)) return;
	SetActorRotation(FMath::RInterpConstantTo(GetActorRotation(), FRotator(0.f, Dir.Rotation().Yaw, 0.f), Dt, 420.f));
}

bool ARDMonster::ApplyDamage(float Amount, AActor* From)
{
	return ApplyDamageAt(Amount, From, nullptr);
}

bool ARDMonster::ApplyDamageAt(float Amount, AActor* From, const FVector* At)
{
	if (!bCombat || bDead || Amount <= 0.f) return false;
	Health = FMath::Max(0.f, Health - Amount);
	LastHurtTime = GetWorld()->GetTimeSeconds();
	bAggro = true; WaitTime = 0.f;
	// the wound: where the weapon is nearest to it, on the attacker's side
	ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	const FVector Center = GetActorLocation();
	const FVector FromLoc = From ? From->GetActorLocation() : Center + GetActorForwardVector() * 150.f;
	FVector Strike = FMath::Lerp(FromLoc, Center, 0.7f);
	if (From)
		if (const URDCombatComponent* C = From->FindComponentByClass<URDCombatComponent>())
			if (const UStaticMeshComponent* W = C->GetWeaponMesh())
				if (W->GetStaticMesh()) Strike = W->Bounds.GetBox().GetClosestPointTo(Center);
	if (At) Strike = *At;
	// (drawn toward its trunk on the attacker's side, at a height of its own: a blow that only met a hand or a horn would hardly show)
	const FVector ToFrom = ((FromLoc - Center) * FVector(1, 1, 0)).GetSafeNormal(1e-4f, GetActorForwardVector());
	const FVector Trunk = Center + ToFrom * GetCapsuleComponent()->GetScaledCapsuleRadius() * 0.9f + FVector(0, 0, SR.FRandRange(-0.3f, 0.5f) * GetCapsuleComponent()->GetScaledCapsuleHalfHeight());
	Strike = FMath::Lerp(Strike, Trunk, 0.6f);
	const float Share = Amount / FMath::Max(MaxHealth, 1.f);
	const FVector WoundAt = AddWound(Strike + SR.VRand() * FVector(6.f, 6.f, 10.f), FromLoc, Share);
	if (G)
	{
		if (URDBloodComponent* B = G->GetBlood())
		{
			const FVector Out = ((WoundAt - Center) * FVector(1.f, 1.f, 0.3f)).GetSafeNormal() * 0.6f + ((FromLoc - Center) * FVector(1.f, 1.f, 0.f)).GetSafeNormal() * 0.4f;
			B->Burst(WoundAt, Out, Health <= 0.f ? 1.f : FMath::Clamp(Share * 1.6f, 0.3f, 1.f));
		}
		G->PlaySoundAt(TEXT("Blood.Splat"), WoundAt);
		G->PlaySoundAt(Health <= 0.f ? SndDeath : SndHurt, Center);
		VoiceTimer = FMath::Max(VoiceTimer, 2.5f);
	}
	if (Health <= 0.f) { Die(); return true; }
	// a flinch: the blow it was winding up is lost
	AttackTime = -1.f; AttackCooldown = FMath::Max(AttackCooldown, 0.45f);
	Stun = 0.3f;
	if (GetHitAnim) { GetMesh()->PlayAnimation(GetHitAnim, false); Stun = FMath::Clamp(RDClipLength(GetHitAnim) * 0.6f, 0.25f, 0.55f); }
	return false;
}

void ARDMonster::Die()
{
	bDead = true; bAggro = false; AttackTime = -1.f; Stun = 0.f; DeadTime = 0.f;
	Path.Reset();
	GetCharacterMovement()->StopMovementImmediately();
	GetCharacterMovement()->DisableMovement();
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);       // (the body is no obstacle)
	if (DeathAnim) GetMesh()->PlayAnimation(DeathAnim, false);
	if (Section && Section->Generator) Section->Generator->OnMonsterKilled(this);
}

bool ARDMonster::TickCombat(float Dt)
{
	ARDDungeonGenerator* G = Section->Generator;
	if (bDead)
	{
		// the body lies a while, then sinks into the floor and is gone
		DeadTime += Dt;
		if (!bBodyDown && DeadTime > 0.8f)
		{
			// it is down: the thud, and a pool spreads under it
			bBodyDown = true;
			const FVector Body = GetMesh()->Bounds.Origin;
			G->PlaySoundAt(TEXT("Env.BodyFall"), Body);
			if (URDBloodComponent* B = G->GetBlood()) B->Pool(Body, 150.f + 2.f * GetCapsuleComponent()->GetScaledCapsuleRadius());
		}
		if (DeadTime > G->CorpseSeconds) AddActorWorldOffset(FVector(0, 0, -45.f * Dt));
		if (DeadTime > G->CorpseSeconds + 3.f) { Section->SpawnedMonsters.Remove(this); Destroy(); }
		return true;
	}
	AttackCooldown = FMath::Max(0.f, AttackCooldown - Dt);
	if (Stun > 0.f)
	{
		Stun -= Dt;
		if (Stun <= 0.f) { bWalkingAnim = true; SetWalkingAnim(false); }
		return true;
	}
	URDCombatComponent* Pc = G->GetPlayerCombat();
	const AActor* P = Pc ? Pc->GetOwner() : nullptr;
	if (!P || Pc->IsDead())
	{
		if (bAggro || AttackTime >= 0.f) { bAggro = false; AttackTime = -1.f; Path.Reset(); WaitTime = 1.f; bWalkingAnim = true; SetWalkingAnim(false); GetCharacterMovement()->MaxWalkSpeed = WalkSpeed; }
		return false;
	}
	const FVector L = GetActorLocation(), Pl = P->GetActorLocation();
	FVector D = Pl - L; const float Dz = FMath::Abs(D.Z); D.Z = 0.f;
	const float Dist = D.Size();
	const float Gap = Dist - GetCapsuleComponent()->GetScaledCapsuleRadius() - 36.f;       // (between the two capsules)
	if (AttackTime >= 0.f)
	{
		AttackTime += Dt;
		Face(D, Dt);
		if (!bHitDone && AttackTime >= AttackHit)
		{
			bHitDone = true;
			// the blow lands if she is still in reach and in front of it
			if (Gap <= Reach + 30.f && Dz < 260.f && FVector::DotProduct(D.GetSafeNormal(), GetActorForwardVector()) > 0.3f) { Pc->ApplyDamage(Damage, this); ++HitsLanded; }
		}
		if (AttackTime >= AttackLen) { AttackTime = -1.f; AttackCooldown = AttackInterval; bWalkingAnim = true; SetWalkingAnim(false); }
		return true;
	}
	ChaseTimer -= Dt;
	if (!bAggro)
	{
		// it notices her when she is near and there is a way to her that is not much longer than the straight line
		if (Dist > G->AggroDistance || Dz > 300.f || ChaseTimer > 0.f) return false;
		ChaseTimer = 0.4f;
		TArray<FIntPoint> Tiles;
		const FIntPoint From = WalkableTileAt(L), To = WalkableTileAt(Pl);
		if (From != To && (!Section->FindPath(From, To, Tiles) || Tiles.Num() * G->TileSize > Dist * 2.f + 1200.f)) return false;
		bAggro = true; Path.Reset(); WaitTime = 0.f; ChaseTimer = 0.f; StuckTime = 0.f;
		Roar();
	}
	if (Dist > G->LoseDistance || Dz > 400.f)
	{
		bAggro = false; Path.Reset(); WaitTime = 1.f; GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
		return false;
	}
	if (Gap <= Reach * 0.7f)
	{
		Face(D, Dt);
		if (AttackCooldown <= 0.f && AttackAnims.Num() > 0 && FVector::DotProduct(D.GetSafeNormal(), GetActorForwardVector()) > 0.6f)
		{
			const int32 K = R.RandRange(0, AttackAnims.Num() - 1);
			GetMesh()->PlayAnimation(AttackAnims[K], false);
			AttackLen = RDClipLength(AttackAnims[K]); AttackHit = FMath::Clamp(HitTimes[K], 0.05f, AttackLen); AttackTime = 0.f; bHitDone = false;
			++AttacksMade;
			G->PlaySoundAt(SndAttack, L);
			VoiceTimer = FMath::Max(VoiceTimer, 2.f);
		}
		else SetWalkingAnim(false);
		return true;
	}
	// the chase: over the tile grid to her tile, then straight at her
	if (ChaseTimer <= 0.f || Path.Num() == 0)
	{
		ChaseTimer = 0.35f;
		const FIntPoint From = WalkableTileAt(L), To = WalkableTileAt(Pl);
		TArray<FIntPoint> Tiles;
		Path.Reset();
		if (From == To || FMath::Abs(From.X - To.X) + FMath::Abs(From.Y - To.Y) == 1) Path.Add(Pl);
		else if (Section->FindPath(From, To, Tiles) && Tiles.Num() >= 2) { SetPathFromTiles(Tiles); if (Path.Num() > 0) Path.Last() = Pl; }
		if (Path.Num() == 0) { bAggro = false; WaitTime = 1.f; GetCharacterMovement()->MaxWalkSpeed = WalkSpeed; return false; }
	}
	GetCharacterMovement()->MaxWalkSpeed = FMath::Min(WalkSpeed * G->ChaseSpeedScale, G->MaxChaseSpeed);
	const FVector Dir2 = FVector(Path[0].X - L.X, Path[0].Y - L.Y, 0);
	if (WaitForDoor(L, Dir2)) return true;
	if (Dir2.Size() < 70.f && Path.Num() > 1) { Path.RemoveAt(0); return true; }
	FVector Side = FVector::ZeroVector;
	if (StuckTime > 0.5f) { const FVector Fw = Dir2.GetSafeNormal(); Side = FVector(-Fw.Y, Fw.X, 0) * (((int32)(StuckTime / 0.8f)) % 2 ? 1.f : -1.f); }
	AddMovementInput((Dir2.GetSafeNormal() + Side * 0.9f).GetSafeNormal(), 1.f);
	const float Speed = GetVelocity().Size2D();
	SetWalkingAnim(Speed > 25.f);
	if (bWalkingAnim) GetMesh()->SetPlayRate(FMath::Clamp(Speed / ClipSpeed, 0.4f, 2.2f));
	StuckTime = FVector::Dist2D(L, LastPos) < 30.f * Dt ? StuckTime + Dt : FMath::Max(0.f, StuckTime - Dt);
	LastPos = L;
	if (StuckTime > 3.f) { StuckTime = 0.f; Path.Reset(); }
	return true;
}

void ARDMonster::Tick(float Dt)
{
	Super::Tick(Dt);
	if (!Section) return;
	TickSounds(Dt);
	if (bCombat && TickCombat(Dt)) return;
	if (WaitTime > 0.f)
	{
		WaitTime -= Dt;
		SetWalkingAnim(false);
		if (WaitTime <= 0.f && Path.Num() == 0) PickTrip();
		return;
	}
	if (Path.Num() == 0) { WaitTime = R.FRandRange(2.f, 6.f); return; }
	const FVector L = GetActorLocation();
	const FVector Target = Path[0];
	const FVector Dir2 = FVector(Target.X - L.X, Target.Y - L.Y, 0);
	// a closed door between here and the next waypoint: push it open and wait
	if (WaitForDoor(L, Dir2)) return;
	// the player ahead: step aside toward the wall away from her (hallways are 3 m wide), wait if she is right there
	FVector Side = FVector::ZeroVector;
	if (const AActor* P = Section->Generator ? Section->Generator->GetTrackedActor() : UGameplayStatics::GetPlayerPawn(this, 0))
	{
		const FVector Dp = (P->GetActorLocation() - L) * FVector(1, 1, 0);
		const FVector Fw = Dir2.GetSafeNormal();
		if (!bCombat && Dp.Size() < 400.f && FVector::DotProduct(Dp.GetSafeNormal(), Fw) > 0.2f)
		{
			const FVector Rt(-Fw.Y, Fw.X, 0);
			Side = Rt * (FVector::DotProduct(Dp, Rt) > 0.f ? -1.f : 1.f);
			if (Dp.Size() < 170.f) { AddMovementInput(Side, 0.5f); SetWalkingAnim(GetVelocity().Size2D() > 25.f); StuckTime = 0.f; return; }
		}
	}
	if (Dir2.Size() < 70.f)
	{
		Path.RemoveAt(0);
		if (Path.Num() == 0) { ++TripsDone; WaitTime = R.FRandRange(3.f, 9.f); }
		return;
	}
	// brushing furniture / a barrel in a hallway: slide sideways for a moment (alternating sides per attempt)
	if (StuckTime > 0.5f && Side.IsZero())
	{
		const FVector Fw = Dir2.GetSafeNormal();
		Side = FVector(-Fw.Y, Fw.X, 0) * ((Repaths + (int32)(StuckTime / 0.8f)) % 2 ? 1.f : -1.f);
	}
	AddMovementInput((Dir2.GetSafeNormal() + Side * 0.9f).GetSafeNormal(), Side.IsZero() ? 1.f : 0.7f);
	const float Speed = GetVelocity().Size2D();
	SetWalkingAnim(Speed > 25.f);
	if (bWalkingAnim) GetMesh()->SetPlayRate(FMath::Clamp(Speed / ClipSpeed, 0.4f, 1.6f));
	// stuck (furniture corner, another monster): pick another trip
	StuckTime = FVector::Dist2D(L, LastPos) < 30.f * Dt ? StuckTime + Dt : FMath::Max(0.f, StuckTime - Dt);
	LastPos = L;
	if (StuckTime > 2.5f) { ++Repaths; StuckTime = 0.f; Path.Reset(); WaitTime = R.FRandRange(0.5f, 2.f); }
}

// ------------------------------------------------------------------------------------------------ wounds
FVector ARDMonster::AddWound(const FVector& Strike, const FVector& From, float Share)
{
	USkeletalMeshComponent* M = GetMesh();
	const FVector Center = GetActorLocation();
	const FVector Away = ((Center - From) * FVector(1, 1, 0)).GetSafeNormal(1e-4f, -GetActorForwardVector());
	const float MeshScale = FMath::Max((float)M->GetComponentScale().X, 0.01f);
	FWound Wd;
	Wd.Radius = FMath::Clamp(12.f + 26.f * Share, 14.f, 25.f);
	FVector World = Strike;
	// the vertex nearest to the weapon with the pose as it is now (a spread of the mesh's vertices is enough), rather on
	// the attacker's side and not inside a wound it already has
	const FSkeletalMeshRenderData* RD = M->GetSkeletalMeshRenderData();
	if (RD && RD->LODRenderData.Num() > 0)
	{
		const int32 LODIdx = FMath::Clamp(RD->GetPendingFirstLODIdx(0), 0, RD->LODRenderData.Num() - 1);
		const FSkeletalMeshLODRenderData& LOD = RD->LODRenderData[LODIdx];
		const FPositionVertexBuffer& PB = LOD.StaticVertexBuffers.PositionVertexBuffer;
		FSkinWeightVertexBuffer* SW = M->GetSkinWeightBuffer(LODIdx);
		const int32 Num = (int32)PB.GetNumVertices();
		if (Num > 0 && PB.GetVertexData() && SW && SW->GetNeedsCPUAccess() && (int32)SW->GetNumVertices() == Num)
		{
			TArray<FMatrix44f> RefToLocals;
			M->CacheRefToLocalMatrices(RefToLocals);
			const FTransform Xf = M->GetComponentTransform();
			const int32 Step = FMath::Max(1, Num / 1200);
			float Best = MAX_flt;
			for (int32 V = SR.RandRange(0, Step - 1); V < Num; V += Step)
			{
				const FVector P = Xf.TransformPosition(FVector(USkinnedMeshComponent::GetSkinnedVertexPosition(M, V, LOD, *SW, RefToLocals)));
				float Cost = FVector::Dist(P, Strike) + 0.8f * FVector::DotProduct(P - Center, Away) + 0.5f * FVector::Dist2D(P, Center);
				const FVector3f Ref = PB.VertexPosition(V);
				for (const FWound& O : Wounds) if (FVector3f::Dist(Ref, O.Ref) < O.Radius / MeshScale * 1.3f) Cost += 30.f;
				if (Cost < Best) { Best = Cost; Wd.Vertex = V; Wd.Ref = Ref; World = P; }
			}
		}
	}
	if (Wd.Vertex < 0)
	{
		// (no vertex data to read: the nearest bone, with a wound big enough to reach the skin around it)
		FVector BoneAt = Center;
		Wd.Bone = M->FindClosestBone(Strike, &BoneAt);
		const int32 BI = M->GetBoneIndex(Wd.Bone);
		if (BI != INDEX_NONE && M->GetSkeletalMeshAsset())
			Wd.Ref = FVector3f(FAnimationRuntime::GetComponentSpaceTransformRefPose(M->GetSkeletalMeshAsset()->GetRefSkeleton(), BI).GetLocation());
		Wd.Radius *= 2.2f;
		World = BoneAt;
	}
	if (Wounds.Num() < MaxWounds) Wounds.Add(Wd);
	else
	{
		// it cannot carry more: the nearest wound opens further
		int32 Near = 0;
		for (int32 I = 1; I < Wounds.Num(); ++I) if (FVector3f::Dist(Wounds[I].Ref, Wd.Ref) < FVector3f::Dist(Wounds[Near].Ref, Wd.Ref)) Near = I;
		Wounds[Near].Radius = FMath::Min(Wounds[Near].Radius * 1.15f, 30.f);
		World = GetWoundLocation(Near);
	}
	PushWounds();
	return World;
}

void ARDMonster::PushWounds()
{
	const ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	USkeletalMeshComponent* M = GetMesh();
	if (!WoundMID)
	{
		if (!G || !G->WoundMaterial) return;
		WoundMID = UMaterialInstanceDynamic::Create(G->WoundMaterial, this);
		WoundMID->SetVectorParameterValue(TEXT("Seed"), FLinearColor(SR.FRandRange(0.f, 100.f), SR.FRandRange(0.f, 100.f), SR.FRandRange(0.f, 100.f), 0.f));
		M->SetOverlayMaterial(WoundMID);
	}
	const float MeshScale = FMath::Max((float)M->GetComponentScale().X, 0.01f);
	for (int32 I = 0; I < Wounds.Num(); ++I)
		WoundMID->SetVectorParameterValue(FName(*FString::Printf(TEXT("Wound%d"), I)), FLinearColor(Wounds[I].Ref.X, Wounds[I].Ref.Y, Wounds[I].Ref.Z, Wounds[I].Radius / MeshScale));
	WoundMID->SetScalarParameterValue(TEXT("Bleed"), 1.f - Health / FMath::Max(MaxHealth, 1.f));
}

FVector ARDMonster::GetWoundLocation(int32 Index) const
{
	if (!Wounds.IsValidIndex(Index)) return GetActorLocation();
	const FWound& Wd = Wounds[Index];
	USkeletalMeshComponent* M = GetMesh();
	if (Wd.Vertex < 0) return Wd.Bone.IsNone() ? GetActorLocation() : M->GetBoneLocation(Wd.Bone);
	const FSkeletalMeshRenderData* RD = M->GetSkeletalMeshRenderData();
	if (!RD || RD->LODRenderData.Num() == 0) return GetActorLocation();
	const int32 LODIdx = FMath::Clamp(RD->GetPendingFirstLODIdx(0), 0, RD->LODRenderData.Num() - 1);
	const FSkeletalMeshLODRenderData& LOD = RD->LODRenderData[LODIdx];
	FSkinWeightVertexBuffer* SW = M->GetSkinWeightBuffer(LODIdx);
	if (!SW || Wd.Vertex >= (int32)LOD.StaticVertexBuffers.PositionVertexBuffer.GetNumVertices()) return GetActorLocation();
	return M->GetComponentTransform().TransformPosition(FVector(USkinnedMeshComponent::GetSkinnedVertexPosition(M, Wd.Vertex, LOD, *SW)));
}

// ------------------------------------------------------------------------------------------------ sound
void ARDMonster::Roar()
{
	ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	const float Now = GetWorld()->GetTimeSeconds();
	if (!G || Now - RoarTime < 8.f) return;
	RoarTime = Now;
	G->PlaySoundAt(SndRoar, GetActorLocation());
	VoiceTimer = FMath::Max(VoiceTimer, 3.5f);
}

void ARDMonster::TickSounds(float Dt)
{
	ARDDungeonGenerator* G = Section->Generator;
	if (!G || bDead) return;
	const AActor* P = G->GetTrackedActor();
	if (!P) return;
	const FVector L = GetActorLocation();
	const bool bNear = FVector::DistSquared(L, P->GetActorLocation()) < 3200.f * 3200.f;
	// a footstep for every StepLength of ground it covers
	StepDist += FVector::Dist2D(L, StepPos); StepPos = L;
	if (StepDist >= StepLength)
	{
		StepDist = 0.f;
		if (bNear && !SndStep.IsNone()) G->PlaySoundAt(SndStep, L - FVector(0, 0, GetCapsuleComponent()->GetScaledCapsuleHalfHeight()));
	}
	// its voice now and then: a growl while it wanders, more often on the chase
	VoiceTimer -= Dt;
	if (VoiceTimer <= 0.f)
	{
		VoiceTimer = bAggro ? SR.FRandRange(2.5f, 5.f) : SR.FRandRange(7.f, 15.f);
		if (bNear && !SndIdle.IsNone() && AttackTime < 0.f && Stun <= 0.f) G->PlaySoundAt(SndIdle, L);
	}
	// wounded: it drips, faster the less it has left
	if (Wounds.Num() > 0 && bNear)
	{
		DripTimer -= Dt;
		if (DripTimer <= 0.f)
		{
			DripTimer = SR.FRandRange(0.25f, 0.7f) / FMath::Clamp(1.f - Health / FMath::Max(MaxHealth, 1.f), 0.25f, 1.f);
			if (URDBloodComponent* B = G->GetBlood()) B->Drip(GetWoundLocation(SR.RandRange(0, Wounds.Num() - 1)));
		}
	}
}
