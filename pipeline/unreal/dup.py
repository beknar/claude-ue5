import sys, unreal
src, dst = sys.argv[1], sys.argv[2]
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
o = unreal.load_asset(src)
if mhs.is_object_added_for_editing(o):
    mhs.remove_object_to_edit(o)
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(o)
if unreal.EditorAssetLibrary.does_asset_exist(dst):
    unreal.EditorAssetLibrary.delete_asset(dst)
print("dup", unreal.EditorAssetLibrary.duplicate_asset(src, dst))
