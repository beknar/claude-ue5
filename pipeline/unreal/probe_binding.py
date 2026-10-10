import unreal
print([n for n in dir(unreal) if "GroomBinding" in n or ("Groom" in n and ("Library" in n or "Factory" in n or "Editor" in n))])
b = unreal.load_asset("/Game/MetaHumans/Fig4/Grooms/Eyebrows_M_Natural_Binding")
print(type(b).__name__)
for p in ("groom", "target_skeletal_mesh", "source_skeletal_mesh", "binding_type", "num_interpolation_points", "matching_section", "groom_binding_type"):
    try: print(" ", p, b.get_editor_property(p))
    except Exception as e: print(" ", p, "ERR", str(e)[:80])
