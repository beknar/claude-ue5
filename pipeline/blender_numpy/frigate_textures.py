"""The frigate's textures, after its reference picture (I:\\game assets\\3d unity samples\\frigate2.png, the user's of
2026-11-11): the light grey hull plating with its panel seams, holes and markings, the dark deck plates, the red trim,
the dark machinery; colours from the picture's lit faces (palette.json, which frigate_build.py reads). Each texture is
16 m square on the ship (frigate_build.py projects them from the side, top or end of each face).
Python (numpy, Pillow): frigate_textures.py <out dir>"""
import json, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
# (the picture's lit flat faces: hull (188,192,204) to (151,156,168), the deck plates (81,91,107), the red (166,45,51), its
# shaded recess (65,5,15), the machinery (39,45,55), the lights' cores (166,234,252))
PAL = {"hull": (176, 180, 190), "deck": (74, 80, 92), "red": (156, 34, 42), "red_dark": (70, 14, 22), "metal": (44, 49, 58),
       "blue": (96, 186, 255), "window": (150, 225, 255)}
json.dump(PAL, open(os.path.join(OUT, "palette.json"), "w"), indent=1)
S = 1024                                                                          # (16 m: 64 px a metre)


def panels(rng, x0, y0, x1, y1, depth, out):
    """the square split into plates, as a plater lays them: long plates, cut across now and then"""
    w, h = x1 - x0, y1 - y0
    if depth == 0 or (w < 140 and h < 140) or (depth < 3 and rng.random() < 0.18):
        out.append((x0, y0, x1, y1)); return
    if w > h * (0.8 + rng.random() * 0.6):
        c = int(x0 + w * rng.uniform(0.3, 0.7)); panels(rng, x0, y0, c, y1, depth - 1, out); panels(rng, c, y0, x1, y1, depth - 1, out)
    else:
        c = int(y0 + h * rng.uniform(0.3, 0.7)); panels(rng, x0, y0, x1, c, depth - 1, out); panels(rng, x0, c, x1, y1, depth - 1, out)


def plating(name, base, seed, seam=0.62, tone=0.05, rivets=True, marks=True, slots=True, depth=6):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), base); d = ImageDraw.Draw(img)
    rects = []; panels(rng, 0, 0, S, S, depth, rects)
    dark = lambda k: tuple(int(c * k) for c in base)
    for (x0, y0, x1, y1) in rects:
        k = 1 + rng.uniform(-tone, tone)
        d.rectangle((x0, y0, x1, y1), fill=tuple(min(255, int(c * k)) for c in base))
    for (x0, y0, x1, y1) in rects:                                                # (the seams: a dark line, a light lip under it)
        d.rectangle((x0, y0, x1, y1), outline=dark(seam), width=3)
        d.line([(x0 + 3, y1 - 4), (x1 - 3, y1 - 4)], fill=tuple(min(255, int(c * 1.08)) for c in base), width=1)
        if rivets and rng.random() < 0.55:                                          # (fastener holes near a plate's corners)
            for (cx, cy) in ((x0 + 14, y0 + 14), (x1 - 14, y0 + 14), (x0 + 14, y1 - 14), (x1 - 14, y1 - 14)):
                d.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=dark(0.55), outline=dark(0.8), width=2)
        if slots and rng.random() < 0.18 and x1 - x0 > 120 and y1 - y0 > 80:        # (an access hatch or a vent slot)
            w, h = rng.randint(40, min(160, x1 - x0 - 40)), rng.randint(18, min(70, y1 - y0 - 30))
            sx, sy = rng.randint(x0 + 20, x1 - 20 - w), rng.randint(y0 + 15, y1 - 15 - h)
            d.rectangle((sx, sy, sx + w, sy + h), outline=dark(0.6), width=3)
        if marks and rng.random() < 0.12 and x1 - x0 > 160:                        # (stencil marks: rows of short dashes)
            mx, my = x0 + 24, y0 + 30
            for row in range(rng.randint(1, 3)):
                xx = mx
                for _ in range(rng.randint(4, 9)):
                    ln = rng.randint(4, 12); d.line([(xx, my + row * 12), (xx + ln, my + row * 12)], fill=dark(0.5), width=2); xx += ln + 4
    a = np.asarray(img).astype(np.float32)
    a *= (0.97 + 0.03 * np.asarray(Image.effect_noise((S, S), 40).filter(ImageFilter.GaussianBlur(2))).astype(np.float32)[..., None] / 128.0)
    Image.fromarray(a.clip(0, 255).astype(np.uint8)).save(os.path.join(OUT, name)); print("TEX", name)


plating("hull.png", PAL["hull"], 11, tone=0.035, depth=4)                         # (the picture's hull: big plain plates)
plating("deck.png", PAL["deck"], 23, seam=0.55, tone=0.08, marks=False)
plating("red.png", PAL["red"], 37, seam=0.6, tone=0.04, rivets=False, marks=False, slots=False)
# the machinery: dark ribbed metal (pipes and ribs across, bolts)
img = Image.new("RGB", (S, S), PAL["metal"]); d = ImageDraw.Draw(img); rng = random.Random(5)
for y in range(0, S, 32):
    d.rectangle((0, y, S, y + 10), fill=tuple(int(c * 1.25) for c in PAL["metal"]))
    d.line([(0, y + 11), (S, y + 11)], fill=tuple(int(c * 0.6) for c in PAL["metal"]), width=2)
for _ in range(60):
    x, y, w, h = rng.randint(0, S), rng.randint(0, S), rng.randint(30, 160), rng.randint(20, 90)
    d.rectangle((x, y, x + w, y + h), outline=tuple(int(c * 1.5) for c in PAL["metal"]), width=3)
img.save(os.path.join(OUT, "metal.png")); print("TEX metal.png")
print("TEXTURES DONE", OUT)
