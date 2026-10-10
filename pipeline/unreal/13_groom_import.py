"""Import fig4's Alembic hair as a Groom and report its placement. Args: rx ry rz sx sy sz"""
import sys, unreal
rx, ry, rz, sx, sy, sz = map(float, sys.argv[1:7]) if len(sys.argv) > 6 else (90, 0, 0, 1, -1, 1)
t = unreal.AssetImportTask()
t.filename = r"E:\code\claude-ue5\claude_ue5\SourceArt\fig4\fig4_hair.abc"
t.destination_path = "/Game/Fig4/Hair"; t.destination_name = "GR_Fig4_Hair"
t.automated = True; t.replace_existing = True; t.save = True
opts = unreal.GroomImportOptions()
cs = opts.get_editor_property("conversion_settings")
cs.set_editor_property("rotation", unreal.Vector(rx, ry, rz))
cs.set_editor_property("scale", unreal.Vector(sx, sy, sz))
opts.set_editor_property("conversion_settings", cs)
t.options = opts
try:
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
except RuntimeError as e:
    print("(non-fatal)", str(e)[:150])
print("imported", list(t.imported_object_paths))
g = unreal.load_asset("/Game/Fig4/Hair/GR_Fig4_Hair")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "HairProbe": eas.destroy_actor(a)
ga = eas.spawn_actor_from_class(unreal.GroomActor, unreal.Vector(0, 0, 0))
ga.set_actor_label("HairProbe")
gc = ga.get_component_by_class(unreal.GroomComponent)
gc.set_editor_property("groom_asset", g)
o, e = ga.get_actor_bounds(False)
print("groom bounds origin", o, "extent", e)
eas.destroy_actor(ga)
