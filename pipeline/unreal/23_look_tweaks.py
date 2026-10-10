"""Hair: rougher, more scraggle and melanin variation."""
import unreal
mel = unreal.MaterialEditingLibrary
mi = unreal.load_asset("/Game/Fig4/Hair/MI_Fig4_Hair")
for k, v in {"HairRoughness": 0.42, "Scraggle": 0.22, "MelaninVariationFine": 0.08, "RoughnessVariation": 0.2}.items():
    mel.set_material_instance_scalar_parameter_value(mi, k, v)
unreal.EditorAssetLibrary.save_loaded_asset(mi)
print("hair tweaked")
