"""The Summoner's MetaHuman face, her side (Blender): what of her own head the MetaHuman's head replaces. Her head is
part of the big piece that is her body (welded seams): a closed skull with her hair painted on it, the face, the ears and
the neck, with her collar painted on the neck. The bangs, the side locks, the twin tails and the ribbons are pieces of
their own; her eyes, lashes and brows are small pieces set into the face.

Writes into <out_dir>:
  - T_Summoner_MH_Mask.png: her texture's UV space, red where her own face, ears and neck skin are hidden (the MetaHuman's
    head is there instead), with the face's small pieces (eyes, lashes, brows), the eye zone whatever its colour and the
    bangs' tips below the brows; green where her painted hair skull and her collar are pushed out along their normals
    (they lie on the MetaHuman's scalp and neck). A texel a hidden face and a kept face share goes to the hidden one.
    839's material reads it;
  - check_*.png: her head with the hidden part dark red and the pushed part green (front, side, back), and what is left of
    her with the cut made (cut_front, cut_q);
  - classes.json: the counts.

The skin is found by colour on the body piece's head (her cheeks' hue 15-21 degrees, the blond hair painted on her skull
30-36), smoothed over neighbouring faces, and kept only where it joins the face (the ears are seeded too); under the chin
everything that is not the collar is skin; holes in it (the painted eyeliner, the mouth's line) go with it.

(A first try fitted the MetaHuman to her head: MetaHuman's face tracker found her painted eyelids, not her mouth, and the
conform followed her anime skull into a grotesque. 837 takes a preset face instead.)

    blender -b -P summoner_mh_prep.py -- <Summoner_rig.glb> <out_dir>"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
GLB, OUT = argv[0], argv[1]
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
ob = max([o for o in bpy.context.scene.objects if o.type == "MESH"], key=lambda o: len(o.data.vertices))
mw = ob.matrix_world.copy()
img = None
for m in ob.data.materials:
    if m and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image: img = n.image; break
W, H = img.size
PX = np.array(img.pixels[:], dtype=np.float32).reshape(H, W, 4)[:, :, :3]

bm = bmesh.new(); bm.from_mesh(ob.data)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
uvl = bm.loops.layers.uv.active
NF = len(bm.faces)
# ---- the welded pieces (union of vertices at the same place and of edges)
par = list(range(len(bm.verts)))
def root(a):
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
first = {}
for v in bm.verts:
    k = (round(v.co.x, 5), round(v.co.y, 5), round(v.co.z, 5))
    if k in first: par[root(v.index)] = root(first[k])
    else: first[k] = v.index
for e in bm.edges:
    a, b = root(e.verts[0].index), root(e.verts[1].index)
    if a != b: par[a] = b
vpiece = np.array([root(v.index) for v in bm.verts])
fpiece = np.array([vpiece[f.verts[0].index] for f in bm.faces])
sizes = {}
for p in fpiece: sizes[p] = sizes.get(p, 0) + 1
BODY = max(sizes, key=sizes.get)
WC = np.array([(mw @ v.co)[:] for v in bm.verts])                       # world positions (m, GLB frame: front -Y)
fc = np.array([WC[[v.index for v in f.verts]].mean(0) for f in bm.faces])
fz = np.array([WC[[v.index for v in f.verts]][:, 2].min() for f in bm.faces])

# ---- each face's colour: the texture at 7 points of its UV triangle(s)
def face_colour(f):
    uv = np.array([l[uvl].uv[:] for l in f.loops])
    pts = [uv.mean(0)] + [0.5 * (uv[i] + uv.mean(0)) for i in range(len(uv))] + [(uv[0] + uv[1]) / 2]
    cs = []
    for u in pts:
        x = int(min(max(u[0], 0), 0.9999) * W); y = int(min(max(u[1], 0), 0.9999) * H)
        cs.append(PX[y, x])
    return np.median(np.array(cs), 0)
col = np.array([face_colour(f) for f in bm.faces])
r, g, b = col[:, 0], col[:, 1], col[:, 2]
mx = col.max(1); mn = col.min(1); sat = (mx - mn) / np.maximum(mx, 1e-4)
hue = np.where(mx == r, (60 * (g - b) / np.maximum(mx - mn, 1e-4)) % 360,
               np.where(mx == g, 60 * (b - r) / np.maximum(mx - mn, 1e-4) + 120, 60 * (r - g) / np.maximum(mx - mn, 1e-4) + 240))
# (measured on her texture's sRGB values: her cheeks hue 15-21 degrees, saturation 0.18-0.29; the blond hair painted on
#  her skull hue 30-36, saturation 0.33-0.37; the collar blue or gold)
skin_score = (hue > 4) & (hue < 26) & (sat > 0.06) & (sat < 0.34) & (mx > 0.55)
collar = (sat > 0.42) | ((hue > 150) & (hue < 320))
# (no hair at the front and sides of her neck under the chin: there everything that is not the collar is skin; shadowed
#  skin there read as hair)
skin_score |= (fc[:, 2] < 1.475) & (fc[:, 1] < 0.02) & ~collar
HEAD = (fpiece == BODY) & (fz > 1.37)
nb = [[] for _ in range(NF)]
for e in bm.edges:
    lf = [f.index for f in e.link_faces]
    for i in lf:
        for j in lf:
            if i != j: nb[i].append(j)
# (also across the welded seams: faces sharing a welded vertex position)
pos_faces = {}
for f in bm.faces:
    if not HEAD[f.index]: continue
    for v in f.verts:
        pos_faces.setdefault(root(v.index), set()).add(f.index)
for s in pos_faces.values():
    for i in s:
        nb[i].extend(j for j in s if j != i)
nb = [list(set(x)) for x in nb]
skin = skin_score & HEAD
for _ in range(3):                                                         # smooth: the majority of the neighbours
    new = skin.copy()
    for i in np.nonzero(HEAD)[0]:
        n = [j for j in nb[i] if HEAD[j]]
        if not n: continue
        k = np.mean(skin[n])
        if k > 0.6: new[i] = True
        elif k < 0.25: new[i] = False
    skin = new
# keep the skin regions that hold a seed: the nose, each cheek, the chin, the throat, each ear
seeds_m = [(0.0, 1.50), (-0.045, 1.49), (0.045, 1.49), (0.0, 1.455)]
seed = set()
for sx, sz in seeds_m:
    d = (fc[:, 0] - sx) ** 2 + (fc[:, 2] - sz) ** 2 + 4 * np.maximum(fc[:, 1] + 0.12, 0) ** 2
    d[~(skin & (fc[:, 1] < -0.02))] = 9
    seed.add(int(np.argmin(d)))
for side in (-1, 1):                                                      # the ears: the skin faces furthest out at eye height
    m = skin & (np.abs(fc[:, 2] - 1.53) < 0.03) & (fc[:, 0] * side > 0.06) & (fc[:, 1] > -0.06)
    if m.any(): seed.add(int(np.nonzero(m)[0][np.argmax(fc[m, 0] * side)]))
keep = np.zeros(NF, bool); st = list(seed)
for s in st: keep[s] = True
while st:
    a = st.pop()
    for j in nb[a]:
        if skin[j] and not keep[j]: keep[j] = True; st.append(j)
# the throat ends at the collar: nothing below 1.39; nothing high on the skull (the hair's light streaks there read as
# skin and would have left holes in her hair) but the forehead under the bangs
hide = keep & (fz > 1.385) & ((fc[:, 2] < 1.60) | (fc[:, 1] < -0.10))
# holes: a patch of kept faces inside the hidden face (the painted eyeliner, the mouth's line, the nostrils) goes too
for _ in range(2):
    seen = np.zeros(NF, bool)
    for i in np.nonzero(HEAD & ~hide)[0]:
        if seen[i]: continue
        comp_ = [i]; seen[i] = True; st = [i]; touches_hidden = False
        while st:
            a = st.pop()
            for j in nb[a]:
                if not HEAD[j]: continue
                if hide[j]: touches_hidden = True; continue
                if not seen[j]: seen[j] = True; comp_.append(j); st.append(j)
        if len(comp_) < 60 and touches_hidden and fc[comp_, 2].min() > 1.40:
            hide[comp_] = True
# the face's small pieces: wholly in front of the eyes and mouth (eyes, lashes, brows), and the eye pieces themselves
small = {}
for i in range(NF):
    p = fpiece[i]
    if p == BODY: continue
    c = fc[i]; ok = abs(c[0]) < 0.095 and 1.43 < c[2] < 1.57 and c[1] < -0.08
    small[p] = small.get(p, True) and ok
facepieces = {p for p, ok in small.items() if ok and sizes[p] < 120}
# (and every small piece in front of her face that stays below the bangs' reach: the first cut left her painted lashes
#  and eyeliner standing in front of the MetaHuman's eyes)
pz = {}
for i in range(NF):
    p = fpiece[i]
    if p == BODY: continue
    c = fc[i]; z0, z1, y0, ax = pz.get(p, (9, -9, 9, 0))
    pz[p] = (min(z0, c[2]), max(z1, c[2]), min(y0, c[1]), max(ax, abs(c[0])))
facepieces |= {p for p, (z0, z1, y0, ax) in pz.items() if z1 < 1.585 and z0 > 1.43 and y0 < -0.07 and ax < 0.10 and sizes[p] < 200}
hide |= np.isin(fpiece, list(facepieces))
# the eye zone of the body piece goes whatever its colour (dark eyeliner wings there read as hair)
hide |= (fpiece == BODY) & (np.abs(fc[:, 0]) < 0.085) & (fc[:, 2] > 1.495) & (fc[:, 2] < 1.575) & (fc[:, 1] < -0.06)
# the bangs' tips: on her anime face they come down over the brows and between the eyes; over the MetaHuman's they hung
# as flat pale strips across the brows and the eyes, which carry most of an expression. The bangs (pieces of their own
# in front of the forehead) end at brow height: their triangles below BANGS_END in front of the face go
BANGS_END = 1.556
bangs = (fpiece != BODY) & (fc[:, 1] < -0.06) & (np.abs(fc[:, 0]) < 0.095) & (fc[:, 2] < BANGS_END) & (fc[:, 2] > 1.48)
bangs &= np.array([pz.get(p, (9, -9, 9, 0))[1] > 1.60 for p in fpiece])       # (only pieces that reach up past the forehead: the bangs)
hide |= bangs
print("SUMMONER MH bangs' tips cut:", int(bangs.sum()), "faces below", BANGS_END)
push = HEAD & ~hide
print("SUMMONER MH classes: head faces", int(HEAD.sum()), "skin by colour", int((skin_score & HEAD).sum()),
      "hidden", int(hide.sum()), "of them face pieces", int(np.isin(fpiece, list(facepieces)).sum()), "pushed", int(push.sum()),
      "seeds", len(seed), "face pieces", len(facepieces))

# ---- the mask in UV space (R hide, G push), with the UV overlap between the two checked
S = 2048
R = np.zeros((S, S), np.uint8); G = np.zeros((S, S), np.uint8); O = np.zeros((S, S), np.uint8)
def fill(A, poly, grow=0.5):
    """rasterise a UV polygon (pixel centres inside it or within `grow` pixels of its edges; negative: that far inside)"""
    p = np.array(poly); x0, y0 = np.floor(p.min(0)).astype(int) - 1; x1, y1 = np.ceil(p.max(0)).astype(int) + 1
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, S - 1), min(y1, S - 1)
    if x1 < x0 or y1 < y0: return
    ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1]; X = xs + 0.5; Y = ys + 0.5
    for k in range(1, len(p) - 1):
        a, b_, c = p[0], p[k], p[k + 1]
        def side(P, Q):
            e = Q - P; L = max(np.hypot(*e), 1e-9)
            return ((X - P[0]) * e[1] - (Y - P[1]) * e[0]) / L
        s1, s2, s3 = side(a, b_), side(b_, c), side(c, a)
        sg = 1.0 if (b_[0] - a[0]) * (c[1] - a[1]) - (b_[1] - a[1]) * (c[0] - a[0]) < 0 else -1.0
        inside = (sg * s1 >= -grow) & (sg * s2 >= -grow) & (sg * s3 >= -grow)
        A[y0:y1 + 1, x0:x1 + 1][inside] = 255
for f in bm.faces:
    poly = [(l[uvl].uv[0] * S, (1.0 - l[uvl].uv[1]) * S) for l in f.loops]
    if hide[f.index]: fill(R, poly, 1.0)
    else: fill(G if push[f.index] else O, poly, -0.25)
over_rg = int(((R > 0) & (G > 0)).sum()); over_ro = int(((R > 0) & (O > 0)).sum())
print("SUMMONER MH mask: hidden px", int((R > 0).sum()), "pushed px", int((G > 0).sum()), "overlap hidden/pushed", over_rg, "hidden/other", over_ro)
# (where a hidden and a kept face share texels the hidden one wins: kept winning left slivers of her old face standing in
#  front of the MetaHuman's (by the nose, over the lip); a hidden texel lost at the edge of her hair or collar shows the
#  MetaHuman's skin behind it, which is hardly seen. The material samples the mask nearest-texel without mip levels.
#  Each grows a few pixels into the empty texture round it)
G[R > 0] = 0; O[R > 0] = 0
def grey_dilation(A, size=5):
    h = size // 2; P = np.pad(A, h); out = np.zeros_like(A)
    for dy in range(size):
        for dx in range(size): out = np.maximum(out, P[dy:dy + A.shape[0], dx:dx + A.shape[1]])
    return out
empty = (R == 0) & (G == 0) & (O == 0)
Rg = np.where(empty, grey_dilation(R, size=5), R)
Gg = np.where(empty & (Rg == 0), grey_dilation(G, size=5), G)
mimg = bpy.data.images.new("mask", S, S, alpha=True)
rgba = np.dstack([Rg, Gg, np.zeros_like(R), np.full_like(R, 255)]).astype(np.float32) / 255.0
mimg.pixels[:] = rgba[::-1].ravel()
mimg.filepath_raw = os.path.join(OUT, "T_Summoner_MH_Mask.png"); mimg.file_format = "PNG"; mimg.save()

assert (np.abs(np.array(mw) - np.eye(4)) < 1e-6).all(), "the mesh object carries a transform"

# ---- check renders: hidden dark red, pushed green, the rest textured
me = ob.data
ca = me.color_attributes.new("cls", "BYTE_COLOR", "CORNER")
for f in me.polygons:
    c = (0.55, 0.05, 0.05, 1) if hide[f.index] else ((0.1, 0.8, 0.2, 1) if push[f.index] else (1, 1, 1, 1))
    for li in f.loop_indices: ca.data[li].color = c
bm.free()
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading; sh.light = "FLAT"; sh.color_type = "VERTEX"
sc.render.resolution_x = 700; sc.render.resolution_y = 700
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 0.40
for name, loc, rot in [("front", (0, -2, 1.52), (90, 0, 0)), ("side", (2, 0, 1.52), (90, 0, 90)), ("back", (0, 2, 1.52), (90, 0, 180))]:
    cam.location = loc; cam.rotation_euler = [math.radians(a) for a in rot]
    sc.render.filepath = os.path.join(OUT, f"check_{name}.png"); bpy.ops.render.render(write_still=True)
# what is left of her when the cut is made (as the material does): textured, from the front and three-quarter
sh.color_type = "TEXTURE"
bm2 = bmesh.new(); bm2.from_mesh(me); bm2.faces.ensure_lookup_table()
bmesh.ops.delete(bm2, geom=[bm2.faces[i] for i in np.nonzero(hide)[0]], context="FACES"); bm2.to_mesh(me); bm2.free()
for name, loc, rot in [("cut_front", (0, -2, 1.52), (90, 0, 0)), ("cut_q", (1.4, -1.4, 1.53), (90, 0, 45))]:
    cam.location = loc; cam.rotation_euler = [math.radians(a) for a in rot]
    sc.render.filepath = os.path.join(OUT, f"check_{name}.png"); bpy.ops.render.render(write_still=True)

json.dump({"head_faces": int(HEAD.sum()), "hidden": int(hide.sum()), "pushed": int(push.sum()), "face_pieces": len(facepieces),
           "bangs_tips_cut": int(bangs.sum()), "uv_overlap_hidden_pushed": over_rg, "uv_overlap_hidden_other": over_ro},
          open(os.path.join(OUT, "classes.json"), "w"), indent=1)
print("SUMMONER MH prep done")
