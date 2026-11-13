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

## The chunks made in steps, the captain's quests (2026-11-07: `RD/RDWildGame.cpp`'s `StepWildBuild`, `RD/RDWildQuest.cpp`, `893`)

- **A maximum that mixes two paths names neither**: `WildBuildMsMax` (the record's `build_ms_max`, 45 to 72 ms) took the chunks she is put on (made at once, their collision cooked on the game thread) with the streamed ones; TODO called it the stutter of walking. Streamed chunks took 12 to 16 ms in one go. The making's measures now count streamed chunks only (`GetWildBuildStats`).
- **A frame's cost is not the function's**: split into steps, the game thread's making fell to 9.3 ms a frame at most (6 ms the longest step), yet frames with making stayed 12 to 16 ms longer than those without, both ways. Stat unit's threads per frame (`GGameThreadTime`, `GRenderThreadTime`, `GRHIThreadTime`, `RHIGetGPUFrameCycles`; RHI is in the module's dependencies for it) put it in the render thread and the GPU: the new ground drawn. Read the threads before splitting code further.
- **Count long frames against their base rate**: most frames over 50 ms in the flight had no chunk work in them (the editor's own, the GPU near its 12 GB); a count of long frames went 63 -> 14 in one run and 60 -> 50 in the next. Compare frames with and without the thing measured, in the same run, at both tick lags (the test's tick is Slate's; the frame's drawing comes after it).
- **Run a memory check first in a fresh editor**: `stream` after `build7`'s flights held 1.6 GB more at its end than at its start (failed); alone after a restart, 191 MB less.
- **A chunk being made is not whole**: it is in `WildChunks` from its first step (so it is not asked again) with `bMaking` set; its grass waits (`SetWildNear` passes it by), the state's "in flight" counts it, and one she is put on while it is made is made again at once (`WildPutHer`). The ground's collision is a hidden mesh of its own (`GroundCollision`, BlockAll), made the step after the drawn ground.
- **A quest's place is the world's, not the town's**: the den and the tower follow the roads out of Brokenspire's gate, which differs every game: a quest's hint names the road, never a compass way (the first hint's "the road north" was west in the test's game). Their ids are `FRDWildWorld::QuestIdBase` (2^29) + index, between the places' and the towns'.
- **A quest done in the world is read from the world**: the den's pack from the kills kept (`WildKilled`, its id x 16 + 0..3), not a counter taken when the quest was accepted (killed first, it could never have finished).

## The list of 2026-11-07 (`898`, `RD/RDWild8.cpp`, `docs/improvements8.txt`)

- **Measure what she stands on, not only the ground's mesh**: the walked ground was the drawn ground's own mesh, yet she ran 2 m over the farms round Brokenspire. The character's floor (`current_floor`'s hit component) named `BS_FarGround`, `881`'s plane, which `887` had hidden with its collision set off from Python: the collision call did not keep in the saved level. A plane no longer wanted is taken out, not hidden.
- **The height fog's cutoff draws an edge on the clouds**: clouds nearer than the cutoff are fogged, farther ones not; with the clouds 1.6 km up and the cutoff at 6 km the edge ran round the sky at 15 degrees (a white disc overhead, sharpest in rain). Stronger fall-off with height (up to 0.2) left it in rain. The cutoff is past every cloud (1000 km): the sky's own pixels are still clear. Judge it on pictures of the horizon, not straight up: the camera looking up is under her (hide her body and the HUD).
- **The engine's sky texture does not tile** (`T_Sky_Clouds_M`): laid flat from the view's way it showed its seams as straight lines to the horizon. A dome's own mapping pinches at the top: thin the layer out there.
- **A bolt flies at her hand's height**: it passed over a wolf's back (hares and squirrels are lower). With no monster to fly at it flies at the nearest animal ahead of her.
- **A body lying holds a place it should not**: the animals' cap counted the dead, and no deer came back. Count the living.
- **A frame rate read just after arriving is the making's**: the farms read 5.5 a second at first and 38 settled (39 to 42 with the crops hidden). Compare the thing on and off in the same place, after the chunks are made.
- **A fringe round everything against the sky is the clouds' render target** (2026-11-08b): traced at a quarter of the view and put back at half (`r.VolumetricRenderTarget.Mode 0`), the clouds bled the sky's colour 2 to 4 px round every roof (blue under a blue sky, grey and shimmering under an overcast one). Compare one setting at a time in pictures of the same view: anti-aliasing off kept it, mode 2 and 1 cured it; mode 2 cannot meet opaque ground (the wilds' peaks reach into the cloud layer), so mode 1, set with the clouds (`BeginSky7`). Measure the fringe in the pictures (bluish pixels within 4 px of a dark edge, per edge pixel: 6 to 13 before, under 1 after).
- **A mix that keeps the heaviest few must fade the rest out, not drop them** (the user's sheer wall, 2026-11-08): `Blend` kept four regions at their whole weight and dropped any under 0.03, so a mountain region came in at 2 to 9 % at once and the ground stepped up to 125 m between two samples, in walls 22 and 32 km long round Brokenspire. Weigh each by how much it is over the cut (the fifth's weight). The same for any feature that holds the ground and stops at a radius (a lake's bank cut off at 120 m, a road's bed eased over 9 m whatever its height): ease it out. `888 ground7`'s lines (300 m in six regions, 1.4 km clear of the towns) had never crossed one.
- **Measure the ground without the game** when play cannot run (GPU memory): `-run=RDWildProbe -nullrhi` makes the world from a seed and writes its grid; `blender_numpy/wild_seams.py` finds the seams (a step over 6 m and 4 times its neighbours'; a steep face rises over many samples alike). The seed of a player's world is the save's `WildSeed` (`URDGameInstance`, serialized in the save's `Game` bytes as an IntProperty), her place its `At`.
- **GPU memory climbs with every play session** (6 GB fresh, 10.5 to 11.4 after four or five): a play at 1 frame a second, a castle test's pose measured late, and two out-of-memory crashes at play's start. Restart the editor every few sessions and before a final run.
## The medieval farms (2026-11-08b, phase 2: `RDWildWorld.cpp` `FarmAt` / `FarmsteadsIn`, `RD/RDWildFarm.cpp`, `899 farms`)

- **Look at a layout from above before walking it**: `RDWildProbe` writes the drawn ground's colour (`col.bin`) and the farms' kind and crop; a first picture showed crofts of every crop over a whole 420 m field (confetti) and yards with no farmstead in them. Count what should match (yards against farmsteads: 24 of 29, the others on a slope or a road).
- **What she walks on and what is drawn must be one function**: the ridges are added in `Sample` and in `Height` from the same `FarmAt` under the same conditions; `-Heights` writes their difference (0.000 m over a 5 km square).
- **A pieces' height can be a mesh's wrong part**: the docks' well is a 1.6 m ring with no roof, and "well: 3.5" made it 6.7 m across in every village. Measure a piece's bounds before giving it a height; one mesh shared by two kinds keeps one scale (`WildPieceScale` is by mesh name).
- **A body by its def's name, not its scale**: a townswoman's def is 0.93 (the first farm's "child" pool took her, its farmwife was a man). Women are named "Townswoman", children have their own role (`Child`).
- **A mesh's origin is not its foot or its middle**: the Lake Village fence's origin is its middle (half of it under the ground); farm pieces are put by their box's middle and bottom.
- **PR #30's review (2026-11-08)**: a place that spreads (a farmstead 40 m round) is checked over its whole ground (rings of samples), not at its point, and against the other places' points; a ridge in what she walks on is measured against the same ground with no farm (`BareHeight`), not against a line through the land (the land's own swell passed the first test); an animal that walks reads a height grid taken once over its pen, not the world's height each frame; something that lays 30 pieces and 14 actors waits its turn, one a frame (`WildFarmQueue`).

## Something every 40 seconds (2026-11-08b, phase 7: `FRDWildWorld::PoisIn`, `RD/RDWildPoi.cpp`, `912`, `888 poi7`)

- **Count what a run meets, not what a rule allows**: a 160 m grid at 80 % gave a median gap of 77 s along the lines, and near Brokenspire nothing at all (every farm ground refused, `FarmKind != 0`). Measure along lines of the world's model per region before playing: the mountains' slopes and the farms took most of it. Refuse only the fields and the yards, try a few spots in a cell, allow a slope.
- **A world's spacing alone leaves gaps** (exponential-like: the 90th percentile twice the median): the 40 s is kept in play by the director, which meets her when 25 s pass with nothing near.
- **An event log said once per change reads long gaps**: "near" said only when what was near changed made a 49.5 s gap of a run that was never 30 s without something. Say it again every 3 s while it lasts.
- **PR #36's review (2026-11-09)**: an id's bits must hold the grid's whole span (11 bits a 120 m cell left a third of the continent empty: 2500 cells across), and a test must reach every part (its lines lay near Brokenspire); a check near a cell's edge takes the next cell's places too; what a director makes it takes away (its satchels); "something near" is something to do (an emptied spot, a cleared nest stopped the director); a pile of found things is not a harvest ("take the bread"); one helper per rule (the pieces' laying, the things' rolls, the tier's kinds).
- **A memory reading of one run is not a measure**: `stream` read +1078 MB, then +119 MB in the same build (and +666, -191, +1638 before). Read it twice before blaming a change.

## The list of 2026-11-10's first phase

- **The encounter director sends nothing while anything is near her** (a point of interest, an animal, a monster within 45 m): on the plains something nearly always is, and a test waited 40 s for an ambush in vain. `ForceWildEncounter(<kind>)` sends one now.
- **An ambush hunts** (`ARDMonster::bHunting`, a minute): from beyond its noticing distance and past its leash; it comes at its kind's own chase speed (a slow one at 1.5 m/s).
- **A box that stops her must not be set on her**: the horse called or left where no spot beside her was found stood on her; its box waits until she is 2 m clear.
- **A speed's run-up**: at 5.5 times her speed the gallop needs a couple of seconds to reach it; measured over a whole 4 s run it read 5.04. Measure after it is up to speed.

## The list of 2026-11-10's sixth phase (`916`, `RD/RDWild10.cpp`, `888 houses10,tower10,farms10,travellers10`)

- **A pack's house scaled to its height shrinks its doors**: the village houses stand 13.6 m in their own units; laid at 9 m their 2.3 m doors would be 1.5 m. Enterable, they are laid at 0.8 (1.85 m doors) and the village's ring widened for them.
- **Python takes an `In` off a struct's names** (`InMin`, `InMax` are `min`, `max`), and **a bool and an array of one name are one Python name** (`bWildHouses` and `WildHouses` both `wild_houses`: the bool is `bWildHouseInsides`).
- **interactive.json holds Blender's y** for the hinges and the leaves' ways (the dungeon rules' note): a leaf's way goes into its width's sign.
- **A door that swings out at her shuts her out**: opened from 1.1 m, the leaf (1.5 m) swung into her place; it swings away from whoever opens it.
- **A mesh with no simple collision under the default trace flag is walked through**: the Lake Village barn and farmhouse (CTF_USE_DEFAULT, 0 simple shapes). Their mesh is their collision now.
- **A road a few metres wide is missed by samples 100 m apart**: a test that needs a road starts from a place that is beside one by design (the den).
- **A camp beside the road lay in a bean field**: a thing put off a road looks at its ground (field, water) first.
- **Picture a kit's pieces before trusting their letters**: the tower quarters' doorway is B (882's note put it at D, a small window); the wild tower's "doorway" was a window and she walked through its wall between the hidden colliders, while the test passed. A test that walks through a doorway must also look at it.
- **A floor on the highest ground under a ring stands over its doorway's sill on a slope**: the tower stands on that ground, a stone footing down to the lowest, steps from its doorway.
- **PR #43's review (2026-11-10)**: what replaces a mesh's collision must cover the whole of it (the third storey's kept walls had none); a prop that holds a light hands the light over to whatever takes its place (`SetProp` ends the lantern); a nearer door wins over a person; the draws of one call keep their order when split (MSVC: right to left); a search over a world's cells is kept for the cell she is in.

## The farmsteads' designs (the list of 2026-11-11's fourth phase: `RD/RDWildFarm11.cpp`, `919`, `blender_numpy/farm_designs.py`, `888 farms11`)

- **A layout made as data is checked before it is built**: `farm_designs.py` refuses a design whose footprints come within 2 m, that leaves the yard's 31 m, or that blocks a door's 4 m; look at its contact sheet from above (a scratch picture of the 60) before the stage.
- **A wild container is a chunk door with `bBox`**: its find, prompt, F and tick are the doors' (`WildDoorNear` passes an opened one by, the houses' `door|` lines leave them out). Its key goes into `WildKilled` (saved) above every other range: `(1 << 40)` + farm id x 64 + n for a farm's, `(2 << 40)` for a house's; the kills are place x 16 + n, the points' negative.
- **Build a test's thing so it can be taken away**: a farm built by `SpawnFarmDesignAt` keeps every component it made and its ranges of the chunk's doors, houses and clears (`FRDWildFarmRec::Comps`, `Door0`..`Clear1`); `RemoveWildFarm` takes them out, so all 60 designs are measured in one play without piling up.
- **A small room's middle must stay free**: the test walks her to a building's middle; a coop's hay and its hens stood her 44 cm up. A low box an animal carries is never stepped up on (`CanCharacterStepUpOn`).
- **A prop scaled for the yard is too big indoors**: the cart filled a barn.
- **A picture from a raised point is a fall**: falls hurt (886); put her on the ground for a view and step back far enough (42 m for a yard).
- **PR #49's review (2026-11-12)**: a thing of many pieces made in one frame is instances, one component a mesh, material, collision and visibility (`WildFarmInstance`), not a component a piece; a rule kept in two places says the same (the door's place across its wall in `farm_designs.py`'s `door_y` and `RDWF11DoorY`; the containers' hinge sign `RDContainerSign`, the dungeon's too); keys counted per thing made, never by a part's index times a slot count; a part turned its own way records its turn for whatever reads it back (the animals' pens); one rule's old copy goes when the new one covers it (the fixed layout is the default design); taking a range out of a shared list moves the ranges after it.

## The meadows, the leaves and the director's new kinds (the list of 2026-11-11's fifth phase: `920`, `RD/RDWild11.cpp`, `888 meadows11,events11`)

- **A struct read out of a list from Python is a copy**: `890`'s wind set the swaying materials on copies of the biomes' foliage and wrote nothing back; for nine days no grass in the wilds swayed, and nothing measured it. Write the element back into its list and the list back into its owner (`fol[i] = F`, `bios[i] = B`), then read the result from the level (the test reads the grass instances' material).
- **A pattern's strength is a spread, not a count**: 43 trees round a spot with 95 % of cells bare "had groves" by eye, but the counts per cell were spread 1.4 times a random one's (barely clustered): density raised to 120 a hectare, 3.1.
- **Measure a debris mesh before naming it**: a "branch" 6 m standing, "logs" that were stacks, branch cards 2 cm thick flat on the ground.
- **Screen an effect against the base**: the base leaves (`WildLeavesFx` already on) showed in every candidate's picture; `SetWildLeavesFx` swaps the one system for the screening. Of six leaf systems only one read as leaves blowing at play's distance (the first choice was a few dark specks): look at the full-size crops, not a contact sheet.
- **A test's log read by count misses lines**: the encounter lines are kept to 400; take the lines newer than the step's start by their time.
- **A pile in reach takes F before a person**: a test that speaks to someone where an earlier event left things takes them up first (`events11`'s refugee).
- **The port's coast** is in `graymourne.md`'s rules (the sea lifted to the harbour, every target that eases to a town's height less the lift).

## Swimming (the user's of 2026-11-12: `RD/RDSwim.cpp`, `921`, `887 materials`, `884 swim12`)

- **Read a claimed rule in the geometry before keeping it**: the "invisible wall that keeps her out of the deep sea" was a flat sheet 3 m over the water past 8 m deep; nothing stopped her there (she would have walked off the floor's edge to the sea bed). The swimming floor follows each corner's depth (to 145 cm under the face), so there is no step between wading and swimming either.
- **A body held under an opaque face is gone**: by her pelvis 22 cm down, a flat swim loop's whole body lay under the water (the first pictures showed only the wake); by her head over the face, some rigs' flat bodies lay on top of it. Swimming along, by the pelvis just under (6 cm); treading, by the head over (18 cm). Ease the mesh slowly: chasing each stroke's bob moved the body against it. Read the medians over the strokes, not one moment.
- **Python names drop "Kismet"**: `UKismetMaterialLibrary` is `unreal.MaterialLibrary` (as `KismetSystemLibrary` is `SystemLibrary`); the step stopped half way on `unreal.KismetMaterialLibrary`.
- **A batch retarget takes the registry's records** (`eal.find_asset_data(path)`), not loaded clips: "Cannot nativize 'AnimSequence' as 'AssetData'".
- **Measure a sound against its own moments, the game's others silent, its set on and off**: the town's own bed (people, fires, wind) sat at -27 dB, and bursts round -23 dB came from no sound set (they stayed with every set at 0), so a whole recording's level showed a splash as +0.3 dB. A recording's loudest 30 % of tenth-second windows, the set on against off, showed it (+12.5 dB); a before / after window round each event fails for strokes 0.75 s apart (each "before" is the last stroke's sound). Wait until the recording can be opened: it was still being written after the stop.
- **A long session runs the machine short of memory for brokenspire's play**: a test was stopped with 1.2 GB of 32 free (the editor 20.7 GB, its map's load 115 s). Restart the editor before the swim test, and after a stage that loads brokenspire.

## The big map and the mouse (the list of 2026-11-12's first phase: `RD/RDList12.cpp`, `RDWildHUD.cpp`, `888 list12`)

- **An overlay cannot hide what is under it on a see-through backdrop**: a cut in the backdrop's colour drawn over the map past the scroll's torn edge stood as a black square round the scroll (the backdrop lets the world show through). Draw the map only where it may show: inside the scroll, at insets measured on the edge's picture (`bs_scroll.py` prints them). Measure it with two pictures of one screen, the map moved between them: past the edge nothing may change.
- **The pointer is not up by itself**: the map's drag and wheel code was there, but the game's own input mode keeps the mouse captured and hidden. Raise it while the map wants it (`WantsMapPointer`) and again if a menu put it down; the combat code reads the mouse buttons as raw keys, so an input context consuming them does not stop a strike: gate the combat input itself.
- **A click is a press let go near where it began**: a drag moves the map; the click acts on the press's point.
- **A teleport puts her where she can stand**: (PR #54's review) the wilds' ground dry and not too steep (the nearest such within 200 m), a town's or a dungeon's floor where her capsule fits, within 2.5 m of her own height (traced down floor after floor: the first hit was taken for the floor unless 4 m over her, and a vault's top put her on the dungeon's roof).
- **The real mouse over the play window pulls the game's pointer**: a Slate press became a drag when the pointer jumped to the resting real mouse (the same spot every time in `RDMAPPOINTER`'s log); a retry at the same pixel then hit a map the drag had moved (8 km off). Test a click's outcome by calling it at its screen point; test the pointer's path through Slate, and say when it was spoiled.
- **Only `save_*` slots are listed** (`URDSaveGame::AllSlots`, with `save` and `autosave`): a test's save under another slot name is written but never shown.
## The dungeons' keys (2026-11-08b, phase 3: `RD/RDKeys.cpp`, `905`)

- **PR #31's review (2026-11-08)**: something given once a game (a key from a boss who never comes back) is the player's when it is given, not when its pile is taken (a death or a door taken at once lost the chain); a new rule needs a way in for the saves made before it (the keys from the counters of what she has done); a test's switch must never be a saved counter (it went into the autosaves); a table read every tick is parsed once (the chain, the tiers' towns at Init); a reveal that found nothing to reveal is not marked done; a tier past a table's last needs the table's last (the harvest's parts).

## The high clouds that turned (2026-11-10, the shipping game: `RD/RDSky.cpp`, `890 sky`, `884 skyspin`)

- **A sky layer turned about the zenith reads as a disc spinning overhead** against layers that drift in a straight line (the volumetric clouds); a texture panned along a sphere's U is a turn about the zenith too. Every layer moves the way the others do: the high clouds are a flat layer drifting along the clouds' wind, and their dome never turns.
- **`connect_material_expressions` fails silently on a wrong pin name**: the noise node's position pin is "World Position" (`get_material_expression_input_names`). Joined as "Position" nothing was joined and the noise read the world's centimetres: a grain over the whole sky, unchanged when the layer's tile was made 10,000 times wider. Assert the connections a material depends on.
- **`TextureExporterPNG` on an HDR texture asserts and takes the editor down** (`SupportsTexture`, the engine's `T_CloudPattern`): don't export a texture to look at it without knowing its format.
- **Motion in two pictures is measured part by part** (`blender_numpy/sky_shift.py`): phase correlation of the whole on soft cloud shapes gave weak, disagreeing peaks; a least-squares search per part gave one shift for all within 1.6 px.

## The far land as the ground, and its haze (2026-11-10, later: `RD/RDSkyFar.cpp`, `RD/RDSky.cpp`, `RD/RDTownDay.cpp`, `884 horizon`)

- **A strip at the horizon is told apart by measuring down a column** (`blender_numpy/sky_horizon.py`): the sky darkened smoothly to (126, 181, 204) and jumped in one row to a flat (183, 194, 208) with hill-shaped tops: land, not sky. Measure each change as the land against the sky just over it, at several hours: the fog's fixed daylight grey made it +22 at noon and +110 at 17:30.
- **What a far quad holds, it holds over kilometres**: one lava sample spread a glow over a whole hill, as a lava quad and again as the ground material's own glow from the colour's alpha; a lake's level held at a dry corner would float a sheet over the lowland. The far land has no lava, and its water goes down under a dry corner's ground.
- **The sky atmosphere's aerial perspective follows the hour; a fog colour does not**: the fog lit by the atmosphere (`HeightFogContribution` up to 8, its own colour off) turned the near town blue and stayed blue at dusk. The clear air's haze is the atmosphere's; the height fog is capped low there and rises with the weather's and the port's fog, and dims and warms with the sun low.
- **PR #45's review (2026-11-11)**: the far land's water lay under the chunks too, sunk only its ring's few metres: under a
  chunk's lake deeper than that it was a second surface between the chunk's water and its bed. No far water where the chunks
  lie or may come before the ring is made again (`WildDropM`, half a chunk, `FarLandRebuildM`: 81 quads left of 83). The far
  land and the chunks take a ground vertex from one function (`RDWildGroundVertex`, RDWild.h), or a change to the rock, snow
  or crops' encoding would have to be made twice. A material's parameters that a tick's arithmetic depends on are set in the
  same tick (the drift wrapped at the live tile, the material repeated at the one set at start). A table's count is one
  constant (`ARDDungeonGenerator::NumWeathers`, `WeatherCloudless`), not literals in each file. A test step that sets an
  engine console variable or hides her puts it back in a `finally`.
- **A probe's setting the game resets four times a second is set every frame, or made the game's own**: the fog's density and colour are written by `ApplySky7` and `ApplyDayNight`; the probe's later rounds set generator properties the game applies.

## The far land (2026-11-10, `RD/RDSkyFar.cpp`)

- **Past the chunks' 2 km nothing was drawn**: a ring of coarse land (0.85 to 80 km, 17 rings of 192 points from `Wild->Sample`, under the ground so the chunks draw over it) closes the horizon; made again once she has gone 150 m (12 ms). PR #39's review: a ring that starts where the chunks end leaves a gap behind her until it is made again (its inner edge must be the chunks' reach less the distance it is made again at), and one that lies under the chunks shows over a valley between two of its points unless it is sunk by its spacing (4 m and 6 % of the way to the next ring). Its components are `Transient` without Blueprint flags: a test finds them by name (`RDFarLand`, `RDSkyHigh`, ...).
