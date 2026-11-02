---
paths:
  - "claude_ue5/Source/claude_ue5/RD/RDTown*"
  - "claude_ue5/Source/claude_ue5/RD/RDGameInstance*"
  - "pipeline/unreal/881_*.py"
  - "pipeline/unreal/882_*.py"
  - "pipeline/unreal/883_*.py"
  - "pipeline/unreal/884_*"
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

## The map's pictures

- `rdm4_ui_gen.py` creates its board on the InvokeAI server when the board does not exist, and the server answered 500 to that: the batch went to the existing board "claude-ue5 level4 UI".
- `rdm4_ui_cut.py` sizes its export by kind (`SIZES`): the map's pictures are of kind `icon` (their style is the map's ink-and-wash, named under `icon` in `map_art.json`), the papyrus a `texture`.
