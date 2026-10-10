"""Stage 1 of the outfit refit (Blender): pose fig4's MetaHuman armature into the scan's stance
and dump the posed body + skinning data.

Pose: lift by the heel offset, arms to the scan's T-pose, legs along the scan's leg centre line,
feet plantar-flexed so the ball of the foot sits on the shoe's forefoot, toes flat.
Dumps: posed body verts/normals, body skin weights (top 4, bone indices), per-bone skinning
matrices (posed_world @ rest_world^-1), bone names, and the foot/ball local rotations.
Blender: -- body.fbx scan_body_target.npz shoes.glb out.npz out_pose.json"""
import bpy, sys, json, numpy as np
from mathutils import Matrix, Vector, Quaternion

argv = sys.argv[sys.argv.index("--") + 1:]
BODY_FBX, SCAN_NPZ, SHOES_GLB, OUT_NPZ, OUT_JSON = argv[:5]
HEAD_OFFSET = Vector((0.0, -0.006, 0.169))      # MetaHuman -> scan (nose-tip alignment)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SHOES_GLB)
shoe = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
SH = np.array([shoe.matrix_world @ v.co for v in shoe.data.vertices])
bpy.data.objects.remove(shoe)
bpy.ops.import_scene.fbx(filepath=BODY_FBX)
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
body = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
S = np.load(SCAN_NPZ)["co"]

bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')
pb = arm.pose.bones
AW = arm.matrix_world.copy(); AWi = AW.inverted()

def head_w(n): return AW @ pb[n].head
def rotate_world(n, q):
    b = pb[n]; M = b.matrix.copy(); h = M.translation.copy()
    R = (AWi.to_3x3() @ q.to_matrix() @ AW.to_3x3()).to_4x4()
    b.matrix = Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ M
    bpy.context.view_layer.update()
def aim(n, child, d):
    cur = (head_w(child) - head_w(n)).normalized()
    rotate_world(n, cur.rotation_difference(Vector(d).normalized()))
def line_dir(p):
    c = p.mean(0); return np.linalg.svd(p - c)[2][0]

# lift so a realistic stiletto foot (~58 deg plantar flexion) puts the ball on the sole
foot_len = (head_w("ball_l") - head_w("foot_l")).length
LIFT = 0.028 + foot_len * 0.85 - head_w("foot_l").z
print("foot length", round(foot_len, 3), "lift", round(LIFT, 3))
pel = pb["pelvis"]
pel.matrix = Matrix.Translation(AWi.to_3x3() @ Vector((0, 0, LIFT))) @ pel.matrix
bpy.context.view_layer.update()

for side, sg in (("l", 1), ("r", -1)):
    ua = S[(sg * S[:, 0] > 0.24) & (sg * S[:, 0] < 0.44) & (S[:, 2] > 1.25)]
    fa = S[(sg * S[:, 0] > 0.47) & (sg * S[:, 0] < 0.66) & (S[:, 2] > 1.25)]
    du = line_dir(ua); df = line_dir(fa)
    du = du if du[0] * sg > 0 else -du; df = df if df[0] * sg > 0 else -df
    aim(f"upperarm_{side}", f"lowerarm_{side}", du)
    aim(f"lowerarm_{side}", f"hand_{side}", df)

import math
foot_pose = {}
for side in ("l", "r"):
    # pitch the foot about its lateral axis until the ball of the foot reaches the sole (z 0.028)
    a = head_w(f"foot_{side}"); b0 = head_w(f"ball_{side}")
    fwd = Vector((b0.x - a.x, b0.y - a.y, 0)).normalized()
    lat = Vector((0, 0, 1)).cross(fwd).normalized()      # positive rotation tips the toes down
    lo, hi = 0.0, math.radians(80)
    base = pb[f"foot_{side}"].matrix.copy()
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        pb[f"foot_{side}"].matrix = base; bpy.context.view_layer.update()
        rotate_world(f"foot_{side}", Quaternion(lat, mid))
        if head_w(f"ball_{side}").z > 0.028: lo = mid
        else: hi = mid
    # toes flat on the sole
    b = head_w(f"ball_{side}"); t = AW @ pb[f"ball_{side}"].tail
    cur = (t - b).normalized(); flat = Vector((cur.x, cur.y, 0.0)).normalized()
    rotate_world(f"ball_{side}", cur.rotation_difference(flat))
    print(side, "foot pitch", round(math.degrees(0.5 * (lo + hi)), 1), "ankle", [round(c, 3) for c in head_w(f"foot_{side}")],
          "ball", [round(c, 3) for c in head_w(f"ball_{side}")])
for n in ("foot_l", "ball_l", "foot_r", "ball_r"):
    foot_pose[n] = list(pb[n].matrix_basis.to_quaternion())

bpy.ops.object.mode_set(mode='OBJECT')
dg = bpy.context.evaluated_depsgraph_get()
be = body.evaluated_get(dg); me = be.to_mesh()
BW = np.array(body.matrix_world)
Pb = np.array([v.co for v in me.vertices]) @ BW[:3, :3].T + BW[:3, 3]
Nb = np.array([v.normal for v in me.vertices]) @ BW[:3, :3].T
Nb /= np.linalg.norm(Nb, axis=1, keepdims=True) + 1e-9
be.to_mesh_clear()

bones = [b.name for b in arm.data.bones]; bi = {n: i for i, n in enumerate(bones)}
gn = [g.name for g in body.vertex_groups]
nv = len(body.data.vertices)
Wi = np.zeros((nv, 4), int); Ww = np.zeros((nv, 4))
for v in body.data.vertices:
    gs = sorted(((g.weight, bi[gn[g.group]]) for g in v.groups if gn[g.group] in bi), reverse=True)[:4]
    s = sum(w for w, _ in gs) or 1.0
    for k, (w, b) in enumerate(gs):
        Ww[v.index, k] = w / s; Wi[v.index, k] = b
# skinning matrices in world space: posed_world @ rest_world^-1
SK = np.zeros((len(bones), 4, 4))
for i, n in enumerate(bones):
    rest = AW @ arm.data.bones[n].matrix_local
    posed = AW @ pb[n].matrix
    SK[i] = np.array(posed @ rest.inverted())
J = {n: list(head_w(n)) for n in ("foot_l", "ball_l", "foot_r", "ball_r", "neck_01", "head", "spine_05", "pelvis")}
np.savez(OUT_NPZ, posed=Pb, normals=Nb, wi=Wi, ww=Ww, skin=SK, bones=np.array(bones), lift=LIFT,
         joints=json.dumps(J))
json.dump({"lift": LIFT, "rotations": foot_pose}, open(OUT_JSON, "w"), indent=1)
print("POSE dumped", len(Pb), "verts,", len(bones), "bones; posed z", Pb[:, 2].min().round(3), Pb[:, 2].max().round(3))
