"""A frigate after its reference picture (I:\\game assets\\3d unity samples\\frigate2.png, the user's of 2026-11-11), built in
Blender from script, its proportions measured from the picture by frigate_fit.py (fit.json: a camera solved with the
engine block, every feature carried back to the ship along its ray; the numbers here are those "picture metres", the
engine block 16 tall, scaled to the ship's length).
Its parts: the hull lofted through its sections (the engine block with its stern chamfers, the step out to the twice as
wide superstructure, its deck rising to the red-capped nose); the stern's engine panel (three chamfered pods of two
nozzles, bezels and glowing throats); the forked bow (the sloping upper blade with its red band, the pod, the two
drooping wedge plates with red leading edges and inset panel lines, the lower blade, the dark keel); the side armour in
layers (framed plates, the porthole panel, the red stripe and wedge, round sockets, hatches, vents, the light bar in its
housing); the deck's framed dark plates, rails, pipe runs and greebles; the chunky sensor head with its recessed blue
window, its mount and three sleeved barrels; the underside's machinery and twin blue capsule lights; the two fins (dark
roots, light blades, red leading edges). Textured with frigate_textures.py's plating (projected from each face's side, top
or end, 16 m a tile); lights are emissive.
Metres: 110 m long, bow toward -Y (glTF +Z), up +Z (glTF +Y). The .blend is saved beside the texture folder; with
--overlay <fit.json> <dir> it also renders her from the fitted camera (<dir>/fitcam.png, transparent), to lay over the
picture: the check. Its silhouette overlaps the picture's by 0.896 (intersection over union, 2026-11-11). The cross-
sections are the picture's: the superstructure's lower side upright to its knuckle at the red stripe, then a steep slope up
to a narrow deck; one view cannot fix every depth, so the superstructure's width (20.8 m) and the engine block's (11.2 m)
are the fit's assumption and the overlay's choice.
Blender: blender -b -P frigate_build.py -- <tex dir> <out.glb> [--preview <dir>] [--overlay <fit.json> <dir>]"""
import bpy, bmesh, json, math, os, random, sys
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
TEX, GLB = os.path.abspath(argv[0]), os.path.abspath(argv[1])
PREVIEW = os.path.abspath(argv[argv.index("--preview") + 1]) if "--preview" in argv else None
OVERLAY = (os.path.abspath(argv[argv.index("--overlay") + 1]), os.path.abspath(argv[argv.index("--overlay") + 2])) if "--overlay" in argv else None
PAL = json.load(open(os.path.join(TEX, "palette.json")))
bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene
COL = SC.collection
L = 110.0
LEN_FIT = 110.0                                                                      # (her length in the fit's units: the wedge tips)
K = L / LEN_FIT
# (the stations along her length: the numbers below were first measured with a camera that saw her too nearly edge-on; the
# second fit, with the engine block's near deck edge picked, measures the step at 24.8, the nose at 71 and the wedge tips at
# 110: s is carried through these knots, piece by piece)
SMAP = [(-5.0, -5.0), (0.0, 0.0), (25.4, 24.8), (65.6, 71.0), (92.0, 110.0), (100.0, 118.0)]


def smap(s, inv=False):
    pts = [(b, a) for a, b in SMAP] if inv else SMAP
    for (a0, b0), (a1, b1) in zip(pts, pts[1:]):
        if s <= a1 or (a1, b1) == pts[-1]:
            return b0 + (b1 - b0) * (s - a0) / (a1 - a0)
    return s


def s_of(c):
    """the measured s of a world point (its station, back through the map)"""
    return smap((L / 2 - c.y) / K, inv=True)
TILE = 16.0
rng = random.Random(2026)


def P(s, x, z):
    """the ship's frame in picture metres: s from the stern toward the bow, x (the picture's near side is -x), z up"""
    return Vector((K * x, L / 2 - K * smap(s), K * z))


# ---------------------------------------------------------------- materials
def lin(c):
    f = lambda v: (v / 255) / 12.92 if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]), 1.0)


def material(name, tex=None, color=None, rough=0.45, metal=0.35, glow=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Roughness"].default_value, b.inputs["Metallic"].default_value = rough, metal
    col = lin(PAL[color] if isinstance(color, str) else color) if color else None
    if tex:
        n = m.node_tree.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(os.path.join(TEX, tex), check_existing=True)
        m.node_tree.links.new(n.outputs["Color"], b.inputs["Base Color"])
    else:
        b.inputs["Base Color"].default_value = col; m.diffuse_color = col
    if glow:
        b.inputs["Emission Color"].default_value = col; b.inputs["Emission Strength"].default_value = glow
    return m


MATS = [material("Hull", tex="hull.png"), material("Deck", tex="deck.png", rough=0.55), material("Red", tex="red.png", rough=0.4),
        material("RedDark", color="red_dark", rough=0.5), material("Machinery", tex="metal.png", rough=0.5, metal=0.6),
        material("Glow", color="blue", rough=0.3, metal=0.0, glow=8.0), material("Window", color="window", rough=0.2, metal=0.0, glow=5.0),
        material("Trim", color=(120, 126, 138), rough=0.4, metal=0.5), material("Dark", color=(26, 29, 35), rough=0.6, metal=0.3)]
HULL, DECK, RED, REDDARK, METAL, GLOW, WINDOW, TRIM, DARK = range(9)

# ---------------------------------------------------------------- parts: every one a closed solid
PARTS = []


def solid(verts, faces, mat, mfn=None, bevel=0.0, seg=2):
    me = bpy.data.meshes.new("part")
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces]); me.update()
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:
        f.material_index = mfn(f.calc_center_median(), f.normal) if mfn else mat
    bm.to_mesh(me); bm.free()
    for m in MATS: me.materials.append(m)
    ob = bpy.data.objects.new("part", me); COL.objects.link(ob)
    if bevel > 0:
        b = ob.modifiers.new("Bevel", "BEVEL"); b.width = bevel * K; b.segments = seg; b.limit_method = "ANGLE"
        b.angle_limit = math.radians(30); b.use_clamp_overlap = True
    PARTS.append(ob)
    return ob


def prism(poly, offset, mat, mfn=None, bevel=0.0, seg=2):
    n = len(poly)
    V = [Vector(p) for p in poly] + [Vector(p) + Vector(offset) for p in poly]
    F = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return solid(V, F, mat, mfn, bevel, seg)


def side_prism(sz, x0, x1, mat, mfn=None, bevel=0.0, seg=2):
    """a profile in (s, z) swept across x0 to x1"""
    return prism([P(s, x0, z) for s, z in sz], (K * (x1 - x0), 0, 0), mat, mfn, bevel, seg)


def plan_prism(sx, z0, z1, mat, mfn=None, bevel=0.0, dz=None):
    """an outline in (s, x) swept up from z0 to z1 (dz: a slope, z rising by dz a metre of s)"""
    if dz is None:
        return prism([P(s, x, z0) for s, x in sx], (0, 0, K * (z1 - z0)), mat, mfn, bevel)
    pts = [P(s, x, z0 + dz * s) for s, x in sx]
    return prism(pts, (0, 0, K * (z1 - z0)), mat, mfn, bevel)


def box(s0, s1, x0, x1, z0, z1, mat, bevel=0.15, mfn=None, seg=2):
    x0, x1 = min(x0, x1), max(x0, x1)
    return side_prism([(s0, z0), (s1, z0), (s1, z1), (s0, z1)], x0, x1, mat, mfn, bevel, seg)


def cylinder(c0, c1, r, mat, seg=20, bevel=0.0):
    c0, c1 = Vector(c0), Vector(c1)
    ax = (c1 - c0).normalized()
    a = ax.orthogonal().normalized(); b = ax.cross(a)
    V = [c + (a * math.cos(2 * math.pi * i / seg) + b * math.sin(2 * math.pi * i / seg)) * (r * K) for c in (c0, c1) for i in range(seg)]
    F = [tuple(range(seg)), tuple(range(2 * seg - 1, seg - 1, -1))] + [(i, (i + 1) % seg, seg + (i + 1) % seg, seg + i) for i in range(seg)]
    return solid(V, F, mat, None, bevel, 1)


def side_x(sx, x):
    return x * sx


def socket(s, z, x, sx, r=0.38):
    """a round socket on a side: a trim rim, a dark hole"""
    out = Vector((sx, 0, 0))
    c = P(s, x * sx, z)
    cylinder(c, c + out * K * 0.18, r, TRIM, 16, 0.04)
    cylinder(c + out * K * 0.05, c + out * K * 0.22, r * 0.62, DARK, 14)


def frame(s0, s1, z0, z1, x, sx, w=0.16, d=0.12, mat=TRIM):
    """a raised outline on a side (a plate's frame): four thin bars"""
    xa, xb = x * sx, (x + d) * sx
    box(s0, s1, xa, xb, z0, z0 + w, mat, 0.03); box(s0, s1, xa, xb, z1 - w, z1, mat, 0.03)
    box(s0, s0 + w, xa, xb, z0, z1, mat, 0.03); box(s1 - w, s1, xa, xb, z0, z1, mat, 0.03)


# ---------------------------------------------------------------- the hull's sections (fit.json's measures, picture metres)
# s, half width, bottom, top (the deck), the top corner's width and height (a slope from the side's knuckle up to the deck:
# the superstructure's is the picture's big sloped upper side, its knuckle at the red stripe's line), bottom chamfer
HW, HM = 5.6, 10.4                                                                    # (the engine block's half width, the superstructure's)
HULL_S = [
    (0.0, 3.5, -7.9, 5.0, 0.5, 0.5, 0.4),                                             # (the stern face: the engine panel's plane)
    (2.5, HW, -8.2, 7.4, 3.4, 1.5, 1.6),                                              # (past the 45 degree stern chamfers)
    (25.4, HW, -5.8, 7.9, 3.4, 1.6, 1.6),
    (27.4, HM - 0.6, -5.6, 8.6, 3.2, 1.9, 1.6),                                       # (the step out to the superstructure)
    (31.0, HM, -5.4, 9.3, 3.4, 2.6, 1.6), (35.1, HM, -5.2, 10.2, 3.4, 3.5, 1.6), (46.1, HM, -5.0, 12.4, 3.4, 5.7, 1.6),
    (56.0, HM, -5.0, 14.4, 3.4, 7.7, 1.6), (64.6, HM - 0.4, -5.0, 15.4, 3.4, 8.7, 1.6), (66.4, 9.4, -4.8, 15.4, 3.2, 8.7, 1.6),
    (69.3, 7.6, -4.2, 13.4, 3.0, 6.7, 1.8)]                                           # (the nose, under its red cap)
KNUCKLE = 6.7                                                                          # (the superstructure's knuckle: the side's top)            # (the nose, under its red cap)


def section(s, hw, zb, zt, cw, ch, cb):
    """a section: its sides; its top corners, cw wide and ch high, nearly straight slopes with a little round to them
    (a superellipse); its bottom edges rounded (cb); always the same number of points"""
    def corner(cx, cz, rx, rz, q, n, e):
        out = []
        for k in range(n + 1):
            a = (q + k / n) * math.pi / 2
            c, sn = math.cos(a), math.sin(a)
            out.append(P(s, cx + rx * math.copysign(abs(c) ** e, c), cz + rz * math.copysign(abs(sn) ** e, sn)))
        return out
    top_e = 1.45                                                                       # (2 a circle; toward 2 / 1 a straight slope)
    return (corner(hw - cw, zt - ch, cw, ch, 0, 4, top_e) + corner(-hw + cw, zt - ch, cw, ch, 1, 4, top_e)
            + corner(-hw + cb, zb + cb, cb, cb, 2, 2, 1.0) + corner(hw - cb, zb + cb, cb, cb, 3, 2, 1.0))


NSEC = len(section(0, 1, -1, 1, 0.3, 0.3, 0.2))


def slope_at(s, f, sx, lift=0.0):
    """a point on the superstructure's near (or far) slope, a share f of the way from the knuckle up to the deck's edge,
    and the slope's outward normal"""
    hw, zb, zt = hull_at(s)
    cw = next(sec[4] for sec in HULL_S if sec[0] >= s) if s <= HULL_S[-1][0] else HULL_S[-1][4]
    a, b = Vector((hw * sx, 0, KNUCKLE)), Vector(((hw - cw) * sx, 0, zt))
    pt = a.lerp(b, f)
    n = Vector(((zt - KNUCKLE) * sx, 0, cw)).normalized()
    return P(s, pt.x + n.x * lift, pt.z + n.z * lift), Vector((n.x, 0, n.z))


def hull_at(s):
    """the hull's (half width, bottom, top) at s"""
    for a, b in zip(HULL_S, HULL_S[1:]):
        if a[0] <= s <= b[0]:
            t = (s - a[0]) / max(1e-6, b[0] - a[0]); return tuple(a[i] + (b[i] - a[i]) * t for i in (1, 2, 3))
    return HULL_S[-1][1:4]


V, F = [], []
for sec in HULL_S: V += section(*sec)
for k in range(len(HULL_S) - 1):
    for i in range(NSEC):
        a, b = k * NSEC + i, k * NSEC + (i + 1) % NSEC
        F.append((a, b, b + NSEC, a + NSEC))
F.append(tuple(range(NSEC))); F.append(tuple(range(len(V) - 1, len(V) - 1 - NSEC, -1)))


def hull_mat(c, n):
    s = s_of(c)
    if s < 0.2 and n.y > 0.9: return DARK                                             # (behind the engine panel)
    if s < 2.6:                                                                      # (the stern chamfers: red at the corners, dark top)
        return RED if abs(n.x) > 0.35 and abs(n.z) < 0.6 else METAL
    if s > 64.0 and n.z > 0.3: return RED                                            # (the red cap on the nose's top)
    if s > 66.0 and c.z / K > 4: return RED                                          # (and its front)
    return HULL


solid(V, F, HULL, hull_mat, bevel=0.12, seg=2)

# ---------------------------------------------------------------- the stern: the engine panel, three pods of two nozzles
box(-0.3, 0.05, -3.4, 3.4, -7.8, 4.9, METAL, 0.2)
for zc in (2.9, -1.4, -5.7):
    oct8 = []
    for k in range(8):                                                                 # (a pod: a chamfered frame)
        a = math.pi / 8 + k * math.pi / 4
        oct8.append((3.2 * math.cos(a) / math.cos(math.pi / 8), 2.05 * math.sin(a) / math.cos(math.pi / 8)))
    prism([P(-0.3, x, zc + z) for x, z in oct8], (0, K * 0.45, 0), TRIM, None, 0.06)
    prism([P(-0.5, x * 0.9, zc + z * 0.86) for x, z in oct8], (0, K * 0.2, 0), DARK, None, 0.03)
    for x in (-1.5, 1.5):
        cylinder(P(-0.85, x, zc), P(-0.45, x, zc), 1.32, TRIM, 28, 0.06)             # (the bezel)
        cylinder(P(-0.9, x, zc), P(-0.6, x, zc), 1.02, METAL, 28)                    # (its inner ring)
        cylinder(P(-0.95, x, zc), P(-0.7, x, zc), 0.86, GLOW, 28)                    # (the glowing throat)
# the stern chamfers' detail: a dark slot on each red corner, a rail along the top chamfer
for sx in (1, -1):
    for z in (3.8, -2.2):
        prism([P(0.6, side_x(sx, 4.3), z), P(1.6, side_x(sx, 5.1), z), P(1.6, side_x(sx, 5.1), z + 1.6), P(0.6, side_x(sx, 4.3), z + 1.6)],
              (K * 0.1 * sx, -K * 0.1, 0), DARK, None, 0.03)

for sx in (1, -1):
    # ------------------------------------------------------------ the engine block's side: plates, hatches, sockets, vents
    xs = HW
    box(4.0, 24.6, side_x(sx, xs), side_x(sx, xs + 0.22), -6.4, 5.8, HULL, 0.12)
    box(4.0, 24.6, side_x(sx, xs), side_x(sx, xs + 0.12), 5.95, 6.25, TRIM, 0.04)
    box(6.5, 22.0, side_x(sx, xs), side_x(sx, xs + 0.12), -7.4, -6.8, TRIM, 0.04)
    frame(9.0, 16.5, -4.6, 3.4, xs + 0.22, sx)
    frame(17.5, 23.8, -2.0, 5.0, xs + 0.22, sx)
    for z in (4.2, 0.6, -3.4):                                                       # (the hatches by the stern)
        box(3.0, 4.6, side_x(sx, xs), side_x(sx, xs + 0.45), z, z + 2.0, TRIM, 0.08)
        box(3.2, 4.4, side_x(sx, xs + 0.3), side_x(sx, xs + 0.5), z + 0.25, z + 1.75, DARK, 0.04)
    for s, z in ((7.5, 6.5), (12.0, -6.0), (17.0, 5.2), (19.5, 1.3), (21.5, -5.4), (24.0, 6.5), (14.0, 3.9)):
        socket(s, z, xs + (0.22 if -6.4 < z < 5.8 else 0.0), sx)
    box(11.0, 12.6, side_x(sx, xs + 0.18), side_x(sx, xs + 0.34), -0.4, 0.3, DARK, 0.08)    # (an oval vent)
    for s in (22.2, 22.8):
        box(s, s + 0.25, side_x(sx, xs + 0.2), side_x(sx, xs + 0.32), 2.4, 4.4, DARK, 0.02)
    # ------------------------------------------------------------ the step: the superstructure's aft face, its corner trim
    box(25.4, 27.4, side_x(sx, HM - 0.8), side_x(sx, HM - 0.5), -5.2, 6.4, TRIM, 0.08)
    # ------------------------------------------------------------ the superstructure's side, in layers
    xm = HM
    box(27.4, 41.5, side_x(sx, xm), side_x(sx, xm + 0.3), -4.6, 6.4, HULL, 0.15)             # (the aft plate)
    box(29.0, 33.5, side_x(sx, xm + 0.3), side_x(sx, xm + 0.7), 1.0, 3.6, HULL, 0.1)        # (the notch: a plate stepped out)
    box(31.0, 32.6, side_x(sx, xm + 0.7), side_x(sx, xm + 0.85), 1.5, 3.2, DARK, 0.03)
    box(41.5, 50.5, side_x(sx, xm), side_x(sx, xm + 0.45), 0.0, 6.0, HULL, 0.15)            # (the porthole panel)
    for i in range(4):
        for z in (3.96, 1.9):
            socket(43.2 + i * 1.55, z, xm + 0.45, sx, 0.55)
    # (on the slope: a raised panel's outline, and the round sockets the picture shows there)
    for s0, s1 in ((44.0, 52.0), (53.0, 63.0)):
        q = [slope_at(s0, 0.28, sx, 0.08)[0], slope_at(s1, 0.28, sx, 0.08)[0], slope_at(s1, 0.78, sx, 0.08)[0], slope_at(s0, 0.78, sx, 0.08)[0]]
        prism(q, slope_at((s0 + s1) / 2, 0.5, sx)[1] * (0.12 * K), TRIM, None, 0.03)
    for s, f, r in ((48.5, 0.55, 0.62), (57.5, 0.5, 0.55), (36.0, 0.45, 0.45)):
        c, n = slope_at(s, f, sx, 0.05)
        cylinder(c, c + n * (0.2 * K), r, TRIM, 16, 0.04); cylinder(c + n * (0.05 * K), c + n * (0.26 * K), r * 0.62, DARK, 14)
    box(50.5, 64.6, side_x(sx, xm), side_x(sx, xm + 0.3), -4.4, 4.8, HULL, 0.15)            # (the fore plate)
    box(54.2, 64.8, side_x(sx, xm + 0.1), side_x(sx, xm + 0.55), 5.2, 6.65, RED, 0.12)       # (the red stripe: below the knuckle)
    q = [slope_at(54.2, 0.0, sx, 0.06)[0], slope_at(64.8, 0.0, sx, 0.06)[0], slope_at(64.8, 0.16, sx, 0.06)[0], slope_at(54.2, 0.16, sx, 0.06)[0]]
    prism(q, slope_at(59.5, 0.08, sx)[1] * (0.3 * K), RED, None, 0.06)                     # (and over it, up the slope)
    side_prism([(51.4, -1.4), (55.6, -1.8), (59.0, 2.9), (54.6, 3.3)], side_x(sx, xm + 0.3) if sx > 0 else -(xm + 0.65),
               side_x(sx, xm + 0.65) if sx > 0 else -(xm + 0.3), RED, None, 0.1)            # (the red wedge)
    box(62.3, 64.1, side_x(sx, xm + 0.3), side_x(sx, xm + 0.8), -1.7, 1.7, DARK, 0.12)       # (the light bar's housing)
    box(62.6, 63.8, side_x(sx, xm + 0.75), side_x(sx, xm + 0.95), -1.3, 1.3, GLOW, 0.05)
    box(59.4, 61.4, side_x(sx, xm + 0.3), side_x(sx, xm + 0.5), -0.9, -0.2, GLOW, 0.04)
    box(27.4, 64.6, side_x(sx, xm), side_x(sx, xm + 0.12), -5.2, -4.7, TRIM, 0.03)
    for s, z in ((36.0, 5.6), (38.5, -2.2)):
        socket(s, z, xm + 0.25 if z > 7 else xm + 0.3, sx, 0.62 if z > 7 else 0.4)
    # ------------------------------------------------------------ the bow: the wedge plates (drooping), red leading edges
    wx0, wx1 = HM - 2.2, HM
    WEDGE = [(58.0, -5.6), (65.5, 4.5), (92.1, -0.6), (87.8, -5.8)]
    side_prism(WEDGE, *sorted((side_x(sx, wx0), side_x(sx, wx1))), HULL, None, 0.18)
    side_prism([(90.4, -0.25), (92.3, -0.55), (88.0, -5.85), (86.2, -5.5)], *sorted((side_x(sx, wx0 - 0.1), side_x(sx, wx1 + 0.1))), RED, None, 0.08)
    # (inset lines: a long groove and a lower panel's outline)
    box(66.5, 86.0, *sorted((side_x(sx, wx1), side_x(sx, wx1 + 0.08))), 2.2, 2.4, DARK, 0.0)
    frame(66.0, 78.0, -3.6, -1.0, wx1, sx, 0.12, 0.08, DARK)
    # ------------------------------------------------------------ the underside's twin capsule lights
    for s, x, z in ((27.6, 4.6, -7.0), (46.0, 6.4, -7.4), (52.0, 6.4, -7.4), (58.0, 5.8, -7.2)):
        for ds in (0.0, 2.4):
            cylinder(P(s + ds, side_x(sx, x), z), P(s + ds + 2.0, side_x(sx, x), z), 0.62, METAL, 16, 0.08)
            cylinder(P(s + ds + 0.2, side_x(sx, x + 0.25), z), P(s + ds + 1.8, side_x(sx, x + 0.25), z), 0.48, GLOW, 16)
    # ------------------------------------------------------------ the fin: a dark root, a light blade, a red leading edge
    r0, r1 = P(29.4, side_x(sx, 7.0), -6.0), P(38.6, side_x(sx, 7.0), -6.8)
    t0, t1 = P(42.4, side_x(sx, 19.0), -11.2), P(45.3, side_x(sx, 19.0), -10.2)
    m0, m1 = r0.lerp(t0, 0.38), r1.lerp(t1, 0.38)
    nrm = (r1 - r0).cross(t0 - r0).normalized() * (0.55 * K)
    prism([r0, r1, m1, m0], nrm, METAL, None, 0.06)
    prism([m0, m1, t1, t0], nrm, HULL, None, 0.06)
    lip = nrm * -0.3
    back = (r0 - r1).normalized() * (0.9 * K)
    prism([r1 + lip, t1 + lip, t1 + back + lip, r1 + back + lip], nrm * 1.6, RED, None, 0.04)
    box(28.6, 39.4, side_x(sx, 5.6), side_x(sx, 7.8), -6.8, -5.0, METAL, 0.2)               # (its housing)

# ---------------------------------------------------------------- the bow's middle: the upper blade, the pod, lower blade, keel
UB = (66.1, 9.7, 87.0, 5.0)                                                               # (the upper prongs: root s, z; tip s, z)
for sx in (1, -1):
    # (a prong on each side, 4 m wide, its tip toward the ship's middle line; it slopes from its root down to its tip:
    # plan_prism adds dz*s, so its base is shifted back by the root's s)
    plan_prism([(UB[0], side_x(sx, HM)), (UB[2], side_x(sx, HM - 1.0)), (UB[2], side_x(sx, HM - 1.8)), (UB[0] + 4.0, side_x(sx, HM - 4.2)),
                (UB[0], side_x(sx, HM - 4.2))], UB[1], UB[1] + 0.6, HULL,
               lambda c, n: RED if 77.5 < s_of(c) < 80.5 or s_of(c) > 84.4 else HULL, 0.08, dz=-(UB[1] - UB[3]) / (UB[2] - UB[0]))
    PARTS[-1].location.z += K * ((UB[1] - UB[3]) / (UB[2] - UB[0]) * UB[0])
side_prism([(63.5, 2.6), (63.5, 7.6), (85.6, 4.6), (87.0, 3.8), (87.0, 1.8)], -6.6, 6.6, HULL, None, 0.4)      # (the pod)
box(64.0, 85.5, -6.7, 6.7, 3.0, 3.25, DARK, 0.0)                                                                   # (its seam)
LB = (66.0, -7.4, 86.0, -9.6)                                                             # (the lower prongs: root s, z; tip s, z)
for sx in (1, -1):
    plan_prism([(LB[0], side_x(sx, HM - 0.6)), (LB[2], side_x(sx, HM - 1.4)), (LB[2], side_x(sx, HM - 2.2)), (LB[0] + 5.0, side_x(sx, HM - 4.6)),
                (LB[0], side_x(sx, HM - 4.6))], LB[1], LB[1] + 0.55, HULL, None, 0.08, dz=-(LB[1] - LB[3]) / (LB[2] - LB[0]))
    PARTS[-1].location.z += K * ((LB[1] - LB[3]) / (LB[2] - LB[0]) * LB[0])
box(60.0, 83.0, -7.2, 7.2, -8.2, 2.0, METAL, 0.2)                                                                  # (the keel)
for z in (-5.0, -3.0, -1.0, 0.9):
    cylinder(P(64.0, -7.4, z), P(83.0, -7.4, z), 0.3, TRIM, 10)
    cylinder(P(64.0, 7.4, z), P(83.0, 7.4, z), 0.3, TRIM, 10)

# ---------------------------------------------------------------- the underside's machinery
box(26.5, 64.0, -7.6, 7.6, -7.6, -4.8, METAL, 0.25)
for s0 in range(28, 62, 5):
    box(s0, s0 + 3.0, -5.6, 5.6, -8.0, -7.2, METAL, 0.12)
box(3.0, 21.0, -3.4, 3.4, -9.4, -8.7, METAL, 0.15)                                                                 # (under the engine block)
for x in (-2.6, 0.0, 2.6):
    cylinder(P(3.5, x * 0.85, -9.4), P(20.5, x * 0.85, -9.4), 0.32, TRIM, 10)

# ---------------------------------------------------------------- the deck: framed dark plates, rails, the spine and its pipes
def deck_plate(s0, s1, x0, x1, zf):
    """a dark plate in a raised trim frame, on the deck at height zf(s)"""
    a, b = zf(s0), zf(s1)
    side_prism([(s0, a - 0.05), (s1, b - 0.05), (s1, b + 0.25), (s0, a + 0.25)], x0, x1, TRIM, None, 0.05)
    side_prism([(s0 + 0.25, a + 0.2), (s1 - 0.25, b + 0.2), (s1 - 0.25, b + 0.34), (s0 + 0.25, a + 0.34)], x0 + 0.25, x1 - 0.25, DECK, None, 0.03)


top_aft = lambda s: 7.9
top_mid = lambda s: hull_at(s)[2]
for s0, s1 in ((3.5, 9.0), (10.0, 15.5), (16.5, 22.0)):
    for sx in (1, -1):
        deck_plate(s0, s1, *sorted((side_x(sx, 0.4), side_x(sx, 1.9))), top_aft)
for s0, s1 in ((28.5, 34.0), (44.5, 50.0), (51.0, 56.0), (57.0, 60.5)):
    for sx in (1, -1):
        for x0, x1 in ((1.0, 3.3), (3.7, 6.3)):
            deck_plate(s0, s1, *sorted((side_x(sx, x0), side_x(sx, x1))), top_mid)
for sx in (1, -1):                                                                   # (rails along the deck's edges)
    box(3.0, 25.0, side_x(sx, 2.0), side_x(sx, 2.15), 7.9, 8.25, TRIM, 0.04)
    side_prism([(27.5, top_mid(27.5)), (60.5, top_mid(60.5)), (60.5, top_mid(60.5) + 0.45), (27.5, top_mid(27.5) + 0.45)],
               *sorted((side_x(sx, 6.7), side_x(sx, 6.92))), TRIM, None, 0.04)
box(2.5, 26.0, -1.3, 1.3, 7.85, 8.45, METAL, 0.12)                                               # (the spine, low on the deck)
side_prism([(26.0, 7.85), (44.0, top_mid(44.0)), (44.0, top_mid(44.0) + 0.8), (26.0, 8.45)], -1.6, 1.6, METAL, None, 0.12)
for x in (-0.85, 0.0, 0.85):                                                         # (its pipe runs)
    cylinder(P(2.8, x, 8.55), P(25.5, x, 8.55), 0.16, TRIM, 10)
for _ in range(46):                                                                  # (greebles: low aft, taller by the head and the mount)
    s0 = rng.uniform(3, 58); d = rng.uniform(0.5, 1.8); w = rng.uniform(0.4, 1.4)
    h = rng.uniform(0.15, 0.45) if s0 < 22 else rng.uniform(0.25, 1.0)
    zt = 8.45 if s0 < 26 else top_mid(s0 + d) + 0.8
    x0 = rng.uniform(-1.6, 1.6 - w) if rng.random() < 0.6 or s0 < 26 else rng.choice([-1, 1]) * rng.uniform(1.8, 2.6)
    box(s0, s0 + d, x0, x0 + w, zt - 0.1, zt + h, rng.choice([TRIM, METAL, METAL, DECK, DARK]), 0.04)

# ---------------------------------------------------------------- the sensor head (its window aft) and the barrels' mount
deck31 = top_mid(31.0)
deck31 = top_mid(31.0)
box(31.2, 35.4, -1.5, 1.5, deck31 - 0.3, 12.5, METAL, 0.2)                                        # (the neck)
cylinder(P(32.0, -1.8, 11.9), P(32.0, 1.8, 11.9), 0.45, TRIM, 14)
box(30.2, 36.0, -2.4, 2.4, 12.3, 16.3, HULL, 0.8, seg=3)                                          # (the head)
box(29.9, 30.6, -1.95, 1.95, 12.8, 15.8, DARK, 0.25)                                              # (the window's frame)
box(29.75, 30.1, -1.55, 1.55, 13.2, 15.4, WINDOW, 0.15)
for x in (-2.45, 2.45):
    box(32.2, 35.2, x - 0.08, x + 0.08, 13.1, 15.5, DARK, 0.02)                                    # (its side vents)
box(31.4, 34.8, -1.2, 1.2, 16.2, 16.6, TRIM, 0.08)
deck41 = top_mid(41.1)
box(38.8, 43.6, -1.9, 1.9, deck41 - 0.2, 14.6, METAL, 0.25)                                       # (the barrels' mount)
box(39.6, 42.8, -1.5, 1.5, 14.6, 16.0, TRIM, 0.2)
for x, tip in ((-1.0, (41.0, 21.5)), (0.0, (43.9, 19.9)), (1.0, (46.9, 20.1))):
    base = P(41.1, x, 16.3); end = P(tip[0], x, tip[1])
    d = (end - base).normalized()
    cylinder(base, base + d * (K * 1.6), 0.42, METAL, 14, 0.05)                                  # (the sleeve)
    cylinder(base, end, 0.2, TRIM, 12)
    cylinder(end - d * (K * 0.7), end, 0.28, METAL, 12)                                          # (the muzzle)

# ---------------------------------------------------------------- one mesh: the modifiers applied, UVs projected, joined
dg = bpy.context.evaluated_depsgraph_get()
for ob in PARTS:
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data; ob.modifiers.clear(); ob.data = me; bpy.data.meshes.remove(old)
    if ob.location.length > 0:
        me.transform(Matrix.Translation(ob.location)); ob.location = (0, 0, 0)
for ob in PARTS:
    me = ob.data
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            u, v = {0: (co.y, co.z), 1: (co.x, co.z), 2: (co.x, co.y)}[ax]
            uv.data[li].uv = (u / TILE, v / TILE)
    for p in me.polygons: p.use_smooth = False
for ob in PARTS: ob.select_set(True)
bpy.context.view_layer.objects.active = PARTS[0]
bpy.ops.object.join()
ship = bpy.context.view_layer.objects.active
ship.name = ship.data.name = "Frigate"
tris = sum(len(p.vertices) - 2 for p in ship.data.polygons)
lo = Vector([min(v.co[i] for v in ship.data.vertices) for i in range(3)])
hi = Vector([max(v.co[i] for v in ship.data.vertices) for i in range(3)])
print("FRIGATE", "triangles", tris, "box", [round(v, 2) for v in lo], [round(v, 2) for v in hi])


# ---------------------------------------------------------------- pictures: views, and her from the fitted camera
def workbench(w, h):
    SC.render.engine = "BLENDER_WORKBENCH"
    SC.display.shading.light = "STUDIO"; SC.display.shading.color_type = "TEXTURE"
    SC.display.shading.show_cavity = True; SC.display.shading.cavity_type = "BOTH"
    SC.render.resolution_x, SC.render.resolution_y = w, h
    if not SC.world: SC.world = bpy.data.worlds.new("W")


if PREVIEW:
    os.makedirs(PREVIEW, exist_ok=True)
    workbench(1400, 900)
    cd = bpy.data.cameras.new("Cam"); cd.lens = 35
    cam = bpy.data.objects.new("Cam", cd); COL.objects.link(cam); SC.camera = cam
    centre = Vector((0, 0, 4.0))
    for tag, loc in (("side", Vector((-150, 0, 6))), ("top", Vector((-30, 0, 150))), ("stern", Vector((-60, 120, 30))),
                     ("bow", Vector((-90, -130, 40))), ("below", Vector((-90, -40, -80))), ("threeq", Vector((-110, 70, 60)))):
        cam.location = loc; cam.rotation_euler = (centre - loc).to_track_quat("-Z", "Y").to_euler()
        SC.render.filepath = os.path.join(PREVIEW, tag + ".png")
        bpy.ops.render.render(write_still=True)
if OVERLAY:
    fit = json.load(open(OVERLAY[0])); odir = OVERLAY[1]; os.makedirs(odir, exist_ok=True)
    cm = fit["camera"]
    Cf = Vector(cm["C"]); R = Matrix(cm["R"])                                         # (world to camera, OpenCV axes)
    C = Vector((K * Cf.x, K * Cf.y + 55.0 * (1 - K), K * Cf.z))                         # (the fit's frame to hers)
    workbench(1632, 1216)
    SC.render.film_transparent = True
    cd = bpy.data.cameras.new("FitCam"); cd.sensor_fit = "HORIZONTAL"; cd.sensor_width = 36.0
    cd.lens = cm["f"] * 36.0 / 1632.0; cd.clip_end = 1e5; cd.clip_start = 1.0
    cam = bpy.data.objects.new("FitCam", cd); COL.objects.link(cam); SC.camera = cam
    cam.matrix_world = Matrix.Translation(C) @ (R.transposed() @ Matrix.Diagonal((1, -1, -1))).to_4x4()
    SC.render.filepath = os.path.join(odir, "fitcam.png")
    bpy.ops.render.render(write_still=True)
    SC.render.film_transparent = False

os.makedirs(os.path.dirname(GLB), exist_ok=True)
for ob in list(SC.objects):
    if ob.type != "MESH": bpy.data.objects.remove(ob)
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", export_yup=True, export_apply=True, export_materials="EXPORT")
print("FRIGATE DONE", GLB, os.path.getsize(GLB))
BLEND = os.path.join(os.path.dirname(TEX), os.path.splitext(os.path.basename(GLB))[0] + ".blend")
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("FRIGATE BLEND", BLEND)
