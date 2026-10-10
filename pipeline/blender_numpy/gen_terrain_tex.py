"""Tileable ground texture sets (numpy, FFT-filtered noise) + terrain heightfield.
  grass / dirt / rock: T_<X>_BC (sRGB), T_<X>_R (linear), T_<X>_N (normal), T_<X>_H (16-bit height)
  terrain_h.npy: (G, G) heights in metres over a 400 m square centred on the origin.
Usage: gen_terrain_tex.py out_dir [size]"""
import sys, os, numpy as np
from PIL import Image
out = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 2048
os.makedirs(out, exist_ok=True)

def fnoise(beta, lo=1.0, hi=None, seed=0, n=N, aniso=None):
    r = np.random.default_rng(seed)
    F = np.fft.fft2(r.normal(size=(n, n)))
    fy = np.fft.fftfreq(n)[:, None] * n; fx = np.fft.fftfreq(n)[None, :] * n
    if aniso:  # stretch: (angle, ratio) -> elongated features
        a, k = aniso; c, s = np.cos(a), np.sin(a)
        fx, fy = (c * fx + s * fy), (-s * fx + c * fy) * k
    f = np.sqrt(fx * fx + fy * fy); f[0, 0] = 1
    amp = 1 / f ** beta
    amp[f < lo] = 0
    if hi: amp[f > hi] = 0
    v = np.real(np.fft.ifft2(F * amp))
    return (v - v.mean()) / (v.std() + 1e-9)

def norm01(a): return (a - a.min()) / (a.max() - a.min() + 1e-9)
def save(a, name, srgb=False):
    a = np.clip(a, 0, 1)
    if srgb: a = np.where(a <= 0.0031308, a * 12.92, 1.055 * a ** (1 / 2.4) - 0.055)
    Image.fromarray((a * 255 + 0.5).astype(np.uint8)).save(os.path.join(out, name + ".png")); print("saved", name)
def save_set(prefix, alb, rough, height, nstrength):
    gy, gx = np.gradient(height * nstrength)
    nrm = np.stack([-gx, gy, np.ones_like(gx)], -1); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    save(alb, f"T_{prefix}_BC", srgb=True); save(rough, f"T_{prefix}_R"); save(nrm * 0.5 + 0.5, f"T_{prefix}_N")
    Image.fromarray((norm01(height) * 65535).astype(np.uint16)).save(os.path.join(out, f"T_{prefix}_H.png")); print("saved", prefix, "H")

def mix(a, b, t): return a + (b - a) * t[..., None]

# --- grass ground (1.5 m tile): clumpy turf, thatch streaks, dry patches -------------
clump = fnoise(1.2, 6, 60, seed=11)
streak = sum(fnoise(0.5, 40, 400, seed=20 + i, aniso=(i * 1.1, 6.0)) for i in range(4)) / 2
fine = fnoise(0.3, 200, seed=12)
dry = np.clip(fnoise(1.5, 1, 8, seed=13) * 0.6 + 0.1, 0, 1)
h = 0.55 * clump + 0.35 * streak + 0.15 * fine
lush = np.array([0.055, 0.095, 0.022]); yel = np.array([0.15, 0.16, 0.05]); straw = np.array([0.24, 0.20, 0.11])
alb = mix(np.broadcast_to(lush, (N, N, 3)), np.broadcast_to(yel, (N, N, 3)), np.clip(0.5 + 0.25 * streak, 0, 1))
alb = mix(alb, np.broadcast_to(straw, (N, N, 3)), np.clip(dry * 0.6 + 0.2 * fine, 0, 1) * 0.6)
alb *= (0.75 + 0.25 * norm01(h))[..., None]
save_set("Grass", alb, np.clip(0.78 + 0.08 * fine - 0.05 * clump, 0.5, 0.95), h, 10.0)

# --- dirt (2 m tile): compacted soil + pebbles --------------------------------------
soil = 0.6 * fnoise(1.5, 2, seed=31) + 0.3 * fnoise(0.9, 30, seed=32)
peb_n = fnoise(0.4, 60, 220, seed=33)
pebbles = np.clip((peb_n - 1.7) * 1.6, 0, 1) ** 0.5
small = np.clip((fnoise(0.2, 200, 700, seed=34) - 2.0) * 2, 0, 1)
h = 0.35 * soil + 1.4 * pebbles + 0.4 * small + 0.1 * fnoise(0.2, 300, seed=35)
brown = np.array([0.15, 0.10, 0.065]); dark = np.array([0.07, 0.05, 0.035]); stone = np.array([0.22, 0.20, 0.18])
alb = mix(np.broadcast_to(brown, (N, N, 3)), np.broadcast_to(dark, (N, N, 3)), np.clip(0.5 - 0.3 * soil, 0, 1))
alb = mix(alb, np.broadcast_to(stone, (N, N, 3)) * (0.8 + 0.4 * norm01(fnoise(0.8, 80, seed=36)))[..., None], np.maximum(pebbles, small * 0.7))
save_set("Dirt", alb, np.clip(0.88 - 0.25 * pebbles + 0.05 * soil, 0.4, 0.97), h, 14.0)

# --- rock (4 m tile): layered sedimentary strata, cracks, lichen --------------------
yy = np.arange(N)[:, None] / N
warp = fnoise(1.6, 1, seed=41)
strata = np.sin((yy * 9 + 0.08 * warp) * 2 * np.pi) * 0.5 + 0.5
strata = np.broadcast_to(strata, (N, N))
crack = np.abs(fnoise(1.1, 4, 120, seed=42)); crack = np.clip(1 - crack * 6, 0, 1) ** 3
grain = fnoise(0.5, 60, seed=43)
h = 0.6 * strata + 0.5 * fnoise(1.4, 2, seed=44) + 0.12 * grain - 0.7 * crack
grey = np.array([0.16, 0.155, 0.145]); warm = np.array([0.20, 0.17, 0.135]); lichen = np.array([0.12, 0.13, 0.06])
alb = mix(np.broadcast_to(grey, (N, N, 3)), np.broadcast_to(warm, (N, N, 3)), np.clip(strata * 0.7, 0, 1))
alb = alb * (0.8 + 0.25 * norm01(grain))[..., None] * (1 - 0.6 * crack)[..., None]
alb = mix(alb, np.broadcast_to(lichen, (N, N, 3)), np.clip((fnoise(1.2, 6, seed=45) - 1.0) * 0.8, 0, 0.7))
save_set("Rock", alb, np.clip(0.72 + 0.1 * grain + 0.15 * crack, 0.4, 0.98), h, 12.0)

# --- terrain heightfield: 400 m, valley meadow around origin, ridged hills beyond ~40 m ---
G = 801; S = 400.0
xs = np.linspace(-S / 2, S / 2, G); X, Y = np.meshgrid(xs, xs)
r = np.sqrt(X ** 2 + Y ** 2)
def sm(e0, e1, x): t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def gn(beta, lo, hi, seed): return fnoise(beta, lo, hi, seed=seed, n=G)
roll = 0.9 * gn(2.6, 1, 40, 51) + 0.04 * gn(1.5, 20, 200, 52)            # gentle meadow undulation (m)
ridge = 1 - np.abs(gn(2.4, 1, 10, 53)); ridge = ridge ** 2
hills = 14 * gn(2.8, 1, 6, 54) + 10 * ridge + 1.5 * gn(2.0, 6, 40, 55)
hills = hills - hills.min() + 1
H = roll + sm(40, 150, r) * hills
H += 30 * sm(120, 200, r) * norm01(gn(2.0, 1, 8, 56))                    # distant mountains
H -= H[G // 2, G // 2]                                                    # origin at z = 0
np.save(os.path.join(out, "terrain_h.npy"), H.astype(np.float32))
print("terrain range", float(H.min()), float(H.max()), "centre 5 m patch", float(np.ptp(H[G//2-10:G//2+10, G//2-10:G//2+10])))
