"""Dystopia_Soldier_02 -> one UE-ready FBX: mesh with per-part materials (Body / Details / FireGun, from the Unity prefab),
skeleton, and all 39 animation takes as actions. The 3ds Max export (armature x0.01, rotated 90) is converted to a
native-centimetre rig so UE imports the root with scale 1 (root motion stays in cm).
Blender: -b -P soldier_build.py -- src_dir out_dir"""
import bpy, bmesh, sys, os, json
argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[0], argv[1]
os.makedirs(out, exist_ok=True)
FIREGUN = {"Blade_Mesh", "Firegun_Backpack_Mesh", "Firegun_Base_Mesh", "Firegun_Hose_Mesh"}
BODY = {"Dystopia_Soldier_2_Body_Mesh", "Dystopia_Soldier_2_Cloth_Mesh", "Dystopia_Soldier_2_Head_Mesh",
        "Dystopia_Soldier_2_Pants_Mesh", "Dystopia_Soldier_2_Shoes_Mesh"}
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.fps = 30
bpy.ops.import_scene.fbx(filepath=os.path.join(src, "Mesh", "Dystopia_Soldier_02_Mesh.FBX"))
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
meshes = [o for o in sc.objects if o.type == 'MESH']
arm.name = "Armature"; arm.data.name = "Armature"
mats = {n: bpy.data.materials.new(n) for n in ("M_Soldier_Body", "M_Soldier_Details", "M_Soldier_FireGun")}
for o in meshes:
    m = mats["M_Soldier_FireGun"] if o.name in FIREGUN else (mats["M_Soldier_Body"] if o.name in BODY else mats["M_Soldier_Details"])
    o.data.materials.clear(); o.data.materials.append(m)
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
arm.animation_data_clear()
# ---- collect every animation take onto this armature ----
report = {}
anim_dir = os.path.join(src, "Animations")
for f in sorted(os.listdir(anim_dir)):
    if not f.lower().endswith(".fbx"): continue
    clip = f.split("@", 1)[1][:-4] if "@" in f else f[:-4]
    if not clip: clip = "Take"
    before_o, before_a = set(bpy.data.objects), set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=os.path.join(anim_dir, f))
    new_o = [o for o in bpy.data.objects if o not in before_o]
    acts = [a for a in bpy.data.actions if a not in before_a]
    src_arm = next((o for o in new_o if o.type == 'ARMATURE'), None)
    if not acts or src_arm is None:
        print("no action in", f)
        for o in new_o: bpy.data.objects.remove(o, do_unlink=True)
        continue
    src_act = src_arm.animation_data.action if src_arm.animation_data and src_arm.animation_data.action else acts[0]
    # rest poses must match for a straight basis copy
    rest_diff = max((src_arm.data.bones[b.name].matrix_local.to_translation() - b.matrix_local.to_translation()).length
                    for b in arm.data.bones if b.name in src_arm.data.bones)
    f0, f1 = [int(round(v)) for v in src_act.frame_range]
    # re-key on the soldier's own armature (an imported action stays bound to the armature it came in with)
    new = bpy.data.actions.new("A_" + clip); new.use_fake_user = True
    arm.animation_data_create(); arm.animation_data.action = new
    if hasattr(arm.animation_data, "action_slot") and hasattr(new, "slots"):
        try: arm.animation_data.action_slot = new.slots.new('OBJECT', "Armature")
        except Exception: pass
    for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
    shared = [pb for pb in arm.pose.bones if pb.name in src_arm.pose.bones]
    for t in range(f0, f1 + 1):
        sc.frame_set(t)                                      # evaluates the source armature's action
        basis = {pb.name: src_arm.pose.bones[pb.name].matrix_basis.copy() for pb in shared}
        for pb in shared:
            loc, rot, scl = basis[pb.name].decompose()
            pb.location = loc; pb.rotation_quaternion = rot; pb.scale = scl
            pb.keyframe_insert("location", frame=t - f0, group=pb.name)
            pb.keyframe_insert("rotation_quaternion", frame=t - f0, group=pb.name)
    for o in new_o: bpy.data.objects.remove(o, do_unlink=True)
    for a in acts: bpy.data.actions.remove(a)
    report[clip] = [f0, f1, round(rest_diff, 4)]
    print("clip", clip, f0, f1, "rest diff", round(rest_diff, 4))
print("actions", len(report))
# ---- native-centimetre rig: bake the 90deg rotation, drop the 0.01 object scale (bone data is already in cm) ----
sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 0.01
bpy.ops.object.select_all(action='DESELECT')
for o in [arm] + meshes: o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
arm.scale = (1.0, 1.0, 1.0)
bpy.context.view_layer.update()
# bake every mesh's world transform into its vertices and re-parent with an identity parent-inverse
# (the Max export leaves x100 / rotated parent-inverse matrices, which UE's skeletal import misreads)
arm.location = (0.0, 0.0, 0.0); bpy.context.view_layer.update()
for o in meshes:
    mw = o.matrix_world.copy()
    o.parent = None; o.matrix_world = mw
bpy.ops.object.select_all(action='DESELECT')
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in meshes:
    o.parent = arm; o.matrix_parent_inverse.identity()
    if not any(m.type == 'ARMATURE' for m in o.modifiers): o.modifiers.new("Armature", 'ARMATURE')
    for m in o.modifiers:
        if m.type == 'ARMATURE': m.object = arm
    bm = bmesh.new(); bm.from_mesh(o.data)                # n-gons block tangent export
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4]); bm.to_mesh(o.data); bm.free()
    print("mesh", o.name, "uv layers", [u.name for u in o.data.uv_layers], "verts", len(o.data.vertices))
bpy.context.view_layer.update()
bb_min = min((o.matrix_world @ v.co).z for o in meshes for v in list(o.data.vertices)[::25])
bb_max = max((o.matrix_world @ v.co).z for o in meshes for v in list(o.data.vertices)[::25])
print("height (cm units):", round(bb_max - bb_min, 1), "arm rot", tuple(arm.rotation_euler), "scale", tuple(arm.scale))
arm.animation_data_create(); arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.ops.object.select_all(action='DESELECT')
for o in [arm] + meshes: o.select_set(True)
bpy.ops.export_scene.fbx(filepath=os.path.join(out, "SK_Dystopia_Soldier_02.fbx"), use_selection=True,
                         object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False, bake_anim=True,
                         bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
                         bake_anim_simplify_factor=0.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE',
                         use_armature_deform_only=False, mesh_smooth_type='FACE', use_tspace=True, path_mode='STRIP')
json.dump(report, open(os.path.join(out, "clips.json"), "w"), indent=1)
print("EXPORT DONE")
