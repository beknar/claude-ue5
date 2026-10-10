import unreal
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
ok = unreal.EditorAssetLibrary.save_directory("/Game/Fig4", only_if_is_dirty=True, recursive=True)
ok2 = unreal.EditorAssetLibrary.save_directory("/Game/MetaHumans", only_if_is_dirty=True, recursive=True)
print("saved", ok, ok2)
