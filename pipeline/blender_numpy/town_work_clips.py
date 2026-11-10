"""Looping work clips for Brokenspire's townsfolk (the NPC packs' bodies on the UE5 Manny skeleton; their packs ship only
idle / walk / run / jump):
  Stir       2.4 s: at a cooking pot, both fists on a long ladle (right above left, 15 cm apart along it), the hands' middle
             going once round a horizontal circle (STIR_R) in front of her, a slight forward lean
  Crank      2.0 s: at the end of a roasting spit, knees bent, the right fist on the crank's handle going once round a
             vertical circle square to her facing, the left hand resting on her left thigh
  Tend       3.2 s: gardening in a deep squat (knees wide, feet flat: down on one knee the hand could not reach the soil),
             the right hand reaching to the soil in front, closing on a weed, pulling it up and tossing it aside; the left
             hand resting on the left knee; looking down
  Scatter    2.6 s: feeding animals: the left forearm across the waist with a bowl in the palm (tipped toward her middle,
             the bowl upright on it), the right hand dipping into it and throwing grain forward and to her right in a sweep
  SitDrink   6.0 s: seated on a 45 cm bench, forearms on a 75 cm table, a mug in the right hand raised to the mouth once
  SitTalk    5.0 s: seated the same way, a gesture with the right hand, then the left, a nod with each
  CarryWalk  MM_Walk_Fwd's length: the walk's legs, pelvis, spine and head exactly (frame for frame, in place: the root
             stays at the origin, as the game plays it with the root locked), the arms carrying a tray in front, the
             palms under it tipped in toward each other (flat up, the forearms would turn past their limit), the tray
             resting on the hands' highest skin
  CarryIdle  3.0 s: MM_Idle's body (a 3 s window of it, closed into a loop) with the same tray arms
  Talk       5.0 s: MM_Idle's body (a 5 s window), open-hand gestures with alternating hands, a small turn of the
             shoulders, nods
Each loops: its last frame is its first.
How the poses are made (crowd_clips.py's machinery, copied here because that script runs on import): the mesh's bones do
not point along their own Y in Blender, so every pose is made on a stand-in armature with the same joints and each bone
pointing at its child, and carried over bone by bone as the same turn from the reference pose. The arms are solved every
frame by rogue_clips.solve_arm (the elbow a hinge taken from Manny's own bent reference arm, the wrist within its limits,
half the hand's twist on lowerarm_twist_01, the arm's bone line kept ARM_CLEAR off the torso's skin), the hand turned
exactly as the clip asks (its axis and its palm), the elbow kept near the previous frame's. Where a hand holds something
the place given is the thing's (the fist's hole on a ladle or a crank handle, the palm on a tray, a bowl, a knee or a
mug), worked out from the hand's own skin; what the hand may turn about without letting go (a fist about its handle, a
palm about the surface it lies on, the hand round a mug) is searched for the turn the arm bears best, frame by frame and
kept near the frame before; keyed hand turns are refined the same way (refine_q). A loop is solved round again until its
first frame comes out as it went in. Legs: standing clips keep the idle's feet where they stand (two-bone solve); the
seated and squatting legs are set and the pelvis moved until the skin, measured, sits on the bench (45 cm).
Measured on Body_Character01's skinned mesh (a clothed townsperson, skinned here to SKM_Manny's skeleton), every frame,
printed and written to town_work_clips.json: the wrists' worst angle past their limits (rogue_clips.over); the forearms and
hands inside the torso's skin (points more than 0.5 cm behind it, within TORSO_R of the spine chain) and inside the legs'
(more than LEG_DEEP behind it, near the leg's bones); the two hands' skins crossing; the feet sliding (each foot and
ball's largest move from frame 0); the loop seam (first against last frame, and the last step against the largest step
inside the clip); and per clip: the ladle grip, its axis, the circle's centre and the pot's middle (Stir); the crank
circle's centre, radius and plane as the fist's hole goes round, and the left palm against the thigh (Crank); where the
fingers touch the ground, the body's lowest point, the soles, the torso against the thighs (Tend); the bowl's point, the
throw's release and its direction (Scatter); the seat point (the lowest skin under her hips), the table top under the
forearms, the table edge, the mug's grip and the rim against the mouth at the sip (SitDrink, SitTalk); the tray's point
and normal at frame 0, how far it moves and tilts, and the left palm against the tray (CarryWalk, CarryIdle); for
CarryWalk, the legs', pelvis', spine's and head's turns against MM_Walk_Fwd's (0).
Positions are relative to the root (the skeleton's root bone at the origin) as (her right, forward, up) in cm and as UE
component-space vectors (UE = Blender (x, -y, z): she faces UE +Y, her right is UE -X). Sockets (a prop attached to a
hand bone) are given in UE's hand bone space: Blender's bone-local coordinates with y negated (UE's FBX converter writes
every local transform mirrored in Y); a socket's Z is the prop's axis (the ladle's shaft toward its tip, the mug's,
the tray's and the bowl's up), its X a way across it.
Writes <out_dir>/SK_Manny_Town_Work_Clips.fbx (the armature only, named root as the skeleton's root bone, centimetres,
30 fps, each clip a take; Interchange took the crowd clips' 30 fps FBX at 25 fps: the lengths here are the built ones),
<out_dir>/town_work_clips.json, and pictures into <out_dir>/preview (workbench: front, side and three-quarter at four
frames of each clip, with stand-in props placed from the sockets and placement numbers, one sheet per clip). Then reads
the FBX back and checks its reference pose and frames against the poses made.
Blender: -b -P town_work_clips.py -- SKM_Manny.fbx Body_Character01.fbx MM_Idle.fbx MM_Walk_Fwd.fbx out_dir [nopreview]
[only=Stir,Crank,...] (the four FBX exported from Unreal: the pack's mannequin, a townsperson's body, MM_Idle and
MM_Walk_Fwd; with only= the FBX is not written and the JSON is town_work_clips_partial.json, unless writefbx is given too: then
the FBX holds only those clips (the list of 2026-11-10's Sleep: its own out_dir, imported on its own by 914 sleep))
Sleep (the list of 2026-11-10: "if an NPC is supposed to be sleeping at night, have them sleep in their beds with a new animation
or clip in blender"): lying on her back, the pelvis tipped back a quarter turn (the whole body with it: her feet toward her
forward, her head behind), lowered until the lowest skin rests 1 cm over the root (the bed's top in the game), a slow breath
over 4 s (the chest and the head), the loop closed."""
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
MANNY_FBX, BODY_FBX, IDLE_FBX, WALK_FBX, OUT_DIR = argv[:5]
OPTS = argv[5:]
PREVIEW = "nopreview" not in OPTS
ONLY = next((o[5:].split(",") for o in OPTS if o.startswith("only=")), None)
WRITE_FBX = "writefbx" in OPTS
SLEEP_LEN = 4.0
PREV_DIR = os.path.join(OUT_DIR, "preview")
FPS = 30
F, U, LEAN, OUT = C.F, C.U, C.LEAN, C.OUT
RT = OUT["r"]                                         # her right (Blender -X)
Y = Vector((0.0, 1.0, 0.0))
I3 = Vector((1.0, 1.0, 1.0))
FINGERS = C.FINGERS + ("thumb",)
SPINE = (("spine_01", 0.16), ("spine_02", 0.18), ("spine_03", 0.20), ("spine_04", 0.24), ("spine_05", 0.22))
NECK = (("neck_01", 0.35), ("neck_02", 0.30), ("head", 0.35))
CHAIN = ("pelvis", "spine_01", "spine_02", "spine_03", "spine_04", "spine_05", "neck_01", "neck_02", "head")
TORSO_R = 22.0      # a point behind the torso's skin counts as inside only this near the spine chain (cm; clothes' open sheets)
LEG_DEEP = 1.0      # a hand or forearm point this far behind a leg's skin (and near its bones) is inside it (cm)
HAND_DEEP = 3.0     # a point further than this behind a hand's skin is not inside it (a hand is about 3 cm thick)

# ---- the clips' places (cm, from the root: her right, forward, up) and timing
# (Manny's arm is 55 cm from the shoulder to the wrist: with the circle 46 cm out and 11 wide and a lean of 9 degrees the
# arms fell 9 to 11 cm short at its far side, locked straight, and the forearms lay across the belly)
STIR_LEN, STIR_C, STIR_R, STIR_GAP = 2.4, (0.0, 42.0, 97.0), 10.0, 16.0   # the hands' middle's circle; the hands apart along the ladle
STIR_LEAN, STIR_CURL = 16.0, 0.75
CRANK_TAU = 30.0                                      # (the handle slants this far across the fist)
STIR_TILT = 0.45                                      # the ladle's shaft: down and this much forward (its tip ahead of the hands, the lower hand further out)
STIR_TIP_BELOW = 70.0                                 # the ladle's tip this far below the hands' middle
LADLE_R = 1.7                                         # the handle's radius (the fist closed on it)
# (at 78 cm and 42 out the fist fell short of the circle's bottom by up to 21 cm with a 24 degree lean)
# (12 cm to her right, the forearm crossed the belly at the circle's left side)
CRANK_LEN, CRANK_C, CRANK_R = 2.0, (17.0, 40.0, 80.0), 14.0
TEND_LEN = 3.2
SCATTER_LEN = 2.6
SIT_LEN_DRINK, SIT_LEN_TALK = 6.0, 5.0
SEAT_Z, TABLE_Z = 45.0, 75.0
MUG_R, MUG_H = 4.3, 11.0
CARRY_IDLE_LEN, TALK_LEN = 3.0, 5.0
# the palms' middle point (each palm TRAY_HALF to its side); the tray rests on the hands' highest skin, measured, which
# with the palms tipped in stands about 5 cm over it: the tray's bottom then about 105 cm up
TRAY_AT, TRAY_HALF = (0.0, 35.0, 100.0), 13.0
TRAY_BOB = 0.35                                       # the tray follows this share of the chest's bob in the walk
# (the upper arm's turn about itself allowed to 60 degrees: rogue_clips' 40 is for the Rogue's cape, which townsfolk
# do not wear; held to 40 the stirring elbows folded in)
R.ARM_ROLL = 60.0
# (the arm's bone line kept this far off the torso's skin (cm): the townsfolk's puffy sleeves stand up to 12 cm off the
# forearm bone at the elbow; at rogue_clips' 3 to 4 cm the sleeves went 5 to 6 cm into the ribs with the elbows bent)
R.ARM_CLEAR = {"upper": 5.0, "elbow": 8.0, "fore": 7.0, "wrist": 4.0}


def log(*a): print("TOWN", *a, flush=True)


def her(v): return (v.dot(RT), v.dot(F), v.dot(U))
def from_her(r, f, u): return RT * r + F * f + U * u
def ue(v): return [round(v.x, 2), round(-v.y, 2), round(v.z, 2)]
def rnd(t, n=2): return [round(float(x), n) for x in t]


# ---------------------------------------------------------------- loading
def import_fbx(path):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    return [o for o in bpy.context.scene.objects if o not in before]


def drop_empties(objs):
    for o in [o for o in objs if o.type == 'EMPTY']:
        for ch in list(o.children): ch.parent = None
        bpy.data.objects.remove(o, do_unlink=True)


def load():
    """SKM_Manny's skeleton (the armature exported, named root as its root bone) with Body_Character01's mesh skinned to it"""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    new = import_fbx(MANNY_FBX)
    arm = next(o for o in new if o.type == 'ARMATURE')
    for o in [o for o in new if o.type == 'MESH']: bpy.data.objects.remove(o, do_unlink=True)
    drop_empties([o for o in sc.objects if o.type == 'EMPTY'])
    arm.matrix_world = Matrix.Identity(4)
    new = import_fbx(BODY_FBX)
    barm = next(o for o in new if o.type == 'ARMATURE'); mesh = next(o for o in new if o.type == 'MESH')
    drop_empties([o for o in new if o.type == 'EMPTY'])
    # (the body's own skeleton differs from Manny's only at the balls of the feet, 2.1 cm; its mesh follows Manny's)
    drest = max((barm.data.bones[b.name].head_local - b.head_local).length for b in arm.data.bones if b.name in barm.data.bones)
    mesh.parent = arm; mesh.matrix_parent_inverse.identity(); mesh.matrix_world = Matrix.Identity(4)
    for m in mesh.modifiers:
        if m.type == 'ARMATURE': m.object = arm
    bpy.data.objects.remove(barm, do_unlink=True)
    sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 0.01
    sc.render.fps = FPS; sc.render.fps_base = 1.0
    for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'; pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    zs = [v.co.z for v in mesh.data.vertices]
    log("skeleton", arm.name, len(arm.data.bones), "bones; body", mesh.name, len(mesh.data.vertices), "vertices, %.1f to %.1f cm high;"
        " its own skeleton's joints differ from Manny's by up to %.2f cm" % (min(zs), max(zs), drest))
    return sc, arm, mesh


def order(arm): return sorted(arm.pose.bones, key=lambda pb: len(pb.parent_recursive))


def set_world(arm, W):
    """each bone's armature-space matrix as W says (the basis worked out from the parents', no update between bones)"""
    for pb in arm.pose.bones:
        b = pb.bone
        base = b.matrix_local if b.parent is None else W[b.parent.name] @ (b.parent.matrix_local.inverted() @ b.matrix_local)
        pb.matrix_basis = base.inverted() @ W[b.name]
    bpy.context.view_layer.update()


def world(arm): return {pb.name: pb.matrix.copy() for pb in arm.pose.bones}


def basis_of(arm, W):
    """the pose's basis per bone (loc, rot, scale): a translation on the bones without a parent and where a clip moves a
    bone off its reference offset (the ik bones); elsewhere what is left is rounding, dropped"""
    out = {}
    for pb in arm.pose.bones:
        b = pb.bone
        base = b.matrix_local if b.parent is None else W[b.parent.name] @ (b.parent.matrix_local.inverted() @ b.matrix_local)
        l, q, s = (base.inverted() @ W[b.name]).decompose()
        if b.parent is not None and l.length < 0.01: l = Vector((0.0, 0.0, 0.0))
        out[b.name] = (l, q.normalized(), Vector((1.0, 1.0, 1.0)))
    return out


def set_basis(arm, P):
    for pb in arm.pose.bones:
        l, q, s = P[pb.name]; pb.location = l; pb.rotation_quaternion = q; pb.scale = s
    bpy.context.view_layer.update()


def read_clip(arm, path):
    """an Unreal clip's frames as the mesh skeleton's armature-space matrices (local turns carried over; the root's
    own motion, on the armature object, left out: in place)"""
    sc = bpy.context.scene
    new = import_fbx(path)
    ia = next(o for o in new if o.type == 'ARMATURE')
    act = ia.animation_data.action
    f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
    k = arm.data.bones["pelvis"].head_local.z / ia.data.bones["pelvis"].head_local.z
    out, err, roots = [], 0.0, []
    for f in range(f0, f1 + 1):
        sc.frame_set(f); bpy.context.view_layer.update()
        Wa = {pb.name: pb.matrix.copy() for pb in ia.pose.bones}
        W = {}
        for pb in order(arm):
            b = pb.name; bone = pb.bone
            if b not in Wa: W[b] = bone.matrix_local.copy(); continue
            if bone.parent is None: W[b] = Matrix.LocRotScale(Wa[b].translation * k, Wa[b].to_quaternion(), I3)
            else:
                # (the clip's own local translation: the ik bones are moved by it, the others keep their reference offsets)
                p = bone.parent.name; rel = Wa[p].inverted() @ Wa[b]
                W[b] = W[p] @ Matrix.LocRotScale(rel.translation * k, rel.to_quaternion(), I3)
        err = max(err, max((W[b].translation - Wa[b].translation * k).length for b in W if b in Wa))
        out.append(W); roots.append((ia.location.copy() * 100.0, tuple(ia.rotation_euler)))
    for o in new: bpy.data.objects.remove(o, do_unlink=True)
    for a in list(bpy.data.actions): bpy.data.actions.remove(a)
    travel = (roots[-1][0] - roots[0][0]).length
    rot = max(max(abs(x) for x in r[1]) for r in roots)
    log("read %s: %d frames (%d..%d), units x%.3f; its joints rebuilt on the mesh's skeleton within %.3f cm; the root (left out)"
        " travels %.1f cm, turns at most %.4f rad" % (os.path.basename(path), len(out), f0, f1, k, err, travel, rot))
    return out, {"frames": len(out), "joint_rebuild_err_cm": round(err, 4), "root_travel_cm": round(travel, 1), "root_turn_rad_max": round(rot, 5)}


# ---------------------------------------------------------------- the stand-in armature
MAIN_CHILD = {a: b for a, b in zip(CHAIN[:-1], CHAIN[1:])}
for s in "lr":
    MAIN_CHILD.update({f"clavicle_{s}": f"upperarm_{s}", f"upperarm_{s}": f"lowerarm_{s}", f"lowerarm_{s}": f"hand_{s}",
                       f"hand_{s}": f"middle_01_{s}", f"thigh_{s}": f"calf_{s}", f"calf_{s}": f"foot_{s}", f"foot_{s}": f"ball_{s}"})
    for fn in FINGERS:
        MAIN_CHILD[f"{fn}_01_{s}"] = f"{fn}_02_{s}"; MAIN_CHILD[f"{fn}_02_{s}"] = f"{fn}_03_{s}"
        if fn != "thumb": MAIN_CHILD[f"{fn}_metacarpal_{s}"] = f"{fn}_01_{s}"


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
        elif b.parent is not None and b.parent.name in dirs:          # (the fingers' tips, twist and corrective bones: their parent's way)
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
        set_world(self.h, {b: Matrix.LocRotScale(Wr[b].translation, Wr[b].to_quaternion() @ self.Rr0[b].inverted() @ self.Rh0[b], I3) for b in Wr})

    def from_helper(self):
        Wh = world(self.h)
        return {b: Matrix.LocRotScale(Wh[b].translation, Wh[b].to_quaternion() @ self.Rh0[b].inverted() @ self.Rr0[b], I3) for b in Wh}

    def helper_rot(self, Wr, b): return Wr[b].to_quaternion() @ self.Rr0[b].inverted() @ self.Rh0[b]


def hand_frame(h, ctx, hand):
    """the hand's own ways as posed: along it (wrist to knuckles), across it toward the index, its palm's normal"""
    P = h.pose.bones; s = hand[-1]; q = P[hand].matrix.to_quaternion()
    ax = q @ Y; pn = q @ ctx["palm"][hand]; pn = (pn - ax * pn.dot(ax)).normalized()
    ac = P[f"index_01_{s}"].head - P[f"pinky_01_{s}"].head; ac = (ac - ax * ac.dot(ax) - pn * ac.dot(pn)).normalized()
    return ax, ac, pn


def ops_apply(h, spec, ctx):
    """turns on top of the pose the bones have, parents first: ('rot', axis, deg) about the bone's head, ('move', v),
    ('flex', deg) a finger toward the palm about the knuckles' line, ('aim', along, across, palm) a thumb bone pointed
    that way in the hand's frame (crowd_clips.ops_apply)"""
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


def point(h, name, d):
    """the stand-in bone turned (the shortest way) to point along d"""
    pb = h.pose.bones[name]; M = pb.matrix.copy(); q = M.to_quaternion()
    pb.matrix = Matrix.LocRotScale(M.translation, (q @ Y).rotation_difference(d.normalized()) @ q, M.to_scale())
    bpy.context.view_layer.update()


def set_rot(h, name, q):
    pb = h.pose.bones[name]; M = pb.matrix.copy(); pb.matrix = Matrix.LocRotScale(M.translation, q, M.to_scale())
    bpy.context.view_layer.update()


def leg_ik(h, s, ankle, pole, foot_q):
    """the leg bent so the ankle is at `ankle`, the knee toward `pole`, the foot turned foot_q (world)"""
    P = h.pose.bones; Bh = h.data.bones
    a = (Bh[f"calf_{s}"].head_local - Bh[f"thigh_{s}"].head_local).length
    b = (Bh[f"foot_{s}"].head_local - Bh[f"calf_{s}"].head_local).length
    H = P[f"thigh_{s}"].head.copy(); d = ankle - H; dist = min(d.length, (a + b) * 0.9995); dn = d.normalized()
    pp = pole - dn * pole.dot(dn); pp.normalize()
    c = max(-1.0, min(1.0, (a * a + dist * dist - b * b) / (2 * a * dist)))
    K = H + (dn * c + pp * math.sqrt(1.0 - c * c)) * a
    point(h, f"thigh_{s}", K - H); point(h, f"calf_{s}", H + dn * dist - K)
    set_rot(h, f"foot_{s}", foot_q)
    return d.length - (a + b)


def keep_feet(h, feet):
    """the legs bent so each ankle stays where `feet` has it (the foot turned as it was), the knee bending the way it did"""
    P = h.pose.bones
    for s in "lr":
        T, qf = feet[s]; pole = P[f"calf_{s}"].head - P[f"thigh_{s}"].head
        dn = (T - P[f"thigh_{s}"].head).normalized(); pole = pole - dn * pole.dot(dn)
        if pole.length < 1e-3: pole = F.copy()
        leg_ik(h, s, T, pole + F * 0.05, qf)


# ---------------------------------------------------------------- hands
OPEN_THUMB = ((0.80, 0.55, -0.10), (0.92, 0.38, -0.20), (0.97, 0.22, -0.20))
FIST_THUMB = ((0.60, 0.20, 0.75), (0.20, -0.75, 0.60), (0.0, -0.95, 0.30))
FIST = (85.0, 100.0, 65.0)


def fingers(side, curl, thumb=None, spread=0.0):
    """curl 0 the reference hand's (Manny's: a little curled), 1 a fist (FIST: knuckles, middle joints, tips), below 0
    straightened; thumb 0 laid along the index (open), 1 across the fingers (fist); default as the curl"""
    sp = {}
    for fn in C.FINGERS:
        for i, k in enumerate(("01", "02", "03")):
            a = curl * FIST[i] if curl >= 0.0 else curl * 80.0 * (0.4, 1.0, 0.8)[i]     # (-0.15: crowd_clips' open hand)
            sp[f"{fn}_{k}_{side}"] = [("flex", a)]
    t = max(0.0, min(1.0, curl if thumb is None else thumb))
    for i, k in enumerate(("01", "02", "03")):
        v = Vector(OPEN_THUMB[i]).lerp(Vector(FIST_THUMB[i]), t).normalized()
        sp[f"thumb_{k}_{side}"] = [("aim", v.x, v.y, v.z)]
    return sp


# ---------------------------------------------------------------- posing
class Poser:
    """a pose made on the stand-in: start from a frame of the mesh skeleton, the body's turns, the legs, the fingers, the
    arms solved; finish() gives it back as the mesh skeleton's armature-space matrices"""
    def __init__(self, rig, ctx, idle_W):
        self.rig, self.ctx, self.h, self.idle_W = rig, ctx, rig.h, idle_W
        rig.to_helper(idle_W)
        P = self.h.pose.bones
        self.idle_feet = {s: (P[f"foot_{s}"].head.copy(), P[f"foot_{s}"].matrix.to_quaternion()) for s in "lr"}
        self.idle_ball = {s: P[f"ball_{s}"].matrix.to_quaternion() for s in "lr"}
        self.idle_ball_z = {s: P[f"ball_{s}"].head.z for s in "lr"}
        self.rest_foot = {s: self.h.data.bones[f"foot_{s}"].matrix_local.to_quaternion() for s in "lr"}

    def start(self, W=None):
        self.rig.to_helper(W if W is not None else self.idle_W)

    def body(self, lean=0.0, twist=0.0, look=0.0, tilt=0.0, clav=None, keep_head=0.45, turn_head=0.0):
        """lean forward and twist toward her right over the spine (deg), the head nodded down by `look`, tilted to her
        right by `tilt`; the neck takes back `keep_head` of the lean (her eyes stay up); clav: {side: (up, forward) deg}"""
        sp = {}
        for b, w in SPINE: sp[b] = [("rot", U, -twist * w), ("rot", LEAN, lean * w), ("rot", F, tilt * w)]
        for b, w in NECK: sp[b] = [("rot", LEAN, (-lean * keep_head + look) * w), ("rot", U, -turn_head * w)]
        ops_apply(self.h, sp, self.ctx)
        # (the shoulders raised and drawn forward about the chest's own ways, as the spine has turned it: about the
        # world's up, a torso leaning 47 degrees had its shoulder raised over its neck instead of brought forward)
        P = self.h.pose.bones; up_t = (P["neck_01"].head - P["spine_05"].head).normalized(); sp = {}
        for s, (up, fw) in (clav or {}).items():
            lat = (P[f"upperarm_{s}"].head - P[f"clavicle_{s}"].head); lat = (lat - up_t * lat.dot(up_t)).normalized()
            sp[f"clavicle_{s}"] = [("rot", lat.cross(up_t).normalized(), up), ("rot", up_t, fw if s == "r" else -fw)]
        if sp: ops_apply(self.h, sp, self.ctx)

    def pelvis(self, move=None, pitch=0.0, twist=0.0):
        sp = {"pelvis": []}
        if move is not None: sp["pelvis"].append(("move", move))
        if pitch: sp["pelvis"].append(("rot", LEAN, pitch))
        if twist: sp["pelvis"].append(("rot", U, -twist))
        ops_apply(self.h, sp, self.ctx)

    def keep_feet(self): keep_feet(self.h, self.idle_feet)

    def hands(self, spec):
        for pb in self.h.pose.bones:                              # (the fingers from their reference shape)
            if pb.name.split("_")[0] in FINGERS and pb.name[-1] in "lr" and any(k.endswith(pb.name[-2:]) for k in spec):
                pb.matrix_basis.identity()
        bpy.context.view_layer.update()
        ops_apply(self.h, spec, self.ctx)

    def reach(self, side, wrist, pole, want=None, exact=None):
        """the arm solved so the wrist (the hand's root) is at `wrist` (armature space), the hand as `exact` says
        ({front, up}) or as near `want` as the wrist allows"""
        at = her(wrist - self.h.pose.bones["neck_01"].head)
        R.solve_arm(self.h, self.ctx, side, ("reach", at, pole, want, exact))
        self.ctx.setdefault("prev_arm", {})[side] = self.h.pose.bones[f"upperarm_{side}"].matrix.to_quaternion()

    def hold(self, side, point_, q, local, pole):
        """the hand turned q (the stand-in hand's world turn) with its own point `local` (stand-in hand frame) at point_"""
        A = self.ctx["arms"][side]
        exact = {"front": q @ A["local"]["front"], "up": q @ A["local"]["up"]}
        self.reach(side, point_ - q @ local, pole, exact=exact)

    def hold_costs(self, side, point_, q_of, local, pole, cands):
        """for each c of `cands`: what the arm bears holding the fist turned q_of(c) at point_ (the wrist's cost and the
        arm against the torso); the arm is put back as it was after each"""
        P = self.h.pose.bones; ctx = self.ctx; A = ctx["arms"][side]
        names = [f"upperarm_{side}", f"lowerarm_{side}", f"hand_{side}", f"lowerarm_twist_01_{side}"]
        saved = {n: P[n].matrix_basis.copy() for n in names}
        pa = ctx.get("prev_arm", {}).get(side)
        out = []
        for c in cands:
            for n in names: P[n].matrix_basis = saved[n]
            bpy.context.view_layer.update()
            if pa is not None: ctx["prev_arm"][side] = pa
            self.hold(side, point_, q_of(c), local, pole)
            w = R.wrist_of(A, P[f"lowerarm_{side}"].matrix.to_quaternion(), P[f"hand_{side}"].matrix.to_quaternion())
            out.append((R.wrist_cost(*w) + 4.0 * arm_torso_cost(self.h, ctx, side), R.over(*w)))
        for n in names: P[n].matrix_basis = saved[n]
        bpy.context.view_layer.update()
        if pa is not None: ctx["prev_arm"][side] = pa
        else: ctx.get("prev_arm", {}).pop(side, None)
        return out

    def hold_free(self, side, point_, q_of, local, pole, cands, prev=None, anchor=None):
        """a fist on a handle: the hand turned q_of(c) for the c among `cands` the arm bears best (hold_costs), near the
        previous frame's c and the clip's own (anchor), its point `local` at point_; returns that c"""
        costs = self.hold_costs(side, point_, q_of, local, pole, cands)
        best = None
        wrap = lambda d: (d + 180.0) % 360.0 - 180.0
        for c, (cost, ov) in zip(cands, costs):
            if prev is not None: cost += 0.004 * wrap(c[0] - prev[0]) ** 2 + (0.0 if c[1:] == prev[1:] else 30.0)
            if anchor is not None: cost += 0.002 * wrap(c[0] - anchor[0]) ** 2
            if best is None or cost < best[0]: best = (cost, c)
        self.hold(side, point_, q_of(best[1]), local, pole)
        return best[1]

    def finish(self):
        W = self.rig.from_helper()
        for ik, b, rel in self.ctx["ik_follow"]: W[ik] = W[b] @ rel
        return W


def arm_torso_cost(h, ctx, side):
    """the arm as posed against the torso's skin (rogue_clips' keep-out: the bone line ARM_CLEAR off the skin)"""
    if not ctx.get("torso_pts"): return 0.0
    P = h.pose.bones; TQ, TN = R.torso_now(h, ctx)
    S, E, Wr = P[f"upperarm_{side}"].head, P[f"lowerarm_{side}"].head, P[f"hand_{side}"].head
    c = 0.0
    for p_, m_ in ((S.lerp(E, 0.75), R.ARM_CLEAR["upper"]), (E, R.ARM_CLEAR["elbow"]), (E.lerp(Wr, 0.35), R.ARM_CLEAR["fore"]),
                   (E.lerp(Wr, 0.7), R.ARM_CLEAR["fore"]), (Wr, R.ARM_CLEAR["wrist"])):
        sh = R.body_short(TQ, TN, p_, m_, 1.0)
        if sh > 0.0: c += sh * sh
    return c


def grip_q(ctx, side, axis, psi, tau, flip=1.0):
    """a fist round a handle along `axis`: the handle runs across the knuckles (little finger to index), slanted tau
    degrees toward the fingers at the index's end (as in a fist), the fist rolled psi degrees about the handle"""
    t_l = ctx["across_l"][side]; ax_l = Y
    h_l = (t_l * math.cos(math.radians(tau)) + ax_l * math.sin(math.radians(tau))).normalized()
    a = axis.normalized() * flip
    return Quaternion(a, math.radians(psi)) @ h_l.rotation_difference(a)


def hand_q(ctx, side, axis, palm):
    """the stand-in hand's world turn with its axis (wrist to knuckles) and its palm's normal as given (palm first)"""
    A = ctx["arms"][side]; pn = palm.normalized(); ax = (axis - pn * axis.dot(pn)).normalized()
    return R.exact_hand(A, ax, pn)


def hand_q_across(ctx, side, across, palm):
    """the same from the way across the knuckles (little finger to index) and the palm"""
    pn = palm.normalized(); t = (across - pn * across.dot(pn)).normalized()
    return hand_q(ctx, side, ctx["hand_sign"][side] * pn.cross(t), pn)


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
        isfinger = lambda n: n.split("_")[0] in FINGERS
        self.hand = {s: verts(lambda n, s=s: n == f"hand_{s}" or (n.endswith("_" + s) and isfinger(n))) for s in "lr"}
        self.tips = {s: verts(lambda n, s=s: n.endswith("_" + s) and n.split("_")[0] in C.FINGERS and n.split("_")[1] in ("02", "03")) for s in "lr"}
        self.fore = {s: verts(lambda n, s=s: n in (f"lowerarm_{s}", f"lowerarm_twist_01_{s}")) for s in "lr"}
        self.torsov = verts(lambda n: n in CHAIN or n.startswith("clavicle"))
        self.headv = verts(lambda n: n in ("head", "neck_02"))
        self.legv = {s: verts(lambda n, s=s: n in (f"thigh_{s}", f"calf_{s}")) for s in "lr"}
        self.footv = {s: verts(lambda n, s=s: n in (f"foot_{s}", f"ball_{s}")) for s in "lr"}
        self.ballv = {s: verts(lambda n, s=s: n == f"ball_{s}") for s in "lr"}
        polys = [tuple(p.vertices) for p in me.polygons]
        def polys_of(idx):
            st = set(idx.tolist()); return [p for p in polys if all(i in st for i in p)]
        self.hand_polys = {s: polys_of(self.hand[s]) for s in "lr"}
        self.tip_polys = {s: polys_of(self.tips[s]) for s in "lr"}
        self.torso_polys = polys_of(self.torsov)
        self.leg_polys = polys_of(np.concatenate([self.legv["l"], self.legv["r"]]))
        self.leg_polys_s = {s: polys_of(self.legv[s]) for s in "lr"}
        self.armv = np.concatenate([self.fore["l"], self.fore["r"], self.hand["l"], self.hand["r"]])
        self.armside = np.array(["l"] * len(self.fore["l"]) + ["r"] * len(self.fore["r"]) + ["l"] * len(self.hand["l"]) + ["r"] * len(self.hand["r"]))
        log("mesh parts: hands %d / %d vertices, fingertips %d / %d, forearms %d / %d, torso %d (%d faces), legs %d faces" % (
            len(self.hand["l"]), len(self.hand["r"]), len(self.tips["l"]), len(self.tips["r"]), len(self.fore["l"]), len(self.fore["r"]),
            len(self.torsov), len(self.torso_polys), len(self.leg_polys)))
        # the palm: its normal from the skin over the hand bone (the mean normal of the palm side), and the point where a
        # ray from the hand's bone line (60 % of the way from the wrist to the middle knuckle) along it leaves the skin
        B = arm.data.bones; co0 = np.array([v.co[:] for v in me.vertices]); vl0 = [tuple(c) for c in co0]
        self.palm = {}; self.palm_n0 = {}
        for s in "lr":
            hb = B[f"hand_{s}"]; hh = hb.head_local; m1 = B[f"middle_01_{s}"].head_local
            a = (m1 - hh).normalized(); L = (m1 - hh).length
            along = (B[f"middle_03_{s}"].head_local - B[f"middle_01_{s}"].head_local).normalized()
            across = (B[f"index_01_{s}"].head_local - B[f"pinky_01_{s}"].head_local).normalized()
            n0 = along.cross(across).normalized()
            if s == "r": n0 = -n0
            n0 = (n0 - a * n0.dot(a)).normalized()
            idx = self.hand[s][np.isin(gname[self.hand[s]], [f"hand_{s}"] + [f"{fn}_metacarpal_{s}" for fn in C.FINGERS])]
            nrm = np.array([me.vertices[i].normal[:] for i in idx])
            pa = (co0[idx] - np.array(hh)) @ np.array(a)
            sel = (pa > 2.0) & (pa < 0.95 * L) & (nrm @ np.array(n0) > 0.5)
            n = Vector(nrm[sel].mean(0)); n = (n - a * n.dot(a)).normalized()
            bvh = BVHTree.FromPolygons(vl0, self.hand_polys[s])
            o = hh + a * (0.6 * L)
            hit = bvh.ray_cast(o, n, 20.0); back = bvh.ray_cast(o, -n, 20.0)
            self.palm_n0[s] = n
            M0 = hb.matrix_local
            self.palm[s] = (M0.inverted() @ hit[0], M0.to_quaternion().inverted() @ n)
            log("palm %s: its skin faces %.0f deg off the way the finger bones give (%d vertices); the skin %.1f cm off the bone line, %.1f on the back"
                % (s, math.degrees(n.angle(n0)), int(sel.sum()), hit[3], back[3] if back[0] else -1))

    def coords(self):
        dg = bpy.context.evaluated_depsgraph_get(); ev = self.mesh.evaluated_get(dg); m = ev.to_mesh()
        co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", co); ev.to_mesh_clear()
        return co.reshape(-1, 3)

    @staticmethod
    def signed(bvh, pts):
        out = []
        for p in pts:
            loc, nrm, idx, dist = bvh.find_nearest(Vector(p))
            out.append(99.0 if loc is None else (dist if (Vector(p) - loc).dot(nrm) >= 0.0 else -dist))
        return np.array(out)

    def palm_at(self, W, s):
        """the palm's skin point and its normal as posed"""
        M = W[f"hand_{s}"]; return M @ self.palm[s][0], (M.to_quaternion() @ self.palm[s][1]).normalized()

    def inside_points(self, W, co):
        """the forearm and hand points the frame counts as inside the torso or the legs (for the pictures' red marks)"""
        vl = [tuple(c) for c in co]; P = co[self.armv]
        chain = [W[b].translation for b in CHAIN]
        sd = self.signed(BVHTree.FromPolygons(vl, self.torso_polys), P)
        dsp = np.min([seg_dist_np(P, c0, c1) for c0, c1 in zip(chain[:-1], chain[1:])], axis=0)
        sl = self.signed(BVHTree.FromPolygons(vl, self.leg_polys), P)
        segs = []
        for s in "lr":
            segs += [(W[f"thigh_{s}"].translation, W[f"calf_{s}"].translation), (W[f"calf_{s}"].translation, W[f"foot_{s}"].translation)]
        dl = np.min([seg_dist_np(P, a, b) for a, b in segs], axis=0)
        return P[((sd < -0.5) & (dsp < TORSO_R)) | ((sl < -LEG_DEEP) & (dl < 14.0))]

    def frame(self, W, co, legs=True):
        r = {}
        worst = 0.0
        for s in "lr":
            A = self.ctx["arms"][s]
            w = R.wrist_of(A, self.rig.helper_rot(W, f"lowerarm_{s}"), self.rig.helper_rot(W, f"hand_{s}"))
            worst = max(worst, R.over(*w)); r[f"wrist_{s}"] = [round(v, 1) for v in w]
        r["wrist_over"] = worst
        vl = [tuple(c) for c in co]
        chain = [W[b].translation for b in CHAIN]
        body = BVHTree.FromPolygons(vl, self.torso_polys)
        P = co[self.armv]
        sd = self.signed(body, P)
        dsp = np.min([seg_dist_np(P, c0, c1) for c0, c1 in zip(chain[:-1], chain[1:])], axis=0)
        near = dsp < TORSO_R
        inside = (sd < -0.5) & near
        r["arm_in_body"] = float(sd[near].min()) if near.any() else 99.0; r["arm_in_body_n"] = int(inside.sum())
        if inside.any():
            i = int(np.argmin(np.where(inside, sd, 99.0)))
            r["arm_in_body_at"] = (str(self.gname[self.armv[i]]), round(float(sd[i]), 1), rnd(her(Vector(P[i])), 1))
        if legs:
            # (the hands and forearms against the legs' skin: a point behind it counts when near the leg's bones)
            lb = BVHTree.FromPolygons(vl, self.leg_polys)
            sl = self.signed(lb, P)
            segs = []
            for s in "lr":
                segs += [(W[f"thigh_{s}"].translation, W[f"calf_{s}"].translation), (W[f"calf_{s}"].translation, W[f"foot_{s}"].translation)]
            dl = np.min([seg_dist_np(P, a, b) for a, b in segs], axis=0)
            nl = dl < 14.0
            r["arm_in_legs"] = float(sl[nl].min()) if nl.any() else 99.0
            ins = (sl < -LEG_DEEP) & nl
            r["arm_in_legs_n"] = int(ins.sum())
            if ins.any():
                i = int(np.argmin(np.where(ins, sl, 99.0)))
                r["arm_in_legs_at"] = (str(self.gname[self.armv[i]]), round(float(sl[i]), 1), rnd(her(Vector(P[i])), 1))
        bl = BVHTree.FromPolygons(vl, self.hand_polys["l"]); br = BVHTree.FromPolygons(vl, self.hand_polys["r"])
        r["hands_cross"] = len(bl.overlap(br))
        return r


def seg_dist_np(P, a, b):
    a, b = np.array(a), np.array(b); ab = b - a
    t = np.clip((P - a) @ ab / max(float(ab @ ab), 1e-9), 0.0, 1.0)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


# ---------------------------------------------------------------- keyed tracks
def ease(u): return u * u * (3.0 - 2.0 * u)


def angdeg(q1, q2):
    a = math.degrees(q1.rotation_difference(q2).angle); return min(a, 360.0 - a)


def mix(a, b, u):
    if isinstance(a, Quaternion):
        if a.dot(b) < 0.0: b = -b
        return a.slerp(b, u)
    if isinstance(a, Vector): return a.lerp(b, u)
    if isinstance(a, tuple): return tuple(mix(x, y, u) for x, y in zip(a, b))
    return a + (b - a) * u


class Track:
    """values at times (eased from key to key: each key a stop, as crowd_clips' poses); the last key equals the first"""
    def __init__(self, keys): self.k = list(keys)
    def __call__(self, t):
        k = self.k
        if t <= k[0][0]: return k[0][1]
        for (t0, a), (t1, b) in zip(k[:-1], k[1:]):
            if t <= t1 + 1e-9: return mix(a, b, ease(min(1.0, max(0.0, (t - t0) / (t1 - t0)))))
        return k[-1][1]


def through(pts, t):
    """a point moving through `pts` [(time, Vector)] without stopping at them (Catmull-Rom, the times uneven; the
    list a loop: the last equals the first)"""
    n = len(pts) - 1; L = pts[-1][0]
    j = max(i for i in range(n) if pts[i][0] <= t + 1e-9) if t < L else n - 1
    g = lambda i: (pts[i % n][0] + L * (i // n), pts[i % n][1])
    (t0, p0), (t1, p1), (t2, p2), (t3, p3) = g(j - 1), g(j), g(j + 1), g(j + 2)
    u = (t - t1) / (t2 - t1)
    m1 = (p2 - p0) * ((t2 - t1) / (t2 - t0)); m2 = (p3 - p1) * ((t2 - t1) / (t3 - t1))
    h00 = 2 * u ** 3 - 3 * u ** 2 + 1; h10 = u ** 3 - 2 * u ** 2 + u; h01 = -2 * u ** 3 + 3 * u ** 2; h11 = u ** 3 - u ** 2
    return p1 * h00 + m1 * h10 + p2 * h01 + m2 * h11


def bump(t, t0, t1, rise=0.25):
    """0 outside [t0, t1], 1 inside, eased in and out over `rise` seconds"""
    if t <= t0 or t >= t1: return 0.0
    return ease(min(1.0, (t - t0) / rise, (t1 - t) / rise))


# ---------------------------------------------------------------- the clips
class Build:
    """everything the clip makers share: the rig, the stand-in's context, the meter, the idle and the walk"""
    pass


def calib_hole(B, side, curl, thumb):
    """the fist's hole (where a handle lies): from the palm's skin along its normal to the curled fingers' skin; its
    centre in the mesh hand bone's frame and in the stand-in's, and its width"""
    P = B.poser; P.start(); P.hands(fingers(side, curl, thumb)); W = P.finish()
    set_world(B.arm, W); co = B.meter.coords(); vl = [tuple(c) for c in co]
    pt, n = B.meter.palm_at(W, side)
    bvh = BVHTree.FromPolygons(vl, B.meter.tip_polys[side])
    best = None
    ax = (W[f"middle_01_{side}"].translation - W[f"hand_{side}"].translation).normalized()
    for dx in (0.0, 1.0, 2.0, 3.0, 4.0):                           # (rays from the palm toward the knuckles: a handle lies near their line)
        o = pt + ax * dx + n * 0.05
        hit = bvh.ray_cast(o, n, 15.0)
        if hit[0] is not None and (best is None or hit[3] < best[0]): best = (hit[3], o)
    d, o = best if best else (2 * LADLE_R, pt)
    c = o + n * (d * 0.5)
    loc = W[f"hand_{side}"].inverted() @ c
    qh = B.rig.helper_rot(W, f"hand_{side}")
    loc_h = qh.inverted() @ (c - W[f"hand_{side}"].translation)
    return loc, loc_h, d


def palm_local(B, side, off=0.0):
    """the palm's skin point pushed `off` cm out along its normal, in the stand-in hand's frame (from the reference pose)"""
    rp, rn = B.meter.palm[side]
    hb = B.arm.data.bones[f"hand_{side}"]
    p = hb.matrix_local @ rp; n = hb.matrix_local.to_quaternion() @ rn
    Hh = B.h.data.bones[f"hand_{side}"].matrix_local
    return Hh.to_quaternion().inverted() @ (p + n * off - Hh.translation)


def mesh_local(B, side, loc_h):
    """a point in the stand-in hand's frame -> the mesh hand bone's rest-local frame"""
    Hh = B.h.data.bones[f"hand_{side}"].matrix_local
    p = Hh.translation + Hh.to_quaternion() @ loc_h
    return B.arm.data.bones[f"hand_{side}"].matrix_local.inverted() @ p


def socket(W, bone, P, Z, X):
    """a prop's frame (origin P, axis Z, X across) in the bone's frame: Blender's and UE's (y mirrored)"""
    M = W[bone]; Mi = M.inverted(); qi = M.to_quaternion().inverted()
    z = Z.normalized(); x = (X - z * X.dot(z)).normalized()
    p = Mi @ P; zl = qi @ z; xl = qi @ x
    return {"bone": bone, "location_ue": [round(p.x, 2), round(-p.y, 2), round(p.z, 2)],
            "x_axis_ue": [round(xl.x, 4), round(-xl.y, 4), round(xl.z, 4)], "z_axis_ue": [round(zl.x, 4), round(-zl.y, 4), round(zl.z, 4)],
            "_blender": (p, xl, zl)}


def socket_world(W, sk):
    """the prop's frame (as a matrix) where the socket puts it in pose W"""
    p, xl, zl = sk["_blender"]
    yl = zl.cross(xl)
    Ml = Matrix(((xl.x, yl.x, zl.x, p.x), (xl.y, yl.y, zl.y, p.y), (xl.z, yl.z, zl.z, p.z), (0, 0, 0, 1)))
    return W[sk["bone"]] @ Ml


def solve_frames(B, n, make, warm=12):
    """make(t) poses and returns W for each frame 0..n-1; frame n is frame 0 again (the loop closed exactly). The last
    `warm` frames are solved first, so frame 0 starts from the elbows (and fists) the loop runs into: solved cold,
    frame 0 to 1 jumped 20 to 32 degrees"""
    B.ctx["prev_arm"] = {}
    for i in range(max(0, n - warm), n): make(i / FPS)
    # (solved again from frame 0 until frame 0, solved after the last frame, comes out as it went in: the elbows' and
    # fists' choices then run round the loop; a warm-up alone left the last step 16 to 38 degrees)
    for p in range(4):
        Ws = [make(i / FPS) for i in range(n)]
        W0 = make(0.0)
        d = max(angdeg(W0[b].to_quaternion(), Ws[0][b].to_quaternion()) for b in B.arm_bones)
        log("loop pass %d: frame 0 after the last frame differs by %.2f deg" % (p + 1, d))
        if d < 0.5: break
    Ws.append(Ws[0])
    return Ws


def refine_q(B, side, point_, q0, local, pole, spread=40, step=20):
    """q0 turned about the palm's normal and the hand's own axis by up to `spread` degrees: the turn the arm bears best
    (the wrist, the arm against the torso), a little toward q0; returns it and its wrist's degrees past the limits"""
    P = B.poser; A = B.ctx["arms"][side]
    pn = q0 @ A["local"]["up"]; ax = q0 @ A["local"]["front"]
    cands = [(float(a), float(b)) for a in range(-spread, spread + 1, step) for b in range(-spread, spread + 1, step)]
    q_of = lambda c: Quaternion(pn, math.radians(c[0])) @ Quaternion(ax, math.radians(c[1])) @ q0
    costs = P.hold_costs(side, point_, q_of, local, pole, cands)
    i = min(range(len(cands)), key=lambda i: costs[i][0] + 0.002 * (cands[i][0] ** 2 + cands[i][1] ** 2))
    return q_of(cands[i]), costs[i][1]


def knee_contact(B, W, back):
    """the skin on top of the left knee as posed, `back` cm up the thigh from the joint: a ray onto it along the
    thigh's front (as the thigh carries its reference front); its point, its outward way (the face's, eased toward
    the front), the thigh's way down. (Placed from the knee's thickness measured standing, the palm sank into the bent
    knee and lifted clear it floated 6 cm over it)"""
    rq = AB_rest_q(B, "thigh_l")
    kn = W["calf_l"].translation; th = (kn - W["thigh_l"].translation).normalized()
    front = W["thigh_l"].to_quaternion() @ rq.inverted() @ F; front = (front - th * front.dot(th)).normalized()
    p0 = kn - th * back
    set_world(B.arm, W); co = B.meter.coords()
    hit = BVHTree.FromPolygons([tuple(c) for c in co], B.meter.leg_polys_s["l"]).ray_cast(p0 + front * 30.0, -front, 60.0)
    if hit[0] is None: return p0 + front * B.knee_top, front, th
    n = (hit[1].normalized() + front).normalized()
    return hit[0], n, th


# (the resting palm this far up the thigh from the knee joint; its fingers a little lifted: flat or curled, the ring and
# middle fingertips went 4 to 7 cm into the knee and the hand had to be lifted 5 to 8 cm clear, floating. A resting hand
# is lifted only until no point of it is more than REST_DEEP inside the leg: its fingertips then press the cloth)
KNEE_BACK, KNEE_CURL, REST_DEEP = 12.0, -0.12, 1.5


def hand_on_knee(B, W, pole, st, back):
    """the left hand resting on the left knee: the palm on the thigh's top `back` cm up from the knee joint, the fingers
    near flat toward the knee and turned out round its side, the hand turned on the thigh as the arm bears it best (laid
    on the kneecap, or curled over it, the middle fingertip went 4 to 7 cm into the bent knee)"""
    pt, nn, th = knee_contact(B, W, back)
    side = OUT["l"] - nn * OUT["l"].dot(nn) - th * OUT["l"].dot(th); side.normalize()
    along = th * math.cos(math.radians(35.0)) + side * math.sin(math.radians(35.0))
    return palm_on(B, "l", pt, nn, along, B.palm_loc["l"], pole, st, spread=40)


def palm_on(B, side, point_, normal, along, local, pole, st, spread=90):
    """the palm laid on a surface at point_ (its normal out of the surface), the hand turned about that normal as the
    arm bears it best (from `along`), near the frame before (st["v"]); keeps st"""
    P = B.poser; ctx = B.ctx
    q0 = hand_q(ctx, side, along, -normal)
    q_of = lambda c: Quaternion(normal, math.radians(c[0])) @ q0
    if st.get("v") is None: cands = [(float(a),) for a in range(-spread, spread + 1, 15)]
    else: cands = [((st["v"][0] + d),) for d in (-10, -5, 0, 5, 10)]
    st["v"] = P.hold_free(side, point_ + normal * st.get("lift", 0.3), q_of, local, pole, cands, st.get("v"), st.get("anchor"))
    if st.get("anchor") is None: st["anchor"] = st["v"]
    return st["v"]


# ---- Stir
def make_stir(B):
    ctx = B.ctx; P = B.poser
    a_s = (-U + F * STIR_TILT).normalized()                      # the shaft, down toward the tip
    loc_m, loc_h = {}, {}
    for s in "lr":
        loc_m[s], loc_h[s], d = calib_hole(B, s, STIR_CURL, 0.7)
        log("stir: the %s fist's hole %.1f cm wide (the handle %.1f)" % (s, d, 2 * LADLE_R))
    C0 = from_her(*STIR_C); n = int(round(STIR_LEN * FPS))
    hands = {}; hands.update(fingers("r", STIR_CURL, 0.7)); hands.update(fingers("l", STIR_CURL, 0.7))
    def mid(t):
        th = 2.0 * math.pi * t / STIR_LEN
        return C0 + (RT * math.cos(th) + F * math.sin(th)) * STIR_R, th
    # (each fist rolls about the shaft as the arm bears it best, frame by frame, kept near the frame before: with both
    # fists held at one turn the wrists went 22 to 34 degrees past their limits and the elbows folded in across the chest)
    # one roll and slant per fist for the whole clip, the one whose worst frame the arm bears best (searched over the
    # whole turn at eight frames); then each frame refines it a little, kept near it and near the frame before
    def body(t):
        M, th = mid(t)
        P.start(); P.body(lean=STIR_LEAN + 3.0 * math.sin(th), twist=7.0 * math.cos(th), look=12.0, tilt=1.5 * math.cos(th),
                          clav={"r": (0.0, 7.0 + 3.0 * math.sin(th)), "l": (0.0, 7.0 + 3.0 * math.sin(th))})
        P.keep_feet(); P.hands(hands)
        return M
    q_of = {s: (lambda c, s=s: grip_q(ctx, s, -a_s, c[0], c[1], c[2])) for s in "lr"}
    pole = {s: C.D(s, 1.0, 0.0, -0.6) for s in "lr"}
    grip_at = lambda M, s: M + a_s * ((-1.0 if s == "r" else 1.0) * STIR_GAP / 2)
    full = [(float(p), tau, 1.0) for tau in (-25.0, 0.0, 25.0) for p in range(0, 360, 15)]
    worst = {s: [0.0] * len(full) for s in "lr"}; overs = {s: [0.0] * len(full) for s in "lr"}
    ctx["prev_arm"] = {}
    for k in range(8):
        M = body(k * STIR_LEN / 8)
        for s in "rl":
            for i, (c_, ov) in enumerate(P.hold_costs(s, grip_at(M, s), q_of[s], loc_h[s], pole[s], full)):
                worst[s][i] = max(worst[s][i], c_); overs[s][i] = max(overs[s][i], ov)
    anchor = {}
    for s in "rl":
        i = int(np.argmin(worst[s])); anchor[s] = full[i]
        log("stir: the %s fist rolled %.0f deg, the handle slanted %.0f: the wrist at most %.1f deg past its limits over the sample frames" % (s, full[i][0], full[i][1], overs[s][i]))
    st = dict(anchor); B.short = {}; psis = {}
    def make(t):
        M = body(t)
        for s in "rl":
            g = grip_at(M, s)
            B.short[s] = max(B.short.get(s, -99.0), (g - B.h.pose.bones[f"upperarm_{s}"].head).length - 7.0 - B.ctx["arms"][s]["a"] - B.ctx["arms"][s]["b"])
            cands = [((st[s][0] + d) % 360.0, st[s][1], 1.0) for d in (-10, -5, -2.5, 0, 2.5, 5, 10)]     # (20 a frame spun the fist visibly)
            st[s] = P.hold_free(s, g, q_of[s], loc_h[s], pole[s], cands, st[s], anchor[s])
            psis.setdefault(s, []).append(st[s][0])
        return P.finish()
    Ws = solve_frames(B, n, make)
    log("stir: the fists' roll about the shaft over the clip: r %s, l %s; the arms %.1f / %.1f cm short at worst" % (
        rnd((min(psis["r"]), max(psis["r"])), 0), rnd((min(psis["l"]), max(psis["l"])), 0), B.short["r"], B.short["l"]))
    W0 = Ws[0]; G = W0["hand_r"] @ loc_m["r"]
    L_tip = (STIR_TIP_BELOW - STIR_GAP / 2 * abs(a_s.z)) / abs(a_s.z)       # (grip to tip along the shaft: the tip 70 cm under the hands' middle)
    tip_c = C0 - a_s * (STIR_GAP / 2) + a_s * L_tip
    sk = socket(W0, "hand_r", G, a_s, F)
    info = {"ladle_grip_r_root": {"her": rnd(her(G)), "ue": ue(G)}, "ladle_axis_root": {"her": rnd(her(a_s), 4), "ue": ue(a_s)},
            "ladle_tip_from_grip_cm": round(L_tip, 1), "hands_apart_along_ladle_cm": STIR_GAP, "handle_diameter_cm": 2 * LADLE_R,
            "hands_circle": {"centre_her": list(STIR_C), "centre_ue": ue(C0), "radius_cm": STIR_R, "turns": 1},
            "pot_middle_root": {"her": rnd(her(tip_c)), "ue": ue(tip_c), "note": "the ladle's tip circles it at the hands' radius"},
            "socket_ladle_hand_r": sk}
    def extra(i, W, co):
        Gr = W["hand_r"] @ loc_m["r"]; Gl = W["hand_l"] @ loc_m["l"]
        Mw = (Gr + Gl) * 0.5; Mt, _ = mid(i / FPS)
        line = (Gl - Gr).normalized()
        return {"grip_err": (Mw - Mt).length, "hands_apart": (Gl - Gr).length, "shaft_err_deg": math.degrees(line.angle(a_s)),
                "left_off_shaft": ((Gl - Gr) - a_s * (Gl - Gr).dot(a_s)).length}
    def summary(rows):
        return {"grip_middle_off_circle_cm_max": round(max(r["grip_err"] for r in rows), 2),
                "hands_apart_cm": rnd((min(r["hands_apart"] for r in rows), max(r["hands_apart"] for r in rows))),
                "left_fist_off_the_shaft_cm_max": round(max(r["left_off_shaft"] for r in rows), 2)}
    props = {"ladle": sk, "pot": tip_c}
    return Ws, info, extra, summary, props


# ---- Crank
def make_crank(B):
    ctx = B.ctx; P = B.poser
    loc_m, loc_h, d = calib_hole(B, "r", 0.62, 0.7)
    log("crank: the right fist's hole %.1f cm wide" % d)
    C0 = from_her(*CRANK_C); n = int(round(CRANK_LEN * FPS))
    def grip(t):
        th = 2.0 * math.pi * t / CRANK_LEN
        return C0 + (RT * math.cos(th) + U * math.sin(th)) * CRANK_R, th
    # the fist on the handle (the handle along her facing, slanted across the knuckles), rolled about it as the arm bears
    # it best frame by frame (the handle turns in the fist); the body dips and leans in as the handle goes down
    left_pt = B.thigh_pt
    hands = {}; hands.update(fingers("r", STIR_CURL, 0.7)); hands.update(fingers("l", KNEE_CURL, 0.2))
    def body(th):
        down = 0.5 * (1.0 - math.sin(th))                          # (1 at the circle's bottom)
        P.start(); P.body(lean=28.0 + 8.0 * down, twist=12.0 + 4.0 * math.cos(th), look=6.0, tilt=-2.0 * math.cos(th),
                          clav={"r": (-4.0 * down, 6.0 + 5.0 * down)})
        P.pelvis(move=-U * (11.0 + 7.0 * down))
        P.keep_feet(); P.hands(hands)
    lift = {"v": None, "anchor": None, "lift": 0.3}
    rq = AB_rest_q(B, "thigh_l")
    def left(W_):
        # the left palm on her left knee, just above the kneecap (laid on the thigh's front half way down, its fingertips
        # went 6.8 cm into the knee, and lifted clear the hand floated 6.7 cm off the thigh), turned on it as the arm
        # bears it best
        hand_on_knee(B, W_, C.D("l", 1.0, 0.0, 0.2), lift, KNEE_BACK)
    st = {"v": None}; psis = []
    def make(t):
        G, th = grip(t)
        body(th)
        cands = [(float(p), CRANK_TAU, fl) for p in range(0, 360, 15) for fl in (1.0, -1.0)] if st["v"] is None else \
                [((st["v"][0] + d) % 360.0, st["v"][1], st["v"][2]) for d in (-15, -10, -5, 0, 5, 10, 15)]
        st["v"] = P.hold_free("r", G, lambda c: grip_q(ctx, "r", F, c[0], c[1], c[2]), loc_h, C.D("r", 1.0, -0.2, -0.6), cands, st["v"])
        psis.append(st["v"][0])
        W_ = P.finish(); B.rig.to_helper(W_)
        left(W_)
        return P.finish()
    # (the resting hand lifted off the knee until no point of it is more than REST_DEEP inside the leg)
    for it in range(6):
        deep = 0.0
        for k in range(4):
            W_ = make(k * CRANK_LEN / 4); set_world(B.arm, W_); co = B.meter.coords()
            lb = BVHTree.FromPolygons([tuple(c) for c in co], B.meter.leg_polys_s["l"])
            sd = Meter.signed(lb, co[B.meter.hand["l"]]); i = int(np.argmin(sd))
            if sd[i] < deep: deep = float(sd[i]); where = str(B.meter.gname[B.meter.hand["l"][i]])
        log("crank: the left palm %.1f cm off the knee: its hand at most %.1f cm inside the leg (%s)" % (lift["lift"], -deep, where if deep < 0 else "-"))
        if deep > -REST_DEEP: break
        lift["lift"] += -REST_DEEP - deep + 0.2
    st["v"] = None; lift["v"] = None; lift["anchor"] = None
    Ws = solve_frames(B, n, make)
    q = grip_q(ctx, "r", F, st["v"][0], st["v"][1], st["v"][2])
    log("crank: the fist's roll about the handle over the clip %s (the handle %s)" % (rnd((min(psis), max(psis)), 0), "toward her" if st["v"][2] < 0 else "away"))
    info = {"crank_circle_root": {"centre_her": list(CRANK_C), "centre_ue": ue(C0), "radius_cm": CRANK_R, "plane_normal_her": [0, 1, 0],
                                  "plane_normal_ue": ue(F), "turns": 1, "direction": "her right, up, her left, down (seen from behind her)",
                                  "handle_along": "her facing (UE +Y)", "phase_0": "at her right of the centre"},
            "fist_hole_cm": round(d, 1), "fist_roll_deg": rnd((min(psis), max(psis)), 0), "left_palm_lifted_off_knee_cm": round(lift["lift"], 1)}
    def extra(i, W, co):
        Gw = W["hand_r"] @ loc_m; Gt, _ = grip(i / FPS)
        pt, nn = B.meter.palm_at(W, "l")
        lb = BVHTree.FromPolygons([tuple(c) for c in co], B.meter.leg_polys_s["l"])
        sd = Meter.signed(lb, [pt])[0]
        return {"grip": Gw, "grip_err": (Gw - Gt).length, "left_palm_to_thigh": sd}
    def summary(rows):
        G = np.array([her(r["grip"]) for r in rows]); c = G.mean(0)
        rad = np.linalg.norm(G[:, [0, 2]] - c[[0, 2]], axis=1)
        return {"fist_hole_circle_measured": {"centre_her": rnd(c), "radius_cm": rnd((rad.min(), rad.max())),
                                              "forward_spread_cm": round(float(G[:, 1].max() - G[:, 1].min()), 2)},
                "grip_off_circle_cm_max": round(max(r["grip_err"] for r in rows), 2),
                "left_palm_to_thigh_skin_cm": rnd((min(r["left_palm_to_thigh"] for r in rows), max(r["left_palm_to_thigh"] for r in rows)))}
    return Ws, info, extra, summary, {"crank": (C0, grip)}


# ---- Tend (a deep squat)

# the fingers touch the soil here (her right, forward): under her right shoulder as she leans (at 44 cm out the arm,
# stretched, left the fingertips 25 cm over the ground)
TEND_TOUCH = (9.0, 38.0)                               # (between the knees: at 18 cm to her right the forearm passed through the right knee)


TEND_POLE = C.D("r", 1.0, 0.3, 0.4)                    # (the reaching elbow out and up: out and down it dropped into the right thigh)
SQUAT_Z, SQUAT_FEET = 41.0, (17.0, 6.0)             # the pelvis bone's height; each ankle out to its side and forward (cm)


def squat(B, z, lean, look, twist=0.0, clav=None):
    """a deep squat (the gardener's crouch): both feet flat, turned out, the knees wide and forward, the hips low and back
    over the heels, the pelvis at height z pitched forward with the lean"""
    P = B.poser; h = B.h; Ph = h.pose.bones
    P.start()
    p0 = Ph["pelvis"].head.copy()
    P.pelvis(move=from_her(0.0, -4.0, z) - p0, pitch=0.4 * lean)
    P.body(lean=0.6 * lean, twist=twist, look=look, keep_head=0.25, clav=clav)
    for s, sg in (("l", -1.0), ("r", 1.0)):
        ankle = from_her(sg * SQUAT_FEET[0], SQUAT_FEET[1], P.idle_feet[s][0].z)
        leg_ik(h, s, ankle, F + OUT[s] * 0.9 + U * 0.3, Quaternion(U, math.radians(-22.0 * sg)) @ P.rest_foot[s])


def make_tend(B):
    ctx = B.ctx; P = B.poser; h = B.h; m = B.meter
    n = int(round(TEND_LEN * FPS))
    # (down on the right knee with the left knee up, the hips stay 50 cm up: at a 73 degree lean the stretched arm still
    # left the fingertips 14 cm over the ground, and the torso was 10 cm into the raised thigh. A deep squat, knees wide,
    # brings the hips down to 44 and the chest down between the knees)
    tx, tf = TEND_TOUCH
    ax_dn = from_her(0.0, 0.25, -1.0); pa_bk = from_her(0.15, -1.0, -0.2)
    # the right hand's keys: time, wrist (her right, forward, up), hand axis, palm, curl, lean, look, the right shoulder
    # dropped and forward (deg), and after refine_q the hand's turn; the touch's wrist height (tz) is lowered below until
    # the fingertips' skin meets the ground
    def keys_for(tz):
        # (the toss out to her right over the knee: at (29, 32, 38) the forearm went through the right knee; the fist closes
        # at the soil, the wrist lowered as the fingers curl)
        hover = (tx, tf - 3.0, tz + 12.0); touch = (tx, tf - 1.0, tz); pulled = (tx - 2.0, tf - 9.0, tz + 21.0); toss = (tx + 30.0, tf + 2.0, tz + 32.0)
        grip = (tx, tf - 1.0, tz - 2.5)
        # (at a 62 degree lean with the hips at 44 cm the stretched arm left the fingertips 9.6 cm over the ground)
        return [[0.0, hover, ax_dn, pa_bk, -0.05, 60.0, 30.0, 6.0], [0.55, touch, ax_dn, pa_bk, -0.05, 75.0, 32.0, 12.0], [0.95, grip, ax_dn, pa_bk, 0.72, 75.0, 32.0, 12.0],
                [1.55, pulled, from_her(0.1, 0.6, -0.8), from_her(0.2, -0.9, 0.3), 0.72, 54.0, 28.0, 4.0],
                # (the toss keeps the hand near its turn at the pull, the weed flicked off by opening the fingers: turned
                # palm down for it, the wrist went 17 to 23 degrees past its limits on the way and the arm jumped 30 to
                # 50 degrees in a frame; a key half way keeps the path out from the knee)
                [1.78, tuple((Vector(pulled) + Vector(toss)) * 0.5 + Vector((0.0, 0.0, 3.0))), from_her(0.2, 0.6, -0.75), from_her(0.15, -0.85, 0.2), 0.6, 53.0, 28.0, 4.0],
                [2.0, toss, from_her(0.3, 0.6, -0.7), from_her(0.1, -0.8, 0.1), -0.1, 52.0, 28.0, 4.0],
                [2.6, (tx + 6.0, tf - 5.0, tz + 14.0), ax_dn, pa_bk, 0.0, 55.0, 30.0, 5.0], [TEND_LEN, hover, ax_dn, pa_bk, -0.05, 58.0, 30.0, 6.0]]
    knee = {"v": None, "anchor": None, "lift": 0.3}
    def body_at(t, k):
        j = max(i for i in range(len(k) - 1) if k[i][0] <= t + 1e-6) if t < TEND_LEN else len(k) - 2
        a, b = k[j], k[j + 1]; u = ease(min(1.0, max(0.0, (t - a[0]) / (b[0] - a[0]))))
        lean = a[5] + (b[5] - a[5]) * u; look = a[6] + (b[6] - a[6]) * u; cl = a[7] + (b[7] - a[7]) * u
        squat(B, SQUAT_Z, lean, look, twist=-5.0 * bump(t, 1.45, 2.5, 0.4), clav={"r": (-0.5 * cl, cl)})
        hands = {}; hands.update(fingers("r", a[4] + (b[4] - a[4]) * u)); hands.update(fingers("l", KNEE_CURL, 0.2)); P.hands(hands)
        q = mix(a[8], b[8], u) if len(a) > 8 else mix(hand_q(ctx, "r", a[2], a[3]), hand_q(ctx, "r", b[2], b[3]), u)
        return Vector(a[1]).lerp(Vector(b[1]), u), q
    def pose_at(t, k):
        wr, q = body_at(t, k)
        A = ctx["arms"]["r"]
        P.reach("r", from_her(wr.x, wr.y, wr.z), TEND_POLE, exact={"front": q @ A["local"]["front"], "up": q @ A["local"]["up"]})
        W_ = P.finish(); B.rig.to_helper(W_)
        hand_on_knee(B, W_, C.D("l", 1.0, 0.0, 0.4), knee, KNEE_BACK)        # (the elbow out and up: down and in, the forearm lay in the thigh)
        return P.finish()
    tz = 17.0
    for it in range(6):
        W = pose_at(0.55, keys_for(tz)); set_world(B.arm, W); co = m.coords()      # (the touch key: the fingers straightest, lowest)
        tip = float(co[m.tips["r"]][:, 2].min())
        log("tend: the touch's wrist at %.1f cm: the fingertips' skin %.2f cm off the ground (the right shoulder at %s, the wrist at %s, the pelvis at %s, the neck at %s)" % (
            tz, tip, rnd(her(W["upperarm_r"].translation), 1), rnd(her(W["hand_r"].translation), 1), rnd(her(W["pelvis"].translation), 1), rnd(her(W["neck_01"].translation), 1)))
        if abs(tip - 0.3) < 0.15: break
        tz += max(-6.0, 0.3 - tip)
    keys = keys_for(tz)
    for kk in keys[:-1]:                                          # (each key's hand turned as the arm bears it best)
        wr, q = body_at(kk[0], keys)
        q2, ov = refine_q(B, "r", from_her(wr.x, wr.y, wr.z), q, Vector((0, 0, 0)), TEND_POLE)
        kk.append(q2)
        log("tend: key %.2f s: the wrist %.1f deg past its limits" % (kk[0], ov))
    keys[-1].append(keys[0][8])
    # (the resting hand lifted off the thigh until no point of it is more than REST_DEEP inside the leg)
    for it in range(5):
        knee["v"] = None; knee["anchor"] = None; deep = 0.0
        for k in range(4):
            W_ = pose_at(k * TEND_LEN / 4, keys); set_world(B.arm, W_); co = m.coords()
            lb = BVHTree.FromPolygons([tuple(c) for c in co], m.leg_polys_s["l"])
            sd = Meter.signed(lb, co[m.hand["l"]]); i = int(np.argmin(sd))
            if sd[i] < deep: deep = float(sd[i]); where = str(m.gname[m.hand["l"][i]])
        log("tend: the left palm %.1f cm off the thigh: its hand at most %.1f cm inside the leg (%s)" % (knee["lift"], -deep, where if deep < 0 else "-"))
        if deep > -REST_DEEP: break
        knee["lift"] += -REST_DEEP - deep + 0.2
    knee["v"] = None; knee["anchor"] = None
    Ws = solve_frames(B, n, lambda t: pose_at(t, keys))
    def extra(i, W, co):
        tipv = co[m.tips["r"]]; j = int(np.argmin(tipv[:, 2]))
        allz = co[:, 2]; k = int(np.argmin(allz))
        # (the leaning torso between the knees: torso skin points inside either leg, near its thigh bone)
        tv = co[m.torsov[::3]]
        sd = Meter.signed(BVHTree.FromPolygons([tuple(c) for c in co], m.leg_polys), tv)
        near = np.minimum(seg_dist_np(tv, W["thigh_l"].translation, W["calf_l"].translation),
                          seg_dist_np(tv, W["thigh_r"].translation, W["calf_r"].translation)) < 12.0
        body = np.concatenate([m.torsov, m.legv["l"], m.legv["r"]]); bz = co[body][:, 2]; kb = int(np.argmin(bz))
        return {"tip": Vector(tipv[j]), "low": (float(allz[k]), str(m.gname[k]), Vector(co[k])),
                "seat": (float(bz[kb]), str(m.gname[body[kb]])),
                "sole_l": float(co[m.footv["l"]][:, 2].min()), "sole_r": float(co[m.footv["r"]][:, 2].min()),
                "torso_in_thigh": float(sd[near].min()) if near.any() else 99.0, "torso_in_thigh_n": int(((sd < -1.0) & near).sum())}
    def summary(rows):
        ti = min(range(len(rows)), key=lambda i: rows[i]["tip"].z)
        lo = min(range(len(rows)), key=lambda i: rows[i]["low"][0])
        return {"hand_touch_root": {"her": rnd(her(rows[ti]["tip"])), "ue": ue(rows[ti]["tip"]), "frame": ti, "time_s": round(ti / FPS, 2)},
                "touch_frames": [i for i, r in enumerate(rows) if r["tip"].z < 1.0],
                "lowest_point": {"z_cm": round(rows[lo]["low"][0], 2), "bone": rows[lo]["low"][1], "her": rnd(her(rows[lo]["low"][2])), "frame": lo},
                "lowest_of_the_body_above_the_feet_cm": {"z_cm": round(min(r["seat"][0] for r in rows), 1), "bone": min(rows, key=lambda r: r["seat"][0])["seat"][1]},
                "soles_z_cm": {"l": rnd((min(r["sole_l"] for r in rows), max(r["sole_l"] for r in rows))), "r": rnd((min(r["sole_r"] for r in rows), max(r["sole_r"] for r in rows)))},
                "pelvis_height_cm": SQUAT_Z,
                "torso_in_thighs_cm_min": round(min(r["torso_in_thigh"] for r in rows), 2),
                "torso_in_thighs_frames": sum(1 for r in rows if r["torso_in_thigh_n"] > 0)}
    return Ws, {"pose": "a deep squat, the feet flat (one knee down could not reach the soil: see the comment in make_tend)",
                "touch_wrist_height_cm": round(tz, 2), "left_palm_lifted_off_thigh_cm": round(knee["lift"], 1)}, extra, summary, {"weed": from_her(tx, tf, 0.0)}


def AB_rest_q(B, name): return B.arm.data.bones[name].matrix_local.to_quaternion()


# ---- Scatter
# the left palm's point (the bowl's foot): her right, forward, up (27 cm out the forearm lay 12 cm into the belly)
SC_BOWL = (3.0, 42.0, 100.0)
BOWL_PALM = (U * math.cos(math.radians(35.0)) + RT * math.sin(math.radians(35.0))).normalized()   # the left palm's normal


def make_scatter(B):
    ctx = B.ctx; P = B.poser
    n = int(round(SCATTER_LEN * FPS))
    bowl = from_her(*SC_BOWL)
    ql = hand_q(ctx, "l", from_her(-0.8, 0.55, 0.0), U)      # (left palm up, the fingers toward her right and forward)
    b = SC_BOWL
    # the right hand: (time, wrist, axis, palm, curl, twist); the hand into the bowl, closed, drawn in, swept out
    # (the dip's wrist high enough that the fingers stay over the left palm: 10 cm over it the two hands crossed)
    keys = [(0.0, (b[0] + 2.0, b[1] - 2.0, b[2] + 19.0), from_her(-0.1, 0.5, -1.0), from_her(0.0, -1.0, 0.1), 0.25, 0.0),
            (0.35, (b[0] + 2.0, b[1] - 1.0, b[2] + 16.0), from_her(-0.1, 0.5, -1.0), from_her(0.0, -1.0, 0.1), 0.45, 0.0),
            (0.7, (b[0] + 6.0, b[1] + 2.0, b[2] + 15.0), from_her(-0.2, 0.6, -0.6), from_her(0.1, -0.6, -0.8), 0.85, 6.0),
            # (the sweep forward and to her right: through (24, 56) to (50, 40) the hand went right and back at its fastest;
            # wound up 15 cm over the bowl the forearm crossed her chest)
            (1.05, (b[0] + 8.0, b[1] + 2.0, b[2] + 10.0), from_her(-0.2, 1.0, -0.1), from_her(0.0, -0.3, -1.0), 0.85, 10.0),
            (1.35, (18.0, 56.0, 116.0), from_her(0.4, 1.0, 0.1), from_her(0.0, 0.3, -1.0), 0.1, -8.0),
            (1.65, (46.0, 62.0, 116.0), from_her(1.0, 0.3, 0.0), from_her(0.0, 0.4, -1.0), -0.1, -14.0),
            (2.15, (25.0, 24.0, 106.0), from_her(0.2, 0.6, -0.8), from_her(-0.2, -0.8, -0.4), 0.15, -4.0),
            (SCATTER_LEN, None, None, None, None, None)]
    keys[-1] = (SCATTER_LEN,) + keys[0][1:]
    hl = {}; hl.update(fingers("l", 0.2, 0.0))
    keys = [list(k) for k in keys]
    bowl_st = {"v": None, "anchor": None, "lift": 0.0}
    def setup(t):
        j = max(i for i in range(len(keys) - 1) if keys[i][0] <= t + 1e-6) if t < SCATTER_LEN else len(keys) - 2
        a, b = keys[j], keys[j + 1]; u = ease(min(1.0, max(0.0, (t - a[0]) / (b[0] - a[0]))))
        P.start(); P.body(lean=6.0, twist=a[5] + (b[5] - a[5]) * u, look=14.0 * (1.0 - bump(t, 0.9, 2.3, 0.4)) + 4.0)
        P.keep_feet()
        hands = dict(hl); hands.update(fingers("r", a[4] + (b[4] - a[4]) * u)); P.hands(hands)
        # (the bowl's palm up, the hand turned about the up axis as the arm bears it best)
        # (the round-bottomed bowl rests in the palm tipped toward her middle: palm flat up, the forearm had to turn past
        # what a forearm turns, the wrist 64 degrees past its limits)
        palm_on(B, "l", bowl, -BOWL_PALM, from_her(-0.8, 0.55, 0.0), B.palm_loc["l"], C.D("l", 1.0, -0.3, -0.3), bowl_st, spread=75)
        q = mix(a[6], b[6], u) if len(a) > 6 else mix(hand_q(ctx, "r", a[2], a[3]), hand_q(ctx, "r", b[2], b[3]), u)
        # (the wrist runs through its keys without stopping: eased to a stop at each, the hand halted at the release)
        return through([(k[0], Vector(k[1])) for k in keys], t), q
    for kk in keys[:-1]:
        wr, q = setup(kk[0])
        q2, ov = refine_q(B, "r", from_her(wr.x, wr.y, wr.z), q, Vector((0, 0, 0)), C.D("r", 1.0, 0.0, -0.2))
        kk.append(q2); log("scatter: key %.2f s: the right wrist %.1f deg past its limits" % (kk[0], ov))
    keys[-1].append(keys[0][6])
    bowl_st["v"] = None
    def make(t):
        wr, q = setup(t)
        A = ctx["arms"]["r"]
        P.reach("r", from_her(wr.x, wr.y, wr.z), C.D("r", 1.0, 0.0, -0.2), exact={"front": q @ A["local"]["front"], "up": q @ A["local"]["up"]})
        return P.finish()
    Ws = solve_frames(B, n, make)
    W0 = Ws[0]; bp, bn = B.meter.palm_at(W0, "l")
    sk = socket(W0, "hand_l", bp, U, F)                          # (the bowl upright on the tipped palm: its foot at the palm's middle)
    # the release: where the throwing hand (its middle knuckle) moves fastest in the sweep
    spd = lambda i: (Ws[i + 1]["middle_01_r"].translation - Ws[i - 1]["middle_01_r"].translation) * (FPS / 2.0)
    rel = max(range(int(1.0 * FPS), int(1.75 * FPS)), key=lambda i: spd(i).length); v = spd(rel)
    info = {"bowl_point_root": {"her": rnd(her(bp)), "ue": ue(bp), "bowl_up_her": [0.0, 0.0, 1.0], "palm_normal_her": rnd(her(bn), 3)}, "socket_bowl_hand_l": sk,
            "release": {"time_s": round(rel / FPS, 3), "frame": rel, "hand_root_her": rnd(her(Ws[rel]["middle_01_r"].translation)),
                        "hand_velocity_her_cm_s": rnd(her(v), 0), "throw_way_her": rnd(her(v.normalized()), 3)}}
    def extra(i, W, co):
        Mb = socket_world(W, sk); p, nn = B.meter.palm_at(W, "l")
        return {"bowl": Mb.translation, "tilt": math.degrees((Mb.to_quaternion() @ Vector((0, 0, 1))).angle(U)), "palm": math.degrees(nn.angle(U))}
    def summary(rows):
        Bp = np.array([her(r["bowl"]) for r in rows])
        return {"bowl_moves_cm": round(float(np.linalg.norm(Bp - Bp[0], axis=1).max()), 2), "bowl_tilt_deg_max": round(max(r["tilt"] for r in rows), 1),
                "palm_tipped_deg": rnd((min(r["palm"] for r in rows), max(r["palm"] for r in rows)), 1)}
    return Ws, info, extra, summary, {"bowl": sk}


# ---- seated (SitDrink, SitTalk)
def seat(B, z, lean, look=0.0, twist=0.0, tilt=0.0):
    """seated: the pelvis' head at height z over the root, tipped back a little, the thighs forward, the shins down to the
    feet flat on the floor under the knees"""
    P = B.poser; h = B.h; Ph = h.pose.bones
    P.start()
    p0 = Ph["pelvis"].head.copy()
    P.pelvis(move=from_her(0.0, 0.0, z) - p0, pitch=-8.0)
    P.body(lean=lean + 8.0, twist=twist, look=look, tilt=tilt, keep_head=0.6)
    for s, x in (("l", -13.0), ("r", 13.0)):
        hip = Ph[f"thigh_{s}"].head
        ankle = from_her(x, her(hip)[1] + 41.0, P.idle_feet[s][0].z)
        leg_ik(h, s, ankle, F + U * 0.8, Quaternion(U, math.radians(-6.0 if s == "r" else 6.0)) @ P.rest_foot[s])


def blend_side(B, Wa, Wb, side, g):
    """Wa with one arm's local turns (upper arm down to the fingers) eased toward Wb's by g"""
    Pa = basis_of(B.arm, Wa); Pb = basis_of(B.arm, Wb)
    for b in B.side_bones[side]:
        l0, q0, s0 = Pa[b]; q1 = Pb[b][1]
        if q0.dot(q1) < 0.0: q1 = -q1
        Pa[b] = (l0, q0.slerp(q1, g), s0)
    set_basis(B.arm, Pa); out = world(B.arm)
    for ik, b, rel in B.ctx["ik_follow"]: out[ik] = out[b] @ rel
    return out


def seat_sel(W, co):
    """the skin under the buttocks: from 14 cm behind the pelvis bone to 4 cm in front of it, below it"""
    pv = W["pelvis"].translation; f = -(co[:, 1] - pv.y)
    return np.where((np.abs(co[:, 0] - pv.x) < 18.0) & (f > -14.0) & (f < 4.0) & (co[:, 2] < pv.z))[0]


def mug_inside(B, W, co):
    """the right fingertips' skin points inside the mug (its cylinder less 0.5 cm)"""
    m = B.meter
    mc = W["hand_r"] @ mesh_local(B, "r", B.mug_loc)
    qh = B.rig.helper_rot(W, "hand_r"); ax = (qh @ B.ctx["across_l"]["r"]).normalized()
    tv2 = co[m.tips["r"]] - np.array(mc); along = tv2 @ np.array(ax)
    radial = np.linalg.norm(tv2 - along[:, None] * np.array(ax), axis=1)
    return int(((np.abs(along) < MUG_H / 2) & (radial < MUG_R - 0.5)).sum())


def make_sit(B, name, length, drink):
    ctx = B.ctx; P = B.poser; m = B.meter
    n = int(round(length * FPS))
    is_rest = (lambda t: not (1.5 <= t <= 3.6)) if drink else (lambda t: t < 0.3 or 2.1 < t < 2.5 or t > 4.4)
    # the seat: the pelvis lowered until the lowest skin under her hips is on the bench
    if not hasattr(B, "seat_z"):
        # (the seat is the buttocks' lowest skin, from 14 cm behind the pelvis bone to 4 in front: the lowest skin under
        # the hips at all was under the thighs, 14 cm forward, and left the buttocks over the bench)
        z = 56.0
        for it in range(6):
            seat(B, z, 12.0); W = P.finish(); set_world(B.arm, W); co = m.coords()
            low = float(co[seat_sel(W, co), 2].min())
            log("sit: pelvis at %.1f cm: the buttocks' lowest skin at %.2f cm" % (z, low))
            if abs(low - SEAT_Z) < 0.1: break
            z += SEAT_Z - low
        B.seat_z = z
        B.sit_q = {"r": hand_q_across(ctx, "r", U, -RT + F * 0.25), "l": hand_q(ctx, "l", from_her(-0.45, 1.0, 0.0), -U)}
        B.mug_loc = palm_local(B, "r", MUG_R + 0.3)
        # the mug hand's fingers: curled until their tips rest on the mug's side (at 0.42 212 fingertip points were in it)
        tg = {"r": [12.0, 46.0, TABLE_Z + MUG_H / 2], "l": [-12.0, 58.0, TABLE_Z + 8.7]}
        lo_c, hi_c = 0.0, 0.6
        for it in range(7):
            c = 0.5 * (lo_c + hi_c); B.mug_curl = c
            W = sit_pose(B, 0.0, tg, 12.0, None)
            set_world(B.arm, W); co = m.coords()
            if mug_inside(B, W, co) > 0: hi_c = c
            else: lo_c = c
        B.mug_curl = lo_c
        log("sit: the mug hand's fingers curled %.2f (their tips then on the mug's side)" % lo_c)
        # the forearms on the table (the right: the mug's middle, the mug standing on the table; the left: the palm, the
        # hand flat on it). Each reaches further while its forearm dips into the table (a straighter arm lifts the elbow)
        # and back while it hovers; the left hand's height follows its own skin. (Seated, the shoulders are 105 cm up and
        # the upper arm 28 cm long: an elbow on a 75 cm table puts the forearm forward, the hands 45 to 60 cm out)
        for it in range(8):
            W = sit_pose(B, 0.0, tg, 12.0, None)
            set_world(B.arm, W); co = m.coords()
            ok = True
            for s in "rl":
                low = float(co[m.fore[s]][:, 2].min()); d = TABLE_Z + 0.2 - low
                msg = "sit: %s forearm skin lowest %.2f (table %.1f)" % (s, low, TABLE_Z)
                if abs(d) > 0.2: ok = False; tg[s][1] = min(66.0, max(20.0, tg[s][1] + 1.5 * d))
                if s == "l":
                    hl = float(co[m.hand[s]][:, 2].min()); dh = TABLE_Z + 0.2 - hl; msg += ", hand %.2f" % hl
                    if abs(dh) > 0.15: ok = False; tg[s][2] += dh
                log(msg + ", target %s" % rnd(tg[s], 1))
            if ok: break
        B.sit_targets = tg
    tg = B.sit_targets
    if drink:
        # (at the sip the hand goes round the mug as the wrist bears it best (the mug turns about its own axis in the
        # hand): held as on the table, the wrist bent 8 degrees past its limit toward the little finger)
        best = None
        for psi in range(-60, 61, 10):
            B.sip_psi = float(psi); ctx["prev_arm"] = {}
            W = sit_pose(B, 2.5, tg, 9.0, ("drink", 1.0)); B.rig.to_helper(W)
            c = B.meter_wrist(W, "r") + 0.5 * arm_torso_cost(B.h, ctx, "r") + 0.01 * abs(psi)
            if best is None or c < best[0]: best = (c, psi, B.meter_wrist(W, "r"))
        B.sip_psi = float(best[1])
        log("sit: at the sip the hand %d deg round the mug: the wrist %.1f deg past its limits" % (best[1], best[2]))
        def make(t):
            sw = 2.0 * math.pi * t / length
            up = bump(t, 1.6, 3.5, 0.6)
            return sit_pose(B, t, tg, 12.0 + 1.5 * math.sin(sw) - 3.0 * up, ("drink", up), look=-6.0 * bump(t, 2.2, 3.1, 0.3) + 2.0 * math.sin(2 * sw),
                            twist=1.5 * math.sin(2 * sw))
    else:
        # (each open hand's turn refined at its gesture's middle, as the arm bears it best)
        B.talk_q = {}
        for s, sg in (("r", 1.0), ("l", -1.0)):
            seat(B, B.seat_z, 11.0); P.hands(fingers(s, 0.08, 0.0))
            q0 = hand_q(ctx, s, from_her(0.15 * sg, 1.0, 0.35), from_her(-0.75 * sg, 0.0, 0.66))
            B.talk_q[s], ov = refine_q(B, s, from_her(18.0 * sg, 34.0, 96.0), q0, B.palm_loc[s], C.D(s, 1.0, 0.0, 0.1))
            log("sit talk: the %s hand's gesture: the wrist %.1f deg past its limits" % (s, ov))
        # (each frame the arms on the table and each gesturing arm raised are solved on their own, each following its own
        # frame before, and the gesturing arm's local turns blended from one to the other: blending the targets instead,
        # the elbow jumped 24 to 34 degrees in a frame as the gesture ended)
        prevs = {"rest": {}, "r": {}, "l": {}}
        def track(k, t, lean, act, nod, tw):
            ctx["prev_arm"] = dict(prevs[k]); W = sit_pose(B, t, tg, lean, act, look=nod, twist=tw); prevs[k] = ctx["prev_arm"]
            return W
        def make(t):
            sw = 2.0 * math.pi * t / length
            gr = bump(t, 0.3, 2.1, 0.45); gl = bump(t, 2.5, 4.4, 0.45)
            # (the lean the forearms were laid on the table at, 12 degrees, swaying 1 either way: at 11 they hovered 1 to 1.5 cm over it)
            nod = 9.0 * (bump(t, 0.9, 1.4, 0.2) + bump(t, 3.1, 3.6, 0.2)); lean = 12.0 + 1.0 * math.sin(sw); tw = 5.0 * (gl - gr)
            out = track("rest", t, lean, ("talk", 0.0, 0.0), nod, tw)
            for s, g in (("r", gr), ("l", gl)):
                if g > 0.0: out = blend_side(B, out, track(s, t, lean, ("talk", 1.0 if s == "r" else 0.0, 1.0 if s == "l" else 0.0), nod, tw), s, g)
            return out
    Ws = solve_frames(B, n, make)
    W0 = Ws[0]
    info = {"seat_z_cm": SEAT_Z, "table_top_z_cm": TABLE_Z, "pelvis_height_cm": round(B.seat_z, 1)}
    if drink:
        mc = W0["hand_r"] @ mesh_local(B, "r", B.mug_loc)
        qh = B.rig.helper_rot(W0, "hand_r"); ax = qh @ ctx["across_l"]["r"]
        info["socket_mug_hand_r"] = socket(W0, "hand_r", mc, ax, F)
        info["mug"] = {"radius_cm": MUG_R, "height_cm": MUG_H, "centre_root_her": rnd(her(mc)), "note": "socket origin: the mug's middle; z its axis"}
        info["sip"] = {"up_s": [1.6, 2.2], "at_mouth_s": [2.2, 2.9], "down_s": [2.9, 3.5]}
    def extra(i, W, co):
        r = {}
        fl = [co[m.fore[s]] for s in "lr"]
        tl = np.vstack(fl)
        on = tl[tl[:, 2] < TABLE_Z + 0.6]
        r["fore_low"] = float(tl[:, 2].min()); r["edge"] = float(on[:, 1].max() * -1.0) if len(on) else None
        r["on_n"] = len(on)
        r["on_min_fwd"] = float((-on[:, 1]).min()) if len(on) else None
        tv = co[m.torsov]; band = tv[(tv[:, 2] > TABLE_Z - 6.0) & (tv[:, 2] < TABLE_Z + 2.0)]
        r["belly_fwd"] = float((-band[:, 1]).max()) if len(band) else None
        lv = np.vstack([co[m.legv[s]] for s in "lr"])
        r["thigh_top"] = float(lv[(-lv[:, 1]) > 10.0][:, 2].max())
        sel = seat_sel(W, co)
        k = sel[int(np.argmin(co[sel, 2]))]; r["seat"] = Vector(co[k])
        if drink:
            mc = W["hand_r"] @ mesh_local(B, "r", B.mug_loc)
            qh = B.rig.helper_rot(W, "hand_r"); ax = (qh @ ctx["across_l"]["r"]).normalized()
            mouth = W["head"] @ B.mouth_local
            top = mc + ax * (MUG_H / 2)
            toward = (mouth - top); toward = (toward - ax * toward.dot(ax)).normalized()
            rim = top + toward * MUG_R
            r["rim_mouth"] = (rim - mouth).length; r["mug_tilt"] = math.degrees(ax.angle(U)); r["mug_bottom"] = (mc - ax * MUG_H / 2).z
            r["fingers_in_mug"] = mug_inside(B, W, co)
        # the bench: the skin below its top (the thighs pass over its front edge further forward than this)
        under = co[(np.abs(co[:, 0]) < 25.0) & (co[:, 2] < SEAT_Z - 0.5) & (co[:, 2] > 20.0)]
        r["under_bench_fwd"] = float((-under[:, 1]).min()) if len(under) else 99.0
        r["arm_pts"] = co[np.concatenate([m.fore["l"], m.fore["r"], m.hand["l"], m.hand["r"]])]
        return r
    def summary(rows):
        rest = [r for i, r in enumerate(rows) if is_rest(i / FPS)] or rows
        onf = [r["on_min_fwd"] for r in rest if r["on_min_fwd"] is not None]
        edge = min(onf) - 1.0 if onf else None
        # (over the table, every frame: the forearms' and hands' skin below its top)
        deep = []
        for r in rows:
            a = r.pop("arm_pts"); over = a[(-a[:, 1]) > (edge if edge is not None else 30.0)]
            deep.append(float(TABLE_Z - over[:, 2].min()) if len(over) else -99.0)
        s = {"forearm_skin_lowest_z_cm_at_rest": rnd((min(r["fore_low"] for r in rest), max(r["fore_low"] for r in rest))),
             "forearm_points_on_table_at_rest_min": min(r["on_n"] for r in rest),
             "table_edge_forward_cm": round(edge, 1) if edge is not None else None,
             "arms_below_table_top_over_it_cm_max": round(max(deep), 2),
             "belly_front_at_table_height_cm": round(max(r["belly_fwd"] for r in rows if r["belly_fwd"] is not None), 1),
             "thigh_top_z_cm_max": round(max(r["thigh_top"] for r in rows), 1),
             "bench_front_edge_at_most_forward_cm": round(min(r["under_bench_fwd"] for r in rows), 1),
             "seat_point_root": {"her": rnd(her(rows[0]["seat"])), "ue": ue(rows[0]["seat"]),
                                 "z_range_cm": rnd((min(r["seat"].z for r in rows), max(r["seat"].z for r in rows))),
                                 "note": "the buttocks' lowest skin: the bench top under it"}}
        if drink:
            sip = [r for i, r in enumerate(rows) if 2.2 * FPS <= i <= 2.9 * FPS]
            s["rim_to_mouth_cm_at_sip"] = rnd((min(r["rim_mouth"] for r in sip), max(r["rim_mouth"] for r in sip)))
            s["mug_tilt_deg_at_sip"] = round(max(r["mug_tilt"] for r in sip), 1)
            s["mug_bottom_z_cm_at_rest"] = rnd((min(r["mug_bottom"] for r in rest), max(r["mug_bottom"] for r in rest)))
            s["fingertip_points_inside_mug_max"] = max(r["fingers_in_mug"] for r in rows)
        return s
    return Ws, info, extra, summary, {"sit": True, "mug": info.get("socket_mug_hand_r")}


def sit_pose(B, t, tg, lean, act, look=0.0, twist=0.0):
    ctx = B.ctx; P = B.poser
    seat(B, B.seat_z, lean, look=look, twist=twist)
    talk = act is not None and act[0] == "talk"
    hands = {}; hands.update(fingers("r", 0.08 if talk else B.mug_curl, 0.0 if talk else 0.45)); hands.update(fingers("l", 0.08, 0.0)); P.hands(hands)
    # the right: a mug on the table (its middle MUG_H / 2 over the top), the palm on its side; talking, the hand flat on
    # the table as the left (mirrored)
    if talk:
        tl = tg["l"]; qr = hand_q(ctx, "r", from_her(-0.45, 1.0, 0.0), -U); mc = from_her(-tl[0], tl[1], tl[2])
    else:
        qr = B.sit_q["r"]; mc = from_her(*tg["r"])
    if act is not None and act[0] == "drink" and act[1] > 0.0:
        up = act[1]
        W_ = P.finish(); mouth = W_["head"] @ B.mouth_local
        tilt = math.radians(55.0 * up)
        ax = (U * math.cos(tilt) - F * math.sin(tilt)).normalized()      # (the mug's top tipped toward her)
        q_s = Quaternion(ax, math.radians(getattr(B, "sip_psi", 0.0))) @ hand_q_across(ctx, "r", ax, -RT + F * 0.25)
        # the rim's near side at the lips: the mug's middle half its height down its axis and its radius off
        toward = -F
        mc_s = mouth + F * 1.0 - ax * (MUG_H / 2) - (toward - ax * toward.dot(ax)).normalized() * MUG_R
        mc = mc.lerp(mc_s, ease(min(1.0, up * 1.0))); qr = mix(qr, q_s, up)
    # (a gesturing elbow is drawn out to her side, not down: lifted with the elbow kept low, the forearm went 3.5 cm
    # down into the table)
    gr = act[1] if talk else 0.0; gl = act[2] if talk else 0.0
    if talk and gr > 0.0:
        wv = math.sin(2.0 * math.pi * 1.6 * t) * gr
        ga = from_her(18.0 + 2.0 * wv, 34.0, 96.0 + 2.5 * wv)
        q_g = B.talk_q["r"] if hasattr(B, "talk_q") else hand_q(ctx, "r", from_her(0.15, 1.0, 0.35), from_her(-0.75, 0.0, 0.66))
        mc = mc.lerp(ga, gr); qr = mix(qr, q_g, gr)
    P.hold("r", mc, qr, B.palm_loc["r"] if talk else B.mug_loc, (C.D("r", 1.0, -0.3, -0.7) * (1.0 - gr) + C.D("r", 1.0, 0.0, 0.1) * gr).normalized())
    ql = B.sit_q["l"]; pl = from_her(*tg["l"])
    if talk and gl > 0.0:
        wv = math.sin(2.0 * math.pi * 1.6 * t) * gl
        ga = from_her(-18.0 - 2.0 * wv, 34.0, 96.0 + 2.5 * wv)
        q_g = B.talk_q["l"] if hasattr(B, "talk_q") else hand_q(ctx, "l", from_her(-0.15, 1.0, 0.35), from_her(0.75, 0.0, 0.66))
        pl = pl.lerp(ga, gl); ql = mix(ql, q_g, gl)
    P.hold("l", pl, ql, B.palm_loc["l"], (C.D("l", 1.0, -0.3, -0.7) * (1.0 - gl) + C.D("l", 1.0, 0.0, 0.1) * gl).normalized())
    return P.finish()


# ---- the tray (CarryWalk, CarryIdle)
def tray_orient(B, base_frames):
    """the hands under the tray: their axis (out from forward) and the palms tipped in toward each other, chosen by the
    worst wrist over some frames and the arms against the torso (palms flat up the forearms had to turn 84 to 94 degrees
    from the reference, past the 80 a forearm turns)"""
    ctx = B.ctx; P = B.poser; best = None
    for o in (-0.5, -0.3, 0.0):
        for tilt in (20.0, 30.0, 40.0):
            q = {s: hand_q(ctx, s, C.D(s, o, 1.0, 0.0), U * math.cos(math.radians(tilt)) - OUT[s] * math.sin(math.radians(tilt))) for s in "lr"}
            worst = 0.0; body = 0.0; ctx["prev_arm"] = {}
            for W in base_frames:
                Wt = tray_pose(B, W, q, 0.0, 0.0); worst = max(worst, B.meter_wrist(Wt, "r"), B.meter_wrist(Wt, "l"))
                B.rig.to_helper(Wt); body = max(body, arm_torso_cost(B.h, ctx, "r"), arm_torso_cost(B.h, ctx, "l"))
            log("tray: the hands' axis %.2f out, the palms tipped in %.0f deg: the wrists at most %.1f deg past their limits, the arms' keep-out cost %.1f" % (o, tilt, worst, body))
            c = worst + 0.5 * body + 0.05 * tilt
            if best is None or c < best[0] - 0.5: best = (c, q, (o, tilt))
    return best


def tray_pose(B, W, q, bob, sway):
    P = B.poser; P.start(W)
    hands = {}; hands.update(fingers("r", -0.1, 0.0)); hands.update(fingers("l", -0.1, 0.0)); P.hands(hands)
    T = from_her(TRAY_AT[0] + sway, TRAY_AT[1], TRAY_AT[2] + bob)
    for s in "rl":
        P.hold(s, T + OUT[s] * TRAY_HALF, q[s], B.palm_loc[s], C.D(s, 1.0, -0.2, -0.7))
    Wt = P.finish()
    out = dict(W)
    for b in B.arm_bones: out[b] = Wt[b]
    return out


def make_carry(B, name, base, length_frames):
    """base: the body's frames (the walk's, or the idle window's), each a W; the arms carry the tray"""
    keep = R.ARM_CLEAR; R.ARM_CLEAR = CARRY_CLEAR
    try: return make_carry_(B, name, base, length_frames)
    finally: R.ARM_CLEAR = keep


# (the tray's elbows held in by her sides: with the sleeves' full clearance (ARM_CLEAR) the elbows went out and the
# wrists 24 to 26 degrees past their limits; with rogue_clips' the sleeves pressed 5 to 6.5 cm into the ribs)
CARRY_CLEAR = {"upper": 4.5, "elbow": 6.0, "fore": 5.0, "wrist": 3.5}


def make_carry_(B, name, base, length_frames):
    best = tray_orient(B, base[::max(1, len(base) // 6)])
    q = best[1]
    ch = np.array([W["spine_05"].translation.z for W in base]); chx = np.array([her(W["spine_05"].translation)[0] for W in base])
    zc, xc = float(ch.mean()), float(chx.mean())
    B.ctx["prev_arm"] = {}
    Ws = []
    for i, W in enumerate(base[:length_frames]):
        Ws.append(tray_pose(B, W, q, TRAY_BOB * (ch[i] - zc), 0.25 * (chx[i] - xc)))
    Ws[0] = tray_pose(B, base[0], q, TRAY_BOB * (ch[0] - zc), 0.25 * (chx[0] - xc))
    # (a frame whose body is the first frame's (the walk's last two, the idle window's last) takes the first frame's
    # arms too: the loop closes exactly)
    same = [i for i, W in enumerate(base) if i > 0 and max((W[b].translation - base[0][b].translation).length for b in CHAIN) < 0.01
            and max(angdeg(W[b].to_quaternion(), base[0][b].to_quaternion()) for b in CHAIN) < 0.01]
    for i in same: Ws[i] = Ws[0]
    log("tray: frames with the first frame's body:", same)
    W0 = Ws[0]
    pr, nr = B.meter.palm_at(W0, "r"); pl, nl = B.meter.palm_at(W0, "l")
    T = (pr + pl) * 0.5
    # (the tray rests on the hands' highest skin under it: with the palms tipped in, their thumb edges stand above the
    # palms' middles)
    def hands_top(W, Tp):
        set_world(B.arm, W); co = B.meter.coords(); hv = co[np.concatenate([B.meter.hand["l"], B.meter.hand["r"]])]
        rel = hv - np.array(Tp); f = -rel[:, 1]
        return float(hv[(np.abs(rel[:, 0]) < 22.0) & (np.abs(f) < 16.0)][:, 2].max()) - Tp.z
    lift = max(0.0, hands_top(W0, T)); T = T + U * lift
    sk = socket(W0, "hand_r", T, U, F)
    info = {"tray_point_root": {"her": rnd(her(T)), "ue": ue(T), "normal_her": [0.0, 0.0, 1.0], "normal_ue": [0.0, 0.0, 1.0],
                                "note": "the tray's bottom centre, between the palms"},
            "socket_tray_hand_r": sk, "tray_above_palms_cm": round(lift, 2), "hands_axis_out": best[2][0], "palms_tipped_in_deg": best[2][1], "palms_apart_cm": round((pr - pl).length, 1)}
    def extra(i, W, co):
        pr_, nr_ = B.meter.palm_at(W, "r"); pl_, nl_ = B.meter.palm_at(W, "l")
        Mt = socket_world(W, sk); Tp = Mt.translation; Tn = Mt.to_quaternion() @ Vector((0, 0, 1))
        hv = co[np.concatenate([B.meter.hand["l"], B.meter.hand["r"]])]; rel = hv - np.array(Tp)
        top = float(hv[(np.abs(rel[:, 0]) < 22.0) & (np.abs(rel[:, 1]) < 16.0)][:, 2].max()) - Tp.z
        return {"tray": Tp, "tray_tilt": math.degrees(Tn.angle(U)), "left_gap": (pl_ - Tp).dot(Tn),
                "left_off": ((pl_ - Tp) - Tn * (pl_ - Tp).dot(Tn)).length, "mid": (pr_ + pl_) * 0.5, "top": top}
    def summary(rows):
        Tp = np.array([her(r["tray"]) for r in rows])
        return {"tray_moves_her_cm": {"right": rnd((Tp[:, 0].min(), Tp[:, 0].max())), "forward": rnd((Tp[:, 1].min(), Tp[:, 1].max())),
                                      "up": rnd((Tp[:, 2].min(), Tp[:, 2].max()))},
                "tray_tilt_deg_max": round(max(r["tray_tilt"] for r in rows), 2),
                "left_palm_to_tray_bottom_cm": rnd((min(r["left_gap"] for r in rows), max(r["left_gap"] for r in rows))),
                "left_palm_sideways_from_its_place_cm_max": round(max(abs(r["left_off"] - rows[0]["left_off"]) for r in rows), 2),
                "hands_skin_above_tray_bottom_cm": rnd((min(r["top"] for r in rows), max(r["top"] for r in rows)))}
    return Ws, info, extra, summary, {"tray": sk}


# ---- Talk (standing)
def make_talk(B, base):
    ctx = B.ctx; P = B.poser
    n = int(round(TALK_LEN * FPS))
    gest = lambda s, t: from_her((19.0 + 3.0 * math.sin(2.0 * math.pi * 1.4 * t)) * (1 if s == "r" else -1),
                                 30.0 + 2.0 * math.sin(2.0 * math.pi * 1.4 * t), 108.0 + 3.0 * math.sin(2.0 * math.pi * 1.4 * t))
    # (each hand's open-palm turn refined once, at the middle of its gesture, as the arm bears it best)
    qref = {}
    for s, tm in (("r", 1.25), ("l", 3.55)):
        i = int(round(tm * FPS)); P.start(base[i]); P.hands(fingers(s, 0.05, 0.1))
        q0 = hand_q(ctx, s, C.D(s, 0.15, 1.0, 0.25), C.D(s, -0.65, 0.15, 0.75))
        qref[s], ov = refine_q(B, s, gest(s, tm), q0, B.palm_loc[s], C.D(s, 1.0, -0.2, -0.8))
        log("talk: the %s hand's gesture: the wrist %.1f deg past its limits" % (s, ov))
    def make(i):
        t = i / FPS; W = base[i]
        gr = bump(t, 0.3, 2.2, 0.5); gl = bump(t, 2.6, 4.5, 0.5)
        nod = 8.0 * (bump(t, 1.0, 1.5, 0.22) + bump(t, 3.3, 3.8, 0.22))
        P.start(W); P.body(twist=6.0 * (gl - gr), look=nod, turn_head=3.0 * (gl - gr))
        Wb = P.finish()
        out = dict(Wb)
        for s, g in (("r", gr), ("l", gl)):
            if g <= 0.0: continue
            ga = gest(s, t); qg = qref[s]
            P.start(Wb); P.hands(fingers(s, 0.05, 0.1))
            P.hold(s, ga, qg, B.palm_loc[s], C.D(s, 1.0, -0.2, -0.8))
            Wg = P.finish()
            # (the arm's local turns blended from the idle's to the gesture's)
            Pb = basis_of(B.arm, Wb); Pg = basis_of(B.arm, Wg); mixd = {}
            for b in B.side_bones[s]:
                l0, q0, s0 = Pb[b]; l1, q1, s1 = Pg[b]
                if q0.dot(q1) < 0.0: q1 = -q1
                mixd[b] = q0.slerp(q1, g)
            set_world(B.arm, out); Pc = basis_of(B.arm, out)
            for b, qq in mixd.items(): Pc[b] = (Pc[b][0], qq, Pc[b][2])
            set_basis(B.arm, Pc); out = world(B.arm)
        for ik, b, rel in ctx["ik_follow"]: out[ik] = out[b] @ rel
        return out
    ctx["prev_arm"] = {}
    Ws = [make(i) for i in range(n)]
    Ws.append(Ws[0])
    return Ws, {}, None, None, {}


# ---------------------------------------------------------------- asleep (the list of 2026-11-10)
def make_sleep(B):
    """lying on her back in bed: the pelvis tipped back a quarter turn about her left-right way (the legs and the body follow
    it: her feet toward her forward, her head behind her), the arms as the idle hangs them (along her sides), the head a little
    to one side; lowered until the lowest skin of frame 0 rests 1 cm over the root; a breath over SLEEP_LEN (the chest and the
    head rising a little)"""
    P = B.poser; m = B.meter; h = B.h
    n = int(round(SLEEP_LEN * FPS))
    P.start(); p0 = h.pose.bones["pelvis"].head.copy()
    def pose(t, z):
        br = 0.5 - 0.5 * math.cos(2.0 * math.pi * t / SLEEP_LEN)
        P.start(); P.pelvis(move=from_her(0.0, 0.0, z) - p0, pitch=-90.0)
        P.body(lean=-2.0 * br, look=-4.0 + 2.0 * br, tilt=10.0, keep_head=0.0)
        out = P.finish()
        for ik, b, rel in B.ctx["ik_follow"]: out[ik] = out[b] @ rel
        return out
    # (the bed under her: the lowest skin of the lying body, measured, put 1 cm over the root)
    z = 15.0
    for _ in range(3):
        W = pose(0.0, z); set_world(B.arm, W); co = m.coords()
        low = float(co[:, 2].min()); z += 1.0 - low
        if abs(1.0 - low) < 0.2: break
    log("sleep: the pelvis %.1f cm over the root, the lowest skin %.2f cm over it" % (z, low))
    ctx = B.ctx; ctx["prev_arm"] = {}
    Ws = [pose(i / FPS, z) for i in range(n)]
    Ws.append(Ws[0])
    set_world(B.arm, Ws[0]); co = m.coords()
    info = {"pelvis_over_root_cm": round(z, 2), "lowest_skin_cm": round(float(co[:, 2].min()), 2),
            "length_along_cm": round(float(co[:, 1].max() - co[:, 1].min()), 1), "width_cm": round(float(co[:, 0].max() - co[:, 0].min()), 1),
            "highest_cm": round(float(co[:, 2].max()), 1), "head_behind_cm": round(float(-co[:, 1].min()), 1), "feet_ahead_cm": round(float(co[:, 1].max()), 1)}
    return Ws, info, None, None, {}


# ---------------------------------------------------------------- idle windows
def idle_loop(B, idle, L):
    """a window of L frames of the idle (its cycle wraps), the one whose ends differ least, closed into a loop: each
    bone's turn eased from the window's own to the turn its first frame has (spread over the window)"""
    cyc = idle[:-1] if max((idle[0][b].translation - idle[-1][b].translation).length for b in CHAIN) < 0.05 else idle
    n = len(cyc)
    Pc = [basis_of(B.arm, W) for W in cyc]
    keyb = [b for b in CHAIN] + [f"{x}_{s}" for s in "lr" for x in ("clavicle", "upperarm", "lowerarm", "hand", "thigh", "calf", "foot")]
    def seam(s):
        a, b = Pc[s], Pc[(s + L) % n]
        return max(angdeg(a[k][1], b[k][1]) for k in keyb)
    d, s0 = min((seam(s), s) for s in range(n))
    out = []
    for i in range(L + 1):
        base = Pc[(s0 + i) % n]; a, e = Pc[s0], Pc[(s0 + L) % n]; u = i / L; fr = {}
        for b in base:
            dq = e[b][1].inverted() @ a[b][1]
            if dq.w < 0.0: dq = -dq
            fr[b] = (base[b][0] + (a[b][0] - e[b][0]) * u, (base[b][1] @ Quaternion().slerp(dq, u)).normalized(), base[b][2])
        set_basis(B.arm, fr); out.append(world(B.arm))
    log("idle window of %d frames: starts at frame %d of %d; its ends differ by %.2f deg (eased away over the window)" % (L, s0, n, d))
    return out, {"idle_start_frame": s0, "idle_cycle_frames": n, "ends_differed_deg": round(d, 2)}


# ---------------------------------------------------------------- measuring a clip
def measure(B, name, Ws, extra, legs=True):
    rows = []; feet0 = None; slide = {}
    for i, W in enumerate(Ws):
        set_world(B.arm, W); co = B.meter.coords()
        r = B.meter.frame(W, co, legs)
        if extra: r.update(extra(i, W, co))
        rows.append(r)
        fp = {b: W[b].translation.copy() for b in ("foot_l", "foot_r", "ball_l", "ball_r")}
        if feet0 is None: feet0 = fp
        for b in fp: slide[b] = max(slide.get(b, 0.0), (fp[b] - feet0[b]).length)
    frames = [basis_of(B.arm, W) for W in Ws]
    def step(a, b, only=None): return max(min(x, 360.0 - x) for x in (math.degrees(a[k][1].rotation_difference(b[k][1]).angle) for k in a if only is None or k in only))
    steps = [step(frames[i], frames[i + 1]) for i in range(len(frames) - 1)]
    asteps = [step(frames[i], frames[i + 1], B.arm_bones) for i in range(len(frames) - 1)]
    rep = {"frames": len(frames), "length_s": round((len(frames) - 1) / FPS, 4),
           "loop_first_last_deg": round(step(frames[0], frames[-1]), 4),
           "loop_last_step_deg": round(steps[-1], 2), "largest_step_deg": round(max(steps[:-1]), 2),
           "largest_step_frame": int(np.argmax(steps[:-1])),
           "arm_loop_last_step_deg": round(asteps[-1], 2), "arm_largest_step_deg": round(max(asteps), 2), "arm_largest_step_frame": int(np.argmax(asteps)),
           "loop_last_step_bone": max(frames[-2], key=lambda k: angdeg(frames[-2][k][1], frames[-1][k][1])),
           "largest_step_bone": max(frames[int(np.argmax(asteps))], key=lambda k: angdeg(frames[int(np.argmax(asteps))][k][1], frames[int(np.argmax(asteps)) + 1][k][1])),
           "wrist_over_max_deg": round(max(r["wrist_over"] for r in rows), 1),
           "arm_in_body_min_cm": round(min(r["arm_in_body"] for r in rows), 2), "arm_in_body_frames": sum(1 for r in rows if r["arm_in_body_n"] > 0),
           "hands_cross_frames": sum(1 for r in rows if r["hands_cross"] > 0),
           "feet_slide_cm": {b: round(v, 2) for b, v in slide.items()}}
    if legs:
        rep["arm_in_legs_min_cm"] = round(min(r["arm_in_legs"] for r in rows), 2)
        rep["arm_in_legs_frames"] = sum(1 for r in rows if r["arm_in_legs_n"] > 0)
    bad = [(i, r["arm_in_body_n"], r["arm_in_body_at"]) for i, r in enumerate(rows) if r["arm_in_body_n"] > 0]
    if bad: rep["arm_in_body_worst"] = max(bad, key=lambda b: b[1])
    badl = [(i, r["arm_in_legs_n"], r["arm_in_legs_at"]) for i, r in enumerate(rows) if r.get("arm_in_legs_n")]
    if badl: rep["arm_in_legs_worst"] = max(badl, key=lambda b: b[1])
    wi = max(range(len(rows)), key=lambda i: rows[i]["wrist_over"])
    rep["wrist_worst"] = {"frame": wi, "l": rows[wi]["wrist_l"], "r": rows[wi]["wrist_r"]}
    return rep, rows, frames


# ---------------------------------------------------------------- pictures
COLS = {"body": (0.75, 0.72, 0.68, 1), "wood": (0.55, 0.36, 0.2, 1), "iron": (0.25, 0.25, 0.28, 1), "clay": (0.75, 0.45, 0.3, 1),
        "green": (0.3, 0.6, 0.25, 1), "floor": (0.55, 0.6, 0.55, 1), "red": (0.9, 0.1, 0.1, 1)}


def prop_obj(name, kind, dims, col):
    """a stand-in prop in its own frame: 'cyl' along z from z0 to z1 with radius r; 'box' centred (sx, sy, sz); 'ring'"""
    if kind == "cyl":
        r, z0, z1 = dims
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=z1 - z0, location=(0, 0, (z0 + z1) / 2), vertices=20)
    elif kind == "box":
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0)); o = bpy.context.active_object; o.scale = dims
    elif kind == "ring":
        bpy.ops.mesh.primitive_torus_add(major_radius=dims[0], minor_radius=dims[1], major_segments=40, minor_segments=8)
    elif kind == "ball":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=dims[0], location=(0, 0, 0))
    o = bpy.context.active_object; o.name = name
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
    o.color = col
    return o


def frame_of(origin, z, x):
    z = z.normalized(); x = (x - z * x.dot(z)).normalized(); y = z.cross(x)
    return Matrix(((x.x, y.x, z.x, origin.x), (x.y, y.y, z.y, origin.y), (x.z, y.z, z.z, origin.z), (0, 0, 0, 1)))


def setup_render(sc):
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'OBJECT'; sh.show_cavity = True
    sc.render.resolution_x = 300; sc.render.resolution_y = 400; sc.render.film_transparent = False
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.clip_end = 5000.0
    bpy.ops.mesh.primitive_plane_add(size=300.0, location=(0, -30, -0.05))
    fl = bpy.context.active_object; fl.name = "floor"; fl.color = COLS["floor"]
    return cam


def shoot(sc, cam, path, target, ang, scale, elev=0.15):
    a = math.radians(ang); d = Vector((math.sin(a), -math.cos(a), elev)).normalized()
    cam.location = target + d * 600.0; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = scale; sc.render.filepath = path; bpy.ops.render.render(write_still=True)


def sheet(paths, out, cols):
    """the pictures in a grid (rows of `cols`), saved as one PNG"""
    imgs = [bpy.data.images.load(p) for p in paths]
    w, h = imgs[0].size; rows = (len(imgs) + cols - 1) // cols
    big = np.ones((rows * h, cols * w, 4), dtype=np.float32)
    for k, im in enumerate(imgs):
        px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
        r, c = divmod(k, cols); rr = rows - 1 - r
        big[rr * h:(rr + 1) * h, c * w:(c + 1) * w] = px
    out_im = bpy.data.images.new("sheet", cols * w, rows * h, alpha=True)
    out_im.pixels = big.ravel(); out_im.filepath_raw = out; out_im.file_format = 'PNG'; out_im.save()
    for im in imgs: bpy.data.images.remove(im)
    bpy.data.images.remove(out_im)


def previews(B, clips, props):
    sc = bpy.context.scene; cam = setup_render(sc)
    B.mesh.color = COLS["body"]
    made = {}
    def get(name, kind, dims, col):
        if name not in made: made[name] = prop_obj(name, kind, dims, col)
        o = made[name]; o.hide_render = False; return o
    n = 0
    for name, frames in clips.items():
        for o in made.values(): o.hide_render = True
        pr = props.get(name, {}); paths = []
        L = len(frames) - 1; picks = [0, L // 4, L // 2, (3 * L) // 4]
        seated = name in ("SitDrink", "SitTalk", "Tend")
        for fi in picks:
            set_basis(B.arm, frames[fi]); W = world(B.arm)
            if "ladle" in pr:
                sk = pr["ladle"]; M = socket_world(W, sk)
                o = get("ladle", "cyl", (LADLE_R, -18.0, STIR_TIP_BELOW + 8.0), COLS["wood"]); o.matrix_world = M
                pot = pr["pot"]
                o = get("pot", "cyl", (24.0, -14.0, 22.0), COLS["iron"]); o.matrix_world = Matrix.Translation(pot)
            if "crank" in pr:
                c0, grip = pr["crank"]; g, th = grip(fi / FPS)
                o = get("crank_ring", "ring", (CRANK_R, 0.4), COLS["red"]); o.matrix_world = frame_of(c0, F, RT)
                o = get("spit", "cyl", (1.2, 0.0, 120.0), COLS["iron"]); o.matrix_world = frame_of(c0, F, RT)
                o = get("crank_arm", "cyl", (0.9, 0.0, CRANK_R), COLS["iron"]); o.matrix_world = frame_of(c0, g - c0, F)
                o = get("handle", "cyl", (LADLE_R, -6.0, 6.0), COLS["wood"]); o.matrix_world = frame_of(g, F, RT)
            if "weed" in pr:
                o = get("weed", "ball", (3.0,), COLS["green"]); o.matrix_world = Matrix.Translation(pr["weed"])
            if "bowl" in pr:
                o = get("bowl", "cyl", (9.0, 0.0, 7.0), COLS["clay"]); o.matrix_world = socket_world(W, pr["bowl"])
            if pr.get("sit"):
                sp, e, bf = pr["sit"]
                o = get("bench", "box", (110.0, 32.0, SEAT_Z), COLS["wood"]); o.matrix_world = Matrix.Translation(from_her(0.0, bf - 16.0, SEAT_Z / 2))
                o = get("table", "box", (130.0, 80.0, 5.0), COLS["wood"]); o.matrix_world = Matrix.Translation(from_her(0.0, e + 40.0, TABLE_Z - 2.5))
                if pr.get("mug"):
                    o = get("mug", "cyl", (MUG_R, -MUG_H / 2, MUG_H / 2), COLS["clay"]); o.matrix_world = socket_world(W, pr["mug"])
            if "tray" in pr:
                o = get("tray", "box", (44.0, 32.0, 1.5), COLS["wood"]); o.matrix_world = socket_world(W, pr["tray"]) @ Matrix.Translation((0, 0, 0.75))
                o = get("cup", "cyl", (3.5, 0.0, 9.0), COLS["clay"]); o.matrix_world = socket_world(W, pr["tray"]) @ Matrix.Translation((6.0, 5.0, 1.5))
            # (the skin points measured inside the torso or the legs, marked red)
            co = B.meter.coords(); pts = B.meter.inside_points(W, co)
            if "inside" in made: bpy.data.objects.remove(made.pop("inside"), do_unlink=True)
            if len(pts):
                me = bpy.data.meshes.new("inside"); vs, fs = [], []
                for p in pts[::max(1, len(pts) // 400)]:
                    k = len(vs); vs += [(p[0] + 0.8, p[1], p[2]), (p[0] - 0.8, p[1] + 0.8, p[2]), (p[0] - 0.8, p[1] - 0.8, p[2]), (p[0], p[1], p[2] + 1.2)]
                    fs += [(k, k + 1, k + 2), (k, k + 1, k + 3), (k + 1, k + 2, k + 3), (k, k + 2, k + 3)]
                me.from_pydata(vs, [], fs); o = bpy.data.objects.new("inside", me); sc.collection.objects.link(o); o.color = COLS["red"]
                o.show_in_front = True; made["inside"] = o
            tgt = Vector((0, -20, 62 if seated else 100)); scl = 175 if seated else 215
            for view, ang in (("front", 0), ("side", 90), ("q", 35), ("xray", -35)):
                sc.display.shading.show_xray = view == "xray"; sc.display.shading.xray_alpha = 0.35
                p = os.path.join(PREV_DIR, f"{name}_{fi:03d}_{view}.png")
                shoot(sc, cam, p, tgt, ang, scl); paths.append(p); n += 1
            sc.display.shading.show_xray = False
        sheet(paths, os.path.join(PREV_DIR, f"{name}_sheet.png"), 4)
    log("pictures", n, "in", PREV_DIR)


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
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=MANNY_FBX)
    a3 = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
    out["manny_vs_made_rest_cm"] = round(max((a3.data.bones[b].matrix_local.translation - m.translation).length for b, m in made_rest.items()), 4)
    log("FBX read back:", json.dumps(out))
    return out


def clean(v):
    """the report's values made JSON (vectors as lists; the sockets' Blender frames left out)"""
    if isinstance(v, dict): return {k: clean(x) for k, x in v.items() if not k.startswith("_")}
    if isinstance(v, (list, tuple)): return [clean(x) for x in v]
    if isinstance(v, Vector): return rnd(v)
    if isinstance(v, (np.floating,)): return float(v)
    if isinstance(v, (np.integer,)): return int(v)
    return v


# ---------------------------------------------------------------- main
def main():
    os.makedirs(OUT_DIR, exist_ok=True); os.makedirs(PREV_DIR, exist_ok=True)
    sc, arm, mesh = load()
    idle, idle_info = read_clip(arm, IDLE_FBX)
    walk, walk_info = read_clip(arm, WALK_FBX)
    h = build_helper(sc, arm); rig = Rig(arm, h)
    ctx = C.context(h); DC.add_thumb_op(ctx, h); ctx["cm"] = 1.0
    ctx["cont_w"] = 0.03                     # (the upper arm near its turn a frame before: at rogue_clips' 0.01 the seated gestures' elbows jumped 34 degrees in a frame)
    B = Build(); B.arm, B.mesh, B.h, B.rig, B.ctx = arm, mesh, h, rig, ctx
    meter = Meter(rig, mesh, ctx); B.meter = meter
    HB = h.data.bones
    for s in "lr": ctx["palm"][f"hand_{s}"] = HB[f"hand_{s}"].matrix_local.to_quaternion().inverted() @ meter.palm_n0[s]
    R.arm_context(ctx, h)
    for s in "lr":
        ctx["arms"][s]["local"]["front"] = Y.copy(); ctx["arms"][s]["local"]["up"] = ctx["palm"][f"hand_{s}"].copy()
        up = (HB[f"lowerarm_{s}"].head_local - HB[f"upperarm_{s}"].head_local).normalized()
        fo = (HB[f"hand_{s}"].head_local - HB[f"lowerarm_{s}"].head_local).normalized()
        A = ctx["arms"][s]; old = A["hinge"].copy()
        A["hinge"] = HB[f"upperarm_{s}"].matrix_local.to_quaternion().inverted() @ up.cross(fo).normalized()
        log("elbow %s: reference bend %.0f deg; hinge moved %.0f deg from rogue_clips' (forearm x forward)" % (s, math.degrees(up.angle(fo)), math.degrees(old.angle(A["hinge"]))))
    # (where the reference hand is turned: the wrist's twist limits (rogue_clips.TWIST, +-80) count from it. Measured as
    # the turn about the forearm from a palm facing her middle (thumb forward) to the reference palm)
    B.ref_turn = {}
    for s in "lr":
        fa = (HB[f"hand_{s}"].head_local - HB[f"lowerarm_{s}"].head_local).normalized()
        nz = -OUT[s] - fa * (-OUT[s]).dot(fa); nz.normalize()
        pn = meter.palm_n0[s] - fa * meter.palm_n0[s].dot(fa); pn.normalize()
        ang = math.degrees(nz.angle(pn)) * (1.0 if nz.cross(pn).dot(fa) >= 0.0 else -1.0)
        B.ref_turn[s] = {"deg_from_palm_in": round(ang, 1), "palm_her": rnd(her(meter.palm_n0[s]), 2)}
    log("reference hands: turned from a palm facing her middle by", B.ref_turn)
    # the hand's handedness: the way across the knuckles (little finger to index) against axis x palm
    ctx["hand_sign"] = {}; ctx["across_l"] = {}
    for s in "lr":
        A = ctx["arms"][s]; ax = Y; pn = ctx["palm"][f"hand_{s}"]
        Hq = HB[f"hand_{s}"].matrix_local.to_quaternion()
        t = Hq.inverted() @ (HB[f"index_01_{s}"].head_local - HB[f"pinky_01_{s}"].head_local)
        t = (t - ax * t.dot(ax) - pn * t.dot(pn)).normalized()
        ctx["hand_sign"][s] = 1.0 if ax.cross(pn).dot(t) > 0 else -1.0
        ctx["across_l"][s] = t
    log("hands: across = sign x (axis x palm):", ctx["hand_sign"])
    # the ik bones that sit on a bone in the reference pose follow it (as in the idle: measured)
    AB = arm.data.bones; ctx["ik_follow"] = []
    for ik, b in (("ik_hand_gun", "hand_r"), ("ik_hand_r", "hand_r"), ("ik_hand_l", "hand_l"), ("ik_foot_l", "foot_l"), ("ik_foot_r", "foot_r")):
        if ik not in AB: continue
        rel = AB[b].matrix_local.inverted() @ AB[ik].matrix_local
        e = (idle[0][b] @ rel).translation - idle[0][ik].translation
        ea = math.degrees((idle[0][b] @ rel).to_quaternion().rotation_difference(idle[0][ik].to_quaternion()).angle)
        log("ik %s on %s in the idle: %.2f cm, %.1f deg off its reference place" % (ik, b, e.length, min(ea, 360 - ea)))
        if ik.startswith("ik_hand") and e.length < 1.0: ctx["ik_follow"].append((ik, b, rel))
    B.arm_bones = set()
    B.side_bones = {"l": set(), "r": set()}
    for b in arm.data.bones:
        for s in "lr":
            if b.name == f"upperarm_{s}" or any(p.name == f"upperarm_{s}" for p in b.parent_recursive):
                B.arm_bones.add(b.name); B.side_bones[s].add(b.name)
    for ik, b, rel in ctx["ik_follow"]: B.arm_bones.add(ik)
    B.poser = Poser(rig, ctx, idle[0])
    B.palm_loc = {s: palm_local(B, s, 0.0) for s in "lr"}
    def meter_wrist(W, s):
        A = ctx["arms"][s]; return R.over(*R.wrist_of(A, rig.helper_rot(W, f"lowerarm_{s}"), rig.helper_rot(W, f"hand_{s}")))
    B.meter_wrist = meter_wrist
    # landmarks on the skin (reference pose): the front of the left thigh (a third of the way down, a little out), the
    # top of the knee (above the calf bone's head), the mouth
    set_world(arm, {b.name: b.matrix_local.copy() for b in arm.data.bones}); co = meter.coords(); vl = [tuple(c) for c in co]
    lb = BVHTree.FromPolygons(vl, meter.leg_polys_s["l"])
    th0, ca0 = AB["thigh_l"].head_local, AB["calf_l"].head_local
    pin = th0.lerp(ca0, 0.58); d = (F + OUT["l"] * 0.35).normalized()      # (at 38 % the forearm lay in her hip)
    hit = lb.ray_cast(pin + d * 30.0, -d, 60.0)
    B.thigh_pt = (AB["thigh_l"].matrix_local.inverted() @ hit[0], AB["thigh_l"].matrix_local.to_quaternion().inverted() @ hit[1])
    log("left thigh's front skin %.1f cm from its bone line" % (hit[0] - pin).length)
    kh = lb.ray_cast(ca0 + F * 30.0 + U * 0.0, -F, 60.0)
    B.knee_top = (kh[0] - ca0).length                              # (the knee's thickness in front of its joint: on top when the thigh is level)
    hv = co[meter.headv]; fwd = -hv[:, 1]
    nose = int(np.argmax(np.where(hv[:, 2] > AB["head"].head_local.z, fwd, -1e9)))
    nz = hv[nose, 2]
    band = (np.abs(hv[:, 2] - (nz - 4.5)) < 0.6)
    mi = np.where(band)[0][int(np.argmax(fwd[band]))]
    mouth = Vector(hv[mi])
    B.mouth_local = AB["head"].matrix_local.inverted() @ mouth
    log("knee's skin %.1f cm in front of its joint; nose tip at %s, mouth at %s (her right, forward, up)" % (B.knee_top, rnd(her(Vector(hv[nose])), 1), rnd(her(mouth), 1)))
    # the torso's skin for the arm solver's keep-out (rogue_clips.solve_arm's torso_pts: per bone, points and their
    # outward ways in the stand-in bone's rest frame; one vertex in four)
    nrm0 = np.array([v.normal[:] for v in mesh.data.vertices]); tp = []
    for b in CHAIN + ("clavicle_l", "clavicle_r"):
        idx = meter.torsov[meter.gname[meter.torsov] == b][::4]
        if not len(idx): continue
        Hm = HB[b].matrix_local; R3 = np.array(Hm.to_3x3()); t0 = np.array(Hm.translation)
        tp.append((b, (co[idx] - t0) @ R3, nrm0[idx] @ R3))
    ctx["torso_pts"] = tp
    log("arm keep-out: %d torso skin points" % sum(len(x[1]) for x in tp))
    set_world(arm, idle[0]); m0 = meter.frame(idle[0], meter.coords())
    log("the idle's first frame: wrists %.1f deg past limits, arms in the body %d points" % (m0["wrist_over"], m0["arm_in_body_n"]))
    # ---- the clips
    want = ONLY or ["Stir", "Crank", "Tend", "Scatter", "SitDrink", "SitTalk", "CarryWalk", "CarryIdle", "Talk"]
    clips, report, props = {}, {}, {}
    for name in want:
        log("----", name)
        legs = True
        if name == "Stir": Ws, info, extra, summ, pr = make_stir(B)
        elif name == "Crank": Ws, info, extra, summ, pr = make_crank(B)
        elif name == "Tend": Ws, info, extra, summ, pr = make_tend(B)
        elif name == "Scatter": Ws, info, extra, summ, pr = make_scatter(B)
        elif name == "SitDrink": Ws, info, extra, summ, pr = make_sit(B, name, SIT_LEN_DRINK, True)
        elif name == "SitTalk": Ws, info, extra, summ, pr = make_sit(B, name, SIT_LEN_TALK, False)
        elif name == "CarryWalk":
            Ws, info, extra, summ, pr = make_carry(B, name, walk, len(walk)); info["source"] = walk_info
            info["in_place"] = "the walk's root motion left out (the root at the origin): as MM_Walk_Fwd played with the root locked"
        elif name == "CarryIdle":
            base, wi = idle_loop(B, idle, int(round(CARRY_IDLE_LEN * FPS)))
            Ws, info, extra, summ, pr = make_carry(B, name, base, len(base)); info["idle_window"] = wi
        elif name == "Talk":
            base, wi = idle_loop(B, idle, int(round(TALK_LEN * FPS)))
            Ws, info, extra, summ, pr = make_talk(B, base); info["idle_window"] = wi
        elif name == "Sleep":
            Ws, info, extra, summ, pr = make_sleep(B); legs = False
        rep, rows, frames = measure(B, name, Ws, extra, legs)
        if summ: rep.update(summ(rows))
        rep.update(info)
        if name == "CarryWalk":
            # the legs, pelvis, spine and head against the walk's own (frame for frame)
            Pw = [basis_of(arm, W) for W in walk]; worst = 0.0; worstp = 0.0
            for a, b in zip(frames, Pw):
                for k in a:
                    if k in B.arm_bones: continue
                    x = math.degrees(a[k][1].rotation_difference(b[k][1]).angle); worst = max(worst, min(x, 360 - x))
                    worstp = max(worstp, (a[k][0] - b[k][0]).length)
            rep["body_vs_walk_deg_max"] = round(worst, 5); rep["body_vs_walk_cm_max"] = round(worstp, 5)
            rep["frames_vs_walk"] = [len(frames), len(walk)]
        if name in ("SitDrink", "SitTalk"):
            pr["sit"] = (rows[0]["seat"], rep["table_edge_forward_cm"] if rep["table_edge_forward_cm"] is not None else 25.0,
                         min(her(rows[0]["seat"])[1] + 10.0, rep["bench_front_edge_at_most_forward_cm"]))
        clips[name] = frames; report[name] = rep; props[name] = pr
        log(name, json.dumps(clean(rep)))
    if PREVIEW: previews(B, clips, props)
    js = {"fps": FPS, "skeleton_root": "root", "frames_note": "frame count = length x 30 + 1; the last frame equals the first",
          "axes": "her: (her right, forward, up) cm from the root; ue: UE component space (she faces +Y, her right is -X)",
          "idle_source": idle_info, "wrist_limits_deg": {"flex": list(R.FLEX), "deviation": list(R.DEV), "twist": list(R.TWIST),
                                                         "twist_counted_from": B.ref_turn},
          "clips": clean(report)}
    if ONLY and not WRITE_FBX:
        json.dump(js, open(os.path.join(OUT_DIR, "town_work_clips_partial.json"), "w"), indent=1)
        log("DONE (partial)"); return
    # ---- export (the pose back to the reference pose after keying: the bones' own transforms are read back as it)
    for pb in arm.pose.bones: pb.matrix_basis.identity()
    for name, frames in clips.items(): key_action(arm, name, frames)
    for pb in arm.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    for o in [o for o in sc.objects if o is not arm]: bpy.data.objects.remove(o, do_unlink=True)
    for o in sc.objects: o.select_set(False)
    arm.select_set(True); bpy.context.view_layer.objects.active = arm
    fbx = os.path.join(OUT_DIR, "SK_Manny_Town_Work_Clips.fbx")
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={'ARMATURE'}, add_leaf_bones=False,
                             bake_anim=True, bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
                             bake_anim_simplify_factor=0.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE',
                             use_armature_deform_only=False)
    log("exported", fbx, os.path.getsize(fbx), "bytes")
    made_rest = {b.name: b.matrix_local.copy() for b in arm.data.bones}
    probe = {}
    for name, frames in clips.items():
        for fi in (0, len(frames) // 3, len(frames) - 1):
            set_basis(arm, frames[fi]); probe[(name, fi)] = {b: m.translation.copy() for b, m in world(arm).items()}
    js["fbx"] = os.path.basename(fbx)
    js["fbx_check"] = verify(fbx, made_rest, probe)
    json.dump(js, open(os.path.join(OUT_DIR, "town_work_clips.json"), "w"), indent=1)
    log("DONE")


main()
