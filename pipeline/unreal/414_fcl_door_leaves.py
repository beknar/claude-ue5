"""Import the re-pivoted Lake Village door leaves (blender_numpy/fcl_leaf_pivot.py: hinge at the origin, leaf along +X) into
/Game/FantasyCastleLevel/Meshes as SM_M_Door0X_Leaf with the original doors' materials (BP_Door leaves for both the castle
and the lake village interiors)."""
import os, unreal
eal = unreal.EditorAssetLibrary
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\fantasy_castle"; D = "/Game/FantasyCastleLevel/Meshes"
tasks = []
for n in ("SM_M_Door01", "SM_M_Door02", "SM_M_Door03"):
    t = unreal.AssetImportTask(); t.filename = os.path.join(SA, n + "_Leaf.fbx"); t.destination_path = D; t.automated = True; t.replace_existing = True; t.save = True
    o = unreal.FbxImportUI(); o.import_mesh = True; o.import_materials = False; o.import_textures = False; o.import_as_skeletal = False
    o.static_mesh_import_data.combine_meshes = True; o.static_mesh_import_data.auto_generate_collision = True
    t.options = o; tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
for n in ("SM_M_Door01", "SM_M_Door02", "SM_M_Door03"):
    new = unreal.load_asset(f"{D}/{n}_Leaf"); old = unreal.load_asset(f"/Game/Medieval_Lake_Village/Meshs/HouseModule/{n}")
    om = {str(s.material_slot_name): s.material_interface for s in old.static_materials}
    new.set_editor_property("static_materials", [unreal.StaticMaterial(material_interface=om.get(str(s.material_slot_name)) or old.static_materials[min(i, len(old.static_materials) - 1)].material_interface,
                                                                       material_slot_name=s.material_slot_name) for i, s in enumerate(new.static_materials)])
    new.modify(); eal.save_loaded_asset(new, only_if_is_dirty=False)
    b = new.get_bounding_box(); print(n + "_Leaf", "min", [round(v) for v in (b.min.x, b.min.y, b.min.z)], "max", [round(v) for v in (b.max.x, b.max.y, b.max.z)])
