"""An idle for Summoner5 (the user's of 2026-11-11: "create an idle animation with her shifting her feet, swinging her
arms, looking left and right and tilting her head"). Her GLB has a walk and a run only. A 9 s loop, every frame solved
from the time (martialartist_clips' body, feet planted by its leg solver, so a planted foot never slides; the arms by the
ways they point), over a breath and a small pendulum of her arms:
  1.2-2.8 s  her weight onto her left leg, her right foot lifted and set down a little out and back, her weight between
  3.0-4.4 s  both arms swung forward and back, twice, loosely
  4.6-6.2 s  she looks to her left, then to her right
  6.2-7.2 s  she tilts her head to her right, and back
  7.2-8.6 s  her weight onto her left leg again, her right foot back where it began, her weight between
Her arms hang by her sides (the model stands in an A-pose: they are lowered from it). Writes <out.glb>: the model with the
Idle first, then its own clips; summoner5_cloak.py then gives the cloak its bones and bakes it into every clip.
Blender: -b -P summoner5_idle.py -- Summoner5.glb out.glb [picture_prefix]"""
import bpy, sys, os, math, json, struct
from mathutils import Vector, Quaternion, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = argv[0], argv[1]
PICS = argv[2] if len(argv) > 2 else None
import caster_clips as C
import darkcaster_clips as DC
import rogue_clips as R
import martialartist_clips as MA
FPS = 24
F, U, LEAN = C.F, C.U, C.LEAN
RIGHT = C.OUT["r"]
IDLE_T = 9.0                                         # (216 frames: the loop closes on a frame)
HANG = 11.0                                          # (degrees her arms hang out from straight down)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
sc = bpy.context.scene; sc.render.fps = FPS
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
for o in [o for o in sc.objects if o.type == 'MESH' and not o.vertex_groups]: bpy.data.objects.remove(o, do_unlink=True)
ad = arm.animation_data_create()
for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
ad.action = None
for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'; pb.matrix_basis.identity()
bpy.context.view_layer.update()
_raw = open(SRC, "rb").read(); _J = json.loads(_raw[20:20 + struct.unpack("<I", _raw[12:16])[0]])
ORDER = [x.get("name") for x in _J.get("animations", [])]
OWN = sorted(bpy.data.actions, key=lambda a: ORDER.index(a.name) if a.name in ORDER else len(ORDER))

ctx = C.context(arm); DC.add_thumb_op(ctx, arm); ctx["cm"] = R.model_height(sc) / 170.0; MA.leg_context(ctx, arm)
cm = ctx["cm"]
B = arm.data.bones
REST_OUT = {}
for s in "lr":
    d = (B[f"lowerarm_{s}"].head_local - B[f"upperarm_{s}"].head_local).normalized()
    REST_OUT[s] = math.degrees(math.atan2(d.dot(C.OUT[s]), -d.z))
print("IDLE her arms at rest stand %.0f / %.0f degrees out from straight down; they hang at %.0f" % (REST_OUT["l"], REST_OUT["r"], HANG))


def bump(t, t0, t1):
    if t <= t0 or t >= t1: return 0.0, 0.0
    u = (t - t0) / (t1 - t0); return u, math.sin(math.pi * u) ** 2


def ramp(t, t0, t1):
    """0 before t0, 1 after t1, eased between"""
    x = min(1.0, max(0.0, (t - t0) / (t1 - t0))); return x * x * (3.0 - 2.0 * x)


def arm_ways(side, out_deg, swing, bend):
    """the upper arm's, forearm's and hand's ways: `out_deg` out from straight down to her side, swung `swing` degrees
    forward (negative: back), the elbow bent `bend` forward"""
    o = C.OUT[side]; a = math.radians(out_deg)
    up = -U * math.cos(a) + o * math.sin(a)
    q_up = Quaternion(LEAN, math.radians(-swing))            # (about her lateral axis: a negative turn takes "down" forward)
    low = -U * math.cos(a * 0.6) + o * math.sin(a * 0.6)
    q_low = Quaternion(LEAN, math.radians(-(swing + bend)))
    hand = Quaternion(LEAN, math.radians(-(swing + bend + 6.0))) @ (-U * math.cos(a * 0.4) + o * math.sin(a * 0.4) + F * 0.05).normalized()
    return q_up @ up, q_low @ low, hand


def idle(t):
    ph = 2.0 * math.pi * t / IDLE_T
    breath = math.sin(3.0 * ph)
    # weight: to her left (+) for each step, back between them
    w = 1.0 * (ramp(t, 1.2, 1.6) - ramp(t, 2.4, 2.8)) + 1.0 * (ramp(t, 7.2, 7.6) - ramp(t, 8.2, 8.6))
    # her right foot: out (to her right) and back while away (0 at home, 1 at its new place), lifted while it moves
    away = ramp(t, 1.65, 2.35) - ramp(t, 7.65, 8.35)
    u1, s1 = bump(t, 1.6, 2.4); u2, s2 = bump(t, 7.6, 8.4); lift = 5.0 * (s1 + s2)
    # her weight a little onto the moved foot between the steps (it is further out)
    w -= 0.35 * ramp(t, 2.8, 3.4) * (1.0 - ramp(t, 6.6, 7.2))
    fr = MA.Fr()
    ul, look = bump(t, 4.6, 6.2); turn = 38.0 * math.sin(2.0 * math.pi * ul) * math.sin(math.pi * ul) if look else 0.0
    ut, tilt = bump(t, 6.2, 7.2); roll = 13.0 * tilt + 4.0 * math.sin(2.0 * math.pi * ul) * math.sin(math.pi * ul)
    sp = MA.body(ctx, fr, twist=-0.15 * turn, lean=1.5 - 0.8 * breath, side=2.5 * w, drop=1.0 - 0.3 * breath, look=0.0)
    sp.setdefault("pelvis", []).append(("move", RIGHT * (-2.6 * w) * cm))
    sp["pelvis"].append(("rot", F, 3.0 * w))                                  # (the hip of the leg she stands on, up)
    sp["neck_01"].append(("rot", U, turn * 0.4)); sp["neck_01"].append(("rot", fr.v(F), -roll * 0.4))
    sp["head"] = [("rot", U, turn * 0.45), ("rot", fr.v(F), -roll * 0.6), ("rot", LEAN, 2.0 * breath)]
    # the feet: the left planted; the right out 7 cm and back 4 when away, lifted while it moves, its toes down a little
    sp.update(MA.plant("l", 0.0, 0.0, yaw=4.0))
    sp.update(MA.plant("r", 7.0 * away, -4.0 * away, z=lift, yaw=-4.0 - 8.0 * away, pitch=12.0 * (s1 + s2)))
    # the arms: a small pendulum always (opposite arms), and the swing, twice forward and back, in its window
    ua, swing = bump(t, 3.0, 4.4)
    big = 28.0 * math.sin(4.0 * math.pi * ua) * (swing ** 0.5) if swing else 0.0
    for side, sgn in (("l", 1.0), ("r", -1.0)):
        pend = 3.0 * sgn * math.sin(ph * 2.0)
        sw = pend + big * (1.0 if side == "l" else 0.85) + 2.0 * w * sgn
        up, low, hand = arm_ways(side, HANG + 2.0 * swing, sw, 12.0 + 6.0 * swing * (1.0 if big > 0 else 0.5))
        sp[f"upperarm_{side}"] = [("dir", up)]; sp[f"lowerarm_{side}"] = [("dir", low)]; sp[f"hand_{side}"] = [("dir", hand)]
        sp.update(MA.open_hand(side, curl=14.0))
    return sp


n = int(round(IDLE_T * FPS))
frames = [MA.apply(arm, idle(i / FPS), ctx) for i in range(n)]
frames.append(frames[0])
act = bpy.data.actions.new("Idle"); act.use_fake_user = True; ad.action = act
for i, fr_ in enumerate(frames):
    for pb in arm.pose.bones:
        loc, rot, scl = fr_[pb.name]; pb.location = loc; pb.rotation_quaternion = rot
        # (from frame 0: keyed from 1 the clip came out 9.04 s, its start held a frame where the loop closes)
        pb.keyframe_insert("rotation_quaternion", frame=i, group=pb.name)
        if pb.name == "pelvis": pb.keyframe_insert("location", frame=i, group=pb.name)
ad.action = None
print("IDLE keyed %d frames (%.2f s)" % (len(frames), (len(frames) - 1) / FPS))

if PICS:
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'TEXTURE'; sc.display.shading.light = 'STUDIO'
    sc.render.resolution_x = 520; sc.render.resolution_y = 600
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.15; cam.data.clip_end = 100
    ad.action = act
    for f in (0, 30, 46, 60, 85, 98, 128, 142, 162, 192):
        sc.frame_set(f)
        for view, ang in (("front", 0), ("side", 90), ("q", 35)):
            r = math.radians(ang); d = Vector((math.sin(r), -math.cos(r), 0.05))
            cam.location = Vector((0, 0, 0.5)) + d * 6; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = f"{PICS}_{f}_{view}.png"; bpy.ops.render.render(write_still=True)
    ad.action = None
    bpy.data.objects.remove(cam, do_unlink=True)

for a in [act] + OWN:
    a.use_fake_user = True
    tr = ad.nla_tracks.new(); tr.name = a.name; st = tr.strips.new(a.name, int(a.frame_range[0]), a); st.name = a.name
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_animations=True, export_animation_mode='NLA_TRACKS',
                          export_force_sampling=True, export_optimize_animation_size=False, export_skins=True, export_yup=True)
print("IDLE DONE", OUT, os.path.getsize(OUT))
