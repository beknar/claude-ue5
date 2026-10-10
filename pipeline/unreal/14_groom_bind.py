"""Create the hair binding to the final face mesh and attach the groom to the Fig4 actor."""
import unreal
eal = unreal.EditorAssetLibrary
print("GroomLibrary:", [m for m in dir(unreal.GroomLibrary) if not m.startswith("_")][:30])
groom = unreal.load_asset("/Game/Fig4/Hair/GR_Fig4_Hair")
face = unreal.load_asset("/Game/MetaHumans/Fig4/Face/SKM_MHC_Fig4_Final_FaceMesh")
path = "/Game/Fig4/Hair/GR_Fig4_Hair_Binding"
if eal.does_asset_exist(path):
    eal.delete_asset(path)
binding = None
if hasattr(unreal.GroomLibrary, "create_new_groom_binding_asset_with_path"):
    binding = unreal.GroomLibrary.create_new_groom_binding_asset_with_path(path, groom, face, 32, None, 0)
elif hasattr(unreal.GroomLibrary, "create_new_groom_binding_asset"):
    binding = unreal.GroomLibrary.create_new_groom_binding_asset(groom, face, 32, None, 0)
else:
    binding = unreal.AssetToolsHelpers.get_asset_tools().create_asset("GR_Fig4_Hair_Binding", "/Game/Fig4/Hair",
                                                                      unreal.GroomBindingAsset, unreal.GroomBindingFactory())
    binding.set_editor_property("groom", groom)
    binding.set_editor_property("target_skeletal_mesh", face)
print("binding", binding)
if binding:
    eal.save_loaded_asset(binding)

# hair rendering: strands, physically sized, dark melanin
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Fig4":
        for gc in a.get_components_by_class(unreal.GroomComponent):
            if gc.get_name() == "Hair":
                gc.set_editor_property("groom_asset", groom)
                gc.set_editor_property("binding_asset", binding)
                print("assigned hair to", a.get_actor_label())
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
