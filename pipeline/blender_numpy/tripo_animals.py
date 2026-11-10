"""The Tripo farm animals and the riding horse (the user's list of 2026-11-10, docs/improvements10.txt: "replace the chickens in the
game with the chicken model in ai models/chicken.glb and animate it", the same for the riding horse, the goats, the rabbits and
the pigs; the cow's model was not given: the Blender cow stays). Each Tripo model's mesh and texture are kept; its own rig is not
used (the pig's has 7 bones and one leg; none has clips): the skeleton of farm_animals.py's animal of that kind is fitted to the
mesh, the mesh skinned to it here, and farm_animals.py's clips made on it (its rig, IK, gaits and measures, imported).

Each animal:
  Mesh      the glb's largest mesh (Tripo leaves a 42-vertex icosphere beside it), its texture and UVs as they are; turned to face
            +X (the head's bones' side of the body), scaled to the height of farm_animals.py's animal of the kind, standing on z 0
            with its feet's middle on the spec's (cm, scene unit scale 0.01, as farm_animals.py).
  Skeleton  farm_animals.py's bones of the kind (the same names: the game's clips and the horse's saddle bone go by them) mapped
            from the spec's body box onto the mesh's, then fitted: each leg's joints below the belly moved to the middle of the
            mesh's leg at their height (the feet found as clusters of the lowest vertices), the neck's and head's joints to the
            middle of the mesh across them, the horse's saddle bone onto the top of its back.
  Skin      by distance to the bones (the four nearest within 1.6 times the nearest; ears, jaw and tail only where they are the
            nearest), smoothed twice along the mesh on welded positions (the glb's vertices are split at the texture's seams:
            smoothed apart, the seams would open), the hooves / feet held rigid to their planted bone as farm_animals.py does.
  Clips     farm_animals.py's: Idle, Graze (not the horse's), Walk, and the horse's Run (its gallop); measured on the skinned mesh
            the same way (soles, slide, walk speed, stretch, seam).
Writes into out_dir: SK_Tripo_<Animal>.fbx (mesh, armature, takes; the texture embedded), T_Tripo_<Animal>.png, tripo_animals.json
(as farm_animals.json: size, clips, walk speeds, weights) and preview/<animal>_sheet.png (12 panels: side, front, three-quarter,
from behind, Idle 1.2 s and 3.5 s, Graze or Run twice, Walk 0, 1/4, 1/2, 3/4).
Blender: -b -P tripo_animals.py -- out_dir [only=chicken,pig] [nopreview]"""
import json, math, os, sys
import bpy, bmesh
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import farm_animals as FA                                     # (its main() runs only as Blender's own script)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0]) if argv else os.path.abspath("tripo_animals")
OPTS = argv[1:]
ONLY = next((a.split("=", 1)[1].split(",") for a in OPTS if a.startswith("only=")), None)
PREVIEW = "nopreview" not in OPTS
PREV = os.path.join(OUT, "preview")
FA.OUT = OUT
GLB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ai models")
KINDS = {"chicken": "chicken.glb", "goat": "goat.glb", "pig": "pig.glb", "rabbit": "rabbit.glb", "horse": "ridinghorse.glb"}
ACCESSORY = ("ear_", "jaw", "tail_")                           # (bones that take only what they are the nearest to)
TAIL_FIT = ("horse",)
FRONT_BY_TOP = ("horse",)
BEND_KEEP = {"horse": 0.5}                                     # (its knees and hocks this far back toward the spec's bend: a leg fitted
                                                               # straight leaves the IK no stride; the Tripo horse stands straight-legged)
def RDTweak(key, A):
    """the spec's clip settings changed for the Tripo mesh, where its skin creased (measured in the sheets): the rabbit's round haunch
    folded at the back as its spine tipped 14 degrees to graze; the horse's flank creased under a hind swing folded 55 degrees"""
    if key == "rabbit": A["graze"]["pre"] = {"spine_01": 7}
    if key == "horse":
        A["run"]["gait"]["rear"].update(fold=35, tilt=35, height=11); A["run"]["gait"]["front"].update(fold=48, tilt=42, height=14)                                   # (a tail of its own in the mesh: found and its bones laid along it)
NO_SKIN = ("root", "saddle")


def log(*a): print("TRIPO", *a, flush=True)


def seg_d(P, h, t):
    return FA.seg_dist(P, np.array(h, float), np.array(t, float))


# ---------------------------------------------------------------- the glb's mesh, turned, scaled and set down
def load_glb(path):
    bpy.ops.import_scene.gltf(filepath=path)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    ob = max(meshes, key=lambda o: len(o.data.vertices))
    arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    heads = []
    if arm is not None:
        for b in arm.data.bones:
            if "Head" in b.name: heads.append(arm.matrix_world @ b.head_local)
    # (out of the rig: its world place applied to the mesh, the glb's armature and the icosphere gone)
    mw = ob.matrix_world.copy(); ob.parent = None; ob.matrix_world = mw
    for md in list(ob.modifiers): ob.modifiers.remove(md)
    ob.vertex_groups.clear()
    for o in meshes:
        if o != ob: bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if arm is not None: bpy.data.objects.remove(arm)
    for o in list(bpy.data.objects):
        if o.type == 'EMPTY': bpy.data.objects.remove(o)
    return ob, heads


def verts(ob):
    a = np.empty(len(ob.data.vertices) * 3); ob.data.vertices.foreach_get("co", a); return a.reshape(-1, 3)


def set_verts(ob, V):
    ob.data.vertices.foreach_set("co", V.astype(np.float64).ravel()); ob.data.update()


def place(ob, heads, S, spec_lo, spec_hi, spec_feet_xy):
    V = verts(ob)
    c = V.mean(0); zr = V[:, 2].max() - V[:, 2].min()
    # (its long way: the body's main axis over the legs (a turn of Tripo's head bones misled: the pig came out 47 degrees round),
    # snapped to the nearest quarter turn; the head's bones say which end is the front)
    body = V[V[:, 2] > V[:, 2].min() + 0.35 * zr][:, :2]; body = body - body.mean(0)
    ev, evec = np.linalg.eigh(np.cov(body.T)); ax = evec[:, np.argmax(ev)]
    th = round(math.atan2(ax[1], ax[0]) / (math.pi / 2)) * (math.pi / 2); f = np.array([math.cos(th), math.sin(th)])
    h = np.mean(np.array([tuple(x) for x in heads]), 0) if heads else V[V[:, 2] > np.percentile(V[:, 2], 80)].mean(0)
    # (the riding horse's head bones stand at its tail: its front is the end of its highest point, its head and ears)
    if S.key in FRONT_BY_TOP: h = V[np.argmax(V[:, 2])]
    if (h[0] - c[0]) * f[0] + (h[1] - c[1]) * f[1] < 0: f = -f
    a = -math.atan2(f[1], f[0])
    R = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    V = (V - c) @ R.T
    s = (spec_hi[2] - spec_lo[2]) / max(V[:, 2].max() - V[:, 2].min(), 1e-6)
    V *= s; V[:, 2] -= V[:, 2].min()
    # (its feet's middle on the spec's: the lowest vertices' middle)
    low = V[V[:, 2] < 0.05 * V[:, 2].max()]
    V[:, 0] += spec_feet_xy[0] - low[:, 0].mean(); V[:, 1] += spec_feet_xy[1] - low[:, 1].mean()
    set_verts(ob, V)
    return dict(turn_deg=round(math.degrees(a), 1), scale=round(float(s), 4))


# ---------------------------------------------------------------- the spec's bones fitted to the mesh
def kmeans(P, C, it=20):
    C = C.copy()
    for _ in range(it):
        lab = np.argmin(((P[:, None, :] - C[None, :, :]) ** 2).sum(2), 1)
        for k in range(len(C)):
            if (lab == k).any(): C[k] = P[lab == k].mean(0)
    return C, lab


def fit_bones(S, V, spec_lo, spec_hi):
    lo, hi = V.min(0), V.max(0); H = hi[2]
    k = (hi - lo) / np.maximum(spec_hi - spec_lo, 1e-6); k[2] = 1.0
    def M(p): return lo + (np.array(p, float) - spec_lo) * k
    B = {n: [par, Vector(M(h)), Vector(M(t))] for n, par, h, t in S.bones}
    # (the root stays on the ground at the origin, as the spec's)
    for n in B:
        if B[n][0] is None: B[n][1] = Vector((0, 0, 0)); B[n][2] = Vector((0, 0, max(15.0, B[n][2].z)))
    report = {"axis_scale": [round(float(x), 3) for x in k]}
    # the feet: clusters of the lowest vertices, one a leg, seeded at the mapped feet
    feet0 = np.array([[B[lg["bones"][3]][2].x, B[lg["bones"][3]][2].y] for lg in S.legs])
    low = V[V[:, 2] < 0.06 * H][:, :2]
    C, lab = kmeans(low, feet0)
    report["feet"] = {lg["id"]: [round(float(C[i, 0]), 1), round(float(C[i, 1]), 1), int((lab == i).sum())] for i, lg in enumerate(S.legs)}
    cx = 0.5 * (lo[0] + hi[0])
    for i, lg in enumerate(S.legs):
        chain = [b for b in lg["bones"] if b]
        hip = B[chain[0]][1].copy()
        d = Vector((C[i, 0] - feet0[i, 0], C[i, 1] - feet0[i, 1], 0.0))
        pts = [B[b][1] for b in chain] + [B[chain[-1]][2]]
        for p in pts[1:]:
            w = min(1.0, max(0.0, 1.0 - p.z / max(hip.z, 1e-3)))
            p.x += d.x * w; p.y += d.y * w
        # (the joints below the belly onto the middle of the mesh's leg at their height)
        side = 1.0 if lg["id"].endswith("_l") else -1.0
        front = C[i, 0] > cx if len(S.legs) > 2 else None
        for p in pts[1:]:
            if p.z > 0.55 * hip.z: continue
            band = max(1.0, 0.03 * H); r = 0.16 * H
            sel = (np.abs(V[:, 2] - p.z) < band) & (np.hypot(V[:, 0] - p.x, V[:, 1] - p.y) < r) & (V[:, 1] * side > -0.02 * H)
            if front is not None: sel &= (V[:, 0] > cx) == front
            if sel.sum() >= 6:
                m = V[sel].mean(0); p.x, p.y = float(m[0]), float(m[1])
        pts[-1].z = 0.0
        kb = BEND_KEEP.get(S.key, 0.0)
        if kb > 0:
            sp_pts = [Vector(M(next(x for x in S.bones if x[0] == b)[2])) for b in chain]
            for j in range(1, len(pts) - 1):
                # (the spec's joint offset from its own hip-to-foot line, put back on the fitted line at that share)
                a0, a1 = sp_pts[0], Vector(M(next(x for x in S.bones if x[0] == chain[-1])[3]))
                t_ = (sp_pts[j] - a0).dot(a1 - a0) / max((a1 - a0).length_squared, 1e-6)
                off = sp_pts[j] - (a0 + (a1 - a0) * t_)
                f0, f1 = pts[0], pts[-1]; base = f0 + (f1 - f0) * t_
                q = base + off
                pts[j].x += (q.x - pts[j].x) * kb; pts[j].z += (q.z - pts[j].z) * kb
        for j, b in enumerate(chain): B[b][1] = pts[j]; B[b][2] = pts[j + 1]
    # (the neck's and head's joints to the middle of the mesh across them: a slab of the mesh at each joint's x)
    for n in ("neck_01", "neck_02", "head"):
        if n not in B: continue
        for p in (B[n][1], B[n][2]):
            sel = (np.abs(V[:, 0] - p.x) < max(1.0, 0.025 * (hi[0] - lo[0]))) & (V[:, 2] > 0.45 * H) & (np.hypot(V[:, 1] - p.y, V[:, 2] - p.z) < 0.22 * H)
            if sel.sum() >= 6:
                m = V[sel].mean(0); p.y, p.z = float(0.5 * (lo[1] + hi[1])), float(0.5 * (m[2] + p.z))          # (on the body's middle line, as the spine)
    # (the tail: the mesh behind the rear legs' hips and over a fifth of the height, its bones laid along it from its root by
    # distance (the horse's hangs a metre down: as the spec's bones were mapped, the thighs took it and the gallop smeared it))
    tails = [b for b, _p, _h, _t in S.bones if b.startswith("tail_")]
    if S.key in TAIL_FIT and tails:
        rear = [lg for lg in S.legs if lg["kind"] in ("rear", "hind")]
        xh = float(np.mean([B[lg["bones"][0]][1].x for lg in rear])) if rear else lo[0]
        cand = (V[:, 0] < xh - 0.05 * (hi[0] - lo[0])) & (V[:, 2] > 0.2 * H)
        log(S.name, 'tail candidates', int(cand.sum()), 'behind x', round(xh - 0.05 * (hi[0] - lo[0]), 1), 'mesh x from', round(float(lo[0]), 1))
        if cand.sum() >= 80:
            P = V[cand]; root = np.array(tuple(B[tails[0]][1]))
            # (its root: the candidates' point nearest the spec's, moved onto the body's middle line)
            rp = P[np.argmin(np.linalg.norm(P - root, axis=1))].copy(); rp[1] = 0.5 * (lo[1] + hi[1])
            d = np.linalg.norm(P - rp, axis=1); qs = np.quantile(d, np.linspace(0, 1, len(tails) + 1))
            pts = [Vector(tuple(rp))]
            for k_ in range(1, len(tails) + 1):
                band = (d >= qs[k_ - 1] + 0.75 * (qs[k_] - qs[k_ - 1])) & (d <= qs[k_] + 1e-6)
                m = P[band].mean(0) if band.any() else P[np.argmax(d)]
                pts.append(Vector(tuple(m)))
            for k_, b in enumerate(tails): B[b][1] = pts[k_]; B[b][2] = pts[k_ + 1]
            report["tail"] = {"vertices": int(cand.sum()), "root": [round(x, 1) for x in rp], "end": [round(x, 1) for x in pts[-1]]}
            S.tail_mask = cand
    # chain joints shared: a bone's head at its parent's tail where they were one point in the spec
    sp = {n: (h, t) for n, _p, h, t in S.bones}
    for n, par, h, t in S.bones:
        if par and (Vector(h) - Vector(sp[par][1])).length < 1e-3: B[n][1] = B[par][2].copy()
    if "saddle" in B:                                              # (the horse's seat: the top of its back there)
        p = B["saddle"][1]
        sel = np.hypot(V[:, 0] - p.x, V[:, 1]) < 0.06 * H
        if sel.any():
            top = float(V[sel, 2].max()); B["saddle"][1] = Vector((p.x, 0, top)); B["saddle"][2] = Vector((p.x, 0, top + 12))
            report["saddle_top_cm"] = round(top, 1)
    S.bones = [(n, B[n][0], B[n][1], B[n][2]) for n, _p, _h, _t in S.bones]
    return report


# ---------------------------------------------------------------- the skin
def skin(S, ob, V):
    names = [b[0] for b in S.bones]; nb = len(names)
    me = ob.data; me.calc_loop_triangles()
    T = np.array([tuple(t.vertices) for t in me.loop_triangles], dtype=np.int64)
    D = np.full((len(V), nb), 1e9)
    for j, (n, _p, h, t) in enumerate(S.bones):
        if n in NO_SKIN: continue
        D[:, j] = seg_d(V, h, t)
    dmin = D.min(1); near = D.argmin(1)
    W = np.where(D < 1.6 * dmin[:, None] + 0.5, 1.0 / (D + 0.5) ** 4, 0.0)
    for j, n in enumerate(names):
        if n.startswith(ACCESSORY): W[near != j, j] = 0.0
    # (a leg's lower bones only below their own top: the belly's skin is not a knee's; its upper bone nothing over its hip (the
    # rabbit's haunch on its thighs caved in as its body tipped forward to graze))
    Hh = V[:, 2].max()
    for lg in S.legs:
        for b in [x for x in lg["bones"] if x]:
            j = names.index(b); _n, _p, h, t = next(x for x in S.bones if x[0] == b)
            top = max(h.z, t.z) if b != lg["bones"][0] else h.z
            W[V[:, 2] > top + 0.04 * Hh, j] = 0.0
    # (the tail's vertices on its own bones alone)
    tm = getattr(S, "tail_mask", None)
    if tm is not None:
        tj = [names.index(n) for n in names if n.startswith("tail_")]
        Dt = D[np.ix_(tm, tj)]; Wt = 1.0 / (Dt + 0.5) ** 4
        W[tm] = 0.0; W[np.ix_(tm, tj)] = Wt
    W[W.sum(1) <= 0, :] = 0.0
    for i in np.nonzero(W.sum(1) <= 0)[0]: W[i, near[i]] = 1.0
    W /= W.sum(1)[:, None]
    # smoothed twice along the edges of the welded mesh (the glb's vertices are split at the texture's seams)
    key = np.round(V, 3); uq, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
    Wu = np.zeros((len(uq), nb)); np.add.at(Wu, inv, W); Wu /= np.bincount(inv, minlength=len(uq))[:, None]
    e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]); e = inv[e]; e = e[e[:, 0] != e[:, 1]]
    for _ in range(2):
        acc = np.zeros_like(Wu); cnt = np.zeros(len(uq))
        np.add.at(acc, e[:, 0], Wu[e[:, 1]]); np.add.at(cnt, e[:, 0], 1)
        np.add.at(acc, e[:, 1], Wu[e[:, 0]]); np.add.at(cnt, e[:, 1], 1)
        Wu = 0.5 * Wu + 0.5 * acc / np.maximum(cnt, 1)[:, None]
    W = Wu[inv]
    # the planted bones hold their hoof / foot zone alone (farm_animals.py's rule, at the spec's sizes)
    if S.rigid[0] > 0:
        for lg in S.legs:
            pl = lg["bones"][3]; j = names.index(pl); h, t = S.bone_seg(pl)
            nr = (V[:, 2] < S.rigid[0]) & (seg_d(V, h, t) < S.rigid[1] * 1.5)
            W[nr] = 0.0; W[nr, j] = 1.0
    idx = np.argsort(-W, axis=1)
    keep = np.zeros_like(W, dtype=bool); np.put_along_axis(keep, idx[:, :4], True, axis=1)
    W = np.where(keep & (W >= 0.01), W, 0.0); W /= W.sum(1)[:, None]
    for n in names: ob.vertex_groups.new(name=n)
    for j, n in enumerate(names):
        vg = ob.vertex_groups[n]; ix = np.nonzero(W[:, j] > 0)[0]
        for i in ix: vg.add([int(i)], float(W[i, j]), 'REPLACE')
    return dict(V=V, T=T, W=W, names=names, tags=None, part=None)


# ---------------------------------------------------------------- pictures and export
def setup_render(sc):
    cam = FA.setup_render(sc)
    sc.display.shading.color_type = 'TEXTURE'
    return cam


def previews(S, arm, ob, G, clips, cam, sc):
    os.makedirs(os.path.join(PREV, "panels"), exist_ok=True)
    V = G["V"]; lo, hi = V.min(0), V.max(0); c = Vector(((lo + hi) / 2).tolist()); ext = float(max(hi[0] - lo[0], hi[2] - lo[2]))
    dist = ext * 2.6; shots = []
    def go(tag, clip, fi, ang, elev):
        FA.set_basis(arm, clips[clip][fi])
        p = os.path.join(PREV, "panels", f"{S.name.lower()}_{len(shots):02d}_{tag}.png")
        FA.shoot(sc, cam, p, c, ang, elev, dist); shots.append(p)
    go("side", "Idle", 0, 0, 6); go("front", "Idle", 0, 90, 8); go("q", "Idle", 0, 40, 18); go("qback", "Idle", 0, 150, 18)
    go("idle_l", "Idle", int(1.2 * FA.FPS), 40, 18); go("idle_r", "Idle", int(3.5 * FA.FPS), 40, 18)
    if "Graze" in clips: go("graze0", "Graze", 0, 0, 6); go("graze", "Graze", int(1.4 * FA.FPS), 40, 18)
    else:
        nr = len(clips["Run"]) - 1; go("run0", "Run", nr // 3, 0, 4); go("run1", "Run", 2 * nr // 3, 0, 4)
    n = len(clips["Walk"]) - 1
    go("walk0", "Walk", 0, 0, 4); go("walk1", "Walk", n // 4, 0, 4); go("walk2", "Walk", n // 2, 0, 4); go("walk3", "Walk", 3 * n // 4, 40, 18)
    FA.sheet(shots, 4, os.path.join(PREV, f"{S.name.lower()}_sheet.png"))
    FA.set_basis(arm, clips["Idle"][0])


def export(S, arm, ob, clips, sc):
    old = arm.name; arm.name = "Armature"
    for pb in arm.pose.bones: pb.matrix_basis.identity()
    acts = [FA.key_action(arm, n, f) for n, f in clips.items()]
    for pb in arm.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    ob.name = "SK_Tripo_" + S.name; ob.data.name = ob.name
    for o in sc.objects: o.select_set(False)
    arm.select_set(True); ob.select_set(True); bpy.context.view_layer.objects.active = arm
    fn = os.path.join(OUT, ob.name + ".fbx")
    bpy.ops.export_scene.fbx(filepath=fn, use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                             bake_anim=True, bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False,
                             bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_NONE', use_armature_deform_only=False, mesh_smooth_type='FACE',
                             use_tspace=False, path_mode='COPY', embed_textures=True)
    for a in acts: bpy.data.actions.remove(a)
    arm.name = old
    # (its texture beside it too)
    tex = None
    for m in ob.data.materials:
        if m and m.node_tree:
            for n in m.node_tree.nodes:
                if n.type == 'TEX_IMAGE' and n.image is not None: tex = n.image; break
        if tex: break
    tfn = None
    if tex is not None:
        # (the glb's image is packed: its pixels into an image of its own, saved)
        tfn = os.path.join(OUT, f"T_Tripo_{S.name}.png"); w, h = tex.size
        im = bpy.data.images.new("T_Tripo_" + S.name, w, h, alpha=True); im.pixels.foreach_set(np.array(tex.pixels[:], np.float32))
        im.filepath_raw = tfn; im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)
    log(S.name, "exported", fn, os.path.getsize(fn), "bytes; texture", tfn)
    return os.path.basename(fn), (os.path.basename(tfn) if tfn else None)


# ---------------------------------------------------------------- the run
def main():
    os.makedirs(OUT, exist_ok=True); os.makedirs(PREV, exist_ok=True)
    report = {"fps": FA.FPS, "units": "cm", "faces": "+X"}
    for key, glb in KINDS.items():
        if ONLY and key not in ONLY: continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        sc = bpy.context.scene
        sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 0.01
        sc.render.fps = FA.FPS; sc.render.fps_base = 1.0
        S = FA.ANIMALS[key](); S.key = key; S.tail_mask = None
        RDTweak(key, S.anim)
        # (the spec's animal as farm_animals.py built it: its box from its record (the metaball body alone leaves out the lofted
        # parts: the chicken's legs, the rabbit's ears, the horns; scaled to it the Tripo chicken stood 32 cm with straight legs and
        # no stride), and its feet's middle)
        SA_ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "brokenspire")
        rec0 = json.load(open(os.path.join(SA_, "horse" if key == "horse" else "farm_animals", "farm_animals.json"), encoding="utf-8"))[S.name]["size_cm"]
        spec_lo, spec_hi = np.array(rec0["min"], float), np.array(rec0["max"], float)
        feet = np.array([[S.bone_seg(lg["bones"][3])[1].x, S.bone_seg(lg["bones"][3])[1].y] for lg in S.legs]).mean(0)
        ob, heads = load_glb(os.path.abspath(os.path.join(GLB, glb)))
        pl = place(ob, heads, S, spec_lo, spec_hi, feet)
        V = verts(ob)
        fit = fit_bones(S, V, spec_lo, spec_hi)
        arm = FA.build_armature(S, sc)
        G = skin(S, ob, V)
        log(S.name, "placed", json.dumps(pl), "fit", json.dumps(fit))
        for lg in S.legs:
            j = G["names"].index(lg["bones"][3]); h, t = S.bone_seg(lg["bones"][3])
            log(S.name, "foot", lg["id"], "bone", [round(x, 1) for x in h], [round(x, 1) for x in t], "held >0.5:", int((G["W"][:, j] > 0.5).sum()), "lowest z near:", round(float(V[seg_d(V, h, t) < 15, 2].min()) if (seg_d(V, h, t) < 15).any() else -1, 1))
        ob.parent = arm; md = ob.modifiers.new("Armature", 'ARMATURE'); md.object = arm
        me = ob.data
        for p in me.polygons: p.use_smooth = True
        rig = FA.Rig(arm, S)
        bi = {n: i for i, n in enumerate(G["names"])}
        # (the mouth's points: those its head and jaw hold most of (farm_animals.py's 90 % found none on the rabbit, its head shared
        # with its ears and neck: its graze was never solved), else the nearest to the head's end)
        rig.mouth_pts = {b: G["V"][G["W"][:, bi[b]] >= 0.6] for b in ("head", "jaw") if b in bi}
        if sum(len(v) for v in rig.mouth_pts.values()) < 20:
            h_, t_ = S.bone_seg("head"); dd = np.linalg.norm(G["V"] - np.array(tuple(t_)), axis=1)
            rig.mouth_pts = {"head": G["V"][np.argsort(dd)[:200]]}
        T = rig.solve(FA.empty_pose()); rest_err = max((T[n][1] - rig.h0[n]).length for n in T)
        clips, cinfo = FA.make_clips(rig, S)
        meas = FA.measure(S, rig, arm, ob, G, clips)
        lo, hi = V.min(0), V.max(0)
        backb = [bi[b] for b in ("pelvis", "spine_01", "spine_02") if b in bi]
        back = V[G["W"][:, backb].sum(1) > 0.5]
        rec = {"glb": glb, "placed": pl, "fit": fit,
               "size_cm": {"length_x": round(float(hi[0] - lo[0]), 1), "width_y": round(float(hi[1] - lo[1]), 1), "height_z": round(float(hi[2] - lo[2]), 1),
                           "min": [round(float(x), 1) for x in lo], "max": [round(float(x), 1) for x in hi],
                           "back_height": round(float(back[:, 2].max()), 1) if len(back) else None},
               "triangles": int(len(G["T"])), "vertices": int(len(V)), "bones": G["names"],
               "legs": {lg["id"]: [b for b in lg["bones"] if b] for lg in S.legs},
               "rest_pose_rebuilt_err_cm": round(rest_err, 5), "weights": FA.weight_check(S, G),
               "clips": {k: {**cinfo[k], **meas[k]} for k in clips}}
        rec["walk_speed_cm_s"] = meas["Walk"]["walk_speed_cm_s"]; rec["walk_cycle_s"] = S.anim["walk"]["T"]
        if "Run" in meas: rec["run_speed_cm_s"] = meas["Run"]["walk_speed_cm_s"]; rec["run_cycle_s"] = S.anim["run"]["T"]
        log(S.name, json.dumps({k: rec[k] for k in ("placed", "fit", "size_cm", "triangles", "weights", "walk_speed_cm_s")}))
        for k in clips: log(S.name, k, json.dumps(rec["clips"][k])[:900])
        if PREVIEW:
            cam = setup_render(sc); previews(S, arm, ob, G, clips, cam, sc)
        rec["fbx"], rec["texture"] = export(S, arm, ob, clips, sc)
        report[S.name] = rec
        json.dump(report, open(os.path.join(OUT, "tripo_animals.json"), "w"), indent=1)
    log("DONE", os.path.join(OUT, "tripo_animals.json"))


main()
