"""Walk by default, Shift = run: scale Move() input by (Sprint ? 1 : 0.383), diagonal-normalized.
CMC MaxWalkSpeed is 470 (run); analog input scaling yields ~180 cm/s walk."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
pbp = unreal.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
graphs = {x.get_name(): x for x in T.list_graphs(pbp)}
if "MoveScale" not in graphs:
    fg = T.add_function_graph(pbp, "MoveScale")
    T.write_graph_dsl(fg, """
(fn MoveScale (X Y)
  (bind s (select (Input|EnhancedActionValues|IA_Sprint) 1.0 0.383))
  (bind len (Math|Float|Sqrt (+ (* X X) (* Y Y))))
  (bind k (/ s (Math|Float|Max(Float) len 1.0)))
  (return (* X k) (* Y k)))
""")
    graphs = {x.get_name(): x for x in T.list_graphs(pbp)}
print(T.read_graph_dsl(graphs["MoveScale"]))
g = graphs["Move"]
def infos(n): return T.get_node_infos([n])[0]
def nodepath(pid): return str(pid.get_editor_property("node").get_path_name()) if hasattr(pid.get_editor_property("node"), "get_path_name") else str(pid.get_editor_property("node"))
nodes = T.find_nodes(g, "")
byname = {n.get_path_name(): n for n in nodes}
entry = [n for n in nodes if infos(n).type_id == "|Move"][0]
ei = infos(entry)
print("entry out", [(str(p.name), p.pin_id.get_editor_property("index_id")) for p in ei.output_pins])
def trace(pin_info):
    """follow an input pin back through knots; return entry output pin name or None"""
    cps = pin_info.get_editor_property("connected_pins")
    while cps:
        src = cps[0]; srcnode = src.get_editor_property("node")
        if srcnode == entry:
            idx = src.get_editor_property("index_id")
            return [str(p.name) for p in ei.output_pins if p.pin_id.get_editor_property("index_id") == idx][0]
        si = infos(srcnode)
        if "Knot" in srcnode.get_class().get_name():
            cps = si.input_pins[0].get_editor_property("connected_pins"); continue
        return "other:" + str(si.type_id)
    return None
unreal.BlueprintEditorLibrary.compile_blueprint(pbp)
for n in [n for n in nodes if "MoveScale" in str(infos(n).type_id)]:
    if "X" not in [str(p.name) for p in infos(n).input_pins]: T.delete_node(n)
nodes = T.find_nodes(g, "")
existing = [n for n in nodes if "MoveScale" in str(infos(n).type_id)]
print("existing MoveScale calls:", len(existing))
ids = [str(x) for x in T.find_node_types(g, "MoveScale")]
print("ids", ids)
ms = existing[0] if existing else T.create_node(g, ids[0], unreal.IntPoint(1500, -1100))
mi = infos(ms)
print("MoveScale pins in", [str(p.name) for p in mi.input_pins], "out", [str(p.name) for p in mi.output_pins])
def pin(info, name, out):
    for p in (info.output_pins if out else info.input_pins):
        if str(p.name) == name: return p
    raise KeyError(name)
if True:
    then = pin(ei, "then", True)
    cur = then.get_editor_property("connected_pins")
    if not (cur and cur[0].get_editor_property("node") == ms):
        if cur: T.break_pins(then.pin_id, cur[0])
        T.connect_pins(then.pin_id, pin(mi, "execute", False).pin_id)
    if not pin(mi, "then", True).get_editor_property("connected_pins"):
        heads = [n for n in nodes if infos(n).type_id == "Pawn|Input|AddMovementInput"
                 and not pin(infos(n), "execute", False).get_editor_property("connected_pins")]
        print("exec heads", len(heads))
        T.connect_pins(pin(mi, "then", True).pin_id, pin(infos(heads[0]), "execute", False).pin_id)
    T.connect_pins(pin(ei, "X Axis", True).pin_id, pin(mi, "X", False).pin_id)
    T.connect_pins(pin(ei, "Y Axis", True).pin_id, pin(mi, "Y", False).pin_id)
    outs = [p for p in mi.output_pins if str(p.name) != "then"]
    for n in nodes:
        ni = infos(n)
        if ni.type_id != "Pawn|Input|AddMovementInput": continue
        sv = pin(ni, "ScaleValue", False)
        src = trace(sv); print("AddMovementInput ScaleValue from", src)
        if src not in ("X Axis", "Y Axis"): continue
        o = outs[0] if src == "X Axis" else outs[1]
        old = sv.get_editor_property("connected_pins")
        if old: T.break_pins(old[0], sv.pin_id)
        T.connect_pins(o.pin_id, sv.pin_id)
unreal.BlueprintEditorLibrary.compile_blueprint(pbp)
unreal.EditorAssetLibrary.save_loaded_asset(pbp)
print(T.read_graph_dsl(g))
# CMC max walk speed = run speed on our character
cbp = unreal.load_asset("/Game/Fig4/Game/BP_Fig4Character")
cdo = unreal.get_default_object(cbp.generated_class())
cdo.character_movement.set_editor_property("max_walk_speed", 470.0)
cdo.character_movement.set_editor_property("min_analog_walk_speed", 0.0)
gch = unreal.BlueprintEditorLibrary.find_event_graph(cbp)
for n in T.find_nodes(gch, ""):  # remove leftovers from sprint-graph attempt
    if not isinstance(n, unreal.K2Node_Event): T.delete_node(n)
unreal.BlueprintEditorLibrary.compile_blueprint(cbp)
unreal.EditorAssetLibrary.save_loaded_asset(cbp)
print("cmc", cdo.character_movement.max_walk_speed)
