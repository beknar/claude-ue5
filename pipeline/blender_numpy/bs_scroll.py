"""Brokenspire's map sheet as an ancient scroll (the user's of 2026-11-02: "the edges of the town overhead map should be frayed
and unraveling, like an ancient scroll"): from the painted parchment (rdm4_ui_cut.py's export, mapc_parchment.png) a square
sheet whose edges are torn (a fractal noise moves the edge in and out), unravelling (loose threads hang out of the left and
right edges, frayed fibres along every edge), worn through near them (a few holes), darkened toward them (age and soot), rolled
at the top and the bottom (a shaded roll each); outside it, transparent. Written as mapc_scroll.png beside the parchment, which
pipeline/unreal/883 imports with the others; ARDHUD::DrawTownMapColour draws it in place of the parchment when it is there.

    bs_scroll.py <export_dir> [size 1536] [seed 7]

Needs numpy and Pillow (CLAUDE.md: the amv-maker venv)."""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

D = sys.argv[1]
SIZE = int(sys.argv[2]) if len(sys.argv) > 2 else 1536
SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 7
rng = np.random.default_rng(SEED)


def fbm(shape, scales):
    """a fractal noise in [0, 1]: smooth random fields at several scales, added"""
    h, w = shape; out = np.zeros(shape, np.float32); tot = 0.0
    for sc, amp in scales:
        g = rng.random((max(2, h // sc + 2), max(2, w // sc + 2))).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        out += amp * (np.asarray(im, np.float32) / 255.0); tot += amp
    return out / tot


src = Image.open(os.path.join(D, "mapc_parchment.png")).convert("RGB")
N = SIZE
base = np.asarray(src.resize((N, N), Image.LANCZOS), np.float32) / 255.0
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
m = N * 0.045                                   # (the margin the torn edge wanders in)
roll = N * 0.05                                 # (the rolls' height, top and bottom)
# distance in from the sheet's edge (left/right to the edge, top/bottom to the rolls' outer side)
dx = np.minimum(xx, N - 1 - xx) - m * 0.5
dy = np.minimum(yy, N - 1 - yy) - m * 0.2
d = np.minimum(dx, dy)
tear = (fbm((N, N), [(10, 0.15), (40, 0.45), (130, 0.4)]) - 0.5) * m * 2.6
alpha = np.clip((d + tear) / 3.0, 0.0, 1.0)
# (the frayed fibres are drawn as threads below: a pixel noise read as speckle)
# holes worn through near the edges
for _ in range(9):
    side = rng.integers(0, 4); t_ = rng.uniform(0.1, 0.9) * N; inset = rng.uniform(m * 0.8, m * 2.2); r = rng.uniform(N * 0.004, N * 0.012)
    cx, cy = [(inset, t_), (N - inset, t_), (t_, inset + roll), (t_, N - inset - roll)][side]
    hole = np.hypot(xx - cx, yy - cy) + (fbm((N, N), [(4, 1.0)]) - 0.5) * r * 1.4
    alpha = np.minimum(alpha, np.clip((hole - r) / 2.0, 0.0, 1.0))
# age: darker and browner toward the edges and in blotches
edge_dark = np.clip(1.0 - (d + tear) / (m * 2.6), 0.0, 1.0) ** 1.6
blot = fbm((N, N), [(40, 0.6), (120, 0.4)])
col = base.copy()
burn = np.array([0.33, 0.21, 0.10], np.float32)
k = (0.68 * edge_dark + 0.14 * np.clip(blot - 0.55, 0, 1) * 2.0)[..., None]
col = col * (1.0 - k) + burn * k
# the rolls: top and bottom bands shaded as cylinders (light on the near side, dark at the turn)
for top in (True, False):
    y0 = 0.0 if top else N - roll * 1.6
    band = (yy >= y0) & (yy < y0 + roll * 1.6)
    t_ = np.clip((yy - y0) / (roll * 1.6), 0.0, 1.0)
    shade = 0.55 + 0.55 * np.sin(t_ * math.pi) if top else 0.55 + 0.55 * np.sin(t_ * math.pi)
    shade = np.where(band, shade, 1.0)[..., None]
    col = col * shade
    # (a dark line where the roll meets the sheet)
    seam_y = y0 + roll * 1.6 if top else y0
    seam = np.exp(-((yy - seam_y) ** 2) / (2 * (N * 0.002) ** 2))[..., None]
    col = col * (1.0 - 0.45 * seam)
col = np.clip(col, 0.0, 1.0)
rgba = np.dstack([col, alpha]).astype(np.float32)
img = Image.fromarray((rgba * 255).astype(np.uint8), "RGBA")
# loose threads hanging out of the left and right edges (unravelling)
dr = ImageDraw.Draw(img, "RGBA")
# (a fringe of short fibres all along the torn left and right edges, and a few long threads)
alpha_np = np.asarray(img)[..., 3]
for _ in range(420):
    left = rng.random() < 0.5
    y = int(rng.uniform(roll * 1.8, N - roll * 1.8))
    row = alpha_np[y]
    xs = np.nonzero(row > 128)[0]
    if len(xs) == 0: continue
    x = float(xs[0] if left else xs[-1])
    ang = (math.pi if left else 0.0) + rng.uniform(-0.5, 0.5); ln = rng.uniform(N * 0.003, N * 0.011)
    c = tuple(int(v * 255) for v in (0.5 + rng.uniform(-0.08, 0.08), 0.38 + rng.uniform(-0.06, 0.05), 0.22)) + (int(rng.uniform(170, 240)),)
    dr.line([(x, y), (x + math.cos(ang) * ln, y + math.sin(ang) * ln)], fill=c, width=1)
for _ in range(46):
    left = rng.random() < 0.5
    y = rng.uniform(roll * 1.8, N - roll * 1.8)
    x = m * 0.6 if left else N - m * 0.6
    ln = rng.uniform(N * 0.01, N * 0.035); ang = rng.uniform(-0.6, 0.6) + (math.pi if left else 0.0)
    pts = [(x, y)]
    for s in range(6):
        ang += rng.uniform(-0.35, 0.35)
        x += math.cos(ang) * ln / 6; y += math.sin(ang) * ln / 6 + ln * 0.04
        pts.append((x, y))
    c = tuple(int(v * 255) for v in (0.62 + rng.uniform(-0.08, 0.06), 0.5 + rng.uniform(-0.06, 0.05), 0.32)) + (int(rng.uniform(150, 230)),)
    dr.line(pts, fill=c, width=max(1, int(N / 900)))
out = os.path.join(D, "mapc_scroll.png")
img.save(out)
a = np.asarray(img)[..., 3]
print(f"bs_scroll: {out} {N}x{N}, opaque {np.mean(a > 128):.3f}, edge columns transparent: left {np.mean(a[:, 2] < 20):.2f} right {np.mean(a[:, -3] < 20):.2f}")
# the edge alone (the third list of 2026-11-02: the map zooms): the same sheet with its middle cut away, feathered over 1.5 % of
# the sheet from 9 % in, so that a map drawn over the sheet and spilling past it is framed again by the torn edge and the rolls
inner = np.clip((np.minimum(dx - m * 2.0, dy - roll * 1.4) - N * 0.0) / (N * 0.015), 0.0, 1.0)
ring = np.asarray(img).astype(np.float32)
ring[..., 3] = ring[..., 3] * (1.0 - inner)
out2 = os.path.join(D, "mapc_scroll_edge.png")
Image.fromarray(ring.astype(np.uint8), "RGBA").save(out2)
print(f"bs_scroll: {out2}, opaque {np.mean(ring[..., 3] > 128):.3f}, middle transparent {np.mean(ring[N // 3:2 * N // 3, N // 3:2 * N // 3, 3] < 5):.2f}")
