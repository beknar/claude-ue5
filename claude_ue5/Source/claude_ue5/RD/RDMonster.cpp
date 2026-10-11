#include "RD/RDMonster.h"
#include "RD/RDSection.h"
#include "RD/RDDungeonGenerator.h"
#include "Animation/AnimationAsset.h"
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
	LastPos = GetActorLocation();
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

void ARDMonster::PickTrip()
{
	Path.Reset();
	if (!Section) return;
	FIntPoint From = Section->WorldToLocal(GetActorLocation());
	if (!Section->IsWalkable(From))
	{
		// pushed off the walkable tiles (next to furniture): start from the nearest walkable neighbour
		for (int32 D = 1; D <= 2 && !Section->IsWalkable(From); ++D)
			for (int32 Dx = -D; Dx <= D; ++Dx) for (int32 Dy = -D; Dy <= D; ++Dy)
				if (Section->IsWalkable(From + FIntPoint(Dx, Dy))) { From += FIntPoint(Dx, Dy); Dx = Dy = D + 1; }
	}
	const FIntPoint To = Section->RandomRoomTile(R, Section->RoomAtLocal(From));
	TArray<FIntPoint> Tiles;
	if (!Section->FindPath(From, To, Tiles) || Tiles.Num() < 2) { WaitTime = R.FRandRange(1.f, 3.f); return; }
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
	int32 I = 0;
	while (I < Tiles.Num() - 1)
	{
		int32 J = Tiles.Num() - 1;
		while (J > I + 1 && !Clear(Tiles[I], Tiles[J])) --J;
		Path.Add(Section->LocalToWorld(Tiles[J]));
		I = J;
	}
	Goal = Path.Last();
	StuckTime = 0.f;
}

void ARDMonster::Tick(float Dt)
{
	Super::Tick(Dt);
	if (!Section) return;
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
	// a closed door between here and the next waypoint: push it open and wait
	const FIntPoint Cur = Section->WorldToLocal(L);
	const FVector Dir2 = FVector(Target.X - L.X, Target.Y - L.Y, 0);
	const FIntPoint Ahead = Section->WorldToLocal(L + Dir2.GetSafeNormal() * 160.f);
	if (Ahead != Cur && FMath::Abs(Ahead.X - Cur.X) + FMath::Abs(Ahead.Y - Cur.Y) == 1)
	{
		const int32 D = Section->DoorBetween(Cur, Ahead);
		if (D >= 0 && !Section->IsDoorOpenIndex(D))
		{
			if (Section->GetDoorOpenAlpha(D) < 0.01f) Section->ToggleDoor(D, L, true);
			SetWalkingAnim(false);
			return;
		}
	}
	// the player ahead: step aside toward the wall away from her (hallways are 3 m wide), wait if she is right there
	FVector Side = FVector::ZeroVector;
	if (const AActor* P = Section->Generator ? Section->Generator->GetTrackedActor() : UGameplayStatics::GetPlayerPawn(this, 0))
	{
		const FVector Dp = (P->GetActorLocation() - L) * FVector(1, 1, 0);
		const FVector Fw = Dir2.GetSafeNormal();
		if (Dp.Size() < 400.f && FVector::DotProduct(Dp.GetSafeNormal(), Fw) > 0.2f)
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
