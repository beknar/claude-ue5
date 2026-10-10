import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
n = 0
for a in eas.get_all_level_actors():
    if isinstance(a, (unreal.PointLight, unreal.RectLight, unreal.SpotLight, unreal.SkyLight)):
        rc = a.get_editor_property("root_component")
        rc.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        n += 1
print("lights set movable:", n)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Fig4":
        for c in a.get_components_by_class(unreal.PrimitiveComponent):
            if c.get_name() in ("Hair", "Face", "Body"):
                b = c.get_editor_property("bounds") if False else None
                o, e, r = unreal.SystemLibrary.get_component_bounds(c)
                print(f"{c.get_name():5s} origin {o} extent {e} visible={c.is_visible()}")
        hair = [c for c in a.get_components_by_class(unreal.GroomComponent) if c.get_name() == "Hair"][0]
        print("hair groom", hair.groom_asset, "binding", hair.binding_asset, "attach parent", hair.get_attach_parent().get_name() if hair.get_attach_parent() else None)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
