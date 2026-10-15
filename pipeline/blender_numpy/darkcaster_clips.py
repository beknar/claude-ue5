"""Clips for girl-darkcaster-tripo (tripo_build.py's clip_maker), on her own rig: she fights with a sword in her right hand
and casts fire with her left (random_dungeonmagic_level2). Her own Idle, Walk and Run are kept, with the right hand closed
on the hilt (a fist) in every frame; made for her:
  CastL1   left-hand throw: the left hand drawn back by her shoulder, then thrust forward, palm out; the sword low in
           the right hand
  CastL2   left-hand overhead: raised above her head, then swept forward and down
  Slash1   a horizontal cut: the sword drawn back over her right shoulder, swept across in front of her to the left
  Slash2   an overhead chop: the sword raised behind her head, brought down in front of her
  Slash3   a thrust: the sword pulled back by her right hip, driven straight forward at chest height
Poses are written as in caster_clips.py (where the bones point, armature space: she faces -Y, her right is -X); a hand
can also be turned about its own axis so the thumb points a given way: the sword lies along the thumb (the grip of
pipeline/unreal/817 puts the blade the way the thumb points in the reference pose, as 790 does), so that is where the
blade points. The strike times are measured on the imported clips (817: where the right hand moves fastest, for the
casts the left).
Preview (renders the key poses with a stand-in blade on the right hand): blender -b -P darkcaster_clips.py -- model.glb out_prefix"""
import math, os, sys
import bpy
from mathutils import Matrix, Vector, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import caster_clips as C
D, F, U = C.D, C.F, C.U
FIST = {"01": 72.0, "02": 95.0, "03": 62.0}


def fist(side):
    """the hand closed on a hilt (the thumb across)"""
    sp = {}
    for fn in C.FINGERS:
        for k, a in FIST.items(): sp[f"{fn}_{k}_{side}"] = [("curl", a)]
    sp[f"thumb_02_{side}"] = [("curl", 38.0)]; sp[f"thumb_03_{side}"] = [("curl", 30.0)]
    return sp


def sword_arm(up, low, hand, thumb=None):
    """the sword arm: upper arm, forearm, and where the blade points (`thumb`): the hand is turned so the blade points
    exactly there, the fingers as near the way `hand` says as they can be (at right angles to the blade)"""
    sp = {"upperarm_r": [("dir", up)], "lowerarm_r": [("dir", low)], "hand_r": [("blade", thumb, hand)] if thumb is not None else [("dir", hand)]}
    sp.update(fist("r")); return sp


def low_guard():
    """the sword hanging in her right hand, the blade forward and down a little"""
    return sword_arm(D("r", 0.30, 0.15, -0.95), D("r", 0.10, 0.55, -0.85), D("r", 0.05, 0.20, -1.0), thumb=D("r", 0.05, 1.0, -0.30))


def cast_l1(ctx, k):
    if k == "wind":
        sp = C.body(ctx, twist=-26, lean=-4, knees=9)
        sp.update(C.arm("l", D("l", 0.62, -0.42, -0.30), D("l", 0.10, 0.55, 0.80), D("l", -0.05, 0.85, 0.35), curl=22, thumb=10, twist=70))
    elif k == "release":
        sp = C.body(ctx, twist=18, lean=7, knees=12)
        sp.update(C.arm("l", D("l", -0.04, 1.0, 0.14), D("l", -0.06, 1.0, 0.12), D("l", 0.0, 0.32, 1.0), curl=4, thumb=2))
    else:
        sp = C.body(ctx, twist=13, lean=5, knees=9)
        sp.update(C.arm("l", D("l", 0.02, 1.0, 0.02), D("l", 0.0, 1.0, -0.05), D("l", 0.0, 0.70, 0.60), curl=8, thumb=4))
    sp.update(low_guard()); return sp


def cast_l2(ctx, k):
    if k == "wind":
        sp = C.body(ctx, twist=-18, lean=-8, knees=6)
        sp.update(C.arm("l", D("l", 0.25, -0.10, 1.0), D("l", 0.08, -0.35, 1.0), D("l", 0.0, -0.55, 1.0), curl=18, thumb=8))
    elif k == "release":
        sp = C.body(ctx, twist=20, lean=12, knees=14)
        sp.update(C.arm("l", D("l", 0.0, 1.0, -0.05), D("l", -0.05, 1.0, -0.15), D("l", 0.0, 1.0, -0.10), curl=4, thumb=2))
    else:
        sp = C.body(ctx, twist=15, lean=10, knees=11)
        sp.update(C.arm("l", D("l", 0.05, 0.85, -0.40), D("l", 0.0, 0.80, -0.55), D("l", 0.0, 0.70, -0.65), curl=12, thumb=6))
    sp.update(low_guard()); return sp


def balance(sp, o=0.55, f=0.25, u=-0.75):
    """the free left hand out for balance while she cuts"""
    sp.update(C.arm("l", D("l", o, f, u), D("l", o * 0.5, 0.6, -0.55), D("l", o * 0.3, 0.7, -0.5), curl=20, thumb=8)); return sp


def slash1(ctx, k):
    if k == "wind":
        sp = C.body(ctx, twist=34, lean=-3, knees=8)
        sp.update(sword_arm(D("r", 0.75, -0.30, 0.40), D("r", 0.35, -0.25, 0.85), D("r", 0.15, -0.35, 0.90), thumb=D("r", 0.35, -1.0, 0.05)))
        return balance(sp, 0.35, 0.65, -0.45)
    if k == "release":
        sp = C.body(ctx, twist=-24, lean=7, knees=12)
        sp.update(sword_arm(D("r", -0.25, 1.0, 0.10), D("r", -0.45, 1.0, 0.05), D("r", -0.55, 0.85, 0.0), thumb=D("r", -0.35, 1.0, 0.05)))
        return balance(sp)
    sp = C.body(ctx, twist=-42, lean=6, knees=10)
    sp.update(sword_arm(D("r", -0.75, 0.55, -0.15), D("r", -0.90, 0.30, -0.15), D("r", -0.80, -0.10, -0.10), thumb=D("r", -0.55, -0.85, 0.0)))
    return balance(sp, 0.6, -0.1, -0.7)


def slash2(ctx, k):
    if k == "wind":
        sp = C.body(ctx, twist=12, lean=-7, knees=6)
        sp.update(sword_arm(D("r", 0.20, -0.10, 1.0), D("r", 0.05, -0.55, 0.85), D("r", 0.0, -0.75, 0.65), thumb=D("r", 0.0, -1.0, 0.35)))
        return balance(sp, 0.5, 0.45, -0.3)
    if k == "release":
        sp = C.body(ctx, twist=-6, lean=15, knees=16)
        sp.update(sword_arm(D("r", 0.05, 1.0, 0.15), D("r", 0.0, 1.0, -0.15), D("r", 0.0, 1.0, -0.30), thumb=D("r", 0.0, 0.70, -1.0)))
        return balance(sp)
    sp = C.body(ctx, twist=-8, lean=12, knees=13)
    sp.update(sword_arm(D("r", 0.08, 0.80, -0.55), D("r", 0.0, 0.70, -0.70), D("r", 0.0, 0.60, -0.80), thumb=D("r", 0.0, 0.25, -1.0)))
    return balance(sp, 0.6, 0.0, -0.75)


def slash3(ctx, k):
    if k == "wind":
        sp = C.body(ctx, twist=26, lean=-4, knees=9)
        sp.update(sword_arm(D("r", 0.30, -0.85, -0.45), D("r", 0.10, 0.90, -0.10), D("r", -1.0, 0.25, 0.0), thumb=D("r", 0.0, 1.0, 0.05)))
        return balance(sp, 0.4, 0.7, -0.2)
    if k == "release":
        sp = C.body(ctx, twist=-20, lean=11, knees=15)
        sp.update(sword_arm(D("r", -0.10, 1.0, 0.06), D("r", -0.10, 1.0, 0.06), D("r", -1.0, 0.15, 0.0), thumb=D("r", 0.0, 1.0, 0.05)))
        return balance(sp, 0.6, -0.35, -0.6)
    sp = C.body(ctx, twist=-14, lean=8, knees=12)
    sp.update(sword_arm(D("r", -0.05, 1.0, -0.10), D("r", -0.05, 1.0, -0.15), D("r", -1.0, 0.10, -0.10), thumb=D("r", 0.0, 1.0, -0.15)))
    return balance(sp, 0.55, -0.2, -0.7)


def rest_pose(ctx):
    sp = C.body(ctx, knees=3.0)
    sp.update(C.arm("l", D("l", 0.21, 0.05, -1), D("l", 0.12, 0.30, -1), D("l", 0.05, 0.36, -1), curl=16, thumb=8))
    sp.update(low_guard()); return sp


def add_thumb_op(ctx, arm_obj):
    """('thumb', v): the hand turned about its own axis until the thumb points as near v as it can (a sword lies along it)"""
    B = arm_obj.data.bones
    for h in ("hand_l", "hand_r"):
        s = h[-1]; q = B[h].matrix_local.to_quaternion()
        th = (B[f"thumb_01_{s}"].head_local - B[h].head_local)
        along = (B[f"middle_01_{s}"].head_local - B[h].head_local).normalized()
        th = (th - along * th.dot(along)).normalized()                  # (the thumb side of the hand, across the fingers)
        ctx.setdefault("thumb", {})[h] = q.inverted() @ th


def apply(arm_obj, spec, ctx):
    """caster_clips.apply with the 'thumb' operation"""
    for pb in arm_obj.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    for pb in ctx["order"]:
        ops = spec.get(pb.name)
        if not ops: continue
        M = pb.matrix.copy(); head = M.translation.copy(); rot = M.to_quaternion(); scl = M.to_scale()
        for op in ops:
            k = op[0]; cur = rot @ Vector((0.0, 1.0, 0.0))
            if k == "dir": rot = cur.rotation_difference(op[1]) @ rot
            elif k == "twist": rot = Quaternion(cur, math.radians(op[1])) @ rot
            elif k == "rot": rot = Quaternion(op[1], math.radians(op[2])) @ rot
            elif k in ("toward", "curl"):
                to = op[1] if k == "toward" else arm_obj.pose.bones[ctx["hand_of"][pb.name]].matrix.to_quaternion() @ ctx["palm"][ctx["hand_of"][pb.name]]
                ax = cur.cross(to)
                if ax.length > 1e-6: rot = Quaternion(ax.normalized(), math.radians(op[2] if k == "toward" else op[1])) @ rot
            elif k == "blade":
                b = op[1].normalized(); f = op[2] - b * op[2].dot(b)
                if f.length < 1e-4: f = Vector((0.0, 0.0, -1.0)) - b * (-b.z)
                rot = cur.rotation_difference(f.normalized()) @ rot; cur = rot @ Vector((0.0, 1.0, 0.0))
                th = rot @ ctx["thumb"][pb.name]; want = b - cur * b.dot(cur)
                if want.length > 1e-6:
                    want.normalize(); ang = th.angle(want); sgn = 1.0 if th.cross(want).dot(cur) >= 0 else -1.0
                    rot = Quaternion(cur, sgn * ang) @ rot
            elif k == "thumb":
                th = rot @ ctx["thumb"][pb.name]; want = op[1] - cur * op[1].dot(cur)
                if want.length > 1e-6:
                    want.normalize(); ang = th.angle(want); sgn = 1.0 if th.cross(want).dot(cur) >= 0 else -1.0
                    rot = Quaternion(cur, sgn * ang) @ rot
            elif k == "rest": rot = pb.bone.matrix_local.to_quaternion()
            elif k == "move": head = head + op[1]
        pb.matrix = Matrix.LocRotScale(head, rot, scl)
        bpy.context.view_layer.update()
    return {pb.name: pb.matrix_basis.decompose() for pb in arm_obj.pose.bones}


TIMES = {"CastL1": (0.32, 0.46, 0.70, 1.25), "CastL2": (0.42, 0.58, 0.85, 1.35), "Slash1": (0.30, 0.44, 0.64, 1.10), "Slash2": (0.36, 0.52, 0.74, 1.20), "Slash3": (0.28, 0.40, 0.62, 1.05)}
MAKERS = {"CastL1": cast_l1, "CastL2": cast_l2, "Slash1": slash1, "Slash2": slash2, "Slash3": slash3}


def make_clips(arm_obj, scene, clips):
    ctx = C.context(arm_obj); add_thumb_op(ctx, arm_obj)
    P = lambda spec: apply(arm_obj, spec, ctx)
    # her own clips: the right hand closed on the hilt in every frame (a finger's local turn does not depend on the arm)
    closed = P(fist("r"))
    keep = [b for b in closed if b.endswith("_r") and b.split("_")[0] in C.FINGERS + ("thumb",)]
    for name, frames in clips.items():
        for fr in frames:
            for b in keep: fr[b] = (fr[b][0], closed[b][1], fr[b][2])
    r0 = P(rest_pose(ctx)); out = {}
    for name, fn in MAKERS.items():
        tw, tr, tf, te = TIMES[name]
        out[name] = C.sample([(0.0, r0), (tw, P(fn(ctx, "wind"))), (tr, P(fn(ctx, "release"))), (tf, P(fn(ctx, "follow"))), (te, r0)])
    for pb in arm_obj.pose.bones: pb.matrix_basis.identity()
    return out


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:]
    src, prefix = argv[0], argv[1]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    sc = bpy.context.scene
    for o in [o for o in sc.objects if o.type == 'MESH' and not o.vertex_groups]: bpy.data.objects.remove(o, do_unlink=True)
    arm_obj = next(o for o in sc.objects if o.type == 'ARMATURE')
    if arm_obj.animation_data: arm_obj.animation_data.action = None
    for pb in arm_obj.pose.bones: pb.rotation_mode = 'QUATERNION'; pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    # a stand-in blade on the right hand: from the closed hand along the thumb's way (as the grip will hold it)
    B = arm_obj.data.bones; ctx0 = C.context(arm_obj); add_thumb_op(ctx0, arm_obj)
    hq = B["hand_r"].matrix_local.to_quaternion(); th = hq @ ctx0["thumb"]["hand_r"]
    fore = (B["hand_r"].head_local - B["lowerarm_r"].head_local).normalized()
    grip = B["hand_r"].head_local + fore * 0.04
    bpy.ops.mesh.primitive_cylinder_add(radius=0.006, depth=0.55, location=grip + th * 0.25)
    blade = bpy.context.active_object; blade.rotation_euler = th.to_track_quat('Z', 'Y').to_euler()
    mat = bpy.data.materials.new("blade"); mat.diffuse_color = (0.1, 0.9, 1.0, 1.0); blade.data.materials.append(mat)
    bpy.context.view_layer.update(); mw = blade.matrix_world.copy()
    blade.parent = arm_obj; blade.parent_type = 'BONE'; blade.parent_bone = "hand_r"; blade.matrix_world = mw
    clips = make_clips(arm_obj, sc, {})
    ctx = C.context(arm_obj); add_thumb_op(ctx, arm_obj); R_ = Vector((-1.0, 0.0, 0.0))
    for name, fn in MAKERS.items():
        for k in ("wind", "release", "follow"):
            spec = fn(ctx, k); apply(arm_obj, spec, ctx)
            pb = arm_obj.pose.bones["hand_r"]; th = pb.matrix.to_quaternion() @ ctx["thumb"]["hand_r"]
            want = next((op[1] for op in spec["hand_r"] if op[0] in ("thumb", "blade")), None)
            f = lambda v: "(%+.2f out, %+.2f fwd, %+.2f up)" % (v.dot(R_), v.dot(F), v.dot(U))
            print("BLADE %-7s %-8s %s  wanted %s  off %.0f deg" % (name, k, f(th), f(want) if want else "-", math.degrees(th.angle(want)) if want else -1))
    for pb in arm_obj.pose.bones: pb.matrix_basis.identity()
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'MATERIAL'; sc.display.shading.light = 'STUDIO'
    sc.render.resolution_x = 320; sc.render.resolution_y = 460
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.5
    for name, frames in clips.items():
        for fi in [int(round(t * C.FPS)) for t in TIMES[name][:3]]:
            for pb in arm_obj.pose.bones:
                l, q, s = frames[fi][pb.name]; pb.location = l; pb.rotation_quaternion = q; pb.scale = s
            bpy.context.view_layer.update()
            for view, ang in (("front", 0), ("side", 90), ("q", 40)):
                a = math.radians(ang); d = Vector((math.sin(a), -math.cos(a), 0.0))
                cam.location = Vector((0, 0, 0.6)) + d * 4.0; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
                sc.render.filepath = f"{prefix}_{name}_{fi:02d}_{view}.png"; bpy.ops.render.render(write_still=True)
    print("DONE", list(clips))
