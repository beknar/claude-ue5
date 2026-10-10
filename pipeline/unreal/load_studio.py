import unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
print("current world:", w.get_path_name())
if "L_Fig4_Studio" not in w.get_path_name():
    try:
        les.load_level("/Game/Fig4/Maps/L_Fig4_Studio")
    except RuntimeError as e:
        print("(non-fatal)", str(e)[:100])
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
print("world now:", unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name())
print([a.get_actor_label() for a in eas.get_all_level_actors() if "Fig4" in a.get_actor_label()])
