# Towns, cities and villages

The Fab library cache (`I:\game assets\3d fab library data cache\VaultCache`, 251 packs, read only) holds the parts for about 22 kinds of settlement. This page lists each kind, the packs it would be built from and what it looks like. Its companion for interiors is [dungeon_types.md](dungeon_types.md).

Some of these packs already build the project's outdoor levels:

| Level | Scripts | Settlement packs it uses |
|---|---|---|
| castle_level | `290`-`383` | Castle, Medieval Fantasy Village |
| The fantasy castle level | `400`-`421` | Fantasy Castle, Medieval Lake Village |
| sf-city-level | `700`-`714` | Mega City, Monolith Megastructure, Red Echo, Diner, MC Environment, Silent Zone |
| random_level (the town) | `750`-`756` | Hivemind, Hive Sherwood, Castle |
| random_isometric_village_level | `780`-`787` | House Forge, Village Collection, War Camp Collection, Castle Collection, Old Windmill, Modular Church, Hivemind, Hive Sherwood |

## How this was found

- Every `.uasset`, `.umap`, `.fbx` and `.obj` path in the cache was listed: 218 603 files.
- Each candidate pack's static meshes were counted by name for buildings, walls, roofs, doors, windows, streets and pavements, fences, lights, market stalls and waterside pieces.
- For each pack, a spread of mesh names and its maps' names was read.

What that means:

- **Judged from names only.** No pack was opened in the editor for this page, so scale, grid fit and looks are not checked. The packs already used by a level are the exception.
- **Kit strength.**
  - A **strong** kit builds whole streets: modular buildings, or many whole buildings, plus streets and street furniture.
  - A **workable** kit builds a believable place but repeats itself, or lacks streets or interiors.
  - A **thin** kit is one landmark or one street, and needs the rest from another pack.
- **Mesh counts.** These are the pack's `SM_` static mesh files, variants included.
- **Level instances.** A pack that ships whole buildings as level instances (`LI_...` maps) can be placed building by building, as the town level does with Hivemind's.

## Summary

| # | Settlement | Era | Kit | Main packs |
|---|---|---|---|---|
| 1 | Medieval harbour and market town | Medieval | Strong (built) | Hivemind, Hive Sherwood |
| 2 | Medieval farming village | Medieval | Strong (built) | House Forge, Village Collection |
| 3 | Lakeside fantasy village | Medieval | Workable (built) | Medieval Lake Village, Medieval Fantasy Village |
| 4 | Castle and fortress town | Medieval | Strong (built) | Castle, Castle of Eternal Mist, Fantasy Castle |
| 5 | Feudal Japanese village | Feudal Japan | Strong | Japanese Village |
| 6 | Desert city and bazaar | Ancient | Workable | Desert Ruins, Egyptian Palace, Bazaar |
| 7 | Temple city of the ancients | Ancient / fantasy | Workable | Artemis Temple, Olympus, Ancient Tech City |
| 8 | Vertical city of arches | Fantasy | Thin | City of Height |
| 9 | Pioneer and frontier settlement | Medieval / frontier | Workable | Hyper Building System, Hyper Farming System |
| 10 | European riverside old town | Modern Europe | Strong | Riverside European Village, Barcelona |
| 11 | Seaside promenade | Modern | Workable | Waterfront Baywalk, French Village |
| 12 | Fishing harbour | Modern | Strong | Docks (four packs), Dockhouse, Seaside Docks |
| 13 | Wild West town | 1800s | Thin | Saloon |
| 14 | Victorian steampunk city | 1900s / steampunk | Workable | Steampunk Zeppelin Station, 1900s Industrial |
| 15 | American small town | Modern USA | Strong | Meridian (five packs), Diner |
| 16 | East Asian shopping street | Modern | Workable | Stylized Street, Korean Restaurant |
| 17 | Modern city block and works | Modern | Workable | Residential Buildings, Warehouse Big Pack, Roadside Construction |
| 18 | Soviet panel-block district | Modern | Strong | SnowTown, Post-Soviet World, Volstok District |
| 19 | Abandoned exclusion-zone town | Modern ruin | Strong | Silent Zone |
| 20 | Wasteland shanty town | Post-apocalyptic | Strong | Wasteland, Container District |
| 21 | Military base | Modern | Workable | MC Environment, Desert Outpost |
| 22 | Sci-fi megacity | Sci-fi | Workable (built) | Mega City, Monolith Megastructure |
| 23 | Frontier colony on another world | Sci-fi | Workable (built) | Red Echo, SciFi Cliff, Megastructure Fallen City |
| 24 | Tropical sci-fi town | Sci-fi | Workable | Tropical Sci-Fi City |

Themes 8 and 13 are single landmarks rather than towns. That makes about 22 settlements that can be built, plus two that need another pack's streets.

## Medieval and fantasy

### 1. Medieval harbour and market town (built: random_level)

**What it is.** A stone-and-timber port town: cobbled streets and slab paths, market stands and carts, a tavern sign, weapon stands and smithies, and cargo ships at the quays. Its buildings come as whole level instances. Hive Sherwood adds a wooden outlaw village with towers, stands and stone walls.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Hivemind | `ModularM2744bb9f44d1V1` | 274 | Whole buildings as level instances (`LI_Building_01a` ...), stone and wood walls, wall doors and windows, floors, staircases, cobbles (4 m, 8 m, patches), market carts and stands, tavern sign, anvil, torches, cargo ship |
| Hive Sherwood | `ModularM8974323abc38V1` | 178 | Village map (`L_Sherwood_Village`), stone walls, gates, towers, roofs, wooden stands, torches, wall candles |

### 2. Medieval farming village (built: random_isometric_village_level)

**What it is.** Timber and stone cottages built from modular walls, roofs, doors and windows, with fences, food stands and carts. Around them are wells, a windmill, wanted boards, a war camp and a small church.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| House Forge | `HouseFor7fa57d25bf7aV1` | 380 | Modular house walls, roofs and overhangs, doors, windows and shutters, foundations, ramps, fences, food stands, carts, sign boards, chests |
| Village Collection | `NaniteMe95836a52e931V1` | 75 | Old well, camp windmill, wanted boards, bell, carts, benches, house furnishings |
| Old Windmill | `OldWindm8855a461cca0V1` | 63 | A modular windmill, millstones, sacks, barrels |
| War Camp Collection | `NaniteMee1c943429865V1` | 42 | Barricades, ballista, weapon stands, pillory, guillotine, camp fire |
| Modular Church | `ModularNa9cd4cc34fc2V1` | 56 | Church walls, pillars, doors, roof |
| House Collection | `NaniteMoe58d71f688e2V2` | 67 | Concrete and wood house walls with doors and windows, roofs |
| Modular Wooden Buildings | `ModularW0e8fc5138170V1` | 116 | Wooden shacks, side sheds, balconies, a lookout tower, awnings, food stand |
| Modular Shop Stand | `NaniteMee7b3ebe5432eV1` | 33 | Market tables of fruit, fish and cheese |

### 3. Lakeside fantasy village (built: the fantasy castle level, castle_level)

**What it is.** A misty village by a lake: whole house and church sets, farmhouse walls, dirt roads and side paths, wooden bridges and boats. Medieval Fantasy Village adds storybook houses with dormer roofs and chimneys.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Medieval Lake Village | `Medieval051d3826569fV1` | 253 | House sets, church set, farmhouse walls, soil road and side paths, bridges, boats, stand lights, stone walls; day and foggy maps |
| Medieval Fantasy Village | `Medieval9ff219ea5d87V1` | 52 | Houses, door modules, roofs with windows, chimneys, a bridge; a town map (`L_Medieval_Town`) |
| Flower Meadows | `FlowerFi80e568d548cbV1` | 36 | A water mill with its tunnel, doors and crates, flower fields |

### 4. Castle and fortress town (built: castle_level, the fantasy castle level)

**What it is.** A castle with its town below the walls:
- Castle supplies towers (round, square, six-sided), gatehouses, bridges and walls.
- Castle of Eternal Mist is a ruined fortress of arch bridges, round towers and broken walls.
- Fantasy Castle has a far skyline of towers and bridges, with houses and roads.
- Crownfall is a cathedral that could stand in the town square.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Castle | `CastleGra8dd40785514V1` | 528 | Towers of every shape, main gate, walls, arches, bridges, distant-tower level instances |
| Castle of Eternal Mist | `Fortresse9ac538c2d72V1` | 903 | Ruined and whole walls, arch bridges, round towers, buttresses, stairs; day and night maps |
| Fantasy Castle | `FantasyCa53eee4a8c4fV1` | 121 | Towers, bridges, houses, roads, a temple door |
| Medieval Castle | `Untitled6097a9e98924V1` | 443 | Castle tower walls and roofs, food stands, carts, a Viking boat, cobble and tile floors |
| Crownfall | `Crownfal9007bfe3fd94V1` | 220 | A Gothic cathedral, inside and out |
| Castle Collection | `NaniteMed0ea78ca92ddV1` | 65 | Furnishings, chests, wall torches |

### 5. Feudal Japanese village

**What it is.** Thatched houses and fishing huts by a river, rope and log bridges hung with lanterns, a watch tower, and temple stairs and fences. A mountain shrine and a martial-arts school add a temple quarter.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Japanese Village | `FeudalJa5826d4645d77V1` | 411 | Houses and fishing huts as maps of their own (`L_House_01`, `FishHut_01` ...), thatched roofs, walls, bridges with lanterns, temple stairs and fences, a tower, boats |
| Mountain Shrine | `Mountain26adfeda91b6V1` | 47 | Shrine roofs and railings, lanterns, ginkgo trees |
| Martial Art School | `MartialA80b49c1b5f79V1` | 77 | Dojo wall and floor modules, tatami, training weapons |
| Sacred (temple pack) | `SacredTr0586bf4556a7V1` | 89 | Temple buildings, stone, wood and ornamented bridges, entrance walls, a river |

### 6. Desert city and bazaar

**What it is.** A sun-baked town of mud-brick and stone buildings, with a palace of tall walls, columns and a pool, palms, and a covered bazaar heaped with spices, bread and nuts.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Desert Ruins | `AncientDa096d1af8ffdV1` | 170 | Buildings in several sizes, walls, corners, doors, stairs |
| Egyptian Palace | `Egyptian73d618ed5db8V1` | 49 | House and high-building modules, entrances, columns, a pool, palms |
| Bazaar | `Bazaara21ec9b47d5eV1` | 95 | Market stalls and covered stands, stone wall modules, food and spice piles, sacks, jugs |
| Ancient Ruins | `AncientRb1654f0f3adfV1` | 37 | A temple front, a boat, pottery, a statue |

### 7. Temple city of the ancients

**What it is.** White marble and gold. Artemis Temple's walls, doors, bridges, statues and fountains; Olympus's sculpted columns and arches; Ancient Tech City's overgrown central building, paved plazas, temple bells and waterfalls.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Artemis Temple | `MythicArcec06cdd9819V1` | 274 | Walls, floors, pillars, doors, stairs, bridges, statues, fountain |
| Olympus | `OlympusT3b66343ef8c0V1` | 74 | Modular arches, sculpted columns, floor bases, banners |
| Ancient Tech City | `AncientT82a9305f7729V1` | 104 | Central and ground buildings, big walls with windows, twelve pavement pieces, temple bells, a waterfall |

### 8. Vertical city of arches (thin)

**What it is.** A city stacked up a cliff: building modules joined by arches and bridges, hung with ivy. It has five building and bridge maps but no streets.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| City of Height | `CityofHe7fe3b1e13294V1` | 50 | Building modules, arches, straight and angled bridges, stairs, ivy |

### 9. Pioneer and frontier settlement

**What it is.** A settlement the player builds:
- Hyper's building system brings thatch, wood and stone walls, roofs, doors, ceilings and stairs, which break apart as geometry collections.
- The farming system brings crop plots and a well.
- Wooden defence walls and gates ring the camp.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Hyper Building System | `HyperBui1731c0595630V4` | 241 | Thatch, wooden and stone walls, sloped roofs, doors, ceilings, stair ramps, defence walls and gates |
| Hyper Farming System | `HyperFar1913831baea8V4` | 287 | The same building parts, plus crops, growing plots, sprinklers, a well |

## Historic and modern Earth

### 10. European riverside old town

**What it is.** A canal town:
- **Riverside:** floating houses, river walls, bridges, boats, kerbed streets with drains, stalls and a café, with houses and the café as level instances.
- **Barcelona:** its two squares (Barcelona Square and Royal Square) add arcades, vaults, terraces with balustrades, shutters and street lamps.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Riverside European Village | `Riverside66b5591de69V1` | 247 | Walls, roofs, floating-house foundations, river walls, bridges, boats, street paths, kerbs and drains, stalls, café level instances |
| Barcelona | `Barcelon278bd2768826V1` | 132 | Two square maps, arches and vaults, terrace balustrades, shutters, street lamps, benches |

### 11. Seaside promenade

**What it is.** A warm coastal strip: modular houses and restaurants along a pier, palm trees and street lamps. French Village adds a village street of houses, a shop and a restaurant. Feather's house on a cliff, with its lighthouse, could stand at the end of the bay.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Waterfront Baywalk | `WaterFro41acdec3874cV1` | 87 | Wall, door and window modules, small houses, restaurant level instances, a pier, street lamps, palms |
| French Village | `European7848079e356aV1` | 38 | Houses, a store, a restaurant sign, a bridge, background houses |
| Feather | `HouseOnA1eccd9aedfedV3` | 67 | A house, a lighthouse, fences, a garden swing |

### 12. Fishing harbour

**What it is.** A working fishing harbour:
- **The waterfront:** many dock and pier sets, some broken; sheds; a warehouse dockhouse with ramps, doors and tarps.
- **On the water and quay:** boats, wrecks and lifeboats; crab and lobster cages, fish racks, buoys; electric poles and park benches.
- **Medieval variant:** Harbour Collection's broken ship and fish nets would suit the medieval town instead.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Docks (three packs) | `DOCKSVOL4bdecbe992c7V2`, `DOCKSVOL5b0e0b42ffebV1`, `DOCKSVOL5fb2de584cb7V1` | 143, 171, 135 | Dock and pier sets, sheds, boats, canoes, wrecks, cages, fishing gear, lights; day and night maps |
| Docks (a fourth pack) | `Untitled24493581f5aeV1` | 103 | Tall and short piers (whole and destroyed), railings, a boat lift, buoys |
| Dockhouse | `TownBuilfbff62006d30V1` | 135 | A warehouse dockhouse: walls, floor, roof, doors, ramps, boat stands |
| Seaside Docks (two packs) | `SeasideD3dc347cebe38V1`, `SeasideD229dd5e93c0dV1` | 129, 54 | Pier pilings, gutting tables, lobster traps; boat wrecks |
| Boatyard | `Boatyarda8095a8f3311V2` | 66 | Boat piers and stairs, dock doors, dunes and beach grass |
| Harbour Collection | `NaniteMe648799fb008dV1` | 29 | A broken ship, small boats, anchors, fish nets and traps (medieval) |

### 13. Wild West town (thin)

**What it is.** One saloon, with its walls, windows, swing doors, sign, bar and barrel stands. Desert Ruins' buildings could give the rest of the street.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Saloon | `SaloonInc266338d4316V1` | 55 | Saloon wall and window modules, doors, a sign, the bar, cart wheels |

### 14. Victorian steampunk city

**What it is.** Brass and iron. A zeppelin station with a clock tower, geared lift bridges, ticket towers and an airship. Around it are a steam café, a 1900s factory street with road, pavement and lamps, and a Victorian grand mansion.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Steampunk Zeppelin Station | `Steampun2faf9b2b76c5V1` | 161 | Station walls and floors, clock-tower roof, metal bridges with gears, ticket tower, airship, fences, lights |
| Steampunk Cafe | `Steampundf0c1de2a93bV1` | 104 | A café, inside and out |
| 1900s Industrial | `1900sInd139834383358V1` | 153 | A main building and its parts, road, sidewalk, street lamps |
| Victorian Grand Mansion | `Victoria45380ca66db1V1` | 110 | Mansion wall modules, doors, windows |

### 15. American small town

**What it is.** A small American town:
- **Houses:** a modular suburban house (55 Elm Street) and a trailer home (14 Widow St).
- **Town buildings:** a school, a church with a belfry, and a strip mall with a laundromat, repair shop and arcade.
- **Streets:** sidewalks, parking blocks, newspaper stands and sale signs.
- **On the roadside:** a diner and a motel.

Each Meridian pack has a building map and day and night lighting maps.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Meridian VOL21 55 Elm Street | `Meridian3d66b9f81a2bV1` | 670 | A modular two-storey house (walls, floors, roofs, deck, foundation, chimney), furnished; a garden |
| Meridian VOL31 14 Widow St | `Meridian728df1119abbV1` | 595 | A modular mobile home (chassis, floors, walls, roof), furnished; a yard |
| Meridian VOL57 School | `Meridian6313d7fa92beV1` | 1004 | A school: classroom walls, pillars, ceilings, offices |
| Meridian VOL12 Holy Pines Church | `Meridian05debe7fc5baV1` | 712 | A church with belfry, walkways, concrete walls, sidewalk |
| Meridian VOL55 King Wash Strip | `Meridianc08ef9cf16aaV1` | 795 | A strip mall: shop fronts, sidewalks and corners, parking blocks, road decals, signs |
| Diner | `Dinerece17cafb0bbV1` | 56 | Store and entrance modules, a road, diner and open signs |
| Motel Prop Pack | `MotelPro8fe319a2a7b9V1` | 96 | Reception and room signs, motel furniture |
| Roadside Construction | `Roadsidedcc6474504d0V1` | 70 | Asphalt, cobbles, sidewalks, kerbs, road signs, cones, barriers |

### 16. East Asian shopping street

**What it is.** A narrow street of small shops: a lottery shop, cloth and street shops, roller shutters and air-conditioning units, broken road. Korean Restaurant adds a street module with a bank, a hospital, an electronics shop and bike-repair signs.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Stylized Street | `Stylized01654488916dV1` | 119 | Shop fronts, walls, windows, shutters, roofs, road (whole and broken), a light tower, produce sacks (stylised, not realistic) |
| Korean Restaurant | `KoreanRe20033eb0a1dcV1` | 103 | A building, a house, street modules, road, street lamps, shop signs, the restaurant |

### 17. Modern city block and works

**What it is.** Apartment blocks and the industrial edge of town:
- **Apartment blocks:** a modular apartment kit (loggias, balconies, townhouse doors, rooftop plant).
- **Industry:** a big warehouse with loading docks, an unfinished concrete building.
- **Roadworks and fun:** roadworks; a casino and a water park for something different.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Residential Buildings | `Residentd73b7d35efe5V1` | 64 | Apartment wall, corner and window modules, loggias, balconies, entrances, roofs and rooftop units |
| Warehouse Big Pack | `Warehous9a3b440ef7a3V1` | 365 | Warehouse walls, roofs, roof windows, loading-dock doors, ramps and kerbs, awnings, carts |
| Unfinished Building | `Unfinishefd623cfe7e2V1` | 56 | Concrete pillars, ceiling beams, stairs, rubble |
| Roadside Construction | `Roadsidedcc6474504d0V1` | 70 | Roads, kerbs, roadworks |
| Casino | `Casino66e943afe469V1` | 87 | A casino interior with signs and lights |
| Water Slide System | `WaterSli266c22b8baa0V1` | 47 | Water slides, flumes, towers, signs |

### 18. Soviet panel-block district

**What it is.** Snowy estates of nine- and sixteen-storey panel blocks, shipped as level instances, inside and out. It has courtyards with playgrounds and sandboxes, asphalt and streetlights, shops of tinned food, broken roads and bridges.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| SnowTown | `PostSovi058174b830d2V6` | 1102 | Panel houses as level instances (9 and 16 floors), balconies, stairwells, elevators, roofs with snow caps, snowy roads, shop goods |
| Post-Soviet World | `PostSovi8286dbc9511bV3` | 306 | Panel-block walls and entrances, asphalt plates, streetlights, playgrounds; a world map (`PanelkiWorld`) |
| Volstok District | `VolstokDa99a623310e0V1` | 791 | Building panels, corners and windows, pavements, kerbs, broken asphalt, bridges, cars; main and damaged buildings |

### 19. Abandoned exclusion-zone town

**What it is.** A dead town after a disaster. Destroyed homes of 2 to 9 storeys and a ruined school, each a map of its own; a fairground wheel; portacabins and radiation signs; damaged concrete everywhere.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Silent Zone | `ToskovPo4f99b21e9269V1` | 887 | Destroyed residential buildings as maps of their own (2, 3, 5, 8, 9 floors), a destroyed school, a factory, damaged walls and floors, roads, a Ferris-wheel cabin, portacabins |

### 20. Wasteland shanty town

**What it is.** Survivors' towns:
- **Wasteland:** prefab houses, a church of boards and a bar.
- **Container District:** a shanty of shipping containers with panel walls, cloth and bridges.
- **Post-Apocalyptic House:** a ruined house with façade walls and a garage door.
- **Around them:** a junkyard, salvage shacks and a lookout tower.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Wasteland | `Wastelan4f403e80f2f9V2` | 368 | Prefab houses, a church of boards with its tower, a bar, bridges, a bus |
| Container District | `Containe928ce87af3e1V1` | 332 | Container houses, panel walls, windows, barriers, wooden bridges |
| Post-Apocalyptic House | `Untitleda1c9ee255c33V1` | 238 | Façade walls (door, window, garage), shed roofs, a chimney |
| Albert Mansion | `PostApoc34b9ba5dbabfV2` | 314 | A ruined mansion, inside and out, sidewalks |
| Scene Junkyard | `Junkyard681d135e7856V1` | 61 | Junk piles in fourteen arrangements |
| Modular Wooden Buildings | `ModularW0e8fc5138170V1` | 116 | Shacks, sheds, a lookout tower |

### 21. Military base

**What it is.** A garrison: apartment blocks in six variants as level instances, a watch tower, a hangar and antennas. Desert Outpost adds a sandbagged outpost with a water tower, warning signs and a crashed helicopter.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| MC Environment | `Military047fcd641de6V1` | 292 | Building walls, corners, entrances, windows, roofs, apartment buildings as level instances, a watch tower, hangar beams, antennas |
| Desert Outpost | `DesertIn18ff75bc7d6eV1` | 119 | Outpost buildings, a water tower, signs, a crashed helicopter |

## Science fiction

### 22. Sci-fi megacity (built: sf-city-level)

**What it is.** Towering blocks and landing pads, holograms, flying ships and street antennas. Monolith Megastructure adds tall and large modules joined by bridges.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Mega City | `OpenWorl56658a0bf262V1` | 120 | Buildings (bottom, top, large modules), interior modules, landing pads, holograms, flying ships, street lamps |
| Monolith Megastructure | `Monolithf7dc4e86718fV1` | 48 | Tall, large and wall modules, bridges, generators, lamps |

### 23. Frontier colony on another world (built in part: sf-city-level)

**What it is.** A red-planet outpost:
- **Red Echo:** circular and stacked habitat modules, landing pads with ships, antennas.
- **SciFi Cliff:** a station on a cliff.
- **Megastructure Fallen City:** a city built round a crashed ship.
- **Polar Station:** a research base in the cold.
- **Alien Planet:** the land around them.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Red Echo | `ScifiDes14d5b0a45640V1` | 116 | Building, circular, alien and interior modules, landing pads, flying ships, antennas |
| SciFi Cliff | `ScienceFbdeba3ae0cfaV1` | 56 | Circular, square and large modules, corridors, a bridge |
| Megastructure Fallen City | `ScienceF19fa072c5e08V1` | 128 | Modules and entrances, a spaceship hull, gateways |
| Polar Station | `SciFiPol163b623d8961V1` | 78 | A polar research station, hangar doors, lockers |
| Alien Planet | `AlienPla6b4311c58bbdV2` | 305 | Alien trees, spikes and flowers; four planet maps |

### 24. Tropical sci-fi town

**What it is.** A bright island town: square houses, big buildings and towers among palms and coral, with market stands.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Tropical Sci-Fi City | `ScienceF164336681386V1` | 144 | Big buildings, square houses, towers, roofs, market stands, palms, coral, rocks; a town map |

## Land around them

These packs have no buildings, but they make the country between settlements:

| Pack | Cache folder | Meshes | What it is |
|---|---|---|---|
| Wildlands | `Wildland74a54c71e702V1` | 165 | Pine forest (with a snow variant), modular pier, fences |
| Flower Meadows | `FlowerFi80e568d548cbV1` | 36 | Meadows and a water mill |
| Frozen Norse Environment | `FrozenNoe90973929678V1` | 102 | Glaciers, ice, mountains, Norse arches |
| Quarry Slate | `AfricanS5f01daad2a87V1` | 65 | A slate quarry with water |
| Volcano Land | `VolcanoL816d51ae88f7V2` | 67 | Lava fields and lava rock |
| Fences Vol 3 | `Fencesan5ea60020be36V1` | 35 | Fences and walls |

## Building one

A new settlement follows one of the existing ways:
- **Generated in play:**
  - the town (`ARTTownGenerator`, start square built by `752`);
  - the village (`AIVVillageGenerator`, its `Pieces` filled by `780`);
  - each fills a table of pieces from the packs, fitted to the generator's frame.
- **Hand-placed by a numbered script:** castle_level and sf-city-level.

Packs that ship whole buildings as level instances or maps of their own (Hivemind, SnowTown, MC Environment, Riverside; Japanese Village and Silent Zone as maps) fit the town's way. Modular kits (House Forge, Meridian, Hyper, Residential Buildings) fit the village's way: walls, roofs and corners built per house.
