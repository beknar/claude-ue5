"""Refresh the existing AS_Soldier_* clips in place from the rebuilt FBX (keeps every reference intact):
import into a temp folder, copy each bone track (local transforms, frame by frame) into the existing sequence, delete temp."""
import os, unreal
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); APE = unreal.AnimPoseExtensions
SRC = r"E:\code\claude-ue5\claude_ue5\SourceArt\dystopia_soldier02\SK_Dystopia_Soldier_02.fbx"
TMP = "/Game/Soldier/_ImportTmp"
t = unreal.AssetImportTask(); t.filename = SRC; t.destination_path = TMP; t.automated = True; t.replace_existing = True; t.save = False
at.import_asset_tasks([t])
fresh = {}
for p in t.imported_object_paths:
    a = unreal.load_asset(p)
    if isinstance(a, unreal.AnimSequence): fresh[a.get_name().split("A_", 1)[-1]] = a
print("fresh clips", len(fresh))
done = []
for clip, src in sorted(fresh.items()):
    dst_path = f"/Game/Soldier/Anims/AS_Soldier_{clip}"
    if not eal.does_asset_exist(dst_path): print("no target for", clip); continue
    dst = unreal.load_asset(dst_path)
    n = unreal.AnimationLibrary.get_num_frames(src); L = unreal.AnimationLibrary.get_sequence_length(src)
    bones = [str(b) for b in unreal.AnimationLibrary.get_animation_track_names(dst)]
    pos = {b: [] for b in bones}; rot = {b: [] for b in bones}; scl = {b: [] for b in bones}
    opts = unreal.AnimPoseEvaluationOptions()
    for k in range(n + 1):
        pose = APE.get_anim_pose_at_time(src, min(L, k * L / max(n, 1)), opts)
        for b in bones:
            tr = APE.get_bone_pose(pose, b, unreal.AnimPoseSpaces.LOCAL)
            pos[b].append(tr.translation); rot[b].append(tr.rotation); scl[b].append(tr.scale3d)
    ctrl = dst.get_editor_property("controller")
    ctrl.open_bracket("refresh", False)
    bad = [b for b in bones if not ctrl.set_bone_track_keys(b, pos[b], rot[b], scl[b], False)]
    ctrl.close_bracket(False)
    eal.save_loaded_asset(dst); done.append(clip)
    if bad: print(clip, "failed bones", bad[:5])
print("refreshed", len(done))
for p in eal.list_assets(TMP, recursive=True): eal.delete_asset(p.split(".")[0])
eal.delete_directory(TMP)
a = unreal.load_asset("/Game/Soldier/Anims/AS_Soldier_02_Walk"); L = unreal.AnimationLibrary.get_sequence_length(a)
for tt in (0.0, L / 3, 2 * L / 3):
    p = APE.get_anim_pose_at_time(a, tt, unreal.AnimPoseEvaluationOptions())
    f = APE.get_bone_pose(p, "foot_l", unreal.AnimPoseSpaces.WORLD).translation; h = APE.get_bone_pose(p, "head", unreal.AnimPoseSpaces.WORLD).translation
    print(f"02_Walk t={tt:.2f} foot_l=({f.x:.0f},{f.y:.0f},{f.z:.0f}) head=({h.x:.0f},{h.y:.0f},{h.z:.0f})")
