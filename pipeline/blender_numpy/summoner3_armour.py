"""The five armour sets of random_dungeonmagic_level5 refitted to Summoner3 (Blender; 849 exported the pieces and her mesh).
Each set's pieces are skinned to the UE4 mannequin's skeleton in their own character's bind pose (a big knight, an orc, a
bear-man); she has the same bone names on other proportions. Per piece, per vertex, per bone it is skinned to:
  - the bone's frame on each rig: its head, its direction (to the child that sets it: the next spine bone, the next joint
    of a limb, the middle finger; leaves and twist bones take their parent's), its turn about it fixed by the way the
    rig faces (from its feet; up for the feet themselves);
  - the vertex in the source bone's frame, stretched along the bone by the ratio of the two bones' lengths, and scaled
    across it so that the armour sits on her: around each bone her skin's distance from the bone is read from her mesh
    (in 24 directions round it, 3 cm slices along it), and the armour's own (inner) layer is brought to 6 mm off it -
    for each quarter round the bone (front, back, left, right) the scale that puts 90 % of its vertices at least that far
    out, blended between the quarters; then placed in her bone's frame;
  - the bones' results blended by the vertex's weights (linear blend skinning with a fit per bone).
What is left inside her skin (the scale fits most, not all) is pushed out along her skin's normal to 3 mm. Each set's
pieces are joined into one mesh (their materials kept by name), skinned with the pieces' own weights to her skeleton in
her rest pose, and written as armour_fit/<set>.fbx with her armature; armour_fit/fit.json says per set how many vertices
were pushed out and how far, and per bone the scales; check renders armour_fit/<set>_{front,side,back}.png.
Another hero (the heroes share her bone names; --pct: the percentile of her skin's distance taken, 95): --hero <mesh name> (Fem5, DarkCaster, Rogue ...) takes armour_src/
SK_JRPG_<name>.fbx (849 heroes) and writes armour_fit/<name>/<set>.fbx, its renders and fit.json there.
A piece's FBX carries only the bones that piece uses (MysticDungeon's arm piece has no feet, its torso no calves): each
set's source rig is all its pieces' bones together (one character's bind pose), and the way it faces comes from the feet,
else the clavicles, else the thighs. Pieces marked skeleton "ue5" in armour.json may use UE5 mannequin bones the heroes
lack (spine_04, spine_05, neck_02, the metacarpals): their weights go to the UE4 bone they lie in (REMAP) before the fit.
fit.json keeps the sets fitted in earlier runs.
    blender -b -P summoner3_armour.py -- <SourceArt/summoner3> [--hero <name>] [--pct N] [set key ...]"""
import bpy, sys, os, json, math, numpy as np, mathutils
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index("--") + 1:]
SA = argv[0]; rest = argv[1:]; HERO = "Summoner3"
if "--hero" in rest: k = rest.index("--hero"); HERO = rest[k + 1]; rest = rest[:k] + rest[k + 2:]
# (how far out her skin is round a bone: this percentile of its vertices' distance; straps and holsters on a hero's thigh
# made 95 balloon the bear warrior's trousers on the Warrior)
PCT = 95.0
if "--pct" in rest: k = rest.index("--pct"); PCT = float(rest[k + 1]); rest = rest[:k] + rest[k + 2:]
# (the share of a bone's armour vertices the scale puts outside her skin, 90; on the legs inner straps, belts and pouch
# backs near the bone pushed whole trousers out at 90 (the orc raider's, the crocodile warrior's, the epic plate's): --legs 60
# for the hips, thighs and calves, the rest pushed out to her skin afterwards. 60 on the torso let her chest through a
# breastplate)
NEED = 90.0; NEED_LEGS = 90.0
if "--legs" in rest: k = rest.index("--legs"); NEED_LEGS = float(rest[k + 1]); rest = rest[:k] + rest[k + 2:]
LEGS = ("pelvis", "thigh_", "calf_")
ONLY = set(rest)
J = json.load(open(os.path.join(SA, "armour.json"), encoding="utf-8"))
SRC = os.path.join(SA, "armour_src"); OUT = os.path.join(SA, "armour_fit", *([] if HERO == "Summoner3" else [HERO])); os.makedirs(OUT, exist_ok=True)
PREFIX = "SK_S3_" if HERO == "Summoner3" else f"SK_{HERO}_"
GAP, PUSH = 0.006, 0.003
SIDES = ("l", "r"); FING = ("thumb", "index", "middle", "ring", "pinky")
AIM = {"pelvis": "spine_01", "spine_01": "spine_02", "spine_02": "spine_03", "spine_03": "neck_01", "neck_01": "head"}
for s in SIDES:
    AIM.update({f"clavicle_{s}": f"upperarm_{s}", f"upperarm_{s}": f"lowerarm_{s}", f"lowerarm_{s}": f"hand_{s}", f"hand_{s}": f"middle_01_{s}",
                f"thigh_{s}": f"calf_{s}", f"calf_{s}": f"foot_{s}", f"foot_{s}": f"ball_{s}"})
    for f in FING: AIM.update({f"{f}_01_{s}": f"{f}_02_{s}", f"{f}_02_{s}": f"{f}_03_{s}"})
# (bones that lie along another: they take its frame and its fit)
ALONG = {}
for s in SIDES:
    ALONG.update({f"upperarm_twist_01_{s}": f"upperarm_{s}", f"lowerarm_twist_01_{s}": f"lowerarm_{s}", f"thigh_twist_01_{s}": f"thigh_{s}",
                  f"calf_twist_01_{s}": f"calf_{s}", f"ball_{s}": f"foot_{s}"})
    for f in FING: ALONG[f"{f}_03_{s}"] = f"{f}_02_{s}"


# (the UE5 mannequin's bones the UE4 one lacks -> the bone they lie in)
REMAP = {"spine_04": "spine_03", "spine_05": "spine_03", "neck_02": "neck_01"}
for s in SIDES:
    for f in ("index", "middle", "ring", "pinky"): REMAP[f"{f}_metacarpal_{s}"] = f"hand_{s}"
    REMAP.update({f"upperarm_twist_02_{s}": f"upperarm_twist_01_{s}", f"lowerarm_twist_02_{s}": f"lowerarm_twist_01_{s}",
                  f"thigh_twist_02_{s}": f"thigh_twist_01_{s}", f"calf_twist_02_{s}": f"calf_twist_01_{s}"})


def remap_groups(me, known):
    """a UE5 piece's weights on bones she lacks moved to the bone they lie in (REMAP; a bone neither hers nor in REMAP: its
    nearest ancestor of hers is not known here, so it is reported)"""
    moved, unknown = 0, set()
    for g in list(me.vertex_groups):
        if g.name in known: continue
        t = REMAP.get(g.name)
        if t is None: unknown.add(g.name); continue
        tg = me.vertex_groups.get(t) or me.vertex_groups.new(name=t)
        for v in me.data.vertices:
            for e in v.groups:
                if e.group == g.index and e.weight > 0: tg.add([v.index], e.weight, "ADD"); moved += 1
        me.vertex_groups.remove(g)
    return moved, unknown


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def imp_fbx(path):
    before = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    return next(o for o in new if o.type == "ARMATURE"), [o for o in new if o.type == "MESH"]


def facing(head):
    """the way a rig faces (level): from its feet, else its clavicles or thighs (left to right, turned a quarter about up)"""
    if all(("ball_" + s) in head and ("foot_" + s) in head for s in SIDES):
        f = sum((head["ball_" + s] - head["foot_" + s] for s in SIDES))
    else:
        pair = next(p for p in (("clavicle_l", "clavicle_r"), ("upperarm_l", "upperarm_r"), ("thigh_l", "thigh_r")) if p[0] in head and p[1] in head)
        r = head[pair[1]] - head[pair[0]]; f = np.cross(np.array([0, 0, 1.0]), r)
    f = np.array(f, float); f[2] = 0
    return f / np.linalg.norm(f)


class Rig:
    def __init__(self, arm, extra=None):
        self.arm = arm; mw = arm.matrix_world
        self.head = {b.name: np.array(mw @ b.head_local) for b in arm.data.bones}
        self.parent = {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}
        for n, (h, p) in (extra or {}).items():
            if n not in self.head: self.head[n] = h; self.parent[n] = p
        self.front = facing(self.head)
        self.frames = {}
        for n in self.head: self.frames[n] = self.frame(n)
    def key(self, n):
        """the bone whose frame n takes (itself, or the one it lies along, or up to the nearest that has an aim)"""
        k = n
        while k is not None and k not in AIM and k not in ALONG: k = self.parent.get(k)
        return ALONG.get(k, k) if k is not None else None
    def frame(self, n):
        """(axes, origin, length): a bone with a child to aim at, its own; a bone along another (a twist bone, the ball
        of the foot, a finger's last joint), that one's; any other (the head), its own origin with the axes and length of
        the nearest bone above it that aims"""
        k = self.key(n)
        if k is None or k not in self.head or AIM.get(k) not in self.head:
            return np.eye(3), self.head[n], 1.0
        d = self.head[AIM[k]] - self.head[k]; L = np.linalg.norm(d); y = d / L
        ref = self.front if abs(np.dot(y, self.front)) < 0.75 else np.array([0, 0, 1.0])
        z = ref - y * np.dot(ref, y); z /= np.linalg.norm(z); x = np.cross(y, z)
        origin = self.head[k] if (n in AIM or n in ALONG) else self.head[n]
        return np.stack([x, y, z], 1), origin, L                       # columns: x (across), y (along), z (front)


def weights(mesh, names):
    """vertex x bone weights (normalised), the bones by name"""
    idx = {g.index: g.name for g in mesh.vertex_groups}
    W = np.zeros((len(mesh.data.vertices), len(names))); col = {n: i for i, n in enumerate(names)}
    for v in mesh.data.vertices:
        for g in v.groups:
            n = idx.get(g.group)
            if n in col: W[v.index, col[n]] += g.weight
    s = W.sum(1, keepdims=True); W = np.where(s > 0, W / np.maximum(s, 1e-9), 0)
    return W


def her_profile(her, hv, hW, names):
    """per frame-bone: her skin's distance from the bone, by direction round it (24) and by slice along it (3 cm)"""
    prof = {}
    for k in names:
        if k not in her.frames: continue
        R, o, L = her.frames[k]
        cols = [names.index(k)]
        m = hW[:, cols].sum(1) > 0.4
        if m.sum() < 30: continue
        loc = (hv[m] - o) @ R
        th = np.arctan2(loc[:, 2], loc[:, 0]); rho = np.hypot(loc[:, 0], loc[:, 2]); y = loc[:, 1]
        tb = ((th + math.pi) / (2 * math.pi) * 24).astype(int) % 24
        y0 = y.min(); yb = ((y - y0) / 0.03).astype(int); NY = yb.max() + 1
        G = np.full((24, NY), np.nan)
        for a in range(24):
            for b in range(NY):
                s = rho[(tb == a) & (yb == b)]
                if len(s) >= 3: G[a, b] = np.percentile(s, PCT)
        # (holes: the nearest filled bin along the ring, then along the bone)
        for _ in range(24):
            if not np.isnan(G).any(): break
            G2 = G.copy()
            for a in range(24):
                for b in range(NY):
                    if np.isnan(G[a, b]):
                        nb = [G[(a + d) % 24, b] for d in (-1, 1)] + [G[a, b + d] for d in (-1, 1) if 0 <= b + d < NY]
                        nb = [x for x in nb if not np.isnan(x)]
                        if nb: G2[a, b] = np.mean(nb)
            G = G2
        G = np.where(np.isnan(G), np.nanmedian(rho), G)
        prof[k] = (G, y0, NY)
    return prof


def skin_r(prof, k, th, y):
    G, y0, NY = prof[k]
    a = (((th + math.pi) / (2 * math.pi) * 24).astype(int)) % 24
    b = np.clip(((y - y0) / 0.03).astype(int), 0, NY - 1)
    return G[a, b]


def set_bones(key):
    """all the set's pieces' bones (world heads, parents): one character's bind pose, each piece carrying only some"""
    out = {}
    for f in sorted(os.listdir(os.path.join(SRC, key))):
        if not f.lower().endswith(".fbx"): continue
        before = set(bpy.data.objects); arm, meshes = imp_fbx(os.path.join(SRC, key, f))
        for b in arm.data.bones:
            if b.name not in out: out[b.name] = (np.array(arm.matrix_world @ b.head_local), b.parent.name if b.parent else None)
        for o in [o for o in bpy.data.objects if o not in before]: bpy.data.objects.remove(o, do_unlink=True)
    return out


def fit_set(s, her, hb, hv, hW, hnames, bvh_h, report):
    pieces = []; allb = set_bones(s["key"])
    for f in sorted(os.listdir(os.path.join(SRC, s["key"]))):
        if not f.lower().endswith(".fbx"): continue
        arm, meshes = imp_fbx(os.path.join(SRC, s["key"], f))
        src = Rig(arm, allb)
        for me in meshes:
            if s.get("skeleton") == "ue5":
                mv, unk = remap_groups(me, set(her.head))
                print("S3ARM remap", me.name, "| weights moved", mv, "| bones she lacks, not mapped", sorted(unk))
                report.setdefault("remap", {})[me.name] = {"moved": mv, "unmapped": sorted(unk)}
            names = [g.name for g in me.vertex_groups]
            W = weights(me, names)
            V = np.array([me.matrix_world @ v.co for v in me.data.vertices])
            NEW = np.zeros_like(V); WS = np.zeros(len(V))
            for kb in names:
                cols = [names.index(kb)]
                w = W[:, cols].sum(1); sel = w > 1e-4
                if not sel.any() or kb not in her.frames or kb not in src.frames: continue
                Rs, os_, Ls = src.frames[kb]; Rh, oh, Lh = her.frames[kb]
                loc = (V[sel] - os_) @ Rs
                loc[:, 1] *= (Lh / Ls) if Ls > 1e-6 else 1.0
                th = np.arctan2(loc[:, 2], loc[:, 0]); rho = np.hypot(loc[:, 0], loc[:, 2])
                # the scale across the bone, per quarter round it (from the vertices this bone carries most)
                dom = w[sel] > 0.5
                sq = np.ones(4)
                if kb in prof and dom.sum() >= 30:
                    need = (skin_r(prof, kb, th[dom], loc[dom, 1]) + GAP) / np.maximum(rho[dom], 1e-4)
                    q = (((th[dom] + math.pi / 4) % (2 * math.pi)) / (math.pi / 2)).astype(int) % 4
                    for i in range(4):
                        if (q == i).sum() >= 12: sq[i] = np.clip(np.percentile(need[q == i], NEED_LEGS if kb.startswith(LEGS) else NEED), 0.5, 1.7)
                        else: sq[i] = np.nan
                    sq = np.where(np.isnan(sq), np.nanmean(sq) if not np.isnan(sq).all() else 1.0, sq)
                    report.setdefault("bones", {})[kb] = [round(float(x), 3) for x in sq]
                # (blended between the quarters' middles: 0 at +x, 90 deg at +z ...)
                ang = (th % (2 * math.pi)) / (math.pi / 2); i0 = np.floor(ang).astype(int) % 4; t = ang - np.floor(ang)
                sc = sq[i0] * (1 - t) + sq[(i0 + 1) % 4] * t
                loc[:, 0] *= sc; loc[:, 2] *= sc
                NEW[sel] += w[sel, None] * (oh + loc @ Rh.T); WS[sel] += w[sel]
            ok = WS > 0.5
            print("S3ARM piece", me.name, "| source", V.min(0).round(3), V.max(0).round(3), "| fitted", NEW[ok].min(0).round(3) if ok.any() else None, NEW[ok].max(0).round(3) if ok.any() else None)
            NEW[~ok] = V[~ok]; NEW[ok] /= WS[ok, None]
            # what is left inside her skin, pushed out
            pushed = 0; depth = []
            for i in range(len(NEW)):
                p = mathutils.Vector(NEW[i]); q, n, _, d = bvh_h.find_nearest(p)
                if q is None or d > 0.05 + (0.04 if NEED_LEGS < 90 else 0.0): continue
                sd = (p - q).dot(n)
                if sd < PUSH:
                    NEW[i] = np.array(q + n * PUSH); pushed += 1; depth.append(PUSH - sd)
            report.setdefault("pieces", {})[me.name] = {"verts": len(NEW), "pushed": pushed, "pushed_max_cm": round(100 * max(depth), 2) if depth else 0.0,
                                                        "unweighted": int((~ok).sum())}
            # (in world space, no parent: the armature this piece came with goes, and with it the cm scale it carried)
            me.parent = None; me.matrix_world = mathutils.Matrix.Identity(4); me.modifiers.clear()
            for i, v in enumerate(me.data.vertices): v.co = mathutils.Vector(NEW[i])
            me.data.update()
            pieces.append(me)
        bpy.data.objects.remove(arm, do_unlink=True)
    # one mesh, on her armature
    for o in bpy.context.scene.objects: o.select_set(o in pieces)
    bpy.context.view_layer.objects.active = pieces[0]
    bpy.ops.object.join()
    a = bpy.context.active_object; a.name = a.data.name = PREFIX + s["key"]
    a.parent = hb; a.matrix_parent_inverse = hb.matrix_world.inverted()
    mod = a.modifiers.new("Armature", "ARMATURE"); mod.object = hb
    return a


FJ = os.path.join(OUT, "fit.json")
report_all = json.load(open(FJ)) if os.path.exists(FJ) else {}
for s in J["sets"]:
    if ONLY and s["key"] not in ONLY: continue
    clear()
    hb, hm = imp_fbx(os.path.join(SRC, f"SK_JRPG_{HERO}.fbx")); hm = hm[0]
    her = Rig(hb); hnames = [g.name for g in hm.vertex_groups]
    dg = bpy.context.evaluated_depsgraph_get(); ev = hm.evaluated_get(dg); me_ = ev.to_mesh()
    hv = np.array([hm.matrix_world @ v.co for v in me_.vertices]); me_.calc_loop_triangles()
    tri = [lt.vertices[:] for lt in me_.loop_triangles]; ev.to_mesh_clear()
    bvh_h = BVHTree.FromPolygons([tuple(p) for p in hv], [tuple(t) for t in tri], all_triangles=True)
    hW = weights(hm, hnames)
    prof = her_profile(her, hv, hW, hnames)
    rep = {}
    a = fit_set(s, her, hb, hv, hW, hnames, bvh_h, rep)
    rep["materials"] = [m.name for m in a.data.materials if m]; rep["pct"] = PCT; rep["need_legs"] = NEED_LEGS
    rep["verts"] = len(a.data.vertices)
    report_all[s["key"]] = rep
    for o in bpy.context.scene.objects: o.select_set(o in (hb, a))
    bpy.context.view_layer.objects.active = hb
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, s["key"] + ".fbx"), use_selection=True, add_leaf_bones=False, bake_anim=False,
                             mesh_smooth_type="FACE", object_types={"ARMATURE", "MESH"}, path_mode="AUTO", armature_nodetype="NULL",
                             use_armature_deform_only=False)
    tot = sum(p["verts"] for p in rep["pieces"].values()); pu = sum(p["pushed"] for p in rep["pieces"].values())
    print("S3ARM %s: %d pieces, %d vertices, %d pushed out (%.1f %%), deepest %.1f cm | materials %s" % (
        s["key"], len(rep["pieces"]), tot, pu, 100.0 * pu / max(tot, 1), max(p["pushed_max_cm"] for p in rep["pieces"].values()), rep["materials"]))
    # check renders
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
    skin = bpy.data.materials.new("skin"); skin.diffuse_color = (0.85, 0.7, 0.62, 1)
    hm.data.materials.clear(); hm.data.materials.append(skin)
    for i, m in enumerate(a.data.materials):
        if m: m.diffuse_color = (0.35 + 0.1 * (i % 3), 0.38, 0.45, 1)
    cd = bpy.data.cameras.new("c"); cd.type = "ORTHO"; cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
    ctr = mathutils.Vector(her.head["pelvis"]); ctr.z = (hv[:, 2].max() + hv[:, 2].min()) / 2
    hgt = hv[:, 2].max() - hv[:, 2].min()
    f = mathutils.Vector(her.front)
    for nm, d in (("front", f), ("side", mathutils.Vector((f.y, -f.x, 0))), ("back", -f)):
        cam.location = ctr + d * 5; cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler(); cd.ortho_scale = hgt * 1.08
        sc.render.resolution_x, sc.render.resolution_y = 520, 900
        sc.render.filepath = os.path.join(OUT, f"{s['key']}_{nm}.png"); bpy.ops.render.render(write_still=True)
json.dump(report_all, open(FJ, "w"), indent=1)
print("S3ARM done")
