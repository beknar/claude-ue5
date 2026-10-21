# Dungeon types

The Fab library cache (`I:\game assets\3d fab library data cache\VaultCache`, 251 packs, read only) holds the parts for about 16 kinds of themed dungeon. This page lists each kind, the packs it would be built from and the enemies that suit it. Nothing here is built yet, except the stone dungeon the dungeon levels use now.

## How this was found

- Every `.uasset`, `.umap`, `.fbx` and `.obj` path in the cache was listed: 218 603 files.
- Each pack's static meshes were counted by name for kit parts (walls, floors, ceilings and roofs, doors and gates, arches and columns, stairs, corridors), containers and light sources.
- For the promising packs, a spread of mesh names was read to see whether they form an interior kit or a scene.

What that means:

- **Judged from names only.** No pack was opened in the editor for this page. A wall's size, whether a kit sits on a grid, and how a pack looks in the dungeon's light are not checked.
- **Kit strength.** A **strong** kit has its own walls, floors, doors and ceilings for whole rooms and corridors. A **workable** kit covers most of a room but has gaps (no ceiling, few doors). A **thin** kit is a handful of modules that needs walls or floors borrowed from another pack.
- **Containers.** Every container in the dungeon must open, with a body and a moving part (CLAUDE.md). Few fantasy packs ship a lid as a mesh of its own; the ones found are noted. Elsewhere a lid is cut from the body in Blender, as was done for the current dungeon.
- **Mesh counts.** These are the pack's `SM_` static meshes, variants included.

## Summary

| # | Theme | Tone | Kit | Main packs |
|---|---|---|---|---|
| 1 | Stone dungeon and crypt | Fantasy | Strong (built) | MysticDungeon, HallowedDepths, DarkHalls |
| 2 | Castle keep and its cells | Fantasy | Strong | Medieval Castle, Castle, Castle of Eternal Mist |
| 3 | Dwarven deep halls | Fantasy | Strong | Dwarven Citadel |
| 4 | Cathedral and mausoleum | Fantasy | Strong | Crownfall, Fantasy Cemetery, Modular Church |
| 5 | Jungle temple ruins | Fantasy | Workable | Lost Temple, Ancient Mayan Ruins |
| 6 | Sunken pirate ship | Fantasy | Workable | Underwater Ship |
| 7 | Haunted mansion | Fantasy / horror | Workable | Albert Mansion, Victorian Grand Mansion, Anemoia |
| 8 | Desert tomb | Fantasy | Thin | Egyptian Palace, Desert Ruins |
| 9 | Frozen Norse halls | Fantasy | Thin | Frozen Norse Environment |
| 10 | Marble temple of the gods | Fantasy | Thin | Olympus, Artemis Temple |
| 11 | Sewers | Modern | Workable | Sewer, Subway Tunnel |
| 12 | Prison and asylum | Modern horror | Strong | Prison, Abandoned Hospital |
| 13 | Military bunker | Modern | Strong | Underground Bunker, Bunker Constructor |
| 14 | Derelict spaceship or station | Sci-fi | Workable | Space Colony 2086, Cargo Ship, Spaceship Kit |
| 15 | Exclusion-zone ruins | Modern | Workable | Silent Zone, SnowTown, Post-Soviet World |
| 16 | Steampunk works | Steampunk | Thin | Steampunk Zeppelin Station |

For the current game the best next themes are 2, 3 and 4. Their kits are complete, and their enemy packs are already in the cache. The castle (`/Game/Castle/`) is already in the project: `770_rd_level.py` uses its pieces.

## Fantasy themes

### 1. Stone dungeon and crypt (built)

**What it is.** Grey stone corridors and halls, crypt chambers with columns, vaulted ceilings, cells with bars, candles and braziers. This is the dungeon of `random_dungeon_level` and its copies.

**Rooms it suggests.** Crypts, cell blocks, a chapel, storerooms, a great hall.

**Variant.** An ossuary: Bone Temple's bone columns, skull piles and wooden gate set into HallowedDepths' crypt walls. Bone Temple has no walls or floors of its own.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| MysticDungeon | `DungeonB8d1de910e988V1` | 499 | Walls (straight, curved, broken), stone floors, stairs, columns, arches, beams, vases, boxes |
| HallowedDepths | `ModularD4c0132f37b5bV1` | 121 | Crypt and chamber walls, floors and roofs, cell walls with doors, crypt doors, torches, chandeliers |
| DarkHalls | `ModularD6eb3e091f31dV1` | 92 | Corridor walls and floors, cell bars and doors, vaulted ceilings, arches, braziers, bone piles |
| Gothic Props | `Medieval3c5a0a999b62V1` | 71 | Wooden chest, candles, chandelier, books, flags |
| Bone Temple (variant) | `TempleOfc489afe603f3V1` | 392 | Bone columns, skull piles, skeletons, wooden gate, lanterns |

**Enemies.** The Creatures Pack (`Creatureebd7c217dd72V1`) the dungeon uses now.

### 2. Castle keep and its cells

**What it is.** The inside of a castle: dressed stone walls, towers, gates and portcullises, great halls with tables and chandeliers, and a cell block below. Castle of Eternal Mist adds a ruined keep, with broken walls, damaged columns and bending stairs.

**Rooms it suggests.** Gatehouse, great hall, kitchens with ovens, armoury (archery storage), tower stairs, dungeon cells, a ruined wing.

**Containers.** Castle Collection has a small chest and chest variants; whether their lids are separate is not checked.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Medieval Castle | `Untitled6097a9e98924V1` | 443 | Castle stone walls, corners and pillars, tower walls, stone floors and stairs, castle doors, gates, **dungeon cell doors**, windows, roofs |
| Castle | `CastleGra8dd40785514V1` | 514 | Brick walls and arches, vault pillars, gates, bridges, towers (already in the project) |
| Castle of Eternal Mist | `Fortresse9ac538c2d72V1` | 903 | Ruined and damaged walls, arched walls, columns, buttresses, many stair shapes, round towers |
| Castle Collection | `NaniteMed0ea78ca92ddV1` | 65 | Chests, wall torches, chandeliers, candelabra, big table, oven, fire pit, sofa, paintings, coins |
| Hive Sherwood | `ModularM8974323abc38V1` | 178 | Stone walls, gates, wall candles, torches, barrels |

**Enemies.** Knights (`KnightsPa8758c08168cV1`), Orcs (`OrcsPackc67eac8a7210V1`), Fantasy Enemies (`FantasyEbb19142cf9b5V1`).

### 3. Dwarven deep halls

**What it is.** A carved underground citadel: a central hall and side halls with ribbed vaults, massive columns, grand gates, carpeted stairs, guardian statues and a treasure room with a grave. Old Mine and the Hyper Cave toolkit add timbered mine tunnels and raw cave between the halls.

**Rooms it suggests.** Gate hall, main hall, side halls, treasure vault, forge, mine shafts, collapsed caves.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Dwarven Citadel | `DwarvenCabdd49ceafa3V1` | 629 | Central, main and side hall walls, floors and ceilings, rib vaults, columns, gates, stairs, treasure room, fire stands, weapon racks, barrels |
| Old Mine | `OldMinec015335c6173V1` | 58 | Timbered tunnel walls, cave, beams, mine carts and rails, tools, caged lamps |
| Hyper Cave Building Toolkit | `HyperCavb3712dcc7a1aV2` | 60 | Cave tunnels and floors |

**Enemies.** Dwarf Pack (`DwarfsPa3aec1fa9fedeV1`), and the Creatures Pack's troll and spider.

### 4. Cathedral and mausoleum

**What it is.** A Gothic cathedral fallen to ruin, with nave, aisles, altar, staircases, chained incense burners and broken knight statues. Below it are the family mausoleums and catacombs, with coffins and urns.

**Rooms it suggests.** Nave, side aisles, altar, bell-tower stairs, chapels heaped with bones, mausoleum chambers, catacomb corridors.

**Containers.** Fantasy Cemetery's chest has a lid of its own (`SM_Chest`, `SM_ChestLid`), the only one found among the fantasy packs. Coffins come from the Church packs and Fantasy Cemetery.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Crownfall | `Crownfal9007bfe3fd94V1` | 220 | Nave, aisle and staircase walls, ceilings and floors, columns, arched doors, altar floor, sexpartite vault ribs, candles, incense chandeliers, knight statues |
| Fantasy Cemetery | `DarkFantf94d90678ca5V1` | 150 | Mausoleum walls, mausoleum and church doors, stone interior floors, stairs, coffins, **chest with its lid**, urns, lamps |
| Modular Church | `ModularNa9cd4cc34fc2V1` | 56 | Church walls, pillars, doors, spike walls, benches, bone piles, candelabra |
| Church (two packs) | `ChurchVO26117403ac7aV1`, `ChurchVOca9d77edfde9V1` | 89, 170 | Coffins, candle sets, church lights, banners, crosses |
| Religion Memorial | `Memorialdc2e6e3778b7V1` | 95 | Burial caskets, urns, graves |
| Cemetery Vol 1 to 5 | `Cemetery95f086fd545bV1` and four more | 10 to 24 each | Gravestones and doors for the crypt entrances |

**Enemies.** Fantasy Enemies, Half Creatures (`Creeping3d10d77cc8c7V1`), the Creatures Pack's daemon.

### 5. Jungle temple ruins

**What it is.** An overgrown stone temple: carved walls and ceilings, broken pillars, stairs, pots, braziers, cave walls and cliffs where the temple meets the rock.

**Rooms it suggests.** Pillared halls, a sunken stairwell, altar chambers, cave passages, a relic vault.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Lost Temple | `LostTemp266268c70f6dV1` | 153 | Walls, floors, ceilings (whole and broken), pillars, stairs, braziers, pots |
| Ancient Mayan Ruins | `AncientE801541d5dfa8V1` | 256 | Ruin wall and column modules, face-carved walls, dragon pillars, cave walls, cliffs, ceilings |
| Relics | `RelicsVO6599ed7f4515V1` | 62 | Altars, totems, runes, cages, pottery |
| Mountain Shrine | `Mountain26adfeda91b6V1` | 47 | Shrine pieces and lanterns |

**Missing.** Few doors.

**Enemies.** Insects (`Creature75fc4bca0363V1`), the Creatures Pack's spider, Primitive Characters (`Primitiv7dfa5fb63264V1`).

### 6. Sunken pirate ship

**What it is.** The inside of a wrecked galleon on the sea floor: cabin walls and ceilings, decks on several levels, trapdoors, port doors, and coral and starfish growing over everything.

**Rooms it suggests.** Captain's and officers' cabins, the gun decks, the forecastle, the hold, a treasure room.

**Containers.** Large and treasure chests (`SM_LargeChest`, `SM_TreasureChest`).

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Underwater Ship | `Underwat0ec9e2b52d4eV1` | 200 | Cabin walls and ceilings, deck floors (cabin, officer, cannon decks, forecastle), pillars, stairs, port doors, trapdoor, chests, lanterns, coral |
| Underwater Shipwreck | `Shipwrecac715137c13dV1` | 74 | The wreck's outside |
| Pirates Age (two packs) | `AgeofPir9ceff62e01daV1`, `PiratesA63b3bb235eb8V1` | 34, 91 | Pirate props |

**Enemies.** Underwater Monsters (`Monsters75adcbb6378fV1`), drowned sailors from NPC Sailor (`NPCSailocf6f496c697fV1`).

### 7. Haunted mansion

**What it is.** A decaying manor: panelled and papered walls, a stone basement with archways and torches, grand stairs, sconces, curtains, old furniture and bones.

**Rooms it suggests.** Entrance hall, parlours, library, bedrooms, servants' stairs, basement and wine cellar.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Albert Mansion | `PostApoc34b9ba5dbabfV2` | 314 | Walls and corners, floor and ceiling tiles, front, secondary and basement doors, stone archways, stairs, torches, sconces, bones |
| Victorian Grand Mansion | `Victoria45380ca66db1V1` | 110 | Mansion interior |
| Anemoia | `AnemoiaM888d251fd7a4V1` | 183 | Walls, wallpapers, floors, ceilings, columns, arches, doors, stairs, period furniture |
| Horror and Decay (four packs) | `Horroran6063b9e39a4dV1` and three more | 7 each | Decals and decay dressing |

**Enemies.** Cartoon Zombies (`CartoonZ036f52cb99cbV1`), Half Creatures.

### 8. Desert tomb

**What it is.** A pharaoh's palace and tomb: tall walls, columns and a throne room, with sand-filled ruin rooms, skeletons and a dragon's bones.

**Rooms it suggests.** Throne room, pillared halls, a pool chamber, burial rooms, collapsed ruins.

**Missing.** No sarcophagus was found by name, and the palace kit is small (49 meshes). Desert Ruins' walls and doors would make the corridors.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Egyptian Palace | `Egyptian73d618ed5db8V1` | 49 | Throne-room walls and ceiling, high walls, columns, floors, a pool, stairs |
| Desert Ruins | `AncientDa096d1af8ffdV1` | 170 | Walls, corners, floors, doors and frames, stairs, open boxes |
| Bones (three packs) | `BonesVOL305b97738b72V1`, `BonesVOL9cee370dfeafV1`, `BonesVOLe8852def785eV1` | 73 to 112 | Human and animal skeletons, skulls, bones |
| Dragon Graveyard | `DragonGr9ee1a3847e21V1` | 34 | A dragon's skull, spine and bones |

**Enemies.** The Creatures Pack, Humanoid Creatures (`Humanoid717b7b55acdbV1`).

### 9. Frozen Norse halls

**What it is.** Ice-bound halls of the north: carved wall, arch and column modules, giant columns, a gate, stairs, ice formations and light shafts.

**Rooms it suggests.** A long hall, a gate chamber, ice caves, a frozen throne room.

**Missing.** Only 102 meshes, with no floors or ceilings by name. Floors would have to come from another stone kit.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Frozen Norse Environment | `FrozenNoe90973929678V1` | 102 | Wall, arch and column modules, giant columns, gate, stairs, ice, glaciers, a fire pit |

**Enemies.** Vikings (`VikingCo8c1d138f17feV1`).

### 10. Marble temple of the gods

**What it is.** White marble and gold: arches, sculpted columns, banners, chandeliers and floor tiles, with Artemis Temple's walls, doors and statues.

**Rooms it suggests.** Colonnades, a sanctuary, statue galleries, fountain courts.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Olympus | `OlympusT3b66343ef8c0V1` | 74 | Modular arches, sculpted columns, floor-base pieces, chandeliers, flags |
| Artemis Temple | `MythicArcec06cdd9819V1` | 274 | Walls, floors, pillars, doors, stairs, bridges, statues, fountain, vases |
| Ancient Tech City | `AncientT82a9305f7729V1` | 104 | Big walls with windows, round pillars, indoor tiles, indoor trees |

**Enemies.** Fantasy Enemies.

## Modern and sci-fi themes

These would suit another game's tone. They are listed because their kits are good.

### 11. Sewers

**What it is.** Brick, cinder-block and concrete tunnels, arched walls, gates and doors, pipes and wall lights, joined to a subway tunnel with tracks.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Sewer | `ModularSb35746afa6c6V1` | 113 | Walls (brick, cinder, concrete, arch, beam), floor, stairs, gates, doors, tube doors, wall lights, pipes, electrical cabinets |
| Subway Tunnel | `CitySubwf94dbf93df76V3` | 125 | Walls, wall doors, floor, tracks, lights, signs |

**Missing.** No ceilings by name.

**Enemies.** Insects, Parasites (`Parasiteef437a93f62aV1`).

### 12. Prison and asylum

**What it is.** A concrete prison of cell doors, cages, showers and spotlights, joined to an abandoned hospital with medical cabinets, a modern hospital wing and a quarantine tent.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Prison | `Prisonaf6a5ae7cebdV2` | 188 | Walls, cell doors and frames, wall cages, floors, columns, stairs, showers, ceiling lights, beds |
| Abandoned Hospital | `Abandone6deed178f9ddV1` | 214 | Walls of 50, 100 and 200 cm, wall windows, doorways and doors, floors, ceilings, medical cabinets |
| Modern Hospital Vol 1 and Vol 3 | `ModernHo5d5150050914V1`, `ModernHo5efe1cc89a77V1` | 56, 42 | Hospital interiors |
| Quarantine Tent | `Quarantid68819234a95V1` | 121 | Medical tent and equipment |

**Enemies.** Prisoners (`NPCPriso06b9d3827babV1`), Parasites, Half Creatures.

### 13. Military bunker

**What it is.** A Cold War bunker of concrete walls, curved corridors, bunk rooms, kitchens and evidence rooms, and a larger modular bunker with grilled floors and a central stairwell.

**Containers.** Military crates with separate tops, lockers and cabinets with doors (MC Environment), and evidence boxes with tops (Underground Bunker).

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Underground Bunker | `ColdWarU1bf612c33c35V1` | 152 | Walls (straight, curved, with doors), floors, pillars, stairs, shelves, evidence boxes with tops |
| Bunker Constructor | `BunkerCo6ca90ed01ea2V3` | 477 | Wall modules of 60 to 400 cm, floor sections, doors, a central stairwell, lamps, a bathroom |
| MC Environment | `Military047fcd641de6V1` | 292 | Military crates with tops, lockers, cabinets |

**Enemies.** Soldier Future 1 to 3 (`SoldierFc34a3b65960cV1`, `SoldierF7a1edcef15cbV1`, `SoldierFb1b6c59c7cacV1`).

### 14. Derelict spaceship or station

**What it is.** A dead colony ship or station: modular corridors, ship gates, hibernation pods, crew quarters, kitchens, offices with cubicles, a data centre, a reactor room.

**Containers.** Crates with doors (Cargo Ship), dumpsters with lids (Space Colony 2086).

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Space Colony 2086 | `SpaceCol59efa29fc905V4` | 719 | Wall and floor modules, doors, offices, kitchens, bathrooms, dumpsters with lids |
| Cargo Ship | `SciFiSpa2a74d31eec85V1` | 158 | Walls, floors, ship gates, pillars, stairs, hibernation pods, crates with doors |
| Spaceship Kit | `Spaceshi00915ff66758V1` | 118 | Wall modules, doors and gateways, floors, stairs, beds, reactor |
| Orbital Base | `OrbitalB114e559e635bV1` | 221 | Dome doors, storage doors, support columns, bathrooms |
| Data Center | `DataCentc5d76ba66050V1` | 99 | Walls, floors, ceilings, doors, server walls |
| Sci-Fi Experiment | `SciFiExp7da0bf2ea391V1` | 12 | Laboratory pieces |

**Enemies.** Aliens Warrior (`AliensWa55ac04712f66V1`), Parasites, Sci-Fi Mercenaries (`SciFiMerc1c8aafd3790V1`).

### 15. Exclusion-zone ruins

**What it is.** Basements, stairwells and flats of abandoned Soviet panel blocks and factories: damaged concrete walls and floors, elevator shafts, cupboards with doors, radiators, rubble.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Silent Zone | `ToskovPo4f99b21e9269V1` | 886 | Concrete walls and floors, whole and damaged; a factory |
| SnowTown | `PostSovi058174b830d2V6` | 1102 | Panel walls, stairwells, elevator shafts and doors, hallway doors, cupboards with doors |
| Post-Soviet World | `PostSovi8286dbc9511bV3` | 306 | Walls, doors, kitchen cabinets with doors |
| Volstok District | `VolstokDa99a623310e0V1` | 791 | Walls, floors, ceilings |

**Enemies.** Dystopia NPCs (`NPCDysto63a1cd454c27V1`), the Creatures Pack's mutant.

### 16. Steampunk works

**What it is.** Brass and iron corridors of a zeppelin station, a gear-driven main gate, a café, a 1900s factory and a Victorian train.

| Pack | Cache folder | Meshes | What it gives |
|---|---|---|---|
| Steampunk Zeppelin Station | `Steampun2faf9b2b76c5V1` | 161 | Corridor walls, doors, a geared main gate, floors, columns |
| Steampunk Cafe | `Steampundf0c1de2a93bV1` | 104 | Café interior |
| 1900s Industrial | `1900sInd139834383358V1` | 153 | Factory props |
| Victorian Train Interior | `Victoria35ca9db825e8V1` | 119 | Carriage interior |

**Enemies.** None in the cache fits.

## Not a dungeon kit

**Volcano Land** (`VolcanoL816d51ae88f7V2`) has lava, lava rock and terrain, but no walls or floors. It could dress another theme (a lava floor in the dwarven halls), not build one.

## Building one

A new theme follows the stone dungeon's way. Its packs are imported into `Content/`, and a script like `770_rd_level.py` fills the generator's `Pieces` table with them. That script fits each mesh to the dungeon frame with `Adjust`: front +X, footprint centred, floor at z 0.

The furnishing code places pieces by name and skips a missing one silently. A theme therefore needs:

- the names the generator asks for, or furnishing code of its own behind a flag;
- every container cut into a body and a lid or door, with its hinge, and checked by `container_check.py`;
- broken walls with backings and seals (`wall_check.py`);
- its own monsters, with their hit points following the dungeon's rule;
- a step in the level's scripted test.
