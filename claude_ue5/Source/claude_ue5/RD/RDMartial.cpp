// The Martial Artist (the user's of 2026-10-28; mistward_castle and martial_arts): her hero's data on the generator
// (FRDHeroDef: TypeBonus, DexterityTypes, DashClip, LockedWeapons), read here:
//   StartWeaponsOf      her card's weapons (her fists, two chi attacks), and with bUnlockAll every locked one
//   UnlockHeroWeapons   a tier's boss slain: the next two of her chi attacks are hers (OnMonsterKilled)
//   TypeBonusOf, DexterityBoosts   her knives' share more; the Dexterity ring on her fists and knives (GetBonusOf)
//   StartDash           forward at the monster ahead (stopping short of it), then her attack (the roll's machinery)
//   TickOneRoom         martial_arts: monsters of tier 1 in the one room, one more a while after one falls
#include "RD/RDCombat.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDMonster.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/RootMotionSource.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimSequenceBase.h"
#include "Kismet/GameplayStatics.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDMartial, Log, All);
static const FName RDMaSlot(TEXT("DefaultSlot"));          // (her AnimBP's slot: RDCombat.cpp's RDCombatSlot)

// ------------------------------------------------------------------------------------------------ her weapons
void ARDDungeonGenerator::StartWeaponsOf(const FRDHeroDef& H, TArray<FRDWeaponDef>& Out) const
{
	Out = H.Weapons;
	if (bUnlockAll) Out.Append(H.LockedWeapons);
}

int32 ARDDungeonGenerator::UnlockHeroWeapons(int32 Count)
{
	const FRDHeroDef* H = FindHero(CurrentHero);
	if (!H || bUnlockAll) return 0;
	int32 Added = 0;
	while (Added < Count && WeaponsUnlocked < H->LockedWeapons.Num())
	{
		const FRDWeaponDef& W = H->LockedWeapons[WeaponsUnlocked++];
		if (Weapons.ContainsByPredicate([&W](const FRDWeaponDef& X) { return X.Name == W.Name; })) continue;
		Weapons.Add(W); ++Added;
		UE_LOG(LogRDMartial, Log, TEXT("RDMARTIAL unlocked %s (%d of %d)"), *W.Name.ToString(), WeaponsUnlocked, H->LockedWeapons.Num());
	}
	if (Added > 0 && PlayerCombat) { PlayerCombat->SyncWear(); PlayerCombat->UpdateManaShares(); }
	return Added;
}

float ARDDungeonGenerator::TypeBonusOf(const FString& Type) const
{
	const FRDHeroDef* H = Type.IsEmpty() ? nullptr : FindHero(CurrentHero);
	if (!H) return 0.f;
	for (const TPair<FString, float>& P : H->TypeBonus) if (P.Key.Equals(Type, ESearchCase::IgnoreCase)) return P.Value;
	return 0.f;
}

bool ARDDungeonGenerator::DexterityBoosts(const FString& Type) const
{
	const FRDHeroDef* H = Type.IsEmpty() ? nullptr : FindHero(CurrentHero);
	return H && H->DexterityTypes.ContainsByPredicate([&Type](const FString& T) { return T.Equals(Type, ESearchCase::IgnoreCase); });
}

// ------------------------------------------------------------------------------------------------ the dash
bool URDCombatComponent::StartDash()
{
	ACharacter* C = Cast<ACharacter>(GetOwner());
	USkeletalMeshComponent* M = Body();
	UAnimInstance* AI = M ? M->GetAnimInstance() : nullptr;
	if (!C || !AI || !Generator || !Generator->DashClip || bDead || RollTime >= 0.f || bInventoryOpen || bCraftOpen) return false;
	const float Now = GetWorld()->GetTimeSeconds();
	UCharacterMovementComponent* CM = C->GetCharacterMovement();
	if (Now < RollReadyAt || !CM->IsMovingOnGround()) return false;
	// (the way she is moved, else the way she faces; the nearest monster within DashSeek within 60 degrees of it is the one
	// she dashes at, and she stops short of it by its size, hers and half her weapon's reach)
	FVector Fw = CM->GetCurrentAcceleration() * FVector(1, 1, 0);
	if (Fw.IsNearlyZero()) Fw = C->GetActorForwardVector() * FVector(1, 1, 0);
	Fw = Fw.GetSafeNormal();
	const FVector L = C->GetActorLocation();
	ARDMonster* Best = nullptr; float BestD = Generator->DashSeek;
	for (ARDMonster* Mo : Generator->GetMonsters())
	{
		if (!IsValid(Mo) || Mo->IsDead() || Mo->IsAlly()) continue;
		const FVector D = (Mo->GetActorLocation() - L) * FVector(1, 1, 0);
		const float Dist = D.Size();
		if (Dist < BestD && FMath::Abs(Mo->GetActorLocation().Z - L.Z) < 260.f && FVector::DotProduct(D.GetSafeNormal(), Fw) > 0.5f) { BestD = Dist; Best = Mo; }
	}
	FVector Dir = Fw; float Len = Generator->DashDistance;
	if (Best)
	{
		const FVector D = (Best->GetActorLocation() - L) * FVector(1, 1, 0);
		Dir = D.GetSafeNormal();
		const float Reach = Weapon() && !Weapon()->bSpell ? Weapon()->Reach : 150.f;
		Len = FMath::Clamp(D.Size() - Best->GetCapsuleComponent()->GetScaledCapsuleRadius() - C->GetCapsuleComponent()->GetScaledCapsuleRadius() - 0.5f * Reach,
			0.f, Generator->DashDistance);
	}
	if (Dir.IsNearlyZero()) return false;
	if (AttackTime >= 0.f) EndAttack();
	C->SetActorRotation(FRotator(0.f, Dir.Rotation().Yaw, 0.f));
	UAnimSequenceBase* Clip = Generator->DashClip.Get();
	AI->PlaySlotAnimationAsDynamicMontage(Clip, RDMaSlot, 0.05f, 0.12f, 1.f, 1, -1.f, 0.f);
	RollLen = Clip->GetPlayLength(); RollTime = 0.f; bRollBack = false; bDashing = true;
	if (Len > 5.f)
	{
		TSharedPtr<FRootMotionSource_ConstantForce> F = MakeShared<FRootMotionSource_ConstantForce>();
		F->InstanceName = TEXT("RDDash");
		F->AccumulateMode = ERootMotionAccumulateMode::Override;
		F->Settings.SetFlag(ERootMotionSourceSettingsFlags::IgnoreZAccumulate);
		F->Priority = 5;
		F->Duration = RollLen * 0.72f;
		F->Force = Dir * (Len / F->Duration);
		F->FinishVelocityParams.Mode = ERootMotionFinishVelocityMode::ClampVelocity;
		F->FinishVelocityParams.ClampVelocity = 60.f;
		RollSourceId = CM->ApplyRootMotionSource(F);
	}
	if (AController* Ctl = C->GetController()) { Ctl->SetIgnoreMoveInput(true); bRollIgnoringMove = true; }
	++Dashes; LastDashLength = Len; LastDashTarget = Best;
	Generator->PlaySoundAt(TEXT("Player.Roll"), C->GetActorLocation());
	UE_LOG(LogRDMartial, Log, TEXT("RDMARTIAL dash %.0f cm%s"), Len, Best ? *FString::Printf(TEXT(" at %s"), *Best->MonsterName.ToString()) : TEXT(""));
	return true;
}

// ------------------------------------------------------------------------------------------------ martial_arts: one room
void ARDDungeonGenerator::TickOneRoom(float Dt)
{
	OneRoomLive.RemoveAll([](const TWeakObjectPtr<ARDMonster>& M) { return !M.IsValid() || M->IsDead(); });
	const float Now = GetWorld()->GetTimeSeconds();
	if (OneRoomLive.Num() >= OneRoomMonsters) { OneRoomNext = Now + OneRoomRespawn; return; }
	if (Now < OneRoomNext) return;
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S || S->IsBuilding()) return;
	const int32 Room = S->RoomAt(GetStartRoomCenter());
	TArray<FVector> Free = S->GetRoomFreeTiles(Room);
	TArray<int32> Kinds; MonsterKindsFor(FIntPoint::ZeroValue, Kinds);
	if (Free.Num() == 0 || Kinds.Num() == 0) return;
	// (the free tile farthest from her of a few, so a monster is not made on top of her)
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	const FVector HerAt = Her ? Her->GetActorLocation() : GetStartRoomCenter();
	FVector At = Free[0]; float Far = -1.f;
	for (int32 K = 0; K < 5; ++K)
	{
		const FVector& P = Free[(OneRoomSpawned * 7 + K * 3) % Free.Num()];
		const float D = FVector::Dist2D(P, HerAt);
		if (D > Far) { Far = D; At = P; }
	}
	const int32 Kind = Kinds[OneRoomSpawned % Kinds.Num()];
	if (ARDMonster* Mo = SpawnMonsterKind(Kind, At, 1, 1.f, 1.f, 1.f))
	{
		OneRoomLive.Add(Mo); ++OneRoomSpawned;
		UE_LOG(LogRDMartial, Log, TEXT("RDMARTIAL the room's monster %d: %s"), OneRoomSpawned, *Mo->MonsterName.ToString());
	}
	OneRoomNext = Now + (OneRoomLive.Num() < OneRoomMonsters ? 0.4f : OneRoomRespawn);
}
