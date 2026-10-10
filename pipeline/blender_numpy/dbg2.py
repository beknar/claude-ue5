import numpy as np, sys
from scipy.spatial import ConvexHull
P = np.load(sys.argv[1])["co"]; x, y, z = P.T
def g(z0, xm=0.20):
    m = (np.abs(z - z0) < 0.005) & (np.abs(x) < xm)
    pts = P[m][:, :2]; h = ConvexHull(pts); v = pts[h.vertices]
    return np.sum(np.linalg.norm(np.roll(v, -1, 0) - v, axis=1)) * 100, P[m][:,0].max()*100, P[m][:,1].min()*100
for zz in np.arange(1.10, 1.42, 0.02):
    print(f"z {zz:.2f} girth {g(zz)[0]:6.1f}  half-width {g(zz)[1]:5.1f}  front y {g(zz)[2]:6.1f}")
