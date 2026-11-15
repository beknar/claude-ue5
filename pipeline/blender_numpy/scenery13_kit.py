"""The biomes' scenery's own pieces (the list of 2026-11-14, docs/improvements13.txt; the user's choice: what no pack has is built
in Blender by script). Each piece is shapes and painted pictures (numpy), as wild_trees.py's trees (its tube, card and cluster
helpers and its noise are used here):

  Skep_A, Skep_B   straw bee skeps on a plank bench (the meadows' wild hives)
  Nest             a great bird's nest of sticks, three eggs in it (a lone tree's nest)
  Heron_A, Heron_B a grey heron standing, its neck up (A) or bent to the water (B) (the reed ponds)
  BurrowMouth      a burrow's mouth: a ring of thrown-up earth round a dark hole (a burrow town)
  Milestone        a stone post, its top rounded, its face cut with a mark and numerals (beside the old roads)
  Noose            a rope hanging from a branch in a noose (the hanged man's tree)
  StormCell        a storm cell for the far horizon: an anvil cloud 3.2 km across, a rain curtain, a funnel (the far storms)
  Drystone_A/B     a 3 m length of field wall laid dry, its copes on edge (the shepherd's pen)
  AppleTree_A/B,   the old orchard's gnarled fruit trees: a short leaning trunk, a low wide crown of leaf clusters with their
  PlumTree_A/B     fruit painted in
Writes into out_dir: SM_N13_<Piece>.fbx (material slots named <Piece><Part>), T_N13_<Piece><Part>.png, scenery13_kit.json (each
piece's size and triangles, which slots are masked). Z up, metres, origin at the piece's foot. 926 kit <out_dir> imports them.
Blender: -b -P scenery13_kit.py -- out_dir [piece ...]"""
import bpy, bmesh, math, random, sys, os, json
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0] if argv else "scenery13_kit")
ONLY = set(argv[1:])
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wild_trees as WT
WT.OUT = OUT
tube, card, cluster, noise = WT.tube, WT.card, WT.cluster, WT.noise
REC = {}


def png(name, rgb, alpha=None):
    n = rgb.shape[0]
    a = np.ones((n, n, 1)) if alpha is None else alpha[..., None]
    return WT.save_png(name, np.concatenate([np.clip(rgb, 0, 1), a], -1))


def paint_flat(name, col, var=0.12, seed=1, n=256, streak=None):
    """a colour with a noise's grain (and streaks along U or V when asked)"""
    nz = noise(n, seed)
    rgb = np.array(col)[None, None, :] * (1 - var + 2 * var * nz[..., None])
    if streak:
        yy, xx = np.mgrid[0:n, 0:n] / n
        s = np.sin((yy if streak == "v" else xx) * math.pi * 2 * 14 + noise(n, seed + 5, ((8, 1.0),)) * 4) * 0.5 + 0.5
        rgb *= (0.82 + 0.18 * s)[..., None]
    return png(name, rgb)


def new_mesh(name):
    me = bpy.data.meshes.new(name); ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap")
    return me, ob, bm, uvl


def lathe(bm, uvl, profile, sides, mat, z0=0.0, urep=1.0):
    """a surface of revolution about Z from (radius, height) points, its UVs round (urep times) and up"""
    rings = [[bm.verts.new((r * math.cos(2 * math.pi * k / sides), r * math.sin(2 * math.pi * k / sides), z0 + h)) for k in range(sides)] for r, h in profile]
    for i in range(len(rings) - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            f = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k])); f.material_index = mat
            for lp, (u, v) in zip(f.loops, ((k / sides, i / (len(rings) - 1)), ((k + 1) / sides, i / (len(rings) - 1)), ((k + 1) / sides, (i + 1) / (len(rings) - 1)), (k / sides, (i + 1) / (len(rings) - 1)))):
                lp[uvl].uv = (u * urep, v)


def box(bm, uvl, c, s, mat, uvo=(0.0, 0.0), uvs=1.0):
    """an axis box of size s centred at c; its faces map the picture's square at uvo of side uvs (each stone its own patch)"""
    v = [bm.verts.new((c[0] + sx * s[0] / 2, c[1] + sy * s[1] / 2, c[2] + sz * s[2] / 2)) for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
    for q in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        f = bm.faces.new([v[i] for i in q]); f.material_index = mat
        for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = (uvo[0] + uv[0] * uvs, uvo[1] + uv[1] * uvs)


def sphere(bm, uvl, c, r, mat, rx=1.0, ry=1.0, rz=1.0, seg=10, rough=0.0, rng=None):
    """an ellipsoid; rough: each point pushed in or out by up to that share of the radius (a stone's, a cloud's lumpiness)"""
    rings = []
    for i in range(seg + 1):
        th = math.pi * i / seg
        row = []
        for k in range(seg):
            f = 1.0 + (rng.uniform(-rough, rough) if rough and rng and 0 < i < seg else 0.0)
            row.append(bm.verts.new((c[0] + r * f * rx * math.sin(th) * math.cos(2 * math.pi * k / seg), c[1] + r * f * ry * math.sin(th) * math.sin(2 * math.pi * k / seg), c[2] + r * f * rz * math.cos(th))))
        rings.append(row)
    for i in range(seg):
        for k in range(seg):
            k2 = (k + 1) % seg
            q = (rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k])
            if len(set(q)) < 4: continue
            try: f = bm.faces.new(q)
            except ValueError: continue
            f.material_index = mat
            for lp, uv in zip(f.loops, ((k / seg, i / seg), ((k + 1) / seg, i / seg), ((k + 1) / seg, (i + 1) / seg), (k / seg, (i + 1) / seg))): lp[uvl].uv = uv


def finish(me, ob, bm, slots, masked=(), translucent=(), flat=False):
    """the mesh written as an FBX (flat: every face flat-shaded, a dry wall's stones), its record"""
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    bm.to_mesh(me); bm.free()
    for s in slots:
        m = bpy.data.materials.get(s) or bpy.data.materials.new(s); me.materials.append(m)
    for p in me.polygons: p.use_smooth = not flat
    bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    fn = os.path.join(OUT, ob.name + ".fbx")
    # (scale 1: with the unit scale applied the file is already in centimetres; wild_trees.py's 100 made its meshes 100 times their size,
    # unseen because its trees are always laid by a height)
    bpy.ops.export_scene.fbx(filepath=fn, use_selection=True, object_types={"MESH"}, apply_unit_scale=True, global_scale=1.0, axis_forward="X", axis_up="Z", mesh_smooth_type="FACE")
    xs = [v.co for v in me.vertices]
    size = [round(max(c[i] for c in xs) - min(c[i] for c in xs), 2) for i in range(3)]
    REC[ob.name] = {"fbx": fn, "size_m": size, "triangles": sum(len(p.vertices) - 2 for p in me.polygons), "slots": list(slots), "masked": list(masked), "translucent": list(translucent)}
    print("N13KIT", ob.name, REC[ob.name]["size_m"], REC[ob.name]["triangles"])


# ------------------------------------------------------------------------------------------------ the pieces
def skep(variant, seed):
    rng = random.Random(seed)
    name = f"SM_N13_Skep_{variant}"
    me, ob, bm, uvl = new_mesh(name)
    # (a bench of two posts and a plank, the skeps on it: one or two straw domes, coiled (the bands in the picture))
    L = 1.3 if variant == "B" else 0.8
    for x in (-L / 2 + 0.08, L / 2 - 0.08):
        box(bm, uvl, (x, 0, 0.22), (0.09, 0.32, 0.44), 1)
    box(bm, uvl, (0, 0, 0.47), (L, 0.42, 0.06), 1)
    n = 2 if variant == "B" else 1
    for i in range(n):
        x = (i - (n - 1) / 2) * 0.62
        h = rng.uniform(0.46, 0.54); r = rng.uniform(0.21, 0.25)
        prof = [(r * 1.02, 0.0), (r, 0.06)] + [(r * math.cos(t * math.pi / 2) ** 0.8 + 0.001, 0.06 + (h - 0.06) * math.sin(t * math.pi / 2)) for t in np.linspace(0.1, 1.0, 9)]
        bmv = len(bm.verts)
        lathe(bm, uvl, prof, 14, 0, z0=0.50)
        for v in list(bm.verts)[bmv:]: v.co.x += x
        # (the hive's mouth: a dark notch at its foot)
        box(bm, uvl, (x + r * 0.95, 0, 0.53), (0.03, 0.09, 0.05), 1)
    finish(me, ob, bm, [f"Skep{variant}Straw", f"Skep{variant}Wood"])


def nest():
    rng = random.Random(77)
    me, ob, bm, uvl = new_mesh("SM_N13_Nest")
    # (sticks laid round a bowl 2.2 m across: tubes along arcs at a few heights, a bowl of matted twigs inside, three eggs)
    for i in range(70):
        a0 = rng.uniform(0, 2 * math.pi); span = rng.uniform(0.6, 1.4); rr = rng.uniform(0.75, 1.15); z = rng.uniform(0.05, 0.6) * (rr - 0.55) / 0.6
        pts = [Vector((math.cos(a0 + span * t) * rr, math.sin(a0 + span * t) * rr, z + rng.uniform(-0.04, 0.04))) for t in np.linspace(0, 1, 6)]
        tube(bm, uvl, pts, [rng.uniform(0.025, 0.045)] * 6, 5, 0)
    lathe(bm, uvl, [(0.05, 0.12), (0.45, 0.16), (0.78, 0.32), (0.95, 0.5)], 18, 0)
    for k in range(3):
        a = k * 2.1 + 0.4
        sphere(bm, uvl, (math.cos(a) * 0.18, math.sin(a) * 0.18, 0.24), 0.08, 1, 1.0, 1.0, 1.3, 8)
    finish(me, ob, bm, ["NestTwigs", "NestEggs"])


def heron(variant):
    me, ob, bm, uvl = new_mesh(f"SM_N13_Heron_{variant}")
    # (a grey body, a white neck, a yellow bill, black crest and wing edges, yellow-brown legs: a picture of four colours, each face
    # mapped into its colour's square)
    bent = variant == "B"
    def paint(mat_uv):
        pass
    body_c = Vector((0, 0, 0.62))
    sphere(bm, uvl, body_c, 0.17, 0, 1.6, 0.85, 0.9, 10)
    # neck: an S up and forward (A) or down and forward to the water (B)
    if bent: pts = [body_c + Vector((0.2, 0, 0.05)), Vector((0.38, 0, 0.66)), Vector((0.52, 0, 0.6)), Vector((0.62, 0, 0.42)), Vector((0.66, 0, 0.3))]
    else: pts = [body_c + Vector((0.2, 0, 0.06)), Vector((0.3, 0, 0.86)), Vector((0.24, 0, 1.02)), Vector((0.3, 0, 1.18)), Vector((0.36, 0, 1.24))]
    tube(bm, uvl, pts, [0.05, 0.035, 0.03, 0.03, 0.028], 6, 1)
    head = pts[-1]
    sphere(bm, uvl, head, 0.045, 1, 1.4, 0.9, 0.9, 8)
    d = (Vector((0.15, 0, -0.35)) if bent else Vector((0.22, 0, -0.02))).normalized()
    tube(bm, uvl, [head + d * 0.04, head + d * 0.22], [0.014, 0.002], 5, 2)
    tube(bm, uvl, [head + Vector((-0.03, 0, 0.02)), head + Vector((-0.16, 0, 0.0))], [0.008, 0.002], 4, 3)   # the crest
    for y in (-0.06, 0.06):
        tube(bm, uvl, [Vector((0.02, y, 0.5)), Vector((0.04, y, 0.24)), Vector((0.03, y, 0.0))], [0.012, 0.01, 0.01], 5, 3)
        tube(bm, uvl, [Vector((0.03, y, 0.005)), Vector((0.15, y * 1.4, 0.005))], [0.008, 0.005], 4, 3)
    tube(bm, uvl, [body_c + Vector((-0.2, 0, 0.0)), body_c + Vector((-0.38, 0, -0.08))], [0.07, 0.01], 6, 0)   # the tail
    finish(me, ob, bm, [f"Heron{variant}Body", f"Heron{variant}Neck", f"Heron{variant}Bill", f"Heron{variant}Dark"])


def burrow():
    me, ob, bm, uvl = new_mesh("SM_N13_BurrowMouth")
    # (earth thrown up round a hole 0.5 m across, its foot at the ground: a ring rising to a lip, its inside down to the ground's
    # level, and there the hole: a dark disc a hair over the ground (the ground is drawn over anything below it))
    prof = [(1.25, -0.08), (1.0, 0.12), (0.7, 0.3), (0.42, 0.34), (0.3, 0.2), (0.27, 0.03)]
    lathe(bm, uvl, prof, 20, 0)
    lathe(bm, uvl, [(0.27, 0.03), (0.0, 0.02)], 20, 1)
    finish(me, ob, bm, ["BurrowEarth", "BurrowHole"])


def milestone():
    me, ob, bm, uvl = new_mesh("SM_N13_Milestone")
    # (a squared post 0.45 x 0.3 m, 1.15 m out of the ground, its top a half round; the face's picture carries the cut marks)
    w, d, h = 0.46, 0.3, 0.92
    box(bm, uvl, (0, 0, h / 2 - 0.15), (d, w, h + 0.3), 0)
    prof = [(0.001, 0.0)]
    rings = []
    for i in range(9):
        t = math.pi * i / 8
        rings.append([bm.verts.new((sx * d / 2, -math.cos(t) * w / 2, h + math.sin(t) * w / 2)) for sx in (-1, 1)])
    for i in range(8):
        f = bm.faces.new((rings[i][0], rings[i][1], rings[i + 1][1], rings[i + 1][0])); f.material_index = 0
        for lp, uv in zip(f.loops, ((0, i / 8), (1, i / 8), (1, (i + 1) / 8), (0, (i + 1) / 8))): lp[uvl].uv = uv
    for sx in (-1, 1):
        vs = [r[0 if sx < 0 else 1] for r in rings]
        f = bm.faces.new(vs if sx > 0 else list(reversed(vs))); f.material_index = 1
        for lp, v in zip(f.loops, vs if sx > 0 else list(reversed(vs))): lp[uvl].uv = (0.5 + v.co.y / w, (v.co.z - h) / (w / 2) * 0.5 + 0.5)
    # (the face: a plate a hair proud of the post's front, carrying the cut numerals)
    vs = [bm.verts.new((d / 2 + 0.004, y, z)) for (y, z) in ((-w / 2 + 0.03, 0.12), (w / 2 - 0.03, 0.12), (w / 2 - 0.03, h - 0.02), (-w / 2 + 0.03, h - 0.02))]
    f = bm.faces.new(vs); f.material_index = 1
    for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
    finish(me, ob, bm, ["MilestoneStone", "MilestoneFace"])


def drystone(variant, seed):
    """a field wall of stones laid dry, 3 m long, 1.1 m high, 0.6 m thick at its foot and 0.4 at its top: rows of rough stones
    (boxes of varied size, turned a little), copes stood on edge along its top"""
    rng = random.Random(seed)
    me, ob, bm, uvl = new_mesh(f"SM_N13_Drystone_{variant}")
    z = 0.0; rows = 0
    while z < 0.92:
        h = rng.uniform(0.14, 0.22); w = 0.6 - 0.2 * z / 1.1; x = -1.5
        while x < 1.5:
            L = min(rng.uniform(0.25, 0.5), 1.5 - x)
            if L < 0.06: break
            bmv = len(bm.verts)
            sphere(bm, uvl, (x + L / 2, rng.uniform(-0.04, 0.04), z + h / 2), 0.5, 0, L * 1.05, w * rng.uniform(0.85, 1.0), h * rng.uniform(0.95, 1.1), 7, 0.18, rng)
            a = rng.uniform(-0.14, 0.14)
            for v in list(bm.verts)[bmv:]:
                v.co.z += (v.co.x - (x + L / 2)) * a
            x += L
        z += h; rows += 1
    x = -1.5
    while x < 1.45:
        L = rng.uniform(0.12, 0.2)
        sphere(bm, uvl, (x + L / 2, 0, z + 0.13), 0.5, 0, L * 1.0, 0.34, 0.28 * rng.uniform(0.85, 1.05), 6, 0.15, rng)
        x += L
    finish(me, ob, bm, [f"Drystone{variant}Stone"])


def storm():
    """a storm cell seen from kilometres off (the plains' "distant storm cells or tornadoes visible for miles"): a dark anvil cloud of
    lumps 3.2 km across, 1.2 to 2.6 km up, a curtain of rain under it (an open cylinder, its streaks masked), a funnel to the ground
    off its middle; its origin at the ground under the cloud's middle"""
    rng = random.Random(91)
    me, ob, bm, uvl = new_mesh("SM_N13_StormCell")
    for i in range(110):
        a = rng.uniform(0, 2 * math.pi); d = math.sqrt(rng.random()) * 1350.0
        z = 1350.0 + rng.uniform(0.0, 900.0) * (1.0 - 0.5 * d / 1350.0)
        sphere(bm, uvl, (math.cos(a) * d, math.sin(a) * d, z), rng.uniform(180.0, 420.0), 0, 1.0, 1.0, rng.uniform(0.7, 1.0), 10, 0.22, rng)
    # (the anvil's flat top spreading out on one side)
    for i in range(14):
        a = rng.uniform(-0.6, 0.6); d = rng.uniform(600.0, 1700.0)
        sphere(bm, uvl, (math.cos(a) * d, math.sin(a) * d, rng.uniform(2300.0, 2550.0)), rng.uniform(300.0, 500.0), 0, 1.4, 1.0, 0.25, 10)
    lathe(bm, uvl, [(900.0, 0.0), (960.0, 700.0), (1020.0, 1400.0)], 48, 1, urep=48.0)
    # (the funnel: a twisted cone from the cloud's base down to the ground, 1150 m off its middle: outside the rain)
    pts = [Vector((1150.0 + 60.0 * math.sin(t * 5.0), 40.0 * math.cos(t * 4.0), 1450.0 * (1 - t))) for t in np.linspace(0, 1, 14)]
    tube(bm, uvl, pts, [lerp_(160.0, 18.0, t) for t in np.linspace(0, 1, 14)], 12, 2)
    finish(me, ob, bm, ["StormCloud", "StormRain", "StormFunnel"], translucent=["StormRain"])


def lerp_(a, b, t): return a + (b - a) * t


def noose():
    me, ob, bm, uvl = new_mesh("SM_N13_Noose")
    # (a rope from 2.4 m down to a loop at 1.1 m, its knot a thick wrap: hung from a branch)
    pts = [Vector((0, 0, 2.4 - 1.1 * t)) for t in np.linspace(0, 1, 8)]
    tube(bm, uvl, pts, [0.018] * 8, 6, 0)
    tube(bm, uvl, [Vector((0, 0, 1.36)), Vector((0, 0, 1.18))], [0.04, 0.04], 8, 0)
    loop = [Vector((math.sin(a) * 0.14, 0, 1.18 - (1 - math.cos(a)) * 0.2)) for a in np.linspace(0, 2 * math.pi, 14)]
    tube(bm, uvl, loop, [0.018] * 14, 6, 0)
    finish(me, ob, bm, ["NooseRope"])


def fruit_tree(kind, variant, seed):
    """an old orchard tree: a short leaning, forking trunk, its limbs out to a low wide crown of leaf clusters"""
    rng = random.Random(seed)
    me, ob, bm, uvl = new_mesh(f"SM_N13_{kind}Tree_{variant}")
    H = rng.uniform(4.2, 5.4); r0 = rng.uniform(0.15, 0.2)
    lean = Vector((rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), 0))
    fork = rng.uniform(1.3, 1.8)
    pts = [Vector((0, 0, fork * t)) + lean * fork * t + Vector((0.08 * math.sin(t * 4 + seed), 0.06 * math.cos(t * 3 + seed), 0)) for t in np.linspace(0, 1, 6)]
    tube(bm, uvl, pts, [r0 * (1.25 - 0.3 * t) for t in np.linspace(0, 1, 6)], 8, 0)
    base = pts[-1]; nl = rng.randint(4, 6); a0 = rng.uniform(0, 2 * math.pi); clusters = 0
    for i in range(nl):
        a = a0 + i * 2 * math.pi / nl + rng.uniform(-0.35, 0.35); out = rng.uniform(1.4, 2.4)
        end = base + Vector((math.cos(a) * out, math.sin(a) * out, H - fork - rng.uniform(0.3, 1.2)))
        mid = base + (end - base) * 0.45 + Vector((0, 0, 0.35))
        bp = [WT.lerp(WT.lerp(base, mid, t), WT.lerp(mid, end, t), t) for t in np.linspace(0, 1, 7)]
        tube(bm, uvl, bp, [r0 * 0.62 * (1 - 0.8 * t) for t in np.linspace(0, 1, 7)], 6, 0)
        for c in range(rng.randint(3, 5)):
            p = bp[rng.randint(3, 6)] + Vector((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), rng.uniform(-0.2, 0.4)))
            clusters += cluster(bm, uvl, p, rng.uniform(1.3, 1.9), rng, 1)
    clusters += cluster(bm, uvl, base + Vector((0, 0, H - fork)), 2.0, rng, 1)
    finish(me, ob, bm, [f"{kind}TreeBark", f"{kind}TreeLeaves"], masked=[f"{kind}TreeLeaves"])


# ------------------------------------------------------------------------------------------------ the pictures
def pictures():
    n = 256
    yy, xx = np.mgrid[0:n, 0:n] / n
    # straw: pale gold coils (bands along V, the coil's stitching)
    nz = noise(n, 3)
    band = (np.sin(yy * math.pi * 2 * 16) * 0.5 + 0.5) ** 0.6
    straw = np.array([0.72, 0.58, 0.30])[None, None] * (0.7 + 0.3 * band[..., None]) * (0.88 + 0.24 * nz[..., None])
    for v in ("A", "B"):
        png(f"T_N13_Skep{v}Straw", straw); paint_flat(f"T_N13_Skep{v}Wood", (0.36, 0.26, 0.17), 0.18, 4, streak="u")
    paint_flat("T_N13_NestTwigs", (0.33, 0.25, 0.16), 0.3, 6, streak="u")
    paint_flat("T_N13_NestEggs", (0.78, 0.80, 0.72), 0.08, 7)
    for v in ("A", "B"):
        paint_flat(f"T_N13_Heron{v}Body", (0.46, 0.49, 0.52), 0.1, 8, streak="v")
        paint_flat(f"T_N13_Heron{v}Neck", (0.86, 0.86, 0.84), 0.06, 9)
        paint_flat(f"T_N13_Heron{v}Bill", (0.82, 0.66, 0.18), 0.06, 10)
        paint_flat(f"T_N13_Heron{v}Dark", (0.10, 0.10, 0.11), 0.1, 11)
    # earth round the burrow, darkening down the hole (V up the profile: the last rings are the hole)
    earth = np.array([0.36, 0.28, 0.19])[None, None] * (0.78 + 0.4 * noise(n, 12)[..., None])
    earth *= np.clip(1.6 - yy * 1.9, 0.04, 1.0)[..., None]
    png("T_N13_BurrowEarth", earth)
    stone = np.array([0.52, 0.50, 0.46])[None, None] * (0.75 + 0.4 * noise(n, 13)[..., None])
    png("T_N13_MilestoneStone", stone)
    # the face: the stone with a cut cross and numerals (dark grooves drawn as strokes)
    face = stone.copy()
    def stroke(x0, y0, x1, y1, w=0.018):
        px, py = xx, 1 - yy
        dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy
        t = np.clip(((px - x0) * dx + (py - y0) * dy) / L2, 0, 1)
        m = (px - x0 - t * dx) ** 2 + (py - y0 - t * dy) ** 2 < w * w
        face[m] = face[m] * 0.35
    stroke(0.5, 0.86, 0.5, 0.66); stroke(0.40, 0.76, 0.60, 0.76)        # the cross
    for x in (0.18, 0.30):                                              # "II"
        stroke(x, 0.52, x, 0.32)
    stroke(0.42, 0.52, 0.52, 0.32); stroke(0.52, 0.32, 0.62, 0.52)      # "V"
    stroke(0.70, 0.52, 0.84, 0.32); stroke(0.84, 0.52, 0.70, 0.32)      # "X"
    stroke(0.18, 0.22, 0.84, 0.22, 0.008)
    png("T_N13_MilestoneFace", face)
    paint_flat("T_N13_NooseRope", (0.58, 0.48, 0.32), 0.15, 14, streak="v")
    # (the storm: blue-grey cloud, dark rain streaks masked, a funnel of grey bands)
    png("T_N13_StormCloud", np.array([0.22, 0.24, 0.28])[None, None] * (0.55 + 0.7 * noise(n, 18)[..., None]) * (0.7 + 0.5 * (1 - yy))[..., None])
    # (rain: fine streaks, fading in under the cloud and out at the ground (the translucent master reads the picture's alpha))
    rs = np.random.default_rng(19); al = np.zeros((n, n))
    for _ in range(420):
        x = rs.integers(0, n); y0 = rs.integers(0, n // 4); al[y0:, x] = np.maximum(al[y0:, x], rs.uniform(0.35, 1.0))
    fade = np.clip(np.minimum((1 - yy) / 0.25, yy / 0.15), 0, 1)
    png("T_N13_StormRain", np.full((n, n, 3), 0.42), np.clip(al * fade * 1.4, 0, 1))
    png("T_N13_StormFunnel", np.array([0.26, 0.26, 0.28])[None, None] * (0.75 + 0.35 * np.sin((xx + yy * 0.4) * math.pi * 12)[..., None] * 0.5 + 0.25 * noise(n, 20)[..., None]))
    png("T_N13_BurrowHole", np.full((n, n, 3), 0.02) + 0.02 * noise(n, 15)[..., None])
    for v, sd in (("A", 16), ("B", 17)):
        g = np.array([0.80, 0.78, 0.72])[None, None] * (0.72 + 0.4 * noise(n, sd, ((4, 1.0), (16, 0.6), (64, 0.3)))[..., None])
        lich = noise(n, sd + 9, ((8, 1.0), (16, 0.5))) > 0.75
        g[lich] = g[lich] * 0.75 + np.array([0.62, 0.64, 0.42]) * 0.25
        png(f"T_N13_Drystone{v}Stone", g)
    # the orchard trees: dark gnarled bark; leaves with their fruit (red apples, dark purple plums)
    for kind, fruit in (("Apple", (0.72, 0.12, 0.08)), ("Plum", (0.30, 0.10, 0.32))):
        b = np.array([0.30, 0.25, 0.20])[None, None] * (0.6 + 0.5 * noise(n, 20 + len(kind))[..., None])
        b *= (0.75 + 0.25 * np.abs(np.sin(xx * 30 + noise(n, 30, ((4, 1.0),)) * 8)) ** 0.5)[..., None]
        png(f"T_N13_{kind}TreeBark", b)
        rng = np.random.default_rng(40 + len(kind)); N = 512
        Y, X = np.mgrid[0:N, 0:N] / N
        rgba = np.zeros((N, N, 4))
        pal = [(0.30, 0.42, 0.14), (0.36, 0.48, 0.16), (0.24, 0.36, 0.12)]
        for _ in range(170):
            a = rng.uniform(0, 2 * math.pi); d = math.sqrt(rng.random()) * 0.46
            cx, cy = 0.5 + math.cos(a) * d, 0.5 + math.sin(a) * d
            rot = rng.uniform(0, math.pi); s = 0.05 * rng.uniform(0.7, 1.3)
            dx, dy = X - cx, Y - cy
            u = dx * math.cos(rot) + dy * math.sin(rot); v = -dx * math.sin(rot) + dy * math.cos(rot)
            m = (u / s) ** 2 + (v / (s * 0.55)) ** 2 < 1.0
            rgba[m, :3] = np.array(pal[rng.integers(3)]) * rng.uniform(0.8, 1.15); rgba[m, 3] = 1.0
        for _ in range(26):
            a = rng.uniform(0, 2 * math.pi); d = math.sqrt(rng.random()) * 0.4
            cx, cy = 0.5 + math.cos(a) * d, 0.5 + math.sin(a) * d; s = rng.uniform(0.022, 0.03)
            m = (X - cx) ** 2 + (Y - cy) ** 2 < s * s
            sh = np.clip(1.0 - ((X - cx + s * 0.4) ** 2 + (Y - cy + s * 0.4) ** 2) / (s * s), 0.5, 1.0)
            rgba[m, :3] = np.array(fruit) * sh[m][:, None] * 1.25; rgba[m, 3] = 1.0
        r = np.sqrt((X - 0.5) ** 2 + (Y - 0.5) ** 2)
        rgba[..., :3] *= (0.72 + 0.28 * np.clip(r / 0.45, 0, 1))[..., None]
        WT.save_png(f"T_N13_{kind}TreeLeaves", rgba)


if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    pictures()
    todo = {"Skep_A": lambda: skep("A", 3), "Skep_B": lambda: skep("B", 5), "Nest": nest, "Heron_A": lambda: heron("A"), "Heron_B": lambda: heron("B"),
            "StormCell": storm, "BurrowMouth": burrow, "Milestone": milestone, "Noose": noose, "Drystone_A": lambda: drystone("A", 61), "Drystone_B": lambda: drystone("B", 67),
            "AppleTree_A": lambda: fruit_tree("Apple", "A", 101), "AppleTree_B": lambda: fruit_tree("Apple", "B", 133),
            "PlumTree_A": lambda: fruit_tree("Plum", "A", 151), "PlumTree_B": lambda: fruit_tree("Plum", "B", 177)}
    for k, f in todo.items():
        if not ONLY or k in ONLY: f()
    old = json.load(open(os.path.join(OUT, "scenery13_kit.json"))) if os.path.exists(os.path.join(OUT, "scenery13_kit.json")) else {}
    old.update(REC)
    json.dump(old, open(os.path.join(OUT, "scenery13_kit.json"), "w"), indent=1)
    print("N13KIT done", len(REC), OUT)
