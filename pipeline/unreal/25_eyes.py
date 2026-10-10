"""Dark brown irises (her scan's eye colour) on the built eye materials."""
import unreal
mel = unreal.MaterialEditingLibrary
for side in ("L", "R"):
    mi = unreal.load_asset(f"/Game/MetaHumans/Fig4/Face/Materials/MI_Eye{side}_Baked")
    mel.set_material_instance_vector_parameter_value(mi, "Iris Color Multiply", unreal.LinearColor(0.30, 0.17, 0.09, 1))
    mel.set_material_instance_scalar_parameter_value(mi, "Pupil Dilation", 1.08)
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
print("irises tinted dark brown")
