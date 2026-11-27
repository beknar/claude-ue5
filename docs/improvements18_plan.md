# The list of 2026-11-27: the plan

The user's list is [improvements18.txt](improvements18.txt):

- in Closed Structures, windows opaque and reflective where the building has glass (Heaven), and barricaded inside and out everywhere else;
- at least 20 designs of the cities' square stands;
- at least 20 designs of the town gates, one chosen when a town is first made in a game;
- the red scrub that floats over hills and mountain sides;
- giant beasts roaming the wilds now and then, some hostile, at the top of the area's tier or the bottom of the next;
- at least 20 designs of the wilds' item spots under a tent (tents, a wrecked house, and so on);
- the instructions on its last line.

This plan breaks the list into phases, each one PR. Each PR is built, tested with a step of its own in a level's scripted test, reviewed by an independent review agent, fixed, tested again and merged, in the order below. After the last PR the Shipping package is built and run.

An independent review of the first draft found 22 problems, and this version answers them. The main ones:

- giants out of her blows' reach (her targets are picked by the distance between capsule middles);
- new monster kinds moving every wild spawn's pick;
- a peaceful monster provoked by a dozen rules that take every monster for a foe;
- the gate's movers counted by index;
- the tents' new draws moving the camps' loot;
- plants seated on a ground that is drawn again as she moves;
- boards that leave gaps, and inner boards in the furniture;
- the village houses left out;
- designs merged into meshes from Blueprint pieces;
- tests that read back what the code wrote;
- two phases too large.

Conventions, as in lists 16 and 17:

- New C++ goes in `RD/RDList18*.cpp`; a changed rule in its own file where it can.
- Stages: `951_improvements18.py <part>` (`windows`, `stalls`, `gates`, `tents`, `giants`).
- A design (a stand, a gate, a tent spot) is data: a list of parts, each a piece of the generator's table (a pack mesh or a Blueprint, written by `951`), laid one by one. Nothing is merged into new meshes: the Docks' stands are Blueprints, merged meshes lose their instancing and often their collision, and a part list keeps each piece's own materials and Nanite.
- Each feature has a named step with a stated measure in `884` (the towns) or `888` (the wilds), run with `-Light`.
- No existing draw moves: a new choice is made from a hash of the town's or place's seed, never from a plan stream another rule draws from.
- What is not built or not measured goes in `TODO.md`. CLAUDE.md's stage list and the rules files are updated where a phase changes what they say.

## What the code does now (the survey of 2026-11-27)

**Closed Structures' windows** (`RD/RDList17e.cpp`, `RD/RDBuilding17.cpp`, `RD/RDList17f.cpp`):
- From outside, every window of an enterable building has an unlit pane with a picture of a room of its kind, glowing at night when the building is lit (`TickPanes17`, `M_B17_Pane`, 55 pictures). The wilds' farmhouses have the same panes (`AddWildPanes17`); the village houses (one pack mesh each) have none.
- From inside, the building level shows a pane per window with a cube of the street captured on entry (up to 40 cubes of 128 px, about 0.8 MB each, and one of 512 px).
- A building's glass: Heaven's styles 7 to 9 (`TownBld.Style >= 7`) have glass window pieces (`Modern.WallWindow` = `SM_HV_Window`, `MI_HV_Glass`: dark, metallic 1, roughness 0.06). Styles 0 to 6 are taken to be open frames; phase 3 checks each style's window piece for a glass material.
- The boarded houses board their ground-floor windows with `Town.Planks` (`SM_Wooden_Planks_B`) 14 cm out, with a collider (`RDTownPlan.cpp` 1477-1481). Nothing boards a window inside.

**The square's stands** (`RDTownPlan.cpp` 1042-1050 and 2097, `RD/RDList17b.cpp`):
- Twelve stands a square, each with a trade of its own. Every medieval city's stands are the three `Town.Stall1-3` pieces: Medieval_Docks' `BP_MarketStand_01-03` (actor pieces). Heaven's are three kiosks made from boxes (`950 stalls`).
- The old four draw their piece from the outdoors stream (`R.RandRange(0, 2)`), the new eight from a hash of their place.
- Everything round a stand assumes about 2.6 m square: the blocked tiles, the 420 cm spacing, the keeper 2 m behind, F within 260 cm.
- Packs with market pieces: Medieval_Docks (stands, cart, cloth in three colours, crates, barrels, tables, weapon stand, fruit), RiversideEuropeanVillage (`SM_StallA/B`, fabric, four prefab stalls), Viking_Village_Props and Castle Kit (`BP_StorageMarket_01a-f`), ModularWoodenBuildings (awnings), City_Assets_Kit (awnings, canopies).

**The gates** (`RDTownPlan.cpp` 1890-1959, `RD/RDTown7.cpp` 127-165):
- One gate for every city: `Town.Gate` (`SM_Main_Gate_03a`) built as a lifting portcullis (`TownGateWorks`, not themed: Heaven has the same), in a 4 m gap of the wall (`GHalf` 202) with a stretched lintel over it, two levers beside it.
- What depends on its place: the guards, the stable, the flat ground round it, the road out, the walk-in point. Nothing depends on the gate's looks beyond the 4 m gap and its height.
- A town's seed: the wild towns' from the world seed (`Hash(i, 0, Seed)`), Brokenspire's drawn once a game (`GI->TownSeed`); both saved. Each town has a saved record (`FRDTownSave`, by name).
- Gate meshes in the packs: Castle Kit's `SM_Main_Gate_01a-04a` and `SM_Gate_Door_01a-f`, CastleofEternalMist's gate, DwarvenCitadel's gate kit, BoneTemple's and Cemetery's gates, City_Assets_Kit's big gate and boom gates.

**The floating scrub** (`RDWildChunk.cpp` 292-346, `biomes.json`):
- Bushes stand upright (no `a` flag), on slopes up to 30 degrees, sunk 3 cm: on a 30 degree slope a bush 0.5 m wide hangs about 29 cm clear on its downhill side.
- Far chunks are drawn on a 4 m or 8 m grid past 250 m (`RDList16c.cpp`), while plants are placed on the 2 m grid: on a convex slope the drawn ground lies below them.
- The red one is most likely bearberry (`SM_Bearberry_02`, `MI_Bearberry_Atlas`), in the mountains and cold biomes by the list 7 extras; the hills' `Old_Windmill SM_bush` (`MI_desert_bush2`) is the other candidate. Not yet seen in a picture.

**The wilds' beasts** (`RD/RDList15j.cpp`, `RD/RDWildPoi.cpp`, `RD/RDMonster.cpp`):
- Named roamers walk a ring in 60 % of the region cells, 4 tiers above the region's, with 2.5 times the hit points, at their normal size.
- `ARDMonster::Empower(Tier, Hp, Dmg, ScaleMul, Named)` scales the capsule, mesh and reach with `ScaleMul`, and keeps the feet on the ground; the wilds always pass 1.
- Hit points and blows by tier come from `tier25.json` (`TierHealth`, `TierBlow`: past tier 5, x1.12 and x1.09 a tier).
- Every `ARDMonster` is hostile; the wild animals (`FRDWildFauna`) never attack.
- Big models: the Fantasy Elephant (7 m, and one with a tower), the Fantasy Dragon, the Rock, the Nasty spider, Titan, Hunter, trolls.

**The tents** (`RD/RDWildPoi.cpp` 57-107, `poi.json`, `biomes.json` 143):
- The item spots are the points of interest `abandoned_camp` (in every biome, the commonest) and `bandit_cache`: a tent at the spot, the pile 1.2 m along world X, a campfire and logs.
- The tent is one of four meshes (`tent1-4`: Hive_Sherwood `SM_Tent_A/B`, Wildlands `SM_tent_1/2`), all scaled to 3 m.
- Unused tents in the packs: Hive_Sherwood `SM_Tent_C/D`, BoneTemple's eight fabric tents, FantasyCastle's, MC_Environment's two, StylizedVillage's, `SM_N13_FrozenTent`.
- The layout language (`LayWildParts`, `RDWildRuin12.cpp`) already lays whole designs from data: pieces by prefix, rings, rectangles of walls, scatters, mounds, a container that keeps its looted state (`box=Chest`).

## The phases

### Phase 1: this plan (PR)

### Phase 2: the floating scrub

- **First find the plant and the cause, in pictures**: `888 scrub18` stands her on a hill and a mountain side at noon and takes pictures near (50 m) and far (300 m, 600 m). It names the red plant by measuring the candidates' base colour (`SCS_BASE_COLOR` captures of each bush mesh alone). The same views are taken with each suspect switched in turn: `rd.WildLod 0` (the ground drawn on the 2 m grid everywhere), Nanite foliage off for the plant (`r.Nanite.Foliage 0`), the sway off. The cause is the switch that makes the float go away in the picture.
- **Measure the float**: for every bush instance in each of the three rings of the drawn ground (2 m within 250 m, 4 m within 500 m, 8 m beyond, to the streamed reach), the gap between its lowest point on the downhill side (its bounds' corners turned with it) and the drawn surface under it (a complex trace on the chunk's drawn mesh). `GetWildFootGaps16` is extended to every ring and every instance.
- **Fix by what the measure finds**, among:
  - a bush sunk by its radius times the slope's tangent (its downhill edge at the ground), capped at 25 degrees unless its entry says otherwise;
  - the coarse ground never under the fine one: each coarse vertex takes the highest fine height of the cells it stands for, so a plant seated on the 2 m grid never floats over a coarser drawing. The plants are not moved when the chunk is drawn again (a chunk's step changes as she moves);
  - the plant's height on a quad by the drawn triangle's split, not a bilinear blend.
- **Measure**: the largest gap per ring under 5 cm on hills and mountains, before and after in the same run (`rd.Scrub18 0` for the old rules); the near and far pictures before and after; her walk unchanged (the collision ground is the 2 m grid, untouched).

### Phase 3: Closed Structures' windows: glass or barricades

- **Glass** (Heaven's buildings, `Style >= 7`): Heaven's glass (`MI_HV_Glass`) is already dark, metallic and opaque, an 8 cm box seen from both sides. Closed Structures only stops covering it: no room picture outside (`TickPanes17` skips them), and inside no street cube and no capture (the town's own window piece stands round the building level). A window piece of any other style found by its material to hold glass is treated the same.
- **Barricades** (every other closed building in a town, the wilds' farm buildings and the village houses): each window boarded over its whole opening, outside and inside.
  - The opening of each style's window piece (styles 0 to 6, `WallWindow` and `WallWindow2`) and of each village house mesh is measured once by a grid of traces through the piece, and written to `SourceArt/list18/windows18.json` by `951 windows`. The village houses' windows, baked into their pack meshes, get their places from the same traces.
  - The boards (`Town.Planks` and two more plank meshes of the packs, for variety) are sized and laid to cover the opening with a small overlap: a few horizontal boards and one or two across, turned by a hash of the window.
  - Outside: laid with the building's shell in Closed Structures, the window piece's own collider kept (nothing new collides).
  - Inside: recorded with the furniture (`RecordPiece17`) and laid in the building level, with no collision; a board is trimmed or left out where the building's furniture footprint (`TownFeet`) stands against it.
- List 17's night glow of the room pictures goes with them: the user's new words replace it, and the report says so. The pictures, `M_B17_Pane` and the cube capture's code stay behind `rd.Windows18 0` (list 17's way), the assets kept.
- Immersive Interiors is unchanged; `TownWindows16` (also read by Immersive's window sight rule) is not changed.
- **Tests**:
  - `884 windows18`: in all six cities in Closed Structures, every window of every closed building traced through its opening on a grid from outside and from inside: every ray meets a board, or for Heaven the glass; none is bare. A picture of each style from outside and from inside. A sweep of her capsule along each inner wall with a window finds no new obstacle;
  - `888 windows18w`: the same for a farmhouse and a village house of each mesh, outside and in their levels;
  - `884 building17` (its view check) and `panes17` (its picture checks) run with `rd.Windows18 0`; `rooms17` stays.

### Phase 4: twenty square stands

- **The designs**: `SourceArt/list18/stalls18.json`: 20 medieval and 20 modern (Heaven) designs, each a list of parts placed in the stand's frame, all within the 2.6 m square, the counter on +X. Each design names the trades it suits (some suit any trade), so that every one of the 12 trades has at least 5 designs and the square's 12 stands can always take 12 different designs (checked by `951 stalls` when it reads the data: a matching of trades to designs exists).
  - Medieval parts: the three Docks stands (Blueprints), RiversideEuropeanVillage's stalls and fabrics, the storage markets, tables, crates, barrels, sacks, kegs, the weapon stand, awnings, the cloths, fruit and goods.
  - Modern parts: `950 stalls`' kiosks and new ones built from boxes the same way, City_Assets_Kit's awnings and canopies.
- **`951 stalls`** writes each part as a piece (`Stall18.<part>`) and the designs as data on the generator.
- **The choice**: the square's 12 stands are matched to 12 different designs suiting their trades, from a hash of the town's seed. The old four's draw from the outdoors stream is still drawn (unused), so nothing after it moves. `rd.Stalls18 0` gives the old three.
- **Tests** (`884 stalls18`):
  - in each of the six cities, each stand's design read from what was laid there (its parts' meshes within 2.6 m of the stand) and compared: 12 different a square;
  - each design's footprint swept by her capsule: inside its 2.6 m square only, the keeper's place 2 m behind clear, F from the front opens its trade;
  - every one of the 40 designs laid in turn at a test stand (a test call) with the same checks, and its picture;
  - the frame rate on a square with the old and the new stands (`rd.Stalls18`), read with, without and with again.

### Phase 5: twenty gates (two PRs)

**5a: the gate as a design, chosen once a game, with three designs**
- `SourceArt/list18/gates18.json`: a design is a frame (static parts), a leaf (the parts of one mover: a portcullis, a pair of doors drawn up together, a lifting bar), its lift height, the length of wall it replaces each side of the gap, and its lintel (or none: the frame's own top replaces the stretched lintel at 530 cm).
- `TownGateWorks` lays the design: one mover with several `Parts` (the door list and its indices unchanged: `TownPortcullis`, the two levers), the lift from the design, the levers placed past the frame's flanks along the wall. The wall runs beside the gap are cut by the design's length (static pieces only, no draws).
- **The choice**: one permutation of the designs drawn from the game's world seed (`GI->WildSeed`, new each game); the six cities take its first six in the world table's order. Distinct by construction, the same whatever order she visits them, and the same after a load with no new saved field (an old save's game draws its own permutation). Heaven takes its own from the modern designs the same way.
- **Tests** (`884 gates18`): each city's gate read from what was laid; six different in a game, the same after a save and a load, and different in a second game (another seed); for each design laid in Brokenspire (a test call): the leaf rises and closes, she walks through it open and is stopped shut (a sweep), F at each lever names that lever from inside and outside, the guards' posts and the stable spot reachable, the wall traced along both faces each side of the frame with no gap and no overlap, a picture from inside and outside.

**5b: the other seventeen medieval designs and three more modern**, as data, through the same test; the 20 medieval gate designs and 4 modern in all.
- Parts from Castle Kit's `SM_Main_Gate_01a-04a` and `SM_Gate_Door_01a-f`, CastleofEternalMist's and DwarvenCitadel's gate kits, BoneTemple's and Cemetery's gates, the town's wall and tower pieces, banners and torches; Heaven's from City_Assets_Kit's gate and boom gates and boxes.

### Phase 6: twenty tent spots

- **The designs**: `SourceArt/wilderness/tents18.json`, 20 designs in the layout language (`parts`), each with the point where its pile lies in its own frame and whether that point is under cover: pitched tents of each tent mesh of the packs (Hive_Sherwood's four, BoneTemple's fabric tents, FantasyCastle's, MC_Environment's, StylizedVillage's, the frozen tent), a collapsed tent, a lean-to, a tarp between poles, a hide shelter, two tents round a fire, a wagon under canvas, a wrecked house (`rect` walls with gaps, a fallen roof, rubble), a burned cottage, a ruined shepherd's hut, a cave mouth with a hide door, and more. No design adds a container (`box=`): the pile is the spot's only loot, under its own key.
- The meshes not yet in the places table are added (`biomes.json` "pieces", `887 data`).
- `SpawnWildPoi` still draws its old props loop from its stream, in the same order, so the loot drawn after it is unchanged; the design is laid with its own stream (a hash of the spot's id) by `LayWildParts`, and its pile placed at the design's point turned by the spot's yaw. A biome can exclude designs (the frozen tent in cold biomes only). `rd.Tents18 0` lays the old tent.
- **Tests** (`888 tents18`): each of the 20 designs laid in turn at a test spot: its pile opened by F, under cover where the design says (a trace up from the pile meets it), resting on the ground (traced), reached by her on foot; the abandoned camps over a 30 km square counted by design (all 20 seen) and their loot compared with `rd.Tents18 0` (the same things); the frame rate at a spot with the largest design and with the old tent; a picture of each design.

### Phase 7: the giant beasts (two PRs)

**7a: hostile giants, and her blows reaching them**
- **Reaching a big monster**: her target pick, auto-turn, bolts' and spells' targets and any other "height within N" rule compare her height with the monster's capsule's span, not with its middle (`RDCombat.cpp` 465 and 2471 and the like found by a search); `Empower`'s scale also scales the monster's step height and reach.
- **The giants**: `SourceArt/wilderness/giants18.json`: the big models (the Rock, Titan, Hunter, the Nasty spider, trolls) and the region's own hostile kinds, each scaled to a target height (5 to 9 m), not by a factor of its own size. Their definitions are kept out of every wild pick (weight 0 in the wild bands, a list of their own), so no lair, camp, ambush or roamer changes; `910`, `935` and `945 level` run after `951 giants`, as for any stage that adds monster kinds.
- **Where**: built on the roamers' machinery (`RDList15j.cpp`): a cell layer of their own (about 1 cell in 8 of the roamers' cells), a round of 600 m to 1.5 km on dry land away from towns, water, lava and slopes too steep for its size; laid within 900 m (the reach of the chunks' collision), removed past 1.2 km, the slain kept dead (a list of their own), marked on her map within 300 m. Its footsteps shake her camera within 40 m.
- **Strength**: "the top of the area's tier or the bottom of the next" is read from the monsters the area really has: for an area of tier `t` (`TierAt`, at most 29 so that `t+1` is a game tier), a giant's hit points and blow lie between those of the strongest kind laid at tier `t` and those of the weakest kind laid at tier `t+1` (each with its own kind factor), drawn from the giant's seed; the difficulty applies on top, as to every monster.
- **Tests** (`888 giants18`): the giants over a 40 km square counted (about 1 in 8 cells); one laid near her on ground of 15 to 25 degrees: its height, its feet on the ground (traced under each foot bone), her blows with each weapon kind and a bolt taking its hit points down, its hunt; its hit points and blow compared with monsters spawned at tiers `t` and `t+1` at the same place in the same session (between them); killed, still dead after she goes and comes back; pictures.

**7b: peaceful giants**
- The elephant and its towered kind (the only big models with the clips to walk, fight and die), and the existing "beastback" site's elephant left as it is (a structure of its own, `RDWildSite12.cpp`). Peaceful giants walk their round and graze; struck, they fight back (`ARDMonster::bPassive` until hurt).
- Every rule that takes a monster for a foe asks whether it is passive: the director's "something near", the fight's music, her allies' and summons' targets, her auto-turn, area spells and bolts (no provoking by a spell aimed elsewhere), its own prey (`PickFoe`: no hunting of people or farm animals), the locks' alarm, the kill counts of quests and contracts, the map's skulls, her stealth.
- **Tests** (`888 giants18p`): one laid near her: 30 s beside it, with her allies out and music measured, no attack, no fight music, no ally attack, its prey untouched; struck once, it fights her; each rule above checked by a call of its own.

### Phase 8: the Shipping package, the report

- `869` (usage flags of the new pieces' meshes), a full cook, `package_mistward.ps1 -Test` with every run.
- `docs/improvements18_report.md`: what was built, measured, and not checked.

## Order and what runs in parallel

The editor allows one session at a time, so the editor's stages and tests go one after the other: the scrub (2), the windows (3, while list 17's tests are fresh), the stands (4) and the gates (5a, 5b), which share the part-list designs, the tents (6), the giants (7a, 7b), the package (8).

Beside it, without the editor:
- the designs' data (stalls18.json, gates18.json, tents18.json, giants18.json) drafted by sub-agents from `asset_survey/` (the packs' meshes and their bounds already measured there) while the earlier phases are built; the sizes are checked in each phase's own editor run;
- each PR's review runs while the next phase starts.
