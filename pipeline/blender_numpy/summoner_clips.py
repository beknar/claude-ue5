"""The Summoner's clips: the Mage's, retargeted onto her rig (tripo_build.py's clip maker; her rig renamed by summoner_rig.py).

make_clips(arm, scene, clips): loads ai models/Mage.glb into the same scene, takes the Mage's own Walk and Run (her GLB's
clips) and the Idle and three casts caster_clips.py makes for her, and her Flinch and Death as Unreal has them (exported by
pipeline/unreal/832 to SourceArt/summoner/mage_clips/*.fbx, each with the Mage's skeleton; that rig is turned to face the
way the Summoner faces, by their feet, if it does not), and poses the Summoner frame by frame:
  - each bone that both rigs have points where the Mage's bone points (from its head to the head of the child that sets
    its direction: the spine bone above, the next joint of a limb, the middle finger for a hand), turned about that
    direction as the Mage's turns (a reference axis carried by the Mage's bone: the world axis most square to both rest
    directions). Their rest poses differ (the Summoner's arms are level, her spine has four bones), so copying rotations
    would not do: directions are what the eye sees.
  - bones with no child to aim at (the head, the Mage's last finger joints) and the feet (her heels against the Mage's
    flat boots) turn as the Mage's do in the world, from their own rest;
  - her fourth spine bone follows the Mage's third; her palm, the last joint of each finger, the balls of her feet, the
    toes and the hub under her spine stay at rest under their parents;
  - the hips move as the Mage's do, scaled by their legs' length; the root (on the floor) as the Mage's root.
Writes nothing itself; returns {clip: frames} (frames: each pose bone's matrix_basis decomposed, on her GLB's armature).
Preview: blender -b -P summoner_clips.py -- <Summoner_rig.glb> <out_prefix>   (renders key poses front and side, and the
Mage's in the same poses beside her, and prints how far each bone's direction is from the Mage's: "SUMMONER aim")"""
import bpy, os, sys, math, importlib.util
from mathutils import Vector, Matrix, Quaternion
HERE = os.path.dirname(os.path.abspath(__file__))
MAGE = os.path.join(HERE, "..", "..", "ai models", "Mage.glb")
FBX_DIR = os.path.join(HERE, "..", "..", "claude_ue5", "SourceArt", "summoner", "mage_clips")
SIDES = ("l", "r")
FING = ("thumb", "index", "middle", "ring", "pinky")


def aims():
    """bone -> the child whose head sets its direction (the same names on both rigs)"""
    a = {"pelvis": "spine_01", "spine_01": "spine_02", "spine_02": "spine_03", "spine_03": "neck_01", "neck_01": "head"}
    for s in SIDES:
        a.update({f"clavicle_{s}": f"upperarm_{s}", f"upperarm_{s}": f"lowerarm_{s}", f"lowerarm_{s}": f"hand_{s}", f"hand_{s}": f"middle_01_{s}",
                  f"thigh_{s}": f"calf_{s}", f"calf_{s}": f"foot_{s}"})
        for f in FING: a.update({f"{f}_01_{s}": f"{f}_02_{s}", f"{f}_02_{s}": f"{f}_03_{s}"})
    return a


AIM = aims()
# turned as the Mage's in the world (no child to aim at on the Mage's rig). The feet too: she stands in heels, the Mage in
# flat boots; aimed along the Mage's foot, her foot was laid flat and the toes, turned on their own, tore the shoe apart in
# the run. Turned as the Mage's from their rest, her feet keep their shape; the balls and toes stay on them.
DELTA = ["head"] + [f"{f}_03_{s}" for f in FING for s in SIDES] + [f"foot_{s}" for s in SIDES]
FOLLOW = {"spine_04": "spine_03"}          # (her extra spine bone: the Mage's third's direction, to the neck)
# (her own child to aim with where it differs from the Mage's: her third spine bone ends at her fourth, which ends at the
# neck; both take the Mage's third's direction. Aimed at the neck through the fourth, the fourth turned again on top: 21
# degrees off in the run)
SUM_TIP = {"spine_03": "spine_04", "spine_04": "neck_01"}


def frame(d, u):
    y = d.normalized(); x = (u - y * u.dot(y)); x = x.normalized() if x.length > 1e-6 else y.orthogonal().normalized(); z = x.cross(y)
    return Matrix((x, y, z)).transposed()


def depth(b):
    n = 0
    while b.parent: b = b.parent; n += 1
    return n


class Rig:
    def __init__(self, obj):
        self.o = obj; self.B = obj.data.bones; self.mw = obj.matrix_world.copy()
        self.rest = {b.name: self.mw @ b.matrix_local for b in self.B}
    def head0(self, n): return self.rest[n].translation
    def world(self):
        return {pb.name: self.o.matrix_world @ pb.matrix for pb in self.o.pose.bones}


def legs(r):
    return (r.head0("calf_l") - r.head0("thigh_l")).length + (r.head0("foot_l") - r.head0("calf_l")).length


def transfer(sumr, mager, mframes, prev=None):
    """the Summoner's pose (matrix_basis per bone) for the Mage's pose mframes ({bone: (loc, rot, scale)} on the Mage)"""
    mo = mager.o
    for pb in mo.pose.bones:
        if pb.name in mframes:
            l, q, s = mframes[pb.name]; pb.matrix_basis = Matrix.LocRotScale(l, q, s)
        else: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    Wm = mager.world()
    ratio = legs(sumr) / legs(mager)
    out = {}; posed = {}
    Rw2a = sumr.mw.to_3x3().inverted()
    for b in sorted(sumr.B, key=depth):
        n = b.name
        P = posed[b.parent.name] if b.parent else Matrix.Identity(4)
        rest_rel = (b.parent.matrix_local.inverted() @ b.matrix_local) if b.parent else b.matrix_local.copy()
        default = P @ rest_rel
        src = FOLLOW.get(n, n)
        R0s = sumr.rest[n].to_3x3().normalized()
        Rw = None
        if src in mager.rest and (src in AIM or src in DELTA):
            Rm0 = mager.rest[src].to_3x3().normalized(); Rm = Wm[src].to_3x3().normalized()
            Dm = Rm @ Rm0.inverted()                  # (the Mage bone's turn in the world from its rest)
            if src in AIM and AIM[src] in mager.rest and (AIM.get(n) in sumr.rest or n in FOLLOW):
                tip_s = SUM_TIP.get(n) if SUM_TIP.get(n) in sumr.rest else AIM.get(n)     # (a rig without a fourth spine bone: Summoner3)
                dm0 = mager.head0(AIM[src]) - mager.head0(src); dm = Wm[AIM[src]].translation - Wm[src].translation
                ds0 = sumr.head0(tip_s) - sumr.head0(n)
                axes = [Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))]
                w = max(axes, key=lambda a: min(a.cross(dm0.normalized()).length, a.cross(ds0.normalized()).length))
                Rw = frame(dm, Dm @ w) @ frame(ds0, w).inverted() @ R0s
            else:
                Rw = Dm @ R0s
        if Rw is None:
            posed[n] = default
        else:
            head = default.translation.copy()
            if n == "pelvis":
                # (the hips: the Mage's move from her rest, relative to her root, scaled; the root moves the root)
                # (a rig from Unreal's FBX has no root bone: Blender makes it the armature itself, whose origin then stands for it)
                r_now = Wm["root"].translation if "root" in Wm else mager.o.matrix_world.translation
                r_rest = mager.head0("root") if "root" in mager.rest else mager.mw.translation
                mv = (Wm["pelvis"].translation - r_now) - (mager.head0("pelvis") - r_rest)
                head = P @ (rest_rel.translation) if False else default.translation + Rw2a @ (mv * ratio)
            posed[n] = Matrix.LocRotScale(head, (Rw2a @ Rw).to_quaternion(), Vector((1, 1, 1)))
        if n == "root" and "root" in Wm:
            mv = Wm["root"].translation - mager.head0("root")
            posed[n] = Matrix.Translation(Rw2a @ (mv * ratio)) @ default
        basis = rest_rel.inverted() @ P.inverted() @ posed[n]
        l, q, s = basis.decompose()
        if prev and n in prev and prev[n][1].dot(q) < 0: q = -q
        out[n] = (l, q, Vector((1, 1, 1)))
    return out


def sample_actions(arm_obj, scene):
    ad = arm_obj.animation_data
    clips = {}
    if not ad: return clips
    acts = [a for a in bpy.data.actions if a.users >= 0]
    for act in list(bpy.data.actions):
        if not any(fc.data_path.startswith("pose.bones") for fc in getattr(act, "fcurves", [])) and not getattr(act, "layers", None): continue
        ad.action = act
        if hasattr(ad, "action_slot") and act.slots: ad.action_slot = act.slots[0]
        f0, f1 = [int(round(v)) for v in act.frame_range]
        frames = []
        for t in range(f0, f1 + 1):
            scene.frame_set(t); frames.append({pb.name: pb.matrix_basis.decompose() for pb in arm_obj.pose.bones})
        name = act.name.split(".")[0]; clips[name[:1].upper() + name[1:]] = frames
    ad.action = None
    return clips


def make_clips(arm, scene, clips):
    before = set(bpy.data.objects); acts0 = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=MAGE)
    new = [o for o in bpy.data.objects if o not in before]
    marm = next(o for o in new if o.type == 'ARMATURE')
    for o in [o for o in new if o.type == 'MESH' and not o.vertex_groups]: bpy.data.objects.remove(o, do_unlink=True)
    for pb in marm.pose.bones: pb.rotation_mode = 'QUATERNION'
    for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
    mclips = {}
    ad = marm.animation_data
    if ad:
        for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
        for act in [a for a in bpy.data.actions if a not in acts0]:
            ad.action = act
            if hasattr(ad, "action_slot") and act.slots: ad.action_slot = act.slots[0]
            f0, f1 = [int(round(v)) for v in act.frame_range]
            fr = []
            for t in range(f0, f1 + 1):
                scene.frame_set(t); fr.append({pb.name: pb.matrix_basis.decompose() for pb in marm.pose.bones})
            nm = act.name.split(".")[0]; mclips[nm[:1].upper() + nm[1:]] = fr
        ad.action = None
    for pb in marm.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    spec = importlib.util.spec_from_file_location("caster_clips", os.path.join(HERE, "caster_clips.py")); cc = importlib.util.module_from_spec(spec); spec.loader.exec_module(cc)
    mclips.update(cc.make_clips(marm, scene, mclips))
    for pb in marm.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    sumr, mager = Rig(arm), Rig(marm)
    out = {}
    for name, frames in mclips.items():
        res = []; prev = None
        for fr in frames:
            prev = transfer(sumr, mager, fr, prev); res.append(prev)
        out[name] = res
        print("SUMMONER clip", name, len(res))
    # the Mage's clips that only Unreal has (her flinch and death), each on its own exported rig
    for fbx in sorted(f for f in os.listdir(FBX_DIR) if f.lower().endswith(".fbx")) if os.path.isdir(FBX_DIR) else []:
        b0 = set(bpy.data.objects); a0 = set(bpy.data.actions)
        fps0, base0 = scene.render.fps, scene.render.fps_base
        bpy.ops.import_scene.fbx(filepath=os.path.join(FBX_DIR, fbx))
        # (the importer sets the scene to the file's rate, 30, and keys the clip on its frames: the build keys at the scene's
        # own rate (24), so the clip is sampled at those times between its frames. Left at 30, every clip came out 0.8 times
        # its length and she walked a quarter faster.)
        src_fps = scene.render.fps / scene.render.fps_base
        scene.render.fps, scene.render.fps_base = fps0, base0
        step = src_fps / (fps0 / base0)
        nw = [o for o in bpy.data.objects if o not in b0]
        farm = next(o for o in nw if o.type == 'ARMATURE')
        for o in nw:
            if o.type == 'MESH': bpy.data.objects.remove(o, do_unlink=True)
        act = farm.animation_data.action if farm.animation_data else None
        if act is None: print("SUMMONER", fbx, "has no clip"); continue
        farm.animation_data.action = None
        for pb in farm.pose.bones: pb.rotation_mode = 'QUATERNION'; pb.matrix_basis.identity()
        bpy.context.view_layer.update()
        # (facing the Summoner's way: the feet's forward, flat)
        def fwd(r):
            v = Vector((0, 0, 0))
            for s_ in SIDES: v += r.head0(f"ball_{s_}") - r.head0(f"foot_{s_}")
            v.z = 0.0; return v.normalized()
        ang = fwd(Rig(farm)).to_2d().angle_signed(fwd(sumr).to_2d())
        if abs(ang) > math.radians(3):
            farm.matrix_world = Matrix.Rotation(-ang, 4, 'Z') @ farm.matrix_world; bpy.context.view_layer.update()
        frig = Rig(farm)
        farm.animation_data.action = act
        if hasattr(farm.animation_data, "action_slot") and act.slots: farm.animation_data.action_slot = act.slots[0]
        f0, f1 = act.frame_range
        fr_ = []; f = f0
        while f <= f1 + 1e-6:
            scene.frame_set(int(math.floor(f)), subframe=f - math.floor(f)); fr_.append({pb.name: pb.matrix_basis.decompose() for pb in farm.pose.bones}); f += step
        farm.animation_data.action = None
        name = os.path.splitext(fbx)[0]; res = []; prev = None
        for fr in fr_:
            prev = transfer(sumr, frig, fr, prev); res.append(prev)
        out[name] = res
        print("SUMMONER clip", name, len(res), "from", fbx, "(turned %.1f degrees; %g fps sampled at %g)" % (math.degrees(ang), src_fps, fps0 / base0))
        for o in [o for o in bpy.data.objects if o not in b0]: bpy.data.objects.remove(o, do_unlink=True)
        for a in [a for a in bpy.data.actions if a not in a0]: bpy.data.actions.remove(a)
    # (the Mage goes: her armature, mesh and clips must not be exported with the Summoner)
    for o in [o for o in bpy.data.objects if o in new or o.parent in new]:
        if o.name in bpy.data.objects: bpy.data.objects.remove(o, do_unlink=True)
    for a in [a for a in bpy.data.actions if a not in acts0]: bpy.data.actions.remove(a)
    for pb in arm.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    return out


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:]
    src, prefix = argv[0], argv[1]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    sc = bpy.context.scene; sc.render.fps = 24
    for o in [o for o in sc.objects if o.type == 'MESH' and not o.vertex_groups]: bpy.data.objects.remove(o, do_unlink=True)
    arm = next(o for o in sc.objects if o.type == 'ARMATURE')
    clips = make_clips(arm, sc, {})
    # (the Mage again, beside her, to compare the poses)
    before = set(bpy.data.objects); acts0 = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=MAGE)
    new = [o for o in bpy.data.objects if o not in before]
    marm = next(o for o in new if o.type == 'ARMATURE')
    for o in [o for o in new if o.type == 'MESH' and not o.vertex_groups]: bpy.data.objects.remove(o, do_unlink=True)
    if marm.animation_data: marm.animation_data.action = None
    for pb in marm.pose.bones: pb.rotation_mode = 'QUATERNION'
    spec = importlib.util.spec_from_file_location("caster_clips", os.path.join(HERE, "caster_clips.py")); cc = importlib.util.module_from_spec(spec); spec.loader.exec_module(cc)
    mc = {}
    acts = [a for a in bpy.data.actions if a not in acts0]
    ad = marm.animation_data_create()
    for act in acts:
        ad.action = act
        if hasattr(ad, "action_slot") and act.slots: ad.action_slot = act.slots[0]
        f0, f1 = [int(round(v)) for v in act.frame_range]; fr = []
        for t in range(f0, f1 + 1): sc.frame_set(t); fr.append({pb.name: pb.matrix_basis.decompose() for pb in marm.pose.bones})
        nm = act.name.split(".")[0]; mc[nm[:1].upper() + nm[1:]] = fr
    ad.action = None
    for pb in marm.pose.bones: pb.matrix_basis.identity()
    mc.update(cc.make_clips(marm, sc, mc))
    sumr, mager = Rig(arm), Rig(marm)
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'TEXTURE'; sc.display.shading.light = 'STUDIO'
    sc.render.resolution_x = 900; sc.render.resolution_y = 700
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.6
    worst = (0.0, None)
    for name in clips:
        n = len(clips[name]); picks = sorted({0, n // 4, n // 2, (3 * n) // 4})
        for fi in picks:
            for pb in arm.pose.bones:
                l, q, s = clips[name][fi][pb.name]; pb.matrix_basis = Matrix.LocRotScale(l, q, s)
            for pb in marm.pose.bones:
                if name not in mc: pb.matrix_basis.identity(); continue          # (the clips from Unreal: hers only)
                if pb.name in mc[name][fi]: l, q, s = mc[name][fi][pb.name]; pb.matrix_basis = Matrix.LocRotScale(l, q, s)
            bpy.context.view_layer.update()
            Ws, Wm = sumr.world(), mager.world()
            for b, c in AIM.items():
                if name in mc and b in Ws and c in Ws and b in Wm and c in Wm:
                    ds = (Ws[c].translation - Ws[b].translation).normalized(); dm = (Wm[c].translation - Wm[b].translation).normalized()
                    worst = max(worst, (math.degrees(ds.angle(dm)), f"{b} in {name} frame {fi}"), key=lambda x: x[0])
            for view, ang in (("front", 0), ("side", 90)):
                a = math.radians(ang); d = Vector((math.sin(a), -math.cos(a), 0.0))
                marm.location = Vector((1.1, 0, 0)) if view == "front" else Vector((0, 1.2, 0))      # (beside her in either view)
                bpy.context.view_layer.update()
                cam.location = Vector((0.55, 0, 0.85)) + d * 5.0; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
                sc.render.filepath = f"{prefix}_{name}_{fi:02d}_{view}.png"; bpy.ops.render.render(write_still=True)
    print("SUMMONER aim: the worst bone direction against the Mage's", round(worst[0], 2), "degrees,", worst[1])
