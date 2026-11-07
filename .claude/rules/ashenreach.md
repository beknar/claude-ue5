---
paths:
  - "claude_ue5/Source/claude_ue5/RD/RDForge*"
  - "pipeline/unreal/894_*"
  - "pipeline/unreal/895_*"
  - "claude_ue5/SourceArt/ashenreach/**"
  - "claude_ue5/SourceArt/war_engine/**"
---

# Ashenreach and The War Engine (`894`, `895`, `RD/RDForge.cpp`, the forge plan in `RD/RDTownPlan.cpp`; the user's spec of 2026-11-07, `docs/ashenreach.txt`, `docs/levels/ashenreach.md`)

The city is a wilderness town on `brokenspire` with the forge plan (`FRDWildTown::Plan` 2 -> the generator's `TownPlan`, `bForge`; `bMid` the rules it shares with the holy city: a landmark at the town's middle over a dungeon of its own); The War Engine is `war_engine`, a Save As copy of `mistward_castle` with its own `DungeonKey`. Every rule is behind `TownPlan == 2`, `TownDungeons` or a level's own data: Brokenspire, Vel Morrath, the other towns and the castle are unchanged.

## A town's own dungeon (2026-11-07, generalised from Vel Morrath's)

- **One level property was one city's**: `CatacombsLevel` (and `TownPlan == 1` at four places) made a dungeon Vel Morrath's alone. The generator's `TownDungeons` (town name -> level, each city's script sets its own) and `CurrentDungeonLevel()` (Vel Morrath's `CatacombsLevel` when it is not there) say whether the town she is in has one (`HasTownDungeon`); the gate's walk-in, the teleporter's glow and `EnterCatacombs` ask that. `-RDTownGo=dungeon:<town>` goes down into a town's dungeon from where she stands (the packaged game's test).
- **The landmark is the castle's part**: the foundry is the town's `CastleBld` and its gate the `MistgateAt` / `MistgateNormal`, so `GetTownPlace("mistgate" / "castle door")`, `ReturnAt` and the town's map's mark work unchanged.

## Building it

- **An editor capture of a line-up comes out white** (SceneCapture2D from Python, orthographic or not, base colour or not): the editor viewport's own `HighResShot` with `viewmode unlit`, the camera set by `set_level_viewport_camera_info`, a segment of the row a picture, shows them (the scratch probe `lineup.py`).
- **A kit's stone has several slots** (House Forge's walls: grout, rocks, wood): a piece's `Material` replaces them all, so a tint is a copy of one slot's instance (`MI_Forge_SootStone`, MI_Rocks' child) made by the script; another pack's material on the mesh (three Dwarven Citadel instances tried) hardly changed it. 0.34 of the base colour read black against the morning sky; 0.5 now (still dark where the walls are in the low sun's shadow: the light, as Vel Morrath's morning blue-grey).
- **A piece placed against a wall at the wall's line is inside the wall**: the cathedral's arch stands 30 cm behind the edge; the foundry's brick (its face 25 cm into the room) hid the gate there (ar1's picture). The gate stands 45 cm into the furnace hall.
- **A fire at a fraction of a kiln's height can sit over its mouth**: at 0.35 it was unseen; 0.15 and further out shows a small fire at the mouth.
- **A hall furnished only by its room kind reads bare at 14 m**: the casting hall's own forge lines (`OpenForgeBuild(..., false)`: no work there for the guild, the foundry is lost to them) and a rail with carts.

## The War Engine's machines

- **None of the game's 56 monsters is mechanical** (the survey of 2026-11-07); the machines are other packs' characters (`monsters.json`). The Stone Golem and Dystopia's mech have every clip on their own skeleton; the robots, cyborgs, mutants and the mechanic only idle and walk: their pack's UE4 mannequin skeleton is made compatible with the Fantasy Pack's (`add_compatible_skeleton`, saved) and they play its warrior's attacks, hits and deaths.
- **Python reaches no single node instance** (`get_single_node_instance` is not exposed): that a clip plays is measured by the bones moving against the actor over half a second (all eleven 1.9 to 55 cm in ad4); a kind whose skeleton cannot play its clips stands still in its rig's pose.
- **A kind's own look**: `FRDMonsterDef::Material` (every slot); the iron golem and colossus wear Junkyard's rusted gear metal (reads very dark in the hall's light).
- **Weights, not lists**: the castle's 56 kinds stay (other stages name them: ranged set-ups, the balance's kits); their weight in each tier is cut so the machines' weight is twice theirs together. `895` keeps itself idempotent: it drops the machines by name and works the castle's weights out from the machines' again.
- **Tier 1 in the plain pieces read as Mistward Castle's great hall** (banners, throne): tiers 1 and 2 are the Foundry theme; the saved start section still has the castle's furniture.
