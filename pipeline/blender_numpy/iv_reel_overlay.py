"""random_isometric_village_level demo reel HUD: composites a title, the village minimap (the same stylised isometric
miniature the game's HUD draws: ground, fields, roads, houses with their roofs, trees, market stalls; her arrow; the new
section fading in under a cyan tint as it is generated) and captions onto the MRQ frames.
The map is 784's recording (cine_demo_path.json: same fixed session seed). The generation time comes from the render's own
log line (last "IVGEN reveal": her tracked position there is looked up in the recording, which she follows on the sequence
clock); the section's counts come from the render's "IVSECTION (x,y) ..." line.
Usage: iv_reel_overlay.py frames_dir out_dir editor_log [step]"""
import sys, os, re, json, glob, bisect, math
from PIL import Image, ImageChops, ImageDraw, ImageFont
src, dst, log = sys.argv[1], sys.argv[2], sys.argv[3]
step = int(sys.argv[4]) if len(sys.argv) > 4 else 1
FPS = 30
R = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "random_isometric_village", "cine_demo_path.json")))
rows = R["rows"]; ts = [r[0] for r in rows]; SS = R["section_size"]
def her(t):
    t = min(max(t, ts[0]), ts[-1]); i = min(max(1, bisect.bisect_left(ts, t)), len(ts) - 1)
    a, b = rows[i - 1], rows[i]; u = 0 if ts[i] == ts[i - 1] else (t - ts[i - 1]) / (ts[i] - ts[i - 1])
    dy = (b[4] - a[4] + 180) % 360 - 180
    return a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u, a[4] + dy * u
# ---- the render's generation event and section stats
text = open(log, encoding="utf-8", errors="ignore").read()
rev = re.findall(r"IVGEN reveal \((-?\d+),(-?\d+)\) t=([\d.]+) from \((-?\d+),(-?\d+)\) tracked \((-?\d+),(-?\d+)\)", text)[-1]
NEW = (int(rev[0]), int(rev[1])); tx, ty = float(rev[5]), float(rev[6])
T_GEN = min(rows, key=lambda r: (r[1] - tx) ** 2 + (r[2] - ty) ** 2)[0]
st = re.findall(r"IVSECTION \(%d,%d\) seed -?\d+: (\d+) buildings, (\d+) vacant sites, (\d+) doors, (\d+) containers, (\d+) instances, (\d+) lights, (\d+) trees" % NEW, text)[-1]
nb, nv, nd, nc, ni, nl, nt = map(int, st)
_in = next((i for i, r in enumerate(rows) if r[6] >= 0), 0)
T_OUT = next((r[0] for r in rows[_in:] if r[6] < 0), 3.5)        # she steps out of her house (the cutaway closes)
print(f"generation of section {NEW} at sequence {T_GEN:.2f} s; {nb} buildings, {nd} doors, {nc} container parts, {nt} trees")
# ---- isometric projection (the game camera's)
yaw, pit = math.radians(R["iso_yaw"]), math.radians(abs(R["iso_pitch"]))
RX, RY, UX, UY, SN, CS = -math.sin(yaw), math.cos(yaw), math.cos(yaw), math.sin(yaw), math.sin(pit), math.cos(pit)
def proj(x, y, z=0.0): return (x * RX + y * RY, -((x * UX + y * UY) * SN + z * CS))
def srgb(c, k=1.0): return tuple(int(255 * min(1.0, max(0.0, v * k)) ** (1 / 2.2)) for v in c)
WALL = {"THATCH": (0.80, 0.74, 0.60), "TIMBER": (0.60, 0.44, 0.29), "STONE": (0.68, 0.68, 0.66)}
ROOF = {"THATCH": (0.84, 0.69, 0.31), "TIMBER": (0.50, 0.30, 0.19), "STONE": (0.42, 0.46, 0.55)}
PATCH = [(0.62, 0.60, 0.56), (0.76, 0.66, 0.30), (0.44, 0.36, 0.22), (0.45, 0.62, 0.30), (0.28, 0.48, 0.66), (0.33, 0.46, 0.28)]
ROADC = [(0.66, 0.56, 0.38), (0.74, 0.65, 0.46), (0.70, 0.60, 0.42), (0.62, 0.60, 0.56)]
GROUND, CYAN = (0.36, 0.50, 0.25), (0.43, 0.88, 1.0)
SECS = {tuple(m["coord"]): m for m in R["map"]}
SSAA = 2
def draw_map(size, center, scale, with_new, t):
    """the miniature around `center` (world x, y), `scale` px/cm, as an RGB image `size` (w, h)"""
    W, H = size[0] * SSAA, size[1] * SSAA; sc = scale * SSAA
    im = Image.new("RGB", (W, H), srgb((0.10, 0.13, 0.09))); d = ImageDraw.Draw(im)
    cx, cy = proj(center[0], center[1])
    def px(x, y, z=0.0):
        u, v = proj(x, y, z); return (W / 2 + (u - cx) * sc, H / 2 + (v - cy) * sc)
    reach = math.hypot(W, H) / 2 / sc / SN + 1500
    near = lambda x, y, pad=0: abs(x - center[0]) < reach + pad and abs(y - center[1]) < reach + pad
    secs = [m for c, m in SECS.items() if (with_new or c != NEW) and near(c[0] * SS, c[1] * SS, SS)]
    for m in secs:
        x0, y0 = (m["coord"][0] - 0.5) * SS, (m["coord"][1] - 0.5) * SS
        d.polygon([px(x0, y0), px(x0 + SS, y0), px(x0 + SS, y0 + SS), px(x0, y0 + SS)], fill=srgb(GROUND))
    for m in secs:
        for p in m["patches"]:
            if len(p["pts"]) >= 3 and near(*p["pts"][0], 6000): d.polygon([px(x, y) for x, y in p["pts"]], fill=srgb(PATCH[min(p["type"], 5)]))
    for outline in (True, False):
        for m in secs:
            for r in m["roads"]:
                if r["type"] == 3 or len(r["pts"]) < 2: continue
                hw = r["hw"] + (max(40.0, 1.2 * SSAA / sc) if outline else 0.0)
                col = srgb((0.30, 0.24, 0.15)) if outline else srgb(ROADC[min(r["type"], 3)])
                for (ax, ay), (bx, by) in zip(r["pts"], r["pts"][1:]):
                    if not (near(ax, ay, 500) or near(bx, by, 500)): continue
                    L = math.hypot(bx - ax, by - ay) or 1.0; nx, ny = -(by - ay) / L * hw, (bx - ax) / L * hw
                    d.polygon([px(ax + nx, ay + ny), px(bx + nx, by + ny), px(bx - nx, by - ny), px(ax - nx, ay - ny)], fill=col)
                    c0 = px(bx, by); rx, ry = hw * sc, hw * sc * SN
                    d.ellipse((c0[0] - rx, c0[1] - ry, c0[0] + rx, c0[1] + ry), fill=col)
    items = []
    for m in secs:
        for b in m["buildings"]:
            if near(*b["c"]): items.append((b["c"][0] * UX + b["c"][1] * UY, 0, b))
        for tr in m["trees"]:
            if near(tr[0], tr[1]): items.append((tr[0] * UX + tr[1] * UY, 1, tr))
        for p in m["props"]:
            if near(p[0], p[1]): items.append((p[0] * UX + p[1] * UY, 2, p))
    items.sort(key=lambda it: -it[0])
    tocam = (-UX, -UY)
    for _, kind, o in items:
        if kind == 0:
            b = o; yr = math.radians(b["yaw"]); fx, fy = (math.cos(yr), math.sin(yr)), (-math.sin(yr), math.cos(yr))
            hx, hy = b["half"]; Hh, Rh = b["wall"], b["roof"]; Cx, Cy = b["c"]
            wc = WALL[b["style"]]; rc = ROOF[b["style"]]
            if b["kind"] == "CHURCH": wc, rc = (0.74, 0.73, 0.70), (0.33, 0.40, 0.55)
            elif b["kind"] == "TAVERN": rc = (0.66, 0.26, 0.18)
            elif b["kind"] == "MANOR": rc = (0.55, 0.22, 0.26)
            pt = lambda X, Y, Z: px(Cx + fx[0] * X + fy[0] * Y, Cy + fx[1] * X + fy[1] * Y, Z)
            def wallq(n, a, c2, z0, z1):
                dn = n[0] * tocam[0] + n[1] * tocam[1]
                if dn <= 0.02: return
                k = 0.80 + 0.20 * max(0.0, n[0] * RX + n[1] * RY)
                d.polygon([pt(a[0], a[1], z0), pt(c2[0], c2[1], z0), pt(c2[0], c2[1], z1), pt(a[0], a[1], z1)], fill=srgb(wc, k))
            def box(x0, x1, y0, y1, z0, z1):
                wallq(fx, (x1, y0), (x1, y1), z0, z1); wallq((-fx[0], -fx[1]), (x0, y1), (x0, y0), z0, z1)
                wallq(fy, (x1, y1), (x0, y1), z0, z1); wallq((-fy[0], -fy[1]), (x0, y0), (x1, y0), z0, z1)
            box(-hx, hx, -hy, hy, 0, Hh)
            ax, cr = (fy, fx) if b["ridge_y"] else (fx, fy)
            la, lc = (hy, hx) if b["ridge_y"] else (hx, hy)
            rp = lambda al, ac, Z: px(Cx + ax[0] * al + cr[0] * ac, Cy + ax[1] * al + cr[1] * ac, Z)
            for e in (-1, 1):
                if (ax[0] * e * tocam[0] + ax[1] * e * tocam[1]) > 0.02:
                    d.polygon([rp(e * la, -lc, Hh), rp(e * la, lc, Hh), rp(e * la, 0, Hh + Rh)], fill=srgb(wc, 0.80 + 0.20 * max(0.0, (ax[0] * RX + ax[1] * RY) * e)))
            far = -1 if (cr[0] * tocam[0] + cr[1] * tocam[1]) > 0 else 1
            ov = 45.0
            for n, sd in enumerate((far, -far)):
                k = 0.78 + 0.30 * max(0.0, (cr[0] * RX + cr[1] * RY) * sd) + (0.06 if n else 0.0)
                d.polygon([rp(-la - ov, sd * (lc + ov), Hh - ov * 0.6), rp(la + ov, sd * (lc + ov), Hh - ov * 0.6), rp(la + ov, 0, Hh + Rh), rp(-la - ov, 0, Hh + Rh)], fill=srgb(rc, k))
            if b["tower"] > 0:
                s = hy; x1, x0 = hx, hx - 2 * hy
                box(x0, x1, -s, s, 0, b["tower"])
                apex = pt((x0 + x1) / 2, 0, b["tower"] + s * 2.2)
                cn = [pt(x0 - ov, -s - ov, b["tower"]), pt(x1 + ov, -s - ov, b["tower"]), pt(x1 + ov, s + ov, b["tower"]), pt(x0 - ov, s + ov, b["tower"])]
                ns = [(-fy[0], -fy[1]), fx, fy, (-fx[0], -fx[1])]
                for want in (False, True):
                    for i in range(4):
                        if ((ns[i][0] * tocam[0] + ns[i][1] * tocam[1]) > 0) == want:
                            d.polygon([cn[i], cn[(i + 1) % 4], apex], fill=srgb(rc, 0.8 + 0.3 * max(0.0, ns[i][0] * RX + ns[i][1] * RY)))
        elif kind == 1:
            x, y, rad, hgt, ty = o
            g = px(x - RX * rad * 0.25, y - RY * rad * 0.25); rr = rad * 0.95 * sc
            d.ellipse((g[0] - rr, g[1] - rr * SN, g[0] + rr, g[1] + rr * SN), fill=srgb((0.24, 0.36, 0.17)))
            if ty == 1:
                col = (0.16, 0.36, 0.22)
                d.polygon([px(x - RX * rad * 0.8, y - RY * rad * 0.8, hgt * 0.18), px(x + RX * rad * 0.8, y + RY * rad * 0.8, hgt * 0.18), px(x, y, hgt)], fill=srgb(col))
                d.polygon([px(x, y, hgt * 0.18), px(x + RX * rad * 0.8, y + RY * rad * 0.8, hgt * 0.18), px(x, y, hgt)], fill=srgb(col, 1.25))
            else:
                col = (0.42, 0.62, 0.24) if ty == 2 else (0.30, 0.50, 0.22) if ty == 3 else (0.22, 0.46, 0.20)
                zt = rad * 0.6 if ty == 3 else hgt * 0.62
                if ty != 3: d.polygon([px(x - RX * 18, y - RY * 18), px(x + RX * 18, y + RY * 18), px(x + RX * 18, y + RY * 18, zt), px(x - RX * 18, y - RY * 18, zt)], fill=srgb((0.33, 0.24, 0.15)))
                c0 = px(x, y, zt); rr = rad * sc
                d.ellipse((c0[0] - rr, c0[1] - rr, c0[0] + rr, c0[1] + rr), fill=srgb(col, 0.8))
                c1 = px(x + RX * rad * 0.22, y + RY * rad * 0.22, zt + rad * 0.28); rr *= 0.68
                d.ellipse((c1[0] - rr, c1[1] - rr, c1[0] + rr, c1[1] + rr), fill=srgb(col, 1.18))
        else:
            x, y, pyaw, ty = o; yr = math.radians(pyaw); fx, fy = (math.cos(yr), math.sin(yr)), (-math.sin(yr), math.cos(yr))
            q = lambda X, Y, Z=0.0: px(x + fx[0] * X + fy[0] * Y, y + fx[1] * X + fy[1] * Y, Z)
            if ty == 0:
                c0 = px(x, y, 60)
                for rad, col in ((130, (0.55, 0.55, 0.53)), (80, (0.16, 0.26, 0.36))): d.ellipse((c0[0] - rad * sc, c0[1] - rad * sc * SN, c0[0] + rad * sc, c0[1] + rad * sc * SN), fill=srgb(col))
            elif ty == 1:
                red = (round(x * 0.013 + y * 0.007) & 1) != 0
                d.polygon([q(-110, -160), q(110, -160), q(110, 160), q(-110, 160)], fill=srgb((0.42, 0.30, 0.19)))
                d.polygon([q(-130, -180, 240), q(130, -180, 200), q(130, 180, 200), q(-130, 180, 240)], fill=srgb((0.78, 0.22, 0.18) if red else (0.90, 0.84, 0.66)))
                d.polygon([q(-130, -60, 241), q(130, -60, 201), q(130, 60, 201), q(-130, 60, 241)], fill=srgb((0.92, 0.86, 0.70) if red else (0.30, 0.44, 0.66)))
            elif ty == 2: d.polygon([q(-120, -60, 70), q(120, -60, 70), q(120, 60, 70), q(-120, 60, 70)], fill=srgb((0.46, 0.31, 0.18)))
            elif ty == 3:
                c0 = px(x, y, 70); rr = 120 * sc; d.ellipse((c0[0] - rr, c0[1] - rr, c0[0] + rr, c0[1] + rr), fill=srgb((0.80, 0.68, 0.28)))
            elif ty == 4: d.polygon([px(x - RX * 30, y - RY * 30), px(x + RX * 30, y + RY * 30), px(x + RX * 30, y + RY * 30, 260), px(x - RX * 30, y - RY * 30, 260)], fill=srgb((0.70, 0.70, 0.68)))
            elif ty == 6: d.polygon([px(x - RX * 25, y - RY * 25), px(x + RX * 25, y + RY * 25), px(x + RX * 25, y + RY * 25, 85), px(x - RX * 25, y - RY * 25, 85)], fill=srgb((0.62, 0.63, 0.62)))
    # her arrow (over everything)
    hx_, hy_, hyaw = her(t); L = 8.0 * SSAA / sc; yr = math.radians(hyaw); f = (math.cos(yr), math.sin(yr)); rt = (-f[1], f[0])
    g = px(hx_, hy_); rr = L * 1.4 * sc
    tri = lambda k0, k1: [px(hx_ + f[0] * L * k0, hy_ + f[1] * L * k0, 40), px(hx_ - f[0] * L * k1 + rt[0] * L * k1, hy_ - f[1] * L * k1 + rt[1] * L * k1, 40),
                          px(hx_ - f[0] * L * k1 - rt[0] * L * k1, hy_ - f[1] * L * k1 - rt[1] * L * k1, 40)]
    d.polygon(tri(1.25, 0.85), fill=(255, 255, 255)); d.polygon(tri(0.95, 0.60), fill=srgb((1.0, 0.42, 0.66)))
    if with_new and NEW in SECS and 0 <= t - T_GEN < 5.0:
        x0, y0 = (NEW[0] - 0.5) * SS, (NEW[1] - 0.5) * SS; a = 1 - (t - T_GEN) / 5.0
        cn = [px(x0, y0), px(x0 + SS, y0), px(x0 + SS, y0 + SS), px(x0, y0 + SS)]
        d.line(cn + [cn[0]], fill=tuple(int(255 * (v * a + 0.3 * (1 - a)) ** (1 / 2.2)) for v in CYAN), width=3 * SSAA)
    return im.resize(size, Image.LANCZOS)
# ---- drawing
F = r"C:\Windows\Fonts"
def font(name, size):
    for n in (name, "segoeui.ttf", "arial.ttf"):
        try: return ImageFont.truetype(os.path.join(F, n), size)
        except OSError: pass
    return ImageFont.load_default()
f_title, f_sub, f_head, f_line, f_small = font("segoeuib.ttf", 40), font("segoeui.ttf", 24), font("seguisb.ttf", 30), font("segoeui.ttf", 24), font("seguisb.ttf", 19)
CY = tuple(int(255 * v ** (1 / 2.2)) for v in CYAN)
def fade(t, t0, t1, fin=0.35, fout=0.6):
    if t < t0 or t > t1: return 0.0
    return min(1.0, (t - t0) / fin, (t1 - t) / fout)
MW, MH = 384, 300
def overlay(t):
    W, H = 1920, 1080
    o = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(o)
    a = fade(t, 0.3, 5.2)
    if a > 0:
        d.text((44, 34), "random_isometric_village_level", font=f_title, fill=(255, 255, 255, int(235 * a)), stroke_width=2, stroke_fill=(0, 0, 0, int(140 * a)))
        d.text((46, 86), "procedural nucleated village  \u00b7  fixed isometric view  \u00b7  jrpg-fem5-tripo", font=f_sub, fill=(232, 236, 240, int(225 * a)), stroke_width=2, stroke_fill=(0, 0, 0, int(140 * a)))
    # minimap
    x0s, y0s = W - 44 - MW, 86
    d.rounded_rectangle((x0s - 14, 36, x0s + MW + 14, y0s + MH + 44), 14, fill=(14, 12, 9, 200))
    hx_, hy_, _ = her(t); scale = MW / 11500.0
    age = t - T_GEN
    mm = draw_map((MW, MH), (hx_, hy_), scale, age >= 0, t)
    if 0 <= age < 2.6:
        # the new part comes in under a cyan tint that clears over 2.6 s
        base = draw_map((MW, MH), (hx_, hy_), scale, False, t)
        tint = Image.blend(mm, Image.new("RGB", mm.size, CY), 0.6 * (1 - age / 2.6))
        mask = ImageChops.difference(mm, base).convert("L").point(lambda v: 255 if v > 6 else 0)      # where the new part shows
        mm = Image.composite(tint, mm, mask)
    o.paste(mm, (x0s, y0s))
    d.rectangle((x0s, y0s, x0s + MW, y0s + MH), outline=(200, 170, 110, 240), width=2)
    nbld = sum(len(m["buildings"]) for c, m in SECS.items() if c != NEW or age >= 0)
    d.text((x0s, 44), "VILLAGE", font=f_small, fill=(238, 228, 200, 240))
    d.text((x0s + MW, 44), f"{nbld} buildings", font=f_small, fill=(238, 228, 200, 240), anchor="ra")
    ly = y0s + MH + 10
    for i, (lab, col) in enumerate((("thatch", ROOF["THATCH"]), ("timber", ROOF["TIMBER"]), ("stone", ROOF["STONE"]), ("new part", CYAN))):
        xx = x0s + i * 98
        d.rectangle((xx, ly + 6, xx + 12, ly + 18), fill=srgb(col) + (255,)); d.text((xx + 18, ly), lab, font=f_small, fill=(214, 214, 208, 220))
    # captions (bottom left)
    def caption(a, head, lines, col=(255, 240, 214)):
        if a <= 0: return
        y = H - 62 - 36 - 34 * len(lines)
        d.rounded_rectangle((32, y - 14, 60 + max([d.textlength(head, font=f_head)] + [d.textlength(s, font=f_line) for s in lines]), H - 48), 12, fill=(12, 11, 9, int(180 * a)))
        d.text((50, y - 4), head, font=f_head, fill=col + (int(255 * a),))
        for i, s in enumerate(lines): d.text((54, y + 42 + 34 * i), s, font=f_line, fill=(240, 244, 248, int(240 * a)))
    caption(fade(t, 0.8, T_OUT + 0.5), "INSIDE A HOUSE", ["the roof and the camera-side walls are cut away", "doors, chests, wardrobes, barrels and crates open with F"])
    caption(fade(t, T_OUT + 1.2, min(T_OUT + 6.4, T_GEN - 0.3)), "8-DIRECTION MOVEMENT", ["W A S D or an Xbox controller  \u00b7  the view never turns"])
    caption(fade(t, T_GEN, T_GEN + 6.5), "\u25b2 NEW PART OF THE VILLAGE GENERATED",
            [f"section ({NEW[0]}, {NEW[1]})  \u00b7  250 m x 250 m  \u00b7  the same rings and lanes carried on", f"{nb} buildings  \u00b7  {nd} doors  \u00b7  {nc} container parts  \u00b7  {nt} trees"], CY)
    return o
os.makedirs(dst, exist_ok=True)
frames = sorted(glob.glob(os.path.join(src, "*.png")))
for i, p in enumerate(frames):
    if i % step: continue
    t = i / FPS
    im = Image.open(p).convert("RGBA")
    if im.size != (1920, 1080): im = im.resize((1920, 1080))
    Image.alpha_composite(im, overlay(t)).convert("RGB").save(os.path.join(dst, f"ivhud.{i:04d}.png"), compress_level=1)
print("wrote", len(range(0, len(frames), step)), "frames to", dst)
