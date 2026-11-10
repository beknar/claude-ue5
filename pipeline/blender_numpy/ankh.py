"""The ankh, the revealing light (the user's list of 2026-11-10: "new type of item that can be held in the left hand and put in the
quick slot: revealing light, looks like an ankh ... new model needed for this in blender"): a metal ankh about 27 cm tall, a
teardrop loop over a flared crossbar over a tapering shaft, its edges bevelled. Its frame is the torch's (the held light's fit is
the torch's grip): its long axis +Z, its grip (a quarter of the way up the shaft) at the origin, so 914's ankh step gives it each
hero's torch grip moved by nothing. One material slot ("Ankh"; 914 makes its metal). Writes <out>/SM_RD_Ankh.fbx and ankh.json.
Blender: blender -b -P ankh.py -- <out_dir>"""
import bpy, bmesh, json, math, os, sys
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else os.getcwd()
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)

# (metres: the shaft from -0.065 under the grip to the crossbar at 0.085; the loop over it to 0.205)
SHAFT_LO, SHAFT_HI = -0.065, 0.085
BAR_Z, BAR_HALF, BAR_T = 0.095, 0.075, 0.022
LOOP_C, LOOP_RX, LOOP_RZ, LOOP_T = 0.15, 0.042, 0.055, 0.016

bm = bmesh.new()
# the shaft: a tapering eight-sided column, wider at its foot, a flare at the bottom
segs = 8
def ring(z, r, rot=0.0):
    return [bm.verts.new((r * math.cos(2 * math.pi * k / segs + rot), r * math.sin(2 * math.pi * k / segs + rot) * 0.8, z)) for k in range(segs)]
rings = [ring(SHAFT_LO, 0.019), ring(SHAFT_LO + 0.008, 0.016), ring(0.0, 0.0125), ring(SHAFT_HI, 0.0105)]
for a, b in zip(rings, rings[1:]):
    for k in range(segs): bm.faces.new((a[k], a[(k + 1) % segs], b[(k + 1) % segs], b[k]))
bm.faces.new(list(reversed(rings[0])))
# the crossbar: a box flaring toward its ends (each arm a frustum)
def frustum(c0, c1, r0, r1, ax):
    """a square frustum from c0 (half size r0) to c1 (half size r1) along ax"""
    o = [Vector((0, 1, 0)), Vector((0, 0, 1))] if ax == "x" else [Vector((1, 0, 0)), Vector((0, 1, 0))]
    def sq(c, r):
        return [bm.verts.new(c + (o[0] * sx + o[1] * sz) * r) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    a, b = sq(c0, r0), sq(c1, r1)
    for k in range(4): bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    bm.faces.new(list(reversed(a))); bm.faces.new(b)
frustum(Vector((0, 0, BAR_Z)), Vector((BAR_HALF, 0, BAR_Z)), BAR_T * 0.5, BAR_T * 0.75, "x")
frustum(Vector((0, 0, BAR_Z)), Vector((-BAR_HALF, 0, BAR_Z)), BAR_T * 0.5, BAR_T * 0.75, "x")
# the loop: a teardrop ring (an ellipse, narrower at its foot), a tube round it
N, M = 40, 8
pts = []
for i in range(N):
    t = 2 * math.pi * i / N
    x = LOOP_RX * math.sin(t) * (0.75 + 0.25 * (1 - math.cos(t)) / 2 * 1.6)
    z = LOOP_C - LOOP_RZ * math.cos(t)
    pts.append(Vector((x, 0, z)))
tube = []
for i in range(N):
    p = pts[i]; tng = (pts[(i + 1) % N] - pts[i - 1]).normalized(); nrm = tng.cross(Vector((0, 1, 0))).normalized(); bnm = Vector((0, 1, 0))
    tube.append([bm.verts.new(p + (nrm * math.cos(2 * math.pi * k / M) + bnm * math.sin(2 * math.pi * k / M) * 0.7) * LOOP_T) for k in range(M)])
for i in range(N):
    a, b = tube[i], tube[(i + 1) % N]
    for k in range(M): bm.faces.new((a[k], a[(k + 1) % M], b[(k + 1) % M], b[k]))
me = bpy.data.meshes.new("SM_RD_Ankh"); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("SM_RD_Ankh", me); bpy.context.scene.collection.objects.link(ob)
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
mat = bpy.data.materials.new("Ankh"); me.materials.append(mat)
# (smooth, a bevel on the edges, normals outward, UVs by a smart projection)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.uv.smart_project(angle_limit=math.radians(60)); bpy.ops.object.mode_set(mode='OBJECT')
bev = ob.modifiers.new("bevel", 'BEVEL'); bev.width = 0.0015; bev.segments = 2; bev.limit_method = 'ANGLE'
bpy.ops.object.modifier_apply(modifier="bevel")
tri = ob.modifiers.new("tri", 'TRIANGULATE'); bpy.ops.object.modifier_apply(modifier="tri")          # (the caps' n-gons: no tangents for them)
bpy.ops.object.shade_smooth()
for p in me.polygons: p.use_smooth = True
zs = [v.co.z for v in me.vertices]; xs = [v.co.x for v in me.vertices]
info = {"height_m": round(max(zs) - min(zs), 3), "width_m": round(max(xs) - min(xs), 3), "z": [round(min(zs), 3), round(max(zs), 3)], "verts": len(me.vertices), "faces": len(me.polygons)}
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "SM_RD_Ankh.fbx"), use_selection=True, object_types={'MESH'}, apply_unit_scale=True,
                         apply_scale_options='FBX_SCALE_ALL', mesh_smooth_type='FACE', use_tspace=True, add_leaf_bones=False)
json.dump(info, open(os.path.join(OUT, "ankh.json"), "w"), indent=1)
# (a preview: front and side, metal-ish)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.render.resolution_x = sc.render.resolution_y = 512
mat.diffuse_color = (0.85, 0.66, 0.3, 1); sc.display.shading.color_type = 'MATERIAL'
cd = bpy.data.cameras.new("c"); cd.type = 'ORTHO'; cd.ortho_scale = 0.34; cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
for nm, d in (("front", Vector((0, -1, 0))), ("side", Vector((1, 0, 0))), ("three_quarter", Vector((0.6, -0.8, 0.2)).normalized())):
    cam.location = Vector((0, 0, 0.078)) + d; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, f"ankh_preview_{nm}.png"); bpy.ops.render.render(write_still=True)
print("ANKH", json.dumps(info))
