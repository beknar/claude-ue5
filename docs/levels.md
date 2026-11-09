# Levels

Every level in the project: what it is, its properties, and which characters can play it. The game modes and pawns were read from the levels' own map files (`claude_ue5/Content/.../*.umap`); the heroes' numbers come from the data the scripts put on the levels (`SourceArt/random_dungeon_magic4/heroes.json`, `SourceArt/random_dungeon_magic5/summoner_hero.json`, `SourceArt/summoner3/armour.json`; in Mistward Castle and the levels copied from it, `SourceArt/mistward/balance6.json`). Each level's document under [levels/](levels/) (linked from README's [Levels](../README.md#levels) table) and [controls.md](controls.md) have the full detail of each one. The scripts that build them are in `pipeline/unreal/`, numbered in build order.

There are **25 levels**: 24 to play, and the photo studio for stills. Four of them open with a menu level first (levels 4 and 5, Mistward Castle and Brokenspire), three are entered from the wilderness's cities (`vel_morrath`, `war_engine`, `sewers`), and ten have a `*_Cine` copy for their demo reel (see [Other maps](#other-maps)). The current game, packaged by `package_mistward.ps1`, is five of them and the hero menu: `brokenspire`, `mistward_castle`, `vel_morrath`, `war_engine` and `sewers` ([Mistward Castle's game](#mistward-castles-game)).

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
| `random_dungeonmagic_level5` | dungeon game: five heroes, armour, a weapons table, five tiers of rooms | Warrior, Mage, Warlock, Rogue, Summoner (menu; Summoner by default) | `BP_RDM4_GameMode` | `853` (through `828 -lv 5`) | `RandomDungeonMagic5_Summoner_Armour_`, `_Faces_`, `_MetaHuman_Faces_Showcase` |
| `mistward_castle` | level 5's game as a castle: themed tiers, rooms of other shapes, traps, prisoners, shields, a torch, teleporters, bosses, special rooms, harvests and scrolls, shooting monsters, autoplay, the heroes balanced tier by tier, the final boss Aurorim | Warrior (Warrior3), Mage, Warlock, Rogue, Martial Artist, Summoner (Summoner4) (menu `mistward_castle_select`) | `BP_RDM4_GameMode` | `868` (`868_mistward_test.ps1`) | `MistwardCastle_Heroes_`, `_Heroes2_` to `_Heroes5_Showcase`; `MistwardCastle_Aurorim_`, `_Aurorim2_..._Showcase` (Game Bar, `renders/gamebar renders/`) |
| `martial_arts` | one room of the castle to try the Martial Artist in | the Martial Artist | `BP_RDM4_GameMode` | `868 martialroom -lv martial_arts` | - |
| `brokenspire` | the castle's starting town, generated for every new game: trades, townspeople at their work and quests, an hour-long day, gold, the castle's hall into the dungeon; the wilderness round it (300 x 300 km, three more cities, a sky and weather, wild animals, farms, fast travel, a save) | the castle's six heroes (the hero menu `mistward_castle_select` opens it) | `BP_RDM4_GameMode` | `884` (`884_brokenspire_test.ps1`), `888` (`888_wilderness_test.ps1`) | `Brokenspire_`, `Brokenspire2_` to `Brokenspire4_..._Showcase`, `Brokenspire7_2026-11-05_Showcase` (Game Bar, `renders/gamebar renders/`) |
| `vel_morrath` | the catacombs under Vel Morrath's cathedral: the castle's game in five tiers going down | the castle's six heroes (down the cathedral's stair) | `BP_RDM4_GameMode` | `884 holy,descend`, `868 catacombs -lv vel_morrath` | - |
| `war_engine` | The War Engine under Ashenreach's Great Foundry: the castle's game in foundry brick, with its machines | the castle's six heroes (through the foundry's iron gate) | `BP_RDM4_GameMode` | `884 forge,descendwar` | - |
| `sewers` | the sewers under Graymourne: the castle's game in five tiers going down, damp brick, with its drowned | the castle's six heroes (through the Sluice House's sewer gate) | `BP_RDM4_GameMode` | `884 port,descendsewer` | - |
| `starship_level` | space flight | a space fighter | `SSGameMode` | `802` / `803` flight test | `Starship_Fighter_Showcase` |

The editor starts on `L_Fig4_Meadow` (`GameDefaultMap` in `Config/DefaultEngine.ini`); `package_mistward.ps1` and `package_starship.ps1` set it to the hero menu and to `starship_level` for their cook only, so their games start there. Each `*_Showcase` reel is also in a `_20MB` copy but three: `Fig4_Locomotion_Meadow.mp4`, the oldest, and `MistwardCastle_Heroes4_` and `_Heroes5_Showcase` (full size only, the user's choice).

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
- **Characters:** the Meshy AI biped (`BP_MeshyCharacter`: 18 moves on input actions plus a sprint on Ctrl), and the JRPG characters (`BP_JRPGFem1Character` … `BP_JRPGFem5Character`, `BP_JRPGCasterCharacter`, `BP_JRPGDarkCasterCharacter`, `BP_JRPGRogueCharacter`, `BP_JRPGSummonerCharacter`, `BP_JRPGSummoner3Character`, `BP_JRPGSummoner4Character`, `BP_JRPGWarrior3Character`, `BP_JRPGMartialArtistCharacter`). Each character's script sets the meadow's game mode to its own, so the one built last plays: now Fem5 (`BP_JRPGFem5GameMode`), the Warrior's model.
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

and on from level 5, [Mistward Castle's game](#mistward-castles-game): `_level5` → `mistward_castle` → `martial_arts`, `brokenspire`, `vel_morrath`, `war_engine`, `sewers` (each a Save As copy of the castle).

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
- **Characters:** level 4's four heroes, with the same numbers (the Warrior's model Warrior3 since `862`: `BP_RDM5_Warrior3Character`, `ai models/Warrior3.glb`), and the Summoner, who is the default.

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

- **Tiers of rooms:** each 252 m section is a set of rooms, and its tier is its ring around the start plus one:

  | Tier | Sets of rooms | Opens when |
  |---|---|---|
  | 1 | 1 (the start) | at the start |
  | 2 | 8 around it | at the start, as she walks to them |
  | 3 | 16 around those | all 8 sets of tier 2 are cleared |
  | 4 | 24 | all 16 sets of tier 3 are cleared |
  | 5 | 32 | all 24 sets of tier 4 are cleared; nothing is made beyond tier 5 |

  A set is cleared when every room in it has been entered, every chest and trunk opened and every monster in it killed. Monsters she killed stay dead when a set is dropped and generated again. A hallway into a tier that isn't open is barred by a grating, and the hallways out of tier 5 are walled. The maps mark these with a red cross. A panel under the minimap shows her tier, its sets cleared, and the rooms, chests and monsters left in her set.
- **Weapons table:** 29 weapons in the containers of their tiers, each with a speed and a damage rating (1 to 10), a durability and a rarity (`SourceArt/random_dungeon_magic5/weapons_table.json`):

  | Type | Weapons (tiers) |
  |---|---|
  | Short sword | Viking Shortsword (1), Sherwood Sword (1), Orc Cleaver (2), Toothed Bone Sword (2) |
  | One-handed sword | Arming Sword (1), Longsword (1), Viking Sword (1), Veteran's Sword (2), Templar Sword (2) |
  | Two-handed sword | Plate Knight's Sword (1), Paladin's Sword (2), Dark Knight's Sword (3), Ursag's Horn Blade (4, 5) |
  | Curved and eastern sword | Eastern Sabre (1), Katana (2), Wakizashi (3) |
  | Short blades | Dagger (1), Leaf-Blade Knife (1), Obsidian Knife (2), Bone Blade (2), Combat Knife (3), Survival Knife (3), Kukri (4), Sniper's Knife (4), Wrist Blade (5) |
  | Ranged | Longbow (1), Viking Bow (2), Crossbow (3), Dwarf Crossbow (4, 5) |

  - **Damage:** 8 + 3 × the damage rating, from 11 (rating 1) to 38 (rating 10), with the hero's bonus on top.
  - **Speed:** one attack every 1.6 − (speed − 1) × 1.05 / 9 seconds, from 1.6 s (rating 1) to 0.55 s (rating 10).
  - **Durability:** each attack that hits a monster takes 1 off. At 0 the weapon breaks and she draws the next one. The weapons she starts with never break.
  - **Rarity:** 33 for every weapon, used as its weight among the items a container may hold.
- **Who wields what:** as the hero cards say:

  | Hero | Can wield |
  |---|---|
  | Warrior, Warlock | all 29 |
  | Rogue | short blades and ranged weapons (13) |
  | Mage, Summoner | none: they carry what they find but can't wield it |

  - **One-handed weapons:** the hero's own animations: the Warrior's sword and shield, the Warlock's sword cuts, the Rogue's dagger strikes (a found blade in both hands).
  - **Two-handed swords:** three new cuts with both hands on the hilt.
  - **Bows:** a new shot, with the bow in the left hand.
  - **Crossbows:** the Rogue's shot (made for the Warrior and the Warlock too).
  - **Where the hand goes:** each weapon is held where its handle was measured on its model.
- **Properties:**
  - 67 items: the 33 potions and foods, the five sets of armour and the 29 weapons. The containers of every tier hold items, not only the start's.
  - A container holds up to six things; the inventory scrolls.
- **Her face:** the Summoner had a face that showed what happened to her. It was first painted and then a MetaHuman face, with expressions on being hurt, casting, finding something, a monster after her, low hit points and death (`URDFaceComponent`, scripts `832`-`841`).
- **Earlier versions:** before the Summoner3 rebuild, the level was played by:
  - the first Summoner (`BP_RDM5_SummonerCharacter`, `Summoner.glb`, game mode `BP_RDM5_GameMode`);
  - then Summoner2 (`BP_RDM5_Summoner2Character`, a whole MetaHuman fitted to `Summoner2.glb`, game mode `BP_RDM5S2_GameMode`, scripts `842`-`848`).

  Their characters and game modes are still in the project, but the level no longer uses them.
- **Scripts:** `849`-`853`; the weapons and the tiers `854`, `855` (with `blender_numpy/weapon5_clips.py`); armour by weight, the armour and loot tables, crafting, spells, rings, monsters by tier `856`-`859`; the heroes' arms `860`; Warrior3 `862`; the castle's third list, which is on level 5 too, `870`.

## Mistward Castle's game

Level 5's game rebuilt as a castle, with a town to start in, a continent round the town and three more cities, each over a dungeon of its own. Played from the hero menu `mistward_castle_select` ("Mistward Castle" over CHOOSE YOUR HERO), whose START opens Brokenspire; Brokenspire's Mistgate opens the castle, and each city's gate its dungeon. What she carries, her gold, her storage, her quests and her whole state go with her between them. Every one plays `BP_RDM4_GameMode` with the castle's six heroes; the cities' three dungeons share the castle's heroes, balance, loot, traps, special rooms and bosses, and keep their own tiers, loot and counters under their own keys, apart from the castle's. This is the game `package_mistward.ps1` packages as a Shipping game (all but `martial_arts`), with a console of its own.

| Hero | Blueprint | Model |
|---|---|---|
| Warrior | `BP_RDM5_Warrior3Character` | `ai models/Warrior3.glb` |
| Mage | `BP_RDM_CasterCharacter` | `ai models/Mage.glb` |
| Warlock | `BP_RDM2_DarkCasterCharacter` | `ai models/Warlock.glb` |
| Rogue | `BP_RDM3_RogueCharacter` | `ai models/Rogue.glb` |
| Martial Artist | `BP_MA_MartialArtistCharacter` | `ai models/MartialArtist2.glb` |
| Summoner | `BP_SU4_SummonerCharacter` | `ai models/Summoner4.glb` |

Their hit points, damage, mana and growth by tier are the balance of 2026-11-01 (`880`, `SourceArt/mistward/balance6.json`), not level 5's: [the numbers](levels/mistward_castle.md#mistward_castle-the-castle).

### `mistward_castle`
Level 5's game (a Save As copy of `random_dungeonmagic_level5`) as a castle: [mistward_castle: the castle](levels/mistward_castle.md#mistward_castle-the-castle) has the whole of it.
- **Menu first:** through `mistward_castle_select`: the six heroes above (the Warrior with the Heater Shield on her arm); START opens Brokenspire, and AUTOPLAY plays any hero for a set time.
- **Characters:** the Warrior alone carries shields, every hero the torch, the Rogue alone sees and disarms traps and hides in stealth; the Martial Artist fights with fists, feet, knives and ten chi attacks; the Summoner calls fighters to her side, a new summoning for each tier boss she slays.
- **Properties:** five themed tiers (the stone dungeon, a castle keep, dwarven deep halls, then mixed) opening at 50 % of the tier before, rooms of other shapes with vaulted and domed ceilings, a boss and a guarded ring at each opening, thirteen kinds of traps, teleporters, prisoners and caged monsters, eight special rooms, boss slashes, harvests, potions and scrolls made at the anvil, monsters that shoot, the arena's audience; once tier 5 is half cleared the final boss, Aurorim, whose death opens a door back to Brokenspire.
- **Scripts:** `863`-`880`, `889` (and `885`, `886`, `898`, shared with the town).

### `martial_arts`
One room of `mistward_castle` (the great hall alone, 30 m, no doors) to try the Martial Artist in: all ten chi attacks with infinite mana, her fists, dodge and dash, three monsters of tier 1 that come back after one falls. Script `873`; [its part of the castle's document](levels/mistward_castle.md).

### `brokenspire`
The castle's starting town ([Brokenspire](levels/brokenspire.md)) and the wilderness round it ([the wilderness](levels/wilderness.md)), on one level (a Save As copy of `mistward_castle`).
- **The town:** a walled town of 500 m generated by rules from a new seed every game: the square, the trades and their services, homes lived in, burned and boarded up, 32 kinds of townspeople at their rounds of work, 16 quests, gardens, pens and cooking fires, an hour-long day and night, the castle building's Mistward Hall and its Mistgate into the castle.
- **The wilderness:** a continent of 300 by 300 km made from one seed as she comes to it (the ground within a 2 km square round her), 28 terrain templates, rivers, lakes and roads, places to find, a sky, weather, wild animals to hunt, farms of crops, a map from above with a fog of war, fast travel and named saves.
- **The cities:** [Vel Morrath](levels/vel_morrath.md) (a holy city north-east of Brokenspire), [Ashenreach](levels/ashenreach.md) (a forge city due north, at the edge of a burned plain) and [Graymourne](levels/graymourne.md) (a fog-bound port on the northern coast), each of Brokenspire's size with its own people and quests and a gate down into its dungeon, built as she nears it.
- **Scripts:** `881`-`888`, `890`, `892`-`894`, `896`, `898`.

### `vel_morrath`
The catacombs under Vel Morrath's cathedral, entered by the stair at the choir's far wall ([Vel Morrath](levels/vel_morrath.md)): five tiers, each a floor 4.5 m below the last, joined by ramped stairs; the dungeon's old stone, the crypt stone, a buried cathedral's arches and deep halls by tier. The Escape menu's "Return to Vel Morrath" brings her back before the cathedral's door. Played from the editor it starts the generator's default hero. Script `891`.

### `war_engine`
The War Engine, the besieged factory under Ashenreach's Great Foundry, entered by the iron gate in its furnace hall ([Ashenreach](levels/ashenreach.md)): five tiers of foundry brick and dwarven forge halls, gears, chains and ore carts by the walls, and eleven kinds of machines and half-machines among the castle's monsters. "Return to Ashenreach" brings her back. Script `895`.

### `sewers`
The sewers under Graymourne, entered by the sewer gate in the Sluice House ([Graymourne](levels/graymourne.md)): five tiers going down as the catacombs' do, in damp sewer brick and a vaulted cistern, sludge, rags and the drowned's things by the walls, and eleven kinds of drowned sailors and fish-men among the castle's monsters. "Return to Graymourne" brings her back. Script `897`.

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
| Warrior (jrpg-fem5-tripo) | `ai models/Warrior.glb` | `BP_JRPGFem5Character`, `BP_SFC_Fem5Character`, `BP_RDM4_WarriorCharacter` | `L_Meshy_Meadow`, `sf-city-level`, `random_level`, `random_dungeon_level`, `random_isometric_village_level`, `random_dungeoncombat_level`, `random_dungeonmagic_level4`; formerly `random_dungeonmagic_level5` |
| Warrior (Warrior3) | `ai models/Warrior3.glb` | `BP_JRPGWarrior3Character`, `BP_RDM5_Warrior3Character` | `L_Meshy_Meadow`, `random_dungeonmagic_level5`, Mistward Castle's game (`mistward_castle`, `brokenspire`, `vel_morrath`, `war_engine`, `sewers`) |
| Mage (girl-caster-tripo) | `ai models/Mage.glb` | `BP_JRPGCasterCharacter`, `BP_RDM_CasterCharacter` | `L_Meshy_Meadow`, `random_dungeonmagic_level`, `random_dungeonmagic_level4`, `random_dungeonmagic_level5`, Mistward Castle's game |
| Warlock (girl-darkcaster-tripo) | `ai models/Warlock.glb` | `BP_JRPGDarkCasterCharacter`, `BP_RDM2_DarkCasterCharacter` | `L_Meshy_Meadow`, `random_dungeonmagic_level2`, `random_dungeonmagic_level4`, `random_dungeonmagic_level5`, Mistward Castle's game |
| Rogue | `ai models/Rogue.glb` | `BP_JRPGRogueCharacter`, `BP_RDM3_RogueCharacter` | `L_Meshy_Meadow`, `random_dungeonmagic_level3`, `random_dungeonmagic_level4`, `random_dungeonmagic_level5`, Mistward Castle's game |
| Martial Artist | `ai models/MartialArtist2.glb` | `BP_JRPGMartialArtistCharacter`, `BP_MA_MartialArtistCharacter` | `L_Meshy_Meadow`, `martial_arts`, Mistward Castle's game |
| Summoner (Summoner4) | `ai models/Summoner4.glb` | `BP_JRPGSummoner4Character`, `BP_SU4_SummonerCharacter` | `L_Meshy_Meadow`, Mistward Castle's game |
| Summoner (Summoner3) | `ai models/Summoner3.glb` | `BP_JRPGSummoner3Character`, `BP_RDM5_Summoner3Character` | `L_Meshy_Meadow`, `random_dungeonmagic_level5` |
| Summoner (the first) | `ai models/Summoner.glb` | `BP_JRPGSummonerCharacter`, `BP_RDM5_SummonerCharacter` | `L_Meshy_Meadow`; formerly `random_dungeonmagic_level5` |
| Summoner2 | `ai models/Summoner2.glb`, as a MetaHuman | `BP_JRPGSummoner2Character`, `BP_RDM5_Summoner2Character` | formerly `random_dungeonmagic_level5` |
| Space fighter | pack meshes, kitbashed | `ASSFighter` (C++) | `starship_level` |

"`L_Meshy_Meadow`" means a character has a game mode for the meadow (`BP_JRPG<name>GameMode`); the meadow plays whichever one it was last set to.

## Other maps

These are in the project's own folders but are not levels to play on their own.

| Map | What it is |
|---|---|
| `random_dungeonmagic_level4_select`, `random_dungeonmagic_level5_select`, `mistward_castle_select` | the hero menus of levels 4 and 5 and of Mistward Castle (`RDHeroSelectGameMode`): they open the dungeon with the hero chosen (Mistward Castle's opens Brokenspire, and starts the packaged game) |
| `L_Fig4_Meadow_Cine`, `L_Meshy_Meadow_Cine`, `soldier_level_Cine`, `ff_level_Cine`, `ff2_level_Cine`, `castle_level_Cine`, `sf-city-level_Cine`, `random_level_Cine`, `random_dungeon_level_Cine`, `random_isometric_village_level_Cine` | copies for the demo reels (`MoviePipelineGameMode`): an AI demo character runs a recorded route on the sequence clock. The dungeon games and the fighter have no copy: their reels are rendered on the level itself, with a pilot script playing the game |
| `fcl_lake_village`, `sfc_monolith` | sublevels streamed into `fantasy_castle_level` and `sf-city-level` |
| `L_Tripo_Trio_Showcase`, `L_Tripo_Quartet_Showcase` | stages of the trio and quartet reels (`TripoTrio_Showcase`, `TripoQuartet_Showcase`: the Warrior, Mage, Warlock and then the Rogue on plinths) |
| `L_RDM5_FaceStudio` | the stage of the Summoner's two face reels |
| `rl_scratch` | the scratch level the galleries are staged in (`900`-`904`) |
| `rl_perf` | an empty test level beside it; no script names it |

The Fab packs in `Content/` bring 743 maps of their own (611 without their level-instance and foliage sublevels) in 203 pack folders: demo, overview and showcase maps. They are not part of this project's game; [assets.md](assets.md) lists the packs.
