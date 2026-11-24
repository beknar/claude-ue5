"""caves rebuilt with the Hyper Cave Building Toolkit (the user's list of 2026-11-22, docs/improvements16.txt; the plan
docs/improvements16_plan.md, phases 8 and 9): "not the same as the dungeon procedural generation, not a dungeon with cave textures".
The game lays the cave itself (C++ RD/RDCave16.cpp: rooms of the kit's sizes on the dungeon's tile grid joined by winding tunnels
whose paths are tile paths) and draws it with the kit's meshes: its rooms' combined meshes, its tunnel meshes bent along splines
(spline-mesh components, as the kit's BP_Cave_Spline_* do), its caps at dead ends and its stairs between heights.
Parts:
- collide: copies of the kit's tunnel meshes whose collision is a reduced LOD (a bent piece's collision is cooked in play)
- level: the kit and bCave16 written onto the cave level's generator, its start set built again
- measure: each room's walkable tiles and floor heights, each tunnel's floor, traced on the meshes
- study: the kit's example map (Map_Example_Caves) read once: each room kind's mesh, size and connection points (the Blueprints'
  arrows, where a tunnel meets the room), the roof hole and god-ray points, the stairs' two ends, the tunnels' meshes, their
  cross-section and segment length (the spline's tangent), the cap; written to SourceArt/caves/hyper16.json for the game.
Args: <part> [check]"""
import sys, os, json, gc, math, unreal

ARGS = [a.lower() for a in sys.argv[1:]]
CHECK = "check" in ARGS
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\caves"
OUT = os.path.join(SA, "hyper16.json")
EXAMPLE = "/Game/Hyper/Environment_Building/Cave/Map/Map_Example_Caves"
KIT = "/Game/Hyper/Environment_Building/Cave/"
ROOMS = {"BP_Cave_Room_Small_01_C": "small", "BP_Cave_Room_Medium_01_C": "medium", "BP_Cave_Room_Large_01_C": "large",
         "BP_Cave_Stairs_Large_01_C": "stairs"}
TUNNELS = {"small": "CombinedMeshes/Tunnels/SM_CaveTunnel_Small", "medium": "CombinedMeshes/Tunnels/SM_CaveTunnel_medium",
           "large": "CombinedMeshes/Tunnels/SM_CaveTunnel_Large"}
TUNNEL_BP = {"BP_Cave_Spline_Small_C": "small", "BP_Cave_Spline_Medium_C": "medium", "BP_Cave_Spline_Large_C": "large"}


def r1(v): return round(float(v), 1)


def box(m):
    b = m.get_bounding_box()
    return {"min": [r1(b.min.x), r1(b.min.y), r1(b.min.z)], "max": [r1(b.max.x), r1(b.max.y), r1(b.max.z)]}


def rel(c):
    l = c.get_editor_property("relative_location"); r = c.get_editor_property("relative_rotation")
    return [r1(l.x), r1(l.y), r1(l.z), r1(r.yaw)]


def study():
    unreal.EditorLoadingAndSavingUtils.load_map(EXAMPLE)
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    acts = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor)
    out = {"source": EXAMPLE, "rooms": {}, "tunnels": {}, "cap": None}
    for a in acts:
        cn = a.get_class().get_name()
        if cn in ROOMS and ROOMS[cn] not in out["rooms"]:
            sms = [c for c in a.get_components_by_class(unreal.StaticMeshComponent) if not isinstance(c, unreal.InstancedStaticMeshComponent)]
            room = next(c for c in sms if c.get_name() == "Room_Mesh")
            e = {"blueprint": a.get_class().get_path_name(), "mesh": room.static_mesh.get_path_name(), "box": box(room.static_mesh),
                 # a connection: where a tunnel's end meets the room (x, y, z in the room's frame, the arrow's yaw pointing out)
                 "connections": [rel(c) for c in sorted(a.get_components_by_class(unreal.ArrowComponent), key=lambda c: c.get_name())],
                 "roof": [], "godray": None}
            for c in sms:
                if c is not room and c.static_mesh: e["roof"].append({"mesh": c.static_mesh.get_path_name(), "at": rel(c)})
            for c in a.get_components_by_class(unreal.SceneComponent):
                if c.get_name() == "Godray_Parent": e["godray"] = rel(c)
            out["rooms"][ROOMS[cn]] = e
        elif cn in TUNNEL_BP:
            kind = TUNNEL_BP[cn]
            seg = a.get_components_by_class(unreal.SplineMeshComponent)
            if not seg or kind in out["tunnels"]: continue
            st = [c.get_start_tangent().length() for c in seg]
            steps = [(c.get_end_position() - c.get_start_position()).length() for c in seg]
            # successive segments overlap: the next starts before this one's end
            laps = [(seg[i].get_end_position() - seg[i + 1].get_start_position()).length() for i in range(len(seg) - 1)]
            m = seg[0].static_mesh
            out["tunnels"][kind] = {"blueprint": a.get_class().get_path_name(), "mesh": m.get_path_name(), "box": box(m),
                                    "forward": "x", "tangent": r1(sorted(st)[len(st) // 2]), "segment": r1(sum(steps) / len(steps)),
                                    "overlap": r1(sum(laps) / max(len(laps), 1)), "height_var": r1(a.get_editor_property("Height"))}
        elif cn == "BP_Cave_Cap_01_C" and not out["cap"]:
            c = a.get_components_by_class(unreal.StaticMeshComponent)[0]
            out["cap"] = {"blueprint": a.get_class().get_path_name(), "mesh": c.static_mesh.get_path_name(), "box": box(c.static_mesh)}
    for k, p in TUNNELS.items():
        if k not in out["tunnels"]: print("CAVE16 no tunnel of kind", k, "in the example: its mesh only"); m = unreal.load_asset(KIT + p); out["tunnels"][k] = {"mesh": m.get_path_name(), "box": box(m), "forward": "x"}
    for k in ("small", "medium", "large", "stairs"):
        if k not in out["rooms"]: raise RuntimeError("no room of kind " + k + " in the example map")
    for k, e in out["rooms"].items(): print("CAVE16 room", k, "connections", len(e["connections"]), "box", e["box"])
    for k, e in out["tunnels"].items(): print("CAVE16 tunnel", k, e)
    if CHECK: print("CAVE16 check: not written"); return
    open(OUT, "w", encoding="utf-8").write(json.dumps(out, indent=1) + "\n")
    print("CAVE16 wrote", OUT)


TILE = 300.0
SCRATCH = "/Game/RandomLevel/Test/rl_scratch"


def trace(w, a, b):
    """the first surface a ray meets (complex collision: the kit's meshes are their own faces): (z, normal z) or None"""
    h = unreal.SystemLibrary.line_trace_single(w, a, b, unreal.TraceTypeQuery.ECC_VISIBILITY, True, [], unreal.DrawDebugTrace.NONE, True)
    if not h: return None
    t = h.to_tuple()
    return t[4].z, t[7].z          # (impact point, impact normal)


def floor_at(w, x, y, z0, z1):
    """the floor under (x, y) between z1 (above) and z0 (below) with room over it: its height, or None (a wall, a slope too steep,
    rock within 2.5 m over it). The kit's rooms are open at the top (a roof piece closes them), so the ray from above meets the
    floor first; outside a room's walls it meets their backs or nothing (the tiles joined to the middle are kept)"""
    f = trace(w, unreal.Vector(x, y, z1), unreal.Vector(x, y, z0))
    if not f or f[1] < 0.7: return None
    if trace(w, unreal.Vector(x, y, f[0] + 30.0), unreal.Vector(x, y, f[0] + 250.0)): return None
    return f[0]


def walk_tile(w, cx, cy, z0, z1, rise=60.0):
    """a tile she can stand anywhere on: its middle and four points 100 cm off it on floor within 60 cm of each other; the middle's
    height"""
    # (the stairs: their treads' edges and rails turn the rays off them at points 1 m apart: the middle alone)
    pts = ((0, 0),) if rise > 90.0 else ((0, 0), (100, 0), (-100, 0), (0, 100), (0, -100))
    zs = [floor_at(w, cx + dx, cy + dy, z0, z1) for dx, dy in pts]
    if any(z is None for z in zs) or max(zs) - min(zs) > rise: return None
    return zs[0]


def mask_of(w, mesh, z0, z1, rise=60.0):
    """the walkable tiles of a mesh standing at the origin: tile (i, j)'s middle at ((i - pivot x) * TILE, (j - pivot y) * TILE);
    only the tiles joined to the one nearest the mesh's middle (the floor outside its walls left out). Returns the size, the pivot's
    tile, the mask and each tile's floor height (cm, 0 where not walkable)"""
    b = mesh.get_bounding_box()
    i0, i1 = int(b.min.x // TILE) - 1, int(b.max.x // TILE) + 2
    j0, j1 = int(b.min.y // TILE) - 1, int(b.max.y // TILE) + 2
    W, H = i1 - i0, j1 - j0
    Z = {}
    for j in range(H):
        for i in range(W):
            z = walk_tile(w, (i + i0) * TILE, (j + j0) * TILE, z0, z1, rise)
            if z is not None: Z[(i, j)] = z
    if not Z: raise RuntimeError("no floor found on " + mesh.get_name())
    cx, cy = -i0 + (b.min.x + b.max.x) * 0.5 / TILE, -j0 + (b.min.y + b.max.y) * 0.5 / TILE
    seed = min(Z, key=lambda t: (t[0] - cx) ** 2 + (t[1] - cy) ** 2)
    keep, todo = {seed}, [seed]
    while todo:
        i, j = todo.pop()
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (i + d[0], j + d[1])
            if n in Z and n not in keep and abs(Z[n] - Z[(i, j)]) < max(80.0, rise * 1.6): keep.add(n); todo.append(n)
    mask = [1 if (i, j) in keep else 0 for j in range(H) for i in range(W)]
    zs = [r1(Z[(i, j)]) if (i, j) in keep else 0.0 for j in range(H) for i in range(W)]
    return [W, H], [-i0, -j0], mask, zs


def measure():
    """each room's walkable tiles and their floor heights (traced on its mesh at the origin of the scratch level), each tunnel's
    walkable half-width and floor height across its middle"""
    kit = json.load(open(OUT, encoding="utf-8"))
    unreal.EditorLoadingAndSavingUtils.load_map(SCRATCH)
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    def stand(path):
        a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0))
        c = a.static_mesh_component; c.set_static_mesh(unreal.load_asset(path.split(".")[0]))
        c.set_collision_profile_name("BlockAll"); return a
    for k, e in kit["rooms"].items():
        a = stand(e["mesh"])
        try:
            # (the rays start inside the cavity: from above its roof they meet the roof's back (a tunnel's at 7 m); the stairs rise
            # 1.2 m a tile)
            size, pivot, mask, zs = mask_of(w, a.static_mesh_component.static_mesh, -600.0, 400.0 if k != "stairs" else 700.0, 60.0 if k != "stairs" else 100.0)
        finally:
            a.destroy_actor()
        e.update({"size": size, "pivot": pivot, "mask": mask, "floor": zs})
        print("CAVE16 room", k, "tiles", sum(mask), "of", size, "floor", min(z for z, m in zip(zs, mask) if m), "to", max(z for z, m in zip(zs, mask) if m))
    for k, e in kit["tunnels"].items():
        a = stand(e["mesh"])
        try:
            b = a.static_mesh_component.static_mesh.get_bounding_box(); mx = (b.min.x + b.max.x) * 0.5
            ys = [y * 25.0 for y in range(int(b.min.y // 25), int(b.max.y // 25) + 1)]
            fl = {y: floor_at(w, mx, y, -600.0, 300.0) for y in ys}
            mid = fl.get(0.0)
            if mid is None: raise RuntimeError("no floor in the middle of tunnel " + k)
            def run(sign):
                y = 0.0
                while fl.get(y + 25.0 * sign) is not None and abs(fl[y + 25.0 * sign] - mid) < 80.0: y += 25.0 * sign
                return abs(y)
            e.update({"half_walk": r1(min(run(1), run(-1))), "floor_z": r1(mid)})
        finally:
            a.destroy_actor()
        print("CAVE16 tunnel", k, "walkable half-width", e["half_walk"], "floor", e["floor_z"])
    if CHECK: print("CAVE16 check: not written"); return
    open(OUT, "w", encoding="utf-8").write(json.dumps(kit, indent=1) + "\n")
    print("CAVE16 wrote", OUT)


def dressing():
    """the kit's PCG dressing measured on its example map (phase 9: the game scatters the same meshes at the same densities): for each
    mesh its instances a metre of tunnel (floor and roof apart: height over the spline under or over 4 m) and a walkable tile of room,
    their distance from the tunnel's line as a share of its half-width, their scales; the rooms' wall-light points (their Blueprints'
    Wall_Light_Parent children), the kit's torch (BP_WallTorch's mesh, fire and light) and god ray"""
    kit = json.load(open(OUT, encoding="utf-8"))
    unreal.EditorLoadingAndSavingUtils.load_map(EXAMPLE)
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    tun, room = {}, {}
    tun_len, room_tiles = 0.0, 0
    tiles_of = {k: sum(e["mask"]) for k, e in kit["rooms"].items()}
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        cn = a.get_class().get_name()
        if cn in TUNNEL_BP:
            sp = a.get_components_by_class(unreal.SplineComponent)[0]
            if sp.get_number_of_spline_points() < 2: continue
            L = sp.get_spline_length(); tun_len += L
            half = kit["tunnels"][TUNNEL_BP[cn]]["box"]["max"][1]
            seen = set()
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                m = c.static_mesh
                if not m or c.get_instance_count() == 0: continue
                key = (m.get_path_name(), c.get_instance_count(), round(c.get_instance_transform(0, True).translation.x))
                if key in seen: continue          # (the same PCG output listed twice)
                seen.add(key)
                e = tun.setdefault(m.get_path_name(), {"n": 0, "roof": 0, "lat": [], "scale": []})
                for i in range(c.get_instance_count()):
                    t = c.get_instance_transform(i, True); p = t.translation
                    k_ = sp.find_input_key_closest_to_world_location(p)
                    q = sp.get_location_at_spline_input_key(k_, unreal.SplineCoordinateSpace.WORLD)
                    e["n"] += 1; e["roof"] += 1 if p.z - q.z > 400.0 else 0
                    e["lat"].append(min(1.5, math.hypot(p.x - q.x, p.y - q.y) / max(half, 1.0))); e["scale"].append(t.scale3d.x)
        elif cn in ROOMS and ROOMS[cn] != "stairs":
            room_tiles += tiles_of[ROOMS[cn]]
            seen = set()
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                m = c.static_mesh
                if not m or c.get_instance_count() == 0: continue
                key = (m.get_path_name(), c.get_instance_count(), round(c.get_instance_transform(0, True).translation.x))
                if key in seen: continue          # (the same PCG output listed twice, as in the tunnels: PR #116's review)
                seen.add(key)
                e = room.setdefault(m.get_path_name(), {"n": 0, "scale": []})
                for i in range(c.get_instance_count()):
                    e["n"] += 1; e["scale"].append(c.get_instance_transform(i, True).scale3d.x)
    def q(v, f): v = sorted(v); return round(v[int(f * (len(v) - 1))], 2) if v else 1.0
    out = {"tunnel": [], "room": []}
    for m, e in sorted(tun.items()):
        out["tunnel"].append({"mesh": m, "per_m": round(e["n"] / (tun_len / 100.0), 3), "roof_share": round(e["roof"] / e["n"], 2),
                              "lat": [q(e["lat"], 0.1), q(e["lat"], 0.9)], "scale": [q(e["scale"], 0.1), q(e["scale"], 0.9)]})
    for m, e in sorted(room.items()):
        out["room"].append({"mesh": m, "per_tile": round(e["n"] / max(room_tiles, 1), 3), "scale": [q(e["scale"], 0.1), q(e["scale"], 0.9)]})
    # (the rooms' wall-light points, in each room's frame: each point's world transform against the room actor's (relative to their
    # parent they would miss any offset or turn of Wall_Light_Parent), measured again on every run, from the first room of a kind that
    # has any (PR #116's review))
    got = set()
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        cn = a.get_class().get_name()
        if cn not in ROOMS or ROOMS[cn] in got: continue
        at = a.get_actor_transform(); pts = []
        for c in a.get_components_by_class(unreal.SceneComponent):
            if not (c.get_attach_parent() and c.get_attach_parent().get_name() == "Wall_Light_Parent"): continue
            r_ = c.get_world_transform().make_relative(at)
            l_ = r_.translation; pts.append([r1(l_.x), r1(l_.y), r1(l_.z), r1(r_.rotation.rotator().yaw)])
        if pts: kit["rooms"][ROOMS[cn]]["lights"] = pts; got.add(ROOMS[cn])
    gr = [a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor) if a.get_class().get_name() == "BP_GodRay_Sun_C"]
    if gr:
        c = gr[0].get_components_by_class(unreal.StaticMeshComponent)[0]
        mt = c.get_material(0)
        while isinstance(mt, unreal.MaterialInstanceDynamic): mt = mt.get_editor_property("parent")          # (the kit's instance under the level's dynamic one)
        out["godray"] = {"mesh": c.static_mesh.get_path_name(), "material": mt.get_path_name() if mt else GODRAY_MI, "scale": [round(v, 2) for v in (c.get_world_scale().x, c.get_world_scale().y, c.get_world_scale().z)],
                         "pitch": round(c.get_world_rotation().pitch, 1), "yaw": round(c.get_world_rotation().yaw, 1)}
    kit["dressing"] = out
    kit["torch"] = {"mesh": "/Game/Hyper/ResourcePack/Structures/Wall_Torch/Mesh/SM_Wall_Torch.SM_Wall_Torch", "fire": "/Game/Hyper/ResourcePack/Effects/Particles/2DGas/NS_2DGasIntro.NS_2DGasIntro",
                    "fire_at": [0, -29, 109], "light_at": [0, -45, 80]}
    for e in out["tunnel"]: print("CAVE16 tunnel dressing", e)
    for e in out["room"]: print("CAVE16 room dressing", e)
    print("CAVE16 godray", out.get("godray"), "| lights", {k: len(e.get("lights", [])) for k, e in kit["rooms"].items()})
    if CHECK: print("CAVE16 check: not written"); return
    open(OUT, "w", encoding="utf-8").write(json.dumps(kit, indent=1) + "\n")


TREASURE = os.path.join(SA, "treasure16.json")
SA_ROOT = os.path.dirname(SA)
# (phase 12: a set's side tunnels (rooms joined both ways) carry the rubble and its cache: at 0.2 one loop was tried a set and nearly
# every set came out a tree (no rubble in five sets)
LOOP_SHARE = 0.6
MAPS16 = "/Game/RandomDungeon/Maps/"
ITEM_KINDS = {"COMPONENT": "COMPONENT", "REPAIR": "REPAIR", "HEALING": "HEALING", "MANA": "MANA", "FOOD": "FOOD", "SCROLL": "SCROLL", "WEAPON": "WEAPON",
              "ARMOUR": "ARMOUR", "RING": "RING", "TOME": "TOME", "TOKEN": "TOKEN", "RECIPE": "RECIPE", "SHIELD": "SHIELD"}


def treasure_phases():
    """every phase's block of treasure16.json, in order (phase10, phase11, ...)"""
    T = json.load(open(TREASURE, encoding="utf-8"))
    return T, [T[k] for k in sorted(k for k in T if k.startswith("phase"))]


def each_map(maps, fn, label):
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    out = []
    for m in maps:
        if not unreal.EditorAssetLibrary.does_asset_exist(MAPS16 + m): out.append(f"{label}: no map {m}"); continue
        les.load_level(MAPS16 + m); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
        what = fn(g)
        g.modify(); les.save_current_level()
        g = None; gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        out.append(f"945 {label} {m}: {what}")
    for l in out: print(l)


BANDS = ["", "Fine ", "Masterwork ", "Exalted ", "Celestial ", "Divine "]


def w854():
    """854's measuring functions (pca, slices, verts, the vector helpers), its module's definitions only"""
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "854_rdm5_weapons_meshes.py"), encoding="utf-8").read()
    ns = {"__name__": "w854"}
    exec(src[:src.index("\nres = {")], ns)
    return ns


def pick_frame(ns, P):
    """a pick's frame as 854's blade frame is read: the origin where the hand closes (22 % up the handle from its end), x toward
    the head, y the head's spread (its point's way), z square to them"""
    c, (a, b, z) = ns["pca"](P)
    dot, sub, add, mul, norm, cross = ns["dot"], ns["sub"], ns["add"], ns["mul"], ns["norm"], ns["cross"]
    t = [dot(sub(q, c), a) for q in P]; t0, t1 = min(t), max(t)
    def width(lo, hi):
        Q = [q for q, tt in zip(P, t) if lo <= tt <= hi]
        if len(Q) < 2: return 0.0
        return max(max(dot(sub(q, c), b) for q in Q) - min(dot(sub(q, c), b) for q in Q), max(dot(sub(q, c), z) for q in Q) - min(dot(sub(q, c), z) for q in Q))
    head_hi = width(t1 - 10.0, t1) >= width(t0, t0 + 10.0)
    X = a if head_hi else mul(a, -1.0)
    tg = t0 + 0.22 * (t1 - t0) if head_hi else t1 - 0.22 * (t1 - t0)
    near = [q for q, tt in zip(P, t) if abs(tt - tg) < 2.0] or P
    ctr = ns["mean"](near)
    origin = add(c, add(mul(a, tg), add(mul(b, dot(sub(ctr, c), b)), mul(z, dot(sub(ctr, c), z)))))
    H = [sub(q, c) for q, tt in zip(P, t) if (tt > t1 - 12.0 if head_hi else tt < t0 + 12.0)]
    Hc = [sub(h, mul(a, dot(h, a))) for h in H]
    _, (hb, _, _) = ns["pca"]([tuple(h) for h in Hc]) if len(Hc) >= 3 else (None, (b, None, None))
    Y = norm(sub(hb, mul(X, dot(hb, X)))); Z = norm(cross(X, Y)); Y = norm(cross(Z, X))
    return {"origin": origin, "x": X, "y": Y, "z": Z, "length": t1 - t0}


def frame_tf(fr):
    """a frame (origin, x, y) as a transform from the frame's space into the mesh's"""
    rot = unreal.MathLibrary.make_rot_from_xy(unreal.Vector(*fr["x"]), unreal.Vector(*fr["y"]))
    return unreal.Transform(unreal.Vector(*fr["origin"]), rot, unreal.Vector(1, 1, 1))


def cave_weapons(its, P, missing):
    """phase 12's weapons on a map: (items, looks, mended, lightless, breakers, lost bases, their names)"""
    W = [w for p_ in P for w in p_.get("weapons", [])]
    if not W: return [], {}, {}, [], [], [], []
    frames = json.load(open(os.path.join(SA_ROOT, "random_dungeon_magic5", "weapon_frames.json"), encoding="utf-8"))["weapons"]
    ns = None; swapped = {}
    out, looks, mends, lightless, breakers, lost, names = [], {}, {}, [], [], [], []
    by = {str(i.name): i for i in its}
    for w in W:
        for band in BANDS:
            like = by.get(band + w["like"])
            # (a map has the bands its tiers have: the plain one always, the others where 910 made them)
            if not like:
                if not band: missing.append(f"no {w['like']} for {w['name']}")
                continue
            nm = band + w["name"]; names.append(nm)
            it = unreal.RDItemDef(); it.import_text(like.export_text())
            it.set_editor_property("name", nm); it.set_editor_property("icon", unreal.Name(w["icon"])); it.set_editor_property("looks", w["looks"])
            it.set_editor_property("weight", float(w["weight"]))
            if "durability" in w and like.get_editor_property("durability") > 0: it.set_editor_property("durability", like.get_editor_property("durability") * w["durability"])
            fits = []
            for f in it.get_editor_property("weapon_fits"):
                wd = f.get_editor_property("weapon")
                wd.set_editor_property("name", nm); wd.set_editor_property("item", nm); wd.set_editor_property("icon", unreal.Name(w["icon"]))
                wd.set_editor_property("damage", wd.get_editor_property("damage") * w["damage"])
                if wd.get_editor_property("durability") > 0: wd.set_editor_property("durability", wd.get_editor_property("durability") * w["durability"])
                if w.get("lightless"):
                    for k in ("bolt_effect", "bolt_core_effect"): wd.set_editor_property(k, None)
                if w.get("mesh"):
                    m = unreal.load_asset(w["mesh"])
                    if not m: missing.append(f"no mesh {w['mesh']}"); continue
                    if w["mesh"] not in swapped:
                        ns = ns or w854()
                        k_ = "".join(c for c in w["like"].title() if c.isalnum())
                        if k_ not in frames: missing.append(f"no frame of {w['like']} ({k_})"); continue
                        nf = pick_frame(ns, ns["verts"](m))
                        swapped[w["mesh"]] = (frame_tf(frames[k_]), frame_tf(nf), nf)
                    F, Fn, nf = swapped[w["mesh"]]
                    g0 = wd.get_editor_property("grip")
                    # (the new mesh's frame where the old one's was in her hand: grip' = inverse(F') * F * grip)
                    g1 = unreal.MathLibrary.compose_transforms(unreal.MathLibrary.compose_transforms(unreal.MathLibrary.invert_transform(Fn), F), g0)
                    wd.set_editor_property("mesh", m); wd.set_editor_property("grip", g1)
                f.set_editor_property("weapon", wd); fits.append(f)
            it.set_editor_property("weapon_fits", fits)
            out.append(it)
            if w.get("material"):
                mt = unreal.load_asset(w["material"])
                if mt: looks[unreal.Name(nm)] = mt
                else: missing.append(f"no material {w['material']}")
            if w.get("mended_by"):
                e = unreal.RDMend16(); e.set_editor_property("by", [unreal.Name(x) for x in w["mended_by"]]); e.set_editor_property("share", float(w.get("mend_share", 0.25))); mends[unreal.Name(nm)] = e
            if w.get("lightless"): lightless.append(unreal.Name(nm))
            if w.get("breaks_rubble"): breakers.append(unreal.Name(nm))
        if w.get("lost"): lost.append(unreal.Name(w["name"]))
    for k_, (F, Fn, nf) in swapped.items(): print(f"945 weapons: {k_.split('/')[-1]} on its like's grip (its handle {nf['length']:.0f} cm, the hand 22 % up it)")
    return out, looks, mends, lightless, breakers, lost, names


def items():
    """the caves' treasures of every phase written so far (treasure16.json) on every map of the game: each item copied from its 'like'
    (its kind, numbers, buff, picture, tiers, weight, words), its recipe where it has one; the caves' own items (CaveItems16) on every
    map (drawn only in a cave), the regions and the veins and growths. Idempotent: its own items and recipes taken out first, by name.
    Run after 910, 905, 911, 918, 925, 928, 929, 937, 938 and 943 (they write the items anew)"""
    T, P = treasure_phases()
    X = [x for p in P for x in p.get("items", [])]
    mine = {x["name"] for x in X} | {b + w["name"] for p in P for w in p.get("weapons", []) for b in BANDS}
    regions = [r for p in P for r in p.get("regions", [])]
    nodes = [n for p in P for n in p.get("nodes", [])]
    def fn(g):
        its = [i for i in g.get_editor_property("items") if str(i.name) not in mine]
        recs = [r for r in g.get_editor_property("recipes") if str(r.item) not in mine]
        have = {str(i.name) for i in its} | mine
        missing = []
        for x in X:
            like = next((i for i in its if str(i.name) == x["like"]), None)
            # (a map without the 'like' (not every map has every material): the first of the item's kind there)
            if not like: like = next((i for i in its if str(i.kind).endswith("." + ITEM_KINDS[x["kind"]]) or ITEM_KINDS[x["kind"]] in str(i.kind)), None)
            if not like: missing.append(f"no {x['like']} or any {x['kind']} to copy for {x['name']}"); continue
            it = unreal.RDItemDef()
            for k in ("kind", "amount", "seconds", "weight", "icon", "looks", "tiers", "found_max", "durability", "armour_weight", "armour_type"):
                it.set_editor_property(k, like.get_editor_property(k))
            it.set_editor_property("name", x["name"])
            it.set_editor_property("kind", getattr(unreal.RDItemKind, ITEM_KINDS[x["kind"]]))
            for k in ("amount", "seconds", "weight"):
                if k in x: it.set_editor_property(k, float(x[k]))
            it.set_editor_property("icon", unreal.Name(x["icon"])); it.set_editor_property("looks", x.get("looks", ""))
            it.set_editor_property("tiers", list(x.get("tiers", [])))
            if "found_max" in x: it.set_editor_property("found_max", int(x["found_max"]))
            if x.get("repairs"): it.set_editor_property("armour_type", x["repairs"])
            if x.get("buff"):
                it.set_editor_property("buff_kind", unreal.Name(x["buff"][0])); it.set_editor_property("buff_amount", float(x["buff"][1])); it.set_editor_property("buff_seconds", float(x["buff"][2]))
            else:
                it.set_editor_property("buff_kind", unreal.Name("None")); it.set_editor_property("buff_amount", 0.0); it.set_editor_property("buff_seconds", 0.0)
            its.append(it)
            if x.get("recipe"):
                st, parts = x["recipe"]
                rc = unreal.RDRecipe(); rc.item = x["name"]; rc.tier = 0; rc.station = st
                ps = []
                for lb, any_of, n in parts:
                    if not any(a in have for a in any_of): missing.append(f"{x['name']}: no {any_of}")
                    p = unreal.RDRecipePart(); p.label = lb; p.any_of = [unreal.Name(a) for a in any_of if a in have]; p.count = int(n); ps.append(p)
                rc.parts = ps; recs.append(rc)
        # (phase 11: the inks stand in for every scroll recipe's reagent (its part that is not an essence); taken off every recipe first,
        # so a re-run adds them once)
        inks = [x["name"] for x in X if x.get("ink")]
        kinds = {str(i.name): str(i.kind) for i in its}
        recs2 = []
        for r in recs:
            ps = []
            for p_ in r.parts:
                q = unreal.RDRecipePart(); q.label = p_.label; q.count = p_.count
                q.any_of = [a_ for a_ in p_.any_of if str(a_) not in inks]
                ps.append(q)
            if inks and "SCROLL" in kinds.get(str(r.item), "") and str(r.item) not in mine:
                # (the reagent: the first part that is not an essence, only it (PR #118's review: Starfall's and Singularity's seraph
                # feather, their second, was an ink away))
                q = next((q for q in ps if "essence" not in str(q.label).lower()), None)
                if q is not None: q.any_of = list(q.any_of) + [unreal.Name(n) for n in inks]
            r.parts = ps; recs2.append(r)
        recs = recs2
        # (phase 12: the caves' weapons, copied band by band from the table's)
        wits, looks, mends, lightless, breakers, lost, wnames = cave_weapons(its, P, missing)
        its = its + wits
        g.set_editor_property("items", its); g.set_editor_property("recipes", recs)
        g.set_editor_property("weapon_looks16", looks); g.set_editor_property("mend_only16", mends)
        g.set_editor_property("lightless16", lightless); g.set_editor_property("rubble_breakers16", breakers); g.set_editor_property("lost_blades16", lost)
        rb = next((p_["rubble"] for p_ in P if p_.get("rubble")), None)
        if rb:
            g.set_editor_property("rubble_meshes16", [m for m in (unreal.load_asset(x) for x in rb["meshes"]) if m])
            g.set_editor_property("rubble_scale16", unreal.Vector2D(*rb["scale"])); g.set_editor_property("rubble_share16", float(rb["share"]))
            g.set_editor_property("rubble_hero16", rb["hero"]); g.set_editor_property("rubble_hero_hits16", int(rb["hero_hits"]))
        lb = next((p_["lost"] for p_ in P if p_.get("lost")), None)
        if lb:
            g.set_editor_property("lost_skeleton16", unreal.load_asset(lb["skeleton"])); g.set_editor_property("lost_skeleton_turn16", unreal.Rotator(*lb["turn"]))
        sk = {}
        for p_ in P:
            for n, (stat, amt) in p_.get("sockets", {}).items():
                e = unreal.RDSocket16(); e.set_editor_property("stat", stat); e.set_editor_property("amount", float(amt)); sk[unreal.Name(n)] = e
        g.set_editor_property("socket_stones16", sk)
        g.set_editor_property("cave_items16", [unreal.Name(x["name"]) for x in X if x.get("cave")] + [unreal.Name(n) for n in wnames])
        # (made at the anvil whatever their kind: a recipe with the anvil's station '' on a kind the tables would send to the
        # alchemist (the linings, kind HEALING for their buff; PR #117's review))
        g.set_editor_property("anvil_made16", [unreal.Name(x["name"]) for x in X if x.get("recipe") and x["recipe"][0] == "" and x["kind"] in ("HEALING", "MANA", "SPEED")])
        rg = []
        for r in regions:
            e = unreal.RDCaveRegion16(); e.set_editor_property("name", r["name"]); e.set_editor_property("biomes", r["biomes"]); e.set_editor_property("items", [unreal.Name(i) for i in r["items"]]); rg.append(e)
        g.set_editor_property("cave_regions16", rg)
        nd = []
        for n in nodes:
            m = unreal.load_asset(n["mesh"])
            if not m: missing.append(f"no mesh {n['mesh']}"); continue
            e = unreal.RDCaveNode16(); e.set_editor_property("mesh", m); e.set_editor_property("item", n["item"])
            e.set_editor_property("scale", unreal.Vector2D(*n["scale"])); e.set_editor_property("count", unreal.IntPoint(*n["count"]))
            e.set_editor_property("per_room", unreal.IntPoint(*n["per_room"])); e.set_editor_property("wall", bool(n["wall"]))
            if n.get("region"): e.set_editor_property("region", n["region"])
            if n.get("material"): e.set_editor_property("material", unreal.load_asset(n["material"]))          # (the vein: the kit's rocks in dark iron (the first, a pack's crystal, was a caged lamp))
            nd.append(e)
        g.set_editor_property("cave_nodes16", nd)
        assert not missing, f"945 items: {missing}"
        n_ink = sum(1 for r in recs if any(str(a_) in inks for p_ in r.parts for a_ in p_.any_of)) if inks else 0
        return f"{len(wits)} cave weapons, {len(X)} cave things ({sum(1 for x in X if x.get('recipe'))} with recipes), {len(rg)} regions, {len(nd)} veins and growths, {len(sk)} socket stones, inks in {n_ink} scroll recipes"
    if CHECK: print("945 items: would write", len(X), "things on", T["maps"]); return
    each_map(T["maps"], fn, "items")


def icons():
    """the caves' pictures (SourceArt/caves/icons16/icon_<icon>.png) imported and given to every map's UIArt under their names"""
    import importlib
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    ui_texture = importlib.import_module("ui_tex").ui_texture
    T, P = treasure_phases()
    src = os.path.join(SA, "icons16")
    names = sorted({x["icon"] for p in P for x in p.get("items", []) + p.get("weapons", [])})
    found = [n for n in names if os.path.exists(os.path.join(src, f"icon_{n}.png"))]
    lost = sorted(set(names) - set(found))
    if lost: print("945 icons: no picture for", lost)
    if CHECK: print("945 icons: would import", len(found)); return
    tex = {n: ui_texture(os.path.join(src, f"icon_{n}.png"), "/Game/RandomDungeon/UI/Caves16", f"T_Cave16_{n}") for n in found}
    def fn(g):
        ua = g.get_editor_property("ui_art")
        for n, t in tex.items():
            art = unreal.RDUIArt(); art.set_editor_property("texture", t)
            art.set_editor_property("border", unreal.Vector4(0, 0, 0, 0)); art.set_editor_property("inner", unreal.Vector4(0, 0, 1, 1))
            ua[unreal.Name(n)] = art
        g.set_editor_property("ui_art", ua)
        return f"{len(tex)} pictures"
    each_map(T["maps"], fn, "icons")


COLLIDE = "/Game/RandomDungeon/Caves16"


def collide():
    """copies of the kit's tunnel meshes whose collision is a reduced level of detail (a tenth of the triangles, LODForCollision 1):
    a bent piece's collision is cooked in play from the mesh's triangles, at once (USplineMeshComponent::RecreateCollision), and the
    kit's 20,000 to 30,000 took a ring set's shell 3 s in one frame. Their looks stay the kit's (Nanite draws LOD 0)"""
    eal = unreal.EditorAssetLibrary; sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    kit = json.load(open(OUT, encoding="utf-8"))
    for k, e in kit["tunnels"].items():
        src = e["mesh"].split(".")[0]; dst = COLLIDE + "/" + src.rsplit("/", 1)[1] + "_C"
        if CHECK: print("CAVE16 would copy", src, "->", dst); continue
        if eal.does_asset_exist(dst): eal.delete_asset(dst)
        m = eal.duplicate_asset(src, dst)
        o = unreal.StaticMeshReductionOptions()
        o.set_editor_property("auto_compute_lod_screen_size", False)
        o.set_editor_property("reduction_settings", [unreal.StaticMeshReductionSettings(1.0, 1.0), unreal.StaticMeshReductionSettings(0.1, 0.01)])
        n = sms.set_lods(m, o)
        m.set_editor_property("lod_for_collision", 1)
        eal.save_loaded_asset(m, only_if_is_dirty=False)
        e["collide"] = m.get_path_name()
        print("CAVE16 tunnel", k, "collision copy", dst, "| lods", n, "| triangles", sms.get_number_verts(m, 0), "->", sms.get_number_verts(m, 1), "vertices")
    if not CHECK: open(OUT, "w", encoding="utf-8").write(json.dumps(kit, indent=1) + "\n")


CAVES = "/Game/RandomDungeon/Maps/caves"
SORREL_SHARE = 0.15
GODRAY_MI = "/Game/Hyper/ResourcePack/Environments/GodRay/Materials/MI_GodRay_Animated"
WEIGHTS = {"small": 1.0, "medium": 0.8, "large": 0.45, "stairs": 0.0}
# (the kit's small tunnel is drawn by none: its walkable way is 2 to 3 m wide and closed up where it bent (868 cave16: she stuck on its
# walls in every small tunnel, never in a medium one))
TUNNEL_WEIGHTS = {"small": 0.0, "medium": 1.0, "large": 0.5}
FLOORS = {"small": KIT + "CombinedMeshes/Floor/SM_Cave_Floor_S", "medium": KIT + "CombinedMeshes/Floor/SM_Cave_Floor_M", "large": KIT + "CombinedMeshes/Floor/SM_Cave_Floor_L"}


def level():
    """the cave level's generator: bCave16 and the kit as measured (hyper16.json), then its start set built again (the castle's shell
    it saved goes; the cave's shell is never saved: play lays it)"""
    kit = json.load(open(OUT, encoding="utf-8"))
    for k, e in kit["rooms"].items():
        if "mask" not in e: raise RuntimeError("room " + k + " not measured: run 945 measure")
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(CAVES)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    def mesh(p): m = unreal.load_asset(p.split(".")[0]); assert m, p; return m
    def tf(at): return unreal.Transform(unreal.Vector(at[0], at[1], at[2]), unreal.Rotator(0.0, 0.0, at[3] if len(at) > 3 else 0.0), unreal.Vector(1, 1, 1))
    rooms = []
    for k in ("large", "medium", "small", "stairs"):
        e = kit["rooms"][k]
        r = unreal.RDCaveRoom16()
        r.set_editor_property("kind", k)
        r.set_editor_property("mesh", mesh(e["mesh"]))
        r.set_editor_property("roof", [mesh(x["mesh"]) for x in e["roof"]])
        # (Rotator(roll, pitch, yaw) in Python's order: the yaw last)
        r.set_editor_property("roof_at", [tf(x["at"]) for x in e["roof"]])
        r.set_editor_property("size", unreal.IntPoint(e["size"][0], e["size"][1]))
        r.set_editor_property("pivot", unreal.IntPoint(e["pivot"][0], e["pivot"][1]))
        r.set_editor_property("mask", e["mask"])
        r.set_editor_property("floor", e["floor"])
        r.set_editor_property("joints", [tf(c) for c in e["connections"]])
        g = e.get("godray")
        r.set_editor_property("god_ray", unreal.Vector(g[0], g[1], g[2]) if g else unreal.Vector(0, 0, 0))
        r.set_editor_property("weight", WEIGHTS[k])
        r.set_editor_property("lights", [tf(x) for x in e.get("lights", [])])
        rooms.append(r)
    tunnels = []
    for k in ("small", "medium", "large"):
        e = kit["tunnels"][k]
        t = unreal.RDCaveTunnel16()
        t.set_editor_property("kind", k)
        # (its collision copy where 945 collide made one: the same looks, its collision a tenth of the triangles)
        t.set_editor_property("mesh", mesh(e.get("collide") or e["mesh"]))
        t.set_editor_property("segment", e["segment"])
        t.set_editor_property("overlap", e["overlap"])
        # (the tunnel's own floor (measured, near its pivot) has gaps where the kit's example stands it on a ground of its own:
        # under it the kit's floor strip of its size, as wide as 90 % of the mesh (under the walls' feet), 10 cm lower; she walks the
        # measured half-width, 1.5 m at least)
        width = e["box"]["max"][1] - e["box"]["min"][1]
        t.set_editor_property("floor_mesh", mesh(FLOORS[k]))
        t.set_editor_property("floor_width", round(width * 0.9, 1))
        t.set_editor_property("half_walk", max(e["half_walk"], 150.0))
        t.set_editor_property("floor_z", e["floor_z"])
        t.set_editor_property("weight", TUNNEL_WEIGHTS[k])
        tunnels.append(t)
    gen.modify()
    gen.set_editor_property("cave16", True)
    gen.set_editor_property("cave_rooms16", rooms)
    gen.set_editor_property("cave_tunnels16", tunnels)
    gen.set_editor_property("cave_cap16", mesh(kit["cap"]["mesh"]))
    gen.set_editor_property("cave_rooms_per_set16", unreal.IntPoint(4, 7)); gen.set_editor_property("cave_loop_share16", LOOP_SHARE)
    # (phase 9: the kit's PCG dressing as measured; the sorrel hung from the roofs at 15 % of the kit's density (about 88 a metre of
    # tunnel at full: 12,000 instances a set))
    dr = []
    for where in ("tunnel", "room"):
        for e in kit.get("dressing", {}).get(where, []):
            d = unreal.RDCaveDress16()
            d.set_editor_property("mesh", mesh(e["mesh"]))
            d.set_editor_property("tunnel", where == "tunnel")
            roof = where == "tunnel" and e.get("roof_share", 0) > 0.5
            d.set_editor_property("roof", roof)
            d.set_editor_property("per_unit", round((e["per_m"] * (SORREL_SHARE if roof else 1.0)) if where == "tunnel" else e["per_tile"], 3))
            lat = e.get("lat", [0.0, 0.5]); d.set_editor_property("lateral", unreal.Vector2D(lat[0], lat[1]))
            d.set_editor_property("scale", unreal.Vector2D(e["scale"][0], e["scale"][1]))
            dr.append(d)
    gen.set_editor_property("cave_dress16", dr)
    t = kit.get("torch", {})
    if t:
        gen.set_editor_property("cave_torch_mesh16", mesh(t["mesh"]))
        # (the castle's torch flame: the kit's NS_2DGasIntro needs the NiagaraFluids plugin, which the project does not have (the
        # package's cook: "a dependency on package /NiagaraFluids/... which does not exist"))
        fx = gen.get_editor_property("effects").get(unreal.Name("TorchFire"))
        gen.set_editor_property("cave_torch_fire16", fx)
        gen.set_editor_property("cave_torch_fire_at16", unreal.Vector(*t["fire_at"]))
        gen.set_editor_property("cave_torch_light_at16", unreal.Vector(*t["light_at"]))
    g = kit.get("dressing", {}).get("godray")
    if g:
        gen.set_editor_property("cave_god_ray_mesh16", mesh(g["mesh"]))
        gen.set_editor_property("cave_god_ray_material16", unreal.load_asset(g.get("material", GODRAY_MI).split(".")[0]))
        gen.set_editor_property("cave_god_ray_turn16", unreal.Rotator(0.0, g["pitch"], g["yaw"]))
        gen.set_editor_property("cave_god_ray_scale16", unreal.Vector(*g.get("scale", [1.0, 1.0, 1.0])))          # (the example's, measured: PR #116's review)
    print("CAVE16 dressing", len(dr), "meshes | torch", bool(t), "| god ray", bool(g))
    # (the joints' yaw read back: a Rotator's argument order is easy to get wrong)
    j = gen.get_editor_property("cave_rooms16")[0].get_editor_property("joints")
    print("CAVE16 large room's openings' yaw", [round(x.rotation.rotator().yaw) for x in j], "| from the kit", [c[3] for c in kit["rooms"]["large"]["connections"]])
    if CHECK: print("CAVE16 check: not saved"); return
    gen.build_start_section()
    les.save_current_level()
    print("CAVE16 level", CAVES, "| rooms", [str(r.get_editor_property("kind")) for r in rooms], "| tunnels", [str(t.get_editor_property("kind")) for t in tunnels])
    del gen


PARTS = {"study": study, "measure": measure, "dressing": dressing, "collide": collide, "level": level, "items": items, "icons": icons}
for p in [a for a in ARGS if a in PARTS] or ["study"]:
    PARTS[p]()
gc.collect()
