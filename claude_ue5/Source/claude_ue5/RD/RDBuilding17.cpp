// The user's list of 2026-11-26 (docs/improvements17.txt; the plan docs/improvements17_plan.md), its fifth phase: a building a level of its own.
//   "Make a game mode ... that makes all buildings their own level, where opening a door opens a new level just for that building ... when looking
//   outside a window, show a solid or glowing texture depicting the outside of that building."
//   - Closed Structures (rd.Structures17 1; the Options page's choice in the sixth phase): the town is planned and furnished as in Immersive
//     Interiors, every draw in its place, but an enterable building's static furnishing is recorded (its pieces' meshes, materials and places,
//     its blueprint props) instead of drawn in the town. Its lights, hearth, containers, doors and people stay the town's, shown only while she
//     is inside it.
//   - Its outer door's F opens a level of its own for it: the small map town_building streamed in as a level instance, the recorded
//     furnishing laid in it where it stood, and a pane at each of its windows showing the street outside, captured as she came in (a cube
//     with the building's own pieces taken out, as the skyscrapers' level's (RDTower24.cpp)). The door from inside lets her out and the level
//     goes. Walking in at a door left open enters it too, and walking out leaves it.
//   - Not enterable (built as before): the castle and the cities' landmark halls (the dungeons' ways in), Heaven's skyscrapers (a level of
//     their own already), burned and boarded houses.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "RD/RDGameInstance.h"
#include "RD/RDCombat.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/LevelStreamingDynamic.h"
#include "Engine/Level.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Engine/TextureRenderTargetCube.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SceneCaptureComponentCube.h"
#include "Components/VolumetricCloudComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformTime.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDBuilding17, Log, All);

namespace
{
	TAutoConsoleVariable<int32> CVarRDStructures17(TEXT("rd.Structures17"), -1, TEXT("Structures: Immersive Interiors (0), Closed Structures (1), or the Options page's choice (-1); read when a town is built"));
	const FIntPoint RDB17Dir4[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };
}

// ================================================================================================ the mode and what is enterable
bool ARDDungeonGenerator::Closed17() const
{
	const int32 C = CVarRDStructures17.GetValueOnGameThread();
	if (C >= 0) return C != 0;
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (GI && !GI->bStructuresLoaded17) { GI->bStructuresLoaded17 = true; const_cast<ARDDungeonGenerator*>(this)->LoadStructures17(); }          // (the option read before the first town is planned)
	return GI && GI->Structures17 == 1;
}

bool ARDDungeonGenerator::IsEnterable17(const ARDSection* S, int32 BI) const
{
	if (!S || !S->TownBlds.IsValidIndex(BI) || BI == S->CastleBld) return false;
	const ARDSection::FTownBld& B = S->TownBlds[BI];
	if (B.State != 0 || B.bBoarded || B.Rooms.Num() == 0) return false;
	switch (B.Kind)
	{
	case TK_Castle: case TK_Cathedral: case TK_Foundry: case TK_SluiceHouse: case TK_Spire: case TK_Research: case TK_SkyTower: return false;
	default: return true;
	}
}

bool ARDSection::RecordsBuilding17(int32 BI) const
{
	return Generator && Generator->bTown && BldClosed17 && Generator->IsEnterable17(this, BI);
}

void ARDSection::RecordPiece17(int32 BI, UStaticMesh* Mesh, UMaterialInterface* Mat, bool bCol, bool bSmall, float Cull, const FTransform& W)
{
	FBldRec17& R = BldRec17.FindOrAdd(BI);
	if (Mesh) BldRecRefs17.AddUnique(Mesh);
	if (Mat) BldRecRefs17.AddUnique(Mat);
	const FString Key = FString::Printf(TEXT("%s|%s|%d|%d"), Mesh ? *Mesh->GetPathName() : TEXT("-"), Mat ? *Mat->GetPathName() : TEXT("-"), bCol ? 1 : 0, bSmall ? 1 : 0);
	FBldRecPiece17& P = R.Pieces.FindOrAdd(Key);
	P.Mesh = Mesh; P.Mat = Mat; P.bCol = bCol; P.bSmall = bSmall; P.Cull = Cull;
	P.T.Add(W);
	++R.N;
}

void ARDSection::RecordActor17(int32 BI, UClass* Class, const FTransform& W)
{
	FBldRec17& R = BldRec17.FindOrAdd(BI);
	if (Class) BldRecRefs17.AddUnique(Class);
	R.Actors.Add({ Class, W });
	++R.N;
}

// ================================================================================================ in and out
int32 ARDDungeonGenerator::BuildingDoorNear17(const FVector& From, bool bOut) const
{
	// (an enterable building whose outer door is within reach: from outside its door's outside, from inside (the building she is in) its inside)
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S || S->IsBuilding()) return -1;
	int32 Best = -1; float BestD = 260.f;
	for (int32 I = 0; I < S->TownBlds.Num(); ++I)
	{
		if (bOut ? I != InBuilding17 : !S->HasRecord17(I)) continue;
		const ARDSection::FTownBld& B = S->TownBlds[I];
		if (B.Door < 0) continue;
		const FVector Out(RDB17Dir4[B.DoorSide].X, RDB17Dir4[B.DoorSide].Y, 0.f);
		const FVector Door = S->LocalToWorld(B.DoorTile) + Out * (TileSize * 0.5f);
		const FVector Side = Door + Out * (bOut ? -110.f : 110.f);
		const float D = FMath::Min(FVector::Dist2D(Door, From), FVector::Dist2D(Side, From));
		if (D < BestD && FMath::Abs(From.Z - Door.Z) < 300.f && (FVector::DotProduct(From - Door, Out) > 0.f) != bOut) { BestD = D; Best = I; }
	}
	return Best;
}

bool ARDDungeonGenerator::BuildingDoorFirst17(const FVector& From, int32 I, float NearerThan, const ARDSection* BestS, bool bBestDoor, int32 BestI) const
{
	// (PR #141's review: a nearer door, container or person keeps F, as every town target yields; the building's own door leaf is no rival
	// (F at it goes in or out))
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S || !S->TownBlds.IsValidIndex(I)) return false;
	if (bBestDoor && BestS == S && BestI == S->TownBlds[I].Door) return true;
	const ARDSection::FTownBld& B = S->TownBlds[I];
	const FVector Out(RDB17Dir4[B.DoorSide].X, RDB17Dir4[B.DoorSide].Y, 0.f);
	const float D = FVector::Dist2D(S->LocalToWorld(B.DoorTile) + Out * (TileSize * 0.5f), From);
	if (D >= NearerThan) return false;
	for (const ARDTownsfolk* T : TownPeople) if (T && !T->IsHidden() && FVector::Dist2D(T->GetActorLocation(), From) < FMath::Min(D, 160.f) && FMath::Abs(T->GetActorLocation().Z - From.Z) < 200.f) return false;
	return true;
}

FString ARDDungeonGenerator::BuildingDescribe17(const FVector& From, float NearerThan, const ARDSection* BestS, bool bBestDoor, int32 BestI) const
{
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!bTown || !S || !S->BldClosed17 || PendingBuilding17 >= 0) return FString();
	if (InBuilding17 >= 0) { if (BuildingDoorNear17(From, true) >= 0 && BuildingDoorFirst17(From, InBuilding17, NearerThan, BestS, bBestDoor, BestI)) return FString::Printf(TEXT("leave %s"), *RDTTheLabel17(S, InBuilding17)); return FString(); }
	const int32 I = BuildingDoorNear17(From, false);
	return I >= 0 && BuildingDoorFirst17(From, I, NearerThan, BestS, bBestDoor, BestI) ? FString::Printf(TEXT("enter %s"), *RDTTheLabel17(S, I)) : FString();
}

FString ARDDungeonGenerator::BuildingDoorUse17(const FVector& From, float NearerThan, const ARDSection* BestS, bool bBestDoor, int32 BestI)
{
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!bTown || !S || !S->BldClosed17 || PendingBuilding17 >= 0) return FString();
	if (InBuilding17 >= 0) return BuildingDoorNear17(From, true) >= 0 && BuildingDoorFirst17(From, InBuilding17, NearerThan, BestS, bBestDoor, BestI) && LeaveBuilding17() ? FString(TEXT("leave building")) : FString();
	const int32 I = BuildingDoorNear17(From, false);
	return I >= 0 && BuildingDoorFirst17(From, I, NearerThan, BestS, bBestDoor, BestI) && EnterBuilding17(I) ? FString(TEXT("enter building")) : FString();
}

FString ARDDungeonGenerator::RDTTheLabel17(const ARDSection* S, int32 BI)
{
	if (!S || !S->TownBlds.IsValidIndex(BI)) return FString();
	const FString L = S->TownBlds[BI].Label;
	return L.IsEmpty() ? FString(TEXT("the building")) : L.ToLower().StartsWith(TEXT("the ")) ? L : TEXT("the ") + L;
}

bool ARDDungeonGenerator::EnterBuilding17(int32 BI)
{
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S || !S->TownBlds.IsValidIndex(BI) || BuildingLevel17.IsEmpty() || (PlayerCombat && PlayerCombat->IsDead())) return false;
	if (!S->HasRecord17(BI)) return false;
	if (InBuilding17 >= 0) UnloadBuilding17();
	bool bOk = false;
	Building17Asked = FPlatformTime::Seconds();
	ULevelStreamingDynamic* L = ULevelStreamingDynamic::LoadLevelInstance(GetWorld(), BuildingLevel17, FVector::ZeroVector, FRotator::ZeroRotator, bOk, FString::Printf(TEXT("RDBuilding17_%d_%d"), BI, ++Building17Count));
	if (!bOk || !L) { UE_LOG(LogRDBuilding17, Warning, TEXT("RDBUILDING17 the level %s did not load"), *BuildingLevel17); return false; }
	BuildingStream17 = L; PendingBuilding17 = BI;
	if (!bBuilding17Walked) ShowCover16(TEXT("building"));          // (a walk-in is not covered: the cover holds her input still in the doorway)
	UE_LOG(LogRDBuilding17, Log, TEXT("RDBUILDING17 into %d (%s): the level asked for"), BI, *RDTTheLabel17(S, BI));
	return true;
}

void ARDDungeonGenerator::TickBuilding17(float Dt)
{
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	// (a town built again, or gone: its building's level goes)
	if (Building17For.Get() != S) { if (InBuilding17 >= 0 || PendingBuilding17 >= 0 || BuildingActor17) UnloadBuilding17(); Building17For = S; }
	if (!S || !Her) return;
	// ---- the level asked for, loaded: its furnishing laid, the outside captured for its windows, she put inside its door
	if (PendingBuilding17 >= 0)
	{
		ULevelStreamingDynamic* L = BuildingStream17.Get();
		ULevel* Lv = L ? L->GetLoadedLevel() : nullptr;
		if (!Lv || !L->IsLevelVisible())
		{
			if (FPlatformTime::Seconds() - Building17Asked > 15.0) { UE_LOG(LogRDBuilding17, Warning, TEXT("RDBUILDING17 the level never came: given up")); PendingBuilding17 = -1; UnloadBuilding17(); }
			return;
		}
		const int32 BI = PendingBuilding17; PendingBuilding17 = -1;
		const ARDSection::FTownBld& B = S->TownBlds[BI];
		FActorSpawnParameters Sp; Sp.OverrideLevel = Lv; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		AActor* A = GetWorld()->SpawnActor<AActor>(AActor::StaticClass(), FTransform::Identity, Sp);
		if (!A) { UnloadBuilding17(); return; }
		USceneComponent* Root = NewObject<USceneComponent>(A, TEXT("Root")); A->SetRootComponent(Root); Root->RegisterComponent();
		BuildingActor17 = A; Building17Pieces = 0; Building17Panes = 0;
		if (const ARDSection::FBldRec17* R = S->BldRec17.Find(BI))
		{
			for (const TPair<FString, ARDSection::FBldRecPiece17>& Kv : R->Pieces)
			{
				const ARDSection::FBldRecPiece17& P = Kv.Value;
				if (!P.Mesh) continue;
				UInstancedStaticMeshComponent* H = NewObject<UInstancedStaticMeshComponent>(A);
				H->SetStaticMesh(P.Mesh);
				if (P.Mat) for (int32 Sl = 0; Sl < P.Mesh->GetStaticMaterials().Num(); ++Sl) H->SetMaterial(Sl, P.Mat);
				H->SetMobility(EComponentMobility::Static);
				H->SetupAttachment(Root);
				H->SetCollisionProfileName(P.bCol ? TEXT("BlockAll") : TEXT("NoCollision"));
				if (P.Cull > 0.f) { H->SetCullDistances(FMath::RoundToInt(P.Cull * 0.8f), FMath::RoundToInt(P.Cull)); H->SetCastShadow(false); }
				if (P.bSmall) H->SetCastShadow(false);
				H->RegisterComponent();
				for (const FTransform& T : P.T) H->AddInstance(T, true);
				A->AddInstanceComponent(H);
				Building17Pieces += P.T.Num();
			}
			for (const TPair<TObjectPtr<UClass>, FTransform>& Ac : R->Actors)
				if (Ac.Key) if (AActor* Pa = GetWorld()->SpawnActor<AActor>(Ac.Key, Ac.Value, Sp)) { Pa->AttachToActor(A, FAttachmentTransformRules::KeepWorldTransform); ++Building17Pieces; }
		}
		CaptureBuildingView17(BI);
		// (a pane in each window, on its inside, showing the street its own cube saw)
		if (BuildingPaneMesh17 && BuildingViewMaterial17)
		{
			int32 Wk = 0;
			for (const ARDSection::FTownWin16& Wn : S->TownWindows16)
			{
				if (Wn.Bld != BI) continue;
				UTextureRenderTargetCube* Cube = BuildingViews17.IsValidIndex(Wk) ? BuildingViews17[Wk].Get() : BuildingView17.Get();
				++Wk;
				if (!Cube) continue;
				UMaterialInstanceDynamic* Mi = UMaterialInstanceDynamic::Create(BuildingViewMaterial17, A);
				Mi->SetTextureParameterValue(TEXT("View"), Cube);
				Mi->SetScalarParameterValue(TEXT("Scale"), BuildingViewScale17);
				Mi->SetScalarParameterValue(TEXT("Turn"), 0.f);
				UStaticMeshComponent* Pn = NewObject<UStaticMeshComponent>(A);
				Pn->SetStaticMesh(BuildingPaneMesh17); Pn->SetMaterial(0, Mi);
				Pn->SetMobility(EComponentMobility::Movable); Pn->SetCollisionProfileName(TEXT("NoCollision")); Pn->SetCastShadow(false);
				Pn->SetupAttachment(Root);
				// (the engine's plane faces +Z: turned to face into the room, its width along the wall)
				const FVector In = -Wn.Out.GetSafeNormal2D();
				Pn->SetWorldTransform(FTransform(FRotationMatrix::MakeFromZX(In, FVector(-In.Y, In.X, 0.f)).Rotator(), Wn.At - Wn.Out * BuildingPaneIn17, FVector(BuildingPaneSize17.X / 100.f, BuildingPaneSize17.Y / 100.f, 1.f)));
				Pn->RegisterComponent(); A->AddInstanceComponent(Pn);
				++Building17Panes;
			}
		}
		// (she is put inside its door, facing in)
		const FVector Out(RDB17Dir4[B.DoorSide].X, RDB17Dir4[B.DoorSide].Y, 0.f);
		const FVector In0 = S->LocalToWorld(B.DoorTile) - Out * 40.f;
		{
			Her->SetActorLocation(FVector(In0.X, In0.Y, Her->GetActorLocation().Z), false, nullptr, ETeleportType::TeleportPhysics);
			if (ACharacter* Ch = Cast<ACharacter>(Her)) Ch->GetCharacterMovement()->StopMovementImmediately();
			Her->SetActorRotation(FRotator(0.f, (-Out).Rotation().Yaw, 0.f));
			if (AController* C = Her->GetController()) C->SetControlRotation(FRotator(-10.f, (-Out).Rotation().Yaw, 0.f));
		}
		bBuilding17Walked = false;
		InBuilding17 = BI;
		Building17LoadMs = (float)((FPlatformTime::Seconds() - Building17Asked) * 1000.0);
		++Building17Entered;
		UE_LOG(LogRDBuilding17, Log, TEXT("RDBUILDING17 in %d: %d pieces, %d panes, %.0f ms"), BI, Building17Pieces, Building17Panes, Building17LoadMs);
		return;
	}
	if (!bTown || !S->BldClosed17) return;
	// ---- walked in at a door left open: entered; walked from the one she is in into the next: that one; walked out: left
	const int32 Here = S->TownBuildingAt(Her->GetActorLocation());
	if (Here >= 0 && Here != InBuilding17 && S->HasRecord17(Here)) { bBuilding17Walked = true; if (!EnterBuilding17(Here)) bBuilding17Walked = false; return; }
	if (InBuilding17 >= 0 && Here != InBuilding17)
	{
		const ARDSection::FTownBld& B = S->TownBlds[InBuilding17];
		const FVector C = (S->LocalToWorld(B.Min) + S->LocalToWorld(B.Max - FIntPoint(1, 1))) * 0.5f;
		const float Half = FMath::Max(B.Max.X - B.Min.X, B.Max.Y - B.Min.Y) * TileSize * 0.5f;
		if (FVector::Dist2D(Her->GetActorLocation(), C) > Half + 250.f) { UnloadBuilding17(); UE_LOG(LogRDBuilding17, Log, TEXT("RDBUILDING17 walked out")); }
	}
}

bool ARDDungeonGenerator::LeaveBuilding17()
{
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!S || !Her || !S->TownBlds.IsValidIndex(InBuilding17)) return false;
	const ARDSection::FTownBld& B = S->TownBlds[InBuilding17];
	const FVector Out(RDB17Dir4[B.DoorSide].X, RDB17Dir4[B.DoorSide].Y, 0.f);
	const FVector Door = S->LocalToWorld(B.DoorTile) + Out * (TileSize * 0.5f);
	const FVector At = Door + Out * 180.f;
	Her->SetActorLocation(FVector(At.X, At.Y, Her->GetActorLocation().Z), false, nullptr, ETeleportType::TeleportPhysics);
	if (ACharacter* Ch = Cast<ACharacter>(Her)) Ch->GetCharacterMovement()->StopMovementImmediately();
	Her->SetActorRotation(FRotator(0.f, Out.Rotation().Yaw, 0.f));
	if (AController* C = Her->GetController()) C->SetControlRotation(FRotator(-10.f, Out.Rotation().Yaw, 0.f));
	UE_LOG(LogRDBuilding17, Log, TEXT("RDBUILDING17 out of %d"), InBuilding17);
	UnloadBuilding17();
	return true;
}

void ARDDungeonGenerator::UnloadBuilding17()
{
	if (AActor* A = BuildingActor17.Get()) A->Destroy();
	BuildingActor17 = nullptr;
	if (ULevelStreamingDynamic* L = BuildingStream17.Get()) { L->SetShouldBeLoaded(false); L->SetShouldBeVisible(false); L->SetIsRequestingUnloadAndRemoval(true); }
	BuildingStream17 = nullptr;
	InBuilding17 = -1; PendingBuilding17 = -1; bBuilding17Walked = false;
	// (the visit's cubes let go after it (heaven.md: session state carried for one visit))
	BuildingViews17.Reset(); BuildingView17 = nullptr;
}

void ARDDungeonGenerator::CaptureBuildingView17(int32 BI)
{
	// (the street round the building from its middle at an eye's height, the building's own pieces taken out (the tower's way))
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S || !S->TownBlds.IsValidIndex(BI)) return;
	const double T0 = FPlatformTime::Seconds();
	TArray<FTowerMoved24> Moved; TArray<UPrimitiveComponent*> Hidden; TArray<AActor*> HiddenA;
	TowerOutOfCity24(BI, Moved, Hidden, HiddenA);
	USceneCaptureComponentCube* Cap = NewObject<USceneCaptureComponentCube>(this);
	Cap->bCaptureEveryFrame = false; Cap->bCaptureOnMovement = false; Cap->bCaptureRotation = false;
	Cap->CaptureSource = ESceneCaptureSource::SCS_SceneColorHDR;
	Cap->RegisterComponent();
	for (UPrimitiveComponent* P : Hidden) Cap->HiddenComponents.Add(P);
	for (AActor* A : HiddenA) Cap->HiddenActors.Add(A);
	if (AActor* A = BuildingActor17.Get()) Cap->HiddenActors.Add(A);
	UVolumetricCloudComponent* Cl = SkyClouds.Get();
	const bool bClouds = Cl && Cl->IsVisible();
	if (bClouds) Cl->SetVisibility(false);
	// (a cube a window, just inside it at its height (its own street, no parallax from the building's middle); the middle's for any past 40)
	int32 Wk = 0;
	for (const ARDSection::FTownWin16& Wn : S->TownWindows16)
	{
		if (Wn.Bld != BI || Wk >= 40) continue;
		if (BuildingViews17.Num() <= Wk) BuildingViews17.SetNum(Wk + 1);
		TObjectPtr<UTextureRenderTargetCube>& Rt = BuildingViews17[Wk];
		if (!Rt) { Rt = NewObject<UTextureRenderTargetCube>(this); Rt->Init(FMath::Clamp(BuildingWindowCapture17, 32, 1024), PF_FloatRGBA); }
		Cap->TextureTarget = Rt;
		Cap->SetWorldLocation(Wn.At - Wn.Out.GetSafeNormal2D() * 30.f);
		Cap->CaptureScene(); if (Wk == 0) Cap->CaptureScene();          // (the first twice: the GPU's copy of the moved pieces comes with the first)
		++Wk;
	}
	const FVector Ctr = S->TownBldPoint24(S->TownBlds[BI], 0.f, 0.f, 0.f);
	int32 Nw = 0; for (const ARDSection::FTownWin16& Wn : S->TownWindows16) if (Wn.Bld == BI) ++Nw;
	if (Nw > 40)
	{
		if (!BuildingView17) { BuildingView17 = NewObject<UTextureRenderTargetCube>(this); BuildingView17->Init(FMath::Clamp(BuildingCaptureSize17, 128, 2048), PF_FloatRGBA); }
		Cap->TextureTarget = BuildingView17;
		Cap->SetWorldLocation(FVector(Ctr.X, Ctr.Y, S->GetActorLocation().Z + 160.f));
		Cap->CaptureScene();
	}
	if (bClouds) Cl->SetVisibility(true);
	Cap->DestroyComponent();
	TowerBackInCity24(Moved);
	Building17CaptureMs = (float)((FPlatformTime::Seconds() - T0) * 1000.0);
	Building17ViewAt = FVector(Ctr.X, Ctr.Y, S->GetActorLocation().Z + 160.f);
}

// ================================================================================================ the tests
void ARDDungeonGenerator::SetBuildingPanes17(bool bShow)
{
	// (tests: the panes hidden, to see the street through the window's opening itself)
	if (AActor* A = BuildingActor17.Get())
	{
		TInlineComponentArray<UStaticMeshComponent*> Ms(A);
		for (UStaticMeshComponent* C : Ms) if (!C->IsA<UInstancedStaticMeshComponent>()) C->SetHiddenInGame(!bShow);
	}
}

TArray<FString> ARDDungeonGenerator::GetBuildingWindows17(int32 BI) const
{
	TArray<FString> Out;
	if (const ARDSection* S = GetSection(FIntPoint::ZeroValue))
		for (const ARDSection::FTownWin16& Wn : S->TownWindows16) if (Wn.Bld == BI) Out.Add(FString::Printf(TEXT("%.0f|%.0f|%.0f|%.3f|%.3f"), Wn.At.X, Wn.At.Y, Wn.At.Z, Wn.Out.X, Wn.Out.Y));
	return Out;
}

FString ARDDungeonGenerator::GetBuilding17State() const
{
	// ("<closed 0/1>|<in>|<pending>|<level loaded>|<pieces laid>|<panes>|<load ms>|<capture ms>|<entered>|<view x>|<view y>|<view z>")
	const ULevelStreamingDynamic* L = BuildingStream17.Get();
	return FString::Printf(TEXT("%d|%d|%d|%d|%d|%d|%.0f|%.0f|%d|%.0f|%.0f|%.0f"), Closed17() ? 1 : 0, InBuilding17, PendingBuilding17, L && L->GetLoadedLevel() ? 1 : 0, Building17Pieces, Building17Panes,
		Building17LoadMs, Building17CaptureMs, Building17Entered, Building17ViewAt.X, Building17ViewAt.Y, Building17ViewAt.Z);
}

TArray<FString> ARDDungeonGenerator::GetBuildingPieces17(int32 BI, bool bLevel) const
{
	// (tests: a building's furnishing, "<mesh>|<x>|<y>|<z>|<yaw>": as the town drew it (Immersive: its own batches), as it recorded it, or (bLevel)
	// as its level laid it)
	TArray<FString> Out;
	auto Line = [&Out](const UStaticMesh* M, const FTransform& T) { Out.Add(FString::Printf(TEXT("%s|%.0f|%.0f|%.0f|%.0f"), M ? *M->GetName() : TEXT("-"), T.GetLocation().X, T.GetLocation().Y, T.GetLocation().Z, T.Rotator().Yaw)); };
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S) return Out;
	if (bLevel)
	{
		if (const AActor* A = BuildingActor17.Get())
		{
			TInlineComponentArray<UInstancedStaticMeshComponent*> Is(A);
			for (const UInstancedStaticMeshComponent* C : Is) for (int32 I = 0; I < C->GetInstanceCount(); ++I) { FTransform T; C->GetInstanceTransform(I, T, true); Line(C->GetStaticMesh(), T); }
		}
		return Out;
	}
	if (const ARDSection::FBldRec17* R = S->BldRec17.Find(BI))
	{
		for (const TPair<FString, ARDSection::FBldRecPiece17>& Kv : R->Pieces) for (const FTransform& T : Kv.Value.T) Line(Kv.Value.Mesh, T);
		return Out;
	}
	if (const TArray<TWeakObjectPtr<UInstancedStaticMeshComponent>>* Is = S->TownBldIsm16.Find(BI))
		for (const TWeakObjectPtr<UInstancedStaticMeshComponent>& W : *Is) if (const UInstancedStaticMeshComponent* C = W.Get())
			for (int32 I = 0; I < C->GetInstanceCount(); ++I) { FTransform T; C->GetInstanceTransform(I, T, true); Line(C->GetStaticMesh(), T); }
	return Out;
}

TArray<FString> ARDDungeonGenerator::GetEnterable17() const
{
	// (tests: every enterable building, "<index>|<kind>|<label>|<recorded pieces>|<door x>|<door y>|<out x>|<out y>|<windows>|<door index>")
	TArray<FString> Out;
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S) return Out;
	for (int32 I = 0; I < S->TownBlds.Num(); ++I)
	{
		if (!IsEnterable17(S, I)) continue;
		const ARDSection::FTownBld& B = S->TownBlds[I];
		const FVector Out_(RDB17Dir4[B.DoorSide].X, RDB17Dir4[B.DoorSide].Y, 0.f);
		const FVector Door = S->LocalToWorld(B.DoorTile) + Out_ * (TileSize * 0.5f);
		const ARDSection::FBldRec17* R = S->BldRec17.Find(I);
		int32 Nw = 0; for (const ARDSection::FTownWin16& Wn : S->TownWindows16) if (Wn.Bld == I) ++Nw;
		Out.Add(FString::Printf(TEXT("%d|%d|%s|%d|%.0f|%.0f|%.0f|%.0f|%d|%d"), I, (int32)B.Kind, *B.Label, R ? R->N : 0, Door.X, Door.Y, Out_.X, Out_.Y, Nw, B.Door));
	}
	return Out;
}
