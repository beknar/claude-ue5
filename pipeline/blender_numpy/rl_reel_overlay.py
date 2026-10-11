"""random_level demo reel HUD: composites a title, a town minimap (start square, ungenerated cells, cells as they are
generated with a wipe from the side she approaches, her position and the 70 m generation trigger range) and
"terrain generated" captions onto the MRQ frames.
Generation events are the last RTGEN reveal lines in the editor log (the render's); each is placed on the sequence clock
by matching its tracked position to her recorded path (755's cine_demo_path.json shifted by LAG, as in 756).
Usage: rl_reel_overlay.py frames_dir out_dir editor_log [lag] [step]"""
import sys, os, re, json, glob, bisect, math
from PIL import Image, ImageDraw, ImageFont
src, dst, log = sys.argv[1], sys.argv[2], sys.argv[3]
LAG = float(sys.argv[4]) if len(sys.argv) > 4 else 0.57
FPS, CELL, TRIGGER, START_BUILDINGS = 30, 25000.0, 7000.0, 151
R = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "random_level", "cine_demo_path.json")))
rows = R["rows"]; ts = [r[0] for r in rows]
def her(t):
    t = min(max(t + LAG, ts[0]), ts[-1]); i = min(max(1, bisect.bisect_left(ts, t)), len(ts) - 1)
    a, b = rows[i - 1], rows[i]; u = 0 if ts[i] == ts[i - 1] else (t - ts[i - 1]) / (ts[i] - ts[i - 1])
    return [a[j] + (b[j] - a[j]) * u for j in (1, 2, 4)]
# ---- events
pat = re.compile(r"RTGEN reveal \((-?\d+),(-?\d+)\) t=([\d.]+) from \((-?\d+),(-?\d+)\) tracked \((-?\d+),(-?\d+)\): (\d+) buildings, (\d+) instances")
lines = [m for m in (pat.search(l) for l in open(log, encoding="utf-8", errors="ignore")) if m]
ev = []
for m in lines[-5:]:
    cx, cy, wt, ox, oy, tx, ty, nb, ni = m.groups()
    ev.append({"cell": (int(cx), int(cy)), "wt": float(wt), "tracked": (float(tx), float(ty)), "origin": (float(ox), float(oy)), "buildings": int(nb), "instances": int(ni)})
# world time -> sequence time: offset (MRQ warm-up) from the events on her straight east leg, where position pins the time
offs = []
for e in ev:
    tx, ty = e["tracked"]
    if abs(ty - 20000) < 5 and tx < 19500:
        offs.append(e["wt"] - min((abs(her(k / 100.0)[0] - tx), k / 100.0) for k in range(0, 2001))[1])
off = sorted(offs)[len(offs) // 2] if offs else 32.0 / FPS
for e in ev: e["t"] = e["wt"] - off
ev.sort(key=lambda e: e["t"])
print("world->sequence offset %.3f s" % off)
print("events:", [(e["cell"], round(e["t"], 2)) for e in ev])
# caption groups: events within 1 s of each other
groups = []
for e in ev:
    if groups and e["t"] - groups[-1][-1]["t"] < 1.0: groups[-1].append(e)
    else: groups.append([e])
# ---- drawing
F = r"C:\Windows\Fonts"
def font(name, size):
    for n in (name, "segoeui.ttf", "arial.ttf"):
        try: return ImageFont.truetype(os.path.join(F, n), size)
        except OSError: pass
    return ImageFont.load_default()
f_title, f_sub, f_head, f_line, f_small = font("segoeuib.ttf", 40), font("segoeui.ttf", 24), font("seguisb.ttf", 30), font("segoeui.ttf", 24), font("seguisb.ttf", 19)
CYAN = (110, 225, 255)
def fade(t, t0, t1, fin=0.35, fout=0.6):
    if t < t0 or t > t1: return 0.0
    return min(1.0, (t - t0) / fin, (t1 - t) / fout)
def overlay(t):
    W, H = 1920, 1080
    o = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(o)
    # title (top left)
    a = fade(t, 0.2, 5.0)
    if a > 0:
        d.text((44, 34), "random_level", font=f_title, fill=(255, 255, 255, int(235 * a)))
        d.text((46, 86), "procedural medieval town  \u00b7  jrpg-fem5-tripo", font=f_sub, fill=(225, 230, 235, int(215 * a)))
    # minimap (top right): cells -2..2, X right, Y down (UE top view)
    cp, n = 52, 5; gx0 = W - 44 - cp * n; gy0 = 86; c0 = -2
    d.rounded_rectangle((gx0 - 16, 36, gx0 + cp * n + 16, gy0 + cp * n + 80), 14, fill=(12, 16, 22, 165))
    gen = [e for e in ev if e["t"] <= t]
    nb = START_BUILDINGS + sum(e["buildings"] for e in gen)
    d.text((gx0 - 2, 44), "TOWN", font=f_small, fill=(235, 240, 245, 230))
    d.text((gx0 + cp * n, 44), f"{4 + len(gen)} cells \u00b7 {nb} buildings", font=f_small, fill=(235, 240, 245, 230), anchor="ra")
    def cell_box(cx, cy): return (gx0 + (cx - c0) * cp, gy0 + (cy - c0) * cp, gx0 + (cx - c0 + 1) * cp, gy0 + (cy - c0 + 1) * cp)
    def to_px(x, y): return (gx0 + (x / CELL - c0) * cp, gy0 + (y / CELL - c0) * cp)
    for cx in range(c0, c0 + n):
        for cy in range(c0, c0 + n):
            b = cell_box(cx, cy)
            d.rectangle((b[0] + 1, b[1] + 1, b[2] - 1, b[3] - 1), fill=(26, 31, 38, 200), outline=(70, 80, 92, 220))
            if -1 <= cx <= 0 and -1 <= cy <= 0: d.rectangle((b[0] + 1, b[1] + 1, b[2] - 1, b[3] - 1), fill=(150, 128, 92, 225))
    for e in gen:
        age = t - e["t"]; b = cell_box(*e["cell"]); u = min(1.0, age / 2.3)
        ox, oy = to_px(*e["origin"])
        # wipe from the origin side
        x0, y0, x1, y1 = b[0] + 1, b[1] + 1, b[2] - 1, b[3] - 1
        if abs(ox - b[0]) < 1: x1 = x0 + (x1 - x0) * u
        elif abs(ox - b[2]) < 1: x0 = x1 - (x1 - x0) * u
        if abs(oy - b[1]) < 1: y1 = y0 + (y1 - y0) * u
        elif abs(oy - b[3]) < 1: y0 = y1 - (y1 - y0) * u
        fl = max(0.0, 1.0 - age / 1.6)
        col = tuple(int(c1 + (c2 - c1) * fl) for c1, c2 in zip((60, 150, 170), (150, 240, 255))) + (235,)
        d.rectangle((x0, y0, x1, y1), fill=col)
        if age < 3.0: d.rectangle((b[0] + 1, b[1] + 1, b[2] - 1, b[3] - 1), outline=CYAN + (int(255 * (1 - age / 3.0)),), width=3)
    d.rectangle(cell_box(-1, -1)[:2] + cell_box(0, 0)[2:], outline=(250, 225, 170, 235), width=2)
    hx, hy, yaw = her(t); px, py = to_px(hx, hy); r = TRIGGER / CELL * cp
    for k in range(0, 360, 20):
        a0 = math.radians(k); a1 = math.radians(k + 10)
        d.line((px + r * math.cos(a0), py + r * math.sin(a0), px + r * math.cos(a1), py + r * math.sin(a1)), fill=(255, 255, 255, 170), width=2)
    fx, fy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    d.polygon([(px + fx * 11, py + fy * 11), (px - fy * 6 - fx * 4, py + fx * 6 - fy * 4), (px + fy * 6 - fx * 4, py - fx * 6 - fy * 4)], fill=(255, 120, 170, 255))
    d.ellipse((px - 5, py - 5, px + 5, py + 5), fill=(255, 255, 255, 255), outline=(255, 120, 170, 255), width=2)
    lx, ly = gx0 - 2, gy0 + cp * n + 12
    d.rectangle((lx, ly + 6, lx + 12, ly + 18), fill=(150, 128, 92, 235)); d.text((lx + 18, ly), "start square", font=f_small, fill=(210, 215, 220, 210))
    d.rectangle((lx + 140, ly + 6, lx + 152, ly + 18), fill=(60, 150, 170, 235)); d.text((lx + 158, ly), "generated", font=f_small, fill=(210, 215, 220, 210))
    d.ellipse((lx, ly + 31, lx + 12, ly + 43), outline=(255, 255, 255, 190), width=2); d.text((lx + 18, ly + 25), "70 m generation trigger", font=f_small, fill=(210, 215, 220, 210))
    # captions (bottom left)
    for g in groups:
        t0, t1 = g[0]["t"], g[-1]["t"] + 3.6
        a = fade(t, t0, t1)
        if a <= 0: continue
        n_ = len(g); y = H - 60 - 40 - 34 * n_
        d.rounded_rectangle((32, y - 14, 640, H - 48), 12, fill=(10, 14, 20, int(170 * a)))
        d.text((50, y - 4), "\u25b2 TERRAIN GENERATED", font=f_head, fill=CYAN + (int(255 * a),))
        for i, e in enumerate(g):
            ai = a * min(1.0, max(0.0, (t - e["t"]) / 0.25))
            d.text((54, y + 42 + 34 * i), f"cell ({e['cell'][0]}, {e['cell'][1]})   {e['buildings']} buildings \u00b7 {e['instances']:,} props", font=f_line, fill=(240, 244, 248, int(240 * ai)))
    return o
os.makedirs(dst, exist_ok=True)
frames = sorted(glob.glob(os.path.join(src, "*.png")))
step = int(sys.argv[5]) if len(sys.argv) > 5 else 1          # (>1: a quick look at every step-th frame)
for i, p in enumerate(frames):
    if i % step: continue
    t = i / FPS
    im = Image.open(p).convert("RGBA")
    if im.size != (1920, 1080): im = im.resize((1920, 1080))
    Image.alpha_composite(im, overlay(t)).convert("RGB").save(os.path.join(dst, f"rlhud.{i:04d}.png"), compress_level=1)
print("wrote", len(frames), "frames to", dst)
