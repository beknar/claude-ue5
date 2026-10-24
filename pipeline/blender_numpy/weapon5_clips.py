"""Clips random_dungeonmagic_level5's found weapons need, made on a Tripo hero's own rig (tripo_build.py's clip_maker;
the Warrior, the Warlock and the Rogue have the same 61 bones). Made (the environment's W5_CLIPS picks some: e.g.
"Bow"; all by default):
  W5_TwoHand1  a two-handed sword, both hands on the hilt (the left a hand's breadth below the right): a diagonal cut
               from over her right shoulder down across to her left hip
  W5_TwoHand2  an overhead chop: raised behind her head, brought down in front of her
  W5_TwoHand3  a horizontal sweep from her right to her left
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
sword in the right hand, LEFT_ON_HILT cm toward the pommel). The arrow leaves at RELEASE["Bow"], the bolt at
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
LEFT_ON_HILT = 7.5          # (cm of her 170: Tripo's heroes have short arms, 34 cm from shoulder to wrist, and hands to match)
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


def two_hands(at, blade, edge, pole_r=None, pole_l=None):
    """both hands on the hilt: the right at `at` (cm from the base of her neck: right, forward, up), the blade and its
    edge exactly as given; the left LEFT_ON_HILT cm below it on the hilt, turned the same"""
    b, e = square(blade, edge)
    sp = R.reach("r", at, pole_r or D("r", 0.7, -0.1, -0.7), None, {"front": b, "up": e})
    sp.update(R.reach("l", ("palm_on", -LEFT_ON_HILT, 0.0, 0.0), pole_l or D("l", 0.7, -0.1, -0.7), None, {"front": b, "up": e}))
    sp.update(DC.fist("r")); sp.update(DC.fist("l"))
    return sp


# A two-handed pose: (the body, where the right hand goes, the blade's way, the way its edge should rather lead). The
# hands' places, cm from the base of her neck (right, forward, up), are inside her reach: her shoulders are 9 to 12 cm
# out from it and turn with her twist, her arm is 32 to 35 cm to the wrist. The blade's turn about its own length is
# chosen by solve2: the one that asks least of both wrists (the edge hint only breaks ties).
# (twist, lean, knees, where the right hand goes, the blade's way, the way its edge should rather lead)
def guard2():
    """the two-handed low guard: the hilt at her waist, the blade forward and up"""
    return 8, 2, 7, (2, 16, -20), D("r", 0.05, 0.60, 0.80), D("r", 0.0, 0.8, -0.6)


def two1(k):
    if k == "wind": return 34, -3, 8, (12, -2, 14), D("r", 0.25, -0.55, 0.80), D("r", -0.3, 0.8, -0.4)
    if k == "release": return -20, 9, 13, (-3, 22, -14), D("r", -0.55, 0.75, -0.35), D("r", -0.6, 0.2, -0.8)
    return -36, 7, 11, (-8, 16, -20), D("r", -0.75, -0.15, -0.60), D("r", -0.2, 0.6, -0.5)


def two2(k):
    if k == "wind": return 10, -8, 6, (5, -2, 20), D("r", 0.05, -0.75, 0.60), D("r", 0.0, 0.6, 0.8)
    if k == "release": return -4, 15, 16, (2, 24, -11), D("r", -0.05, 0.85, -0.50), D("r", 0.0, 0.4, -1.0)
    return -6, 12, 14, (3, 18, -20), D("r", -0.05, 0.40, -0.90), D("r", 0.0, -0.9, -0.4)


def two3(k):
    if k == "wind": return 44, -2, 9, (16, 4, -6), D("r", 0.60, -0.75, 0.15), D("r", -0.45, -0.35, 0.0)
    if k == "release": return -14, 6, 12, (-3, 24, -8), D("r", -0.80, 0.60, 0.05), D("r", -0.6, -0.8, 0.0)
    return -44, 5, 10, (-14, 16, -10), D("r", -0.85, 0.30, -0.15), D("r", 0.3, 0.9, 0.0)


POLES = [((0.7, -0.1, -0.7), (0.7, -0.1, -0.7)), ((0.7, -0.1, -0.7), (1.0, 0.0, -0.25)), ((0.7, -0.1, -0.7), (0.85, -0.4, -0.35)),
         ((1.0, 0.0, -0.25), (1.0, 0.0, -0.25)), ((0.7, -0.1, -0.7), (0.6, 0.35, -0.7)), ((1.0, 0.0, -0.25), (0.85, -0.4, -0.35))]


def poles_of(prm):
    """a pose's elbows: (right, left) ways the elbow rather goes, each side's (out, forward, up); the default if not given"""
    return prm[6] if len(prm) > 6 else POLES[0]


PROTRACT = 26.0     # degrees both clavicles come forward on a hilt held low (her shoulders reach toward it); none for one
                    # raised over her head (from the hilt 5 cm above her neck's base down to 20 cm below it)


def spec2(ctx, prm, edge):
    tw, le, kn, at, blade = prm[:5]; pr, pl = poles_of(prm)
    sp = C.body(ctx, twist=tw, lean=le, knees=kn)
    chest = Quaternion(U, math.radians(-tw)) @ F
    pro = PROTRACT * min(max((5.0 - at[2]) / 25.0, 0.0), 1.0)
    for s in "rl": sp[f"clavicle_{s}"] = [("toward", chest, pro)]
    sp.update(two_hands(at, blade, edge, D("r", *pr), D("l", *pl))); return sp


# Her arms outside her body. The poses' hand places were written against her reach alone, and the user saw the arms
# inside her body: measured, every frame of the three cuts had a forearm or a hand 4 to 10 cm inside her torso (the hilt
# held at her breastbone, her chest further forward than the hands). Each key and each frame is now measured against her
# torso as the pose deforms it (the faces whose vertices follow the pelvis and spine bones) and the hilt moved out until
# the bone lines of both forearms and hands are CLEAR cm outside it (the bone runs through the middle of the forearm).
TORSO = ("pelvis", "spine_01", "spine_02", "spine_03", "spine_04", "spine_05")
CLEAR = {"fore": 4.5, "hand": 3.5}


def torso_context(arm_obj, scene, ctx):
    """her torso's faces (those whose vertices each follow a TORSO bone most), per mesh, for clearance()"""
    parts = []
    for o in scene.objects:
        if o.type != 'MESH' or not o.vertex_groups: continue
        names = {g.index: g.name for g in o.vertex_groups}
        keep = [v.index for v in o.data.vertices if v.groups and names.get(max(v.groups, key=lambda g: g.weight).group) in TORSO]
        pos = {vi: i for i, vi in enumerate(keep)}
        polys = [[pos[v] for v in p.vertices] for p in o.data.polygons if all(v in pos for v in p.vertices)]
        if keep and polys: parts.append((o, keep, polys))
    ctx["torso"] = parts


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
    for s in "rl":
        a, b = P[f"lowerarm_{s}"].head, P[f"hand_{s}"].head
        palm = b + P[f"hand_{s}"].matrix.to_quaternion() @ ctx["arms"][s]["palm_pt"]
        for kind, p in [("fore", a.lerp(b, t)) for t in (0.35, 0.55, 0.75, 1.0)] + [("hand", palm)]:
            loc, nrm, _, _ = bvh.find_nearest(p)
            if loc is None: continue
            d = (p - loc).dot(nrm) / cm
            short = CLEAR[kind] - d
            if worst is None or short > worst[0]: worst = (short, d, nrm.copy())
    return worst or (-99.0, 99.0, F.copy())


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
        p = prm[:3] + (at,) + prm[4:6] + (poles,)
        n0 = len(ctx.get("wrists", [])); R.apply(arm_obj, spec2(ctx, p, edge), ctx); ws = ctx["wrists"][n0:]; del ctx["wrists"][n0:]
        return clearance(arm_obj, ctx)[0], hilt_miss(arm_obj, ctx, at), max([R.over(*w) for _, w in ws] or [0.0])
    at0 = Vector(prm[3]); short0, miss0, wr0 = put(tuple(at0), poles_of(prm))
    if short0 <= 0.0: return prm
    best = None
    for pi, poles in enumerate(POLES):
        for dz in (0, -4, -8, -12):
            for dy in (0, 4, 8):
                for dx in (-6, 0, 6):
                    at = at0 + Vector((dx, dy, dz)); short, miss, wr = put(tuple(at), poles)
                    if miss > miss0 + 1.0 or wr > max(wr0, 10.0) + 8.0: continue
                    # (clear: the nearest such place, a wrist past its limits and other elbows counted as distance; none
                    # clear yet: the one that clears most)
                    key = (0, (at - at0).length + 0.8 * wr + 2.0 * (pi > 0)) if short <= 0.0 else (1, short + 0.05 * wr)
                    if best is None or key < best[0]: best = (key, at, poles)
    return prm if best is None else prm[:3] + (tuple(best[1]),) + prm[4:6] + (best[2],)


def solve2(arm_obj, ctx, prm, rolls=16):
    """a two-handed key pose: the blade exactly its way, turned about it the way that leaves both wrists nearest their
    limits, the hilt moved where her arms clear her body (search_place); returns the pose (each bone's matrix_basis), the
    edge chosen, the spec, the params as moved"""
    def roll(prm):
        b = prm[4].normalized(); hint = prm[5]; h = (hint - b * hint.dot(b)).normalized(); best = None
        for k in range(rolls):
            e = Quaternion(b, math.radians(360.0 * k / rolls)) @ h
            sp = spec2(ctx, prm, e)
            n0 = len(ctx.get("wrists", [])); R.apply(arm_obj, sp, ctx); ws = ctx["wrists"][n0:]; del ctx["wrists"][n0:]
            cost = sum(R.over(*w) ** 2 for _, w in ws) + 0.002 * math.degrees(e.angle(h)) ** 2
            if best is None or cost < best[0]: best = (cost, e)
        return best[1]
    e = roll(prm); prm = search_place(arm_obj, ctx, prm, e); e = roll(prm)
    prm, _ = clear_pose(arm_obj, ctx, prm, e)
    return R.apply(arm_obj, spec2(ctx, prm, e), ctx), e, spec2(ctx, prm, e), prm


def swing(arm_obj, ctx, keys):
    """a two-handed clip solved frame by frame (keys: [(seconds, params, edge)]): between the keys the body, the right hand's
    place, the blade and its edge are eased from one to the next and both hands are put on the hilt again in every frame
    (eased local turns alone let the left hand drift 8 to 10 cm off the hilt half way through a cut). Where an eased
    frame brings her arms into her body the hilt is moved out (clear_pose), the moves smoothed over neighbouring frames so
    the swing does not jerk, and the frame measured again; returns the frames and the worst frame's shortfall (cm)"""
    n = int(round(keys[-1][0] * FPS)); base = []
    for i in range(n + 1):
        t = i / FPS
        j = max(k for k in range(len(keys) - 1) if keys[k][0] <= t + 1e-6) if t < keys[-1][0] else len(keys) - 2
        (t0, a, ea), (t1, b, eb) = keys[j], keys[j + 1]
        u = C.ease(min(max((t - t0) / (t1 - t0), 0.0), 1.0))
        lerp = lambda x, y: x + (y - x) * u
        turn = lambda v0, v1: Quaternion((1.0, 0.0, 0.0, 0.0)).slerp(v0.normalized().rotation_difference(v1.normalized()), u) @ v0.normalized()
        blade = turn(a[4], b[4]); edge = turn(ea, eb); edge = (edge - blade * edge.dot(blade)).normalized()
        poles = tuple(tuple(lerp(pa[q], pb[q]) for q in range(3)) for pa, pb in zip(poles_of(a), poles_of(b)))
        base.append(((lerp(a[0], b[0]), lerp(a[1], b[1]), lerp(a[2], b[2]), tuple(lerp(a[3][q], b[3][q]) for q in range(3)), blade, edge, poles), edge))
    # (the blade's turn about its length eased between two keys bent the wrists 70 to 76 degrees past their limits in
    # some frames: each frame's turn is one of 24 round the blade, chosen over the whole clip at once (a shortest path)
    # for the least strain on both wrists with the least change from frame to frame)
    OFFS = [15.0 * k for k in range(-11, 13)]
    cost = []
    for prm, edge in base:
        row = []
        for deg in OFFS:
            e = Quaternion(prm[4].normalized(), math.radians(deg)) @ edge
            n0 = len(ctx.get("wrists", [])); R.apply(arm_obj, spec2(ctx, prm, e), ctx); ws = ctx["wrists"][n0:]; del ctx["wrists"][n0:]
            row.append(sum(R.over(*w) ** 2 for _, w in ws) + 0.01 * deg * deg)
        cost.append(row)
    step = lambda a, b: 0.15 * min(abs(a - b), 360.0 - abs(a - b)) ** 2
    acc = [cost[0][:]]; back = []
    for i in range(1, len(cost)):
        prev = acc[-1]; row, bk = [], []
        for j, dj in enumerate(OFFS):
            k = min(range(len(OFFS)), key=lambda k: prev[k] + step(OFFS[k], dj)); bk.append(k); row.append(prev[k] + step(OFFS[k], dj) + cost[i][j])
        acc.append(row); back.append(bk)
    j = min(range(len(OFFS)), key=lambda k: acc[-1][k]); path = [j]
    for bk in reversed(back): j = bk[j]; path.append(j)
    path.reverse()
    base = [(prm[:5] + (e,) + prm[6:], e) for (prm, edge), j in zip(base, path)
            for e in [Quaternion(prm[4].normalized(), math.radians(OFFS[j])) @ edge]]
    moves = []
    for prm, edge in base:
        moved, _ = clear_pose(arm_obj, ctx, prm, edge)
        moves.append(Vector(moved[3]) - Vector(prm[3]))
    # (each frame's move: the largest of its neighbours' within 3 frames, then averaged over 5: no frame moves less than it needs)
    wide = [max(moves[max(0, i - 3):i + 4], key=lambda v: v.length) for i in range(len(moves))]
    smooth = [sum(wide[max(0, i - 2):i + 3], Vector()) / len(wide[max(0, i - 2):i + 3]) for i in range(len(wide))]
    frames, worst = [], -99.0; ctx["swing_wrists"] = []
    for i, ((prm, edge), mv) in enumerate(zip(base, smooth)):
        prm = prm[:3] + (tuple(Vector(prm[3]) + mv),) + prm[4:]
        prm, short = clear_pose(arm_obj, ctx, prm, edge)
        worst = max(worst, short)
        n0 = len(ctx.get("wrists", []))
        frames.append(R.apply(arm_obj, spec2(ctx, prm, edge), ctx))
        ctx["swing_wrists"].append((i, max([R.over(*w) for _, w in ctx["wrists"][n0:]] or [0.0])))
    return frames, worst


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
    sp.update(R.reach("l", (-5, 36, -1), D("l", 0.6, 0.0, -0.8), None, {"front": F, "up": U}))
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
        report.append("W5POSE %-18s wrist past limits %s | from its place %s" % (label, ", ".join("%s %.0f" % (s, R.over(*w)) for s, w in ws) or "-", ", ".join(miss) or "-"))
        return res
    out = {}
    if "TwoHand" in want:
        use(ctx, "sword"); torso_context(arm_obj, scene, ctx)
        def key2(prm, label):
            at0 = prm[3]
            res, e, sp, prm = solve2(arm_obj, ctx, prm)
            P(sp, label)                     # (once more, for the report)
            short, d, _ = clearance(arm_obj, ctx)
            report.append("W5POSE %-18s hilt moved out (%s) -> (%s) cm, elbows %d; her arms' nearest point %.1f cm outside her torso (short of CLEAR by %.1f)"
                          % (label, ", ".join("%.0f" % v for v in at0), ", ".join("%.1f" % v for v in prm[3]), POLES.index(poles_of(prm)), d, max(short, 0.0)))
            return prm, e
        g = key2(guard2(), "guard2")
        for name, fn in (("W5_TwoHand1", two1), ("W5_TwoHand2", two2), ("W5_TwoHand3", two3)):
            tw, tr, tf, te = TIMES[name]
            ks = [(0.0,) + g, (tw,) + key2(fn("wind"), name + " wind"), (tr,) + key2(fn("release"), name + " release"),
                  (tf,) + key2(fn("follow"), name + " follow"), (te,) + g]
            out[name], short = swing(arm_obj, ctx, ks)
            report.append("W5POSE %-18s her arms against her torso, the worst frame: short of CLEAR (forearm %.1f, hand %.1f cm outside) by %.1f cm"
                          % (name, CLEAR["fore"], CLEAR["hand"], max(short, 0.0)))
            report.append("W5POSE %-18s wrists past their limits per frame: %s" % (name, " ".join("%d:%.0f" % iw for iw in ctx["swing_wrists"])))
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
