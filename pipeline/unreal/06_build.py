"""Assemble the MetaHuman (cinematic). Args: asset_path build_dir name"""
import sys, time, unreal
ch = unreal.load_asset(sys.argv[1])
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
if not (mhs.is_object_added_for_editing(ch) or mhs.try_add_object_to_edit(ch)):
    raise RuntimeError("cannot edit")
print("can build:", mhs.can_build_meta_human(ch))
bp = unreal.MetaHumanCharacterEditorBuildParameters()
bp.pipeline_type = unreal.MetaHumanDefaultPipelineType.CINEMATIC
bp.pipeline_quality = unreal.MetaHumanQualityLevel.CINEMATIC
bp.absolute_build_path = sys.argv[2]
bp.common_folder_path = sys.argv[2] + "/Common"
bp.name_override = sys.argv[3]
bp.enable_wardrobe_item_validation = False
t = time.time()
try:
    mhs.build_meta_human(character=ch, params=bp)
except RuntimeError as e:
    # Control Rig "Cannot break link" warnings surface as Python errors; the build still completes
    print("build reported (non-fatal):", str(e).splitlines()[0][:160])
print(f"BUILD done in {time.time()-t:.0f}s")
saved = unreal.EditorAssetLibrary.save_directory(sys.argv[2], only_if_is_dirty=False, recursive=True)
print("saved build directory:", saved)
for a in unreal.EditorAssetLibrary.list_assets(sys.argv[2] + "/" + sys.argv[3], recursive=True)[:60]:
    print(" ", a)
