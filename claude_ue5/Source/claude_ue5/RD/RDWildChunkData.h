// What a worker thread computes for one wilderness chunk (RDWildChunk.cpp) and the game thread makes into an ARDWildChunk.
#pragma once

#include "CoreMinimal.h"
#include "Containers/Queue.h"
#include "Async/Future.h"
#include "RD/RDWild.h"
#include "ProceduralMeshComponent.h"

struct FRDWChunkData
{
	FIntPoint Coord = FIntPoint::ZeroValue;
	double ChunkM = 250.0, StepM = 2.0;
	int32 Nv = 0;
	/** a loaded town's section square here: the ground sinks under the town's own */
	bool bTownHole = false;
	FVector2D TownAt = FVector2D::ZeroVector;
	double TownHalfM = 252.0;
	// the ground (positions relative to the chunk's corner, cm)
	TArray<FVector> V, N;
	TArray<int32> T;
	/** UV1 (rock, snow), UV2 (sand, mud), UV3 (the road, its ruts' noise): the ground material's layers */
	TArray<FVector2D> UV0, UV1, UV2, UV3;
	TArray<FLinearColor> C;
	TArray<float> Slope;
	TArray<FProcMeshTangent> Tan;
	// water: 0 fresh (lakes, rivers, ponds, marsh pools), 1 the sea, 2 hot springs, 3 lava
	struct FWater { TArray<FVector> V; TArray<int32> T; TArray<FVector2D> UV; TArray<FLinearColor> C; };
	FWater Water[4];
	// the wading floor under deep water and the sea's barrier (collision only)
	TArray<FVector> Block;
	TArray<int32> BlockT;
	// the plants and rocks: per biome and table entry
	struct FInst { int32 Biome = 0, Foliage = 0; bool bNear = false; TArray<FTransform> X; };
	TArray<FInst> Inst;
	TArray<FRDWildPlace> Places;
	double Ms = 0.0;
	/** asked for at this generation of the streaming (a chunk dropped and asked again is computed again) */
	int32 Ticket = 0;
	/** its collision cooked at once (she is put on it, or she runs faster than a worker's cooking: rd.WildRunSpeed) */
	bool bSyncCollision = false;
	/** made at once because she is put on it (left out of the streaming's measures; a fast run's streamed chunks stay in them) */
	bool bPutOn = false;
	/** the list of 2026-11-22's third phase (RDList16c.cpp): the drawn ground takes every DrawEvery-th vertex of the 2 m grid (1, 2 or 4,
	 *  the border's last always), with a skirt under its edges; its collision (CV, CT: the whole 2 m grid) only when bCollision; a
	 *  ground-only job (bGroundOnly) computes the ground alone for a chunk standing (its level of detail or its collision changed) */
	int32 DrawEvery = 1;
	bool bCollision = true, bGroundOnly = false;
	int32 RegridSeq = 0;
	TArray<FVector> CV;
	TArray<int32> CT;
};

/** what the worker threads hand back, and the world's making (shared: the tasks outlive nothing they point at) */
struct FRDWStream
{
	TQueue<TSharedPtr<FRDWChunkData, ESPMode::ThreadSafe>, EQueueMode::Mpsc> Done;
	TFuture<void> Init;
};

void RDWildComputeChunk(const FRDWildWorld& W, FRDWChunkData& D);
