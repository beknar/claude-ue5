"""Brokenspire's quest board's papers (the user's of 2026-11-02: "the quest board in town has no papers on it to indicate
quests"; the board pack's own "notes" mesh is the board's plank face): a bounty notice drawn from the painted parchment
(rdm4_ui_cut.py's export, mapc_parchment.png): a crop of it, a heading in heavy ink strokes, lines of handwriting (wavy ink
strokes, no letters), a red wax seal, the paper's edges darkened and a little torn. Written as mapc_notice.png beside the
parchment; pipeline/unreal/883 imports it (T_BS_mapc_notice), 882 makes the notices' material and piece (Town.Notice), and
RDTownPlan.cpp pins notices on the board.

    bs_notice.py <export_dir> [seed 11]

Needs numpy and Pillow (CLAUDE.md: the amv-maker venv)."""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

D = sys.argv[1]
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 11
rng = np.random.default_rng(SEED)
W, H = 384, 512
src = Image.open(os.path.join(D, "mapc_parchment.png")).convert("RGB")
sw, sh = src.size
crop = src.crop((sw * 0.2, sh * 0.15, sw * 0.2 + sw * 0.45, sh * 0.15 + sw * 0.45 * H / W)).resize((W, H), Image.LANCZOS)
img = crop.convert("RGBA")
dr = ImageDraw.Draw(img, "RGBA")
ink = (52, 34, 20, 235)
# the heading: three heavy strokes across the top ("WANTED" as a mark, not letters)
for k in range(3):
    y = 70 + k * 6 + rng.uniform(-2, 2)
    dr.line([(60, y), (W - 60, y + rng.uniform(-3, 3))], fill=ink, width=7 if k == 1 else 3)
# a rough drawing of a beast's head in a box
dr.rectangle([110, 110, W - 110, 250], outline=ink, width=3)
cx, cy = W / 2, 182
pts = [(cx + math.cos(a) * (48 + rng.uniform(-6, 6)), cy + math.sin(a) * (40 + rng.uniform(-6, 6))) for a in np.linspace(0, 2 * math.pi, 14)]
dr.line(pts + [pts[0]], fill=ink, width=3)
for sx in (-1, 1): dr.line([(cx + sx * 30, cy - 34), (cx + sx * 46, cy - 62)], fill=ink, width=3)
dr.ellipse([cx - 22, cy - 12, cx - 10, cy], fill=ink); dr.ellipse([cx + 10, cy - 12, cx + 22, cy], fill=ink)
# lines of handwriting: wavy strokes broken into words
y = 285
while y < H - 70:
    x = 50
    while x < W - 60:
        wl = rng.uniform(18, 60)
        pts = [(x + t, y + 3 * math.sin((x + t) * 0.35 + rng.uniform(0, 6)) + rng.uniform(-1, 1)) for t in np.linspace(0, wl, 10)]
        dr.line(pts, fill=(60, 40, 24, 210), width=2)
        x += wl + rng.uniform(8, 16)
    y += 26
# the reward line, bolder, and the seal
dr.line([(60, H - 55), (W * 0.55, H - 57)], fill=ink, width=5)
sx, sy, r = W - 85, H - 70, 30
seal = [(sx + math.cos(a) * (r + rng.uniform(-4, 3)), sy + math.sin(a) * (r + rng.uniform(-4, 3))) for a in np.linspace(0, 2 * math.pi, 22)]
dr.polygon(seal, fill=(150, 22, 18, 255)); dr.ellipse([sx - 16, sy - 16, sx + 16, sy + 16], outline=(95, 10, 8, 255), width=4)
# aged edges: darker toward the border, a few nicks
a = np.asarray(img).astype(np.float32)
yy, xx = np.mgrid[0:H, 0:W]
d = np.minimum.reduce([xx, W - 1 - xx, yy, H - 1 - yy]).astype(np.float32)
k = np.clip(1.0 - d / 40.0, 0, 1)[..., None] ** 1.5 * 0.55
a[..., :3] = a[..., :3] * (1 - k) + np.array([70, 45, 22], np.float32) * k
alpha = np.where(d < 2, 0, 255).astype(np.float32)
for _ in range(10):
    side = rng.integers(0, 4); t = rng.uniform(0.05, 0.95); r = rng.uniform(4, 11)
    cx2, cy2 = [(0, t * H), (W, t * H), (t * W, 0), (t * W, H)][side]
    alpha = np.where(np.hypot(xx - cx2, yy - cy2) < r, 0, alpha)
a[..., 3] = alpha
out = os.path.join(D, "mapc_notice.png")
Image.fromarray(a.astype(np.uint8)).save(out)
print("bs_notice:", out, W, "x", H)
