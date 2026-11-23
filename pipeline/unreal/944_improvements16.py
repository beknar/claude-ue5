"""The user's list of 2026-11-22 (docs/improvements16.txt; the plan docs/improvements16_plan.md): its editor stages by part.

  nanite_wild [skip=<kind>+<kind>] [check]   phase 4: every mesh the wilderness's biomes scatter (brokenspire's WildBiomes) made Nanite
      where it can be: none whose materials are see-through (translucent: Nanite draws opaque and masked only); trees, bushes,
      grass, flowers, reeds and crops with the voxel shape preservation (UE 5.8's Nanite foliage: a canopy's leaves kept as a volume
      far off instead of thinning away), rocks, logs, ice and the rest plain; the kinds named after skip= left as they are (the
      measure decides per kind: Nanite foliage can cost more than instances with LODs); a wind-swayed material gets a maximum
      displacement (its world position offset's bound, or Nanite culls a swaying leaf at its rest bounds). check reports only.
  nanite_town [check]   phase 5: every mesh the towns' pieces use (brokenspire's Pieces: the towns, the holy, forge, port, mage and modern
      cities, their furniture and props; the castle's and the dungeons' share many of them) made Nanite where it can be; one that
      cannot (a see-through material) gets generated LODs: LOD1 at the screen size of 80 m, LOD2 at 200 m (screen size = the mesh's
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


def see_through(mats):
    """a material drawn translucent (or additive, modulate): Nanite cannot draw it"""
    for m in mats:
        b = m.get_base_material()
        if not b: continue
        bm = b.get_editor_property("blend_mode")
        if bm not in (unreal.BlendMode.BLEND_OPAQUE, unreal.BlendMode.BLEND_MASKED): return True
    return False


def set_nanite(mesh, voxel):
    ns = mesh.get_editor_property("nanite_settings")
    was = ns.enabled
    ns.set_editor_property("enabled", True)
    try:
        ns.set_editor_property("shape_preservation", unreal.NaniteShapePreservation.VOXELIZE if voxel else unreal.NaniteShapePreservation.NONE)
    except Exception as e:
        print("NANITE16 no shape preservation on", mesh.get_path_name(), e)
    mesh.set_editor_property("nanite_settings", ns)
    return was


def sway_bound(mats, cm=60.0):
    """a wind-swayed material's maximum world position offset displacement (Nanite's bounds grow by it); left if one is set"""
    n = 0
    for m in mats:
        b = m.get_base_material()
        if not b or not b.get_path_name().startswith("/Game/"): continue
        try:
            if b.get_editor_property("max_world_position_offset_displacement") <= 0.0:
                if not CHECK:
                    b.set_editor_property("max_world_position_offset_displacement", cm)
                    unreal.MaterialEditingLibrary.recompile_material(b); EAL.save_loaded_asset(b, only_if_is_dirty=False)
                n += 1
        except Exception as e:
            print("NANITE16 no displacement bound on", b.get_path_name(), e)
    return n


def nanite_wild():
    open_map(BROKENSPIRE)
    g = generator()
    seen, stats = set(), {"made": 0, "already": 0, "see_through": 0, "skipped": 0, "voxel": 0, "bounds": 0}
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
            ns = mesh.get_editor_property("nanite_settings")
            if ns.enabled and not voxel: stats["already"] += 1; continue
            if kind in SWAY_KINDS: stats["bounds"] += sway_bound(mats)
            if CHECK: print("NANITE16 would make", "voxel" if voxel else "plain", kind, mesh.get_path_name()); continue
            set_nanite(mesh, voxel)
            EAL.save_loaded_asset(mesh, only_if_is_dirty=False)
            stats["made"] += 1; stats["voxel"] += 1 if voxel else 0
            print("NANITE16 made", "voxel" if voxel else "plain", kind, mesh.get_path_name())
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
    seen, stats = set(), {"made": 0, "already": 0, "lods": 0, "no_mesh": 0}
    for name, p in g.get_editor_property("pieces").items():
        mesh = p.mesh
        if not mesh: stats["no_mesh"] += 1; continue
        if mesh.get_path_name() in seen: continue
        seen.add(mesh.get_path_name())
        mats = mats_of(mesh, [p.get_editor_property("material")] if p.get_editor_property("material") else [])
        if see_through(mats):
            if CHECK: print("NANITE16 would give LODs", name, mesh.get_path_name()); continue
            if mesh.get_num_lods() < 3:
                r = mesh.get_bounds().sphere_radius
                n = lods(mesh, r); EAL.save_loaded_asset(mesh, only_if_is_dirty=False); stats["lods"] += 1
                print("NANITE16 LODs", n, name, mesh.get_path_name())
            continue
        if mesh.get_editor_property("nanite_settings").enabled: stats["already"] += 1; continue
        if CHECK: print("NANITE16 would make", name, mesh.get_path_name()); continue
        set_nanite(mesh, False)
        EAL.save_loaded_asset(mesh, only_if_is_dirty=False)
        stats["made"] += 1
        print("NANITE16 made", name, mesh.get_path_name())
    print("NANITE16 town", len(seen), "meshes:", stats)


if PART == "nanite_wild": nanite_wild()
elif PART == "nanite_town": nanite_town()
else: print("944: parts nanite_wild, nanite_town")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
