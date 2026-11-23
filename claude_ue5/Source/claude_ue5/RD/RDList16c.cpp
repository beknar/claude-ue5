// The user's list of 2026-11-22 (docs/improvements16.txt; the plan docs/improvements16_plan.md), its third phase: the wilds' ground in
// levels of detail. A chunk's drawn ground takes every DrawEvery-th vertex of its 2 m grid by its nearest edge's distance from her (every
// one within WildLod1M, every second within WildLod2M, every fourth beyond), its edges' skirts covering the slivers where neighbours of
// two steps meet (RDWildDrawGround16); its collision the whole 2 m grid, on every chunk (collision only near her was measured and dropped:
// the wild monsters stand on most chunks). A chunk whose step or collision should change gets a ground-only job on the
// workers (the plants, water and places it has are left as they are) and its ground is swapped when the job is done.
// rd.WildLod 0 draws every chunk at 2 m with its collision, as before (the tests' and the measures' comparison).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDWildChunkData.h"
#include "RD/RDMonster.h"
#include "ProceduralMeshComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Async/Async.h"
#include "HAL/IConsoleManager.h"
#include "EngineUtils.h"
#include "GameFramework/Character.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList16c, Log, All);

namespace
{
	TAutoConsoleVariable<int32> CVarRDWildLod(TEXT("rd.WildLod"), 1, TEXT("The wilds' ground in levels of detail by distance (1), or every chunk drawn at 2 m (0); every chunk keeps its collision either way"));
}

bool ARDDungeonGenerator::IsWildLod16() const { return CVarRDWildLod.GetValueOnGameThread() != 0; }

double ARDDungeonGenerator::WildChunkNearM16(const FIntPoint& C, const FVector2D& At) const
{
	const double Cm = WildChunkM, X0 = C.X * Cm, Y0 = C.Y * Cm;
	const double Ex = FMath::Max3(X0 - At.X, 0.0, At.X - (X0 + Cm)), Ey = FMath::Max3(Y0 - At.Y, 0.0, At.Y - (Y0 + Cm));
	return FMath::Sqrt(Ex * Ex + Ey * Ey);
}

int32 ARDDungeonGenerator::WildDrawEveryFor16(double NearM, int32 Cur) const
{
	if (!IsWildLod16()) return 1;
	auto Want = [this](double D) { return D < WildLod1M16 ? 1 : D < WildLod2M16 ? 2 : 4; };
	int32 W = Want(NearM);
	// (finer at once; coarser only 80 m past the ring, or a chunk on the ring would be swapped back and forth)
	if (Cur > 0 && W > Cur) W = FMath::Max(Cur, Want(NearM - 80.0));
	return W;
}

bool ARDDungeonGenerator::WildCollisionFor16(double NearM, bool bHas) const
{
	// (measured in 888 lod16: the wild monsters stand on 52 to 58 of the 64 chunks, so collision near her only saved six chunks' and cost a
	// ground swap each time one changed: every chunk keeps its collision, as before; TODO.md keeps the idea for a later measure)
	return true;
}

void ARDDungeonGenerator::AskWildRegrid16(ARDWildChunk* C, int32 Every, bool bCollision, bool bNow)
{
	if (!C || !Wild.IsValid()) return;
	TSharedPtr<FRDWChunkData, ESPMode::ThreadSafe> D = MakeShared<FRDWChunkData, ESPMode::ThreadSafe>();
	D->Coord = C->Coord; D->ChunkM = WildChunkM; D->StepM = WildStepM; D->Ticket = C->Ticket16;
	// (each ask numbered: a slower job asked before a newer one (a put-down's at once) is not applied over it (PR #112's review); the 2 m
	// collision copied only for a chunk that has none)
	D->RegridSeq = ++C->RegridSeq16;
	D->DrawEvery = Every; D->bCollision = bCollision && !C->GroundCollision; D->bGroundOnly = true; D->bSyncCollision = bNow;
	WildTownHole(*D);
	C->bRegrid16 = true;
	++WildRegrids16;
	if (bNow) { RDWildComputeChunk(*Wild, *D); ApplyWildRegrid16(*D); return; }
	++WildRegridInFlight16;
	TSharedPtr<FRDWildWorld, ESPMode::ThreadSafe> W = Wild;
	TSharedPtr<FRDWStream, ESPMode::ThreadSafe> St = WildStream;
	Async(EAsyncExecution::ThreadPool, [W, St, D]() { RDWildComputeChunk(*W, *D); St->Done.Enqueue(D); });
}

void ARDDungeonGenerator::ApplyWildRegrid16(FRDWChunkData& D)
{
	if (!D.bSyncCollision) WildRegridInFlight16 = FMath::Max(0, WildRegridInFlight16 - 1);
	TObjectPtr<ARDWildChunk>* Cp = WildChunks.Find(D.Coord);
	ARDWildChunk* C = Cp ? Cp->Get() : nullptr;
	if (!IsValid(C)) return;
	C->bRegrid16 = false;
	// (asked for an older chunk of this place (the new one has its own ground), or before a newer ask of this chunk)
	if (C->Ticket16 != D.Ticket || C->bMaking || D.RegridSeq != C->RegridSeq16) return;
	const double T0 = FPlatformTime::Seconds();
	C->Ground->CreateMeshSection_LinearColor(0, D.V, D.T, D.N, D.UV0, D.UV1, D.UV2, D.UV3, D.C, D.Tan, false);
	if (WildGroundMaterial) C->Ground->SetMaterial(0, WildGroundMaterial);
	C->Triangles = D.T.Num() / 3;
	C->DrawEvery16 = D.DrawEvery;
	if (D.bCollision && !C->GroundCollision) MakeWildCollision16(C, D.CV, D.CT, D.bSyncCollision);
	WildRegridMsMax16 = FMath::Max(WildRegridMsMax16, (FPlatformTime::Seconds() - T0) * 1000.0);
}

void ARDDungeonGenerator::MakeWildCollision16(ARDWildChunk* C, const TArray<FVector>& V, const TArray<int32>& T, bool bSync)
{
	// (she, the monsters, the camera and the traces stand on it as on the ground before: BlockAll, hidden, not in the scene)
	if (!C || V.Num() == 0) return;
	UProceduralMeshComponent* G = NewObject<UProceduralMeshComponent>(C, TEXT("GroundCollision"));          // (by name: 888's skin step finds it so)
	G->SetupAttachment(C->Ground);
	G->bUseAsyncCooking = !bSync;
	G->SetCollisionProfileName(TEXT("BlockAll"));
	G->SetHiddenInGame(true); G->SetVisibility(false); G->SetCastShadow(false);
	G->RegisterComponent();
	G->CreateMeshSection(0, V, T, TArray<FVector>(), TArray<FVector2D>(), TArray<FColor>(), TArray<FProcMeshTangent>(), true);
	C->GroundCollision = G;
}

void ARDDungeonGenerator::TickWildLod16(const FVector2D& At)
{
	// (each chunk's step by its distance, the nearest first, a few jobs at a time; every chunk keeps the collision it was made with
	// (WildCollisionFor16: collision only near her was measured and dropped, PR #112))
	struct FWant { double D; ARDWildChunk* C; int32 Every; };
	TArray<FWant> Wants;
	for (auto& Kv : WildChunks)
	{
		ARDWildChunk* C = Kv.Value;
		if (!IsValid(C) || C->bMaking || C->bRegrid16) continue;
		const double D = WildChunkNearM16(Kv.Key, At);
		const int32 Ev = WildDrawEveryFor16(D, C->DrawEvery16);
		if (Ev != C->DrawEvery16 || !C->GroundCollision) Wants.Add({ D, C, Ev });
	}
	Wants.Sort([](const FWant& A, const FWant& B) { return A.D < B.D; });
	for (const FWant& W : Wants)
	{
		if (WildRegridInFlight16 >= WildRegridMax16) break;
		AskWildRegrid16(W.C, W.Every, true, false);
	}
}

FString ARDDungeonGenerator::GetWildLod16() const
{
	// (tests: "<regrids>|<in flight>|<longest swap ms>|<on>|<chunks at 1>|<at 2>|<at 4>|<with collision>|<triangles>")
	int32 N1 = 0, N2 = 0, N4 = 0, Col = 0, Tri = 0;
	for (const auto& Kv : WildChunks)
	{
		const ARDWildChunk* C = Kv.Value; if (!IsValid(C)) continue;
		(C->DrawEvery16 <= 1 ? N1 : C->DrawEvery16 == 2 ? N2 : N4)++;
		if (C->GroundCollision) ++Col;
		Tri += C->Triangles;
	}
	return FString::Printf(TEXT("%d|%d|%.1f|%d|%d|%d|%d|%d|%d"), WildRegrids16, WildRegridInFlight16, WildRegridMsMax16, IsWildLod16() ? 1 : 0, N1, N2, N4, Col, Tri);
}

// ================================================================================================ the tests' measures, on the meshes themselves
namespace
{
	// (the drawn surface's height at a point of a chunk (cm, relative to the chunk's corner), from its ground mesh's first section: its
	// grid of every DrawEvery-th vertex as RDWildDrawGround16 lays it, each cell's two triangles split from (a+1, b) to (a, b+1))
	bool RDWildDrawnZ16(const ARDWildChunk* C, int32 Nv, double StCm, double Lx, double Ly, float& Z)
	{
		if (!C || !C->Ground) return false;
		const FProcMeshSection* S = C->Ground->GetProcMeshSection(0);
		if (!S) return false;
		TArray<int32> Ix;
		const int32 Ev = FMath::Max(1, C->DrawEvery16);
		for (int32 I = 0; I < Nv; I += Ev) Ix.Add(I);
		if (Ix.Last() != Nv - 1) Ix.Add(Nv - 1);
		const int32 M = Ix.Num();
		if (S->ProcVertexBuffer.Num() < M * M) return false;
		auto Cell = [&](double L, int32& A, double& F)
		{
			const double G = FMath::Clamp(L / StCm, 0.0, (double)(Nv - 1));
			A = 0; while (A + 2 < M && Ix[A + 1] <= G) ++A;
			F = FMath::Clamp((G - Ix[A]) / FMath::Max(1, Ix[A + 1] - Ix[A]), 0.0, 1.0);
		};
		int32 A, B; double Fa, Fb; Cell(Lx, A, Fa); Cell(Ly, B, Fb);
		auto Pz = [&](int32 a, int32 b) { return S->ProcVertexBuffer[a * M + b].Position.Z; };
		const float Z00 = Pz(A, B), Z10 = Pz(A + 1, B), Z01 = Pz(A, B + 1), Z11 = Pz(A + 1, B + 1);
		Z = Fa + Fb <= 1.0 ? (float)(Z00 + (Z10 - Z00) * Fa + (Z01 - Z00) * Fb) : (float)(Z11 + (Z01 - Z11) * (1.0 - Fa) + (Z10 - Z11) * (1.0 - Fb));
		return true;
	}
}

FString ARDDungeonGenerator::GetWildSeams16() const
{
	// (tests: along every edge between two chunks drawn at different steps, every 50 cm, the two surfaces' heights there: the largest gap,
	// how many points are deeper than the skirt; and the drawn surfaces' largest departure from the 2 m ground (the world model's own
	// height, sampled at the same points): "<pairs>|<points>|<largest gap cm>|<points past the skirt>|<largest departure cm>")
	if (!IsWildReady()) return FString();
	const int32 Nv = FMath::RoundToInt(WildChunkM / WildStepM) + 1;
	const double StCm = WildStepM * 100.0, Cm = WildChunkM * 100.0;
	int32 Pairs = 0, Pts = 0, Past = 0; float Gap = 0.f, Dev = 0.f;
	for (const auto& Kv : WildChunks)
	{
		const ARDWildChunk* A = Kv.Value;
		if (!IsValid(A) || A->bMaking) continue;
		for (const FIntPoint Dd : { FIntPoint(1, 0), FIntPoint(0, 1) })
		{
			const TObjectPtr<ARDWildChunk>* Bp = WildChunks.Find(Kv.Key + Dd);
			const ARDWildChunk* B = Bp ? Bp->Get() : nullptr;
			if (!IsValid(B) || B->bMaking || B->DrawEvery16 == A->DrawEvery16) continue;
			++Pairs;
			for (double S = 0.0; S <= Cm; S += 50.0)
			{
				// (the edge in A's frame: x = Cm (or y = Cm); in B's: 0)
				float Za, Zb;
				const bool bX = Dd.X == 1;
				if (!RDWildDrawnZ16(A, Nv, StCm, bX ? Cm : S, bX ? S : Cm, Za) || !RDWildDrawnZ16(B, Nv, StCm, bX ? 0.0 : S, bX ? S : 0.0, Zb)) continue;
				++Pts;
				const float G = FMath::Abs(Za - Zb);
				Gap = FMath::Max(Gap, G);
				if (G > 500.f) ++Past;
				// (the 2 m surface there: the world model's height)
				const double Wx = (Kv.Key.X * Cm + (bX ? Cm : S)) / 100.0, Wy = (Kv.Key.Y * Cm + (bX ? S : Cm)) / 100.0;
				FRDWSample Q; Wild->Sample(Wx, Wy, Q, true);
				const float Zt = Wild->ToZ(Q.H);
				Dev = FMath::Max(Dev, FMath::Max(FMath::Abs(Za - Zt), FMath::Abs(Zb - Zt)));
			}
		}
	}
	return FString::Printf(TEXT("%d|%d|%.1f|%d|%.1f"), Pairs, Pts, Gap, Past, Dev);
}

FString ARDDungeonGenerator::GetWildFootGaps16() const
{
	// (tests: the trees and rocks on chunks drawn coarser than 2 m: each instance's foot against the drawn surface under it (cm, above it
	// positive), as the plants were laid on the 2 m ground: "<instances>|<largest above cm>|<95th percentile above cm>|<largest below cm>")
	if (!IsWildReady()) return FString();
	const int32 Nv = FMath::RoundToInt(WildChunkM / WildStepM) + 1;
	const double StCm = WildStepM * 100.0;
	TArray<float> Up; float Below = 0.f;
	for (const auto& Kv : WildChunks)
	{
		const ARDWildChunk* C = Kv.Value;
		if (!IsValid(C) || C->bMaking || C->DrawEvery16 <= 1) continue;
		const FVector O = C->GetActorLocation();
		for (const UHierarchicalInstancedStaticMeshComponent* H : C->Foliage)
		{
			if (!H) continue;
			for (int32 I = 0; I < H->GetInstanceCount() && I < 400; ++I)
			{
				FTransform X; H->GetInstanceTransform(I, X, true);
				const FVector L = X.GetLocation() - O;
				float Z; if (!RDWildDrawnZ16(C, Nv, StCm, L.X, L.Y, Z)) continue;
				const float D = L.Z - Z;
				if (D >= 0.f) Up.Add(D); else Below = FMath::Max(Below, -D);
			}
		}
	}
	Up.Sort();
	return FString::Printf(TEXT("%d|%.1f|%.1f|%.1f"), Up.Num(), Up.Num() ? Up.Last() : 0.f, Up.Num() ? Up[FMath::Clamp(FMath::FloorToInt(Up.Num() * 0.95f), 0, Up.Num() - 1)] : 0.f, Below);
}

FString ARDDungeonGenerator::GetWildMoversOffGround16() const
{
	// (tests: every wild monster and every animal or person of the wilds standing where no chunk under it has collision (a town's own
	// ground excepted): "<checked>|<without ground>|<their names, ; between>")
	int32 N = 0, Off = 0; FString Names;
	auto Check = [&](const AActor* A, const FString& Nm)
	{
		if (!IsValid(A)) return;
		const FVector L = A->GetActorLocation();
		if (IsInLoadedTown(L)) return;
		++N;
		const FIntPoint C(FMath::FloorToInt(L.X / 100.0 / WildChunkM), FMath::FloorToInt(L.Y / 100.0 / WildChunkM));
		// (a mover beyond every chunk (past the streamed square) is not the levels of detail's to answer for: only a chunk standing there
		// without its collision counts)
		const TObjectPtr<ARDWildChunk>* Cp = WildChunks.Find(C);
		if (!Cp || !IsValid(*Cp) || (*Cp)->bMaking) { --N; return; }
		if (!(*Cp)->GroundCollision) { ++Off; if (Names.Len() < 400) Names += Nm + TEXT(";"); }
	};
	for (const ARDMonster* Mo : GetMonsters()) if (IsValid(Mo) && !Mo->IsDead()) Check(Mo, Mo->GetName());
	if (UWorld* W = GetWorld())
		for (TActorIterator<ACharacter> It(W); It; ++It) if (!Cast<ARDMonster>(*It) && *It != UGameplayStatics::GetPlayerPawn(this, 0)) Check(*It, It->GetName());
	return FString::Printf(TEXT("%d|%d|%s"), N, Off, *Names);
}