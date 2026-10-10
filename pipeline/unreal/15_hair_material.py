import unreal
mel = unreal.MaterialEditingLibrary; eal = unreal.EditorAssetLibrary
path = "/Game/Fig4/Hair/MI_Fig4_Hair"
if not eal.does_asset_exist(path):
    mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset("MI_Fig4_Hair", "/Game/Fig4/Hair",
            unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, unreal.load_asset("/MetaHumanCharacter/Materials/MI_Hair"))
else:
    mi = unreal.load_asset(path)
for k, v in {"hairMelanin": 0.97, "hairRedness": 0.10, "MelaninVariationFine": 0.04, "MelaninVariationRough": 0.06,
             "HairRoughness": 0.30, "RoughnessVariation": 0.12, "Scraggle": 0.08, "RedVariation": 0.03}.items():
    mel.set_material_instance_scalar_parameter_value(mi, k, v)
eal.save_loaded_asset(mi)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Fig4":
        for gc in a.get_components_by_class(unreal.GroomComponent):
            if gc.get_name() == "Hair":
                n = gc.get_num_materials()
                for i in range(max(n, 1)):
                    gc.set_material(i, mi)
                print("hair materials set:", max(n, 1))
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
