"""884's horizon pictures (2026-11-10, the far land under the haze): in each column clear of the HUD, where the sky ends (the
first row from the top whose colour jumps from the row two above by more than a threshold), the sky just above it and the land
just below it; their medians over the columns and the jump between them. A white strip is land brighter than the sky over it.
Needs numpy and Pillow (CLAUDE.md: the amv-maker venv).
Usage: python sky_horizon.py <picture.png> [...]   (prints one line a picture; --json writes them as a list)"""
import sys, json
import numpy as np
from PIL import Image


def luma(c):
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def measure(path, x0=0.27, x1=0.75, y0=0.18, y1=0.70, jump=14.0):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float64)
    h, w, _ = a.shape
    tops, sky, land = [], [], []
    for x in range(int(w * x0), int(w * x1), 4):
        col = a[:, x - 1:x + 2].mean(axis=1)
        for y in range(int(h * y0) + 2, int(h * y1)):
            if np.abs(col[y] - col[y - 2]).max() > jump:
                if y - 10 < 0 or y + 14 >= h: break
                tops.append(y); sky.append(col[y - 9:y - 3].mean(axis=0)); land.append(col[y + 3:y + 13].mean(axis=0))
                break
    if not tops: return {"picture": path.split("\\")[-1], "found": 0}
    s, l = np.median(np.array(sky), axis=0), np.median(np.array(land), axis=0)
    return {"picture": path.split("\\")[-1].split("/")[-1], "found": len(tops), "top_row": int(np.median(tops)),
            "sky": [int(round(v)) for v in s], "land": [int(round(v)) for v in l],
            "jump": round(float(np.linalg.norm(l - s)), 1), "land_minus_sky_luma": round(float(luma(l) - luma(s)), 1)}


if __name__ == "__main__":
    out = [measure(p) for p in sys.argv[1:] if p != "--json"]
    if "--json" in sys.argv: print(json.dumps(out))
    else:
        for o in out: print(o)
