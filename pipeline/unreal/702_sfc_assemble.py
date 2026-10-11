"""sf-city-level: stream in the stripped Monolith (sfc_monolith, always loaded) west of the city, across the void from the
city's south dock platform (x -20400..-10600, deck z 32, open west end at y -58400). Its entrance plaza faces the city (+Y);
the low channel in its +Y landscape edge (local x -6000) lines up with the dock so the road (703) runs straight west.
World game mode = BP_JRPGFem5GameMode (jrpg-fem5-tripo, her own idle / walk / run + template jump).
Args: [x y z yaw]   (default -9000 -103600 -150 0)"""
import sys, unreal
OFF = [float(v) for v in sys.argv[1:5]] if len(sys.argv) >= 5 else [-9000.0, -103600.0, -150.0, 0.0]
MAP = "/Game/SFCityLevel/Maps/sf-city-level"; SUB = "/Game/SFCityLevel/Maps/sfc_monolith"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
w = ues.get_editor_world(); assert w.get_path_name().startswith(MAP + "."), w.get_path_name()
tr = unreal.Transform(location=unreal.Vector(*OFF[:3]), rotation=unreal.Rotator(roll=0, pitch=0, yaw=OFF[3]), scale=unreal.Vector(1, 1, 1))
existing = [s for s in unreal.EditorLevelUtils.get_levels(w) if "sfc_monolith" in s.get_path_name()]
if existing:
    print("sub-level already present:", [s.get_path_name() for s in existing])
else:
    st = unreal.EditorLevelUtils.add_level_to_world_with_transform(w, SUB, unreal.LevelStreamingAlwaysLoaded, tr)
    print("added", st.get_class().get_name() if st else None, "transform", OFF)
les.set_current_level_by_name("sf-city-level")       # adding a level makes it current: spawn into the persistent level again
ws = w.get_world_settings()
ws.set_editor_property("default_game_mode", unreal.load_asset("/Game/JRPG/Game/BP_JRPGFem5GameMode").generated_class())
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
print("levels", [l.get_path_name().split(":")[0] for l in unreal.EditorLevelUtils.get_levels(w)], "| game mode", ws.get_editor_property("default_game_mode").get_name())
