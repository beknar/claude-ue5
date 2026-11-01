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
#include "Camera/PlayerCameraManager.h"

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

float RDClipLength(const UAnimationAsset* A)
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
		float MeanH = 1.f, MeanD = 1.f; G->MeanMonsterFactors(MeanH, MeanD, Section->Coord);
		MaxHealth = Health = FMath::Max(1.f, FMath::RoundToFloat(G->GetMonsterHealth(Section->Coord) * Def.HealthFactor / MeanH));
		Damage = FMath::Max(1.f, FMath::RoundToFloat(G->GetMonsterDamage(Section->Coord) * Def.DamageFactor / MeanD));
		Reach = Def.Reach; AttackInterval = Def.AttackInterval;
		AttackCooldown = R.FRandRange(0.f, 0.6f);
		// (it must keep its pose up to date while she fights it at the edge of the view)
		M->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
		// (level 5: the tier of its rooms makes it faster, quicker to strike, and its ability stronger)
		Tier = G->TierOf(Section->Coord); Ability = Def.Ability; Title = Def.Title;
		if (G->MaxTier > 0)
		{
			SpeedScale = ARDDungeonGenerator::TierValue(G->TierSpeed, Tier, 1.f);
			WalkSpeed *= SpeedScale; GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
			AttackInterval *= ARDDungeonGenerator::TierValue(G->TierAttackInterval, Tier, 1.f);
			AbilityPower = Ability == ERDMonsterAbility::None ? 0.f : ARDDungeonGenerator::TierValue(G->TierAbility, Tier, 1.f);
			MaxChaseScale = SpeedScale;
		}
		SetupRanged(Def);          // (mistward5: its shot, its wait scaled as its blows' interval)
	}
	// (level 5: parts made on its skeleton follow its body; a weapon in its hand)
	for (USkeletalMesh* PartMesh : Def.Parts)
	{
		if (!PartMesh) continue;
		USkeletalMeshComponent* C = NewObject<USkeletalMeshComponent>(this);
		C->SetSkeletalMeshAsset(PartMesh);
		C->SetupAttachment(M);
		C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		C->RegisterComponent();
		C->SetLeaderPoseComponent(M);
	}
	if (Def.WeaponMesh)
	{
		UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
		C->SetStaticMesh(Def.WeaponMesh);
		C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		C->SetupAttachment(M, Def.WeaponBone);
		C->RegisterComponent();
		C->SetRelativeTransform(Def.WeaponGrip);
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
	return ApplyDamageEx(Amount, From, At, true, true);
}

bool ARDMonster::ApplyDamageEx(float Amount, AActor* From, const FVector* At, bool bFlinch, bool bWound)
{
	if (!bCombat || bDead || Amount <= 0.f) return false;
	Amount *= 1.f + GetCurseShare();            // (cursed: it takes more)
	Health = FMath::Max(0.f, Health - Amount);
	LastHurtTime = GetWorld()->GetTimeSeconds();
	bAggro = true; WaitTime = 0.f;
	if (!bWound)
	{
		// (a burn, a cloud: no wound, no flinch; it dies all the same)
		if (Health <= 0.f) { if (Section && Section->Generator) Section->Generator->PlaySoundAt(SndDeath, GetActorLocation()); Die(); return true; }
		return false;
	}
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
	if (!bFlinch) return false;
	// a flinch: the blow it was winding up is lost
	AttackTime = -1.f; AttackCooldown = FMath::Max(AttackCooldown, 0.45f);
	Stun = 0.3f;
	if (GetHitAnim) { GetMesh()->PlayAnimation(GetHitAnim, false); Stun = FMath::Clamp(RDClipLength(GetHitAnim) * 0.6f, 0.25f, 0.55f); }
	return false;
}

void ARDMonster::Die()
{
	bDead = true; bAggro = false; AttackTime = -1.f; Stun = 0.f; DeadTime = 0.f;
	Burns.Reset(); CurrentFoe = nullptr;
	Path.Reset();
	GetCharacterMovement()->StopMovementImmediately();
	GetCharacterMovement()->DisableMovement();
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);       // (the body is no obstacle)
	GetMesh()->SetPlayRate(1.f);
	if (DeathAnim) GetMesh()->PlayAnimation(DeathAnim, false);
	ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	// (level 5: the dead stay; one of her allies falls and is gone, its death long counted)
	bCorpse = G && G->bKeepCorpses && !bAlly;
	if (G && !bAlly) G->OnMonsterKilled(this);
}

// ------------------------------------------------------------------------------------------------ mistward
void ARDMonster::Empower(int32 InTier, float HealthMul, float DamageMul, float ScaleMul, const FString& InTitle)
{
	ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	if (!G || !bCombat) return;
	// (its kind's share of its tier's average, as Setup does for its own section's tier)
	const FRDMonsterDef* Def = G->Monsters.FindByPredicate([this](const FRDMonsterDef& D) { return D.Name == MonsterName; });
	const float Hf = Def ? Def->HealthFactor : 1.f, Df = Def ? Def->DamageFactor : 1.f;
	const float RefH = G->MonsterReferenceHealth > 0.f ? G->MonsterReferenceHealth : G->PlayerMaxHealth;
	const float RefD = G->MonsterReferenceBlow > 0.f ? G->MonsterReferenceBlow : G->GetAverageWeaponDamage();
	float MeanH = 1.f, MeanD = 1.f;
	// (the means of the kinds of that tier: a set of rooms of it)
	const FIntPoint TierSection(FMath::Max(InTier - 1, 0), 0);
	G->MeanMonsterFactors(MeanH, MeanD, TierSection);
	MaxHealth = Health = FMath::Max(1.f, FMath::RoundToFloat(RefH * ARDDungeonGenerator::TierValue(G->TierHealth, InTier, 1.f) * Hf / MeanH * HealthMul));
	Damage = FMath::Max(1.f, FMath::RoundToFloat(RefD * ARDDungeonGenerator::TierValue(G->TierDamage, InTier, 1.f) * Df / MeanD * DamageMul));
	Tier = InTier;
	if (G->MaxTier > 0)
	{
		const float Sp = ARDDungeonGenerator::TierValue(G->TierSpeed, InTier, 1.f);
		WalkSpeed = (Def ? Def->WalkSpeed : WalkSpeed) * Sp; SpeedScale = Sp; MaxChaseScale = Sp;
		GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
		AttackInterval = (Def ? Def->AttackInterval : AttackInterval) * ARDDungeonGenerator::TierValue(G->TierAttackInterval, InTier, 1.f);
		AbilityPower = Ability == ERDMonsterAbility::None ? 0.f : ARDDungeonGenerator::TierValue(G->TierAbility, InTier, 1.f);
	}
	if (Def) SetupRanged(*Def);    // (mistward5: the shot's wait follows the interval just set)
	if (ScaleMul != 1.f)
	{
		// (bigger: its capsule and its mesh, its feet kept on the floor; its reach grows with it)
		UCapsuleComponent* Cap = GetCapsuleComponent();
		const float R0 = Cap->GetUnscaledCapsuleRadius(), H0 = Cap->GetUnscaledCapsuleHalfHeight();
		Cap->SetCapsuleSize(R0 * ScaleMul, H0 * ScaleMul);
		USkeletalMeshComponent* M = GetMesh();
		const FVector Rel = M->GetRelativeLocation();
		M->SetRelativeLocation(FVector(Rel.X, Rel.Y, Rel.Z * ScaleMul));
		M->SetRelativeScale3D(M->GetRelativeScale3D() * ScaleMul);
		AddActorWorldOffset(FVector(0, 0, H0 * (ScaleMul - 1.f) + 2.f));
		Reach *= ScaleMul;
	}
	if (!InTitle.IsEmpty()) Title = InTitle;
}

void ARDMonster::Release(const FVector& Doorway, const FVector& Exit)
{
	if (!bCaged) return;
	// (out of its cell it comes for her at once: noticing her needs a tile path, and from inside its cell there was none,
	// so a freed monster stood in the open cell)
	bCaged = false; bAggro = true; Path.Reset(); ChaseTimer = 0.f; WaitTime = 0.f; StuckTime = 0.f;
	// (the tile path from inside its cell to her may not exist: it walks out through the door first)
	CellDoorway = Doorway; CellExit = Exit; ReleasedUntil = GetWorld() ? GetWorld()->GetTimeSeconds() + 8.f : -1.f;
	Roar();
}

float ARDMonster::GetDrawnBottom(float Percentile, bool bBodyOnly) const
{
	// (its skinned vertices as drawn now, a spread of them: its body's (or with the parts made on its skeleton: a weapon
	// part's tip on the floor would lift a whole orc); the Percentile-th lowest of them, not the lowest: a tail or a strap
	// dragging is not where it stands)
	TArray<float> Zs;
	TInlineComponentArray<USkeletalMeshComponent*> Ms(this);
	for (USkeletalMeshComponent* M : Ms)
	{
		if (bBodyOnly && M != GetMesh()) continue;
		const FSkeletalMeshRenderData* RD = M ? M->GetSkeletalMeshRenderData() : nullptr;
		if (!RD || RD->LODRenderData.Num() == 0) continue;
		const int32 LODIdx = FMath::Clamp(RD->GetPendingFirstLODIdx(0), 0, RD->LODRenderData.Num() - 1);
		const FSkeletalMeshLODRenderData& LOD = RD->LODRenderData[LODIdx];
		const FPositionVertexBuffer& PB = LOD.StaticVertexBuffers.PositionVertexBuffer;
		FSkinWeightVertexBuffer* SW = M->GetSkinWeightBuffer(LODIdx);
		const int32 Num = (int32)PB.GetNumVertices();
		if (Num <= 0 || !PB.GetVertexData() || !SW || !SW->GetNeedsCPUAccess() || (int32)SW->GetNumVertices() != Num) continue;
		TArray<FMatrix44f> RefToLocals;
		M->CacheRefToLocalMatrices(RefToLocals);
		const FTransform Xf = M->GetComponentTransform();
		const int32 Step = FMath::Max(1, Num / 6000);
		for (int32 V = 0; V < Num; V += Step)
			Zs.Add((float)Xf.TransformPosition(FVector(USkinnedMeshComponent::GetSkinnedVertexPosition(M, V, LOD, *SW, RefToLocals))).Z);
	}
	if (Zs.Num() == 0) return 0.f;
	Zs.Sort();
	const float Lo = Zs[FMath::Clamp(FMath::FloorToInt32(Percentile * (Zs.Num() - 1)), 0, Zs.Num() - 1)];
	return Lo - (GetActorLocation().Z - GetCapsuleComponent()->GetScaledCapsuleHalfHeight());
}

// ------------------------------------------------------------------------------------------------ level 5: corpses, allies, the spells' hold
void ARDMonster::LayDead()
{
	bDead = true; bCorpse = true; bBodyDown = true; bAggro = false; Health = 0.f;
	GetCharacterMovement()->StopMovementImmediately();
	GetCharacterMovement()->DisableMovement();
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (DeathAnim) { GetMesh()->PlayAnimation(DeathAnim, false); GetMesh()->SetPosition(RDClipLength(DeathAnim)); }
	// (it is frozen a moment later, once its pose at the clip's end has been taken)
	bFrozen = false; DeadTime = 0.f; FreezeAt = 0.25f;
}

void ARDMonster::Freeze()
{
	// (a corpse costs nothing: its pose held, no ticking)
	bFrozen = true;
	GetMesh()->bPauseAnims = true;
	GetMesh()->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
	SetActorTickEnabled(false);
}

void ARDMonster::BecomeAlly(float Seconds, float InHealth, float InDamage)
{
	const bool bRise = bDead;
	bAlly = true; bDead = false; bCorpse = false; bFrozen = false; bBodyDown = false;
	MaxHealth = Health = FMath::Max(1.f, InHealth); Damage = FMath::Max(1.f, InDamage);
	AllySeconds = Seconds; AllyLeft = Seconds;
	bAggro = false; AttackTime = -1.f; Path.Reset(); DeadTime = 0.f; CurrentFoe = nullptr; Burns.Reset(); SlowUntil = CurseUntil = -100.f;
	SetActorTickEnabled(true);
	USkeletalMeshComponent* M = GetMesh();
	M->bPauseAnims = false;
	M->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	// (she walks through her allies, and they through each other and the monsters)
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	// (and her camera passes them: one behind her pulled it into her back)
	TArray<UPrimitiveComponent*> Prims; GetComponents<UPrimitiveComponent>(Prims);
	for (UPrimitiveComponent* P : Prims) if (P) P->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
	GetCharacterMovement()->SetMovementMode(MOVE_Walking);
	GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
	if (bRise && DeathAnim)
	{
		// (a corpse rises: its death clip played backward)
		const float L = RDClipLength(DeathAnim);
		M->PlayAnimation(DeathAnim, false); M->SetPosition(L); M->SetPlayRate(-1.4f);
		Stun = L / 1.4f;
	}
	else { bWalkingAnim = true; SetWalkingAnim(false); }
}

float ARDMonster::GetSlowShare() const
{
	const UWorld* W = GetWorld();
	return W && W->GetTimeSeconds() < SlowUntil ? SlowShare : 0.f;
}

float ARDMonster::GetCurseShare() const
{
	const UWorld* W = GetWorld();
	return W && W->GetTimeSeconds() < CurseUntil ? CurseShare : 0.f;
}

void ARDMonster::SlowFor(float Share, float Seconds)
{
	if (bDead) return;
	const float Now = GetWorld()->GetTimeSeconds();
	SlowShare = Now < SlowUntil ? FMath::Max(SlowShare, Share) : Share;
	SlowUntil = FMath::Max(SlowUntil, Now + Seconds);
}

void ARDMonster::CurseFor(float Share, float Seconds)
{
	if (bDead) return;
	const float Now = GetWorld()->GetTimeSeconds();
	CurseShare = Now < CurseUntil ? FMath::Max(CurseShare, Share) : Share;
	CurseUntil = FMath::Max(CurseUntil, Now + Seconds);
}

void ARDMonster::AddBurn(float PerSecond, float Seconds, float DrainShare)
{
	if (bDead || PerSecond <= 0.f || Seconds <= 0.f) return;
	Burns.Add({ PerSecond, Seconds, DrainShare });
}

void ARDMonster::BlindFor(float Share, float Seconds)
{
	if (bDead) return;
	const float Now = GetWorld()->GetTimeSeconds();
	BlindShare = Now < BlindUntil ? FMath::Max(BlindShare, Share) : Share;
	BlindUntil = FMath::Max(BlindUntil, Now + Seconds);
}

float ARDMonster::GetBlindShare() const
{
	const UWorld* W = GetWorld();
	return W && W->GetTimeSeconds() < BlindUntil ? BlindShare : 0.f;
}

void ARDMonster::StunFor(float Seconds)
{
	if (bDead || Seconds <= 0.f) return;
	// (held where it stands: its swing broken off, its flinch played)
	AttackTime = -1.f; Stun = FMath::Max(Stun, Seconds); bStunHeld = true;
	if (GetHitAnim) GetMesh()->PlayAnimation(GetHitAnim, false);
	GetCharacterMovement()->StopMovementImmediately();
}

void ARDMonster::Knock(const FVector& Velocity)
{
	if (bDead) return;
	LaunchCharacter(Velocity + FVector(0, 0, 160.f), true, true);
	AttackTime = -1.f; Stun = FMath::Max(Stun, 0.45f);
}

void ARDMonster::PullToward(const FVector& To, float Speed, float Dt)
{
	if (bDead) return;
	const FVector D = (To - GetActorLocation()) * FVector(1, 1, 0);
	if (D.Size() < 60.f) return;
	AddActorWorldOffset(D.GetSafeNormal() * FMath::Min(Speed * Dt, D.Size() - 50.f), true);
}

void ARDMonster::TickStatus(float Dt)
{
	if (bDead || Burns.Num() == 0) return;
	// (burns: their hurt a second, counted out every half second; a share of it goes back to her)
	ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	URDCombatComponent* Pc = G ? G->GetPlayerCombat() : nullptr;
	float Drain = 0.f;
	for (int32 I = Burns.Num() - 1; I >= 0; --I)
	{
		FBurn& B = Burns[I];
		const float T = FMath::Min(Dt, B.Left);
		BurnAcc += B.PerSecond * T; Drain += B.PerSecond * T * B.Drain;
		if ((B.Left -= Dt) <= 0.f) Burns.RemoveAt(I);
	}
	if (Pc && Drain > 0.f) Pc->HealBy(Drain);
	BurnTick -= Dt;
	if (BurnTick <= 0.f || Burns.Num() == 0)
	{
		BurnTick = 0.5f;
		const float A = BurnAcc; BurnAcc = 0.f;
		if (A > 0.f)
		{
			AActor* From = Pc ? Pc->GetOwner() : nullptr;
			if (G) G->AddHitText(GetActorLocation() + FVector(0, 0, GetCapsuleComponent()->GetScaledCapsuleHalfHeight()), A, false);
			if (Pc) Pc->CountSpellDamage(A);
			if (ApplyDamageEx(A, From, nullptr, false, false) && Pc) ++Pc->Kills;
		}
	}
}

AActor* ARDMonster::PickFoe(URDCombatComponent* Pc, bool& bFoePlayer) const
{
	bFoePlayer = false;
	ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	if (!G) return nullptr;
	const FVector L = GetActorLocation();
	AActor* Best = nullptr; float BestD = 0.f;
	if (bAlly)
	{
		// (her ally: the nearest monster within reach of its senses that is not far from her)
		const AActor* Her = Pc ? Pc->GetOwner() : nullptr;
		BestD = G->AggroDistance * 0.9f;
		for (ARDMonster* Mo : G->GetMonsters())
		{
			if (!Mo || Mo->IsDead() || FMath::Abs(Mo->GetActorLocation().Z - L.Z) > 300.f) continue;
			if (Her && FVector::Dist2D(Mo->GetActorLocation(), Her->GetActorLocation()) > 1800.f) continue;
			const float D = FVector::Dist2D(Mo->GetActorLocation(), L);
			if (D < BestD) { BestD = D; Best = Mo; }
		}
		return Best;
	}
	// (a monster: her, unless she is veiled; or one of her allies nearer)
	if (Pc && Pc->GetOwner() && !Pc->IsDead() && !Pc->IsVeiled())
	{
		Best = Pc->GetOwner(); bFoePlayer = true;
		BestD = FVector::Dist2D(Best->GetActorLocation(), L);
	}
	for (ARDMonster* A : G->GetAllies())
	{
		const float D = FVector::Dist2D(A->GetActorLocation(), L);
		if (D > G->AggroDistance || FMath::Abs(A->GetActorLocation().Z - L.Z) > 300.f) continue;
		if (!Best || D < BestD * 0.85f) { Best = A; BestD = D; bFoePlayer = false; }
	}
	return Best;
}

bool ARDMonster::FollowPlayer(float Dt, URDCombatComponent* Pc)
{
	const AActor* Her = Pc ? Pc->GetOwner() : nullptr;
	CurrentFoe = nullptr;
	if (!Her) { SetWalkingAnim(false); return true; }
	ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	const FVector L = GetActorLocation(), Hl = Her->GetActorLocation();
	const float Dist = FVector::Dist2D(L, Hl);
	// (left far behind, or on another floor: it comes to her side, left or right of her (behind her is where her camera
	// is), the side with room)
	if (Dist > 2600.f || FMath::Abs(Hl.Z - L.Z) > 500.f)
	{
		const float Sgn = (GetUniqueID() & 1) ? 1.f : -1.f;
		FVector Side = Hl + Her->GetActorRightVector() * (240.f * Sgn) - Her->GetActorForwardVector() * 40.f;
		// (mistward4: to a spot no other ally stands on: all of one side came to the same one; toward her front first)
		if (G && G->bAllySpacing)
		{
			FVector Spot;
			if (G->FindAllySpot(Hl, Her->GetActorRightVector() * Sgn, GetCapsuleComponent()->GetScaledCapsuleRadius(), this, Spot, Her->GetActorForwardVector()))
			{
				SetActorLocation(Spot + FVector(0, 0, GetCapsuleComponent()->GetScaledCapsuleHalfHeight() - 80.f), false, nullptr, ETeleportType::TeleportPhysics);
				Path.Reset();
				return true;
			}
		}
		FHitResult Hh; FCollisionQueryParams Qp(SCENE_QUERY_STAT(RDAllySide), false, this); Qp.AddIgnoredActor(Her);
		if (GetWorld()->SweepSingleByChannel(Hh, Hl, Side, FQuat::Identity, ECC_Visibility, FCollisionShape::MakeSphere(45.f), Qp))
		{
			const FVector Other = Hl - Her->GetActorRightVector() * (240.f * Sgn) - Her->GetActorForwardVector() * 40.f;
			FHitResult H2;
			Side = GetWorld()->SweepSingleByChannel(H2, Hl, Other, FQuat::Identity, ECC_Visibility, FCollisionShape::MakeSphere(45.f), Qp)
				? Hl + Her->GetActorForwardVector() * 200.f : Other;
		}
		SetActorLocation(Side + FVector(0, 0, GetCapsuleComponent()->GetScaledCapsuleHalfHeight() - 80.f), false, nullptr, ETeleportType::TeleportPhysics);
		Path.Reset();
		return true;
	}
	// (by her: it waits; mistward4: stepping out of another ally, or out of her, first)
	const FVector Push = AllySpacingPush();
	if (Dist < 380.f)
	{
		Path.Reset();
		if (Push.Size() > 0.05f)
		{
			GetCharacterMovement()->MaxWalkSpeed = WalkSpeed * SpeedMul();
			AddMovementInput(Push.GetSafeNormal(), FMath::Clamp(Push.Size() * 1.5f, 0.35f, 1.f));
			SetWalkingAnim(GetVelocity().Size2D() > 25.f);
		}
		else SetWalkingAnim(false);
		return true;
	}
	GetCharacterMovement()->MaxWalkSpeed = FMath::Min(WalkSpeed * (G ? G->ChaseSpeedScale : 1.5f), 330.f) * SpeedMul();
	ChaseTimer -= Dt;
	if (ChaseTimer <= 0.f || Path.Num() == 0)
	{
		ChaseTimer = 0.5f;
		TArray<FIntPoint> Tiles; Path.Reset();
		const FIntPoint From = WalkableTileAt(L), To = WalkableTileAt(Hl);
		if (Section && Section->FindPath(From, To, Tiles) && Tiles.Num() >= 2) SetPathFromTiles(Tiles);
		if (Path.Num() == 0) Path.Add(Hl);
	}
	const FVector Dir2 = FVector(Path[0].X - L.X, Path[0].Y - L.Y, 0);
	if (WaitForDoor(L, Dir2)) return true;
	if (Dir2.Size() < 70.f && Path.Num() > 1) { Path.RemoveAt(0); return true; }
	AddMovementInput(AllySteer(Dir2), 1.f);
	const float Speed = GetVelocity().Size2D();
	SetWalkingAnim(Speed > 25.f);
	if (bWalkingAnim) GetMesh()->SetPlayRate(FMath::Clamp(Speed / ClipSpeed, 0.4f, 2.2f));
	return true;
}

bool ARDMonster::TickCombat(float Dt)
{
	ARDDungeonGenerator* G = Section->Generator;
	TickStatus(Dt);
	if (bDead)
	{
		// the body lies a while, then sinks into the floor and is gone (level 5: it stays; an ally of hers is gone)
		DeadTime += Dt;
		if (!bBodyDown && DeadTime > 0.8f)
		{
			// it is down: the thud, and a pool spreads under it
			bBodyDown = true;
			const FVector Body = GetMesh()->Bounds.Origin;
			G->PlaySoundAt(TEXT("Env.BodyFall"), Body);
			if (URDBloodComponent* B = G->GetBlood()) B->Pool(Body, 150.f + 2.f * GetCapsuleComponent()->GetScaledCapsuleRadius());
		}
		if (bAlly) { if (DeadTime > 2.5f) G->ConsumeCorpse(this); return true; }
		if (bCorpse)
		{
			// (frozen once its death clip has played; one laid dead at once, a moment after)
			if (!bFrozen && DeadTime > (FreezeAt > 0.f ? FreezeAt : (DeathAnim ? RDClipLength(DeathAnim) + 0.3f : 1.f))) Freeze();
			return true;
		}
		if (DeadTime > G->CorpseSeconds) AddActorWorldOffset(FVector(0, 0, -45.f * Dt));
		if (DeadTime > G->CorpseSeconds + 3.f) { Section->SpawnedMonsters.Remove(this); Destroy(); }
		return true;
	}
	// (her ally: its time runs out, and it falls)
	if (bAlly && AllySeconds > 0.f && (AllyLeft -= Dt) <= 0.f) { Health = 0.f; Die(); return true; }
	AttackCooldown = FMath::Max(0.f, AttackCooldown - Dt);
	RangedWaitLeft = FMath::Max(0.f, RangedWaitLeft - Dt);
	if (Stun > 0.f)
	{
		Stun -= Dt;
		if (Stun <= 0.f) { bStunHeld = false; bWalkingAnim = true; GetMesh()->SetPlayRate(1.f); SetWalkingAnim(false); }
		return true;
	}
	URDCombatComponent* Pc = G->GetPlayerCombat();
	// (mistward: locked in its cell, it waits)
	if (bCaged) { SetWalkingAnim(false); return true; }
	// the one it fights (level 5: her or her allies; her ally fights the monsters)
	bool bFoePlayer = false;
	AActor* P = AttackTime >= 0.f && CurrentFoe.IsValid() ? CurrentFoe.Get() : PickFoe(Pc, bFoePlayer);
	if (AttackTime >= 0.f && P) bFoePlayer = Pc && P == Pc->GetOwner();
	if (const ARDMonster* Fm = Cast<ARDMonster>(P); Fm && Fm->IsDead()) P = nullptr;
	if (!P || (bFoePlayer && Pc->IsDead()))
	{
		CurrentFoe = nullptr;
		if (bAlly) return FollowPlayer(Dt, Pc);
		if (bAggro || AttackTime >= 0.f) { bAggro = false; AttackTime = -1.f; Path.Reset(); WaitTime = 1.f; bWalkingAnim = true; SetWalkingAnim(false); GetCharacterMovement()->MaxWalkSpeed = WalkSpeed * SpeedMul(); }
		return false;
	}
	const FVector L = GetActorLocation(), Pl = P->GetActorLocation();
	FVector D = Pl - L; const float Dz = FMath::Abs(D.Z); D.Z = 0.f;
	const float Dist = D.Size();
	const ARDMonster* FoeMo = Cast<ARDMonster>(P);
	const float FoeRad = FoeMo ? FoeMo->GetCapsuleComponent()->GetScaledCapsuleRadius() : 36.f;
	const float Gap = Dist - GetCapsuleComponent()->GetScaledCapsuleRadius() - FoeRad;       // (between the two capsules)
	if (AttackTime >= 0.f)
	{
		AttackTime += Dt;
		Face(D, Dt);
		if (!bHitDone && AttackTime >= AttackHit && bRangedSwing)
		{
			// (mistward5: its shot leaves its hand; the generator flies it)
			bHitDone = true;
			ReleaseShot(P);
		}
		else if (!bHitDone && AttackTime >= AttackHit)
		{
			bHitDone = true;
			// the blow lands if its foe is still in reach and in front of it (a curse on it: weaker)
			// (the third list: a blinded monster's blow misses its share of the time; the roll a hash of its swings, never a
			// stream the play draws from)
			const float Blind = GetBlindShare();
			const bool bMissBlind = Blind > 0.f && (float)(HashCombine(GetUniqueID(), (uint32)(++Swings * 2654435761u)) % 10000u) / 10000.f < Blind;
			if (bMissBlind) ++BlindMisses;
			if (!bMissBlind && Gap <= Reach + 30.f && Dz < 260.f && FVector::DotProduct(D.GetSafeNormal(), GetActorForwardVector()) > 0.3f)
			{
				const float Dmg = Damage * (1.f - GetCurseShare());
				if (bFoePlayer) { Pc->ApplyDamage(Dmg, this); if (Ability != ERDMonsterAbility::None) Pc->ApplyMonsterAbility(Ability, AbilityPower, Dmg); }
				else if (ARDMonster* Fm = Cast<ARDMonster>(P)) { Fm->ApplyDamageAt(Dmg, this, nullptr); G->AddHitText(Fm->GetActorLocation() + FVector(0, 0, Fm->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()), Dmg, false); }
				++HitsLanded;
			}
		}
		if (AttackTime >= AttackLen)
		{
			// (a shot: its own longer wait; its blows may follow at once when its foe closes in)
			if (bRangedSwing) { RangedWaitLeft = RangedWait; bRangedSwing = false; }
			else AttackCooldown = AttackInterval;
			AttackTime = -1.f; bWalkingAnim = true; SetWalkingAnim(false);
		}
		return true;
	}
	ChaseTimer -= Dt;
	const bool bSameSection = !FoeMo || FoeMo->Section == Section;
	if (!bAggro && !bAlly)
	{
		// it notices its foe when it is near and there is a way to it that is not much longer than the straight line
		if (Dist > G->AggroDistance || Dz > 300.f || ChaseTimer > 0.f) return false;
		ChaseTimer = 0.4f;
		TArray<FIntPoint> Tiles;
		const FIntPoint From = WalkableTileAt(L), To = WalkableTileAt(Pl);
		if (bSameSection && From != To && (!Section->FindPath(From, To, Tiles) || Tiles.Num() * G->TileSize > Dist * 2.f + 1200.f)) return false;
		if (!bSameSection && Dist > G->AggroDistance * 0.6f) return false;
		bAggro = true; Path.Reset(); WaitTime = 0.f; ChaseTimer = 0.f; StuckTime = 0.f;
		Roar();
	}
	bAggro = true;
	CurrentFoe = P;
	if (Dist > G->LoseDistance || Dz > 400.f)
	{
		bAggro = false; Path.Reset(); WaitTime = 1.f; GetCharacterMovement()->MaxWalkSpeed = WalkSpeed * SpeedMul(); CurrentFoe = nullptr;
		return bAlly ? FollowPlayer(Dt, Pc) : false;
	}
	if (Gap <= Reach * 0.7f)
	{
		Face(D, Dt);
		if (AttackCooldown <= 0.f && AttackAnims.Num() > 0 && FVector::DotProduct(D.GetSafeNormal(), GetActorForwardVector()) > 0.6f)
		{
			const int32 K = R.RandRange(0, AttackAnims.Num() - 1);
			GetMesh()->PlayAnimation(AttackAnims[K], false);
			AttackLen = RDClipLength(AttackAnims[K]); AttackHit = FMath::Clamp(HitTimes[K], 0.05f, AttackLen); AttackTime = 0.f; bHitDone = false;
			bRangedSwing = false;         // (a shot cut short by a flinch or a stun must not make this blow a shot)
			++AttacksMade;
			G->PlaySoundAt(SndAttack, L);
			VoiceTimer = FMath::Max(VoiceTimer, 2.f);
		}
		else if (const FVector Push = AllySpacingPush(); Push.Size() > 0.15f)
		{
			// (mistward4: her ally in another one at the foe: a step aside, round the foe, still facing it)
			AddMovementInput(Push.GetSafeNormal(), 0.6f);
			SetWalkingAnim(GetVelocity().Size2D() > 25.f);
		}
		else SetWalkingAnim(false);
		return true;
	}
	// (mistward5: out of reach of its blows, in its range, with a sight line: it stands and shoots)
	if (bShoots && G->bMonsterRanged && CellExit.IsZero() && TryShoot(P, D, Dist, Dz, Gap, Dt)) return true;
	// (mistward: just out of its cell: through its door first, then at her)
	// (the middle of a cell's front is where its bars meet its door: straight from the cell's middle to the exit it walked
	// into the bars and stuck there; it goes to the door's gap first)
	if (!CellExit.IsZero())
	{
		const bool bLate = GetWorld()->GetTimeSeconds() > ReleasedUntil;
		if (!CellDoorway.IsZero() && (bLate || FVector::Dist2D(L, CellDoorway) < 75.f)) CellDoorway = FVector::ZeroVector;
		if (FVector::Dist2D(L, CellExit) < 90.f || bLate) CellExit = FVector::ZeroVector;
		else { Path.Reset(); if (!CellDoorway.IsZero()) Path.Add(CellDoorway); Path.Add(CellExit); Path.Add(Pl); ChaseTimer = 0.35f; }
	}
	// the chase: over the tile grid to its foe's tile, then straight at it (across a section's border: straight)
	if (ChaseTimer <= 0.f || Path.Num() == 0)
	{
		ChaseTimer = 0.35f;
		const FIntPoint From = WalkableTileAt(L), To = WalkableTileAt(Pl);
		TArray<FIntPoint> Tiles;
		Path.Reset();
		if (From == To || FMath::Abs(From.X - To.X) + FMath::Abs(From.Y - To.Y) == 1) Path.Add(Pl);
		else if (bSameSection && Section->FindPath(From, To, Tiles) && Tiles.Num() >= 2) { SetPathFromTiles(Tiles); if (Path.Num() > 0) Path.Last() = Pl; }
		else if (!bSameSection && Dist < 900.f) Path.Add(Pl);
		if (Path.Num() == 0)
		{
			bAggro = false; WaitTime = 1.f; GetCharacterMovement()->MaxWalkSpeed = WalkSpeed * SpeedMul(); CurrentFoe = nullptr;
			return bAlly ? FollowPlayer(Dt, Pc) : false;
		}
	}
	GetCharacterMovement()->MaxWalkSpeed = FMath::Min(WalkSpeed * G->ChaseSpeedScale, G->MaxChaseSpeed * MaxChaseScale) * SpeedMul();
	const FVector Dir2 = FVector(Path[0].X - L.X, Path[0].Y - L.Y, 0);
	if (WaitForDoor(L, Dir2)) return true;
	if (Dir2.Size() < 70.f && Path.Num() > 1) { Path.RemoveAt(0); return true; }
	FVector Side = FVector::ZeroVector;
	if (StuckTime > 0.5f) { const FVector Fw = Dir2.GetSafeNormal(); Side = FVector(-Fw.Y, Fw.X, 0) * (((int32)(StuckTime / 0.8f)) % 2 ? 1.f : -1.f); }
	// (mistward4: her allies chasing one monster keep apart, and come at it from either side)
	AddMovementInput(bAlly ? AllySteer(Dir2.GetSafeNormal() + Side * 0.9f) : (Dir2.GetSafeNormal() + Side * 0.9f).GetSafeNormal(), 1.f);
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
	if (bAlly)
	{
		// (an ally the player's camera is in, or nearly: hidden while it is, so it never fills the view)
		const APlayerCameraManager* Cm = UGameplayStatics::GetPlayerCameraManager(this, 0);
		if (Cm)
		{
			const UCapsuleComponent* Cap = GetCapsuleComponent();
			const float Cr = Cap->GetScaledCapsuleRadius(), Ch = Cap->GetScaledCapsuleHalfHeight();
			const FVector Cc = GetActorLocation(), A0 = Cc - FVector(0, 0, Ch), A1 = Cc + FVector(0, 0, Ch);
			const float Cd = FMath::PointDistToSegment(Cm->GetCameraLocation(), A0, A1);
			const bool bHide = Cd < Cr + 70.f;
			if (bHide != IsHidden()) SetActorHiddenInGame(bHide);
		}
	}
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
	GetCharacterMovement()->MaxWalkSpeed = WalkSpeed * SpeedMul();      // (level 5: a spell may slow it)
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
			// (a monster spawned this frame has no bone matrices yet: the skinning read past the empty array (a test's arrow
			// struck one): the nearest bone below instead)
			// (a body that follows a leader pose reads the leader's bones through its bone map, which is made on its first tick:
			// empty before it, read past too)
			const bool bPose = RefToLocals.Num() > 0 && RefToLocals.Num() >= M->GetNumBones() && (!M->LeaderPoseComponent.IsValid() || M->GetLeaderBoneMap().Num() > 0)
				&& M->GetNumComponentSpaceTransforms() > 0;
			for (int32 V = SR.RandRange(0, Step - 1); bPose && V < Num; V += Step)
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
