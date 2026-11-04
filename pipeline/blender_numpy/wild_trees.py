"""The wilderness's aspen, birch and acacia (the user's spec of 2026-11-03 names temperate aspen forests and savannahs; no pack
in the project, the asset library or the Fab vault has an aspen, a birch or an acacia): built here from shapes, two of each.

  Trunk     a tapered tube along a slightly wandering line (8 sides), its bark's UVs a repeat a metre up and once round.
  Branches  tapered tubes from the trunk's upper part (aspen: short, steep, a narrow crown; birch: longer, arching out and
            down at their ends; acacia: the trunk forks low into three or four limbs that spread to a flat top).
  Leaves    clusters of crossed cards (three upright at 60 degrees and one flat) on the branches' outer parts, mapped whole
            to a painted leaf-spray picture with transparency (the acacia: wide flat cards over its crown).
  Pictures  painted by this script (numpy): the bark (aspen: pale green-white with dark eyes; birch: white with black dashes;
            acacia: dark brown, fissured) and the leaves (aspen: rounded, yellow-green; birch: small, green; acacia: tiny,
            olive), 512 px, written beside the FBX.
Writes into out_dir: SM_Wild_<Kind>_<A|B>.fbx (two material slots: Bark, Leaves), T_Wild_<Kind>Bark.png,
T_Wild_<Kind>Leaves.png, wild_trees.json (each tree's height, triangles, clusters). Z up, metres, origin at the trunk's foot.
887_wilderness.py trees <out_dir> imports them.
Blender: -b -P wild_trees.py -- out_dir"""
import bpy, bmesh, math, random, sys, os, json
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0] if argv else "wild_trees")
os.makedirs(OUT, exist_ok=True)

SPECIES = {
    "Aspen":  {"h": (15.0, 18.0), "r0": 0.17, "fork": None, "branches": (11, 15), "from": 0.42, "len": (1.3, 3.2), "up": (38, 62), "droop": 0.0, "clusters": (2, 3), "csize": (1.5, 2.2), "flat": False},
    "Birch":  {"h": (13.0, 16.0), "r0": 0.14, "fork": None, "branches": (13, 17), "from": 0.38, "len": (1.8, 3.8), "up": (25, 45), "droop": 0.55, "clusters": (3, 4), "csize": (1.2, 1.8), "flat": False},
    "Acacia": {"h": (7.0, 8.5), "r0": 0.24, "fork": (2.4, 3.4), "branches": (3, 4), "from": 0.0, "len": (3.5, 4.8), "up": (32, 46), "droop": 0.0, "clusters": (0, 0), "csize": (2.6, 3.4), "flat": True},
}


# ------------------------------------------------------------------------------------------------ pictures
def save_png(name, rgba):
    h, w, _ = rgba.shape
    img = bpy.data.images.new(name, width=w, height=h, alpha=True)
    img.pixels = np.flipud(rgba).astype(np.float32).ravel()
    img.filepath_raw = os.path.join(OUT, name + ".png"); img.file_format = "PNG"; img.save()
    return img.filepath_raw


def noise(n, seed, octaves=((8, 1.0), (16, 0.5), (32, 0.25), (64, 0.12))):
    rng = np.random.default_rng(seed); acc = np.zeros((n, n))
    for o, a in octaves:
        g = rng.random((o + 1, o + 1)); ys = np.linspace(0, o, n, endpoint=False); i0 = ys.astype(int); f = ys - i0; f = f * f * (3 - 2 * f)
        row = g[i0][:, i0] * (1 - f)[None, :] + g[i0][:, i0 + 1] * f[None, :]
        row2 = g[i0 + 1][:, i0] * (1 - f)[None, :] + g[i0 + 1][:, i0 + 1] * f[None, :]
        acc += a * (row * (1 - f)[:, None] + row2 * f[:, None])
    acc -= acc.min(); return acc / max(acc.max(), 1e-6)


def bark(kind, n=512):
    nz = noise(n, hash(kind) % 1000)
    rng = np.random.default_rng(7 + len(kind))
    yy, xx = np.mgrid[0:n, 0:n] / n
    if kind == "Acacia":
        fiss = noise(n, 3, ((4, 1.0), (64, 0.6), (128, 0.3)))
        stretch = np.abs(np.sin(xx * 38 + fiss * 6)) ** 0.4
        base = np.array([0.30, 0.22, 0.15]) * (0.65 + 0.45 * stretch[..., None] * (0.8 + 0.4 * nz[..., None]))
    else:
        light = np.array([0.80, 0.82, 0.74]) if kind == "Aspen" else np.array([0.90, 0.89, 0.86])
        base = light * (0.88 + 0.16 * nz[..., None])
        for _ in range(70 if kind == "Birch" else 26):
            cx, cy = rng.random(), rng.random()
            if kind == "Birch":   # black dashes across the trunk
                w, h = rng.uniform(0.04, 0.16), rng.uniform(0.006, 0.02)
                m = (np.abs(((xx - cx + 0.5) % 1) - 0.5) < w) & (np.abs(yy - cy) < h)
            else:                 # the aspen's dark eyes (diamonds)
                w, h = rng.uniform(0.03, 0.07), rng.uniform(0.02, 0.05)
                m = (np.abs(((xx - cx + 0.5) % 1) - 0.5) / w + np.abs(yy - cy) / h) < 1.0
            base[m] = base[m] * 0.18 + np.array([0.08, 0.07, 0.06]) * 0.82
    rgba = np.concatenate([np.clip(base, 0, 1), np.ones((n, n, 1))], -1)
    return save_png(f"T_Wild_{kind}Bark", rgba)


def leaves(kind, n=512):
    rng = np.random.default_rng(31 + len(kind))
    rgba = np.zeros((n, n, 4))
    yy, xx = np.mgrid[0:n, 0:n] / n
    pal = {"Aspen": [(0.55, 0.62, 0.18), (0.70, 0.66, 0.20), (0.42, 0.52, 0.16)], "Birch": [(0.30, 0.45, 0.14), (0.38, 0.52, 0.16), (0.26, 0.38, 0.12)],
           "Acacia": [(0.30, 0.36, 0.14), (0.36, 0.40, 0.16), (0.24, 0.30, 0.12)]}[kind]
    count, size = {"Aspen": (150, 0.055), "Birch": (230, 0.04), "Acacia": (520, 0.022)}[kind]
    # twigs from the middle of the picture's foot out to the leaves
    for _ in range(count):
        a = rng.uniform(0, 2 * math.pi); d = math.sqrt(rng.random()) * 0.46
        cx, cy = 0.5 + math.cos(a) * d, 0.5 + math.sin(a) * d
        rot = rng.uniform(0, math.pi); s = size * rng.uniform(0.7, 1.3)
        dx, dy = xx - cx, yy - cy
        u = dx * math.cos(rot) + dy * math.sin(rot); v = -dx * math.sin(rot) + dy * math.cos(rot)
        m = (u / s) ** 2 + (v / (s * 0.62)) ** 2 < 1.0
        c = np.array(pal[rng.integers(len(pal))]) * rng.uniform(0.8, 1.15) * (0.85 + 0.15 * (u[m] / s)[:, None] if False else 1.0)
        rgba[m, :3] = c; rgba[m, 3] = 1.0
    # a faint dark line down the middle of each leaf is too fine at this size: a little shade toward the cluster's middle instead
    r = np.sqrt((xx - 0.5) ** 2 + (yy - 0.5) ** 2)
    rgba[..., :3] *= (0.72 + 0.28 * np.clip(r / 0.45, 0, 1))[..., None]
    return save_png(f"T_Wild_{kind}Leaves", rgba)


# ------------------------------------------------------------------------------------------------ the shapes
def tube(bm, uvl, pts, radii, sides, mat):
    rings = []
    length = [0.0]
    for i in range(1, len(pts)): length.append(length[-1] + (pts[i] - pts[i - 1]).length)
    for i, (p, r) in enumerate(zip(pts, radii)):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        a = Vector((1, 0, 0)) if abs(t.x) < 0.9 else Vector((0, 1, 0))
        n_ = t.cross(a).normalized(); b = t.cross(n_)
        rings.append([bm.verts.new(p + (n_ * math.cos(2 * math.pi * k / sides) + b * math.sin(2 * math.pi * k / sides)) * r) for k in range(sides)])
    faces = 0
    for i in range(len(rings) - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            f = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k])); f.material_index = mat; faces += 1
            for lp, (u, v) in zip(f.loops, ((k / sides, length[i]), ((k + 1) / sides, length[i]), ((k + 1) / sides, length[i + 1]), (k / sides, length[i + 1]))):
                lp[uvl].uv = (u, v)
    return faces


def card(bm, uvl, c, size, normal_axis, up_axis, mat):
    side = normal_axis.cross(up_axis).normalized() * size * 0.5; up = up_axis.normalized() * size * 0.5
    vs = [bm.verts.new(c - side - up), bm.verts.new(c + side - up), bm.verts.new(c + side + up), bm.verts.new(c - side + up)]
    f = bm.faces.new(vs); f.material_index = mat
    for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
    return 1


def cluster(bm, uvl, c, size, rng, mat):
    n = 0
    tilt = Vector((rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), 1.0)).normalized()
    a0 = rng.uniform(0, math.pi)
    for k in range(3):
        a = a0 + k * math.pi / 3
        nrm = Vector((math.cos(a), math.sin(a), 0.0))
        n += card(bm, uvl, c, size, nrm, tilt, mat)
    n += card(bm, uvl, c + Vector((0, 0, size * 0.05)), size * 0.9, Vector((0, 0, 1)), Vector((math.cos(a0), math.sin(a0), 0)), mat)
    return n


def lerp(a, b, t): return a + (b - a) * t


def build(kind, variant, seed):
    S = SPECIES[kind]; rng = random.Random(seed)
    me = bpy.data.meshes.new(f"SM_Wild_{kind}_{variant}"); ob = bpy.data.objects.new(me.name, me); bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap")
    H = rng.uniform(*S["h"]); r0 = S["r0"] * rng.uniform(0.9, 1.1)
    lean = Vector((rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04), 0))
    def trunk_at(t): return Vector((0, 0, H * t)) + lean * (H * t) + Vector((0.18 * math.sin(t * 5.1 + seed), 0.18 * math.cos(t * 4.3 + seed), 0)) * t
    clusters = 0
    if S["fork"]:
        # the acacia: a short trunk, then limbs out to a flat top
        fh = rng.uniform(*S["fork"]); top = H
        pts = [trunk_at(t * fh / H) for t in np.linspace(0, 1, 6)]
        tube(bm, uvl, pts, [r0 * (1.15 - 0.3 * t) for t in np.linspace(0, 1, 6)], 8, 0)
        base = pts[-1]; nl = rng.randint(*S["branches"]); a0 = rng.uniform(0, 2 * math.pi)
        ends = []
        for i in range(nl):
            a = a0 + i * 2 * math.pi / nl + rng.uniform(-0.3, 0.3); out = rng.uniform(2.6, 4.2)
            end = base + Vector((math.cos(a) * out, math.sin(a) * out, top - fh - rng.uniform(0, 1.0)))
            mid = base + (end - base) * 0.5 + Vector((0, 0, 0.5))
            pts = [lerp(lerp(base, mid, t), lerp(mid, end, t), t) for t in np.linspace(0, 1, 7)]
            tube(bm, uvl, pts, [r0 * 0.7 * (1 - 0.75 * t) for t in np.linspace(0, 1, 7)], 6, 0)
            ends.append(end)
        # the flat crown: wide cards round the limbs' ends at the top
        for e in ends:
            for _ in range(rng.randint(5, 7)):
                c = e + Vector((rng.uniform(-1.8, 1.8), rng.uniform(-1.8, 1.8), rng.uniform(-0.25, 0.35)))
                a = rng.uniform(0, math.pi)
                clusters += card(bm, uvl, c, rng.uniform(*S["csize"]), Vector((rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), 1)).normalized(), Vector((math.cos(a), math.sin(a), 0)), 1)
                clusters += card(bm, uvl, c - Vector((0, 0, 0.35)), rng.uniform(*S["csize"]) * 0.7, Vector((math.cos(a), math.sin(a), 0)), Vector((0, 0, 1)), 1)
    else:
        n = 12
        pts = [trunk_at(t) for t in np.linspace(0, 1, n)]
        tube(bm, uvl, pts, [lerp(r0, r0 * 0.18, t) * (1.25 if t < 0.04 else 1.0) for t in np.linspace(0, 1, n)], 8, 0)
        nb = rng.randint(*S["branches"])
        for i in range(nb):
            t = lerp(S["from"], 0.96, (i + rng.random()) / nb)
            o = trunk_at(t); a = rng.uniform(0, 2 * math.pi) + i * 2.4
            up = math.radians(rng.uniform(*S["up"]))
            L = lerp(S["len"][1], S["len"][0], (t - S["from"]) / (1 - S["from"])) * rng.uniform(0.8, 1.1)
            d = Vector((math.cos(a) * math.cos(up), math.sin(a) * math.cos(up), math.sin(up)))
            pts = []
            for k in np.linspace(0, 1, 6):
                p = o + d * (L * k)
                p.z -= S["droop"] * (k ** 2) * L * 0.7
                pts.append(p)
            tube(bm, uvl, pts, [lerp(r0 * lerp(0.42, 0.18, t), 0.012, k) for k in np.linspace(0, 1, 6)], 5, 0)
            for c in range(rng.randint(*S["clusters"])):
                k = lerp(0.45, 1.0, (c + rng.random()) / max(S["clusters"][1], 1))
                p = pts[min(int(k * 5), 5)]
                clusters += cluster(bm, uvl, p + Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), rng.uniform(-0.1, 0.3))), rng.uniform(*S["csize"]), rng, 1)
        # a crown cluster at the top
        clusters += cluster(bm, uvl, trunk_at(1.0) + Vector((0, 0, 0.2)), S["csize"][1] * 1.1, rng, 1)
    bm.to_mesh(me); bm.free()
    for mn in ("Bark", "Leaves"):
        m = bpy.data.materials.get(f"M_Wild_{kind}{mn}") or bpy.data.materials.new(f"M_Wild_{kind}{mn}")
        me.materials.append(m)
    for p in me.polygons: p.use_smooth = p.material_index == 0
    return ob, {"height_m": round(H, 2), "triangles": sum(len(p.vertices) - 2 for p in me.polygons), "cards": clusters}


def export(ob):
    bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    fn = os.path.join(OUT, ob.name + ".fbx")
    bpy.ops.export_scene.fbx(filepath=fn, use_selection=True, object_types={"MESH"}, apply_unit_scale=True, global_scale=100.0, axis_forward="X", axis_up="Z", mesh_smooth_type="FACE")
    return fn


if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rec = {}
    for kind in SPECIES:
        rec[kind] = {"bark": bark(kind), "leaves": leaves(kind), "trees": {}}
        for v, sd in (("A", 11), ("B", 29)):
            ob, info = build(kind, v, sd + len(kind) * 97)
            info["fbx"] = export(ob); rec[kind]["trees"][v] = info
            print(f"WILDTREE {kind} {v}: {info}")
    json.dump(rec, open(os.path.join(OUT, "wild_trees.json"), "w"), indent=1)
    print("WILDTREES done", OUT)
