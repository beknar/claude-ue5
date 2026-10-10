"""Render a front portrait of the full fig4 scan with a known pinhole camera, for MetaHuman
face landmark tracking. Blender world space (meters, Z up, she faces -Y).
Blender: -b -P render_portrait.py -- scan.glb out.png cam_x cam_y cam_z hfov_deg size"""
import bpy, sys, math, mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[0], argv[1]
cam_pos = mathutils.Vector(map(float, argv[2:5])); hfov = float(argv[5]); size = int(argv[6])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys() else 'BLENDER_EEVEE'
sc.render.resolution_x = sc.render.resolution_y = size
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.75, 0.75, 0.75, 1); bg.inputs[1].default_value = 0.9
for rot, e in (((math.radians(60), 0, math.radians(-25)), 2.0), ((math.radians(70), 0, math.radians(30)), 0.8)):
    l = bpy.data.objects.new("l", bpy.data.lights.new("l", 'SUN')); l.data.energy = e
    l.rotation_euler = rot; sc.collection.objects.link(l)
cd = bpy.data.cameras.new("cam"); cd.sensor_fit = 'HORIZONTAL'; cd.angle = math.radians(hfov)
cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
cam.location = cam_pos
cam.rotation_euler = mathutils.Vector((0, 1, 0)).to_track_quat('-Z', 'Z').to_euler()   # look along +Y, Z up
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("PORTRAIT", out, tuple(cam_pos), hfov)
