"""Clips random_dungeonmagic_level5's found weapons need, made on a Tripo hero's own rig (tripo_build.py's clip_maker;
the Warrior, the Warlock and the Rogue have the same 61 bones). Made (the environment's W5_CLIPS picks some: e.g.
"Bow"; all by default):
  W5_TwoHand1  a two-handed sword, both hands on the hilt (the left a hand's breadth below the right): a diagonal cut
               from over her right shoulder down across to her left hip
  W5_TwoHand2  an overhead chop: raised over her head (elbows out and up), brought down in front of her
  W5_TwoHand3  a horizontal sweep from her right round to her left, her waist turning with it
  W5_Bow       the bow in her left hand: raised at the target (her shoulders turned, the left arm out, the bow upright),
               the right hand at the string, drawn to her cheek, loosed, lowered
  W5_Shoot     a crossbow at her right shoulder: the Rogue's shot (rogue_clips.shoot) on this rig
Poses are written as in rogue_clips.py (the arms solved: the elbow a hinge, the wrist within its limits). A weapon's way
in the hand (its local frame, the grips of pipeline/unreal/855 hold it so, from the same reference-pose bones):
  sword    the blade: the thumb's way leaning toward the fingers by TILT["sword"]; its edge the way the fingers point
           (square to the blade): the knuckles lead the cut
  bow      the limbs: the thumb's way leaning by TILT["bow"]; its front (where the arrow flies) the forearm's way square
           to them
  crossbow rogue_clips' (GRIP_TILT["crossbow"])
Each hand is put where the pose says with the weapon turned exactly (the left on a two-handed hilt: a place on the
sword in the right hand, LEFT_ON_HILT cm toward the pommel: her two fists' span on the hilt, measured on her mesh, plus
FIST_GAP; the left hand turned about the hilt by its own angle, at most 60 degrees from the right's, so each forearm
comes to the hilt from its own side). The two-handed cuts follow reference poses of a two-handed sword (posemy.art's):
the hilt held out at arm's length, the hands below the blade and the blade rising out of the fists (a fist holds the grip
across the palm: the blade leaves the forearm at 100 to 110 degrees, never along it), her waist and chest turned with
the cut, landing at her chest well out in front, following through level or dipping a little; a hero may have her own
places for some keys (HERO_PLACES). A place is searched where her arms clear her torso (inside: only where the torso is
round the point) and head, each other (GAP_MIN) and the wrists' limits; the follow-through is solved from the release's
arms. Frame by frame (swing): the blade's edge carried from the frame before, its turn about the blade at most 30
degrees a frame and 90 from the carried edge (a key frame's pulled to its key's), the sweep's blade swung round her
(round_turn), the upper arms rather as they were a frame ago (rogue_clips.solve_arm's prev_arm) and led toward the
follow-through's from the blow on, so the engine's blend between frames keeps the left hand on the hilt; the clip ends
held at its follow-through. The arrow leaves at RELEASE["Bow"], the bolt at
rogue_clips.RELEASE; the cuts land where the hands move fastest (855 measures them). times: <out_dir>/w5_times.json.
Preview (stand-ins on the hands: a cyan blade, an orange bow): blender -b -P weapon5_clips.py -- model.glb out_prefix"""
import json, math, os, sys
import bpy
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import caster_clips as C
import darkcaster_clips as DC
import rogue_clips as R
D, F, U = C.D, C.F, C.U
FPS = C.FPS
TILT = {"sword": 25.0, "bow": 15.0}
LEFT_ON_HILT = 7.5          # (cm of her 170: Tripo's heroes have short arms, 34 cm from shoulder to wrist, and hands to match;
                            # make_clips sets it from her fists: their span on the hilt, measured on the mesh, and FIST_GAP)
FIST_GAP = 1.0              # cm between the two fists on the hilt (7.5 put 37 to 48 of the left hand's vertices inside the right)
GAP_MIN = 5.0               # cm the two forearms keep apart (the hilt at her breastbone crossed them over her chest)
GAP_W = 100.0                # what a cm short of GAP_MIN costs, squared, against a wrist's degree past its limits
TIMES = {"W5_TwoHand1": (0.40, 0.58, 0.82, 1.30), "W5_TwoHand2": (0.44, 0.62, 0.86, 1.35), "W5_TwoHand3": (0.38, 0.56, 0.80, 1.25)}
BOW = {"raise": 0.26, "draw": 0.52, "release": 0.58, "loose": 0.64, "hold": 0.82, "end": 1.15}
RELEASE = {"Bow": BOW["release"]}


def frames(ctx, arm_obj):
    """each hand's local ways for a sword and a bow (from the reference pose, as rogue_clips.arm_context does)"""
    B = arm_obj.data.bones
    for s in "rl":
        A = ctx["arms"][s]; h0 = B[f"hand_{s}"].matrix_local.to_quaternion()
        fore = (B[f"hand_{s}"].head_local - B[f"lowerarm_{s}"].head_local).normalized()
        th = B[f"thumb_01_{s}"].head_local - B[f"hand_{s}"].head_local
        along = (B[f"middle_01_{s}"].head_local - B[f"hand_{s}"].head_local).normalized()
        th = th - along * th.dot(along); th = (th - fore * th.dot(fore)).normalized()
        sl = lambda deg: (th * math.cos(math.radians(deg)) + fore * math.sin(math.radians(deg))).normalized()
        blade = sl(TILT["sword"]); edge = (along - blade * along.dot(blade)).normalized()
        limb = sl(TILT["bow"]); front = (fore - limb * fore.dot(limb)).normalized()
        A["local"].update({"xb_front": A["local"]["front"], "xb_up": A["local"]["up"],
                           "sword": h0.inverted() @ blade, "edge": h0.inverted() @ edge,
                           "bow_front": h0.inverted() @ front, "bow_up": h0.inverted() @ limb})


def use(ctx, which):
    """the weapon the 'exact' turns of solve_arm hold: 'sword', 'bow' or 'crossbow'"""
    for s in "rl":
        L = ctx["arms"][s]["local"]
        L["front"], L["up"] = {"sword": (L["sword"], L["edge"]), "bow": (L["bow_front"], L["bow_up"]), "crossbow": (L["xb_front"], L["xb_up"])}[which]


def square(blade, edge):
    b = blade.normalized(); e = edge - b * edge.dot(b)
    return b, e.normalized()


def two_hands(at, blade, edge, pole_r=None, pole_l=None, phi=0.0):
    """both hands on the hilt: the right at `at` (cm from the base of her neck: right, forward, up), the blade and its
    edge exactly as given; the left LEFT_ON_HILT cm below it on the hilt, turned `phi` degrees further about the hilt
    (turned the same, both forearms left the hilt the same way, parallel: the upper one swept through the lower hand)"""
    b, e = square(blade, edge)
    sp = R.reach("r", at, pole_r or D("r", 0.7, -0.1, -0.7), None, {"front": b, "up": e})
    el = Quaternion(b, math.radians(phi)) @ e
    sp.update(R.reach("l", ("palm_on", -LEFT_ON_HILT, 0.0, 0.0), pole_l or D("l", 0.7, -0.1, -0.7), None, {"front": b, "up": el}))
    sp.update(DC.fist("r")); sp.update(DC.fist("l"))
    return sp


# A two-handed pose: (the body, where the right hand goes, the blade's way, the way its edge should rather lead). The
# hands' places, cm from the base of her neck (right, forward, up), are inside her reach: her shoulders are 9 to 12 cm
# out from it and turn with her twist, her arm is 32 to 35 cm to the wrist. The blade's turn about its own length is
# chosen by solve2: the one that asks least of both wrists (the edge hint only breaks ties).
# (twist, lean, knees, where the right hand goes, the blade's way, the way its edge should rather lead)
# The places follow reference poses of a two-handed sword (posemy.art's "two handed sword poses": the overhead strike,
# the guarded stance, the mid-swing slash, the thrust): the hilt is held out at arm's length, above the head for a cut
# from above, in front of the chest with the arms reaching forward as it lands, low by the hip after it; the arms nearly
# straight, coming from either shoulder and meeting only at the hilt. (The first places held the hilt a hand in front of
# her breastbone: both forearms lay across her chest, one over the other, and the left wrist folded 69 degrees past its
# limits to close round the hilt.)
def guard2():
    """the guard (the katana's middle guard): the hands well out in front of her lower belly, the left (on the pommel)
    lower, the blade rising toward an opponent's throat, the elbows down beside her"""
    return 5, 2, 8, (2, 38, -26), D("r", 0.0, 0.78, 0.62), D("r", 0.0, 0.62, -0.78)


# (her chest reaches 16 cm forward of her neck's base from 10 to 20 cm below it, 6 to 9 cm at her shoulders and 12 cm at
# her waist.) Through the strike and the follow-through her chest (hips and spine: HIPS) turns to face the way the blade
# points and the hilt is held out along that way, so the blade runs straight out from her chest and the hands stack one
# behind the other: with the blade pointing past her chest's front the hand nearer the guard (the right) came across the
# other and the forearms crossed (the sweep: the waist has to turn for the sword to sweep). The overhead chop is raised
# over her head, the blade lying back over it, her elbows out and up and her shoulders raised (ELEVATE).
# The wrists: a fist holds the grip across the palm, so the blade leaves it at about 100 to 110 degrees to the forearm
# (140 with the wrist bent fully toward the little finger), never along it. A blade pointing ahead is held with the hands
# below it and the arms angled down from the shoulders, the blade rising out of the fists; held level at shoulder height
# with the arms reaching along it, the wrists went 23 to 42 degrees past their limits. So the cuts land with the hilt at
# her chest, well out in front, the blade rising (a steeper blade also keeps the left hand, the lower one on the
# hilt, under the right instead of back against her chest), and follow through with it level or dipping a little, not
# pointing down (down along forearms that point down is the same strain); her body (hips, spine, shoulders) and her forearms' turn do the aiming. Below her
# lower chest (16 cm under her neck) the left forearm, coming from the far shoulder, lies on her breast: the hilt stays
# at or above it unless it is well out in front.
OVERHEAD_POLES = ((0.9, 0.15, 0.4), (0.9, 0.15, 0.4))


# (a hero's own places for some keys (a place, or a place and the blade's way), where her body takes another: the
# Warlock's head and hair stand higher and wider, so her arms raised for the chop at (2, 4, 24) were 6.5 cm short of
# clearing them; her diagonal's follow-through, her sweep's blow and her chop's blow and follow-through were 1 to 2 cm
# into her at the Warrior's places. Picked by the clip folder's name, or W5_HERO)
HERO_PLACES = {}


def hero_key(p, v):
    """a key's params with a hero's own place (and blade) put in"""
    if isinstance(v[0], tuple): return p[:3] + (v[0], D("r", *v[1])) + p[5:]
    return p[:3] + (v,) + p[4:]


def hero_name():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return os.environ.get("W5_HERO") or (os.path.basename(os.path.normpath(argv[1])) if len(argv) > 1 and os.path.isdir(argv[1]) else "")


def two1(k):
    """a diagonal cut: from beside her raised right shoulder (the blade up and back over it), down across her at full
    reach (struck at her chest's height), on low to her left hip"""
    if k == "mid": return None
    if k == "wind": return 35, -3, 8, (14, 12, 20), D("r", 0.3, -0.45, 0.85), D("r", -0.3, 0.8, -0.4)
    if k == "release": return -15, 9, 13, (-4, 46, -16), D("r", -0.35, 0.8, 0.5), D("r", -0.6, 0.2, -0.8)
    return -40, 7, 11, (-18, 36, -32), D("r", -0.55, 0.65, -0.5), D("r", -0.2, 0.6, -0.5)


def two2(k):
    """an overhead chop: from the raised guard (the hands well over her head, the blade back over it, the elbows out
    and forward), down to full reach at her chest's height (the blade rising a little, as a kendo strike lands), back to
    the middle guard's height"""
    # (half way up: the sword upright, the hands in front of her forehead, as the reference's raised guard begins. Eased
    # straight from the middle guard to the blade back over her head, it turned 150 degrees and the wrists went 34 to 55
    # past their range)
    if k == "mid": return 0, -4, 6, (0, 26, 12), D("r", 0.0, 0.15, 0.99), D("r", 0.0, 1.0, -0.15)
    if k == "wind": return 0, -8, 6, (0, 18, 40), D("r", 0.0, -0.7, 0.7), D("r", 0.0, 0.7, 0.7), OVERHEAD_POLES
    if k == "release": return 0, 15, 16, (0, 48, -6), D("r", 0.0, 0.85, 0.5), D("r", 0.0, 0.3, -1.0)
    return 0, 12, 14, (0, 42, -24), D("r", 0.0, 0.85, -0.52), D("r", 0.0, -0.6, -0.8)


def two3(k):
    """a horizontal sweep from her right round to her left, turned at the waist: from by the right of her chest (the
    blade up and back over her right shoulder, as a bat is held), round to full reach at her waist's height, the blade
    level, on to her left side"""
    # (half way, just before the blow: the blade level and out to her right, the hands coming round in front of her right
    # side. Eased straight from the wind-up to the blow, the blade turned 165 degrees in four frames and the left wrist
    # went 98 degrees past its range, the forearms 1 to 2 cm apart)
    if k == "mid": return 15, 2, 10, (12, 36, -14), D("r", 0.75, 0.65, 0.12), D("r", -0.6, 0.75, 0.0)
    if k == "wind": return 50, -2, 9, (20, 30, 8), D("r", 0.05, -0.25, 0.97), D("r", -0.45, -0.35, 0.0)
    if k == "release": return -25, 6, 12, (-4, 46, -24), D("r", -0.45, 0.88, 0.15), D("r", -0.6, -0.8, 0.0)
    return -55, 5, 10, (-24, 34, -26), D("r", -0.85, 0.5, 0.1), D("r", 0.3, 0.9, 0.0)


POLES = [((0.7, -0.1, -0.7), (0.7, -0.1, -0.7)), ((0.7, -0.1, -0.7), (1.0, 0.0, -0.25)), ((0.7, -0.1, -0.7), (0.85, -0.4, -0.35)),
         ((1.0, 0.0, -0.25), (1.0, 0.0, -0.25)), ((0.7, -0.1, -0.7), (0.6, 0.35, -0.7)), ((1.0, 0.0, -0.25), (0.85, -0.4, -0.35)), OVERHEAD_POLES]


# (the user's reference, a katana held through its guards (examples/katana_2handed.mp4): the wrists near straight, the
# blade set by the forearms' turn and the elbows; the elbows out to their own sides of the hands and down, never folded
# up and in across her chest. COMFORT: the ranges a wrist holds the grip in without strain (the limits, FLEX / DEV /
# TWIST, let it bend 50 to 60 degrees nearly free: the user saw the right wrist bent too far); ELBOWS: rogue_clips'
# elbow rules (in, up: how far the elbow may point in toward her middle and up off the line from shoulder to hand, cm)
COMFORT = {"flex": (-20.0, 20.0), "dev": (-35.0, 5.0), "twist": (-60.0, 60.0), "w": 0.5}
ELBOWS = {"in": 2.0, "up": 3.0, "w": 0.2}
AIM_CONE = 40.0          # (degrees a key's blade may turn from its written way: solve2's aim)
MID_UP = {"two2"}        # (cuts whose "mid" key comes half way up, from the guard to the wind-up)
AIM_RELEASE = 15.0       # (at the blow: the blade's way there is the cut; with 40 the chop and the sweep struck with it upright)


def strain(w):
    """a wrist's degrees past its comfortable range (COMFORT), and past its limits again"""
    ex = lambda x, r: max(0.0, r[0] - x, x - r[1])
    return max(ex(w[0], COMFORT["flex"]), ex(w[1], COMFORT["dev"]), ex(w[2], COMFORT["twist"])) + R.over(*w)


def elbow_cost(arm_obj, ctx):
    """the elbows' cost as posed now: ELBOWS' cm past its allowance, squared, both sides (as a wrist's degrees count)"""
    return sum(i_ * i_ + u_ * u_ for i_, u_, _ in elbows(arm_obj, ctx).values())


def elbows(arm_obj, ctx):
    """per side (r, l): how far the elbow points in toward her middle and up, off the line from her shoulder to her hand,
    past ELBOWS' allowance (cm, 0 within), and the elbow's bend (degrees, 180 straight)"""
    P = arm_obj.pose.bones; cm = ctx["cm"]; res = {}
    for s in "rl":
        S, E, Hh = P[f"upperarm_{s}"].head, P[f"lowerarm_{s}"].head, P[f"hand_{s}"].head
        i_, u_ = R.elbow_off(E - S, (Hh - S).normalized(), C.OUT[s], cm, ELBOWS)
        res[s] = (max(0.0, i_), max(0.0, u_), math.degrees((S - E).angle(Hh - E)))
    return res


def poles_of(prm):
    """a pose's elbows: (right, left) ways the elbow rather goes, each side's (out, forward, up); the default if not given"""
    return prm[6] if len(prm) > 6 else POLES[0]


def phi_of(prm):
    """the left hand's own turn about the hilt (degrees past the right's): params' eighth"""
    return prm[7] if len(prm) > 7 else 0.0


def with_phi(prm, phi):
    return prm[:6] + (poles_of(prm), phi)


PROTRACT = 26.0     # degrees both clavicles come forward on a hilt held low (her shoulders reach toward it); none for one
                    # raised over her head (from the hilt 5 cm above her neck's base down to 20 cm below it)


HIPS = 0.4          # the share of the body's turn her hips take (C.body)
ELEVATE = 22.0      # degrees both clavicles rise for a hilt over her head (from 6 cm above her neck's base to 22)


def spec2(ctx, prm, edge):
    tw, le, kn, at, blade = prm[:5]; pr, pl = poles_of(prm)
    sp = C.body(ctx, twist=tw, lean=le, knees=kn, hips=HIPS)
    chest = Quaternion(U, math.radians(-tw)) @ F
    pro = PROTRACT * min(max((5.0 - at[2]) / 25.0, 0.0), 1.0); elev = ELEVATE * min(max((at[2] - 6.0) / 16.0, 0.0), 1.0)
    for s in "rl": sp[f"clavicle_{s}"] = [("toward", chest, pro)] + ([("toward", U, elev)] if elev > 0.0 else [])
    sp.update(two_hands(at, blade, edge, D("r", *pr), D("l", *pl), phi_of(prm))); return sp


# Her arms outside her body. The poses' hand places were written against her reach alone, and the user saw the arms
# inside her body: measured, every frame of the three cuts had a forearm or a hand 4 to 10 cm inside her torso (the hilt
# held at her breastbone, her chest further forward than the hands). Each key and each frame is now measured against her
# torso as the pose deforms it (the faces whose vertices follow the pelvis and spine bones) and the hilt moved out until
# the bone lines of both forearms and hands are CLEAR cm outside it (the bone runs through the middle of the forearm).
TORSO = ("pelvis", "spine_01", "spine_02", "spine_03", "spine_04", "spine_05")
BODY_EXTRA = ("clavicle_r", "clavicle_l", "neck_01")   # (also kept clear of: an arm crossing her upper chest or her neck)
CLEAR = {"upper": 4.0, "fore": 4.0, "hand": 3.0}


def body_skin(arm_obj, o, p_arm):
    """a skin point (armature space, rest) that is her body, not what hangs off it: the Warlock's cape is skinned to her
    spine and collarbones and counted as her chest and back (her arms were "inside" it beside her shoulders); it lies
    more than BODY_BACK cm behind her neck's line or BODY_SIDE cm out to a side"""
    B = arm_obj.data.bones; cm = R.model_height(bpy.context.scene) / 170.0; r = p_arm - B["neck_01"].head_local
    # (nor the shoulder's cap, SHOULDER_CAP cm round each shoulder joint: it moves with the arm, and the Warlock's
    # shoulder armour, skinned to her collarbones, made every raised arm "inside" her)
    if any((p_arm - B[f"upperarm_{s}"].head_local).length / cm < SHOULDER_CAP for s in "rl"): return False
    return r.dot(F) / cm > -BODY_BACK and abs(r.dot(C.OUT["r"])) / cm < BODY_SIDE


BODY_BACK, BODY_SIDE, SHOULDER_CAP = 14.0, 16.0, 10.0


def torso_context(arm_obj, scene, ctx):
    """her torso's faces (those whose vertices each follow a TORSO bone most), per mesh, for clearance()"""
    parts = []
    for o in scene.objects:
        if o.type != 'MESH' or not o.vertex_groups: continue
        names = {g.index: g.name for g in o.vertex_groups}; m_ = arm_obj.matrix_world.inverted() @ o.matrix_world
        keep = [v.index for v in o.data.vertices if v.groups and names.get(max(v.groups, key=lambda g: g.weight).group) in TORSO + BODY_EXTRA
                and body_skin(arm_obj, o, m_ @ v.co)]
        pos = {vi: i for i, vi in enumerate(keep)}
        polys = [[pos[v] for v in p.vertices] for p in o.data.polygons if all(v in pos for v in p.vertices)]
        if keep and polys: parts.append((o, keep, polys))
    ctx["torso"] = parts
    # (the same skin with her collarbones and neck, as points with their outward ways in their bones' rest spaces, for
    # rogue_clips.solve_arm to keep each elbow's whole arm out of her: every 6th vertex)
    import numpy as np
    Bn = arm_obj.data.bones; inv = arm_obj.matrix_world.inverted(); per = {}
    for o in scene.objects:
        if o.type != 'MESH' or not o.vertex_groups: continue
        names = {g.index: g.name for g in o.vertex_groups}; m = inv @ o.matrix_world; m3 = m.to_3x3()
        for v in (o.data.vertices[i] for i in range(0, len(o.data.vertices), 6)):
            if not v.groups: continue
            b = names.get(max(v.groups, key=lambda g: g.weight).group)
            if b not in TORSO + BODY_EXTRA or not body_skin(arm_obj, o, m @ v.co): continue
            Li = Bn[b].matrix_local.inverted()
            per.setdefault(b, ([], []))[0].append(tuple(Li @ (m @ v.co))); per[b][1].append(tuple((Li.to_3x3() @ (m3 @ v.normal)).normalized()))
    ctx["torso_pts"] = [(b, np.array(p), np.array(n)) for b, (p, n) in per.items()]
    # (her head, a ball: the face's vertices (those that follow the head bone, in front of it and below its top: her
    # hair hangs behind and beside it) give its size; a raised arm's elbow went behind it, the arm through it)
    B = arm_obj.data.bones; hz = B["head"].head_local; pts = []
    for o in scene.objects:
        if o.type != 'MESH' or not o.vertex_groups: continue
        names = {g.index: g.name for g in o.vertex_groups}; m = arm_obj.matrix_world.inverted() @ o.matrix_world
        pts += [m @ v.co for v in o.data.vertices if v.groups and names.get(max(v.groups, key=lambda g: g.weight).group) == "head"]
    top = max(p.z for p in pts); front = max((p - hz).dot(F) for p in pts if p.z > hz.z)
    ctx["head_ball"] = (hz + U * (top - hz.z) * 0.45 + F * front * 0.15, max((top - hz.z) * 0.5, front * 0.8))


def clearance(arm_obj, ctx):
    """how far the arm point nearest her torso falls short of its CLEAR (cm; 0 or less: clear), how far outside the torso
    that point is (cm, negative: inside), and the torso's outward way there (armature space)"""
    bpy.context.view_layer.update()
    inv = arm_obj.matrix_world.inverted(); dg = bpy.context.evaluated_depsgraph_get(); verts, polys = [], []
    for o, keep, pl in ctx["torso"]:
        ev = o.evaluated_get(dg); me = ev.to_mesh(); m = inv @ ev.matrix_world; base = len(verts); vs = me.vertices
        verts.extend(m @ vs[vi].co for vi in keep); polys.extend([base + i for i in p] for p in pl)
        ev.to_mesh_clear()
    bvh = BVHTree.FromPolygons(verts, polys); P = arm_obj.pose.bones; cm = ctx["cm"]; worst = None
    if "head_ball" in ctx:
        # (her head: the arms CLEAR outside its ball, which turns with her neck)
        c0, r0 = ctx["head_ball"]; Bh = arm_obj.data.bones["head"]
        c = P["head"].matrix @ (Bh.matrix_local.inverted() @ c0)
        for s in "rl":
            u, a, b = P[f"upperarm_{s}"].head, P[f"lowerarm_{s}"].head, P[f"hand_{s}"].head
            for p in [u.lerp(a, 0.75), a] + [a.lerp(b, t) for t in (0.35, 0.7, 1.0)]:
                d = ((p - c).length - r0) / cm; short = CLEAR["fore"] - d; n = (p - c).normalized()
                if worst is None or short > worst[0]: worst = (short, d, n)
    # (both arms, the upper arm and elbow too: this was measured for the left forearm and hand only, the right arm and the
    # upper arms never, while the upper arms went through her chest)
    for s in "rl":
        u, a, b = P[f"upperarm_{s}"].head, P[f"lowerarm_{s}"].head, P[f"hand_{s}"].head
        palm = b + P[f"hand_{s}"].matrix.to_quaternion() @ ctx["arms"][s]["palm_pt"]
        for kind, p in [("upper", u.lerp(a, 0.75)), ("fore", a)] + [("fore", a.lerp(b, t)) for t in (0.35, 0.55, 0.75, 1.0)] + [("hand", palm)]:
            loc, nrm, _, dist = bvh.find_nearest(p)
            if loc is None: continue
            d = (p - loc).dot(nrm) / cm
            # (inside only where her torso is round the point: the nearest face's side alone called points far above
            # the torso's open neck "inside", 11 to 19 cm from any of its vertices, and refused every hilt over her head)
            if d < 0.0 and not surrounded(bvh, p): d = dist / cm
            short = CLEAR[kind] - d
            if worst is None or short > worst[0]: worst = (short, d, nrm.copy())
    return worst or (-99.0, 99.0, F.copy())


def seg_gap(a0, a1, b0, b1):
    """the least distance between two segments (sampled finely: the arms' bones are short)"""
    best = 1e9
    for i in range(9):
        p = a0.lerp(a1, i / 8.0); d = b1 - b0; t = max(0.0, min(1.0, (p - b0).dot(d) / max(d.length_squared, 1e-12)))
        best = min(best, (p - (b0 + d * t)).length)
    for i in range(9):
        p = b0.lerp(b1, i / 8.0); d = a1 - a0; t = max(0.0, min(1.0, (p - a0).dot(d) / max(d.length_squared, 1e-12)))
        best = min(best, (p - (a0 + d * t)).length)
    return best


def forearms_gap(arm_obj, ctx):
    """cm between her two forearms (elbow to wrist, the bone lines): under GAP_MIN they cross or lie on each other"""
    P = arm_obj.pose.bones
    return seg_gap(P["lowerarm_r"].head, P["hand_r"].head, P["lowerarm_l"].head, P["hand_l"].head) / ctx["cm"]


def hand_vertices(scene):
    """the body mesh and, per side, the vertices that follow her hand and finger bones most"""
    body = next(o for o in scene.objects if o.type == 'MESH' and o.vertex_groups)
    gi = {g.index: g.name for g in body.vertex_groups}; out = {"r": [], "l": []}
    for v in body.data.vertices:
        if not v.groups: continue
        n = gi.get(max(v.groups, key=lambda g: g.weight).group, "")
        if n[-2:] in ("_r", "_l") and (n.startswith("hand") or n.split("_")[0] in C.FINGERS + ("thumb",)): out[n[-1]].append(v.index)
    return body, out


def fist_span(arm_obj, scene, ctx):
    """cm the two fists take on the hilt, palm point to palm point, with FIST_GAP between them: the right fist's reach
    toward the pommel from its palm point and the left's toward the guard from its own, measured on the mesh in the guard"""
    R.apply(arm_obj, spec2(ctx, guard2(), guard2()[5]), ctx); del ctx["wrists"][-2:]
    body, hv = hand_vertices(scene); dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); me = ev.to_mesh()
    inv = arm_obj.matrix_world.inverted() @ ev.matrix_world; P = arm_obj.pose.bones; cm = ctx["cm"]
    qr, ql = P["hand_r"].matrix.to_quaternion(), P["hand_l"].matrix.to_quaternion()
    blade = (qr @ ctx["arms"]["r"]["local"]["front"]).normalized()
    pr = P["hand_r"].head + qr @ ctx["arms"]["r"]["palm_pt"]; pl = P["hand_l"].head + ql @ ctx["arms"]["l"]["palm_pt"]
    below_r = -min((inv @ me.vertices[i].co - pr).dot(blade) for i in hv["r"]) / cm
    above_l = max((inv @ me.vertices[i].co - pl).dot(blade) for i in hv["l"]) / cm
    ev.to_mesh_clear()
    return below_r + above_l + FIST_GAP, below_r, above_l


def surrounded(bvh, p):
    """the torso on both sides of p along at least two of three ways (her forward, her right, up): p is inside it"""
    n = 0
    for ax in (F, C.OUT["r"], U):
        if bvh.ray_cast(p, ax)[0] is not None and bvh.ray_cast(p, -ax)[0] is not None: n += 1
    return n >= 2


def hilt_miss(arm_obj, ctx, at):
    """cm the worse hand is from its place (the right from `at`, the left palm from its place on the hilt): over her reach"""
    Pb = arm_obj.pose.bones; cm = ctx["cm"]
    goal = Pb["neck_01"].head + (C.OUT["r"] * at[0] + F * at[1] + U * at[2]) * cm
    Ar = ctx["arms"]["r"]; qr = Pb["hand_r"].matrix.to_quaternion()
    gl = Pb["hand_r"].head + qr @ Ar["palm_pt"] + (qr @ Ar["local"]["front"]) * (-LEFT_ON_HILT * cm)
    pl = Pb["hand_l"].head + Pb["hand_l"].matrix.to_quaternion() @ ctx["arms"]["l"]["palm_pt"]
    return max((Pb["hand_r"].head - goal).length, (pl - gl).length) / cm


def clear_pose(arm_obj, ctx, prm, edge, tries=16):
    """the pose with its hilt moved out until clearance() is met (or `tries` moves); returns the params, the shortfall.
    The hilt goes out along the torso's way at the point nearest her arms, level; where that leaves her reach (her arms
    are short: 34 cm to the wrist), it goes down and a little out instead, toward her waist, where her body is shallower"""
    def put(p):
        n0 = len(ctx.get("wrists", [])); R.apply(arm_obj, spec2(ctx, p, edge), ctx); del ctx["wrists"][n0:]
        return clearance(arm_obj, ctx) + (hilt_miss(arm_obj, ctx, p[3]),)
    short, d, nrm, miss = put(prm); miss0 = miss; ok = None; down = False
    for _ in range(tries):
        if miss > miss0 + 1.0:                          # (out of her reach: back to the last place she reached)
            if ok is None or down:
                if ok is not None: prm = ok; short, d, nrm, miss = put(prm)
                break
            prm, down = ok, True; short, d, nrm, miss = put(prm)
        if short <= 0.0: break
        ok = prm
        h = Vector((nrm.x, nrm.y, 0.0)); h = h.normalized() if h.length > 0.2 else F.copy()
        step = (h * (short + 0.5) * 0.8) if not down else (h * 0.35 - U).normalized() * (short + 0.5) * 0.8
        at = prm[3]; prm = prm[:3] + ((at[0] + step.dot(C.OUT["r"]), at[1] + step.dot(F), at[2] + step.dot(U)),) + prm[4:]
        short, d, nrm, miss = put(prm)
    return prm, short


def search_place(arm_obj, ctx, prm, edge):
    """a key pose's hilt moved to the nearest place (a grid round it: lower, further out, to either side) where both hands
    still reach it and her arms clear her body; none: the place that clears most. Returns the params"""
    def put(at, poles):
        p = prm[:3] + (at,) + prm[4:6] + (poles,) + prm[7:]
        n0 = len(ctx.get("wrists", [])); R.apply(arm_obj, spec2(ctx, p, edge), ctx); ws = ctx["wrists"][n0:]; del ctx["wrists"][n0:]
        # ("wrist": the worst wrist's degrees past its comfortable range, and the elbows' cm past theirs)
        return clearance(arm_obj, ctx)[0], hilt_miss(arm_obj, ctx, at), max([strain(w) for _, w in ws] or [0.0]) + math.sqrt(elbow_cost(arm_obj, ctx)), forearms_gap(arm_obj, ctx)
    at0 = Vector(prm[3]); short0, miss0, wr0, gap0 = put(tuple(at0), poles_of(prm))
    print("W5SEARCH at (%.0f, %.0f, %.0f): short of CLEAR %.1f cm, miss %.1f cm, wrist %.0f deg past, forearms %.1f cm apart" % (*prm[3], short0, miss0, wr0, gap0))
    if short0 <= 0.0 and gap0 >= GAP_MIN and wr0 <= 8.0: return prm
    best = None
    for pi, poles in enumerate(POLES):
        for dz in (4, 0, -4, -8, -12):
            for dy in (-4, 0, 4, 8):
                for dx in (-6, 0, 6):
                    at = at0 + Vector((dx, dy, dz)); short, miss, wr, gap = put(tuple(at), poles)
                    if miss > max(miss0, 0.5) + 1.0: continue
                    # (good: her arms clear her body and each other: the nearest such place, a wrist past its limits and
                    # other elbows counted as distance; none good yet: the one nearest to it)
                    bad = max(short, 0.0) + max(GAP_MIN - gap, 0.0)
                    key = (0, (at - at0).length + 0.4 * wr + 2.0 * (pi > 0)) if bad <= 0.0 else (1, bad + 0.05 * wr)
                    if best is None or key < best[0]: best = (key, at, poles)
    return prm if best is None else prm[:3] + (tuple(best[1]),) + prm[4:6] + (best[2],) + prm[7:]


def solve2(arm_obj, ctx, prm, rolls=16, cone=AIM_CONE):
    """a two-handed key pose: the blade exactly its way, turned about it the way that leaves both wrists nearest their
    limits, the hilt moved where her arms clear her body (search_place); returns the pose (each bone's matrix_basis), the
    edge chosen, the spec, the params as moved"""
    def roll(prm):
        b = prm[4].normalized(); hint = prm[5]; h = (hint - b * hint.dot(b)).normalized(); best = None
        for k in range(rolls):
            e = Quaternion(b, math.radians(360.0 * k / rolls)) @ h
            sp = spec2(ctx, prm, e)
            n0 = len(ctx.get("wrists", [])); R.apply(arm_obj, sp, ctx); ws = ctx["wrists"][n0:]; del ctx["wrists"][n0:]
            cost = sum(strain(w) ** 2 for _, w in ws) + elbow_cost(arm_obj, ctx) + 0.002 * math.degrees(e.angle(h)) ** 2 + GAP_W * max(0.0, GAP_MIN - forearms_gap(arm_obj, ctx)) ** 2
            if best is None or cost < best[0]: best = (cost, e)
        return best[1]
    def turn_left(prm, e):
        # (the left hand's own turn about the hilt: the least strain on its wrist with the forearms apart)
        best = None
        for ph in range(-60, 61, 15):            # (more than 60 degrees from the right's, the grip itself looks twisted)
            p = with_phi(prm, float(ph))
            n0 = len(ctx.get("wrists", [])); R.apply(arm_obj, spec2(ctx, p, e), ctx); ws = ctx["wrists"][n0:]; del ctx["wrists"][n0:]
            c = sum(strain(w) ** 2 for s_, w in ws if s_ == "l") + elbow_cost(arm_obj, ctx) + GAP_W * max(0.0, GAP_MIN - forearms_gap(arm_obj, ctx)) ** 2 + 0.004 * ph * ph
            if best is None or c < best[0]: best = (c, p)
        return best[1]
    def aim(prm):
        # (the key's blade way is what the cut means; within AIM_CONE of it, the way her wrists and elbows take most
        # easily: a fist holds the grip across the palm, so a blade written along the forearms (down and ahead from low
        # hands) bent the wrists 35 to 50 degrees aside; turned, the hands below and the blade rising out of them)
        b0 = prm[4].normalized(); side_ = b0.cross(U); side_ = side_.normalized() if side_.length > 1e-3 else C.OUT["r"].copy()
        up_ = side_.cross(b0).normalized(); best = None
        for pa in (-cone, -cone / 2, 0.0, cone / 2, cone):
            for ya in (-cone, -cone / 2, 0.0, cone / 2, cone):
                b = (Quaternion(U, math.radians(ya)) @ Quaternion(side_, math.radians(pa)) @ b0).normalized()
                p = prm[:4] + (b,) + prm[5:]; e = roll(p)
                n0 = len(ctx.get("wrists", [])); R.apply(arm_obj, spec2(ctx, p, e), ctx); ws = ctx["wrists"][n0:]; del ctx["wrists"][n0:]
                c = (sum(strain(w) ** 2 for _, w in ws) + elbow_cost(arm_obj, ctx) + GAP_W * max(0.0, GAP_MIN - forearms_gap(arm_obj, ctx)) ** 2
                     + 10.0 * max(0.0, clearance(arm_obj, ctx)[0]) ** 2 + 0.08 * math.degrees(b.angle(b0)) ** 2)
                if best is None or c < best[0]: best = (c, p)
        return best[1]
    prm = aim(prm)
    e = roll(prm); prm = turn_left(prm, e); prm = search_place(arm_obj, ctx, prm, e); e = roll(prm); prm = turn_left(prm, e)
    prm, _ = clear_pose(arm_obj, ctx, prm, e)
    return R.apply(arm_obj, spec2(ctx, prm, e), ctx), e, spec2(ctx, prm, e), prm


def round_turn(v0, v1, u):
    """a blade's way a share u from v0 to v1 swung round her: its compass way (about her upright axis, the shorter way
    round) and its rise eased apart. The shortest turn from the sweep's wind-up (back past her right hip) to its blow
    (ahead, to her left) went through straight up, 138 degrees in a few frames: the Warlock's left palm came 6 cm off
    the hilt and a wrist 37 degrees past"""
    x0, y0, z0 = v0.dot(C.OUT["r"]), v0.dot(F), v0.dot(U); x1, y1, z1 = v1.dot(C.OUT["r"]), v1.dot(F), v1.dot(U)
    a0, a1 = math.atan2(y0, x0), math.atan2(y1, x1); d = (a1 - a0 + math.pi) % (2.0 * math.pi) - math.pi
    e0, e1 = math.asin(max(-1.0, min(1.0, z0 / v0.length))), math.asin(max(-1.0, min(1.0, z1 / v1.length)))
    a = a0 + d * u; e = e0 + (e1 - e0) * u
    return (C.OUT["r"] * (math.cos(e) * math.cos(a)) + F * (math.cos(e) * math.sin(a)) + U * math.sin(e)).normalized()


def swing(arm_obj, ctx, keys, round_blade=False):
    """a two-handed clip solved frame by frame (keys: [(seconds, params, edge)]; round_blade: the blade swung round her,
    round_turn, not the shortest way): between the keys the body, the right hand's
    place, the blade and its edge are eased from one to the next and both hands are put on the hilt again in every frame
    (eased local turns alone let the left hand drift 8 to 10 cm off the hilt half way through a cut). Where an eased
    frame brings her arms into her body the hilt is moved out (clear_pose), the moves smoothed over neighbouring frames so
    the swing does not jerk, and the frame measured again; returns the frames and the worst frame's shortfall (cm)"""
    n = int(round(keys[-1][0] * FPS)); base = []; carry = None
    for i in range(n + 1):
        t = i / FPS
        j = max(k for k in range(len(keys) - 1) if keys[k][0] <= t + 1e-6) if t < keys[-1][0] else len(keys) - 2
        (t0, a, ea), (t1, b, eb) = keys[j], keys[j + 1]
        u = C.ease(min(max((t - t0) / (t1 - t0), 0.0), 1.0))
        lerp = lambda x, y: x + (y - x) * u
        turn = lambda v0, v1: Quaternion((1.0, 0.0, 0.0, 0.0)).slerp(v0.normalized().rotation_difference(v1.normalized()), u) @ v0.normalized()
        # (round her only from the wind-up on: from the guard to the wind-up the blade rises up and back, and swung round
        # her right side there the Warlock's wrists went 28 to 53 degrees past their range)
        blade = round_turn(a[4].normalized(), b[4].normalized(), u) if round_blade and j >= 1 else turn(a[4], b[4]); edge = turn(ea, eb)
        # (the edge carried from the frame before by the blade's own turn: the edge eased on its own came nearly along a
        # fast-turning blade and its square flipped to the other side, half a turn of the hands from one frame to the next)
        if carry is not None:
            b0, e0 = carry; edge = b0.normalized().rotation_difference(blade.normalized()) @ e0
        edge = (edge - blade * edge.dot(blade)).normalized(); carry = (blade.copy(), edge.copy())
        poles = tuple(tuple(lerp(pa[q], pb[q]) for q in range(3)) for pa, pb in zip(poles_of(a), poles_of(b)))
        base.append(((lerp(a[0], b[0]), lerp(a[1], b[1]), lerp(a[2], b[2]), tuple(lerp(a[3][q], b[3][q]) for q in range(3)), blade, edge, poles,
                      lerp(phi_of(a), phi_of(b))), edge))
    # (the blade's turn about its length eased between two keys bent the wrists 70 to 76 degrees past their limits in
    # some frames: each frame's turn is one of 24 round the blade, chosen over the whole clip at once (a shortest path)
    # for the least strain on both wrists with the least change from frame to frame)
    OFFS = [15.0 * k for k in range(-6, 7)]          # (no more than 90 degrees from the carried edge: past it the hands turned half round the grip)
    # (a key frame rather keeps the turn solve2 chose for it, where her arms cleared her body: carried edges alone left the
    # held follow-through 15 to 45 degrees from it, its arms 3 to 5 cm into her and a wrist 26 degrees past)
    key_edge = {int(round(k[0] * FPS)): k[2] for k in keys}
    cost = []
    for fi, (prm, edge) in enumerate(base):
        row = []
        for deg in OFFS:
            e = Quaternion(prm[4].normalized(), math.radians(deg)) @ edge
            n0 = len(ctx.get("wrists", [])); R.apply(arm_obj, spec2(ctx, prm, e), ctx); ws = ctx["wrists"][n0:]; del ctx["wrists"][n0:]
            # (the turn also decides from which side each forearm comes to the hilt: forearms closer than GAP_MIN pay)
            ke = key_edge.get(fi)
            anchor = 0.2 * math.degrees(e.angle((ke - prm[4].normalized() * ke.dot(prm[4].normalized())).normalized())) ** 2 if ke is not None else 0.0
            row.append(sum(strain(w) ** 2 for _, w in ws) + elbow_cost(arm_obj, ctx) + 0.01 * deg * deg + GAP_W * max(0.0, GAP_MIN - forearms_gap(arm_obj, ctx)) ** 2 + anchor)
        cost.append(row)
    # (no more than 30 degrees from one frame to the next: the forearms' gap bought a 90-degree turn of both hands in a frame)
    step = lambda a, b: 0.15 * min(abs(a - b), 360.0 - abs(a - b)) ** 2 + (1e6 if min(abs(a - b), 360.0 - abs(a - b)) > 30.0 else 0.0)
    acc = [cost[0][:]]; back = []
    for i in range(1, len(cost)):
        prev = acc[-1]; row, bk = [], []
        for j, dj in enumerate(OFFS):
            k = min(range(len(OFFS)), key=lambda k: prev[k] + step(OFFS[k], dj)); bk.append(k); row.append(prev[k] + step(OFFS[k], dj) + cost[i][j])
        acc.append(row); back.append(bk)
    j = min(range(len(OFFS)), key=lambda k: acc[-1][k]); path = [j]
    for bk in reversed(back): j = bk[j]; path.append(j)
    path.reverse(); ctx["swing_rolls"] = [OFFS[j] for j in path]
    base = [(prm[:5] + (e,) + prm[6:], e) for (prm, edge), j in zip(base, path)
            for e in [Quaternion(prm[4].normalized(), math.radians(OFFS[j])) @ edge]]
    # (then the left hand's own turn about the hilt, frame by frame the same way: its wrist and the forearms apart, eased)
    PHIS = [15.0 * k for k in range(-5, 6)]; pc = []
    for prm, edge in base:
        row = []
        for ph in PHIS:
            p = with_phi(prm, phi_of(prm) + ph)
            if abs(phi_of(p)) > 60.0: row.append(1e6); continue
            n0 = len(ctx.get("wrists", [])); R.apply(arm_obj, spec2(ctx, p, edge), ctx); ws = ctx["wrists"][n0:]; del ctx["wrists"][n0:]
            row.append(sum(strain(w) ** 2 for s_, w in ws if s_ == "l") + elbow_cost(arm_obj, ctx) + GAP_W * max(0.0, GAP_MIN - forearms_gap(arm_obj, ctx)) ** 2 + 0.004 * phi_of(p) ** 2)
        pc.append(row)
    acc = [pc[0][:]]; back = []
    for i in range(1, len(pc)):
        prev = acc[-1]; row, bk = [], []
        for j, dj in enumerate(PHIS):
            k = min(range(len(PHIS)), key=lambda k: prev[k] + 0.1 * (PHIS[k] - dj) ** 2); bk.append(k); row.append(prev[k] + 0.1 * (PHIS[k] - dj) ** 2 + pc[i][j])
        acc.append(row); back.append(bk)
    j = min(range(len(PHIS)), key=lambda k: acc[-1][k]); pth = [j]
    for bk in reversed(back): j = bk[j]; pth.append(j)
    pth.reverse()
    base = [(with_phi(prm, phi_of(prm) + PHIS[j]), edge) for (prm, edge), j in zip(base, pth)]
    ctx["swing_phis"] = [phi_of(prm) for prm, _ in base]
    moves = []
    for prm, edge in base:
        moved, _ = clear_pose(arm_obj, ctx, prm, edge)
        moves.append(Vector(moved[3]) - Vector(prm[3]))
    # (each frame's move: the largest of its neighbours' within 3 frames, then averaged over 5: no frame moves less than it needs)
    wide = [max(moves[max(0, i - 3):i + 4], key=lambda v: v.length) for i in range(len(moves))]
    smooth = [sum(wide[max(0, i - 2):i + 3], Vector()) / len(wide[max(0, i - 2):i + 3]) for i in range(len(wide))]
    # (the key frames keep the places solve2 found for them, and no frame is moved more than 10 cm: one frame's big move
    # spread over its neighbours carried the diagonal cut's wind-up 35 cm, to where its right wrist bent 65 degrees past)
    keyf = {int(round(k[0] * FPS)) for k in keys}
    smooth = [Vector() if i in keyf else (v if v.length <= 10.0 else v.normalized() * 10.0) for i, v in enumerate(smooth)]
    frames, worst = [], -99.0; ctx["swing_keyoff"] = []; ctx["swing_capped"] = []; ctx["swing_elbows"] = []; ctx["swing_wrists"] = []; ctx["swing_gaps"] = []; ctx["swing_short"] = []; ctx["swing_refits"] = []; ctx.pop("prev_arm", None)
    ctx["roll_scale"] = 0.02          # (the roll's limit is for the Rogue's cape: here the arm's last frame counts first)
    ctx["cont_w"] = 0.025             # (a degree of the upper arm's turn from its last frame, squared: at 0.01 it still swung 60 to 110 degrees in a frame; at 0.05 it held the sweep's forearms crossed, 2 cm apart, through its follow-through)
    # (from the blow on to the follow-through: the arms led, a share each frame, to the follow-through key's own upper
    # arms. The swing came on with its elbows as the frame before had them, which for the overhead chop was not where the
    # key cleared her body (wrists 20 to 28 degrees past through the hold against the key's 8); each frame is still
    # solved whole, both hands on the hilt)
    hold = int(round(keys[-3][0] * FPS)) if len(keys) > 3 and keys[-2][1] is keys[-1][1] else None
    hold_arms = ctx.get("key_arms", {}).get(id(keys[-1][1])) if hold is not None else None
    for i, ((prm, edge), mv) in enumerate(zip(base, smooth)):
        if hold_arms and i > hold and "prev_arm" in ctx:
            ctx["prev_arm"] = {s_: ctx["prev_arm"][s_].slerp(hold_arms[s_], 0.35) for s_ in "rl"}
        # (the smoothed move held to where both hands still reach the hilt: moves spread over their neighbours carried
        # the hilt past her reach, the Warlock's left palm 3 to 4 cm off it)
        def miss_at(p):
            n0 = len(ctx.get("wrists", [])); R.apply(arm_obj, spec2(ctx, p, edge), ctx); del ctx["wrists"][n0:]
            return hilt_miss(arm_obj, ctx, p[3])
        put = lambda f_: prm[:3] + (tuple(Vector(prm[3]) + mv * f_),) + prm[4:]
        f_ = 1.0
        if mv.length > 0.5:
            m0 = miss_at(put(0.0))
            while f_ > 0.0 and miss_at(put(f_)) > max(m0, 0.5) + 1.0: f_ = round(f_ - 0.25, 2)
            ctx.setdefault("swing_capped", []).append((i, f_)) if f_ < 1.0 else None
        prm = put(f_)
        # (a key frame keeps its key's place: moved out again here, the Warlock's raised guard was played 21 cm from where
        # its key was solved, a pose nobody solved)
        if i in keyf:
            n0_ = len(ctx.get("wrists", [])); R.apply(arm_obj, spec2(ctx, prm, edge), ctx); del ctx["wrists"][n0_:]; short = clearance(arm_obj, ctx)[0]
        else: prm, short = clear_pose(arm_obj, ctx, prm, edge)
        worst = max(worst, short); ctx.setdefault("swing_short", []).append((i, short, tuple(prm[3])))
        n0 = len(ctx.get("wrists", []))
        frames.append(R.apply(arm_obj, spec2(ctx, prm, edge), ctx))
        # (an upper arm that still turned more than 45 degrees from the frame before (its elbow popped round): this frame
        # solved again with the last frame weighing far more)
        if "prev_arm" in ctx:
            turned = lambda: max(min(x, 360.0 - x) for x in (math.degrees(arm_obj.pose.bones[f"upperarm_{s_}"].matrix.to_quaternion().rotation_difference(ctx["prev_arm"][s_]).angle) for s_ in "rl"))
            # (from the blow on, led to the follow-through, the arms move little from frame to frame: a 41-degree turn there
            # was a one-frame pop that crossed the Warlock's forearms, 1.7 cm apart, in her held chop)
            if turned() > (30.0 if hold_arms and i > hold else 45.0):
                w0 = ctx["cont_w"]; ctx["cont_w"] = 0.2; del ctx["wrists"][n0:]
                frames[-1] = R.apply(arm_obj, spec2(ctx, prm, edge), ctx); ctx["cont_w"] = w0
                ctx.setdefault("swing_refits", []).append((i, round(turned(), 0)))
        # (the next frame's arms rather as these: rogue_clips.solve_arm)
        ctx["prev_arm"] = {s_: arm_obj.pose.bones[f"upperarm_{s_}"].matrix.to_quaternion() for s_ in "rl"}
        ctx["swing_wrists"].append((i, max([strain(w) for _, w in ctx["wrists"][n0:]] or [0.0])))
        eb_ = elbows(arm_obj, ctx); ctx.setdefault("swing_elbows", []).append((i, max(eb_["r"][0], eb_["l"][0]), max(eb_["r"][1], eb_["l"][1])))
        if i in key_edge:             # (a key frame against its key: the edge's turn, the left hand's turn, the hilt's place)
            kp = next(k[1] for k in keys if int(round(k[0] * FPS)) == i); ke = key_edge[i]; b_ = prm[4].normalized()
            ke = (ke - b_ * ke.dot(b_)).normalized()
            ctx.setdefault("swing_keyoff", []).append("%d: edge %.0f deg, left turn %.0f deg, hilt %.1f cm" % (i, math.degrees(edge.angle(ke)), phi_of(prm) - phi_of(kp), (Vector(prm[3]) - Vector(kp[3])).length))
        ctx.setdefault("swing_gaps", []).append((i, forearms_gap(arm_obj, ctx)))
    ctx.pop("prev_arm", None); ctx.pop("roll_scale", None); ctx.pop("cont_w", None)
    return frames, worst


# (the bow hand out at the target, cm from her neck; the crossbow's right hand on the stock (rogue_clips.XB_HAND is the
# Rogue's). Set for the Warrior's and the Warlock's arms as tripo_proportions lengthened them: at the places written for
# their old arms, 34 cm to the wrist, the bow wrist went 28 degrees past its limits; at the new place, none. The crossbow's
# right wrist goes 9 to 17 degrees past (0 to 5 on the old arms) wherever the hand was tried: the Rogue's place is kept)
BOW_LEFT = (-4, 58, 0)      # (her bow arm straight: the stance turns her shoulders, bringing the left one forward)
XB_HAND_W5 = None


def bow_pose(ctx, k):
    """the bow: 'rest' low in the left hand; 'raise' at the target, the right hand at the string; 'draw' to her cheek;
    'loose' the right hand flown back a little, open"""
    if k == "rest":
        sp = C.body(ctx, twist=0, lean=0, knees=3)
        sp.update(R.reach("l", (-14, 6, -30), D("l", 0.8, -0.2, -0.5), {"axis": D("l", 0.1, 0.7, -0.7)}))
        sp.update(DC.fist("l"))
        sp.update(C.arm("r", D("r", 0.21, 0.05, -1), D("r", 0.12, 0.30, -1), D("r", 0.05, 0.36, -1), curl=16, thumb=8))
        return sp
    sp = C.body(ctx, twist=55, lean=2, knees=8, look=0.95)
    sp.update(R.reach("l", BOW_LEFT, D("l", 0.6, 0.0, -0.8), None, {"front": F, "up": U}))
    sp.update(DC.fist("l"))
    hand_r = {"raise": (2, 14, -3), "draw": (3, 4, 3), "loose": (6, -2, 4)}[k]
    sp.update(R.reach("r", hand_r, D("r", 0.6, -0.6, 0.3), {"axis": D("r", -0.25, 1.0, 0.0), "palm": D("r", -1.0, 0.0, 0.0)}))
    curl = {"raise": 35.0, "draw": 48.0, "loose": 10.0}[k]
    for fn in C.FINGERS:
        for kk, w in (("01", 0.7), ("02", 1.0), ("03", 0.8)): sp[f"{fn}_{kk}_r"] = [("curl", curl * w)]
    return sp


def make_clips(arm_obj, scene, clips):
    want = [w.strip() for w in os.environ.get("W5_CLIPS", "TwoHand,Bow,Shoot").split(",") if w.strip()]
    ctx = C.context(arm_obj); DC.add_thumb_op(ctx, arm_obj); ctx["cm"] = R.model_height(scene) / 170.0; R.arm_context(ctx, arm_obj)
    frames(ctx, arm_obj)
    report = []
    def P(spec, label="?"):
        n0 = len(ctx.get("wrists", []))
        res = R.apply(arm_obj, spec, ctx)
        # (each hand that has a place: how far from it it ended, and how far past a limit its wrist went)
        Pb = arm_obj.pose.bones; miss = []
        for s, op in ((k[-1], v) for k, v in spec.items() if k.startswith("arm_") and v[0] == "reach"):
            at = op[1]
            if at[0] in ("crossbow", "palm_on"):
                Ar = ctx["arms"]["r"]; qr = Pb["hand_r"].matrix.to_quaternion(); fw, uw = qr @ Ar["local"]["front"], qr @ Ar["local"]["up"]
                goal = Pb["hand_r"].head + qr @ Ar["palm_pt"] + (fw * at[1] + uw * at[2] + uw.cross(fw) * at[3]) * ctx["cm"]
            else:
                goal = Pb["neck_01"].head + (C.OUT["r"] * at[0] + F * at[1] + U * at[2]) * ctx["cm"]
            got = Pb[f"hand_{s}"].head + Pb[f"hand_{s}"].matrix.to_quaternion() @ ctx["arms"][s]["palm_pt"] if at[0] == "palm_on" else Pb[f"hand_{s}"].head
            miss.append("%s %.1f cm" % (s, (got - goal).length / ctx["cm"]))
        ws = ctx.get("wrists", [])[n0:]
        eb_ = elbows(arm_obj, ctx)
        report.append("W5POSE %-18s wrist past limits %s, past the comfortable range %s | from its place %s | elbows pointing in r %.0f l %.0f, up r %.0f l %.0f cm, bent to r %.0f l %.0f deg" % (
            label, ", ".join("%s %.0f" % (s, R.over(*w)) for s, w in ws) or "-", ", ".join("%s %.0f" % (s, strain(w) - R.over(*w)) for s, w in ws) or "-", ", ".join(miss) or "-",
            eb_["r"][0], eb_["l"][0], eb_["r"][1], eb_["l"][1], eb_["r"][2], eb_["l"][2]))
        return res
    out = {}
    if "TwoHand" in want:
        use(ctx, "sword"); torso_context(arm_obj, scene, ctx)
        # (the upper arm's roll limit is for the Rogue's cape: here it pulled a raised elbow in behind her head)
        ctx["roll_scale_key"] = 0.05
        ctx["wrist_comfort"] = COMFORT; ctx["elbow_rules"] = ELBOWS
        # (the left fist a fist's span below the right on the hilt: measured twice, the second with the first's spacing)
        global LEFT_ON_HILT
        for _ in range(2):
            span, below_r, above_l = fist_span(arm_obj, scene, ctx); LEFT_ON_HILT = round(span, 1)
        report.append("W5POSE fists on the hilt: the right reaches %.1f cm toward the pommel, the left %.1f cm toward the guard: palms %.1f cm apart" % (below_r, above_l, LEFT_ON_HILT))
        def key2(prm, label):
            at0 = prm[3]
            res, e, sp, prm = solve2(arm_obj, ctx, prm, cone=AIM_RELEASE if "release" in label else AIM_CONE)
            P(sp, label)                     # (once more, for the report)
            ctx.setdefault("key_arms", {})[id(prm)] = {s_: arm_obj.pose.bones[f"upperarm_{s_}"].matrix.to_quaternion() for s_ in "rl"}
            short, d, _ = clearance(arm_obj, ctx)
            report.append("W5POSE %-18s hilt moved out (%s) -> (%s) cm, elbows %d; her arms' nearest point %.1f cm outside her torso (short of CLEAR by %.1f); forearms %.1f cm apart"
                          % (label, ", ".join("%.0f" % v for v in at0), ", ".join("%.1f" % v for v in prm[3]), POLES.index(poles_of(prm)), d, max(short, 0.0), forearms_gap(arm_obj, ctx)))
            return prm, e
        def key_score(k):
            # (a solved key's strain: the wrists past their range, the elbows past theirs, her arms short of CLEAR)
            n0 = len(ctx.get("wrists", [])); R.apply(arm_obj, spec2(ctx, k[0], k[1]), ctx); ws = ctx["wrists"][n0:]; del ctx["wrists"][n0:]
            return sum(strain(w) ** 2 for _, w in ws) + elbow_cost(arm_obj, ctx) + 10.0 * max(0.0, clearance(arm_obj, ctx)[0]) ** 2
        g = key2(guard2(), "guard2")
        places = HERO_PLACES.get(hero_name(), {})
        if places: report.append("W5POSE %s's own places: %s" % (hero_name(), "; ".join("%s %s %s" % (a, b, v) for (a, b), v in places.items())))
        for name, fn0, fname in (("W5_TwoHand1", two1, "two1"), ("W5_TwoHand2", two2, "two2"), ("W5_TwoHand3", two3, "two3")):
            fn = lambda k, fn0=fn0, fname=fname: (lambda p: hero_key(p, places[(fname, k)]) if (fname, k) in places else p)(fn0(k))
            tw, tr, tf, te = TIMES[name]
            # (it ends held at its follow-through: swung back to the guard, the blade passed level at her waist and the
            # left hand went 4 cm into her; the game blends from here to her idle, as it did from the guard)
            kw = key2(fn("wind"), name + " wind"); kr = key2(fn("release"), name + " release")
            # (the follow-through solved on from the release, its upper arms rather as there: solved on its own it found
            # its clear place with the left elbow on the other side, 150 degrees round from where the swing brought it;
            # the swing then held the elbow where it came, 1 to 5 cm into her and a wrist 25 degrees past)
            ctx["prev_arm"] = {s_: arm_obj.pose.bones[f"upperarm_{s_}"].matrix.to_quaternion() for s_ in "rl"}; ctx["cont_w"] = 0.025; ctx["roll_scale"] = 0.02
            fo = key2(fn("follow"), name + " follow"); sc_c = key_score(fo)
            for k_ in ("prev_arm", "cont_w", "roll_scale"): ctx.pop(k_, None)
            # (and solved freely: kept on from the blow, the diagonal's held end had the left elbow 9 cm in and the arm in
            # her chest, its free solve clear; the swing leads the arms to it from the blow on. The better of the two)
            fo_f = key2(fn("follow"), name + " follow (free)"); sc_f = key_score(fo_f)
            if sc_f < sc_c - 5.0: fo = fo_f
            report.append("W5POSE %-18s follow-through solved on from the blow %.0f, freely %.0f: %s" % (name, sc_c, sc_f, "free" if fo is fo_f else "on from the blow"))
            ks = [(0.0,) + g, (tw,) + kw, (tr,) + kr, (tf,) + fo, (te,) + fo]
            if fn("mid") is not None:
                # (a key half way: on the way up for the chop (MID_UP: from the guard to the raised guard the blade
                # turned 150 degrees with nothing between), else from the wind-up to the blow (the sweep)
                up = fname in MID_UP; frm = g if up else kw
                ctx["prev_arm"] = dict(ctx.get("key_arms", {}).get(id(frm[0]), {})) or None
                if ctx["prev_arm"] is None: ctx.pop("prev_arm")
                else: ctx["cont_w"] = 0.025; ctx["roll_scale"] = 0.02
                km = key2(fn("mid"), name + " mid")
                for k_ in ("prev_arm", "cont_w", "roll_scale"): ctx.pop(k_, None)
                if up: ks.insert(1, (0.5 * tw,) + km)
                else: ks.insert(2, (0.5 * (tw + tr),) + km)
            out[name], short = swing(arm_obj, ctx, ks, round_blade=(fname == "two3"))      # (the sweep's blade swings round in front of her, not over)
            report.append("W5POSE %-18s her arms against her torso, the worst frame: short of CLEAR (forearm %.1f, hand %.1f cm outside) by %.1f cm"
                          % (name, CLEAR["fore"], CLEAR["hand"], max(short, 0.0)))
            report.append("W5POSE %-18s wrists past their comfortable range (and limits) per frame: %s" % (name, " ".join("%d:%.0f" % iw for iw in ctx["swing_wrists"])))
            report.append("W5POSE %-18s elbows per frame, pointing in / up past the allowance (cm, the worse side): %s" % (name, " ".join("%d:%.0f/%.0f" % e_ for e_ in ctx["swing_elbows"])))
            report.append("W5POSE %-18s forearms apart per frame (cm): %s" % (name, " ".join("%d:%.0f" % ig for ig in ctx["swing_gaps"])))
            report.append("W5POSE %-18s short of CLEAR per frame (cm) at the hilt: %s" % (name, " ".join("%d:%.1f@(%.0f,%.0f,%.0f)" % (i, sh, *a) for i, sh, a in ctx["swing_short"] if sh > 0.0)))
            report.append("W5POSE %-18s the left hand's own turn about the hilt per frame (deg): %s" % (name, " ".join("%d:%.0f" % (i, v) for i, v in enumerate(ctx["swing_phis"]))))
            report.append("W5POSE %-18s the blade's turn about itself per frame (deg from the carried edge): %s" % (name, " ".join("%d:%.0f" % (i, v) for i, v in enumerate(ctx["swing_rolls"]))))
            report.append("W5POSE %-18s key frames off their keys: %s" % (name, "; ".join(ctx["swing_keyoff"])))
            report.append("W5POSE %-18s frames whose move out was cut to keep the hilt in reach (share kept): %s" % (name, " ".join("%d:%.2f" % c_ for c_ in ctx["swing_capped"]) or "none"))
            report.append("W5POSE %-18s frames solved again for an upper arm's turn from the frame before (deg after): %s" % (name, " ".join("%d:%.0f" % r_ for r_ in ctx["swing_refits"]) or "none"))
            # (both hands on the hilt in every frame: the left palm's distance from its place on the hilt, worst frame)
            worst = 0.0
            for fr in out[name]:
                for pb in arm_obj.pose.bones:
                    l_, q_, s_ = fr[pb.name]; pb.location = l_; pb.rotation_quaternion = q_; pb.scale = s_
                bpy.context.view_layer.update()
                Pb = arm_obj.pose.bones; Ar = ctx["arms"]["r"]; qr = Pb["hand_r"].matrix.to_quaternion()
                goal = Pb["hand_r"].head + qr @ Ar["palm_pt"] + (qr @ Ar["local"]["front"]) * (-LEFT_ON_HILT * ctx["cm"])
                got = Pb["hand_l"].head + Pb["hand_l"].matrix.to_quaternion() @ ctx["arms"]["l"]["palm_pt"]
                worst = max(worst, (got - goal).length / ctx["cm"])
            report.append("W5POSE %-18s the left palm off its place on the hilt, worst frame: %.1f cm" % (name, worst))
        for k_ in ("wrist_comfort", "elbow_rules"): ctx.pop(k_, None)
    ctx["wrist_comfort"] = COMFORT
    if XB_HAND_W5: ctx["xb_hand"] = XB_HAND_W5
    if "Bow" in want:
        use(ctx, "bow"); r0 = P(bow_pose(ctx, "rest"), "bow rest"); up = P(bow_pose(ctx, "raise"), "bow raise")
        dr = P(bow_pose(ctx, "draw"), "bow draw"); lo = P(bow_pose(ctx, "loose"), "bow loose")
        out["W5_Bow"] = C.sample([(0.0, r0), (BOW["raise"], up), (BOW["draw"], dr), (BOW["release"], dr), (BOW["loose"], lo), (BOW["hold"], lo), (BOW["end"], r0)])
    if "Shoot" in want:
        use(ctx, "crossbow"); i0 = P(R.idle(ctx), "xbow idle")
        out["W5_Shoot"] = C.sample([(0.0, i0), (R.SHOT["aim"], P(R.shoot(ctx, "aim"), "xbow aim")), (R.RELEASE, P(R.shoot(ctx, "aim"), "xbow aim")),
                                    (R.SHOT["kick"], P(R.shoot(ctx, "kick"), "xbow kick")), (R.SHOT["hold"], P(R.shoot(ctx, "hold"), "xbow hold")), (R.SHOT["end"], i0)])
    for line in report: print(line)
    for pb in arm_obj.pose.bones: pb.matrix_basis.identity()
    worst = max(ctx["wrists"], key=lambda sw: R.over(*sw[1])) if ctx.get("wrists") else ("-", (0, 0, 0))
    print("W5 wrists: %d hands solved, the furthest past a limit %.1f deg (%s: flexion %.0f, deviation %.0f, twist %.0f)"
          % (len(ctx.get("wrists", [])), R.over(*worst[1]), worst[0], *worst[1]))
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) > 1 and os.path.isdir(argv[1]):
        json.dump({"TwoHand": {k: {"wind": v[0], "release": v[1], "follow": v[2], "end": v[3]} for k, v in TIMES.items()},
                   "Bow": {"release": RELEASE["Bow"], "length": BOW["end"]}, "Shoot": {"release": R.RELEASE, "length": R.SHOT["end"]},
                   "tilt": TILT, "left_on_hilt": LEFT_ON_HILT, "crossbow_tilt": R.GRIP_TILT["crossbow"], "clips": sorted(out)},
                  open(os.path.join(argv[1], "w5_times.json"), "w"), indent=1)
    return out


# ---------------------------------------------------------------- preview
def stand_in(arm_obj, ctx, side, local_x, local_y, length, width, colour, back=0.0):
    """a flat bar in a hand as it is posed now: along its local way local_x (its width along local_y), from the palm
    point, `back` cm of it behind the palm (made again for every picture, in the armature object's frame)"""
    pb = arm_obj.pose.bones[f"hand_{side}"]; q = pb.matrix.to_quaternion()
    x = (q @ local_x).normalized(); y = (q @ local_y).normalized(); z = x.cross(y)
    p0 = pb.head + q @ ctx["arms"][side]["palm_pt"]
    c = ctx["cm"]; L_, W_, T_ = length * c, width * c, 0.6 * c
    verts = [p0 + x * (a * L_ - back * c) + y * (b * W_ * 0.5) + z * (d * T_ * 0.5) for a in (0, 1) for b in (-1, 1) for d in (-1, 1)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new("si"); me.from_pydata(verts, [], faces); ob = bpy.data.objects.new("si", me); bpy.context.scene.collection.objects.link(ob)
    m = bpy.data.materials.new("si"); m.diffuse_color = colour; me.materials.append(m)
    ob.matrix_world = arm_obj.matrix_world.copy()
    return ob


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
    clips = make_clips(arm_obj, sc, {})
    ctx = C.context(arm_obj); DC.add_thumb_op(ctx, arm_obj); ctx["cm"] = R.model_height(sc) / 170.0; R.arm_context(ctx, arm_obj); frames(ctx, arm_obj)
    L_r, L_l = ctx["arms"]["r"]["local"], ctx["arms"]["l"]["local"]
    print("ARMATURE object matrix", [list(map(lambda v: round(v, 3), r)) for r in arm_obj.matrix_world])
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'MATERIAL'; sc.display.shading.light = 'STUDIO'
    sc.render.resolution_x = 360; sc.render.resolution_y = 460
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.5
    picks = {k: [0] + [round(t * FPS) for t in v[:3]] + [round((v[2] + v[3]) * 0.5 * FPS)] for k, v in TIMES.items()}
    picks.update({"W5_Bow": [0, round(BOW["raise"] * FPS), round(BOW["draw"] * FPS), round(BOW["loose"] * FPS)], "W5_Shoot": [round(R.SHOT["aim"] * FPS)]})
    for name, fis in picks.items():
        if name not in clips: continue
        for fi in fis:
            for pb in arm_obj.pose.bones:
                l, q, s = clips[name][fi][pb.name]; pb.location = l; pb.rotation_quaternion = q; pb.scale = s
            bpy.context.view_layer.update()
            for o in [o for o in sc.objects if o.name.startswith("si")]: bpy.data.objects.remove(o, do_unlink=True)
            if name.startswith("W5_TwoHand"):
                stand_in(arm_obj, ctx, "r", L_r["sword"], L_r["edge"], 105.0, 5.0, (0.1, 0.9, 1.0, 1), back=22.0)
                stand_in(arm_obj, ctx, "l", L_l["sword"], L_l["edge"], 30.0, 2.0, (1.0, 0.2, 0.6, 1), back=4.0)     # (the left hand's own blade way: on the cyan one?)
            elif name == "W5_Bow": stand_in(arm_obj, ctx, "l", L_l["bow_up"], L_l["bow_front"], 150.0, 3.0, (1.0, 0.55, 0.1, 1), back=75.0)
            else: stand_in(arm_obj, ctx, "r", L_r["xb_front"], L_r["xb_up"], 70.0, 8.0, (0.9, 0.8, 0.2, 1), back=31.0)
            bpy.context.view_layer.update()
            for view, ang in (("front", 0), ("side", 90), ("q", 40)):
                a = math.radians(ang); d = Vector((math.sin(a), -math.cos(a), 0.0))
                cam.location = Vector((0, 0, 0.55)) + d * 4.0; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
                sc.render.filepath = f"{prefix}_{name}_{fi:02d}_{view}.png"; bpy.ops.render.render(write_still=True)
    print("DONE", {k: len(v) for k, v in clips.items()})
