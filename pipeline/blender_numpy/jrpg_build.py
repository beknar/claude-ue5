"""Meshy JRPG character GLB -> UE-ready FBX: skinned mesh + armature with a real `root` bone (pelvis re-parented to it),
NO animations (the GLB's own Walking/Running clips are discarded: she plays the Dystopia Soldier's retargeted clips).
Centimetre rig (scale x100 applied, scene unit cm) so UE reads no unit scale onto the root. Also writes the textures as PNG.
Blender: -b -P jrpg_build.py -- model.glb out_dir name"""
import bpy, sys, os
from mathutils import Matrix
argv = sys.argv[sys.argv.index("--") + 1:]
glb, out, name = argv[0], argv[1], argv[2]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=glb)
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
mesh = max((o for o in sc.objects if o.type == 'MESH' and o.parent is arm), key=lambda o: len(o.data.vertices))
for o in list(sc.objects):                                           # stray helpers (e.g. an Icosphere) go
    if o not in (arm, mesh): bpy.data.objects.remove(o, do_unlink=True)
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
arm.animation_data_clear(); mesh.animation_data_clear()
arm.name = "Armature"; arm.data.name = "Armature"; mesh.name = name
for img in bpy.data.images:
    if img.packed_file or img.has_data:
        p = os.path.join(out, img.name.replace(" ", "_") + ".png"); img.filepath_raw = p; img.file_format = 'PNG'; img.save(); print("texture", p, tuple(img.size))
# mesh: bake its world transform and parent it to the armature with an identity parent-inverse (else UE imports it rotated)
mw = mesh.matrix_world.copy(); mesh.parent = None; mesh.matrix_world = Matrix.Identity(4); mesh.data.transform(mw)
amw = arm.matrix_world.copy()
mesh.data.transform(amw.inverted()); mesh.parent = arm; mesh.matrix_parent_inverse = Matrix.Identity(4); mesh.matrix_world = amw
for m in mesh.modifiers:
    if m.type == 'ARMATURE': m.object = arm
# root bone at the origin
bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
root = eb.new("root"); root.head = (0, 0, 0); root.tail = (0, 0.25, 0); root.roll = 0
eb["pelvis"].parent = root; eb["pelvis"].use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')
for pb in arm.pose.bones: pb.matrix_basis.identity()
# centimetre rig
sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 0.01
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); mesh.select_set(True)
arm.scale = (arm.scale.x * 100, arm.scale.y * 100, arm.scale.z * 100)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
print("height cm", round(max(zs) - min(zs), 1), "min z", round(min(zs), 2), "pelvis z", round(arm.data.bones["pelvis"].head_local.z, 1), "bones", len(arm.data.bones))
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); mesh.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(filepath=os.path.join(out, name + ".fbx"), use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                         bake_anim=False, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', use_armature_deform_only=False,
                         mesh_smooth_type='FACE', use_tspace=True, path_mode='COPY', embed_textures=False)
print("EXPORT DONE", os.path.join(out, name + ".fbx"))
