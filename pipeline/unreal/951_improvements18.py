"""The list of 2026-11-27 (docs/improvements18.txt; the plan docs/improvements18_plan.md) on `brokenspire`:

    951_improvements18.py windows   phase 3: Closed Structures' windows boarded. Every window piece of the towns' kits (Town.<style>_WallWindow
                                    and _WallWindow2, Holy., Forge., Mage.) and every wild village house mesh is measured once: its triangles
                                    are laid flat on the wall's plane on a 2 cm grid and the enclosed holes found (an opening: a hole the
                                    piece's own faces surround, its bottom over the floor). The openings go to the generator
                                    (WindowHoles18: a piece's in its piece frame, out +X; a house mesh's in the mesh's own frame with the
                                    side's way out) and to SourceArt/list18/windows18.json, for RD/RDList18b.cpp to board them.

    951_improvements18.py stalls    phase 4: the squares' stands of twenty designs a style (SourceArt/list18/stalls18.json): each design's
                                    parts written as pieces (Stall18.<design>.<n>: a pack's mesh, a Blueprint (the Docks' stands as the town's
                                    own Town.Stall1-3), or the engine's cube in a Heaven material) in the stand's frame, each design laid once in
                                    the editor's world and measured (one wider than the 2.6 m square drawn in), the designs and their trades on
                                    the generator (StallDesigns18); every trade suited by three or more of each style (asserted)

Run on the editor with any level open: it opens brokenspire and saves it."""
import sys, gc, json, os, math
import unreal

EAL = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MAP = "/Game/RandomDungeon/Maps/brokenspire"
OUT = os.path.join(unreal.Paths.project_dir(), "SourceArt", "list18", "windows18.json")
REPORT = []
CELL = 2.0
BAND = 60.0


def tris_of(mesh, xf=None):
    """the mesh's triangles (LOD 0, every section) as lists of three (x, y, z), through xf if given"""
    out = []
    for s in range(mesh.get_num_sections(0)):
        r = unreal.ProceduralMeshLibrary.get_section_from_static_mesh(mesh, 0, s)
        vs, ts = r[0], r[1]
        P = [xf.transform_location(v) if xf else v for v in vs]
        P = [(p.x, p.y, p.z) for p in P]
        for i in range(0, len(ts) - 2, 3):
            out.append((P[ts[i]], P[ts[i + 1]], P[ts[i + 2]]))
    return out


def reveal(tris, u_of, v_of, x_of, h, ring=15.0):
    """the faces round a hole (within ring cm of its rectangle, not inside it): their range along the wall's normal, the opening's two
    faces (inner, outer)"""
    u0, u1, v0, v1 = h[:4]
    xs = []
    for t in tris:
        cu = sum(u_of(p) for p in t) / 3.0; cv = sum(v_of(p) for p in t) / 3.0
        if u0 - ring <= cu <= u1 + ring and v0 - ring <= cv <= v1 + ring and not (u0 + 2 < cu < u1 - 2 and v0 + 2 < cv < v1 - 2):
            xs += [x_of(p) for p in t]
    return (min(xs), max(xs)) if xs else None


def holes(tris, u_of, v_of, keep=None, min_area=900.0):
    """triangles laid flat by (u, v) on a CELL grid; the empty regions the faces surround (not touching the grid's edge), as
    (u0, u1, v0, v1, area cm2)"""
    tt = [t for t in tris if keep is None or keep(t)]
    if not tt: return []
    us = [u_of(p) for t in tt for p in t]; vs = [v_of(p) for t in tt for p in t]
    u0, v0 = min(us) - CELL, min(vs) - CELL
    nu, nv = int((max(us) - u0) / CELL) + 3, int((max(vs) - v0) / CELL) + 3
    full = bytearray(nu * nv)
    for t in tt:
        a = [((u_of(p) - u0) / CELL, (v_of(p) - v0) / CELL) for p in t]
        (ax, ay), (bx, by), (cx, cy) = a
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        i0, i1 = int(min(ax, bx, cx)), int(max(ax, bx, cx)) + 1
        j0, j1 = int(min(ay, by, cy)), int(max(ay, by, cy)) + 1
        if abs(den) < 1e-6:
            # (a face edge on to the plane: its line's cells)
            n = max(i1 - i0, j1 - j0, 1) * 2
            for (px, py), (qx, qy) in ((a[0], a[1]), (a[1], a[2]), (a[0], a[2])):
                for k in range(n + 1):
                    x, y = px + (qx - px) * k / n, py + (qy - py) * k / n
                    if 0 <= int(x) < nu and 0 <= int(y) < nv: full[int(x) * nv + int(y)] = 1
            continue
        for i in range(max(0, i0), min(nu, i1 + 1)):
            for j in range(max(0, j0), min(nv, j1 + 1)):
                x, y = i + 0.5, j + 0.5
                l1 = ((by - cy) * (x - cx) + (cx - bx) * (y - cy)) / den
                l2 = ((cy - ay) * (x - cx) + (ax - cx) * (y - cy)) / den
                if l1 >= -0.05 and l2 >= -0.05 and l1 + l2 <= 1.05: full[i * nv + j] = 1
    seen = bytearray(nu * nv); out = []
    for s in range(nu * nv):
        if full[s] or seen[s]: continue
        st = [s]; seen[s] = 1; cells = []; edge = False
        while st:
            c = st.pop(); cells.append(c); i, j = divmod(c, nv)
            if i == 0 or j == 0 or i == nu - 1 or j == nv - 1: edge = True
            for d in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                if 0 <= d[0] < nu and 0 <= d[1] < nv:
                    k = d[0] * nv + d[1]
                    if not full[k] and not seen[k]: seen[k] = 1; st.append(k)
        area = len(cells) * CELL * CELL
        if edge or area < min_area: continue
        ii = [c // nv for c in cells]; jj = [c % nv for c in cells]
        out.append((u0 + min(ii) * CELL, u0 + (max(ii) + 1) * CELL, v0 + min(jj) * CELL, v0 + (max(jj) + 1) * CELL, area))
    return out


def piece_openings(g):
    """the towns' window pieces, in the piece frame (out +X, along Y, up Z): their openings and the wall's faces"""
    res = {}
    for name, pc in g.get_editor_property("pieces").items():
        n = str(name)
        if "WallWindow" not in n or n.startswith(("Modern", "Heaven", "Lab")): continue
        m = pc.get_editor_property("mesh")
        if not m: continue
        tr = tris_of(m, pc.get_editor_property("adjust"))
        xs = [p[0] for t in tr for p in t]
        hs = holes(tr, lambda p: p[1], lambda p: p[2])
        zmin = min(p[2] for t in tr for p in t)
        hs = [h for h in hs if h[2] > zmin + 30.0 and h[1] - h[0] >= 20.0 and h[3] - h[2] >= 20.0]
        hl = []
        for h in sorted(hs, key=lambda h: -h[4]):
            rv = reveal(tr, lambda p: p[1], lambda p: p[2], lambda p: p[0], h) or (min(xs), max(xs))
            hl.append([round(v, 1) for v in h[:4]] + [round(rv[0], 1), round(rv[1], 1)])
        res[n] = {"mesh": m.get_path_name(), "x_in": round(min(xs), 1), "x_out": round(max(xs), 1), "holes": hl}
        REPORT.append(f"windows: {n}: {len(hs)} opening(s) {res[n]['holes'][:2]}, faces x {res[n]['x_in']}..{res[n]['x_out']}")
    return res


def house_openings(g):
    """the wild village houses (the places' table's house pieces, one pack mesh each): on each of the four sides, the faces in its outer
    60 cm band laid flat on the side's plane; the enclosed holes over 60 cm above the floor (doors reach the floor) are its windows"""
    res = {}
    meshes = set()
    # (the village houses' open copies that FitWildHouse furnishes (WildHouses, 916))
    for h in g.get_editor_property("wild_houses"):
        m = h.get_editor_property("mesh")
        if m: meshes.add(m)
    for m in meshes:
        tr = tris_of(m)
        P = [p for t in tr for p in t]
        bx = (min(p[0] for p in P), max(p[0] for p in P)); by = (min(p[1] for p in P), max(p[1] for p in P)); zmin = min(p[2] for p in P)
        out = []
        for side, (ax, sg) in {"+x": (0, 1), "-x": (0, -1), "+y": (1, 1), "-y": (1, -1)}.items():
            # (the mesh's outermost on that side: its dormers' and gables' openings go through it there. The ground storey's windows are
            # painted on its walls: no hole through any section of the mesh (a slice at the wall's face found only the plaster panels
            # between the beams, a storey high), so there is nothing there to see through or to board)
            edge = (bx if ax == 0 else by)[1 if sg > 0 else 0]
            keep = lambda t, ax=ax, edge=edge: all(abs(p[ax] - edge) < BAND for p in t)
            other = 1 - ax
            hs = holes(tr, lambda p, o=other: p[o], lambda p: p[2], keep)
            band = [t for t in tr if keep(t)]
            for h in hs:
                if h[2] > zmin + 60.0 and 30.0 <= h[1] - h[0] <= 300.0 and 30.0 <= h[3] - h[2] <= 300.0:
                    rv = reveal(band, lambda p, o=other: p[o], lambda p: p[2], lambda p, a=ax: p[a], h) or (edge - 10.0 * sg, edge)
                    out.append({"side": side, "face_a": round(rv[0], 1), "face_b": round(rv[1], 1), "u0": round(h[0], 1), "u1": round(h[1], 1), "z0": round(h[2], 1), "z1": round(h[3], 1)})
        res[m.get_path_name()] = out
        REPORT.append(f"windows: house {m.get_name()}: {len(out)} window(s)")
    return res


BOARD = "/Game/CastleofEternalMist/Meshes/Beam/SM_Plank_200_B"


def board(g):
    """the plank the boards are made of, turned to the board's frame: its thinnest way X, its longest Y, the other Z, centred"""
    m = unreal.load_asset(BOARD)
    assert m, "951: the plank is missing: " + BOARD
    bb = m.get_bounding_box()
    lo, hi = bb.min, bb.max
    corners = [unreal.Vector(x, y, z) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
    best = None
    for p in (0, 90):
        for yw in (0, 90):
            for r in (0, 90):
                rot = unreal.Rotator(roll=r, pitch=p, yaw=yw)
                xf = unreal.Transform(rotation=rot); pts = [xf.transform_location(c) for c in corners]
                ex = [max(getattr(q, a) for q in pts) - min(getattr(q, a) for q in pts) for a in "xyz"]
                if ex[0] <= ex[2] <= ex[1] and (best is None or ex[1] - ex[0] > best[1][1] - best[1][0]):
                    mid = unreal.Vector(*[(max(getattr(q, a) for q in pts) + min(getattr(q, a) for q in pts)) / 2.0 for a in "xyz"])
                    best = (rot, ex, mid)
    assert best, "951: the plank's axes not found"
    rot, ex, mid = best
    g.set_editor_property("board_mesh18", m)
    g.set_editor_property("board_adjust18", unreal.Transform(location=unreal.Vector(-mid.x, -mid.y, -mid.z), rotation=rot, scale=unreal.Vector(1, 1, 1)))
    g.set_editor_property("board_size18", unreal.Vector(*ex))
    REPORT.append(f"windows: the board {m.get_name()}: {ex[0]:.1f} thick, {ex[1]:.1f} long, {ex[2]:.1f} wide (turned {rot})")


def windows():
    les.load_level(MAP)
    unreal.SystemLibrary.execute_console_command(None, "obj gc")
    g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    board(g)
    data = {"pieces": piece_openings(g), "houses": house_openings(g)}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f: json.dump(data, f, indent=1)
    holes18 = []
    for n, d in data["pieces"].items():
        for h in d["holes"]:
            w = unreal.RDWindowHole18()
            w.set_editor_property("key", n); w.set_editor_property("side", 0)
            w.set_editor_property("box", unreal.Box(unreal.Vector(h[4], h[0], h[2]), unreal.Vector(h[5], h[1], h[3])))
            holes18.append(w)
    for mp, hs in data["houses"].items():
        for h in hs:
            w = unreal.RDWindowHole18()
            w.set_editor_property("key", mp); w.set_editor_property("side", {"+x": 1, "-x": 2, "+y": 3, "-y": 4}[h["side"]])
            w.set_editor_property("box", unreal.Box(unreal.Vector(h["face_a"], h["u0"], h["z0"]), unreal.Vector(h["face_b"], h["u1"], h["z1"])))
            holes18.append(w)
    g.set_editor_property("window_holes18", holes18)
    g.modify(); les.save_current_level()
    REPORT.append(f"windows: {len(holes18)} openings on brokenspire's generator, {OUT}")
    del g


STALLS = os.path.join(unreal.Paths.project_dir(), "SourceArt", "list18", "stalls18.json")
TRADES = ["weaponsmith", "armourer", "shieldmaker", "jeweller", "potions", "food", "scribe", "bookseller", "herbalist", "tinker", "chandler", "enchanter"]
CUBE = "/Engine/BasicShapes/Cube"
HV = "/Game/RandomDungeon/Heaven"


def hv_material(name):
    """a material instance of Heaven's kit by its name (heaven_kit.py's)"""
    for p in EAL.list_assets(HV, recursive=True, include_folder=False):
        if p.split("/")[-1].split(".")[0] == name: return unreal.load_asset(p)
    return None


BP_PIECES = {}          # (a Blueprint's path: the town's own piece of it, Town.Stall1-3: its Adjust as the town has always laid it)


def part_piece(p):
    """a design's part as a piece: a pack's mesh, a Blueprint (its generated class), or the engine's cube in a Heaven material, placed in the
    stand's frame by its Adjust"""
    pc = unreal.RDPiece()
    if "box" in p:
        cx, cy, cz, ex, ey, ez = p["box"]
        m = unreal.load_asset(CUBE); assert m, "951: the engine's cube"
        mat = hv_material(p["material"]); assert mat, "951: Heaven's material " + p["material"]
        # (the engine's cube is 100 cm about its middle)
        pc.set_editor_property("mesh", m); pc.set_editor_property("material", mat)
        pc.set_editor_property("adjust", unreal.Transform(location=unreal.Vector(cx, cy, cz), rotation=unreal.Rotator(0, 0, 0), scale=unreal.Vector(ex / 50.0, ey / 50.0, ez / 50.0)))
        pc.set_editor_property("size", unreal.Vector(2 * ex, 2 * ey, 2 * ez))
        return pc
    sc = p.get("scale", 1.0)
    sv = unreal.Vector(*sc) if isinstance(sc, list) else unreal.Vector(sc, sc, sc)
    xf = unreal.Transform(location=unreal.Vector(p["x"], p["y"], p["z"]), rotation=unreal.Rotator(roll=0, pitch=0, yaw=p.get("yaw", 0.0)), scale=sv)
    if p.get("actor") and p["mesh"].split(".")[0] in BP_PIECES:
        # (the Docks' market stands: the town's own pieces of them (882), not the draft's guess at their place (they measured 4 m across))
        src = BP_PIECES[p["mesh"].split(".")[0]]
        pc.set_editor_property("actor_class", src.get_editor_property("actor_class")); pc.set_editor_property("adjust", src.get_editor_property("adjust"))
        pc.set_editor_property("size", src.get_editor_property("size"))
        return pc
    if p.get("actor"):
        bp = unreal.load_asset(p["mesh"]); assert bp, "951: the Blueprint " + p["mesh"]
        pc.set_editor_property("actor_class", bp.generated_class())
    else:
        m = unreal.load_asset(p["mesh"]); assert m, "951: the mesh " + p["mesh"]
        pc.set_editor_property("mesh", m)
        bb = m.get_bounding_box(); pc.set_editor_property("size", bb.max - bb.min)
    pc.set_editor_property("adjust", xf)
    return pc


def measure_design(pieces, at):
    """the design laid in the editor's world at `at` (its parts as actors, as the town lays them): the union of their bounds in the stand's
    frame, and the actors (to picture, then take away)"""
    acts = []
    for pc in pieces:
        xf = pc.get_editor_property("adjust")
        loc = xf.translation + at
        ac = pc.get_editor_property("actor_class")
        if ac:
            a = eas.spawn_actor_from_class(ac, loc, xf.rotation.rotator())
            if a: a.set_actor_scale3d(xf.scale3d)
        else:
            a = eas.spawn_actor_from_class(unreal.StaticMeshActor, loc, xf.rotation.rotator())
            a.static_mesh_component.set_static_mesh(pc.get_editor_property("mesh")); a.set_actor_scale3d(xf.scale3d)
            mt = pc.get_editor_property("material")
            if mt:
                for i in range(a.static_mesh_component.get_num_materials()): a.static_mesh_component.set_material(i, mt)
        if a: acts.append(a)
    lo = [1e9] * 3; hi = [-1e9] * 3
    for a in acts:
        o, e = a.get_actor_bounds(False)
        for k, ax in enumerate("xyz"):
            lo[k] = min(lo[k], getattr(o, ax) - getattr(e, ax) - getattr(at, ax)); hi[k] = max(hi[k], getattr(o, ax) + getattr(e, ax) - getattr(at, ax))
    return lo, hi, acts


def stalls():
    les.load_level(MAP)
    unreal.SystemLibrary.execute_console_command(None, "obj gc")
    g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    data = json.load(open(STALLS, encoding="utf-8"))
    pieces = {str(k): v for k, v in g.get_editor_property("pieces").items() if not str(k).startswith("Stall18.")}
    BP_PIECES.clear()
    for k in ("Town.Stall1", "Town.Stall2", "Town.Stall3"):
        ac = pieces[k].get_editor_property("actor_class") if k in pieces else None
        if ac: BP_PIECES[ac.get_path_name().split(".")[0].removesuffix("_C")] = pieces[k]
    designs, report = [], []
    at = unreal.Vector(0, 0, 300000)
    for d in data["designs"]:
        pcs = [part_piece(p) for p in d["parts"]]
        lo, hi, acts = measure_design(pcs, at)
        for a in acts: eas.destroy_actor(a)
        # (a design wider than the stands' 2.6 m square is drawn in about its middle, parts and places alike)
        reach = max(abs(lo[0]), abs(hi[0]), abs(lo[1]), abs(hi[1]))
        k = min(1.0, 130.0 / reach) if reach > 132.0 else 1.0
        # (a design of the town's own stands (Town.Stall1-3) keeps their size: the squares have always made room for them)
        if all(p.get("actor") and p["mesh"].split(".")[0] in BP_PIECES for p in d["parts"]): k = 1.0
        names = []
        for n, pc in enumerate(pcs):
            if k < 1.0:
                xf = pc.get_editor_property("adjust")
                pc.set_editor_property("adjust", unreal.Transform(location=xf.translation * k, rotation=xf.rotation.rotator(), scale=xf.scale3d * k))
            nm = f"Stall18.{d['id']}.{n}"
            pieces[nm] = pc; names.append(unreal.Name(nm))
        ds = unreal.RDStallDesign18()
        ds.set_editor_property("id", d["id"]); ds.set_editor_property("modern", d["style"] == "modern")
        ds.set_editor_property("parts", names)
        ds.set_editor_property("trades", [] if "any" in d["trades"] else [TRADES.index(t) for t in d["trades"]])
        designs.append(ds)
        report.append({"id": d["id"], "measured": [round(v) for v in lo + hi], "scaled": round(k, 3)})
        REPORT.append(f"stalls: {d['id']} {d['name']}: {len(pcs)} parts, x {lo[0]:.0f}..{hi[0]:.0f} y {lo[1]:.0f}..{hi[1]:.0f} z {lo[2]:.0f}..{hi[2]:.0f}" + (f", drawn in to {k:.3f}" if k < 1.0 else ""))
    # (every trade has a design of each style that suits it, and the twelve stands of a square can take twelve different ones)
    for style in (False, True):
        sd = [d for d in designs if d.get_editor_property("modern") == style]
        for t in range(12):
            n = sum(1 for d in sd if not d.get_editor_property("trades") or t in d.get_editor_property("trades"))
            assert n >= 3, f"951: the {'modern' if style else 'medieval'} trade {TRADES[t]} has {n} designs"
    g.set_editor_property("pieces", pieces)
    g.set_editor_property("stall_designs18", designs)
    g.modify(); les.save_current_level()
    with open(os.path.join(os.path.dirname(STALLS), "stalls18_measured.json"), "w", encoding="utf-8") as f: json.dump(report, f, indent=1)
    REPORT.append(f"stalls: {len(designs)} designs, {sum(len(d.get_editor_property('parts')) for d in designs)} parts on brokenspire's generator")
    del g


PARTS = {"windows": windows, "stalls": stalls}
for part in (sys.argv[1] if len(sys.argv) > 1 else "").split(","):
    if part: PARTS[part]()
for r in REPORT: print("951", r)
gc.collect()
