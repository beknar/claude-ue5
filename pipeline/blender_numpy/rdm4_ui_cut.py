"""Cut out and measure rdm4_ui_gen.py's pictures, and lay them out on a contact sheet.

    python rdm4_ui_cut.py <ui_art.json> <out_dir> [--sheet name.jpg] [--export <dir>]

--export writes the picks at the sizes the game draws them (SIZES: the longer side) as <dir>/<element>.png
and <dir>/layout.json, which pipeline/unreal/830 reads: per piece its `border` (left, top, right, bottom
shares kept when it is stretched: the element's `slice`, else its kind's default; a hollow frame's border
is everything round its open inside) and `inner` (the open inside of a frame with `holes`, measured on
the exported picture: the transparent part joined to the hole point).

For every picture in <out_dir>/raw/manifest.json:
- the ground is near white but not flat: the light, colourless pixels joined to the border (or to one
  of the element's `holes` points: the inside of a hollow frame) are taken as ground and their colour
  spread over the picture, so each pixel is compared with the ground around it; whatever is close to
  that (colour distance below CUT) and joined to the border or a hole point is ground; its alpha ramps
  from 0 at FADE0 to 1 at CUT, and the ground's colour is taken out of the edge pixels;
- the cut picture is cropped to its opaque box plus a margin and written to <out_dir>/cut/;
- measured (written to <out_dir>/cut/measure.json and on the sheet):
  ground  how far the border is from the ground found there (median colour distance; large when the
          border is a painted backdrop or torn-paper edge, which the cut cannot take away)
  cover   the opaque share of the picture
  edge    the main shape's least distance to the picture's border, in pixels (0: cut off by the frame);
          specks under 0.05 % of the picture (dust from the ground's grain) are dropped first
  fringe  the share of the shape's outline pixels still close to the ground's colour (a pale halo:
          a drop shadow or glow on the ground that the cut kept)
  bits    loose pieces besides the main shape larger than 0.05 % of the picture (painted shadows,
          marks), cut away unless the element is made of `pieces`
  sym     for `symmetric` elements, the overlap of the opaque shape with its mirror image (1 = exact)
  hole    for elements with `holes`, the transparent share of the box's middle third (the frame's inside)
and flagged (`flags`, red on the sheet) when a measurement fails: `backdrop` (ground over 3: a painted
backdrop, vignette or torn-paper edge instead of the plain ground), `border` (edge under 4: cut off by
the frame), `fills` (an icon covering over 70 %: the backdrop was kept), `closed`
(hole under 0.9), `lopsided` (sym under 0.95), `pale` (a panel or slot with over 3 % of its opaque
pixels the ground's colour: ground enclosed inside it, which the cut cannot reach; `pale` is measured
on every picture, but glass highlights are pale too, so icons are not flagged by it), `uneven` (a fill
`texture`, kept whole, whose columns' mean brightness spreads over 20 % of their mean: a bar shows any
share of it). What no number catches (a symbol, a signature joined to
the shape, a plate) is for the eye: the sheets are made to be looked at.
Needs numpy, scipy, Pillow.
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

args = sys.argv[1:]
SHEET, EXPORT, ONLY = "sheet.jpg", None, None
if "--only" in args:
    # (a few elements only, for their sheet: no picks, no export, the measures in <sheet>.json)
    i = args.index("--only"); ONLY = set(args[i + 1].split(",")); del args[i:i + 2]
if "--sheet" in args:
    i = args.index("--sheet"); SHEET = args[i + 1]; del args[i:i + 2]
if "--export" in args:
    i = args.index("--export"); EXPORT = args[i + 1]; del args[i:i + 2]
DATA, OUT = args
D = json.load(open(DATA, encoding="utf-8"))
EL = {e["name"]: e for e in D["elements"]}
RAW, CUT = os.path.join(OUT, "raw"), os.path.join(OUT, "cut")
os.makedirs(CUT, exist_ok=True)
FADE0, CUT_D = 10.0, 40.0


def cut(path, e):
    rgb = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    h, w, _ = rgb.shape
    if e["kind"] == "texture":
        # a fill (a bar's liquid): the whole picture (or its `crop`: left, top, right, bottom shares), nothing cut; it
        # must be even along its length (a bar shows any share of it): the spread of its columns' mean brightness
        # against their mean
        if e.get("crop"):
            c0, c1, c2, c3 = e["crop"]
            rgb = rgb[int(c1 * h):int(c3 * h), int(c0 * w):int(c2 * w)]; h, w, _ = rgb.shape
        # (evened along its length: each column brought to the mean brightness by a smooth gain; FLUX lit one end
        # of the red liquids a third brighter than the other, and a low bar would have shown another colour)
        cols0 = rgb.mean(2).mean(0)
        gain = cols0.mean() / np.maximum(ndimage.gaussian_filter1d(cols0, w / 30.0, mode="nearest"), 1.0)
        rgb = np.clip(rgb * gain[None, :, None], 0, 255)
        cols = rgb.mean(2).mean(0)
        return Image.fromarray(np.dstack([rgb, np.full((h, w), 255.0)]).astype(np.uint8)), {
            "ground": 0.0, "cover": 1.0, "edge": 99, "bits": 0, "even": round(float(cols.std() / max(cols.mean(), 1)), 3),
            "even_before": round(float(cols0.std() / max(cols0.mean(), 1)), 3)}

    def joined(mask):                        # the parts of mask joined to the border or a hole point
        lab, _ = ndimage.label(mask)
        seeds = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
        for fx, fy in e.get("holes", []):
            seeds.add(lab[int(fy * (h - 1)), int(fx * (w - 1))])
        seeds.discard(0)
        return np.isin(lab, list(seeds))

    # the ground is near white but not flat (FLUX paints soft gradients and vignettes on it): take the
    # light, colourless pixels joined to the border as ground and spread their colour over the picture
    # (a normalised blur), so each pixel is compared with the ground as it is around it
    # (or, for an element with a coloured backdrop of its own, the pixels near the border's colour)
    mx, mn = rgb.max(2), rgb.min(2)
    edge_col = np.median(np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]]), axis=0)
    if "backdrop" in e:
        g0 = joined(np.linalg.norm(rgb - edge_col, axis=2) < 48)
    else:
        g0 = joined((mx > 170) & ((mx - mn) / np.maximum(mx, 1) < 0.12))
    g0 = g0.astype(np.float32)
    flat = np.median(rgb[g0 > 0], axis=0) if g0.any() else edge_col
    # the blurs at a quarter of the size, then back to full size; the near one is small (8 px): the
    # vignette darkens the corners to 190 within a few dozen pixels, and a 24 px blur left them opaque
    q = 4
    gs = g0[::q, ::q]
    ws, ww = ndimage.gaussian_filter(gs, 8 / q), ndimage.gaussian_filter(gs, 64 / q)
    bg = np.empty_like(rgb)
    for c in range(3):
        cs = rgb[::q, ::q, c] * gs
        near_c = ndimage.gaussian_filter(cs, 8 / q) / np.maximum(ws, 1e-6)
        wide_c = ndimage.gaussian_filter(cs, 64 / q) / np.maximum(ww, 1e-6)
        small = np.where(ws > 1e-3, near_c, np.where(ww > 1e-4, wide_c, flat[c]))
        big = ndimage.zoom(small, (h / small.shape[0], w / small.shape[1]), order=1)
        bg[..., c] = big[:h, :w]
    d = np.linalg.norm(rgb - bg, axis=2)
    ground = float(np.median(np.concatenate([d[0], d[-1], d[:, 0], d[:, -1]])))
    is_bg = joined(d < CUT_D)
    if e.get("enclosed"):
        # (ground the border cannot reach: white, colourless parts over 0.2 % of the picture inside the shape)
        lab_e, n_e = ndimage.label((mx > 200) & ((mx - mn) / np.maximum(mx, 1) < 0.08) & ~is_bg)
        if n_e:
            sz = ndimage.sum(np.ones_like(mx), lab_e, range(1, n_e + 1))
            is_bg |= np.isin(lab_e, [i + 1 for i, s in enumerate(sz) if s > 0.002 * h * w])
    # the ramp also reaches one pixel outside the ground region: the painted outline's soft edge
    near = ndimage.binary_dilation(is_bg, iterations=1)
    a = np.ones((h, w), np.float32)
    a[near] = np.clip((d[near] - FADE0) / (CUT_D - FADE0), 0, 1)
    a[is_bg & (d < FADE0)] = 0
    safe = np.maximum(a, 1e-3)[..., None]
    col = np.clip((rgb - (1 - a[..., None]) * bg) / safe, 0, 255)       # bg: the local ground colour
    solid = a > 0.5
    lab2, n2 = ndimage.label(a > 0.05)
    if n2 == 0:
        return None, {"ground": round(ground, 1), "cover": 0}
    sizes = ndimage.sum(solid, lab2, range(1, n2 + 1))
    main = int(np.argmax(sizes)) + 1
    # only the main shape is kept (loose pieces were painted shadows under floating things, a signature,
    # a speck of the ground's grain), unless the element is made of `pieces` (spilled nuts): then
    # pieces over 0.05 % of the picture stay
    bits = int(np.sum(sizes > 0.0005 * h * w)) - 1
    if e.get("pieces"):
        keep = np.isin(lab2, [i + 1 for i, s in enumerate(sizes) if s > 0.0005 * h * w])
    else:
        keep = lab2 == main
    a[~keep] = 0
    solid = a > 0.5
    ys, xs = np.nonzero(lab2 == main)
    mx0, mx1, my0, my1 = xs.min(), xs.max(), ys.min(), ys.max()
    ys, xs = np.nonzero(solid)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    rim = solid & ndimage.binary_dilation(~solid, iterations=2)
    fringe = float((d[rim] < 60).mean()) if rim.any() else 0.0
    m = {"ground": round(ground, 1), "cover": round(float(solid.mean()), 3),
         "edge": int(min(mx0, my0, w - 1 - mx1, h - 1 - my1)), "fringe": round(fringe, 3), "bits": bits,
         "pale": round(float((d[solid] < CUT_D).mean()), 3),
         "box": [int(x0), int(y0), int(x1), int(y1)]}
    if e.get("symmetric") and not e.get("thin"):
        box = solid[y0:y1 + 1, x0:x1 + 1]
        m["sym"] = round(float((box & box[:, ::-1]).sum() / max(1, (box | box[:, ::-1]).sum())), 3)
    if e.get("holes"):
        bh, bw = y1 - y0 + 1, x1 - x0 + 1
        mid = a[y0 + bh // 3:y0 + 2 * bh // 3, x0 + bw // 3:x0 + 2 * bw // 3]
        m["hole"] = round(float((mid < 0.5).mean()), 3)
    pad = 8
    X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(w, x1 + pad + 1), min(h, y1 + pad + 1)
    rgba = np.dstack([col, a * 255]).astype(np.uint8)[Y0:Y1, X0:X1]
    return Image.fromarray(rgba), m


man = json.load(open(os.path.join(RAW, "manifest.json")))
results = []
for r in man:
    e = EL.get(r["element"])
    if not e or (ONLY and r["element"] not in ONLY):
        continue
    img, m = cut(os.path.join(RAW, r["file"]), e)
    if img is not None:
        img.save(os.path.join(CUT, r["file"]))
    f = []
    if m["ground"] > 3: f.append("backdrop")
    if m.get("edge", 0) < 4: f.append("border")
    if e["kind"] == "icon" and m["cover"] > 0.7: f.append("fills")
    if m.get("hole", 1) < 0.9: f.append("closed")
    if m.get("sym", 1) < 0.95: f.append("lopsided")
    if e["kind"] in ("panel", "slot") and m.get("pale", 0) > 0.03: f.append("pale")
    if m.get("even", 0) > 0.2: f.append("uneven")
    m["flags"] = f
    results.append(dict(r, **m))
json.dump(results, open(os.path.join(CUT, os.path.splitext(SHEET)[0] + ".json" if ONLY else "measure.json"), "w"), indent=1)

# contact sheets: one row per element (PAGE rows a sheet), its candidates on a checkerboard (the cut's alpha shows)
CELL, LBL, PAGE = 300, 54, 4
rows = {}
for r in results:
    rows.setdefault(r["element"], []).append(r)
ncol = max(len(v) for v in rows.values())
try:
    font = ImageFont.truetype("arial.ttf", 14)
except OSError:
    font = ImageFont.load_default()
ii, jj = np.indices((CELL, CELL))
chk = (ii // 16 + jj // 16) % 2
chk = Image.fromarray(np.where(chk[..., None], [200, 200, 200], [120, 120, 120]).astype(np.uint8))
items = list(rows.items())
stem, ext = os.path.splitext(SHEET)
sheets = []
for page in range(0, len(items), PAGE):
    part = items[page:page + PAGE]
    sheet = Image.new("RGB", (150 + ncol * CELL, len(part) * (CELL + LBL)), (40, 40, 40))
    dr = ImageDraw.Draw(sheet)
    for ri, (name, rs) in enumerate(part):
        y = ri * (CELL + LBL)
        dr.text((8, y + CELL // 2), name, fill=(255, 255, 255), font=font)
        for ci, r in enumerate(rs):
            x = 150 + ci * CELL
            sheet.paste(chk, (x, y))
            p = os.path.join(CUT, r["file"])
            if os.path.exists(p):
                im = Image.open(p)
                im.thumbnail((CELL - 8, CELL - 8))
                sheet.paste(im, (x + (CELL - im.width) // 2, y + (CELL - im.height) // 2), im)
            t = f"{ci + 1}: {r['seed']}  cover {r.get('cover')}\nedge {r.get('edge')} fringe {r.get('fringe')} bits {r.get('bits')}"
            if "sym" in r:
                t += f" sym {r['sym']}"
            if "hole" in r:
                t += f" hole {r['hole']}"
            dr.multiline_text((x + 4, y + CELL + 2), t, fill=(230, 230, 230), font=font, spacing=2)
            if r["flags"]:
                dr.rectangle([x, y, x + CELL - 1, y + CELL - 1], outline=(220, 40, 40), width=3)
                dr.text((x + 6, y + 4), " ".join(r["flags"]), fill=(255, 60, 60), font=font)
    sheets.append(os.path.join(OUT, f"{stem}_{page // PAGE + 1}{ext}"))
    sheet.save(sheets[-1], quality=90)
print("sheets", sheets, len(results), "pictures")
for r in results:
    print(r["file"], {k: r.get(k) for k in ("ground", "cover", "edge", "fringe", "bits", "sym", "hole", "flags")})
ok = {}
for r in results:
    ok[r["element"]] = ok.get(r["element"], 0) + (not r["flags"])
print("unflagged per element:", ok, "total", sum(ok.values()), "of", len(results))

# the picks (ui_art.json's `picks`: element -> seed): copied to <out_dir>/picks/<element>.png and laid
# out on the HUD's dark ground, each icon inside the picked slot frame, to be judged where it will be seen
picks = {k: v for k, v in D.get("picks", {}).items() if not k.startswith("_")}
if picks and not ONLY:
    PK = os.path.join(OUT, "picks"); os.makedirs(PK, exist_ok=True)
    by = {(r["element"], r["seed"]): r for r in results}
    chosen = {}
    for name, seed in picks.items():
        r = by.get((name, seed))
        if r is None:
            print("PICK MISSING", name, seed); continue
        if r["flags"]:
            print("PICK FLAGGED", name, seed, r["flags"])
        chosen[name] = Image.open(os.path.join(CUT, r["file"]))
        chosen[name].save(os.path.join(PK, name + ".png"))
    BG, C = (22, 19, 16), 170
    icons = [n for n in chosen if EL[n]["kind"] == "icon"]
    ncol = 7
    nrow = (len(icons) + ncol - 1) // ncol
    W = 40 + ncol * C
    sheet = Image.new("RGB", (W, 420 + nrow * (C + 24) + 20), BG)
    dr = ImageDraw.Draw(sheet)

    def put(im, box):                        # fit im into box (x, y, w, h), centred
        im = im.copy(); im.thumbnail((box[2], box[3]), Image.LANCZOS)
        sheet.paste(im, (box[0] + (box[2] - im.width) // 2, box[1] + (box[3] - im.height) // 2), im)
    if "panel" in chosen:
        put(chosen["panel"], (20, 20, 300, 380))
    for i, b in enumerate(("bar_health", "bar_mana")):
        if b in chosen:
            put(chosen[b], (340, 60 + i * 110, W - 360, 90))
            dr.text((340, 40 + i * 110), b, fill=(200, 190, 170), font=font)
    if "slot" in chosen:
        put(chosen["slot"], (340, 270, 130, 130))
        dr.text((480, 330), "slot", fill=(200, 190, 170), font=font)
    for i, n in enumerate(icons):
        x, y = 20 + (i % ncol) * C, 420 + (i // ncol) * (C + 24)
        if "slot" in chosen:
            put(chosen["slot"], (x + 5, y, C - 10, C - 10))
        put(chosen[n], (x + 30, y + 25, C - 60, C - 60))
        dr.text((x + 8, y + C - 6), n, fill=(200, 190, 170), font=font)
    sheet.save(os.path.join(OUT, "picks.jpg"), quality=92)
    print("picks", len(chosen), "of", len(picks), "->", PK, "and", os.path.join(OUT, "picks.jpg"))

    if EXPORT:
        SIZES = {"icon": 256, "panel": 1024, "slot": 256, "bar": 1024, "ring": 512, "ornament": 512, "texture": 512}
        SLICE = {"panel": [0.12, 0.12, 0.12, 0.12], "slot": [0.22, 0.22, 0.22, 0.22], "ornament": [0.25, 0.0, 0.25, 0.0],
                 "icon": [0, 0, 0, 0], "ring": [0, 0, 0, 0], "texture": [0, 0, 0, 0]}
        os.makedirs(EXPORT, exist_ok=True)
        layout = {}
        for name, im in chosen.items():
            e = EL[name]
            s = SIZES[e["kind"]] / max(im.size)
            im2 = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS) if s < 1 else im.copy()
            im2.save(os.path.join(EXPORT, name + ".png"))
            ent = {"kind": e["kind"], "size": list(im2.size), "border": e.get("slice", SLICE.get(e["kind"], [0, 0, 0, 0])),
                   "inner": [0.0, 0.0, 1.0, 1.0]}
            if e.get("holes"):
                al = np.asarray(im2)[..., 3] < 128
                lab, _ = ndimage.label(al)
                hx, hy = e["holes"][0]
                hl = lab[int(hy * (im2.height - 1)), int(hx * (im2.width - 1))]
                if hl:
                    ys, xs = np.nonzero(lab == hl)
                    ent["inner"] = [round(xs.min() / im2.width, 4), round(ys.min() / im2.height, 4),
                                    round((xs.max() + 1) / im2.width, 4), round((ys.max() + 1) / im2.height, 4)]
                else:
                    print("NO HOLE", name)
                if e["kind"] == "bar":
                    i0, i1 = ent["inner"][:2], ent["inner"][2:]
                    ent["border"] = [i0[0], i0[1], round(1 - i1[0], 4), round(1 - i1[1], 4)]
            layout[name] = ent
        layout["_icons"] = {k: v for k, v in D.get("icons", {}).items() if not k.startswith("_")}
        layout["_weapons"] = {k: v for k, v in D.get("weapons", {}).items() if not k.startswith("_")}
        json.dump(layout, open(os.path.join(EXPORT, "layout.json"), "w"), indent=1)
        print("exported", len(chosen), "pieces ->", EXPORT)
