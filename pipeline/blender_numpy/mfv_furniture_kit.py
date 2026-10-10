"""Medieval furniture / household kit for castle_level interiors, built procedurally in cm (UE: front = +Y, base at z = 0).
Material SLOT NAMES carry the material (mapped in UE): Wood, Planks, Stone, Iron, Bark, Straw, Ember, Flame, Linen, WoolRed,
WoolGreen, WoolBlue, WoolBrown, Fur, Bread, Cheese, Apple, Clay, Wax, Stew, Dough, Plaster, Rope.
Blender: -b -P mfv_furniture_kit.py -- out_dir"""
import bpy, bmesh, sys, os, math, random, json
from mathutils import Vector, Matrix
OUT = sys.argv[sys.argv.index("--") + 1]; os.makedirs(OUT, exist_ok=True)
random.seed(11)
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene; s.unit_settings.system = 'METRIC'; s.unit_settings.scale_length = 0.01
def mat(name):
    return bpy.data.materials.get(name) or bpy.data.materials.new(name)
def finish(bm, name, material):
    """bmesh -> object with one material slot, box-projected UVs (1 UV per metre)"""
    uv = bm.loops.layers.uv.verify(); bm.normal_update()
    for f in bm.faces:
        n = f.normal; ax = max(range(3), key=lambda k: abs(n[k]))
        for l in f.loops:
            c = l.vert.co; u, v = [(c.y, c.z), (c.x, c.z), (c.x, c.y)][ax]; l[uv].uv = (u / 100.0, v / 100.0)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); me.materials.append(mat(material)); return ob
def box(sx, sy, sz, x=0, y=0, z=0, m="Wood", rot=(0, 0, 0), bevel=0.0):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    if bevel > 0: bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=1, affect='EDGES')
    R = Matrix.Rotation(math.radians(rot[0]), 4, 'X') @ Matrix.Rotation(math.radians(rot[1]), 4, 'Y') @ Matrix.Rotation(math.radians(rot[2]), 4, 'Z')
    bmesh.ops.transform(bm, matrix=Matrix.Translation((x, y, z + sz / 2)) @ R, verts=bm.verts)
    return finish(bm, "p", m)
def cyl(r, h, x=0, y=0, z=0, m="Wood", seg=16, r2=None, rot=(0, 0, 0)):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h)
    R = Matrix.Rotation(math.radians(rot[0]), 4, 'X') @ Matrix.Rotation(math.radians(rot[1]), 4, 'Y') @ Matrix.Rotation(math.radians(rot[2]), 4, 'Z')
    bmesh.ops.transform(bm, matrix=Matrix.Translation((x, y, z)) @ R @ Matrix.Translation((0, 0, h / 2)), verts=bm.verts)
    return finish(bm, "c", m)
def lathe(prof, m, seg=24, x=0, y=0, z=0, sx=1, sy=1, cap=True):
    """prof: [(radius, z), ...] bottom -> top, revolved around Z"""
    bm = bmesh.new(); rings = []
    for r, zz in prof:
        rings.append([bm.verts.new((x + r * sx * math.cos(2 * math.pi * k / seg), y + r * sy * math.sin(2 * math.pi * k / seg), z + zz)) for k in range(seg)])
    for a, b in zip(rings, rings[1:]):
        for k in range(seg): bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    if cap and prof[0][0] > 0.01: bm.faces.new(rings[0][::-1])
    return finish(bm, "l", m)
def sphere(r, x=0, y=0, z=0, m="Apple", sx=1, sy=1, sz=1, sub=2, noise=0.0):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    for v in bm.verts:
        v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz)) * (1 + random.uniform(-noise, noise))
    bmesh.ops.translate(bm, vec=(x, y, z), verts=bm.verts); return finish(bm, "s", m)
def rod(p0, p1, r, m="Wood", seg=8):
    """cylinder of radius r from point p0 to point p1"""
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=d.length)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bmesh.ops.transform(bm, matrix=Matrix.Translation((p0 + p1) / 2) @ q.to_matrix().to_4x4(), verts=bm.verts)
    return finish(bm, "r", m)
def flame(x, y, z, h=10, r=2.2):
    return lathe([(0.0, 0), (r * 0.8, h * 0.18), (r, h * 0.35), (r * 0.6, h * 0.7), (0.0, h)], "Flame", seg=10, x=x, y=y, z=z)
def export(name):
    obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs: o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]; bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active; ob.name = name
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, name + ".fbx"), use_selection=True, object_types={'MESH'}, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_NONE', mesh_smooth_type='FACE', path_mode='STRIP', bake_anim=False)
    me = ob.data; lo = [min(v.co[k] for v in me.vertices) for k in range(3)]; hi = [max(v.co[k] for v in me.vertices) for k in range(3)]
    KIT[name] = {"size": [round(hi[k] - lo[k], 1) for k in range(3)], "slots": [m.name for m in me.materials]}
    print("kit", name, KIT[name]["size"], KIT[name]["slots"])
KIT = {}
PROPS = {}
def prop(fn): PROPS[fn.__name__] = fn; return fn
# ---------------- bedroom ----------------
def bed(w, blanket):
    L = 205
    for sx in (-w / 2 + 4, w / 2 - 4):
        box(8, 8, 95, sx, L / 2 - 4, 0); box(8, 8, 55, sx, -L / 2 + 4, 0)              # posts (head at +y, against the wall)
        box(6, L - 8, 18, sx, 0, 24)                                                       # side rails
    box(w - 8, 5, 55, 0, L / 2 - 4, 35, bevel=0.6); box(w - 8, 5, 25, 0, -L / 2 + 4, 25)   # head / foot boards
    for k in range(5): box(w - 10, 10, 2.5, 0, -L / 2 + 25 + k * 40, 38)                  # slats
    box(w - 10, L - 14, 15, 0, 0, 40, m="Straw", bevel=4)                                  # straw mattress
    box(w - 6, L * 0.62, 5, 0, -L * 0.17, 54, m=blanket, bevel=1.5)                        # blanket
    for sx in (-1, 1): box(2, L * 0.62, 26, sx * (w / 2 - 1), -L * 0.17, 32, m=blanket)    # blanket drape
    for k in range(1 if w < 120 else 2):
        px = 0 if w < 120 else (-w / 4 + k * w / 2)
        sphere(1, px, L / 2 - 30, 62, m="Linen", sx=26, sy=17, sz=7, sub=2)               # pillow
@prop
def SM_Kit_BedSingle(): bed(95, "WoolRed")
@prop
def SM_Kit_BedSingleGreen(): bed(95, "WoolGreen")
@prop
def SM_Kit_BedDouble(): bed(150, "WoolBlue")
@prop
def SM_Kit_Wardrobe():
    box(110, 55, 190, 0, 0, 0, bevel=1.0)
    for sx in (-27, 27): box(50, 2, 160, sx, -28, 15)                                      # door panels
    for sx in (-6, 6): box(2.5, 3, 14, sx, -30.5, 95, m="Iron")
    box(116, 60, 8, 0, 0, 190, bevel=1.5)                                                  # cornice
@prop
def SM_Kit_Chest():
    box(90, 50, 45, 0, 0, 0, bevel=0.8); box(92, 52, 10, 0, 0, 45, bevel=2.5)
    for sx in (-35, 0, 35): box(4, 53, 56, sx, 0, -0.5, m="Iron")
    box(8, 2, 10, 0, -26.5, 38, m="Iron")
@prop
def SM_Kit_Rug():
    box(220, 150, 1.2, m="WoolRed", bevel=0.4); box(196, 126, 1.4, m="WoolBrown")
    for k in range(22):
        for sy in (-1, 1): box(1.2, 5, 0.8, -105 + k * 10, sy * 77, 0, m="Linen")
@prop
def SM_Kit_FurRug():
    sphere(1, 0, 0, 0.5, m="Fur", sx=110, sy=75, sz=1.5, sub=3, noise=0.04)
@prop
def SM_Kit_Washstand():
    box(55, 40, 3, 0, 0, 75); [box(4, 4, 75, sx, sy, 0) for sx in (-23, 23) for sy in (-16, 16)]
    lathe([(0, 0), (12, 0.5), (19, 7), (20, 9), (17, 9.5), (0, 2)], "Clay", x=0, y=0, z=78)
@prop
def SM_Kit_CandleStick():
    lathe([(0, 0), (6, 0), (6, 1.2), (1.4, 2.5), (1.2, 12), (3.5, 13), (3.5, 14), (0, 14)], "Iron")
    cyl(1.4, 12, 0, 0, 14, m="Wax", seg=10); flame(0, 0, 26.5, h=5, r=1.0)
# ---------------- dining ----------------
def trestle(L, W, H=76):
    box(L, W, 7, 0, 0, H - 7, m="Planks", bevel=0.8)
    for sx in (-L / 2 + 25, L / 2 - 25):
        box(8, W - 16, 55, sx, 0, 14); box(9, W - 6, 9, sx, 0, 0, bevel=1); box(9, W - 22, 8, sx, 0, H - 15)
    box(L - 50, 7, 8, 0, 0, 30)
@prop
def SM_Kit_TableLong(): trestle(230, 85)
@prop
def SM_Kit_TableSmall(): trestle(120, 75)
@prop
def SM_Kit_Bench():
    box(180, 30, 5, 0, 0, 42, m="Planks", bevel=0.5)
    for sx in (-70, 70): box(5, 26, 42, sx, 0, 0)
    box(140, 4, 6, 0, 0, 18)
@prop
def SM_Kit_Stool():
    cyl(17, 4, 0, 0, 44, seg=18)
    for k in range(3):
        a = 2 * math.pi * k / 3; cyl(2.2, 47, 10 * math.cos(a), 10 * math.sin(a), 0, seg=8, rot=(math.degrees(0.18) * math.sin(a), -math.degrees(0.18) * math.cos(a), 0))
@prop
def SM_Kit_Tankard():
    lathe([(0, 0), (5.2, 0), (5.0, 13), (4.4, 13), (4.6, 1), (0, 1)], "Wood", seg=16)
    for z in (2, 10): lathe([(5.4, z), (5.4, z + 1.2)], "Iron", seg=16)
    box(1.5, 2, 9, 0, 6.2, 2.5); box(1.5, 4, 1.5, 0, 4.8, 10.5); box(1.5, 4, 1.5, 0, 4.8, 2.5)
@prop
def SM_Kit_Goblet():
    lathe([(0, 0), (4, 0), (4, 0.6), (0.9, 2), (0.8, 8), (3.5, 10), (4, 16), (3.6, 16), (0.3, 10.5), (0, 10.5)], "Iron", seg=18)
@prop
def SM_Kit_Bowl():
    lathe([(0, 0), (4, 0), (8, 3), (9, 6), (8.2, 6), (0, 1)], "Wood", seg=20)
@prop
def SM_Kit_BreadLoaf():
    sphere(1, 0, 0, 5, m="Bread", sx=13, sy=7.5, sz=5.5, sub=3, noise=0.03)
    for k in range(3): box(1.2, 8, 1, -6 + k * 6, 0, 9.5, m="Dough", rot=(0, 0, 20))
@prop
def SM_Kit_BreadRound():
    sphere(1, 0, 0, 4, m="Bread", sx=10, sy=10, sz=5, sub=3, noise=0.03)
@prop
def SM_Kit_Cheese():
    cyl(12, 8, m="Cheese", seg=24)
@prop
def SM_Kit_AppleBasket():
    lathe([(0, 0), (13, 0), (19, 12), (20, 14), (18.5, 14), (12, 2), (0, 2)], "Straw", seg=20)
    for k in range(9):
        a = random.uniform(0, 6.28); r = random.uniform(0, 11); sphere(4.2, r * math.cos(a), r * math.sin(a), 8 + random.uniform(0, 4), m="Apple", sub=2, noise=0.05)
# ---------------- kitchen / cooking ----------------
@prop
def SM_Kit_Fireplace():
    box(230, 95, 15, 0, 0, 0, m="Stone", bevel=2)                                          # hearth stone
    box(200, 15, 135, 0, 40, 15, m="Stone")                                                # back
    for sx in (-100, 100): box(32, 90, 135, sx, 0, 15, m="Stone", bevel=2)                 # jambs
    box(240, 100, 22, 0, -3, 150, m="Wood", bevel=1.5)                                     # mantel beam
    box(190, 75, 150, 0, 8, 172, m="Stone")                                                # chimney breast
    for k, (a, l) in enumerate(((20, 75), (-20, 75), (90, 60))):
        cyl(7, l, 0, 5, 22 + k * 7, m="Bark", seg=10, rot=(0, 90, a))                       # logs
    box(90, 55, 2.5, 0, 5, 15, m="Ember")
    for k in range(9): flame(random.uniform(-32, 32), random.uniform(-6, 18), 20, h=random.uniform(38, 70), r=random.uniform(7, 12))
@prop
def SM_Kit_Cauldron():
    lathe([(0, 6), (14, 7), (24, 14), (28, 26), (27, 38), (28.5, 40), (27, 41), (25.5, 39), (26, 26), (0, 9)], "Iron", seg=28)
    lathe([(0, 33), (25.5, 33), (25.5, 33.5), (0, 33.5)], "Stew", seg=28)
    for k in range(3):
        a = 2 * math.pi * k / 3; cyl(2.5, 9, 18 * math.cos(a), 18 * math.sin(a), 0, m="Iron", seg=8)
    bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=False, segments=24, radius=29)
    ret = bmesh.ops.extrude_edge_only(bm, edges=bm.edges[:]); bmesh.ops.translate(bm, vec=(0, 0, 1.2), verts=[e for e in ret["geom"] if isinstance(e, bmesh.types.BMVert)])
    for v in bm.verts:
        if v.co.y < 0: v.co.z += 40 + 22 * abs(math.sin(math.atan2(v.co.y, v.co.x)))
        else: v.co.z += 40
    finish(bm, "handle", "Iron")
@prop
def SM_Kit_Tripod():
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.3
        rod((60 * math.cos(a), 60 * math.sin(a), 0), (-6 * math.cos(a), -6 * math.sin(a), 158), 2.6, "Wood")
    for k in range(10): rod((0, 0, 148 - 7 * k), (0, 0, 141 - 7 * k), 0.9 + 0.5 * (k % 2), "Iron", seg=6)     # chain
@prop
def SM_Kit_BreadOven():
    box(180, 170, 65, 0, 0, 0, m="Stone", bevel=2)
    lathe([(82, 65), (80, 95), (70, 125), (50, 148), (25, 160), (0, 163)], "Stone", seg=24)
    box(56, 8, 36, 0, -78, 68, m="Ember")                                                  # glowing mouth
    box(66, 6, 6, 0, -82, 104, m="Stone"); [box(6, 6, 40, sx, -82, 64, m="Stone") for sx in (-31, 31)]
    cyl(14, 70, 0, 25, 150, m="Stone", seg=12)                                             # flue
    box(60, 4, 45, 0, -95, 0, m="Wood", rot=(-12, 0, 0))                                   # oven door leaning
@prop
def SM_Kit_PrepTable():
    trestle(140, 70, 80)
    box(45, 28, 3, -25, 0, 80, bevel=0.5)                                                  # cutting board
    box(22, 3, 0.6, -20, -5, 83.2, m="Iron"); box(11, 2.2, 2.2, -36, -5, 83, m="Wood")     # knife
    lathe([(0, 0), (6, 0), (10, 5), (11, 8), (10, 8), (0, 1)], "Clay", x=30, y=10, z=80)   # mixing bowl
    sphere(1, 30, 10, 85, m="Dough", sx=8, sy=8, sz=4)
    cyl(2.2, 40, 18, -18, 82.2, m="Wood", seg=10, rot=(0, 90, 10))                         # rolling pin
    for k in range(3): sphere(1, -55 + k * 9, 20, 82, m="Apple", sx=4, sy=4, sz=3.5)        # onions/apples
@prop
def SM_Kit_PotRack():
    box(140, 6, 6, 0, 0, 175); [box(6, 6, 175, sx, 0, 0) for sx in (-67, 67)]
    for k, (r, d) in enumerate(((14, 6), (10, 12), (16, 5), (9, 14))):
        x = -48 + k * 32
        cyl(0.6, 18, x, 0, 157, m="Iron", seg=6)
        lathe([(0, 0), (r, 0.5), (r + 1, d), (r + 0.4, d)], "Iron", seg=18, x=x, y=0, z=157 - d - 20)
        cyl(1.0, 20, x, 0, 157 - 20, m="Iron", seg=6)
    lathe([(0, 0), (4, 1), (4.5, 3), (0, 3.2)], "Wood", x=-60, y=12, z=118); cyl(0.8, 35, -60, 12, 121, seg=6)   # ladle
@prop
def SM_Kit_FryingPan():
    lathe([(0, 0), (15, 0), (17, 4), (16.2, 4), (14, 1), (0, 1)], "Iron", seg=24); box(30, 3, 2, 0, -31, 3, m="Iron")
@prop
def SM_Kit_ShelfRack():
    for sx in (-58, 58):
        for sy in (-14, 14): box(5, 5, 180, sx, sy, 0)
    for z in (8, 55, 100, 145, 178): box(122, 34, 3, 0, 0, z, m="Planks")
@prop
def SM_Kit_Firewood():
    for row, n in enumerate((6, 5, 4, 3)):
        for k in range(n): cyl(7.5, 60, -((n - 1) * 15) / 2 + k * 15, 0, 7 + row * 13, m="Bark", seg=10, rot=(90, 0, random.uniform(-4, 4)))
@prop
def SM_Kit_Candles():
    for k, (x, y, h) in enumerate(((0, 0, 14), (6, 4, 9), (-5, 5, 11))):
        cyl(1.6, h, x, y, 0, m="Wax", seg=10); flame(x, y, h + 0.3, h=5, r=1.0)
@prop
def SM_Kit_Chandelier():
    for k in range(4):
        a = math.pi / 2 * k + math.pi / 4; rod((66 * math.cos(a), 66 * math.sin(a), 0), (0, 0, 110), 0.8, "Iron", seg=6)   # chains to the hook
    rod((0, 0, 110), (0, 0, 118), 2.0, "Iron", seg=8)
    lathe([(60, -3), (70, -3), (70, 3), (60, 3), (60, -3)], "Wood", seg=40, cap=False)
    for k in range(8):
        a = 2 * math.pi * k / 8; rod((0, 0, 0), (60 * math.cos(a), 60 * math.sin(a), 0), 2.0, "Wood")       # spokes
    for k in range(8):
        a = 2 * math.pi * k / 8; x, y = 66 * math.cos(a), 66 * math.sin(a)
        cyl(1.8, 12, x, y, 2, m="Wax", seg=8); flame(x, y, 14.3, h=6, r=1.2)
# ---------------- barn / stable / smithy ----------------
@prop
def SM_Kit_HayBale():
    box(95, 48, 42, m="Straw", bevel=5)
    for sx in (-25, 25): box(2, 49, 43, sx, 0, -0.3, m="Rope")
@prop
def SM_Kit_HayPile():
    sphere(1, 0, 0, 0, m="Straw", sx=110, sy=80, sz=70, sub=4, noise=0.08)
@prop
def SM_Kit_StallPartition():
    for sx in (-148, 148): box(12, 12, 160, sx, 0, 0, bevel=1)
    for z in (15, 45, 75, 105): box(296, 5, 24, 0, 0, z, m="Planks")
    box(310, 14, 10, 0, 0, 155, bevel=1)
@prop
def SM_Kit_Trough():
    box(150, 45, 5, 0, 0, 5); [box(150, 5, 35, 0, sy, 5) for sy in (-20, 20)]; [box(5, 45, 35, sx, 0, 5) for sx in (-72.5, 72.5)]
    box(140, 36, 8, 0, 0, 12, m="Straw"); [box(10, 40, 6, sx, 0, 0) for sx in (-60, 60)]
@prop
def SM_Kit_Pitchfork():
    cyl(1.6, 150, 0, 0, 0, m="Wood", seg=8); box(26, 2, 2, 0, 0, 150, m="Iron")
    for k in range(3): cyl(0.8, 32, -10 + k * 10, 0, 151, m="Iron", seg=6, r2=0.2)
@prop
def SM_Kit_Rake():
    cyl(1.6, 155, 0, 0, 0, m="Wood", seg=8); box(48, 4, 4, 0, 0, 155)
    for k in range(9): cyl(0.6, 10, -22 + k * 5.5, 0, 158, m="Wood", seg=6)
@prop
def SM_Kit_Shovel():
    cyl(1.8, 120, 0, 0, 0, m="Wood", seg=8); box(26, 2, 32, 0, 0, 118, m="Iron", bevel=0.5)
@prop
def SM_Kit_Ladder():
    for sx in (-22, 22): box(6, 6, 300, sx, 0, 0)
    for k in range(10): cyl(1.8, 44, -22, 0, 22 + k * 28, m="Wood", seg=8, rot=(0, 90, 0))
@prop
def SM_Kit_Cart():
    box(220, 120, 6, 0, 0, 55, m="Planks"); [box(220, 5, 35, 0, sy, 61, m="Planks") for sy in (-58, 58)]; [box(5, 120, 35, sx, 0, 61, m="Planks") for sx in (-108, 108)]
    box(10, 130, 10, 0, 0, 45, m="Wood")
    for sy in (-25, 25): box(180, 6, 6, -195, sy, 52, rot=(0, -8, 0))                       # shafts
    for sy in (-68, 68):
        lathe([(55, 0), (60, 0), (60, 8), (55, 8)], "Wood", seg=32, x=0, y=0, z=0)          # placeholder ring, rotated below
        ob = bpy.context.scene.objects[-1]; ob.data.transform(Matrix.Translation((0, sy, 60)) @ Matrix.Rotation(math.radians(90), 4, 'X') @ Matrix.Translation((0, 0, -4)))
        for k in range(8): box(5, 4, 110, 0, sy, 5, rot=(0, 22.5 * k, 0))
@prop
def SM_Kit_Anvil():
    cyl(26, 55, m="Bark", seg=16)
    box(46, 18, 10, 0, 0, 55, m="Iron", bevel=1); box(26, 12, 14, 0, 0, 65, m="Iron"); box(54, 22, 10, 4, 0, 79, m="Iron", bevel=1.5)
    cyl(9, 26, 31, 0, 84, m="Iron", seg=12, r2=1.0, rot=(0, 90, 0))
@prop
def SM_Kit_Forge():
    box(170, 115, 85, 0, 0, 0, m="Stone", bevel=3); box(120, 75, 6, 0, -5, 83, m="Ember")
    for k in range(8): sphere(1, random.uniform(-45, 45), random.uniform(-30, 20), 88, m="Ember", sx=9, sy=8, sz=5, noise=0.2)
    for k in range(4): flame(random.uniform(-30, 30), random.uniform(-15, 10), 88, h=random.uniform(12, 24), r=4)
    lathe([(95, 210), (90, 230), (45, 290), (35, 300), (35, 420), (0, 420)], "Stone", seg=4, sx=1.0, sy=0.75)   # hood + flue
    for sx in (-75, 75): box(14, 14, 125, sx, 30, 85, m="Wood")
@prop
def SM_Kit_ToolBoard():
    box(150, 4, 90, 0, 0, 0, m="Planks")
    for k, (l, hw) in enumerate(((45, 10), (40, 6), (50, 8), (38, 12))):
        x = -55 + k * 37; box(3, 3, l, x, -4, 20, m="Wood"); box(hw, 5, 6, x, -4, 20 + l, m="Iron")
    for k in range(2): box(2, 2, 40, 60 + k * 4, -5, 30, m="Iron", rot=(0, 8 * (1 - 2 * k), 0))    # tongs
@prop
def SM_Kit_QuenchTub():
    lathe([(0, 0), (40, 0), (44, 55), (40.5, 55), (37, 2), (0, 2)], "Wood", seg=24)
    for z in (8, 45): lathe([(42, z), (43.5, z), (43.5, z + 3), (42, z + 3)], "Iron", seg=24)
    lathe([(0, 46), (40, 46), (40, 46.4), (0, 46.4)], "Stew", seg=24)
# ---------------- openable storage (separate body / lid / doors; pivots on the hinges) ----------------
# UE front = +Y = Blender -y. Lids hinge on the back top edge (Blender +y), doors on the outer vertical edges.
HINGES = {}
def hollow_box(W, D, H, t, m="Wood"):
    """open-top box: floor + 4 walls (thickness t), outer W x D x H"""
    box(W, D, t, 0, 0, 0, m=m)
    for sy in (-1, 1): box(W, t, H - t, 0, sy * (D - t) / 2, t, m=m)
    for sx in (-1, 1): box(t, D - 2 * t, H - t, sx * (W - t) / 2, 0, t, m=m)
def linens(W, D, z):
    for k, mm in enumerate(("Linen", "WoolRed", "Linen", "WoolBlue")):
        box(W * 0.7 - k * 4, D * 0.6, 5, -2 + k, 0, z + k * 5, m=mm, bevel=1.5)
@prop
def SM_Kit_ChestBody():
    hollow_box(90, 50, 45, 3.0); linens(90, 50, 3)
    for sx in (-35, 35):
        for sy in (-1, 1): box(4, 1.2, 45, sx, sy * 25.6, 0, m="Iron")                  # bands on the outer faces only
    box(8, 2, 10, 0, -26.5, 32, m="Iron")
@prop
def SM_Kit_ChestLid():
    box(92, 52, 10, 0, -26, 0, bevel=2.5)                                              # extends from the hinge (y=0) to the front
    for sx in (-35, 0, 35): box(4, 54, 11, sx, -26, -0.3, m="Iron")
    HINGES["Chest"] = [0, 25.0, 45.0]                                                   # Blender hinge position on the body
@prop
def SM_Kit_TrunkBody():
    hollow_box(104, 60, 50, 3.0); linens(104, 60, 3)
    for sx in (-40, 40):
        for sy in (-1, 1): box(5, 1.2, 50, sx, sy * 30.6, 0, m="Iron")
    for sx in (-52.6, 52.6): box(1.2, 30, 6, sx, 0, 22, m="Iron")                       # side handles
    box(9, 2, 11, 0, -31, 38, m="Iron")                                                 # hasp
@prop
def SM_Kit_TrunkLid():
    box(106, 62, 7, 0, -31, 0, bevel=1.5)                                              # lid board, hinge at y=0 -> front
    box(104, 56, 12, 0, -31, 6, bevel=5.5)                                             # rounded crown
    for sx in (-40, 40): box(5, 63, 19, sx, -31, -0.3, m="Iron", bevel=2)
    HINGES["Trunk"] = [0, 30.0, 50.0]
@prop
def SM_Kit_WardrobeBody():
    W, D, H, t = 110, 55, 190, 3.0
    box(W, D, t, 0, 0, 0); box(W, D, t, 0, 0, H - t); box(W, t, H, 0, D / 2 - t / 2, 0)        # floor, top, back
    for sx in (-1, 1): box(t, D, H, sx * (W / 2 - t / 2), 0, 0)
    box(W - 2 * t, D - t, t, 0, 0, 150)                                                         # shelf
    for k, mm in enumerate(("WoolBlue", "Linen", "WoolGreen", "WoolBrown", "WoolRed")):
        box(5, 40, 95, -40 + k * 18, 2, 45, m=mm, bevel=1.2)                                    # hanging garments
    cyl(1.2, W - 10, -W / 2 + 5, 0, 145, m="Iron", seg=8, rot=(0, 90, 0))                       # rail
    for k in range(3): box(28, 30, 8, -35 + k * 33, 2, 153 + (k % 2) * 4, m="Linen", bevel=1.5)  # folded on the shelf
    box(116, 60, 8, 0, 0, 190, bevel=1.5)
@prop
def SM_Kit_WardrobeDoorL():
    box(53, 2.5, 182, 26.5, 0, 0); box(45, 1.5, 150, 26.5, -1.5, 16)                        # pivot = left hinge, door spans +x
    box(2.5, 3, 14, 49, -2.8, 85, m="Iron")
    HINGES["WardrobeL"] = [-54.0, -27.5, 4.0]
@prop
def SM_Kit_WardrobeDoorR():
    box(53, 2.5, 182, -26.5, 0, 0); box(45, 1.5, 150, -26.5, -1.5, 16)                       # pivot = right hinge, door spans -x
    box(2.5, 3, 14, -49, -2.8, 85, m="Iron")
    HINGES["WardrobeR"] = [54.0, -27.5, 4.0]
# ---------------- structure ----------------
@prop
def SM_Kit_Stairs300():
    n, rise, run, W = 15, 20.0, 28.0, 110.0          # open stair: bottom at y=+run*n, top landing edge at y=0 (UE: climbs toward +Y)
    for k in range(n):
        y = run * (n - k - 0.5); z = rise * (k + 1)
        box(W, run + 3, 5, 0, y, z - 5, m="Planks", bevel=0.5)                              # tread
        box(W - 4, 3, rise - 5, 0, y + run / 2, z - rise, m="Wood")                         # riser
    for sx in (-W / 2 - 3, W / 2 + 3):                                                      # stringers
        rod((sx, run * n + 5, 4), (sx, -2, rise * n - 4), 0.1, "Wood")                      # (placeholder, replaced below)
    for o in [o for o in bpy.context.scene.objects if o.name.startswith("r")]: bpy.data.objects.remove(o, do_unlink=True)
    L = math.hypot(run * n, rise * n); ang = math.degrees(math.atan2(rise * n, run * n))
    for sx in (-W / 2 - 3, W / 2 + 3): box(6, L + 10, 28, sx, run * n / 2, rise * n / 2 - 18, m="Wood", rot=(-ang, 0, 0))
    for k in range(6):                                                                      # handrail posts on the open (+x) side
        y = run * n * (1 - k / 5.0) - 4; z = rise * n * (k / 5.0)
        box(6, 6, 95, W / 2 + 3, y, z + 6, m="Wood")
    rod((W / 2 + 3, run * n, 100), (W / 2 + 3, -4, rise * n + 100), 3.0, "Wood")
@prop
def SM_Kit_Panel():
    box(100, 100, 100, m="Plaster")
@prop
def SM_Kit_Beam():
    box(100, 22, 22, m="Wood", bevel=1.5)
@prop
def SM_Kit_Railing():
    box(200, 8, 8, 0, 0, 100, m="Wood", bevel=1); box(200, 6, 6, 0, 0, 5, m="Wood")
    for k in range(11): box(5, 5, 100, -100 + k * 20, 0, 0, m="Wood")
for name, fn in PROPS.items():
    reset(); fn(); export(name)
KIT["_hinges"] = HINGES                       # Blender coords (UE = x, -y, z)
json.dump(KIT, open(os.path.join(OUT, "kit.json"), "w"), indent=1)
print("KIT DONE", len(KIT))
