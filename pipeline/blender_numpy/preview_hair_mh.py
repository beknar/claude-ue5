"""Render strands over the MetaHuman (FBX face+body). Blender: -- face.fbx body.fbx strands.npz out_prefix [max]"""
import bpy, sys, numpy as np, mathutils
argv = sys.argv[sys.argv.index("--") + 1:]
face, body, snpz, outp = argv[:4]; maxn = int(argv[4]) if len(argv) > 4 else 12000
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=face); bpy.ops.import_scene.fbx(filepath=body)
skin = bpy.data.materials.new("skin"); skin.diffuse_color = (0.85, 0.7, 0.62, 1)
for o in bpy.context.scene.objects:
    if o.type == 'MESH':
        o.data.materials.clear(); o.data.materials.append(skin)
S = np.load(snpz)["strands"]
if len(S) > maxn: S = S[np.random.default_rng(0).choice(len(S), maxn, replace=False)]
n, p, _ = S.shape
cu = bpy.data.curves.new("hair", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.00035
for s in S:
    sp = cu.splines.new('POLY'); sp.points.add(p - 1)
    sp.points.foreach_set("co", np.concatenate([s, np.ones((p, 1))], 1).ravel())
ob = bpy.data.objects.new("hair", cu); bpy.context.scene.collection.objects.link(ob)
m = bpy.data.materials.new("h"); m.diffuse_color = (0.03, 0.03, 0.035, 1); cu.materials.append(m)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.light = 'STUDIO'
sc.render.resolution_x, sc.render.resolution_y = 800, 1000
cd = bpy.data.cameras.new("c"); cd.type = 'ORTHO'; cd.ortho_scale = 0.8
cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
tgt = mathutils.Vector((0, 0, 1.22))
for name, d in (("front", (0, -1, 0)), ("back", (0, 1, 0)), ("side", (1, 0, 0)), ("q", (0.7, -0.7, 0.15))):
    dv = mathutils.Vector(d).normalized()
    cam.location = tgt + dv * 3
    cam.rotation_euler = (-dv).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f"{outp}_{name}.png"
    bpy.ops.render.render(write_still=True)
