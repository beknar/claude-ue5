#include "SS/SSMissile.h"
#include "SS/SSArena.h"
#include "SS/SSTarget.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "NiagaraComponent.h"
#include "Particles/ParticleSystemComponent.h"

ASSMissile::ASSMissile()
{
	PrimaryActorTick.bCanEverTick = true;
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;
	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	Mesh->SetupAttachment(Root);
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mesh->SetGenerateOverlapEvents(false);
	Flame = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Flame"));
	Flame->SetupAttachment(Root);
	Flame->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Flame->SetCastShadow(false);
	Flame->SetGenerateOverlapEvents(false);
	Trail = CreateDefaultSubobject<UNiagaraComponent>(TEXT("Trail"));
	Trail->SetupAttachment(Root);
	Trail->SetAutoActivate(false);
	TrailPS = CreateDefaultSubobject<UParticleSystemComponent>(TEXT("TrailPS"));
	TrailPS->SetupAttachment(Root);
	TrailPS->SetRelativeLocation(FVector(-80.f, 0.f, 0.f));
	TrailPS->bAutoActivate = false;
	Glow = CreateDefaultSubobject<UPointLightComponent>(TEXT("Glow"));
	Glow->SetupAttachment(Root);
	Glow->SetRelativeLocation(FVector(-120.f, 0.f, 0.f));
	Glow->SetCastShadows(false);
	Glow->SetIntensityUnits(ELightUnits::Candelas);
	Glow->SetIntensity(260.f);
	Glow->SetAttenuationRadius(4000.f);
	Glow->SetLightColor(FLinearColor(1.f, 0.62f, 0.3f));
}

void ASSMissile::Launch(ASSArena* InArena, AActor* InOwner, ASSTarget* InTarget, const FVector& InVelocity, float InDamage, float InBlastRadius)
{
	Arena = InArena; Shooter = InOwner; Target = InTarget; Velocity = InVelocity; Damage = InDamage; BlastRadius = InBlastRadius;
	if (Trail->GetAsset()) Trail->Activate(true);
	if (TrailPS->Template) TrailPS->Activate(true);
}

void ASSMissile::Detonate(const FVector& At)
{
	if (bDone) return;
	bDone = true;
	if (Arena)
	{
		Arena->Blast(At, BlastRadius * 0.55f);
		Arena->RadialDamage(At, BlastRadius, Damage, true);
	}
	// the contrail lingers and fades by itself
	Trail->Deactivate(); TrailPS->Deactivate();
	Mesh->SetVisibility(false); Flame->SetVisibility(false); Glow->SetVisibility(false);
	SetActorTickEnabled(false);
	SetLifeSpan(3.f);
}

void ASSMissile::Tick(float Dt)
{
	Super::Tick(Dt);
	if (bDone) return;
	Age += Dt;
	const FVector L = GetActorLocation();
	FVector Fw = GetActorForwardVector();
	float Speed = Velocity.Size();
	ASSTarget* T = Target.Get();
	if (T && !T->IsAlive()) T = nullptr;
	if (T && Age > 0.25f)
	{
		// lead the target: aim at where it will be when the missile gets there
		const FVector To = T->GetActorLocation() - L;
		const float Time = FMath::Clamp(To.Size() / FMath::Max(Speed, 1000.f), 0.f, 3.f);
		const FVector Want = (To + (T->GetVelocity()) * Time).GetSafeNormal();
		const float Ang = FMath::Acos(FMath::Clamp(FVector::DotProduct(Fw, Want), -1.f, 1.f));
		const float Step = FMath::DegreesToRadians(TurnRate) * Dt;
		if (Ang > 1e-4f)
		{
			const FVector Axis = FVector::CrossProduct(Fw, Want).GetSafeNormal();
			if (!Axis.IsNearlyZero()) Fw = Fw.RotateAngleAxisRad(FMath::Min(Ang, Step), Axis).GetSafeNormal();
		}
	}
	Speed = FMath::Min(MaxSpeed, Speed + Acceleration * Dt);
	Velocity = Fw * Speed;
	const FVector New = L + Velocity * Dt;
	FCollisionQueryParams Q(SCENE_QUERY_STAT(SSMissile), true, this);
	if (AActor* S = Shooter.Get()) Q.AddIgnoredActor(S);
	FHitResult Hit;
	if (GetWorld()->LineTraceSingleByChannel(Hit, L, New, ECC_Visibility, Q)) { SetActorLocation(Hit.ImpactPoint); Detonate(Hit.ImpactPoint); return; }
	SetActorLocationAndRotation(New, Fw.Rotation());
	if (T && FVector::Dist(New, T->GetActorLocation()) < T->GetRadius() + Proximity) { Detonate(New); return; }
	if (Age > Fuel) Detonate(New);
}
