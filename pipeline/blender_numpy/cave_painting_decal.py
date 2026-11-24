"""The list of 2026-11-22's caves, phase 15: the cave painting's decal (SourceArt/caves/painting16_decal.png), laid on a flat stretch of
a cave set's wall (RDCave16g.cpp). Drawn, not cut from the item's painted icon: cut and scaled up, the icon's figures were soft blobs
that read as a red smear on the wall (the test's pictures). Here: two hunters with spears, a stag between them, three hand prints
and a sun at the top left (it also tells the picture's way up and its side in the game's pictures), in a red ochre with rough
edges (the strokes jittered, the paint thinned by a noise), on a clear ground, 1024 x 1024.
Args: [out.png]   (default SourceArt/caves/painting16_decal.png)
Needs numpy and Pillow (the amv-maker venv)."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\caves"
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SA, "painting16_decal.png")
N = 1024
rng = np.random.default_rng(16)
mask = Image.new("L", (N, N), 0)
d = ImageDraw.Draw(mask)


def jit(p, a=4.0):
    return (p[0] + rng.normal(0, a), p[1] + rng.normal(0, a))


def stroke(pts, w):
    """a brush stroke along pts, its points jittered and its width varied"""
    pts = [jit(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        d.line([a, b], fill=255, width=int(max(3, w + rng.normal(0, w * 0.15))))
        r = w * 0.5
        d.ellipse([b[0] - r, b[1] - r, b[0] + r, b[1] + r], fill=255)


def blob(cx, cy, rx, ry, rot=0.0):
    pts = []
    for k in range(28):
        t = 2 * math.pi * k / 28
        rr = 1.0 + rng.normal(0, 0.05)
        x, y = rx * math.cos(t) * rr, ry * math.sin(t) * rr
        pts.append((cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot)))
    d.polygon(pts, fill=255)


def hunter(x, y, s, spear_way):
    """a hunter standing at (x, y) (his feet), s tall"""
    blob(x, y - s * 0.90, s * 0.07, s * 0.08)                                  # head
    stroke([(x, y - s * 0.80), (x + s * 0.02, y - s * 0.45)], s * 0.09)        # body
    stroke([(x + s * 0.02, y - s * 0.45), (x - s * 0.12, y)], s * 0.05)        # legs
    stroke([(x + s * 0.02, y - s * 0.45), (x + s * 0.14, y)], s * 0.05)
    hx = x + spear_way * s * 0.22
    stroke([(x, y - s * 0.72), (hx, y - s * 0.62)], s * 0.04)                  # arm to the spear
    stroke([(x - spear_way * s * 0.10, y - s * 0.25), (hx + spear_way * s * 0.30, y - s * 1.05)], s * 0.025)   # spear
    tip = (hx + spear_way * s * 0.30, y - s * 1.05)
    d.polygon([jit(tip, 2), jit((tip[0] - spear_way * s * 0.06, tip[1] + s * 0.02), 2), jit((tip[0] - spear_way * s * 0.01, tip[1] + s * 0.08), 2)], fill=255)


def stag(x, y, s):
    """a stag facing right, its hooves on y, s long"""
    blob(x, y - s * 0.55, s * 0.36, s * 0.16, -0.05)                           # body
    for fx in (-0.26, -0.16, 0.18, 0.28):                                       # legs
        stroke([(x + fx * s, y - s * 0.45), (x + fx * s + s * 0.03, y - s * 0.22), (x + fx * s, y)], s * 0.045)
    stroke([(x + s * 0.30, y - s * 0.62), (x + s * 0.44, y - s * 0.86)], s * 0.10)   # neck
    blob(x + s * 0.50, y - s * 0.90, s * 0.09, s * 0.05, 0.4)                  # head
    stroke([(x - s * 0.36, y - s * 0.60), (x - s * 0.44, y - s * 0.52)], s * 0.04)   # tail
    for side in (-1, 1):                                                        # antlers
        base = (x + s * 0.47, y - s * 0.95)
        tip = (base[0] + side * s * 0.10 - s * 0.05, base[1] - s * 0.40)
        stroke([base, tip], s * 0.03)
        for f in (0.35, 0.6, 0.85):
            p = (base[0] + (tip[0] - base[0]) * f, base[1] + (tip[1] - base[1]) * f)
            stroke([p, (p[0] + side * s * 0.10 + s * 0.04, p[1] - s * 0.06)], s * 0.025)


def hand(x, y, s, rot):
    blob(x, y, s * 0.22, s * 0.26, rot)
    for a, ln in ((-0.9, 0.42), (-0.35, 0.55), (0.0, 0.6), (0.35, 0.55), (0.8, 0.4)):
        t = rot - math.pi / 2 + a
        stroke([(x + math.cos(t) * s * 0.2, y + math.sin(t) * s * 0.2), (x + math.cos(t) * s * ln, y + math.sin(t) * s * ln)], s * 0.09)


ground = 830
hunter(250, ground, 330, 1)
stag(560, ground, 360)
hunter(850, ground - 10, 310, -1)
# (a sun at the top left: rays round a disc)
blob(170, 170, 62, 62)
for k in range(10):
    t = 2 * math.pi * k / 10
    stroke([(170 + math.cos(t) * 85, 170 + math.sin(t) * 85), (170 + math.cos(t) * 125, 170 + math.sin(t) * 125)], 14)
for hx, hy, r in ((720, 170, 0.3), (840, 230, -0.2), (930, 150, 0.15)):
    hand(hx, hy, 120, r)
stroke([(120, ground + 40), (920, ground + 30)], 10)                            # the ground line

# (the paint thinned by a noise: blotchy at the strokes' edges, as paint on rock)
m = np.asarray(mask.filter(ImageFilter.GaussianBlur(2.2))).astype(np.float32) / 255.0
noise = np.asarray(Image.fromarray((rng.random((N // 16, N // 16)) * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC)).astype(np.float32) / 255.0
fine = rng.random((N, N)).astype(np.float32)
a = np.clip(m * (0.75 + 0.35 * noise) - 0.10 * fine, 0.0, 1.0)
a = np.clip((a - 0.18) / 0.55, 0.0, 1.0)
img = np.zeros((N, N, 4), np.uint8)
img[..., 0], img[..., 1], img[..., 2] = 176, 58, 28          # (a red ochre light enough to read on the dark rock: 122, 34, 18 did not)
img[..., 3] = (a * 255).astype(np.uint8)
Image.fromarray(img).save(out)
print(f"cave_painting_decal: {out} {N}x{N}, {float((a > 0.2).mean()) * 100:.1f} % painted")
