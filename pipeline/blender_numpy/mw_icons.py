"""mistward_castle's item pictures: <icon>_rgb.png + <icon>_mask.png (867 shoot) -> <icon>.png, 256 x 256 with alpha.

    python mw_icons.py <dir> [--sheet <contact.jpg>]

The mask (the thing in plain white, base colour, on black) is the alpha; the lit picture was taken over black, so its
colour is divided by the alpha at the edges (no dark fringe). Cut to the thing with 6 % room, centred, 256 x 256.
--sheet: every picture on a grey and a dark ground, to look at."""
import os, sys
import numpy as np
from PIL import Image

D = os.path.abspath(sys.argv[1])
SHEET = sys.argv[sys.argv.index("--sheet") + 1] if "--sheet" in sys.argv else None
SIZE = 256
done = []
for f in sorted(os.listdir(D)):
    if not f.endswith("_rgb.png"): continue
    n = f[:-8]
    rgb = np.asarray(Image.open(os.path.join(D, f)).convert("RGB")).astype(np.float32) / 255.0
    m = np.asarray(Image.open(os.path.join(D, n + "_mask.png")).convert("L")).astype(np.float32) / 255.0
    # (base colour is in sRGB; white is 1, the ground 0: anything above a trace is the thing)
    a = np.clip((m - 0.02) / 0.6, 0.0, 1.0)
    ys, xs = np.nonzero(a > 0.05)
    if len(xs) == 0:
        print("MWICONS empty", n); continue
    col = np.clip(rgb / np.maximum(a[..., None], 0.25), 0.0, 1.0)
    out = np.dstack([col, a])
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    side = int(max(x1 - x0, y1 - y0) * 1.06) + 2
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    canvas = np.zeros((side, side, 4), np.float32)
    sx0, sy0 = cx - side // 2, cy - side // 2
    H, W = a.shape
    ax0, ay0 = max(sx0, 0), max(sy0, 0); ax1, ay1 = min(sx0 + side, W), min(sy0 + side, H)
    canvas[ay0 - sy0:ay1 - sy0, ax0 - sx0:ax1 - sx0] = out[ay0:ay1, ax0:ax1]
    im = Image.fromarray((canvas * 255).round().astype(np.uint8), "RGBA").resize((SIZE, SIZE), Image.LANCZOS)
    im.save(os.path.join(D, n + ".png"))
    done.append((n, im))
print("MWICONS", len(done), "pictures in", D)
if SHEET:
    cols = 8; rows = (len(done) + cols - 1) // cols
    sh = Image.new("RGB", (cols * 136, rows * 272), (0, 0, 0))
    for i, (n, im) in enumerate(done):
        t = im.resize((128, 128), Image.LANCZOS)
        for k, g in enumerate(((150, 150, 150), (28, 24, 22))):
            bg = Image.new("RGBA", (128, 128), g + (255,)); bg.alpha_composite(t)
            sh.paste(bg.convert("RGB"), ((i % cols) * 136 + 4, (i // cols) * 272 + 4 + k * 132))
    sh.save(SHEET, quality=90)
