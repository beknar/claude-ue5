"""Replace the stale ABP_Unarmed_Meshy (bound to the deleted first-import skeleton) with the fresh retarget."""
import unreal
eal = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    les.editor_request_end_play(); print("PIE stop requested")
LA = "/Game/Meshy/Locomotion/Anims"
dupes = [p.split(".")[0] for p in eal.list_assets("/Game/Meshy", recursive=True) if p.split(".")[0][-1].isdigit()]
print("numbered assets:", dupes)
old, new = f"{LA}/ABP_Unarmed_Meshy", f"{LA}/ABP_Unarmed_Meshy1"
if eal.does_asset_exist(new):
    old_a = unreal.load_asset(old) if eal.does_asset_exist(old) else None
    new_a = unreal.load_asset(new)
    print("old skeleton:", old_a.get_editor_property("target_skeleton") if old_a else None)
    print("new skeleton:", new_a.get_editor_property("target_skeleton"))
    if old_a: print("consolidate:", eal.consolidate_assets(new_a, [old_a]))
    print("rename:", eal.rename_asset(new, old))
print("referencers of ABP:", eal.find_package_referencers_for_asset(old, False))
bp = unreal.load_asset("/Game/Meshy/Game/BP_MeshyCharacter")
cdo = unreal.get_default_object(bp.generated_class())
print("character anim class:", cdo.get_editor_property("mesh").get_editor_property("anim_class"))
