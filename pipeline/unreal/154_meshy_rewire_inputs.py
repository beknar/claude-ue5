"""Rewire Enhanced Input events (Started) -> Act_* functions on BP_MeshyCharacter without touching Tick/demo logic."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
bp = unreal.load_asset("/Game/Meshy/Game/BP_MeshyCharacter")
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
MOVES = ("IA_Jab", "IA_Hook", "IA_Punch", "IA_Sweep", "IA_Kick", "IA_TurnLeft", "IA_TurnRight", "IA_Stroll", "IA_IdleAnim")
def info(n): return T.get_node_infos([n])[0]
def pin(i, name, out):
    for p in (i.output_pins if out else i.input_pins):
        if str(p.name) == name: return p.pin_id
    raise KeyError(name)
removed = 0
for n in T.find_nodes(g, ""):
    t = str(info(n).type_id)
    if "EnhancedActionEvents" in t or "|Act_" in t or t.startswith("CallFunction|Act"):
        T.delete_node(n); removed += 1
print("removed", removed)
ids = {str(x) for x in T.find_node_types(g, "CallFunction|Act")}
for k, ia in enumerate(MOVES):
    ev = T.create_node(g, f"Input|EnhancedActionEvents|{ia}", unreal.IntPoint(-1200, 1600 + 220 * k))
    cid = f"CallFunction|Act{ia[3:]}"
    call = T.create_node(g, cid if cid in ids else f"CallFunction|Act_{ia[3:]}", unreal.IntPoint(-750, 1600 + 220 * k))
    T.connect_pins(pin(info(ev), "Started", True), pin(info(call), "execute", False))
nodes = [str(info(n).type_id) for n in T.find_nodes(g, "")]
print("events:", sum("EnhancedActionEvents" in t for t in nodes), "act calls:", sum(("Act_" in t or "|Act" in t) for t in nodes),
      "tick present:", any("EventTick" in t for t in nodes))
print("compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp)); unreal.EditorAssetLibrary.save_loaded_asset(bp)
