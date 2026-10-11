"""JRPG Fem1: IK rig (auto) + Soldier -> JRPG retargeter, then batch-retarget the Dystopia Soldier's whole animation set onto her:
the soldier locomotion AnimBP (ABP_Unarmed_Soldier: blendspace idle/walk/run, jump/fall/land, RemapSpeed) and every AS_Soldier_*
clip and AM_Soldier_* montage -> /Game/JRPG/Anims (suffix _JRPG). Her own Meshy clips were never imported.
Measures the stance-foot speed of the retargeted walk / run (her legs are shorter than the soldier's) and rewrites RemapSpeed."""
import unreal
at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary; APE = unreal.AnimPoseExtensions
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
D = "/Game/JRPG"; R = D + "/Rigs"; AN = D + "/Anims"
for p in eal.list_assets(D + "/Character", recursive=False):                  # FBX-created placeholder material
    if p.split("/")[-1].startswith("BakedMaterial"): eal.delete_asset(p.split(".")[0])
src_mesh = unreal.load_asset("/Game/Soldier/Character/SK_Dystopia_Soldier_02")
tgt_mesh = unreal.load_asset(D + "/Character/SK_JRPG_Fem1")
src_rig = unreal.load_asset("/Game/Soldier/Locomotion/Rigs/IK_Soldier_Auto")
def make(cls, fac, name, folder):
    p = f"{folder}/{name}"
    if eal.does_asset_exist(p): eal.delete_asset(p)
    return at.create_asset(name, folder, cls, fac)
rig = make(unreal.IKRigDefinition, unreal.IKRigDefinitionFactory(), "IK_JRPG_Fem1_Auto", R)
c = unreal.IKRigController.get_controller(rig); c.set_skeletal_mesh(tgt_mesh)
print("auto rig:", c.apply_auto_generated_retarget_definition(), "root", c.get_retarget_root())
try: c.apply_auto_fbik()
except Exception: pass
eal.save_loaded_asset(rig)
print("target chains", [str(ch.chain_name) for ch in c.get_retarget_chains()])
print("source chains", [str(ch.chain_name) for ch in unreal.IKRigController.get_controller(src_rig).get_retarget_chains()])
rtg = make(unreal.IKRetargeter, unreal.IKRetargetFactory(), "RTG_Soldier_To_JRPG_Fem1", R)
rc = unreal.IKRetargeterController.get_controller(rtg)
rc.add_default_ops()
rc.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, rig)
rc.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, src_mesh); rc.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET, tgt_mesh)
rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.TARGET, rig)
rc.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
rm = rc.get_op_controller(rc.get_index_of_op_by_name("Root Motion"))           # root motion root -> root (not baked into the pelvis)
rm.set_source_root_bone("root"); rm.set_target_root_bone("root"); rm.set_target_pelvis_bone("pelvis")
try: rc.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
except Exception as e: print("align", e)
eal.save_loaded_asset(rtg)
srcs = ["/Game/Soldier/Locomotion/Anims/ABP_Unarmed_Soldier"] + [p.split(".")[0] for p in eal.list_assets("/Game/Soldier/Anims", recursive=False)
                                                               if p.split("/")[-1].startswith(("AS_Soldier_", "AM_Soldier_"))]
inp = unreal.IKRetargetBatchOperationInputs()
inp.set_editor_property("assets_to_retarget", [eal.find_asset_data(s) for s in srcs])
inp.set_editor_property("source_mesh", src_mesh); inp.set_editor_property("target_mesh", tgt_mesh)
inp.set_editor_property("ik_retarget_asset", rtg); inp.set_editor_property("suffix", "_JRPG")
inp.set_editor_property("target_path", AN); inp.set_editor_property("include_referenced_assets", True)
inp.set_editor_property("overwrite_existing_files", True)
out = [str(r.package_name) for r in unreal.IKRetargetBatchOperation.run_batch_retarget(inp)]
print("retargeted", len(out), "from", len(srcs), "sources")
for p in eal.list_assets(AN, recursive=True): eal.save_asset(p.split(".")[0], True)
def stance_speed(a):
    L = unreal.AnimationLibrary.get_sequence_length(a); n = 60; o = unreal.AnimPoseEvaluationOptions(); prev = None; sp = []
    for k in range(n + 1):
        p = APE.get_anim_pose_at_time(a, L * k / n, o)
        f = {b: APE.get_bone_pose(p, b, unreal.AnimPoseSpaces.WORLD).translation for b in ("ball_l", "ball_r")}
        if prev:
            lo = min(f, key=lambda b: f[b].z); d = f[lo] - prev[lo]; sp.append((d.x ** 2 + d.y ** 2) ** 0.5 / (L / n))
        prev = f
    sp.sort(); return sp[len(sp) // 2]
find = lambda n: next((unreal.load_asset(p.split(".")[0]) for p in eal.list_assets(AN, recursive=True) if p.split("/")[-1].split(".")[0] == n), None)
walk, run = find("AS_Soldier_02_Walk_JRPG"), find("AS_Soldier_Run_Fast_JRPG")
sw, sr = stance_speed(walk), stance_speed(run)
print(f"stance speed walk {sw:.1f} cm/s, run {sr:.1f} cm/s  (soldier 90 / 410)")
open(r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_fem1\speeds.txt", "w").write(f"{sw:.2f} {sr:.2f}\n")
for a in (walk, run, find("AS_Soldier_Idle_01_JRPG")): a.set_editor_property("enable_root_motion", False); eal.save_loaded_asset(a)
abp = find("ABP_Unarmed_Soldier_JRPG"); print("ABP", abp.get_path_name() if abp else None)
gs = {x.get_name(): x for x in T.list_graphs(abp)}
k1, k2 = 300.0 / sw, 300.0 / (sr - sw)
T.write_graph_dsl(gs["RemapSpeed"], f"""
(fn RemapSpeed (S)
  (return (select (< S {sw:.3f}) (* S {k1:.6f}) (Math|Float|Min(Float) 600.0 (+ 300.0 (* (- S {sw:.3f}) {k2:.6f}))))))""")
print("ABP compile", unreal.BlueprintEditorLibrary.compile_blueprint(abp)); eal.save_loaded_asset(abp, only_if_is_dirty=False)
bs = next((unreal.load_asset(p.split(".")[0]) for p in eal.list_assets(AN, recursive=True) if "/BS_Idle_Walk_Run" in p), None)
if bs: print("BS", sorted({(s.export_text().split("Animation=")[1].split(",")[0].split(".")[-1].strip("'\""), s.export_text().split("Y=")[1][:5]) for s in bs.get_editor_property("sample_data")}))
print("montages", sorted(p.split("/")[-1].split(".")[0] for p in eal.list_assets(AN, recursive=True) if "/AM_" in p))
