"""random_dungeonmagic_level5's weapons table (SourceArt/random_dungeon_magic5/weapons_table.json), step 1: the meshes.
- the two that are skeletal meshes (Ursag's horn blade, the dwarf crossbow) get a static copy: exported as FBX
  (SourceArt/random_dungeon_magic5/weapons_src, ignored) and imported back as /Game/RandomDungeon/Magic5/Weapons/SM_W5_<key>
  with the skeletal mesh's materials, slot by slot
- each weapon (and the templates the heroes already hold: the arming sword SM_Sword_1, the dagger SM_Dagger, the crossbow
  SM_Crossbow) measured on its own vertices, in its own space (cm), with no help from its name:
  blades (swords, knives): the long axis (the vertices' principal axis); along it, slice by slice, how wide and how
    round the mesh is; the handle is the rounder end (5 to 30 % of the length), the guard where it gets wide or flat;
    the hand closes HAND_FROM_GUARD cm from the guard toward the pommel (half the handle when it is shorter). The frame:
    its origin there on the handle's middle line, X the blade's way, Y the way of its edge (the blade's widest way across;
    toward the thinner side when one side is thinner: the edge of a one-edged blade), Z square to both
  bows: the long axis (the limbs); the grip is the middle; the way the arrow flies is from the line between the tips
    (where the string runs) to the farthest point of the middle (the bow's back)
  crossbows: the axis along which the prod (the widest part across) sits at one end is the length, its widest way across
    the prod's span; the front is the prod's end, up the side the prod is on (the stock and the trigger hang below the
    rail); the hand, the muzzle and the bolt lying ready are placed as on the template crossbow (SM_Crossbow: the hand
    31 cm behind its front at the rail's height less 5.1 cm, the muzzle at its front on the rail)
Writes SourceArt/random_dungeon_magic5/weapon_frames.json (per weapon: kind, frame, sizes, what was measured).
Args: none"""
import json, math, os, unreal
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
T = json.load(open(os.path.join(SA, "random_dungeon_magic5", "weapons_table.json"), encoding="utf-8"))
OBJ = {o["id"]: o for o in json.load(open(os.path.join(SA, "object_gallery", "objects.json"), encoding="utf-8"))["objects"]}
SRC = os.path.join(SA, "random_dungeon_magic5", "weapons_src"); os.makedirs(SRC, exist_ok=True)
OUT = os.path.join(SA, "random_dungeon_magic5", "weapon_frames.json")
D = "/Game/RandomDungeon/Magic5/Weapons"
MW = "/Game/Medieval_Weapons/Meshes/VOL2"
TEMPLATES = {"template_sword": (f"{MW}/SM_Sword_1", "blade"), "template_dagger": (f"{MW}/SM_Dagger", "blade"), "template_crossbow": (f"{MW}/SM_Crossbow", "crossbow")}
HAND_FROM_GUARD = 4.5
eal = unreal.EditorAssetLibrary
KIND = lambda typ: "bow" if typ == "ranged" else "blade"


def key(name): return "".join(c for c in name.title() if c.isalnum())


# ---- small linear algebra (the editor's Python has no numpy)
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a):
    l = math.sqrt(dot(a, a)) or 1.0
    return (a[0] / l, a[1] / l, a[2] / l)
def mean(P): n = len(P); return (sum(p[0] for p in P) / n, sum(p[1] for p in P) / n, sum(p[2] for p in P) / n)


def pca(P):
    """centre, and the principal axes, longest first (Jacobi on the 3 x 3 covariance)"""
    c = mean(P)
    A = [[0.0] * 3 for _ in range(3)]
    for p in P:
        d = sub(p, c)
        for i in range(3):
            for j in range(3): A[i][j] += d[i] * d[j]
    Vm = [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]
    for _ in range(60):
        i, j = max(((0, 1), (0, 2), (1, 2)), key=lambda ij: abs(A[ij[0]][ij[1]]))
        if abs(A[i][j]) < 1e-9: break
        th = 0.5 * math.atan2(2 * A[i][j], A[j][j] - A[i][i]); cs, sn = math.cos(th), math.sin(th)
        for k in range(3):
            aki, akj = A[k][i], A[k][j]; A[k][i] = cs * aki - sn * akj; A[k][j] = sn * aki + cs * akj
        for k in range(3):
            aik, ajk = A[i][k], A[j][k]; A[i][k] = cs * aik - sn * ajk; A[j][k] = sn * aik + cs * ajk
        for k in range(3):
            vki, vkj = Vm[k][i], Vm[k][j]; Vm[k][i] = cs * vki - sn * vkj; Vm[k][j] = sn * vki + cs * vkj
    ev = [A[i][i] for i in range(3)]
    order = sorted(range(3), key=lambda i: -ev[i])
    axes = [norm((Vm[0][i], Vm[1][i], Vm[2][i])) for i in order]
    if dot(cross(axes[0], axes[1]), axes[2]) < 0: axes[2] = mul(axes[2], -1.0)
    return c, axes


def slices(P, c, a, b, z, step=1.0):
    """along a: per slice of `step` cm the points' (u, w) across (on b, z)"""
    t = [dot(sub(p, c), a) for p in P]; t0, t1 = min(t), max(t)
    n = max(2, int(math.ceil((t1 - t0) / step)))
    S = [[] for _ in range(n)]
    for p, tt in zip(P, t):
        S[min(n - 1, int((tt - t0) / step))].append((dot(sub(p, c), b), dot(sub(p, c), z)))
    return t0, t1, S


def blade_frame(P):
    c, (a, b, z) = pca(P)
    t0, t1, S = slices(P, c, a, b, z)
    n = len(S); L = t1 - t0
    # (a slice with no vertex in it is unknown: a long face runs through it; it neither starts nor ends anything)
    W = []
    for s in S:
        if len(s) >= 2:
            us, ws = [q[0] for q in s], [q[1] for q in s]
            W.append((max(us) - min(us), max(ws) - min(ws), (max(us) + min(us)) * 0.5, (max(ws) + min(ws)) * 0.5))
        else: W.append(None)
    size = [max(w[0], w[1]) if w else None for w in W]; rnd = [min(w[0], w[1]) / max(max(w[0], w[1]), 1e-3) if w else None for w in W]
    known = lambda ii: [i for i in ii if size[i] is not None]
    # which end is the handle: the blade's end narrows to its point (the widest thing in its last 3 cm is less than 0.6 of
    # the other end's: a pommel, a butt cap); when they are alike, the rounder end (3 to 15 % of the length) is the handle
    tip = lambda ii: max([size[i] for i in known(ii)] or [0.0])
    e0, e1 = tip(range(0, 3)), tip(range(n - 3, n))
    def roundness(from_min):
        ii = known([i if from_min else n - 1 - i for i in range(int(0.03 * n), max(int(0.15 * n), int(0.03 * n) + 2))])
        return sum(rnd[i] for i in ii) / max(len(ii), 1)
    r0, r1 = roundness(True), roundness(False)
    at_min = e1 < 0.6 * e0 if (e1 < 0.6 * e0 or e0 < 0.6 * e1) else r0 >= r1
    order = list(range(n)) if at_min else list(range(n - 1, -1, -1))
    dirn = 1.0 if at_min else -1.0                         # (from the handle toward the blade, along a)
    # the handle's size: the narrower quarter of the hilt's half of the weapon
    half = sorted(size[i] for i in known(order[:n // 2])); hsize = half[len(half) // 4]
    # the guard: once 5 cm of handle-like slices (no wider than 1.8 x the handle) have gone by, the first slice 3/4 as wide
    # as the widest thing in the weapon's first 55 % (a katana's tsuba and a sabre's crossbar are a centimetre thick; a
    # pommel or a knob at the end comes before the handle, and is narrower than the guard; a guard's ramp no longer
    # counts against the handle once it has been seen). A knife with nothing much wider than its handle (the widest
    # less than 1.8 x it): the first flat slice after the handle (the blade's root)
    hilt = known(order[:int(0.55 * n)]); gmax = max(size[i] for i in hilt)
    wide = max(0.75 * gmax, 1.4 * hsize) if gmax >= 1.8 * hsize else 1.4 * hsize      # (a knife: its bolster, 1.4 x the handle)
    def find(test):
        run = 0; seen = False
        for k in range(n):
            i = order[k]
            if size[i] is None: continue
            if seen and test(i): return k
            run = run + 1 if size[i] <= 1.8 * hsize else (run if seen else 0)
            seen = seen or run >= 5
        return None
    guard = find(lambda i: size[i] >= wide)
    if guard is None: guard = find(lambda i: rnd[i] < 0.3 and size[i] > 1.1 * hsize)    # (no wider part: the flat blade's root)
    if guard is None: guard = int(0.3 * n)
    if os.environ.get("W5_DEBUG"):
        print("W5PROF hsize %.1f gmax %.1f guard %d |" % (hsize, gmax, guard), " ".join("-" if size[order[k]] is None else "%.0f" % size[order[k]] for k in range(min(n, 70))))
    grip_k = max(1, guard - min(HAND_FROM_GUARD, guard * 0.5))
    tg = t0 + order[int(round(grip_k))] + 0.5
    near = [W[order[k]] for k in range(max(0, int(grip_k) - 3), min(n, int(grip_k) + 4)) if W[order[k]]]
    near = near or [W[i] for i in sorted(known(range(n)), key=lambda i: abs(i - order[int(round(grip_k))]))[:3]]
    uc, wc = sum(w[2] for w in near) / len(near), sum(w[3] for w in near) / len(near)
    origin = add(add(add(c, mul(a, tg)), mul(b, uc)), mul(z, wc))
    X = mul(a, dirn)
    # the edge: the blade's widest way across (each slice centred: a curved blade bends), toward its thinner side
    blade = [order[k] for k in range(guard + 2, n - 2) if W[order[k]]]
    cu = cw = cuw = 0.0; pts = []
    for i in blade:
        for (u, w) in S[i]:
            du, dw = u - W[i][2], w - W[i][3]; pts.append((i, du, dw)); cu += du * du; cw += dw * dw; cuw += du * dw
    ang = 0.5 * math.atan2(2 * cuw, cu - cw) if pts else 0.0
    e = (math.cos(ang), math.sin(ang))
    Y0 = norm(add(mul(b, e[0]), mul(z, e[1]))); Z0 = norm(cross(X, Y0)); Y0 = norm(cross(Z0, X))
    thick = {1: [], -1: []}
    for i in blade:
        q = [(du * e[0] + dw * e[1], -du * e[1] + dw * e[0]) for (ii, du, dw) in pts if ii == i]
        if len(q) < 6: continue
        ys = [y for y, _ in q]; lo, hi = min(ys), max(ys); band = 0.18 * (hi - lo)
        for sgn, keep in ((1, lambda y: y > hi - band), (-1, lambda y: y < lo + band)):
            zz = [zv for y, zv in q if keep(y)]
            if len(zz) >= 2: thick[sgn].append(max(zz) - min(zz))
    tp = sum(thick[1]) / max(len(thick[1]), 1); tm = sum(thick[-1]) / max(len(thick[-1]), 1)
    # (Y0 in mesh axes: ang measured from b; flip it when the -Y side is the thin one)
    yb = dot(Y0, add(mul(b, e[0]), mul(z, e[1])))
    if yb < 0: tp, tm = tm, tp
    single = min(tp, tm) < 0.8 * max(tp, tm)
    if single and tm < tp: Y0 = mul(Y0, -1.0)
    Z = norm(cross(X, Y0))
    widths = [W[i][0] if abs(dot(Y0, b)) > abs(dot(Y0, z)) else W[i][1] for i in blade] or [0.0]
    return {"kind": "blade", "origin": origin, "x": X, "y": Y0, "z": Z, "length": L, "handle": guard * 1.0, "grip_from_guard": guard - grip_k,
            "blade_len": L - guard, "blade_width": max(widths), "single_edged": single, "edge_thickness": [round(tp, 2), round(tm, 2)],
            "ends": [round(e0, 1), round(e1, 1), round(r0, 2), round(r1, 2)], "handle_size": round(hsize, 2)}


def bow_frame(P):
    c, (a, b, z) = pca(P)
    t = [dot(sub(p, c), a) for p in P]; t0, t1 = min(t), max(t); L = t1 - t0; tm = (t0 + t1) * 0.5
    tips = [p for p, tt in zip(P, t) if tt > t1 - 0.04 * L or tt < t0 + 0.04 * L]
    up_tip = mean([p for p, tt in zip(P, t) if tt > t1 - 0.04 * L]); lo_tip = mean([p for p, tt in zip(P, t) if tt < t0 + 0.04 * L])
    mid_line = mul(add(up_tip, lo_tip), 0.5)
    mid = [p for p, tt in zip(P, t) if abs(tt - tm) < 0.06 * L]
    perp = lambda p: (lambda d: sub(d, mul(a, dot(d, a))))(sub(p, mid_line))
    far = max(mid, key=lambda p: dot(perp(p), perp(p)))
    front = norm(perp(far))
    grip = mean([p for p in mid if math.sqrt(dot(sub(p, far), sub(p, far))) < 6.0])
    X = a; Y = norm(sub(front, mul(X, dot(front, X)))); Z = norm(cross(X, Y))
    return {"kind": "bow", "origin": grip, "x": X, "y": Y, "z": Z, "length": L, "depth": math.sqrt(dot(perp(far), perp(far)))}


def crossbow_frame(P, front, up):
    """a crossbow's frame from its front and up ways (mesh axes). They are given, not found: the template's prod sweeps
    back (its widest part is half way down the stock, its spike in front), the dwarf's has a stirrup before its prod;
    looked at in the gallery's pictures and the meshes' slices"""
    c = mean(P); f = norm(front); h = norm(up)
    g = norm(cross(h, f))                                    # (f, g, h right-handed: x front, y left, z up)
    tf = [dot(sub(p, c), f) for p in P]; t0, t1 = min(tf), max(tf); L = t1 - t0
    def near(tt, width=4.0, lateral=None):
        while True:          # (a gap in the mesh there: a wider slice)
            s = [p for p, q in zip(P, tf) if abs(q - tt) < width and (lateral is None or abs(dot(sub(p, c), g)) < lateral)]
            if s or width > L: return s
            width *= 1.6
    def top_at(tt):
        s = near(tt, lateral=3.0) or near(tt)
        return max(dot(sub(p, c), h) for p in s)
    def centre_at(tt):
        gs = [dot(sub(p, c), g) for p in near(tt)]
        return (max(gs) + min(gs)) * 0.5
    return {"kind": "crossbow", "c": c, "f": f, "g": g, "h": h, "front_t": t1, "back_t": t0, "length": L, "top_at": top_at, "centre_at": centre_at}


def place_xbow(fr, marks):
    """the crossbow's frame (origin at the hand), the muzzle and the ready bolt's tip in mesh space. marks: the hand's
    distance from the butt and below the rail there; the muzzle's and the ready bolt tip's from the front end (cm)"""
    c, f, g, h = fr["c"], fr["f"], fr["g"], fr["h"]
    pt = lambda tt, gg, hh: add(add(add(c, mul(f, tt)), mul(g, gg)), mul(h, hh))
    from_butt, rail_below, mz_back, ld_back = marks
    th = fr["back_t"] + from_butt; tz = fr["front_t"] - mz_back; tl = fr["front_t"] - ld_back
    hand = pt(th, fr["centre_at"](th), fr["top_at"](th) - rail_below)
    muzzle = pt(tz, fr["centre_at"](tz), fr["top_at"](tz)); loaded = pt(tl, fr["centre_at"](tl), fr["top_at"](tl))
    return {"kind": "crossbow", "origin": hand, "x": f, "y": g, "z": h, "length": fr["length"], "muzzle": muzzle, "loaded_tip": loaded}


def verts(m):
    vs = []
    for sec in range(m.get_num_sections(0)): vs += [(v.x, v.y, v.z) for v in unreal.ProceduralMeshLibrary.get_section_from_static_mesh(m, 0, sec)[0]]
    return vs


def static_copy(sk_path, k):
    """an SK weapon as a static mesh (FBX out, Interchange back in as static), its materials slot by slot"""
    dst = f"{D}/SM_W5_{k}"
    sk = unreal.load_asset(sk_path); assert sk, sk_path
    f = os.path.join(SRC, k + ".fbx")
    t = unreal.AssetExportTask(); t.object = sk; t.filename = f; t.automated = True; t.prompt = False; t.replace_identical = True
    o = unreal.FbxExportOption(); o.level_of_detail = False; o.collision = False; o.export_morph_targets = False; o.vertex_color = False; o.ascii = False
    t.options = o
    assert unreal.Exporter.run_asset_export_task(t), "export failed: " + sk_path
    pipe = unreal.InterchangeGenericAssetsPipeline()
    mp = pipe.mesh_pipeline
    for n, v in (("import_skeletal_meshes", False), ("import_static_meshes", True), ("combine_static_meshes", True)):
        try: mp.set_editor_property(n, v)
        except Exception as e: print("  (skip)", n, str(e)[:60])
    pipe.common_meshes_properties.set_editor_property("force_all_mesh_as_type", unreal.InterchangeForceMeshType.IFMT_STATIC_MESH)
    pipe.animation_pipeline.set_editor_property("import_animations", False); pipe.material_pipeline.set_editor_property("import_materials", False)
    tmp = f"{D}/_import_{k}"
    prm = unreal.ImportAssetParameters(); prm.is_automated = True; prm.replace_existing = True
    prm.override_pipelines.append(unreal.SoftObjectPath(pipe.get_path_name()))
    try: unreal.InterchangeManager.get_interchange_manager_scripted().import_asset(tmp, unreal.InterchangeManager.create_source_data(f), prm)
    except RuntimeError as e: print("W5MESH import (non-fatal)", str(e)[:160])
    sm = next((unreal.load_asset(a.split(".")[0]) for a in eal.list_assets(tmp, recursive=True) if isinstance(unreal.load_asset(a.split(".")[0]), unreal.StaticMesh)), None)
    assert sm, "nothing imported for " + k
    if eal.does_asset_exist(dst): eal.delete_asset(dst)
    eal.rename_asset(sm.get_path_name().split(".")[0], dst); sm = unreal.load_asset(dst)
    for a in eal.list_assets(tmp, recursive=True): eal.delete_asset(a.split(".")[0])
    eal.delete_directory(tmp)
    mats = [s.get_editor_property("material_interface") for s in sk.get_editor_property("materials")]
    for i in range(sm.get_num_sections(0)):
        if mats: sm.set_material(i, mats[min(i, len(mats) - 1)])
    eal.save_loaded_asset(sm, only_if_is_dirty=False)
    return dst


res = {"_note": "854's measurements: each weapon's frame in its own mesh space (cm): origin where the hand closes on it (a "
                "crossbow: the right hand), x the blade's / bow's limbs' / crossbow's front way, y the edge's / the arrow's way / "
                "the crossbow's left, z square to them (a crossbow: up, its rail); a crossbow's muzzle and ready bolt's tip",
       "weapons": {}}
# the crossbows' ways (mesh axes: front, up). The template's marks (822: its hand at (31, 0, 0.5), its muzzle at
# (-32, 0, 5.6), the ready bolt's tip at (-30, 0, 5.6)) measured from its butt and its front; the dwarf's hand as far
# from its butt, its muzzle at the front of its rail (its prod's middle, 15 cm behind the stirrup)
XBOW_AXES = {"template_crossbow": ((-1, 0, 0), (0, 0, 1)), "Crossbow": ((-1, 0, 0), (0, 0, 1)), "DwarfCrossbow": ((0, 1, 0), (0, 0, 1))}
xt = crossbow_frame(verts(unreal.load_asset(TEMPLATES["template_crossbow"][0])), *XBOW_AXES["template_crossbow"])
c, f, h = xt["c"], xt["f"], xt["h"]
hand_m, muzzle_m, loaded_m = (31.0, 0.0, 0.5), (-32.0, 0.0, 5.6), (-30.0, 0.0, 5.6)       # (822's, mesh space)
tt = lambda p: dot(sub(p, c), f)
marks = (tt(hand_m) - xt["back_t"], xt["top_at"](tt(hand_m)) - dot(sub(hand_m, c), h), xt["front_t"] - tt(muzzle_m), xt["front_t"] - tt(loaded_m))
XBOW_MARKS = {"template_crossbow": marks, "Crossbow": marks, "DwarfCrossbow": (marks[0], marks[1], 15.0, 17.0)}
print("W5MESH template crossbow: the hand %.1f cm from the butt, %.1f below the rail; the muzzle %.1f, the bolt's tip %.1f behind the front" % marks)
items = [(k_, p_, kind_) for k_, (p_, kind_) in TEMPLATES.items()]
for w in T["weapons"]:
    o = OBJ[w["gallery"]]; mesh = o["meshes"][0].split(".")[0]; k = key(w["name"])
    if "/SK_" in mesh: mesh = static_copy(mesh, k)
    kind = "crossbow" if "crossbow" in w["name"].lower() else KIND(w["type"])
    items.append((k, mesh, kind))
for k, mesh, kind in items:
    m = unreal.load_asset(mesh); assert m, mesh
    P = verts(m)
    if kind == "blade": fr = blade_frame(P)
    elif kind == "bow": fr = bow_frame(P)
    else:
        fr = place_xbow(crossbow_frame(P, *XBOW_AXES[k]), XBOW_MARKS[k])
        if k in ("template_crossbow", "Crossbow"): fr["muzzle"], fr["loaded_tip"] = muzzle_m, loaded_m      # (822's own: its rail is under the spike's top)
    out = {"mesh": mesh, "verts": len(P)}
    for kk, v in fr.items():
        out[kk] = [round(x, 3) for x in v] if isinstance(v, tuple) else (round(v, 3) if isinstance(v, float) else v)
    res["weapons"][k] = out
    extra = f"single-edged {fr['single_edged']} (edges {fr['edge_thickness']}), handle {fr['handle']:.0f} cm, blade {fr['blade_len']:.0f} x {fr['blade_width']:.1f}" if kind == "blade" else \
            (f"depth {fr['depth']:.1f}" if kind == "bow" else f"muzzle {[round(v, 1) for v in fr['muzzle']]}")
    print(f"W5MESH {k:20s} {kind:8s} {len(P):6d} verts, {fr['length']:.0f} cm | origin {[round(v, 1) for v in fr['origin']]} x {[round(v, 2) for v in fr['x']]} y {[round(v, 2) for v in fr['y']]} | {extra}")
json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1)
print("W5MESH wrote", OUT, len(res["weapons"]), "weapons")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
