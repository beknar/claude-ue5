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
import sys, os, json, gc, unreal

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
    gen.set_editor_property("cave_rooms_per_set16", unreal.IntPoint(4, 7))
    # (the joints' yaw read back: a Rotator's argument order is easy to get wrong)
    j = gen.get_editor_property("cave_rooms16")[0].get_editor_property("joints")
    print("CAVE16 large room's openings' yaw", [round(x.rotation.rotator().yaw) for x in j], "| from the kit", [c[3] for c in kit["rooms"]["large"]["connections"]])
    if CHECK: print("CAVE16 check: not saved"); return
    gen.build_start_section()
    les.save_current_level()
    print("CAVE16 level", CAVES, "| rooms", [str(r.get_editor_property("kind")) for r in rooms], "| tunnels", [str(t.get_editor_property("kind")) for t in tunnels])
    del gen


PARTS = {"study": study, "measure": measure, "collide": collide, "level": level}
for p in [a for a in ARGS if a in PARTS] or ["study"]:
    PARTS[p]()
gc.collect()
