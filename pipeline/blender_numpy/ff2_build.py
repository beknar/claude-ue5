"""Animated Tripo anime female GLB -> UE-ready FBX: skinned mesh (165 cm, native-centimetre rig, baked mesh transforms with
identity parent-inverse) + all 8 glTF clips as actions (re-keyed on the export armature, translations scaled with the rig).
Blender: -b -P ff2_build.py -- model.glb out_dir"""
import bpy, sys, os, json
from mathutils import Matrix
argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[0], argv[1]
HEIGHT_CM = 165.0
NAMES = {"box_01": "Box", "cast_a_spell": "CastSpell", "dance_01": "Dance", "idle": "Idle", "jump": "Jump",
         "run": "Run", "shoot": "Shoot", "walk": "Walk"}
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=src)
sc.render.fps = 24
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
meshes = [o for o in sc.objects if o.type == 'MESH' and o.vertex_groups]      # skip the importer's bone-shape icosphere
for o in [o for o in sc.objects if o.type == 'MESH' and o not in meshes]: bpy.data.objects.remove(o, do_unlink=True)
arm.name = "Armature"; arm.data.name = "Armature"; meshes[0].name = "SK_FF2_Anime"
ad = arm.animation_data
for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
# textures
for img in bpy.data.images:
    if img.packed_file or img.has_data:
        p = os.path.join(out, "T_FF2_" + ("MetalRough" if "metallic" in img.name.lower() else img.name.replace(" ", "_")) + ".png")
        img.filepath_raw = p; img.file_format = 'PNG'; img.save(); print("texture", img.name, "->", p)
# ---- sample every clip's local bone transforms (bone-space basis) ----
for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
clips = {}
for act in list(bpy.data.actions):
    key = act.name.split(".")[0]; name = NAMES.get(key, key)
    ad.action = act
    if hasattr(ad, "action_slot") and act.slots: ad.action_slot = act.slots[0]
    f0, f1 = [int(round(v)) for v in act.frame_range]
    frames = []
    for t in range(f0, f1 + 1):
        sc.frame_set(t)
        frames.append({pb.name: pb.matrix_basis.decompose() for pb in arm.pose.bones})
    clips[name] = frames
    print("sampled", name, f0, f1, len(frames))
ad.action = None
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
# ---- scale to HEIGHT_CM in a centimetre scene; bake mesh transforms ----
zs = [(meshes[0].matrix_world @ v.co).z for v in meshes[0].data.vertices]
h = max(zs) - min(zs); S = HEIGHT_CM / h          # metres -> cm with the height fix
print("source height m", round(h, 4), "unit scale", round(S, 3))
sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 0.01
for o in meshes:
    mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
for o in [arm] + meshes: o.matrix_world = Matrix.Scale(S, 4) @ o.matrix_world
bpy.ops.object.select_all(action='DESELECT')
for o in [arm] + meshes: o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in meshes:
    o.parent = arm; o.matrix_parent_inverse.identity()
    mods = [m for m in o.modifiers if m.type == 'ARMATURE'] or [o.modifiers.new("Armature", 'ARMATURE')]
    for m in mods: m.object = arm
# mesh-only FBX first: with clips in the file UE rebinds the skin to the time-zero (first clip) pose
bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
for o in [arm] + meshes: o.select_set(True)
bpy.ops.export_scene.fbx(filepath=os.path.join(out, "SK_FF2_Anime.fbx"), use_selection=True,
                         object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False, bake_anim=False,
                         apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', use_armature_deform_only=False,
                         mesh_smooth_type='FACE', use_tspace=True, path_mode='STRIP')
# ---- re-key every clip on the scaled armature (bone-space translations scale with the rig) ----
ad = arm.animation_data_create()
for name, frames in clips.items():
    new = bpy.data.actions.new("A_" + name); new.use_fake_user = True
    ad.action = new
    if hasattr(ad, "action_slot") and hasattr(new, "slots"):
        try: ad.action_slot = new.slots.new('OBJECT', "Armature")
        except Exception: pass
    for i, fr in enumerate(frames):
        for pb in arm.pose.bones:
            loc, rot, scl = fr[pb.name]
            pb.location = loc * S; pb.rotation_quaternion = rot; pb.scale = scl
            pb.keyframe_insert("location", frame=i, group=pb.name)
            pb.keyframe_insert("rotation_quaternion", frame=i, group=pb.name)
            pb.keyframe_insert("scale", frame=i, group=pb.name)
    print("keyed", name, len(frames))
# check: deformed height at rest and one walk frame
ad.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
B = arm.data.bones
print("rest: head z", round(B["head"].head_local.z, 1), "pelvis z", round(B["pelvis"].head_local.z, 1), "arm scale", tuple(arm.scale))
ad.action = bpy.data.actions["A_Walk"]
if hasattr(ad, "action_slot"): ad.action_slot = bpy.data.actions["A_Walk"].slots[0]
sc.frame_set(10)
print("walk f10: pelvis", tuple(round(v, 1) for v in arm.pose.bones["pelvis"].head), "ball_l", tuple(round(v, 1) for v in arm.pose.bones["ball_l"].head))
ad.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.ops.object.select_all(action='DESELECT')
for o in [arm] + meshes: o.select_set(True)
bpy.ops.export_scene.fbx(filepath=os.path.join(out, "A_FF2_Clips.fbx"), use_selection=True,
                         object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False, bake_anim=True,
                         bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
                         bake_anim_simplify_factor=0.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE',
                         use_armature_deform_only=False, mesh_smooth_type='FACE', use_tspace=True, path_mode='STRIP')
json.dump({k: len(v) for k, v in clips.items()}, open(os.path.join(out, "clips.json"), "w"), indent=1)
print("EXPORT DONE")
