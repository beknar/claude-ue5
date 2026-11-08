# Graymourne and its sewers (`896`, `897`, `RD/RDPort.cpp`, the port plan in `RD/RDTownPlan.cpp`, the fog in `RD/RDSky.cpp`; the user's spec of 2026-11-07, `docs/graymourne.txt`, `docs/levels/graymourne.md`)

The city is a wilderness town on `brokenspire` with the port plan (`FRDWildTown::Plan` 3 -> the generator's `TownPlan`, `bPort`; `bMid` the rules it shares with the holy and forge cities: a landmark at the middle over a dungeon of its own); the sewers are `sewers`, a Save As copy of `mistward_castle` with `bTierFloors` and its own `DungeonKey`. Every rule is behind `TownPlan == 3`, a non-empty `TownHarbour`, `PortFog` or a level's own data: the other towns and dungeons are unchanged.

## The harbour

- **The sea is out of reach**: every town's ground is at Brokenspire's height, 12 m or more over the sea, and the wilds level and dry the land round a town. The harbour is an inner basin of the town's own along the sea wall (`TownHarbour`, `TownPiers`): water at -110 cm, the walked floor at -170 behind blockers, the drawn bed at -260. The town wall still stands between it and the sea.
- **Pier tiles are walkable ground to every other rule**: the grass, flowers and bushes grew on them and the drawn ground stood at the quay's height between the planks (884 gm1's picture). The drawn ground sinks under the whole harbour rectangle, the walked ground on a pier is flat at 0 (not `TownLiftAt`), and neither plant pass places anything in the harbour. The test counts every instance on a pier that is not the port's own.
- **Push her at every way of the edge, from the land** (PR #25's review, 2026-11-08): the walk mesh's vertices on a tile's edge take the tile on their +X / +Y side, so where the water lies +X or +Y of the quay the walked ground drops 1.4 m in its last 1.5 m before the blocker and she slid down it; the pier push alone never saw it (the decks' own collision holds her up there). `884 port` traces every edge both sides and pushes her on each way (`harbour_edges`, `edge_push`).
- **Draw the harbour's drop behind the quay's face** (PR #26's review, 2026-11-08): on the drawn ground's regular grid the bed's drop was a 1 m ramp out of the water in front of the face (and under the piers' roots); moved to 5 cm in front of the line it was a cliff of stretched grass over the stone (gm8's pictures). The vertex on the rectangle's edge stands 10 cm back into the land and the sunk vertex next to it 5 cm back, under the wall: the stone shows (gm9). Look at an edge from above, not only from the quay.
- **The blockers are measured by pushing**: she walks a pier, is pushed across it 2.5 s each way, and must stay on its deck (2.55 m off its middle: the 3 m edge less her capsule).
- **A pier's way out** comes from the ship moored beside it (the longer axis of ship minus pier): the spot lines carry no yaw.

## The fog

- **A density alone did nothing near**: the wilds' fog starts 250 m out (887's `WILD_FOG` start 25000 cm), so nine times its density left the whole town clear (the wall 80 m off sharp, gm1). `PortFogStart` draws the start in to 5 m as `PortFog` rises. The test reads the world's fog component, not the generator's number.
- **It eases in over seconds** as the town comes (`PortFog` 0.04 a call): read it after it settles (gm3 read it at 0.88 and failed).

## The sewer gate

- **Look at a piece where it stands**: the Sewer pack's barred outfall (`SM_Sewer_Bars_01a`) is pale concrete and read as a glowing white ring in the Sluice House under its light; dimming the light did not help (gm2). The round iron gate (`SM_Sewer_Tube_Gate_01a`) in Junkyard's rusted iron reads as a grating (gm5). The pack's gateway (`SM_Gateway_01`) is a plain metal door frame.
- **The pale disc before a dungeon's gate** is the walk-in mark the other towns' gates have; it is not the Sewer pack's mud (taken out, the disc stayed).

## The sewers

- **A kit's clean stone reads as a hall**: the Sewer pack's cream brick and pale concrete under the castle's torches looked like a lit hall (gd1). `897` makes damp copies of their instances (`Albedo tint` toward green-grey, `Roughness Strength` lower) as `894` made the soot stone.
- **A vault took its mesh's material, not its piece's** (`RDCeilings.cpp`): the damp concrete reached the floors and walls but not the vaults over them (gd2). A piece's `Material` comes first now; only rooms built by the dungeon's shell have vaults, so the towns are unchanged.
- **The saved start section keeps the castle's great-hall furniture** (throne, carpet, banners) whatever the theme: as The War Engine's.
- **The drowned**: none of the castle's 56 kinds comes from the sea. Underwater Odyssey's crew have every clip on their own skeletons; the Monsters Underwater Pack's fish-men are on the UE4 mannequin rig with only rifle locomotion: they play the Fantasy Pack's idle, walk, warrior swings, hits and deaths (`compat`, as The War Engine's robots). The deepman's shell is a part (`FRDMonsterDef::Parts`).
