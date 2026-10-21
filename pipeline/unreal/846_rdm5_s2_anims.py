"""random_dungeonmagic_level5, Summoner2, step 5: her animations on her MetaHuman body (SKM_MHC_Summoner2_BodyMesh,
MetaHuman's body skeleton: the UE5 mannequin's bones and more), by Unreal's IK retargeter (auto IK rigs, fuzzy chain map):
  - walking, running, standing, jumping: the template's unarmed AnimBP (ABP_Unarmed: its blendspace of idle / walk / run,
    the jump, the fall, the landing, its DefaultSlot for the casts) from the UE5 mannequin (Quinn), as fig4's locomotion
    (31): MetaHuman's body is that skeleton with more bones, and the clips are motion capture, realistic as her body is
    -> /Game/JRPG/MetaHuman/Summoner2/Locomotion/ABP_Unarmed_S2 and its clips (root locked);
  - casting, flinching, dying: the Summoner's (the Mage's three casts, her flinch and her death as 832 / summoner_clips.py
    made them on her rig with the mannequin's bone names) -> /Game/JRPG/MetaHuman/Summoner2/Anims/AS_S2_Cast1..3,
    AS_S2_Flinch, AS_S2_Death (root locked);
  - each cast's release (where her right hand moves fastest, as 833 measures) -> SourceArt/random_dungeon_magic5/
    spell_s2.json (the Mage's fire as 833 wrote it, with these clips);
  - her walk and run speeds: how fast the root travels in the retargeted walk and jog (motion capture with root motion)
    -> SourceArt/summoner2/speeds.txt, and the AnimBP's RemapSpeed (as 610) puts them on its blendspace's grid (300 / 600);
    a check that each clip keeps her feet on the floor (lowest foot bone over the clip).
Args: none"""
import json, os, re, unreal
at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary; APE = unreal.AnimPoseExtensions
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
D = "/Game/JRPG/MetaHuman/Summoner2"; R = D + "/Rigs"; LOC = D + "/Locomotion"; AN = D + "/Anims"
tgt_mesh = unreal.load_asset(f"{D}/Body/SKM_MHC_Summoner2_BodyMesh"); assert tgt_mesh, "run 844"
quinn = unreal.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple"); quinn_rig = unreal.load_asset("/Game/Fig4/Locomotion/Rigs/IK_Quinn_Auto")
summ = unreal.load_asset("/Game/JRPG/Character/SK_JRPG_Summoner"); summ_rig = unreal.load_asset("/Game/JRPG/Rigs/IK_JRPG_Summoner_Auto")
assert quinn and quinn_rig and summ and summ_rig, "Quinn's IK rig (31) and the Summoner's (610) first"
def make(cls, fac, name, folder):
    p = f"{folder}/{name}"
    if eal.does_asset_exist(p): eal.delete_asset(p)
    return at.create_asset(name, folder, cls, fac) or unreal.load_asset(p)
rig = make(unreal.IKRigDefinition, unreal.IKRigDefinitionFactory(), "IK_S2_Body_Auto", R)
c = unreal.IKRigController.get_controller(rig); c.set_skeletal_mesh(tgt_mesh)
print("S2ANIM auto rig:", c.apply_auto_generated_retarget_definition(), "root", c.get_retarget_root(), "chains", len(c.get_retarget_chains()))
try: c.apply_auto_fbik()
except Exception: pass
eal.save_loaded_asset(rig)
def retargeter(name, src_rig, src_mesh):
    rtg = make(unreal.IKRetargeter, unreal.IKRetargetFactory(), name, R)
    rc = unreal.IKRetargeterController.get_controller(rtg); rc.add_default_ops()
    rc.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, rig)
    rc.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, src_mesh); rc.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET, tgt_mesh)
    rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.TARGET, rig)
    rc.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
    rm = rc.get_op_controller(rc.get_index_of_op_by_name("Root Motion"))
    rm.set_source_root_bone("root"); rm.set_target_root_bone("root"); rm.set_target_pelvis_bone("pelvis")
    try: rc.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
    except Exception as e: print("align", e)
    eal.save_loaded_asset(rtg); return rtg
def batch(assets, src_mesh, rtg, folder, suffix):
    inp = unreal.IKRetargetBatchOperationInputs()
    inp.set_editor_property("assets_to_retarget", [eal.find_asset_data(a) for a in assets])
    inp.set_editor_property("source_mesh", src_mesh); inp.set_editor_property("target_mesh", tgt_mesh)
    inp.set_editor_property("ik_retarget_asset", rtg); inp.set_editor_property("suffix", suffix)
    inp.set_editor_property("target_path", folder); inp.set_editor_property("include_referenced_assets", True)
    inp.set_editor_property("overwrite_existing_files", True)
    return [str(r.package_name) for r in unreal.IKRetargetBatchOperation.run_batch_retarget(inp)]
def lock(folder):
    for p in eal.list_assets(folder, recursive=False):
        a = unreal.load_asset(p.split(".")[0])
        if isinstance(a, unreal.AnimSequence):
            a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True); eal.save_asset(p.split(".")[0], True)
# ---- (a re-run starts from empty folders: the batch retarget would otherwise add ABP_Unarmed_S3, _S4 ... beside the old
#      ones; 847 must run again after this, its characters point at the AnimBP made here)
for folder in (LOC, AN):
    if eal.does_directory_exist(folder): eal.delete_directory(folder)
# ---- locomotion: Quinn's
out = batch(["/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed"], quinn, retargeter("RTG_Quinn_To_S2", quinn_rig, quinn), LOC, "_S2")
lock(LOC); print("S2ANIM locomotion", len(out), "assets ->", LOC)
# ---- casts, flinch, death: the Summoner's
CL = {"Cast1": "AS_Summoner_Cast1", "Cast2": "AS_Summoner_Cast2", "Cast3": "AS_Summoner_Cast3", "Flinch": "AS_Summoner_Flinch", "Death": "AS_Summoner_Death"}
out = batch([f"/Game/JRPG/SummonerAnims/{v}" for v in CL.values()], summ, retargeter("RTG_Summoner_To_S2", summ_rig, summ), AN, "_S2")
for k, v in CL.items():                                                    # AS_Summoner_Cast1_S2 -> AS_S2_Cast1
    src = f"{AN}/{v}_S2"; dst = f"{AN}/AS_S2_{k}"
    if eal.does_asset_exist(dst): eal.delete_asset(dst)
    assert eal.rename_asset(src, dst), src
lock(AN); print("S2ANIM actions", [f"AS_S2_{k}" for k in CL])
# ---- measurements
o = unreal.AnimPoseEvaluationOptions()
FEET = ("ball_l", "ball_r", "foot_l", "foot_r")
ref = APE.get_reference_pose(tgt_mesh.get_editor_property("skeleton"))
rest_ball = APE.get_bone_pose(ref, "ball_l", unreal.AnimPoseSpaces.WORLD).translation.z
def stats(a):
    L = unreal.AnimationLibrary.get_sequence_length(a); n = 60; prev = None; sp = []; lows = []
    for k in range(n + 1):
        p = APE.get_anim_pose_at_time(a, L * k / n, o)
        f = {b: APE.get_bone_pose(p, b, unreal.AnimPoseSpaces.WORLD).translation for b in FEET}
        lows.append(min(v.z for v in f.values()))
        if prev:
            lo = min(("ball_l", "ball_r"), key=lambda b: f[b].z); d = f[lo] - prev[lo]; sp.append((d.x ** 2 + d.y ** 2) ** 0.5 / (L / n))
        prev = f
    sp.sort()
    # (motion capture with root motion: the root travels, the planted foot stays; the speed is the root's)
    r0 = APE.get_bone_pose(APE.get_anim_pose_at_time(a, 0.0, o), "root", unreal.AnimPoseSpaces.WORLD).translation
    r1 = APE.get_bone_pose(APE.get_anim_pose_at_time(a, L, o), "root", unreal.AnimPoseSpaces.WORLD).translation
    rs = ((r1.x - r0.x) ** 2 + (r1.y - r0.y) ** 2) ** 0.5 / L
    return max(rs, sp[len(sp) // 2] if sp else 0.0), min(lows), max(lows), L
bs = unreal.load_asset(f"{LOC}/BS_Idle_Walk_Run_S2"); clips = {}
for s in bs.get_editor_property("sample_data"):
    t = s.export_text(); y = float(t.split("Y=")[1].split(",")[0]); x = float(t.split("X=")[1].split(",")[0]); a = s.get_editor_property("animation")
    if abs(x) < 1e-3: clips[round(y)] = a                                  # (straight ahead: direction 0)
print("S2ANIM blendspace samples", {k: v.get_name() for k, v in sorted(clips.items())})
ys = sorted(k for k in clips if k > 0)
walk_a, run_a = clips[ys[0]], clips[ys[-1]]
W, wl, wh, _ = stats(walk_a); Rn, rl, rh, _ = stats(run_a)
print(f"S2ANIM walk {walk_a.get_name()}: stance {W:.1f} cm/s (blendspace {ys[0]}), feet z {wl:.1f}..{wh:.1f} | run {run_a.get_name()}: {Rn:.1f} cm/s (blendspace {ys[-1]}), feet {rl:.1f}..{rh:.1f} | rest ball {rest_ball:.1f}")
os.makedirs(SA + r"\summoner2", exist_ok=True)
open(SA + r"\summoner2\speeds.txt", "w").write(f"{W:.2f} {Rn:.2f}\n")
# her speeds onto the blendspace's grid (610's RemapSpeed): walking at W plays the walk at its own pace, running at Rn the jog
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
abp = unreal.load_asset(f"{LOC}/ABP_Unarmed_S2")
gs = {x.get_name(): x for x in T.list_graphs(abp)}
if "RemapSpeed" not in gs:
    fg = T.add_function_graph(abp, "RemapSpeed"); T.add_function_param(fg, "S", "float", True); T.add_function_param(fg, "Out", "float", False)
    unreal.BlueprintEditorLibrary.compile_blueprint(abp); gs = {x.get_name(): x for x in T.list_graphs(abp)}
BW, BR = float(ys[0]), float(ys[-1]); k1, k2 = BW / W, (BR - BW) / (Rn - W)
T.write_graph_dsl(gs["RemapSpeed"], f"""
(fn RemapSpeed (S)
  (return (select (< S {W:.3f}) (* S {k1:.6f}) (Math|Float|Min(Float) {BR:.1f} (+ {BW:.1f} (* (- S {W:.3f}) {k2:.6f}))))))""")
unreal.BlueprintEditorLibrary.compile_blueprint(abp)
eg = gs["EventGraph"]
def info(n): return T.get_node_infos([n])[0]
def pin(i, name, out):
    for p_ in (i.output_pins if out else i.input_pins):
        if str(p_.name) == name: return p_
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
print("S2ANIM ABP compile", unreal.BlueprintEditorLibrary.compile_blueprint(abp), "| speeds walk", round(W, 1), "run", round(Rn, 1), "-> blendspace", BW, BR)
eal.save_loaded_asset(abp, only_if_is_dirty=False)
for k in CL:
    a = unreal.load_asset(f"{AN}/AS_S2_{k}"); _, lo, hi, L = stats(a)
    print(f"S2ANIM {k}: {L:.2f} s, lowest foot bone z {lo:.1f}..{hi:.1f}")
# ---- the spell with her clips: each cast's release where the right hand moves fastest (833's measure)
V = unreal.Vector
def release(anim):
    L_ = unreal.AnimationLibrary.get_sequence_length(anim); n = max(30, int(L_ * 60)); pts = []
    for k in range(n + 1):
        p = APE.get_anim_pose_at_time(anim, L_ * k / n, o)
        h = APE.get_bone_pose(p, "hand_r", unreal.AnimPoseSpaces.WORLD).translation; q = APE.get_bone_pose(p, "pelvis", unreal.AnimPoseSpaces.WORLD).translation
        pts.append(V(h.x - q.x, h.y - q.y, h.z - q.z))
    sp = [(pts[k + 1] - pts[k]).length() / (L_ / n) for k in range(n)]
    sm = [sum(sp[max(0, k - 2):k + 3]) / len(sp[max(0, k - 2):k + 3]) for k in range(n)]
    k = max(range(n), key=lambda i: sm[i]); return L_, L_ * (k + 0.5) / n, sm[k]
S1 = json.load(open(SA + r"\random_dungeon_magic5\spell.json"))
casts = []
for i, n in enumerate(("Cast1", "Cast2", "Cast3")):
    p = f"{AN}/AS_S2_{n}"; L_, hit, speed = release(unreal.load_asset(p))
    casts.append({"clip": p, "length": round(L_, 3), "hit": round(hit, 3), "end": round(min(L_, hit + 0.42), 3), "hand_speed": round(speed)})
res = dict({k: v for k, v in S1.items() if k not in ("casts", "flinch", "death")}, casts=casts, flinch=f"{AN}/AS_S2_Flinch", death=f"{AN}/AS_S2_Death")
json.dump(res, open(SA + r"\random_dungeon_magic5\spell_s2.json", "w"), indent=1)
print("S2ANIM casts: " + ", ".join(f"{c['clip'].split('_')[-1]} bolt at {c['hit']:.2f} s (the Summoner's {s['hit']:.2f})" for c, s in zip(casts, S1["casts"])))
