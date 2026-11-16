"""The biomes' scenery's own pieces (the list of 2026-11-14, docs/improvements13.txt; the user's choice: what no pack has is built
in Blender by script). Each piece is shapes and painted pictures (numpy), as wild_trees.py's trees (its tube, card and cluster
helpers and its noise are used here):

  Skep_A, Skep_B   straw bee skeps on a plank bench (the meadows' wild hives)
  Nest             a great bird's nest of sticks, three eggs in it (a lone tree's nest)
  Heron_A, Heron_B a grey heron standing, its neck up (A) or bent to the water (B) (the reed ponds)
  BurrowMouth      a burrow's mouth: a ring of thrown-up earth round a dark hole (a burrow town)
  Milestone        a stone post, its top rounded, its face cut with a mark and numerals (beside the old roads)
  Noose            a rope hanging from a branch in a noose (the hanged man's tree)
  Baobab_A/B, Termite_A/B, Yurt_A/B, Balbal_A/B, PrayerCairn, HotSpring, SaltPan, Petroglyph_A/B, FusedGlass, SmokePlume,
  Fireweed, Granary  the second phase's (the farms, savannahs, cold steppes and the burned plain): a baobab, termite mounds, nomads'
                   yurts, steppe stone figures, a cairn with prayer flags, a steaming pool, a salt pan's crust, rocks cut with
                   spirals and hunters, fused glass shards, a grass fire's smoke on the horizon, fireweed, a granary on staddle stones
  Flume, SeidStone, Lavvu_A/B, BeaverLodge, BeaverDam, FurStretcher, StiltCache, CharcoalMound, FungusLog, CarvedFace,
  ResinPine_A/B, GoldCard  the third phase's (the forests): a logging camp's timber chute, a sacred stone on three stones, herders'
                   cone tents, a beaver's lodge and dam, a trapper's fur stretcher and his cache on stilts, a charcoal burner's clamp,
                   a log of shelf fungi, an oak's trunk with a carved face, a tapped pine (its herringbone scar and clay cup), and a
                   card whose gold leaves and needles are the gold aspens' and larches' material
  TurfStack_A/B    the fourth phase's (hills and moorland): peat turves stacked to dry (the dew pond is two skins of the land)
  RopeBridge, Serac_A/B, IceArch, FrozenTent, IceBlock  the fifth phase's (mountains, peaks, glaciers): a rope bridge over a
                   gorge, towers of glacier ice, an ice cave's mouth (a moulin is a skin of the land), a climbers' tent drifted with snow, a block
                   of clear ice for what is frozen in it
  NaturalArch, Hoodoo_A/B, CliffDwelling, SunDagger, LogJam, SandRock_A/B/C, Pueblo  the sixth phase's (canyons, canyon networks,
                   mesas): a natural arch of banded sandstone, hoodoos with their caprocks, adobe cliff dwellings in an alcove, a slab
                   with a pecked spiral and two leaning slabs before it, flood debris jammed in a channel, sandstone boulders, a
                   terraced mesa-top pueblo with its ladders
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


def floor(bm):
    """what a dome puts under the ground, set on it (a piece is laid by its lowest point: its underside would stand in view)"""
    for v in bm.verts:
        if v.co.z < 0.0: v.co.z = 0.0


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


def baobab(variant, seed):
    """a baobab: a fat bottle trunk 3 m across, short stubby limbs from its top, sparse leaf clusters at their ends"""
    rng = random.Random(seed)
    me, ob, bm, uvl = new_mesh(f"SM_N13_Baobab_{variant}")
    H = rng.uniform(11.0, 14.0); r0 = rng.uniform(1.4, 1.8)
    prof = [(r0 * f, H * t) for t, f in ((0.0, 1.05), (0.15, 1.0), (0.45, 0.92), (0.7, 0.72), (0.85, 0.5), (1.0, 0.35))]
    lathe(bm, uvl, prof, 14, 0)
    top = Vector((0, 0, H)); n = rng.randint(6, 8)
    for i in range(n):
        a = i * 2 * math.pi / n + rng.uniform(-0.3, 0.3); out = rng.uniform(2.5, 4.0)
        end = top + Vector((math.cos(a) * out, math.sin(a) * out, rng.uniform(1.0, 2.5)))
        pts = [top + (end - top) * t + Vector((0, 0, math.sin(t * math.pi) * 0.6)) for t in np.linspace(0, 1, 6)]
        tube(bm, uvl, pts, [r0 * 0.3 * (1 - 0.7 * t) for t in np.linspace(0, 1, 6)], 6, 0)
        for c in range(2):
            cluster(bm, uvl, end + Vector((rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6), rng.uniform(0, 0.5))), rng.uniform(1.6, 2.2), rng, 1)
    finish(me, ob, bm, [f"Baobab{variant}Bark", f"Baobab{variant}Leaves"], masked=[f"Baobab{variant}Leaves"])


def termite(variant, seed):
    """a termite mound: a lumpy spire of red earth 2.5 to 4 m high, a few lesser spires leaning on it"""
    rng = random.Random(seed)
    me, ob, bm, uvl = new_mesh(f"SM_N13_Termite_{variant}")
    H = rng.uniform(2.6, 4.2)
    for k in range(rng.randint(3, 5)):
        h = H * (1.0 if k == 0 else rng.uniform(0.4, 0.75)); r = rng.uniform(0.5, 0.75) * (1.0 if k == 0 else 0.7)
        cx, cy = (0, 0) if k == 0 else (rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6))
        bmv = len(bm.verts)
        lathe(bm, uvl, [(r * 1.25, -0.05), (r, h * 0.25), (r * 0.7, h * 0.6), (r * 0.35, h * 0.9), (0.05, h)], 10, 0)
        for v in list(bm.verts)[bmv:]:
            v.co.x += cx + rng.uniform(-0.06, 0.06); v.co.y += cy + rng.uniform(-0.06, 0.06); v.co.z += rng.uniform(-0.04, 0.04) * h
    finish(me, ob, bm, [f"Termite{variant}Earth"])


def yurt(variant, seed):
    """a nomads' yurt: a round felt wall 6 m across and 1.7 m high on a lattice, a low cone of a roof to a crown, a painted door"""
    rng = random.Random(seed)
    me, ob, bm, uvl = new_mesh(f"SM_N13_Yurt_{variant}")
    R = rng.uniform(2.8, 3.3)
    lathe(bm, uvl, [(R, 0.0), (R, 1.7)], 24, 0, urep=4.0)
    lathe(bm, uvl, [(R + 0.15, 1.65), (R * 0.55, 2.6), (0.45, 3.1), (0.42, 3.25), (0.0, 3.3)], 24, 1, urep=3.0)
    box(bm, uvl, (R + 0.04, 0, 0.75), (0.08, 0.95, 1.5), 2)
    finish(me, ob, bm, [f"Yurt{variant}Felt", f"Yurt{variant}Roof", f"Yurt{variant}Door"])


def balbal(variant, seed):
    """a steppe stone figure: a squared stone pillar 1.6 to 2.2 m, its top rounded to a head, a face and arms cut into its front"""
    rng = random.Random(seed)
    me, ob, bm, uvl = new_mesh(f"SM_N13_Balbal_{variant}")
    h = rng.uniform(1.5, 2.1)
    box(bm, uvl, (0, 0, h * 0.4 - 0.2), (0.32, 0.5, h * 0.8 + 0.4), 0)
    sphere(bm, uvl, (0, 0, h * 0.85), 0.24, 0, 1.0, 1.1, 1.25, 8, 0.05, rng)
    vs = [bm.verts.new((0.165, y, z)) for (y, z) in ((-0.22, h * 0.25), (0.22, h * 0.25), (0.22, h * 0.95), (-0.22, h * 0.95))]
    f = bm.faces.new(vs); f.material_index = 1
    for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
    finish(me, ob, bm, [f"Balbal{variant}Stone", f"Balbal{variant}Face"])


def prayer_cairn():
    """a cairn of stones 1.5 m high, a pole in its top with strings of cloth flags running down to stones round it"""
    rng = random.Random(203)
    me, ob, bm, uvl = new_mesh("SM_N13_PrayerCairn")
    for i in range(40):
        a = rng.uniform(0, 2 * math.pi); d = rng.random() * 1.0; z = (1.0 - d) * 1.2 * rng.uniform(0.6, 1.0)
        sphere(bm, uvl, (math.cos(a) * d, math.sin(a) * d, z + 0.12), rng.uniform(0.15, 0.3), 0, 1.0, 0.9, 0.6, 6, 0.15, rng)
    tube(bm, uvl, [Vector((0, 0, 0.8)), Vector((0, 0, 3.4))], [0.05, 0.03], 6, 1)
    for k in range(4):
        a = k * math.pi / 2 + 0.3; end = Vector((math.cos(a) * 3.2, math.sin(a) * 3.2, 0.3))
        top = Vector((0, 0, 3.3))
        for i in range(9):
            t = (i + 0.5) / 9
            p = top + (end - top) * t - Vector((0, 0, math.sin(t * math.pi) * 0.35))
            card(bm, uvl, p, 0.22, Vector((-math.sin(a), math.cos(a), 0)), Vector((0, 0, 1)), 2)
    finish(me, ob, bm, ["PrayerCairnStone", "PrayerCairnPole", "PrayerCairnFlags"], masked=["PrayerCairnFlags"])


def hot_spring():
    """a steaming pool 5 m across in a rim of pale mineral stone, its water a hair over the ground"""
    rng = random.Random(211)
    me, ob, bm, uvl = new_mesh("SM_N13_HotSpring")
    for i in range(26):
        a = i * 2 * math.pi / 26 + rng.uniform(-0.06, 0.06); d = 2.5 + rng.uniform(-0.15, 0.15)
        sphere(bm, uvl, (math.cos(a) * d, math.sin(a) * d, 0.08), rng.uniform(0.28, 0.45), 0, 1.2, 0.9, 0.55, 7, 0.15, rng)
    lathe(bm, uvl, [(2.45, 0.06), (0.0, 0.06)], 28, 1)
    finish(me, ob, bm, ["HotSpringRim", "HotSpringWater"], translucent=["HotSpringWater"])


def salt_pan():
    """a dry salt pan's crust: a flat white disc 30 m across, cracked into plates, a hair over the ground"""
    me, ob, bm, uvl = new_mesh("SM_N13_SaltPan")
    prof = [(15.0 * (1 - t) + 0.01, 0.03 + 0.01 * math.sin(t * 9)) for t in np.linspace(0, 1, 8)]
    lathe(bm, uvl, prof, 40, 0, urep=6.0)
    finish(me, ob, bm, ["SaltPanCrust"], masked=["SaltPanCrust"])


def petroglyph(variant, seed):
    """a rounded rock 2 m high with a smoothed face, spirals and hunting figures cut into it"""
    rng = random.Random(seed)
    me, ob, bm, uvl = new_mesh(f"SM_N13_Petroglyph_{variant}")
    sphere(bm, uvl, (0, 0, 0.8), 1.0, 0, 1.4, 0.9, 1.0, 10, 0.08, rng)
    vs = [bm.verts.new((0.78, y, z)) for (y, z) in ((-0.9, 0.35), (0.9, 0.35), (0.9, 1.35), (-0.9, 1.35))]
    f = bm.faces.new(vs); f.material_index = 1
    for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
    finish(me, ob, bm, [f"Petroglyph{variant}Rock", f"Petroglyph{variant}Face"], masked=[f"Petroglyph{variant}Face"])


def fused_glass():
    """a scatter of black glassy shards where the burn ran hottest: twisted blades of glass up to 1.4 m"""
    rng = random.Random(223)
    me, ob, bm, uvl = new_mesh("SM_N13_FusedGlass")
    for i in range(18):
        a = rng.uniform(0, 2 * math.pi); d = rng.random() * 2.0; h = rng.uniform(0.3, 1.4)
        base = Vector((math.cos(a) * d, math.sin(a) * d, -0.1)); tip = base + Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), h))
        tube(bm, uvl, [base, (base + tip) * 0.5, tip], [rng.uniform(0.08, 0.18), rng.uniform(0.05, 0.12), 0.005], 4, 0)
    finish(me, ob, bm, ["FusedGlassGlass"], flat=True)


def smoke_plume():
    """a grass fire's smoke on the horizon: a leaning column 200 m across at its foot widening to 900 m, 1.8 km high (see-through)"""
    me, ob, bm, uvl = new_mesh("SM_N13_SmokePlume")
    pts = [Vector((t * 500.0, 0.0, 1800.0 * t)) for t in np.linspace(0, 1, 12)]
    tube(bm, uvl, pts, [100.0 + 350.0 * t ** 0.8 for t in np.linspace(0, 1, 12)], 24, 0)
    finish(me, ob, bm, ["SmokePlumeSmoke"], translucent=["SmokePlumeSmoke"])


def fireweed():
    """a clump of fireweed: tall pink flower spikes on crossed cards, 1.2 to 1.6 m"""
    rng = random.Random(229)
    me, ob, bm, uvl = new_mesh("SM_N13_Fireweed")
    for i in range(7):
        c = Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), 0.7)); a = rng.uniform(0, math.pi)
        card(bm, uvl, c, 1.4, Vector((math.cos(a), math.sin(a), 0)), Vector((0, 0, 1)), 0)
        card(bm, uvl, c, 1.4, Vector((-math.sin(a), math.cos(a), 0)), Vector((0, 0, 1)), 0)
    finish(me, ob, bm, ["FireweedSpike"], masked=["FireweedSpike"])


def granary():
    """a small timber granary up on staddle stones (mushroom-shaped stones the rats cannot climb), its roof a thatched pyramid"""
    me, ob, bm, uvl = new_mesh("SM_N13_Granary")
    for x in (-1.5, 0.0, 1.5):
        for y in (-1.1, 1.1):
            n0 = len(bm.verts)
            lathe(bm, uvl, [(0.18, 0.0), (0.12, 0.42), (0.36, 0.48), (0.34, 0.6), (0.001, 0.62)], 8, 0)
            for v in list(bm.verts)[n0:]: v.co.x += x; v.co.y += y
    box(bm, uvl, (0, 0, 0.68), (3.8, 2.9, 0.12), 1)
    box(bm, uvl, (0, 0, 1.74), (3.6, 2.7, 2.0), 1)
    n0 = len(bm.verts)
    lathe(bm, uvl, [(2.75, 2.7), (0.001, 4.0)], 4, 2)
    for v in list(bm.verts)[n0:]:
        x, y = v.co.x, v.co.y
        v.co.x, v.co.y = (x - y) * 0.7071 * 1.25, (x + y) * 0.7071
    finish(me, ob, bm, ["GranaryStone", "GranaryWood", "GranaryThatch"])


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


# ------------------------------------------------------------------------------------------------ the third phase: the forests
def flume():
    """a timber chute: a V trough of planks 12 m long on trestles, falling 2.5 m along it (the logging camp's)"""
    me, ob, bm, uvl = new_mesh("SM_N13_Flume")
    L, drop = 12.0, 2.5
    for k in range(7):
        t = k / 6; x = -L / 2 + L * t; z = 1.6 + drop * (1 - t)
        for s in (-1, 1):
            tube(bm, uvl, [Vector((x, s * 0.55, 0.0)), Vector((x, s * 0.3, z))], [0.08, 0.07], 6, 1)
        box(bm, uvl, (x, 0, z - 0.05), (0.12, 0.9, 0.1), 1)
    for s in (-1, 1):
        a = Vector((-L / 2, s * 0.02, 1.6 + drop)); b = Vector((L / 2, s * 0.02, 1.6))
        n = Vector((0, s * 0.42, 0.42))
        # (each wall wound to face into the trough (PR #67's review: the -Y wall faced out, culled from inside the V))
        quad = (a, b, b + n, a + n) if s > 0 else (b, a, a + n, b + n)
        vs = [bm.verts.new(p) for p in quad]
        f = bm.faces.new(vs); f.material_index = 0
        for lp, uv in zip(f.loops, ((0, 0), (6, 0), (6, 1), (0, 1))): lp[uvl].uv = uv
    finish(me, ob, bm, ["FlumePlanks", "FlumeTrestle"])


def seid_stone():
    """a seid: a great rounded boulder 2.4 m high set up on three small stones (the herders' sacred stone)"""
    rng = random.Random(401)
    me, ob, bm, uvl = new_mesh("SM_N13_SeidStone")
    for k in range(3):
        a = k * 2 * math.pi / 3 + 0.4
        sphere(bm, uvl, (math.cos(a) * 0.7, math.sin(a) * 0.7, 0.25), 0.35, 0, 1.0, 1.0, 0.8, 7, 0.15, rng)
    sphere(bm, uvl, (0, 0, 1.55), 1.25, 0, 1.25, 1.0, 0.85, 12, 0.08, rng)
    finish(me, ob, bm, ["SeidStoneRock"])


def lavvu(variant, seed):
    """a herders' lavvu: a cone of poles 4.5 m across, its canvas to 3.4 m, the poles crossing out of its top, a door flap"""
    rng = random.Random(seed)
    me, ob, bm, uvl = new_mesh(f"SM_N13_Lavvu_{variant}")
    R = rng.uniform(2.1, 2.4)
    lathe(bm, uvl, [(R, 0.0), (R * 0.55, 1.6), (0.32, 3.2), (0.25, 3.4)], 16, 0, urep=3.0)
    for k in range(10):
        a = k * 2 * math.pi / 10 + rng.uniform(-0.1, 0.1)
        tube(bm, uvl, [Vector((math.cos(a) * R * 1.02, math.sin(a) * R * 1.02, 0)), Vector((-math.cos(a) * 0.35, -math.sin(a) * 0.35, 4.3))], [0.05, 0.03], 5, 1)
    box(bm, uvl, (R * 0.92, 0, 0.7), (0.06, 0.8, 1.4), 2)
    finish(me, ob, bm, [f"Lavvu{variant}Canvas", f"Lavvu{variant}Pole", f"Lavvu{variant}Door"])


def beaver_lodge():
    """a beaver's lodge: a dome of mud and sticks 5 m across and 1.6 m high, sticks poking out of it every way"""
    rng = random.Random(409)
    me, ob, bm, uvl = new_mesh("SM_N13_BeaverLodge")
    sphere(bm, uvl, (0, 0, -0.2), 2.5, 0, 1.0, 1.0, 0.72, 12, 0.07, rng)
    for i in range(70):
        a = rng.uniform(0, 2 * math.pi); el = rng.uniform(0.05, 1.3); r = 2.5
        p = Vector((math.cos(a) * math.cos(el) * r, math.sin(a) * math.cos(el) * r, -0.2 + math.sin(el) * r * 0.72))
        d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.3, 0.6))).normalized() * rng.uniform(0.8, 1.6)
        tube(bm, uvl, [p - d * 0.5, p + d * 0.5], [0.035, 0.025], 4, 1)
    floor(bm)
    finish(me, ob, bm, ["BeaverLodgeMud", "BeaverLodgeSticks"])


def beaver_dam():
    """a beaver dam: a low bank of sticks and mud 10 m long, 1.3 m high, 2 m thick at its foot"""
    rng = random.Random(419)
    me, ob, bm, uvl = new_mesh("SM_N13_BeaverDam")
    for k in range(9):
        sphere(bm, uvl, (-4.5 + k * 1.12, rng.uniform(-0.2, 0.2), 0.0), 1.0, 0, 0.8, 1.0, 1.1, 8, 0.1, rng)
    for i in range(90):
        x = rng.uniform(-5, 5); p = Vector((x, rng.uniform(-0.7, 0.7), rng.uniform(0.2, 1.1)))
        d = Vector((rng.uniform(-0.4, 0.4), rng.uniform(-1, 1), rng.uniform(-0.3, 0.3))).normalized() * rng.uniform(0.9, 1.8)
        tube(bm, uvl, [p - d * 0.5, p + d * 0.5], [0.04, 0.03], 4, 1)
    floor(bm)
    finish(me, ob, bm, ["BeaverLodgeMud", "BeaverLodgeSticks"])


def fur_stretcher():
    """a trapper's fur stretcher: a bent-wood hoop 1.4 m across on a stake, a pelt laced inside it"""
    me, ob, bm, uvl = new_mesh("SM_N13_FurStretcher")
    ring = [Vector((0, math.sin(a) * 0.7, 1.35 + math.cos(a) * 0.7)) for a in np.linspace(0, 2 * math.pi, 20)]
    tube(bm, uvl, ring, [0.035] * 20, 6, 0)
    tube(bm, uvl, [Vector((0, 0, 0)), Vector((0, 0, 0.66))], [0.05, 0.05], 6, 0)
    card(bm, uvl, Vector((0, 0, 1.35)), 1.2, Vector((0, 1, 0)), Vector((0, 0, 1)), 1)
    finish(me, ob, bm, ["FurStretcherWood", "FurStretcherPelt"], masked=["FurStretcherPelt"])


def stilt_cache():
    """a trapper's cache on stilts: a log box 2 m square with a plank roof, up on four 2.6 m poles, a ladder to its door"""
    me, ob, bm, uvl = new_mesh("SM_N13_StiltCache")
    for x in (-0.9, 0.9):
        for y in (-0.9, 0.9):
            tube(bm, uvl, [Vector((x, y, 0)), Vector((x, y, 2.7))], [0.11, 0.09], 7, 0)
    box(bm, uvl, (0, 0, 2.75), (2.2, 2.2, 0.15), 0)
    box(bm, uvl, (0, 0, 3.45), (2.0, 2.0, 1.3), 0)
    n0 = len(bm.verts)
    lathe(bm, uvl, [(1.75, 4.05), (0.001, 4.75)], 4, 1)
    for v in list(bm.verts)[n0:]:
        x, y = v.co.x, v.co.y; v.co.x, v.co.y = (x - y) * 0.7071, (x + y) * 0.7071
    for s in (-0.25, 0.25):
        tube(bm, uvl, [Vector((1.9, s, 0)), Vector((1.15, s, 2.8))], [0.04, 0.04], 5, 0)
    for k in range(6):
        t = (k + 0.5) / 6
        tube(bm, uvl, [Vector((1.9 - 0.75 * t, -0.25, 2.8 * t)), Vector((1.9 - 0.75 * t, 0.25, 2.8 * t))], [0.025, 0.025], 4, 0)
    finish(me, ob, bm, ["StiltCacheLogs", "StiltCacheRoof"])


def charcoal_mound():
    """a charcoal burner's clamp: a turf-covered dome 4.5 m across and 1.7 m high, its vents round its foot"""
    rng = random.Random(431)
    me, ob, bm, uvl = new_mesh("SM_N13_CharcoalMound")
    sphere(bm, uvl, (0, 0, -0.3), 2.3, 0, 1.0, 1.0, 0.86, 14, 0.05, rng)
    for k in range(8):
        a = k * math.pi / 4
        box(bm, uvl, (math.cos(a) * 2.05, math.sin(a) * 2.05, 0.18), (0.25, 0.25, 0.25), 1)
    floor(bm)
    finish(me, ob, bm, ["CharcoalMoundTurf", "CharcoalMoundVent"])


def fungus_log():
    """a fallen trunk 7 m long, 0.6 m thick, its bark peeling, shelf fungi stepped along its side"""
    rng = random.Random(439)
    me, ob, bm, uvl = new_mesh("SM_N13_FungusLog")
    pts = [Vector((-3.5 + 7 * t, 0.15 * math.sin(t * 3), 0.32)) for t in np.linspace(0, 1, 8)]
    tube(bm, uvl, pts, [0.34 - 0.06 * t for t in np.linspace(0, 1, 8)], 10, 0)
    for i in range(22):
        x = rng.uniform(-3.2, 3.2); s = rng.choice((-1, 1)); z = rng.uniform(0.15, 0.6)
        n0 = len(bm.verts)
        lathe(bm, uvl, [(0.001, 0.06), (0.16, 0.05), (0.22, 0.0), (0.001, -0.03)], 10, 1)
        for v in list(bm.verts)[n0:]:
            v.co.y = v.co.y * 0.7 + s * (0.3 + abs(v.co.y) * 0.2); v.co.x += x; v.co.z += z
    finish(me, ob, bm, ["FungusLogBark", "FungusLogShelf"])


def carved_face():
    """a great oak's lower trunk, 3.2 m and 1.1 m thick, a solemn face carved into its front (a harvest shrine's)"""
    rng = random.Random(443)
    me, ob, bm, uvl = new_mesh("SM_N13_CarvedFace")
    lathe(bm, uvl, [(0.75, 0.0), (0.56, 0.4), (0.55, 2.6), (0.6, 3.2), (0.001, 3.25)], 14, 0)
    vs = [bm.verts.new((0.565, y, z)) for (y, z) in ((-0.42, 1.0), (0.42, 1.0), (0.42, 2.3), (-0.42, 2.3))]
    f = bm.faces.new(vs); f.material_index = 1
    for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
    finish(me, ob, bm, ["CarvedFaceBark", "CarvedFaceFace"], masked=["CarvedFaceFace"])


def resin_pine(variant, seed):
    """a tapped pine: a straight trunk 16 m, a high crown of needle clusters, a herringbone scar cut into its foot over a clay cup"""
    rng = random.Random(seed)
    me, ob, bm, uvl = new_mesh(f"SM_N13_ResinPine_{variant}")
    H = rng.uniform(14.0, 17.0)
    # (its lean from 0 at the foot, where the scar and cup are laid for a trunk on x=0 (PR #67's review: centred at 0.15 sin(seed), the
    # scar stood 16 cm off the bark and the cup in the air))
    tube(bm, uvl, [Vector((0.15 * (math.sin(t * 2 + seed) - math.sin(seed)), 0, H * t)) for t in np.linspace(0, 1, 8)], [0.32 * (1 - 0.8 * t) for t in np.linspace(0, 1, 8)], 9, 0)
    for k in range(9):
        z = H * rng.uniform(0.55, 0.98); a = rng.uniform(0, 2 * math.pi); o = rng.uniform(0.6, 2.2) * (1.2 - z / H)
        cluster(bm, uvl, Vector((math.cos(a) * o, math.sin(a) * o, z)), rng.uniform(1.8, 2.6), rng, 1)
    vs = [bm.verts.new((0.33, y, z)) for (y, z) in ((-0.22, 0.4), (0.22, 0.4), (0.22, 1.6), (-0.22, 1.6))]
    f = bm.faces.new(vs); f.material_index = 2
    for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
    n0 = len(bm.verts)
    lathe(bm, uvl, [(0.001, 0.0), (0.1, 0.02), (0.12, 0.18), (0.13, 0.2)], 8, 3)
    for v in list(bm.verts)[n0:]: v.co.x += 0.42; v.co.z += 0.35
    finish(me, ob, bm, [f"ResinPine{variant}Bark", f"ResinPine{variant}Needles", f"ResinPine{variant}Scar", f"ResinPine{variant}Cup"], masked=[f"ResinPine{variant}Needles", f"ResinPine{variant}Scar"])


# ------------------------------------------------------------------------------------------------ the fourth phase: hills and moorland
def turf_stack(variant, seed):
    """peat turves set up to dry: a ridge of dark bricks stacked in a long crossed heap 3 m long and 1 m high"""
    rng = random.Random(seed)
    me, ob, bm, uvl = new_mesh(f"SM_N13_TurfStack_{variant}")
    for layer in range(5):
        n = 9 - layer
        for k in range(n):
            x = -1.5 + (k + 0.5 + layer * 0.5) * 0.33
            if layer % 2 == 0: box(bm, uvl, (x, rng.uniform(-0.05, 0.05), 0.11 + layer * 0.2), (0.3, 0.6, 0.18), 0, (rng.random() * 0.5, rng.random() * 0.5), 0.5)
            else: box(bm, uvl, (x, rng.uniform(-0.05, 0.05), 0.11 + layer * 0.2), (0.6, 0.3, 0.18), 0, (rng.random() * 0.5, rng.random() * 0.5), 0.5)
    finish(me, ob, bm, [f"TurfStack{variant}Peat"], flat=True)


# ------------------------------------------------------------------------------------------------ the fifth phase: mountains, peaks, glaciers
def rope_bridge():
    """a rope bridge 24 m across a gorge: two post pairs, plank deck sagging 1.5 m between them, rope rails and hangers"""
    me, ob, bm, uvl = new_mesh("SM_N13_RopeBridge")
    L = 24.0; sag = 1.5
    for x in (-L / 2, L / 2):
        for y in (-0.7, 0.7):
            tube(bm, uvl, [Vector((x, y, -0.6)), Vector((x, y, 1.4))], [0.1, 0.09], 6, 1)
    deck = lambda t: Vector((-L / 2 + L * t, 0, -sag * math.sin(t * math.pi)))
    for k in range(40):
        t = (k + 0.5) / 40; c = deck(t)
        box(bm, uvl, (c.x, 0, c.z), (0.42, 1.2, 0.05), 0)
    for y in (-0.62, 0.62):
        tube(bm, uvl, [deck(t) + Vector((0, y, 1.0 - 0.25 * math.sin(t * math.pi))) for t in np.linspace(0, 1, 16)], [0.025] * 16, 5, 2)
        tube(bm, uvl, [deck(t) + Vector((0, y, -0.02)) for t in np.linspace(0, 1, 16)], [0.03] * 16, 5, 2)
        for k in range(12):
            t = (k + 0.5) / 12; c = deck(t)
            tube(bm, uvl, [c + Vector((0, y, 0)), c + Vector((0, y, 1.0 - 0.25 * math.sin(t * math.pi)))], [0.015, 0.015], 4, 2)
    finish(me, ob, bm, ["RopeBridgePlanks", "RopeBridgePost", "RopeBridgeRope"])


def serac(variant, seed):
    """a serac: a leaning tower of glacier ice 7 to 10 m, its faces broken flat, smaller blocks round its foot"""
    rng = random.Random(seed)
    me, ob, bm, uvl = new_mesh(f"SM_N13_Serac_{variant}")
    H = rng.uniform(7.0, 10.0)
    for k in range(rng.randint(4, 6)):
        h = H * (1.0 if k == 0 else rng.uniform(0.25, 0.55)); w = rng.uniform(1.6, 2.6) * (1.0 if k == 0 else 0.7)
        cx, cy = (0, 0) if k == 0 else (rng.uniform(-2.5, 2.5), rng.uniform(-2.5, 2.5))
        n0 = len(bm.verts)
        box(bm, uvl, (cx, cy, h / 2), (w, w * rng.uniform(0.7, 1.1), h), 0, (rng.random() * 0.5, rng.random() * 0.5), 0.5)
        lean = rng.uniform(-0.12, 0.12)
        for v in list(bm.verts)[n0:]:
            v.co.x += lean * v.co.z + rng.uniform(-0.15, 0.15); v.co.y += rng.uniform(-0.15, 0.15)
    floor(bm)
    finish(me, ob, bm, [f"Serac{variant}Ice"], flat=True)


def ice_arch():
    """an ice cave's mouth: an arch of blue ice blocks 6 m wide and 4.5 m high over a dark opening"""
    rng = random.Random(601)
    me, ob, bm, uvl = new_mesh("SM_N13_IceArch")
    for k in range(13):
        a = math.pi * k / 12
        x, z = math.cos(a) * 3.2, math.sin(a) * 3.8
        box(bm, uvl, (0, x, z + 0.3), (2.2, 1.1, 1.0), 0, (rng.random() * 0.5, rng.random() * 0.5), 0.5)
    vs = [bm.verts.new((-0.3, y, z)) for (y, z) in ((-2.6, 0.0), (2.6, 0.0), (2.6, 3.4), (-2.6, 3.4))]
    f = bm.faces.new(vs); f.material_index = 1
    for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
    finish(me, ob, bm, ["IceArchIce", "IceArchDark"], flat=True)


def frozen_tent():
    """a climbers' tent left on the mountain: a low ridge tent 2.4 m long, drifted with snow on its windward side"""
    rng = random.Random(613)
    me, ob, bm, uvl = new_mesh("SM_N13_FrozenTent")
    for quad in (((-1.2, -0.9, 0.0), (1.2, -0.9, 0.0), (1.2, 0.0, 1.05), (-1.2, 0.0, 1.05)),
                 ((-1.2, 0.0, 1.05), (1.2, 0.0, 1.05), (1.2, 0.9, 0.0), (-1.2, 0.9, 0.0))):
        vs = [bm.verts.new(p) for p in quad]
        f = bm.faces.new(vs); f.material_index = 0
        for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
    sphere(bm, uvl, (0, -1.0, 0.0), 1.1, 1, 1.4, 0.6, 0.5, 8, 0.1, rng)
    floor(bm)
    finish(me, ob, bm, ["FrozenTentCloth", "FrozenTentSnow"])


def ice_block():
    """a block of clear glacier ice 3 m long, something dark held inside it (the test lays bones within): see-through"""
    rng = random.Random(619)
    me, ob, bm, uvl = new_mesh("SM_N13_IceBlock")
    n0 = len(bm.verts)
    box(bm, uvl, (0, 0, 1.0), (3.0, 1.8, 2.0), 0)
    for v in list(bm.verts)[n0:]: v.co.x += rng.uniform(-0.2, 0.2); v.co.z += rng.uniform(-0.15, 0.15)
    floor(bm)
    finish(me, ob, bm, ["IceBlockIce"], translucent=["IceBlockIce"], flat=True)


# ------------------------------------------------------------------------------------------------ the sixth phase: canyons, mesas
def natural_arch():
    """a natural arch of banded sandstone: two thick legs and a span 14 m across, 10 m high, its underside worn round; the stone in
    rough flat-shaded blocks along an arc (the arch's strata are its picture's bands, by height)"""
    rng = random.Random(701)
    me, ob, bm, uvl = new_mesh("SM_N13_NaturalArch")
    span, hgt = 7.0, 10.0
    for k in range(25):
        a = math.pi * k / 24
        x, z = math.cos(a) * span, math.sin(a) * (hgt - 2.0)
        th = 2.6 + 1.6 * (1.0 - math.sin(a))                  # (thicker at the legs)
        n0 = len(bm.verts)
        box(bm, uvl, (x, 0, z + th * 0.5), (2.2, 3.2 + rng.uniform(-0.3, 0.4), th), 0, (0.0, z / 12.0), 0.25)
        for v in list(bm.verts)[n0:]: v.co.y += rng.uniform(-0.25, 0.25); v.co.x += rng.uniform(-0.2, 0.2)
    for x in (-span, span):                                     # (the legs' feet, wider)
        box(bm, uvl, (x * 1.05, 0, 1.2), (3.6, 4.2, 2.4), 0, (0.0, 0.0), 0.25)
    floor(bm)
    finish(me, ob, bm, ["NaturalArchStone"], flat=True)


def hoodoo(variant, seed):
    """a hoodoo: a spire of soft banded rock 5 to 9 m tall, pinched in places, a hard flat caprock balanced on its top"""
    rng = random.Random(seed)
    me, ob, bm, uvl = new_mesh(f"SM_N13_Hoodoo_{variant}")
    H = rng.uniform(5.0, 9.0); r0 = rng.uniform(1.1, 1.6)
    prof = []
    for i in range(12):
        t = i / 11
        pinch = 1.0 - 0.35 * math.sin(t * math.pi * rng.uniform(2.0, 3.5) + rng.uniform(0, 1)) ** 2
        prof.append((r0 * (1.0 - 0.45 * t) * pinch, H * t))
    lathe(bm, uvl, prof, 9, 0)
    n0 = len(bm.verts)
    for v in list(bm.verts)[:n0]: v.co.x += rng.uniform(-0.08, 0.08); v.co.y += rng.uniform(-0.08, 0.08)
    cw = r0 * rng.uniform(1.1, 1.5)
    box(bm, uvl, (rng.uniform(-0.2, 0.2), 0, H + 0.35), (cw * 1.7, cw * 1.4, 0.7), 1, (0, 0), 1.0)
    floor(bm)
    finish(me, ob, bm, [f"Hoodoo{variant}Stone", f"Hoodoo{variant}Cap"], flat=True)


def cliff_dwelling():
    """cliff dwellings tucked into an alcove: an overhang of rock over a ledge 14 m wide, on it four to five adobe rooms of one and two
    storeys with T-shaped doorways and small windows, roof beams (vigas) poking out, a round tower at one end"""
    rng = random.Random(709)
    me, ob, bm, uvl = new_mesh("SM_N13_CliffDwelling")
    box(bm, uvl, (-1.5, 0, 0.4), (6.0, 16.0, 0.8), 0, (0, 0), 0.5)               # the ledge
    box(bm, uvl, (-4.0, 0, 3.6), (2.0, 17.0, 7.2), 0, (0.5, 0), 0.5)             # the back wall of the alcove
    box(bm, uvl, (-1.8, 0, 7.6), (6.5, 17.5, 1.4), 0, (0, 0.5), 0.5)             # the overhang
    y = -6.5
    while y < 5.5:
        w = rng.uniform(2.2, 3.2); d = rng.uniform(2.4, 3.2); h = rng.choice((2.3, 2.3, 4.4))
        box(bm, uvl, (-3.0 + d / 2, y + w / 2, 0.8 + h / 2), (d, w, h), 1, (rng.random() * 0.5, rng.random() * 0.5), 0.5)
        fx = -3.0 + d + 0.02
        # (a T-shaped doorway on its front (+X), dark; a window on an upper storey)
        for (yy, zz, ww, hh) in ((y + w / 2, 0.8 + 0.6, 0.45, 1.2), (y + w / 2, 0.8 + 1.35, 0.85, 0.35)):
            vs = [bm.verts.new((fx, yy + sy * ww / 2, zz + sz * hh / 2)) for (sy, sz) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            f = bm.faces.new(vs); f.material_index = 2
            for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
        if h > 3.0:
            vs = [bm.verts.new((fx, y + w / 2 + sy * 0.25, 3.9 + sz * 0.2)) for (sy, sz) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            f = bm.faces.new(vs); f.material_index = 2
            for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
        for k in range(3):                                                       # the vigas
            yy = y + w * (k + 1) / 4
            tube(bm, uvl, [Vector((fx - 0.3, yy, 0.8 + h - 0.25)), Vector((fx + 0.5, yy, 0.8 + h - 0.25))], [0.08, 0.08], 5, 3)
        y += w + rng.uniform(0.1, 0.4)
    lathe(bm, uvl, [(1.3, 0.8), (1.25, 4.0), (1.25, 5.6)], 12, 1, z0=0.0)          # the round tower at the near end
    for v in list(bm.verts)[-36:]: v.co.y += 6.6; v.co.x += -1.2
    floor(bm)
    finish(me, ob, bm, ["CliffDwellingRock", "CliffDwellingAdobe", "CliffDwellingDark", "CliffDwellingBeam"], flat=True)


def sun_dagger():
    """a sun dagger: a slab of stone 2.6 m tall with a spiral pecked into its face, two thin slabs leaning in front of it so a blade of
    light falls through their gap"""
    me, ob, bm, uvl = new_mesh("SM_N13_SunDagger")
    box(bm, uvl, (0, 0, 1.3), (0.6, 2.2, 2.6), 0)                    # the carved slab (its face +X carries the spiral)
    for y, lean in ((-0.55, 0.12), (0.55, -0.12)):
        n0 = len(bm.verts)
        box(bm, uvl, (1.0, y, 1.1), (0.25, 0.9, 2.2), 1)
        for v in list(bm.verts)[n0:]: v.co.x -= 0.15 * (v.co.z / 2.2); v.co.y += lean * (v.co.z / 2.2)
    floor(bm)
    finish(me, ob, bm, ["SunDaggerFace", "SunDaggerSlab"], flat=True)


def log_jam():
    """flood debris jammed in a channel: bleached logs, branches and a root wad heaped 6 m across, wedged as the water left them"""
    rng = random.Random(719)
    me, ob, bm, uvl = new_mesh("SM_N13_LogJam")
    for k in range(16):
        a = rng.uniform(-0.6, 0.6) + (math.pi / 2 if k % 3 == 0 else 0.0)
        L = rng.uniform(3.0, 7.0); c = Vector((rng.uniform(-1.5, 1.5), rng.uniform(-2.0, 2.0), rng.uniform(0.2, 1.6)))
        d = Vector((math.cos(a), math.sin(a), rng.uniform(-0.15, 0.25))).normalized()
        tube(bm, uvl, [c - d * L / 2, c + d * L / 2], [rng.uniform(0.12, 0.25), rng.uniform(0.06, 0.15)], 6, 0)
    for k in range(10):
        c = Vector((rng.uniform(-2.5, 2.5), rng.uniform(-2.5, 2.5), rng.uniform(0.3, 1.8)))
        d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.3, 0.6))).normalized()
        tube(bm, uvl, [c, c + d * rng.uniform(1.0, 2.2)], [0.05, 0.02], 4, 0)
    sphere(bm, uvl, (2.2, 1.2, 1.0), 0.9, 1, 1.0, 1.2, 0.8, 8, 0.3, rng)            # a root wad, earth in it
    floor(bm)
    finish(me, ob, bm, ["LogJamWood", "LogJamRoots"])


def sand_rock(variant, seed):
    """a sandstone boulder 1 m across, rounded by the wind, its layers showing (the canyons' rubble: the packs' rocks are dark grey
    and stood out as blue-black boulders on the red sand)"""
    rng = random.Random(seed)
    me, ob, bm, uvl = new_mesh(f"SM_N13_SandRock_{variant}")
    sphere(bm, uvl, (0, 0, 0.25), 0.55, 0, rng.uniform(1.0, 1.4), rng.uniform(0.8, 1.1), rng.uniform(0.55, 0.8), 9, 0.22, rng)
    floor(bm)
    finish(me, ob, bm, [f"SandRock{variant}Stone"], flat=True)


def pueblo():
    """a mesa-top pueblo: mud-brick rooms in terraces, four on the ground, three set back on them, one on top; T-shaped doorways, small
    windows, roof beams (vigas) poking out, ladders up each terrace (its front +X)"""
    rng = random.Random(727)
    me, ob, bm, uvl = new_mesh("SM_N13_Pueblo")
    def door(fx, yc, z0, t_shape=True):
        for (yy, zz, ww, hh) in (((yc, z0 + 0.6, 0.45, 1.2), (yc, z0 + 1.35, 0.85, 0.35)) if t_shape else ((yc, z0 + 1.4, 0.45, 0.4),)):
            vs = [bm.verts.new((fx, yy + sy * ww / 2, zz + sz * hh / 2)) for (sy, sz) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            f = bm.faces.new(vs); f.material_index = 1
            for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
    H = 2.5
    for lvl, (n, x0, depth) in enumerate(((4, 0.0, 3.4), (3, -2.2, 3.0), (1, -4.0, 2.6))):
        w = 3.2; y0 = -n * w / 2
        for k in range(n):
            yc = y0 + w * (k + 0.5) + (0.0 if lvl else rng.uniform(-0.1, 0.1))
            box(bm, uvl, (x0, yc, lvl * H + H / 2), (depth, w - 0.1, H), 0, (rng.random() * 0.5, rng.random() * 0.5), 0.5)
            fx = x0 + depth / 2 + 0.02
            door(fx, yc + rng.uniform(-0.5, 0.5), lvl * H, t_shape=(k % 2 == 0))
            for j in range(3):
                tube(bm, uvl, [Vector((x0 - depth / 2 - 0.3, yc - w / 3 + j * w / 3, lvl * H + H - 0.2)), Vector((x0 - depth / 2 + 0.4, yc - w / 3 + j * w / 3, lvl * H + H - 0.2))], [0.08, 0.08], 5, 2)
                tube(bm, uvl, [Vector((fx - 0.4, yc - w / 3 + j * w / 3, lvl * H + H - 0.2)), Vector((fx + 0.35, yc - w / 3 + j * w / 3, lvl * H + H - 0.2))], [0.08, 0.08], 5, 2)
        if lvl < 2:                                                     # a ladder up to the next terrace
            lx = x0 + depth / 2 + 0.5; ly = y0 + w * 0.5 + lvl * 2.0
            for s_ in (-0.25, 0.25):
                tube(bm, uvl, [Vector((lx, ly + s_, (lvl) * H)), Vector((lx - 0.5, ly + s_, (lvl + 1) * H + 0.9))], [0.04, 0.04], 4, 2)
            for r_ in range(5):
                t = (r_ + 0.5) / 5
                tube(bm, uvl, [Vector((lx - 0.5 * t, ly - 0.25, lvl * H + t * (H + 0.9))), Vector((lx - 0.5 * t, ly + 0.25, lvl * H + t * (H + 0.9)))], [0.025, 0.025], 4, 2)
    floor(bm)
    finish(me, ob, bm, ["PuebloAdobe", "PuebloDark", "PuebloBeam"], flat=True)


def gold_card():
    """one card of gold leaves: only its material is used (the gold aspens' and larches' crowns, a part's mat=)"""
    me, ob, bm, uvl = new_mesh("SM_N13_GoldCard")
    card(bm, uvl, Vector((0, 0, 0.5)), 1.0, Vector((1, 0, 0)), Vector((0, 0, 1)), 0)
    card(bm, uvl, Vector((0, 0, 0.5)), 1.0, Vector((0, 1, 0)), Vector((0, 0, 1)), 1)
    finish(me, ob, bm, ["GoldLeaves", "GoldNeedles"], masked=["GoldLeaves", "GoldNeedles"])


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

    # (the second phase's pieces: farms, savannahs, cold steppes, the burned plain)
    def grain(col, seed, var=0.35, octs=((8, 1.0), (32, 0.5), (64, 0.25))):
        return np.array(col)[None, None] * (1 - var + 2 * var * noise(n, seed, octs)[..., None])
    for v in ("A", "B"):
        png(f"T_N13_Baobab{v}Bark", grain((0.52, 0.47, 0.42), 30) * (0.85 + 0.15 * np.sin(xx * 50)[..., None]))
        rng2 = np.random.default_rng(31); N = 512; Y, X = np.mgrid[0:N, 0:N] / N; rg = np.zeros((N, N, 4))
        for _ in range(110):
            a = rng2.uniform(0, 2 * math.pi); dd = math.sqrt(rng2.random()) * 0.45; cx, cy = 0.5 + math.cos(a) * dd, 0.5 + math.sin(a) * dd
            m = (X - cx) ** 2 + ((Y - cy) * 1.6) ** 2 < 0.03 ** 2
            rg[m, :3] = np.array((0.30, 0.42, 0.14)) * rng2.uniform(0.8, 1.2); rg[m, 3] = 1.0
        WT.save_png(f"T_N13_Baobab{v}Leaves", rg)
        png(f"T_N13_Termite{v}Earth", grain((0.62, 0.36, 0.20), 33 + len(v)))
        felt = grain((0.86, 0.80, 0.68), 35, 0.12)
        band = (np.abs(yy - 0.82) < 0.05) | (np.abs(yy - 0.2) < 0.03)
        felt[band] = np.array((0.62, 0.14, 0.10)); felt[(np.abs(yy - 0.82) < 0.05) & (np.sin(xx * math.pi * 24) > 0.6)] = np.array((0.90, 0.72, 0.30))
        png(f"T_N13_Yurt{v}Felt", felt)
        png(f"T_N13_Yurt{v}Roof", grain((0.82, 0.77, 0.66), 36, 0.1))
        door = grain((0.60, 0.12, 0.08), 37, 0.1); door[(np.abs(xx - 0.5) < 0.42) & (np.abs(yy - 0.5) < 0.45) & ((np.abs(xx - 0.5) > 0.38) | (np.abs(yy - 0.5) > 0.41))] = np.array((0.85, 0.65, 0.2))
        png(f"T_N13_Yurt{v}Door", door)
        stone = grain((0.58, 0.55, 0.50), 38 + len(v))
        png(f"T_N13_Balbal{v}Stone", stone)
        face = stone.copy()
        def cut(x0, y0, x1, y1, w=0.03):
            px, py = xx, 1 - yy; dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy
            t = np.clip(((px - x0) * dx + (py - y0) * dy) / L2, 0, 1)
            face[(px - x0 - t * dx) ** 2 + (py - y0 - t * dy) ** 2 < w * w] *= 0.45
        for a0, a1 in ((0.35, 0.82), (0.65, 0.82)): cut(a0 - 0.06, a1, a0 + 0.06, a1)          # eyes
        cut(0.5, 0.80, 0.5, 0.70); cut(0.40, 0.64, 0.60, 0.64)                                   # nose, mouth
        cut(0.15, 0.50, 0.50, 0.35); cut(0.85, 0.50, 0.50, 0.35); cut(0.44, 0.35, 0.56, 0.32)  # arms to a cup
        png(f"T_N13_Balbal{v}Face", face)
        rock = grain((0.60, 0.50, 0.42), 40 + len(v))
        png(f"T_N13_Petroglyph{v}Rock", rock)
        al = np.zeros((n, n))
        def mark(x0, y0, x1, y1, w=0.012):
            px, py = xx, 1 - yy; dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy + 1e-9
            t = np.clip(((px - x0) * dx + (py - y0) * dy) / L2, 0, 1)
            al[(px - x0 - t * dx) ** 2 + (py - y0 - t * dy) ** 2 < w * w] = 1.0
        for k in range(48):                                                   # a spiral
            t0, t1 = k * 0.35, (k + 1) * 0.35; r0, r1 = 0.012 * t0, 0.012 * t1
            mark(0.25 + r0 * math.cos(t0 * 2), 0.6 + r0 * math.sin(t0 * 2), 0.25 + r1 * math.cos(t1 * 2), 0.6 + r1 * math.sin(t1 * 2))
        for hx in (0.55, 0.72):                                               # two stick hunters with spears
            mark(hx, 0.35, hx, 0.55); mark(hx, 0.55, hx - 0.05, 0.62); mark(hx, 0.55, hx + 0.05, 0.62); mark(hx, 0.35, hx - 0.04, 0.25); mark(hx, 0.35, hx + 0.04, 0.25)
            sphere_mask = (xx - hx) ** 2 + (1 - yy - 0.6) ** 2 < 0.025 ** 2; al[sphere_mask] = 1.0
            mark(hx + 0.06, 0.45, hx + 0.06, 0.75)
        mark(0.82, 0.42, 0.95, 0.42); mark(0.84, 0.42, 0.84, 0.32); mark(0.93, 0.42, 0.93, 0.32); mark(0.95, 0.42, 0.98, 0.5)   # a beast
        WT.save_png(f"T_N13_Petroglyph{v}Face", np.concatenate([np.full((n, n, 3), 0.88), al[..., None]], -1))
    png("T_N13_PrayerCairnStone", grain((0.56, 0.54, 0.50), 42))
    png("T_N13_PrayerCairnPole", grain((0.40, 0.30, 0.20), 43, 0.15))
    fl = np.zeros((n, n, 4)); cols = [(0.15, 0.30, 0.75), (0.95, 0.95, 0.92), (0.80, 0.12, 0.10), (0.15, 0.55, 0.20), (0.92, 0.80, 0.15)]
    for k, c in enumerate(cols):
        m = (xx >= k / 5 + 0.02) & (xx < (k + 1) / 5 - 0.02) & (yy > 0.1) & (yy < 0.9); fl[m, :3] = c; fl[m, 3] = 1.0
    WT.save_png("T_N13_PrayerCairnFlags", fl)
    png("T_N13_HotSpringRim", grain((0.86, 0.78, 0.62), 44, 0.2))
    png("T_N13_HotSpringWater", grain((0.20, 0.62, 0.62), 45, 0.1), np.full((n, n), 0.85))
    crust = grain((0.92, 0.91, 0.88), 46, 0.06)
    cr = noise(n, 47, ((6, 1.0), (12, 0.6)))
    cracks = np.abs(np.sin(cr * 40)) < 0.06
    crust[cracks] = np.array((0.55, 0.50, 0.44))
    png("T_N13_SaltPanCrust", crust, np.clip((1.0 - yy) * 6.0 + noise(n, 48) - 0.4, 0, 1))
    png("T_N13_FusedGlassGlass", grain((0.06, 0.06, 0.07), 49, 0.5))
    png("T_N13_SmokePlumeSmoke", grain((0.80, 0.78, 0.74), 50, 0.2), np.clip(0.55 + 0.45 * noise(n, 51) - 0.3 * yy, 0, 1))
    sp = np.zeros((n, n, 4))
    rs3 = np.random.default_rng(52)
    for k in range(6):
        cx = 0.12 + k * 0.15
        stem = (np.abs(xx - cx) < 0.008) & (yy > 0.05); sp[stem, :3] = (0.25, 0.35, 0.12); sp[stem, 3] = 1.0
        for _ in range(26):
            fy = rs3.uniform(0.05, 0.55); fx = cx + rs3.uniform(-0.03, 0.03)
            m = (xx - fx) ** 2 + (yy - fy) ** 2 < 0.018 ** 2; sp[m, :3] = np.array((0.86, 0.30, 0.62)) * rs3.uniform(0.85, 1.1); sp[m, 3] = 1.0
    WT.save_png("T_N13_FireweedSpike", sp)
    png("T_N13_GranaryStone", grain((0.62, 0.60, 0.55), 53))
    png("T_N13_GranaryWood", grain((0.42, 0.32, 0.22), 54, 0.2) * (0.85 + 0.15 * np.sin(yy * 90)[..., None]))
    png("T_N13_GranaryThatch", grain((0.62, 0.52, 0.30), 55, 0.25) * (0.8 + 0.2 * np.sin(xx * 160)[..., None]))
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

    # (the third phase's pieces: the forests)
    planks = grain((0.46, 0.34, 0.22), 60, 0.2) * (0.8 + 0.2 * (np.sin(yy * math.pi * 2 * 6) > -0.9)[..., None]) * (0.9 + 0.1 * np.sin(xx * 120)[..., None])
    png("T_N13_FlumePlanks", planks); png("T_N13_FlumeTrestle", grain((0.40, 0.30, 0.20), 61, 0.2))
    png("T_N13_SeidStoneRock", grain((0.50, 0.50, 0.47), 62, 0.3) * (1.0 - 0.25 * (noise(n, 63, ((8, 1.0),)) > 0.7))[..., None])
    for v in ("A", "B"):
        png(f"T_N13_Lavvu{v}Canvas", grain((0.70, 0.64, 0.52) if v == "A" else (0.55, 0.50, 0.42), 64 + len(v), 0.12) * (0.85 + 0.15 * (yy > 0.6))[..., None])
        png(f"T_N13_Lavvu{v}Pole", grain((0.42, 0.32, 0.22), 66, 0.2))
        png(f"T_N13_Lavvu{v}Door", grain((0.34, 0.22, 0.16), 67, 0.15))
    png("T_N13_BeaverLodgeMud", grain((0.30, 0.24, 0.17), 68, 0.35))
    png("T_N13_BeaverLodgeSticks", grain((0.44, 0.36, 0.26), 69, 0.25) * (0.8 + 0.2 * np.sin(xx * 60)[..., None]))
    png("T_N13_FurStretcherWood", grain((0.48, 0.36, 0.24), 70, 0.2))
    # (the pelt: a stretched hide's outline, brown fur on its front; nothing round it)
    px, py = xx - 0.5, yy - 0.5
    pelt = ((px / 0.33) ** 2 + (py / 0.42) ** 2 < 1.0) | (((px / 0.42) ** 2 + ((py - 0.25) / 0.12) ** 2) < 1.0)
    png("T_N13_FurStretcherPelt", grain((0.42, 0.30, 0.20), 71, 0.25), pelt.astype(float))
    png("T_N13_StiltCacheLogs", grain((0.44, 0.34, 0.23), 72, 0.2) * (0.78 + 0.22 * np.abs(np.sin(yy * math.pi * 10)))[..., None])
    png("T_N13_StiltCacheRoof", grain((0.32, 0.28, 0.22), 73, 0.25) * (0.85 + 0.15 * np.sin(xx * 90)[..., None]))
    turf = grain((0.28, 0.30, 0.16), 74, 0.35); bare = noise(n, 75, ((6, 1.0), (16, 0.5))) > 0.62
    turf[bare] = np.array((0.16, 0.13, 0.10)) * (0.8 + 0.4 * noise(n, 76)[bare][:, None])
    png("T_N13_CharcoalMoundTurf", turf); png("T_N13_CharcoalMoundVent", np.full((n, n, 3), 0.03))
    png("T_N13_FungusLogBark", grain((0.30, 0.25, 0.19), 77, 0.3) * (0.75 + 0.25 * np.abs(np.sin(xx * 40 + noise(n, 78, ((4, 1.0),)) * 6)))[..., None])
    png("T_N13_FungusLogShelf", grain((0.66, 0.52, 0.34), 79, 0.15) * (0.75 + 0.25 * np.sin(yy * math.pi * 2 * 5)[..., None] * 0.5 + 0.25))
    oak = grain((0.36, 0.31, 0.25), 80, 0.3) * (0.7 + 0.3 * np.abs(np.sin(xx * 34 + noise(n, 81, ((4, 1.0),)) * 7)) ** 0.5)[..., None]
    png("T_N13_CarvedFaceBark", oak)
    fa = np.zeros((n, n))
    def groove(x0, y0, x1, y1, w=0.022):
        gx, gy = xx, 1 - yy; dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy + 1e-9
        t = np.clip(((gx - x0) * dx + (gy - y0) * dy) / L2, 0, 1)
        fa[(gx - x0 - t * dx) ** 2 + (gy - y0 - t * dy) ** 2 < w * w] = 1.0
    for ex in (0.33, 0.67):                                               # deep eyes, brows
        fa[((xx - ex) / 0.07) ** 2 + ((1 - yy - 0.66) / 0.04) ** 2 < 1.0] = 1.0; groove(ex - 0.12, 0.75, ex + 0.12, 0.73)
    groove(0.5, 0.70, 0.46, 0.45); groove(0.46, 0.45, 0.55, 0.43)          # the nose
    groove(0.32, 0.30, 0.5, 0.25); groove(0.5, 0.25, 0.68, 0.30)          # the mouth, turned down
    for k in range(7): groove(0.18 + k * 0.1, 0.12, 0.2 + k * 0.1, 0.02, 0.012)   # a beard of cuts
    WT.save_png("T_N13_CarvedFaceFace", np.concatenate([oak * 0.35, fa[..., None]], -1))
    for v in ("A", "B"):
        png(f"T_N13_ResinPine{v}Bark", grain((0.42, 0.28, 0.20), 82, 0.3) * (0.7 + 0.3 * np.abs(np.sin(yy * 50 + noise(n, 83, ((4, 1.0),)) * 5)) ** 0.5)[..., None])
        rg = np.zeros((512, 512, 4)); R5 = np.random.default_rng(84 + len(v)); Y5, X5 = np.mgrid[0:512, 0:512] / 512
        for _ in range(240):
            a = R5.uniform(0, 2 * math.pi); d = math.sqrt(R5.random()) * 0.45; cx, cy = 0.5 + math.cos(a) * d, 0.5 + math.sin(a) * d
            rot = R5.uniform(0, math.pi); u = (X5 - cx) * math.cos(rot) + (Y5 - cy) * math.sin(rot); w_ = -(X5 - cx) * math.sin(rot) + (Y5 - cy) * math.cos(rot)
            m = (np.abs(u) < 0.045) & (np.abs(w_) < 0.004)
            rg[m, :3] = np.array((0.16, 0.26, 0.12)) * R5.uniform(0.8, 1.2); rg[m, 3] = 1.0
        WT.save_png(f"T_N13_ResinPine{v}Needles", rg)
        sc = np.zeros((n, n))
        for k in range(8):                                               # the herringbone cuts: a V stepped down the face, a channel
            y0 = 0.9 - k * 0.1
            for s in (-1, 1):
                gx, gy = xx - 0.5, 1 - yy
                t = np.clip((gx * s) / 0.35, 0, 1); yl = y0 - 0.12 * t
                sc[(np.abs(gy - yl) < 0.014) & (gx * s >= 0) & (gx * s < 0.35)] = 1.0
        sc[np.abs(xx - 0.5) < 0.015] = 1.0
        WT.save_png(f"T_N13_ResinPine{v}Scar", np.concatenate([np.ones((n, n, 3)) * np.array((0.80, 0.62, 0.30)), sc[..., None]], -1))
        png(f"T_N13_ResinPine{v}Cup", grain((0.62, 0.38, 0.24), 85, 0.15))
    # (the fourth phase: peat turves, each variant its own grain (PR #68's review: seeded by len(v), A and B came out alike))
    for v in ("A", "B"):
        png(f"T_N13_TurfStack{v}Peat", grain((0.17, 0.12, 0.08), 103 + ord(v), 0.35) * (0.8 + 0.2 * (noise(n, 105 + ord(v), ((16, 1.0),)) > 0.5))[..., None])
    # (the fifth phase: planks, posts and rope; glacier ice in blue-white, its shadowed hollows darker; the dark of a cave or a shaft;
    # a tent's faded orange cloth; snow; clear ice)
    png("T_N13_RopeBridgePlanks", grain((0.42, 0.32, 0.22), 120, 0.25) * (0.85 + 0.15 * np.sin(xx * 70)[..., None]))
    png("T_N13_RopeBridgePost", grain((0.36, 0.28, 0.20), 121, 0.2))
    png("T_N13_RopeBridgeRope", grain((0.62, 0.52, 0.36), 122, 0.15))
    ice = lambda sd: grain((0.72, 0.84, 0.92), sd, 0.12) * (0.85 + 0.15 * (noise(n, sd + 1, ((4, 1.0), (16, 0.5))) > 0.5))[..., None]
    for v in ("A", "B"):
        # (lighter than the arch's ice: their flat faces stand mostly in their own shadow, and at 0.72 they read as dark stone)
        png(f"T_N13_Serac{v}Ice", np.clip(grain((0.86, 0.94, 0.99), 124 + ord(v), 0.08) * 1.05, 0, 1))
    png("T_N13_IceArchIce", ice(130)); png("T_N13_IceArchDark", np.full((n, n, 3), 0.03) + np.array((0.0, 0.02, 0.05))[None, None])
    png("T_N13_FrozenTentCloth", grain((0.72, 0.38, 0.16), 134, 0.15) * (0.9 + 0.1 * np.sin(yy * 40)[..., None]))
    png("T_N13_FrozenTentSnow", grain((0.92, 0.94, 0.97), 135, 0.05))
    png("T_N13_IceBlockIce", grain((0.70, 0.84, 0.92), 136, 0.08), np.full((n, n), 0.45))
    # (the sixth phase: banded sandstone (layers of red, orange, cream and brown along V, each its own grain), a hoodoo's dark caprock,
    # sandstone, adobe, dark openings, pale weathered beams, a spiral pecked into a slab's face, bleached flood logs and root earth)
    def strata(sd):
        rr = np.random.default_rng(sd)
        pal = np.array([(0.62, 0.30, 0.17), (0.78, 0.58, 0.40), (0.52, 0.22, 0.14), (0.70, 0.42, 0.24), (0.84, 0.72, 0.56), (0.44, 0.26, 0.21)])
        edges = np.cumsum(rr.uniform(0.04, 0.11, 24)); idx = np.searchsorted(edges / edges[-1], (yy + 0.02 * noise(n, sd + 1)) % 1.0)
        rgb = pal[rr.integers(0, 6, 25)[np.clip(idx, 0, 24)]]
        return np.clip(rgb * (0.86 + 0.24 * noise(n, sd + 2)[..., None]), 0, 1)
    png("T_N13_NaturalArchStone", strata(140))
    for v in ("A", "B"):
        png(f"T_N13_Hoodoo{v}Stone", strata(150 + ord(v))); png(f"T_N13_Hoodoo{v}Cap", grain((0.30, 0.22, 0.17), 160 + ord(v), 0.2))
    png("T_N13_CliffDwellingRock", strata(170))
    png("T_N13_CliffDwellingAdobe", grain((0.66, 0.48, 0.32), 171, 0.14))
    png("T_N13_CliffDwellingDark", np.full((n, n, 3), 0.04) + np.array((0.02, 0.01, 0.0))[None, None])
    png("T_N13_CliffDwellingBeam", grain((0.55, 0.47, 0.38), 172, 0.15) * (0.88 + 0.12 * np.sin(xx * 60)[..., None]))
    face = grain((0.66, 0.46, 0.30), 180, 0.15)
    rr_ = np.hypot(xx - 0.5, yy - 0.5); th_ = np.arctan2(yy - 0.5, xx - 0.5)
    spiral = np.abs(((rr_ * 40.0 - th_ / (2 * math.pi) * 2.5) % 2.5) - 1.25) < 0.35
    face[spiral & (rr_ < 0.42)] *= 0.45
    png("T_N13_SunDaggerFace", face); png("T_N13_SunDaggerSlab", grain((0.60, 0.42, 0.28), 181, 0.18))
    png("T_N13_LogJamWood", grain((0.62, 0.58, 0.52), 190, 0.2) * (0.85 + 0.15 * np.sin(xx * 80)[..., None]))
    png("T_N13_LogJamRoots", grain((0.30, 0.22, 0.15), 191, 0.3))
    for v in ("A", "B", "C"):
        png(f"T_N13_SandRock{v}Stone", strata(200 + ord(v)))
    png("T_N13_PuebloAdobe", grain((0.70, 0.52, 0.36), 210, 0.12)); png("T_N13_PuebloDark", np.full((n, n, 3), 0.05))
    png("T_N13_PuebloBeam", grain((0.55, 0.47, 0.38), 211, 0.15) * (0.88 + 0.12 * np.sin(xx * 60)[..., None]))
    # (gold leaves: the aspen's round leaves in yellow and gold; gold needles: a larch's sprays)
    for name, shape in (("GoldLeaves", "leaf"), ("GoldNeedles", "needle")):
        rg = np.zeros((512, 512, 4)); R6 = np.random.default_rng(90 + len(name)); Y6, X6 = np.mgrid[0:512, 0:512] / 512
        pal = [(0.92, 0.70, 0.12), (0.85, 0.58, 0.08), (0.96, 0.80, 0.22)]
        for _ in range(200 if shape == "leaf" else 300):
            a = R6.uniform(0, 2 * math.pi); d = math.sqrt(R6.random()) * 0.46; cx, cy = 0.5 + math.cos(a) * d, 0.5 + math.sin(a) * d
            rot = R6.uniform(0, math.pi); u = (X6 - cx) * math.cos(rot) + (Y6 - cy) * math.sin(rot); w_ = -(X6 - cx) * math.sin(rot) + (Y6 - cy) * math.cos(rot)
            m = ((u / 0.035) ** 2 + (w_ / 0.03) ** 2 < 1.0) if shape == "leaf" else ((np.abs(u) < 0.04) & (np.abs(w_) < 0.004))
            rg[m, :3] = np.array(pal[R6.integers(3)]) * R6.uniform(0.85, 1.1); rg[m, 3] = 1.0
        WT.save_png(f"T_N13_{name}", rg)


if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    pictures()
    todo = {"Skep_A": lambda: skep("A", 3), "Skep_B": lambda: skep("B", 5), "Nest": nest, "Heron_A": lambda: heron("A"), "Heron_B": lambda: heron("B"),
            "StormCell": storm, "BurrowMouth": burrow, "Milestone": milestone, "Noose": noose, "Drystone_A": lambda: drystone("A", 61), "Drystone_B": lambda: drystone("B", 67),
            "Baobab_A": lambda: baobab("A", 301), "Baobab_B": lambda: baobab("B", 307), "Termite_A": lambda: termite("A", 311), "Termite_B": lambda: termite("B", 313),
            "Yurt_A": lambda: yurt("A", 317), "Yurt_B": lambda: yurt("B", 331), "Balbal_A": lambda: balbal("A", 337), "Balbal_B": lambda: balbal("B", 347),
            "PrayerCairn": prayer_cairn, "HotSpring": hot_spring, "SaltPan": salt_pan, "Petroglyph_A": lambda: petroglyph("A", 349), "Petroglyph_B": lambda: petroglyph("B", 353),
            "FusedGlass": fused_glass, "SmokePlume": smoke_plume, "Fireweed": fireweed, "Granary": granary,
            "AppleTree_A": lambda: fruit_tree("Apple", "A", 101), "AppleTree_B": lambda: fruit_tree("Apple", "B", 133),
            "PlumTree_A": lambda: fruit_tree("Plum", "A", 151), "PlumTree_B": lambda: fruit_tree("Plum", "B", 177),
            "Flume": flume, "SeidStone": seid_stone, "Lavvu_A": lambda: lavvu("A", 401), "Lavvu_B": lambda: lavvu("B", 403),
            "BeaverLodge": beaver_lodge, "BeaverDam": beaver_dam, "FurStretcher": fur_stretcher, "StiltCache": stilt_cache,
            "CharcoalMound": charcoal_mound, "FungusLog": fungus_log, "CarvedFace": carved_face,
            "ResinPine_A": lambda: resin_pine("A", 451), "ResinPine_B": lambda: resin_pine("B", 457), "GoldCard": gold_card,
            "TurfStack_A": lambda: turf_stack("A", 511), "TurfStack_B": lambda: turf_stack("B", 523),
            "RopeBridge": rope_bridge, "Serac_A": lambda: serac("A", 631), "Serac_B": lambda: serac("B", 641), "IceArch": ice_arch,
            "FrozenTent": frozen_tent, "IceBlock": ice_block,
            "NaturalArch": natural_arch, "Hoodoo_A": lambda: hoodoo("A", 703), "Hoodoo_B": lambda: hoodoo("B", 707),
            "CliffDwelling": cliff_dwelling, "SunDagger": sun_dagger, "LogJam": log_jam,
            "SandRock_A": lambda: sand_rock("A", 731), "SandRock_B": lambda: sand_rock("B", 733), "SandRock_C": lambda: sand_rock("C", 739),
            "Pueblo": pueblo}
    for k, f in todo.items():
        if not ONLY or k in ONLY: f()
    old = json.load(open(os.path.join(OUT, "scenery13_kit.json"))) if os.path.exists(os.path.join(OUT, "scenery13_kit.json")) else {}
    old.update(REC)
    json.dump(old, open(os.path.join(OUT, "scenery13_kit.json"), "w"), indent=1)
    print("N13KIT done", len(REC), OUT)
