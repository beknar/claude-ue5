"""Aurorim, the final boss of Mistward Castle's tier 5 (the user's spec of 2026-11-03), from `ai models/Aurorim Low.glb` (a
Tripo angel on a Mixamo rig: 65 bones, no wing bones; its own clips: three punches, a kick, walk, run, hit reactions) to the
FBX pair 600_tripo_import.py reads (as tripo_build.py writes it):
  SK_JRPG_Aurorim.fbx        the skinned mesh (centimetres, BODY_CM to the top of the head)
  SK_JRPG_Aurorim_Clips.fbx  the clips, as actions A_<Clip>
  T_Aurorim_<role>.png, build.json

What it adds:
  - the bones' names without "mixamorig:"
  - four wings (two above the shoulders, two at the waist): the mesh is 3030 islands, and the wings' were skinned to the arms
    and shoulders by Tripo (they bent with every punch). An island is a wing's when it lies behind the back (its middle more
    than WING_BACK behind the spine's line) and most of its weight is on an arm, a shoulder or the upper spine; its side and
    row from its middle (row: above or below WING_SPLIT). Each wing gets a chain of three bones from its root (its points
    nearest the spine) to its tip (its farthest point), parented to Spine2; its vertices are skinned to the chain alone
    (blended between neighbouring bones, the root's fifth half on Spine2 so the wing stays on the back).
  - the clips the boss needs, made by aiming bones (each a direction in the armature's space; a bone not aimed follows its
    parent): Idle (hovering: arms relaxed, legs hanging, toes down), Fly (leaning into it), Throw (a lance over the right
    shoulder, released at THROW_RELEASE of the clip), Cast (both arms up to the sky, the right brought down at the foe at
    CAST_RELEASE: the light falls there), Death (the wings folded back, falling backwards to lie on the floor)
  - his own clips kept for the fists: Box_01, Box_02, Box_03 (punches), Hit_to_body_01 (his flinch); the others dropped
  - a wing beat in every clip (slow when he hovers, quicker in flight, folded in death)
The levitating itself is the game's: the mesh is raised over his capsule and bobs (RDAurorim.cpp).

Blender: -b -P aurorim_build.py -- "<glb>" <out_dir> [<preview_dir>]       (preview: key frames of each clip, front and side)
Coordinates: Blender, front toward -Y, left +X, up +Z; after the scale, centimetres."""
import bpy, bmesh, sys, os, json, math, re
from mathutils import Matrix, Vector, Quaternion

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = argv[0], argv[1]
PREVIEW = argv[2] if len(argv) > 2 else None
NAME, TAG = "SK_JRPG_Aurorim", "Aurorim"
BODY_CM = 190.0                 # the top of his head (the wing tips stand higher)
FPS = 24
WING_BACK = 0.03                # (in the GLB's units: its body is 0.84 tall) an island behind the spine's line by this
WING_SPLIT = 0.66               # the two rows of wings meet at this height
THROW_RELEASE = 0.54
CAST_RELEASE = 0.59
KEEP = {"Box_01", "Box_02", "Box_03", "Hit_to_body_01"}
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=SRC)
sc.render.fps = FPS
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
meshes = [o for o in sc.objects if o.type == 'MESH' and o.vertex_groups]
for o in [o for o in sc.objects if o.type == 'MESH' and o not in meshes]: bpy.data.objects.remove(o, do_unlink=True)
mesh = meshes[0]
arm.name = "Armature"; arm.data.name = "Armature"; mesh.name = NAME
ad = arm.animation_data or arm.animation_data_create()
for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)

# ---- the textures, named by what they feed (as tripo_build.py)
roles = {}
for m in bpy.data.materials:
    if not m.use_nodes: continue
    for n in m.node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image:
            for l in n.outputs[0].links:
                roles[n.image.name] = {"BSDF_PRINCIPLED": "Color", "SEPARATE_COLOR": "MetalRough", "NORMAL_MAP": "Normal"}.get(l.to_node.type, "Tex")
tex = {}
for img in bpy.data.images:
    if img.packed_file or img.has_data:
        r = roles.get(img.name, img.name.replace(" ", "_"))
        p = os.path.join(OUT, f"T_{TAG}_{r}.png"); img.filepath_raw = p; img.file_format = 'PNG'; img.save(); tex[r] = p

# ---- his own clips, sampled on the GLB's armature (bone basis per frame); kept ones only
for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
sampled = {}
for act in list(bpy.data.actions):
    nm = re.sub(r"[^A-Za-z0-9_]+", "_", act.name.split(".")[0]).strip("_"); nm = nm[:1].upper() + nm[1:]
    if nm not in KEEP: continue
    ad.action = act
    if hasattr(ad, "action_slot") and act.slots: ad.action_slot = act.slots[0]
    f0, f1 = [int(round(v)) for v in act.frame_range]
    fr = []
    for t in range(f0, f1 + 1):
        sc.frame_set(t); fr.append({pb.name.replace("mixamorig:", ""): pb.matrix_basis.decompose() for pb in arm.pose.bones})
    sampled[nm] = fr
ad.action = None
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
print("sampled", {k: len(v) for k, v in sampled.items()})

# ---- the wings: islands behind the back, mostly on an arm / a shoulder / the upper spine (in the GLB's units)
mw = mesh.matrix_world.copy()
V0 = [mw @ v.co for v in mesh.data.vertices]
gname = {g.index: g.name.replace("mixamorig:", "") for g in mesh.vertex_groups}
bm = bmesh.new(); bm.from_mesh(mesh.data); bm.verts.ensure_lookup_table()
seen = [False] * len(bm.verts); islands = []
for v0 in bm.verts:
    if seen[v0.index]: continue
    st = [v0]; seen[v0.index] = True; ids = []
    while st:
        v = st.pop(); ids.append(v.index)
        for e in v.link_edges:
            w = e.other_vert(v)
            if not seen[w.index]: seen[w.index] = True; st.append(w)
    islands.append(ids)
bm.free()
spine_y = sum(V0[i].y for i in range(len(V0))) / len(V0)          # (roughly the body's middle front to back)
UPPER = {"LeftArm", "RightArm", "LeftShoulder", "RightShoulder", "Spine2", "Spine1", "Neck"}
wing_of = {}
for ids in islands:
    c = sum((V0[i] for i in ids), Vector()) / len(ids)
    if c.y < spine_y + WING_BACK: continue
    w = {}
    for i in ids:
        for g in mesh.data.vertices[i].groups: w[gname[g.group]] = w.get(gname[g.group], 0.0) + g.weight
    tot = sum(w.values()) or 1.0
    if sum(v for k, v in w.items() if k in UPPER) / tot < 0.6: continue          # (hair: the head and neck; the robe: the hips, legs)
    if abs(c.x) < 0.015: continue                                                  # (the spine's own line: hair between the wings)
    side = "l" if c.x > 0 else "r"; row = "u" if c.z > WING_SPLIT else "d"
    for i in ids: wing_of[i] = row + side
report = {"wing_vertices": {k: sum(1 for v in wing_of.values() if v == k) for k in ("ul", "ur", "dl", "dr")}}
print("wings", report["wing_vertices"])

# ---- the scale: the top of his head at BODY_CM (as tripo_build: centimetres in a scene of scale_length 0.01)
B = arm.data.bones
head_top = (arm.matrix_world @ B["mixamorig:HeadTop_End"].head_local).z
S = BODY_CM / (head_top - min(v.z for v in V0))
sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 0.01
mwm = mesh.matrix_world.copy(); mesh.parent = None; mesh.matrix_world = mwm
for o in (arm, mesh): o.matrix_world = Matrix.Scale(S, 4) @ o.matrix_world
bpy.ops.object.select_all(action='DESELECT')
for o in (arm, mesh): o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
mesh.parent = arm; mesh.matrix_parent_inverse.identity()
mods = [m for m in mesh.modifiers if m.type == 'ARMATURE'] or [mesh.modifiers.new("Armature", 'ARMATURE')]
for m in mods: m.object = arm
for b in arm.data.bones: b.name = b.name.replace("mixamorig:", "")
for g in mesh.vertex_groups: g.name = g.name.replace("mixamorig:", "")
bpy.context.view_layer.update()
V = [v.co.copy() for v in mesh.data.vertices]          # (the mesh's space is the armature's now, in cm)

# ---- the wing chains: root (the points nearest the spine), tip (the farthest from it), three bones; skinned to them
chains = {}
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
for wid in ("ul", "ur", "dl", "dr"):
    ids = [i for i, w in wing_of.items() if w == wid]
    if not ids: continue
    ids.sort(key=lambda i: abs(V[i].x))
    near = ids[:max(8, len(ids) // 12)]
    root = sum((V[i] for i in near), Vector()) / len(near)
    far = sorted(ids, key=lambda i: (V[i] - root).length)[-max(4, len(ids) // 60):]
    tip = sum((V[i] for i in far), Vector()) / len(far)
    J = [root.lerp(tip, k / 3.0) for k in range(4)]
    names = [f"wing_{wid}_{k + 1}" for k in range(3)]
    for k, n in enumerate(names):
        b = eb.new(n); b.head = J[k]; b.tail = J[k + 1]; b.roll = 0.0
        b.parent = eb["Spine2"] if k == 0 else eb[names[k - 1]]; b.use_connect = k > 0; b.use_deform = True
    chains[wid] = {"bones": names, "root": list(root), "tip": list(tip), "n": len(ids)}
bpy.ops.object.mode_set(mode='OBJECT')
for wid, ch in chains.items():
    root, tip = Vector(ch["root"]), Vector(ch["tip"]); d = tip - root; L2 = d.length_squared
    gs = [mesh.vertex_groups.get(n) or mesh.vertex_groups.new(name=n) for n in ch["bones"]]
    sp = mesh.vertex_groups.get("Spine2")
    for i, w in wing_of.items():
        if w != wid: continue
        for g in list(mesh.data.vertices[i].groups): mesh.vertex_groups[g.group].remove([i])
        t = max(0.0, min(1.0, (V[i] - root).dot(d) / L2)) * 3.0
        k = min(2, int(t)); f = t - k
        wts = {k: 1.0}
        if f > 0.7 and k < 2: wts = {k: 1.0 - (f - 0.7) / 0.6, k + 1: (f - 0.7) / 0.6}
        elif f < 0.3 and k > 0: wts = {k: 0.5 + f / 0.6, k - 1: 0.5 - f / 0.6}
        root_share = max(0.0, 0.5 - t / 0.6 * 0.5) if t < 0.6 else 0.0       # (the root half on the back)
        for kk, ww in wts.items(): gs[kk].add([i], ww * (1.0 - root_share), 'REPLACE')
        if root_share > 0 and sp: sp.add([i], root_share, 'REPLACE')
report["chains"] = {k: {"n": v["n"], "root": [round(c, 1) for c in v["root"]], "tip": [round(c, 1) for c in v["tip"]]} for k, v in chains.items()}
print("chains", json.dumps(report["chains"]))

# ---- posing by directions: a bone's world delta rotation from its rest direction to the one asked; others follow
B = arm.data.bones
for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
REST = {b.name: b.matrix_local.to_quaternion() for b in B}
RDIR = {b.name: (b.tail_local - b.head_local).normalized() for b in B}
ORDER = []
def _walk(b):
    ORDER.append(b.name)
    for c in b.children: _walk(c)
for b in B:
    if b.parent is None: _walk(b)

def qaxis(axis, deg): return Quaternion(Vector(axis).normalized(), math.radians(deg))
def aim(rest_dir, want): return Vector(rest_dir).rotation_difference(Vector(want).normalized())

def pose_frame(aims=None, turns=None, hips_move=None):
    """aims: bone -> direction (armature space); turns: bone -> delta quaternion about rest axes (relative to its parent);
    hips_move: a translation of the hips (cm). Returns {bone: (loc, rot, scale)} as basis values."""
    aims = aims or {}; turns = turns or {}
    Qw = {}; out = {}
    for n in ORDER:
        b = B[n]; Qp = Qw[b.parent.name] if b.parent else Quaternion()
        if n in aims: Qc = Qp.inverted() @ aim(RDIR[n], aims[n])
        else: Qc = turns.get(n, Quaternion())
        if n in aims and n in turns: Qc = Qc @ turns[n]
        Qw[n] = Qp @ Qc
        rot = REST[n].inverted() @ Qc @ REST[n]
        loc = Vector()
        if n == "Hips" and hips_move is not None: loc = REST[n].inverted() @ Vector(hips_move)
        out[n] = (loc, rot, Vector((1, 1, 1)))
    return out

def wings(phase, beat, spread, fold=0.0):
    """the four wings' delta rotations: a beat (tips forward and back), a spread (in the back's plane), each bone further
    out lagging; fold: the tips swept back"""
    t = {}
    for wid, ch in chains.items():
        root, tip = Vector(ch["root"]), Vector(ch["tip"]); d = (tip - root).normalized()
        back = Vector((0, 1, 0)); ab = back.cross(d).normalized()
        sgn = 1.0 if wid[1] == "l" else -1.0
        row = 1.0 if wid[0] == "u" else -0.6
        for k, n in enumerate(ch["bones"]):
            lag = phase - 0.6 * k
            b = (beat * math.sin(lag) - fold) * (1.0 if k == 0 else 0.45)
            s = sgn * row * spread * math.sin(lag) * (1.0 if k == 0 else 0.3)
            t[n] = qaxis(ab, b) @ qaxis(back, s)
    return t

def lerp_dir(a, b, f): return Vector(a).normalized().slerp(Vector(b).normalized(), f) if hasattr(Vector, "slerp") else Vector(a).lerp(Vector(b), f).normalized()
def ease(f): return f * f * (3 - 2 * f)

# the hovering pose: arms relaxed and a little forward, hands soft, legs hanging, toes down
HOVER = {"LeftArm": (0.42, -0.12, -0.9), "LeftForeArm": (0.3, -0.38, -0.87), "RightArm": (-0.42, -0.12, -0.9), "RightForeArm": (-0.3, -0.38, -0.87),
         "LeftUpLeg": (0.05, -0.12, -1.0), "LeftLeg": (0.02, 0.18, -1.0), "RightUpLeg": (-0.05, -0.08, -1.0), "RightLeg": (-0.02, 0.22, -1.0),
         "LeftFoot": (0.0, -0.45, -0.9), "RightFoot": (0.0, -0.45, -0.9)}

def blend(keys, f):
    """keys: [(time share, {bone: dir})...] -> the directions at f, eased between keys"""
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t0 <= f <= t1:
            g = ease((f - t0) / max(t1 - t0, 1e-6)); out = {}
            for n in set(a) | set(b):
                da = a.get(n, b.get(n)); db = b.get(n, a.get(n)); out[n] = lerp_dir(da, db, g)
            return out
    return dict(keys[-1][1])

def make(seconds, keys, beat, spread, period, extra=None, hips=None, fold=None):
    n = max(2, int(round(seconds * FPS))); frames = []
    for i in range(n):
        f = i / (n - 1); tsec = i / FPS
        dirs = blend(keys, f)
        tr = wings(2 * math.pi * tsec / period, beat, spread, fold(f) if fold else 0.0)
        if extra: tr.update(extra(f))
        frames.append(pose_frame(dirs, tr, hips(f) if hips else None))
    return frames

clips = {}
# Idle: 2 s, two slow beats
clips["Idle"] = make(2.0, [(0, HOVER), (1, HOVER)], 24, 14, 1.0)
# Fly: leaning into it, arms back, legs trailing; quicker beats
FLY = dict(HOVER); FLY.update({"LeftArm": (0.35, 0.35, -0.87), "RightArm": (-0.35, 0.35, -0.87), "LeftForeArm": (0.25, 0.25, -0.93), "RightForeArm": (-0.25, 0.25, -0.93),
                               "LeftUpLeg": (0.05, 0.3, -0.95), "RightUpLeg": (-0.05, 0.3, -0.95), "LeftLeg": (0.0, 0.45, -0.9), "RightLeg": (0.0, 0.45, -0.9)})
clips["Fly"] = make(1.2, [(0, FLY), (1, FLY)], 34, 20, 0.6, extra=lambda f: {"Hips": qaxis((1, 0, 0), 20)})
# Throw: the lance over the right shoulder, the left arm pointing the way; release at THROW_RELEASE
WIND = dict(HOVER); WIND.update({"RightArm": (-0.65, 0.62, 0.42), "RightForeArm": (-0.05, 0.3, 0.95), "LeftArm": (0.45, -0.88, 0.15), "LeftForeArm": (0.25, -0.96, 0.12)})
REL = dict(HOVER); REL.update({"RightArm": (-0.18, -0.86, 0.47), "RightForeArm": (-0.08, -0.92, 0.38), "LeftArm": (0.6, 0.35, -0.72), "LeftForeArm": (0.45, 0.2, -0.87)})
clips["Throw"] = make(1.4, [(0, HOVER), (0.36, WIND), (THROW_RELEASE, REL), (0.72, REL), (1, HOVER)], 20, 10, 1.0,
                      extra=lambda f: {"Spine1": qaxis((0, 0, 1), -22 * math.sin(math.pi * min(f / 0.36, 1.0) / 2) * (1 - ease(max(0, (f - 0.36) / 0.4))) + 18 * ease(max(0, min(1, (f - 0.36) / 0.18))) * (1 - ease(max(0, (f - 0.72) / 0.28))))})
# Cast: both arms up to the sky, the right brought down at the foe at CAST_RELEASE
UP = dict(HOVER); UP.update({"LeftArm": (0.28, -0.12, 0.95), "LeftForeArm": (0.15, -0.12, 0.98), "RightArm": (-0.28, -0.12, 0.95), "RightForeArm": (-0.15, -0.12, 0.98)})
DOWN = dict(UP); DOWN.update({"RightArm": (-0.2, -0.85, -0.45), "RightForeArm": (-0.14, -0.9, -0.4)})
clips["Cast"] = make(1.6, [(0, HOVER), (0.32, UP), (0.48, UP), (CAST_RELEASE, DOWN), (0.78, DOWN), (1, HOVER)], 26, 18, 0.8,
                     extra=lambda f: {"Head": qaxis((1, 0, 0), -18 * ease(min(1, f / 0.32)) * (1 - ease(max(0, (f - 0.48) / 0.11))))})
# Death: the wings swept back and still, falling backwards to lie on the floor
hips_z = B["Hips"].head_local.z
LIE = dict(HOVER); LIE.update({"LeftArm": (0.85, 0.1, -0.5), "RightArm": (-0.85, 0.1, -0.5), "LeftForeArm": (0.9, 0.2, -0.38), "RightForeArm": (-0.9, 0.2, -0.38)})
clips["Death"] = make(2.0, [(0, HOVER), (0.45, LIE), (1, LIE)], 0, 0, 1.0,
                      extra=lambda f: {"Hips": qaxis((1, 0, 0), -82 * ease(min(1, f / 0.7)))},
                      hips=lambda f: (0, 30 * ease(min(1, f / 0.7)), -(hips_z - 22) * ease(min(1, f / 0.7))),
                      fold=lambda f: 50 * ease(min(1, f / 0.4)))
# his own: the punches and the flinch, with the wings beating (their locations in the GLB's units: times S); his legs hang
# as when he hovers (the clips' boxing stance planted his feet on a floor he floats over)
LEGS = ("LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase", "RightUpLeg", "RightLeg", "RightFoot", "RightToeBase")
hang = pose_frame(HOVER)
for nm, fr in sampled.items():
    out = []
    for i, f in enumerate(fr):
        tr = wings(2 * math.pi * (i / FPS) / 0.9, 22, 12)
        d = {}
        for n in ORDER:
            if n in LEGS: d[n] = hang[n]
            elif n in f: loc, rot, scl = f[n]; d[n] = (loc * S, rot, scl)
            elif n in tr: d[n] = (Vector(), REST[n].inverted() @ tr[n] @ REST[n], Vector((1, 1, 1)))
        out.append(d)
    clips[nm] = out
print("clips", {k: len(v) for k, v in clips.items()})

# ---- the mesh FBX, then the clips FBX (as tripo_build.py)
bpy.ops.object.select_all(action='DESELECT')
for o in (arm, mesh): o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, NAME + ".fbx"), use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                         bake_anim=False, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', use_armature_deform_only=False,
                         mesh_smooth_type='FACE', use_tspace=True, path_mode='STRIP')
ad = arm.animation_data_create()
for name, frames in clips.items():
    new = bpy.data.actions.new("A_" + name); new.use_fake_user = True; ad.action = new
    if hasattr(ad, "action_slot") and hasattr(new, "slots"):
        try: ad.action_slot = new.slots.new('OBJECT', "Armature")
        except Exception: pass
    for i, fr in enumerate(frames):
        for pb in arm.pose.bones:
            if pb.name not in fr: continue
            loc, rot, scl = fr[pb.name]
            pb.location = loc; pb.rotation_quaternion = rot; pb.scale = scl
            pb.keyframe_insert("location", frame=i, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=i, group=pb.name)
            pb.keyframe_insert("scale", frame=i, group=pb.name)
ad.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()

# ---- when each punch lands: the frame its faster hand is fastest (the world places of the hands, frame to frame)
hit_times = {}
for name in ("Box_01", "Box_02", "Box_03"):
    if name not in clips: continue
    act = bpy.data.actions["A_" + name]; ad.action = act
    if hasattr(ad, "action_slot") and act.slots: ad.action_slot = act.slots[0]
    prev = None; best = (0.0, 0)
    for i in range(len(clips[name])):
        sc.frame_set(i)
        hands = [arm.matrix_world @ arm.pose.bones[h].head for h in ("LeftHand", "RightHand")]
        if prev:
            v = max((a - b).length for a, b in zip(hands, prev)) * FPS
            if v > best[0]: best = (v, i)
        prev = hands
    hit_times[name] = round(best[1] / FPS, 3)
ad.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
print("hit times", hit_times)

# ---- preview: key frames of each clip, front and side (the action played on the armature)
def preview(dirp):
    os.makedirs(dirp, exist_ok=True)
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'TEXTURE'
    sc.render.resolution_x = 640; sc.render.resolution_y = 640
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = BODY_CM * 1.75
    cam.data.clip_end = 5000.0          # (at its default of 1000 the wings behind him, 1000 cm and more off, were cut away)
    c = Vector((0, 0, BODY_CM * 0.55))
    shots = []
    for name in clips:
        act = bpy.data.actions["A_" + name]; ad.action = act
        if hasattr(ad, "action_slot") and act.slots: ad.action_slot = act.slots[0]
        n = len(clips[name])
        for share in (0.0, 0.36, 0.55, 0.8):
            fi = int(round(share * (n - 1))); sc.frame_set(fi)
            for view, dvec in (("front", Vector((0, -1, 0))), ("side", Vector((1, 0, 0)))):
                cam.location = c + dvec * 1000.0
                cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
                sc.render.filepath = os.path.join(dirp, f"{name}_{int(share * 100):02d}_{view}.png"); bpy.ops.render.render(write_still=True)
                shots.append(sc.render.filepath)
    ad.action = None
    return shots

bpy.ops.object.select_all(action='DESELECT')
for o in (arm, mesh): o.select_set(True)
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, NAME + "_Clips.fbx"), use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                         bake_anim=True, bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
                         bake_anim_simplify_factor=0.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE',
                         use_armature_deform_only=False, mesh_smooth_type='FACE', use_tspace=True, path_mode='STRIP')
tip_z = max(v.co.z for v in mesh.data.vertices)
json.dump({"clips": {k: len(v) for k, v in clips.items()}, "fps": FPS, "textures": tex, "height_cm": BODY_CM, "wing_tip_cm": round(tip_z, 1),
           "throw_release": THROW_RELEASE, "cast_release": CAST_RELEASE, "hit_times": hit_times, "wings": report, "scale": S},
          open(os.path.join(OUT, "build.json"), "w"), indent=1)
if PREVIEW: print("preview", len(preview(PREVIEW)))
print("EXPORT DONE", json.dumps({"wing_tip_cm": round(tip_z, 1), "wings": report["wing_vertices"]}))
