"""MartialArtist3.glb (a Tripo model with a rig and no clips) given MartialArtist2.glb's clips (the user's of 2026-11-10):
her own (Walk, Run, Box_01-03, Front_kick_01-02) and the ones martialartist_clips.py makes for her (Idle, the stabs, the
rolls, Dash, the ten chi attacks), as tripo_build.py would export them.
The rigs differ: MartialArtist2 has 61 bones and rests in a T pose with her legs apart; MartialArtist3 has 80 (five
spine bones, two neck bones, two twist bones a limb, metacarpals) and rests with her arms down and her legs straight; her
legs are shorter and her arms longer for her height. So a clip does not go over by local turns:
- each clip is played on MartialArtist2 and every bone's turn from its rest read in world space;
- each bone of MartialArtist3 takes its namesake's turn, after a turn that puts it in MartialArtist2's rest pose (the
  limbs and fingers by the way each bone points to its child, the hands by their knuckles' line as well);
- the spine's and neck's extra bones take a turn half way between their neighbours', the twist bones one between the
  limb's and its twist bone's; the metacarpals follow the hand;
- the pelvis moves as MartialArtist2's does, by the legs' lengths (hip to ankle); each ankle is then put where
  MartialArtist2's is from her pelvis, by the same scale (two bones solved, the knee kept the way it bent), the foot
  keeping its turn: her feet stand where the clip's do.
Writes <out_dir>/MartialArtist3_Animated.glb (every clip an animation of its name) and <out_dir>/ma3_clips.json (each
clip's length, its blow's time from ma_times.json, the walk's and the run's speed measured from the planted foot, the
feet's lowest place in each clip against the rest pose's).
Blender: -b -P martialartist3_retarget.py -- MartialArtist2.glb out_dir MartialArtist3.glb [preview_prefix [clip:frame,...]]
  [--maker m1,m2] [--tag T] [--carry a,b] [--own] [--noskin] [--name N] [--env K=V] (another hero's body: the Rogue's attacks
  from Rogue.glb onto Rogue2.glb, the Summoner's casts from Summoner4.glb onto Summoner5, each beside her own clips)
A target with summoner5_cloak.py's cloak bones: in the carried clips the cloak hangs from her upper back, turned back toward
hanging by one turn for the whole cloak (a share of it down each chain) and kept over the floor (cloak_turn(), hang())."""
import bpy, sys, os, json, math, re
from mathutils import Matrix, Vector, Quaternion
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
argv = sys.argv[sys.argv.index("--") + 1:]
# (another hero's body the same way, the user's list of 2026-11-11 (Rogue2, Summoner5): options after the positional args,
# their defaults the Martial Artist's run as it was:
#   --maker m1,m2   the source's clip makers, in turn (martialartist_clips); --tag T  tripo_proportions' tag (MartialArtist)
#   --carry a,b     only these of the source's clips are carried (all)
#   --own           the target GLB's own clips kept as they are, beside the carried ones (she has none: MartialArtist3)
#   --noskin        MartialArtist3's skin fixes left out (her thighs' and hips' weights; another body has its own)
#   --name N        the output's name: <out_dir>/<N>_Animated.glb, <N>_clips.json (MartialArtist3, ma3_clips.json)
#   --env K=V       set before the makers run (weapon5_clips' W5_CLIPS / W5_HERO)
#   --inplace a,b   these of her own clips walked in place: the pelvis's steady way over the clip taken out, flat on the
#                   floor, and the rest centred (Rogue2's and Summoner5's walk and run carry her forward; the game's
#                   locomotion plays clips in place and 610 reads their speed from the planted foot: 4.3 cm/s for her walk))
OPT = {"maker": "martialartist_clips", "tag": "MartialArtist", "carry": "", "own": False, "skin": True, "name": "MartialArtist3", "inplace": ""}
_pos = []; _i = 0
while _i < len(argv):
    a_ = argv[_i]
    if a_ in ("--maker", "--tag", "--carry", "--name", "--inplace"): OPT[a_[2:]] = argv[_i + 1]; _i += 2; continue
    if a_ == "--env": k_, v_ = argv[_i + 1].split("=", 1); os.environ[k_] = v_; _i += 2; continue
    if a_ == "--own": OPT["own"] = True; _i += 1; continue
    if a_ == "--noskin": OPT["skin"] = False; _i += 1; continue
    _pos.append(a_); _i += 1
argv = _pos
SRC, OUT, TGT = argv[0], argv[1], argv[2]
# (the makers find their output folder as argv[1] (times.json and the rest go there): the positional args alone)
sys.argv = sys.argv[:sys.argv.index("--") + 1] + _pos
PREVIEW = argv[3] if len(argv) > 3 else None
SHOTS = [(s.split(":")[0], int(s.split(":")[1])) for s in argv[4].split(",")] if len(argv) > 4 else []
os.makedirs(OUT, exist_ok=True)
FPS = 24
VIEWS = [(v.split(":")[0], float(v.split(":")[1])) for v in os.environ.get("MA3_VIEWS", "front:0,side:90,q:35").split(",")]   # (name:degrees round her)
SKIN = os.environ.get("MA3_SKIN", "1") != "0" and OPT["skin"]  # (0 / --noskin: Tripo's weights as they came)
ZOOM = int(os.environ.get("MA3_ZOOM", "1"))
TRACE = os.environ.get("MA3_TRACE", "").split(",")
FINGERS = ("thumb", "index", "middle", "ring", "pinky")


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    sc = bpy.context.scene; sc.render.fps = FPS
    arm = next(o for o in sc.objects if o.type == 'ARMATURE')
    meshes = [o for o in sc.objects if o.type == 'MESH' and o.vertex_groups]
    for o in [o for o in sc.objects if o.type == 'MESH' and o not in meshes]: bpy.data.objects.remove(o, do_unlink=True)
    for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
    return sc, arm, meshes


def pictures(sc, prefix, set_pose):
    """SHOTS (clip, frame) from the front, the side and three-quarter"""
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'TEXTURE'; sc.display.shading.light = 'STUDIO'
    sc.render.resolution_x = 300 * ZOOM; sc.render.resolution_y = 380 * ZOOM                     # (MA3_ZOOM: bigger pictures)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.7; cam.data.clip_end = 100
    bpy.ops.mesh.primitive_plane_add(size=1.8, location=(0, 0, -0.004)); fl = bpy.context.active_object
    mt = bpy.data.materials.new("floor"); mt.diffuse_color = (0.25, 0.35, 0.25, 1); fl.data.materials.append(mt)
    for name, i in SHOTS:
        set_pose(name, i)
        for view, ang in VIEWS:
            a = math.radians(ang); d = Vector((math.sin(a), -math.cos(a), 0.15))
            cam.location = Vector((0, 0, 0.5)) + d * 4.0; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = f"{prefix}_{name}_{i}_{view}.png"; bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(fl, do_unlink=True); bpy.data.objects.remove(cam, do_unlink=True)


# ---------------------------------------------------------------- MartialArtist2: her clips, as tripo_build makes them
sc, arm, meshes = load(SRC)
ad = arm.animation_data or arm.animation_data_create()
for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
clips = {}
for act in list(bpy.data.actions):
    name = act.name.split(".")[0]; name = name[:1].upper() + name[1:]
    name = re.sub(r"[^A-Za-z0-9_]+", "_", name).strip("_")
    ad.action = act
    if hasattr(ad, "action_slot") and act.slots: ad.action_slot = act.slots[0]
    f0, f1 = [int(round(v)) for v in act.frame_range]
    frames = []
    for t in range(f0, f1 + 1):
        sc.frame_set(t); frames.append({pb.name: pb.matrix_basis.decompose() for pb in arm.pose.bones})
    clips[name] = frames
ad.action = None
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
import tripo_proportions, importlib
tripo_proportions.apply(arm, meshes, OPT["tag"])
for mk in [m.strip() for m in OPT["maker"].split(",") if m.strip()]:
    MK = importlib.import_module(mk)
    for name, frames in MK.make_clips(arm, sc, clips).items(): clips[name] = frames
    for pb in arm.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
if OPT["carry"]:
    want = [c.strip() for c in OPT["carry"].split(",") if c.strip()]
    lost = [c for c in want if c not in clips]
    assert not lost, ("the source has no", lost, sorted(clips))
    clips = {c: clips[c] for c in want}
print("MA3 source clips:", {k: len(v) for k, v in clips.items()})

AW = arm.matrix_world.copy()
S_REST = {b.name: AW @ b.matrix_local for b in arm.data.bones}
S_POS = {n: m.translation.copy() for n, m in S_REST.items()}
S_WORLD = {}
for name, frames in clips.items():
    out = []
    for fr in frames:
        for pb in arm.pose.bones:
            if pb.name in fr:
                loc, rot, scl = fr[pb.name]; pb.matrix_basis = Matrix.LocRotScale(loc, rot, scl)
        bpy.context.view_layer.update()
        out.append({pb.name: (AW @ pb.matrix) for pb in arm.pose.bones})
    S_WORLD[name] = out
S_Q0 = {n: m.to_quaternion() for n, m in S_REST.items()}
if PREVIEW:                                                     # (MartialArtist2 in the same frames, to tell her clip's faults from the retarget's)
    def src_pose(name, i):
        fr = clips[name][min(i, len(clips[name]) - 1)]
        for pb in arm.pose.bones:
            if pb.name in fr: pb.matrix_basis = Matrix.LocRotScale(*fr[pb.name])
        bpy.context.view_layer.update()
    pictures(sc, PREVIEW + "_src", src_pose)

# ---------------------------------------------------------------- MartialArtist3
sc, arm, meshes = load(TGT)
# (--own: the target's own clips, each frame's bones as the clip has them, named as tripo_build names them; then her
# importer's tracks and actions go, or they would be written out a second time)
OWN = {}
tad = arm.animation_data
if tad:
    for t in list(tad.nla_tracks): tad.nla_tracks.remove(t)
    if OPT["own"]:
        for act in list(bpy.data.actions):
            name = act.name.split(".")[0]; name = name[:1].upper() + name[1:]
            name = re.sub(r"[^A-Za-z0-9_]+", "_", name).strip("_")
            # (two actions cut to one name ('idle' and 'idle.001'): one would replace the other unseen)
            assert name not in OWN, ("--own: two of her clips are both named", name, [a.name for a in bpy.data.actions])
            tad.action = act
            if hasattr(tad, "action_slot") and act.slots: tad.action_slot = act.slots[0]
            f0, f1 = [int(round(v)) for v in act.frame_range]; fr_ = []
            for t in range(f0, f1 + 1):
                sc.frame_set(t); fr_.append({pb.name: (pb.matrix_basis.to_translation(), pb.matrix_basis.to_quaternion()) for pb in arm.pose.bones})
            OWN[name] = fr_
    tad.action = None
    for a in list(bpy.data.actions): bpy.data.actions.remove(a)
if OWN: print("MA3 her own clips kept:", {k: len(v) for k, v in OWN.items()})
for nm in [c.strip() for c in OPT["inplace"].split(",") if c.strip()]:
    assert nm in OWN, ("--inplace: no clip of hers named", nm, sorted(OWN))
    fr_ = OWN[nm]; pbn = arm.data.bones["pelvis"]
    # (the pelvis's place is in its bone's rest frame: its way over the clip in the world, flat, and back into that frame)
    M = (arm.matrix_world.to_3x3() @ pbn.matrix_local.to_3x3()); Mi = M.inverted()
    world = [M @ f["pelvis"][0] for f in fr_]
    drift = world[-1] - world[0]; drift.z = 0.0; n_ = len(fr_) - 1
    flat = [w - drift * (i / n_) for i, w in enumerate(world)]
    mean = sum(flat, Vector()) / len(flat); mean.z = 0.0
    for i, f in enumerate(fr_):
        loc, rot = f["pelvis"]; f["pelvis"] = (Mi @ (flat[i] - mean), rot)
    print("MA3 %s walked in place: the pelvis's way over the clip %.3f (%.3f a second), its middle %.3f off her rest, taken out" % (
        nm, drift.length, drift.length * FPS / max(1, n_), mean.length))
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
AW = arm.matrix_world.copy(); AWI = AW.inverted(); AWQ = AW.to_quaternion()
B = arm.data.bones
T_REST = {b.name: AW @ b.matrix_local for b in B}
T_POS = {n: m.translation.copy() for n, m in T_REST.items()}
T_Q0 = {n: m.to_quaternion() for n, m in T_REST.items()}


def way(pos, a, b): return (pos[b] - pos[a]).normalized()


def reweight(me, upper, lower, end, share=0.15):
    """Tripo's skin: vertices well below a joint weighted to the limb above it (116 of the shins' 976 mostly to
    thigh_twist_02: with the knee bent they stayed in the thigh's line, a fin behind the knee; the user's picture of
    2026-11-10). The upper limb's weight fades out over `share` of the lower limb's length past the joint and goes to
    the lower limb's bone. -> the vertices changed"""
    J = T_POS[lower]; ax = T_POS[end] - J; D = ax.length * share; ax.normalize()
    ups = {me.vertex_groups[n].index: me.vertex_groups[n] for n in upper if n in me.vertex_groups}; low = me.vertex_groups[lower]
    n = 0
    for v in me.data.vertices:
        mine = [(g.group, g.weight) for g in v.groups if g.group in ups and g.weight > 0.0]
        if not mine: continue
        t = ((me.matrix_world @ v.co) - J).dot(ax) / D
        if t <= 0.0: continue
        t = min(t, 1.0); keep = 1.0 - t * t * (3.0 - 2.0 * t); moved = 0.0
        for gi, w in mine:
            ups[gi].add([v.index], w * keep, 'REPLACE'); moved += w * (1.0 - keep)
        low.add([v.index], moved, 'ADD'); n += 1
    return n


def reweight_hip(me, s, rise=0.035):
    """vertices above the hip joint weighted to the thigh's bones (her belt and waist: a raised thigh dragged them); the
    weight fades out over `rise` of her height above the joint and goes to the pelvis. -> the vertices changed"""
    z0 = T_POS[f"thigh_{s}"].z; pel = me.vertex_groups["pelvis"]
    ups = {me.vertex_groups[n].index: me.vertex_groups[n] for n in (f"thigh_{s}", f"thigh_twist_01_{s}", f"thigh_twist_02_{s}")}
    n = 0
    for v in me.data.vertices:
        mine = [(g.group, g.weight) for g in v.groups if g.group in ups and g.weight > 0.0]
        if not mine: continue
        t = ((me.matrix_world @ v.co).z - z0) / rise
        if t <= 0.0: continue
        t = min(t, 1.0); keep = 1.0 - t * t * (3.0 - 2.0 * t); moved = 0.0
        for gi, w in mine:
            ups[gi].add([v.index], w * keep, 'REPLACE'); moved += w * (1.0 - keep)
        pel.add([v.index], moved, 'ADD'); n += 1
    return n


def reweight_thigh_top(me, drop=0.035, mid=(0.006, 0.03)):
    """the top of her thighs (the skin under the shorts' hem, the hem, the shorts' legs) weighted to the pelvis, the spine
    or the other leg: a raised thigh left it hanging under her, a flap by the hem (the user's picture of the Roundhouse
    Kick, 2026-11-10). That weight fades out over `drop` of her height below the hip joint and goes to the vertex's own
    thigh; between her legs (within `mid` of her middle) it stays, so the crotch does not follow one leg.
    (Told by colour instead, skin from shorts, the hem tore: neighbours went to different bones.) -> the vertices changed"""
    name = {g.index: g.name for g in me.vertex_groups}; n = 0
    low = max(T_POS[f"calf_{s}"].z for s in "lr"); reach = 2.5 * max(abs(T_POS[f"thigh_{s}"].x) for s in "lr")   # (her thighs, not her hands)
    step = lambda t: (lambda t: t * t * (3.0 - 2.0 * t))(max(0.0, min(1.0, t)))
    for v in me.data.vertices:
        w = me.matrix_world @ v.co
        if w.z < low or abs(w.x) > reach: continue
        s = "l" if (w.x > 0) == (T_POS["thigh_l"].x > 0) else "r"; o = "r" if s == "l" else "l"
        f = step((T_POS[f"thigh_{s}"].z - w.z) / drop) * step((abs(w.x) - mid[0]) / (mid[1] - mid[0]))
        if f <= 0.0: continue
        off = [(g.group, g.weight) for g in v.groups if g.weight > 0.0 and (name[g.group].startswith(("pelvis", "spine")) or name[g.group].endswith("_" + o))]
        if not off: continue
        for gi, wt in off: me.vertex_groups[gi].add([v.index], wt * (1.0 - f), 'REPLACE')
        me.vertex_groups[f"thigh_{s}"].add([v.index], sum(wt for gi, wt in off) * f, 'ADD'); n += 1
    return n


if SKIN: print("MA3 skin: %d vertices at the top of her thighs taken off the pelvis, the spine and the other leg" % reweight_thigh_top(meshes[0]))
for s in ("lr" if SKIN else ""):
    print("MA3 skin %s: %d vertices above the hip taken off the thigh's bones" % (s, reweight_hip(meshes[0], s)))
    print("MA3 skin %s: %d shin vertices taken off the thigh's bones, %d forearm vertices off the upper arm's" % (s,
          reweight(meshes[0], [f"thigh_{s}", f"thigh_twist_01_{s}", f"thigh_twist_02_{s}"], f"calf_{s}", f"foot_{s}"),
          reweight(meshes[0], [f"upperarm_{s}", f"upperarm_twist_01_{s}", f"upperarm_twist_02_{s}"], f"lowerarm_{s}", f"hand_{s}")))


def hand_frame(pos, s):
    x = way(pos, f"hand_{s}", f"middle_01_{s}"); y = way(pos, f"index_01_{s}", f"pinky_01_{s}")
    y = (y - x * y.dot(x)).normalized()
    return Matrix((x, y, x.cross(y))).transposed()


# the turn that puts each bone of hers in MartialArtist2's rest pose (world)
FIX = {}
for s in "lr":
    for a, b in (("clavicle", "upperarm"), ("upperarm", "lowerarm"), ("lowerarm", "hand"), ("thigh", "calf"), ("calf", "foot"), ("foot", "ball")):
        FIX[f"{a}_{s}"] = way(T_POS, f"{a}_{s}", f"{b}_{s}").rotation_difference(way(S_POS, f"{a}_{s}", f"{b}_{s}"))
    FIX[f"ball_{s}"] = FIX[f"foot_{s}"]
    FIX[f"hand_{s}"] = (hand_frame(S_POS, s) @ hand_frame(T_POS, s).inverted()).to_quaternion()
    for f in FINGERS:
        for k in ("01", "02"):
            FIX[f"{f}_{k}_{s}"] = way(T_POS, f"{f}_{k}_{s}", f"{f}_0{int(k) + 1}_{s}").rotation_difference(way(S_POS, f"{f}_{k}_{s}", f"{f}_0{int(k) + 1}_{s}"))
        FIX[f"{f}_03_{s}"] = FIX[f"{f}_02_{s}"]
ID = Quaternion()
# her bone: (MartialArtist2's bone a, bone b, the share of b's turn, the bone whose rest turn it takes)
PLAN = {"pelvis": ("pelvis", None, 0, None), "spine_01": ("spine_01", None, 0, None), "spine_02": ("spine_01", "spine_02", 0.5, None),
        "spine_03": ("spine_02", None, 0, None), "spine_04": ("spine_02", "spine_03", 0.5, None), "spine_05": ("spine_03", None, 0, None),
        "neck_01": ("neck_01", None, 0, None), "neck_02": ("neck_01", "head", 0.5, None), "head": ("head", None, 0, None)}
for s in "lr":
    for n in ("clavicle", "upperarm", "lowerarm", "hand", "thigh", "calf", "foot", "ball"): PLAN[f"{n}_{s}"] = (f"{n}_{s}", None, 0, f"{n}_{s}")
    for f in FINGERS:
        for k in ("01", "02", "03"): PLAN[f"{f}_{k}_{s}"] = (f"{f}_{k}_{s}", None, 0, f"{f}_{k}_{s}")
    PLAN[f"upperarm_twist_01_{s}"] = (f"upperarm_twist_01_{s}", f"upperarm_{s}", 1 / 3, f"upperarm_{s}")
    PLAN[f"upperarm_twist_02_{s}"] = (f"upperarm_twist_01_{s}", f"upperarm_{s}", 2 / 3, f"upperarm_{s}")
    PLAN[f"lowerarm_twist_02_{s}"] = (f"lowerarm_{s}", f"lowerarm_twist_01_{s}", 2 / 3, f"lowerarm_{s}")
    PLAN[f"lowerarm_twist_01_{s}"] = (f"lowerarm_twist_01_{s}", None, 0, f"lowerarm_{s}")
    PLAN[f"thigh_twist_01_{s}"] = (f"thigh_twist_01_{s}", None, 0, f"thigh_{s}")
    PLAN[f"thigh_twist_02_{s}"] = (f"thigh_twist_01_{s}", f"thigh_{s}", 1 / 3, f"thigh_{s}")
    PLAN[f"calf_twist_02_{s}"] = (f"calf_{s}", f"calf_twist_01_{s}", 2 / 3, f"calf_{s}")
    PLAN[f"calf_twist_01_{s}"] = (f"calf_twist_01_{s}", None, 0, f"calf_{s}")
missing = [n for n in PLAN if n not in B] + [a for a, b, f, c in PLAN.values() if a not in S_REST]
assert not missing, missing
print("MA3 bones: %d planned, %d following their parents: %s" % (len(PLAN), len(B) - len(PLAN), sorted(b.name for b in B if b.name not in PLAN)))


def leg_len(pos, s): return (pos[f"calf_{s}"] - pos[f"thigh_{s}"]).length + (pos[f"foot_{s}"] - pos[f"calf_{s}"]).length


# her cloak's chains in the carried clips (summoner5_cloak.py's bones, cloak_<chain>_<bone>: the Summoner's and the Rogue's;
# their own clips were keyed there): left at rest under her upper back they stood stiff out of it, and in the Rogue's
# rolls, curled low, the cloak went 70 cm through the floor (the preview's RollF). The cloak as she carries it (each bone
# its rest way turned as her upper back turns) is turned back toward hanging by one turn for the whole cloak, the one that
# takes her upper back's "down" to the world's, a share of it down each chain (none at the top, where it hangs from her
# back). Each bone pulled toward its own way down tore the hem upside down in the roll (neighbouring chains' pulls, near
# opposite to their ways, went off in different ways: a hem edge 7 times its length); one turn keeps the sheet whole.
# None goes under the floor: a bone whose end would is laid along it, still pointing the way it went
CLOAK_BONES = {b.name: int(b.name.split("_")[2]) for b in B if re.fullmatch(r"cloak_\d+_\d+", b.name)}
CLOAK_SHARE = (0.0, 0.35, 0.6, 0.8)                             # (the turn's share at each bone down a chain)
CLOAK_FLOOR = min(T_POS[f"ball_{s}"].z for s in "lr") + 0.015
CLOAK_REST = {n: (B[n].matrix_local.to_3x3() @ Vector((0.0, 1.0, 0.0))).normalized() for n in CLOAK_BONES}
DOWN_A = (AWI.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized(); LEFT_A = (AWI.to_3x3() @ Vector((1.0, 0.0, 0.0))).normalized()
SP_REST_Q = B["spine_05"].matrix_local.to_quaternion() if CLOAK_BONES else None
BACK_A = (AWI.to_3x3() @ Vector((0.0, 1.0, 0.0))).normalized()                    # (she faces -Y)
MID_HEM = "cloak_%d_%d" % (max(int(n.split("_")[1]) for n in CLOAK_BONES) // 2, max(CLOAK_BONES.values())) if CLOAK_BONES else None
if CLOAK_BONES: print("MA3 her cloak: %d bones hang and keep over the floor in the carried clips" % len(CLOAK_BONES))


def cloak_turn(A):
    """her upper back's turn from rest, and the turn that takes its carried "down" to the world's (about her left when
    she is near upside down: a roll turns her about it)"""
    Qs = A["spine_05"].to_quaternion() @ SP_REST_Q.inverted()
    carried = Qs @ DOWN_A; ang = carried.angle(DOWN_A)
    ax = carried.cross(DOWN_A)
    if ax.length < 0.2 * math.sin(max(ang, 1e-3)) or ang > math.radians(150):
        ax = Qs @ LEFT_A; ax = ax - DOWN_A * ax.dot(DOWN_A)
        if carried.cross(DOWN_A).dot(ax) < 0: ax = -ax
    R = Quaternion(ax.normalized(), ang) if ax.length > 1e-6 else Quaternion()
    # (the way the cloak lies on the floor: its middle chain's hem, flat; else behind her back; else behind her rest)
    flat = None
    for d in (Quaternion().slerp(R, CLOAK_SHARE[-1]) @ (Qs @ CLOAK_REST[MID_HEM]), Qs @ BACK_A, BACK_A):
        w = AW.to_3x3() @ d; w = Vector((w.x, w.y, 0.0))
        if w.length > 0.2: flat = w.normalized(); break
    return Qs, R, flat


def hang(A, b, turn):
    Qs, R, com = turn
    m = A[b.name]; head = m.translation.copy(); L = b.length
    cur = (m.to_3x3() @ Vector((0.0, 1.0, 0.0))).normalized()
    k = CLOAK_BONES[b.name]; f = CLOAK_SHARE[min(k, len(CLOAK_SHARE) - 1)]
    new = (Quaternion().slerp(R, f) @ (Qs @ CLOAK_REST[b.name])).normalized()
    hw = AW @ head; tw = hw + (AW.to_3x3() @ new) * L
    if tw.z < CLOAK_FLOOR:
        # (laid the way the cloak's middle trails at the hem, every chain alike: each laid its own way out fanned the hem
        # out on the floor, 4.9 times its edges' length in the roll; near the top its own way, flat: laid the common way
        # there, a chain's first bone that met the floor turned back while its neighbour, a little over it, went on
        # forward (3.8 times))
        dw = AW.to_3x3() @ new; own = Vector((dw.x, dw.y, 0.0))
        wk = CLOAK_BONES[b.name] / max(1, max(CLOAK_BONES.values()))
        flat = own.normalized() * (1.0 - wk) + com * wk if own.length > 1e-4 else com
        if flat.length < 1e-4: flat = com
        dz = max(-1.0, min(1.0, (CLOAK_FLOOR - hw.z) / L))
        new = (AWI.to_3x3() @ (flat.normalized() * math.sqrt(1.0 - dz * dz) + Vector((0.0, 0.0, dz)))).normalized()
    if (new - cur).length < 1e-6: return
    q = cur.rotation_difference(new) @ m.to_quaternion()
    A[b.name] = Matrix.LocRotScale(head, q, None)


K = sum(leg_len(T_POS, s) for s in "lr") / sum(leg_len(S_POS, s) for s in "lr")
print("MA3 legs: hers %.3f, MartialArtist2's %.3f of the height: the pelvis and the ankles move by %.3f" % (leg_len(T_POS, "l"), leg_len(S_POS, "l"), K))
ORDER = list(B)                                                 # (parents first)
REST_LOCAL = {b.name: (b.parent.matrix_local.inverted() @ b.matrix_local if b.parent else b.matrix_local.copy()) for b in B}
ANKLE_Z = {s: T_POS[f"foot_{s}"].z - T_POS["pelvis"].z - (S_POS[f"foot_{s}"].z - S_POS["pelvis"].z) * K for s in "lr"}


def retarget(sw):
    """one frame: MartialArtist2's bones' world matrices -> her bones' world turns and her pelvis's place"""
    D = {n: sw[n].to_quaternion() @ S_Q0[n].inverted() for n in S_Q0}
    Q = {}
    for n, (a, b, f, fix) in PLAN.items():
        d = D[a] if b is None else D[a].slerp(D[b], f)
        Q[n] = d @ (FIX[fix] if fix else ID) @ T_Q0[n]
    pel = T_POS["pelvis"] + (sw["pelvis"].translation - S_POS["pelvis"]) * K
    ankles = {s: pel + (sw[f"foot_{s}"].translation - sw["pelvis"].translation) * K + Vector((0, 0, ANKLE_Z[s])) for s in "lr"}
    return Q, pel, ankles


LEFT = Vector((1.0, 0.0, 0.0))                                  # (her left, in the world: a knee bending turns the shin about it)
assert T_POS["thigh_l"].x > 0 > T_POS["thigh_r"].x and T_POS["ball_l"].y < T_POS["foot_l"].y, "she is expected to face -Y, her left +X"


def side_frame(d, h):
    """a frame with its first axis along d and its second as near h as it can be"""
    h = h - d * h.dot(d); h.normalize()
    return Matrix((d, h, d.cross(h))).transposed()


def solve(Q, pel, ankles):
    """her bones' matrices in armature space, the legs solved to the ankles; -> {bone: (basis loc, basis rot)}, world places"""
    A = {}; W = {}
    def place(b):
        base = (A[b.parent.name] @ REST_LOCAL[b.name]) if b.parent else REST_LOCAL[b.name]
        if b.name in Q:
            loc = base.translation if b.name != "pelvis" else AWI @ pel
            A[b.name] = Matrix.LocRotScale(loc, AWQ.inverted() @ Q[b.name], None)
        else: A[b.name] = base
        W[b.name] = AW @ A[b.name].translation
    for b in ORDER: place(b)
    short = 0.0; ANKLES = {}
    for s in "lr":
        H, K0, A0 = W[f"thigh_{s}"], W[f"calf_{s}"], W[f"foot_{s}"]; T = ankles[s]
        a, c = (T_POS[f"calf_{s}"] - T_POS[f"thigh_{s}"]).length, (T_POS[f"foot_{s}"] - T_POS[f"calf_{s}"]).length
        d = T - H; short = max(short, d.length - (a + c)); dist = min(d.length, (a + c) * 0.999); dn = d.normalized()
        pole = (K0 - H) - dn * (K0 - H).dot(dn)                 # (the knee the way it bent)
        if pole.length < 1e-5: pole = Q[f"thigh_{s}"] @ (T_Q0[f"thigh_{s}"].inverted() @ Vector((0, -1, 0)))
        pole = (pole - dn * pole.dot(dn)).normalized()
        ca = max(-1.0, min(1.0, (a * a + dist * dist - c * c) / (2 * a * dist))); sa = math.sqrt(1.0 - ca * ca)
        Kn = H + (dn * ca + pole * sa) * a; An = H + dn * dist; ANKLES[s] = An
        # the thigh keeps MartialArtist2's turn (moved the least way onto its new line: a hip turns any way and her clips'
        # thighs are right to look at); the shin is the thigh's turn bent at the knee and nothing more, a hinge.
        # MartialArtist2's own shin is not copied: martialartist_clips' kicks leave it rolled any way round about its
        # length (in the Spinning Kick's chamber its front faced backward: unseen on her boots; on MartialArtist3 the
        # knee was twisted, and the foot held to its ankle's limits against that shin pointed backward: the user's
        # picture of 2026-11-10). (Both bones built from the hip's, knee's and ankle's places alone turned the
        # thigh over in her rolls: the places do not say which way a hip is turned.)
        td, sd = (Kn - H).normalized(), (An - Kn).normalized()
        Q[f"thigh_{s}"] = (K0 - H).normalized().rotation_difference(td) @ Q[f"thigh_{s}"]
        dth = Q[f"thigh_{s}"] @ T_Q0[f"thigh_{s}"].inverted()
        dca = (dth @ way(T_POS, f"calf_{s}", f"foot_{s}")).rotation_difference(sd) @ dth
        for bn, dq in ((f"thigh_twist_01_{s}", dth), (f"thigh_twist_02_{s}", dth), (f"calf_{s}", dca), (f"calf_twist_01_{s}", dca), (f"calf_twist_02_{s}", dca)):
            Q[bn] = dq @ T_Q0[bn]
    # her ankle: MartialArtist2's kicks point her foot straight along her shin (90 degrees and more; she wears heeled
    # boots) and turn it about the shin (85 degrees in two of her boxing clips), which folds a flat shoe off its ankle and
    # turns it at an angle no ankle has (the user's pictures of the Spinning Kick, 2026-11-10). The foot's turn from its
    # rest against the shin is split into its turn about the shin and its bend:
    # - a turn past ANKLE_TURN goes into the leg (the thigh and calf turned about the line from hip to ankle: the knee
    #   comes round to where the toes point, the ankle and the foot stay where they are);
    # - a bend past ANKLE_BEND is held there.
    bend = 0.0
    for s in "lr":
        a0 = way(T_POS, f"calf_{s}", f"foot_{s}"); H = W[f"thigh_{s}"]; n = (ANKLES[s] - H).normalized()
        legb = [f"thigh_{s}", f"calf_{s}", f"thigh_twist_01_{s}", f"thigh_twist_02_{s}", f"calf_twist_01_{s}", f"calf_twist_02_{s}"]
        # - first its roll about its own length (the sole turned to one side): martialartist_clips' kicks aim the foot's
        #   length only and leave the sole wherever the leg's turns brought it (86 degrees off in the Spinning Kick's
        #   chamber: on her the toes pointed back, the user's second picture). Past FOOT_ROLL it is held.
        f0 = way(T_POS, f"foot_{s}", f"ball_{s}"); dc = Q[f"calf_{s}"] @ T_Q0[f"calf_{s}"].inverted()
        r = dc.inverted() @ (Q[f"foot_{s}"] @ T_Q0[f"foot_{s}"].inverted())
        if r.w < 0: r.negate()
        v = Vector((r.x, r.y, r.z)); pr = f0 * v.dot(f0); t = Quaternion((r.w, pr.x, pr.y, pr.z))
        if t.magnitude < 1e-9: t = Quaternion()
        t.normalize(); roll0 = math.degrees(2.0 * math.atan2(Vector((t.x, t.y, t.z)).dot(f0), t.w)); roll0 = (roll0 + 180.0) % 360.0 - 180.0
        if abs(roll0) > FOOT_ROLL:                                       # (past FOOT_WILD it says nothing: the sole level with the shin)
            keep = 0.0 if abs(roll0) > FOOT_WILD else (FOOT_ROLL if roll0 > 0 else -FOOT_ROLL)
            new = dc @ (r @ t.inverted()) @ Quaternion(f0, math.radians(keep)) @ T_Q0[f"foot_{s}"]
            fix = new @ Q[f"foot_{s}"].inverted(); Q[f"foot_{s}"] = new; Q[f"ball_{s}"] = fix @ Q[f"ball_{s}"]
        df = Q[f"foot_{s}"] @ T_Q0[f"foot_{s}"].inverted()
        def split():
            r = (Q[f"calf_{s}"] @ T_Q0[f"calf_{s}"].inverted()).inverted() @ df
            if r.w < 0: r.negate()
            v = Vector((r.x, r.y, r.z)); pr = a0 * v.dot(a0); t = Quaternion((r.w, pr.x, pr.y, pr.z))
            if t.magnitude < 1e-9: t = Quaternion()
            t.normalize(); return r, t, r @ t.inverted()
        def turn():
            r, t, sw = split(); tw = math.degrees(2.0 * math.atan2(Vector((t.x, t.y, t.z)).dot(a0), t.w))
            return (tw + 180.0) % 360.0 - 180.0, r, sw
        tw, r, sw = turn(); bend = max(bend, math.degrees(r.angle)); tw0 = tw; sw0 = math.degrees(sw.angle); rolled = 0.0
        for it in range(8):
            over = tw - max(-ANKLE_TURN, min(ANKLE_TURN, tw))
            if abs(over) < 0.5: break
            step = max(-LEG_ROLL - rolled, min(LEG_ROLL - rolled, over))        # (the leg rolls LEG_ROLL at most, either way)
            if abs(step) < 0.5: break
            keep = {bn: Q[bn].copy() for bn in legb}
            for bn in legb: Q[bn] = Quaternion(n, math.radians(step)) @ Q[bn]
            tw2, r2, sw2 = turn()
            if abs(tw2) >= abs(tw) - 0.1:                                       # (it did not help: with the knee bent the roll swings the shin instead)
                for bn in legb: Q[bn] = keep[bn]
                break
            tw = tw2; rolled += step
        r, t, sw = split()
        if TRACE_ANKLE: print("MA3 ankle %s: sole roll %6.1f, turn %6.1f -> %6.1f, bend %5.1f -> %5.1f, leg rolled %5.1f" % (s, roll0, tw0, tw, sw0, math.degrees(sw.angle), rolled))
        solve.roll = max(getattr(solve, "roll", 0.0), abs(roll0))
        if math.degrees(sw.angle) > ANKLE_BEND or abs(math.degrees(t.angle)) > ANKLE_TURN + 1.0:
            if math.degrees(sw.angle) > ANKLE_BEND: sw = Quaternion(sw.axis, math.radians(ANKLE_BEND))
            if math.degrees(t.angle) > ANKLE_TURN + 1.0: t = Quaternion(t.axis, math.radians(ANKLE_TURN))
            new = (Q[f"calf_{s}"] @ T_Q0[f"calf_{s}"].inverted()) @ sw @ t @ T_Q0[f"foot_{s}"]
            fix = new @ Q[f"foot_{s}"].inverted(); Q[f"foot_{s}"] = new; Q[f"ball_{s}"] = fix @ Q[f"ball_{s}"]
    A.clear(); turn = None
    for b in ORDER:
        place(b)
        if b.name in CLOAK_BONES:
            if turn is None: turn = cloak_turn(A)                  # (once a frame: her upper back is placed before any cloak bone)
            hang(A, b, turn)
    solve.bend = bend
    out = {}
    for b in ORDER:
        base = (A[b.parent.name] @ REST_LOCAL[b.name]) if b.parent else REST_LOCAL[b.name]
        m = base.inverted() @ A[b.name]; out[b.name] = (m.translation.copy(), m.to_quaternion())
    return out, dict(W), short


def twist(qp, qc, qp0, qc0, axis):
    """the child's turn about its parent's own line (degrees, from the rest pose), the swing left out"""
    r = (qp @ qp0.inverted()).inverted() @ (qc @ qc0.inverted())
    a = math.degrees(2.0 * math.atan2(Vector((r.x, r.y, r.z)).dot(axis), r.w))
    return (a + 180.0) % 360.0 - 180.0


JOINTS = (("hip", "pelvis", "thigh", "calf"), ("ankle", "calf", "foot", "foot"))    # (name, parent, child, the bone the line runs to)
def twists(q, q0, pos):
    out = {}
    for s in "lr":
        for nm, par, ch, to in JOINTS:
            p_, c_ = (par if par == "pelvis" else f"{par}_{s}"), f"{ch}_{s}"
            ax = way(pos, f"thigh_{s}", f"calf_{s}") if nm == "hip" else way(pos, f"calf_{s}", f"foot_{s}")
            out[f"{nm}_{s}"] = twist(q[p_], q[c_], q0[p_], q0[c_], ax)
    return out


ANKLE_TURN, ANKLE_BEND, LEG_ROLL, FOOT_ROLL, FOOT_WILD = 20.0, 40.0, 30.0, 20.0, 60.0
TRACE_ANKLE = False
ANKLE_MAX = ANKLE_BEND
FLOOR = min(T_POS[f"ball_{s}"].z for s in "lr"); S_FLOOR = min(S_POS[f"ball_{s}"].z for s in "lr")
T_FRAMES = {}; META = {}
for name, frames in S_WORLD.items():
    out = []; places = []; worst = 0.0; prev = {}; bend = 0.0; held = 0; solve.roll = 0.0
    for sw in frames:
        TRACE_ANKLE = name in TRACE
        if TRACE_ANKLE: print("MA3 ankle frame", len(out))
        Q, pel, ankles = retarget(sw)
        if TRACE_ANKLE:
            ang = lambda a, b: round(math.degrees(a.angle(b)), 1)
            sp = {n: sw[n].translation for n in ("thigh_r", "calf_r", "foot_r", "ball_r")}
            fd = (sp["ball_r"] - sp["foot_r"]).normalized(); sd = (sp["foot_r"] - sp["calf_r"]).normalized()
            print("MA3 src r: shin %s foot %s  shin^foot %s (rest %s)  thigh^shin %s  foot bone Y %s" % ([round(x, 2) for x in sd], [round(x, 2) for x in fd], ang(sd, fd),
                  ang(way(S_POS, "calf_r", "foot_r"), way(S_POS, "foot_r", "ball_r")), ang((sp["calf_r"] - sp["thigh_r"]), sd), [round(x, 2) for x in (sw["foot_r"].to_quaternion() @ Vector((0, 1, 0)))]))
        basis, W, short = solve(Q, pel, ankles)
        if TRACE_ANKLE:
            fd = (W["ball_r"] - W["foot_r"]).normalized(); sd = (W["foot_r"] - W["calf_r"]).normalized()
            print("MA3 her r: shin %s foot %s  shin^foot %s (rest %s)" % ([round(x, 2) for x in sd], [round(x, 2) for x in fd], ang(sd, fd), ang(way(T_POS, "calf_r", "foot_r"), way(T_POS, "foot_r", "ball_r"))))
        worst = max(worst, short); bend = max(bend, solve.bend); held += solve.bend > ANKLE_MAX
        for n, (loc, rot) in basis.items():                    # (the same way round as the frame before)
            if n in prev and prev[n].dot(rot) < 0: rot.negate()
            prev[n] = rot
        out.append(basis); places.append(W)
        tw_t = twists(Q, T_Q0, T_POS); tw_s = twists({n: sw[n].to_quaternion() for n in S_Q0}, S_Q0, S_POS)
        if name in TRACE: print("MA3 twist %s %2d  hers %s  source %s" % (name, len(out) - 1, {k: round(v) for k, v in tw_t.items()}, {k: round(v) for k, v in tw_s.items()}))
    T_FRAMES[name] = out
    low = min(min(W[f"ball_{s}"].z for s in "lr") for W in places) - FLOOR
    s_low = min(min(sw[f"ball_{s}"].translation.z for s in "lr") for sw in frames) - S_FLOOR
    m = {"frames": len(out), "length": round((len(out) - 1) / FPS, 4), "feet_low": round(low, 4), "feet_low_source": round(s_low, 4), "ankle_short": round(max(0.0, worst), 4),
         "ankle_bend_source": round(bend, 1), "sole_roll_source": round(solve.roll, 1), "ankle_frames_held": held}
    if name in ("Walk", "Run"):                                 # (the planted foot's speed back under her: she faces -Y)
        v = []
        for i in range(len(places) - 1):
            s = min("lr", key=lambda s: places[i][f"ball_{s}"].z + places[i + 1][f"ball_{s}"].z)
            v.append((places[i + 1][f"foot_{s}"].y - places[i][f"foot_{s}"].y) * FPS)
        v.sort(); m["speed"] = round(v[len(v) // 2], 4)
    META[name] = m
tp = os.path.join(OUT, "ma_times.json")
if os.path.exists(tp):
    for n, t in json.load(open(tp)).items():
        if n in META: META[n]["hit"] = t["hit"]; META[n]["bone"] = t["bone"]
# (--own: her own clips first, as they came, then the carried ones)
if OWN:
    T_FRAMES = {**OWN, **{k: v for k, v in T_FRAMES.items() if k not in OWN}}
    for k, v in OWN.items(): META.setdefault(k, {"frames": len(v), "length": round((len(v) - 1) / FPS, 4), "own": True})
zs = [(meshes[0].matrix_world @ v.co).z for v in meshes[0].data.vertices]
CLIPS_JSON = "ma3_clips.json" if OPT["name"] == "MartialArtist3" else f"{OPT['name']}_clips.json"
json.dump({"fps": FPS, "height": round(max(zs) - min(zs), 4), "clips": META}, open(os.path.join(OUT, CLIPS_JSON), "w"), indent=1)
for n, m in META.items(): print("MA3 clip", n, m)


def pose(fr):
    for pb in arm.pose.bones:
        loc, rot = fr[pb.name]; pb.location = loc; pb.rotation_quaternion = rot
    bpy.context.view_layer.update()


# ---------------------------------------------------------------- pictures of chosen frames (front, side, three-quarter)
if PREVIEW: pictures(sc, PREVIEW, lambda name, i: pose(T_FRAMES[name][min(i, len(T_FRAMES[name]) - 1)]))

# ---------------------------------------------------------------- the clips keyed, each a track of its name; the GLB
ad = arm.animation_data or arm.animation_data_create()
acts = []
for name, frames in T_FRAMES.items():
    act = bpy.data.actions.new(name); act.use_fake_user = True; ad.action = act
    # (the pelvis's place, and any other bone's that a clip of her own moves (its root, a prop's bone))
    moved = {"pelvis"} | {b for b in frames[0] if any(fr[b][0].length > 1e-5 for fr in frames)}
    for i, fr in enumerate(frames):
        for pb in arm.pose.bones:
            loc, rot = fr[pb.name]; pb.location = loc; pb.rotation_quaternion = rot
            pb.keyframe_insert("rotation_quaternion", frame=i, group=pb.name)
            if pb.name in moved: pb.keyframe_insert("location", frame=i, group=pb.name)
    acts.append(act); print("keyed", name, len(frames))
ad.action = None
for act in acts:
    tr = ad.nla_tracks.new(); tr.name = act.name; st = tr.strips.new(act.name, 0, act); st.name = act.name
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
glb = os.path.join(OUT, f"{OPT['name']}_Animated.glb")
bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', export_animations=True, export_animation_mode='NLA_TRACKS',
                          export_force_sampling=True, export_optimize_animation_size=False, export_skins=True, export_yup=True)
print("MA3 DONE", glb, os.path.getsize(glb))
