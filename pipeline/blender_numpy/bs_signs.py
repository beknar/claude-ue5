"""Brokenspire's trades' signs (the user's list of 2026-11-04, docs/improvements7.txt: "the signs outside buildings ... often
fall outside of the sign's boundaries. the font should also be an appropriate medieval one for the town of brokenspire and
vell Morath"): each trade's words painted for its hanging board, gold leaf with a dark edge on a clear ground, in Almendra (a
calligraphic medieval face, SIL Open Font License). 890 imports them as T_BS_Sign_<WORDS> and puts them on planes against both
faces of every trade's board.

The list of 2026-11-16 (item 1: "the lettering on some of the signs ... will sometimes fall outside of the sign's boundaries.
example: store house"): the board is a shield that narrows to a point (927 signboard measures its outline into
SourceArt/brokenspire/sign_board.json); fitted to a 58 x 42 cm rectangle low on it, "Store House" stood past its sloping edges.
Every line is now fitted inside the outline, 3 cm in from it, its dark edge and a one-line sign's rule counted; the picture covers
the board's 63 x 47.25 cm about its middle (x 90.4, z -89.5 in the sign's frame), and every painted pixel is checked against the
outline before it is saved (the script stops on one outside). Every word of the town plans' signs is painted (RDTownPlan.cpp's
RDTSignText: 20), so no sign falls back to the engine's text.
Args: out_dir [font.ttf] [sign_board.json]. Needs Pillow and numpy."""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = sys.argv[1] if len(sys.argv) > 1 else "signs"
FONT = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts\Almendra-Bold.ttf")
BOARD = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "brokenspire", "sign_board.json")
W, H = 512, 384
# (the picture's plane in the sign's frame: x along the bracket (the board's width), z down from the bracket; 63 x 47.25 cm about the
# board's middle, the picture's 4:3)
PX0, PX1 = 90.4 - 31.5, 90.4 + 31.5
PZ0, PZ1 = -89.5 + 23.625, -89.5 - 23.625
INSET_CM = 3.0
EDGE_PX = 6                     # (the dark edge's reach: MaxFilter 7 and a blur)
# (the words as the C++ keys them: RDTSignText's letters; the board's lines as painted, each with the splits it may take)
SIGNS = {"SMITHY": [["Smithy"]], "GENERALGOODS": [["General", "Goods"]], "HEALER": [["Healer"]], "TEMPLE": [["Temple"]],
         "STOREHOUSE": [["Store", "House"], ["Storehouse"]], "TAVERN": [["Tavern"]], "CHAPEL": [["Chapel"]], "BARRACKS": [["Barracks"]],
         "HEDGEWITCH": [["Hedge", "Witch"]], "MONASTERY": [["Monastery"], ["Monas-", "tery"]], "WORKSHOP": [["Workshop"], ["Work-", "shop"]],
         "WAREHOUSE": [["Ware", "House"], ["Warehouse"]], "SLUICEHOUSE": [["Sluice", "House"]], "LIBRARY": [["Library"]],
         "LABORATORY": [["Labora-", "tory"], ["Laboratory"]], "STUDY": [["Study"]], "MEDITATION": [["Medita-", "tion"], ["Meditation"]],
         "TOWER": [["Tower"]], "OFFICES": [["Offices"]], "SHOP": [["Shop"]]}

B = json.load(open(BOARD, encoding="utf-8"))
BANDS = sorted((b for b in B["bands"] if b[2] - b[1] > 5.0), key=lambda b: b[0])
ZS = np.array([b[0] for b in BANDS]); X0S = np.array([b[1] for b in BANDS]); X1S = np.array([b[2] for b in BANDS])


def allowed(row):
    """the pixels of a row (0 at the picture's top) inside the board's outline less the inset: (x0, x1), or None"""
    z = PZ0 + (row + 0.5) / H * (PZ1 - PZ0)
    if z < ZS[0] or z > ZS[-1]: return None
    x0 = float(np.interp(z, ZS, X0S)) + INSET_CM; x1 = float(np.interp(z, ZS, X1S)) - INSET_CM
    if x1 <= x0: return None
    return ((x0 - PX0) / (PX1 - PX0) * W, (x1 - PX0) / (PX1 - PX0) * W)


ROWS = [allowed(r) for r in range(H)]


def fits(x0, x1, y0, y1):
    for r in range(max(0, int(y0)), min(H, int(y1) + 1)):
        a = ROWS[r]
        if a is None or x0 < a[0] or x1 > a[1]: return False
    return y0 >= 0 and y1 < H


def layout(lines, size):
    """where the lines go at this size, centred across the board, the highest block that fits searched from the board's widest
    part down (the most room), or None"""
    f = ImageFont.truetype(FONT, size)
    boxes = [f.getbbox(t) for t in lines]
    hs = [b[3] - b[1] for b in boxes]; gap = int(size * 0.12)
    rule = 26 if len(lines) == 1 else 0
    total = sum(hs) + gap * (len(lines) - 1) + rule
    cx = W / 2; found = []
    for top in range(EDGE_PX, H - int(total) - EDGE_PX, 2):
        y = top; ok = True; spots = []
        for t, b, h in zip(lines, boxes, hs):
            w = b[2] - b[0]
            if not fits(cx - w / 2 - EDGE_PX, cx + w / 2 + EDGE_PX, y - EDGE_PX, y + h + EDGE_PX): ok = False; break
            spots.append((cx - w / 2 - b[0], y - b[1])); y += h + gap
        if ok and rule:
            ry = int(y - gap + gap * 0.6 + 8); rw = int(W * 0.30)
            ok = fits(cx - rw - EDGE_PX, cx + rw + EDGE_PX, ry - 9 - EDGE_PX, ry + 9 + EDGE_PX)
        if ok: found.append((f, spots, (top + total / 2), (int(y - gap + gap * 0.6 + 8) if rule else None)))
    # (the middle of the places it fits: centred in the room the board gives it, not pressed to its top)
    return found[len(found) // 2] if found else None


def fit(options):
    """the largest size any of a word's splits fits the board at"""
    for size in range(200, 20, -2):
        for lines in options:
            if layout(lines, size):
                # (85 % of the largest: room round it, so it can sit in the middle of the board's room)
                s2 = int(size * 0.85)
                return lines, s2, layout(lines, s2)
    raise RuntimeError("no size fits")


def paint(key, options):
    lines, size, (f, spots, _, ry) = fit(options)
    mask = Image.new("L", (W, H), 0); d = ImageDraw.Draw(mask)
    for t, (x, y) in zip(lines, spots): d.text((x, y), t, font=f, fill=255)
    if ry is not None:
        rw = int(W * 0.30)
        d.line([(W / 2 - rw, ry), (W / 2 + rw, ry)], fill=255, width=4)
        d.polygon([(W / 2, ry - 9), (W / 2 + 9, ry), (W / 2, ry + 9), (W / 2 - 9, ry)], fill=255)
    m = np.asarray(mask).astype(np.float32) / 255.0
    edge = np.asarray(mask.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255.0
    yy = np.linspace(0, 1, H)[:, None]
    rng = np.random.default_rng(abs(hash(key)) % (2 ** 32))
    wear = np.clip(1.0 - 0.35 * (rng.random((H // 4 + 1, W // 4 + 1)) ** 6), 0.6, 1.0)
    wear = np.kron(wear, np.ones((4, 4)))[:H, :W]
    gold = np.stack([0.95 - 0.15 * yy + 0 * m, 0.74 - 0.18 * yy + 0 * m, 0.30 - 0.12 * yy + 0 * m], axis=-1)
    dark = np.array([0.16, 0.09, 0.04])
    col = dark[None, None, :] * (1 - m[..., None]) + gold * m[..., None]
    a = np.clip(np.maximum(m * wear, edge * 0.92), 0, 1)
    # (measured, not assumed: every pixel drawn at all (alpha over the material's 0.35 clip) inside the board's outline, not its inset)
    outside = 0
    for r in range(H):
        cols = np.nonzero(a[r] > 0.35)[0]
        if not len(cols): continue
        z = PZ0 + (r + 0.5) / H * (PZ1 - PZ0)
        if z < ZS[0] or z > ZS[-1]: outside += len(cols); continue
        bx0 = (float(np.interp(z, ZS, X0S)) - PX0) / (PX1 - PX0) * W; bx1 = (float(np.interp(z, ZS, X1S)) - PX0) / (PX1 - PX0) * W
        outside += int(((cols < bx0) | (cols > bx1)).sum())
    assert outside == 0, f"bs_signs: {key}: {outside} pixels outside the board"
    img = np.dstack([np.clip(col, 0, 1), a])
    Image.fromarray((img * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, f"sign_{key}.png"))
    return lines, size


os.makedirs(OUT, exist_ok=True)
rep = {}
for k, v in SIGNS.items():
    lines, size = paint(k, v); rep[k] = {"lines": lines, "size": size}
json.dump({"plane_cm": [round(PX1 - PX0, 2), round(PZ0 - PZ1, 3)], "middle": [90.4, -89.5], "inset_cm": INSET_CM, "signs": rep},
          open(os.path.join(OUT, "signs.json"), "w", encoding="utf-8"), indent=1)
print("bs_signs:", len(SIGNS), "signs in", OUT, "with", os.path.basename(FONT), "; sizes", {k: r["size"] for k, r in rep.items()})
