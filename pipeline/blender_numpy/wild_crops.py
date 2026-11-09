"""The wilderness's farm fields' crops that no pack has (the fields grow 13 crops, by how common they were in medieval
Europe: wheat, barley, oats, rye, peas, beans, flax, hemp, corn, potatoes, cabbages, pumpkins, sunflowers; the packs have
wheat, barley, cabbage, pumpkin and sunflower): corn (maize), potato, oats, rye, peas, field beans, flax and hemp, built
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
  Oats      SM_Wild_Oats_<A|B>, 0.9-1.0 m: a tuft of 4-7 slender stems (3 sides, leaning out, nodding at the top), three
            narrow strap leaves low on each; each stem ends in an open, drooping panicle (three crossed cards, bent over:
            whorls of long thin branches arching down, pale green-gold spikelets dangling from them). Under 500 triangles.
  Rye       SM_Wild_Rye_<A|B>, 1.45-1.6 m: 4-7 tall thin stems, bluish-green turning to straw at the top, four strap
            leaves up each; a long slender ear with long awns (two crossed cards, nodding a little), grey-green or straw
            (A mostly green, B mostly straw). Under 650 triangles.
  Peas      SM_Wild_Peas_<A|B>, 0.55-0.65 m tall, 1.1 m across: seven to nine weak vines (3 sides) arching out and down,
            a few climbing over the others, with tangled spray cards along them (paired leaflets, stipules, tendrils);
            green pods hanging (crossed cards) and white (A) or violet (B) flowers (crossed cards) at the vines' tips.
            Under 450 triangles.
  Beans     SM_Wild_Beans_<A|B>, field beans (Vicia faba), 0.9-1.05 m: two to four stiff upright square stems (4 sides);
            9-10 alternate leaves up each, two pairs of grey-green oval leaflets (one pair near the top; each leaflet a
            quad); racemes of white flowers with black blotches in the axils (crossed cards); one or two fat upright
            pods (5 sides) from the lower axils. Under 650 triangles.
  Flax      SM_Wild_Flax_<A|B>, 0.8-0.85 m: a clump of 10-15 very thin stems (3 sides) fanning up, most with a sky-blue
            flower facing up and out at the top (a quad each), over four crossed cards painted with more stems, tiny
            narrow leaves and flowers. Under 300 triangles.
  Hemp      SM_Wild_Hemp_<A|B>, 1.9-2.1 m: a single tall stalk (5 sides) bare at its foot; 9-10 nodes of opposite
            palmate leaves, turned a quarter at each, closer and smaller up the stalk: a long leaf-stalk (3 sides) and
            9, 7 or 5 serrated leaflets fanned from its end (a quad each, the outer ones hanging more); a dense cone of
            small leaves and flowers at the top (three crossed cards). Under 650 triangles.
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
            The six after them paint each card's picture in centimetres of the card it is drawn on (sizes in the
            regions' table below the imports); the stems' tubes run v 0-1 along them:
            T_Wild_OatsStem / T_Wild_RyeStem (opaque) green at the foot to straw at the top, darker bands at the nodes.
            T_Wild_OatsLeaves      (masked) u 0-0.25: the strap leaf; u 0.25-1: the panicle (18 x 25 cm).
            T_Wild_RyeLeaves       (masked) u 0-0.3: the strap leaf; u 0.3-0.65 and 0.65-1: the ear with its awns
                                   (3.5 x 18 cm), grey-green and straw.
            T_Wild_PeasStem        (opaque) pale green.
            T_Wild_PeasLeaves      (masked) v 0-0.74: a spray of five vines (26 x 20 cm) with stipules, leaflet pairs,
                                   tendrils, two pods and three flowers; v 0.75-1: four 8 cm cells: white flowers,
                                   violet flowers, two pods, one pod.
            T_Wild_BeansStem       (opaque) u 0-0.5 the square stem's dark green; u 0.5-1 the pod (four beans along
                                   v, a seam).
            T_Wild_BeansLeaves     (masked) v 0-0.6: two oval leaflets (3.6 x 6.4 cm); v 0.6-1: two racemes of white
                                   flowers with black blotches (6 x 5 cm).
            T_Wild_FlaxStem        (opaque) green.
            T_Wild_FlaxLeaves      (masked) u 0-0.75: the clump of stems with tiny leaves and flowers (30 x 80 cm);
                                   u 0.75-1: two open flowers (3.2 cm), sky-blue and a little lilac.
            T_Wild_HempStem        (opaque) ridged green.
            T_Wild_HempLeaves      (masked) u 0-0.25 and 0.25-0.5: a serrated leaflet (2.4 x 14 cm), dark and lighter;
                                   u 0.5-1: the top's cone of small palmate leaves and flowers (30 x 45 cm).
Material slots (each mesh two, as wild_trees.py's trees, so 887's trees() pattern applies):
  0 M_Wild_<Kind>Bark   (opaque: stalks, stems, vines, nodes, roots, husks, pods) <- T_Wild_CornStalk / T_Wild_<Kind>Stem
  1 M_Wild_<Kind>Leaves (masked, two-sided: leaves, leaflets, tassel, silk, heads, spray, flower and pod cards)
                        <- T_Wild_<Kind>Leaves
Writes into out_dir: SM_Wild_<Kind>_<A|B>.fbx (Kind: Corn, Potato, Oats, Rye, Peas, Beans, Flax, Hemp), the 16 PNGs,
wild_crops.json (each mesh's height, width, triangles; "kind_textures": each kind's [bark, leaves] texture names, which
the Unreal import reads). Z up, metres (exported x100 to cm as the trees), origin at the plant's foot on the ground; any yaw.
With preview_dir also renders (Eevee, or Cycles when Eevee cannot) each plant from the front and three-quarter, a short
row of corn and one of potatoes a metre apart, four rows of each of the six others (rows_<kind>.png) and a field of six
strips of them (field6_mid.png, field6_far.png), into preview_dir.
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

TEX = {"CornBark": "T_Wild_CornStalk", "CornLeaves": "T_Wild_CornLeaves", "PotatoBark": "T_Wild_PotatoStem", "PotatoLeaves": "T_Wild_PotatoLeaves",
       "OatsBark": "T_Wild_OatsStem", "OatsLeaves": "T_Wild_OatsLeaves", "RyeBark": "T_Wild_RyeStem", "RyeLeaves": "T_Wild_RyeLeaves",
       "PeasBark": "T_Wild_PeasStem", "PeasLeaves": "T_Wild_PeasLeaves", "BeansBark": "T_Wild_BeansStem", "BeansLeaves": "T_Wild_BeansLeaves",
       "FlaxBark": "T_Wild_FlaxStem", "FlaxLeaves": "T_Wild_FlaxLeaves", "HempBark": "T_Wild_HempStem", "HempLeaves": "T_Wild_HempLeaves"}
# atlas regions (u0, u1, v0, v1)
CORN_LEAF = (0.0, 0.75, 0.0, 1.0); CORN_TASSEL = (0.75, 1.0, 0.5, 1.0); CORN_SILK = (0.75, 1.0, 0.0, 0.5)
STALK_U = (0.0, 0.4); HUSK_U = (0.4, 0.7); ROOT_U = (0.7, 1.0)
POT_LEAF = (0.0, 1.0, 0.0, 0.74)
POT_FLOWER = [(0.25 * k + 0.012, 0.25 * k + 0.238, 0.762, 0.988) for k in range(4)]   # inset: no bleeding from the next picture
# the six kinds after them: each card's picture is painted in centimetres of the card it is drawn on (the size noted)
GRAIN_NODES = (0.22, 0.42, 0.62)                                   # oats' and rye's nodes, as fractions of the stem (its v)
OATS_LEAF = (0.0, 0.25, 0.0, 1.0); OATS_PANICLE = (0.25, 1.0, 0.0, 1.0)                    # panicle card 18 x 25 cm
RYE_LEAF = (0.0, 0.3, 0.0, 1.0); RYE_EAR = [(0.3, 0.65, 0.0, 1.0), (0.65, 1.0, 0.0, 1.0)]  # ear cards 3.5 x 18 cm: grey-green, straw
PEA_SPRAY = (0.0, 1.0, 0.0, 0.74)                                                         # 26 x 20 cm
PEA_CELL = [(0.25 * k + 0.012, 0.25 * k + 0.238, 0.762, 0.988) for k in range(4)]         # 8 x 8 cm: white, violet flowers; two pods
BEAN_LEAFLET = [(0.0, 0.5, 0.0, 0.6), (0.5, 1.0, 0.0, 0.6)]                                # 3.6 x 6.4 cm
BEAN_FLOWER = [(0.0, 0.5, 0.6, 1.0), (0.5, 1.0, 0.6, 1.0)]                                 # 6 x 5 cm
BEAN_STEM_U = (0.0, 0.5); BEAN_POD_U = (0.5, 1.0)
FLAX_CARD = (0.0, 0.75, 0.0, 1.0)                                                         # 30 x 80 cm
FLAX_FLOWER = [(0.75, 1.0, 0.0, 0.5), (0.75, 1.0, 0.5, 1.0)]                               # 3.2 x 3.2 cm
HEMP_LEAFLET = [(0.0, 0.25, 0.0, 1.0), (0.25, 0.5, 0.0, 1.0)]                              # 2.4 x 14 cm
HEMP_TOP = (0.5, 1.0, 0.0, 1.0)                                                           # 30 x 45 cm


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


# the six kinds after corn and potato: helpers that paint in centimetres of a card
def rxy(U, V, reg, w, h, inset=0.004):
    """a region's pixels in centimetres of its card (x 0 at its middle, y 0 at its foot), and the mask inside it"""
    u0, u1, v0, v1 = reg
    m = (U > u0 + inset) & (U < u1 - inset) & (V > v0 + inset) & (V < v1 - inset)
    return (U - u0) / (u1 - u0) * w - w * 0.5, (V - v0) / (v1 - v0) * h, m


def put(rgba, mask, col, nz, shade=None, var=0.28):
    if not mask.any(): return
    c = np.array(col, float)[None, :] * (1 - var * 0.5 + var * nz[mask])[:, None]
    if shade is not None: c = c * np.broadcast_to(shade, mask.shape)[mask][:, None]
    rgba[mask, :3] = np.clip(c, 0, 1); rgba[mask, 3] = 1.0


def polyline(X, Y, pts, w):
    m = np.zeros(X.shape, bool)
    for a, b in zip(pts, pts[1:]): m |= line_mask(X, Y, a, b, w)
    return m


def stem_png(key, base, top, seed, lines=10, nodes=(), node_col=None, n=512):
    """an opaque stem: base colour at v 0 easing to the top colour at v 1 (the stems' tubes run v 0-1 along them),
    faint lines along v, a band at each node's v"""
    U, V = grid(n); nz = noise(n, seed)
    col = mix(np.broadcast_to(np.array(base, float), (n, n, 3)).copy(), top, smooth(0.1, 1.0, V))
    col = col * (0.86 + 0.24 * nz)[..., None] * (0.9 + 0.1 * (0.5 + 0.5 * np.sin(U * 2 * math.pi * lines + nz * 2.0)))[..., None]
    for v in nodes: col = mix(col, node_col, 0.75 * (1 - smooth(0.004, 0.012, np.abs(V - v))))
    rgba = np.concatenate([np.clip(col, 0, 1), np.ones((n, n, 1))], -1)
    return save_png(TEX[key], rgba)


def grass_leaf(rgba, U, V, reg, base, tip, nz):
    """a narrow grass leaf across the region, base to tip along v (the strip's shape gives its taper)"""
    u0, u1, v0, v1 = reg
    lu = (U - u0) / (u1 - u0); lv = (V - v0) / (v1 - v0); d = np.abs(lu - 0.5)
    col = np.array(base)[None, None, :] * (0.86 + 0.24 * nz[..., None])
    col = col * (0.92 + 0.08 * (0.5 + 0.5 * np.sin(lu * 2 * math.pi * 7)))[..., None]   # parallel veins
    col = mix(col, np.array(base) * 1.6, 0.5 * (1 - smooth(0.02, 0.06, d)))               # the paler midrib
    col = mix(col, tip, 0.75 * smooth(0.55, 1.0, lv))                                   # dry toward the tip
    m = (U > u0 + 0.004) & (U < u1 - 0.004) & (V >= v0) & (V <= v1) & (d < 0.47 + 0.012 * np.sin(lv * 57))
    rgba[m, :3] = np.clip(col[m], 0, 1); rgba[m, 3] = 1.0


def oats_leaves_png(n=512):
    U, V = grid(n); nz = noise(n, 71); rng = np.random.default_rng(71)
    rgba = np.zeros((n, n, 4))
    grass_leaf(rgba, U, V, OATS_LEAF, (0.30, 0.47, 0.17), (0.62, 0.60, 0.32), nz)
    # the panicle: a rachis with whorls of branches spreading out and drooping, spikelets hanging from them
    X, Y, ins = rxy(U, V, OATS_PANICLE, 18.0, 25.0)
    gold = (0.68, 0.73, 0.47); straw = (0.52, 0.58, 0.32)
    def rach(t): return (0.6 * math.sin(t * 2.6), 0.3 + 23.4 * t)
    put(rgba, polyline(X, Y, [rach(t) for t in np.linspace(0, 1, 9)], 0.14) & ins, straw, nz)
    hang = []
    for i, t in enumerate((0.08, 0.27, 0.45, 0.62, 0.78)):  # few whorls, long thin branches: an open, airy head
        p = rach(t); nb = 3 if i < 2 else 2; Lw = lerp(9.0, 3.6, t / 0.78)
        for b in range(nb):
            sgn = (1 if (b + i) % 2 == 0 else -1) if b < 2 else (1 if rng.random() < 0.5 else -1)
            L = Lw * rng.uniform(0.7, 1.0); a, a1 = math.radians(rng.uniform(30, 55)), math.radians(rng.uniform(-85, -60))
            pts = [p]; q = p
            for s in range(6):
                aa = lerp(a, a1, ((s + 0.5) / 6) ** 1.2); q = (q[0] + sgn * math.cos(aa) * L / 6, q[1] + math.sin(aa) * L / 6); pts.append(q)
            put(rgba, polyline(X, Y, pts, 0.07) & ins, straw, nz)
            hang.append(pts[-1])
            if rng.random() < 0.7: hang.append(pts[int(rng.integers(3, 5))])
    hang.append(rach(1.0))
    for q in hang:                                             # each a pedicel and a pendulous two-flowered spikelet
        tilt = rng.uniform(-0.3, 0.3); pl = rng.uniform(0.5, 1.1)
        bot = (q[0] + math.sin(tilt) * pl, q[1] - math.cos(tilt) * pl)
        put(rgba, line_mask(X, Y, q, bot, 0.05) & ins, straw, nz)
        hl = rng.uniform(1.1, 1.4); c = (bot[0] + math.sin(tilt) * hl, bot[1] - math.cos(tilt) * hl)
        r2, x, y = ellipse_mask(X, Y, c, hl, hl * 0.36, tilt - math.pi / 2)
        shade = 0.82 + 0.32 * np.clip(r2, 0, 1)                # the papery glumes paler at their rims
        shade = np.where(np.abs(y) < hl * 0.05, 0.8, shade)    # the line between the two glumes
        put(rgba, (r2 < 1) & ins, gold, nz, shade)
    return save_png(TEX["OatsLeaves"], np.clip(rgba, 0, 1))


def rye_leaves_png(n=512):
    U, V = grid(n); nz = noise(n, 81); rng = np.random.default_rng(81)
    rgba = np.zeros((n, n, 4))
    grass_leaf(rgba, U, V, RYE_LEAF, (0.34, 0.47, 0.35), (0.66, 0.62, 0.42), nz)
    for k, reg in enumerate(RYE_EAR):                          # a slender two-ranked ear with long awns
        X, Y, ins = rxy(U, V, reg, 3.5, 18.0)
        ear, awn, stalk = (((0.50, 0.58, 0.48), (0.64, 0.68, 0.54), (0.44, 0.54, 0.42)) if k == 0 else
                           ((0.78, 0.69, 0.44), (0.86, 0.78, 0.54), (0.70, 0.64, 0.42)))
        put(rgba, line_mask(X, Y, (0, 0), (0, 11.4), 0.09) & ins, stalk, nz)
        ns = 22
        for i in range(ns):
            y = 1.4 + i * 0.45; sgn = 1 if i % 2 else -1; taper = 1 - 0.4 * (i / ns) ** 2
            ang = math.pi / 2 - sgn * math.radians(16); c = (sgn * 0.2 * taper, y + 0.45)
            r2, x, yy = ellipse_mask(X, Y, c, 0.55, 0.22 * taper, ang)
            put(rgba, (r2 < 1) & ins, ear, nz, 0.82 + 0.3 * np.clip(r2, 0, 1))
            tip = (c[0] + math.cos(ang) * 0.5, c[1] + math.sin(ang) * 0.5)
            for _ in range(2):
                end = (tip[0] + sgn * rng.uniform(0.05, 0.55) * (1.25 - i / ns), tip[1] + rng.uniform(4.0, 6.2))
                put(rgba, line_mask(X, Y, tip, end, 0.028) & ins, awn, nz)
    return save_png(TEX["RyeLeaves"], np.clip(rgba, 0, 1))


def peas_leaves_png(n=512):
    U, V = grid(n); nz = noise(n, 91); rng = np.random.default_rng(91)
    rgba = np.zeros((n, n, 4))
    vine = (0.40, 0.56, 0.30); stip = (0.37, 0.55, 0.36); tend = (0.48, 0.62, 0.32); podc = (0.47, 0.64, 0.30)
    lf = [(0.30, 0.48, 0.31), (0.34, 0.52, 0.34), (0.27, 0.44, 0.28)]
    white, violet, wing = (0.95, 0.95, 0.92), (0.80, 0.64, 0.92), (0.52, 0.24, 0.56)
    def leaflet(X, Y, ins, c, a, L, W, col):
        r2, x, y = ellipse_mask(X, Y, c, L, W, a)
        put(rgba, (r2 < 1) & ins, col, nz, np.where(np.abs(y) < W * 0.08, 1.2, 0.85 + 0.25 * np.clip(1 - r2, 0, 1)))
    def tendril(X, Y, ins, p, a, L, curl):
        pts = [p]; q = p
        for s in range(10):
            a += curl * (0.2 + s * 0.07); q = (q[0] + math.cos(a) * L / 10, q[1] + math.sin(a) * L / 10); pts.append(q)
        put(rgba, polyline(X, Y, pts, 0.045) & ins, tend, nz)
    def pod(X, Y, ins, p, a, L, W):
        put(rgba, line_mask(X, Y, p, (p[0] + math.cos(a) * 0.6, p[1] + math.sin(a) * 0.6), 0.05) & ins, vine, nz)
        c = (p[0] + math.cos(a) * (L + 0.5), p[1] + math.sin(a) * (L + 0.5))
        r2, x, y = ellipse_mask(X, Y, c, L, W, a)
        put(rgba, (r2 < 1) & ins, podc, nz, np.where(y > W * 0.25, 1.18, 0.88 + 0.12 * np.clip(1 - r2, 0, 1)))
    def flower(X, Y, ins, p, r, col):
        put(rgba, ((X - p[0]) ** 2 + (Y - p[1]) ** 2 < r * r) & ins, col, nz, var=0.12)            # the standard
        for s in (-1, 1):                                                                       # the wings
            r2, x, y = ellipse_mask(X, Y, (p[0] + s * r * 0.55, p[1] - r * 0.75), r * 0.7, r * 0.42, math.pi / 2 + s * 0.6)
            put(rgba, (r2 < 1) & ins, wing if col == violet else (0.88, 0.90, 0.84), nz, var=0.12)
    # the spray, v 0-0.74: weak vines from the foot's middle, at each node two stipules and a leaf of two pairs of
    # leaflets ending in tendrils; a pod hangs from two of them, flowers at the others' tips
    X, Y, ins = rxy(U, V, PEA_SPRAY, 26.0, 20.0)
    o = (0.0, 0.4)
    for k, (a0, L) in enumerate(((-1.15, 12.5), (-0.6, 15.5), (-0.05, 17.0), (0.55, 15.5), (1.1, 12.5))):
        pts = [o]; q = o; a = math.pi / 2 - a0
        for s in range(9):
            a += rng.uniform(-0.35, 0.35); q = (q[0] + math.cos(a) * L / 9, q[1] + math.sin(a) * L / 9); pts.append(q)
        put(rgba, polyline(X, Y, pts, 0.09) & ins, vine, nz)
        for j, s in enumerate((2, 4, 6, 8)):
            p = pts[s]; d = math.atan2(pts[s + 1][1] - p[1], pts[s + 1][0] - p[0])
            sgn = 1 if (j + k) % 2 else -1
            for ss in (-1, 1): leaflet(X, Y, ins, (p[0] + math.cos(d + ss * 1.6) * 0.55, p[1] + math.sin(d + ss * 1.6) * 0.55), d + ss * 1.2, 0.8, 0.52, stip)
            la = d + sgn * rng.uniform(0.5, 0.9); pl = rng.uniform(2.6, 3.4)
            tip = (p[0] + math.cos(la) * pl, p[1] + math.sin(la) * pl)
            put(rgba, line_mask(X, Y, p, tip, 0.05) & ins, vine, nz)
            for f in (0.42, 0.88):
                b = (p[0] + math.cos(la) * pl * f, p[1] + math.sin(la) * pl * f)
                for ss in (-1, 1):
                    fa = la + ss * rng.uniform(0.7, 1.0); L_ = rng.uniform(1.0, 1.3)
                    leaflet(X, Y, ins, (b[0] + math.cos(fa) * L_ * 0.95, b[1] + math.sin(fa) * L_ * 0.95), fa, L_, L_ * 0.62, lf[int(rng.integers(3))])
            for _ in range(2): tendril(X, Y, ins, tip, la + rng.uniform(-0.4, 0.4), rng.uniform(1.8, 2.8), (1 if rng.random() < 0.5 else -1) * rng.uniform(0.25, 0.4))
        if k in (1, 3): pod(X, Y, ins, pts[5], -math.pi / 2 + rng.uniform(-0.35, 0.35), 2.6, 0.55)
        else: flower(X, Y, ins, (pts[-1][0], pts[-1][1] + 0.6), 0.75, white if k != 2 else violet)
    # four cells, v 0.75-1: white flowers, violet flowers, two pods (from the cell's foot middle, which hangs down)
    for k, reg in enumerate(PEA_CELL):
        X, Y, ins = rxy(U, V, reg, 8.0, 8.0, inset=0.0)
        if k < 2:
            for f, (dx, dy) in enumerate(((-1.8, 4.6), (1.6, 5.4), (0.0, 6.4))):
                put(rgba, line_mask(X, Y, (0, 0.3), (dx, dy - 0.8), 0.08) & ins, vine, nz)
                leaflet(X, Y, ins, (dx * 0.5, dy * 0.45), math.atan2(dy, dx) + 1.2, 0.9, 0.5, stip)
                flower(X, Y, ins, (dx, dy), 1.05, white if k == 0 else violet)
        else:
            for f, (a, L) in enumerate(((math.pi / 2 + 0.18, 2.9), (math.pi / 2 - 0.2, 2.6)) if k == 2 else ((math.pi / 2 + 0.08, 3.1),)):
                pod(X, Y, ins, (0.0, 0.3), a, L, 0.62)
    return save_png(TEX["PeasLeaves"], np.clip(rgba, 0, 1))


def beans_stem_png(n=512):
    U, V = grid(n); nz = noise(n, 61)
    col = np.zeros((n, n, 3))
    face = np.abs(((U / 0.5) * 4) % 1.0 - 0.5)                                         # four faces of the square stem
    st = np.array((0.27, 0.39, 0.20))[None, None, :] * (0.86 + 0.24 * nz)[..., None] * (1.0 + 0.18 * smooth(0.36, 0.5, face))[..., None]
    st = st * (0.92 + 0.08 * np.sin(U * 2 * math.pi * 24 + nz * 2))[..., None]
    pu = (U - 0.5) / 0.5
    bump = 0.5 + 0.5 * np.cos(V * 2 * math.pi * 4.0)                                    # the beans inside, four along it
    pod = np.array((0.40, 0.56, 0.22))[None, None, :] * (0.86 + 0.2 * nz)[..., None] * (0.84 + 0.22 * bump)[..., None]
    pod = mix(pod, (0.26, 0.36, 0.14), 0.7 * (1 - smooth(0.01, 0.03, np.abs(pu - 0.5))))   # the seam
    pod = mix(pod, (0.30, 0.38, 0.16), 0.5 * (smooth(0.9, 1.0, V) + smooth(0.08, 0.0, V)))  # its ends
    col = np.where((U < 0.5)[..., None], st, pod)
    rgba = np.concatenate([np.clip(col, 0, 1), np.ones((n, n, 1))], -1)
    return save_png(TEX["BeansBark"], rgba)


def beans_leaves_png(n=512):
    U, V = grid(n); nz = noise(n, 101); rng = np.random.default_rng(101)
    rgba = np.zeros((n, n, 4))
    for k, reg in enumerate(BEAN_LEAFLET):                   # an oval, grey-green, fleshy leaflet with a short stalk
        X, Y, ins = rxy(U, V, reg, 3.6, 6.4)
        col = (0.38, 0.48, 0.36) if k == 0 else (0.33, 0.44, 0.30)
        t = np.clip((Y - 0.25) / 5.9, 0, 1)
        hw = 1.66 * np.sin(np.pi * t) ** 0.7 * (0.88 + 0.2 * t)
        m = ins & (np.abs(X) < hw) & (Y > 0.25) & (Y < 6.15)
        stalk = ins & (np.abs(X) < 0.09) & (Y <= 0.6)
        shade = (0.92 + 0.08 * np.sin((Y - np.abs(X) * 0.9) * 5.0)) * (0.86 + 0.22 * (1 - np.abs(X) / np.maximum(hw, 0.05)))
        shade = np.where(np.abs(X) < 0.06, 1.25, shade)
        put(rgba, m | stalk, col, nz, shade)
    for k, reg in enumerate(BEAN_FLOWER):                    # a raceme of white flowers, each with a black blotch on its wings
        X, Y, ins = rxy(U, V, reg, 6.0, 5.0)
        nfl = 3 if k == 0 else 4
        put(rgba, line_mask(X, Y, (0, 0.1), (0, 0.5 + 0.6 * (nfl - 1)), 0.1) & ins, (0.32, 0.46, 0.22), nz)
        for f in range(nfl):
            sgn = 1 if f % 2 else -1; el = math.radians(rng.uniform(-5, 30))
            d = (sgn * math.cos(el), math.sin(el)); nrm = (-d[1], d[0]) if sgn > 0 else (d[1], -d[0])
            p = (0.0, 0.5 + 0.6 * f)
            def at(a, b): return (p[0] + d[0] * a + nrm[0] * b, p[1] + d[1] * a + nrm[1] * b)
            ang = math.atan2(d[1], d[0])
            r2, x, y = ellipse_mask(X, Y, at(1.15, 0.42), 0.78, 0.52, ang + sgn * 0.6)          # the standard, veined
            put(rgba, (r2 < 1) & ins, (0.95, 0.94, 0.93), nz, 0.9 + 0.1 * np.sin(y * 14.0), var=0.1)
            r2, x, y = ellipse_mask(X, Y, at(0.35, 0.0), 0.36, 0.2, ang)                         # the calyx
            put(rgba, (r2 < 1) & ins, (0.34, 0.48, 0.25), nz)
            r2, x, y = ellipse_mask(X, Y, at(1.0, 0.0), 0.56, 0.32, ang)                         # wings and keel
            put(rgba, (r2 < 1) & ins, (0.92, 0.92, 0.88), nz, var=0.1)
            c = at(1.1, 0.06)
            put(rgba, ((X - c[0]) ** 2 + (Y - c[1]) ** 2 < 0.22 ** 2) & ins, (0.07, 0.05, 0.06), nz, var=0.1)
    return save_png(TEX["BeansLeaves"], np.clip(rgba, 0, 1))


def flax_flower(rgba, X, Y, ins, nz, c, r, a0, blue):
    for p in range(5):
        a = a0 + p * 2 * math.pi / 5
        r2, x, y = ellipse_mask(X, Y, (c[0] + math.cos(a) * r * 0.5, c[1] + math.sin(a) * r * 0.5), r * 0.54, r * 0.4, a)
        put(rgba, (r2 < 1) & ins, blue, nz, (0.86 + 0.18 * np.clip(1 - r2, 0, 1)) * (0.93 + 0.07 * np.sin(y / r * 30)), var=0.14)
    put(rgba, ((X - c[0]) ** 2 + (Y - c[1]) ** 2 < (r * 0.2) ** 2) & ins, (0.93, 0.90, 0.70), nz, var=0.1)


def flax_leaves_png(n=512):
    U, V = grid(n); nz = noise(n, 111); rng = np.random.default_rng(111)
    rgba = np.zeros((n, n, 4))
    stemc, leafc, blue = (0.38, 0.54, 0.25), (0.33, 0.50, 0.26), (0.46, 0.61, 0.90)
    # the card, u 0-0.75: a clump of thin stems with tiny narrow leaves, branching at the top into sky-blue flowers
    X, Y, ins = rxy(U, V, FLAX_CARD, 30.0, 80.0)
    for s in range(9):
        x0 = rng.uniform(-4.0, 4.0); h = rng.uniform(60, 76); x1 = x0 * 1.5 + rng.uniform(-9, 9); bow = rng.uniform(-2, 2)
        def at(t): return (lerp(x0, x1, t) + bow * math.sin(math.pi * t), 0.5 + h * t)
        put(rgba, polyline(X, Y, [at(t) for t in np.linspace(0, 1, 10)], 0.1) & ins, stemc, nz)
        for j, t in enumerate(np.arange(0.1, 0.86, 0.04)):
            p = at(t); sg = 1 if j % 2 else -1
            a = math.pi / 2 - sg * math.radians(rng.uniform(22, 38)); L = rng.uniform(1.6, 2.4)
            r2, x, y = ellipse_mask(X, Y, (p[0] + math.cos(a) * L * 0.5, p[1] + math.sin(a) * L * 0.5), L * 0.5, 0.15, a)
            put(rgba, (r2 < 1) & ins, leafc, nz)
        tops = [at(1.0)]
        for b in range(int(rng.integers(2, 5))):
            sp = at(rng.uniform(0.86, 0.97)); a = math.pi / 2 + rng.uniform(-0.8, 0.8); L = rng.uniform(2.5, 5.0)
            e = (sp[0] + math.cos(a) * L, sp[1] + math.sin(a) * L)
            put(rgba, line_mask(X, Y, sp, e, 0.08) & ins, stemc, nz); tops.append(e)
        for e in tops:
            if rng.random() < 0.55: flax_flower(rgba, X, Y, ins, nz, e, rng.uniform(1.1, 1.4), rng.uniform(0, 6.3), blue)
            else:
                r2, x, y = ellipse_mask(X, Y, e, 0.6, 0.35, math.pi / 2); put(rgba, (r2 < 1) & ins, (0.38, 0.52, 0.42), nz)
    # two flower pictures, u 0.75-1: one open flower each (sky-blue; a little lilac)
    for k, reg in enumerate(FLAX_FLOWER):
        X, Y, ins = rxy(U, V, reg, 3.2, 3.2)
        flax_flower(rgba, X, Y, ins, nz, (0.0, 1.6), 1.45, 0.3 + k, blue if k == 0 else (0.54, 0.58, 0.88))
    return save_png(TEX["FlaxLeaves"], np.clip(rgba, 0, 1))


def hemp_leaves_png(n=512):
    U, V = grid(n); nz = noise(n, 121); rng = np.random.default_rng(121)
    rgba = np.zeros((n, n, 4))
    for k, reg in enumerate(HEMP_LEAFLET):                   # a long lanceolate leaflet, serrated, pointed
        X, Y, ins = rxy(U, V, reg, 2.4, 14.0)
        col = (0.15, 0.33, 0.09) if k == 0 else (0.22, 0.42, 0.13)
        t = np.clip((Y - 0.3) / 13.5, 0, 1)
        hw = np.where(t < 0.32, 1.08 * (t / 0.32) ** 0.75, 1.08 * ((1 - t) / 0.68) ** 1.25)
        hw = hw * (1 - 0.18 * ((Y * 2.4) % 1.0))               # the teeth, pointing forward
        m = ins & (np.abs(X) < hw) & (Y > 0.3)
        stalk = ins & (np.abs(X) < 0.07) & (Y < 0.6)
        shade = (0.92 + 0.08 * np.sin((Y - np.abs(X) * 1.3) * 4.5)) * (0.86 + 0.22 * (1 - np.abs(X) / np.maximum(hw, 0.05)))
        shade = np.where(np.abs(X) < 0.06, 1.4, shade)
        put(rgba, m | stalk, col, nz, shade)
    # the top, u 0.5-1: a cone of small palmate leaves in opposite pairs round the stem, flower clusters near the top
    X, Y, ins = rxy(U, V, HEMP_TOP, 30.0, 45.0)
    put(rgba, line_mask(X, Y, (0, 0), (0, 43.5), 0.22) & ins, (0.30, 0.45, 0.18), nz)
    greens = [(0.15, 0.33, 0.09), (0.20, 0.40, 0.12), (0.17, 0.36, 0.10)]
    for i, t in enumerate(np.linspace(0.03, 0.9, 10)):
        y = 44.0 * t
        for sgn in (-1, 1):
            reach = lerp(13.5, 3.5, t) * rng.uniform(0.8, 1.0)
            c = (sgn * reach * 0.3, y + reach * 0.18)
            put(rgba, line_mask(X, Y, (0, y), c, 0.1) & ins, (0.28, 0.44, 0.16), nz)
            nl = 7 if t < 0.4 else 5 if t < 0.7 else 3
            th0 = (0.0 if sgn > 0 else math.pi) + sgn * rng.uniform(0.15, 0.45)
            for j in range(nl):
                f = j - (nl - 1) / 2; th = th0 + f * 0.42; L = reach * 0.7 * (1 - 0.16 * abs(f))
                cc = (c[0] + math.cos(th) * L * 0.5, c[1] + math.sin(th) * L * 0.5)
                r2, x, yy = ellipse_mask(X, Y, cc, L * 0.5, L * 0.09, th)
                put(rgba, (r2 < 1) & ins, greens[int(rng.integers(3))], nz, np.where(np.abs(yy) < L * 0.012, 1.35, 0.85 + 0.25 * np.clip(1 - r2, 0, 1)))
    for _ in range(18):                                      # the flowers: green bracts with a few pale pistils
        y = rng.uniform(24, 43); x = rng.uniform(-1.8, 1.8) * (1.2 - y / 44.0) * 2
        r = rng.uniform(0.5, 0.9)
        put(rgba, ((X - x) ** 2 + ((Y - y) / 1.4) ** 2 < r * r) & ins, (0.30, 0.45, 0.16), nz)
        for _ in range(2):
            px, py = x + rng.uniform(-r, r) * 0.8, y + rng.uniform(-r, r)
            put(rgba, ((X - px) ** 2 + (Y - py) ** 2 < 0.1 ** 2) & ins, (0.80, 0.78, 0.66), nz, var=0.1)
    return save_png(TEX["HempLeaves"], np.clip(rgba, 0, 1))


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


def dir_of(yaw, el):
    return Vector((math.cos(el) * math.cos(yaw), math.cos(el) * math.sin(yaw), math.sin(el)))


def flat_side(d, roll=0.0):
    """a horizontal width across the direction d (its card faces up), rolled about d"""
    s = d.cross(Vector((0, 0, 1)))
    s = s.normalized() if s.length > 1e-6 else Vector((1, 0, 0))
    return Matrix.Rotation(roll, 3, d) @ s


def crossed(bm, uvl, base, along, width, reg, n=2, a0=0.0, bend=None):
    """n cards about the line `along` from base, a0 the first one's turn"""
    a = along.normalized(); s0 = flat_side(a)
    for k in range(n):
        card(bm, uvl, base, along, (Matrix.Rotation(a0 + k * math.pi / n, 3, a) @ s0) * width, 1, reg, bend=bend)


def grain_stems(bm, uvl, rng, ns, H, head_len, head_w, head_regs, head_cards, r0, leaf_reg, leaf_ts, leaf_L, leaf_W, leaf_e1, lean_deg, nod, head_bend):
    """a tuft of grass stems from one foot: each a 3-sided tube (v 0-1 along it, so GRAIN_NODES fall on its nodes),
    strap leaves from its nodes, a head of crossed cards from its top nodding outward"""
    a0 = rng.uniform(0, 2 * math.pi)
    for s in range(ns):
        yaw = a0 + s * 2 * math.pi / ns + rng.uniform(-0.4, 0.4); out = Vector((math.cos(yaw), math.sin(yaw), 0))
        lean = math.radians(rng.uniform(*lean_deg)); h = H * rng.uniform(0.86, 1.0)
        hl = head_len * rng.uniform(0.88, 1.08) * (h / H); sh = h - hl * 0.9
        nd = rng.uniform(*nod) * sh
        foot = out * rng.uniform(0.005, 0.02) + Vector((0, 0, -0.01))
        def at(t): return foot + out * (math.sin(lean) * sh * t + nd * t ** 3) + Vector((0, 0, sh * t))
        ts = [0.0, 0.2, 0.42, 0.62, 0.82, 1.0]
        pts = [at(t) for t in ts]
        tube(bm, uvl, pts, [r0 * (1 - 0.45 * t) for t in ts], 3, 0, (0.0, 1.0), 1.0 / sh)
        for t in leaf_ts:
            ly = yaw + rng.choice((-1, 1)) * rng.uniform(0.3, 1.6)
            leaf(bm, uvl, at(t), ly, rng.uniform(*leaf_L), rng.uniform(*leaf_W), math.radians(82), math.radians(rng.uniform(42, 62)),
                 math.radians(rng.uniform(*leaf_e1)), rng.uniform(-0.35, 0.35), rng.uniform(-0.3, 0.3), 3, 1, leaf_reg, fold=0.12, base_w=0.6)
        d = (pts[-1] - pts[-2]).normalized()
        along = (d + out * 0.25).normalized() * hl
        bend = (out * 0.35 + Vector((0, 0, -0.3))) * hl * rng.uniform(*head_bend)
        crossed(bm, uvl, pts[-1] - d * 0.01, along, hl * head_w, head_regs(rng), head_cards, rng.uniform(0, math.pi), bend)


def build_oats(variant, seed):
    rng = random.Random(seed)
    me, ob, bm, uvl = new_mesh(f"SM_Wild_Oats_{variant}")
    ns = rng.randint(4, 6) if variant == "A" else rng.randint(6, 7)
    H = rng.uniform(0.85, 1.05)
    grain_stems(bm, uvl, rng, ns, H, rng.uniform(0.21, 0.25), 18.0 / 25.0, lambda r: OATS_PANICLE, 3, 0.0028, OATS_LEAF,
                (0.04, GRAIN_NODES[0], GRAIN_NODES[1]), (0.18, 0.28), (0.012, 0.015), (-35, 0), (4, 13), (0.04, 0.09), (0.45, 0.8))
    info = finish(me, ob, bm, "Oats"); info["stems"] = ns
    return ob, info


def build_rye(variant, seed):
    rng = random.Random(seed)
    me, ob, bm, uvl = new_mesh(f"SM_Wild_Rye_{variant}")
    ns = rng.randint(4, 6) if variant == "A" else rng.randint(6, 7)
    H = rng.uniform(1.35, 1.65)
    straw = 0.3 if variant == "A" else 0.7                  # the share of its ears turned to straw
    grain_stems(bm, uvl, rng, ns, H, rng.uniform(0.19, 0.22), 3.5 / 18.0, lambda r: RYE_EAR[1 if r.random() < straw else 0], 2, 0.0026, RYE_LEAF,
                (0.06,) + GRAIN_NODES, (0.18, 0.28), (0.012, 0.016), (-45, -10), (2, 9), (0.02, 0.05), (0.2, 0.45))
    info = finish(me, ob, bm, "Rye"); info["stems"] = ns
    return ob, info


def build_peas(variant, seed):
    rng = random.Random(seed)
    me, ob, bm, uvl = new_mesh(f"SM_Wild_Peas_{variant}")
    nv = rng.randint(7, 8) if variant == "A" else rng.randint(8, 9)
    a0 = rng.uniform(0, 2 * math.pi); vines = []
    for s in range(nv):
        yaw = a0 + s * 2 * math.pi / nv + rng.uniform(-0.35, 0.35)
        climb = s % 3 == 0                                   # a few vines climb over the others
        e = math.radians(rng.uniform(76, 82) if climb else rng.uniform(56, 70))
        fall = math.radians(rng.uniform(48, 60) if climb else rng.uniform(65, 90))
        L = rng.uniform(0.6, 0.7) if climb else rng.uniform(0.4, 0.54)
        p = Vector((math.cos(yaw) * 0.02, math.sin(yaw) * 0.02, -0.01)); pts = [p.copy()]; wy = 0.0
        for i in range(4):
            t = (i + 0.5) / 4; wy += rng.uniform(-0.3, 0.3)
            p = p + dir_of(yaw + wy, e - fall * t) * (L / 4); p.z = max(p.z, 0.04); pts.append(p.copy())
        tube(bm, uvl, pts, [0.004, 0.0035, 0.003, 0.0025, 0.002], 3, 0)
        vines.append((pts, yaw))
        for k, t in enumerate((0.2, 0.4, 0.6, 0.8, 1.0)):    # spray cards along the vine, every way (tangled)
            i0 = min(int(t * 4), 3); q = lerp(pts[i0], pts[i0 + 1], t * 4 - i0)
            fy = yaw + (rng.uniform(-0.4, 0.4) if t == 1.0 else (1 if k % 2 else -1) * rng.uniform(0.4, 1.4))
            cl = rng.uniform(0.17, 0.21)
            along = dir_of(fy, math.radians(rng.uniform(-5, 40))) * cl
            card(bm, uvl, q - along * 0.3, along, flat_side(along.normalized(), rng.uniform(-0.6, 0.6)) * cl * 1.3, 1, PEA_SPRAY,
                 bend=Vector((0, 0, -cl * rng.uniform(0.15, 0.4))))
    top_z = max(max(v.z for v in pts) for pts, _ in vines)
    for k in range(5):                                       # a crown of cards over the middle
        fy = a0 + k * 2 * math.pi / 5 + rng.uniform(-0.4, 0.4); cl = rng.uniform(0.16, 0.2)
        along = dir_of(fy, math.radians(rng.uniform(20, 50))) * cl
        card(bm, uvl, Vector((0, 0, top_z * rng.uniform(0.55, 0.7))) - along * 0.2, along, flat_side(along.normalized()) * cl * 1.3, 1, PEA_SPRAY,
             bend=Vector((0, 0, -cl * 0.35)))
    npod = rng.randint(4, 5) if variant == "A" else rng.randint(5, 6)
    for k in range(npod):                                    # pods hanging from the vines
        pts, yaw = vines[(k * 3 + 1) % len(vines)]
        q = lerp(pts[2], pts[3], rng.uniform(0.0, 0.8)) + Vector((0, 0, -0.01))
        crossed(bm, uvl, q, Vector((math.cos(yaw) * 0.015, math.sin(yaw) * 0.015, -0.085)), 0.085, PEA_CELL[2 + k % 2], 2, rng.uniform(0, math.pi))
    nf = rng.randint(3, 4) if variant == "A" else rng.randint(4, 5)
    for k in range(nf):                                      # flowers at the vines' tips (white; violet for B)
        pts, yaw = vines[(k * 2) % len(vines)]
        crossed(bm, uvl, pts[-1] - Vector((0, 0, 0.01)), Vector((math.cos(yaw) * 0.025, math.sin(yaw) * 0.025, 0.075)), 0.08,
                PEA_CELL[0 if variant == "A" else 1], 2, rng.uniform(0, math.pi))
    info = finish(me, ob, bm, "Peas"); info["vines"] = nv; info["pods"] = npod; info["flower_clusters"] = nf
    return ob, info


def build_beans(variant, seed):
    rng = random.Random(seed)
    me, ob, bm, uvl = new_mesh(f"SM_Wild_Beans_{variant}")
    nst = rng.randint(2, 3) if variant == "A" else rng.randint(3, 4)
    H = rng.uniform(0.85, 1.15); a0 = rng.uniform(0, 2 * math.pi); npods = 0
    for s in range(nst):
        yaw = a0 + s * 2 * math.pi / nst + rng.uniform(-0.4, 0.4); out = Vector((math.cos(yaw), math.sin(yaw), 0))
        h = H * (1.0 if s == 0 else rng.uniform(0.82, 0.97)); lean = math.radians(rng.uniform(3, 8)); ph = rng.uniform(0, 6.3)
        foot = out * 0.02 + Vector((0, 0, -0.01))
        def sp(t): return foot + out * (math.sin(lean) * h * t) + Vector((0.006 * math.sin(t * 7 + ph), 0.006 * math.cos(t * 6 + ph), h * t))
        tube(bm, uvl, [sp(i / 5) for i in range(6)], [0.006 * (1 - 0.4 * i / 5) for i in range(6)], 4, 0, BEAN_STEM_U, 1.0 / h)
        rank = rng.uniform(0, 2 * math.pi); nl = 10 if nst <= 3 else 9; leaf_yaws = []
        for i in range(nl):                                  # alternate leaves of two pairs of leaflets (one pair near the top)
            x = i / (nl - 1); node = sp(0.1 + 0.86 * x ** 0.85)
            ly = rank + math.pi * (i % 2) + rng.uniform(-0.6, 0.6); leaf_yaws.append((node, ly))
            r = dir_of(ly, math.radians(lerp(28, 55, x) + rng.uniform(-8, 8))); hp = Vector((-math.sin(ly), math.cos(ly), 0))
            Ll = lerp(0.10, 0.062, x) * rng.uniform(0.9, 1.1)
            for pj in range(2 if x < 0.7 else 1):
                b = node + r * (0.012 + pj * 0.035)
                for sg in (-1, 1):
                    a = math.radians(rng.uniform(25, 50) - pj * 10)
                    d = r * math.cos(a) + hp * (math.sin(a) * sg); d.z -= rng.uniform(0.0, 0.35); d.normalize()
                    card(bm, uvl, b, d * Ll, flat_side(d, rng.uniform(-0.4, 0.4)) * Ll * 0.56, 1, BEAN_LEAFLET[rng.randrange(2)])
        tip = sp(1.0)                                        # the growing tip: two small leaflets held up
        for sg in (-1, 1):
            d = dir_of(rank + sg * 1.4, math.radians(62)); card(bm, uvl, tip, d * 0.04, flat_side(d) * 0.024, 1, BEAN_LEAFLET[0])
        for i in rng.sample(range(2, 6), 3):                 # flower clusters in the axils of the middle leaves
            node, ly = leaf_yaws[i]; fy = ly + rng.uniform(-0.8, 0.8)
            crossed(bm, uvl, node + Vector((math.cos(fy), math.sin(fy), 0)) * 0.006,
                    (Vector((math.cos(fy), math.sin(fy), 0)) * 0.45 + Vector((0, 0, 1))).normalized() * 0.06, 0.072, BEAN_FLOWER[rng.randrange(2)], 2, rng.uniform(0, 1))
        for i in rng.sample(range(1, 4), 1 if variant == "A" else rng.randint(1, 2)):   # upright fat pods from the lower axils
            node, ly = leaf_yaws[i]; fy = ly + rng.uniform(-0.5, 0.5); tilt = math.radians(rng.uniform(22, 42))
            d = Vector((math.cos(fy) * math.sin(tilt), math.sin(fy) * math.sin(tilt), math.cos(tilt))); L = rng.uniform(0.10, 0.14)
            o = node + Vector((math.cos(fy), math.sin(fy), 0)) * 0.008; ox = Vector((math.cos(fy), math.sin(fy), 0)) * 0.012
            tube(bm, uvl, [o, o + d * L * 0.25, o + d * L * 0.7 + ox, o + d * L + ox * 1.6], [0.003, 0.0095, 0.0095, 0.0025], 5, 0, BEAN_POD_U, 1.0 / L)
            npods += 1
    info = finish(me, ob, bm, "Beans"); info["stems"] = nst; info["pods"] = npods
    return ob, info


def build_flax(variant, seed):
    rng = random.Random(seed)
    me, ob, bm, uvl = new_mesh(f"SM_Wild_Flax_{variant}")
    ns = rng.randint(10, 12) if variant == "A" else rng.randint(13, 15)
    H = rng.uniform(0.66, 0.86); a0 = rng.uniform(0, 2 * math.pi); nfl = 0
    for s in range(ns):                                      # thin stems fanning up from one foot, flowers at their tops
        yaw = a0 + s * 2 * math.pi / ns + rng.uniform(-0.3, 0.3); out = Vector((math.cos(yaw), math.sin(yaw), 0))
        h = H * rng.uniform(0.82, 1.0); sp = rng.uniform(0.03, 0.11)
        foot = out * rng.uniform(0.0, 0.05) + Vector((0, 0, -0.01))
        pts = [foot + out * (sp * t ** 1.5) + Vector((0, 0, h * t)) for t in (0.0, 0.35, 0.7, 1.0)]
        tube(bm, uvl, pts, [0.0019, 0.0016, 0.0013, 0.0011], 3, 0, (0.0, 1.0), 1.0 / h)
        for f in range(0 if rng.random() < 0.35 else 1):
            fy = yaw + rng.uniform(-0.9, 0.9); tilt = math.radians(rng.uniform(30, 60))
            nrm = Vector((math.cos(fy) * math.sin(tilt), math.sin(fy) * math.sin(tilt), math.cos(tilt)))
            along = nrm.cross(Vector((-math.sin(fy), math.cos(fy), 0))).normalized(); side = nrm.cross(along)
            fs = rng.uniform(0.028, 0.034)
            c = pts[-1] + (Vector((math.cos(fy), math.sin(fy), 0)) * 0.015 + Vector((0, 0, -0.02)) if f else Vector((0, 0, 0.004)))
            card(bm, uvl, c - along * fs * 0.5, along * fs, side * fs, 1, FLAX_FLOWER[rng.randrange(2)]); nfl += 1
    sc = H / 0.8                                             # the painted clump is 80 cm tall
    crossed(bm, uvl, Vector((0, 0, -0.01)), Vector((0, 0, 0.8 * sc)), 0.30 * sc, FLAX_CARD, 4, rng.uniform(0, math.pi))
    info = finish(me, ob, bm, "Flax"); info["stems"] = ns; info["flowers"] = nfl
    return ob, info


def build_hemp(variant, seed):
    rng = random.Random(seed)
    me, ob, bm, uvl = new_mesh(f"SM_Wild_Hemp_{variant}")
    H = rng.uniform(1.7, 1.95) if variant == "A" else rng.uniform(2.05, 2.35)
    lean = Vector((rng.uniform(-0.02, 0.02), rng.uniform(-0.02, 0.02), 0)); ph = rng.uniform(0, 6.28)
    def at(z): return Vector((0, 0, z)) + lean * z + Vector((0.01 * math.sin(z * 2.3 + ph), 0.01 * math.cos(z * 1.9 + ph), 0)) * z
    top = H * 0.94; r0 = rng.uniform(0.010, 0.012)
    def rad(z): return r0 * (1.0 - 0.72 * min(z / top, 1.0))
    zs = [0.0, 0.06] + [top * f for f in (0.18, 0.32, 0.45, 0.57, 0.68, 0.78, 0.87, 1.0)]
    tube(bm, uvl, [at(z) for z in zs], [rad(z) * (1.15 if z == 0 else 1.0) for z in zs], 5, 0, (0.0, 1.0), 2.0)
    n = 9 if variant == "A" else 10; rank = rng.uniform(0, 2 * math.pi); nleaves = 0
    for i in range(n):                                       # opposite pairs, turned a quarter at each node, closer and smaller up the stalk
        x = i / (n - 1); z = H * (0.25 + 0.6 * (1 - (1 - x) ** 1.5))
        for side_ in (0, 1):
            yaw = rank + i * math.pi / 2 + side_ * math.pi + rng.uniform(-0.25, 0.25)
            lp = lerp(0.11, 0.05, x) * rng.uniform(0.9, 1.1); e0 = math.radians(lerp(30, 45, x) + rng.uniform(-8, 8))
            p0 = at(z) + Vector((math.cos(yaw), math.sin(yaw), 0)) * rad(z) * 0.8
            p1 = p0 + dir_of(yaw, e0) * lp * 0.5; p2 = p1 + dir_of(yaw, e0 - 0.6) * lp * 0.5
            tube(bm, uvl, [p0, p1, p2], [0.0028, 0.0022, 0.0017], 3, 0)
            nlf = 9 if x < 0.3 else 7 if x < 0.65 else 5
            Lc = lerp(0.22, 0.12, x) * rng.uniform(0.9, 1.1); spread = math.radians(lerp(200, 150, x))
            for j in range(nlf):                             # the leaflets fanned from the stalk's end, the outer ones hanging more
                f = j / (nlf - 1) * 2 - 1; a = yaw + f * spread / 2
                L = Lc * (1 - 0.6 * abs(f) ** 1.6)
                el = -math.radians(lerp(12, 50, abs(f)) + rng.uniform(-8, 8)) + (math.radians(15) if x > 0.7 else 0.0)
                d = dir_of(a, el)
                card(bm, uvl, p2, d * L, flat_side(d, rng.uniform(-0.35, 0.35)) * L * (2.4 / 14.0), 1, HEMP_LEAFLET[0 if rng.random() < 0.7 else 1])
            nleaves += 1
    zb = H * 0.72                                            # the dense top: three crossed cards
    crossed(bm, uvl, at(zb), at(H) - at(zb), (H - zb) * 30.0 / 45.0, HEMP_TOP, 3, rng.uniform(0, math.pi))
    info = finish(me, ob, bm, "Hemp"); info["leaves"] = nleaves
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
    for o in sc.collection.objects:
        if o.name.startswith("Field"): o.hide_render = True
    # the six kinds after them: four rows of each (its step along the row, the rows' gap), then a field of six strips
    spacing = {"Oats": (0.18, 0.30), "Rye": (0.18, 0.30), "Peas": (0.35, 0.60), "Beans": (0.30, 0.60), "Flax": (0.15, 0.25), "Hemp": (0.35, 0.50)}
    for kind, (step, gap) in spacing.items():
        src = [o for o in objs if o.name.startswith(f"SM_Wild_{kind}_")]
        if not src: continue
        h = max(v.co.z for v in src[0].data.vertices); n = int(3.2 / step); made = []
        for r in range(4):
            for i in range(n):
                d = bpy.data.objects.new(f"KRow_{kind}_{r}_{i}", src[rng.randrange(2)].data); sc.collection.objects.link(d); made.append(d)
                d.location = ((i - (n - 1) / 2) * step + rng.uniform(-0.03, 0.03), r * gap + rng.uniform(-0.03, 0.03), 0); d.rotation_euler = (0, 0, rng.uniform(0, 2 * math.pi))
        shots.append(shoot(os.path.join(PREVIEW, f"rows_{kind.lower()}.png"), Vector((0, gap * 1.5, h * 0.5)), max(3.0, h * 2.0), Vector((-0.5, -1, 0.38)), (1400, 900)))
        for d in made: d.hide_render = True
    # the field: each kind a strip 2 m across of rows running away from the camera, 7 m long
    for k, (kind, (step, gap)) in enumerate(spacing.items()):
        src = [o for o in objs if o.name.startswith(f"SM_Wild_{kind}_")]
        if not src: continue
        x0 = (k - 2.5) * 2.4
        for r in range(int(2.0 / gap) + 1):
            for i in range(int(7.0 / step)):
                d = bpy.data.objects.new(f"KField_{kind}_{r}_{i}", src[rng.randrange(2)].data); sc.collection.objects.link(d)
                d.location = (x0 - 1.0 + r * gap + rng.uniform(-0.03, 0.03), i * step + rng.uniform(-0.03, 0.03), 0); d.rotation_euler = (0, 0, rng.uniform(0, 2 * math.pi))
    shots.append(shoot(os.path.join(PREVIEW, "field6_mid.png"), Vector((0, 3.0, 0.6)), 15.0, Vector((-0.1, -1, 0.35)), (1600, 900)))
    shots.append(shoot(os.path.join(PREVIEW, "field6_far.png"), Vector((0, 3.0, 0.6)), 30.0, Vector((-0.1, -1, 0.22)), (1600, 900)))
    return shots


if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rec = {"textures": {"corn_stalk": corn_stalk_png(), "corn_leaves": corn_leaves_png(), "potato_stem": potato_stem_png(), "potato_leaves": potato_leaves_png(),
                        "oats_stem": stem_png("OatsBark", (0.34, 0.50, 0.20), (0.62, 0.64, 0.36), 72, nodes=GRAIN_NODES, node_col=(0.45, 0.42, 0.22)),
                        "oats_leaves": oats_leaves_png(),
                        "rye_stem": stem_png("RyeBark", (0.39, 0.50, 0.38), (0.74, 0.67, 0.43), 82, nodes=GRAIN_NODES, node_col=(0.46, 0.40, 0.26)),
                        "rye_leaves": rye_leaves_png(),
                        "peas_stem": stem_png("PeasBark", (0.40, 0.56, 0.32), (0.46, 0.62, 0.36), 92),
                        "peas_leaves": peas_leaves_png(),
                        "beans_stem": beans_stem_png(), "beans_leaves": beans_leaves_png(),
                        "flax_stem": stem_png("FlaxBark", (0.34, 0.50, 0.24), (0.42, 0.58, 0.30), 112),
                        "flax_leaves": flax_leaves_png(),
                        "hemp_stem": stem_png("HempBark", (0.30, 0.42, 0.18), (0.30, 0.46, 0.17), 122, lines=24),
                        "hemp_leaves": hemp_leaves_png()},
           "kind_textures": {k: [TEX[k + "Bark"], TEX[k + "Leaves"]] for k in ("Corn", "Potato", "Oats", "Rye", "Peas", "Beans", "Flax", "Hemp")},
           "slots": {"Bark": "opaque (stalks, stems, vines, roots, husks, pods)",
                     "Leaves": "masked, two-sided (leaves, leaflets, tassel, silk, heads, spray, flower and pod cards)"}, "meshes": {}}
    objs = []
    for kind, fn in (("Corn", build_corn), ("Potato", build_potato), ("Oats", build_oats), ("Rye", build_rye), ("Peas", build_peas),
                     ("Beans", build_beans), ("Flax", build_flax), ("Hemp", build_hemp)):
        for v, sd in (("A", 13), ("B", 37)):
            ob, info = fn(v, sd + len(kind) * 101)
            info["fbx"] = export(ob); rec["meshes"][ob.name] = info; objs.append(ob)
            print(f"WILDCROP {ob.name}: {info}")
    json.dump(rec, open(os.path.join(OUT, "wild_crops.json"), "w"), indent=1)
    if PREVIEW: print("WILDCROPS previews", preview(objs))
    print("WILDCROPS done", OUT)
