import numpy as np, sys
P = np.load(sys.argv[1])["co"]; x, y, z = P.T
for zz in np.arange(0.55, 0.95, 0.02):
    m = np.abs(z - zz) < 0.005
    mid = m & (np.abs(x) < 0.01)
    left = m & (x > 0.005) & (x < 0.2)
    print(f"z {zz:.2f} n {m.sum():5d} mid {mid.sum():4d} left {left.sum():5d} xr [{x[m].min() if m.any() else 0:+.3f},{x[m].max() if m.any() else 0:+.3f}]")
