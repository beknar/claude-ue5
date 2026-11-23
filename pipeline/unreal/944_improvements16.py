"""The user's list of 2026-11-22 (docs/improvements16.txt; the plan docs/improvements16_plan.md): its editor stages by part.

  nanite_wild [skip=<kind>+<kind>] [check]   phase 4: every mesh the wilderness's biomes scatter (brokenspire's WildBiomes) made Nanite
      where it can be: none whose materials are see-through (translucent: Nanite draws opaque and masked only); trees, bushes,
      grass, flowers, reeds and crops with the voxel shape preservation (UE 5.8's Nanite foliage: a canopy's leaves kept as a volume
      far off instead of thinning away), rocks, logs, ice and the rest plain; the kinds named after skip= left as they are (the
      measure decides per kind: Nanite foliage can cost more than instances with LODs); a material that moves its vertices (a world
      position offset) gets a maximum displacement (its bound, or Nanite culls a swaying leaf at its rest bounds; 200 cm, enough for
      any sway here); a mesh on such a material that cannot be bounded (a plugin's, which cannot be saved) is left as it was. A mesh
      already Nanite with the shape preservation it should have is left untouched. check reports only.
  nanite_town [check]   phase 5: every mesh the towns' pieces use (brokenspire's Pieces: the towns, the holy, forge, port, mage and modern
      cities, their furniture and props; the castle's and the dungeons' share many of them), and their moving parts (lids, doors),
      made Nanite where it can be, with the same bound on a swaying material; one that cannot (a see-through material) gets
      generated LODs: LOD1 at the screen size of 80 m, LOD2 at 200 m (screen size = the mesh's
      bounding radius over the distance, for a 90 degree view).
Run 869 after either (the Nanite usage on their materials, for the packaged game). Each mesh changed is saved.
"""
import sys, unreal

ARGS = sys.argv[1:]
PART = ARGS[0] if ARGS else ""
CHECK = "check" in ARGS
SKIP = set()
for a in ARGS:
    if a.startswith("skip="): SKIP = set(a[5:].split("+"))
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAL = unreal.EditorAssetLibrary
BROKENSPIRE = "/Game/RandomDungeon/Maps/brokenspire"
VOXEL_KINDS = {"tree", "bush", "grass", "flower", "reed", "crop"}
SWAY_KINDS = {"tree", "bush", "grass", "flower", "reed", "crop"}


def open_map(m):
    if not ues.get_editor_world().get_path_name().startswith(m + "."):
        unreal.SystemLibrary.execute_console_command(None, "obj gc")
        les.load_level(m)


def generator():
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


def mats_of(mesh, extra=()):
    out = [s.get_editor_property("material_interface") for s in mesh.get_editor_property("static_materials")]
    return [m for m in list(out) + list(extra) if m]


def blend_of(m):
    """the blend mode a material is drawn with: an instance's own override (up its parents) before its base material's"""
    x = m
    while isinstance(x, unreal.MaterialInstance):
        try:
            o = x.get_editor_property("base_property_overrides")
            if o.get_editor_property("override_blend_mode"): return o.get_editor_property("blend_mode")
        except Exception:
            pass
        x = x.get_editor_property("parent")
    b = m.get_base_material()
    return b.get_editor_property("blend_mode") if b else unreal.BlendMode.BLEND_OPAQUE


def see_through(mats):
    """a material drawn translucent (or additive, modulate): Nanite cannot draw it"""
    return any(blend_of(m) not in (unreal.BlendMode.BLEND_OPAQUE, unreal.BlendMode.BLEND_MASKED) for m in mats)


def moves_vertices(m, guess):
    """whether a material's base offsets its vertices (world position offset connected); guess when it cannot be read"""
    b = m.get_base_material()
    if not b: return False
    try:
        if b.get_editor_property("use_material_attributes"): return guess
        return unreal.MaterialEditingLibrary.get_material_property_input_node(b, unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET) is not None
    except Exception:
        return guess


def shape_of(voxel):
    return unreal.NaniteShapePreservation.VOXELIZE if voxel else unreal.NaniteShapePreservation.NONE


def is_set(mesh, voxel):
    """Nanite already on with the shape preservation wanted"""
    ns = mesh.get_editor_property("nanite_settings")
    if not ns.enabled: return False
    try:
        return ns.get_editor_property("shape_preservation") == shape_of(voxel)
    except Exception:
        return not voxel


def set_nanite(mesh, voxel):
    """Nanite on with the shape preservation; True if the shape preservation was taken (read back)"""
    ns = mesh.get_editor_property("nanite_settings")
    ns.set_editor_property("enabled", True)
    try:
        ns.set_editor_property("shape_preservation", shape_of(voxel))
    except Exception as e:
        print("NANITE16 no shape preservation on", mesh.get_path_name(), e)
    mesh.set_editor_property("nanite_settings", ns)
    return is_set(mesh, voxel)


def sway_bound(mats, guess, cm=200.0):
    """each vertex-moving material's maximum world position offset displacement (Nanite's bounds grow by it); left if one is set.
    Returns (bounds set, False if one could not be bounded: a plugin's base material, which cannot be saved)"""
    n, ok = 0, True
    for m in mats:
        if not moves_vertices(m, guess): continue
        b = m.get_base_material()
        try:
            # (60 cm is what this stage's first run set (2026-11-23): raised to the bound now wanted)
            if b.get_editor_property("max_world_position_offset_displacement") > 0.0 and abs(b.get_editor_property("max_world_position_offset_displacement") - 60.0) > 0.01: continue
            if not b.get_path_name().startswith("/Game/"):
                print("NANITE16 cannot bound (not the project's)", b.get_path_name()); ok = False; continue
            if not CHECK:
                b.set_editor_property("max_world_position_offset_displacement", cm)
                unreal.MaterialEditingLibrary.recompile_material(b); EAL.save_loaded_asset(b, only_if_is_dirty=False)
            n += 1
        except Exception as e:
            print("NANITE16 no displacement bound on", b.get_path_name(), e); ok = False
    return n, ok


# (a pack mesh's slot with no material of its own draws in the engine's grey grid, and as Nanite needs usages the engine's material
#  cannot be given: the farms' pumpkin's "wood" slot, found by 888 nanite16's usage check, 2026-11-23; the pack's own wood for it)
SLOT_FIXES = {"/Game/BoneTemple/Meshes/SM_Pumpkin03": {1: "/Game/BoneTemple/Materials/MI_WoodDebris01_Var01"}}


def fix_slots():
    n = 0
    for path, slots in SLOT_FIXES.items():
        mesh = unreal.load_asset(path)
        if not mesh: print("NANITE16 slot fix: no mesh", path); continue
        sm = list(mesh.get_editor_property("static_materials"))
        changed = False
        for i, mp in slots.items():
            cur = sm[i].get_editor_property("material_interface")
            if cur and cur.get_path_name().startswith("/Game/"): continue
            if CHECK: print("NANITE16 would give slot", i, "of", path, mp); continue
            s = sm[i]; s.set_editor_property("material_interface", unreal.load_asset(mp)); sm[i] = s; changed = True
        if changed:
            mesh.modify(); mesh.set_editor_property("static_materials", sm); EAL.save_loaded_asset(mesh, only_if_is_dirty=False); n += 1
            print("NANITE16 slot fixed", path)
    return n


def nanite_wild():
    open_map(BROKENSPIRE)
    fix_slots()
    g = generator()
    seen, stats = set(), {"made": 0, "already": 0, "see_through": 0, "skipped": 0, "voxel": 0, "bounds": 0, "unbounded": 0, "voxel_failed": 0}
    for bm in g.get_editor_property("wild_biomes"):
        for f in bm.get_editor_property("foliage"):
            mesh = f.get_editor_property("mesh")
            if not mesh or mesh.get_path_name() in seen: continue
            seen.add(mesh.get_path_name())
            kind = str(f.get_editor_property("kind"))
            mats = mats_of(mesh, [m for m in f.get_editor_property("materials") if m])
            if kind in SKIP: stats["skipped"] += 1; print("NANITE16 skip (asked)", kind, mesh.get_path_name()); continue
            if see_through(mats): stats["see_through"] += 1; print("NANITE16 see-through, left", kind, mesh.get_path_name()); continue
            voxel = kind in VOXEL_KINDS
            nb, bounded = sway_bound(mats, kind in SWAY_KINDS); stats["bounds"] += nb
            # (a plugin's base is bounded through 869's project copy, which its instances point at once 869 has run)
            if not bounded and mesh.get_editor_property("nanite_settings").enabled:
                stats["nanite_unbounded"] = stats.get("nanite_unbounded", 0) + 1; print("NANITE16 Nanite with an unbounded sway (run 869, then this again)", kind, mesh.get_path_name())
            # (a plain kind's mesh already Nanite is left as it is: its shape preservation is its own)
            if is_set(mesh, voxel) or (not voxel and mesh.get_editor_property("nanite_settings").enabled): stats["already"] += 1; continue
            if not bounded: stats["unbounded"] += 1; print("NANITE16 left (its sway cannot be bounded)", kind, mesh.get_path_name()); continue
            if CHECK: print("NANITE16 would make", "voxel" if voxel else "plain", kind, mesh.get_path_name()); continue
            took = set_nanite(mesh, voxel)
            EAL.save_loaded_asset(mesh, only_if_is_dirty=False)
            stats["made"] += 1
            if voxel: stats["voxel" if took else "voxel_failed"] += 1
            print("NANITE16 made", "voxel" if voxel else "plain", kind, mesh.get_path_name(), "" if took else "(its shape preservation not taken)")
    print("NANITE16 wild", len(seen), "meshes:", stats)


def lods(mesh, r_cm):
    """LOD1 at the screen size of 80 m, LOD2 at 200 m (radius over distance, a 90 degree view); half and a quarter of the triangles"""
    sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    opts = unreal.EditorScriptingMeshReductionOptions()
    s1, s2 = max(0.002, r_cm / 8000.0), max(0.001, r_cm / 20000.0)
    opts.set_editor_property("auto_compute_lod_screen_size", False)
    opts.set_editor_property("reduction_settings", [unreal.EditorScriptingMeshReductionSettings(1.0, 1.0), unreal.EditorScriptingMeshReductionSettings(0.5, s1), unreal.EditorScriptingMeshReductionSettings(0.25, s2)])
    return sms.set_lods(mesh, opts)


def nanite_town():
    open_map(BROKENSPIRE)
    g = generator()
    seen, stats = set(), {"made": 0, "already": 0, "lods": 0, "no_mesh": 0, "bounds": 0, "unbounded": 0}
    for name, p in g.get_editor_property("pieces").items():
        name = str(name)
        if not p.mesh and not p.moving: stats["no_mesh"] += 1
        pm = p.get_editor_property("material")
        # (the piece's mesh and its moving parts: a lid or a door is drawn with the piece's own material too)
        for part, mesh in (("", p.mesh), (" lid/door", p.moving), (" second door", p.moving2)):
            if not mesh or mesh.get_path_name() in seen: continue
            seen.add(mesh.get_path_name())
            mats = mats_of(mesh, [pm] if pm else [])
            if see_through(mats):
                if CHECK: print("NANITE16 would give LODs", name + part, mesh.get_path_name()); continue
                if mesh.get_num_lods() < 3:
                    r = mesh.get_bounds().sphere_radius
                    n = lods(mesh, r); EAL.save_loaded_asset(mesh, only_if_is_dirty=False); stats["lods"] += 1
                    print("NANITE16 LODs", n, name + part, mesh.get_path_name())
                continue
            nb, bounded = sway_bound(mats, False); stats["bounds"] += nb
            # (a mesh already Nanite is left as it is: its shape preservation is its own)
            if mesh.get_editor_property("nanite_settings").enabled: stats["already"] += 1; continue
            if not bounded: stats["unbounded"] += 1; print("NANITE16 left (its sway cannot be bounded)", name + part, mesh.get_path_name()); continue
            if CHECK: print("NANITE16 would make", name + part, mesh.get_path_name()); continue
            set_nanite(mesh, False)
            EAL.save_loaded_asset(mesh, only_if_is_dirty=False)
            stats["made"] += 1
            print("NANITE16 made", name + part, mesh.get_path_name())
    print("NANITE16 town", len(seen), "meshes:", stats)


if PART == "nanite_wild": nanite_wild()
elif PART == "nanite_town": nanite_town()
else: print("944: parts nanite_wild, nanite_town")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
