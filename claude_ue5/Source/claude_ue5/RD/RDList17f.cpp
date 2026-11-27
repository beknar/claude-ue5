// The user's list of 2026-11-26 (docs/improvements17.txt; the plan docs/improvements17_plan.md), its eighth phase: Closed Structures in the wilds.
//   "Make a game mode ... that makes all buildings their own level, where opening a door opens a new level just for that building."
//   - The wilds' houses (a village's or a lone house: the village houses' open copies, RDWild10.cpp's FitWildHouse) and the farmsteads'
//     buildings of the town's kit (RDWildFarm11.cpp's WildKitBuilding) are laid as before, every draw and every overlap test in its place;
//     each one's furniture and lamp are recorded (both modes), and in Closed Structures taken out of the chunk once laid: not drawn there.
//     Their containers, doors, beds' places, hearths, households and ovens stay the chunk's own, as in Immersive Interiors.
//   - Walking in through its door (F opens it as before) streams in the building level (town_building, the towns' own) at the building's
//     place with its recorded furniture and lamp laid in it; walking out lets it go.
//   - The kit buildings' windows have a pane facing out with a room of their kind (949 rooms' pictures: a farmhouse a home, a barn, shed,
//     coop or granary a storehouse), glowing in the evening (19:00 to 23:30), when the farm folk are awake (RDList14f.cpp). The village
//     houses are the packs' meshes: their window openings are not known, and they have no panes.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "Engine/LevelStreamingDynamic.h"
#include "Engine/Level.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "ProceduralMeshComponent.h"
#include "Kismet/GameplayStatics.h"
#include "HAL/PlatformTime.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList17f, Log, All);

namespace
{
	FVector RDL17fAt(const FVector& O, float Yaw, float X, float Y, float Z) { return O + FRotator(0.f, Yaw, 0.f).RotateVector(FVector(X, Y, 0.f)) + FVector(0, 0, Z); }
}

// ================================================================================================ the record, made as a building is laid
void ARDDungeonGenerator::RemoveWildRoom17(int32 I)
{
	// (PR #144's review: the level she is in or waits for goes with its record, and both indices follow the list)
	if (!WildBlds17.IsValidIndex(I)) return;
	if (I == InWild17 || I == PendingWild17) UnloadWild17();
	WildBlds17.RemoveAt(I);
	if (InWild17 > I) --InWild17;
	if (PendingWild17 > I) --PendingWild17;
}

int32 ARDDungeonGenerator::BeginWildRoom17(ARDWildChunk* C, const FVector& O, float Yaw, const FVector2D& Mn, const FVector2D& Mx, float Floor, const FString& Kind, int32 Farm)
{
	if (!C) return -1;
	// (laid again in place (the chunk made again): the old record goes)
	for (int32 I = WildBlds17.Num() - 1; I >= 0; --I)
		if (!WildBlds17[I].C.IsValid() || (WildBlds17[I].C.Get() == C && FVector::Dist(WildBlds17[I].O, O) < 5.f)) RemoveWildRoom17(I);
	FWildBld17& B = WildBlds17.AddDefaulted_GetRef();
	B.C = C; B.O = O; B.Yaw = Yaw; B.Mn = Mn; B.Mx = Mx; B.Floor = Floor; B.Kind = Kind; B.bClosed = Closed17(); B.Farm = Farm; B.Made = FPlatformTime::Seconds();
	return WildBlds17.Num() - 1;
}

void ARDDungeonGenerator::AddWildPending17(ARDWildChunk* C, const FVector& O, UStaticMeshComponent* Sm)
{
	// (a household's bed laid after its house: recorded with the house's furniture and taken with it)
	if (!C || !Sm || !Sm->GetStaticMesh()) return;
	for (int32 I = 0; I < WildBlds17.Num(); ++I)
		if (WildBlds17[I].C.Get() == C && FVector::Dist2D(WildBlds17[I].O, O) < 5.f && !WildBlds17[I].bTaken)
		{
			RecordWildPiece17(I, Sm->GetStaticMesh(), Sm->GetMaterial(0), Sm->GetCollisionEnabled() != ECollisionEnabled::NoCollision, Sm->GetComponentTransform());
			WildBlds17[I].Pend.Add(Sm);
			return;
		}
}

void ARDDungeonGenerator::RecordWildPiece17(int32 Ri, UStaticMesh* Mesh, UMaterialInterface* Mat, bool bCol, const FTransform& W)
{
	if (!WildBlds17.IsValidIndex(Ri) || !Mesh) return;
	FWildBld17& B = WildBlds17[Ri];
	const FString Key = FString::Printf(TEXT("%s|%s|%d"), *Mesh->GetPathName(), Mat ? *Mat->GetPathName() : TEXT("-"), bCol ? 1 : 0);
	FWildPiece17& P = B.Pieces.FindOrAdd(Key);
	P.Mesh = Mesh; P.Mat = Mat; P.bCol = bCol; P.T.Add(W);
	++B.N;
}

void ARDDungeonGenerator::TakeWildProps17(int32 Ri, ARDWildChunk* C, int32 From)
{
	// (a village house's furniture: its own components laid since From on the chunk's ground (a container's parts are on their own base));
	// the fireplace stays the chunk's (its fire burns in it, seen through the door: PR #144's review); taken once the households are laid
	if (!WildBlds17.IsValidIndex(Ri) || !C) return;
	const FRDPiece* Fp = Piece(TEXT("Fireplace"));
	for (int32 K = From; K < C->PlaceProps.Num(); ++K)
	{
		UStaticMeshComponent* P = C->PlaceProps[K];
		if (!P || P->GetAttachParent() != C->Ground || !P->GetStaticMesh() || (Fp && P->GetStaticMesh() == Fp->Mesh)) continue;
		RecordWildPiece17(Ri, P->GetStaticMesh(), P->GetMaterial(0), P->GetCollisionEnabled() != ECollisionEnabled::NoCollision, P->GetComponentTransform());
		WildBlds17[Ri].Pend.Add(P);
	}
}

void ARDDungeonGenerator::TakeWildBatch17(int32 Ri, TMap<FString, TWeakObjectPtr<UInstancedStaticMeshComponent>>& Batch, const TMap<FString, int32>& Snap, const TArray<const UStaticMesh*>& Keep)
{
	// (a farm building's furniture: the instances its batch components gained since Snap, the oven's (a station) and the fireplace's left)
	if (!WildBlds17.IsValidIndex(Ri)) return;
	const bool bTake = WildBlds17[Ri].bClosed;
	for (const TPair<FString, TWeakObjectPtr<UInstancedStaticMeshComponent>>& Kv : Batch)
	{
		UInstancedStaticMeshComponent* Is = Kv.Value.Get();
		if (!Is || !Is->GetStaticMesh() || Keep.Contains(Is->GetStaticMesh()) || !Is->IsVisible()) continue;
		const int32* S0 = Snap.Find(Kv.Key);
		const int32 From = S0 ? *S0 : 0, To = Is->GetInstanceCount();
		if (To <= From) continue;
		TArray<int32> Gone;
		for (int32 I = From; I < To; ++I)
		{
			FTransform T; if (!Is->GetInstanceTransform(I, T, true)) continue;
			RecordWildPiece17(Ri, Is->GetStaticMesh(), Is->GetMaterial(0), Is->GetCollisionEnabled() != ECollisionEnabled::NoCollision, T);
			Gone.Add(I);
		}
		if (bTake && Gone.Num() > 0) Is->RemoveInstances(Gone);
	}
}

bool ARDDungeonGenerator::TakeWildLamp17(int32 Ri, UPointLightComponent* Lt)
{
	if (!WildBlds17.IsValidIndex(Ri) || !Lt) return false;
	FWildBld17& B = WildBlds17[Ri];
	B.Lamps.Add(FVector4(Lt->GetComponentLocation(), Lt->Intensity));
	B.LampR = Lt->AttenuationRadius;
	if (!B.bClosed) return false;
	Lt->DestroyComponent();
	return true;
}

void ARDDungeonGenerator::AddWildPanes17(int32 Ri, const TArray<FTransform>& Windows, TArray<TWeakObjectPtr<UActorComponent>>* Keep)
{
	// (a pane facing out in each window of a closed kit building: a room of its kind)
	if (!WildBlds17.IsValidIndex(Ri) || !BuildingPaneMesh17) return;
	FWildBld17& B = WildBlds17[Ri];
	ARDWildChunk* C = B.C.Get();
	if (!B.bClosed || !C || !C->Ground || Windows.Num() == 0) return;
	const FName Key = B.Kind == TEXT("house") ? FName(TEXT("home")) : FName(TEXT("storehouse"));
	const TObjectPtr<UMaterialInterface>* M = RoomPanes17.Find(Key);
	if (!M || !*M) M = RoomPanes17.Find(FName(TEXT("home")));
	if (!M || !*M) return;
	UInstancedStaticMeshComponent* H = NewObject<UInstancedStaticMeshComponent>(C);
	H->SetStaticMesh(BuildingPaneMesh17); H->SetMaterial(0, *M);
	H->NumCustomDataFloats = 1;
	H->SetCollisionProfileName(TEXT("NoCollision")); H->SetCastShadow(false);
	H->SetCullDistances(6000, 8000);
	H->SetupAttachment(C->Ground);
	H->ComponentTags.Add(TEXT("RDPane17"));
	H->RegisterComponent();
	for (const FTransform& Wn : Windows)
	{
		const FVector Out = Wn.GetRotation().GetForwardVector().GetSafeNormal2D();
		H->AddInstance(FTransform(FRotationMatrix::MakeFromZX(Out, FVector(Out.Y, -Out.X, 0.f)).Rotator(), Wn.GetLocation() + Out * BuildingPaneOut17,
			FVector(BuildingPaneSize17.X / 100.f, BuildingPaneSize17.Y / 100.f, 1.f)), true);
	}
	B.PaneC = H; B.Panes = Windows.Num();
	if (Keep) Keep->Add(H);
}

// ================================================================================================ in and out
bool ARDDungeonGenerator::WildRoomAt17(int32 Ri, const FVector& P, float Pad) const
{
	if (!WildBlds17.IsValidIndex(Ri)) return false;
	const FWildBld17& B = WildBlds17[Ri];
	const FVector L = FRotator(0.f, -B.Yaw, 0.f).RotateVector(P - B.O);
	return L.X > B.Mn.X - Pad && L.X < B.Mx.X + Pad && L.Y > B.Mn.Y - Pad && L.Y < B.Mx.Y + Pad && P.Z > B.Floor - 120.f && P.Z < B.Floor + 450.f;
}

void ARDDungeonGenerator::UnloadWild17()
{
	if (AActor* A = WildActor17.Get()) A->Destroy();
	WildActor17 = nullptr;
	if (ULevelStreamingDynamic* L = WildStream17.Get()) { L->SetShouldBeLoaded(false); L->SetShouldBeVisible(false); L->SetIsRequestingUnloadAndRemoval(true); }
	WildStream17 = nullptr;
	InWild17 = -1; PendingWild17 = -1;
}

void ARDDungeonGenerator::TickWildBld17(float Dt, const FVector& Her)
{
	// (the records of chunks let go, let go, every 2 s)
	Wild17PruneT -= Dt;
	if (Wild17PruneT <= 0.f)
	{
		Wild17PruneT = 2.f;
		for (int32 I = WildBlds17.Num() - 1; I >= 0; --I) if (!WildBlds17[I].C.IsValid()) RemoveWildRoom17(I);
	}
	// (a village house's furniture and beds taken out of a closed chunk once every household queued is laid, half a second on)
	if (VillageHouseQueue15.Num() == 0)
		for (FWildBld17& B : WildBlds17)
		{
			if (B.bTaken || B.Pend.Num() == 0 || FPlatformTime::Seconds() - B.Made < 0.5) continue;
			B.bTaken = true;
			if (B.bClosed)
				if (ARDWildChunk* C = B.C.Get())
					for (const TWeakObjectPtr<UStaticMeshComponent>& W : B.Pend)
						if (UStaticMeshComponent* P = W.Get()) { C->PlaceProps.Remove(P); P->DestroyComponent(); }
			B.Pend.Reset();
		}
	// ---- the level asked for, loaded: the furniture and lamp laid
	if (PendingWild17 >= 0)
	{
		ULevelStreamingDynamic* L = WildStream17.Get();
		ULevel* Lv = L ? L->GetLoadedLevel() : nullptr;
		if (!WildBlds17.IsValidIndex(PendingWild17)) { UnloadWild17(); return; }
		if (!Lv || !L->IsLevelVisible())
		{
			if (FPlatformTime::Seconds() - Wild17Asked > 15.0) { UE_LOG(LogRDList17f, Warning, TEXT("RDWILD17 the level never came: given up")); UnloadWild17(); }
			return;
		}
		const int32 Ri = PendingWild17; PendingWild17 = -1;
		const FWildBld17& B = WildBlds17[Ri];
		FActorSpawnParameters Sp; Sp.OverrideLevel = Lv; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		AActor* A = GetWorld()->SpawnActor<AActor>(AActor::StaticClass(), FTransform::Identity, Sp);
		if (!A) { UnloadWild17(); return; }
		USceneComponent* Root = NewObject<USceneComponent>(A, TEXT("Root")); A->SetRootComponent(Root); Root->RegisterComponent();
		Wild17Pieces = 0;
		for (const TPair<FString, FWildPiece17>& Kv : B.Pieces)
		{
			const FWildPiece17& P = Kv.Value;
			if (!P.Mesh) continue;
			UInstancedStaticMeshComponent* H = NewObject<UInstancedStaticMeshComponent>(A);
			H->SetStaticMesh(P.Mesh);
			if (P.Mat) H->SetMaterial(0, P.Mat);
			H->SetMobility(EComponentMobility::Static);
			H->SetupAttachment(Root);
			H->SetCollisionProfileName(P.bCol ? TEXT("BlockAll") : TEXT("NoCollision"));
			H->RegisterComponent();
			for (const FTransform& T : P.T) H->AddInstance(T, true);
			A->AddInstanceComponent(H);
			Wild17Pieces += P.T.Num();
		}
		for (const FVector4& Lp : B.Lamps)
		{
			UPointLightComponent* Lt = NewObject<UPointLightComponent>(A);
			Lt->SetupAttachment(Root);
			Lt->SetIntensityUnits(ELightUnits::Candelas); Lt->SetIntensity(Lp.W);
			Lt->SetAttenuationRadius(B.LampR); Lt->SetLightColor(FLinearColor(1.f, 0.72f, 0.45f)); Lt->SetCastShadows(false);
			Lt->RegisterComponent(); Lt->SetWorldLocation(FVector(Lp.X, Lp.Y, Lp.Z));
			A->AddInstanceComponent(Lt);
		}
		WildActor17 = A; InWild17 = Ri; ++Wild17Entered;
		Wild17LoadMs = (float)((FPlatformTime::Seconds() - Wild17Asked) * 1000.0);
		UE_LOG(LogRDList17f, Log, TEXT("RDWILD17 in %s %d: %d pieces, %d lamps, %.0f ms"), *B.Kind, Ri, Wild17Pieces, B.Lamps.Num(), Wild17LoadMs);
		return;
	}
	// ---- walked in: its level; walked out: let go
	if (InWild17 >= 0)
	{
		if (!WildRoomAt17(InWild17, Her, 150.f)) { UE_LOG(LogRDList17f, Log, TEXT("RDWILD17 out of %d"), InWild17); UnloadWild17(); }
	}
	else if (!BuildingLevel17.IsEmpty())
	{
		for (int32 I = 0; I < WildBlds17.Num(); ++I)
		{
			if (!WildBlds17[I].bClosed || !WildRoomAt17(I, Her, -20.f)) continue;
			bool bOk = false;
			Wild17Asked = FPlatformTime::Seconds();
			ULevelStreamingDynamic* L = ULevelStreamingDynamic::LoadLevelInstance(GetWorld(), BuildingLevel17, FVector::ZeroVector, FRotator::ZeroRotator, bOk, FString::Printf(TEXT("RDWild17_%d_%d"), I, ++Wild17Count));
			if (!bOk || !L) { UE_LOG(LogRDList17f, Warning, TEXT("RDWILD17 the level %s did not load"), *BuildingLevel17); break; }
			WildStream17 = L; PendingWild17 = I;
			break;
		}
	}
	// ---- the panes glow in the evening
	Wild17PaneT -= Dt;
	if (Wild17PaneT > 0.f) return;
	Wild17PaneT = 1.f;
	const float Hr = GetTownHour();
	const float G = bDayNight && Hr >= 19.f && Hr < 23.5f ? 1.f : 0.f;
	for (FWildBld17& B : WildBlds17)
	{
		UInstancedStaticMeshComponent* H = B.PaneC.Get();
		if (!H || B.Glow == G) continue;
		B.Glow = G;
		for (int32 I = 0; I < H->GetInstanceCount(); ++I) H->SetCustomDataValue(I, 0, G, false);
		H->MarkRenderStateDirty();
	}
}

// ================================================================================================ the tests
TArray<FString> ARDDungeonGenerator::GetWildBlds17() const
{
	// ("<index>|<kind>|<closed>|<pieces>|<lamps>|<panes>|<o x>|<o y>|<floor>|<yaw>|<mid x>|<mid y>|<glow>|<half x>|<half y>")
	TArray<FString> Out;
	for (int32 I = 0; I < WildBlds17.Num(); ++I)
	{
		const FWildBld17& B = WildBlds17[I];
		if (!B.C.IsValid()) continue;
		const FVector M = RDL17fAt(B.O, B.Yaw, (B.Mn.X + B.Mx.X) * 0.5f, (B.Mn.Y + B.Mx.Y) * 0.5f, 0.f);
		Out.Add(FString::Printf(TEXT("%d|%s|%d|%d|%d|%d|%.0f|%.0f|%.0f|%.1f|%.0f|%.0f|%.0f|%.0f|%.0f"), I, *B.Kind, B.bClosed ? 1 : 0, B.N, B.Lamps.Num(), B.Panes, B.O.X, B.O.Y, B.Floor, B.Yaw, M.X, M.Y, B.Glow, (B.Mx.X - B.Mn.X) * 0.5f, (B.Mx.Y - B.Mn.Y) * 0.5f));
	}
	return Out;
}

FString ARDDungeonGenerator::GetWild17State() const
{
	// ("<in>|<pending>|<level loaded>|<pieces laid>|<entered>|<load ms>")
	const ULevelStreamingDynamic* L = WildStream17.Get();
	return FString::Printf(TEXT("%d|%d|%d|%d|%d|%.0f"), InWild17, PendingWild17, L && L->GetLoadedLevel() ? 1 : 0, Wild17Pieces, Wild17Entered, Wild17LoadMs);
}
