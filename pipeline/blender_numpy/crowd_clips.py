"""Two looping clips for the townsfolk who watch an arena fight (the NPC pack's UE4 mannequin skeleton,
/Game/NPC_Characters_Pack/Demoscene_UE4/Mesh/UE4_Mannequin_Skeleton); their pack idle is kept as it is.
  Clap    2.0 s loop: applause, five claps (CLAPS below): the hands meet palm to palm in front of the chest, the palms
          flat on each other and the hands crossed a little in their plane (the left hand's fingers forward and up, the
          right's forward, across the left palm), the body leaning forward a little; between claps the hands open
  Cheer   2.4 s loop: both fists raised above the head in a V, pumped up twice (PUMPS), a small knee bounce, the head
          tilted up
Both start from the pack idle's first frame for the legs and body (its local turns taken onto the mesh's own skeleton)
and end on their first pose.
Posing: the UE4 mannequin's bones do not point along their own Y in Blender (the right side's point back at their parents),
so the poses are made on a stand-in armature built here with the same joints and every bone pointing at its child, and
carried over bone by bone as the same turn from the reference pose (the stand-in is what caster_clips / rogue_clips /
darkcaster_clips expect: it faces -Y, its right is -X). The arms are solved by rogue_clips.solve_arm (the elbow a hinge,
the wrist within its limits); the elbow's hinge is taken from the mannequin's own bent reference arm (A-pose), and the
palm's normal from the skin of the palm. The clap's hands are turned exactly (solve_arm's `exact`: palms facing). The
legs keep the idle's feet where they stand while the pelvis bounces (two-bone solve). The claps' hand separation is
solved against the skinned mesh until the two hands' skins just touch.
Measured on the skinned mesh, frame by frame (printed, and written to crowd_clips.json): at each clap the palms' gap (the
palm surfaces, along the palm's normal), how far they face off each other, and the two hands' skins' nearest signed
distance (negative: through each other); the wrists' worst angle past their limits (rogue_clips.over); the forearms and
hands against the body (the bone lines' distance to the spine chain, and arm skin inside the body's skin); for the Cheer
the wrists' height over the top of the head.
Writes <out_dir>/SK_NPC_Crowd_Clips.fbx (the armature only, named root as the skeleton's root bone, centimetres, the two
clips as takes Clap and Cheer, 30 fps) and <out_dir>/crowd_clips.json; preview pictures (workbench: front, side,
three-quarter, back, the hands close up at a clap and the fists) into preview_dir. Then reads the FBX back and checks it
against the poses it was made from (reference pose and frames).
Blender: -b -P crowd_clips.py -- SK_NPC_Character_01.fbx NPC_Idle.fbx out_dir preview_dir [nopreview]
(the two FBX are exported from Unreal: the pack's SK_NPC_Character_01_Full_01 and Demoscene_UE4/Animations/ThirdPersonIdle)"""
import json, math, os, sys
import bpy
import numpy as np
from mathutils import Matrix, Vector, Quaternion
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import caster_clips as C
import darkcaster_clips as DC
import rogue_clips as R

argv = sys.argv[sys.argv.index("--") + 1:]
NPC_FBX, IDLE_FBX, OUT_DIR, PREV_DIR = argv[0], argv[1], argv[2], argv[3]
PREVIEW = "nopreview" not in argv[4:]
FPS = 30
F, U, LEAN, OUT = C.F, C.U, C.LEAN, C.OUT
Y = Vector((0.0, 1.0, 0.0))
FINGERS = C.FINGERS + ("thumb",)
I3 = Vector((1.0, 1.0, 1.0))

# the clips' timing (seconds)
CLAP_LEN, CLAPS = 2.0, [0.2, 0.6, 1.0, 1.4, 1.8]
CHEER_LEN = 2.4
PUMPS = [0.0, 1.2]                                   # each pump: high at +0, pulled down at +0.45, thrust up at +0.70
# the Cheer's keys: the wrist (cm from the base of the neck: out to its side, forward, up), the pelvis dropped (cm), the
# collarbones raised (deg), the lean (deg, forward)
CHEER_KEYS = {"high": (28.0, 6.0, 47.0, 0.0, 16.0, -2.0), "low": (30.0, 8.0, 34.0, 4.5, 8.0, 1.5), "peak": (26.0, 5.0, 50.0, 0.0, 20.0, -3.0)}
# (the upper arm's turn about itself allowed to 90 degrees for the raised arms (rogue_clips.ARM_ROLL is 40, for the
# Rogue's cape): held to 40, the upper arms stood straight up by the ears with the elbows bent in over the head and the
# forearms out, the pulled-down pump a crown of forearms; at 90 the elbows go out to the sides and the forearms up)
CHEER_ARM_ROLL = 90.0
CLAP_AT = (0.0, 42.0, -18.0)                         # where the hands meet: cm from the base of the neck (her right, forward, up)
# The clap: the palms flat on each other (facing exactly), the two hands' ways crossed in the plane of the palms, the
# right hand's fingers across the left palm. A style: the left palm's normal tilted up from her right (deg), the left
# hand's way and the right's in the palms' plane (deg up from forward), and how far each wrist is behind the meeting point
# (cm). The arms are solved for the hands turned exactly so (rogue_clips.solve_arm's `exact`); the first style whose
# wrists stay within their limits and whose arms stay out of the body is kept. Measured over a grid (tilt -20..10, left
# 10..40, right -30..0): with the hands side by side the wrists are 8 cm apart and the sleeves' wide cuffs went through
# each other (253 crossing triangles); no style with the palms together kept them apart (a V turned in until they
# cleared met only at the fingertips, the palms 10 cm apart; the steeper crosses bent a wrist 25 to 70 degrees past its
# limits). The styles below keep the cuffs' crossing smallest of those that pass.
CLAP_STYLES = [(10.0, 30.0, 0.0, 7.5, 9.5), (0.0, 40.0, -10.0, 7.5, 9.5), (10.0, 20.0, 0.0, 7.5, 9.5)]
CLAP_OPEN = 13.0                                     # each hand moves this far off the other between claps (cm)
SKIN_TOUCH = 0.2                                     # the hands' skins at a clap: this far apart (cm)
HAND_DEEP = 3.0                                      # a point further than this behind a hand's skin is not inside it (a hand is ~3 cm thick)
TORSO_R = 18.0                                       # ...nor inside the body unless this near the spine chain (the clothes' open sheets: lapels)


def log(*a): print("CROWD", *a)


# ---------------------------------------------------------------- loading
def load():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    bpy.ops.import_scene.fbx(filepath=NPC_FBX)
    arm = next(o for o in sc.objects if o.type == 'ARMATURE')
    mesh = next(o for o in sc.objects if o.type == 'MESH')
    # (the importer hangs the skeleton under an empty scaled 0.01: the armature is in centimetres; it is taken out to the
    # scene's root and the scene made a centimetre scene, as tripo_build.py exports its rigs)
    for o in [o for o in sc.objects if o.type == 'EMPTY']:
        for ch in list(o.children): ch.parent = None
        bpy.data.objects.remove(o, do_unlink=True)
    arm.matrix_world = Matrix.Identity(4)
    mesh.parent = arm; mesh.matrix_parent_inverse.identity(); mesh.matrix_world = Matrix.Identity(4)
    sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 0.01
    sc.render.fps = FPS; sc.render.fps_base = 1.0
    for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'; pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    log("skeleton", arm.name, len(arm.data.bones), "bones; mesh", mesh.name, len(mesh.data.vertices), "vertices; pelvis z",
        round(arm.data.bones["pelvis"].head_local.z, 1))
    # the idle: its first frame's local turns
    before = set(sc.objects)
    bpy.ops.import_scene.fbx(filepath=IDLE_FBX)
    new = [o for o in sc.objects if o not in before]
    ia = next(o for o in new if o.type == 'ARMATURE')
    act = ia.animation_data.action
    f0, f1 = act.frame_range
    sc.frame_set(int(round(f0))); bpy.context.view_layer.update()
    Wa = {pb.name: pb.matrix.copy() for pb in ia.pose.bones}
    k = arm.data.bones["pelvis"].head_local.z / ia.data.bones["pelvis"].head_local.z
    drest = max((ia.data.bones[b.name].head_local * k - b.head_local).length for b in arm.data.bones if b.name in ia.data.bones)
    log("idle", act.name, "frames", f0, f1, "units x%.3f" % k, "its reference joints differ from the mesh's by up to %.2f cm" % drest)
    W = {}
    for pb in order(arm):
        b = pb.name; bone = pb.bone
        if b not in Wa: W[b] = bone.matrix_local.copy(); continue
        if bone.parent is None:
            W[b] = Matrix.LocRotScale(Wa[b].translation * k, Wa[b].to_quaternion(), I3)
        else:
            p = bone.parent.name
            loc_a = (Wa[p].inverted() @ Wa[b]).to_quaternion()
            off = (bone.parent.matrix_local.inverted() @ bone.matrix_local).translation
            W[b] = W[p] @ Matrix.LocRotScale(off, loc_a, I3)
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    for a in list(bpy.data.actions): bpy.data.actions.remove(a)
    set_world(arm, W)
    return sc, arm, mesh, W


def order(arm):
    return sorted(arm.pose.bones, key=lambda pb: len(pb.parent_recursive))


def set_world(arm, W):
    """each bone's armature-space matrix as W says (the basis worked out from the parents', no update between bones)"""
    for pb in arm.pose.bones:
        b = pb.bone
        if b.parent is None: base = b.matrix_local
        else: base = W[b.parent.name] @ (b.parent.matrix_local.inverted() @ b.matrix_local)
        pb.matrix_basis = base.inverted() @ W[b.name]
    bpy.context.view_layer.update()


def world(arm): return {pb.name: pb.matrix.copy() for pb in arm.pose.bones}


# ---------------------------------------------------------------- the stand-in armature
MAIN_CHILD = {"pelvis": "spine_01", "spine_01": "spine_02", "spine_02": "spine_03", "spine_03": "neck_01", "neck_01": "head"}
for s in "lr":
    MAIN_CHILD.update({f"clavicle_{s}": f"upperarm_{s}", f"upperarm_{s}": f"lowerarm_{s}", f"lowerarm_{s}": f"hand_{s}",
                       f"hand_{s}": f"middle_01_{s}", f"thigh_{s}": f"calf_{s}", f"calf_{s}": f"foot_{s}", f"foot_{s}": f"ball_{s}"})
    for fn in FINGERS:
        MAIN_CHILD[f"{fn}_01_{s}"] = f"{fn}_02_{s}"; MAIN_CHILD[f"{fn}_02_{s}"] = f"{fn}_03_{s}"


def build_helper(sc, arm):
    """an armature with the mannequin's joints, each bone pointing at its child (Y along the bone)"""
    hd = bpy.data.armatures.new("helper"); ho = bpy.data.objects.new("helper", hd); sc.collection.objects.link(ho)
    for o in sc.objects: o.select_set(False)
    ho.select_set(True); bpy.context.view_layer.objects.active = ho
    bpy.ops.object.mode_set(mode='EDIT')
    B = arm.data.bones; dirs = {}
    for b in sorted(B, key=lambda b: len(b.parent_recursive)):
        h = b.head_local.copy(); n = b.name
        if n in MAIN_CHILD and (B[MAIN_CHILD[n]].head_local - h).length > 0.5:
            t = B[MAIN_CHILD[n]].head_local.copy(); d = (t - h).normalized()
        elif n == "head": d = U.copy(); t = h + d * 15.0
        elif n.startswith("ball_"): d = F.copy(); t = h + d * 8.0
        elif n.startswith("ik_"): t = b.tail_local.copy(); d = (t - h).normalized()
        elif b.parent is not None and b.parent.name in dirs:          # (the fingers' tips, the twist bones: their parent's way)
            d = dirs[b.parent.name]; t = h + d * max(1.5, 0.8 * (B[b.parent.name].head_local - h).length if "twist" not in n else 10.0)
        else: d = U.copy(); t = h + d * 5.0
        dirs[n] = d
        eb = hd.edit_bones.new(n); eb.head = h; eb.tail = t; eb.roll = 0.0
    for b in B:
        if b.parent: hd.edit_bones[b.name].parent = hd.edit_bones[b.parent.name]
    bpy.ops.object.mode_set(mode='OBJECT')
    for pb in ho.pose.bones: pb.rotation_mode = 'QUATERNION'
    ho.hide_render = True
    return ho


class Rig:
    """the mesh's skeleton (arm), the stand-in (h), and the turn that carries one onto the other"""
    def __init__(self, arm, h):
        self.arm, self.h = arm, h
        self.Rr0 = {b.name: b.matrix_local.to_quaternion() for b in arm.data.bones}
        self.Rh0 = {b.name: h.data.bones[b.name].matrix_local.to_quaternion() for b in arm.data.bones}

    def to_helper(self, Wr):
        Wh = {b: Matrix.LocRotScale(Wr[b].translation, Wr[b].to_quaternion() @ self.Rr0[b].inverted() @ self.Rh0[b], I3) for b in Wr}
        set_world(self.h, Wh)

    def from_helper(self):
        Wh = world(self.h)
        return {b: Matrix.LocRotScale(Wh[b].translation, Wh[b].to_quaternion() @ self.Rh0[b].inverted() @ self.Rr0[b], I3) for b in Wh}

    def helper_rot(self, Wr, b):
        return Wr[b].to_quaternion() @ self.Rr0[b].inverted() @ self.Rh0[b]


def basis_of(arm, W):
    """the pose's basis per bone (loc, rot, scale): a translation only on the bones without a parent (the others' are
    rounding left by the turn carried over)"""
    out = {}
    for pb in arm.pose.bones:
        b = pb.bone
        base = b.matrix_local if b.parent is None else W[b.parent.name] @ (b.parent.matrix_local.inverted() @ b.matrix_local)
        l, q, s = (base.inverted() @ W[b.name]).decompose()
        if b.parent is not None: l = Vector((0.0, 0.0, 0.0))
        out[b.name] = (l, q.normalized(), Vector((1.0, 1.0, 1.0)))
    return out


def set_basis(arm, P):
    for pb in arm.pose.bones:
        l, q, s = P[pb.name]; pb.location = l; pb.rotation_quaternion = q; pb.scale = s
    bpy.context.view_layer.update()


# ---------------------------------------------------------------- posing (on the stand-in)
def hand_frame(h, ctx, hand):
    """the hand's own ways as posed: along it (wrist to knuckles), across it toward the index (and thumb), its palm's normal"""
    P = h.pose.bones; s = hand[-1]; q = P[hand].matrix.to_quaternion()
    ax = q @ Y; pn = q @ ctx["palm"][hand]; pn = (pn - ax * pn.dot(ax)).normalized()
    ac = P[f"index_01_{s}"].head - P[f"pinky_01_{s}"].head; ac = (ac - ax * ac.dot(ax) - pn * ac.dot(pn)).normalized()
    return ax, ac, pn


def ops_apply(h, spec, ctx):
    """darkcaster_clips.apply's operations, on top of the pose the bones have (no reset), and for the fingers:
    ('flex', deg): turned toward the palm about the knuckles' line (the same axis for every joint of a finger:
    caster_clips' curl turns about the bone's own way crossed with the palm's normal, which on a finger already bent near
    that normal swung it sideways: the first fists came out claws); ('aim', along, across, palm): the bone pointed that
    way in the hand's frame (the thumb)"""
    for pb in ctx["order"]:
        ops = spec.get(pb.name)
        if not ops: continue
        M = pb.matrix.copy(); head = M.translation.copy(); rot = M.to_quaternion(); scl = M.to_scale()
        for op in ops:
            k = op[0]; cur = rot @ Y
            if k == "rot": rot = Quaternion(op[1], math.radians(op[2])) @ rot
            elif k == "flex":
                ax, ac, pn = hand_frame(h, ctx, ctx["hand_of"][pb.name])
                rot = Quaternion(ax.cross(pn).normalized(), math.radians(op[1])) @ rot
            elif k == "aim":
                ax, ac, pn = hand_frame(h, ctx, ctx["hand_of"][pb.name])
                rot = cur.rotation_difference((ax * op[1] + ac * op[2] + pn * op[3]).normalized()) @ rot
            elif k == "move": head = head + op[1]
        pb.matrix = Matrix.LocRotScale(head, rot, scl)
        bpy.context.view_layer.update()


def keep_feet(h, feet):
    """the legs bent so each ankle stays where `feet` has it (and the foot turned as it was), the knee bending the way it did"""
    P = h.pose.bones
    for s in "lr":
        th, ca, ft = P[f"thigh_{s}"], P[f"calf_{s}"], P[f"foot_{s}"]
        a = (h.data.bones[f"calf_{s}"].head_local - h.data.bones[f"thigh_{s}"].head_local).length
        b = (h.data.bones[f"foot_{s}"].head_local - h.data.bones[f"calf_{s}"].head_local).length
        H = th.head.copy(); T, qfoot = feet[s]
        d = T - H; dist = min(d.length, (a + b) * 0.9995); dn = d.normalized()
        pole = ca.head - H; pole = pole - dn * pole.dot(dn)
        if pole.length < 1e-3: pole = F - dn * F.dot(dn)
        pole.normalize()
        c = max(-1.0, min(1.0, (a * a + dist * dist - b * b) / (2 * a * dist)))
        K = H + (dn * c + pole * math.sqrt(1.0 - c * c)) * a
        for pb, tgt in ((th, K), (ca, H + dn * dist)):
            M = pb.matrix.copy(); q = (M.to_quaternion() @ Y).rotation_difference(tgt - M.translation) @ M.to_quaternion()
            pb.matrix = Matrix.LocRotScale(M.translation, q, M.to_scale()); bpy.context.view_layer.update()
        M = ft.matrix.copy(); ft.matrix = Matrix.LocRotScale(M.translation, qfoot, M.to_scale()); bpy.context.view_layer.update()


def open_hand(side, straighten=12.0):
    """the fingers straightened from the reference hand's curl (left in it, the fingertips met with the palms 9 cm apart)
    and the thumb laid back along the index (the reference thumb stands off the palm: at a clap the thumbs met first)"""
    sp = {}
    for fn in C.FINGERS:
        for k, w in (("01", 0.4), ("02", 1.0), ("03", 0.8)): sp[f"{fn}_{k}_{side}"] = [("flex", -straighten * w)]
    sp[f"thumb_01_{side}"] = [("aim", 0.80, 0.55, -0.10)]
    sp[f"thumb_02_{side}"] = [("aim", 0.92, 0.38, -0.20)]
    sp[f"thumb_03_{side}"] = [("aim", 0.97, 0.22, -0.20)]
    return sp


def fist(side):
    """the fingers closed (knuckles 85, middle joints 100, tips 65 degrees) and the thumb across them"""
    sp = {}
    for fn in C.FINGERS:
        for k, a in (("01", 85.0), ("02", 100.0), ("03", 65.0)): sp[f"{fn}_{k}_{side}"] = [("flex", a)]
    sp[f"thumb_01_{side}"] = [("aim", 0.60, 0.20, 0.75)]
    sp[f"thumb_02_{side}"] = [("aim", 0.20, -0.75, 0.60)]
    sp[f"thumb_03_{side}"] = [("aim", 0.0, -0.95, 0.30)]
    return sp


def D(side, o, f, u): return C.D(side, o, f, u)


def pose(rig, ctx, idle_W, idle_h, body, arms, hands):
    """idle_W: the idle's first frame (the mesh's skeleton); body: {"lean", "drop", "clav", "look"}; arms: {side:
    rogue_clips.solve_arm's reach op}; hands: finger specs. Returns the pose as the mesh's skeleton's armature-space
    matrices."""
    h = rig.h
    rig.to_helper(idle_W)
    sp = {}
    lean, drop, clav, look = body.get("lean", 0.0), body.get("drop", 0.0), body.get("clav", 0.0), body.get("look", 0.0)
    if drop: sp["pelvis"] = [("move", U * -drop)]
    for b, w in (("spine_01", 0.3), ("spine_02", 0.35), ("spine_03", 0.35)): sp[b] = [("rot", LEAN, lean * w)]
    sp["neck_01"] = [("rot", LEAN, -lean * 0.45 - look * 0.4)]; sp["head"] = [("rot", LEAN, -look * 0.6)]
    if clav:
        for s in "lr": sp[f"clavicle_{s}"] = [("rot", OUT[s].cross(U).normalized(), clav)]
    ops_apply(h, sp, ctx)
    keep_feet(h, idle_h["feet"])
    for pb in h.pose.bones:                                        # the fingers from their reference shape
        if pb.name.split("_")[0] in FINGERS: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    for s, op in arms.items(): R.solve_arm(h, ctx, s, op)
    ops_apply(h, hands, ctx)
    W = rig.from_helper()
    # (the ik bones follow the feet and hands, as in the mannequin's own clips)
    for ik, b in (("ik_foot_l", "foot_l"), ("ik_foot_r", "foot_r"), ("ik_hand_gun", "hand_r"), ("ik_hand_r", "hand_r"), ("ik_hand_l", "hand_l")):
        if ik in W and ctx["ik_same"].get(ik): W[ik] = W[b].copy()
    return W


def her(v):
    """an armature-space way as (her right, forward, up)"""
    return (v.dot(OUT["r"]), v.dot(F), v.dot(U))


def clap_pose(rig, ctx, idle_W, idle_h, w, style, open_=0.0, lean=4.0):
    """w: each hand's skin moved this far (cm) off the meeting point along the palms' normal; style: one of CLAP_STYLES;
    open_: the hands this much further apart, a little back, and opened like a book"""
    tilt, phl, phr, bl, br = style
    t = math.radians(tilt)
    n = (OUT["r"] * math.cos(t) + U * math.sin(t)).normalized()       # (the left palm's normal: toward her right, tilted up)
    e1 = (F - n * F.dot(n)).normalized(); e2 = n.cross(e1).normalized()
    c = OUT["r"] * CLAP_AT[0] + F * CLAP_AT[1] + U * CLAP_AT[2]
    arms = {}
    for s, ph, back, sgn in (("l", phl, bl, -1.0), ("r", phr, br, 1.0)):
        a = e1 * math.cos(math.radians(ph)) + e2 * math.sin(math.radians(ph))
        pn = n * -sgn                                                  # (the palm faces the other hand)
        book = Quaternion(U, math.radians(0.35 * open_ * sgn))
        a, pn = book @ a, book @ pn
        wrist = c - a * back + n * sgn * (w + open_) - F * (0.3 * open_)
        arms[s] = ("reach", her(wrist), D(s, 1.0, -0.25, -0.6), None, {"front": a, "up": pn})
    hands = {}; hands.update(open_hand("l")); hands.update(open_hand("r"))
    return pose(rig, ctx, idle_W, idle_h, {"lean": lean}, arms, hands)


def cheer_pose(rig, ctx, idle_W, idle_h, k, palm=(-1.0, 0.6, 0.0)):
    """k: 'high' (fists up, arms near straight), 'low' (pulled down above the head, elbows bent, knees bent), 'peak' (thrust);
    palm: the way the fists' palms face (in, forward, up)"""
    x, y, z, drop, clav, lean = CHEER_KEYS[k]
    arms = {}
    for s in "lr":
        sx = 1.0 if s == "r" else -1.0
        arms[s] = ("reach", (sx * x, y, z), D(s, 1.0, 0.3, -0.2), {"axis": D(s, 0.25, 0.0, 1.0), "palm": D(s, *palm)}, None)
    hands = {}; hands.update(fist("l")); hands.update(fist("r"))
    keep = R.ARM_ROLL; R.ARM_ROLL = CHEER_ARM_ROLL
    try: return pose(rig, ctx, idle_W, idle_h, {"lean": lean, "drop": drop, "clav": clav, "look": 14.0}, arms, hands)
    finally: R.ARM_ROLL = keep


# ---------------------------------------------------------------- measuring (on the skinned mesh)
class Meter:
    def __init__(self, rig, mesh, ctx):
        self.rig, self.mesh, self.ctx = rig, mesh, ctx
        arm = rig.arm; me = mesh.data; names = [g.name for g in mesh.vertex_groups]
        dom = np.full(len(me.vertices), -1)
        for v in me.vertices:
            if v.groups:
                g = max(v.groups, key=lambda g: g.weight); dom[v.index] = g.group
        gname = np.array(names + [""])[dom]; self.gname = gname
        def verts(pred): return np.array([i for i, n in enumerate(gname) if pred(n)], dtype=np.int64)
        self.hand = {s: verts(lambda n, s=s: n == f"hand_{s}" or (n.endswith("_" + s) and n.split("_")[0] in FINGERS)) for s in "lr"}
        self.fore = {s: verts(lambda n, s=s: n in (f"lowerarm_{s}", f"lowerarm_twist_01_{s}")) for s in "lr"}
        self.bodyv = verts(lambda n: n in ("pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head", "clavicle_l", "clavicle_r"))
        self.headv = verts(lambda n: n == "head")
        polys = [tuple(p.vertices) for p in me.polygons]
        def polys_of(idx):
            st = set(idx.tolist()); return [p for p in polys if all(i in st for i in p)]
        # the hand itself (for the claps' contact) is its skin: the mesh's pieces (islands) that hold finger vertices. The
        # sleeve is a piece of its own whose cuff and frill hang round the wrist from the hand bone: counted as hand, the
        # hand measured 8.5 cm thick and the frills' open sheets gave the contact a wrong side. The cuffs are that sleeve
        # piece's faces moved by the hand and forearm bones.
        B = arm.data.bones; co0 = np.array([v.co[:] for v in me.vertices])
        par = list(range(len(me.vertices)))
        def find(a):
            while par[a] != a: par[a] = par[par[a]]; a = par[a]
            return a
        for e in me.edges:
            a, b = find(e.vertices[0]), find(e.vertices[1])
            if a != b: par[a] = b
        isl = np.array([find(i) for i in range(len(me.vertices))])
        fingered = set(isl[[i for i, n in enumerate(gname) if n.split("_")[0] in FINGERS]].tolist())
        skin = np.isin(isl, list(fingered))
        self.hand = {s: idx[skin[idx]] for s, idx in self.hand.items()}
        self.cuff = {s: verts(lambda n, s=s: n in (f"hand_{s}", f"lowerarm_{s}", f"lowerarm_twist_01_{s}")) for s in "lr"}
        self.cuff = {s: idx[~skin[idx]] for s, idx in self.cuff.items()}
        self.hand_polys = {s: polys_of(self.hand[s]) for s in "lr"}
        self.cuff_polys = {s: polys_of(self.cuff[s]) for s in "lr"}
        self.body_polys = polys_of(self.bodyv)
        self.arm_polys = polys_of(np.concatenate([self.fore["l"], self.fore["r"], self.hand["l"], self.hand["r"],
                                                  verts(lambda n: n in ("hand_l", "hand_r"))]))
        log("mesh parts: %d pieces; hands' skin %d / %d vertices (%d / %d faces), cuffs %d / %d faces, forearms %d / %d vertices, body %d (%d faces)" % (
            len(set(isl.tolist())), len(self.hand["l"]), len(self.hand["r"]), len(self.hand_polys["l"]), len(self.hand_polys["r"]),
            len(self.cuff_polys["l"]), len(self.cuff_polys["r"]), len(self.fore["l"]), len(self.fore["r"]), len(self.bodyv), len(self.body_polys)))
        # the palm: where a ray from the hand's bone line (60 % of the way from the wrist to the knuckles) along the palm's
        # normal leaves the skin, and that normal, in each hand bone's rest frame
        vl0 = [tuple(c) for c in co0]; self.palm = {}; self.palm_n0 = {}
        for s in "lr":
            hb = B[f"hand_{s}"]; hh = hb.head_local; m1 = B[f"middle_01_{s}"].head_local
            a = (m1 - hh).normalized(); L = (m1 - hh).length
            along = (B[f"middle_03_{s}"].head_local - B[f"middle_01_{s}"].head_local).normalized()
            across = (B[f"index_01_{s}"].head_local - B[f"pinky_01_{s}"].head_local).normalized()
            n0 = along.cross(across).normalized()
            if s == "r": n0 = -n0
            n0 = (n0 - a * n0.dot(a)).normalized()
            # (the palm's normal from the skin itself: the mean normal of the palm side's skin over the hand bone. Taken from
            # the finger bones alone it leant toward the thumb, and the hands met at the thumbs' pads in a tent, the
            # middles of the palms 7 cm apart)
            idx = self.hand[s][gname[self.hand[s]] == f"hand_{s}"]
            nrm = np.array([me.vertices[i].normal[:] for i in idx])
            pa = (co0[idx] - np.array(hh)) @ np.array(a)
            sel = (pa > 2.0) & (pa < 0.85 * L) & (nrm @ np.array(n0) > 0.5)
            n = Vector(nrm[sel].mean(0)); n = (n - a * n.dot(a)).normalized()
            log("palm %s: its skin faces %.0f deg off the way the finger bones give (%d vertices)" % (s, math.degrees(n.angle(n0)), int(sel.sum())))
            self.palm_n0[s] = n
            bvh = BVHTree.FromPolygons(vl0, self.hand_polys[s])
            o = hh + a * (0.6 * L)
            hit = bvh.ray_cast(o, n, 20.0); back = bvh.ray_cast(o, -n, 20.0)
            M0 = hb.matrix_local
            self.palm[s] = (M0.inverted() @ hit[0], M0.to_quaternion().inverted() @ n)
            log("palm %s: the skin %.1f cm off the hand's bone line on the palm side, %.1f on the back" % (s, hit[3], back[3] if back[0] else -1))
        # the palms' sides: the hand's skin over the hand bone and the fingers (the thumb's left out) that faces the palm's
        # way in the reference pose (the fingers are near straight in it)
        self.palm_side = {}
        for s in "lr":
            n = self.palm_n0[s]
            self.palm_side[s] = np.array([i for i in self.hand[s] if not gname[i].startswith("thumb") and Vector(me.vertices[i].normal).dot(n) > 0.3], dtype=np.int64)
        self.palm_side_polys = {s: polys_of(self.palm_side[s]) for s in "lr"}
        log("palm sides: %d / %d vertices (%d / %d faces)" % (len(self.palm_side["l"]), len(self.palm_side["r"]), len(self.palm_side_polys["l"]), len(self.palm_side_polys["r"])))

    def coords(self):
        dg = bpy.context.evaluated_depsgraph_get(); ev = self.mesh.evaluated_get(dg); m = ev.to_mesh()
        co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", co); ev.to_mesh_clear()
        return co.reshape(-1, 3)

    @staticmethod
    def signed(bvh, pts):
        """each point's signed distance to the surface (negative: behind it, inside)"""
        out = []
        for p in pts:
            loc, nrm, idx, dist = bvh.find_nearest(Vector(p))
            if loc is None: continue
            out.append(dist if (Vector(p) - loc).dot(nrm) >= 0.0 else -dist)
        return np.array(out)

    def frame(self):
        arm = self.rig.arm; W = world(arm); co = self.coords(); vl = [tuple(c) for c in co]; r = {}
        # wrists
        worst = 0.0
        for s in "lr":
            A = self.ctx["arms"][s]
            w = R.wrist_of(A, self.rig.helper_rot(W, f"lowerarm_{s}"), self.rig.helper_rot(W, f"hand_{s}"))
            worst = max(worst, R.over(*w)); r[f"wrist_{s}"] = [round(v, 1) for v in w]
        r["wrist_over"] = worst
        # forearms and hands against the spine chain (bone lines) and inside the body's skin
        chain = [W[b].translation for b in ("pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head")]
        dmin = 1e9
        for s in "lr":
            pts = [W[f"lowerarm_{s}"].translation, W[f"hand_{s}"].translation, W[f"middle_01_{s}"].translation]
            for p0, p1 in zip(pts[:-1], pts[1:]):
                for i in range(21):
                    p = p0.lerp(p1, i / 20.0)
                    for c0, c1 in zip(chain[:-1], chain[1:]):
                        dmin = min(dmin, seg_dist(p, c0, c1))
        r["arm_to_spine"] = dmin
        # (a point behind the nearest body face counts as inside only near the spine chain: in front of the chest the
        # nearest face can be the inside of the open jacket's lapel)
        body = BVHTree.FromPolygons(vl, self.body_polys)
        armv = np.concatenate([self.fore["l"], self.fore["r"], self.hand["l"], self.hand["r"]])
        sd = self.signed(body, co[armv])
        dsp = np.min([seg_dist_np(co[armv], c0, c1) for c0, c1 in zip(chain[:-1], chain[1:])], axis=0)
        near = dsp < TORSO_R
        inside = (sd < -0.5) & near
        r["arm_in_body"] = float(sd[near].min()) if near.any() else 99.0; r["arm_in_body_n"] = int(inside.sum())
        if inside.any():
            i = int(np.argmin(np.where(inside, sd, 99.0)))
            r["arm_in_body_at"] = (str(self.gname[armv[i]]), round(float(sd[i]), 1), round(float(dsp[i]), 1), [round(float(x), 1) for x in co[armv[i]]])
        # the two hands: the nearest signed distance of one hand's skin points to the other's skin (a point deeper than a
        # hand is thick is not inside it: the nearest face seen from its back)
        bl = BVHTree.FromPolygons(vl, self.hand_polys["l"]); br = BVHTree.FromPolygons(vl, self.hand_polys["r"])
        d = np.concatenate([self.signed(bl, co[self.hand["r"]]), self.signed(br, co[self.hand["l"]])])
        d = d[d > -HAND_DEEP]
        r["skin_gap"] = float(d.min()); r["skin_through_n"] = int((d < -0.3).sum())
        # surfaces through each other, counted as pairs of crossing triangles: the two hands' skins, the two cuffs, and the
        # forearms, cuffs and hands with the body
        r["hands_cross"] = len(bl.overlap(br))
        r["cuffs_cross"] = len(BVHTree.FromPolygons(vl, self.cuff_polys["l"]).overlap(BVHTree.FromPolygons(vl, self.cuff_polys["r"])))
        r["arm_body_cross"] = len(BVHTree.FromPolygons(vl, self.arm_polys).overlap(body))
        # the palms: the nearest distance between the two palms' sides (skin to skin), what touches what, and how far the
        # palms face off each other; and the distance between the palms' middles (the skin over the hand bone's middle)
        pl = BVHTree.FromPolygons(vl, self.palm_side_polys["l"])
        best = (1e9, None, None)
        for i in self.palm_side["r"]:
            loc, nrm, fi, dist = pl.find_nearest(Vector(co[i]))
            if loc is not None and dist < best[0]: best = (dist, i, fi)
        r["palm_gap"] = best[0]
        r["touch"] = (str(self.gname[best[1]]), str(self.gname[self.palm_side_polys["l"][best[2]][0]])) if best[1] is not None else ("-", "-")
        Pl = W["hand_l"] @ self.palm["l"][0]; Pr = W["hand_r"] @ self.palm["r"][0]
        nl = W["hand_l"].to_quaternion() @ self.palm["l"][1]; nr = W["hand_r"].to_quaternion() @ self.palm["r"][1]
        r["palm_mid_gap"] = (Pr - Pl).length; r["palm_facing"] = math.degrees(nl.angle(-nr))
        # the wrists over the head
        top = float(co[self.headv][:, 2].max())
        r["wrist_over_head"] = min(W[f"hand_{s}"].translation.z for s in "lr") - top
        r["head_top"] = top
        return r


def seg_dist_np(P, a, b):
    a, b = np.array(a), np.array(b); ab = b - a
    t = np.clip((P - a) @ ab / max(float(ab @ ab), 1e-9), 0.0, 1.0)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


def seg_dist(p, a, b):
    ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
    return (p - (a + ab * t)).length


# ---------------------------------------------------------------- sampling
def sample(keys, length):
    """keys: [(seconds, pose (basis per bone), easing of the way to the next key)], the last at `length` -> frames at FPS.
    Easing: 'in' speeds up into the next key (a clap meets at speed), 'out' slows from it, 'smooth' both"""
    n = int(round(length * FPS)); frames = []
    fn = {"in": lambda u: u * u, "out": lambda u: 1.0 - (1.0 - u) * (1.0 - u), "smooth": C.ease, "lin": lambda u: u}
    for i in range(n + 1):
        t = i / FPS
        j = max(k for k in range(len(keys) - 1) if keys[k][0] <= t + 1e-6) if i < n else len(keys) - 2
        (t0, a, e), (t1, b, _) = keys[j], keys[j + 1]
        u = fn[e](min(max((t - t0) / (t1 - t0), 0.0), 1.0)); fr = {}
        for bn in a:
            l0, q0, s0 = a[bn]; l1, q1, s1 = b[bn]
            if q0.dot(q1) < 0.0: q1 = -q1
            fr[bn] = (l0.lerp(l1, u), q0.slerp(q1, u), s0.lerp(s1, u))
        frames.append(fr)
    return frames


# ---------------------------------------------------------------- preview pictures
def setup_render(sc):
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.75, 0.72, 0.68)
    sh.show_cavity = True
    sc.render.resolution_x = 420; sc.render.resolution_y = 560; sc.render.film_transparent = False
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.clip_end = 5000.0
    bpy.ops.mesh.primitive_plane_add(size=260.0, location=(0, 0, -0.2))
    fl = bpy.context.active_object; fl.name = "floor"
    return cam


def shoot(sc, cam, path, target, ang, scale, elev=0.12):
    a = math.radians(ang); d = Vector((math.sin(a), -math.cos(a), elev)).normalized()
    cam.location = target + d * 600.0; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = scale; sc.render.filepath = path; bpy.ops.render.render(write_still=True)


def shoot_dir(sc, cam, path, target, d, scale):
    d = d.normalized(); cam.location = target + d * 600.0
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = scale; sc.render.filepath = path; bpy.ops.render.render(write_still=True)


# ---------------------------------------------------------------- export and the check of the file
def key_action(arm, name, frames):
    ad = arm.animation_data_create()
    act = bpy.data.actions.new(name); act.use_fake_user = True; ad.action = act
    if hasattr(ad, "action_slot") and hasattr(act, "slots"):
        try: ad.action_slot = act.slots.new('OBJECT', arm.name)
        except Exception: pass
    for i, fr in enumerate(frames):
        for pb in arm.pose.bones:
            l, q, s = fr[pb.name]; pb.location = l; pb.rotation_quaternion = q; pb.scale = s
            pb.keyframe_insert("location", frame=i, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=i, group=pb.name)
            pb.keyframe_insert("scale", frame=i, group=pb.name)
    ad.action = None
    return act


def main():
    os.makedirs(OUT_DIR, exist_ok=True); os.makedirs(PREV_DIR, exist_ok=True)
    sc, arm, mesh, idle_W = load()
    h = build_helper(sc, arm)
    rig = Rig(arm, h)
    # the stand-in's context for the helpers (caster_clips.context, rogue_clips.arm_context; centimetres)
    ctx = C.context(h); DC.add_thumb_op(ctx, h); ctx["cm"] = 1.0
    meter = Meter(rig, mesh, ctx)
    HB = h.data.bones
    for s in "lr":                                                 # (the palm's normal as the skin has it, for every use)
        ctx["palm"][f"hand_{s}"] = HB[f"hand_{s}"].matrix_local.to_quaternion().inverted() @ meter.palm_n0[s]
    R.arm_context(ctx, h)
    for s in "lr":                                                 # (solve_arm's `exact` hand: its own way and its palm)
        ctx["arms"][s]["local"]["front"] = Y.copy(); ctx["arms"][s]["local"]["up"] = ctx["palm"][f"hand_{s}"].copy()
    for s in "lr":                                                 # (the elbow's hinge from the mannequin's bent reference arm)
        up = (HB[f"lowerarm_{s}"].head_local - HB[f"upperarm_{s}"].head_local).normalized()
        fo = (HB[f"hand_{s}"].head_local - HB[f"lowerarm_{s}"].head_local).normalized()
        A = ctx["arms"][s]; old = A["hinge"].copy()
        A["hinge"] = HB[f"upperarm_{s}"].matrix_local.to_quaternion().inverted() @ up.cross(fo).normalized()
        log("elbow %s: reference bend %.0f deg; hinge moved %.0f deg from rogue_clips' (forearm x forward)" % (s, math.degrees(up.angle(fo)), math.degrees(old.angle(A["hinge"]))))
    AB = arm.data.bones
    ctx["ik_same"] = {ik: AB[ik].matrix_local.to_quaternion().rotation_difference(AB[b].matrix_local.to_quaternion()).angle < 0.01 and (AB[ik].head_local - AB[b].head_local).length < 0.1
                      for ik, b in (("ik_foot_l", "foot_l"), ("ik_foot_r", "foot_r"), ("ik_hand_gun", "hand_r"), ("ik_hand_r", "hand_r"), ("ik_hand_l", "hand_l")) if ik in AB}
    log("ik bones placed on their bones:", ctx["ik_same"])
    rig.to_helper(idle_W)
    idle_h = {"feet": {s: (h.pose.bones[f"foot_{s}"].head.copy(), h.pose.bones[f"foot_{s}"].matrix.to_quaternion()) for s in "lr"}}
    idle_basis = basis_of(arm, idle_W)

    def measure(W):
        set_world(arm, W); return meter.frame()

    set_world(arm, idle_W); m0 = meter.frame()
    log("the idle's first frame: crossing triangles: hands %d, cuffs %d, arms with the body %d" % (m0["hands_cross"], m0["cuffs_cross"], m0["arm_body_cross"]))
    # ---- Clap: for each style (CLAP_STYLES, in order), the hands' distance off the meeting point solved until their skins
    # just touch (bracketed, then halved: the gap is not smooth in it, as the solver's elbow choices step); the first style
    # whose wrists stay within their limits and whose arms stay out of the body is kept
    for si, style in enumerate(CLAP_STYLES):
        tries = {}
        def gap_at(w):
            Wc = clap_pose(rig, ctx, idle_W, idle_h, w, style); m = measure(Wc); tries[w] = (m, Wc)
            log("clap solve: style %d, hands %.2f cm off the meeting point -> skins %.2f cm apart (%d points through, %d triangles crossing), "
                "palms %.2f cm (%s on %s), facing %.0f deg off; cuffs crossing %d, arms with the body %d, wrists %.1f deg past their limits"
                % (si, w, m["skin_gap"], m["skin_through_n"], m["hands_cross"], m["palm_gap"], m["touch"][0], m["touch"][1], m["palm_facing"],
                   m["cuffs_cross"], m["arm_body_cross"], m["wrist_over"]))
            ok = m["skin_through_n"] == 0 and m["hands_cross"] == 0
            return m["skin_gap"] - SKIN_TOUCH if ok else min(m["skin_gap"] - SKIN_TOUCH, -0.5)
        lo, hi = 2.0, 6.0
        while gap_at(hi) < 0.0: lo, hi = hi, hi + 2.0
        for _ in range(7):
            mid = 0.5 * (lo + hi)
            if gap_at(mid) < 0.0: lo = mid
            else: hi = mid
        w = hi; mc, Wc = tries[w]
        if mc["arm_body_cross"] <= m0["arm_body_cross"] and mc["wrist_over"] < 1.0: break
    clap_style = si
    log("clap: style %d %s, hands %.2f cm off the meeting point" % (si, style, w))
    P_clap = basis_of(arm, Wc)
    P_open = basis_of(arm, clap_pose(rig, ctx, idle_W, idle_h, w, style, open_=CLAP_OPEN, lean=3.0))
    P_open2 = basis_of(arm, clap_pose(rig, ctx, idle_W, idle_h, w, style, open_=CLAP_OPEN * 0.85, lean=3.5))
    keys = [(0.0, P_open, "in")]
    for i, t in enumerate(CLAPS):
        keys.append((t, P_clap, "out"))
        keys.append((t + 0.2, P_open if i % 2 else P_open2, "in"))
    keys[-1] = (CLAP_LEN, P_open, "in")
    clap = sample(keys, CLAP_LEN)
    # ---- Cheer: the fists' palms facing the way the wrists bear best (the first try, in and forward, twisted the right
    # wrist 87 degrees, 7 past its limit)
    best = None
    for palm in ((-1.0, 0.6, 0.0), (-1.0, 0.0, 0.0), (-1.0, 1.0, 0.0), (-0.3, 1.0, 0.0), (0.0, 1.0, 0.0)):
        worst = 0.0
        for k in ("high", "low", "peak"):
            set_world(arm, cheer_pose(rig, ctx, idle_W, idle_h, k, palm)); worst = max(worst, meter.frame()["wrist_over"])
        log("cheer: fists' palms facing (in %.1f, forward %.1f, up %.1f): wrists at most %.1f deg past their limits" % (*palm, worst))
        if best is None or worst < best[0] - 0.5: best = (worst, palm)
    cheer_palm = best[1]
    Ph, Pl, Pp = (basis_of(arm, cheer_pose(rig, ctx, idle_W, idle_h, k, cheer_palm)) for k in ("high", "low", "peak"))
    keys = []
    for t0 in PUMPS:
        keys += [(t0, Ph, "smooth"), (t0 + 0.45, Pl, "out"), (t0 + 0.70, Pp, "smooth")]
    keys.append((CHEER_LEN, Ph, "smooth"))
    cheer = sample(keys, CHEER_LEN)
    clips = {"Clap": clap, "Cheer": cheer}
    # ---- measure every frame
    report = {}
    for name, frames in clips.items():
        rows = []
        for i, fr in enumerate(frames):
            set_basis(arm, fr); rows.append(meter.frame())
        loop = max(min(a, 360.0 - a) for a in (math.degrees(frames[0][b][1].rotation_difference(frames[-1][b][1]).angle) for b in frames[0]))
        rep = {"frames": len(frames), "length": (len(frames) - 1) / FPS, "loop_first_last_deg": round(loop, 3),
               "wrist_over_max": round(max(r["wrist_over"] for r in rows), 1),
               "arm_to_spine_min": round(min(r["arm_to_spine"] for r in rows), 1),
               "arm_in_body_min": round(min(r["arm_in_body"] for r in rows), 2), "arm_in_body_frames": sum(1 for r in rows if r["arm_in_body_n"] > 0),
               "arm_body_cross_max": max(r["arm_body_cross"] for r in rows), "arm_body_cross_idle": m0["arm_body_cross"],
               "hands_cross_frames": sum(1 for r in rows if r["hands_cross"] > 0), "cuffs_cross_frames": sum(1 for r in rows if r["cuffs_cross"] > 0)}
        bad = [(i, r["arm_in_body_n"], r["arm_in_body_at"]) for i, r in enumerate(rows) if r["arm_in_body_n"] > 0]
        if bad: rep["arm_in_body_worst"] = max(bad, key=lambda b: b[1])
        wi = max(range(len(rows)), key=lambda i: rows[i]["wrist_over"])
        rep["wrist_worst"] = {"frame": wi, "l": rows[wi]["wrist_l"], "r": rows[wi]["wrist_r"]}
        if name == "Clap":
            rep["claps"] = []
            for t in CLAPS:
                r = rows[int(round(t * FPS))]
                rep["claps"].append({"t": t, "palm_gap_cm": round(r["palm_gap"], 2), "touch": r["touch"], "skin_gap_cm": round(r["skin_gap"], 2),
                                     "skin_points_through": r["skin_through_n"], "hands_crossing_triangles": r["hands_cross"],
                                     "cuffs_crossing_triangles": r["cuffs_cross"], "palms_facing_off_deg": round(r["palm_facing"], 1),
                                     "palm_middles_apart_cm": round(r["palm_mid_gap"], 1)})
            rep["skin_gap_min_all_frames"] = round(min(r["skin_gap"] for r in rows), 2)
            rep["skin_through_frames"] = sum(1 for r in rows if r["skin_through_n"] > 0)
            rep["open_palm_gap_cm"] = round(rows[0]["palm_gap"], 1)
            rep["clap_style"] = dict(zip(("palm_tilt_deg", "left_way_deg", "right_way_deg", "left_wrist_behind_cm", "right_wrist_behind_cm"),
                                         CLAP_STYLES[clap_style]), index=clap_style, hands_off_meeting_point_cm=round(w, 2))
        else:
            rep["wrist_over_head_min_cm"] = round(min(r["wrist_over_head"] for r in rows), 1)
            rep["wrist_over_head_max_cm"] = round(max(r["wrist_over_head"] for r in rows), 1)
            rep["fists_palm"] = cheer_palm
            pel = [fr["pelvis"][0].length for fr in frames]
            rep["pelvis_bounce_cm"] = round(max(pel) - min(pel), 1)
        report[name] = rep
        log(name, json.dumps(rep))
    # ---- pictures
    if PREVIEW:
        cam = setup_render(sc); n = 0
        picks = {"Clap": [0, int(round(CLAPS[0] * FPS)), int(round((CLAPS[0] + 0.1) * FPS)), int(round(CLAPS[2] * FPS))],
                 "Cheer": [0, int(round(0.45 * FPS)), int(round(0.70 * FPS)), int(round(1.0 * FPS))]}
        for name, idx in picks.items():
            for fi in idx:
                set_basis(arm, clips[name][fi])
                for view, ang in (("front", 0), ("side", 90), ("q", 35), ("back", 180)):
                    shoot(sc, cam, os.path.join(PREV_DIR, f"{name}_{fi:02d}_{view}.png"), Vector((0, 0, 108 if name == "Clap" else 118)), ang, 215 if name == "Clap" else 240); n += 1
        for t in (CLAPS[0], CLAPS[3]):                              # the hands close up at a clap
            fi = int(round(t * FPS)); set_basis(arm, clips["Clap"][fi])
            W = world(arm); c = (W["hand_l"].translation + W["hand_r"].translation) * 0.5
            for view, ang, el in (("front", 0, 0.1), ("top", 0, 3.0), ("q", 35, 0.3), ("side", 90, 0.1)):
                shoot(sc, cam, os.path.join(PREV_DIR, f"Clap_{fi:02d}_hands_{view}.png"), c, ang, 38, el); n += 1
        for fi in (0, int(round(0.45 * FPS))):                     # the fists close up
            set_basis(arm, clips["Cheer"][fi]); W = world(arm)
            for s in "lr":
                c = W[f"hand_{s}"].translation.lerp(W[f"middle_01_{s}"].translation, 0.6)
                for view, ang in (("front", 0), ("side", 90 if s == "l" else -90), ("back", 180)):
                    shoot(sc, cam, os.path.join(PREV_DIR, f"Cheer_{fi:02d}_fist_{s}_{view}.png"), c, ang, 30); n += 1
                pn = W[f"hand_{s}"].to_quaternion() @ meter.palm[s][1]          # (from the palm's side)
                shoot_dir(sc, cam, os.path.join(PREV_DIR, f"Cheer_{fi:02d}_fist_{s}_palm.png"), c, pn, 30); n += 1
        set_basis(arm, idle_basis)                                  # the idle's first frame, for comparison
        for view, ang in (("front", 0), ("side", 90)):
            shoot(sc, cam, os.path.join(PREV_DIR, f"Idle_00_{view}.png"), Vector((0, 0, 108)), ang, 215); n += 1
        log("pictures", n, "in", PREV_DIR)
    # ---- export (the pose put back to the reference pose after keying: with no mesh in the file, the bones' own transforms
    # in it are read back as the reference pose, and the first export carried the Cheer's last frame as one)
    for pb in arm.pose.bones: pb.matrix_basis.identity()
    for name, frames in clips.items(): key_action(arm, name, frames)
    for pb in arm.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    for o in [o for o in sc.objects if o is not arm]: bpy.data.objects.remove(o, do_unlink=True)
    for o in sc.objects: o.select_set(False)
    arm.select_set(True); bpy.context.view_layer.objects.active = arm
    fbx = os.path.join(OUT_DIR, "SK_NPC_Crowd_Clips.fbx")
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={'ARMATURE'}, add_leaf_bones=False,
                             bake_anim=True, bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
                             bake_anim_simplify_factor=0.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE',
                             use_armature_deform_only=False)
    log("exported", fbx, os.path.getsize(fbx), "bytes")
    # ---- the file read back: reference pose against the NPC FBX's, and frames against the poses made
    made_rest = {b.name: b.matrix_local.copy() for b in arm.data.bones}
    probe = {}
    for name, frames in clips.items():
        for fi in (0, len(frames) // 3, len(frames) - 1):
            set_basis(arm, frames[fi]); probe[(name, fi)] = {b: m.translation.copy() for b, m in world(arm).items()}
    check = verify(fbx, made_rest, probe)
    json.dump({"fps": FPS, "fbx": os.path.basename(fbx), "skeleton_root": "root",
               "Clap": {"length": CLAP_LEN, "frames": len(clap), "meet": CLAPS, **{k: v for k, v in report["Clap"].items() if k != "frames"}},
               "Cheer": {"length": CHEER_LEN, "frames": len(cheer), "pump_peaks": [t + 0.70 for t in PUMPS], "pump_lows": [t + 0.45 for t in PUMPS],
                         **{k: v for k, v in report["Cheer"].items() if k != "frames"}},
               "fbx_check": check}, open(os.path.join(OUT_DIR, "crowd_clips.json"), "w"), indent=1)
    log("DONE")


def verify(fbx, made_rest, probe):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    bpy.ops.import_scene.fbx(filepath=fbx)
    a2 = next(o for o in sc.objects if o.type == 'ARMATURE')
    k = made_rest["pelvis"].translation.z / a2.data.bones["pelvis"].head_local.z
    rest = max((a2.data.bones[b].matrix_local.translation * k - m.translation).length for b, m in made_rest.items())
    rrot = max(math.degrees(a2.data.bones[b].matrix_local.to_quaternion().rotation_difference(m.to_quaternion()).angle) for b, m in made_rest.items())
    acts = {a.name: tuple(a.frame_range) for a in bpy.data.actions}
    out = {"objects": [o.name for o in sc.objects], "armature": a2.name, "units_x": round(k, 4), "rest_joint_err_cm": round(rest, 4),
           "rest_turn_err_deg": round(min(rrot, 360.0 - rrot), 4), "takes": acts}
    errs = {}
    for (name, fi), pos in probe.items():
        act = next((a for a in bpy.data.actions if a.name.endswith("|" + name)), None)
        if act is None: continue
        a2.animation_data_create(); a2.animation_data.action = act
        if hasattr(a2.animation_data, "action_slot") and act.slots: a2.animation_data.action_slot = act.slots[0]
        sc.frame_set(int(round(act.frame_range[0])) + fi); bpy.context.view_layer.update()
        e = max((a2.pose.bones[b].head * k - p).length for b, p in pos.items() if b in a2.pose.bones)
        errs[f"{name}@{fi}"] = round(e, 3)
    out["frame_joint_err_cm"] = errs
    # the NPC FBX's own reference pose, read the same way
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=NPC_FBX)
    a3 = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
    out["npc_vs_made_rest_cm"] = round(max((a3.data.bones[b].matrix_local.translation - m.translation).length for b, m in made_rest.items()), 4)
    out["npc_vs_made_rest_deg"] = round(max(min(a, 360.0 - a) for a in (math.degrees(a3.data.bones[b].matrix_local.to_quaternion().rotation_difference(m.to_quaternion()).angle) for b, m in made_rest.items())), 4)
    log("FBX read back:", json.dumps(out))
    return out


main()
