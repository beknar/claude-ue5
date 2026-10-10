import unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
try:
    les.editor_set_game_view(True)
    print("game view on")
except Exception as e:
    print("game view:", e)
