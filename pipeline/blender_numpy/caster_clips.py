"""Clips girl-caster-tripo lacks, made on her own rig for tripo_build.py (its clip_maker argument): an Idle and three
spell casts that throw a bolt from the right hand.
  Idle    3.2 s loop: arms hanging, fingers a little curled, breathing (the chest rises and falls)
  Cast1   right-hand throw: the hand is drawn back beside her shoulder (palm up, the left hand points at the target),
          then thrust forward, palm out; the bolt leaves at 0.46 s
  Cast2   two-handed push: both hands gathered at her chest, elbows out, then pushed forward together; release 0.54 s
  Cast3   overhead: the right hand raised above her head, then swept forward and down; release 0.58 s
Each pose is written as where her bones point (armature space: she faces -Y, her right is -X, up +Z), turned into
local rotations parent first, and keyed poses are eased into each other at 24 fps. Her legs bend a little in a cast
and the pelvis goes down with them, so the feet stay where they stand; the casts start and end on the idle pose.
The release times are where the throwing hand moves fastest: pipeline/unreal/811 measures them on the imported clips.
Preview (renders each clip's key poses, front and side): blender -b -P caster_clips.py -- model.glb out_prefix"""
import math
import bpy
from mathutils import Matrix, Vector, Quaternion

FPS = 24
F = Vector((0.0, -1.0, 0.0)); U = Vector((0.0, 0.0, 1.0))
OUT = {"r": Vector((-1.0, 0.0, 0.0)), "l": Vector((1.0, 0.0, 0.0))}
LEAN = Vector((1.0, 0.0, 0.0))                 # a positive turn about it leans her forward
FINGERS = ("index", "middle", "ring", "pinky")


def D(side, o, f, u):
    """a direction for one side: o outward (her right for the right arm), f forward, u up"""
    return (OUT[side] * o + F * f + U * u).normalized()


def arm(side, up, low, hand, curl=12.0, thumb=6.0, twist=0.0):
    sp = {f"upperarm_{side}": [("dir", up)], f"lowerarm_{side}": [("dir", low)], f"hand_{side}": [("dir", hand)] + ([("twist", twist)] if twist else [])}
    for fn in FINGERS:
        for k, w in (("01", 0.7), ("02", 1.0), ("03", 0.8)):
            sp[f"{fn}_{k}_{side}"] = [("curl", curl * w)]
    for k in ("02", "03"):
        sp[f"thumb_{k}_{side}"] = [("curl", thumb)]
    return sp


def body(ctx, twist=0.0, lean=0.0, knees=3.0, look=0.7):
    """twist: degrees her shoulders turn to her right (negative: left); lean: forward; knees: bend; look: share of the
    twist the neck takes back (her eyes stay on the target)"""
    sp = {}
    for b, w in (("spine_01", 0.3), ("spine_02", 0.35), ("spine_03", 0.35)):
        sp[b] = [("rot", U, -twist * w), ("rot", LEAN, lean * w)]
    sp["neck_01"] = [("rot", U, twist * look), ("rot", LEAN, -lean * 0.4)]
    if knees:
        drop = ctx["legs"] * (1.0 - math.cos(math.radians(knees)))
        sp["pelvis"] = [("move", Vector((0.0, 0.0, -drop)))]
        for s in "lr":
            sp[f"thigh_{s}"] = [("toward", F, knees)]
            sp[f"calf_{s}"] = [("toward", -F, 2.0 * knees)]
            sp[f"foot_{s}"] = [("rest",)]
    return sp


def idle(ctx, breath=0.0):
    sp = body(ctx, lean=-1.6 * breath, knees=3.0)
    for s in "rl":
        sp.update(arm(s, D(s, 0.21 + 0.015 * breath, 0.05, -1), D(s, 0.12, 0.30 + 0.02 * breath, -1), D(s, 0.05, 0.36, -1), curl=16, thumb=8))
    return sp


def cast1(ctx, k):
    if k == "wind":
        sp = body(ctx, twist=26, lean=-4, knees=9)
        sp.update(arm("r", D("r", 0.62, -0.42, -0.30), D("r", 0.10, 0.55, 0.80), D("r", -0.05, 0.85, 0.35), curl=22, thumb=10, twist=-70))
        sp.update(arm("l", D("l", 0.10, 1.0, 0.12), D("l", -0.02, 1.0, 0.15), D("l", -0.05, 1.0, 0.22), curl=6, thumb=2))
    elif k == "release":
        sp = body(ctx, twist=-18, lean=7, knees=12)
        sp.update(arm("r", D("r", -0.04, 1.0, 0.14), D("r", -0.06, 1.0, 0.12), D("r", 0.0, 0.32, 1.0), curl=4, thumb=2))
        sp.update(arm("l", D("l", 0.42, -0.30, -0.80), D("l", 0.25, 0.20, -0.90), D("l", 0.15, 0.30, -0.90), curl=16, thumb=8))
    else:                                            # follow-through
        sp = body(ctx, twist=-13, lean=5, knees=9)
        sp.update(arm("r", D("r", 0.02, 1.0, 0.02), D("r", 0.0, 1.0, -0.05), D("r", 0.0, 0.70, 0.60), curl=8, thumb=4))
        sp.update(arm("l", D("l", 0.35, -0.15, -0.90), D("l", 0.20, 0.25, -0.90), D("l", 0.10, 0.35, -0.90), curl=16, thumb=8))
    return sp


def cast2(ctx, k):
    if k == "wind":
        sp = body(ctx, twist=0, lean=-3, knees=11)
        for s in "rl":
            sp.update(arm(s, D(s, 0.90, 0.10, -0.45), D(s, -0.80, 0.45, 0.30), D(s, -0.35, 0.25, 1.0), curl=10, thumb=4))
    elif k == "release":
        sp = body(ctx, twist=0, lean=9, knees=13)
        for s in "rl":
            sp.update(arm(s, D(s, -0.10, 1.0, 0.08), D(s, -0.14, 1.0, 0.08), D(s, -0.06, 0.30, 1.0), curl=4, thumb=2))
    else:
        sp = body(ctx, twist=0, lean=6, knees=10)
        for s in "rl":
            sp.update(arm(s, D(s, -0.05, 1.0, -0.05), D(s, -0.08, 1.0, -0.10), D(s, -0.04, 0.70, 0.60), curl=8, thumb=4))
    return sp


def cast3(ctx, k):
    if k == "wind":
        sp = body(ctx, twist=18, lean=-8, knees=6)
        sp.update(arm("r", D("r", 0.25, -0.10, 1.0), D("r", 0.08, -0.35, 1.0), D("r", 0.0, -0.55, 1.0), curl=18, thumb=8))
        sp.update(arm("l", D("l", 0.55, 0.70, 0.10), D("l", 0.35, 0.85, 0.20), D("l", 0.25, 0.85, 0.25), curl=6, thumb=2))
    elif k == "release":
        sp = body(ctx, twist=-20, lean=12, knees=14)
        sp.update(arm("r", D("r", 0.0, 1.0, -0.05), D("r", -0.05, 1.0, -0.15), D("r", 0.0, 1.0, -0.10), curl=4, thumb=2))
        sp.update(arm("l", D("l", 0.35, -0.40, -0.85), D("l", 0.20, 0.10, -0.95), D("l", 0.10, 0.30, -0.90), curl=16, thumb=8))
    else:
        sp = body(ctx, twist=-15, lean=10, knees=11)
        sp.update(arm("r", D("r", 0.05, 0.85, -0.40), D("r", 0.0, 0.80, -0.55), D("r", 0.0, 0.70, -0.65), curl=12, thumb=6))
        sp.update(arm("l", D("l", 0.30, -0.25, -0.90), D("l", 0.18, 0.20, -0.95), D("l", 0.10, 0.30, -0.90), curl=16, thumb=8))
    return sp


# ---------------------------------------------------------------- posing
def context(arm_obj):
    B = arm_obj.data.bones
    legs = (B["calf_l"].head_local - B["thigh_l"].head_local).length + (B["foot_l"].head_local - B["calf_l"].head_local).length
    order = sorted(arm_obj.pose.bones, key=lambda pb: len(pb.parent_recursive))
    hand_of = {pb.name: "hand_" + pb.name[-1] for pb in arm_obj.pose.bones if pb.name.split("_")[0] in FINGERS + ("thumb",)}
    palm = {}
    for h in ("hand_l", "hand_r"):
        # the palm's normal in the hand bone's frame, from the reference pose: the side away from the back of the hand,
        # found as the side the fingers' tips do not stick out to (the middle finger's chain bends toward the palm)
        hb = B[h]; q = hb.matrix_local.to_quaternion()
        mid = [B[f"middle_0{i}_{h[-1]}"] for i in (1, 2, 3)]
        across = (B[f"index_01_{h[-1]}"].head_local - B[f"pinky_01_{h[-1]}"].head_local).normalized()
        along = (mid[2].tail_local - mid[0].head_local).normalized()
        n = along.cross(across).normalized()
        if h == "hand_r": n = -n                     # (mirror: the same cross product points out of the back of the left hand)
        palm[h] = q.inverted() @ n
    return {"legs": legs, "order": order, "hand_of": hand_of, "palm": palm}


def apply(arm_obj, spec, ctx):
    for pb in arm_obj.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    for pb in ctx["order"]:
        ops = spec.get(pb.name)
        if not ops: continue
        M = pb.matrix.copy(); head = M.translation.copy(); rot = M.to_quaternion(); scl = M.to_scale()
        for op in ops:
            k = op[0]; cur = rot @ Vector((0.0, 1.0, 0.0))
            if k == "dir":
                rot = cur.rotation_difference(op[1]) @ rot
            elif k == "twist":
                rot = Quaternion(cur, math.radians(op[1])) @ rot
            elif k == "rot":
                rot = Quaternion(op[1], math.radians(op[2])) @ rot
            elif k in ("toward", "curl"):
                to = op[1] if k == "toward" else arm_obj.pose.bones[ctx["hand_of"][pb.name]].matrix.to_quaternion() @ ctx["palm"][ctx["hand_of"][pb.name]]
                ax = cur.cross(to)
                if ax.length > 1e-6: rot = Quaternion(ax.normalized(), math.radians(op[2] if k == "toward" else op[1])) @ rot
            elif k == "rest":
                rot = pb.bone.matrix_local.to_quaternion()
            elif k == "move":
                head = head + op[1]
        pb.matrix = Matrix.LocRotScale(head, rot, scl)
        bpy.context.view_layer.update()
    return {pb.name: pb.matrix_basis.decompose() for pb in arm_obj.pose.bones}


def ease(u): return u * u * (3.0 - 2.0 * u)


def sample(keys):
    """keys: [(seconds, pose)] -> frames at FPS (poses eased into each other)"""
    n = int(round(keys[-1][0] * FPS)); frames = []
    for i in range(n + 1):
        t = i / FPS
        j = max(k for k in range(len(keys) - 1) if keys[k][0] <= t + 1e-6) if t < keys[-1][0] else len(keys) - 2
        (t0, a), (t1, b) = keys[j], keys[j + 1]
        u = ease(min(max((t - t0) / (t1 - t0), 0.0), 1.0)); fr = {}
        for bn in a:
            l0, q0, s0 = a[bn]; l1, q1, s1 = b[bn]
            if q0.dot(q1) < 0.0: q1 = -q1
            fr[bn] = (l0.lerp(l1, u), q0.slerp(q1, u), s0.lerp(s1, u))
        frames.append(fr)
    return frames


def make_clips(arm_obj, scene, clips):
    ctx = context(arm_obj)
    P = lambda spec: apply(arm_obj, spec, ctx)
    i0, i1 = P(idle(ctx)), P(idle(ctx, 1.0))
    out = {"Idle": sample([(0.0, i0), (1.6, i1), (3.2, i0)])}
    for name, fn, (tw, tr, tf, te) in (("Cast1", cast1, (0.32, 0.46, 0.70, 1.25)), ("Cast2", cast2, (0.38, 0.54, 0.80, 1.35)), ("Cast3", cast3, (0.42, 0.58, 0.85, 1.35))):
        out[name] = sample([(0.0, i0), (tw, P(fn(ctx, "wind"))), (tr, P(fn(ctx, "release"))), (tf, P(fn(ctx, "follow"))), (te, i0)])
    for pb in arm_obj.pose.bones: pb.matrix_basis.identity()
    return out


# ---------------------------------------------------------------- preview
if __name__ == "__main__":
    import sys
    argv = sys.argv[sys.argv.index("--") + 1:]
    src, prefix = argv[0], argv[1]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    sc = bpy.context.scene
    for o in [o for o in sc.objects if o.type == 'MESH' and not o.vertex_groups]: bpy.data.objects.remove(o, do_unlink=True)
    arm_obj = next(o for o in sc.objects if o.type == 'ARMATURE')
    if arm_obj.animation_data: arm_obj.animation_data.action = None
    for pb in arm_obj.pose.bones: pb.rotation_mode = 'QUATERNION'
    ctx = context(arm_obj)
    B = arm_obj.data.bones
    print("PALM", {h: [round(v, 2) for v in (B[h].matrix_local.to_quaternion() @ ctx["palm"][h])] for h in ctx["palm"]},
          "thumb_r offset", [round(v, 3) for v in (B["thumb_01_r"].head_local - B["hand_r"].head_local)])
    clips = make_clips(arm_obj, sc, {})
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'TEXTURE'; sc.display.shading.light = 'STUDIO'
    sc.render.resolution_x = 360; sc.render.resolution_y = 520
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.25
    shots = []
    for name, frames in clips.items():
        picks = [0, len(frames) // 2] if name == "Idle" else [int(round(t * FPS)) for t in {"Cast1": (0.32, 0.46, 0.70), "Cast2": (0.38, 0.54, 0.80), "Cast3": (0.42, 0.58, 0.85)}[name]]
        for fi in picks:
            for pb in arm_obj.pose.bones:
                l, q, s = frames[fi][pb.name]; pb.location = l; pb.rotation_quaternion = q; pb.scale = s
            bpy.context.view_layer.update()
            for view, ang in (("front", 0), ("side", 90), ("q", 40)):
                a = math.radians(ang); d = Vector((math.sin(a), -math.cos(a), 0.0))
                cam.location = Vector((0, 0, 0.5)) + d * 4.0; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
                p = f"{prefix}_{name}_{fi:02d}_{view}.png"; sc.render.filepath = p; bpy.ops.render.render(write_still=True); shots.append(p)
    print("SHOTS", len(shots))
