"""Brokenspire's trades' signs (the user's list of 2026-11-04, docs/improvements7.txt: "the signs outside buildings ... often
fall outside of the sign's boundaries. the font should also be an appropriate medieval one for the town of brokenspire and
vell Morath"): each trade's words painted for its hanging board, gold leaf with a dark edge on a clear ground, fitted to the
board's face (58 x 42 cm of its 64 x 50: 512 x 384 pixels), in Almendra (a calligraphic medieval face, SIL Open Font
License). 890 imports them as T_BS_Sign_<WORDS> and puts them on planes against both faces of every trade's board.
Args: out_dir [font.ttf] (default: Almendra Bold as installed for the user). Needs Pillow and numpy."""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = sys.argv[1] if len(sys.argv) > 1 else "signs"
FONT = sys.argv[2] if len(sys.argv) > 2 else os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts\Almendra-Bold.ttf")
W, H = 512, 384
# (the words as the C++ keys them: RDTSignText's letters; the board's lines as painted)
SIGNS = {"SMITHY": ["Smithy"], "GENERALGOODS": ["General", "Goods"], "HEALER": ["Healer"], "TEMPLE": ["Temple"], "STOREHOUSE": ["Store", "House"],
         "TAVERN": ["Tavern"], "CHAPEL": ["Chapel"], "BARRACKS": ["Barracks"], "HEDGEWITCH": ["Hedge", "Witch"]}


def fit(lines, max_w, max_h):
    """the largest size at which every line fits the width and all of them the height"""
    for size in range(220, 20, -2):
        f = ImageFont.truetype(FONT, size)
        boxes = [f.getbbox(t) for t in lines]
        ws = [b[2] - b[0] for b in boxes]; hs = [b[3] - b[1] for b in boxes]
        gap = int(size * 0.12)
        if max(ws) <= max_w and sum(hs) + gap * (len(lines) - 1) <= max_h: return f, boxes, gap
    raise RuntimeError("no size fits")


def paint(key, lines):
    f, boxes, gap = fit(lines, W * 0.86, H * 0.74)
    hs = [b[3] - b[1] for b in boxes]
    total = sum(hs) + gap * (len(lines) - 1)
    mask = Image.new("L", (W, H), 0); d = ImageDraw.Draw(mask)
    y = (H - total) / 2
    for t, b, h in zip(lines, boxes, hs):
        x = (W - (b[2] - b[0])) / 2 - b[0]
        d.text((x, y - b[1]), t, font=f, fill=255)
        y += h + gap
    # (a fine rule under a one-line sign, with a lozenge in its middle)
    if len(lines) == 1:
        ry = int(y + gap * 0.6); rw = int(W * 0.30)
        d.line([(W / 2 - rw, ry), (W / 2 + rw, ry)], fill=255, width=4)
        d.polygon([(W / 2, ry - 9), (W / 2 + 9, ry), (W / 2, ry + 9), (W / 2 - 9, ry)], fill=255)
    m = np.asarray(mask).astype(np.float32) / 255.0
    edge = np.asarray(mask.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255.0
    # (gold leaf: brighter toward the letters' tops, worn a little by a noise; a dark brown edge round them)
    yy = np.linspace(0, 1, H)[:, None]
    rng = np.random.default_rng(abs(hash(key)) % (2 ** 32))
    wear = np.clip(1.0 - 0.35 * (rng.random((H // 4 + 1, W // 4 + 1)) ** 6), 0.6, 1.0)
    wear = np.kron(wear, np.ones((4, 4)))[:H, :W]
    gold = np.stack([0.95 - 0.15 * yy + 0 * m, 0.74 - 0.18 * yy + 0 * m, 0.30 - 0.12 * yy + 0 * m], axis=-1)
    dark = np.array([0.16, 0.09, 0.04])
    col = dark[None, None, :] * (1 - m[..., None]) + gold * m[..., None]
    a = np.clip(np.maximum(m * wear, edge * 0.92), 0, 1)
    img = np.dstack([np.clip(col, 0, 1), a])
    Image.fromarray((img * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, f"sign_{key}.png"))


os.makedirs(OUT, exist_ok=True)
for k, v in SIGNS.items(): paint(k, v)
print("bs_signs:", len(SIGNS), "signs in", OUT, "with", os.path.basename(FONT))
