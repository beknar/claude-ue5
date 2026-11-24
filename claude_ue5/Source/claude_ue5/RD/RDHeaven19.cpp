// The user's list of 2026-11-22 (docs/improvements16.txt, "the city of heaven"; the plan docs/improvements16_plan.md), its nineteenth
// phase, Heaven's streets:
// - the markings: a dashed centre line, edge lines, a zebra crossing and a stop line before every crossing (Heaven.Mark, a unit square
//   of white paint stretched to each line);
// - the traffic lights: our own four-way pole at every signalled crossing (Heaven.Signal19), its lenses instances of one mesh whose
//   colour and light are per-instance data (M_HV_SignalLens): the two roads' phases cycle green, amber, all red;
// - stop signs at every approach to a crossing with no lights, a street-name sign at every crossing, a district sign in each quarter;
// - parked cars: lay-bys cut into the pavement (two tiles, along the street) and small lots (nose in, two tiles deep), asphalt;
// - the medieval things gone from Heaven (the theme's own pieces by name, 946 streets; their fires never lit: RDSection.cpp).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDHeaven19, Log, All);

static TAutoConsoleVariable<int32> CVarRDStreets19(TEXT("rd.Streets19"), 1, TEXT("Heaven's street things (markings, signals, signs, parked cars): 1 shown, 0 hidden (tests: the frame rate with and without them)"));

static const FIntPoint RDH19Dir4[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };

// ------------------------------------------------------------------------------------------------ the signals' phases
int32 ARDDungeonGenerator::SignalPhase19(float T, float Offset, bool bAlongX) const
{
	// (one cycle: the X roads green, amber, all red, then the Y roads the same; 2 green, 1 amber, 0 red)
	const float G = FMath::Max(SignalGreen19, 1.f), A = FMath::Max(SignalAmber19, 0.5f), Rr = FMath::Max(SignalAllRed19, 0.f);
	const float C = 2.f * (G + A + Rr);
	float Tt = FMath::Fmod(T + Offset, C); if (Tt < 0.f) Tt += C;
	const float Half = G + A + Rr;
	const bool bXTurn = Tt < Half;
	const float U = bXTurn ? Tt : Tt - Half;
	const int32 Mine = U < G ? 2 : U < G + A ? 1 : 0;
	return bXTurn == bAlongX ? Mine : 0;
}

void ARDDungeonGenerator::TickSignals19(float Dt)
{
	SignalLook19 -= Dt;
	if (SignalLook19 > 0.f) return;
	SignalLook19 = 0.2f;
	if (TownPlan != 5) return;
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S || S->IsBuilding()) return;
	S->TickSignals19(GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f);
	// (the street things shown or hidden, for the frame-rate test)
	const int32 Show = CVarRDStreets19.GetValueOnGameThread() != 0 ? 1 : 0;
	if (Show != Streets19Shown || S != Streets19Of.Get())
	{
		Streets19Shown = Show; Streets19Of = S;
		static const TCHAR* Names[] = { TEXT("Heaven.Mark"), TEXT("Heaven.Signal19"), TEXT("Heaven.StopSign19"), TEXT("Heaven.StreetSign19"), TEXT("Heaven.DistrictSign19"),
			TEXT("Heaven.Car_1"), TEXT("Heaven.Car_2"), TEXT("Heaven.Car_3"), TEXT("Heaven.Car_4"), TEXT("Heaven.Car_5"), TEXT("Heaven.Car_6") };
		TSet<const UStaticMesh*> Ms;
		for (const TCHAR* N : Names) if (const FRDPiece* P = Piece(N)) if (P->Mesh) Ms.Add(P->Mesh);
		TArray<UActorComponent*> Cs; S->GetComponents(Cs);
		int32 Set = 0;
		for (UActorComponent* C : Cs)
		{
			USceneComponent* Sc = Cast<USceneComponent>(C);
			if (!Sc) continue;
			bool bMine = C->ComponentHasTag(TEXT("HeavenSign19")) || C->ComponentHasTag(TEXT("HeavenSignal19"));
			if (const UInstancedStaticMeshComponent* I = Cast<UInstancedStaticMeshComponent>(C); I && Ms.Contains(I->GetStaticMesh()) && !C->ComponentHasTag(TEXT("HeavenCar"))) bMine = true;
			if (bMine) { Sc->SetVisibility(Show == 1); ++Set; }
		}
		UE_LOG(LogRDHeaven19, Log, TEXT("RDHEAVEN19 street things %s (%d components)"), Show ? TEXT("shown") : TEXT("hidden"), Set);
	}
}

void ARDSection::HeavenSignal19(const FTownSpot& Sp)
{
	// (four faces on the head, each three lenses: the faces along X show the X roads' phase (a car heading -X sees the +X face))
	for (const FSignal19& O : Signals19) if (FVector::Dist2D(O.At, Sp.At) < 10.f) return;          // (built once: a second pass adds nothing)
	FSignal19 Sg; Sg.At = Sp.At;
	Sg.Offset = (float)(HashCombine(GetTypeHash(FIntPoint(FMath::RoundToInt(Sp.At.X), FMath::RoundToInt(Sp.At.Y))), 0x519Au) % 997u) * 0.1f;
	const FRDPiece* Lp = Generator->Piece(TEXT("Heaven.SignalLens19"));
	// (a replan with static building off (RestartPlay's ActivateForPlay) keeps the built lenses: found again, in the same order (PR #126's
	// review: every signal stood at its last phase after a restart))
	if (!bBuildStatic)
	{
		if (!SignalLenses19.IsValid())
			for (UActorComponent* C : GetComponentsByTag(UInstancedStaticMeshComponent::StaticClass(), TEXT("HeavenSignal19"))) { SignalLenses19 = Cast<UInstancedStaticMeshComponent>(C); break; }
		if (const UInstancedStaticMeshComponent* I = SignalLenses19.Get(); I && (Signals19.Num() + 1) * 12 <= I->GetInstanceCount()) Sg.First = Signals19.Num() * 12;
	}
	if (bBuildStatic && Lp && Lp->Mesh)
	{
		UInstancedStaticMeshComponent* I = SignalLenses19.Get();
		if (!I)
		{
			I = NewObject<UInstancedStaticMeshComponent>(this, NAME_None, RF_Transactional);
			I->SetStaticMesh(Lp->Mesh);
			if (Lp->Material) I->SetMaterial(0, Lp->Material);
			I->SetNumCustomDataFloats(4);
			I->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			I->SetCastShadow(false);
			I->SetupAttachment(RootComponent);
			I->ComponentTags.Add(TEXT("HeavenSignal19"));
			I->RegisterComponent();
			AddInstanceComponent(I);
			SignalLenses19 = I;
		}
		static const FLinearColor Col[3] = { FLinearColor(1.f, 0.04f, 0.02f), FLinearColor(1.f, 0.5f, 0.f), FLinearColor(0.08f, 1.f, 0.3f) };
		const float Zs[3] = { Generator->SignalHead19.Z + 30.f, Generator->SignalHead19.Z, Generator->SignalHead19.Z - 30.f };
		static const FVector Faces[4] = { FVector(1, 0, 0), FVector(-1, 0, 0), FVector(0, 1, 0), FVector(0, -1, 0) };
		Sg.First = I->GetInstanceCount();
		for (int32 F = 0; F < 4; ++F)
			for (int32 Cc = 0; Cc < 3; ++Cc)
			{
				const FVector P = Sp.At + Faces[F] * Generator->SignalHead19.X + FVector(0, 0, Zs[Cc]);
				const int32 K = I->AddInstance(FTransform(Faces[F].Rotation(), P), true);
				const float Data[4] = { Col[Cc].R, Col[Cc].G, Col[Cc].B, 0.f };
				I->SetCustomData(K, TArrayView<const float>(Data, 4), false);
			}
		I->MarkRenderStateDirty();
	}
	Signals19.Add(Sg);
}

void ARDSection::TickSignals19(float Now)
{
	UInstancedStaticMeshComponent* I = SignalLenses19.Get();
	bool bDirty = false;
	for (FSignal19& Sg : Signals19)
	{
		const int32 X = Generator->SignalPhase19(Now, Sg.Offset, true), Y = Generator->SignalPhase19(Now, Sg.Offset, false);
		const uint8 Shown = (uint8)(X * 3 + Y);
		if (Shown == Sg.Shown) continue;
		Sg.Shown = Shown;
		if (!I || Sg.First < 0) continue;
		for (int32 F = 0; F < 4; ++F)
		{
			const int32 Ph = F < 2 ? X : Y;
			// (lens 0 red, 1 amber, 2 green; phase 0 red, 1 amber, 2 green)
			for (int32 Cc = 0; Cc < 3; ++Cc)
			{
				const int32 K = Sg.First + F * 3 + Cc;
				if (K < I->GetInstanceCount()) I->SetCustomDataValue(K, 3, (Cc == 0 && Ph == 0) || (Cc == 1 && Ph == 1) || (Cc == 2 && Ph == 2) ? 1.f : 0.f, false);
			}
		}
		bDirty = true;
	}
	if (bDirty && I) I->MarkRenderStateDirty();
}

TArray<FString> ARDSection::GetSignals19() const
{
	// (for the tests: "signals|<n>|<time>", "sig|<i>|<x>|<y>|<x phase>|<y phase>|<lit lenses>|<which>|<x now>|<y now>": the phases the
	// lenses were last set to (the tick sets them five times a second), then the phases at this moment)
	TArray<FString> Out;
	const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	Out.Add(FString::Printf(TEXT("signals|%d|%.2f"), Signals19.Num(), Now));
	const UInstancedStaticMeshComponent* I = SignalLenses19.Get();
	for (int32 K = 0; K < Signals19.Num(); ++K)
	{
		const FSignal19& Sg = Signals19[K];
		int32 Lit = 0;
		FString Which;
		if (I && Sg.First >= 0)
			for (int32 J = 0; J < 12; ++J)
			{
				const int32 Ix = (Sg.First + J) * 4 + 3;
				if (I->PerInstanceSMCustomData.IsValidIndex(Ix) && I->PerInstanceSMCustomData[Ix] > 0.5f) { ++Lit; Which += FString::FromInt(J); Which += TEXT(","); }
			}
		const int32 Sx = Sg.Shown == 255 ? -1 : Sg.Shown / 3, Sy = Sg.Shown == 255 ? -1 : Sg.Shown % 3;
		Out.Add(FString::Printf(TEXT("sig|%d|%.0f|%.0f|%d|%d|%d|%s|%d|%d"), K, Sg.At.X, Sg.At.Y, Sx, Sy, Lit, *Which, Generator->SignalPhase19(Now, Sg.Offset, true), Generator->SignalPhase19(Now, Sg.Offset, false)));
	}
	return Out;
}

// ------------------------------------------------------------------------------------------------ the streets' plan
void ARDSection::HeavenRuns19()
{
	// (each street of the grid between its crossings: a run of tiles along it; its ends at a crossing (both kinds of road over the
	// tile), the square, the facility's forecourt (a road 5 tiles and more each way) or another road beyond its rectangle's end)
	Runs19.Reset(); JGroup19.Init(-1, N * N); Junctions19.Reset();
	TArray<uint8> Ax; Ax.Init(0, N * N);
	for (int32 Ri = 0; Ri < TownRoads.Num(); ++Ri)
	{
		const FIntRect& Rr = TownRoads[Ri];
		const bool bX = Rr.Width() >= Rr.Height(), bPlaza = FMath::Min(Rr.Width(), Rr.Height()) >= 5;
		for (int32 X = Rr.Min.X; X < Rr.Max.X; ++X)
			for (int32 Y = Rr.Min.Y; Y < Rr.Max.Y; ++Y)
				if (In(FIntPoint(X, Y))) Ax[Idx(FIntPoint(X, Y))] |= bPlaza ? 4 : (bX ? 1 : 2);
	}
	auto Junc = [&](const FIntPoint& T) { return In(T) && (((Ax[Idx(T)] & 3) == 3) || (Ax[Idx(T)] & 4) || TownSquare.Contains(T)); };
	auto RoadT = [&](const FIntPoint& T) { return In(T) && (TownRoadMask[Idx(T)] == 1 || TownSquare.Contains(T)); };
	// (the crossings: the junction tiles joined; one that holds the square or a forecourt is a plaza)
	for (int32 Y = 0; Y < N; ++Y)
		for (int32 X = 0; X < N; ++X)
		{
			const FIntPoint T0(X, Y);
			if (!Junc(T0) || JGroup19[Idx(T0)] >= 0) continue;
			FJunction19 Jn; Jn.Min = T0; Jn.Max = T0;
			const int32 Gi = Junctions19.Num();
			TArray<FIntPoint> Q; Q.Add(T0); JGroup19[Idx(T0)] = Gi;
			for (int32 Qi = 0; Qi < Q.Num(); ++Qi)
			{
				const FIntPoint T = Q[Qi];
				Jn.Min = FIntPoint(FMath::Min(Jn.Min.X, T.X), FMath::Min(Jn.Min.Y, T.Y)); Jn.Max = FIntPoint(FMath::Max(Jn.Max.X, T.X), FMath::Max(Jn.Max.Y, T.Y));
				if ((Ax[Idx(T)] & 4) || TownSquare.Contains(T)) Jn.bPlaza = true;
				for (const FIntPoint& D : RDH19Dir4) { const FIntPoint U = T + D; if (Junc(U) && JGroup19[Idx(U)] < 0) { JGroup19[Idx(U)] = Gi; Q.Add(U); } }
			}
			Jn.Mid = (TileWorld(Jn.Min) + TileWorld(Jn.Max)) * 0.5f;
			for (int32 K = 0; K < Signals19.Num(); ++K)
				if (FVector::Dist2D(Signals19[K].At, Jn.Mid) < 300.f * (FMath::Max(Jn.Max.X - Jn.Min.X, Jn.Max.Y - Jn.Min.Y) + 1) * 0.71f + 500.f) { Jn.Signal = K; break; }
			Junctions19.Add(Jn);
		}
	for (int32 Ri = 0; Ri < TownRoads.Num(); ++Ri)
	{
		const FIntRect& Rr = TownRoads[Ri];
		const bool bX = Rr.Width() >= Rr.Height();
		if (FMath::Min(Rr.Width(), Rr.Height()) >= 5 || FMath::Min(Rr.Width(), Rr.Height()) < 2) continue;
		const int32 A0 = bX ? Rr.Min.X : Rr.Min.Y, A1 = bX ? Rr.Max.X : Rr.Max.Y, C0 = bX ? Rr.Min.Y : Rr.Min.X, C1 = bX ? Rr.Max.Y : Rr.Max.X;
		auto Tile = [&](int32 A, int32 C) { return bX ? FIntPoint(A, C) : FIntPoint(C, A); };
		auto ColJ = [&](int32 A) { for (int32 C = C0; C < C1; ++C) if (Junc(Tile(A, C))) return true; return false; };
		const int32 Cm = (C0 + C1) / 2;
		int32 A = A0;
		while (A < A1)
		{
			if (ColJ(A)) { ++A; continue; }
			int32 E = A; while (E < A1 && !ColJ(E)) ++E;
			FRun19 Ru; Ru.Road = Ri; Ru.bX = bX; Ru.S = A; Ru.E = E; Ru.C0 = C0; Ru.C1 = C1;
			const FIntPoint Bs = Tile(A - 1, Cm), Be = Tile(E, Cm);
			Ru.bStartJ = A > A0 || RoadT(Bs); Ru.bEndJ = E < A1 || RoadT(Be);
			Ru.StartJ = In(Bs) ? JGroup19[Idx(Bs)] : -1; Ru.EndJ = In(Be) ? JGroup19[Idx(Be)] : -1;
			Runs19.Add(Ru);
			A = E;
		}
	}
}

bool ARDSection::ParkFree19(const FIntPoint& T) const
{
	if (!In(T) || Type[Idx(T)] != 2 || Owner[Idx(T)] != 1000 || TownRoadMask[Idx(T)] != 0 || TownSquare.Contains(T) || Blocked[Idx(T)] || ParkTiles19.Contains(Idx(T))) return false;
	for (const FTownBld& Tb : TownBlds)
	{
		const FIntPoint O = Tb.DoorTile + RDH19Dir4[Tb.DoorSide];
		if (FMath::Max(FMath::Abs(O.X - T.X), FMath::Abs(O.Y - T.Y)) <= 1 || Tb.DoorTile == T) return false;
	}
	const FVector W = TileWorld(T);
	for (const FTownSpot& Sp : TownSpots) if (FVector::Dist2D(Sp.At, W) < 350.f) return false;
	return true;
}

void ARDSection::HeavenStreets19Plan()
{
	// (before the ground is laid: the crossings and runs, then the parking: on each side of a run, the pavement's row of tiles beside
	// the kerb (two tiles from a crossing's end): free stretches of three tiles or more whose next row is free too are lots, nose in;
	// the rest lay-bys of two tiles along the street. Asphalt under them. No random draws: the plan's streams stay as they were)
	ParkTiles19.Reset(); Parks19.Reset();
	if (!Generator->Piece(TEXT("Heaven.Mark"))) return;
	HeavenRuns19();
	int32 Lots = 0;
	for (int32 RuI = 0; RuI < Runs19.Num(); ++RuI)
	{
		const FRun19& Ru = Runs19[RuI];
		auto Tile = [&](int32 A, int32 C) { return Ru.bX ? FIntPoint(A, C) : FIntPoint(C, A); };
		for (int32 Side = -1; Side <= 1; Side += 2)
		{
			const int32 Ck = Side > 0 ? Ru.C1 : Ru.C0 - 1, Cd = Side > 0 ? Ru.C1 + 1 : Ru.C0 - 2;
			int32 A = Ru.S + 2;
			while (A < Ru.E - 2)
			{
				if (!ParkFree19(Tile(A, Ck))) { ++A; continue; }
				int32 Q = A; while (Q < Ru.E - 2 && ParkFree19(Tile(Q, Ck))) ++Q;
				bool bDeep = Q - A >= 3 && Lots < Generator->HeavenLots19;
				for (int32 K = A; K < Q && bDeep; ++K) if (!ParkFree19(Tile(K, Cd))) bDeep = false;
				if (bDeep)
				{
					FPark19 Pk; Pk.Run = RuI; Pk.Side = Side; Pk.A = A; Pk.B = Q; Pk.bLot = true;
					for (int32 K = A; K < Q; ++K) { ParkTiles19.Add(Idx(Tile(K, Ck))); ParkTiles19.Add(Idx(Tile(K, Cd))); }
					Parks19.Add(Pk); ++Lots;
				}
				else
					for (int32 K = A; K + 1 < Q; K += 2)
					{
						FPark19 Pk; Pk.Run = RuI; Pk.Side = Side; Pk.A = K; Pk.B = K + 2; Pk.bLot = false;
						ParkTiles19.Add(Idx(Tile(K, Ck))); ParkTiles19.Add(Idx(Tile(K + 1, Ck)));
						Parks19.Add(Pk);
					}
				A = Q;
			}
		}
	}
}

// ------------------------------------------------------------------------------------------------ the streets built
void ARDSection::AddText19(const FString& Text, const FTransform& T, float MaxW, float MaxH, const FColor& Col)
{
	if (!bBuildStatic || Text.IsEmpty()) return;
	UTextRenderComponent* Tx = NewObject<UTextRenderComponent>(this, NAME_None, RF_Transactional);
	Tx->SetupAttachment(RootComponent);
	Tx->SetMobility(EComponentMobility::Static);
	Tx->SetText(FText::FromString(Text));
	Tx->SetHorizontalAlignment(EHTA_Center);
	Tx->SetVerticalAlignment(EVRTA_TextCenter);
	Tx->SetWorldSize(10.f);
	const FVector Ls = Tx->GetTextLocalSize();
	Tx->SetWorldSize(10.f * FMath::Min(MaxW / FMath::Max(Ls.Y, 1.f), MaxH / FMath::Max(Ls.Z, 1.f)));
	Tx->SetTextRenderColor(Col);
	Tx->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Tx->ComponentTags.Add(TEXT("HeavenSign19"));
	Tx->LDMaxDrawDistance = 6000.f; Tx->SetCachedMaxDrawDistance(6000.f);          // (words read within 60 m; each is a draw of its own)
	Tx->SetWorldTransform(T);
	Tx->RegisterComponent();
	AddInstanceComponent(Tx);
}

FString ARDSection::StreetName19(int32 Road) const
{
	// (a street's name by its line: the X roads by their place across, from the list's front; the Y roads from its back; one street
	// cut in two by the facility keeps one name)
	const TArray<FString>& Nm = Generator->HeavenStreetNames19;
	if (!TownRoads.IsValidIndex(Road) || Nm.Num() == 0) return FString();
	const FIntRect& R0 = TownRoads[Road];
	const bool bX = R0.Width() >= R0.Height();
	TArray<int32> Lines;
	for (const FIntRect& Rr : TownRoads)
		if ((Rr.Width() >= Rr.Height()) == bX && FMath::Min(Rr.Width(), Rr.Height()) < 5) Lines.AddUnique(bX ? Rr.Min.Y : Rr.Min.X);
	Lines.Sort();
	const int32 K = Lines.IndexOfByKey(bX ? R0.Min.Y : R0.Min.X);
	return bX ? Nm[FMath::Max(K, 0) % Nm.Num()] : Nm[(Nm.Num() - 1 - (FMath::Max(K, 0) % Nm.Num()) + Nm.Num()) % Nm.Num()];
}

void ARDSection::HeavenStreets19Build()
{
	if (!Generator->Piece(TEXT("Heaven.Mark")) || (Runs19.Num() == 0 && Junctions19.Num() == 0)) return;
	const float M = Generator->TileSize;
	Streets19.Reset(); StopLines19.Reset();
	int32 Dashes = 0, Edges = 0, Zebras = 0, Stops = 0, StopSigns = 0, NameSigns = 0, Districts = 0, Parked = 0, Bays = 0, LotsN = 0;
	int32 MarksN = 0;
	auto Mark = [&](const FVector& At, const FVector& Along, float Len, float Wd)
	{
		++MarksN;
		AddPiece(TEXT("Heaven.Mark"), FTransform(Along.Rotation(), At, FVector(Len / 100.f, Wd / 100.f, 1.f)), true);
	};
	auto Open = [&](const FIntPoint& T)
	{
		if (!In(T) || Type[Idx(T)] != 2 || Owner[Idx(T)] != 1000 || TownRoadMask[Idx(T)] != 0 || TownSquare.Contains(T) || Blocked[Idx(T)] || ParkTiles19.Contains(Idx(T))) return false;
		for (const FTownBld& Tb : TownBlds) { const FIntPoint O = Tb.DoorTile + RDH19Dir4[Tb.DoorSide]; if (FMath::Max(FMath::Abs(O.X - T.X), FMath::Abs(O.Y - T.Y)) <= 1) return false; }
		return true;
	};
	TArray<FVector> Placed;          // (the signs' poles: one tile apart at least)
	auto Clear = [&](const FVector& P) { for (const FVector& Q : Placed) if (FVector::Dist2D(P, Q) < 250.f) return false; for (const FTownSpot& Sp : TownSpots) if (FVector::Dist2D(Sp.At, P) < 250.f) return false; return true; };
	TMap<int32, FIntPoint> RoadCounts;          // (per road: dashes, edges | zebra bars, stop lines)
	TMap<int32, FIntPoint> RoadCounts2;
	for (int32 Ri = 0; Ri < Runs19.Num(); ++Ri)
	{
		const FRun19& Ru = Runs19[Ri];
		auto Tile = [&](int32 A, int32 C) { return Ru.bX ? FIntPoint(A, C) : FIntPoint(C, A); };
		const FVector Av = (TileWorld(Tile(Ru.S + 1, Ru.C0)) - TileWorld(Tile(Ru.S, Ru.C0))).GetSafeNormal2D();
		const FVector Cv = (TileWorld(Tile(Ru.S, Ru.C0 + 1)) - TileWorld(Tile(Ru.S, Ru.C0))).GetSafeNormal2D();
		const float Hw = (Ru.C1 - Ru.C0) * M * 0.5f;
		auto Mw = [&](float A) { const FVector P0 = (TileWorld(Tile(Ru.S, Ru.C0)) + TileWorld(Tile(Ru.S, Ru.C1 - 1))) * 0.5f; return P0 + Av * ((A - Ru.S) * M); };
		const int32 Len = Ru.E - Ru.S;
		FIntPoint& Rc = RoadCounts.FindOrAdd(Ru.Road); FIntPoint& Rc2 = RoadCounts2.FindOrAdd(Ru.Road);
		if (Len < 2) continue;
		const bool bZebra = Len >= 4;
		// ---- the centre line: a 3 m dash every other tile, clear of the crossings' last two tiles
		for (int32 A = Ru.S + (Ru.bStartJ ? 2 : 0); A < Ru.E - (Ru.bEndJ ? 2 : 0); ++A)
			if ((A - Ru.S) % 2 == 0) { Mark(Mw(A), Av, 300.f, 15.f); ++Dashes; ++Rc.X; }
		// ---- the edge lines, 40 cm in from each kerb, between the zebras
		{
			const int32 B0 = Ru.S + (Ru.bStartJ && bZebra ? 1 : 0), B1 = Ru.E - (Ru.bEndJ && bZebra ? 1 : 0);
			if (B1 > B0)
				for (int32 Sd = -1; Sd <= 1; Sd += 2)
				{
					Mark((Mw(B0) + Mw(B1 - 1)) * 0.5f + Cv * (Sd * (Hw - 40.f)), Av, (B1 - B0) * M, 12.f);
					++Edges; ++Rc.Y;
				}
		}
		// ---- each end at a crossing: the zebra in its last tile, the stop line before it across the lane coming in, a stop sign at that
		// lane's kerb where the crossing has no lights
		for (int32 End = 0; End < 2; ++End)
		{
			const bool bJ = End == 0 ? Ru.bStartJ : Ru.bEndJ;
			if (!bJ) continue;
			const int32 Gi = End == 0 ? Ru.StartJ : Ru.EndJ;
			const FJunction19* Jn = Junctions19.IsValidIndex(Gi) ? &Junctions19[Gi] : nullptr;
			const bool bPlaza = Jn && Jn->bPlaza;
			const int32 Zc = End == 0 ? Ru.S : Ru.E - 1;
			const FVector Way = End == 0 ? -Av : Av;          // (the way the incoming lane drives)
			const FVector Right(-Way.Y, Way.X, 0.f);
			if (bZebra)
			{
				// (50 cm bars 100 cm apart across the street, 40 cm clear of each kerb, even about its middle)
				const int32 Nb = FMath::Max(1, FMath::FloorToInt((2.f * Hw - 80.f) / 100.f));
				for (int32 Bk = 0; Bk < Nb; ++Bk) { Mark(Mw(Zc) + Cv * ((Bk - (Nb - 1) * 0.5f) * 100.f), Av, 250.f, 50.f); ++Zebras; ++Rc2.X; }
			}
			if (bPlaza) continue;
			const FVector Edge = Mw(Zc) - Way * (bZebra ? 150.f + 30.f : -(150.f - 30.f));
			const FVector Sl = Edge + Right * ((15.f + Hw - 40.f) * 0.5f);
			Mark(Sl, Av, 40.f, Hw - 55.f);
			// (a mark stretched across: its X along the way, its Y across: 40 cm deep, the lane wide)
			++Stops; ++Rc2.Y;
			FStop19 St; St.At = Edge + Right * 220.f; St.Way = Way; St.Signal = Jn ? Jn->Signal : -1; St.bAlongX = Ru.bX;
			StopLines19.Add(St);
			if (!Jn || Jn->Signal < 0)
			{
				// (the kerb's tile on the incoming lane's right, beside the zebra's tile, or one or two further back (the first test: the
				// four approaches with no lights all had their kerb's tile taken))
				const int32 Cs = (Right | Cv) > 0.f ? Ru.C1 : Ru.C0 - 1;
				FIntPoint Pt(-1, -1); FVector P = FVector::ZeroVector;
				for (int32 Back = 0; Back <= 2 && Pt.X < 0; ++Back)
				{
					const int32 Za = End == 0 ? Zc + Back : Zc - Back;
					if (Za < Ru.S || Za >= Ru.E) break;
					const FIntPoint Tq = Tile(Za, Cs); const FVector Pq = TileWorld(Tq) - Right * 100.f;
					if (Open(Tq) && Clear(Pq)) { Pt = Tq; P = Pq; }
				}
				if (Pt.X >= 0 && Generator->Piece(TEXT("Heaven.StopSign19")))
				{
					AddPieceAt(TEXT("Heaven.StopSign19"), P, (-Way).Rotation().Yaw);
					AddText19(TEXT("STOP"), FTransform((-Way).Rotation(), P + (-Way) * 2.8f + FVector(0, 0, Generator->StopSignFace19)), 52.f, 20.f, FColor::White);
					MarkBlocked(P, 0.f, FVector2D(40.f, 40.f), true);
					Placed.Add(P); ++StopSigns;
					Streets19.Add(FString::Printf(TEXT("stopsign|%.0f|%.0f|%.0f"), P.X, P.Y, (-Way).Rotation().Yaw));
				}
			}
		}
	}
	// ---- the street names: a pole at a corner of each crossing of two streets, a blade along each
	TArray<int32> Quarter = { -1, -1, -1, -1 };
	const FVector SqMid = (TileWorld(TownSquare.Min) + TileWorld(TownSquare.Max - FIntPoint(1, 1))) * 0.5f;
	for (int32 Gi = 0; Gi < Junctions19.Num(); ++Gi)
	{
		FJunction19& Jn = Junctions19[Gi];
		if (Jn.bPlaza) continue;
		int32 RX = -1, RY = -1;
		for (int32 Ri = 0; Ri < TownRoads.Num(); ++Ri)
		{
			const FIntRect& Rr = TownRoads[Ri];
			if (FMath::Min(Rr.Width(), Rr.Height()) >= 5 || !Rr.Contains(Jn.Min)) continue;
			if (Rr.Width() >= Rr.Height()) RX = Ri; else RY = Ri;
		}
		if (RX < 0 || RY < 0) continue;
		Jn.NameX = StreetName19(RX); Jn.NameY = StreetName19(RY);
		// (the district's sign at the crossing nearest the square in each quarter)
		const int32 Qd = (Jn.Mid.X >= SqMid.X ? 1 : 0) + (Jn.Mid.Y >= SqMid.Y ? 2 : 0);
		if (Quarter[Qd] < 0 || FVector::Dist2D(Jn.Mid, SqMid) < FVector::Dist2D(Junctions19[Quarter[Qd]].Mid, SqMid)) Quarter[Qd] = Gi;
		if (!Generator->Piece(TEXT("Heaven.StreetSign19"))) continue;
		const FIntPoint Cn[4] = { Jn.Min - FIntPoint(1, 1), Jn.Max + FIntPoint(1, 1), FIntPoint(Jn.Min.X - 1, Jn.Max.Y + 1), FIntPoint(Jn.Max.X + 1, Jn.Min.Y - 1) };
		for (const FIntPoint& T : Cn)
		{
			const FVector Tw = TileWorld(T);
			const FVector To = Jn.Mid - Tw;
			const FVector P = Tw + FVector(FMath::Sign(To.X), FMath::Sign(To.Y), 0.f) * 100.f;
			if (!Open(T) || !Clear(P)) continue;
			const int32 Sx = To.X >= 0.f ? 1 : -1, Sy = To.Y >= 0.f ? 1 : -1;
			const float Yaw = Sx > 0 && Sy > 0 ? 0.f : Sx < 0 && Sy > 0 ? 90.f : Sx < 0 && Sy < 0 ? 180.f : -90.f;
			AddPieceAt(TEXT("Heaven.StreetSign19"), P, Yaw);
			const FRotator Rt(0, Yaw, 0);
			// (each blade's words on both its faces; a blade along world X names the X road)
			const FVector BX = Rt.RotateVector(FVector(1, 0, 0)), BY = Rt.RotateVector(FVector(0, 1, 0));
			const FString& NmBX = FMath::Abs(BX.X) > 0.5f ? Jn.NameX : Jn.NameY;
			const FString& NmBY = FMath::Abs(BY.X) > 0.5f ? Jn.NameX : Jn.NameY;
			const FVector& BL = Generator->StreetBlade19;          // (blade x: its middle along, its height; blade y: the second height)
			for (int32 Sd = -1; Sd <= 1; Sd += 2)
			{
				AddText19(NmBX, FTransform(FRotator(0, Yaw + Sd * 90.f, 0), P + Rt.RotateVector(FVector(BL.X, Sd * 2.8f, BL.Y))), 118.f, 15.f, FColor::White);
				AddText19(NmBY, FTransform(FRotator(0, Yaw + (Sd > 0 ? 0.f : 180.f), 0), P + Rt.RotateVector(FVector(Sd * 2.8f, BL.X, BL.Z))), 118.f, 15.f, FColor::White);
			}
			MarkBlocked(P, 0.f, FVector2D(40.f, 40.f), true);
			Placed.Add(P); ++NameSigns;
			Streets19.Add(FString::Printf(TEXT("namesign|%.0f|%.0f|%s|%s"), P.X, P.Y, *Jn.NameX, *Jn.NameY));
			break;
		}
	}
	// ---- the districts: a board at the crossing nearest the square in each quarter (a free corner)
	for (int32 Qd = 0; Qd < 4; ++Qd)
	{
		if (Quarter[Qd] < 0 || !Generator->HeavenDistrictNames19.IsValidIndex(Qd) || !Generator->Piece(TEXT("Heaven.DistrictSign19"))) continue;
		const FJunction19& Jn = Junctions19[Quarter[Qd]];
		const FIntPoint Cn[4] = { Jn.Max + FIntPoint(1, 1), Jn.Min - FIntPoint(1, 1), FIntPoint(Jn.Min.X - 1, Jn.Max.Y + 1), FIntPoint(Jn.Max.X + 1, Jn.Min.Y - 1) };
		for (const FIntPoint& T : Cn)
		{
			const FVector P = TileWorld(T);
			if (!Open(T) || !Clear(P)) continue;
			const float Yaw = (Jn.Mid - P).Rotation().Yaw;
			AddPieceAt(TEXT("Heaven.DistrictSign19"), P, Yaw);
			const FString Words = Generator->HeavenDistrictNames19[Qd] + TEXT(" DISTRICT");
			for (int32 Sd = -1; Sd <= 1; Sd += 2)
				AddText19(Words, FTransform(FRotator(0, Yaw + (Sd > 0 ? 0.f : 180.f), 0), P + FRotator(0, Yaw, 0).RotateVector(FVector(Sd * 5.f, 0, Generator->DistrictFace19))), 260.f, 46.f, FColor::White);
			MarkBlocked(P, Yaw, FVector2D(40.f, 320.f), true);
			Placed.Add(P); ++Districts;
			Streets19.Add(FString::Printf(TEXT("district|%.0f|%.0f|%s"), P.X, P.Y, *Words));
			break;
		}
	}
	// ---- the parked cars: one in three quarters of the lay-bys (along the street, heading as that side's lane), two thirds of the lots'
	// bays (nose in); the bays' lines
	TSet<FIntPoint> BayEnds;
	TArray<FName> Kinds;
	// (only what fits a 6 m bay: the traffic's bus (12.4 m) parked nose in stood half across the street (the first pictures))
	for (int32 K = 1; K <= 6; ++K) { const FName Nk(*FString::Printf(TEXT("Heaven.Car_%d"), K)); if (const FRDPiece* P = Generator->Piece(Nk)) if (P->Mesh && P->Size.X <= 2.f * M - 20.f) Kinds.Add(Nk); }
	for (const FPark19& Pk : Parks19)
	{
		const FRun19& Ru = Runs19[Pk.Run];
		auto Tile = [&](int32 A, int32 C) { return Ru.bX ? FIntPoint(A, C) : FIntPoint(C, A); };
		const FVector Av = (TileWorld(Tile(Ru.S + 1, Ru.C0)) - TileWorld(Tile(Ru.S, Ru.C0))).GetSafeNormal2D();
		const FVector Cv = (TileWorld(Tile(Ru.S, Ru.C0 + 1)) - TileWorld(Tile(Ru.S, Ru.C0))).GetSafeNormal2D();
		const FVector Rp(-Av.Y, Av.X, 0.f);          // (the right of +Av: that side's lane heads +Av)
		const int32 Ck = Pk.Side > 0 ? Ru.C1 : Ru.C0 - 1, Cd = Pk.Side > 0 ? Ru.C1 + 1 : Ru.C0 - 2;
		const FVector Out = Cv * (float)Pk.Side;          // (from the street out across the pavement)
		if (!Pk.bLot)
		{
			const FVector C = (TileWorld(Tile(Pk.A, Ck)) + TileWorld(Tile(Pk.A + 1, Ck))) * 0.5f;
			const FVector Hd = (Out | Rp) > 0.f ? Av : -Av;          // (the right side of +Av heads +Av)
			// (a bay's end lines; one shared with the bay before it is drawn once)
			for (int32 E = 0; E < 2; ++E)
			{
				const FVector Lp = C + Av * (E == 0 ? -M : M) - Out * 10.f;
				const FIntPoint Key(FMath::RoundToInt(Lp.X / 10.f), FMath::RoundToInt(Lp.Y / 10.f));
				if (BayEnds.Contains(Key)) continue;
				BayEnds.Add(Key); Mark(Lp, Av, 12.f, 240.f);
			}
			++Bays;
			const uint32 Hh = HashCombine(GetTypeHash(Tile(Pk.A, Ck)), 0xCA75u);
			if (Kinds.Num() && Hh % 100u < 75u)
			{
				const FName Nm = Kinds[(Hh >> 8) % (uint32)Kinds.Num()];
				const FRDPiece* P = Generator->Piece(Nm);
				AddPieceAt(Nm, C, Hd.Rotation().Yaw);
				MarkBlocked(C, Hd.Rotation().Yaw, FVector2D(P->Size.X + 20.f, P->Size.Y + 20.f), true);
				++Parked;
				Streets19.Add(FString::Printf(TEXT("car|%.0f|%.0f|%.0f|0|%.0f|%.0f"), C.X, C.Y, Hd.Rotation().Yaw, P->Size.X, P->Size.Y));
			}
		}
		else
		{
			++LotsN;
			for (int32 A = Pk.A; A <= Pk.B; ++A)
			{
				const FVector Bd = (TileWorld(Tile(A, Ck)) + TileWorld(Tile(A, Cd))) * 0.5f - Av * (M * 0.5f);
				Mark(Bd + Out * 10.f, Out, 560.f, 12.f);
			}
			for (int32 A = Pk.A; A < Pk.B; ++A)
			{
				const FVector C = (TileWorld(Tile(A, Ck)) + TileWorld(Tile(A, Cd))) * 0.5f;
				++Bays;
				const uint32 Hh = HashCombine(GetTypeHash(Tile(A, Ck)), 0x7075u);
				if (!Kinds.Num() || Hh % 100u >= 67u) continue;
				const FName Nm = Kinds[(Hh >> 8) % (uint32)Kinds.Num()];
				const FRDPiece* P = Generator->Piece(Nm);
				AddPieceAt(Nm, C, Out.Rotation().Yaw);
				MarkBlocked(C, Out.Rotation().Yaw, FVector2D(P->Size.X + 20.f, P->Size.Y + 20.f), true);
				++Parked;
				Streets19.Add(FString::Printf(TEXT("car|%.0f|%.0f|%.0f|1|%.0f|%.0f"), C.X, C.Y, Out.Rotation().Yaw, P->Size.X, P->Size.Y));
			}
		}
	}
	for (const TPair<int32, FIntPoint>& Kv : RoadCounts)
	{
		const FIntRect& Rr = TownRoads[Kv.Key];
		const FIntPoint Z2 = RoadCounts2.FindRef(Kv.Key);
		Streets19.Add(FString::Printf(TEXT("road|%d|%s|%d|%d|%d|%d|%d|%s"), Kv.Key, Rr.Width() >= Rr.Height() ? TEXT("x") : TEXT("y"), FMath::Max(Rr.Width(), Rr.Height()),
			Kv.Value.X, Kv.Value.Y, Z2.X, Z2.Y, *StreetName19(Kv.Key)));
	}
	int32 Crossings = 0, Signalled = 0;
	for (const FJunction19& Jn : Junctions19)
	{
		if (Jn.bPlaza) continue;
		++Crossings; if (Jn.Signal >= 0) ++Signalled;
		Streets19.Add(FString::Printf(TEXT("junction|%.0f|%.0f|%d|%d|%d"), Jn.Mid.X, Jn.Mid.Y, Jn.Signal, Jn.Max.X - Jn.Min.X + 1, Jn.Max.Y - Jn.Min.Y + 1));
	}
	Streets19.Append(YardLines19);
	for (const FStop19& St : StopLines19) Streets19.Add(FString::Printf(TEXT("stopline|%.0f|%.0f|%.0f|%.0f|%d"), St.At.X, St.At.Y, St.Way.X, St.Way.Y, St.Signal));
	Streets19.Insert(FString::Printf(TEXT("streets|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d"), Runs19.Num(), Dashes, Edges, Zebras, Stops, StopSigns, NameSigns, Districts,
		Crossings, Signalled, Parked, Bays, LotsN, Signals19.Num(), MarksN), 0);
	UE_LOG(LogRDHeaven19, Log, TEXT("RDHEAVEN19 streets: %d runs, %d dashes, %d edge lines, %d zebra bars, %d stop lines, %d stop signs, %d name signs, %d district signs; %d crossings (%d with lights), %d cars parked in %d bays (%d lots)"),
		Runs19.Num(), Dashes, Edges, Zebras, Stops, StopSigns, NameSigns, Districts, Crossings, Signalled, Parked, Bays, LotsN);
}

TArray<FString> ARDSection::GetHeavenStreets19() const { return Streets19; }
