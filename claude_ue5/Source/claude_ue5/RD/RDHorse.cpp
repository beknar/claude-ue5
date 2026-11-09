// The ridable horse (the user's list of 2026-11-08b, docs/improvements9.txt, its eighth phase; RDHorse.h, 913): bought at a town's
// stable by its gate (the stable's own horse stands there until it is hers), called to her side at the stable, mounted and left
// with F. Mounted, she rides it: it goes under her where she goes (her capsule still the one that moves, so everything that
// keys on her pawn holds), plays its walk or gallop by her speed, she sits its saddle playing her hero's rider clip (the Animals
// pack's, retargeted to each hero by 913), she goes HorseDef.SpeedMul times as fast, makes no attack, and the camera sits higher
// and further back. Hers is kept in the game instance (bHorseOwned, saved) and comes to her side on the town's level; the dungeons
// have none.
#include "RD/RDHorse.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDCombat.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "RD/RDGameInstance.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Animation/AnimSequenceBase.h"
#include "Animation/AnimInstance.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDHorse, Log, All);

namespace { const FName RDHorseSlot(TEXT("DefaultSlot")); }

ARDHorse::ARDHorse()
{
	PrimaryActorTick.bCanEverTick = false;
	Body = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Body"));
	RootComponent = Body;
	Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);           // (her capsule is what moves and collides)
	Body->SetGenerateOverlapEvents(false);
	Body->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
}

void ARDHorse::Init(const FRDHorseDef& InDef, bool bSecondColouring)
{
	Def = InDef;
	USkeletalMesh* M = bSecondColouring && Def.MeshB ? Def.MeshB.Get() : Def.Mesh.Get();
	if (M) Body->SetSkeletalMesh(M);
	PlayFor(0.f);
}

void ARDHorse::PlayFor(float Speed)
{
	// (the walk up to a canter's speed, then the gallop; each at the rate its soles keep pace with the ground, held within reason)
	FName Want = TEXT("idle"); UAnimSequenceBase* Clip = Def.Idle; float Rate = 1.f;
	if (Speed > 40.f && Def.Walk && (Speed < Def.GallopFrom || !Def.Run)) { Want = TEXT("walk"); Clip = Def.Walk; Rate = FMath::Clamp(Speed / FMath::Max(Def.WalkClipSpeed, 1.f), 0.5f, 3.f); }
	else if (Speed >= Def.GallopFrom && Def.Run) { Want = TEXT("run"); Clip = Def.Run; Rate = FMath::Clamp(Speed / FMath::Max(Def.RunClipSpeed, 1.f), 0.5f, 3.5f); }
	if (!Clip) return;
	if (Want != ClipNow) { Body->PlayAnimation(Clip, true); ClipNow = Want; }
	Body->SetPlayRate(Rate); RateNow = Rate;
}

FVector ARDHorse::GetSaddleLocation() const
{
	return Body && Body->DoesSocketExist(Def.SaddleBone) ? Body->GetSocketLocation(Def.SaddleBone) : GetActorLocation() + FVector(0, 0, 160.f);
}

// ================================================================================================ the generator's side
bool ARDDungeonGenerator::HasHorse() const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	return GI && GI->bHorseOwned;
}

ARDHorse* ARDDungeonGenerator::SpawnHorseAt(const FVector& At, float Yaw, bool bHers)
{
	if (!HorseDef.Mesh) return nullptr;
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ARDHorse* H = GetWorld()->SpawnActor<ARDHorse>(ARDHorse::StaticClass(), FTransform(FRotator(0.f, Yaw, 0.f), At), Sp);
	if (!H) return nullptr;
	H->bHers = bHers;
	H->Init(HorseDef, !bHers);          // (the stable's grey, her bay)
	return H;
}

bool ARDDungeonGenerator::CallHorse()
{
	APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Her || !HasHorse() || bMounted) return false;
	// (beside her, on the ground under that point)
	const FVector Side = Her->GetActorRightVector() * 220.f;
	FVector At = Her->GetActorLocation() + Side;
	FHitResult Hit;
	const float Hh = Her->GetSimpleCollisionHalfHeight();
	if (GetWorld()->LineTraceSingleByChannel(Hit, At + FVector(0, 0, 200.f), At - FVector(0, 0, 600.f), ECC_Visibility, FCollisionQueryParams(SCENE_QUERY_STAT(RDHorseCall), false, Her)))
		At = Hit.ImpactPoint;
	else At.Z -= Hh;
	if (!Horse) Horse = SpawnHorseAt(At, Her->GetActorRotation().Yaw, true);
	else { Horse->SetActorLocationAndRotation(At, FRotator(0.f, Her->GetActorRotation().Yaw, 0.f)); Horse->PlayFor(0.f); }
	return Horse != nullptr;
}

bool ARDDungeonGenerator::BuyHorse()
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || !PlayerCombat) return false;
	if (GI->bHorseOwned) { SetTownNote(TEXT("You have a horse already: the stable calls it for you")); return CallHorse(); }
	const int32 Cost = HorsePriceNow();
	if (GetGold() < Cost) { SetTownNote(TEXT("You have too little gold")); return false; }
	AddGold(-Cost, TEXT("the stable"));
	GI->bHorseOwned = true;
	if (StableHorse) { StableHorse->Destroy(); StableHorse = nullptr; }
	CallHorse();
	TownCount(TEXT("horse"));
	SetTownNote(FString::Printf(TEXT("The horse is yours for %d gold: F beside it to ride"), Cost));
	UE_LOG(LogRDHorse, Log, TEXT("RDHORSE bought for %d gold"), Cost);
	return true;
}

bool ARDDungeonGenerator::MountHorse()
{
	ACharacter* C = Cast<ACharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
	if (!C || !Horse || bMounted || !PlayerCombat || PlayerCombat->IsDead()) return false;
	bMounted = true;
	MountMeshWas = C->GetMesh()->GetRelativeLocation();
	if (USpringArmComponent* B = C->FindComponentByClass<USpringArmComponent>()) { BoomArmWas = B->TargetArmLength; BoomOffsetWas = B->TargetOffset; B->TargetArmLength += 140.f; B->TargetOffset.Z += 110.f; }
	PlayerCombat->MountFactor = FMath::Max(HorseDef.SpeedMul, 1.f); PlayerCombat->RefreshWalkSpeed();
	RiderClipNow = NAME_None;
	TickHorse(0.f);
	PlayerCombat->ShowMessage(TEXT("You ride your horse  (F: get off)"));
	UE_LOG(LogRDHorse, Log, TEXT("RDHORSE mounted"));
	return true;
}

bool ARDDungeonGenerator::DismountHorse()
{
	ACharacter* C = Cast<ACharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
	if (!bMounted) return false;
	bMounted = false;
	if (C)
	{
		C->GetMesh()->SetRelativeLocation(MountMeshWas);
		if (UAnimInstance* AI = C->GetMesh()->GetAnimInstance()) AI->StopSlotAnimation(0.2f, RDHorseSlot);
		if (USpringArmComponent* B = C->FindComponentByClass<USpringArmComponent>()) { B->TargetArmLength = BoomArmWas; B->TargetOffset = BoomOffsetWas; }
		// (the horse left standing beside her)
		if (Horse) { Horse->SetActorLocation(Horse->GetActorLocation() + C->GetActorRightVector() * 200.f); Horse->PlayFor(0.f); }
	}
	if (PlayerCombat) { PlayerCombat->MountFactor = 1.f; PlayerCombat->RefreshWalkSpeed(); }
	RiderClipNow = NAME_None;
	UE_LOG(LogRDHorse, Log, TEXT("RDHORSE dismounted"));
	return true;
}

void ARDDungeonGenerator::TickHorse(float Dt)
{
	ACharacter* C = Cast<ACharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
	if (!C || !HorseDef.Mesh) return;
	// (hers comes to her on this level; she rides only while alive)
	if (HasHorse() && !Horse && !bMounted && PlayerCombat && (bWild ? IsWildReady() : true)) CallHorse();
	if (bMounted && (!Horse || !PlayerCombat || PlayerCombat->IsDead())) { DismountHorse(); return; }
	// (the stable's horse: by the town's stable while she has none)
	if (!HasHorse())
	{
		const ARDSection* S = GetSection(FIntPoint::ZeroValue);
		const ARDSection::FTownSpot* St = S ? S->TownSpots.FindByPredicate([](const ARDSection::FTownSpot& Sp) { return Sp.Kind == TS_Stable; }) : nullptr;
		if (St && (!StableHorse || FVector::Dist2D(StableHorse->GetActorLocation(), St->At) > 300.f))
		{
			if (StableHorse) StableHorse->Destroy();
			StableHorse = SpawnHorseAt(St->At, St->Yaw, false);
		}
	}
	if (!bMounted || !Horse) return;
	// ---- riding: the horse under her, its clip by her speed; her root on its saddle, her rider clip by its gait
	const float Hh = C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	const FVector Feet = C->GetActorLocation() - FVector(0, 0, Hh);
	Horse->SetActorLocationAndRotation(Feet, FRotator(0.f, C->GetActorRotation().Yaw, 0.f));
	const float Speed = C->GetVelocity().Size2D();
	Horse->PlayFor(Speed);
	USkeletalMeshComponent* M = C->GetMesh();
	// (her pelvis on the saddle, RiderLift over it: the rider clips are a camel rider's, whose pelvis sits about 2 m over its root
	// and forward of it (the first rides put her 2.1 m above the saddle, then on the withers); her pelvis's place against her
	// mesh's origin read each frame, so every hero's rig sits right)
	const FVector Sad = Horse->GetSaddleLocation();
	const FVector PelvisOff = M->GetSocketLocation(TEXT("pelvis")) - M->GetComponentLocation();
	M->SetWorldLocation(Sad + FVector(0, 0, HorseDef.RiderLift) - PelvisOff);
	const FRDRiderClips* RC = RiderClips.Find(CurrentHero);
	UAnimSequenceBase* Clip = RC ? (Horse->ClipNow == TEXT("run") ? RC->Run.Get() : Horse->ClipNow == TEXT("walk") ? RC->Walk.Get() : RC->Idle.Get()) : nullptr;
	if (UAnimInstance* AI = M->GetAnimInstance(); AI && Clip)
	{
		const FName Want(*Horse->ClipNow.ToString());
		if (Want != RiderClipNow || !AI->IsSlotActive(RDHorseSlot))
		{
			AI->PlaySlotAnimationAsDynamicMontage(Clip, RDHorseSlot, 0.25f, 0.25f, 1.f, 10000);
			RiderClipNow = Want;
		}
	}
}

FString ARDDungeonGenerator::GetHorseState() const
{
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	const FVector H = Horse ? Horse->GetActorLocation() : FVector::ZeroVector;
	const FVector Sd = Horse ? Horse->GetSaddleLocation() : FVector::ZeroVector;
	const FVector Pv = Her ? Cast<ACharacter>(Her)->GetMesh()->GetSocketLocation(TEXT("pelvis")) : FVector::ZeroVector;
	return FString::Printf(TEXT("%d|%d|%d|%.0f|%.0f|%.0f|%s|%.2f|%.0f|%.1f|%.1f|%s|%d|%.1f"), HasHorse() ? 1 : 0, Horse ? 1 : 0, bMounted ? 1 : 0, H.X, H.Y, H.Z,
		Horse ? *Horse->ClipNow.ToString() : TEXT("none"), Horse ? Horse->RateNow : 0.f, Her ? Her->GetVelocity().Size2D() : 0.f, Sd.Z, Pv.Z,
		*RiderClipNow.ToString(), StableHorse ? 1 : 0, Horse ? FVector::Dist2D(Sd, Pv) : -1.f);
}
