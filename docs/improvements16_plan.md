# The list of 2026-11-22: the plan

The user's list is [improvements16.txt](improvements16.txt): performance measured before and after, level of detail and Nanite in the wilds and the cities, the caves rebuilt with the Hyper Cave Building Toolkit and given treasures of their own, a long list for Heaven and its fortress, and the instructions on its last line. This plan breaks it into phases, each one PR: built, tested with a step of its own in a level's scripted test, reviewed (`/code-review high`), its fixes tested again, then merged, in the order below. After the last phase the Shipping package is built (a full cook) and run. An independent review of the first draft found 21 problems (terrain steps that do not nest in a chunk, measures that would not compare like with like, the caves' movement and the kit's Blueprints in a package, PCG not set up, Nanite after the interiors, the street lamps culled dark, phases too large, the package left to the end); this version answers them.

The user's choices (one question round, 2026-11-22):

- **Line 177** ("the city of heaven should have typical", cut off): **both** typical modern services (a clinic for the healer, a gear shop for the smith, a grocery, a bank, a hotel for the inn) **and** typical city ambience (people on the pavements, the city's sound, billboards, neon at night).
- **Interiors:** **all three** options: each building's interior in components of its own (so the engine's occlusion culling hides what walls hide), Nanite on the furniture and props, and the game's own rule hiding an interior until a door of it is open or she sees in through a window (its townsfolk with it).
- **Merging:** each PR is merged after its review, then the next begins; the Shipping package after the last.

Stages go under `944` (`944_improvements16.py <part>`, as `934` did for list 15); the caves' rebuild is `945`, Heaven's stages `946` (the city) and `947` (the fortress), the tower level `948`. C++ goes in new files `RD/RDList16*.cpp` (the caves `RD/RDCave16*.cpp`) where it is new, and in the existing files where it changes a rule. Each feature has a step in a level's scripted test (`868` the castle and the dungeons, `884` the towns, `888` the wilds) with a name of its own and a stated measure, and its part of the level's document; what is not built or not measured goes in `TODO.md`. CLAUDE.md's stage list and order, and the rules files, are updated where a phase changes what they say.

**The stages' order:** every new item stage (the caves' treasures, Heaven's goods) runs after `910`, `905`, `911`, `918`, `925`, `928`, `929`, `937`, `938` and `943`; `945` (the caves) and `947` (the fortress) run again after any stage that writes the castle's or brokenspire's monsters, items or heroes, as `935` did. CLAUDE.md says so.

## What the code does now (the survey of 2026-11-22)

- **The wilds' ground:** every 250 m chunk is a 2 m grid (126 x 126 vertices, 31,250 triangles) at any distance, about 64 chunks out to 1 km (2 million triangles), each with a full-resolution collision mesh of its own beside the drawn one (`RDWildGame.cpp` `StepWildBuild`). The far land rebuilds on the game thread every 150 m. Trees cull at 1.1 km (never, in practice), rocks at 600 m. No wild mesh is Nanite but what its pack shipped so.
- **The towns:** one plain instanced component per mesh for the whole town (`ARDSection::AddPiece`), so a component's bounds are the town's; no cull distances but the grass's. The project renders with Nanite, virtual shadow maps, Lumen with hardware ray tracing and Substrate (`DefaultEngine.ini`). Point lights draw to 90 m; hearths, braziers and forges cast shadows; Brokenspire has about 611 lights. Townsfolk tick every frame (update-rate optimisation on, pose only when drawn); Brokenspire 99 to 129 people, Graymourne 163.
- **Heaven:** 84 cars, each a Movable mesh with full collision moved every frame; the shield dome a translucent sphere never culled; the street lights one pole in three at 220 cd, 7.4 m up (about a sixth of a wall torch's light on the ground); every building one room (offices 9 to 15 m tall and hollow, skyscrapers a 3 m lobby under a stack of scenery); the town's medieval signs, map symbols, containers, carts, hay, braziers, torches and goods; shops are storerooms whose clerk sells nothing; cars U-turn at a street's end and pass through each other at crossings. Kratos Aurorim Research is 33 m tall beside skyscrapers of up to 101 m, and its hall's security door is the fortress's way in.
- **The caves:** a Save As copy of the castle with the Cave theme's rock on the castle's pieces: the dungeon's rooms and hallways on the dungeon's tile grid, which every monster's path, the maps, a set's progress and its saved state are built on (there is no navmesh in the game).
- **Loading:** no loading screen anywhere; a level opens bare and its textures stream in in front of her. Fast travel and loads build a town in one frame. Coming back from a cave opens the wilds' level, which builds Brokenspire round her before the load puts her by the tower's mouth.
- **The measures already there:** the HUD's FPS (`bShowFps`), the chunks' thread times (`GetWildBuildStats`), `884 cityfps13` (each city's square in the editor's play), the package's `-RDTownGo=` runs.

## Readings of the list

- **Performance "in all the cities, wilderness in all biomes":** measured in the **Shipping package** (what the user plays), the editor closed, full screen at the desktop's resolution and at 1920 x 1080, by a run of the game's own (`-RDPerf=<file>`, `pipeline/perf_mistward.ps1`):
  - each city's square and a street about 100 m off it, at noon and at midnight; each of the 29 biomes at its nearest site to Brokenspire (the biome under her feet checked; "not found" said if the put-down lands in another), at noon, plus a 30 s run of 150 m or more from there (the frames while the ground streams in); the castle's great hall and one dungeon's first hall (pack meshes the cities share);
  - each place settled 20 s after the world round her is built, then measured until both 15 s and 300 frames have passed (at most 45 s): the mean FPS, the 95th and 99th percentile frame times with the frame count, the game, draw, RHI and GPU thread times (where the build has them: a Shipping build that reads 0 for them says so, and they are taken from a Test package), and a picture of the place (`perf_<place>.png`);
  - the run's places (position, facing, hour, weather) are written by the BEFORE run and replayed exactly by the later runs (`-RDPerfPlaces=<file>`), and the game's graphics level and screen percentage are recorded with them;
  - the results go into `docs/performance.md` with a time stamp, under **BEFORE LIST16 changes** (phase 1), **MID LIST16 changes** (after the performance phases, before any new content: what the level-of-detail work alone gained) and **AFTER LIST16 changes** (phase 28, with the change from BEFORE per place).
- **"Is there a way to load textures before the game is displayed?"** Yes: the engine can be asked to stream every texture a view needs while a cover hides the world. The plan builds a loading screen with the engine's own (`MoviePlayer`, drawn while the map loads) followed by a cover held after the level opens, fast travel, a load or a respawn until the town and the chunks round her are built and the texture streamer has settled, logging each time it took and why it lifted; its cap is set from those times (5 to 8 s), not a guess.
- **The cities' table** is built as written, with these readings: point lights culled from 35 to 45 m with a fade and shadows only within 15 to 20 m, **except the street lamps** (Heaven's and the cities' lamp posts), whose glow stays drawn: they keep their light to 90 m without shadows, so an avenue is not black beyond 45 m (the user's own complaint of line 146); townsfolk at full rate under 15 m, half to 40 m, a quarter to 80 m, an eighth to 110 m, and beyond 110 m not drawn, their day kept by a logic tick once a second (never frozen); Heaven's cars' distance rules are built with the traffic (phase 23), where cars beyond 150 m move along their routes undrawn and cheaply instead of freezing.
- **Nanite in the cities** replaces the hand-set LODs for every opaque pack mesh and town building piece; a mesh that cannot be Nanite keeps generated LODs (LOD1 at the screen size of 80 m, LOD2 at 200 m). The same pack meshes stand in the castle and the dungeons, so those are measured and pictured too, and the trap outlines' overlay material checked on Nanite meshes.
- **Nanite foliage in the wilds:** UE 5.8's Nanite foliage (`ENaniteShapePreservation::Voxelize` for the dense canopies, plain Nanite for rocks and trunks), with the wind's displacement allowed for, on every biome mesh where it costs less than its instances with LODs (measured kind by kind, not only for grass).
- **Interiors, all three options:** Nanite first (phase 5), since Nanite culls each cluster against the depth buffer whatever its component's bounds; then the per-building components and the hiding rule (phase 7), each measured on top of Nanite: an interior is drawn when she is inside it, or a door of it is open or opening and she is within 40 m, or a window of it within 40 m has a clear line from the camera; otherwise its components, lights and people are hidden. The rule shows an interior a little early (from 45 m, or as she nears a door) so that the lighting of a room shown again has settled before she sees it; its pictures through a doorway in the door's first frames are measured, not its flags.
- **The caves:** "not the same as the dungeon procedural generation, not a dungeon with cave textures": a planner of its own lays rooms of the kit's sizes (small, medium, large, stairs) on the cave's tile grid by its own rules (organic, uneven, no blocks or straight halls), joined by winding tunnels whose paths are tile paths; the drawn shell is the Hyper kit's (its rooms' meshes, its tunnel meshes bent along the tunnels' splines, caps at the dead ends, the combined-mesh prefabs where they fit, its floors and roofs), so monsters, the maps, progress and the saves keep working on tiles. The kit routes tunnels by hand in the editor; the game routes them itself. Phase 8 begins with a spike in a Shipping package (one tunnel, one room, one PCG dressing: geometry, collision and PCG output checked), and builds the pieces in C++ (spline-mesh components with the kit's meshes, the rooms' connection points read from the kit's Blueprints once by `945` and kept as data) if the kit's Blueprints do not build in a package. The guide's steps are followed: the example map studied (its pieces listed and pictured by `945 study`), tunnels by size, rooms and caps at their ends and connection points, stairs between heights, combined meshes, PCG floor and roof dressing with its parameters, the kit's lights and god rays. The product page and its documentation were read when the plan was written; the video's frames and transcript are taken at phase 8's start (the Chrome extension was not connected when the plan was written; if it still is not, the report says so).
- **"These treasure types should be found in caves instead of the things that can be found in dungeons":** a cave's gear, rings, tomes and scrolls come from the caves' own table (the items below at the cave's tier); its potions, food, repair items and gold stay as now, and the Angel Token materials too. The dungeons are unchanged.
- **The treasures' details:**
  - deepiron: one tier above what the region's town smith sells;
  - fungi: glowcap for the darksight potion (she sees farther without a torch), grave-moss for poison resistance and the slow regeneration potion;
  - cave-pearl: a trade good, and the gem of the Ring of the Echo;
  - blind-fish oil: the torch and the ankh burn twice as long on it;
  - bat-wing leather: patches for light armour; crawler chitin: patches, and a repair item for medium armour;
  - geode shards: cut at the librarian's table into scroll inks or socket stones, the colour by the cave's region (each region's colour its own bonus); a weapon or armour set gets one socket, a stone set in it adds its colour's bonus;
  - old bones: rare, for a named weapon's recipe;
  - amber: an alchemy reagent, and a collectible (it counts in the region's fossil set);
  - frost quartz and sun-glass: by region, for the warm and cool gear's upgrades;
  - the shard blade is mended only with geode shards.
- **Armour:**
  - the spelunker's armour: quieter footsteps, read as monsters noticing her from a shorter distance (four fifths), and a little darksight;
  - chitin plate: heavy, with poison resistance;
  - the drowned knight's set: four pieces (helm, cuirass, gauntlets, greaves), one in each cave of a region, made into the set at the anvil; the whole set worn lets her breathe longer under water;
  - the deepiron sets: the existing sets' looks one tier higher;
  - all of them reuse existing fitted sets in new materials: a new body of armour would need fitting to all six heroes.
- **Breath:** the game has no breath today (she swims on the surface). A cave's flooded chamber has a passage under a low roof that she swims under water with a breath meter (15 s); the whole drowned knight's set triples it.
- **The charms:** the game has no amulet slot. A charm slot is added (inventory, HUD, save) for the glow-worm amulet and the cursed relics; the Ring of the Echo and the lucky stone are rings.
- **The lightless bow:** a shot from it does not turn the monster it strikes toward her while she is stealthed, and draws no shot trail.
- **The miner's pick "breaks cave rubble":** the caves lay rubble across side tunnels and caches; the pick's blow (or three of the Warrior's) clears it.
- **The tower's key:** the cave's deepest room holds it; at the broken tower's foot it opens a lift (a door in the base) to a platform at the top, a lookout (the map round it revealed, as the lookouts do) and a chest.
- **"Models built in Blender and imported":** a cave item with no fitting mesh in the packs gets one modelled by script in Blender (`blender_numpy/cave16_kit.py`), its icon and any texture from the InvokeAI server (`rdm4_ui_gen.py` / `rdm4_ui_cut.py`).
- **Heaven's buildings by height:**
  - up to 5 storeys (the apartments and offices) get walked floors with stairs and an elevator;
  - the skyscrapers and offices of 6 storeys or more take her through their door to the tower level;
  - Kratos Aurorim Research stays the fortress's way in (its hall's security door) and becomes at least one and a half times the city's tallest building.
- **Heaven's traffic:**
  - a road graph of lanes and crossings, traffic lights in phases, and stop signs at the small crossings;
  - each car has a driver with a goal tree: a job's address to reach, then lunch, errands, home and parking;
  - drivers choose routes over the graph, obey the lights, stop signs, right of way and speed limits, keep their distance and ease in and out;
  - buses run on two fixed routes, stopping at the bus stops, where townsfolk wait, board and get off;
  - drivers and passengers are townsfolk seated in the cars: the town's `AS_Town_SitTalk`, with drivers' arms set to the wheel's grip;
  - cars beyond 150 m move along their routes undrawn, collision only within 30 m, hidden beyond 200 m.
- **The skyscrapers' level** (`heaven_tower`):
  - entered by a tall tower's door;
  - its floors are generated from the tower's seed: an elevator core and stairs, offices, cubicle farms, meeting rooms, bathrooms, a data centre room, equipment closets, a cafeteria and a lobby;
  - its windows show the city as it stands round that tower, from cube captures taken before the travel at three heights (low, middle and high floors) at the hour she entered, kept by the game instance; the city is seen but not reached;
  - the elevators and stairs go between floors, and the lobby's doors take her back to the street before the tower.
- **The fortress's tiers 3 to 5, "a wider open world that uses the Alien Planet":**
  - the sections are open, with no walls or ceilings, on alien ground built by the game;
  - the ground is dressed at run time by the pack's PCG graphs where they can read it: a spike decides between the pack's graphs on a ground they can sample, our own graph built on the pack's subgraphs, or the pack's baked point data placed by the game;
  - the rocks and plants block the tiles they stand on;
  - tiers 1 and 2 are a modern building made from the sci-fi city packs, and the sun and sky change between the indoor tiers and the open ones;
  - the shut tiers are sealed outdoors by a force wall, not a grating.

## The phases

| Phase | What |
|---|---|
| 1 | This plan; the measuring run (`-RDPerf`), its places kept; **BEFORE** in `docs/performance.md` |
| 2 | Quick fixes: the summons on the wilds' minimap; the cave's teleporter straight to the cave's mouth; the loading screen and cover |
| 3 | The wilds' ground in levels of detail (2 / 4 / 8 m by distance, with skirts), collision only near her; the far land off the game thread |
| 4 | Nanite foliage in the wilds (kind by kind) |
| 5 | Nanite in the cities, the castle and the dungeons; LOD1/LOD2 where Nanite cannot go; the skyscrapers' shell |
| 6 | The cities' lights by distance (street lamps kept), the townsfolk's animation by distance, the dome drawn only from outside |
| 7 | Interiors: per-building components, the hiding rule, clutter culled; **MID** in `docs/performance.md`; a package smoke run |
| 8 | The caves: the spike, the video, the example map studied; the cave planner on tiles; the Hyper shell; collision; the walk |
| 9 | The caves: PCG dressing, lights and god rays, monsters, containers, the boss, the maps, the way out, rubble; a package run |
| 10 | Cave crafting materials and their recipes (veins, fungi, pearl and oil, leather and chitin, bones, amber, frost quartz and sun-glass) and the potions' effects |
| 11 | Geodes, inks and socket stones (the sockets) |
| 12 | Cave weapons (the pick, the shard blade, the lost adventurers' weapons, bone weapons, the lightless bow) |
| 13 | Cave armour (spelunker's, chitin plate, the drowned knight's pieces and set, deepiron sets); breath and the flooded chamber |
| 14 | The charm slot; the Ring of the Echo, the glow-worm amulet, the lucky stone; the cursed relics and the temple's lifting |
| 15 | Fossils and relics, tablets, cave paintings, the Angel Token from a cave's last boss |
| 16 | Caves and the open world: treasure maps, contract lairs, the found prisoner, waystone fragments, the tower's key and its top |
| 17 | Gold and trade goods: gems, old coins, the collector, dragonglass and blackstone |
| 18 | Heaven, first fixes: the street lights, modern signs, modern map symbols, the sleepers on their beds, Kratos Aurorim Research's tower |
| 19 | Heaven's streets: markings, crossings, traffic lights, stop and street signs, parked cars, the carts and medieval leftovers replaced |
| 20 | Heaven's buildings: storeys, stairs, elevators and roofs |
| 21 | Heaven's shops as shops, the modern services, modern containers |
| 22 | Heaven's goods and life: modern food, items and icons, its own stock; people on the pavements, the city's sound, billboards and neon |
| 23 | Heaven's traffic: the road graph, drivers with goal trees and the traffic laws, buses with routes and passengers, the cars by distance |
| 24 | The skyscrapers' level (`heaven_tower`); a package run |
| 25 | The fortress's defenders: soldiers, medics, drones, mechs and aliens in variants |
| 26 | The fortress's tiers 1-2 as a modern building |
| 27 | The fortress's tiers 3-5: the Alien Planet open world; a package run |
| 28 | **AFTER** in `docs/performance.md`; the Shipping package (full cook) and its runs; the final report |

### Phase 1: the plan and BEFORE

- `RD/RDList16.cpp` `-RDPerf=<file>` as read above (the wilds' level: the cities and biomes; the castle's and a dungeon's level: their first hall), `-RDPerfPlaces=<file>` replaying a run's places.
- `pipeline/perf_mistward.ps1` runs a package at the desktop's resolution and at 1920 x 1080 (the wilds' run, then the castle's and a dungeon's), keeps the player's settings and saves and puts them back; `blender_numpy/perf_doc.py` writes `docs/performance.md`. The raw lines are kept in `SourceArt/perf16/`.
- Measure: every place present or said skipped with why; the biome under her feet named; the thread times non-zero or said missing; two runs of the same build agree within 10 % at each place (else the settling is lengthened and the run repeated).

### Phase 2: quick fixes

- **The summons on the wilds' minimap and big map**, drawn as the dungeon maps draw her allies; `888 allies16` counts the marks against the allies.
- **The cave's teleporter**: the trip from a cave opens the wilds' level without building Brokenspire round her first (a pending load to a place outside Brokenspire skips the home town's build); `868 caveport16` reads where she stands after the trip (before the mouth) and that no Brokenspire section was built on the way.
- **The loading screen and cover** as read above; `884 loading16` / `888 loading16`: the picture at the moment the cover lifts against one 30 s later (their difference), and the cover's times and reasons over ten trips.

### Phase 3: the wilds' ground in levels of detail

- A chunk's drawn grid by its distance from her: 125 cells (2 m) within 375 m, 63 cells (3.97 m) to 625 m, 31 cells (8.06 m) beyond, so every grid has vertices on the chunk's borders; a skirt hangs under every edge, covering the gaps where neighbours of two steps meet. A chunk crossing a ring is computed again on the workers and swapped in place (the old one drawn until the new is ready).
- Collision only for the chunks within 500 m (5 x 5), at 2 m from the samples; fast travel, the map's teleport and `rd.GoTo` build theirs before she is put down, as now.
- The far land's rebuild moves to a worker.
- Measures (`888 lod16`):
  - the triangles of the loaded ground before and after;
  - no crack: rays from above along the real meshes' seams must hit ground;
  - every moving character (her horse, road travellers, roamers, the director's spawns, the herds' animals) stands on collision;
  - the foot gaps of trees and rocks at 400 to 600 m;
  - roads in pictures of the far ground;
  - the hitch of a swap (ray tracing's rebuild included);
  - the frame times while running 1 km;
  - `RDWildProbe` unchanged.

### Phase 4: Nanite foliage

- `944 nanite_wild`: every biome mesh (174), each kind made Nanite (trees and bushes `Voxelize`, rocks and logs plain, the wind's maximum displacement set) only where its measured cost is lower; materials' `used_with_nanite` (and `869` for the package).
- Measures: each biome's frame time (the perf run's biomes, two packages); pictures of each kind near and far (no leaves cut off by the wind).

### Phase 5: Nanite in the cities

- `944 nanite_town`: every opaque mesh the town pieces use (the Town, Holy, Forge, Port, Mage, Heaven, Lab, Modern pieces and the furniture), Heaven's merged boxes and cars; meshes that cannot keep generated LODs; the skyscrapers' upper floors a simplified shell never culled before 1 km; `869` sets the materials' usage for the package.
- Measures: the pieces' Nanite state listed; each city's, the castle's and a dungeon's frame time; pictures of each place against BEFORE's (none missing or black); a trap's outline drawn on a Nanite mesh.

### Phase 6: lights and people by distance; the dome

- Lights in towns: culled from 4500 cm with a 1000 cm fade; shadows only within 18 m of the camera (a pass four times a second, with 2 m of hysteresis); the street lamps as read above; flicker as now.
- Townsfolk and town animals by distance as read above.
- The dome drawn only while the camera is outside its sphere.
- Measures (`884 dist16`): counts of lights casting shadows and of people drawn, ticking and at their logic tick, at three places in each city, against their distance; a resident 200 m off still reaches work by the hour; a night picture down an avenue (its brightness between lamps); a picture from inside the dome; each city's frame time.

### Phase 7: interiors, then MID

- `AddPiece` batches a building's interior (its floor, furniture, props, lights, containers' bodies) by building and mesh; the shell and the outdoors as now. The hiding rule as read above (ten times a second); small clutter (cups, books, candles, food, debris) culled at 25 m.
- Measures (`884 interior16`):
  - the GPU time with option 1 alone, option 3 alone, and both;
  - pictures through an open doorway in the first frames of the swing, against the same picture taken 2 s later;
  - none of a shut house's interior drawn from the square.
- **MID** in `docs/performance.md`.
- A package smoke run (Nanite in a cooked build).

### Phases 8 and 9: the caves rebuilt

- Phase 8:
  - the spike, the video and the example map, as read above;
  - `945`: the cave level keeps its key, tier and switches;
  - its generator is a cave planner on the tile grid (`RD/RDCave16.cpp`): 12 to 30 rooms by tier, winding tunnels as tile paths (loops a fifth of the joins), and stairs rooms where the floor's height changes. Each tile has its height, and the monsters' paths read it;
  - the Hyper shell is laid over the plan, with nothing overlapping (each room's box and each tunnel's sweep tested);
  - collision under every walked tile;
  - the cave's state is saved under its key as before (an old cave save starts that cave anew; the report says so).
- Phase 9:
  - the kit's PCG dressing (PCG and `PCGGeometryScriptInterop` enabled in `claude_ue5.uproject` and `Build.cs`, the rooms' meshes readable on the CPU for its sampler, generated under the loading cover and timed);
  - lights: torches and lanterns at the tunnel meshes' sockets, and god rays where a room's roof has its hole;
  - the tier's monsters in rooms and tunnels, containers by the walls, the boss in the deepest room;
  - the way in and out, the maps (rooms and tunnels drawn from the tiles), rubble across side tunnels;
  - a package run.
- Measures (`868 cave16`):
  - every room reached on foot: she is walked along the tile paths with `add_movement_input`;
  - monsters chase her through a tunnel's bends;
  - no hole in the shell: rays from each tunnel's centreline every 2 m in 16 directions must hit cave rock within the tunnel's radius, and rays down must find floor at every step;
  - no blockage: a capsule swept through every tunnel;
  - the boss in the deepest room;
  - the frame times and the PCG's time;
  - pictures of each kind of room and tunnel lit.

### Phases 10 to 17: the caves' treasures

- Items, recipes and places from `SourceArt/caves/treasure16.json`; icons from the InvokeAI server (started in the background a phase ahead); meshes from the packs where one fits, else `blender_numpy/cave16_kit.py`; the caves' table as read above (phase 10 on); every new item on every map of the game (as `928`).
- Each phase's measure (`868 cave16_<part>`, `888 cave16_<part>`) reads each item found in a cave, each recipe made, and each effect on the thing it changes:
  - darksight: the view distance without a torch;
  - the oil: the torch's and the ankh's burn time;
  - poison: the damage resisted;
  - the socket: the bonus applied;
  - the pick: the rubble gone;
  - the lightless bow: the monster not turned toward her;
  - the breath: its seconds;
  - the echo: its pings against the monsters near her;
  - the amulet: the light at her;
  - a curse: its cost taken, and the temple's lifting;
  - the fossil set: the trade;
  - the painting: the region's caves on the map;
  - the fragment: the travel;
  - the tower: its top reached, and its map revealed;
  - the collector: his price;
  - the smith: the only one who works dragonglass.

### Phases 18 to 24: Heaven

- Phase 18:
  - the street lights' lamp heads measured on the mesh, every pole lit at night and off by day, with an emissive glow drawn to 90 m;
  - signs on a modern board (a lit panel) in a modern face (`bs_signs.py --modern`);
  - the town map's symbols for Heaven drawn from a modern set made on the InvokeAI server;
  - the sleepers laid on the mattress as measured on the bed's mesh (not its simple collision);
  - Kratos Aurorim Research as read above.
- Phase 19:
  - lane lines, centre lines, crossings and stop lines (the packs' decal meshes, or our own);
  - traffic lights with phases and their lamps lit;
  - stop signs and street-name signs at the crossings, and district signs;
  - parked cars along the kerbs and in lots;
  - the medieval carts, hay, logs, braziers, torches, fireplaces and candles in Heaven replaced by modern things: cars, trailers made in Blender, bins, lamps and ceiling lights.
- Phase 20: storeys with floors, stairs and an elevator (a platform she rides) to each floor and the roof, in the buildings of up to 5 storeys; the per-building interiors of phase 7 carried to each storey.
- Phase 21:
  - shops as shops: rows of shelves full of goods, a checkout, and a clerk who sells the shop's stock;
  - the modern services (clinic, gear shop, grocery, bank, hotel);
  - modern containers (lockers, filing cabinets, fridges, safes, toolboxes, dumpsters), each a body and a moving part, its door split off in Blender where a pack's mesh is one piece.
- Phase 22: modern food, drink, medicine and things with their own icons and meshes, and Heaven's stock its own; people walking the pavements, the city's sound, billboards, and neon lit at night.
- Phase 23: the traffic as read above.
- Phase 24: the tower level as read above, with a package run.
- Measures (`884 heaven16_*`):
  - the brightness on the street at night under a lamp and between lamps, read from a picture;
  - the signs' and symbols' pictures;
  - the sleeper's hips on the mattress, within 10 cm;
  - the facility's height against the tallest tower;
  - markings counted per street;
  - the lights cycling;
  - cars stopping at red and at stop signs (never crossing a red), and no two cars within 2 m;
  - buses stopping, and people boarding and leaving;
  - each storey reached by the stairs and by the elevator;
  - shop shelves full, and a purchase from the clerk;
  - every container opening;
  - the tower level's floors generated and walked, a window's picture against the city seen from the same point, and the way back.

### Phases 25 to 27: the fortress

- Phase 25 (`947 monsters`), by tier:
  - soldier variants: Sci_Fi_Characters_Pack_Vol_2's guards and defenders with their 43 clips, the Soldier pack's, and the Dystopia UE4 soldiers on the mech pack's clips, in their colour variants;
  - medics: Dystopia's, who heal their side;
  - drones: Military_Pack's combat drone, and Military_Drone's in colours;
  - mechs: Dystopia's UE4 mech and its clips;
  - aliens: Aliens_Warrior_Pack's fifth warrior with its clips, the others on compatible skeletons, and the Creatures_Pack's aliens.
- Phase 26 (`947 building`): tiers 1 and 2 as a modern building of the sci-fi city packs (SpaceColony2086, Office, Mega_City, Data_Center).
- Phase 27 (`947 world`): tiers 3 to 5 as read above, and a package run.
- Measures (`868 heaven16_*`):
  - each kind spawned, animated (its bones move), shooting or striking, hit and dying;
  - a medic's heal;
  - pictures of tiers 1 and 2;
  - tiers 3 to 5: walked between sections, their PCG instances counted, the rocks blocking their tiles, the frame times.

### Phase 28: AFTER and the package

- `-RDPerf` again in the final Shipping package, with BEFORE's places, at the same two resolutions; `docs/performance.md` under **AFTER LIST16 changes**, with the change from BEFORE per place.
- The package's runs: every level, the new cave and tower levels, and the wilds.
- The final report: what was built, what was measured, and what could not be.

## Order and parallel work

- The measuring run comes first: BEFORE must see today's code.
- The performance phases (3 to 7) come next. Nanite comes before the interiors, so the interiors' options are measured on top of it. MID then separates what they gained from the content that follows.
- The caves come before Heaven. Their treasures touch every map's items (a full re-run of the item stages), and Heaven's goods come after them in the same tables.
- Heaven's streets (19) come before its traffic (23), and its buildings (20, 21) before the tower level (24).
- Package runs follow the phases whose features can fail only in a cooked build (7, 9, 24, 27), not only the last.
- One editor only, and C++ builds need it closed, so the phases run one at a time.
- Work that needs no editor runs beside them in background agents, each started a phase or two before the phase that imports it:
  - the InvokeAI batches (the caves' item icons, Heaven's symbols, signs and goods);
  - the Blender models (`cave16_kit.py`, the trailers, the modern containers' doors split).

## Risks

- **Memory:** 32 GB of RAM and a 12 GB GPU; the full cook needs the 6 GB floor (`DefaultEditor.ini`). Nanite and the packs new to the game (MERIDIAN, Hyper, Alien Planet) add to the cook. The package's wild run measures memory over 20 minutes as before, and the perf runs are made with the editor closed.
- **Saves:** the terrain's levels of detail change no save. The caves' new layout starts an old save's caves anew. New items extend the item tables; old saves keep their items by name.
- **The kit's Blueprints and PCG in a package**: decided by phase 8's spike, with the C++ fallback named above.
- **What cannot be measured** (how a city sounds, whether traffic looks natural) is said so. The traffic is measured by its rules (stops, distances, routes), and pictures of it are taken.
