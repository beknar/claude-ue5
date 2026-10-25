"""A Tripo hero's proportions changed at build time (tripo_build.py, right after it samples the GLB's own clips, so the
clips it makes and exports are made on the changed rig). Now: the arms lengthened.

The Warrior's and the Warlock's arms were about 60 % of a person's: shoulder joint to wrist 33.7 and 34.8 cm on a body
170 tall (a person: about 56), their span 0.71 of their height (a person: about 1.0); standing, their wrists hung at
their navel. With both fists on a two-handed sword's grip her hands reached no higher than the top of her head and 33 cm
out from her shoulder, so every cut folded or crossed her arms. ARM_LENGTH lengthens the upper arm and the forearm alike
(the hand keeps its size: the grip is measured on it) so the wrist hangs just below the crotch and the fingertips at
mid-thigh, as on a person (her legs are long: the hip joint at 0.58 of her height).

How: each arm bone's rest is moved, and every skin vertex moved with the bones it is weighted to (its bones' moves
blended by its weights), so the bind stays exact. A segment's move at a point is the stretch along the segment of how
far along it the point is, held to the segment (0 before its joint: chest and armpit skin weighted to the upper arm
does not move inward; the whole stretch past its end): the upper arm and its twist bone stretched from the shoulder
joint, the forearm and its twist bone carried out with the elbow and stretched from it, the hand and its fingers carried
out with the wrist, unchanged. Bones keep their way and roll.

Then the shoulders widened (SHOULDER_SPREAD): each collarbone stretched from its root by how far along it a point is,
the arm carried out with the shoulder joint; the chest stays where it is.

Usage: apply(arm_obj, meshes, tag) -> report (None when the tag has no change); lengthen_arms(arm_obj, meshes, k);
widen_shoulders(arm_obj, meshes, k)."""
import bpy
from mathutils import Vector

# (shoulder joint to wrist x this; chosen by where the hanging wrist and fingertip come to: probe_landmarks)
ARM_LENGTH = {"Fem5": 1.5, "DarkCaster": 1.4}
# (the shoulder joints' spread x this, the collarbones made longer: their joints were 23.9 / 22.6 cm apart on a body 170
# tall, 0.14 / 0.13 of the height (a woman: about 0.19), each joint inside her chest's side (its front 17 to 18 cm ahead
# of them): an arm brought forward to a two-handed grip went through her chest whichever way the elbow went (the user
# saw it). Spread so, each joint is 3 to 4 cm outside her chest's side: probe_shoulders)
SHOULDER_SPREAD = {"Fem5": 1.35, "DarkCaster": 1.4}


def _moves(B, k):
    """per bone name, the move (a function of a point, armature space) lengthening the arms by k"""
    M = {}; rep = {}
    for s in "rl":
        sh, el, wr = B[f"upperarm_{s}"].head_local.copy(), B[f"lowerarm_{s}"].head_local.copy(), B[f"hand_{s}"].head_local.copy()
        au, Lu = (el - sh).normalized(), (el - sh).length
        al, Ll = (wr - el).normalized(), (wr - el).length
        e_move = au * ((k - 1.0) * Lu); w_move = e_move + al * ((k - 1.0) * Ll)
        up = lambda p, sh=sh, au=au, Lu=Lu: au * ((k - 1.0) * min(max((p - sh).dot(au), 0.0), Lu))
        lo = lambda p, el=el, al=al, Ll=Ll, e_move=e_move: e_move + al * ((k - 1.0) * min(max((p - el).dot(al), 0.0), Ll))
        ha = lambda p, w_move=w_move: w_move
        for n in (f"upperarm_{s}", f"upperarm_twist_01_{s}"):
            if n in B: M[n] = up
        for n in (f"lowerarm_{s}", f"lowerarm_twist_01_{s}"):
            if n in B: M[n] = lo
        M[f"hand_{s}"] = ha
        for b in B[f"hand_{s}"].children_recursive: M[b.name] = ha
        rep[s] = {"shoulder_to_wrist_before": round((wr - sh).length, 5), "after": round((wr + w_move - sh).length, 5)}
    return M, rep


def _shoulder_moves(B, k):
    """per bone, the move widening the shoulders by k: the collarbone stretched from its root, the arm carried out"""
    M = {}; rep = {}
    for s in "rl":
        c0, sh = B[f"clavicle_{s}"].head_local.copy(), B[f"upperarm_{s}"].head_local.copy()
        a, Lc = (sh - c0).normalized(), (sh - c0).length
        mv = a * ((k - 1.0) * Lc)
        M[f"clavicle_{s}"] = lambda p, c0=c0, a=a, Lc=Lc: a * ((k - 1.0) * min(max((p - c0).dot(a), 0.0), Lc))
        arm_ = lambda p, mv=mv: mv
        M[f"upperarm_{s}"] = arm_
        for b in B[f"upperarm_{s}"].children_recursive: M[b.name] = arm_
        rep[s] = {"collarbone_before": round(Lc, 5), "after": round(k * Lc, 5)}
    rep["joints_before"] = round((B["upperarm_r"].head_local - B["upperarm_l"].head_local).length, 5)
    rep["joints_after"] = round((B["upperarm_r"].head_local + M["upperarm_r"](None) - B["upperarm_l"].head_local - M["upperarm_l"](None)).length, 5)
    return M, rep


def _apply_moves(arm_obj, meshes, M):
    """every skin vertex moved by its bones' moves, blended by its weights; the bones' heads and tails moved alike"""
    B = arm_obj.data.bones; inv_arm = arm_obj.matrix_world.inverted(); moved = {}
    for o in meshes:
        to_arm = inv_arm @ o.matrix_world; to_mesh = to_arm.inverted()
        names = {g.index: g.name for g in o.vertex_groups}; n_ = 0
        for v in o.data.vertices:
            ws = [(names[g.group], g.weight) for g in v.groups if g.weight > 0.0 and names.get(g.group) in B]
            tot = sum(w for _, w in ws)
            if tot <= 0.0 or not any(n in M for n, _ in ws): continue
            p = to_arm @ v.co; d = Vector((0.0, 0.0, 0.0))
            for n, w in ws:
                if n in M: d += M[n](p) * (w / tot)
            if d.length > 1e-9: v.co = to_mesh @ (p + d); n_ += 1
        o.data.update(); moved[o.name] = n_
    act = bpy.context.view_layer.objects.active
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_obj.data.edit_bones
    new = {n: (eb[n].head + f(eb[n].head), eb[n].tail + f(eb[n].tail), eb[n].roll) for n, f in M.items()}
    conn = {n: eb[n].use_connect for n in new}
    for n in new: eb[n].use_connect = False
    for n, (h, t, r) in new.items(): eb[n].head = h; eb[n].tail = t; eb[n].roll = r
    for n, c in conn.items(): eb[n].use_connect = c
    bpy.ops.object.mode_set(mode='OBJECT')
    if act is not None: bpy.context.view_layer.objects.active = act
    bpy.context.view_layer.update()
    return moved


def widen_shoulders(arm_obj, meshes, k):
    """the shoulder joints spread k times as far from her middle's collarbone roots (rest pose); returns a report"""
    M, rep = _shoulder_moves(arm_obj.data.bones, k); rep["factor"] = k
    rep["vertices_moved"] = _apply_moves(arm_obj, meshes, M)
    return rep


def lengthen_arms(arm_obj, meshes, k):
    """the upper arms and forearms of arm_obj and its skinned meshes made k times as long (rest pose); returns a report"""
    B = arm_obj.data.bones
    M, rep = _moves(B, k); rep["factor"] = k
    inv_arm = arm_obj.matrix_world.inverted()
    for o in meshes:
        to_arm = inv_arm @ o.matrix_world; to_mesh = to_arm.inverted()
        names = {g.index: g.name for g in o.vertex_groups}
        moved = 0
        for v in o.data.vertices:
            ws = [(names[g.group], g.weight) for g in v.groups if g.weight > 0.0 and names.get(g.group) in B]
            tot = sum(w for _, w in ws)
            if tot <= 0.0 or not any(n in M for n, _ in ws): continue
            p = to_arm @ v.co; d = Vector((0.0, 0.0, 0.0))
            for n, w in ws:
                if n in M: d += M[n](p) * (w / tot)
            if d.length > 1e-9: v.co = to_mesh @ (p + d); moved += 1
        o.data.update(); rep.setdefault("vertices_moved", {})[o.name] = moved
    act = bpy.context.view_layer.objects.active
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_obj.data.edit_bones
    new = {n: (eb[n].head + f(eb[n].head), eb[n].tail + f(eb[n].tail), eb[n].roll) for n, f in M.items()}
    conn = {n: eb[n].use_connect for n in new}
    for n in new: eb[n].use_connect = False
    for n, (h, t, r) in new.items(): eb[n].head = h; eb[n].tail = t; eb[n].roll = r
    for n, c in conn.items(): eb[n].use_connect = c
    bpy.ops.object.mode_set(mode='OBJECT')
    if act is not None: bpy.context.view_layer.objects.active = act
    bpy.context.view_layer.update()
    return rep


def tag_of(glb_path):
    """the tag tripo_build is given for a model in ai models/ (for probes that load the GLB themselves)"""
    import os
    return {"warrior.glb": "Fem5", "warlock.glb": "DarkCaster", "mage.glb": "Caster", "rogue.glb": "Rogue"}.get(os.path.basename(glb_path).lower(), "")


def apply(arm_obj, meshes, tag):
    """the proportions ARM_LENGTH gives the hero `tag` (None: unchanged)"""
    k = ARM_LENGTH.get(tag)
    if not k: return None
    rep = lengthen_arms(arm_obj, meshes, k)
    print("PROPORTIONS %s: arms x%.2f, shoulder joint to wrist r %.4f -> %.4f units; vertices moved %s"
          % (tag, k, rep["r"]["shoulder_to_wrist_before"], rep["r"]["after"], rep.get("vertices_moved")))
    ks = SHOULDER_SPREAD.get(tag)
    if ks:
        rep["shoulders"] = widen_shoulders(arm_obj, meshes, ks)
        print("PROPORTIONS %s: shoulders x%.2f, the joints %.4f -> %.4f units apart; vertices moved %s"
              % (tag, ks, rep["shoulders"]["joints_before"], rep["shoulders"]["joints_after"], rep["shoulders"]["vertices_moved"]))
    return rep
