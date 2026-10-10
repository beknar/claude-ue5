"""Render strands (npz 'strands' (n,p,3)) over the body target. Blender:
-b -P preview_hair.py -- body.glb strands.npz out_prefix [max_strands]"""
import bpy, sys, math, numpy as np, mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
body, snpz, outp = argv[:3]
maxn = int(argv[3]) if len(argv) > 3 else 15000
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=body)
S = np.load(snpz)["strands"]
if len(S) > maxn: S = S[np.random.default_rng(0).choice(len(S), maxn, replace=False)]
n, p, _ = S.shape
cu = bpy.data.curves.new("hair", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0004
for s in S:
    sp = cu.splines.new('POLY'); sp.points.add(p - 1)
    sp.points.foreach_set("co", np.concatenate([s, np.ones((p, 1))], 1).ravel())
ob = bpy.data.objects.new("hair", cu); bpy.context.scene.collection.objects.link(ob)
m = bpy.data.materials.new("h"); m.diffuse_color = (0.05, 0.25, 0.9, 1); cu.materials.append(m)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x, sc.render.resolution_y = 800, 1000
cd = bpy.data.cameras.new("c"); cd.type = 'ORTHO'; cd.ortho_scale = 0.75
cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
tgt = mathutils.Vector((0, 0, 1.38))
for name, d in (("front", (0, -1, 0)), ("back", (0, 1, 0)), ("side", (1, 0, 0)), ("top", (0.0001, 0, 1))):
    dv = mathutils.Vector(d).normalized()
    cam.location = tgt + dv * 3
    cam.rotation_euler = (-dv).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f"{outp}_{name}.png"
    bpy.ops.render.render(write_still=True)
