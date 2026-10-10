"""Scatter grass clumps and rocks on the terrain heightfield (UE coords, cm).
Blender +Y maps to UE -Y on glb import, so UE (x, y) samples the field at Blender (x, -y).
Trail centre line: Y = 400 sin(X / 2500) (cm), kept clear.
Usage: gen_placements.py terrain_dir out.json [flipY=1]"""
import sys, json, numpy as np
d, outp = sys.argv[1], sys.argv[2]; FLIP = int(sys.argv[3]) if len(sys.argv) > 3 else 1
H = np.load(f"{d}/terrain_h.npy"); G = H.shape[0]; S = 400.0; step = S / (G - 1)
rng = np.random.default_rng(9)

def height(xc, yc):
    """UE cm -> terrain height cm (bilinear)"""
    x = xc / 100.0; y = (-yc if FLIP else yc) / 100.0
    fx = (x + S / 2) / step; fy = (y + S / 2) / step
    i0 = np.clip(np.floor(fy).astype(int), 0, G - 2); j0 = np.clip(np.floor(fx).astype(int), 0, G - 2)
    ty = fy - i0; tx = fx - j0
    h = (H[i0, j0] * (1 - tx) * (1 - ty) + H[i0, j0 + 1] * tx * (1 - ty) + H[i0 + 1, j0] * (1 - tx) * ty + H[i0 + 1, j0 + 1] * tx * ty)
    return h * 100.0
def slope_ok(xc, yc, maxdeg):
    e = 50.0
    gx = (height(xc + e, yc) - height(xc - e, yc)) / (2 * e); gy = (height(xc, yc + e) - height(xc, yc - e)) / (2 * e)
    return np.degrees(np.arctan(np.sqrt(gx * gx + gy * gy))) < maxdeg
def trail_dist(xc, yc): return np.abs(yc - 400 * np.sin(xc / 2500))

# smooth patchiness field for grass density (value noise on a coarse lattice)
lat = rng.random((64, 64))
def patch(xc, yc):
    u = (xc / 1800.0) % 63; v = (yc / 1800.0) % 63
    i, j = np.floor(v).astype(int), np.floor(u).astype(int); a, b = v - i, u - j
    a = a * a * (3 - 2 * a); b = b * b * (3 - 2 * b)
    return lat[i, j] * (1 - a) * (1 - b) + lat[i, j + 1] * (1 - a) * b + lat[i + 1, j] * a * (1 - b) + lat[i + 1, j + 1] * a * b

def scatter(n, xr, yr, keep):
    x = rng.uniform(*xr, n); y = rng.uniform(*yr, n)
    k = keep(x, y); return x[k], y[k]

grass = []
# near field: dense around the trail section used for the video / play start
x, y = scatter(70000, (-3000, 7000), (-3000, 3000),
               lambda x, y: (trail_dist(x, y) > 110 + rng.uniform(0, 70, x.size)) & (rng.random(x.size) < 0.35 + 0.65 * patch(x, y)))
x, y = x[slope_ok(x, y, 28)], y[slope_ok(x, y, 28)]
grass.append((x, y, rng.uniform(0.75, 1.45, x.size)))
# mid field: sparser out to ~110 m
x, y = scatter(60000, (-11000, 11000), (-11000, 11000),
               lambda x, y: ((np.abs(x - 2000) > 5000) | (np.abs(y) > 3000)) & (np.hypot(x, y) < 11000)
               & (trail_dist(x, y) > 150) & (rng.random(x.size) < patch(x, y) ** 2))
x, y = x[slope_ok(x, y, 26)], y[slope_ok(x, y, 26)]
grass.append((x, y, rng.uniform(0.9, 1.6, x.size)))
gx = np.concatenate([g[0] for g in grass]); gy = np.concatenate([g[1] for g in grass]); gs = np.concatenate([g[2] for g in grass])
gz = height(gx, gy) - 2.0
gyaw = rng.uniform(0, 360, gx.size)

rocks = []
def add_rocks(n, rmin, rmax, smin, smax, near_trail_ok=False):
    c = 0
    while c < n:
        a = rng.uniform(0, 2 * np.pi); r = rng.uniform(rmin, rmax)
        x, y = r * np.cos(a), r * np.sin(a)
        if trail_dist(x, y) < (300 if not near_trail_ok else 230): continue
        s = rng.uniform(smin, smax)
        rocks.append(dict(mesh="ABC"[rng.integers(3)], x=float(x), y=float(y), z=float(height(x, y) - 25 * s),
                          yaw=float(rng.uniform(0, 360)), pitch=float(rng.uniform(-8, 8)), roll=float(rng.uniform(-8, 8)), s=float(s)))
        c += 1
add_rocks(14, 600, 3000, 0.12, 0.45, True)      # small stones near the trail
add_rocks(30, 3000, 9000, 0.4, 1.6)
add_rocks(45, 9000, 19000, 1.0, 4.5)
json.dump(dict(grass=[[float(a), float(b), float(c), float(e), float(f)] for a, b, c, e, f in zip(gx, gy, gz, gyaw, gs)],
               rocks=rocks, start_z=float(height(np.array([0.0]), np.array([0.0]))[0]),
               probe=[[float(px), float(py), float(height(np.array([px]), np.array([py]))[0])] for px, py in ((5000, 4000), (-6000, 7000), (8000, -9000), (12000, 3000))]),
          open(outp, "w"))
print("grass", gx.size, "rocks", len(rocks))
