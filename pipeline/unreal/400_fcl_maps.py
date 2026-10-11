"""fantasy_castle_level map copies (Save As; restart the editor after each, see CLAUDE.md):
  castle -> /Game/FantasyCastleLevel/Maps/fantasy_castle_level   (copy of the Fantasy Castle Environment's Scene map)
  lake   -> /Game/FantasyCastleLevel/Maps/fcl_lake_village       (copy of the Medieval Lake Village's Scene-Day map; becomes a
            streaming sub-level of fantasy_castle_level, stripped by 401 and placed by 402)
Args: castle|lake. The pack maps themselves are never saved."""
import sys, unreal
SRC = {"castle": "/Game/FantasyCastle/Map/Scene", "lake": "/Game/Medieval_Lake_Village/Scene/Scene-Day"}
DST = {"castle": "/Game/FantasyCastleLevel/Maps/fantasy_castle_level", "lake": "/Game/FantasyCastleLevel/Maps/fcl_lake_village"}
k = sys.argv[1]
eal = unreal.EditorAssetLibrary
assert not eal.does_asset_exist(DST[k]), DST[k] + " exists: move its .umap out of Content first (Save As cannot overwrite a loaded package)"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if SRC[k] not in unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name(): les.load_level(SRC[k])
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
print("save as", DST[k], unreal.EditorLoadingAndSavingUtils.save_map(w, DST[k]))
