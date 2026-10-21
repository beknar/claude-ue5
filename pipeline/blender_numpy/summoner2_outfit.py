"""Summoner2's bikini on her MetaHuman body (Blender). The bikini (s2_bikini.glb: cups, bottom, strings, bows and chains, cut
from her model by summoner2_prep.py, her T-pose) is moved onto the built MetaHuman body (s2_body.fbx, 845 export: its bind
pose, MetaHuman's A-pose) and skinned to it:
  - each bikini vertex's place on her: the nearest point of her own skin (s2_target.glb) and how far out it is (along the
    skin's normal);
  - the same place on the MetaHuman: the body's nearest point to that skin point, and out by the same amount (2 mm at
    least: the cups sit on the body's breasts as they are, not as hers were); a vertex far off the skin (the hanging
    chains) moves with the skin point it hangs from;
  - its weights: the body's, from its nearest face (interpolated; Blender's data transfer), the hanging chains' from the
    point they hang from;
  - the body's own skeleton (the FBX's armature), exported as s2_bikini_skinned.fbx for 845 import;
  - her texture's three images written to tex/ (T_S2_Color, T_S2_Normal, T_S2_MetalRough) for the bikini's material;
  - check renders (outfit_front/side/back/close) over the body.
Her T-pose and the A-pose differ at the arms and the legs; the bikini sits on the torso and the hips, where the fitted
MetaHuman is where she was (842 fitted it in her pose).
    blender -b -P summoner2_outfit.py -- <SourceArt/summoner2>"""
import bpy, bmesh, sys, os, math, json, numpy as np, mathutils
from mathutils.bvhtree import BVHTree
SA = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
def imp_glb(p):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=p)
    o = [x for x in bpy.data.objects if x not in before and x.type == "MESH"][0]
    for x in bpy.context.scene.objects: x.select_set(x == o)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM"); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return o
bik = imp_glb(os.path.join(SA, "s2_bikini.glb")); bik.name = "SKM_S2_Bikini"
tgt = imp_glb(os.path.join(SA, "s2_target.glb")); tgt.name = "target"
before = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=os.path.join(SA, "s2_body.fbx"))
arm = next(o for o in bpy.data.objects if o not in before and o.type == "ARMATURE"); arm.name = "Armature"
body = max([o for o in bpy.data.objects if o not in before and o.type == "MESH"], key=lambda o: len(o.data.vertices))
before = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=os.path.join(SA, "s2_face.fbx"))
face = max([o for o in bpy.data.objects if o not in before and o.type == "MESH"], key=lambda o: len(o.data.vertices))
for o in [o for o in bpy.data.objects if o not in before and o is not face]: o.hide_render = True     # (its armature carries the cm scale: kept)
print("S2OUT face mesh", np.array([face.matrix_world @ mathutils.Vector(c) for c in face.bound_box]).min(0).round(3), np.array([face.matrix_world @ mathutils.Vector(c) for c in face.bound_box]).max(0).round(3))
dg = bpy.context.evaluated_depsgraph_get()
def world_verts(o):
    e = o.evaluated_get(dg); m = e.to_mesh(); mw = o.matrix_world
    co = np.array([mw @ v.co for v in m.vertices]); tri = []
    m.calc_loop_triangles()
    tri = np.array([lt.vertices[:] for lt in m.loop_triangles]); e.to_mesh_clear(); return co, tri
BV, BT = world_verts(body); TV, TT = world_verts(tgt); FV, FT = world_verts(face); KV = np.array([bik.matrix_world @ v.co for v in bik.data.vertices])
print("S2OUT body", BV.min(0).round(3), BV.max(0).round(3), "| target", TV.min(0).round(3), TV.max(0).round(3), "| bikini", KV.min(0).round(3), KV.max(0).round(3))
# (both face -Y: her bust is the most forward at bust height; the body's too)
def front_y(V, z0, z1):
    m = (V[:, 2] > z0) & (V[:, 2] < z1) & (np.abs(V[:, 0]) < 0.15); return V[m, 1].min(), V[m, 1].max()
print("S2OUT bust band y: body", np.round(front_y(BV, 1.15, 1.25), 3), "target", np.round(front_y(TV, 1.15, 1.25), 3))
bvh_t = BVHTree.FromPolygons([tuple(p) for p in TV], [tuple(t) for t in TT], all_triangles=True)
# (the body and the face mesh together: the neck goes on above the body's collar)
BF = np.vstack([BV, FV]); BFT = np.vstack([BT, FT + len(BV)])
bvh_b = BVHTree.FromPolygons([tuple(p) for p in BF], [tuple(t) for t in BFT], all_triangles=True)
new = np.zeros_like(KV); offs = np.zeros(len(KV)); moved = np.zeros(len(KV))
for i, v in enumerate(KV):
    p, n, _, d = bvh_t.find_nearest(mathutils.Vector(v))
    off = (mathutils.Vector(v) - p).dot(n); offs[i] = off
    q, nb, _, _ = bvh_b.find_nearest(p)
    on_skin = q + nb * max(off, 0.002)
    hang = mathutils.Vector(v) + (q - p)
    k = min(max((abs(off) - 0.012) / 0.02, 0.0), 1.0)             # 0: lies on the skin, 1: hangs (1.2 to 3.2 cm out)
    w_ = on_skin * (1 - k) + hang * k
    new[i] = w_; moved[i] = (w_ - mathutils.Vector(v)).length
print("S2OUT offsets: median %.4f, 95%% %.4f m; moved median %.4f, max %.4f m" % (np.median(np.abs(offs)), np.percentile(np.abs(offs), 95), np.median(moved), moved.max()))
mwi = bik.matrix_world.inverted()
for i, v in enumerate(bik.data.vertices): v.co = mwi @ mathutils.Vector(new[i])
bik.data.update()
# weights: from the body (its bind pose), nearest face interpolated
for vg in body.vertex_groups:
    if vg.name not in bik.vertex_groups: bik.vertex_groups.new(name=vg.name)
dt = bik.modifiers.new("dt", "DATA_TRANSFER"); dt.object = body; dt.use_vert_data = True
dt.data_types_verts = {"VGROUP_WEIGHTS"}; dt.vert_mapping = "POLYINTERP_NEAREST"
dt.layers_vgroup_select_src = "ALL"; dt.layers_vgroup_select_dst = "NAME"
for x in bpy.context.scene.objects: x.select_set(x == bik)
bpy.context.view_layer.objects.active = bik
bpy.ops.object.modifier_apply(modifier="dt")
for vg in list(bik.vertex_groups):                                   # (drop the groups nothing uses)
    if not any(g.group == vg.index and g.weight > 1e-4 for v in bik.data.vertices for g in v.groups): bik.vertex_groups.remove(vg)
print("S2OUT weights: %d groups" % len(bik.vertex_groups), sorted(vg.name for vg in bik.vertex_groups)[:30])
# her texture's images
os.makedirs(os.path.join(SA, "tex"), exist_ok=True)
roles = {}
for m in bik.data.materials:
    if not m or not m.use_nodes: continue
    for n in m.node_tree.nodes:
        if n.type != "TEX_IMAGE" or not n.image: continue
        to = [l.to_socket.name + ":" + l.to_node.type for l in n.outputs[0].links]
        role = "Color" if any("Base Color" in t for t in to) else ("Normal" if any("NORMAL_MAP" in t for t in to) else "MetalRough")
        roles[role] = n.image
for role, img in roles.items():
    p = os.path.join(SA, "tex", f"T_S2_{role}.png")
    img.filepath_raw = p; img.file_format = "PNG"; img.save()
print("S2OUT textures", {k: v.name for k, v in roles.items()})
bik.data.materials.clear(); bik.data.materials.append(bpy.data.materials.new("M_S2_Bikini"))
# parent and export
bik.parent = arm; bik.matrix_parent_inverse = arm.matrix_world.inverted()
mod = bik.modifiers.new("Armature", "ARMATURE"); mod.object = arm
for p_ in bik.data.polygons: p_.use_smooth = True
for x in bpy.context.scene.objects: x.select_set(x in (arm, bik))
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(filepath=os.path.join(SA, "s2_bikini_skinned.fbx"), use_selection=True, add_leaf_bones=False, bake_anim=False,
                         mesh_smooth_type="FACE", object_types={"ARMATURE", "MESH"}, path_mode="AUTO", armature_nodetype="NULL",
                         use_armature_deform_only=False)
print("S2OUT FBX", os.path.join(SA, "s2_bikini_skinned.fbx"), len(bik.data.vertices), "verts")
# check renders over the body
tgt.hide_render = True; fm_ = bpy.data.materials.new("fskin"); fm_.diffuse_color = (0.8, 0.66, 0.6, 1); face.data.materials.clear(); face.data.materials.append(fm_)
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
bm_ = bpy.data.materials.new("skin"); bm_.diffuse_color = (0.8, 0.66, 0.6, 1); body.data.materials.clear(); body.data.materials.append(bm_)
km = bik.data.materials[0]; km.diffuse_color = (0.85, 0.05, 0.05, 1)
cd = bpy.data.cameras.new("c"); cd.type = "ORTHO"; cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
for name, d, ctr, ortho in (("front", (0, -1, 0), (0, 0, 1.05), 0.75), ("side", (1, 0, 0), (0, 0, 1.05), 0.75), ("back", (0, 1, 0), (0, 0, 1.05), 0.75),
                            ("close", (0.6, -1, 0.1), (0, 0, 0.95), 0.45)):
    dv = mathutils.Vector(d).normalized(); cam.location = mathutils.Vector(ctr) + dv * 4
    cam.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler(); cd.ortho_scale = ortho
    sc.render.resolution_x = sc.render.resolution_y = 800
    sc.render.filepath = os.path.join(SA, f"outfit_{name}.png"); bpy.ops.render.render(write_still=True)
print("S2OUT done")
