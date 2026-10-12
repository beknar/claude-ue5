#include "IV/IVVillager.h"
#include "IV/IVSection.h"
#include "IV/IVVillageGenerator.h"
#include "Animation/AnimationAsset.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "HAL/PlatformTime.h"

AIVVillager::AIVVillager()
{
	PrimaryActorTick.bCanEverTick = true;
	Capsule = CreateDefaultSubobject<UCapsuleComponent>(TEXT("Capsule"));
	RootComponent = Capsule;
	Capsule->InitCapsuleSize(30.f, 88.f);
	// only pawns notice it (she cannot walk through a villager); it is moved along its path without sweeping
	Capsule->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Capsule->SetCollisionObjectType(ECC_Pawn);
	Capsule->SetCollisionResponseToAllChannels(ECR_Ignore);
	Capsule->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
	Capsule->SetGenerateOverlapEvents(false);
	Capsule->SetCanEverAffectNavigation(false);
	Mesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Mesh"));
	Mesh->SetupAttachment(Capsule);
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mesh->SetGenerateOverlapEvents(false);
	Mesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
	Mesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
	Mesh->bEnableUpdateRateOptimizations = true;
}

void AIVVillager::Setup(AIVSection* InSection, const FIVVillagerDef& Def, int32 InSeed)
{
	Section = InSection; VillagerName = Def.Name;
	R.Initialize(InSeed);
	const float S = FMath::Clamp(Def.Scale, 0.3f, 2.f);
	HalfHeight = 88.f * S;
	Capsule->SetCapsuleSize(30.f * S, HalfHeight);
	if (Section && Section->Generator && !Section->Generator->bVillagersBlockPawns) Capsule->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
	Mesh->SetSkeletalMesh(Def.Mesh);
	Mesh->SetRelativeLocationAndRotation(FVector(0, 0, -HalfHeight), FRotator(0, Def.MeshYaw, 0));
	Mesh->SetRelativeScale3D(FVector(S));
	IdleAnim = Def.Idle; WalkAnim = Def.Walk;
	// a stroll: the walk cycle played a little slower than it was drawn
	ClipSpeed = FMath::Max(Def.WalkClipSpeed, 10.f) * S;
	WalkSpeed = ClipSpeed * R.FRandRange(0.54f, 0.70f);
	const FVector L = GetActorLocation();
	SetActorLocation(FVector(L.X, L.Y, HalfHeight + 2.f));
	bWalkingAnim = true; SetWalkingAnim(false);
	Mesh->SetPosition(R.FRandRange(0.f, 5.f));
	WaitTime = R.FRandRange(0.5f, 9.f);
}

void AIVVillager::SetWalkingAnim(bool bWalk)
{
	if (bWalk == bWalkingAnim) return;
	bWalkingAnim = bWalk;
	UAnimationAsset* A = bWalk ? WalkAnim.Get() : IdleAnim.Get();
	if (!A) A = IdleAnim ? IdleAnim.Get() : WalkAnim.Get();
	if (A) Mesh->PlayAnimation(A, true);
	if (!bWalk) Mesh->SetPlayRate(1.f);
}

void AIVVillager::StandStill(float Dt)
{
	Speed = 0.f;
	SetWalkingAnim(false);
}

void AIVVillager::PickTrip()
{
	Path.Reset();
	AIVVillageGenerator* Gen = Section ? Section->Generator.Get() : nullptr;
	if (!Gen) return;
	const FVector L = GetActorLocation();
	FVector To;
	if (!Section->RandomVillagerSpot(R, L, To)) { WaitTime = R.FRandRange(1.f, 3.f); return; }
	// streets only: villagers do not walk through houses
	const double T0 = FPlatformTime::Seconds();
	const TArray<FVector> Pts = Gen->FindPathEx(L, To, 16000, false);
	Gen->NotePath((FPlatformTime::Seconds() - T0) * 1000.0, Pts.Num() >= 2);
	if (Pts.Num() < 2) { WaitTime = R.FRandRange(1.f, 3.f); return; }
	// straighten: drop the turning points a straight walk can do without
	auto Clear = [Gen](const FVector& A, const FVector& B)
	{
		const int32 Steps = FMath::CeilToInt(FVector::Dist2D(A, B) / 22.f);
		for (int32 K = 1; K < Steps; ++K)
		{
			const FVector P = FMath::Lerp(A, B, (float)K / Steps);
			if (Gen->NavBlocked(FVector2D(P.X, P.Y))) return false;
		}
		return true;
	};
	FVector From(L.X, L.Y, 0.f);
	int32 I = 0;
	while (I < Pts.Num() - 1)
	{
		int32 J = Pts.Num() - 1;
		while (J > I + 1 && !Clear(From, Pts[J])) --J;
		Path.Add(Pts[J]);
		From = Pts[J]; I = J;
	}
	Goal = Path.Last();
	BlockedTime = 0.f; YieldTime = 0.f;
}

void AIVVillager::Tick(float Dt)
{
	Super::Tick(Dt);
	AIVVillageGenerator* Gen = Section ? Section->Generator.Get() : nullptr;
	if (!Gen) return;
	const FVector2D Me = Ground();
	FVector2D ToHer(1e6f, 1e6f), HerVel(0.f, 0.f);
	if (const AActor* Who = Gen->GetTrackedActor())
	{
		const FVector D = Who->GetActorLocation() - GetActorLocation(), V = Who->GetVelocity();
		ToHer = FVector2D(D.X, D.Y); HerVel = FVector2D(V.X, V.Y);
	}
	const float HerDist = ToHer.Size();
	// out of sight: think less often
	SetActorTickInterval(HerDist > 9000.f ? 0.25f : HerDist > 5200.f ? 0.07f : 0.f);

	if (WaitTime > 0.f)
	{
		StandStill(Dt);
		// she walks into it: step out of her way
		if (HerDist < 120.f && HerVel.SizeSquared() > 400.f && FVector2D::DotProduct(HerVel.GetSafeNormal(), -ToHer.GetSafeNormal()) > 0.3f)
		{
			const FVector2D Hv = HerVel.GetSafeNormal(), Side(-Hv.Y, Hv.X);
			const float Sg = FVector2D::DotProduct(Side, -ToHer) >= 0.f ? 1.f : -1.f;
			for (const FVector2D& D : { Side * Sg, Side * -Sg, -ToHer.GetSafeNormal() })
			{
				const FVector2D P = Me + D * 170.f;
				if (Gen->NavBlocked(P) || Gen->NavBlocked(Me + D * 85.f)) continue;
				Path.Reset(); Path.Add(FVector(P, 0.f)); Goal = Path[0];
				WaitTime = 0.f; BlockedTime = 0.f;
				break;
			}
			return;
		}
		WaitTime -= Dt;
		if (WaitTime <= 0.f && Path.Num() == 0)
		{
			// (one path search a frame for the whole village)
			if (Gen->TakePathSlot()) PickTrip(); else WaitTime = R.FRandRange(0.05f, 0.3f);
		}
		return;
	}
	if (Path.Num() == 0) { WaitTime = R.FRandRange(3.f, 10.f); return; }

	const FVector2D To = FVector2D(Path[0].X, Path[0].Y) - Me;
	const float Dist = To.Size();
	if (Dist < FMath::Max(10.f, Speed * Dt))
	{
		Path.RemoveAt(0);
		if (Path.Num() == 0) { ++TripsDone; WaitTime = R.FRandRange(3.f, 11.f); StandStill(Dt); }
		return;
	}
	const FVector2D Fw = To / Dist;
	// the player in the way: let her pass, and find something else to do if she stays
	if (HerDist < 130.f && FVector2D::DotProduct(ToHer / FMath::Max(HerDist, 1.f), Fw) > 0.25f)
	{
		StandStill(Dt);
		BlockedTime += Dt;
		if (BlockedTime > 2.2f) { ++Repaths; Path.Reset(); BlockedTime = 0.f; WaitTime = R.FRandRange(0.4f, 1.5f); }
		return;
	}
	BlockedTime = FMath::Max(0.f, BlockedTime - Dt);
	// another villager right ahead: walk round on the right
	FVector2D Dir = Fw;
	bool bSteer = false;
	for (const AIVVillager* O : Section->GetVillagers())
	{
		if (!O || O == this) continue;
		const FVector2D D = O->Ground() - Me;
		const float Ds = D.SizeSquared();
		if (Ds > 90.f * 90.f || Ds < 1.f || FVector2D::DotProduct(D, Fw) < 0.35f * FMath::Sqrt(Ds)) continue;
		const FVector2D Rt(-Fw.Y, Fw.X);
		Dir = (Fw + Rt * (FVector2D::DotProduct(Rt, D) > 4.f ? -1.1f : 1.1f)).GetSafeNormal();
		bSteer = true;
		break;
	}
	Speed = FMath::FInterpConstantTo(Speed, WalkSpeed, Dt, 280.f);
	const float Step = bSteer ? Speed * Dt : FMath::Min(Speed * Dt, Dist);
	const FVector2D New = Me + Dir * Step;
	if (Gen->NavBlocked(New) || (bSteer && Gen->NavBlocked(New + Dir * 25.f)))
	{
		// no room to pass (or the way is shut): wait a moment, then give the trip up
		StandStill(Dt);
		YieldTime += Dt;
		if (YieldTime > 1.8f) { ++Repaths; Path.Reset(); YieldTime = 0.f; WaitTime = R.FRandRange(0.4f, 1.5f); }
		return;
	}
	YieldTime = 0.f;
	FRotator Rot = GetActorRotation();
	Rot = FMath::RInterpConstantTo(Rot, FRotator(0.f, FMath::RadiansToDegrees(FMath::Atan2(Dir.Y, Dir.X)), 0.f), Dt, 420.f);
	SetActorLocationAndRotation(FVector(New, HalfHeight + 2.f), Rot);
	Walked += Step;
	SetWalkingAnim(true);
	Mesh->SetPlayRate(FMath::Clamp(Speed / ClipSpeed, 0.35f, 1.5f));
}
