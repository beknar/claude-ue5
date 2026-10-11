#include "RT/RTCell.h"
#include "RT/RTTownGenerator.h"
#include "RT/RTBuilding.h"
#include "ProceduralMeshComponent.h"
#include "KismetProceduralMeshLibrary.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "TimerManager.h"
#include "HAL/PlatformTime.h"

DEFINE_LOG_CATEGORY_STATIC(LogRandomTown, Log, All);

static const float PadSink = 8.f;      // ground under a building sits this far below its floor (no z-fighting)
static const float PadMargin = 60.f;   // flat margin around the footprint
static const float PadBlend = 380.f;   // then back to the natural terrain over this distance (ends inside the cell)

ARTCell::ARTCell()
{
	PrimaryActorTick.bCanEverTick = false;
	Ground = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("Ground"));
	RootComponent = Ground;
	Ground->bUseAsyncCooking = true;
	Ground->SetMobility(EComponentMobility::Static);
	Ground->SetCollisionProfileName(TEXT("BlockAll"));
}

FVector2D ARTCell::GetCellMin() const
{
	const float CS = Generator ? Generator->CellSize : 25000.f;
	return FVector2D(Coord.X * CS, Coord.Y * CS);
}

float ARTCell::SurfaceHeight(float X, float Y) const
{
	float Z = ARTTownGenerator::TerrainHeight(X, Y);
	float BestW = 0.f, BestZ = Z;
	for (const FRTPad& P : Pads)
	{
		const float Dx = (float)FMath::Max3<double>(P.Min.X - X, 0.0, X - P.Max.X), Dy = (float)FMath::Max3<double>(P.Min.Y - Y, 0.0, Y - P.Max.Y);
		const float D = FMath::Sqrt(Dx * Dx + Dy * Dy);
		if (D <= 0.f) return P.Z - PadSink;                            // under the building
		float Wt = 0.f, Zt = P.Z;
		if (D <= PadMargin) Wt = 1.f;
		else if (D < PadMargin + PadBlend) { const float U = (D - PadMargin) / PadBlend; Wt = 1.f - U * U * (3.f - 2.f * U); }
		if (D < PadMargin * 0.5f) Zt = P.Z - PadSink * (1.f - D / (PadMargin * 0.5f));
		if (Wt > BestW) { BestW = Wt; BestZ = Zt; }
	}
	return FMath::Lerp(Z, BestZ, BestW);
}

float ARTCell::StreetDistance(const FVector2D& P) const
{
	const float BS = Generator->BlockSize;
	const float Dx = FMath::Abs(P.X - FMath::RoundToFloat(P.X / BS) * BS), Dy = FMath::Abs(P.Y - FMath::RoundToFloat(P.Y / BS) * BS);
	return FMath::Min(Dx, Dy);
}

void ARTCell::BuildGround()
{
	if (!Generator) return;
	const float S = Generator->GroundSpacing, CS = Generator->CellSize;
	const int32 N = FMath::RoundToInt(CS / S) + 1;
	const FVector2D Min = GetCellMin();
	const float Half = Generator->StreetHalfWidth;
	TArray<FVector> V; TArray<FVector> Nrm; TArray<FVector2D> UV; TArray<FLinearColor> Col; TArray<FProcMeshTangent> Tan;
	V.Reserve(N * N); Nrm.Reserve(N * N); UV.Reserve(N * N); Col.Reserve(N * N);
	for (int32 I = 0; I < N; ++I)
	{
		for (int32 J = 0; J < N; ++J)
		{
			const float X = Min.X + I * S, Y = Min.Y + J * S;
			const float Z = SurfaceHeight(X, Y);
			V.Add(FVector(I * S, J * S, Z));
			const float E = S * 0.5f;
			const FVector Nm = FVector(SurfaceHeight(X - E, Y) - SurfaceHeight(X + E, Y), SurfaceHeight(X, Y - E) - SurfaceHeight(X, Y + E), 2.f * E).GetSafeNormal();
			Nrm.Add(Nm);
			UV.Add(FVector2D(X / 400.f, Y / 400.f));
			const float Sd = StreetDistance(FVector2D(X, Y));
			const float Road = 1.f - FMath::SmoothStep(Half - 70.f, Half + 50.f, Sd);
			float Dirt = 0.f;
			for (const FRTPad& P : Pads)
			{
				const float Dx = (float)FMath::Max3<double>(P.Min.X - X, 0.0, X - P.Max.X), Dy = (float)FMath::Max3<double>(P.Min.Y - Y, 0.0, Y - P.Max.Y);
				Dirt = FMath::Max(Dirt, 1.f - FMath::SmoothStep(PadMargin, PadMargin + 250.f, FMath::Sqrt(Dx * Dx + Dy * Dy)));
			}
			Col.Add(FLinearColor(Road, Dirt, 0.f, 1.f));
		}
	}
	TArray<int32> Tri;
	UKismetProceduralMeshLibrary::CreateGridMeshTriangles(N, N, false, Tri);      // (true faces down: culled from above)
	Ground->ClearAllMeshSections();
	Ground->CreateMeshSection_LinearColor(0, V, Tri, Nrm, UV, Col, Tan, true);
	if (Generator->GroundMaterial) Ground->SetMaterial(0, Generator->GroundMaterial);
}

const FRTScatterItem* ARTCell::Pick(FRandomStream& R, const TArray<FRTScatterItem>& Items) const
{
	float Sum = 0.f;
	for (const FRTScatterItem& It : Items) if (It.Mesh) Sum += It.Weight;
	if (Sum <= 0.f) return nullptr;
	float U = R.FRand() * Sum;
	for (const FRTScatterItem& It : Items) { if (!It.Mesh) continue; U -= It.Weight; if (U <= 0.f) return &It; }
	return nullptr;
}

float ARTCell::ItemRadius(const FRTScatterItem& It, float Scale)
{
	if (It.Radius > 0.f) return It.Radius * Scale;
	const FVector E = It.Mesh ? It.Mesh->GetBounds().BoxExtent : FVector(50);
	return FMath::Max(E.X, E.Y) * Scale;
}

bool ARTCell::IsFree(const FVector2D& P, float Radius, bool bIgnoreCircles) const
{
	const FVector2D Min = GetCellMin(); const float CS = Generator->CellSize;
	if (P.X < Min.X + Radius || P.Y < Min.Y + Radius || P.X > Min.X + CS - Radius || P.Y > Min.Y + CS - Radius) return false;
	if (StreetDistance(P) < Generator->StreetHalfWidth + Radius + 40.f) return false;
	for (const FBox2D& B : Solid) if (B.ExpandBy(Radius).IsInside(P)) return false;
	for (const FBox2D& B : KeepClear) if (B.ExpandBy(Radius).IsInside(P)) return false;
	if (!bIgnoreCircles) for (const FCircle& C : Circles) if (FVector2D::Distance(C.C, P) < C.R + Radius) return false;
	return true;
}

void ARTCell::AddInstance(const FRTScatterItem& It, const FVector2D& P, float Yaw, float Scale)
{
	const float Z = SurfaceHeight(P.X, P.Y) - 2.f;
	PendingInstances.FindOrAdd(It.Mesh).Add(FTransform(FRotator(0, Yaw, 0), FVector(P.X, P.Y, Z), FVector(Scale)));
	if (!Hisms.Contains(It.Mesh))
	{
		UHierarchicalInstancedStaticMeshComponent* H = NewObject<UHierarchicalInstancedStaticMeshComponent>(this, NAME_None, RF_Transactional);
		H->SetStaticMesh(It.Mesh);
		H->SetMobility(EComponentMobility::Static);
		H->SetupAttachment(RootComponent);
		H->SetCollisionProfileName(It.bCollision ? TEXT("BlockAll") : TEXT("NoCollision"));
		if (!It.bCollision) H->SetCanEverAffectNavigation(false);
		if (It.CullDistance > 0.f) H->SetCullDistances(It.CullDistance * 0.7f, It.CullDistance);
		H->RegisterComponent();
		AddInstanceComponent(H);
		Hisms.Add(It.Mesh, H);
	}
	++NumInstances;
}

void ARTCell::FlushInstances()
{
	for (auto& KV : PendingInstances)
		if (UHierarchicalInstancedStaticMeshComponent** H = Hisms.Find(KV.Key)) (*H)->AddInstances(KV.Value, false, true);
	PendingInstances.Reset();
}

void ARTCell::ScatterIn(FRandomStream& R, const FBox2D& Area, const TArray<FRTScatterItem>& Items, int32 Count, bool bSolid, float Clearance)
{
	int32 Placed = 0;
	for (int32 Try = 0; Try < Count * 10 && Placed < Count; ++Try)
	{
		const FRTScatterItem* It = Pick(R, Items);
		if (!It) return;
		const float Sc = R.FRandRange(It->Scale.X, It->Scale.Y);
		const float Rad = ItemRadius(*It, Sc);
		const FVector2D P(R.FRandRange(Area.Min.X, Area.Max.X), R.FRandRange(Area.Min.Y, Area.Max.Y));
		if (!IsFree(P, Rad + (bSolid ? Clearance : 0.f), !bSolid)) continue;
		AddInstance(*It, P, R.FRandRange(0.f, 360.f), Sc);
		if (bSolid) Circles.Add({ P, Rad });
		++Placed;
	}
}

static FVector2D Rot2(const FVector2D& V, float YawDeg)
{
	const float C = FMath::Cos(FMath::DegreesToRadians(YawDeg)), S = FMath::Sin(FMath::DegreesToRadians(YawDeg));
	return FVector2D(V.X * C - V.Y * S, V.X * S + V.Y * C);
}

bool ARTCell::PlaceBuilding(FRandomStream& R, const FBox2D& Slot, int32 Axis, float Sign, float StreetLine, const TArray<FName>& Purposes)
{
	const TArray<FRTBuildingTemplate>& Ts = Generator->Templates;
	const int32 Lat = 1 - Axis;
	const FVector2D Front = Axis == 0 ? FVector2D(Sign, 0) : FVector2D(0, Sign);
	const float SlotDepth = Slot.GetSize()[Axis], SlotLen = Slot.GetSize()[Lat];
	struct FCand { int32 T; float Yaw; FVector2D RMin, RMax; };
	TArray<FCand> Cands; float WSum = 0.f;
	for (int32 I = 0; I < Ts.Num(); ++I)
	{
		const FRTBuildingTemplate& T = Ts[I];
		if (!Purposes.Contains(T.Purpose)) continue;
		const float Yaw = FMath::RadiansToDegrees(FMath::Atan2(Front.Y, Front.X) - FMath::Atan2(T.EntryOut.Y, T.EntryOut.X));
		FVector2D RMin(1e9), RMax(-1e9);
		for (const FVector2D& Cn : { T.BoundsMin, FVector2D(T.BoundsMin.X, T.BoundsMax.Y), T.BoundsMax, FVector2D(T.BoundsMax.X, T.BoundsMin.Y) })
		{
			const FVector2D Q = Rot2(Cn, Yaw); RMin = FVector2D::Min(RMin, Q); RMax = FVector2D::Max(RMax, Q);
		}
		const FVector2D Sz = RMax - RMin;
		if (Sz[Axis] > SlotDepth - 120.f || Sz[Lat] > SlotLen - 100.f) continue;
		Cands.Add({ I, Yaw, RMin, RMax }); WSum += T.Weight;
	}
	if (Cands.Num() == 0) return false;
	float U = R.FRand() * WSum; const FCand* C = &Cands.Last();
	for (const FCand& Cd : Cands) { U -= Ts[Cd.T].Weight; if (U <= 0.f) { C = &Cd; break; } }
	const FRTBuildingTemplate& T = Ts[C->T];
	// entrance face 80 cm back from the slot's street edge, centred along the street
	FVector2D O;
	const float FrontEdge = Sign > 0 ? Slot.Max[Axis] : Slot.Min[Axis];
	const float Face = Sign > 0 ? C->RMax[Axis] : C->RMin[Axis];
	O[Axis] = FrontEdge - Sign * 80.f - Face;
	O[Lat] = Slot.GetCenter()[Lat] - (C->RMin[Lat] + C->RMax[Lat]) * 0.5f;
	const FBox2D Foot(O + C->RMin, O + C->RMax);
	float PadZ = 0.f;
	for (const FVector2D& Q : { Foot.Min, Foot.Max, FVector2D(Foot.Min.X, Foot.Max.Y), FVector2D(Foot.Max.X, Foot.Min.Y), Foot.GetCenter() })
		PadZ += ARTTownGenerator::TerrainHeight(Q.X, Q.Y) / 5.f;
	FRTPad Pad; Pad.Min = Foot.Min; Pad.Max = Foot.Max; Pad.Z = PadZ;
	Pads.Add(Pad);
	Solid.Add(Foot);
	const FVector2D Entry = O + Rot2(T.EntryMid, C->Yaw);
	FVector2D StreetP = Entry; StreetP[Axis] = StreetLine;
	KeepClear.Add(FBox2D(FVector2D::Min(Entry, StreetP) - FVector2D(160), FVector2D::Max(Entry, StreetP) + FVector2D(160)));
	FActorSpawnParameters P; P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ARTBuilding* Bd = GetWorld()->SpawnActor<ARTBuilding>(ARTBuilding::StaticClass(), FTransform(FRotator(0, C->Yaw, 0), FVector(O.X, O.Y, PadZ - T.FloorZ)), P);
	if (!Bd) return false;
	Bd->StreetPoint = FVector(StreetP.X, StreetP.Y, ARTTownGenerator::TerrainHeight(StreetP.X, StreetP.Y));
#if WITH_EDITOR
	if (bEditor) { Bd->SetActorLabel(FString::Printf(TEXT("RT_%s_%d_%d_%d"), *T.Name.ToString(), Coord.X, Coord.Y, Buildings.Num())); Bd->SetFolderPath(TEXT("RandomTown/Buildings")); }
#endif
	Bd->Init(Generator, C->T, bEditor);
	Buildings.Add(Bd);
	return true;
}

void ARTCell::LayoutBlock(FRandomStream& R, int32 Bx, int32 By, const FString& Type)
{
	const float BS = Generator->BlockSize, H = Generator->StreetHalfWidth;
	const FVector2D Min = GetCellMin();
	const FVector2D B0(Min.X + Bx * BS, Min.Y + By * BS);
	const FBox2D Inner(B0 + FVector2D(H + 50.f), B0 + FVector2D(BS - H - 50.f));
	const FVector2D Ctr = Inner.GetCenter();
	if (Type == TEXT("houses") || Type == TEXT("tavern") || Type == TEXT("garden"))
	{
		const int32 Axis = R.RandBool() ? 0 : 1, Lat = 1 - Axis;
		const TArray<FName> Homes = Type == TEXT("garden") ? TArray<FName>{ TEXT("cabin") } : TArray<FName>{ TEXT("home"), TEXT("store"), TEXT("workshop"), TEXT("cabin") };
		bool bTavernDone = Type != TEXT("tavern");
		for (int32 Side = 0; Side < 2; ++Side)
		{
			const float Sign = Side == 0 ? -1.f : 1.f;
			FBox2D Lot = Inner;
			if (Side == 0) Lot.Max[Axis] = Ctr[Axis]; else Lot.Min[Axis] = Ctr[Axis];
			const float Line = Side == 0 ? B0[Axis] : B0[Axis] + BS;
			if (Type == TEXT("garden") && R.FRand() < 0.35f) continue;
			if (!bTavernDone)
			{
				// the tavern takes a whole lot side if it fits there
				if (PlaceBuilding(R, Lot, Axis, Sign, Line, { TEXT("tavern") })) { bTavernDone = true; continue; }
			}
			bool bTwo = Type != TEXT("garden") && R.FRand() < 0.4f, bDone = false;
			if (bTwo)
			{
				FBox2D A = Lot, Bb = Lot; A.Max[Lat] = Lot.GetCenter()[Lat]; Bb.Min[Lat] = Lot.GetCenter()[Lat];
				const bool Ok1 = PlaceBuilding(R, A, Axis, Sign, Line, Homes);
				const bool Ok2 = PlaceBuilding(R, Bb, Axis, Sign, Line, Homes);
				bDone = Ok1 || Ok2;
			}
			if (!bDone) PlaceBuilding(R, Lot, Axis, Sign, Line, Homes);
		}
		ScatterIn(R, Inner, Generator->YardProps, Type == TEXT("garden") ? 7 : 5, true);
		ScatterIn(R, Inner, Generator->Trees, Type == TEXT("garden") ? 4 : 1, true, 150.f);
		ScatterIn(R, Inner, Generator->Bushes, 4, false);
		ScatterIn(R, Inner, Generator->Rocks, 1, true);
		ScatterIn(R, Inner, Generator->Grass, Type == TEXT("garden") ? 90 : 40, false);
	}
	else if (Type == TEXT("market"))
	{
		// well in the middle, two rows of stalls facing the centre aisle, tents at two corners
		if (const FRTScatterItem* W = Pick(R, Generator->Wells)) { AddInstance(*W, Ctr, R.FRandRange(0, 360), 1.f); Circles.Add({ Ctr, ItemRadius(*W, 1.f) + 120.f }); }
		const int32 Axis = R.RandBool() ? 0 : 1, Lat = 1 - Axis;
		for (int32 Row = -1; Row <= 1; Row += 2)
		{
			for (int32 K = -1; K <= 1; ++K)
			{
				if (Generator->MarketStalls.Num() == 0) break;
				UClass* Cls = Generator->MarketStalls[R.RandRange(0, Generator->MarketStalls.Num() - 1)].LoadSynchronous();
				if (!Cls) continue;
				FVector2D P = Ctr; P[Axis] += Row * 900.f; P[Lat] += K * 1100.f;
				const float Yaw = (Axis == 0 ? (Row < 0 ? 0.f : 180.f) : (Row < 0 ? 90.f : 270.f)) + 90.f;
				FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
				AActor* A = GetWorld()->SpawnActor<AActor>(Cls, FTransform(FRotator(0, Yaw, 0), FVector(P.X, P.Y, SurfaceHeight(P.X, P.Y)), FVector(1.f)), Sp);
				if (!A) continue;
#if WITH_EDITOR
				if (bEditor) A->SetFolderPath(TEXT("RandomTown/Market"));
#endif
				FVector O, E; A->GetActorBounds(true, O, E);
				Solid.Add(FBox2D(FVector2D(O.X - E.X, O.Y - E.Y), FVector2D(O.X + E.X, O.Y + E.Y)));
				OtherActors.Add(A);
			}
		}
		for (int32 Cn = 0; Cn < 2; ++Cn)
		{
			const FRTScatterItem* Tn = Pick(R, Generator->Tents);
			if (!Tn) break;
			const float Rad = ItemRadius(*Tn, 1.f);
			FVector2D P(Cn == 0 ? Inner.Min.X + Rad + 100.f : Inner.Max.X - Rad - 100.f, Cn == 0 ? Inner.Min.Y + Rad + 100.f : Inner.Max.Y - Rad - 100.f);
			if (IsFree(P, Rad + 60.f)) { AddInstance(*Tn, P, R.FRandRange(0, 360), 1.f); Circles.Add({ P, Rad }); }
		}
		ScatterIn(R, Inner, Generator->MarketProps, 12, true, 40.f);
		ScatterIn(R, Inner, Generator->Trees, 2, true, 150.f);
		ScatterIn(R, Inner, Generator->Grass, 25, false);
	}
	else // green
	{
		if (R.FRand() < 0.4f) if (const FRTScatterItem* W = Pick(R, Generator->Wells)) { AddInstance(*W, Ctr, R.FRandRange(0, 360), 1.f); Circles.Add({ Ctr, ItemRadius(*W, 1.f) + 100.f }); }
		ScatterIn(R, Inner, Generator->Trees, R.RandRange(6, 10), true, 150.f);
		ScatterIn(R, Inner, Generator->Rocks, 3, true);
		ScatterIn(R, Inner, Generator->Bushes, 8, false);
		ScatterIn(R, Inner, Generator->YardProps, 2, true);
		ScatterIn(R, Inner, Generator->Grass, 140, false);
	}
}

void ARTCell::Generate(ARTTownGenerator* InGenerator, FIntPoint InCoord, int32 InSeed, bool bEditorBuild)
{
	const double T0 = FPlatformTime::Seconds();
	Generator = InGenerator; Coord = InCoord; Seed = InSeed; bEditor = bEditorBuild; bEditorBuilt = bEditorBuild;
	FRandomStream R(Seed);
	const int32 NB = FMath::RoundToInt(Generator->CellSize / Generator->BlockSize);
	// block types: one tavern per cell, at most two markets
	TArray<FString> Types; Types.SetNum(NB * NB);
	const int32 Tavern = R.RandRange(0, NB * NB - 1);
	int32 Markets = 0;
	for (int32 K = 0; K < NB * NB; ++K)
	{
		if (K == Tavern) { Types[K] = TEXT("tavern"); continue; }
		const float U = R.FRand();
		Types[K] = U < 0.42f ? TEXT("houses") : U < 0.66f ? TEXT("garden") : (U < 0.8f && Markets < 2) ? (++Markets, TEXT("market")) : TEXT("green");
	}
	BlockTypes = Types;
	Pads.Reset(); Solid.Reset(); KeepClear.Reset(); Circles.Reset();
	for (int32 K = 0; K < NB * NB; ++K) LayoutBlock(R, K % NB, K / NB, Types[K]);
	FlushInstances();
	BuildGround();
	GenerateMs = (FPlatformTime::Seconds() - T0) * 1000.0;
	UE_LOG(LogRandomTown, Log, TEXT("RTCELL (%d,%d) seed %d: %d buildings, %d instances, %d other, %.0f ms%s"), Coord.X, Coord.Y, Seed, Buildings.Num(), NumInstances, OtherActors.Num(), GenerateMs, bEditor ? TEXT(" [editor]") : TEXT(""));
}

void ARTCell::ShowCurtain(UMaterialInterface* Material, float StartTime, float Height, float Lifetime)
{
	if (!Generator || !Material) return;
	UProceduralMeshComponent* C = NewObject<UProceduralMeshComponent>(this);
	C->SetupAttachment(RootComponent);
	C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	C->SetCastShadow(false);
	C->RegisterComponent();
	// a column every 5 m around the border, following the ground; U runs along the border in units of 10 m
	const float CS = Generator->CellSize, Step = 500.f;
	const int32 N = FMath::RoundToInt(CS / Step);
	const FVector2D Min = GetCellMin();
	const FVector2D Corner[5] = { FVector2D(0, 0), FVector2D(CS, 0), FVector2D(CS, CS), FVector2D(0, CS), FVector2D(0, 0) };
	TArray<FVector> V; TArray<int32> Tri; TArray<FVector> Nrm; TArray<FVector2D> UV; TArray<FLinearColor> Col; TArray<FProcMeshTangent> Tan;
	float U = 0.f;
	for (int32 Side = 0; Side < 4; ++Side)
	{
		const FVector2D Dir = (Corner[Side + 1] - Corner[Side]).GetSafeNormal();
		const FVector Out = FVector(Dir.Y, -Dir.X, 0.f);
		for (int32 K = 0; K <= N; ++K)
		{
			const FVector2D P = Corner[Side] + (Corner[Side + 1] - Corner[Side]) * ((float)K / N);
			const float Z = SurfaceHeight(Min.X + P.X, Min.Y + P.Y) - 40.f;
			const int32 I0 = V.Num();
			V.Add(FVector(P.X, P.Y, Z)); V.Add(FVector(P.X, P.Y, Z + Height));
			UV.Add(FVector2D(U / 1000.f, 0.f)); UV.Add(FVector2D(U / 1000.f, 1.f));
			Nrm.Add(Out); Nrm.Add(Out);
			if (K > 0) { Tri.Append({ I0 - 2, I0, I0 - 1, I0 - 1, I0, I0 + 1 }); }
			U += Step;
		}
	}
	C->CreateMeshSection_LinearColor(0, V, Tri, Nrm, UV, Col, Tan, false);
	UMaterialInstanceDynamic* M = UMaterialInstanceDynamic::Create(Material, C);
	M->SetScalarParameterValue(TEXT("StartTime"), StartTime);
	C->SetMaterial(0, M);
	FTimerHandle H;
	GetWorldTimerManager().SetTimer(H, FTimerDelegate::CreateWeakLambda(C, [C]() { C->DestroyComponent(); }), Lifetime, false);
}

void ARTCell::BeginPlay()
{
	Super::BeginPlay();
	BuildGround();      // procedural mesh sections are rebuilt (cheap) so collision is always cooked
}

void ARTCell::Destroyed()
{
	for (ARTBuilding* B : Buildings) if (B) B->Destroy();
	for (AActor* A : OtherActors) if (A) A->Destroy();
	Buildings.Reset(); OtherActors.Reset();
	Super::Destroyed();
}
