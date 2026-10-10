"""Meshy biped -> one UE-ready FBX: mesh + armature with a real `root` bone + all 18 animations as actions.
Root-motion clips (turns, kick, sweep, walking_2) get their pelvis ground travel and yaw moved onto `root`;
in-place clips keep `root` at rest. Also extracts textures and measures stance-foot speed of each loop.
Blender: -b -P meshy_build.py -- src_dir out_dir"""
import bpy, sys, os, math, json
from mathutils import Matrix, Vector
argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[0], argv[1]
os.makedirs(out, exist_ok=True)
files = sorted(f for f in os.listdir(src) if f.endswith(".glb"))
def clip_name(f): return f.replace("Meshy_AI_biped_Animation_", "").replace("_withSkin.glb", "")
ROOT_MOTION = {"Idle_Turn_Left", "Idle_Turn_Right", "Step_Step_Turn_Kick", "Leg_Sweep", "walking_2"}

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
# ---- base: mesh + armature from the first file -------------------------------------------
bpy.ops.import_scene.gltf(filepath=os.path.join(src, files[0]))
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
mesh = next(o for o in sc.objects if o.type == 'MESH')
arm.name = "Armature"; arm.data.name = "Armature"
mesh.name = "SK_Meshy_Biped"
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
arm.animation_data_clear()
# textures out
for img in bpy.data.images:
    if img.packed_file or img.has_data:
        p = os.path.join(out, img.name.replace(" ", "_") + ".png")
        img.filepath_raw = p; img.file_format = 'PNG'; img.save()
        print("texture", p, tuple(img.size))
# add root bone at the origin, parent pelvis to it
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
root = eb.new("root"); root.head = (0, 0, 0); root.tail = (0, 0.25, 0); root.roll = 0
eb["pelvis"].parent = root; eb["pelvis"].use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')

# ---- gather actions ------------------------------------------------------------------------
report = {}
for f in files:
    name = clip_name(f)
    before_objs = set(bpy.data.objects); before_acts = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=os.path.join(src, f))
    new_objs = [o for o in bpy.data.objects if o not in before_objs]
    act = next(a for a in bpy.data.actions if a not in before_acts)
    for o in new_objs: bpy.data.objects.remove(o, do_unlink=True)
    act.name = "src_" + name
    # sample the source pelvis on our armature (root at rest)
    arm.animation_data_create(); arm.animation_data.action = act
    if hasattr(arm.animation_data, "action_slot") and act.slots: arm.animation_data.action_slot = act.slots[0]
    f0, f1 = [int(round(v)) for v in act.frame_range]
    pel, feet, hipyaw = [], [], []
    for t in range(f0, f1 + 1):
        sc.frame_set(t)
        pel.append(arm.pose.bones["pelvis"].matrix.copy())          # armature space
        hl = arm.pose.bones["thigh_l"].head - arm.pose.bones["thigh_r"].head          # hip line, armature space
        hipyaw.append(math.atan2(hl.y, hl.x))
        feet.append([(arm.matrix_world @ arm.pose.bones[b].head).copy() for b in ("ball_l", "ball_r", "foot_l", "foot_r")])
    # ---- 1) sample every bone's local basis from the source action ----
    bases = []
    for t in range(f0, f1 + 1):
        sc.frame_set(t)
        bases.append({pb.name: pb.matrix_basis.copy() for pb in arm.pose.bones if pb.name != "root"})
    # ---- 2) root / pelvis split computed directly (root rest = identity, so root basis = armature-space root) ----
    pel_rest = arm.data.bones["pelvis"].matrix_local.copy()
    m0 = pel[0].translation.copy()
    yaws = [hipyaw[0]]
    for y in hipyaw[1:]:                      # unwrap
        while y - yaws[-1] > math.pi: y -= 2 * math.pi
        while y - yaws[-1] < -math.pi: y += 2 * math.pi
        yaws.append(y)
    root_b, pel_b = [], []
    for i in range(len(pel)):
        rootM = Matrix.Identity(4)
        if name in ROOT_MOTION:
            d = pel[i].translation - m0
            rootM = Matrix.Translation((d.x, d.y, 0.0)) @ Matrix.Rotation(yaws[i] - yaws[0], 4, 'Z')
        root_b.append(rootM)
        pel_b.append(pel_rest.inverted() @ rootM.inverted() @ pel[i])     # pelvis stays where the source had it
    # ---- 3) write keys; values are assigned right before each insert so no re-evaluation can overwrite them ----
    new = bpy.data.actions.new("A_" + name)
    arm.animation_data.action = new
    if hasattr(arm.animation_data, "action_slot") and hasattr(new, "slots"):
        try: arm.animation_data.action_slot = new.slots.new('OBJECT', "Armature")
        except Exception: pass
    for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
    for i, t in enumerate(range(f0, f1 + 1)):
        sc.frame_set(t)
        for pb in arm.pose.bones:
            M = root_b[i] if pb.name == "root" else (pel_b[i] if pb.name == "pelvis" else bases[i][pb.name])
            loc, rot, _ = M.decompose()
            pb.location = loc; pb.rotation_quaternion = rot
            pb.keyframe_insert("location", frame=t - f0, group=pb.name)
            pb.keyframe_insert("rotation_quaternion", frame=t - f0, group=pb.name)
    new.use_fake_user = True
    # check: root travel/yaw actually stored
    sc.frame_set(f1)
    rb = arm.pose.bones["root"].matrix_basis
    print("  root end", name, tuple(round(v, 3) for v in rb.translation), round(math.degrees(rb.to_euler().z), 1))
    # stance-foot speed: horizontal speed of the lowest ball/foot point while it is near the ground
    dt = 1.0 / sc.render.fps
    sp = []
    for i in range(1, len(feet)):
        lo = min(range(4), key=lambda k: feet[i][k].z)
        if feet[i][lo].z < min(p.z for p in feet[i]) + 0.02:
            v = feet[i][lo] - feet[i - 1][lo]
            sp.append(math.hypot(v.x, v.y) / dt)
    sp.sort()
    report[name] = dict(frames=f1 - f0 + 1, dur=round((f1 - f0) / sc.render.fps, 3), root_motion=name in ROOT_MOTION,
                        stance_speed_cm_s=round(100 * sp[len(sp) // 2], 1) if sp else 0)
    bpy.data.actions.remove(act)
    print("baked", name, report[name])

# ---- export --------------------------------------------------------------------------------
arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
# ---- centimetre rig: UE reads the FBX unit scale onto the root bone otherwise (root scale 100 multiplied
#      every root-motion delta by 100). Scale the rig x100, apply, scale location keys x100, scene unit = cm.
sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 0.01
bpy.ops.object.select_all(action='DESELECT')
for o in (arm, mesh):
    o.select_set(True)
    if o.parent is None: o.scale = (o.scale.x * 100, o.scale.y * 100, o.scale.z * 100)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
def fcurves(act):
    if hasattr(act, "layers") and act.layers:
        for layer in act.layers:
            for strip in layer.strips:
                for bag in strip.channelbags: yield from bag.fcurves
    else:
        yield from act.fcurves
n_loc = 0
for act in bpy.data.actions:
    for fc in fcurves(act):
        if fc.data_path.endswith(".location"):
            for kp in fc.keyframe_points:
                kp.co[1] *= 100; kp.handle_left[1] *= 100; kp.handle_right[1] *= 100
            n_loc += 1
print("scaled location curves", n_loc, "arm scale", tuple(arm.scale), "pelvis rest z", arm.data.bones["pelvis"].head_local.z)
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True); mesh.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(filepath=os.path.join(out, "SK_Meshy_Biped.fbx"), use_selection=True,
                         object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False, bake_anim=True,
                         bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
                         bake_anim_simplify_factor=0.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE',
                         use_armature_deform_only=False, mesh_smooth_type='FACE', use_tspace=True, path_mode='COPY', embed_textures=False)
json.dump(report, open(os.path.join(out, "anim_report2.json"), "w"), indent=1)
print("EXPORT DONE")
