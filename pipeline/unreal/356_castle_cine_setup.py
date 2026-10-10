"""castle_level_Cine: MoviePipelineGameMode (no player pawn), FF2 demo character at house_02's door running the castle
route (DemoMode 1, sequence-clocked, DemoStartTime 1.5 s), the door and the furnished-interior tour pieces (dormitory bed
chests, manor cupboard + chest) auto-open on the sequence clock (times match 358)."""
import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert "castle_level_Cine" in w.get_path_name(), w.get_path_name()
w.get_world_settings().set_editor_property("default_game_mode", unreal.load_class(None, "/Script/MovieRenderPipelineCore.MoviePipelineGameMode"))
LEAD = 1.5
TOUR = [((456, 2712, 663), 14.2), ((221, 2724, 663), 14.6), ((-13, 2736, 663), 15.0),     # tavern dormitory bed chests, left to right
        ((3195, 2138, 363), 18.2), ((3202, 2618, 363), 18.8)]                              # manor hall: cupboard under the stairs, chest
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "FF2_Demo": eas.destroy_actor(a)
cls = unreal.EditorAssetLibrary.load_blueprint_class("/Game/FF2/Game/BP_FF2Character")
demo = eas.spawn_actor_from_class(cls, unreal.Vector(1658, -1515, 100), unreal.Rotator(roll=0, pitch=0, yaw=-2))
demo.set_actor_label("FF2_Demo")
for k, v in (("bAutoDemo", True), ("DemoMode", 1.0), ("DemoStartTime", LEAD)): demo.set_editor_property(k, v)
demo.set_editor_property("auto_possess_ai", unreal.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED)
done = []
for a in eas.get_all_level_actors():
    lab = a.get_actor_label()
    if lab == "Door_SM_models_Cube_075_0": a.set_editor_property("AutoOpenAt", LEAD + 0.4); done.append(lab)
    if a.get_class().get_name() in ("BP_Container_C", "BP_Wardrobe_C"):
        for p, t in TOUR:
            if (a.get_actor_location() - unreal.Vector(*p)).length() < 40: a.set_editor_property("AutoOpenAt", t); done.append(f"{lab}@{t}")
print("auto-open set on", done, "| demo at", demo.get_actor_location())
les.save_current_level(); print("saved")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
