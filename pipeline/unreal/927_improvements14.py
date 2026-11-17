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
  horse           the third phase (items 7, 10, 6): her horse called by a key (bHorseCall14: J or the D-pad up) on the game's maps
                  (refused in the dungeons), and brokenspire's HorseDef seated by blender_numpy/horse_seat.py's measure of the
                  saddle (SourceArt/brokenspire/horse_seat.json: the seat 30 cm ahead of the saddle bone, which stands on the
                  cantle; the reins' grip over the withers).
  reins           the third phase (item 6: "she should be holding the reins instead of holding her weapons"): every hero's rider
                  clips (brokenspire's RiderClips: idle, walk, run) given arms that hold the reins: each frame, both arms solved
                  (two bones, the elbow in its own plane, the hand's turn kept) so the hands reach the grip, placed from her pelvis
                  as the seat and the grip stand on the horse; written into the clips through their data controller and read back
                  (the hands' distance from their grips printed). Run after 913 rider and 927 horse.
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
AL = unreal.AnimationLibrary
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
        # (the generator let go before the next map loads: one left in a variable made a load fatal (PR #78's review))
        g = None; gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
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


def horse_cfg(g):
    g.set_editor_property("horse_call14", True)
    hs = os.path.join(SA, "brokenspire", "horse_seat.json")
    if not g.get_editor_property("horse_def").get_editor_property("mesh") or not os.path.isfile(hs): return "the call key (no horse here)"
    J = json.load(open(hs, encoding="utf-8"))
    hd = g.get_editor_property("horse_def")
    hd.set_editor_property("seat_ahead", float(J["seat"]["ahead_cm"])); hd.set_editor_property("seat_up", float(J["seat"]["up_cm"]))
    hd.set_editor_property("rein_ahead", float(J["rein_grip"]["ahead_cm"])); hd.set_editor_property("rein_up", float(J["rein_grip"]["up_cm"]))
    hd.set_editor_property("rein_apart", float(J["rein_grip"]["apart_cm"]))
    hd.set_editor_property("bit_ahead", float(J["bit_from_head_bone"]["ahead_cm"])); hd.set_editor_property("bit_up", float(J["bit_from_head_bone"]["up_cm"]))
    g.set_editor_property("horse_def", hd)
    h2 = g.get_editor_property("horse_def")
    return (f"the call key; the seat {h2.get_editor_property('seat_ahead')} cm ahead, {h2.get_editor_property('seat_up')} up; the reins "
            f"{h2.get_editor_property('rein_ahead')} ahead, {h2.get_editor_property('rein_up')} up, {h2.get_editor_property('rein_apart')} apart")


# ---- the reins: two-bone arms solved on the rider clips (plain quaternion arithmetic: x, y, z, w tuples)
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)
def qinv(a): return (-a[0], -a[1], -a[2], a[3])
def qrot(q, v):
    p = qmul(qmul(q, (v[0], v[1], v[2], 0.0)), qinv(q)); return (p[0], p[1], p[2])
def vsub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def vadd(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def vmul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def vdot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def vcross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def vlen(a): return math.sqrt(vdot(a, a))
def vnorm(a): l = vlen(a) or 1.0; return (a[0] / l, a[1] / l, a[2] / l)
def qbetween(a, b):
    a = vnorm(a); b = vnorm(b); d = max(-1.0, min(1.0, vdot(a, b)))
    if d > 0.99999: return (0.0, 0.0, 0.0, 1.0)
    ax = vcross(a, b)
    if vlen(ax) < 1e-6: ax = vcross(a, (0, 0, 1)) if abs(a[2]) < 0.9 else vcross(a, (1, 0, 0))
    ax = vnorm(ax); h = math.acos(d) * 0.5; s = math.sin(h)
    return (ax[0] * s, ax[1] * s, ax[2] * s, math.cos(h))
def uq(q): return (q.x, q.y, q.z, q.w)
def uv(v): return (v.x, v.y, v.z)


def solve_two(S, E, Wr, T, pole):
    """the elbow's new place: shoulder S, elbow E, wrist Wr, target T, the elbow bent toward pole (all component space)"""
    a = vlen(vsub(E, S)); b = vlen(vsub(Wr, E))
    d = vsub(T, S); dl = min(vlen(d), (a + b) * 0.995); dn = vnorm(d)
    x = (a * a - b * b + dl * dl) / (2 * dl); h = math.sqrt(max(0.0, a * a - x * x))
    pv = vsub(pole, S); pv = vsub(pv, vmul(dn, vdot(pv, dn))); pn = vnorm(pv)
    return vadd(vadd(S, vmul(dn, x)), vmul(pn, h)), vadd(S, vmul(dn, dl))


def reins():
    g = open_map("brokenspire")
    hd = g.get_editor_property("horse_def")
    lift = hd.get_editor_property("rider_lift")
    seat = (hd.get_editor_property("seat_ahead"), hd.get_editor_property("seat_up"))
    rein = (hd.get_editor_property("rein_ahead"), hd.get_editor_property("rein_up"), hd.get_editor_property("rein_apart"))
    jobs = []
    for hero, rc in g.get_editor_property("rider_clips").items():
        for k in ("idle", "walk", "run"):
            c = rc.get_editor_property(k)
            if c: jobs.append((str(hero), k, c.get_path_name()))
    g = None; gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    les.load_level(SCRATCH)
    done = set()
    for hero, k, path in jobs:
        if path in done: continue
        done.add(path)
        clip = unreal.load_asset(path)
        sk = clip.get_editor_property("skeleton")
        refs = [r for r in eal.find_package_referencers_for_asset(sk.get_path_name().split(".")[0], False)]
        mesh = next((m for m in (unreal.load_asset(r) for r in refs) if isinstance(m, unreal.SkeletalMesh)), None)
        if not mesh: REPORT.append(f"927 reins {hero} {k}: no mesh on its skeleton"); continue
        a = eas.spawn_actor_from_object(mesh, unreal.Vector(0, 0, 0))
        comp = a.get_editor_property("skeletal_mesh_component")
        names = [str(comp.get_bone_name(i)) for i in range(comp.get_num_bones())]
        parent = {n: str(comp.get_parent_bone(n)) for n in names}
        ref = {n: comp.get_ref_pose_transform(i) for i, n in enumerate(names)}
        eas.destroy_actor(a)
        tracks = [str(x) for x in AL.get_animation_track_names(clip)]
        n = AL.get_num_frames(clip)
        arms = {s: ("upperarm_" + s, "lowerarm_" + s, "hand_" + s) for s in ("l", "r")}
        if not all(b in names for s in arms for b in arms[s]) or "pelvis" not in names: REPORT.append(f"927 reins {hero} {k}: no mannequin arms"); continue
        keys = {b: ([], [], []) for s in arms for b in arms[s]}
        worst = 0.0
        for f in range(n + 1):
            loc = {nm: ref[nm] for nm in names}
            for b, tr in zip(tracks, AL.get_bone_poses_for_frame(clip, tracks, f, False)): loc[b] = tr
            cs = {}
            def csof(b):
                if b in cs: return cs[b]
                tr = loc[b]; r, p = uq(tr.rotation), uv(tr.translation)
                pb = parent.get(b, "None")
                if pb in ("None", "") or pb not in loc: cs[b] = (r, p)
                else:
                    pr, pp = csof(pb); cs[b] = (qmul(pr, r), vadd(pp, qrot(pr, p)))
                return cs[b]
            for b in names: csof(b)
            pel = cs["pelvis"][1]
            knee = vmul(vadd(cs["calf_l"][1], cs["calf_r"][1]), 0.5) if "calf_l" in cs else vadd(pel, (0, 1, 0))
            fwd = vnorm((knee[0] - pel[0], knee[1] - pel[1], 0.0)); up = (0.0, 0.0, 1.0)
            left = vnorm(vcross(fwd, up))
            if vdot(vsub(cs["upperarm_l"][1], pel), left) < 0: left = vmul(left, -1.0)
            for s, sg in (("l", 1.0), ("r", -1.0)):
                ua, la, ha = arms[s]
                S, E, Wr = cs[ua][1], cs[la][1], cs[ha][1]
                # (the hold from her pelvis: HorseDef's ReinAhead / ReinUp (927 horse), as the game draws the reins to it)
                T = vadd(vadd(pel, vmul(fwd, rein[0])), vadd(vmul(up, rein[1]), vmul(left, sg * rein[2] * 0.5)))
                pole = vadd(E, vadd(vmul(up, -20.0), vmul(left, sg * 15.0)))
                E2, T2 = solve_two(S, E, Wr, T, pole)
                # (the upper arm turned so its elbow is at E2; the forearm so its wrist is at the target; the hand's world turn kept)
                q1 = qbetween(vsub(E, S), vsub(E2, S)); ua_r = qmul(q1, cs[ua][0])
                la_r0 = qmul(ua_r, uq(loc[la].rotation)); W0 = vadd(E2, qrot(la_r0, (0, 0, 0)))
                wr_old = vadd(E2, qrot(la_r0, uv(loc[ha].translation)))
                q2 = qbetween(vsub(wr_old, E2), vsub(T2, E2)); la_r = qmul(q2, la_r0)
                ha_r = cs[ha][0]
                pr_ua = cs[parent[ua]][0]
                l_ua = qmul(qinv(pr_ua), ua_r); l_la = qmul(qinv(ua_r), la_r); l_ha = qmul(qinv(la_r), ha_r)
                for b, lr in ((ua, l_ua), (la, l_la), (ha, l_ha)):
                    keys[b][0].append(loc[b].translation); keys[b][1].append(unreal.Quat(*lr)); keys[b][2].append(loc[b].scale3d)
                hand_now = vadd(E2, qrot(la_r, uv(loc[ha].translation)))
                worst = max(worst, vlen(vsub(hand_now, T)))
        ctrl = clip.controller
        ctrl.open_bracket(unreal.Text("reins"), True)
        for b, kk in keys.items():
            if b not in tracks: ctrl.add_bone_track(b, True)
            ctrl.set_bone_track_keys(b, *kk, True)
        ctrl.close_bracket(True)
        eal.save_loaded_asset(clip, only_if_is_dirty=False)
        REPORT.append(f"927 reins {hero} {k}: {n + 1} frames, the hands at most {worst:.1f} cm from their grips as solved")
    les.save_current_level()


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
if args and args[0] == "horse": each(GAME_MAPS, horse_cfg, "horse")
if args and args[0] == "reins": reins()
if args and args[0] == "hud": each(GAME_MAPS + ("martial_arts",), hud, "hud")
for line in REPORT: print(line)
import gc; gc.collect()
