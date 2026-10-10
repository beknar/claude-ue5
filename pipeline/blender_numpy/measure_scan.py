"""Tape-measure fig4's scan (body target, metres, Z up, facing -Y) for MetaHuman body constraints.
Girths = convex-hull perimeter of a 1 cm horizontal slice. Heights are corrected for the heels."""
import sys, json, numpy as np
from scipy.spatial import ConvexHull
P = np.load(sys.argv[1])["co"]
x, y, z = P.T

def girth(mask):
    pts = P[mask][:, :2]
    if len(pts) < 10: return 0.0
    h = ConvexHull(pts); v = pts[h.vertices]
    return float(np.sum(np.linalg.norm(np.roll(v, -1, 0) - v, axis=1)))

def slice_(z0, xmask=None, w=0.005):
    m = np.abs(z - z0) < w
    if xmask is not None: m &= xmask
    return m

torso = np.abs(x) < 0.20
prof = {}
for zz in np.arange(0.10, 1.70, 0.01):
    prof[round(zz, 2)] = girth(slice_(zz, torso))
# leg (left side, x>0) girth profile below the crotch
legp = {round(zz, 2): girth(slice_(zz, (x > 0.005) & (x < 0.2))) for zz in np.arange(0.10, 0.80, 0.01)}

def argext(d, lo, hi, fn):
    ks = [k for k in d if lo <= k <= hi and d[k] > 0]
    k = fn(ks, key=lambda k: d[k]); return k, d[k]

# ankle: narrowest leg just above the shoe tops (~0.19 m)
ank_z, ank = argext(legp, 0.17, 0.30, min)
# barefoot ankle bone height ~ 0.075 m for a 160 cm woman -> heel lift
lift = ank_z - 0.075
bust_z, bust = argext(prof, 1.18, 1.36, max)
under_z, under = argext(prof, bust_z - 0.12, bust_z - 0.05, min)
waist_z, waist = argext(prof, 0.98, 1.12, min)
hip_z, hip = argext(prof, 0.78, 0.95, max)
# the scan's inner thighs are fused, so the crotch sits ~9 cm below the hip line (anthropometric)
crotch_z = hip_z - 0.09
thigh_z, thigh = argext(legp, round(crotch_z - 0.06, 2), round(crotch_z - 0.02, 2), max)
knee_z, knee = argext(legp, 0.40, 0.55, min)
calf_z, calf = argext(legp, 0.28, 0.42, max)
neck_z, neck = argext(prof, 1.48, 1.54, min)
# shoulders: acromion ~ top of the arm junction; T-pose arms at shoulder height
arm = np.abs(x) > 0.22
sh_z = float(np.percentile(z[arm & (np.abs(x) < 0.26)], 90))
across = float(2 * np.percentile(np.abs(x[(np.abs(z - sh_z) < 0.02) & (np.abs(x) < 0.22)]), 98))
top = z.max()
m = {
    "Height": (top - lift) * 100 + 0.5,
    "Chest": bust * 100, "Underbust": under * 100, "Waist": waist * 100, "Hip": hip * 100,
    "High Hip": prof[round(hip_z + 0.08, 2)] * 100,
    "Thigh": thigh * 100, "Knee": knee * 100, "Calf": calf * 100, "Neck": neck * 100,
    "Shoulder Height": (sh_z - lift) * 100, "Across Shoulder": across * 100,
}
print(json.dumps({k: round(v, 1) for k, v in m.items()}, indent=1))
print(f"lift {lift:.3f}  ankle z {ank_z} bust z {bust_z} waist z {waist_z} hip z {hip_z} crotch z {crotch_z:.3f} sh z {sh_z:.3f}")
json.dump({k: round(v, 1) for k, v in m.items()}, open(sys.argv[2], "w"), indent=1)
