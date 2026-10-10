"""IA_Sprint (Left Shift / gamepad left-thumb) in IMC_Default; find node types for the sprint graph."""
import unreal
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
path = "/Game/Input/Actions/IA_Sprint"
if not eal.does_asset_exist(path):
    fac = [getattr(unreal, n) for n in ("InputAction_Factory", "InputActionFactory") if hasattr(unreal, n)]
    ia = at.create_asset("IA_Sprint", "/Game/Input/Actions", unreal.InputAction, fac[0]() if fac else None)
else:
    ia = unreal.load_asset(path)
ia.set_editor_property("value_type", unreal.InputActionValueType.BOOLEAN)
eal.save_loaded_asset(ia)
imc = unreal.load_asset("/Game/Input/IMC_Default")
existing = [str(m.action.get_name()) for m in imc.get_editor_property("mappings") if m.action]
def key(n):
    k = unreal.Key(); k.set_editor_property("key_name", n); return k
if "IA_Sprint" not in existing:
    imc.map_key(ia, key("LeftShift"))
    imc.map_key(ia, key("Gamepad_LeftThumbstick"))
eal.save_loaded_asset(imc)
print("IMC actions:", [str(m.action.get_name()) for m in imc.get_editor_property("mappings") if m.action])
import editor_toolset.toolsets.blueprint as BT
bp = unreal.load_asset("/Game/Fig4/Game/BP_Fig4Character")
for q in ("IA_Sprint", "Set Max Walk Speed", "MaxWalkSpeed", "Get Character Movement"):
    try:
        r = BT.BlueprintTools.find_node_types(bp, q) if hasattr(BT.BlueprintTools, "find_node_types") else None
        print(q, "->", str(r)[:600])
    except Exception as e:
        print(q, "ERR", str(e)[:200])
