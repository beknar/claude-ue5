"""Re-import only the soldier skeletal mesh (geometry/skin) onto the existing skeleton; clips, ABP and BPs stay as they are.
Re-assigns the three materials by slot name and reports bounds (should be upright: extent z ~95)."""
import unreal
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
SRC = r"E:\code\claude-ue5\claude_ue5\SourceArt\dystopia_soldier02\SK_Dystopia_Soldier_02.fbx"
D = "/Game/Soldier"
sk_path = next(p.split(".")[0] for p in eal.list_assets(D + "/Character", recursive=False)
               if isinstance(unreal.load_asset(p), unreal.SkeletalMesh))
sk_old = unreal.load_asset(sk_path); skel = sk_old.get_editor_property("skeleton")
print("target", sk_path, "skeleton", skel.get_path_name())
o = unreal.FbxImportUI()
o.set_editor_property("import_mesh", True); o.set_editor_property("import_as_skeletal", True)
o.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
o.set_editor_property("skeleton", skel)
o.set_editor_property("import_animations", False); o.set_editor_property("import_materials", False)
o.set_editor_property("import_textures", False); o.set_editor_property("create_physics_asset", False)
smd = o.get_editor_property("skeletal_mesh_import_data")
smd.set_editor_property("import_morph_targets", True)
smd.set_editor_property("normal_import_method", unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)
t = unreal.AssetImportTask(); t.filename = SRC; t.destination_path = D + "/Character"
t.destination_name = sk_path.split("/")[-1]; t.automated = True; t.replace_existing = True; t.save = True; t.options = o
at.import_asset_tasks([t])
print("imported", list(t.imported_object_paths))
sk = unreal.load_asset(sk_path)
mats = {k: unreal.load_asset(f"{D}/Materials/M_Soldier_{k}") for k in ("Body", "Details", "FireGun")}
slots = sk.get_editor_property("materials")
for i in range(len(slots)):
    sn = str(slots[i].get_editor_property("material_slot_name"))
    key = "FireGun" if "FireGun" in sn else ("Body" if "Body" in sn else "Details")
    slots[i].set_editor_property("material_interface", mats[key]); print("slot", sn, "->", key)
sk.set_editor_property("materials", slots)
eal.save_loaded_asset(sk)
b = sk.get_bounds(); print("bounds origin", b.origin, "extent", b.box_extent)
print("nanite", sk.get_editor_property("nanite_settings").get_editor_property("enabled"))
