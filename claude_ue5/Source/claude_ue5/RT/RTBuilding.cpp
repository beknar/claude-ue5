#include "RT/RTBuilding.h"
#include "RT/RTTownGenerator.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/Level.h"
#include "Engine/LevelStreamingDynamic.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "LevelInstance/LevelInstanceActor.h"
#include "LevelInstance/LevelInstanceSubsystem.h"
#include "InputCoreTypes.h"

static const FName RTInteractiveTag(TEXT("RTInteractive"));
static int32 GRTLevelCounter = 0;

ARTBuilding::ARTBuilding()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.0f;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent->SetMobility(EComponentMobility::Static);
}

const FRTBuildingTemplate* ARTBuilding::GetTemplate() const
{
	return (Generator && Generator->Templates.IsValidIndex(TemplateIndex)) ? &Generator->Templates[TemplateIndex] : nullptr;
}

FName ARTBuilding::GetPurpose() const { const FRTBuildingTemplate* T = GetTemplate(); return T ? T->Purpose : NAME_None; }
FName ARTBuilding::GetTemplateName() const { const FRTBuildingTemplate* T = GetTemplate(); return T ? T->Name : NAME_None; }

void ARTBuilding::Init(ARTTownGenerator* InGenerator, int32 InTemplate, bool bEditorBuild)
{
	Generator = InGenerator; TemplateIndex = InTemplate;
	const FRTBuildingTemplate* T = GetTemplate();
	if (!T) return;
	UWorld* W = GetWorld();
	const FTransform B = GetActorTransform();
	if (!T->ActorClass.IsNull())
	{
		if (UClass* C = T->ActorClass.LoadSynchronous())
		{
			FActorSpawnParameters P; P.Owner = this; P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			PrefabActor = W->SpawnActor<AActor>(C, B, P);
			if (PrefabActor) PrefabActor->AttachToActor(this, FAttachmentTransformRules::KeepWorldTransform);
		}
	}
	else if (!T->Level.IsNull())
	{
#if WITH_EDITOR
		if (bEditorBuild)
		{
			FActorSpawnParameters P; P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			ALevelInstance* LI = W->SpawnActor<ALevelInstance>(ALevelInstance::StaticClass(), B, P);
			if (LI)
			{
				LI->SetWorldAsset(T->Level);
				LI->LoadLevelInstance();
				LI->SetActorLabel(FString::Printf(TEXT("%s_Interior"), *GetActorLabel()));
				LI->SetFolderPath(TEXT("RandomTown/Interiors"));
				EditorLevelInstance = LI;
			}
		}
		else
#endif
		{
			bool bOk = false;
			const FString Name = FString::Printf(TEXT("RTBld_%d_%s"), ++GRTLevelCounter, *T->Name.ToString());
			Streamed = ULevelStreamingDynamic::LoadLevelInstanceBySoftObjectPtr(this, T->Level, B, bOk, Name);
		}
	}
	CreateInteractive();
	bInitialized = true;
}

USceneComponent* ARTBuilding::AddPivot(USceneComponent* Parent, const FTransform& Rel)
{
	USceneComponent* C = NewObject<USceneComponent>(this, NAME_None, RF_Transactional);
	C->ComponentTags.Add(RTInteractiveTag);
	C->SetMobility(EComponentMobility::Movable);
	C->SetupAttachment(Parent);
	C->SetRelativeTransform(Rel);
	C->RegisterComponent();
	AddInstanceComponent(C);
	return C;
}

UStaticMeshComponent* ARTBuilding::AddMesh(USceneComponent* Parent, UStaticMesh* Mesh, const FTransform& Rel, bool bCollision)
{
	UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this, NAME_None, RF_Transactional);
	C->ComponentTags.Add(RTInteractiveTag);
	C->SetMobility(EComponentMobility::Movable);
	C->SetStaticMesh(Mesh);
	C->SetupAttachment(Parent);
	C->SetRelativeTransform(Rel);
	C->SetCollisionProfileName(bCollision ? TEXT("BlockAllDynamic") : TEXT("NoCollision"));
	C->RegisterComponent();
	AddInstanceComponent(C);
	return C;
}

void ARTBuilding::ClearInteractive()
{
	TArray<UActorComponent*> Comps;
	GetComponents(Comps);
	for (UActorComponent* C : Comps)
		if (C && C->ComponentHasTag(RTInteractiveTag)) C->DestroyComponent();
	Doors.Reset(); Containers.Reset();
}

/** sign of an angle about Axis that lifts / swings Tip toward Want */
static float PickSign(const FVector& Axis, const FVector& Tip, const FVector& Want)
{
	const FVector P = FQuat(Axis, FMath::DegreesToRadians(60.f)).RotateVector(Tip);
	return FVector::DotProduct(P - Tip, Want) >= 0.f ? 1.f : -1.f;
}

void ARTBuilding::AddLidContainer(UStaticMesh* Body, UStaticMesh* Lid, const FVector& Loc, float Yaw, float HingeY, float BodyH, const FString& Kind)
{
	if (!Body || !Lid) return;
	USceneComponent* Base = AddPivot(RootComponent, FTransform(FRotator(0, Yaw, 0), Loc));
	AddMesh(Base, Body, FTransform::Identity, true);
	USceneComponent* Hinge = AddPivot(Base, FTransform(FVector(0, HingeY, BodyH)));
	UStaticMeshComponent* L = AddMesh(Hinge, Lid, FTransform::Identity, true);
	FMover M; M.Pivot = Hinge; M.Parts = { L }; M.Closed = FQuat::Identity; M.Axis = FVector::ForwardVector; M.Kind = Kind;
	M.OpenAngle = 100.f * PickSign(M.Axis, FVector(0, 50, 0), FVector::UpVector);
	M.Center = GetActorTransform().TransformPosition(Loc + FRotator(0, Yaw, 0).RotateVector(FVector(0, 0, BodyH)));
	Containers.Add(M);
}

void ARTBuilding::CreateInteractive()
{
	ClearInteractive();
	const FRTBuildingTemplate* T = GetTemplate();
	if (!T || !Generator) return;
	const FTransform B = GetActorTransform();
	// doors: hinged copies of the template's leaves, shut
	for (const FRTDoorDef& D : T->Doors)
	{
		if (!D.Mesh) continue;
		USceneComponent* P = AddPivot(RootComponent, FTransform(FRotator(0, D.ClosedYaw, 0), D.Location));
		UStaticMeshComponent* L = AddMesh(P, D.Mesh, FTransform(FQuat::Identity, FVector::ZeroVector, D.Scale), true);
		FMover M; M.Pivot = P; M.Parts = { L }; M.Closed = P->GetRelativeRotation().Quaternion(); M.bDoor = true; M.Kind = TEXT("door");
		const FBox MB = D.Mesh->GetBoundingBox();
		M.bDoor01Side = MB.GetCenter().X >= 0.f;
		const float Half = MB.GetSize().X * 0.5f * (M.bDoor01Side ? 1.f : -1.f);
		const FRotator CY(0, D.ClosedYaw, 0);
		M.Center = B.TransformPosition(D.Location + CY.RotateVector(FVector(Half, 0, 100)));
		M.Normal = B.TransformVectorNoScale(CY.RotateVector(FVector(0, 1, 0)));
		Doors.Add(M);
	}
	// existing crate lids: hinged copies (the originals are hidden once the interior is loaded)
	for (const FRTLidDef& Ld : T->Lids)
	{
		if (!Ld.Mesh) continue;
		USceneComponent* P = AddPivot(RootComponent, Ld.Transform);
		UStaticMeshComponent* L = AddMesh(P, Ld.Mesh, FTransform::Identity, true);
		FMover M; M.Pivot = P; M.Parts = { L }; M.Axis = FVector::ForwardVector; M.Kind = TEXT("crate");
		const FBox MB = Ld.Mesh->GetBoundingBox();          // pivot at a corner: hinge along local X at y = 0
		M.OpenAngle = 105.f * PickSign(M.Axis, FVector(0, MB.GetCenter().Y, 0), FVector::UpVector);
		M.Center = B.TransformPosition(Ld.Transform.TransformPosition(MB.GetCenter()));
		Containers.Add(M);
	}
	// additions: bedroom chests, wardrobes (openable), washstands
	for (const FRTAddition& A : T->Additions)
	{
		switch (A.Kind)
		{
		case ERTAddKind::Chest: AddLidContainer(Generator->ChestBody, Generator->ChestLid, A.Location, A.Yaw, -26.f, 45.f, TEXT("chest")); break;
		case ERTAddKind::Trunk: AddLidContainer(Generator->TrunkBody, Generator->TrunkLid, A.Location, A.Yaw, -31.f, 50.f, TEXT("trunk")); break;
		case ERTAddKind::Washstand:
		{
			if (!Generator->Washstand) break;
			USceneComponent* Base = AddPivot(RootComponent, FTransform(FRotator(0, A.Yaw, 0), A.Location));
			AddMesh(Base, Generator->Washstand, FTransform::Identity, true);
			break;
		}
		case ERTAddKind::Wardrobe:
		{
			if (!Generator->WardrobeBody || !Generator->WardrobeDoorL || !Generator->WardrobeDoorR) break;
			USceneComponent* Base = AddPivot(RootComponent, FTransform(FRotator(0, A.Yaw, 0), A.Location));
			AddMesh(Base, Generator->WardrobeBody, FTransform::Identity, true);
			FMover M; M.Kind = TEXT("wardrobe"); M.Axis = FVector::UpVector;
			// two doors on one mover: left hinge at x -53, right at +53, front face y 30
			USceneComponent* PL = AddPivot(Base, FTransform(FVector(-53, 30, 8)));
			USceneComponent* PR = AddPivot(Base, FTransform(FVector(53, 30, 8)));
			M.Pivot = PL; M.Parts = { AddMesh(PL, Generator->WardrobeDoorL, FTransform::Identity, true) };
			M.OpenAngle = 100.f * PickSign(M.Axis, FVector(53, 0, 0), FVector(0, 1, 0));
			M.Center = B.TransformPosition(A.Location + FRotator(0, A.Yaw, 0).RotateVector(FVector(0, 30, 100)));
			Containers.Add(M);
			FMover M2 = M; M2.Pivot = PR; M2.Parts = { AddMesh(PR, Generator->WardrobeDoorR, FTransform::Identity, true) };
			M2.OpenAngle = 100.f * PickSign(M2.Axis, FVector(-53, 0, 0), FVector(0, 1, 0)); M2.Kind = TEXT("wardrobe_r");
			Containers.Add(M2);
			break;
		}
		}
	}
}

bool ARTBuilding::TryProcessInterior()
{
	const FRTBuildingTemplate* T = GetTemplate();
	if (!T) return true;
	TArray<AActor*> Actors;
	if (PrefabActor)
	{
		Actors.Add(PrefabActor);
	}
	else if (EditorLevelInstance)
	{
		ULevelInstanceSubsystem* LIS = GetWorld()->GetSubsystem<ULevelInstanceSubsystem>();
		ILevelInstanceInterface* LI = Cast<ILevelInstanceInterface>(EditorLevelInstance);
		if (!LIS || !LI || !LIS->IsLoaded(LI)) return false;
		LIS->ForEachActorInLevelInstance(LI, [&Actors](AActor* A) { Actors.Add(A); return true; });
	}
	else if (Streamed)
	{
		if (!Streamed->IsLevelLoaded() || !Streamed->IsLevelVisible() || !Streamed->GetLoadedLevel()) return false;
		for (AActor* A : Streamed->GetLoadedLevel()->Actors) if (A) Actors.Add(A);
	}
	else return true;
	if (Actors.Num() == 0) return false;
	// hide the original leaves / lids that the interactive copies replace
	const FTransform B = GetActorTransform();
	struct FTarget { UStaticMesh* Mesh; FVector Loc; };
	TArray<FTarget> Targets;
	for (const FRTDoorDef& D : T->Doors) Targets.Add({ D.Mesh, B.TransformPosition(D.Location) });
	for (const FRTLidDef& L : T->Lids) Targets.Add({ L.Mesh, B.TransformPosition(L.Transform.GetLocation()) });
	for (AActor* A : Actors)
	{
		TArray<UStaticMeshComponent*> Comps;
		A->GetComponents(Comps);
		for (UStaticMeshComponent* C : Comps)
		{
			if (!C || C->ComponentHasTag(RTInteractiveTag)) continue;
			for (const FTarget& Tg : Targets)
			{
				if (C->GetStaticMesh() == Tg.Mesh && FVector::Dist(C->GetComponentLocation(), Tg.Loc) < 30.f)
				{
					C->SetVisibility(false); C->SetHiddenInGame(true);
					C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
					++HiddenOriginals;
					break;
				}
			}
		}
	}
	return true;
}

void ARTBuilding::BeginPlay()
{
	Super::BeginPlay();
	// saved start-square buildings: rebuild the interactive parts (the editor copies are previews)
	if (Generator && TemplateIndex >= 0 && !bInitialized)
	{
		CreateInteractive();
		bInitialized = true;
	}
}

void ARTBuilding::EndPlay(const EEndPlayReason::Type Reason)
{
	if (Streamed)
	{
		Streamed->SetShouldBeLoaded(false);
		Streamed->SetShouldBeVisible(false);
		Streamed->SetIsRequestingUnloadAndRemoval(true);
		Streamed = nullptr;
	}
	Super::EndPlay(Reason);
}

void ARTBuilding::Destroyed()
{
	if (Streamed)
	{
		Streamed->SetShouldBeLoaded(false); Streamed->SetShouldBeVisible(false); Streamed->SetIsRequestingUnloadAndRemoval(true);
		Streamed = nullptr;
	}
	if (EditorLevelInstance) { EditorLevelInstance->Destroy(); EditorLevelInstance = nullptr; }
	if (PrefabActor) { PrefabActor->Destroy(); PrefabActor = nullptr; }
	Super::Destroyed();
}

void ARTBuilding::Tick(float Dt)
{
	Super::Tick(Dt);
	UWorld* W = GetWorld();
	if (!W || !W->IsGameWorld()) return;
	if (!bProcessed)
	{
		WaitTime += Dt;
		bProcessed = TryProcessInterior() || WaitTime > 30.f;
	}
	APawn* Pawn = UGameplayStatics::GetPlayerPawn(this, 0);
	const FVector PL = Pawn ? Pawn->GetActorLocation() : FVector(1e9);
	// doors: open away from the player while she is near, close once she has gone
	for (FMover& M : Doors)
	{
		const FVector D = PL - M.Center;
		const float H = FVector2D(D.X, D.Y).Size();
		if (M.Target == 0.f && H < 260.f && FMath::Abs(D.Z) < 200.f)
		{
			const float Side = FVector::DotProduct(D, M.Normal) >= 0.f ? 1.f : -1.f;   // player on the +normal side
			// +yaw swings a +X leaf toward +normal: swing away from the player
			M.OpenAngle = 95.f * (-Side) * (M.bDoor01Side ? 1.f : -1.f);
			M.Target = 1.f;
		}
		else if (M.Target == 1.f && (H > 380.f || FMath::Abs(D.Z) > 260.f)) M.Target = 0.f;
	}
	// containers: F next to one toggles the nearest
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
		if (PC->WasInputKeyJustPressed(EKeys::F) && Pawn) ToggleNearestContainer(PL, 200.f);
	auto Animate = [Dt](FMover& M)
	{
		if (M.Alpha == M.Target) return;
		M.Alpha = FMath::FInterpConstantTo(M.Alpha, M.Target, Dt, M.bDoor ? 1.6f : 1.8f);
		const float E = M.Alpha * M.Alpha * (3.f - 2.f * M.Alpha);
		M.Pivot->SetRelativeRotation(M.Closed * FQuat(M.Axis, FMath::DegreesToRadians(M.OpenAngle * E)));
		const bool bShut = M.Alpha < 0.02f;
		for (UStaticMeshComponent* C : M.Parts)
			C->SetCollisionEnabled(bShut || !M.bDoor ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
	};
	for (FMover& M : Doors) Animate(M);
	for (FMover& M : Containers) Animate(M);
}

void ARTBuilding::GetEntry(FVector& Street, FVector& Outside, FVector& Inside) const
{
	const FRTBuildingTemplate* T = GetTemplate();
	if (!T) { Street = Outside = Inside = GetActorLocation(); return; }
	const FTransform B = GetActorTransform();
	const FVector Mid(T->EntryMid.X, T->EntryMid.Y, T->FloorZ), Out(T->EntryOut.X, T->EntryOut.Y, 0);
	Outside = B.TransformPosition(Mid + Out * 250.f);
	Inside = B.TransformPosition(Mid - Out * 100.f);
	Street = StreetPoint;
}

int32 ARTBuilding::GetNumInteriorPaths() const { const FRTBuildingTemplate* T = GetTemplate(); return T ? T->Paths.Num() : 0; }

TArray<FVector> ARTBuilding::GetInteriorPath(int32 Index) const
{
	TArray<FVector> Out;
	const FRTBuildingTemplate* T = GetTemplate();
	if (!T || !T->Paths.IsValidIndex(Index)) return Out;
	const FTransform B = GetActorTransform();
	for (const FVector2D& P : T->Paths[Index].Points) Out.Add(B.TransformPosition(FVector(P.X, P.Y, T->FloorZ)));
	return Out;
}

float ARTBuilding::GetDoorOpenAlpha(int32 I) const { return Doors.IsValidIndex(I) ? Doors[I].Alpha : -1.f; }
FVector ARTBuilding::GetDoorLocation(int32 I) const { return Doors.IsValidIndex(I) ? Doors[I].Center : FVector::ZeroVector; }
bool ARTBuilding::IsContainerOpen(int32 I) const { return Containers.IsValidIndex(I) && Containers[I].Target > 0.5f; }
float ARTBuilding::GetContainerOpenAlpha(int32 I) const { return Containers.IsValidIndex(I) ? Containers[I].Alpha : -1.f; }
FVector ARTBuilding::GetContainerLocation(int32 I) const { return Containers.IsValidIndex(I) ? Containers[I].Center : FVector::ZeroVector; }
FString ARTBuilding::GetContainerKind(int32 I) const { return Containers.IsValidIndex(I) ? Containers[I].Kind : FString(); }

bool ARTBuilding::ToggleContainer(int32 I)
{
	if (!Containers.IsValidIndex(I)) return false;
	FMover& M = Containers[I];
	M.Target = M.Target > 0.5f ? 0.f : 1.f;
	// a wardrobe opens both doors together
	if (M.Kind == TEXT("wardrobe") && Containers.IsValidIndex(I + 1)) Containers[I + 1].Target = M.Target;
	if (M.Kind == TEXT("wardrobe_r") && Containers.IsValidIndex(I - 1)) Containers[I - 1].Target = M.Target;
	return true;
}

int32 ARTBuilding::ToggleNearestContainer(FVector From, float MaxDistance)
{
	int32 Best = -1; float BestD = MaxDistance;
	for (int32 I = 0; I < Containers.Num(); ++I)
	{
		const FVector D = Containers[I].Center - From;
		const float H = FVector2D(D.X, D.Y).Size();
		if (H < BestD && FMath::Abs(D.Z) < 180.f) { BestD = H; Best = I; }
	}
	if (Best >= 0) ToggleContainer(Best);
	return Best;
}
