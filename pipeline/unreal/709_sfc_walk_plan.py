"""sf-city-level walk test, part 1 (editor): plan the routes for 710.
- route: PlayerStart -> through every structure (front door, each room, inner doors, back out) -> road -> Monolith plaza ->
  excavation lab (both rooms) -> megastructure gate / hall -> landscape hilltop -> back over the road -> city streets.
  Legs between keypoints: A* on 708's reach grid (8-connected, every move re-checked with Pawn-profile traces, doors
  ignored, only cells where her capsule fits, cost raised within 2 m of obstacles), then shortened with capsule sweeps\n  (her radius + 2) + continuous-floor checks.
- edge probes: ~90 of 708's barrier walls (spread over the level) with a start point just inside each and the push direction.
Writes SourceArt/sf_city/walk_plan.json.  Args: [n_probes]"""
import sys, json, math, heapq, random, collections, unreal
NPROBE = int(sys.argv[1]) if len(sys.argv) > 1 else 90
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); V = unreal.Vector
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert w.get_path_name().startswith("/Game/SFCityLevel/Maps/sf-city-level."), w.get_path_name()
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\sf_city"
R = json.load(open(SA + r"\reach.json")); ST = R["step"]; X0, Y0 = R["x0"], R["y0"]
Z = {}; ZL = collections.defaultdict(list)                      # Z: first-reached level per grid cell (routes), ZL: every level
for c in R["cells"]: Z.setdefault((c[0], c[1]), c[2]); ZL[(c[0], c[1])].append(c[2])
X = lambda i: X0 + i * ST; Y = lambda j: Y0 + j * ST
cell = lambda x, y: (int(round((x - X0) / ST)), int(round((y - Y0) / ST)))
IGN = [a for a in eas.get_all_level_actors() if a.get_class().get_name() == "BP_SciFiDoor_C"]
LT = unreal.SystemLibrary.line_trace_single_by_profile; NONE = unreal.DrawDebugTrace.NONE
def hit(a, b):
    r = LT(w, a, b, "Pawn", False, IGN, NONE, True)
    return bool(r and r.to_tuple()[0])
def floor_z(x, y, ztop, zbot):
    r = LT(w, V(x, y, ztop), V(x, y, zbot), "Pawn", False, IGN, NONE, True)
    return r.to_tuple()[4].z if (r and r.to_tuple()[0]) else None
# clearance: BFS distance (cells) from the reachable set's border, capped at 3
dist = {}; q = collections.deque()
for c in Z:
    if any((c[0] + a, c[1] + b) not in Z for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))): dist[c] = 0; q.append(c)
while q:
    c = q.popleft()
    if dist[c] >= 3: continue
    for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        n = (c[0] + a, c[1] + b)
        if n in Z and n not in dist: dist[n] = dist[c] + 1; q.append(n)
def rough(c):
    """largest height jump to a reachable 4-neighbour: rubble piles (Monolith gate) have rock edges above her step height"""
    zs = [Z[(c[0] + a, c[1] + b)] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (c[0] + a, c[1] + b) in Z]
    return max((abs(z - Z[c]) for z in zs), default=0.0)
FREE = {}; OT = [unreal.ObjectTypeQuery.ECC_WORLD_STATIC, unreal.ObjectTypeQuery.ECC_WORLD_DYNAMIC]
def free(c):
    """her (BP_SFC_Fem5Character) capsule fits here: r 38 (36 + 2), raised so its bottom clears slopes / steps (z+42)"""
    if c not in FREE:
        o = unreal.SystemLibrary.capsule_overlap_actors(w, V(X(c[0]), Y(c[1]), Z[c] + 120), 38.0, 78.0, OT, None, IGN)
        FREE[c] = not (o and len(list(o)))
    return FREE[c]
MOVE = {}
def ok(c, n):
    k = (c, n)                                                     # directional: a 60 cm drop is fine, the climb back is not
    if k not in MOVE:
        z0, z1 = Z[c], Z[n]; zt = max(z0, z1)
        good = abs(z1 - z0) <= 45 or (z1 < z0 and z0 - z1 <= 60)
        if good and (hit(V(X(c[0]), Y(c[1]), zt + 50), V(X(n[0]), Y(n[1]), zt + 50)) or hit(V(X(c[0]), Y(c[1]), zt + 140), V(X(n[0]), Y(n[1]), zt + 140))): good = False
        MOVE[k] = good
    return MOVE[k]
def snap(x, y, z=None, tol=25.0):
    """nearest reachable cell (preferring >= 1 cell of clearance) whose floor is within tol of z (z None: any height)"""
    c = cell(x, y)
    for r in range(0, 12):
        best = None
        for a in range(-r, r + 1):
            for b in range(-r, r + 1):
                n = (c[0] + a, c[1] + b)
                if n in Z and dist.get(n, 3) >= min(1, r) and (z is None or abs(Z[n] - z) <= tol) and free(n) and rough(n) <= 40 and (best is None or a * a + b * b < best[0]): best = (a * a + b * b, n)
        if best: return best[1]
    raise RuntimeError(f"no reachable cell near {x:.0f},{y:.0f},{z}")
def component(s, limit=200000):
    seen = {s}; q = collections.deque([s])
    while q and len(seen) < limit:
        c = q.popleft()
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c[0] + a, c[1] + b)
            if n in Z and n not in seen and ok(c, n): seen.add(n); q.append(n)
    return seen
def astar(s, g, limit=600000):
    D8 = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    openq = [(0.0, s)]; cost = {s: 0.0}; prev = {}; n_exp = 0
    while openq:
        _, c = heapq.heappop(openq); n_exp += 1
        if c == g or n_exp > limit: break
        for a, b, L in D8:
            n = (c[0] + a, c[1] + b)
            if n not in Z: continue
            if a and b and not ((c[0] + a, c[1]) in Z and (c[0], c[1] + b) in Z and ok(c, (c[0] + a, c[1])) and ok(c, (c[0], c[1] + b))): continue
            if not ok(c, n) or not free(n) or (rough(n) > 40 and n != g): continue
            nc = cost[c] + L * (1.0 + 1.5 * max(0, 2 - dist.get(n, 3)))
            if nc < cost.get(n, 1e18):
                cost[n] = nc; prev[n] = c; heapq.heappush(openq, (nc + math.hypot(n[0] - g[0], n[1] - g[1]), n))
    if g not in prev and g != s: return None
    p = [g]
    while p[-1] != s: p.append(prev[p[-1]])
    return p[::-1]
CT = unreal.SystemLibrary.capsule_trace_single_by_profile
def clear(a, b):
    za, zb = Z[a] + 100, Z[b] + 100
    if CT(w, V(X(a[0]), Y(a[1]), za), V(X(b[0]), Y(b[1]), zb), 38.0, 52.0, "Pawn", False, IGN, NONE, True): return False
    L = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, int(L * ST / 50))
    fp = Z[a]
    for k in range(1, n + 1):                                      # continuous floor near the straight line's height, no ledge
        u = k / n; x, y = X(a[0]) + (X(b[0]) - X(a[0])) * u, Y(a[1]) + (Y(b[1]) - Y(a[1])) * u; ze = Z[a] + (Z[b] - Z[a]) * u
        f = floor_z(x, y, ze + 60, ze - 80)
        if f is None or abs(f - ze) > 40 or f - fp > 40: return False        # (a 58 cm ledge hid inside the 40 cm band)
        fp = f
    return True
def pull(path):
    out = [path[0]]; i = 0
    while i < len(path) - 1:
        j = min(len(path) - 1, i + 40)
        while j > i + 1 and not clear(path[i], path[j]): j -= 1
        out.append(path[j]); i = j
    return out
# ---- keypoints
S = json.load(open(SA + r"\structures.json")); st = {s["name"]: s for s in S}
start = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.PlayerStart)).get_actor_location()
def through(s):
    """enter by the front door, visit every room (through the inner doors), leave by the front door"""
    fd = s["doors"][0]; kp = [(fd[0], f"{s['name']} front door (outside)"), (fd[1], f"{s['name']} front door"), (fd[2], f"{s['name']} inside")]
    kp.append((s["rooms"][0]["centre"], f"{s['name']} {s['rooms'][0]['purpose']}"))
    for k, idr in enumerate(s["doors"][1:]):
        kp += [(idr[0], "inner door (near side)"), (idr[1], "inner door"), (idr[2], "inner door (far side)"), (s["rooms"][k + 1]["centre"], f"{s['name']} {s['rooms'][k + 1]['purpose']}"),
               (idr[2], "inner door (far side)"), (idr[1], "inner door"), (idr[0], "inner door (near side)")]
    kp += [(fd[2], f"{s['name']} inside"), (fd[1], f"{s['name']} front door"), (fd[0], f"{s['name']} outside")]
    return kp
def best_cell(pred, key):
    cands = [c for c in Z if pred(X(c[0]), Y(c[1]), Z[c])]
    return max(cands, key=key) if cands else None
mono = lambda x, y, z: y < -74000
hall = None
for yy in range(-104000, -142000, -1500):                         # first roofed reachable cell down the megastructure's axis
    c = cell(-9000, yy)
    for a in range(-6, 7):
        n = (c[0] + a, c[1])
        if n in Z and hit(V(X(n[0]), Y(n[1]), Z[n] + 200), V(X(n[0]), Y(n[1]), Z[n] + 4000)): hall = n; break
    if hall and yy < -110000: break
hill = None                                                        # highest landscape cell she can WALK to (smooth route) from the plaza
plaza = snap(-15000, -86500)
for c in sorted((c for c in Z if mono(X(c[0]), Y(c[1]), Z[c]) and Y(c[1]) > -90000 and Z[c] > 600), key=lambda c: -Z[c])[:4000:400]:
    if free(c) and rough(c) <= 40 and astar(plaza, c, limit=150000): hill = c; break
KP = [((start.x, start.y, None), "PlayerStart")]
KP += through(st["PortAuthority"]) + through(st["HabApartment"]) + through(st["NoodleBar"])
KP += [((-15000, -57500, None), "road head"), ((-15000, -68000, None), "bridge middle"), ((-15000, -86500, None), "road end / Monolith plaza")]
KP += through(st["ExcavationLab"])
KP += [((-8000, -95500, None), "Monolith gate")]
if hall: KP.append(((X(hall[0]), Y(hall[1]), Z[hall]), "megastructure hall (roofed)"))
if hill: KP.append(((X(hill[0]), Y(hill[1]), Z[hill]), f"landscape hilltop z {Z[hill]:.0f}"))
KP += [((-29000, -92600, None), "Monolith plaza west"), ((11000, -92600, None), "Monolith plaza east")]   # (its hills are steeper than she can walk)
KP += [((-15000, -86500, None), "road end"), ((-15000, -57500, None), "road head"), ((-15000, -8000, None), "dock east"), ((29557, -19600, None), "city streets"),
       ((10000, 10000, None), "landing ring")]
route = []; labels = []; legs = []
prev = snap(KP[0][0][0], KP[0][0][1])
route.append(prev); labels.append(KP[0][1])
for (p, lab) in KP[1:]:
    g = snap(p[0], p[1], p[2] if len(p) > 2 else None)
    if g == prev: continue
    path = astar(prev, g)
    if path is None:
        comp = component(prev)
        legs.append({"to": lab, "ok": False}); print(f"NO PATH to {lab}: from {prev} z {Z[prev]:.0f} to {g} z {Z[g]:.0f} | start component {len(comp)} cells, goal in it {g in comp}"); continue
    pp = pull(path)
    for c in pp[1:-1]: route.append(c); labels.append("")
    route.append(g); labels.append(lab); legs.append({"to": lab, "ok": True, "cells": len(path), "pts": len(pp)}); prev = g
pts = [[X(c[0]), Y(c[1]), Z[c]] for c in route]
L = sum(math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1]) for k in range(len(pts) - 1))
# ---- edge probes
walls = [wl for wl in R["walls"] if wl["n"] >= 2]
random.Random(7).shuffle(walls); walls.sort(key=lambda wl: (wl["axis"], round(wl["plane"] / 20000), round(sum(wl["a"]) / 40000)))
pick = walls[::max(1, len(walls) // NPROBE)][:NPROBE]
probes = []
for wl in pick:
    m = (wl["a"][0] + wl["a"][1]) / 2
    for sgn in (-1, 1):                                            # inner side = the reachable cell next to the plane, on the wall's level
        if wl["axis"] == "x": c = cell(wl["plane"] + sgn * ST / 2, m)
        else: c = cell(m, wl["plane"] + sgn * ST / 2)
        lv = [z for z in ZL.get(c, ()) if wl["floor"][0] - 60 <= z <= wl["floor"][1] + 60]
        if not lv: continue
        start = None                                               # nearest cell inward (same level) where her capsule fits
        for k in range(4):
            off = sgn * (ST / 2 + k * ST); sx, sy = (wl["plane"] + off, m) if wl["axis"] == "x" else (m, wl["plane"] + off)
            zz = [z for z in ZL.get(cell(sx, sy), ()) if abs(z - lv[0]) < 60]
            if zz and not unreal.SystemLibrary.capsule_overlap_actors(w, V(sx, sy, zz[0] + 120), 38.0, 78.0, OT, None, IGN): start = (sx, sy, zz[0]); break
        if start:
            d = -sgn                                               # push toward the plane
            probes.append({"start": list(start), "dir": [d, 0] if wl["axis"] == "x" else [0, d], "axis": wl["axis"], "plane": wl["plane"], "z": start[2]})
        break
json.dump({"route": pts, "labels": labels, "legs": legs, "probes": probes, "zmin": R["zmin"]}, open(SA + r"\walk_plan.json", "w"), indent=0)
print(f"route {len(pts)} waypoints, {L / 100:.0f} m, legs ok {sum(1 for l in legs if l['ok'])}/{len(legs)} | probes {len(probes)} | hall {hall is not None} hill z {Z[hill] if hill else None}")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
