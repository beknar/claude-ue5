"""Hair chains for a Tripo character whose hair is one with the rest of the mesh (girl-darkcaster-tripo, the Warlock): Tripo's
rig has no hair bones, and the hair was skinned to the head, neck and spine, so it moved as one stiff piece. This adds
bone chains through the hair and skins the hair to them; Unreal swings them (pipeline/unreal/820, AnimDynamics).

The hair is found per vertex by where it is and by the texture under it (the mesh and its one texture hold skin, leather,
the cape and the hair together): inside the hair's region (config "region") and not red (the cape), not bright skin, not
cool leather; the result is smoothed over the mesh's neighbours. The chains are placed in it: "back" chains side by side
down the back (the hair's points split by x), "front" locks left and right; each chain's joints are the hair's mean
position at evenly spaced heights from "root_z" down to its lowest hair. A chain is <name>_0 (its root at the scalp,
fixed to the head), <name>_1 .. _N (swung in Unreal) and <name>_end (the tip: gives the last bone its length, no
vertices). A hair vertex's weight goes to the two nearest bones of its nearest chains (blended by distance), faded in over
"fade_cm" below the chain's root so that the scalp stays on the head; what it had before keeps the rest.

    add_hair(arm, mesh, cfg, texture_path) -> report      (called by tripo_build.py with its 7th argument, a hair.json)
    blender -b -P tripo_hair.py -- built_mesh.fbx hair.json texture.png out_prefix      (preview: renders + report)

Coordinates: Blender world, centimetres, front toward -Y (as tripo_build leaves the character)."""
import bpy, bmesh, json, math, colorsys, sys, os
from mathutils import Vector


def _vertex_colours(mesh, tex_path):
    """mean texture colour (r, g, b) under each vertex, from the active UV map"""
    import numpy as np
    img = bpy.data.images.load(tex_path, check_existing=True); W, H = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(H, W, 4)
    uv = mesh.data.uv_layers.active.data; n = len(mesh.data.vertices)
    acc = np.zeros((n, 3)); cnt = np.zeros(n)
    for li, l in enumerate(mesh.data.loops):
        u, v = uv[li].uv
        acc[l.vertex_index] += px[min(H - 1, max(0, int(v * H))), min(W - 1, max(0, int(u * W))), :3]; cnt[l.vertex_index] += 1
    return acc / np.maximum(cnt, 1)[:, None]


def _hair_like(rgb):
    h, s, v = colorsys.rgb_to_hsv(*rgb)
    if s > 0.45 and (h > 0.9 or h < 0.02): return 0.0        # red: the cape, the trims
    if v > 0.42 and s > 0.2: return 0.0                      # bright skin
    if rgb[0] - rgb[2] > 0.008: return 1.0                    # warm: the hair is brown even where it is dark
    if rgb[0] - rgb[2] < -0.005: return 0.0                   # cool: the leather
    return 0.5                                                # (near black and neutral: a wave's shadow or leather; its neighbours decide)


def _in_box(p, b):
    """a group's box: |x| within x_abs, y and z within theirs; minus its 'not' boxes (same keys)"""
    def inside(q, bb):
        return (bb.get("x_abs", (0, 1e9))[0] <= abs(q.x) <= bb.get("x_abs", (0, 1e9))[1] and bb.get("y", (-1e9, 1e9))[0] <= q.y <= bb.get("y", (-1e9, 1e9))[1]
                and bb.get("z", (-1e9, 1e9))[0] <= q.z <= bb.get("z", (-1e9, 1e9))[1])
    return inside(p, b) and not any(inside(p, x) for x in b.get("not", []))


def _group_of(p, groups):
    for gi, g in enumerate(groups):
        if _in_box(p, g["box"]): return gi
    return -1


def _neighbours(mesh):
    nb = [[] for _ in mesh.data.vertices]
    for e in mesh.data.edges:
        a, b = e.vertices; nb[a].append(b); nb[b].append(a)
    return nb


def _closest_on_polyline(p, pts):
    """(distance, segment index, fraction along it)"""
    best = (1e9, 0, 0.0)
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]; ab = b - a; L2 = max(ab.length_squared, 1e-6)
        t = max(0.0, min(1.0, (p - a).dot(ab) / L2)); d = (a + ab * t - p).length
        if d < best[0]: best = (d, k, t)
    return best


def add_hair(arm, mesh, cfg, tex_path):
    mw = mesh.matrix_world; P = [mw @ v.co for v in mesh.data.vertices]
    rgb = _vertex_colours(mesh, tex_path); G = cfg["groups"]
    grp_of = [_group_of(P[i], G) for i in range(len(P))]
    h = [(_hair_like(rgb[i]) if grp_of[i] >= 0 else 0.0) for i in range(len(P))]
    nb = _neighbours(mesh)
    for _ in range(cfg.get("smooth", 3)):
        h = [(h[i] + sum(h[j] for j in nb[i])) / (1 + len(nb[i])) if nb[i] else h[i] for i in range(len(P))]
    lo, hi = cfg.get("threshold", (0.3, 0.7))
    h = [max(0.0, min(1.0, (x - lo) / (hi - lo))) * (1.0 if grp_of[i] >= 0 else 0.0) for i, x in enumerate(h)]
    hair = [i for i in range(len(P)) if h[i] > 0.0]
    # ---- the chains' joints
    chains = []
    for gi, grp in enumerate(G):
        pts = [i for i in hair if grp_of[i] == gi]
        if grp["kind"] == "back":
            xs = sorted(P[i].x for i in pts); n = grp["chains"]
            cuts = [xs[int(len(xs) * k / n)] for k in range(n)] + [xs[-1] + 1]
            bins = [[i for i in pts if cuts[k] <= P[i].x < cuts[k + 1]] for k in range(n)]
            names = [f"{grp['name']}{k + 1}" for k in range(n)]
        else:
            bins = [[i for i in pts if P[i].x > 0], [i for i in pts if P[i].x < 0]]; names = [f"{grp['name']}l", f"{grp['name']}r"]
        for nm, b in zip(names, bins):
            if len(b) < 40: continue
            zs = sorted(P[i].z for i in b); z_tip = zs[int(len(zs) * grp.get("tip_quantile", 0.04))]
            z0 = grp["root_z"]; N = grp["bones"]
            levels = [z0 - (z0 - z_tip) * k / (N + 1) for k in range(N + 2)]        # root, N joints, tip
            joints = []
            for z in levels:
                sl = [P[i] for i in b if abs(P[i].z - z) < grp.get("slice_cm", 4.0)]
                if len(sl) < 5: sl = sorted((P[i] for i in b), key=lambda q: abs(q.z - z))[:30]
                c = sum(sl, Vector()) / len(sl); c.z = z
                c.y += grp.get("inset_cm", 0.0) * (-1.0 if grp["kind"] == "back" else 1.0)        # (toward the body: inside the hair's mass)
                joints.append(c)
            chains.append({"name": nm, "group": gi, "joints": joints, "verts": b})
    # ---- the bones
    bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.data.edit_bones; inv = arm.matrix_world.inverted()
    for ch in chains:
        parent = eb[cfg["root"]]; J = [inv @ j for j in ch["joints"]]
        for k in range(len(J) - 1):
            b = eb.new(f"{ch['name']}_{k}"); b.head = J[k]; b.tail = J[k + 1]; b.parent = parent; b.use_connect = k > 0; b.use_deform = True; parent = b
        tip = eb.new(f"{ch['name']}_end"); d = (J[-1] - J[-2]).normalized()
        tip.head = J[-1]; tip.tail = J[-1] + d * 2.0; tip.parent = parent; tip.use_connect = True; tip.use_deform = False
    bpy.ops.object.mode_set(mode='OBJECT')
    # ---- the weights
    vg = {g.name: g for g in mesh.vertex_groups}
    for ch in chains:
        for k in range(len(ch["joints"]) - 1):
            n_ = f"{ch['name']}_{k}"
            if n_ not in vg: vg[n_] = mesh.vertex_groups.new(name=n_)
    gname = {g.index: g.name for g in mesh.vertex_groups}
    fade = cfg.get("fade_cm", 6.0); moved = 0; per = {c["name"]: 0 for c in chains}
    for i in hair:
        p = P[i]
        cand = sorted(((_closest_on_polyline(p, c["joints"]), c) for c in chains if c["group"] == grp_of[i]), key=lambda e: e[0][0])[:2]
        if not cand: continue
        ws = [1.0 / max(e[0][0], 1.0) ** 2 for e in cand]; tot = sum(ws)
        new = {}
        for (dist_seg, c), w in zip(cand, ws):
            d, k, t = dist_seg; nb_ = len(c["joints"]) - 1
            a = f"{c['name']}_{k}"; new[a] = new.get(a, 0.0) + (w / tot) * (1.0 - t)
            b = f"{c['name']}_{min(k + 1, nb_ - 1)}"; new[b] = new.get(b, 0.0) + (w / tot) * t
        root_z = min(c["joints"][0].z for _, c in cand)
        f = h[i] * max(0.0, min(1.0, (root_z + fade * 0.5 - p.z) / fade))
        if f <= 0.0: continue
        old = {gname[g.group]: g.weight for g in mesh.data.vertices[i].groups}
        tot_old = sum(old.values()) or 1.0
        out = {k: (1.0 - f) * w / tot_old for k, w in old.items()}
        for k, w in new.items(): out[k] = out.get(k, 0.0) + f * w
        for k, w in out.items():
            if k not in vg: vg[k] = mesh.vertex_groups.new(name=k)
            if w > 1e-4: vg[k].add([i], w, 'REPLACE')
            else: vg[k].remove([i])
        moved += 1; per[cand[0][1]["name"]] += 1
    return {"hair_vertices": len(hair), "reweighted": moved, "chains": {c["name"]: {"joints_cm": [[round(v.x, 1), round(v.y, 1), round(v.z, 1)] for v in c["joints"]], "vertices": per[c["name"]]} for c in chains}}


def _preview(argv):
    """renders: the hair's weight on its chains (colour per chain) from the back, side and front, joints as balls"""
    src, cfgp, tex, outp = argv
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=src)
    arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE'); me = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    for o in (arm, me): o.matrix_world = Matrix.Scale(100.0, 4) @ o.matrix_world
    bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); me.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    rep = add_hair(arm, me, json.load(open(cfgp)), tex)
    print("HAIR", json.dumps(rep))
    pal = [(0.95, 0.3, 0.2), (0.2, 0.8, 0.3), (0.25, 0.45, 1.0), (1.0, 0.85, 0.2), (0.9, 0.3, 0.95), (0.2, 0.9, 0.95), (1, 1, 1)]
    names = list(rep["chains"]); col = me.data.color_attributes.new("hc", 'FLOAT_COLOR', 'POINT'); gname = {g.index: g.name for g in me.vertex_groups}
    for v in me.data.vertices:
        c = Vector((0.12, 0.12, 0.14)); tot = 0.0
        for g in v.groups:
            n = gname[g.group]
            for ci, cn in enumerate(names):
                if n.startswith(cn + "_") and not n.endswith("_0"): c += Vector(pal[ci % len(pal)]) * g.weight; tot += g.weight
        col.data[v.index].color = (min(c.x, 1), min(c.y, 1), min(c.z, 1), 1.0)
    for cn, c in rep["chains"].items():
        for j in c["joints_cm"]:
            bpy.ops.mesh.primitive_uv_sphere_add(radius=1.2, location=j); s = bpy.context.active_object
            s.color = (1, 1, 1, 1)
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'VERTEX'; sc.display.shading.light = 'FLAT'
    sc.render.resolution_x = 700; sc.render.resolution_y = 900
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 90.0; cam.data.clip_end = 5000
    hd = arm.matrix_world @ arm.data.bones["head"].head_local; tgt = Vector((hd.x, hd.y, hd.z - 20))
    for nm, d in (("back", Vector((0, -1, 0))), ("side", Vector((1, 0, 0))), ("front", Vector((0, 1, 0)))):
        cam.location = tgt - d * 400; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f"{outp}_{nm}.png"; bpy.ops.render.render(write_still=True)
    print("PREVIEW DONE")


if __name__ == "__main__" and "--" in sys.argv:
    from mathutils import Matrix
    _preview(sys.argv[sys.argv.index("--") + 1:])
