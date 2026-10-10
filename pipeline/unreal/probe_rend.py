import unreal
g = unreal.load_asset("/Game/Fig4/Hair/GR_Fig4_Hair")
r = g.get_editor_property("hair_groups_rendering")[0]
print(r.to_dict())
print(list(g.get_editor_property("hair_groups_physics")[0].to_dict().keys()))
