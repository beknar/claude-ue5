"""Run clip with a more upright torso: heel retargeter + spine_01 tilted back in the target retarget pose.
Args: back_deg sign"""
import sys, math, unreal
BACK = float(sys.argv[1]) if len(sys.argv) > 1 else 13.0
SIGN = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
eal = unreal.EditorAssetLibrary; ML = unreal.MathLibrary
D = "/Game/Fig4/Locomotion"
fig_mesh = unreal.load_asset("/Game/MetaHumans/Fig4/Body/SKM_MHC_Fig4_Final_BodyMesh")
mh_mesh = unreal.load_asset("/MetaHumanCharacter/Body/IdentityTemplate/SKM_Body")
src = f"{D}/Rigs/RTG_MH_To_Fig4_Heels"; dst = f"{D}/Rigs/RTG_MH_To_Fig4_HeelsRun"
if eal.does_asset_exist(dst): eal.delete_asset(dst)
rtg = eal.duplicate_asset(src, dst)
rc = unreal.IKRetargeterController.get_controller(rtg)
rc.set_current_retarget_pose("Heels", unreal.RetargetSourceOrTarget.TARGET)
def quat_axis(axis, deg):
    h = math.radians(deg) / 2; s = math.sin(h)
    return unreal.Quat(axis[0] * s, axis[1] * s, axis[2] * s, math.cos(h))
ref = unreal.AnimPoseExtensions.get_reference_pose(fig_mesh.get_editor_property("skeleton"))
G = unreal.AnimPoseExtensions.get_bone_pose(ref, "spine_01", unreal.AnimPoseSpaces.WORLD).rotation
Q = quat_axis((1, 0, 0), SIGN * BACK)
rc.set_rotation_offset_for_retarget_pose_bone("spine_01", ML.multiply_quat_quat(ML.multiply_quat_quat(ML.quat_inversed(G), Q), G), unreal.RetargetSourceOrTarget.TARGET)
eal.save_loaded_asset(rtg)
inp = unreal.IKRetargetBatchOperationInputs()
inp.set_editor_property("assets_to_retarget", [eal.find_asset_data("/MetaHumanCharacter/Optional/Animation/UEFNAnimPreset/Locomotion/AS_MH_Neutral_Run_Loop_F")])
inp.set_editor_property("source_mesh", mh_mesh); inp.set_editor_property("target_mesh", fig_mesh)
inp.set_editor_property("ik_retarget_asset", rtg); inp.set_editor_property("prefix", "HR_")
inp.set_editor_property("target_path", f"{D}/Heels"); inp.set_editor_property("include_referenced_assets", False)
inp.set_editor_property("overwrite_existing_files", True)
out = [str(r.package_name) for r in unreal.IKRetargetBatchOperation.run_batch_retarget(inp)]
print(out)
a = unreal.load_asset(out[0])
a.set_editor_property("enable_root_motion", False); eal.save_loaded_asset(a)
APE = unreal.AnimPoseExtensions
L = unreal.AnimationLibrary.get_sequence_length(a); res = []
for i in range(6):
    p = APE.get_anim_pose_at_time(a, L * i / 6, unreal.AnimPoseEvaluationOptions())
    d = APE.get_bone_pose(p, "head", unreal.AnimPoseSpaces.WORLD).translation - APE.get_bone_pose(p, "pelvis", unreal.AnimPoseSpaces.WORLD).translation
    res.append(round(math.degrees(math.atan2(math.hypot(d.x, d.y), d.z))))
    if i == 0: print("head-pelvis", d)
print("HR lean", res)
