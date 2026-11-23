"""The user's list of 2026-11-22 (docs/improvements16.txt; the plan docs/improvements16_plan.md): its editor stages by part.

  nanite_wild [check]   phase 4: every mesh the wilderness's biomes scatter (brokenspire's WildBiomes) made Nanite where it can be:
      none whose materials are see-through (translucent: Nanite draws opaque and masked only; one already Nanite is turned off);
      trees, bushes, grass, flowers, reeds and crops with the voxel shape preservation (Nanite foliage: a canopy's leaves kept as a
      volume far off instead of thinning away; the project's r.Nanite.Foliage must be on, or the engine drops it), rocks, logs, ice
      and the rest plain (a plain mesh already Nanite keeps its own setting). A material that moves its vertices (a world position
      offset) gets a maximum displacement of 200 cm (its bound, or Nanite culls a swaying leaf at its rest bounds); a mesh on such a
      material that cannot be bounded (a plugin's, which cannot be saved) is left as it was. Each mesh is judged by every biome entry
      that lays it: all their materials, voxel if any of them is a plant. check reports only.
  nanite_town [check]   phase 5: every mesh the game's maps' pieces use (brokenspire's towns and cities, the castle, the catacombs,
      the War Engine, the sewers, the spire's and Heaven's dungeons, the caves, martial_arts: a mesh is one asset shared by all), their
      moving parts (lids, doors) too, made Nanite where it can be, judged by every piece on every map that draws it (each piece's own
      material too), with the same bound on a vertex-moving material; one that cannot be (a see-through material) gets generated
      LODs (LOD1 at the screen size of 80 m, LOD2 at 200 m: the mesh's bounding radius over the distance, a 90 degree view) and
      Nanite turned off if it had it.
Run 869 after either (the Nanite and Voxels usages on their materials, for the packaged game). Each mesh changed is saved; a second
run changes nothing.
"""
import gc, importlib, os, sys, unreal

ARGS = sys.argv[1:]
PART = ARGS[0] if ARGS else ""
CHECK = "check" in ARGS
_d = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "..", "pipeline", "unreal")
if _d not in sys.path: sys.path.insert(0, _d)
import rd_nanite
rd_nanite = importlib.reload(rd_nanite)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAL = unreal.EditorAssetLibrary
MAPS = "/Game/RandomDungeon/Maps/"
BROKENSPIRE = MAPS + "brokenspire"
TOWN_MAPS = [BROKENSPIRE] + [MAPS + n for n in ("mistward_castle", "vel_morrath", "war_engine", "sewers", "kethrys_spire", "heaven_fortress", "caves", "martial_arts")]
VOXEL_KINDS = {"tree", "bush", "grass", "flower", "reed", "crop"}
BOUND_CM = 200.0
BOUNDED = set()   # bases bounded (or that would be, with check) this run: each counted once
# (a pack mesh's slot with no material of its own draws in the engine's grey grid, and the engine's material can take no usage:
#  the farms' pumpkin's "wood" slot, found by 888 nanite16's usage check, 2026-11-23; the pack's own wood for it)
SLOT_FIXES = {"/Game/BoneTemple/Meshes/SM_Pumpkin03": {1: "/Game/BoneTemple/Materials/MI_WoodDebris01_Var01"}}


def open_map(m):
    if not ues.get_editor_world().get_path_name().startswith(m + "."):
        unreal.SystemLibrary.execute_console_command(None, "obj gc")
        les.load_level(m)


def generator():
    return next((a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator)), None)


def own_mats(mesh):
    return [s.get_editor_property("material_interface") for s in mesh.get_editor_property("static_materials")]


def is_set(mesh, voxel):
    """Nanite already on with the shape preservation wanted (a setting that cannot be read is taken as set: it cannot be set either)"""
    if not mesh.get_editor_property("nanite_settings").enabled: return False
    v = rd_nanite.is_voxel(mesh)
    if v is None:
        print("NANITE16 shape preservation unreadable, left", mesh.get_path_name()); return True
    return v == voxel


def set_nanite(mesh, on, voxel=False):
    """Nanite on (with the shape preservation) or off; True if what was asked was taken (read back)"""
    ns = mesh.get_editor_property("nanite_settings")
    ns.set_editor_property("enabled", on)
    if on:
        try: ns.set_editor_property("shape_preservation", rd_nanite.shape_of(voxel))
        except Exception as e: print("NANITE16 no shape preservation on", mesh.get_path_name(), e)
    mesh.set_editor_property("nanite_settings", ns)
    EAL.save_loaded_asset(mesh, only_if_is_dirty=False)
    return is_set(mesh, voxel) if on else not mesh.get_editor_property("nanite_settings").enabled


def sway_bound(mats):
    """each vertex-moving material's maximum world position offset displacement (Nanite's bounds grow by it); kept where one is set.
    Returns (bounds set, False if one could not be bounded: a plugin's base material, which cannot be saved)"""
    n, ok = 0, True
    for b in {m.get_base_material().get_path_name(): m.get_base_material() for m in mats if m and m.get_base_material() and rd_nanite.moves_vertices(m)}.values():
        try:
            if b.get_editor_property("max_world_position_offset_displacement") > 0.0: continue
            if not b.get_path_name().startswith("/Game/"):
                print("NANITE16 cannot bound (not the project's)", b.get_path_name()); ok = False; continue
            if b.get_path_name() in BOUNDED: continue
            BOUNDED.add(b.get_path_name())
            if CHECK:
                print("NANITE16 would bound", b.get_path_name(), "(material attributes)" if b.get_editor_property("use_material_attributes") else "")
            else:
                b.set_editor_property("max_world_position_offset_displacement", BOUND_CM)
                unreal.MaterialEditingLibrary.recompile_material(b); EAL.save_loaded_asset(b, only_if_is_dirty=False)
            n += 1
        except Exception as e:
            print("NANITE16 no displacement bound on", b.get_path_name(), e); ok = False
    return n, ok


def lods(mesh, r_cm):
    """LOD1 at the screen size of 80 m, LOD2 at 200 m (radius over distance, a 90 degree view); half and a quarter of the triangles"""
    sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    opts = unreal.EditorScriptingMeshReductionOptions()
    s1, s2 = max(0.002, r_cm / 8000.0), max(0.001, r_cm / 20000.0)
    opts.set_editor_property("auto_compute_lod_screen_size", False)
    opts.set_editor_property("reduction_settings", [unreal.EditorScriptingMeshReductionSettings(1.0, 1.0), unreal.EditorScriptingMeshReductionSettings(0.5, s1), unreal.EditorScriptingMeshReductionSettings(0.25, s2)])
    return sms.set_lods(mesh, opts)


def fix_slots():
    for path, slots in SLOT_FIXES.items():
        mesh = unreal.load_asset(path)
        if not mesh: print("NANITE16 slot fix: no mesh", path); continue
        sm = list(mesh.get_editor_property("static_materials")); changed = False
        for i, mp in slots.items():
            cur = sm[i].get_editor_property("material_interface")
            if cur and cur.get_path_name().startswith("/Game/"): continue
            if CHECK: print("NANITE16 would give slot", i, "of", path, mp); continue
            s = sm[i]; s.set_editor_property("material_interface", unreal.load_asset(mp)); sm[i] = s; changed = True
        if changed:
            mesh.modify(); mesh.set_editor_property("static_materials", sm); EAL.save_loaded_asset(mesh, only_if_is_dirty=False)
            print("NANITE16 slot fixed", path)


def decide(path, mesh, mats, voxel, stats, name, with_lods):
    """one mesh, judged by every use's materials: LODs (the towns') and Nanite off if any is see-through, else bounded and made
    Nanite; a plain mesh already Nanite keeps its own shape preservation. Only the project's meshes: the engine's cube (the castle's
    invisible seals and cell blocks) is never changed or saved"""
    if not path.startswith("/Game/"):
        stats["not_ours"] = stats.get("not_ours", 0) + 1; return
    if rd_nanite.see_through(mats):
        stats["see_through"] += 1
        if CHECK: print("NANITE16 see-through", name, path, "(Nanite on: would turn it off)" if mesh.get_editor_property("nanite_settings").enabled else ""); return
        if mesh.get_editor_property("nanite_settings").enabled:
            set_nanite(mesh, False); stats["nanite_off"] += 1; print("NANITE16 Nanite off (see-through)", name, path)
        if with_lods and mesh.get_num_lods() < 3:
            n = lods(mesh, mesh.get_bounds().sphere_radius); EAL.save_loaded_asset(mesh, only_if_is_dirty=False); stats["lods"] += 1
            print("NANITE16 LODs", n, name, path)
        return
    nb, bounded = sway_bound(mats); stats["bounds"] += nb
    if not bounded and mesh.get_editor_property("nanite_settings").enabled:
        stats["nanite_unbounded"] += 1; print("NANITE16 Nanite with an unbounded sway (run 869, then this again)", name, path)
    if is_set(mesh, voxel) or (not voxel and mesh.get_editor_property("nanite_settings").enabled):
        stats["already"] += 1; return
    if not bounded: stats["unbounded"] += 1; print("NANITE16 left (its sway cannot be bounded)", name, path); return
    if CHECK: print("NANITE16 would make", "voxel" if voxel else "plain", name, path); return
    took = set_nanite(mesh, True, voxel)
    stats["made"] += 1
    if voxel: stats["voxel" if took else "voxel_failed"] += 1
    print("NANITE16 made", "voxel" if voxel else "plain", name, path, "" if took else "(its shape preservation not taken)")


def nanite_wild():
    open_map(BROKENSPIRE)
    fix_slots()
    g = generator()
    uses = {}          # mesh path -> [mesh, kinds, materials]: every biome entry that lays it
    for bm in g.get_editor_property("wild_biomes"):
        for f in bm.get_editor_property("foliage"):
            mesh = f.get_editor_property("mesh")
            if not mesh: continue
            u = uses.setdefault(mesh.get_path_name(), [mesh, set(), list(own_mats(mesh))])
            u[1].add(str(f.get_editor_property("kind"))); u[2] += [m for m in f.get_editor_property("materials") if m]
    g = None
    stats = {"made": 0, "already": 0, "see_through": 0, "nanite_off": 0, "voxel": 0, "voxel_failed": 0, "bounds": 0, "unbounded": 0, "nanite_unbounded": 0}
    for path, (mesh, kinds, mats) in uses.items():
        decide(path, mesh, mats, bool(kinds & VOXEL_KINDS), stats, "+".join(sorted(kinds)), False)
    print("NANITE16 wild", len(uses), "meshes:", stats)


def town_uses(m_, uses):
    """a map's generator pieces: each part's mesh with the materials it is drawn in there"""
    open_map(m_)
    g = generator()
    if not g: print("NANITE16 no generator on", m_); return
    for name, p in g.get_editor_property("pieces").items():
        pm = p.get_editor_property("material")
        for part, mesh in (("", p.mesh), (" lid/door", p.moving), (" second door", p.moving2)):
            if not mesh: continue
            u = uses.setdefault(mesh.get_path_name(), [mesh, set(), list(own_mats(mesh))])
            u[1].add(m_.split("/")[-1] + ":" + str(name) + part)
            if pm: u[2].append(pm)


def nanite_town():
    uses = {}
    for m_ in TOWN_MAPS:
        town_uses(m_, uses)
        gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    open_map(BROKENSPIRE)
    stats = {"made": 0, "already": 0, "see_through": 0, "nanite_off": 0, "lods": 0, "voxel": 0, "voxel_failed": 0, "bounds": 0, "unbounded": 0, "nanite_unbounded": 0}
    for path, (mesh, names, mats) in uses.items():
        names = sorted(names)
        decide(path, mesh, mats, False, stats, names[0] + (" (+%d)" % (len(names) - 1) if len(names) > 1 else ""), True)
    print("NANITE16 town", len(uses), "meshes over", len(TOWN_MAPS), "maps:", stats)


if PART == "nanite_wild": nanite_wild()
elif PART == "nanite_town": nanite_town()
else: print("944: parts nanite_wild, nanite_town")
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
