import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() in ("BP_Fig4", "HairProbe") or "PreviewActor" in a.get_actor_label():
        eas.destroy_actor(a)
print([a.get_actor_label() for a in eas.get_all_level_actors() if "Fig4" in a.get_actor_label()])
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
