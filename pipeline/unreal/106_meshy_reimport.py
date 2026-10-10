"""Reimport the rebuilt Meshy FBX; consolidate the fresh clips onto the existing AS_Meshy_* (keeps montage/BS/ABP refs);
re-apply the Substrate material + Nanite; re-flag root motion."""
import os, unreal
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
SRC = r"E:\code\claude-ue5\claude_ue5\SourceArt\meshy_biped"
C = "/Game/Meshy/Character"; A = "/Game/Meshy/Anims"
ROOT_MOTION = {"Idle_Turn_Left", "Idle_Turn_Right", "Step_Step_Turn_Kick", "Leg_Sweep", "walking_2"}
t = unreal.AssetImportTask(); t.filename = os.path.join(SRC, "SK_Meshy_Biped.fbx"); t.destination_path = C
t.automated = True; t.replace_existing = True; t.save = True
at.import_asset_tasks([t])
fresh = {}
for p in t.imported_object_paths:
    a = unreal.load_asset(p)
    if isinstance(a, unreal.AnimSequence):
        fresh[a.get_name().replace("SK_Meshy_BipedArmature_A_", "")] = a
print("fresh clips", len(fresh))
for clip, new in fresh.items():
    old_path = f"{A}/AS_Meshy_{clip}"
    if eal.does_asset_exist(old_path):
        old = unreal.load_asset(old_path)
        eal.consolidate_assets(new, [old])            # references -> new; old deleted
    new_path = new.get_path_name().split(".")[0]
    eal.rename_asset(new_path, old_path)
    a = unreal.load_asset(old_path)
    a.set_editor_property("enable_root_motion", clip in ROOT_MOTION)
    eal.save_loaded_asset(a)
sk = unreal.load_asset(C + "/SK_Meshy_Biped")
mats = sk.get_editor_property("materials"); m = unreal.load_asset("/Game/Meshy/Materials/M_Meshy_Substrate")
for i in range(len(mats)): mats[i].set_editor_property("material_interface", m)
sk.set_editor_property("materials", mats)
ns = sk.get_editor_property("nanite_settings"); ns.set_editor_property("enabled", True); sk.set_editor_property("nanite_settings", ns)
eal.save_loaded_asset(sk)
# verify root motion on the turns
APE = unreal.AnimPoseExtensions
for clip in ("Idle_Turn_Left", "Idle_Turn_Right", "Step_Step_Turn_Kick", "walking_2"):
    a = unreal.load_asset(f"{A}/AS_Meshy_{clip}"); a.set_editor_property("enable_root_motion", False)
    L = unreal.AnimationLibrary.get_sequence_length(a)
    r = APE.get_bone_pose(APE.get_anim_pose_at_time(a, L, unreal.AnimPoseEvaluationOptions()), "root", unreal.AnimPoseSpaces.WORLD)
    a.set_editor_property("enable_root_motion", True)
    print(clip, "root end", round(r.translation.x), round(r.translation.y), "yaw", round(r.rotation.rotator().yaw, 1))
for p in eal.list_assets(A, recursive=False):
    if "AM_Meshy_" in p: print("montage ok", p.split(".")[-1], unreal.load_asset(p.split(".")[0]).get_play_length() > 0)
