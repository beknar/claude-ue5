"""fantasy_castle_level: stream in the stripped Lake Village (fcl_lake_village, always loaded) offset into the castle's lake,
south of the castle's eastern island - its water line (-33 local) meets the castle lake surface (z 3390) and its walled village
faces the island (no rotation). World game mode = BP_FF2GameMode (the animated Tripo anime female).
Args: [x y z yaw]   (default 26000 48000 3423 0)"""
import sys, unreal
OFF = [float(v) for v in sys.argv[1:5]] if len(sys.argv) >= 5 else [26000.0, 48000.0, 3423.0, 0.0]
SUB = "/Game/FantasyCastleLevel/Maps/fcl_lake_village"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if "fantasy_castle_level." not in ues.get_editor_world().get_path_name(): les.load_level("/Game/FantasyCastleLevel/Maps/fantasy_castle_level")
w = ues.get_editor_world(); assert "fantasy_castle_level." in w.get_path_name(), w.get_path_name()
tr = unreal.Transform(location=unreal.Vector(*OFF[:3]), rotation=unreal.Rotator(roll=0, pitch=0, yaw=OFF[3]), scale=unreal.Vector(1, 1, 1))
existing = [s for s in unreal.EditorLevelUtils.get_levels(w) if SUB.split("/")[-1] in s.get_path_name()]
if existing:
    print("sub-level already present:", [s.get_path_name() for s in existing])
else:
    st = unreal.EditorLevelUtils.add_level_to_world_with_transform(w, SUB, unreal.LevelStreamingAlwaysLoaded, tr)
    print("added", st.get_class().get_name() if st else None, "transform", OFF)
les.set_current_level_by_name("fantasy_castle_level")   # adding a level makes it the current one: spawn into the persistent level again
ws = w.get_world_settings()
ws.set_editor_property("default_game_mode", unreal.load_asset("/Game/FF2/Game/BP_FF2GameMode").generated_class())
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
print("levels", [l.get_path_name().split(":")[0] for l in unreal.EditorLevelUtils.get_levels(w)], "| game mode", ws.get_editor_property("default_game_mode").get_name())
