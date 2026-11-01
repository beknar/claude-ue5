"""mistward_castle for a packaged game: every material its generator's pieces are drawn with gets the InstancedStaticMeshes
usage. The sections draw every piece through instanced meshes (ARDSection's HISMs). The editor adds a missing usage flag
while it plays, so play in the editor looked right; a packaged game has no shaders for it and draws the default material
(the packaged game's log: "Material ... missing usage flag InstancedStaticMeshes! Default Material will be used in game";
370's M_KitColor: iron, clay, dough, apples, stew, embers and flames grey). The flag is set on each base material (an
instance takes its parent's), the material recompiled and saved. Engine materials are reported, not changed.
The hero menu (mistward_castle_select) the same way for its placed meshes: a Nanite mesh's materials need the Nanite usage
(the packaged menu: Fig4's studio cyclorama and plinth materials "missing usage flag Nanite").
Run before pipeline/package_mistward.ps1; it ends on mistward_castle. Args: [check] (report only)"""
import sys, unreal
CHECK = len(sys.argv) > 1 and sys.argv[1] == "check"
MAP = "/Game/RandomDungeon/Maps/mistward_castle"; MENU = MAP + "_select"
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def open_map(m):
    if not ues.get_editor_world().get_path_name().startswith(m + "."): les.load_level(m)
def bases_of(mesh, mats=None):
    out = []
    for mi in (mats or [s.get_editor_property("material_interface") for s in mesh.get_editor_property("static_materials")]):
        b = mi.get_base_material() if mi else None
        if b: out.append(b)
    return out
need = {}          # base material path -> (material, set of usage properties it needs)
def want(b, prop): need.setdefault(b.get_path_name(), (b, set()))[1].add(prop)
# the castle: every generator piece through instanced meshes
open_map(MAP)
gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
meshes = {p.mesh for p in gen.get_editor_property("pieces").values() if p.mesh}
for m in meshes:
    for b in bases_of(m): want(b, "used_with_instanced_static_meshes")
# the menu: its placed meshes; Nanite ones need the Nanite usage
open_map(MENU)
nmenu = 0
for a in eas.get_all_level_actors():
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.get_editor_property("static_mesh")
        if not m or not m.get_editor_property("nanite_settings").enabled: continue
        nmenu += 1
        for b in bases_of(m, [c.get_material(i) for i in range(c.get_num_materials())]): want(b, "used_with_nanite")
# (the editor sets a usage it needs while it draws, in memory only: the menu's two read true here while the files on disk,
# and so the package, did not have them. Such a material is saved too.)
# (they did not show as dirty either: the menu's Nanite materials are saved every run, the castle's when one is dirty)
# (every one is saved: the fountain's M_Fountain read true here, was not dirty, and the packaged game drew it in the default
# material ("missing usage flag InstancedStaticMeshes", the castle run of 2026-11-01): the flag was the editor's, in memory)
unsaved = sorted(p for p, (b, props) in need.items() if not p.startswith("/Engine/"))
if not CHECK:
    for p in unsaved: unreal.EditorAssetLibrary.save_loaded_asset(need[p][0], only_if_is_dirty=False)
for p in unsaved: print("ISMUSAGE  ", "unsaved usage", "saved" if not CHECK else "(check: left)", p)
open_map(MAP)
missing = sorted((p, prop) for p, (b, props) in need.items() for prop in props if not b.get_editor_property(prop))
fixed = []
if not CHECK:
    for p, prop in missing:
        if p.startswith("/Engine/"): continue
        b = need[p][0]
        b.set_editor_property(prop, True)
        unreal.MaterialEditingLibrary.recompile_material(b)
        unreal.EditorAssetLibrary.save_loaded_asset(b, only_if_is_dirty=False)
        fixed.append((p, prop))
print(f"ISMUSAGE castle meshes {len(meshes)} | menu Nanite components {nmenu} | base materials {len(need)} | missing {len(missing)} | set {len(fixed)}")
for p, prop in missing: print("ISMUSAGE  ", "set" if (p, prop) in fixed else ("engine, left" if p.startswith("/Engine/") else "missing"), prop, p)
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
