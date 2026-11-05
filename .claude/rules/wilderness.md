---
paths:
  - "claude_ue5/Source/claude_ue5/RD/RDWild*"
  - "claude_ue5/Source/claude_ue5/RD/RDSave*"
  - "pipeline/unreal/887_*"
  - "pipeline/unreal/888_*"
  - "pipeline/blender_numpy/wild_*.py"
  - "claude_ue5/SourceArt/wilderness/**"
  - "claude_ue5/Source/claude_ue5/RD/RDSky*"
  - "pipeline/unreal/890_*"
---

# The wilderness (`887`, `888`, `RD/RDWild*.cpp`, `RD/RDSave.cpp`, `docs/wilderness.txt`, `docs/levels/wilderness.md`)

A continent of 300 x 300 km round Brokenspire, on the `brokenspire` level (the generator's `bWild`), made from one seed as she comes to it: `FRDWildWorld` (`RDWildWorld.cpp`) is pure functions of the seed, called from worker threads; the chunks (`RDWildChunk.cpp`, `RDWildGame.cpp`), the towns (`RDWildTown.cpp`), the places (`RDWildPlaces.cpp`), the map (`RDWildMap.cpp`, `RDWildHUD.cpp`) and the save (`RDSave.cpp`) use it.

## Building it

- **The procedural mesh keeps its UVs at half precision** (`FStaticMeshVertexBuffer` on PC): the ground's detail coordinates counted from the continent's corner (up to 75000 repeats) came out as one texel everywhere, a flat colour. The ground, water and lava materials take their coordinates from the world position (full precision in the shader). Its vertex colours are stored linear (`CreateMeshSection_LinearColor`'s `bSRGBConversion` defaults to false).
- **A detail texture's brightness is measured against its own average** (its coarsest mip, `TMVM_MIP_LEVEL`): a constant for the average clamped every pixel to the floor (no detail at all).
- **FrozenNorseEnvironment's masters do not compile here** (`MatLayerBlend_Simple: arithmetic between float3 and float4`, its cliffs, ice and runestones): its meshes drew the default material. `887 fixmats` gives them materials of our own from each broken instance's textures; the runestones' instance has none (Relics' rune stones stand in). Probe a pack's meshes' base materials for 0 pixel instructions before using them.
- **No pack has an aspen, a birch or an acacia**: `blender_numpy/wild_trees.py` builds them (trunk and branches as tubes, leaf cards with a painted spray), `887 trees` imports them.
- **A plant's size comes from its mesh's bounds** (the table gives a height in metres): the packs' meshes are of every scale.
- **The level's kill height came from the castle's**: the marshes lie 45 m and the sea floor 117 m below Brokenspire's ground, and a pawn below the kill height is destroyed (her too: the wilderness's tick then waited for a pawn for ever, and the test went on "passing"). `887 level` sets it at -50 km.
- **The town's height fog thickened sharply below its own height**: the coasts and valleys came out washed out. The wilderness's fog is nearly even with height, from 250 m on. The pale look that stayed was the morning light (08:00, a low sun, the sky light's blue): the base colour buffer (`r.BufferVisualizationTarget BaseColor`, `ShowFlag.VisualizeBuffer 1`) showed the ground's own colours right. Look at the albedo before changing a material for a lighting problem.
- **Every town's ground is at Brokenspire's height above the sea** (the game's z 0), each town's region eased to it over 1.7 km: the town code needs no height of its own. The flattening does not lift the sea or a beach beyond a town's core (it raised Graymourne's coast 3.5 km out to sea).

## The world's model

- **Look at the whole of it before the chunks**: `WildDebugMap` writes the continent from above; the first pictures showed flat blobs (the regions' colours alone): relief over every region but the flattest and colours varied at three scales made it read.
- **A factor meant for forests took every tree of the open biomes**: a tree's chance was multiplied by the sample's canopy over its biome's, and the 14 open biomes whose tables list a few trees (the savannah's acacias, the plains', the marshes' dead beeches) have canopy 0: none stood anywhere, while the test's count of all plants passed on their bushes and rocks. The factor applies to forest biomes only, and the look step counts trees (a chunk's `Trees`) for every biome whose table has them. Count each kind a table promises, not a total.
- **A lookup at every sample costs**: the ponds of the nine 4 km cells round each sample, each testing its rim, made a chunk take a second; all ponds are made at Init and hashed like the lakes (50-120 ms a chunk now).
- **A river traced downhill stops in the first hollow** (one river of 60): it cuts through rises of up to 45 m (its surface still only falls) and leans toward the coast. **An element added from its own array** (`R.W.Add(R.W.Last())`) can be read after the array moved: copy it first (it crashed the world's making).
- **A town on the coast is placed by walking out to the sea**, then a few hundred metres back; a loop that walked it inland "until the land was solid" put Graymourne 2.6 km from the sea.

## Playing it

- **The chunks' collision cooks on worker threads**: a chunk she is put on is made with its collision cooked at once (`WildPutHer`, `bSyncCollision`).
- **A steep slope slides her down as a fall**: put on a volcano's upper flank she slid 465 m and died. The test puts her only where the ground is walkable; out there a death brings her back in the square of the nearest town she has found (`WildRespawnAt`, loaded at once).
- **A town loaded as she comes must not put her in its square** (`AfterTownBuilt` sets `bTownPlaced` false; `FinishWildTownLoad` sets it back).
- **The town code assumes section (0, 0) at the world's origin**: a town elsewhere moves the grid (`GridOrigin`: `WorldToTile`, `TileCenter`, `SpawnSection`); everything else goes through the section's own location.
- **The wilderness's monsters have no tile grid** (`ARDMonster::bOpenGround`): they live in a section of no tiles (`WildSection`, not in `Sections`) that `GetMonsters` adds.

## PR #16's review (2026-11-03)

- **Two id ranges must not meet**: a place's id packs its cell (`x << 14`), and the 75 cells across reach 1,228,800: the towns' ids started at 1,000,000, so the northern places were taken for towns (no travel there, not on the map) and one cell's were exactly towns 0 to 7. The towns' are `FRDWildWorld::TownIdBase` (2^30) now; the world step checks the northern ids.
- **A load's flags must be read where the save was made**: a castle save set the town's "put her back" flag, which nothing in the castle reads; back in the wilds it moved her to the castle's coordinates. The save says whether it was made in a town (`bInTown`).
- **A level that always comes back as Brokenspire must leave Brokenspire's state in the game instance**: the castle from another town's circle carried that town's looted chests and dead guards back as Brokenspire's (`EnterCastle` swaps them as the save does).
- **A leash that drops the foe must also stop the notice**: past its leash a monster took her and dropped her each tick, frozen at the edge. It walks home and notices her again within 0.8 of the leash.
- **Made again from the seed means made again in full**: a lair's monsters came back every time its chunk was made again (gold, counters). Kills are kept (`WildKilled`: place id x 16 + n, saved), their draws still made so the others keep their places.
- **A cache keyed by the view is rebuilt as the view moves**: the fog was made for the view's middle and scale, so every frame of a drag made it again (65k texels of noise). It covers twice the view and is kept while the view stays in it.
- **A menu's cursor by index breaks when lines are added**: Back from Options put the cursor on 1, now Save the game (Enter then overwrote her save). `BackToMainMenu` finds the line that opened the page; the castle's test finds Options by its line.
- The hero menu read both saves every 2 s (`Latest` and `Info`): each slot's head is read once per change of its file's time. A load of an empty or unreadable slot says so and keeps the menu open. A town's square, not a circle round its middle, says whether a save was made in it.

## The test (`888`)

- Steps that move her far leave the town unloaded: a step that needs a town loads it first.
- A step whose pawn is gone keeps "passing" on what it no longer measures: the look step checks her pawn and the chunks round her at every visit.
- **The whole test in one play session ran the machine short of memory** (the editor's committed memory 32 to 34 GB; two background runs were killed). Trimming after drops held eight long teleports flat at about 30.3 GB, but the 28 template visits still ran out: run the test in batches with the editor restarted between them (`world`; `look=<seven templates>` four times; `stream,towns,gate,map`; `places,travel,save`). Don't restart a run that was killed for memory without asking.
- What is built but not yet tested, and the known limits, are in `TODO.md`: keep it current when a step is added or a limit removed.

## The list of 2026-11-04 (`890`, `RD/RDSky.cpp`, `RD/RDWildLife.cpp`, `docs/improvements7.txt`)

- **The fog covered the sky**: the height fog's own colour hid the clouds and stars at every hour; `FogSkyCutoff` (6 km) leaves the sky to the sky.
- **Screen a pack's effect before using it by name**: Wildlands' wind effect drew huge green blobs and the rain effect showed nothing: the rain and snow are our own drops (instanced planes round the camera with `M_RD_Drops`). The first stars (a fine tiling) read as snow: they are tiled coarser and come out only after dusk.
- **A filter written as "the same" drops one side**: the swarms' town check was `bInTown != Biomes.Contains("town")`, so out in the wilds every swarm that also lives in towns (the fireflies) was dropped and the night had none. In a town only the town's swarms; outside, all.
- **The towns' level ground reaches 1.15 km**: a relief measured on a region's nearest cell to Brokenspire measured the town's flattening; the test's lines are moved 1.4 km clear of every town.
- **The roads doubled back**: the path finder starts from the 1 km grid's node nearest the gate (the town's middle), so a road left the gate and ran back along the wall; from the gate none was seen ahead. Each road now runs 600 m straight out of its town before joining the grid. Measure a road where it leaves (rings round the gate), not along the line from the square through the gate.
- **A pilot moved far drops the town**: 17 km out the home section is gone (`GetSection(0, 0)` is null), and a pilot that required it stopped without a word. Read what the town gives before moving her.