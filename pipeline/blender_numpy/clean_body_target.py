"""Remove the stray 'skin' fragments (texture-mislabeled hair) floating around fig4's head in
the conform target: on the head, keep only the face/ears/neck and what lies near the skull.
Blender: -b -P clean_body_target.py -- in.glb out.glb"""
import bpy, bmesh, sys, numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
C = np.array([0.0, -0.010, 1.600]); R = np.array([0.083, 0.103, 0.112])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(obj.data)
mw = obj.matrix_world
dead = []
for v in bm.verts:
    p = np.array(mw @ v.co)
    if p[2] < 1.47: continue
    # Keep only the clean front of the face (below the swept bangs, inside the temples) and
    # the neck; the cranium, temples and ears are hair-covered, so the MetaHuman prior fills them.
    face = (p[1] < C[1] - 0.025) and (p[2] < 1.66) and (abs(p[0]) < 0.068)
    neck = p[2] < 1.53 and np.hypot(p[0], p[1] - 0.0) < 0.068
    if not (face or neck):
        dead.append(v)
bmesh.ops.delete(bm, geom=dead, context='VERTS')
bm.to_mesh(obj.data); bm.free()
print("CLEANED removed", len(dead), "head verts; left", len(obj.data.vertices))

# Fill the hair-covered cranium with a skull ellipsoid so the conform sees a complete head.
# The ellipsoid is least-squares fitted to the face's edge (forehead top, temples) and to the
# hair shell pulled in by its thickness, so it meets the face without a step.
import mathutils
HAIR_NPZ = argv[2]
mw = obj.matrix_world
fv = np.array([mw @ v.co for v in obj.data.vertices])
edge = fv[(fv[:, 2] > 1.47) & (fv[:, 1] < C[1] - 0.02) &
          ((fv[:, 2] > 1.615) | ((np.abs(fv[:, 0]) > 0.056) & (fv[:, 2] > 1.53)))]
hs = np.load(HAIR_NPZ)["co"]
hs = hs[(hs[:, 2] > 1.50) & ((hs[:, 2] > 1.64) | (hs[:, 1] > C[1] + 0.02))]
d = hs - C; n = np.linalg.norm(d, axis=1, keepdims=True)
hs = hs - d / n * 0.014                                    # hair thickness
rng = np.random.default_rng(0)
hs = hs[rng.choice(len(hs), min(len(hs), 6000), replace=False)]
pts = np.vstack([np.repeat(edge, max(1, len(hs) // max(len(edge), 1)), axis=0), hs])
# constrained fit: head proportions R fixed; search uniform scale s and centre offsets dy, dz
best = None
for s in np.linspace(0.85, 0.93, 9):            # realistic adult female skull sizes
    for dy in np.linspace(-0.02, 0.02, 21):
        for dz in np.linspace(-0.02, 0.02, 21):
            c0 = C + [0, dy, dz]
            r = np.linalg.norm((pts - c0) / (R * s), axis=1)
            err = np.mean((r - 1) ** 2)
            if best is None or err < best[0]: best = (err, s, dy, dz)
_, s, dy, dz = best
SK = R * s; SC = C + [0, dy, dz]
print("SKULL fit centre", SC.round(4), "radii", SK.round(4), "edge pts", len(edge))
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=96, radius=1.0)
sk = bpy.context.active_object
sk.scale = tuple(SK); sk.location = tuple(SC)
bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
kd = mathutils.kdtree.KDTree(len(fv))
for i, p in enumerate(fv): kd.insert(p, i)
kd.balance()
bm = bmesh.new(); bm.from_mesh(sk.data)
drop = [v for v in bm.verts if v.co.z < 1.50 or kd.find(v.co)[2] < 0.006
        or ((v.co.y < SC[1] - 0.03) and (v.co.z < 1.62) and abs(v.co.x) < 0.07)]
bmesh.ops.delete(bm, geom=drop, context='VERTS')
# Blend the skull into the face: near the face edge, move each skull point along its radius
# to the radius of the nearest face point, fading out over BLEND metres.
BLEND = 0.05
head_face = fv[(fv[:, 2] > 1.50) & (fv[:, 1] < SC[1] - 0.01)]
kf = mathutils.kdtree.KDTree(len(head_face))
for i, p in enumerate(head_face): kf.insert(p, i)
kf.balance()
scv = mathutils.Vector(tuple(SC))
for v in bm.verts:
    co, idx, d = kf.find(v.co)
    if d > BLEND: continue
    w = (1 - d / BLEND) ** 2 * (3 - 2 * 0) if False else (1 - d / BLEND) ** 1.5
    dirv = (v.co - scv); r_sk = dirv.length; dirv.normalize()
    r_face = (co - scv).dot(dirv)
    v.co = scv + dirv * (r_sk + (r_face - r_sk) * w)
bm.to_mesh(sk.data); bm.free()
for o in bpy.context.scene.objects: o.select_set(o in (obj, sk))
bpy.context.view_layer.objects.active = obj
bpy.ops.object.join()
print("SKULL added; total", len(obj.data.vertices))
bpy.ops.export_scene.gltf(filepath=argv[1], export_format='GLB')
