"""Fantasy Castle pack meshes ship with ONE convex hull as their simple collision, so the player walks on an invisible shrink-wrap:
over the island mountain (SM_Mount2), on top of the arched bridge's railings, and every doorway / arch / terrace is sealed.
For the terrain and architecture meshes used in fantasy_castle_level, collide with the real triangles instead
(CTF_USE_COMPLEX_AS_SIMPLE on the asset's body setup). Foliage, grass, cloud cards, water and backdrop mountains keep theirs.
Args: [dry]"""
import sys, re, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
SKIP = re.compile(r"(?i)tree|spruce|pine|grass|bush|cloud|dune|stub|grpace|plane$|^SM_Small_N1$|fog|leaf|flower|lightbeam")
DRY = "dry" in sys.argv
meshes = {}
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh:
        sm = a.static_mesh_component.static_mesh
        if sm.get_path_name().startswith("/Game/FantasyCastle/") and not SKIP.search(sm.get_name()): meshes[sm.get_path_name()] = sm
changed = []
for p, sm in sorted(meshes.items()):
    bs = sm.get_editor_property("body_setup")
    if bs and bs.get_editor_property("collision_trace_flag") != unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE:
        changed.append(sm.get_name())
        if not DRY:
            sm.modify(); bs.modify(); bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            eal.save_loaded_asset(sm, only_if_is_dirty=False)
print("dry run:" if DRY else "complex-as-simple:", len(changed), "of", len(meshes), sorted(changed))
