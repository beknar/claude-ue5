"""Render the MetaHuman body+face (FBX) next to/over the scan for a sanity check.
Blender: -- body.fbx face.fbx scan.glb out_prefix"""
import bpy, sys, math, mathutils
argv = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=argv[0]); bpy.ops.import_scene.fbx(filepath=argv[1])
mh = [o for o in bpy.context.scene.objects if o.type == 'MESH']
bpy.ops.import_scene.gltf(filepath=argv[2])
scan = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o not in mh]
red = bpy.data.materials.new("mh"); red.diffuse_color = (0.9, 0.5, 0.4, 1)
grey = bpy.data.materials.new("scan"); grey.diffuse_color = (0.3, 0.5, 0.9, 0.35)
for o in mh:
    o.data.materials.clear(); o.data.materials.append(red)
for o in scan:
    o.data.materials.clear(); o.data.materials.append(grey)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.show_xray = False
sc.render.resolution_x, sc.render.resolution_y = 700, 1100
cd = bpy.data.cameras.new("c"); cd.type = 'ORTHO'; cd.ortho_scale = 1.9
cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
tgt = mathutils.Vector((0, 0, 0.88))
for name, d, hide_scan in (("front", (0, -1, 0), True), ("side", (1, 0, 0), True), ("side_overlay", (1, 0, 0), False), ("front_overlay", (0, -1, 0), False)):
    for o in scan: o.hide_render = hide_scan
    for o in mh: o.location.x = 0
    dv = mathutils.Vector(d)
    cam.location = tgt + dv * 4
    cam.rotation_euler = (-dv).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f"{argv[3]}_{name}.png"
    bpy.ops.render.render(write_still=True)
