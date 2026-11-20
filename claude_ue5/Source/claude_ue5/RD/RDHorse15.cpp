// The user's of 2026-11-18: "there is a new ultimate horse kit downloaded in the fab cache. use those resources to improve the horse
// movement and riding mechanics" (the user's choices: the pack's own horse and clips; momentum and gaits, getting on and off, a jump
// and a rear, the hooves' sound and dust, swimming; a natural gallop of about 12 m/s). HorseDef.bPack (933 writes it):
//   - the ride: her capsule still the one that moves (everything that keys on her pawn holds), but its own acceleration and braking
//     off while she rides: the horse's heading and speed are its own, eased up (Accel) and down (Decel, HardStop when let go at a
//     gallop, the pack's sudden stop's pose and dust), turned at a rate that falls with the speed (TurnSlow to TurnFast), backed
//     (TopBack) when held back with the camera behind it, stopped short of a wall by a sweep ahead of its chest; written into her
//     velocity each frame after her movement's tick, so walls, slopes and falls are still the movement's;
//   - its clips (URDHorseAnimInstance, crossfaded): idle, the walk and the gallop at the rate their hooves keep to the ground (933
//     measures each clip's ground speed), backing, the stop, the jump's three, the rear, the swim's two, a hit from the side it came;
//     the horse pitched to the ground under its hooves;
//   - the rider: carried by the horse's rider socket (its move from its rest, as the pack carries its rider: rising with each
//     stride and the rear), her hero's rig brought to the pack's rider's seat (RiderClips.SeatOffset, 933); up and down by the
//     pack's clips from the horse's nearer side (her feet eased from the ground to the stirrups);
//   - the hooves heard where each lands (the pack's grass, dirt or hard-ground steps by the ground under it), dust thrown on dirt;
//   - in deep water it swims (her too: the saddle stays above the face), slower, no jump.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDHorse.h"
#include "RD/RDHorseAnim.h"
#include "RD/RDCombat.h"
#include "RD/RDMonster.h"
#include "RD/RDWild.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/PlayerController.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequenceBase.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDHorse15, Log, All);

namespace
{
	const FName RDRide15Slot(TEXT("DefaultSlot"));          // (the rider's slot, as RDHorse.cpp's)
	float RDRide15Len(const UAnimSequenceBase* C) { return C ? C->GetPlayLength() / FMath::Max(FMath::Abs(C->RateScale), 0.01f) : 0.f; }
	// (a phase crossed between two frames' shares of a loop, either way round it)
	bool RDRide15Crossed(float A, float B, float F)
	{
		if (FMath::Abs(B - A) > 0.5f) { if (B < A) B += 1.f; else A += 1.f; if (F < FMath::Min(A, B)) F += 1.f; }
		return F > FMath::Min(A, B) && F <= FMath::Max(A, B);
	}
}

FTransform ARDDungeonGenerator::RiderFrame15() const
{
	if (!Horse || !Horse->Body) return FTransform::Identity;
	const FTransform Sock = Horse->Body->GetSocketTransform(HorseDef.RiderSocket, RTS_World);
	// (RiderFrameUp over the horse's origin in the horse's mesh (pitched with it on a slope), moved as the socket has moved from its
	// rest; not turned with it (the first rear's picture: carried rigidly by the socket she lay on her back, the pack's rear clip
	// leaning her forward as the horse rises), unless RiderTurnShare asks for a share of the socket's turn)
	const FTransform BodyT = Horse->Body->GetComponentTransform();
	const FVector Rest = BodyT.TransformPosition(HorseDef.RiderSocketRef.GetLocation());
	FTransform Fr = FTransform(FVector(0.f, 0.f, HorseDef.RiderFrameUp)) * BodyT;
	Fr.AddToTranslation(Sock.GetLocation() - Rest);
	if (HorseDef.RiderTurnShare > 0.f)
	{
		const FQuat Turn = Sock.GetRotation() * (BodyT.GetRotation() * HorseDef.RiderSocketRef.GetRotation()).Inverse();
		const FQuat Part = FQuat::Slerp(FQuat::Identity, Turn, FMath::Clamp(HorseDef.RiderTurnShare, 0.f, 1.f));
		Fr.SetTranslation(Sock.GetLocation() + Part.RotateVector(Fr.GetLocation() - Sock.GetLocation()));
		Fr.SetRotation(Part * Fr.GetRotation());
	}
	return Fr;
}

void ARDDungeonGenerator::PlayRider15(ACharacter* C, UAnimSequenceBase* Clip, bool bLoop, float Rate, float Blend)
{
	UAnimInstance* AI = C && Clip ? C->GetMesh()->GetAnimInstance() : nullptr;
	if (!AI) return;
	if (Clip != RiderClipAsset || !AI->IsSlotActive(RDRide15Slot))
	{
		RiderMontage = AI->PlaySlotAnimationAsDynamicMontage(Clip, RDRide15Slot, Blend, Blend, Rate, bLoop ? 10000 : 1);
		RiderClipAsset = Clip;
	}
	else if (RiderMontage) AI->Montage_SetPlayRate(RiderMontage, Rate);
}

FString ARDDungeonGenerator::HoofSurface15(const FVector& At) const
{
	// (a town's streets and squares are stone; out in the wilds the ground's own sample: the cobbles and rock hard, a road's bed,
	// sand, mud, snow and a field's earth dirt, the rest grass)
	if (!bWild || IsInTownWalls(At)) return TEXT("Hard");
	if (!IsWildReady()) return TEXT("Grass");
	FRDWSample S; Wild->Sample(At.X / 100.0, At.Y / 100.0, S, false);
	if (S.Cobble > 0.4f || S.Rock > 0.55f) return TEXT("Hard");
	if (S.Road > 0.35f || S.Sand > 0.4f || S.Mud > 0.25f || S.Snow > 0.4f || S.Field > 0.4f) return TEXT("Dirt");
	return TEXT("Grass");
}

bool ARDDungeonGenerator::MountHorse15(ACharacter* C)
{
	UCharacterMovementComponent* CM = C->GetCharacterMovement();
	const FRDRiderClips* RC = RiderClips.Find(CurrentHero);
	FRide15& R = Ride15;
	// (the session's counters kept across a mount, as a dismount keeps them: PR #93's review)
	const FRide15 Keep = R;
	R = FRide15(); R.Mounts = Keep.Mounts + 1; R.Dismounts = Keep.Dismounts;
	R.Jumps = Keep.Jumps; R.Rears = Keep.Rears; R.Hits = Keep.Hits; R.Stops = Keep.Stops; R.Swims = Keep.Swims; R.Falls = Keep.Falls; R.Dust = Keep.Dust; R.Blocked = Keep.Blocked; R.FallsOn = Keep.FallsOn;
	// (from the horse's nearer side: its left is -Y of its actor (the pack's mesh's +X, where its left mount begins))
	const FVector Local = Horse->GetActorTransform().InverseTransformPosition(C->GetActorLocation());
	R.bLeft = Local.Y <= 0.f;
	R.Yaw = Horse->GetActorRotation().Yaw;
	UAnimSequenceBase* Clip = RC ? (R.bLeft ? RC->MountL.Get() : RC->MountR.Get()) : nullptr;
	R.Phase = Clip ? ERide15::Mounting : ERide15::Riding; R.Len = RDRide15Len(Clip);
	bMounted = true;
	Horse->SetBlocking(false);
	// (her movement's own acceleration, braking and turning off: the horse's speed and heading are written into her velocity)
	R.MaxAccelWas = CM->MaxAcceleration; R.BrakeWas = CM->BrakingDecelerationWalking; R.FrictionWas = CM->GroundFriction;
	R.BrakeFrictionWas = CM->BrakingFriction; R.bSepBrakeWas = CM->bUseSeparateBrakingFriction; R.bOrientWas = CM->bOrientRotationToMovement;
	CM->MaxAcceleration = 0.f; CM->BrakingDecelerationWalking = 0.f; CM->GroundFriction = 0.f; CM->BrakingFriction = 0.f;
	CM->bUseSeparateBrakingFriction = true; CM->bOrientRotationToMovement = false;
	CM->Velocity = FVector::ZeroVector;
	JumpWas = CM->JumpZVelocity; CM->JumpZVelocity = 0.f;
	PrimaryActorTick.AddPrerequisite(CM, CM->PrimaryComponentTick);
	MountMeshWas = C->GetMesh()->GetRelativeLocation(); R.MeshRotWas = C->GetMesh()->GetRelativeRotation();
	// (her capsule under the saddle: the clip carries her body up from the side)
	const float Hh = C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	C->SetActorLocationAndRotation(Horse->GetActorLocation() + FVector(0, 0, Hh + 2.f), FRotator(0.f, R.Yaw, 0.f), false, nullptr, ETeleportType::TeleportPhysics);
	if (USpringArmComponent* B = C->FindComponentByClass<USpringArmComponent>()) { BoomArmWas = B->TargetArmLength; BoomOffsetWas = B->TargetOffset; B->TargetArmLength += 120.f; B->TargetOffset.Z += 80.f; }
	PlayerCombat->MountFactor = 1.f; PlayerCombat->RefreshWalkSpeed();
	if (bHorseCall14) PlayerCombat->SetRideHands(true);
	RiderClipNow = NAME_None; RiderClipAsset = nullptr;
	if (Clip) { PlayRider15(C, Clip, false, 1.f, 0.15f); RiderClipNow = R.bLeft ? TEXT("mountl") : TEXT("mountr"); }
	Horse->PlayClip15(TEXT("idle"), HorseDef.Idle, true, 1.f, 0.3f, 0.f); R.Gait = TEXT("idle");
	R.LastHealth = PlayerCombat->GetHealth();
	PlaySoundAt(TEXT("Horse.Mount"), C->GetActorLocation());
	TickRide15(0.f, C);
	PlayerCombat->ShowMessage(TEXT("You ride your horse  (F: get off, the attack: rear, jump: jump)"));
	UE_LOG(LogRDHorse15, Log, TEXT("RDHORSE15 mounting from the %s (%.2f s)"), R.bLeft ? TEXT("left") : TEXT("right"), R.Len);
	return true;
}

bool ARDDungeonGenerator::DismountHorse15(ACharacter* C, bool bNow)
{
	FRide15& R = Ride15;
	if (!C) { bMounted = false; return true; }
	// (the horse gone while she rides (PR #93's review): her movement, mesh and camera still put back, beside nothing)
	if (!Horse) { R.bOffPlaced = false; FinishDismount15(C); return true; }
	const FRDRiderClips* RC = RiderClips.Find(CurrentHero);
	if (bNow || PlayerCombat == nullptr || PlayerCombat->IsDead() || R.bSwim || R.Phase == ERide15::Mounting)
	{
		R.bOffPlaced = false; FinishDismount15(C); return true;
	}
	if (R.Phase == ERide15::Dismounting) return false;
	// (at a gallop she does not jump off: the horse is stopped first, then she gets down)
	if (FMath::Abs(R.Speed) > 120.f || R.bAir || R.bRear) { R.bWantOff = true; return true; }
	// (down on the side with room for her: the side she came up, else the other; her capsule must fit there, on the ground)
	const float Hh = C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight(), Rr = C->GetCapsuleComponent()->GetScaledCapsuleRadius();
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDRide15Off), false, C); Q.AddIgnoredActor(Horse);
	const FVector Right = Horse->GetActorRightVector();
	bool bFound = false;
	for (const bool bLeft : { R.bLeft, !R.bLeft })
	{
		const FVector P = Horse->GetActorLocation() + Right * (bLeft ? -95.f : 95.f) - Horse->GetActorForwardVector() * 10.f;
		FHitResult G;
		if (!GetWorld()->LineTraceSingleByChannel(G, P + FVector(0, 0, 150.f), P - FVector(0, 0, 300.f), ECC_Visibility, Q)) continue;
		const FVector At = G.ImpactPoint + FVector(0, 0, Hh + 3.f);
		if (GetWorld()->OverlapAnyTestByChannel(At, FQuat::Identity, ECC_Pawn, FCollisionShape::MakeCapsule(Rr, Hh), Q)) continue;
		R.bLeft = bLeft; R.OffAt = At; bFound = true; break;
	}
	UAnimSequenceBase* Clip = RC ? (R.bLeft ? RC->DismountL.Get() : RC->DismountR.Get()) : nullptr;
	if (!bFound || !Clip) { R.bOffPlaced = false; FinishDismount15(C); return true; }
	R.Phase = ERide15::Dismounting; R.T = 0.f; R.Len = RDRide15Len(Clip); R.bOffPlaced = true; R.Speed = 0.f;
	PlayRider15(C, Clip, false, 1.f, 0.2f); RiderClipNow = R.bLeft ? TEXT("dismountl") : TEXT("dismountr");
	PlaySoundAt(TEXT("Horse.Dismount"), C->GetActorLocation());
	UE_LOG(LogRDHorse15, Log, TEXT("RDHORSE15 getting down to the %s (%.2f s)"), R.bLeft ? TEXT("left") : TEXT("right"), R.Len);
	return true;
}

void ARDDungeonGenerator::FinishDismount15(ACharacter* C)
{
	FRide15& R = Ride15;
	bMounted = false;
	if (C)
	{
		USkeletalMeshComponent* M = C->GetMesh();
		UCharacterMovementComponent* CM = C->GetCharacterMovement();
		const float Hh = C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
		M->SetRelativeLocationAndRotation(MountMeshWas, R.MeshRotWas);
		const bool bDeadNow = PlayerCombat && PlayerCombat->IsDead();
		if (UAnimInstance* AI = M->GetAnimInstance(); AI && !bDeadNow) AI->StopSlotAnimation(0.25f, RDRide15Slot);
		if (USpringArmComponent* B = C->FindComponentByClass<USpringArmComponent>()) { B->TargetArmLength = BoomArmWas; B->TargetOffset = BoomOffsetWas; }
		CM->MaxAcceleration = R.MaxAccelWas; CM->BrakingDecelerationWalking = R.BrakeWas; CM->GroundFriction = R.FrictionWas;
		CM->BrakingFriction = R.BrakeFrictionWas; CM->bUseSeparateBrakingFriction = R.bSepBrakeWas; CM->bOrientRotationToMovement = R.bOrientWas;
		CM->JumpZVelocity = JumpWas; CM->Velocity = FVector::ZeroVector;
		PrimaryActorTick.RemovePrerequisite(CM, CM->PrimaryComponentTick);
		// (down where the clip put her feet, beside the horse; else beside it as before (a death, a swim, no room))
		if (R.bOffPlaced) C->SetActorLocation(R.OffAt, false, nullptr, ETeleportType::TeleportPhysics);
		else if (Horse)
		{
			const FVector Spot = HorseSpotBeside(C);
			C->SetActorLocation(Spot + FVector(0, 0, Hh + 3.f), false, nullptr, ETeleportType::TeleportPhysics);
		}
	}
	if (Horse)
	{
		Horse->Pivot->SetRelativeLocationAndRotation(FVector::ZeroVector, FRotator::ZeroRotator);
		// (a horse left in the water is put on the bank beside her)
		if (R.bSwim && C) Horse->SetActorLocation(HorseSpotBeside(C));
		Horse->PlayFor(0.f);
		Horse->SetBlocking(false);          // (on again once she is clear of it: TickHorse)
	}
	if (PlayerCombat) { PlayerCombat->MountFactor = 1.f; PlayerCombat->RefreshWalkSpeed(); if (PlayerCombat->bRideHands) PlayerCombat->SetRideHands(false); }
	RiderClipNow = NAME_None; RiderClipAsset = nullptr;
	const int32 Mounts = R.Mounts, Dismounts = R.Dismounts + 1;
	const FRide15 Keep = R;
	R = FRide15();
	R.Mounts = Mounts; R.Dismounts = Dismounts;
	R.Jumps = Keep.Jumps; R.Rears = Keep.Rears; R.Hits = Keep.Hits; R.Stops = Keep.Stops; R.Swims = Keep.Swims; R.Falls = Keep.Falls; R.Dust = Keep.Dust; R.Blocked = Keep.Blocked; R.FallsOn = Keep.FallsOn;
	TickReins14();
	UE_LOG(LogRDHorse15, Log, TEXT("RDHORSE15 down"));
}

bool ARDDungeonGenerator::RearHorse()
{
	FRide15& R = Ride15;
	if (!bMounted || !Horse || !HorseDef.bPack || R.Phase != ERide15::Riding || R.bAir || R.bSwim || R.bRear || !HorseDef.Rear) return false;
	if (FMath::Abs(R.Speed) > HorseDef.GallopEdge) return false;          // (not at a gallop: it would throw her)
	R.bRear = true; R.ActT = RDRide15Len(HorseDef.Rear); ++R.Rears;
	Horse->PlayClip15(TEXT("rear"), HorseDef.Rear, false, 1.f, 0.2f, 0.f);
	if (ACharacter* C = Cast<ACharacter>(UGameplayStatics::GetPlayerPawn(this, 0)))
		if (const FRDRiderClips* RC = RiderClips.Find(CurrentHero); RC && RC->Rear) { PlayRider15(C, RC->Rear, false, RDRide15Len(RC->Rear) / FMath::Max(R.ActT, 0.1f), 0.2f); RiderClipNow = TEXT("rear"); }
	PlaySoundAt(TEXT("Horse.Neigh"), Horse->GetActorLocation() + FVector(0, 0, 150.f));
	return true;
}

void ARDDungeonGenerator::TickRide15(float Dt, ACharacter* C)
{
	FRide15& R = Ride15;
	const FRDHorseDef& D = HorseDef;
	UCharacterMovementComponent* CM = C->GetCharacterMovement();
	USkeletalMeshComponent* M = C->GetMesh();
	const FRDRiderClips* RC = RiderClips.Find(CurrentHero);
	URDHorseAnimInstance* HA = Horse->GetAnim15();
	const float Hh = C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	const FVector Feet = C->GetActorLocation() - FVector(0, 0, Hh);
	R.T += Dt;
	if (PlayerCombat->IsBusyForMount()) PlayerCombat->SetBlocking(false);
	if (PlayerCombat->bRideHands) PlayerCombat->SetRideHands(true);
	auto Rider = [&](UAnimSequenceBase* Clip, FName Name, bool bLoop, float Rate, float Blend) { if (Clip) { PlayRider15(C, Clip, bLoop, Rate, Blend); RiderClipNow = Name; } };
	// ---- getting on and off: the horse stands; her body eased from the ground (her lowest foot on it) to the seat
	float SeatShare = 1.f;
	if (R.Phase == ERide15::Mounting || R.Phase == ERide15::Dismounting)
	{
		CM->Velocity = FVector::ZeroVector; R.Speed = 0.f;
		const float S = R.Len > 0.f ? FMath::Clamp(R.T / R.Len, 0.f, 1.f) : 1.f;
		SeatShare = R.Phase == ERide15::Mounting ? FMath::SmoothStep(0.25f, 0.85f, S) : 1.f - FMath::SmoothStep(0.15f, 0.75f, S);
		// (the ride's clips take over a little before the getting on's ends: its blend out would show her standing pose between them)
		if (R.T >= R.Len - (R.Phase == ERide15::Mounting ? 0.15f : 0.f))
		{
			if (R.Phase == ERide15::Dismounting) { FinishDismount15(C); return; }
			R.Phase = ERide15::Riding; SeatShare = 1.f;
			UE_LOG(LogRDHorse15, Log, TEXT("RDHORSE15 mounted"));
		}
	}
	// ---- the water: it swims where she would (the face SwimDepth over her feet)
	float Fz = 0.f;
	const bool bWater = WaterFaceAt(C->GetActorLocation(), Fz);
	const bool bSwimNow = bWater && Feet.Z < Fz - (R.bSwim ? D.SwimDepth - 15.f : D.SwimDepth) && D.Swim;
	if (bSwimNow && !R.bSwim) { R.bSwim = true; ++R.Swims; PlaySoundAt(TEXT("Horse.Swim"), FVector(Feet.X, Feet.Y, Fz)); }
	else if (!bSwimNow && R.bSwim) R.bSwim = false;
	CM->JumpZVelocity = R.Phase == ERide15::Riding && !R.bSwim && !R.bRear && !R.bAir ? D.JumpZ : 0.f;
	// ---- a hit taken: the horse shies from the side it came from
	const float Hp = PlayerCombat->GetHealth();
	if (R.LastHealth >= 0.f && Hp < R.LastHealth - 0.5f && D.Hits.Num() >= 4 && !R.bRear && !R.bAir && R.Phase == ERide15::Riding)
	{
		const ARDMonster* Near = nullptr; float Best = 1200.f;
		for (const ARDMonster* Mo : GetMonsters()) if (Mo && !Mo->IsDead()) { const float Dd = FVector::Dist(Mo->GetActorLocation(), Feet); if (Dd < Best) { Best = Dd; Near = Mo; } }
		int32 K = 0;
		if (Near)
		{
			const FVector L = Horse->GetActorTransform().InverseTransformVectorNoScale(Near->GetActorLocation() - Feet);
			const float A = FMath::RadiansToDegrees(FMath::Atan2(L.Y, L.X));
			K = FMath::Abs(A) <= 45.f ? 0 : FMath::Abs(A) >= 135.f ? 1 : A < 0.f ? 2 : 3;          // (front, back, left, right)
		}
		if (UAnimSequenceBase* Hc = D.Hits[K])
		{
			Horse->PlayClip15(TEXT("hit"), Hc, false, 1.f, 0.1f, 0.f);
			R.HitT = RDRide15Len(Hc); ++R.Hits;
			PlaySoundAt(TEXT("Horse.Hit"), Horse->GetActorLocation() + FVector(0, 0, 140.f));
		}
	}
	R.LastHealth = Hp;
	// ---- the ride: the heading and the speed
	if (R.Phase == ERide15::Riding)
	{
		const FVector In3 = C->GetLastMovementInputVector();
		const FVector2D In(In3.X, In3.Y);
		const float Mag = FMath::Min(In.Size(), 1.f);
		const bool bRun = PlayerCombat->IsRunMode();
		const APlayerController* PCo = Cast<APlayerController>(C->GetController());
		const float CamYaw = PCo ? PCo->GetControlRotation().Yaw : R.Yaw;
		float Want = 0.f; bool bHardStop = false;
		const bool bHeld = R.bRear || R.bWantOff || R.HitT > 0.f;
		if (!bHeld && Mag > 0.08f)
		{
			const float DirYaw = FMath::RadiansToDegrees(FMath::Atan2(In.Y, In.X));
			const float dA = FMath::FindDeltaAngleDegrees(R.Yaw, DirYaw);
			// (backed when the stick is held back with the camera behind it: a turn toward the camera is a turn round)
			const bool bBackNow = FMath::Abs(dA) > 135.f && FMath::Abs(FMath::FindDeltaAngleDegrees(R.Yaw, CamYaw)) < 60.f && (R.bBack || R.Speed < 150.f);
			R.bBack = bBackNow;
			if (R.bBack) Want = -D.TopBack * FMath::Min(Mag * 2.f, 1.f);
			else
			{
				const float Turn = FMath::Lerp(D.TurnSlow, D.TurnFast, FMath::Clamp(FMath::Abs(R.Speed) / FMath::Max(D.TopRun, 1.f), 0.f, 1.f)) * (R.bSwim ? 0.6f : 1.f);
				R.Yaw = FRotator::NormalizeAxis(R.Yaw + FMath::Clamp(dA, -Turn * Dt, Turn * Dt));
				// (the walk mode: her input is her walk's share of her run (about a third, MoveScale): a brisk walk at most; the run mode:
				// a walk on a small push, else the gallop from half again its edge up to its top)
				if (!bRun) Want = D.TopWalk * FMath::Clamp(Mag * 3.f, 0.f, 1.f);
				else Want = Mag < 0.6f ? D.TopWalk * Mag / 0.6f : FMath::Lerp(D.GallopEdge * 1.5f, D.TopRun, (Mag - 0.6f) / 0.4f);
				// (slower into a sharp turn; a horse standing walks round to turn rather than spin on the spot)
				Want *= FMath::Lerp(1.f, 0.55f, FMath::Clamp((FMath::Abs(dA) - 30.f) / 120.f, 0.f, 1.f));
				if (FMath::Abs(dA) > 25.f) Want = FMath::Max(Want, 70.f);
			}
		}
		else if (!bHeld) R.bBack = R.bBack && R.Speed < -5.f;
		if (R.bSwim) Want = FMath::Clamp(Want, -0.f, D.TopSwim);
		// (let go at a gallop: the sudden stop, harder than an easing)
		if (Mag <= 0.08f && R.Speed > D.GallopEdge && !R.bSwim && !R.bAir) { bHardStop = true; }
		if (R.bStop && R.Speed < 120.f) R.bStop = false;
		if (bHardStop && !R.bStop && D.Stop)
		{
			R.bStop = true; ++R.Stops;
			Horse->PlayClip15(TEXT("stop"), D.Stop, true, 1.f, 0.25f, 0.f);
			// (counted only when made: PR #93's review)
			if (D.DustStop) { UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, D.DustStop, Feet + Horse->GetActorForwardVector() * 40.f, Horse->GetActorRotation(), FVector(D.DustScale), true, true); ++R.Dust; }
			PlaySoundAt(TEXT("Horse.Snort"), Horse->GetActorLocation() + FVector(0, 0, 140.f));
		}
		if (!R.bAir)
		{
			const float Up = R.Speed < D.TopWalk * 1.1f ? D.Accel * 1.6f : D.Accel;          // (a walk is reached quickly)
			// (the water takes a gallop's speed at once: 888 horse15's first swim went in at 12 m/s and swam at 11.6, eased down at the
			// land's rate)
			const float Down = R.bSwim ? D.HardStop * 3.f : R.bStop ? D.HardStop : R.bRear ? D.HardStop : D.Decel;
			const float Dv = Want - R.Speed;
			const bool bFaster = (R.Speed >= 0.f && Dv > 0.f) || (R.Speed < 0.f && Dv < 0.f);
			R.Speed += FMath::Clamp(Dv, -(bFaster ? Up : Down) * Dt, (bFaster ? Up : Down) * Dt);
		}
		// (short of a wall: a sweep from its chest ahead (or its rump behind, backing), the ground and slopes it can walk passed by)
		{
			const FVector Fw = FRotator(0.f, R.Yaw, 0.f).Vector();
			const float Sgn = R.Speed >= 0.f ? 1.f : -1.f;
			const FVector From = Feet + FVector(0, 0, 125.f);
			const float Body = 105.f, Reach = Body + FMath::Abs(R.Speed) * 0.25f + 10.f;
			FCollisionQueryParams Q(SCENE_QUERY_STAT(RDRide15Ahead), false, C); Q.AddIgnoredActor(Horse);
			IgnoreAllies15(Q);          // (her allies are solid to her now: the ride passes them as it did (PR #94's review))
			FHitResult Hit;
			if (FMath::Abs(R.Speed) > 5.f && GetWorld()->SweepSingleByChannel(Hit, From, From + Fw * Sgn * Reach, FQuat::Identity, ECC_Pawn, FCollisionShape::MakeSphere(28.f), Q)
				&& Hit.ImpactNormal.Z < 0.6f)
			{
				const float Room = FMath::Max(Hit.Distance - Body, 0.f);
				const float Cap = Room / 0.25f;
				if (FMath::Abs(R.Speed) > Cap) { R.Speed = Sgn * Cap; ++R.Blocked; }
			}
			// (held up by what her capsule met: its speed is what it moved)
			if (CM->IsMovingOnGround() && FMath::Abs(R.Speed) > 150.f && Dt > 0.f)
			{
				const float Moved = FVector::DotProduct(C->GetVelocity(), Fw);
				if (FMath::Abs(Moved) < FMath::Abs(R.Speed) * 0.5f) R.Speed = FMath::Sign(R.Speed) * FMath::Max(FMath::Abs(Moved), 0.f);
			}
			C->SetActorRotation(FRotator(0.f, R.Yaw, 0.f));
			if (CM->IsMovingOnGround()) CM->Velocity = Fw * R.Speed;
		}
		// ---- the air: a jump taken (her jump's button, on the ground) and the landing
		if (CM->IsFalling() && !R.bAir)
		{
			R.bAir = true; R.bJumped = CM->Velocity.Z > 100.f;
			if (R.bJumped)
			{
				++R.Jumps;
				if (D.JumpStart) Horse->PlayClip15(TEXT("jump"), D.JumpStart, false, 1.f, 0.1f, 0.f);
				if (RC) Rider(RC->JumpStart, TEXT("jump"), false, 1.f, 0.1f);
				PlaySoundAt(TEXT("Horse.Jump"), Feet);
			}
		}
		else if (R.bAir && !CM->IsFalling())
		{
			R.bAir = false;
			if (D.JumpLand) { Horse->PlayClip15(TEXT("land"), D.JumpLand, false, 1.f, 0.1f, 0.f); R.ActT = RDRide15Len(D.JumpLand); }
			if (RC && RC->JumpLand) Rider(RC->JumpLand, TEXT("land"), false, 1.f, 0.1f);
			PlaySoundAt(*FString::Printf(TEXT("Horse.Hoof.%s"), *HoofSurface15(Feet)), Feet, 1.4f);
			if (D.DustStop && HoofSurface15(Feet) != TEXT("Hard")) { UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, D.DustStop, Feet, Horse->GetActorRotation(), FVector(D.DustScale), true, true); ++R.Dust; }
			R.Gait = TEXT("land");
		}
		if (R.bAir && R.bJumped && HA && HA->IsClipDone() && Horse->ClipNow == TEXT("jump") && D.JumpLoop)
		{
			Horse->PlayClip15(TEXT("jumploop"), D.JumpLoop, true, 1.f, 0.1f, 0.f);
			if (RC) Rider(RC->JumpLoop, TEXT("jumploop"), true, 1.f, 0.1f);
		}
		if (R.bRear) { R.ActT -= Dt; if (R.ActT <= 0.f || (HA && HA->IsClipDone())) { R.bRear = false; R.Gait = NAME_None; } }
		if (R.HitT > 0.f) { R.HitT -= Dt; if (R.HitT <= 0.f) R.Gait = NAME_None; }
		if (R.Gait == TEXT("land")) { R.ActT -= Dt; if (R.ActT <= 0.f) R.Gait = NAME_None; }
		if (R.bWantOff && FMath::Abs(R.Speed) < 60.f && !R.bAir && !R.bRear) { R.bWantOff = false; R.Speed = 0.f; DismountHorse15(C, false); }
	}
	// ---- the horse's clip: its gait by its speed (each played at the rate its hooves keep to the ground), unless a one-off plays
	const float As = FMath::Abs(R.Speed);
	const bool bOneOff = R.bRear || R.HitT > 0.f || (R.bAir && R.bJumped) || R.Gait == TEXT("land") || R.bStop;
	if (!bOneOff)
	{
		FName G = TEXT("idle"); UAnimSequenceBase* Clip = D.Idle; float Rate = 1.f; bool bPhase = true;
		const bool bWasRun = R.Gait == TEXT("run");
		if (R.bSwim) { if (As > 40.f && D.Swim) { G = TEXT("swim"); Clip = D.Swim; Rate = FMath::Clamp(As / FMath::Max(D.SwimClipSpeed, 1.f), 0.5f, 1.5f); } else if (D.SwimIdle) { G = TEXT("swimidle"); Clip = D.SwimIdle; } }
		else if (R.Speed < -10.f && D.Back) { G = TEXT("back"); Clip = D.Back; Rate = FMath::Clamp(As / FMath::Max(D.BackClipSpeed, 1.f), 0.4f, 1.6f); }
		else if (As > 15.f)
		{
			const float Edge = D.GallopEdge * (bWasRun ? 0.9f : 1.f);
			if (As >= Edge && D.Run) { G = TEXT("run"); Clip = D.Run; Rate = FMath::Clamp(As / FMath::Max(D.RunClipSpeed, 1.f), 0.55f, 1.8f); }
			else if (D.Walk) { G = TEXT("walk"); Clip = D.Walk; Rate = FMath::Clamp(As / FMath::Max(D.WalkClipSpeed, 1.f), 0.35f, 2.2f); }
		}
		else
		{
			// (standing: now and then one of its idles, then back to its own)
			R.IdleT += Dt; bPhase = false;
			if (R.Gait == TEXT("idlevar")) { if (HA && HA->IsClipDone()) { R.IdleT = 0.f; } else { G = TEXT("idlevar"); Clip = nullptr; } }
			else if (R.IdleT > 9.f && D.Idles.Num() > 0)
			{
				UAnimSequenceBase* V = D.Idles[FMath::Abs(FMath::FloorToInt(GetWorld()->GetTimeSeconds() * 7.f)) % D.Idles.Num()];
				if (V) { Horse->PlayClip15(TEXT("idlevar"), V, false, 1.f, 0.5f, 0.f); R.Gait = TEXT("idlevar"); Clip = nullptr; G = TEXT("idlevar"); }
			}
			R.SnortT -= Dt;
			if (R.SnortT <= 0.f) { R.SnortT = 10.f + FMath::Fmod(GetWorld()->GetTimeSeconds() * 3.7f, 9.f); PlaySoundAt(TEXT("Horse.Snort"), Horse->GetActorLocation() + FVector(0, 0, 140.f)); }
		}
		if (As > 15.f) R.IdleT = 0.f;
		if (Clip)
		{
			const bool bGaits = (G == TEXT("walk") || G == TEXT("run")) && (R.Gait == TEXT("walk") || R.Gait == TEXT("run"));
			Horse->PlayClip15(G, Clip, true, Rate, G == R.Gait ? 0.f : 0.35f, bGaits && bPhase ? -1.f : 0.f);
			Horse->RateNow = Rate;
			R.Gait = G;
		}
	}
	// ---- the hooves: heard where each lands, by the ground under it; dust thrown on dirt
	if (HA && (Horse->ClipNow == TEXT("walk") || Horse->ClipNow == TEXT("run") || Horse->ClipNow == TEXT("back")) && Dt > 0.f)
	{
		// (backing has landings of its own, measured on the backing clip (933): PR #93's review; the walk's if none were written)
		const TArray<float>& Falls = Horse->ClipNow == TEXT("run") ? D.RunFalls
			: (Horse->ClipNow == TEXT("back") && D.BackFalls.Num() > 0) ? D.BackFalls : D.WalkFalls;
		const float P0 = HA->GetPhaseBefore(), P1 = HA->GetPhase();
		for (int32 K = 0; K < Falls.Num() && K < D.HoofBones.Num(); ++K)
		{
			if (!RDRide15Crossed(P0, P1, Falls[K])) continue;
			const FVector At = Horse->Body->GetSocketLocation(D.HoofBones[K]);
			const FString Surf = HoofSurface15(At);
			const bool bGallop = Horse->ClipNow == TEXT("run");
			PlaySoundAt(*FString::Printf(TEXT("Horse.Hoof.%s"), *Surf), At, bGallop ? 1.15f : 0.8f);
			++R.Falls; ++R.FallsOn.FindOrAdd(Surf); R.Surface = Surf;
			if (Surf == TEXT("Dirt") || (bGallop && Surf == TEXT("Grass") && (K & 1)))
				if (UNiagaraSystem* Fx = bGallop && D.DustGallop ? D.DustGallop.Get() : D.DustStep.Get())
				{
					UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, Fx, At, Horse->GetActorRotation(), FVector(D.DustScale * (bGallop ? 1.f : 0.6f)), true, true);
					++R.Dust;
				}
		}
	}
	// ---- the horse under her: at her feet, her heading; pitched to the ground under its front and hind hooves; lifted to swim
	{
		Horse->SetActorLocationAndRotation(Feet, FRotator(0.f, R.Yaw, 0.f));
		float WantPitch = 0.f, WantLift = 0.f;
		if (R.bSwim) WantLift = FMath::Max(0.f, Fz + D.SwimLift - Feet.Z);
		else if (!R.bAir)
		{
			FCollisionQueryParams Q(SCENE_QUERY_STAT(RDRide15Pitch), false, C); Q.AddIgnoredActor(Horse);
			const FVector Fw = FRotator(0.f, R.Yaw, 0.f).Vector();
			FHitResult Hf, Hb;
			// (the slope over the horse's whole length, 2.2 m: the ground's bumps under two points 1.7 m apart nodded the body each
			// frame, and a planted hoof 1.1 m from the pivot moved with it (888 gait12's walk read a slide of half the speed))
			const FVector Pf = Feet + Fw * 110.f, Pb = Feet - Fw * 110.f;
			if (GetWorld()->LineTraceSingleByChannel(Hf, Pf + FVector(0, 0, 120.f), Pf - FVector(0, 0, 160.f), ECC_Visibility, Q)
				&& GetWorld()->LineTraceSingleByChannel(Hb, Pb + FVector(0, 0, 120.f), Pb - FVector(0, 0, 160.f), ECC_Visibility, Q))
				WantPitch = FMath::Clamp(FMath::RadiansToDegrees(FMath::Atan2(Hf.ImpactPoint.Z - Hb.ImpactPoint.Z, 220.f)), -22.f, 22.f);
		}
		const float K = FMath::Min(1.f, Dt * 2.5f);
		R.Pitch += (WantPitch - R.Pitch) * K; R.Lift += (WantLift - R.Lift) * FMath::Min(1.f, Dt * 3.f);
		Horse->Pivot->SetRelativeLocationAndRotation(FVector(0, 0, R.Lift), FRotator(R.Pitch, 0.f, 0.f));
	}
	// ---- her clip on it: by the horse's gait, at its stride; and her body carried by the horse's rider socket
	if (R.Phase == ERide15::Riding && RC && !R.bRear && !(R.bAir && R.bJumped) && RiderClipNow != TEXT("land"))
	{
		const FName G = R.Gait;
		const bool bFast = G == TEXT("run");
		UAnimSequenceBase* Clip = bFast ? RC->Run.Get() : (G == TEXT("walk") || G == TEXT("back") || G == TEXT("swim")) ? RC->Walk.Get() : RC->Idle.Get();
		if (Clip)
		{
			const float Strides = Horse->GetStridesASecond();
			const float Rate = Strides > 0.f && G != TEXT("swim") ? FMath::Clamp(RDRide15Len(Clip) * Strides, 0.3f, 3.f) : 1.f;
			Rider(Clip, bFast ? FName(TEXT("run")) : G == TEXT("idle") || G == TEXT("idlevar") || G == TEXT("swimidle") ? FName(TEXT("idle")) : FName(TEXT("walk")), true, Rate, 0.25f);
		}
	}
	else if (RiderClipNow == TEXT("land") && R.Gait != TEXT("land")) RiderClipNow = NAME_None;
	{
		// (her mesh's turn: the pack's rider's mesh faces its +Y as the horse's does; hers faces whatever her relative turn says)
		const FTransform Fr = RiderFrame15();
		const FQuat W = Fr.GetRotation() * FRotator(0.f, 90.f, 0.f).Quaternion() * R.MeshRotWas.Quaternion();
		const FVector Off = RC ? FMath::Lerp(RC->GroundOffset, RC->SeatOffset, SeatShare) : FVector::ZeroVector;
		M->SetWorldLocationAndRotation(Fr.GetLocation() + W.RotateVector(Off), W);
	}
	TickReins14();
}

FString ARDDungeonGenerator::GetRideLine15() const
{
	const FRide15& R = Ride15;
	const ACharacter* C = Cast<ACharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
	float SeatErr = -1.f, HandL = -1.f, HandR = -1.f;
	if (C && Horse && bMounted && R.Phase == ERide15::Riding)
	{
		const USkeletalMeshComponent* M = C->GetMesh();
		const FTransform Fr = RiderFrame15();
		SeatErr = FVector::Dist(M->GetSocketLocation(TEXT("pelvis")), Fr.TransformPosition(HorseDef.SeatPelvis));
		if (Horse->Body->DoesSocketExist(TEXT("LHandIK"))) HandL = FVector::Dist(M->GetSocketLocation(TEXT("hand_l")), Horse->Body->GetSocketLocation(TEXT("LHandIK")));
		if (Horse->Body->DoesSocketExist(TEXT("RHandIK"))) HandR = FVector::Dist(M->GetSocketLocation(TEXT("hand_r")), Horse->Body->GetSocketLocation(TEXT("RHandIK")));
	}
	const TCHAR* Ph = R.Phase == ERide15::Mounting ? TEXT("mounting") : R.Phase == ERide15::Riding ? TEXT("riding") : R.Phase == ERide15::Dismounting ? TEXT("dismounting") : TEXT("none");
	const int32* Fg = R.FallsOn.Find(TEXT("Grass")); const int32* Fd = R.FallsOn.Find(TEXT("Dirt")); const int32* Fh = R.FallsOn.Find(TEXT("Hard"));
	return FString::Printf(TEXT("%s|%.0f|%.1f|%s|%.2f|%.2f|%.1f|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%s|%.1f|%.1f|%.1f|%d|%d|%d|%d|%d|%d|%d|%.0f"),
		Ph, R.Speed, R.Yaw, Horse ? *Horse->ClipNow.ToString() : TEXT("none"), Horse ? Horse->RateNow : 0.f, Horse ? Horse->GetStridesASecond() : 0.f, R.Pitch,
		R.bSwim ? 1 : 0, R.bAir ? 1 : 0, R.bRear ? 1 : 0, R.Jumps, R.Rears, R.Hits, R.Stops, R.Swims, R.Falls, R.Dust, *R.Surface, SeatErr, HandL, HandR,
		R.bBack ? 1 : 0, R.Mounts, R.Dismounts, R.Blocked, Fg ? *Fg : 0, Fd ? *Fd : 0, Fh ? *Fh : 0, R.Lift);
}
