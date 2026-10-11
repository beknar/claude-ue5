"""fcl_lake_village (the Lake Village copy, a sub-level of fantasy_castle_level): remove what the castle map already provides or
what would clash once the village sits in the castle's lake - sun / sky light / atmosphere / clouds / height fog / post process /
local fog, the backdrop mountains, cine cameras and the village's own water planes (the castle lake, raised to the same level by
402's +3423 cm offset, replaces them). Args: [dry]"""
import sys, re, collections, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert "fcl_lake_village" in w.get_path_name(), w.get_path_name()
DRY = "dry" in sys.argv
ENV = {"DirectionalLight", "SkyLight", "AtmosphericFog", "SkyAtmosphere", "VolumetricCloud", "ExponentialHeightFog", "PostProcessVolume",
       "LocalFogVolume", "CineCameraActor"}
BACKDROP = {"SM_Mount2", "SM_DistantMesh"}
WATER = re.compile(r"MI_LaterWater")                     # lake / pond / river surfaces (not the river rocks, bushes, well cylinders)
gone = collections.Counter(); water = []
for a in eas.get_all_level_actors():
    cn = a.get_class().get_name(); why = None
    if cn in ENV: why = cn
    elif isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh:
        sm = a.static_mesh_component.static_mesh.get_name()
        mats = " ".join(m.get_name() for m in a.static_mesh_component.get_materials() if m)
        if sm in BACKDROP: why = sm
        elif WATER.search(mats) and max(a.get_actor_bounds(False)[1].x, a.get_actor_bounds(False)[1].y) > 1000:
            why = "water:" + sm; o, e = a.get_actor_bounds(False); water.append((sm, round(o.z), [round(e.x), round(e.y)]))
    if why:
        gone[why] += 1
        if not DRY: eas.destroy_actor(a)
print("dry run" if DRY else "removed", dict(gone)); print("water planes", water)
if not DRY: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level(); print("saved")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
