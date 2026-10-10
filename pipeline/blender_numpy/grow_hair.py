"""Grow strand hair for fig4 from her scanned hair shell.

Guides start on a scalp, flow down the shell surface (gravity projected onto it, combed away
from the part on top), stop where the shell ends, and avoid the body. Child strands are
interpolated from the nearest guides with clumping and frizz.

Coordinates: Blender world space, meters, Z up, she faces -Y.
Usage: python grow_hair.py work_dir out.npz [--scalp scalp.npz] [--guides N] [--strands N]
  scalp.npz (optional): co/nr/tri of a real scalp (e.g. the MetaHuman head); roots are
  snapped onto it. Without it an ellipsoid fitted to the shell stands in.
"""
import argparse, numpy as np
from scipy.spatial import cKDTree

ap = argparse.ArgumentParser()
ap.add_argument("work"); ap.add_argument("out")
ap.add_argument("--scalp"); ap.add_argument("--guides", type=int, default=4000)
ap.add_argument("--strands", type=int, default=90000); ap.add_argument("--seed", type=int, default=7)
a = ap.parse_args()
rng = np.random.default_rng(a.seed)

H = np.load(f"{a.work}/fig4_hair_shell.npz"); B = np.load(f"{a.work}/fig4_body_target.npz")
hp, bp, bn = H["co"].astype(np.float64), B["co"].astype(np.float64), B["nr"].astype(np.float64)
C = np.array([0.0, -0.010, 1.600])            # head centre
R = np.array([0.083, 0.103, 0.112])           # scalp ellipsoid radii (shell minus ~1 cm)
PART_X = 0.004
htree = cKDTree(hp)

# Body normals point outward? Orient them away from the body's vertical axis.
def axis_point(p):
    q = np.zeros_like(p); q[:, 2] = p[:, 2]
    q[:, 1] = 0.02
    q[p[:, 2] > 1.47] = C                      # the head: outward = away from its centre
    return q
flip = np.einsum("ij,ij->i", bn, bp - axis_point(bp)) < 0
bn[flip] *= -1
# Below the head only: the head's "skin" under the hair is mostly mislabeled hair bits, so
# the head collides with the scalp ellipsoid instead (see collide()).
low = bp[:, 2] < 1.50
bp, bn = bp[low], bn[low]
btree = cKDTree(bp)


def collide(q, margin=0.004):
    """Push points out of the body (below the head), the scalp ellipsoid and the face."""
    bd, bi = btree.query(q)
    pen = np.einsum("ij,ij->i", q - bp[bi], bn[bi]) - margin
    hit = (pen < 0) & (bd < 0.03) & (q[:, 2] < 1.50)
    q[hit] -= pen[hit, None] * bn[bi[hit]]
    e = (q - C) / R
    r = np.linalg.norm(e, axis=1)
    inside = r < 1.0
    q[inside] = C + e[inside] / r[inside, None] * R
    # keep the face clear: a box in front of it, exit sideways
    face = (q[:, 1] < -0.055) & (q[:, 2] > 1.45) & (q[:, 2] < 1.645) & (np.abs(q[:, 0]) < 0.068)
    q[face, 0] = np.where(q[face, 0] >= 0, 0.068, -0.068)
    return q, hit.sum() + inside.sum() + face.sum()


# Shell frame: local plane through the k nearest shell points (large k smooths the lumpy scan)
def shell_frame(p, k=40):
    d, i = htree.query(p, k=k)
    nb = hp[i]                                   # (n,k,3)
    m = nb.mean(1)
    # local plane normal via smallest eigenvector of the neighbourhood covariance
    X = nb - m[:, None, :]
    cov = np.einsum("nki,nkj->nij", X, X)
    w, v = np.linalg.eigh(cov)
    n = v[:, :, 0]
    out = m - axis_point(m)
    n *= np.sign(np.einsum("ij,ij->i", n, out))[:, None] + (np.einsum("ij,ij->i", n, out) == 0)[:, None]
    return m, n, d[:, 0]

# ---------------------------------------------------------------- roots
def hairline_z(theta):          # theta 0 = front, pi = back
    return 1.565 + 0.090 * np.cos(theta)

def ellipsoid_point(dirs):
    dirs = dirs / np.linalg.norm(dirs / R, axis=1, keepdims=True) / 1.0
    return C + dirs

def sample_roots(n):
    pts = []
    while sum(len(p) for p in pts) < n:
        u = rng.normal(size=(n * 3, 3)); u /= np.linalg.norm(u, axis=1, keepdims=True)
        p = C + u * R
        theta = np.arctan2(p[:, 0], -(p[:, 1] - C[1]))
        ok = p[:, 2] > hairline_z(np.abs(theta))
        # thin out the area right on the part line
        ok &= ~((np.abs(p[:, 0] - PART_X) < 0.003) & (p[:, 1] < C[1] + 0.03) & (p[:, 2] > 1.66))
        pts.append(p[ok])
    p = np.concatenate(pts)[:n]
    if a.scalp:
        S = np.load(a.scalp); st = cKDTree(S["co"]); _, i = st.query(p); p = S["co"][i].astype(np.float64)
    return p

# ---------------------------------------------------------------- guides
STEP, MAX_STEPS = 0.003, 300
def trace(roots, depth):
    n = len(roots)
    path = np.full((MAX_STEPS + 1, n, 3), np.nan); path[0] = roots
    p = roots.copy(); alive = np.ones(n, bool); length = np.zeros(n)
    prev = np.zeros((n, 3)); prev[:, 2] = -1
    for s in range(MAX_STEPS):
        idx = np.nonzero(alive)[0]
        if not len(idx): break
        q = p[idx]
        m, nrm, dist = shell_frame(q)
        z = q[:, 2]
        top = np.clip((z - 1.60) / 0.08, 0, 1)
        side = np.sign(q[:, 0] - PART_X); side[side == 0] = 1
        comb = np.zeros_like(q); comb[:, 0] = side * 2.2 * top
        back = (q[:, 1] > C[1] + 0.015)
        comb[:, 1] = np.where(back, 1.8 * top, 0.0)
        d0 = comb + np.array([0, 0, -1.0])
        d = d0 - np.einsum("ij,ij->i", d0, nrm)[:, None] * nrm
        d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
        d = 0.5 * d + 0.5 * prev[idx]                  # smooth turning
        d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
        free = q + STEP * d
        # pull onto this strand's layer of the shell, ramping in over the first 2.5 cm
        plane = free - np.einsum("ij,ij->i", free - m, nrm)[:, None] * nrm
        target = plane + nrm * depth[idx, None]
        w = np.clip(length[idx] / 0.025, 0.15, 1.0)[:, None] * 0.35
        nq = free * (1 - w) + target * w
        nq, _ = collide(nq)
        step_len = np.linalg.norm(nq - q, axis=1)
        length[idx] += step_len
        prev[idx] = (nq - q) / (step_len[:, None] + 1e-9)
        p[idx] = nq
        path[s + 1, idx] = nq
        # stop past the shell's end, at the floor of the hair, or at max length
        dd = htree.query(nq)[0]
        dead = (dd > 0.014) & (length[idx] > 0.03) | (nq[:, 2] < 1.04) | (length[idx] > 0.80)
        alive[idx[dead]] = False
    return path, length

def resample(path, npts):
    """path (S,n,3) with NaN tails -> (n,npts,3) evenly spaced along each strand."""
    S, n, _ = path.shape
    out = np.empty((n, npts, 3))
    for j in range(n):
        c = path[:, j]; c = c[~np.isnan(c[:, 0])]
        if len(c) < 2: c = np.vstack([c, c + [0, 0, -0.01]])
        seg = np.linalg.norm(np.diff(c, axis=0), axis=1); t = np.concatenate([[0], np.cumsum(seg)])
        tt = np.linspace(0, t[-1], npts)
        out[j] = np.stack([np.interp(tt, t, c[:, k]) for k in range(3)], 1)
    return out

print("tracing guides...")
groots = sample_roots(a.guides)
gdepth = rng.uniform(-0.011, 0.001, a.guides)
gpath, glen = trace(groots, gdepth)
keep = glen > 0.04
G = resample(gpath[:, keep], 48); glen = glen[keep]; groots = G[:, 0]
# relax the guides along their length (root pinned), re-colliding as they settle
for _ in range(40):
    Gs = G.copy()
    Gs[:, 1:-1] = 0.5 * G[:, 1:-1] + 0.25 * (G[:, :-2] + G[:, 2:])
    Gs[:, -1] = 0.5 * G[:, -1] + 0.5 * (2 * G[:, -2] - G[:, -3])
    G = Gs
    G = collide(G.reshape(-1, 3))[0].reshape(G.shape)
print(f"guides: {keep.sum()} kept, length mean {glen.mean():.3f} max {glen.max():.3f}")

# ---------------------------------------------------------------- children
NP = 48
croots = sample_roots(a.strands)
gt = cKDTree(groots)
gd, gi = gt.query(croots, k=3)
wts = 1.0 / (gd + 0.004); wts /= wts.sum(1, keepdims=True)
rel = G - G[:, :1]                                       # guide shapes relative to root
child = croots[:, None, :] + np.einsum("nk,nkpj->npj", wts, rel[gi])
# per-strand length variation: trim tips by up to 15 %
t = np.linspace(0, 1, NP)
trim = rng.uniform(0.85, 1.0, a.strands)
for j in range(0, a.strands, 20000):
    sl = slice(j, j + 20000)
    tt = t[None, :] * trim[sl, None]
    seg = child[sl]
    child[sl] = np.stack([np.array([np.interp(tt[i], t, seg[i, :, k]) for i in range(len(tt))]) for k in range(3)], 2)
# clumping toward the nearest guide's path (stronger toward the tips)
clump = rng.uniform(0.35, 0.75, a.strands)[:, None, None] * (t[None, :, None] ** 0.9)
child = child * (1 - clump) + G[gi[:, 0]] * clump
# frizz / waviness: smooth noise that grows along the strand
phase = rng.uniform(0, 2 * np.pi, (a.strands, 1)); freq = rng.uniform(6, 11, (a.strands, 1))
amp = rng.uniform(0.0008, 0.0022, (a.strands, 1)) * t[None, :]
wav = np.stack([np.sin(freq * t * 2 * np.pi + phase), np.zeros_like(amp), np.cos(freq * t * 2 * np.pi + phase * 1.3)], 2)
child += wav * amp[:, :, None]
child += rng.normal(scale=0.0002, size=child.shape) * t[None, :, None]
flat, nfix = collide(child.reshape(-1, 3), margin=0.003)
child = flat.reshape(child.shape)
print(f"children: {len(child)} x {NP} pts, collision fixes {nfix}")
np.savez(a.out, strands=child.astype(np.float32), guides=G.astype(np.float32))
