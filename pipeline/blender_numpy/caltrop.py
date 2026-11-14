"""A caltrop for the Rogue's Caltrops art (the user's list of 2026-11-12, docs/improvements12.txt, its seventh phase: "Real iron spike
meshes on the floor, no glow"): four tapered square spikes from one middle along a tetrahedron's corners, so one always stands up
whichever way it lands; 7 cm across, its base the lowest three points' plane. Written as an FBX (Blender's units: the scene in
metres, scale_length 1) for 925 to import.
blender -b -P pipeline/blender_numpy/caltrop.py -- <out dir>"""
import bpy, bmesh, sys, os, math
from mathutils import Vector

out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else os.path.abspath("caltrop_out")
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bm = bmesh.new()
L, W = 0.042, 0.0055          # (a spike's length and its root's half width, metres)
# (a tetrahedron's corners: one straight up, three below round it)
ups = [Vector((0, 0, 1))]
for k in range(3):
    a = 2 * math.pi * k / 3
    ups.append(Vector((math.cos(a) * math.sqrt(8 / 9), math.sin(a) * math.sqrt(8 / 9), -1 / 3)))
for d in ups:
    d = d.normalized()
    side = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))).normalized()
    up2 = d.cross(side).normalized()
    root = [bm.verts.new(side * sx * W + up2 * sy * W) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    tip = bm.verts.new(d * L)
    for i in range(4): bm.faces.new((root[i], root[(i + 1) % 4], tip))
    bm.faces.new(tuple(reversed(root)))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("SM_RD_Caltrop"); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("SM_RD_Caltrop", me); bpy.context.scene.collection.objects.link(ob)
# (its base on the ground: the three lower tips' plane at z 0)
low = min(v.co.z for v in me.vertices)
for v in me.vertices: v.co.z -= low
for p in me.polygons: p.use_smooth = False
mat = bpy.data.materials.new("M_RD_CaltropIron"); me.materials.append(mat)
bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True); bpy.context.view_layer.objects.active = ob
path = os.path.join(out, "SM_RD_Caltrop.fbx")
bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS", mesh_smooth_type="FACE", add_leaf_bones=False)
print("CALTROP", path, len(me.vertices), "verts", round(max(v.co.z for v in me.vertices) * 100, 2), "cm tall")
