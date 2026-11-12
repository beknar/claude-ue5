"""The summoner witch's textures, drawn from her reference picture (E:\\temp\\summoner.jpg, the user's of 2026-11-10): the
colours are sampled from it (palette.json, which witch_build.py reads), the face is cut from it (levelled by the eyes,
faded into her skin), and the costume's patterns (the hat's band and brim, the cape's border, the boots' stitching, the
dress's V-neck and hem) are drawn after it.
Each texture's layout is the UV layout witch_build.py gives its mesh: u round the part (0.5 her front, 0 and 1 her back),
v along it (the picture's top row is v = 1).
Python (numpy, Pillow): witch_textures.py <reference.jpg> <out dir>"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

REF, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
im = Image.open(REF).convert("RGB")
A = np.asarray(im).astype(np.float32)


def sample(x, y, r=4):
    """the median colour of a small patch of the picture (its pixel coordinates)"""
    p = A[y - r:y + r + 1, x - r:x + r + 1].reshape(-1, 3)
    return tuple(int(v) for v in np.median(p, axis=0))


# ---------------------------------------------------------------- the palette (points picked on the picture)
PAL = {
    "skin": sample(560, 412, 3), "hair": (238, 182, 96), "hair_dark": (201, 142, 70),
    "hat": sample(420, 290, 5), "gold": sample(600, 925, 3), "band_red": sample(540, 185, 3),
    "cape_out": sample(985, 960, 6), "cape_in": sample(330, 930, 6), "dress": sample(560, 820, 6),
    "belt": sample(650, 735, 3), "buckle": sample(533, 726, 2), "boot": sample(355, 1580, 5),
    "stock_black": sample(720, 1200, 5), "stock_purple": sample(430, 1260, 5), "bandage": sample(450, 1050, 4),
    "glove": sample(180, 470, 4), "eye": sample(603, 338, 2),
}
# (the hair: the median of the yellow pixels of her side locks (x 430-480 and 640-700, y 420-650), the 25th percentile
# for its shade; a sample that fell on an outline or a highlight is set from the picture's flat colours)
FALLBACK = {"gold": (236, 168, 40), "band_red": (150, 40, 32), "buckle": (175, 175, 180)}
for k, v in FALLBACK.items():
    if k == "gold" and not (PAL[k][0] > 180 and PAL[k][1] > 120 and PAL[k][2] < 110): PAL[k] = v
    if k == "band_red" and not (PAL[k][0] > 100 and PAL[k][1] < 80): PAL[k] = v
    if k == "buckle" and not (min(PAL[k]) > 120): PAL[k] = v
json.dump(PAL, open(os.path.join(OUT, "palette.json"), "w"), indent=1)
print("PALETTE", PAL)
C = PAL
dark = lambda c, k: tuple(int(v * k) for v in c)
mix = lambda a, b, t: tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def zigzag(d, x0, x1, ytop, ybot, period, col, width):
    pts, x, up = [], x0, True
    while x <= x1 + period:
        pts.append((x, ytop if up else ybot)); x += period / 2; up = not up
    d.line(pts, fill=col, width=width, joint="curve")


def save(img, name):
    img.save(os.path.join(OUT, name)); print("TEX", name, img.size)


# ---------------------------------------------------------------- face: the picture's face, levelled and faded into skin
# her eyes in the picture: (525, 357) her right, (605, 335) her left; the build maps the face square (0.22 m) onto the
# 512 texture with the eyes' middle 19 px below its centre and 83 px between them in the picture = 0.064 m on her
EYE_R, EYE_L = np.array([525.0, 357.0]), np.array([605.0, 335.0])
mid = (EYE_R + EYE_L) / 2
ang = math.degrees(math.atan2(EYE_L[1] - EYE_R[1], EYE_L[0] - EYE_R[0]))       # (about -15: her head tilted)
lev = im.rotate(ang, resample=Image.BICUBIC, center=tuple(mid))               # (eyes level)
px_per_m = np.linalg.norm(EYE_L - EYE_R) / 0.064
half = 0.11 * px_per_m                                                          # (the face square's half, picture px)
cx, cy = mid[0], mid[1] - 0.015 * px_per_m                                       # (the square's centre: 15 mm over the eyes' line; up is -y)
crop = lev.crop((int(cx - half), int(cy - half), int(cx + half), int(cy + half))).resize((512, 512), Image.LANCZOS)
skin = Image.new("RGB", (512, 512), C["skin"])
# the mask: the eyes, nose, mouth and cheeks, faded at its rim (the bangs and the hat's shadow in the crop stay out)
m = Image.new("L", (512, 512), 0)
dm = ImageDraw.Draw(m)
e = 256 + int(0.015 * 512 / 0.22)                                                # (the eyes' row in the texture)
dm.ellipse((256 - 150, e - 70, 256 + 150, e + 150), fill=255)
m = m.filter(ImageFilter.GaussianBlur(22))
face = Image.composite(crop, skin, m)
save(face, "face.png")

# ---------------------------------------------------------------- hair: gold with darker strands, lighter crown band
W, H = 512, 1024
g = np.zeros((H, W, 3), np.float32)
base, shade = np.array(C["hair"], np.float32), np.array(C["hair_dark"], np.float32)
rng = np.random.default_rng(7)
streak = np.convolve(rng.random(W), np.ones(5) / 5, mode="same")
for y in range(H):
    t = y / H                                                                     # (0 top: the roots; 1 the tips)
    row = base * (1 - 0.25 * t) + shade * 0.25 * t
    g[y] = row[None, :] * (0.86 + 0.22 * streak[:, None])
hl = (np.arange(H) > 0.08 * H) & (np.arange(H) < 0.14 * H)                       # (a highlight band near the crown)
g[hl] = np.minimum(255, g[hl] * 1.18)
save(Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)), "hair.png")

# ---------------------------------------------------------------- hat cone: u round, v up (base at the bottom, the tip at the top)
W, H = 1024, 512
hat = Image.new("RGB", (W, H), C["hat"]); d = ImageDraw.Draw(hat)
y = lambda v: int(H * (1 - v))
red, gold = C["band_red"], C["gold"]
d.rectangle((0, y(0.17), W, y(0.0)), fill=red)                                   # (the band: red borders, gold middle)
d.rectangle((0, y(0.145), W, y(0.03)), fill=gold)
n = 14
for i in range(n * 2):                                                          # (red triangles in the gold: a zigzag band)
    x0 = i * W / (n * 2)
    if i % 2 == 0: d.polygon([(x0, y(0.03)), (x0 + W / (n * 2), y(0.145)), (x0 + W / n, y(0.03))], fill=red)
zigzag(d, 0, W, y(0.30), y(0.22), W / 12, gold, 7)                               # (gold zigzag and diamonds over the band)
zigzag(d, 0, W, y(0.22), y(0.30), W / 12, gold, 7)
for i in range(12):
    xc = (i + 0.5) * W / 12; d.rectangle((xc - 6, y(0.375) - 6, xc + 6, y(0.375) + 6), fill=gold)
save(hat, "hat_cone.png")

# ---------------------------------------------------------------- hat brim: u round, v out (inner edge at the bottom, the rim at the top)
W, H = 1024, 256
br = Image.new("RGB", (W, H), C["hat"]); d = ImageDraw.Draw(br)
y = lambda v: int(H * (1 - v))
d.rectangle((0, y(1.0), W, y(0.93)), fill=gold)
zigzag(d, 0, W, y(0.84), y(0.70), W / 24, gold, 6)
save(br, "hat_brim.png")

# ---------------------------------------------------------------- cape outside: u across (0 and 1 her front edges), v down (1 the collar, 0 the hem)
W, H = 1024, 1024
co = Image.new("RGB", (W, H), C["cape_out"]); d = ImageDraw.Draw(co)
y = lambda v: int(H * (1 - v))
d.rectangle((0, y(0.02), W, H), fill=gold)                                       # (gold hem, edges)
d.rectangle((0, 0, 12, H), fill=gold); d.rectangle((W - 13, 0, W, H), fill=gold)
d.rectangle((0, y(0.215), W, y(0.20)), fill=gold)                                 # (the border band's lines)
d.rectangle((0, y(0.06), W, y(0.045)), fill=gold)
n = 10
for i in range(n):                                                                # (gold triangles with a square in each)
    x0 = i * W / n
    d.line([(x0 + 8, y(0.07)), (x0 + W / (2 * n), y(0.19)), (x0 + W / n - 8, y(0.07)), (x0 + 8, y(0.07))], fill=gold, width=8)
    xc = x0 + W / (2 * n); d.rectangle((xc - 7, y(0.11) - 7, xc + 7, y(0.11) + 7), fill=gold)
# (soft folds: darker stripes down the cape)
a = np.asarray(co).astype(np.float32)
fold = 0.88 + 0.12 * (0.5 + 0.5 * np.sin(np.linspace(0, 2 * math.pi * 9, W)))
a *= fold[None, :, None]
save(Image.fromarray(a.clip(0, 255).astype(np.uint8)), "cape_out.png")

# ---------------------------------------------------------------- cape lining: gold, pale line triangles near the hem
ci = Image.new("RGB", (W, H), C["cape_in"]); d = ImageDraw.Draw(ci)
pale, deep = mix(C["cape_in"], (255, 240, 180), 0.45), dark(C["cape_in"], 0.8)
d.rectangle((0, y(0.02), W, H), fill=deep)
for vv in (0.06, 0.24):
    d.line([(0, y(vv)), (W, y(vv))], fill=pale, width=4)
n = 12
for i in range(n):
    x0 = i * W / n
    d.line([(x0, y(0.07)), (x0 + W / (2 * n), y(0.23)), (x0 + W / n, y(0.07))], fill=pale, width=4)
    d.line([(x0 + W / (2 * n), y(0.07)), (x0 + W / (2 * n), y(0.12))], fill=pale, width=3)
a = np.asarray(ci).astype(np.float32); a *= fold[None, :, None] * 0.6 + 0.4
save(Image.fromarray(a.clip(0, 255).astype(np.uint8)), "cape_in.png")

# ---------------------------------------------------------------- dress: u round (0.5 her front), v up (0 the hem, 1 the neckline)
W, H = 512, 1024
dr = Image.new("RGB", (W, H), C["dress"]); d = ImageDraw.Draw(dr)
y = lambda v: int(H * (1 - v))
d.rectangle((0, y(0.05), W, H), fill=gold)                                        # (the hem's gold band)
d.rectangle((0, 0, W, y(0.985)), fill=gold)                                       # (the neckline's trim)
xc = W / 2
d.polygon([(xc - 46, 0), (xc + 46, 0), (xc, y(0.89))], fill=gold)               # (the V-neck: gold rim, skin within)
d.polygon([(xc - 36, 0), (xc + 36, 0), (xc, y(0.905))], fill=C["skin"])
for k in range(3):                                                               # (the laces: a white cross under the V)
    yy = y(0.885) + k * 18
    d.line([(xc - 10, yy), (xc + 10, yy + 14)], fill=(235, 232, 225), width=3); d.line([(xc + 10, yy), (xc - 10, yy + 14)], fill=(235, 232, 225), width=3)
a = np.asarray(dr).astype(np.float32)
v = 1 - np.arange(H) / H
folds = 1 - 0.10 * np.clip((0.45 - v) / 0.45, 0, 1)[:, None] * (0.5 + 0.5 * np.sin(np.linspace(0, 2 * math.pi * 7, W)))[None, :]
a *= folds[:, :, None]
save(Image.fromarray(a.clip(0, 255).astype(np.uint8)), "dress.png")

# ---------------------------------------------------------------- sleeve: u round, v along (1 the shoulder, 0 the cuff)
W, H = 256, 512
sl = Image.new("RGB", (W, H), C["dress"]); d = ImageDraw.Draw(sl)
y = lambda v: int(H * (1 - v))
d.rectangle((0, y(0.12), W, H), fill=gold)
d.rectangle((0, y(0.125), W, y(0.115)), fill=dark(gold, 0.75))
save(sl, "sleeve.png")

# ---------------------------------------------------------------- belt: u round (0.5 front), the buckle at her front
W, H = 512, 64
bt = Image.new("RGB", (W, H), C["belt"]); d = ImageDraw.Draw(bt)
d.rectangle((W / 2 - 22, 4, W / 2 + 22, H - 5), outline=C["buckle"], width=7)
d.rectangle((W / 2 - 3, 18, W / 2 + 14, H - 19), fill=C["buckle"])
d.line([(0, 3), (W, 3)], fill=dark(C["belt"], 0.6), width=2); d.line([(0, H - 4), (W, H - 4)], fill=dark(C["belt"], 0.6), width=2)
save(bt, "belt.png")

# ---------------------------------------------------------------- boot shaft: u round (0.5 front), v up (0 the ankle, 1 the cuff's top)
W, H = 512, 512
bo = Image.new("RGB", (W, H), C["boot"]); d = ImageDraw.Draw(bo)
y = lambda v: int(H * (1 - v))
cuff = mix(C["boot"], gold, 0.25)
d.rectangle((0, 0, W, y(0.78)), fill=cuff)
d.rectangle((0, y(0.80), W, y(0.765)), fill=gold); d.rectangle((0, 0, W, 10), fill=gold)
for i in range(8):                                                                 # (the cuff's gold notches)
    xc = (i + 0.5) * W / 8; d.polygon([(xc - 14, y(0.80)), (xc + 14, y(0.80)), (xc, y(0.90))], fill=gold)
xc = W / 2                                                                         # (the lightning stitch up her shin)
pts = [(xc + (12 if k % 2 else -12), y(0.12 + 0.6 * k / 9)) for k in range(10)]
d.line(pts, fill=gold, width=9)
save(bo, "boot.png")

# ---------------------------------------------------------------- stockings: the purple wrap and the bandage (u round, v up)
W, H = 256, 512
pw = Image.new("RGB", (W, H), C["stock_purple"]); d = ImageDraw.Draw(pw)
for k in range(16):
    yy = k * H / 16; d.line([(0, yy), (W, yy + 22)], fill=mix(C["stock_purple"], (140, 120, 170), 0.35), width=3)
save(pw, "stock_purple.png")
bd = Image.new("RGB", (W, H), C["bandage"]); d = ImageDraw.Draw(bd)
for k in range(10):
    yy = k * H / 10; d.line([(0, yy), (W, yy + 30)], fill=dark(C["bandage"], 0.78), width=3)
save(bd, "bandage.png")
print("TEXTURES DONE", OUT)
