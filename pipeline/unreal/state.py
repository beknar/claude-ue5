import unreal
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
for a in unreal.EditorAssetLibrary.list_assets("/Game/Fig4/MetaHuman", recursive=True):
    o = unreal.load_asset(a)
    print(a, type(o).__name__, "editing:" , mhs.is_object_added_for_editing(o) if isinstance(o, unreal.MetaHumanCharacter) else "-")
print("open:", [x.get_path_name() for x in unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).get_all_edited_assets()])
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
print("actors:", [a.get_actor_label() for a in eas.get_all_level_actors() if "Fig4" in a.get_actor_label() or "REVIEW" in a.get_actor_label()])
