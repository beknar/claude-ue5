"""random_dungeonmagic_level, random_dungeonmagic_level2 and random_dungeonmagic_level3 demo reel HUD (generalised from
rdc_reel_overlay.py; the level is the recording's): composites onto the Movie Render Queue
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
A recording made with the tactical maps on (the generator's bTacticalMaps, every dungeon level since 821; level 3's reel)
gets the tactical minimap instead, as ARDHUD::DrawTacticalMinimap draws it: no frame, a dark backdrop feathered into the
picture, the tiles in dark greys fading to the rim (the rooms she has seen lighter, the rest faint), light lines where a
seen floor meets no floor, a red dot for each monster within 25 m (an orange triangle for the strongest of their tier),
gold stars on the unopened chests and trunks in rooms she has seen, cyan diamonds on the hallway exits toward sections
she has not seen (815 records the markers).
Level 3 (the Rogue): her keys are 1 / 2 (daggers / crossbow), the left mouse button (strike or shoot) and B (roll).
Level 4 (one hero's run of the choice-of-hero reel, 815's cine_<hero>.json): her keys, her mana under her hit points,
her weapons with her bonus, a chip for each potion or food working on her, FOUND when a container gives her something,
what the inventory says, and the inventory itself while she has it open (as the game's HUD draws them).
Level 4 with its painted interface (the sixth argument: rdm4_ui_cut.py --export's folder, which 830 imported): the
status panel, its bars and weapon slots, the effect chips, the minimap's ring, the FOUND plaque and the inventory are
drawn with the painted pieces where the game's HUD draws them (rdm4_ui_draw.py: the same stretch rules as ARDHUD), and
while the big map is open (the record's "mapo") it is drawn as ARDHUD::DrawPaintedMap draws it, the minimap off. Its
lettering is the game's (rdm4_fonts.py's files, the roles of ARDHUD's FRDUIDraw::Text): Cinzel for titles, names, keys and
numbers standing alone, Alegreya for the text, Alegreya SC for labels ("MANA BACK" written "Mana Back": sc()); the reel's
own captions follow the same roles. The other levels keep Segoe UI.
Level 5 (the Summoner's armour reel, 815's cine_summoner.json) is drawn as level 4 is, with what level 5's HUD adds: FOUND
names the first thing a container held "and N more", the inventory has its ARMOUR section (WORN on the set she has on;
scrolled to keep the chosen row in view when the list is longer than the screen, as ARDHUD::DrawInventory does) and her
armour under her hit points, and the captions say what each set is and what it takes off the blows on her.
Level "5c" (the armour table, loot and crafting reel, 815's run5c: cine_craft_<hero>.json) adds what level 5's HUD draws
since 857: the anvils on both maps (a small anvil) and each room's tier (the minimap "T2" in the room, the big map a "TIER 2"
line under the room's name), the inventory's REPAIR ITEMS and MATERIALS sections and each set's durability ("WORN  158 /
210", "WORN OUT"), the repair list a repair item opens (ARDHUD::DrawInventory), the anvil's crafting panel
(ARDHUD::DrawCrafting: the recipes, each part with what she has against what it takes), and the captions of each beat.
Usage: rdm_reel_overlay.py frames_dir out_dir [step] [level: 1, 2, 3, 4, 5, 5h or 5c] [level 4 / 5: hero] [level 4 / 5: ui art dir]"""
import sys, os, re, json, glob, math
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
src, dst = sys.argv[1], sys.argv[2]
step = int(sys.argv[3]) if len(sys.argv) > 3 else 1
LV = sys.argv[4] if len(sys.argv) > 4 else "1"
Q5 = LV == "5h"; C5 = LV == "5c"; LV = "5" if (Q5 or C5) else LV        # ("5h": level 5's four heroes' weapons reel, 815's run5h: cine_quartet_<hero>.json; "5c": run5c, cine_craft_<hero>.json)
L5 = LV == "5"; L4 = LV == "4" or L5     # (level 5: level 4's HUD and the armour)
HERO = sys.argv[5] if len(sys.argv) > 5 else ("Summoner" if L5 else "Rogue")            # (level 4: whose run: 815 wrote cine_<hero>.json)
UI = None
if L4 and len(sys.argv) > 6:
    from rdm4_ui_draw import UIArt
    UI = UIArt(sys.argv[6])
def wicon(name): return UI.weapons.get("%s/%s" % (HERO, name)) if UI else None
def iicon(name): return UI.icons.get(name) if UI else None
L2, L3 = LV == "2" or (L4 and HERO == "Warlock"), LV == "3" or (L4 and HERO == "Rogue")
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "random_dungeon_magic" + ("" if LV == "1" else LV))
SND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "random_dungeon_combat")      # (the sounds are the combat level's)
R = json.load(open(os.path.join(SRC, (f"cine_quartet_{HERO.lower()}.json" if Q5 else f"cine_craft_{HERO.lower()}.json" if C5 else f"cine_{HERO.lower()}.json") if L4 else "cine_render.json"), encoding="utf-8"))
W5 = L5 and (HERO == "Warrior" or Q5 or C5)          # (level 5's weapons and tiers reels: 815's run5w, the Warrior; run5h, any of four; run5c's tiers too)
# (who wields what: the weapons table's rules, weapons_table.json "who")
WHO = {"Warrior": "the Warrior wields every weapon of the table", "Warlock": "the Warlock wields every weapon of the table",
       "Rogue": "the Rogue wields short blades and ranged weapons only", "Mage": "the Mage wields none of the table's weapons: her spells are hers",
       "Summoner": "the Summoner wields none of the table's weapons"}
HJ = ({h["name"]: h for h in json.load(open(os.path.join(SRC, "heroes.json")))["heroes"]} if LV == "4" else
      {h["name"]: h for h in json.load(open(os.path.join(SRC, "..", "random_dungeon_magic4", "heroes.json")))["heroes"]} if W5 else
      {"Summoner": json.load(open(os.path.join(SRC, "summoner_hero.json"), encoding="utf-8"))} if L5 else {})
FPS = R["fps"]; ROWS = {r["frame"]: r for r in R["rows"]}; LASTF = max(ROWS); C = R["const"]; EV = R["events"]
TS = C["tile"]; NT = C["section_tiles"]
W, H, K = 1920, 1080, 2                       # the layer is drawn K times larger and scaled down (smooth edges)
def row(f): return ROWS.get(min(max(f, 0), LASTF)) or ROWS[min(ROWS, key=lambda k: abs(k - f))]
HITS = [e for e in EV if e["kind"] == "hit"]; KILLS = [e for e in EV if e["kind"] == "kill"]; FIGHTS = [e for e in EV if e["kind"] == "fight"]
GENS = [e for e in EV if e["kind"] == "generated"]; DISC = [e for e in EV if e["kind"] == "discovered"]; CHESTS = [e for e in EV if e["kind"] == "chest"]
CASTS = [e for e in EV if e["kind"] == "cast"]; SPELL = C["spell"]; ROLLS = [e for e in EV if e["kind"] == "rolled"]; DODGED = [e for e in EV if e["kind"] == "dodged"]
TACTICAL = C.get("tactical", False)
POIS = sorted((r["frame"], r["pois"]) for r in R["rows"] if r.get("pois") is not None)
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
        elif e["key"] == "Player.Hit.Daggers": HEARD.append((e["t"], "the dagger bites"))
        elif e["key"] == "Player.Charge.Crossbow": HEARD.append((e["t"], "she raises the crossbow"))
        elif e["key"] == "Player.Cast.Crossbow": HEARD.append((e["t"], "the crossbow snaps"))
        elif e["key"] == "Player.Hit.Crossbow": HEARD.append((e["t"], "the bolt strikes"))
        elif e["key"] == "Player.Roll": HEARD.append((e["t"], "she rolls"))
        elif e["key"] == "Player.Charge.Dark Fire": HEARD.append((e["t"], "dark fire gathers in her hand"))
        elif e["key"] == "Player.Cast.Dark Fire": HEARD.append((e["t"], "the dark fire roars away"))
        elif e["key"] == "Player.Hit.Dark Fire": HEARD.append((e["t"], "the dark fire bursts"))
        elif e["key"] == "Player.Loot": HEARD.append((e["t"], "she takes what it held"))
        elif e["key"] == "Player.Drink": HEARD.append((e["t"], "she drinks"))
        elif e["key"] == "Player.Eat": HEARD.append((e["t"], "she eats"))
        elif e["key"] == "Player.Inventory": HEARD.append((e["t"], "her bag rustles"))
        elif e["key"] == "Player.NoMana": HEARD.append((e["t"], "not enough mana"))
    elif e["kind"] == "door": HEARD.append((e["t"], "a door creaks open"))
    elif e["kind"] == "chest": HEARD.append((e["t"], "the %s creaks open" % e["what"].split()[-1]))
HEARD.sort()
# ---- level 4: what she found, used and was told, the inventory's lines as they were
FOUND = [e for e in EV if e["kind"] == "found"]; USED = [e for e in EV if e["kind"] == "used"]; INVS = [e for e in EV if e["kind"] == "inventory"]
LINES = [e for e in EV if e["kind"] == "lines"]; MSGS = [e for e in EV if e["kind"] == "message" and e["t"] > 0.3]     # (not one left from before the restart)
WORN = [e for e in EV if e["kind"] == "worn"]; BLOWS = [e for e in EV if e["kind"] == "blow_on_her"]       # (level 5)
ITEMS = {it["name"]: it for it in C.get("items", [])}
# (run5h: for her fights the pilot lets the monsters notice her from farther than in play; the first fight after says so)
LURES = [e for e in EV if e["kind"] == "lure" and e.get("on")]
def wears_line(it):
    """(run5h) what her hero wears, and the set's weight: why it goes on or not"""
    ws = [x for x in ("light", "medium", "heavy") if x in (C.get("wears") or [])]
    who = "the %s wears %s" % (HERO.lower(), "no armour" if not ws else ("all armour: light, medium and heavy" if len(ws) == 3 else "only " + " and ".join(ws) + " armour"))
    return "%s  ·  the %s is %s  ·  each set was fitted to the bodies of the heroes who wear its weight" % (who, it.get("name", "set").lower(), it.get("weight", "?"))
def lured(e):
    if not LURES: return None
    first = next((f for f in EV if f["kind"] == "fight" and f["t"] >= LURES[0]["t"]), None)
    if first is None or abs(first["t"] - e["t"]) > 1e-3: return None
    return "for this reel the monsters notice her from %.0f m (in play %.0f m): they come to her" % (LURES[0]["aggro_cm"] / 100.0, LURES[0]["game_aggro_cm"] / 100.0)
# (the weapons reel: her weapons as they were (found ones join, broken ones go, their wear), the tiers' notices, the jump)
WPNS = [e for e in EV if e["kind"] == "weapons"]; TNOTE = [e for e in EV if e["kind"] == "tier_notice" and e["text"]]
# (run5c: the crafting panel's and the repair list's lines as they were; what the reel did, said by the captions)
CRAFTL = [e for e in EV if e["kind"] == "craft_lines"]; REPL = [e for e in EV if e["kind"] == "repair_lines"]
RECIPES = {r_["item"]: r_ for r_ in C.get("recipes", [])}
def tier_of(c): return max(abs(c[0]), abs(c[1])) + 1
TIER_INK = (1.0, 0.78, 0.38)
def last_at(evs, t):
    out = None
    for e in evs:
        if e["t"] <= t + 1e-6: out = e
    return out
def weapons_at(t):
    e = last_at(WPNS, t)
    return e["list"] if e else C["weapons"]
def ev1(kind): return next((e for e in EV if e["kind"] == kind), None)
# (a bow plays the crossbow's sounds (the weapon it is like): what is heard is said by the weapon in her hands)
def drawn_at(t):
    wl = weapons_at(t); i = row(int(t * FPS)).get("w", -1)
    return wl[i]["name"].lower() if 0 <= i < len(wl) else ""
BOWTXT = {"she raises the crossbow": "she draws the bow", "the crossbow snaps": "the arrow flies", "the bolt strikes": "the arrow strikes"}
HEARD = [(t0, BOWTXT.get(s, s) if ("bow" in drawn_at(t0) and "crossbow" not in drawn_at(t0)) else s) for t0, s in HEARD]
def inv_closed_after(t):
    """when the inventory was shut again after t (the rows' inv flag)"""
    f = next((k for k in sorted(ROWS) if k > t * FPS and ROWS[k].get("inv", [0])[0] == 0), None)
    return f / FPS if f is not None else t + 1.8
JUMP, AT_GRATING = ev1("jump"), ev1("at_grating")
OPENED = next((e for e in TNOTE if "IS OPEN" in e["text"]), None)
WEAR_SET, BROKE, LAST_M = ev1("wear_set"), ev1("broke"), ev1("last_monster")
CARD = (JUMP["t"], AT_GRATING["t"] + 3.0) if (JUMP and AT_GRATING) else None      # (the card over the reel's shortcut; 815 waits 3.4 s at the grating)
LANDED = ev1("landed")
if C5 and JUMP and LANDED: CARD = (JUMP["t"], LANDED["t"] + 3.0)                       # (run5c: the card over the jump into tier 2)
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
# ---- level 4 with its painted interface: the game's lettering (sizes as the HUD's: Alegreya a tenth larger than the
# Segoe UI it replaces, for the same x-height; Cinzel's capitals are as tall)
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "random_dungeon_magic4", "fonts")
LETTERS = bool(UI) and os.path.exists(os.path.join(FD, "Cinzel-700.ttf"))
def lfont(fn, size): return ImageFont.truetype(os.path.join(FD, fn + ".ttf"), int(size * K))
_FIT = {}
def fit_font(fn, size, k):
    """a face at size x k (k in twentieths): a name fitted to its slot"""
    q = round(k * 20) / 20.0
    if (fn, size, q) not in _FIT: _FIT[(fn, size, q)] = lfont(fn, size * q)
    return _FIT[(fn, size, q)]
def sc(s):
    """a label for the small-capitals face (FRDUIDraw's RDUISmallCaps): a word of three letters or more written in capitals
    keeps its first and lowers the rest"""
    if not LETTERS: return s
    return re.sub(r"[^\W\d_]{3,}", lambda m: m.group(0)[0] + m.group(0)[1:].lower() if m.group(0).isupper() else m.group(0), s)
if LETTERS:
    f_title, f_head, f_num, f_ban = lfont("Cinzel-700", 40), lfont("Cinzel-700", 30), lfont("Cinzel-700", 30), lfont("Cinzel-700", 30)
    f_sub, f_line, f_small, f_tiny = lfont("Alegreya-500", 26), lfont("Alegreya-500", 26), lfont("Alegreya-500", 19), lfont("Alegreya-500", 15.5)
    fl_small, fl_tiny, ft_small, ft_tiny = lfont("AlegreyaSC-700", 18), lfont("AlegreyaSC-700", 15), lfont("Cinzel-700", 17), lfont("Cinzel-700", 14)
else:
    fl_small, fl_tiny, ft_small, ft_tiny = f_small, f_tiny, f_small, f_tiny
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
TAC = {"room": (0.15, 0.16, 0.17, 0.95), "hall": (0.115, 0.12, 0.13, 0.95), "unknown": (0.055, 0.058, 0.064, 0.7), "wall": (0.36, 0.385, 0.41, 0.9), "fresh": (0.16, 0.32, 0.36),
       "red": (1.0, 0.16, 0.10), "elite": (1.0, 0.55, 0.08), "gold": (1.0, 0.82, 0.22), "exit": (0.25, 0.95, 1.0)}
DISC_IM = {}
def pois_at(f):
    """the markers 815 recorded nearest before frame f (every third frame)"""
    best = None
    for fr, ps in POIS:
        if fr > f: break
        best = ps
    return best or []
def tactical(o, r, t, maps, disc, cx, cy, R, half, ua, under=None):
    """ARDHUD::DrawTacticalMinimap: centred on (cx, cy) layer pixels, radius R, `half` cm from the middle to the rim"""
    d = ImageDraw.Draw(o, "RGBA"); px0, py0 = r["p"][0], r["p"][1]; k = R / half; Tp = TS * k
    ToS = lambda wx, wy: (cx + (wy - py0) * k, cy - (wx - px0) * k)
    fade_ = lambda x, y: max(0.0, min(1.0, (1.0 - math.hypot(x - cx, y - cy) / R) / 0.38))
    # the backdrop: a dark disc whose alpha falls off to its rim (1.3 R), no frame
    B = int(R * 2.6); c0 = B / 2.0; key = (B, round(ua, 2))
    if key not in DISC_IM:                      # (made once: the same disc every frame)
        disc_im = Image.new("RGBA", (B, B), (0, 0, 0, 0)); px = disc_im.load(); col = lin((0.004, 0.005, 0.007))[:3]
        for yy in range(B):
            for xx in range(B):
                q = math.hypot(xx + 0.5 - c0, yy + 0.5 - c0) / c0
                if q < 1.0:
                    u = min(1.0, max(0.0, (q - 0.4) / 0.6)); a = 1.0 - u * u * (3 - 2 * u)
                    px[xx, yy] = col + (int(255 * a * 0.92 * ua),)
        DISC_IM[key] = disc_im
    disc_im = DISC_IM[key]
    o.alpha_composite(disc_im, (int(cx - c0), int(cy - c0))); d = ImageDraw.Draw(o, "RGBA")
    # the tiles: 1 generated, 2 seen, 4 hallway
    tiles = {}
    for c, m in maps.items():
        seen = disc.get(c, set())
        for i, q in enumerate(m["rects"]):
            fl = 1 | (2 if i in seen else 0) | (4 if q[5] else 0)
            for X in range(q[0], q[2]):
                for Y in range(q[1], q[3]): tiles[(X, Y)] = tiles.get((X, Y), 0) | fl
    fresh = set()
    for e in GENS:
        if 0.0 <= t - e["t"] < 4.0:
            for c, m in maps.items():
                if abs(m["t"] - e["t"]) < 1.0 and c != (0, 0): fresh.add(c)
    sec_of = lambda X, Y: (int(math.floor(((X + 0.5) * TS) / (NT * TS) + 0.5)), int(math.floor(((Y + 0.5) * TS) / (NT * TS) + 0.5)))
    n = int(half / TS) + 2; X0, Y0 = int(math.floor(px0 / TS)), int(math.floor(py0 / TS))
    edges = []
    for X in range(X0 - n, X0 + n + 1):
        for Y in range(Y0 - n, Y0 + n + 1):
            v = tiles.get((X, Y))
            if not v: continue
            sx, sy = ToS((X + 0.5) * TS, (Y + 0.5) * TS); a = fade_(sx, sy)
            if a <= 0: continue
            cc = (TAC["hall"] if v & 4 else TAC["room"]) if v & 2 else TAC["unknown"]
            if fresh and sec_of(X, Y) in fresh: cc = TAC["fresh"] + (cc[3],)
            h = Tp * 0.5 + 0.5 * K
            d.rectangle((sx - h, sy - h, sx + h, sy + h), fill=lin(cc[:3], cc[3] * a * ua))
            if not v & 2: continue
            for nb, (a0, b0) in (((X + 1, Y), ((X + 1, Y), (X + 1, Y + 1))), ((X - 1, Y), ((X, Y), (X, Y + 1))), ((X, Y + 1), ((X, Y + 1), (X + 1, Y + 1))), ((X, Y - 1), ((X, Y), (X + 1, Y)))):
                if nb not in tiles: edges.append((ToS(a0[0] * TS, a0[1] * TS), ToS(b0[0] * TS, b0[1] * TS), a))
    for p0, p1, a in edges: d.line((p0, p1), fill=lin(TAC["wall"][:3], TAC["wall"][3] * a * ua), width=max(1, int(1.4 * K)))
    # the markers, bright over the dark ground (chests only in rooms she has seen)
    inside = lambda x, y: math.hypot(x - cx, y - cy) <= R * 0.94
    def poly(pts, c, edge):
        d.polygon(pts, fill=lin(c, ua)); d.line(pts + [pts[0]], fill=lin(edge, ua), width=max(1, int(1.2 * K)))
    for wx, wy, kind in pois_at(int(round(t * FPS))):
        x, y = ToS(wx, wy)
        if not inside(x, y): continue
        if kind == 2 and tiles.get((int(math.floor(wx / TS)), int(math.floor(wy / TS))), 0) & 2:
            s_ = 6.5 * K; pts = [(x + math.cos(-math.pi / 2 + j * math.pi / 5) * (s_ if j % 2 == 0 else s_ * 0.45), y + math.sin(-math.pi / 2 + j * math.pi / 5) * (s_ if j % 2 == 0 else s_ * 0.45)) for j in range(10)]
            poly(pts, TAC["gold"], (1.0, 0.97, 0.8))
        elif kind == 3:
            s_ = 5.5 * K; poly([(x, y - s_), (x + s_ * 0.75, y), (x, y + s_), (x - s_ * 0.75, y)], TAC["exit"], (0.85, 1.0, 1.0))
        elif kind == 5:
            # (level 5: a sealed passage, ARDHUD::SealMark: a red cross on a dark spot)
            s_ = 5.0 * K; rr = s_ * 1.7; d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(0, 0, 0, int(140 * ua)))
            for a0, b0 in (((x - s_, y - s_), (x + s_, y + s_)), ((x - s_, y + s_), (x + s_, y - s_))): d.line((a0, b0), fill=lin((1.0, 0.22, 0.16), ua), width=max(2, int(s_ * 0.38)))
        elif kind == 6 and tiles.get((int(math.floor(wx / TS)), int(math.floor(wy / TS))), 0) & 2:
            d = anvil_mark(o, d, x, y, 10.0 * K, ua)          # (level 5: an anvil she has seen)
    if C5:
        # (level 5: each room she has found writes its tier, small, in its middle: ARDHUD::DrawTacticalMinimap)
        for c, m in maps.items():
            seen = disc.get(c, set())
            for i, q in enumerate(m["rects"]):
                if i not in seen or q[5] or q[4] == "JUNCTION": continue
                x, y = ToS((q[0] + q[2]) * 0.5 * TS, (q[1] + q[3]) * 0.5 * TS)
                if math.hypot(x - cx, y - cy) > R * 0.86 or fade_(x, y) < 0.3: continue
                a_ = fade_(x, y)
                d.text((x + K, y + K), "T%d" % tier_of(c), font=fl_tiny, fill=(0, 0, 0, int(205 * a_ * ua)), anchor="mm")
                d.text((x, y), "T%d" % tier_of(c), font=fl_tiny, fill=lin(TIER_INK, a_ * ua), anchor="mm")
    for mo in r["mon"]:
        if mo[8] or math.hypot(mo[2] - px0, mo[3] - py0) > 2500.0: continue
        x, y = ToS(mo[2], mo[3])
        if not inside(x, y): continue
        elite = len(mo) > 12 and mo[12]
        c = TAC["elite"] if elite else TAC["red"]
        for rr, al in ((11.0 if elite else 9.0, 0.12), (7.0, 0.2)): d.ellipse((x - rr * K, y - rr * K, x + rr * K, y + rr * K), fill=lin(c, al * ua))
        if elite: s_ = 7.0 * K; poly([(x, y - s_), (x + s_ * 0.9, y + s_ * 0.65), (x - s_ * 0.9, y + s_ * 0.65)], c, (1.0, 0.9, 0.6))
        else: rr = 4.6 * K; d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=lin(c, ua))
    a = math.radians(r["yaw"] - 90.0); fx, fy = math.cos(a), math.sin(a); s_ = 9.0 * K
    tri = [(cx + fx * s_, cy + fy * s_), (cx - fx * s_ * 0.6 - fy * s_ * 0.6, cy - fy * s_ * 0.6 + fx * s_ * 0.6), (cx - fx * s_ * 0.6 + fy * s_ * 0.6, cy - fy * s_ * 0.6 - fx * s_ * 0.6)]
    d.polygon(tri, fill=lin((1.0, 0.47, 0.67), ua)); d.line(tri + [tri[0]], fill=(255, 255, 255, int(255 * ua)), width=2 * K)
    ink = lin((0.75, 0.77, 0.8), 0.85 * ua)
    d.text((cx, cy - R * 0.98), "N", font=ft_small, fill=ink, anchor="ma")
    rooms = sum(1 for m in maps.values() for q in m["rects"] if not q[5]); seen = sum(1 for c, m in maps.items() for i, q in enumerate(m["rects"]) if not q[5] and i in disc.get(c, set()))
    d.text((cx, cy + max(R * 0.96, under or 0)), "%d / %d rooms    M  map" % (seen, rooms), font=f_small, fill=ink, anchor="ma")
    if W5 and r.get("tier"):
        # (level 5: the tiers, ARDHUD::DrawTiers: her tier and its sets cleared, what is left in her set, when the next opens)
        tr = r["tier"]; t_, done, size, rx_, rn, cl_, cn, kl, mn, clr, opn, mx = tr
        ls = [("TIER %d  ·  SETS CLEARED %d / %d" % (t_, done, size), (1.0, 0.82, 0.35))]
        if rn >= 0: ls.append(("this set of rooms is cleared" if clr else "rooms %d/%d   chests %d/%d   monsters %d/%d" % (rx_, rn, cl_, cn, kl, mn), (0.45, 0.95, 0.5) if clr else (0.86, 0.84, 0.78)))
        ls.append(("tier %d opens when all of tier %d is cleared" % (opn + 1, opn) if opn < mx else "all %d tiers are open" % mx, (0.7, 0.72, 0.75)))
        y = cy + max(R * 0.96, under or 0) + 30 * K; wmax = max(d.textlength(sc(s), font=fl_small) for s, _ in ls)
        d.rectangle((cx - wmax / 2 - 10 * K, y - 4 * K, cx + wmax / 2 + 10 * K, y + 26 * K * len(ls) + 4 * K), fill=(5, 5, 8, int(140 * ua)))
        for s, c in ls:
            d.text((cx, y), sc(s), font=fl_small, fill=lin(c, ua), anchor="ma"); y += 26 * K
ANVIL_SHAPE = [(-1.0, -0.32), (-0.45, -0.52), (0.85, -0.52), (0.85, -0.14), (0.35, -0.08), (0.22, 0.22), (0.55, 0.42), (0.55, 0.58), (-0.55, 0.58),
               (-0.55, 0.42), (-0.22, 0.22), (-0.32, -0.08), (-0.62, -0.12)]
def anvil_mark(o, d, x, y, rr, ua):
    """ARDHUD::AnvilMark: a dark spot, a warm glow, the painted anvil (map_anvil) or a drawn one; returns a fresh ImageDraw"""
    d.ellipse((x - rr * 1.5, y - rr * 1.5, x + rr * 1.5, y + rr * 1.5), fill=(0, 0, 0, int(127 * ua)))
    d.ellipse((x - rr * 1.25, y - rr * 1.25, x + rr * 1.25, y + rr * 1.25), fill=lin((1.0, 0.62, 0.25), 0.95 * ua))     # (the dark painted anvil on a forge's glow)
    if UI and UI.has("map_anvil"):
        UI.fit(o, "map_anvil", (x - rr * 0.95, y - rr * 0.95), (x + rr * 0.95, y + rr * 0.95), (1, 1, 1, ua)); return ImageDraw.Draw(o, "RGBA")
    pts = [(x + px * rr, y + py * rr) for px, py in ANVIL_SHAPE]
    d.polygon(pts, fill=lin((0.80, 0.82, 0.88), ua)); d.line(pts + [pts[0]], fill=lin((0.12, 0.12, 0.14), ua), width=max(1, int(1.2 * K)))
    return d
def blend_box(o, box, radius, fill, outline=None, width=0):
    """a rounded box blended over what is drawn already (ImageDraw on an RGBA image replaces the pixels: over the big map's
    board a see-through box would cut a hole in it)"""
    x0, y0, x1, y1 = (int(round(v)) for v in box)
    if x1 <= x0 or y1 <= y0: return
    small = Image.new("RGBA", (x1 - x0 + 1, y1 - y0 + 1), (0, 0, 0, 0))
    ImageDraw.Draw(small, "RGBA").rounded_rectangle((0, 0, x1 - x0, y1 - y0), radius, fill=fill, outline=outline, width=width)
    o.alpha_composite(small, (x0, y0))
VIGNETTE = {}
# (the rooms' names as ARDDungeonGenerator::KindName gives them, by the kind the record holds; the face of the labels)
ROOM_NAMES = {"HALL": "Great hall", "BARRACKS": "Barracks", "PRISON": "Prison cells", "TORTURE": "Torture chamber", "STOREROOM": "Storeroom", "ARMORY": "Armory",
              "KITCHEN": "Kitchen", "LIBRARY": "Library", "CHAPEL": "Chapel", "CRYPT": "Crypt", "TREASURY": "Treasury", "GUARD_ROOM": "Guard room", "FORGE": "Forge"}
ROOM_FONTS = {}
def lfont_room(sz):
    k = round(sz, 1)
    if k not in ROOM_FONTS: ROOM_FONTS[k] = lfont("AlegreyaSC-700", k) if LETTERS else font("seguisb.ttf", k)
    return ROOM_FONTS[k]
def painted_map(o, r, t, maps, disc, ua):
    """ARDHUD::DrawPaintedMap (level 4, the big map open): the wide board round a 900 x 880 area in the middle, its leather
    darkened by the minimap's feathered disc stretched over the area, the minimap's tiles (snapped to whole pixels) and lit
    walls fading out toward the board, the doorways, the markers, her arrow, the plaque, the compass, the key, the rooms"""
    import numpy as np
    A_, B_ = (W * K / 2 - 450 * K, 104 * K), (W * K / 2 + 450 * K, H * K - 96 * K)
    cx, cy = (A_[0] + B_[0]) / 2, (A_[1] + B_[1]) / 2; hx, hy = (B_[0] - A_[0]) / 2, (B_[1] - A_[1]) / 2
    UI.board(o, "panel_wide", A_, B_, 40 * K, (1, 1, 1, ua))
    vw, vh = int(hx * 2.24), int(hy * 2.24)
    if (vw, vh) not in VIGNETTE:
        yy, xx = np.mgrid[0:vh, 0:vw]
        q = np.hypot((xx + 0.5 - vw / 2) / (vw / 2), (yy + 0.5 - vh / 2) / (vh / 2))
        u = np.clip((q - 0.4) / 0.6, 0, 1); VIGNETTE[(vw, vh)] = np.where(q < 1, 1 - u * u * (3 - 2 * u), 0.0) * 0.9
    al = VIGNETTE[(vw, vh)]; rgba = np.zeros((vh, vw, 4), np.uint8); rgba[..., :3] = lin((0.004, 0.005, 0.007))[:3]; rgba[..., 3] = (al * 255 * ua).astype(np.uint8)
    o.alpha_composite(Image.fromarray(rgba, "RGBA"), (int(cx - vw / 2), int(cy - vh / 2)))
    # (the terrain, doorways, markers and arrow on a layer of their own, laid over the board after: ImageDraw replaces an
    # RGBA image's pixels instead of blending, and see-through tiles drawn on the board would cut holes in it)
    lay = Image.new("RGBA", o.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA")
    k = (B_[1] - A_[1]) / (110.0 * 100.0); px0, py0 = r["p"][0], r["p"][1]
    ToS = lambda wx, wy: (cx + (wy - py0) * k, cy - (wx - px0) * k)
    fade_ = lambda x, y: max(0.0, min(1.0, (1.0 - math.hypot((x - cx) / hx, (y - cy) / hy)) / 0.24))
    tiles = {}
    for c, m in maps.items():
        seen = disc.get(c, set())
        for i, q in enumerate(m["rects"]):
            fl = 1 | (2 if i in seen else 0) | (4 if q[5] else 0)
            for X in range(q[0], q[2]):
                for Y in range(q[1], q[3]): tiles[(X, Y)] = tiles.get((X, Y), 0) | fl
    fresh = set()
    for e in GENS:
        if 0.0 <= t - e["t"] < 4.0:
            for c, m in maps.items():
                if abs(m["t"] - e["t"]) < 1.0 and c != (0, 0): fresh.add(c)
    sec_of = lambda X, Y: (int(math.floor(((X + 0.5) * TS) / (NT * TS) + 0.5)), int(math.floor(((Y + 0.5) * TS) / (NT * TS) + 0.5)))
    nX, nY = int(hy / k / TS) + 2, int(hx / k / TS) + 2; X0, Y0 = int(math.floor(px0 / TS)), int(math.floor(py0 / TS))
    edges = []
    for X in range(X0 - nX, X0 + nX + 1):
        for Y in range(Y0 - nY, Y0 + nY + 1):
            v = tiles.get((X, Y))
            if not v: continue
            sx, sy = ToS((X + 0.5) * TS, (Y + 0.5) * TS); a = fade_(sx, sy)
            if a <= 0: continue
            cc = (TAC["hall"] if v & 4 else TAC["room"]) if v & 2 else TAC["unknown"]
            if fresh and sec_of(X, Y) in fresh: cc = TAC["fresh"] + (cc[3],)
            qa, qb = ToS(X * TS, Y * TS), ToS((X + 1) * TS, (Y + 1) * TS)
            x0, y0, x1, y1 = round(min(qa[0], qb[0])), round(min(qa[1], qb[1])), round(max(qa[0], qb[0])), round(max(qa[1], qb[1]))
            if x1 > x0 and y1 > y0: d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=lin(cc[:3], cc[3] * a * ua))
            if not v & 2: continue
            for nb, (a0, b0) in (((X + 1, Y), ((X + 1, Y), (X + 1, Y + 1))), ((X - 1, Y), ((X, Y), (X, Y + 1))), ((X, Y + 1), ((X, Y + 1), (X + 1, Y + 1))), ((X, Y - 1), ((X, Y), (X + 1, Y)))):
                if nb not in tiles: edges.append((ToS(a0[0] * TS, a0[1] * TS), ToS(b0[0] * TS, b0[1] * TS), a))
    for p0, p1, a in edges: d.line((p0, p1), fill=lin(TAC["wall"][:3], TAC["wall"][3] * a * ua), width=max(1, int(1.6 * K)))
    # doorways of the rooms she has found
    for c, m in maps.items():
        for dx_, dy_ in m["doors"]:
            q = ToS(dx_, dy_); a = fade_(*q)
            if a <= 0: continue
            va = tiles.get((int(math.floor((dx_ + 30) / TS)), int(math.floor((dy_ + 30) / TS))), 0); vb = tiles.get((int(math.floor((dx_ - 30) / TS)), int(math.floor((dy_ - 30) / TS))), 0)
            if not (va & 2 or vb & 2): continue
            on_x = abs(dx_ / TS - round(dx_ / TS)) < abs(dy_ / TS - round(dy_ / TS))
            hv = (0.0, TS * 0.36) if on_x else (TS * 0.36, 0.0)
            d.line((ToS(dx_ - hv[0], dy_ - hv[1]), ToS(dx_ + hv[0], dy_ + hv[1])), fill=lin((1.0, 0.90, 0.50), 0.9 * a * ua), width=max(1, int(2.5 * K)))
    # the names of the rooms she has found (ARDHUD::DrawPaintedMap): the labels' small capitals in the middle of each room,
    # on two lines when one is too wide, smaller when that is too, left out when nothing fits; faded toward the board
    for c, m in maps.items():
        seen = disc.get(c, set())
        for i, q in enumerate(m["rects"]):
            if i not in seen or q[5] or q[4] == "JUNCTION": continue
            qa, qb = ToS(q[0] * TS, q[1] * TS), ToS(q[2] * TS, q[3] * TS)
            lo, hi = (min(qa[0], qb[0]), min(qa[1], qb[1])), (max(qa[0], qb[0]), max(qa[1], qb[1])); mx, my = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
            a = fade_(mx, my)
            if not (A_[0] <= mx <= B_[0] and A_[1] <= my <= B_[1]) or a < 0.25: continue
            lines = [sc(ROOM_NAMES.get(q[4], q[4].replace("_", " ")).upper())]; rw, rh_ = hi[0] - lo[0] - 10 * K, hi[1] - lo[1] - 6 * K
            tl = sc("TIER %d" % tier_of(c)) if C5 else None            # (level 5: a line under the name with the room's tier, a little smaller)
            sz = 18.0
            if d.textlength(lines[0], font=lfont_room(sz)) > rw and " " in lines[0]: lines = lines[0].split(" ", 1)
            def fits(sz_):
                f1, f2 = lfont_room(sz_), lfont_room(sz_ * 0.8)
                wmax = max([d.textlength(x, font=f1) for x in lines] + ([d.textlength(tl, font=f2)] if tl else []))
                return wmax <= rw and f1.size * 1.2 * len(lines) + (f2.size * 1.2 if tl else 0) <= rh_
            for _ in range(6):
                if fits(sz): break
                sz *= 0.88
            if not fits(sz): continue
            f_ = lfont_room(sz); f2 = lfont_room(sz * 0.8)
            lh = f_.size * 1.05; nl = len(lines) + (0.9 if tl else 0); y0 = my - lh * (nl - 1) / 2
            for j, x in enumerate(lines):
                d.text((mx + 1.5 * K, y0 + j * lh + 1.5 * K), x, font=f_, fill=(0, 0, 0, int(215 * a * ua)), anchor="mm")
                d.text((mx, y0 + j * lh), x, font=f_, fill=lin((0.90, 0.82, 0.62), a * ua), anchor="mm")
            if tl:
                yt = y0 + len(lines) * lh - lh * 0.1
                d.text((mx + 1.5 * K, yt + 1.5 * K), tl, font=f2, fill=(0, 0, 0, int(215 * a * ua)), anchor="mm")
                d.text((mx, yt), tl, font=f2, fill=lin(TIER_INK, a * ua), anchor="mm")
    def poly(pts, c, edge):
        d.polygon(pts, fill=lin(c, ua)); d.line(pts + [pts[0]], fill=lin(edge, ua), width=max(1, int(1.2 * K)))
    def star(x, y, s_, c): poly([(x + math.cos(-math.pi / 2 + j * math.pi / 5) * (s_ if j % 2 == 0 else s_ * 0.45), y + math.sin(-math.pi / 2 + j * math.pi / 5) * (s_ if j % 2 == 0 else s_ * 0.45)) for j in range(10)], c, (1.0, 0.97, 0.8))
    def diamond(x, y, s_, c): poly([(x, y - s_), (x + s_ * 0.75, y), (x, y + s_), (x - s_ * 0.75, y)], c, (0.85, 1.0, 1.0))
    def tri(x, y, s_, c): poly([(x, y - s_), (x + s_ * 0.9, y + s_ * 0.65), (x - s_ * 0.9, y + s_ * 0.65)], c, (1.0, 0.9, 0.6))
    def soft(x, y, rr, c, a): d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=lin(c, a * ua))
    ok = lambda x, y: A_[0] <= x <= B_[0] and A_[1] <= y <= B_[1] and fade_(x, y) >= 0.3
    for wx, wy, kind in pois_at(int(round(t * FPS))):
        x, y = ToS(wx, wy)
        if not ok(x, y): continue
        if kind == 2 and tiles.get((int(math.floor(wx / TS)), int(math.floor(wy / TS))), 0) & 2: star(x, y, 8.5 * K, TAC["gold"])
        elif kind == 3: diamond(x, y, 7.5 * K, TAC["exit"])
        elif kind == 5 and C5:
            s_ = 7.0 * K; rr = s_ * 1.7; d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(0, 0, 0, int(140 * ua)))
            for a0, b0 in (((x - s_, y - s_), (x + s_, y + s_)), ((x - s_, y + s_), (x + s_, y - s_))): d.line((a0, b0), fill=lin((1.0, 0.22, 0.16), ua), width=max(2, int(s_ * 0.38)))
        elif kind == 6 and C5 and tiles.get((int(math.floor(wx / TS)), int(math.floor(wy / TS))), 0) & 2: d = anvil_mark(lay, d, x, y, 13.0 * K, ua)
    for mo in r["mon"]:
        if mo[8] or math.hypot(mo[2] - px0, mo[3] - py0) > 2500.0: continue
        x, y = ToS(mo[2], mo[3])
        if not ok(x, y): continue
        if len(mo) > 12 and mo[12]: soft(x, y, 13 * K, TAC["elite"], 0.18); tri(x, y, 8.5 * K, TAC["elite"])
        else: soft(x, y, 11 * K, TAC["red"], 0.18); soft(x, y, 5.5 * K, TAC["red"], 1.0)
    a = math.radians(r["yaw"] - 90.0); fx, fy = math.cos(a), math.sin(a); s_ = 12.0 * K
    tr = [(cx + fx * s_, cy + fy * s_), (cx - fx * s_ * 0.6 - fy * s_ * 0.6, cy - fy * s_ * 0.6 + fx * s_ * 0.6), (cx - fx * s_ * 0.6 + fy * s_ * 0.6, cy - fy * s_ * 0.6 - fx * s_ * 0.6)]
    d.polygon(tr, fill=lin((1.0, 0.47, 0.67), ua)); d.line(tr + [tr[0]], fill=(255, 255, 255, int(255 * ua)), width=2 * K)
    o.alpha_composite(lay); d = ImageDraw.Draw(o, "RGBA")
    # the plaque, the compass (an N over its gem), the key, the rooms and the key that closes it
    gold, ink = lin((1.0, 0.84, 0.45), ua), lin((0.86, 0.82, 0.72), 0.95 * ua)
    title = "DUNGEON MAP"; tw = d.textlength(title, font=f_head); ph = 58 * K
    t0, t1 = (cx - tw / 2 - 90 * K, A_[1] + 6 * K), (cx + tw / 2 + 90 * K, A_[1] + 6 * K + ph)
    if UI.has("banner"): UI.nine(o, "banner", t0, t1, UI.height_px("banner", ph), (1, 1, 1, ua)); d = ImageDraw.Draw(o, "RGBA")
    d.text((cx + 2 * K, (t0[1] + t1[1]) / 2 + 2 * K), title, font=f_head, fill=(0, 0, 0, int(200 * ua)), anchor="mm"); d.text((cx, (t0[1] + t1[1]) / 2), title, font=f_head, fill=gold, anchor="mm")
    cz = 118 * K
    if UI.fit(o, "compass", (B_[0] - 40 * K - cz, A_[1] + 46 * K), (B_[0] - 40 * K, A_[1] + 46 * K + cz), (1, 1, 1, ua)):
        d = ImageDraw.Draw(o, "RGBA"); d.text((B_[0] - 40 * K - cz / 2, A_[1] + 45 * K), "N", font=ft_small, fill=gold, anchor="md")
    x, y = A_[0] + 44 * K, B_[1] - (166 + (23 + 23 if C5 else 0)) * K       # (level 5: the sealed passages and the anvils, a line each)
    d.text((x - 6 * K, y - 30 * K), sc("KEY"), font=fl_small, fill=gold)
    if UI.fit(o, "divider", (x - 14 * K, y - 14 * K), (x + 200 * K, y + 2 * K), (1, 1, 1, ua)): d = ImageDraw.Draw(o, "RGBA")
    for kind, what in ((0, "monster"), (1, "elite"), (2, "unlooted chest or trunk"), (3, "unexplored passage"), (4, "door")) + (((5, "sealed passage"), (6, "anvil: make repair items")) if C5 else ()):
        mx, my = x + 6 * K, y + 10 * K
        if kind == 0: soft(mx, my, 5.5 * K, TAC["red"], 1.0)
        elif kind == 1: tri(mx, my, 7.5 * K, TAC["elite"])
        elif kind == 2: star(mx, my, 7.5 * K, TAC["gold"])
        elif kind == 3: diamond(mx, my, 6.5 * K, TAC["exit"])
        elif kind == 5:
            s_ = 6.0 * K; d.ellipse((mx - s_ * 1.7, my - s_ * 1.7, mx + s_ * 1.7, my + s_ * 1.7), fill=(0, 0, 0, int(140 * ua)))
            for a0, b0 in (((mx - s_, my - s_), (mx + s_, my + s_)), ((mx - s_, my + s_), (mx + s_, my - s_))): d.line((a0, b0), fill=lin((1.0, 0.22, 0.16), ua), width=max(2, int(s_ * 0.38)))
        elif kind == 6: d = anvil_mark(o, d, mx, my, 9.0 * K, ua)
        else: d.line(((mx - 7 * K, my), (mx + 7 * K, my)), fill=lin((1.0, 0.90, 0.50), ua), width=int(2.5 * K))
        d.text((x + 24 * K, y), what, font=f_small, fill=ink); y += 23 * K
    rooms = sum(1 for m in maps.values() for q in m["rects"] if not q[5]); seen = sum(1 for c, m in maps.items() for i, q in enumerate(m["rects"]) if not q[5] and i in disc.get(c, set()))
    d.text((cx, B_[1] - 34 * K), "%d / %d rooms found      Arrows  scroll      C  centre      M  close" % (seen, rooms), font=f_small, fill=ink, anchor="ma")
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
def stylised(o, r, t, maps, disc, P, x0, y0, ua, A):
    """the stylised minimap in its frame (the combat level's look, before the tactical maps)"""
    d = ImageDraw.Draw(o, "RGBA")
    d.rectangle((x0 - 8 * K, y0 - 34 * K, x0 + P + 8 * K, y0 + P + 30 * K), fill=lin((0.04, 0.05, 0.07), A(0.72)))
    mm = minimap(r, t, maps, disc, P, 84.0 * 50.0)
    if ua < 1.0: mm.putalpha(mm.getchannel("A").point(lambda v: int(v * ua)))
    o.alpha_composite(mm, (int(x0), int(y0))); d = ImageDraw.Draw(o, "RGBA")
    d.rectangle((x0, y0, x0 + P, y0 + P), outline=lin((0.75, 0.65, 0.45), A(0.9)), width=2 * K)
    rooms = sum(1 for m in maps.values() for q in m["rects"] if not q[5]); seen = sum(1 for c, m in maps.items() for i, q in enumerate(m["rects"]) if not q[5] and i in disc.get(c, set()))
    d.text((x0, y0 - 28 * K), "DUNGEON", font=f_small, fill=lin(INK, A(1.0))); d.text((x0 + P, y0 - 28 * K), "%d / %d rooms" % (seen, rooms), font=f_small, fill=lin(INK, A(1.0)), anchor="ra")
    d.text((x0 + P / 2, y0 + 3 * K), "N", font=f_small, fill=lin(INK, A(1.0)), anchor="ma"); d.text((x0, y0 + P + 5 * K), "M  map", font=f_small, fill=lin((0.7, 0.68, 0.62), A(1.0)))
def describe(it, r):
    """what an item does for her (ARDHUD::DescribeItem)"""
    hp, mp = r["mhp"], r.get("mmana", 0)
    if it["kind"] == "healing": return "Restores %d%% of your hit points  (%d HP)" % (round(it["amount"] * 100), round(it["amount"] * hp))
    if it["kind"] == "mana": return ("Restores %d%% of your mana  (%d)" % (round(it["amount"] * 100), round(it["amount"] * mp))) if mp > 0 else "No use to you: you have no mana"
    if it["kind"] == "speed": return "You move %d%% faster for %d seconds" % (round(it["amount"] * 100), it["seconds"])
    title = C.get("title", HERO).lower()
    if it["kind"] == "armour":
        # (ARDHUD::DescribeItem / ARDDungeonGenerator::ArmourRefusal: its weight, and why her hero cannot wear it)
        lk = it.get("looks", ""); wt = it.get("weight")
        s = (("%s armour%s.  " % (wt.capitalize(), (" (%s)" % it["type"]) if it.get("type") else "")) if wt else "") + ((lk[:1].upper() + lk[1:] + ".  ") if lk else "")
        if it.get("dr"): s += "Damage reduction %d / 10, speed %d / 10.  " % (it["dr"], it["sr"])
        s += "Worn, each blow on you takes %d%% less" % round(it["amount"] * 100) + (" and you move %d%% slower." % round(it["slower"] * 100) if it.get("slower", 0) > 0 else ".")
        if it.get("durability", 0) > 0:
            left = armour_left(it["name"], r.get("t", 0.0))
            s += "  Durability %d / %d: each blow that reaches you takes 1 off; at 0 it takes off half as much." % (left, it["durability"])
            if left <= 0: s += "  It is worn out: mend it with a repair item."
        wears = C.get("wears")
        if wt and wears is not None and wt not in wears:
            ws = [x for x in ("light", "medium", "heavy") if x in wears]
            s += ("  The %s wears no armour." % title) if not ws else ("  The %s is %s: the %s wears only %s armour." % (it["name"].lower(), wt, title, ws[0] if len(ws) == 1 else ", ".join(ws[:-1]) + " and " + ws[-1]))
        elif "fits" in it and HERO not in it["fits"]: s += "  The %s was not made for the %s." % (it["name"].lower(), title)
        return s
    if it["kind"] == "repair":
        return "Mends %d%% of a set of armour's or a found weapon's full durability, up to full.  Enter, then choose what it mends." % round(it["amount"] * 100)
    if it["kind"] == "component":
        uses = [r_["item"].lower() for r_ in C.get("recipes", []) if any(it["name"] in p_[2] for p_ in r_["parts"])]
        return "A crafting material: an anvil makes repair items from it (F at an anvil; anvils are on the maps)." + ("  It goes into: " + ", ".join(uses) + "." if uses else "")
    if it["kind"] == "weapon":
        # (level 5: a weapon she carries; its type and ratings, its durability, and whether her hero can wield it)
        lk = it.get("looks", "")
        return ((lk[:1].upper() + lk[1:] + ".  ") if lk else "") + "Durability %d." % round(it["amount"]) + (
            "  The %s cannot wield it." % title if "wielded_by" in it and HERO not in it["wielded_by"] else "")
    return "Restores %d%% of your hit points a second for %d s  (%.1f HP/s)" % (round(it["amount"] * 100), it["seconds"], it["amount"] * hp)
def armour_left(name, t):
    """what was left of a set's durability at t (the inventory's armour line)"""
    le = last_at(LINES, t)
    for x in (le["lines"] if le else []):
        p_ = x.split("|")
        if p_[0] == "armour" and p_[1] == name and len(p_) >= 5: return float(p_[3])
    return 0.0
def l4_panels(o, r, t, ua):
    """level 4: FOUND under the middle of the view, what the inventory said, and the inventory while it is open (the
    game's HUD as ARDHUD::DrawNotices / DrawInventory draw them)"""
    d = ImageDraw.Draw(o, "RGBA"); gold = (1.0, 0.82, 0.35)
    inv = r.get("inv", [0, 0])
    fe = last_at(FOUND, t)
    if fe and 0 <= t - fe["t"] < 3.2 and not inv[0]:
        a = max(0.0, min(1.0, (t - fe["t"]) / 0.25, (3.2 - (t - fe["t"])) / 0.6)) * ua
        # (level 5: a container may hold up to six things: the first by name, the others counted)
        more = len(fe.get("items", [])) - 1
        fname = fe["item"] + ("  and %d more" % more if more > 0 else "")
        y = H * K * 0.60; nw = d.textlength(fname, font=f_head)
        ic = iicon(fe["item"])
        if UI and UI.has("banner"):
            # (ARDHUD::DrawNotices: the painted plaque, the item's picture on its left, the text right of it)
            bh = 106 * K + 28 * K; ppx = UI.height_px("banner", bh)
            ends = UI.L["banner"]["border"][0] * UI.img["banner"].size[0] * ppx
            ih = 106 * K if (ic and UI.has(ic)) else 0
            bw = max(nw, 200 * K) + 48 * K + ih + ends * 2
            x0, x1 = W * K / 2 - bw / 2, W * K / 2 + bw / 2
            UI.nine(o, "banner", (x0, y - 24 * K), (x1, y + 110 * K), ppx, (1, 1, 1, a))
            if ih: UI.fit(o, ic, (x0 + ends + 12 * K, y - 8 * K), (x0 + ends + 4 * K + ih, y + 94 * K), (1, 1, 1, a))
            d = ImageDraw.Draw(o, "RGBA"); cx = W * K / 2 + ih / 2
        else:
            bw = max(nw, 200 * K) + 48 * K; cx = W * K / 2
            d.rectangle((W * K / 2 - bw / 2, y - 10 * K, W * K / 2 + bw / 2, y + 96 * K), fill=lin((0.05, 0.04, 0.02), 0.78 * a), outline=lin(gold, 0.95 * a), width=2 * K)
        text_c(d, (cx, y + 6 * K), sc("FOUND"), fl_small, lin(gold, a), "mt", False)
        text_c(d, (cx, y + 30 * K), fname, f_head, lin((1.0, 0.97, 0.88), a), "mt", False)
        text_c(d, (cx, y + 70 * K), "I  inventory", f_tiny, lin((0.75, 0.72, 0.65), a), "mt", False)
    me = last_at(MSGS, t)
    if not inv[0] and not r.get("craft", [0])[0] and me and me["text"] and 0 <= t - me["t"] < 2.6:
        a = max(0.0, min(1.0, (2.6 - (t - me["t"])) / 0.5)) * ua; tw = d.textlength(me["text"], font=f_line); y = H * K * 0.30
        if UI and UI.has("banner"):
            bh = 34 * K + 40 * K; ppx = UI.height_px("banner", bh); ends = UI.L["banner"]["border"][0] * UI.img["banner"].size[0] * ppx + 14 * K
            UI.nine(o, "banner", (W * K / 2 - tw / 2 - ends, y - 20 * K), (W * K / 2 + tw / 2 + ends, y + 54 * K), ppx, (1, 1, 1, a)); d = ImageDraw.Draw(o, "RGBA")
        else:
            d.rectangle((W * K / 2 - tw / 2 - 14 * K, y - 7 * K, W * K / 2 + tw / 2 + 14 * K, y + 38 * K), fill=lin((0.03, 0.03, 0.04), 0.65 * a))
        text_c(d, (W * K / 2, y), me["text"], f_line, lin((0.95, 0.92, 0.82), a), "mt", False)
    if r.get("craft", [0, 0])[0]: craft_panel(o, r, t, ua, me); return        # (level 5: the anvil's crafting panel)
    if not inv[0]: return
    # (level 5: choosing what a repair item mends: its list in place of the inventory's, as ARDHUD::DrawInventory)
    rep = r.get("rep", [0, 0, ""]); picking = bool(rep[0])
    if picking:
        le = last_at(REPL, t); lines = le["lines"] if le else []; cur = rep[1]
        rit = ITEMS.get(rep[2], {})
        secs = [("armour", "MEND WITH THE %s  (+%d%%)" % (rep[2].upper(), round(rit.get("amount", 0) * 100)), False), ("weapon", "WEAPONS YOU FOUND", False)]
    else:
        le = last_at(LINES, t); lines = le["lines"] if le else []; cur = inv[1]
        secs = [("weapon", "WEAPONS AND SPELLS", True), ("item", "POTIONS AND FOOD", True), ("repair", "REPAIR ITEMS", False), ("armour", "ARMOUR", False),
                ("component", "MATERIALS", False), ("carried", "WEAPONS THE %s CANNOT WIELD" % C.get("title", HERO).upper(), False)]
    sec_of = []; count = [0] * len(secs)
    for x in lines:
        k_ = next((j for j, sv in enumerate(secs) if x.startswith(sv[0] + "|")), 0); sec_of.append(k_); count[k_] += 1
    # (a layer of its own, put over the rest: drawing on the HUD's layer replaces what is there instead of blending)
    top = o; o = Image.new("RGBA", top.size, (0, 0, 3, int(140 * ua))); d = ImageDraw.Draw(o, "RGBA")
    rh, pw, pd, head_h = 34 * K, 1000 * K, 22 * K, 58 * K
    empty = rh if (len(secs) > 1 and secs[1][2] and count[1] == 0) else 0
    def heads(f0, f1):
        n_ = 0
        for j, sv in enumerate(secs):
            shown_ = sv[2] and count[j] == 0
            if not shown_: shown_ = any(sec_of[i] == j for i in range(f0, min(f1, len(lines))))
            n_ += 1 if shown_ else 0
        return n_
    room = H * K - 80 * K - 150 * K - 30 * K
    fit, first = len(lines), 0
    for _ in range(3):
        nh = heads(first, first + fit)
        if head_h * nh + empty + rh * len(lines) <= room: fit, first = len(lines), 0; break
        fit = max(4, min(len(lines), int((room - head_h * nh - empty) // rh))); first = max(0, min(cur - fit // 2, len(lines) - fit))
    shown = lambda i: first <= i < first + fit
    lh = 46 * K + head_h * heads(first, first + fit) + rh * fit + (30 * K if fit < len(lines) else 0) + empty
    ph = max(lh, (400 if (UI and UI.has("slot")) else 330) * K) + 150 * K
    ax, ay = (W * K - pw) / 2, max(40 * K, (H * K - ph) / 2); bx, by = ax + pw, ay + ph
    if UI and UI.has("panel_wide"): UI.board(o, "panel_wide", (ax, ay), (bx, by), 44 * K); d = ImageDraw.Draw(o, "RGBA")
    else: d.rectangle((ax, ay, bx, by), fill=lin((0.035, 0.04, 0.055), 0.94), outline=lin((0.75, 0.65, 0.45), 0.9), width=2 * K)
    divider = bool(UI and UI.has("divider")); plate = bool(UI and UI.has("button"))
    tin = 24 * K if (UI and UI.has("panel_wide")) else 0           # (the title row clear of the board's corner ornaments)
    d.text((ax + pd + tin, ay + 16 * K), "REPAIR" if picking else "INVENTORY", font=f_title, fill=lin(INK)); d.text((bx - pd - tin, ay + 18 * K), C["title"], font=ft_small, fill=lin(gold), anchor="ra")
    d.text((bx - pd - tin, ay + 46 * K), "in play the game pauses while it is open", font=f_tiny, fill=lin((0.70, 0.68, 0.62)), anchor="ra")
    lx, lw = ax + pd, pw * 0.5 - pd; y = ay + 76 * K
    def header(s_):
        nonlocal y, d
        d.text((lx, y), sc(s_), font=fl_small, fill=lin((0.70, 0.68, 0.62))); y += 26 * K
        if divider: UI.fit(o, "divider", (lx - 8 * K, y - 18 * K), (lx + lw + 8 * K, y + 12 * K)); d = ImageDraw.Draw(o, "RGBA")
        else: d.rectangle((lx, y - 4 * K, lx + lw, y - 3 * K), fill=lin((0.75, 0.65, 0.45), 0.4))
        y += 4 * K
    def rowl(i, name, tag, tagc, icon=None):
        nonlocal y, d
        if not shown(i): return
        on = i == cur
        if on:
            if plate:
                UI.nine(o, "button", (lx - 4 * K, y - 4 * K), (lx + lw + 4 * K, y + rh), UI.height_px("button", rh + 4 * K), (1.25, 1.05, 0.7, 1)); d = ImageDraw.Draw(o, "RGBA")
                d.rectangle((lx, y, lx + lw, y + rh - 4 * K), outline=lin(gold), width=2 * K)
            else: d.rectangle((lx, y, lx + lw, y + rh - 4 * K), fill=lin((0.36, 0.27, 0.10), 0.95), outline=lin(gold), width=2 * K)
        ix = 0
        if icon and UI.has(icon): ix = rh; UI.fit(o, icon, (lx + 8 * K, y - 2 * K), (lx + 4 * K + rh, y + rh - 2 * K)); d = ImageDraw.Draw(o, "RGBA")
        gw = d.textlength(sc(tag), font=fl_tiny) if tag else 0
        avail = lw - 24 * K - ix - (gw + 14 * K if gw else 0); f_n = f_line; nw = d.textlength(name, font=f_line)
        if nw > avail and LETTERS: f_n = fit_font("Alegreya-500", 26, max(0.7, avail / nw))
        d.text((lx + 12 * K + ix, y + 5 * K), name, font=f_n, fill=(255, 255, 255, 255) if on else lin((0.86, 0.84, 0.78)))
        if tag: d.text((lx + lw - 12 * K, y + 9 * K), sc(tag), font=fl_tiny, fill=lin(tagc), anchor="ra")
        y += rh
    last = [-1]
    def open_sec(k_):
        nonlocal y
        for j in range(last[0] + 1, k_ + 1):
            rows_ = count[j] > 0
            if not rows_ and not secs[j][2]: continue
            if rows_ and j < k_: continue
            if last[0] >= 0 or j > 0: y += 12 * K
            header(secs[j][1])
            if not rows_: d.text((lx + 12 * K, y + 6 * K), "nothing yet: the chests, trunks and barrels hold some", font=f_tiny, fill=lin((0.70, 0.68, 0.62))); y += rh
        last[0] = k_
    WL = weapons_at(t)
    for i, x in enumerate(lines):
        if not shown(i): continue
        if sec_of[i] != last[0]: open_sec(sec_of[i])
        p_ = x.split("|")
        if picking:
            arm = p_[0] == "armour"
            if len(p_) < (5 if arm else 6): continue
            nm = p_[1] if arm else p_[2]; left, full, after = (float(p_[2]), float(p_[3]), float(p_[4])) if arm else (float(p_[3]), float(p_[4]), float(p_[5]))
            tag = ("%d / %d  WHOLE" % (left, full)) if left >= full else ("%d  TO  %d / %d" % (left, after, full))
            rowl(i, nm, tag, (0.70, 0.68, 0.62) if left >= full else gold, iicon(nm) if arm else wicon(nm))
            continue
        if p_[0] == "weapon":
            wd = WL[i] if i < len(WL) else {"name": p_[1]}
            tag = "ALWAYS AT HAND" if wd.get("alongside") else ("IN YOUR HANDS" if i == r["w"] else "")
            if wd.get("durability", 0) > 0: tag = (tag + "   " if tag else "") + "%d / %d" % (wd["wear"], wd["durability"])
            rowl(i, wd["name"], tag, CYAN if wd.get("alongside") else gold, wicon(wd["name"]))
        elif p_[0] == "armour":
            left, full = (float(p_[3]), float(p_[4])) if len(p_) >= 5 else (0.0, 0.0)
            tag = "WORN" if p_[2] == "1" else ""
            if full > 0: tag = (tag + "   " if tag else "") + ("WORN OUT" if left <= 0 else "%d / %d" % (left, full))
            rowl(i, p_[1], tag, (1.0, 0.45, 0.35) if (full > 0 and left <= 0) else CYAN, iicon(p_[1]))
        else: rowl(i, p_[1], "x %s" % p_[2], (0.70, 0.68, 0.62) if p_[0] in ("carried", "component") else gold, iicon(p_[1]))
    if not lines or last[0] < len(secs) - 1: open_sec(len(secs) - 1)
    if fit < len(lines):
        d.text((lx + 12 * K, y + 6 * K), "%d more above,  %d more below" % (first, len(lines) - first - fit), font=f_tiny, fill=lin((0.70, 0.68, 0.62))); y += 30 * K
    rx, rw = ax + pw * 0.5 + pd, pw * 0.5 - pd * 2; ry = ay + 76 * K
    d.rectangle((rx - pd / 2, ry, rx - pd / 2 + K, by - 110 * K), fill=lin((0.75, 0.65, 0.45), 0.4))
    def para(s_, c, f_):
        nonlocal ry
        words = s_.split(); line = ""
        for w_ in words:
            tr = (line + " " + w_).strip()
            if d.textlength(tr, font=f_) > rw and line: d.text((rx, ry), line, font=f_, fill=c); ry += f_.size + 6 * K; line = w_
            else: line = tr
        if line: d.text((rx, ry), line, font=f_, fill=c); ry += f_.size + 6 * K
    def picture(ic, title):
        nonlocal ry, d
        if ic and UI.has(ic):
            sz = 104 * K
            UI.fit(o, "slot", (rx, ry), (rx + sz, ry + sz)); UI.fit(o, ic, (rx + 16 * K, ry + 14 * K), (rx + sz - 16 * K, ry + sz - 14 * K)); d = ImageDraw.Draw(o, "RGBA")
            f_t = f_head; tw_ = d.textlength(title.upper(), font=f_head)
            if tw_ > rw - sz - 20 * K and LETTERS: f_t = fit_font("Cinzel-700", 30, max(0.6, (rw - sz - 20 * K) / tw_))
            d.text((rx + sz + 16 * K, ry + sz / 2), title.upper(), font=f_t, fill=(255, 255, 255, 255), anchor="lm"); ry += sz + 12 * K
        else:
            d.text((rx, ry), title.upper(), font=f_head, fill=(255, 255, 255, 255)); ry += 46 * K
    if 0 <= cur < len(lines):
        p_ = lines[cur].split("|")
        if picking:
            arm = p_[0] == "armour"; nm = p_[1] if arm else p_[2]
            left, full, after = (float(p_[2]), float(p_[3]), float(p_[4])) if arm else (float(p_[3]), float(p_[4]), float(p_[5]))
            picture(iicon(nm) if arm else wicon(nm), nm)
            para("Durability now %d / %d" % (left, full), lin(INK), f_line)
            if left >= full: para("It is whole: nothing to mend", lin((0.70, 0.68, 0.62)), f_line)
            else:
                para("The %s gives it back %d:  %d / %d after" % (rep[2].lower(), after - left, after, full), lin((0.6, 0.95, 0.6)), f_line)
                if arm and left <= 0: para("Worn out now: mended, it takes off its whole share again", lin(CYAN), f_line)
            ry += 6 * K; para("Enter  mend it      Backspace  back", lin(gold), f_line)
        else:
            picture(wicon(p_[1]) if p_[0] == "weapon" else iicon(p_[1]), p_[1])
            if p_[0] == "weapon":
                wd = WL[cur] if cur < len(WL) else C["weapons"][min(cur, len(C["weapons"]) - 1)]
                para("A spell: a bolt flies after the monster you face" if wd.get("spell") and not wd.get("ranged") else "A ranged weapon: its bolts fly straight at the monster you face" if wd.get("ranged") else "A melee weapon", lin((0.70, 0.68, 0.62)), f_line)
                if wd.get("speed", 0) > 0:
                    para("%s  ·  speed %d / 10  ·  damage %d / 10" % (wd["type"][:1].upper() + wd["type"][1:], wd["speed"], wd["rating"]), lin(INK), f_line)
                    para("Durability %d / %d: a hit takes 1 off, at 0 it breaks; a repair item mends it" % (wd["wear"], wd["durability"]), lin((0.75, 0.85, 0.7)), f_line)
                para("%s damage" % (("%.1f" % wd["damage"]).rstrip("0").rstrip(".")), lin(INK), f_line)
                if wd.get("mana"): para("%d mana a cast" % wd["mana"], lin((0.55, 0.7, 1.0)), f_line)
                ry += 6 * K; para("Cast with RMB or E (LB) while your weapon stays drawn" if wd.get("alongside") else "In your hands" if cur == r["w"] else "Enter  wield it", lin(gold), f_line)
            else:
                it = ITEMS.get(p_[1])
                if it: para(describe(it, r), lin(INK), f_line)
                ry += 6 * K
                if p_[0] == "item": para("Enter  use it", lin(gold), f_line)
                elif p_[0] == "repair": para("Enter  choose what it mends", lin(gold), f_line)
                elif p_[0] == "armour": para("Enter  take it off" if len(p_) > 2 and p_[2] == "1" else "Enter  put it on", lin(gold), f_line)
    ry = max(ry + 18 * K, ay + 250 * K)
    para("Hit points  %d / %d" % (math.ceil(r["hp"]), r["mhp"]), lin((0.5, 0.9, 0.55)), f_line)
    if r.get("mmana", 0) > 0: para("Mana  %d / %d" % (math.floor(r["mana"]), r["mmana"]), lin((0.55, 0.7, 1.0)), f_line)
    if r.get("arm", "None") != "None":
        s_ = "Armour  %s,  blows %d%% less" % (r["arm"], round(r.get("armv", 0) * 100))
        if r.get("slow", 0) > 0: s_ += ",  %d%% slower" % round(r["slow"] * 100)
        if r.get("armw") and r["armw"][1] > 0: s_ += ",  durability %d / %d" % (r["armw"][0], r["armw"][1])
        para(s_, lin(CYAN), f_line)
    fy = by - 92 * K
    if divider: UI.fit(o, "divider", (ax + pd, fy - 20 * K), (bx - pd, fy + 20 * K)); d = ImageDraw.Draw(o, "RGBA")
    else: d.rectangle((ax + pd, fy, bx - pd, fy + K), fill=lin((0.75, 0.65, 0.45), 0.4))
    op = last_at(INVS, t)
    if me and me["text"] and op and me["t"] >= op["t"]: d.text((ax + pd + tin, fy + 14 * K), me["text"], font=f_line, fill=lin((1.0, 0.93, 0.75)))
    d.text((ax + pd + tin, fy + 52 * K), ("W S / arrows / wheel  select      Enter or E  mend it      Backspace  back      I or Tab  close" if picking else
                                          "W S / arrows / wheel  select      Enter or E  wield or use      I or Tab  close"), font=f_small, fill=lin((0.70, 0.68, 0.62)))
    top.alpha_composite(o)
def craft_panel(top, r, t, ua, me):
    """ARDHUD::DrawCrafting: the anvil's panel; the recipes on the left (CAN MAKE where she has everything), the chosen one on
    the right: its picture, what it mends, each part with what she carries of it against what it takes"""
    gold, dim, have_c, lack_c = (1.0, 0.82, 0.35), (0.70, 0.68, 0.62), (0.55, 0.95, 0.55), (1.0, 0.5, 0.4)
    le = last_at(CRAFTL, t); lines = le["lines"] if le else []; cur = r["craft"][1]
    o = Image.new("RGBA", top.size, (0, 0, 3, int(140 * ua))); d = ImageDraw.Draw(o, "RGBA")
    rh, pw, pd, ph = 40 * K, 1000 * K, 22 * K, 640 * K
    ax, ay = (W * K - pw) / 2, max(40 * K, (H * K - ph) / 2); bx, by = ax + pw, ay + ph
    if UI and UI.has("panel_wide"): UI.board(o, "panel_wide", (ax, ay), (bx, by), 44 * K); d = ImageDraw.Draw(o, "RGBA")
    else: d.rectangle((ax, ay, bx, by), fill=lin((0.035, 0.04, 0.055), 0.94), outline=lin((0.75, 0.65, 0.45), 0.9), width=2 * K)
    divider = bool(UI and UI.has("divider")); plate = bool(UI and UI.has("button")); tin = 24 * K if (UI and UI.has("panel_wide")) else 0
    d.text((ax + pd + tin, ay + 16 * K), "THE ANVIL", font=f_title, fill=lin(INK))
    d.text((bx - pd - tin, ay + 22 * K), "make repair items from your materials", font=f_line, fill=lin(gold), anchor="ra")
    d.text((bx - pd - tin, ay + 56 * K), "in play the game pauses while it is open", font=f_tiny, fill=lin(dim), anchor="ra")
    lx, lw = ax + pd, pw * 0.42 - pd; y = ay + 80 * K
    d.text((lx, y), sc("RECIPES"), font=fl_small, fill=lin(dim)); y += 26 * K
    if divider: UI.fit(o, "divider", (lx - 8 * K, y - 18 * K), (lx + lw + 8 * K, y + 12 * K)); d = ImageDraw.Draw(o, "RGBA")
    y += 4 * K
    parsed = [x.split("|") for x in lines]
    for i, p_ in enumerate(parsed):
        if len(p_) < 3: continue
        on, can = i == cur, p_[2] == "1"
        if on:
            if plate:
                UI.nine(o, "button", (lx - 4 * K, y - 4 * K), (lx + lw + 4 * K, y + rh), UI.height_px("button", rh + 4 * K), (1.25, 1.05, 0.7, 1)); d = ImageDraw.Draw(o, "RGBA")
                d.rectangle((lx, y, lx + lw, y + rh - 4 * K), outline=lin(gold), width=2 * K)
            else: d.rectangle((lx, y, lx + lw, y + rh - 4 * K), fill=lin((0.36, 0.27, 0.10), 0.95), outline=lin(gold), width=2 * K)
        ix = 0; ic = iicon(p_[1])
        if ic and UI.has(ic): ix = rh; UI.fit(o, ic, (lx + 8 * K, y - 2 * K), (lx + 4 * K + rh, y + rh - 2 * K)); d = ImageDraw.Draw(o, "RGBA")
        d.text((lx + 12 * K + ix, y + 8 * K), p_[1], font=f_line, fill=(255, 255, 255, 255) if on else lin((0.86, 0.84, 0.78)))
        n_have = sum(int(x.split("|")[2]) for x in (last_at(LINES, t) or {"lines": []})["lines"] if x.startswith("repair|" + p_[1] + "|"))
        d.text((lx + lw - 12 * K, y + 11 * K), sc("CAN MAKE") if can else "x %d" % n_have, font=fl_tiny, fill=lin(have_c if can else dim), anchor="ra")
        y += rh
    rx, rw = ax + pw * 0.42 + pd, pw * 0.58 - pd * 2; ry = ay + 80 * K
    d.rectangle((rx - pd / 2, ry, rx - pd / 2 + K, by - 110 * K), fill=lin((0.75, 0.65, 0.45), 0.4))
    if 0 <= cur < len(parsed) and len(parsed[cur]) >= 3:
        p_ = parsed[cur]; ic = iicon(p_[1])
        if ic and UI.has(ic):
            sz = 104 * K
            UI.fit(o, "slot", (rx, ry), (rx + sz, ry + sz)); UI.fit(o, ic, (rx + 16 * K, ry + 14 * K), (rx + sz - 16 * K, ry + sz - 14 * K)); d = ImageDraw.Draw(o, "RGBA")
            d.text((rx + sz + 16 * K, ry + sz / 2), p_[1].upper(), font=f_head, fill=(255, 255, 255, 255), anchor="lm"); ry += sz + 12 * K
        else: d.text((rx, ry), p_[1].upper(), font=f_head, fill=(255, 255, 255, 255)); ry += 46 * K
        it = ITEMS.get(p_[1], {})
        d.text((rx, ry), "Mends %d%% of a set of armour's or a found weapon's durability" % round(it.get("amount", 0) * 100), font=f_small, fill=lin(INK)); ry += 30 * K
        d.text((rx, ry), sc("IT TAKES"), font=fl_tiny, fill=lin(dim)); ry += 24 * K
        parts = [q.split(":") for q in (p_[3].split(";") if len(p_) >= 4 and p_[3] else [])]
        cw = rw * 0.5
        for k_, q in enumerate(parts):
            if len(q) < 3: continue
            hv, nd = int(q[1]), int(q[2]); px, py = rx + (k_ % 2) * cw, ry + (k_ // 2) * 27 * K
            d.text((px, py), q[0], font=f_small, fill=lin((0.86, 0.84, 0.78)))
            d.text((px + cw - 16 * K, py + K), "%d / %d" % (hv, nd), font=fl_tiny, fill=lin(have_c if hv >= nd else lack_c), anchor="ra")
        ry += ((len(parts) + 1) // 2) * 27 * K + 14 * K
        d.text((rx, ry), "Enter  make it" if p_[2] == "1" else "You lack some of what it takes: the containers hold materials", font=f_small, fill=lin(gold if p_[2] == "1" else dim))
    fy = by - 92 * K
    if divider: UI.fit(o, "divider", (ax + pd, fy - 20 * K), (bx - pd, fy + 20 * K)); d = ImageDraw.Draw(o, "RGBA")
    if me and me["text"]: d.text((ax + pd + tin, fy + 14 * K), me["text"], font=f_line, fill=lin((1.0, 0.93, 0.75)))
    d.text((ax + pd + tin, fy + 52 * K), "W S / arrows / wheel  select      Enter or E  make it      F, Backspace or Tab  close", font=f_small, fill=lin(dim))
    top.alpha_composite(o)
def c5_caps():
    """(run5c) the captions of the armour table, loot and crafting reel, each from what the record says happened"""
    out = []; gold = (255, 226, 150)
    hj = HJ.get(HERO, {}); acc = tuple(int(255 * v) for v in hj.get("accent", (1.0, 0.94, 0.84)))
    maps_ = [e for e in EV if e["kind"] == "map" and e.get("open")]
    close = lambda e: next((x["t"] for x in EV if x["kind"] == "map" and not x.get("open") and x["t"] > e["t"]), e["t"] + 4.0)
    ws = [x for x in ("light", "medium", "heavy") if x in (C.get("wears") or [])]
    wear_txt = "she wears %s" % ("no armour" if not ws else ("all armour: light, medium and heavy" if len(ws) == 3 else "only " + " and ".join(ws) + " armour"))
    t_map = maps_[0]["t"] if maps_ else 4.0
    out.append((0.8, t_map - 0.1, "THE " + HERO.upper(), ["  ·  ".join(hj.get("abilities", [])), "%s  ·  %d hit points" % (wear_txt, hj.get("health", 0))], acc))
    if maps_:
        out.append((maps_[0]["t"], close(maps_[0]), "M  ·  THE BIG MAP:  TIERS AND ANVILS", ["each room she has found is written with its tier: this set is tier 1, the 8 round it tier 2, then 16, 24, 32",
                    "the small anvil: one in every forge, at least one in every set of rooms (here, in the great hall): F there makes repair items"], gold))
    tc0 = next((e["t"] for e in EV if e["kind"] == "to_chest"), None); tc1 = CHESTS[0]["t"] if CHESTS else None
    if tc0 is not None and tc1 is not None:
        out.append((tc0, tc1 - 0.35, "THE FIRES ARE QUIETER", ["the crackle of the torches, braziers and hearths is about 8 dB lower than in the earlier reels",
                    "measured in the game's own output 2.5 m from a torch: -9.5 dB (853's fire step)"], (255, 200, 150)))
    for e in CHESTS:
        fd = next((x for x in FOUND if x["t"] >= e["t"] - 0.05), None); held = fd.get("items", []) if fd else []
        kinds = [ITEMS.get(x, {}).get("kind") for x in held]
        names = ", ".join(x.lower() for x in held[:4]) + (" ..." if len(held) > 4 else "")
        out.append((e["t"] - 0.3, e["t"] + 2.6, "F  ·  A CHEST OF THE GREAT HALL", ["it held %d things: %s" % (len(held), names),
                    "materials come 1 to 3 at a time, in every tier (%d here)  ·  potions, food and armour by tier: these are tier 1's" % sum(1 for k in kinds if k == "component")], gold))
    for e in INVS:
        u = next((x for x in USED if x["t"] >= e["t"]), None)
        if not u: continue
        nxt = next((x["t"] for x in EV if x["t"] > u["t"] + 0.2 and x["kind"] in ("inventory", "quiet", "wear_set", "craft_open")), u["t"] + 5.0)
        if e.get("why") == "armour":
            nm = u["entry"].split("|")[1]; it = ITEMS.get(nm, {})
            out.append((e["t"], u["t"], "I  ·  ENTER  ·  ARMOUR", ["the sets she found are in her inventory, each with its durability (in play the game pauses here)",
                        "she goes down the list to the %s and puts it on" % nm.lower()], gold))
            out.append((u["t"], nxt - 0.05, nm.upper(), ["%s, %s armour  ·  damage reduction %d / 10: blows take %d%% less  ·  speed %d / 10: she moves %d%% slower" % (
                it.get("type", ""), it.get("weight", ""), it.get("dr", 0), round(it.get("amount", 0) * 100), it.get("sr", 0), round(it.get("slower", 0) * 100)),
                "durability %d: each blow that reaches her takes 1 off; at 0 it takes off half as much  ·  %s" % (it.get("durability", 0), wear_txt)], lin(CYAN)[:3]))
        elif e.get("why") == "refused":
            it = ITEMS.get(e.get("item", ""), {}); cl = inv_closed_after(u["t"])
            out.append((cl, min(nxt - 0.05, cl + 3.6), "I  ·  ENTER  ·  " + u["message"].upper(), [wears_line(it),
                        "the %s: %s armour (%s), %d%% less a blow, %d%% slower" % (e.get("item", "").lower(), it.get("weight", ""), it.get("type", ""), round(it.get("amount", 0) * 100), round(it.get("slower", 0) * 100))], (255, 170, 130)))
        elif e.get("why") == "repair":
            rp = next((x for x in EV if x["kind"] == "repaired" and x["t"] >= u["t"]), None)
            out.append((e["t"], u["t"], "I  ·  ENTER  ·  " + e.get("item", "").upper(), ["Enter on a repair item lists what it can mend: her armour, the weapons she found",
                        "she goes down the list to the %s" % e.get("item", "").lower()], gold))
            if rp:
                out.append((u["t"], rp["t"], "THE REPAIR LIST", ["each set and each found weapon with its durability now and after the %s" % e.get("item", "").lower(),
                            "she chooses the %s" % rp["set"].lower()], gold))
                out.append((rp["t"], rp["t"] + 3.2, "ENTER  ·  MENDED", [rp["message"], "it takes off its whole share again: blows take %d%% less" % round(rp["share"] * 100)], lin(CYAN)[:3]))
    ws_ = ev1("wear_set"); co = ev1("craft_open")
    if ws_:
        it = ITEMS.get(ws_["set"], {})
        out.append((ws_["t"], (co["t"] - 0.1) if co else ws_["t"] + 3.0, "THE REEL WEARS THE SET DOWN", ["the %s set to %d of %d durability, as %d blows that reach her would" % (ws_["set"].lower(), ws_["wear"], ws_["durability"], ws_["durability"] - ws_["wear"]),
                    ("worn out: it takes off half its share now, %d%% instead of %d%%  ·  the inventory says WORN OUT" % (round(ws_["share"] * 100), round(it.get("amount", 0) * 100))) if ws_["wear"] <= 0 else
                    "for the reel the monsters leave her be from here until she has mended it (in play the panels pause the game)"], (255, 200, 120)))
    gv = next((x for x in EV if x["kind"] == "given" and x.get("why") == "craft"), None); cr = ev1("crafted")
    if co:
        out.append((co["t"], gv["t"] if gv else co["t"] + 3.0, "F  ·  THE ANVIL", ["the crafting panel: five repair items, each part with what she carries against what it takes",
                    "in play it pauses the game; for the reel the world goes on, and the monsters leave her be meanwhile"], gold))
    if gv:
        rc = RECIPES.get(gv["recipe"], {"parts": []})
        out.append((gv["t"], cr["t"] if cr else gv["t"] + 2.0, "THE REEL GIVES HER THE MATERIALS", ["the recipe for %s: %s" % (gv["recipe"].lower(), ", ".join("%d %s" % (p_[1], p_[0]) for p_ in rc["parts"])),
                    "she lacked %d of them; in play they come from the containers, 1 to 3 at a time" % sum(gv["items"].values())], (255, 200, 120)))
    if cr:
        it = ITEMS.get(cr["item"], {})
        out.append((cr["t"], cr["t"] + 2.4, "ENTER  ·  %s MADE" % cr["item"].upper(), ["the parts are used up (wood of any kind: the kind she has most of first)",
                    "the %s mends %d%% of a set's or a found weapon's full durability" % (cr["item"].lower(), round(it.get("amount", 0) * 100))], lin(CYAN)[:3]))
    if LANDED:
        m2 = next((e for e in maps_ if e["t"] > LANDED["t"]), None)
        out.append((LANDED["t"] + 3.0, m2["t"] - 0.1 if m2 else LANDED["t"] + 6.0, "A SET OF TIER 2", ["the minimap writes the tier in the rooms it shows: T2",
                    "for the reel she was put here behind the card; the set was generated as she arrived"], gold))
        if m2: out.append((m2["t"], close(m2), "M  ·  TIER 2 ON THE BIG MAP", ["each room of this set: TIER 2", "its monsters are stronger, its containers hold tier 2's items"], gold))
        for i, e in enumerate([x for x in FIGHTS if x["t"] > LANDED["t"]][:2]):
            end = next((k["t"] for k in KILLS if k["t"] > e["t"]), e["t"] + 6.0) + 1.2
            bl = [b for b in BLOWS if e["t"] <= b["t"] <= end]
            arm = e.get("armour") or r_arm_at(e["t"])
            if arm and arm != "None" and HERO != "Mage":
                w0, w1 = armour_left(arm, e["t"]), armour_left(arm, end)
                l2 = "%d of its blows reached her: each took 1 off the %s's durability, %d to %d" % (len(bl), arm.lower(), w0, w1) if bl else "its blows would take 1 each off the %s's durability" % arm.lower()
                l3 = "and %d%% off each blow" % round((bl[0]["armour"] if bl else 0) * 100) if bl else ""
            else:
                l2 = "the mage wears no armour: its blows take her hit points whole"; l3 = ""
            l3 = lured(e) or l3 or "the monsters' strength follows the tier of their set"
            out.append((e["t"], end, "%s  ·  TIER %d" % (e["monster"].replace("_", " ").upper(), max(abs(e["section"][0]), abs(e["section"][1])) + 1),
                        ["%.0f hit points, %.0f damage a blow  ·  she has %.0f" % (e["its_hit_points"], e["its_damage"], C["max_health"]), l2, l3], gold))
    return out
def r_arm_at(t):
    """the set she wore at t (the rows' arm)"""
    return row(int(t * FPS)).get("arm", "None")
C5CAPS = None
def overlay(f):
    r = row(f); t = f / FPS
    maps, disc = map_at(t)
    o = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0)); d = ImageDraw.Draw(o, "RGBA")
    ua = fade(t, 0.25, 1e9, 0.5, 0.5)                    # the HUD comes up as the reel opens
    A = lambda v: v * ua
    # ---- level 4: the big map (M) under the rest of the HUD, in the minimap's painted style (the minimap is off meanwhile)
    mapo = bool(L4 and UI and UI.has("panel_wide") and r.get("mapo"))
    if mapo: painted_map(o, r, t, maps, disc, ua); d = ImageDraw.Draw(o, "RGBA")
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
        text_c(d, (s[0], y0 - 4 * K), sc("%s  %.0f" % (mo[1].replace("_", " ").upper(), mo[5])), fl_small, lin(INK, A(1.0)), "mb")
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
    if mapo: pass
    elif TACTICAL and UI and UI.has("minimap_ring"):
        # (level 4's painted ring round it: its open inside the size of the map, the map moved in to make room)
        inn = UI.L["minimap_ring"]["inner"]; ring = (P / 2) * 1.03 / max(inn[2] - inn[0], 0.2)
        cx, cy = W * K - mg - ring, mg + ring
        tactical(o, r, t, maps, disc, cx, cy, P / 2, C.get("stylized_minimap_m", 84.0) * 50.0, ua, under=ring + 4 * K)
        UI.fit(o, "minimap_ring", (cx - ring, cy - ring), (cx + ring, cy + ring), (1, 1, 1, ua)); d = ImageDraw.Draw(o, "RGBA")
    elif TACTICAL:
        tactical(o, r, t, maps, disc, W * K - mg - P / 2, mg + 14 * K + P / 2, P / 2, C.get("stylized_minimap_m", 84.0) * 50.0, ua); d = ImageDraw.Draw(o, "RGBA")
    else:
        stylised(o, r, t, maps, disc, P, x0, y0, ua, A); d = ImageDraw.Draw(o, "RGBA")
    # ---- status panel
    # ---- status panel (bottom right): hit points, the weapons with their damage, kills
    mb = 30 * K if (L4 and r.get("mmana", 0) > 0) else 0       # (level 4: her mana under her hit points)
    art = bool(UI and UI.has("bar_health"))                     # (level 4's painted bars: framed, taller rows; ARDHUD::DrawCombat)
    bh = 44 * K
    if art and mb: mb = bh + 2 * K
    hx = bh - 30 * K if art else 0
    ext = 28 * K if (UI and UI.has("panel_wide")) else 0; up = ext * 1.6
    pw, ph, pd = 400 * K, 176 * K + mb + hx, 14 * K; ax, ay = W * K - mg - ext - pw, H * K - mg - ext - ph; bx, by = ax + pw, ay + ph
    if ext:
        UI.board(o, "panel_wide", (ax, ay), (bx, by), ext, (1, 1, 1, ua)); d = ImageDraw.Draw(o, "RGBA")
    else:
        d.rectangle((ax, ay, bx, by), fill=lin((0.04, 0.05, 0.07), A(0.78)), outline=lin((0.75, 0.65, 0.45), A(0.9)), width=2 * K)
    inn = 18 * K if ext else 0          # (clear of the board's corner ornaments)
    d.text((ax + pd + inn, ay + 8 * K), C["title"], font=ft_small, fill=lin(INK, A(1.0))); d.text((bx - pd - inn, ay + 8 * K), sc("KILLS  %d" % r["kills"]), font=fl_small, fill=lin(INK, A(1.0)), anchor="ra")
    fr = r["hp"] / max(r["mhp"], 1.0); hx0, hy0, hx1, hy1 = ax + pd, ay + 36 * K, bx - pd, ay + 64 * K
    def artbar(frame, fill, y0, f, fill_tint, frame_tint):
        a0, a1 = (ax + pd - 6 * K, y0), (bx - pd + 6 * K, y0 + bh); px = UI.height_px(frame, bh)
        UI.bar(o, frame, fill, a0, a1, px, f, fill_tint, frame_tint)
        (i0x, i0y), (i1x, i1y) = UI.inner_box(frame, a0, a1, px)
        return i0x, i0y, i1x, i1y
    if art:
        lo = 0.75 + 0.25 * math.sin(t * 8.0) if fr < 0.25 else 1.0
        hx0, hy0, hx1, hy1 = artbar("bar_health", "fill_health", ay + 30 * K, fr, (lo, lo, lo, ua), (1, 1, 1, ua)); d = ImageDraw.Draw(o, "RGBA")
    else:
        d.rectangle((hx0, hy0, hx1, hy1), fill=lin((0.10, 0.03, 0.03), A(0.95)))
        d.rectangle((hx0 + 2, hy0 + 2, hx0 + 2 + (hx1 - hx0 - 4) * fr, hy1 - 2), fill=lin((0.20, 0.72, 0.26) if fr > 0.5 else (0.90, 0.62, 0.12) if fr > 0.25 else (0.88, 0.16, 0.12), A(1.0)))
        d.rectangle((hx0, hy0, hx1, hy1), outline=lin((0.75, 0.65, 0.45), A(0.9)), width=K)
    text_c(d, ((hx0 + hx1) / 2, (hy0 + hy1) / 2 - K), sc("HP  %d / %d" % (math.ceil(r["hp"]), r["mhp"])), fl_small, (255, 255, 255, int(255 * ua)))
    if mb:
        mf = r["mana"] / max(r["mmana"], 1.0); m0x, m0y, m1x, m1y = ax + pd, ay + 70 * K, bx - pd, ay + 92 * K
        refused = any(e["kind"] == "no_mana" and 0 <= t - e["t"] < 0.6 for e in EV)
        if art and UI.has("bar_mana"):
            fl = max((1.0 - (t - e["t"]) / 0.6 for e in EV if e["kind"] == "no_mana" and 0 <= t - e["t"] < 0.6), default=0.0)
            m0x, m0y, m1x, m1y = artbar("bar_mana", "fill_mana", ay + 30 * K + bh + 2 * K, mf, (1, 1, 1, ua), (1, 1 - 0.7 * fl, 1 - 0.75 * fl, ua)); d = ImageDraw.Draw(o, "RGBA")
            if fl > 0: d.rectangle((m0x, m0y, m1x, m1y), outline=lin((1.0, 0.3, 0.25), fl * ua), width=2 * K)
        else:
            d.rectangle((m0x, m0y, m1x, m1y), fill=lin((0.33 if refused else 0.03, 0.04, 0.12), A(0.95)))
            d.rectangle((m0x + 2, m0y + 2, m0x + 2 + (m1x - m0x - 4) * mf, m1y - 2), fill=lin((0.18, 0.40, 0.95), A(1.0)))
            d.rectangle((m0x, m0y, m1x, m1y), outline=lin((1.0, 0.3, 0.25) if refused else (0.75, 0.65, 0.45), A(0.9)), width=K)
        text_c(d, ((m0x + m1x) / 2, (m0y + m1y) / 2 - K), sc("MANA  %d / %d" % (math.floor(r["mana"]), r["mmana"])), fl_tiny, (255, 255, 255, int(255 * ua)))
    if L4:
        # the potions and food working on her: a chip each over the panel, with the seconds left
        ex = bx
        for e in reversed(USED):
            it = ITEMS.get(e["entry"].split("|")[1]) if e["entry"].startswith("item|") else None
            if not e.get("ok") or it is None or it["kind"] not in ("speed", "food") or not 0 <= t - e["t"] < it["seconds"]: continue
            s = ("SPEED +%d%%  %ds" % (round(it["amount"] * 100), math.ceil(it["seconds"] - (t - e["t"])))) if it["kind"] == "speed" else ("REGEN +%.1f/s  %ds" % (it["amount"] * r["mhp"], math.ceil(it["seconds"] - (t - e["t"]))))
            ic = ("chip_speed" if it["kind"] == "speed" else "chip_regen") if UI else None
            iw = (30 * K) if (ic and UI.has(ic)) else 0
            s = sc(s); tw = d.textlength(s, font=fl_tiny); c0 = (ex - tw - 16 * K - iw, ay - 8 * K - 30 * K - up)
            d.rectangle((c0[0], c0[1], ex, ay - 8 * K - up), fill=lin((0.10, 0.22, 0.30) if it["kind"] == "speed" else (0.12, 0.26, 0.12), A(0.85)), outline=lin(CYAN if it["kind"] == "speed" else (0.45, 0.9, 0.45), A(1.0)), width=K)
            if iw: UI.fit(o, ic, (c0[0] + 4 * K, c0[1] - 6 * K), (c0[0] + iw, ay - 2 * K - up), (1, 1, 1, ua)); d = ImageDraw.Draw(o, "RGBA")
            d.text((c0[0] + 8 * K + iw, c0[1] + 6 * K), s, font=fl_tiny, fill=(255, 255, 255, int(255 * ua))); ex = c0[0] - 8 * K
    # (level 5's weapons: the list as it is now; at most three slots, round the one in her hands: ARDHUD::DrawCombat)
    WL = weapons_at(t); total_w = len(WL); n = min(total_w, 3); first_w = max(0, min(r["w"] - 1, total_w - 3)) if total_w > 3 else 0
    gp = 8 * K; sw = (pw - pd * 2 - gp * (n - 1)) / n
    if total_w > 3:
        d.text((bx - pd, ay + 76 * K + mb + hx + 70 * K), "%d of %d weapons  ·  %d before, %d after  (wheel)" % (n, total_w, first_w, total_w - first_w - n), font=f_tiny, fill=lin((0.72, 0.70, 0.66), A(1.0)), anchor="ra")
    for j in range(n):
        i = first_w + j; wd = WL[i]
        on = i == r["w"]; sx0, sy0 = ax + pd + j * (sw + gp), ay + 76 * K + mb + hx; sx1, sy1 = sx0 + sw, sy0 + 66 * K
        dur = ("%d / %d" % (wd["wear"], wd["durability"])) if wd.get("durability", 0) > 0 else ""
        ic = wicon(wd["name"])
        if ic and sw - (66 - 8) * K - 16 * K < 80 * K: ic = None        # (the picture only where the text has room beside it)
        if UI and UI.has("slot"):
            sp = 18 * K / max(UI.L["slot"]["border"][0] * UI.img["slot"].size[0], 1)
            UI.nine(o, "slot", (sx0, sy0), (sx1, sy1), sp, (1.15, 1.05, 0.85, ua) if on else (0.62, 0.62, 0.62, ua)); d = ImageDraw.Draw(o, "RGBA")
            if on: d.rectangle((sx0 + 1, sy0 + 1, sx1 - 1, sy1 - 1), outline=lin((1.0, 0.82, 0.35), 0.85 * ua), width=2 * K)
        else:
            d.rectangle((sx0, sy0, sx1, sy1), fill=lin((0.36, 0.27, 0.10), A(0.95)) if on else lin((0.10, 0.10, 0.12), A(0.9)), outline=lin((1.0, 0.82, 0.35), A(1.0)) if on else lin((0.40, 0.38, 0.34), A(1.0)), width=int((2.5 if on else 1) * K))
        tc = (255, 255, 255, int(255 * ua)) if on else lin((0.72, 0.70, 0.66), A(1.0))
        if ic and UI.has(ic):
            # (the weapon's picture on the left; its name, damage and mana a line each beside it: ARDHUD::DrawCombat)
            iw = (sy1 - sy0) - 8 * K
            UI.fit(o, ic, (sx0 + 10 * K, sy0 + 8 * K), (sx0 + 6 * K + iw, sy1 - 8 * K), (1, 1, 1, ua) if on else (0.7, 0.7, 0.7, ua)); d = ImageDraw.Draw(o, "RGBA")
            d.text((sx0 + 7 * K, sy0 + 3 * K), str(i + 1), font=ft_tiny, fill=lin((1.0, 0.82, 0.35), A(1.0)) if on else tc)
            cx0, cx1 = sx0 + iw + 10 * K, sx1 - 6 * K
            d.text(((cx0 + cx1) / 2, sy0 + 18 * K), sc(wd["name"].upper()), font=fl_small, fill=tc, anchor="mm")
            dm = "%.1f damage" % wd["damage"] if abs(wd["damage"] - round(wd["damage"])) > 0.05 else "%.0f damage" % wd["damage"]
            d.text(((cx0 + cx1) / 2, sy0 + 37 * K), dm, font=f_tiny, fill=lin((1.0, 0.9, 0.6), A(1.0)) if on else tc, anchor="mm")
            if wd.get("mana"): d.text(((cx0 + cx1) / 2, sy0 + 53 * K), "%.0f mana" % wd["mana"], font=f_tiny, fill=lin((0.55, 0.7, 1.0), A(1.0)), anchor="mm")
            elif dur: d.text(((cx0 + cx1) / 2, sy0 + 53 * K), dur, font=f_tiny, fill=lin((1.0, 0.45, 0.3) if wd["wear"] < wd["durability"] * 0.2 else (0.75, 0.85, 0.7), A(1.0)), anchor="mm")
            continue
        on = on if not (L2 and wd.get("spell")) else any(e["t"] <= t <= e["t"] + 0.9 for e in CASTS)
        d.text((sx0 + 7 * K, sy0 + 3 * K), "RMB / E" if (L2 and wd.get("spell")) else (str(i + 1) if i < 3 else "wheel"), font=ft_tiny, fill=lin((1.0, 0.82, 0.35), A(1.0)) if on else tc)
        # (a name too wide for its slot goes on two lines, split at the space nearest its middle, and smaller if a line is
        # still too wide; a line too wide likewise: ARDHUD::DrawCombat)
        nm_ = wd["name"].upper(); room = sw - 10 * K
        nl = [nm_]
        if d.textlength(sc(nm_), font=fl_small) > room and " " in nm_:
            cut = min((i_ for i_, ch in enumerate(nm_) if ch == " "), key=lambda i_: abs(i_ - len(nm_) // 2)); nl = [nm_[:cut], nm_[cut + 1:]]
        wmax = max(d.textlength(sc(x), font=fl_small) for x in nl)
        fn_ = fit_font("AlegreyaSC-700", 18, max(0.55, min(1.0, room / wmax))) if LETTERS else fl_small
        for li, x in enumerate(nl):
            d.text(((sx0 + sx1) / 2, sy0 + ((19 + 14 * li) if len(nl) > 1 else 26) * K), sc(x), font=fn_, fill=tc, anchor="mm")
        dmg = ("%.0f damage  ·  %.0f mana" % (wd["damage"], wd["mana"])) if wd.get("mana") else ("%.1f damage" % wd["damage"] if abs(wd["damage"] - round(wd["damage"])) > 0.05 else "%.0f damage" % wd["damage"])
        if dur: dmg = ("%.0f" % wd["damage"]) + "  ·  " + dur if total_w > 3 else dmg + "  ·  " + dur
        fd_ = f_tiny; wdm = d.textlength(dmg, font=f_tiny)
        if LETTERS and wdm > sw - 8 * K: fd_ = fit_font("Alegreya-500", 15.5, max(0.6, (sw - 8 * K) / wdm))
        d.text(((sx0 + sx1) / 2, sy0 + (52 if len(nl) > 1 else 48) * K), dmg, font=fd_, fill=lin((1.0, 0.9, 0.6), A(1.0)) if on else tc, anchor="mm")
    d.text((ax + pd, by - 26 * K), C["hint"], font=f_tiny, fill=lin((0.7, 0.68, 0.62), A(1.0)))
    # ---- the keys that do what she does now (above the status panel): W A S D lit as she moves (W: the way she faces),
    # Shift as she runs, E as she casts, F as she opens a door or chest
    mv, kh = r.get("moving", ""), r.get("keys", "")
    caps = [("W", mv != ""), ("A", False), ("S", False), ("D", False), ("SHIFT", mv == "run")] + ([("LMB", kh == "lmb")] if L2 else []) + [("E", kh == "e"), ("F", kh == "f")]
    if L3: caps = [("W", mv != ""), ("A", False), ("S", False), ("D", False), ("SHIFT", mv == "run"), ("1", kh == "1"), ("2", kh == "2"), ("LMB", kh == "lmb"), ("B", kh == "b" or r.get("rolling", 0) == 1), ("F", kh == "f")]
    inv_open = L4 and r.get("inv", [0, 0])[0] == 1
    if L4:
        caps = [("W", mv != "" or kh == "w"), ("A", False), ("S", kh == "s"), ("D", False), ("SHIFT", mv == "run")]
        caps += ({"Mage": [("1", kh == "1"), ("2", kh == "2"), ("E", kh == "e")], "Summoner": [("1", kh == "1"), ("2", kh == "2"), ("E", kh == "e")], "Warlock": [("LMB", kh == "lmb"), ("E", kh == "e")],
                  "Rogue": [("1", kh == "1"), ("2", kh == "2"), ("LMB", kh == "lmb"), ("B", kh == "b" or r.get("rolling", 0) == 1)]}.get(HERO, [("LMB", kh == "lmb")]))
        caps += [("I", kh == "i" or inv_open)] + ([("ENTER", kh == "enter")] if inv_open else []) + [("F", kh == "f"), ("M", kh == "m" or mapo)]
        if mapo: caps = [("W", mv != ""), ("SHIFT", mv == "run"), ("M", True)]         # (only what she uses: the row fits beside the map's board)
    kw = {"SHIFT": 112, "LMB": 76, "ENTER": 100}; gap = 8 * K; total = sum(kw.get(c, 52) * K for c, _ in caps) + gap * (len(caps) - 1) + 24 * K
    kx = bx - 16 * K - total; ky = ay - 100 * K - (up + 6 * K if ext else 0)     # (above the effect chips)
    d.rounded_rectangle((kx - 14 * K, ky - 52 * K, kx + total + 14 * K, ky + 64 * K), 14 * K, fill=(12, 11, 9, int(150 * ua)))
    k0x = kx
    for i, (c, on) in enumerate(caps):
        w_ = kw.get(c, 52) * K
        if c == "SHIFT": kx += 24 * K
        d.rounded_rectangle((kx, ky, kx + w_, ky + 52 * K), 9 * K, fill=(238, 214, 150, int(255 * ua)) if on else (60, 58, 54, int(220 * ua)), outline=(255, 236, 180, int(255 * ua)) if on else (120, 112, 98, int(200 * ua)), width=2 * K)
        d.text((kx + w_ / 2, ky + 26 * K), c, font=ft_small if c in ("SHIFT", "LMB", "ENTER") else f_head, fill=(28, 24, 18, int(255 * ua)) if on else (210, 204, 190, int(230 * ua)), anchor="mm")
        kx += w_ + gap
    lab = "run" if mv == "run" else "walk" if mv == "walk" else ""
    lab = "cast the fire spell" if kh == "e" else "swing the sword" if kh == "lmb" else "open" if kh == "f" else lab
    if L3:
        drawn = C["weapons"][r["w"]]["name"].lower() if 0 <= r["w"] < len(C["weapons"]) else ""
        lab = ("roll" if (kh == "b" or r.get("rolling", 0)) else "shoot the crossbow" if (kh == "lmb" and drawn == "crossbow") else "strike with the daggers" if kh == "lmb"
               else "draw the daggers" if kh == "1" else "draw the crossbow" if kh == "2" else "open" if kh == "f" else ("run" if mv == "run" else "walk" if mv == "walk" else ""))
    if L4 and kh in ("i", "s", "w", "enter", "e", "1", "2", "m") or (L4 and HERO in ("Warrior", "Warlock") and kh == "lmb"):
        drawn = C["weapons"][r["w"]]["name"].lower() if 0 <= r["w"] < len(C["weapons"]) else ""
        le_ = last_at(USED, t)
        use = ("put it on" if le_ and le_["entry"].startswith("armour|") else "use it")
        lab = {"i": "close the inventory" if not inv_open else "open the inventory", "s": "down the list", "w": "up the list", "enter": use,
               "m": "open the map" if mapo else "close the map",
               "e": ("cast the " + drawn) if HERO in ("Mage", "Summoner") else "cast the fire", "1": "draw the " + C["weapons"][0]["name"].lower(),
               "2": "draw the " + (C["weapons"][1]["name"].lower() if len(C["weapons"]) > 1 else ""), "lmb": "swing the sword"}[kh]
    if W5 and kh == "lmb":
        # (the weapons reels: the weapon in her hands now, found ones too; the Rogue's as well)
        wl_ = weapons_at(t); wn_ = wl_[r["w"]] if 0 <= r.get("w", -1) < len(wl_) else None
        if wn_: lab = ("shoot the " if wn_.get("ranged") else "strike with the " if HERO == "Rogue" else "swing the ") + wn_["name"].lower()
    if lab: text_c(d, ((k0x + kx) / 2, ky - 24 * K), lab, f_line, (244, 240, 228, int(240 * ua)))
    # ---- the banner when a section is generated (the weapons reel: not the sets the reel made behind its card)
    for e in GENS:
        age = t - e["t"]
        if W5 and JUMP and AT_GRATING and JUMP["t"] - 0.1 <= e["t"] <= AT_GRATING["t"] + 0.5: continue
        if C5 and CARD and CARD[0] - 0.1 <= e["t"] <= CARD[1] + 0.5: continue
        if 0.0 <= age < 3.5: text_c(d, (W * K / 2, 212 * K), ("NEW DUNGEON SECTION GENERATED" if LETTERS else "\u25b2 NEW DUNGEON SECTION GENERATED"), f_ban, lin(CYAN, max(0.0, min(age / 0.3, (3.5 - age) / 0.8, 1.0))))
    if W5:
        # ---- level 5's tiers: a set cleared, a tier opened (ARDHUD, under the top), and what a seal says by it
        tn = last_at(TNOTE, t)
        if tn and 0.0 <= t - tn["t"] < 4.5 and not (JUMP and AT_GRATING and JUMP["t"] <= tn["t"] <= AT_GRATING["t"]):
            ag = t - tn["t"]; a_ = max(0.0, min(1.0, ag / 0.3, (4.5 - ag) / 0.8))
            text_c(d, (W * K / 2, 160 * K), tn["text"], f_ban, lin((1.0, 0.82, 0.35), a_))
        if r.get("seal"):
            s_ = r["seal"]; tw = d.textlength(s_, font=f_line); y_ = H * K * 0.72
            d.rectangle((W * K / 2 - tw / 2 - 14 * K, y_ - 8 * K, W * K / 2 + tw / 2 + 14 * K, y_ + 38 * K), fill=lin((0.10, 0.02, 0.02), 0.7 * ua))
            d.text((W * K / 2, y_), s_, font=f_line, fill=lin((1.0, 0.75, 0.65), ua), anchor="ma")
    # ---- the reel's own: title, captions (bottom left)
    a = fade(t, 0.3, 4.6)
    if a > 0:
        d.text((44 * K, 34 * K), "random_dungeonmagic_level" + ("" if LV == "1" else LV), font=f_title, fill=(255, 255, 255, int(235 * a)), stroke_width=2 * K, stroke_fill=(0, 0, 0, int(140 * a)))
        d.text((46 * K, 86 * K), ("procedural dungeon  \u00b7  the %s, chosen in the menu  \u00b7  armour by its table, loot by tier, repair items made at anvils" % HERO.lower() if C5 else
                                  "procedural dungeon  \u00b7  the %s, chosen in the menu  \u00b7  %s" % (HERO.lower(), WHO[HERO].replace("the %s " % HERO, "she ", 1)) if Q5 else
                                  "procedural dungeon  \u00b7  the warrior, chosen in the menu  \u00b7  a weapons table and five tiers of rooms" if W5 else
                                  "procedural dungeon  \u00b7  the summoner, chosen in the menu  \u00b7  five armour sets to find and wear" if L5 else
                                  ("procedural dungeon  \u00b7  the %s, chosen in the menu  \u00b7  %s" % (HERO.lower(), HJ[HERO]["starts_with"].lower())) if L4 else
                                  "procedural dungeon  \u00b7  two daggers, a crossbow and a roll  \u00b7  the Rogue" if L3 else
                                  "procedural dungeon  \u00b7  fire from the left hand, a sword in the right  \u00b7  girl-darkcaster-tripo" if L2 else
                                  "procedural dungeon  \u00b7  a fire spell at medium range  \u00b7  girl-caster-tripo"), font=f_sub, fill=(232, 236, 240, int(225 * a)), stroke_width=2 * K, stroke_fill=(0, 0, 0, int(140 * a)))
    caps = []
    t_first = FIGHTS[0]["t"] if FIGHTS else 6.0
    t_chest = CHESTS[0]["t"] if CHESTS else 99.0
    XB = next((w_ for w_ in C["weapons"] if w_.get("spell")), None); DG = next((w_ for w_ in C["weapons"] if not w_.get("spell")), None)
    if L4:
        hj = HJ[HERO]
        # (level 5: her caption stays until the first chest's takes over)
        caps.append((0.8, (INVS[0]["t"] if INVS else 30.0) if L5 else min(t_first - 0.2, t_chest - 0.4, (GENS[0]["t"] if GENS else 99) - 0.2), "THE " + HERO.upper(), ["  ·  ".join(hj["abilities"]),
                     "%d hit points%s  ·  %s" % (hj["health"], ("  ·  %d mana, %.1f a second back" % (hj["mana"], hj["mana_per_second"])) if hj["mana"] else "", hj["starts_with"].lower())], tuple(int(255 * v) for v in hj["accent"])))
        for e in INVS:
            # (what she does there is said once she has done it)
            u = next((x for x in USED if x["t"] >= e["t"]), None); end = (u["t"] + 1.9) if u else e["t"] + 2.6
            head, first = "I  ·  HER INVENTORY", "what the containers held goes in with her weapons; she wields and uses them from here (in play the game pauses)"
            if W5 and e.get("why") == "wield" and u:
                # (the weapons reel: a weapon of the table wielded; said with its numbers while the camera goes round her)
                nm = e.get("weapon", ""); wd = next((w_ for w_ in weapons_at(u["t"] + 0.1) if w_["name"] == nm), None)
                nxt = next((x["t"] for x in INVS if x["t"] > e["t"]), u["t"] + 9.0)
                cl = inv_closed_after(u["t"])           # (said once the inventory is shut: open, it covers the captions)
                if BROKE and e["t"] > BROKE["t"]:
                    # (after the break: the list without it)
                    caps.append((cl, cl + 4.5, "I  ·  ENTER  ·  HER WEAPONS NOW", ["the %s is gone from the list: %s" % (BROKE["weapon"].lower(), ", ".join(w_["name"].lower() for w_ in weapons_at(e["t"]))),
                                 "she wields the %s again (%d of %d durability left)" % (nm.lower(), round(wd["wear"]), wd["durability"]) if wd else "she wields the %s again" % nm.lower()], (255, 226, 150)))
                    continue
                if wd and wd.get("speed"):
                    bonus = wd["damage"] / max(wd["base_damage"], 1e-3) - 1.0
                    caps.append((cl, min(nxt - 0.05, cl + 6.5), "I  ·  ENTER  ·  " + nm.upper(),
                                 ["from her inventory: what she finds joins her weapons, and %s" % WHO[HERO],
                                  "%s  ·  speed %d / 10: an attack every %.2f s  ·  damage %d / 10: %.0f a %s (8 + 3 x %d)%s" % (
                                  wd["type"], wd["speed"], 1.6 - (wd["speed"] - 1) * 1.05 / 9.0, wd["rating"], wd["base_damage"], "shot" if wd.get("ranged") else "blow", wd["rating"],
                                  (", %.1f with her +%d%%" % (wd["damage"], round(bonus * 100))) if bonus > 0.005 else ""),
                                  "durability %d: each %s that lands takes 1 off, at 0 it breaks  ·  %s" % (wd["durability"], "arrow" if wd.get("ranged") else "blow",
                                  "a bow shot made in Blender for her: the bow in her left hand, drawn to her cheek" if wd.get("ranged") and "bow" in nm.lower() else
                                  "two-handed cuts made in Blender for her: both hands on the hilt" if wd["type"] == "two handed sword" else
                                  "her own dagger strikes" if HERO == "Rogue" else "her own sword cuts")], (255, 226, 150)))
                continue
            if Q5 and e.get("why") == "refused" and u:
                # (run5h: Enter on what her hero cannot use; the game's words, then why: said once the inventory is shut)
                cl = inv_closed_after(u["t"]); nxt = next((x["t"] for x in INVS if x["t"] > e["t"]), cl + 9.0)
                it = ITEMS.get(e.get("item", ""), {})
                why = ([wears_line(it), "the %s: %s" % (e.get("item", "").lower(), it.get("looks", ""))] if e.get("what") == "armour" else
                       ["%s: what she cannot wield goes into her bag under its own heading" % WHO[HERO],
                        "the %s: %s  ·  wielded by %s" % (e.get("item", "").lower(), it.get("looks", "").split("  ")[0], " and ".join("the " + h_.lower() for h_ in it.get("wielded_by", [])) or "nobody")])
                caps.append((cl, min(nxt - 0.05, cl + 3.6), "I  ·  ENTER  ·  " + u["message"].upper(), why, (255, 170, 130)))
                continue
            if L5 and e.get("why") == "armour" and u:
                # (level 5: a set put on; said while the camera goes round her)
                nm = u["entry"].split("|")[1]; it = ITEMS.get(nm, {}); n_ = sum(1 for x in USED if x["entry"].startswith("armour|") and x["t"] <= u["t"])
                nxt = next((x["t"] for x in INVS if x["t"] > e["t"]), u["t"] + 5.0)
                caps.append((e["t"], u["t"], "I  ·  ENTER  ·  ARMOUR", [("the sets she found are in her inventory; " if Q5 else "the five sets she found are in her inventory; ") + "one is worn at a time (in play the game pauses here)",
                             "she goes down the list to the %s and puts it on" % nm.lower()], (255, 226, 150)))
                caps.append((u["t"], min(nxt - 0.05, u["t"] + 4.6), nm.upper() + ("" if n_ < 6 else "  ·  AGAIN"),
                             [(("%s armour  ·  " % it["weight"]) if it.get("weight") else "") + (it.get("looks", "")[:1].upper() + it.get("looks", "")[1:]) + "  ·  each blow on her takes %d%% less" % round(it.get("amount", 0) * 100),
                              wears_line(it) if Q5 else "made for her body from a Fab warrior's armour: it moves with her skeleton (the game puts the set's mesh on her bones)"], lin(CYAN)[:3]))
                continue
            if u:
                caps.append((e["t"], u["t"], head, [first, "she goes down the list to what helps her now"], (255, 226, 150)))
                caps.append((u["t"], end, head, [first, u["message"]], (255, 226, 150)))
            else: caps.append((e["t"], end, head, [first, "she looks down the list"], (255, 226, 150)))
        for e in [x for x in EV if x["kind"] == "map" and x.get("open")]:
            # (the big map: from M to M)
            e1 = next((x["t"] for x in EV if x["kind"] == "map" and not x.get("open") and x["t"] > e["t"]), e["t"] + 4.0)
            caps.append((e["t"], e1, "M  ·  THE BIG MAP", ["the dungeon so far, as the minimap draws it", "the game goes on under it: she walks on"], (255, 226, 150)))
    elif L3:
        caps.append((0.8, min(t_first - 0.2, t_chest - 0.4, (GENS[0]["t"] if GENS else 99) - 0.2), "THE ROGUE", ["Rogue.glb: her own walk and run; an idle, three dagger strikes, a crossbow shot and a roll made for her in Blender",
                     "WASD walk  \u00b7  Shift run  \u00b7  1 / 2 daggers / crossbow  \u00b7  left mouse strikes or shoots  \u00b7  B rolls  \u00b7  F opens"], (255, 240, 214)))
    elif L2:
        caps.append((0.8, min(t_first - 0.2, t_chest - 0.4, (GENS[0]["t"] if GENS else 99) - 0.2), "FIRE AND STEEL", ["girl-darkcaster-tripo: her own idle, walk and run, and two left-hand casts and three sword cuts made for her in Blender",
                     "WASD walk  \u00b7  Shift run  \u00b7  left mouse: the sword  \u00b7  right mouse or E: the fire  \u00b7  F opens doors and containers"], (255, 240, 214)))
    else:
        caps.append((0.8, min(t_first - 0.2, t_chest - 0.4, (GENS[0]["t"] if GENS else 99) - 0.2), "A FIRE CASTER", ["girl-caster-tripo: her own walk and run, and an idle and three casts made for her in Blender",
                     "WASD walk  \u00b7  Shift run  \u00b7  left mouse or E: the fire spell  \u00b7  F opens doors and containers"], (255, 240, 214)))
    for e in CHESTS:
        if W5:
            fd = next((x for x in FOUND if x["t"] >= e["t"] - 0.05), None); held = fd.get("items", []) if fd else []
            wp = [x for x in held if ITEMS.get(x, {}).get("kind") == "weapon"]
            caps.append((e["t"] - 0.3, e["t"] + 2.6, "F  ·  A CHEST OF THE GREAT HALL", ["it held %d things%s" % (len(held), (": " + " and ".join(x.lower() for x in wp) + " among them") if wp else ""),
                         "the table's weapons are in the containers of their tiers of rooms: these are tier 1's  ·  " +
                         ("one session seed for the four heroes: the same chests hold the same weapons" if Q5 else "as rare as their rarity")], (255, 226, 150)))
            continue
        if L5:
            fd = next((x for x in FOUND if x["t"] >= e["t"] - 0.05), None); held = fd.get("items", []) if fd else []
            arm = [x for x in held if ITEMS.get(x, {}).get("kind") == "armour"]
            caps.append((e["t"] - 0.3, e["t"] + 2.4, "F  \u00b7  A CHEST OF THE GREAT HALL", ["up to six things in a container: this one held %d%s" % (len(held), (", " + " and ".join(a.lower() for a in arm)) if arm else ""),
                         "the five armour sets are in the great hall's chests, the first room"], (255, 226, 150)))
            continue
        caps.append((e["t"] - 0.3, e["t"] + 1.6, "F  \u00b7  THE %s OPENS" % e["what"].split()[-1].upper(), ["every door and container of the dungeon opens: chests, trunks, wardrobes, barrels, crates"], (255, 226, 150)))
    if W5:
        if BROKE:
            caps.append((BROKE["t"], BROKE["t"] + 3.6, "THE %s BREAKS" % BROKE["weapon"].upper(), ["no durability left: it is gone from her weapons and from her inventory",
                         "she has the %s in hand again: the weapons a hero starts with are kept and never break" % BROKE["now"].lower()], (255, 150, 120)))
        if CARD:
            t_lm = LAST_M["t"] if LAST_M else CARD[1] + 6.0
            caps.append((CARD[1] - 0.2, t_lm, "A SEALED GRATING  ·  TIER 2 TO TIER 3", ["the ways out of tier 2 are barred until all 8 of its sets are cleared:",
                         "every room walked into, every chest and trunk opened, every monster killed  ·  under the minimap: each tier's sets cleared"], (255, 200, 120)))
        if OPENED:
            caps.append((OPENED["t"], OPENED["t"] + 5.0, OPENED["text"], ["the last set of tier 2 cleared: the gratings toward tier 3 are gone",
                         "tier 3's 16 sets open tier 4's 24, and those open tier 5, the last: past it stand walls"], (255, 200, 120)))
            g3 = next((e for e in GENS if e["t"] > OPENED["t"]), None)
            if g3: caps.append((max(g3["t"], OPENED["t"] + 4.2), max(g3["t"], OPENED["t"] + 4.2) + 4.5, ("" if LETTERS else "▲ ") + "TIER 3 IS GENERATED AS SHE NEARS IT", ["a set of 252 m x 252 m: stronger monsters, and the table's weapons of tier 3 in its chests",
                                 "never saved: a new dungeon every time"], lin(CYAN)[:3]))
    for e in ([] if W5 else GENS[:1]):
        caps.append((e["t"], min(e["t"] + 4.2, t_first - 0.1 if t_first > e["t"] else 99), ("" if LETTERS else "\u25b2 ") + "THE NEXT 252 m x 252 m OF DUNGEON IS GENERATED", ["as she nears the edge of what there is  \u00b7  never saved: a new dungeon every time"], lin(CYAN)[:3]))
    for i, e in enumerate(FIGHTS):
        end = next((k["t"] for k in KILLS if k["t"] > e["t"]), e["t"] + 6.0) + 1.2
        if i + 1 < len(FIGHTS): end = min(end, FIGHTS[i + 1]["t"] - 0.1)
        tier = "start section" if list(e["section"][:2]) == [0, 0] else "generated section"
        cs = [c for c in CASTS if e["t"] <= c["t"] <= end]
        note = ("the first square's monsters are weaker than her" if list(e["section"][:2]) == [0, 0] else "in the generated sections they are on a par with her (the average: %.0f hit points, %.0f a blow)" % tuple(C["runtime_tier"]))
        more = ("the bolt: %.0f m reach, %.0f m/s, it follows the monster she turned to and bursts on the first thing it meets" % (SPELL["reach"] / 100.0, SPELL["speed"] / 100.0),
                "the burst also burns every other monster within %.1f m for half the damage" % (SPELL["splash"] / 100.0),
                "the music turns to a battle track when a monster comes at her")[min(i, 2)]
        if L3:
            rl = [x for x in ROLLS if e["t"] <= x["t"] <= end]; dg = [x for x in DODGED if e["t"] <= x["t"] <= end]
            more = ("B: a roll %.1f m out of its reach, and blows miss her through most of it%s" % (C.get("roll_distance", 420.0) / 100.0, (" (%d missed her)" % len(dg)) if dg else "") if rl else
                    ("the crossbow bolt: %.0f m reach, %.0f m/s, straight at the monster she turned to; it sticks where it strikes a wall" % (SPELL["reach"] / 100.0, SPELL["speed"] / 100.0),
                     "the daggers strike fast, one hand, the other, then both",
                     "the music turns to a battle track when a monster comes at her")[min(i, 2)])
        if W5:
            # (the weapons reel: the weapon in her hands and what it does; its wear; the tier of the set)
            tr = max(abs(e["section"][0]), abs(e["section"][1])) + 1
            wl_ = weapons_at(e["t"] + 0.05)
            if not e.get("weapon"): e = dict(e, weapon=wl_[0]["name"], damage=wl_[0]["damage"])      # (a fight on the way to a chest: her own sword)
            wd = next((w_ for w_ in wl_ if w_["name"] == e.get("weapon")), None) or {}
            if e.get("damage") is None: e = dict(e, damage=wd.get("damage", 0))
            ws_ = WEAR_SET if (WEAR_SET and "weapon" in WEAR_SET and WEAR_SET["t"] <= e["t"] and (not BROKE or e["t"] <= BROKE["t"])) else None     # (run5c's wear_set is a set of armour)
            lm = LAST_M if (LAST_M and abs(LAST_M["t"] - e["t"]) < 0.5) else None
            unit = "cast" if (wd.get("spell") and not wd.get("ranged")) else "shot" if wd.get("ranged") else "blow"
            own = "her own %s: the weapons a hero starts with are kept and never break" % (e.get("weapon") or "").lower()
            l1 = "%.0f hit points, %.0f damage a blow  ·  she has %.0f  ·  in her hands: the %s, %s a %s%s" % (e["its_hit_points"], e["its_damage"], C["max_health"],
                 (e.get("weapon") or "").lower(), ("%.1f" % e.get("damage", 0)).rstrip("0").rstrip("."), unit, (", shot from %.0f m" % e["from_m"] if wd.get("ranged") else ""))
            if e.get("spells"):
                # (run5h's Mage: her spells; none of the table's weapons)
                fi = next((w_ for w_ in wl_ if w_["name"] == "Fire"), {}); df = next((w_ for w_ in wl_ if w_["name"] == "Dark Fire"), {})
                l1 = "%.0f hit points, %.0f damage a blow  ·  she has %.0f  ·  dark fire %s a cast, then fire %s" % (e["its_hit_points"], e["its_damage"], C["max_health"],
                     ("%.1f" % df.get("damage", 0)).rstrip("0").rstrip("."), ("%.1f" % fi.get("damage", 0)).rstrip("0").rstrip("."))
                l2 = "every cast takes mana: dark fire %d, fire %d; it comes back at %.1f a second" % (df.get("mana", 0), fi.get("mana", 0), C.get("mana_per_second", 0))
                l3 = WHO[HERO] + " (the weapons she found are in her bag)"
                if lured(e): l3 = lured(e)
                caps.append((e["t"], end, "%s  ·  TIER %d" % (e["monster"].replace("_", " ").upper(), tr), [l1, l2, l3], (255, 226, 150)))
                continue
            if lm: l2, l3 = "tier 2's last set: one monster left in it", "when it falls every set of tier 2 is cleared and tier 3 opens"
            elif tr >= 3: l2, l3 = "a monster of tier 3: its hit points and blows grow with the tier of its set", \
                                   "the %s: %d of %d durability left" % ((e.get("weapon") or "").lower(), round(wd.get("wear", 0)), wd.get("durability", 0)) if wd.get("durability") else own
            elif ws_: l2, l3 = "the reel started the %s at 3 of its %d durability: each blow that lands takes 1 off" % (ws_["weapon"].lower(), ws_["durability"]), \
                               "at 0 it breaks and is gone; the %s she started with never breaks" % (wl_[0]["name"].lower() if wl_ else "sword")
            elif wd.get("speed"): l2, l3 = "speed %d / 10: an attack every %.2f s (the clip played at %.2f x)  ·  damage %d / 10" % (wd["speed"], 1.6 - (wd["speed"] - 1) * 1.05 / 9.0, wd.get("rate", 1.0), wd["rating"]), \
                                          "durability %d of %d: 1 off each blow that lands" % (round(wd["wear"]), wd["durability"])
            else: l2, l3 = own, "the monsters' strength follows the tier of their set"
            if lured(e): l3 = lured(e)
            caps.append((e["t"], end, "%s  ·  TIER %d" % (e["monster"].replace("_", " ").upper(), tr), [l1, l2, l3], (255, 226, 150)))
            continue
        if L5 and e.get("take"):
            # (level 5: she lets it come; its blows land on her armour)
            bl = [b for b in BLOWS if e["t"] <= b["t"] <= min(end, t)]
            note = "she lets it come in the %s: each of its blows on her loses %d%%" % ((e.get("armour") or "armour").lower(), round(bl[0]["armour"] * 100) if bl else 0)
            more = ("its blows: " + ",  ".join("%s reached her as %s" % (("%.2f" % b["before"]).rstrip("0").rstrip("."), ("%.2f" % b["reached"]).rstrip("0").rstrip(".")) for b in bl)) if bl else "it comes at her"
        elif L4:
            note = "the monsters are the same whoever she is: the first square's are weaker than her" if list(e["section"][:2]) == [0, 0] and tier == "start section" else note
            if i == 0 and HERO != "Summoner":
                more = ({"Warrior": lambda: "her melee bonus: +%d%% on every blow (the sword's %.0f is %.1f)" % (round(C["melee_bonus"] * 100), C["weapons"][0]["base_damage"], C["weapons"][0]["damage"]),
                         "Mage": lambda: "every cast takes mana: fire %.0f, dark fire %.0f; it comes back at %.1f a second" % (C["weapons"][0]["mana"], C["weapons"][1]["mana"], C["mana_per_second"]),
                         "Warlock": lambda: "fire from her left hand takes %.0f mana; the sword in her right takes none" % next(w_["mana"] for w_ in C["weapons"] if w_.get("spell")),
                         "Rogue": lambda: "her ranged bonus: +%d%% on every bolt (the crossbow's %.0f is %.1f)  \u00b7  B rolls her out of a blow" % (round(C["ranged_bonus"] * 100), XB["base_damage"], XB["damage"])})[HERO]()
        caps.append((e["t"], end, "%s  \u00b7  %s" % (e["monster"].replace("_", " ").upper(), tier),
                     [("%.0f hit points, %.0f damage a blow  \u00b7  she has %.0f; %s" % (e["its_hit_points"], e["its_damage"], C["max_health"],
                       ", ".join("%s %s" % (w_["name"].lower(), ("%.1f" % w_["damage"]).rstrip("0").rstrip(".")) for w_ in C["weapons"]))) if L4 else
                      ("%.0f hit points, %.0f damage a blow  \u00b7  she has %.0f; a crossbow bolt does %.0f, a dagger strike %.0f  \u00b7  bolts from %.0f m, then the daggers" % (e["its_hit_points"], e["its_damage"], C["max_health"],
                       XB["damage"], DG["damage"], cs[0].get("m", e["from_m"]) if cs and cs[0].get("m") else e["from_m"])) if L3 else
                      ("%.0f hit points, %.0f damage a blow  \u00b7  she has %.0f; her fire bolt does %.0f, her sword %.0f  \u00b7  fire from %.0f m, then the sword" % (e["its_hit_points"], e["its_damage"], C["max_health"],
                       SPELL["damage"], next(w_["damage"] for w_ in C["weapons"] if not w_.get("spell")), cs[0].get("m", e["from_m"]) if cs else e["from_m"])) if L2 else
                      ("%.0f hit points, %.0f damage a blow  \u00b7  she has %.0f, and her fire bolt does %.0f  \u00b7  she casts from %.0f m" % (e["its_hit_points"], e["its_damage"], C["max_health"],
                       SPELL["damage"], cs[0].get("m", e["from_m"]) if cs else e["from_m"])), note, more], (255, 226, 150)))
    if C5:
        global C5CAPS
        if C5CAPS is None: C5CAPS = c5_caps()
        caps = C5CAPS
    # (one caption at a time, in the one place: the one that began last; an earlier one still running shows again after it)
    live = [cp for cp in caps if fade(t, cp[0], cp[1]) > 0]
    for t0, t1, head, lines, c in ([max(live, key=lambda cp: cp[0])] if live else []):
        k = fade(t, t0, t1)
        if k <= 0: continue
        dn = 44 if (C5 and mapo) else 0           # (run5c: under the big map's key while the map is open)
        y = (H - 62 - 36 - 34 * len(lines) + dn) * K
        wd = max([d.textlength(head, font=f_head)] + [d.textlength(s, font=f_line) for s in lines])
        blend_box(o, (32 * K, y - 14 * K, 60 * K + wd, (H - 48 + dn * 0.7) * K), 12 * K, (12, 11, 9, int(180 * k))); d = ImageDraw.Draw(o, "RGBA")
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
        blend_box(o, (32 * K, y - 20 * K, 102 * K + tw, y + 20 * K), 10 * K, (12, 11, 9, int((150 + 70 * hot) * ua)), col + (int(255 * hot * ua),), 2 * K); d = ImageDraw.Draw(o, "RGBA")
        d.text((48 * K, y), "\u266b", font=f_note, fill=col + (int(255 * ua),), anchor="lm"); d.text((86 * K, y), s, font=f_line, fill=(236, 240, 244, int(245 * ua)), anchor="lm")
    # ---- what is heard (left, above the captions): each for a moment, the newest lowest; a torch while she is by it
    lines = [(s, fade(t, t0, t0 + 1.9, 0.12, 0.5)) for t0, s in HEARD if t0 <= t <= t0 + 1.9]
    fire = r.get("fire", -1)
    if 0 <= fire < 520: lines.insert(0, ("a torch crackles", min(1.0, (520 - fire) / 170.0) * ua))
    y = (H - 252) * K
    for s, k in reversed(lines[-4:]):
        if k <= 0: continue
        tw = d.textlength(s, font=f_line)
        blend_box(o, (32 * K, y - 19 * K, 96 * K + tw, y + 19 * K), 10 * K, (12, 11, 9, int(150 * k))); d = ImageDraw.Draw(o, "RGBA")
        d.text((48 * K, y), "\u266a", font=f_note, fill=(150, 220, 255, int(255 * k)), anchor="lm"); d.text((80 * K, y), s, font=f_line, fill=(236, 240, 244, int(245 * k)), anchor="lm")
        y -= 44 * K
    if L4: l4_panels(o, r, t, ua); d = ImageDraw.Draw(o, "RGBA")
    if W5 and CARD and CARD[0] - 0.35 <= t <= CARD[1] + 0.5:
        # (the card over the reel's shortcut: what the generator's debug clear did, said as it is)
        k = max(0.0, min(1.0, (t - CARD[0] + 0.35) / 0.35, (CARD[1] + 0.5 - t) / 0.5))
        d.rectangle((0, 0, W * K, H * K), fill=(4, 4, 6, int(255 * k)))
        text_c(d, (W * K / 2, H * K * 0.36), "TIER 2", f_title, (255, 214, 140, int(255 * k)))
        for i, s_ in enumerate(["the eight sets round the great hall's set: tier 2",
                                "for the reel she is put in one of them, generated as she arrives",
                                "its rooms are written TIER 2 on the maps"] if C5 else
                               ["the eight sets round the start square, each to clear: every room, every chest and trunk, every monster",
                                "for the reel the generator's debug clear does seven of them and all but one monster of the eighth",
                                "she stands in the eighth, at a grating into tier 3"]):
            text_c(d, (W * K / 2, H * K * 0.36 + (90 + 44 * i) * K), s_, f_line, (236, 236, 240, int(235 * k)))
    if t < 0.4: d.rectangle((0, 0, W * K, H * K), fill=(0, 0, 0, int(255 * max(0.0, 1.0 - max(0.0, t - 0.07) / 0.33))))       # (the reel fades in: on the first frames the camera is still settling behind her)
    return o.resize((W, H), Image.LANCZOS)
os.makedirs(dst, exist_ok=True)
frames = sorted(glob.glob(os.path.join(src, "*.png")))
RESUME = os.environ.get("OVERLAY_RESUME") == "1"          # (a run cut short: the frames already drawn are kept)
for i, p in enumerate(frames):
    if i % step: continue
    if RESUME and os.path.exists(os.path.join(dst, f"rdm{'' if LV == '1' else LV}{HERO.lower() if L4 else ''}hud.{i:04d}.png")): continue
    im = Image.open(p).convert("RGBA")
    if im.size != (W, H): im = im.resize((W, H), Image.LANCZOS)
    Image.alpha_composite(im, overlay(i)).convert("RGB").save(os.path.join(dst, f"rdm{'' if LV == '1' else LV}{HERO.lower() if L4 else ''}hud.{i:04d}.png"), compress_level=1)
print("wrote", len(range(0, len(frames), step)), "frames to", dst)
