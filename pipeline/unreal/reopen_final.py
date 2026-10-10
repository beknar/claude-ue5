import unreal
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
aes = unreal.get_editor_subsystem(unreal.AssetEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ch = unreal.load_asset("/Game/Fig4/MetaHuman/MHC_Fig4_Final")
for a in eas.get_all_level_actors():
    if "PreviewActor" in a.get_actor_label():
        eas.destroy_actor(a)
aes.close_all_editors_for_asset(ch)
if mhs.is_object_added_for_editing(ch):
    mhs.remove_object_to_edit(ch)
unreal.EditorAssetLibrary.save_loaded_asset(ch, only_if_is_dirty=False)
print("added after release:", mhs.is_object_added_for_editing(ch))
aes.open_editor_for_assets([ch])
print("added after open:", mhs.is_object_added_for_editing(ch))
