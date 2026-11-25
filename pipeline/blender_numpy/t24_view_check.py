"""The list of 2026-11-22's phase 24 (948, RDTower24.cpp): the city seen from a tower's window against the city itself. `884 tower24_window`
pictures the city's picture inside the tower with the tower hidden (bs_<tag>_t24_look_<way>.png: from the middle of the floor the middle
picture stands for, level each way, up and down); `tower24_exit` pictures Heaven from the same point with the tower taken out, as the
windows' picture was taken (bs_<tag>_t24_citylook_<way>.png). This reads each pair: both pictures reduced to 64 x 64 grey levels, each
scaled to its own mean and spread (the tower's exposure is its own), then their correlation and the share of their 8 x 8 blocks whose
brightness ranks agree; and a pair of different ways as the baseline (north against east). Writes a sheet of the pairs beside the
record. Args: <screenshots dir> <tag> [out.json]"""
import sys, os, json
import numpy as np
from PIL import Image

D, TAG = sys.argv[1], sys.argv[2]
OUT = sys.argv[3] if len(sys.argv) > 3 else None
WAYS = ["n", "e", "s", "w", "up", "down"]


def grey(path, n=64):
    a = np.asarray(Image.open(path).convert("L").resize((n, n), Image.BILINEAR), dtype=np.float64)
    return (a - a.mean()) / (a.std() + 1e-6)


def blocks(a, k=8):
    n = a.shape[0] // k
    return a.reshape(k, n, k, n).mean(axis=(1, 3)).ravel()


res = {}
for w in WAYS:
    pa, pb = os.path.join(D, f"bs_{TAG}_t24_look_{w}.png"), os.path.join(D, f"bs_{TAG}_t24_citylook_{w}.png")
    if not (os.path.exists(pa) and os.path.exists(pb)): continue
    a, b = grey(pa), grey(pb)
    corr = float((a * b).mean())
    ba, bb = blocks(a), blocks(b)
    ra, rb = ba.argsort().argsort(), bb.argsort().argsort()
    rank = float(np.corrcoef(ra, rb)[0, 1])
    res[w] = {"correlation": round(corr, 3), "block_rank_correlation": round(rank, 3)}
# (the baseline: one way's look against another way's city)
if all(os.path.exists(os.path.join(D, f"bs_{TAG}_t24_{k}_{w}.png")) for k, w in (("look", "n"), ("citylook", "e"))):
    a, b = grey(os.path.join(D, f"bs_{TAG}_t24_look_n.png")), grey(os.path.join(D, f"bs_{TAG}_t24_citylook_e.png"))
    res["baseline_n_vs_e"] = {"correlation": round(float((a * b).mean()), 3)}
print(json.dumps(res, indent=1))
# (a sheet: the tower's pictures over the city's)
ims = [(w, Image.open(os.path.join(D, f"bs_{TAG}_t24_look_{w}.png")).convert("RGB").resize((256, 256)), Image.open(os.path.join(D, f"bs_{TAG}_t24_citylook_{w}.png")).convert("RGB").resize((256, 256)))
       for w in WAYS if w in res]
sheet = Image.new("RGB", (256 * max(1, len(ims)), 512), (20, 20, 20))
for i, (w, a, b) in enumerate(ims): sheet.paste(a, (i * 256, 0)); sheet.paste(b, (i * 256, 256))
sheet.save(os.path.join(D, f"bs_{TAG}_t24_viewcheck.jpg"), quality=88)
if OUT: json.dump(res, open(OUT, "w"), indent=1)
