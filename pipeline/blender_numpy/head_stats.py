import numpy as np, sys
w = sys.argv[1]
H = np.load(w + r"\fig4_hair_shell.npz"); B = np.load(w + r"\fig4_body_target.npz")
h, b = H["co"], B["co"]
print("hair bbox", h.min(0).round(3), h.max(0).round(3))
print("body bbox", b.min(0).round(3), b.max(0).round(3))
top = h[:, 2].max()
for dz in np.arange(0, 0.40, 0.02):
    z0 = top - dz; mh = np.abs(h[:, 2] - z0) < 0.01; mb = np.abs(b[:, 2] - z0) < 0.01
    s = f"z={z0:.3f} hair n={mh.sum():6d}"
    if mh.any(): s += f" x[{h[mh,0].min():+.3f},{h[mh,0].max():+.3f}] y[{h[mh,1].min():+.3f},{h[mh,1].max():+.3f}]"
    if mb.any(): s += f" | body n={mb.sum():6d} x[{b[mb,0].min():+.3f},{b[mb,0].max():+.3f}] y[{b[mb,1].min():+.3f},{b[mb,1].max():+.3f}]"
    print(s)
