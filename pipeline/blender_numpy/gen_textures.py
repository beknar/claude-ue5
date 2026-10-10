"""Generate tileable studio textures with numpy (FFT-filtered noise):
  concrete: T_Concrete_BC (sRGB), T_Concrete_R (linear), T_Concrete_N (normal), T_Concrete_H (height)
  specular-profile LUTs: T_SP_Leather, T_SP_Patent (view x light, sRGB)
Usage: gen_textures.py out_dir [size]"""
import sys, os, numpy as np
from PIL import Image
out = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 2048
os.makedirs(out, exist_ok=True)
rng = np.random.default_rng(3)

def fnoise(beta, lo=1.0, hi=None, seed=0):
    r = np.random.default_rng(seed)
    w = r.normal(size=(N, N))
    F = np.fft.fft2(w)
    fy = np.fft.fftfreq(N)[:, None] * N; fx = np.fft.fftfreq(N)[None, :] * N
    f = np.sqrt(fx * fx + fy * fy); f[0, 0] = 1
    amp = 1 / f ** beta
    amp[f < lo] = 0
    if hi: amp[f > hi] = 0
    n = np.real(np.fft.ifft2(F * amp))
    return (n - n.mean()) / (n.std() + 1e-9)

# --- concrete -------------------------------------------------------------
base = 0.6 * fnoise(1.6, 1, seed=1) + 0.35 * fnoise(1.1, 8, seed=2) + 0.15 * fnoise(0.6, 64, seed=3)
# aggregate pits: sparse dark blobs
pits = fnoise(0.9, 40, 200, seed=4)
pits = np.clip((pits - 2.2) * 2.5, 0, 1)
trowel = 0.25 * fnoise(2.0, 2, 30, seed=5)
height = 0.5 + 0.18 * base + 0.08 * trowel - 0.35 * pits
height = (height - height.min()) / (height.max() - height.min())
tone = 0.46 + 0.05 * base + 0.03 * fnoise(1.3, 4, seed=6) - 0.12 * pits
alb = np.stack([tone * 1.0, tone * 0.985, tone * 0.96], -1)           # slightly warm grey
rough = np.clip(0.55 + 0.12 * fnoise(1.4, 3, seed=7) + 0.25 * pits - 0.05 * trowel, 0.2, 0.95)
gy, gx = np.gradient(height * 6.0)
nrm = np.stack([-gx, -gy, np.ones_like(gx)], -1); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
def save(a, name, srgb=False):
    a = np.clip(a, 0, 1)
    if srgb: a = np.where(a <= 0.0031308, a * 12.92, 1.055 * a ** (1 / 2.4) - 0.055)
    Image.fromarray((a * 255 + 0.5).astype(np.uint8)).save(os.path.join(out, name + ".png"))
    print("saved", name)
save(alb, "T_Concrete_BC", srgb=True)
save(rough, "T_Concrete_R")
save(nrm * 0.5 + 0.5, "T_Concrete_N")
Image.fromarray((height * 65535).astype(np.uint16)).save(os.path.join(out, "T_Concrete_H.png")); print("saved T_Concrete_H")

# --- specular profile LUTs (u = NoV view axis, v = NoL light axis) -----------
L = 64
u = np.linspace(0, 1, L)[None, :, None]; v = np.linspace(0, 1, L)[:, None, None]
def lut(graze, face, gamma, name):
    graze = np.array(graze)[None, None, :]; face = np.array(face)[None, None, :]
    view = graze + (face - graze) * (u ** gamma)
    light = 0.92 + 0.08 * v
    save(view * light * np.ones((L, L, 3)), name, srgb=True)
lut((1.00, 0.80, 0.74), (1.0, 0.97, 0.95), 0.6, "T_SP_Leather")     # warm red bloom at grazing (dyed leather)
lut((0.82, 0.88, 1.00), (1.0, 1.0, 1.0), 0.5, "T_SP_Patent")       # cool lacquer edge
