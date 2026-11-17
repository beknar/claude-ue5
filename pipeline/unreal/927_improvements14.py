"""The user's list of 2026-11-16 (docs/improvements14.txt; the plan docs/improvements14_plan.md), in phases.

Parts (args):
  collide [fix]   items 17 and 18: every mesh the wilds lay (brokenspire's WildPieces, the landmark, the scenery kit) measured on the
                  scratch level: rays from 16 ways at three heights, each against the mesh's drawn faces (complex) and against its
                  collision shapes (simple, what stops her). A mesh whose shapes stand a metre or more inside its faces, or let a
                  third of the rays through, fails (the tenth phase's landmark tower kept the convex hull of its first, smaller build
                  through the kit's reimport: she walked 4.5 m into it, in the user's save game3b). With "fix", a failing mesh of our
                  own (the kit's) is given its shape again (a convex decomposition), a pack's mesh a solid copy of our own (the pack's
                  left alone: the towns and dungeons use it), the table pointed at the copy; then measured again. Writes
                  SourceArt/wilderness/collide14.json.
  signboard       the second phase (item 1): the trades' sign board's own outline (brokenspire's Town.Sign piece, a shield that
                  narrows to its point: the lettering fitted to a 58 x 42 cm rectangle stood past its sloping edges, the user's
                  "store house"): its width at each height in the sign's frame from its mesh's vertices, written to
                  SourceArt/brokenspire/sign_board.json for blender_numpy/bs_signs.py and 884 signs14.
  hud             the second phase (items 8 and 20): the last 20 messages (bMessageLog14: L or the D-pad's down opens them) and a
                  potion or food on the quick bar used by the attack button, food allowed on the bar (bQuickUse14), on the game's
                  maps and martial_arts.
"""
import json, math, os, sys, gc
import unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, wild_tables
importlib.reload(wild_tables)          # (ue_exec keeps a module imported between runs)

SA = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "SourceArt")
eal = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
sme = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
KIT = "/Game/RandomDungeon/Wild13/Kit"
SOLID = "/Game/RandomDungeon/Wild/Solid"
SCRATCH = "/Game/RandomLevel/Test/rl_scratch"
REPORT = []
MAPS = "/Game/RandomDungeon/Maps/"
GAME_MAPS = ("brokenspire", "mistward_castle", "vel_morrath", "war_engine", "sewers", "kethrys_spire", "heaven_fortress")


def open_map(m):
    path = MAPS + m
    if not ues.get_editor_world().get_path_name().startswith(path + "."):
        les.load_level(path); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    w = ues.get_editor_world(); assert w.get_path_name().startswith(path + "."), w.get_path_name()
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


def each(maps, fn, label):
    for m in maps:
        if not eal.does_asset_exist(MAPS + m): REPORT.append(f"{label}: no map {m}"); continue
        g = open_map(m)
        what = fn(g)
        g.modify(); les.save_current_level()
        unreal.SystemLibrary.execute_console_command(None, "obj gc")
        REPORT.append(f"927 {label} {m}: {what}")


def signboard():
    g = open_map("brokenspire")
    pc = g.get_editor_property("pieces")[unreal.Name("Town.Sign")]
    m = pc.get_editor_property("mesh"); adj = pc.get_editor_property("adjust")
    tris = []
    for s in range(m.get_num_sections(0)):
        sec = unreal.ProceduralMeshLibrary.get_section_from_static_mesh(m, 0, s)
        vs = [adj.transform_location(v) for v in sec[0]]; ix = list(sec[1])
        for k in range(0, len(ix) - 2, 3): tris.append((vs[ix[k]], vs[ix[k + 1]], vs[ix[k + 2]]))
    del g
    # (the board: past the bracket's arm (x 55 on), under its chains (z -63 down), within its thickness; its outline at each
    # height from where its triangles' edges cross that height (165 vertices: sampled by vertices, heights between them read 0))
    btris = [tr for tr in tris if all(q.x > 55.0 and q.z < -63.0 and abs(q.y) < 4.0 for q in tr)]
    board = [q for tr in btris for q in tr]
    z0, z1 = min(q.z for q in board), max(q.z for q in board)
    bands = []
    z = z0 + 0.5
    while z <= z1 - 0.5:
        xs = []
        for tr in btris:
            for a, b in ((tr[0], tr[1]), (tr[1], tr[2]), (tr[2], tr[0])):
                if (a.z - z) * (b.z - z) <= 0 and a.z != b.z: xs.append(a.x + (b.x - a.x) * (z - a.z) / (b.z - a.z))
        if xs: bands.append([round(z, 1), round(min(xs), 1), round(max(xs), 1)])
        z += 1.0
    out = {"mesh": m.get_name(), "z": [round(z0, 1), round(z1, 1)], "x": [round(min(q.x for q in board), 1), round(max(q.x for q in board), 1)],
           "face_y": round(max(abs(q.y) for q in board), 2), "bands": bands, "vertices": len(board)}
    json.dump(out, open(os.path.join(SA, "brokenspire", "sign_board.json"), "w", encoding="utf-8"), indent=1)
    REPORT.append(f"927 signboard: {m.get_name()}: {len(board)} vertices, z {out['z']}, x {out['x']}, {len(bands)} bands; widest "
                  f"{max(b[2] - b[1] for b in bands):.1f} cm, at the foot {bands[0][2] - bands[0][1]:.1f} cm")


def hud(g):
    g.set_editor_property("message_log14", True); g.set_editor_property("quick_use14", True)
    return f"messages {g.get_editor_property('message_log14')}, quick use {g.get_editor_property('quick_use14')}"


def generator():
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


def wild_meshes():
    """(name in the table, mesh) for every mesh the wilds lay: the places' table, the landmark, the kit's pieces"""
    les.load_level("/Game/RandomDungeon/Maps/brokenspire")
    g = generator()
    out = {}
    for k, m in g.get_editor_property("wild_pieces").items():
        if m: out.setdefault(m.get_path_name(), (str(k), m))
    lm = g.get_editor_property("wild_landmark_mesh")
    if lm: out.setdefault(lm.get_path_name(), ("landmark", lm))
    for p in eal.list_assets(KIT, recursive=False):
        m = unreal.load_asset(p)
        if isinstance(m, unreal.StaticMesh): out.setdefault(m.get_path_name(), ("kit:" + m.get_name(), m))
    return list(out.values())


def soft(name, m):
    return wild_tables.soft_name(name, m.get_name())


def hit_dist(w, s, e, cplx):
    """how far from s a trace toward e first hits (cm), against the faces (cplx) or the collision shapes; None if nothing"""
    h = unreal.SystemLibrary.line_trace_single(w, s, e, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, cplx, [], unreal.DrawDebugTrace.NONE, True)
    t_ = h.to_tuple() if h else None
    if not t_ or not t_[0]: return None
    L = t_[4]
    return math.sqrt((L.x - s.x) ** 2 + (L.y - s.y) ** 2 + (L.z - s.z) ** 2)


def measure(m, at):
    """rays from 16 ways at 15, 45 and 75 % of the mesh's height toward its upright axis, from 3 m outside its box: where the faces
    are hit, how far inside them the shapes are first hit (or not at all)"""
    w = ues.get_editor_world()
    # (a mesh that traces its simple shapes as complex can't be told from its faces by a complex trace (PR #77's review): its
    # flag set to the default while it is measured (in memory, not saved), then put back)
    bs = m.get_editor_property("body_setup")
    flag0 = bs.get_editor_property("collision_trace_flag") if bs else None
    if flag0 == unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX: bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
    a = eas.spawn_actor_from_object(m, at)
    try:
        bb = m.get_bounding_box()
        cx, cy = at.x + (bb.min.x + bb.max.x) * 0.5, at.y + (bb.min.y + bb.max.y) * 0.5
        R = max(bb.max.x - bb.min.x, bb.max.y - bb.min.y) * 0.5 + 300.0
        H = bb.max.z - bb.min.z
        rays = hits = misses = 0; worst = 0.0
        for f in (0.15, 0.45, 0.75):
            z = at.z + bb.min.z + f * H
            for k in range(16):
                ang = k * math.pi / 8.0
                s = unreal.Vector(cx + math.cos(ang) * R, cy + math.sin(ang) * R, z); e = unreal.Vector(cx, cy, z)
                dcm = hit_dist(w, s, e, True)
                if dcm is None: continue
                rays += 1
                dsm = hit_dist(w, s, e, False)
                if dsm is None: misses += 1; continue
                hits += 1
                worst = max(worst, (dsm - dcm) / 100.0)
        return {"rays": rays, "misses": misses, "inside_m": round(worst, 2), "h_m": round(H / 100.0, 1),
                "convex": sme.get_convex_collision_count(m), "simple": sme.get_simple_collision_count(m),
                "trace": str(m.get_editor_property("body_setup").get_editor_property("collision_trace_flag")).split(".")[-1].split(":")[0] if m.get_editor_property("body_setup") else "none"}
    finally:
        eas.destroy_actor(a)
        if flag0 == unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX: bs.set_editor_property("collision_trace_flag", flag0)


def fails(r):
    return r["rays"] >= 4 and (r["inside_m"] >= 1.0 or r["misses"] > r["rays"] / 3.0)


def fix_on_brokenspire(bad):
    """the failing meshes given their shapes again: a kit piece in place, a pack's mesh a solid copy of our own, every table that
    lays it (the places' table, the landmark) pointed at the copy; the map saved. A function, so the generator is let go before
    another map loads (a generator left in a variable made the next load fatal)"""
    les.load_level("/Game/RandomDungeon/Maps/brokenspire")
    g = generator(); wp = g.get_editor_property("wild_pieces"); fixed = []
    for name, m in bad:
        path = m.get_path_name().split(".")[0]
        if path.startswith(KIT): wild_tables.reshape(m); fixed.append((name, m)); continue
        dst = f"{SOLID}/{m.get_name()}_Solid14"
        c = unreal.load_asset(dst) if eal.does_asset_exist(dst) else eal.duplicate_asset(path, dst)
        wild_tables.reshape(c)
        for k in [k for k, v in wp.items() if v == m]: wp[k] = c
        if g.get_editor_property("wild_landmark_mesh") == m: g.set_editor_property("wild_landmark_mesh", c)
        fixed.append((name, c))
    g.set_editor_property("wild_pieces", wp)
    les.save_current_level()
    return [(n, m.get_path_name()) for n, m in fixed]


def collide(fix):
    meshes = wild_meshes()
    g_paths = {m.get_path_name(): n for n, m in meshes}
    les.load_level(SCRATCH)
    rows = {}; bad = []; unmeasured = []
    for i, (name, m) in enumerate(meshes):
        if soft(name, m): continue
        bb = m.get_bounding_box()
        # (small pieces and flat ones (a plane of rock 10 cm high: nothing to walk into) are not measured)
        if bb.max.z - bb.min.z < 50.0 or (bb.max.z - bb.min.z < 150.0 and max(bb.max.x - bb.min.x, bb.max.y - bb.min.y) < 150.0): continue
        r = measure(m, unreal.Vector(5000000.0 + (i % 20) * 30000.0, 5000000.0 + (i // 20) * 30000.0, 0.0))
        r["name"] = name; rows[m.get_path_name()] = r
        # (no ray met its faces (a mesh built to trace its simple shapes as complex has no faces to trace: the wheel's 439 boxes):
        # named as not measured, never passed silently (PR #77's review))
        if r["rays"] < 4: unmeasured.append(name)
        if fails(r): bad.append((name, m))
    REPORT.append(f"927 collide: {len(unmeasured)} not measured (no faces to trace): {', '.join(unmeasured)}")
    REPORT.append(f"927 collide: {len(rows)} solid meshes measured, {len(bad)} fail: " + ", ".join(f"{n} ({rows[m.get_path_name()]['inside_m']} m in, {rows[m.get_path_name()]['misses']}/{rows[m.get_path_name()]['rays']} through)" for n, m in bad))
    fixed = []; still = []
    if fix and bad:
        bad_paths = [(n, m.get_path_name()) for n, m in bad]
        del meshes, bad; gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        fixed = fix_on_brokenspire([(n, unreal.load_asset(p)) for n, p in bad_paths])
        gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        les.load_level(SCRATCH)
        for i, (name, p) in enumerate(fixed):
            m = unreal.load_asset(p)
            r = measure(m, unreal.Vector(5000000.0 + i * 30000.0, 4000000.0, 0.0)); r["name"] = name; r["after_fix"] = True
            rows[p] = r
            if fails(r): still.append(name)
            REPORT.append(f"927 collide: {name} after its new shape: {r['inside_m']} m in, {r['misses']}/{r['rays']} through" + (" STILL FAILS" if fails(r) else ""))
        bad = [(n, None) for n, _ in bad_paths]
    les.save_current_level()
    json.dump({"meshes": rows, "failed": [n for n, _ in bad], "fixed": [n for n, _ in fixed], "still_failing": still, "not_measured": unmeasured},
              open(os.path.join(SA, "wilderness", "collide14.json"), "w", encoding="utf-8"), indent=1)
    assert not still, f"927 collide: still failing after their new shapes: {still}"


args = sys.argv[1:]
if args and args[0] == "collide": collide("fix" in args[1:])
if args and args[0] == "signboard": signboard()
if args and args[0] == "hud": each(GAME_MAPS + ("martial_arts",), hud, "hud")
for line in REPORT: print(line)
import gc; gc.collect()
