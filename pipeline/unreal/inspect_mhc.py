import unreal
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
print("SUBSYSTEM:", [m for m in dir(mhs) if not m.startswith("_") and m not in dir(unreal.Object)])
ch = unreal.load_asset("/Game/Fig4/MetaHuman/MHC_Fig4")
print("CHAR props:", [m for m in dir(ch) if not m.startswith("_") and m not in dir(unreal.Object)])
for p in ("skin_settings", "eyes_settings", "makeup_settings", "head_model_settings", "preview_material_type"):
    try:
        print("==", p, ch.get_editor_property(p))
    except Exception as e:
        print("==", p, "ERR", e)
for cls in ("MetaHumanCharacterSkinProperties", "MetaHumanCharacterEyesSettings", "MetaHumanCharacterEyeProperties",
            "MetaHumanCharacterHeadModelSettings", "MetaHumanCharacterEyelashesProperties", "MetaHumanCharacterTeethProperties"):
    c = getattr(unreal, cls, None)
    print("STRUCT", cls, [m for m in dir(c) if not m.startswith("_")] if c else None)
