# Heaven

A modern city surrounded by a shimmering shield, with skyscrapers, office buildings, modern shops, modern streets and modern vehicles driving them; its dungeon is a mechanised fortress with modern and sci-fi defenders armed with firearms, entered through a foreboding research facility called "Kratos Aurorim Research, LLC" (the user's list of 2026-11-08b, [docs/improvements9.txt](../improvements9.txt), its fourth phase). The city is the wilderness's last town on the `brokenspire` level; the fortress is a level of its own, `heaven_fortress`, the last of the chain of dungeons ([the keys](wilderness.md#the-list-of-2026-11-08b-third-part-the-dungeons-keys-and-the-roads-tiers)): its Kratos Keycard is dropped by the Black Tower of Kethrys Spire's boss.

- **Maps:** the city on `/Game/RandomDungeon/Maps/brokenspire` (streamed in the wilds as she comes, like the other towns); the fortress `/Game/RandomDungeon/Maps/heaven_fortress` (a Save As copy of `mistward_castle`: the same heroes, balance, loot, traps, special rooms and bosses)
- **Played from:** the security door at the far wall of the facility's laboratory hall (walked into; without the Kratos Keycard it stays shut and says whose master holds it); the fortress's Escape menu's "Return to Heaven" brings her back before the facility's door. `heaven_fortress` has no menu of its own: played from the editor it starts the generator's `DefaultHero`.
- **C++:** `RD/RDTownPlan.cpp` (the modern plan, `TownPlan` 5, `bModern`: the facility at the middle, a grid of straight streets, the towers, office blocks, shops and apartments, the street furniture's spots, the posts; no earth roads, mill, stalls, tents, gardens, pens, grass or bushes; the buildings' modern style and flat roof), `RD/RDHeaven.cpp` (the facility's lobby and laboratory hall in glass and steel, its dark glass block, its name over its door, its security door; the buildings' flat roofs, parapets and roof plant, a tower's floors over its lobby; the streets' asphalt and the paving; street lights and furniture; the shield; the cars and their driving), `RD/RDSection.cpp` (the town section's theme "Heaven": every piece the town asks for is Heaven's own where it has one), `RD/RDTown7.cpp` (Heaven's ground flat), `RD/RDTown.h` and `RD/RDTownHUD.cpp` (the facility, the tower, the office block and the shop as buildings, the street light, traffic light and street prop as spots, on the town's map), `RD/RDWildWorld.cpp` (the city's place and its road to Kethrys Spire)
- **Scripts:** `heaven_kit.py` (the materials and the merge of boxes into meshes, shared by both stages), `908_heaven_city.py` (the materials, the merged pieces and cars, the packs' pieces, the furniture, the people and quests on `brokenspire`, the fortress's level for the town), `909_heaven_fortress.py` (the fortress level, its steel halls and its defenders); tests `884 heaven,descendheaven` and `888 world,towns` (all with `-Light`)
- **Data:** `SourceArt/heaven/city.json` (the townsfolk and the quests), `SourceArt/heaven_fortress/monsters.json` (the defenders and their guns)

## The city

- **Where:** past Kethrys Spire to the south-west, inland: placed 30 km south and 58 km west of it and walked inland until the land is solid (114.1 km north of Brokenspire and 110.9 km west in the test's game, 56 km from Kethrys Spire, measured). A road joins it to Kethrys Spire.
- **Its size and plan:** Brokenspire's size (168 tiles, 504 m a side), built from the town's rules with the modern plan (`FRDWildTown::Plan` 5): the research facility at the middle (16 m from it, measured); straight streets 3 tiles wide every 19 tiles each way (none through the facility's ground or the square); skyscrapers round the middle (9 in `test_hv10.json`; the kind "skyscraper", not "tower": the wall's watchtowers are "tower"), office blocks of three to five storeys (12), shops round the square (12), apartments (56, none burned or boarded), the trades (the smithy (its keeper an armorer), the store, the healer (a doctor), the storehouse, the tavern (a bar's owner), the barracks, a chapel, the temple: their signs the town's), the graveyard. Their signs are Heaven's own (phase 18 below). Every building has rooms, a door that opens and containers (312 containers, 104 doors in `test_hv10.json`).
- **Its buildings:** concrete, glass and steel, made by `908` from boxes merged into meshes in the house kit's frame (`Modern.*`: walls, windows with mullions, glass walls, doorways, glass doors, polished floors, pillars, flat roofs, parapets, roof plant), in three facings by the building's seed (pale concrete, dark stone, brick red: `Modern`, `Modern2`, `Modern3`). A tower is a lobby walked into with SpaceColony2086's tower floors stacked over it (4 to 10 floors, fitted to the lobby's footprint) and its rooftop: the tallest 101.1 m (measured). Their rooms have Heaven's own furniture (office desks and chairs, book and storage shelving, planters, lunch and cocktail tables, sofa benches, beds, shelving, a kitchen unit, a fridge as the oven), the town's furnishing asking for it by name.
- **The research facility:** a lobby (4 by 9 tiles, a guard room) before a laboratory hall (the rest, 15 wide), their walls dark glass in steel frames, white floors, ceilings of light panels, a tower of dark glass over the hall (161.8 m: phase 18 below), "KRATOS AURORIM RESEARCH, LLC" in white letters over the front door, security guards at the door. The security door (a steel vault door with a red light over it) stands at the hall's far wall. It reads on the town's map as "KRATOS AURORIM RESEARCH, LLC · the facility".
- **Its streets:** asphalt (3,787 tiles in `test_hv10.json`), the rest paved (6,591 tiles: the square, the pavements, the lane by the wall); street lights every 7 tiles along each side (164; lit at night: phase 18 below), and between them a bench, a bus stop, a hydrant or a bin (95); a traffic light at a corner of every crossing (36). The buildings' doors are lit by a white ceiling light, not a sconce. The square has a fountain and no market stalls; street trees, no grass or bushes; no vegetable gardens, animal pens or cooking fires.
- **Its traffic:** Vehicles_Vol1's civilian cars, taxi, police car and bus (each blueprint's 6 to 15 parts merged into one mesh), a car every 70 m or so in each lane of every grid street 14 tiles long or more (84 in `test_hv10.json`, all moving: 30 m in 3 s for the middle one; none on the main road or the cross road through the square: no car on the square or at the facility's door), keeping to the right and turning back into the other lane at the street's end once that lane's start is clear of her and its cars. They stand still while she is more than 300 m beyond the shield. A car waits while she (or another car) stands within 9 m ahead of it in its lane: one she stood 6 m ahead of did not move in 2.5 s and drove on 30 m once she stepped aside (measured).
- **Its wall and shield:** the town wall and its towers are glass and steel in the castle kit's boxes (`Heaven.Town.CityWall` and the rest), each tower's cone roof a flat steel roof and a mast with a red light. A dome of hexagon panels in a translucent, glowing, slowly breathing shield material covers the whole town: its radius 229.8 m, 33.5 m past the farthest building (measured); seen from outside by day and by night (`hv_skyline`, `hv_skyline_night`).
- **Its people** (23 kinds, `city.json`: the dystopian city's and the old gangsters' NPC packs, in modern clothes, with their own clips): Director Cassia Vael before the facility (the elder's part: talk, quests), Dr. Imre Solace (the scholar's), Security Chief Dana Roarke (the captain's), the trades' keepers (Chaplain Ruth Okonkwo, Teo Brask the armorer, Lydia Marsh's market, Dr. Abel Nwosu, Morris Haig's storage, Nina Sato's bar), a street preacher, office workers in the towers and office blocks and clerks in the shops (33 workers in one test), Kratos security guards, city officers and patrols, children, a widow, Jax the busker, citizens.
- **Its quests** (on its map and over its givers' heads): the director's "Past the Lobby" (go into the fortress, 60 gold), "Deeper Clearance" (its tier 2, 120), "The Core" (tier 4, 300), each offered once the one before is done; the security chief's "Security Sweep" (30 kills below, 80) and, after it, "The Fortress Commander" (a tier's boss, 150); the scientist's "Former Staff" (talk to an office worker, 20); the board's "Contract: Rogue Defenders" (12 kills, 40). They count the fortress's own counters (`heaven:enter`, `:tier`, `:kills`, `:boss`).
- **Its roads' tier:** 25 at the city, 23 half way from Kethrys Spire (`TierAt`).
- **Frame rate:** 13 to 26 a second in a play window of 1280 x 720 just after the city was built round her (not measured settled).

## The list of 2026-11-22: first fixes (phase 18)

`946_heaven16.py lamps,signs,symbols` (or `all`) on `brokenspire`; C++ `RD/RDHeaven16.cpp`, with hooks in `RDHeaven.cpp` (the lamps, the facility's tower), `RDTownPlan.cpp` (the signs), `RDTownHUD.cpp` (the map), `RDList10d.cpp` and `RDTownGame.cpp` (the sleepers).

- **The street lights give light**: every pole's lamp is lit (one in three had a 220 cd light 7.4 m up, from where the head was guessed, day and night). The lamp's head is measured on the mesh (`946 lamps`: the arm's last 45 cm over 3 m up: 3.61 m out along the arm, its underside 7.05 m up) into `HeavenLampHead16`; a 1000 cd light (18 m, no indirect light) under it, drawn within 35 m of her (`HeavenLampDraw16`), and a glowing lens (`Heaven.LampGlow`, the kit's lit panel) at it, seen from anywhere. They burn from 19:00 to 6:30 (`HeavenLampsOn16`, `HeavenLampsOff16`; switched twice a second with the town's clock; `rd.StreetLamps 0` keeps them off, for tests). Every lamp's light drawn to 90 m at 24 m had dropped the frame rate at midnight from 20.1 to 4.4 a second (PR #125's review).
- **Modern signs**: every trade's board in Heaven is a dark panel with a steel rim on an arm (`Heaven.Town.Sign`, boxes merged by `946 signs`), its faces lit pictures of a modern city's words (white letters in Bahnschrift on dark glass: `blender_numpy/bs_signs.py <dir> --modern` into `SourceArt/heaven/signs16`, an emissive material of our own): GEAR SHOP (the smithy, the workshop), GROCERY (the store), CLINIC (the healer), CHAPEL, STORAGE, BAR (the tavern), SECURITY (the barracks), TOWER, OFFICES, SHOP. The other towns keep their gold Almendra boards.
- **Modern map symbols**: the big map marks Heaven's buildings with its 19 pictograms (painted on the InvokeAI server on 2026-11-22: `SourceArt/heaven/art16/map`, imported by `946 symbols` into the UI art as `hvmap_*`), each on its own coloured tile and named in the map's key (the research lab "Kratos Aurorim Research: the way into the fortress", the skyscrapers, offices, shops, grocery, gear shop, clinic, chapel, storage, bar, security, apartments); the town's painted medieval building pictures and parchment badges are not drawn there.
- **The sleepers on their mattresses**: a bed's top is traced on its mesh (complex), not its simple collision (which stood over Heaven's mattresses), and a sleeper is laid 72 cm over it (`SleepLift16`: 92 put the hips 32.5 cm over every mattress, measured), in every town.
- **Kratos Aurorim Research's tower**: over the laboratory hall, three tiers stepping in (0.86, 0.68 and 0.48 of the hall's width, 45, 33 and 22 % of its height) and a spire, red air lights at each tier's corners and a beacon on the spire (lit boxes, `Heaven.AirLight`: the town's lights are cut at 45 m and these stand 70 to 160 m up); its top 1.6 times the tallest a skyscraper of the plan can stand (`HeavenSkyMaxZ16`, 101.1 m): 161.8 m.

### Measured (phase 18)

- `884 heaven16_lamps -Light` (`test_h18h.json`, after PR #125's review): all 154 poles' lamps lit at 23:30 and none at noon; at midnight the street read from 6 m over it under a lamp and half way between two 21 m apart: 133.3 and 66.7 with the lamps on (2.0 times), 18.8 and 18.6 with them off (1.01: the picture's exposure adapts, so the light is the contrast, not a level); the frame rate there 22.0 a second with them on, 21.6 off; a picture of the lit street.
- `884 sleep10,heaven16_signs,heaven16_map,heaven16_sleep,heaven16_tower -Light` (`test_h18g.json`): 41 modern boards, no shield board and no gold face; the big map's badges all Heaven's pictograms (11 kinds), no medieval picture drawn (the map drawn on the picture from above, where the painted buildings were not drawn before either; the homes keep theirs on the painted map); every sleeper's hips 12.5 cm over its mattress; the facility's top 161.8 m as its placed blocks stand, against the tallest skyscraper's 101.3 m, 13 air lights, its security door there; Brokenspire's `sleep10` passed (below); pictures of a sign, the map and the tower.
- **A keeper woken at night served from its bed** (found by Brokenspire's `sleep10`, which had passed since 2026-11-10 only because the trader it spoke to never had a bed): F only turned it to her, and it left the bed in its next tick, after the panel that pauses the game; while it faced her (8 s) its day's reset was skipped, so a morning that came then left it up but "asleep". It is out of bed as F turns it now, posed standing, and awake while it faces her. The test speaks to a keeper in bed and reads it out of bed as the panel opens, and reads the sleepers' poses from inside their buildings (a body behind a hidden interior's wall is not drawn, so not posed: counted apart as not drawn). `sleep10` passed in Brokenspire (`test_h18g.json`: the trader in bed before F, out of it with the store open, nobody asleep in the morning).

## The fortress

- **Its halls by tier:** tiers 1 to 4 the fortress's steel ("Facility": steel and concrete wall panels with a cyan light strip, warning walls with a red strip or hazard stripes, steel floor plates, concrete floors with a hazard edge, ceilings of light panels; boxes merged into meshes in Heaven's own materials), tier 5 the fortress and the castle mixed; by every room's walls its machines (`ThemeProps`: Data_Center's servers and chillers, the sci-fi racks, generators and power boxes, electrical cabinets). Its lights are drawn toward a cold white (`DungeonLightTint` (0.75, 0.88, 1.0) at 0.7). Only tier 1's first hall has been seen, and it keeps the castle's great-hall furniture (throne, carpet, banners, columns) in the saved start section, as the other dungeons' do.
- **Its defenders** (`monsters.json`, five kinds among the castle's 56, weighted so that about two in three monsters of a tier are these): tier 1 the Kratos security trooper (the Soldier pack's, its own clips), tier 2 the facility guard (slow), tier 3 the Kratos operative (weaken), tier 4 the Kratos field commander (poison, 1.1 times), all three on the UE4 rig playing the Sci-Fi pack's Defender clips; tier 5 the Kratos assault tank (slow; the Dystopia pack's, 0.55 times). Each shoots (the castle's monsters that shoot: 9 m or 15 m), with its own shot clip, a tracer for its round, a muzzle flash and a bullet's impact (the tank a blue tracer and an energy impact), then fights hand to hand. All five measured playing (their bones moving 2.4 to 71 cm in half a second); a trooper held 7 m from her fired twice in 12 s and both rounds reached her (`test_hv10.json`).
- **Its own record:** its tiers, its start set's loot, its bosses and prisoners and the quests' counters are kept under its key (`DungeonKey` "heaven"), apart from the other dungeons'. No final boss. The chain ends here: its last tier's boss drops no further key.
- **Her whole state** goes down and comes back with her.

## The test

- `884_brokenspire_test.ps1 "heaven" <tag> -Light` (`SourceArt/brokenspire/test_hv10.json`): the city past Kethrys Spire, its tier 25 and 23 half way; the modern plan; the facility near the middle, its two rooms, its name over its door; the towers (and the tallest's height), office blocks, shops, apartments (none burned or boarded) and trades, every building's rooms, door and containers; the asphalt, paving, windows, tower floors, the facility's glass walls and block, the glass wall, street lights; no castle wall, cone roof, House Forge wall or grass left; the three facings; the shield over every building; the cars (each moving, one waiting for her and driving on, none on the square or at the facility's door); the traffic lights; no shut gate's mesh in its gateway; its people's roles and titles; the director's panel with the first quest; the security door refused without the Kratos Keycard ("locked") and opened with every key (its dry run); pictures of a street with its cars, the facility's front, the skyline under the shield by day and at 22:00, a tower's lobby, a shop, an office block and the security door.
- `884_brokenspire_test.ps1 "descendheaven" <tag> -Light` (`test_hv10.json`): the Warrior made different in the city, through the security door into `heaven_fortress`: her state as she left and as she came in the same (57 lines both ways); its key, title and themes; the menu's "Return to Heaven"; the defender kinds, one of each spawned in a row, each one's clips playing, a picture of the row; a trooper's rounds at her from 7 m (fired, on her, a picture of a round leaving the barrel); the counter `heaven:enter` at 1. Changed again below and back by the menu: the city built round her again, she stands at `ReturnAt` (0.0 m), 2.5 m before the facility's door.
- `888_wilderness_test.ps1 "world,towns" <tag> -Light` (`SourceArt/wilderness/test_hv7.json`): Heaven past Kethrys Spire, south-west of it, inland, 56 km off; six roads; every town built.
- The other cities again after Heaven's changes to the shared town code and PR #33's review (its gate: no shut gate's mesh in a wild town's gateway, `spire` checks it): `884 spire,holy` (`test_hv11.json`) `forge` (`test_hv12.json`) and `port` (`test_hv13.json`), all with `-Light`, all passed.
- Packaged on 2026-11-14 (Shipping, `builds\todo13`, `package_mistward.ps1 -Test`): the city ran 150 s and `heaven_fortress` 90 s, no crash report.
- Not yet run: the deeper tiers; the defenders fought.

## Rebuild notes

1. `908_heaven_city.py` on `brokenspire`, after `882` / `886` / `890` / `892` / `894` / `896` / `906`: its materials, the merged pieces and cars (saved under `/Game/RandomDungeon/Heaven/Meshes`; `908 rebuild` makes them again), the packs' pieces, the furniture, `TownDungeons["Heaven"]`, its people and quests from `city.json`.
2. `909_heaven_fortress.py saveas`: saves `mistward_castle` as `heaven_fortress` and quits the editor; start the editor again and run `909` (no argument): the Facility theme's pieces (made from boxes in 908's materials: run 908 first), the machines, the tiers' themes, the cold light, its key, title and town, no final boss, no menu, the defenders; its start section built. The fortress is a copy of the castle as it was on 2026-11-09: a later stage that writes the castle's heroes, items, monsters or pieces must be run on `heaven_fortress` too. Then `905` (the chain's keys and maps on every map, `heaven_fortress` among them).
3. The C++ (`RDHeaven.cpp`, the modern plan in `RDTownPlan.cpp`, the theme in `RDSection.cpp`, the city's place in `RDWildWorld.cpp`): `pipeline\build_cpp.ps1` with the editor closed.
4. `946_heaven16.py all` (the list of 2026-11-22: the lamps' head, the modern signs, the map's pictograms), after `908`; its faces painted first by `blender_numpy/bs_signs.py SourceArt/heaven/signs16 --modern`.
5. The tests above; Brokenspire's (`884`) and the other cities' own (`884 holy,descend`, `forge,descendwar`, `port,descendsewer`, `spire,descendspire`) after anything shared.
5. A game to play: `869_mistward_ism_usage.py` (the editor open; it reads `heaven_fortress`'s pieces too), then `pipeline\package_mistward.ps1 -Out <dir> -Test` (the editor closed; `heaven_fortress` is named to the cook).

## The list of 2026-11-22: the streets (phase 19)

`946 streets` (its pieces from boxes, `SourceArt/heaven/streets19.json`'s names and timings) and C++ `RD/RDHeaven19.cpp`, hooked into `HeavenStreets` (before the ground is laid: the crossings, runs and parking; after it: the markings, signs and cars) and `HeavenSpotBuild` (the signals). No random draw is taken: the plan's streams and everything placed from them are unchanged.

- **The streets' runs**: each street of the grid is cut into runs between its crossings (a tile under both kinds of road, the square, the facility's forecourt, or another road beyond the street's end).
- **Markings** (`Heaven.Mark`, a unit square of white paint stretched to each line):
  - a 3 m centre dash every other tile;
  - an edge line 40 cm in from each kerb;
  - at each end that meets a crossing, a zebra (50 cm bars a metre apart) in the last tile and a 40 cm stop line across the lane coming in;
  - a plaza (the square, the forecourt) gets its zebra and no stop line.
- **Traffic lights**: the pack's pole had no lamps, so each signalled crossing has our own four-way signal (`Heaven.Signal19`).
  - Its twelve lenses are instances of one mesh in one component per town. Each lens carries its colour and its light as per-instance data (`M_HV_SignalLens`), set five times a second by `TickSignals19`.
  - Each crossing's two roads take turns: green 14 s, amber 3 s, all red 2 s (`SignalGreen19`, `SignalAmber19`, `SignalAllRed19`). Each crossing has its own offset in the cycle.
  - The stop lines keep their lane, way and signal (`StopLines19`) for the traffic of phase 23.
- **Signs**:
  - a stop sign at the kerb of every approach to a crossing without lights (in this town only the four T-junctions; every grid crossing has lights);
  - a street-name sign at a corner of each crossing of two streets, its green blades naming the street each one lies along;
  - a district board at the crossing nearest the square in each quarter: Elysian, Meridian, Sanctum, Ascent.
- **Parking**: the pavement's row of tiles along each run, two tiles clear of the crossings, where it is free (no door's way, street furniture, tree or spot).
  - A stretch of three tiles or more whose next row is free too becomes a lot (bays nose in, two tiles deep; at most six a town). The rest becomes two-tile lay-bys along the street.
  - Asphalt is laid under both, with the bays' lines painted.
  - A car stands in three lay-bys of four and two lot bays of three, of the kinds 5.8 m long or less. The traffic's 12.4 m bus, parked nose in, stood half across the street in the first pictures.
- **No medieval leftovers**: Heaven's theme has a modern piece for each medieval one, and its fires are never lit (`AddEffect`).

  | Medieval piece | Heaven's piece |
  |---|---|
  | wall torch | wall lamp (its light white and steady) |
  | candles | desk lamp |
  | chandelier | ceiling light |
  | hearth | media wall (a screen's soft glow) |
  | kitchen tripod and cauldron | cooker and pot |
  | pot rack | wall shelf |
  | wall shield | picture |
  | cart | trailer |
  | wagon | parked car |
  | hay | dumpster |
  | logs | pallets |
  | sacks | bin |
  | fire basket | bollard light |

### Measured

- `884 heaven19_medieval,heaven19_markings,heaven19_signals,heaven19_signs,heaven19_parking,heaven19_fps,heaven19_restart -Light` (`test_h19d.json`, after PR #126's review):
- **Medieval leftovers**:
  - none of the 13 medieval meshes in Heaven and no torch, candle or hearth fire;
  - Brokenspire, counted first in the same run, keeps 158 torches, 256 candles, 38 hearths and its fires;
  - of Heaven's 646 lights, none flickering and none a flame's warm colour, and no desk lamp on a floor.
- **Markings**:
  - 85 runs on 18 streets and 36 crossings;
  - 452 dashes, 158 edge lines, 1026 zebra bars, 129 stop lines;
  - all 2294 marks laid, against the plan's count of instances.
  - Read apart from the plan: over 30 s, the moving cars were seen 394 times within 15 m before a stop line of their own way. Every one drove in that line's lane, 0 cm off its middle, and none in the other lane.
- **Signals**:
  - 36 signals, none of the pack's old poles;
  - over a full 38 s cycle (77 reads of every signal), the timing never let both roads go (green or amber) at once. The cars do not obey the lights yet: phase 23;
  - every read four lenses lit, the ones of the phase they were last set to (42 of 2772 reads a tick behind the clock);
  - every signal went green, amber, red in order on both roads.
  - In the pictures, each lens's own colour on the screen:
    - the +X face at the X road's green: its green lens 150 green pixels, its red lens 9;
    - the same face at its red: the red lens 91 red, the green lens 12 green;
    - the +Y face at the Y road's green: its green lens 224 green pixels.
  - After `RestartPlay`, whose replan builds nothing static, all 36 found their lenses again and kept changing, every read right.
- **Signs**:
  - 4 stop signs for the 4 approaches without lights;
  - 33 name signs at 36 crossings;
  - 4 district boards;
  - 144 text components, every sign's words, drawn within 60 m.
- **Parking**:
  - 246 cars in 324 bays (234 in lay-bys, 12 in 6 lots), the longest 5.67 m;
  - 5 yard things by the homes, set along their fronts off the streets, the whole footprint blocked (at a random turn they had stood half in the street);
  - no two footprints overlapping;
  - over 30 s, none of the 84 moving cars within 1.6 m of a parked car's or yard thing's footprint.
- **Frame rate** at a signalled crossing looking along a street, in the editor's play window (`rd.Streets19` hides the street things):
  - 9.3 frames a second shown (the first reading, as the view settled);
  - 11.9 hidden;
  - 11.6 shown again.
- **Pictures**: a crossing from its approach, a signal at green, at red and from its other side, each sign, a lay-by, a lot, the media wall, a trailer, a dumpster, a wall lamp.
- **Packaging**: the phase adds settings to the generator (`HeavenStreetNames19`...) and assets saved into `brokenspire`. A package needs a full cook (no `-SkipCook`) and `869` first (phase 28).

## The list of 2026-11-22: the storeys (phase 20)

`946 storeys` (the flight, rail, shaft wall, lift platform and ceiling panel from boxes; the roofs' slab and parapet made to collide; run it after `908`) and C++ `RD/RDHeaven20.cpp`, hooked into `TownShellBuilding` (before the roof), `ModernRoof` (the openings, the collision, no roof plant over a core), `Furnish` (the core and its way in kept free on the ground floor; no wall lamp, hung piece or kitchen fire in it) and `TownFurnish` (the upper storeys). Each building's own seed draws its furnishing: the plan's streams are unchanged (where a lamp is left out its draws are still taken). `rd.Storeys20 0` builds a town without them (for the frame-rate test).

- **Which buildings**: every home and office block, and every trade 8 tiles wide or more, of two storeys or more that is lived in. In this town that is 71 buildings: 56 homes, 12 office blocks, the temple, the tavern and the storehouse. The shops and the skyscrapers' lobbies are one storey.
- **The core**: three strips of four tiles along the back wall, in the back corner away from the door, never over the door or a doorway between rooms.
  - Its ground floor is kept free of furniture and of the townsfolk's ways.
  - The row before its lift strip is its way in and out: kept clear on the ground floor, bare upstairs.
- **The floors**: a slab between every two storeys, its top at 4 + 300 k cm, its underside 268 cm over the floor below. It is open over the flight that comes up through it and over the lift's shaft. The roof is open the same way, and its slabs and parapet collide on these buildings.
- **The stairs**: flight k rises from storey k to k + 1 (the last to the roof): 15 steps of 20 cm over two tiles, 2.5 m wide, a box each.
  - The even flights go up the back strip toward the far tile, the odd ones up the next strip back toward the corner, each with a landing tile at both ends.
  - Glass rails stand round every opening, along its open sides and across its low end.
- **The lift**: a steel platform 2.5 m square she rides (`LiftSpeed20` 220 cm a second) in a shaft at the core's corner, glass on its two inner sides, to every floor and the roof.
  - Well on it (within 85 cm of its middle, so she is clear of the floors' gates), F rides up a floor, and from the roof back to the street ("ride the lift to floor 2", "... the roof", "... the street").
  - At its door, F calls it to her floor ("the lift is here: step on" when it is there). A door or container nearer takes F first.
  - Each floor's door is an invisible gate, shut unless the platform stands there.
  - The platform is not one of the interactive pieces. `RestartPlay` keeps it and puts it back at the street.
- **The upper storeys**:
  - each furnished as its building's kind: an office's desks and chairs with shelves and planters along the walls; a flat's beds (town beds: its residents sleep in them), media wall, kitchen, sofa and table; a trade's shelves and tables;
  - a ceiling light panel on every other tile;
  - all of it the building's interior: hidden from the street, shown from inside (the seventh phase).
- **The ground floor's ceiling**: under Heaven's theme a room's hanging lights, its fill light and the hall's and chapel's chandelier lights are capped to the storey (272 and 230 cm). With the room's 6 m height they had hung in the storey above.
- **Packaging**: the phase adds a setting to the generator (`LiftSpeed20`) and pieces saved into `brokenspire`. A package needs a full cook (no `-SkipCook`) and `869` first (phase 28).

### Measured

- `884 heaven20_fps,heaven20_floors,heaven20_lift,heaven20_restart -Light` (`test_h20e.json`), and `heaven20_lift,heaven20_stairs,heaven16_sleep` again (`test_h20f.json`), after PR #127's review.
- **Floors**:
  - 71 cores (the 68 homes and office blocks all have one): 3 of two storeys, 62 of three, 3 of four, 3 of five;
  - a floor traced at every upper storey's height over each core's lift strip (148);
  - every slab and the roof probed: open over the flight coming up and over the shaft, closed over the lift strip's far tile and the tile before it, all 876 right;
  - 219 flights, 811 rails, 1103 pieces of furniture upstairs.
- **Roof**:
  - traced at its surface exactly, her height over it 84.6 cm (on the first run she stood on a wall's top 24 cm under it: the roof did not collide);
  - pushed out over its front edge for 2.5 s, she stopped 90 cm out from the edge tile's middle (at its parapet) and stayed on it.
- **The way in and out**: she walked from the street door to the row before the core and onto its lift strip (within 51 and 30 cm), and on the first storey out of it again (54 cm, her height over that floor 84.6).
- **Hidden interiors**: the tallest office's interior is hidden from the street and shown from its second storey ("inside").
- **Stairs**: in the five-storey office, she walked herself from the lift's strip round to the first flight and up all five flights and across every landing to the roof. All 12 points were reached, her height over each 84.5 to 84.7 cm.
- **Lift**:
  - she rode it a floor at a time to the roof and back to the street, its words each time the floor it goes to, her height over each floor 84.7 cm;
  - from floor 2's door with the lift at the street, pushed at the shaft for 2 s, she came no nearer than 1.92 m to its middle and stayed on her floor;
  - F there called it ("lift called"), it came to floor 2 with the other 5 gates shut, and she walked onto it;
  - on its edge (1.1 m from its middle) it said "the lift is here: step on", and in its middle "ride the lift to floor 3".
- **After `RestartPlay`**: all 71 lifts had their platform, back at the street, and one was ridden to floor 1.
- **Sleepers**: 66 in bed at night (57 before the storeys).
- **Frame rate** at phase 19's crossing view, the town built each time in the same session:
  - 11.5 frames a second with the storeys;
  - 9.8 without (`rd.Storeys20 0`);
  - 9.5 with them again.
  - No cost is seen. A reading of 4.8 in an earlier run (the editor long open) was not the storeys': the run that left them out read about the same.
- **Pictures**: the stairwell beside the lift's shaft; an office's upper storey.

## The list of 2026-11-22: shops, services and containers (phase 21)

`946 shops` (the shelves, the checkout and the services' and containers' pieces from boxes, the containers' words; after `908`), `946 signs` again (the new words from `blender_numpy/bs_signs.py <dir> --modern`), and C++ `RD/RDHeaven21.cpp`, hooked into the plan's posts and signs, `TownFurnish` (Heaven's shops furnished as shops), `AddContainer` (upright doors, words), the town's F and its panels (`RDTownGame.cpp`).

- **Shops as shops**: the market (the trader's store) and every shop: a checkout by the door, its clerk behind it, and rows of double-sided gondola shelves full of goods.
  - The rows run across the building 6.45 m in from the door's wall and every 2.7 m, with aisles of 1.5 m at the walls and a cross aisle in a long row.
  - There are three looks of goods: a grocery's, a pharmacy's and a hardware store's. The market mixes them.
  - Light panels hang under the ceiling.
  - F at the checkout, or at its clerk, opens the shop's store with its own stock only:
    - the grocery's food;
    - the pharmacy's healing, mana and speed potions;
    - the hardware store's repair kits and torches;
    - the market everything the trader sells.
  - Each shop's kind comes from its seed, and its sign says it: GROCERY, PHARMACY or HARDWARE.
  - The shops' own furnishing (a storeroom's barrels) is not laid. The furnishing's stream then moves on differently in Heaven only.
- **The services**: the trader's store is the market (its sign MARKET), the healer the clinic, the smith the gear shop, the storehouse the bank (BANK), the inn the hotel (HOTEL), the temple the chapel. Their panels' names and words are modern.
  - The clinic has a reception desk.
  - The bank keeps her things in a safe-deposit box, with its vault's door against the back wall.
  - The gear shop has a workbench with a pegboard, a vice on a stand (the anvil's piece, so its crafting stays) and a parts bin, in place of the forge, anvil and quench tub.
  - The hotel's keeper rents a room for the night: she sleeps until seven and wakes with all her hit points and mana, her afflictions gone (8 gold a tier, 10 at least). The hotel also sells food.
- **Modern containers**: Heaven's theme replaces each medieval container with a modern one, each a body and its moving part on its hinge (an upright door where the part is taller than it is deep, else a lid), and names it:

  | Medieval | Heaven | Opens by |
  |---|---|---|
  | barrel | fridge | door |
  | second barrel | filing cabinet | door |
  | crate | tool chest | lid |
  | second crate | bin | lid |
  | chest | safe | door |
  | wardrobe | double locker | two doors |
  | (a yard's hay) | dumpster | lid |

  - Their kinds (barrel, crate, chest, wardrobe) are kept, so what they hold is drawn as before.
  - Only her words change: "open the fridge".
- **Built from boxes**: the containers and the shops' pieces are built from boxes in Heaven's kit, as its other pieces are. No pack mesh's door is split in Blender: none of the packs' fridges, safes or lockers is used.

### Measured

- `884 heaven21_shops` (`test_h21b.json`), `heaven21_services,heaven16_signs` (`test_h21a.json`), `heaven21_containers` (`test_h21d.json`), all `-Light`.
- **Shops**:
  - 13 shops (the market and 12), each with its checkout;
  - every shop's gondolas counted inside its rectangle as laid: 12 to 22 each, the market 44.
  - At the market and at a grocery, a pharmacy and a hardware store, F at the checkout opened the store:
    - "The market": 27 lines;
    - "The grocery": 15, all food;
    - "The pharmacy": 6, all potions;
    - "The hardware store": 6, repair kits and torches.
  - None sold anything outside its trade. Each sold one thing: its price taken, the thing in her pack.
- **Services**:
  - lit faces MARKET, BANK, HOTEL, CLINIC, GEARSHOP, PHARMACY (2), HARDWARE (10), GROCERY (12), and none of the old STORAGE, BAR or SHOP;
  - the clinic's desk, the vault, the workbench, the vice and the parts bin there, and no forge, anvil or quench tub;
  - the keepers' panels: "The market", "The clinic", "The gear shop", "Your safe-deposit box", "The hotel", "The chapel";
  - a night at the hotel from 22:00 at 40 % health: woken at 7:00, whole, 10 gold.
- **Containers**:
  - none of the 13 medieval container meshes in Heaven (Brokenspire, counted first, keeps 1078);
  - 134 containers: 36 fridges, 31 safes, 44 locker doors, 16 tool chests, 3 filing cabinets, 3 bins, 1 dumpster.
  - One of each opened by F from 90 cm before it: its words "open fridge" and so on, only it opened (both doors of the locker), its door or lid turned 100 degrees from shut.
  - On the first runs F from 1.4 m took another container across a storeroom's aisle: nearer, as F should.
- **Pictures**: a shop's shelves and checkout, the clinic, the bank, the gear shop, an open fridge and locker.

### After PR #128's review

- **The hotel**:
  - It is open at night: the innkeeper wakes to serve, as the keepers do.
  - A night moves the day on: to seven next morning, and from before seven to that same day's seven. It is autosaved as the camp's rest is.
  - Its price is what the clinic would ask now for the same (hit points, mana, cures) plus a room priced by the tier as the town's prices are.
- **The shops**:
  - They have their lights: one steady light every two tiles under the ceiling.
  - Their shelves and checkout block their tiles for the tile paths.
  - The market's light panels hang under its roof (its hall is two storeys high).
- **Leaving Heaven**: its words and the shops' stock hold only while Heaven stands round her (`InHeaven21`), and a store forgets its shop when its panel shuts.
- **The map**: it names the market, the bank and the hotel, and a shop as a grocery, a pharmacy or a hardware store.
- **The bank's vault** stands against its back wall.
- **Old saves**: a save made in Heaven before this phase keeps its looted containers by their order. The shops' storeroom containers are gone and the yards' dumpsters come first, so it marks others as looted. No save version was raised for it.
- **Measured again** (`884 heaven21_containers,heaven21_services -Light`, `test_h21e.json`; `heaven21_shops -Light`, `test_h21f.json`):
  - **Shops**:
    - 2 to 4 rows of shelves a shop, every shelf 6 m and more in from its door's wall and turned across the room;
    - the three shelves' meshes 4104, 4266 and 4212 vertices (their frames and boards alone about 290: the goods are there);
    - the four kinds' stores as before, and F from beside a pharmacy's clerk opened "The pharmacy".
  - **Services**:
    - the clinic's desk, the vault, the bench and the vice each in its own building;
    - at 23:00 the innkeeper was asleep and served;
    - the night woke her at 7:00 the next day, whole, for 31 gold against the clinic's 21 for the same body.
  - **Containers**: each part's middle moved where it should: the doors 20 to 28 cm out in front of their bodies, the lids 16 to 28 cm up (a door turning into its body would have read inward).

## The list of 2026-11-22: goods and life (phase 22: `946 goods`, `946 life`, `RD/RDHeaven22.cpp`, `884 heaven22_*`)

The user's words: "food, items and other things bought in the city of heaven should be modern in looks", and "the city of heaven should have typical ..." (the plan: typical city ambience: people on the pavements, the city's sound, billboards, neon at night).

### Modern goods

- **Twins**:
  - Every everyday item (the foods, the healing, mana and speed potions, the five repair items, the torch) has a modern twin, 40 in all (`SourceArt/heaven/goods22.json`).
  - Each twin is copied from its item, so it has the same kind, numbers, tiers and buff. Only its name, words and picture are its own: a Sandwich for Bread, a First-Aid Kit for the Medium Healing Potion, Focus Pills, an Energy Drink, Duct Tape, a Road Flare...
  - `946 goods` writes them on every map of the game, so what she buys in Heaven goes with her. The map's `HeavenGoods22` pairs each item with its twin.
- **Where they come from**:
  - Heaven's stores sell the twin in its item's place (`TownStock` through `HeavenGood22`), each shop still by its trade.
  - Heaven's tables lay modern food: a sandwich in its wedge pack, a takeaway box, crackers, a fruit cup. Each gives the twin.
  - No container, shelf, prize or other store draws a twin: `CaveItemAllowed16` refuses them, and they have no weight in any draw.
- **Their pictures**:
  - 31 pictures were painted on the InvokeAI server (`art22/goods22_art.json`, two seeds each) and chosen on the contact sheets; the trail mix and the bandage were painted again on teal.
  - The trail mix and the bandage still carry a faint teal shadow at their feet.
  - `martial_arts` has no Cheese, so it has 39 twins.

### People on the pavements

- **Where they walk**:
  - The pavements are made from the streets' runs: the open ground beside the asphalt is a walk's goal, a zebra's tiles cross the street, and the square and second rows are walked between them.
  - A pedestrian (`ARDTownsfolk::bPave22`, one of the town's own townsfolk) walks a tile path over those tiles only, to a pavement 15 to 60 m off, more often ahead of it.
  - They come and go round her: 30 by day and 8 at night, within 90 m, made 25 m and more from her.
- **The cars**: a car waits for a pedestrian on the street as it waits for her (`CarYield22`).

### The city's sound

- **The bed**: The Sound Guild's city loops by day (`Heaven.City`) and its night loops by night (`Heaven.CityNight`), heard everywhere inside Heaven's walls.
- **The crowd**: `Heaven.Crowd` near the square by day: full within 25 m, none past 90 m.
- **Now and then**:
  - a horn from a car 15 to 80 m off, every 10 to 35 s (`Heaven.Horn`, SoundBits' horns);
  - a car passing within 10 m (`Heaven.PassBy`);
  - at night, the hum of the neon within 12 m (`Heaven.Neon`).
- **Source**: `SourceArt/heaven/city22.json`, converted by `rdc_sound_prep.py` into `audio_city` (ignored).

### Billboards and neon

- **Billboards**:
  - One low building in three that is wide enough has a billboard on its roof, its face 6.4 by 3.2 m toward the street.
  - Its picture is one of seven ads painted on the InvokeAI server: a burger, a car, a cola, an energy drink, a phone, a beach, a watch. All are without lettering. The running shoes were left out: a real maker's mark was painted on all three.
  - The face is in the sign faces' emissive material. Its glow is 0.9 by day and 3 at night.
- **Neon**:
  - Over the door of every shop, the market, the hotel, the clinic and the gear shop: a frame of four tubes in the trade's colour.
  - It stands 6 cm out from the wall piece's measured outer face.
  - Its light is 0.1 by day and 1 at night, through the signal lens's material.
- **The hotel's still**: the tavern's still and kegs outside the hotel are a condenser unit and recycling bins in Heaven.
- **Switches**: `rd.Neon22`, `rd.Peds22` and `rd.CitySound22` turn each of these off for the tests.

### Measured

- **Goods** (`884 heaven22_goods -Light`, `test_h22a.json`):
  - 40 twins, none missing, weighted, without a picture or of another kind, and none drawn.
  - Heaven's store had 27 lines, 15 of them twins and none of the items that have one; the market sold a Bandage Roll for 12 gold.
  - The tables held 57 modern food pieces and no bread or cheese meshes; one table's food gave a Sandwich.
- **Pedestrians** (`heaven22_peds`, `test_h22c.json`):
  - 30 walking round her for 40 s, 2190 readings, none on the asphalt.
  - One crossed at a zebra; 9 walked new ways; no car came within 3.8 m of one.
  - 8 at night.
  - The frame rate with them, without, then with again in one place: 13.2, 14.0, 14.9.
- **Sound** (`heaven22_sound`, `test_h22b.json`):
  - The day's bed at 0.85, the crowd 0.70 at the square and 0.27 at 65 m.
  - 9 horns in 30 s (with them made frequent); the night's set at night with no crowd.
  - Recorded in the square with every other set silent: -27.6 dB with the city's sound, -41.6 without (14.0 dB).
- **Neon and billboards** (`heaven22_neon`, `test_h22d.json`):
  - 16 fronts with 64 tubes and 30 billboards; dim by day (0.1, 0.9), lit at night (1, 3).
  - At midnight, read where each is on the screen with it on and off: the hotel's front 1.13 times as bright, a billboard 2.40 times.
  - The first neon stood inside Heaven's walls (13 cm out against walls 23 cm thick) and made no difference until it was measured on the wall piece.
- **The medieval things** (`heaven19_medieval`, `test_h22b.json`): none left in Heaven, the still's stand-ins included.

### After PR #129's review

- **Leaving Heaven**:
  - The city's sound and its walkers go when another town is loaded straight from Heaven (a fast travel, the map, a respawn), as when she walks out.
  - Outside the walls the walkers there are kept within her reach and none are made.
- **The goods**:
  - The twins are sold only inside Heaven's walls (a cleared camp's trader within 2 km had sold them).
  - A recipe that asks for an item with a twin takes the twin too: 26 recipe parts on each map, 7 on `martial_arts`.
- **Pedestrians**:
  - A walker's draws move with every failed search (six searches a call at most).
  - One that fails six times in a row is taken away, so none holds the traffic on a zebra.
  - The pavements are never read while the town is still being built.
  - At night, the walkers over the night's number more than 15 m from her go.
- **Neon**: it is lit again only when what it lights has changed.
- **Sound**:
  - The sounds draw on their own stream.
  - The loops follow the sound volume, and the hum follows the menu while it plays.
  - Nothing is written to a sound asset in play.
- **Measured again** (`884 heaven22_goods,heaven22_neon,heaven22_sound,heaven22_peds -Light`, `test_h22e.json`, all four pass):
  - **Goods**: 60 m out of the gate the store's list has no twin; no recipe part asks for an item without its twin.
  - **Neon**: the frame boxed where it is on the screen: the front 1.39 times as bright at midnight with the neon on, a billboard 2.51.
  - **Sound**:
    - with every other set silent, -22.9 dB with the city's sound against -43.6 without (20.7 dB);
    - 60 m out of the gate the bed, the crowd and the walkers are 0.
  - **Pedestrians**:
    - one crossed a zebra and none stood on one 15 s;
    - 20 walked new ways;
    - 13.0 frames a second with them against 13.7 without.
- **The test leaves no trace**: the goods' test gives back the gold and takes back what she bought and ate.

## The list of 2026-11-22: the traffic (phase 23: `946 traffic`, `RD/RDHeaven23.cpp`, `884 heaven23_*`)

The user's words: "the movement of vehicles in heaven is not natural, they follow each other instead of following a set route. none of the vehicles have anyone driving them and there are never any passengers on the buses ... have each driver with a goal tree ... follow typical traffic laws, traffic lights and signs. buses in particular should have a route, and passengers that get on and off of the bus."

### The road graph

- **Lanes**:
  - Each street's run between its crossings has a lane each way, on the right, 2.2 m from the street's middle.
  - A lane starts past the last crossing's zebra.
  - It ends at its stop line 4.2 m before the next zebra (the painted line is 1.9 m; at that line a bus's turn swept over cars waiting at the other lines), or turns back at a street's end.
  - The square's and the facility's streets are left to people.
  - Heaven has 142 lanes, every crossing with lights (as phase 19 laid them: 36 of 36).
- **Turns**: a car crosses a crossing on a curve from its lane's line to the next lane's start.
- **Routes**: the shortest by length, a turn back costing more.
- **Parking bays**: the free lay-bys and lot bays (those phase 19 left without a parked car): 68.
- **Bus stops and loops**: the bus stops are the street props of that kind, 16. The two loops each go from stop to nearest stop through one half of the town, east and west.

### The drivers

- **Who drives**: every car has a driver, a townsperson seated at the front left on the Drive clip.
  - The clip was made in Blender by `town_work_clips.py`: seated as at the table, both fists round a wheel's rim at ten to two, the wheel turning 4 degrees each way.
  - Measured on the clip: the fists on the rim to 0 cm, the wrists within their limits, no arm in the body, the largest step between frames 2.6 degrees.
  - It was given by `946 traffic` to the 177 townsfolk bodies on the NPC skeleton.
- **The goal tree by the hour** (each driver's times moved up to 45 minutes either way):
  - work 7:00 to 11:30 and 13:00 to 16:30;
  - lunch 11:30 to 13:00;
  - errands 16:30 to 18:30;
  - home in the evening and at night.
  - Each goal is a building (its home, its work, a place to eat, a shop), reached at the free bay nearest the lane by its door.
  - The driver parks there 20 to 60 s (at home at night until the morning), then drives to the next.
  - It looks at its goal again every 10 s as the hour moves on.

### The laws

- **Lights**:
  - A red light stops a car at its line.
  - On amber it goes on only when it reaches the line before the amber ends; otherwise it stops when it can stop at its usual braking.
- **Stop signs**: a car makes a full stop of a second at a stop sign. Heaven has no crossing without lights, so none applies there.
- **Left turns**: a left turn yields to an oncoming car that is moving, or that stands at its line to go straight or right.
- **Entering a crossing**: a car goes into a crossing only when its whole curve is clear: of cars waiting at the other lines by their footprints and 30 cm, and of every car crossing it now, along that car's whole remaining way.
- **On the curve**: its next few metres are checked against every car's footprint.
- **Distance and speed**: it keeps 2.6 m to the car ahead, and to her and to pedestrians. It eases its speed by the room ahead, down to the crossing's speed before the line.
- **Parking**: a car turning into or out of its bay is still in its lane.

### The buses

- **Loops**: the two buses drive their loops and stop at each stop for 6 s.
- **Getting off**: a third of their passengers get off, at least one, and walk away as pedestrians.
- **Getting on**: the people waiting there get on, up to six aboard.
- **Waiting and riding**:
  - Now and then someone comes to wait at a stop within 150 m of her, up to three a stop, none at night.
  - Those aboard sit in the bus's seats on the seated talk clip.

### By distance

- **Collision**: a car collides only within 30 m of her.
- **Drawing**: its driver and riders are drawn within 60 m and the car within 200 m.
- **Far cars**: a car beyond 150 m moves four times a second.
- **Switch**: `rd.Traffic23 0` holds them all still (tests).

### Measured

All five steps pass in one run: `884 heaven23_roads,heaven23_laws,heaven23_buses,heaven23_goals,heaven23_distance -Light`, `test_h23s.json`.

- **Roads**:
  - 142 lanes, 68 free bays, 16 bus stops, 2 loops.
  - 40 cars and 2 buses, each with its driver seated inside its footprint on its left.
  - Pictures of a driver at the wheel and of a street.
- **Laws** (120 s at 9:00):
  - Lights: no car crossed its line on red; 35 cars were read standing at a red line.
  - Gaps:
    - the least gap between two footprints anywhere was 55 cm (a bus passing a parked car);
    - between moving cars 1.17 m;
    - in a lane bumper to bumper 2.27 m.
  - Speed: one change over 16 m/s² in a quarter second (an amber stop); none from 10.7 to 6.5 m/s onto a curve, as there had been before the cars eased to the crossing's speed.
  - Routes: the median car drove six lanes; 21 parked at their goals.
- **Buses** (240 s):
  - Each stopped at the stops of its loop in turn: 12, 5, 11, 10, 1 and 8, 6, 2, 3.
  - 21 got on and 14 got off; up to three waited at a stop; 12 were seen seated.
- **Goals**:
  - At 9:00, 38 of 38 drove to work; at 12:00, 34 of 38 to lunch; at 21:00, 38 of 38 home.
  - 8 parked at lunch in the step's minutes.
- **Distance**:
  - Every car drawn and colliding as its distance from her says.
  - The frame rate driving, held still and driving again in one place: 22.7, 23.3, 22.4.
- **What could not be measured**: whether it looks natural. The rules were measured; the pictures are in the step's record.
- **How it got there**, the traffic failing its first runs:
  - The streets were not planned when the traffic was made (0 lanes): it is made once the town is built.
  - Lane by lane, 8 cars came of 142 lanes: one every 90 m over all of them now.
  - A gap measured along the line between two middles read a bus beside a parked car as 2.4 m "into" it: footprints by separating axes now.
  - Cars held each other in knots: a car going straight behind the car waiting across the crossing; two left turns waiting for each other; a bus's turn sweeping over cars at their lines; a car rolling into a turning bus; two cars turning across each other entering together.

### After PR #130's review

- **Lights**: a car on a green or amber that reaches its line before the red, at no more than the crossing's speed, is committed and goes. A car not committed stops 40 cm before its line. A car whose front is already past its line is never stopped there. A red run is counted at the line itself.
- **Crossings**: a car goes into a crossing only when all of it fits in the next lane beyond.
- **Goals**: a car whose way to its goal was lost, or that has no bay, looks again at its next look. At a lane's end it takes the next lane that leads to its goal.
- **Drivers and riders**: they are drawn by their own rule again when their car comes back into view (empty seats are never shown). They go with their car when it is made again.
- **Bays**: a car turning into or out of a bay waits for her and for pedestrians.
- **After a restart**: the streets' runs and parking are the static build's, kept.
- **Bus stops**: only the stops a bus calls at get people waiting. Those off the bus walk away only within her reach.
- **Far away**: the traffic stands still while she is far beyond the shield.
- **Measured again** (all five steps pass: `884 heaven23_roads,heaven23_laws,heaven23_buses,heaven23_goals,heaven23_distance -Light`, `test_h23x.json`):
  - **Laws**:
    - no red run, and no car stopped over its line by the light (one stood over it held by the queue ahead after going in on green);
    - the least gap between footprints anywhere was 66 cm, in a lane 2.12 m;
    - no change of speed over 16 m/s² in a quarter second;
    - every car drove three lanes or more.
  - **Buses**: their loops, 12 got on and 11 got off, and no rider was seen in a bus carrying nobody.
  - **Distance**: drivers drawn only within 60 m.
  - **Pictures**: a bus at its stop, from behind it along its lane.

## The list of 2026-11-22: the skyscrapers' level (phase 24: `948`, `RD/RDTower24.cpp`, `884 tower24_*`)

The user's words: "the skyscrapers and very tall office buildings can have the front door or entrances transport them to a new level that holds only the skyscraper's floors ... office furniture and rooms that look like an office, as well as typical rooms that are in a modern building, like bathrooms, offices, cubicles, datacenter rooms, equipment closets, a cafeteria ... if the player looks out the window, she should see the layout of the city, but not be able to interact with it ... procedurally generated."

### The way in and out

- **The door**: F at a tower's door in Heaven (a tower has 5 to 11 storeys; the offices three to five; only towers have the door) reads "enter <name> Tower (<n> floors)". The name comes from the tower's seed; its floors are the lobby and the floors drawn over it in the city (5 to 11).
- **The trip**: as into a dungeon (`DescendToCatacombs`): her state carried, the autosave, the way back kept 4.5 m before the door.
- **The level**: `heaven_tower` is a Save As copy of the castle with `bTower24`: no sets of rooms, no monsters, no map. The tower is built at play's start from the seed the game instance carries (`TowerSeed24`, `TowerFloors24`, `TowerName24`); played from the editor, from `TowerDefaultSeed24`.
- **The way back**: the lobby's glass doors. F reads "leave <name> for the street" and puts her back in Heaven before the tower's door.

### The tower

- **Its plan, every floor**: a grid of 14 x 14 cells of 1.5 m (the tower's 21 m square in the city), storeys of 3.5 m.
  - The core in the middle (6 m square): a stair and two lift shafts.
  - A corridor ring round the core.
  - Four bands of rooms along the windows, split by the floor's own stream; each room has a doorway onto the corridor.
- **Its floors**:
  - The lobby: a reception desk, two seating groups by the front windows, planters, palms, a water dispenser; a bathroom, a second bathroom and a closet in its east band.
  - A cafeteria floor and a data centre floor (by the seed, for towers of more than three and four floors).
  - The executive floor at the top: a boardroom across its north band, executive offices.
  - The other floors: offices, a cubicle farm (three floors in five), meeting rooms.
  - Every floor has a bathroom and an equipment closet.
- **Its rooms' furniture** (`SourceArt/heaven_tower/tower24.json`: the office, data centre and bathroom packs' meshes, each turned front to +X by a picture of it from +X and +Y):
  - offices: a desk and chair facing the door, a screen and keyboard, shelving and drawers against the walls, a cork board, a plant;
  - cubicle farms: pods of 3 m with partitions, a desk, a chair, a screen and a computer each, printers;
  - meeting rooms and the boardroom: a table along the room, chairs round it, a whiteboard on a solid wall; glass toward the corridor;
  - bathrooms: toilets in stalls, sinks, a towel dispenser, a bin, tiled walls and floor;
  - closets: storage shelving, a cleaning cart or a generator, a mop, a cabinet;
  - the cafeteria: kitchen units with a sink, a fridge, a water dispenser, tables with chairs;
  - the data centre: two rows of server racks facing a cold aisle, cooling units at the ends.
- **Walls, floors, glass**: the engine's cube stretched over each wall, slab and pane, in the office packs' materials, drawn through one instanced component per mesh and material (47 for 5 floors: 4,269 boxes and 784 pieces).
- **The stair**: a switchback of two flights of ten steps (17.5 cm by 30 cm) a storey, a half landing between them; the steps are thin treads, so the flight above leaves 3 m of head room.
- **The lifts**:
  - Two, at the core's east face: one stops at every floor, the express runs between the lobby and the top.
  - F on the platform rides to the next stop (the top's next is the lobby); F at a landing calls it; while it is elsewhere a gate keeps her out of the shaft.
- **Lights**: 28 point lights moved to the rooms and corridor of the floor she is on, and a ceiling light on every other cell of every floor.

### The city from the windows

- **The pictures**: as she goes in, the city is captured from the tower's middle at three heights (the level's own eye on the floors at 0.12, 0.5 and 0.88 of its floors), at the hour she enters, in cube pictures of 768 (HDR scene colour), the clouds hidden.
  - The tower's own pieces are moved out of the town's instanced components for the capture and put back; its other components and the people in it are hidden from it.
  - Each picture is taken twice: the first of a capture can draw instances where they stood a moment before.
  - The game instance keeps them.
- **In the level**: a sphere 80 m round her floor draws the picture of the nearest height, by the view's way. It is turned by the tower's turn, so the street before the lobby's doors is the street before the tower's door in Heaven.
  - The castle's height fog is turned off inside the tower, and so are bloom and lens flare: the picture's sky, as bright as a real sky, bloomed over the windows.
- **Not reached**: the city is a picture: nothing in it can be walked to or touched.

### Measured

On the tallest tower, Zenith Tower (11 floors): `884 tower24_enter,tower24_floors,tower24_stairs,tower24_lifts,tower24_window,tower24_exit -Light`, `test_t24i.json`; the lifts again in `test_t24j.json`, the windows in `test_t24k.json`.

- **Enter**:
  - F named "Zenith Tower (11 floors)".
  - The level opened with its seed, name and floors, no monsters, and none of the table's pieces missing: 9,258 boxes and 1,788 pieces in 47 instanced components.
  - She stood in the lobby.
  - The three pictures took 63 ms to capture together. Their 18 faces read back with light in each.
- **Floors**: 11 floors, 143 rooms:
  - 1 lobby, 12 bathrooms, 11 closets, 54 offices, 3 cubicle farms, 12 meeting rooms;
  - 1 cafeteria, 2 data centre rooms, 6 executive offices and 1 boardroom.

  Every floor has a bathroom and a closet, and no room is empty. There is a picture of each kind from its doorway.
- **Stairs**: she walked (her own movement) every flight from the lobby to the top floor: the landing, the half landing, across it, the next landing. On each point she stood within 45 cm, 84.6 cm over it (her capsule's half height).
- **Lifts**:
  - The local lift rode floor by floor to floor 10 and back to the lobby, her height 84.6 cm over each floor. The express rode from the lobby to floor 10 and back.
  - From floor 2's landing, the lift's gate held her 2.1 m from the shaft's middle while the lift was in the lobby. F called it, and she walked onto it.
  - Before the express's own door in the lobby, F named the express and called it down from the top (not the local lift, whose door is 1.5 m away).
- **Frame rate**: 62 frames a second in the lobby, 54 at the windows of floor 5 (the editor's play, 1280 x 720).
- **Way back**: F at the lobby's doors named the street. She stood in Heaven 4.5 m from the tower's door.
- **The windows against the city** (`blender_numpy/t24_view_check.py`, `test_t24k_views.json`):
  - What was compared: the city's picture in the tower, the tower hidden, from the floor's middle each way, against Heaven itself. Heaven was pictured from the capture's point with the tower taken out, at the pictures' hour.
  - Correlations of grey levels at 64 x 64: north 0.996, east 0.986, south 0.992, west 0.994, up 0.847, down 0.999. Two different ways: 0.21.
  - How it got there: the first pictures had a pale veil over near buildings in four ways (0.26 to 0.45). It was the volumetric clouds, drawn in their render-target mode without depth in a cube capture. They are hidden while the pictures are taken, so the windows' sky has no clouds.
- **What could not be measured**: whether the rooms read as an office to a person (pictures are in the record).

### After PR #131's review

- **F at a tower's door**: it yields to a nearer door, container or person, but not to the tower's own door leaf.
- **The lifts' doors**: F takes the nearest door's lift (the two doors are 1.5 m apart).
- **The pictures**:
  - They are taken at the level's own eye height for their floor.
  - The clouds are hidden while they are taken.
  - Their memory is let go once she leaves the tower; a new game or a load forgets the tower (a load in the tower builds it from its default seed).
- **The save**: one dungeon key for all towers ("tower").
- **The lights**: the corridor's first, none inside the core, 7.5 m reach.
- **The platform**: 2.6 m, so it fits the shaft.
- **The lobby**: the space under the stair is filled.
- **Music**: no castle music in the offices.
- **The tests**:
  - They take the tallest tower.
  - They read back the pictures' faces (a blank cube fails).
  - They call the express from its own door.
  - They compare the windows at the pictures' hour.

## The list of 2026-11-22: the fortress's defenders (phase 25: `947 monsters`, `RD/RDFortress25.cpp`, `868 fortress25 -lv heaven_fortress`)

The user's words: "vary the Heaven dungeon with soldier variants, medics, differently colored/designed drones and differently colored/designed mechs from the Dystopia and Sci-fi packs. also use aliens and monsters from the Aliens Warrior Pack."

### The kinds

Twenty-four kinds beside 909's five, from `SourceArt/heaven_fortress/defenders25.json` (29 in all, by the fortress's tiers):

| Tier | Kinds |
|---|---|
| 1 | Kratos Defender, Kratos Defender (grey), Kratos Sentry Drone, Kratos Medic |
| 2 | Facility Guard (red), Facility Guard (blue), Grenadier Drone, Grenadier Drone (olive), Kratos Field Medic |
| 3 | Kratos Operative (black), Kratos Flame Trooper, Kratos Medic (masked), Alien Warrior |
| 4 | Kratos Heavy Gunner, Kratos Combat Mech, Alien Brute, Alien Stalker, Bomber Drone, Kratos Chief Medic |
| 5 | Kratos Siege Mech (the mech's second colourway, 1.6 times), Alien Sniper, Alien Warlord, Alien Hunter, Alien Exterminator |

- **Where they come from**: the Sci-Fi Characters Pack Vol 2's defender, guard and operative on its 43 clips; the Dystopia pack's flame trooper, gunner and mech on the mech pack's clips; its four medics on Vol 2's; Military_Pack's gun drone and Military_Drone's quadcopters on their own clips; Aliens_Warrior_Pack's fifth warrior on its own clips and the brute, stalker and sniper on its clips (the skeletons made compatible); the Creatures_Pack's Alien and Exterminator.
- **Colours and designs**: a kind's variant is its pack's numbered colour set, slot by slot (`M_X_1` to `M_X_n`, `M_X` to `M_X_Set_0n`; `FRDMonsterDef::Materials`). None of the packs has material instances: their sets are whole materials. The mech's crimson set is its Set_02.
- **Medics heal their side** (`FRDMonsterDef::bHeals`): in a fight a medic stops for the most hurt of its side within 10 to 13 m (with a sight line, missing 15 % of its hit points or more), heals it 30 to 40 % of its hit points with a green glow, then waits 5 to 6 s. No pack has a healing clip: the medics' heal is the defenders' reload. The first medic fights with blows only, the others shoot too.
- **Drones fly**: the gun drone and the quadcopters (2.5 times the pack's size, 13 cm tall otherwise) fly 1.5 to 2 m up; the quadcopters' own clips carry them up, so they are lowered by their mesh and dropped onto the floor when they die (`FRDMonsterDef::DeathDrop`). The quadcopters have no hit or death clip: they shudder in their idle and fall.
- **On every map**: `910` copies them with the fortress's own kinds to every map (weight 0 there; made again from the fortress's at every run) and gives them their wild band, tiers 26 to 30; the castle's kinds' weights in the fortress are cut so the defenders are two in three of each tier. `947 monsters` runs after `909` (909 leaves them out of its weights).
- **909's kinds' feet** are corrected by their measured bottoms (the Operative stood 9 cm into the floor, the Commander 9 cm and the tank 19 cm over it).

### Measured

`868 fortress25 -lv heaven_fortress` (`test_f25l.json` in `SourceArt/mistward`):

- **All 29 kinds**: spawned in rows of six (pictured), each one's bones moving in its clip.
  - Each variant's colour set drawn on its mesh, slot by slot.
  - The walkers' drawn bottoms are within 8 cm of the floor (an idle's sway moves them some 6 cm from run to run).
  - The flyers fly 1.5 to 2 m up.
- **Each alone**: a shooter shot her at least once from 7 m, and a fighter struck her at least once from 1.2 m. Each one:
  - lost hit points to a blow of a fifth of them;
  - when killed, was dead, its death clip moving its body (all but the quadcopters, which have none);
  - if a drone, lay on the floor when dead.
- **Medics**: each of the four, in a fight with her, healed a trooper at half its hit points by exactly its share (the trooper's 30 to 40 %), 1.5 to 5.7 s into the fight.
- **What could not be measured**: how the kinds read to a player in a fight, and their voices.
  - The packs have no sound sets of the drones', aliens' or creatures' own on this map: they speak with the Horned set as 909's do.
  - Several soldiers' rifles are separate meshes on other skeletons and are not in their hands.

### After PR #132's review

- **A heal cut short** (a flinch, a stun, a curse) no longer turns the medic's next shot into a heal.
- **Curse of Silence** breaks off a heal under way.
- **Who is healed**:
  - A medic heals its side before anything else it would do in a fight (in reach of her it struck and never healed).
  - It heals no boss or elite, never another medic's patient, and faces its patient.
  - A heal is at most twice the medic's own share's worth.
- **A dead drone** reaches the floor before its body is frozen.
- **A kind's colour set** is looked for in its material's own folder first; each swap is printed.
- **On the other maps**: `910` makes the fortress's kinds again there at every run; `869` gives the colour sets' materials the skeletal-mesh usage (brokenspire's and the caves' too).

## The list of 2026-11-22: the fortress's tiers 1 and 2 an office building (phase 26: `947 building`, `868 fortress26 -lv heaven_fortress`)

The user's words: "the heaven dungeon's assets should be taken from any modern city building pack, looking like the inside of a modern building for the first two levels ... also use props and buildings from the sci-fi city packs for Tiers 1-2."

- **The theme**: tiers 1 and 2 are drawn in the `Office` theme (`TierThemes`); tiers 3 and 4 stay the steel facility and 5 the mixed until phase 27. A theme takes `<Theme>.<piece>` for any piece the castle names, so every wall, floor, ceiling, piece of furniture and prop of those tiers is the office's.
- **The shell** (boxes merged in Heaven's and Office_Environment's materials):
  - walls of white plaster over a wood or plaster dado, with a steel skirting and white pilasters and cornice;
  - terrazzo, wood and grey stone floors;
  - white ceilings with a light panel in each tile;
  - doorways of plaster with a steel frame, and glass doors in steel frames on the castle's hinges;
  - white columns, daises and grey carpets, each in the box the castle's piece took.
- **The furniture**: Heaven's modern pieces under the castle's names (brokenspire's, copied as text): desks, chairs, tables, beds, bookshelves, shelf racks, desk lamps for candles, ceiling lights for chandeliers, the media wall for the hearth, the cooker for the cauldron and tripod, the gear shop's bench, vice and bin for the forge, anvil and quench tub, the fridge, filing cabinet, tool chest, bin, safe and locker for the containers, with their words.
  - The castle's other pieces as an office's: the brazier and pedestal as planters, the altar a desk, the thrones executive chairs, the stool a chair, the tool board a cork board, the banner and painting a picture, the trunk Heaven's chest (its word Heaven's), the pew a bench, the shrine a water dispenser on a white plinth (its glow and prayer kept).
  - The cells, gratings and the tiers' seals: steel frames round glass in the castle pieces' boxes, the cell's door a glass leaf on the castle's hinge.
  - Left out: the gibbets, cages, chains, shackles, bones, hay, firewood, debris, tombs, crystals, loose books and wall weapons.
  - Not themed: the traps' plates and chains and the weapons she finds, the game's own things in every theme.
- **The things by the walls**: the fortress's machines' places hold office things from the tower's table: printers, water dispensers, shelving, planters, drawers and storage shelving.
- **Modern in the game's rules too**: the Office theme is modern as Heaven's is (`IsModernTheme26`): no fires in torches, candles, braziers or hearths, white lamps, upright locker doors, the containers' words.

### Measured

`868 fortress26 -lv heaven_fortress` (`test_f26e.json` in `SourceArt/mistward`):

- **Tier 1** (the first hall's set): 8102 instances of the office's own meshes, none of the facility's, 1237 of Heaven's furniture, 227 office things by the walls.
- **Tier 2** (a set generated once the first was cleared): 7839 office pieces, none of the facility's, 1380 of Heaven's furniture, 186 office things.
- **No castle mesh left**: every visible mesh component of both sets (doors and containers too) against the castle's own pieces' meshes (the traps' and weapons' left out): none.
- **Pictures**: the first hall, and three rooms of the tier-2 set.
- **What could not be measured**: whether it reads as a modern building to a player. The pictures show the white walls and ceilings with their panels, glass doors, desks and shelves, and the barracks' beds.

## The list of 2026-11-22: the fortress's tiers 3 to 5 an open alien world (phase 27: `947 study27,world`, `RD/RDAlien27.cpp`, `868 fortress27 -lv heaven_fortress`)

The user's words: "eventually opening up into a wider open world that uses the Alien Planet, using its procedural content generation graphs to generate areas that can be explored by the player for Tiers 3-5".

- **The pack's graphs and the game's sets**: the Alien Planet's PCG graphs (`PCG_Main` and its subgraphs) read a landscape (Get Landscape Data, the surface sampler, its projections) and splines; the game's sets are tiles of instanced floors with no landscape, and running PCG in a packaged game would need its plugin, its graphs cooked and a ground they can sample. The plan's spike chose the third of its ways: the pack's baked point data placed by the game. Those are the level instances its graphs copy (`LI_*`: flowers, ice crystals, moss, mushrooms, plants, roots, pebbles, spike formations, trees). `947 study27` reads each one's mesh instances into `SourceArt/heaven_fortress/alien27.json` (58 clusters, 709 parts), and the game lays them itself, as the caves lay the Hyper kit's dressing.
- **The sets are open**: tiers 3 to 5 are drawn in the `Alien` theme, which the generator's `OpenThemes27` names open. A set keeps its plan of rooms and hallways and its tiles (so monsters, maps, progress and saves are unchanged), but:
  - it has no walls, ceilings, doorways, doors, columns, torches, hung things or room lights;
  - every tile is the pack's ground (`MI_Ground01`, triplanar);
  - where the plan has no tile, a ridge of the pack's rocks stands, and next to a walked tile an invisible blocker two rooms high keeps her (and the monsters' sight) out;
  - the clearings and paths are dressed with the clusters: plants and pebbles to walk through, and spike formations and trees that block the tiles they stand on (a tree its trunk's), never a lane's;
  - the castle's furniture is the steel facility's where it has one, else the office's modern pieces (an outpost's camp); the crystals are the pack's ice crystals, the hall's pillars spike rocks of their height, and the tombs, bones, candles, cages and pews are left out.
- **Seals**: a shut tier is sealed across the path by a force wall (a see-through cyan sheet, brighter at its edges: `M_Alien27_Force`) and its blocker, not a grating.
- **The sky**: the sun, sky atmosphere, sky light and fog (components of the generator) come up over 1.5 s as she walks into an open set, and go as she walks back into the office.
- **No draw from the plan's stream**: each solid tile, clearing and path has a stream of its own (a hash of the set's seed and its place).

### Measured

`868 fortress27 -lv heaven_fortress` (`test_f27e.json` in `SourceArt/mistward`): with tier 3 open and tier 4 shut, the tier-3 set had 3 force walls; then a set of each tier, generated:

| Tier | Ground tiles | Blockers | Ridge rocks | Pack instances | Blocking clusters' tiles blocked | Walked | Frames a second |
|---|---|---|---|---|---|---|---|
| 3 | 4633 | 1802 | 5461 | 15879 | 73 of 73 | 17.1 m | 19.5 |
| 4 | 4839 | 1759 | 5481 | 15351 | 63 of 63 | 10.2 m | 22.3 |
| 5 | 4529 | 1769 | 5394 | 16811 | 72 of 72 | 5.7 m | 23.2 |

- **No shell**: none of any theme's wall, ceiling, doorway or column meshes in the three sets, and no castle mesh left (traps' and weapons' aside).
- **The sky**: 1.0 in each open set after 2.5 s, 0.0 back in the office's first hall.
- **The walk**: from a clearing's middle each of four ways for 1.5 s; the farthest is in the table, her feet never more than 2 cm under where she began.
- **Pictures**: one from each tier's first clearing.
- **The packaged game**: `package_mistward.ps1`'s `fortress_open` run goes down into the fortress and opens tier 3 round her (`-RDOpen27`); its mark is written once the sky is up.
- **What could not be measured**: whether the world reads as alien to a player; the pictures show rock spires, white ice formations and a purple sky over brown ground.

