"""Input actions for the Meshy character's moves, mapped in IMC_Default, plus a node-type survey for the graphs."""
import unreal
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
ACTIONS = {"IA_Jab": ["One", "LeftMouseButton"], "IA_Hook": ["Two", "RightMouseButton"], "IA_Punch": ["Three"],
           "IA_Sweep": ["Four"], "IA_Kick": ["Five"], "IA_TurnLeft": ["Q"], "IA_TurnRight": ["E"],
           "IA_IdleAnim": ["Six"], "IA_Stroll": ["Seven"]}
imc = unreal.load_asset("/Game/Input/IMC_Default")
def key(n):
    k = unreal.Key(); k.set_editor_property("key_name", n); return k
def mapped():
    out = set()
    try:
        for m in imc.get_editor_property("default_key_mappings").get_editor_property("mappings"):
            out.add((m.get_editor_property("action").get_name(), str(m.get_editor_property("key").get_editor_property("key_name"))))
    except Exception as e: print("read mappings:", str(e)[:120])
    return out
have = mapped()
for name, keys in ACTIONS.items():
    p = f"/Game/Input/Actions/{name}"
    ia = unreal.load_asset(p) if eal.does_asset_exist(p) else at.create_asset(name, "/Game/Input/Actions", unreal.InputAction, None)
    ia.set_editor_property("value_type", unreal.InputActionValueType.BOOLEAN); eal.save_loaded_asset(ia)
    for k in keys:
        if (name, k) not in have: imc.map_key(ia, key(k))
eal.save_loaded_asset(imc)
print("IMC now:", sorted(a for a in mapped() if a[0] in ACTIONS or a[0] in ("IA_Sprint", "IA_Jump")))
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
g = unreal.BlueprintEditorLibrary.find_event_graph(unreal.load_asset("/Game/Fig4/Game/BP_Fig4Character"))
for q in ("IA_Jab", "PlayAnimMontage", "StopAnimMontage", "GetCurrentMontage", "RandomInteger", "IsFalling", "GetWorldDeltaSeconds", "VectorLengthXY", "GetVelocity"):
    print(q, [str(x) for x in T.find_node_types(g, q)][:6])
