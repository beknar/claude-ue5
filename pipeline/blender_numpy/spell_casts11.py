"""Three spells' own casts (the user's list of 2026-11-11: "need new animation and visual for starfall that's different from meteor
storm", "... for spell singularity that's different from void rift", "... for spell soul rend that's different from life drain"),
a clip maker for tripo_build.py (make_clips(arm, scene, clips) -> {name: frames}), on any caster's rig (the Mage, the Warlock
after her arms are lengthened, the Summoner): martialartist_clips' body, her feet planted by its leg solver, her arms by the
ways they point (summoner5_idle's way), eased from her hanging arms and back:
  Cast_Starfall     2.0 s  both arms raised over her head, her head back, a breath there gathering, then swept down and
                           forward as she leans in (the stars called down: the release at 1.15 s), back to her sides
  Cast_Singularity  2.0 s  her hands brought together before her chest, drawn apart slowly (the void opening), then crushed
                           together (the release at 1.25 s) with her shoulders hunched over them, back
  Cast_SoulRend     1.6 s  her right hand thrust out, clawed, her body turned into it, then ripped back to her hip as she
                           turns away (the release at 0.75 s), her left hand up before her, back
Writes spell_casts11_times.json in the out dir given to tripo_build (argv[1]): each clip's length and release.
Run through tripo_build.py:  -b -P tripo_build.py -- <hero.glb> <out_dir> SK_JRPG_<CH> <Tag> <height> spell_casts11.py"""
import bpy, sys, os, math, json
from mathutils import Vector, Quaternion
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import caster_clips as C
import darkcaster_clips as DC
import rogue_clips as R
import martialartist_clips as MA
FPS = 24
F, U, LEAN = C.F, C.U, C.LEAN
HANG = 11.0
CLIPS = {"Cast_Starfall": (2.0, 1.15), "Cast_Singularity": (2.0, 1.25), "Cast_SoulRend": (1.6, 0.75)}


def ramp(t, t0, t1):
    x = min(1.0, max(0.0, (t - t0) / (t1 - t0))); return x * x * (3.0 - 2.0 * x)


def mix(a, b, w):
    v = a * (1.0 - w) + b * w
    return v.normalized() if v.length > 1e-6 else b.normalized()


def lerp3(a, b, w): return tuple(x * (1.0 - w) + y * w for x, y in zip(a, b))


def put(sp, fr, side, at, pole, curl):
    """her hand's root at `at` (cm from the base of her neck: her right, forward, up; mirrored for her left) with the elbow
    toward `pole` (out, forward, up from her side), martialartist_clips' reach: the same places on any rig"""
    sx = 1.0 if side == "r" else -1.0
    sp.update(MA.hand(fr, side, sx * at[0], at[1], at[2], C.D(side, *pole), closed=False))
    sp.update(MA.open_hand(side, curl=curl))


def key(seq, t):
    """a place along keys [(t, value), ...], eased between them"""
    if t <= seq[0][0]: return seq[0][1]
    for (t0, a), (t1, b) in zip(seq, seq[1:]):
        if t <= t1: return lerp3(a, b, ramp(t, t0, t1))
    return seq[-1][1]


HANG_AT, HANG_POLE = (19.0, 3.0, -38.0), (0.6, -0.5, 0.0)


def starfall(ctx, t):
    r = ramp(t, 0.1, 0.65); d = ramp(t, 0.95, 1.2); back = ramp(t, 1.45, 1.95)
    fr = MA.Fr()
    sp = MA.body(ctx, fr, lean=-7.0 * r * (1 - d) + 9.0 * d * (1 - back), drop=1.5 * d * (1 - back), look=0.0)
    sp["head"] = [("rot", LEAN, -16.0 * r * (1 - d) + 6.0 * d * (1 - back))]
    sp.update(MA.plant("l", 0.0, 0.0)); sp.update(MA.plant("r", 0.0, 0.0))
    at = key([(0.0, HANG_AT), (0.65, (15.0, 6.0, 33.0)), (0.95, (18.0, 8.0, 30.0)), (1.2, (16.0, 34.0, -12.0)), (1.45, (16.0, 32.0, -14.0)), (1.95, HANG_AT)], t)
    pole = key([(0.0, HANG_POLE), (0.65, (1.0, -0.3, 0.0)), (1.2, (0.7, 0.0, -0.7)), (1.95, HANG_POLE)], t)
    for side in "lr": put(sp, fr, side, at, pole, curl=8.0 + 10.0 * d * (1 - back))
    return sp


def singularity(ctx, t):
    c = ramp(t, 1.1, 1.3); back = ramp(t, 1.45, 1.95)
    fr = MA.Fr()
    sp = MA.body(ctx, fr, lean=3.0 + 7.0 * c * (1 - back), drop=1.0 + 2.0 * c * (1 - back), look=0.0)
    sp["head"] = [("rot", LEAN, 8.0 * (1 - back))]
    sp.update(MA.plant("l", 0.0, 0.0)); sp.update(MA.plant("r", 0.0, 0.0))
    at = key([(0.0, HANG_AT), (0.45, (5.0, 26.0, -14.0)), (0.55, (5.0, 26.0, -14.0)), (0.95, (27.0, 24.0, -8.0)), (1.1, (27.0, 24.0, -8.0)),
              (1.3, (3.0, 22.0, -16.0)), (1.45, (3.0, 22.0, -16.0)), (1.95, HANG_AT)], t)
    pole = key([(0.0, HANG_POLE), (0.45, (1.0, 0.0, -0.6)), (0.95, (0.4, 0.0, -1.0)), (1.3, (1.0, 0.2, -0.4)), (1.95, HANG_POLE)], t)
    for side in "lr": put(sp, fr, side, at, pole, curl=10.0 + 50.0 * c * (1 - back))
    return sp


def soul_rend(ctx, t):
    r = ramp(t, 0.05, 0.4); p = ramp(t, 0.6, 0.82); back = ramp(t, 1.05, 1.55)
    fr = MA.Fr()
    sp = MA.body(ctx, fr, twist=18.0 * r * (1 - p) - 24.0 * p * (1 - back), lean=6.0 * r * (1 - p) - 3.0 * p * (1 - back), look=0.0)
    sp.update(MA.plant("l", 0.0, 0.0)); sp.update(MA.plant("r", 0.0, 0.0))
    at = key([(0.0, HANG_AT), (0.4, (12.0, 40.0, 0.0)), (0.6, (12.0, 40.0, 0.0)), (0.82, (22.0, -12.0, -43.0)), (1.05, (22.0, -12.0, -43.0)), (1.55, HANG_AT)], t)
    pole = key([(0.0, HANG_POLE), (0.4, (0.8, 0.0, -0.6)), (0.82, (0.5, -1.0, 0.0)), (1.55, HANG_POLE)], t)
    put(sp, fr, "r", at, pole, curl=10.0 + 45.0 * r * (1 - back))
    g = max(r, p) * (1 - back)
    put(sp, fr, "l", lerp3(HANG_AT, (9.0, 22.0, -4.0), g), lerp3(HANG_POLE, (0.9, 0.0, -0.5), g), curl=12.0)
    return sp

POSE = {"Cast_Starfall": starfall, "Cast_Singularity": singularity, "Cast_SoulRend": soul_rend}


def preview(arm_obj, scene, out, prefix):
    """each clip at its key moments, front and side (workbench, textured), for a look before it is imported"""
    scene.render.engine = 'BLENDER_WORKBENCH'; scene.display.shading.color_type = 'TEXTURE'; scene.display.shading.light = 'STUDIO'
    scene.render.resolution_x = 420; scene.render.resolution_y = 520
    cam = bpy.data.objects.new("spell11_cam", bpy.data.cameras.new("spell11_cam")); scene.collection.objects.link(cam); scene.camera = cam
    h = R.model_height(scene)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = h * 1.45; cam.data.clip_end = h * 60
    keys = {"Cast_Starfall": (0.0, 0.7, 1.15, 1.7), "Cast_Singularity": (0.45, 0.95, 1.25, 1.7), "Cast_SoulRend": (0.4, 0.75, 1.0, 1.4)}
    for name, frames in out.items():
        for t in keys.get(name, ()):
            fr_ = frames[min(len(frames) - 1, int(round(t * FPS)))]
            for pb in arm_obj.pose.bones:
                loc, rot, scl = fr_[pb.name]; pb.location = loc; pb.rotation_quaternion = rot; pb.scale = scl
            bpy.context.view_layer.update()
            for view, ang in (("front", 0), ("side", 90)):
                r = math.radians(ang); d = Vector((math.sin(r), -math.cos(r), 0.08))
                cam.location = Vector((0, 0, h * 0.55)) + d * h * 8; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
                scene.render.filepath = f"{prefix}_{name}_{t:.2f}_{view}.png"; bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)


def make_clips(arm_obj, scene, clips):
    ctx = C.context(arm_obj); DC.add_thumb_op(ctx, arm_obj); ctx["cm"] = R.model_height(scene) / 170.0
    R.arm_context(ctx, arm_obj); MA.leg_context(ctx, arm_obj)
    ctx["cont_w"] = 0.03
    keep_roll = R.ARM_ROLL; R.ARM_ROLL = 95.0          # (arms over her head and across her chest turn the upper arm far about itself: martialartist_clips' hips allowance)
    out = {}
    for name, (length, release) in CLIPS.items():
        ctx.pop("prev_arm", None)
        frames = []
        for i in range(int(round(length * FPS)) + 1):
            frames.append(MA.apply(arm_obj, POSE[name](ctx, i / FPS), ctx))
            ctx["prev_arm"] = {s: arm_obj.pose.bones[f"upperarm_{s}"].matrix.to_quaternion() for s in "rl"}
        out[name] = frames
        print("SPELL11 %s: %d frames (%.2f s), the release at %.2f s" % (name, len(frames), (len(frames) - 1) / FPS, release))
    R.ARM_ROLL = keep_roll
    pics = os.environ.get("SPELL11_PICS")
    if pics: preview(arm_obj, scene, out, pics)
    for pb in arm_obj.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) > 1 and os.path.isdir(argv[1]):
        json.dump({n: {"length": L, "release": r} for n, (L, r) in CLIPS.items()}, open(os.path.join(argv[1], "spell_casts11_times.json"), "w"), indent=1)
    return out
