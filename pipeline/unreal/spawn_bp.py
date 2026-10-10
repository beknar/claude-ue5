"""Spawn BP_Fig4 at a location (removing old instances) and report its components. Args: x y z yaw"""
import sys, unreal
x, y, z, yaw = map(float, sys.argv[1:5])
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    lab = a.get_actor_label()
    if lab.startswith("BP_Fig4") or "PreviewActor" in lab or lab.startswith("REVIEW_"):
        eas.destroy_actor(a)
bp = unreal.load_asset("/Game/MetaHumans/Fig4/BP_Fig4")
a = eas.spawn_actor_from_object(bp, unreal.Vector(x, y, z), unreal.Rotator(0, yaw, 0))
a.set_actor_label("BP_Fig4")
for c in a.get_components_by_class(unreal.SceneComponent):
    extra = ""
    if isinstance(c, unreal.SkeletalMeshComponent) and c.get_skeletal_mesh_asset():
        sm = c.get_skeletal_mesh_asset()
        extra = f"{sm.get_name()} bones={c.get_num_bones()}"
    if isinstance(c, unreal.GroomComponent):
        extra = f"groom={c.groom_asset.get_name() if c.groom_asset else None}"
    print(" ", type(c).__name__, c.get_name(), extra)
