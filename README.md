# claude-ue5

An Unreal Engine 5.8 project built almost entirely from scripts. The scripts drive the running editor over Python remote execution, Blender + numpy prepare the source art, and a C++ module holds the games that generate themselves in play. The project has twenty levels (and three menu levels): a photo studio and five character showcases, three hand-built worlds with walk-in buildings, three procedural worlds (a town, a dungeon, an isometric village), the dungeon again with melee combat, blood, sound and music, four magic levels built on it (a caster, a dark caster with a sword, a rogue, a choice of four heroes), the full dungeon game with four heroes to choose, the same game as a castle (Mistward Castle: themed tiers, rooms of other shapes, traps, prisoners, shields, teleporters, bosses), and a space fighter. Most have a recorded demo route or a scripted test, and a Movie Render Queue showcase video.

The most complete game, `random_dungeonmagic_level5`, is described for players in [the game now](docs/levels/random_dungeonmagic_level5.md#random_dungeonmagic_level5-the-game-now), specified requirement by requirement in **[docs/spec.md](docs/spec.md)** (with its configured values, its tests and its known issues) and its architecture in **[docs/design.md](docs/design.md)**. Its castle version, `mistward_castle`, is described in [mistward_castle: the castle](docs/levels/mistward_castle.md#mistward_castle-the-castle).

This repository is **source only**: the pipeline scripts, the C++ source, project config and small data files. Unreal assets (`Content/`), source art binaries, sounds, renders and the third-party packs they come from stay local. See [What's not in the repo](#whats-not-in-the-repo).

## Capabilities

What the project does today, in short; [docs/capabilities.md](docs/capabilities.md) has the whole list.

- **Characters and animation:** a MetaHuman conformed to a 3D scan; characters from six kinds of source on the same third-person controls; IK rigs and retargeters built from Python; feet that stay put; clips made in Blender; the dungeon's heroes with armour, weapons, shields and a torch fitted to them; the monster gallery's 55 usable kinds placed by tier.
- **Worlds:** hand-built from pack maps (a meadow, a photo studio, a medieval village, a castle with a lake village, a sci-fi city) and procedural in C++ (a town, a dungeon, an isometric village) generated ahead of her as she walks, with doors and containers that open and maps of what she has discovered; third-person, isometric and chase views.
- **Combat** (`random_dungeoncombat_level`): melee weapons, monsters that notice her, chase, fight and die, blood and wounds, sound placed in the world and music that follows the fight.
- **Magic, the rogue, the choice of hero and a face that moves** (`random_dungeonmagic_level` to `random_dungeonmagic_level5`): a fire spell, then 30 spells from tomes; a rogue with daggers and a crossbow; a menu of heroes; armour, weapons, loot, crafting, rings and five tiers of rooms.
- **Mistward Castle** (`mistward_castle`): level 5's game as a castle with themed tiers, rooms of other shapes, shields, a torch, traps, teleporters, prison cells, bosses, special rooms and slashes, the Martial Artist and the Summoner, harvests and scrolls, monsters that shoot, an arena with an audience, vaulted and domed ceilings, and an autoplay mode that plays any hero for a set time.
- **Space flight** (`starship_level`): a kitbashed fighter in a 5 km combat area round a station, and a standalone Windows package of it.
- **Input:** keyboard and mouse everywhere, an Xbox controller in most played levels ([docs/controls.md](docs/controls.md)).
- **Tests:** scripted play-in-editor tests driven from PowerShell that measure what they test and write it out as JSON; a sound self test; a packaged game's own self test.
- **Demo reels:** 1080p Movie Render Queue renders with the HUD, maps and captions drawn over the frames and the game's own sound ([docs/reels.md](docs/reels.md)).
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
| `mistward_castle` (menu first) | level 5's heroes, the Martial Artist and the Summoner | Level 5's game as a castle: themed tiers, shaped and vaulted rooms, traps, shields, prisoners, teleporters, bosses, harvests, shooting monsters, an arena audience, autoplay | [mistward_castle](docs/levels/mistward_castle.md) |
| `martial_arts` | the Martial Artist | One room of the castle to try her in | [mistward_castle](docs/levels/mistward_castle.md) |
| `random_isometric_village_level` | jrpg-fem5-tripo | Procedural village seen from a fixed isometric camera, with villagers | [random_isometric_village_level](docs/levels/random_isometric_village_level.md) |
| `starship_level` | a space fighter | Space combat round a station, and a standalone Windows package | [starship_level](docs/levels/starship_level.md) |

## Documentation

The README's parts, each in a document of its own:

- [docs/capabilities.md](docs/capabilities.md): everything the project does today, in full: characters, worlds, combat, magic, Mistward Castle, space flight, input, tests, reels, tooling
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
- [docs/levels/mistward_castle.md](docs/levels/mistward_castle.md): the castle game and its lists of changes, `martial_arts`, and its rebuild order
- [docs/levels/random_isometric_village_level.md](docs/levels/random_isometric_village_level.md): the procedural isometric village, and its rebuild order
- [docs/levels/starship_level.md](docs/levels/starship_level.md): the space fighter and its standalone package, and its rebuild order
- [docs/controls.md](docs/controls.md): the keys and gamepad buttons of every level
- [docs/pipeline.md](docs/pipeline.md): requirements, the repository's layout, running the scripts, the stage numbers and what each range builds, links to every rebuild order
- [docs/reels.md](docs/reels.md): how the showcase reels are made, the Tripo trio and quartet showcases, and the early results' stills

Other documents:

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
