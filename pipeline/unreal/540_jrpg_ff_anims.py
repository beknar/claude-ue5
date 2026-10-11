"""JRPG Fem1 with the animation set of the FF anime showcase (FF_Anime_Showcase.mp4): the UE5 template unarmed AnimBP (blendspace
idle / walk / jog, jump, fall, land) + MM_Attack_01/02/03, MM_ChargedAttack, MM_Dash, retargeted Quinn -> JRPG into
/Game/JRPG/FFSet (suffix _JRPGFF). Same fixes as the FF character (212/216): template foot-IK control rig off, GroundSpeed
remapped from her measured stride speeds onto the 300/600 grid, root locked on locomotion clips (attacks/dash keep root motion),
montages AM_JRPGFF_*. Speeds -> SourceArt/jrpg_fem1/speeds_ff.txt (read by 520 ff)."""
import re, sys, unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary; APE = unreal.AnimPoseExtensions
CH = sys.argv[1] if len(sys.argv) > 1 else "Fem1"           # Fem1 | Fem3
SFX = "_JRPGFF" if CH == "Fem1" else f"_JRPG{CH}FF"
D = "/Game/JRPG"; FS = D + ("/FFSet" if CH == "Fem1" else f"/FFSet_{CH}"); R = D + "/Rigs"
src_mesh = unreal.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple")
tgt_mesh = unreal.load_asset(D + f"/Character/SK_JRPG_{CH}")
src_rig = unreal.load_asset("/Game/Fig4/Locomotion/Rigs/IK_Quinn_Auto")
RIG = f"IK_JRPG_{CH}_Auto"
if CH == "Fem1": tgt_rig = unreal.load_asset(R + "/" + RIG)                   # from 510
else:
    if eal.does_asset_exist(R + "/" + RIG): eal.delete_asset(R + "/" + RIG)
    tgt_rig = at.create_asset(RIG, R, unreal.IKRigDefinition, unreal.IKRigDefinitionFactory())
    tgt_rig = tgt_rig or unreal.load_asset(R + "/" + RIG)
    ic = unreal.IKRigController.get_controller(tgt_rig); ic.set_skeletal_mesh(tgt_mesh)
    print("auto rig:", ic.apply_auto_generated_retarget_definition(), "root", ic.get_retarget_root(), [str(x.chain_name) for x in ic.get_retarget_chains()])
    try: ic.apply_auto_fbik()
    except Exception: pass
    eal.save_loaded_asset(tgt_rig)
p = R + f"/RTG_Quinn_To_JRPG_{CH}"
if eal.does_asset_exist(p): eal.delete_asset(p)
rtg = at.create_asset(f"RTG_Quinn_To_JRPG_{CH}", R, unreal.IKRetargeter, unreal.IKRetargetFactory()) or unreal.load_asset(p)   # (left in memory by an aborted run)
rc = unreal.IKRetargeterController.get_controller(rtg)
rc.add_default_ops()
rc.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
rc.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, src_mesh); rc.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET, tgt_mesh)
rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
rc.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
rm = rc.get_op_controller(rc.get_index_of_op_by_name("Root Motion"))
rm.set_source_root_bone("root"); rm.set_target_root_bone("root"); rm.set_target_pelvis_bone("pelvis")
try: rc.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
except Exception as e: print("align", e)
eal.save_loaded_asset(rtg)
U = "/Game/Characters/Mannequins/Anims/Unarmed"
srcs = [U + "/ABP_Unarmed", U + "/Attack/MM_Attack_01", U + "/Attack/MM_Attack_02", U + "/Attack/MM_Attack_03", U + "/Attack/MM_ChargedAttack", U + "/Jump/MM_Dash"]
inp = unreal.IKRetargetBatchOperationInputs()
inp.set_editor_property("assets_to_retarget", [eal.find_asset_data(s) for s in srcs])
inp.set_editor_property("source_mesh", src_mesh); inp.set_editor_property("target_mesh", tgt_mesh)
inp.set_editor_property("ik_retarget_asset", rtg); inp.set_editor_property("suffix", SFX)
inp.set_editor_property("target_path", FS); inp.set_editor_property("include_referenced_assets", True)
inp.set_editor_property("overwrite_existing_files", True)
out = [str(r.package_name) for r in unreal.IKRetargetBatchOperation.run_batch_retarget(inp)]
print("retargeted", len(out), sorted(o.split("/")[-1] for o in out))
for q in eal.list_assets(FS, recursive=True): eal.save_asset(q.split(".")[0], True)
find = lambda n: next((unreal.load_asset(q.split(".")[0]) for q in eal.list_assets(FS, recursive=True) if q.split("/")[-1].split(".")[0] == n), None)
# stride speeds from the root-motion travel of the retargeted loops (as for the FF: the clips carry root motion)
def root_speed(a):
    L = unreal.AnimationLibrary.get_sequence_length(a); o = unreal.AnimPoseEvaluationOptions()
    o.set_editor_property("extract_root_motion", False) if hasattr(o, "extract_root_motion") else None
    p0 = APE.get_bone_pose(APE.get_anim_pose_at_time(a, 0.0, o), "root", unreal.AnimPoseSpaces.WORLD).translation
    p1 = APE.get_bone_pose(APE.get_anim_pose_at_time(a, L, o), "root", unreal.AnimPoseSpaces.WORLD).translation
    return ((p1.x - p0.x) ** 2 + (p1.y - p0.y) ** 2) ** 0.5 / L
def stance_speed(a):
    L = unreal.AnimationLibrary.get_sequence_length(a); n = 60; o = unreal.AnimPoseEvaluationOptions(); prev = None; sp = []
    for k in range(n + 1):
        pp = APE.get_anim_pose_at_time(a, L * k / n, o)
        f = {b: APE.get_bone_pose(pp, b, unreal.AnimPoseSpaces.WORLD).translation for b in ("ball_l", "ball_r")}
        if prev:
            lo = min(f, key=lambda b: f[b].z); d = f[lo] - prev[lo]; sp.append((d.x ** 2 + d.y ** 2) ** 0.5 / (L / n))
        prev = f
    sp.sort(); return sp[len(sp) // 2]
walk, jog = find("MF_Unarmed_Walk_Fwd" + SFX), find("MF_Unarmed_Jog_Fwd" + SFX)
rw, rj = root_speed(walk), root_speed(jog)
sw, sj = stance_speed(walk), stance_speed(jog)
print(f"walk root {rw:.1f} stance {sw:.1f} | jog root {rj:.1f} stance {sj:.1f} cm/s")
W_, J_ = (rw, rj) if rw > 30 and rj > rw else (sw, sj)
open(r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_" + CH.lower() + r"\speeds_ff.txt", "w").write(f"{W_:.2f} {J_:.2f}\n")
# root lock on locomotion clips; attacks / dash keep root motion
KEEP = ("MM_Attack", "MM_ChargedAttack", "MM_Dash"); n = 0
for q in eal.list_assets(FS, recursive=True):
    a = unreal.load_asset(q.split(".")[0])
    if isinstance(a, unreal.AnimSequence) and not any(k in q for k in KEEP):
        a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True)
        a.set_editor_property("root_motion_root_lock", unreal.RootMotionRootLock.REF_POSE); eal.save_loaded_asset(a); n += 1
print("root-locked", n)
abp = find("ABP_Unarmed" + SFX); print("ABP", abp.get_path_name())
for g in T.list_graphs(abp):
    for nd_ in T.find_nodes(g, ""):
        if nd_.get_class().get_name() == "AnimGraphNode_ControlRig":
            nd = nd_.get_editor_property("node"); nd.import_text(re.sub(r"Alpha=[0-9.]+", "Alpha=0.000000", nd.export_text())); nd_.set_editor_property("node", nd)
            for pn in T.get_node_infos([nd_])[0].input_pins:
                if str(pn.name) == "Alpha": T.set_pin_value(pn.pin_id, "0.0")
gs = {x.get_name(): x for x in T.list_graphs(abp)}
if "RemapSpeed" not in gs:
    fg = T.add_function_graph(abp, "RemapSpeed"); T.add_function_param(fg, "S", "float", True); T.add_function_param(fg, "Out", "float", False)
    unreal.BlueprintEditorLibrary.compile_blueprint(abp); gs = {x.get_name(): x for x in T.list_graphs(abp)}
k1, k2 = 300.0 / W_, 300.0 / (J_ - W_)
T.write_graph_dsl(gs["RemapSpeed"], f"""
(fn RemapSpeed (S)
  (return (select (< S {W_:.3f}) (* S {k1:.6f}) (Math|Float|Min(Float) 600.0 (+ 300.0 (* (- S {W_:.3f}) {k2:.6f}))))))""")
unreal.BlueprintEditorLibrary.compile_blueprint(abp)
eg = gs["EventGraph"]
def info(x): return T.get_node_infos([x])[0]
def pin(i, name, o):
    for pn in (i.output_pins if o else i.input_pins):
        if str(pn.name) == name: return pn
    raise KeyError(name)
nodes = T.find_nodes(eg, "")
if not any("RemapSpeed" in str(info(x).type_id) for x in nodes):
    sg = [x for x in nodes if "SetGroundSpeed" in str(info(x).type_id)][0]; si = info(sg)
    ex, vi = pin(si, "execute", False), pin(si, "GroundSpeed", False)
    pe, pv = ex.get_editor_property("connected_pins")[0], vi.get_editor_property("connected_pins")[0]
    ids = [str(x) for x in T.find_node_types(eg, "RemapSpeed")]
    call = T.create_node(eg, "CallFunction|RemapSpeed" if "CallFunction|RemapSpeed" in ids else ids[0], unreal.IntPoint(400, 300)); ci = info(call)
    T.break_pins(pe, ex.pin_id); T.break_pins(pv, vi.pin_id)
    T.connect_pins(pe, pin(ci, "execute", False).pin_id); T.connect_pins(pin(ci, "then", True).pin_id, ex.pin_id)
    T.connect_pins(pv, pin(ci, "S", False).pin_id); T.connect_pins(pin(ci, "Out", True).pin_id, vi.pin_id)
print("ABP compile", unreal.BlueprintEditorLibrary.compile_blueprint(abp)); eal.save_loaded_asset(abp, only_if_is_dirty=False)
print("remap in graph:", any("Remap" in l for l in T.read_graph_dsl(eg).splitlines()))
for clip in ("MM_Attack_01", "MM_Attack_02", "MM_Attack_03", "MM_ChargedAttack", "MM_Dash"):
    seq = find(clip + SFX); name = "AM" + SFX + "_" + clip[3:]; q = f"{FS}/{name}"
    if eal.does_asset_exist(q): eal.delete_asset(q)
    f = unreal.AnimMontageFactory(); f.set_editor_property("source_animation", seq)
    m = at.create_asset(name, FS, unreal.AnimMontage, f); eal.save_loaded_asset(m)
    print("montage", name, round(m.get_play_length(), 2), "root motion", seq.get_editor_property("enable_root_motion"))
