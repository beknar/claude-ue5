"""random_isometric_village_level demo reel HUD: composites onto the MRQ frames what the game's HUD draws in play, and
captions:
- the village minimap (the same stylised isometric miniature: ground, fields, roads, houses with their roofs, trees,
  market stalls, the villagers, her arrow, north; the new section fading in under a cyan tint as it is generated). It
  is drawn from where the camera looks, so it turns with the view;
- the big map (M) while she stands in the new part: the village around her with every building labelled, turning with
  the view as well;
- a key cap for each turn of the view (Q / E) and for the map (M), a title and captions.
Everything is the render's own: 787's recording of it (cine_render.json: her path, the villagers, when the new section
was built and what is in it, the map data) and 785's camera (cine_camera.json: view yaw per frame, turns, map window).
Usage: iv_reel_overlay.py frames_dir out_dir [step]"""
import sys, os, json, glob, math
from PIL import Image, ImageChops, ImageDraw, ImageFont
src, dst = sys.argv[1], sys.argv[2]
step = int(sys.argv[3]) if len(sys.argv) > 3 else 1
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "random_isometric_village")
R = json.load(open(os.path.join(SRC, "cine_render.json"))); CAM = json.load(open(os.path.join(SRC, "cine_camera.json")))
FPS = R["fps"]; rows = R["rows"]; SS = R["section_size"]; VSTEP = R["vill_step"]; VILL = R["vill"]
def her(f):
    r = rows[min(max(f, 0), len(rows) - 1)]; return r[1], r[2], r[4]
def villagers(f):
    """the villagers at frame f (sampled every VSTEP frames, linear in between)"""
    k = min(f // VSTEP, len(VILL) - 1); a = VILL[k]; b = VILL[min(k + 1, len(VILL) - 1)]; u = (f - k * VSTEP) / VSTEP
    out = []
    for i, p in enumerate(a):
        if p is None: continue
        q = b[i] if i < len(b) and b[i] is not None else p
        out.append((p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u))
    return out
# ---- the render's generation event and what the new section holds
EV = next(e for e in R["events"] if "built" in e)
NEW = tuple(EV["section"]); T_TRIG, T_GEN = EV["frame"] / FPS, EV["built"] / FPS
_in = next((i for i, r in enumerate(rows) if r[6] >= 0), 0)
T_OUT = next((r[0] for r in rows[_in:] if r[6] < 0), 6.0)         # she steps out of her house (the cutaway closes)
MAP0, MAP1 = CAM["map"]; TURNS = CAM["turns"]; TURN = CAM["turn_time"]
SECS = {tuple(m["coord"]): m for m in R["map"]}
print(f"section {NEW} triggered at {T_TRIG:.2f} s, built at {T_GEN:.2f} s: {EV['buildings']} buildings, {EV['doors']} doors, {EV['containers']} container parts, {EV['trees']} trees, "
      f"{EV['villagers']} villagers | out of her house at {T_OUT:.2f} s | map {MAP0:.2f}-{MAP1:.2f} s | turns {TURNS}")
# ---- isometric projection: the game camera's, at the yaw the view has in this frame
PIT = math.radians(abs(R["iso_pitch"])); SN, CS = math.sin(PIT), math.cos(PIT)
RX = RY = UX = UY = 0.0
def set_view(f):
    global RX, RY, UX, UY
    yaw = math.radians(R["iso_yaw"] + CAM["yaw_off"][min(max(f, 0), len(CAM["yaw_off"]) - 1)])
    RX, RY, UX, UY = -math.sin(yaw), math.cos(yaw), math.cos(yaw), math.sin(yaw)
def proj(x, y, z=0.0): return (x * RX + y * RY, -((x * UX + y * UY) * SN + z * CS))
def srgb(c, k=1.0): return tuple(int(255 * min(1.0, max(0.0, v * k)) ** (1 / 2.2)) for v in c)
WALL = {"THATCH": (0.80, 0.74, 0.60), "TIMBER": (0.60, 0.44, 0.29), "STONE": (0.68, 0.68, 0.66)}
ROOF = {"THATCH": (0.84, 0.69, 0.31), "TIMBER": (0.50, 0.30, 0.19), "STONE": (0.42, 0.46, 0.55)}
PATCH = [(0.62, 0.60, 0.56), (0.76, 0.66, 0.30), (0.44, 0.36, 0.22), (0.45, 0.62, 0.30), (0.28, 0.48, 0.66), (0.33, 0.46, 0.28)]
ROADC = [(0.66, 0.56, 0.38), (0.74, 0.65, 0.46), (0.70, 0.60, 0.42), (0.62, 0.60, 0.56)]
GROUND, CYAN, INK = (0.36, 0.50, 0.25), (0.43, 0.88, 1.0), (0.93, 0.89, 0.78)
KIND = {"COTTAGE": "Cottage", "FARMHOUSE": "Farmhouse", "TAVERN": "Tavern", "SMITHY": "Smithy", "BAKERY": "Bakery", "STORE": "General store", "WORKSHOP": "Carpenter", "BARN": "Barn",
        "STOREHOUSE": "Storehouse", "CHURCH": "Church", "MANOR": "Elder's hall"}
F = r"C:\Windows\Fonts"
def font(name, size):
    for n in (name, "segoeui.ttf", "arial.ttf"):
        try: return ImageFont.truetype(os.path.join(F, n), size)
        except OSError: pass
    return ImageFont.load_default()
f_title, f_sub, f_head, f_line, f_small = font("segoeuib.ttf", 40), font("segoeui.ttf", 24), font("seguisb.ttf", 30), font("segoeui.ttf", 24), font("seguisb.ttf", 19)
f_lab = [font("segoeuib.ttf", 19), font("seguisb.ttf", 16), font("segoeui.ttf", 14), font("segoeui.ttf", 14)]
f_key, f_map = font("segoeuib.ttf", 34), font("seguisb.ttf", 44)
SSAA = 2
def draw_map(size, center, scale, with_new, f, big=False):
    """the miniature around `center` (world x, y), `scale` px/cm, as an RGB image `size` (w, h); `big`: the M map
    (larger figures, every building labelled where there is room)"""
    t = f / FPS
    W, H = size[0] * SSAA, size[1] * SSAA; sc = scale * SSAA
    im = Image.new("RGB", (W, H), srgb((0.10, 0.13, 0.09))); d = ImageDraw.Draw(im, "RGBA")
    cx, cy = proj(center[0], center[1])
    def px(x, y, z=0.0):
        u, v = proj(x, y, z); return (W / 2 + (u - cx) * sc, H / 2 + (v - cy) * sc)
    reach = math.hypot(W, H) / 2 / sc / SN + 1500
    near = lambda x, y, pad=0: abs(x - center[0]) < reach + pad and abs(y - center[1]) < reach + pad
    def on_panel(x, y, pad):
        p = px(x, y); return -pad < p[0] < W + pad and -pad < p[1] < H + pad
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
            if on_panel(*b["c"], (math.hypot(*b["half"]) + b["wall"] + b["roof"] + b["tower"]) * sc): items.append((b["c"][0] * UX + b["c"][1] * UY, 0, b))
        for tr in m["trees"]:
            if on_panel(tr[0], tr[1], (tr[2] + tr[3]) * sc): items.append((tr[0] * UX + tr[1] * UY, 1, tr))
        for p in m["props"]:
            if on_panel(p[0], p[1], 400 * sc): items.append((p[0] * UX + p[1] * UY, 2, p))
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
            elif b["kind"] in ("BARN", "STOREHOUSE"): rc = tuple(v * 0.86 for v in rc)
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
    # villagers: small upright figures
    S = (4.6 if big else 3.4) * SSAA / sc
    for vx, vy in villagers(f):
        if not on_panel(vx, vy, 6 * SSAA): continue
        d.polygon([px(vx - RX * S * 0.75, vy - RY * S * 0.75), px(vx + RX * S * 0.75, vy + RY * S * 0.75), px(vx, vy, S * 2.9)], fill=srgb((0.20, 0.13, 0.09)))
        c0 = px(vx, vy, S * 3.0); rr = S * 0.62 * sc
        d.ellipse((c0[0] - rr, c0[1] - rr, c0[0] + rr, c0[1] + rr), fill=srgb((0.96, 0.80, 0.62)))
    # her: a ring on the ground and an arrow along her facing (over everything)
    hx_, hy_, hyaw = her(f); L = (11.0 if big else 8.0) * SSAA / sc; yr = math.radians(hyaw); fw = (math.cos(yr), math.sin(yr)); rt = (-fw[1], fw[0])
    g = px(hx_, hy_); rr = L * (1.25 + 0.25 * (0.5 + 0.5 * math.sin(t * 4.0))) * sc
    d.ellipse((g[0] - rr, g[1] - rr * SN, g[0] + rr, g[1] + rr * SN), fill=(255, 255, 255, 77))
    tri = lambda k0, k1, k2: [px(hx_ + fw[0] * L * k0, hy_ + fw[1] * L * k0, 40), px(hx_ - fw[0] * L * k1 + rt[0] * L * k2, hy_ - fw[1] * L * k1 + rt[1] * L * k2, 40),
                              px(hx_ - fw[0] * L * k1 - rt[0] * L * k2, hy_ - fw[1] * L * k1 - rt[1] * L * k2, 40)]
    d.polygon(tri(1.25, 0.85, 0.85), fill=(255, 255, 255)); d.polygon(tri(0.95, 0.60, 0.58), fill=srgb((1.0, 0.42, 0.66)))
    if with_new and NEW in SECS and 0 <= t - T_GEN < 5.0:
        x0, y0 = (NEW[0] - 0.5) * SS, (NEW[1] - 0.5) * SS; a = 1 - (t - T_GEN) / 5.0
        cn = [px(x0, y0), px(x0 + SS, y0), px(x0 + SS, y0 + SS), px(x0, y0 + SS)]
        d.line(cn + [cn[0]], fill=tuple(int(255 * (v * a + 0.3 * (1 - a)) ** (1 / 2.2)) for v in CYAN), width=3 * SSAA)
    im = im.resize(size, Image.LANCZOS)
    if big:
        # labels: landmarks first, then the houses wherever there is room
        d = ImageDraw.Draw(im, "RGBA"); labs = []
        for m in secs:
            for b in m["buildings"]:
                p = px(*b["c"]); p = (p[0] / SSAA, p[1] / SSAA)
                if not (12 < p[0] < size[0] - 12 and 12 < p[1] < size[1] - 12): continue
                pri = 0 if b["kind"] == "CHURCH" else 3 if b["kind"] in ("COTTAGE", "FARMHOUSE") else 2 if b["kind"] in ("BARN", "STOREHOUSE") else 1
                labs.append((pri, (b["c"][0] - hx_) ** 2 + (b["c"][1] - hy_) ** 2, b))
        labs.sort(key=lambda q: q[:2]); used = []
        for pri, _, b in labs:
            n = KIND.get(b["kind"], "House"); fn = f_lab[pri]
            tw = d.textlength(n, font=fn); th = fn.size + 3
            top = px(b["c"][0], b["c"][1], b["wall"] + b["roof"] + b["tower"] * 0.4); top = (top[0] / SSAA, top[1] / SSAA)
            x0, y0 = top[0] - tw / 2, top[1] - th - 3
            bx = (x0 - 4, y0 - 1, x0 + tw + 4, y0 + th + 1)
            if bx[0] < 0 or bx[2] > size[0] or bx[1] < 0 or bx[3] > size[1]: continue
            if any(bx[0] < u[2] and bx[2] > u[0] and bx[1] < u[3] and bx[3] > u[1] for u in used): continue
            used.append(bx)
            d.rectangle(bx, fill=(13, 13, 10, 158 if pri <= 1 else 107))
            d.text((x0, y0 - 1), n, font=fn, fill=srgb((1.0, 0.93, 0.62)) if pri == 0 else srgb((1.0, 0.97, 0.88)) if pri == 1 else srgb((0.86, 0.86, 0.80)))
    return im
# ---- drawing
CY = tuple(int(255 * v ** (1 / 2.2)) for v in CYAN)
def fade(t, t0, t1, fin=0.35, fout=0.6):
    if t < t0 or t > t1: return 0.0
    return min(1.0, (t - t0) / fin, (t1 - t) / fout)
MW, MH = 384, 300
W, H = 1920, 1080
NB = lambda with_new: sum(len(m["buildings"]) for c, m in SECS.items() if c != NEW or with_new)
def minimap(o, d, f):
    t = f / FPS
    x0s, y0s = W - 44 - MW, 86
    d.rounded_rectangle((x0s - 14, 36, x0s + MW + 14, y0s + MH + 44), 14, fill=(14, 12, 9, 200))
    hx_, hy_, _ = her(f); scale = MW / 11500.0
    age = t - T_GEN
    mm = draw_map((MW, MH), (hx_, hy_), scale, age >= 0, f)
    if 0 <= age < 2.6:
        # the new part comes in under a cyan tint that clears over 2.6 s
        base = draw_map((MW, MH), (hx_, hy_), scale, False, f)
        tint = Image.blend(mm, Image.new("RGB", mm.size, CY), 0.6 * (1 - age / 2.6))
        mask = ImageChops.difference(mm, base).convert("L").point(lambda v: 255 if v > 6 else 0)      # where the new part shows
        mm = Image.composite(tint, mm, mask)
    o.paste(mm, (x0s, y0s))
    d.rectangle((x0s, y0s, x0s + MW, y0s + MH), outline=(200, 170, 110, 240), width=2)
    d.text((x0s, 44), "VILLAGE", font=f_small, fill=(238, 228, 200, 240))
    d.text((x0s + MW, 44), f"{NB(age >= 0)} buildings", font=f_small, fill=(238, 228, 200, 240), anchor="ra")
    # north (+X): up-left in the view the level starts with
    nx, ny = proj(1, 0); nl = math.hypot(nx, ny) or 1.0; nx, ny = nx / nl, ny / nl
    ncx, ncy = x0s + 36, y0s + MH - 36
    d.line((ncx - nx * 10, ncy - ny * 10, ncx + nx * 13, ncy + ny * 13), fill=srgb(INK) + (255,), width=3)
    d.text((ncx + nx * 23, ncy + ny * 23), "N", font=f_small, fill=srgb(INK) + (255,), anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0, 150))
    ly = y0s + MH + 10
    for i, (lab, col) in enumerate((("thatch", ROOF["THATCH"]), ("timber", ROOF["TIMBER"]), ("stone", ROOF["STONE"]), ("new part", CYAN))):
        xx = x0s + i * 98
        d.rectangle((xx, ly + 6, xx + 12, ly + 18), fill=srgb(col) + (255,)); d.text((xx + 18, ly), lab, font=f_small, fill=(214, 214, 208, 220))
def bigmap(f, a):
    """the M map as a full-frame RGBA layer at opacity a"""
    o = Image.new("RGBA", (W, H), srgb((0.05, 0.045, 0.035)) + (230,)); d = ImageDraw.Draw(o)
    A0, A1 = (60, 104), (W - 60, H - 64)
    k = (A1[1] - A0[1]) / (240.0 * 100.0 * SN)
    hx_, hy_, _ = her(f)
    o.paste(draw_map((A1[0] - A0[0], A1[1] - A0[1]), (hx_, hy_), k, True, f, big=True), A0)
    d.rectangle((A0[0], A0[1], A1[0], A1[1]), outline=srgb((0.78, 0.66, 0.42)) + (242,), width=2)
    d.text((60, 26), "VILLAGE MAP", font=f_map, fill=srgb(INK) + (255,))
    nv = sum(1 for m in SECS.values() for b in m["buildings"] if b.get("visited"))
    d.text((62, 76), f"{NB(True)} buildings in {len(SECS)} parts of the village  \u00b7  {nv} entered  \u00b7  M  close  \u00b7  mouse wheel  zoom  \u00b7  Q / E  turn", font=f_small, fill=srgb((0.75, 0.72, 0.64)) + (255,))
    x = 62
    for lab, col in (("thatched", (0.84, 0.69, 0.31)), ("timber", (0.50, 0.30, 0.19)), ("stone", (0.42, 0.46, 0.55)), ("tavern", (0.66, 0.26, 0.18)), ("church", (0.33, 0.40, 0.55)), ("road", (0.70, 0.60, 0.42)),
                     ("field", (0.76, 0.66, 0.30))):
        d.rectangle((x, H - 40, x + 14, H - 26), fill=srgb(col) + (255,)); d.text((x + 20, H - 46), lab, font=f_small, fill=srgb((0.78, 0.75, 0.67)) + (255,))
        x += d.textlength(lab, font=f_small) + 48
    if a < 1.0: o.putalpha(o.getchannel("A").point(lambda v: int(v * a)))
    return o
def keycap(d, a, key, text, y=H - 126):
    """a key cap and what it does, bottom right"""
    if a <= 0: return
    tw = d.textlength(text, font=f_line); kw = 64; wd = kw + 18 + tw; x = W - 66 - wd
    d.rounded_rectangle((x - 22, y - 14, x + wd + 22, y + 78), 14, fill=(12, 11, 9, int(190 * a)))
    d.rounded_rectangle((x, y, x + kw, y + 64), 10, fill=(238, 232, 214, int(255 * a)), outline=(120, 110, 90, int(255 * a)), width=3)
    d.text((x + kw / 2, y + 30), key, font=f_key, fill=(30, 26, 20, int(255 * a)), anchor="mm")
    d.text((x + kw + 18, y + 32), text, font=f_line, fill=(244, 240, 228, int(255 * a)), anchor="lm")
def overlay(f):
    t = f / FPS
    set_view(f)
    o = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(o)
    am = fade(t, MAP0, MAP1, 0.15, 0.15)
    if am < 1.0:
        a = fade(t, 0.3, 5.2)
        if a > 0:
            d.text((44, 34), "random_isometric_village_level", font=f_title, fill=(255, 255, 255, int(235 * a)), stroke_width=2, stroke_fill=(0, 0, 0, int(140 * a)))
            d.text((46, 86), "procedural nucleated village  \u00b7  isometric view that turns  \u00b7  jrpg-fem5-tripo", font=f_sub, fill=(232, 236, 240, int(225 * a)), stroke_width=2, stroke_fill=(0, 0, 0, int(140 * a)))
        minimap(o, d, f)
        # captions (bottom left)
        def caption(a, head, lines, col=(255, 240, 214)):
            if a <= 0: return
            y = H - 62 - 36 - 34 * len(lines)
            d.rounded_rectangle((32, y - 14, 60 + max([d.textlength(head, font=f_head)] + [d.textlength(s, font=f_line) for s in lines]), H - 48), 12, fill=(12, 11, 9, int(180 * a)))
            d.text((50, y - 4), head, font=f_head, fill=col + (int(255 * a),))
            for i, s in enumerate(lines): d.text((54, y + 42 + 34 * i), s, font=f_line, fill=(240, 244, 248, int(240 * a)))
        t1 = TURNS[0][0]
        caption(fade(t, 0.7, t1 - 0.25), "VILLAGERS", ["unarmed townsfolk wander every part of the village", f"three for every ten buildings  \u00b7  {SECS[(0, 0)]['villagers']} in this part"])
        caption(fade(t, t1 - 0.1, T_OUT + 0.4), "INSIDE A HOUSE", ["the roof and the walls that face the camera are cut away,", "whichever way the view is turned  \u00b7  doors and containers open with F"])
        caption(fade(t, T_OUT + 0.9, T_GEN - 0.3), "8-DIRECTION MOVEMENT", ["W A S D or an Xbox controller  \u00b7  Q / E (LB / RB) turn the view in 45\u00b0 steps"])
        caption(fade(t, T_GEN, min(T_GEN + 6.8, MAP0 - 0.4)), "\u25b2 NEW PART OF THE VILLAGE GENERATED",
                [f"section ({NEW[0]}, {NEW[1]})  \u00b7  250 m x 250 m  \u00b7  the same rings and lanes carried on",
                 f"{EV['buildings']} buildings  \u00b7  {EV['doors']} doors  \u00b7  {EV['containers']} container parts  \u00b7  {EV['trees']} trees  \u00b7  {EV['villagers']} villagers"], CY)
        caption(fade(t, MAP1 + 0.5, 29.6), "THE VILLAGE GOES ON", ["every 250 m square is generated as she nears it,", "from the same plan of rings, lanes and main roads"])
        for t0, n in TURNS:
            if not (MAP0 - 0.5 < t0 < MAP1): keycap(d, fade(t, t0 - 0.2, t0 + 1.1, 0.12, 0.4), "Q" if n > 0 else "E", "turn the view left" if n > 0 else "turn the view right")
        keycap(d, fade(t, MAP0 - 0.7, MAP0 + 0.1, 0.12, 0.15), "M", "village map")
    if am > 0:
        o = Image.alpha_composite(o, bigmap(f, am)); d = ImageDraw.Draw(o)
        for t0, n in TURNS:
            if MAP0 - 0.5 < t0 < MAP1: keycap(d, fade(t, t0 - 0.2, t0 + 1.1, 0.12, 0.4), "Q" if n > 0 else "E", "turn the view left" if n > 0 else "turn the view right", H - 190)
        keycap(d, fade(t, MAP1 - 0.6, MAP1 + 0.1, 0.12, 0.15), "M", "close the map", H - 190)
    return o
os.makedirs(dst, exist_ok=True)
frames = sorted(glob.glob(os.path.join(src, "*.png")))
for i, p in enumerate(frames):
    if i % step: continue
    im = Image.open(p).convert("RGBA")
    if im.size != (W, H): im = im.resize((W, H))
    Image.alpha_composite(im, overlay(i)).convert("RGB").save(os.path.join(dst, f"ivhud.{i:04d}.png"), compress_level=1)
print("wrote", len(range(0, len(frames), step)), "frames to", dst)
