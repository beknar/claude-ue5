# Kethrys Spire and its tower (`906`, `907`, `RD/RDMage.cpp`, the mage plan in `RD/RDTownPlan.cpp`; the user's list of 2026-11-08b, `docs/improvements9.txt`, its fourth phase; `docs/levels/kethrys_spire.md`)

The city is a wilderness town on `brokenspire` with the mage plan (`FRDWildTown::Plan` 4 -> the generator's `TownPlan`, `bMage`; `bMid` as the holy, forge and port cities: a landmark at the middle over a dungeon of its own); the tower's dungeon is `kethrys_spire`, a Save As copy of `mistward_castle` with its own `DungeonKey` ("kethrys"). Every rule is behind `TownPlan == 4`, the `Spire.*` / `Mage.*` pieces or a level's own data: the other towns and dungeons are unchanged.

## The city

- **Placed from Graymourne, then walked inland**: 45 km south and 70 km west of the port, then stepped inland until `Continent` is 0.08 or more (a point by a coast can be sea). Measured at (152.4, -70.0) km, 83 km from Graymourne; its road joins Graymourne's (`MakeRoad`), and `888 world` counts five roads.
- **The tower's height comes from its storeys**: Castle of Eternal Mist's round tower with windows (`SM_TowerRound_Window_8m_A`) at 2.2 times, stacked up to `SpireTowerTop` (5500 cm), then its crown and cap: 69.1 m to the top in play (`884 spire`). Its storeys have no floors: the tower is seen, its gatehouse and hall are walked.
- **Not a poor city**: the mage plan burns under 2 % of its homes and boards under 5 % (1 and 1 of 92 in `test_ks11.json`).
- **A library is a room kind, not a container**: the castle's library room kind furnishes it (tall cases, candle stands), so the libraries count no containers; the laboratories take the kitchen's kind (their containers) with a cauldron and a table of potions (`MageLabBuild`); a study is a smaller library room.
- **Build into a room after its furnishing, among its footprints** (PR #32's review): the laboratory's cauldron and table placed before the kitchen's furniture had barrels and crates set into them. Built in the per-building pass after the room (`FurnRoom` set: a piece that would stand in another is refused), each tried at a few places. The test counts each laboratory's own cauldron and potions inside its rectangle (`town_building_at`), not the town's: every kitchen has prep tables and the still is a cauldron.
- **What stands near a lane takes the lane's tiles into account**: a chamber's rune stones at fixed radii stood in the lane cross (190 cm) or found no room off it (240 and 320 cm in a five-tile room: 0 and 1 stones); they go on the four tiles nearest the middle off the room's lane row and column. Outdoor rune stones block their tiles, the square's circle is across the square from the quest board, and a main road's pylon goes only on ground clear of every building's way out.
- **`MaterialEditingLibrary.set_material_instance_scalar_parameter_value` returns False when the value is already there**: `907`'s first print said no parameter was taken while the copies held 0.32 and 0.45. Read the instance's `scalar_parameter_values` back.
- **An empty room is not a Junction**: the dungeon's Junction kind (no furniture) is a hallway to the lights (`LightRoom` skips it), the map and the doorways. A meditation chamber is a library room whose furnishing is its own (`Furnish`'s Library case: the room's building is `TK_Meditation`).
- **A tower's windows can be recesses**: lights orbiting inside the round storeys lit nothing seen from outside (the first night picture); at the windows' line just outside the wall the glow passes over the windows (`test_ks11.json`). The lights' pivots are turned by `URotatingMovementComponent`s, each tagged `SpireWindow` with its lights for the test (`get_components_by_tag`).

## The tower's dungeon

- **A copy of the castle reads as the castle**: in Mystic Dungeon's own cream stone and the castle's orange torchlight, the start hall looked like Mistward's great hall (the first run's picture). The kit's instances are copied darker and greyer (`Albedo Multiply (S)`, `Albedo Desaturate`: `MI_Arcane_*`), and the level's lights are tinted (`DungeonLightTint` / `DungeonLightTintShare`, read in `ARDSection::AddLight`, only when the generator is not a town: the town's lights are its own). Judge a theme in the first hall's picture: the saved start section still keeps the castle's great-hall furniture.
- **Clips found by name under a pack**: the casters' clips are Mystic Dungeon's (`clip_pack`), on its own mannequin; `907` makes the meshes' skeletons compatible with the clips', saved, as `895` and `897` do.
- **An idle barely moves**: the test's half-second bone measure read 0.5 to 5 cm for a caster in its idle and 20 to 100 cm walking (five runs): its 0.3 cm threshold tells a playing clip from a frozen pose, nothing more.

## The tests

- **`888` has `-Light` too** (2026-11-08b, as `884`'s): the editor on `rl_scratch`, play in a 1280 x 720 window of its own, the town opened from play. `world,towns` ran in it (`test_ks9.json`, `test_ks4.json`).
