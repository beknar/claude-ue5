"""Stage 2 of the outfit refit (numpy/scipy): place each scanned garment on the posed MetaHuman,
skin it, and inverse-skin it back to the bind pose.

  dress     shifted by the bust-apex offset, pushed out of the body (3 mm), displacement smoothed
  stockings shifted with the legs, shrink-wrapped to the skin (0.6 mm; lace band 1.2 mm)
  shoes     rigidly moved under each posed foot (ball of foot on the forefoot, heel aligned)
  choker    moved with the head, then radially snugged to sit 1.5 mm off the neck
Weights: dress/stockings from the nearest posed body vertices (IDW, top 4, smoothed on the mesh);
shoes 100 % foot bone; choker neck_01/neck_02 by height.
Usage: python fit_outfit_np.py work_dir mh.npz out.npz"""
import sys, json, numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix

W, MH, OUT = sys.argv[1:4]
P = np.load(f"{W}/posed.npz")
Pb, Nb, Wi, Ww, SK = P["posed"], P["normals"], P["wi"], P["ww"], P["skin"]
bones = [str(b) for b in P["bones"]]; bidx = {b: i for i, b in enumerate(bones)}
LIFT = float(P["lift"]); J = json.loads(str(P["joints"]))
M = np.load(MH)
face = M["face_co"] + np.array([0, 0, LIFT]); face_n = M["face_nr"]
scan = np.load(f"{W}/fig4_body_target.npz")["co"]
btree = cKDTree(Pb)
parts = {n: np.load(f"{W}/part_{n}.npz") for n in ("dress", "stockings", "shoes", "choker")}

def adjacency(tri, n):
    e = np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
    e = np.concatenate([e, e[:, ::-1]])
    A = coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
    A.data[:] = 1.0
    deg = np.asarray(A.sum(1)).ravel(); deg[deg == 0] = 1
    return A, deg

def smooth_field(F, A, deg, it):
    for _ in range(it):
        F = 0.5 * F + 0.5 * (A @ F) / deg[:, None]
    return F

def signed_dist(p):
    d, i = btree.query(p)
    return np.einsum("ij,ij->i", p - Pb[i], Nb[i]), i

def body_weights(p, k=8):
    d, i = btree.query(p, k=k)
    w = 1.0 / (d + 1e-4); w /= w.sum(1, keepdims=True)
    acc = np.zeros((len(p), len(bones)), np.float32)
    for j in range(k):
        for c in range(4):
            np.add.at(acc, (np.arange(len(p)), Wi[i[:, j], c]), w[:, j] * Ww[i[:, j], c])
    return acc

def top4(acc):
    idx = np.argsort(-acc, axis=1)[:, :4]
    w = np.take_along_axis(acc, idx, 1); w /= w.sum(1, keepdims=True) + 1e-9
    return idx, w

out = {}
# --- torso offset from the bust apex -------------------------------------------------------
def apex(pts, zlo, zhi):
    m = (np.abs(pts[:, 0]) > 0.04) & (np.abs(pts[:, 0]) < 0.13) & (pts[:, 2] > zlo) & (pts[:, 2] < zhi)
    q = pts[m]; return q[np.argmin(q[:, 1])]
a_s = apex(scan, 1.15, 1.40); a_m = apex(Pb, 1.00, 1.32)
D_t = a_m - a_s; D_t[0] = 0.0
print("bust apex scan", a_s.round(3), "mh", a_m.round(3), "torso offset", D_t.round(3))

# --- dress -------------------------------------------------------------------------------------
dr = parts["dress"]; X = dr["co"] + D_t
# drop loose fragments (mislabeled hair bits): connected components on position-welded vertices
from scipy.sparse.csgraph import connected_components
_, inv = np.unique(np.round(dr["co"] / 1e-5).astype(np.int64), axis=0, return_inverse=True)
inv = inv.ravel(); t = inv[dr["tri"]]
e = np.concatenate([t[:, [0, 1]], t[:, [1, 2]]])
G = coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(inv.max() + 1,) * 2)
ncomp, lab = connected_components(G, directed=False)
sizes = np.bincount(lab)
keep_comp = sizes >= 0.01 * sizes.sum()
dress_keep = keep_comp[lab[inv]]
print(f"dress components {ncomp}, keeping {keep_comp.sum()}, dropping {np.sum(~dress_keep)} verts")
A, deg = adjacency(dr["tri"], len(X))
sd, _ = signed_dist(X)
disp = np.zeros_like(X)
_, ii = btree.query(X)
push = np.clip(0.004 - sd, 0, None)
disp += push[:, None] * Nb[ii]
disp = smooth_field(disp, A, deg, 12)
X = X + disp
# smooth the ragged open edges (neckline, straps, hem): work on position-welded vertices
uniq, winv = np.unique(np.round(dr["co"] / 1e-5).astype(np.int64), axis=0, return_inverse=True)
winv = winv.ravel(); nu = winv.max() + 1
U = np.zeros((nu, 3)); np.add.at(U, winv, X); U /= np.bincount(winv, minlength=nu)[:, None]
wt = winv[dr["tri"]]
edges = np.sort(np.concatenate([wt[:, [0, 1]], wt[:, [1, 2]], wt[:, [2, 0]]]), axis=1)
eu, ec = np.unique(edges, axis=0, return_counts=True)
bnd = eu[ec == 1]                                         # open boundary edges
isb = np.zeros(nu, bool); isb[bnd.ravel()] = True
Bn = coo_matrix((np.ones(2 * len(bnd)), (np.r_[bnd[:, 0], bnd[:, 1]], np.r_[bnd[:, 1], bnd[:, 0]])), shape=(nu, nu)).tocsr()
bdeg = np.asarray(Bn.sum(1)).ravel(); bdeg[bdeg == 0] = 1
U0 = U.copy()
for _ in range(40):                                       # 1-D smoothing along the edge loops
    Ub = (Bn @ U) / bdeg[:, None]
    U[isb] = 0.5 * U[isb] + 0.5 * Ub[isb]
Aw, dw = adjacency(wt, nu)
dU = U - U0
for _ in range(15):                                       # blend the edge correction into the surface
    dU = np.where(isb[:, None], dU, (Aw @ dU) / dw[:, None] * 0.9)
U = U0 + dU
X = U[winv]
print(f"dress: smoothed {isb.sum()} boundary verts")
sd2, _ = signed_dist(X); print(f"dress: pushed {np.sum(push > 0)} verts, still inside {np.sum(sd2 < 0.0)}")
acc = body_weights(X)
acc = smooth_field(acc, A, deg, 6)
out["dress"] = (X, *top4(acc))

# --- stockings ---------------------------------------------------------------------------------
st = parts["stockings"]; X = st["co"] + np.array([0, 0, D_t[2]])
A, deg = adjacency(st["tri"], len(X))
top = X[:, 2].max()
d, i = btree.query(X)
off = np.where(X[:, 2] > top - 0.075, 0.0012, 0.0006)
proj = Pb[i] + Nb[i] * off[:, None]
X = smooth_field(proj - X, A, deg, 4) + X
acc = smooth_field(body_weights(X, k=4), A, deg, 3)
out["stockings"] = (X, *top4(acc))
print("stockings z", X[:, 2].min().round(3), X[:, 2].max().round(3))

# --- shoes (rigid per side) --------------------------------------------------------------------
sh = parts["shoes"]; X = sh["co"].copy()
idx = np.zeros((len(X), 4), int); wts = np.zeros((len(X), 4))
for side, sg in (("l", 1), ("r", -1)):
    m = sg * X[:, 0] > 0
    s = X[m]
    sole = s[s[:, 2] < 0.035]
    tip = sole[np.argmin(sole[:, 1])]
    fore = sole[sole[:, 1] < tip[1] + 0.09].mean(0)
    back = s[s[:, 1] > np.percentile(s[:, 1], 90)]
    heel_top = back[np.argmax(back[:, 2])]
    ball = np.array(J[f"ball_{side}"]); ank = np.array(J[f"foot_{side}"])
    s = fore + (s - fore) * np.array([1.10, 1.10, 1.06])     # roomier: MetaHuman feet are larger
    v_s = (heel_top - fore)[:2]; v_m = (ank - ball)[:2]
    ang = np.arctan2(v_m[1], v_m[0]) - np.arctan2(v_s[1], v_s[0])
    c, s_ = np.cos(ang), np.sin(ang)
    R = np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])
    fwd = (ball - ank)[:2]; fwd = fwd / np.linalg.norm(fwd)
    anchor = ball[:2] + fwd * 0.03               # forefoot centroid sits ~3 cm ahead of the ball joint
    newp = (s - fore) @ R.T + np.array([anchor[0], anchor[1], fore[2]])
    X[m] = newp
    idx[m, 0] = bidx[f"foot_{side}"]; wts[m, 0] = 1.0
    print(f"shoe {side}: yaw {np.degrees(ang):.1f} deg, forefoot -> ball {ball.round(3)}")
out["shoes"] = (X, idx, wts)

# --- choker ------------------------------------------------------------------------------------
ch = parts["choker"]
head_off = np.array([0.0, -0.006, 0.169 - LIFT])
X = ch["co"] - head_off
# the MetaHuman neck is shorter than the stylised scan's: sit the band at mid-neck (2.5 cm lower)
X[:, 2] -= 0.025
# fit as a band: per angle, inner radius = neck radius + 2.5 mm (band thickness kept)
zlo, zhi = X[:, 2].min(), X[:, 2].max()
neck = np.vstack([face, Pb])
neck = neck[(neck[:, 2] > zlo) & (neck[:, 2] < zhi)]
neck = neck[np.linalg.norm(neck[:, :2] - np.median(neck[:, :2], 0), axis=1) < 0.068]   # neck column only
cen = neck[:, :2].mean(0)
NB = 36
def polar(p):
    d = p[:, :2] - cen
    return np.arctan2(d[:, 1], d[:, 0]), np.linalg.norm(d, axis=1)
tn, rn_ = polar(neck); tc, rc = polar(X)
bins = np.linspace(-np.pi, np.pi, NB + 1)
bn = np.clip(np.digitize(tn, bins) - 1, 0, NB - 1); bc = np.clip(np.digitize(tc, bins) - 1, 0, NB - 1)
r_neck = np.array([np.percentile(rn_[bn == k], 75) if np.any(bn == k) else np.nan for k in range(NB)])
r_in = np.array([np.percentile(rc[bc == k], 5) if np.any(bc == k) else np.nan for k in range(NB)])
ok = ~np.isnan(r_neck) & ~np.isnan(r_in)
delta = np.interp(np.arange(NB), np.nonzero(ok)[0], (r_neck + 0.0025 - r_in)[ok])
delta = np.clip(np.convolve(np.r_[delta[-2:], delta, delta[:2]], np.ones(5) / 5, "valid"), -0.02, 0.02)
newr = rc + delta[bc]
X[:, 0] = cen[0] + np.cos(tc) * newr; X[:, 1] = cen[1] + np.sin(tc) * newr
print("choker band fit: neck r", np.nanmedian(r_neck).round(4), "radial change", np.round([delta.min(), delta.max()], 4),
      "z", zlo.round(3), zhi.round(3))
zc = (X[:, 2] - X[:, 2].min()) / (np.ptp(X[:, 2]) + 1e-9)
idx = np.zeros((len(X), 4), int); wts = np.zeros((len(X), 4))
idx[:, 0] = bidx["neck_01"]; idx[:, 1] = bidx["neck_02"]
wts[:, 0] = 1 - 0.5 * zc; wts[:, 1] = 0.5 * zc
out["choker"] = (X, idx, wts)

# --- inverse skinning to the bind pose ---------------------------------------------------------
res = {}
for name, (X, idx, w) in out.items():
    Mx = np.einsum("nk,nkij->nij", w, SK[idx])
    Xh = np.concatenate([X, np.ones((len(X), 1))], 1)
    rest = np.einsum("nij,nj->ni", np.linalg.inv(Mx), Xh)[:, :3]
    res[f"{name}_rest"] = rest; res[f"{name}_idx"] = idx; res[f"{name}_w"] = w
    print(f"{name}: {len(X)} verts; rest z {rest[:, 2].min():.3f}..{rest[:, 2].max():.3f}")
np.savez(OUT, bones=np.array(bones), dress_keep=dress_keep, **res)
