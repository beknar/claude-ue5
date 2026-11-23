// The user's list of 2026-11-22 (docs/improvements16.txt; the plan docs/improvements16_plan.md), its seventh phase: the towns' interiors.
//   - Option 1 (RDSection::AddPiece): what TownFurnish lays in a building is batched by building, so the engine's occlusion culling
//     hides what its walls hide; culled from 40 m (small clutter from 25 m). rd.InteriorBatch 0 batches it with the town (a rebuild).
//   - Option 3 (TickTownInteriors16, ten times a second): a building's interior (its batches, the lights and flames inside it, its
//     props and containers, the townsfolk in it) is drawn only when the camera or she is inside it, a door of it is open (or opening)
//     within 45 m, or a window of it within 45 m has a clear line from the camera on its outside; else hidden in game (its people's
//     day goes on; collision, F and the lit rule are untouched). 45 m, not the 40 m of the cull: shown a little early, so a room's
//     lighting has settled before she sees in. rd.InteriorHide 0 draws every interior.
//   - Option 2 is Nanite on the furniture and props (944 nanite_town, phase 5).
// The special shells (the castle, the cathedral, the foundry, the spire, the research facility) and burned houses (open to the sky) are
// never hidden.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "NiagaraComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Camera/PlayerCameraManager.h"
#include "HAL/IConsoleManager.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList16e, Log, All);

namespace
{
	TAutoConsoleVariable<int32> CVarRDInteriorBatch(TEXT("rd.InteriorBatch"), 1, TEXT("A town building's interior in instanced components of its own (1) or the town's (0); read when a town is built"));
	TAutoConsoleVariable<int32> CVarRDInteriorWindows(TEXT("rd.InteriorWindows"), 1, TEXT("A window of a town building in sight shows its interior (1), or only she or the camera inside or a door open does (0: the door's rule tested alone)"));
	TAutoConsoleVariable<int32> CVarRDInteriorHide(TEXT("rd.InteriorHide"), 1, TEXT("A town building's interior hidden unless she or the camera is in it, a door of it is open or a window of it is seen (1), or always drawn (0)"));
	const FName RDInteractiveTag16(TEXT("RDInteractive"));
	constexpr float RDInteriorSeeM16 = 4500.f;
}

bool ARDDungeonGenerator::InteriorBatch16() { return CVarRDInteriorBatch.GetValueOnGameThread() != 0; }

void ARDDungeonGenerator::TickTownInteriors16(float Dt)
{
	// (the whole rule ten times a second; in between, every frame, only a hidden interior whose door has begun to open is shown: in the
	// first frame of the door's swing, not up to a tenth of a second after)
	TownInteriorTimer16 -= Dt;
	const bool bFull = TownInteriorTimer16 <= 0.f;
	if (bFull) TownInteriorTimer16 = 0.1f;
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S || S->IsBuilding() || S->TownBlds.Num() == 0) return;
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	const APawn* Her = PC ? PC->GetPawn() : nullptr;
	if (!PC || !PC->PlayerCameraManager || !Her) return;
	const bool bOn = CVarRDInteriorHide.GetValueOnGameThread() != 0;
	const float M = TileSize;
	// ---- gathered once per section: each building's rectangle, doors, props
	if (S != TownInteriorsFor16.Get())
	{
		TownInteriorsFor16 = S; TownInt16.Reset();
		TownInt16.SetNum(S->TownBlds.Num());
		for (int32 BI = 0; BI < S->TownBlds.Num(); ++BI)
		{
			const ARDSection::FTownBld& B = S->TownBlds[BI];
			FTownInterior16& I = TownInt16[BI];
			I.bNever = BI == S->CastleBld || B.State == 1 || B.Kind == TK_Castle || B.Kind == TK_Cathedral || B.Kind == TK_Foundry || B.Kind == TK_Spire || B.Kind == TK_Research;
			I.A = FVector2D(S->LocalToWorld(B.Min) - FVector(M * 0.5f, M * 0.5f, 0)); I.B = FVector2D(S->LocalToWorld(B.Max - FIntPoint(1, 1)) + FVector(M * 0.5f, M * 0.5f, 0));
			if (const TArray<TWeakObjectPtr<UInstancedStaticMeshComponent>>* Is = S->TownBldIsm16.Find(BI)) I.Ism = *Is;
		}
		for (int32 D = 0; D < S->GetNumDoors(); ++D)
		{
			const FVector L = S->GetDoorLocation(D);
			for (const FVector Off : { FVector(80, 0, 0), FVector(-80, 0, 0), FVector(0, 80, 0), FVector(0, -80, 0) })
			{
				const int32 BI = S->TownBuildingAt(L + Off);
				if (TownInt16.IsValidIndex(BI)) { TownInt16[BI].Doors.AddUnique(D); break; }
			}
		}
		for (int32 W = 0; W < S->TownWindows16.Num(); ++W) if (TownInt16.IsValidIndex(S->TownWindows16[W].Bld)) TownInt16[S->TownWindows16[W].Bld].Windows.Add(W);
		// (its hearth: the fire and its glow, which the lit rule leaves burning whoever is home, hidden with the interior (PR #113's review))
		TInlineComponentArray<USceneComponent*> Hs(S);
		for (USceneComponent* C : Hs)
		{
			if (!C || !(C->IsA<UPointLightComponent>() || C->IsA<UNiagaraComponent>())) continue;
			const UNiagaraComponent* Nc = Cast<UNiagaraComponent>(C);
			if (!((Nc && HearthFx15 && Nc->GetAsset() == HearthFx15) || C->ComponentHasTag(TEXT("RDHearth15")))) continue;
			const int32 BI = S->TownBuildingAt(C->GetComponentLocation());
			if (TownInt16.IsValidIndex(BI)) TownInt16[BI].Hearths.Add(C);
		}
		// (its props and containers: the interactive meshes inside its rectangle, 80 cm in from its walls, away from its doors' leaves)
		TInlineComponentArray<UStaticMeshComponent*> Ms(S);
		for (UStaticMeshComponent* C : Ms)
		{
			if (!C || !C->ComponentHasTag(RDInteractiveTag16) || C->IsA<UInstancedStaticMeshComponent>()) continue;
			const FVector L = C->GetComponentLocation();
			for (int32 BI = 0; BI < TownInt16.Num(); ++BI)
			{
				FTownInterior16& I = TownInt16[BI];
				if (L.X < I.A.X + 80.f || L.X > I.B.X - 80.f || L.Y < I.A.Y + 80.f || L.Y > I.B.Y - 80.f) continue;
				bool bByDoor = false;
				for (const int32 D : I.Doors) if (FVector::Dist2D(S->GetDoorLocation(D), L) < 150.f) bByDoor = true;
				if (!bByDoor)
				{
					// (the prop and every component under it, each with the hidden state it had: shown again as it was, a helper another
					// rule hides is never shown by this one (PR #113's review))
					TArray<USceneComponent*> Sub; C->GetChildrenComponents(true, Sub); Sub.Insert(C, 0);
					for (USceneComponent* Sc : Sub) if (Sc) I.Props.Add({ Sc, Sc->bHiddenInGame });
				}
				break;
			}
		}
	}
	// ---- each building: shown or hidden
	const FVector Cam = PC->PlayerCameraManager->GetCameraLocation();
	const FVector Me = Her->GetActorLocation();
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDInterior16), false, Her);
	if (bFull) { TownIntShown16 = 0; TownIntHidden16 = 0; }
	for (int32 BI = 0; BI < TownInt16.Num(); ++BI)
	{
		FTownInterior16& I = TownInt16[BI];
		if (!bFull && (!I.bSet || I.bShown)) continue;
		bool bShow = !bOn || I.bNever;
		uint8 Why = bShow ? 1 : 0;          // (1 off or never hidden, 2 inside, 3 a door open, 4 a window seen; 0 hidden)
		int32 WhyWin = -1;
		auto Inside = [&](const FVector& P, float Pad) { return P.X > I.A.X - Pad && P.X < I.B.X + Pad && P.Y > I.A.Y - Pad && P.Y < I.B.Y + Pad; };
		if (!bShow) { bShow = Inside(Cam, 100.f) || Inside(Me, 100.f); if (bShow) Why = 2; }
		const FVector2D Mid = (I.A + I.B) * 0.5f;
		const float Far = (float)FVector2D::Distance(FVector2D(Cam), Mid) - (float)(I.B - I.A).Size() * 0.5f;
		if (!bShow && Far < RDInteriorSeeM16)
		{
			for (const int32 D : I.Doors) if (S->GetDoorOpenAlpha(D) > 0.001f || S->IsTargetOpen(true, D)) { bShow = true; Why = 3; break; }
			if (!bShow && bFull && CVarRDInteriorWindows.GetValueOnGameThread() != 0)
				for (const int32 W : I.Windows)
				{
					const ARDSection::FTownWin16& Wn = S->TownWindows16[W];
					const FVector To = Wn.At - Cam;
					if (To.Size() > RDInteriorSeeM16 || FVector::DotProduct(-To, Wn.Out) <= 0.f) continue;          // (only from its outside)
					FHitResult H;
					// (clear to the window: nothing struck before it (its own sill's collider stands at it: a hit within 1 m of it counts as there))
					if (!GetWorld()->LineTraceSingleByChannel(H, Cam, Wn.At, ECC_Visibility, Q) || FVector::Dist(H.ImpactPoint, Wn.At) < 100.f) { bShow = true; Why = 4; WhyWin = W; break; }
				}
		}
		if (!bFull && !bShow) continue;          // (between the full passes: only shown, never hidden)
		I.Why = Why; I.WhyWin = WhyWin;
		if (bFull) { if (bShow) ++TownIntShown16; else ++TownIntHidden16; }
		if (I.bShown == bShow && I.bSet) continue;
		I.bShown = bShow; I.bSet = true;
		for (const TWeakObjectPtr<UInstancedStaticMeshComponent>& W : I.Ism) if (UInstancedStaticMeshComponent* C = W.Get()) C->SetHiddenInGame(!bShow);
		for (const FTownInterior16::FProp& Pp : I.Props) if (USceneComponent* C = Pp.C.Get()) C->SetHiddenInGame(bShow ? Pp.bHidden0 : true);
		if (const TArray<TWeakObjectPtr<USceneComponent>>* Ls = TownBldLights.Find(BI))
			for (const TWeakObjectPtr<USceneComponent>& W : *Ls) if (USceneComponent* C = W.Get()) C->SetHiddenInGame(!bShow);
		for (const TWeakObjectPtr<USceneComponent>& W : I.Hearths) if (USceneComponent* C = W.Get()) C->SetHiddenInGame(!bShow);
	}
	// ---- the townsfolk in a hidden interior: hidden with it
	if (!bFull) return;
	TownIntPeopleHidden16 = 0;
	for (ARDTownsfolk* T : TownPeople)
	{
		if (!IsValid(T)) continue;
		const int32 BI = S->TownBuildingAt(T->GetActorLocation());
		const bool bHide = TownInt16.IsValidIndex(BI) && TownInt16[BI].bSet && !TownInt16[BI].bShown;
		if (bHide) ++TownIntPeopleHidden16;
		SetHidden16(T, TEXT("RDInt16"), bHide);          // (with the distance rule's: hidden while either wants it, RDList16d.cpp)
	}
}

FString ARDDungeonGenerator::GetInteriors16() const
{
	// (tests: "<hide on>|<batch on>|<buildings>|<shown>|<hidden>|<people hidden>|<windows>|<interior batches>")
	int32 Ni = 0, Nw = 0;
	for (const FTownInterior16& I : TownInt16) { Ni += I.Ism.Num(); Nw += I.Windows.Num(); }
	return FString::Printf(TEXT("%d|%d|%d|%d|%d|%d|%d|%d"), CVarRDInteriorHide.GetValueOnGameThread(), CVarRDInteriorBatch.GetValueOnGameThread(), TownInt16.Num(), TownIntShown16, TownIntHidden16,
		TownIntPeopleHidden16, Nw, Ni);
}

TArray<FString> ARDDungeonGenerator::GetInteriorLines16() const
{
	// (tests: a line a building: "<index>|<shown>|<never hidden>|<batches>|<props>|<doors>|<windows>|<min x>|<min y>|<max x>|<max y>|<why: 0 hidden,
	// 1 off or never, 2 inside, 3 a door open, 4 a window seen>|<the window seen: x|y|z, or -|-|->")
	TArray<FString> Out;
	const ARDSection* S = TownInteriorsFor16.Get();
	for (int32 BI = 0; BI < TownInt16.Num(); ++BI)
	{
		const FTownInterior16& I = TownInt16[BI];
		const FString Wn = S && S->TownWindows16.IsValidIndex(I.WhyWin) ? FString::Printf(TEXT("%.0f|%.0f|%.0f"), S->TownWindows16[I.WhyWin].At.X, S->TownWindows16[I.WhyWin].At.Y, S->TownWindows16[I.WhyWin].At.Z) : FString(TEXT("-|-|-"));
		Out.Add(FString::Printf(TEXT("%d|%d|%d|%d|%d|%d|%d|%.0f|%.0f|%.0f|%.0f|%d|%s"), BI, I.bShown ? 1 : 0, I.bNever ? 1 : 0, I.Ism.Num(), I.Props.Num(), I.Doors.Num(), I.Windows.Num(), I.A.X, I.A.Y, I.B.X, I.B.Y, I.Why, *Wn));
	}
	return Out;
}
