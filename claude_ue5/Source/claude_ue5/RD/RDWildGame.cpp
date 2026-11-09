// The wilderness in play (RDWild.h; the user's spec of 2026-11-03, docs/wilderness.txt): the world made from its seed on a
// worker thread once play begins, the chunks round her asked for nearest first and computed on worker threads, made into
// actors a few a frame, dropped when their middle is more than WildDropM off on an axis (the spec's 2 km square: nothing
// else of the terrain is kept), the grass and the trees' collision only round her; the map's fog lifted round her and the
// places she comes to found.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDWildChunkData.h"
#include "RD/RDSection.h"
#include "RD/RDCombat.h"
#include "RD/RDGameInstance.h"
#include "ProceduralMeshComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Async/Async.h"
#include "Engine/Engine.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "Async/ParallelFor.h"
#include "ImageUtils.h"
#include "Misc/FileHelper.h"
#include "HAL/PlatformTime.h"
#include "RenderTimer.h"
#include "DynamicRHI.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDWild, Log, All);

namespace
{
	constexpr double RDWRevealCellM = 50.0;
	constexpr int32 RDWRevealBlock = 32;
}

bool ARDDungeonGenerator::IsWildReady() const
{
	return Wild.IsValid() && WildStream.IsValid() && WildStream->Init.IsValid() && WildStream->Init.IsReady() && Wild->bReady;
}

void ARDDungeonGenerator::StartWild()
{
	if (Wild.IsValid()) return;
	Wild = MakeShared<FRDWildWorld, ESPMode::ThreadSafe>();
	WildStream = MakeShared<FRDWStream, ESPMode::ThreadSafe>();
	uint32 Seed = (uint32)(WildSeedFixed != 0 ? WildSeedFixed : StartSeed);
	if (WildSeedFixed == 0) if (const uint32 Gs = WildGameSeed(); Gs != 0) Seed = Gs;
	// (Brokenspire's gate, when its section is there: the roads leave by it)
	if (ARDSection* S = GetSection(FIntPoint::ZeroValue); S && !S->TownGateOut.IsNearlyZero())
	{
		const FVector2D G(S->TownGate.X / 100.0, S->TownGate.Y / 100.0), O = FVector2D(S->TownGateOut.X, S->TownGateOut.Y).GetSafeNormal();
		const double Half = SectionTiles * TileSize / 200.0;
		double T = 1e9;
		if (FMath::Abs(O.X) > 1e-3) T = FMath::Min(T, (Half - FMath::Sign(O.X) * G.X) / FMath::Abs(O.X));
		if (FMath::Abs(O.Y) > 1e-3) T = FMath::Min(T, (Half - FMath::Sign(O.Y) * G.Y) / FMath::Abs(O.Y));
		Wild->GateOut.Add(0, G + O * (FMath::Max(T, 0.0) + 20.0));
	}
	// (the home town as the level has it; the map and places she has found this game)
	HomeTownSeed = StartSeed; HomeSectionTiles = SectionTiles; HomeTownName = TownName;
	WildTownIdx = GetSection(FIntPoint::ZeroValue) ? 0 : -1; bTownHome = true;
	if (const URDGameInstance* GI = URDGameInstance::Of(this))
	{
		for (int32 K = 0; K < GI->WildRevealKeys.Num(); ++K)
		{
			TArray<uint64>& Bits = WildRevealed.FindOrAdd(GI->WildRevealKeys[K]); Bits.SetNumZeroed(16);
			for (int32 Q = 0; Q < 16 && GI->WildRevealBits.IsValidIndex(K * 16 + Q); ++Q)
			{
				Bits[Q] = (uint64)GI->WildRevealBits[K * 16 + Q];
				const int32 Nb = FMath::CountBits64(Bits[Q]); WildRevealedCells += Nb; WildRevealCount.FindOrAdd(GI->WildRevealKeys[K]) += Nb;
			}
		}
		for (const int32 Id : GI->WildFound) WildFound.Add(Id);
	}
	if (WildFound.Num() == 0) WildFound.Add(FRDWildWorld::TownIdBase);      // (Brokenspire: known from the start)
	TSharedPtr<FRDWildWorld, ESPMode::ThreadSafe> W = Wild;
	const TArray<FRDWildBiome> Biomes = WildBiomes;
	WildStream->Init = Async(EAsyncExecution::Thread, [W, Biomes, Seed]() { W->Init(Seed, Biomes); });
	UE_LOG(LogRDWild, Log, TEXT("RDWILD the world asked for (seed %u, %d biomes)"), Seed, Biomes.Num());
}

void ARDDungeonGenerator::TickWild(float Dt, APlayerController* PC)
{
	++WildTicks;
	if (!Wild.IsValid()) StartWild();
	if (!IsWildReady()) return;
	if (!bWildMadeLogged) { bWildMadeLogged = true; UE_LOG(LogRDWild, Log, TEXT("RDWILD the world made in %.2f s: %d rivers, %d lakes, %d roads, %d biome cells"), Wild->InitSeconds, Wild->Rivers.Num(), Wild->Lakes.Num(), Wild->Roads.Num(), Wild->CellBiome.Num()); }
	TickWildLoad();
	APawn* P = PC ? PC->GetPawn() : nullptr;
	if (!P) return;
	TickWildRunSpeed(P);          // (the list of 2026-11-07: rd.WildRunSpeed)
	const FVector L = P->GetActorLocation();
	const double Xm = L.X / 100.0, Ym = L.Y / 100.0, Cm = WildChunkM;
	// (every two minutes the map has grown: an autosave)
	if (WildRevealVersion != LastSaveReveal && GetWorld()->GetTimeSeconds() - LastSaveTime > 120.f) WildAutosave(TEXT("map"));
	// ---- the far chunks dropped
	for (auto It = WildChunks.CreateIterator(); It; ++It)
	{
		const double Cx = (It->Key.X + 0.5) * Cm, Cy = (It->Key.Y + 0.5) * Cm;
		if (FMath::Abs(Cx - Xm) > WildDropM || FMath::Abs(Cy - Ym) > WildDropM)
		{
			if (It->Value) It->Value->Destroy();
			WildKept.Remove(It->Key); It.RemoveCurrent(); ++WildDropped;
		}
	}
	// ---- the missing ones asked for, nearest first
	auto Making = [this](const FIntPoint& C) { for (const FWildBuild& B : WildBuilding) if (B.D.IsValid() && B.D->Coord == C) return true; return false; };
	TTuple<double, FIntPoint> Want[256]; int32 Nw = 0;
	const int32 I0 = FMath::FloorToInt((Xm - WildActiveM) / Cm), I1 = FMath::FloorToInt((Xm + WildActiveM) / Cm);
	const int32 J0 = FMath::FloorToInt((Ym - WildActiveM) / Cm), J1 = FMath::FloorToInt((Ym + WildActiveM) / Cm);
	for (int32 I = I0; I <= I1; ++I)
		for (int32 J = J0; J <= J1; ++J)
		{
			const double Cx = (I + 0.5) * Cm, Cy = (J + 0.5) * Cm;
			if (FMath::Abs(Cx - Xm) > WildActiveM || FMath::Abs(Cy - Ym) > WildActiveM) continue;
			const FIntPoint C(I, J);
			if (WildChunks.Contains(C) || WildInFlight.Contains(C) || Nw >= 256 || Making(C)) continue;
			Want[Nw++] = MakeTuple(FMath::Square(Cx - Xm) + FMath::Square(Cy - Ym), C);
		}
	Algo::Sort(TArrayView<TTuple<double, FIntPoint>>(Want, Nw), [](const auto& A, const auto& B) { return A.template Get<0>() < B.template Get<0>(); });
	for (int32 K = 0; K < Nw && WildInFlight.Num() < WildMaxInFlight; ++K) AskWildChunk(Want[K].Get<1>());
	// ---- the computed ones made, within the frame's budget: in steps (2026-11-07: a chunk made in one go took 45 to 72 ms of
	// a frame), the ones begun first, nearest first; at least one step a frame
	const double T0 = FPlatformTime::Seconds();
	auto Spent = [T0]() { return (FPlatformTime::Seconds() - T0) * 1000.0; };
	int32 Steps = 0;
	TSharedPtr<FRDWChunkData, ESPMode::ThreadSafe> D;
	while (WildStream->Done.Dequeue(D))
	{
		WildInFlight.Remove(D->Coord);
		if (WildStale.Remove(D->Coord) > 0) continue;          // (asked before a town came or went: asked again)
		WildComputeMs = WildComputeMs <= 0.0 ? D->Ms : FMath::Lerp(WildComputeMs, D->Ms, 0.1);
		const double Cx = (D->Coord.X + 0.5) * Cm, Cy = (D->Coord.Y + 0.5) * Cm;
		if (WildChunks.Contains(D->Coord) || Making(D->Coord) || FMath::Abs(Cx - Xm) > WildDropM || FMath::Abs(Cy - Ym) > WildDropM) continue;
		// (the old way, kept for the test's comparison: each chunk in one go, as many as the budget lets begin)
		if (!bWildBuildSteps && (Steps == 0 || Spent() <= WildBuildBudgetMs)) { BuildWildChunk(D, true); ++Steps; continue; }
		FWildBuild B; B.D = D; WildBuilding.Add(MoveTemp(B));
	}
	if (WildBuilding.Num() > 0 && (Steps == 0 || Spent() <= WildBuildBudgetMs))
	{
		// (those begun first; of the rest the nearest)
		WildBuilding.StableSort([Xm, Ym, Cm](const FWildBuild& A, const FWildBuild& B)
		{
			if ((A.Step > 0) != (B.Step > 0)) return A.Step > 0;
			auto D2 = [&](const FWildBuild& W) { return FMath::Square((W.D->Coord.X + 0.5) * Cm - Xm) + FMath::Square((W.D->Coord.Y + 0.5) * Cm - Ym); };
			return D2(A) < D2(B);
		});
		while (WildBuilding.Num() > 0)
		{
			if (Steps > 0 && Spent() > WildBuildBudgetMs) break;
			FWildBuild& B = WildBuilding[0];
			const double Cx = (B.D->Coord.X + 0.5) * Cm, Cy = (B.D->Coord.Y + 0.5) * Cm;
			// (dropped while being made, or gone far before it began)
			if ((B.Step > 0 && !B.C.IsValid()) || (B.Step == 0 && (WildChunks.Contains(B.D->Coord) || FMath::Abs(Cx - Xm) > WildDropM || FMath::Abs(Cy - Ym) > WildDropM)))
			{
				WildBuilding.RemoveAt(0); continue;
			}
			if (!bWildBuildSteps) { const TSharedPtr<FRDWChunkData, ESPMode::ThreadSafe> Bd = B.D; WildBuilding.RemoveAt(0); BuildWildChunk(Bd, true); }
			else if (StepWildBuild(B)) WildBuilding.RemoveAt(0);
			++Steps;
		}
	}
	if (Steps > 0) { WildFrameBuildMsMax = FMath::Max(WildFrameBuildMsMax, Spent()); ++WildMakeFrames; }
	WildMaxActive = FMath::Max(WildMaxActive, WildChunks.Num());
	// ---- the chunks round her: grass, the trees' collision
	for (auto& Kv : WildChunks)
	{
		ARDWildChunk* C = Kv.Value; if (!C || C->bMaking) continue;
		const double X0 = Kv.Key.X * Cm, Y0 = Kv.Key.Y * Cm;
		const double Ex = FMath::Max3(X0 - Xm, 0.0, Xm - (X0 + Cm)), Ey = FMath::Max3(Y0 - Ym, 0.0, Ym - (Y0 + Cm));
		SetWildNear(C, FMath::Sqrt(Ex * Ex + Ey * Ey) < WildNearM);
	}
	// ---- the map's fog lifted round her; the places she comes to found (four times a second)
	WildLookTimer -= Dt;
	if (WildLookTimer <= 0.f)
	{
		WildLookTimer = 0.25f;
		RevealWild(FVector2D(Xm, Ym), WildRevealM);
		TickWildPlaces(FVector2D(Xm, Ym));
		TickWildQuests(FVector2D(Xm, Ym));
	}
	TickWildTowns(FVector2D(Xm, Ym));
	TickWildMap(Dt);
	// (the map's tiles round her at the zoom it opens at, made ahead: opened, the map shows them at once)
	WildMapWarmTimer -= Dt;
	if (WildMapWarmTimer <= 0.f && !bMapOpen)
	{
		WildMapWarmTimer = 2.f;
		const int32 Lv = WildMapLevelFor(WildMapOpenMpp); const double Sp = WildMapTileSpan(Lv);
		const int32 Ti = FMath::FloorToInt((Xm - Wild->Xs) / Sp), Tj = FMath::FloorToInt((Ym - Wild->Yw) / Sp);
		for (int32 I = Ti - 1; I <= Ti + 1; ++I) for (int32 J = Tj - 1; J <= Tj + 1; ++J) WildMapTile(Lv, I, J, true);
		WildMapTile(3, FMath::FloorToInt((Xm - Wild->Xs) / WildMapTileSpan(3)), FMath::FloorToInt((Ym - Wild->Yw) / WildMapTileSpan(3)), true);
	}
	// (what dropped chunks held back to the system: after a big drop at once, else once a minute while walking)
	const double Now = FPlatformTime::Seconds();
	if (!bWildTrimPending && WildDropped - WildDroppedAtTrim >= 40 && Now - WildLastTrim > 60.0) WildAskTrim();
	if (bWildTrimPending)
	{
		if (WildTrimAt < 0.0) { GEngine->ForceGarbageCollection(true); WildTrimAt = Now + 1.5; }
		else if (Now >= WildTrimAt)
		{
			FMemory::Trim(true);
			bWildTrimPending = false; WildLastTrim = Now; WildDroppedAtTrim = WildDropped; ++WildTrims;
		}
	}
}

void ARDDungeonGenerator::AskWildChunk(FIntPoint C)
{
	TSharedPtr<FRDWChunkData, ESPMode::ThreadSafe> D = MakeShared<FRDWChunkData, ESPMode::ThreadSafe>();
	D->Coord = C; D->ChunkM = WildChunkM; D->StepM = WildStepM; D->Ticket = ++WildTicket;
	// (the list of 2026-11-07: run fast (rd.WildRunSpeed over 1) she outruns a worker's cooking: the ground's collision at once)
	D->bSyncCollision = WildRunApplied > 1.f;
	WildTownHole(*D);
	WildInFlight.Add(C);
	TSharedPtr<FRDWildWorld, ESPMode::ThreadSafe> W = Wild;
	TSharedPtr<FRDWStream, ESPMode::ThreadSafe> St = WildStream;
	Async(EAsyncExecution::ThreadPool, [W, St, D]() { RDWildComputeChunk(*W, *D); St->Done.Enqueue(D); });
}

void ARDDungeonGenerator::BuildWildChunk(const TSharedPtr<FRDWChunkData, ESPMode::ThreadSafe>& D, bool /*bStreamed*/)
{
	FWildBuild B; B.D = D;
	while (!StepWildBuild(B)) if (B.Step > 0 && !B.C.IsValid()) return;
}

bool ARDDungeonGenerator::StepWildBuild(FWildBuild& B)
{
	// one part of a chunk's making a call: 0 the actor and its ground as it is seen, 1 the ground's collision (a hidden mesh
	// of its own, cooked on a worker unless she is put on it: the two together were 11 ms of a frame, s2), 2 the water, 3 the
	// wading floor, 4 the plants and rocks (up to RDWInstStep instances of one table entry a call; those round her only, the
	// grass and flowers, wait for SetWildNear), 5 the places and the steam
	constexpr int32 RDWInstStep = 2500;
	const double T0 = FPlatformTime::Seconds();
	FRDWChunkData* D = B.D.Get();
	const TCHAR* Part = TEXT("ground");
	bool bDone = false;
	if (B.Step == 0)
	{
		FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		const FVector O(D->Coord.X * WildChunkM * 100.0, D->Coord.Y * WildChunkM * 100.0, 0.0);
		ARDWildChunk* C = GetWorld()->SpawnActor<ARDWildChunk>(ARDWildChunk::StaticClass(), FTransform(O), Sp);
		if (!C) return true;
		C->Coord = D->Coord; C->bMaking = true;
		C->Ground->CreateMeshSection_LinearColor(0, D->V, D->T, D->N, D->UV0, D->UV1, D->UV2, D->UV3, D->C, D->Tan, false);
		if (WildGroundMaterial) C->Ground->SetMaterial(0, WildGroundMaterial);
		C->Triangles = D->T.Num() / 3;
		// (what only the drawn ground needed goes now; the positions and triangles wait for its collision)
		D->N.Empty(); D->Tan.Empty(); D->UV0.Empty(); D->UV1.Empty(); D->UV2.Empty(); D->UV3.Empty(); D->C.Empty(); D->Slope.Empty();
		B.C = C; B.Step = 1;
		WildChunks.Add(D->Coord, C);
	}
	else if (!B.C.IsValid()) return true;
	else if (B.Step == 1)
	{
		Part = TEXT("collision");
		ARDWildChunk* C = B.C.Get();
		// (she, the monsters, the camera and the traces stand on it as on the ground before: BlockAll, hidden, not in the scene)
		UProceduralMeshComponent* G = NewObject<UProceduralMeshComponent>(C, TEXT("GroundCollision"));
		G->SetupAttachment(C->Ground);
		G->bUseAsyncCooking = !D->bSyncCollision;
		G->SetCollisionProfileName(TEXT("BlockAll"));
		G->SetHiddenInGame(true); G->SetVisibility(false); G->SetCastShadow(false);
		G->RegisterComponent();
		G->CreateMeshSection(0, D->V, D->T, TArray<FVector>(), TArray<FVector2D>(), TArray<FColor>(), TArray<FProcMeshTangent>(), true);
		C->GroundCollision = G;
		D->V.Empty(); D->T.Empty();
		B.Step = 2;
	}
	else if (B.Step == 2)
	{
		Part = TEXT("water");
		ARDWildChunk* C = B.C.Get();
		UMaterialInterface* Wm[4] = { WildWaterMaterial, WildSeaMaterial ? WildSeaMaterial.Get() : WildWaterMaterial.Get(), WildSpringMaterial ? WildSpringMaterial.Get() : WildWaterMaterial.Get(), WildLavaMaterial };
		for (int32 S = 0; S < 4; ++S)
		{
			FRDWChunkData::FWater& Wt = D->Water[S];
			if (Wt.V.Num() == 0) continue;
			TArray<FVector> Up; Up.Init(FVector::UpVector, Wt.V.Num());
			C->WaterMesh->CreateMeshSection_LinearColor(S, Wt.V, Wt.T, Up, Wt.UV, TArray<FVector2D>(), TArray<FVector2D>(), TArray<FVector2D>(), Wt.C, TArray<FProcMeshTangent>(), false);
			if (Wm[S]) C->WaterMesh->SetMaterial(S, Wm[S]);
			Wt.V.Empty(); Wt.T.Empty(); Wt.UV.Empty(); Wt.C.Empty();
		}
		B.Step = 3;
	}
	else if (B.Step == 3)
	{
		Part = TEXT("wade");
		ARDWildChunk* C = B.C.Get();
		if (D->Block.Num() > 0)
		{
			UProceduralMeshComponent* W = NewObject<UProceduralMeshComponent>(C, TEXT("Wade"));
			W->SetupAttachment(C->Ground);
			W->bUseAsyncCooking = !D->bSyncCollision;
			W->SetHiddenInGame(true); W->SetVisibility(false);
			W->RegisterComponent();
			W->CreateMeshSection(0, D->Block, D->BlockT, TArray<FVector>(), TArray<FVector2D>(), TArray<FColor>(), TArray<FProcMeshTangent>(), true);
			W->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
			W->SetCollisionResponseToAllChannels(ECR_Ignore);
			W->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
		}
		D->Block.Empty(); D->BlockT.Empty();
		B.Step = 4; B.Inst = 0; B.InstAt = 0;
	}
	else if (B.Step == 4)
	{
		Part = TEXT("plants");
		ARDWildChunk* C = B.C.Get();
		// (the next table entry with instances to add; a big one in parts)
		while (B.Inst < D->Inst.Num())
		{
			FRDWChunkData::FInst& In = D->Inst[B.Inst];
			if (In.bNear || In.X.Num() == 0 || !Wild->Biomes.IsValidIndex(In.Biome) || !WildBiomes.IsValidIndex(In.Biome) || !WildBiomes[In.Biome].Foliage.IsValidIndex(In.Foliage) || !WildBiomes[In.Biome].Foliage[In.Foliage].Mesh) { ++B.Inst; B.InstAt = 0; continue; }
			const FRDWildFoliage& F = WildBiomes[In.Biome].Foliage[In.Foliage];
			UHierarchicalInstancedStaticMeshComponent*& H = B.ByMesh.FindOrAdd(F.Mesh);
			if (!H)
			{
				H = NewObject<UHierarchicalInstancedStaticMeshComponent>(C);
				H->SetStaticMesh(F.Mesh);
				H->SetupAttachment(C->Ground);
				H->SetCullDistances(FMath::RoundToInt(F.CullDistance * 0.85f), FMath::RoundToInt(F.CullDistance));
				H->SetCastShadow(F.Kind != TEXT("grass") && F.Kind != TEXT("flower") && F.Kind != TEXT("reed"));
				H->SetCollisionEnabled(ECollisionEnabled::NoCollision);
				if (F.bCollision) H->ComponentTags.Add(TEXT("rdw_col"));
				for (int32 Sl = 0; Sl < F.Materials.Num(); ++Sl) if (F.Materials[Sl]) H->SetMaterial(Sl, F.Materials[Sl]);
				H->RegisterComponent();
				C->Foliage.Add(H);
			}
			// (a part of RDWInstStep from where the last stopped (B.InstAt): the rest is not moved down each part (PR #25's review:
			// RemoveAt(0, N) shifted a big entry's every remaining instance at each step))
			const int32 N = FMath::Min(In.X.Num() - B.InstAt, RDWInstStep);
			if (B.InstAt == 0 && N == In.X.Num()) H->AddInstances(In.X, false, false, false);
			else H->AddInstances(TArray<FTransform>(In.X.GetData() + B.InstAt, N), false, false, false);
			C->Instances += N;
			if (F.Kind == TEXT("tree")) C->Trees += N;
			B.InstAt += N;
			if (B.InstAt >= In.X.Num()) { In.X.Empty(); ++B.Inst; B.InstAt = 0; }
			break;
		}
		if (B.Inst >= D->Inst.Num()) B.Step = 5;
	}
	else
	{
		Part = TEXT("places");
		ARDWildChunk* C = B.C.Get();
		// (what the chunk keeps: its near plants and its places)
		D->Inst.RemoveAll([](const FRDWChunkData::FInst& In) { return !In.bNear; });
		WildKept.Add(D->Coord, B.D);
		SpawnWildPlaces(C, D->Places);
		if (WildSteamFx)
			for (const FRDWildWorld::FLake& Pd : Wild->Ponds)
			{
				if (Pd.Kind != 6) continue;
				const double X0 = D->Coord.X * WildChunkM, Y0 = D->Coord.Y * WildChunkM;
				if (Pd.C.X < X0 || Pd.C.X >= X0 + WildChunkM || Pd.C.Y < Y0 || Pd.C.Y >= Y0 + WildChunkM) continue;
				UNiagaraFunctionLibrary::SpawnSystemAttached(WildSteamFx, C->Ground, NAME_None, FVector(Pd.C.X * 100.0, Pd.C.Y * 100.0, Wild->ToZ(Pd.Level) + 20.f) - C->GetActorLocation(),
					FRotator::ZeroRotator, FVector(2.5f), EAttachLocation::KeepRelativeOffset, true, ENCPoolMethod::None);
			}
		C->bMaking = false;
		++WildBuilt;
		bDone = true;
	}
	// (the measures: streamed chunks only; one she is put on is made at once, its collision cooked on the game thread. Those
	// streamed while she runs fast cook theirs on the game thread too and are counted: PR #27's review, left out by
	// bSyncCollision they vanished from perf8's 5x run)
	const double Ms = (FPlatformTime::Seconds() - T0) * 1000.0;
	B.Ms += Ms;
	if (!D->bPutOn)
	{
		double& Pm = WildPartMsMax.FindOrAdd(Part); Pm = FMath::Max(Pm, Ms);
		WildStepMsMax = FMath::Max(WildStepMsMax, Ms);
	}
	if (bDone)
	{
		WildBuildMsLast = B.Ms;
		WildBuildMsMax = FMath::Max(WildBuildMsMax, B.Ms);
		if (!D->bPutOn) { WildChunkMsMax = FMath::Max(WildChunkMsMax, B.Ms); ++WildStreamBuilt; }
	}
	return bDone;
}

FString ARDDungeonGenerator::GetWildBuildStats(bool bReset)
{
	FString Parts;
	for (const auto& Kv : WildPartMsMax) Parts += FString::Printf(TEXT("%s%s=%.1f"), Parts.IsEmpty() ? TEXT("") : TEXT(","), *Kv.Key, Kv.Value);
	// (and the last frame's threads, as stat unit has them: game, render, RHI, GPU ms: which one a long frame waited on)
	const FString Out = FString::Printf(TEXT("%d|%.1f|%.1f|%.1f|%d|%s|%d|%d|%d|%d|%.1f|%.1f|%.1f|%.1f"), WildStreamBuilt, WildStepMsMax, WildFrameBuildMsMax, WildChunkMsMax, WildBuilding.Num(), *Parts, WildMakeFrames, WildTrims, WildDropped,
		!bWildTrimPending ? 0 : WildTrimAt < 0.0 ? 1 : 2, FPlatformTime::ToMilliseconds(GGameThreadTime), FPlatformTime::ToMilliseconds(GRenderThreadTime), FPlatformTime::ToMilliseconds(GRHIThreadTime),
		FPlatformTime::ToMilliseconds(RHIGetGPUFrameCycles(0)));
	if (bReset) { WildStreamBuilt = 0; WildStepMsMax = WildFrameBuildMsMax = WildChunkMsMax = 0.0; WildPartMsMax.Reset(); }
	return Out;
}

void ARDDungeonGenerator::SetWildNear(ARDWildChunk* C, bool bNear)
{
	if (!C || C->bNear == bNear) return;
	C->bNear = bNear;
	for (UHierarchicalInstancedStaticMeshComponent* H : C->Foliage)
		if (H && H->ComponentHasTag(TEXT("rdw_col")))
		{
			if (bNear)
			{
				H->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
				H->SetCollisionResponseToAllChannels(ECR_Block);
				H->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
			}
			else H->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		}
	C->bCollisionOn = bNear;
	if (!bNear)
	{
		for (UHierarchicalInstancedStaticMeshComponent* H : C->NearFoliage) if (H) H->DestroyComponent();
		C->NearFoliage.Reset();
		return;
	}
	const TSharedPtr<FRDWChunkData, ESPMode::ThreadSafe>* K = WildKept.Find(C->Coord);
	if (!K || !K->IsValid()) return;
	TMap<UStaticMesh*, UHierarchicalInstancedStaticMeshComponent*> ByMesh;
	for (const FRDWChunkData::FInst& In : (*K)->Inst)
	{
		if (!WildBiomes.IsValidIndex(In.Biome)) continue;
		const FRDWildFoliage& F = WildBiomes[In.Biome].Foliage[In.Foliage];
		if (!F.Mesh) continue;
		UHierarchicalInstancedStaticMeshComponent*& H = ByMesh.FindOrAdd(F.Mesh);
		if (!H)
		{
			H = NewObject<UHierarchicalInstancedStaticMeshComponent>(C);
			H->SetStaticMesh(F.Mesh);
			H->SetupAttachment(C->Ground);
			H->SetCullDistances(FMath::RoundToInt(F.CullDistance * 0.8f), FMath::RoundToInt(F.CullDistance));
			H->SetCastShadow(false);
			H->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			for (int32 Sl = 0; Sl < F.Materials.Num(); ++Sl) if (F.Materials[Sl]) H->SetMaterial(Sl, F.Materials[Sl]);
			H->RegisterComponent();
			C->NearFoliage.Add(H);
		}
		H->AddInstances(In.X, false, false, false);
	}
}

// ------------------------------------------------------------------------------------------------ the fog, the ground
void ARDDungeonGenerator::RevealWild(const FVector2D& At, float R)
{
	const int32 Cx0 = FMath::FloorToInt((At.X - R) / RDWRevealCellM), Cx1 = FMath::FloorToInt((At.X + R) / RDWRevealCellM);
	const int32 Cy0 = FMath::FloorToInt((At.Y - R) / RDWRevealCellM), Cy1 = FMath::FloorToInt((At.Y + R) / RDWRevealCellM);
	int32 New = 0;
	for (int32 I = Cx0; I <= Cx1; ++I)
		for (int32 J = Cy0; J <= Cy1; ++J)
		{
			const double Dx = (I + 0.5) * RDWRevealCellM - At.X, Dy = (J + 0.5) * RDWRevealCellM - At.Y;
			if (Dx * Dx + Dy * Dy > (double)R * R) continue;
			const FIntPoint Bk(FMath::FloorToInt((float)I / RDWRevealBlock), FMath::FloorToInt((float)J / RDWRevealBlock));
			TArray<uint64>& Bits = WildRevealed.FindOrAdd(Bk);
			if (Bits.Num() == 0) Bits.SetNumZeroed(RDWRevealBlock * RDWRevealBlock / 64);
			const int32 Bi = (I - Bk.X * RDWRevealBlock) * RDWRevealBlock + (J - Bk.Y * RDWRevealBlock);
			const uint64 M = 1ull << (Bi & 63);
			if (!(Bits[Bi >> 6] & M)) { Bits[Bi >> 6] |= M; ++New; WildRevealCount.FindOrAdd(Bk)++; }
		}
	if (New > 0) { WildRevealedCells += New; ++WildRevealVersion; }
}

bool ARDDungeonGenerator::IsWildRevealed(double Xm, double Ym) const
{
	const int32 I = FMath::FloorToInt(Xm / RDWRevealCellM), J = FMath::FloorToInt(Ym / RDWRevealCellM);
	const FIntPoint Bk(FMath::FloorToInt((float)I / RDWRevealBlock), FMath::FloorToInt((float)J / RDWRevealBlock));
	const TArray<uint64>* Bits = WildRevealed.Find(Bk);
	if (!Bits || Bits->Num() == 0) return false;
	const int32 Bi = (I - Bk.X * RDWRevealBlock) * RDWRevealBlock + (J - Bk.Y * RDWRevealBlock);
	return ((*Bits)[Bi >> 6] >> (Bi & 63)) & 1ull;
}

float ARDDungeonGenerator::WildGroundZ(FVector At) const
{
	if (!IsWildReady()) return 0.f;
	if (IsInLoadedTown(At)) return 0.f;
	return Wild->ToZ(Wild->Height(At.X / 100.0, At.Y / 100.0));
}

// ------------------------------------------------------------------------------------------------ for tests and the docs
FString ARDDungeonGenerator::GetWildState() const
{
	if (!Wild.IsValid()) return TEXT("0");
	// (in flight: computed or still being made: a chunk being made over frames has not all its plants or places yet)
	return FString::Printf(TEXT("%d|%u|%.2f|%d|%d|%d|%d|%d|%.1f|%.1f|%d|%d|%d|%d|%d|%d|%d|%d"), IsWildReady() ? 1 : 0, Wild->Seed, Wild->InitSeconds, WildChunks.Num(), WildInFlight.Num() + WildBuilding.Num(),
		WildBuilt, WildDropped, WildMaxActive, WildComputeMs, WildBuildMsMax, WildRevealedCells, WildFound.Num(), Wild->Towns.Num(), WildTicks, GenTicks,
		GetWorld()->IsPaused() ? 1 : 0, bMenuOpen ? 1 : 0, IsTownPanelOpen() ? 1 : 0);
}

TArray<FString> ARDDungeonGenerator::GetWildChunkLines() const
{
	TArray<FString> Out;
	for (const auto& Kv : WildChunks)
		if (const ARDWildChunk* C = Kv.Value)
			Out.Add(FString::Printf(TEXT("%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d"), Kv.Key.X, Kv.Key.Y, C->Instances, C->Triangles, C->bNear ? 1 : 0, C->bCollisionOn ? 1 : 0, C->Props.Num(), C->PlaceProps.Num(), C->NearFoliage.Num(), C->Trees, C->bMaking ? 1 : 0));
	return Out;
}

FString ARDDungeonGenerator::GetWildSampleAt(FVector At) const
{
	if (!IsWildReady()) return FString();
	FRDWSample S; Wild->Sample(At.X / 100.0, At.Y / 100.0, S, true);
	// (the list of 2026-11-08b: and the field's crop, "" outside a field)
	const FString Crop = Wild->CropName(S);
	return FString::Printf(TEXT("%.2f|%.0f|%s|%s|%.2f|%d|%.2f|%.2f|%.2f|%.2f|%.2f|%.2f|%.2f|%.2f|%d|%s"), S.H, Wild->ToZ(S.H), *Wild->BiomeName(S.Biome), *Wild->BiomeName(S.Biome2), S.W1, S.WaterKind,
		S.WaterKind ? S.Water : 0.f, S.Rock, S.Snow, S.Sand, S.Road, S.Field, S.Canopy, S.Lava, Wild->TierAt(At.X / 100.0, At.Y / 100.0), *Crop);
}

TArray<FString> ARDDungeonGenerator::GetWildTownLines() const
{
	TArray<FString> Out;
	if (!IsWildReady()) return Out;
	for (const FRDWildTown& T : Wild->Towns) Out.Add(FString::Printf(TEXT("%s|%s|%.0f|%.0f|%.1f|%d"), *T.Name, *T.Kind, T.Site.X, T.Site.Y, T.H, T.Style));
	return Out;
}

TArray<FString> ARDDungeonGenerator::GetWildBiomeLines() const
{
	TArray<FString> Out;
	if (!IsWildReady()) return Out;
	for (int32 B = 0; B < Wild->Biomes.Num(); ++B)
	{
		int32 N = 0; double Best = 1e18; FVector2D Bs = FVector2D::ZeroVector;
		for (int32 K = 0; K < Wild->CellBiome.Num(); ++K)
			if (Wild->CellBiome[K] == B) { ++N; const double D = Wild->CellSite[K].Size(); if (D < Best) { Best = D; Bs = Wild->CellSite[K]; } }
		Out.Add(FString::Printf(TEXT("%s|%d|%.0f|%.0f|%.1f"), *Wild->Biomes[B].Name, N, Bs.X, Bs.Y, N ? Best / 1000.0 : -1.0));
	}
	return Out;
}

TArray<FString> ARDDungeonGenerator::GetWildFeatureLines() const
{
	TArray<FString> Out;
	if (!IsWildReady()) return Out;
	for (const FRDWildWorld::FRiver& R : Wild->Rivers)
	{
		double L = 0; for (int32 I = 0; I + 1 < R.P.Num(); ++I) L += FVector2D::Distance(R.P[I], R.P[I + 1]);
		Out.Add(FString::Printf(TEXT("river|%d|%.1f|%.0f|%.0f|%.0f|%.1f|%.1f"), R.P.Num(), L / 1000.0, R.W.Last(), R.P[0].X, R.P[0].Y, R.S[0], R.S.Last()));
	}
	for (const FRDWildWorld::FLake& K : Wild->Lakes) Out.Add(FString::Printf(TEXT("lake|%.0f|%.0f|%.0f|%.1f"), K.C.X, K.C.Y, K.R, K.Level));
	for (const FRDWildWorld::FRoad& R : Wild->Roads)
	{
		double L = 0; for (int32 I = 0; I + 1 < R.P.Num(); ++I) L += FVector2D::Distance(R.P[I], R.P[I + 1]);
		Out.Add(FString::Printf(TEXT("road|%s|%s|%.1f|%.0f|%.0f"), *Wild->Towns[R.From].Name, *Wild->Towns[R.To].Name, L / 1000.0, R.P[0].X, R.P[0].Y));
	}
	return Out;
}

TArray<FString> ARDDungeonGenerator::GetWildPlacesNear(FVector At, float RadiusM) const
{
	TArray<FString> Out;
	if (!IsWildReady()) return Out;
	const double X = At.X / 100.0, Y = At.Y / 100.0;
	const FIntPoint C0 = Wild->PlaceCellOf(X - RadiusM, Y - RadiusM), C1 = Wild->PlaceCellOf(X + RadiusM, Y + RadiusM);
	TArray<FRDWildPlace> Ps;
	for (int32 I = C0.X; I <= C1.X; ++I) for (int32 J = C0.Y; J <= C1.Y; ++J) Wild->PlacesIn(FIntPoint(I, J), Ps);
	for (const FRDWildPlace& P : Ps)
		if (FVector2D::Distance(P.At, FVector2D(X, Y)) <= RadiusM)
			Out.Add(FString::Printf(TEXT("%d|%s|%s|%.0f|%.0f|%.1f|%d|%d"), P.Id, *P.Kind, *P.Name, P.At.X, P.At.Y, P.H, P.Tier, WildFound.Contains(P.Id) ? 1 : 0));
	return Out;
}

bool ARDDungeonGenerator::WildDebugMap(const FString& Path, int32 Px, float X0m, float Y0m, float X1m, float Y1m, bool bFog)
{
	if (!IsWildReady() || Px < 8) return false;
	const FRDWildWorld& W = *Wild;
	// north up: a row is a line of X (X1 at the top), a column a line of Y (Y0 at the left)
	const double Pm = (X1m - X0m) / Px;
	TArray<float> H; H.SetNumUninitialized((Px + 2) * (Px + 2));
	TArray<FLinearColor> Cl; Cl.SetNumUninitialized(Px * Px);
	TArray<uint8> Wet; Wet.SetNumZeroed(Px * Px);
	ParallelFor(Px + 2, [&](int32 R)
	{
		for (int32 Cc = 0; Cc < Px + 2; ++Cc)
		{
			const double X = X1m - (R - 0.5) * Pm, Y = Y0m + (Cc - 0.5) * Pm;
			FRDWSample S; W.Sample(X, Y, S, Pm < 30.0, (float)Pm);
			H[R * (Px + 2) + Cc] = S.WaterKind ? S.Water : S.H;
			if (R >= 1 && Cc >= 1 && R <= Px && Cc <= Px) { Cl[(R - 1) * Px + (Cc - 1)] = S.Color; Wet[(R - 1) * Px + (Cc - 1)] = S.WaterKind ? 1 : 0; }
		}
	});
	TArray<FColor> Pix; Pix.SetNumUninitialized(Px * Px);
	const FVector Light = FVector(-0.55, 0.55, 0.63).GetSafeNormal();      // (from the north-west; x east, y north)
	const float K = FMath::Clamp(1.6f + (float)(Pm / 300.0), 1.6f, 5.f);
	ParallelFor(Px, [&](int32 R)
	{
		for (int32 Cc = 0; Cc < Px; ++Cc)
		{
			const int32 A = (R + 1) * (Px + 2) + (Cc + 1);
			const float Dzde = (H[A + 1] - H[A - 1]) / (float)(2.0 * Pm), Dzdn = (H[A - (Px + 2)] - H[A + (Px + 2)]) / (float)(2.0 * Pm);
			const FVector Nr = FVector(-K * Dzde, -K * Dzdn, 1.f).GetSafeNormal();
			const float Sh = Wet[R * Px + Cc] ? 0.75f : FMath::Clamp((float)FVector::DotProduct(Nr, Light), 0.f, 1.f);
			FLinearColor C = Cl[R * Px + Cc] * (0.45f + 0.8f * Sh);
			// (the reference's look: somewhat greyed and cool)
			const float Lum = C.R * 0.3f + C.G * 0.59f + C.B * 0.11f;
			C = FMath::Lerp(C, FLinearColor(Lum, Lum * 1.02f, Lum * 1.05f), 0.25f);
			if (bFog)
			{
				const double X = X1m - (R + 0.5) * Pm, Y = Y0m + (Cc + 0.5) * Pm;
				if (!IsWildRevealed(X, Y)) C = FLinearColor(0.55f, 0.53f, 0.47f);
			}
			Pix[R * Px + Cc] = C.ToFColor(true);
		}
	});
	// (the towns: a dark square with a light rim)
	for (const FRDWildTown& T : W.Towns)
	{
		const int32 R = FMath::RoundToInt((X1m - T.Site.X) / Pm), Cc = FMath::RoundToInt((T.Site.Y - Y0m) / Pm);
		for (int32 Dr = -4; Dr <= 4; ++Dr) for (int32 Dc = -4; Dc <= 4; ++Dc)
		{
			const int32 Rr = R + Dr, Cr = Cc + Dc; if (Rr < 0 || Cr < 0 || Rr >= Px || Cr >= Px) continue;
			Pix[Rr * Px + Cr] = (FMath::Abs(Dr) == 4 || FMath::Abs(Dc) == 4) ? FColor(240, 230, 200) : FColor(60, 20, 20);
		}
	}
	TArray64<uint8> Png;
	FImageUtils::PNGCompressImageArray(Px, Px, TArrayView64<const FColor>(Pix.GetData(), Pix.Num()), Png);
	return FFileHelper::SaveArrayToFile(Png, *Path);
}

bool ARDDungeonGenerator::WildPutHer(float Xm, float Ym)
{
	if (!IsWildReady()) return false;
	APawn* P = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!P) return false;
	// the chunk she lands on and its neighbours made now, their collision cooked at once
	const double Cm = WildChunkM;
	const int32 Ic = FMath::FloorToInt(Xm / Cm), Jc = FMath::FloorToInt(Ym / Cm);
	for (int32 I = Ic - 1; I <= Ic + 1; ++I)
		for (int32 J = Jc - 1; J <= Jc + 1; ++J)
		{
			const FIntPoint C(I, J);
			// (one still being made over frames: its collision may not be cooked yet; made again now)
			const int32 Mk = WildBuilding.IndexOfByPredicate([&C](const FWildBuild& B) { return B.D.IsValid() && B.D->Coord == C; });
			if (Mk != INDEX_NONE)
			{
				WildBuilding.RemoveAt(Mk);
				if (TObjectPtr<ARDWildChunk>* Old = WildChunks.Find(C)) { if (*Old) (*Old)->Destroy(); WildChunks.Remove(C); WildKept.Remove(C); }
			}
			if (WildChunks.Contains(C)) continue;
			TSharedPtr<FRDWChunkData, ESPMode::ThreadSafe> D = MakeShared<FRDWChunkData, ESPMode::ThreadSafe>();
			D->Coord = C; D->ChunkM = WildChunkM; D->StepM = WildStepM; D->bSyncCollision = true; D->bPutOn = true;
			WildTownHole(*D);
			RDWildComputeChunk(*Wild, *D);
			BuildWildChunk(D);
		}
	const float Z = WildGroundZ(FVector(Xm * 100.0, Ym * 100.0, 0.0));
	P->SetActorLocation(FVector(Xm * 100.0, Ym * 100.0, Z + 120.f), false, nullptr, ETeleportType::TeleportPhysics);
	if (ACharacter* Ch = Cast<ACharacter>(P)) Ch->GetCharacterMovement()->StopMovementImmediately();
	LastSafeSpot = P->GetActorLocation(); bHasSafeSpot = true;
	return true;
}

void ARDDungeonGenerator::WildDropAll()
{
	WildAskTrim();
	for (auto& Kv : WildChunks) if (Kv.Value) Kv.Value->Destroy();
	WildDropped += WildChunks.Num();
	WildChunks.Reset(); WildKept.Reset(); WildBuilding.Reset();
}

