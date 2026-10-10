"""Stage 3 of the outfit refit (Blender): build the skinned outfit on the MetaHuman armature in
its bind pose, export FBX (armature + outfit), and render a check over the bind-pose body.
Blender: -- body.fbx parts_dir outfit_fit.npz out.fbx preview_prefix"""
import bpy, sys, os, numpy as np, mathutils
argv = sys.argv[sys.argv.index("--") + 1:]
BODY_FBX, PARTS, FIT, OUT_FBX, PREV = argv[:5]
F = np.load(FIT); bones = [str(b) for b in F["bones"]]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=BODY_FBX)
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
body = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
arm.name = "Armature"
objs = []
# stockings: a shell over the MetaHuman's own legs (exact skin weights), toes to mid-thigh.
# UV1 = body UVs; UV2: u = around the leg, v = metres below the lace top (lace band in the material).
STOCK_TOP = 0.60
st = body.copy(); st.data = body.data.copy(); bpy.context.scene.collection.objects.link(st)
st.modifiers.clear()
for x in bpy.context.scene.objects: x.select_set(x == st)
bpy.context.view_layer.objects.active = st
import bmesh
bm = bmesh.new(); bm.from_mesh(st.data)
mw = st.matrix_world
dead = [v for v in bm.verts if (mw @ v.co).z > STOCK_TOP]
bmesh.ops.delete(bm, geom=dead, context='VERTS')
bm.normal_update()
inv = mw.inverted().to_3x3()
for v in bm.verts:
    wn = (mw.to_3x3() @ v.normal).normalized()
    lace = (mw @ v.co).z > STOCK_TOP - 0.075
    v.co = v.co + inv @ (wn * (0.0030 if lace else 0.0022))
uv2 = bm.loops.layers.uv.new("LaceUV")
import math
for f in bm.faces:
    for l in f.loops:
        p = mw @ l.vert.co
        cx = 0.09 if p.x > 0 else -0.09
        l[uv2].uv = ((math.atan2(p.y, p.x - cx) / (2 * math.pi)) * 0.33, STOCK_TOP - p.z)
bm.to_mesh(st.data); bm.free()
st.data.materials.clear()
st.data.materials.append(bpy.data.materials.new("M_Fig4_Stockings"))
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
sub = st.modifiers.new("subd", 'SUBSURF'); sub.levels = 1; sub.render_levels = 1
bpy.ops.object.modifier_apply(modifier="subd")
st.name = "Fig4_stockings"; objs.append(st)
print("built stockings from body:", len(st.data.vertices), "verts")
for part in ("dress", "shoes", "choker"):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(PARTS, f"fig4_outfit_{part}.glb"))
    o = next(x for x in bpy.context.scene.objects if x not in before and x.type == 'MESH')
    for x in bpy.context.scene.objects: x.select_set(x == o)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    rest = F[f"{part}_rest"]; idx = F[f"{part}_idx"]; w = F[f"{part}_w"]
    assert len(rest) == len(o.data.vertices), (part, len(rest), len(o.data.vertices))
    o.data.vertices.foreach_set("co", rest.astype(np.float32).ravel())
    o.data.update()
    groups = {}
    for v in range(len(rest)):
        for k in range(4):
            if w[v, k] > 1e-4:
                b = bones[idx[v, k]]
                g = groups.get(b) or o.vertex_groups.new(name=b); groups[b] = g
                g.add([v], float(w[v, k]), 'REPLACE')
    if part == "dress" and "dress_keep" in F:
        keep = F["dress_keep"]
        bm2 = bmesh.new(); bm2.from_mesh(o.data); bm2.verts.ensure_lookup_table()
        bmesh.ops.delete(bm2, geom=[bm2.verts[i] for i in np.nonzero(~keep)[0]], context='VERTS')
        bm2.to_mesh(o.data); bm2.free()
    for m in o.data.materials:
        if m: m.name = f"M_Fig4_{part.capitalize()}"
    o.name = f"Fig4_{part}"
    objs.append(o)
    print("built", part, len(rest), "verts,", len(groups), "groups")

for x in bpy.context.scene.objects: x.select_set(x in objs)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.join()
outfit = bpy.context.active_object; outfit.name = "SKM_Fig4_Outfit"; outfit.data.name = "SKM_Fig4_Outfit"
outfit.parent = arm
outfit.matrix_parent_inverse = arm.matrix_world.inverted()   # armature carries the cm->m 0.01 scale
mod = outfit.modifiers.new("Armature", 'ARMATURE'); mod.object = arm
for p in outfit.data.polygons: p.use_smooth = True

for x in bpy.context.scene.objects: x.select_set(x in (arm, outfit))
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(filepath=OUT_FBX, use_selection=True, add_leaf_bones=False, bake_anim=False,
                         mesh_smooth_type='FACE', object_types={'ARMATURE', 'MESH'}, path_mode='AUTO',
                         armature_nodetype='NULL', use_armature_deform_only=False)
print("FBX", OUT_FBX)

# preview render over the bind-pose body
dg = bpy.context.evaluated_depsgraph_get()
ev = outfit.evaluated_get(dg)
bb = [ev.matrix_world @ mathutils.Vector(c) for c in ev.bound_box]
print("outfit world bbox", [round(min(v[i] for v in bb), 3) for i in range(3)], [round(max(v[i] for v in bb), 3) for i in range(3)])
print("armature matrix", [list(map(lambda x: round(x, 3), r)) for r in arm.matrix_world])
skin = bpy.data.materials.new("skin_prev"); skin.diffuse_color = (0.75, 0.6, 0.55, 1)
body.data.materials.clear(); body.data.materials.append(skin)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'TEXTURE'
sc.display.shading.light = 'STUDIO'
sc.render.resolution_x, sc.render.resolution_y = 700, 1100
cd = bpy.data.cameras.new("c"); cd.type = 'ORTHO'; cd.ortho_scale = 1.75
cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
tgt = mathutils.Vector((0, 0, 0.8))
for name, d in (("front", (0, -1, 0)), ("side", (1, 0, 0)), ("back", (0, 1, 0))):
    dv = mathutils.Vector(d)
    cam.location = tgt + dv * 4
    cam.rotation_euler = (-dv).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f"{PREV}_{name}.png"
    bpy.ops.render.render(write_still=True)
