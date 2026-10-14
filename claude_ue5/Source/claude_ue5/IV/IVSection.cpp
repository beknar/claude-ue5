#include "IV/IVSection.h"
#include "IV/IVVillageGenerator.h"
#include "IV/IVVillager.h"
#include "ProceduralMeshComponent.h"
#include "KismetProceduralMeshLibrary.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "TimerManager.h"
#include "HAL/PlatformTime.h"

DEFINE_LOG_CATEGORY_STATIC(LogIsoVillage, Log, All);

static const FName IVInteractiveTag(TEXT("IVInteractive"));
static const FName IVFlickerTag(TEXT("IVFlicker"));
static const float GroundStep = 125.f;

AIVSection::AIVSection()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.f;
	Ground = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("Ground"));
	RootComponent = Ground;
	Ground->SetMobility(EComponentMobility::Static);
	Ground->SetCollisionEnabled(ECollisionEnabled::NoCollision);      // (she walks on the level's ground plane)
	Ground->SetCastShadow(false);
}

FVector2D AIVSection::GetSectionMin() const { const FVector L = GetActorLocation(); return FVector2D(L.X, L.Y); }

// ------------------------------------------------------------------------------------------------ instancing helpers
void AIVSection::AddPiece(FName Name, const FTransform& T, bool bForceNoCollision)
{
	if (!bBuildStatic) return;
	const FIVPiece* P = Generator->Piece(Name);
	if (!P) return;
	const FTransform W = P->Adjust * T;
	if (P->ActorClass)
	{
		FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		AActor* A = GetWorld()->SpawnActor<AActor>(P->ActorClass, W, Sp);
		if (A)
		{
			A->AttachToActor(this, FAttachmentTransformRules::KeepWorldTransform);
#if WITH_EDITOR
			if (bEditorBuilt) A->SetFolderPath(TEXT("IsoVillage/Props"));
#endif
			OtherActors.Add(A);
		}
		return;
	}
	if (!P->Mesh) return;
	const bool bCol = (P->bCollision && !bForceNoCollision) || P->bHidden;
	(P->bHidden ? PendingHidden : bCol ? Pending : PendingNoCol).FindOrAdd(P->Mesh).Add(W);
	TMap<UStaticMesh*, UInstancedStaticMeshComponent*>& Map = P->bHidden ? IsmsHidden : bCol ? Isms : IsmsNoCol;
	if (!Map.Contains(P->Mesh))
	{
		UInstancedStaticMeshComponent* H = NewObject<UInstancedStaticMeshComponent>(this, NAME_None, RF_Transactional);
		H->SetStaticMesh(P->Mesh);
		H->SetMobility(EComponentMobility::Static);
		H->SetupAttachment(RootComponent);
		H->SetCollisionProfileName(bCol ? TEXT("BlockAll") : TEXT("NoCollision"));
		if (P->bHidden) { H->SetVisibility(false); H->SetHiddenInGame(true); H->SetCastShadow(false); }
		if (!bCol) H->SetCanEverAffectNavigation(false);
		H->RegisterComponent();
		AddInstanceComponent(H);
		Map.Add(P->Mesh, H);
	}
	++NumInstances;
}

void AIVSection::AddPieceAt(FName Name, const FVector& Loc, float Yaw, float Scale, bool bForceNoCollision)
{
	AddPiece(Name, FTransform(FRotator(0, Yaw, 0), Loc, FVector(Scale)), bForceNoCollision);
}

void AIVSection::AddToGroup(FBld& B, int32 BI, int32 G, FName Name, const FTransform& T)
{
	if (!bBuildStatic) return;
	const FIVPiece* P = Generator->Piece(Name);
	if (!P || !P->Mesh) return;
	UInstancedStaticMeshComponent* H = nullptr;
	for (UInstancedStaticMeshComponent* C : B.Group[G]) if (C->GetStaticMesh() == P->Mesh) { H = C; break; }
	if (!H)
	{
		H = NewObject<UInstancedStaticMeshComponent>(this, NAME_None, RF_Transactional);
		H->SetStaticMesh(P->Mesh);
		H->SetMobility(EComponentMobility::Static);
		H->SetupAttachment(RootComponent);
		// the roof never blocks anything; walls keep their collision while hidden
		H->SetCollisionProfileName((G == GRoof || !P->bCollision) ? TEXT("NoCollision") : TEXT("BlockAll"));
		// cut away = hidden but still casting shadows: the light inside does not change when the roof comes off
		H->bCastHiddenShadow = true;
		H->bAffectIndirectLightingWhileHidden = true;
		H->ComponentTags.Add(FName(*FString::Printf(TEXT("IVG_%d_%d"), BI, G)));
		H->RegisterComponent();
		AddInstanceComponent(H);
		B.Group[G].Add(H);
	}
	H->AddInstance(P->Adjust * T, true);
	++NumInstances;
}

void AIVSection::FlushInstances()
{
	for (auto& KV : Pending) if (UInstancedStaticMeshComponent** H = Isms.Find(KV.Key)) (*H)->AddInstances(KV.Value, false, true);
	for (auto& KV : PendingNoCol) if (UInstancedStaticMeshComponent** H = IsmsNoCol.Find(KV.Key)) (*H)->AddInstances(KV.Value, false, true);
	for (auto& KV : PendingHidden) if (UInstancedStaticMeshComponent** H = IsmsHidden.Find(KV.Key)) (*H)->AddInstances(KV.Value, false, true);
	Pending.Reset(); PendingNoCol.Reset(); PendingHidden.Reset();
}

UPointLightComponent* AIVSection::AddLight(const FVector& Loc, const FLinearColor& Color, float Candelas, float Radius, float Flicker, FName Tag)
{
	if (!bBuildStatic) return nullptr;
	UPointLightComponent* L = NewObject<UPointLightComponent>(this, NAME_None, RF_Transactional);
	L->SetMobility(EComponentMobility::Movable);
	L->SetupAttachment(RootComponent);
	L->SetWorldLocation(Loc);
	L->SetIntensityUnits(ELightUnits::Candelas);
	L->SetIntensity(Candelas);
	L->SetLightColor(Color);
	L->SetAttenuationRadius(Radius);
	L->SetSourceRadius(8.f);
	L->SetCastShadows(false);
	// (no draw distance: the orthographic camera stands 120 m away from everything it shows)
	if (Flicker > 0.f) { L->ComponentTags.Add(IVFlickerTag); L->ComponentTags.Add(FName(*FString::Printf(TEXT("F%.2f"), Flicker))); }
	if (!Tag.IsNone()) L->ComponentTags.Add(Tag);
	L->RegisterComponent();
	AddInstanceComponent(L);
	++NumLights;
	return L;
}

void AIVSection::AddEffect(FName Name, const FVector& Loc, float Scale)
{
	if (!bBuildStatic) return;
	const TObjectPtr<UNiagaraSystem>* S = Generator->Effects.Find(Name);
	if (!S || !*S) return;
	UNiagaraComponent* C = NewObject<UNiagaraComponent>(this, NAME_None, RF_Transactional);
	C->SetAsset(*S);
	C->SetupAttachment(RootComponent);
	C->SetWorldLocation(Loc);
	C->SetWorldScale3D(FVector(Scale));
	C->SetAutoActivate(true);
	C->RegisterComponent();
	AddInstanceComponent(C);
}

USceneComponent* AIVSection::AddPivot(USceneComponent* Parent, const FTransform& Rel)
{
	USceneComponent* C = NewObject<USceneComponent>(this, NAME_None, RF_Transactional);
	C->ComponentTags.Add(IVInteractiveTag);
	C->SetMobility(EComponentMobility::Movable);
	C->SetupAttachment(Parent);
	C->SetRelativeTransform(Rel);
	C->RegisterComponent();
	AddInstanceComponent(C);
	return C;
}

UStaticMeshComponent* AIVSection::AddMesh(USceneComponent* Parent, UStaticMesh* Mesh, const FTransform& Rel, bool bCollision)
{
	UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this, NAME_None, RF_Transactional);
	C->ComponentTags.Add(IVInteractiveTag);
	C->SetMobility(EComponentMobility::Movable);
	C->SetStaticMesh(Mesh);
	C->SetupAttachment(Parent);
	C->SetRelativeTransform(Rel);
	C->SetCollisionProfileName(bCollision ? TEXT("BlockAllDynamic") : TEXT("NoCollision"));
	C->RegisterComponent();
	AddInstanceComponent(C);
	return C;
}

/** sign of an angle about Axis that swings Tip toward Want */
static float IVPickSign(const FVector& Axis, const FVector& Tip, const FVector& Want)
{
	const FVector P = FQuat(Axis, FMath::DegreesToRadians(60.f)).RotateVector(Tip);
	return FVector::DotProduct(P - Tip, Want) >= 0.f ? 1.f : -1.f;
}

int32 AIVSection::AddContainer(FName Name, const FVector& Loc, float Yaw, const FString& Kind)
{
	const FIVPiece* P = Generator->Piece(Name);
	if (!P || !bBuildInteractive || !P->Moving) return -1;
	const FVector Local = Loc - GetActorLocation();
	USceneComponent* Base = AddPivot(RootComponent, FTransform(FRotator(0, Yaw, 0), Local));
	UStaticMeshComponent* Body = AddMesh(Base, P->Mesh, P->Adjust, true);
	const FVector Front = FRotator(0, Yaw, 0).RotateVector(FVector(1, 0, 0));
	auto AddMoving = [&](UStaticMesh* Mesh, const FVector& Hinge, bool bVerticalAxis, int32 Partner)
	{
		USceneComponent* Hp = AddPivot(Base, FTransform(Hinge));
		// A moving part's mesh has its origin AT its hinge (a lid runs forward from it, a wardrobe door sideways), in the
		// body mesh's axes: on the hinge pivot it takes the piece's rotation and scale and no offset. (It used to get the
		// body's offset minus the hinge, as if it shared the body's origin: every lid lay on the floor inside its body and
		// every wardrobe door stood in the middle of the wardrobe.)
		FTransform Rel = P->Adjust; Rel.SetTranslation(FVector::ZeroVector);
		UStaticMeshComponent* M = AddMesh(Hp, Mesh, Rel, true);
		FMover Mv; Mv.Pivot = Hp; Mv.Parts = { M }; Mv.Kind = Kind; Mv.Partner = Partner; Mv.Building = CurBld; Mv.Body = Body;
		const FBox Bx = Mesh->GetBoundingBox().TransformBy(Rel);
		if (bVerticalAxis)
		{
			Mv.Axis = FVector::UpVector;          // wardrobe door: swings out toward the front (+X)
			Mv.OpenAngle = 100.f * IVPickSign(Mv.Axis, FVector(0, Bx.GetCenter().Y, 0), FVector(1, 0, 0));
		}
		else
		{
			Mv.Axis = FVector::RightVector;       // lid: hinge along Y at the back, lifts up
			Mv.OpenAngle = 100.f * IVPickSign(Mv.Axis, FVector(Bx.GetCenter().X, 0, 0), FVector::UpVector);
		}
		Mv.Center = Loc + FVector(0, 0, P->Size.Z * 0.6f);
		Mv.Stand = Loc + Front * (P->Size.X * 0.5f + 62.f);
		return Containers.Add(Mv);
	};
	const bool bWardrobe = Kind == TEXT("wardrobe");
	const int32 I0 = AddMoving(P->Moving, P->Hinge, bWardrobe, -1);
	if (P->Moving2)
	{
		const int32 I1 = AddMoving(P->Moving2, P->Hinge2, bWardrobe, I0);
		Containers[I0].Partner = I1;
	}
	return I0;
}

// ------------------------------------------------------------------------------------------------ nav grid
FIntPoint AIVSection::GlobalCell(const FVector2D& W)
{
	return FIntPoint(FMath::FloorToInt(W.X / NavCell), FMath::FloorToInt(W.Y / NavCell));
}

FIntPoint AIVSection::NavIndex(const FVector2D& W) const
{
	const FVector2D Mn = GetSectionMin() - FVector2D(NavMargin);
	return FIntPoint(FMath::FloorToInt((W.X - Mn.X) / NavCell), FMath::FloorToInt((W.Y - Mn.Y) / NavCell));
}

int32 AIVSection::NavAt(const FVector2D& W) const
{
	const FIntPoint I = NavIndex(W);
	if (I.X < 0 || I.Y < 0 || I.X >= NavN || I.Y >= NavN || Nav.Num() != NavN * NavN) return -1;
	return Nav[I.Y * NavN + I.X];
}

void AIVSection::NavBox(const FVector2D& C, const FVector2D& Fx, const FVector2D& Fy, const FVector2D& Half, uint8 Value, float Grow)
{
	if (Nav.Num() != NavN * NavN) return;
	const FVector2D H = Half + FVector2D(Grow);
	const float Ex = FMath::Abs(Fx.X) * H.X + FMath::Abs(Fy.X) * H.Y, Ey = FMath::Abs(Fx.Y) * H.X + FMath::Abs(Fy.Y) * H.Y;
	const FIntPoint A = NavIndex(C - FVector2D(Ex, Ey)), B = NavIndex(C + FVector2D(Ex, Ey));
	const FVector2D Mn = GetSectionMin() - FVector2D(NavMargin);
	for (int32 Y = FMath::Max(A.Y, 0); Y <= FMath::Min(B.Y, NavN - 1); ++Y)
		for (int32 X = FMath::Max(A.X, 0); X <= FMath::Min(B.X, NavN - 1); ++X)
		{
			const FVector2D P = Mn + FVector2D((X + 0.5f) * NavCell, (Y + 0.5f) * NavCell) - C;
			if (FMath::Abs(FVector2D::DotProduct(P, Fx)) > H.X || FMath::Abs(FVector2D::DotProduct(P, Fy)) > H.Y) continue;
			uint8& V = Nav[Y * NavN + X];
			// outdoor things never claim a house floor; furniture (blocking a floor cell) does
			if (Value == 1 || V != 1 || Value == 2) V = Value;
		}
}

void AIVSection::NavDisc(const FVector2D& C, float Radius, uint8 Value)
{
	if (Nav.Num() != NavN * NavN) return;
	const FIntPoint A = NavIndex(C - FVector2D(Radius)), B = NavIndex(C + FVector2D(Radius));
	const FVector2D Mn = GetSectionMin() - FVector2D(NavMargin);
	for (int32 Y = FMath::Max(A.Y, 0); Y <= FMath::Min(B.Y, NavN - 1); ++Y)
		for (int32 X = FMath::Max(A.X, 0); X <= FMath::Min(B.X, NavN - 1); ++X)
		{
			const FVector2D P = Mn + FVector2D((X + 0.5f) * NavCell, (Y + 0.5f) * NavCell);
			if (FVector2D::DistSquared(P, C) > Radius * Radius) continue;
			uint8& V = Nav[Y * NavN + X];
			if (V != 2) V = Value;
		}
}

void AIVSection::NavBuilding(const FBld& B)
{
	// the wall band blocks (wall thickness + the capsule radius on both sides), the floor inside is free
	const float M = Generator->Module;
	const FVector2D Half(B.Nx * M * 0.5f, B.Ny * M * 0.5f);
	NavBox(B.C, B.Fx, B.Fy, Half + FVector2D(52.f), 1);
	NavBox(B.C, B.Fx, B.Fy, Half - FVector2D(62.f), 2);
}

void AIVSection::AppendPortals(TMultiMap<FIntPoint, FIntPoint>& Out) const
{
	for (const TPair<FIntPoint, FIntPoint>& P : Portals) { Out.Add(P.Key, P.Value); Out.Add(P.Value, P.Key); }
}

int32 AIVSection::CountUnreachableDoors(FVector From) const
{
	// flood over this section's own grid from From; a building counts as reached when the cell inside its door is
	if (Nav.Num() != NavN * NavN || Blds.Num() == 0) return 0;
	const FVector2D Mn = GetSectionMin() - FVector2D(NavMargin);
	auto ToIdx = [&](const FIntPoint& G) { return FIntPoint(G.X - FMath::FloorToInt(Mn.X / NavCell), G.Y - FMath::FloorToInt(Mn.Y / NavCell)); };
	TMultiMap<FIntPoint, FIntPoint> Pm;
	for (const TPair<FIntPoint, FIntPoint>& P : Portals) { Pm.Add(ToIdx(P.Key), ToIdx(P.Value)); Pm.Add(ToIdx(P.Value), ToIdx(P.Key)); }
	TArray<uint8> Seen; Seen.Init(0, NavN * NavN);
	FIntPoint S = NavIndex(FVector2D(From.X, From.Y));
	auto Free = [&](const FIntPoint& I) { return I.X >= 0 && I.Y >= 0 && I.X < NavN && I.Y < NavN && Nav[I.Y * NavN + I.X] != 1; };
	if (!Free(S))
	{
		bool bOk = false;
		for (int32 D = 1; D <= 6 && !bOk; ++D)
			for (int32 Dx = -D; Dx <= D && !bOk; ++Dx)
				for (int32 Dy = -D; Dy <= D && !bOk; ++Dy)
					if (Free(S + FIntPoint(Dx, Dy))) { S += FIntPoint(Dx, Dy); bOk = true; }
		if (!bOk) return Blds.Num();
	}
	TArray<FIntPoint> Q; Q.Reserve(NavN * NavN / 2);
	Q.Add(S); Seen[S.Y * NavN + S.X] = 1;
	static const FIntPoint D4[4] = { FIntPoint(1, 0), FIntPoint(-1, 0), FIntPoint(0, 1), FIntPoint(0, -1) };
	for (int32 H = 0; H < Q.Num(); ++H)
	{
		const FIntPoint C = Q[H];
		for (int32 K = 0; K < 4; ++K)
		{
			const FIntPoint N = C + D4[K];
			if (!Free(N) || Seen[N.Y * NavN + N.X]) continue;
			Seen[N.Y * NavN + N.X] = 1; Q.Add(N);
		}
		TArray<FIntPoint> Ps; Pm.MultiFind(C, Ps);
		for (const FIntPoint& N : Ps) if (Free(N) && !Seen[N.Y * NavN + N.X]) { Seen[N.Y * NavN + N.X] = 1; Q.Add(N); }
	}
	int32 Bad = 0;
	for (int32 I = 0; I < Blds.Num(); ++I)
	{
		FVector Out, In; GetBuildingEntry(I, Out, In);
		const FIntPoint C = NavIndex(FVector2D(In.X, In.Y));
		if (!(C.X >= 0 && C.Y >= 0 && C.X < NavN && C.Y < NavN && Seen[C.Y * NavN + C.X]))
		{
			++Bad;
			UE_LOG(LogIsoVillage, Warning, TEXT("IVSECTION (%d,%d): door of building %d (%s) not reachable"), Coord.X, Coord.Y, I, *GetBuildingKind(I));
		}
	}
	// containers: the spot in front of each must be reachable too
	for (int32 I = 0; I < Containers.Num(); ++I)
	{
		if (Containers[I].Partner >= 0 && Containers[I].Partner < I) continue;
		const FIntPoint C = NavIndex(FVector2D(Containers[I].Stand.X, Containers[I].Stand.Y));
		bool bOk = false;
		for (int32 Dx = -1; Dx <= 1 && !bOk; ++Dx)
			for (int32 Dy = -1; Dy <= 1 && !bOk; ++Dy)
			{
				const FIntPoint N = C + FIntPoint(Dx, Dy);
				bOk = N.X >= 0 && N.Y >= 0 && N.X < NavN && N.Y < NavN && Seen[N.Y * NavN + N.X];
			}
		if (!bOk)
		{
			++Bad;
			UE_LOG(LogIsoVillage, Warning, TEXT("IVSECTION (%d,%d): container %d (%s, building %d) not reachable"), Coord.X, Coord.Y, I, *Containers[I].Kind, Containers[I].Building);
		}
	}
	return Bad;
}

// ------------------------------------------------------------------------------------------------ ground
bool AIVSection::GroundRows(double Budget, double T0)
{
	// vertex colours: R = trodden earth (roads, yards), G = cobbles (the square), B = tilled soil, A = lush grass
	const float SS = Generator->SectionSize;
	const int32 N = FMath::RoundToInt(SS / GroundStep) + 1;
	const FVector2D Mn = GetSectionMin();
	if (GroundRow == 0) { GV.Reset(N * N); GN.Reset(N * N); GUV.Reset(N * N); GC.Reset(N * N); }
	while (GroundRow < N)
	{
		const int32 I = GroundRow++;
		for (int32 J = 0; J < N; ++J)
		{
			const float X = Mn.X + I * GroundStep, Y = Mn.Y + J * GroundStep;
			GV.Add(FVector(I * GroundStep, J * GroundStep, 0.f));
			GN.Add(FVector::UpVector);
			GUV.Add(FVector2D(X / 400.f, Y / 400.f));
			int32 Type = 0;
			const float D = Generator->RoadDistance(FVector2D(X, Y), Type);
			float Dirt = 0.f, Cobble = 0.f;
			if (Type == 3) { Cobble = 1.f - FMath::SmoothStep(-70.f, 70.f, D); Dirt = (1.f - FMath::SmoothStep(40.f, 260.f, D)) * 0.8f; }
			else Dirt = 1.f - FMath::SmoothStep(-50.f, 110.f, D);
			GC.Add(FLinearColor(Dirt, Cobble, 0.f, 0.f));
		}
		if (FPlatformTime::Seconds() - T0 > Budget) break;
	}
	return GroundRow >= N;
}

void AIVSection::FinishGround()
{
	const float SS = Generator->SectionSize;
	const int32 N = FMath::RoundToInt(SS / GroundStep) + 1;
	const FVector2D Mn = GetSectionMin();
	if (GV.Num() != N * N) return;
	auto Paint = [&](const FVector2D& Lo, const FVector2D& Hi, TFunctionRef<void(const FVector2D&, FLinearColor&)> Fn)
	{
		const int32 I0 = FMath::Max(0, FMath::FloorToInt((Lo.X - Mn.X) / GroundStep)), I1 = FMath::Min(N - 1, FMath::CeilToInt((Hi.X - Mn.X) / GroundStep));
		const int32 J0 = FMath::Max(0, FMath::FloorToInt((Lo.Y - Mn.Y) / GroundStep)), J1 = FMath::Min(N - 1, FMath::CeilToInt((Hi.Y - Mn.Y) / GroundStep));
		for (int32 I = I0; I <= I1; ++I)
			for (int32 J = J0; J <= J1; ++J) Fn(Mn + FVector2D(I * GroundStep, J * GroundStep), GC[I * N + J]);
	};
	// patches: signed distance to the convex polygon gives a soft edge
	for (const FPatch& P : Patches)
	{
		if (P.Pts.Num() < 3 || P.Type == 0) continue;
		FBox2D Bx(ForceInit); for (const FVector2D& Q : P.Pts) Bx += Q;
		FVector2D Cn(0, 0); for (const FVector2D& Q : P.Pts) Cn += Q; Cn /= P.Pts.Num();
		Paint(Bx.Min - FVector2D(150.f), Bx.Max + FVector2D(150.f), [&](const FVector2D& W, FLinearColor& C)
		{
			float In = 1e9f;
			for (int32 K = 0; K < P.Pts.Num(); ++K)
			{
				const FVector2D A = P.Pts[K], B = P.Pts[(K + 1) % P.Pts.Num()];
				FVector2D Nm = FVector2D(-(B - A).Y, (B - A).X).GetSafeNormal();
				if (FVector2D::DotProduct(Cn - A, Nm) < 0.f) Nm = -Nm;
				In = FMath::Min(In, (float)FVector2D::DotProduct(W - A, Nm));
			}
			const float K = FMath::SmoothStep(-60.f, 90.f, In);
			if (P.Type == 1 || P.Type == 2) C.B = FMath::Max(C.B, K);
			else if (P.Type == 3 || P.Type == 5) C.A = FMath::Max(C.A, K);
			if (P.Type == 5) C.R = FMath::Max(C.R, K * 0.25f);
		});
	}
	// trodden earth around every house and in front of its doors
	const float M = Generator->Module;
	for (int32 BI = 0; BI < Blds.Num(); ++BI)
	{
		const FBld& B = Blds[BI];
		const FVector2D Half(B.Nx * M * 0.5f, B.Ny * M * 0.5f);
		const float Reach = Half.Size() + 400.f;
		FVector Out, In; GetBuildingEntry(BI, Out, In);
		Paint(B.C - FVector2D(Reach), B.C + FVector2D(Reach), [&](const FVector2D& W, FLinearColor& C)
		{
			const FVector2D L = BldLocal(B, W);
			const float Dx = FMath::Max(FMath::Abs(L.X) - Half.X, 0.f), Dy = FMath::Max(FMath::Abs(L.Y) - Half.Y, 0.f);
			const float D = FMath::Sqrt(Dx * Dx + Dy * Dy);
			C.R = FMath::Max(C.R, 0.75f * (1.f - FMath::SmoothStep(40.f, 190.f, D)));
			const float Dd = FVector2D::Distance(W, FVector2D(Out.X, Out.Y));
			C.R = FMath::Max(C.R, 0.9f * (1.f - FMath::SmoothStep(120.f, 380.f, Dd)));
			if (D <= 0.f) { C.B = 0.f; C.A = 0.f; }
		});
	}
	TArray<int32> Tri; TArray<FProcMeshTangent> Tan;
	UKismetProceduralMeshLibrary::CreateGridMeshTriangles(N, N, false, Tri);      // (true faces down: culled from above)
	Ground->ClearAllMeshSections();
	Ground->CreateMeshSection_LinearColor(0, GV, Tri, GN, GUV, GC, Tan, false);
	if (Generator->GroundMaterial) Ground->SetMaterial(0, Generator->GroundMaterial);
	GV.Empty(); GN.Empty(); GUV.Empty(); GC.Empty();
}

// ------------------------------------------------------------------------------------------------ build / play
void AIVSection::ClearInteractive()
{
	TArray<UActorComponent*> Comps;
	GetComponents(Comps);
	for (UActorComponent* C : Comps) if (C && C->ComponentHasTag(IVInteractiveTag)) C->DestroyComponent();
	Doors.Reset(); Containers.Reset(); Portals.Reset();
}

void AIVSection::BeginGenerate(AIVVillageGenerator* InGenerator, FIntPoint InCoord, int32 InSeed, bool bEditorBuild)
{
	GenStart = FPlatformTime::Seconds();
	Generator = InGenerator; Coord = InCoord; Seed = InSeed; bEditorBuilt = bEditorBuild;
	bBuildStatic = true; bBuildInteractive = true;
	NumInstances = 0; NumLights = 0; GenTicks = 0; WorkMs = 0.0;
	Step = 0; SubStep = 0; GroundRow = 0; CurBld = -1;
	NavN = FMath::RoundToInt((Generator->SectionSize + 2.f * NavMargin) / NavCell);
	Nav.Init(0, NavN * NavN);
	Plan();
	for (const FBld& B : Blds) NavBuilding(B);
	WorkMs = (FPlatformTime::Seconds() - GenStart) * 1000.0;
	bBuilding = true;
}

bool AIVSection::ContinueGenerate(double Budget)
{
	if (!bBuilding) return true;
	const double T0 = FPlatformTime::Seconds();
	++GenTicks;
	auto Over = [&]() { return FPlatformTime::Seconds() - T0 > Budget; };
	while (bBuilding && !Over())
	{
		switch (Step)
		{
		case 0:      // houses: shell, door leaves, furniture
			if (SubStep < Blds.Num()) { const int32 I = SubStep++; BuildShell(I); AddDoorsFor(I); CurBld = I; Furnish(I); CurBld = -1; }
			else { Step = 1; SubStep = 0; }
			break;
		case 1:      // yards and gardens
			if (SubStep < Blds.Num()) { const int32 I = SubStep++; FRandomStream R(Blds[I].Seed ^ 0x51ed270b); BuildYard(I, R); if (Blds[I].Kind == EIVBuildingKind::Church) BuildChurchyard(Blds[I], R); }
			else { Step = 2; SubStep = 0; }
			break;
		case 2:      // unbuilt sites
			if (SubStep < Vacant.Num()) { const int32 I = SubStep++; FRandomStream R(Vacant[I].Id ^ (uint32)Seed); BuildVacant(I, R); }
			else { Step = 3; SubStep = 0; }
			break;
		case 3: { FRandomStream R(Seed ^ 0x2545f491); BuildHub(R); Step = 4; break; }
		case 4: { FRandomStream R(Seed ^ 0x7f4a7c15); ScatterNature(R); Step = 5; break; }
		case 5:      // the ground last: it paints the gardens and the earth around the houses
			if (!bBuildStatic || GroundRows(Budget, T0)) Step = 6;
			break;
		case 6: if (bBuildStatic) FinishGround(); Step = 7; SubStep = 0; break;
		case 7:      // the villagers (play only: they are never part of the saved level)
			if (bBuildInteractive && GetWorld() && GetWorld()->IsGameWorld() && SubStep < GetWantedVillagers()) SpawnVillager(SubStep++);
			else Step = 8;
			break;
		default: Finish(); break;
		}
	}
	WorkMs += (FPlatformTime::Seconds() - T0) * 1000.0;
	if (!bBuilding && bBuildStatic)
	{
		GenerateMs = WorkMs;
		UE_LOG(LogIsoVillage, Log, TEXT("IVSECTION (%d,%d) seed %d: %d buildings, %d vacant sites, %d doors, %d containers, %d instances, %d lights, %d trees, %d villagers, %.0f ms over %d frames (%.1f s)%s"),
			Coord.X, Coord.Y, Seed, Blds.Num(), Vacant.Num(), Doors.Num(), Containers.Num(), NumInstances, NumLights, MapTrees.Num(), Villagers.Num(), WorkMs, GenTicks,
			FPlatformTime::Seconds() - GenStart, bEditorBuilt ? TEXT(" [editor]") : TEXT(""));
	}
	return !bBuilding;
}

void AIVSection::Finish()
{
	FlushInstances();
	bBuilding = false;
	UWorld* W = GetWorld();
	if (W && W->IsGameWorld()) { RegisterMap(); CollectFlicker(); }
}

void AIVSection::Generate(AIVVillageGenerator* InGenerator, FIntPoint InCoord, int32 InSeed, bool bEditorBuild)
{
	BeginGenerate(InGenerator, InCoord, InSeed, bEditorBuild);
	while (!ContinueGenerate(1e9)) {}
}

void AIVSection::RelinkGroups()
{
	// saved start section: find each building's roof / wall components and lights again (tags IVG_<building>_<group>, IVF_<building>)
	TArray<UInstancedStaticMeshComponent*> Is; GetComponents(Is);
	for (UInstancedStaticMeshComponent* C : Is)
		for (const FName& Tg : C->ComponentTags)
		{
			const FString S = Tg.ToString();
			if (!S.StartsWith(TEXT("IVG_"))) continue;
			TArray<FString> Parts; S.ParseIntoArray(Parts, TEXT("_"));
			if (Parts.Num() != 3) continue;
			const int32 BI = FCString::Atoi(*Parts[1]), G = FCString::Atoi(*Parts[2]);
			if (Blds.IsValidIndex(BI) && G >= 0 && G < GNum) Blds[BI].Group[G].AddUnique(C);
		}
	TArray<UPointLightComponent*> Ls; GetComponents(Ls);
	for (UPointLightComponent* L : Ls)
		for (const FName& Tg : L->ComponentTags)
		{
			const FString S = Tg.ToString();
			if (!S.StartsWith(TEXT("IVF_"))) continue;
			const int32 BI = FCString::Atoi(*S.Mid(4));
			if (Blds.IsValidIndex(BI)) Blds[BI].FillLights.AddUnique(L);
		}
}

void AIVSection::ActivateForPlay()
{
	if (!Generator) return;
	// same plan as the editor build (same seed); only the interactive part is instantiated
	const int32 Inst = NumInstances, Lights = NumLights;
	const double T0 = FPlatformTime::Seconds();
	bBuildStatic = false; bBuildInteractive = true;
	ClearInteractive();
	NavN = FMath::RoundToInt((Generator->SectionSize + 2.f * NavMargin) / NavCell);
	Nav.Init(0, NavN * NavN);
	Plan();
	for (const FBld& B : Blds) NavBuilding(B);
	RelinkGroups();
	Step = 0; SubStep = 0; GroundRow = 0; bBuilding = true;
	while (!ContinueGenerate(1e9)) {}
	// the ground is rebuilt (procedural mesh sections are not kept in the level)
	bBuildStatic = true;
	GroundRow = 0;
	GroundRows(1e9, FPlatformTime::Seconds());
	FinishGround();
	NumInstances = Inst; NumLights = Lights;
	for (FBld& B : Blds) for (UPointLightComponent* L : B.FillLights) if (L) L->SetVisibility(false);
	UE_LOG(LogIsoVillage, Log, TEXT("IVSECTION (%d,%d) activated for play: %d buildings, %d doors, %d containers, %d villagers, %.0f ms"), Coord.X, Coord.Y, Blds.Num(), Doors.Num(), Containers.Num(), Villagers.Num(),
		(FPlatformTime::Seconds() - T0) * 1000.0);
}

FIVSectionMap AIVSection::BuildMapData() const
{
	FIVSectionMap M; M.Coord = Coord; M.bStart = Generator && Generator->IsStartSection(Coord);
	if (!Generator) return M;
	const float Md = Generator->Module, WH = Generator->WallHeight;
	for (const FBld& B : Blds)
	{
		FIVMapBuilding Mb;
		Mb.Center = B.C; Mb.Half = FVector2D(B.Nx * Md * 0.5f, B.Ny * Md * 0.5f); Mb.Yaw = B.Yaw;
		Mb.WallHeight = B.FloorZ + B.Storeys * WH; Mb.RoofHeight = B.Span * Md * 0.5f; Mb.bRidgeAlongY = B.bRidgeY;
		Mb.TowerHeight = B.TowerStoreys > 0 ? B.FloorZ + B.TowerStoreys * WH : 0.f;
		Mb.Style = B.Style; Mb.Kind = B.Kind; Mb.bVisited = B.bVisited;
		const FVector D = BldPoint(B, B.Nx * Md * 0.5f, (B.DoorCell + 0.5f - B.Ny * 0.5f) * Md);
		Mb.Door = FVector2D(D.X, D.Y);
		M.Buildings.Add(Mb);
	}
	for (const FPatch& P : Patches) { FIVMapPatch Mp; Mp.Points = P.Pts; Mp.Type = P.Type; M.Patches.Add(Mp); }
	M.Trees = MapTrees; M.Props = MapProps;
	// roads of the plan crossing this section
	const float SS = Generator->SectionSize;
	const FVector2D Mn = GetSectionMin();
	const FBox2D Bx(Mn - FVector2D(300.f), Mn + FVector2D(SS + 300.f));
	float Rmin = 0.f, Rmax = 0.f;
	{
		const FVector2D Cl(FMath::Clamp(0.f, (float)Mn.X, (float)Mn.X + SS), FMath::Clamp(0.f, (float)Mn.Y, (float)Mn.Y + SS));
		Rmin = Cl.Size();
		for (const FVector2D& Cn : { Mn, Mn + FVector2D(SS, 0), Mn + FVector2D(0, SS), Mn + FVector2D(SS) }) Rmax = FMath::Max(Rmax, (float)Cn.Size());
	}
	for (int32 K = 0; ; ++K)
	{
		const float Base = Generator->RingBase(K);
		if (Base - 800.f > Rmax + 300.f) break;
		if (Generator->RingBase(K + 1) + 800.f < Rmin - 300.f) continue;      // ring K and its band lie inside the section's reach
		// ring K: walk the whole circle in 4 m steps and keep the runs inside the section
		const int32 Steps = FMath::Max(48, FMath::CeilToInt(2.f * PI * Base / 400.f));
		FIVMapRoad Run; Run.HalfWidth = Generator->RingHalf(K); Run.Type = K == 0 ? 3 : 2;
		for (int32 I = 0; I <= Steps && Base + 800.f >= Rmin - 300.f; ++I)
		{
			const float Th = 2.f * PI * I / Steps;
			const FVector2D P = FVector2D(FMath::Cos(Th), FMath::Sin(Th)) * Generator->RingRadius(K, Th);
			if (Bx.IsInside(P)) Run.Points.Add(P);
			else { if (Run.Points.Num() > 1) M.Roads.Add(Run); Run.Points.Reset(); }
		}
		if (Run.Points.Num() > 1) M.Roads.Add(Run);
		if (K == 0 && M.bStart)
		{
			// the cobbled square itself
			FIVMapPatch Sq; Sq.Type = 0;
			for (int32 I = 0; I < 40; ++I) { const float Th = 2.f * PI * I / 40; Sq.Points.Add(FVector2D(FMath::Cos(Th), FMath::Sin(Th)) * Generator->RingRadius(0, Th)); }
			M.Patches.Insert(Sq, 0);
		}
		// lanes of band K
		const int32 Ns = Generator->SpokeCount(K);
		for (int32 S = 0; S < Ns; ++S)
		{
			FIVMapRoad Rd; Rd.HalfWidth = Generator->SpokeHalf(K, S); Rd.Type = Generator->IsMainSpoke(K, S) ? 1 : 0;
			bool bAny = false;
			for (int32 I = 0; I <= 10; ++I)
			{
				const FVector2D P = Generator->SpokePoint(K, S, I / 10.f);
				Rd.Points.Add(P); bAny |= Bx.IsInside(P);
			}
			if (!bAny) continue;
			// keep only the part in this section (the neighbour draws the rest)
			FIVMapRoad Cut = Rd; Cut.Points.Reset();
			for (int32 I = 0; I < Rd.Points.Num(); ++I)
			{
				const bool In = Bx.IsInside(Rd.Points[I]) || (I > 0 && Bx.IsInside(Rd.Points[I - 1])) || (I + 1 < Rd.Points.Num() && Bx.IsInside(Rd.Points[I + 1]));
				if (In) Cut.Points.Add(Rd.Points[I]);
				else { if (Cut.Points.Num() > 1) M.Roads.Add(Cut); Cut.Points.Reset(); }
			}
			if (Cut.Points.Num() > 1) M.Roads.Add(Cut);
		}
	}
	return M;
}

void AIVSection::RegisterMap()
{
	if (!Generator) return;
	FIVSectionMap M = BuildMapData();
	if (const FIVSectionMap* Old = Generator->MapData.Find(Coord))
	{
		// regenerated after an unload: keep what she has visited
		for (int32 I = 0; I < M.Buildings.Num() && I < Old->Buildings.Num(); ++I) M.Buildings[I].bVisited = Old->Buildings[I].bVisited;
		for (int32 I = 0; I < Blds.Num() && I < M.Buildings.Num(); ++I) Blds[I].bVisited = M.Buildings[I].bVisited;
		M.GeneratedTime = Old->GeneratedTime;
	}
	Generator->MapData.Add(Coord, M);
}

void AIVSection::CollectFlicker()
{
	Flickers.Reset();
	TArray<UPointLightComponent*> Ls; GetComponents(Ls);
	FRandomStream R(Seed + 99);
	for (UPointLightComponent* L : Ls)
	{
		if (!L->ComponentHasTag(IVFlickerTag)) continue;
		float Amt = 0.15f;
		for (const FName& Tg : L->ComponentTags) if (Tg.ToString().StartsWith(TEXT("F"))) { const FString V = Tg.ToString().Mid(1); if (V.IsNumeric()) Amt = FCString::Atof(*V); }
		Flickers.Add({ L, (float)L->Intensity, (float)R.FRandRange(0.f, 100.f), Amt });
	}
}

void AIVSection::Destroyed()
{
	for (AActor* A : OtherActors) if (A) A->Destroy();
	OtherActors.Reset();
	for (AIVVillager* V : Villagers) if (V) V->Destroy();
	Villagers.Reset();
	Super::Destroyed();
}

// ------------------------------------------------------------------------------------------------ buildings (queries)
FString AIVSection::GetBuildingKind(int32 I) const { return Blds.IsValidIndex(I) ? AIVVillageGenerator::KindName(Blds[I].Kind) : FString(); }
FString AIVSection::GetBuildingStyle(int32 I) const { return Blds.IsValidIndex(I) ? StyleName(Blds[I].Style).ToString() : FString(); }
FVector AIVSection::GetBuildingCenter(int32 I) const { return Blds.IsValidIndex(I) ? FVector(Blds[I].C, Blds[I].FloorZ) : FVector::ZeroVector; }
float AIVSection::GetBuildingYaw(int32 I) const { return Blds.IsValidIndex(I) ? Blds[I].Yaw : 0.f; }
FVector2D AIVSection::GetBuildingSize(int32 I) const { return Blds.IsValidIndex(I) && Generator ? FVector2D(Blds[I].Nx, Blds[I].Ny) * Generator->Module : FVector2D::ZeroVector; }
int32 AIVSection::GetBuildingDoor(int32 I) const { return Blds.IsValidIndex(I) ? Blds[I].DoorIndex : -1; }
bool AIVSection::IsBuildingCut(int32 I) const { return Blds.IsValidIndex(I) && Blds[I].bCutWalls; }
bool AIVSection::IsBuildingRoofHidden(int32 I) const { return Blds.IsValidIndex(I) && Blds[I].bCutRoof; }

void AIVSection::GetBuildingEntry(int32 I, FVector& Outside, FVector& Inside) const
{
	Outside = Inside = FVector::ZeroVector;
	if (!Blds.IsValidIndex(I) || !Generator) return;
	const FBld& B = Blds[I];
	const float M = Generator->Module;
	const float Y = (B.DoorCell + 0.5f - B.Ny * 0.5f) * M, X = B.Nx * M * 0.5f;
	Outside = BldPoint(B, X + 130.f, Y, 0.f);
	Inside = BldPoint(B, X - 100.f, Y, B.FloorZ);
}

TArray<int32> AIVSection::GetBuildingContainers(int32 I) const
{
	TArray<int32> Out;
	for (int32 K = 0; K < Containers.Num(); ++K) if (Containers[K].Building == I && (Containers[K].Partner < 0 || Containers[K].Partner > K)) Out.Add(K);
	return Out;
}

FVector AIVSection::GetDoorLocation(int32 I) const { return Doors.IsValidIndex(I) ? Doors[I].Center : FVector::ZeroVector; }
float AIVSection::GetDoorOpenAlpha(int32 I) const { return Doors.IsValidIndex(I) ? Doors[I].Alpha : -1.f; }
FString AIVSection::GetDoorKind(int32 I) const { return Doors.IsValidIndex(I) ? Doors[I].Kind : FString(); }
FVector AIVSection::GetContainerLocation(int32 I) const { return Containers.IsValidIndex(I) ? Containers[I].Center : FVector::ZeroVector; }
float AIVSection::GetContainerOpenAlpha(int32 I) const { return Containers.IsValidIndex(I) ? Containers[I].Alpha : -1.f; }
FString AIVSection::GetContainerKind(int32 I) const { return Containers.IsValidIndex(I) ? Containers[I].Kind : FString(); }
int32 AIVSection::GetContainerBuilding(int32 I) const { return Containers.IsValidIndex(I) ? Containers[I].Building : -1; }
FVector AIVSection::GetContainerStandPoint(int32 I) const { return Containers.IsValidIndex(I) ? Containers[I].Stand : FVector::ZeroVector; }

// ------------------------------------------------------------------------------------------------ interaction
float AIVSection::FindNearestInteractive(const FVector& From, float MaxDistance, bool& bDoor, int32& Index) const
{
	Index = -1; float Best = MaxDistance; bDoor = false;
	for (int32 I = 0; I < Doors.Num(); ++I)
	{
		const FVector D = Doors[I].Center - From;
		const float H = FVector2D(D.X, D.Y).Size();
		if (H < Best && FMath::Abs(D.Z) < 220.f) { Best = H; Index = I; bDoor = true; }
	}
	for (int32 I = 0; I < Containers.Num(); ++I)
	{
		if (Containers[I].bCut) continue;                     // (cut away with its wall: turn the view to open it)
		const FVector D = Containers[I].Center - From;
		const float H = FVector2D(D.X, D.Y).Size() + 20.f;     // a door at the same distance wins
		if (H < Best && FMath::Abs(D.Z) < 220.f) { Best = H; Index = I; bDoor = false; }
	}
	return Index >= 0 ? Best : 1e9f;
}

void AIVSection::ToggleDoor(int32 I, const FVector& Opener)
{
	if (!Doors.IsValidIndex(I)) return;
	FMover& M = Doors[I];
	const float Target = M.Target > 0.5f ? 0.f : 1.f;
	if (Target > 0.5f)
	{
		// swing away from whoever opens it: +yaw swings a +Y leaf toward -X of its pivot (Normal = pivot +X)
		const float Side = FVector::DotProduct(Opener - M.Center, M.Normal) >= 0.f ? 1.f : -1.f;
		M.OpenAngle = 100.f * Side * M.LeafSign;
	}
	M.Target = Target;
}

bool AIVSection::IsTargetOpen(bool bDoor, int32 I) const
{
	const TArray<FMover>& A = bDoor ? Doors : Containers;
	return A.IsValidIndex(I) && A[I].Target > 0.5f;
}

void AIVSection::ToggleContainer(int32 I)
{
	if (!Containers.IsValidIndex(I)) return;
	FMover& M = Containers[I];
	M.Target = M.Target > 0.5f ? 0.f : 1.f;
	if (Containers.IsValidIndex(M.Partner)) Containers[M.Partner].Target = M.Target;
}

// ------------------------------------------------------------------------------------------------ cutaway
int32 AIVSection::BuildingAt(const FVector& L, int32 Current) const
{
	if (!Generator) return -1;
	const float M = Generator->Module;
	for (int32 I = 0; I < Blds.Num(); ++I)
	{
		const FBld& B = Blds[I];
		const FVector2D P = BldLocal(B, FVector2D(L.X, L.Y));
		const float Mg = I == Current ? 70.f : -20.f;
		if (FMath::Abs(P.X) < B.Nx * M * 0.5f + Mg && FMath::Abs(P.Y) < B.Ny * M * 0.5f + Mg && L.Z < B.FloorZ + 260.f) return I;
	}
	return -1;
}

void AIVSection::SetBuildingCut(int32 I, bool bRoof, bool bWalls)
{
	if (!Blds.IsValidIndex(I)) return;
	FBld& B = Blds[I];
	// the building she is in: the roof and the walls facing the camera as the view is turned now (with the tall
	// furniture standing against them); an occluder in front of it: its roof, or everything above its floor
	const bool bAll = bWalls && I != InsideBld;
	B.bCutRoof = bRoof; B.bCutWalls = bWalls;
	const FVector Uc = Generator ? Generator->ToCamera() : FVector(-1, -1, 1);
	const FVector2D ToCam = FVector2D(Uc.X, Uc.Y).GetSafeNormal();
	bool bHide[GNum];
	bHide[GRoof] = bRoof;
	for (int32 G = GWall; G < GNum; ++G) bHide[G] = bWalls && (bAll || GroupNear(B, G, ToCam));
	for (int32 G = 0; G < GNum; ++G)
		for (UInstancedStaticMeshComponent* C : B.Group[G]) if (C) C->SetVisibility(!bHide[G]);
	for (FMover& M : Doors)
		if (M.Building == I && M.Group >= 0 && M.Group < GNum)
			for (UStaticMeshComponent* P : M.Parts) if (P) P->SetVisibility(!bHide[M.Group]);
	for (FMover& M : Containers)
		if (M.Building == I && M.Group >= GWall && M.Group < GNum)
		{
			M.bCut = bHide[M.Group];
			if (M.Body) M.Body->SetVisibility(!M.bCut);
			for (UStaticMeshComponent* P : M.Parts) if (P) P->SetVisibility(!M.bCut);
		}
	for (UPointLightComponent* L : B.FillLights) if (L) L->SetVisibility(bRoof && I == InsideBld);
}

FVector2D AIVSection::GroupOut(int32 G)
{
	if (G >= GCorner) return FVector2D(((G - GCorner) & 2) ? 1.f : -1.f, ((G - GCorner) & 1) ? 1.f : -1.f).GetSafeNormal();
	switch (G - GWall) { case 0: return FVector2D(1, 0); case 1: return FVector2D(-1, 0); case 2: return FVector2D(0, 1); default: return FVector2D(0, -1); }
}

bool AIVSection::GroupNear(const FBld& B, int32 G, const FVector2D& ToCam) const
{
	const FVector2D O = GroupOut(G);
	return FVector2D::DotProduct(B.Fx * O.X + B.Fy * O.Y, ToCam) > 0.08f;
}

bool AIVSection::IsBuildingWallHidden(int32 I, int32 Wall) const
{
	if (!Blds.IsValidIndex(I) || Wall < GWall || Wall >= GCorner) return false;
	for (const UInstancedStaticMeshComponent* C : Blds[I].Group[Wall]) if (C && !C->IsVisible()) return true;
	return false;
}

bool AIVSection::IsBuildingWallNear(int32 I, int32 Wall) const
{
	if (!Blds.IsValidIndex(I) || Wall < GWall || Wall >= GCorner || !Generator) return false;
	const FVector U = Generator->ToCamera();
	return GroupNear(Blds[I], Wall, FVector2D(U.X, U.Y).GetSafeNormal());
}

void AIVSection::ClearCutaway()
{
	const int32 Was = InsideBld;
	InsideBld = -1;
	for (int32 I = 0; I < Blds.Num(); ++I) if (Blds[I].bCutRoof || Blds[I].bCutWalls || I == Was) SetBuildingCut(I, false, false);
}

void AIVSection::EnterBuilding(int32 I)
{
	if (!Blds.IsValidIndex(I)) return;
	InsideBld = I;
	SetBuildingCut(I, true, true);
	Blds[I].bVisited = true;
	if (Generator) if (FIVSectionMap* M = Generator->MapData.Find(Coord)) if (M->Buildings.IsValidIndex(I)) M->Buildings[I].bVisited = true;
}

void AIVSection::GetBuildingFloorSamples(int32 I, TArray<FVector>& Out) const
{
	Out.Reset();
	if (!Blds.IsValidIndex(I) || !Generator) return;
	const FBld& B = Blds[I];
	const float M = Generator->Module;
	const float Hx = B.Nx * M * 0.5f - 45.f, Hy = B.Ny * M * 0.5f - 45.f;
	const int32 Sx = B.Nx + 1, Sy = B.Ny + 1;
	for (int32 X = 0; X < Sx; ++X)
		for (int32 Y = 0; Y < Sy; ++Y)
			for (float Z : { 15.f, 130.f })
				Out.Add(BldPoint(B, FMath::Lerp(-Hx, Hx, X / (float)(Sx - 1)), FMath::Lerp(-Hy, Hy, Y / (float)(Sy - 1)), B.FloorZ + Z));
}

void AIVSection::CutOccluders(const TArray<FVector>& Floor, const FVector& U, int32 Skip)
{
	if (!Generator || Floor.Num() == 0) return;
	const float M = Generator->Module, WH = Generator->WallHeight;
	const FVector F0 = Floor[0];
	for (int32 I = 0; I < Blds.Num(); ++I)
	{
		if (I == Skip) continue;
		FBld& B = Blds[I];
		if (FVector2D::DistSquared(B.C, FVector2D(F0.X, F0.Y)) > FMath::Square(3600.f)) continue;
		const float Hx = B.Nx * M * 0.5f, Hy = B.Ny * M * 0.5f;
		const float Top = B.FloorZ + B.Storeys * WH;
		const float HalfSpan = B.Span * M * 0.5f;
		const float TowerTop = B.TowerStoreys > 0 ? B.FloorZ + B.TowerStoreys * WH + M * 1.2f : 0.f;
		bool bRoof = false, bWalls = false;
		for (const FVector& F : Floor)
		{
			for (float S = 60.f; S < 2400.f && !(bRoof && bWalls); S += 55.f)
			{
				const FVector P = F + U * S;
				if (P.Z > FMath::Max(Top + HalfSpan + 60.f, TowerTop)) break;
				const FVector2D L = BldLocal(B, FVector2D(P.X, P.Y));
				if (FMath::Abs(L.X) > Hx + 70.f || FMath::Abs(L.Y) > Hy + 70.f) continue;
				if (P.Z < Top) { if (FMath::Abs(L.X) < Hx + 25.f && FMath::Abs(L.Y) < Hy + 25.f) bWalls = true; }
				else
				{
					const float Across = B.bRidgeY ? L.X : L.Y;
					if (P.Z < Top + HalfSpan + 50.f - FMath::Abs(Across)) bRoof = true;
					if (B.TowerStoreys > 0 && L.X > Hx - B.TowerCells * M - 30.f && P.Z < TowerTop) bRoof = true;
				}
			}
			if (bRoof && bWalls) break;
		}
		if (bRoof || bWalls) SetBuildingCut(I, true, bWalls);
	}
}

// ------------------------------------------------------------------------------------------------ villagers
int32 AIVSection::GetWantedVillagers() const
{
	if (!Generator || Blds.Num() == 0) return 0;
	bool bAny = false;
	for (const FIVVillagerDef& D : Generator->Villagers) bAny |= D.Mesh != nullptr && D.Weight > 0.f;
	return bAny ? FMath::RoundToInt(Generator->VillagerCoverage * Blds.Num()) : 0;
}

bool AIVSection::RandomVillagerSpot(FRandomStream& R, const FVector& From, FVector& Out, float MinDist, float MaxDist) const
{
	if (!Generator) return false;
	const float M = Generator->Module, SS = Generator->SectionSize;
	const FVector2D Mn = GetSectionMin(), F(From.X, From.Y);
	const bool bSquare = Generator->IsStartSection(Coord);
	for (int32 Try = 0; Try < 14; ++Try)
	{
		const float U = R.FRand();
		FVector2D P(0, 0);
		if (U < 0.42f && Blds.Num() > 0)
		{
			// in front of somebody's house, clear of the doorway
			const FBld& B = Blds[R.RandRange(0, Blds.Num() - 1)];
			const float Y = (B.DoorCell + 0.5f - B.Ny * 0.5f) * M;
			const FVector D = BldPoint(B, B.Nx * M * 0.5f + R.FRandRange(290.f, 520.f), Y + R.FRandRange(-240.f, 240.f));
			P = FVector2D(D.X, D.Y);
		}
		else if (U < 0.60f && bSquare)
		{
			// the market square
			const float A = R.FRandRange(0.f, 2.f * PI), Rd = Generator->SquareRadius * 0.9f * FMath::Sqrt(R.FRand());
			P = FVector2D(FMath::Cos(A), FMath::Sin(A)) * Rd;
		}
		else
		{
			// on a street or a lane
			bool bRoad = false;
			for (int32 K = 0; K < 8 && !bRoad; ++K)
			{
				P = Mn + FVector2D(R.FRandRange(150.f, SS - 150.f), R.FRandRange(150.f, SS - 150.f));
				int32 Type = 0;
				bRoad = Generator->RoadDistance(P, Type) < -60.f;
			}
			if (!bRoad) continue;
		}
		const float D = FVector2D::Distance(P, F);
		if (D < MinDist || D > MaxDist) continue;
		// its own section (each keeps its share of the villagers), free ground with some elbow room
		if (P.X < Mn.X + 60.f || P.Y < Mn.Y + 60.f || P.X > Mn.X + SS - 60.f || P.Y > Mn.Y + SS - 60.f) continue;
		bool bFree = NavAt(P) == 0;
		for (int32 K = 0; K < 4 && bFree; ++K) bFree = !Generator->NavBlocked(P + FVector2D(K == 0 ? 60.f : K == 1 ? -60.f : 0.f, K == 2 ? 60.f : K == 3 ? -60.f : 0.f));
		if (!bFree) continue;
		Out = FVector(P, 0.f);
		return true;
	}
	return false;
}

void AIVSection::SpawnVillager(int32 K)
{
	UWorld* W = GetWorld();
	if (!W || !Generator) return;
	FRandomStream R((int32)(((uint32)Seed * 2654435761u + (uint32)K * 40503u + 977u) & 0x7fffffff));
	// the model, by weight
	float Total = 0.f;
	for (const FIVVillagerDef& D : Generator->Villagers) if (D.Mesh) Total += FMath::Max(D.Weight, 0.f);
	if (Total <= 0.f) return;
	float Pick = R.FRand() * Total;
	const FIVVillagerDef* Def = nullptr;
	for (const FIVVillagerDef& D : Generator->Villagers)
	{
		if (!D.Mesh || D.Weight <= 0.f) continue;
		Def = &D; Pick -= D.Weight;
		if (Pick <= 0.f) break;
	}
	if (!Def) return;
	// it starts somewhere a villager would go: not on top of another one, not where she starts
	FVector P = FVector::ZeroVector; bool bOk = false;
	for (int32 Try = 0; Try < 6 && !bOk; ++Try)
	{
		if (!RandomVillagerSpot(R, FVector::ZeroVector, P, 0.f, 1e9f)) continue;
		bOk = FVector2D(P.X, P.Y).SizeSquared() > 350.f * 350.f;
		for (const AIVVillager* O : Villagers) if (O && FVector2D::DistSquared(O->Ground(), FVector2D(P.X, P.Y)) < 160.f * 160.f) bOk = false;
	}
	if (!bOk) return;
	FActorSpawnParameters Sp;
	Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	Sp.Owner = this; Sp.ObjectFlags |= RF_Transient;
	AIVVillager* V = W->SpawnActor<AIVVillager>(AIVVillager::StaticClass(), FTransform(FRotator(0.f, R.FRandRange(-180.f, 180.f), 0.f), FVector(P.X, P.Y, 90.f)), Sp);
	if (!V) return;
	V->Setup(this, *Def, R.RandRange(1, 0x3fffffff));
	Villagers.Add(V);
}

// ------------------------------------------------------------------------------------------------ curtain + tick
void AIVSection::ShowCurtain(UMaterialInterface* Material, float StartTime, float Height, float Lifetime)
{
	if (!Generator || !Material) return;
	UProceduralMeshComponent* C = NewObject<UProceduralMeshComponent>(this);
	C->SetupAttachment(RootComponent);
	C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	C->SetCastShadow(false);
	C->RegisterComponent();
	const float SS = Generator->SectionSize, Stp = 500.f;
	const int32 Ns = FMath::RoundToInt(SS / Stp);
	const FVector2D Corner[5] = { FVector2D(0, 0), FVector2D(SS, 0), FVector2D(SS, SS), FVector2D(0, SS), FVector2D(0, 0) };
	TArray<FVector> V; TArray<int32> Tri; TArray<FVector> Nrm; TArray<FVector2D> UV; TArray<FLinearColor> Col; TArray<FProcMeshTangent> Tan;
	float Uu = 0.f;
	for (int32 Side = 0; Side < 4; ++Side)
	{
		const FVector2D Dr = (Corner[Side + 1] - Corner[Side]).GetSafeNormal();
		const FVector Out = FVector(Dr.Y, -Dr.X, 0.f);
		for (int32 K = 0; K <= Ns; ++K)
		{
			const FVector2D P = Corner[Side] + (Corner[Side + 1] - Corner[Side]) * ((float)K / Ns);
			const int32 I0 = V.Num();
			V.Add(FVector(P.X, P.Y, -20.f)); V.Add(FVector(P.X, P.Y, -20.f + Height));
			UV.Add(FVector2D(Uu / 1000.f, 0.f)); UV.Add(FVector2D(Uu / 1000.f, 1.f));
			Nrm.Add(Out); Nrm.Add(Out);
			if (K > 0) Tri.Append({ I0 - 2, I0, I0 - 1, I0 - 1, I0, I0 + 1 });
			Uu += Stp;
		}
	}
	C->CreateMeshSection_LinearColor(0, V, Tri, Nrm, UV, Col, Tan, false);
	UMaterialInstanceDynamic* Mi = UMaterialInstanceDynamic::Create(Material, C);
	Mi->SetScalarParameterValue(TEXT("StartTime"), StartTime);
	C->SetMaterial(0, Mi);
	FTimerHandle H;
	GetWorldTimerManager().SetTimer(H, FTimerDelegate::CreateWeakLambda(C, [C]() { C->DestroyComponent(); }), Lifetime, false);
}

void AIVSection::Tick(float Dt)
{
	Super::Tick(Dt);
	UWorld* W = GetWorld();
	if (!W || !W->IsGameWorld()) return;
	const float Now = W->GetTimeSeconds();
	const AActor* Pawn = Generator ? Generator->GetTrackedActor() : UGameplayStatics::GetPlayerPawn(this, 0);
	const FVector PL = Pawn ? Pawn->GetActorLocation() : FVector(1e9);
	// cinematics: doors open by themselves in front of the tracked actor and close behind her
	if (Generator && Generator->TrackedActor && Generator->TrackedAutoDoorDistance > 0.f)
		for (int32 I = 0; I < Doors.Num(); ++I)
		{
			FMover& M = Doors[I];
			const float D = FVector::Dist2D(PL, M.Center);
			if (M.Target < 0.5f && D < Generator->TrackedAutoDoorDistance) ToggleDoor(I, PL);
			else if (M.Target > 0.5f && D > Generator->TrackedAutoDoorDistance + 260.f) M.Target = 0.f;
		}
	for (const FFlicker& F : Flickers)
	{
		if (!F.Light || !F.Light->IsVisible() || FVector::DistSquared(F.Light->GetComponentLocation(), PL) > 4000.f * 4000.f) continue;
		const float Nz = FMath::PerlinNoise1D(Now * 7.f + F.Phase) * 0.6f + FMath::PerlinNoise1D(Now * 19.f + F.Phase * 2.f) * 0.4f;
		F.Light->SetIntensity(F.Base * (1.f + F.Amount * Nz * 1.6f));
	}
	auto Animate = [Dt](FMover& M)
	{
		if (M.Alpha == M.Target) return;
		M.Alpha = FMath::FInterpConstantTo(M.Alpha, M.Target, Dt, M.bDoor ? 1.6f : 1.8f);
		const float E = M.Alpha * M.Alpha * (3.f - 2.f * M.Alpha);
		M.Pivot->SetRelativeRotation(M.Closed * FQuat(M.Axis, FMath::DegreesToRadians(M.OpenAngle * E)));
		// moving / open leaves and lids never push anyone
		const bool bShut = M.Alpha < 0.02f;
		for (UStaticMeshComponent* C : M.Parts)
			C->SetCollisionEnabled(bShut ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
	};
	for (FMover& M : Doors) Animate(M);
	for (FMover& M : Containers) Animate(M);
}
