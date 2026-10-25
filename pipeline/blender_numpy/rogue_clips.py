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
right is -X), but the arms are solved (solve_arm): the elbow is a hinge (the upper arm turns about its own axis until the
forearm bends the way the elbow does, no more than ARM_ROLL: her cape hangs from the upper arms; a held arm's forearm
may swing about the upper arm instead), the wrist stays within what a wrist can do (FLEX, DEV, TWIST), half of the hand's
turn goes to the forearm's twist bone, and the hand points the blade as near its aim as that allows (the crossbow:
exactly, the elbow put where the wrist can hold it). The clips aimed the blade with the thumb before, whatever it cost
the wrist: the hands came out folded back or twisted half round. The grips of pipeline/unreal/822 put a dagger's blade
and the crossbow's front the way the thumb points in her reference pose, leaning toward the fingers by GRIP_TILT (a
handle lies across a fist at a slant; written to times.json for 822). Every solve prints how far past a limit the worst
wrist went ("ROGUE wrists").
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


# what a wrist and an elbow can do (degrees). The wrist: flexion toward the palm (+) or the back of the hand, deviation
# toward the thumb (+) or the little finger, and the hand's turn about the forearm from her reference pose (palms down in
# the T-pose: the forearm half way between its turns), half of which the forearm's twist bone takes as the radius turns
# over the ulna. The elbow is a hinge: it bends the forearm only the way it bends forward from the T-pose.
FLEX, DEV, TWIST = (-50.0, 60.0), (-30.0, 15.0), (-80.0, 80.0)
ARM_ROLL = 40.0       # the upper arm's turn about itself (from the shortest swing from the T-pose), at most: her cape hangs from her
                      # upper arms, and a turn of 120 degrees and more (the elbow made a hinge with the arm's ways as written) lifted it off her back


def roll_cost(roll):
    return 0.0005 * roll * roll + 0.5 * max(0.0, abs(roll) - ARM_ROLL) ** 2
# a dagger's handle and the crossbow's stock lie across the palm at a slant, as in a fist: the blade (the crossbow's
# front) leans from the thumb's way toward the fingers' by these (822 grips them so); held square to the hand, the blade
# could only point along the forearm with the wrist bent 90 degrees, and the crossbow only be aimed with it folded back
GRIP_TILT = {"dagger": 25.0, "crossbow": 45.0}


def hold(side, up, low, hand, thumb):
    """an arm with a closed hand on a dagger: upper arm and forearm ways, and as near as the wrist allows, the blade
    pointing `thumb`, the fingers' way `hand` (the hand and the forearm's twist are solved: solve_arm)"""
    sp = {f"arm_{side}": ("hold", up, low, {"blade": thumb, "axis": hand})}
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


def reach(side, at, pole, want, exact=None):
    """the arm bent so the hand's root is at `at` (cm from the base of her neck: (her right, forward, up)), the elbow on the
    circle that allows, rather toward `pole`; the hand turned as `exact` says ({"front", "up"}: the crossbow's front and rail)
    or as near `want` as the wrist allows"""
    return {f"arm_{side}": ("reach", at, pole, want, exact)}


STANCE, XB_HAND, XB_SUPPORT = 55.0, (12.0, 26.0, -4.0), (8.0, -7.0, 2.0)   # (shoulders turned; the right hand's root: cm from her neck (right, forward, up); the left's: cm along the crossbow (forward, up, left))


def shoot(ctx, k):
    """the crossbow at her right shoulder, level and aimed: the right hand round the stock below her chin (the stock
    slanting through the fist toward the thumb: its butt then lies just in front of her shoulder), the elbow out and
    down; the left hand under the forestock (a place on the crossbow, wherever the right hand put it), palm up"""
    up, back = {"aim": (0.0, 0.0), "kick": (2.5, 2.5), "hold": (0.8, 1.0)}[k]
    sp = C.body(ctx, twist=STANCE, lean=4 - 0.8 * up, knees=9, look=0.95)
    front = D("r", 0.0, 1.0, 0.03 + 0.03 * up)
    xh = ctx.get("xb_hand", XB_HAND)                          # (weapon5_clips' heroes: their own, for their longer arms)
    sp.update(reach("r", (xh[0], xh[1] - back, xh[2] + up), D("r", 0.6, 0.0, -0.8), None, {"front": front, "up": U}))
    sp.update(DC.fist("r"))
    sp.update(reach("l", ("crossbow",) + XB_SUPPORT, D("l", 0.3, 0.1, -1.0), {"axis": D("l", -0.55, 0.8, 0.15), "palm": U}))
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


Y = Vector((0.0, 1.0, 0.0))


def arm_context(ctx, arm_obj):
    """each arm's reference pose: the elbow's and the wrist's rest relations, the elbow's hinge, the wrist's axes, and the
    weapons' ways in the hand's frame as 822 grips them (a dagger's blade, the crossbow's front: the thumb's way leaning
    GRIP_TILT toward the forearm's; the crossbow's rail square to its front, away from the fingers), and the palm point
    the grips are made at"""
    B = arm_obj.data.bones; q = lambda n: B[n].matrix_local.to_quaternion(); ctx["arms"] = {}
    for s in "rl":
        u0, f0, h0 = q(f"upperarm_{s}"), q(f"lowerarm_{s}"), q(f"hand_{s}")
        rel_e, rel_h = u0.inverted() @ f0, f0.inverted() @ h0
        fore = (B[f"hand_{s}"].head_local - B[f"lowerarm_{s}"].head_local).normalized()
        th = B[f"thumb_01_{s}"].head_local - B[f"hand_{s}"].head_local
        along = (B[f"middle_01_{s}"].head_local - B[f"hand_{s}"].head_local).normalized()
        th = th - along * th.dot(along); th = (th - fore * th.dot(fore)).normalized()
        g = math.radians(GRIP_TILT["dagger"]); blade = (th * math.cos(g) + fore * math.sin(g)).normalized()
        g = math.radians(GRIP_TILT["crossbow"]); front = (th * math.cos(g) + fore * math.sin(g)).normalized(); rail = (th * math.sin(g) - fore * math.cos(g)).normalized()
        # the wrist's axes, square to each other: the hand's own, across the knuckles toward the thumb's side, the palm's
        # normal (the thumb bone itself stands off the palm, half way to its normal)
        ax0 = rel_h @ Y
        t0 = f0.inverted() @ (B[f"index_01_{s}"].head_local - B[f"pinky_01_{s}"].head_local); t0 = (t0 - ax0 * t0.dot(ax0)).normalized()
        p0 = ax0.cross(t0).normalized()
        if p0.dot(rel_h @ ctx["palm"][f"hand_{s}"]) < 0: p0 = -p0
        A = {"rel_e": rel_e, "rel_h": rel_h, "hinge": u0.inverted() @ fore.cross(F).normalized(), "ax0": ax0, "p0": p0, "t0": t0,
             "a": (B[f"lowerarm_{s}"].head_local - B[f"upperarm_{s}"].head_local).length, "b": (B[f"hand_{s}"].head_local - B[f"lowerarm_{s}"].head_local).length,
             "local": {"blade": h0.inverted() @ blade, "axis": Y.copy(), "palm": ctx["palm"][f"hand_{s}"], "front": h0.inverted() @ front, "up": h0.inverted() @ rail},
             "palm_pt": h0.inverted() @ ((fore * 6.5 + Vector((0.0, 0.0, -2.5))) * ctx["cm"])}
        A["grid"] = [(fl, dv, tw, wrist_q(A, fl, dv, tw) @ rel_h) for fl in range(-40, 61, 10) for dv in (-30, -22.5, -15, -7.5, 0, 7.5, 15)
                     for tw in range(-75, 76, 15)]
        ctx["arms"][s] = A


def wrist_q(A, fl, dv, tw):
    """the wrist's turn in the forearm's frame: the hand turned tw about its axis, then bent fl toward the palm, dv toward the thumb"""
    ax0 = A["ax0"]
    return (Quaternion(ax0.cross(A["t0"]).normalized(), math.radians(dv)) @ Quaternion(ax0.cross(A["p0"]).normalized(), math.radians(fl))
            @ Quaternion(ax0, math.radians(tw)))


def wrist_of(A, qf, qh):
    """(flexion, deviation, twist) of a hand turned qh on a forearm turned qf"""
    W = qf.inverted() @ qh @ A["rel_h"].inverted(); ax0 = A["ax0"]; ax = W @ ax0
    fl = math.degrees(math.atan2(ax.dot(A["p0"]), ax.dot(ax0))); dv = math.degrees(math.atan2(ax.dot(A["t0"]), ax.dot(ax0)))
    tq = ax0.rotation_difference(ax).inverted() @ W
    tw = (math.degrees(2.0 * math.atan2(Vector(tq[1:]).dot(ax0), tq[0])) + 180.0) % 360.0 - 180.0
    return fl, dv, tw


def over(fl, dv, tw):
    """degrees past the wrist's limits (0 inside them)"""
    ex = lambda x, r: max(0.0, r[0] - x, x - r[1])
    return max(ex(fl, FLEX), ex(dv, DEV), ex(tw, TWIST))


def wrist_cost(fl, dv, tw):
    ex = lambda x, r: max(0.0, r[0] - x, x - r[1])
    return 0.5 * (ex(fl, FLEX) ** 2 + ex(dv, DEV) ** 2 + ex(tw, TWIST) ** 2) + 0.0004 * (fl * fl + dv * dv + tw * tw)


# (cm from the bone line to her skin: the arm's own thickness, so the arm may lie against her ribs but not go into her;
# 5 / 4.5 cm and a weight of 2 forbade the touch of a resting upper arm too, and every frame gave its wrists up for it)
ARM_CLEAR = {"upper": 4.0, "elbow": 3.5, "fore": 3.5, "wrist": 3.0}


def comfort_cost(ctx, fl, dv, tw):
    """(ctx["wrist_comfort"]: {"flex", "dev", "twist": ranges, "w": weight}) a wrist bent past the range it holds a weapon
    in without strain, squared: the limits alone let a two-handed grip bend 50 to 60 degrees (inside them, nearly free);
    held as in a katana's guards, the wrists stay near straight and the forearms' turn and the elbows set the blade"""
    wc = ctx.get("wrist_comfort")
    if not wc: return 0.0
    ex = lambda x, r: max(0.0, r[0] - x, x - r[1])
    return wc["w"] * (ex(fl, wc["flex"]) ** 2 + ex(dv, wc["dev"]) ** 2 + ex(tw, wc["twist"]) ** 2)


def elbow_off(Ev, dn, out, cm, er):
    """(Ev: shoulder to elbow; dn: the way shoulder to hand) how far the elbow points in toward her middle and up off
    the line from the shoulder to the hand, past what er allows (cm; <= 0 within)"""
    perp = Ev - dn * Ev.dot(dn)
    return perp.dot(-out) / cm - er["in"], perp.dot(U) / cm - er["up"]


def torso_now(arm_obj, ctx):
    """(ctx["torso_pts"]: per bone, points of her torso's skin and their outward ways in the bone's rest space) those
    points and ways as the pose carries them now, two arrays (armature space)"""
    import numpy as np
    P = arm_obj.pose.bones; B = arm_obj.data.bones; qs, ns = [], []
    for b, pts, nrm in ctx["torso_pts"]:
        M = P[b].matrix; R3 = np.array(M.to_3x3()); t = np.array(M.translation)     # (the points are in the bone's own rest space)
        qs.append(pts @ R3.T + t); ns.append(nrm @ R3.T)
    return np.vstack(qs), np.vstack(ns)


def body_short(TQ, TN, p, margin, cm):
    """how far the point p falls short of `margin` cm outside her torso (the nearest skin point's outward way)"""
    import numpy as np
    d2 = ((TQ - np.array(p)) ** 2).sum(1); i = int(d2.argmin())
    d = float(np.dot(np.array(p) - TQ[i], TN[i])) / cm
    return margin - d


def exact_hand(A, front, up):
    """the hand's turn that puts the weapon's front and rail (its own frame: A["local"]) on front and up"""
    def frame(x, z):
        x = x.normalized(); y = z.cross(x).normalized(); z = x.cross(y)
        return Matrix((x, y, z)).transposed().to_quaternion()
    return frame(front, up) @ frame(A["local"]["front"], A["local"]["up"]).inverted()


def solve_arm(arm_obj, ctx, side, op):
    """('hold', up, low, want) or ('reach', at, pole, want, exact): the arm with the elbow a hinge (the upper arm turned about
    its own axis until the forearm bends the way the elbow bends) and the wrist within its limits, the hand as near `want`
    as they allow ({"blade" | "axis" | "palm": a way}) or exactly as `exact` says; half the hand's turn goes to the twist bone"""
    A = ctx["arms"][side]; P = arm_obj.pose.bones
    ua, la, ha, tb = P[f"upperarm_{side}"], P[f"lowerarm_{side}"], P[f"hand_{side}"], P[f"lowerarm_twist_01_{side}"]
    qu0 = ua.matrix.to_quaternion(); S = ua.head.copy()
    cands = []                                                    # (upper arm way, forearm way, cost of the elbow's place)
    if op[0] == "hold":
        # (the forearm may swing about the upper arm's axis, the bend kept, to keep the upper arm's turn within ARM_ROLL)
        Uw = op[1].normalized(); want, exact = op[3], None
        for al in range(-90, 91, 15): cands.append((Uw, Quaternion(Uw, math.radians(al)) @ op[2].normalized(), 0.002 * al * al))
    else:
        _, at, pole, want, exact = op
        if at[0] in ("crossbow", "palm_on"):                      # (cm along the crossbow in the right hand: forward, up, to her left)
            R_ = ctx["arms"]["r"]; qr = P["hand_r"].matrix.to_quaternion(); fw, uw = qr @ R_["local"]["front"], qr @ R_["local"]["up"]
            goal = P["hand_r"].head + qr @ R_["palm_pt"] + (fw * at[1] + uw * at[2] + uw.cross(fw) * at[3]) * ctx["cm"]
            # ('palm_on': that place is for the palm, not the wrist: a second hand on a two-handed hilt, weapon5_clips.py)
            if at[0] == "palm_on" and exact: goal = goal - exact_hand(A, exact["front"], exact["up"]) @ A["palm_pt"]
        else:
            goal = P["neck_01"].head + (C.OUT["r"] * at[0] + F * at[1] + U * at[2]) * ctx["cm"]
        a, b = A["a"], A["b"]; d = goal - S; dist = min(d.length, (a + b) * 0.999); dn = d.normalized()
        if d.length > (a + b) * 1.02: print("ROGUE the %s hand falls %.1f cm short of its place" % (side, (d.length - a - b) / ctx["cm"]))
        ang = math.acos(max(-1.0, min(1.0, (a * a + dist * dist - b * b) / (2 * a * dist))))
        e1 = dn.orthogonal().normalized(); e2 = dn.cross(e1)
        for k in range(36):
            ph = math.radians(10 * k); p = e1 * math.cos(ph) + e2 * math.sin(ph)
            Uw = dn * math.cos(ang) + p * math.sin(ang); E = S + Uw * a
            cands.append((Uw, (S + dn * dist - E).normalized(), 0.0004 * math.degrees(p.angle(pole - dn * pole.dot(dn))) ** 2))
    qx = exact_hand(A, exact["front"], exact["up"]) if exact else None
    # (a head to keep the elbow and forearm out of (weapon5_clips' head_ball, in the head's rest frame): the elbow chosen for
    # the wrist alone went behind her head for a hilt raised over it)
    hb = ctx.get("head_ball"); hc = None
    if hb is not None:
        Bh = arm_obj.data.bones["head"]; hc = P["head"].matrix @ (Bh.matrix_local.inverted() @ hb[0]); hr = hb[1] + 4.0 * ctx["cm"]
    aims = [(A["local"][k], v.normalized(), {"blade": 0.012, "axis": 0.002, "palm": 0.003}[k]) for k, v in (want or {}).items()]
    # (ctx["elbow_rules"]: the elbow kept as in a katana's guards: off the line from the shoulder to the hand it points
    # out to its own side and down, never in toward her middle nor up (er["in"], er["up"]: cm allowed); the elbow chosen
    # for the wrist alone folded up and in across her chest)
    er = ctx.get("elbow_rules") if op[0] != "hold" else None
    # (ctx["torso_pts"]: the whole arm, upper arm, elbow, forearm and wrist, kept outside her torso by ARM_CLEAR (cm, the
    # bone line to her skin): the elbow placed for the hands alone hung down and in, and the upper arms went through her
    # chest as she raised the sword (the user saw it); kept out, the elbows flare to the sides or forward)
    TQ = None
    if ctx.get("torso_pts") and op[0] != "hold": TQ, TN = torso_now(arm_obj, ctx)
    best = None
    for Uw, L, c0 in cands:
        if er:
            c0 = c0 + er["w"] * sum(max(0.0, v) ** 2 for v in elbow_off(Uw * A["a"], dn, C.OUT[side], ctx["cm"], er))
        if hc is not None or TQ is not None:
            E = S + Uw * A["a"]; Wr = E + L * A["b"]
            # (the upper arm from three quarters along: nearer the shoulder it meets her body in the armpit's fold whenever
            # the arm is raised, and counting it there dragged the Warlock's raised hilts down to her waist)
            arm_pts = [(S.lerp(E, 0.75), ARM_CLEAR["upper"]), (E, ARM_CLEAR["elbow"]),
                       (E.lerp(Wr, 0.35), ARM_CLEAR["fore"]), (E.lerp(Wr, 0.7), ARM_CLEAR["fore"]), (Wr, ARM_CLEAR["wrist"])]
        if hc is not None:
            for p_, _m in arm_pts:
                dd = ((p_ - hc).length - hr) / ctx["cm"]
                if dd < 0.0: c0 = c0 + 2.0 * dd * dd
        if TQ is not None:
            for p_, m_ in arm_pts:
                sh_ = body_short(TQ, TN, p_, m_, ctx["cm"])
                if sh_ > 0.0: c0 = c0 + ctx.get("torso_w", 1.0) * sh_ * sh_
        qmin = (qu0 @ Y).rotation_difference(Uw) @ qu0
        bend = math.degrees(Uw.angle(L)); h = qmin @ A["hinge"]; h = h - Uw * h.dot(Uw)
        bax = Uw.cross(L)
        sh = math.atan2(h.cross(bax).dot(Uw), h.dot(bax)) if bax.length > 1e-6 and h.length > 1e-6 else 0.0
        for ds in ((0,) if bend >= 25.0 else range(-90, 91, 15)):
            # the upper arm's turn about itself (from the shortest swing there): her cape is skinned to it, and a big
            # one lifted the cape off her back
            roll = (math.degrees(sh) + ds + 180.0) % 360.0 - 180.0
            qu = Quaternion(Uw, sh + math.radians(ds)) @ qmin
            # (a clip solved frame by frame (weapon5_clips' two-handed cuts): the upper arm rather as it was a frame ago;
            # chosen afresh, it jumped 140 to 225 degrees between frames and the engine's blend spun the arm through her.
            # The roll's limit then counts for little: measured from the shortest swing from the T-pose, it flips half a
            # turn when the arm reaches across her body, and kept, it forced the arm to flip with it)
            prev = ctx.get("prev_arm", {}).get(side)
            c1 = c0 + 0.02 * (ds * min(1.0, bend / 25.0)) ** 2 + roll_cost(roll) * (ctx.get("roll_scale", 1.0) if prev is not None else ctx.get("roll_scale_key", 1.0))
            if prev is not None:
                da = math.degrees(qu.rotation_difference(prev).angle); da = min(da, 360.0 - da); c1 += ctx.get("cont_w", 0.01) * da * da
            qfi = qu @ A["rel_e"]; qf = (qfi @ Y).rotation_difference(L) @ qfi
            if qx is not None:
                w = wrist_of(A, qf, qx); c = c1 + wrist_cost(*w) + comfort_cost(ctx, *w)
                if best is None or c < best[0]: best = (c, qu, qf, qx, w, c1, roll)
                continue
            for fl, dv, tw, Wr in A["grid"]:
                qh = qf @ Wr; c = c1 + wrist_cost(fl, dv, tw) + comfort_cost(ctx, fl, dv, tw)
                for v, aim, wt in aims: c += wt * math.degrees((qh @ v).angle(aim)) ** 2
                if best is None or c < best[0]: best = (c, qu, qf, qh, (fl, dv, tw), c1, roll)
    c, qu, qf, qh, w, c1, roll = best
    if qx is None:                                                # finer, about the best of the grid
        for step in (5.0, 2.5):
            fl0, dv0, tw0 = w
            for fl in (fl0 - step, fl0, fl0 + step):
                for dv in (dv0 - step, dv0, dv0 + step):
                    for tw in (tw0 - 2 * step, tw0, tw0 + 2 * step):
                        qh_ = qf @ wrist_q(A, fl, dv, tw) @ A["rel_h"]; c_ = c1 + wrist_cost(fl, dv, tw) + comfort_cost(ctx, fl, dv, tw)
                        for v, aim, wt in aims: c_ += wt * math.degrees((qh_ @ v).angle(aim)) ** 2
                        if c_ < c: c, qh, w = c_, qh_, (fl, dv, tw)
        w = wrist_of(A, qf, qh)
    for pb, q in ((ua, qu), (la, qf), (ha, qh)):
        M = pb.matrix.copy(); pb.matrix = Matrix.LocRotScale(M.translation, q, M.to_scale()); bpy.context.view_layer.update()
    M = tb.matrix.copy(); tb.matrix = Matrix.LocRotScale(M.translation, Quaternion(qf @ Y, math.radians(0.5 * w[2])) @ M.to_quaternion(), M.to_scale())
    bpy.context.view_layer.update()
    ctx.setdefault("wrists", []).append((side, w)); ctx.setdefault("rolls", []).append((side, roll))


def apply(arm_obj, spec, ctx):
    """darkcaster_clips.apply, then each arm given as 'arm_<side>' solved (solve_arm)"""
    arms = {k[-1]: v for k, v in spec.items() if k.startswith("arm_")}
    DC.apply(arm_obj, {k: v for k, v in spec.items() if not k.startswith("arm_")}, ctx)
    for side, op in arms.items(): solve_arm(arm_obj, ctx, side, op)
    return {pb.name: pb.matrix_basis.decompose() for pb in arm_obj.pose.bones}


def make_clips(arm_obj, scene, clips):
    ctx = C.context(arm_obj); DC.add_thumb_op(ctx, arm_obj); ctx["cm"] = model_height(scene) / 170.0; arm_context(ctx, arm_obj)
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
    worst = max(ctx["wrists"], key=lambda sw: over(*sw[1]))
    print("ROGUE wrists: %d hands solved, the furthest past a limit %.1f deg (%s: flexion %.0f, deviation %.0f, twist %.0f)"
          % (len(ctx["wrists"]), over(*worst[1]), worst[0], *worst[1]))
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) > 1 and os.path.isdir(argv[1]):
        json.dump({"Shoot": {"release": RELEASE, "length": SHOT["end"]}, "Roll": {"length": ROLL[-1][0], "turn": [ROLL[1][0], ROLL[-2][0]]},
                   "Stabs": {k: {"wind": v[0], "release": v[1], "follow": v[2], "end": v[3]} for k, v in TIMES.items()}, "grip_tilt": GRIP_TILT},
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
        slant = lambda k: (th * math.cos(math.radians(GRIP_TILT[k])) + fore * math.sin(math.radians(GRIP_TILT[k]))).normalized()
        z = -slant("dagger"); y = z.cross(fore).normalized(); Xd, Yd, Zd = y.cross(z), y, z    # (MakeFromZX: the handle at +Z, the blade toward -Z)
        out.append(place(arm_obj, f"dagger_{s}", dag, dag_f, f"hand_{s}", (Xd, Yd, Zd), palm - Zd * 28.5, 1.0 / S, (0.75, 0.8, 0.9, 1)))
        if s == "r":
            g = math.radians(GRIP_TILT["crossbow"])
            Xc, Yc, Zc = ue_frame(-slant("crossbow"), th * math.sin(g) - fore * math.cos(g))    # (the crossbow's front is -X, its rail up +Z)
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
