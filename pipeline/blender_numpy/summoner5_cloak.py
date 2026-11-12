"""Summoner5's cloak given bones of its own, so it billows behind her (the user's of 2026-11-11: "the cloak should billow
behind the summoner instead of moving with her arms and hands. the cloak breaks apart when the summoner runs. it should
billow behind her when she runs"). Tripo skinned the cloak to the bones nearest it: its panels to her arm twist bones (70
to 100 % of their weight), its back to her neck and head, so it swung with her arms and tore apart where neighbouring
vertices followed different arms.
- The cloak is picked island by island (the mesh is 2015 islands): an island that hangs below her hips (its lowest point
  under the pelvis), is more than 6 cm tall, has under half its weight on her legs and over a third on her arms, head and
  collarbones; not a short piece by her hands (the gloves' parts). Her bell sleeves are found first (her red pieces by
  her arms' bones and what touches them within 6 cm: their gold linings and cuffs) and never taken; then the pieces on the
  cloak join it: the hem's trims (below her hair's ends), its upper strips away from her arms' bones, and its small
  purple and gold pieces lying on it.
- Seven chains of four bones hang from her upper back (spine_05) down the cloak, spread round it from one front edge over
  her back to the other (each chain at an angle round her middle, each joint where the cloak is at that height and angle).
- Each cloak vertex is weighed to the chains by its height (a bone's weight 1 at its middle, shared half and half at a
  joint) and its angle (between the two chains beside it); its top band (from 10 cm under her shoulders up) goes to her
  upper spine and collarbones. Nothing of it is left on her arms, neck or head.
- Each clip's frames turn the chains as they hang from her upper back, her body as the clip has it: back behind her by her
  speed (the clip's pelvis's way over its length; at the hem 10 degrees and 14 more each metre a second, at most 70: her
  walk's 23, her run's 57), little at the top (her hair lies over it there) and more down to the hem; the side panels flare
  out (a fifth of that); a ripple goes down the cloak, its turns a whole number a loop (the loop still closes on itself)
  and stronger with speed.
Writes <out.glb> (the model with the cloak's bones and every clip, keyed by frame) and, with a prefix, pictures of each
clip at a few frames from the front, side, back and three-quarter.
The Rogue's body (Rogue2.glb, the user's of 2026-11-12: "the rogue's shoot and other animations involving her arms take
part of her cloak with her forward ... use the same solution for the cloak that was used for the new summoner model"):
`--hero Rogue2`. Tripo skinned her cloak the same way (its panels 56 to 74 % on her upper arms' twist bones, both arms,
16 % on her head). Her cloak is longer (from her shoulders, 0.81, to her ankles, 0.06), her hair reaches lower (0.60)
and she is all in black: her profile's heights and the colours of the small pieces that join it (HERO below); no sleeve
of hers is red, so none is kept apart.
Blender: -b -P summoner5_cloak.py -- Summoner5.glb out.glb [picture_prefix] [--hero Summoner5 | Rogue2]"""
import bpy, bmesh, sys, os, math
from mathutils import Vector, Matrix, Quaternion
from collections import defaultdict
argv = sys.argv[sys.argv.index("--") + 1:]
HERO_NAME = "Summoner5"
if "--hero" in argv:
    _k = argv.index("--hero"); HERO_NAME = argv[_k + 1]; argv = argv[:_k] + argv[_k + 2:]
SRC, OUT = argv[0], argv[1]
PICS = argv[2] if len(argv) > 2 else None
FPS = 24
# (each body's numbers, the model's units (1.0 tall): the Summoner's as they were built)
HERO = {
    "Summoner5": {"height_m": 1.65, "joints": (0.66, 0.54, 0.42, 0.29, 0.16), "top": (0.60, 0.70), "grow_top": 0.56,
                  "small": ("purple", "gold")},
    # (her shoulders' joints at 0.814, her cloak's top 0.81 and its hem's lowest 0.056; her hair's ends at 0.60)
    "Rogue2": {"height_m": 1.70, "joints": (0.76, 0.585, 0.41, 0.235, 0.06), "top": (0.71, 0.79), "grow_top": 0.60,
               "small": ("black", "other")},
}[HERO_NAME]
HEIGHT_M = HERO["height_m"]                        # (her height in the viewer and the game: the model is 1.0 tall)
CHAINS = (-95.0, -62.0, -30.0, 0.0, 30.0, 62.0, 95.0)  # (degrees round her middle from straight behind; + toward her left)
JOINTS = HERO["joints"]                            # (heights of the chains' joints, the model's units: shoulders to hem)
SHARE = (0.05, 0.25, 0.35, 0.35)                   # (each bone's part of the turn back: little under her hair)
TOP = HERO["top"]                                  # (the top band: from all chain to all spine over these heights)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
sc = bpy.context.scene; sc.render.fps = FPS
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
me = next(o for o in sc.objects if o.type == 'MESH' and o.vertex_groups)
for o in [o for o in sc.objects if o.type == 'MESH' and o is not me]: bpy.data.objects.remove(o, do_unlink=True)
ad = arm.animation_data_create()
for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
ad.action = None
for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'; pb.matrix_basis.identity()
bpy.context.view_layer.update()
import json, struct
_raw = open(SRC, "rb").read(); _J = json.loads(_raw[20:20 + struct.unpack("<I", _raw[12:16])[0]])
_ORDER = [x.get("name") for x in _J.get("animations", [])]
# (the GLB's own order, walk before run: Blender lists the actions by name, and the export wrote run first)
ACTS = sorted(bpy.data.actions, key=lambda a: _ORDER.index(a.name) if a.name in _ORDER else len(_ORDER))
print("CLOAK clips", [a.name for a in ACTS])
AW = arm.matrix_world.copy(); AWI = AW.inverted()
assert (AW.to_scale() - Vector((1, 1, 1))).length < 1e-4, "the armature is scaled: the heights below are the model's own"
MW = me.matrix_world; V = me.data.vertices
names = {g.index: g.name for g in me.vertex_groups}
B = arm.data.bones
SP = AW @ B["spine_05"].head_local; CX, CY = SP.x, SP.y   # (her middle, seen from above)
HANDS = [AW @ B[f"hand_{s}"].head_local for s in "lr"]
PELVIS_Z = (AW @ B["pelvis"].head_local).z


# ---------------------------------------------------------------- the cloak, island by island
def cat(n):
    if n.startswith(("thigh", "calf", "foot", "ball")): return "leg"
    if n.startswith(("upperarm", "lowerarm", "hand")) or n.split("_")[0] in ("thumb", "index", "middle", "ring", "pinky"): return "arm"
    if n.startswith(("head", "neck")): return "head"
    if n.startswith("clavicle"): return "clav"
    return "trunk"


bm = bmesh.new(); bm.from_mesh(me.data); bm.verts.ensure_lookup_table()
seen = [False] * len(bm.verts); ISL = []
for v0 in bm.verts:
    if seen[v0.index]: continue
    stack = [v0]; seen[v0.index] = True; ids = []
    while stack:
        v = stack.pop(); ids.append(v.index)
        for e in v.link_edges:
            w = e.other_vert(v)
            if not seen[w.index]: seen[w.index] = True; stack.append(w)
    ps = [MW @ V[i].co for i in ids]; zs = [p.z for p in ps]; mid = sum(ps, Vector()) / len(ps)
    c = defaultdict(float)
    for i in ids:
        for g in V[i].groups: c[cat(names[g.group])] += g.weight
    tot = sum(c.values()) or 1.0
    sh = {k: c[k] / tot for k in ("leg", "arm", "head", "clav", "trunk")}
    # (a glove's piece: short, its middle within 4 cm of a hand's bone; at 7 cm bits of the cloak's lining beside her hands
    # were taken for gloves, left on her arms, and tore 77 cm from the cloak in the run (tearall's measure))
    glove = max(zs) - min(zs) < 0.15 and min((mid - h).length for h in HANDS) < 0.04
    ISL.append((ids, ps, min(zs), max(zs), sh, glove))
bm.free()
picked = [k for k, (ids, ps, lo, hi, sh, glove) in enumerate(ISL)
          if lo < PELVIS_Z - 0.03 and hi - lo > 0.06 and sh["leg"] < 0.5 and sh["arm"] + sh["head"] + sh["clav"] > 0.35 and not glove]
from mathutils.kdtree import KDTree
from mathutils.geometry import intersect_point_line
import numpy as np
SEGS = [(AW @ B[f"upperarm_{s}"].head_local, AW @ B[f"lowerarm_{s}"].head_local) for s in "lr"] + \
       [(AW @ B[f"lowerarm_{s}"].head_local, AW @ B[f"hand_{s}"].head_local) for s in "lr"]


def from_arm(p):
    best = 9.0
    for a_, b_ in SEGS:
        q, t = intersect_point_line(p, a_, b_); t = max(0.0, min(1.0, t)); best = min(best, (p - a_.lerp(b_, t)).length)
    return best


ARMD = [sum(from_arm(p) for p in ps) / len(ps) for ids, ps, lo, hi, sh, glove in ISL]   # (each piece's mean distance)
# (each vertex's colour from the texture, by its loops' UVs)
_img = next(n.image for n in me.data.materials[0].node_tree.nodes if n.type == 'TEX_IMAGE' and n.image)
_W, _H = _img.size; _px = np.array(_img.pixels[:], dtype=np.float32).reshape(_H, _W, 4)
_uv = me.data.uv_layers.active.data; _vc = np.zeros((len(V), 3)); _vn = np.zeros(len(V))
for poly in me.data.polygons:
    for li in poly.loop_indices:
        u_, v_ = _uv[li].uv; vi = me.data.loops[li].vertex_index
        _vc[vi] += _px[min(_H - 1, max(0, int(v_ % 1.0 * _H))), min(_W - 1, max(0, int(u_ % 1.0 * _W))), :3]; _vn[vi] += 1
_vc /= np.maximum(_vn, 1)[:, None]


def colour(ids):
    r, g, b = _vc[ids].mean(axis=0); mx = max(r, g, b)
    if mx < 0.12: return "black"                                          # (the gloves)
    if b > r * 0.8 and mx < 0.45: return "purple"                         # (the cloak's outside)
    if r > 0.35 and g < 0.45 * r and b < 0.45 * r: return "red"           # (her dress and sleeves)
    if r > 0.4 and g > 0.25 * r and b < 0.55 * g: return "gold"           # (the cloak's lining and trims; her cuffs too)
    return "other"


def kd_of(ks):
    pts = [p for k in ks for p in ISL[k][1]]; kd = KDTree(len(pts))
    for j, p in enumerate(pts): kd.insert(p, j)
    kd.balance(); return kd


# her sleeves, first, so that no pass below takes them: wide bell sleeves, red outside and lined and cuffed in gold like
# the cloak, flaring 5 to 6 cm from the arm's bones where they touch the cloak's side panels. The growth passes took
# their bell's pieces (strips at her elbows), and a pass by colour their gold back panels, which flew off with the cloak
# and left the sleeve open (pictures of the marked pieces at rest and in the run). A sleeve: her red pieces mostly on her
# arms within 5 cm of their bones, and every piece mostly on her arms within 6 cm that touches them (a fifth of its
# vertices within 5 mm), its lining, cuffs and trims, until none does
SLEEVE = {k for k, (ids, ps, lo, hi, sh, glove) in enumerate(ISL) if k not in picked and sh["arm"] >= 0.6 and ARMD[k] < 0.05 and colour(ids) == "red"}
while SLEEVE:                                      # (none on the Rogue: nothing of hers is red)
    kd = kd_of(SLEEVE); new = []
    for k, (ids, ps, lo, hi, sh, glove) in enumerate(ISL):
        if k in SLEEVE or k in picked or sh["arm"] < 0.5 or ARMD[k] >= 0.06: continue
        if sum(1 for p in ps if kd.find(p)[2] < 0.005) >= 0.2 * len(ps): new.append(k)
    if not new: break
    SLEEVE.update(new)
print("CLOAK her sleeves: %d pieces, %d vertices, kept on her arms" % (len(SLEEVE), sum(len(ISL[k][0]) for k in SLEEVE)))
# (and the small pieces on it: the hem's gold teeth and trims, too short for the rule, were left on her arms and hung in
# the air where the cloak had been (the first pictures). Any piece whose vertices lie within 1.5 cm of the cloak on
# average, no leg's, trunk's, glove's, sleeve's or hair's, joins it, until none does. Hair lies on the cloak's back: grown
# without a height its strands joined (531 pieces, 9917 vertices) and streamed back with it; her hair ends at 0.54, the
# pieces looked for hang below 0.56)
GROW_TOP = HERO["grow_top"]
inside = set(picked); grown = 0
while True:
    kd = kd_of(inside); new = []
    for k, (ids, ps, lo, hi, sh, glove) in enumerate(ISL):
        if k in inside or k in SLEEVE or glove or hi > GROW_TOP or sh["leg"] >= 0.5 or sh["trunk"] >= 0.5 or sh["head"] >= 0.6 or len(ids) > 400: continue
        if sum(kd.find(p)[2] for p in ps) / len(ps) < 0.015: new.append(k)
    if not new: break
    inside.update(new); grown += len(new)
# (and the cloak's upper pieces still on her arms: strips of it over her shoulders went on swinging with her arms in the
# run (pictures coloured by the bone that moves each vertex). A piece mostly on her arms, not a sleeve's, 4 cm or more
# from their bones on average and within 2 cm of the cloak, no hair's (head under 30 %), joins it, up to her shoulders)
upper = 0
while True:
    kd = kd_of(inside); new = []
    for k, (ids, ps, lo, hi, sh, glove) in enumerate(ISL):
        if k in inside or k in SLEEVE or glove or sh["arm"] < 0.5 or sh["head"] >= 0.3 or len(ids) > 400: continue
        if sum(kd.find(p)[2] for p in ps) / len(ps) < 0.02 and ARMD[k] > 0.04: new.append(k)
    if not new: break
    inside.update(new); upper += len(new)
print("CLOAK and %d of its upper pieces off her arms" % upper)
# (and the small pieces of it lying on it: half or more of a piece's vertices within 1 cm of the cloak's, 60 vertices or
# fewer, of its colours (purple, gold), no leg's, trunk's, hair's, glove's or sleeve's: the lining's bits beside her hands
# were taken for gloves at first and tore 77 cm from the cloak in the run (tearall's measure))
touching = 0
while True:
    kd = kd_of(inside); new = []
    for k, (ids, ps, lo, hi, sh, glove) in enumerate(ISL):
        if k in inside or k in SLEEVE or glove or len(ids) > 60 or sh["leg"] >= 0.5 or sh["trunk"] >= 0.5 or sh["head"] >= 0.5: continue
        if sum(1 for p in ps if kd.find(p)[2] < 0.01) >= 0.5 * len(ps) and colour(ids) in HERO["small"]: new.append(k)
    if not new: break
    inside.update(new); touching += len(new)
print("CLOAK and %d small pieces of it lying on it" % touching)
CLOAK = set(i for k in inside for i in ISL[k][0])
gz = [ISL[k][3] for k in inside if k not in picked]
print("CLOAK picked %d islands by the rule and %d pieces on them (their tops %.2f to %.2f), %d vertices of %d" % (
    len(picked), grown, min(gz) if gz else 0, max(gz) if gz else 0, len(CLOAK), len(V)))
P = {i: MW @ V[i].co for i in CLOAK}


def theta(p): return math.degrees(math.atan2(p.x - CX, p.y - CY))   # (0 behind her (+Y), + toward her left (+X))


TH = {i: theta(P[i]) for i in CLOAK}
_ths = sorted(TH.values())
print("CLOAK its angles round her: %.0f to %.0f (1 %% and 99 %%), the rule's pieces' colours %s" % (
    _ths[len(_ths) // 100], _ths[-1 - len(_ths) // 100], dict(sorted(defaultdict(int, {c: sum(1 for k in picked if colour(ISL[k][0]) == c) for c in ("black", "purple", "red", "gold", "other")}).items()))))


# ---------------------------------------------------------------- the chains: each joint where the cloak is
def place(th, z):
    """the cloak's mean distance from her middle near this angle and height, the joint there"""
    for dth, dz in ((10, 0.03), (20, 0.05), (35, 0.08)):
        rs = [math.hypot(P[i].x - CX, P[i].y - CY) for i in CLOAK if abs(TH[i] - th) < dth and abs(P[i].z - z) < dz]
        if len(rs) >= 6: break
    r = sorted(rs)[len(rs) // 2] if rs else 0.15
    a = math.radians(th)
    return Vector((CX + r * math.sin(a), CY + r * math.cos(a), z))


bpy.context.view_layer.objects.active = arm; arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
EB = arm.data.edit_bones
CB = []                                            # [chain][bone] names
for c, th in enumerate(CHAINS):
    pts = [AWI @ place(th, z) for z in JOINTS]; names_c = []
    for k in range(len(JOINTS) - 1):
        n = f"cloak_{c}_{k}"; eb = EB.new(n); eb.head = pts[k]; eb.tail = pts[k + 1]
        eb.roll = 0.0; eb.use_deform = True
        eb.parent = EB["spine_05"] if k == 0 else EB[names_c[-1]]; eb.use_connect = k > 0
        names_c.append(n)
    CB.append(names_c)
bpy.ops.object.mode_set(mode='POSE')
for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
bpy.ops.object.mode_set(mode='OBJECT')
print("CLOAK bones: %d chains of %d" % (len(CB), len(CB[0])), [tuple(round(v, 3) for v in (AW @ arm.data.bones[ch[0]].head_local)) for ch in CB])

# ---------------------------------------------------------------- the weights
groups = {g.name: g for g in me.vertex_groups}
for ch in CB:
    for n in ch: groups[n] = me.vertex_groups.new(name=n)
for n in ("spine_05", "clavicle_l", "clavicle_r"): assert n in groups, n
nseg = len(JOINTS) - 1


def chain_weights(p, th):
    """{bone: weight}: the two chains beside its angle, the bones along them by its height"""
    out = defaultdict(float)
    if th <= CHAINS[0]: pair = [(0, 1.0)]
    elif th >= CHAINS[-1]: pair = [(len(CHAINS) - 1, 1.0)]
    else:
        j = max(k for k in range(len(CHAINS) - 1) if CHAINS[k] <= th); f = (th - CHAINS[j]) / (CHAINS[j + 1] - CHAINS[j])
        pair = [(j, 1.0 - f), (j + 1, f)]
    # (its place along the chain in bones: 0 at the top joint, nseg at the hem)
    z = p.z
    if z >= JOINTS[0]: u = 0.0
    elif z <= JOINTS[-1]: u = float(nseg) - 1e-6
    else:
        k = max(i for i in range(nseg) if JOINTS[i] >= z); u = k + (JOINTS[k] - z) / (JOINTS[k] - JOINTS[k + 1])
    bw = [max(0.0, 1.0 - abs(u - (k + 0.5))) if not (k == 0 and u < 0.5) and not (k == nseg - 1 and u > nseg - 0.5) else 1.0 for k in range(nseg)]
    s = sum(bw); bw = [w / s for w in bw]
    for c, fc in pair:
        for k, w in enumerate(bw):
            if fc * w > 1e-4: out[CB[c][k]] += fc * w
    return out


for i in CLOAK:
    v = V[i]; p = P[i]
    for g in list(v.groups): me.vertex_groups[g.group].remove([i])
    up = min(1.0, max(0.0, (p.z - TOP[0]) / (TOP[1] - TOP[0]))); up = up * up * (3 - 2 * up)
    w = {k: x * (1.0 - up) for k, x in chain_weights(p, TH[i]).items()}
    if up > 0:
        side = min(1.0, max(0.0, (abs(p.x - CX) - 0.05) / 0.06)) * 0.7
        w["spine_05"] = w.get("spine_05", 0.0) + up * (1.0 - side)
        cl = "clavicle_l" if p.x > CX else "clavicle_r"; w[cl] = w.get(cl, 0.0) + up * side
    for n, x in w.items():
        if x > 1e-4: groups[n].add([i], x, 'REPLACE')
print("CLOAK weights: %d vertices on the chains and her upper spine and collarbones" % len(CLOAK))


# ---------------------------------------------------------------- the chains' turns, frame by frame
def set_action(act):
    ad.action = act
    try:
        if act.slots: ad.action_slot = act.slots[0]
    except Exception: pass


BACK = Vector((0.0, 1.0, 0.0))                    # (behind her, in her rest frame)
for act in ACTS:
    set_action(act)
    f0, f1 = [int(round(x)) for x in act.frame_range]; dur = (f1 - f0) / FPS
    sc.frame_set(f0); a0 = (AW @ arm.pose.bones["pelvis"].head).copy()
    sc.frame_set(f1); a1 = (AW @ arm.pose.bones["pelvis"].head).copy()
    way = Vector((a1.x - a0.x, a1.y - a0.y, 0.0)).length
    v = way / dur * HEIGHT_M                     # (m/s at her height)
    # (degrees back at the hem: at 10 + 14 a metre a second the run's 59 laid the cloak out flat behind her like a flag;
    # standing (her idle) it hangs: the 10 comes in by half a metre a second)
    hem = min(50.0, 10.0 * min(1.0, v / 0.5) + 11.0 * v)
    flut = 3.0 + 2.5 * v                         # (the ripple's turn at the hem, degrees)
    cyc = 2                                      # (ripples a loop: one a step)
    print("CLOAK %s: %d frames, %.2f m/s at her height: %.0f degrees back at the hem, a ripple of %.0f" % (act.name, f1 - f0 + 1, v, hem, flut))
    rest_sp = arm.data.bones["spine_05"].matrix_local
    for f in range(f0, f1 + 1):
        sc.frame_set(f); bpy.context.view_layer.update()
        t = (f - f0) / FPS; ph = 2.0 * math.pi * cyc * t / dur
        sp = arm.pose.bones["spine_05"]
        Qs = sp.matrix.to_quaternion() @ rest_sp.to_quaternion().inverted()   # (her upper back's turn from its rest)
        for c, (th, ch) in enumerate(zip(CHAINS, CB)):
            side = math.sin(math.radians(th))                                 # (-1 her right edge, +1 her left)
            back_sum = 0.0; flare_sum = 0.0
            for k, n in enumerate(ch):
                pb = arm.pose.bones[n]; rb = arm.data.bones[n]
                q_rest = rb.matrix_local.to_quaternion(); d0 = q_rest @ Vector((0.0, 1.0, 0.0))
                rip = flut * (k + 1) / len(ch) * (math.sin(ph - 0.9 * k + 0.6 * c) + 0.35 * math.sin(1.5 * ph - 1.3 * k + 1.1 * c + 0.4))
                back_sum += SHARE[k] * hem + (rip / len(ch) if k else 0.0)
                flare_sum += SHARE[k] * hem * 0.12 * abs(side)                # (at a fifth the run's panels spread like wings)
                # (back: a turn about her rest's +X takes the hanging way (-Z) toward behind her (+Y); the flare: about her
                # forward axis, outward to the panel's own side)
                qb = Quaternion(Vector((1.0, 0.0, 0.0)), math.radians(back_sum))
                qf = Quaternion(Vector((0.0, 1.0, 0.0)), math.radians(-flare_sum if side > 0 else flare_sum))
                want = Qs @ (qf @ qb @ d0)
                q0 = Qs @ q_rest
                q = (q0 @ Vector((0.0, 1.0, 0.0))).rotation_difference(want) @ q0
                if k == 0:
                    head = sp.matrix @ (rest_sp.inverted() @ rb.head_local)
                else:
                    head = pb.parent.tail.copy()
                pb.matrix = Matrix.LocRotScale(head, q, Vector((1.0, 1.0, 1.0)))
                bpy.context.view_layer.update()
                pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
ad.action = None

# ---------------------------------------------------------------- pictures, then the GLB
if PICS:
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'TEXTURE'; sc.display.shading.light = 'STUDIO'
    sc.render.resolution_x = 520; sc.render.resolution_y = 600
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.15; cam.data.clip_end = 100
    for act in ACTS:
        set_action(act); f0, f1 = [int(round(x)) for x in act.frame_range]
        for f in sorted({f0, f0 + (f1 - f0) // 4, f0 + (f1 - f0) // 2, f0 + 3 * (f1 - f0) // 4}):
            sc.frame_set(f); pv = AW @ arm.pose.bones["pelvis"].head
            for view, ang in (("front", 0), ("side", 90), ("back", 180), ("q", 35)):
                r = math.radians(ang); d = Vector((math.sin(r), -math.cos(r), 0.05))
                cam.location = Vector((pv.x, pv.y, 0.5)) + d * 6; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
                sc.render.filepath = f"{PICS}_{act.name.split('.')[0]}_{f}_{view}.png"; bpy.ops.render.render(write_still=True)
    ad.action = None
    bpy.data.objects.remove(cam, do_unlink=True)

for act in ACTS:
    act.use_fake_user = True
    tr = ad.nla_tracks.new(); tr.name = act.name; st = tr.strips.new(act.name, int(act.frame_range[0]), act); st.name = act.name
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_animations=True, export_animation_mode='NLA_TRACKS',
                          export_force_sampling=True, export_optimize_animation_size=False, export_skins=True, export_yup=True)
print("CLOAK DONE", OUT, os.path.getsize(OUT))
