"""Frigate 4b after its reference picture (I:\\game assets\\3d unity samples\\frigate4b.jpg, the user's of 2026-11-11), built
in Blender from script. The picture is a side view, so its profile is measured straight off it: every station and height
below is the picture's pixel (x along her, y down), read from the ship's silhouette (separated from the grey backdrop by
colour) and from gridded crops; 1274 px from the nose's tip to the engines' ends are her 110 m (8.63 cm a pixel). A side
view shows no beam: her cross-sections are taken as superellipses 0.85 as wide as they are high (the one assumption), and
her engines as a stacked pair on each side.
Her parts: the blue upper hull lofted through its stations, the green nose cone, the raised forward hump with its canopy
and antenna, the white lower hull, the blue keel bulge; the two engine pairs (dark intakes, green and white rings, nozzles)
on their pylons; the swept dorsal fin and the two canted ventral fins; a twin-barrel turret on each side; the banded gun
pods under the nose; the windows; the "TX223" hull number on both sides; the pods and the missile underneath.
Metres: 110 m long, bow toward -Y (glTF +Z), up +Z; the picture's side is +X. With --overlay <dir> it renders her side-on
(orthographic, the picture's frame) for the check against the picture's silhouette.
Blender: blender -b -P frigate4b_build.py -- <tex dir> <out.glb> [--preview <dir>] [--overlay <dir>]"""
import bpy, bmesh, json, math, os, sys
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
TEX, GLB = os.path.abspath(argv[0]), os.path.abspath(argv[1])
PREVIEW = os.path.abspath(argv[argv.index("--preview") + 1]) if "--preview" in argv else None
OVERLAY = os.path.abspath(argv[argv.index("--overlay") + 1]) if "--overlay" in argv else None
PAL = json.load(open(os.path.join(TEX, "palette.json")))
bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene
COL = SC.collection
L = 110.0
PX0, PX1, PY0 = 65.0, 1339.0, 690.0                                                  # (the nose's tip, the engines' ends, the hull's waterline)
KP = L / (PX1 - PX0)                                                                  # (metres a pixel)
TILE = 16.0
WIDTH = 0.85                                                                          # (beam / height: the assumption)


def Q(px, xpx, py):
    """a point from the picture: px along her (the nose at 65), xpx across her (pixels, +X the picture's side), py up-down"""
    return Vector((xpx * KP, L / 2 - (PX1 - px) * KP, (PY0 - py) * KP))


# ---------------------------------------------------------------- materials
def lin(c):
    f = lambda v: (v / 255) / 12.92 if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]), 1.0)


def material(name, tex=None, color=None, rough=0.45, metal=0.25, glow=0.0, alpha=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Roughness"].default_value, b.inputs["Metallic"].default_value = rough, metal
    if tex:
        n = m.node_tree.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(os.path.join(TEX, tex), check_existing=True)
        m.node_tree.links.new(n.outputs["Color"], b.inputs["Base Color"])
        if alpha:
            m.node_tree.links.new(n.outputs["Alpha"], b.inputs["Alpha"])
            if hasattr(m, "surface_render_method"): m.surface_render_method = "BLENDED"
    else:
        col = lin(PAL[color] if isinstance(color, str) else color)
        b.inputs["Base Color"].default_value = col; m.diffuse_color = col
        if glow: b.inputs["Emission Color"].default_value = col; b.inputs["Emission Strength"].default_value = glow
    return m


MATS = [material("Blue", tex="blue.png"), material("White", tex="white.png"), material("Green", color="green", rough=0.4),
        material("Machinery", tex="metal.png", rough=0.5, metal=0.6), material("Grey", color="grey", rough=0.45, metal=0.5),
        material("Glass", color="glass", rough=0.1, metal=0.1, glow=0.4), material("Window", color="window", rough=0.3),
        material("Fin", color="fin", rough=0.45), material("Gun", color="gun", rough=0.4, metal=0.7),
        material("HullNumber", tex="tx223.png", rough=0.5, metal=0.0, alpha=True)]
BLUE, WHITE, GREEN, METAL, GREY, GLASS, WIN, FIN, GUN, DECAL = range(10)
PARTS = []


def mesh_obj(V, F, mat, mfn=None, bevel=0.0, seg=2, uv=None, closed=True):
    me = bpy.data.meshes.new("part")
    me.from_pydata([tuple(v) for v in V], [], [tuple(f) for f in F]); me.update()
    bm = bmesh.new(); bm.from_mesh(me)
    if closed: bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces: f.material_index = mfn(f.calc_center_median(), f.normal) if mfn else mat
    bm.to_mesh(me); bm.free()
    for m in MATS: me.materials.append(m)
    if uv is not None:
        lay = me.uv_layers.new(name="UVMap")
        for lp in me.loops: lay.data[lp.index].uv = uv[lp.vertex_index]
    ob = bpy.data.objects.new("part", me); COL.objects.link(ob)
    if bevel > 0:
        b = ob.modifiers.new("Bevel", "BEVEL"); b.width = bevel; b.segments = seg; b.limit_method = "ANGLE"
        b.angle_limit = math.radians(30); b.use_clamp_overlap = True
    ob["own_uv"] = uv is not None
    PARTS.append(ob)
    return ob


def prism(poly, offset, mat, mfn=None, bevel=0.0):
    n = len(poly)
    V = [Vector(p) for p in poly] + [Vector(p) + Vector(offset) for p in poly]
    F = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return mesh_obj(V, F, mat, mfn, bevel)


def cylinder(c0, c1, r, mat, seg=24, bevel=0.0):
    """between two points; r in pixels"""
    c0, c1 = Vector(c0), Vector(c1)
    ax = (c1 - c0).normalized(); a = ax.orthogonal().normalized(); b = ax.cross(a)
    V = [c + (a * math.cos(2 * math.pi * i / seg) + b * math.sin(2 * math.pi * i / seg)) * (r * KP) for c in (c0, c1) for i in range(seg)]
    F = [tuple(range(seg)), tuple(range(2 * seg - 1, seg - 1, -1))] + [(i, (i + 1) % seg, seg + (i + 1) % seg, seg + i) for i in range(seg)]
    return mesh_obj(V, F, mat, None, bevel, 1)


def pod_x(px0, px1, py, xpx, r, mat, bevel=0.0, seg=28):
    """a cylinder along her length at the picture's height py, xpx across"""
    return cylinder(Q(px0, xpx, py), Q(px1, xpx, py), r, mat, seg, bevel)


def box(px0, px1, x0, x1, py0, py1, mat, bevel=0.15):
    """in pixels: along px0..px1, across x0..x1, from py0 (top) to py1"""
    x0, x1 = min(x0, x1), max(x0, x1)
    poly = [Q(px0, x0, py1), Q(px1, x0, py1), Q(px1, x0, py0), Q(px0, x0, py0)]
    return prism(poly, ((x1 - x0) * KP, 0, 0), mat, None, bevel)


# ---------------------------------------------------------------- lofts: superellipse sections through stations
NS = 32


def sec(px, top, bot, hw, e=2.6, xc=0.0):
    zc, hh = (top + bot) / 2, (bot - top) / 2
    out = []
    for i in range(NS):
        a = 2 * math.pi * i / NS
        c, s = math.cos(a), math.sin(a)
        out.append(Q(px, xc + hw * math.copysign(abs(c) ** (2 / e), c), zc - hh * math.copysign(abs(s) ** (2 / e), s)))
    return out


def loft(stations, mat, mfn=None, e=2.6, width=WIDTH, xc=0.0, bevel=0.0, tip_front=None):
    """stations: (px, top, bottom[, half width]) in pixels; the ends closed (tip_front: the nose's tip point)"""
    V, F = [], []
    for st in stations:
        px, top, bot = st[:3]
        hw = st[3] if len(st) > 3 else width * (bot - top) / 2
        V += sec(px, top, bot, hw, e, xc)
    n = len(stations)
    for k in range(n - 1):
        for i in range(NS):
            a, b = k * NS + i, k * NS + (i + 1) % NS
            F.append((a, b, b + NS, a + NS))
    if tip_front is not None:
        t = len(V); V.append(tip_front)
        for i in range(NS): F.append((i, (i + 1) % NS, t))
    else:
        F.append(tuple(range(NS)))
    F.append(tuple(range(n * NS - 1, (n - 1) * NS - 1, -1)))
    return mesh_obj(V, F, mat, mfn, bevel)


# ---------------------------------------------------------------- the blue upper hull (its top line from the silhouette)
HULL = [(190, 642, 700), (210, 629, 702), (260, 615, 702), (310, 604, 702), (360, 593, 702), (410, 585, 702), (460, 575, 702),
        (500, 567, 702), (560, 561, 702), (640, 558, 702), (735, 558, 702), (810, 560, 702), (860, 559, 702), (910, 553, 702),
        (960, 549, 702), (1010, 546, 702), (1100, 543, 704), (1180, 548, 705), (1240, 566, 705)]
loft(HULL, BLUE, e=2.4)


def hull_at(px):
    for a, b in zip(HULL, HULL[1:]):
        if a[0] <= px <= b[0]:
            t = (px - a[0]) / (b[0] - a[0]); return a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t
    return HULL[-1][1:3]


def surface_x(px, py, e=2.4):
    """how far across the blue hull's side is at the picture's (px, py), pixels"""
    top, bot = hull_at(px)
    zc, hh = (top + bot) / 2, (bot - top) / 2
    hw = WIDTH * hh
    v = min(1.0, abs(py - zc) / hh)
    return hw * max(0.0, 1 - v ** e) ** (1 / e)


# the green nose cone (its axis dips to the tip) and a dark ring at its base
loft([(190, 642, 700), (160, 648, 697), (125, 657, 695), (95, 668, 692), (75, 679, 691)], GREEN, e=2.0, tip_front=Q(65, 0, 688))
loft([(186, 640, 702), (194, 640, 702)], METAL, e=2.4, width=WIDTH * 1.03)
loft([(118, 692, 700, 10), (150, 690, 708, 18), (200, 690, 712, 24)], GREY, e=2.4)            # (the grey chin under the cone)
# the raised hump forward of the turret, its canopy and antenna
loft([(482, 600, 600 + 1, 20), (500, 566, 600, 30), (525, 551, 600, 36), (560, 542, 600, 40), (725, 539, 600, 40), (737, 556, 600, 34)], BLUE, e=3.0)
c = Q(680, 0, 547)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=1.0)
dome = [v.co.copy() for v in bm.verts]; faces = [[v.index for v in f.verts] for f in bm.faces]; bm.free()
mesh_obj([c + Vector((v.x * 22 * KP, v.y * 44 * KP, max(v.z, -0.2) * 15 * KP)) for v in dome], faces, GLASS)
cylinder(Q(690, 0, 536), Q(775, 0, 497), 1.6, GREEN, 8)
cylinder(Q(752, -10, 501), Q(752, 10, 501), 1.2, GREEN, 6)
cylinder(Q(650, 0, 538), Q(650, 0, 519), 1.4, GREY, 6)
for px in (1030, 1255):                                                              # (small fairings on her spine)
    box(px, px + 18, -8, 8, hull_at(px)[0] - 12, hull_at(px)[0] + 4, BLUE, 0.3)

# ---------------------------------------------------------------- the white lower hull and the blue keel bulge
blue_hw = lambda px: WIDTH * (hull_at(px)[1] - hull_at(px)[0]) / 2
WHITE_S = [(172, 692, 712), (200, 688, 738), (240, 688, 752), (300, 688, 755), (460, 688, 757), (560, 688, 763), (600, 688, 765),
           (840, 688, 765), (880, 688, 757), (1000, 688, 754), (1100, 688, 758), (1136, 690, 752)]
loft([(px, t, b, 0.9 * blue_hw(px) if px > 200 else 26) for px, t, b in WHITE_S], WHITE, e=3.2)
loft([(592, 752, 760, 14), (620, 752, 798, 30), (790, 752, 808, 32), (835, 752, 772, 20)], BLUE, e=2.2)
for px in range(320, 1100, 120):                                                     # (the white hull's panel breaks)
    box(px, px + 3, -0.9 * blue_hw(px) - 1, 0.9 * blue_hw(px) + 1, 704, 754, METAL, 0.0)

# ---------------------------------------------------------------- the engines: a stacked pair on each side, on pylons
ENG = [(613, 46, 1106, 1338, [(1165, 1200, GREEN), (1200, 1214, WHITE)]), (697, 42, 1110, 1335, [(1160, 1180, GREEN), (1180, 1194, WHITE), (1210, 1230, GREEN)])]
for sx in (1, -1):
    for py, r, a, b, bands in ENG:
        xe = sx * (blue_hw(1180) + 10)
        pod_x(1150, b - 12, py, xe, r, BLUE, 0.2)
        pod_x(a, 1150, py, xe, r * 1.02, METAL, 0.15)                               # (the intake's lip)
        pod_x(a - 2, a + 10, py, xe, r * 0.8, WIN)                                    # (the intake's dark mouth)
        pod_x(a + 4, a + 40, py, xe, r * 0.32, GREY)                                  # (its centre cone)
        for p0, p1, m in bands:
            pod_x(p0, p1, py, xe, r * 1.035, m)
        pod_x(b - 14, b, py, xe, r * 0.88, METAL, 0.1)                                # (the nozzle)
        pod_x(b - 4, b + 1, py, xe, r * 0.66, WIN)
    # (the pylons joining them to the hull)
    for py0, py1 in ((598, 628), (684, 712)):
        box(1150, 1300, sx * blue_hw(1240) * 0.6, sx * (blue_hw(1180) + 10), py0, py1, BLUE, 0.3)
    box(1128, 1312, sx * 10, sx * (blue_hw(1180) + 22), 720, 752, BLUE, 0.6)           # (the fairing under the lower engines)
    box(1135, 1310, sx * (blue_hw(1180) + 10 - 20), sx * (blue_hw(1180) + 10 + 20), 640, 670, METAL, 0.2)

# ---------------------------------------------------------------- the fins: the dorsal one swept back, two ventral ones canted
fin_poly = lambda pts, x: [Q(px, x, py) for px, py in pts]
prism(fin_poly([(1086, 548), (1200, 460), (1221, 455), (1192, 549)], -4), (8 * KP, 0, 0), FIN, None, 0.12)
for sx in (1, -1):
    root = [(1148, 756), (1208, 752), (1222, 828), (1186, 830)]
    pts = []
    for px, py in root:
        drop = (py - 752) * KP                                                          # (canted out 25 degrees as it falls)
        p = Q(px, sx * 34, 752); p.z -= drop * math.cos(math.radians(25)); p.x += sx * drop * math.sin(math.radians(25))
        pts.append(p)
    # (its thickness across the fin's plane on both sides: the fin falls along (sx sin 25, 0, -cos 25), so across it is
    # (cos 25, 0, sx sin 25) (PR #52's review: the -X fin was thickened at 40 degrees to its plane))
    prism(pts, Vector((math.cos(math.radians(25)), 0, sx * math.sin(math.radians(25)))) * (0.6 * sx), WHITE, None, 0.1)

# ---------------------------------------------------------------- a twin-barrel turret on each side
for sx in (1, -1):
    xs = surface_x(760, 628)
    box(712, 812, sx * (xs - 8), sx * (xs + 26), 590, 666, GREY, 1.1)                 # (the housing, rounded)
    box(722, 800, sx * (xs + 26), sx * (xs + 30), 600, 656, METAL, 0.2)
    cylinder(Q(752, sx * (xs + 26), 616), Q(752, sx * (xs + 33), 616), 22, GREY, 24, 0.2)   # (the drum on its face)
    cylinder(Q(752, sx * (xs + 33), 616), Q(752, sx * (xs + 35), 616), 14, METAL, 20)
    cylinder(Q(800, sx * (xs + 26), 628), Q(800, sx * (xs + 33), 628), 11, GREY, 20, 0.1)   # (its trunnion)
    box(718, 798, sx * (xs - 6), sx * (xs + 20), 664, 676, METAL, 0.2)                # (its base)
    for px in (730, 760, 790):
        box(px, px + 8, sx * (xs + 18), sx * (xs + 28), 662, 676, GREY, 0.1)
    for py in (612, 637):
        pod_x(570, 716, py, sx * (xs + 14), 4.6, GUN)
        pod_x(676, 716, py, sx * (xs + 14), 8.5, GREY, 0.1)                          # (the sleeves)
        pod_x(566, 590, py, sx * (xs + 14), 6.6, GUN)                                # (the muzzle brakes)
    box(700, 714, sx * (xs - 2), sx * (xs + 24), 596, 662, METAL, 0.2)              # (the mantlet)

# ---------------------------------------------------------------- the banded gun pods under the nose
for sx in (1, -1):
    x = sx * 26
    pod_x(170, 340, 736, x, 24, WHITE, 0.25)
    pod_x(148, 172, 736, x, 10, GUN)
    pod_x(160, 174, 736, x, 15, METAL)
    for p0, p1 in ((200, 216), (256, 272), (302, 314)):
        pod_x(p0, p1, 736, x, 24.8, METAL)
    box(220, 320, x - sx * 6, x - sx * 2, 712, 720, METAL, 0.05)

# ---------------------------------------------------------------- windows and the hull number, on the hull's surface
WINDOWS = [(392, 632, 8, 12), (408, 630, 8, 12), (428, 627, 9, 12), (270, 641, 60, 6), (705, 569, 14, 9), (867, 584, 18, 11),
           (938, 579, 16, 10), (980, 576, 12, 9), (520, 600, 30, 5)]
for sx in (1, -1):
    for px, py, w, h in WINDOWS:
        xs = surface_x(px + w / 2, py)
        box(px, px + w, sx * (xs - 2), sx * (xs + 0.8), py - h / 2, py + h / 2, WIN, 0.02)
for sx in (1, -1):
    V, UV, F = [], [], []
    nu, nv = 24, 4
    for j in range(nv + 1):
        py = 618 + (665 - 618) * j / nv
        for i in range(nu + 1):
            px = 820 + (1045 - 820) * i / nu
            V.append(Q(px, sx * (surface_x(px, py) + 0.7), py))
            UV.append((i / nu if sx > 0 else 1 - i / nu, 1 - j / nv))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            # (wound to face out of the hull: Q's px runs +Y and its py -Z, so (a, a+1, ...) faced -X on the +X side, inward on both
            # (PR #52's review); an open sheet's normals are not recalculated)
            F.append((a, a + nu + 1, a + nu + 2, a + 1) if sx > 0 else (a, a + 1, a + nu + 2, a + nu + 1))
    mesh_obj(V, F, DECAL, uv=UV, closed=False)

# ---------------------------------------------------------------- underneath: two pods, the missile, small fins
box(726, 750, -4, 4, 790, 800, METAL, 0.1); pod_x(712, 766, 815, 0, 12, GREY, 0.1)
box(822, 870, -7, 7, 786, 806, GREY, 0.2)
box(1040, 1058, -3, 3, 758, 812, METAL, 0.1)
pod_x(1004, 1096, 820, 0, 7, GREY); cylinder(Q(995, 0, 820), Q(1004, 0, 820), 3, GREY, 12)
for a in (0, 90, 180, 270):
    d = Vector((math.cos(math.radians(a)), 0, math.sin(math.radians(a))))
    prism([Q(1080, 0, 820), Q(1098, 0, 820), Q(1098, 0, 820) + d * (12 * KP), Q(1090, 0, 820) + d * (12 * KP)], Vector((0, 0, 0.0)) + Vector((-d.z, 0, d.x)) * 0.1, GREY)
pod_x(1268, 1302, 566, 0, 5, GREY)                                                   # (a sensor on her stern)

# ---------------------------------------------------------------- one mesh: modifiers applied, UVs projected, joined
dg = bpy.context.evaluated_depsgraph_get()
for ob in PARTS:
    own = ob["own_uv"]
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data; ob.modifiers.clear(); ob.data = me; bpy.data.meshes.remove(old)
    if not own:
        uv = me.uv_layers[0] if me.uv_layers else me.uv_layers.new(name="UVMap")
        for poly in me.polygons:
            n = poly.normal; ax = max(range(3), key=lambda i: abs(n[i]))
            for li in poly.loop_indices:
                co = me.vertices[me.loops[li].vertex_index].co
                u, v = {0: (co.y, co.z), 1: (co.x, co.z), 2: (co.x, co.y)}[ax]
                uv.data[li].uv = (u / TILE, v / TILE)
    for p in me.polygons: p.use_smooth = p.material_index in (BLUE, WHITE, GREEN, GLASS, FIN, GUN, GREY)
for ob in PARTS: ob.select_set(True)
bpy.context.view_layer.objects.active = PARTS[0]
bpy.ops.object.join()
ship = bpy.context.view_layer.objects.active
ship.name = ship.data.name = "Frigate4b"
# (smooth parts keep their hard edges: split where faces meet at more than 40 degrees)
mod = ship.modifiers.new("Split", "EDGE_SPLIT"); mod.split_angle = math.radians(40)
me = bpy.data.meshes.new_from_object(ship.evaluated_get(bpy.context.evaluated_depsgraph_get()))
old = ship.data; ship.modifiers.clear(); ship.data = me; bpy.data.meshes.remove(old)
tris = sum(len(p.vertices) - 2 for p in ship.data.polygons)
lo = Vector([min(v.co[i] for v in ship.data.vertices) for i in range(3)]); hi = Vector([max(v.co[i] for v in ship.data.vertices) for i in range(3)])
print("FRIGATE4B triangles", tris, "box", [round(v, 2) for v in lo], [round(v, 2) for v in hi])


def workbench(w, h):
    SC.render.engine = "BLENDER_WORKBENCH"
    SC.display.shading.light = "STUDIO"; SC.display.shading.color_type = "TEXTURE"
    SC.display.shading.show_cavity = True; SC.display.shading.cavity_type = "BOTH"
    SC.render.resolution_x, SC.render.resolution_y = w, h
    if not SC.world: SC.world = bpy.data.worlds.new("W")


if PREVIEW:
    os.makedirs(PREVIEW, exist_ok=True); workbench(1400, 900)
    cd = bpy.data.cameras.new("Cam"); cd.lens = 35
    cam = bpy.data.objects.new("Cam", cd); COL.objects.link(cam); SC.camera = cam
    centre = Vector((0, 0, 0.0))
    for tag, loc in (("side", Vector((150, 0, 4))), ("top", Vector((30, 0, 150))), ("bow", Vector((90, -120, 40))),
                     ("stern", Vector((70, 120, 35))), ("below", Vector((90, -40, -80))), ("farside", Vector((-120, 60, 40)))):
        cam.location = loc; cam.rotation_euler = (centre - loc).to_track_quat("-Z", "Y").to_euler()
        SC.render.filepath = os.path.join(PREVIEW, tag + ".png"); bpy.ops.render.render(write_still=True)
if OVERLAY:
    os.makedirs(OVERLAY, exist_ok=True); workbench(1408, 1408)
    SC.render.film_transparent = True
    cd = bpy.data.cameras.new("Side"); cd.type = "ORTHO"; cd.ortho_scale = 1408 * KP; cd.clip_end = 1000
    cam = bpy.data.objects.new("Side", cd); COL.objects.link(cam); SC.camera = cam
    cam.location = Q(704, 0, 704) + Vector((300, 0, 0))
    cam.rotation_euler = (Vector((-1, 0, 0))).to_track_quat("-Z", "Y").to_euler()
    SC.render.filepath = os.path.join(OVERLAY, "side_ortho.png"); bpy.ops.render.render(write_still=True)
    SC.render.film_transparent = False
for ob in list(SC.objects):
    if ob.type != "MESH": bpy.data.objects.remove(ob)
os.makedirs(os.path.dirname(GLB), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", export_yup=True, export_apply=True, export_materials="EXPORT")
print("FRIGATE4B DONE", GLB, os.path.getsize(GLB))
BLEND = os.path.join(os.path.dirname(TEX), os.path.splitext(os.path.basename(GLB))[0] + ".blend")
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("FRIGATE4B BLEND", BLEND)
