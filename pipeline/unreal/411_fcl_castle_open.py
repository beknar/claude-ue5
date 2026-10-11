"""Import the doorway-cut castle buildings (blender_numpy/fcl_castle_rooms.py -> SourceArt/fantasy_castle/<mesh>_open.fbx) into
/Game/FantasyCastleLevel/Meshes, give them the original meshes' materials (matched by slot name, else slot index) and
triangle collision, and swap them onto the castle actors listed in castle_rooms.json (only buildings with a usable room)."""
import json, os, sys, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\fantasy_castle"; D = "/Game/FantasyCastleLevel/Meshes"
GEO = json.load(open(os.path.join(SA, "castle_rooms_geo.json"))); ROOMS = json.load(open(os.path.join(SA, "castle_rooms.json")))
use = {m: g for m, g in GEO.items() if (g["room"][1] - g["room"][0]) > 300 and (g["room"][3] - g["room"][2]) > 300}
tasks = []
for m in use:
    t = unreal.AssetImportTask(); t.filename = os.path.join(SA, m + "_open.fbx"); t.destination_path = D; t.automated = True; t.replace_existing = True; t.save = True
    o = unreal.FbxImportUI(); o.import_mesh = True; o.import_materials = False; o.import_textures = False; o.import_as_skeletal = False
    o.static_mesh_import_data.combine_meshes = True; o.static_mesh_import_data.generate_lightmap_u_vs = False; o.static_mesh_import_data.auto_generate_collision = False
    t.options = o; tasks.append(t)
if "swaponly" not in sys.argv: unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
del tasks
for m in use:
    new = unreal.load_asset(f"{D}/{m}_open"); old = unreal.load_asset(f"/Game/FantasyCastle/Mesh/{m}")
    om = {str(s.material_slot_name): s.material_interface for s in old.static_materials}
    mats = []
    for i, s in enumerate(new.static_materials):
        mi = om.get(str(s.material_slot_name)) or (old.static_materials[min(i, len(old.static_materials) - 1)].material_interface)
        mats.append(unreal.StaticMaterial(material_interface=mi, material_slot_name=s.material_slot_name))
    new.set_editor_property("static_materials", mats)
    bs = new.get_editor_property("body_setup"); bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    new.modify(); eal.save_loaded_asset(new, only_if_is_dirty=False)
    label = next(k for k, v in ROOMS.items() if v["mesh"] == m)
    a = next(x for x in eas.get_all_level_actors() if x.get_actor_label() == label)
    a.static_mesh_component.set_static_mesh(new)
    print(label, "->", new.get_name(), "slots", [str(s.material_slot_name) for s in new.static_materials], "skipped" if False else "")
print("not used (no room):", [m for m in GEO if m not in use])
new = old = a = mats = om = None
import gc; gc.collect()
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True); print("saved")
