"""Restore FF2 clips (args: clip names) from A_FF2_Clips.fbx: import into a temp folder on the FF2 skeleton, copy every
bone track (local, per frame) into the existing AS_FF2_<clip> (references stay intact), delete the temp import."""
import sys, unreal
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); APE = unreal.AnimPoseExtensions
CLIPS = sys.argv[1:]
TMP = "/Game/FF2/_Restore"
skel = unreal.load_asset("/Game/FF2/Character/SK_FF2_Anime").get_editor_property("skeleton")
o = unreal.FbxImportUI()
o.set_editor_property("import_mesh", False); o.set_editor_property("import_as_skeletal", True)
o.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
o.set_editor_property("skeleton", skel); o.set_editor_property("import_animations", True)
o.set_editor_property("import_materials", False); o.set_editor_property("import_textures", False)
t = unreal.AssetImportTask(); t.filename = r"E:\code\claude-ue5\claude_ue5\SourceArt\ff2_anime\A_FF2_Clips.fbx"
t.destination_path = TMP; t.automated = True; t.replace_existing = True; t.save = False; t.options = o
at.import_asset_tasks([t])
fresh = {p.split(".")[-1].split("Armature_A_")[-1]: unreal.load_asset(p) for p in t.imported_object_paths}
opts = unreal.AnimPoseEvaluationOptions()
for clip in CLIPS:
    src = fresh[clip]; dst = unreal.load_asset(f"/Game/FF2/Anims/AS_FF2_{clip}")
    n = unreal.AnimationLibrary.get_num_frames(src); L = unreal.AnimationLibrary.get_sequence_length(src)
    bones = [str(b) for b in unreal.AnimationLibrary.get_animation_track_names(dst)]
    pos = {b: [] for b in bones}; rot = {b: [] for b in bones}; scl = {b: [] for b in bones}
    for k in range(n + 1):
        p = APE.get_anim_pose_at_time(src, min(L, k * L / max(n, 1)), opts)
        for b in bones:
            tr = APE.get_bone_pose(p, b, unreal.AnimPoseSpaces.LOCAL); pos[b].append(tr.translation); rot[b].append(tr.rotation); scl[b].append(tr.scale3d)
    ctrl = dst.get_editor_property("controller"); ctrl.open_bracket("restore", False)
    bad = [b for b in bones if not ctrl.set_bone_track_keys(b, pos[b], rot[b], scl[b], False)]
    ctrl.close_bracket(False); eal.save_loaded_asset(dst)
    print("restored", clip, "frames", n, "bad", bad[:3])
for p in eal.list_assets(TMP, recursive=True): eal.delete_asset(p.split(".")[0])
eal.delete_directory(TMP)
