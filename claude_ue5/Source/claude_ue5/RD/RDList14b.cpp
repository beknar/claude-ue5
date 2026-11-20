// The user's list of 2026-11-16 (docs/improvements14.txt; the plan docs/improvements14_plan.md), its third phase: her horse called
// by a key from anywhere but a dungeon (item 7), her horse on the maps (item 10), and the rider in the middle of the saddle holding
// the reins with her weapons put away (item 6). Behind the generator's bHorseCall14 (927 horse) and the horse's own seat and rein
// numbers (HorseDef, from blender_numpy/horse_seat.py's measure of the saddle on the model).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDCombat.h"
#include "RD/RDHUD.h"
#include "RD/RDHorse.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/Canvas.h"
#include "Engine/StaticMesh.h"
#include "Components/PointLightComponent.h"
#include "NiagaraComponent.h"
#include "Materials/MaterialInstanceDynamic.h"

bool ARDDungeonGenerator::CallHorseByKey()
{
	// (item 7: "enable calling your horse from anywhere except the dungeon": the castle and the cities' dungeons have no horse
	// (no HorseDef there); the wilds and the towns on brokenspire have)
	if (!bHorseCall14 || !PlayerCombat) return false;
	if (!HorseDef.Mesh || !(bWild || bTown)) { PlayerCombat->ShowMessage(TEXT("No horse can come to you down here")); return false; }
	if (!HasHorse()) { PlayerCombat->ShowMessage(TEXT("You have no horse: the stable by the gate sells one")); return false; }
	if (bMounted) { PlayerCombat->ShowMessage(TEXT("You are on your horse")); return false; }
	if (bSwimming) { PlayerCombat->ShowMessage(TEXT("Not while swimming")); return false; }
	if (bWild && !IsWildReady()) return false;
	// (PR #79's review: not indoors (a roof over her: the house's, the cathedral's), nor where no spot beside her is clear (the
	// call would set it down on her feet, inside the room))
	if (ACharacter* Her = Cast<ACharacter>(UGameplayStatics::GetPlayerPawn(this, 0)))
	{
		FCollisionQueryParams Q(SCENE_QUERY_STAT(RDHorseCall), false, Her); if (Horse) Q.AddIgnoredActor(Horse);
		FHitResult Up;
		const FVector Head = Her->GetActorLocation() + FVector(0, 0, Her->GetSimpleCollisionHalfHeight());
		if (GetWorld()->LineTraceSingleByChannel(Up, Head, Head + FVector(0, 0, 2000.f), ECC_Visibility, Q)) { PlayerCombat->ShowMessage(TEXT("Your horse cannot come in here")); return false; }
		if (FVector::Dist2D(HorseSpotBeside(Her), Her->GetActorLocation()) < 60.f) { PlayerCombat->ShowMessage(TEXT("No room for your horse here")); return false; }
	}
	if (!CallHorse()) return false;
	++HorseCalls14;
	PlayerCombat->ShowMessage(TEXT("You whistle: your horse comes to your side"));
	return true;
}

bool ARDDungeonGenerator::GetHorseMapAt(FVector& At) const
{
	// (item 10: her own horse, out and not under her)
	if (!HasHorse() || !Horse || bMounted) return false;
	At = Horse->GetActorLocation();
	return true;
}

FTransform ARDDungeonGenerator::HorseSeatFrame() const
{
	// (the saddle bone, turned as the horse faces: its +X along the horse toward its head)
	if (!Horse) return FTransform::Identity;
	return FTransform(FRotator(0.f, Horse->GetActorRotation().Yaw, 0.f), Horse->GetSaddleLocation());
}

FVector ARDDungeonGenerator::HorseSeatPoint() const
{
	return HorseSeatFrame().TransformPosition(FVector(HorseDef.SeatAhead, 0.f, HorseDef.SeatUp));
}

FVector ARDDungeonGenerator::HorseReinPoint(int32 Side) const
{
	// (her hand's hold, Side -1 her left, +1 her right: from her pelvis on the seat (the seat and the lift), ahead and up, half the
	// spread to each side)
	return HorseSeatFrame().TransformPosition(FVector(HorseDef.SeatAhead + HorseDef.ReinAhead, Side * HorseDef.ReinApart * 0.5f, HorseDef.SeatUp + HorseDef.RiderLift + HorseDef.ReinUp));
}

FVector ARDDungeonGenerator::HorseBitPoint(int32 Side) const
{
	// (the bit's ring each side of the mouth, from the head bone where the clip has it this frame)
	if (!Horse) return FVector::ZeroVector;
	const FVector Hd = Horse->Body ? Horse->Body->GetSocketLocation(TEXT("head")) : Horse->GetActorLocation();
	const FRotator Yw(0.f, Horse->GetActorRotation().Yaw, 0.f);
	return Hd + Yw.RotateVector(FVector(HorseDef.BitAhead, Side * 6.f, HorseDef.BitUp));
}

void ARDDungeonGenerator::TickReins14()
{
	// (item 6: no reins on the model: two leather cords from the bit to her hands while she rides, a cylinder each stretched
	// between them; hidden when she is down)
	ACharacter* C = Cast<ACharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
	// (2026-11-18: the pack's horse holds its own reins (HorseDef.bModelReins): none drawn)
	const bool bOn = bHorseCall14 && bMounted && Horse && C && !HorseDef.bModelReins;
	// (the reins' mesh and material are the generator's, set by 927 horse: referenced by the level, so cooked and kept (PR #79's
	// review: a function-static raw pointer loaded by its path dangled after a level change and was never cooked))
	UStaticMesh* Cyl = ReinsMesh;
	for (int32 K = 0; K < 2; ++K)
	{
		UStaticMeshComponent* R = Reins14[K].Get();
		if (!bOn) { if (R) R->SetVisibility(false); continue; }
		if (!R && Cyl)
		{
			R = NewObject<UStaticMeshComponent>(this);
			R->SetStaticMesh(Cyl); R->SetMobility(EComponentMobility::Movable);
			R->SetCollisionEnabled(ECollisionEnabled::NoCollision); R->SetCastShadow(false);
			if (ReinsMaterial) R->SetMaterial(0, ReinsMaterial);
			R->RegisterComponent();
			if (UMaterialInstanceDynamic* Md = R->CreateDynamicMaterialInstance(0)) Md->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.12f, 0.06f, 0.03f));
			Reins14[K] = R;
		}
		if (!R) continue;
		const int32 Side = K == 0 ? -1 : 1;
		const FVector A = HorseBitPoint(Side), B = C->GetMesh()->GetSocketLocation(Side < 0 ? TEXT("hand_l") : TEXT("hand_r"));
		const FVector D = B - A; const float Len = D.Size();
		if (Len < 1.f) { R->SetVisibility(false); continue; }
		// (the engine's cylinder: 100 cm high along its Z, 100 across; a cord 1.6 cm thick)
		R->SetWorldTransform(FTransform(FRotationMatrix::MakeFromZ(D / Len).ToQuat(), (A + B) * 0.5f, FVector(0.016f, 0.016f, Len / 100.f)));
		R->SetVisibility(true);
	}
}

FString ARDDungeonGenerator::GetRiderLine() const
{
	// (for the test: her pelvis against the seat (along the horse, across it, up: cm, the lift taken off), each hand from its grip
	// (cm), her weapons hidden or not)
	const ACharacter* C = Cast<ACharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
	if (!C || !Horse || !bMounted) return TEXT("not riding");
	const USkeletalMeshComponent* M = C->GetMesh();
	const FVector Pv = HorseSeatFrame().InverseTransformPosition(M->GetSocketLocation(TEXT("pelvis")));
	const float Hl = FVector::Dist(M->GetSocketLocation(TEXT("hand_l")), HorseReinPoint(-1));
	const float Hr = FVector::Dist(M->GetSocketLocation(TEXT("hand_r")), HorseReinPoint(1));
	int32 ReinsShown = 0; for (const TWeakObjectPtr<UStaticMeshComponent>& R : Reins14) if (R.IsValid() && R->IsVisible()) ++ReinsShown;
	return FString::Printf(TEXT("%.1f|%.1f|%.1f|%.1f|%.1f|%d|%d"), Pv.X - HorseDef.SeatAhead, Pv.Y, Pv.Z - HorseDef.SeatUp - HorseDef.RiderLift, Hl, Hr,
		PlayerCombat && PlayerCombat->AreRideHandsEmpty() ? 1 : 0, ReinsShown);
}

void URDCombatComponent::SetRideHands(bool bRiding)
{
	// (item 6: "she should be holding the reigns instead of holding her weapons": what she holds is hidden while she rides, each
	// shown again when she gets down only if it was showing; hidden again each tick (a weapon changed on the way would show))
	// (PR #79's review: hidden with their children (the torch's flame and light are the left hand's children); on getting down her
	// hands are made again from what she holds then, not shown as they were (a shield taken off on the way came back))
	UStaticMeshComponent* Held[] = { WeaponComp, OffHandComp, LeftComp, LoadedBoltComp };
	if (bRiding)
	{
		for (UStaticMeshComponent* H : Held) if (H) H->SetVisibility(false, true);
		bRideHands = true;
	}
	else
	{
		bRideHands = false;
		if (LeftComp) LeftComp->SetVisibility(true, true);
		if (WeaponIndex >= 0) { const int32 I = WeaponIndex; WeaponIndex = -1; SelectWeapon(I); }
		UpdateLeftHand();
		ShowLoadedBolt(true);
	}
}

bool URDCombatComponent::AreRideHandsEmpty() const
{
	const UStaticMeshComponent* Held[] = { WeaponComp, OffHandComp, LeftComp, LoadedBoltComp };
	for (const UStaticMeshComponent* H : Held) if (H && H->IsVisible()) return false;
	if ((TorchLight && TorchLight->IsVisible()) || (TorchFlame && TorchFlame->IsVisible())) return false;
	return true;
}

void ARDHUD::DrawHorseMark(const FVector2D& S, float Sc)
{
	// (her horse on a map: the map's horse symbol (blender_numpy/wild_symbols.py's wmap_horse), a brown dot without it)
	const float Ic = 10.f * Sc;
	if (!UI.Fit(TEXT("wmap_horse"), S - FVector2D(Ic), S + FVector2D(Ic), FLinearColor(1.f, 1.f, 1.f, 1.f)))
	{
		SoftDot(S, 6.f * Sc, FLinearColor(0.45f, 0.28f, 0.12f, 0.9f));
		SoftDot(S, 3.f * Sc, FLinearColor(0.95f, 0.85f, 0.6f, 1.f));
	}
}
