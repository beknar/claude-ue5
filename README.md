# claude-ue5

An Unreal Engine 5.8 project built almost entirely from scripts. The scripts drive the running editor over Python remote execution, Blender + numpy prepare the source art, and a C++ module holds the games that generate themselves in play. The project has twenty-seven levels (and three menu levels): a photo studio and five character showcases, three hand-built worlds with walk-in buildings, three procedural worlds (a town, a dungeon, an isometric village), the dungeon again with melee combat, blood, sound and music, four magic levels built on it (a caster, a dark caster with a sword, a rogue, a choice of four heroes), the full dungeon game with four heroes to choose (and the Summoner, kept off its menu), the same game as a castle (Mistward Castle: themed tiers, rooms of other shapes, traps, prisoners, shields, teleporters, bosses, six heroes and a final boss) with a room to try its Martial Artist in, its starting town (Brokenspire: a walled town generated for every new game, with its trades, people and quests, and a continent of wilderness round it with five more cities), the dungeons under those cities (the catacombs under the holy city of Vel Morrath, The War Engine under the forge city of Ashenreach, the sewers under the port of Graymourne, the black tower's halls in the mage city of Kethrys Spire, the mechanised fortress under Heaven's research facility), and a space fighter. Most have a recorded demo route or a scripted test, and a showcase video.

**The current game** is Mistward Castle's, packaged as a standalone Windows (Shipping) game by `pipeline/package_mistward.ps1`: the hero menu (`mistward_castle_select`, six heroes) opens Brokenspire (`brokenspire`), the wilderness round it leads to Vel Morrath, Ashenreach, Graymourne, Kethrys Spire and Heaven and down into their dungeons (`vel_morrath`, `war_engine`, `sewers`, `kethrys_spire`, `heaven_fortress`), and the castle building's Mistgate into Mistward Castle (`mistward_castle`), where the final boss, Aurorim, opens a door back to Brokenspire at his death. The castle is described in [mistward_castle: the castle](docs/levels/mistward_castle.md#mistward_castle-the-castle), the town in [Brokenspire](docs/levels/brokenspire.md), the continent in [the wilderness](docs/levels/wilderness.md), and the cities and their dungeons in [Vel Morrath](docs/levels/vel_morrath.md), [Ashenreach](docs/levels/ashenreach.md), [Graymourne](docs/levels/graymourne.md), [Kethrys Spire](docs/levels/kethrys_spire.md) and [Heaven](docs/levels/heaven.md). The game the castle was copied from, `random_dungeonmagic_level5`, is described for players in [the game now](docs/levels/random_dungeonmagic_level5.md#random_dungeonmagic_level5-the-game-now), specified requirement by requirement in **[docs/spec.md](docs/spec.md)** (with its configured values, its tests and its known issues) and its architecture in **[docs/design.md](docs/design.md)**.

This repository is **source only**: the pipeline scripts, the C++ source, project config and small data files. Unreal assets (`Content/`), source art binaries, sounds, renders and the third-party packs they come from stay local. See [What's not in the repo](#whats-not-in-the-repo).

## Capabilities

What the project does today, in short; [docs/capabilities.md](docs/capabilities.md) has the whole list.

- **Characters and animation:** a MetaHuman conformed to a 3D scan; characters from six kinds of source on the same third-person controls; IK rigs and retargeters built from Python; feet that stay put; clips made in Blender (the heroes' casts and cuts, the townsfolk's work, the farm animals, Aurorim's wings); the dungeon's heroes with armour, weapons, shields and a torch fitted to them; the monster gallery's 55 usable kinds placed by tier, and eleven machines and eleven drowned for the cities' dungeons.
- **Worlds:** hand-built from pack maps (a meadow, a photo studio, a medieval village, a castle with a lake village, a sci-fi city) and procedural in C++ (a town, a dungeon, an isometric village) generated ahead of her as she walks, with doors and containers that open and maps of what she has discovered; third-person, isometric and chase views.
- **Combat** (`random_dungeoncombat_level`): melee weapons, monsters that notice her, chase, fight and die, blood and wounds, sound placed in the world and music that follows the fight.
- **Magic, the rogue, the choice of hero and a face that moves** (`random_dungeonmagic_level` to `random_dungeonmagic_level5`): a fire spell, then 30 spells from tomes; a rogue with daggers and a crossbow; a menu of heroes; armour, weapons, loot, crafting, rings and five tiers of rooms.
- **Mistward Castle** (`mistward_castle`): level 5's game as a castle with themed tiers, rooms of other shapes, shields, a torch, traps, teleporters, prison cells, bosses, special rooms and slashes, the Martial Artist and the Summoner, harvests and scrolls, monsters that shoot, an arena with an audience, vaulted and domed ceilings, an autoplay mode that plays any hero for a set time, the Rogue's stealth, a final boss (Aurorim, an angel of four wings: a thrown lance, light from above, wind round his fists, a door back to Brokenspire at his death), and the six heroes balanced against each other tier by tier, each growing her own way as the tiers open (hit points, damage, spells and chi by tier: [the numbers](docs/levels/mistward_castle.md#mistward_castle-the-castle)).
- **Brokenspire** (`brokenspire`, the castle's starting town): a walled town of 500 m generated by rules from a new seed every game (a square with its well, quest board, market and teleport circle; a smithy, a trader, a healer, a temple, a storehouse, a tavern, a chapel and its graveyard, barracks, a mill, a still, a witch's hut, homes lived in, burned or boarded up; a wall with towers and a gate onto the wilderness), every building walked into through a working door with containers that open, 32 kinds of townspeople (the elder, the scholar and the guard captain with 16 quests, the others with lines of their own) going between their jobs (gardens, pens of farm animals, cooking fires, the tavern's seats, the smith's anvil), a day of an hour with its sun and moon, gold, a trader who buys and sells, a healer, a smith, a temple's blessing and a storage, gardens to harvest and ovens to bake at, training dummies, a portcullis raised by levers, falls that hurt, the castle building whose hall (guarded by 5 to 10 monsters that keep to it) leads into Mistward Castle and back with her things, a dungeon-style minimap and a map of the town from above ([Brokenspire](docs/levels/brokenspire.md)).
- **The wilderness** (on `brokenspire`, round the town): a continent of 300 by 300 km made from one seed as she comes to it, only a 2 km square of its ground at a time: 29 terrain templates (the spec's 28 and Ashenreach's burned plain) blended into each other (grasslands to glaciers, volcanoes, canyons and marshes), rivers, lakes and roads, Vel Morrath (a cathedral city over the catacombs, [its document](docs/levels/vel_morrath.md)), Ashenreach (a forge city over The War Engine at the edge of a burned plain, [its document](docs/levels/ashenreach.md)) Graymourne (a fog-bound port over its sewers on the northern coast, [its document](docs/levels/graymourne.md)) Kethrys Spire (a mage city round a black tower sealed for a century, north-west of Graymourne, [its document](docs/levels/kethrys_spire.md)) and Heaven (a modern city of towers, office blocks, shops, streets and cars under a shimmering shield, [its document](docs/levels/heaven.md)) built as she nears them (Brokenspire dropped 2 km off and built again), villages, camps, ruins, stone circles, caves and monster lairs found and named, the captain's two quests out in the wilds, a sky of clouds, stars and a moon, weather and wind, hills and hollows, farms of six crops in rows, wild animals that flee and are hunted for hides, swarms, music by the scene, a map of the world from above with a fog of war, fast travel and named saves ([the wilderness](docs/levels/wilderness.md)).
- **Space flight** (`starship_level`): a kitbashed fighter in a 5 km combat area round a station, and a standalone Windows package of it.
- **Input:** keyboard and mouse everywhere, an Xbox controller in most played levels ([docs/controls.md](docs/controls.md)); a console of the game's own in the Shipping game (the `` ` `` key: its commands and console variables, such as `rd.WildRunSpeed`).
- **Tests:** scripted play-in-editor tests driven from PowerShell that measure what they test and write it out as JSON; the wilderness's ground checked for seams without a game (`RDWildProbe`); a sound self test; a packaged game's own self test in each of its levels and cities.
- **Demo reels:** 1080p Movie Render Queue renders with the HUD, maps and captions drawn over the frames and the game's own sound, and the packaged game recorded by Windows Game Bar ([docs/reels.md](docs/reels.md)).
- **Tooling:** `ue_exec.py`, `build_cpp.ps1` and the packaging scripts, shared builders, a survey of the local Fab library, and galleries of heroes, enemies, vehicles, objects and monsters.

## Levels

Each level's document has its full description and its rebuild notes. [docs/levels.md](docs/levels.md) lists every level with its properties and who can play it; [docs/controls.md](docs/controls.md) has the controls. "Menu first": Play opens the level's hero menu first.

| Level | Character | What it is | Document |
|---|---|---|---|
| `L_Fig4_Studio` | `fig4`, a MetaHuman conformed to a 3D scan | Photo studio for stills | [character_levels](docs/levels/character_levels.md) |
| `L_Fig4_Meadow` | fig4 | Meadow of procedural Nanite terrain; heel-stance locomotion | [character_levels](docs/levels/character_levels.md) |
| `L_Meshy_Meadow` | Meshy AI biped; the JRPG characters | The same meadow: 18 moves and a sprint; the stage of the JRPG characters | [character_levels](docs/levels/character_levels.md) |
| `soldier_level` | Dystopia Soldier 02 | The same meadow; a Unity-sourced soldier | [character_levels](docs/levels/character_levels.md) |
| `ff_level` | Tripo anime female | The same meadow; a static GLB rigged onto a mannequin skeleton | [character_levels](docs/levels/character_levels.md) |
| `ff2_level` | Animated Tripo anime female | The same meadow; her own clips fixed on the sole contacts | [character_levels](docs/levels/character_levels.md) |
| `castle_level` | FF2 | The Medieval Fantasy Village with walk-in, furnished houses | [castle_level](docs/levels/castle_level.md) |
| `fantasy_castle_level` | FF2 | The Fantasy Castle Environment with the Medieval Lake Village in its lake | [fantasy_castle_level](docs/levels/fantasy_castle_level.md) |
| `sf-city-level` | jrpg-fem5-tripo | A sci-fi city and a megastructure joined by a bridge road; furnished rooms behind blast doors | [sf-city-level](docs/levels/sf-city-level.md) |
| `random_level` | jrpg-fem5-tripo | Procedural medieval town (C++), generated as she nears its edge | [random_level](docs/levels/random_level.md) |
| `random_dungeon_level` | jrpg-fem5-tripo | Procedural dungeon (C++), generated section by section | [random_dungeon_level](docs/levels/random_dungeon_level.md) |
| `random_dungeoncombat_level` | jrpg-fem5-tripo with three melee weapons | The dungeon with fighting, blood, wounds, sound and music | [random_dungeoncombat_level](docs/levels/random_dungeoncombat_level.md) |
| `random_dungeonmagic_level` | girl-caster-tripo | The combat level with a caster and a fire spell | [magic_levels_1-3](docs/levels/magic_levels_1-3.md) |
| `random_dungeonmagic_level2` | girl-darkcaster-tripo | A sword in her right hand, fire from her left | [magic_levels_1-3](docs/levels/magic_levels_1-3.md) |
| `random_dungeonmagic_level3` | the Rogue | Two daggers, a crossbow and a roll | [magic_levels_1-3](docs/levels/magic_levels_1-3.md) |
| `random_dungeonmagic_level4` (menu first) | the Warrior, the Mage, the Warlock or the Rogue | A choice of hero; mana, potions and food, an inventory, a painted interface | [random_dungeonmagic_level4](docs/levels/random_dungeonmagic_level4.md) |
| `random_dungeonmagic_level5` (menu first) | level 4's heroes and the Summoner | The full dungeon game: armour, weapons, five tiers of rooms, loot, crafting, spells, rings, monsters by tier | [random_dungeonmagic_level5](docs/levels/random_dungeonmagic_level5.md) |
| `mistward_castle` (menu first) | level 5's heroes, the Martial Artist and the Summoner | Level 5's game as a castle: themed tiers, shaped and vaulted rooms, traps, shields, prisoners, teleporters, bosses, harvests, shooting monsters, an arena audience, autoplay, the Rogue's stealth, the heroes balanced tier by tier, the final boss Aurorim and his door back to Brokenspire | [mistward_castle](docs/levels/mistward_castle.md) |
| `brokenspire` (menu first) | the castle's six heroes | Mistward Castle's starting town, generated for every new game: trades, townspeople at their work and quests, an hour-long day, gold, the castle building's hall into the dungeon and back; since 2026-11-03 the wilderness round it (300 x 300 km, three more towns, fast travel, a save); since 2026-11-04 a sky with clouds, stars and a moon, weather and wind, hills, animals that flee, a portcullis and its levers, gardens and an oven, named saves; since 2026-11-07 farms of crops in rows, animals to hunt for hides, training dummies, the Warrior's slow block walk, `rd.WildRunSpeed`, the captain's two wilderness quests; since 2026-11-08 the wilderness's sheer walls of earth fixed in its ground's making (measured without a game; not yet walked over in play) | [brokenspire](docs/levels/brokenspire.md), [the wilderness](docs/levels/wilderness.md) |
| `vel_morrath` (from Vel Morrath's cathedral) | the castle's six heroes | The catacombs under the holy city of Vel Morrath (on `brokenspire`, north-east of Brokenspire: its cathedral, monastery, chapels, trades, people and quests): Mistward Castle's game in five tiers, each a floor 4.5 m below the last, joined by stairs; its own tiers, counters and quests | [vel_morrath](docs/levels/vel_morrath.md) |
| `war_engine` (from Ashenreach's foundry) | the castle's six heroes | The War Engine, the besieged factory under the forge city of Ashenreach (on `brokenspire`, in the continent's middle north of Brokenspire at the edge of its burned plain: its Great Foundry, workshops, open forges, trades, the forge-guild's people and quests): Mistward Castle's game in five tiers of foundry brick and dwarven forge halls, gears, chains and ore carts by the walls, eleven kinds of machines and half-machines among the castle's monsters; its own tiers, counters and quests | [ashenreach](docs/levels/ashenreach.md) |
| `sewers` (from Graymourne's Sluice House) | the castle's six heroes | The Sewers of Graymourne, under the fog-bound port on the northern coast (on `brokenspire`: its harbour of five piers with longships and boats moored, wrecks, the drowned dead laid on the quay, gibbets, fishers' racks, warehouses, trades, the harbour's people and quests, its own thick fog): Mistward Castle's game in five tiers going down, each 4.5 m below the last, in damp sewer brick and a vaulted cistern, sludge, rags and the drowned's things by the walls, eleven kinds of drowned sailors and fish-men among the castle's monsters; its own tiers, counters and quests | [graymourne](docs/levels/graymourne.md) |
| `kethrys_spire` (from the black tower's gate) | the castle's six heroes | The Black Tower of Kethrys Spire, inside the tower of the mage city north-west of Graymourne (on `brokenspire`: the tower 69 m high over its gatehouse and hall, sealed for a century, libraries, laboratories, study rooms and meditation chambers, the lights in its upper windows moving, rune circles and crystal pylons, cauldrons, stone houses, the archmage's people and quests): Mistward Castle's game in five tiers of darkened arcane halls lit violet and the castle's halls, crystals, candle stands and rune stones by the walls, five kinds of skeletal mages and witches that shoot among the castle's monsters; its own tiers, counters and quests | [kethrys_spire](docs/levels/kethrys_spire.md) |
| `heaven_fortress` (from the research facility's security door) | the castle's six heroes | Kratos Aurorim Research, the mechanised fortress under Heaven, the modern city south-west of Kethrys Spire (on `brokenspire`: towers up to 101 m, office blocks, shops and apartments of concrete, glass and steel in three facings, a grid of asphalt streets with street lights, benches and bus stops, cars, taxis, police cars and buses driving them, the research facility with its name over its door, the director's people and quests, all under a shimmering shield): Mistward Castle's game in five tiers of steel halls with light strips and machines by the walls, five kinds of troopers, guards, operatives, commanders and a tank that fire rifles and cannons among the castle's monsters; its own tiers, counters and quests | [heaven](docs/levels/heaven.md) |
| `martial_arts` | the Martial Artist | One room of the castle to try her in | [mistward_castle](docs/levels/mistward_castle.md) |
| `random_isometric_village_level` | jrpg-fem5-tripo | Procedural village seen from a fixed isometric camera, with villagers | [random_isometric_village_level](docs/levels/random_isometric_village_level.md) |
| `starship_level` | a space fighter | Space combat round a station, and a standalone Windows package | [starship_level](docs/levels/starship_level.md) |

## Documentation

The README's parts, each in a document of its own:

- [docs/capabilities.md](docs/capabilities.md): everything the project does today, in full: characters, worlds, combat, magic, Mistward Castle, Brokenspire, the wilderness and its cities, space flight, input, tests, reels, tooling
- [docs/levels/character_levels.md](docs/levels/character_levels.md): the photo studio, the meadow levels and the JRPG and Tripo characters (with their rebuild notes)
- [docs/levels/castle_level.md](docs/levels/castle_level.md): the medieval village with walk-in houses, and its rebuild order
- [docs/levels/fantasy_castle_level.md](docs/levels/fantasy_castle_level.md): the castle and its lake village, and its rebuild order
- [docs/levels/sf-city-level.md](docs/levels/sf-city-level.md): the sci-fi city and the megastructure, and its rebuild order
- [docs/levels/random_level.md](docs/levels/random_level.md): the procedural town, and its rebuild order
- [docs/levels/random_dungeon_level.md](docs/levels/random_dungeon_level.md): the procedural dungeon, and its rebuild order
- [docs/levels/random_dungeoncombat_level.md](docs/levels/random_dungeoncombat_level.md): the dungeon fight (weapons, blood, wounds, sound, music), and its rebuild order
- [docs/levels/magic_levels_1-3.md](docs/levels/magic_levels_1-3.md): the caster, the dark caster and the Rogue, and their rebuild orders
- [docs/levels/random_dungeonmagic_level4.md](docs/levels/random_dungeonmagic_level4.md): the choice of hero and the painted interface, and its rebuild order
- [docs/levels/random_dungeonmagic_level5.md](docs/levels/random_dungeonmagic_level5.md): the full dungeon game for players (heroes, spells, rings, monsters, armour, loot, crafting, weapons, tiers: its tables are written from the game's data) and its rebuild order
- [docs/levels/mistward_castle.md](docs/levels/mistward_castle.md): the castle game and its lists of changes, the heroes' balance, the final boss, `martial_arts`, the Shipping game's own console, and its rebuild order
- [docs/levels/wilderness.md](docs/levels/wilderness.md): the wilderness round Brokenspire (the continent, its templates and towns, the chunks round her, the map, fast travel, the save), its test and its rebuild order
- [docs/levels/vel_morrath.md](docs/levels/vel_morrath.md): Vel Morrath, the holy city in the wilds, and its catacombs (the level `vel_morrath`, its floors going down), their test and rebuild order
- [docs/levels/ashenreach.md](docs/levels/ashenreach.md): Ashenreach, the forge city in the wilds, and The War Engine under its foundry (the level `war_engine`, its machines), their test and rebuild order
- [docs/levels/graymourne.md](docs/levels/graymourne.md): Graymourne, the fog-bound port in the wilds, and the sewers under it (the level `sewers`, its harbour, its drowned), their test and rebuild order
- [docs/levels/kethrys_spire.md](docs/levels/kethrys_spire.md): Kethrys Spire, the mage city in the wilds, and the dungeon in its black tower (the level `kethrys_spire`, its arcane halls, its casters), their test and rebuild order
- [docs/levels/heaven.md](docs/levels/heaven.md): Heaven, the modern city in its shield, and the fortress under its research facility (the level `heaven_fortress`, its steel halls, its defenders with firearms), their test and rebuild order
- [docs/secondary.md](docs/secondary.md): the heroes' secondary abilities earned with Angel Tokens (each ability by rank, how the tokens are made from the wilderness's materials), its tests and rebuild order
- [docs/tiers.md](docs/tiers.md): the game's 25 tiers from Brokenspire to Heaven (each dungeon's five in them, the strength by tier, the Mage's spell a tier, the abilities earned after Mistward, the gear's qualities, the monsters along the roads), its tests and rebuild order
- [docs/levels/brokenspire.md](docs/levels/brokenspire.md): the starting town for players (its rules, the services and their prices, the people and the quests: its tables written from its data), its test and its rebuild order
- [docs/levels/random_isometric_village_level.md](docs/levels/random_isometric_village_level.md): the procedural isometric village, and its rebuild order
- [docs/levels/starship_level.md](docs/levels/starship_level.md): the space fighter and its standalone package, and its rebuild order
- [docs/controls.md](docs/controls.md): the keys and gamepad buttons of every level
- [docs/pipeline.md](docs/pipeline.md): requirements, the repository's layout, running the scripts, the stage numbers and what each range builds, links to every rebuild order
- [docs/reels.md](docs/reels.md): how the showcase reels are made (Movie Render Queue, and the packaged game recorded by Game Bar), the Tripo trio and quartet showcases, and the early results' stills

Other documents:

- [TODO.md](TODO.md): what is still to be tested and done, and the known limits (the wilderness and Brokenspire)
- [docs/hero-balance.md](docs/hero-balance.md): the six heroes balanced against each other and against the monsters: the preliminary attempt on Mistward Castle's five tiers, and what a continent-wide one needs
- [docs/levels.md](docs/levels.md): every level, its properties and which characters can play it
- [docs/spec.md](docs/spec.md): `random_dungeonmagic_level5` specified requirement by requirement (configured values, tests, known issues)
- [docs/design.md](docs/design.md): `random_dungeonmagic_level5`'s architecture
- [docs/assets.md](docs/assets.md): every visual and sound asset the project uses, with its author or store listing
- [docs/heroes.md](docs/heroes.md): the hero gallery
- [docs/humanoid_enemies.md](docs/humanoid_enemies.md): the enemy gallery
- [docs/vehicles.md](docs/vehicles.md): the vehicle gallery
- [docs/objects.md](docs/objects.md): the weapons and items gallery
- [docs/monsters.md](docs/monsters.md): the monster gallery
- [docs/dungeon_types.md](docs/dungeon_types.md): with [outdoors.md](docs/outdoors.md), [magic.md](docs/magic.md) and [emotional-content.md](docs/emotional-content.md): what the libraries hold for future work
- [docs/godot-feasibility.md](docs/godot-feasibility.md): what porting Mistward Castle to Godot would take (2026-10-28)

The user's own specs and lists, as they were pasted, with the answers to the questions asked before building them:

- the levels' specs: [brokenspire.txt](docs/brokenspire.txt) (the town), [wilderness.txt](docs/wilderness.txt), [final_boss.txt](docs/final_boss.txt) (Aurorim), [vel_morrath.txt](docs/vel_morrath.txt), [ashenreach.txt](docs/ashenreach.txt), [graymourne.txt](docs/graymourne.txt)
- the lists of changes: [improvements.txt](docs/improvements.txt) (mistward_castle made from level 5), [improvements2.txt](docs/improvements2.txt) (the castle's third list), [improvements3.txt](docs/improvements3.txt) (the list of 2026-10-30: harvests, recipes, scrolls, the Summoner), [improvements4.txt](docs/improvements4.txt) (2026-10-31: allies kept apart, the summons panel, the Options page, the Martial Artist's arm), [improvements5.txt](docs/improvements5.txt) (2026-10-31b: this README split into documents, the arena's audience, autoplay, monsters that shoot, names, ceilings), [improvements6.txt](docs/improvements6.txt) (2026-11-01: the Rogue's stealth, the heroes balanced), [improvements7.txt](docs/improvements7.txt) (2026-11-04: the town and the wilderness), [improvements8.txt](docs/improvements8.txt) (2026-11-07, from the Graymourne build)
- the user's tables: `docs/levelups.xlsx` (weapons, armour, other loot, spells) and `docs/ARPG_Spell_Drop_Table*.xlsx` (the spells' drop table, four versions)

The galleries' pictures and the stills are in `docs/images/`.

## What's not in the repo

[docs/assets.md](docs/assets.md) lists every visual and sound asset the project uses, with its author or store listing.

These are excluded for size (the project's `Content/` is about 450 GB with all the packs, and single files exceed 1 GB) and licensing:

- **Unreal content** (`claude_ue5/Content/`), including third-party packs:
  - Medieval Fantasy Village and Fantasy Castle Environment, both from Fab
  - Monolith megastructure
  - Megascans scans (Saloon Interior pack)
  - the packs named in each level's rebuild notes in [docs/levels/](docs/levels/) (the sci-fi city, the dungeon, town, village and space kits, the creature, villager, weapon and animation packs)
  - MetaHuman assets and the UE template mannequins
- **Source characters:**
  - the Tripo anime female GLBs
  - the Meshy AI biped zip
  - the Dystopia Soldiers pack (Fab, Unity format)
  - the fig4 scan
- **Source art binaries:** FBX, GLB, Alembic, DNA and textures.
- **Sound:** the sound-effect and music library that `random_dungeoncombat_level` plays from, and the files converted from it (`SourceArt/random_dungeon_combat/audio/`). Only `sounds.json`, which names the files, is committed.
- **Renders and showcase videos** (`renders/`).
- **Packaged games** (`builds/`): they hold cooked pack content.
- **Per-machine folders:** `Saved/`, `Intermediate/`, `DerivedDataCache/`.

To rebuild a level you need the same packs locally:
1. Add the Fab packs to the project through the Epic Games Launcher.
2. Put the character sources where the build scripts expect them.
3. Build the C++ module (`pipeline\build_cpp.ps1`).
4. Run the scripts in order ([docs/pipeline.md](docs/pipeline.md) and each level's rebuild notes).
