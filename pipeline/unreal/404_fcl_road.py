"""fantasy_castle_level road: castle bridge landing on the eastern island (15300, 100600) -> down the island's west shore -> wooden causeway over the
lake -> into the Lake Village's walled village.
- island leg: A* over a 5 m grid of traced heights (terrain meshes only, >= 70 cm above the lake, slope-penalised), smoothed,
  laid as the Lake Village's own road spline (BP_PathLine + SM_SoilRoad, one ~5.5 m tile per spline segment)
- causeway: the village pack's wooden SM_Bridge, two spans end to end, decks levelled to the shore heights
- village leg: A* on the village landscape (houses / walls / fences are obstacles) from the causeway to the walled village's
  south-west lane opening at (23900, 50300); the village's own lanes lead on to the plaza
Writes SourceArt/fantasy_castle/route.json (the walkable route, for tests and the cinematic). Actors tagged 'fcl_road'."""
import json, math, heapq, os, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); V = unreal.Vector
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert "fantasy_castle_level." in w.get_path_name(), w.get_path_name()
# spawn into the persistent level, never into the streamed village (fcl_lake_village is rebuilt from the pack)
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_current_level_by_name("fantasy_castle_level")
TAG = unreal.Name("fcl_road"); WATER = 3390.0
for a in eas.get_all_level_actors():
    if TAG in a.tags: eas.destroy_actor(a)
TERRAIN = {"SM_Mount2", "SM_PlaneGr", "SM_EdgeDirtStone", "SM_LongStoneMountain", "SM_mud_low", "SM_mud_Rocky", "SM_groundbigpace"}
def probe(x, y):
    h = unreal.SystemLibrary.line_trace_single(w, V(x, y, 30000), V(x, y, -5000), unreal.TraceTypeQuery.ECC_VISIBILITY, True, [], unreal.DrawDebugTrace.NONE, True)
    t = h.to_tuple() if h else None
    if not t or not (t[0] or t[1]): return None, None
    a = t[9]
    if a is None: return t[4].z, "?"
    if "Landscape" in a.get_class().get_name(): return t[4].z, "Landscape"
    if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh: return t[4].z, a.static_mesh_component.static_mesh.get_name()
    return t[4].z, a.get_class().get_name()
def astar(x0, x1, y0, y1, st, start, goal, walkable, maxslope=0.42, clearance=0, no_corner=False):
    nx, ny = int((x1 - x0) / st) + 1, int((y1 - y0) / st) + 1
    Z = {}; OK = {}
    for j in range(ny):
        for i in range(nx):
            z, k = probe(x0 + i * st, y0 + j * st); Z[i, j] = z; OK[i, j] = walkable(z, k)
    OK0 = dict(OK)
    if clearance:                                   # keep a margin around anything that is not walkable (walls, fences, houses)
        bad = [c for c, ok in OK.items() if not ok]
        for (i, j) in bad:
            for di in range(-clearance, clearance + 1):
                for dj in range(-clearance, clearance + 1):
                    if (i + di, j + dj) in OK: OK[i + di, j + dj] = False
    def cell(p): return (min(nx - 1, max(0, round((p[0] - x0) / st))), min(ny - 1, max(0, round((p[1] - y0) / st))))
    if clearance:                                   # ...but not right at the ends: the gate lane / causeway foot may be narrow
        for p in (start, goal):
            pc = cell(p); r = int(400 / st)
            for di in range(-r, r + 1):
                for dj in range(-r, r + 1):
                    q = (pc[0] + di, pc[1] + dj)
                    if q in OK0: OK[q] = OK0[q]
    def near_ok(c):
        best = None
        for (i, j), ok in OK.items():
            if ok:
                d = (i - c[0]) ** 2 + (j - c[1]) ** 2
                if best is None or d < best[0]: best = (d, (i, j))
        return best[1]
    s, g = near_ok(cell(start)), near_ok(cell(goal))
    openq = [(0.0, s)]; cost = {s: 0.0}; prev = {}
    while openq:
        _, c = heapq.heappop(openq)
        if c == g: break
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                n = (c[0] + di, c[1] + dj)
                if (di or dj) and n in OK and OK[n] and (not (no_corner and di and dj) or (OK.get((c[0] + di, c[1])) and OK.get((c[0], c[1] + dj)))):   # optionally no corner cutting through thin walls
                    run = st * math.hypot(di, dj); slope = abs(Z[n] - Z[c]) / run
                    if slope > maxslope: continue
                    wet = 0.8 if Z[n] < WATER + 120 else 0.0
                    high = max(0.0, Z[n] - 4800.0) / 2500.0             # prefer the low shore to the island's summit
                    nc = cost[c] + run * (1 + 10 * slope * slope + wet + high)
                    if nc < cost.get(n, 1e18):
                        cost[n] = nc; prev[n] = c
                        heapq.heappush(openq, (nc + math.hypot(n[0] - g[0], n[1] - g[1]) * st, n))
    if not (g in prev or g == s):                    # debug picture: S/G, reached (+), walkable (.), blocked (#)
        for jj in range(ny - 1, -1, -2):
            print("".join("S" if (ii, jj) == s else "G" if (ii, jj) == g else "+" if (ii, jj) in cost else "." if OK[ii, jj] else "#" for ii in range(0, nx, 2)))
    assert g in prev or g == s, "no path"
    path = [g]
    while path[-1] != s: path.append(prev[path[-1]])
    path.reverse()
    return [(x0 + i * st, y0 + j * st) for i, j in path]
def smooth(pts, it=3):
    for _ in range(it):
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]): out += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        out.append(pts[-1]); pts = out
    return pts
def resample(pts, step):
    out = [pts[0]]; acc = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1]); t = 0.0
        while acc + seg - t >= step:
            t += step - acc; acc = 0.0; u = t / seg; out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
        acc += seg - t
    if math.hypot(out[-1][0] - pts[-1][0], out[-1][1] - pts[-1][1]) > step * 0.3: out.append(pts[-1])
    return out
ROAD_BP = unreal.EditorAssetLibrary.load_blueprint_class("/Game/Medieval_Lake_Village/BP/BP_PathLine")
ROAD_SM = unreal.load_asset("/Game/Medieval_Lake_Village/Meshs/SM_SoilRoad")
def lay_road(label, pts, lift=8.0):
    raw = []; ctr = []
    for k, (x, y) in enumerate(pts):                 # highest of centre, both edges and just ahead/behind: rides over terrain-mesh lips
        a, b = pts[max(0, k - 1)], pts[min(len(pts) - 1, k + 1)]; dx, dy = b[0] - a[0], b[1] - a[1]; d = math.hypot(dx, dy) or 1.0
        nx_, ny_ = -dy / d, dx / d; tx0, ty0 = dx / d, dy / d
        zc = probe(x, y)[0]
        zs = [probe(x + nx_ * o, y + ny_ * o)[0] for o in (-200.0, 200.0)] + [probe(x + tx0 * o, y + ty0 * o)[0] for o in (-150.0, 150.0)] + [zc]
        zs = [z for z in zs if z is not None]; raw.append(max(zs) if zs else WATER); ctr.append(zc if zc is not None else WATER)
    # smooth along the road (the per-point maxima jump around) without ever dipping under the centre-line ground
    sm = [max(ctr[k], sum(raw[max(0, k - 2):k + 3]) / len(raw[max(0, k - 2):k + 3])) for k in range(len(raw))]
    pts3 = [V(x, y, z + lift) for (x, y), z in zip(pts, sm)]
    a = eas.spawn_actor_from_class(ROAD_BP, pts3[0]); a.set_actor_label(label); a.tags = [TAG]; a.set_folder_path("FCL/Road")
    sp = a.get_editor_property("Spline"); sp.clear_spline_points(True)
    for p in pts3: sp.add_spline_point(p, unreal.SplineCoordinateSpace.WORLD, False)
    sp.update_spline(); sp.set_editor_property("spline_has_been_edited", True)   # else the construction script restores the 2 default points
    a.set_editor_property("StaticMesh", ROAD_SM)                     # property edit re-runs the construction script
    assert len(a.get_components_by_class(unreal.SplineMeshComponent)) == len(pts3) - 1, label + ": spline meshes not built"
    return pts3
# ---- island leg ----
island_ok = lambda z, k: z is not None and k in TERRAIN and z >= WATER + 70
isl = astar(9000, 24000, 64000, 110000, 500, (15300, 100600), (19500, 66000), island_ok)      # from where the castle bridge (SM_BridgeUvd) lands
isl = resample(smooth(isl), 330)
# the castle bridge's deck ends 6 m below the island ground, boxed in by boulders: a stone stair climbs from the deck end to the
# first road point at least 12 m away, and the road starts where the stair arrives
DECK_END = (15050.0, 101250.0)
k0 = next(k for k, p in enumerate(isl) if math.hypot(p[0] - DECK_END[0], p[1] - DECK_END[1]) >= 1200)
isl = isl[k0:]
road1 = lay_road("FCL_Road_Island", isl)
hd = unreal.SystemLibrary.line_trace_single(w, V(DECK_END[0], DECK_END[1], 20000), V(DECK_END[0], DECK_END[1], 0), unreal.TraceTypeQuery.ECC_VISIBILITY, True, [], unreal.DrawDebugTrace.NONE, True).to_tuple()
zb, zt = hd[4].z, road1[0].z - 8
bx, by, tx_, ty_ = DECK_END[0], DECK_END[1], road1[0].x, road1[0].y
run = math.hypot(tx_ - bx, ty_ - by); yaw = math.degrees(math.atan2(ty_ - by, tx_ - bx))
STAIR = unreal.load_asset("/Game/FantasyCastle/Mesh/SM_Stairslong")            # 2400 run (X) x 600 x 1511 rise
st = eas.spawn_actor_from_class(unreal.StaticMeshActor, V((bx + tx_) / 2, (by + ty_) / 2, (zb + zt) / 2), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
st.static_mesh_component.set_static_mesh(STAIR); st.set_actor_scale3d(V(run / 2400.0, 0.7, (zt - zb) / 1511.0))
st.set_actor_label("FCL_Landing_Stair"); st.tags = [TAG]; st.set_folder_path("FCL/Road")
def stz(x, y):
    r = st.static_mesh_component.line_trace_component(V(x, y, 20000), V(x, y, 0), True, False, False); return r[0].z if r else None
u = 60.0 / run; lo = stz(bx + (tx_ - bx) * u, by + (ty_ - by) * u); hi = stz(tx_ - (tx_ - bx) * u, ty_ - (ty_ - by) * u)
if lo is not None and hi is not None and lo > hi: st.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw + 180), False)
hi = stz(tx_ - (tx_ - bx) * u, ty_ - (ty_ - by) * u)
if hi is not None: st.set_actor_location(st.get_actor_location() + V(0, 0, zt - hi), False, True)
print(f"landing stair {run / 100:.1f} m run, {zb:.0f} -> {zt:.0f}")
# ---- causeway: straight south from the island end to the village shore ----
ex, ey = road1[-1].x, road1[-1].y
shore = None
for k in range(1, 200):
    y = ey - 100 * k; z, kind = probe(ex, y)
    if kind == "Landscape" and z is not None and z > WATER + 30 and ey - y > 2000: shore = (ex, y, z); break
assert shore, "no village shore south of the island tip"
BR = unreal.load_asset("/Game/Medieval_Lake_Village/Meshs/SM_Bridge"); blen = 3134.0
span = ey - shore[1] + 300; n = max(1, math.ceil(span / (blen * 0.98)))
y_top = ey + 150; deck = []
for k in range(n):
    cy = y_top - blen * (k + 0.5)
    b = eas.spawn_actor_from_class(unreal.StaticMeshActor, V(ex, cy, 0), unreal.Rotator(roll=0, pitch=0, yaw=0))
    b.static_mesh_component.set_static_mesh(BR); b.set_actor_label(f"FCL_Causeway_{k}"); b.tags = [TAG]; b.set_folder_path("FCL/Road")
    deck.append(b)
# end-of-deck height relative to the actor, against the bridge's own collision (the deck is an arch: ends low, middle high)
def deck_at(b, dy):
    L = b.get_actor_location(); r = b.static_mesh_component.line_trace_component(V(L.x, L.y + dy, L.z + 3000), V(L.x, L.y + dy, L.z - 3000), True, False, False)
    return r[0].z - L.z if r else None
deck_rel = deck_at(deck[0], blen / 2 - 20)
z_from, z_to = road1[-1].z - 6, shore[2]
for k, b in enumerate(deck):                     # tilt each span so its two ends sit on the straight line island end -> village shore
    za = z_from + (z_to - z_from) * k / n; zb = z_from + (z_to - z_from) * (k + 1) / n
    roll = -math.degrees(math.atan2(za - zb, blen))          # +roll lifts the bridge's south (-Y) end
    b.set_actor_location_and_rotation(V(ex, y_top - blen * (k + 0.5), (za + zb) / 2 - deck_rel), unreal.Rotator(roll=roll, pitch=0, yaw=0), False, True)
ends = [(round(deck_at(b, blen / 2 - 20) + b.get_actor_location().z), round(deck_at(b, -blen / 2 + 20) + b.get_actor_location().z)) for b in deck]
print("span end decks (north, south):", ends)
cause_end = (ex, y_top - blen * n)
# ---- village leg: shore -> walled village plaza ----
# village leg: across the open sand field west of the causeway foot to the lane that enters the ring wall's south-west gate
# (read off a top-down view; the A* kept failing in the narrow pocket by the hut at the lane mouth)
VILLAGE_WP = [(21000, 57000), (22500, 55600), (23700, 54800), (24500, 54550), (25000, 54500), (25550, 54500)]
# the walled village's ring wall is unbroken along this field (its own ways in are a cluttered gate lane in the south-west and a
# gatehouse bridge over the river): open a 5 m gap in the ring where the road meets it, at (25000, 54500), with open courtyard inside
GAP, GAP_R = (25000.0, 54500.0), 260.0
for a in eas.get_all_level_actors():
    if "fcl_lake_village" not in a.get_level().get_path_name() or not isinstance(a, unreal.StaticMeshActor) or not a.static_mesh_component.static_mesh: continue
    if not any(k in a.static_mesh_component.static_mesh.get_name() for k in ("StoneWall", "WallPillar")): continue
    o, e = a.get_actor_bounds(False); dx = max(0.0, abs(o.x - GAP[0]) - e.x); dy = max(0.0, abs(o.y - GAP[1]) - e.y)
    if dx * dx + dy * dy < GAP_R * GAP_R: print("opened the ring wall:", a.get_actor_label()); eas.destroy_actor(a)
vl = [(ex, cause_end[1] - 200)] + VILLAGE_WP
vl = resample(smooth(vl), 330)
road2 = lay_road("FCL_Road_Village", vl)
# clear foliage (trees / bushes / grass instances, not seen by the traces) off the road, in both levels
def clear_foliage(pts, r=350.0):
    n = 0
    xs = [p.x for p in pts]; ys = [p.y for p in pts]
    box = unreal.Box(min=V(min(xs) - r, min(ys) - r, -20000), max=V(max(xs) + r, max(ys) + r, 40000))
    for f in [a for a in eas.get_all_level_actors() if a.get_class().get_name() == "InstancedFoliageActor"]:
        for c in f.get_components_by_class(unreal.InstancedStaticMeshComponent):
            kill = []
            for i in (c.get_instances_overlapping_box(box, True) or []):
                t = c.get_instance_transform(i, True).translation
                if min((t.x - p.x) ** 2 + (t.y - p.y) ** 2 for p in pts) < r * r: kill.append(i)
            if kill: c.remove_instances(kill); n += len(kill)
    return n
cleared = clear_foliage(road1) + clear_foliage(road2)
# small scattered props (stone stacks, loose rocks) the 5 m path grid stepped over but the capsule cannot: remove them off the road
KEEP = {"SM_BridgeUvd", "SM_Bridge", "SM_Stairslong", "SM_FloorType1", "SM_Mount2", "SM_PlaneGr", "SM_LongStoneMountain", "SM_EdgeDirtStone"}
def clear_props(pts, r=200.0):
    gone = []
    for a in eas.get_all_level_actors():
        if not isinstance(a, unreal.StaticMeshActor) or not a.static_mesh_component.static_mesh or TAG in a.tags: continue
        if "fcl_lake_village" in a.get_level().get_path_name(): continue          # never touch the village: its leg is routed around structures
        n = a.static_mesh_component.static_mesh.get_name()
        if n in KEEP: continue
        o, e = a.get_actor_bounds(False)
        if max(e.x, e.y) > 1200: continue
        for p in pts:
            dx = max(0.0, abs(p.x - o.x) - e.x); dy = max(0.0, abs(p.y - o.y) - e.y)
            if dx * dx + dy * dy < r * r and o.z + e.z > p.z + 40 and o.z - e.z < p.z + 200:
                gone.append(n); eas.destroy_actor(a); break
    return gone
props_gone = clear_props(road1) + clear_props(road2)
print("props removed off the road:", len(props_gone), sorted(set(props_gone)))
print("foliage instances cleared off the road:", cleared)
route = {"island": [[p.x, p.y, p.z] for p in road1], "causeway": [[ex, y_top, z_from], [ex, cause_end[1], z_to]],
         "village": [[p.x, p.y, p.z] for p in road2], "deck_rel": deck_rel, "spans": n}
os.makedirs(r"E:\code\claude-ue5\claude_ue5\SourceArt\fantasy_castle", exist_ok=True)
json.dump(route, open(r"E:\code\claude-ue5\claude_ue5\SourceArt\fantasy_castle\route.json", "w"), indent=1)
L = lambda pts: sum(math.dist(a[:2], b[:2]) for a, b in zip(pts, pts[1:]))
print(f"island road {len(road1)} pts {L(route['island']) / 100:.0f} m from {route['island'][0][:2]} to {route['island'][-1][:2]} | causeway {n} spans "
      f"{(y_top - cause_end[1]) / 100:.0f} m deck_rel {deck_rel:.0f} z {z_from:.0f}->{z_to:.0f} | village road {len(road2)} pts {L(route['village']) / 100:.0f} m to {route['village'][-1][:2]}")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True); print("saved")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
