"""Clips for the Summoner (ai models/Summoner4.glb; tripo_build.py's clip_maker, tag Summoner4), on her own rig (a 61-bone
rig with the mannequin's bone names, as MartialArtist2.glb's). Her own clips kept as Tripo made them: Walk, Run and the hit
reactions (Hit_to_body_01-02, Hit_to_head, Hit_to_side, Hit_to_stomach), each recentred where it holds her pelvis off its
rest place (warrior3_clips.recentre); her Dance_01, Box_01-03, Front_kick_02, Chop, Slash and Cast_a_spell (5.4 s: too
long) are dropped. Made for her:
  Idle       a caster's calm stance: her weight on the left leg (the pelvis over it), the right knee easy, the hands open and
             relaxed by her hips, breathing; 2.4 s loop
  Stab1-3    rogue_clips.py's knife stabs (a dagger in each hand), solved on her rig (its RollF / RollB, Idle, Shoot unused)
  CastBolt   the Fire Bolt / Dark Fire cast: the right hand drawn back by her shoulder, open, then thrust forward at shoulder
             height, palm first, the left hand back by her hip; back to the idle (the bolt leaves at the thrust)
  Summon1    tier 1 (a soldier), a beckoning call: the right arm reaches forward palm up, then sweeps up and back to her
             chest, the fingers curling in; twice, the second the call (two beats)
  Summon2    tier 2 (gunners), a two-handed push: both palms drawn to her chest, elbows out, crouched, then thrust forward
             together at chest height with a step forward on the left foot (a coil and a burst)
  Summon3    tier 3 (an orc), a ground strike: the right hand raised high, then she drops onto her right knee and slams the
             right palm down at the floor in front of her, the left arm out for balance; held, then she rises
  Summon4    tier 4 (alien warriors), a rising invocation: both arms low at her sides, swept up high overhead (on her toes,
             head back, chest open), held, then both hands brought down forward to point at the ground ahead
  Summon5    tier 5 (spiders), a spiral: a full clockwise turn on the left foot, both arms spread wide, ending facing front
             with both hands thrust forward and down, the fingers spread
Poses are written as in martialartist_clips.py (its body, plant, under, kick, Fr and leg solver; rogue_clips.solve_arm for
the arms: hand places in cm from the base of her neck, her right, forward, up). Her arms are a Tripo hero's and shorter
than the Martial Artist's (31 cm shoulder to wrist at 170 cm): places beyond her reach stretch the arm toward them, which
reads as the reach. Open hands curl a little; a spread (degrees) fans the fingers apart about the palm's normal.
Writes <out_dir>/s4_times.json: each made cast's length, the time the spell leaves her (`hit`: the bolt, or the creature
appearing in front of her) and the bone it leaves from; and rogue_clips' times.json (the stabs, the knives' grip tilt).
Preview: blender -b -P summoner4_clips.py -- model.glb out_prefix [clip,clip...]   (each key pose front / side /
three-quarter / back, a contact sheet per clip; Walk and Run: frames of the recentred clips)"""
import json, math, os, sys
import bpy
from mathutils import Matrix, Vector, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import caster_clips as C
import darkcaster_clips as DC
import rogue_clips as R
import martialartist_clips as MA
FPS = C.FPS
F, U, LEAN = C.F, C.U, C.LEAN
RIGHT = C.OUT["r"]
Fr, plant, under, kick = MA.Fr, MA.plant, MA.under, MA.kick
DROP = ("dance", "box_", "front_kick", "chop", "slash", "cast_a_spell", "run_upstairs")


# ---------------------------------------------------------------- pose parts
def body(ctx, fr, twist=0.0, lean=0.0, side=0.0, drop=0.0, fwd=0.0, look=0.75, hips=0.0, shift=0.0, head=0.0, pitch=0.0):
    """martialartist_clips.body, and: shift: the pelvis moved toward her left (cm, her unturned frame: over the left foot);
    head: the head bowed forward (degrees; negative: tilted back); pitch: the pelvis itself tipped forward (degrees)"""
    sp = MA.body(ctx, fr, twist=twist, lean=lean, side=side, drop=drop, fwd=fwd, look=look, hips=hips)
    if shift: sp.setdefault("pelvis", []).append(("move", -RIGHT * shift * ctx["cm"]))
    if pitch: sp.setdefault("pelvis", []).append(("rot", fr.v(LEAN), pitch))
    if head: sp["head"] = [("rot", fr.v(LEAN), head)]
    return sp


def open_hand(side, curl=4.0, spread=0.0):
    """the fingers a little curled (curl: degrees at the middle joint), fanned apart by `spread` degrees (index and little
    finger the most; applied after the pose: spread_fingers)"""
    sp = {}
    for fn in C.FINGERS:
        for k, w in (("01", 0.6), ("02", 1.0), ("03", 0.8)): sp[f"{fn}_{k}_{side}"] = [("curl", curl * w)]
    sp[f"thumb_02_{side}"] = [("curl", 6.0 + 0.3 * curl)]; sp[f"thumb_03_{side}"] = [("curl", 4.0 + 0.3 * curl)]
    if spread: sp[f"spread_{side}"] = spread
    return sp


def hand(fr, side, x, y, z, pole, axis=None, palm=None, curl=4.0, spread=0.0):
    """the hand's root at (x her right, y forward, z up) cm from the base of her neck (in her frame `fr`), the elbow toward
    `pole`, the fingers' way `axis` and the palm facing `palm` as near as the wrist allows; open (curl, spread)"""
    want = {}
    if axis is not None: want["axis"] = fr.v(axis)
    if palm is not None: want["palm"] = fr.v(palm)
    sp = {f"arm_{side}": ("reach", fr.at(x, y, z), fr.v(pole), want, None)}
    sp.update(open_hand(side, curl, spread))
    return sp


SPREAD_W = {"index": 1.0, "middle": 0.25, "ring": -0.45, "pinky": -1.0}


def spread_context(ctx, arm_obj):
    """each finger's first bone: the palm's normal in its own rest frame, and the sign that fans it toward its own side"""
    B = arm_obj.data.bones; ctx["spread"] = {}
    for s in "lr":
        h = f"hand_{s}"; n = (B[h].matrix_local.to_quaternion() @ ctx["palm"][h]).normalized()
        across = (B[f"index_01_{s}"].head_local - B[f"pinky_01_{s}"].head_local).normalized()
        for fn in C.FINGERS:
            b = B[f"{fn}_01_{s}"]; d = (b.tail_local - b.head_local).normalized()
            sg = 1.0 if n.cross(d).dot(across) > 0 else -1.0
            ctx["spread"][(s, fn)] = (b.matrix_local.to_quaternion().inverted() @ n, sg)


def apply(arm_obj, spec, ctx):
    """martialartist_clips.apply (the legs, then the arms solved), then the fingers fanned (spread_<side>)"""
    spreads = {k[-1]: v for k, v in spec.items() if k.startswith("spread_")}
    MA.apply(arm_obj, {k: v for k, v in spec.items() if not k.startswith("spread_")}, ctx)
    P = arm_obj.pose.bones
    for s, deg in spreads.items():
        for fn in C.FINGERS:
            ax, sg = ctx["spread"][(s, fn)]; pb = P[f"{fn}_01_{s}"]
            pb.rotation_mode = 'QUATERNION'
            pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion(ax, math.radians(deg * sg * SPREAD_W[fn]))
    bpy.context.view_layer.update()
    return {pb.name: pb.matrix_basis.decompose() for pb in arm_obj.pose.bones}


def side_hand(fr, side, k=0.0, curl=16.0):
    """a hand hanging easy by her hip, open, the palm toward her thigh, the elbow a little bent and back (k: breathing)"""
    sx = 1.0 if side == "r" else -1.0
    return hand(fr, side, sx * (13 + 0.6 * k), 7 + 0.8 * k, -30 + 0.6 * k, fr.D(side, 0.6, -0.7, -0.4),
                axis=C.D(side, 0.1, 0.3, -1.0), palm=C.D(side, -1.0, 0.25, 0.0), curl=curl)


# ---------------------------------------------------------------- the poses
def idle(ctx, k=0.0):
    """the weight on her left leg (the pelvis over it), the right knee easy and its foot a little forward and out"""
    fr = Fr()
    sp = body(ctx, fr, lean=1.0 - 1.4 * k, side=-2.0, drop=1.5 + 0.3 * k, shift=3.0, look=0.8)
    sp.update(plant("l", 0, 0, yaw=-6)); sp.update(plant("r", 2, 7, yaw=-16, pitch=8))
    sp.update(side_hand(fr, "r", k)); sp.update(side_hand(fr, "l", k))
    return sp


def cast_bolt(ctx, k):
    fr = Fr()
    if k == "wind":
        sp = body(ctx, fr, twist=32, lean=-4, drop=5, look=0.9)
        sp.update(plant("l", -2, 10, yaw=-6)); sp.update(plant("r", 3, -10, yaw=-30))
        sp.update(hand(fr, "r", 15, -6, 0, fr.D("r", 0.5, -0.4, -1.0), axis=C.D("r", 0.1, 0.2, 1.0), palm=F, curl=22, spread=6))
        sp.update(hand(fr, "l", -6, 26, -8, fr.D("l", 0.4, 0.0, -1.0), axis=F, palm=C.D("l", -0.3, 0.0, -1.0), curl=6))
    elif k == "release":
        sp = body(ctx, fr, twist=-22, lean=9, drop=7, fwd=6, hips=0.3)
        sp.update(plant("l", -2, 10, yaw=-6)); sp.update(plant("r", 3, -10, yaw=-24, pitch=12))
        sp.update(hand(fr, "r", 2, 34, -4, fr.D("r", 0.4, 0.0, -1.0), axis=C.D("r", 0.0, 0.5, 0.85), palm=F, curl=2, spread=14))
        sp.update(hand(fr, "l", -16, -8, -28, fr.D("l", 0.5, -0.3, -1.0), axis=C.D("l", 0.2, -0.3, -1.0), palm=C.D("l", -1.0, 0.0, 0.0), curl=14))
    else:                                                 # follow
        sp = body(ctx, fr, twist=-16, lean=7, drop=6, fwd=5, hips=0.25)
        sp.update(plant("l", -2, 10, yaw=-6)); sp.update(plant("r", 3, -10, yaw=-24, pitch=6))
        sp.update(hand(fr, "r", 3, 28, -10, fr.D("r", 0.4, 0.0, -1.0), axis=C.D("r", 0.0, 0.8, 0.3), palm=C.D("r", -0.2, 0.5, -0.8), curl=8, spread=8))
        sp.update(hand(fr, "l", -16, -6, -28, fr.D("l", 0.5, -0.3, -1.0), axis=C.D("l", 0.2, -0.3, -1.0), palm=C.D("l", -1.0, 0.0, 0.0), curl=14))
    return sp


def summon1(ctx, k):
    """the beckoning call: reach (palm up), pull (up and back to her chest, the fingers curling in)"""
    fr = Fr(); ext = 0.85 if k == "reach2" else 1.0
    if k in ("reach", "reach2"):
        sp = body(ctx, fr, twist=-8, lean=7 * ext, drop=4, fwd=3 * ext, look=0.8)
        sp.update(plant("l", -2, 6, yaw=-6)); sp.update(plant("r", 3, -4, yaw=-20))
        sp.update(hand(fr, "r", 4, 32 * ext, -14, fr.D("r", 0.4, 0.0, -1.0), axis=F, palm=U, curl=4, spread=10))
    else:
        sp = body(ctx, fr, twist=8, lean=-6, drop=3, look=0.8, head=-4)
        sp.update(plant("l", -2, 6, yaw=-6)); sp.update(plant("r", 3, -4, yaw=-20))
        sp.update(hand(fr, "r", 11, 13, -11, fr.D("r", 0.7, -0.2, -1.0), axis=C.D("r", -0.2, 0.1, 1.0), palm=C.D("r", -0.3, -0.8, 0.5), curl=50, spread=4))
    sp.update(side_hand(fr, "l", curl=14))
    return sp


def summon2(ctx, k):
    """the two-handed push: gathered at her chest (elbows out, crouched), thrust forward with a step on the left foot"""
    fr = Fr(); sp = {}
    if k == "gather":
        sp = body(ctx, fr, lean=-5, drop=9, look=0.8)
        sp.update(plant("l", -1, 2, yaw=-8)); sp.update(plant("r", 1, -2, yaw=-14))
        for s in "rl":
            sx = 1.0 if s == "r" else -1.0
            sp.update(hand(fr, s, sx * 9, 13, -12, fr.D(s, 1.0, -0.3, -0.3), axis=C.D(s, -0.3, 0.3, 1.0), palm=F, curl=12, spread=6))
    else:
        push = k == "push"
        sp = body(ctx, fr, lean=11 if push else 8, drop=12 if push else 10, fwd=14 if push else 12, look=0.8)
        sp.update(plant("l", -2, 32, yaw=-4)); sp.update(plant("r", 2, -12, yaw=-10, pitch=25 if push else 15))
        for s in "rl":
            sx = 1.0 if s == "r" else -1.0
            sp.update(hand(fr, s, sx * 7, 33 if push else 28, -10 if push else -13, fr.D(s, 0.6, 0.0, -1.0),
                           axis=C.D(s, -0.1, 0.5, 0.85), palm=F, curl=2 if push else 8, spread=16 if push else 8))
    return sp


def summon3(ctx, k):
    """the ground strike: the right hand raised, dropped onto the right knee, the right palm slammed at the floor ahead,
    the left arm out for balance; held; risen"""
    fr = Fr()
    if k == "raise":
        sp = body(ctx, fr, twist=14, lean=-6, drop=10, look=0.85, head=-6)
        sp.update(plant("l", -2, 24, yaw=-6)); sp.update(plant("r", 3, -14, yaw=-20, pitch=10))
        sp.update(hand(fr, "r", 10, 4, 26, fr.D("r", 1.0, 0.0, 0.2), axis=U, palm=F, curl=6, spread=10))
        sp.update(hand(fr, "l", -26, 8, -14, fr.D("l", 0.3, -0.2, -1.0), axis=C.D("l", 1.0, 0.2, -0.3), palm=-U, curl=8))
    elif k in ("slam", "held"):
        low = 1.0 if k == "slam" else 1.04
        sp = body(ctx, fr, twist=-10, lean=48 * low, drop=54 * low, look=0.6, head=-16, pitch=22)
        sp.update(plant("l", -2, 34, yaw=-4)); sp.update(plant("r", 2, -40, yaw=-6, pitch=55))
        sp.update(hand(fr, "r", 14, 30, -100, fr.D("r", 1.0, 0.0, 0.3), axis=F, palm=-U, curl=2, spread=18))
        sp.update(hand(fr, "l", -34, 4, -12, fr.D("l", 0.0, -0.3, -1.0), axis=C.D("l", 1.0, 0.1, -0.2), palm=-U, curl=6, spread=8))
    else:                                                 # rising
        sp = body(ctx, fr, lean=16, drop=20, look=0.7)
        sp.update(plant("l", -2, 20, yaw=-6)); sp.update(plant("r", 3, -14, yaw=-14, pitch=20))
        sp.update(hand(fr, "r", 10, 16, -28, fr.D("r", 0.6, 0.0, -1.0), axis=C.D("r", 0.0, 0.5, -1.0), palm=C.D("r", -0.5, 0.0, -1.0), curl=10))
        sp.update(hand(fr, "l", -18, 8, -24, fr.D("l", 0.4, -0.2, -1.0), axis=C.D("l", 0.6, 0.2, -0.8), palm=-U, curl=10))
    return sp


def summon4(ctx, k):
    """the rising invocation: arms low at her sides, swept up overhead (on her toes, head back), held, then both hands
    brought down forward to point at the ground ahead"""
    fr = Fr(); sp = {}
    feet = lambda pitch=0.0: (plant("l", -3, 6, yaw=-10, pitch=pitch), plant("r", 3, -4, yaw=-14, pitch=pitch))
    if k == "low":
        sp = body(ctx, fr, lean=8, drop=8, look=0.6, head=10)
        for f_ in feet(): sp.update(f_)
        for s in "rl":
            sx = 1.0 if s == "r" else -1.0
            sp.update(hand(fr, s, sx * 26, -8, -24, fr.D(s, 0.3, -1.0, -0.3), axis=C.D(s, 0.5, -0.1, -1.0), palm=F, curl=10, spread=6))
    elif k in ("high", "hold"):
        hold = k == "hold"
        sp = body(ctx, fr, lean=-19 if hold else -16, drop=-3, look=0.6, head=-32 if hold else -26)
        for f_ in feet(22): sp.update(f_)
        for s in "rl":
            sx = 1.0 if s == "r" else -1.0
            sp.update(hand(fr, s, sx * (24 if hold else 22), 2, 24, fr.D(s, 1.0, 0.0, 0.0), axis=C.D(s, 0.6, 0.0, 1.0),
                           palm=C.D(s, -1.0, 0.3, 0.2), curl=3, spread=16))
    else:                                                 # point at the ground ahead
        held = k == "point2"
        sp = body(ctx, fr, lean=18 if not held else 16, drop=8, fwd=4, look=0.6, head=12)
        for f_ in feet(): sp.update(f_)
        for s in "rl":
            sx = 1.0 if s == "r" else -1.0
            sp.update(hand(fr, s, sx * 7, 26, -32, fr.D(s, 0.6, 0.0, -1.0), axis=C.D(s, -0.1, 0.6, -0.8), palm=C.D(s, -0.2, -0.3, -1.0),
                           curl=4 if not held else 8, spread=10))
    return sp


SPIN = {"s0": -40, "s1": -120, "s2": -210, "s3": -300, "s4": -360}


def summon5(ctx, k):
    """the spiral: a clockwise turn (to her right, seen from above) on the left foot, the pelvis over it, the right foot
    off the floor, both arms spread wide; at the front both hands thrust forward and down, the fingers spread"""
    if k in SPIN:
        yaw = SPIN[k]; fr = Fr(yaw)
        mid = k in ("s1", "s2", "s3")
        # (leaning into the turn, the arms on a slant: the right, leading, high, the left trailing low)
        sp = body(ctx, fr, lean=4, side=-10 if mid else -5, drop=6, shift=10, look=0.9, head=-4)
        sp.update(under("l", 0.0, yaw=yaw - 10, pitch=12))
        sp.update(kick("r", fr.D("r", 0.25, 0.1, -1.0), fr.D("r", 0.15, -0.65, -0.75), fr.D("r", 0.1, 0.4, -0.9), fr.v(F)))
        for s, z, y in (("r", 8 if mid else -6, 4), ("l", -16 if mid else -10, -4)):
            sx = 1.0 if s == "r" else -1.0
            sp.update(hand(fr, s, sx * 33, y, z, fr.D(s, 0.0, -0.4, -1.0), axis=C.D(s, 1.0, 0.0, 0.0), palm=C.D(s, 0.0, 0.4, -1.0), curl=4, spread=12))
        return sp
    fr = Fr(); thrust = k == "thrust"
    sp = body(ctx, fr, lean=13 if thrust else 10, drop=12 if thrust else 10, fwd=6, look=0.7, head=6)
    sp.update(plant("l", -4, 14, yaw=-6)); sp.update(plant("r", 4, -14, yaw=-20, pitch=12))
    for s in "rl":
        sx = 1.0 if s == "r" else -1.0
        sp.update(hand(fr, s, sx * 9, 30 if thrust else 27, -22 if thrust else -24, fr.D(s, 0.6, 0.0, -1.0), axis=C.D(s, 0.0, 0.8, -0.5),
                       palm=C.D(s, 0.0, 0.3, -1.0), curl=2, spread=20 if thrust else 14))
    return sp


# the casts: (clip, the key poses as (seconds, maker, its key; None the idle), the release (`hit`), the bone it leaves from)
CASTS = [
    ("CastBolt", [(0.0, None, 0), (0.24, cast_bolt, "wind"), (0.40, cast_bolt, "release"), (0.56, cast_bolt, "follow"), (0.95, None, 0)], 0.40, "hand_r"),
    ("Summon1", [(0.0, None, 0), (0.28, summon1, "reach"), (0.55, summon1, "pull"), (0.76, summon1, "reach2"), (1.00, summon1, "pull"),
                 (1.25, summon1, "pull"), (1.65, None, 0)], 1.00, "hand_r"),
    ("Summon2", [(0.0, None, 0), (0.42, summon2, "gather"), (0.60, summon2, "push"), (0.86, summon2, "follow"), (1.45, None, 0)], 0.60, "hand_r"),
    ("Summon3", [(0.0, None, 0), (0.45, summon3, "raise"), (0.72, summon3, "slam"), (1.15, summon3, "held"), (1.55, summon3, "rise"), (2.00, None, 0)], 0.72, "hand_r"),
    ("Summon4", [(0.0, None, 0), (0.40, summon4, "low"), (0.92, summon4, "high"), (1.25, summon4, "hold"), (1.55, summon4, "point"),
                 (1.80, summon4, "point2"), (2.20, None, 0)], 1.55, "hand_r"),
    ("Summon5", [(0.0, None, 0), (0.18, summon5, "s0"), (0.40, summon5, "s1"), (0.62, summon5, "s2"), (0.84, summon5, "s3"), (1.04, summon5, "s4"),
                 (1.24, summon5, "thrust"), (1.50, summon5, "follow"), (1.95, None, 0)], 1.24, "hand_r"),
]


def context(arm_obj, scene):
    ctx = C.context(arm_obj); DC.add_thumb_op(ctx, arm_obj); ctx["cm"] = R.model_height(scene) / 170.0
    R.arm_context(ctx, arm_obj); MA.leg_context(ctx, arm_obj); spread_context(ctx, arm_obj)
    return ctx


def make_clips(arm_obj, scene, clips):
    import warrior3_clips as W3
    out = {}
    for nm in [n for n in clips if n.lower().startswith(DROP)]: del clips[nm]
    for nm, frames in list(clips.items()):
        fixed, mean = W3.recentre(arm_obj, frames)
        if fixed is not None:
            out[nm] = fixed; print("S4 %s: the pelvis held (%.2f, %.2f) of her height off its rest place on average: moved back" % (nm, mean.x / W3.W2_height(arm_obj), mean.y / W3.W2_height(arm_obj)))
    # rogue_clips': the stabs (a dagger in each hand); given no clips, so her own keep Tripo's hands (it closes theirs)
    made = R.make_clips(arm_obj, scene, {})
    for nm in ("Stab1", "Stab2", "Stab3"): out[nm] = made[nm]
    ctx = context(arm_obj, scene)
    P = lambda spec: apply(arm_obj, spec, ctx)
    i0, i1 = P(idle(ctx)), P(idle(ctx, 1.0))
    out["Idle"] = C.sample([(0.0, i0), (1.2, i1), (2.4, i0)])
    times = {}
    for name, keys, hit, bone in CASTS:
        poses = [(t, i0 if fn is None else P(fn(ctx, k))) for t, fn, k in keys]
        out[name] = C.sample(poses); times[name] = {"length": keys[-1][0], "hit": hit, "bone": bone}
    for pb in arm_obj.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    worst = max(ctx["wrists"], key=lambda sw: R.over(*sw[1]))
    print("S4 wrists: %d hands solved, the furthest past a limit %.1f deg (%s: flexion %.0f, deviation %.0f, twist %.0f)"
          % (len(ctx["wrists"]), R.over(*worst[1]), worst[0], *worst[1]))
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) > 1 and os.path.isdir(argv[1]):
        json.dump(times, open(os.path.join(argv[1], "s4_times.json"), "w"), indent=1)
    return out


# ---------------------------------------------------------------- preview
def _sheet(paths, cols, out_path):
    """the pictures (rows of `cols`) in one PNG"""
    import numpy as np
    imgs = []
    for p in paths:
        im = bpy.data.images.load(p); w, h = im.size
        imgs.append(np.array(im.pixels[:]).reshape(h, w, 4)); bpy.data.images.remove(im)
    h, w = imgs[0].shape[:2]; rows = (len(imgs) + cols - 1) // cols
    big = np.ones((rows * h, cols * w, 4), dtype=np.float32)
    for i, a in enumerate(imgs):
        r, c = divmod(i, cols); big[(rows - 1 - r) * h:(rows - r) * h, c * w:(c + 1) * w] = a       # (Blender's rows go up)
    im = bpy.data.images.new("sheet", cols * w, rows * h, alpha=True); im.pixels[:] = big.ravel()
    im.filepath_raw = out_path; im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)


if __name__ == "__main__" and os.path.basename(sys.argv[sys.argv.index("-P") + 1] if "-P" in sys.argv else "") == "summoner4_clips.py":
    argv = sys.argv[sys.argv.index("--") + 1:]
    src, prefix = argv[0], argv[1]; only = argv[2].split(",") if len(argv) > 2 else None
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    sc = bpy.context.scene
    for o in [o for o in sc.objects if o.type == 'MESH' and not o.vertex_groups]: bpy.data.objects.remove(o, do_unlink=True)
    arm_obj = next(o for o in sc.objects if o.type == 'ARMATURE')
    for pb in arm_obj.pose.bones: pb.rotation_mode = 'QUATERNION'
    # her own clips, sampled as tripo_build does (for Walk and Run)
    own = {}
    ad = arm_obj.animation_data
    if ad and (not only or "Walk" in only or "Run" in only):
        for act in list(bpy.data.actions):
            nm = act.name.split(".")[0]; nm = nm[:1].upper() + nm[1:]
            if nm not in ("Walk", "Run"): continue
            ad.action = act
            if hasattr(ad, "action_slot") and act.slots: ad.action_slot = act.slots[0]
            f0, f1 = [int(round(v)) for v in act.frame_range]; fr_ = []
            for t in range(f0, f1 + 1):
                sc.frame_set(t); fr_.append({pb.name: pb.matrix_basis.decompose() for pb in arm_obj.pose.bones})
            own[nm] = fr_
    if ad: ad.action = None
    for pb in arm_obj.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    ctx = context(arm_obj, sc)
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'TEXTURE'; sc.display.shading.light = 'STUDIO'
    sc.render.resolution_x = 300; sc.render.resolution_y = 400
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.12
    bpy.ops.mesh.primitive_plane_add(size=1.6, location=(0, 0, ctx["floor"] - 0.004)); fl = bpy.context.active_object
    m = bpy.data.materials.new("floor"); m.diffuse_color = (0.25, 0.35, 0.25, 1); fl.data.materials.append(m)
    VIEWS = (("front", 0), ("side", 90), ("q", 35), ("back", 180))

    def shoot(tag):
        ps = []
        for view, ang in VIEWS:
            a = math.radians(ang); d = Vector((math.sin(a), -math.cos(a), 0.15))
            cam.location = Vector((0, -0.08, 0.5)) + d * 4.0; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = f"{tag}_{view}.png"; bpy.ops.render.render(write_still=True); ps.append(sc.render.filepath)
        return ps

    import warrior3_clips as W3
    for nm, frames in own.items():
        fixed, mean = W3.recentre(arm_obj, frames); frames = fixed or frames
        print("S4 preview %s: recentred %s (mean offset %.3f m)" % (nm, fixed is not None, mean.length))
        ps = []
        for fi in (0, len(frames) // 4, len(frames) // 2):
            for pb in arm_obj.pose.bones:
                l, q, s = frames[fi][pb.name]; pb.location = l; pb.rotation_quaternion = q; pb.scale = s
            bpy.context.view_layer.update(); ps += shoot(f"{prefix}_{nm}_{fi}")
        _sheet(ps, len(VIEWS), f"{prefix}_{nm}_sheet.png")
    for pb in arm_obj.pose.bones: pb.matrix_basis.identity()
    if not only or "Idle" in only:
        ps = []
        for ki, k in enumerate((0.0, 1.0)):
            apply(arm_obj, idle(ctx, k), ctx); ps += shoot(f"{prefix}_Idle_{ki}")
        _sheet(ps, len(VIEWS), f"{prefix}_Idle_sheet.png")
    for name, keys, hit, bone in CASTS:
        if only and name not in only: continue
        ps = []
        for ki, (t, fn, k) in enumerate(keys):
            if fn is None: continue
            apply(arm_obj, fn(ctx, k), ctx); ps += shoot(f"{prefix}_{name}_{ki}")
        _sheet(ps, len(VIEWS), f"{prefix}_{name}_sheet.png")
    # 'Name@' in the list: the made clip's frames (every third, as sampled between the keys), front and three-quarter
    between = [n[:-1] for n in (only or []) if n.endswith("@")]
    if between:
        made = make_clips(arm_obj, sc, {})
        for nm in between:
            frames = made[nm]; ps = []
            for fi in range(0, len(frames), 3):
                for pb in arm_obj.pose.bones:
                    l, q, s = frames[fi][pb.name]; pb.location = l; pb.rotation_quaternion = q; pb.scale = s
                bpy.context.view_layer.update()
                for view, ang in (("front", 0), ("q", 35)):
                    a = math.radians(ang); d = Vector((math.sin(a), -math.cos(a), 0.15))
                    cam.location = Vector((0, -0.08, 0.5)) + d * 4.0; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
                    sc.render.filepath = f"{prefix}_{nm}_f{fi:02d}_{view}.png"; bpy.ops.render.render(write_still=True); ps.append(sc.render.filepath)
            _sheet(ps, 6, f"{prefix}_{nm}_frames.png")
    worst = max(ctx["wrists"], key=lambda sw: R.over(*sw[1])) if ctx.get("wrists") else None
    print("PREVIEW DONE", worst and (round(R.over(*worst[1]), 1), worst[0], [round(v) for v in worst[1]]))
