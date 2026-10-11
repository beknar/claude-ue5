"""sf-city-level map copies (Save As; restart the editor after each, see CLAUDE.md):
  city     -> /Game/SFCityLevel/Maps/sf-city-level   (copy of the Open World Science fiction City showcase, /Game/Mega_City)
  monolith -> /Game/SFCityLevel/Maps/sfc_monolith    (copy of the Monolith Megastructure showcase; becomes a streaming
              sub-level of sf-city-level, stripped by 701 and placed by 702)
  cine     -> /Game/SFCityLevel/Maps/sf-city-level_Cine  (cinematic copy of the finished sf-city-level, for 712-713)
Needs the HDRIBackdrop plugin (the city's sky). Both packs call their map L_showcase_level: compare full paths.
Args: city|monolith|cine. The pack maps themselves are never saved."""
import sys, unreal
SRC = {"city": "/Game/Mega_City/Level/L_showcase_level", "monolith": "/Game/Monolith_megastructure/Level/L_showcase_level",
       "cine": "/Game/SFCityLevel/Maps/sf-city-level"}
DST = {"city": "/Game/SFCityLevel/Maps/sf-city-level", "monolith": "/Game/SFCityLevel/Maps/sfc_monolith",
       "cine": "/Game/SFCityLevel/Maps/sf-city-level_Cine"}
k = sys.argv[1]
eal = unreal.EditorAssetLibrary
assert not eal.does_asset_exist(DST[k]), DST[k] + " exists: move its .umap out of Content first (Save As cannot overwrite a loaded package)"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if not ues.get_editor_world().get_path_name().startswith(SRC[k] + "."): les.load_level(SRC[k])
w = ues.get_editor_world(); assert w.get_path_name().startswith(SRC[k] + "."), w.get_path_name()
print("save as", DST[k], unreal.EditorLoadingAndSavingUtils.save_map(w, DST[k]))
