import unreal
mel = unreal.MaterialEditingLibrary
mi = unreal.load_asset("/MetaHumanCharacter/Materials/MI_Hair")
print("parent:", mi.get_editor_property("parent"))
print("scalars:", [str(n) for n in mel.get_scalar_parameter_names(mi)])
print("vectors:", [str(n) for n in mel.get_vector_parameter_names(mi)])
print("textures:", [str(n) for n in mel.get_texture_parameter_names(mi)])
print("switches:", [str(n) for n in mel.get_static_switch_parameter_names(mi)])
g = unreal.load_asset("/Game/Fig4/Hair/GR_Fig4_Hair")
for p in ("hair_groups_materials", "hair_groups_rendering", "hair_groups_physics", "enable_simulation", "hair_groups_lod"):
    try:
        v = g.get_editor_property(p); print(p, v[:1] if hasattr(v, "__len__") else v)
    except Exception as e:
        print(p, "ERR", str(e)[:100])
