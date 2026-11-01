// mistward_castle, the list of 2026-10-31b (docs/improvements5.txt; pipeline/unreal/879). Each rule a switch on the
// generator ("Mistward5" category), off on the other levels:
//   monster ranged   half the kinds shoot from afar in their own theme (FRDMonsterDef's Ranged*): weaker than their blows,
//                    with a longer wait; the shots fly here, strike her, her allies, monsters (an ally's) and walls
//   name-only bars   a monster's bar shows its name only (RDHUD.cpp)
//   arena lock       no way out of an arena while it is fought (doors, the ring, the pads; put back inside)
//   arena crowd      townsfolk appear along its walls before the first wave, cheer at a wave, clap and cheer at a kill
//   autoplay         the game plays her hero for a while (-Autoplay=<seconds>, the menu's AUTOPLAY)
//   ceiling styles   rooms' ceilings raised, beamed, domed and vaulted (ARDSection)
#include "RD/RDMistward5.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDCombat.h"
#include "RD/RDMonster.h"
#include "RD/RDSection.h"
#include "RD/RDMistward.h"
#include "Animation/AnimationAsset.h"
#include "Animation/AnimSequenceBase.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Materials/MaterialInterface.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "NiagaraComponent.h"
#include "Particles/ParticleSystemComponent.h"
#include "ProceduralMeshComponent.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDMistward5, Log, All);

static constexpr float RD5ShotRadius = 55.f;       // (a shot strikes within this of its way, as a trap's dart)


// ================================================================================================ a monster's shot
void ARDMonster::SetupRanged(const FRDMonsterDef& Def)
{
	const ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	bShoots = Def.bShoots && G && G->bMonsterRanged;
	if (!bShoots) return;
	RangedRange = Def.RangedRange; RangedMin = Def.RangedMin; RangedShare = Def.RangedDamage; RangedSpeed = FMath::Max(Def.RangedSpeed, 200.f);
	RangedRelease = FMath::Clamp(Def.RangedRelease, 0.05f, 0.95f); RangedFxScale = Def.RangedFxScale;
	RangedClip = Def.RangedClip ? Def.RangedClip.Get() : (AttackAnims.Num() > 0 ? AttackAnims[0].Get() : nullptr);
	RangedFx = Def.RangedFx; RangedMuzzleFx = Def.RangedMuzzleFx; RangedHitFx = Def.RangedHitFx; RangedTheme = Def.RangedTheme;
	// (its wait scales as its blows' interval does with its tier: always longer than theirs by its kind's own ratio)
	RangedWait = Def.RangedCooldown * (Def.AttackInterval > 0.f ? AttackInterval / Def.AttackInterval : 1.f);
	const uint32 H = HashCombine(GetTypeHash(Def.Name), GetTypeHash(FIntPoint(FMath::RoundToInt(GetActorLocation().X), FMath::RoundToInt(GetActorLocation().Y))));
	RangedWaitLeft = FMath::Max(RangedWaitLeft, 0.5f + (float)(H % 1000u) / 1000.f);
}

float ARDMonster::GetShotDamage() const
{
	return bShoots ? Damage * RangedShare * (1.f - GetCurseShare()) : 0.f;
}

FVector ARDMonster::ShotMuzzle() const
{
	const UCapsuleComponent* Cap = GetCapsuleComponent();
	return GetActorLocation() + GetActorForwardVector() * (Cap->GetScaledCapsuleRadius() + 20.f) + FVector(0, 0, Cap->GetScaledCapsuleHalfHeight() * 0.45f);
}

bool ARDMonster::TryShoot(AActor* P, const FVector& D, float Dist, float Dz, float Gap, float Dt)
{
	if (!P || RangedWaitLeft > 0.f || AttackCooldown > 0.f || !RangedClip) return false;
	// (out of its blows' reach, in its range, not far above or below)
	if (Gap <= Reach * 1.5f || Dist < RangedMin || Dist > RangedRange || Dz > 250.f) return false;
	// (a sight line from its hand to its foe's chest: walls, doors and furniture stop it; pawns do not)
	const FVector From = ShotMuzzle();
	const FVector To = P->GetActorLocation() + FVector(0, 0, 20.f);
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDShotSight), false, this); Q.AddIgnoredActor(P);
	FCollisionObjectQueryParams O; O.AddObjectTypesToQuery(ECC_WorldStatic); O.AddObjectTypesToQuery(ECC_WorldDynamic);
	if (GetWorld()->LineTraceTestByObjectType(From, To, O, Q)) return false;
	Face(D, Dt);
	if (FVector::DotProduct(D.GetSafeNormal(), GetActorForwardVector()) < 0.9f) { SetWalkingAnim(false); return true; }      // (turning to aim)
	GetMesh()->PlayAnimation(RangedClip, false);
	AttackLen = RDClipLength(RangedClip); AttackHit = AttackLen * RangedRelease; AttackTime = 0.f; bHitDone = false; bRangedSwing = true;
	ShotAim = To;
	if (ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr) G->PlaySoundAt(SndAttack, GetActorLocation());
	VoiceTimer = FMath::Max(VoiceTimer, 2.f);
	return true;
}

void ARDMonster::ReleaseShot(AActor* P)
{
	ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	if (!G) return;
	const FVector From = ShotMuzzle();
	FVector Aim = P ? P->GetActorLocation() + FVector(0, 0, 20.f) : ShotAim;
	// (a little ahead of a foe on the move: half of where it will be when the shot arrives)
	if (P) Aim += P->GetVelocity() * (FVector::Dist(From, Aim) / RangedSpeed) * 0.5f;
	// (blinded: its shot goes wide its share of the time; the roll a hash of its swings, never a stream of the play)
	const float Blind = GetBlindShare();
	if (Blind > 0.f && (float)(HashCombine(GetUniqueID(), (uint32)(++Swings * 2654435761u)) % 10000u) / 10000.f < Blind)
	{
		++BlindMisses;
		Aim += FVector::CrossProduct((Aim - From).GetSafeNormal(), FVector::UpVector) * 220.f;
	}
	if (RangedMuzzleFx) RDMSpawnFx(this, RangedMuzzleFx, From, (Aim - From).Rotation(), RangedFxScale, nullptr, true, true);
	G->FireMonsterShot(this, From, Aim, RangedSpeed, GetShotDamage(), RangedRange * 1.3f, RangedFx, RangedHitFx, RangedFxScale, RangedTheme);
	++ShotsFired; ++AttacksMade;
}

void ARDDungeonGenerator::FireMonsterShot(ARDMonster* From, const FVector& Muzzle, const FVector& Aim, float Speed, float Damage, float Range, UFXSystemAsset* Fx, UFXSystemAsset* HitFx, float FxScale, const FString& Theme)
{
	FMonsterShot S;
	S.From = From; S.bAlly = From && From->IsAlly(); S.At = Muzzle; S.Vel = (Aim - Muzzle).GetSafeNormal() * Speed;
	S.Damage = Damage; S.Life = Range / FMath::Max(Speed, 1.f); S.HitFx = HitFx; S.FxScale = FxScale; S.Theme = Theme;
	S.Kind = From ? From->MonsterName : NAME_None;
	if (Fx) S.Fx = RDMSpawnFx(this, Fx, Muzzle, S.Vel.Rotation(), FxScale, nullptr, true, false);
	MonsterShots.Add(S);
	ShotStats.FindOrAdd(TEXT("fired"))++;
	PlaySoundAt(TEXT("Monster.Shot"), Muzzle);
	UE_LOG(LogRDMistward5, Verbose, TEXT("RDSHOT %s fired %s: %.0f damage at %.0f cm/s"), *S.Kind.ToString(), *Theme, Damage, Speed);
}

void ARDDungeonGenerator::ResetMistward5()
{
	for (FMonsterShot& S : MonsterShots) if (UFXSystemComponent* F = S.Fx.Get()) { F->DeactivateImmediate(); F->DestroyComponent(); }
	for (auto& E : ShotFxEnding) if (UFXSystemComponent* F = E.Key.Get()) { F->DeactivateImmediate(); F->DestroyComponent(); }
	MonsterShots.Reset(); ShotFxEnding.Reset(); ShotStats.Reset(); LastShotOnHer.Reset();
	for (ARDSpectator* A : Crowd) if (IsValid(A)) A->Destroy();
	Crowd.Reset(); ArenaWaveDue = -1.f; bArenaSheInside = false; CrowdLastLeft = 0;
	StopAutoplay(TEXT("restart"));
}

void ARDDungeonGenerator::TickMonsterShots(float Dt)
{
	// (the effects of shots that ended: faded for a moment, then gone)
	for (int32 I = ShotFxEnding.Num() - 1; I >= 0; --I)
	{
		ShotFxEnding[I].Value -= Dt;
		if (ShotFxEnding[I].Value > 0.f) continue;
		if (UFXSystemComponent* F = ShotFxEnding[I].Key.Get()) { F->DeactivateImmediate(); F->DestroyComponent(); }
		ShotFxEnding.RemoveAtSwap(I);
	}
	if (MonsterShots.Num() == 0) return;
	URDCombatComponent* Pc = GetPlayerCombat();
	AActor* Her = Pc ? Pc->GetOwner() : nullptr;
	const TArray<ARDMonster*> Mons = GetMonsters();
	const TArray<ARDMonster*> HerAllies = GetAllies();
	FCollisionObjectQueryParams O; O.AddObjectTypesToQuery(ECC_WorldStatic); O.AddObjectTypesToQuery(ECC_WorldDynamic);
	auto Close = [](const FVector& A, const FVector& B, const AActor* Who, float Pad) -> bool
	{
		// (the shot's way this frame against the target's capsule: the nearest points of two segments)
		const ACharacter* Ch = Cast<ACharacter>(Who);
		if (!Ch) return false;
		const UCapsuleComponent* Cap = Ch->GetCapsuleComponent();
		const float R = Cap->GetScaledCapsuleRadius(), H = FMath::Max(Cap->GetScaledCapsuleHalfHeight() - R, 0.f);
		const FVector C = Ch->GetActorLocation();
		FVector P1, P2;
		FMath::SegmentDistToSegmentSafe(A, B, C - FVector(0, 0, H), C + FVector(0, 0, H), P1, P2);
		return FVector::Dist(P1, P2) <= R + Pad;
	};
	for (int32 I = MonsterShots.Num() - 1; I >= 0; --I)
	{
		FMonsterShot& S = MonsterShots[I];
		const FVector A = S.At;
		FVector B = A + S.Vel * Dt;
		S.Life -= Dt;
		FString Ended;
		FVector EndAt = B;
		// a wall, a door, furniture on the way: it bursts there (her and the monsters are pawns: not in this trace)
		FCollisionQueryParams Q(SCENE_QUERY_STAT(RDShot), false, S.From.Get());
		FHitResult Hit;
		const bool bWall = GetWorld()->LineTraceSingleByObjectType(Hit, A, B, O, Q);
		if (bWall) B = Hit.ImpactPoint;
		const float Pad = RD5ShotRadius - 30.f;
		if (!S.bAlly)
		{
			// her, then her allies
			if (Her && Pc && !Pc->IsDead() && Close(A, B, Her, Pad))
			{
				Pc->ApplyDamage(S.Damage, S.From.Get());
				ShotStats.FindOrAdd(TEXT("on_her"))++;
				const ARDMonster* Fm = S.From.Get();
				LastShotOnHer = FString::Printf(TEXT("%s|%.1f|%.1f|%s"), *S.Kind.ToString(), S.Damage, Fm ? Fm->GetDamage() : 0.f, *S.Theme);
				Ended = TEXT("her"); EndAt = Her->GetActorLocation();
			}
			else
				for (ARDMonster* Al : HerAllies)
					if (IsValid(Al) && !Al->IsDead() && Close(A, B, Al, Pad))
					{
						Al->ApplyDamageAt(S.Damage, S.From.Get(), &B);
						AddHitText(Al->GetActorLocation() + FVector(0, 0, Al->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()), S.Damage, false);
						ShotStats.FindOrAdd(TEXT("on_ally"))++;
						Ended = TEXT("ally"); EndAt = Al->GetActorLocation();
						break;
					}
		}
		else
			for (ARDMonster* Mo : Mons)
				if (IsValid(Mo) && !Mo->IsDead() && !Mo->IsAlly() && !Mo->bCaged && Close(A, B, Mo, Pad))
				{
					Mo->ApplyDamageAt(S.Damage, S.From.Get(), &B);
					AddHitText(Mo->GetActorLocation() + FVector(0, 0, Mo->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()), S.Damage, false);
					ShotStats.FindOrAdd(TEXT("on_monster"))++;
					Ended = TEXT("monster"); EndAt = Mo->GetActorLocation();
					break;
				}
		if (Ended.IsEmpty() && bWall) { Ended = TEXT("wall"); EndAt = B; ShotStats.FindOrAdd(TEXT("on_wall"))++; }
		if (Ended.IsEmpty() && S.Life <= 0.f) { Ended = TEXT("faded"); ShotStats.FindOrAdd(TEXT("faded"))++; }
		S.At = B;
		if (UFXSystemComponent* F = S.Fx.Get()) F->SetWorldLocationAndRotation(B, S.Vel.Rotation());
		if (Ended.IsEmpty()) continue;
		if (S.HitFx && Ended != TEXT("faded")) RDMSpawnFx(this, S.HitFx, EndAt == B ? B : (B + EndAt) * 0.5f, (-S.Vel).Rotation(), S.FxScale, nullptr, true, true);
		if (Ended != TEXT("faded")) PlaySoundAt(TEXT("Monster.ShotHit"), B);
		if (UFXSystemComponent* F = S.Fx.Get()) { F->Deactivate(); ShotFxEnding.Add(TPair<TWeakObjectPtr<UFXSystemComponent>, float>(S.Fx, 0.4f)); }
		MonsterShots.RemoveAtSwap(I);
	}
}

TArray<FString> ARDDungeonGenerator::GetShotLines() const
{
	TArray<FString> Out;
	for (const FMonsterShot& S : MonsterShots)
		Out.Add(FString::Printf(TEXT("%s|%.0f|%.0f|%.0f|%.0f"), *S.Kind.ToString(), S.At.X, S.At.Y, S.At.Z, S.Vel.Size()));
	return Out;
}

// ================================================================================================ the arena's audience
ARDSpectator::ARDSpectator()
{
	PrimaryActorTick.bCanEverTick = true;
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;
	Body = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Body"));
	Body->SetupAttachment(Root);
	Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Body->SetAnimationMode(EAnimationMode::AnimationSingleNode);
	Body->SetRelativeRotation(FRotator(0, -90.f, 0));          // (the UE4 mannequin's skeleton faces +Y)
	Body->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
}

void ARDSpectator::Init(USkeletalMesh* Mesh, UAnimationAsset* InIdle, const TArray<UAnimationAsset*>& InClaps, const TArray<UAnimationAsset*>& InCheers, int32 Seed)
{
	R.Initialize(Seed);
	Body->SetSkeletalMesh(Mesh);
	IdleAnim = InIdle;
	for (UAnimationAsset* A : InClaps) if (A) Claps.Add(A);
	for (UAnimationAsset* A : InCheers) if (A) Cheers.Add(A);
	PlayIdle();
	Body->SetPosition(R.FRandRange(0.f, 2.f));
	Body->SetPlayRate(R.FRandRange(0.9f, 1.1f));
#if WITH_EDITOR
	SetActorLabel(FString::Printf(TEXT("RD_Spectator_%d"), Seed & 0xffff));
	SetFolderPath(TEXT("RandomDungeon/Arena"));
#endif
}

void ARDSpectator::PlayIdle()
{
	Doing = 0;
	if (IdleAnim) Body->PlayAnimation(IdleAnim, true);
}

void ARDSpectator::React(bool bCheer, float Delay)
{
	if (IsLeaving() && !bCheer) return;
	PendingAt = Age + Delay; bPendingCheer = bCheer;
}

FString ARDSpectator::GetDoing() const
{
	if (IsLeaving()) return TEXT("leaving");
	return Doing == 1 ? TEXT("clap") : Doing == 2 ? TEXT("cheer") : TEXT("idle");
}

void ARDSpectator::Tick(float Dt)
{
	Super::Tick(Dt);
	Age += Dt;
	if (PendingAt >= 0.f && Age >= PendingAt)
	{
		PendingAt = -1.f;
		const TArray<TObjectPtr<UAnimationAsset>>& From = bPendingCheer || Claps.Num() == 0 ? Cheers : Claps;
		if (From.Num() > 0)
		{
			UAnimationAsset* A = From[R.RandRange(0, From.Num() - 1)];
			Body->PlayAnimation(A, false);
			Body->SetPlayRate(R.FRandRange(0.92f, 1.08f));
			const UAnimSequenceBase* S = Cast<UAnimSequenceBase>(A);
			BusyUntil = Age + (S ? S->GetPlayLength() / FMath::Max(S->RateScale, 0.05f) : 2.f) / FMath::Max(Body->GetPlayRate(), 0.1f);     // (the clip's own rate too)
			Doing = (bPendingCheer || Claps.Num() == 0) ? 2 : 1;
			++Reactions;
		}
	}
	if (Doing != 0 && BusyUntil >= 0.f && Age >= BusyUntil) { BusyUntil = -1.f; Body->SetPlayRate(R.FRandRange(0.9f, 1.1f)); PlayIdle(); }
}

void ARDDungeonGenerator::CrowdAppear(ARDSection* S, int32 Room)
{
	CrowdLeave();
	if (!S || CrowdMeshes.Num() == 0) return;
	TArray<float> Heights;
	const TArray<FVector> Tiles = S->GetRoomTiles(Room, Heights);
	if (Tiles.Num() == 0) return;
	const float T = TileSize;
	auto Key = [T](const FVector& P) { return FIntPoint(FMath::RoundToInt(P.X / T * 2.f), FMath::RoundToInt(P.Y / T * 2.f)); };
	TSet<FIntPoint> Set;
	FVector Mid = FVector::ZeroVector;
	for (const FVector& P : Tiles) { Set.Add(Key(P)); Mid += P; }
	Mid /= (float)Tiles.Num();
	TArray<FVector> Doors;
	for (const int32 D : S->GetRoomDoors(Room)) Doors.Add(S->GetDoorLocation(D));
	// (the spots along the room's walls: each edge tile's wall side, two places on it)
	struct FSpot { FVector P; float Yaw; uint32 H; };
	TArray<FSpot> Spots;
	static const FVector Dirs[4] = { FVector(1, 0, 0), FVector(-1, 0, 0), FVector(0, 1, 0), FVector(0, -1, 0) };
	FCollisionObjectQueryParams O; O.AddObjectTypesToQuery(ECC_WorldStatic); O.AddObjectTypesToQuery(ECC_WorldDynamic);
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDCrowd), false);
	for (const FVector& P : Tiles)
		for (const FVector& D : Dirs)
		{
			if (Set.Contains(Key(P + D * T))) continue;
			const FVector Side = FVector(-D.Y, D.X, 0.f);
			for (const float Along : { -T * 0.25f, T * 0.25f })
			{
				FVector Sp = P + D * (T * 0.5f - CrowdInset) + Side * Along;
				bool bNearDoor = false;
				for (const FVector& Dl : Doors) if (FVector::Dist2D(Dl, Sp) < 260.f) { bNearDoor = true; break; }
				if (bNearDoor) continue;
				// (on the floor, with nothing standing there: a capsule of a person)
				FHitResult Fl;
				if (!GetWorld()->LineTraceSingleByObjectType(Fl, Sp + FVector(0, 0, 150.f), Sp - FVector(0, 0, 250.f), O, Q)) continue;
				Sp.Z = Fl.ImpactPoint.Z;
				if (GetWorld()->OverlapAnyTestByObjectType(Sp + FVector(0, 0, 100.f), FQuat::Identity, O, FCollisionShape::MakeCapsule(26.f, 80.f), Q)) continue;
				const FVector In = (Mid - Sp).GetSafeNormal2D();
				Spots.Add({ Sp, (float)FMath::RadiansToDegrees(FMath::Atan2(In.Y, In.X)),HashCombine((uint32)SessionSeed ^ 0xC40Du, GetTypeHash(FIntPoint(FMath::RoundToInt(Sp.X), FMath::RoundToInt(Sp.Y)))) });
			}
		}
	// (spread out: in hash order, each at least CrowdSpacing from the ones taken)
	Spots.Sort([](const FSpot& A, const FSpot& B) { return A.H < B.H; });
	TArray<UAnimationAsset*> ClapList, CheerList;
	for (UAnimationAsset* A : CrowdClaps) ClapList.Add(A);
	for (UAnimationAsset* A : CrowdCheers) CheerList.Add(A);
	int32 Made = 0;
	TArray<FVector> Taken;
	for (const FSpot& Sp : Spots)
	{
		if (Made >= CrowdMax) break;
		bool bClose = false;
		for (const FVector& Tk : Taken) if (FVector::Dist2D(Tk, Sp.P) < CrowdSpacing) { bClose = true; break; }
		if (bClose) continue;
		FActorSpawnParameters Pa; Pa.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		ARDSpectator* A = GetWorld()->SpawnActor<ARDSpectator>(ARDSpectator::StaticClass(), FTransform(FRotator(0, Sp.Yaw, 0), Sp.P), Pa);
		if (!A) continue;
		A->Init(CrowdMeshes[Sp.H % (uint32)CrowdMeshes.Num()], CrowdIdle, ClapList, CheerList, (int32)Sp.H);
		if (CrowdAppearFx) RDMSpawnFx(this, CrowdAppearFx, Sp.P + FVector(0, 0, 60.f), FRotator::ZeroRotator, CrowdAppearFxScale, nullptr, true, true);
		Crowd.Add(A); Taken.Add(Sp.P); ++Made;
	}
	PlaySoundAt(TEXT("Env.Arena.Crowd"), Mid);
	RoomUses.FindOrAdd(TEXT("crowd_appeared"))++;
	UE_LOG(LogRDMistward5, Log, TEXT("RDCROWD %d townsfolk along the walls of room %d (%d spots)"), Made, Room, Spots.Num());
}

void ARDDungeonGenerator::CrowdReact(bool bCheer, float Share)
{
	if (Crowd.Num() == 0) return;
	const uint32 Salt = HashCombine((uint32)SessionSeed ^ 0xC5E3u, (uint32)(CrowdCheersMade * 131 + CrowdClapsMade * 7 + 1));
	int32 K = 0;
	FVector Mid = FVector::ZeroVector;
	for (ARDSpectator* A : Crowd)
	{
		if (!IsValid(A)) continue;
		Mid += A->GetActorLocation(); ++K;
		const uint32 H = HashCombine(Salt, (uint32)K * 2654435761u);
		// (a wave: everyone cheers; a kill: most clap, some cheer)
		const bool bThisCheer = bCheer || (H % 100u) < 30u;
		A->React(bThisCheer, (float)((H >> 8) % 600u) / 1000.f);
	}
	if (K == 0) return;
	Mid /= (float)K;
	if (bCheer) { ++CrowdCheersMade; PlaySoundAt(TEXT("Env.Arena.Cheer"), Mid); }
	else { ++CrowdClapsMade; PlaySoundAt(TEXT("Env.Arena.Clap"), Mid); if (Share >= 1.f) PlaySoundAt(TEXT("Env.Arena.Cheer"), Mid); }
	UE_LOG(LogRDMistward5, Log, TEXT("RDCROWD %s (%d townsfolk)"), bCheer ? TEXT("cheer") : TEXT("clap"), K);
}

void ARDDungeonGenerator::CrowdLeave()
{
	int32 K = 0;
	for (ARDSpectator* A : Crowd) if (IsValid(A) && !A->IsLeaving()) A->LeaveAfter(2.5f + (float)(HashCombine((uint32)SessionSeed, (uint32)++K) % 2000u) / 1000.f);
}

TArray<FString> ARDDungeonGenerator::GetCrowdLines() const
{
	TArray<FString> Out;
	for (const ARDSpectator* A : Crowd)
		if (IsValid(A))
		{
			const FVector P = A->GetActorLocation();
			const USkeletalMeshComponent* B = A->GetBody();
			Out.Add(FString::Printf(TEXT("%s|%s|%d|%.0f|%.0f|%.0f|%.0f"), *A->GetDoing(), B && B->GetSkeletalMeshAsset() ? *B->GetSkeletalMeshAsset()->GetName() : TEXT(""),
				A->Reactions, P.X, P.Y, P.Z, A->GetActorRotation().Yaw));
		}
	return Out;
}

// ================================================================================================ no way out of the arena
FString ARDDungeonGenerator::ArenaDoorNear(const FVector& From) const
{
	const ARDSection* S = IsArenaHolding() ? GetSection(ArenaSection) : nullptr;
	if (!S) return FString();
	// (only when what F reaches is one of its doors: a pile, a trap she sees, a pad or a container nearer is used as ever (the
	// PR review's find: every F within 2.4 m of an arena door said it was barred))
	bool bDoor = false; int32 I = -1;
	const float D = S->FindNearestInteractive(From, 260.f, bDoor, I);
	if (I < 0 || !bDoor || S->DoorRoom(I) != ArenaRoom || D > 240.f) return FString();
	for (const ARDLootPile* P : LootPiles) if (IsValid(P) && FVector::Dist2D(P->GetActorLocation(), From) < 260.f) return FString();
	if (Traps.Num() > 0 && !DescribeTrapNear(From).IsEmpty()) return FString();
	if (bTeleporters && PadNear(From) > 0) return FString();
	return TEXT("the arena's doors are barred until its last wave falls");
}

bool ARDDungeonGenerator::RefuseArenaExit(const TCHAR* How)
{
	++ArenaEscapesRefused;
	if (URDCombatComponent* Pc = GetPlayerCombat())
	{
		Pc->ShowMessage(FString::Printf(TEXT("The arena holds you: %s until its last wave falls"),
			FCString::Strcmp(How, TEXT("ring")) == 0 ? TEXT("the ring is cold") : FCString::Strcmp(How, TEXT("pad")) == 0 ? TEXT("the teleporter is dark") : TEXT("its doors are barred")));
		if (const AActor* O = Pc->GetOwner()) PlaySoundAt(TEXT("Env.CellClose"), O->GetActorLocation());
	}
	UE_LOG(LogRDMistward5, Log, TEXT("RDARENA way out refused (%s)"), How);
	return true;
}

void ARDDungeonGenerator::TickArenaHold(float Dt)
{
	// (the audience: the ones whose time is up leave in a puff; with no arena going on they all go)
	if (ArenaRoom < 0) CrowdLeave();
	for (int32 I = Crowd.Num() - 1; I >= 0; --I)
	{
		ARDSpectator* A = Crowd[I];
		if (!IsValid(A)) { Crowd.RemoveAt(I); continue; }
		if (!A->ShouldGo()) continue;
		if (CrowdAppearFx) RDMSpawnFx(this, CrowdAppearFx, A->GetActorLocation() + FVector(0, 0, 60.f), FRotator::ZeroRotator, CrowdAppearFxScale, nullptr, true, true);
		A->Destroy(); Crowd.RemoveAt(I);
	}
	// (she left the arena by some way not shut (a roll through a closing door, a push): back inside)
	if (!IsArenaHolding()) return;
	URDCombatComponent* Pc = GetPlayerCombat();
	ACharacter* Her = Pc ? Cast<ACharacter>(Pc->GetOwner()) : nullptr;
	ARDSection* S = GetSection(ArenaSection);
	if (!Her || !S || Pc->IsDead()) return;
	const FVector L = Her->GetActorLocation();
	FVector2D Mn, Mx; S->GetRoomBounds(ArenaRoom, Mn, Mx);
	const float Out = FMath::Max(FMath::Max(Mn.X - L.X, L.X - Mx.X), FMath::Max(Mn.Y - L.Y, L.Y - Mx.Y));
	// (held once she has been in it: an arena begun from afar (a test's) does not pull her in)
	if (S->RoomAt(L) == ArenaRoom) bArenaSheInside = true;
	if (!bArenaSheInside || Out < 60.f) return;           // (inside, or in the doorway inside the room's box)
	const TArray<FVector> Free = S->GetRoomFreeTilesNear(ArenaRoom, L);
	if (Free.Num() == 0) return;
	const FVector To = Free[0] + FVector(0, 0, Her->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 5.f);
	Her->SetActorLocation(To, false, nullptr, ETeleportType::TeleportPhysics);
	Her->GetCharacterMovement()->StopMovementImmediately();
	++ArenaPutBack;
	RefuseArenaExit(TEXT("door"));
	UE_LOG(LogRDMistward5, Log, TEXT("RDARENA she was %.0f cm out: put back at (%.0f, %.0f)"), Out, To.X, To.Y);
}

// ================================================================================================ autoplay
void ARDDungeonGenerator::ReadAutoplayOption()
{
	if (!bAutoplayMode) { bAutoplayOptionRead = true; return; }
	if (!PlayerCombat) return;          // (once her combat component is made)
	bAutoplayOptionRead = true;
	// (the menu's AUTOPLAY opens the castle with ?Autoplay=<seconds>; the command line's -Autoplay=<seconds> once a game run)
	float Secs = -1.f; bool bQuit = false;
	if (const AGameModeBase* GM = GetWorld()->GetAuthGameMode())
	{
		const FString V = UGameplayStatics::ParseOption(GM->OptionsString, TEXT("Autoplay"));
		if (!V.IsEmpty()) Secs = FCString::Atof(*V);
	}
	static bool bCommandDone = false;
	float C = 0.f;
	if (Secs < 0.f && !bCommandDone && FParse::Value(FCommandLine::Get(), TEXT("-Autoplay="), C))
	{
		bCommandDone = true; Secs = C; bQuit = !FParse::Param(FCommandLine::Get(), TEXT("AutoplayStay"));
		// (-AutoplayLocked: no key of the player's takes over (a recording: Game Bar's hotkey reaches the game))
		if (FParse::Param(FCommandLine::Get(), TEXT("AutoplayLocked"))) bAutoplayIgnorePlayer = true;
	}
	if (Secs >= 0.f) StartAutoplay(Secs, bQuit);
}

void ARDDungeonGenerator::StartAutoplay(float Seconds, bool bQuitAtEnd)
{
	bAutoplay = true; bAutoplayQuit = bQuitAtEnd; AutoplaySeconds = FMath::Max(Seconds, 0.f);
	AutoplayStart = GetWorld()->GetTimeSeconds(); AutoplayThink = 0.f; AutoplayStuck = 0.f; AutoplayNextAct = 0.f; AutoplayUseNext = 0.f; AutoplayGoalKind = 0; AutoplayGoalKey = 0; AutoplayPrey = nullptr;
	AutoplayPath.Reset(); AutoplayFoe = nullptr; AutoplayRoomsSeen.Reset(); AutoplayRoomsBlocked.Reset(); AutoplayGoal = FVector::ZeroVector;
	AutoplayStats.Reset(); AutoplayWeaponTurn = 0; AutoplayWalked = 0.f; AutoplayWalkFrom = FVector::ZeroVector;
	bAutoplayHunting = false; AutoplayHuntNext = 0.f; AutoplayPreyBlocked.Reset();
	AutoplayR.Initialize((int32)HashCombine((uint32)SessionSeed, 0xA070u));
	if (PlayerCombat) { PlayerCombat->SetRunMode(true); PlayerCombat->ShowMessage(AutoplaySeconds > 0.f ? FString::Printf(TEXT("Autoplay for %.0f s: any key takes over"), AutoplaySeconds) : FString(TEXT("Autoplay: any key takes over"))); }
	UE_LOG(LogRDMistward5, Log, TEXT("RDAUTOPLAY begun: %s, %.0f s%s"), *CurrentHero.ToString(), AutoplaySeconds, bAutoplayQuit ? TEXT(", the game quits after") : TEXT(""));
}

void ARDDungeonGenerator::StopAutoplay(const FString& Why)
{
	if (!bAutoplay) return;
	bAutoplay = false; AutoplayDoing.Reset();
	AutoplayPath.Reset(); AutoplayFoe = nullptr;
	UE_LOG(LogRDMistward5, Log, TEXT("RDAUTOPLAY ended (%s) after %.0f s: %d kills, %d attacks, %d things used, %d opened, %d rooms"), *Why,
		GetWorld()->GetTimeSeconds() - AutoplayStart, PlayerCombat ? PlayerCombat->Kills : 0, AutoplayStats.FindRef(TEXT("attacks")), AutoplayStats.FindRef(TEXT("used")),
		AutoplayStats.FindRef(TEXT("opened")), AutoplayRoomsSeen.Num());
	if (PlayerCombat && Why != TEXT("quit")) PlayerCombat->ShowMessage(Why.StartsWith(TEXT("player")) ? FString(TEXT("You take over")) : FString(TEXT("Autoplay ended")));
}

float ARDDungeonGenerator::GetAutoplayLeft() const
{
	if (!bAutoplay) return 0.f;
	return AutoplaySeconds > 0.f ? FMath::Max(0.f, AutoplaySeconds - (GetWorld()->GetTimeSeconds() - AutoplayStart)) : -1.f;
}

/** the tile path from From to To without its first point, the middle of the tile she stands on */
static TArray<FVector> RD5PathTo(const ARDSection* S, const FVector& From, const FVector& To)
{
	TArray<FVector> P = S ? S->FindPathWorld(From, To) : TArray<FVector>();
	if (P.Num() >= 2) P.RemoveAt(0);
	return P;
}

/** her weapons the pilot may use: index, how far it reaches (cm between capsules), whether it is a summon (and its spell) */
struct FRD5Arm { int32 Index; float Range; bool bSummon; bool bSpell; FName Spell; int32 Count; };

static TArray<FRD5Arm> RD5Arms(const ARDDungeonGenerator* G)
{
	TArray<FRD5Arm> Out;
	for (int32 I = 0; I < G->Weapons.Num(); ++I)
	{
		const FRDWeaponDef& W = G->Weapons[I];
		if (W.bScroll) continue;
		FRD5Arm A{ I, W.Reach * 0.85f, false, W.bSpell, NAME_None, 0 };
		if (W.bSpell)
		{
			A.Range = W.BoltRange > 0.f ? W.BoltRange * 0.85f : W.Reach + 100.f;
			if (G->Spells.IsValidIndex(W.SpellIndex))
			{
				const FRDSpellDef& S = G->Spells[W.SpellIndex];
				A.Spell = S.Name;
				if (S.Kind == ERDSpellKind::Summon) { A.bSummon = true; A.Count = FMath::Max(S.Count, 1); A.Range = 1e6f; }
				else if (S.Kind != ERDSpellKind::Bolt && S.Kind != ERDSpellKind::Rend && S.Kind != ERDSpellKind::Lash && S.Kind != ERDSpellKind::Drain)
					A.Range = FMath::Min(FMath::Max(S.Reach, 600.f), 1400.f);
				if (S.Kind == ERDSpellKind::Lash) A.Range = FMath::Max(S.Reach, 250.f);
			}
		}
		Out.Add(A);
	}
	return Out;
}

void ARDDungeonGenerator::TickAutoplay(float Dt)
{
	URDCombatComponent* Pc = GetPlayerCombat();
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	ACharacter* Her = PC ? Cast<ACharacter>(PC->GetPawn()) : nullptr;
	if (!Pc || !Her) return;
	UWorld* W = GetWorld();
	const float Now = W->GetTimeSeconds();
	if (AutoplaySeconds > 0.f && Now - AutoplayStart >= AutoplaySeconds)
	{
		const bool bQuit = bAutoplayQuit;
		StopAutoplay(bQuit ? TEXT("quit") : TEXT("time"));
		if (bQuit) UKismetSystemLibrary::QuitGame(this, PC, EQuitPreference::Quit, false);
		return;
	}
	// (a key, a click or a stick of the player's: she is theirs again)
	if (!bAutoplayIgnorePlayer)
	{
		static TArray<FKey> Take;
		if (Take.Num() == 0)
		{
			TArray<FKey> All; EKeys::GetAllKeys(All);
			for (const FKey& K : All)
				if (K.IsValid() && !K.IsAxis1D() && !K.IsAxis2D() && !K.IsAxis3D() && !K.IsTouch() && !K.IsGesture() && !K.IsModifierKey()
					&& K != EKeys::LeftCommand && K != EKeys::RightCommand) Take.Add(K);
		}
		// (Alt or the Windows key down, or down within the last second, the keys are a system chord's (Game Bar's Win+Alt+R
		// reached the game as an R with no Alt seen down: the Game Bar recordings of 2026-11-01 stood still from their 4th s))
		if (PC->IsInputKeyDown(EKeys::LeftAlt) || PC->IsInputKeyDown(EKeys::RightAlt) || PC->IsInputKeyDown(EKeys::LeftCommand) || PC->IsInputKeyDown(EKeys::RightCommand)
			|| PC->WasInputKeyJustReleased(EKeys::LeftAlt) || PC->WasInputKeyJustReleased(EKeys::LeftCommand)) AutoplayChordUntil = Now + 1.f;
		FKey Took;
		if (Now >= AutoplayChordUntil) for (const FKey& K : Take) if (PC->WasInputKeyJustPressed(K)) { Took = K; break; }
		for (const FKey& K : { EKeys::Gamepad_LeftX, EKeys::Gamepad_LeftY, EKeys::Gamepad_RightX, EKeys::Gamepad_RightY })
			if (FMath::Abs(PC->GetInputAnalogKeyState(K)) > 0.5f) Took = K;
		if (Took.IsValid()) { StopAutoplay(FString::Printf(TEXT("player: %s"), *Took.ToString())); return; }
	}
	if (Pc->IsDead()) { AutoplayDoing = TEXT("down"); AutoplayPath.Reset(); AutoplayFoe = nullptr; return; }
	if (Pc->IsInventoryOpen()) Pc->SetInventoryOpen(false);
	if (Pc->IsCraftingOpen()) Pc->SetCraftingOpen(false);
	const FVector L = Her->GetActorLocation();
	// (how far she went: whole centimetres a frame, a jump of more than 5 m (a respawn, a teleport) not counted)
	if (!AutoplayWalkFrom.IsZero()) { const float Step = FVector::Dist2D(L, AutoplayWalkFrom); if (Step < 500.f) AutoplayWalked += Step; AutoplayStats.FindOrAdd(TEXT("metres")) = (int32)(AutoplayWalked / 100.f); }
	AutoplayWalkFrom = L;
	ARDSection* S = GetSection(WorldToSection(L));
	FVector Move = FVector::ZeroVector;
	FVector Look = Her->GetActorForwardVector();
	// ---- hurt: a healing potion or food (the best she has); low on mana in a fight: a mana potion
	if (Now >= AutoplayUseNext)
	{
		const float Hp = Pc->GetHealth() / FMath::Max(Pc->GetMaxHealth(), 1.f);
		const bool bLowMana = Pc->GetMaxMana() > 0.f && Pc->GetMana() < Pc->GetMaxMana() * 0.25f && AutoplayFoe.IsValid();
		if (Hp < 0.45f || bLowMana)
		{
			const ERDItemKind Want = Hp < 0.45f ? ERDItemKind::Healing : ERDItemKind::Mana;
			int32 Best = -1; float BestAmt = -1.f;
			for (int32 I = 0; I < Items.Num(); ++I)
				if ((Items[I].Kind == Want || (Want == ERDItemKind::Healing && Items[I].Kind == ERDItemKind::Food && Pc->GetRegenPerSecond() <= 0.f)) && Pc->GetItemCount(Items[I].Name) > 0 && Items[I].Amount > BestAmt)
				{ Best = I; BestAmt = Items[I].Amount; }
			if (Best >= 0 && Pc->UseItem(Items[Best].Name)) { AutoplayStats.FindOrAdd(TEXT("used"))++; AutoplayNextAct = Now + 0.6f; }
			AutoplayUseNext = Now + 3.f;          // (a potion's or food's effect shows before the next: food heals over time)
		}
	}
	// ---- the one to fight: the nearest she can see within 18 m, or one coming at her
	ARDMonster* Foe = AutoplayFoe.Get();
	if (Foe && (Foe->IsDead() || Foe->bCaged || Foe->IsAlly() || FVector::Dist(Foe->GetActorLocation(), L) > 2600.f)) Foe = nullptr;
	if (AutoplayThink <= 0.f)
	{
		AutoplayThink = 0.25f;
		FCollisionObjectQueryParams O; O.AddObjectTypesToQuery(ECC_WorldStatic); O.AddObjectTypesToQuery(ECC_WorldDynamic);
		FCollisionQueryParams Q(SCENE_QUERY_STAT(RDAutoSight), false, Her);
		ARDMonster* Best = nullptr; float BestD = 1e9f;
		for (ARDMonster* M : GetMonsters())
		{
			if (!IsValid(M) || M->IsDead() || M->bCaged || M->IsAlly() || M->IsCorpse()) continue;
			const FVector Ml = M->GetActorLocation();
			const float D = FVector::Dist(Ml, L);
			if (D > 1800.f || FMath::Abs(Ml.Z - L.Z) > 300.f) continue;
			Q.ClearIgnoredSourceObjects(); Q.AddIgnoredActor(Her); Q.AddIgnoredActor(M);
			const bool bSeen = !W->LineTraceTestByObjectType(L + FVector(0, 0, 50.f), Ml + FVector(0, 0, 30.f), O, Q);
			if (!bSeen && !(M->IsAggro() && D < 900.f)) continue;
			const float Score = D * (M == Foe ? 0.6f : 1.f) * (bSeen ? 1.f : 1.6f);
			if (Score < BestD) { BestD = Score; Best = M; }
		}
		if (Best != Foe) { Foe = Best; AutoplayPath.Reset(); }
	}
	AutoplayThink -= Dt;
	AutoplayFoe = Foe;
	if (Foe)
	{
		const FVector Fl = Foe->GetActorLocation();
		FVector D = Fl - L; D.Z = 0.f;
		const float Gap = D.Size() - Her->GetCapsuleComponent()->GetScaledCapsuleRadius() - Foe->GetCapsuleComponent()->GetScaledCapsuleRadius();
		const FString Name = Foe->Title.IsEmpty() ? Foe->MonsterName.ToString() : Foe->Title;
		AutoplayDoing = FString::Printf(TEXT("fight %s"), *Name);
		const TArray<FRD5Arm> Arms = RD5Arms(this);
		float BestRange = 0.f;
		for (const FRD5Arm& A : Arms)
			if (!A.bSummon && Pc->GetMana() >= Weapons[A.Index].ManaCost && Pc->GetCooldownLeft(A.Index) <= 0.f) BestRange = FMath::Max(BestRange, A.Range);
		if (BestRange <= 0.f) for (const FRD5Arm& A : Arms) if (!A.bSummon && Weapons[A.Index].ManaCost <= 0.f) BestRange = FMath::Max(BestRange, A.Range);
		// (attacks: summons while she leads fewer than she may, then the weapons and spells in turn, each in its reach)
		if (Now >= AutoplayNextAct && !Pc->IsAttacking())
		{
			Her->SetActorRotation(FRotator(0, D.Rotation().Yaw, 0));
			bool bDid = false;
			for (const FRD5Arm& A : Arms)
				if (A.bSummon && CountSummoned(A.Spell) < A.Count && Pc->GetMana() >= Weapons[A.Index].ManaCost && Pc->StartAttackWith(A.Index))
				{ bDid = true; AutoplayStats.FindOrAdd(TEXT("summons"))++; break; }
			for (int32 K = 0; K < Arms.Num() && !bDid; ++K)
			{
				const FRD5Arm& A = Arms[(K + AutoplayWeaponTurn) % Arms.Num()];
				if (A.bSummon || Gap > A.Range) continue;
				if (Pc->GetMana() < Weapons[A.Index].ManaCost) continue;
				if (Pc->StartAttackWith(A.Index)) { bDid = true; AutoplayWeaponTurn = (K + AutoplayWeaponTurn + 1) % FMath::Max(Arms.Num(), 1); }
			}
			if (bDid) { AutoplayStats.FindOrAdd(TEXT("attacks"))++; AutoplayNextAct = Now + 0.15f; }
			else AutoplayNextAct = Now + 0.2f;
		}
		// (her own abilities now and then: a roll away from a blow, a dash at one a few metres off)
		if (Foe->IsAttacking() && Gap < 160.f && AutoplayR.FRand() < 0.02f && Pc->StartRoll(FVector::CrossProduct(D.GetSafeNormal(), FVector::UpVector) * (AutoplayR.FRand() < 0.5f ? 1.f : -1.f)))
			AutoplayStats.FindOrAdd(TEXT("rolls"))++;
		else if (Gap > 300.f && Gap < 650.f && AutoplayR.FRand() < 0.01f && Pc->StartDash()) AutoplayStats.FindOrAdd(TEXT("dashes"))++;
		// (closer while out of her reach; she stands and faces it in reach)
		const float Want = FMath::Max(FMath::Min(BestRange * 0.7f, 900.f), 60.f);
		Look = D.GetSafeNormal();
		if (Gap > Want && !Pc->IsAttacking())
		{
			if (AutoplayPath.Num() == 0 || AutoplayThink <= 0.05f)
			{
				AutoplayPath = S && S == GetSection(WorldToSection(Fl)) ? RD5PathTo(S, L, Fl) : TArray<FVector>();
				if (AutoplayPath.Num() == 0) AutoplayPath.Add(Fl);
				else AutoplayPath.Last() = Fl;
			}
		}
		else { AutoplayPath.Reset(); Her->SetActorRotation(FMath::RInterpConstantTo(Her->GetActorRotation(), FRotator(0, D.Rotation().Yaw, 0), Dt, 540.f)); }
	}
	else
	{
		// ---- things to take or use where she stands: harvests, her things, pickups, chests, shrines, fountains, prisoners
		if (Now >= AutoplayNextAct)
		{
			const FString What = DescribeNearest(L, 230.f);
			static const TCHAR* Ok[] = { TEXT("harvest"), TEXT("take"), TEXT("pray"), TEXT("drink"), TEXT("unlock the cell"), TEXT("open chest"), TEXT("open trunk"),
				TEXT("open barrel"), TEXT("open crate"), TEXT("open wardrobe"), TEXT("open coffin"), TEXT("open urn"), TEXT("open sarcophagus"), TEXT("open cabinet"), TEXT("open vase") };
			bool bUse = false;
			for (const TCHAR* P : Ok) if (What.StartsWith(P)) { bUse = true; break; }
			if (bUse) { const FString Did = InteractNearest(L, 230.f); AutoplayStats.FindOrAdd(TEXT("opened"))++; AutoplayDoing = What; AutoplayNextAct = Now + 1.2f; UE_LOG(LogRDMistward5, Log, TEXT("RDAUTOPLAY %s -> %s"), *What, *Did); }
			// (armour she found and does not wear: put on, if her hero wears it)
			for (const FRDItemDef& It : Items)
				if (It.Kind == ERDItemKind::Armour && Pc->GetItemCount(It.Name) > 0 && !AutoplayStats.Contains(FString(TEXT("tried ")) + It.Name.ToString()))
				{
					AutoplayStats.Add(FString(TEXT("tried ")) + It.Name.ToString(), Pc->WearArmour(It.Name) ? 1 : 0);
					break;
				}
		}
		// ---- the next place to go: a chest close by, else the nearest monster she can reach (hunted: the way again every 1.5 s
		// as it moves), else a room not seen, else on to the next set (the first test's pilot went chest to chest across the
		// 250 m set and never came within sight of a monster)
		const bool bArrived = !AutoplayGoal.IsZero() && FVector::Dist2D(AutoplayGoal, L) < 180.f;
		if (bAutoplayHunting && Now >= AutoplayHuntNext) { AutoplayGoal = FVector::ZeroVector; AutoplayPath.Reset(); }
		if (S && (AutoplayGoal.IsZero() || bArrived || AutoplayPath.Num() == 0))
		{
			if (bArrived && AutoplayGoalKind == 1) AutoplayRoomsBlocked.Add(AutoplayGoalKey);
			if (bArrived || AutoplayGoal.IsZero())
			{
				const int32 Rm = S->RoomAt(L);
				if (Rm >= 0) { AutoplayRoomsSeen.Add(FIntVector(S->Coord.X, S->Coord.Y, Rm)); AutoplayStats.FindOrAdd(TEXT("rooms")) = AutoplayRoomsSeen.Num(); }
			}
			AutoplayGoal = FVector::ZeroVector; AutoplayPath.Reset(); bAutoplayHunting = false; AutoplayGoalKind = 0; AutoplayPrey = nullptr;
			float BestD = 1500.f; int32 BestKey = 0;
			for (int32 I = 0; I < S->GetNumContainers(); ++I)
			{
				if (S->IsContainerLooted(I) || S->IsTargetOpen(false, I)) continue;
				const FString K = S->GetContainerKind(I);
				if (!(K.Contains(TEXT("chest")) || K.Contains(TEXT("trunk")) || K.Contains(TEXT("wardrobe")) || K.Contains(TEXT("coffin")))) continue;
				const FVector Cl = S->GetContainerLocation(I);
				const int32 Key = (S->Coord.X * 7919 + S->Coord.Y) * 4096 + I;
				if (AutoplayRoomsBlocked.Contains(-1 - Key)) continue;
				const float Dd = FVector::Dist2D(Cl, L);
				if (Dd < BestD) { BestD = Dd; AutoplayGoal = Cl; BestKey = -1 - Key; }
			}
			if (!AutoplayGoal.IsZero())
			{
				// (a chest stands on a tile off the way: the path's end is the last tile before it, then straight on)
				AutoplayPath = RD5PathTo(S, L, AutoplayGoal);
				if (AutoplayPath.Num() == 0) { AutoplayRoomsBlocked.Add(BestKey); AutoplayGoal = FVector::ZeroVector; }
				else { AutoplayPath.Add(AutoplayGoal); AutoplayDoing = TEXT("to a chest"); AutoplayGoalKind = 1; AutoplayGoalKey = BestKey; }
			}
			if (AutoplayGoal.IsZero())
			{
				// (the nearest monster of this set or the ones round it, by the way to it where it is in this set)
				ARDMonster* Prey = nullptr; float PreyD = 15000.f; TArray<FVector> PreyPath;
				TArray<ARDMonster*> Cands;
				for (ARDMonster* M : GetMonsters())
					if (IsValid(M) && !M->IsDead() && !M->bCaged && !M->IsAlly() && !M->IsCorpse() && FMath::Abs(M->GetActorLocation().Z - L.Z) < 300.f
						&& !AutoplayPreyBlocked.Contains(M)) Cands.Add(M);
				Cands.Sort([&L](const ARDMonster& A, const ARDMonster& B) { return FVector::DistSquared2D(A.GetActorLocation(), L) < FVector::DistSquared2D(B.GetActorLocation(), L); });
				for (int32 K = 0; K < Cands.Num() && K < 6; ++K)
				{
					const FVector Ml = Cands[K]->GetActorLocation();
					const bool bHere = GetSection(WorldToSection(Ml)) == S;
					TArray<FVector> P = bHere ? RD5PathTo(S, L, Ml) : TArray<FVector>();
					const float Len = bHere ? (P.Num() > 0 ? P.Num() * TileSize : 1e9f) : FVector::Dist2D(Ml, L) * 1.5f;
					if (bHere && P.Num() == 0) { AutoplayPreyBlocked.Add(Cands[K]); continue; }
					if (Len < PreyD) { PreyD = Len; Prey = Cands[K]; PreyPath = P; }
				}
				if (Prey)
				{
					AutoplayPath = PreyPath.Num() > 0 ? PreyPath : TArray<FVector>{ Prey->GetActorLocation() };
					AutoplayPath.Last() = Prey->GetActorLocation();
					AutoplayGoal = Prey->GetActorLocation(); bAutoplayHunting = true; AutoplayHuntNext = Now + 1.5f; AutoplayGoalKind = 2; AutoplayPrey = Prey;
					AutoplayDoing = FString::Printf(TEXT("hunt %s"), *(Prey->Title.IsEmpty() ? Prey->MonsterName.ToString() : Prey->Title));
				}
			}
			if (AutoplayGoal.IsZero())
			{
				BestD = 1e9f;
				for (int32 Rm = 0; Rm < S->GetNumRooms(); ++Rm)
				{
					const FIntVector K(S->Coord.X, S->Coord.Y, Rm);
					if (AutoplayRoomsSeen.Contains(K) || AutoplayRoomsBlocked.Contains(GetTypeHash(K)) || S->GetRoomKindEnum(Rm) == ERDRoomKind::Junction) continue;
					const FVector C = S->GetRoomCenter(Rm);
					const float Dd = FVector::Dist2D(C, L);
					if (Dd < BestD) { BestD = Dd; AutoplayGoal = C; }
				}
				if (!AutoplayGoal.IsZero())
				{
					AutoplayPath = RD5PathTo(S, L, AutoplayGoal);
					if (AutoplayPath.Num() == 0)
					{
						const int32 Rm = S->RoomAt(AutoplayGoal);
						AutoplayRoomsBlocked.Add(GetTypeHash(FIntVector(S->Coord.X, S->Coord.Y, Rm)));
						AutoplayGoal = FVector::ZeroVector;
					}
					else { AutoplayDoing = FString::Printf(TEXT("to room %d"), S->RoomAt(AutoplayGoal)); AutoplayGoalKind = 3; AutoplayGoalKey = (int32)GetTypeHash(FIntVector(S->Coord.X, S->Coord.Y, S->RoomAt(AutoplayGoal))); }
				}
			}
			if (AutoplayGoal.IsZero())
			{
				// (every room of this set seen: a way out to a set not sealed, the one least visited first)
				TArray<int32> Kinds; const TArray<FVector> Seals = S->GetSealPoints(Kinds);
				int32 BestP = -1; float BestScore = 1e9f; FVector BestBorder, BestOut;
				for (int32 P = 0; P < S->GetNumPortals(); ++P)
				{
					FVector Border, Outward;
					const FIntPoint Nb = S->PortalNeighbour(P, Border, Outward);
					bool bSealed = false;
					for (const FVector& Sl : Seals) if (FVector::Dist2D(Sl, Border) < 500.f) { bSealed = true; break; }
					if (bSealed || AutoplayRoomsBlocked.Contains((int32)GetTypeHash(FIntVector(S->Coord.X, S->Coord.Y, -100 - P)))) continue;
					int32 Seen = 0;
					for (const FIntVector& K : AutoplayRoomsSeen) if (K.X == Nb.X && K.Y == Nb.Y) ++Seen;
					const float Score = Seen * 100000.f + FVector::Dist2D(Border, L) + AutoplayR.FRandRange(0.f, 2000.f);
					if (Score < BestScore) { BestScore = Score; BestP = P; BestBorder = Border; BestOut = Outward; }
				}
				if (BestP >= 0)
				{
					AutoplayPath = RD5PathTo(S, L, BestBorder - BestOut * 150.f);
					AutoplayPath.Add(BestBorder + BestOut * 900.f);
					AutoplayGoal = BestBorder + BestOut * 900.f;
					AutoplayDoing = TEXT("on to the next set"); AutoplayGoalKind = 4; AutoplayGoalKey = (int32)GetTypeHash(FIntVector(S->Coord.X, S->Coord.Y, -100 - BestP));
				}
				else AutoplayRoomsSeen.Reset();          // (nowhere new: round again)
			}
		}
	}
	// ---- along the path: a closed door between her and the next point is pushed open
	while (AutoplayPath.Num() > 0 && FVector::Dist2D(AutoplayPath[0], L) < 90.f) AutoplayPath.RemoveAt(0);
	if (AutoplayPath.Num() > 0 && !Pc->IsAttacking())
	{
		const FVector To = AutoplayPath[0];
		if (S)
		{
			const int32 Dr = S->DoorBetween(S->WorldToLocal(L), S->WorldToLocal(To));
			if (Dr >= 0 && !S->IsTargetOpen(true, Dr) && FVector::Dist2D(S->GetDoorLocation(Dr), L) < 320.f && Now >= AutoplayNextAct)
			{
				S->ToggleDoor(Dr, L); AutoplayNextAct = Now + 0.5f; AutoplayStats.FindOrAdd(TEXT("doors"))++;
			}
		}
		Move = (To - L).GetSafeNormal2D();
		if (!Foe) Look = Move;
	}
	// ---- stuck: a step aside, then the goal is given up
	if (!Move.IsZero())
	{
		AutoplayStuck += Dt;
		if (AutoplayStuck > 1.f)
		{
			const float Moved = FVector::Dist2D(L, AutoplayLastPos);
			if (Moved < 40.f)
			{
				AutoplayStats.FindOrAdd(TEXT("stuck"))++;
				if (AutoplayStats.FindRef(TEXT("stuck")) % 3 == 0)
				{
					if (AutoplayGoalKind == 2) { if (AutoplayPrey.IsValid()) AutoplayPreyBlocked.Add(AutoplayPrey); }
					else if (AutoplayGoalKind != 0) AutoplayRoomsBlocked.Add(AutoplayGoalKey);
					AutoplayGoalKind = 0; AutoplayPrey = nullptr;
					AutoplayGoal = FVector::ZeroVector; AutoplayPath.Reset(); AutoplayFoe = nullptr; AutoplayThink = 1.5f;
				}
				else { AutoplayPath.Insert(L + FVector::CrossProduct(Move, FVector::UpVector) * (AutoplayR.FRand() < 0.5f ? 200.f : -200.f) - Move * 80.f, 0); Her->Jump(); }
			}
			AutoplayStuck = 0.f; AutoplayLastPos = L;
		}
	}
	else { AutoplayStuck = 0.f; AutoplayLastPos = L; }
	if (!Move.IsZero()) Her->AddMovementInput(Move, 1.f);
	// ---- the camera: behind her, turning with where she goes or the one she fights
	const FRotator Cr = PC->GetControlRotation();
	const FRotator Want(-14.f, Look.Rotation().Yaw, 0.f);
	PC->SetControlRotation(FMath::RInterpTo(Cr, Want, Dt, 2.5f));
}
