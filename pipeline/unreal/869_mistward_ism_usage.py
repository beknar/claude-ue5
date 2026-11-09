"""mistward_castle, brokenspire, vel_morrath, war_engine, sewers, kethrys_spire and heaven_fortress for a packaged game: every material their generators' pieces are drawn with gets the InstancedStaticMeshes
usage. The sections draw every piece through instanced meshes (ARDSection's HISMs). The editor adds a missing usage flag
while it plays, so play in the editor looked right; a packaged game has no shaders for it and draws the default material
(the packaged game's log: "Material ... missing usage flag InstancedStaticMeshes! Default Material will be used in game";
370's M_KitColor: iron, clay, dough, apples, stew, embers and flames grey). The flag is set on each base material (an
instance takes its parent's), the material recompiled and saved. Engine materials are reported, not changed; nothing outside
the project (/Game/) is written: a plugin's base material that our pieces need (the SpeedTree importer's SpeedTreeMaster, under
two of the wilderness's Nanite plants) is copied into the project (PluginCopies), the usage set on the copy, and the project's
instances made from it pointed at the copy (a copy made once is kept: delete PluginCopies to make the copies again).
The hero menu (mistward_castle_select) the same way for its placed meshes: a Nanite mesh's materials need the Nanite usage
(the packaged menu: Fig4's studio cyclorama and plinth materials "missing usage flag Nanite").
Each map is loaded once (an `obj gc` before each load). Run before pipeline/package_mistward.ps1; it ends on mistward_castle.
Args: [check] (report only)"""
import sys, unreal
CHECK = len(sys.argv) > 1 and sys.argv[1] == "check"
MAP = "/Game/RandomDungeon/Maps/mistward_castle"; MENU = MAP + "_select"; VEL = "/Game/RandomDungeon/Maps/vel_morrath"
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def open_map(m):
    if not ues.get_editor_world().get_path_name().startswith(m + "."):
        unreal.SystemLibrary.execute_console_command(None, "obj gc")
        les.load_level(m)
OWN, COPIES = "/Game/", "/Game/RandomDungeon/Materials/PluginCopies"
kids = {}          # base material path -> the instances whose parent it is (among the materials our pieces draw with)
via = {}           # base material path -> the project's instances whose chain to it passes through an instance outside the project
def note(mi):
    x = mi
    while isinstance(x, unreal.MaterialInstance):
        par = x.get_editor_property("parent")
        if par is not None and not isinstance(par, unreal.MaterialInstance):
            kids.setdefault(par.get_path_name(), set()).add(x)
            if mi.get_path_name().startswith(OWN) and not x.get_path_name().startswith(OWN): via.setdefault(par.get_path_name(), set()).add(mi)
            return
        x = par
def bases_of(mesh, mats=None):
    out = []
    for mi in (mats or [s.get_editor_property("material_interface") for s in mesh.get_editor_property("static_materials")]):
        b = mi.get_base_material() if mi else None
        if b: out.append(b); note(mi)
    return out
need = {}          # base material path -> (material, set of usage properties it needs)
def want(b, prop): need.setdefault(b.get_path_name(), (b, set()))[1].add(prop)
def use(mesh, mats=None):
    """a mesh drawn through instanced meshes: its materials' bases get that usage, and the Nanite usage if the mesh is Nanite
    (the packaged town drew two of the wilderness's plants, Medieval_Lake_Village's MI_Leaves11 and MI_RiverBush01, in the
    default material: "missing usage flag Nanite", the Development package of 2026-11-06)"""
    nan = mesh.get_editor_property("nanite_settings").enabled
    for b in bases_of(mesh, mats):
        want(b, "used_with_instanced_static_meshes")
        if nan: want(b, "used_with_nanite")
meshes, overrides, nwild, nmenu = set(), 0, 0, 0
def pieces_of(m_):
    """a map's generator pieces: each mesh, and a piece drawn in a material of its own (FRDPiece::Material: the burned houses'
    MI_Wood_Burnt, through HismsMat) in that material too (the PR review's find: only the meshes' own were checked)"""
    global overrides
    open_map(m_)
    g_ = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    for p in g_.get_editor_property("pieces").values():
        if not p.mesh: continue
        meshes.add(p.mesh); use(p.mesh)
        mat = p.get_editor_property("material")
        if mat: overrides += 1; use(p.mesh, [mat])
    return g_
# Brokenspire's pieces (2026-11-02: the castle's new walls, towers and stair; the town's houses; the holy city's): its generator's
# own table; and the wilderness on it: its plants and rocks are instanced too, the list of 2026-11-04's swaying grass and bushes
# in materials of their own (FRDWildFoliage::Materials), and the weather's rain and snow drops (instanced planes)
g_ = pieces_of("/Game/RandomDungeon/Maps/brokenspire")
for bm in g_.get_editor_property("wild_biomes"):
    for f in bm.get_editor_property("foliage"):
        fm = f.get_editor_property("mesh")
        if not fm: continue
        nwild += 1
        use(fm)
        own = [m for m in f.get_editor_property("materials") if m]
        if own: use(fm, own)
dm = g_.get_editor_property("drop_mesh")
for k in ("rain_drop_material", "snow_drop_material"):
    dmat = g_.get_editor_property(k)
    if dm and dmat: use(dm, [dmat])
# (Vel Morrath's catacombs (2026-11-06, 891): the copy of the castle with its crypt pieces in a table of its own)
pieces_of(VEL)
# (The War Engine and the sewers (2026-11-07, 895 / 897): copies of the castle with the Foundry's and the damp Sewer's pieces
# and props; a monster drawn in a material of its own (FRDMonsterDef::Material: the iron golem's rusted iron, a static pack's
# material) needs the skeletal-mesh usage)
nskel = 0
for m_ in ("/Game/RandomDungeon/Maps/war_engine", "/Game/RandomDungeon/Maps/sewers", "/Game/RandomDungeon/Maps/kethrys_spire", "/Game/RandomDungeon/Maps/heaven_fortress"):
    g_ = pieces_of(m_)
    for d in g_.get_editor_property("monsters"):
        mm = d.get_editor_property("material")
        if mm and mm.get_base_material():
            nskel += 1; note(mm); want(mm.get_base_material(), "used_with_skeletal_mesh")
# the menu: its placed meshes; Nanite ones need the Nanite usage
open_map(MENU)
for a in eas.get_all_level_actors():
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.get_editor_property("static_mesh")
        if not m or not m.get_editor_property("nanite_settings").enabled: continue
        nmenu += 1
        for b in bases_of(m, [c.get_material(i) for i in range(c.get_num_materials())]): want(b, "used_with_nanite")
# the castle last: the script ends on it
g_ = pieces_of(MAP)
del g_
print("ISMUSAGE pieces in materials of their own:", overrides, "| the wilderness's plants:", nwild, "| monsters in materials of their own:", nskel)
# (the editor sets a usage it needs while it draws, in memory only: the menu's two read true here while the files on disk,
# and so the package, did not have them. Such a material is saved too.)
# (they did not show as dirty either: the menu's Nanite materials are saved every run, the castle's when one is dirty)
# (every one is saved: the fountain's M_Fountain read true here, was not dirty, and the packaged game drew it in the default
# material ("missing usage flag InstancedStaticMeshes", the castle run of 2026-11-01): the flag was the editor's, in memory)
# (a plugin's base material (the SpeedTree importer's, 2026-11-06): its file is in the engine's install, not the project: a
# project copy carries the usages, and the project's instances made from it are pointed at the copy)
copied = []
for p in sorted(p for p in need if not p.startswith(OWN) and not p.startswith("/Engine/")):
    b, props = need[p]
    ins = sorted((m for m in kids.get(p, ()) if m.get_path_name().startswith(OWN)), key=lambda m: m.get_path_name())
    for m in sorted(via.get(p, ()), key=lambda m: m.get_path_name()):
        print("ISMUSAGE  ", "plugin material reached through a plugin's own instance (left: copy that instance too)", p, "<-", m.get_path_name())
    if CHECK or not ins:
        print("ISMUSAGE  ", "plugin material", "(check: left)" if CHECK else "(no project instance of it: left)", p); continue
    # (a copy carries where it came from (its metadata tag RDCopyOf): two plugins' materials of one name get copies of their own)
    cp, k = None, 1
    while cp is None:
        dst = COPIES + "/" + b.get_name() + ("" if k == 1 else f"_{k}")
        if not unreal.EditorAssetLibrary.does_asset_exist(dst):
            cp = unreal.EditorAssetLibrary.duplicate_asset(p.split(".")[0], dst)
            if cp is None: break
            unreal.EditorAssetLibrary.set_metadata_tag(cp, "RDCopyOf", p)
        else:
            c_ = unreal.load_asset(dst); of = unreal.EditorAssetLibrary.get_metadata_tag(c_, "RDCopyOf")
            if of == p or (not of and k == 1): cp = c_; unreal.EditorAssetLibrary.set_metadata_tag(cp, "RDCopyOf", p)
        k += 1
    if cp is None:
        print("ISMUSAGE  ", "plugin material NOT copied (the copy failed: its instances left as they were)", p); continue
    for m in ins:
        if m.get_editor_property("parent") != cp:
            unreal.MaterialEditingLibrary.set_material_instance_parent(m, cp)
            unreal.EditorAssetLibrary.save_loaded_asset(m, only_if_is_dirty=False)
    del need[p]
    for prop in props: want(cp, prop)
    copied.append((p, dst, len(ins)))
for p, dst, n in copied: print("ISMUSAGE  ", "plugin material copied", p, "->", dst, "|", n, "instances pointed at it")
unsaved = sorted(p for p, (b, props) in need.items() if p.startswith(OWN))
if not CHECK:
    for p in unsaved: unreal.EditorAssetLibrary.save_loaded_asset(need[p][0], only_if_is_dirty=False)
for p in unsaved: print("ISMUSAGE  ", "unsaved usage", "saved" if not CHECK else "(check: left)", p)
missing = sorted((p, prop) for p, (b, props) in need.items() for prop in props if not b.get_editor_property(prop))
fixed = []
if not CHECK:
    for p in sorted({p for p, prop in missing if p.startswith(OWN)}):
        b = need[p][0]; props = [prop for q, prop in missing if q == p]
        for prop in props: b.set_editor_property(prop, True)
        unreal.MaterialEditingLibrary.recompile_material(b)
        unreal.EditorAssetLibrary.save_loaded_asset(b, only_if_is_dirty=False)
        fixed += [(p, prop) for prop in props]
print(f"ISMUSAGE castle meshes {len(meshes)} | menu Nanite components {nmenu} | base materials {len(need)} | missing {len(missing)} | set {len(fixed)}")
for p, prop in missing: print("ISMUSAGE  ", "set" if (p, prop) in fixed else ("outside the project, left" if not p.startswith(OWN) else "missing"), prop, p)
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
