#include "SS/SSTarget.h"
#include "SS/SSArena.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "NiagaraComponent.h"
#include "Particles/ParticleSystemComponent.h"

ASSTarget::ASSTarget()
{
	PrimaryActorTick.bCanEverTick = true;
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;
	Root->SetMobility(EComponentMobility::Movable);
	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	Mesh->SetupAttachment(Root);
	Mesh->SetMobility(EComponentMobility::Movable);
	Mesh->SetCollisionProfileName(TEXT("BlockAll"));
	Mesh->SetGenerateOverlapEvents(false);
	Mesh->SetCanEverAffectNavigation(false);
	Trail = CreateDefaultSubobject<UNiagaraComponent>(TEXT("Trail"));
	Trail->SetupAttachment(Root);
	Trail->SetAutoActivate(false);
	TrailPS = CreateDefaultSubobject<UParticleSystemComponent>(TEXT("TrailPS"));
	TrailPS->SetupAttachment(Root);
	TrailPS->bAutoActivate = false;
}

void ASSTarget::Setup(ASSArena* InArena, ESSTargetKind InKind, UStaticMesh* InMesh, const FRotator& MeshRotation, float Scale, float InHealth, int32 InPoints)
{
	Arena = InArena; Kind = InKind;
	Health = MaxHealth = FMath::Max(1.f, InHealth); Points = InPoints;
	Mesh->SetStaticMesh(InMesh);
	BaseScale = FVector(Scale);
	// the mesh is centred on the actor whatever its pivot
	const FBoxSphereBounds B = InMesh ? InMesh->GetBounds() : FBoxSphereBounds(FVector::ZeroVector, FVector(100.f), 100.f);
	Mesh->SetRelativeRotation(MeshRotation);
	Mesh->SetRelativeScale3D(BaseScale);
	Mesh->SetRelativeLocation(-MeshRotation.RotateVector(B.Origin * Scale));
	Radius = B.SphereRadius * Scale * 0.8f;
	if (Kind == ESSTargetKind::Debris) Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	else if (Arena) Arena->Register(this);
}

void ASSTarget::SetPatrol(const FVector& Center, float InRadius, const FVector& Axis, float Speed, float Phase)
{
	bPatrol = true;
	PCenter = Center; PRadius = InRadius; PSpeed = Speed; PAngle = Phase;
	PN = Axis.GetSafeNormal(UE_SMALL_NUMBER, FVector::UpVector);
	PN.FindBestAxisVectors(PU, PV);
	Wobble = FMath::Frac(Phase * 7.31f) * 6.28f;
}

bool ASSTarget::ApplyHit(float Damage, bool bByPlayer)
{
	if (bDead || Kind == ESSTargetKind::Debris) return false;
	Health -= Damage;
	Alarm = 6.f;                 // a drone that is shot at runs faster for a while
	if (Health > 0.f) return false;
	bDead = true;
	if (Arena) Arena->OnTargetDestroyed(this, bByPlayer);
	Destroy();
	return true;
}

void ASSTarget::Tick(float Dt)
{
	Super::Tick(Dt);
	if (Lifetime > 0.f)
	{
		LifeLeft -= Dt;
		if (LifeLeft <= 0.f) { Destroy(); return; }
		Mesh->SetRelativeScale3D(BaseScale * FMath::Clamp(LifeLeft / (Lifetime * 0.5f), 0.f, 1.f));
	}
	if (bPatrol)
	{
		Alarm = FMath::Max(0.f, Alarm - Dt);
		const float Sp = PSpeed * (Alarm > 0.f ? 1.7f : 1.f);
		PAngle += Sp / FMath::Max(PRadius, 100.f) * Dt;
		Wobble += Dt * (Alarm > 0.f ? 2.6f : 0.9f);
		// a circle that breathes in and out and bobs across its plane: harder to hit when it is alarmed
		const float Rr = PRadius * (1.f + 0.18f * FMath::Sin(Wobble * 0.7f));
		const FVector P = PCenter + (PU * FMath::Cos(PAngle) + PV * FMath::Sin(PAngle)) * Rr + PN * (PRadius * (Alarm > 0.f ? 0.22f : 0.10f) * FMath::Sin(Wobble));
		const FVector Old = GetActorLocation();
		if (Dt > UE_SMALL_NUMBER) Vel = (P - Old) / Dt;
		FRotator Rot = GetActorRotation();
		if (!Vel.IsNearlyZero(1.f))
		{
			// nose along the flight path, banked into the turn
			const FVector Fw = Vel.GetSafeNormal();
			const FVector Up = (PN + (PCenter - P).GetSafeNormal() * 0.6f).GetSafeNormal();
			Rot = FRotationMatrix::MakeFromXZ(Fw, Up).Rotator();
		}
		SetActorLocationAndRotation(P, Rot);
		return;
	}
	if (!Drift.IsZero() || !Spin.IsZero())
	{
		Vel = Drift;
		AddActorWorldOffset(Drift * Dt);
		AddActorLocalRotation(Spin * Dt);
	}
}

void ASSTarget::EndPlay(const EEndPlayReason::Type Reason)
{
	if (Arena) Arena->Unregister(this);
	Super::EndPlay(Reason);
}

// ---------------------------------------------------------------------------------------------------------------------

ASSBlast::ASSBlast()
{
	PrimaryActorTick.bCanEverTick = true;
	Light = CreateDefaultSubobject<UPointLightComponent>(TEXT("Light"));
	RootComponent = Light;
	Light->SetMobility(EComponentMobility::Movable);
	Light->SetCastShadows(false);
	Light->SetIntensityUnits(ELightUnits::Candelas);
	Light->SetIntensity(0.f);
	Ball = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Ball"));
	Ball->SetupAttachment(Light);
	Ball->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Ball->SetCastShadow(false);
	Ball->SetGenerateOverlapEvents(false);
}

void ASSBlast::Start(float InSize, UStaticMesh* BallMesh, UMaterialInterface* Material, const FLinearColor& Color, float Seconds)
{
	Size = InSize; Life = FMath::Max(0.1f, Seconds); Age = 0.f;
	Peak = FMath::Clamp(Size * Size * 0.02f, 200.f, 2.0e6f);            // candelas: lights what is around it
	Light->SetLightColor(Color);
	Light->SetAttenuationRadius(FMath::Clamp(Size * 14.f, 3000.f, 120000.f));
	Light->SetIntensity(Peak);
	if (BallMesh && Material)
	{
		Ball->SetStaticMesh(BallMesh);
		MID = UMaterialInstanceDynamic::Create(Material, this);
		MID->SetVectorParameterValue(TEXT("Color"), Color);
		MID->SetScalarParameterValue(TEXT("Alpha"), 1.f);
		Ball->SetMaterial(0, MID);
		Ball->SetWorldScale3D(FVector(Size * 0.3f / 50.f));
	}
}

void ASSBlast::Tick(float Dt)
{
	Super::Tick(Dt);
	Age += Dt;
	const float U = Age / Life;
	if (U >= 1.f) { Destroy(); return; }
	// the ball swells fast and thins out; the light dies a little sooner
	const float Grow = 0.3f + 0.7f * (1.f - FMath::Square(1.f - FMath::Min(U * 1.6f, 1.f)));
	Ball->SetWorldScale3D(FVector(Size * Grow / 50.f));
	if (MID) MID->SetScalarParameterValue(TEXT("Alpha"), FMath::Square(1.f - U));
	Light->SetIntensity(Peak * FMath::Square(FMath::Max(0.f, 1.f - U * 1.4f)));
}
