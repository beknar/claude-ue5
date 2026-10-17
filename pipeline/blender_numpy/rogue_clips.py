"""Clips for the Rogue (ai models/Rogue.glb; tripo_build.py's clip_maker), on her own rig: a dagger in each hand, a
crossbow, and a roll (random_dungeonmagic_level3). Her own Walk and Run are kept, with both hands closed on a grip in
every frame (a dagger in each, or the crossbow in the right); made for her:
  Idle     3.2 s loop: a low guard, the daggers forward in both hands, breathing
  Stab1    a thrust with the right dagger (the left held back by her chest)
  Stab2    a backhand cut with the left: from by her right shoulder out to her left
  Stab3    both at once: crossed high in front of her face, cut down and out
  Shoot    the crossbow raised to her right shoulder (right hand on the stock, left under the front), the shot, lowered
  RollF    a forward roll (in place: the game moves her), tucked, once round
  RollB    the same played backward: a backward roll
Poses are written as in caster_clips.py / darkcaster_clips.py (where the bones point, armature space: she faces -Y, her
right is -X); `blade` turns a hand so its thumb points exactly where the blade (or the crossbow) is to point: the grips of
pipeline/unreal/822 put a dagger's blade, and the crossbow's front, the way the thumb points in her reference pose.
In a roll the tucked body turns about her side axis and is lowered until its lowest point (bones and their flesh)
touches the floor. The strike times are measured on the imported clips (822: where the striking hand moves fastest);
the shot's release, which no hand speed marks, is written to times.json beside the build (TIMES below).
Preview (key poses with the real weapons, exported from Unreal as OBJ into a folder):
  blender -b -P rogue_clips.py -- model.glb out_prefix [weapons_dir]"""
import json, math, os, sys
import bpy
from mathutils import Matrix, Vector, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import caster_clips as C
import darkcaster_clips as DC
D, F, U, LEAN = C.D, C.F, C.U, C.LEAN
FPS = C.FPS


def hold(side, up, low, hand, thumb):
    """an arm with a closed hand: upper arm, forearm, the hand's way, and where its thumb (the blade) points"""
    sp = {f"upperarm_{side}": [("dir", up)], f"lowerarm_{side}": [("dir", low)], f"hand_{side}": [("blade", thumb, hand)]}
    sp.update(DC.fist(side)); return sp


def guard(side, k=0.0):
    """the low guard: forearm forward, the dagger forward and a little down (k: breathing)"""
    return hold(side, D(side, 0.24 + 0.01 * k, 0.18, -1.0), D(side, 0.10, 0.75 + 0.02 * k, -0.62), D(side, 0.0, 0.85, -0.5), D(side, -0.08, 1.0, -0.18))


def idle(ctx, k=0.0):
    sp = C.body(ctx, lean=1.0 - 1.6 * k, knees=6.0)
    sp.update(guard("r", k)); sp.update(guard("l", k)); return sp


def stab1(ctx, k):
    if k == "wind":
        sp = C.body(ctx, twist=28, lean=-2, knees=10)
        sp.update(hold("r", D("r", 0.35, -0.55, -0.75), D("r", 0.05, 0.95, 0.15), D("r", 0.0, 1.0, -0.1), D("r", -0.05, 1.0, 0.05)))
        sp.update(hold("l", D("l", 0.30, 0.55, -0.75), D("l", -0.35, 0.90, 0.30), D("l", -0.2, 0.9, 0.2), D("l", -0.25, 1.0, 0.35)))
    elif k == "release":
        sp = C.body(ctx, twist=-22, lean=11, knees=15)
        sp.update(hold("r", D("r", -0.06, 1.0, 0.04), D("r", -0.08, 1.0, 0.02), D("r", -0.05, 1.0, -0.05), D("r", -0.02, 1.0, 0.0)))
        sp.update(hold("l", D("l", 0.45, -0.35, -0.82), D("l", -0.25, 0.90, 0.40), D("l", -0.3, 0.8, 0.4), D("l", -0.2, 0.6, 0.8)))
    else:
        sp = C.body(ctx, twist=-14, lean=8, knees=12)
        sp.update(hold("r", D("r", 0.02, 0.95, -0.25), D("r", -0.02, 0.95, -0.25), D("r", 0.0, 0.9, -0.4), D("r", 0.0, 1.0, -0.2)))
        sp.update(guard("l"))
    return sp


def stab2(ctx, k):
    if k == "wind":
        sp = C.body(ctx, twist=30, lean=-3, knees=10)
        sp.update(hold("l", D("l", -0.35, 0.55, 0.15), D("l", -0.85, 0.15, 0.50), D("l", -0.6, -0.1, 0.8), D("l", -0.45, -0.35, 0.85)))
        sp.update(guard("r"))
    elif k == "release":
        sp = C.body(ctx, twist=-18, lean=9, knees=14)
        sp.update(hold("l", D("l", 0.25, 1.0, 0.10), D("l", 0.55, 0.85, 0.0), D("l", 0.6, 0.8, -0.05), D("l", 0.45, 0.9, 0.05)))
        sp.update(hold("r", D("r", 0.45, -0.25, -0.85), D("r", -0.30, 0.85, 0.40), D("r", -0.3, 0.8, 0.4), D("r", -0.2, 0.6, 0.8)))
    else:
        sp = C.body(ctx, twist=-30, lean=7, knees=12)
        sp.update(hold("l", D("l", 0.80, 0.45, -0.25), D("l", 0.95, 0.10, -0.25), D("l", 0.9, -0.15, -0.3), D("l", 0.75, -0.6, -0.1)))
        sp.update(guard("r"))
    return sp


def stab3(ctx, k):
    if k == "wind":
        sp = C.body(ctx, twist=0, lean=-6, knees=9)
        for s in "rl":
            sp.update(hold(s, D(s, 0.15, 0.55, 0.80), D(s, -0.80, 0.30, 0.55), D(s, -0.7, 0.1, 0.7), D(s, -0.25, -0.35, 0.9)))
    elif k == "release":
        sp = C.body(ctx, twist=0, lean=12, knees=16)
        for s in "rl":
            sp.update(hold(s, D(s, 0.30, 0.95, -0.05), D(s, 0.45, 0.85, -0.25), D(s, 0.5, 0.8, -0.3), D(s, 0.35, 0.9, -0.25)))
    else:
        sp = C.body(ctx, twist=0, lean=9, knees=13)
        for s in "rl":
            sp.update(hold(s, D(s, 0.75, 0.45, -0.50), D(s, 0.80, 0.25, -0.55), D(s, 0.8, 0.1, -0.6), D(s, 0.55, 0.5, -0.65)))
    return sp


def reach(side, at, pole):
    """the arm bent so the hand's root is at `at` (cm from the base of her neck: (her right, forward, up)), the elbow toward
    `pole`"""
    return {f"upperarm_{side}": [("reach", at, pole)], f"lowerarm_{side}": [("reach2",)]}


def shoot(ctx, k):
    """the crossbow at her right shoulder: the right hand on the stock under her chin (fingers down round it, the thumb
    along it toward the front: the stock's butt then lies at her shoulder), the left hand under the forestock"""
    up, back = {"aim": (0.0, 0.0), "kick": (2.5, 4.0), "hold": (0.8, 1.0)}[k]
    sp = C.body(ctx, twist=24, lean=4 - 0.8 * up, knees=9, look=0.95)
    sp.update(reach("r", (9.0, 16.0 - back, -3.0 + up), D("r", 0.7, -0.3, -0.65)))
    sp["hand_r"] = [("blade", D("r", 0.0, 1.0, 0.03 + 0.03 * up), D("r", -0.1, 0.35, -0.95))]; sp.update(DC.fist("r"))
    sp.update(reach("l", (5.0, 28.0 - back, -9.0 + up), D("l", 0.3, 0.1, -1.0)))
    sp["hand_l"] = [("dir", D("l", -0.55, 0.8, 0.15)), ("twist", -75.0)]
    for fn in C.FINGERS:
        for kk, w in (("01", 0.7), ("02", 1.0), ("03", 0.8)): sp[f"{fn}_{kk}_l"] = [("curl", 40 * w)]
    return sp


def tuck(ctx):
    """curled for a roll: chin in, back round, knees to the chest, the hands (and what they hold) in by the shins"""
    sp = {}
    for b, w in (("spine_01", 0.3), ("spine_02", 0.35), ("spine_03", 0.35)): sp[b] = [("rot", LEAN, 78 * w)]
    sp["neck_01"] = [("rot", LEAN, 28)]; sp["head"] = [("rot", LEAN, 18)]
    for s in "lr":
        sp[f"thigh_{s}"] = [("toward", F, 118.0)]
        sp[f"calf_{s}"] = [("toward", -F, 140.0)]
        sp[f"foot_{s}"] = [("toward", -U, 40.0)]
    sp.update(hold("r", D("r", 0.25, 0.75, -0.6), D("r", -0.15, 0.2, -1.0), D("r", -0.1, -0.2, -1.0), D("r", 0.0, -0.6, -0.8)))
    sp.update(hold("l", D("l", 0.25, 0.75, -0.6), D("l", -0.15, 0.2, -1.0), D("l", -0.1, -0.2, -1.0), D("l", 0.0, -0.6, -0.8)))
    return sp


# flesh round each bone (cm; Tripo's model is one metre tall, made 170 cm by tripo_build): the floor test of a roll
FLESH = {"pelvis": 13, "spine_01": 13, "spine_02": 13, "spine_03": 12, "neck_01": 6, "head": 11, "thigh": 8, "calf": 6, "foot": 4, "ball": 3,
         "upperarm": 5, "lowerarm": 4, "hand": 4}


def lowest(arm_obj, cm):
    """the lowest point of her body (each bone from head to tail, less its flesh), in armature units"""
    lo = 1e9
    for pb in arm_obj.pose.bones:
        key = pb.name if pb.name in FLESH else pb.name.rsplit("_", 1)[0]
        if key not in FLESH: continue
        for t in (0.0, 0.5, 1.0):
            p = pb.head.lerp(pb.tail, t)
            lo = min(lo, p.z - FLESH[key] * cm)
    return lo


def spun(arm_obj, ctx, spec, angle, cm, floor_z):
    """the pose `spec`, turned forward by `angle` degrees about her side axis through her middle, set on the floor"""
    DC.apply(arm_obj, spec, ctx)
    pb = arm_obj.pose.bones["pelvis"]
    M = pb.matrix.copy(); pivot = M.translation + Vector((0.0, 0.0, 0.10 * 100 * cm))
    R = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(angle), 4, LEAN) @ Matrix.Translation(-pivot)
    pb.matrix = R @ M; bpy.context.view_layer.update()
    dz = floor_z - lowest(arm_obj, cm)
    pb.matrix = Matrix.Translation(Vector((0.0, 0.0, dz))) @ pb.matrix; bpy.context.view_layer.update()
    return {p.name: p.matrix_basis.decompose() for p in arm_obj.pose.bones}


TIMES = {"Stab1": (0.16, 0.26, 0.40, 0.70), "Stab2": (0.18, 0.29, 0.44, 0.74), "Stab3": (0.20, 0.32, 0.48, 0.80)}
MAKERS = {"Stab1": stab1, "Stab2": stab2, "Stab3": stab3}
SHOT = {"aim": 0.24, "kick": 0.42, "hold": 0.60, "end": 0.95}           # the bolt leaves at RELEASE
RELEASE = 0.40
ROLL = [(0.0, None, 0), (0.10, "tuck", 25), (0.22, "tuck", 115), (0.34, "tuck", 205), (0.46, "tuck", 295), (0.58, "tuck", 360), (0.80, None, 0)]


def model_height(scene):
    """her height in armature units (the model before tripo_build scales it to 170 cm)"""
    me = next(o for o in scene.objects if o.type == 'MESH' and o.vertex_groups)
    zs = [(me.matrix_world @ v.co).z for v in me.data.vertices]
    return max(zs) - min(zs)


def apply(arm_obj, spec, ctx):
    """darkcaster_clips.apply with two more operations: ('reach', at, pole) on an upper arm and ('reach2',) on its forearm
    put the hand's root at a point (two bones, the elbow toward the pole)"""
    cm = ctx["cm"]; targets = {}
    for pb in arm_obj.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    plain = {}
    for name, ops in spec.items():
        if ops and ops[0][0] in ("reach", "reach2"):
            pb = arm_obj.pose.bones[name]; side = name[-1]
            if ops[0][0] == "reach": targets[side] = ops[0]
            continue
        plain[name] = ops
    if not targets: return DC.apply(arm_obj, spec, ctx)
    # pose everything else first, then each reaching arm (shoulder, then elbow), keeping what was set
    DC.apply(arm_obj, plain, ctx)
    B = arm_obj.data.bones
    for side, (_, at, pole) in targets.items():
        neck = arm_obj.pose.bones["neck_01"].head
        goal = neck + (C.OUT["r"] * at[0] + F * at[1] + U * at[2]) * cm
        ua, la = arm_obj.pose.bones[f"upperarm_{side}"], arm_obj.pose.bones[f"lowerarm_{side}"]
        a = (B[f"lowerarm_{side}"].head_local - B[f"upperarm_{side}"].head_local).length
        b = (B[f"hand_{side}"].head_local - B[f"lowerarm_{side}"].head_local).length
        d = goal - ua.head; dist = min(d.length, (a + b) * 0.999); dn = d.normalized()
        cosA = max(-1.0, min(1.0, (a * a + dist * dist - b * b) / (2 * a * dist))); A = math.acos(cosA)
        p = pole - dn * pole.dot(dn); p.normalize()
        for pb_, want in ((ua, dn * math.cos(A) + p * math.sin(A)), (la, None)):
            if want is None: want = (goal - pb_.head).normalized()
            M = pb_.matrix.copy(); rot = M.to_quaternion(); cur = rot @ Vector((0.0, 1.0, 0.0))
            pb_.matrix = Matrix.LocRotScale(M.translation, cur.rotation_difference(want) @ rot, M.to_scale()); bpy.context.view_layer.update()
        # the hand again (its ops are absolute, and the arm has moved; the fingers' turns are their own and go with it)
        rest = {n: o for n, o in plain.items() if n == f"hand_{side}"}
        for n, ops in rest.items():
            pb_ = arm_obj.pose.bones[n]; M = pb_.matrix.copy(); rot = M.to_quaternion(); head = M.translation.copy(); scl = M.to_scale()
            if n.startswith("hand_"):
                pb_.matrix_basis.identity(); bpy.context.view_layer.update(); M = pb_.matrix.copy(); rot = M.to_quaternion()
            for op in ops:
                k = op[0]; cur = rot @ Vector((0.0, 1.0, 0.0))
                if k == "dir": rot = cur.rotation_difference(op[1]) @ rot
                elif k == "twist": rot = Quaternion(cur, math.radians(op[1])) @ rot
                elif k == "curl":
                    hq = arm_obj.pose.bones[ctx["hand_of"][n]].matrix.to_quaternion() @ ctx["palm"][ctx["hand_of"][n]]
                    ax = cur.cross(hq)
                    if ax.length > 1e-6: rot = Quaternion(ax.normalized(), math.radians(op[1])) @ rot
                elif k == "blade":
                    bb = op[1].normalized(); f = op[2] - bb * op[2].dot(bb)
                    rot = cur.rotation_difference(f.normalized()) @ rot; cur = rot @ Vector((0.0, 1.0, 0.0))
                    th = rot @ ctx["thumb"][n]; want = bb - cur * bb.dot(cur)
                    if want.length > 1e-6:
                        want.normalize(); ang = th.angle(want); sgn = 1.0 if th.cross(want).dot(cur) >= 0 else -1.0
                        rot = Quaternion(cur, sgn * ang) @ rot
            pb_.matrix = Matrix.LocRotScale(head, rot, scl); bpy.context.view_layer.update()
    return {pb.name: pb.matrix_basis.decompose() for pb in arm_obj.pose.bones}


def make_clips(arm_obj, scene, clips):
    ctx = C.context(arm_obj); DC.add_thumb_op(ctx, arm_obj); ctx["cm"] = model_height(scene) / 170.0
    P = lambda spec: apply(arm_obj, spec, ctx)
    # her own clips: both hands closed on a grip in every frame (a finger's local turn does not depend on the arm)
    closed = P({**DC.fist("r"), **DC.fist("l")})
    keep = [b for b in closed if b.split("_")[0] in C.FINGERS + ("thumb",)]
    for name, frames in clips.items():
        for fr in frames:
            for b in keep: fr[b] = (fr[b][0], closed[b][1], fr[b][2])
    i0, i1 = P(idle(ctx)), P(idle(ctx, 1.0)); out = {"Idle": C.sample([(0.0, i0), (1.6, i1), (3.2, i0)])}
    for name, fn in MAKERS.items():
        tw, tr, tf, te = TIMES[name]
        out[name] = C.sample([(0.0, i0), (tw, P(fn(ctx, "wind"))), (tr, P(fn(ctx, "release"))), (tf, P(fn(ctx, "follow"))), (te, i0)])
    out["Shoot"] = C.sample([(0.0, i0), (SHOT["aim"], P(shoot(ctx, "aim"))), (RELEASE, P(shoot(ctx, "aim"))), (SHOT["kick"], P(shoot(ctx, "kick"))),
                             (SHOT["hold"], P(shoot(ctx, "hold"))), (SHOT["end"], i0)])
    # the roll: the floor is where her feet are in the idle (its lowest bone point less the flesh)
    cm = model_height(scene) / 170.0
    P(idle(ctx)); floor_z = min(arm_obj.pose.bones[f"ball_{s}"].head.z for s in "lr") - FLESH["ball"] * cm
    keys = [(t, i0 if spec is None else spun(arm_obj, ctx, tuck(ctx), ang, cm, floor_z)) for t, spec, ang in ROLL]
    out["RollF"] = C.sample(keys)
    out["RollB"] = list(reversed(out["RollF"]))
    for pb in arm_obj.pose.bones: pb.matrix_basis.identity()
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) > 1 and os.path.isdir(argv[1]):
        json.dump({"Shoot": {"release": RELEASE, "length": SHOT["end"]}, "Roll": {"length": ROLL[-1][0], "turn": [ROLL[1][0], ROLL[-2][0]]},
                   "Stabs": {k: {"wind": v[0], "release": v[1], "follow": v[2], "end": v[3]} for k, v in TIMES.items()}},
                  open(os.path.join(argv[1], "times.json"), "w"), indent=1)
    return out


# ---------------------------------------------------------------- preview with the weapons
def ue_frame(X, Z):
    """FRotationMatrix::MakeFromXZ: X exact, Z made square to it"""
    x = X.normalized(); y = Z.normalized().cross(x).normalized(); z = x.cross(y)
    return x, y, z


def weapon_points(obj_path):
    """an OBJ written by Unreal's exporter: (x, z, y) of the mesh's own axes -> Unreal's (x, y, z)"""
    vs, fs = [], []
    for line in open(obj_path):
        if line.startswith("v "):
            a, b, c = map(float, line.split()[1:4]); vs.append(Vector((a, c, b)))
        elif line.startswith("f "):
            fs.append([int(t.split("/")[0]) - 1 for t in line.split()[1:]])
    return vs, fs


def place(arm_obj, name, pts, faces, bone, frame, at, unit, colour):
    """the weapon placed on the reference pose as 822 places it (Unreal component space: Blender (x, -y, z) x 170 / height),
    then parented to the bone"""
    X, Y, Z = frame
    to_b = lambda p: Vector((p.x, -p.y, p.z)) * unit
    verts = [to_b(X * p.x + Y * p.y + Z * p.z + at) for p in pts]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    m = bpy.data.materials.new(name); m.diffuse_color = colour; me.materials.append(m)
    mw = ob.matrix_world.copy(); ob.parent = arm_obj; ob.parent_type = 'BONE'; ob.parent_bone = bone; ob.matrix_world = mw
    return ob


def grips(arm_obj, wdir):
    """the grips of 822 (dagger in each hand, crossbow in the right), worked out on the reference pose in Unreal's frame"""
    B = arm_obj.data.bones; S = 170.0 / model_height(bpy.context.scene)          # armature units -> cm
    ue = lambda v: Vector((v.x, -v.y, v.z)) * S
    out = []
    dag, dag_f = weapon_points(os.path.join(wdir, "SM_Dagger.obj")); xb, xb_f = weapon_points(os.path.join(wdir, "SM_Crossbow.obj"))
    for s in "rl":
        hand = ue(B[f"hand_{s}"].head_local); fore = (hand - ue(B[f"lowerarm_{s}"].head_local)).normalized()
        th = ue(B[f"thumb_01_{s}"].head_local) - hand; along = (ue(B[f"middle_01_{s}"].head_local) - hand).normalized()
        th = th - along * th.dot(along); th = (th - fore * th.dot(fore)).normalized()
        palm = hand + fore * 6.5 + Vector((0.0, 0.0, -2.5))
        Xd, Yd, Zd = ue_frame(fore, -th)                        # (the dagger's handle is at +Z, its blade toward -Z: blade -> thumb)
        out.append(place(arm_obj, f"dagger_{s}", dag, dag_f, f"hand_{s}", (Xd, Yd, Zd), palm - Zd * 28.5, 1.0 / S, (0.75, 0.8, 0.9, 1)))
        if s == "r":
            Xc, Yc, Zc = ue_frame(-th, -fore)                   # (the crossbow's front is -X, its rail up +Z)
            out.append(place(arm_obj, "crossbow", xb, xb_f, "hand_r", (Xc, Yc, Zc), palm - (Xc * 31.0 + Zc * 0.5), 1.0 / S, (0.9, 0.7, 0.2, 1)))
    return out


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:]
    src, prefix = argv[0], argv[1]; wdir = argv[2] if len(argv) > 2 else None
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    sc = bpy.context.scene
    for o in [o for o in sc.objects if o.type == 'MESH' and not o.vertex_groups]: bpy.data.objects.remove(o, do_unlink=True)
    arm_obj = next(o for o in sc.objects if o.type == 'ARMATURE')
    if arm_obj.animation_data: arm_obj.animation_data.action = None
    for pb in arm_obj.pose.bones: pb.rotation_mode = 'QUATERNION'; pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    weps = grips(arm_obj, wdir) if wdir else []
    clips = make_clips(arm_obj, sc, {})
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'MATERIAL'; sc.display.shading.light = 'STUDIO'
    sc.render.resolution_x = 360; sc.render.resolution_y = 460
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.3
    show = lambda which: [setattr(w, "hide_render", not any(k in w.name for k in which)) for w in weps]
    picks = {"Idle": [0], "Stab1": [round(t * FPS) for t in TIMES["Stab1"][:3]], "Stab2": [round(t * FPS) for t in TIMES["Stab2"][:3]],
             "Stab3": [round(t * FPS) for t in TIMES["Stab3"][:3]], "Shoot": [round(SHOT["aim"] * FPS), round(SHOT["kick"] * FPS)],
             "RollF": [round(t * FPS) for t, _, _ in ROLL[1:-1]]}
    for name, fis in picks.items():
        show(("crossbow",) if name == "Shoot" else ("dagger",))
        for fi in fis:
            for pb in arm_obj.pose.bones:
                l, q, s = clips[name][fi][pb.name]; pb.location = l; pb.rotation_quaternion = q; pb.scale = s
            bpy.context.view_layer.update()
            for view, ang in (("front", 0), ("side", 90), ("q", 40)):
                a = math.radians(ang); d = Vector((math.sin(a), -math.cos(a), 0.0))
                cam.location = Vector((0, 0, 0.5)) + d * 4.0; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
                sc.render.filepath = f"{prefix}_{name}_{fi:02d}_{view}.png"; bpy.ops.render.render(write_still=True)
    print("DONE", {k: len(v) for k, v in clips.items()})
