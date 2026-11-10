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
#include "Components/BoxComponent.h"
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
	// (the list of 2026-11-10: a box that stops pawns (her, monsters, townsfolk) and nothing else: the camera passes, traces pass)
	Blocker = CreateDefaultSubobject<UBoxComponent>(TEXT("Blocker"));
	Blocker->SetupAttachment(Body);
	Blocker->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	Blocker->SetCollisionObjectType(ECC_WorldDynamic);
	Blocker->SetCollisionResponseToAllChannels(ECR_Ignore);
	Blocker->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
	Blocker->SetGenerateOverlapEvents(false);
	Blocker->SetCanEverAffectNavigation(false);
	Blocker->SetBoxExtent(FVector(100.f, 32.f, 70.f));
	Blocker->SetRelativeLocation(FVector(0.f, 0.f, 95.f));
}

void ARDHorse::Init(const FRDHorseDef& InDef, bool bSecondColouring)
{
	Def = InDef;
	USkeletalMesh* M = bSecondColouring && Def.MeshB ? Def.MeshB.Get() : Def.Mesh.Get();
	if (M) Body->SetSkeletalMesh(M);
	// (the box from the mesh's own bounds: its body from the knees up, a little inside its outline)
	if (M && Blocker)
	{
		const FBoxSphereBounds Bd = M->GetBounds();
		const FVector E = Bd.BoxExtent, O = Bd.Origin;
		const float Bottom = O.Z - E.Z, Top = O.Z + E.Z;
		const float Z0 = Bottom + (Top - Bottom) * 0.3f;
		Blocker->SetBoxExtent(FVector(FMath::Max(E.X * 0.85f, 20.f), FMath::Max(E.Y * 0.85f, 20.f), FMath::Max((Top - Z0) * 0.5f, 20.f)));
		Blocker->SetRelativeLocation(FVector(O.X, O.Y, (Z0 + Top) * 0.5f));
	}
	PlayFor(0.f);
}

void ARDHorse::SetBlocking(bool bOn)
{
	if (Blocker) Blocker->SetCollisionEnabled(bOn ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
}

bool ARDHorse::IsBlocking() const
{
	return Blocker && Blocker->GetCollisionEnabled() != ECollisionEnabled::NoCollision;
}

void ARDHorse::PlayFor(float Speed)
{
	// (the walk up to a canter's speed, then the gallop; each at the rate its soles keep pace with the ground, held within reason)
	FName Want = TEXT("idle"); UAnimSequenceBase* Clip = Def.Idle; float Rate = 1.f;
	if (Speed > 40.f && Def.Walk && (Speed < Def.GallopFrom || !Def.Run)) { Want = TEXT("walk"); Clip = Def.Walk; Rate = FMath::Clamp(Speed / FMath::Max(Def.WalkClipSpeed, 1.f), 0.5f, 3.f); }
	// (the list of 2026-11-10: at five times her speed the gallop plays up to six times over: its legs keep up with the ground)
	else if (Speed >= Def.GallopFrom && Def.Run) { Want = TEXT("run"); Clip = Def.Run; Rate = FMath::Clamp(Speed / FMath::Max(Def.RunClipSpeed, 1.f), 0.5f, 6.f); }
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

FVector ARDDungeonGenerator::HorseSpotBeside(const APawn* Her) const
{
	// (beside her on the ground under that point: her right, else her left, else behind her; the ground traced)
	const float Hh = Her->GetSimpleCollisionHalfHeight();
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDHorseSpot), false, Her);
	if (Horse) Q.AddIgnoredActor(Horse);
	for (const FVector Off : { Her->GetActorRightVector() * 220.f, Her->GetActorRightVector() * -220.f, Her->GetActorForwardVector() * -260.f })
	{
		const FVector P = Her->GetActorLocation() + Off;
		FHitResult Hit;
		// (a clear line from her to it, at her chest: not through a wall)
		if (GetWorld()->LineTraceSingleByChannel(Hit, Her->GetActorLocation(), P, ECC_Visibility, Q)) continue;
		if (GetWorld()->LineTraceSingleByChannel(Hit, P + FVector(0, 0, 200.f), P - FVector(0, 0, 600.f), ECC_Visibility, Q)) return Hit.ImpactPoint;
	}
	return Her->GetActorLocation() - FVector(0, 0, Hh);
}

bool ARDDungeonGenerator::CallHorse()
{
	APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Her || !HasHorse() || bMounted) return false;
	const FVector At = HorseSpotBeside(Her);
	if (!Horse) Horse = SpawnHorseAt(At, Her->GetActorRotation().Yaw, true);
	else { Horse->SetActorLocationAndRotation(At, FRotator(0.f, Her->GetActorRotation().Yaw, 0.f)); Horse->PlayFor(0.f); }
	// (its box stops her only once she is clear of it: set down where she stands (no spot found beside her) it would hold her inside)
	if (Horse) Horse->SetBlocking(false);
	return Horse != nullptr;
}

bool ARDDungeonGenerator::BuyHorse()
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || !PlayerCombat) return false;
	if (GI->bHorseOwned) { SetTownNote(TEXT("You have a horse already: the stable calls it for you")); return CallHorse(); }
	const int32 Cost = HorsePriceNow();
	if (GetGold() < Cost) { SetTownNote(TEXT("You have too little gold")); return false; }
	// (PR #37's review: the horse made before her gold is taken: no horse, no sale)
	if (!HorseDef.Mesh) { SetTownNote(TEXT("The stable has no horse today")); return false; }
	GI->bHorseOwned = true;
	if (!CallHorse()) { GI->bHorseOwned = false; SetTownNote(TEXT("The stable has no horse today")); return false; }
	AddGold(-Cost, TEXT("the stable"));
	if (StableHorse) { StableHorse->Destroy(); StableHorse = nullptr; }
	TownCount(TEXT("horse"));
	SetTownNote(FString::Printf(TEXT("The horse is yours for %d gold: F beside it to ride"), Cost));
	UE_LOG(LogRDHorse, Log, TEXT("RDHORSE bought for %d gold"), Cost);
	return true;
}

bool ARDDungeonGenerator::MountHorse()
{
	ACharacter* C = Cast<ACharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
	if (!C || !Horse || bMounted || !PlayerCombat || PlayerCombat->IsDead()) return false;
	if (PlayerCombat->IsBusyForMount()) { PlayerCombat->ShowMessage(TEXT("Not in the middle of a move")); return false; }
	bMounted = true;
	Horse->SetBlocking(false);          // (the list of 2026-11-10: ridden, it stops nothing: her capsule does)
	// (no jump from the saddle: it lifted the horse; the generator's tick after her movement's, so the horse is put under where
	// she is this frame, not where she was (it trailed her by 26 cm at a gallop: PR #37's review))
	JumpWas = C->GetCharacterMovement()->JumpZVelocity; C->GetCharacterMovement()->JumpZVelocity = 0.f;
	PrimaryActorTick.AddPrerequisite(C->GetCharacterMovement(), C->GetCharacterMovement()->PrimaryComponentTick);
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
		// (her rider clip off, but not a death's: it plays on the same slot (PR #37's review: she stood up dead))
		const bool bDeadNow = PlayerCombat && PlayerCombat->IsDead();
		if (UAnimInstance* AI = C->GetMesh()->GetAnimInstance(); AI && !bDeadNow) AI->StopSlotAnimation(0.2f, RDHorseSlot);
		if (USpringArmComponent* B = C->FindComponentByClass<USpringArmComponent>()) { B->TargetArmLength = BoomArmWas; B->TargetOffset = BoomOffsetWas; }
		C->GetCharacterMovement()->JumpZVelocity = JumpWas;
		PrimaryActorTick.RemovePrerequisite(C->GetCharacterMovement(), C->GetCharacterMovement()->PrimaryComponentTick);
		// (the horse left standing beside her, on the ground (PR #37's review: moved without a trace it floated on a slope))
		if (Horse) { Horse->SetActorLocation(HorseSpotBeside(C)); Horse->PlayFor(0.f); }
	}
	if (Horse) Horse->SetBlocking(false);          // (on again once she is clear of it: TickHorse)
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
	if (bMounted && PlayerCombat->IsBusyForMount()) PlayerCombat->SetBlocking(false);          // (a block begun before: off)
	// (the stable's horse: by the town's stable while she has none)
	StableLookIn -= Dt;
	if (!HasHorse() && StableLookIn <= 0.f)
	{
		// (once a second, not each frame (PR #37's review); gone when the town that had it is gone)
		StableLookIn = 1.f;
		const ARDSection* S = GetSection(FIntPoint::ZeroValue);
		const ARDSection::FTownSpot* St = S ? S->TownSpots.FindByPredicate([](const ARDSection::FTownSpot& Sp) { return Sp.Kind == TS_Stable; }) : nullptr;
		if (!St) { if (StableHorse) { StableHorse->Destroy(); StableHorse = nullptr; } }
		else if (!StableHorse || FVector::Dist2D(StableHorse->GetActorLocation(), St->At) > 300.f)
		{
			if (StableHorse) StableHorse->Destroy();
			StableHorse = SpawnHorseAt(St->At, St->Yaw, false);
		}
	}
	// (the list of 2026-11-10: unridden, its box on once she stands clear of it (2 m from its middle))
	if (!bMounted && Horse && !Horse->IsBlocking() && FVector::Dist2D(C->GetActorLocation(), Horse->GetActorLocation()) > 200.f) Horse->SetBlocking(true);
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
		// (at the horse's pace: her bounce in step with its stride (PR #37's review))
		const float Rate = FMath::Clamp(Horse->RateNow, 0.5f, 4.f);
		if (Want != RiderClipNow || !AI->IsSlotActive(RDHorseSlot))
		{
			RiderMontage = AI->PlaySlotAnimationAsDynamicMontage(Clip, RDHorseSlot, 0.25f, 0.25f, Rate, 10000);
			RiderClipNow = Want;
		}
		else if (RiderMontage) AI->Montage_SetPlayRate(RiderMontage, Rate);
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
