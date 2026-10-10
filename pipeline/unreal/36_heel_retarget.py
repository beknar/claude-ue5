"""Heel-stance retargeters (FK only) whose target retarget pose lifts the pelvis 7.6 cm and pitches
the feet 33 deg toes-down with toes flattened, then retarget the locomotion clips through them.
Args: foot_pitch_deg toe_sign(+1/-1)"""
import sys, math, unreal
PITCH = float(sys.argv[1]) if len(sys.argv) > 1 else 33.0
SIGN = float(sys.argv[2]) if len(sys.argv) > 2 else -1.0      # rotation about +X (lateral): negative = toes down
LIFT = 7.6
at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary
D = "/Game/Fig4/Locomotion"
fig_mesh = unreal.load_asset("/Game/MetaHumans/Fig4/Body/SKM_MHC_Fig4_Final_BodyMesh")
mh_mesh = unreal.load_asset("/MetaHumanCharacter/Body/IdentityTemplate/SKM_Body")
tgt_rig = unreal.load_asset(f"{D}/Rigs/IK_Fig4_Auto")

def ik_rig(name, mesh):
    path = f"{D}/Rigs/{name}"
    if eal.does_asset_exist(path): return unreal.load_asset(path)
    rig = at.create_asset(name, f"{D}/Rigs", unreal.IKRigDefinition, unreal.IKRigDefinitionFactory())
    c = unreal.IKRigController.get_controller(rig); c.set_skeletal_mesh(mesh); c.apply_auto_generated_retarget_definition()
    eal.save_loaded_asset(rig); return rig

def quat_axis(axis, deg):
    h = math.radians(deg) / 2; s = math.sin(h)
    return unreal.Quat(axis[0] * s, axis[1] * s, axis[2] * s, math.cos(h))

skel = fig_mesh.get_editor_property("skeleton")
ref = unreal.AnimPoseExtensions.get_reference_pose(skel)
def gq(b): return unreal.AnimPoseExtensions.get_bone_pose(ref, b, unreal.AnimPoseSpaces.WORLD).rotation
ML = unreal.MathLibrary
def qmul(a, b): return ML.multiply_quat_quat(a, b)
def local_delta(G, Q):            # local post-multiplied offset equivalent to a global pre-rotation Q
    return qmul(qmul(ML.quat_inversed(G), Q), G)

def heel_retargeter(name, src_rig, src_mesh):
    path = f"{D}/Rigs/{name}"
    if eal.does_asset_exist(path): eal.delete_asset(path)
    rtg = at.create_asset(name, f"{D}/Rigs", unreal.IKRetargeter, unreal.IKRetargetFactory())
    rc = unreal.IKRetargeterController.get_controller(rtg)
    rc.add_default_ops()
    rc.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
    rc.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, src_mesh); rc.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET, fig_mesh)
    rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
    i = rc.get_index_of_op_by_name("Run IK Rig")
    if i >= 0: rc.remove_retarget_op(i)                      # FK only: copy the mocap rotations faithfully
    rc.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
    pose = rc.create_retarget_pose("Heels", unreal.RetargetSourceOrTarget.TARGET)
    rc.set_current_retarget_pose(pose, unreal.RetargetSourceOrTarget.TARGET)
    Q = quat_axis((1, 0, 0), SIGN * PITCH)
    Qback = quat_axis((1, 0, 0), -SIGN * PITCH)
    for side in ("l", "r"):
        Gf = gq(f"foot_{side}"); Gb = gq(f"ball_{side}")
        rc.set_rotation_offset_for_retarget_pose_bone(f"foot_{side}", local_delta(Gf, Q), unreal.RetargetSourceOrTarget.TARGET)
        Gb2 = qmul(Q, Gb)                                     # ball after the foot rotates
        rc.set_rotation_offset_for_retarget_pose_bone(f"ball_{side}", local_delta(Gb2, Qback), unreal.RetargetSourceOrTarget.TARGET)
    rc.set_root_offset_in_retarget_pose(unreal.Vector(0, 0, LIFT), unreal.RetargetSourceOrTarget.TARGET)
    eal.save_loaded_asset(rtg)
    return rtg

mh_rig = ik_rig("IK_MHBody_Auto", mh_mesh)
rtg_mh = heel_retargeter("RTG_MH_To_Fig4_Heels", mh_rig, mh_mesh)
rtg_self = heel_retargeter("RTG_Fig4_To_Fig4_Heels", tgt_rig, fig_mesh)

def batch(assets, rtg, src_mesh):
    inp = unreal.IKRetargetBatchOperationInputs()
    inp.set_editor_property("assets_to_retarget", [eal.find_asset_data(a) for a in assets])
    inp.set_editor_property("source_mesh", src_mesh); inp.set_editor_property("target_mesh", fig_mesh)
    inp.set_editor_property("ik_retarget_asset", rtg); inp.set_editor_property("prefix", "H_")
    inp.set_editor_property("target_path", f"{D}/Heels"); inp.set_editor_property("include_referenced_assets", False)
    inp.set_editor_property("overwrite_existing_files", True)
    return [str(r.package_name) for r in unreal.IKRetargetBatchOperation.run_batch_retarget(inp)]

L = "/MetaHumanCharacter/Optional/Animation/UEFNAnimPreset/Locomotion/"
print(batch([L + "AS_MH_Neutral_Stand_Idle_Loop", L + "AS_MH_Neutral_Walk_Loop_F", L + "AS_MH_Neutral_Run_Loop_F"], rtg_mh, mh_mesh))
A = "/Game/Fig4/Locomotion/Anims/"
others = [A + n for n in ("MM_Jump_Fig4", "MM_Fall_Loop_Fig4", "MM_Land_Fig4")]
others += [A + a.split(".")[-1] for a in eal.list_assets(A, recursive=False) if a.split(".")[-1].startswith("MF_Unarmed_") and "_Fwd_Fig4" not in a.split(".")[-1].replace("_Fwd_Left", "").replace("_Fwd_Right", "")]
print(batch(others, rtg_self, fig_mesh))

# check the stance on the heel idle
a = unreal.load_asset(f"{D}/Heels/H_AS_MH_Neutral_Stand_Idle_Loop")
p = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, 0.0, unreal.AnimPoseEvaluationOptions())
for b in ("pelvis", "foot_l", "ball_l"):
    print(b, unreal.AnimPoseExtensions.get_bone_pose(p, b, unreal.AnimPoseSpaces.WORLD).translation)
