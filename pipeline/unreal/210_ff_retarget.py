"""FF anime female: IK rig + Quinn->FF retargeter; batch-retarget the template unarmed AnimBP (BS idle/walk/jog, jump,
fall, land) plus the unarmed attacks and dash. Reports blendspace samples and the stance-foot speed of walk/jog
(-> character walk/run speeds that don't foot-slide)."""
import unreal
at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary; APE = unreal.AnimPoseExtensions
D = "/Game/FF"; LA = D + "/Locomotion"
src_mesh = unreal.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple")
tgt_mesh = unreal.load_asset(D + "/Character/SK_FF_Anime")
src_rig = unreal.load_asset("/Game/Fig4/Locomotion/Rigs/IK_Quinn_Auto")
for p in eal.list_assets(D + "/Character", recursive=False):           # FBX-embedded texture copies (real ones live in /Textures)
    if "/T_FF_" in p: eal.delete_asset(p.split(".")[0])
def make(cls, fac, name, folder):
    p = f"{folder}/{name}"
    if eal.does_asset_exist(p): eal.delete_asset(p)
    return at.create_asset(name, folder, cls, fac)
rig = make(unreal.IKRigDefinition, unreal.IKRigDefinitionFactory(), "IK_FF_Auto", LA + "/Rigs")
c = unreal.IKRigController.get_controller(rig); c.set_skeletal_mesh(tgt_mesh)
print("auto rig:", c.apply_auto_generated_retarget_definition(), "root", c.get_retarget_root())
try: c.apply_auto_fbik()
except Exception: pass
eal.save_loaded_asset(rig)
print("chains", [str(ch.chain_name) for ch in c.get_retarget_chains()])
rtg = make(unreal.IKRetargeter, unreal.IKRetargetFactory(), "RTG_Quinn_To_FF", LA + "/Rigs")
rc = unreal.IKRetargeterController.get_controller(rtg)
rc.add_default_ops()
rc.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, rig)
rc.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, src_mesh); rc.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET, tgt_mesh)
rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.TARGET, rig)
rc.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
# root motion goes source root -> target root (otherwise it is baked into the pelvis and the mesh runs off the capsule)
rm = rc.get_op_controller(rc.get_index_of_op_by_name("Root Motion"))
rm.set_source_root_bone("root"); rm.set_target_root_bone("root"); rm.set_target_pelvis_bone("pelvis")
print("root motion op:", rm.get_settings().export_text()[:160])
try: rc.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
except Exception as e: print("align", e)
eal.save_loaded_asset(rtg)
U = "/Game/Characters/Mannequins/Anims/Unarmed"
srcs = [U + "/ABP_Unarmed", U + "/Attack/MM_Attack_01", U + "/Attack/MM_Attack_02", U + "/Attack/MM_Attack_03",
        U + "/Attack/MM_ChargedAttack", U + "/Jump/MM_Dash"]
inp = unreal.IKRetargetBatchOperationInputs()
inp.set_editor_property("assets_to_retarget", [eal.find_asset_data(s) for s in srcs])
inp.set_editor_property("source_mesh", src_mesh); inp.set_editor_property("target_mesh", tgt_mesh)
inp.set_editor_property("ik_retarget_asset", rtg); inp.set_editor_property("suffix", "_FF")
inp.set_editor_property("target_path", LA + "/Anims"); inp.set_editor_property("include_referenced_assets", True)
inp.set_editor_property("overwrite_existing_files", True)
out = [str(r.package_name) for r in unreal.IKRetargetBatchOperation.run_batch_retarget(inp)]
print("retargeted", len(out), sorted(o.split("/")[-1] for o in out))
for p in eal.list_assets(LA + "/Anims", recursive=False): eal.save_asset(p.split(".")[0], True)
bs = next(unreal.load_asset(p) for p in eal.list_assets(LA + "/Anims", recursive=False) if "/BS_Idle_Walk_Run" in p)
print("BS", bs.get_path_name())
for s in bs.get_editor_property("sample_data"):
    t = s.export_text(); print("  sample", t.split("Animation=")[1].split(",")[0].split(".")[-1], "Y=" + t.split("Y=")[1].split(",")[0])
def stance_speed(a):
    L = unreal.AnimationLibrary.get_sequence_length(a); n = 60; o = unreal.AnimPoseEvaluationOptions()
    prev = None; sp = []
    for k in range(n + 1):
        p = APE.get_anim_pose_at_time(a, L * k / n, o)
        f = {b: APE.get_bone_pose(p, b, unreal.AnimPoseSpaces.WORLD).translation for b in ("ball_l", "ball_r")}
        if prev:
            lo = min(f, key=lambda b: f[b].z)
            d = f[lo] - prev[lo]; sp.append((d.x ** 2 + d.y ** 2) ** 0.5 / (L / n))
        prev = f
    sp.sort(); return sp[len(sp) // 2], L
for p in eal.list_assets(LA + "/Anims", recursive=False):
    a = unreal.load_asset(p)
    if isinstance(a, unreal.AnimSequence) and any(k in p for k in ("Walk_Fwd", "Jog_Fwd")):
        v, L = stance_speed(a); print("speed", a.get_name(), round(v, 1), "cm/s  len", round(L, 2))
