"""Fresh character with fig4's measured body constraints; spawn its preview beside her for review.
Also report the unlit BSDF pin names (bulb material fix)."""
import unreal
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
eal = unreal.EditorAssetLibrary
src = unreal.load_asset("/Game/Fig4/MetaHuman/MHC_Fig4v9")
if not (mhs.is_object_added_for_editing(src) or mhs.try_add_object_to_edit(src)):
    raise RuntimeError("edit src")
targets = {str(c.name): c.target_measurement for c in mhs.get_body_constraints(src)}
mhs.remove_object_to_edit(src)

path = "/Game/Fig4/MetaHuman/MHC_Fig4_Final"
if eal.does_asset_exist(path):
    eal.delete_asset(path)
ch = unreal.AssetToolsHelpers.get_asset_tools().create_asset("MHC_Fig4_Final", "/Game/Fig4/MetaHuman",
        unreal.MetaHumanCharacter, unreal.new_object(type=unreal.MetaHumanCharacterFactoryNew))
if not mhs.try_add_object_to_edit(ch):
    raise RuntimeError("edit new")
cons = mhs.get_body_constraints(ch)
for c in cons:
    n = str(c.name)
    if n in targets:
        c.is_active = True
        c.target_measurement = targets[n]
mhs.set_body_constraints(character=ch, body_constraints=cons)
mhs.commit_body_state(character=ch)
unreal.MetaHumanGeneratorSubsystemWrapper.reset_neck_to_body(ch)
eal.save_loaded_asset(ch, only_if_is_dirty=False)
print("fresh body:", {str(c.name): round(c.target_measurement, 1) for c in mhs.get_body_constraints(ch)
                       if str(c.name) in ("Height", "Chest", "Waist", "Hip", "Across Shoulder")})
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([ch])
a = mhs.spawn_meta_human_actor(ch)
a.set_actor_location(unreal.Vector(-120, 0, 6), False, False)
mel = unreal.MaterialEditingLibrary
m = unreal.load_asset("/Game/Fig4/Studio/Materials/M_Bulb")
for e in [mel.create_material_expression(m, unreal.MaterialExpressionSubstrateUnlitBSDF, 0, 0)]:
    print("unlit pins:", list(mel.get_material_expression_input_names(e)))
    mel.delete_material_expression(m, e)
