"""fantasy_castle_level PlayerStart (FF2 via BP_FF2GameMode, set in 402). Args: x y yaw  (default: the castle's east terrace at the foot of the 406 link ramp)."""
import sys, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert "fantasy_castle_level." in w.get_path_name(), w.get_path_name()
# spawn into the persistent level, never into the streamed village (fcl_lake_village is rebuilt from the pack)
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_current_level_by_name("fantasy_castle_level")
x, y, yaw = [float(v) for v in sys.argv[1:4]] if len(sys.argv) >= 4 else (6250.0, 118450.0, 0.0)   # foot of the 406 link ramp, facing the bridge and the lake
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.PlayerStart): eas.destroy_actor(a)
h = unreal.SystemLibrary.line_trace_single(w, unreal.Vector(x, y, 30000), unreal.Vector(x, y, -5000), unreal.TraceTypeQuery.ECC_VISIBILITY, True, [], unreal.DrawDebugTrace.NONE, True).to_tuple()
gz = h[4].z
ps = eas.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(x, y, gz + 100.0), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
ps.set_folder_path("FCL")
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print("player start", [round(x), round(y), round(gz)], "on", h[9].get_actor_label() if h[9] else None, "yaw", yaw)
