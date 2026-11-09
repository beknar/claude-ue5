"""Farm animals for Brokenspire's pens, built procedurally in Blender: a chicken, a rabbit, a goat, a pig and a cow.
Nothing of the kind is in the project's packs or the asset library, so each is modelled here from shapes, rigged, skinned
and given three looping clips, and exported as one FBX per animal for Unreal.

Each animal:
  Mesh      a metaball body (balls, capsules and ellipsoids that blend: barrel, chest, rump, neck, head, muzzle, legs,
            udder, comb...) turned into a mesh and decimated, plus lofted parts that metaballs cannot make thin or sharp
            enough (ears, horns, beak, tails, the goat's beard, the chicken's legs and toes, eyes, nostrils, the pig's snout
            disc). Smooth shading. Under 6000 triangles (TRI_BUDGET). Faces the +X axis (Unreal +X), stands on z 0,
            centimetres (scene unit scale 0.01, as tripo_build.py / crowd_clips.py export).
  Colours   one material per part (Principled BSDF base colour, roughness 0.8; the FBX carries it as the diffuse colour
            Unreal's import reads). Each face takes the part whose field is strongest at it, then the variant's pattern
            (a cow's patches, a pig's spots, a rabbit's pale belly, the inner ear) changes some. Two or three colourings
            (variants A, B, C) of the same mesh on the same skeleton.
  Skeleton  root at the origin on the ground; pelvis, spine, neck, head, jaw, ears, tail; four bones a leg for hooved
            animals (upper, lower, cannon, hoof) and the chicken (thigh, shin, tarsus, toes), three for the rabbit.
  Skin      weights from the shapes themselves: a vertex follows the bones of the metaball elements whose fields make it
            (the field sums to the threshold on the surface, so the shares are smooth where shapes blend), smoothed along
            the mesh twice; the hoof / paw / toe zone is held rigid to its planted bone; at most four bones a vertex. (Blender's
            heat weighting was not used: on blended metaball meshes with thin legs it bleeds between neighbouring parts.)
  Clips     (30 fps, the last key equal to the first, so they loop)
            Idle   5 s: breathing, a look round (left, then right), ear flicks, a tail swish; the feet planted.
            Graze  4 s: the head down to the ground, chewing; the chicken pecks four times, the rabbit nibbles; the feet
                   planted. Solved: the body tips forward a little, the head is held at an angle below the horizontal, and the
                   neck's turn is searched until the lowest of the head's own vertices is at `graze_z` (a turn of every bone
                   at once curled the head under the chest).
            Walk   one stride, in place (root still): each foot's stance moves it back at the ground speed, its swing lifts
                   and folds it; the stride is the longest the legs reach without stretching (searched), up to the
                   animal's natural speed. The legs are solved (two-bone IK, the cannon following the leg's swing).
Measured on the skinned mesh, frame by frame (printed, and written to farm_animals.json): the size (bounding box, back
height), the triangles, the bones; for each planted foot its sole's lowest point (should be 0) and, in Idle and Graze,
how far its sole moves (should be 0); in Walk the sole's speed over its stance (the walk speed the game moves the animal
at) and how far it strays from that steady speed; the mouth's lowest point in Graze; the edges' worst stretch; the
loop's seam (the last frame against the first); the legs' overreach (IK clamped). The weights are checked: the sums,
the bones per vertex, the farthest a vertex is from a bone that moves it.
Writes into out_dir: SK_Farm_<Animal>.fbx (mesh A + armature + takes Idle, Graze, Walk), SK_Farm_<Animal>_<V>.fbx for the
other colourings (mesh + armature, no takes: import them onto the first one's skeleton), farm_animals.json, and in
out_dir/preview: <animal>_sheet.png (16 panels, see SHEET below), <animal>_q.png, lineup.png (all five beside a 180 cm
figure). Then reads each FBX back and checks its bones, materials' colours and takes.
Blender: -b -P farm_animals.py -- out_dir [only=chicken,pig] [nopreview]"""
import json, math, os, sys
import bpy, bmesh
import numpy as np
from mathutils import Matrix, Vector, Quaternion
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0]) if argv else os.path.abspath("farm_animals")
OPTS = argv[1:]
ONLY = next((a.split("=", 1)[1].split(",") for a in OPTS if a.startswith("only=")), None)
PREVIEW = "nopreview" not in OPTS
PREV = os.path.join(OUT, "preview")
FPS = 30
THRESH = 0.6                    # the metaballs' threshold: a lone element's surface is at radius x K(stiffness)
TRI_BUDGET = 6000
IDLE_LEN, GRAZE_LEN = 5.0, 4.0
SIDES = (("l", 1.0), ("r", -1.0))            # left is +Y (the animal faces +X)
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
I4 = Matrix.Identity(4)
ONE = Vector((1.0, 1.0, 1.0))


def log(*a): print("FARM", *a, flush=True)


# ---------------------------------------------------------------- small helpers
def K(s):
    """where a lone element's surface is, as a share of its radius, for a stiffness s"""
    return math.sqrt(1.0 - (THRESH / s) ** (1.0 / 3.0))


def qrot(pitch=0.0, yaw=0.0, roll=0.0):
    """a turn in the animal's axes (degrees): pitch about +Y (positive: nose down), yaw about +Z (positive: to its left),
    roll about +X"""
    return Quaternion(Z, math.radians(yaw)) @ Quaternion(Y, math.radians(pitch)) @ Quaternion(X, math.radians(roll))


def angY(v):
    """the turn about +Y that takes straight down onto v (radians, in the XZ plane)"""
    return math.atan2(-v.x, -v.z)


def smooth(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3.0 - 2.0 * x)


def hold(t, t0, t1, ramp):
    """0 before t0, up to 1 over `ramp`, held, back to 0 by t1"""
    return smooth((t - t0) / ramp) * (1.0 - smooth((t - (t1 - ramp)) / ramp))


def bump(t, t0, dur):
    u = (t - t0) / dur
    return math.sin(math.pi * u) ** 2 if 0.0 <= u <= 1.0 else 0.0


def srgb(h):
    """'#RRGGBB' (as a painter picks it) to linear RGB (what the material and the FBX hold)"""
    c = [int(h[i:i + 2], 16) / 255.0 for i in (1, 3, 5)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def seg_dist(p, a, b):
    """distance from p (n,3) to the segment a-b"""
    ab = b - a; L2 = float(ab @ ab)
    t = np.clip(((p - a) @ ab) / max(L2, 1e-9), 0.0, 1.0)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=1)


def noise3(P, freq, seed, n=14):
    """smooth 3D noise (a sum of cosine waves in random ways), about unit spread: patches for coats"""
    rng = np.random.default_rng(seed)
    d = rng.normal(size=(n, 3)); d /= np.linalg.norm(d, axis=1)[:, None]
    k = d * (freq * (0.6 + 0.8 * rng.random(n)))[:, None]
    ph = rng.random(n) * 2 * math.pi
    return np.cos(P @ k.T + ph).sum(1) / math.sqrt(n / 2.0)


# ---------------------------------------------------------------- an animal's description
class Spec:
    """bones, metaball elements, lofted parts, legs, colours and clip settings of one animal (cm, faces +X)"""

    def __init__(self, name, res, body_tris, sole_band, hoof_h=0.0, rigid=(0.0, 0.0)):
        self.name = name; self.res = res; self.body_tris = body_tris
        self.sole_band = sole_band          # vertices lower than this are put on the ground: flat soles at z 0
        self.hoof_h = hoof_h                # faces of the coat lower than this are hoof
        self.rigid = rigid                  # (height, distance): the planted bone holds these vertices alone
        self.bones, self.blobs, self.parts, self.legs = [], [], [], []
        self.variants = {}; self.pattern = None; self.parts_fn = None; self.anim = {}
        self.surf = None

    def bone(self, name, parent, head, tail):
        self.bones.append((name, parent, Vector(head), Vector(tail)))

    def bone_seg(self, name):
        b = next(b for b in self.bones if b[0] == name); return b[2], b[3]

    # metaball elements: given by their visible sizes, the element's radius made from the stiffness
    def ball(self, c, r, bone, mat="coat", s=2.0):
        self.blobs.append(dict(type='BALL', co=Vector(c), q=Quaternion(), R=r / K(s), size=ONE.copy(), s=s, bone=bone, mat=mat))

    def ell(self, c, a, bone, mat="coat", rot=(0.0, 0.0, 0.0), s=2.0):
        R = max(a) / K(s)
        self.blobs.append(dict(type='ELLIPSOID', co=Vector(c), q=qrot(*rot), R=R, size=Vector([x / (K(s) * R) for x in a]),
                               s=s, bone=bone, mat=mat))

    def cap(self, p0, p1, r, bone, mat="coat", s=2.0):
        p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
        self.blobs.append(dict(type='CAPSULE', co=(p0 + p1) * 0.5, q=X.rotation_difference(d), R=r / K(s),
                               size=Vector((d.length * 0.5, 1.0, 1.0)), s=s, bone=bone, mat=mat))

    def leg(self, kind, sd, y, pts, parent, names, bend, follow=0.8):
        """a leg's bones from the hip / shoulder down to its ground point (x, z pairs at side y); the last bone is the
        planted one (hoof, toes, paw, foot); with four bones the third is the cannon / tarsus, which follows the swing"""
        P = [Vector((p[0], y, p[1])) for p in pts]
        bones = [f"{n}_{sd}" for n in names]; prev = parent
        for i, b in enumerate(bones):
            self.bone(b, prev, P[i], P[i + 1]); prev = b
        chain = bones if len(bones) == 4 else [bones[0], bones[1], None, bones[2]]
        self.legs.append(dict(id=f"{kind}_{sd}", kind=kind, bones=chain, bend=bend, follow=follow))
        return P

    # lofted parts: a tube along points, an elliptic section (rx across, ry along `up`), closed at both ends
    def loft(self, name, pts, rx, ry, up, w, mat, n=8):
        pts = [Vector(p) for p in pts]; m = len(pts)
        ups = [Vector(u) for u in up] if isinstance(up, list) else [Vector(up)] * m
        ws = w if isinstance(w, list) else [w] * m
        verts, wts, tris, rings = [], [], [], []
        for i, p in enumerate(pts):
            t = (pts[min(i + 1, m - 1)] - pts[max(i - 1, 0)]).normalized()
            u = ups[i] - t * ups[i].dot(t); u.normalize(); s = t.cross(u)
            wi = ws[i] if isinstance(ws[i], dict) else {ws[i]: 1.0}
            if rx[i] <= 1e-4:
                rings.append([len(verts)]); verts.append(p.copy()); wts.append(wi)
            else:
                r = []
                for k in range(n):
                    a = 2 * math.pi * k / n
                    r.append(len(verts)); verts.append(p + s * (rx[i] * math.cos(a)) + u * (ry[i] * math.sin(a))); wts.append(wi)
                rings.append(r)
        for i in range(m - 1):
            A, B = rings[i], rings[i + 1]
            if len(A) == 1 and len(B) == 1: continue
            if len(A) == 1: tris += [(A[0], B[(k + 1) % n], B[k]) for k in range(n)]
            elif len(B) == 1: tris += [(A[k], A[(k + 1) % n], B[0]) for k in range(n)]
            else:
                for k in range(n):
                    a0, a1, b0, b1 = A[k], A[(k + 1) % n], B[k], B[(k + 1) % n]
                    tris += [(a0, a1, b1), (a0, b1, b0)]
        for end, ring in ((0, rings[0]), (m - 1, rings[-1])):
            if len(ring) > 1:
                c = len(verts); verts.append(pts[end].copy()); wts.append(wts[ring[0]])
                tris += [(c, ring[(k + 1) % n], ring[k]) for k in range(n)]
        self.parts.append(dict(name=name, verts=verts, w=wts, tris=tris, mat=[mat] * len(tris)))

    def sphere(self, name, c, r, w, mat, axis=X, flat=1.0, n=10, m=6):
        axis = Vector(axis).normalized(); up = Z if abs(axis.z) < 0.9 else X
        pts, rr = [], []
        for i in range(m + 1):
            th = math.pi * (1.0 - i / m)
            pts.append(Vector(c) + axis * (r * flat * math.cos(th))); rr.append(r * math.sin(th) if 0 < i < m else 0.0)
        self.loft(name, pts, rr, rr, up, w, mat, n=n)

    def chain_w(self, pts, chain):
        """weights along a chain of bones for points of a tail: the two nearest bones, blended"""
        out = []
        for p in pts:
            p = np.array(p, float)[None]
            d = {b: float(seg_dist(p, np.array(self.bone_seg(b)[0]), np.array(self.bone_seg(b)[1]))[0]) for b in chain}
            inv = sorted(((1.0 / (d[b] + 0.4) ** 4, b) for b in chain), reverse=True)[:2]
            tot = sum(v for v, _ in inv); out.append({b: v / tot for v, b in inv})
        return out

    def snap(self, c, d, inset):
        """a point on the body's surface: from c out along d, back onto the skin, then `inset` in (eyes, nostrils)"""
        d = Vector(d).normalized(); c = Vector(c)
        hit = self.surf.ray_cast(c + d * 60.0, -d)
        return (hit[0] - d * inset) if hit[0] is not None else c


def quad_names(front):
    return ["upperarm", "forearm", "cannon_front", "hoof_front"] if front else ["thigh", "shin", "cannon_rear", "hoof_rear"]


def hooved_leg_blobs(S, P, front, r_up, r_mid, r_can, r_hoof, sd):
    """the visible leg of a hooved animal on the bones from S.leg: upper (mostly inside the body), lower, cannon, hoof"""
    n = [f"{x}_{sd}" for x in quad_names(front)]
    if front: S.cap(P[0], P[1], r_up, n[0])
    S.cap(P[1], P[2], r_mid, n[1])
    S.ball(P[2], r_mid * 0.85, n[2])                                   # the knee / hock
    S.cap(P[2], P[3], r_can, n[2], s=3.0)
    S.ball(P[3] + Vector((0.3, 0, 0.4)), r_can * 1.12, n[3], s=3.0)    # the fetlock
    S.cap(P[3] + Vector((0.2, 0, -0.4 * r_hoof)), Vector((P[4].x + 0.35 * r_hoof, P[4].y, r_hoof)), r_hoof, n[3], s=3.0)


# ---------------------------------------------------------------- the five animals
def pig():
    S = Spec("Pig", res=1.0, body_tris=5000, sole_band=0.6, hoof_h=4.6, rigid=(5.0, 6.0))
    S.bone("root", None, (0, 0, 0), (0, 0, 15))
    S.bone("pelvis", "root", (-30, 0, 47), (-2, 0, 48))
    S.bone("spine_01", "pelvis", (-2, 0, 48), (22, 0, 48))
    S.bone("spine_02", "spine_01", (22, 0, 48), (34, 0, 46))
    S.bone("neck_01", "spine_02", (34, 0, 42), (47, 0, 47))
    S.bone("head", "neck_01", (47, 0, 47), (76, 0, 38))
    S.bone("jaw", "head", (52, 0, 40), (68, 0, 34))
    for sd, y in SIDES: S.bone(f"ear_{sd}", "head", (51, 6 * y, 55), (59.5, 12.5 * y, 69.5))
    S.bone("tail_01", "pelvis", (-46, 0, 54), (-50, 0, 53)); S.bone("tail_02", "tail_01", (-50, 0, 53), (-54, 0, 51))
    # the body: barrel, rump, chest, belly, jowl
    S.ell((-4, 0, 45), (41, 22, 20.5), "spine_01")
    S.ball((-28, 0, 45), 19, "pelvis")
    S.ell((22, 0, 44), (17, 20.5, 20.5), "spine_02")
    S.ell((-2, 0, 35), (32, 18.5, 12), "spine_01")                          # the belly, low
    S.ell((38, 0, 41), (12, 16, 17), "neck_01")                             # the jowl
    # the head: a wedge to the snout, the cheeks / jaw
    S.ell((50, 0, 46), (13, 12.5, 12.5), "head", rot=(12, 0, 0))
    S.cap((56, 0, 43), (70, 0, 39.5), 7.6, "head")
    S.cap((51, 0, 38), (65, 0, 35.5), 6.0, "jaw")
    for sd, y in SIDES:
        S.ell((-28, 10 * y, 36), (16, 11, 16), f"thigh_{sd}")              # the ham
        Pf = S.leg("front", sd, 11 * y, [(28, 44), (17, 30), (24, 13), (26, 4), (27, 0)], "spine_02", quad_names(True), 1)
        Pr = S.leg("rear", sd, 11 * y, [(-30, 46), (-21, 31), (-34, 15), (-32, 4), (-31, 0)], "pelvis", quad_names(False), -1)
        hooved_leg_blobs(S, Pf, True, 9.0, 6.4, 4.4, 3.8, sd)
        hooved_leg_blobs(S, Pr, False, 0, 6.6, 4.4, 3.8, sd)

    def parts(S):
        S.loft("snout", [(69.5, 0, 39.5), (73.5, 0, 39.0), (75.8, 0, 38.8)], [6.8, 7.0, 6.6], [6.0, 6.2, 5.9], Z, "head", "snout", n=14)
        for sd, y in SIDES:
            S.sphere("nostril", (75.9, 2.5 * y, 39.0), 1.25, "head", "nostril", axis=X, flat=0.45, n=8, m=4)
            S.sphere("eye", S.snap((60, 8 * y, 51), (0.25, y, 0.3), 0.5), 1.3, "head", "eye", axis=Vector((0.25, y, 0.3)), n=8, m=5)
            # the ears: broad triangles leaning forward and out, their faces seen from the side
            S.loft("ear", [(50, 6.5 * y, 55), (55, 9.5 * y, 61), (60.5, 12 * y, 65), (65, 13 * y, 67)], [4.0, 6.5, 4.5, 0],
                   [1.3, 1.1, 0.8, 0], (0.55, 0.75 * y, 0.35), f"ear_{sd}", "coat")
        base = Vector((-46.5, 0, 53)); ax = Vector((-1, 0, -0.35)).normalized(); pts = []
        for k in range(17):                                    # the curly tail: a corkscrew back and down
            s = k / 16.0; th = s * 1.75 * 2 * math.pi
            pts.append(base + ax * (s * 8.0) + Vector((0, math.sin(th) * 2.6, (math.cos(th) - 1.0) * 2.6)))
        r = [1.5 - 0.7 * k / 16 for k in range(16)] + [0]
        S.loft("tail", pts, r, r, X, S.chain_w(pts, ["tail_01", "tail_02"]), "coat", n=6)
    S.parts_fn = parts
    S.variants = {"A": {"coat": "#E8B0A2", "snout": "#D88C82", "nostril": "#5A3430", "hoof": "#8E7268", "eye": "#141010"},
                  "B": {"coat": "#E9C3B5", "spot": "#2B2523", "snout": "#D88C82", "nostril": "#5A3430", "hoof": "#6E5A54", "eye": "#141010"}}

    def pattern(v, c):                                         # B: a Gloucester Old Spot, black spots on pink
        if v == "B":
            n = noise3(c["centers"], 0.32, 7)
            coat = c["tags"] == "coat"; t = np.quantile(n[coat], 0.86)
            c["tags"][coat & (n > t)] = "spot"
    S.pattern = pattern
    S.anim = dict(neck=[("neck_01", 0.55), ("head", 0.45)], look=24, look_pitch=-4, breaths=2, breath_z=0.25, breath_pitch=0.6,
                  ears=["ear_l", "ear_r"], ear_flick=22, tail=["tail_01", "tail_02"], tail_swish=25,
                  graze=dict(pre={"spine_01": 3, "spine_02": 10}, neck=[("neck_01", 1.0)], head_deg=62), graze_z=1.0,
                  chew=6, chews=8, graze_yaw=8,
                  walk=dict(T=0.9, v=60, bob=0.8, nod=3, roll=1.5, tail=20,
                            phase={"rear_l": 0.0, "front_l": 0.25, "rear_r": 0.5, "front_r": 0.75},
                            gait={"front": dict(duty=0.62, height=5, tilt=30, fold=35), "rear": dict(duty=0.62, height=5, tilt=30, fold=30)}))
    return S


def cow():
    S = Spec("Cow", res=1.8, body_tris=5100, sole_band=1.2, hoof_h=8.5, rigid=(9.0, 10.0))
    S.bone("root", None, (0, 0, 0), (0, 0, 30))
    S.bone("pelvis", "root", (-62, 0, 116), (-10, 0, 120))
    S.bone("spine_01", "pelvis", (-10, 0, 120), (38, 0, 124))
    S.bone("spine_02", "spine_01", (38, 0, 124), (52, 0, 116))
    S.bone("neck_01", "spine_02", (40, 0, 98), (70, 0, 113))
    S.bone("neck_02", "neck_01", (70, 0, 113), (97, 0, 126))
    S.bone("head", "neck_02", (97, 0, 126), (141, 0, 97))
    S.bone("jaw", "head", (103, 0, 108), (132, 0, 92))
    for sd, y in SIDES: S.bone(f"ear_{sd}", "head", (99, 12 * y, 124), (101.5, 32 * y, 119.5))
    S.bone("tail_01", "pelvis", (-85, 0, 131), (-91.5, 0, 112))
    S.bone("tail_02", "tail_01", (-91.5, 0, 112), (-91.5, 0, 84))
    S.bone("tail_03", "tail_02", (-91.5, 0, 84), (-90, 0, 50))
    # the body: barrel, chest, withers, rump with its hook and pin bones, belly, neck, dewlap
    S.ell((-8, 0, 104), (66, 30, 33), "spine_01")
    S.ell((40, 0, 104), (25, 27, 33), "spine_02")
    S.ball((36, 0, 122), 16, "spine_02")
    S.ell((-62, 0, 113), (24, 27, 25), "pelvis")
    S.ball((-82, 0, 129), 6, "pelvis")
    for sd, y in SIDES:
        S.ball((-55, 20 * y, 130), 5.5, "pelvis"); S.ball((-80, 8 * y, 126.5), 4.5, "pelvis")
    S.ell((-10, 0, 92), (48, 29, 22), "spine_01")
    S.cap((54, 0, 110), (80, 0, 120), 19, "neck_01")
    S.cap((80, 0, 120), (96, 0, 124), 15, "neck_02")
    S.ell((72, 0, 94), (16, 6, 13), "neck_01")
    # the head: poll, the long face, the muzzle, the jaw
    S.ell((99, 0, 124), (12, 13, 13), "head")
    S.cap((100, 0, 118), (116, 0, 110), 11.5, "head")
    S.cap((116, 0, 110), (130, 0, 101), 9.5, "head")
    S.ball((133.5, 0, 99), 9.0, "head", "muzzle")
    S.cap((104, 0, 106), (128, 0, 94), 7, "jaw")
    # the udder and its four teats
    S.ell((-40, 0, 75), (17, 15, 10), "pelvis", "udder")
    for dx in (-7, 7):
        for sd, y in SIDES: S.cap((-40 + dx, 5.5 * y, 69), (-40 + dx, 5.5 * y, 59), 2.0, "pelvis", "udder", s=4.0)
    for sd, y in SIDES:
        S.ell((-58, 15 * y, 98), (20, 13, 26), f"thigh_{sd}")
        Pf = S.leg("front", sd, 17 * y, [(46, 112), (26, 78), (38, 38), (42, 11), (44, 0)], "spine_02", quad_names(True), 1)
        Pr = S.leg("rear", sd, 18 * y, [(-60, 116), (-46, 84), (-70, 52), (-66, 11), (-64, 0)], "pelvis", quad_names(False), -1)
        hooved_leg_blobs(S, Pf, True, 15, 8.5, 5.5, 6.0, sd)
        hooved_leg_blobs(S, Pr, False, 0, 9.0, 5.5, 6.0, sd)

    def parts(S):
        for sd, y in SIDES:
            S.loft("ear", [(99, 12 * y, 124), (100, 19 * y, 123), (101, 26 * y, 121.5), (101.5, 32 * y, 119.5)], [3.5, 7, 6, 0],
                   [2.0, 1.6, 1.2, 0], (1, 0, 0.35), f"ear_{sd}", "coat")
            S.loft("horn", [(97, 8 * y, 131), (97, 15 * y, 137), (99, 20 * y, 141), (102, 23 * y, 146)], [3.2, 2.6, 1.8, 0],
                   [3.2, 2.6, 1.8, 0], X, "head", "horn")
            S.sphere("eye", S.snap((106, 11 * y, 124), (0.15, y, 0.2), 0.8), 2.3, "head", "eye", axis=Vector((0.15, y, 0.2)), n=8, m=5)
            S.sphere("nostril", S.snap((136, 4.5 * y, 100), (1, 0.3 * y, 0), 0.3), 1.7, "head", "nostril", axis=X, flat=0.5, n=8, m=4)
        pts = [(-85, 0, 131), (-89, 0, 124), (-91.5, 0, 112), (-92, 0, 98), (-91.5, 0, 84), (-91, 0, 72), (-90.5, 0, 64),
               (-90, 0, 58), (-90, 0, 53), (-90, 0, 49)]
        r = [3.4, 2.8, 2.4, 2.1, 1.9, 1.8, 2.6, 4.2, 3.6, 0]
        S.loft("tail", pts, r, r, X, S.chain_w(pts, ["tail_01", "tail_02", "tail_03"]), "coat")
        p = S.parts[-1]                                         # the switch's tuft
        for i, tri in enumerate(p["tris"]):
            if np.mean([p["verts"][k].z for k in tri]) < 67: p["mat"][i] = "tuft"
    S.parts_fn = parts
    S.variants = {"A": {"coat": "#F0EEE8", "black": "#1E1C1C", "udder": "#E2A69C", "muzzle": "#B8908A", "nostril": "#3A2A28",
                        "hoof": "#3A3533", "horn": "#D8CDB4", "tuft": "#F0EEE8", "eye": "#0C0A0A"},
                  "B": {"coat": "#7E3A1C", "white": "#EEEAE0", "udder": "#E2A69C", "muzzle": "#E0B4A6", "nostril": "#5A3A32",
                        "hoof": "#4A403A", "horn": "#DCD0B5", "tuft": "#EEEAE0", "eye": "#0C0A0A"}}

    def pattern(v, c):
        tg, P, N, dom = c["tags"], c["centers"], c["normals"], c["dom"]
        coat = tg == "coat"
        head = np.isin(dom, ["head", "jaw", "ear_l", "ear_r"])
        legs_low = P[:, 2] < 34
        if v == "A":                                            # Holstein: black patches on white, a white blaze
            n = noise3(P, 0.07, 11)
            t = np.quantile(n[coat & ~head], 0.5)
            blk = coat & (n > t) & ~legs_low
            blk |= coat & head
            blaze = head & (np.abs(P[:, 1]) < 5.0) & (N[:, 0] > 0.25) & (P[:, 2] > 104) & ~np.isin(dom, ["ear_l", "ear_r"])
            blk &= ~blaze
            belly = coat & (N[:, 2] < -0.6) & (P[:, 2] < 82)
            blk &= ~belly
            tg[blk] = "black"
        else:                                                   # Hereford: red with a white face, throat, belly, legs
            face = head & ~np.isin(dom, ["ear_l", "ear_r"])
            throat = coat & np.isin(dom, ["neck_01", "neck_02"]) & (N[:, 2] < -0.35)
            belly = coat & (N[:, 2] < -0.55) & (P[:, 2] < 90)
            crest = coat & np.isin(dom, ["neck_02"]) & (N[:, 2] > 0.6)
            tg[coat & (face | throat | belly | legs_low | crest)] = "white"
    S.pattern = pattern
    S.anim = dict(neck=[("neck_01", 0.35), ("neck_02", 0.35), ("head", 0.3)], look=30, look_pitch=-5, breaths=2, breath_z=0.5,
                  breath_pitch=0.5, ears=["ear_l", "ear_r"], ear_flick=28, tail=["tail_01", "tail_02", "tail_03"], tail_swish=10,
                  graze=dict(pre={"spine_01": 1, "spine_02": 6}, neck=[("neck_01", 0.55), ("neck_02", 0.45)], head_deg=72),
                  graze_z=1.8, chew=7, chews=6, graze_yaw=7,
                  walk=dict(T=1.05, v=95, bob=1.6, nod=3, roll=1.5, tail=6,
                            phase={"rear_l": 0.0, "front_l": 0.25, "rear_r": 0.5, "front_r": 0.75},
                            gait={"front": dict(duty=0.64, height=11, tilt=32, fold=40), "rear": dict(duty=0.64, height=11, tilt=32, fold=35)}))
    return S


def goat():
    S = Spec("Goat", res=1.1, body_tris=4900, sole_band=0.6, hoof_h=4.0, rigid=(4.2, 5.0))
    S.bone("root", None, (0, 0, 0), (0, 0, 15))
    S.bone("pelvis", "root", (-28, 0, 62), (-4, 0, 63))
    S.bone("spine_01", "pelvis", (-4, 0, 63), (16, 0, 64))
    S.bone("spine_02", "spine_01", (16, 0, 64), (24, 0, 62))
    S.bone("neck_01", "spine_02", (17, 0, 53), (32, 0, 72))
    S.bone("neck_02", "neck_01", (32, 0, 72), (40, 0, 84))
    S.bone("head", "neck_02", (40, 0, 84), (62, 0, 75))
    S.bone("jaw", "head", (44, 0, 79), (58, 0, 72))
    for sd, y in SIDES: S.bone(f"ear_{sd}", "head", (42, 4.5 * y, 86.5), (41, 16 * y, 83.5))
    S.bone("tail_01", "pelvis", (-39, 0, 68), (-45, 0, 78.5))
    S.ell((-4, 0, 57), (30, 13.5, 14.5), "spine_01")
    S.ell((18, 0, 56), (14, 13, 16.5), "spine_02")
    S.ball((16, 0, 66), 9, "spine_02")
    S.ell((-27, 0, 61), (13, 12.5, 12.5), "pelvis")
    for sd, y in SIDES: S.ball((-23, 7 * y, 69), 3, "pelvis")
    S.ell((-4, 0, 50), (24, 13, 10), "spine_01")
    S.cap((22, 0, 61), (32, 0, 73), 7.5, "neck_01")
    S.cap((32, 0, 73), (39, 0, 83), 6.0, "neck_02")
    S.ell((43, 0, 86), (7.5, 5.8, 6.5), "head", rot=(25, 0, 0))
    S.cap((45, 0, 84), (57, 0, 77), 4.1, "head")
    S.ball((58.3, 0, 76.2), 3.2, "head")
    S.cap((45, 0, 80), (56, 0, 73.5), 3.0, "jaw")
    for sd, y in SIDES:
        S.ell((-26, 7 * y, 52), (10, 6.5, 13), f"thigh_{sd}")
        Pf = S.leg("front", sd, 8 * y, [(24, 58), (12, 41), (18, 20), (20, 5), (21, 0)], "spine_02", quad_names(True), 1)
        Pr = S.leg("rear", sd, 7.5 * y, [(-28, 62), (-20, 44), (-32, 26), (-30, 5), (-29, 0)], "pelvis", quad_names(False), -1)
        hooved_leg_blobs(S, Pf, True, 7.0, 3.4, 2.2, 2.7, sd)
        hooved_leg_blobs(S, Pr, False, 0, 3.8, 2.2, 2.7, sd)

    def parts(S):
        S.loft("beard", [(50, 0, 74.5), (49.5, 0, 70.5), (48.5, 0, 66.5), (47.5, 0, 63)], [2.4, 2.7, 2.3, 1.3], [2.6, 2.4, 1.9, 1.0], X,
               "jaw", "beard")
        for sd, y in SIDES:
            S.loft("horn", [(42, 2.4 * y, 90), (41, 3.2 * y, 95), (38.5, 4.3 * y, 99.5), (34.5, 5.6 * y, 102), (31, 6.4 * y, 102.5)],
                   [1.8, 1.5, 1.2, 0.8, 0], [1.8, 1.5, 1.2, 0.8, 0], X, "head", "horn")
            S.loft("ear", [(42, 4.5 * y, 86.5), (42, 8 * y, 85.5), (41.5, 12 * y, 84), (41, 16 * y, 82)], [1.6, 2.8, 2.2, 0],
                   [0.8, 0.7, 0.5, 0], (0.65, 0, 0.75), f"ear_{sd}", "coat")
            S.sphere("eye", S.snap((48, 5 * y, 87.5), (0.25, y, 0.2), 0.45), 1.25, "head", "eye", axis=Vector((0.25, y, 0.2)), n=8, m=5)
        S.loft("tail", [(-39, 0, 68), (-42, 0, 72.5), (-44, 0, 76.5), (-45, 0, 78.5)], [2.2, 1.9, 1.3, 0], [2.2, 1.9, 1.3, 0], X,
               "tail_01", "coat", n=6)
    S.parts_fn = parts
    S.variants = {"A": {"coat": "#E8E3D6", "beard": "#A39782", "horn": "#8C7F6B", "hoof": "#4A4440", "eye": "#2A1C0C"},
                  "B": {"coat": "#7A5133", "sock": "#E2DACB", "beard": "#3A2C22", "horn": "#5F5545", "hoof": "#3A3430", "eye": "#2A1C0C"}}

    def pattern(v, c):
        if v == "B":                                            # brown, with white socks and a white face stripe each side
            tg, P, N, dom = c["tags"], c["centers"], c["normals"], c["dom"]
            coat = tg == "coat"
            tg[coat & (P[:, 2] < 19)] = "sock"
            stripe = coat & (dom == "head") & (np.abs(np.abs(P[:, 1]) - 3.4) < 1.3) & (P[:, 0] > 46)
            tg[stripe] = "sock"
    S.pattern = pattern
    S.anim = dict(neck=[("neck_01", 0.35), ("neck_02", 0.35), ("head", 0.3)], look=35, look_pitch=-6, breaths=2, breath_z=0.3,
                  breath_pitch=0.6, ears=["ear_l", "ear_r"], ear_flick=30, tail=["tail_01"], tail_swish=25,
                  graze=dict(pre={"spine_01": 1, "spine_02": 7}, neck=[("neck_01", 0.55), ("neck_02", 0.45)], head_deg=70),
                  graze_z=1.0, chew=8, chews=8, graze_yaw=8,
                  walk=dict(T=0.85, v=75, bob=1.0, nod=4, roll=1.5, tail=10,
                            phase={"rear_l": 0.0, "front_l": 0.25, "rear_r": 0.5, "front_r": 0.75},
                            gait={"front": dict(duty=0.62, height=7, tilt=35, fold=40), "rear": dict(duty=0.62, height=7, tilt=35, fold=35)}))
    return S


def chicken():
    S = Spec("Chicken", res=0.42, body_tris=4800, sole_band=0.25, rigid=(0.0, 0.0))
    S.bone("root", None, (0, 0, 0), (0, 0, 8))
    S.bone("pelvis", "root", (-9, 0, 25), (0, 0, 22))
    S.bone("spine_01", "pelvis", (0, 0, 22), (7, 0, 25))
    S.bone("neck_01", "spine_01", (7, 0, 25), (9.5, 0, 31))
    S.bone("neck_02", "neck_01", (9.5, 0, 31), (11, 0, 35.5))
    S.bone("head", "neck_02", (11, 0, 35.5), (18, 0, 35.2))
    S.bone("tail_01", "pelvis", (-9, 0, 27), (-15, 0, 36))
    for sd, y in SIDES: S.bone(f"wing_{sd}", "spine_01", (5, 7.5 * y, 25), (-10, 8.5 * y, 24))
    S.ell((0, 0, 22.5), (12.5, 9.5, 9.5), "spine_01", rot=(12, 0, 0))
    S.ball((6.5, 0, 21), 8, "spine_01")                                    # the breast
    S.ell((-7, 0, 25), (8.5, 8.5, 8.5), "pelvis")
    S.ell((-3, 0, 17.5), (7, 7, 4.5), "pelvis")                             # the fluff underneath
    S.ell((-12.5, 0, 31), (6.5, 2.6, 9), "tail_01", "tailf", rot=(-30, 0, 0), s=3.0)
    for sd, y in SIDES:
        S.ell((-1, 8.6 * y, 23.5), (10, 2.4, 6), f"wing_{sd}", "wing", rot=(10, -8 * y, 0), s=3.0)
        S.ell((1.5, 4.3 * y, 15.5), (4, 3.2, 5), f"thigh_{sd}")              # the feathered drumstick
    S.cap((7, 0, 27), (10.5, 0, 34), 4.4, "neck_01", "hackle")
    S.cap((10, 0, 33), (11, 0, 35.5), 3.8, "neck_02", "hackle")
    S.ball((11.6, 0, 36.6), 3.5, "head")
    for c, r in (((9.3, 0, 39.8), 1.3), ((10.8, 0, 40.6), 1.5), ((12.4, 0, 40.4), 1.4), ((13.8, 0, 39.4), 1.15)):
        S.ball(c, r, "head", "comb", s=3.0)                                # the comb's points
    S.ell((11.5, 0, 39.3), (3.5, 0.8, 1.2), "head", "comb", s=3.0)
    for sd, y in SIDES: S.ell((14.6, 0.8 * y, 32.9), (1.0, 0.7, 1.6), "head", "comb", s=3.0)   # the wattles
    for sd, y in SIDES:
        S.leg("leg", sd, 4.5 * y, [(0, 19), (4, 14.5), (-0.5, 8.5), (1.5, 1.0), (6.5, 0.55)], "pelvis",
              ["thigh", "shin", "tarsus", "toes"], -1, follow=0.6)

    def parts(S):
        S.loft("beak", [(13.9, 0, 36.5), (16, 0, 36.0), (17.9, 0, 35.0)], [1.3, 0.75, 0], [1.15, 0.65, 0], Z, "head", "beak")
        for sd, y in SIDES:
            S.sphere("eye", S.snap((13.6, 2.9 * y, 37.3), (0.25, y, 0.15), 0.3), 0.8, "head", "eye", axis=Vector((0.25, y, 0.15)), n=8, m=5)
            yy = 4.5 * y
            S.loft("shin", [(4, yy, 14.5), (1.8, yy, 11.5), (-0.5, yy, 8.5)], [1.7, 1.4, 0.9], [1.7, 1.4, 0.9], X,
                   [{f"shin_{sd}": 1.0}, {f"shin_{sd}": 1.0}, {f"shin_{sd}": 0.5, f"tarsus_{sd}": 0.5}], "coat")
            S.loft("tarsus", [(-0.5, yy, 8.5), (0.5, yy, 4.5), (1.5, yy, 1.0)], [0.85, 0.8, 0.75], [0.85, 0.8, 0.75], X,
                   [{f"shin_{sd}": 0.4, f"tarsus_{sd}": 0.6}, {f"tarsus_{sd}": 1.0}, {f"tarsus_{sd}": 0.5, f"toes_{sd}": 0.5}], "leg", n=7)
            ball = Vector((1.5, yy, 0.55))
            for yaw, L in ((-28, 5.0), (0, 5.8), (28, 5.0)):
                d = Quaternion(Z, math.radians(yaw)) @ X
                S.loft("toe", [ball, ball + d * (L * 0.5), ball + d * L], [0.6, 0.5, 0], [0.5, 0.45, 0], Z, f"toes_{sd}", "leg", n=6)
            S.loft("toe", [ball, ball + Vector((-1.4, 0, 0)), ball + Vector((-2.6, 0, 0))], [0.55, 0.45, 0], [0.5, 0.4, 0], Z,
                   f"toes_{sd}", "leg", n=6)
    S.parts_fn = parts
    S.variants = {"A": {"coat": "#EEEBE2", "wing": "#E4E0D4", "tailf": "#E8E4D8", "hackle": "#F2EFE6", "comb": "#C42B22",
                        "beak": "#E8B83A", "leg": "#E3B23C", "eye": "#141010"},
                  "B": {"coat": "#8B4A23", "wing": "#77391A", "tailf": "#2A1E17", "hackle": "#B8782F", "comb": "#C42B22",
                        "beak": "#D9B26A", "leg": "#D9AE4A", "eye": "#141010"}}
    S.anim = dict(neck=[("neck_01", 0.3), ("neck_02", 0.3), ("head", 0.4)], look=40, look_pitch=-3, look_ramp=0.1, tilt=22,
                  breaths=4, breath_z=0.12, breath_pitch=0.8, ears=[], ear_flick=0, tail=["tail_01"], tail_swish=6,
                  graze=dict(pre={"pelvis": 28, "spine_01": 10}, neck=[("neck_01", 0.7), ("neck_02", 0.3)], head_deg=70, between=0.6),
                  graze_z=0.4, peck=True, chew=0, chews=0, graze_yaw=0,
                  walk=dict(T=0.7, v=35, bob=0.6, nod=0, roll=2.5, tail=4, headbob=True,
                            phase={"leg_l": 0.0, "leg_r": 0.5},
                            gait={"leg": dict(duty=0.6, height=4, tilt=55, fold=40)}))
    return S


def rabbit():
    S = Spec("Rabbit", res=0.42, body_tris=4900, sole_band=0.25, rigid=(0.8, 2.0))
    S.bone("root", None, (0, 0, 0), (0, 0, 6))
    S.bone("pelvis", "root", (-11, 0, 12), (0, 0, 12.5))
    S.bone("spine_01", "pelvis", (0, 0, 12.5), (8, 0, 13.5))
    S.bone("neck_01", "spine_01", (8, 0, 13.5), (10.5, 0, 17))
    S.bone("head", "neck_01", (10.5, 0, 17), (19, 0, 15.8))
    S.bone("jaw", "head", (12.5, 0, 14.5), (17.5, 0, 13.2))
    for sd, y in SIDES: S.bone(f"ear_{sd}", "head", (10.5, 1.8 * y, 20.5), (7.2, 3.2 * y, 32.3))
    S.bone("tail_01", "pelvis", (-15, 0, 10), (-19, 0, 10))
    S.ell((-5.5, 0, 11.5), (11.5, 8, 9), "pelvis", rot=(10, 0, 0))
    S.ball((-7, 0, 14), 7.5, "pelvis")
    S.ell((5, 0, 11.5), (7.5, 6.5, 7.5), "spine_01")
    S.ell((12, 0, 17.5), (5.8, 4.4, 5), "head", rot=(15, 0, 0))
    S.ell((13.2, 0, 15.5), (4.4, 5.0, 3.8), "head")
    S.ell((16.3, 0, 15.6), (2.6, 3.3, 2.6), "head")
    S.ball((18.8, 0, 16.2), 0.85, "head", "nose", s=4.0)
    S.ball((15, 0, 13.8), 2.1, "jaw")
    S.ball((-17.2, 0, 9.5), 2.7, "tail_01", "tail", s=3.0)
    for sd, y in SIDES:
        S.ell((-7, 4.5 * y, 8), (7.5, 4, 6.5), f"thigh_{sd}")                    # the haunch
        Pf = S.leg("front", sd, 3.2 * y, [(7, 10.5), (3.5, 6.5), (8.5, 1.2), (11.5, 0.0)], "spine_01", ["upperarm", "forearm", "paw"], 1)
        Pr = S.leg("hind", sd, 5.0 * y, [(-8, 10), (-1, 6.5), (-11, 2.0), (-0.5, 0.0)], "pelvis", ["thigh", "shin", "foot"], -1)
        S.cap(Pf[0], Pf[1], 2.0, f"upperarm_{sd}"); S.cap(Pf[1], Pf[2], 1.35, f"forearm_{sd}", s=3.0)
        S.ell((9.8, 3.2 * y, 0.95), (2.1, 1.2, 0.95), f"paw_{sd}", s=3.0)
        S.cap(Pr[1], Pr[2], 1.8, f"shin_{sd}")
        S.ell((-5.7, 5.0 * y, 1.25), (5.8, 1.7, 1.25), f"foot_{sd}", s=3.0)

    def parts(S):
        for sd, y in SIDES:
            S.loft("ear", [(10.5, 1.8 * y, 20.5), (9.6, 2.3 * y, 24.5), (8.3, 2.8 * y, 29), (7.2, 3.2 * y, 32.3)], [1.4, 2.5, 2.1, 0],
                   [0.55, 0.5, 0.4, 0], (0.8, 0.55 * y, 0.1), f"ear_{sd}", "coat")
            S.sphere("eye", S.snap((14.4, 4 * y, 18.4), (0.3, y, 0.15), 0.35), 1.0, "head", "eye", axis=Vector((0.3, y, 0.15)), n=8, m=5)
    S.parts_fn = parts
    S.variants = {"A": {"coat": "#8A7158", "belly": "#E6DED2", "tail": "#F2EEE8", "ear_in": "#C99A92", "nose": "#B98480", "eye": "#0D0B0A"},
                  "B": {"coat": "#8C8A86", "belly": "#DAD7D2", "tail": "#ECEBE8", "ear_in": "#C9A09C", "nose": "#B98480", "eye": "#0D0B0A"},
                  "C": {"coat": "#EEEDE8", "belly": "#F4F2EE", "tail": "#F6F4F0", "ear_in": "#E6B4B0", "nose": "#D89A98", "eye": "#3A0E0E"}}

    def pattern(v, c):
        tg, P, N, part = c["tags"], c["centers"], c["normals"], c["part"]
        under = np.isin(c["dom"], ["pelvis", "spine_01", "neck_01", "head", "jaw"])
        tg[(tg == "coat") & (part == "body") & under & (N[:, 2] < -0.72) & (P[:, 2] < 8)] = "belly"
        tg[(part == "ear") & (N[:, 0] > 0.3)] = "ear_in"
    S.pattern = pattern
    S.anim = dict(neck=[("neck_01", 0.5), ("head", 0.5)], look=25, look_pitch=-4, breaths=5, breath_z=0.12, breath_pitch=1.2,
                  ears=["ear_l", "ear_r"], ear_flick=30, tail=["tail_01"], tail_swish=10, nose_twitch=True,
                  graze=dict(pre={"spine_01": 14}, neck=[("neck_01", 1.0)], head_deg=50), graze_z=0.6,
                  chew=6, chews=16, graze_yaw=6,
                  walk=dict(T=0.6, v=50, bob=1.0, nod=4, roll=0, tail=8, hop=True,
                            phase={"front_l": 0.0, "front_r": 0.08, "hind_l": 0.55, "hind_r": 0.57},
                            gait={"front": dict(duty=0.5, height=2.0, tilt=15, fold=0), "hind": dict(duty=0.4, height=1.8, tilt=8, fold=0)}))
    return S


def horse():
    """the ridable horse (the user's list of 2026-11-08b, its eighth phase: "make a rideable horse for a player to buy and ride
    with increased speed across the wilderness"; built here as the farm animals are, the user's choice): a riding horse about
    155 cm at the withers, a long neck carried up, a mane and a long tail of hair, a saddle on its back and a `saddle` bone the
    rider sits on (her root on it: the Animals pack's rider clips put her pelvis there); clips Idle, Graze, Walk and Run (a
    gallop: the hind feet, then the fore, a short stance)"""
    S = Spec("Horse", res=1.8, body_tris=5200, sole_band=1.2, hoof_h=9.0, rigid=(9.0, 10.0))
    S.bone("root", None, (0, 0, 0), (0, 0, 30))
    S.bone("pelvis", "root", (-60, 0, 140), (-8, 0, 144))
    S.bone("spine_01", "pelvis", (-8, 0, 144), (36, 0, 148))
    S.bone("spine_02", "spine_01", (36, 0, 148), (52, 0, 146))
    S.bone("neck_01", "spine_02", (44, 0, 132), (74, 0, 160))
    S.bone("neck_02", "neck_01", (74, 0, 160), (96, 0, 186))
    S.bone("head", "neck_02", (96, 0, 186), (140, 0, 150))
    S.bone("jaw", "head", (104, 0, 168), (132, 0, 148))
    for sd, y in SIDES: S.bone(f"ear_{sd}", "head", (99, 6 * y, 196), (102, 9.5 * y, 214))
    S.bone("tail_01", "pelvis", (-82, 0, 147), (-90, 0, 130))
    S.bone("tail_02", "tail_01", (-90, 0, 130), (-94, 0, 104))
    S.bone("tail_03", "tail_02", (-94, 0, 104), (-94, 0, 72))
    S.bone("saddle", "spine_01", (-4, 0, 156), (-4, 0, 168))          # (the rider's seat: no skin on it)
    # the body: barrel, chest, withers, rump, belly; the neck and its crest; the long head
    S.ell((-10, 0, 122), (60, 29, 30), "spine_01")
    S.ell((38, 0, 120), (26, 26, 31), "spine_02")
    S.ball((40, 0, 144), 14, "spine_02")
    S.ell((-58, 0, 128), (25, 26, 24), "pelvis")
    S.ell((-10, 0, 108), (46, 26, 19), "spine_01")
    S.cap((50, 0, 134), (76, 0, 162), 17, "neck_01")
    S.cap((76, 0, 162), (94, 0, 184), 13, "neck_02")
    S.ell((98, 0, 188), (10, 10, 11), "head")
    S.cap((100, 0, 180), (121, 0, 166), 10, "head")
    S.cap((121, 0, 166), (136, 0, 153), 8.5, "head")
    S.ball((139, 0, 150), 8.5, "head", "muzzle")
    S.cap((104, 0, 171), (128, 0, 153), 7, "jaw")
    for sd, y in SIDES:
        S.ell((-56, 15 * y, 116), (20, 12, 28), f"thigh_{sd}")
        # (the joints bent: a near-straight leg left the IK no sweep, 16 cm a half stride (the first build))
        Pf = S.leg("front", sd, 16 * y, [(44, 136), (22, 102), (34, 56), (42, 16), (44, 0)], "spine_02", quad_names(True), 1)
        Pr = S.leg("rear", sd, 17 * y, [(-58, 140), (-44, 100), (-72, 58), (-64, 15), (-62, 0)], "pelvis", quad_names(False), -1)
        hooved_leg_blobs(S, Pf, True, 14, 7.6, 4.8, 6.2, sd)
        hooved_leg_blobs(S, Pr, False, 0, 8.2, 4.8, 6.2, sd)

    def parts(S):
        for sd, y in SIDES:
            S.loft("ear", [(99, 6 * y, 196), (100, 8 * y, 203), (101, 9 * y, 209), (102, 9.5 * y, 214)], [3.0, 3.4, 2.2, 0],
                   [1.5, 1.2, 0.9, 0], (1, 0, 0.2), f"ear_{sd}", "coat")
            S.sphere("eye", S.snap((108, 9 * y, 182), (0.2, y, 0.3), 0.8), 2.2, "head", "eye", axis=Vector((0.2, y, 0.3)), n=8, m=5)
            S.sphere("nostril", S.snap((142, 4 * y, 150), (1, 0.3 * y, 0), 0.3), 1.8, "head", "nostril", axis=X, flat=0.5, n=8, m=4)
        # the mane along the crest, standing up; the tail's hair, spreading
        mp = [(95, 0, 200), (86, 0, 192), (76, 0, 182), (65, 0, 171), (54, 0, 161), (44, 0, 155)]
        S.loft("mane", mp, [3.5, 4.0, 4.2, 4.2, 3.6, 0], [9, 13, 14, 14, 11, 0], Z, S.chain_w(mp, ["head", "neck_02", "neck_01", "spine_02"]), "mane")
        tp = [(-82, 0, 147), (-88, 0, 138), (-92, 0, 124), (-94, 0, 108), (-95, 0, 92), (-95, 0, 78), (-94, 0, 70)]
        tr = [4.0, 5.0, 6.0, 7.0, 7.5, 6.0, 0]
        S.loft("tail", tp, tr, tr, X, S.chain_w(tp, ["tail_01", "tail_02", "tail_03"]), "mane")
        # the saddle: a leather seat on the back, its blanket under it
        S.sphere("saddle", (-3, 0, 153), 24, "spine_01", "saddle", axis=Z, flat=0.22, n=14, m=6)
        S.sphere("blanket", (-3, 0, 150), 29, "spine_01", "blanket", axis=Z, flat=0.12, n=14, m=6)
    S.parts_fn = parts
    S.variants = {"A": {"coat": "#6B3A1E", "mane": "#17110E", "muzzle": "#3A2A24", "nostril": "#2A1A16", "hoof": "#2A2420", "eye": "#0C0A0A",
                        "saddle": "#4A2814", "blanket": "#7A1E1A"},
                  "B": {"coat": "#B9B5AE", "mane": "#EAE6DF", "muzzle": "#8A8580", "nostril": "#3A3230", "hoof": "#4A4440", "eye": "#0C0A0A",
                        "saddle": "#3A2414", "blanket": "#1E3A6A"}}

    def pattern(v, c):                                          # a bay's black points: the legs below the knees
        if v == "A":
            tg, P = c["tags"], c["centers"]
            tg[(tg == "coat") & (P[:, 2] < 48)] = "mane"
    S.pattern = pattern
    S.anim = dict(neck=[("neck_01", 0.35), ("neck_02", 0.35), ("head", 0.3)], look=28, look_pitch=-4, breaths=2, breath_z=0.6,
                  breath_pitch=0.4, ears=["ear_l", "ear_r"], ear_flick=25, tail=["tail_01", "tail_02", "tail_03"], tail_swish=12,
                  graze=None,                                     # (its long neck curled under its chest: the horse has no graze)
                  walk=dict(T=1.1, v=150, bob=2.0, nod=4, roll=1.2, tail=6,
                            phase={"rear_l": 0.0, "front_l": 0.25, "rear_r": 0.5, "front_r": 0.75},
                            gait={"front": dict(duty=0.62, height=13, tilt=34, fold=45), "rear": dict(duty=0.62, height=13, tilt=34, fold=40)}),
                  run=dict(T=0.6, v=900, bob=2, nod=7, roll=0.8, tail=14,
                           phase={"rear_l": 0.0, "rear_r": 0.1, "front_r": 0.45, "front_l": 0.55},
                           # (a swing of 28 cm and a fold of 95 overreached the legs by 17 cm and crushed their faces: lower)
                           gait={"front": dict(duty=0.38, height=17, tilt=50, fold=60), "rear": dict(duty=0.38, height=15, tilt=45, fold=55)}))
    return S


ANIMALS = {"chicken": chicken, "rabbit": rabbit, "goat": goat, "pig": pig, "cow": cow, "horse": horse}


# ---------------------------------------------------------------- the mesh
def field(b, P):
    """an element's field at points P (n,3), as Blender's metaball tessellator computes it"""
    Rm = np.array(b["q"].to_matrix())
    d = (P - np.array(b["co"])) @ Rm
    if b["type"] == 'CAPSULE':
        sx = b["size"][0]; d[:, 0] = np.sign(d[:, 0]) * np.maximum(np.abs(d[:, 0]) - sx, 0.0)
    elif b["type"] == 'ELLIPSOID':
        d = d / np.array(b["size"])
    f = 1.0 - (d * d).sum(1) / (b["R"] ** 2)
    return np.where(f > 0.0, b["s"] * np.maximum(f, 0.0) ** 3, 0.0)


def body_mesh(S):
    """the metaball body as a decimated triangle mesh: vertices (n,3), triangles (m,3), triangles before decimation"""
    sc = bpy.context.scene
    mb = bpy.data.metaballs.new(S.name + "_mb"); mb.resolution = S.res; mb.render_resolution = S.res; mb.threshold = THRESH
    ob = bpy.data.objects.new(S.name + "_mb", mb); sc.collection.objects.link(ob)
    for b in S.blobs:
        e = mb.elements.new(type=b["type"]); e.co = b["co"]; e.rotation = b["q"]; e.radius = b["R"]; e.stiffness = b["s"]
        e.size_x, e.size_y, e.size_z = b["size"]
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(ob); bpy.data.metaballs.remove(mb)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=S.res * 0.05)
    bm.to_mesh(me); bm.free()
    n0 = len(me.polygons)
    tmp = bpy.data.objects.new("dec", me); sc.collection.objects.link(tmp)
    mod = tmp.modifiers.new("dec", 'DECIMATE'); mod.decimate_type = 'COLLAPSE'; mod.ratio = min(1.0, S.body_tris / n0)
    mod.use_collapse_triangulate = True
    bpy.context.view_layer.update()
    me2 = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp); bpy.data.meshes.remove(me)
    bm = bmesh.new(); bm.from_mesh(me2); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(me2); bm.free()
    co = np.empty(len(me2.vertices) * 3); me2.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    tris = np.array([tuple(p.vertices) for p in me2.polygons], dtype=np.int64)
    bpy.data.meshes.remove(me2)
    return co, tris, n0


def build_geometry(S):
    """the body and the parts as one triangle mesh with its skin weights and each face's part and colour tag"""
    names = [b[0] for b in S.bones]; bi = {n: i for i, n in enumerate(names)}
    co, tris, n0 = body_mesh(S)
    S.surf = BVHTree.FromPolygons([Vector(v) for v in co], [tuple(t) for t in tris])
    S.parts = []
    S.parts_fn(S)
    nb = len(co)
    # the body's weights: each bone's share of the field that makes the surface there
    W = np.zeros((nb, len(names)))
    for b in S.blobs: W[:, bi[b["bone"]]] += field(b, co)
    tot = W.sum(1); bad = tot <= 1e-9
    if bad.any():                                                   # (decimation can move a vertex off the field)
        for i in np.nonzero(bad)[0]:
            j = min(range(len(S.blobs)), key=lambda k: (Vector(co[i]) - S.blobs[k]["co"]).length)
            W[i, bi[S.blobs[j]["bone"]]] = 1.0
        tot = W.sum(1)
    W /= tot[:, None]
    # ... smoothed along the mesh's edges, twice
    e = np.concatenate([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    for _ in range(2):
        acc = np.zeros_like(W); cnt = np.zeros(nb)
        np.add.at(acc, e[:, 0], W[e[:, 1]]); np.add.at(cnt, e[:, 0], 1)
        np.add.at(acc, e[:, 1], W[e[:, 0]]); np.add.at(cnt, e[:, 1], 1)
        W = 0.5 * W + 0.5 * acc / np.maximum(cnt, 1)[:, None]
    # the body's faces: the colour tag of the strongest field at the face's middle
    cen = co[tris].mean(1)
    mats = sorted({b["mat"] for b in S.blobs})
    FT = np.zeros((len(tris), len(mats)))
    for b in S.blobs: FT[:, mats.index(b["mat"])] += field(b, cen)
    tags = np.array([mats[i] for i in FT.argmax(1)], dtype=object)
    if S.hoof_h > 0: tags[(tags == "coat") & (cen[:, 2] < S.hoof_h)] = "hoof"
    part = np.array(["body"] * len(tris), dtype=object)
    # the parts appended
    V = [co]; T = [tris]; Wl = [W]; TG = [tags]; PT = [part]; off = nb
    for p in S.parts:
        pv = np.array([tuple(v) for v in p["verts"]]); pw = np.zeros((len(pv), len(names)))
        for i, wd in enumerate(p["w"]):
            for b, w in wd.items(): pw[i, bi[b]] += w
        V.append(pv); T.append(np.array(p["tris"]) + off); Wl.append(pw)
        TG.append(np.array(p["mat"], dtype=object)); PT.append(np.array([p["name"]] * len(p["tris"]), dtype=object)); off += len(pv)
    V = np.concatenate(V); T = np.concatenate(T); W = np.concatenate(Wl); tags = np.concatenate(TG); part = np.concatenate(PT)
    V[V[:, 2] < S.sole_band, 2] = 0.0                               # flat soles on the ground
    # the planted bones hold their hoof / paw / foot zone alone (no sliding from the bone above)
    if S.rigid[0] > 0:
        for lg in S.legs:
            pl = lg["bones"][3]; h, t = S.bone_seg(pl)
            near = (V[:, 2] < S.rigid[0]) & (seg_dist(V, np.array(h), np.array(t)) < S.rigid[1])
            W[near] = 0.0; W[near, bi[pl]] = 1.0
    # at most four bones a vertex, shares under 1 % dropped
    idx = np.argsort(-W, axis=1)
    keep = np.zeros_like(W, dtype=bool); np.put_along_axis(keep, idx[:, :4], True, axis=1)
    W = np.where(keep & (W >= 0.01), W, 0.0); W /= W.sum(1)[:, None]
    return dict(V=V, T=T, W=W, tags=tags, part=part, names=names, body_tris_raw=n0, body_tris=len(tris), body_verts=nb)


# ---------------------------------------------------------------- materials
def material(name, hexcol):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    lin = srgb(hexcol)
    try:
        if m.node_tree is None: m.use_nodes = True
    except Exception: pass
    bsdf = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m.node_tree else None
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = (*lin, 1.0); bsdf.inputs["Roughness"].default_value = 0.8
        if "Specular IOR Level" in bsdf.inputs: bsdf.inputs["Specular IOR Level"].default_value = 0.3
    m.diffuse_color = (*lin, 1.0); m.roughness = 0.8
    return m


# ---------------------------------------------------------------- the skeleton and its posing
def build_armature(S, sc):
    ad = bpy.data.armatures.new("ARM_" + S.name); arm = bpy.data.objects.new("ARM_" + S.name, ad); sc.collection.objects.link(arm)
    for o in sc.objects: o.select_set(False)
    arm.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    for name, parent, h, t in S.bones:
        eb = ad.edit_bones.new(name); eb.head = h; eb.tail = t
        d = (t - h).normalized(); eb.align_roll(Z if abs(d.z) < 0.7 else -X)
        if parent: eb.parent = ad.edit_bones[parent]
        eb.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
    return arm


class Rig:
    """poses as transforms of the reference pose: each bone's turn Q (in the animal's axes) about its own head, and where
    its head is; legs solved from where their planted bone stands"""

    def __init__(self, arm, S):
        B = arm.data.bones
        self.arm = arm; self.S = S
        self.order = [b.name for b in sorted(B, key=lambda b: len(b.parent_recursive))]
        self.parent = {b.name: (b.parent.name if b.parent else None) for b in B}
        self.rest = {b.name: b.matrix_local.copy() for b in B}
        self.rest_inv = {n: m.inverted() for n, m in self.rest.items()}
        self.h0 = {b.name: b.head_local.copy() for b in B}
        self.t0 = {b.name: b.tail_local.copy() for b in B}
        self.leg_of = {}
        for lg in S.legs:
            for b in lg["bones"]:
                if b: self.leg_of[b] = lg
        self.stretch = {}

    def ik2(self, H, A, L1, L2, bend):
        d = A - H; dist = d.length; over = max(0.0, dist - (L1 + L2) * 0.9995)
        dist = min(max(dist, abs(L1 - L2) + 1e-3), (L1 + L2) * 0.9995)
        u = d.normalized()
        ca = (L1 * L1 + dist * dist - L2 * L2) / (2 * L1 * dist); a = math.acos(min(1.0, max(-1.0, ca)))
        ax = Y - u * Y.dot(u); ax.normalize()
        knee = H + (Quaternion(ax, bend * a) @ u) * L1
        return knee, H + u * dist, over

    def solve_leg(self, lg, T, P):
        up, lo, mid, pl = lg["bones"]; h0, t0 = self.h0, self.t0
        Qp, hp = T[self.parent[up]]
        H = hp + Qp @ (h0[up] - h0[self.parent[up]])
        E, tilt, fold = P["feet"].get(lg["id"], (t0[pl].copy(), 0.0, 0.0))
        Rt = Quaternion(Y, math.radians(tilt))
        pl_head = E + Rt @ (h0[pl] - t0[pl])
        if mid:
            g = angY(pl_head - H) - angY(h0[pl] - h0[up])
            Rm = Quaternion(Y, g * lg["follow"] + math.radians(fold))
            A = pl_head - Rm @ (t0[mid] - h0[mid])
        else:
            A = pl_head
        L1 = (t0[up] - h0[up]).length; L2 = (t0[lo] - h0[lo]).length
        knee, A2, over = self.ik2(H, A, L1, L2, lg["bend"])
        self.stretch[lg["id"]] = max(self.stretch.get(lg["id"], 0.0), over)
        T[up] = ((t0[up] - h0[up]).rotation_difference(knee - H), H)
        T[lo] = ((t0[lo] - h0[lo]).rotation_difference(A2 - knee), knee)
        if mid: T[mid] = (Rm, A)
        T[pl] = (Rt, pl_head)

    def solve(self, P):
        T = {}
        for n in self.order:
            if n in T: continue
            lg = self.leg_of.get(n)
            if lg is not None:
                self.solve_leg(lg, T, P); continue
            p = self.parent[n]
            if p is None: Qp, h1 = Quaternion(), self.h0[n].copy()
            else:
                Qp, hp = T[p]; h1 = hp + Qp @ (self.h0[n] - self.h0[p])
            h1 = h1 + P["off"].get(n, Vector())
            q = P["rot"].get(n)
            T[n] = ((Qp @ q) if q is not None else Qp.copy(), h1)
        return T

    def point(self, T, bone, x):
        Q, h1 = T[bone]; return h1 + Q @ (Vector(x) - self.h0[bone])

    def basis(self, T):
        M = {n: Matrix.Translation(h1) @ Q.to_matrix().to_4x4() @ Matrix.Translation(-self.h0[n]) for n, (Q, h1) in T.items()}
        out = {}
        for n in self.order:
            p = self.parent[n]; Mp = M[p] if p else I4
            Bm = self.rest_inv[n] @ Mp.inverted() @ M[n] @ self.rest[n]
            l, r, _ = Bm.decompose(); out[n] = (l, r, ONE.copy())
        return out


def set_basis(arm, F):
    for pb in arm.pose.bones:
        l, q, s = F[pb.name]; pb.location = l; pb.rotation_quaternion = q; pb.scale = s
    bpy.context.view_layer.update()


def empty_pose(): return {"off": {}, "rot": {}, "feet": {}}


def addrot(rig, P, b, q):
    if b in rig.h0: P["rot"][b] = q @ P["rot"].get(b, Quaternion())


# ---------------------------------------------------------------- the clips
def graze_base(rig, A, s, head_deg, k=1.0):
    """the grazing pose: the body's turns (A['graze']['pre'], times k), the neck turned down by s degrees shared along
    its bones, and the head then set to point head_deg below the horizontal"""
    Gz = A["graze"]; P = empty_pose()
    for b, d in Gz["pre"].items(): addrot(rig, P, b, qrot(pitch=d * k))
    for b, share in Gz["neck"]: addrot(rig, P, b, qrot(pitch=s * share))
    T = rig.solve(P); d = T["head"][0] @ (rig.t0["head"] - rig.h0["head"])
    addrot(rig, P, "head", qrot(pitch=head_deg - math.degrees(math.atan2(-d.z, d.x))))
    return P


def mouth_low(rig, T):
    """the lowest of the head's and jaw's own vertices (held 90 % or more by them), moved with their bone"""
    z = 1e9
    for b, pts in rig.mouth_pts.items():
        if len(pts) == 0: continue
        Q, h1 = T[b]; R = np.array(Q.to_matrix())
        z = min(z, float(((pts - np.array(rig.h0[b])) @ R.T)[:, 2].min() + h1.z))
    return z


def graze_g(rig, A, base_z):
    """the neck's turn (degrees) that brings the mouth down to base_z: searched on a grid (past straight down the
    mouth comes up again), then halved down; out of reach, as low as it goes"""
    hd = A["graze"]["head_deg"]

    def mz(g): return mouth_low(rig, rig.solve(graze_base(rig, A, g, hd)))
    gs = [i * 2.0 for i in range(91)]; zs = [mz(g) for g in gs]
    k = next((i for i, z in enumerate(zs) if z <= base_z), None)
    if k is None:
        k = int(np.argmin(zs)); return gs[k], zs[k]             # (out of reach: as low as it goes)
    lo, hi = gs[max(k - 1, 0)], gs[k]
    for _ in range(24):
        m = 0.5 * (lo + hi)
        if mz(m) > base_z: lo = m
        else: hi = m
    return hi, mz(hi)


def look(rig, P, A, yaw, pitch=0.0, roll=0.0):
    for b, share in A["neck"]: addrot(rig, P, b, qrot(pitch=pitch * share, yaw=yaw * share, roll=roll * share))


def ears_tail(rig, P, A, t, L, flicks, swish_amp, swish_n):
    for b, t0, sgn in flicks:
        if b in rig.h0:
            f = bump(t, t0, 0.32); y = 1.0 if b.endswith("_l") else -1.0
            addrot(rig, P, b, qrot(pitch=-0.5 * A["ear_flick"] * f * sgn, yaw=A["ear_flick"] * f * y * sgn))
    for i, b in enumerate(A["tail"]):
        addrot(rig, P, b, qrot(roll=swish_amp * math.sin(2 * math.pi * swish_n * t / L - 0.7 * i)))


def idle_pose(rig, A, t):
    L = IDLE_LEN; P = empty_pose()
    br = math.sin(2 * math.pi * A["breaths"] * t / L)
    P["off"]["pelvis"] = Vector((0, 0, A["breath_z"] * br))
    addrot(rig, P, "spine_01", qrot(pitch=-A["breath_pitch"] * br))
    r = A.get("look_ramp", 0.45)
    if A.get("tilt"):                                           # the chicken: quick head moves, one with a tilt
        yaw = A["look"] * (hold(t, 0.4, 1.3, r) - 0.8 * hold(t, 2.5, 3.4, r) + 0.4 * hold(t, 3.9, 4.6, r))
        roll = A["tilt"] * hold(t, 1.5, 2.3, r)
        look(rig, P, A, yaw, A["look_pitch"] * hold(t, 0.4, 2.3, r), roll)
    else:
        yaw = A["look"] * (hold(t, 0.5, 2.0, r) - 0.85 * hold(t, 2.7, 4.3, r))
        look(rig, P, A, yaw, A["look_pitch"] * (hold(t, 0.5, 2.0, r) + hold(t, 2.7, 4.3, r)))
    if A.get("nose_twitch"):                                    # the rabbit's nose: bursts of quick twitches
        tw = (hold(t, 0.2, 1.0, 0.1) + hold(t, 2.4, 3.1, 0.1) + hold(t, 4.0, 4.7, 0.1)) * math.sin(2 * math.pi * 8 * t)
        addrot(rig, P, "jaw", qrot(pitch=2.5 * tw))
    ears_tail(rig, P, A, t, L, [("ear_l", 1.2, 1), ("ear_r", 3.5, 1), ("ear_l", 4.4, -0.6)], A["tail_swish"], 2)
    return P


def graze_pose(rig, A, t, g0):
    L = GRAZE_LEN; P = empty_pose()
    if A.get("peck"):                                           # pecks: down in 0.1 s, up in 0.2 s, four a loop
        pk = 0.0
        for t0 in (0.4, 1.3, 2.1, 3.2):
            u = t - t0
            if 0 <= u < 0.1: pk = max(pk, smooth(u / 0.1))
            elif 0.1 <= u < 0.16: pk = max(pk, 1.0)
            elif 0.16 <= u < 0.36: pk = max(pk, 1.0 - smooth((u - 0.16) / 0.2))
        hd = A["graze"]["head_deg"]; up = A["graze"]["between"]
        P = graze_base(rig, A, g0 * (up + (1 - up) * pk), 30.0 + (hd - 30.0) * pk, up + (1 - up) * pk)
        look(rig, P, A, 18 * math.sin(2 * math.pi * t / L), 0, 10 * math.sin(2 * math.pi * 2 * t / L))
    else:
        tear = sum(bump(t, t0, 0.5) for t0 in (0.9, 2.9))           # a tug at the grass
        P = graze_base(rig, A, g0, A["graze"]["head_deg"])
        addrot(rig, P, "head", qrot(pitch=-6 * tear))
        look(rig, P, A, A["graze_yaw"] * math.sin(2 * math.pi * t / L))
        addrot(rig, P, "jaw", qrot(pitch=A["chew"] * (0.5 - 0.5 * math.cos(2 * math.pi * A["chews"] * t / L))))
    br = math.sin(2 * math.pi * 2 * t / L)
    P["off"]["pelvis"] = Vector((0, 0, A["breath_z"] * br))
    ears_tail(rig, P, A, t, L, [("ear_r", 0.6, 1), ("ear_l", 2.2, 1)], A["tail_swish"], 2)
    return P


def walk_targets(rig, W, t):
    """each foot's ground point, tilt and fold at time t of the stride, and whether it is in stance"""
    feet, stance, since = {}, {}, {}
    T = W["T"]
    for lg in rig.S.legs:
        G = W["gait"][lg["kind"]]; beta = G["duty"]; S = W["stride"][lg["kind"]]
        p = (t / T + W["phase"][lg["id"]]) % 1.0
        E0 = rig.t0[lg["bones"][3]].copy()
        if p < beta:
            u = p / beta; dx = S * (0.5 - u); dz = 0.0; tilt = fold = 0.0
            stance[lg["id"]] = 0.12 < u < 0.88; since[lg["id"]] = u * beta * T
        else:
            u = (p - beta) / (1.0 - beta); s = smooth(u)
            dx = S * (s - 0.5); lift = math.sin(math.pi * u)
            dz = G["height"] * lift; tilt = G["tilt"] * lift; fold = G["fold"] * lift
            stance[lg["id"]] = False
        feet[lg["id"]] = (E0 + Vector((dx, 0, dz)), tilt, fold)
    return feet, stance, since


def walk_pose(rig, A, t, key="walk"):
    W = A[key]; T = W["T"]; P = empty_pose()
    P["feet"] = walk_targets(rig, W, t)[0]
    w2 = 2 * math.pi * 2 * t / T
    if W.get("hop"):                                           # the rabbit: up as the hind feet push off, the back flexing
        hp = (t / T + W["phase"]["hind_l"]) % 1.0
        up = math.sin(math.pi * (hp - W["gait"]["hind"]["duty"]) / (1 - W["gait"]["hind"]["duty"])) if hp >= W["gait"]["hind"]["duty"] else 0.0
        P["off"]["pelvis"] = Vector((0, 0, W["bob"] * up))
        addrot(rig, P, "pelvis", qrot(pitch=-4 * up))
        addrot(rig, P, "spine_01", qrot(pitch=5 * math.sin(2 * math.pi * t / T)))
        addrot(rig, P, "neck_01", qrot(pitch=-W["nod"] * math.sin(2 * math.pi * t / T)))
    else:
        P["off"]["pelvis"] = Vector((0, 0, W["bob"] * math.cos(w2)))
        addrot(rig, P, "pelvis", qrot(roll=W["roll"] * math.sin(2 * math.pi * t / T)))
        addrot(rig, P, "spine_01", qrot(yaw=1.5 * math.sin(2 * math.pi * t / T)))
        if W.get("headbob"):                                   # the chicken holds its head still, then thrusts it forward
            ph = (2 * t / T) % 1.0
            d = 0.5 - ph / 0.7 if ph < 0.7 else -0.5 + smooth((ph - 0.7) / 0.3)
            D = W["v_eff"] * T * 0.5
            a = math.degrees(d * D / 9.0)
            addrot(rig, P, "neck_01", qrot(pitch=-a)); addrot(rig, P, "head", qrot(pitch=a * 0.8))
        else:
            addrot(rig, P, "neck_01", qrot(pitch=W["nod"] * math.cos(w2 + 0.8)))
            addrot(rig, P, "head", qrot(pitch=-0.5 * W["nod"] * math.cos(w2 + 0.8)))
    for i, b in enumerate(A["tail"]):
        addrot(rig, P, b, qrot(roll=W["tail"] * math.sin(2 * math.pi * t / T - 0.8 * i)))
    for b in A["ears"]:
        addrot(rig, P, b, qrot(pitch=-3 * math.cos(w2)))
    return P


def plan_stride(rig, A, key="walk"):
    """the longest stance sweep each leg reaches without its IK clamping (with the body up by the bob), and the walk
    speed that comes from it: the wanted speed or less (key: "run" for the horse's gallop)"""
    W = A[key]; T = W["T"]; vmax = W["v"]; lim = {}
    for lg in rig.S.legs:
        G = W["gait"][lg["kind"]]; E0 = rig.t0[lg["bones"][3]].copy()

        def over(dx):
            P = empty_pose(); P["off"]["pelvis"] = Vector((0, 0, W["bob"]))
            P["feet"][lg["id"]] = (E0 + Vector((dx, 0, 0)), 0.0, 0.0)
            rig.stretch = {}; rig.solve(P); return rig.stretch.get(lg["id"], 0.0)
        half = []
        for sgn in (1.0, -1.0):
            lo, hi = 0.0, 200.0
            for _ in range(30):
                m = 0.5 * (lo + hi)
                if over(sgn * m) > 1e-4: hi = m
                else: lo = m
            half.append(lo)
        h = min(half) * 0.92; lim[lg["id"]] = round(h, 2)
        vmax = min(vmax, 2 * h / (G["duty"] * T))
    W["v_eff"] = vmax
    W["stride"] = {k: vmax * G["duty"] * T for k, G in W["gait"].items()}
    rig.stretch = {}
    return lim


def make_clips(rig, S):
    A = S.anim; rig.stretch = {}
    g0, mz = graze_g(rig, A, A["graze_z"]) if A.get("graze") else (0.0, 0.0)
    lim = plan_stride(rig, A)
    lim_run = plan_stride(rig, A, "run") if "run" in A else None
    clips, info = {}, {}
    todo = [("Idle", IDLE_LEN, lambda t: idle_pose(rig, A, t))]
    if A.get("graze"): todo.append(("Graze", GRAZE_LEN, lambda t: graze_pose(rig, A, t, g0)))
    todo.append(("Walk", A["walk"]["T"], lambda t: walk_pose(rig, A, t)))
    if "run" in A: todo.append(("Run", A["run"]["T"], lambda t: walk_pose(rig, A, t, "run")))          # (the horse's gallop)
    for name, L, fn in todo:
        n = int(round(L * FPS)); rig.stretch = {}
        frames = [rig.basis(rig.solve(fn(i / FPS))) for i in range(n)]
        frames.append(frames[0])                                # the last key is the first: a seamless loop
        clips[name] = frames
        info[name] = dict(length_s=L, frames=n + 1, ik_overreach_cm={k: round(v, 3) for k, v in rig.stretch.items()})
    if "Graze" in info:
        info["Graze"]["neck_down_deg"] = round(g0, 2); info["Graze"]["head_below_horizontal_deg"] = A["graze"]["head_deg"]
        info["Graze"]["mouth_z_solved"] = round(mz, 2)
    info["Walk"]["designed_speed_cm_s"] = round(A["walk"]["v_eff"], 1)
    info["Walk"]["wanted_speed_cm_s"] = A["walk"]["v"]
    info["Walk"]["stance_sweep_cm"] = {k: round(v, 1) for k, v in A["walk"]["stride"].items()}
    info["Walk"]["half_sweep_limit_cm"] = lim
    if lim_run is not None:
        info["Run"]["designed_speed_cm_s"] = round(A["run"]["v_eff"], 1); info["Run"]["wanted_speed_cm_s"] = A["run"]["v"]
        info["Run"]["stance_sweep_cm"] = {k: round(v, 1) for k, v in A["run"]["stride"].items()}; info["Run"]["half_sweep_limit_cm"] = lim_run
    return clips, info


# ---------------------------------------------------------------- measuring on the skinned mesh
def mesh_co(ob):
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh(); a = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", a); ev.to_mesh_clear()
    return a.reshape(-1, 3)


def measure(S, rig, arm, ob, G, clips):
    V0, W, names = G["V"], G["W"], G["names"]; bi = {n: i for i, n in enumerate(names)}
    soles = {}
    for lg in S.legs:
        pl = bi[lg["bones"][3]]
        idx = np.nonzero((W[:, pl] >= 0.99) & (V0[:, 2] < max(0.6, S.sole_band + 0.3)))[0]
        if len(idx) == 0:
            cand = np.nonzero(W[:, pl] > 0.5)[0]; idx = cand[np.argsort(V0[cand, 2])[:12]]
        soles[lg["id"]] = idx
    mouth_b = [bi[b] for b in ("head", "jaw") if b in bi]
    mouth_v = np.nonzero(W[:, mouth_b].sum(1) > 0.5)[0]
    edges = np.unique(np.sort(np.concatenate([G["T"][:, [0, 1]], G["T"][:, [1, 2]], G["T"][:, [2, 0]]]), axis=1), axis=0)
    L0 = np.linalg.norm(V0[edges[:, 0]] - V0[edges[:, 1]], axis=1)
    rep = {}
    for name, frames in clips.items():
        rows = []
        for F in frames:
            set_basis(arm, F); C = mesh_co(ob)
            row = {k: (C[ix, 2].min(), C[ix, :2].mean(0)) for k, ix in soles.items()}
            row["_mouth"] = C[mouth_v, 2].min(); row["_low"] = C[:, 2].min()
            Ln = np.linalg.norm(C[edges[:, 0]] - C[edges[:, 1]], axis=1); r = Ln / np.maximum(L0, 1e-6)
            row["_str"] = (float(r.max()), float(r.min()), float(np.percentile(r, 99.5)))
            row["_C"] = C if (len(rows) == 0 or len(rows) == len(frames) - 1) else None
            rows.append(row)
        R = {"lowest_vertex_z": round(min(r["_low"] for r in rows), 3),
             "edge_stretch_max": round(max(r["_str"][0] for r in rows), 3), "edge_squash_min": round(min(r["_str"][1] for r in rows), 3),
             "edge_stretch_p99_5": round(max(r["_str"][2] for r in rows), 3),
             "loop_seam_cm": round(float(np.abs(rows[0]["_C"] - rows[-1]["_C"]).max()), 4)}
        feet = {}
        if name in ("Idle", "Graze"):
            for k in soles:
                z = [r[k][0] for r in rows]; xy = np.array([r[k][1] for r in rows])
                feet[k] = {"sole_z_min": round(min(z), 3), "sole_z_max": round(max(z), 3),
                           "slide_cm": round(float(np.linalg.norm(xy - xy[0], axis=1).max()), 3)}
            if name == "Graze":
                R["mouth_lowest_z"] = round(min(r["_mouth"] for r in rows), 2)
                R["mouth_highest_z"] = round(max(r["_mouth"] for r in rows), 2)
        else:
            Wk = S.anim["run" if name == "Run" else "walk"]; speeds = []
            for k in soles:
                ts = [i / FPS for i in range(len(rows) - 1)]
                wt = [walk_targets(rig, Wk, t) for t in ts]
                st = [i for i in range(len(ts)) if wt[i][1][k]]
                x = np.array([rows[i][k][1][0] for i in st]); y = np.array([rows[i][k][1][1] for i in st])
                tt = np.array([wt[i][2][k] for i in st]); z = [rows[i][k][0] for i in st]
                a, b = np.polyfit(tt, x, 1); res = x - (a * tt + b)
                speeds.append(-a)
                feet[k] = {"stance_frames": len(st), "speed_cm_s": round(-a, 2), "off_steady_cm": round(float(np.abs(res).max()), 3),
                           "y_drift_cm": round(float(y.max() - y.min()), 3), "sole_z_min": round(min(z), 3), "sole_z_max": round(max(z), 3)}
            R["walk_speed_cm_s"] = round(float(np.mean(speeds)), 2)
        R["feet"] = feet
        rep[name] = R
    set_basis(arm, clips["Idle"][0])
    return rep


def weight_check(S, G):
    """the weights' sums and counts, and the farthest any vertex is from a bone that moves it by 10 % or more"""
    V, W, names = G["V"], G["W"], G["names"]
    far, far_b = 0.0, ""
    for j, n in enumerate(names):
        ix = np.nonzero(W[:, j] >= 0.1)[0]
        if len(ix) == 0: continue
        h, t = S.bone_seg(n); d = seg_dist(V[ix], np.array(h), np.array(t)).max()
        if d > far: far, far_b = float(d), n
    s = W.sum(1)
    return {"sum_min": round(float(s.min()), 4), "sum_max": round(float(s.max()), 4), "bones_per_vertex_max": int((W > 0).sum(1).max()),
            "unweighted_vertices": int((s < 0.99).sum()), "farthest_from_moving_bone_cm": round(far, 1), "that_bone": far_b}


# ---------------------------------------------------------------- objects, previews, export
def make_objects(S, G, arm, sc):
    me = bpy.data.meshes.new("SK_Farm_" + S.name)
    me.from_pydata([tuple(v) for v in G["V"]], [], [tuple(t) for t in G["T"]]); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons)); me.update()
    cen = np.empty(len(me.polygons) * 3); me.polygons.foreach_get("center", cen); cen = cen.reshape(-1, 3)
    nrm = np.empty(len(me.polygons) * 3); me.polygons.foreach_get("normal", nrm); nrm = nrm.reshape(-1, 3)
    names = G["names"]; W = G["W"]
    fw = W[G["T"]].sum(1); dom = np.array([names[i] for i in fw.argmax(1)], dtype=object)
    obs, slots = {}, {}
    for v, cols in S.variants.items():
        tags = G["tags"].copy()
        if S.pattern: S.pattern(v, dict(tags=tags, centers=cen, normals=nrm, dom=dom, part=G["part"]))
        used = [t for t in cols if (tags == t).any()]
        missing = sorted(set(tags) - set(cols))
        if missing: raise RuntimeError(f"{S.name} {v}: no colour for {missing}")
        m = me if v == "A" else me.copy()
        m.name = "SK_Farm_" + S.name + ("" if v == "A" else "_" + v)
        m.materials.clear()
        for t in used: m.materials.append(material(f"M_Farm_{S.name}_{v}_{t}", cols[t]))
        m.polygons.foreach_set("material_index", [used.index(t) for t in tags]); m.update()
        ob = bpy.data.objects.new(m.name, m); sc.collection.objects.link(ob)
        for n in names: ob.vertex_groups.new(name=n)
        for j, n in enumerate(names):
            vg = ob.vertex_groups[n]
            for i in np.nonzero(W[:, j] > 0)[0]: vg.add([int(i)], float(W[i, j]), 'REPLACE')
        ob.parent = arm; md = ob.modifiers.new("Armature", 'ARMATURE'); md.object = arm
        obs[v] = ob; slots[v] = {t: cols[t] for t in used}
    return obs, slots


def setup_render(sc):
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'
    sh.show_shadows = True; sh.shadow_intensity = 0.35; sh.show_cavity = True; sh.cavity_type = 'WORLD'
    sc.display.light_direction = (0.45, -0.35, 0.82)
    sc.render.resolution_x = 400; sc.render.resolution_y = 300; sc.render.film_transparent = False
    w = bpy.data.worlds.new("farm_sky"); w.color = srgb("#B9C7D3"); sc.world = w
    cam = bpy.data.objects.new("farm_cam", bpy.data.cameras.new("farm_cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.lens = 50; cam.data.clip_start = 1.0; cam.data.clip_end = 20000.0
    me = bpy.data.meshes.new("farm_ground"); s = 3000.0
    me.from_pydata([(-s, -s, -0.05), (s, -s, -0.05), (s, s, -0.05), (-s, s, -0.05)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new("farm_ground", me); sc.collection.objects.link(g); me.materials.append(material("M_preview_ground", "#7F9A5A"))
    return cam


def shoot(sc, cam, path, target, ang, elev, dist, lens=50, res=(400, 300)):
    """a picture from `ang` degrees round (0: its right side, 90: its front), `elev` up, `dist` cm away"""
    a, e = math.radians(ang), math.radians(elev)
    d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    cam.location = target + d * dist; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens; sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)


def sheet(paths, cols, out):
    """the panels side by side in one picture (left to right, top to bottom)"""
    ims = [bpy.data.images.load(p) for p in paths]; w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    canvas = np.ones((rows * h, cols * w, 4), np.float32)
    for k, im in enumerate(ims):
        a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a); a = a.reshape(h, w, 4)
        r, c = k // cols, k % cols
        canvas[(rows - 1 - r) * h:(rows - r) * h, c * w:(c + 1) * w] = a
    o = bpy.data.images.new("sheet", cols * w, rows * h, alpha=True)
    o.pixels.foreach_set(canvas.ravel()); o.filepath_raw = out; o.file_format = 'PNG'; o.save()
    for im in ims: bpy.data.images.remove(im)
    bpy.data.images.remove(o)


# SHEET: the 16 panels of <animal>_sheet.png, left to right, top to bottom
SHEET = ["side (A, Idle's first frame)", "front", "three-quarter", "three-quarter from behind",
         "B (three-quarter)", "C or B again from the other side", "Idle 1.2 s (looking left)", "Idle 3.5 s (looking right)",
         "Graze 0 (side)", "Graze 1.4 s (three-quarter; the chicken mid-peck)", "Walk 0 (side)", "Walk 1/4 (side)",
         "Walk 1/2 (side)", "Walk 3/4 (three-quarter)", "at 5 m, 70-degree view (A)", "at 5 m, 70-degree view (B)"]


def previews(S, arm, obs, G, clips, cam, sc, others):
    os.makedirs(os.path.join(PREV, "panels"), exist_ok=True)
    V = G["V"]; lo, hi = V.min(0), V.max(0); c = Vector(((lo + hi) / 2).tolist()); ext = float(max(hi[0] - lo[0], hi[2] - lo[2]))
    dist = ext * 2.6
    for o in others: o.hide_render = True
    vs = list(obs)

    def only(v):
        for k, o in obs.items(): o.hide_render = (k != v)
    shots = []
    def go(tag, clip, fi, v, ang, elev, d=dist, lens=50, tgt=c):
        set_basis(arm, clips[clip][fi]); only(v)
        p = os.path.join(PREV, "panels", f"{S.name.lower()}_{len(shots):02d}_{tag}.png")
        shoot(sc, cam, p, tgt, ang, elev, d, lens); shots.append(p)
    go("side", "Idle", 0, "A", 0, 6); go("front", "Idle", 0, "A", 90, 8); go("q", "Idle", 0, "A", 40, 18)
    go("qback", "Idle", 0, "A", 150, 18)
    go("B", "Idle", 0, vs[1], 40, 18); go("other", "Idle", 0, vs[-1], -40, 18)
    go("idle_l", "Idle", int(1.2 * FPS), "A", 40, 18); go("idle_r", "Idle", int(3.5 * FPS), "A", 40, 18)
    if "Graze" in clips: go("graze0", "Graze", 0, "A", 0, 6); go("graze", "Graze", int(1.4 * FPS), "A", 40, 18)
    else:                                                       # (the horse: its gallop, at a third and two thirds of its stride)
        nr = len(clips["Run"]) - 1; go("run0", "Run", nr // 3, "A", 0, 4); go("run1", "Run", 2 * nr // 3, "A", 0, 4)
    n = len(clips["Walk"]) - 1
    go("walk0", "Walk", 0, "A", 0, 4); go("walk1", "Walk", n // 4, "A", 0, 4); go("walk2", "Walk", n // 2, "A", 0, 4)
    go("walk3", "Walk", 3 * n // 4, "A", 40, 18)
    tgt5 = Vector((c.x, c.y, (hi[2] - lo[2]) * 0.4))
    go("at5m", "Idle", 0, "A", 35, 20, 500, 25.2, tgt5); go("at5mB", "Idle", 0, vs[1], 35, 20, 500, 25.2, tgt5)
    sheet(shots, 4, os.path.join(PREV, f"{S.name.lower()}_sheet.png"))
    set_basis(arm, clips["Idle"][0]); only("A")
    shoot(sc, cam, os.path.join(PREV, f"{S.name.lower()}_q.png"), c, 40, 18, dist, 50, (800, 600))
    for o in obs.values(): o.hide_render = False


def key_action(arm, name, frames):
    ad = arm.animation_data_create()
    act = bpy.data.actions.new(name); act.use_fake_user = True; ad.action = act
    if hasattr(ad, "action_slot") and hasattr(act, "slots"):
        try: ad.action_slot = act.slots.new('OBJECT', arm.name)
        except Exception: pass
    for i, fr in enumerate(frames):
        for pb in arm.pose.bones:
            l, q, s = fr[pb.name]; pb.location = l; pb.rotation_quaternion = q; pb.scale = s
            pb.keyframe_insert("location", frame=i, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=i, group=pb.name)
            pb.keyframe_insert("scale", frame=i, group=pb.name)
    ad.action = None
    return act


def export(S, arm, obs, clips, sc):
    """SK_Farm_<Animal>.fbx: mesh A + armature + the clips as takes; SK_Farm_<Animal>_<V>.fbx: the other colourings"""
    files = {}
    old = arm.name; arm.name = "Armature"                     # (Unreal skips an armature named so: root is the first bone)
    for pb in arm.pose.bones: pb.matrix_basis.identity()
    acts = [key_action(arm, n, f) for n, f in clips.items()]
    for pb in arm.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    for v, ob in obs.items():
        for o in sc.objects: o.select_set(False)
        arm.select_set(True); ob.select_set(True); bpy.context.view_layer.objects.active = arm
        fn = os.path.join(OUT, ob.name + ".fbx"); anim = (v == "A")
        bpy.ops.export_scene.fbx(filepath=fn, use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                                 bake_anim=anim, bake_anim_use_all_actions=anim, bake_anim_use_nla_strips=False,
                                 bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0, apply_unit_scale=True,
                                 apply_scale_options='FBX_SCALE_NONE', use_armature_deform_only=False, mesh_smooth_type='FACE',
                                 use_tspace=False, path_mode='STRIP')
        files[v] = os.path.basename(fn); log(S.name, "exported", fn, os.path.getsize(fn), "bytes")
    for a in acts: bpy.data.actions.remove(a)
    arm.name = old
    return files


def stick_figure(sc):
    """a 180 cm person of capsules, for scale"""
    S = Spec("Person", res=1.6, body_tris=3000, sole_band=0.5)
    S.ball((0, 0, 168.5), 11.5, "b"); S.cap((0, 0, 150), (0, 0, 157), 5, "b")
    S.ell((0, 0, 128), (11, 19, 24), "b"); S.ell((0, 0, 100), (10, 16, 12), "b")
    for y in (1, -1):
        S.cap((0, 9 * y, 92), (1, 9.5 * y, 50), 6.5, "b"); S.cap((1, 9.5 * y, 50), (0, 10 * y, 8), 5, "b")
        S.cap((-2, 9.5 * y, 4), (12, 9.5 * y, 4), 4, "b")
        S.cap((0, 21 * y, 146), (0, 25 * y, 116), 4.5, "b"); S.cap((0, 25 * y, 116), (3, 26 * y, 88), 4, "b")
    co, tris, _ = body_mesh(S); co[co[:, 2] < 0.5, 2] = 0
    me = bpy.data.meshes.new("person"); me.from_pydata([tuple(v) for v in co], [], [tuple(t) for t in tris]); me.update()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons)); me.materials.append(material("M_preview_person", "#8A8F99"))
    ob = bpy.data.objects.new("person", me); sc.collection.objects.link(ob)
    return ob, float(co[:, 2].max())


def lineup(sc, cam, built):
    person, ph = stick_figure(sc)
    x = 0.0; person.location = (x, 0, 0); person.rotation_euler = (0, 0, math.radians(-90))
    x += 60
    for name in ("Chicken", "Rabbit", "Goat", "Pig", "Cow"):
        if name not in built: continue
        b = built[name]; lo, hi = b["G"]["V"].min(0), b["G"]["V"].max(0)
        x += -lo[0] + 25
        b["arm"].location = (x, 0, 0); set_basis(b["arm"], b["clips"]["Idle"][0])
        for v, o in b["obs"].items(): o.hide_render = (v != "A")
        x += hi[0] + 25
    bpy.context.view_layer.update()
    mid = Vector((x / 2, 0, 80))
    shoot(sc, cam, os.path.join(PREV, "lineup.png"), mid, 8, 6, x * 1.55, 50, (1600, 600))
    shoot(sc, cam, os.path.join(PREV, "lineup_q.png"), mid, 30, 18, x * 1.65, 50, (1600, 700))
    for b in built.values():
        b["arm"].location = (0, 0, 0)
    return ph


def verify(files):
    """each FBX read back: its bones, meshes, materials' base colours and takes"""
    out = {}
    for fn in files:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=os.path.join(OUT, fn))
        sc = bpy.context.scene
        arm = next((o for o in sc.objects if o.type == 'ARMATURE'), None)
        meshes = [o for o in sc.objects if o.type == 'MESH']
        if arm is not None: arm.data.pose_position = 'REST'; bpy.context.view_layer.update()     # (the size of the reference pose)
        mats = {}
        for o in meshes:
            for m in o.data.materials:
                b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m and m.node_tree else None
                if b is not None: mats[m.name] = [round(x, 3) for x in b.inputs["Base Color"].default_value[:3]]
        tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
        lo = np.min([np.array([(o.matrix_world @ Vector(c)) for c in o.bound_box]).min(0) for o in meshes], axis=0)
        hi = np.max([np.array([(o.matrix_world @ Vector(c)) for c in o.bound_box]).max(0) for o in meshes], axis=0)
        out[fn] = {"objects": [o.name for o in sc.objects], "bones": len(arm.data.bones) if arm else 0,
                   "root_bone": next((b.name for b in arm.data.bones if b.parent is None), None) if arm else None,
                   "triangles": tris, "materials": mats,
                   "takes": {a.name: [round(x, 1) for x in a.frame_range] for a in bpy.data.actions},
                   "size_read_back_cm": [round(float(x) * 100.0, 1) for x in (hi - lo)]}
        log("verify", fn, json.dumps(out[fn])[:600])
    return out


# ---------------------------------------------------------------- the run
def main():
    os.makedirs(OUT, exist_ok=True); os.makedirs(PREV, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 0.01
    sc.render.fps = FPS; sc.render.fps_base = 1.0
    cam = setup_render(sc) if PREVIEW else None
    report, built, files = {"fps": FPS, "units": "cm", "faces": "+X", "sheet_panels": SHEET}, {}, []
    for key, fn in ANIMALS.items():
        if ONLY and key not in ONLY: continue
        S = fn()
        arm = build_armature(S, sc)
        G = build_geometry(S)
        obs, slots = make_objects(S, G, arm, sc)
        rig = Rig(arm, S)
        bi = {n: i for i, n in enumerate(G["names"])}
        rig.mouth_pts = {b: G["V"][G["W"][:, bi[b]] >= 0.9] for b in ("head", "jaw") if b in bi}
        # the IK reproduces the reference pose: the largest joint error with nothing moved
        T = rig.solve(empty_pose()); rest_err = max((T[n][1] - rig.h0[n]).length for n in T)
        rest_turn = max(math.degrees(T[n][0].angle) if T[n][0].angle < math.pi else 360 - math.degrees(T[n][0].angle) for n in T)
        clips, cinfo = make_clips(rig, S)
        meas = measure(S, rig, arm, obs["A"], G, clips)
        V = G["V"]; lo, hi = V.min(0), V.max(0)
        bi = {n: i for i, n in enumerate(G["names"])}
        backb = [bi[b] for b in ("pelvis", "spine_01", "spine_02") if b in bi]
        back = V[G["W"][:, backb].sum(1) > 0.5]
        rec = {"size_cm": {"length_x": round(float(hi[0] - lo[0]), 1), "width_y": round(float(hi[1] - lo[1]), 1),
                           "height_z": round(float(hi[2] - lo[2]), 1), "min": [round(float(x), 1) for x in lo],
                           "max": [round(float(x), 1) for x in hi], "back_height": round(float(back[:, 2].max()), 1)},
               "triangles": int(len(G["T"])), "vertices": int(len(V)), "body_triangles_before_decimation": G["body_tris_raw"],
               "bones": G["names"], "legs": {lg["id"]: [b for b in lg["bones"] if b] for lg in S.legs},
               "rest_pose_rebuilt_err_cm": round(rest_err, 5), "rest_pose_rebuilt_turn_deg": round(rest_turn, 5),
               "weights": weight_check(S, G), "variants": slots,
               "clips": {k: {**cinfo[k], **meas[k]} for k in clips}}
        rec["walk_speed_cm_s"] = meas["Walk"]["walk_speed_cm_s"]
        rec["walk_cycle_s"] = S.anim["walk"]["T"]; rec["walk_stride_cm"] = round(rec["walk_speed_cm_s"] * S.anim["walk"]["T"], 1)
        if "Run" in meas: rec["run_speed_cm_s"] = meas["Run"]["walk_speed_cm_s"]; rec["run_cycle_s"] = S.anim["run"]["T"]
        log(S.name, json.dumps({k: rec[k] for k in ("size_cm", "triangles", "rest_pose_rebuilt_err_cm", "weights", "walk_speed_cm_s")}))
        for k in clips: log(S.name, k, json.dumps(rec["clips"][k]))
        if len(G["T"]) >= TRI_BUDGET: log(S.name, "OVER THE TRIANGLE BUDGET", len(G["T"]))
        if PREVIEW:
            others = [o for b in built.values() for o in list(b["obs"].values())]
            previews(S, arm, obs, G, clips, cam, sc, others)
        rec["fbx"] = export(S, arm, obs, clips, sc); files += list(rec["fbx"].values())
        report[S.name] = rec
        built[S.name] = dict(arm=arm, obs=obs, G=G, clips=clips)
    if PREVIEW and len(built) > 1:
        for b in built.values():
            for o in b["obs"].values(): o.hide_render = False
        report["lineup_person_height_cm"] = round(lineup(sc, cam, built), 1)
    path = os.path.join(OUT, "farm_animals.json")
    json.dump(report, open(path, "w"), indent=1)
    report["fbx_check"] = verify(files)
    json.dump(report, open(path, "w"), indent=1)
    log("DONE", path)


main()
