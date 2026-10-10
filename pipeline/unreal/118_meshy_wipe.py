"""Delete all generated /Game/Meshy assets (dependents first) so the pipeline can rebuild them cleanly."""
import unreal
eal = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if "/Game/Meshy/" in w.get_path_name():
    try: les.load_level("/Game/Fig4/Maps/L_Fig4_Meadow")
    except RuntimeError as e: print("(non-fatal)", str(e)[:100])
order = ["/Game/Meshy/Maps", "/Game/Meshy/Game", "/Game/Meshy/Locomotion", "/Game/Meshy/Anims", "/Game/Meshy/Materials",
         "/Game/Meshy/Character", "/Game/Meshy/Textures"]
for d in order:
    if not eal.does_directory_exist(d): continue
    for p in sorted(eal.list_assets(d, recursive=True), key=lambda s: ("ABP_" not in s, "BS_" not in s)):
        p = p.split(".")[0]
        if eal.does_asset_exist(p) and not eal.delete_asset(p): print("could not delete", p)
left = eal.list_assets("/Game/Meshy", recursive=True) if eal.does_directory_exist("/Game/Meshy") else []
print("left:", left)
if not left: print("dir removed:", eal.delete_directory("/Game/Meshy"))
