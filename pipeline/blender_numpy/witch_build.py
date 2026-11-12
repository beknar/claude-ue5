"""The summoner witch from her reference picture (E:\\temp\\summoner.jpg, the user's of 2026-11-10), built in Blender from
script: her body (a skin-modifier frame), head (the picture's face on it), hair (cap, bangs, side locks, the long back
sheet), hat (bent cone, brim, band, buckle, feather), dress, belt, sleeves, fingerless gloves, boots and the two-sided
cape; textured with witch_textures.py's pictures; rigged (a body skeleton and three chains in the cape) with weights
worked out from each part's bones; a walk and a run cycle keyed on it, her lowest foot kept on the floor every frame
and her speed measured from the planted foot. She faces -Y (+Z in glTF), stands 1.56 m to the crown, metres.
Writes <out>/SummonerWitch.glb (clips Walk and Run), SummonerWitch.blend, witch_clips.json (each clip's length and the
speed measured), and with --preview pictures of her (rest, walk, run) to <out>/preview.
Blender: blender -b -P witch_build.py -- <tex dir> <out dir> [--preview]"""
import bpy, bmesh, json, math, os, sys
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
TEX, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
PREVIEW = "--preview" in argv
os.makedirs(OUT, exist_ok=True)
PAL = json.load(open(os.path.join(TEX, "palette.json")))
bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene
COL = SC.collection
FPS = 30
SC.render.fps = FPS


# ---------------------------------------------------------------- materials
def srgb(c):
    """a palette colour (sRGB 0-255) as Blender's linear RGBA"""
    f = lambda v: (v / 255) / 12.92 if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]), 1.0)


def material(name, tex=None, color=None, rough=0.85, cull=True):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = 0.0
    if tex:
        node = m.node_tree.nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(os.path.join(TEX, tex), check_existing=True)
        m.node_tree.links.new(node.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = srgb(PAL[color] if isinstance(color, str) else color)
        m.diffuse_color = bsdf.inputs["Base Color"].default_value                     # (the previews' colour of it)
    m.use_backface_culling = cull
    return m


M = {
    "skin": material("Skin", color="skin"), "face": material("Face", tex="face.png"),
    "black": material("StockingBlack", color="stock_black"), "purple": material("StockingPurple", tex="stock_purple.png"),
    "bandage": material("Bandage", tex="bandage.png"), "hair": material("Hair", tex="hair.png"),
    "hat": material("HatCone", tex="hat_cone.png"), "brim": material("HatBrim", tex="hat_brim.png"),
    "gold": material("Gold", color="gold", rough=0.6), "cape_out": material("CapeOut", tex="cape_out.png"),
    "cape_in": material("CapeIn", tex="cape_in.png"), "purple_plain": material("CapePurple", color="cape_out"),
    "lining_plain": material("CapeGold", color="cape_in"), "dress": material("Dress", tex="dress.png"),
    "sleeve": material("Sleeve", tex="sleeve.png"), "belt": material("Belt", tex="belt.png", rough=0.5),
    "glove": material("Glove", color="glove"), "boot": material("BootShaft", tex="boot.png"),
    "boot_plain": material("Boot", color="boot"), "sole": material("Sole", color=(120, 60, 25)),
}


# ---------------------------------------------------------------- mesh helpers
def add_obj(name, verts, faces, uvs=None, mats=(), midx=None, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    if uvs is not None:
        uv = me.uv_layers.new(name="UVMap")
        for lp in me.loops: uv.data[lp.index].uv = uvs[lp.vertex_index]
    for m in mats: me.materials.append(m)
    if midx is not None: me.polygons.foreach_set("material_index", midx)
    for p in me.polygons: p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    COL.objects.link(ob)
    return ob


def tube(rings, seg):
    """rings: (centre, S, B, rx, ry, v): theta 0 on +B (her back), pi/2 on +S; u = theta / 2 pi (0.5 her front)"""
    V, UV, F = [], [], []
    for (c, S, B, rx, ry, v) in rings:
        for i in range(seg + 1):
            th = 2 * math.pi * i / seg
            V.append(Vector(c) + Vector(S) * (rx * math.sin(th)) + Vector(B) * (ry * math.cos(th)))
            UV.append((i / seg, v))
    n = seg + 1
    for j in range(len(rings) - 1):
        for i in range(seg):
            a = j * n + i
            F.append((a, a + 1, a + 1 + n, a + n))
    return V, F, UV


def cap_end(V, F, UV, ring, seg, centre, uv=(0.5, 0.5), first=False):
    """a fan closing ring number `ring` of a tube (first: the tube's first ring, wound the other way)"""
    k = len(V); V.append(Vector(centre)); UV.append(uv)
    n = seg + 1
    for i in range(seg):
        F.append((ring * n + i + 1, ring * n + i, k) if first else (ring * n + i, ring * n + i + 1, k))


def recalc(ob):
    """a closed part's faces turned outward (bmesh decides it per connected piece)"""
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.to_mesh(ob.data); bm.free()
    ob.data.update()


def mirror(V, F):
    return [Vector((-v.x, v.y, v.z)) for v in V], [tuple(reversed(f)) for f in F]


def flip(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(ob.data); bm.free()
    ob.data.update()


def orient(ob, inner):
    """turn every face of a part outward, away from inner(point) (decided by the whole part)"""
    s = sum(p.normal.dot(p.center - inner(p.center)) * p.area for p in ob.data.polygons)
    if s < 0: flip(ob)


def solidify(ob, t, offset=-1.0, mo=0, rim=0):
    m = ob.modifiers.new("Solidify", "SOLIDIFY")
    m.thickness, m.offset, m.material_offset, m.material_offset_rim, m.use_rim = t, offset, mo, rim, True
    return m


def bake(ob):
    """its modifiers applied"""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data; ob.modifiers.clear(); ob.data = me; bpy.data.meshes.remove(old)
    for p in me.polygons: p.use_smooth = True


def smooth(ob, levels=1):
    m = ob.modifiers.new("Subsurf", "SUBSURF"); m.levels = m.render_levels = levels


lerp = lambda a, b, t: a + (b - a) * t
sstep = lambda e0, e1, x: (lambda t: t * t * (3 - 2 * t))(min(1.0, max(0.0, (x - e0) / (e1 - e0))))

# ---------------------------------------------------------------- her frame (metres; her left is +X, her front -Y)
SHOULDER = Vector((0.14, 0.0, 1.27))
ARM_DIR = Vector((math.cos(math.radians(40)), 0.0, -math.sin(math.radians(40))))      # (an A-pose, 40 degrees down)
L_UP, L_FORE, L_HAND = 0.25, 0.22, 0.165
ELBOW = SHOULDER + ARM_DIR * L_UP
WRIST = ELBOW + ARM_DIR * L_FORE
HAND_END = WRIST + ARM_DIR * L_HAND
HIP, KNEE, ANKLE = Vector((0.085, 0.0, 0.86)), Vector((0.08, 0.0, 0.55)), Vector((0.075, 0.02, 0.10))
HEAD_C, HEAD_R = Vector((0.0, 0.0, 1.455)), Vector((0.083, 0.088, 0.105))


def shin_at(z):
    t = min(1.0, max(0.0, (z - ANKLE.z) / (KNEE.z - ANKLE.z)))
    return ANKLE.lerp(KNEE, t)


# ---------------------------------------------------------------- body: a skin-modifier frame (the parts that show: neck,
# legs, arms under the sleeves)
P = [(0, 0, 0.92), (0, 0, 1.06), (0, 0, 1.17), (0, 0, 1.255), (0, 0, 1.30), (0, 0, 1.38)]
R = [(0.125, 0.095), (0.10, 0.075), (0.12, 0.085), (0.13, 0.08), (0.042, 0.042), (0.040, 0.040)]
E = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]
for sx in (1, -1):
    i0 = len(P)
    P += [tuple(SHOULDER * Vector((sx, 1, 1))), tuple(ELBOW * Vector((sx, 1, 1))), tuple(WRIST * Vector((sx, 1, 1)))]
    R += [(0.048, 0.048), (0.036, 0.036), (0.028, 0.028)]
    E += [(3, i0), (i0, i0 + 1), (i0 + 1, i0 + 2)]
    i1 = len(P)
    legs = [(HIP, (0.08, 0.085)), (Vector((0.083, 0.0, 0.71)), (0.066, 0.068)), (KNEE, (0.047, 0.05)),
            (Vector((0.078, 0.012, 0.36)), (0.05, 0.052)), (ANKLE, (0.032, 0.034))]
    for k, (p, r) in enumerate(legs):
        P.append(tuple(p * Vector((sx, 1, 1)))); R.append(r)
        E.append((0, i1) if k == 0 else (i1 + k - 1, i1 + k))
me = bpy.data.meshes.new("Body"); me.from_pydata(P, E, []); me.update()
body = bpy.data.objects.new("Body", me); COL.objects.link(body)
sk = body.modifiers.new("Skin", "SKIN"); sk.use_smooth_shade = True
assert len(me.skin_vertices), "no skin layer"
for i, r in enumerate(R):
    me.skin_vertices[0].data[i].radius = r
me.skin_vertices[0].data[0].use_root = True
smooth(body, 2)
bake(body)
for m in (M["skin"], M["black"], M["purple"], M["bandage"]): body.data.materials.append(m)
uvl = body.data.uv_layers.new(name="UVMap")
mi = []
for poly in body.data.polygons:
    c = poly.center
    k = 0
    if c.z < 0.86 and abs(c.x) > 0.02:
        if c.x > 0: k = 1 if c.z < 0.755 else 0                                    # (her left leg: the black stocking)
        else: k = 2 if c.z < 0.575 else (3 if c.z < 0.735 else 0)                  # (her right: purple wrap, the bandage)
    mi.append(k)
    us = []
    for li in poly.loop_indices:
        v = body.data.vertices[body.data.loops[li].vertex_index].co
        ax = shin_at(v.z) if v.z < KNEE.z else KNEE.lerp(HIP, (v.z - KNEE.z) / (HIP.z - KNEE.z))
        ax = Vector((math.copysign(ax.x, v.x), ax.y, v.z))
        us.append([math.atan2(v.x - ax.x, -(v.y - ax.y)) / (2 * math.pi) + 0.5, v.z * (1.333 if k != 3 else 3.0)])
    lo = min(u for u, _ in us)
    for (u, vv), li in zip(us, poly.loop_indices):
        if u - lo > 0.5: u -= 1.0                                                     # (a face across the seam stays whole)
        uvl.data[li].uv = (u, vv)
body.data.polygons.foreach_set("material_index", mi)

# ---------------------------------------------------------------- head: an anime head, the picture's face projected on its front
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=28, radius=1.0)
for v in bm.verts:
    x, y, z = v.co
    zl = z
    sx = 1 - 0.30 * zl * zl if zl < 0 else 1.0                                      # (the jaw narrows to her chin)
    sy = (1 - 0.12 * zl * zl if zl < 0 else 1.0) if y < 0 else 1.08              # (the back of the head fuller)
    v.co = HEAD_C + Vector((x * HEAD_R.x * sx, y * HEAD_R.y * sy, z * HEAD_R.z))
me = bpy.data.meshes.new("Head"); bm.to_mesh(me); bm.free()
head = bpy.data.objects.new("Head", me); COL.objects.link(head)
me.materials.append(M["face"])
uvl = me.uv_layers.new(name="UVMap")
for lp in me.loops:
    v = me.vertices[lp.vertex_index].co
    uvl.data[lp.index].uv = (0.5 + v.x / 0.22, 0.5 + (v.z - 1.45) / 0.22) if v.y < 0.02 else (0.02, 0.98)
for p in me.polygons: p.use_smooth = True

# ---------------------------------------------------------------- hair
def head_surface(az, el, k=1.0):
    """a point on the head's ellipsoid (azimuth from her front toward her left, elevation), k times its size"""
    d = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    sy = 1.08 if d.y > 0 else 1.0
    return HEAD_C + Vector((d.x * HEAD_R.x, d.y * HEAD_R.y * sy, d.z * HEAD_R.z)) * k


# the cap: the head's sphere a little larger, kept over the hairline
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=28, radius=1.0)
for v in bm.verts:
    x, y, z = v.co
    v.co = HEAD_C + Vector((x * HEAD_R.x * 1.10, y * HEAD_R.y * (1.10 * (1.08 if y > 0 else 1.0)), z * HEAD_R.z * 1.06))
gone = []
for f in bm.faces:
    c = f.calc_center_median()
    keep = c.z > HEAD_C.z + 0.035 or (c.y > 0.0 and c.z > HEAD_C.z - 0.08) or (abs(c.x) > 0.055 and c.y > -0.035 and c.z > HEAD_C.z - 0.035)
    if not keep: gone.append(f)
bmesh.ops.delete(bm, geom=gone, context="FACES")
me = bpy.data.meshes.new("HairCap"); bm.to_mesh(me); bm.free()
hcap = bpy.data.objects.new("HairCap", me); COL.objects.link(hcap)
me.materials.append(M["hair"])
uvl = me.uv_layers.new(name="UVMap")
for lp in me.loops:
    v = me.vertices[lp.vertex_index].co
    uvl.data[lp.index].uv = (math.atan2(v.x, v.y) / (2 * math.pi) + 0.5, 0.75 + (v.z - HEAD_C.z) * 2)
for p in me.polygons: p.use_smooth = True
solidify(hcap, 0.006, offset=1.0); bake(hcap)


def ribbon(name, centre, width, normal_fn, mat, thick=0.004, v0=1.0, v1=0.0):
    """a strand: a strip along the points `centre`, `width` wide at each, across the side normal_fn(i) gives; v from v0 at
    its root to v1 at its tip"""
    V, UV, F = [], [], []
    n = len(centre)
    for i in range(n):
        t = (centre[min(i + 1, n - 1)] - centre[max(i - 1, 0)]).normalized()
        side = t.cross(normal_fn(i, centre[i])).normalized()
        V += [centre[i] - side * width[i] / 2, centre[i] + side * width[i] / 2]
        vv = lerp(v0, v1, i / (n - 1)); UV += [(0.0, vv), (1.0, vv)]
        if i: F.append((2 * i - 2, 2 * i - 1, 2 * i + 1, 2 * i))
    ob = add_obj(name, V, F, UV, [mat])
    return ob


def out_from_head(i, p):
    return (p - HEAD_C).normalized()


hair_parts = [hcap]
# bangs over her forehead (the tips at her brows, longer ones between her eyes)
for k, az in enumerate([-62, -46, -31, -16, -3, 10, 24, 38, 52, 64]):
    el_end = [14, 8, 2, -3, 1, -4, 3, 8, 12, 16][k]
    pts = [head_surface(math.radians(az * (1 - 0.15 * s)), math.radians(lerp(58, el_end, s)), 1.125 + 0.01 * s) for s in [i / 9 for i in range(10)]]
    w = [0.034 * (1 - s) ** 0.7 + 0.003 for s in [i / 9 for i in range(10)]]
    ob = ribbon("Bang%d" % k, pts, w, out_from_head, M["hair"]); orient(ob, lambda c: HEAD_C)
    solidify(ob, 0.004, offset=-1.0); bake(ob); hair_parts.append(ob)
# side locks: from her temples down in front of her shoulders to her chest
for side in (1, -1):
    for k, (dx, ln) in enumerate([(0.0, 1.0), (0.022, 0.93)]):
        key = [head_surface(math.radians(side * 80), math.radians(18), 1.12),
               Vector((side * (0.098 + dx), -0.035, 1.39)), Vector((side * (0.112 + dx), -0.085, 1.27)),
               Vector((side * (0.118 + dx), -0.120, 1.16)), Vector((side * (0.120 + dx), -0.128, lerp(1.16, 1.02, ln)))]
        pts = []
        for i in range(16):                                                     # (Catmull-Rom through the keys)
            s = i / 15 * (len(key) - 1); j = min(int(s), len(key) - 2); t = s - j
            p0, p1, p2, p3 = key[max(j - 1, 0)], key[j], key[j + 1], key[min(j + 2, len(key) - 1)]
            pts.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
        w = [0.040 * (1 - (i / 15) ** 2) + 0.004 for i in range(16)]
        ob = ribbon("SideLock%s%d" % ("L" if side > 0 else "R", k), pts, w, lambda i, p: Vector((0, -1, 0)), M["hair"])
        orient(ob, lambda c: Vector((0, 0.1, c.z)))
        solidify(ob, 0.005, offset=-1.0); bake(ob); hair_parts.append(ob)


# ---------------------------------------------------------------- the cape: outside purple, inside gold, open at her front
CAPE_TOP, CAPE_BOT = 1.33, 0.24


def cape_point(phi, t, k=1.0):
    """phi: from her front toward her left (radians); t: 0 the shoulders to 1 the hem"""
    z = lerp(CAPE_TOP, CAPE_BOT, t)
    s = t ** 0.8
    rx, ry = 0.19 + 0.28 * s, 0.12 + 0.27 * s
    fold = 1 + 0.06 * t * math.sin(9 * phi + 1.3)
    return Vector((rx * math.sin(phi) * fold * k, -ry * math.cos(phi) * fold * k, z))


def cape_open(t):
    return math.radians(lerp(44, 62, t))                                            # (the front opening's half angle)


CU, CV = 72, 40
V, UV, F = [], [], []
for j in range(CV + 1):
    t = j / CV
    for i in range(CU + 1):
        u = i / CU
        phi = lerp(cape_open(t), 2 * math.pi - cape_open(t), u)
        V.append(cape_point(phi, t)); UV.append((u, 1 - t))
for j in range(CV):
    for i in range(CU):
        a = j * (CU + 1) + i
        F.append((a, a + 1, a + CU + 2, a + CU + 1))
cape = add_obj("Cape", V, F, UV, [M["cape_out"], M["cape_in"], M["gold"]])
orient(cape, lambda c: Vector((0, 0, c.z)))
solidify(cape, 0.008, offset=-1.0, mo=1, rim=2); bake(cape)

# the collar standing round her neck, open at the front
V, F, UV = tube([(Vector((0, 0.005, z)), (1, 0, 0), (0, 1, 0), rx, ry, v) for z, rx, ry, v in
                 [(1.305, 0.075, 0.072, 0.0), (1.355, 0.088, 0.086, 0.5), (1.41, 0.106, 0.102, 1.0)]], 36)
keep = [f for f in F if all(abs(math.atan2(V[k].x, -V[k].y)) > math.radians(78) for k in f)]   # (behind and beside her neck)
collar = add_obj("Collar", V, keep, UV, [M["purple_plain"], M["lining_plain"], M["gold"]])
orient(collar, lambda c: Vector((0, 0, c.z)))
solidify(collar, 0.007, offset=-1.0, mo=1, rim=2); bake(collar)

# the back hair: over the collar and down her back on the cape, to her waist
HU, HV = 26, 22
V, UV, F = [], [], []
for i in range(HU + 1):
    a = lerp(-1, 1, i / HU)
    z_end = 0.97 + 0.035 * math.sin(a * 9.0 + 0.7) - 0.02 * (1 - abs(a))
    for j in range(HV + 1):
        s = j / HV
        z = lerp(1.52, z_end, s)
        phi = math.pi + a * math.radians(lerp(62, 46, s))
        key = [(1.52, head_surface(phi, math.asin(min(1, (1.52 - HEAD_C.z) / (HEAD_R.z * 1.06))), 1.13)),
               (1.43, Vector((0.120 * math.sin(phi), -0.118 * math.cos(phi), 1.43))),
               (1.33, cape_point(phi, 0.0, 1.07))]
        if z >= 1.43: p = key[0][1].lerp(key[1][1], (1.52 - z) / 0.09)
        elif z >= 1.33: p = key[1][1].lerp(key[2][1], (1.43 - z) / 0.10)
        else: p = cape_point(phi, (CAPE_TOP - z) / (CAPE_TOP - CAPE_BOT), 1.0) * Vector((1.05, 1.05, 1)) + Vector((0, 0.012, 0))
        p.z = z
        V.append(p); UV.append((i / HU, 1 - s))
for i in range(HU):
    for j in range(HV):
        a = i * (HV + 1) + j
        F.append((a, a + 1, a + HV + 2, a + HV + 1))
backhair = add_obj("BackHair", V, F, UV, [M["hair"]])
orient(backhair, lambda c: Vector((0, 0, c.z)))
solidify(backhair, 0.008, offset=1.0); bake(backhair)
hair_parts.append(backhair)

# ---------------------------------------------------------------- hat: the cone (bent tip), brim, band, buckle, feather
HAT = Matrix.Translation((0.0, 0.006, 1.532)) @ Matrix.Rotation(math.radians(2), 4, "X") @ Matrix.Rotation(math.radians(7), 4, "Y")
HN = 30


def spine(s):
    return Vector((0.16 * s ** 3, 0.07 * s ** 3, 0.31 * s - 0.04 * s ** 4))


rings = []
for k in range(HN + 1):
    s = k / HN
    c = spine(s)
    tng = (spine(min(1, s + 0.01)) - spine(max(0, s - 0.01))).normalized()
    S = Vector((1, 0, 0)) - tng * tng.x; S.normalize()                             # (her left, square to the cone's line)
    B = S.cross(tng).normalized()
    if B.y < 0: B = -B                                                                # (her back)
    r = 0.125 * (1 - s) ** 1.05 * (1 + 0.06 * math.sin(math.pi * s)) + 0.002
    rings.append((c, S, B, r, r, s))
V, F, UV = tube(rings, 40)
cap_end(V, F, UV, HN, 40, spine(1.0), (0.5, 0.99))
V = [HAT @ v for v in V]
cone = add_obj("HatCone", V, F, UV, [M["hat"]])
orient(cone, lambda c: HAT @ spine(0.3))
V, UV, F = [], [], []
NB, NR, BRIM_R = 64, 7, 0.37
for j in range(NR + 1):
    rr = lerp(0.10, BRIM_R, j / NR)
    for i in range(NB + 1):
        th = 2 * math.pi * i / NB
        droop = -0.045 * ((rr - 0.10) / (BRIM_R - 0.10)) ** 2
        V.append(HAT @ Vector((rr * math.sin(th), rr * math.cos(th), droop))); UV.append((i / NB, j / NR))
for j in range(NR):
    for i in range(NB):
        a = j * (NB + 1) + i
        F.append((a, a + 1, a + NB + 2, a + NB + 1))
brim = add_obj("HatBrim", V, F, UV, [M["brim"], M["gold"]])
orient(brim, lambda c: HAT @ Vector((0, 0, -1)))
solidify(brim, 0.007, offset=-1.0, mo=0, rim=1); bake(brim)
# the buckle (a gold ring on the band at her left front) and the feather rising from it
phi_b = math.radians(52)
s_b = 0.042 / 0.31
cb, rb = spine(s_b), 0.125 * (1 - s_b) ** 1.05 + 0.006
radial = Vector((math.sin(phi_b), -math.cos(phi_b), 0.0))
centre_b = cb + radial * rb
up = Vector((0, 0, 1)); side_b = up.cross(radial).normalized()
V, F, UV = [], [], []
for i in range(25):
    th = 2 * math.pi * i / 24
    c = centre_b + (side_b * math.cos(th) + up * math.sin(th)) * 0.022
    for k in range(9):
        ph = 2 * math.pi * k / 8
        dirr = (side_b * math.cos(th) + up * math.sin(th))
        V.append(c + (dirr * math.cos(ph) + radial * math.sin(ph)) * 0.006); UV.append((0.5, 0.5))
for i in range(24):
    for k in range(8):
        a = i * 9 + k
        F.append((a, a + 1, a + 10, a + 9))
V = [HAT @ v for v in V]
buckle = add_obj("HatBuckle", V, F, UV, [M["gold"]])
recalc(buckle)
fe = [centre_b + radial * 0.01 + (up * 0.95 + side_b * -0.3 + radial * 0.25).normalized() * (0.14 * s) + side_b * (-0.02 * s * s) for s in [i / 11 for i in range(12)]]
fe = [HAT @ p for p in fe]
fw = [0.045 * math.sin(math.pi * min(0.98, s * 0.9 + 0.08)) ** 0.8 + 0.003 for s in [i / 11 for i in range(12)]]
feather = ribbon("HatFeather", fe, fw, lambda i, p: (HAT.to_3x3() @ radial).normalized(), M["gold"])
solidify(feather, 0.003, offset=0.0); bake(feather)
hat_parts = [cone, brim, buckle, feather]

# ---------------------------------------------------------------- dress and belt
DRESS = [(1.305, 0.075, 0.055), (1.29, 0.135, 0.085), (1.27, 0.165, 0.098), (1.22, 0.155, 0.105), (1.17, 0.145, 0.108),
         (1.11, 0.12, 0.092), (1.065, 0.112, 0.085), (1.00, 0.14, 0.10), (0.93, 0.168, 0.125), (0.86, 0.19, 0.145), (0.80, 0.215, 0.165)]
DRESS = DRESS[::-1]                                                                   # (from the hem up)


def dress_r(z):
    for (z0, a0, b0), (z1, a1, b1) in zip(DRESS, DRESS[1:]):
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0); return lerp(a0, a1, t), lerp(b0, b1, t)
    return DRESS[-1][1:]


rings = []
for k in range(len(DRESS) - 1):
    for q in range(3):
        z = lerp(DRESS[k][0], DRESS[k + 1][0], q / 3)
        rx, ry = dress_r(z)
        rings.append(((0, 0, z), (1, 0, 0), (0, 1, 0), rx, ry, (z - 0.80) / (1.305 - 0.80)))
rings.append(((0, 0, DRESS[-1][0]), (1, 0, 0), (0, 1, 0), DRESS[-1][1], DRESS[-1][2], 1.0))
V, F, UV = tube(rings, 48)
dress = add_obj("Dress", V, F, UV, [M["dress"]])
orient(dress, lambda c: Vector((0, 0, c.z)))
solidify(dress, 0.004, offset=-1.0); bake(dress)
rings = []
for z, v in [(1.048, 0.0), (1.07, 0.5), (1.092, 1.0)]:
    rx, ry = dress_r(z)
    rings.append(((0, 0, z), (1, 0, 0), (0, 1, 0), rx + 0.009, ry + 0.009, v))
V, F, UV = tube(rings, 48)
belt = add_obj("Belt", V, F, UV, [M["belt"]])
orient(belt, lambda c: Vector((0, 0, c.z)))
solidify(belt, 0.004, offset=-1.0); bake(belt)

# ---------------------------------------------------------------- sleeves, gloved hands
BACK = Vector((0, 1, 0))
SIDE = ARM_DIR.cross(BACK).normalized()                                               # (up and out: the back of her hand)


def left_and_right(name, V, F, UV, mats, midx_fn=None):
    out = []
    for sx in (1, -1):
        Vs, Fs = (V, F) if sx > 0 else mirror(V, F)
        midx = [midx_fn([Vs[k] for k in f]) for f in Fs] if midx_fn else None
        out.append(add_obj(name + (".L" if sx > 0 else ".R"), Vs, Fs, UV, mats, midx))
    return out


rings = []
for a, r, v in [(-0.03, 0.058, 1.0), (0.0, 0.063, 0.97), (0.12, 0.058, 0.72), (L_UP, 0.055, 0.46), (0.36, 0.060, 0.24), (0.43, 0.074, 0.08), (0.475, 0.086, 0.0)]:
    rings.append((SHOULDER + ARM_DIR * a, SIDE, BACK, r, r, v))
V, F, UV = tube(rings, 32)
sleeves = left_and_right("Sleeve", V, F, UV, [M["sleeve"]])
for ob in sleeves:
    sx = 1 if ob.name.endswith(".L") else -1
    sh = SHOULDER * Vector((sx, 1, 1)); ad = ARM_DIR * Vector((sx, 1, 1))
    orient(ob, lambda c, sh=sh, ad=ad: sh + ad * (c - sh).dot(ad))
    solidify(ob, 0.004, offset=-1.0); bake(ob)

rings = []
for a, w, h, v in [(-0.035, 0.030, 0.026, 0.0), (0.0, 0.033, 0.022, 0.1), (0.04, 0.039, 0.018, 0.3), (0.085, 0.039, 0.015, 0.5),
                   (0.12, 0.036, 0.013, 0.7), (0.15, 0.032, 0.011, 0.85), (0.162, 0.026, 0.009, 0.95), (L_HAND, 0.017, 0.007, 1.0)]:
    rings.append((WRIST + ARM_DIR * a, BACK, SIDE, w, h, v))
V, F, UV = tube(rings, 20)
cap_end(V, F, UV, 0, 20, WRIST + ARM_DIR * -0.04, first=True)
cap_end(V, F, UV, len(rings) - 1, 20, WRIST + ARM_DIR * (L_HAND + 0.004))
k0 = len(V)
th_dir = (ARM_DIR * 0.55 - BACK * 0.8 - SIDE * 0.2).normalized()
th_base = WRIST + ARM_DIR * 0.025 - BACK * 0.028
V2, F2, UV2 = tube([(th_base + th_dir * a, BACK.cross(th_dir).normalized(), SIDE, r, r * 0.85, a) for a, r in [(0.0, 0.014), (0.03, 0.012), (0.055, 0.009), (0.065, 0.004)]], 12)
V += V2; UV += UV2; F += [tuple(k + k0 for k in f) for f in F2]


def hand_mat(vs):
    """fingerless gloves: the glove over her palm and the fingers' first joints, bare fingers and thumb tip beyond"""
    c = sum(vs, Vector()) / len(vs)
    cl = Vector((abs(c.x), c.y, c.z))                                               # (in her left hand's frame)
    along = (cl - WRIST).dot(ARM_DIR)
    off_axis = (cl - (WRIST + ARM_DIR * along)).length
    if along > 0.11 and off_axis < 0.045: return 1
    if (cl - th_base).dot(th_dir) > 0.035 and off_axis > 0.03: return 1
    return 0


hands = left_and_right("Hand", V, F, UV, [M["glove"], M["skin"]], hand_mat)
for ob in hands:
    recalc(ob)
    smooth(ob, 1); bake(ob)

# ---------------------------------------------------------------- boots: the shaft with its cuff, the foot, the sole and heel
rings = []
for z, r, v in [(0.035, 0.050, 0.0), (0.10, 0.049, 0.12), (0.18, 0.052, 0.4), (0.255, 0.056, 0.74), (0.265, 0.068, 0.78), (0.30, 0.072, 0.9), (0.338, 0.076, 1.0)]:
    rings.append((shin_at(z) * Vector((1, 1, 0)) + Vector((0, 0, z)), (1, 0, 0), (0, 1, 0), r, r * 1.05, v))
V, F, UV = tube(rings, 32)
shafts = left_and_right("BootShaft", V, F, UV, [M["boot"]])
for ob in shafts:
    orient(ob, lambda c: Vector((math.copysign(0.075, c.x), 0.02, c.z)))
    solidify(ob, 0.005, offset=-1.0); bake(ob)
rings = []
for y, cz, w, h in [(0.065, 0.055, 0.036, 0.045), (0.05, 0.055, 0.046, 0.055), (0.0, 0.055, 0.048, 0.053), (-0.06, 0.048, 0.047, 0.045),
                    (-0.12, 0.036, 0.042, 0.032), (-0.155, 0.028, 0.032, 0.022), (-0.17, 0.024, 0.014, 0.012)]:
    rings.append((Vector((0.075, y, cz)), (1, 0, 0), (0, 0, 1), w, h, 0.5))
V, F, UV = tube(rings, 20)
cap_end(V, F, UV, 0, 20, Vector((0.075, 0.07, 0.055)), first=True)
cap_end(V, F, UV, len(rings) - 1, 20, Vector((0.075, -0.174, 0.024)))
for v in V:
    if v.z < 0.014: v.z = 0.014
feet = left_and_right("BootFoot", V, F, UV, [M["boot_plain"]])
for ob in feet:
    recalc(ob)
    smooth(ob, 1); bake(ob)
# the sole and the heel block (boxes)
V, F = [], []


def box(V, F, lo, hi):
    k = len(V)
    for z in (lo.z, hi.z):
        for (x, y) in ((lo.x, lo.y), (hi.x, lo.y), (hi.x, hi.y), (lo.x, hi.y)):
            V.append(Vector((x, y, z)))
    F += [(k, k + 3, k + 2, k + 1), (k + 4, k + 5, k + 6, k + 7), (k, k + 1, k + 5, k + 4), (k + 1, k + 2, k + 6, k + 5),
          (k + 2, k + 3, k + 7, k + 6), (k + 3, k, k + 4, k + 7)]


box(V, F, Vector((0.075 - 0.047, -0.176, 0.0)), Vector((0.075 + 0.047, 0.072, 0.016)))     # (the sole under the whole foot)
box(V, F, Vector((0.075 - 0.038, 0.012, 0.0)), Vector((0.075 + 0.038, 0.072, 0.03)))       # (the block heel)
soles = left_and_right("BootSole", V, F, [(0.5, 0.5)] * len(V), [M["sole"]], None)
for ob in soles: recalc(ob)

# ---------------------------------------------------------------- the rig
arm_data = bpy.data.armatures.new("Rig")
arm = bpy.data.objects.new("Rig", arm_data); COL.objects.link(arm)
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
EB = arm_data.edit_bones
BONES = {}


def bone(name, h, t, parent=None, deform=True):
    b = EB.new(name); b.head, b.tail = Vector(h), Vector(t); b.roll = 0.0
    if parent: b.parent = EB[parent]; b.use_connect = False
    b.use_deform = deform
    BONES[name] = (Vector(h), Vector(t))


bone("root", (0, 0, 0), (0, -0.15, 0), deform=False)
bone("hips", (0, 0, 0.92), (0, 0, 1.02), "root")
bone("spine", (0, 0, 1.02), (0, 0, 1.14), "hips")
bone("chest", (0, 0, 1.14), (0, 0, 1.29), "spine")
bone("neck", (0, 0, 1.29), (0, 0, 1.37), "chest")
bone("head", (0, 0, 1.37), (0, 0, 1.58), "neck")
for sx, s in ((1, "L"), (-1, "R")):
    X = Vector((sx, 1, 1))
    bone("shoulder." + s, Vector((0.03, 0, 1.265)) * X, SHOULDER * X, "chest")
    bone("upper_arm." + s, SHOULDER * X, ELBOW * X, "shoulder." + s)
    bone("forearm." + s, ELBOW * X, WRIST * X, "upper_arm." + s)
    bone("hand." + s, WRIST * X, HAND_END * X, "forearm." + s)
    bone("thigh." + s, HIP * X, KNEE * X, "hips")
    bone("shin." + s, KNEE * X, ANKLE * X, "thigh." + s)
    bone("foot." + s, ANKLE * X, Vector((0.075, -0.09, 0.03)) * X, "shin." + s)
    bone("toe." + s, Vector((0.075, -0.09, 0.03)) * X, Vector((0.075, -0.165, 0.025)) * X, "foot." + s)
CHAINS = {"L": math.radians(112), "C": math.pi, "R": math.radians(248)}
for c, phi in CHAINS.items():
    ts = [0.04, 0.36, 0.68, 1.0]
    for k in range(3):
        bone("cape.%s%d" % (c, k + 1), cape_point(phi, ts[k], 0.96), cape_point(phi, ts[k + 1], 0.96), "chest" if k == 0 else "cape.%s%d" % (c, k))
bpy.ops.object.mode_set(mode="OBJECT")
REST = {b.name: b.matrix_local.to_3x3() for b in arm_data.bones}
PARENT = {b.name: (b.parent.name if b.parent else None) for b in arm_data.bones}
ORDER = [b.name for b in arm_data.bones]

# ---------------------------------------------------------------- weights
def seg_d(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
    return (a + ab * t - p).length


def side_ok(n, x):
    return not ((n.endswith(".L") and x < -0.015) or (n.endswith(".R") and x > 0.015))


def dist_w(p, allowed, power=4, top=4):
    ws = sorted(((1.0 / (seg_d(p, *BONES[n]) + 0.008) ** power, n) for n in allowed if side_ok(n, p.x)), reverse=True)[:top]
    s = sum(w for w, _ in ws)
    return {n: w / s for w, n in ws}


def blend(a, b, t):
    out = {}
    for n, w in a.items(): out[n] = out.get(n, 0) + w * (1 - t)
    for n, w in b.items(): out[n] = out.get(n, 0) + w * t
    return out


def assign(ob, fn):
    groups = {}
    for v in ob.data.vertices:
        for n, w in fn(v.co).items():
            if w < 0.01: continue
            if n not in groups: groups[n] = ob.vertex_groups.new(name=n)
            groups[n].add([v.index], w, "REPLACE")
    mod = ob.modifiers.new("Armature", "ARMATURE"); mod.object = arm
    ob.parent = arm


BODY_B = ["hips", "spine", "chest", "neck", "head"] + [b + s for s in (".L", ".R") for b in ("shoulder", "upper_arm", "forearm", "hand", "thigh", "shin", "foot")]
CAPE_B = ["cape.%s%d" % (c, k) for c in "LCR" for k in (1, 2, 3)]


def cape_w(p):
    t = (CAPE_TOP - p.z) / (CAPE_TOP - CAPE_BOT)
    return blend({"chest": 1.0}, dist_w(p, CAPE_B, 4, 3), sstep(0.02, 0.14, t))


def skirt_w(p):
    up = dist_w(p, ["hips", "spine", "chest"], 4, 3)
    t = sstep(0.95, 0.80, p.z)
    sL = min(1, max(0, 0.5 + p.x / 0.16))
    low = {"hips": 1 - 0.35 * t, "thigh.L": 0.35 * t * sL, "thigh.R": 0.35 * t * (1 - sL)}
    return blend(up, low, sstep(1.0, 0.92, p.z))


assign(body, lambda p: dist_w(p, BODY_B, 4, 4))
for ob in [head, hcap] + [o for o in hair_parts if o.name.startswith("Bang")] + hat_parts:
    assign(ob, lambda p: {"head": 1.0})
for ob in [o for o in hair_parts if o.name.startswith("SideLock")]:
    assign(ob, lambda p: blend({"chest": 1.0}, {"head": 1.0}, sstep(1.26, 1.38, p.z)))
assign(backhair, lambda p: blend(cape_w(p), {"head": 1.0}, sstep(1.34, 1.43, p.z)))
assign(cape, cape_w)
assign(collar, lambda p: {"chest": 1.0})
assign(dress, skirt_w)
assign(belt, lambda p: dist_w(p, ["hips", "spine"], 4, 2))
for ob in sleeves:
    s = ob.name[-1]
    assign(ob, lambda p, s=s: dist_w(p, ["shoulder." + s, "upper_arm." + s, "forearm." + s, "hand." + s], 4, 3))
for ob in hands:
    s = ob.name[-1]
    assign(ob, lambda p, s=s: dist_w(p, ["forearm." + s, "hand." + s], 6, 2))
for ob in shafts:
    s = ob.name[-1]
    assign(ob, lambda p, s=s: dist_w(p, ["shin." + s, "foot." + s], 6, 2))
for ob in feet + soles:
    s = ob.name[-1]
    assign(ob, lambda p, s=s: dist_w(p, ["foot." + s, "toe." + s], 6, 2))
for ob in bpy.data.objects:
    if ob.type == "MESH": ob.data.update()

# ---------------------------------------------------------------- the clips: every bone's turn given in the armature's axes
I3 = Matrix.Identity(3)
Rx = lambda d: Matrix.Rotation(math.radians(d), 3, "X")
Ry = lambda d: Matrix.Rotation(math.radians(d), 3, "Y")
Rz = lambda d: Matrix.Rotation(math.radians(d), 3, "Z")


def hang(name, target):
    d = (BONES[name][1] - BONES[name][0]).normalized()
    return d.rotation_difference(target.normalized()).to_matrix()


HANG = {}
for sx, s in ((1, "L"), (-1, "R")):
    tgt = Vector((0.26 * sx, 0.0, -1.0))
    HANG["upper_arm." + s], HANG["forearm." + s] = hang("upper_arm." + s, tgt), hang("forearm." + s, tgt)

PB = arm.pose.bones
for pb in PB: pb.rotation_mode = "QUATERNION"
HIPS_REST = REST["hips"]
CONTACT = {s: [("foot." + s, Vector((0.075 * sx, 0.05, 0.0))), ("foot." + s, Vector((0.075 * sx, -0.09, 0.0))),
               ("toe." + s, Vector((0.075 * sx, -0.165, 0.002)))] for sx, s in ((1, "L"), (-1, "R"))}


def put(D, offset):
    dabs = {}
    for n in ORDER:
        p = PARENT[n]
        Dp = dabs[p] if p else I3
        Dn = D.get(n, Dp)
        dabs[n] = Dn
        R = REST[n]
        PB[n].rotation_quaternion = (R.inverted() @ (Dp.inverted() @ Dn) @ R).to_quaternion()
    PB["hips"].location = HIPS_REST.inverted() @ offset


def contacts():
    out = {}
    for s, pts in CONTACT.items():
        out[s] = []
        for bn, p in pts:
            b = arm_data.bones[bn]
            out[s].append(PB[bn].matrix @ b.matrix_local.inverted() @ p)
    return out


GAIT = {  # thigh swing (deg), arm swing, stance share of the cycle, knee in swing, knee in stance, toe-off heel lift
    "Walk": dict(A=24, B=18, stance=0.60, k_swing=58, k_stance=10, heel=24),
    "Run": dict(A=36, B=32, stance=0.36, k_swing=105, k_stance=24, heel=30),
}


def leg(kind, ph):
    """one leg at its own phase ph (0 to 1; 0 its heel strike): the thigh's swing (forward +), the knee, the foot's pitch
    (toe down +). In stance the thigh sweeps back at an even rate, so the planted foot goes back at an even speed"""
    g = GAIT[kind]; A, s = g["A"], g["stance"]
    ph %= 1.0
    if ph < s:
        q = ph / s
        a = A - 2 * A * q
        k = 4 + g["k_stance"] * math.sin(math.pi * min(1.0, q / 0.6))                 # (the knee gives as her weight comes on)
        f = (-8 * (1 - q / 0.15) if q < 0.15 else 0.0) + (g["heel"] * ((q - 0.7) / 0.3) ** 2 if q > 0.7 else 0.0)
    else:
        u = (ph - s) / (1 - s)
        a = -A + 2 * A * (0.5 - 0.5 * math.cos(math.pi * u))
        k = 4 + g["k_swing"] * math.sin(math.pi * min(1.0, u ** (0.75 if kind == "Run" else 1.0)))
        f = g["heel"] * (1 - u / 0.25) if u < 0.25 else -10 * math.sin(math.pi * (u - 0.25) / 0.75)
    return a, k, f


def pose_at(kind, p):
    """the absolute turns of her bones at phase p (0 to 2 pi; her left heel strikes at 0, her right at pi)"""
    D = {}
    walk = kind == "Walk"
    g = GAIT[kind]; A, B = g["A"], g["B"]
    phL = p / (2 * math.pi)
    legs = {"L": leg(kind, phL), "R": leg(kind, phL + 0.5)}
    tw_n = (legs["L"][0] - legs["R"][0]) / (2 * A)                                    # (+1 her left leg forward)
    lean = (0, 2, 3, 0, -2) if walk else (7, 10, 12, 3, -6)                          # (hips, spine, chest, neck, head)
    tw = 6 if walk else 9
    D["hips"] = Rz(-tw * tw_n) @ Rx(lean[0])
    D["spine"] = Rz(-tw * 0.3 * tw_n) @ Rx(lean[1])
    D["chest"] = Rz(tw * 0.8 * tw_n) @ Rx(lean[2])
    D["neck"] = Rz(tw * 0.3 * tw_n) @ Rx(lean[3])
    D["head"] = Rx(lean[4])
    for s in "LR":
        a, k, f = legs[s]
        D["thigh." + s] = Rx(-a)
        D["shin." + s] = Rx(-(a - k))
        D["foot." + s] = Rx(f)
        D["toe." + s] = Rx(-max(f, 0.0) * 0.8)                                       # (the toes stay down as the heel lifts)
        sw = -B * a / A                                                              # (the arm against the leg on its side)
        e = (12 + 10 * max(0.0, sw / B)) if walk else (70 + 25 * max(0.0, sw / B))
        D["upper_arm." + s] = Rx(-sw) @ HANG["upper_arm." + s]
        D["forearm." + s] = Rx(-(sw + e)) @ HANG["forearm." + s]
        D["hand." + s] = Rx(-(sw + e + (4 if walk else 10))) @ HANG["forearm." + s]
    base, amp, gain = (5, 2.5, (4, 4)) if walk else (24, 4.0, (14, 12))
    for c, flare in (("L", -1), ("C", 0), ("R", 1)):
        th = base + amp * math.sin(2 * p - 0.8)
        th2 = th + gain[0] + amp * 1.2 * math.sin(2 * p - 1.6)
        th3 = th2 + gain[1] + amp * 1.5 * math.sin(2 * p - 2.4)
        fl = flare * (3 if walk else 7)
        for k, t in enumerate((th, th2, th3)):
            D["cape.%s%d" % (c, k + 1)] = Ry(fl * (k + 1) / 3) @ Rx(t)
    st = g["stance"]
    sway = (0.016 if walk else 0.008) * math.cos(2 * math.pi * (phL - st / 2))        # (her hips over the foot she stands on)
    lift = 0.0
    if not walk:                                                                    # (the run's flights: neither foot down)
        for f0 in (st, 0.5 + st):
            q = ((phL - f0) % 1.0) / (0.5 - st)
            if q < 1.0: lift = 0.045 * math.sin(math.pi * q)
    return D, sway, lift


CLIPS = {"Walk": 32, "Run": 20}
ad = arm.animation_data_create()
acts, info = [], {}
for name, N in CLIPS.items():
    # every frame's pose worked out with no action on the rig (an action's curves would win over the values set here), her
    # lowest foot point put on the floor; then keyed
    ad.action = None
    frames, track, roots = [], [], []
    for fr in range(N + 1):
        p = 2 * math.pi * fr / N
        D, sway, lift = pose_at(name, p)
        put(D, Vector((sway, 0, 0)))
        bpy.context.view_layer.update()
        low = min(c.z for s in contacts().values() for c in s)
        put(D, Vector((sway, 0, -low + lift)))
        bpy.context.view_layer.update()
        track.append(contacts()); roots.append(-low + lift)
        frames.append({pb.name: pb.rotation_quaternion.copy() for pb in PB} | {"@hips": PB["hips"].location.copy()})
    act = bpy.data.actions.new(name); act.use_fake_user = True; ad.action = act
    if hasattr(ad, "action_slot") and act.slots: ad.action_slot = act.slots[0]
    prev = {}
    for fr, vals in enumerate(frames):
        for pb in PB:
            q = vals[pb.name]
            if pb.name in prev and q.dot(prev[pb.name]) < 0: q = -q
            prev[pb.name] = q
            pb.rotation_quaternion = q
            pb.keyframe_insert("rotation_quaternion", frame=fr, group=pb.name)
        PB["hips"].location = vals["@hips"]
        PB["hips"].keyframe_insert("location", frame=fr, group="hips")
    if hasattr(ad, "action_slot") and act.slots and not ad.action_slot: ad.action_slot = act.slots[0]
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, N
    # the speed: how fast a planted point of a foot goes back (her body forward): the mean over every step of a frame in
    # which the same point is on the floor (within 1.5 mm) at both ends
    dt = 1.0 / FPS
    v = sorted((track[f + 1][s][k].y - track[f][s][k].y) / dt for f in range(N) for s in "LR" for k in range(3)
               if track[f][s][k].z < 0.0015 and track[f + 1][s][k].z < 0.0015)
    speed = sum(v) / len(v) if v else 0.0
    info[name] = {"frames": N, "fps": FPS, "duration": N / FPS, "speed": speed, "planted_samples": len(v),
                  "speed_p25": v[len(v) // 4] if v else 0, "speed_p75": v[3 * len(v) // 4] if v else 0,
                  "root_z": [min(roots), max(roots)]}
    acts.append(act)
    print("CLIP", name, json.dumps(info[name]))

# ---------------------------------------------------------------- pictures (Workbench, textured)
if PREVIEW:
    pdir = os.path.join(OUT, "preview"); os.makedirs(pdir, exist_ok=True)
    SC.render.engine = "BLENDER_WORKBENCH"
    SC.display.shading.light = "STUDIO"; SC.display.shading.color_type = "TEXTURE"
    SC.display.shading.show_backface_culling = True
    SC.render.resolution_x, SC.render.resolution_y = 640, 900
    SC.render.film_transparent = False
    world = bpy.data.worlds.new("W"); SC.world = world
    cam_d = bpy.data.cameras.new("Cam"); cam_d.type = "ORTHO"; cam_d.ortho_scale = 2.05
    cam = bpy.data.objects.new("Cam", cam_d); COL.objects.link(cam); SC.camera = cam
    views = {"front": (Vector((0, -5, 0.95)), Vector((0, 0, 0.95)), 2.05), "side": (Vector((5, 0, 0.95)), Vector((0, 0, 0.95)), 2.05),
             "back": (Vector((0, 5, 0.95)), Vector((0, 0, 0.95)), 2.05), "threeq": (Vector((3.4, -3.6, 1.3)), Vector((0, 0, 0.92)), 2.05),
             "face": (Vector((0, -3, 1.42)), Vector((0, 0, 1.42)), 0.42), "faceq": (Vector((1.6, -2.6, 1.5)), Vector((0, 0, 1.40)), 0.6),
             "upper": (Vector((0, -4, 1.18)), Vector((0, 0, 1.18)), 0.9)}

    def shoot(tag, which):
        for v in which:
            loc, at, sc = views[v]
            cam_d.ortho_scale = sc
            cam.location = loc; cam.rotation_euler = (at - loc).to_track_quat("-Z", "Y").to_euler()
            SC.render.filepath = os.path.join(pdir, "%s_%s.png" % (tag, v))
            bpy.ops.render.render(write_still=True)

    ad.action = None
    for pb in PB: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    shoot("rest", ["front", "side", "back", "threeq", "face", "faceq", "upper"])
    for act, frames in ((acts[0], (0, 8, 16, 24)), (acts[1], (0, 4, 8, 12, 16))):
        ad.action = act
        if hasattr(ad, "action_slot") and act.slots: ad.action_slot = act.slots[0]
        for f in frames:
            SC.frame_set(f); shoot("%s%02d" % (act.name.lower(), f), ["side", "threeq"])
    ad.action = None

# ---------------------------------------------------------------- the clips as NLA tracks, the GLB, the .blend
ad.action = None
for act in acts:
    tr = ad.nla_tracks.new(); tr.name = act.name
    st = tr.strips.new(act.name, 0, act); st.name = act.name
for pb in PB: pb.matrix_basis.identity()
bpy.context.view_layer.update()
SC.frame_set(0)
glb = os.path.join(OUT, "SummonerWitch.glb")
bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", export_animations=True, export_animation_mode="NLA_TRACKS",
                          export_force_sampling=True, export_optimize_animation_size=False, export_skins=True, export_yup=True)
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == "MESH")
top = max(max((o.matrix_world @ v.co).z for v in o.data.vertices) for o in bpy.data.objects if o.type == "MESH")
json.dump({"height": top, "crown": 1.56, "triangles": tris, "clips": info}, open(os.path.join(OUT, "witch_clips.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "SummonerWitch.blend"))
print("WITCH DONE", glb, os.path.getsize(glb), "triangles", tris, "top", round(top, 3))
