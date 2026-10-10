"""Sole contact points of the FF2 shoes (rest pose, UE coordinates in cm): heel and toe of each foot, taken from the
lowest vertices skinned mainly to foot_/ball_. UE (x, y, z) = Blender (x, -y, z) for this rig.
Blender: -b -P ff2_soles.py -- model.glb out.json"""
import bpy, sys, json
argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[0], argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
me = next(o for o in sc.objects if o.type == 'MESH' and o.vertex_groups)
ad = arm.animation_data
if ad:
    ad.action = None
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
zs = [(me.matrix_world @ v.co).z for v in me.data.vertices]; S = 165.0 / (max(zs) - min(zs))
gi = {g.index: g.name for g in me.vertex_groups}
res = {}
for side in ("l", "r"):
    names = {f"foot_{side}", f"ball_{side}"}
    pts = []
    for v in me.data.vertices:
        w = {gi[g.group]: g.weight for g in v.groups}
        if sum(w.get(n, 0) for n in names) > 0.6:
            p = me.matrix_world @ v.co; pts.append((p.x * S, -p.y * S, p.z * S))     # -> UE coordinates
    zmin = min(p[2] for p in pts)
    sole = [p for p in pts if p[2] < zmin + 1.5]
    heel = max(sole, key=lambda p: -p[1]); toe = max(sole, key=lambda p: p[1])          # UE +Y is forward
    # average a few neighbours for stability
    def near(c): q = [p for p in sole if abs(p[1] - c[1]) < 2.0]; return [sum(a[i] for a in q) / len(q) for i in range(3)]
    res[side] = {"heel": near(heel), "toe": near(toe), "n_sole": len(sole), "zmin": zmin}
    print(side, {k: [round(x, 2) for x in v] if isinstance(v, list) else v for k, v in res[side].items()})
json.dump(res, open(out, "w"), indent=1)
