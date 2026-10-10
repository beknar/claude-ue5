"""Attach a dedicated groom actor (fig4's hair) to Fig4's Face component with the binding."""
import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
fig = next(a for a in eas.get_all_level_actors() if a.get_actor_label() == "Fig4")
face = next(c for c in fig.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == "Face")
for gc in fig.get_components_by_class(unreal.GroomComponent):
    if gc.get_name() == "Hair" and gc.groom_asset is not None:
        gc.set_editor_property("groom_asset", None); gc.set_editor_property("binding_asset", None)
# editing a component re-runs the MetaHuman construction script, which rebuilds components: refetch
fig = next(a for a in eas.get_all_level_actors() if a.get_actor_label() == "Fig4")
face = next(c for c in fig.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == "Face")
for a in eas.get_all_level_actors():
    if a.get_actor_label() in ("HairProbe", "Fig4_Hair"):
        eas.destroy_actor(a)
binds = sorted(a for a in unreal.EditorAssetLibrary.list_assets("/Game/Fig4/Hair", recursive=False) if "Binding" in a)
binding = unreal.load_asset(binds[-1].split(".")[0])
ga = eas.spawn_actor_from_class(unreal.GroomActor, fig.get_actor_location(), fig.get_actor_rotation())
ga.set_actor_label("Fig4_Hair")
gc = ga.get_component_by_class(unreal.GroomComponent)
gc.set_editor_property("groom_asset", unreal.load_asset("/Game/Fig4/Hair/GR_Fig4_Hair"))
gc.set_editor_property("binding_asset", binding)
gc.set_material(0, unreal.load_asset("/Game/Fig4/Hair/MI_Fig4_Hair"))
ga.attach_to_component(face, "", unreal.AttachmentRule.SNAP_TO_TARGET, unreal.AttachmentRule.SNAP_TO_TARGET,
                       unreal.AttachmentRule.KEEP_WORLD, False)
print("hair actor attached to", face.get_name(), "binding", binding.get_name())
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
