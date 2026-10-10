"""Locomotion blendspace with an intact grid: fresh retarget of the template BS (walk 300 / jog 600 grid),
animations swapped in place (same sample order and positions); AnimBP remaps ground speed 140->300, 430->600."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary
LA = "/Game/Meshy/Locomotion/Anims"
src_mesh = unreal.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple")
tgt_mesh = unreal.load_asset("/Game/Meshy/Character/SK_Meshy_Biped")
rtg = unreal.load_asset("/Game/Meshy/Locomotion/Rigs/RTG_Quinn_To_Meshy")
inp = unreal.IKRetargetBatchOperationInputs()
inp.set_editor_property("assets_to_retarget", [eal.find_asset_data("/Game/Characters/Mannequins/Anims/Unarmed/BS_Idle_Walk_Run")])
inp.set_editor_property("source_mesh", src_mesh); inp.set_editor_property("target_mesh", tgt_mesh)
inp.set_editor_property("ik_retarget_asset", rtg); inp.set_editor_property("suffix", "_MeshyLoco")
inp.set_editor_property("target_path", LA); inp.set_editor_property("include_referenced_assets", False)
inp.set_editor_property("overwrite_existing_files", True)
out = [str(r.package_name) for r in unreal.IKRetargetBatchOperation.run_batch_retarget(inp)]
print("retargeted", out)
bs_path = [p for p in out if "BS_" in p][0]
bs = unreal.load_asset(bs_path)
A = lambda c: unreal.load_asset(f"/Game/Meshy/Anims/AS_Meshy_{c}")
walk, run, idle = A("Walking"), A("Running"), A("Idle_3")
samples = bs.get_editor_property("sample_data")
for i in range(len(samples)):
    s = samples[i]
    t = s.export_text()
    y = float(t.split("Y=")[1].split(",")[0])
    clip = idle if y < 1 else (walk if y < 450 else run)
    s.set_editor_property("animation", clip)
    samples[i] = s
bs.set_editor_property("sample_data", samples)
eal.save_loaded_asset(bs)
print("samples", [(s.export_text().split("AS_Meshy_")[1].split(".")[0], s.export_text().split("Y=")[1][:5]) for s in bs.get_editor_property("sample_data")][::4])

abp = unreal.load_asset(f"{LA}/ABP_Unarmed_Meshy1")
for g in T.list_graphs(abp):
    for n in T.find_nodes(g, ""):
        if n.get_class().get_name() == "AnimGraphNode_BlendSpacePlayer":
            nd = n.get_editor_property("node"); t = nd.export_text()
            import re
            t = re.sub(r'BlendSpace="[^"]*"', f'BlendSpace="/Script/Engine.BlendSpace\'{bs.get_path_name()}\'"', t)
            nd.import_text(t); n.set_editor_property("node", nd); print("Walk/Run BS ->", bs.get_name())
# speed remap function, spliced in front of SetGroundSpeed
gs = {x.get_name(): x for x in T.list_graphs(abp)}
if "RemapSpeed" not in gs:
    fg = T.add_function_graph(abp, "RemapSpeed")
    T.add_function_param(fg, "S", "float", True); T.add_function_param(fg, "Out", "float", False)
    unreal.BlueprintEditorLibrary.compile_blueprint(abp)
    gs = {x.get_name(): x for x in T.list_graphs(abp)}
    T.write_graph_dsl(gs["RemapSpeed"], """
(fn RemapSpeed (S)
  (return (select (< S 140.0) (* S 2.142857) (+ 300.0 (* (- S 140.0) 1.034483)))))""")
    unreal.BlueprintEditorLibrary.compile_blueprint(abp)
print(T.read_graph_dsl(gs["RemapSpeed"]))
eg = gs["EventGraph"]
def info(n): return T.get_node_infos([n])[0]
def pin(i, name, out):
    for p in (i.output_pins if out else i.input_pins):
        if str(p.name) == name: return p
    raise KeyError(f"{name} in {[str(p.name) for p in (i.output_pins if out else i.input_pins)]}")
nodes = T.find_nodes(eg, "")
setgs = [n for n in nodes if "SetGroundSpeed" in str(info(n).type_id)][0]
if not any("RemapSpeed" in str(info(n).type_id) for n in nodes):
    si = info(setgs)
    exec_in = pin(si, "execute", False); val_in = pin(si, "GroundSpeed", False)
    prev_exec = exec_in.get_editor_property("connected_pins")[0]; prev_val = val_in.get_editor_property("connected_pins")[0]
    call = T.create_node(eg, [str(x) for x in T.find_node_types(eg, "RemapSpeed")][0], unreal.IntPoint(400, 300))
    ci = info(call)
    T.break_pins(prev_exec, exec_in.pin_id); T.break_pins(prev_val, val_in.pin_id)
    T.connect_pins(prev_exec, pin(ci, "execute", False).pin_id); T.connect_pins(pin(ci, "then", True).pin_id, exec_in.pin_id)
    T.connect_pins(prev_val, pin(ci, "S", False).pin_id); T.connect_pins(pin(ci, "Out", True).pin_id, val_in.pin_id)
    print("RemapSpeed spliced")
print("compile", unreal.BlueprintEditorLibrary.compile_blueprint(abp)); eal.save_loaded_asset(abp)
print(T.read_graph_dsl(eg)[:900])
