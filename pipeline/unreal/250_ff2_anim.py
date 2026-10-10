"""FF2 (animated Tripo anime female) AnimBP: Quinn->FF2 retarget of the template unarmed AnimBP for its state machine,
then her own clips swapped in: blendspace idle/walk/run (Idle, Walk 100 cm/s, Run 350 cm/s; grid intact, GroundSpeed
remapped onto 300/600), Idle state = Idle, Jump + Fall Loop states = her Jump (hips pinned hop; physics does the lift).
Foot-IK rig off, retargeted clips root-locked. Montages for Box, CastSpell, Shoot, Dance."""
import re, unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary
D = "/Game/FF2"; LA = D + "/Locomotion"; A = D + "/Anims"
src_mesh = unreal.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple")
tgt_mesh = unreal.load_asset(D + "/Character/SK_FF2_Anime")
src_rig = unreal.load_asset("/Game/Fig4/Locomotion/Rigs/IK_Quinn_Auto")
WALK, RUN = 102.3, 337.0       # locked stance speeds after 286_ff2_foot_fix
def make(cls, fac, name, folder):
    p = f"{folder}/{name}"
    if eal.does_asset_exist(p): eal.delete_asset(p)
    return at.create_asset(name, folder, cls, fac)
rig = make(unreal.IKRigDefinition, unreal.IKRigDefinitionFactory(), "IK_FF2_Auto", LA + "/Rigs")
c = unreal.IKRigController.get_controller(rig); c.set_skeletal_mesh(tgt_mesh)
print("auto rig:", c.apply_auto_generated_retarget_definition(), "root", c.get_retarget_root())
try: c.apply_auto_fbik()
except Exception: pass
eal.save_loaded_asset(rig)
rtg = make(unreal.IKRetargeter, unreal.IKRetargetFactory(), "RTG_Quinn_To_FF2", LA + "/Rigs")
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
inp.set_editor_property("ik_retarget_asset", rtg); inp.set_editor_property("suffix", "_FF2")
inp.set_editor_property("target_path", LA + "/Anims"); inp.set_editor_property("include_referenced_assets", True)
inp.set_editor_property("overwrite_existing_files", True)
out = [str(r.package_name) for r in unreal.IKRetargetBatchOperation.run_batch_retarget(inp)]
print("retargeted", len(out))
for p in eal.list_assets(LA + "/Anims", recursive=False):
    a = unreal.load_asset(p)
    if isinstance(a, unreal.AnimSequence):
        a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True)
    eal.save_asset(p.split(".")[0], True)
anim = lambda n: unreal.load_asset(f"{A}/AS_FF2_{n}")
walk, run, idle, jump = anim("Walk"), anim("Run"), anim("Idle"), anim("Jump")
bs = unreal.load_asset(f"{LA}/Anims/BS_Idle_Walk_Run_FF2")
smp = bs.get_editor_property("sample_data")
for i in range(len(smp)):
    y = float(smp[i].export_text().split("Y=")[1].split(",")[0])
    s = smp[i]; s.set_editor_property("animation", idle if y < 1 else (walk if y < 450 else run)); smp[i] = s
bs.set_editor_property("sample_data", smp); eal.save_loaded_asset(bs)
print("BS", sorted({(x.export_text().split("AS_FF2_")[1].split(".")[0], x.export_text().split("Y=")[1][:5]) for x in bs.get_editor_property("sample_data")}))
for a in (walk, run, idle, jump): a.set_editor_property("enable_root_motion", False); eal.save_loaded_asset(a)
abp = unreal.load_asset(f"{LA}/Anims/ABP_Unarmed_FF2")
for g in T.list_graphs(abp):
    for n in T.find_nodes(g, ""):
        cn = n.get_class().get_name()
        if cn == "AnimGraphNode_SequencePlayer":
            nd = n.get_editor_property("node"); txt = nd.export_text()
            cur = re.search(r'Sequence="[^"]*\.([A-Za-z0-9_]+)\'?"', txt)
            new = idle if g.get_name() == "Idle" else (jump if g.get_name() in ("Jump", "Fall Loop", "FallLoop") else None)
            print("seq player in", g.get_name(), "->", cur.group(1) if cur else txt[:80], "| set" if new else "")
            if new:
                nd.import_text(re.sub(r'Sequence="[^"]*"', f"Sequence=\"/Script/Engine.AnimSequence'{new.get_path_name()}'\"", txt))
                n.set_editor_property("node", nd)
        if cn == "AnimGraphNode_ControlRig":
            nd = n.get_editor_property("node"); nd.import_text(re.sub(r"Alpha=[0-9.]+", "Alpha=0.000000", nd.export_text())); n.set_editor_property("node", nd)
            for p in T.get_node_infos([n])[0].input_pins:
                if str(p.name) == "Alpha": T.set_pin_value(p.pin_id, "0.0")
gs = {x.get_name(): x for x in T.list_graphs(abp)}
print("graphs", sorted(gs))
if "RemapSpeed" not in gs:
    fg = T.add_function_graph(abp, "RemapSpeed"); T.add_function_param(fg, "S", "float", True); T.add_function_param(fg, "Out", "float", False)
    unreal.BlueprintEditorLibrary.compile_blueprint(abp); gs = {x.get_name(): x for x in T.list_graphs(abp)}
k1, k2 = 300.0 / WALK, 300.0 / (RUN - WALK)
T.write_graph_dsl(gs["RemapSpeed"], f"""
(fn RemapSpeed (S)
  (return (select (< S {WALK}) (* S {k1:.6f}) (Math|Float|Min(Float) 600.0 (+ 300.0 (* (- S {WALK}) {k2:.6f}))))))""")
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
    call = T.create_node(eg, "CallFunction|RemapSpeed", unreal.IntPoint(400, 300)); ci = info(call)
    T.break_pins(pe, ex.pin_id); T.break_pins(pv, vi.pin_id)
    T.connect_pins(pe, pin(ci, "execute", False).pin_id); T.connect_pins(pin(ci, "then", True).pin_id, ex.pin_id)
    T.connect_pins(pv, pin(ci, "S", False).pin_id); T.connect_pins(pin(ci, "Out", True).pin_id, vi.pin_id)
print("ABP compile", unreal.BlueprintEditorLibrary.compile_blueprint(abp)); eal.save_loaded_asset(abp)
for clip in ("Box", "CastSpell", "Shoot", "Dance"):
    p = f"{A}/AM_FF2_{clip}"
    if eal.does_asset_exist(p): eal.delete_asset(p)
    f = unreal.AnimMontageFactory(); f.set_editor_property("source_animation", anim(clip))
    m = at.create_asset(f"AM_FF2_{clip}", A, unreal.AnimMontage, f); eal.save_loaded_asset(m)
    print("montage", clip, round(m.get_play_length(), 2))
