"""Frigate 4b's textures, after its reference picture (I:\\game assets\\3d unity samples\\frigate4b.jpg, the user's of
2026-11-11): the blue upper hull's plating, the white lower hull's, the dark machinery, and the "TX223" hull number as a
decal (white letters on transparency). Colours from the picture's lit flat faces (palette.json, read by
frigate4b_build.py). The platings are 16 m square on the ship (projected from each face's side, top or end).
Python (numpy, Pillow): frigate4b_textures.py <out dir>"""
import json, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
# (the picture's lit faces: blue (45,135,216) to (16,114,198), white (196,187,182) to (204,193,190), green nose and rings
# (163,244,151), the turret's grey (197,192,189) to (121,120,118), the canopy's glass (226,236,246) to (130,166,200), the
# fins' light blue (129,170,218); the intakes black)
PAL = {"blue": (38, 126, 208), "white": (198, 190, 185), "green": (120, 220, 105), "grey": (160, 158, 154), "dark": (32, 36, 40),
       "glass": (170, 200, 228), "fin": (120, 165, 216), "window": (18, 22, 28), "gun": (88, 90, 92)}
json.dump(PAL, open(os.path.join(OUT, "palette.json"), "w"), indent=1)
S = 1024


def panels(rng, x0, y0, x1, y1, depth, out):
    w, h = x1 - x0, y1 - y0
    if depth == 0 or (w < 140 and h < 140) or (depth < 3 and rng.random() < 0.2):
        out.append((x0, y0, x1, y1)); return
    if w > h * (0.8 + rng.random() * 0.6):
        c = int(x0 + w * rng.uniform(0.3, 0.7)); panels(rng, x0, y0, c, y1, depth - 1, out); panels(rng, c, y0, x1, y1, depth - 1, out)
    else:
        c = int(y0 + h * rng.uniform(0.3, 0.7)); panels(rng, x0, y0, x1, c, depth - 1, out); panels(rng, x0, c, x1, y1, depth - 1, out)


def plating(name, base, seed, seam=0.7, tone=0.035, depth=4):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), base); d = ImageDraw.Draw(img)
    rects = []; panels(rng, 0, 0, S, S, depth, rects)
    dark = lambda k: tuple(int(c * k) for c in base)
    for (x0, y0, x1, y1) in rects:
        k = 1 + rng.uniform(-tone, tone); d.rectangle((x0, y0, x1, y1), fill=tuple(min(255, int(c * k)) for c in base))
    for (x0, y0, x1, y1) in rects:
        d.rectangle((x0, y0, x1, y1), outline=dark(seam), width=3)
        if rng.random() < 0.4:
            for (cx, cy) in ((x0 + 12, y0 + 12), (x1 - 12, y1 - 12)):
                d.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=dark(0.6))
        if rng.random() < 0.15 and x1 - x0 > 140 and y1 - y0 > 70:
            # (no wider or taller than the panel leaves room for (PR #52's review: a panel 141-149 px wide gave randint an empty range))
            w, h = rng.randint(40, min(120, x1 - x0 - 31)), rng.randint(16, min(40, y1 - y0 - 25)); sx, sy = rng.randint(x0 + 15, x1 - 15 - w), rng.randint(y0 + 12, y1 - 12 - h)
            d.rectangle((sx, sy, sx + w, sy + h), outline=dark(0.65), width=3)
    a = np.asarray(img).astype(np.float32)
    a *= (0.975 + 0.025 * np.asarray(Image.effect_noise((S, S), 40).filter(ImageFilter.GaussianBlur(2))).astype(np.float32)[..., None] / 128.0)
    Image.fromarray(a.clip(0, 255).astype(np.uint8)).save(os.path.join(OUT, name)); print("TEX", name)


plating("blue.png", PAL["blue"], 41)
plating("white.png", PAL["white"], 53, seam=0.72)
img = Image.new("RGB", (S, S), PAL["dark"]); d = ImageDraw.Draw(img); rng = random.Random(9)
for y in range(0, S, 28):
    d.rectangle((0, y, S, y + 9), fill=tuple(int(c * 1.3) for c in PAL["dark"]))
for _ in range(50):
    x, y, w, h = rng.randint(0, S), rng.randint(0, S), rng.randint(30, 140), rng.randint(20, 80)
    d.rectangle((x, y, x + w, y + h), outline=tuple(int(c * 1.7) for c in PAL["dark"]), width=3)
img.save(os.path.join(OUT, "metal.png")); print("TEX metal.png")

# the hull number: bold white letters on transparency, its box the picture's (225 x 47 px: 4.8 : 1)
W, H = 1024, 213
dec = Image.new("RGBA", (W, H), (255, 255, 255, 0)); d = ImageDraw.Draw(dec)
font = None
for f in ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arial.ttf"):
    if os.path.exists(f): font = ImageFont.truetype(f, 200); break
bb = d.textbbox((0, 0), "TX223", font=font)
d.text(((W - (bb[2] - bb[0])) / 2 - bb[0], (H - (bb[3] - bb[1])) / 2 - bb[1]), "TX223", font=font, fill=(244, 246, 248, 255))
dec.save(os.path.join(OUT, "tx223.png")); print("TEX tx223.png")
print("TEXTURES DONE", OUT)
