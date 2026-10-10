import unreal
mel = unreal.MaterialEditingLibrary
mi = unreal.load_asset("/Game/MetaHumans/Fig4/Face/Materials/MI_EyeL_Baked")
print("parent", mi.get_editor_property("parent").get_path_name())
print("vectors", [str(n) for n in mel.get_vector_parameter_names(mi)])
print("scalars", [str(n) for n in mel.get_scalar_parameter_names(mi)][:60])
print("textures", [str(n) for n in mel.get_texture_parameter_names(mi)])
