import bpy, sys, math, mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
src, out_prefix = argv[0], argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys() else 'BLENDER_EEVEE'
scene.render.resolution_x = 900
scene.render.resolution_y = 1400
world = bpy.data.worlds.new("w"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
world.node_tree.nodes["Background"].inputs[0].default_value = (0.8, 0.8, 0.8, 1)

# bounds in world space
mins = mathutils.Vector((1e9,)*3); maxs = mathutils.Vector((-1e9,)*3)
for o in objs:
    for c in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(c)
        mins = mathutils.Vector(map(min, mins, w)); maxs = mathutils.Vector(map(max, maxs, w))
center = (mins + maxs) / 2
print("BOUNDS", tuple(mins), tuple(maxs))

cam_data = bpy.data.cameras.new("cam"); cam_data.type = 'ORTHO'
cam_data.ortho_scale = max(maxs.z - mins.z, maxs.x - mins.x) * 1.05
cam = bpy.data.objects.new("cam", cam_data); scene.collection.objects.link(cam); scene.camera = cam
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", 'SUN')); scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0, math.radians(20))

def shoot(name, direction, ortho=None, tgt=None):
    tgt = tgt or center
    cam.location = tgt + direction * 5
    cam.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
    if ortho: cam_data.ortho_scale = ortho
    scene.render.filepath = f"{out_prefix}_{name}.png"
    bpy.ops.render.render(write_still=True)

full = max(maxs.z - mins.z, maxs.x - mins.x) * 1.05
shoot("front", mathutils.Vector((0, -1, 0)), full)
shoot("side", mathutils.Vector((1, 0, 0)), full)
shoot("back", mathutils.Vector((0, 1, 0)), full)
head = mathutils.Vector((center.x, center.y, maxs.z - (maxs.z - mins.z) * 0.07))
shoot("face", mathutils.Vector((0, -1, 0)), (maxs.z - mins.z) * 0.16, head)
