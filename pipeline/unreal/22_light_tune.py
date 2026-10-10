import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
I = {"Key_Softbox": 260, "Fill_Scrim": 40, "Rim_L": 170, "Rim_R": 150, "Hair_Top": 95}
for a in eas.get_all_level_actors():
    lab = a.get_actor_label()
    if lab in I:
        a.light_component.set_editor_property("intensity", I[lab])
    elif lab.startswith("Bulb_"):
        a.light_component.set_editor_property("intensity", 0.9)
mel = unreal.MaterialEditingLibrary
m = unreal.load_asset("/Game/Fig4/Studio/Materials/M_Concrete_Cyc")
for e in unreal.MaterialEditingLibrary.get_material_selected_nodes(m) if False else []:
    pass
# Tint is a vector parameter on the master material: use an instance-free edit of the default
for expr in unreal.EditorAssetLibrary.find_package_referencers_for_asset(m.get_path_name()) if False else []:
    pass
mi_path = "/Game/Fig4/Studio/Materials/MI_Concrete_Cyc"
if not unreal.EditorAssetLibrary.does_asset_exist(mi_path):
    mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset("MI_Concrete_Cyc", "/Game/Fig4/Studio/Materials",
            unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, m)
else:
    mi = unreal.load_asset(mi_path)
mel.set_material_instance_vector_parameter_value(mi, "Tint", unreal.LinearColor(0.36, 0.36, 0.38, 1))
unreal.EditorAssetLibrary.save_loaded_asset(mi)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Cyclorama":
        a.static_mesh_component.set_material(0, mi)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print("lights + floor tuned")
