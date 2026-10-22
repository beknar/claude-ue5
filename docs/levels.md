# Levels

Every level in the project: what it is, its properties, and which characters can play it. The game modes and pawns were read from the levels' own map files (`claude_ue5/Content/.../*.umap`); the heroes' numbers come from the data the scripts put on the levels (`SourceArt/random_dungeon_magic4/heroes.json`, `SourceArt/random_dungeon_magic5/summoner_hero.json`, `SourceArt/summoner3/armour.json`). README's [Levels](../README.md#levels) table and its Controls list have the full detail of each one. The scripts that build them are in `pipeline/unreal/`, numbered in build order.

There are **19 levels**: 18 to play, and the photo studio for stills. Two of them open with a menu level first, and ten have a `*_Cine` copy for their demo reel (see [Other maps](#other-maps)).

## At a glance

| Level | Kind | Who plays it | Game mode | Scripted test | Demo reel (`renders/`) |
|---|---|---|---|---|---|
| `L_Fig4_Studio` | photo studio (stills) | fig4, posed | none of its own (the project default, `BP_Fig4GameMode`) | - | - (stills) |
| `L_Fig4_Meadow` | meadow showcase | fig4 | `BP_Fig4GameMode` | - | `Fig4_Locomotion_Meadow.mp4` |
| `L_Meshy_Meadow` | meadow showcase | the JRPG character built last (now Fem5, the Warrior); the Meshy biped | `BP_JRPGFem5GameMode` (now) | - | `Meshy_Biped_Showcase`, `JRPG_Fem5_Meadow_Showcase` |
| `soldier_level` | meadow showcase | Dystopia Soldier 02 | `BP_SoldierGameMode` | - | `Dystopia_Soldier_Showcase` |
| `ff_level` | meadow showcase | FF | `BP_FFGameMode` | - | `FF_Anime_Showcase` |
| `ff2_level` | meadow showcase | FF2 | `BP_FF2GameMode` | - | `FF2_Anime_Showcase` |
| `castle_level` | hand-built world | FF2 | `BP_FF2GameMode` | - | `Castle_Furnished_Showcase`, `Castle_Interiors_Splash_Showcase` |
| `fantasy_castle_level` | hand-built world | FF2 | `BP_FF2GameMode` | - | - |
| `sf-city-level` | hand-built world | jrpg-fem5-tripo (the Warrior's model) | `BP_SFC_GameMode` | `709` / `710` walk test | `SFCity_Fem5_Showcase` |
| `random_level` | procedural town | jrpg-fem5-tripo | `BP_RL_GameMode` | `761` walk test | `RandomLevel_Fem5_Showcase` |
| `random_dungeon_level` | procedural dungeon | jrpg-fem5-tripo | `BP_RD_GameMode` | `771` / `772` walk test | `RandomDungeon_Fem5_Showcase` |
| `random_isometric_village_level` | procedural village, isometric | jrpg-fem5-tripo | `BP_IV_GameMode` | `781` / `782` walk test | `RandomIsoVillage_Fem5_Showcase` |
| `random_dungeoncombat_level` | dungeon game: melee | jrpg-fem5-tripo with sword, spear, axe | `BP_RD_GameMode` | `792` / `793` combat test | `RandomDungeonCombat_Fem5_Showcase`, `_Blood_Sound_`, `_Music_` |
| `random_dungeonmagic_level` | dungeon game: a spell | the Mage | `BP_RDM_GameMode` | `812` / `813` magic test | `RandomDungeonMagic_Caster_Showcase` |
| `random_dungeonmagic_level2` | dungeon game: sword and spell | the Warlock | `BP_RDM2_GameMode` | `813` | `RandomDungeonMagic2_DarkCaster_Showcase` |
| `random_dungeonmagic_level3` | dungeon game: daggers and crossbow | the Rogue | `BP_RDM3_GameMode` | `813` | `RandomDungeonMagic3_Rogue_Showcase` |
| `random_dungeonmagic_level4` | dungeon game: choice of hero, items | Warrior, Mage, Warlock, Rogue (menu) | `BP_RDM4_GameMode` | `827` / `828` hero test | `RandomDungeonMagic4_Heroes_`, `_UI_`, `_Lettering_Showcase` |
| `random_dungeonmagic_level5` | dungeon game: five heroes, armour | Warrior, Mage, Warlock, Rogue, Summoner (menu; Summoner by default) | `BP_RDM4_GameMode` | `853` (through `828 -lv 5`) | `RandomDungeonMagic5_Summoner_Armour_`, `_Faces_`, `_MetaHuman_Faces_Showcase` |
| `starship_level` | space flight | a space fighter | `SSGameMode` | `802` / `803` flight test | `Starship_Fighter_Showcase` |

The editor starts on `L_Fig4_Meadow`, and a packaged game would too (`GameDefaultMap` in `Config/DefaultEngine.ini`). Each `*_Showcase` reel is also in a `_20MB` copy; `Fig4_Locomotion_Meadow.mp4`, the oldest, is not.

## Showcases: the studio and the meadow

The meadow is one map (procedural Nanite terrain, rocks and grass) copied for each character, who walks and runs on it with third-person controls (WASD, mouse, Space jump, Shift run).

### `L_Fig4_Studio`
A photo-studio cyclorama with a plinth, studio lighting and MegaLights, where fig4 is shown for stills.
- **Character:** `fig4`, a MetaHuman conformed to a 3D scan, with a strand hair groom and the scanned outfit refitted to her.
- **Properties:** not a game level: no game mode of its own, no reel, stills only (scripts `01`-`25`).

### `L_Fig4_Meadow`
The meadow with fig4 walking in heels.
- **Character:** fig4 (`BP_Fig4Character`), with heel-stance locomotion retargeted from the UE mannequin.
- **Properties:** game mode `BP_Fig4GameMode`; the project's startup map; scripts `31`-`95` (`50`, `51_level_outdoor.py` build the meadow).

### `L_Meshy_Meadow`
The meadow as a stage for the Meshy biped and the JRPG characters.
- **Characters:** the Meshy AI biped (`BP_MeshyCharacter`: 18 moves on input actions plus a sprint on Ctrl), and the JRPG characters (`BP_JRPGFem1Character` … `BP_JRPGFem5Character`, `BP_JRPGCasterCharacter`, `BP_JRPGDarkCasterCharacter`, `BP_JRPGRogueCharacter`, `BP_JRPGSummonerCharacter`, `BP_JRPGSummoner3Character`). Each character's script sets the meadow's game mode to its own, so the one built last plays: now Fem5 (`BP_JRPGFem5GameMode`), the Warrior's model.
- **Properties:** scripts `100`-`154` (Meshy), `500`-`540` and `600`-`650` (JRPG characters).

### `soldier_level`, `ff_level`, `ff2_level`
The meadow with one character each.
- `soldier_level`: Dystopia Soldier 02 (`BP_SoldierCharacter`), converted from a Unity-format Fab pack, with retargeted locomotion (`160`-`189`).
- `ff_level`: FF, a static Tripo GLB rigged onto a UE4-mannequin skeleton (`BP_FFCharacter`, `200`-`230`).
- `ff2_level`: FF2, an animated Tripo GLB playing her own clips, grounded on the sole contacts so she doesn't float or slide (`BP_FF2Character`, `240`-`289`). Extra moves: jump, boxing, casting (`260`'s inputs).

## Hand-built worlds

### `castle_level`
The Medieval Fantasy Village pack's map with walk-in houses.
- **Character:** FF2 (`BP_FF2GameMode`).
- **Properties:** doors, chests, trunks, wardrobes and barrels open with **F**; interiors furnished by the building's purpose (tavern, manor, homes, bakery, stable, barn, storehouse, smithy) with lofts, attics and lights; water splashes in the river. Scripts `290`-`383`.

### `fantasy_castle_level`
The Fantasy Castle Environment with the Medieval Lake Village streamed into its lake (the sublevel `fcl_lake_village`).
- **Character:** FF2 (`BP_FF2GameMode`; her step and walkable slope raised for the pack's rock).
- **Properties:** the pack meshes collide with their own triangles, so doorways, arches and the bridge can be walked; a stair from the castle's terrace to the island bridge and a road over a causeway into the walled village; three castle buildings opened up and furnished (great hall, armory, barracks) and the village's houses furnished by purpose; doors and chests open with **F**. No reel. Scripts `400`-`421`.

### `sf-city-level`
The Open World Science Fiction City joined by a 200 m bridge road to the Monolith Megastructure (the sublevel `sfc_monolith`).
- **Character:** jrpg-fem5-tripo (`BP_SFC_Fem5Character`: her own idle, walk and run, foot IK).
- **Properties:** four structures with furnished rooms behind automatic sci-fi doors (Port Authority, a noodle bar, a hab apartment, an excavation lab); invisible barrier walls along every drop and a fall guard. Scripts `700`-`714`.

## Procedural worlds

All three are built by C++ generators. A start area is built from a fixed seed and saved. Walking toward its edge generates the next area ahead of her (a new seed each play, never saved), with a reveal effect: a glowing border and a scan wave.

### `random_level`
A medieval town (`ARTTownGenerator`).
- **Character:** jrpg-fem5-tripo (`BP_SFC_Fem5Character`).
- **Properties:**
  - Size: a 500 m x 500 m start square, then 250 m cells generated in play.
  - Buildings: the Modular Medieval Town packs' furnished docks houses, tavern and stores, and Sherwood cabins, streamed in as level instances and turned to face the street.
  - Doors open as she nears them; chests, wardrobes and crates open with **F**.
  - Scripts `750`-`761`.

### `random_dungeon_level`
A dungeon (`ARDDungeonGenerator`), without fighting.
- **Character:** jrpg-fem5-tripo (`BP_SFC_Fem5Character`).
- **Properties:**
  - Size: a 252 m x 252 m start section of 49 rooms, then sections generated in play.
  - Rooms by purpose, furnished and lit for it: great hall, barracks, prison cells, torture chamber, storeroom, armory, kitchen, library, chapel, crypt, treasury, guard room, forge. Hallways are guard passages, supply passages or catacombs.
  - Every door and container opens with **F**.
  - Tactical maps: a minimap, and **M** for a see-through big map that she keeps playing under. Markers: monsters, elites, unlooted chests, unexplored exits.
  - Monsters from Creatures_Pack (troll, daemon, horned demon, ripper dog, spider, mutant) in 40 % of the rooms, wandering from room to room.
  - Scripts `770`-`775`.

### `random_isometric_village_level`
A nucleated village seen from a fixed isometric camera (`AIVVillageGenerator`).
- **Character:** jrpg-fem5-tripo (`BP_SFC_Fem5Character`).
- **Properties:**
  - Layout: a market square with the church, tavern, smithy, bakery, store and elder's hall, ring streets, lanes and three main roads. Houses are built from the House Forge kit and furnished by purpose, with gardens, orchards and farmsteads beyond.
  - Size: a 250 m x 250 m start section, then 250 m sections generated in play.
  - Indoors the roof and the camera-side walls are cut away, and her silhouette shows through whatever hides her.
  - Unarmed villagers (three per ten buildings) walk the streets and give way.
  - Camera: **Q** / **E** turn the view in 45° steps and the wheel zooms.
  - Maps: a minimap, and **M** for a labelled big map. Doors and containers open with **F**.
  - Xbox controller supported.
  - Scripts `780`-`787`.

## The dungeon games

Six levels of one game, each a Save As copy of the one before:
`random_dungeon_level` → `random_dungeoncombat_level` → `random_dungeonmagic_level` → `_level2` → `_level3` → `_level4` → `_level5`

All of them share the dungeon above: generated sections, rooms by purpose, doors and containers, and the tactical maps. They also share the C++ (`ARDDungeonGenerator`, `URDCombatComponent`) and its sound and music.

**What every dungeon game has:**
- **Monsters:** they notice her, chase her, attack, flinch and die. In the start section a monster is weaker than she is; in sections generated in play it is a match for her (tiers).
- **Blood and wounds:** bursts and spray where a blow lands, marks where drops fall, a pool under a body, and a wound on that one monster's skin.
- **Sound:** placed in the world and fading with distance.
- **Music:** a wandering track over a room tone, and a battle track (a new one each fight) while a monster is after her.
- **Death:** at 0 hit points she falls and stands up again in the middle of the start section.

### `random_dungeoncombat_level`
The dungeon with melee fighting (`bCombat`).
- **Character:** jrpg-fem5-tripo (`BP_SFC_Fem5Character`, `BP_RD_GameMode`).
- **Weapons:** from the Medieval_Weapons pack, each with attack, flinch and death clips from a Fab animation pack, retargeted to her:

  | Weapon | Damage a blow | Note |
  |---|---|---|
  | Sword and shield | 22 | |
  | Spear and shield | 17 | long reach |
  | Axe | 36 | slower, wide arc |

- **Properties:**
  - 100 hit points, which come back out of a fight.
  - Monsters in 30 % of the rooms. In the start section they average 50 hit points and 11 damage a blow; in generated sections, 100 and 25.
  - HUD: a status panel, a bar over each monster in the fight, damage numbers.
  - Maps: miniature maps of the dungeon, with every room named on the **M** map.
- **Controls:** left mouse (X or RT) attacks, 1 / 2 / 3 (the D-pad) choose the weapon.
- **Scripts:** `790`-`799`.

### `random_dungeonmagic_level`
The dungeon with a caster.
- **Character:** the Mage (girl-caster-tripo, `ai models/Mage.glb`; `BP_RDM_CasterCharacter`): her own walk and run, and an idle and three casts made for her in Blender.
- **Weapon:** a fire spell. It reaches 14 m and follows the monster she turned to at 17 m/s. It does 25 damage, and half of that to every other monster within 1.7 m.
- **Properties:** the caster controls:
  - Keyboard: R switches walking and running; left mouse or E casts.
  - Xbox controller: LT switches walking and running, RB or LB casts, X opens, Back opens the map.
  - The HUD shows the controls of the device used last.
- **Scripts:** `810`-`816`.

### `random_dungeonmagic_level2`
The dungeon with a dark caster who fights with sword and spell.
- **Character:** the Warlock (girl-darkcaster-tripo, `ai models/Warlock.glb`; `BP_RDM2_DarkCasterCharacter`): three sword cuts and two left-hand casts made for her. Her hair swings on six simulated bone chains.
- **Weapons:** the sword in her right hand (22 damage) and the fire spell from her left, which she casts without putting the sword away.
- **Controls:** left mouse (RB) cuts; right mouse or E (LB) casts.
- **Scripts:** `817`-`820`.

### `random_dungeonmagic_level3`
The dungeon with a rogue.
- **Character:** the Rogue (`ai models/Rogue.glb`, `BP_RDM3_RogueCharacter`): three dagger strikes, a crossbow shot and a roll made for her.
- **Weapons:**

  | Weapon | Damage | Reach | Note |
  |---|---|---|---|
  | Two daggers | 15 a strike | 1.5 m | |
  | Crossbow | 34 | 26 m | the bolt flies straight at 45 m/s and sticks where it misses |

  The weapon not in her hands is carried on her: the crossbow on her back, the daggers on her thighs.
- **Properties:** B rolls her 4.2 m, and blows miss her through most of the roll.
- **Controls:** 1 / 2 or the wheel (Y) switch weapons; left mouse (RB) strikes or shoots.
- **Scripts:** `822`, `823`.

### `random_dungeonmagic_level4`
The dungeon with a choice of hero, mana, items and an inventory.
- **Menu first:** played without a hero chosen (as from the editor's Play), it opens `random_dungeonmagic_level4_select`. In the menu the hero turns on a turntable beside her card, and START opens the dungeon with her (`?Hero=<name>`). `rd.HeroMenu 0` skips the menu.
- **Characters:** four heroes. Each brings her own weapons and controls from the level she comes from.

  | Hero | Blueprint | Model | Hit points | Mana (back a second) | Bonus | Starts with | Armour on her card |
  |---|---|---|---|---|---|---|---|
  | Warrior (the default) | `BP_RDM4_WarriorCharacter` | `Warrior.glb` | 140 | - | +30 % melee | sword and shield (22 → 28.6 a blow) | all armour |
  | Mage | `BP_RDM_CasterCharacter` | `Mage.glb` | 70 | 100 (2.0) | - | fire (25 damage, 8 mana), dark fire (38, 14 mana) | none |
  | Warlock | `BP_RDM2_DarkCasterCharacter` | `Warlock.glb` | 100 | 60 (1.2) | - | sword (22), fire (25, 10 mana) | leather only |
  | Rogue | `BP_RDM3_RogueCharacter` | `Rogue.glb` | 100 | - | +30 % ranged | daggers (15), crossbow (34 → 44.2) | leather only |

- **Properties:**
  - Monsters are the same for every hero: scaled for a 100 hit point hero with a 25-point blow (`monster_reference`).
  - Hit points do not come back by themselves.
  - A cast with too little mana is refused.
  - Items: every container of the start section holds one of 33 potions and foods (healing, mana, speed, food over 10 s), as rare as the item table says (`items.json`).
  - Inventory: I, Tab or Start. It pauses the game; she wields weapons and uses items from it.
  - Painted interface and big map. Lettering: Cinzel, Alegreya and Alegreya SC.
  - There are no armour items in this level: armour is on the cards only.
- **Scripts:** `824`-`831`.

### `random_dungeonmagic_level5`
Level 4's game with a fifth hero, the Summoner, and armour to find and wear.
- **Menu first:** as level 4, through `random_dungeonmagic_level5_select` with five heroes.
- **Characters:** level 4's four heroes, with the same numbers, and the Summoner, who is the default.

  | Hero | Blueprint | Model | Hit points | Mana (back a second) | Starts with | Can wear the armour found here |
  |---|---|---|---|---|---|---|
  | Summoner (the default) | `BP_RDM5_Summoner3Character` | `Summoner3.glb`: her own walk and run, the Mage's casts, flinch and death retargeted onto her | 85 | 90 (1.6) | fire and dark fire, as the Mage; no armour | yes, all five sets |
  | Warrior, Mage, Warlock, Rogue | as level 4 | as level 4 | as level 4 | as level 4 | as level 4 | no ("not made for" her: the sets were fitted to the Summoner only) |

- **Armour:** five sets in the great hall's containers, each refitted to the Summoner bone by bone. Enter in the inventory (A on a controller) puts a set on or takes it off. One set is worn at a time, and the set takes its share off every blow on her:

  | Set | From the pack | Share of a blow taken off |
  |---|---|---|
  | Plate Armour | Knights (Pack) | 40 % |
  | Bear Warrior's Armour | Animals Warrior Pack | 30 % |
  | Orc Veteran's Armour | 14 Orcs Pack | 30 % |
  | Demonic Armour | Fantasy Warriors (Pack) | 25 % |
  | Tiefling's Armour | Fantasy Warriors (Pack) | 15 % |

- **Properties:**
  - 38 items: the 33 potions and foods and the five sets.
  - A container holds up to six things; the inventory scrolls.
- **Her face:** the Summoner had a face that showed what happened to her. It was first painted and then a MetaHuman face, with expressions on being hurt, casting, finding something, a monster after her, low hit points and death (`URDFaceComponent`, scripts `832`-`841`).
- **Earlier versions:** before the Summoner3 rebuild, the level was played by:
  - the first Summoner (`BP_RDM5_SummonerCharacter`, `Summoner.glb`, game mode `BP_RDM5_GameMode`);
  - then Summoner2 (`BP_RDM5_Summoner2Character`, a whole MetaHuman fitted to `Summoner2.glb`, game mode `BP_RDM5S2_GameMode`, scripts `842`-`848`).

  Their characters and game modes are still in the project, but the level no longer uses them.
- **Scripts:** `849`-`853`.

## Space

### `starship_level`
A space fighter in a 5 km x 5 km x 5 km combat area round a space station.
- **Character:** a fighter (C++ `ASSFighter`) kitbashed from pack meshes in the style of a Colonial Viper. It possesses itself: `SSGameMode` has no default pawn.
- **Weapons:** cannons and homing missiles with lock-on.
- **Properties:**
  - Targets: destructible asteroids (big ones break up), cargo containers and target drones in waves.
  - Collisions damage the hull; at 0 the fighter is launched again. It is turned back at the edge of the area.
  - A gate course of six ring tunnels.
  - Engine flames and contrails; a chase camera; a full HUD.
  - A standalone Windows package (`package_starship.ps1`).
- **Controls:**
  - Keyboard and mouse: W / S throttle, A / D roll, the mouse points the nose; left button or Space fires the cannons, right button or Ctrl fires a missile, Shift is the afterburner.
  - An Xbox controller is supported.
- **Scripts:** `800`-`806`.

## Characters and where they play

| Character | Model | Blueprint(s) | Levels |
|---|---|---|---|
| fig4 | a MetaHuman conformed to a 3D scan | `BP_Fig4Character` | `L_Fig4_Studio`, `L_Fig4_Meadow` |
| Meshy biped | Meshy AI | `BP_MeshyCharacter` | `L_Meshy_Meadow` |
| Dystopia Soldier 02 | Fab pack (Unity format) | `BP_SoldierCharacter` | `soldier_level` |
| FF | Tripo, static | `BP_FFCharacter` | `ff_level` |
| FF2 | Tripo, animated | `BP_FF2Character` | `ff2_level`, `castle_level`, `fantasy_castle_level` |
| JRPG Fem1, Fem3, Fem4 | Meshy | `BP_JRPGFem1Character` … `Fem4` | `L_Meshy_Meadow` (when its game mode is theirs) |
| Warrior (jrpg-fem5-tripo) | `ai models/Warrior.glb` | `BP_JRPGFem5Character`, `BP_SFC_Fem5Character`, `BP_RDM4_WarriorCharacter` | `L_Meshy_Meadow`, `sf-city-level`, `random_level`, `random_dungeon_level`, `random_isometric_village_level`, `random_dungeoncombat_level`, `random_dungeonmagic_level4`, `random_dungeonmagic_level5` |
| Mage (girl-caster-tripo) | `ai models/Mage.glb` | `BP_JRPGCasterCharacter`, `BP_RDM_CasterCharacter` | `L_Meshy_Meadow`, `random_dungeonmagic_level`, `random_dungeonmagic_level4`, `random_dungeonmagic_level5` |
| Warlock (girl-darkcaster-tripo) | `ai models/Warlock.glb` | `BP_JRPGDarkCasterCharacter`, `BP_RDM2_DarkCasterCharacter` | `L_Meshy_Meadow`, `random_dungeonmagic_level2`, `random_dungeonmagic_level4`, `random_dungeonmagic_level5` |
| Rogue | `ai models/Rogue.glb` | `BP_JRPGRogueCharacter`, `BP_RDM3_RogueCharacter` | `L_Meshy_Meadow`, `random_dungeonmagic_level3`, `random_dungeonmagic_level4`, `random_dungeonmagic_level5` |
| Summoner (Summoner3) | `ai models/Summoner3.glb` | `BP_JRPGSummoner3Character`, `BP_RDM5_Summoner3Character` | `L_Meshy_Meadow`, `random_dungeonmagic_level5` |
| Summoner (the first) | `ai models/Summoner.glb` | `BP_JRPGSummonerCharacter`, `BP_RDM5_SummonerCharacter` | `L_Meshy_Meadow`; formerly `random_dungeonmagic_level5` |
| Summoner2 | `ai models/Summoner2.glb`, as a MetaHuman | `BP_JRPGSummoner2Character`, `BP_RDM5_Summoner2Character` | formerly `random_dungeonmagic_level5` |
| Space fighter | pack meshes, kitbashed | `ASSFighter` (C++) | `starship_level` |

"`L_Meshy_Meadow`" means a character has a game mode for the meadow (`BP_JRPG<name>GameMode`); the meadow plays whichever one it was last set to.

## Other maps

These are in the project's own folders but are not levels to play on their own.

| Map | What it is |
|---|---|
| `random_dungeonmagic_level4_select`, `random_dungeonmagic_level5_select` | the hero menus of levels 4 and 5 (`RDHeroSelectGameMode`): they open the dungeon with the hero chosen |
| `L_Fig4_Meadow_Cine`, `L_Meshy_Meadow_Cine`, `soldier_level_Cine`, `ff_level_Cine`, `ff2_level_Cine`, `castle_level_Cine`, `sf-city-level_Cine`, `random_level_Cine`, `random_dungeon_level_Cine`, `random_isometric_village_level_Cine` | copies for the demo reels (`MoviePipelineGameMode`): an AI demo character runs a recorded route on the sequence clock. The dungeon games and the fighter have no copy: their reels are rendered on the level itself, with a pilot script playing the game |
| `fcl_lake_village`, `sfc_monolith` | sublevels streamed into `fantasy_castle_level` and `sf-city-level` |
| `L_Tripo_Trio_Showcase`, `L_Tripo_Quartet_Showcase` | stages of the trio and quartet reels (`TripoTrio_Showcase`, `TripoQuartet_Showcase`: the Warrior, Mage, Warlock and then the Rogue on plinths) |
| `L_RDM5_FaceStudio` | the stage of the Summoner's two face reels |
| `rl_scratch` | the scratch level the galleries are staged in (`900`-`904`) |
| `rl_perf` | an empty test level beside it; no script names it |

The Fab packs in `Content/` bring 743 maps of their own (611 without their level-instance and foliage sublevels) in 203 pack folders: demo, overview and showcase maps. They are not part of this project's game; [assets.md](assets.md) lists the packs.
