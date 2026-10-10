"""Conform a new MetaHuman Character to fig4's scan (body + face), with 2D face landmarks
from a portrait rendered by a known camera. Based on Epic's example_conform_from_custom_mesh.py.
Args: target_mesh_path portrait_png out_folder asset_name"""
import sys, unreal

TARGET_MESH_PATH, PORTRAIT, OUT_DIR, NAME = sys.argv[1:5]
# Blender camera (0, -0.80, 1.575) m looking +Y  ==  UE (0, 80, 157.5) cm looking -Y
CAMERA_LOCATION = unreal.Vector(0.0, 80.0, 157.5)
CAMERA_ROTATION = unreal.Rotator(pitch=0.0, yaw=-90.0, roll=0.0)
CAMERA_FOV_DEG = 22.0

mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
asset_path = f"{OUT_DIR}/{NAME}"
if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
    old = unreal.load_asset(asset_path)
    unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(old)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in eas.get_all_level_actors():
        if "PreviewActor" in a.get_actor_label():
            eas.destroy_actor(a)
    del old
    unreal.EditorAssetLibrary.delete_asset(asset_path)

image_size, pixels = unreal.PromotedFrameUtils.get_promoted_frame_as_pixel_array_from_disk(PORTRAIT)
print("portrait", image_size.x, image_size.y)
result = mhs.track_face_landmarks_from_image(pixels, image_size.x, image_size.y)
if isinstance(result, tuple) and len(result) == 1:
    result = result[0]
curves = result if (result and hasattr(result, "items")) else None
if not curves:
    raise RuntimeError("no face landmarks detected")
print("landmark curves:", len(curves), sorted(curves.keys())[:12])

target = unreal.load_asset(TARGET_MESH_PATH)
verts, idx, *_ = mhs.get_mesh_data_for_conforming(target)
print(f"target {len(verts)} verts {len(idx)//3} tris")

character = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    asset_name=NAME, package_path=OUT_DIR, asset_class=unreal.MetaHumanCharacter,
    factory=unreal.new_object(type=unreal.MetaHumanCharacterFactoryNew))
if not mhs.try_add_object_to_edit(character):
    raise RuntimeError("cannot edit character")
ok = False
try:
    params = unreal.ConformTargetParams()
    params.conform_target_mesh.target_parts_type = unreal.TargetPartsType.COMBINED
    params.conform_target_mesh.body_vertices = verts
    params.conform_target_mesh.body_vertex_indices = idx
    params.estimate_body_joints_from_mesh = True
    params.auto_solve = True
    params.body_conform_solve_settings.pipeline_name = "combined"
    # optional overrides: argv[5] = "name=start[:end],..." for WeightSchedule fields / plain values
    if len(sys.argv) > 5 and sys.argv[5] and sys.argv[5] != "none":
        s = params.body_conform_solve_settings
        for kv in sys.argv[5].split(","):
            k, val = kv.split("=")
            cur = getattr(s, k)
            if isinstance(cur, unreal.WeightSchedule):
                a, _, b = val.partition(":")
                cur.start = float(a); cur.end = float(b or a); setattr(s, k, cur)
            elif isinstance(cur, bool):
                setattr(s, k, val.lower() in ("1", "true"))
            elif isinstance(cur, int):
                setattr(s, k, int(val))
            else:
                setattr(s, k, float(val))
        params.body_conform_solve_settings = s
        print("overrides:", sys.argv[5])
    vi = unreal.MinimalViewInfo()
    vi.location = CAMERA_LOCATION; vi.rotation = CAMERA_ROTATION; vi.fov = CAMERA_FOV_DEG
    vi.aspect_ratio = float(image_size.x) / float(image_size.y)
    vi.projection_mode = unreal.CameraProjectionMode.PERSPECTIVE
    params.curve_tracking_points = curves
    params.camera_view_info = vi
    params.image_size = image_size

    key = unreal.MetaHumanCharacterTargetMeshKey()
    key.combined_mesh = target
    print("conforming...")
    if not mhs.conform_to_target_meshes(character, key, params):
        raise RuntimeError("conform_to_target_meshes failed")
    dna = unreal.MetaHumanPosedDNAExportParams()
    dna.target_mesh_key = key; dna.project_path = OUT_DIR; dna.overwrite_existing_assets = True
    unreal.MetaHumanCharacterExportBlueprintLibrary.export_posed_dna(character, dna)
    mhs.commit_posed_state_as_a_pose(character, key)
    unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False)
    print("CONFORMED", asset_path)
    ok = True
finally:
    if mhs.is_object_added_for_editing(character):
        mhs.remove_object_to_edit(character)
    if not ok:
        unreal.EditorAssetLibrary.delete_asset(asset_path)
