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
- **PR #128's review**:
  - **A keeper who sleeps shuts his service**: the innkeeper slept from 22:00 and was not among those woken to serve. The hotel was shut at night, and its test had opened the panel before setting the hour.
  - **Setting the hour back is not a night slept**: `SetTownHour(7)` at 22:00 went back 15 hours to the same day. Move the day on as the camp's rest does (`TownDay`).
  - **A service's price follows the town's prices** (`RDTierPrice`), and covers what a dearer service would charge for the same.
  - **Skipping a room's furnishing skips its lights and blocked tiles**: give a shop its own.
  - **`TownPlan` outlives the town**: it stays 5 after Heaven is unloaded. Words chosen by it alone came to the wilds' trader; ask whether Heaven's section stands there (`InHeaven21`).
  - **An editor call can read nothing in play**: `EditorStaticMeshLibrary.get_number_verts` gave 0. Read a mesh's vertices through its sections (`ProceduralMeshLibrary.get_section_from_static_mesh`).
  - **A container's open value is no measure of where its part went**: the test reads the part's middle before and after.

## The list of 2026-11-22: goods and life (phase 22: `946 goods,life`, `RD/RDHeaven22.cpp`, `884 heaven22_*`)

- **A twin is a copy with a new face**: Heaven's goods are copies of the everyday items (`import_text(export_text())`) with their own names, pictures and words and no weight. Every reader of the kind (stores by trade, the quick bar, buffs) takes them unchanged. Kept out of every draw in one place (`CaveItemAllowed16`), and swapped in by the store's list (`TownStock`), never by a store of its own.
- **A piece placed against a wall stands off the wall's measured face**: the neon 13 cm off the wall's line was inside Heaven's walls (their outer face at 23 cm), visible and lit in every number and nowhere in the pictures. Measure the wall piece's box through its `Adjust` (`TownPiece(B, "Wall")`) and look at the front in a picture.
- **A brightness is read where the thing is on the screen**: a box over the middle of the picture saw a billboard 26 m off change the picture by 7 %; boxed where it projects (`project_world_to_screen`), 2.4 times.
- **A stand point on another's spot puts the camera in her back**: the pedestrians' picture stood her where one of them walked. Stand where another stands, 5 to 25 m off, she hidden.
- **A frame rate on a loaded machine wanders**: one reading said 4.2 with the pedestrians against 7.5 without; read with, without and with again in one place (13.2, 14.0, 14.9).
- **A timer drawn from a range keeps its old draw when the range shrinks**: the test's shortened horn range waited out the long draw already made (1 horn in 30 s). A wait longer than the range allows is drawn again.
- **Pictures for a game are painted without words or makers**: FLUX painted a real sportswear maker's mark on every pair of running shoes; they were left out. Look at every ad's picture before using it.
- **PR #129's review**:
  - **A town loaded straight from another changes `TownPlan` in the same call that unloads it**: a rule gated on `TownPlan == 5` never ran its "Heaven is gone" branch, and the city's loop played on in Graymourne. Stop what Heaven started whenever the plan is not Heaven's.
  - **A retry that draws from the same seed fails the same way for ever**: mix the failures into the stream, and give up after a few.
  - **"Heaven's section loaded" reaches 2 km out**: a rule for what she meets in Heaven asks whether she is inside its walls.
  - **A twin is a new name to every rule that asks by name** (recipes): add it where the like is asked for.
  - **A refresh that resets the state it guards repeats the work**: compare what changed before writing again.

## The list of 2026-11-22: the traffic (phase 23: `946 traffic`, `RD/RDHeaven23.cpp`, `884 heaven23_*`)

- **What a town's plan makes later is not there when its works are made**: `HeavenWorks` runs before the streets' runs and signals are planned, and a replan with static building off never plans them. The traffic is made from the section's tick once the town is built, the runs planned again if a replan left them empty.
- **A count per piece of something short gives nothing**: a car per 90 m of each lane gave 8 cars on 142 lanes. Spread it over the whole.
- **A gap between two long things is measured on their footprints**: the projection of each half-length on the line between their middles read a bus beside a parked car as 2.4 m into it. Use separating axes (`RDH23Overlap`), the largest margin they keep apart.
- **Every rule that holds a car can hold another that holds it**: each of these stood cars for minutes:
  - a distance rule held a car going straight behind the car waiting across the crossing;
  - two left turns each yielded to the other standing at its line;
  - a bus's turn and the car at its line waited for each other;
  - a car in a crossing and the car that came in after it each held the other.

  Record why each car is held and for how long (`Why`, `StillSince`) and read the longest held, not the counts.
- **A decision made late is a hard stop**: checked at the line, a blocked curve stopped cars from 6 to 8 m/s in a quarter second. Check from the braking distance, and ease down to the crossing's speed before it.
- **Committing through a light runs reds**: a car committed while still held by the car ahead went through on red. Decide amber by the time to the line against the amber left.
- **Sample a long thing's way densely**: at six places along a bus's turn the overlap with a car at its line fell between two of them; at twelve it is found.
- **A crossing is reserved, not only checked at its entry**: two cars turning across each other from opposite sides went in together, each seeing the other at its line. Check the whole way against every crossing car's remaining way.
- **A test's picture stand point must be outside**: "across the street" from a bus at its stop stood in buildings twice. Stand behind it along its lane.
- **PR #130's review**:
  - **A decision kept from one frame must be kept**: a car that went on amber was stopped dead across its line at the red, because the light was asked again every frame. Commit when it reaches its line before the red, timed at no more than the speed it slows to. Never stop one already past its line.
  - **Count an offence where it happens**: a red run at the line, not where the curve starts. A car stopping aimed at its line slid over it and read as "already over"; stop 40 cm short.
  - **A fallback that fakes a route ends the re-routing**: a lost car's random next lane was written as its route, so it was never routed again, and its bay stayed reserved.
  - **Showing a parent shows its children**: drivers and empty seats came back with their car; apply the children's own rule at once.
  - **A replan must not re-plan what the static build placed**: keep it.

## The list of 2026-11-22: the skyscrapers' level (phase 24: `948`, `RD/RDTower24.cpp`, `884 tower24_*`)

- **A level with no sets waits for nothing**: the loading cover waits for the start set to be built (`TickCover16`); the tower level has none, and the cover held her input a whole minute (the stairs' test walked nowhere). It waits for the tower now (`bTowerPlaced24`).
- **A pack's mesh has its own front**: each candidate was pictured alone from +X and from +Y (base colour) and its front written in the table; a long ortho picture of all of them drew half black (Nanite meshes in an orthographic capture).
- **A walk from a landing cuts across a flight**: from the next floor's landing straight to the half landing she walked down the flight she had come up. A route goes through every landing.
- **A lift's door is not its shaft's middle**: walked at the shaft's middle she met the wall beside the door; approach along the door's row.
- **A tower's pieces stand in the town's shared instanced components**: for a capture from inside it, its instances in its footprint are moved down and back (`TowerOutOfCity24`), its other components hidden from the capture.
- **A picture of a real sky blooms**: the window's HDR sky washed every view; bloom and lens flare are off in the tower level.
- **Compare a capture with a capture of the same kind from the same point**: Heaven pictured 17 m beyond the tower's wall stood past a building 12 m north of it; the comparison now takes the cube's own point with the tower taken out (`CaptureCity24`).
- **A C++ file changed while a background build runs may be compiled half old**: build again after it, before trusting a run.
- **PR #131's review**:
  - **The volumetric clouds veil near things in a cube capture**: in their render-target mode they are drawn without depth. A building 12 m away showed as a pale haze, and the views matched Heaven at 0.26 to 0.45. Hidden for the capture, they match at 0.99.
  - **A new F target yields to what is nearer**, except to the thing it replaces (the tower's own door leaf).
  - **Two targets near each other: take the nearest, not the first in reach** (the lifts' doors 1.5 m apart).
  - **A capture for a level is taken where the level's eye will be**: the city tower's storeys are 9.6 m, the level's 3.5 m.
  - **Session state carried for one visit is let go after it, and forgotten by a load**: three cubes of 28 MB each.
  - **A test that reads a value after leaving the place that held it reads the reset**: the hour came back -1 and the comparison was taken at night.

## The list of 2026-11-22: the fortress's defenders (phase 25: `947 monsters`, `RD/RDFortress25.cpp`, `868 fortress25`)

- **A flyer's clip can carry it up**: Military_Drone's quadcopters fly in their own idle 1.3 m over their origin (at 2.5 times, 3.2 m); a hover on top put them at 3.3 m. Their mesh is lowered instead, and dropped onto the floor at death (`DeathDrop`); the gun drone's death clip falls 2.6 m by itself.
- **A capped chase speed holds a fighter of blows where it stands**: the test held every kind still (`max_chase_speed` 1) and the melee kinds never struck; only shooters are held.
- **Feet measured once are measured in an idle's sway**: a correction from one run left 5 to 6 cm in the next. Correct by the measure, test within 8 cm.
- **A pack's colours are whole materials, not instances**: a variant is found by name (the set's number), slot by slot, and each slot's swap is asserted.
- **A stage that adds kinds to the fortress is followed by `910`** (the kinds on every map, their wild bands) **and `935` and `945 level`** (the caves copy brokenspire's monsters as text); `947 monsters` follows `909`.
- **PR #132's review**:
  - **A swing's flag left set by a cut-short swing is taken by the next**: a medic's heal interrupted by a flinch turned its next shot into a heal. Every swing clears the others' flags.
  - **A monster's choice that comes after another branch that returns early never runs**: a medic in reach of her struck and never healed.
  - **"Elite" is against the set's mean**: a test that spawns a tier-3 kind (or a kind 1.2 times as strong) in the tier-1 first hall made it an elite, and the medics, rightly, would not heal it. Spawn at the hall's tier, of the kinds' own strength.
  - **Ask the thing why**: the heal's refusals recorded (`GetHealWhy25`) found the elite rule in one run, where guesses had taken four.
  - **A copy made once is a copy kept stale**: `910` skipped kinds a map already had.

