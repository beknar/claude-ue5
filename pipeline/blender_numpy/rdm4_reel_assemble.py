"""random_dungeonmagic_level4 demo reel: puts the reel together from the menu's render and the four heroes' runs.
For each hero in turn (Warrior, Mage, Warlock, Rogue): a passage of the menu (the render of random_dungeonmagic_level4_select,
829's record cine_menu.json: the hero shown, when she was shown, START, the key pressed) with the menu's HUD drawn over it
as ARDHeroSelectHUD draws it in play (the Movie Render Queue does not draw the HUD): the title, her card (name, hit points
and mana against the others', her other numbers (mana back, bonuses, the roll), main abilities, armour, what she starts
with: each weapon and spell with its picture and what it does), the four names along the bottom, the arrows,
START lighting up when it is pressed, the keys pressed; then her run in the dungeon (815 + rdm_reel_overlay.py with level 4:
frames with the dungeon's HUD already on them). The menu passages fade to black and the runs fade in.
Sound: under the menu, the music pack's menu track ("Menu" by name, continuing from passage to passage); under each run, the
game's own mix of that render (its .wav); the menu music levelled to the runs' loudness; short fades at every join.
With the painted interface (ui_art_dir: rdm4_ui_cut.py --export's folder) the menu's card, bars, dividers, name plates,
arrows and START are drawn with the painted pieces where ARDHeroSelectHUD draws them (rdm4_ui_draw.py), and the runs are
taken from <hud_prefix><hero> (rdm_reel_overlay.py with the same folder). Its lettering is then the game's (rdm4_fonts.py's
files, ARDHeroSelectHUD's roles): Cinzel for the titles, names, START and keys, Alegreya for the text, Alegreya SC for the
labels (written "Mana Back": sc()).
Level 5 (the seventh argument "5"; the Summoner's armour reel): the menu of random_dungeonmagic_level5 (829 with level 5:
one passage, the five heroes looked through and the Summoner started) and her run (815 with level 5), from
SourceArt/random_dungeon_magic5.
Usage (a Python with numpy, scipy and Pillow): rdm4_reel_assemble.py <work_dir> <out_frames_dir> <menu_music.wav> <out_track.wav> [ui_art_dir hud_prefix [level: 4, 5, 5w, 5h or 5c]]
  (5w: level 5's weapons and tiers reel, the Warrior picked in the menu; 5h: the four heroes' weapons reel, each of the
  Warrior, Mage, Warlock and Rogue picked in a passage of her own and followed by her run, as level 4's reel; 5c: the
  armour table, loot and crafting reel, the same passages and runs)
  work_dir holds final_menu (the menu's frames), hud_<hero> (her run with the HUD) and final_<hero> (her run's .wav)"""
import sys, os, glob, json, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
WORK, OUT, MUSIC, TRACK = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
UI, HUD = None, "hud_"
if len(sys.argv) > 6:
    from rdm4_ui_draw import UIArt
    UI, HUD = UIArt(sys.argv[5]), sys.argv[6]
LV = sys.argv[7] if len(sys.argv) > 7 else "4"
W5 = LV == "5w"; C5 = LV == "5c"; Q5 = LV in ("5h", "5c"); LV = LV[:1]     # ("5c": the armour table, loot and crafting reel: the quartet's menu, four runs)          # ("5w": level 5's weapons and tiers reel, the Warrior: 829's cine_menu_warrior.json;
                                                       #  "5h": the four heroes' weapons reel, cine_menu_quartet.json)
SRC = os.path.join(HERE, "..", "..", "claude_ue5", "SourceArt", "random_dungeon_magic" + LV)
M = json.load(open(os.path.join(SRC, "cine_menu_warrior.json" if W5 else "cine_menu_quartet.json" if Q5 else "cine_menu.json"), encoding="utf-8"))
ORDER = M.get("want") or ["Warrior", "Mage", "Warlock", "Rogue"]
TITLE, SUB = (("random_dungeonmagic_level5", "four heroes: armour by its table, loot by tier, repair items made at anvils, the tiers on the maps") if C5 else
              ("random_dungeonmagic_level5", "four heroes, the weapons and the armour: who wields and wears what, a weapon that breaks, the tiers of rooms") if Q5 else
              ("random_dungeonmagic_level5", "choose the warrior in the menu: a table of 29 weapons to find, wield and wear out, and five tiers of rooms") if W5 else
              ("random_dungeonmagic_level5", "choose the summoner in the menu, then the great hall: five armour sets to find and wear") if LV == "5" else
              ("random_dungeonmagic_level4", "choose a hero in the menu, then the dungeon: four heroes, four runs"))
FPS = M["fps"]; PASS = int(round(M["passage"] * FPS)); ROWS = {r["frame"]: r for r in M["rows"]}; LAST = max(ROWS)
HEROES = M["heroes"]
W, H, K = 1920, 1080, 2
F = r"C:\Windows\Fonts"
def font(name, size):
    for n in (name, "segoeui.ttf", "arial.ttf"):
        try: return ImageFont.truetype(os.path.join(F, n), int(size * K))
        except OSError: pass
    return ImageFont.load_default()
f_big, f_title, f_name, f_tab, f_line, f_small, f_key, f_cap = (font("segoeuib.ttf", 56), font("segoeuib.ttf", 40), font("segoeuib.ttf", 58), font("seguisb.ttf", 24),
                                                                 font("segoeui.ttf", 23), font("seguisb.ttf", 18), font("segoeuib.ttf", 30), font("seguisb.ttf", 26))
# ---- with the painted interface: the game's lettering (sizes: Alegreya a tenth larger than the Segoe UI it replaces)
FD = os.path.join(HERE, "..", "..", "claude_ue5", "SourceArt", "random_dungeon_magic4", "fonts")       # (level 5 uses level 4's)
LETTERS = bool(UI) and os.path.exists(os.path.join(FD, "Cinzel-700.ttf"))
def lfont(fn, size): return ImageFont.truetype(os.path.join(FD, fn + ".ttf"), int(size * K))
def sc(s):
    """a label for the small-capitals face (FRDUIDraw's RDUISmallCaps)"""
    if not LETTERS: return s
    return re.sub(r"[^\W\d_]{3,}", lambda m: m.group(0)[0] + m.group(0)[1:].lower() if m.group(0).isupper() else m.group(0), s)
if LETTERS:
    f_big, f_title, f_name, f_tab, f_key, f_cap = (lfont("Cinzel-700", 56), lfont("Cinzel-700", 40), lfont("Cinzel-700", 58), lfont("Cinzel-700", 24),
                                                   lfont("Cinzel-700", 30), lfont("Cinzel-700", 26))
    f_line, fx_small, fl_small, ft_line, f_capt = lfont("Alegreya-500", 25), lfont("Alegreya-500", 20), lfont("AlegreyaSC-700", 19), lfont("Cinzel-700", 22), lfont("Alegreya-500", 29)
else:
    fx_small, fl_small, ft_line, f_capt = f_small, f_small, f_line, f_cap
def lin(c, a=1.0): return tuple(int(255 * min(1.0, max(0.0, v)) ** (1 / 2.2)) for v in c[:3]) + (int(255 * min(1.0, max(0.0, a))),)
INK, DIM, LINE = (0.93, 0.88, 0.76), (0.68, 0.66, 0.60), (0.75, 0.65, 0.45)
def row(f): return ROWS.get(min(max(f, 0), LAST)) or ROWS[min(ROWS, key=lambda k: abs(k - f))]

def menu_hud(f, k, fl):
    """the menu's HUD over frame f of the menu render (passage k, frame fl in it)"""
    r = row(f); h = HEROES[r["hero"]]; t = fl / FPS
    o = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0)); d = ImageDraw.Draw(o, "RGBA")
    fade = max(0.0, min(1.0, r["shown_ago"] / 0.35)); acc = tuple(h["accent"])
    ink = lambda c, a=1.0: lin(c, a * fade)
    d.text((80 * K, 44 * K), sc("RANDOM DUNGEON"), font=fl_small, fill=lin(DIM)); d.text((78 * K, 64 * K), "CHOOSE YOUR HERO", font=f_title, fill=lin(INK))
    # ---- her card (laid out twice: measured, then drawn on its panel)
    ax, ay, x = 80 * K, 160 * K, (114 + (18 if (UI and UI.has("panel")) else 0)) * K; wd = 720 * K - x - 30 * K     # (clear of the board's corner ornaments)
    def card(draw):
        y = ay + 22 * K
        if draw: d.text((x, y), h["name"].upper(), font=f_name, fill=ink(acc))
        y += 74 * K
        mh = max(q["hp"] for q in HEROES); mm = max(max(q["mana"] for q in HEROES), 1.0)
        for lab, v, mx, col, note, fr0, fi0 in (("HIT POINTS", h["hp"], mh, (0.25, 0.75, 0.3), "%d" % h["hp"], "bar_health", "fill_health"),
                                                 ("MANA", h["mana"], mm, (0.2, 0.42, 0.95), "%d" % h["mana"] if h["mana"] else "none", "bar_mana", "fill_mana")):
            if UI and UI.has(fr0):
                # (ARDHeroSelectHUD: the painted frame, its fill as far as she has against the strongest)
                bh = 38 * K
                if draw:
                    d.text((x, y + 4 * K), sc(lab), font=fl_small, fill=ink(DIM))
                    a0, a1 = (x + 120 * K, y - 6 * K), (x + wd - 80 * K, y - 6 * K + bh)
                    UI.bar(o, fr0, fi0, a0, a1, UI.height_px(fr0, bh), min(1.0, v / mx), (1, 1, 1, fade), (1, 1, 1, fade))
                    d.text((a1[0] + 12 * K, y + 4 * K), note, font=fx_small, fill=ink(INK))
                y += 44 * K
                continue
            if draw:
                d.text((x, y), sc(lab), font=fl_small, fill=ink(DIM)); b0x, b1x = x + 130 * K, x + wd - 90 * K
                d.rectangle((b0x, y + 2 * K, b1x, y + 20 * K), fill=lin((0.08, 0.08, 0.1), 0.9 * fade))
                d.rectangle((b0x, y + 2 * K, b0x + (b1x - b0x) * min(1.0, v / mx), y + 20 * K), fill=ink(col))
                d.text((b1x + 12 * K, y), note, font=fx_small, fill=ink(INK))
            y += 32 * K
        # her other numbers on one line (ARDHeroSelectHUD): the mana that comes back, her bonuses, the roll
        st = []
        if h["mana"] > 0: st.append(("MANA BACK", "%.1f a second" % h.get("mana_per_second", 0.0)))
        if h.get("melee_bonus", 0) > 0: st.append(("MELEE", "+%.0f%% damage" % (h["melee_bonus"] * 100)))
        if h.get("ranged_bonus", 0) > 0: st.append(("RANGED", "+%.0f%% damage" % (h["ranged_bonus"] * 100)))
        if h.get("roll"): st.append(("DODGE", "roll"))
        sx = x
        for a_, b_ in st:
            if draw: d.text((sx, y), sc(a_), font=fl_small, fill=ink(DIM))
            sx += d.textlength(sc(a_), font=fl_small) + 8 * K
            if draw: d.text((sx, y), b_, font=fx_small, fill=ink(acc))
            sx += d.textlength(b_, font=fx_small) + 28 * K
        if st: y += 28 * K
        y += 14 * K
        def section(s):
            nonlocal y
            if draw:
                d.text((x, y), sc(s), font=fl_small, fill=ink(acc))
                if UI and UI.has("divider"): UI.fit(o, "divider", (x - 6 * K, y + 8 * K), (x + wd + 6 * K, y + 36 * K), (1, 1, 1, fade))
                else: d.rectangle((x, y + 21 * K, x + wd, y + 22 * K), fill=lin(LINE, 0.35 * fade))
            y += 30 * K
        def wrapped(s, ind):
            nonlocal y
            line = ""
            for w_ in s.split():
                tr = (line + " " + w_).strip()
                if d.textlength(tr, font=f_line) > wd - ind and line:
                    if draw: d.text((x + ind, y), line, font=f_line, fill=ink(INK))
                    y += 30 * K; line = w_
                else: line = tr
            if line:
                if draw: d.text((x + ind, y), line, font=f_line, fill=ink(INK))
                y += 34 * K
        section("MAIN ABILITIES")
        for a in h["abilities"]:
            if draw: d.rectangle((x + 4 * K, y + 11 * K, x + 11 * K, y + 18 * K), fill=ink(acc))
            wrapped(a, 24 * K)
        y += 10 * K
        if h["armour"]: section("ARMOUR"); wrapped(h["armour"], 0); y += 10 * K
        if h["starts_with"] or h.get("weapons"):
            section("STARTS WITH")
            if h["starts_with"]: wrapped(h["starts_with"], 0)
            # each weapon and spell: its picture in a slot, its name, what a blow or a cast does with her bonus
            rh = 56 * K
            for w_ in h.get("weapons", []):
                tx = x
                if UI and UI.has(w_["icon"]):
                    if draw:
                        if not UI.fit(o, "slot", (x, y), (x + rh, y + rh), (1, 1, 1, fade)): d.rectangle((x, y, x + rh, y + rh), fill=lin((0.03, 0.035, 0.05), 0.8 * fade), outline=ink(LINE), width=K)
                        UI.fit(o, w_["icon"], (x + 8 * K, y + 8 * K), (x + rh - 8 * K, y + rh - 8 * K), (1, 1, 1, fade))
                    tx = x + rh + 14 * K
                bonus = h.get("melee_bonus", 0) if not w_["spell"] else (h.get("ranged_bonus", 0) if w_["bolt"] else 0.0)
                what = ("%.0f damage a blow, reach %.1f m" % (w_["damage"] * (1 + bonus), w_["reach"] / 100.0) if not w_["spell"] else
                        "%.0f damage a %s, flies %.0f m" % (w_["damage"] * (1 + bonus), "bolt" if w_["bolt"] else "cast", w_["reach"] / 100.0))
                if w_["mana"] > 0: what += ", %.0f mana" % w_["mana"]
                if draw:
                    d.text((tx, y + 2 * K), w_["name"].upper(), font=ft_line, fill=ink(INK))
                    d.text((tx, y + 31 * K), what, font=fx_small, fill=ink(DIM))
                y += rh + 8 * K
        return y
    by = min(card(False) + 18 * K, H * K - 170 * K)
    if UI and UI.has("panel"):
        UI.board(o, "panel", (ax, ay), (720 * K, by), 32 * K); d = ImageDraw.Draw(o, "RGBA")
    else:
        d.rectangle((ax, ay, 720 * K, by), fill=lin((0.03, 0.035, 0.05), 0.82), outline=lin(LINE), width=2 * K)
        d.rectangle((ax, ay, ax + 6 * K, by), fill=ink(acc))
    card(True); d = ImageDraw.Draw(o, "RGBA")
    # ---- the names along the bottom, the arrows, START
    tb, tg, ty, tbh = 210 * K, 14 * K, H * K - 130 * K, 52 * K; n = len(HEROES); t0 = (W * K - (n * tb + (n - 1) * tg)) / 2
    plate = bool(UI and UI.has("button"))
    for i, q in enumerate(HEROES):
        on = i == r["hero"]; p0 = (t0 + i * (tb + tg), ty); p1 = (p0[0] + tb, ty + tbh); qa = tuple(q["accent"])
        if plate:
            UI.nine(o, "button", p0, p1, UI.height_px("button", tbh), tuple(0.75 + c * 0.5 for c in qa) + (1,) if on else (0.55, 0.55, 0.55, 1)); d = ImageDraw.Draw(o, "RGBA")
            if on: d.rectangle((p0[0] + 2 * K, p0[1] + 2 * K, p1[0] - 2 * K, p1[1] - 2 * K), outline=lin(qa), width=2 * K)
        else:
            d.rectangle((*p0, *p1), fill=lin(tuple(c * 0.35 for c in qa), 0.95) if on else lin((0.04, 0.045, 0.06), 0.85), outline=lin(qa) if on else lin((0.40, 0.38, 0.34)), width=(3 if on else 1) * K)
        d.text(((p0[0] + p1[0]) / 2 + (2 * K if plate else 0), (p0[1] + p1[1]) / 2 + (2 * K if plate else 0)), q["name"].upper(), font=f_tab, fill=(0, 0, 0, 200), anchor="mm") if plate else None
        d.text(((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2), q["name"].upper(), font=f_tab, fill=(255, 255, 255, 255) if on else lin(DIM), anchor="mm")
    for j, g in enumerate("<>"):
        px = t0 - tg - 56 * K if j == 0 else t0 + n * tb + (n - 1) * tg + tg
        hot = (r["key"] in ("A", "Left") and j == 0) or (r["key"] in ("D", "Right") and j == 1)
        if UI and UI.has("arrow"):
            # (the painted arrowhead, the left one mirrored; lit while its key is pressed)
            UI.fit(o, "arrow", (px - 4 * K, ty - 4 * K), (px + 60 * K, ty + tbh + 4 * K), (1.5, 1.3, 0.9, 1) if hot else (1, 1, 1, 1), flip=j == 0); d = ImageDraw.Draw(o, "RGBA")
            continue
        d.rectangle((px, ty, px + 56 * K, ty + tbh), fill=lin((0.36, 0.27, 0.10), 0.95) if hot else lin((0.04, 0.045, 0.06), 0.85), outline=lin((1.0, 0.82, 0.35)) if hot else lin(LINE), width=(3 if hot else 1) * K)
        d.text((px + 28 * K, ty + tbh / 2), g, font=f_key, fill=lin(INK), anchor="mm")
    st = "START AS %s" % h["name"].upper(); tw = d.textlength(st, font=f_cap)
    pressed = 0.0 <= r["start_ago"] < 0.7; pulse = 1.0 if pressed else 0.75 + 0.25 * math.sin(r["t"] * 3.0)
    if plate:
        # (ARDHeroSelectHUD: the plate, lit in her colour, wider for its rim and rivets)
        wide = 50 * K; p1 = (W * K - 80 * K + wide / 2, H * K - 170 * K + wide / 4); p0 = (p1[0] - tw - 60 * K - wide, p1[1] - 72 * K - wide / 2)
        k_ = 1.0 if pressed else pulse
        UI.nine(o, "button", p0, p1, UI.height_px("button", p1[1] - p0[1]), tuple(0.6 + c * (0.9 if pressed else 0.6) * k_ for c in acc) + (1,)); d = ImageDraw.Draw(o, "RGBA")
        d.rectangle((p0[0] + 3 * K, p0[1] + 3 * K, p1[0] - 3 * K, p1[1] - 3 * K), outline=lin((1, 1, 1)) if pressed else lin(acc, 0.5 + 0.5 * pulse), width=(4 if pressed else 2) * K)
        d.text(((p0[0] + p1[0]) / 2 + 2 * K, (p0[1] + p1[1]) / 2 + 2 * K), st, font=f_cap, fill=(0, 0, 0, 200), anchor="mm")
    else:
        p1 = (W * K - 80 * K, H * K - 170 * K); p0 = (p1[0] - tw - 60 * K, p1[1] - 72 * K)
        d.rectangle((*p0, *p1), fill=lin(tuple(c * (0.85 if pressed else 0.45) * pulse for c in acc), 0.95), outline=lin((1, 1, 1)) if pressed else lin(acc), width=(5 if pressed else 3) * K)
    d.text(((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2), st, font=f_cap, fill=(255, 255, 255, 255), anchor="mm")
    keys = "A / D, arrows or wheel  another hero      Enter or Space  start      or click"; tw = d.textlength(keys, font=fx_small)
    d.rectangle((W * K / 2 - tw / 2 - 16 * K, H * K - 62 * K, W * K / 2 + tw / 2 + 16 * K, H * K - 30 * K), fill=lin((0.03, 0.035, 0.05), 0.75))
    d.text((W * K / 2, H * K - 46 * K), keys, font=fx_small, fill=lin(INK), anchor="mm")
    # ---- the reel's own: which hero of four, the key being pressed, the opening title
    if len(ORDER) > 1: d.text((W * K - 80 * K, 46 * K), "HERO %d OF %d" % (k + 1, len(ORDER)), font=f_tab, fill=lin(INK), anchor="ra")
    if r["key"]:
        kc = "ENTER" if r["key"] == "Enter" else r["key"]; kw = (130 if kc == "ENTER" else 64) * K; kx, ky = W * K - 80 * K - kw, 84 * K
        d.rounded_rectangle((kx, ky, kx + kw, ky + 60 * K), 10 * K, fill=(238, 214, 150, 255), outline=(255, 236, 180, 255), width=2 * K)
        d.text((kx + kw / 2, ky + 30 * K), kc, font=f_key, fill=(28, 24, 18, 255), anchor="mm")
        d.text((kx - 14 * K, ky + 30 * K), "start" if kc == "ENTER" else "another hero", font=f_line, fill=(244, 240, 228, 240), anchor="rm")
    if k == 0 and t < 3.4:
        # (the reel's title over the menu, veiled, for its first seconds; the menu comes up from under it)
        a = max(0.0, min(1.0, (3.4 - t) / 0.7))
        v = Image.new("RGBA", o.size, (8, 7, 6, int(215 * a))); dv = ImageDraw.Draw(v, "RGBA")
        dv.text((W * K / 2, 470 * K), TITLE, font=f_big, fill=(255, 255, 255, int(255 * a)), anchor="mm")
        dv.text((W * K / 2, 545 * K), SUB, font=f_capt, fill=(232, 236, 240, int(235 * a)), anchor="mm")
        o.alpha_composite(v); d = ImageDraw.Draw(o, "RGBA")
    # (each passage fades in and out through black)
    edge = min(fl, PASS - 1 - fl)
    if edge < 8: d.rectangle((0, 0, W * K, H * K), fill=(0, 0, 0, int(255 * (1.0 - edge / 8.0))))
    return o.resize((W, H), Image.LANCZOS)

# ---- the frames
os.makedirs(OUT, exist_ok=True)
menu = sorted(glob.glob(os.path.join(WORK, "final_menu", "*.png")))
n_out = 0; layout = []
def put(im):
    global n_out
    im.convert("RGB").save(os.path.join(OUT, "reel.%04d.png" % n_out), compress_level=1); n_out += 1
for k, hero in enumerate(ORDER):
    start = len(layout)
    for fl in range(PASS):
        f = k * PASS + fl
        im = Image.open(menu[min(f, len(menu) - 1)]).convert("RGBA")
        if im.size != (W, H): im = im.resize((W, H), Image.LANCZOS)
        put(Image.alpha_composite(im, menu_hud(f, k, fl)))
    layout.append(("menu", k, n_out - PASS, PASS))
    run = sorted(glob.glob(os.path.join(WORK, HUD + hero.lower(), "*.png")))
    for i, p in enumerate(run):
        im = Image.open(p).convert("RGB")
        n_left = len(run) - 1 - i
        if n_left < 6: im = Image.blend(im, Image.new("RGB", im.size, (0, 0, 0)), 1.0 - n_left / 6.0)        # (out through black to the menu)
        put(im)
    layout.append(("run", hero, n_out - len(run), len(run)))
    print("%s: menu passage %d frames, run %d frames" % (hero, PASS, len(run)))
# ---- the sound
SR = 48000
def load(p):
    sr, a = wavfile.read(p)
    a = a.astype(np.float32) / (32768.0 if a.dtype == np.int16 else 2147483648.0 if a.dtype == np.int32 else 1.0)
    if a.ndim == 1: a = np.stack([a, a], 1)
    if sr != SR:
        x = np.arange(0, len(a), sr / SR); a = np.stack([np.interp(x, np.arange(len(a)), a[:, c]) for c in range(2)], 1).astype(np.float32)
    return a
def rms(a):
    v = np.sqrt(np.mean(a.astype(np.float64) ** 2, axis=1)); v = v[v > 1e-3]
    return float(np.sqrt(np.mean(v ** 2))) if len(v) else 1e-3
def edge_fades(a, sec):
    n = min(int(sec * SR), len(a) // 2); r = np.linspace(0, 1, n, dtype=np.float32)[:, None]
    a[:n] *= r; a[-n:] *= r[::-1]; return a
mus = load(MUSIC); runs = {}
for hero in ORDER:
    wv = glob.glob(os.path.join(WORK, "final_" + hero.lower(), "*.wav"))
    runs[hero] = load(wv[0]) if wv else np.zeros((1, 2), np.float32)
target = np.mean([rms(a) for a in runs.values()])
mus *= 0.8 * target / rms(mus)
out = []; mpos = 0
for kind, what, f0, n in layout:
    ns = int(round(n / FPS * SR))
    if kind == "menu":
        seg = mus[mpos:mpos + ns]; mpos += ns
        if len(seg) < ns: seg = np.concatenate([seg, np.zeros((ns - len(seg), 2), np.float32)])
        out.append(edge_fades(seg.copy(), 0.25))
    else:
        a = runs[what][:ns]
        if len(a) < ns: a = np.concatenate([a, np.zeros((ns - len(a), 2), np.float32)])
        out.append(edge_fades(a.copy(), 0.2))
track = np.concatenate(out); peak = float(np.max(np.abs(track))) or 1.0
track *= min(1.0, 0.89 / peak)
wavfile.write(TRACK, SR, (track * 32767).astype(np.int16))
print("wrote %d frames (%.1f s) to %s and %.1f s of sound to %s | runs levelled to %.4f rms, the menu music under the menu" % (n_out, n_out / FPS, OUT, len(track) / SR, TRACK, target))
