import unreal
for a in unreal.EditorAssetLibrary.list_assets("/Game/Fig4/MetaHuman", recursive=True):
    print(a)
ch = unreal.load_asset("/Game/Fig4/MetaHuman/MHC_Fig4_Final")
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([ch])
print("opened")
