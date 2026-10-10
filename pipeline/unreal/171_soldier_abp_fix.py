"""Replace the mis-targeted RemapSpeed call in ABP_Unarmed_Soldier with a call to its own function."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
abp = unreal.load_asset("/Game/Soldier/Locomotion/Anims/ABP_Unarmed_Soldier")
eg = {x.get_name(): x for x in T.list_graphs(abp)}["EventGraph"]
def info(n): return T.get_node_infos([n])[0]
def pin(i, name, out):
    for p in (i.output_pins if out else i.input_pins):
        if str(p.name) == name: return p
    raise KeyError(name)
ids = [str(x) for x in T.find_node_types(eg, "RemapSpeed")]
print("candidate ids:", ids)
own = [i for i in ids if i == "CallFunction|RemapSpeed"] or [i for i in ids if "Meshy" not in i and "Fig4" not in i]
print("using", own[0])
nodes = T.find_nodes(eg, "")
bad = [n for n in nodes if "RemapSpeed" in str(info(n).type_id)]
sg = [n for n in nodes if "SetGroundSpeed" in str(info(n).type_id)][0]; si = info(sg)
ex, vi = pin(si, "execute", False), pin(si, "GroundSpeed", False)
# upstream of the bad call: what fed its exec and S pins
bi = info(bad[0])
pe = pin(bi, "execute", False).get_editor_property("connected_pins")[0]
pv = pin(bi, "S", False).get_editor_property("connected_pins")[0]
for b in bad: T.delete_node(b)
call = T.create_node(eg, own[0], unreal.IntPoint(400, 300)); ci = info(call)
T.connect_pins(pe, pin(ci, "execute", False).pin_id); T.connect_pins(pin(ci, "then", True).pin_id, ex.pin_id)
T.connect_pins(pv, pin(ci, "S", False).pin_id); T.connect_pins(pin(ci, "Out", True).pin_id, vi.pin_id)
print("compile", unreal.BlueprintEditorLibrary.compile_blueprint(abp)); unreal.EditorAssetLibrary.save_loaded_asset(abp)
print(T.read_graph_dsl(eg)[:700])
