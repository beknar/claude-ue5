"""Summoner2's MetaHuman body without its underwear (844's 'underwear' step runs it; numpy, scipy, Pillow). MetaHuman bakes
plain grey briefs into the body's textures (only the top has a switch); she wears her bikini instead. The briefs are found
in the base colour by their colour (neutral grey: red, green and blue within a few levels; her skin is pink, red well
above green), grown a little, and filled in each map with what is around them (an average spreading inward, coarse to
fine), plus the fine detail (pores, the normal map's grain) of the same map 300 texels up, so the filled skin is not
smooth plastic; the edge is feathered.
    python s2_underwear.py <dir>   (reads body_bc.png, body_n.png, body_srmf.png; writes *_fixed.png and mask.png)"""
import sys, os, numpy as np
from PIL import Image
from scipy import ndimage as nd
Image.MAX_IMAGE_PIXELS = None
D = sys.argv[1]
bc = np.asarray(Image.open(os.path.join(D, "body_bc.png")).convert("RGBA"), np.float32)
r, g, b = bc[..., 0], bc[..., 1], bc[..., 2]
grey = (np.abs(r - g) < 14) & (np.abs(r - b) < 16) & (np.abs(g - b) < 14) & (r > 40) & (r < 215)
lab, n = nd.label(grey); sizes = nd.sum(grey, lab, range(1, n + 1))
keep = np.isin(lab, 1 + np.nonzero(sizes > 400)[0])                       # (not the odd grey texel in her skin)
mask = nd.binary_dilation(keep, iterations=6)
print("S2UW mask %.2f%% of the base colour (%d pieces)" % (100 * mask.mean(), int((sizes > 400).sum())))
Image.fromarray((mask * 255).astype(np.uint8)).save(os.path.join(D, "mask.png"))
def fill(img, m):
    """average spreading inward, coarse to fine (a pyramid of normalized blurs)"""
    out = img.copy(); known = (~m).astype(np.float32)
    acc = np.zeros_like(img); wsum = np.zeros(m.shape, np.float32)
    acc[m] = img[~m].mean(0)                                                 # (fallback: the skin's average)
    for s in (256, 128, 64, 32, 16, 8, 4, 2):
        w = nd.gaussian_filter(known, s); v = np.stack([nd.gaussian_filter(img[..., c] * known, s) for c in range(img.shape[2])], -1)
        est = v / np.maximum(w[..., None], 1e-6)
        ok = (w > 0.02) & m
        acc[ok] = est[ok]; wsum[ok] = 1
    out[m] = acc[m]
    return out
def fix(path_in, path_out, m, detail=1.0):
    im = np.asarray(Image.open(path_in).convert("RGBA"), np.float32)
    if im.shape[:2] != m.shape:
        mm = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize(im.shape[1::-1], Image.NEAREST)) > 127
    else:
        mm = m
    k = im.shape[0] / 4096; sh = int(300 * k); pad = int(260 * k)
    rows, cols = np.nonzero(mm.any(1))[0], np.nonzero(mm.any(0))[0]
    y0, y1 = max(rows.min() - pad - sh, 0), min(rows.max() + pad, im.shape[0]); x0, x1 = max(cols.min() - pad, 0), min(cols.max() + pad, im.shape[1])
    sub = im[y0:y1, x0:x1, :3]; ms = mm[y0:y1, x0:x1]                    # (only round the briefs: the maps are 8K)
    f = fill(sub, ms)
    hp = sub - np.stack([nd.gaussian_filter(sub[..., c], 3 * k) for c in range(3)], -1)
    hp = np.roll(hp * (~ms)[..., None], -sh, axis=0)                        # (detail from skin only, not from the briefs)
    f = f + detail * hp * ms[..., None]
    feather = nd.gaussian_filter(ms.astype(np.float32), 2.0 * k)[..., None]
    out = im.copy(); out[y0:y1, x0:x1, :3] = sub * (1 - feather) + f * feather
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(path_out)
    print("S2UW", os.path.basename(path_out), im.shape[:2], "filled %d texels" % int(mm.sum()))
fix(os.path.join(D, "body_bc.png"), os.path.join(D, "body_bc_fixed.png"), mask)
for n_ in ("body_n", "body_srmf"):
    if os.path.exists(os.path.join(D, n_ + ".png")): fix(os.path.join(D, n_ + ".png"), os.path.join(D, n_ + "_fixed.png"), mask, 0.8)
