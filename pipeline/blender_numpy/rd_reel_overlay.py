"""random_dungeon_level demo reel HUD: composites a title, a dungeon minimap (north-up like the in-game HUD: generated rooms
dim, rooms she has been in lit, her arrow; a new section wipes in from the border she approaches with a cyan flash) and a
"new dungeon section generated" caption onto the MRQ frames.
The map is 774's recording (cine_demo_path.json: same fixed session seed). The generation time comes from the render's own
log line (last "RDGEN reveal"): she runs east at a constant speed, so her tracked x gives the sequence time; the section's
counts come from the render's "RDSECTION (x,y) ... monsters" line.
Usage: rd_reel_overlay.py frames_dir out_dir editor_log [step]"""
import sys, os, re, json, glob, bisect, math, statistics
from PIL import Image, ImageDraw, ImageFont
src, dst, log = sys.argv[1], sys.argv[2], sys.argv[3]
step = int(sys.argv[4]) if len(sys.argv) > 4 else 1
FPS, RUN, X0, GO = 30, 376.7, 7300.0, 0.3
R = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "random_dungeon", "cine_demo_path.json")))
TS, NT = R["tile"], R["section_tiles"]
rows = R["rows"]; ts = [r[0] for r in rows]
LAG = statistics.median(r[0] - (GO + (r[1] - X0) / RUN) for r in rows if r[5] > 360 and 8000 < r[1] < 12000)
def her(t):
    t = min(max(t + LAG, ts[0]), ts[-1]); i = min(max(1, bisect.bisect_left(ts, t)), len(ts) - 1)
    a, b = rows[i - 1], rows[i]; u = 0 if ts[i] == ts[i - 1] else (t - ts[i - 1]) / (ts[i] - ts[i - 1])
    return [a[j] + (b[j] - a[j]) * u for j in (1, 2, 4)]
# ---- the render's generation event and section stats
text = open(log, encoding="utf-8", errors="ignore").read()
rev = re.findall(r"RDGEN reveal \((-?\d+),(-?\d+)\) t=([\d.]+) from \((-?\d+),(-?\d+)\) tracked \((-?\d+),(-?\d+)\)", text)[-1]
sx, sy, wt, ox, oy, tx, ty = rev
T_GEN = GO + (float(tx) - X0) / RUN
st = re.findall(r"RDSECTION \(%s,%s\) seed -?\d+: (\d+) rooms, (\d+) hallways, (\d+) doors, (\d+) containers, (\d+) instances, (\d+) lights, (\d+) monsters" % (sx, sy), text)[-1]
rooms, halls, doors, conts, inst, lights, mons = map(int, st)
NEW = (int(sx), int(sy)); ORIGIN = (float(ox), float(oy))
print(f"generation of section {NEW} at sequence {T_GEN:.2f} s (world {wt}); {rooms} rooms, {doors} door leaves, {conts} container parts, {mons} monsters")
KIND = {"HALL": "Great hall", "BARRACKS": "Barracks", "PRISON": "Prison cells", "TORTURE": "Torture chamber", "STOREROOM": "Storeroom",
        "ARMORY": "Armory", "KITCHEN": "Kitchen", "LIBRARY": "Library", "CHAPEL": "Chapel", "CRYPT": "Crypt", "TREASURY": "Treasury",
        "GUARD_ROOM": "Guard room", "FORGE": "Forge", "JUNCTION": "Hallway junction"}
SECS = []
for s in R["map"]:
    rects = []
    for x0, y0, x1, y1, kind, corr in s["rects"]:
        k = kind.split(":")[0].strip()
        rects.append({"min": (x0 * TS, y0 * TS), "max": (x1 * TS, y1 * TS), "corr": corr or k == "JUNCTION", "kind": KIND.get(k, k)})
    SECS.append({"coord": tuple(s["coord"]), "rects": rects, "doors": s["doors"]})
# discovery: when she first enters a room (or comes within 4 tiles of a hallway)
for s in SECS:
    for r in s["rects"]:
        pad = 4 * TS if r["corr"] else 0
        r["seen"] = None
        for row in rows:
            t = row[0] - LAG
            if r["min"][0] - pad <= row[1] < r["max"][0] + pad and r["min"][1] - pad <= row[2] < r["max"][1] + pad:
                r["seen"] = max(t, 0.0); break
total_rooms = lambda t: sum(1 for s in SECS for r in s["rects"] if not r["corr"] and (s["coord"] != NEW or t >= T_GEN))
seen_rooms = lambda t: sum(1 for s in SECS for r in s["rects"] if not r["corr"] and r["seen"] is not None and r["seen"] <= t)
# ---- drawing
F = r"C:\Windows\Fonts"
def font(name, size):
    for n in (name, "segoeui.ttf", "arial.ttf"):
        try: return ImageFont.truetype(os.path.join(F, n), size)
        except OSError: pass
    return ImageFont.load_default()
f_title, f_sub, f_head, f_line, f_small = font("segoeuib.ttf", 40), font("segoeui.ttf", 24), font("seguisb.ttf", 30), font("segoeui.ttf", 24), font("seguisb.ttf", 19)
CYAN = (110, 225, 255)
ROOM_LIT, ROOM_DIM, HALL_LIT, HALL_DIM = (204, 176, 128), (77, 82, 92), (148, 133, 107), (61, 66, 74)
def fade(t, t0, t1, fin=0.35, fout=0.6):
    if t < t0 or t > t1: return 0.0
    return min(1.0, (t - t0) / fin, (t1 - t) / fout)
def overlay(t):
    W, H = 1920, 1080
    o = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(o)
    a = fade(t, 0.2, 4.6)
    if a > 0:
        d.text((44, 34), "random_dungeon_level", font=f_title, fill=(255, 255, 255, int(235 * a)))
        d.text((46, 86), "procedural dungeon  \u00b7  jrpg-fem5-tripo", font=f_sub, fill=(225, 230, 235, int(215 * a)))
    # minimap: north (+X) up, screen right = +Y; 150 m across, centred on her
    PX = 330; x0s, y0s = W - 44 - PX, 86
    d.rounded_rectangle((x0s - 14, 36, x0s + PX + 14, y0s + PX + 50), 14, fill=(10, 13, 18, 185))
    d.rectangle((x0s, y0s, x0s + PX, y0s + PX), fill=(6, 7, 10, 220))
    hx, hy, yaw = her(t); half = 7500.0
    def to_px(x, y): return (x0s + (y - (hy - half)) / (2 * half) * PX, y0s + ((hx + half) - x) / (2 * half) * PX)
    def box(r, col):
        (ax, ay), (bx, by) = to_px(r["max"][0], r["min"][1]), to_px(r["min"][0], r["max"][1])
        ax, ay, bx, by = max(ax, x0s), max(ay, y0s), min(bx, x0s + PX), min(by, y0s + PX)
        if bx > ax and by > ay: d.rectangle((ax, ay, bx, by), fill=col)
    age = t - T_GEN
    for s in SECS:
        new = s["coord"] == NEW
        if new and age < 0: continue
        u = min(1.0, max(0.0, age / 2.0)) if new else 1.0
        # wipe from the border she approaches (west edge of the new section) eastward = upward on the map
        sx0 = (s["coord"][0] * NT - NT // 2) * TS
        lim = sx0 + u * NT * TS
        for r in s["rects"]:
            if new and r["min"][0] >= lim: continue
            rr = dict(r); rr["max"] = (min(r["max"][0], lim) if new else r["max"][0], r["max"][1])
            lit = r["seen"] is not None and r["seen"] <= t
            col = (HALL_LIT if lit else HALL_DIM) if r["corr"] else (ROOM_LIT if lit else ROOM_DIM)
            if new and age < 1.6 and not lit: col = tuple(int(c + (cy - c) * (1 - age / 1.6)) for c, cy in zip(col, CYAN))
            box(rr, col + (235,))
        for dx, dy in s["doors"]:
            if new and dx >= lim: continue
            px, py = to_px(dx, dy)
            if x0s < px < x0s + PX and y0s < py < y0s + PX: d.rectangle((px - 2, py - 2, px + 2, py + 2), fill=(115, 64, 26, 255))
        if new and age < 4.0:
            (ax, ay), (bx, by) = to_px(sx0 + NT * TS, (s["coord"][1] * NT - NT // 2) * TS), to_px(sx0, (s["coord"][1] * NT + NT // 2) * TS)
            al = 1 - age / 4.0
            ax, ay, bx, by = max(ax, x0s), max(ay, y0s), min(bx, x0s + PX), min(by, y0s + PX)
            d.rectangle((ax, ay, bx, by), outline=CYAN + (int(255 * al),), width=3)      # (ImageDraw replaces pixels: no translucent fill over the rooms)
    d.rectangle((x0s, y0s, x0s + PX, y0s + PX), outline=(190, 166, 115, 230), width=2)
    # her arrow (screen angle = yaw - 90)
    cx, cy = x0s + PX / 2, y0s + PX / 2; ang = math.radians(yaw - 90)
    fx, fy = math.cos(ang), math.sin(ang)
    d.polygon([(cx + fx * 12, cy + fy * 12), (cx - fx * 7 - fy * 7, cy - fy * 7 + fx * 7), (cx - fx * 7 + fy * 7, cy - fy * 7 - fx * 7)], fill=(255, 120, 170, 255), outline=(255, 255, 255, 255))
    d.text((x0s, 44), "DUNGEON", font=f_small, fill=(235, 222, 190, 235))
    d.text((x0s + PX, 44), f"{seen_rooms(t)} / {total_rooms(t)} rooms", font=f_small, fill=(235, 222, 190, 235), anchor="ra")
    d.text((x0s + PX / 2, y0s + 4), "N", font=f_small, fill=(235, 222, 190, 200), anchor="ma")
    ly = y0s + PX + 14
    d.rectangle((x0s, ly + 6, x0s + 12, ly + 18), fill=ROOM_LIT + (255,)); d.text((x0s + 18, ly), "discovered", font=f_small, fill=(210, 212, 215, 210))
    d.rectangle((x0s + 128, ly + 6, x0s + 140, ly + 18), fill=ROOM_DIM + (255,)); d.text((x0s + 146, ly), "generated", font=f_small, fill=(210, 212, 215, 210))
    d.rectangle((x0s + 240, ly + 6, x0s + 252, ly + 18), fill=CYAN + (255,)); d.text((x0s + 258, ly), "new", font=f_small, fill=(210, 212, 215, 210))
    # caption (bottom left)
    a = fade(t, T_GEN, T_GEN + 5.5)
    if a > 0:
        y = H - 170
        d.rounded_rectangle((32, y - 14, 760, H - 48), 12, fill=(8, 11, 16, int(175 * a)))
        d.text((50, y - 4), "\u25b2 NEW DUNGEON SECTION GENERATED", font=f_head, fill=CYAN + (int(255 * a),))
        ai = a * min(1.0, max(0.0, (t - T_GEN) / 0.3))
        d.text((54, y + 42), f"section ({NEW[0]}, {NEW[1]})  \u00b7  252 m x 252 m  \u00b7  {rooms} rooms, {halls} hallways", font=f_line, fill=(240, 244, 248, int(240 * ai)))
        d.text((54, y + 74), f"{doors} door leaves  \u00b7  {conts} container parts (all open with F)  \u00b7  {mons} monsters", font=f_line, fill=(240, 244, 248, int(240 * ai)))
    return o
os.makedirs(dst, exist_ok=True)
frames = sorted(glob.glob(os.path.join(src, "*.png")))
for i, p in enumerate(frames):
    if i % step: continue
    t = i / FPS
    im = Image.open(p).convert("RGBA")
    if im.size != (1920, 1080): im = im.resize((1920, 1080))
    Image.alpha_composite(im, overlay(t)).convert("RGB").save(os.path.join(dst, f"rdhud.{i:04d}.png"), compress_level=1)
print("wrote", len(range(0, len(frames), step)), "frames to", dst)
