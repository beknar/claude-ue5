# Heaven and its fortress (`908`, `909`, `RD/RDHeaven.cpp`, the modern plan in `RD/RDTownPlan.cpp`, the theme in `RD/RDSection.cpp`; the user's list of 2026-11-08b, `docs/improvements9.txt`, its fourth phase; `docs/levels/heaven.md`)

The city is a wilderness town on `brokenspire` with the modern plan (`FRDWildTown::Plan` 5 -> the generator's `TownPlan`, `bModern`; `bMid` as the other cities: a landmark at the middle over a dungeon of its own); the fortress is `heaven_fortress`, a Save As copy of `mistward_castle` with its own `DungeonKey` ("heaven"). Every rule is behind `TownPlan == 5`, the `Modern*.` / `Lab.` / `Heaven.` pieces or a level's own data: the other towns and dungeons are unchanged.

## The city

- **A theme reskins a town by piece name**: the town section's `Theme` is "Heaven" for plan 5 (it is `NAME_None` for every other town), so `Pc` / `AddPiece` take "Heaven.<name>" wherever `908` made one: the wall's courses and the towers' cone roofs (`Heaven.Town.CityWall`, `Heaven.Town.CWall`, `Heaven.Town.TowerRoof`), the furniture (`Heaven.Desk`, `Heaven.Bookshelf`...). A direct `Generator->Piece(...)` is not themed: sizes read that way are the original's, so a reskin fills the original's box (`908`'s `refit` reads the original's adjusted bounds). `Bookshelf` and `CandleStand` are blueprint pieces (`ActorClass`, no mesh): a themed mesh replaces them all the same.
- **Pieces from boxes**: `908` merges cubes into meshes (`StaticMeshEditorSubsystem.merge_static_mesh_actors`, the pivot the world's origin, the physics data merged so each box keeps its collision). The merge puts "SM_" before the name it is given, and makes the mesh in memory only: save it (`884 heaven`'s third run found none after a restart: the level's pieces pointed at nothing). Build each in the frame of the piece it stands for (the house kit's walls about their line, the door's leaf along +Y from its hinge, the dungeon's walls through `907`'s normalisation).
- **What the town grows besides its grass**: the gardens' wheat (`Town.Crop2`, `SM_WheatGrass01`) stood in Heaven's streets after the short grass and the bushes were turned off; the homes' gardens, pens and cooking fires are off in Heaven (`TownLife`). Count what the test forbids by mesh name over the whole section.
- **Which way a merged car faces**: read it from the blueprint's parts, not a picture (the front doors stand at +Y, the rear doors at -Y: the front is +Y).
- **Traffic**: a car per lane every 45 m was 160 cars; every 70 m on the grid's streets only (none on the main road or the cross road through the square), 84. A car waits for her within 9 m ahead in its lane (measured: 6 m away, it stayed still 2.5 s and drove 30 m once she stepped aside); it turns into the other lane only once that lane's start is clear; a car checks only its own street's cars; all stand still while she is far beyond the shield.
- **A line between an if and its else** (PR #33's review): `if (bWild) TownGateWorks(); <new line>; else ...` gave the else to the new line, and every other wild town a shut gate's mesh in its open gateway. `884 spire` and `heaven` count the static gate's instances (none).
- **A kind's name is also a place's name**: the skyscraper was "tower" at first, the wall's watchtower spots' name, and `GetTownPlace("tower")` finds spots first.
- **Shared assets, one table**: `908` and `909` wrote the same material instances with their own values; both take them from `heaven_kit.py` (and its merge of boxes).

## The fortress

- **A shot clip's "fastest bone" is late in a burst**: the trooper's and the commander's release came out 3.0 s; the release is held to 0.5 s.
- **A held shooter fires only within its range**: a trooper held 10 m from her (its range 9 m, `max_chase_speed` 1) fired nothing in 12 s; from 7 m it fired twice and both rounds reached her.
- **The start section keeps the castle's great-hall furniture**, as every dungeon copied from the castle.

## The list of 2026-11-22 (phase 18: `946`, `RD/RDHeaven16.cpp`, `884 heaven16_*`)

- **A light placed by a guess is not under the lamp**: the street light's head was taken as 2.6 m out and 7.4 m up; measured on the mesh it is 3.6 m out with its underside at 7.05 m. Measure a fixture's head on its vertices in the piece's frame (after `Adjust`).
- **A bed's simple collision is not its mattress**: Heaven's beds' boxes stood over the mattress and the sleepers floated; a trace of the mesh (complex) finds it. The body's lift over the top then had to come down (92 to 72 cm): measure the hips against the mattress, not the traced top.
- **A test that fails half way leaves what it opened**: the map step stopped on a wrong property name with the map open, and the next step's picture was the map. Close what a step opens in a `finally`.
- **A piece looked up by its plain name is not themed**: the sign faces were found by `Town.SignFace_<WORDS>` (`Generator->Piece`), so Heaven's own needed `<Theme>.Town.SignFace_<WORDS>` asked for first.
- **PR #125's review**: a light for every fixture must be measured in frames: every street lamp's light drawn to 90 m at 24 m took Heaven's midnight from 20.1 to 4.4 frames a second; their lights near her only (35 m) and the glowing heads beyond, 22.0 against 21.6 with them off. A brightness in a picture is no measure of light (the exposure adapts every picture): measure the contrast it makes, with and without it (`rd.StreetLamps`). A light high up is cut by the town's 45 m: a beacon that must be seen is a lit mesh. A stage never deletes what the level uses (a material its instances parent from, a mesh its pieces point at): keep it, or make the new shape under a new name. A test's limit in the wrong units (0 to 1 against a picture's 0 to 255) passes on a black frame.

## The list of 2026-11-22: the streets (phase 19: `946 streets`, `RD/RDHeaven19.cpp`, `884 heaven19_*`)

- **A light that switches on a tick is read against what it was set to**: the lenses change five times a second. Compared with the phase computed at the moment of reading, 34 of 2808 reads "disagreed". `GetSignals19` gives the phases last shown and the phases now; the test checks the lenses against the first and counts the lag on its own.
- **A colour in a picture is read where the thing is**: counted over the middle of the picture, the red signal's picture had 74 green pixels against 100 red, from the side faces' green lenses and their glow. Each lens is boxed where it projects on the screen (`project_world_to_screen`), and its own colour is read.
- **A car list is not all cars**: `Heaven.Car_6` is a 12.4 m bus. Parked nose in a 3 m bay, it stood half across the street. The test had checked parked cars by their middles, so it passed. Parked kinds are filtered by length (6 m bays), and the test checks each car's footprint (its length and width, turned by its yaw) against the moving cars over 30 s.
- **A picture's stand point needs room**: a stand 7 m beside a parked car put the camera inside a building, and one over a crossing put it inside a shelf. Stand in the street, from the stop lines' lanes.
- **Heaven's medieval things are replaced by name**: `PcName` takes `Heaven.<name>` wherever `946` made one (torch, candles, chandelier, fireplace, tripod, cauldron, pot rack, shield; `Town.Cart`, `Cart2`, `Hay`, `Logs`, `Sacks`, `Lamp`). Their fires are cut in `AddEffect` by the theme, along with the fires' sounds (`FirePoints`).
- **PR #126's review**:
  - **A rule old towns lived with can break under a new piece**: the yard rule set a cart at a random turn on any free tile, so in Heaven a trailer or car stood half in the street. Heaven's yard things stand along the building's front, off the streets and the kerb row, with the whole footprint blocked.
  - **A replan with static building off finds what the static build made**: `RestartPlay`'s replan cleared `SignalLenses19`, and every signal froze. The lenses are found again by their tag.
  - **A theme replaces the light as well as the mesh**: the desk lamps kept the candles' flickering orange light and the bollards the fire basket's. In Heaven a warm light is a steady white (`AddLight`).
  - **A count of instances the code made is checked against the code's own plan**: the side of a stop line is read apart from it, from the moving cars' own lanes.

## The list of 2026-11-22: the storeys (phase 20: `946 storeys`, `RD/RDHeaven20.cpp`, `884 heaven20_*`)

- **A roof that was only seen has no collision**: `ModernRoof` laid the slabs and parapet with none. Climbed to by the new stair, she stood on a wall's top 24 cm under the roof, and would have fallen through it elsewhere. Where a core reaches the roof, the slab and parapet collide (`946 storeys` makes the pieces collide; the section asks for it only there).
- **A room's height is not a storey's**: Heaven's rooms are 6 m high in the generator. The hanging lights and the fill light (`RoomHeight - 120`) hung in the storey above once there were floors. Under Heaven's theme they are capped to 272 cm.
- **What takes ground-floor room takes beds**: with the cores, 57 sleepers in bed fell to 49. The flats upstairs lay their beds under the town's name ("Bed", recorded in `TownBeds`), and a sleeper is laid in its bed from where it stands: 77, and 66 once the core's way out was kept bare.
- **A test's "reached" is the tile, not its middle**: walking to a landing tile's middle she stopped 55 cm off it, on the tile. Points that are tiles' middles are reached within 70 cm.
- **Sizes of a themed piece come from `Pc`, not `Generator->Piece`**: the plain name's piece is the medieval one.
- **PR #127's review**:
  - **A part made with `AddMesh` is an interactive piece**: `ClearInteractive` (`RestartPlay`) destroys it. The lift's platform is made apart, and a restart puts it back at the street.
  - **A platform's "on it" is its square less her body**: at 160 cm, past its 135 cm edge, F rode it from the landing and the gate shut in her.
  - **A new F target yields to a nearer door or container** (`Best ? BestD`), as every town target does.
  - **Measure the cost in the same session, with and without** (`rd.Storeys20`): one reading after a long session said 4.8 frames a second against 11.7 earlier; with and without the storeys in one session read 11.5 / 9.8 / 9.5.
  - **A test's placement keeps her speed**: put somewhere after a walk, she slid 57 cm on. Stop her movement after a `put` that a reading depends on.
  - **What a test says it pushed at must be the nearest**: the roof push went 10 to 20 m toward a far parapet. It now goes out over the edge tile and records where she stops.

## The list of 2026-11-22: shops, services and containers (phase 21: `946 shops`, `RD/RDHeaven21.cpp`, `884 heaven21_*`)

- **F reaches a spot, not always the person behind it**: the shops' clerks stood behind their checkouts out of F's reach from the aisle, and the market only worked through its counter's spot (`TS_Counter`). Every shop has that spot at its checkout, and the store opened there knows its building (`StoreBld21`) for its stock.
- **A test that picks a container must stand nearer to it than to any other**: from 1.4 m before a filing cabinet, F opened another one across the storeroom's aisle, the nearer. Stand 90 cm before it, and take one whose neighbours are 50 cm farther from that spot.
- **A container's kind is the loot's, its word her own**: Heaven's containers keep their kinds (barrel, crate, chest, wardrobe) and add a word (`FMover::Word`, `ContainerWords21`); the describe line uses the word.
- **An upright door is told by its part's shape**: under Heaven's theme a moving part taller than twice its depth turns on an upright hinge; the medieval rule (only "wardrobe") is unchanged elsewhere.

