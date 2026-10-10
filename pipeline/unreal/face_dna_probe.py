import unreal
for n in dir(unreal):
    if "ImportFrom" in n and ("Params" in n or "Param" in n):
        try:
            print(n, getattr(unreal, n)().to_dict())
        except Exception as e:
            print(n, "?", e)
for a in unreal.EditorAssetLibrary.list_assets("/Game/MetaHumans/Fig4/Face", recursive=False):
    o = unreal.EditorAssetLibrary.find_asset_data(a)
    print(a, o.asset_class_path.asset_name if hasattr(o, "asset_class_path") else "")
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
print("doc:", mhs.import_from_face_dna.__doc__[:600] if mhs.import_from_face_dna.__doc__ else None)
