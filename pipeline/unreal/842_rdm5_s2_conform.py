"""random_dungeonmagic_level5, Summoner2 (ai models/Summoner2.glb), step 1: a MetaHuman fitted to her. Her model is
realistic (a Tripo model made from two photos), so unlike the first Summoner's anime head MetaHuman's conform can follow it.
Run blender_numpy/summoner2_prep.py first (SourceArt/summoner2: the conform target s2_target.glb, her skin and bikini
without the hair, the skull filled; the portrait s2_portrait.png from a known camera, classes.json).
- imports the target as a static mesh (/Game/JRPG/MetaHuman/Summoner2/Source/s2_target)
- tracks her face's landmarks on the portrait (MetaHuman's face contour tracker)
- MHC_Summoner2 (/Game/JRPG/MetaHuman): a new MetaHuman Character conformed to the target, head and body together
  (target parts COMBINED, the body's joints estimated from the mesh: she stands in a T-pose), with the landmarks and the
  portrait's camera as the face term; the posed state (her T-pose) kept as its A-pose and the posed DNA exported
  (/Game/JRPG/MetaHuman/Summoner2/Posed, and SourceArt/summoner2/dna/MHC_Summoner2_Posed.dna: the fitted body in her
  own pose, for the outfit: 845)
- prints the body's measurements (the parametric body's constraints) and the face landmarks' spread
Args: [overrides: name=start[:end],... for the body conform's solve settings, as fig4's 02, or none] [asset name: tries]"""
import sys, json, unreal
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\summoner2"
INFO = json.load(open(SA + r"\classes.json"))
D = "/Game/JRPG/MetaHuman"; SRC = D + "/Summoner2/Source"
NAME = sys.argv[2] if len(sys.argv) > 2 else "MHC_Summoner2"; path = f"{D}/{NAME}"
eal = unreal.EditorAssetLibrary
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if "PreviewActor" in a.get_actor_label(): eas.destroy_actor(a)
# ---- the target
t = unreal.AssetImportTask(); t.filename = SA + r"\s2_target.glb"; t.destination_path = SRC
t.automated = True; t.replace_existing = True; t.save = True
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
target = next(unreal.load_asset(p) for p in t.imported_object_paths if isinstance(unreal.load_asset(p), unreal.StaticMesh))
bb = target.get_bounding_box()
print("S2CONFORM target", target.get_path_name(), "| box", [round(v, 1) for v in (bb.min.x, bb.min.y, bb.min.z)], [round(v, 1) for v in (bb.max.x, bb.max.y, bb.max.z)])
# ---- the landmarks
P = INFO["portrait"]
size, pixels = unreal.PromotedFrameUtils.get_promoted_frame_as_pixel_array_from_disk(SA + r"\s2_portrait.png")
res = mhs.track_face_landmarks_from_image(pixels, size.x, size.y)
if isinstance(res, tuple) and len(res) == 1: res = res[0]
curves = res if (res and hasattr(res, "items")) else None
assert curves, "no face landmarks found on the portrait"
print("S2CONFORM landmark curves", len(curves))
# ---- the character
if eal.does_asset_exist(path):
    old = unreal.load_asset(path)
    if mhs.is_object_added_for_editing(old): mhs.remove_object_to_edit(old)
    unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(old); del old
    assert eal.delete_asset(path), "could not delete the old " + path
verts, idx, *_ = mhs.get_mesh_data_for_conforming(target)
print(f"S2CONFORM target {len(verts)} vertices, {len(idx) // 3} triangles")
ch = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, D, unreal.MetaHumanCharacter, unreal.new_object(type=unreal.MetaHumanCharacterFactoryNew))
assert mhs.try_add_object_to_edit(ch), "cannot edit " + path
ok = False
try:
    p = unreal.ConformTargetParams()
    p.conform_target_mesh.target_parts_type = unreal.TargetPartsType.COMBINED
    p.conform_target_mesh.body_vertices = verts; p.conform_target_mesh.body_vertex_indices = idx
    p.estimate_body_joints_from_mesh = True; p.auto_solve = True
    p.body_conform_solve_settings.pipeline_name = "combined"
    if len(sys.argv) > 1 and sys.argv[1] not in ("", "none"):
        s = p.body_conform_solve_settings
        for kv in sys.argv[1].split(","):
            k, val = kv.split("="); cur = getattr(s, k)
            if isinstance(cur, unreal.WeightSchedule):
                a, _, b = val.partition(":"); cur.start = float(a); cur.end = float(b or a); setattr(s, k, cur)
            elif isinstance(cur, bool): setattr(s, k, val.lower() in ("1", "true"))
            elif isinstance(cur, int): setattr(s, k, int(val))
            else: setattr(s, k, float(val))
        p.body_conform_solve_settings = s; p.auto_solve = False             # (auto_solve picks its own settings)
        print("S2CONFORM overrides", sys.argv[1])
    vi = unreal.MinimalViewInfo()
    vi.location = unreal.Vector(*P["ue_cam_cm"]); vi.rotation = unreal.Rotator(pitch=0.0, yaw=P["ue_yaw"], roll=0.0)
    vi.fov = P["hfov"]; vi.aspect_ratio = float(size.x) / float(size.y); vi.projection_mode = unreal.CameraProjectionMode.PERSPECTIVE
    p.curve_tracking_points = curves; p.camera_view_info = vi; p.image_size = size
    key = unreal.MetaHumanCharacterTargetMeshKey(); key.combined_mesh = target
    if not mhs.conform_to_target_meshes(ch, key, p): raise RuntimeError("conform_to_target_meshes failed")
    dna = unreal.MetaHumanPosedDNAExportParams()
    dna.target_mesh_key = key; dna.project_path = D + "/Summoner2/Posed"; dna.overwrite_existing_assets = True
    dna.external_path = SA + r"\dna"; dna.asset_name = NAME + "_Posed"            # (the .dna on disk: 845 reads the posed body)
    import os; os.makedirs(SA + r"\dna", exist_ok=True)
    try: unreal.MetaHumanCharacterExportBlueprintLibrary.export_posed_dna(ch, dna)
    except Exception as e: print("S2CONFORM posed DNA export (non-fatal):", str(e)[:200])
    mhs.commit_posed_state_as_a_pose(ch, key)
    cons = mhs.get_body_constraints(ch)
    print("S2CONFORM body", {str(c.name): round(c.target_measurement, 1) for c in cons})
    lm = mhs.get_face_landmarks(ch)
    if lm: print("S2CONFORM face landmarks", len(lm), "| z", round(min(v.z for v in lm), 1), "-", round(max(v.z for v in lm), 1))
    eal.save_loaded_asset(ch, only_if_is_dirty=False)
    print("S2CONFORM CONFORMED", path); ok = True
finally:
    if mhs.is_object_added_for_editing(ch): mhs.remove_object_to_edit(ch)
    if not ok: eal.delete_asset(path)
for a in eal.list_assets(D + "/Summoner2/Posed", recursive=True): print("S2CONFORM posed:", a)
