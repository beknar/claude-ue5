// The user's list of 2026-11-22 (docs/improvements16.txt; the plan docs/improvements16_plan.md), its thirteenth phase: the caves'
// armour, breath and the flooded chamber. The armour are copies of the fitted sets in new materials (945), each with what it does
// while worn (the generator's ArmourPerks16): the spelunker's quieter steps (monsters notice her from a share of their distance) and a
// little darksight, chitin plate's guard against poison, the drowned knight's set her breath three times as long; the deepiron sets
// one band better than the sets they copy. Breath: the game had none (she swims on the water's face); a cave's side tunnel to nowhere
// may be flooded instead of closed by rubble (its middle under water to its roof, its end a dry pocket with the cache and a piece of
// the drowned knight's set): under it she walks slowly, her breath runs down (15 s, the drowned set's three times that), and at none
// the water takes her hit points.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDCombat.h"
#include "RD/RDGameInstance.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/CollisionProfile.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Camera/CameraComponent.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDCave16e, Log, All);

// ================================================================================================ the flooded side tunnel
bool ARDSection::CaveFloodSet16(const FCaveRun16& Run, float Half, float F0, float F1)
{
	// (the stretch from F0 to F1 of the tunnel under water to its roof: a side tunnel to nowhere's from a quarter to 70 %, its end a dry
	// pocket; a loop's 14 m about its middle, crossed on one breath)
	// (whether a tunnel floods does not hang on a world: every build of the set (its census too) lays the same; only the roof's trace
	// and the water's pieces need one (a build with none flooded nothing, and fell back to rubble: the log of 2026-11-23))
	UWorld* W = GetWorld();
	if (!Generator) return false;
	const FVector O = GetActorLocation();
	FCaveFlood16 Fl; Fl.Half = Half * 0.8f;
	float Acc = 0.f, Roof = 1e9f, Floor = -1e9f;
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDCave16Flood), true);
	for (int32 I = 1; I < Run.Points.Num(); ++I)
	{
		Acc += FVector::Dist(Run.Points[I], Run.Points[I - 1]);
		const float F = Run.Length > 1.f ? Acc / Run.Length : 0.f;
		if (F < F0 || F > F1) continue;
		const FVector P = O + Run.Points[I];
		Fl.Pts.Add(P);
		Floor = FMath::Max(Floor, P.Z);
		// (the roof over it: traced up from her chest's height; none found (the shell not laid yet, a census) the kit's height)
		FHitResult H;
		if (W && W->LineTraceSingleByChannel(H, P + FVector(0, 0, 120.f), P + FVector(0, 0, 1500.f), ECC_Visibility, Q)) Roof = FMath::Min(Roof, H.ImpactPoint.Z);
	}
	if (Fl.Pts.Num() < 4) { UE_LOG(LogRDCave16e, Log, TEXT("RDCAVE16 (%d,%d): no water: %d points of %d in %.2f-%.2f of %.0f cm"), Coord.X, Coord.Y, Fl.Pts.Num(), Run.Points.Num(), F0, F1, Run.Length); return false; }
	// (to the roof, and 2.6 m over the floor at least: over her head wherever she walks the stretch)
	Fl.WaterZ = Roof < 1e8f ? FMath::Max(Roof - 30.f, Floor + 260.f) : Floor + 380.f;
	if (bBuildInteractive && W && W->IsGameWorld())
	{
		UStaticMesh* Plane = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Plane.Plane"));
		for (int32 I = 0; Plane && I + 1 < Fl.Pts.Num(); I += 4)
		{
			// (a plane a few points long, as wide as the tunnel, at the water's face; and the face's ends stood up, so the water is seen
			// from the dry tunnel as a wall, not only as a roof)
			const int32 J = FMath::Min(I + 4, Fl.Pts.Num() - 1);
			const FVector A = Fl.Pts[I], B = Fl.Pts[J];
			const FVector D = (B - A).GetSafeNormal2D();
			const float Len = FVector::Dist2D(A, B) + 60.f;
			auto Put = [&](const FTransform& T)
			{
				UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
				C->SetMobility(EComponentMobility::Movable);
				C->SetStaticMesh(Plane);
				if (Generator->FloodWater16) C->SetMaterial(0, Generator->FloodWater16);
				C->SetupAttachment(RootComponent);
				C->SetRelativeTransform(T.GetRelativeTransform(GetActorTransform()));
				C->SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);
				C->SetCastShadow(false);
				C->RegisterComponent();
				Fl.Comps.Add(C); CaveComps16.Add(C);
			};
			const FVector Mid = (A + B) * 0.5f;
			Put(FTransform(FRotator(0.f, D.Rotation().Yaw, 0.f), FVector(Mid.X, Mid.Y, Fl.WaterZ), FVector(Len / 100.f, Half * 2.f / 100.f, 1.f)));
			Put(FTransform(FRotator(0.f, D.Rotation().Yaw, 180.f), FVector(Mid.X, Mid.Y, Fl.WaterZ - 1.f), FVector(Len / 100.f, Half * 2.f / 100.f, 1.f)));          // (its face from under it)
			if (I == 0 || J == Fl.Pts.Num() - 1)
			{
				// (the plane's face is +Z: turned to face out of the water along the tunnel)
				const FVector E = I == 0 ? A : B;
				const float Sgn = I == 0 ? -1.f : 1.f;
				const float Hgt = Fl.WaterZ - E.Z + 40.f;
				Put(FTransform(FRotator(Sgn * 90.f, D.Rotation().Yaw, 0.f), FVector(E.X, E.Y, E.Z - 40.f + Hgt * 0.5f), FVector(Hgt / 100.f, Half * 2.f / 100.f, 1.f)));
			}
		}
	}
	CaveFloods16.Add(Fl);
	UE_LOG(LogRDCave16e, Log, TEXT("RDCAVE16 (%d,%d): a flooded side tunnel, %d points under water to %.0f (its floor at %.0f)"), Coord.X, Coord.Y, Fl.Pts.Num(), Fl.WaterZ, Floor);
	return true;
}

bool ARDDungeonGenerator::UnderWater16(const FVector& Head) const
{
	if (!bCave16) return false;
	const ARDSection* S = GetSection(WorldToSection(Head));
	if (!S) return false;
	for (const ARDSection::FCaveFlood16& Fl : S->CaveFloods16)
	{
		if (Head.Z >= Fl.WaterZ || Fl.Pts.Num() < 2) continue;
		// (within the stretch, not round its ends: a point beyond the first or last point along the tunnel is dry (the first test: the
		// dry tunnel 4 m before the water read as under it))
		const FVector2D H2(Head), A0(Fl.Pts[0]), A1(Fl.Pts[1]), Z0(Fl.Pts.Last()), Z1(Fl.Pts[Fl.Pts.Num() - 2]);
		if (FVector2D::DotProduct(H2 - A0, A1 - A0) < 0.f || FVector2D::DotProduct(H2 - Z0, Z1 - Z0) < 0.f) continue;
		for (int32 I = 1; I < Fl.Pts.Num(); ++I)
			if (FMath::PointDistToSegment(FVector(Head.X, Head.Y, 0.f), FVector(Fl.Pts[I - 1].X, Fl.Pts[I - 1].Y, 0.f), FVector(Fl.Pts[I].X, Fl.Pts[I].Y, 0.f)) < Fl.Half
				&& Head.Z > Fl.Pts[I].Z - 100.f)
				return true;
	}
	return false;
}

FName ARDDungeonGenerator::DrownedPieceOf16() const
{
	if (DrownedPieces16.Num() == 0) return NAME_None;
	const URDGameInstance* GI = URDGameInstance::Of(this);
	const FString Key = GI && !GI->CaveKey15.IsEmpty() ? GI->CaveKey15 : FString(TEXT("cave"));
	return DrownedPieces16[(GetTypeHash(Key) >> 3) % (uint32)DrownedPieces16.Num()];
}

// ================================================================================================ her armour's perks and her breath
FRDArmourPerk16 URDCombatComponent::ArmourPerk16() const
{
	const FRDArmourPerk16* P = Generator && !WornArmour.IsNone() ? Generator->ArmourPerks16.Find(WornArmour) : nullptr;
	return P ? *P : FRDArmourPerk16();
}

float URDCombatComponent::GetBreathMax16() const
{
	return Generator ? Generator->Breath16 * FMath::Max(ArmourPerk16().Breath, 0.1f) : 15.f;
}

void URDCombatComponent::TickBreath16(float Dt)
{
	if (!Generator || !Generator->bCave16 || bDead) return;
	APawn* P = Cast<APawn>(GetOwner());
	if (!P) return;
	const float Max = GetBreathMax16();
	if (Breath16 < 0.f) Breath16 = Max;
	const bool bUnder = Generator->UnderWater16(P->GetActorLocation() + FVector(0, 0, 60.f));
	if (bUnder != bUnder16)
	{
		bUnder16 = bUnder; UpdateWalkSpeed();
		if (bUnder) { ++Dives16; Generator->PlaySoundAt(TEXT("Player.Splash"), P->GetActorLocation()); }
		// (her view under water: a blue-green tint and a dark edge on her camera, her camera's own settings back when she comes up)
		if (UCameraComponent* Cam = P->FindComponentByClass<UCameraComponent>())
		{
			if (bUnder)
			{
				SavedCamPP16 = Cam->PostProcessSettings; SavedCamPPWeight16 = Cam->PostProcessBlendWeight; bCamPPSaved16 = true;
				Cam->PostProcessSettings.bOverride_SceneColorTint = true; Cam->PostProcessSettings.SceneColorTint = FLinearColor(0.60f, 0.88f, 0.98f);
				Cam->PostProcessSettings.bOverride_VignetteIntensity = true; Cam->PostProcessSettings.VignetteIntensity = 0.55f;
				Cam->PostProcessBlendWeight = 1.f;
			}
			else if (bCamPPSaved16) { Cam->PostProcessSettings = SavedCamPP16; Cam->PostProcessBlendWeight = SavedCamPPWeight16; bCamPPSaved16 = false; }
		}
	}
	if (bUnder)
	{
		Breath16 = FMath::Max(0.f, Breath16 - Dt);
		if (Breath16 <= 0.f)
		{
			// (out of breath: the water takes a share of her hit points a second, whatever she wears)
			DrownAcc16 += Generator->DrownShare16 * MaxHealth * Dt;
			if (DrownAcc16 >= 1.f)
			{
				const float D = FMath::FloorToFloat(DrownAcc16); DrownAcc16 -= D;
				Health = FMath::Max(0.f, Health - D); DrownTaken16 += D;
				if (Health <= 0.f) Fall();
				else if (GetWorld()->GetTimeSeconds() - LastDrownMsg16 > 2.f) { LastDrownMsg16 = GetWorld()->GetTimeSeconds(); SetMessage(TEXT("You are drowning: get out of the water")); }
			}
		}
	}
	else Breath16 = FMath::Min(Max, Breath16 + Dt * Max / 3.f);          // (back to full in 3 s above the water)
	Breath16 = FMath::Min(Breath16, Max);
}

FString URDCombatComponent::GetBreath16() const
{
	return FString::Printf(TEXT("breath|%.2f|%.2f|%d|%d|%.1f|notice|%.2f|darksight|%.0f|poisonguard|%.2f"), Breath16, GetBreathMax16(), bUnder16 ? 1 : 0, Dives16, DrownTaken16,
		GetNoticeMul16(), ArmourPerk16().Darksight, ArmourPerk16().PoisonGuard);
}
