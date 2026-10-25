# random_dungeonmagic_level5: specification

What the game on `random_dungeonmagic_level5` does, requirement by requirement. It is derived from the C++ module (`claude_ue5/Source/claude_ue5/RD`), the level's data files, the pipeline scripts `824`-`859`, the generator of the saved level (its properties read in the editor) and the latest records of the level's test (`853`), on 2026-10-24 (branch `level5-spells-rings-monsters`, commit `cfe1998`).

It describes the game as built. Where the code and an earlier description (README, a card, a table's wording) disagree, the requirement follows the code and [§27](#27-known-deviations-and-open-issues) lists the difference. How the game is put together is in [design.md](design.md).

**Conventions**
- Requirements have an ID (`AREA-n`). A number in a requirement is the code's or the level's value.
- **Measured** marks a value a test or reel record showed, with the record named (`test_full10` is `claude_ue5/SourceArt/random_dungeon_magic5/test_full10.json`). Everything else was read from the code and data.
- "She" is the hero being played. Distances are in cm unless given in m; times in seconds.
- Values the pipeline writes into the level are marked *(level)*; C++ class defaults that no level-5 script sets are marked *(default)*.

## Contents

1. [Scope](#1-scope)
2. [Levels and flow](#2-levels-and-flow)
3. [Heroes](#3-heroes)
4. [Controls](#4-controls)
5. [The dungeon's shape](#5-the-dungeons-shape)
6. [Generation in play](#6-generation-in-play)
7. [Doors and containers](#7-doors-and-containers)
8. [Loot](#8-loot)
9. [Tiers of rooms](#9-tiers-of-rooms)
10. [Monsters](#10-monsters)
11. [Fighting](#11-fighting)
12. [Weapons](#12-weapons)
13. [Spells](#13-spells)
14. [Rings](#14-rings)
15. [Armour](#15-armour)
16. [Inventory, potions and food](#16-inventory-potions-and-food)
17. [Repairs, crafting and breaking weapons down](#17-repairs-crafting-and-breaking-weapons-down)
18. [Allies and corpses](#18-allies-and-corpses)
19. [HUD](#19-hud)
20. [Maps](#20-maps)
21. [The hero menu](#21-the-hero-menu)
22. [The Escape menu and volumes](#22-the-escape-menu-and-volumes)
23. [Sound and music](#23-sound-and-music)
24. [Blood, wounds and the face](#24-blood-wounds-and-the-face)
25. [Non-functional requirements](#25-non-functional-requirements)
26. [Configured values and verification](#26-configured-values-and-verification)
27. [Known deviations and open issues](#27-known-deviations-and-open-issues)
28. [Data sources](#28-data-sources)

---

## 1. Scope

A third-person dungeon crawler. The player picks one of five heroes in a menu level, then explores a dungeon generated as she walks: 81 sections of rooms in five rings (tiers), each ring opening when the one before is cleared. She fights the monsters of each tier, loots containers, wears armour, wields weapons she finds, learns spells from tomes, wears rings and makes repair items at anvils. A run lasts one play session: nothing of it is saved.

The level shares its C++ with the five other dungeon levels (`random_dungeon_level`, `random_dungeoncombat_level`, `random_dungeonmagic_level` to `_level4`); everything level 5 adds is behind its data or its flags, and those levels must play as before ([NFR-4](#25-non-functional-requirements)).

## 2. Levels and flow

- **FLOW-1** Two levels: the dungeon `/Game/RandomDungeon/Maps/random_dungeonmagic_level5` and its menu `/Game/RandomDungeon/Maps/random_dungeonmagic_level5_select` (the generator's `MenuLevel` *(level)*). The dungeon's game mode is `BP_RDM4_GameMode` (a child of `ARDHeroGameMode`).
- **FLOW-2** The dungeon played without a `?Hero=` option, with heroes and a `MenuLevel`, while the console variable `rd.HeroMenu` is not 0 (default 1), opens the menu level instead. Until it loads the screen is black and the generator does nothing else.
- **FLOW-3** With `rd.HeroMenu 0` (tests, reel renders) the dungeon plays its `DefaultHero`, the Summoner *(level)*.
- **FLOW-4** The hero played is the `?Hero=` option's if it names a hero, else `DefaultHero` if it exists, else the first hero. Her pawn class comes from her hero entry; her data is applied before anything reads it (§3).
- **FLOW-5** START in the menu opens `<dungeon>?Hero=<Name>`.
- **FLOW-6** The Escape menu's CHOOSE ANOTHER HERO opens the menu level; QUIT ends play (in the editor) or quits the game (§22).
- **FLOW-7** At 0 hit points she lies dead `RespawnSeconds` = 3.5 s, then stands up at the start room's centre (+100 cm up) with full hit points and mana. Her inventory, worn armour, rings, learned spells and found weapons stay; the dungeon, its tiers and what she looted stay.

## 3. Heroes

| Hero | Hit points | Mana (back a second) | Bonus | Starts with | Wears armour | Wields found weapons | Learns spells | Rings |
|---|---|---|---|---|---|---|---|---|
| Warrior | 140 | none | melee +30 % | sword and shield | light, medium, heavy | all | none | health |
| Mage | 70 | 100 (2.0) | | Fire (8 mana, 25 damage), Dark Fire (14 mana, 38 damage) | none | none | offense, protection, curse, summon | magic |
| Warlock | 100 | 60 (1.2) | | sword; Fire (10 mana) cast alongside the sword | light, medium | all | offense, curse | magic, health |
| Rogue | 100 | none | ranged +30 % | daggers (15 damage, 150 cm), crossbow (34 damage, 26 m, bolt 45 m/s); the roll | light | short blades, ranged | none | dexterity |
| Summoner (default) | 85 | 90 (1.6) | | Fire, Dark Fire, cast with her own clips | light, medium, heavy | none | offense, protection, curse, summon | magic |

- **HERO-1** Five heroes in this order: Warrior, Mage, Warlock, Rogue, Summoner. Pawns: `BP_RDM4_WarriorCharacter`, `BP_RDM_CasterCharacter`, `BP_RDM2_DarkCasterCharacter`, `BP_RDM3_RogueCharacter`, `BP_RDM5_Summoner3Character`.
- **HERO-2** When play begins the chosen hero's weapons, hit points, mana, mana a second, melee and ranged bonus, title, controls lines, Rogue controls and roll clips become the generator's (`ApplyHero`); what she may wear, learn and which rings she may wear are read from her entry when needed.
- **HERO-3** The heroes' own weapons and spells never break and are carried on her body when not drawn (holsters), where the hero has holster bones.
- **HERO-4** Monsters are as strong whichever hero plays: their hit points and damage follow a reference hero of 100 hit points and a 25-point blow (`MonsterReferenceHealth`, `MonsterReferenceBlow` *(level)*), not her numbers.
- **HERO-5** Hit points never come back by themselves (`RegenPerSecond` 0 *(level)*); mana comes back at her rate each second while she is alive and the game is not paused.
- **HERO-6** Tests can change hero in play (`SwitchHero`): the old pawn is replaced by the new hero's at the same place with full hit points.

## 4. Controls

The casters' layout (`bCasterControls` *(level)*). Combat keys are read only while the big map is closed or the tactical maps are on (they are: she fights under the map).

| Action | Keyboard and mouse | Gamepad |
|---|---|---|
| Move / look | W A S D / mouse | left stick / right stick |
| Jump | Space | A |
| Walking / running | R switches; Shift held runs | LT switches |
| Use what she holds (strike, shoot, cast) | left mouse, held repeats | RB |
| The spell key | right mouse or E: the alongside spell (the Warlock's Fire), else the drawn spell | LB |
| Draw weapon or spell 1 to 3 | 1, 2, 3 | D-pad left, up, right (not while the big map is open: the D-pad scrolls it) |
| Draw weapon or spell 4 to 10 | 4 to 9, 0 | none |
| Next / previous weapon | wheel down / up (wraps, skips alongside spells) | Y (next) |
| Roll (Rogue) | B | B |
| Open, close, use an anvil | F | X |
| Big map | M; arrows scroll, C centres | Back (View); D-pad scrolls, R3 centres |
| Inventory | I or Tab | Start |
| Escape menu | Escape | none opens it; B closes it |

- **CTL-1** The HUD's controls panel lists her hero's keyboard lines or gamepad lines by the device used last: any of 16 pad buttons or a pad axis beyond 0.3 means the gamepad; any of 20 keyboard / mouse keys or a mouse move means the keyboard.
- **CTL-2** Inventory: W / Up / wheel up / D-pad up and S / Down / wheel down / D-pad down move the cursor (wrapping); the left stick beyond 0.6 steps once, again after 0.4 s and every 0.22 s held (real time); Enter, Space, E, left mouse or A use the line; I, Tab, Start or B close it.
- **CTL-3** Repair picking: Backspace or B returns to the inventory list; I / Tab / Start close the inventory.
- **CTL-4** The anvil panel: cursor and use as the inventory; F, Backspace, I, Tab, Start, B or X close it. The F that closed it does not open it again in the same frame.
- **CTL-5** In the editor Escape reaches the game: the editor's stop-play key is moved to Shift+Escape for this project (`MoveEditorStopKey`, called by `858`).
- **CTL-6** Tests press keys through the player controller (`SimulateKey`, `SimulateAxis`), read exactly as real presses; `SetScriptedOnly` keeps real input out of the combat keys, the inventory and the Escape menu.

## 5. The dungeon's shape

- **WLD-1** Tiles are 300 cm. A section is 84 × 84 tiles (252 m) of 7 × 7 blocks of 12 tiles; each block holds one room or one hallway junction. Rooms are 600 cm high, hallways and junctions 400 cm.
- **WLD-2** The start section (0, 0) is centred on the world origin. A section's seed is a hash of its coordinates and `StartSeed` (20261011 *(default)*) for the start section, the session seed for every other. The session seed is the time at play start unless `FixedSessionSeed` is set; `RestartPlay(seed)` and `SetSessionSeed(seed)` set it for reels and tests.
- **WLD-3** A section's plan is a pure function of its coordinates and seed. Each block's kind is a weighted pick under per-section caps:

  | Kind | Weight | Size (tiles) | Cap | Kind | Weight | Size (tiles) | Cap |
  |---|---|---|---|---|---|---|---|
  | Barracks | 9 | 6-10 | 6 | Library | 5 | 6-10 | 3 |
  | Prison cells | 7 | 7-10 | 5 | Chapel | 4 | 7-10 | 2 |
  | Torture chamber | 4 | 5-8 | 3 | Crypt | 6 | 6-10 | 4 |
  | Storeroom | 9 | 5-9 | 7 | Treasury | 3 | 5-7 | 2 |
  | Armory | 6 | 5-9 | 4 | Guard room | 8 | 5-7 | 6 |
  | Kitchen | 5 | 6-10 | 3 | Forge | 4 | 6-9 | 2 |
  | Great hall | 2 | 9-10 | 1 | Hallway junction | 10 | 3 | 12 |

- **WLD-4** The start section's middle block is always the great hall (10 × 10 tiles) and it rolls no other hall; a runtime section may roll one.
- **WLD-5** Every room is reachable: the blocks are joined by a spanning tree of the 7 × 7 grid plus each other edge with probability 0.3. Hallways are one tile wide along the blocks' centre lines, each with a theme (well lit, dim, old tunnel).
- **WLD-6** Hallways leave every section edge at block rows / columns 1, 3 and 5: 12 per section, so neighbouring sections always join. *Measured* (853 `tiers`): 12 gratings round the start section.
- **WLD-7** Each room has a doorway on every side a hallway reaches, with a double door.
- **WLD-8** The shell's floor, ceiling and wall pieces follow the room's kind; a wall piece with variants (`Name_2` ...) takes one by a hash of the segment's place, never from the plan's random stream. Broken walls have a stone backing and an invisible seal so she cannot see or climb through them.
- **WLD-9** Rooms are furnished and lit for their kind: the great hall (columns, carpet, throne on a doorless far wall, banners, chandeliers, four braziers, chests), barracks (beds, a chest at a bed's foot 60 % of the time, tables), prison cells (cells along two walls with doors or gratings, bars on every open side, hay that blocks, bones, shackles), torture chamber, storeroom (shelves, barrels and crates in rows: all openable), armory (weapon racks, trunks, chests, wardrobes; an anvil and quench tub), kitchen (hearth, oven, cauldron, tables), library, chapel, crypt (tombs), treasury (chests and trunks, crystals), guard room, forge (forge, anvil, quench tub). Torch light, spacing and the share of dead torches differ by kind (the great hall 160 cd every 600 cm; a torture chamber 40 cd every 1500 cm with 30 % unlit; the library only candles).
- **WLD-10** Furniture never covers a lane tile, so the tile paths stay open; hallway clutter never blocks a path tile.
- **WLD-11** Lights flicker only within 40 m of her.
- *Measured* (`test_full10`): the start section holds 1015 containers (barrels and crates included), its great hall 4; a tier-2 set held 42 rooms, 91 chests and trunks and 13 monsters.

## 6. Generation in play

- **GEN-1** The start section is built in the editor and saved with the level. In play its interactive part (doors, containers, monsters, map data, fire points, anvils) is rebuilt from the same seed.
- **GEN-2** Each tick, around her: on each horizontal axis where she moves faster than 30 cm/s, the section 4500 cm ahead is queued; her own section and every neighbour within 1800 cm are queued whatever her direction *(default distances)*.
- **GEN-3** One section is built at a time, over frames, with 6 ms a frame *(default)*: the shell, then each room's furnishing, each hallway's decoration, the anvil, the monsters, the map data. The result does not depend on the budget. A section asked for at once (`GenerateSectionNow`) first finishes the one in progress.
- **GEN-4** A new runtime section shows a reveal: a glowing curtain 700 cm high on its border and a scan wave for 7 s, the sounds `Env.Generate` and `Env.GenerateHit`, and the HUD banner NEW DUNGEON SECTION GENERATED for 3.5 s.
- **GEN-5** Runtime sections more than 2 sections away (Chebyshev) are destroyed; the start section and the one being built never are. The map keeps what she saw of them.
- **GEN-6** A dropped section generated again is the same (same session seed) and keeps what she did there: rooms discovered, containers looted, monsters killed and where they lie, corpses used up.
- **GEN-7** A section of a tier that is not open is never generated ([TIER-2](#9-tiers-of-rooms)).
- **GEN-8** If she falls more than 400 cm below the floor she is put back where she last stood on the ground (or the start room's centre).
- **GEN-9** `RestartPlay(seed)` (reels, tests) puts the dungeon back to its start: every runtime section, the map, the queue, the blood, the music, the counters, the looted containers, the tiers' progress and the allies cleared; her weapons back to her hero's, her items, armour and rings gone; she revived at the start with weapon 1 drawn.

## 7. Doors and containers

- **DOOR-1** Each doorway has two leaves that open together; prison cells have one leaf hinged 5 cm from the corner.
- **DOOR-2** F (X) toggles the nearest door or container within 260 cm, in her section or the eight around it, less than 200 cm above or below her. A container counts 20 cm farther than it is, so a door at the same distance wins. Within an anvil's reach the anvil wins if it is nearer (§17).
- **DOOR-3** A door swings 95° away from whoever opens it (1.4 of its swing a second), a lid or wardrobe door 100° (1.8 a second), eased. Only a shut leaf or lid collides; a moving or open one never pushes anyone.
- **DOOR-4** A door a monster opened closes 2.5 s after nobody is in the doorway (her within 300 cm, a monster within 260 cm).
- **DOOR-5** The HUD names what F would do ("[F] open door", "close chest", "use the anvil").
- **CONT-1** Containers are chests, trunks, wardrobes (two doors, one container), barrels and crates; every one opens (a body and a part on a hinge). Sounds `Env.ChestOpen` / `Env.ChestClose`, `Env.DoorOpen` / `Env.DoorClose`, `Env.CellOpen` / `Env.CellClose`.
- **CONT-2** The first opening gives the container's loot and marks it looted. A container never gives anything again, also after its section is dropped and generated again; only `RestartPlay` forgets.

## 8. Loot

- **LOOT-1** Containers hold items in every section (`bStartLoot`, `bLootAllSections` *(level)*).
- **LOOT-2** The great hall's containers always hold the five tier-1 armour sets of the loot table (Templar's, Eastern Knight's, Desert Hero's, Tiefling's, Orc Warrior's Armour), one per container in turn (with four containers the first gets two), whatever the chance says. *Measured* (`test_full10` `loot`).
- **LOOT-3** Any other container holds anything with probability `ContainerLootChance` 0.33 *(level)*. *Measured*: 1960 of 6000 (32.7 %, `test_full10` `chance`), 1983 of 6000 (33.1 %, `test_s4`).
- **LOOT-4** A container that holds anything holds 1 to `MaxItemsPerContainer` 6 *(level)* picks, uniformly (*measured*: 319 / 346 / 339 / 291 / 318 / 347 for 1 to 6), each picked by its rarity among the items whose tiers include the section's tier (an item without tiers is in every tier).
- **LOOT-5** A pick of the generic Spell Tome becomes "Tome of <spell>": a spell of the section's tier, by the table's drop chances.
- **LOOT-6** Each pick comes 1 to the item's `FoundMax` at a time (materials 1 to 3; everything else 1).
- **LOOT-7** What a container holds is a pure function of the session seed, its section and its index: the order she opens containers in changes nothing, and no random stream the play uses is drawn.
- **LOOT-8** A container that holds nothing says "Empty: nothing inside".
- **LOOT-9** Taking loot plays `Player.Loot` and shows the FOUND plaque for 3.2 s (the first item's picture and name, "and N more").
- **LOOT-10** What happens to each item taken: a weapon her hero may wield joins her weapons; one she may not is carried; a tome teaches its spell if her hero learns its type, is carried if not, and is dropped with "You know <spell> already" if she knows it; a set of armour is carried once, and found again it mends hers to full; everything else stacks.
- **LOOT-11** Items in the level: 170. Healing 8, mana 8, speed 8, food 9 (each with a tier and rarity), armour 27, weapons 29, materials 15, repair items 5, rings 30, tomes 31 (the Spell Tome, rarity 25, and the 30 "Tome of" items, rarity 0, which only a Spell Tome becomes). The per-item tables are in README's [the game now](../README.md#random_dungeonmagic_level5-the-game-now), written from the same data.
- *Measured* (853 `tierloot`, 2500 containers a tier): each tier's containers hold only that tier's weapons and armour; weapons were 19.1 % of the tier-1 picks against 18.4 % expected.

## 9. Tiers of rooms

- **TIER-1** `MaxTier` 5 *(level)*. A section's tier is its ring round the start plus one: max(|x|, |y|) + 1. Tiers hold 1, 8, 16, 24 and 32 sections: 81 in all.
- **TIER-2** Tier 1 is always open. Tier T opens when tier T−1 is open and every one of its sections is cleared. Nothing past tier 5 exists.
- **TIER-3** A section is cleared when every room in it (not hallways or junctions) is discovered, every chest and trunk in it (not barrels, crates or wardrobes) is looted, and as many of its monsters are dead as it spawned. Progress is recorded when a section is first generated and kept for the run.
- **TIER-4** Notices for 4.5 s: "SET CLEARED  -  TIER t: n / N", "TIER t CLEARED" (the next cannot open yet), "TIER t IS OPEN" (with `Env.Generate`), "TIER 5 CLEARED: THE DUNGEON IS YOURS".
- **TIER-5** A hallway end whose neighbour is in a shut tier is sealed by an end wall just inside the border with two half gratings in front; one that would lead past tier 5 by an end wall. Each has an invisible blocker as wide and tall as the hallway. Seals are rebuilt on every generated section when a tier opens. *Measured* (853 `tiers`): a body stops 150 cm before the border; the gratings round the start section went when tier 2 opened; a tier-5 section had 3 walls toward "tier 6".
- **TIER-6** Within 450 cm of a seal, with nothing to open nearer: "Sealed: clear every set of rooms of tier T−1 to open tier T  (n / N cleared)" or "The dungeon ends here".
- **TIER-7** The tier panel under the minimap shows her section's tier, the sets cleared, her progress in this set and what opens the next tier (§19).
- **TIER-8** Monsters, loot and tomes follow the tier (§8, §10).
- *Measured* (853 `tiers`): at the start only tier 1 is open and tier 2 is not generated; clearing the start section said TIER 2 IS OPEN; tiers 3, 4 and 5 opened in turn; a cleared set generated again had 0 living monsters and its 13 corpses.

## 10. Monsters

- **MON-1** 55 kinds from the monster gallery ([docs/monsters.md](monsters.md)), each in one tier: 8, 8, 14, 19 and 6 kinds in tiers 1 to 5. Abilities: none (16 kinds, all of tiers 1 and 2), weaken (21), slow (10), poison (8). Nineteen hold a weapon from their pack. README's monster table lists each kind.
- **MON-2** With `bCombat` exactly round(rooms × `MonsterCoverage`) of a section's rooms (not junctions) get one monster each, `MonsterCoverage` 0.3 *(level, from `791`)*, on a free tile at least 1500 cm from the start room's centre.
- **MON-3** A section spawns only the kinds of its tier (if a tier had none, the nearest tier below, then above), by weight (1 each).
- **MON-4** Hit points = 100 × `TierHealth[tier]` × the kind's factor / the mean factor of the tier's kinds; damage likewise from 25 × `TierDamage`. A kind's factor is 0.8 to 1.2 by its gallery rank within its tier.

  | Tier | Hit points | Damage | Speed | Time between attacks | Ability strength |
  |---|---|---|---|---|---|
  | 1 | 50 | 11.25 | × 1.0 | × 1.15 | 0 |
  | 2 | 100 | 25 | × 1.05 | × 1.0 | 0 |
  | 3 | 160 | 33.75 | × 1.1 | × 0.92 | 1.0 |
  | 4 | 240 | 43.75 | × 1.15 | × 0.85 | 1.4 |
  | 5 | 340 | 55 | × 1.2 | × 0.78 | 1.8 |

  *Measured* means (`test_full10` `monsters`): 50.8 / 11.4, 104.5 / 26.2, 158.8 / 33.4, 233.8 / 42.8, 342.2 / 55.2; each monster's speed and attack interval against its kind's matched the tier factor within 0.01; no kind in a wrong tier; no ability below tier 3.
- **MON-5** A kind's walk speed (90 to 220 cm/s) was measured from its feet in its walk clip, when its blows land from its fastest bone, its time between attacks 1.6 s (1.9 s for kinds taller than 280 cm), its reach 70 + 0.9 × its measured radius, its footstep length 40 + 0.25 × its height (`859`).
- **MON-6** Wandering: a monster walks a tile path to a random tile of another room of its section, waits 3 to 9 s, and goes again. A shut door on its way it opens (it asks where the door is heading, not how far it has moved). Stuck for 0.5 s it sidesteps; for 2.5 s it gives up the trip.
- **MON-7** Noticing (every 0.4 s): she is within 1000 cm (`AggroDistance`) and 300 cm up or down, and either a tile path to her is at most 2 × the straight distance + 1200 cm (same section) or she is within 600 cm (across a section border). It roars (`Monster.<set>.Roar`, at most every 8 s). A monster that is hurt notices her at once.
- **MON-8** A monster gives up beyond 2200 cm (`LoseDistance`) or 400 cm up or down, waits 1 s and wanders again.
- **MON-9** Chasing: it plans again every 0.35 s (straight at her on the same or a neighbouring tile, a tile path in its section, straight at her across a border within 900 cm), at min(walk speed × 1.6, 290 × its tier's speed factor) × (1 − its slowing).
- **MON-10** Attacking: when the gap between the capsules is at most 0.7 × its reach and it faces her (dot > 0.6) with its cooldown run out, it plays a random attack clip and `Monster.<set>.Attack`. The blow lands at the clip's hit time if she is still within reach + 30 cm, less than 260 cm up or down and in front (dot > 0.3), for its damage × (1 − the curse on it). Then it waits its time between attacks.
- **MON-11** From tier 3 a blow that lands carries the kind's ability, at the tier's strength (1.0, 1.4, 1.8):

  | Ability | Effect on her | Lasts (renewed to the later end) | Message |
  |---|---|---|---|
  | Poison | max(current, blow × 0.10 × strength) hit points a second, taken in pieces of at least 2, past armour | 3 + strength s | "You are poisoned" |
  | Weaken | her blows and spells do clamp(0.15 × strength, 0, 0.5) less (15 / 21 / 27 %) | 4 + strength s | "You are weakened: your blows and spells do less" |
  | Slow | she moves clamp(0.2 × strength, 0, 0.6) slower (20 / 28 / 36 %) | 2.5 + 0.5 × strength s | "You are slowed" |

  *Measured* (`test_full10` `abilities`, tier 3): Dardan weakened her 15 % for 5.0 s; Tank slowed her 20 % for 3.0 s; Alien poisoned her at 3.6 a second for 4.0 s (4.2 lost in 1.5 s); Dispel Hex cleared all three and kept a new poisoning off.
- **MON-12** A blow (not a burn or a cloud) makes it flinch: the blow it was winding up is lost and it is stunned for clamp(0.6 × its flinch clip, 0.25, 0.55) s.
- **MON-13** At 0 hit points it plays its death clip, its capsule stops colliding, and 0.8 s later the body is down (`Env.BodyFall`, a blood pool). With `bKeepCorpses` *(level)* the corpse freezes where it fell and stays for the run. Its kill is recorded by its place in its section's spawning order; a section generated again lays the dead as corpses where they fell and spawns the living ones where they were first.
- **MON-14** Monsters block her (`bMonstersBlockPawns`).
- **MON-15** A monster hunts an ally of hers instead of her when the ally is within 1000 cm and nearer than 0.85 × her distance; a veiled or dead hero is nobody's target.
- **MON-16** A monster's steps, idle voice (every 7 to 15 s, 2.5 to 5 s while after her) and drips are heard and seen only within 32 m of her. Six sound families (Troll, Mutant, Daemon, Horned, Dog, Spider) are shared by the 55 kinds.

## 11. Fighting

- **CMB-1** An attack is refused while she is dead, attacking, rolling, in the inventory or at the anvil, or when the weapon has no attack clips.
- **CMB-2** A cast she lacks the mana for is refused: "<spell> takes N mana: more than you have (M)" when it costs more than her maximum, else "Not enough mana for <spell>"; `Player.NoMana` plays and the mana bar's frame flashes red for 0.6 s. A spell still cooling down is refused: "<spell> is not ready:  N s". Both messages are given at most every 0.6 s.
- **CMB-3** Each attack takes the weapon's next clip in turn. A spell turns her toward the monster it will follow (the nearest she can see in reach); a melee weapon toward the nearest living monster within its reach + 160 cm that is not behind her.
- **CMB-4** Mana and the cooldown are taken when the attack starts; an attack broken off gives neither back. Cooldowns are kept per weapon name.
- **CMB-5** While attacking she moves at 0.12 of her speed. Any attack ends her Shadow Veil.
- **CMB-6** A melee blow lands at the clip's hit time on every living monster within the weapon's reach of her capsule, less than 260 cm up or down and inside its arc (any within 40 cm whatever the angle). `Player.Whoosh` plays 0.16 s before. If it hit anything the weapon loses 1 durability (once a swing).
- **CMB-7** Damage = the weapon's damage × (1 + bonus) × (1 − her weakness), the bonus being her melee bonus for a melee weapon, her ranged bonus plus her dexterity ring for a weapon whose bolt is a mesh (crossbows, bows), none for magic. The monster takes it × (1 + the curse on it). *Measured* (`test_full10` `rings`): the Rogue's crossbow 44.2, with Dexterity Ring 10 78.2.
- **CMB-8** Bolts (spells and ranged weapons) leave her hand (or the weapon's muzzle), fly at the weapon's speed toward the monster she turned to, turning toward it at most `BoltTurnRate` degrees a second (learned spells 260; the crossbow 0: straight), and burst on the first monster or wall they meet or after reach + 150 cm. A crossbow bolt or arrow that hits a wall stays in it 8 s. A plain burst does the full damage to the monster hit and half to each other within the weapon's splash; if it hit anything the weapon loses 1 durability.
- **CMB-9** A target is the living monster in reach, less than 300 cm up or down and not behind her, with the lowest gap (× 1.8 if off to the side), that she can see (a trace from her to its middle, its top or either side clear).
- **CMB-10** A blow on her goes through, in order: her roll's dodge window (a miss); a Null Sanctum she stands in (ignored); Shadow Veil (misses with its chance); a ward (a pool absorbs, or a charge takes the whole blow); Mirror of Retribution (its share dealt back to the monster); a Rune of Warding she stands in (its share off); her armour plus Iron Skin, together at most 95 %. A blow that reaches the armour step wears the worn set by 1. Then hit points; at 0 an Undying Pact leaves her at its share once. She bleeds, `Monster.Strike`, `Blood.Splat` and `Player.Hurt` (or `Player.Death`) play, the screen's edges flash red for 0.5 s, and she flinches unless she is attacking or flinched in the last 1.2 s. *Measured* (`test_full10` `damage`): a 12-point blow took 12 bare, 11.4 in Orc Warrior's Armour (5 %), 9.0 in Demonic (25 %), 6.0 in Epic Plate (50 %), each wearing it 1.
- **CMB-11** Poison and the Blood Nova's price come straight off her hit points (no armour, ward or zone); the pact still saves her.
- **CMB-12** Her speed = her own × (0.12 while attacking) × (1 + the strongest speed potion) × (1 − her armour's slowing) × (1 − her slowness).
- **CMB-13** The roll (heroes with a roll clip: the Rogue): B rolls her 420 cm over 0.82 of the clip the way she moves (backward if she stands still or moves more than about 134° from her facing), her move input ignored meanwhile, again 0.25 s after it ends; it breaks off an attack; blows miss her inside the dodge window `RollDodge` (shares of the roll; intended 0.05 to 0.75: see [§27](#27-known-deviations-and-open-issues)).
- **CMB-14** Her blows, bolts and spells never touch her allies.

## 12. Weapons

- **WPN-1** 29 found weapons (`weapons_table.json`): short blades 9, one-handed swords 5, short swords 4, two-handed swords 4, ranged 4 (two bows, two crossbows), curved and eastern swords 3; rarity 33 each; each found in the tiers the table gives.
- **WPN-2** Who wields what: the Warrior and the Warlock all; the Rogue short blades and ranged weapons; the Mage and the Summoner none (they carry them). One she cannot wield says "The <hero> cannot wield the <weapon>".
- **WPN-3** Damage = 8 + 3 × the damage rating (then her bonus); one attack every 1.6 − (speed rating − 1) × 1.05 / 9 s (1.6 s at speed 1 to 0.55 s at 10).

  | Type | Reach | Arc | Clips |
  |---|---|---|---|
  | short blades | 150 | 110° | her own melee clips (the Rogue both hands) |
  | short sword | 165 | 120° | her own |
  | one-handed sword | 175 | 130° | her own |
  | curved and eastern | 180 | 135° | her own |
  | two-handed sword | 210 | 160° | three two-handed cuts made for it |
  | bow | 3000, arrows 5000 cm/s | | a bow shot made for it |
  | crossbow | 2600 (the dwarf crossbow 2800) | | the Rogue's own shot or one made for it |

- **WPN-4** A found weapon is held where its handle was measured on its model (`854`): the grip's middle in her palm, a two-handed sword's second hand on its hilt. *Measured* (853 `weapons`, `test_g2`): one-handed grips 5.3 cm from her palm; the Warrior's Plate Knight's Sword's left palm 0.6 cm off the hilt line.
- **WPN-5** Every attack that hits takes 1 off a found weapon's durability (the table's 52 to 100). At 0 it breaks at the start of the next tick: removed from her weapons, "Your <weapon> broke", and she draws her first weapon if it was in her hands. Her heroes' own weapons never break.
- **WPN-6** Found weapons are not carried visibly on her when not drawn (no holster) and have no picture on the weapon bar (their initials).

## 13. Spells

- **SPL-1** 30 spells (`spells.json`, the user's table), each of a type (offense, protection, curse, summon) and a kind (what the code does: 21 of `ERDSpellKind`'s 22 values are used). Its tome's tier follows its mana: up to 15 tier 1, 30 tier 2, 60 tier 3, 110 tier 4, more tier 5. Where the table gives no damage it is 25 × (mana / 8)^0.75; a lasting spell's damage is a second.
- **SPL-2** A tome teaches its spell to a hero whose card learns its type: the Mage and the Summoner all four, the Warlock offense and curses, the Warrior and the Rogue none. Learned: "You learn <spell>:  key N" (or "the wheel" past 10), `Player.Learn`. Refused: "The <hero> cannot learn <spell> (<type>)" and the tome is carried; it can be tried again from the inventory.
- **SPL-3** A learned spell joins her weapons as a spell weapon cast with her own cast clips (copied from her first spell that has no bolt mesh), with the table's mana, cooldown, reach, speed and effects; it never breaks. A hero without such a spell (the Warrior, the Rogue) cannot learn any.
- **SPL-4** The Mage's and the Summoner's Fire and Dark Fire and the Warlock's Fire are the table's Fire Bolt and Dark Fire in look, flight and cooldown, with their cards' mana and damage. *Measured* (`test_s6`): Fire Bolt 25 damage (the card's), Dark Fire 60.8 (38 + 60 % burn).
- **SPL-5** Each spell does what its kind says, with the table's numbers:

  | # | Spell | Mana | Cooldown | Lasts | What it does in the game |
  |---|---|---|---|---|---|
  | 1 | Fire Bolt | 7 | | | a bolt: 23 damage, half to others within 170 cm |
  | 2 | Dark Fire | 12 | | 4 s | a bolt: 34 damage, then 60 % more burning over 4 s, 30 % of the burn back to her |
  | 3 | Ash Ward | 15 | 10 s | 8 s | a shield on her that takes 3 blows whole |
  | 4 | Frost Shard | 14 | | 2 s | a bolt that passes through monsters: 31 damage each, slows them 40 % for 2 s |
  | 5 | Shadow Lash | 18 | 2 s | | a 150° arc within 420 cm: 46 damage and a launch at 600 cm/s away (+160 up), stunned at least 0.45 s |
  | 6 | Iron Skin | 22 | 15 s | 12 s | +40 % to her armour's share |
  | 7 | Bone Spear | 20 | | | a bolt that passes through: 50 damage each |
  | 8 | Dispel Hex | 25 | 12 s | 3 s | ends her poison, weakness and slowness; none takes hold for 3 s |
  | 9 | Life Drain | 24 | 3 s | 3 s | a channel on the monster she faces (within 1200 cm): 19 a second, 60 % back to her; ends if it dies or moves 1600 cm off |
  | 10 | Chain Lightning | 30 | | | a bolt: 68 damage, then jumps to 4 more monsters within 700 cm she can see from the burst, each × 0.85 |
  | 11 | Bone Armor | 35 | 20 s | 15 s | a shield that takes 5 blows whole |
  | 12 | Plague Cloud | 38 | 6 s | 6 s | an area at the target: 13.5 a second within 350 cm |
  | 13 | Shadow Veil | 40 | 25 s | 4 s | monsters lose her; 75 % of blows miss; ends when she attacks |
  | 14 | Curse of Frailty | 42 | 10 s | 8 s | monsters within 500 cm of the target take 35 % more and deal 35 % less |
  | 15 | Fireball | 45 | 4 s | | a bolt: 91 damage to every monster within 350 cm of the burst |
  | 16 | Raise Dead | 55 | 20 s | 30 s | up to 3 corpses within 1200 cm rise as allies at 60 % of their hit points (§18) |
  | 17 | Rune of Warding | 60 | 30 s | 10 s | a zone at her feet, 400 cm: blows on her inside take 50 % less |
  | 18 | Blood Nova | 28 | 8 s | | costs 15 % of her current hit points (never the last): 64 damage within 500 cm of her |
  | 19 | Mirror of Retribution | 70 | 35 s | 5 s | a monster's blow is dealt back to it whole; she takes the rest (none) |
  | 20 | Soul Rend | 65 | 6 s | | a bolt: 121 damage |
  | 21 | Blizzard | 80 | 12 s | 8 s | an area: 17.6 a second within 500 cm, slows 50 % |
  | 22 | Corpse Explosion | 75 | 3 s | | up to 4 corpses within 800 cm of the target burst (gone for good): 134 damage within 400 cm of each |
  | 23 | Spectral Bulwark | 100 | 60 s | 10 s | a shield that absorbs 60 % of her maximum hit points |
  | 24 | Hellfire Pillar | 110 | 15 s | 6 s | 179 damage within 210 cm of the target, then burning ground: 26.9 a second within 350 cm |
  | 25 | Void Rift | 120 | 20 s | 4 s | pulls monsters within 600 cm toward it at 300 cm/s; 47.5 a second |
  | 26 | Undying Pact | 150 | 180 s | 60 s | a blow that would kill her leaves her at 40 % of her hit points, once: "Your pact holds: you rise again" |
  | 27 | Summon Abyssal Knight | 160 | 90 s | | a Daemon on her side until it falls: 204 hit points, 33 damage; cast again it is healed and brought to her (§18) |
  | 28 | Meteor Storm | 200 | 45 s | 5 s | 12 strikes over 5 s within 600 cm of the target (60 % aimed at a monster): 98 damage within 260 cm of each |
  | 29 | Null Sanctum | 220 | 120 s | 4 s | a zone at her feet, 400 cm: no blow hurts her inside |
  | 30 | Apocalypse | 300 | 300 s | | 380 damage to every monster within 2500 cm she can see |

- **SPL-6** The target point of an area spell is the feet of the monster she faces, else a point up to 700 cm ahead, 60 cm short of the first wall.
- **SPL-7** Spells without a target say so: "Nothing in front of you to drain", "No dead near you to raise", "No corpses there to burst".
- **SPL-8** Effects come from MagicProjectilesVol4 / Vol5, ToonExplosionVol1 / Vol2 and StylizedShieldsVol1, coloured by the packs' parameters; one aura of each kind on her at a time; a shield or zone ends at once when its time is up.
- **SPL-9** The status panel shows what holds her (§19).
- *Measured* (`test_s6`): learning (the Warrior keeps only her sword and carries a Tome of Fireball; the Warlock learns Frost Shard and Curse of Frailty and carries Ash Ward and Raise Dead; the Mage ends with 30 weapons), each of the 30 cast at tier-3 monsters with its effect measured, a cooldown refusing, Apocalypse refused for its price.

## 14. Rings

- **RING-1** 30 rings, three kinds of ten (Magic Potency, HP Potency, Dexterity), ring n giving +n × 10 %; rings 1 and 2 are found in tier 1, 3 and 4 in tier 2, and so on to 9 and 10 in tier 5; rarity 25, one at a time.
- **RING-2** Magic: + its share of her maximum mana (the Mage, the Warlock, the Summoner). Health: + its share of her maximum hit points (the Warrior, the Warlock). Dexterity: + its share to her ranged bonus (the Rogue).
- **RING-3** One ring of each kind is worn; another of the kind replaces it; Enter on the worn one takes it off. Refused: "The <hero> cannot wear the <ring>: it gives <mana | hit points | ranged damage>". Worn: "You put on the <ring>:  +N% <what>".
- **RING-4** When a maximum rises the difference is added to the current value; when it falls the current value is only clamped.
- *Measured* (`test_full10` `rings`): the Mage's mana 100 → 150 (ring 5) → 190 (ring 9) → 100 (off); the Warrior's hit points 140 → 196 (ring 4, current 130 → 186); the Mage refused an HP ring.

## 15. Armour

- **ARM-1** 27 sets (`SourceArt/summoner3/armour.json`): full plate 7, heavy 2, medium 2, light 3, partial 5, orc 8. A set's share of a blow = its damage-reduction rating × 5 % (5 to 50 %); its slowing = (10 − its speed rating) × 3 % (0 to 27 %); durability 125 to 600; rarity 20; the tiers the table gives. README's armour table lists each set.
- **ARM-2** Weight: full plate and heavy are heavy, medium and partial medium, light light; orc armour by its speed rating (7-10 light, 4-6 medium, 1-3 heavy).
- **ARM-3** A hero wears only the weights her card names (§3). Refusals: "The mage wears no armour"; "The <set> is <weight>: the <hero> wears only <weights> armour"; "The <set> was not made for the <hero>".
- **ARM-4** Each set is fitted to the body of every hero who wears its weight (78 fits: a heavy set 2, a medium 3, a light 4). Worn, its meshes follow her skeleton as she moves. *Measured* (853 `follow`): vertices bound to one bone stay within 1 cm of where her bone puts them while running and casting; the same armour left in its rest pose is more than 10 cm off.
- **ARM-5** One set is worn at a time; Enter in the inventory puts it on or takes it off ("You put on the <set>:  blows take N% less,  you move M% slower"; "You take off the <set>").
- **ARM-6** Each blow that reaches the armour step takes 1 off its durability. At 0: "Your <set> is worn out: blows take only N% less until it is mended", and it takes half its share; its slowing stays.
- *Measured* (853 `armourtable`): all 27 sets' shares, slowing, durability, tiers, rarity and weights match the table; Epic Plate at full 600, 597 after three blows, a share of 0.5, of 0.25 worn out.

## 16. Inventory, potions and food

- **INV-1** I, Tab or Start opens the inventory (not while dead); opening ends an attack and shuts the anvil panel; the game pauses (`bInventoryPausesGame`; reels turn it off). One panel at a time: the Escape menu, the inventory and the anvil.
- **INV-2** Sections in order: WEAPONS AND SPELLS, POTIONS AND FOOD (both always shown), REPAIR ITEMS, ARMOUR, RINGS, TOMES THE <HERO> CANNOT LEARN, MATERIALS, WEAPONS THE <HERO> CANNOT WIELD. Tags: ALWAYS AT HAND, IN YOUR HANDS (with left / full for a found weapon), WORN, WORN OUT, x N.
- **INV-3** A long list scrolls with the cursor and says "N more above,  M more below".
- **INV-4** The right side describes the line: a spell's type and the table's effect, its cooldown and duration, "Ready in N s"; a found weapon's type, ratings, durability and damage with her bonus; an item's effect; a set's weight, type, looks, share, slowing, durability and whether her hero wears it; a ring's kind and who wears it; a tome's spell and whether she learns it; then her hit points, mana, armour and running effects.
- **INV-5** Enter on: a weapon wields it ("You wield the <weapon>"); armour puts it on or off; a ring likewise; a repair item opens its list (§17); a tome tries to learn it; a potion or food uses it; a material says it is made into repair items at an anvil.
- **INV-6** Potions and food (level 4's 33, tiered by the loot table): healing + 10 to 80 % of her maximum hit points (refused at full); mana + 10 to 80 % of her maximum mana (refused at full or with no mana); speed + 10 to 80 % for 30 s (the strongest counts, they do not add up); food 1 to 9 % of her maximum hit points a second for 10 s (refused at full; foods add up). `Player.Drink` / `Player.Eat`.

## 17. Repairs, crafting and breaking weapons down

- **REP-1** Five repair items, every tier: Repair Kit 100 %, Patch Kit 75 %, Whetstone 50 %, Slickstone 40 %, Leather Strips 30 % of a full durability (rarity 10, 20, 30, 40, 50).
- **REP-2** Enter on one lists her carried sets and found weapons with their durability now and after; Enter mends one (up to full) and uses the item: "Mended with the <kit>: your <x>,  L to A of F". A whole one is refused ("Your <x> is whole already"); with nothing to mend: "Nothing to mend: ...".
- **CRF-1** Anvils: one in every forge and armory, the great hall always, and every section without one gets one in its largest room (`bAnvilEverySection` *(level)*), on a free tile off the lanes. *Measured* (853 `craft`): the great hall's anvil.
- **CRF-2** F (X) within 260 cm of an anvil in the room she stands in, nearer than any door or container, opens the anvil panel (pauses like the inventory, `Player.Anvil`).
- **CRF-3** Five recipes (README's recipe table): Leather Strips, Slickstone, Whetstone, Patch Kit, Repair Kit, each a count of parts where a part may be any of several materials ("wood (any)" is hardwood, timber and wood logs). All parts are planned from one running count, the materials she has most of first. Enter makes one: "You make a whetstone at the anvil"; short: "For a whetstone you need N wood (any) more, ...".
- **CRF-4** 15 materials, every tier, rarity 25, 1 to 3 at a time.
- **BRK-1** The anvil panel lists her found weapons and the weapons she carries unwielded under BREAK DOWN. Enter breaks one into materials × its lowest tier: blades 2 steel ingot, 3 iron ingot, 2 cured leather strip; bows 3 timber, 2 glue, 3 straw rope; crossbows 3 hardwood, 2 steel ingot, 2 epoxy. Refused: her own weapons ("Your own <weapon> is not to be broken"), the one in her hands ("... draw another first").
- *Measured* (853 `repair`, `craft`, `breakdown`): a worn-out set mended by two patch kits to the expected share; a found weapon to min(full, 10 + 0.75 × full); leather strips made from their parts; the Warrior's Plate Knight's Sword broken into 2 steel, 3 iron, 2 cured leather; the Mage's carried Longbow into 3 timber, 2 glue, 3 straw rope.

## 18. Allies and corpses

- **ALY-1** Allies are the raised dead (Raise Dead: up to 3, for 30 s, at 60 % of their own hit points, with their damage) and the Abyssal Knight (a Daemon with 100 × 3.4 × 0.6 = 204 hit points and 25 × 2.2 × 0.6 = 33 damage, until it falls; one at a time).
- **ALY-2** An ally fights the nearest monster within 900 cm of it that is within 1800 cm of her; with none it follows her, standing within 380 cm, and if more than 2600 cm away or 500 cm up or down it is put 240 cm beside her (the side with room, else 200 cm ahead).
- **ALY-3** She and her allies walk through each other; her camera passes through them; an ally the camera is inside is hidden. *Measured* (`test_s6` Raise Dead): all three true; in the spells reel's record the camera stayed at least 66 cm from her.
- **ALY-4** An ally's kills count for the section, not in her kills. A raised ally whose time runs out falls and is gone 2.5 s later. `RestartPlay` removes all allies.
- **ALY-5** Corpses (with `bKeepCorpses`) stay for the run; a corpse raised or burst is gone for good and is never laid again, its kill still counted.
- *Measured* (853 `corpses`): 3 kills lay within 5 cm of where they fell after 13 s, frozen; laid again within 30 cm when their section was generated again.

## 19. HUD

Every size is at 1080p and scales with the view's height.

- **HUD-1** Hurt flash: red bands on the screen's edges for 0.5 s after a blow reaches her.
- **HUD-2** Monster bars over each living monster after her or hurt in the last 6 s within 24 m: a 96 px bar (red, orange below half) and "<NAME>  <hit points>" with CURSED / SLOWED / BURNING. Allies' bars green: "ALLY  <NAME>  <N>s" (the Knight without seconds).
- **HUD-3** Damage numbers float up 1.1 s: yellow on a monster, red with a minus on her.
- **HUD-4** The status panel (bottom right): her title, KILLS, a hit-point bar (pulsing below 25 %), a mana bar (if she has mana), at most three weapon slots round the one in her hands with "N of M weapons  ·  A before, B after  (wheel)" when there are more; each slot its key, name and damage, its mana or a found weapon's durability (red below 20 %); a picture only when a slot has room beside it.
- **HUD-5** Chips over the panel: potion and food effects (SPEED, REGEN with seconds left) and a row of spells and afflictions: WARD n (or WARD n HP), IRON SKIN +N%, VEILED, MIRROR, UNDYING PACT, RUNE −N% and SANCTUM (inside), HEX-WARDED, DRAINING; POISON x/s, WEAKENED −N%, SLOWED −N% in red.
- **HUD-6** The controls panel (upper left): CONTROLS  -  KEYBOARD & MOUSE or GAMEPAD, RUNNING or WALKING, her hero's lines for that device.
- **HUD-7** The weapon bar (along the bottom): the first 10 of her weapons and spells, 64 px each, the drawn one framed in gold, its key (1 to 0; E for an alongside spell), its mana (red, and the picture tinted, when she has too little), a cooldown shading the slot from the top with the seconds left; the drawn weapon's name above, "(N more: the wheel)" past 10. Hidden in the inventory and at the anvil.
- **HUD-8** Death: a dark red veil, YOU HAVE FALLEN, "back to the middle of the dungeon...".
- **HUD-9** Banners: NEW DUNGEON SECTION GENERATED (3.5 s), the tier notice (4.5 s), the prompt "[F]  <what>" ("[X]" on the gamepad) or the seal prompt on a red box.
- **HUD-10** FOUND (3.2 s, 60 % down) and messages (2.6 s, 30 % down, on a painted plaque); while a panel is open its footer shows the message.
- **HUD-11** The interface is painted (boards, framed bars, slots, plates, plaques, pictures for every item, armour set, spell, ring and the heroes' weapons: 124 pieces) and lettered in three roles: titles, names, keys and lone numbers in Cinzel; text in Alegreya; labels in Alegreya SC (capitals written as small capitals).

## 20. Maps

- **MAP-1** The minimap (top right): 84 m across in a painted ring, north up, centred on her, the terrain fading toward the rim: rooms and hallways she discovered, tiles generated but unseen dimmer, lit lines where a discovered floor meets nothing, a new section tinted teal for 4 s; her arrow; "<discovered> / <generated> rooms    M  map".
- **MAP-2** The big map (M, or Back): a painted board 900 px wide showing 110 m from top to bottom, centred on her plus the scroll; the plaque DUNGEON MAP, a compass, a key, the doorways she found; each discovered room named (small capitals, on two lines or smaller where it is narrow) with TIER n under it. The game goes on under it; she walks and fights.
- **MAP-3** The big map scrolls with the arrows or D-pad at 4000 cm/s up to 40000 cm from her, and C or R3 centres it; while it is open the arrows do not walk her (an input context at priority 1000 takes them) and the D-pad does not draw weapons; opening it resets the scroll.
- **MAP-4** Markers on both: monsters within 25 m as red dots (elites, more than 1.25 × their section's average hit points, as orange triangles), gold stars on chests and trunks not looted yet in discovered tiles (open or shut), cyan diamonds on hallway ends toward sections with nothing discovered, red crosses on sealed hallway ends, a small anvil on anvils she has seen; the minimap writes "T<n>" in each discovered room.
- **MAP-5** Discovery: a room once she is inside it (or in its doorway), a hallway within 4 tiles of her along it, in her section.

## 21. The hero menu

- **MENU-1** A studio with a turntable (28° a second, reset to face the camera when the hero changes) showing only the chosen hero, her starting weapons in her hands and the others where she carries them.
- **MENU-2** The card: RANDOM DUNGEON, CHOOSE YOUR HERO; her name in her colour; hit points and mana as bars against the strongest hero's; MANA BACK, MELEE, RANGED, DODGE; MAIN ABILITIES, ARMOUR, STARTS WITH (each weapon or spell with its picture, damage with her bonus, reach or flight, mana). Five name plates along the bottom with arrows, START AS <NAME> pulsing bottom right, and the keys of the device in use.
- **MENU-3** Keys: A, Left, wheel up, D-pad left or LB the previous hero; D, Right, wheel down, D-pad right or RB the next (wrapping); the left stick beyond 0.6 steps, again every 0.35 s; Enter, Space, A or Start (or a click on START) opens the dungeon; a click on a plate or an arrow chooses.
- *Measured* (853 `select`): five heroes, the Warrior first and the Summoner last, Left from the first shows only her, Enter opens `random_dungeonmagic_level5?Hero=Summoner` with her pawn, 85 hit points and 90 mana.

## 22. The Escape menu and volumes

- **ESC-1** Escape opens and closes it (`bEscapeMenu` *(level)*); opening shuts the inventory and the anvil panel, pauses the game (`bMenuPausesGame`; reels turn it off) and shows the mouse.
- **ESC-2** Seven lines: Overall volume, Action sounds, Environment sounds, Music (sliders), RESUME, CHOOSE ANOTHER HERO, QUIT. W / S (Up / Down, D-pad) choose, wrapping; A / D (Left / Right, D-pad) move a slider 0.05; Enter, Space or A press a button; B closes. The mouse selects by hovering, presses buttons and drags sliders.
- **ESC-3** A sound plays at Overall × its category's volume: music (`Music.*`), environment (`Env.*`, `Atmos.*`: fires, doors, containers, the dungeon's sounds, the room tone), action (everything else: her, the monsters, the fighting, the spells). A change applies at once to what plays and is saved at once in the game's user settings (`GameUserSettings.ini`, `[RandomDungeon.Volume]`, keys `Overall`, `Action`, `Environment`, `Music`); it is loaded when play begins.
- *Measured* (853 `menu`): opens and pauses, seven lines, the environment volume set to 0.5 saved, the buttons answering, Escape toggling; a fire 2.5 m away 6.1 dB quieter at half volume.

## 23. Sound and music

- **SND-1** Every sound is an occasion of the generator's sound table (80 sets *(level)*), each a set of files, a volume, a pitch with a variation, and a distance falloff; an occasion without a set is silent. A set never plays the same file twice running.
- **SND-2** Placed sounds fade with their distance to her (not the camera): natural falloff to −40 dB at the set's falloff distance, a low-pass with distance, spatialised (not under `-deterministicaudio`, where the render's audio device would lose them).
- **SND-3** Fires (torches, braziers, hearths) loop as she nears them: at most 6 voices, the nearest first, each keeping its voice while it stays among them; their volumes are 0.4 of the combat level's (0.22, 0.26, 0.34). *Measured* (853 `fire`): −8.0 dB against the old volumes.
- **SND-4** Her sounds: footsteps (every 72 cm walking, 128 cm running), drawing a weapon, the effort of every other swing, the whoosh, a charge, a cast, the hit, a refused cast, her hurt cry and death, the roll, drinking, eating, the bag, loot, learning, repairs, the anvil.
- **SND-5** Music: four flat layers: a wandering track and atmosphere, a battle track and atmosphere. A fight is on while she is alive and was hurt or landed a hit in the last second, or a monster after her is within 2600 cm. The battle pair fades in from the track's start (0.35 s / 0.8 s); 3.5 s after the fight it fades out over 2.5 s and the wandering pair comes back over 2.5 s where it left off; each fight takes the next battle track. The session seed chooses the tracks.

## 24. Blood, wounds and the face

- **GORE-1** A blow on a monster throws drops and spray from the wound (stronger for a bigger share of its hit points, full when it dies); a blow on her from where she was struck toward the attacker; a burst corpse straight up. Drops fall, and a heavy drop always (a small one 20 % of the time) leaves a splat where it lands; splats fade after 45 s; at most 140 at a time.
- **GORE-2** A dead monster's body leaves a pool that spreads over 3 s (a corpse laid again gets none).
- **GORE-3** Each blow leaves a wound on that monster where the blow met its skin (up to 10, then the nearest grows), staying on the skin in any pose; the more hit points lost the more it bleeds.
- **FACE-1** The C++ has a face system (expressions on her face for being hurt, casting, finding something, a fight, low hit points, death, and blinks; built for the earlier Summoners' faces). The current level has no face data, so no hero's face moves ([§27](#27-known-deviations-and-open-issues)).

## 25. Non-functional requirements

- **NFR-1 Determinism.** The play, the loot, the sounds, the blood, the spells' rolls and the blinks draw from separate random streams, so a reel with a fixed session seed repeats: sound and blood never draw from a stream the play uses; loot is a pure function of the seed and the container; a killed monster's randoms are still drawn so the others keep their places.
- **NFR-2 No save.** Nothing of a run is written to disk; only the four volumes (and the editor's stop-play key) are.
- **NFR-3 Performance.** Section building is spread over frames (6 ms a frame); flicker only near her; corpses freeze (no tick); far sections are dropped; light draw distance 9000 cm.
- **NFR-4 Isolation.** Everything level 5 adds is behind its data or a flag that is off or empty on the other dungeon levels (`MaxTier`, `Spells`, `Recipes`, `bKeepCorpses`, `bEscapeMenu`, `bAnvilEverySection`, `bLootAllSections`, `MaxItemsPerContainer`, `ContainerLootChance`, `StartRoomItems`, `Heroes`, `UIArt`): they play as before. After a change to the combat component its tests run on the combat level (`793`), magic levels 1 to 3 (`813`) and level 4 (`828`).
- **NFR-5 Built by script.** The level and all its data are made by the numbered scripts (§26 and [design.md](design.md#11-build-pipeline)); nothing is arranged by hand.
- **NFR-6 Testable.** Every area has hooks for a scripted test (counters, probes, `SimulateKey`); the test presses keys as a player does.
- **NFR-7 Reels.** The game can be rendered by Movie Render Queue on the level itself with a pilot playing through its inputs (`815`, `814`, `816`); the HUD is drawn over the frames from the render's own record.

## 26. Configured values and verification

### 26.1 The level's generator (read in the editor)

| Group | Values |
|---|---|
| Layout | `TileSize` 300, `SectionTiles` 84, `BlockTiles` 12, `RoomHeight` 600, `CorridorHeight` 400, `StartSeed` 20261011, `TriggerDistance` 4500, `SafetyDistance` 1800, `UnloadSectionDistance` 2, `FrameBudgetMs` 6, `FallResetDepth` 400, `RevealDuration` 7 |
| Flags | `bCombat`, `bStylizedMap`, `bTacticalMaps`, `bCasterControls`, `bStartLoot`, `bLootAllSections`, `bAnvilEverySection`, `bKeepCorpses`, `bEscapeMenu`, `bMenuPausesGame`, `bMonstersBlockPawns`, `bSpatializeSounds` on; `bRogueControls` off until the Rogue is applied |
| Tiers and monsters | `MaxTier` 5, `MonsterCoverage` 0.3, reference 100 / 25, `TierHealth` 0.5 / 1.0 / 1.6 / 2.4 / 3.4, `TierDamage` 0.45 / 1.0 / 1.35 / 1.75 / 2.2, `TierSpeed` 1.0 / 1.05 / 1.1 / 1.15 / 1.2, `TierAttackInterval` 1.15 / 1.0 / 0.92 / 0.85 / 0.78, `TierAbility` 0 / 0 / 1.0 / 1.4 / 1.8, `AggroDistance` 1000, `LoseDistance` 2200, `ChaseSpeedScale` 1.6, `MaxChaseSpeed` 290, `KnightMonster` Daemon, `KnightStrength` 0.6 |
| Loot | `ContainerLootChance` 0.33, `MaxItemsPerContainer` 6, `StartRoomItems` the five tier-1 sets |
| Heroes | `DefaultHero` Summoner, `MenuLevel` the menu level, `RegenPerSecond` 0, `RespawnSeconds` 3.5, `RollDistance` 420, `RollCooldown` 0.25, `RollDodge` (1, 1) |
| Maps | `MapPanSpeed` 4000, `MapPanMax` 40000 |
| Sound | `SoundVolume` 1.5, `MusicVolume` 1.0, `CombatMusicDistance` 2600, `CombatMusicHold` 3.5, `FireLoopVoices` 6 |
| Tables | `Heroes` 5, `Items` 170, `Spells` 30, `Monsters` 55, `Recipes` 5, `Breakdowns` 3, `Sounds` 80, `Pieces` 98, `Effects` 4, `UIArt` 124, `UIFonts` 3; `FaceChannels`, `FaceCues` empty |

The stored player fields (`PlayerMaxHealth` 140, `Weapons` [Sword]) are the Warrior's; `ApplyHero` overwrites them when play begins.

### 26.2 The test

`pipeline\unreal\828_rdm4.ps1 "<plan>" <tag> [maxSeconds] -lv 5` plays the level in the editor and runs `853_rdm5_test.py`'s steps, writing `SourceArt/random_dungeon_magic5/test_<tag>.json`. Its 23 steps:

| Step | Covers | Step | Covers |
|---|---|---|---|
| `select` | MENU, FLOW-4/5, HERO | `maps` | MAP-1/2/4, TIER labels, CRF-1 |
| `loot` | LOOT-2/4/9/10, CONT-2 | `fire` | SND-3 |
| `wear` | ARM-3/5 | `tiers` | TIER-1 to 6, GEN-6/7 |
| `heroarmour` | ARM-3/4 | `tierloot` | LOOT-4, TIER-8 |
| `follow` | ARM-4 | `weapons` | WPN-2 to 5 |
| `damage` | CMB-10, ARM-6 | `chance` | LOOT-3/4/8 |
| `ui` | HUD-10/11, INV-2/3 | `corpses` | MON-13, ALY-5 |
| `armourtable` | ARM-1/2/6 | `monsters` | MON-1 to 5 |
| `repair` | REP-2, INV-5 | `abilities` | MON-11, SPL-5 (Dispel) |
| `craft` | CRF-1 to 3, CTL-4 | `spells` | SPL-1 to 7, ALY-1/3 |
| `rings` | RING-1 to 4, CMB-7 | `breakdown` | BRK-1 |
| `menu` | ESC-1 to 3 | | |

Latest records: `test_full10` (all 23 steps; 22 passed, `spells` failed on Ash Ward, where no place for a monster was found), `test_s6` (`spells` alone: passed, all 30), `test_c7` (14 steps: all passed), `test_g2` (`weapons`, `breakdown`: passed, with the uncommitted two-handed grip work). Every step has a passing latest record; no single record has all 23 passing.

Level 4's `827` steps (`menufirst`, `menuui`, `map`, `ui`, `stars` ...) cover the shared menu, painted map and stars.

## 27. Known deviations and open issues

Found while deriving this document. None was fixed here.

| # | What | Where | Effect |
|---|---|---|---|
| 1 | `RollDodge` on the saved level is (1, 1), not the intended (0.05, 0.75) | generator property; likely `825` copying a struct read from level 3's actor across a map load | the Rogue's roll almost never dodges on levels 5 (and probably 4); no test checks `DodgedHits` |
| 2 | Monster capsules from the mesh are never set: the assignments sit after a `#` on the same line | `859_rdm5_monsters_tiers.py:103` | every kind keeps radius 40, half-height 90; tall kinds may sink and small ones float (from the code; not seen in a render). README says "its capsule from its mesh" |
| 3 | `RestartPlay` adds the start section's monsters again without removing the old ones | `ARDSection::ActivateForPlay` appends to `SpawnedMonsters` | 132 living tier-1 monsters counted in `test_full10` (which restarts before most steps); affects tests and reels, not normal play (her death does not restart) |
| 4 | No monster can be an elite on level 5 | the HUD's rule (> 1.25 × average) against `859`'s factors (≤ 1.2) | README's "the strongest as orange triangles" never shows here |
| 5 | The level has no face data | `FaceChannels` / `FaceCues` empty since the rebuild from level 4 | README's "The Summoner has a face that moves" is not true of the current level |
| 6 | Hellfire Pillar: the instant hit reaches 0.6 × the radius, the ground burns 15 % of the damage *a second* (≈ 90 % more over 6 s) | `RDSpells.cpp` | README says "15 % more over 6 s" |
| 7 | Shadow Lash launches at 600 cm/s, not a 6 m push | `ARDMonster::Knock` | README says "pushes 6 m" |
| 8 | Null Sanctum, Rune of Warding and Spectral Bulwark protect only her | `URDCombatComponent::ApplyDamage` | the table's wording ("allies", "the whole party") |
| 9 | Soul Rend is a plain bolt; the `Rend` kind is unused; Mirror reflects only melee blows (monsters have no projectiles) | `spells.json`, `RDSpells.cpp` | "ignores armor", "reflects projectiles and spells" have nothing to act on |
| 10 | A tome of a known spell is dropped, not carried | `AddItem` | |
| 11 | Mana and cooldowns are spent at the cast's start, with no refund when it is broken off | `StartAttackWith` | |
| 12 | `Player.Break` (a weapon breaks, armour wears out) is not in the sound table, so silent; `Player.Repair`, `Anvil`, `Craft`, `Learn` fall back to `Player.Inventory` / `Player.Loot` | the level's `Sounds` | |
| 13 | The Summoner's card text in the level still says five sets were made for her (`852`'s wording); `856` updates only the four other heroes | `Heroes[Summoner].Armour`, the menu | the menu shows stale text; README's table shows the data file's |
| 14 | README says 22 spell kinds; the table uses 21 (`Rend` unused) | README | |
| 15 | The grip test passes at < 7 cm; README says 5.3 cm or less (the measured value) | `853` `weapons` | |
| 16 | CHOOSE ANOTHER HERO opens the menu without `?Hero=`, so it starts on the Warrior, not the hero played | `ActivateMenuLine` | |
| 17 | No gamepad button opens the Escape menu | `TickMenu` | |
| 18 | `SwitchHero` resets `Weapons` to the hero's own list: found and learned weapons are lost | `ApplyHero` | tests only |
| 19 | The atmosphere layers always play their set's first file | `TickMusic` (`MusicIndex[2]`, `[3]` never advance) | |
| 20 | The kitchen cauldron's flame (a candle effect at scale 2.5) is heard as a brazier | `AddEffect` (any effect scaled > 2 is a brazier) | |
| 21 | Stale comments: "four slots" at `RDHUD.cpp:381` (three are drawn); the `bStartLoot` header comment describes level 4 | source | |
| 22 | The controls panel's lines list neither Escape, keys 3 to 0 nor the map's arrows and C | `heroes.json`, `summoner_hero.json` | |
| 23 | README's measured empty-container share (33.7 %) matches neither latest record (32.7 %, 33.1 %) | README | corrected in README with this document |

Could not be checked here: the menu level's saved contents (it was not opened), whether the saved level overrides the class defaults marked *(default)*, the Warlock's and the Mage's own weapon numbers as stored on the level, and anything that needs a render (an editor render was running).

## 28. Data sources

| Data | File | Written into the level by |
|---|---|---|
| The four heroes, the monster reference, potions and food | `SourceArt/random_dungeon_magic4/heroes.json`, `items.json` | `825`, `856` |
| The Summoner | `SourceArt/random_dungeon_magic5/summoner_hero.json` | `852` |
| Weapons | `SourceArt/random_dungeon_magic5/weapons_table.json`, `weapon_frames.json` (measured), `w5_clips/<hero>/w5_times.json` | `854`, `855` |
| Armour | `SourceArt/summoner3/armour.json`, `armour_fit/` | `849`, `851`, `856`, `857` |
| Loot, materials, repairs, recipes, rings, tomes, breakdown, the fire volume | `SourceArt/random_dungeon_magic5/loot_table.json` | `857`, `858` |
| Spells | `SourceArt/random_dungeon_magic5/spells.json` | `858` |
| Monsters and tiers | `SourceArt/random_dungeon_magic5/monster_tiers.json` | `859` |
| Sounds and music | `SourceArt/random_dungeon_combat/sounds.json` | `797` (+ `825`, `857`) |
| Painted interface and fonts | `SourceArt/random_dungeon_magic4/ui_art.json`, `ui_art/layout.json`, `fonts/` | `830 --level 5` |
| Pieces and effects of the dungeon kit | `770` | `770` (inherited through the Save As chain) |
| Blood and wounds | `798` | `798` (inherited) |
