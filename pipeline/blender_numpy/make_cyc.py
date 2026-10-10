"""Model a photo-studio cyclorama (floor curving up into the back wall) and a round plinth.
Exported as glb in metres (Blender: she faces -Y, so the backdrop is at +Y behind her).
Blender: -b -P make_cyc.py -- out_dir"""
import bpy, bmesh, sys, math
out = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)

W, DEPTH, R, H = 12.0, 7.0, 2.2, 6.0      # width, floor depth in front of the curve, cove radius, wall height
BACK = 2.5                               # y where the cove starts (behind her)
bm = bmesh.new()
profile = []                             # (y, z) along the floor -> cove -> wall
for i in range(41):                      # floor
    profile.append((-DEPTH + (BACK + DEPTH) * i / 40, 0.0))
for i in range(1, 33):                   # quarter-circle cove
    a = (math.pi / 2) * i / 32
    profile.append((BACK + R * math.sin(a), R - R * math.cos(a)))
for i in range(1, 21):                   # wall
    profile.append((BACK + R, R + (H - R) * i / 20))
cols = 81
rows = []
for (y, z) in profile:
    rows.append([bm.verts.new((-W / 2 + W * c / (cols - 1), y, z)) for c in range(cols)])
for r in range(len(rows) - 1):
    for c in range(cols - 1):
        bm.faces.new((rows[r][c], rows[r][c + 1], rows[r + 1][c + 1], rows[r + 1][c]))
# UVs: u = x, v = arc length along the profile, both in 2 m tiles (seamless concrete)
arc = [0.0]
for k in range(1, len(profile)):
    arc.append(arc[-1] + math.dist(profile[k], profile[k - 1]))
uvl = bm.loops.layers.uv.new("UVMap")
row_of = {v: (r, c) for r, row in enumerate(rows) for c, v in enumerate(row)}
for f in bm.faces:
    for loop in f.loops:
        r, c = row_of[loop.vert]
        loop[uvl].uv = ((-W / 2 + W * c / (cols - 1)) / 2.0, arc[r] / 2.0)
me = bpy.data.meshes.new("SM_Cyclorama"); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
cyc = bpy.data.objects.new("SM_Cyclorama", me); bpy.context.scene.collection.objects.link(cyc)
cyc.select_set(True); bpy.context.view_layer.objects.active = cyc
bpy.ops.export_scene.gltf(filepath=f"{out}/SM_Cyclorama.glb", export_format='GLB', use_selection=True)

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=0.75, depth=0.06, location=(0, 0, 0.03))
pl = bpy.context.active_object; pl.name = "SM_Plinth"; pl.data.name = "SM_Plinth"
bev = pl.modifiers.new("bevel", 'BEVEL'); bev.width = 0.012; bev.segments = 4; bev.limit_method = 'ANGLE'
bpy.ops.object.modifier_apply(modifier="bevel")
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(island_margin=0.01); bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.export_scene.gltf(filepath=f"{out}/SM_Plinth.glb", export_format='GLB', use_selection=True)
print("CYC done")
