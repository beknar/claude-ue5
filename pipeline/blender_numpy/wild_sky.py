"""The night sky's moon (the user's list of 2026-11-04, docs/improvements7.txt: "the moon if it's night time"): a full moon's
disc drawn from noise (darker seas, craters with bright rims, its edge darkened), on a clear ground, 512 x 512. 890 imports it
as T_RD_Moon for the moon's disc (the engine's DaySequence moon texture is in a plugin this project does not enable).
Args: out_dir. Needs numpy and Pillow."""
import os, sys
import numpy as np
from PIL import Image

OUT = sys.argv[1] if len(sys.argv) > 1 else "sky"
N = 512
rng = np.random.default_rng(20261104)


def noise(n, octaves, seed):
    r = np.random.default_rng(seed); acc = np.zeros((n, n)); amp = 1.0; tot = 0.0
    for o in range(octaves):
        k = 4 * 2 ** o
        g = r.random((k + 1, k + 1))
        # (bilinear up to n)
        x = np.linspace(0, k, n, endpoint=False); xi = x.astype(int); xf = x - xi; xf = xf * xf * (3 - 2 * xf)
        a = g[np.ix_(xi, xi)]; b = g[np.ix_(xi + 1, xi)]; c = g[np.ix_(xi, xi + 1)]; d = g[np.ix_(xi + 1, xi + 1)]
        v = (a * (1 - xf[:, None]) + b * xf[:, None]) * (1 - xf[None, :]) + (c * (1 - xf[:, None]) + d * xf[:, None]) * xf[None, :]
        acc += v * amp; tot += amp; amp *= 0.5
    return acc / tot


y, x = np.mgrid[0:N, 0:N]
cx = cy = (N - 1) / 2; R = N * 0.47
dx = (x - cx) / R; dy = (y - cy) / R; rr = np.sqrt(dx * dx + dy * dy)
# the seas (maria): broad dark patches
seas = np.clip((noise(N, 4, 7) - 0.48) * 4.0, 0, 1)
alb = 0.92 - 0.34 * seas + 0.10 * (noise(N, 6, 11) - 0.5)
# craters: rings brighter at the rim, a darker floor
for _ in range(70):
    px, py = rng.uniform(-0.85, 0.85, 2); s = rng.uniform(0.015, 0.09)
    d = np.sqrt((dx - px) ** 2 + (dy - py) ** 2) / s
    alb += 0.10 * np.exp(-((d - 1.0) ** 2) / 0.02) - 0.07 * np.clip(1 - d, 0, 1)
# limb darkening and the edge
limb = np.clip(1 - rr * rr, 0, 1) ** 0.25
lum = np.clip(alb * (0.55 + 0.45 * limb), 0, 1)
alpha = np.clip((1.0 - rr) * R / 1.5, 0, 1)
rgb = np.stack([lum * 0.98, lum * 0.97, lum * 0.93], axis=-1)
os.makedirs(OUT, exist_ok=True)
Image.fromarray((np.dstack([rgb, alpha]) * 255).astype(np.uint8)).save(os.path.join(OUT, "moon.png"))
print("wild_sky: moon.png in", OUT)
