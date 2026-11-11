"""884 skyspin's pictures straight up (2026-11-10): the shift of each part of the sky between two pictures, the offset (dx, dy)
that best matches a part of A inside B (least squares over a search window), for a 3 x 2 grid of parts clear of the HUD. A
layer that drifts in a straight line moves every part alike (the spread a pixel or two); one turned about the zenith moves the
left and right parts opposite ways. Needs numpy, scipy and Pillow (CLAUDE.md: the amv-maker venv).
Usage: python sky_shift.py <bs_<tag>_skyspin_up_a.png> <bs_<tag>_skyspin_up_b.png> [search radius px, 90]"""
import sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

R = int(sys.argv[3]) if len(sys.argv) > 3 else 90


def lum(p):
    a = np.asarray(Image.open(p).convert("RGB")).astype(np.float64)
    return gaussian_filter(a.mean(axis=2), 1.5)


A, B = lum(sys.argv[1]), lum(sys.argv[2])
h, w = A.shape
# (the parts: inside the HUD-free middle band; each a 120 x 90 patch)
ys = [int(h * 0.30), int(h * 0.62)]
xs = [int(w * 0.33), int(w * 0.50), int(w * 0.67)]
out = []
for y in ys:
    for x in xs:
        pa = A[y - 45:y + 45, x - 60:x + 60]
        pa = pa - pa.mean()
        if pa.std() < 3: out.append(((x, y), None, "flat")); continue
        best = (1e18, 0, 0)
        for dy in range(-R, R + 1, 2):
            for dx in range(-R, R + 1, 2):
                y0, x0 = y - 45 + dy, x - 60 + dx
                if y0 < 0 or x0 < 0 or y0 + 90 > h or x0 + 120 > w: continue
                pb = B[y0:y0 + 90, x0:x0 + 120]
                e = ((pb - pb.mean() - pa) ** 2).mean()
                if e < best[0]: best = (e, dx, dy)
        # (refine by one pixel)
        e0, bx, by = best
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                y0, x0 = y - 45 + by + dy, x - 60 + bx + dx
                if y0 < 0 or x0 < 0 or y0 + 90 > h or x0 + 120 > w: continue
                pb = B[y0:y0 + 90, x0:x0 + 120]
                e = ((pb - pb.mean() - pa) ** 2).mean()
                if e < best[0]: best = (e, bx + dx, by + dy)
        out.append(((x, y), (best[1], best[2]), round(np.sqrt(best[0]) / pa.std(), 3)))
for o in out: print(o)
v = np.array([o[1] for o in out if o[1] is not None], float)
if len(v):
    print("mean shift", v.mean(axis=0).round(1), "spread", v.std(axis=0).round(1))
