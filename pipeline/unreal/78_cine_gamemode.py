"""Cine map: world GameMode = MoviePipelineGameMode (no player pawn / template controller)."""
import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert "_Cine" in w.get_path_name(), w.get_path_name()
ws = w.get_world_settings()
cls = unreal.load_class(None, "/Script/MovieRenderPipelineCore.MoviePipelineGameMode")
print("class", cls)
ws.set_editor_property("default_game_mode", cls)
print("world game mode", ws.get_editor_property("default_game_mode"))
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
