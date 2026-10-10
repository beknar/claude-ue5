"""Force LOD0 on fig4's face/body/outfit so close-up renders never drop to lower LODs."""
import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() in ("Fig4", "Fig4_Outfit"):
        for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
            try:
                c.set_forced_lod(1)      # 1 = LOD0
                print(a.get_actor_label(), c.get_name(), "forced LOD0")
            except Exception as e:
                print("lod", c.get_name(), str(e)[:80])
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
