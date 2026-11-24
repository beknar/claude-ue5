"""The list of 2026-11-22's caves, phase 16: the cave treasure map's picture (SourceArt/caves/icons16/icon_cave_treasure_map.png), drawn:
a rolled-open sheet of old parchment with a broken tower, a dotted trail and a red cross, on a clear ground, 256 x 256, as the other
cave pictures (they are the inventory's and the quick bar's). The InvokeAI server painted the phase's other pictures; this one is drawn.
Args: [out.png]
Needs numpy and Pillow (the amv-maker venv)."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

out = sys.argv[1] if len(sys.argv) > 1 else r"E:\code\claude-ue5\claude_ue5\SourceArt\caves\icons16\icon_cave_treasure_map.png"
N = 512
rng = np.random.default_rng(1616)
img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
# (the sheet: a ragged quadrilateral, slightly turned)
pts = []
corners = [(70, 95), (445, 70), (460, 420), (60, 440)]
for (a, b) in zip(corners, corners[1:] + corners[:1]):
    for t in np.linspace(0, 1, 14, endpoint=False):
        x = a[0] + (b[0] - a[0]) * t + rng.normal(0, 4)
        y = a[1] + (b[1] - a[1]) * t + rng.normal(0, 4)
        pts.append((x, y))
d.polygon(pts, fill=(214, 186, 132, 255))
# (its stains: darker blotches and a burnt edge)
arr = np.asarray(img).astype(np.float32)
yy, xx = np.mgrid[0:N, 0:N]
for _ in range(9):
    cx, cy, r = rng.uniform(90, 420), rng.uniform(100, 410), rng.uniform(30, 90)
    m = np.clip(1.0 - np.hypot(xx - cx, yy - cy) / r, 0, 1) ** 2 * 0.25
    arr[..., :3] *= (1.0 - m[..., None])
alpha = arr[..., 3] > 0
edge = np.asarray(Image.fromarray(alpha.astype(np.uint8) * 255).filter(ImageFilter.MinFilter(15))) == 0
arr[..., :3] = np.where((edge & alpha)[..., None], arr[..., :3] * 0.55, arr[..., :3])
img = Image.fromarray(arr.astype(np.uint8))
d = ImageDraw.Draw(img)
ink = (70, 45, 25, 255)
# (the broken tower at the top left: a tall shaft, its top broken)
d.polygon([(130, 300), (130, 160), (148, 140), (160, 152), (172, 132), (186, 150), (186, 300)], outline=ink, width=6)
d.line([(110, 300), (205, 300)], fill=ink, width=6)
d.arc([140, 268, 176, 316], 180, 360, fill=ink, width=5)          # (the cave's mouth at its foot)
# (hills, a trail of dots to the cross)
for hx in (250, 320):
    d.arc([hx - 40, 180, hx + 40, 260], 200, 340, fill=ink, width=5)
pts = [(205, 310), (250, 335), (300, 320), (340, 350), (375, 345)]
for a, b in zip(pts, pts[1:]):
    for t in np.linspace(0, 1, 5, endpoint=False):
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=ink)
cx, cy = 395, 345
d.line([(cx - 24, cy - 24), (cx + 24, cy + 24)], fill=(170, 30, 25, 255), width=12)
d.line([(cx - 24, cy + 24), (cx + 24, cy - 24)], fill=(170, 30, 25, 255), width=12)
img = img.resize((256, 256), Image.LANCZOS)
img.save(out)
print("cave_map_icon:", out)
