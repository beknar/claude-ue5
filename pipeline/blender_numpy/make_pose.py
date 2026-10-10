"""Author fig4's standing pose on the MetaHuman body skeleton and export it as an FBX animation.
Heels: pelvis lift + foot/ball rotations from the outfit fit. Arms relaxed at the sides with a
slight elbow bend, a touch of contrapposto, chest/head tilt.
Blender: -- body.fbx foot_pose.json out.fbx"""
import bpy, sys, json, math
from mathutils import Matrix, Vector, Quaternion
argv = sys.argv[sys.argv.index("--") + 1:]
BODY_FBX, FOOT_JSON, OUT = argv[:3]
fp = json.load(open(FOOT_JSON))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=BODY_FBX)
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
for o in list(bpy.context.scene.objects):
    if o.type == 'MESH':
        bpy.data.objects.remove(o)
arm.name = "Armature"
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')
pb = arm.pose.bones
AW = arm.matrix_world.copy(); AWi = AW.inverted()
def head_w(n): return AW @ pb[n].head
def rotate_world(n, q):
    b = pb[n]; M = b.matrix.copy(); h = M.translation.copy()
    R = (AWi.to_3x3() @ q.to_matrix() @ AW.to_3x3()).to_4x4()
    b.matrix = Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ M
    bpy.context.view_layer.update()
def aim(n, child, d):
    cur = (head_w(child) - head_w(n)).normalized()
    rotate_world(n, cur.rotation_difference(Vector(d).normalized()))

# heels
pel = pb["pelvis"]
pel.matrix = Matrix.Translation(AWi.to_3x3() @ Vector((0, 0, fp["lift"]))) @ pel.matrix
bpy.context.view_layer.update()
for n, q in fp["rotations"].items():
    pb[n].rotation_mode = 'QUATERNION'; pb[n].rotation_quaternion = Quaternion(q)
bpy.context.view_layer.update()

# contrapposto: hips tilt toward the weight-bearing left leg, shoulders counter
rotate_world("pelvis", Quaternion(Vector((0, 1, 0)), math.radians(-2.5)))
rotate_world("spine_03", Quaternion(Vector((0, 1, 0)), math.radians(1.5)))
rotate_world("spine_05", Quaternion(Vector((0, 1, 0)), math.radians(1.5)))
# re-plant the feet after the hip tilt (heel pose stays)
for side in ("l", "r"):
    for n in (f"foot_{side}", f"ball_{side}"):
        pb[n].rotation_quaternion = Quaternion(fp["rotations"][n])
bpy.context.view_layer.update()

# arms down by the sides, elbows softly bent, forearms slightly forward
for side, sg in (("l", 1), ("r", -1)):
    aim(f"upperarm_{side}", f"lowerarm_{side}", (0.20 * sg, 0.02, -1.0))
    aim(f"lowerarm_{side}", f"hand_{side}", (0.10 * sg, -0.22, -1.0))
    rotate_world(f"hand_{side}", Quaternion(Vector((0, 0, 1)), math.radians(-12 * sg)))
# head: slight tilt and turn toward camera-left
rotate_world("neck_02", Quaternion(Vector((0, 1, 0)), math.radians(-2.0)))
rotate_world("head", Quaternion(Vector((0, 0, 1)), math.radians(-6.0)))
rotate_world("head", Quaternion(Vector((0, 1, 0)), math.radians(-3.0)))

print("feet balls", [round(c, 3) for c in head_w("ball_l")], [round(c, 3) for c in head_w("ball_r")],
      "hands", [round(c, 3) for c in head_w("hand_l")])
# key two frames of the pose for every bone
scn = bpy.context.scene; scn.frame_start = 0; scn.frame_end = 1
for f in (0, 1):
    for b in pb:
        b.keyframe_insert("location", frame=f)
        b.rotation_mode = 'QUATERNION'
        b.keyframe_insert("rotation_quaternion", frame=f)
        b.keyframe_insert("scale", frame=f)
arm.animation_data.action.name = "A_Fig4_Pose"
bpy.ops.object.mode_set(mode='OBJECT')
for x in bpy.context.scene.objects: x.select_set(x == arm)
bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, add_leaf_bones=False, bake_anim=True,
                         bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                         object_types={'ARMATURE'}, armature_nodetype='NULL')
print("POSE FBX", OUT)
