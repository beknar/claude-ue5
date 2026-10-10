"""Record the placement of every crate/barrel prop in the pack's L_Medieval_Town (the source of castle_level) to
SourceArt/castle_interactive/village_containers.json, so 340 can always (re)create the openable versions."""
import json, unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les.load_level("/Game/Medieval_Fantasy_Village/Levels/L_Medieval_Town")
NAMES = {"SM_crate_01", "SM_crate_02", "SM_barrel_01", "SM_barrel_02"}
rows = []
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh and a.static_mesh_component.static_mesh.get_name() in NAMES:
        l, r, s = a.get_actor_location(), a.get_actor_rotation(), a.get_actor_scale3d()
        rows.append({"mesh": a.static_mesh_component.static_mesh.get_name(), "loc": [l.x, l.y, l.z], "rot": [r.roll, r.pitch, r.yaw], "scale": [s.x, s.y, s.z]})
json.dump(rows, open(r"E:\code\claude-ue5\claude_ue5\SourceArt\castle_interactive\village_containers.json", "w"), indent=1)
print("recorded", len(rows), {n: sum(1 for r_ in rows if r_["mesh"] == n) for n in NAMES})
les.load_level("/Game/Castle/Maps/castle_level")
rows = None; import gc; gc.collect()
