"""L_Fig4_Outdoor_Cine: the playable map saved-as a cinematic variant, with an AI-possessed demo Fig4 that
performs the idle/walk/run/jump routine on its own (bAutoDemo). DemoStartTime offsets MRQ engine warm-up (1 s).
(Duplicating the map asset and loading the copy crashed the 5.8 editor, so this loads the original and saves-as.)"""
import unreal
eal = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SRC, DST = "/Game/Fig4/Maps/L_Fig4_Outdoor", "/Game/Fig4/Maps/L_Fig4_Outdoor_Cine"
try: les.load_level(DST if eal.does_asset_exist(DST) else SRC)
except RuntimeError as e: print("(non-fatal)", str(e)[:120])
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
print("loaded", world.get_path_name())
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.PlayerStart) or a.get_actor_label() == "Fig4_Demo":
        eas.destroy_actor(a)
cls = eal.load_blueprint_class("/Game/Fig4/Game/BP_Fig4Character")
demo = eas.spawn_actor_from_class(cls, unreal.Vector(0, 0, 88), unreal.Rotator(pitch=0, yaw=0, roll=0))
demo.set_actor_label("Fig4_Demo")
demo.set_editor_property("auto_possess_ai", unreal.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED)
demo.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.DISABLED)
def setp(o, names, v):
    for n in names:
        try: o.set_editor_property(n, v); return n
        except Exception: pass
    raise RuntimeError(names)
kA = setp(demo, ["bAutoDemo", "auto_demo", "b_auto_demo", "AutoDemo"], True)
kT = setp(demo, ["DemoStartTime", "demo_start_time"], 1.0)
print("demo", demo.get_name(), kA, demo.get_editor_property(kA), demo.get_editor_property(kT))
if world.get_path_name().startswith(DST):
    les.save_current_level()
else:
    print("save as:", unreal.EditorLoadingAndSavingUtils.save_map(world, DST))
print("now editing", unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name())
