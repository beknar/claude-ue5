"""ABP_Unarmed_FF: template foot-IK control rig off, GroundSpeed remapped from the FF's real stride speeds
(walk 285 / jog 570 cm/s, measured from the retargeted clips' root travel) onto the 300/600 blendspace grid;
montages for the unarmed attacks, charged attack and dash."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary
LA = "/Game/FF/Locomotion/Anims"; A = "/Game/FF/Anims"
WALK, RUN = 285.0, 570.0
abp = unreal.load_asset(LA + "/ABP_Unarmed_FF")
for g in T.list_graphs(abp):
    for n in T.find_nodes(g, ""):
        if n.get_class().get_name() == "AnimGraphNode_ControlRig":
            import re
            nd = n.get_editor_property("node"); nd.import_text(re.sub(r"Alpha=[0-9.]+", "Alpha=0.000000", nd.export_text())); n.set_editor_property("node", nd)
            for p in T.get_node_infos([n])[0].input_pins:
                if str(p.name) == "Alpha": T.set_pin_value(p.pin_id, "0.0")
            print("control rig alpha 0 in", g.get_name())
gs = {x.get_name(): x for x in T.list_graphs(abp)}
if "RemapSpeed" not in gs:
    fg = T.add_function_graph(abp, "RemapSpeed"); T.add_function_param(fg, "S", "float", True); T.add_function_param(fg, "Out", "float", False)
    unreal.BlueprintEditorLibrary.compile_blueprint(abp); gs = {x.get_name(): x for x in T.list_graphs(abp)}
k = 300.0 / WALK
T.write_graph_dsl(gs["RemapSpeed"], f"""
(fn RemapSpeed (S)
  (return (Math|Float|Min(Float) 600.0 (* S {k:.6f}))))""")
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
    print("RemapSpeed ids", ids)
    call = T.create_node(eg, "CallFunction|RemapSpeed" if "CallFunction|RemapSpeed" in ids else ids[0], unreal.IntPoint(400, 300)); ci = info(call)
    T.break_pins(pe, ex.pin_id); T.break_pins(pv, vi.pin_id)
    T.connect_pins(pe, pin(ci, "execute", False).pin_id); T.connect_pins(pin(ci, "then", True).pin_id, ex.pin_id)
    T.connect_pins(pv, pin(ci, "S", False).pin_id); T.connect_pins(pin(ci, "Out", True).pin_id, vi.pin_id)
print("ABP compile", unreal.BlueprintEditorLibrary.compile_blueprint(abp)); eal.save_loaded_asset(abp)
print([l for l in T.read_graph_dsl(eg).splitlines() if "Remap" in l][:3])
for clip in ("MM_Attack_01", "MM_Attack_02", "MM_Attack_03", "MM_ChargedAttack", "MM_Dash"):
    seq = unreal.load_asset(f"{LA}/{clip}_FF")
    name = "AM_FF_" + clip[3:]; p = f"{A}/{name}"
    if eal.does_asset_exist(p): eal.delete_asset(p)
    f = unreal.AnimMontageFactory(); f.set_editor_property("source_animation", seq)
    m = at.create_asset(name, A, unreal.AnimMontage, f); eal.save_loaded_asset(m)
    print("montage", name, round(m.get_play_length(), 2), "root motion", seq.get_editor_property("enable_root_motion"))
