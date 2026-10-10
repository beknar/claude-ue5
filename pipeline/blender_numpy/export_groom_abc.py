"""Write strands (npz 'strands' (n,p,3), Blender meters Z-up) to an Alembic groom for Unreal.
Blender: -b -P export_groom_abc.py -- strands.npz out.abc
The curves are exported in centimetres (global_scale 100); Alembic is Y-up, which the Unreal
groom importer converts back to Z-up with its default (90, 0, 0) rotation."""
import bpy, sys, numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
S = np.load(argv[0])["strands"]
bpy.ops.wm.read_factory_settings(use_empty=True)
n, p, _ = S.shape
cu = bpy.data.curves.new("fig4_hair", 'CURVE'); cu.dimensions = '3D'
cu.splines.new('POLY')
for i in range(n - 1): cu.splines.new('POLY')
coords = np.concatenate([S, np.ones((n, p, 1), np.float32)], 2)
# Unreal reads the Alembic width as 2 x Blender's point radius, unscaled, in cm:
# radius 0.004 -> 0.008 cm (80 um) at the root, tapering to 30 % at the tip
radius = (0.004 * np.linspace(1.0, 0.3, p)).astype(np.float32)
for i, sp in enumerate(cu.splines):
    sp.points.add(p - 1)
    sp.points.foreach_set("co", coords[i].ravel())
    sp.points.foreach_set("radius", radius)
ob = bpy.data.objects.new("fig4_hair", cu); bpy.context.scene.collection.objects.link(ob)
ob.select_set(True); bpy.context.view_layer.objects.active = ob
bpy.ops.wm.alembic_export(filepath=argv[1], selected=True, global_scale=100.0, start=1, end=1,
                          export_hair=False, export_particles=False, evaluation_mode='RENDER')
print("ABC", argv[1], n, "strands", p, "points each")
