"""Tripo anime female GLB -> UE-ready FBX (skinned mesh + UE4-mannequin-named skeleton, no clips in the source).
The source is 0.98 m tall; scaled to HEIGHT_CM. Native-centimetre rig (root scale 1 in UE), mesh transforms baked
into the vertices with an identity parent-inverse (UE's skeletal import misreads anything else). Textures extracted.
Blender: -b -P ff_build.py -- model.glb out_dir"""
import bpy, sys, os, json
from mathutils import Matrix
argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[0], argv[1]
HEIGHT_CM = 165.0
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.fps = 30
bpy.ops.import_scene.gltf(filepath=src)
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
meshes = [o for o in sc.objects if o.type == 'MESH' and o.vertex_groups]      # skip the importer's bone-shape icosphere
for o in [o for o in sc.objects if o.type == 'MESH' and o not in meshes]: bpy.data.objects.remove(o, do_unlink=True)
arm.name = "Armature"; arm.data.name = "Armature"
meshes[0].name = "SK_FF_Anime"
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
arm.animation_data_clear()
for o in [arm] + meshes: print("obj", o.name, "rot", tuple(round(v, 3) for v in o.rotation_euler), "scale", tuple(o.scale), "parent", o.parent.name if o.parent else None)
# textures
tex = {}
for img in bpy.data.images:
    if img.packed_file or img.has_data:
        p = os.path.join(out, "T_FF_" + ("MetalRough" if "metallic" in img.name.lower() else img.name.replace(" ", "_")) + ".png")
        img.filepath_raw = p; img.file_format = 'PNG'; img.save(); tex[img.name] = p
        print("texture", img.name, "->", p, tuple(img.size))
# measure, then scale everything about the origin to HEIGHT_CM in a centimetre scene
bpy.context.view_layer.update()
zs = [(meshes[0].matrix_world @ v.co).z for v in meshes[0].data.vertices]
h = max(zs) - min(zs); k = HEIGHT_CM / (h * 100.0)
print("source height m", round(h, 4), "scale factor", round(k, 4))
sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 0.01
for o in meshes:
    mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
S = Matrix.Scale(100.0 * k, 4)
for o in [arm] + meshes: o.matrix_world = S @ o.matrix_world
bpy.ops.object.select_all(action='DESELECT')
for o in [arm] + meshes: o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in meshes:
    o.parent = arm; o.matrix_parent_inverse.identity()
    mods = [m for m in o.modifiers if m.type == 'ARMATURE']
    if not mods: mods = [o.modifiers.new("Armature", 'ARMATURE')]
    for m in mods: m.object = arm
    print("mesh", o.name, "uv", [u.name for u in o.data.uv_layers], "verts", len(o.data.vertices), "groups", len(o.vertex_groups))
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
ev = meshes[0].evaluated_get(dg); me = ev.to_mesh()
zz = [(meshes[0].matrix_world @ v.co).z for v in me.vertices]; ev.to_mesh_clear()
B = arm.data.bones
print("deformed height cm", round(max(zz) - min(zz), 1), "min z", round(min(zz), 2),
      "head bone z", round(B["head"].head_local.z, 1), "pelvis z", round(B["pelvis"].head_local.z, 1),
      "hand_l", tuple(round(v, 1) for v in B["hand_l"].head_local), "arm rot", tuple(arm.rotation_euler), "scale", tuple(arm.scale))
bpy.ops.object.select_all(action='DESELECT')
for o in [arm] + meshes: o.select_set(True)
bpy.ops.export_scene.fbx(filepath=os.path.join(out, "SK_FF_Anime.fbx"), use_selection=True,
                         object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False, bake_anim=False,
                         apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', use_armature_deform_only=False,
                         mesh_smooth_type='FACE', use_tspace=True, path_mode='STRIP')
json.dump({"height_cm": HEIGHT_CM, "scale": k, "textures": tex}, open(os.path.join(out, "ff_build.json"), "w"), indent=1)
print("EXPORT DONE")
