"""The Warrior's shield-block stance (the user's list of 2026-11-10: "when the warrior does a shield block, she should be in a new
animation shield block stance like in this picture: E:\\temp\\shield_block.jpg"): a lunge behind the shield, her left foot well
forward with its knee bent over it, her right leg back, her hips low, her body leaning into the shield, her sword hand down by
her hip. tripo_build.py's clip maker for Warrior3 (her own rig): it adds BlockLunge (two frames of the one pose) to her clips.

Built from her own Box_03 (the block's pose until now, Tripo's boxing guard) at frame 30, its shield arm kept as it is (the shield
on her forearm faces forward there): the pelvis lowered and moved forward, both feet set by IK (two-bone chains to targets on
the floor, knees forward), the spine leant forward, the right hand brought down to her hip (IK). Previews (front, side, three
quarter) and the pose's numbers go to <out_dir>/block_preview_*.png and block.json.
Blender: tripo_build.py -- "ai models/Warrior3.glb" <out_dir> SK_JRPG_Warrior3 Warrior3 165 <this file>"""
import json, math, os, sys
import bpy
from mathutils import Matrix, Vector, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import warrior2_clips as W2

BASE_CLIP, BASE_FRAME = "Box_03", 29          # (frame 30 of the clip, its deepest guard)
# (the pose, in shares of her pelvis's rest height (her legs' length near enough); her front is -Y)
PELVIS_DOWN = 0.22           # (the hips this much lower than at rest)
PELVIS_FWD = 0.16
FRONT_FOOT = (0.17, -0.42)   # (x out to her left, y forward: the left foot)
BACK_FOOT = (-0.14, 0.42)    # (the right foot behind)
LEAN_DEG = (6.0, 4.0, 2.0)  # (a little: leant 27 degrees the shield on her forearm lay flat across her belly (868 l10p's picture))
SHIELD_HAND = (-0.08, -0.04)  # (the shield hand forward and down of where Box_03 has it, with the hips' move: y, z in shares)  # (spine_01, spine_02, spine_03 forward)
SWORD_HAND = (-0.24, -0.26, 0.98)   # (the right hand by her right hip, forward of it: x, y, z in shares)


def rot_world(arm, pb, axis, deg):
    """turn a pose bone about a world axis through its head (its children follow)"""
    h = pb.head.copy()
    R = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h)
    pb.matrix = R @ pb.matrix
    bpy.context.view_layer.update()


def turn_onto(arm, pb, pivot, v_from, v_to):
    """turn a pose bone (and its children) about a point so that one way becomes another (armature space)"""
    q = v_from.normalized().rotation_difference(v_to.normalized())
    pb.matrix = Matrix.Translation(pivot) @ q.to_matrix().to_4x4() @ Matrix.Translation(-pivot) @ pb.matrix
    bpy.context.view_layer.update()


def ik_to(arm, tip, target, pole):
    """a two-bone solve: the head of the tip bone (the foot, the hand) to a point (armature space), its parent and grandparent
    (calf and thigh, forearm and upper arm) turned onto the joint the lengths and the pole point give (Blender's IK constraint
    did not reach the pose read back in a background run: the feet stayed where they were)"""
    P = arm.pose.bones
    end = P[tip]; lower = end.parent; upper = lower.parent
    # (a twist bone between them is passed by: the joints are the bones' heads)
    while lower and "twist" in lower.name: lower = lower.parent
    upper = lower.parent
    while upper and "twist" in upper.name: upper = upper.parent
    H, K, A = upper.head.copy(), lower.head.copy(), end.head.copy()
    a, b = (K - H).length, (A - K).length
    d = min((target - H).length, (a + b) * 0.999)
    u = (target - H).normalized()
    w = (pole - H) - u * (pole - H).dot(u)
    v = w.normalized() if w.length > 1e-6 else Vector((0, -1, 0))
    ca = max(-1.0, min(1.0, (a * a + d * d - b * b) / (2 * a * d)))
    K2 = H + u * a * ca + v * a * math.sqrt(max(0.0, 1 - ca * ca))
    turn_onto(arm, upper, H, K - H, K2 - H)
    K3, A3 = lower.head.copy(), end.head.copy()
    turn_onto(arm, lower, K3, A3 - K3, (H + u * d) - K3)
    return (end.head - target).length


def frame_of(arm):
    return {pb.name: pb.matrix_basis.decompose() for pb in arm.pose.bones}


def preview(arm, out):
    sc = bpy.context.scene
    me = next(o for o in sc.objects if o.type == 'MESH' and o.vertex_groups)
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'TEXTURE'
    sc.render.resolution_x, sc.render.resolution_y = 640, 800
    cam_d = bpy.data.cameras.new("rd_cam"); cam = bpy.data.objects.new("rd_cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
    cam_d.type = 'ORTHO'; cam_d.ortho_scale = 1.3
    zs = [(me.matrix_world @ v.co).z for v in me.data.vertices]; mid = (max(zs) + min(zs)) / 2
    shots = []
    for nm, d in (("side", Vector((-1, 0, 0))), ("front", Vector((0, -1, 0))), ("three_quarter", Vector((-0.7, -0.7, 0.15)).normalized())):
        cam.location = Vector((0, 0, mid)) + d * 3.0
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out, f"block_preview_{nm}.png"); bpy.ops.render.render(write_still=True); shots.append(sc.render.filepath)
    bpy.data.objects.remove(cam)
    return shots


def make_clips(arm, scene, clips):
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = argv[1] if len(argv) > 1 else os.getcwd()
    P = arm.pose.bones; B = arm.data.bones
    base = clips[BASE_CLIP][min(BASE_FRAME, len(clips[BASE_CLIP]) - 1)]
    for pb in P: pb.matrix_basis.identity()
    W2.pose(arm, base)
    L = B["pelvis"].head_local.z          # (her legs' length near enough: the pelvis's rest height over the floor)
    # (the shield arm as Box_03 holds it: its forearm's and hand's turn in the world (the shield stands upright on it there))
    low0 = P["lowerarm_l"].matrix.to_3x3().copy(); hand0 = P["hand_l"].matrix.to_3x3().copy(); hpos0 = P["hand_l"].head.copy()
    floor = min(B["foot_l"].head_local.z, B["foot_r"].head_local.z)
    # (the hips: lower, a little forward)
    pel = P["pelvis"]
    pel.matrix = Matrix.Translation(Vector((0, -PELVIS_FWD * L, (B["pelvis"].head_local.z - PELVIS_DOWN * L) - pel.head.z))) @ pel.matrix
    bpy.context.view_layer.update()
    # (the feet: on the floor at the stance's places, the knees forward)
    res = {}
    for side, (fx, fy) in (("l", FRONT_FOOT), ("r", BACK_FOOT)):
        tgt = Vector((fx * L, fy * L, floor))
        knee = (P[f"thigh_{side}"].head + tgt) / 2 + Vector((0, -0.6 * L, 0.1 * L))
        res[f"foot_{side}_off_cm"] = round(ik_to(arm, f"foot_{side}", tgt, knee) * 165.0 / 0.9, 2)
    # (the feet flat on the floor, pointing forward: their turn in the world as at rest)
    for side in ("l", "r"):
        fb = P[f"foot_{side}"]; rest = arm.data.bones[f"foot_{side}"].matrix_local
        m = fb.matrix.copy(); fb.matrix = Matrix.Translation(m.to_translation()) @ rest.to_3x3().to_4x4()
        bpy.context.view_layer.update()
    # (the body leaning into the shield)
    for n, deg in zip(("spine_01", "spine_02", "spine_03"), LEAN_DEG):
        if n in P: rot_world(arm, P[n], Vector((1, 0, 0)), deg)
    # (which way is forward for the lean: the head must move toward -Y; else lean the other way)
    if P["head"].head.y > B["head"].head_local.y - 0.02 * L:
        for n, deg in zip(("spine_01", "spine_02", "spine_03"), LEAN_DEG):
            if n in P: rot_world(arm, P[n], Vector((1, 0, 0)), -2 * deg)
    # (the shield arm: the hand forward with her, then the forearm and hand turned back to Box_03's, so the shield stands upright)
    tgt = hpos0 + Vector((0, -PELVIS_FWD * L + SHIELD_HAND[0] * L, SHIELD_HAND[1] * L))
    res["shield_hand_off_cm"] = round(ik_to(arm, "hand_l", tgt, P["upperarm_l"].head + Vector((0.3 * L, 0.05 * L, -0.25 * L))) * 165.0 / 0.9, 2)
    la = P["lowerarm_l"]; la.matrix = Matrix.Translation(la.head) @ low0.to_4x4(); bpy.context.view_layer.update()
    hb = P["hand_l"]; hb.matrix = Matrix.Translation(hb.head) @ hand0.to_4x4(); bpy.context.view_layer.update()
    # (the sword hand down by her right hip, the elbow out and back)
    sh = Vector((SWORD_HAND[0] * L, SWORD_HAND[1] * L + P["pelvis"].head.y, P["pelvis"].head.z + 0.02 * L))
    elbow = P["upperarm_r"].head + Vector((-0.25 * L, 0.2 * L, -0.25 * L))
    res["sword_hand_off_cm"] = round(ik_to(arm, "hand_r", sh, elbow) * 165.0 / 0.9, 2)
    # (the numbers the preview is judged by, in shares of her pelvis's rest height)
    for n in ("pelvis", "foot_l", "foot_r", "hand_l", "hand_r", "head"):
        h = P[n].head; res[n] = [round(h.x / L, 3), round(h.y / L, 3), round(h.z / L, 3)]
    fr = frame_of(arm)
    try: res["previews"] = preview(arm, out)
    except Exception as e: res["preview_error"] = str(e)
    os.makedirs(out, exist_ok=True); json.dump(res, open(os.path.join(out, "block.json"), "w"), indent=1)
    print("WARRIOR3 BLOCK", json.dumps(res))
    for pb in P: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    return {"BlockLunge": [fr, fr]}
