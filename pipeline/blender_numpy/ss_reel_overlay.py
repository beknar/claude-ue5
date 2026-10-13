"""starship_level demo reel HUD: composites onto the Movie Render Queue frames (the queue does not draw the game's HUD)
- what the game's HUD shows in the chase view: the nose crosshair, the mouse's aim point, brackets with name and range
  on the locked target and its lead mark, markers on the target drones, speed / throttle / missiles and the score;
- what the pilot's hands do: the keys held (W A S D, Shift), the mouse buttons, where the mouse has put the aim point
  and how fast the nose is turning;
- a title, a caption for each part of the flight and a line for every target destroyed.
Everything is the render's own: 805's recording of it (SourceArt/starship/cine_render.json: the fighter, the camera,
the inputs, the locked target and the drones for every frame, and the events). The HUD is hidden in the fly-by shots.
Usage: ss_reel_overlay.py frames_dir out_dir [step]"""
import sys, os, json, glob, math
from PIL import Image, ImageDraw, ImageFont
src, dst = sys.argv[1], sys.argv[2]
step = int(sys.argv[3]) if len(sys.argv) > 3 else 1
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "starship")
R = json.load(open(os.path.join(SRC, "cine_render.json")))
FPS = R["fps"]; ROWS = {r["frame"]: r for r in R["rows"]}; LASTF = max(ROWS); C = R["const"]
SEG = {s["name"]: s["t"] for s in R["segs"]}; EV = R["events"]
KILLS = [e for e in EV if e["kind"] == "kill"]; VIEWS = [e for e in EV if e["kind"] == "view"]
W, H, K = 1920, 1080, 2                       # the layer is drawn K times larger and scaled down (smooth lines)
def row(f): return ROWS.get(min(max(f, 0), LASTF)) or ROWS[min(ROWS, key=lambda k: abs(k - f))]
print("frames %d | parts %s | %d asteroids, %d drones destroyed | views %s" % (len(ROWS), " ".join("%s@%.1f" % (k, v) for k, v in SEG.items()), sum(1 for e in KILLS if e["what"] == "asteroid"),
      sum(1 for e in KILLS if e["what"] == "drone"), " ".join("%s@%.1f" % (e["view"], e["t"]) for e in VIEWS)))
GREEN, AMBER, RED, INK, BLUE = (110, 255, 160), (255, 196, 70), (255, 92, 70), (232, 240, 250), (120, 196, 255)
F = r"C:\Windows\Fonts"
def font(name, size):
    for n in (name, "segoeui.ttf", "arial.ttf"):
        try: return ImageFont.truetype(os.path.join(F, n), int(size * K))
        except OSError: pass
    return ImageFont.load_default()
f_title, f_sub, f_head, f_line, f_small, f_tiny, f_key, f_score = (font("segoeuib.ttf", 40), font("segoeui.ttf", 24), font("seguisb.ttf", 30), font("segoeui.ttf", 24), font("seguisb.ttf", 18),
                                                                 font("seguisb.ttf", 15), font("segoeuib.ttf", 20), font("segoeuib.ttf", 30))
def axes(r):
    p, y, ro = (math.radians(v) for v in r); cp, sp, cy, sy, cr, sr = math.cos(p), math.sin(p), math.cos(y), math.sin(y), math.cos(ro), math.sin(ro)
    return (cp * cy, cp * sy, sp), (sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp), (-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def add(a, b, k=1.0): return (a[0] + b[0] * k, a[1] + b[1] * k, a[2] + b[2] * k)
def project(r, P):
    """screen position (layer pixels) of world point P in this frame, or None when it is behind the camera"""
    fw, rt, up = axes(r["cr"]); d = add(P, r["cp"], -1.0); z = dot(d, fw)
    if z <= 1.0: return None
    foc = (W * K / 2) / math.tan(math.radians(r["fov"]) / 2)
    return (W * K / 2 + dot(d, rt) / z * foc, H * K / 2 - dot(d, up) / z * foc, foc / z)
def fade(t, t0, t1, fin=0.35, fout=0.5):
    if t < t0 or t > t1: return 0.0
    return min(1.0, (t - t0) / fin, (t1 - t) / fout)
def col(c, a): return c + (int(255 * max(0.0, min(1.0, a))),)
def hud_alpha(t):
    """the game HUD shows in the chase view: it comes up when the camera has come round behind the fighter and after
    each fly-by shot, and is gone during them"""
    v = "orbit"; t0 = 0.0
    for e in VIEWS:
        if e["t"] <= t: v, t0 = e["view"], e["t"]
    if v != "chase": return 0.0
    end = SEG.get("end", 1e9)
    return min(1.0, (t - t0) / 0.3) * (1.0 - min(1.0, max(0.0, (t - end) / 0.5)))
def line(d, pts, c, w): d.line([(x, y) for x, y in pts], fill=c, width=int(w * K))
def bracket(d, x, y, h, c, w=2.5):
    L = max(8 * K, h * 0.42)
    for sx in (-1, 1):
        for sy in (-1, 1):
            line(d, [(x + sx * h, y + sy * (h - L)), (x + sx * h, y + sy * h), (x + sx * (h - L), y + sy * h)], c, w)
def bar(d, x, y, w, h, frac, c, label, value, a):
    d.text((x, y - 24 * K), label, font=f_small, fill=col(INK, a)); d.text((x + w, y - 24 * K), value, font=f_small, fill=col(INK, a), anchor="ra")
    d.rectangle((x, y, x + w, y + h), fill=(8, 14, 20, int(150 * a)), outline=col(c, 0.55 * a), width=K)
    d.rectangle((x + 2 * K, y + 2 * K, x + 2 * K + (w - 4 * K) * max(0.0, min(1.0, frac)), y + h - 2 * K), fill=col(c, 0.9 * a))
def keycap(d, x, y, w, h, label, on, a=1.0):
    d.rounded_rectangle((x, y, x + w, y + h), 7 * K, fill=col(GREEN, 0.95 * a) if on else (14, 20, 26, int(170 * a)), outline=col(GREEN if on else (150, 160, 172), a), width=2 * K)
    d.text((x + w / 2, y + h / 2 - K), label, font=f_key, fill=(10, 24, 16, int(255 * a)) if on else col((200, 208, 218), a), anchor="mm")
def hands(d, r, a):
    """bottom right: the keys held, the mouse buttons, where the mouse has put the aim point, and the turn rate"""
    if a <= 0: return
    x0, y0 = (W - 46 - 372) * K, (H - 46 - 170) * K; k = K
    d.rounded_rectangle((x0 - 14 * k, y0 - 40 * k, x0 + 386 * k, y0 + 170 * k), 12 * k, fill=(8, 12, 18, int(150 * a)))
    d.text((x0, y0 - 32 * k), "KEYBOARD + MOUSE", font=f_small, fill=col(INK, 0.9 * a))
    w_, s_, a_, d_, sh, lmb, rmb = r["in"][:7]
    keycap(d, x0 + 50 * k, y0, 44 * k, 44 * k, "W", w_, a); keycap(d, x0, y0 + 50 * k, 44 * k, 44 * k, "A", a_, a); keycap(d, x0 + 50 * k, y0 + 50 * k, 44 * k, 44 * k, "S", s_, a)
    keycap(d, x0 + 100 * k, y0 + 50 * k, 44 * k, 44 * k, "D", d_, a); keycap(d, x0, y0 + 100 * k, 144 * k, 44 * k, "SHIFT", sh, a)
    # the mouse: a body with its two buttons
    mx, my = x0 + 168 * k, y0
    d.rounded_rectangle((mx, my, mx + 76 * k, my + 144 * k), 30 * k, fill=(14, 20, 26, int(170 * a)), outline=col((150, 160, 172), a), width=2 * k)
    for i, on in enumerate((lmb, rmb)):
        d.pieslice((mx + 2 * k, my + 2 * k, mx + 74 * k, my + 122 * k), 180 + 90 * i, 270 + 90 * i, fill=col(AMBER if i else GREEN, 0.95 * a) if on else (30, 38, 46, int(200 * a)), outline=col((150, 160, 172), a), width=k)
    d.line((mx + 38 * k, my + 2 * k, mx + 38 * k, my + 62 * k), fill=col((150, 160, 172), a), width=2 * k)
    d.line((mx + 2 * k, my + 62 * k, mx + 74 * k, my + 62 * k), fill=col((150, 160, 172), a), width=2 * k)
    # the aim point the mouse has moved, in the circle it is held in; the nose chases it
    cx, cy, rad = x0 + 318 * k, y0 + 56 * k, 52 * k
    d.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=(10, 16, 22, int(160 * a)), outline=col(GREEN, 0.7 * a), width=2 * k)
    d.line((cx - rad, cy, cx + rad, cy), fill=col(GREEN, 0.25 * a), width=k); d.line((cx, cy - rad, cx, cy + rad), fill=col(GREEN, 0.25 * a), width=k)
    ax, ay = r["aim"][0] / C["max_aim"] * rad, -r["aim"][1] / C["max_aim"] * rad
    d.line((cx, cy, cx + ax, cy + ay), fill=col(INK, 0.6 * a), width=2 * k)
    d.ellipse((cx + ax - 7 * k, cy + ay - 7 * k, cx + ax + 7 * k, cy + ay + 7 * k), fill=col(INK, a))
    turn = math.hypot(*r["rate"])
    d.text((cx, y0 + 118 * k), "TURN", font=f_tiny, fill=col(INK, 0.75 * a), anchor="mm")
    d.text((cx, y0 + 142 * k), "%3.0f\u00b0/s" % turn, font=f_key, fill=col(AMBER if turn > max(C["stick_rates"]) else INK, a), anchor="mm")
def game_hud(d, r, a, t):
    if a <= 0: return
    fw, rt, up = axes(r["r"])
    # ---- the nose (where the cannons fire) and the aim point the nose is chasing
    n = project(r, add(r["p"], fw, C["convergence"]))
    if n:
        g, e = 7 * K, 22 * K
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)): line(d, [(n[0] + dx * g, n[1] + dy * g), (n[0] + dx * e, n[1] + dy * e)], col(GREEN, a), 2.5)
        d.rectangle((n[0] - 2 * K, n[1] - 2 * K, n[0] + 2 * K, n[1] + 2 * K), fill=col(GREEN, a))
        if math.hypot(*r["aim"]) > 0.25:
            ya, pa = math.radians(r["aim"][0]), math.radians(r["aim"][1]); l = (math.cos(pa) * math.cos(ya), math.cos(pa) * math.sin(ya), math.sin(pa))
            w_ = tuple(fw[i] * l[0] + rt[i] * l[1] + up[i] * l[2] for i in range(3)); q = project(r, add(r["p"], w_, C["convergence"]))
            if q:
                line(d, [(n[0], n[1]), (q[0], q[1])], col(INK, 0.3 * a), 1.5)
                d.ellipse((q[0] - 16 * K, q[1] - 16 * K, q[0] + 16 * K, q[1] + 16 * K), outline=col(INK, 0.9 * a), width=2 * K)
    # ---- the target drones in view, and the locked target
    lk = r["lock"]
    for p in r["dr"]:
        if lk and math.dist(p, lk["p"]) < 50.0: continue
        q = project(r, p)
        if q and 0 < q[0] < W * K and 0 < q[1] < H * K:
            s = 9 * K; d.polygon([(q[0], q[1] - s), (q[0] + s, q[1]), (q[0], q[1] + s), (q[0] - s, q[1])], outline=col(RED, 0.9 * a), width=2 * K)
    if lk:
        q = project(r, lk["p"])
        if q and -200 < q[0] < W * K + 200 and -200 < q[1] < H * K + 200:
            h = max(20 * K, lk["rad"] * q[2] * 1.25); dist = math.dist(lk["p"], r["p"]) / 100.0
            bracket(d, q[0], q[1], h, col(AMBER, a))
            d.text((q[0], q[1] - h - 8 * K), str(lk["name"]).upper(), font=f_small, fill=col(AMBER, a), anchor="mb", stroke_width=K, stroke_fill=(0, 0, 0, int(150 * a)))
            d.text((q[0] + h + 8 * K, q[1]), "%.0f m" % dist, font=f_small, fill=col(AMBER, a), anchor="lm", stroke_width=K, stroke_fill=(0, 0, 0, int(150 * a)))
            if lk.get("hp") is not None:
                d.rectangle((q[0] - h, q[1] + h + 7 * K, q[0] + h, q[1] + h + 12 * K), outline=col(AMBER, 0.6 * a), width=K)
                d.rectangle((q[0] - h, q[1] + h + 7 * K, q[0] - h + 2 * h * max(0.0, min(1.0, lk["hp"])), q[1] + h + 12 * K), fill=col(AMBER, 0.9 * a))
            m = project(r, lk["lead"])
            if m and math.hypot(m[0] - q[0], m[1] - q[1]) > 10 * K:
                line(d, [(m[0] - 7 * K, m[1]), (m[0] + 7 * K, m[1])], col(AMBER, a), 2.5); line(d, [(m[0], m[1] - 7 * K), (m[0], m[1] + 7 * K)], col(AMBER, a), 2.5)
    # ---- flight (bottom middle-right, beside the hands): speed, throttle, missiles
    x, w_ = (W - 46 - 372 - 40 - 250) * K, 250 * K; y = (H - 46 - 124) * K
    d.rounded_rectangle((x - 14 * K, y - 36 * K, x + w_ + 14 * K, y + 124 * K), 12 * K, fill=(8, 12, 18, int(150 * a)))
    bar(d, x, y, w_, 12 * K, r["sp"] / C["boost_speed"], AMBER if r["bo"] else GREEN, "SPEED  AFTERBURNER" if r["bo"] else "SPEED", "%.0f m/s" % (r["sp"] / 100.0), a)
    bar(d, x, y + 48 * K, w_, 12 * K, r["th"], BLUE, "THROTTLE", "%.0f %%" % (r["th"] * 100.0), a)
    d.text((x, y + 80 * K), "MISSILES", font=f_small, fill=col(INK, a))
    for i in range(C["rails"]):
        px = x + (100 + i * 26) * K
        d.rectangle((px, y + 84 * K, px + 18 * K, y + 98 * K), fill=col(AMBER, (0.95 if i < r["mis"] else 0.2) * a))
    # ---- the score (top left), and a line for what was just destroyed
    d.text((46 * K, 30 * K), "SCORE  %d" % r["sc"], font=f_score, fill=col(INK, a), stroke_width=K, stroke_fill=(0, 0, 0, int(140 * a)))
    d.text((48 * K, 74 * K), "asteroids %d   \u00b7   drones %d   \u00b7   cannons %d fired, %d hits   \u00b7   missiles %d fired" % (r["ad"], r["dd"], r["sf"], r["sh"], r["mf"]), font=f_small,
           fill=col(INK, 0.85 * a), stroke_width=K, stroke_fill=(0, 0, 0, int(140 * a)))
    y = 106
    for e in KILLS:
        k = fade(t, e["t"], e["t"] + 1.8, 0.1, 0.6)
        if k > 0:
            s = ("DRONE DESTROYED  \u00b7  %s  \u00b7  %d missile%s" % (e["name"].upper(), e["missiles"], "" if e["missiles"] == 1 else "s")) if e["what"] == "drone" else \
                ("ASTEROID DESTROYED  \u00b7  %.0f m across  \u00b7  %d bolts" % (e["radius_m"] * 2, e["shots"]))
            d.text((48 * K, y * K), s, font=f_small, fill=col(AMBER, k * a), stroke_width=K, stroke_fill=(0, 0, 0, int(140 * k * a))); y += 26
T_GATES, T_CANNON, T_MISS, T_STATION = SEG.get("gates", 2.5), SEG.get("cannons", 6.5), SEG.get("missiles", 13.6), SEG.get("station", 21.6)
T_END = SEG.get("end", 27.2); LAST_T = (LASTF + 1) / FPS
CAPTIONS = [
    (0.5, T_GATES + 0.5, "MOUSE FLIGHT", ["the mouse points the nose  \u00b7  W / S throttle  \u00b7  A / D roll  \u00b7  Shift afterburner"], INK),
    (T_GATES + 0.8, T_CANNON - 0.1, "THE GATE COURSE", ["six ring tunnels, each pointing at the next  \u00b7  flown by mouse:",
                                                     "the nose turns at up to %.0f\u00b0 a second (%.0f\u00b0 on the stick)" % (max(C["mouse_rates"]), max(C["stick_rates"]))], INK),
    (T_CANNON + 0.2, T_MISS - 0.1, "CANNONS", ["left mouse button  \u00b7  asteroids break up and can be destroyed"], GREEN),
    (T_MISS + 0.2, T_STATION - 0.1, "HOMING MISSILES", ["right mouse button  \u00b7  they lock on to the target nearest the nose", "target drones fly patrol circles and are replaced in waves"], AMBER),
    (T_STATION + 0.2, T_END - 0.1, "THE STATION", ["the middle of a 5 km x 5 km x 5 km combat area", "built from Mega_City and Red_Echo modules"], INK),
    (T_END + 0.2, LAST_T - 0.15, "KEYBOARD + MOUSE, OR AN XBOX CONTROLLER", ["left stick throttle and roll  \u00b7  right stick nose  \u00b7  RT cannons  \u00b7  LT missile"], INK),
]
def overlay(f):
    r = row(f); t = f / FPS
    o = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0)); d = ImageDraw.Draw(o)
    a = fade(t, 0.3, min(4.6, T_GATES + 1.6))
    if a > 0:
        d.text((44 * K, 34 * K), "starship_level", font=f_title, fill=(255, 255, 255, int(235 * a)), stroke_width=2 * K, stroke_fill=(0, 0, 0, int(140 * a)))
        d.text((46 * K, 86 * K), "space fighter kitbashed from pack meshes  \u00b7  cannons and homing missiles  \u00b7  chase camera", font=f_sub, fill=(232, 236, 240, int(225 * a)), stroke_width=2 * K,
               stroke_fill=(0, 0, 0, int(140 * a)))
    game_hud(d, r, hud_alpha(t) * (1.0 - a), t)
    hands(d, r, fade(t, 0.4, LAST_T - 0.1, 0.4, 0.3))
    for t0, t1, head, lines, c in CAPTIONS:
        k = fade(t, t0, t1)
        if k <= 0: continue
        y = (H - 62 - 36 - 34 * len(lines)) * K
        wd = max([d.textlength(head, font=f_head)] + [d.textlength(s, font=f_line) for s in lines])
        d.rounded_rectangle((32 * K, y - 14 * K, 60 * K + wd, (H - 48) * K), 12 * K, fill=(8, 12, 18, int(175 * k)))
        d.text((50 * K, y - 4 * K), head, font=f_head, fill=col(c, k))
        for i, s in enumerate(lines): d.text((54 * K, y + (42 + 34 * i) * K), s, font=f_line, fill=(240, 244, 248, int(240 * k)))
    return o.resize((W, H), Image.LANCZOS)
os.makedirs(dst, exist_ok=True)
frames = sorted(glob.glob(os.path.join(src, "*.png")))
for i, p in enumerate(frames):
    if i % step: continue
    im = Image.open(p).convert("RGBA")
    if im.size != (W, H): im = im.resize((W, H), Image.LANCZOS)
    Image.alpha_composite(im, overlay(i)).convert("RGB").save(os.path.join(dst, f"sshud.{i:04d}.png"), compress_level=1)
print("wrote", len(range(0, len(frames), step)), "frames to", dst)
