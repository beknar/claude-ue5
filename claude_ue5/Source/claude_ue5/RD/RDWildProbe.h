// The wilderness's ground measured without a game or a GPU (the user's of 2026-11-08: "at around 12km from brokenspire, player
// found a wall of earth that is a sheer drop that can't be climbed"; play on brokenspire ran the GPU out of memory). The world
// is made from a seed as the game makes it (FRDWildWorld::Init with the level's biome table) and its ground sampled on a grid:
//
//   UnrealEditor-Cmd.exe <project> -run=RDWildProbe -nullrhi -unattended -Seed=<n> -X=<m> -Y=<m> -Half=<m> -Step=<m> -Out=<dir>
//       [-Points="x,y;x,y"]  [-Map=/Game/RandomDungeon/Maps/brokenspire]
//
// writes <dir>/info.txt (the seed, the grid, Brokenspire's height, the biomes' names, the towns) and the grid's rows (X north,
// Y east, metres, X0 + i * Step, Y0 + j * Step; row-major by i) as h.bin (the ground, metres above the sea, float32), water.bin
// (the water's surface or -1e9), b.bin / b2.bin (the two heaviest biomes, uint8), w1.bin (the first's weight); with -Points,
// points.txt: each point's regions and weights, its ground before and after the rivers, roads and towns. The roads out of
// Brokenspire's gate are not the game's (the gate is known only once the town is built: StartWild's GateOut).
#pragma once

#include "CoreMinimal.h"
#include "Commandlets/Commandlet.h"
#include "RDWildProbe.generated.h"

UCLASS()
class URDWildProbeCommandlet : public UCommandlet
{
	GENERATED_BODY()
public:
	URDWildProbeCommandlet();
	virtual int32 Main(const FString& Params) override;
};
