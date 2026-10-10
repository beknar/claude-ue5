"""Soldier locomotion: IK rig + Quinn->Soldier retarget of the template AnimBP (jump/fall/land 1:1 on his UE4-mannequin
skeleton), blendspace samples swapped in place (grid intact): idle Idle_01, walk 02_Walk (90 cm/s), run Run_Fast (410 cm/s);
GroundSpeed remapped onto the 300/600 grid; foot-IK rig off; idle state Idle_01; montages for idles and actions."""
import re, unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary
D = "/Game/Soldier"; LA = D + "/Locomotion"; A = D + "/Anims"
src_mesh = unreal.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple")
tgt_mesh = unreal.load_asset(D + "/Character/SK_Dystopia_Soldier_02")
src_rig = unreal.load_asset("/Game/Fig4/Locomotion/Rigs/IK_Quinn_Auto")
WALK, RUN, IDLE = 90.0, 410.0, "Idle_01"
def make(cls, fac, name, folder):
    p = f"{folder}/{name}"
    if eal.does_asset_exist(p): eal.delete_asset(p)
    return at.create_asset(name, folder, cls, fac)
rig = make(unreal.IKRigDefinition, unreal.IKRigDefinitionFactory(), "IK_Soldier_Auto", LA + "/Rigs")
c = unreal.IKRigController.get_controller(rig); c.set_skeletal_mesh(tgt_mesh)
print("auto rig:", c.apply_auto_generated_retarget_definition(), "root", c.get_retarget_root())
try: c.apply_auto_fbik()
except Exception: pass
eal.save_loaded_asset(rig)
rtg = make(unreal.IKRetargeter, unreal.IKRetargetFactory(), "RTG_Quinn_To_Soldier", LA + "/Rigs")
rc = unreal.IKRetargeterController.get_controller(rtg)
rc.add_default_ops()
rc.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, rig)
rc.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, src_mesh); rc.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET, tgt_mesh)
rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.TARGET, rig)
rc.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
try: rc.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
except Exception as e: print("align", e)
eal.save_loaded_asset(rtg)
inp = unreal.IKRetargetBatchOperationInputs()
inp.set_editor_property("assets_to_retarget", [eal.find_asset_data("/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed")])
inp.set_editor_property("source_mesh", src_mesh); inp.set_editor_property("target_mesh", tgt_mesh)
inp.set_editor_property("ik_retarget_asset", rtg); inp.set_editor_property("suffix", "_Soldier")
inp.set_editor_property("target_path", LA + "/Anims"); inp.set_editor_property("include_referenced_assets", True)
inp.set_editor_property("overwrite_existing_files", True)
out = [str(r.package_name) for r in unreal.IKRetargetBatchOperation.run_batch_retarget(inp)]
print("retargeted", len(out), [o.split("/")[-1] for o in out][:6])
abp_path = next((p for p in [f"{LA}/Anims/ABP_Unarmed_Soldier", f"{LA}/Anims/ABP_Unarmed_Soldier1"] if eal.does_asset_exist(p)), None)
print("ABP", abp_path)
anim = lambda n: unreal.load_asset(f"{A}/AS_Soldier_{n}")
walk, run, idle = anim("02_Walk"), anim("Run_Fast"), anim(IDLE)
# blendspace: in-place swap (sample order/positions untouched -> runtime grid stays valid)
bs = unreal.load_asset(f"{LA}/Anims/BS_Idle_Walk_Run_Soldier")
smp = bs.get_editor_property("sample_data")
for i in range(len(smp)):
    y = float(smp[i].export_text().split("Y=")[1].split(",")[0])
    s = smp[i]; s.set_editor_property("animation", idle if y < 1 else (walk if y < 450 else run)); smp[i] = s
bs.set_editor_property("sample_data", smp); eal.save_loaded_asset(bs)
print("BS", sorted({(x.export_text().split("AS_Soldier_")[1].split(".")[0], x.export_text().split("Y=")[1][:5]) for x in bs.get_editor_property("sample_data")}))
for a in (walk, run, idle): a.set_editor_property("enable_root_motion", False); eal.save_loaded_asset(a)
abp = unreal.load_asset(abp_path)
for g in T.list_graphs(abp):
    for n in T.find_nodes(g, ""):
        cn = n.get_class().get_name()
        if cn == "AnimGraphNode_SequencePlayer" and g.get_name() == "Idle":
            nd = n.get_editor_property("node")
            nd.import_text(re.sub(r'Sequence="[^"]*"', f"Sequence=\"/Script/Engine.AnimSequence'{idle.get_path_name()}'\"", nd.export_text()))
            n.set_editor_property("node", nd)
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
    call = T.create_node(eg, [str(x) for x in T.find_node_types(eg, "RemapSpeed")][0], unreal.IntPoint(400, 300)); ci = info(call)
    T.break_pins(pe, ex.pin_id); T.break_pins(pv, vi.pin_id)
    T.connect_pins(pe, pin(ci, "execute", False).pin_id); T.connect_pins(pin(ci, "then", True).pin_id, ex.pin_id)
    T.connect_pins(pv, pin(ci, "S", False).pin_id); T.connect_pins(pin(ci, "Out", True).pin_id, vi.pin_id)
print("ABP compile", unreal.BlueprintEditorLibrary.compile_blueprint(abp)); eal.save_loaded_asset(abp)
for p in eal.list_assets(LA + "/Anims", recursive=False): eal.save_asset(p.split(".")[0], True)
for clip in ("Idle_02", "Idle_03", "02_Reload", "02_Shot", "Attack_01", "Attack_02", "Get_Hit"):
    p = f"{A}/AM_Soldier_{clip}"
    if not eal.does_asset_exist(p):
        f = unreal.AnimMontageFactory(); f.set_editor_property("source_animation", anim(clip))
        m = at.create_asset(f"AM_Soldier_{clip}", A, unreal.AnimMontage, f); eal.save_loaded_asset(m)
    print("montage", clip, round(unreal.load_asset(p).get_play_length(), 2))
