"""The wilderness's farm fields' corn (maize) and potato plants (the user's list asks for regular lines of crops: corn,
cabbages, potatoes, pumpkins; the packs have wheat, cabbage, pumpkin and sunflower but no maize and no potato plant): built
here from shapes, two of each, low enough in triangles to stand in fields by the tens of thousands (seen from 2 to 60 m).

  Corn      SM_Wild_Corn_<A|B>, 1.95-2.25 m: a straight tapering stalk (5 sides) with swollen nodes and brace roots at its
            foot; 8-9 strap leaves (60-90 cm, 6.5-9 cm wide) alternating up the stalk in two ranks, each a strip of 5
            segments with a folded middle, rising from its sheath, arching out and drooping at its tip, a little twisted;
            a tassel of three crossed cards at the top; one or two ears (husk-wrapped spindles) angled out of a leaf's
            axil, each with a husk flag and a crossed card of silk at its tip. Under 900 triangles.
  Potato    SM_Wild_Potato_<A|B>, 0.45-0.6 m tall, 0.5-0.7 m across: six to eight stems from the ground arching out and up
            (3 sides), each with bent leaf cards (a painted spray of pinnate compound leaves, alpha-masked) along it and
            at its tip, a few cards crowning the mound, and white or pale violet flower clusters (crossed cards on short
            stalks) over the top. Under 600 triangles.
  Pictures  painted by this script (numpy), 512 px, written beside the FBX:
            T_Wild_CornStalk.png   (opaque) an atlas of vertical strips: u 0-0.4 the stalk's green, 0.4-0.7 the husk's
                                   paler green, 0.7-1.0 the brace roots' darker green; faint lines along v.
            T_Wild_CornLeaves.png  (masked) u 0-0.75: the strap leaf, across u, base to tip along v (a pale midrib,
                                   parallel veins, a wavy margin in the alpha, yellowed tips); u 0.75-1 v 0.5-1: the
                                   tassel (straw spikes on transparency); u 0.75-1 v 0-0.5: the silk (red-brown threads).
            T_Wild_PotatoStem.png  (opaque) green stems with a purple tinge.
            T_Wild_PotatoLeaves.png (masked) v 0-0.75: a spray of dark-green compound leaves (oval leaflets in pairs and
                                   a terminal one) from the picture's foot middle; v 0.75-1: four flower clusters
                                   (u 0-0.5 white, 0.5-1 pale violet) with yellow middles.
Material slots (each mesh two, as wild_trees.py's trees, so 887's trees() pattern applies):
  0 M_Wild_CornBark / M_Wild_PotatoBark     (opaque: stalk, nodes, roots, husks, stems) <- T_Wild_CornStalk / T_Wild_PotatoStem
  1 M_Wild_CornLeaves / M_Wild_PotatoLeaves (masked, two-sided: leaves, tassel, silk, leaf and flower cards)
                                            <- T_Wild_CornLeaves / T_Wild_PotatoLeaves
Writes into out_dir: SM_Wild_<Corn|Potato>_<A|B>.fbx, the four PNGs, wild_crops.json (each mesh's height, width,
triangles). Z up, metres (exported x100 to cm as the trees), origin at the plant's foot on the ground; any yaw.
With preview_dir also renders (Eevee, or Cycles when Eevee cannot) each plant from the front and three-quarter, and a
short row of corn and one of potatoes a metre apart, into preview_dir.
Blender: -b -P wild_crops.py -- [out_dir (default claude_ue5/SourceArt/wilderness/crops)] [preview_dir]"""
import bpy, bmesh, math, random, sys, os, json
import numpy as np
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
try: REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
except NameError: REPO = os.getcwd()
OUT = os.path.abspath(argv[0] if argv and argv[0] else os.path.join(REPO, "claude_ue5", "SourceArt", "wilderness", "crops"))
PREVIEW = os.path.abspath(argv[1]) if len(argv) > 1 else None
os.makedirs(OUT, exist_ok=True)

TEX = {"CornBark": "T_Wild_CornStalk", "CornLeaves": "T_Wild_CornLeaves", "PotatoBark": "T_Wild_PotatoStem", "PotatoLeaves": "T_Wild_PotatoLeaves"}
# atlas regions (u0, u1, v0, v1)
CORN_LEAF = (0.0, 0.75, 0.0, 1.0); CORN_TASSEL = (0.75, 1.0, 0.5, 1.0); CORN_SILK = (0.75, 1.0, 0.0, 0.5)
STALK_U = (0.0, 0.4); HUSK_U = (0.4, 0.7); ROOT_U = (0.7, 1.0)
POT_LEAF = (0.0, 1.0, 0.0, 0.74)
POT_FLOWER = [(0.25 * k + 0.012, 0.25 * k + 0.238, 0.762, 0.988) for k in range(4)]   # inset: no bleeding from the next picture


# ------------------------------------------------------------------------------------------------ pictures
def save_png(name, rgba):
    h, w, _ = rgba.shape
    img = bpy.data.images.new(name, width=w, height=h, alpha=True)
    img.pixels = np.flipud(rgba).astype(np.float32).ravel()
    img.filepath_raw = os.path.join(OUT, name + ".png"); img.file_format = "PNG"; img.save()
    return img.filepath_raw


def noise(n, seed, octaves=((8, 1.0), (16, 0.5), (32, 0.25), (64, 0.12))):
    rng = np.random.default_rng(seed); acc = np.zeros((n, n))
    for o, a in octaves:
        g = rng.random((o + 1, o + 1)); ys = np.linspace(0, o, n, endpoint=False); i0 = ys.astype(int); f = ys - i0; f = f * f * (3 - 2 * f)
        row = g[i0][:, i0] * (1 - f)[None, :] + g[i0][:, i0 + 1] * f[None, :]
        row2 = g[i0 + 1][:, i0] * (1 - f)[None, :] + g[i0 + 1][:, i0 + 1] * f[None, :]
        acc += a * (row * (1 - f)[:, None] + row2 * f[:, None])
    acc -= acc.min(); return acc / max(acc.max(), 1e-6)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def grid(n):
    """U across, V up (V 0 at the picture's foot, as the mesh's UVs)"""
    yy, xx = np.mgrid[0:n, 0:n] / (n - 1)
    return xx, 1.0 - yy


def mix(col, c, w):
    w = np.asarray(w)[..., None]; return col * (1 - w) + np.array(c) * w


def line_mask(U, V, a, b, width):
    """pixels within width of the segment a-b (in UV units)"""
    ax, ay = a; bx, by = b; dx, dy = bx - ax, by - ay; L2 = max(dx * dx + dy * dy, 1e-9)
    t = np.clip(((U - ax) * dx + (V - ay) * dy) / L2, 0, 1)
    return (U - ax - t * dx) ** 2 + (V - ay - t * dy) ** 2 < width * width


def ellipse_mask(U, V, c, a, b, rot):
    du, dv = U - c[0], V - c[1]
    x = du * math.cos(rot) + dv * math.sin(rot); y = -du * math.sin(rot) + dv * math.cos(rot)
    return (x / a) ** 2 + (y / b) ** 2, x, y


def corn_stalk_png(n=512):
    U, V = grid(n); nz = noise(n, 12)
    col = np.zeros((n, n, 3))
    for (u0, u1), c, lines, amp in ((STALK_U, (0.30, 0.47, 0.15), 18, 0.10), (HUSK_U, (0.56, 0.62, 0.30), 26, 0.16), (ROOT_U, (0.24, 0.36, 0.13), 14, 0.10)):
        m = (U >= u0) & (U <= u1 + 1e-6)
        s = 0.5 + 0.5 * np.sin((U - u0) / (u1 - u0) * 2 * math.pi * lines + nz * 2.0)
        shade = (1 - amp) + amp * s
        col[m] = (np.array(c)[None, :] * (0.88 + 0.22 * nz[m])[:, None] * shade[m][:, None])
    # a little brown at the husk's top end and the roots' foot (dry tips)
    col = mix(col, (0.55, 0.48, 0.26), 0.25 * ((U > HUSK_U[0]) & (U < HUSK_U[1])) * smooth(0.82, 1.0, V))
    rgba = np.concatenate([np.clip(col, 0, 1), np.ones((n, n, 1))], -1)
    return save_png(TEX["CornBark"], rgba)


def corn_leaves_png(n=512):
    U, V = grid(n); nz = noise(n, 5)
    rgba = np.zeros((n, n, 4))
    # the strap leaf, u 0-0.75
    lu = U / CORN_LEAF[1]; d = np.abs(lu - 0.5)
    col = np.array([0.21, 0.42, 0.10])[None, None, :] * (0.86 + 0.24 * nz[..., None])
    col *= (0.92 + 0.08 * (0.5 + 0.5 * np.sin(lu * 2 * math.pi * 16)))[..., None]       # parallel veins
    rib_w = 0.045 * (1 - 0.75 * V) + 0.008
    col = mix(col, (0.66, 0.74, 0.46), 0.85 * (1 - smooth(rib_w * 0.55, rib_w, d)))     # the pale midrib
    col = mix(col, (0.38, 0.52, 0.20), 0.3 * smooth(0.36, 0.5, d))                       # paler margins
    col = mix(col, (0.66, 0.58, 0.24), 0.55 * smooth(0.80, 1.0, V))                      # yellowed tip
    col = mix(col, (0.36, 0.48, 0.18), 0.2 * smooth(0.0, 0.12, 0.12 - V))                # the sheath's paler base
    edge = 0.475 + 0.012 * np.sin(V * 70 + np.sin(V * 13) * 2.5) + 0.006 * np.sin(V * 151)                           # a wavy margin
    leaf = (U < CORN_LEAF[1]) & (d < edge)
    rgba[leaf, :3] = col[leaf]; rgba[leaf, 3] = 1.0
    rng = np.random.default_rng(77)
    # the tassel, u 0.75-1, v 0.5-1: a central spike and branches from its lower part, spreading and drooping
    u0, u1, v0, v1 = CORN_TASSEL; cu = (u0 + u1) / 2; w = u1 - u0; h = v1 - v0
    tm = np.zeros((n, n), bool)
    tm |= line_mask(U, V, (cu, v0 + 0.02), (cu, v1 - 0.01), 0.0065)
    for k in range(9):
        sgn = -1 if k % 2 else 1
        z = v0 + h * rng.uniform(0.12, 0.45)
        ang = math.radians(rng.uniform(18, 50))
        L = h * rng.uniform(0.35, 0.6)
        a = (cu, z); m_ = (cu + sgn * math.sin(ang) * L * 0.55, z + math.cos(ang) * L * 0.55)
        e = (min(max(cu + sgn * math.sin(ang) * L * 0.95, u0 + 0.008), u1 - 0.008), z + math.cos(ang) * L * 0.75)
        tm |= line_mask(U, V, a, m_, 0.0045) | line_mask(U, V, m_, e, 0.004)
    # spikelets: little dashes along every line
    tcol = np.array([0.80, 0.68, 0.38])[None, None, :] * (0.8 + 0.35 * noise(n, 9, ((64, 1.0), (128, 0.6)))[..., None])
    reg = (U >= u0) & (V >= v0)
    rgba[tm & reg, :3] = tcol[tm & reg]; rgba[tm & reg, 3] = 1.0
    # the silk, u 0.75-1, v 0-0.5: threads from the foot's middle fanning up and curling over
    u0, u1, v0, v1 = CORN_SILK; cu = (u0 + u1) / 2; h = v1 - v0
    sm = np.zeros((n, n), bool)
    for k in range(26):
        ang = rng.uniform(-0.55, 0.55); L = h * rng.uniform(0.55, 0.95)
        p = (cu, v0 + 0.01); bend = rng.uniform(-0.6, 0.6)
        for s in range(6):
            t0, t1 = s / 6, (s + 1) / 6
            q0 = (cu + math.sin(ang + bend * t0 * t0) * L * t0, v0 + 0.01 + math.cos(ang + bend * t0 * t0) * L * t0)
            q1 = (cu + math.sin(ang + bend * t1 * t1) * L * t1, v0 + 0.01 + math.cos(ang + bend * t1 * t1) * L * t1)
            sm |= line_mask(U, V, q0, q1, 0.0022)
    sm &= (U > u0 + 0.004) & (U < u1 - 0.004) & (V < v1 - 0.004)
    scol = np.array([0.58, 0.32, 0.16])[None, None, :] * (0.75 + 0.45 * noise(n, 21, ((32, 1.0), (128, 0.5)))[..., None])
    scol = mix(scol, (0.78, 0.66, 0.36), 0.6 * smooth(0.0, 0.25, 0.25 - V))             # paler where they leave the husk
    rgba[sm, :3] = scol[sm]; rgba[sm, 3] = 1.0
    return save_png(TEX["CornLeaves"], np.clip(rgba, 0, 1))


def potato_stem_png(n=512):
    U, V = grid(n); nz = noise(n, 41)
    s = 0.5 + 0.5 * np.sin(U * 2 * math.pi * 10 + nz * 3)
    col = np.array([0.24, 0.40, 0.13])[None, None, :] * (0.85 + 0.25 * nz[..., None])
    col = mix(col, (0.36, 0.22, 0.28), 0.35 * s * nz)
    rgba = np.concatenate([np.clip(col, 0, 1), np.ones((n, n, 1))], -1)
    return save_png(TEX["PotatoBark"], rgba)


def potato_leaves_png(n=512):
    U, V = grid(n); nz = noise(n, 52)
    rgba = np.zeros((n, n, 4)); rng = np.random.default_rng(3)
    pal = [(0.16, 0.31, 0.08), (0.20, 0.36, 0.10), (0.13, 0.27, 0.07), (0.22, 0.38, 0.12)]
    vmax = POT_LEAF[3] - 0.006

    def paint(mask, c, shade=None):
        mask = mask & (V < vmax)
        cc = np.array(c)[None, :] * (0.85 + 0.3 * nz[mask])[:, None]
        if shade is not None: cc = cc * shade[mask][:, None]
        rgba[mask, :3] = cc; rgba[mask, 3] = 1.0

    def compound(origin, ang, L, scale):
        # the rachis
        tip = (origin[0] + math.sin(ang) * L, origin[1] + math.cos(ang) * L)
        dirx, diry = math.sin(ang), math.cos(ang)
        def at(s): return (origin[0] + dirx * L * s, origin[1] + diry * L * s)
        paint(line_mask(U, V, origin, tip, 0.006 * scale), (0.20, 0.32, 0.10))
        # leaflet pairs (biggest near the tip), tiny ones between
        for s, a in ((0.34, 0.070), (0.56, 0.082), (0.78, 0.090)):
            for sgn in (-1, 1):
                fwd = ang + sgn * math.radians(rng.uniform(55, 70))
                p = at(s); a_ = a * scale * rng.uniform(0.9, 1.1)
                c = (p[0] + math.sin(fwd) * a_ * 0.95, p[1] + math.cos(fwd) * a_ * 0.95)
                rot = math.pi / 2 - fwd
                r2, x, y = ellipse_mask(U, V, c, a_, a_ * 0.58, rot)
                m = r2 < 1.0
                shade = 0.82 + 0.25 * np.clip(1 - r2, 0, 1)
                shade = np.where(np.abs(y) < a_ * 0.04, 1.25, shade)                          # its middle vein
                paint(m, pal[rng.integers(len(pal))], shade)
            for sgn in (-1, 1):
                fwd = ang + sgn * math.radians(80); p = at(s + 0.11); a_ = 0.028 * scale
                c = (p[0] + math.sin(fwd) * a_, p[1] + math.cos(fwd) * a_)
                r2, x, y = ellipse_mask(U, V, c, a_, a_ * 0.6, math.pi / 2 - fwd)
                paint(r2 < 1.0, pal[rng.integers(len(pal))])
        # the terminal leaflet
        a_ = 0.105 * scale; c = (tip[0] + dirx * a_ * 0.8, tip[1] + diry * a_ * 0.8)
        r2, x, y = ellipse_mask(U, V, c, a_, a_ * 0.62, math.pi / 2 - ang)
        shade = np.where(np.abs(y) < a_ * 0.04, 1.25, 0.82 + 0.25 * np.clip(1 - r2, 0, 1))
        paint(r2 < 1.0, pal[0], shade)

    o = (0.5, 0.03)
    for ang, L, sc in ((-1.15, 0.30, 1.1), (1.15, 0.30, 1.1), (-0.62, 0.40, 1.15), (0.62, 0.40, 1.15), (-0.22, 0.47, 1.2), (0.22, 0.47, 1.2)):
        compound(o, ang, L, sc)
    # the flowers, v 0.75-1: clusters of five-petalled flowers on fine stalks
    for k, (u0, u1, v0, v1) in enumerate(POT_FLOWER):
        cu = (u0 + u1) / 2; petal = (0.94, 0.93, 0.90) if k < 2 else (0.78, 0.66, 0.92)
        flowers = [(cu + rng.uniform(-0.07, 0.07), v0 + rng.uniform(0.09, 0.2)) for _ in range(rng.integers(6, 9))]
        reg = (U > u0 + 0.004) & (U < u1 - 0.004) & (V > v0 + 0.004) & (V < v1 - 0.004)
        for f in flowers:
            m = line_mask(U, V, (cu, v0 + 0.01), f, 0.0035) & reg
            rgba[m, :3] = (0.22, 0.36, 0.12); rgba[m, 3] = 1.0
        for f in flowers:
            r0 = rng.uniform(0.020, 0.026); a0 = rng.uniform(0, 2 * math.pi)
            for p in range(5):
                a = a0 + p * 2 * math.pi / 5
                c = (f[0] + math.cos(a) * r0 * 0.55, f[1] + math.sin(a) * r0 * 0.55)
                r2, x, y = ellipse_mask(U, V, c, r0 * 0.6, r0 * 0.42, a)
                m = (r2 < 1.0) & reg
                rgba[m, :3] = np.array(petal) * (0.88 + 0.12 * np.clip(1 - r2[m], 0, 1))[:, None]; rgba[m, 3] = 1.0
            m = ((U - f[0]) ** 2 + (V - f[1]) ** 2 < (r0 * 0.3) ** 2) & reg
            rgba[m, :3] = (0.95, 0.78, 0.15); rgba[m, 3] = 1.0
    return save_png(TEX["PotatoLeaves"], np.clip(rgba, 0, 1))


# ------------------------------------------------------------------------------------------------ the shapes
def lerp(a, b, t): return a + (b - a) * t


def frames(pts):
    """tangents and parallel-transported side vectors along a line"""
    n = len(pts)
    T = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
    a = Vector((1, 0, 0)) if abs(T[0].x) < 0.9 else Vector((0, 1, 0))
    N = T[0].cross(a).normalized(); out = []
    for t in T:
        N = N - t * N.dot(t)
        if N.length < 1e-6: N = t.cross(Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0)))
        N.normalize(); out.append((N.copy(), t.cross(N)))
    return out


def tube(bm, uvl, pts, radii, sides, mat, urange=(0.0, 1.0), vscale=1.0):
    fr = frames(pts); rings = []
    length = [0.0]
    for i in range(1, len(pts)): length.append(length[-1] + (pts[i] - pts[i - 1]).length)
    for (n_, b), p, r in zip(fr, pts, radii):
        rings.append([bm.verts.new(p + (n_ * math.cos(2 * math.pi * k / sides) + b * math.sin(2 * math.pi * k / sides)) * r) for k in range(sides)])
    u0, u1 = urange
    for i in range(len(rings) - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            f = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k])); f.material_index = mat
            ua, ub = lerp(u0, u1, k / sides), lerp(u0, u1, (k + 1) / sides)
            va, vb = length[i] * vscale, length[i + 1] * vscale
            for lp, uv in zip(f.loops, ((ua, va), (ub, va), (ub, vb), (ua, vb))): lp[uvl].uv = uv


def strip(bm, uvl, pts, sides, normals, widths, fold, mat, reg):
    """a leaf: three vertices across each section (edge, folded middle, edge), UVs u across the region, v along it"""
    u0, u1, v0, v1 = reg; rows = []
    for p, s, nrm, w in zip(pts, sides, normals, widths):
        rows.append([bm.verts.new(p - s * w * 0.5), bm.verts.new(p - nrm * w * fold), bm.verts.new(p + s * w * 0.5)])
    n = len(rows)
    for i in range(n - 1):
        va, vb = lerp(v0, v1, i / (n - 1)), lerp(v0, v1, (i + 1) / (n - 1))
        for j in range(2):
            f = bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j])); f.material_index = mat
            ua, ub = lerp(u0, u1, j / 2), lerp(u0, u1, (j + 1) / 2)
            for lp, uv in zip(f.loops, ((ua, va), (ub, va), (ub, vb), (ua, vb))): lp[uvl].uv = uv


def card(bm, uvl, base, along, side, mat, reg, bend=None):
    """a card from its foot's middle: along is its length (vector), side its width (vector); bent: a second row half way,
    the tip turned down by `bend` (a vector added to the tip)"""
    u0, u1, v0, v1 = reg
    rows_at = [(0.0, Vector()), (1.0, bend or Vector())] if bend is None else [(0.0, Vector()), (0.5, bend * 0.25), (1.0, bend)]
    rows = [[bm.verts.new(base + along * t + off - side * 0.5), bm.verts.new(base + along * t + off + side * 0.5)] for t, off in rows_at]
    for i in range(len(rows) - 1):
        f = bm.faces.new((rows[i][0], rows[i][1], rows[i + 1][1], rows[i + 1][0])); f.material_index = mat
        va, vb = lerp(v0, v1, rows_at[i][0]), lerp(v0, v1, rows_at[i + 1][0])
        for lp, uv in zip(f.loops, ((u0, va), (u1, va), (u1, vb), (u0, vb))): lp[uvl].uv = uv


def leaf(bm, uvl, origin, yaw, L, W, e_start, e0, e1, twist, curl, segs, mat, reg, fold=0.16, base_w=0.35):
    """a strap leaf: from its sheath (e_start, near upright) out at e0, its elevation falling to e1 at the tip"""
    pts = [origin.copy()]; dirs = []
    ds = L / segs
    def elev(t):
        if t < 0.12: return lerp(e_start, e0, t / 0.12)
        return lerp(e0, e1, ((t - 0.12) / 0.88) ** 1.1)
    def d_at(t):
        e = elev(t); y = yaw + curl * t
        return Vector((math.cos(e) * math.cos(y), math.cos(e) * math.sin(y), math.sin(e)))
    for i in range(segs):
        t = (i + 0.5) / segs; pts.append(pts[-1] + d_at(t) * ds)
    sides, normals, widths = [], [], []
    for i, p in enumerate(pts):
        t = i / segs; d = d_at(t); y = yaw + curl * t
        s = Vector((-math.sin(y), math.cos(y), 0.0))
        s = Matrix.Rotation(twist * t, 3, d) @ s
        sides.append(s); normals.append(d.cross(s).normalized())
        w = W * (base_w + (1 - base_w) * math.sin(min(t / 0.3, 1.0) * math.pi / 2)) if t <= 0.3 else W * (1 - ((t - 0.3) / 0.7) ** 1.6)
        widths.append(max(w, 0.004))
    strip(bm, uvl, pts, sides, normals, widths, fold, mat, reg)
    return pts


def new_mesh(name):
    me = bpy.data.meshes.new(name); ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new(); return me, ob, bm, bm.loops.layers.uv.new("UVMap")


def finish(me, ob, bm, kind):
    bm.to_mesh(me); bm.free()
    for mn in ("Bark", "Leaves"):
        m = bpy.data.materials.get(f"M_Wild_{kind}{mn}") or bpy.data.materials.new(f"M_Wild_{kind}{mn}")
        me.materials.append(m)
    for p in me.polygons: p.use_smooth = True
    xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
    return {"height_m": round(max(zs), 3), "width_m": round(max(max(xs) - min(xs), max(ys) - min(ys)), 3), "foot_z_m": round(min(zs), 3),
            "triangles": sum(len(p.vertices) - 2 for p in me.polygons)}


def build_corn(variant, seed):
    rng = random.Random(seed)
    me, ob, bm, uvl = new_mesh(f"SM_Wild_Corn_{variant}")
    H = rng.uniform(1.95, 2.25)                       # to the tassel's top
    top = H - rng.uniform(0.30, 0.34)                 # the stalk's top, where the tassel's cards stand
    r0 = 0.0165 * rng.uniform(0.92, 1.08)
    lean = Vector((rng.uniform(-0.025, 0.025), rng.uniform(-0.025, 0.025), 0))
    ph = rng.uniform(0, 6.28)
    def at(z): return Vector((0, 0, z)) + lean * z + Vector((0.012 * math.sin(z * 2.1 + ph), 0.012 * math.cos(z * 1.7 + ph), 0)) * z
    def rad(z): return r0 * (1.0 - 0.5 * z / top)
    nl = rng.randint(8, 9)
    nodes = [top * (0.07 + 0.80 * (i / (nl - 1)) ** 1.12) for i in range(nl)]
    # the stalk: a ring at the foot, a swollen ring at every node, one between, the top
    zs = [0.0, 0.035]
    for i, z in enumerate(nodes):
        if i: zs.append((nodes[i - 1] + z) / 2)
        zs.append(z)
    zs.append(top + 0.04)
    radii = [rad(z) * (1.25 if z == 0 else 1.15 if z in nodes else 1.0) for z in zs]
    tube(bm, uvl, [at(z) for z in zs], radii, 5, 0, STALK_U)
    # brace roots
    for k in range(3):
        a = ph + k * 2 * math.pi / 3 + rng.uniform(-0.3, 0.3); z0 = rng.uniform(0.05, 0.09); out = rng.uniform(0.05, 0.08)
        p0 = at(z0); p2 = Vector((math.cos(a) * out, math.sin(a) * out, -0.01)); p1 = (p0 + p2) / 2 + Vector((math.cos(a), math.sin(a), 0)) * 0.012
        tube(bm, uvl, [p0, p1, p2], [0.0055, 0.0048, 0.004], 3, 0, ROOT_U)
    # the leaves: two ranks, alternating
    rank = rng.uniform(0, 2 * math.pi); yaws = []
    for i, z in enumerate(nodes):
        x = i / (nl - 1)
        yaw = rank + math.pi * (i % 2) + rng.uniform(-0.38, 0.38); yaws.append(yaw)
        L = 0.9 * (0.68 + 0.32 * math.sin(math.pi * (0.12 + 0.78 * x))) * rng.uniform(0.94, 1.04)
        if i == nl - 1: L *= 0.85
        W = rng.uniform(0.080, 0.095) * (0.8 + 0.25 * L / 0.9)
        e0 = math.radians(lerp(42, 64, x) + rng.uniform(-6, 6))
        e1 = math.radians(lerp(-52, -10, x) + rng.uniform(-10, 10))
        o = at(z) + Vector((math.cos(yaw), math.sin(yaw), 0)) * rad(z) * 0.9
        leaf(bm, uvl, o, yaw, L, W, math.radians(84), e0, e1, rng.uniform(-0.7, 0.7), rng.uniform(-0.35, 0.35), 5, 1, CORN_LEAF)
    # the tassel: three crossed cards over the stalk's top
    tw, th = rng.uniform(0.17, 0.21), H - top + 0.02
    tb = at(top) - Vector((0, 0, 0.02)); a0 = rng.uniform(0, math.pi)
    for k in range(3):
        a = a0 + k * math.pi / 3
        card(bm, uvl, tb, Vector((0, 0, th)) + lean * th * 2, Vector((math.cos(a), math.sin(a), 0)) * tw, 1, CORN_TASSEL)
    # the ears: out of a leaf's axil, angled 25-35 degrees off the stalk
    ears = 1 if variant == "A" else 2
    picks = sorted(range(nl), key=lambda i: abs(nodes[i] / top - 0.45))[:ears]
    for i in picks:
        z = nodes[i]; yaw = yaws[i] + rng.uniform(-0.25, 0.25)
        tilt = math.radians(rng.uniform(25, 35))
        d = Vector((math.cos(yaw) * math.sin(tilt), math.sin(yaw) * math.sin(tilt), math.cos(tilt)))
        o = at(z + 0.02) + Vector((math.cos(yaw), math.sin(yaw), 0)) * rad(z) * 0.8
        EL, R = rng.uniform(0.20, 0.24), rng.uniform(0.024, 0.029)
        ts = [0.0, 0.12, 0.35, 0.65, 0.88, 1.0]
        droop = Vector((math.cos(yaw), math.sin(yaw), -0.6)) * 0.03
        pts = [o + d * (EL * t) + droop * t * t for t in ts]
        rr = [R * 0.35, R * 0.85, R, R * 0.92, R * 0.55, R * 0.18]
        tube(bm, uvl, pts, rr, 5, 0, HUSK_U, 1.0 / EL)
        tip = pts[-1]; dt = (pts[-1] - pts[-2]).normalized()
        # a husk flag curling out of the tip
        leaf(bm, uvl, pts[-2], yaw + rng.uniform(-0.4, 0.4), rng.uniform(0.09, 0.12), 0.032, math.radians(80), math.radians(55), math.radians(5), 0.4, 0.0, 3, 1, CORN_LEAF, fold=0.1, base_w=0.8)
        # the silk: a crossed card from the tip
        sl = rng.uniform(0.07, 0.09)
        s1 = dt.cross(Vector((0, 0, 1))).normalized() if abs(dt.z) < 0.99 else Vector((1, 0, 0))
        s2 = dt.cross(s1).normalized()
        for s in (s1, s2):
            card(bm, uvl, tip - dt * 0.005, (dt + Vector((0, 0, -0.35))).normalized() * sl, s * sl * 0.8, 1, CORN_SILK)
    info = finish(me, ob, bm, "Corn"); info["leaves"] = nl; info["ears"] = ears
    return ob, info


def build_potato(variant, seed):
    rng = random.Random(seed)
    me, ob, bm, uvl = new_mesh(f"SM_Wild_Potato_{variant}")
    ns = rng.randint(6, 7) if variant == "A" else rng.randint(7, 8)
    a0 = rng.uniform(0, 2 * math.pi); tips = []
    for s in range(ns):
        yaw = a0 + s * 2 * math.pi / ns + rng.uniform(-0.3, 0.3)
        e = math.radians(rng.uniform(58, 78)); L = rng.uniform(0.28, 0.37)
        p = Vector((math.cos(yaw) * 0.025, math.sin(yaw) * 0.025, -0.01)); pts = [p.copy()]
        for i in range(3):
            t = (i + 0.5) / 3; ee = e - math.radians(28) * t
            p = p + Vector((math.cos(ee) * math.cos(yaw), math.cos(ee) * math.sin(yaw), math.sin(ee))) * (L / 3); pts.append(p.copy())
        tube(bm, uvl, pts, [0.0075, 0.0065, 0.0055, 0.0045], 3, 0)
        tips.append((pts, yaw))
        # compound-leaf cards along the stem and at its tip, fanned out and tilted up, layered from the ground to the top
        for k, t in enumerate((0.25, 0.5, 0.75, 1.0)):
            i0 = min(int(t * 3), 2); q = lerp(pts[i0], pts[i0 + 1], t * 3 - i0)
            fy = yaw + (rng.uniform(-0.3, 0.3) if t == 1.0 else (1 if k % 2 else -1) * rng.uniform(0.6, 1.2))
            fe = math.radians(lerp(8, 36, t) + rng.uniform(-8, 8))
            cl = rng.uniform(0.15, 0.19) * (1.1 if t < 0.3 else 1.0)
            along = Vector((math.cos(fe) * math.cos(fy), math.cos(fe) * math.sin(fy), math.sin(fe))) * cl
            side = Vector((-math.sin(fy), math.cos(fy), 0.0))
            side = Matrix.Rotation(rng.uniform(-0.3, 0.3), 3, along.normalized()) @ side
            card(bm, uvl, q - along * 0.25, along, side * cl * 1.3, 1, POT_LEAF, bend=Vector((0, 0, -cl * rng.uniform(0.2, 0.4))))
    # a crown of cards over the middle, so the mound is closed and rounded on top
    top_z = rng.uniform(0.36, 0.42)
    for k in range(5):
        fy = a0 + k * 2 * math.pi / 5 + rng.uniform(-0.4, 0.4); fe = math.radians(rng.uniform(25, 50)); cl = rng.uniform(0.15, 0.19)
        along = Vector((math.cos(fe) * math.cos(fy), math.cos(fe) * math.sin(fy), math.sin(fe))) * cl
        side = Vector((-math.sin(fy), math.cos(fy), 0.0))
        card(bm, uvl, Vector((0, 0, top_z - 0.06)) - along * 0.2, along, side * cl * 1.3, 1, POT_LEAF, bend=Vector((0, 0, -cl * 0.35)))
    tube(bm, uvl, [Vector((0, 0, -0.01)), Vector((0.01, 0, top_z * 0.5)), Vector((0, 0.01, top_z - 0.04))], [0.008, 0.007, 0.005], 3, 0)
    # flower clusters on short stalks just over the foliage
    nf = rng.randint(3, 4) if variant == "A" else rng.randint(4, 5)
    for k in range(nf):
        pts, yaw = tips[(k * 2 + 1) % len(tips)]
        b = lerp(pts[2], pts[3], 0.3)
        top = b + Vector((-math.cos(yaw) * 0.03, -math.sin(yaw) * 0.03, max(rng.uniform(0.37, 0.42) - b.z, 0.04)))
        tube(bm, uvl, [b, (b + top) / 2 + Vector((0, 0, 0.01)), top], [0.004, 0.0035, 0.003], 3, 0)
        reg = POT_FLOWER[rng.randrange(2) + (0 if variant == "A" else 2)]
        fs = rng.uniform(0.09, 0.11); a = rng.uniform(0, math.pi)
        for aa in (a, a + math.pi / 2):
            card(bm, uvl, top - Vector((0, 0, fs * 0.25)), Vector((0, 0, fs)), Vector((math.cos(aa), math.sin(aa), 0)) * fs, 1, reg)
    info = finish(me, ob, bm, "Potato"); info["stems"] = ns; info["flower_clusters"] = nf
    return ob, info


def export(ob):
    bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    fn = os.path.join(OUT, ob.name + ".fbx")
    bpy.ops.export_scene.fbx(filepath=fn, use_selection=True, object_types={"MESH"}, apply_unit_scale=True, global_scale=100.0, axis_forward="X", axis_up="Z", mesh_smooth_type="FACE")
    return fn


# ------------------------------------------------------------------------------------------------ previews
def preview(objs):
    os.makedirs(PREVIEW, exist_ok=True)
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "CYCLES"):
        try: sc.render.engine = eng; break
        except TypeError: continue
    if sc.render.engine == "CYCLES": sc.cycles.samples = 48
    else:
        try: sc.eevee.taa_render_samples = 32
        except AttributeError: pass
    try: sc.view_settings.view_transform = "Standard"
    except TypeError: pass
    w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes.get("Background"); bg.inputs[0].default_value = (0.70, 0.76, 0.84, 1); bg.inputs[1].default_value = 0.9
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); sun.data.energy = 3.6; sun.rotation_euler = (math.radians(48), 0, math.radians(-35))
    sc.collection.objects.link(sun)
    for m in bpy.data.materials:
        key = m.name.replace("M_Wild_", "")
        if key not in TEX: continue
        m.use_nodes = True; nt = m.node_tree; bsdf = nt.nodes.get("Principled BSDF")
        tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(os.path.join(OUT, TEX[key] + ".png"), check_existing=True)
        nt.links.new(tx.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.75
        if "Leaves" in key:
            nt.links.new(tx.outputs["Alpha"], bsdf.inputs["Alpha"])
            for attr, val in (("surface_render_method", "DITHERED"), ("blend_method", "CLIP")):
                try: setattr(m, attr, val)
                except (AttributeError, TypeError): pass
        m.use_backface_culling = False
    gm = bpy.data.materials.new("Ground"); gm.use_nodes = True; gm.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.36, 0.29, 0.20, 1)
    bpy.ops.mesh.primitive_plane_add(size=40); ground = bpy.context.active_object; ground.data.materials.append(gm)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.lens = 50
    fov = 2 * math.atan(18 / 50)

    def shoot(path, target, size, view, res=(900, 900)):
        sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
        d = size * 0.5 / math.tan(fov / 2) * 1.12
        cam.location = target + view.normalized() * d
        cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = path; bpy.ops.render.render(write_still=True)
        return path

    shots = []
    for ob in objs:
        for o in objs: o.hide_render = o is not ob
        h = max(v.co.z for v in ob.data.vertices); wd = max(max(v.co.x for v in ob.data.vertices) - min(v.co.x for v in ob.data.vertices), max(v.co.y for v in ob.data.vertices) - min(v.co.y for v in ob.data.vertices))
        size = max(h, wd) * 1.05; tgt = Vector((0, 0, h * 0.5))
        shots.append(shoot(os.path.join(PREVIEW, ob.name + "_front.png"), tgt, size, Vector((0, -1, 0.05))))
        shots.append(shoot(os.path.join(PREVIEW, ob.name + "_34.png"), tgt, size, Vector((-0.7, -0.7, 0.45))))
    for o in objs: o.hide_render = True
    # the rows: corn every 30 cm, potatoes every 50 cm, a metre apart
    rng = random.Random(5)
    corn = [o for o in objs if "Corn" in o.name]; pot = [o for o in objs if "Potato" in o.name]
    # 1: five of each in a row (the brief's picture); 2: a patch of each, rows along x a metre apart, for the far views
    for row, (src, step, y, n) in enumerate(((corn, 0.30, 0.5, 5), (pot, 0.5, -0.5, 5))):
        for i in range(n):
            d = bpy.data.objects.new(f"Row{row}_{i}", src[i % 2].data); sc.collection.objects.link(d)
            d.location = ((i - (n - 1) / 2) * step, y, 0); d.rotation_euler = (0, 0, rng.uniform(0, 2 * math.pi))
    row_objs = [o for o in sc.collection.objects if o.name.startswith("Row")]
    shots.append(shoot(os.path.join(PREVIEW, "rows_eye.png"), Vector((0, 0.0, 0.8)), 3.2, Vector((-0.55, -1, 0.32)), (1400, 900)))
    shots.append(shoot(os.path.join(PREVIEW, "rows_high.png"), Vector((0, 0.0, 0.5)), 3.6, Vector((-0.3, -1, 1.1)), (1400, 900)))
    for o in row_objs: o.hide_render = True
    for r in range(4):
        for src, step, x0, n in ((corn, 0.30, -3.2, 14), (pot, 0.5, 2.6, 9)):
            for i in range(n):
                d = bpy.data.objects.new(f"Field{r}_{x0}_{i}", src[rng.randrange(2)].data); sc.collection.objects.link(d)
                d.location = (x0 + (i - (n - 1) / 2) * step + rng.uniform(-0.04, 0.04), r * 1.0 + rng.uniform(-0.04, 0.04), 0); d.rotation_euler = (0, 0, rng.uniform(0, 2 * math.pi))
    shots.append(shoot(os.path.join(PREVIEW, "field_mid.png"), Vector((-0.3, 1.5, 0.6)), 10.0, Vector((-0.25, -1, 0.35)), (1400, 900)))
    shots.append(shoot(os.path.join(PREVIEW, "field_far.png"), Vector((-0.3, 1.5, 0.6)), 24.0, Vector((-0.2, -1, 0.25)), (1400, 900)))
    return shots


if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rec = {"textures": {"corn_stalk": corn_stalk_png(), "corn_leaves": corn_leaves_png(), "potato_stem": potato_stem_png(), "potato_leaves": potato_leaves_png()},
           "slots": {"Bark": "opaque (stalk, roots, husks, stems)", "Leaves": "masked, two-sided (leaves, tassel, silk, leaf and flower cards)"}, "meshes": {}}
    objs = []
    for kind, fn in (("Corn", build_corn), ("Potato", build_potato)):
        for v, sd in (("A", 13), ("B", 37)):
            ob, info = fn(v, sd + len(kind) * 101)
            info["fbx"] = export(ob); rec["meshes"][ob.name] = info; objs.append(ob)
            print(f"WILDCROP {ob.name}: {info}")
    json.dump(rec, open(os.path.join(OUT, "wild_crops.json"), "w"), indent=1)
    if PREVIEW: print("WILDCROPS previews", preview(objs))
    print("WILDCROPS done", OUT)
