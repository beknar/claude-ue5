"""Clips for the Martial Artist (ai models/MartialArtist2.glb; tripo_build.py's clip_maker, tag MartialArtist), on her own
rig (the user's of 2026-10-28). Her own clips are kept as Tripo made them (Walk, Run, Box_01-03 and Front_kick_01-02: her
basic punches and kicks), each recentred where it holds her pelvis off its rest place (warrior3_clips.recentre); her
Dance_01 and Run_upstairs are dropped. Made for her:
  Idle            a fighting stance (left foot forward, fists up by her chin), breathing; 2.4 s loop
  Stab1-3, RollF, RollB   rogue_clips.py's (a knife in each hand; the dodge's roll), solved on her rig
  Dash            a low lunge held while the game carries her forward (0.5 s)
  Chi_<Name>      the ten chi attacks, each a move that looks like its name (CHI below)
Poses are written as in rogue_clips.py: her body by its spine's twist and lean, her pelvis dropped or moved, her arms
solved to a place for the hand (cm from the base of her neck: her right, forward, up; rogue_clips.solve_arm: the elbow a
hinge, the wrist within its limits); her legs are solved here (solve_leg): a foot planted at a place on the floor (cm
from where it stands in her reference pose), the knee toward a pole, the foot flat and turned by a yaw, or a kicking leg
given by the ways its thigh, calf and foot point. A pose can be turned about the up axis as a whole (`yaw`: the spinning
kick); everything given in her own frame is turned with it.
Writes <out_dir>/ma_times.json: each made clip's length and the time its blow lands (`hit`), the limb that strikes, and
rogue_clips' times.json (the stabs, the roll, the knives' grip tilt).
Preview: blender -b -P martialartist_clips.py -- model.glb out_prefix [clip,clip...]"""
import json, math, os, sys
import bpy
from mathutils import Matrix, Vector, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import caster_clips as C
import darkcaster_clips as DC
import rogue_clips as R
FPS = C.FPS
F, U, LEAN = C.F, C.U, C.LEAN
RIGHT = C.OUT["r"]


def rz(v, deg):
    return Quaternion(U, math.radians(deg)) @ v if deg else v.copy()


class Fr:
    """her own frame, turned `yaw` degrees about the up axis (positive: toward her left, seen from above anticlockwise)"""
    def __init__(self, yaw=0.0): self.yaw = yaw
    def v(self, w): return rz(w, self.yaw)
    def D(self, side, o, f, u): return self.v(C.D(side, o, f, u))
    def at(self, x, y, z):
        w = self.v(RIGHT * x + F * y)
        return (w.dot(RIGHT), w.dot(F), z)


def fist(side): return DC.fist(side)


def open_hand(side, curl=4.0):
    sp = {}
    for fn in C.FINGERS:
        for k, w in (("01", 0.6), ("02", 1.0), ("03", 0.8)): sp[f"{fn}_{k}_{side}"] = [("curl", curl * w)]
    sp[f"thumb_02_{side}"] = [("curl", 6.0)]; sp[f"thumb_03_{side}"] = [("curl", 4.0)]
    return sp


def hand(fr, side, x, y, z, pole, axis=None, palm=None, closed=True):
    """the hand's root at (x her right, y forward, z up) cm from the base of her neck, the elbow toward `pole`, the hand's
    own way (wrist to knuckles) `axis` and its palm facing `palm` as near as the wrist allows"""
    want = {}
    if axis is not None: want["axis"] = fr.v(axis)
    if palm is not None: want["palm"] = fr.v(palm)
    sp = {f"arm_{side}": ("reach", fr.at(x, y, z), fr.v(pole), want, None)}
    sp.update(fist(side) if closed else open_hand(side))
    return sp


def body(ctx, fr, twist=0.0, lean=0.0, side=0.0, drop=0.0, fwd=0.0, look=0.75, hips=0.0):
    """twist: her shoulders turned to her right (degrees); lean: forward; side: toward her left; drop: the pelvis down (cm;
    negative: up); fwd: the pelvis forward (cm); hips: the share of the twist the pelvis takes"""
    cm = ctx["cm"]; sp = {}
    pel = []
    if fr.yaw: pel.append(("rot", U, fr.yaw))
    if hips: pel.append(("rot", U, -twist * hips))
    mv = U * (-drop) + fr.v(F) * fwd
    if mv.length > 1e-6: pel.append(("move", mv * cm))
    if pel: sp["pelvis"] = pel
    for b, w in (("spine_01", 0.3), ("spine_02", 0.35), ("spine_03", 0.35)):
        sp[b] = [("rot", U, -twist * w * (1.0 - hips)), ("rot", fr.v(LEAN), lean * w), ("rot", fr.v(F), -side * w)]
    sp["neck_01"] = [("rot", U, twist * look), ("rot", fr.v(LEAN), -lean * 0.45), ("rot", fr.v(F), side * 0.5)]
    return sp


def plant(side, x, y, z=0.0, yaw=0.0, pole=None, pitch=0.0):
    """the foot at (x her right, y forward, z up) cm from where it stands in her reference pose (her own frame, unturned),
    turned `yaw` degrees (positive: the toes to her left), its toes `pitch` degrees down (on the ball of the foot)"""
    return {f"leg_{side}": ("plant", (x, y, z), yaw, pole, pitch)}


def under(side, y=0.0, yaw=0.0, pole=None, pitch=0.0):
    """the foot under her pelvis (y cm forward of it), on the floor: the foot she turns on"""
    return {f"leg_{side}": ("under", y, yaw, pole, pitch)}


def kick(side, thigh, calf, foot, pole):
    return {f"leg_{side}": ("kick", thigh, calf, foot, pole)}


# ---------------------------------------------------------------- the legs
def leg_context(ctx, arm_obj):
    B = arm_obj.data.bones; ctx["legs_rest"] = {}
    for s in "lr":
        H0, K0, A0 = B[f"thigh_{s}"].head_local, B[f"calf_{s}"].head_local, B[f"foot_{s}"].head_local
        ctx["legs_rest"][s] = {"a": (K0 - H0).length, "b": (A0 - K0).length, "ankle": A0.copy(),
                               "qf": B[f"foot_{s}"].matrix_local.to_quaternion(), "qb": B[f"ball_{s}"].matrix_local.to_quaternion()}
    ctx["floor"] = min(B[f"ball_{s}"].head_local.z for s in "lr")


def aim(pb, y_t, f_t, f_rest):
    """the bone turned so its own way is y_t and its rest `f_rest` way (armature space) faces f_t as near as it can"""
    q0 = pb.bone.matrix_local.to_quaternion(); yl = Vector((0.0, 1.0, 0.0)); fl = q0.inverted() @ f_rest
    fl = (fl - yl * fl.dot(yl)).normalized()
    y_t = y_t.normalized(); ft = f_t - y_t * f_t.dot(y_t)
    if ft.length < 1e-5: ft = (f_rest - y_t * f_rest.dot(y_t))
    ft.normalize()
    Ml = Matrix((yl, fl, yl.cross(fl))).transposed(); Mt = Matrix((y_t, ft, y_t.cross(ft))).transposed()
    q = (Mt @ Ml.inverted()).to_quaternion()
    M = pb.matrix.copy(); pb.matrix = Matrix.LocRotScale(M.translation, q, M.to_scale()); bpy.context.view_layer.update()


def solve_leg(arm_obj, ctx, side, op):
    P = arm_obj.pose.bones; L = ctx["legs_rest"][side]; cm = ctx["cm"]
    th, ca, ft = P[f"thigh_{side}"], P[f"calf_{side}"], P[f"foot_{side}"]
    if op[0] == "kick":
        _, tw, cw, fw, pole = op
        # (the kneecap faces the way the thigh leads the calf (from the bend); `pole` only where the leg is near straight)
        t_, c_ = tw.normalized(), cw.normalized(); kn = t_ - c_; kn = kn - t_ * kn.dot(t_)
        if kn.length > 0.15: pole = kn.normalized()
        aim(th, tw, pole, F); aim(ca, cw, pole, F)
        cur = ft.matrix.to_quaternion() @ Vector((0.0, 1.0, 0.0))
        M = ft.matrix.copy(); ft.matrix = Matrix.LocRotScale(M.translation, cur.rotation_difference(fw.normalized()) @ M.to_quaternion(), M.to_scale())
        bpy.context.view_layer.update(); return
    kind, where, yaw, pole, pitch = op
    if kind == "plant":
        x, y, z = where; T = L["ankle"] + (RIGHT * x + F * y + U * z) * cm
    else:                                                     # under her pelvis
        pv = P["pelvis"].head; fw = rz(F, yaw)
        T = Vector((pv.x, pv.y, L["ankle"].z)) + fw * where * cm
    if pitch: T = T + U * (math.sin(math.radians(pitch)) * 9.0 * cm)        # (on the ball: the ankle higher)
    H = th.head.copy(); a, b = L["a"], L["b"]
    d = T - H; dist = min(d.length, (a + b) * 0.995); dn = d.normalized()
    if d.length > (a + b) * 1.01: print("MA the %s foot falls %.1f cm short of its place" % (side, (d.length - a - b) / cm))
    pole = (pole if pole is not None else rz(F, yaw)).normalized()
    pp = pole - dn * pole.dot(dn)
    if pp.length < 1e-4: pp = rz(F, yaw) - dn * rz(F, yaw).dot(dn)
    pp.normalize()
    ca_ = max(-1.0, min(1.0, (a * a + dist * dist - b * b) / (2 * a * dist))); sa = math.sqrt(1.0 - ca_ * ca_)
    K = H + (dn * ca_ + pp * sa) * a
    aim(th, K - H, pp, F)
    aim(ca, (H + dn * dist) - ca.head, pp, F)
    q = Quaternion(U, math.radians(yaw)) @ L["qf"]
    if pitch:
        side_ax = q @ Vector((1.0, 0.0, 0.0))
        q = Quaternion((Quaternion(U, math.radians(yaw)) @ RIGHT), math.radians(-pitch)) @ q
    M = ft.matrix.copy(); ft.matrix = Matrix.LocRotScale(M.translation, q, M.to_scale()); bpy.context.view_layer.update()


def apply(arm_obj, spec, ctx):
    arms = {k[-1]: v for k, v in spec.items() if k.startswith("arm_")}
    legs = {k[-1]: v for k, v in spec.items() if k.startswith("leg_")}
    DC.apply(arm_obj, {k: v for k, v in spec.items() if not k.startswith(("arm_", "leg_"))}, ctx)
    for side, op in legs.items(): solve_leg(arm_obj, ctx, side, op)
    for side, op in arms.items(): R.solve_arm(arm_obj, ctx, side, op)
    return {pb.name: pb.matrix_basis.decompose() for pb in arm_obj.pose.bones}


# ---------------------------------------------------------------- the poses
def stance(ctx, fr=None, k=0.0, drop=7.0):
    """the fighting stance: left foot forward, right foot back and turned out, knees bent, fists up by her chin"""
    fr = fr or Fr()
    sp = body(ctx, fr, twist=24, lean=4, drop=drop + 0.8 * k, look=0.85)
    sp.update(plant("l", -2, 16, yaw=-8)); sp.update(plant("r", 4, -16, yaw=-38))
    sp.update(hand(fr, "l", -12, 26, 2 - 0.6 * k, fr.D("l", 0.5, 0.0, -1.0), axis=C.D("l", -0.2, 0.6, 0.8), palm=C.D("l", -1.0, 0.0, 0.0)))
    sp.update(right_guard(fr, 14, 28, 2 - 0.6 * k))
    return sp


# Her right fist in the guard (the user's of 2026-10-31: the right forearm merged into her body; the right elbow should flare
# as the left one does). Her shoulders turn 24 degrees to her right in the stance, which carries the left elbow out and
# tucked the right one in: the right fist at (4, 16, -2) put the elbow 1.9 cm and the forearm 1.7 cm inside her body, the
# elbow 4.9 cm out from her chest's middle against the left's 24.2. Its place, elbow and hand are now given in her frame
# turned 40 degrees to her right (a mirror of the left's in her turned chest): measured (a probe against her body as the
# pose bends it), the elbow 22.5 cm out, the elbow 13.1 and the forearm 13.6 cm outside her body (the left's 13.8, 13.6).
RIGHT_GUARD_YAW = -40.0


def right_guard(fr, x, y, z):
    g = Fr(fr.yaw + RIGHT_GUARD_YAW)
    return hand(g, "r", x, y, z, g.D("r", 0.6, 0.0, -0.8), axis=C.D("r", -0.2, 0.6, 0.8), palm=C.D("r", -1.0, 0.0, 0.0))


def guard_l(fr): return hand(fr, "l", -8, 18, 0, fr.D("l", 0.5, 0.0, -1.0), axis=C.D("l", -0.2, 0.5, 0.85), palm=C.D("l", -1.0, 0.0, 0.0))
def guard_r(fr): return right_guard(fr, 12, 24, 0)


def straight_punch(ctx, k):
    fr = Fr()
    if k == "chamber":
        sp = body(ctx, fr, twist=32, lean=3, drop=9); sp.update(plant("l", -2, 18, yaw=-8)); sp.update(plant("r", 4, -16, yaw=-40))
        sp.update(guard_l(fr)); sp.update(hand(fr, "r", 10, 6, -12, fr.D("r", 0.6, -0.2, -1.0), axis=F, palm=-U))
    else:
        ext = 1.0 if k == "release" else 0.85
        sp = body(ctx, fr, twist=-22, lean=9, drop=11, hips=0.35); sp.update(plant("l", -2, 20, yaw=-6)); sp.update(plant("r", 2, -14, yaw=-12, pitch=20))
        sp.update(hand(fr, "l", -6, 12, 0, fr.D("l", 0.5, 0.0, -1.0), axis=U, palm=C.D("l", -1.0, 0.0, 0.0)))
        sp.update(hand(fr, "r", -2, 60 * ext, -4, fr.D("r", 0.3, 0.0, -1.0), axis=F, palm=-U))
    return sp


def side_kick(ctx, k):
    """she turns her right side to the front (the body a quarter turn to her left, on the left foot), the right knee drawn up
    to her chest, then the leg thrust out sideways at hip height, the blade of the foot first, the body leaning away"""
    yaw = {"chamber": 60, "hit": 90, "retract": 75}[k]; fr = Fr(yaw)
    sp = body(ctx, fr, lean=-2, side=30 if k == "hit" else 14, drop=9)
    sp.update(under("l", 0.0, yaw=yaw - 15, pitch=10))
    if k == "hit":
        sp.update(kick("r", fr.D("r", 1.0, 0.0, 0.14), fr.D("r", 1.0, 0.0, 0.16), fr.D("r", 0.15, 0.6, -0.8), fr.v(U)))
    else:
        sp.update(kick("r", fr.D("r", 0.55, 0.45, 0.70), fr.D("r", -0.35, 0.15, -0.92), fr.D("r", 0.1, 0.7, -0.7), fr.v(F)))
    sp.update(guard_l(fr)); sp.update(hand(fr, "r", 16, 8, -16, fr.D("r", 0.6, 0.0, -1.0), axis=C.D("r", 0.4, 0.6, -0.3), palm=C.D("r", -1.0, 0.0, 0.0)))
    return sp


def smashing_strike(ctx, k):
    fr = Fr()
    if k == "wind":
        sp = body(ctx, fr, lean=-12, drop=2); sp.update(plant("l", -4, 8, yaw=-6)); sp.update(plant("r", 4, -6, yaw=6, pitch=15))
        sp.update(hand(fr, "r", 4, 6, 34, fr.D("r", 0.8, 0.0, 0.3), axis=U, palm=C.D("r", -1.0, 0.0, 0.0)))
        sp.update(hand(fr, "l", -4, 6, 34, fr.D("l", 0.8, 0.0, 0.3), axis=U, palm=C.D("l", -1.0, 0.0, 0.0)))
    else:
        low = 1.0 if k == "release" else 1.08
        sp = body(ctx, fr, lean=34, drop=26 * low); sp.update(plant("l", -8, 14, yaw=-4)); sp.update(plant("r", 8, -8, yaw=4))
        sp.update(hand(fr, "r", 3, 46, -62 * low, fr.D("r", 1.0, 0.0, 0.2), axis=C.D("r", 0.0, 0.3, -1.0), palm=C.D("r", -1.0, 0.0, 0.0)))
        sp.update(hand(fr, "l", -3, 46, -62 * low, fr.D("l", 1.0, 0.0, 0.2), axis=C.D("l", 0.0, 0.3, -1.0), palm=C.D("l", -1.0, 0.0, 0.0)))
    return sp


def roundhouse_kick(ctx, k):
    """the right knee raised out to her side with the shin folded back, her hips turning over on the left foot, the shin
    whipped round through the front at waist height (the instep first), carried on across, then down"""
    yaw = {"chamber": 30, "hit": 70, "follow": 88}[k]; fr = Fr(yaw); w = Fr()       # (the leg's ways in her starting frame)
    sp = body(ctx, fr, lean=-3, side=20 if k != "chamber" else 10, drop=8)
    sp.update(under("l", 0.0, yaw=yaw - 25, pitch=15))
    if k == "chamber":
        sp.update(kick("r", w.D("r", 0.55, 0.80, 0.15), w.D("r", 0.65, -0.60, 0.0), w.D("r", 0.6, -0.6, -0.3), w.v(U)))
    elif k == "hit":
        sp.update(kick("r", w.D("r", 0.10, 1.0, 0.22), w.D("r", -0.20, 1.0, 0.20), w.D("r", -0.25, 1.0, 0.1), w.D("l", 0.6, 0.0, 0.8)))
    else:
        sp.update(kick("r", w.D("r", -0.35, 0.9, 0.0), w.D("r", -0.7, 0.6, -0.25), w.D("r", -0.7, 0.5, -0.4), w.D("l", 0.6, 0.0, 0.8)))
    sp.update(guard_l(fr)); sp.update(hand(fr, "r", 22, -6, -18, fr.D("r", 0.6, -0.2, -1.0), axis=C.D("r", 0.3, -0.5, -0.8), palm=C.D("r", -1.0, 0.0, 0.0)))
    return sp


def chain_punch(ctx, k):
    """k: 'r' or 'l' (the fist that strikes), 'R' the last and strongest"""
    fr = Fr(); s = k.lower(); o = "l" if s == "r" else "r"; strong = k == "R"
    sp = body(ctx, fr, twist=-16 if s == "r" else 16, lean=12 if strong else 7, drop=12 if strong else 10)
    sp.update(plant("l", -2, 10, yaw=-4)); sp.update(plant("r", 2, -6, yaw=4))
    sx = 1.0 if s == "r" else -1.0
    vert = lambda side: C.D(side, -1.0, 0.0, 0.0)          # (a vertical fist: the palm toward the middle)
    sp.update(hand(fr, s, -2 * sx, 50, -4, fr.D(s, 0.3, 0.0, -1.0), axis=F, palm=vert(s)))
    sp.update(hand(fr, o, 2 * sx, 12, -14, fr.D(o, 0.6, 0.0, -1.0), axis=C.D(o, 0.0, 0.7, 0.7), palm=vert(o)))
    return sp


def rear_kick(ctx, k):
    """a half turn away (to her right, on the left foot), the right knee tucked under her, the leg driven straight back at
    the monster, heel first, the body leaning away over the standing leg; turned back"""
    yaw = {"turn": -90, "tuck": -180, "hit": -180, "back": -90}[k]; fr = Fr(yaw)
    sp = body(ctx, fr, lean=34 if k == "hit" else 14, drop=10, look=0.9)
    sp.update(under("l", 0.0, yaw=yaw, pitch=10))
    if k == "hit":
        sp.update(kick("r", fr.D("r", 0.08, -1.0, 0.18), fr.D("r", 0.08, -1.0, 0.20), fr.D("r", 0.0, -0.2, -1.0), fr.v(-U)))
    else:
        sp.update(kick("r", fr.D("r", 0.10, 0.75, -0.35), fr.D("r", 0.05, -0.35, -0.95), fr.D("r", 0.0, 0.5, -0.85), fr.v(F)))
    sp.update(guard_l(fr)); sp.update(guard_r(fr))
    return sp


def piercing_palm(ctx, k):
    fr = Fr()
    if k == "wind":
        sp = body(ctx, fr, twist=38, lean=2, drop=12); sp.update(plant("l", -2, 18, yaw=-10)); sp.update(plant("r", 4, -18, yaw=-45))
        sp.update(hand(fr, "l", -8, 40, -6, fr.D("l", 0.4, 0.0, -1.0), axis=F, palm=C.D("l", -1.0, 0.0, 0.0), closed=False))
        sp.update(hand(fr, "r", 14, -4, -40, fr.D("r", 0.5, -0.6, -0.4), axis=F, palm=U, closed=False))
    else:
        ext = 1.0 if k == "release" else 0.9
        sp = body(ctx, fr, twist=-36, lean=14, drop=20, fwd=14, hips=0.4); sp.update(plant("l", -4, 38, yaw=-4)); sp.update(plant("r", 4, -22, yaw=-14, pitch=28))
        sp.update(hand(fr, "l", -8, 14, -14, fr.D("l", 0.6, 0.0, -1.0), axis=U, palm=C.D("l", -1.0, 0.0, 0.0), closed=False))
        sp.update(hand(fr, "r", 0, 66 * ext, -4, fr.D("r", 0.4, 0.0, -1.0), axis=F, palm=C.D("r", -1.0, 0.0, 0.0), closed=False))
    return sp


def axe_kick(ctx, k):
    """the straight right leg swung up in front of her past her head, then chopped straight down, heel first, landing a
    stride forward"""
    fr = Fr()
    if k == "land":
        sp = body(ctx, fr, lean=8, drop=10); sp.update(plant("l", -2, 4, yaw=-6)); sp.update(plant("r", 2, 36, yaw=-10))
        sp.update(guard_l(fr)); sp.update(guard_r(fr)); return sp
    lean = {"rise": -6, "top": -14, "hit": 14}[k]
    sp = body(ctx, fr, lean=lean, drop=6 if k != "hit" else 12)
    sp.update(plant("l", -2, 6, yaw=-6, pitch=18 if k == "top" else 0))
    if k == "rise":
        sp.update(kick("r", fr.D("r", 0.15, 0.80, 0.55), fr.D("r", 0.15, 0.75, 0.62), fr.D("r", 0.1, 0.1, 1.0), fr.v(U)))
    elif k == "top":
        sp.update(kick("r", fr.D("r", 0.22, 0.30, 0.95), fr.D("r", 0.22, 0.25, 0.97), fr.D("r", 0.1, -0.6, 0.8), fr.v(-F)))
    else:
        sp.update(kick("r", fr.D("r", 0.05, 0.95, -0.25), fr.D("r", 0.02, 0.55, -0.85), fr.D("r", 0.0, 0.7, 0.7), fr.v(U)))
    if k == "top":
        sp.update(hand(fr, "l", -32, 10, 0, fr.D("l", 0.3, 0.0, -1.0), axis=C.D("l", 0.8, 0.4, 0.0), palm=-U))
        sp.update(hand(fr, "r", 30, 6, -2, fr.D("r", 0.3, 0.0, -1.0), axis=C.D("r", 0.8, 0.4, 0.0), palm=-U))
    else:
        sp.update(guard_l(fr)); sp.update(guard_r(fr))
    return sp


def meteor_fist(ctx, k):
    fr = Fr()
    if k == "crouch":
        sp = body(ctx, fr, lean=20, drop=30); sp.update(plant("l", -4, 8, yaw=-6)); sp.update(plant("r", 4, -6, yaw=6))
        sp.update(hand(fr, "r", 18, -22, -32, fr.D("r", 0.8, 0.0, -0.4), axis=-U, palm=F)); sp.update(hand(fr, "l", -18, -22, -32, fr.D("l", 0.8, 0.0, -0.4), axis=-U, palm=F))
    elif k == "rise":
        sp = body(ctx, fr, lean=-6, drop=-40); sp.update(plant("l", -4, 0, 30, yaw=-6, pitch=40)); sp.update(plant("r", 4, -10, 34, yaw=6, pitch=40))
        sp.update(hand(fr, "r", 6, 2, 38, fr.D("r", 0.8, 0.0, 0.2), axis=U, palm=C.D("r", -1.0, 0.0, 0.0)))
        sp.update(hand(fr, "l", -40, 6, 0, fr.D("l", 0.0, -0.2, -1.0), axis=C.D("l", 1.0, 0.0, 0.0), palm=-U, closed=False))
    elif k == "apex":
        sp = body(ctx, fr, lean=4, drop=-48); sp.update(plant("l", -4, 8, 38, yaw=-6, pitch=45)); sp.update(plant("r", 4, -16, 42, yaw=6, pitch=45))
        sp.update(hand(fr, "r", 8, -12, 36, fr.D("r", 0.8, 0.0, 0.2), axis=C.D("r", 0.0, -0.5, 0.85), palm=C.D("r", -1.0, 0.0, 0.0)))
        sp.update(hand(fr, "l", -40, 10, -4, fr.D("l", 0.0, -0.2, -1.0), axis=C.D("l", 1.0, 0.0, 0.0), palm=-U, closed=False))
    else:                                                  # the impact, and held
        sp = body(ctx, fr, lean=38, drop=54); sp.update(plant("l", -6, 22, yaw=-6)); sp.update(plant("r", 6, -26, yaw=10, pitch=40))
        sp.update(hand(fr, "r", 2, 48, -88, fr.D("r", 1.0, 0.0, 0.0), axis=C.D("r", 0.0, 0.3, -1.0), palm=-F))
        sp.update(hand(fr, "l", -36, -10, -24, fr.D("l", 0.4, -0.3, -1.0), axis=C.D("l", 0.6, -0.6, -0.4), palm=-U, closed=False))
    return sp


def spinning_kick(ctx, k):
    """a clockwise turn on the left foot (seen from above: she turns to her right), the right leg out to her right side: at
    three quarters of the turn it sweeps through where she faced at the start (turned the other way, it pointed behind
    her there: the first preview)"""
    yaw = {"chamber": -40, "turn1": -130, "turn2": -210, "hit": -270, "after": -330, "land": -360}[k]; fr = Fr(yaw)
    sp = body(ctx, fr, twist=0, lean=-4 if k in ("turn2", "hit") else 4, side=22 if k in ("turn2", "hit") else 6, drop=8)
    sp.update(under("l", 0.0, yaw=yaw - 10, pitch=15))
    if k == "chamber":
        sp.update(kick("r", fr.D("r", 0.2, 0.9, 0.25), fr.D("r", 0.1, 0.1, -1.0), fr.D("r", 0.0, 0.6, -0.8), fr.v(F)))
    elif k == "turn1":
        sp.update(kick("r", fr.D("r", 0.7, 0.5, 0.1), fr.D("r", 0.4, -0.4, -0.8), fr.D("r", 0.2, -0.3, -0.9), fr.v(F)))
    elif k in ("turn2", "hit"):
        sp.update(kick("r", fr.D("r", 1.0, 0.0, 0.12 if k == "hit" else 0.05), fr.D("r", 1.0, 0.0, 0.15 if k == "hit" else -0.1), fr.D("r", 1.0, 0.0, 0.0), fr.v(F)))
    elif k == "after":
        sp.update(kick("r", fr.D("r", 0.6, 0.2, -0.6), fr.D("r", 0.3, 0.0, -1.0), fr.D("r", 0.2, 0.6, -0.7), fr.v(F)))
    else:
        sp.update(plant("r", 4, -16, yaw=-38))
    arms_out = k in ("turn1", "turn2", "hit")
    if arms_out:
        sp.update(hand(fr, "l", -30, 14, 2, fr.D("l", 0.3, 0.0, -1.0), axis=C.D("l", 0.7, 0.5, 0.0), palm=-U))
        sp.update(hand(fr, "r", 10, 18, -6, fr.D("r", 0.5, 0.0, -1.0), axis=U, palm=C.D("r", -1.0, 0.0, 0.0)))
    else:
        sp.update(guard_l(fr)); sp.update(guard_r(fr))
    return sp


def dash(ctx, k):
    fr = Fr()
    sp = body(ctx, fr, twist=12, lean=26, drop=18)
    sp.update(plant("l", -4, 30, yaw=-6)); sp.update(plant("r", 4, -40, yaw=-10, pitch=40))
    sp.update(hand(fr, "l", -8, 32, -4, fr.D("l", 0.5, 0.0, -1.0), axis=C.D("l", -0.2, 0.8, 0.5), palm=C.D("l", -1.0, 0.0, 0.0)))
    sp.update(hand(fr, "r", 6, 24, -8, fr.D("r", 0.5, 0.0, -1.0), axis=C.D("r", -0.2, 0.8, 0.5), palm=C.D("r", -1.0, 0.0, 0.0)))
    return sp


# the chi attacks: (clip, the key poses as (seconds, maker, its key; None the stance), the blow's time, the striking bone)
CHI = [
    ("Chi_StraightPunch", [(0.0, None, 0), (0.10, straight_punch, "chamber"), (0.20, straight_punch, "release"), (0.34, straight_punch, "follow"), (0.62, None, 0)], 0.20, "hand_r"),
    ("Chi_SideKick", [(0.0, None, 0), (0.16, side_kick, "chamber"), (0.30, side_kick, "hit"), (0.46, side_kick, "retract"), (0.80, None, 0)], 0.30, "foot_r"),
    ("Chi_SmashingStrike", [(0.0, None, 0), (0.34, smashing_strike, "wind"), (0.50, smashing_strike, "release"), (0.68, smashing_strike, "follow"), (1.05, None, 0)], 0.50, "hand_r"),
    ("Chi_RoundhouseKick", [(0.0, None, 0), (0.16, roundhouse_kick, "chamber"), (0.30, roundhouse_kick, "hit"), (0.44, roundhouse_kick, "follow"), (0.80, None, 0)], 0.30, "foot_r"),
    ("Chi_ChainPunch", [(0.0, None, 0), (0.12, chain_punch, "r"), (0.22, chain_punch, "l"), (0.32, chain_punch, "r"), (0.42, chain_punch, "l"),
                        (0.52, chain_punch, "r"), (0.62, chain_punch, "l"), (0.76, chain_punch, "R"), (0.92, chain_punch, "R"), (1.20, None, 0)], 0.76, "hand_r"),
    ("Chi_RearKick", [(0.0, None, 0), (0.16, rear_kick, "turn"), (0.30, rear_kick, "tuck"), (0.44, rear_kick, "hit"), (0.58, rear_kick, "tuck"),
                      (0.72, rear_kick, "back"), (0.95, None, 0)], 0.44, "foot_r"),
    ("Chi_PiercingPalm", [(0.0, None, 0), (0.28, piercing_palm, "wind"), (0.42, piercing_palm, "release"), (0.58, piercing_palm, "follow"), (0.90, None, 0)], 0.42, "hand_r"),
    ("Chi_AxeKick", [(0.0, None, 0), (0.18, axe_kick, "rise"), (0.32, axe_kick, "top"), (0.44, axe_kick, "hit"), (0.58, axe_kick, "land"), (0.92, None, 0)], 0.44, "foot_r"),
    ("Chi_MeteorFist", [(0.0, None, 0), (0.25, meteor_fist, "crouch"), (0.45, meteor_fist, "rise"), (0.60, meteor_fist, "apex"), (0.78, meteor_fist, "impact"),
                        (1.00, meteor_fist, "impact"), (1.45, None, 0)], 0.78, "hand_r"),
    ("Chi_SpinningKick", [(0.0, None, 0), (0.14, spinning_kick, "chamber"), (0.28, spinning_kick, "turn1"), (0.42, spinning_kick, "turn2"), (0.55, spinning_kick, "hit"),
                          (0.70, spinning_kick, "after"), (0.86, spinning_kick, "land"), (1.15, None, 0)], 0.55, "foot_r"),
]
DASH = [(0.0, None, 0), (0.10, dash, 0), (0.36, dash, 0), (0.50, None, 0)]


def make_clips(arm_obj, scene, clips):
    import warrior3_clips as W3
    out = {}
    # her own: the dance and the stairs are not used; the rest recentred where the pelvis is held off its rest place
    for nm in [n for n in clips if n.lower().startswith(("dance", "run_upstairs"))]: del clips[nm]
    for nm, frames in list(clips.items()):
        fixed, mean = W3.recentre(arm_obj, frames)
        if fixed is not None:
            out[nm] = fixed; print("MA %s: the pelvis held (%.2f, %.2f) of her height off its rest place on average: moved back" % (nm, mean.x / W3.W2_height(arm_obj), mean.y / W3.W2_height(arm_obj)))
    # rogue_clips': the stabs (a knife in each hand) and the roll; its Idle and Shoot are not hers
    made = R.make_clips(arm_obj, scene, clips)
    for nm in ("Stab1", "Stab2", "Stab3", "RollF", "RollB"): out[nm] = made[nm]
    ctx = C.context(arm_obj); DC.add_thumb_op(ctx, arm_obj); ctx["cm"] = R.model_height(scene) / 170.0; R.arm_context(ctx, arm_obj); leg_context(ctx, arm_obj)
    P = lambda spec: apply(arm_obj, spec, ctx)
    i0, i1 = P(stance(ctx)), P(stance(ctx, k=1.0))
    out["Idle"] = C.sample([(0.0, i0), (1.2, i1), (2.4, i0)])
    times = {}
    for name, keys, hit, bone in CHI + [("Dash", DASH, 0.0, "pelvis")]:
        poses = [(t, i0 if fn is None else P(fn(ctx, k))) for t, fn, k in keys]
        out[name] = C.sample(poses); times[name] = {"length": keys[-1][0], "hit": hit, "bone": bone}
    for pb in arm_obj.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    worst = max(ctx["wrists"], key=lambda sw: R.over(*sw[1]))
    print("MA wrists: %d hands solved, the furthest past a limit %.1f deg (%s)" % (len(ctx["wrists"]), R.over(*worst[1]), worst[0]))
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) > 1 and os.path.isdir(argv[1]):
        json.dump(times, open(os.path.join(argv[1], "ma_times.json"), "w"), indent=1)
    return out


# ---------------------------------------------------------------- preview
if __name__ == "__main__" and os.path.basename(sys.argv[sys.argv.index("-P") + 1] if "-P" in sys.argv else "") == "martialartist_clips.py":
    argv = sys.argv[sys.argv.index("--") + 1:]
    src, prefix = argv[0], argv[1]; only = argv[2].split(",") if len(argv) > 2 else None
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    sc = bpy.context.scene
    for o in [o for o in sc.objects if o.type == 'MESH' and not o.vertex_groups]: bpy.data.objects.remove(o, do_unlink=True)
    arm_obj = next(o for o in sc.objects if o.type == 'ARMATURE')
    if arm_obj.animation_data: arm_obj.animation_data.action = None
    for pb in arm_obj.pose.bones: pb.rotation_mode = 'QUATERNION'; pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    ctx = C.context(arm_obj); DC.add_thumb_op(ctx, arm_obj); ctx["cm"] = R.model_height(sc) / 170.0; R.arm_context(ctx, arm_obj); leg_context(ctx, arm_obj)
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'TEXTURE'; sc.display.shading.light = 'STUDIO'
    sc.render.resolution_x = 260; sc.render.resolution_y = 330
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.6
    # (a floor line: a thin plane at the feet)
    bpy.ops.mesh.primitive_plane_add(size=1.6, location=(0, 0, ctx["floor"] - 0.004)); fl = bpy.context.active_object
    m = bpy.data.materials.new("floor"); m.diffuse_color = (0.25, 0.35, 0.25, 1); fl.data.materials.append(m)
    i0 = apply(arm_obj, stance(ctx), ctx)
    for name, keys, hit, bone in CHI + [("Dash", DASH, 0.0, "pelvis")]:
        if only and name not in only: continue
        for ki, (t, fn, k) in enumerate(keys):
            if fn is None and ki > 0: continue
            if fn is None: apply(arm_obj, stance(ctx), ctx)
            else: apply(arm_obj, fn(ctx, k), ctx)
            for view, ang in (("front", 0), ("side", 90), ("q", 35)):
                a = math.radians(ang); d = Vector((math.sin(a), -math.cos(a), 0.15))
                cam.location = Vector((0, 0, 0.5)) + d * 4.0; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
                sc.render.filepath = f"{prefix}_{name}_{ki}_{view}.png"; bpy.ops.render.render(write_still=True)
    worst = max(ctx["wrists"], key=lambda sw: R.over(*sw[1])) if ctx.get("wrists") else None
    print("PREVIEW DONE", worst and round(R.over(*worst[1]), 1))
