import os, unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
print("cine on disk:", os.path.exists(r"E:\code\claude-ue5\claude_ue5\Content\Fig4\Maps\L_Fig4_Outdoor_Cine.umap"))
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if w.get_path_name().startswith("/Game/Fig4/Maps/L_Fig4_Outdoor."):
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == "Fig4_Demo": eas.destroy_actor(a)
    if not [a for a in eas.get_all_level_actors() if isinstance(a, unreal.PlayerStart)]:
        ps = eas.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, 0, 110), unreal.Rotator(pitch=0, yaw=0, roll=0))
        ps.set_actor_label("PlayerStart")
    les.save_current_level()
    print("playable map restored:", [a.get_actor_label() for a in eas.get_all_level_actors() if isinstance(a, (unreal.PlayerStart, unreal.Character))])
try: les.load_level("/Game/Fig4/Maps/L_Fig4_Outdoor_Cine")
except RuntimeError as e: print("(non-fatal)", str(e)[:120])
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
print("editing", w.get_path_name(), [a.get_actor_label() for a in eas.get_all_level_actors() if isinstance(a, (unreal.PlayerStart, unreal.Character))])
