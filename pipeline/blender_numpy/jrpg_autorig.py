"""Unrigged Meshy character (static T-pose GLB, e.g. jrpg-fem3) -> UE-ready skinned FBX with a UE-mannequin-named skeleton
(root, pelvis, spine_01-03, neck_01, head, clavicle / upperarm / lowerarm / hand, thigh / calf / foot / ball) like the
Meshy rigs (jrpg_build.py), so UE's auto IK-rig and the Quinn/Soldier retargets work unchanged.
Joints come from the mesh: arm line + fingertips + armpit width, crotch height from the leg gap, leg / torso slice centroids,
toe tip; limb segment ratios fill in elbow / wrist. Skinning: Blender bone-heat (automatic weights); any vertex it leaves
unweighted gets the nearest bone. Scaled to HEIGHT cm, feet on z=0, facing -Y (UE +Y). No animations.
Blender: -b -P jrpg_autorig.py -- model.glb out_dir name [height_cm]"""
import bpy, bmesh, sys, os, math
from mathutils import Vector, Matrix
argv = sys.argv[sys.argv.index("--") + 1:]
glb, out, name = argv[0], argv[1], argv[2]; HEIGHT = float(argv[3]) if len(argv) > 3 else 168.0
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=glb)
meshes = [o for o in sc.objects if o.type == 'MESH']
for o in list(sc.objects):
    if o.type != 'MESH': bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1: bpy.ops.object.join()
mesh = bpy.context.view_layer.objects.active; mesh.name = name
mw = mesh.matrix_world.copy(); mesh.parent = None; mesh.matrix_world = Matrix.Identity(4); mesh.data.transform(mw)
for img in bpy.data.images:
    if img.packed_file or img.has_data:
        p = os.path.join(out, img.name.replace(" ", "_") + ".png"); img.filepath_raw = p; img.file_format = 'PNG'; img.save(); print("texture", p, tuple(img.size))
# normalise: feet on 0, centred, HEIGHT (metres here; converted to cm at the end)
V = [v.co.copy() for v in mesh.data.vertices]
lo = Vector([min(v[i] for v in V) for i in range(3)]); hi = Vector([max(v[i] for v in V) for i in range(3)])
k = (HEIGHT / 100.0) / (hi.z - lo.z)
mesh.data.transform(Matrix.Scale(k, 4) @ Matrix.Translation(Vector(((-(lo.x + hi.x) / 2), -(lo.y + hi.y) / 2, -lo.z))))
P = [v.co.copy() for v in mesh.data.vertices]; H = HEIGHT / 100.0
def band(z0, z1, xmin=-9, xmax=9): return [p for p in P if z0 <= p.z < z1 and xmin <= p.x < xmax]
def cen(ps): return Vector((sum(p.x for p in ps) / len(ps), sum(p.y for p in ps) / len(ps), sum(p.z for p in ps) / len(ps)))
# ---- arms: verts far out to the side ----
armR = [p for p in P if p.x > 0.15 * H]; armL = [p for p in P if p.x < -0.15 * H]
za = sorted(p.z for p in armR + armL)[len(armR + armL) // 2]; ya = sorted(p.y for p in armR + armL)[len(armR + armL) // 2]
xf = (max(p.x for p in armR) + -min(p.x for p in armL)) / 2                       # fingertip reach
# armpit: torso half-width just below the arm (right side only: long hair hangs on the left)
arm_bot = min(p.z for p in P if p.x > 0.12 * H and abs(p.z - za) < 0.1 * H)
tor = band(arm_bot - 0.06 * H, arm_bot - 0.02 * H, 0.0, 0.2 * H)
xs = max(p.x for p in tor)
def arm_pt(f): return xs + f * (xf - xs)
# ---- legs: crotch = highest z where the slice still has a central gap (scanning down) ----
def has_gap(z):
    xs_ = sorted(p.x for p in band(z - 0.005 * H, z + 0.005 * H, -0.12 * H, 0.12 * H))
    return any(b - a > 0.02 * H and a < 0 < b for a, b in zip(xs_, xs_[1:])) if xs_ else True
from mathutils.bvhtree import BVHTree                              # crotch: cast up between the legs (vertex-gap scans fail on
bm = bmesh.new(); bm.from_mesh(mesh.data); bvh = BVHTree.FromBMesh(bm); bm.free()   # touching knees and on sparse low-poly slices)
lg = band(0.22 * H, 0.26 * H, -0.12 * H, 0.12 * H); yl = sorted(p.y for p in lg)[len(lg) // 2]
hits = []
for dx in (-0.006 * H, 0.0, 0.006 * H):
    for dy in (-0.02 * H, 0.0, 0.02 * H):
        o = Vector((dx, yl + dy, 0.33 * H)); h = bvh.ray_cast(o, Vector((0, 0, 1)), 0.4 * H)
        if h[0] is not None: hits.append(h[0].z)
hits.sort(); zc = hits[len(hits) // 2] if hits else 0.47 * H
print("crotch ray hits (z/H)", [round(z / H, 3) for z in hits])
def leg_c(z, side):
    ps = band(z - 0.01 * H, z + 0.01 * H, 0.0, 0.15 * H) if side > 0 else band(z - 0.01 * H, z + 0.01 * H, -0.15 * H, 0.0)
    return cen(ps)
hipz = zc + 0.045 * H
foot = [p for p in P if p.z < 0.06 * H]
toe_y = min(p.y for p in foot); heel_y = max(p.y for p in foot)
J = {}
for s, sg in (("l", 1), ("r", -1)):                                            # UE _l = +X in Blender's -Y-facing frame? see note
    # UE mannequin: _l bones sit on the character's left = Blender +X when facing -Y
    cth = leg_c(zc - 0.04 * H, sg); ck = leg_c(0.28 * H, sg); ca = leg_c(0.06 * H, sg)
    J["thigh_" + s] = Vector((cth.x, cth.y, hipz))
    J["calf_" + s] = Vector((ck.x, ck.y - 0.012 * H, 0.28 * H))
    J["foot_" + s] = Vector((ca.x, ca.y, 0.045 * H))
    J["ball_" + s] = Vector((ca.x, toe_y + 0.3 * (heel_y - toe_y), 0.012 * H))
    J["toe_" + s] = Vector((ca.x, toe_y, 0.008 * H))
    J["clavicle_" + s] = Vector((sg * 0.02 * H, ya, za + 0.005 * H))
    J["upperarm_" + s] = Vector((sg * xs * 0.92, ya, za))
    J["lowerarm_" + s] = Vector((sg * arm_pt(0.42), ya + 0.004 * H, za))
    J["hand_" + s] = Vector((sg * arm_pt(0.76), ya, za))
    J["handend_" + s] = Vector((sg * xf, ya, za))
def torso(z):
    """body centre at height z on the mid line: front skin hit, then the back skin from inside (long hair behind is ignored)"""
    c0 = cen(band(z - 0.01 * H, z + 0.01 * H, -0.09 * H, 0.09 * H))
    f = bvh.ray_cast(Vector((0, -2.0 * H, z)), Vector((0, 1, 0)), 4.0 * H)
    if f[0] is None: return c0
    b = bvh.ray_cast(f[0] + Vector((0, 0.003 * H, 0)), Vector((0, 1, 0)), 0.3 * H)
    yb = b[0].y if b[0] is not None else f[0].y + 0.1 * H
    return Vector((0, (f[0].y + yb) / 2, z))
J["pelvis"] = Vector((0, (J["thigh_l"].y + J["thigh_r"].y) / 2, hipz + 0.02 * H))   # (belts / buckles hang in front of the hips)
for i, f in enumerate((0.25, 0.5, 0.78)):
    z = J["pelvis"].z + f * (za - 0.02 * H - J["pelvis"].z); J[f"spine_0{i + 1}"] = Vector((0, torso(z).y, z))
J["neck_01"] = Vector((0, torso(za + 0.03 * H).y, za + 0.03 * H))
J["head"] = Vector((0, torso(za + 0.08 * H).y, za + 0.08 * H))
J["head_end"] = Vector((0, J["head"].y, H))
print("H", H, "arm z", round(za / H, 3), "fingertip", round(xf / H, 3), "armpit", round(xs / H, 3), "crotch", round(zc / H, 3))
for n_, v in J.items(): print("  ", n_, tuple(round(c * 100, 1) for c in v))
# ---- armature ----
ad = bpy.data.armatures.new("Armature"); arm = bpy.data.objects.new("Armature", ad); sc.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='EDIT')
eb = ad.edit_bones
def bone(n_, head, tail, parent=None, connect=False):
    b = eb.new(n_); b.head = head; b.tail = tail
    if parent: b.parent = eb[parent]; b.use_connect = connect
    return b
bone("root", (0, 0, 0), (0, 0.25, 0))
bone("pelvis", J["pelvis"], J["spine_01"], "root")
bone("spine_01", J["spine_01"], J["spine_02"], "pelvis")
bone("spine_02", J["spine_02"], J["spine_03"], "spine_01", True)
bone("spine_03", J["spine_03"], J["neck_01"], "spine_02", True)
bone("neck_01", J["neck_01"], J["head"], "spine_03", True)
bone("head", J["head"], J["head_end"], "neck_01", True)
for s in ("l", "r"):
    bone("clavicle_" + s, J["clavicle_" + s], J["upperarm_" + s], "spine_03")
    bone("upperarm_" + s, J["upperarm_" + s], J["lowerarm_" + s], "clavicle_" + s, True)
    bone("lowerarm_" + s, J["lowerarm_" + s], J["hand_" + s], "upperarm_" + s, True)
    bone("hand_" + s, J["hand_" + s], J["handend_" + s], "lowerarm_" + s, True)
    bone("thigh_" + s, J["thigh_" + s], J["calf_" + s], "pelvis")
    bone("calf_" + s, J["calf_" + s], J["foot_" + s], "thigh_" + s, True)
    bone("foot_" + s, J["foot_" + s], J["ball_" + s], "calf_" + s, True)
    bone("ball_" + s, J["ball_" + s], J["toe_" + s], "foot_" + s, True)
for b in eb:                                   # consistent rolls: limbs roll 0 about global Z, spine faces -Y
    b.roll = 0.0
bpy.ops.object.mode_set(mode='OBJECT')
# ---- centimetre rig first (bone heat is unreliable at metre scale) ----
sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 0.01
arm.scale = (100, 100, 100); mesh.scale = (100, 100, 100)
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); mesh.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
# ---- skin: region-gated distance weights (bone heat fails on Meshy's loose-shell meshes) ----
import numpy as np
C = 100.0                                                         # metres -> cm (landmarks were measured before the scale)
XS, ZA, ZC, HIPZ = xs * C, za * C, zc * C, hipz * C
co = np.array([v.co[:] for v in mesh.data.vertices])
segs = {b.name: (np.array(b.head_local[:]), np.array(b.tail_local[:])) for b in ad.bones if b.name != "root"}
def seg_dist(nm):
    a, b = segs[nm]; ab = b - a; t = np.clip(((co - a) @ ab) / max(ab @ ab, 1e-9), 0.0, 1.0)
    return np.linalg.norm(a + t[:, None] * ab - co, axis=1)
D = {nm: seg_dist(nm) for nm in segs}
x, z = co[:, 0], co[:, 2]
allowed = {nm: np.zeros(len(co), bool) for nm in segs}
y = co[:, 1]; YA = ya * C
near_arm = ((z - ZA < 16) & (ZA - z < 11) & (np.abs(y - YA) < 10)) | (np.abs(x) > XS * 1.6)   # arm cylinder: hair hanging beside the shoulder stays on the body
arm_l = (x > XS * 0.9) & (z > ZA - 18) & near_arm; arm_r = (x < -XS * 0.9) & (z > ZA - 18) & near_arm
dl = np.minimum.reduce([D[b + "_l"] for b in ("thigh", "calf", "foot", "ball")]); dr = np.minimum.reduce([D[b + "_r"] for b in ("thigh", "calf", "foot", "ball")])
side_l = dl <= dr                                                 # nearest leg (touching knees / feet cross x = 0) ...
# ... but whole mesh islands (a shoe, a sock, a strap) go to one leg: the islands' majority side, unless the island spans both legs
bm_ = bmesh.new(); bm_.from_mesh(mesh.data); bm_.verts.ensure_lookup_table()
seen_ = np.zeros(len(co), bool)
for v0 in bm_.verts:
    if seen_[v0.index]: continue
    isl = []; st_ = [v0]; seen_[v0.index] = True
    while st_:
        v = st_.pop(); isl.append(v.index)
        for e in v.link_edges:
            w_ = e.other_vert(v)
            if not seen_[w_.index]: seen_[w_.index] = True; st_.append(w_)
    isl = np.array(isl)
    if z[isl].max() < ZC + 4 and (x[isl].max() - x[isl].min()) < 14.0:
        side_l[isl] = side_l[isl].mean() >= 0.5
bm_.free()
leg_l = (z < ZC + 4) & side_l & ~arm_l; leg_r = (z < ZC + 4) & ~side_l & ~arm_r
body = ~(arm_l | arm_r | leg_l | leg_r)
for s, m in (("l", arm_l), ("r", arm_r)):
    for nm in ("upperarm_", "lowerarm_", "hand_"): allowed[nm + s] |= m
    allowed["clavicle_" + s] |= m & (np.abs(x) < XS * 1.4)
for s, m in (("l", leg_l), ("r", leg_r)):
    for nm in ("thigh_", "calf_", "foot_", "ball_"): allowed[nm + s] |= m
    allowed["pelvis"] |= m & (z > ZC - 6)
for nm in ("pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head"): allowed[nm] |= body
for s in ("l", "r"):
    allowed["clavicle_" + s] |= body & (z > ZA - 10) & ((x > 0) if s == "l" else (x < 0)) & (np.abs(x) > 3)
    allowed["upperarm_" + s] |= body & (z > ZA - 15) & (z < ZA + 16) & ((x > 0) if s == "l" else (x < 0)) & (np.abs(x) > XS * 0.65) & (np.abs(y - YA) < 12)   # deltoid blends into the arm
    allowed["thigh_" + s] |= body & (z < HIPZ + 6) & ((x >= 0) if s == "l" else (x < 0))
names = list(segs); W = np.zeros((len(co), len(names)))
for j, nm in enumerate(names): W[:, j] = np.where(allowed[nm], 1.0 / (D[nm] + 1.5) ** 4, 0.0)
order = np.argsort(-W, axis=1)
for i in range(len(co)):                                        # keep the 3 strongest, normalise
    keep = order[i, :3]; mask = np.zeros(len(names), bool); mask[keep] = True; W[i, ~mask] = 0.0
W /= np.maximum(W.sum(axis=1, keepdims=True), 1e-12)
mesh.vertex_groups.clear()
for j, nm in enumerate(names):
    vg = mesh.vertex_groups.new(name=nm)
    for val in np.unique(np.round(W[:, j], 3)):
        if val <= 0.001: continue
        idx = np.nonzero(np.round(W[:, j], 3) == val)[0].tolist(); vg.add(idx, float(val), 'REPLACE')
print("weighted verts", int((W.sum(axis=1) > 0.5).sum()), "of", len(co), "| arm", int(arm_l.sum() + arm_r.sum()), "leg", int(leg_l.sum() + leg_r.sum()), "body", int(body.sum()))
mesh.parent = arm; mesh.matrix_parent_inverse = Matrix.Identity(4)
am = mesh.modifiers.new("Armature", 'ARMATURE'); am.object = arm
print("pelvis z cm", round(ad.bones["pelvis"].head_local.z, 1), "bones", len(ad.bones))
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); mesh.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(filepath=os.path.join(out, name + ".fbx"), use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                         bake_anim=False, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', use_armature_deform_only=False,
                         mesh_smooth_type='FACE', use_tspace=True, path_mode='COPY', embed_textures=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, name + "_rig.blend"))
print("EXPORT DONE", os.path.join(out, name + ".fbx"))
