import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "HairProbe": eas.destroy_actor(a)
ga = eas.spawn_actor_from_class(unreal.GroomActor, unreal.Vector(60, 0, 6))
ga.set_actor_label("HairProbe")
gc = ga.get_component_by_class(unreal.GroomComponent)
gc.set_editor_property("groom_asset", unreal.load_asset("/Game/Fig4/Hair/GR_Fig4_Hair"))
gc.set_material(0, unreal.load_asset("/Game/Fig4/Hair/MI_Fig4_Hair"))
print("probe spawned")
