import sys, unreal
bias = float(sys.argv[1])
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "PPV_Studio":
        s = a.settings
        s.set_editor_property("override_auto_exposure_bias", True)
        s.set_editor_property("auto_exposure_bias", bias)
        a.set_editor_property("settings", s)
        print("bias", bias)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
