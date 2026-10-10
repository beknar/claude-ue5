"""(Re)map every custom input action in IMC_Default and verify the mappings survive a reload from disk."""
import unreal
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
KEYS = {"IA_Sprint": ["LeftShift", "Gamepad_LeftThumbstick"], "IA_SprintFast": ["LeftControl", "Gamepad_RightTrigger"],
        "IA_Jab": ["One", "LeftMouseButton"], "IA_Hook": ["Two", "RightMouseButton"], "IA_Punch": ["Three"],
        "IA_Sweep": ["Four"], "IA_Kick": ["Five"], "IA_TurnLeft": ["Q"], "IA_TurnRight": ["E"],
        "IA_IdleAnim": ["Six"], "IA_Stroll": ["Seven"]}
IMC = "/Game/Input/IMC_Default"
def mapped(imc):
    return {(m.get_editor_property("action").get_name(), str(m.get_editor_property("key").get_editor_property("key_name")))
            for m in imc.get_editor_property("default_key_mappings").get_editor_property("mappings") if m.get_editor_property("action")}
imc = unreal.load_asset(IMC)
have = mapped(imc)
added = 0
for name, keys in KEYS.items():
    p = f"/Game/Input/Actions/{name}"
    ia = unreal.load_asset(p) if eal.does_asset_exist(p) else at.create_asset(name, "/Game/Input/Actions", unreal.InputAction, None)
    ia.set_editor_property("value_type", unreal.InputActionValueType.BOOLEAN); eal.save_loaded_asset(ia, False)
    for k in keys:
        if (name, k) not in have:
            key = unreal.Key(); key.set_editor_property("key_name", k); imc.map_key(ia, key); added += 1
imc.modify()
print("added", added, "| save:", eal.save_asset(IMC, False))
# prove it is on disk: reload the package and re-read
pkg = unreal.load_package(IMC)
print("reload:", unreal.EditorLoadingAndSavingUtils.reload_packages([pkg]))
imc = unreal.load_asset(IMC)
now = mapped(imc)
missing = [(n, k) for n, ks in KEYS.items() for k in ks if (n, k) not in now]
print("after reload:", len(now), "mappings; missing:", missing)
