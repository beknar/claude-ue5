"""castle_level: copy of the Medieval Fantasy Village showcase map (the Fab pack's own art-directed landscape, houses,
bridge, river, foliage, Niagara leaves, sky/fog/post) with the FF2 anime character as the playable pawn.
Args: spawn x y yaw"""
import sys, unreal
eal = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SRC = "/Game/Medieval_Fantasy_Village/Levels/L_Medieval_Town"; DST = "/Game/Castle/Maps/castle_level"
x, y, yaw = (float(v) for v in sys.argv[1:4]) if len(sys.argv) >= 4 else (1800.0, -1200.0, 90.0)
# the map itself is a file copy of L_Medieval_Town.umap -> Content/Castle/Maps/castle_level.umap made with the editor
# closed (EditorAssetLibrary.duplicate_asset on a map leaves the copy's world in memory and the next level load hits a
# fatal world-leak check)
assert eal.does_asset_exist(DST), "copy L_Medieval_Town.umap to Content/Castle/Maps/castle_level.umap first"
les.load_level(DST)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
ws = w.get_world_settings()
ws.set_editor_property("default_game_mode", unreal.load_asset("/Game/FF2/Game/BP_FF2GameMode").generated_class())
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.PlayerStart): eas.destroy_actor(a)
hit = unreal.SystemLibrary.line_trace_single(w, unreal.Vector(x, y, 20000), unreal.Vector(x, y, -20000), unreal.TraceTypeQuery.ECC_VISIBILITY,
                                             True, [], unreal.DrawDebugTrace.NONE, True).to_tuple()
gz = hit[4].z if (hit[0] or hit[1]) else 0.0
ps = eas.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(x, y, gz + 95.0), unreal.Rotator(pitch=0, yaw=yaw, roll=0))
ps.set_actor_label("FF2_Start")
print("player start", [round(v) for v in (x, y, gz + 95)], "ground hit", hit[9].get_name() if hit[9] else None, "yaw", yaw)
print("game mode", ws.get_editor_property("default_game_mode").get_name())
les.save_current_level()
print("saved", w.get_path_name())
