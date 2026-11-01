# fantasy_castle_level

[README](../../README.md) · [Levels](../../README.md#levels) · [Documentation](../../README.md#documentation)

## What's in it

| Level | Character | What's in it |
|---|---|---|
| `fantasy_castle_level` | FF2 (`BP_FF2Character`, with a higher step and a steeper walkable slope for the pack's rock) | The Fantasy Castle Environment's map with the Medieval Lake Village streamed into its lake. The pack meshes collide with their real triangles instead of one convex hull each, so doorways, arches and the bridge can be walked. A stone stair links the castle's east terrace to the island bridge, and a road runs from the bridge down the island, over a wooden causeway and into the walled village. Three castle buildings had a doorway cut into their shell and got interiors (great hall, armory, barracks); the village's hollow houses were measured by flood fill and furnished by purpose (tavern, fisherman's house, farmhouse, weaver's cottage, smithy, barn, storehouse). Doors and chests open with **F**. No showcase video |

## Rebuild

**fantasy_castle_level** (`400`–`421`; packs: Fantasy Castle Environment, Medieval Lake Village, castle_level's furniture kit and door / container Blueprints):
1. `400_fcl_maps.py castle`, restart the editor, `400_fcl_maps.py lake`, restart.
2. `401_fcl_lake_strip.py` (the village copy loses its own sky, lights, backdrop and water), `402_fcl_assemble.py` (streams it into the castle's lake; game mode FF2), `403_fcl_collision.py` (triangle collision on the terrain and architecture meshes), `407_ff2_rugged_movement.py`.
3. `404_fcl_road.py` (A* over traced heights from the bridge to the village, the pack's road spline, a two-span causeway), `406_fcl_castle_link.py` (ramp, slab and stair from the terrace to the bridge), `405_fcl_player.py`.
4. Castle interiors: `410_fcl_castle_survey.py`, then `blender_numpy/fcl_castle_rooms.py` and `fcl_castle_open.py` (room frames and the doorway cut into each shell), `411_fcl_castle_open.py`, `412_fcl_materials.py`, `blender_numpy/fcl_leaf_pivot.py` and `414_fcl_door_leaves.py` (door leaves hinged at the origin), `415_fcl_castle_interiors.py`.
5. Village interiors: `420_fcl_village_survey.py`, `421_fcl_village_interiors.py` (rooms by flood fill, the static doors replaced by ones that open, furniture by purpose through `interior_lib.py`).
