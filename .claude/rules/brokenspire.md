---
paths:
  - "claude_ue5/Source/claude_ue5/RD/RDTown*"
  - "claude_ue5/Source/claude_ue5/RD/RDGameInstance*"
  - "pipeline/unreal/881_*.py"
  - "pipeline/unreal/882_*.py"
  - "pipeline/unreal/883_*.py"
  - "pipeline/unreal/884_*"
  - "pipeline/unreal/885_*"
  - "claude_ue5/Source/claude_ue5/RD/RDTownDay*"
  - "pipeline/blender_numpy/bs_*.py"
  - "claude_ue5/SourceArt/brokenspire/**"
---

# Brokenspire (`881`-`884`, `RD/RDTown*.cpp`, `docs/brokenspire.txt`, `docs/levels/brokenspire.md`)

The starting town: a Save As copy of mistward_castle whose generator has `bTown` (its start section is the town: `ARDSection::PlanTown`) and `bTownLink` (also on the castle: gold, her things kept between the levels, the quests' counters, the way back). Every rule is behind those two switches; the other levels are unchanged.

## Building it

- **The plan draws everything from the section's seed**, in one order: the plan, then the shells (each building's own stream, `B.Seed`), the outdoors (a stream per step), the doors, then the furnishing (the plan's stream, building by building). `ActivateForPlay` repeats the same calls with static building off: the saved build's furniture and play's containers stay the same. A new draw must keep its place in that order, or every container moves.
- **One section of 168 tiles** (`SectionTiles`): the ground inside the wall is one hallway (`Corrs[0]`, owner 1000), so monsters and townsfolk path over it with the dungeon's `FindPath`; building rooms are rooms; door edges join a room to the ground or two castle rooms. The dungeon's shell (`ShellColumn`) is not used: walls between two rooms that touch would not be built.
- **The town's frame**: the plan is laid out from the gate (u 0) to the castle (u S-1) and mapped onto the tiles by the gate's side (`FRDTFrame`); a side of the frame becomes a side of the tiles with `Side(du, dv)`.
- **House Forge's pieces keep the village's frame** (`Town.<style>_<part>`, 780's Adjust: walls centred on their segment with the outside +X, roofs cell-centred with the eave +X); the dungeon's pieces their own (room face +X). The castle's walls are the Castle theme's, inward on the room's edge and outward a wall's thickness out; two rooms that touch each get a wall half a thickness into its own room.
- **The burned houses** are the timber pieces in House Forge's `MI_Wood_Burnt` (`FRDPiece::Material`): an instanced component per piece name (`HismsMat`), not per mesh.
- **The drawn ground is seen only**: everyone walks on an invisible flat floor at z 0 (`TownFloor`, as the village), and under the buildings the drawn ground sinks 40 cm. The stone foundation's top is lower than its bounds say, and the grass showed through the smithy's and the temple's floors; the castle's stone floor sat exactly at the ground's level.
- **Too few streets, too few homes**: with four side streets and 70 tries the town was 80 buildings in empty fields. Eight side streets and 170 tries give about 180.
- **Lights**: 1421 at first (the dungeon's torches in 180 buildings); the town halves the wall torches (`LightRoom`), 611 now. The square's fire baskets cast shadows, the torches do not. 30 FPS in the square in the editor's play (2440 x 1616), 24 at least.

## Playing it

- **`AActor` has a member `Role`**: a UPROPERTY named Role on an actor, or a parameter or local of that name in an actor's (or the generator's) function, fails UHT ("shadowing is not allowed") or MSVC (C4458). The townsperson's is `TownRole`.
- **F's order**: a door or container nearer than a townsperson wins (a resident standing before her door took F: "talk to a townswoman"); residents stand beside their door. A post on a tile something stands on is moved to the nearest free tile of the same room or the ground when they spawn (the town's fool, put inside a stall's tile, never walked).
- **The guards' leash**: a monster with `HomeRoom` takes no foe outside it and wanders only in it; a quest counts the Hall's guards killed whole (they stay dead for the game: counted from when the quest was taken, the quest could ask for more than were left).
- **Between the levels**: `URDGameInstance` (the project's GameInstanceClass) keeps her things (`GatherDroppable` plus what she wears and has learned), her purse, her storage, the town's seed and looted containers, the castle's tiers and its first set's looted containers. `RestoreCarry` runs when her combat component is made, after the start shield is put on: it clears her items first. The hero menu's START is a new game.
- **The PR review's finds (2026-11-02)**: whatever a level does when a tier opens (`OnTierOpened`: the boss, the guarded ring) is not done for a tier restored from the game instance (`CheckTierOpenings` passes an open tier by): the castle sets them again (`RestoredBossTiers` / `RestoredRingTiers`, tried once a second until a room of the tier before is seen), and a killed boss is counted (`bossdone:<tier>`). Everything of a level that is hers must go into the game instance before travel, or it goes with the level (her pile where she fell: `HerPiles`). A quest's progress reads the state itself (the tiers open, the guards dead), not a counter beside it. A service's price covers everything it does (the healer's mana and cures). A boarded door is never opened: a townsperson's walk through one is given up. A component cache keyed by name alone keeps the first caller's collision (`HismsMat`: name plus collision now). Command-line switches read once, into the game instance, not a static (it outlived PIE sessions).
- **The PIE test travels**: `OpenLevel` in play-in-editor keeps the game instance; the test's tick waits through the moment with no world (`travel_until`) and finds the new generator.
- **PowerShell 5.1 reads a UTF-8 file without a BOM as ANSI**: the map's "·" came out "Â·" when the test's JSON was printed (`Get-Content -Raw` without `-Encoding UTF8`); the game's text was right.

## The reel (Game Bar, 2026-11-02)

- **The packaged game has no pilot of the town**: autoplay is the castle's (asked in the town, it opens the castle). The tour (`StartTownTour`, `-RDTownTour`) runs on the real clock before the panel's pause returns from the generator's tick (the elder's panel pauses the game). The whole way from the square to the Mistgate is about 210 m, 80 s at her run: while the papyrus map covers the view she is put 100 m before it on the way (`-RDTourRun`). Rehearse it in play (`StartTownTour` from Python; `GetTownTourState`) before packaging: the rehearsal's times held in the recording (the Mistgate at about 45 s with the load).
- **Game Bar recorded the game this time** (its file named after `claude_ue5`), at 2560 x 1440 and about 26 frames a second though the window was 3840 x 2160, with the game's sound (-28 dB mean): the recorder's checks still apply (a clip of another app is deleted unseen). The output keeps Game Bar's variable frame rate; ffmpeg's null muxer warns of non-monotonic timestamps in the first pass, harmless.

## The user's list after the reel (2026-11-02: `885`, the castle's outside, day and night, the colour map)

- **Look at a pack's pieces before using them by name**: Castle Forge's `SM_Castle_Stone_Wall_02a` (the town wall's piece since 882) has an arched doorway through it, so the whole town wall was a row of arches. `01a` is plain; `02h` is an arrow slit; `02d`-`02g` and `02k` are windows. Picture a kit row in base colour (`SCS_BASE_COLOR`, orthographic) from both faces: the lit picture of the first probe showed only silhouettes.
- **The round tower's quarters** (`SM_Castle_Tower_Wall_02a`-`e`: a slit, a small window, a window, a doorway, plain) have their origin at the tower's middle and are placed raw (no centring). Their convex collision closes the doorway's foot (a trace through `02d` hit at 50 cm up): the towers have no mesh collision, and 32 hidden boxes round each ring leave the doors open (`Town.Collider`).
- **The spiral stair piece** (`SM_Stone_Stairs_01a`) is a quarter turn, 100 cm up, climbing clockwise from its own yaw (it spans yaw -90 to 0 with its low step at 0). Trace a stair piece's steps before laying a stair.
- **What the old shell hid shows from the walk**: the dungeon's 9.6 m columns in the Mistward Hall and the walls over the inner doorways stood through the roof once it was walked on. A piece taller than the town castle's room now ends under its ceiling (`AddPiece`), and the test counts anything through the walk.
- **Light through seams**: Castle Forge's pieces set edge to edge (a storey on a storey, a segment beside a segment) let the rooms' torchlight through as bright lines. They overlap by 14 cm now.
- **Moving the castle** a tile forward (so its towers leave the lane behind it) and widening its margin changes every seed's town: the plan's stream is not touched, but the plots see other free ground.
- **A filter that rewrites a list must be safe to run twice**: 870 turned the Warrior's `LT|` line into `L3|` and dropped any `L3|` line first. Run again, it found no `LT|` line and dropped her run line altogether (the user: "run is no longer mapped to the gamepad"). It writes her lines whole now (`885` and 870).
- **Day and night**: the sun is the level's atmosphere sun (881's), driven from the town's tick; the moon is a second atmosphere light made in play. Without the exposure's bias at night, the histogram exposure (bias 0.6, minimum 0.5 EV) would light a moonlit town like the day: 1.2 stops less at night, measured by pictures (noon 105, midnight 21 of 255).

- **The reel's hour**: at 17:24 (`-TownHour 17.4`) the low sun left the castle's front in shadow for the whole run (the second reel's first take); the afternoon (15:30) lights it. Look at a take's contact sheet before deleting the one before it: the dark take was deleted before its retake, and the retakes then failed.
- **Game Bar records whatever app the user is in**: with the user at the machine, two takes of three recorded their browser and Discord (deleted unseen) and the third stopped after 6.6 s. Record when the user leaves the machine alone, or ask.

## The map's pictures

- `rdm4_ui_gen.py` creates its board on the InvokeAI server when the board does not exist, and the server answered 500 to that: the batch went to the existing board "claude-ue5 level4 UI".
- `rdm4_ui_cut.py` sizes its export by kind (`SIZES`): the map's pictures are of kind `icon` (their style is the map's ink-and-wash, named under `icon` in `map_art.json`), the papyrus a `texture`.
