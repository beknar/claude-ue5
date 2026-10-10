"""Grow fig4's strand hair on the MetaHuman (bind pose, Blender metres, Z up, facing -Y).

Shape comes from the scan's hair shell, moved onto the MetaHuman head by the nose-tip offset.
Roots are sampled on the MetaHuman scalp (face skin above the hairline). Strands collide with
the MetaHuman head and body. Guides are traced over the shell; children are interpolated with
clumping and waviness.
Usage: python grow_hair2.py work_dir mh.npz out.npz [--guides N] [--strands N] [--points P]"""
import argparse, numpy as np
from scipy.spatial import cKDTree

ap = argparse.ArgumentParser()
ap.add_argument("work"); ap.add_argument("mh"); ap.add_argument("out")
ap.add_argument("--guides", type=int, default=5000); ap.add_argument("--strands", type=int, default=100000)
ap.add_argument("--points", type=int, default=40); ap.add_argument("--seed", type=int, default=11)
a = ap.parse_args()
rng = np.random.default_rng(a.seed)

H = np.load(f"{a.work}/fig4_hair_shell.npz"); S = np.load(f"{a.work}/fig4_body_target.npz"); M = np.load(a.mh)
fco, fnr = M["face_co"].astype(float), M["face_nr"].astype(float)
bco, bnr = M["body_co"].astype(float), M["body_nr"].astype(float)

# --- align scan -> MetaHuman by the nose tip -------------------------------------------
sp = S["co"]; sface = sp[(sp[:, 2] > 1.50) & (sp[:, 2] < 1.62) & (np.abs(sp[:, 0]) < 0.03)]
s_nose = sface[np.argmin(sface[:, 1])]
mface = fco[(np.abs(fco[:, 0]) < 0.03) & (fco[:, 2] > fco[:, 2].max() - 0.20)]
m_nose = mface[np.argmin(mface[:, 1])]
OFF = m_nose - s_nose
print("nose scan", s_nose.round(3), "mh", m_nose.round(3), "offset", OFF.round(3))
hp = H["co"].astype(float) + OFF
C = np.array([0.0, -0.010, 1.600]) + OFF                  # head centre (scan estimate, moved)
PART_X = 0.004
htree = cKDTree(hp)

# --- collision surfaces: MetaHuman head + body (normals outward) ---------------------------
col_p = np.vstack([fco, bco]); col_n = np.vstack([fnr, bnr])
ctree = cKDTree(col_p)
top = fco[:, 2].max()

def collide(q, margin=0.004):
    d, i = ctree.query(q)
    pen = np.einsum("ij,ij->i", q - col_p[i], col_n[i]) - margin
    hit = (pen < 0) & (d < 0.04)
    q[hit] -= pen[hit, None] * col_n[i[hit]]
    # keep the face clear (box in front of it, exit sideways)
    face = (q[:, 1] < m_nose[1] + 0.06) & (q[:, 2] > m_nose[2] - 0.11) & (q[:, 2] < m_nose[2] + 0.085) & (np.abs(q[:, 0]) < 0.066)
    q[face, 0] = np.where(q[face, 0] >= 0, 0.066, -0.066)
    return q, int(hit.sum() + face.sum())

def shell_frame(p, k=40):
    d, i = htree.query(p, k=k)
    nb = hp[i]; m = nb.mean(1)
    X = nb - m[:, None, :]
    w, v = np.linalg.eigh(np.einsum("nki,nkj->nij", X, X))
    n = v[:, :, 0]
    ax = np.zeros_like(m); ax[:, 2] = m[:, 2]; ax[:, 1] = 0.02 + OFF[1]
    ax[m[:, 2] > C[2] - 0.13] = C
    s = np.sign(np.einsum("ij,ij->i", n, m - ax)); s[s == 0] = 1
    return m, n * s[:, None], d[:, 0]

# --- scalp roots on the MetaHuman --------------------------------------------------------
rel = fco - C
theta = np.abs(np.arctan2(rel[:, 0], -rel[:, 1]))          # 0 = front
hairline = (C[2] - 0.035) + 0.090 * np.cos(theta)           # forehead high, nape low
scalp_mask = (fco[:, 2] > hairline) & ~((theta < 0.6) & (fco[:, 2] < C[2] + 0.055))
# no hair on the ears
ear = (np.abs(rel[:, 0]) > 0.06) & (fco[:, 2] < C[2] - 0.005) & (np.abs(rel[:, 1]) < 0.035)
scalp_mask &= ~ear
scalp = fco[scalp_mask]; scalp_n = fnr[scalp_mask]
print("scalp verts", len(scalp))

def sample_roots(n):
    # area-uniform-ish: jittered picks from scalp vertices, pushed 0.5 mm out
    i = rng.integers(0, len(scalp), n)
    j = rng.normal(scale=0.002, size=(n, 3))
    r = scalp[i] + j
    r -= np.einsum("ij,ij->i", j, scalp_n[i])[:, None] * scalp_n[i]
    return r + scalp_n[i] * 0.0005, scalp_n[i]

STEP, MAX_STEPS = 0.003, 300
def trace(roots, rnorm, depth):
    n = len(roots)
    path = np.full((MAX_STEPS + 1, n, 3), np.nan); path[0] = roots
    p = roots.copy(); alive = np.ones(n, bool); length = np.zeros(n)
    prev = rnorm.copy()                                       # leave the scalp along its normal
    for s in range(MAX_STEPS):
        idx = np.nonzero(alive)[0]
        if not len(idx): break
        q = p[idx]
        m, nrm, dist = shell_frame(q)
        z = q[:, 2]
        top_w = np.clip((z - (C[2] + 0.0)) / 0.08, 0, 1)
        side = np.sign(q[:, 0] - PART_X); side[side == 0] = 1
        comb = np.zeros_like(q); comb[:, 0] = side * 2.2 * top_w
        comb[:, 1] = np.where(q[:, 1] > C[1] + 0.015, 1.8 * top_w, 0.0)
        d0 = comb + np.array([0, 0, -1.0])
        d = d0 - np.einsum("ij,ij->i", d0, nrm)[:, None] * nrm
        d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
        lift = np.clip(1 - length[idx] / 0.012, 0, 1)[:, None]   # first ~1 cm: rise off the scalp
        d = (1 - lift) * d + lift * rnorm[idx]
        d = 0.5 * d + 0.5 * prev[idx]
        d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
        free = q + STEP * d
        plane = free - np.einsum("ij,ij->i", free - m, nrm)[:, None] * nrm
        target = plane + nrm * depth[idx, None]
        w = np.clip(length[idx] / 0.03, 0.0, 1.0)[:, None] * 0.35
        nq = free * (1 - w) + target * w
        nq, _ = collide(nq)
        step_len = np.linalg.norm(nq - q, axis=1)
        length[idx] += step_len
        prev[idx] = (nq - q) / (step_len[:, None] + 1e-9)
        p[idx] = nq; path[s + 1, idx] = nq
        dd = htree.query(nq)[0]
        dead = ((dd > 0.016) & (length[idx] > 0.05)) | (nq[:, 2] < hp[:, 2].min() - 0.01) | (length[idx] > 0.85)
        alive[idx[dead]] = False
    return path, length

def resample(path, npts):
    S_, n, _ = path.shape; out = np.empty((n, npts, 3))
    for j in range(n):
        c = path[:, j]; c = c[~np.isnan(c[:, 0])]
        if len(c) < 2: c = np.vstack([c, c + [0, 0, -0.01]])
        seg = np.linalg.norm(np.diff(c, axis=0), axis=1); t = np.concatenate([[0], np.cumsum(seg)])
        tt = np.linspace(0, t[-1], npts)
        out[j] = np.stack([np.interp(tt, t, c[:, k]) for k in range(3)], 1)
    return out

print("tracing guides...")
groots, gnorm = sample_roots(a.guides)
gdepth = rng.uniform(-0.010, 0.002, a.guides)
gpath, glen = trace(groots, gnorm, gdepth)
keep = glen > 0.06
NP = a.points
G = resample(gpath[:, keep], NP); groots = G[:, 0]
for _ in range(30):
    Gs = G.copy()
    Gs[:, 2:-1] = 0.5 * G[:, 2:-1] + 0.25 * (G[:, 1:-2] + G[:, 3:])
    Gs[:, -1] = 0.5 * G[:, -1] + 0.5 * (2 * G[:, -2] - G[:, -3])
    G = collide(Gs.reshape(-1, 3))[0].reshape(G.shape)
print(f"guides kept {keep.sum()}/{a.guides}, length mean {glen[keep].mean():.3f} max {glen[keep].max():.3f}")

croots, cnorm = sample_roots(a.strands)
gt = cKDTree(groots)
gd, gi = gt.query(croots, k=3)
wts = 1.0 / (gd + 0.004); wts /= wts.sum(1, keepdims=True)
relg = G - G[:, :1]
child = croots[:, None, :] + np.einsum("nk,nkpj->npj", wts, relg[gi])
t = np.linspace(0, 1, NP)
trim = rng.uniform(0.82, 1.0, a.strands)
for j in range(len(child)):
    tt = t * trim[j]
    child[j] = np.stack([np.interp(tt, t, child[j, :, k]) for k in range(3)], 1)
clump = rng.uniform(0.3, 0.7, a.strands)[:, None, None] * (t[None, :, None] ** 1.2)
child = child * (1 - clump) + G[gi[:, 0]] * clump
phase = rng.uniform(0, 2 * np.pi, (a.strands, 1)); freq = rng.uniform(3, 7, (a.strands, 1))
amp = rng.uniform(0.0008, 0.0025, (a.strands, 1)) * t[None, :] ** 0.7
child += np.stack([np.sin(freq * t * 2 * np.pi + phase), np.zeros_like(amp), np.cos(freq * t * 2 * np.pi + phase * 1.3)], 2) * amp[:, :, None]
child += rng.normal(scale=0.00015, size=child.shape) * t[None, :, None]
flat, nfix = collide(child.reshape(-1, 3), margin=0.003)
child = flat.reshape(child.shape)
child[:, 0] = croots                                          # roots stay on the scalp
print(f"children {len(child)} x {NP}, collision fixes {nfix}")
np.savez(a.out, strands=child.astype(np.float32), guides=G.astype(np.float32), offset=OFF)
