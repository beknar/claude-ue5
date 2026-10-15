"""random_dungeonmagic_level and random_dungeonmagic_level2 demo reel HUD (generalised from rdc_reel_overlay.py; the level is
the recording's): composites onto the Movie Render Queue
frames (the queue does not draw the game's HUD) what the game's HUD shows in play, redrawn from 815's recording of the
render itself (SourceArt/random_dungeon_magic/cine_render.json):
- the stylised minimap (top right, north up): the miniature of the dungeon as ARDHUD::DrawDungeon draws it (walls, stone
  floors coloured by room with paving joints and a lit / shaded edge, hallways, doors, chests and flickering torches in
  the rooms she has seen, rooms not yet seen dim), the monsters near her (ringed when they are after her), her arrow,
  a new section flashing as it is generated;
- the status panel (bottom right): her name, hit points, the fire spell with its damage, kills, her keys;
- a bar with name and hit points over each monster in the fight, the damage numbers floating up from each blow, the
  red flash when she is hurt, the banner when a section is generated;
- for the reel: a title, a caption for each fight (the monster's tier against her, how far she cast from), for each chest
  and for the generation; the keys that do what she does at that moment (W A S D as she moves, Shift as she runs, E as
  she casts, F as she opens: the pilot plays through the calls those keys make); what is heard written out as it sounds
  (the record has every sound the game played: the spell's charge, flight and burst, a monster's roar, growl, cry and
  death, a door or chest she opens, a torch she passes, the rumble of a new section), and which music is playing.
Usage: rdm_reel_overlay.py frames_dir out_dir [step] [level: 1 or 2]"""
import sys, os, re, json, glob, math
from PIL import Image, ImageDraw, ImageFont
src, dst = sys.argv[1], sys.argv[2]
step = int(sys.argv[3]) if len(sys.argv) > 3 else 1
L2 = len(sys.argv) > 4 and sys.argv[4] == "2"
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "random_dungeon_magic" + ("2" if L2 else ""))
SND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "random_dungeon_combat")      # (the sounds are the combat level's)
R = json.load(open(os.path.join(SRC, "cine_render.json")))
FPS = R["fps"]; ROWS = {r["frame"]: r for r in R["rows"]}; LASTF = max(ROWS); C = R["const"]; EV = R["events"]
TS = C["tile"]; NT = C["section_tiles"]
W, H, K = 1920, 1080, 2                       # the layer is drawn K times larger and scaled down (smooth edges)
def row(f): return ROWS.get(min(max(f, 0), LASTF)) or ROWS[min(ROWS, key=lambda k: abs(k - f))]
HITS = [e for e in EV if e["kind"] == "hit"]; KILLS = [e for e in EV if e["kind"] == "kill"]; FIGHTS = [e for e in EV if e["kind"] == "fight"]
GENS = [e for e in EV if e["kind"] == "generated"]; DISC = [e for e in EV if e["kind"] == "discovered"]; CHESTS = [e for e in EV if e["kind"] == "chest"]
CASTS = [e for e in EV if e["kind"] == "cast"]; SPELL = C["spell"]
# ---- what is heard, written out: (time, text) from the sounds the game played
HEARD = []
VOICE = {"Roar": "roars", "Idle": "growls", "Hurt": "cries out", "Death": "dies"}
for e in EV:
    if e["kind"] == "sound":
        k = e["key"].split(".")
        if k[0] == "Monster" and len(k) == 3 and k[2] in VOICE: HEARD.append((e["t"], "the %s %s" % (k[1].lower(), VOICE[k[2]])))
        elif e["key"] == "Player.Hurt": HEARD.append((e["t"], "she cries out"))
        elif e["key"] == "Player.Death": HEARD.append((e["t"], "she falls"))
        elif e["key"] == "Env.Generate": HEARD.append((e["t"], "the dungeon rumbles: a new section"))
        elif e["key"] == "Player.Charge.Fire": HEARD.append((e["t"], "fire gathers in her hand"))
        elif e["key"] == "Player.Cast.Fire": HEARD.append((e["t"], "the fire bolt roars away"))
        elif e["key"] == "Player.Hit.Fire": HEARD.append((e["t"], "the fire bursts"))
        elif e["key"] == "Player.Hit.Sword": HEARD.append((e["t"], "the sword bites"))
    elif e["kind"] == "door": HEARD.append((e["t"], "a door creaks open"))
    elif e["kind"] == "chest": HEARD.append((e["t"], "the %s creaks open" % e["what"].split()[-1]))
HEARD.sort()
# ---- the music: its changes between wandering and battle; the tracks' names from the prep's index when it is there
MUSIC = [e for e in EV if e["kind"] == "music"]
TRACK = {}
try:
    for e in json.load(open(os.path.join(SND, "audio", "index.json"), encoding="utf-8")).values():
        for f, s in zip(e["files"], e["source"]):
            n = re.sub(r"_Music_Pack_Volume_\d+", "", os.path.splitext(os.path.basename(s.split(": ", 1)[1]))[0])
            TRACK[os.path.splitext(f)[0]] = re.sub(r"_Track_(\d+)_.*$", r", track \1", n).replace("_", " ")
except Exception as ex: print("no track names:", ex)
print("frames %d | %d fights, %d kills | %d blows on monsters, %d on her | sections generated at %s" % (len(ROWS), len(FIGHTS), len(KILLS), sum(1 for h in HITS if not h["on_player"]),
      sum(1 for h in HITS if h["on_player"]), ", ".join("%.1f s" % e["t"] for e in GENS)))
# ---- the map as the HUD had it at a time: per section its latest snapshot and the rooms discovered by then
for m in R["maps"]:
    def inside(p, pad):
        for i, r in enumerate(m["rects"]):
            if r[0] * TS - pad <= p[0] <= r[2] * TS + pad and r[1] * TS - pad <= p[1] <= r[3] * TS + pad: return i
        return -1
    m["chest_rect"] = [inside(p, 0.0) for p in m["chests"]]; m["torch_rect"] = [inside(p, 30.0) for p in m["torches"]]
def map_at(t):
    out = {}
    for m in R["maps"]:
        if m["t"] <= t + 1e-6: out[tuple(m["coord"])] = m
    disc = {}
    for e in DISC:
        if e["t"] <= t + 1e-6: disc[tuple(e["coord"])] = set(e["rects"])
    return out, disc
def lin(c, a=1.0): return tuple(int(255 * min(1.0, max(0.0, v)) ** (1 / 2.2)) for v in c[:3]) + (int(255 * min(1.0, max(0.0, a))),)
FLOOR = {"HALL": (0.62, 0.55, 0.42), "BARRACKS": (0.50, 0.46, 0.40), "PRISON": (0.38, 0.40, 0.45), "TORTURE": (0.47, 0.30, 0.28), "STOREROOM": (0.52, 0.44, 0.32), "ARMORY": (0.45, 0.48, 0.53),
         "KITCHEN": (0.58, 0.48, 0.36), "LIBRARY": (0.49, 0.38, 0.30), "CHAPEL": (0.61, 0.59, 0.51), "CRYPT": (0.36, 0.39, 0.37), "TREASURY": (0.66, 0.56, 0.27), "GUARD_ROOM": (0.48, 0.44, 0.38),
         "FORGE": (0.54, 0.35, 0.24)}
def floor(kind, corridor): return (0.33, 0.31, 0.29) if corridor else FLOOR.get(kind.upper().replace(" ", "_"), (0.40, 0.38, 0.35))
def shade(c, k): return tuple(v * k for v in c)
INK, CYAN = (0.92, 0.86, 0.72), (0.43, 0.88, 1.0)
F = r"C:\Windows\Fonts"
def font(name, size):
    for n in (name, "segoeui.ttf", "arial.ttf"):
        try: return ImageFont.truetype(os.path.join(F, n), int(size * K))
        except OSError: pass
    return ImageFont.load_default()
f_title, f_sub, f_head, f_line, f_small, f_tiny, f_key, f_num, f_ban = (font("segoeuib.ttf", 40), font("segoeui.ttf", 24), font("seguisb.ttf", 30), font("segoeui.ttf", 24), font("seguisb.ttf", 17),
                                                                      font("seguisb.ttf", 14), font("segoeuib.ttf", 34), font("segoeuib.ttf", 30), font("seguisb.ttf", 30))
f_note = font("seguisym.ttf", 24)                 # (the note sign of the heard lines: not in Segoe UI itself)
def fade(t, t0, t1, fin=0.35, fout=0.5):
    if t < t0 or t > t1: return 0.0
    return min(1.0, (t - t0) / fin, (t1 - t) / fout)
def minimap(r, t, maps, disc, P, half):
    """the miniature around her, P pixels square (layer pixels), `half` cm to each side; north (+X) up"""
    im = Image.new("RGBA", (P, P), lin((0.02, 0.02, 0.03), 0.85)); d = ImageDraw.Draw(im, "RGBA")
    cx, cy = r["p"][0], r["p"][1]; k = P / (2.0 * half); Tp = k * TS
    px = lambda wx, wy: ((wy - cy + half) * k, (cx - wx + half) * k)
    def rc(a, b, grow, col):
        (x0, y0), (x1, y1) = px(*a), px(*b)
        lo = (min(x0, x1) - grow, min(y0, y1) - grow); hi = (max(x0, x1) + grow, max(y0, y1) + grow)
        if hi[0] < 0 or hi[1] < 0 or lo[0] > P or lo[1] > P: return None
        d.rectangle((lo[0], lo[1], hi[0], hi[1]), fill=col); return lo, hi
    def dot(p, h, col):
        x, y = px(*p)
        if -h <= x <= P + h and -h <= y <= P + h: d.rectangle((x - h, y - h, x + h, y + h), fill=col)
    wall = min(7.0 * K, max(1.5 * K, Tp * 0.24))
    vis = []
    for c, m in maps.items():
        seen = disc.get(c, set())
        for i, q in enumerate(m["rects"]):
            a, b = (q[0] * TS, q[1] * TS), (q[2] * TS, q[3] * TS)
            if rc(a, b, wall, lin((0.10, 0.09, 0.08)) if i in seen else lin((0.09, 0.10, 0.12), 0.8)) is not None: vis.append((c, i, q, a, b, i in seen))
    for corridor in (1, 0):
        for c, i, q, a, b, seen in vis:
            if q[5] != corridor: continue
            if not seen: rc(a, b, 0.0, lin((0.16, 0.17, 0.19), 0.9) if corridor else lin((0.20, 0.21, 0.24), 0.9)); continue
            fl = floor(q[4], corridor); box = rc(a, b, 0.0, lin(fl))
            if box is None: continue
            lo, hi = box
            if Tp >= 6.0 * K:
                j = lin(shade(fl, 0.72), 0.55)
                for x in range(q[0] + 1, q[2]): rc((x * TS, q[1] * TS), (x * TS, q[3] * TS), 0.5 * K, j)
                for y in range(q[1] + 1, q[3]): rc((q[0] * TS, y * TS), (q[2] * TS, y * TS), 0.5 * K, j)
            if not corridor:
                e = max(1.5 * K, wall * 0.6)
                d.rectangle((lo[0], lo[1], hi[0], lo[1] + e * 1.6), fill=lin(shade(fl, 0.55), 0.75)); d.rectangle((lo[0], lo[1], lo[0] + e * 1.6, hi[1]), fill=lin(shade(fl, 0.62), 0.6))
                d.rectangle((lo[0], hi[1] - e, hi[0], hi[1]), fill=lin(shade(fl, 1.35), 0.55)); d.rectangle((hi[0] - e, lo[1], hi[0], hi[1]), fill=lin(shade(fl, 1.25), 0.45))
    for c, m in maps.items():
        seen = disc.get(c, set())
        for i, p in enumerate(m["torches"]):
            if m["torch_rect"][i] not in seen: continue
            fl = 0.75 + 0.25 * math.sin(t * 9.0 + (i + 1) * 1.7)
            dot(p, Tp * 0.55, lin((1.0, 0.55, 0.15), 0.13 * fl)); dot(p, Tp * 0.28, lin((1.0, 0.62, 0.2), 0.22 * fl)); dot(p, max(1.2 * K, Tp * 0.09), lin((1.0, 0.85, 0.45), 0.95))
        for i, p in enumerate(m["chests"]):
            if m["chest_rect"][i] not in seen: continue
            h = max(1.6 * K, Tp * 0.17)
            dot(p, h + K, lin((0.16, 0.10, 0.05))); dot(p, h, lin((0.56, 0.36, 0.14))); dot(p, max(0.8 * K, h * 0.35), lin((0.95, 0.78, 0.3)))
        for p in m["doors"]:
            h = max(2.0 * K, Tp * 0.26)
            dot(p, h + K, lin((0.12, 0.07, 0.03))); dot(p, h, lin((0.60, 0.36, 0.14)))
    for e in GENS:                               # a section just generated: its square flashes cyan
        age = t - e["t"]
        if 0.0 <= age < 4.0:
            for c, m in maps.items():
                if abs(m["t"] - e["t"]) < 1.0 and c != (0, 0):
                    x0, y0 = (c[0] - 0.5) * NT * TS, (c[1] - 0.5) * NT * TS
                    b = rc((x0, y0), (x0 + NT * TS, y0 + NT * TS), 0.0, lin(CYAN, 0.22 * (1 - age / 4.0)))
                    if b: d.rectangle((b[0][0], b[0][1], b[1][0], b[1][1]), outline=lin(CYAN, 1 - age / 4.0), width=2 * K)
    for mo in r["mon"]:
        if mo[8] or math.hypot(mo[2] - cx, mo[3] - cy) > 2500.0: continue
        x, y = px(mo[2], mo[3])
        if 4 * K < x < P - 4 * K and 4 * K < y < P - 4 * K:
            h = (4.5 if mo[7] else 3.0) * K
            if mo[7]: d.rectangle((x - h - 2 * K, y - h - 2 * K, x + h + 2 * K, y + h + 2 * K), fill=lin((1.0, 0.9, 0.3), 0.9))
            d.rectangle((x - h, y - h, x + h, y + h), fill=lin((0.95, 0.15, 0.12)))
    # her arrow (north up: her yaw turned a quarter)
    a = math.radians(r["yaw"] - 90.0); fx, fy = math.cos(a), math.sin(a); s = 9.0 * K; c0 = (P / 2, P / 2)
    tri = [(c0[0] + fx * s, c0[1] + fy * s), (c0[0] - fx * s * 0.6 - fy * s * 0.6, c0[1] - fy * s * 0.6 + fx * s * 0.6), (c0[0] - fx * s * 0.6 + fy * s * 0.6, c0[1] - fy * s * 0.6 - fx * s * 0.6)]
    d.polygon(tri, fill=lin((1.0, 0.47, 0.67)), outline=(255, 255, 255, 255))
    d.line(tri + [tri[0]], fill=(255, 255, 255, 255), width=2 * K)
    return im
def axes(r):
    p, y, ro = (math.radians(v) for v in r); cp, sp, cy, sy, cr, sr = math.cos(p), math.sin(p), math.cos(y), math.sin(y), math.cos(ro), math.sin(ro)
    return (cp * cy, cp * sy, sp), (sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp), (-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp)
def project(r, P):
    fw, rt, up = axes(r["cr"]); dx = [P[i] - r["cp"][i] for i in range(3)]; z = sum(dx[i] * fw[i] for i in range(3))
    if z <= 1.0: return None
    foc = (W * K / 2) / math.tan(math.radians(r["fov"]) / 2)
    return (W * K / 2 + sum(dx[i] * rt[i] for i in range(3)) / z * foc, H * K / 2 - sum(dx[i] * up[i] for i in range(3)) / z * foc)
def text_c(d, xy, s, f, fill, anchor="mm", shadow=True):
    if shadow: d.text((xy[0] + K, xy[1] + K), s, font=f, fill=(0, 0, 0, int(fill[3] * 0.75)), anchor=anchor)
    d.text(xy, s, font=f, fill=fill, anchor=anchor)
def overlay(f):
    r = row(f); t = f / FPS
    maps, disc = map_at(t)
    o = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0)); d = ImageDraw.Draw(o, "RGBA")
    ua = fade(t, 0.25, 1e9, 0.5, 0.5)                    # the HUD comes up as the reel opens
    A = lambda v: v * ua
    # ---- she was just hurt: the edges flash red
    for h in HITS:
        age = t - h["t"]
        if h["on_player"] and 0.0 <= age < 0.5:
            c = lin((0.85, 0.05, 0.03), 0.34 * (1 - age / 0.5)); e = 46 * K
            d.rectangle((0, 0, W * K, e), fill=c); d.rectangle((0, H * K - e, W * K, H * K), fill=c); d.rectangle((0, e, e, H * K - e), fill=c); d.rectangle((W * K - e, e, W * K, H * K - e), fill=c)
    # ---- a bar over each monster in the fight
    for mo in r["mon"]:
        hurt = any(not h["on_player"] and 0 <= t - h["t"] < 6.0 and math.hypot(h["at"][0] - mo[2], h["at"][1] - mo[3]) < 400 for h in HITS)
        if mo[8] or not (mo[7] or hurt) or math.hypot(mo[2] - r["p"][0], mo[3] - r["p"][1]) > 2400.0: continue
        s = project(r, (mo[2], mo[3], mo[4] + mo[9] + 34.0))
        if not s or not (0 < s[0] < W * K and 0 < s[1] < H * K): continue
        bw, bh, fr = 96 * K, 8 * K, mo[5] / max(mo[6], 1.0); x0, y0 = s[0] - bw / 2, s[1] - bh
        d.rectangle((x0 - 2, y0 - 2, x0 + bw + 2, y0 + bh + 2), fill=lin((0.02, 0.02, 0.02), A(0.8)))
        d.rectangle((x0, y0, x0 + bw * fr, y0 + bh), fill=lin((0.85, 0.2, 0.14) if fr > 0.5 else (0.95, 0.45, 0.1), A(1.0)))
        text_c(d, (s[0], y0 - 4 * K), "%s  %.0f" % (mo[1].replace("_", " ").upper(), mo[5]), f_small, lin(INK, A(1.0)), "mb")
    # ---- the damage numbers float up
    for h in HITS:
        age = t - h["t"]
        if not 0.0 <= age <= 1.1: continue
        s = project(r, (h["at"][0], h["at"][1], h["at"][2] + 70.0 * age))
        if not s: continue
        al = max(0.0, min(1.0, 1.6 - age * 1.5))
        text_c(d, s, ("-%d" if h["on_player"] else "%d") % h["amount"], f_num, lin((1.0, 0.25, 0.2) if h["on_player"] else (1.0, 0.9, 0.35), al), "mb")
    # ---- minimap (top right)
    P = 300 * K; mg = 24 * K; x0, y0 = W * K - mg - P, mg + 26 * K
    d.rectangle((x0 - 8 * K, y0 - 34 * K, x0 + P + 8 * K, y0 + P + 30 * K), fill=lin((0.04, 0.05, 0.07), A(0.72)))
    mm = minimap(r, t, maps, disc, P, 84.0 * 50.0)
    if ua < 1.0: mm.putalpha(mm.getchannel("A").point(lambda v: int(v * ua)))
    o.alpha_composite(mm, (int(x0), int(y0))); d = ImageDraw.Draw(o, "RGBA")
    d.rectangle((x0, y0, x0 + P, y0 + P), outline=lin((0.75, 0.65, 0.45), A(0.9)), width=2 * K)
    rooms = sum(1 for m in maps.values() for q in m["rects"] if not q[5]); seen = sum(1 for c, m in maps.items() for i, q in enumerate(m["rects"]) if not q[5] and i in disc.get(c, set()))
    d.text((x0, y0 - 28 * K), "DUNGEON", font=f_small, fill=lin(INK, A(1.0))); d.text((x0 + P, y0 - 28 * K), "%d / %d rooms" % (seen, rooms), font=f_small, fill=lin(INK, A(1.0)), anchor="ra")
    d.text((x0 + P / 2, y0 + 3 * K), "N", font=f_small, fill=lin(INK, A(1.0)), anchor="ma"); d.text((x0, y0 + P + 5 * K), "M  map", font=f_small, fill=lin((0.7, 0.68, 0.62), A(1.0)))
    # ---- status panel (bottom right): hit points, the weapons with their damage, kills
    pw, ph, pd = 400 * K, 176 * K, 14 * K; ax, ay = W * K - mg - pw, H * K - mg - ph; bx, by = ax + pw, ay + ph
    d.rectangle((ax, ay, bx, by), fill=lin((0.04, 0.05, 0.07), A(0.78)), outline=lin((0.75, 0.65, 0.45), A(0.9)), width=2 * K)
    d.text((ax + pd, ay + 8 * K), C["title"], font=f_small, fill=lin(INK, A(1.0))); d.text((bx - pd, ay + 8 * K), "KILLS  %d" % r["kills"], font=f_small, fill=lin(INK, A(1.0)), anchor="ra")
    fr = r["hp"] / max(r["mhp"], 1.0); hx0, hy0, hx1, hy1 = ax + pd, ay + 36 * K, bx - pd, ay + 64 * K
    d.rectangle((hx0, hy0, hx1, hy1), fill=lin((0.10, 0.03, 0.03), A(0.95)))
    d.rectangle((hx0 + 2, hy0 + 2, hx0 + 2 + (hx1 - hx0 - 4) * fr, hy1 - 2), fill=lin((0.20, 0.72, 0.26) if fr > 0.5 else (0.90, 0.62, 0.12) if fr > 0.25 else (0.88, 0.16, 0.12), A(1.0)))
    d.rectangle((hx0, hy0, hx1, hy1), outline=lin((0.75, 0.65, 0.45), A(0.9)), width=K)
    text_c(d, ((hx0 + hx1) / 2, (hy0 + hy1) / 2 - K), "HP  %d / %d" % (math.ceil(r["hp"]), r["mhp"]), f_small, (255, 255, 255, int(255 * ua)))
    n = len(C["weapons"]); gp = 8 * K; sw = (pw - pd * 2 - gp * (n - 1)) / n
    for i, wd in enumerate(C["weapons"]):
        on = i == r["w"]; sx0, sy0 = ax + pd + i * (sw + gp), ay + 76 * K; sx1, sy1 = sx0 + sw, sy0 + 66 * K
        d.rectangle((sx0, sy0, sx1, sy1), fill=lin((0.36, 0.27, 0.10), A(0.95)) if on else lin((0.10, 0.10, 0.12), A(0.9)), outline=lin((1.0, 0.82, 0.35), A(1.0)) if on else lin((0.40, 0.38, 0.34), A(1.0)), width=int((2.5 if on else 1) * K))
        tc = (255, 255, 255, int(255 * ua)) if on else lin((0.72, 0.70, 0.66), A(1.0))
        on = on if not (L2 and wd.get("spell")) else any(e["t"] <= t <= e["t"] + 0.9 for e in CASTS)
        d.text((sx0 + 7 * K, sy0 + 3 * K), "RMB / E" if (L2 and wd.get("spell")) else str(i + 1), font=f_tiny, fill=lin((1.0, 0.82, 0.35), A(1.0)) if on else tc)
        d.text(((sx0 + sx1) / 2, sy0 + 26 * K), wd["name"].upper(), font=f_small, fill=tc, anchor="mm")
        d.text(((sx0 + sx1) / 2, sy0 + 48 * K), "%.0f damage" % wd["damage"], font=f_tiny, fill=lin((1.0, 0.9, 0.6), A(1.0)) if on else tc, anchor="mm")
    d.text((ax + pd, by - 26 * K), C["hint"], font=f_tiny, fill=lin((0.7, 0.68, 0.62), A(1.0)))
    # ---- the keys that do what she does now (above the status panel): W A S D lit as she moves (W: the way she faces),
    # Shift as she runs, E as she casts, F as she opens a door or chest
    mv, kh = r.get("moving", ""), r.get("keys", "")
    caps = [("W", mv != ""), ("A", False), ("S", False), ("D", False), ("SHIFT", mv == "run")] + ([("LMB", kh == "lmb")] if L2 else []) + [("E", kh == "e"), ("F", kh == "f")]
    kw = {"SHIFT": 112, "LMB": 76}; gap = 8 * K; total = sum(kw.get(c, 52) * K for c, _ in caps) + gap * (len(caps) - 1) + 24 * K
    kx = bx - 16 * K - total; ky = ay - 100 * K
    d.rounded_rectangle((kx - 14 * K, ky - 52 * K, kx + total + 14 * K, ky + 64 * K), 14 * K, fill=(12, 11, 9, int(150 * ua)))
    k0x = kx
    for i, (c, on) in enumerate(caps):
        w_ = kw.get(c, 52) * K
        if c == "SHIFT": kx += 24 * K
        d.rounded_rectangle((kx, ky, kx + w_, ky + 52 * K), 9 * K, fill=(238, 214, 150, int(255 * ua)) if on else (60, 58, 54, int(220 * ua)), outline=(255, 236, 180, int(255 * ua)) if on else (120, 112, 98, int(200 * ua)), width=2 * K)
        d.text((kx + w_ / 2, ky + 26 * K), c, font=f_small if c in ("SHIFT", "LMB") else f_head, fill=(28, 24, 18, int(255 * ua)) if on else (210, 204, 190, int(230 * ua)), anchor="mm")
        kx += w_ + gap
    lab = "run" if mv == "run" else "walk" if mv == "walk" else ""
    lab = "cast the fire spell" if kh == "e" else "swing the sword" if kh == "lmb" else "open" if kh == "f" else lab
    if lab: text_c(d, ((k0x + kx) / 2, ky - 24 * K), lab, f_line, (244, 240, 228, int(240 * ua)))
    # ---- the banner when a section is generated
    for e in GENS:
        age = t - e["t"]
        if 0.0 <= age < 3.5: text_c(d, (W * K / 2, 212 * K), "\u25b2 NEW DUNGEON SECTION GENERATED", f_ban, lin(CYAN, max(0.0, min(age / 0.3, (3.5 - age) / 0.8, 1.0))))
    # ---- the reel's own: title, captions (bottom left)
    a = fade(t, 0.3, 4.6)
    if a > 0:
        d.text((44 * K, 34 * K), "random_dungeonmagic_level2" if L2 else "random_dungeonmagic_level", font=f_title, fill=(255, 255, 255, int(235 * a)), stroke_width=2 * K, stroke_fill=(0, 0, 0, int(140 * a)))
        d.text((46 * K, 86 * K), ("procedural dungeon  \u00b7  fire from the left hand, a sword in the right  \u00b7  girl-darkcaster-tripo" if L2 else
                                  "procedural dungeon  \u00b7  a fire spell at medium range  \u00b7  girl-caster-tripo"), font=f_sub, fill=(232, 236, 240, int(225 * a)), stroke_width=2 * K, stroke_fill=(0, 0, 0, int(140 * a)))
    caps = []
    t_first = FIGHTS[0]["t"] if FIGHTS else 6.0
    t_chest = CHESTS[0]["t"] if CHESTS else 99.0
    if L2:
        caps.append((0.8, min(t_first - 0.2, t_chest - 0.4, (GENS[0]["t"] if GENS else 99) - 0.2), "FIRE AND STEEL", ["girl-darkcaster-tripo: her own idle, walk and run, and two left-hand casts and three sword cuts made for her in Blender",
                     "WASD walk  \u00b7  Shift run  \u00b7  left mouse: the sword  \u00b7  right mouse or E: the fire  \u00b7  F opens doors and containers"], (255, 240, 214)))
    else:
        caps.append((0.8, min(t_first - 0.2, t_chest - 0.4, (GENS[0]["t"] if GENS else 99) - 0.2), "A FIRE CASTER", ["girl-caster-tripo: her own walk and run, and an idle and three casts made for her in Blender",
                     "WASD walk  \u00b7  Shift run  \u00b7  left mouse or E: the fire spell  \u00b7  F opens doors and containers"], (255, 240, 214)))
    for e in CHESTS:
        caps.append((e["t"] - 0.3, e["t"] + 1.6, "F  \u00b7  THE %s OPENS" % e["what"].split()[-1].upper(), ["every door and container of the dungeon opens: chests, trunks, wardrobes, barrels, crates"], (255, 226, 150)))
    for e in GENS[:1]:
        caps.append((e["t"], min(e["t"] + 4.2, t_first - 0.1 if t_first > e["t"] else 99), "\u25b2 THE NEXT 252 m x 252 m OF DUNGEON IS GENERATED", ["as she nears the edge of what there is  \u00b7  never saved: a new dungeon every time"], lin(CYAN)[:3]))
    for i, e in enumerate(FIGHTS):
        end = next((k["t"] for k in KILLS if k["t"] > e["t"]), e["t"] + 6.0) + 1.2
        if i + 1 < len(FIGHTS): end = min(end, FIGHTS[i + 1]["t"] - 0.1)
        tier = "start section" if e["section"][0] == 0 else "generated section"
        cs = [c for c in CASTS if e["t"] <= c["t"] <= end]
        note = ("the first square's monsters are weaker than her" if e["section"][0] == 0 else "in the generated sections they are on a par with her (the average: %.0f hit points, %.0f a blow)" % tuple(C["runtime_tier"]))
        more = ("the bolt: %.0f m reach, %.0f m/s, it follows the monster she turned to and bursts on the first thing it meets" % (SPELL["reach"] / 100.0, SPELL["speed"] / 100.0),
                "the burst also burns every other monster within %.1f m for half the damage" % (SPELL["splash"] / 100.0),
                "the music turns to a battle track when a monster comes at her")[min(i, 2)]
        caps.append((e["t"], end, "%s  \u00b7  %s" % (e["monster"].replace("_", " ").upper(), tier),
                     [("%.0f hit points, %.0f damage a blow  \u00b7  she has %.0f; her fire bolt does %.0f, her sword %.0f  \u00b7  fire from %.0f m, then the sword" % (e["its_hit_points"], e["its_damage"], C["max_health"],
                       SPELL["damage"], next(w_["damage"] for w_ in C["weapons"] if not w_.get("spell")), cs[0].get("m", e["from_m"]) if cs else e["from_m"])) if L2 else
                      ("%.0f hit points, %.0f damage a blow  \u00b7  she has %.0f, and her fire bolt does %.0f  \u00b7  she casts from %.0f m" % (e["its_hit_points"], e["its_damage"], C["max_health"],
                       SPELL["damage"], cs[0].get("m", e["from_m"]) if cs else e["from_m"])), note, more], (255, 226, 150)))
    for t0, t1, head, lines, c in caps:
        k = fade(t, t0, t1)
        if k <= 0: continue
        y = (H - 62 - 36 - 34 * len(lines)) * K
        wd = max([d.textlength(head, font=f_head)] + [d.textlength(s, font=f_line) for s in lines])
        d.rounded_rectangle((32 * K, y - 14 * K, 60 * K + wd, (H - 48) * K), 12 * K, fill=(12, 11, 9, int(180 * k)))
        d.text((50 * K, y - 4 * K), head, font=f_head, fill=tuple(c[:3]) + (int(255 * k),))
        for i, s in enumerate(lines): d.text((54 * K, y + (42 + 34 * i) * K), s, font=f_line, fill=(240, 244, 248, int(240 * k)))
    # ---- the music playing now (top left, under the title): brighter for a moment when it changes
    mu = None
    for e in MUSIC:
        if e["t"] <= t + 1e-6: mu = e
    if mu:
        hot = max(0.0, 1.0 - (t - mu["t"]) / 1.2); col = (255, 150, 90) if mu["battle"] else (150, 220, 255)
        s = ("battle music" if mu["battle"] else "wandering music") + "  \u00b7  " + TRACK.get(mu["track"], mu["track"])
        y = 146 * K; tw = d.textlength(s, font=f_line)
        d.rounded_rectangle((32 * K, y - 20 * K, 102 * K + tw, y + 20 * K), 10 * K, fill=(12, 11, 9, int((150 + 70 * hot) * ua)), outline=col + (int(255 * hot * ua),), width=2 * K)
        d.text((48 * K, y), "\u266b", font=f_note, fill=col + (int(255 * ua),), anchor="lm"); d.text((86 * K, y), s, font=f_line, fill=(236, 240, 244, int(245 * ua)), anchor="lm")
    # ---- what is heard (left, above the captions): each for a moment, the newest lowest; a torch while she is by it
    lines = [(s, fade(t, t0, t0 + 1.9, 0.12, 0.5)) for t0, s in HEARD if t0 <= t <= t0 + 1.9]
    fire = r.get("fire", -1)
    if 0 <= fire < 520: lines.insert(0, ("a torch crackles", min(1.0, (520 - fire) / 170.0) * ua))
    y = (H - 252) * K
    for s, k in reversed(lines[-4:]):
        if k <= 0: continue
        tw = d.textlength(s, font=f_line)
        d.rounded_rectangle((32 * K, y - 19 * K, 96 * K + tw, y + 19 * K), 10 * K, fill=(12, 11, 9, int(150 * k)))
        d.text((48 * K, y), "\u266a", font=f_note, fill=(150, 220, 255, int(255 * k)), anchor="lm"); d.text((80 * K, y), s, font=f_line, fill=(236, 240, 244, int(245 * k)), anchor="lm")
        y -= 44 * K
    if t < 0.4: d.rectangle((0, 0, W * K, H * K), fill=(0, 0, 0, int(255 * max(0.0, 1.0 - max(0.0, t - 0.07) / 0.33))))       # (the reel fades in: on the first frames the camera is still settling behind her)
    return o.resize((W, H), Image.LANCZOS)
os.makedirs(dst, exist_ok=True)
frames = sorted(glob.glob(os.path.join(src, "*.png")))
for i, p in enumerate(frames):
    if i % step: continue
    im = Image.open(p).convert("RGBA")
    if im.size != (W, H): im = im.resize((W, H), Image.LANCZOS)
    Image.alpha_composite(im, overlay(i)).convert("RGB").save(os.path.join(dst, f"rdm{'2' if L2 else ''}hud.{i:04d}.png"), compress_level=1)
print("wrote", len(range(0, len(frames), step)), "frames to", dst)
