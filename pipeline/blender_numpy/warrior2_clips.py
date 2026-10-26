"""ai models/Warrior2.glb's own clips for its chop test in random_dungeonmagic_level5 (tripo_build.py's clip_maker, tag
Warrior2: her own rig, her own proportions; nothing of hers goes onto the Warrior's rig, and the Warrior's clips stay
hers). Warrior2.glb is the Warrior's mesh, weights and texture with Tripo's clips: chop, slash (the same motion as chop,
frame for frame) and a horizontal two-handed sweep.

The clips are kept as Tripo made them but for one thing: where a clip turns `root` (the chop and the slash turn it 90
degrees and the pelvis about as far back), the pelvis bone's head lies on the floor 60 cm to her side and drags her
hips' skin there (its children are carried back by their own keys); in Unreal the pelvis stood on the floor beside her.
Those clips get their pelvis fitted to its children's heads (spine_01, thigh_l, thigh_r: the rigid turn and move that
takes their rest places to where the frame has them), the root at rest, every other bone where it was.

Writes <out_dir>/chop.json for the test (pipeline/unreal/861, 815's way "chop2"):
  blow        seconds into the chop where the right hand moves fastest (relative to the pelvis) after the wind-up
  swing       its frames from the wind-up's start to standing again (CHOP_SWING), in seconds
  left_on     cm from the right palm to the left along a sword in the right hand (the blade the thumb's way leaning 25
              degrees toward the fingers, as weapon5_clips holds a sword): the median over the frames the fists are
              together; the sword is put in her hand so that its grip point lies there, under the left palm
  left_off    cm the left palm is off that hilt line in those frames (median, most): the clip's own hands on a sword
Preview: blender -b -P warrior2_clips.py -- <Warrior2.glb> <out_dir>   (prints the fix and chop.json)"""
import json, math, os, sys
import bpy
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
FPS = 24
CHOP_SWING = (20, 92)            # (the chop's frames: from the wind-up's start (still before) to standing again; the blow at 51)
TOGETHER = 32.0                  # (cm between the palms (of her 170): the fists together on a hilt)


def _depth(b):
    n = 0
    while b.parent: b = b.parent; n += 1
    return n


def root_turned(frames, deg=10.0):
    """whether any frame turns `root` from its rest by more than deg degrees"""
    return any(math.degrees(fr["root"][1].angle) > deg for fr in frames if "root" in fr)


def level_pelvis(arm, frames):
    """each frame's pelvis fitted to its children's heads (rigid, from their rest places), the root at rest, every other
    bone where the frame has it (its matrix in the armature); returned as matrix_basis per bone"""
    import numpy as np
    P = arm.pose.bones; B = arm.data.bones; rest = {b.name: b.matrix_local.copy() for b in B}; order = sorted(B, key=_depth)
    kids = ("spine_01", "thigh_l", "thigh_r"); out = []; prev = {}
    for fr in frames:
        for pb in P:
            if pb.name in fr: l_, q_, s_ = fr[pb.name]; pb.matrix_basis = Matrix.LocRotScale(l_, q_, s_)
        bpy.context.view_layer.update()
        M = {pb.name: pb.matrix.copy() for pb in P}
        src = np.array([list(rest[k].translation) for k in kids]); dst = np.array([list(M[k].translation) for k in kids])
        cs, cd = src.mean(0), dst.mean(0); U_, _, Vt = np.linalg.svd((src - cs).T @ (dst - cd))
        Rm = Vt.T @ U_.T
        if np.linalg.det(Rm) < 0: Vt[-1] *= -1; Rm = Vt.T @ U_.T
        t = cd - Rm @ cs
        M["pelvis"] = Matrix([list(Rm[0]) + [t[0]], list(Rm[1]) + [t[1]], list(Rm[2]) + [t[2]], [0, 0, 0, 1]]) @ rest["pelvis"]
        M["root"] = rest["root"].copy()
        res = {}
        for b in order:
            par = M[b.parent.name] if b.parent else Matrix.Identity(4)
            rel = (rest[b.parent.name].inverted() @ rest[b.name]) if b.parent else rest[b.name]
            l_, q_, s_ = (rel.inverted() @ par.inverted() @ M[b.name]).decompose()
            if b.name in prev and prev[b.name].dot(q_) < 0: q_ = -q_
            prev[b.name] = q_; res[b.name] = (l_, q_, Vector((1.0, 1.0, 1.0)))
        out.append(res)
    for pb in P: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    return out


def pose(arm, fr):
    for pb in arm.pose.bones:
        if pb.name in fr: l_, q_, s_ = fr[pb.name]; pb.location = l_; pb.rotation_quaternion = q_; pb.scale = s_
    bpy.context.view_layer.update()


def mesh_span(scene):
    """her skin's extent (x, y, z ranges, armature units) as posed: the hips dragged aside show here"""
    me = next(o for o in scene.objects if o.type == 'MESH' and o.vertex_groups)
    ev = me.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh(); vs = [ev.matrix_world @ v.co for v in m.vertices]
    r = [(min(v[i] for v in vs), max(v[i] for v in vs)) for i in range(3)]; ev.to_mesh_clear()
    return r


def chop_numbers(arm, scene, frames):
    """the blow, and the palms on a sword in the right hand (see the docstring)"""
    import caster_clips as C, rogue_clips as R, weapon5_clips as W
    ctx = C.context(arm); ctx["cm"] = R.model_height(scene) / 170.0; R.arm_context(ctx, arm); W.frames(ctx, arm); W.use(ctx, "sword")
    cm = ctx["cm"]; P = arm.pose.bones; Ar, Al = ctx["arms"]["r"], ctx["arms"]["l"]
    speed, along, off = [], [], []; prev = None
    for i, fr in enumerate(frames):
        pose(arm, fr)
        qr, ql = P["hand_r"].matrix.to_quaternion(), P["hand_l"].matrix.to_quaternion()
        pr = P["hand_r"].head + qr @ Ar["palm_pt"]; pl = P["hand_l"].head + ql @ Al["palm_pt"]; blade = (qr @ Ar["local"]["front"]).normalized()
        rel = P["hand_r"].head - P["pelvis"].head
        speed.append(0.0 if prev is None else (rel - prev).length * FPS / cm); prev = rel
        d = pl - pr
        if d.length / cm <= TOGETHER:
            a = d.dot(blade); along.append(a / cm); off.append((d - blade * a).length / cm)
    for pb in P: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    # (the blow: the fastest right hand after the first third, smoothed over five frames)
    sm = [sum(speed[max(0, k - 2):k + 3]) / len(speed[max(0, k - 2):k + 3]) for k in range(len(speed))]
    k = max(range(len(sm) // 4, len(sm)), key=lambda i: sm[i])
    med = lambda v: sorted(v)[len(v) // 2] if v else None
    return {"blow": round(k / FPS, 3), "blow_speed_cm_s": round(sm[k]), "left_on": round(med(along), 1) if along else None,
            "left_off": {"median": round(med(off), 1) if off else None, "most": round(max(off), 1) if off else None, "frames": len(off)},
            "swing": [round((CHOP_SWING[0] - 1) / FPS, 3), round((CHOP_SWING[1] - 1) / FPS, 3)], "length": round((len(frames) - 1) / FPS, 3)}


def make_clips(arm, scene, clips):
    out = {}
    for name, frames in clips.items():
        if not root_turned(frames): continue
        before = []
        for j in (0, len(frames) // 3): pose(arm, frames[j]); before.append(mesh_span(scene))
        out[name] = level_pelvis(arm, frames)
        after = []
        for j in (0, len(frames) // 3): pose(arm, out[name][j]); after.append(mesh_span(scene))
        for pb in arm.pose.bones: pb.matrix_basis.identity()
        print("WARRIOR2 %s: root turned, pelvis set right; her skin across (x) before %s, after %s" % (
            name, " ".join("%.2f..%.2f" % s[0] for s in before), " ".join("%.2f..%.2f" % s[0] for s in after)))
    if "Chop" in clips:
        nums = chop_numbers(arm, scene, out.get("Chop", clips["Chop"]))
        print("WARRIOR2 chop:", json.dumps(nums))
        argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
        if len(argv) > 1: os.makedirs(argv[1], exist_ok=True); json.dump(nums, open(os.path.join(argv[1], "chop.json"), "w"), indent=1)
    return out


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:]
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=argv[0]); sc = bpy.context.scene; sc.render.fps = FPS
    for o in [o for o in sc.objects if o.type == 'MESH' and not o.vertex_groups]: bpy.data.objects.remove(o, do_unlink=True)
    arm = next(o for o in sc.objects if o.type == 'ARMATURE'); ad = arm.animation_data
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
    for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
    clips = {}
    for act in list(bpy.data.actions):
        name = act.name.split(".")[0]; name = name[:1].upper() + name[1:]
        ad.action = act; ad.action_slot = act.slots[0]; fs = []
        for t in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1): sc.frame_set(t); fs.append({pb.name: pb.matrix_basis.decompose() for pb in arm.pose.bones})
        clips[name] = fs
    ad.action = None
    for pb in arm.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    make_clips(arm, sc, clips)
