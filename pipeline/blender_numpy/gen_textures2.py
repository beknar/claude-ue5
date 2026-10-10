"""Tileable leather-grain normal/roughness and a lace mask (numpy). Usage: gen_textures2.py out_dir"""
import sys, os, numpy as np
from PIL import Image
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
N = 1024; rng = np.random.default_rng(5)

def fnoise(beta, lo, hi, seed):
    r = np.random.default_rng(seed); F = np.fft.fft2(r.normal(size=(N, N)))
    fy = np.fft.fftfreq(N)[:, None] * N; fx = np.fft.fftfreq(N)[None, :] * N
    f = np.sqrt(fx * fx + fy * fy); f[0, 0] = 1
    a = 1 / f ** beta; a[(f < lo) | (f > hi)] = 0
    n = np.real(np.fft.ifft2(F * a)); return (n - n.mean()) / n.std()

# pebbled leather: tileable Worley-like cells via many jittered points on a torus
pts = rng.uniform(0, N, (2600, 2))
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
d1 = np.full((N, N), 1e9, np.float32); d2 = np.full((N, N), 1e9, np.float32)
for (px, py) in pts:
    dx = np.abs(xx - px); dx = np.minimum(dx, N - dx)
    dy = np.abs(yy - py); dy = np.minimum(dy, N - dy)
    d = dx * dx + dy * dy
    m = d < d1; d2 = np.where(m, d1, np.minimum(d2, d)); d1 = np.where(m, d, d1)
cell = np.sqrt(d2) - np.sqrt(d1)                      # ridge between pebbles
h = np.tanh(cell / 6.0) + 0.15 * fnoise(1.0, 20, 300, 1)
h = (h - h.min()) / (h.max() - h.min())
gy, gx = np.gradient(h * 3.0)
n = np.stack([-gx, -gy, np.ones_like(gx)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8)).save(os.path.join(out, "T_LeatherGrain_N.png"))
r = np.clip(0.42 + 0.10 * (1 - h) + 0.04 * fnoise(1.2, 4, 80, 2), 0, 1)
Image.fromarray((r * 255).astype(np.uint8)).save(os.path.join(out, "T_LeatherGrain_R.png"))

# lace: floral rosettes on a net, tileable (u around the leg, v down the band)
L = 1024
y, x = np.mgrid[0:L, 0:L] / L
net = (np.abs(np.sin(np.pi * 48 * (x + y))) < 0.16) | (np.abs(np.sin(np.pi * 48 * (x - y))) < 0.16)
ros = np.zeros((L, L), bool)
for cx, cy in [(0.25, 0.3), (0.75, 0.3), (0.5, 0.65), (0.0, 0.65), (1.0, 0.65), (0.25, 1.0), (0.75, 1.0), (0.25, 0.0), (0.75, 0.0)]:
    dx = x - cx; dy = y - cy; rr = np.sqrt(dx * dx + dy * dy); th = np.arctan2(dy, dx)
    petal = rr < 0.11 + 0.035 * np.cos(6 * th)
    hole = rr < 0.035
    ring = np.abs(rr - (0.07 + 0.02 * np.cos(6 * th))) < 0.008
    ros |= (petal & ~hole & ~ring)
scallop = y > 0.9 + 0.06 * np.abs(np.sin(np.pi * 8 * x))   # scalloped edge at the band top (v=1)
mask = (net | ros) & ~scallop
Image.fromarray((mask * 255).astype(np.uint8)).save(os.path.join(out, "T_Lace_Mask.png"))
print("textures written")
