"""AnimBP for an animated Tripo character (generalised 250_ff2_anim.py): Quinn -> <CH> retarget of the template unarmed AnimBP for
its state machine (jump / fall / land stay the template's, retargeted), then HER OWN clips swapped in: blendspace idle / walk / run
(grid intact; GroundSpeed remapped from her measured stance-foot speeds onto 300 / 600), Idle state = her Idle. Foot-IK rig off,
retargeted clips root-locked. Reports per-clip foot clearance (Tripo pins the hips, which can float the feet) and writes
SourceArt/jrpg_<ch>/speeds.txt.  Args: CH"""
import re, sys, unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary; APE = unreal.AnimPoseExtensions
CH = sys.argv[1] if len(sys.argv) > 1 else "Fem5"
D = "/Game/JRPG"; A = f"{D}/{CH}Anims"; LA = f"{D}/{CH}Locomotion"; R = D + "/Rigs"
src_mesh = unreal.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple")
tgt_mesh = unreal.load_asset(f"{D}/Character/SK_JRPG_{CH}")
src_rig = unreal.load_asset("/Game/Fig4/Locomotion/Rigs/IK_Quinn_Auto")
anim = lambda n: unreal.load_asset(f"{A}/AS_{CH}_{n}")
walk, run, idle = anim("Walk"), anim("Run"), anim("Idle")
o = unreal.AnimPoseEvaluationOptions()
FEET = ("ball_l", "ball_r", "foot_l", "foot_r")
def clip_stats(a):
    L = unreal.AnimationLibrary.get_sequence_length(a); n = 60; prev = None; sp = []; lows = []; mins = []
    for k in range(n + 1):
        p = APE.get_anim_pose_at_time(a, L * k / n, o)
        f = {b: APE.get_bone_pose(p, b, unreal.AnimPoseSpaces.WORLD).translation for b in FEET}
        mins.append(min(v.z for v in f.values()))
        if prev:
            lo = min(("ball_l", "ball_r"), key=lambda b: f[b].z); d = f[lo] - prev[lo]; sp.append((d.x ** 2 + d.y ** 2) ** 0.5 / (L / n))
        prev = f
    sp.sort(); r0 = APE.get_bone_pose(APE.get_anim_pose_at_time(a, 0.0, o), "root", unreal.AnimPoseSpaces.WORLD).translation
    r1 = APE.get_bone_pose(APE.get_anim_pose_at_time(a, L, o), "root", unreal.AnimPoseSpaces.WORLD).translation
    return sp[len(sp) // 2] if sp else 0.0, min(mins), max(mins), ((r1.x - r0.x) ** 2 + (r1.y - r0.y) ** 2) ** 0.5
ref = APE.get_reference_pose(tgt_mesh.get_editor_property("skeleton"))
rest_ball = APE.get_bone_pose(ref, "ball_l", unreal.AnimPoseSpaces.WORLD).translation.z
st = {}
for nm, a in (("Idle", idle), ("Walk", walk), ("Run", run)):
    s, lo, hi, rt = clip_stats(a); st[nm] = s
    print(f"{nm}: stance speed {s:.1f} cm/s | lowest foot bone z min {lo:.1f} max {hi:.1f} (rest ball {rest_ball:.1f}) | root travel {rt:.1f}")
WALK, RUN = st["Walk"], st["Run"]
open(r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_" + CH.lower() + r"\speeds.txt", "w").write(f"{WALK:.2f} {RUN:.2f}\n")
def make(cls, fac, name, folder):
    p = f"{folder}/{name}"
    if eal.does_asset_exist(p): eal.delete_asset(p)
    return at.create_asset(name, folder, cls, fac) or unreal.load_asset(p)
rig = make(unreal.IKRigDefinition, unreal.IKRigDefinitionFactory(), f"IK_JRPG_{CH}_Auto", R)
c = unreal.IKRigController.get_controller(rig); c.set_skeletal_mesh(tgt_mesh)
print("auto rig:", c.apply_auto_generated_retarget_definition(), "root", c.get_retarget_root())
try: c.apply_auto_fbik()
except Exception: pass
eal.save_loaded_asset(rig)
rtg = make(unreal.IKRetargeter, unreal.IKRetargetFactory(), f"RTG_Quinn_To_JRPG_{CH}", R)
rc = unreal.IKRetargeterController.get_controller(rtg)
rc.add_default_ops()
rc.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, rig)
rc.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, src_mesh); rc.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET, tgt_mesh)
rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.TARGET, rig)
rc.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
rm = rc.get_op_controller(rc.get_index_of_op_by_name("Root Motion"))
rm.set_source_root_bone("root"); rm.set_target_root_bone("root"); rm.set_target_pelvis_bone("pelvis")
try: rc.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
except Exception as e: print("align", e)
eal.save_loaded_asset(rtg)
inp = unreal.IKRetargetBatchOperationInputs()
inp.set_editor_property("assets_to_retarget", [eal.find_asset_data("/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed")])
inp.set_editor_property("source_mesh", src_mesh); inp.set_editor_property("target_mesh", tgt_mesh)
inp.set_editor_property("ik_retarget_asset", rtg); inp.set_editor_property("suffix", "_" + CH)
inp.set_editor_property("target_path", LA); inp.set_editor_property("include_referenced_assets", True)
inp.set_editor_property("overwrite_existing_files", True)
out = [str(r.package_name) for r in unreal.IKRetargetBatchOperation.run_batch_retarget(inp)]
print("retargeted", len(out))
for p in eal.list_assets(LA, recursive=False):
    a = unreal.load_asset(p.split(".")[0])
    if isinstance(a, unreal.AnimSequence): a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True)
    eal.save_asset(p.split(".")[0], True)
bs = unreal.load_asset(f"{LA}/BS_Idle_Walk_Run_{CH}")
smp = bs.get_editor_property("sample_data")
for i in range(len(smp)):
    y = float(smp[i].export_text().split("Y=")[1].split(",")[0])
    s = smp[i]; s.set_editor_property("animation", idle if y < 1 else (walk if y < 450 else run)); smp[i] = s
bs.set_editor_property("sample_data", smp); bs.modify(); eal.save_loaded_asset(bs, only_if_is_dirty=False)
print("BS", sorted({(x.export_text().split(f"AS_{CH}_")[1].split(".")[0], x.export_text().split("Y=")[1][:5]) for x in bs.get_editor_property("sample_data")}))
for a in (walk, run, idle): a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True); eal.save_loaded_asset(a)
abp = unreal.load_asset(f"{LA}/ABP_Unarmed_{CH}")
for g in T.list_graphs(abp):
    for n in T.find_nodes(g, ""):
        cn = n.get_class().get_name()
        if cn == "AnimGraphNode_SequencePlayer" and g.get_name() == "Idle":
            nd = n.get_editor_property("node")
            nd.import_text(re.sub(r'Sequence="[^"]*"', f"Sequence=\"/Script/Engine.AnimSequence'{idle.get_path_name()}'\"", nd.export_text())); n.set_editor_property("node", nd)
            print("idle state -> her Idle")
        if cn == "AnimGraphNode_ControlRig":
            nd = n.get_editor_property("node"); nd.import_text(re.sub(r"Alpha=[0-9.]+", "Alpha=0.000000", nd.export_text())); n.set_editor_property("node", nd)
            for p in T.get_node_infos([n])[0].input_pins:
                if str(p.name) == "Alpha": T.set_pin_value(p.pin_id, "0.0")
gs = {x.get_name(): x for x in T.list_graphs(abp)}
if "RemapSpeed" not in gs:
    fg = T.add_function_graph(abp, "RemapSpeed"); T.add_function_param(fg, "S", "float", True); T.add_function_param(fg, "Out", "float", False)
    unreal.BlueprintEditorLibrary.compile_blueprint(abp); gs = {x.get_name(): x for x in T.list_graphs(abp)}
k1, k2 = 300.0 / WALK, 300.0 / (RUN - WALK)
T.write_graph_dsl(gs["RemapSpeed"], f"""
(fn RemapSpeed (S)
  (return (select (< S {WALK:.3f}) (* S {k1:.6f}) (Math|Float|Min(Float) 600.0 (+ 300.0 (* (- S {WALK:.3f}) {k2:.6f}))))))""")
unreal.BlueprintEditorLibrary.compile_blueprint(abp)
eg = gs["EventGraph"]
def info(n): return T.get_node_infos([n])[0]
def pin(i, name, out):
    for p in (i.output_pins if out else i.input_pins):
        if str(p.name) == name: return p
    raise KeyError(name)
nodes = T.find_nodes(eg, "")
if not any("RemapSpeed" in str(info(n).type_id) for n in nodes):
    sg = [n for n in nodes if "SetGroundSpeed" in str(info(n).type_id)][0]; si = info(sg)
    ex, vi = pin(si, "execute", False), pin(si, "GroundSpeed", False)
    pe, pv = ex.get_editor_property("connected_pins")[0], vi.get_editor_property("connected_pins")[0]
    ids = [str(x) for x in T.find_node_types(eg, "RemapSpeed")]
    call = T.create_node(eg, "CallFunction|RemapSpeed" if "CallFunction|RemapSpeed" in ids else ids[0], unreal.IntPoint(400, 300)); ci = info(call)
    T.break_pins(pe, ex.pin_id); T.break_pins(pv, vi.pin_id)
    T.connect_pins(pe, pin(ci, "execute", False).pin_id); T.connect_pins(pin(ci, "then", True).pin_id, ex.pin_id)
    T.connect_pins(pv, pin(ci, "S", False).pin_id); T.connect_pins(pin(ci, "Out", True).pin_id, vi.pin_id)
print("ABP compile", unreal.BlueprintEditorLibrary.compile_blueprint(abp)); eal.save_loaded_asset(abp, only_if_is_dirty=False)
print(f"walk {WALK:.1f} / run {RUN:.1f} cm/s")
