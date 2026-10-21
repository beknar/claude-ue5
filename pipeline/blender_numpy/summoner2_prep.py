"""Summoner2 (ai models/Summoner2.glb, a realistic Tripo model made from two photos) for her MetaHuman: one mesh of 492k
triangles in a T-pose, 1.9 units tall, facing -Y, its hair, skin, bikini and the bikini's chains in one texture.

Writes into <out_dir> (Blender metres, feet on z 0, she faces -Y; scaled to <height_cm>):
  - s2_target.glb: the MetaHuman conform target (842): her skin and the bikini's cups and bottom; the hair, the chains,
    the bikini's strings and bows left out; the skull under the hair filled with an ellipsoid fitted to her face's edge
    and the hair shell pulled in by its thickness, blended into the face (as fig4's clean_body_target.py);
  - s2_portrait.png: a front portrait of the whole model (hair and all) from a known camera (in classes.json), for
    MetaHuman's face landmark tracker;
  - s2_bikini.glb: the bikini (cups, bottom, strings, bows, chains) with its UVs and her texture, for the outfit (845);
  - s2_hair.glb: the hair shell (a reference for the groom's length and fringe);
  - check_*.png: the classes on the model (skin grey, hair magenta, bikini red, chain yellow, target green outline);
  - classes.json: the counts, the scale, the heights found (chin, eyes, crown) and the portrait camera.

Each face's class comes from its texture colour (median of 4 points of its UV triangle), smoothed over its neighbours
(across the UV seams too: vertices welded by position), and from where it is: hair is magenta (hue 290-350) or dark on
the head away from the face; the bikini is saturated red below the neck (the lips are red too); the chains are the gold
and pale grey bits on the hip band that the skin does not reach.

    blender -b -P summoner2_prep.py -- <Summoner2.glb> <out_dir> [height_cm=163] [skull|none] [hair_cm=3.5]"""
import bpy, bmesh, sys, os, json, math, numpy as np, mathutils
argv = sys.argv[sys.argv.index("--") + 1:]
GLB, OUT = argv[0], argv[1]
HEIGHT = float(argv[2]) / 100.0 if len(argv) > 2 else 1.63
SKULL = (argv[3] if len(argv) > 3 else "skull") == "skull"    # the ellipsoid under the hair (fig4's way), or none
HAIR_CM = float(argv[4]) if len(argv) > 4 else 3.5              # how much hair is between the hair shell and her skull
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
ob = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
for o in list(bpy.context.scene.objects):
    if o is not ob and o.type != "MESH": pass
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = ob.data
NV = len(me.vertices); NF = len(me.polygons)
co = np.zeros(NV * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3).astype(np.float64)
lo, hi = co.min(0), co.max(0)
s = HEIGHT / (hi[2] - lo[2])
co = (co - np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])) * s
# centre x / y on the feet and the pelvis, not the arms and hair
mid = co[(co[:, 2] > 0.80) & (co[:, 2] < 1.00)]
co[:, 0] -= np.median(mid[:, 0]); co[:, 1] -= np.median(mid[:, 1])
me.vertices.foreach_set("co", co.astype(np.float32).ravel()); me.update()
tri = np.zeros(NF * 3, np.int64); me.polygons.foreach_get("vertices", tri); tri = tri.reshape(-1, 3)
uv = np.zeros(len(me.loops) * 2, np.float32); me.uv_layers.active.data.foreach_get("uv", uv); uv = uv.reshape(-1, 3, 2)
img = next(n.image for n in ob.active_material.node_tree.nodes if n.type == "TEX_IMAGE" and any(l.to_socket.name == "Base Color" for l in n.outputs[0].links))
W, H = img.size
PX = np.array(img.pixels[:], np.float32).reshape(H, W, 4)[:, :, :3]
def sample(u):
    x = np.clip((u[:, 0] % 1.0) * W, 0, W - 1).astype(int); y = np.clip((u[:, 1] % 1.0) * H, 0, H - 1).astype(int)
    return PX[y, x]
c0 = uv.mean(1)
cols = np.stack([sample(c0)] + [sample(0.5 * (uv[:, i] + c0)) for i in range(3)], 0)
col = np.median(cols, 0)
r, g, b = col[:, 0], col[:, 1], col[:, 2]
mx = col.max(1); mn = col.min(1); d = np.maximum(mx - mn, 1e-5); sat = (mx - mn) / np.maximum(mx, 1e-5)
hue = np.where(mx == r, (60 * (g - b) / d) % 360, np.where(mx == g, 60 * (b - r) / d + 120, 60 * (r - g) / d + 240))
val = mx
fc = co[tri].mean(1)
# ---- the welded vertex graph (UV seams split vertices)
key = np.round(co * 2e4).astype(np.int64)
_, weld = np.unique(key, axis=0, return_inverse=True); weld = weld.ravel(); NW = weld.max() + 1
ftri = weld[tri]
def smooth(lab, it=3, hi_=0.6, lo_=0.3, mask=None):
    lab = lab.astype(np.float64)
    for _ in range(it):
        vs = np.zeros(NW); vn = np.zeros(NW)
        np.add.at(vs, ftri.ravel(), np.repeat(lab, 3)); np.add.at(vn, ftri.ravel(), 1)
        fm = (vs / np.maximum(vn, 1))[ftri].mean(1)
        new = lab.copy(); new[fm > hi_] = 1; new[fm < lo_] = 0
        if mask is not None: new[~mask] = lab[~mask]
        lab = new
    return lab > 0.5
# ---- classes
red = ((hue < 14) | (hue > 348)) & (sat > 0.45) & (val > 0.25)
magenta = (hue > 285) & (hue <= 348) & (sat > 0.22)
dark = val < 0.22
# ---- her head's heights (measured): the nose tip is the most forward skin-coloured point in the band 14-21 cm under
# the crown (the fringe's light strands hang higher, at the brows); eyes 4 cm above it, the neck 9 cm below
crown = co[:, 2].max()
cand = ~magenta & ~red & (val > 0.4) & (fc[:, 2] > crown - 0.21) & (fc[:, 2] < crown - 0.14) & (np.abs(fc[:, 0]) < 0.03)
nose_f = np.nonzero(cand)[0][np.argmin(fc[cand, 1])]
NOSE = fc[nose_f]; ez = float(NOSE[2] + 0.04); NECK = float(NOSE[2] - 0.09)
gold = (hue > 25) & (hue < 60) & (sat > 0.18) & (sat < 0.75)
head = fc[:, 2] > NECK + 0.01
face_front = head & (fc[:, 1] < -0.02) & (np.abs(fc[:, 0]) < 0.07) & (fc[:, 2] < NECK + 0.20)
hair = smooth(magenta | (dark & head & ~face_front) | (magenta & ~head), 3)
bikini = smooth(red & (fc[:, 2] < NOSE[2] - 0.06), 2)                   # (the lips are red too)
# chains: gold / pale bits on the hip band beside the bikini bottom
hips = (fc[:, 2] > 0.80) & (fc[:, 2] < 1.02)
pale = (sat < 0.14) & (val > 0.45)                                       # (the chains' pale grey links)
chain = smooth(hips & (gold | pale) & ~bikini, 1) & (fc[:, 2] < 0.96)       # (they hang from the ties, 0.83-0.92 m)
skin0 = ~(hair | bikini | chain)
# the bikini's strings and bows: thin red pieces off the body (behind the back at the bow, round the neck); kept in
# the outfit, left out of the target. Found as the red faces whose welded component is small.
def comps(mask):
    idx = np.nonzero(mask)[0]; par = np.arange(NW)
    def root(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for f in idx:
        a, b_, c = ftri[f]; ra, rb, rc = root(a), root(b_), root(c)
        par[rb] = ra; par[rc] = ra
    lab = np.array([root(ftri[f, 0]) for f in idx])
    return idx, lab
idx, lab = comps(bikini)
u, cnt = np.unique(lab, return_counts=True); size = dict(zip(u, cnt))
big = np.array([size[l] > 1500 for l in lab])
cups = np.zeros(NF, bool); cups[idx[big]] = True
strings = bikini & ~cups
# (red specks the colour test found on her skin: pieces of under 40 faces, not the strings or the bows)
speck = np.zeros(NF, bool); speck[idx[np.array([size[l] < 40 for l in lab])]] = True
bikini = bikini & ~speck; strings = strings & ~speck
# her skin: the skin-coloured faces joined (through skin and the bikini) to her nose or her torso. The fringe's and the
# side locks' light strands are skin-coloured too, but lie on the hair, not on her face.
torso_f = np.nonzero(skin0 & (np.abs(fc[:, 2] - 1.05) < 0.02) & (np.abs(fc[:, 0]) < 0.03) & (fc[:, 1] < 0))[0][0]
allowed = skin0 | cups
idx2, lab2 = comps(allowed)
lab_of = dict(zip(idx2, lab2))
keep_lab = {lab_of[nose_f], lab_of[torso_f]}
joined = np.zeros(NF, bool); joined[idx2[np.isin(lab2, list(keep_lab))]] = True
skin = skin0 & joined
print("S2PREP nose tip", NOSE.round(3), "| skin-coloured faces left out (on the hair):", int((skin0 & ~joined).sum()))
hair = hair | (skin0 & ~joined & (fc[:, 2] > NECK - 0.15))
# the brows and the forehead above them go: the fringe is modelled onto it (strands standing out of the skin); the skull and
# MetaHuman's prior make it
fringe = (fc[:, 2] > ez + 0.012) & (fc[:, 1] < NOSE[1] + 0.07)
# the side locks lying along her cheeks: strips of hair fused to the face (their light strands are skin-coloured). A face
# of one faces into the head (its back), or has her cheek right behind it (its front: a ray from just under it, going in,
# meets skin within 2.5 cm). Only on the sides of the face, away from the nose and the mouth.
from mathutils.bvhtree import BVHTree
tv0 = co[tri]; fn = np.cross(tv0[:, 1] - tv0[:, 0], tv0[:, 2] - tv0[:, 0]); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
HC = np.array([NOSE[0], NOSE[1] + 0.09, ez - 0.02])                     # (inside the head, behind the face)
band = (fc[:, 2] > NOSE[2] - 0.085) & (fc[:, 2] < ez + 0.04) & (np.abs(fc[:, 0] - NOSE[0]) > 0.04) & (fc[:, 1] < HC[1] + 0.02)
inward = band & ((fn * (fc - HC)).sum(1) < 0)
bvh = BVHTree.FromPolygons([tuple(p) for p in co], [tuple(t) for t in tri], all_triangles=True)
strip_front = np.zeros(NF, bool)
for i in np.nonzero(band & ~inward & skin)[0]:
    o_ = mathutils.Vector(fc[i] - fn[i] * 0.0035); hit = bvh.ray_cast(o_, mathutils.Vector(-fn[i]), 0.025)
    if hit[0] is not None: strip_front[i] = True
locks = smooth(inward | strip_front, 2, mask=band)
print("S2PREP side locks: %d faces off the face (inward %d, in front of skin %d)" % ((locks & band).sum(), inward.sum(), strip_front.sum()))
target = (skin | cups) & ~fringe & ~(locks & band)
print("S2PREP neck z %.3f | faces: skin %d hair %d bikini %d (cups+bottom %d, strings %d, specks dropped %d) chain %d" % (
    NECK, skin.sum(), hair.sum(), bikini.sum(), cups.sum(), strings.sum(), speck.sum(), chain.sum()))
for nm, m_ in (("skin", skin), ("hair", hair), ("bikini", bikini), ("chain", chain)):
    if m_.any():
        print("  %-7s hue %s sat %s val %s" % (nm, np.percentile(hue[m_], [5, 50, 95]).round(0), np.percentile(sat[m_], [5, 50, 95]).round(2), np.percentile(val[m_], [5, 50, 95]).round(2)))
# ---- check renders: classes as vertex colours (face corner colours)
CL = np.zeros((NF, 4), np.float32); CL[:] = (0.75, 0.72, 0.70, 1)
CL[hair] = (0.85, 0.1, 0.6, 1); CL[bikini] = (0.9, 0.05, 0.05, 1); CL[strings] = (0.3, 0.0, 0.0, 1); CL[chain] = (1, 0.9, 0.1, 1)
ca = me.color_attributes.new("cls", "FLOAT_COLOR", "CORNER")
ca.data.foreach_set("color", np.repeat(CL, 3, 0).ravel())
def json_dump():
    pass
# ---- write the meshes: by deleting faces of a copy
def export_subset(mask, path, keep_mat=True):
    bpy.ops.object.select_all(action="DESELECT")
    cp = ob.copy(); cp.data = ob.data.copy(); bpy.context.scene.collection.objects.link(cp)
    bm = bmesh.new(); bm.from_mesh(cp.data); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in np.nonzero(~mask)[0]], context="FACES")
    bm.to_mesh(cp.data); bm.free()
    if "cls" in cp.data.color_attributes: cp.data.color_attributes.remove(cp.data.color_attributes["cls"])
    cp.select_set(True); bpy.context.view_layer.objects.active = cp
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_materials="EXPORT" if keep_mat else "NONE")
    return cp
# target first: the skull fill
tg = None
info = {"scale": s, "height": HEIGHT, "neck_z": NECK}
info["crown_z_with_hair"] = float(crown); info["nose_tip"] = NOSE.round(4).tolist(); info["eye_z"] = ez
tgt_obj = export_subset(target, os.path.join(OUT, "_tmp_target.glb"), keep_mat=False)
tv = np.array([tgt_obj.matrix_world @ v.co for v in tgt_obj.data.vertices])
# skull: the head's face edge + the hair shell pulled in (as fig4)
# the cranium's centre sits about 10 cm behind the nose tip, a little above the eyes; the hair shell over the top and
# back of the scalp (not the long hair beyond it) pulled in by its thickness, and the forehead, give its size
C = np.array([NOSE[0], NOSE[1] + 0.10, ez + 0.02])
R = np.array([0.072, 0.095, 0.100])
hs = co[np.unique(tri[hair & head].ravel())]
hs = hs[(hs[:, 2] > ez + 0.02) & (np.abs(hs[:, 0] - NOSE[0]) < 0.09) & (np.linalg.norm(hs - C, axis=1) < 0.13)]
# (the hair is thicker on the crown than at the sides: 1.2 cm at the sides, HAIR_CM straight up)
dd = hs - C; nn = np.linalg.norm(dd, axis=1, keepdims=True); up = np.clip(dd[:, 2:3] / nn, 0, 1)
hs = hs - dd / nn * (0.012 + (HAIR_CM / 100.0 - 0.012) * up)
fv_head = tv[(tv[:, 2] > NECK + 0.02)]
edge = fv_head[(fv_head[:, 2] > ez + 0.035) & (fv_head[:, 1] < NOSE[1] + 0.05)]
rng = np.random.default_rng(0)
hs = hs[rng.choice(len(hs), min(len(hs), 6000), replace=False)] if len(hs) else hs
pts = np.vstack([edge, hs]) if len(hs) else edge
best = None
for sc_ in np.linspace(0.88, 1.12, 13):
  for szz in np.linspace(0.80, 1.10, 11):
    for dy in np.linspace(-0.015, 0.015, 7):
        for dz in np.linspace(-0.02, 0.02, 9):
            c_ = C + [0, dy, dz]; Rs = R * [sc_, sc_, sc_ * szz]
            rr = np.linalg.norm((pts - c_) / Rs, axis=1)
            err = np.mean((rr - 1) ** 2)
            if best is None or err < best[0]: best = (err, sc_, szz, dy, dz)
_, sc_, szz, dy, dz = best
SK = R * [sc_, sc_, sc_ * szz]; SC = C + [0, dy, dz]
info["skull"] = {"centre": SC.round(4).tolist(), "radii": SK.round(4).tolist()}
print("S2PREP skull centre", SC.round(3), "radii", SK.round(3), "eye z %.3f" % ez)
if SKULL:
  bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=96, radius=1.0)
  sk = bpy.context.active_object; sk.scale = tuple(SK); sk.location = tuple(SC)
  bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
  kd = mathutils.kdtree.KDTree(len(tv))
  for i, p in enumerate(tv): kd.insert(p, i)
  kd.balance()
  bm = bmesh.new(); bm.from_mesh(sk.data)
  drop = [v for v in bm.verts if v.co.z < NECK + 0.03 or kd.find(v.co)[2] < 0.006 or
          ((v.co.y < SC[1] - 0.03) and (v.co.z < ez + 0.012) and abs(v.co.x - NOSE[0]) < 0.065)]
  bmesh.ops.delete(bm, geom=drop, context="VERTS")
  hf = tv[(tv[:, 2] > NECK + 0.02) & (tv[:, 1] < SC[1] - 0.01)]
  kf = mathutils.kdtree.KDTree(len(hf))
  for i, p in enumerate(hf): kf.insert(p, i)
  kf.balance(); scv = mathutils.Vector(tuple(SC)); BLEND = 0.05
  for v in bm.verts:
      cc, _, dist = kf.find(v.co)
      if dist > BLEND: continue
      w = (1 - dist / BLEND) ** 1.5; dv = v.co - scv; rs = dv.length; dv.normalize()
      v.co = scv + dv * (rs + ((cc - scv).dot(dv) - rs) * w)
  bm.to_mesh(sk.data); bm.free()
  bpy.ops.object.select_all(action="DESELECT")
  tgt_obj.select_set(True); sk.select_set(True); bpy.context.view_layer.objects.active = tgt_obj
  bpy.ops.object.join()
bpy.ops.object.select_all(action="DESELECT"); tgt_obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "s2_target.glb"), export_format="GLB", use_selection=True, export_materials="NONE")
os.remove(os.path.join(OUT, "_tmp_target.glb"))
info["target_vertices"] = len(tgt_obj.data.vertices)
bik = export_subset(bikini | chain, os.path.join(OUT, "s2_bikini.glb"))
hr = export_subset(hair, os.path.join(OUT, "s2_hair.glb"))
for o in (bik, hr, tgt_obj): o.hide_render = True
# ---- renders
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys() else "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.75, 0.75, 0.75, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.9
for rot, e in (((math.radians(60), 0, math.radians(-25)), 2.0), ((math.radians(70), 0, math.radians(30)), 0.8)):
    l = bpy.data.objects.new("l", bpy.data.lights.new("l", "SUN")); l.data.energy = e; l.rotation_euler = rot; sc.collection.objects.link(l)
cd = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
def shoot(path, loc, look, hfov=None, ortho=None, res=(1000, 1000)):
    sc.render.resolution_x, sc.render.resolution_y = res
    cam.location = mathutils.Vector(loc); dvec = mathutils.Vector(look) - cam.location
    cam.rotation_euler = dvec.to_track_quat("-Z", "Y").to_euler()
    if ortho: cd.type = "ORTHO"; cd.ortho_scale = ortho
    else: cd.type = "PERSP"; cd.sensor_fit = "HORIZONTAL"; cd.angle = math.radians(hfov)
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)
# the portrait: perspective, known camera (UE: x = Blender x, y = -Blender y, z = z, cm)
PZ = ez - 0.02; PX0 = float(NOSE[0]); PCAM = (PX0, -0.80, PZ); PFOV = 22.0
shoot(os.path.join(OUT, "s2_portrait.png"), PCAM, (PX0, 0.0, PZ), hfov=PFOV, res=(1024, 1024))
info["portrait"] = {"blender_cam": PCAM, "hfov": PFOV, "size": 1024, "ue_cam_cm": [PX0 * 100, 80.0, PZ * 100], "ue_yaw": -90.0}
# class checks: an emission material from the colour attribute
mat = bpy.data.materials.new("cls"); mat.use_nodes = True; nt = mat.node_tree
at_ = nt.nodes.new("ShaderNodeVertexColor"); at_.layer_name = "cls"
nt.links.new(at_.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
orig = list(ob.data.materials); ob.data.materials.clear(); ob.data.materials.append(mat)
shoot(os.path.join(OUT, "check_front.png"), (0, -10, 0.85), (0, 0, 0.85), ortho=1.75, res=(900, 900))
shoot(os.path.join(OUT, "check_back.png"), (0, 10, 0.85), (0, 0, 0.85), ortho=1.75, res=(900, 900))
shoot(os.path.join(OUT, "check_head.png"), (0.6, -0.6, ez), (0, 0, ez - 0.02), ortho=0.40, res=(800, 800))
shoot(os.path.join(OUT, "check_hips.png"), (0.5, -0.8, 0.92), (0, 0, 0.92), ortho=0.6, res=(800, 800))
ob.hide_render = True; tgt_obj.hide_render = False
tm = bpy.data.materials.new("t"); tm.use_nodes = True; tgt_obj.data.materials.clear(); tgt_obj.data.materials.append(tm)
shoot(os.path.join(OUT, "check_target.png"), (0.9, -0.9, 0.9), (0, 0, 0.85), ortho=1.8, res=(900, 900))
shoot(os.path.join(OUT, "check_target_head.png"), (0.5, -0.5, ez), (0, 0, ez - 0.02), ortho=0.36, res=(800, 800))
shoot(os.path.join(OUT, "check_target_back.png"), (-0.5, 0.6, ez - 0.1), (0, 0, ez - 0.1), ortho=0.6, res=(800, 800))
info["faces"] = {"skin": int(skin.sum()), "hair": int(hair.sum()), "bikini": int(bikini.sum()), "cups": int(cups.sum()), "strings": int(strings.sum()), "chain": int(chain.sum())}
json.dump(info, open(os.path.join(OUT, "classes.json"), "w"), indent=1)
print("S2PREP done", json.dumps(info))
