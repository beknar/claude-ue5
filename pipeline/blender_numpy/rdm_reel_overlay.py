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
Level "5s" (the spells, rings, monsters by tier, corpses and menu reel, 815's run5s: cine_spells_<hero>.json) adds what
level 5's HUD draws since 858: the hotbar (ARDHUD::DrawHotbar: her first ten weapons and spells, the cooldowns shaded with
their seconds, each cast's mana), the chips of her spells on her and the monsters' afflictions, each monster's gallery
name with CURSED / SLOWED / BURNING, her allies' green bars, the inventory's RINGS and TOMES sections, the anvil's BREAK
DOWN list, Esc's menu (ARDHUD::DrawMenu: the four volumes and the three buttons), the number keys and Esc in the keys row,
and the captions of each beat (the captions and the heard lines stand above the hotbar).
Level "mw" (mistward_castle, 815's run5m: SourceArt/mistward/cine_mw_<hero>.json) is drawn as "5c" is, with what the castle's
HUD adds: the rooms' shapes on both maps (the record's masks), its marks (a boss, a guarded ring, her things, a teleporter, a
trap she has seen: ARDHUD::MistMark; a far boss or ring at the map's edge), the castle's name over the minimap and on the big
map's plaque, the frame rate in the upper left (as the game ticked in the render), what F would do near her, the disarm bar,
the fallen banner, the inventory's SHIELDS, TORCH and TELEPORT RINGS, the reel's cards and its captions.
Usage: rdm_reel_overlay.py frames_dir out_dir [step] [level: 1, 2, 3, 4, 5, 5h, 5c, 5s or mw] [level 4 / 5: hero] [level 4 / 5: ui art dir]"""
import sys, os, re, json, glob, math
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
src, dst = sys.argv[1], sys.argv[2]
step = int(sys.argv[3]) if len(sys.argv) > 3 else 1
LV = sys.argv[4] if len(sys.argv) > 4 else "1"
MW3 = LV == "mw3"              # (mistward_castle's five heroes: 815's "mistward3", cine_mw3_<hero>.json; drawn as "mw2")
MW4 = LV == "mw4"              # (mistward_castle's six heroes in combat at all five tiers: 815's "mistward4", cine_mw4_<hero>.json; drawn as "mw2", its own captions)
if MW3 or MW4: LV = "mw2"
M5 = LV in ("mw", "mw2")       # (mistward_castle: 815's run5m)
MW2 = LV == "mw2"              # (mistward_castle's third list: 815's run5m2)
X5 = LV == "5x"; Q5 = LV == "5h"; C5 = LV in ("5c", "5x", "mw", "mw2"); S5 = LV == "5s"; LV = "5" if (Q5 or C5 or S5) else LV        # ("5x": the four heroes' capabilities reel, 815's run5x: cine_caps_<hero>.json, run5c's captions and the tiers' part)
        # ("5h": level 5's four heroes' weapons reel, 815's run5h: cine_quartet_<hero>.json; "5c": run5c, cine_craft_<hero>.json; "5s": run5s, cine_spells_<hero>.json)
K5 = C5 or S5                 # (the anvils and the rooms' tiers on the maps, the crafting panel)
L5 = LV == "5"; L4 = LV == "4" or L5     # (level 5: level 4's HUD and the armour)
HERO = sys.argv[5] if len(sys.argv) > 5 else ("Summoner" if L5 else "Rogue")            # (level 4: whose run: 815 wrote cine_<hero>.json)
UI = None
if L4 and len(sys.argv) > 6:
    from rdm4_ui_draw import UIArt
    UI = UIArt(sys.argv[6])
# (the Martial Artist's fists and chi attacks: their pictures by name, martial_arts.json's (874 gives the game the same))
# (her name as the game shows it: "Martial Artist", not "MartialArtist")
HNAME = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", HERO)
MA_ICONS = {}
if HERO == "MartialArtist":
    _mj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "martial_arts", "martial_arts.json"), encoding="utf-8"))
    MA_ICONS = dict({c_["name"]: c_["icon"] for c_ in _mj["chi"]}, Fists=_mj["fists"].get("icon", ""))
SU4 = None
if MW4 and HERO == "Summoner":
    # (the castle's Summoner (876, the user's list of 2026-10-30): her card and her weapons' pictures, summoner4.json's)
    SU4 = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "mistward", "summoner4.json"), encoding="utf-8"))
    MA_ICONS = dict(SU4["icons"])
def wicon(name):
    if not UI: return None
    # (a spell learned from a tome in the run is not among her card's weapons: its own picture, spell_<name>)
    sp = "spell_" + "".join(ch if ch.isalnum() else "_" for ch in name.lower())
    return UI.weapons.get("%s/%s" % (HERO, name)) or (MA_ICONS[name] if name in MA_ICONS and UI.has(MA_ICONS[name]) else None) \
        or (sp if UI.has(sp) else None)
def iicon(name): return UI.icons.get(name) if UI else None
L2, L3 = LV == "2" or (L4 and HERO == "Warlock"), LV == "3" or (L4 and HERO == "Rogue")
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "random_dungeon_magic" + ("" if LV == "1" else LV))
MWSRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "mistward")
SND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "random_dungeon_combat")      # (the sounds are the combat level's)
R = json.load(open(os.environ["OVERLAY_RECORD"], encoding="utf-8")) if os.environ.get("OVERLAY_RECORD") else \
    json.load(open(os.path.join(MWSRC, f"cine_{'mw4' if MW4 else 'mw3' if MW3 else 'mw2' if MW2 else 'mw'}_{HERO.lower()}.json"), encoding="utf-8")) if M5 else json.load(open(os.path.join(SRC, (f"cine_quartet_{HERO.lower()}.json" if Q5 else f"cine_caps_{HERO.lower()}.json" if X5 else f"cine_craft_{HERO.lower()}.json" if C5 else f"cine_spells_{HERO.lower()}.json" if S5 else f"cine_{HERO.lower()}.json") if L4 else "cine_render.json"), encoding="utf-8"))
W5 = L5 and (HERO == "Warrior" or Q5 or C5 or S5)          # (level 5's weapons and tiers reels: 815's run5w, the Warrior; run5h, any of four; run5c's tiers too)
# (who wields what: the weapons table's rules, weapons_table.json "who")
WHO = {"Warrior": "the Warrior wields every weapon of the table", "Warlock": "the Warlock wields every weapon of the table",
       "Rogue": "the Rogue wields short blades and ranged weapons only", "Mage": "the Mage wields none of the table's weapons: her spells are hers",
       "Summoner": "the Summoner wields none of the table's weapons"}
HJ = ({h["name"]: h for h in json.load(open(os.path.join(SRC, "heroes.json")))["heroes"]} if LV == "4" else
      {h["name"]: h for h in json.load(open(os.path.join(SRC, "..", "random_dungeon_magic4", "heroes.json")))["heroes"]} if W5 else
      {"Summoner": json.load(open(os.path.join(SRC, "summoner_hero.json"), encoding="utf-8"))} if L5 else {})
if HERO == "MartialArtist" and "MartialArtist" not in HJ:
    # (her card is martial_arts.json's: 872 makes her hero from it)
    _mh = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "martial_arts", "martial_arts.json"), encoding="utf-8"))["hero"]
    HJ["MartialArtist"] = dict(_mh, name="MartialArtist")
if SU4 is not None: HJ["Summoner"] = SU4
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
        sk = next((x for x in reversed(CASTS) if x["t"] <= e["t"] + 0.6), None) if S5 else None
        if sk and k[0] == "Player" and len(k) >= 3 and k[1] in ("Charge", "Cast", "Hit") and sk.get("weapon") and e["t"] - sk["t"] < 3.0 and sk["weapon"] not in ("Sword", "Daggers", "Crossbow") and "Sword" not in sk["weapon"]:
            # (run5s: a spell plays the sounds of its kind (a curse the dark fire's): said by the spell she cast)
            HEARD.append((e["t"], {"Charge": "%s gathers in her hand", "Cast": "%s is cast", "Hit": "%s strikes"}[k[1]] % sk["weapon"])); continue
        if k[0] == "Monster" and len(k) == 3 and k[2] in VOICE: HEARD.append((e["t"], "the %s %s" % (k[1].lower(), VOICE[k[2]])))
        elif e["key"] == "Player.Hurt": HEARD.append((e["t"], "she cries out"))
        elif e["key"] == "Player.Death": HEARD.append((e["t"], "she falls"))
        elif e["key"] == "Env.Generate" and any(x["kind"] == "tier_notice" and "ARENA IS WON" in x.get("text", "") and abs(x["t"] - e["t"]) < 0.6 for x in EV): HEARD.append((e["t"], "a rumble: the arena is won"))
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
        # (run5s: a weapon's sounds the lines above do not name (a found blade's): no spell was cast just before it)
        elif S5 and e["key"].startswith("Player.Charge."): HEARD.append((e["t"], "she draws back for a blow"))
        elif S5 and e["key"].startswith("Player.Cast."): HEARD.append((e["t"], "her blade swings"))
        elif S5 and e["key"].startswith("Player.Hit."): HEARD.append((e["t"], "the blade bites"))
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
SLASHL = [e for e in EV if e["kind"] == "slash_lines"]; SLASHES = {s_["name"]: s_ for s_ in C.get("slashes", [])}       # (run5m2)
# (run5m2: the inventory's tabs (ARDHUD::DrawInventory): each tab's sections, its first shown empty or not)
TAB_NAMES = ["WEAPONS", "ARMOUR", "POTIONS / FOOD", "CRAFTING", "MAGIC"]
def slot_lab(q): return str((q + 1) % 10) if q < 10 else str(q + 1)          # (ARDHUD's slot numbers: 1 to 9, 0, then 11, 12...)
def tab_secs(tab):
    who = C.get("title", HERO).upper()
    return [[("weapon", "WEAPONS AND SPELLS", True), ("ability", "ABILITIES  (ON THE QUICK BAR IF YOU PUT THEM THERE)", False), ("carried", "WEAPONS THE %s CANNOT WIELD" % who, False)],
            [("armour", "ARMOUR", True), ("helmet", "HELMET", False), ("shield", "SHIELDS", False), ("torch", "TORCH", False)],
            [("item", "POTIONS AND FOOD", True)],
            [("component", "MATERIALS", True), ("repair", "REPAIR ITEMS", False)],
            [("slash", "SLASHES", True), ("ring", "RINGS", False), ("key", "KEYS", False), ("teleport", "TELEPORT RINGS", False), ("tome", "TOMES THE %s CANNOT LEARN" % who, False)]][max(0, min(4, tab))]
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
    fl_fps = lfont("AlegreyaSC-700", 24)          # (mistward's frame rate: the HUD's label at 1.5 since 2026-10-27)
    f_par = lfont("Alegreya-500", 21)            # (run5m2: the inventory's paragraphs a size smaller, nearer the game's: more lines to fit)
else:
    fl_small, fl_tiny, ft_small, ft_tiny = f_small, f_tiny, f_small, f_tiny
    fl_fps = f_small
    f_par = font("segoeui.ttf", 21)
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
                for Y in range(q[1], q[3]):
                    if has_tile(q, X, Y): tiles[(X, Y)] = tiles.get((X, Y), 0) | fl
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
        elif kind >= 7: mist_mark(d, x, y, kind, 6.0 * K, ua)
    if M5:
        # (mistward: a boss or a guarded ring beyond the rim sits on it, the way to it)
        for wx, wy, kind in pois_at(int(round(t * FPS))):
            x, y = ToS(wx, wy)
            if kind in (7, 8) and not inside(x, y):
                dd = math.hypot(x - cx, y - cy); mist_mark(d, cx + (x - cx) / dd * R * 0.86, cy + (y - cy) / dd * R * 0.86, kind, 6.0 * K, ua)
    if K5:
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
        ta = r.get("tally")
        if ta and opn < mx:
            # (mistward: the share rule, as ARDHUD::DrawTiers writes it: each count against what the next tier needs)
            pct = round(ta[0] * 100)
            if len(ta) == 3:
                need = [math.ceil(a_ * ta[0] - 1e-3) for a_ in ta[2]]
                ls.append(("tier %d opens at %d%% of tier %d" % (opn + 1, pct, opn), (0.7, 0.72, 0.75)))
                ls.append(("rooms %d/%d   monsters %d/%d   chests %d/%d" % (ta[1][0], need[0], ta[1][1], need[1], ta[1][2], need[2]), (0.86, 0.84, 0.78)))
            else: ls.append(("tier %d opens at %d%% of tier %d (counting...)" % (opn + 1, pct, opn), (0.7, 0.72, 0.75)))
        else:
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
                for Y in range(q[1], q[3]):
                    if has_tile(q, X, Y): tiles[(X, Y)] = tiles.get((X, Y), 0) | fl
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
            tl = sc("TIER %d" % tier_of(c)) if K5 else None            # (level 5: a line under the name with the room's tier, a little smaller)
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
        elif kind == 5 and K5:
            s_ = 7.0 * K; rr = s_ * 1.7; d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(0, 0, 0, int(140 * ua)))
            for a0, b0 in (((x - s_, y - s_), (x + s_, y + s_)), ((x - s_, y + s_), (x + s_, y - s_))): d.line((a0, b0), fill=lin((1.0, 0.22, 0.16), ua), width=max(2, int(s_ * 0.38)))
        elif kind == 6 and K5 and tiles.get((int(math.floor(wx / TS)), int(math.floor(wy / TS))), 0) & 2: d = anvil_mark(lay, d, x, y, 13.0 * K, ua)
        elif kind >= 7: mist_mark(d, x, y, kind, 8.0 * K, ua)
    if M5:
        for wx, wy, kind in pois_at(int(round(t * FPS))):
            x, y = ToS(wx, wy)
            if kind in (7, 8) and not ok(x, y):
                dd = math.hypot((x - cx) / hx, (y - cy) / hy); mist_mark(d, cx + (x - cx) * 0.7 / dd, cy + (y - cy) * 0.7 / dd, kind, 8.0 * K, ua)
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
    title = (C.get("game_title") or "DUNGEON MAP").upper() if M5 else "DUNGEON MAP"; tw = d.textlength(title, font=f_head); ph = 58 * K
    t0, t1 = (cx - tw / 2 - 90 * K, A_[1] + 6 * K), (cx + tw / 2 + 90 * K, A_[1] + 6 * K + ph)
    if UI.has("banner"): UI.nine(o, "banner", t0, t1, UI.height_px("banner", ph), (1, 1, 1, ua)); d = ImageDraw.Draw(o, "RGBA")
    d.text((cx + 2 * K, (t0[1] + t1[1]) / 2 + 2 * K), title, font=f_head, fill=(0, 0, 0, int(200 * ua)), anchor="mm"); d.text((cx, (t0[1] + t1[1]) / 2), title, font=f_head, fill=gold, anchor="mm")
    cz = 118 * K
    if UI.fit(o, "compass", (B_[0] - 40 * K - cz, A_[1] + 46 * K), (B_[0] - 40 * K, A_[1] + 46 * K + cz), (1, 1, 1, ua)):
        d = ImageDraw.Draw(o, "RGBA"); d.text((B_[0] - 40 * K - cz / 2, A_[1] + 45 * K), "N", font=ft_small, fill=gold, anchor="md")
    x, y = A_[0] + 44 * K, B_[1] - (166 + (23 + 23 if K5 else 0) + (23 * len(MW_KEY) if M5 else 0)) * K       # (level 5: the sealed passages and the anvils, a line each; mistward: its marks)
    d.text((x - 6 * K, y - 30 * K), sc("KEY"), font=fl_small, fill=gold)
    if UI.fit(o, "divider", (x - 14 * K, y - 14 * K), (x + 200 * K, y + 2 * K), (1, 1, 1, ua)): d = ImageDraw.Draw(o, "RGBA")
    for kind, what in ((0, "monster"), (1, "elite"), (2, "unlooted chest or trunk"), (3, "unexplored passage"), (4, "door")) + (((5, "sealed passage"), (6, "anvil: make repair items")) if K5 else ()) + (MW_KEY if M5 else ()):
        mx, my = x + 6 * K, y + 10 * K
        if kind == 0: soft(mx, my, 5.5 * K, TAC["red"], 1.0)
        elif kind == 1: tri(mx, my, 7.5 * K, TAC["elite"])
        elif kind == 2: star(mx, my, 7.5 * K, TAC["gold"])
        elif kind == 3: diamond(mx, my, 6.5 * K, TAC["exit"])
        elif kind == 5:
            s_ = 6.0 * K; d.ellipse((mx - s_ * 1.7, my - s_ * 1.7, mx + s_ * 1.7, my + s_ * 1.7), fill=(0, 0, 0, int(140 * ua)))
            for a0, b0 in (((mx - s_, my - s_), (mx + s_, my + s_)), ((mx - s_, my + s_), (mx + s_, my - s_))): d.line((a0, b0), fill=lin((1.0, 0.22, 0.16), ua), width=max(2, int(s_ * 0.38)))
        elif kind == 6: d = anvil_mark(o, d, mx, my, 9.0 * K, ua)
        elif kind >= 7: mist_mark(d, mx, my, kind, 6.0 * K, ua)
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
    if it["kind"] == "ring":
        k_ = it.get("ring_kind", "magic"); s = "+%d%% %s while you wear it (%s; one ring of each kind at a time, rings of a kind do not add up)." % (round(it["amount"] * 100),
             {"magic": "mana", "health": "hit points", "dexterity": "ranged weapons' damage"}.get(k_, k_), {"magic": "spellcasters", "health": "the Warrior and the Warlock", "dexterity": "the Rogue"}.get(k_, ""))
        if C.get("ring_kinds") and k_ not in C.get("ring_kinds", []): s += "  The %s cannot wear it." % title          # (a record without her ring kinds (run5m2) says nothing)
        return s
    if it["kind"] == "tome":
        sp = SPELLS.get(it.get("spell", ""))
        if not sp: return "A spell tome"
        s = "Teaches %s (%s): %s.  %d mana" % (sp["name"], {"summon": "summoning"}.get(sp["type"], sp["type"]), sp["effect"], sp["mana"]) + (", cooldown %d s" % sp["cooldown"] if sp["cooldown"] > 0 else "") + "."
        if sp["type"] not in C.get("learns", []): s += "  The %s cannot learn it." % title
        return s
    if it["kind"] == "shield":
        return "A shield: damage reduction %d / 10, each blow takes %d%% less; speed %d / 10, you move %d%% slower.  Durability %d: it loses what it takes; at 0 it breaks.  On your arm with a one-handed weapon." % (
            it.get("dr", 0), round(it.get("amount", 0) * 100), it.get("sr", 0), round(it.get("slower", 0) * 100), it.get("durability", 0))
    if it["kind"] == "torch": return "A torch for your left hand: its flame lights your way.  Made at an anvil."
    if it["kind"] == "teleport": return "A teleporter's ring: used, it carries you to the great hall's teleporter, and that one back to its tier."
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
    slp = r.get("slp", [0, 0, ""]) if MW2 else [0, 0, ""]; slpick = not picking and bool(slp[0]); tabs = MW2 and not picking and not slpick
    if slpick:
        le = last_at(SLASHL, t); lines = le["lines"] if le else []; cur = slp[1]
        secs = [("weapon", "PUT THE %s ON" % slp[2].upper(), True)]
    elif picking:
        le = last_at(REPL, t); lines = le["lines"] if le else []; cur = rep[1]
        rit = ITEMS.get(rep[2], {})
        secs = [("armour", "MEND WITH THE %s  (+%d%%)" % (rep[2].upper(), round(rit.get("amount", 0) * 100)), False), ("weapon", "WEAPONS YOU FOUND", False)]
    else:
        le = last_at(LINES, t); lines = le["lines"] if le else []; cur = inv[1]
        secs = [("weapon", "WEAPONS AND SPELLS", True), ("item", "POTIONS AND FOOD", True), ("repair", "REPAIR ITEMS", False), ("armour", "ARMOUR", False),
                ("component", "MATERIALS", False), ("carried", "WEAPONS THE %s CANNOT WIELD" % C.get("title", HERO).upper(), False)]
        if S5: secs[4:4] = [("ring", "RINGS", False), ("tome", "TOMES THE %s CANNOT LEARN" % C.get("title", HERO).upper(), False)]
        if M5: secs[4:4] = [("shield", "SHIELDS", False), ("torch", "TORCH", False), ("teleport", "TELEPORT RINGS", False), ("ring", "RINGS", False), ("tome", "TOMES THE %s CANNOT LEARN" % C.get("title", HERO).upper(), False)]
        if tabs: secs = tab_secs(r.get("tab", 0))
    sec_of = []; count = [0] * len(secs)
    for x in lines:
        k_ = next((j for j, sv in enumerate(secs) if x.startswith(sv[0] + "|")), 0); sec_of.append(k_); count[k_] += 1
    # (a layer of its own, put over the rest: drawing on the HUD's layer replaces what is there instead of blending)
    top = o; o = Image.new("RGBA", top.size, (0, 0, 3, int(140 * ua))); d = ImageDraw.Draw(o, "RGBA")
    rh, pw, pd, head_h = 34 * K, 1000 * K, 22 * K, 58 * K
    empty = rh if (len(secs) > 1 and secs[1][2] and count[1] == 0) else 0
    if MW2: empty = sum(rh for j, sv in enumerate(secs) if sv[2] and count[j] == 0)
    tabh = 46 * K if tabs else 0                # (run5m2: the tab strip takes room)
    def heads(f0, f1):
        n_ = 0
        for j, sv in enumerate(secs):
            shown_ = sv[2] and count[j] == 0
            if not shown_: shown_ = any(sec_of[i] == j for i in range(f0, min(f1, len(lines))))
            n_ += 1 if shown_ else 0
        return n_
    room = H * K - 80 * K - 150 * K - 30 * K - tabh
    fit, first = len(lines), 0
    for _ in range(3):
        nh = heads(first, first + fit)
        if head_h * nh + empty + rh * len(lines) <= room: fit, first = len(lines), 0; break
        fit = max(4, min(len(lines), int((room - head_h * nh - empty) // rh))); first = max(0, min(cur - fit // 2, len(lines) - fit))
    shown = lambda i: first <= i < first + fit
    lh = 46 * K + head_h * heads(first, first + fit) + rh * fit + (30 * K if fit < len(lines) else 0) + empty + tabh
    ph = max(lh, (400 if (UI and UI.has("slot")) else 330) * K) + 150 * K
    ax, ay = (W * K - pw) / 2, max(40 * K, (H * K - ph) / 2); bx, by = ax + pw, ay + ph
    if UI and UI.has("panel_wide"): UI.board(o, "panel_wide", (ax, ay), (bx, by), 44 * K); d = ImageDraw.Draw(o, "RGBA")
    else: d.rectangle((ax, ay, bx, by), fill=lin((0.035, 0.04, 0.055), 0.94), outline=lin((0.75, 0.65, 0.45), 0.9), width=2 * K)
    divider = bool(UI and UI.has("divider")); plate = bool(UI and UI.has("button"))
    tin = 24 * K if (UI and UI.has("panel_wide")) else 0           # (the title row clear of the board's corner ornaments)
    d.text((ax + pd + tin, ay + 16 * K), "REPAIR" if picking else "SLASH" if slpick else "INVENTORY", font=f_title, fill=lin(INK)); d.text((bx - pd - tin, ay + 18 * K), C["title"], font=ft_small, fill=lin(gold), anchor="ra")
    d.text((bx - pd - tin, ay + 46 * K), "in play the game pauses while it is open", font=f_tiny, fill=lin((0.70, 0.68, 0.62)), anchor="ra")
    if tabs:
        # (the tab strip: five tabs, the one shown lit; each with how many lines it holds)
        tn = r.get("tabn") or [0, 0, 0, 0, 0]; tx0, ty, tw0, th0 = ax + pd + tin, ay + 64 * K, (pw - 2 * (pd + tin)) / 5.0, 34 * K
        for k_ in range(5):
            t0_, t1_ = (tx0 + k_ * tw0 + 3 * K, ty), (tx0 + (k_ + 1) * tw0 - 3 * K, ty + th0); on_ = k_ == r.get("tab", 0)
            if on_ and UI and UI.has("button"): UI.nine(o, "button", t0_, t1_, UI.height_px("button", th0), (1.25, 1.05, 0.7, 1)); d = ImageDraw.Draw(o, "RGBA")
            else: d.rectangle((*t0_, *t1_), fill=lin((0.36, 0.27, 0.10), 0.95) if on_ else lin((0.08, 0.07, 0.06), 0.85))
            d.rectangle((*t0_, *t1_), outline=lin(gold) if on_ else lin((0.55, 0.48, 0.34), 0.8), width=(2 if on_ else 1) * K)
            text_c(d, ((t0_[0] + t1_[0]) / 2, (t0_[1] + t1_[1]) / 2), sc("%s  %d" % (TAB_NAMES[k_], tn[k_])), fl_tiny, (255, 255, 255, 255) if on_ else lin((0.70, 0.68, 0.62)), "mm", False)
    lx, lw = ax + pd, pw * 0.5 - pd; y = ay + 76 * K + tabh
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
        if slpick:
            if len(p_) < 3: continue
            has = len(p_) >= 4 and p_[3] != ""
            rowl(i, p_[2], ("HAS %s" % p_[3].upper()) if has else "NO SLASH", CYAN if has else (0.70, 0.68, 0.62), wicon(p_[2]))
            continue
        if picking:
            arm = p_[0] == "armour"
            if len(p_) < (5 if arm else 6): continue
            nm = p_[1] if arm else p_[2]; left, full, after = (float(p_[2]), float(p_[3]), float(p_[4])) if arm else (float(p_[3]), float(p_[4]), float(p_[5]))
            tag = ("%d / %d  WHOLE" % (left, full)) if left >= full else ("%d  TO  %d / %d" % (left, after, full))
            rowl(i, nm, tag, (0.70, 0.68, 0.62) if left >= full else gold, iicon(nm) if arm else wicon(nm))
            continue
        if p_[0] == "weapon":
            wi = int(p_[4]) if (MW2 and len(p_) >= 5) else i          # (run5m2: the line names its weapon's index)
            wd = WL[wi] if wi < len(WL) else {"name": p_[1]}
            tag = "ALWAYS AT HAND" if wd.get("alongside") else ("IN YOUR HANDS" if wi == r["w"] else "")
            if wd.get("durability", 0) > 0: tag = (tag + "   " if tag else "") + "%d / %d" % (wd["wear"], wd["durability"])
            nm_ = wd["name"]
            if MW2:
                if len(p_) >= 6 and int(p_[5]) > 1: tag += "   x %s" % p_[5]
                qs_ = r.get("qs", [])
                if not wd.get("alongside"): tag += ("   [%s]" % slot_lab(qs_.index(nm_))) if nm_ in qs_ else "   OFF THE BAR"
                if wd.get("slash"): nm_ = "%s  +  %s" % (nm_, wd["slash"])
            rowl(i, nm_, tag.strip(), CYAN if wd.get("alongside") else gold, wd["icon"] if (UI and wd.get("icon") and UI.has(wd["icon"])) else wicon(wd["name"]))
        elif p_[0] == "ability" and len(p_) >= 3:
            q_ = int(p_[2]); rowl(i, p_[1], ("[%s]" % slot_lab(q_)) if q_ >= 0 else "OFF THE BAR", gold if q_ >= 0 else (0.70, 0.68, 0.62), "ability_" + p_[1].lower())
        elif p_[0] == "helmet" and len(p_) >= 2:
            rowl(i, ("Helmet of the %s" % p_[2]) if len(p_) >= 3 else "Helmet", "HIDDEN" if p_[1] == "1" else "SHOWN", (0.70, 0.68, 0.62) if p_[1] == "1" else CYAN)
        elif p_[0] in ("slash", "key") and len(p_) >= 3:
            rowl(i, p_[1], "x %s" % p_[2], CYAN if p_[0] == "slash" else gold, iicon(p_[1]))
        elif p_[0] == "armour":
            left, full = (float(p_[3]), float(p_[4])) if len(p_) >= 5 else (0.0, 0.0)
            tag = "WORN" if p_[2] == "1" else ""
            if full > 0: tag = (tag + "   " if tag else "") + ("WORN OUT" if left <= 0 else "%d / %d" % (left, full))
            rowl(i, p_[1], tag, (1.0, 0.45, 0.35) if (full > 0 and left <= 0) else CYAN, iicon(p_[1]))
        elif p_[0] == "shield" and len(p_) >= 6:
            tag = ("IN HAND" if p_[2] == "1" else "") + ("   x %s" % p_[5] if p_[5] != "1" else "") + "   %d / %d" % (float(p_[3]), float(p_[4]))
            rowl(i, p_[1], tag.strip(), CYAN, iicon(p_[1]))
        elif p_[0] == "torch" and len(p_) >= 4: rowl(i, p_[1], "LIT" if p_[2] == "1" else ("x %s" % p_[3] if p_[3] != "1" else ""), (1.0, 0.7, 0.35), iicon(p_[1]))
        elif p_[0] == "teleport" and len(p_) >= 3: rowl(i, p_[1], "TIER %s" % p_[2], (0.5, 0.8, 1.0), iicon(p_[1]))
        elif p_[0] == "ring" and len(p_) >= 4:
            rowl(i, p_[1], "WORN" if p_[2] == "1" else ("x %s" % p_[3] if p_[3] != "1" else ""), CYAN, iicon(p_[1]))
        else: rowl(i, p_[1], "x %s" % p_[2], (0.70, 0.68, 0.62) if p_[0] in ("carried", "component", "tome") else gold, iicon(p_[1]))
    if not lines or last[0] < len(secs) - 1: open_sec(len(secs) - 1)
    if fit < len(lines):
        d.text((lx + 12 * K, y + 6 * K), "%d more above,  %d more below" % (first, len(lines) - first - fit), font=f_tiny, fill=lin((0.70, 0.68, 0.62))); y += 30 * K
    rx, rw = ax + pw * 0.5 + pd, pw * 0.5 - pd * 2; ry = ay + 76 * K + tabh
    d.rectangle((rx - pd / 2, ry, rx - pd / 2 + K, by - 110 * K), fill=lin((0.75, 0.65, 0.45), 0.4))
    def para(s_, c, f_):
        nonlocal ry
        if MW2 and f_ is f_line: f_ = f_par
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
    if 0 <= cur < len(lines) and slpick:
        p_ = lines[cur].split("|")
        if len(p_) >= 3:
            picture(wicon(p_[2]), p_[2]); sd_ = SLASHES.get(slp[2], {})
            if sd_: para("The %s:  +%d %s on every hit;  %s" % (sd_["name"], round(sd_["bonus"]), sd_["type"].lower(), sd_["text"]), lin(INK), f_line)
            if len(p_) >= 4 and p_[3]: para("The %s on it now goes back into your pack" % p_[3].lower(), lin((0.70, 0.68, 0.62)), f_line)
            ry += 6 * K; para("Enter  put it on      Backspace  back", lin(gold), f_line)
    elif 0 <= cur < len(lines):
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
            _wd = (WL[int(p_[4])] if (MW2 and len(p_) >= 5 and int(p_[4]) < len(WL)) else {}) if p_[0] == "weapon" else {}
            picture((_wd["icon"] if (UI and _wd.get("icon") and UI.has(_wd["icon"])) else wicon(p_[1])) if p_[0] == "weapon" else (None if p_[0] == "helmet" else ("ability_" + p_[1].lower()) if p_[0] == "ability" else iicon(p_[1])), "Helmet" if p_[0] == "helmet" else p_[1])
            if p_[0] == "ability":
                para("A dash at the monster ahead (up to 5 m, stopping short of it) and a strike with what you hold" if p_[1] == "Dash" else "A dodge: a roll out of the way; blows miss you while you roll", lin(INK), f_line)
                para("V or the right mouse button makes it anywhere" if p_[1] == "Dash" else "B makes it anywhere", lin((0.70, 0.68, 0.62)), f_line)
                q_ = int(p_[2]) if len(p_) >= 3 else -1; asl = slot_lab(r.get("asl", 0)); ry += 6 * K
                para(("In quick slot %s: its number makes it; on the D-pad it is made ready and the attack button makes it" % slot_lab(q_)) if q_ >= 0 else "Off the quick bar", lin(gold), f_line)
                para(("1-0 (Y: slot %s, D-pad left / right) moves it, its own slot takes it off the bar" % asl) if q_ >= 0 else ("1-0 puts it on the bar (Y: slot %s, D-pad left / right)" % asl), lin((0.70, 0.68, 0.62)), f_line)
            elif p_[0] == "helmet":
                para("The worn set's helmet: shown or hidden (its share of the blows stays the same)", lin(INK), f_line)
                ry += 6 * K; para("Enter  %s it      H  the same anywhere" % ("show" if p_[1] == "1" else "hide"), lin(gold), f_line)
            elif p_[0] == "weapon":
                wcur = int(p_[4]) if (MW2 and len(p_) >= 5) else cur
                wd = WL[wcur] if wcur < len(WL) else C["weapons"][min(wcur, len(C["weapons"]) - 1)]
                spd = C.get("spells", [])[wd["spell_index"]] if (S5 and 0 <= wd.get("spell_index", -1) < len(C.get("spells", []))) else None
                if spd:
                    para("%s spell:  %s" % ({"offense": "Offense", "protection": "Protection", "curse": "Curse", "summon": "Summoning"}.get(spd["type"], spd["type"]), spd["effect"]), lin(INK), f_line)
                    num = "  ·  ".join(x for x in (("cooldown %d s" % spd["cooldown"]) if spd["cooldown"] > 0 else "", ("lasts %d s" % spd["duration"]) if spd["duration"] > 0 else "") if x)
                    if num: para(num, lin((0.70, 0.68, 0.62)), f_line)
                else: para("A spell: a bolt flies after the monster you face" if wd.get("spell") and not wd.get("ranged") else "A ranged weapon: its bolts fly straight at the monster you face" if wd.get("ranged") else "A melee weapon", lin((0.70, 0.68, 0.62)), f_line)
                if wd.get("speed", 0) > 0:
                    para("%s  ·  speed %d / 10  ·  damage %d / 10" % (wd["type"][:1].upper() + wd["type"][1:], wd["speed"], wd["rating"]), lin(INK), f_line)
                    if wd.get("durability", 0) <= 0: para("Yours for good: it never breaks, and it stays with you when you fall", lin((0.75, 0.85, 0.7)), f_line)
                    else: para("Durability %d / %d: a hit takes 1 off, at 0 it breaks; a repair item mends it" % (wd["wear"], wd["durability"]), lin((0.75, 0.85, 0.7)), f_line)
                para("%s damage" % (("%.1f" % wd["damage"]).rstrip("0").rstrip(".")), lin(INK), f_line)
                if wd.get("mana"): para("%d mana a cast" % wd["mana"], lin((0.55, 0.7, 1.0)), f_line)
                ry += 6 * K; para("Cast with RMB or E (LB) while your weapon stays drawn" if wd.get("alongside") else "In your hands" if wcur == r["w"] else "Enter  wield it", lin(gold), f_line)
                if MW2 and wd.get("slash"):
                    sd_ = SLASHES.get(wd["slash"], {})
                    para("%s:  +%d %s on every hit;  %s   (T takes it off)" % (wd["slash"], round(sd_.get("bonus", 0)), sd_.get("type", "").lower(), sd_.get("text", "")), lin(CYAN), f_line)
                if MW2 and not wd.get("alongside"):
                    qs_ = r.get("qs", []); asl = slot_lab(r.get("asl", 0))
                    para(("In quick slot %s  ·  1-0 (Y: slot %s, D-pad left / right) moves it, its own slot takes it off the bar" % (slot_lab(qs_.index(wd["name"])), asl)) if wd["name"] in qs_ else "Off the quick bar  ·  1-0 puts it on (Y: slot %s)" % asl, lin((0.70, 0.68, 0.62)), f_line)
            else:
                it = ITEMS.get(p_[1])
                if it: para(describe(it, r), lin(INK), f_line)
                ry += 6 * K
                if p_[0] == "item": para("Enter  use it", lin(gold), f_line)
                elif p_[0] == "repair": para("Enter  choose what it mends", lin(gold), f_line)
                elif p_[0] in ("armour", "ring", "shield"): para("Enter  take it off" if len(p_) > 2 and p_[2] == "1" else "Enter  put it on", lin(gold), f_line)
                elif p_[0] == "torch": para("Enter  put it out" if p_[2] == "1" else "Enter  light it", lin(gold), f_line)
                elif p_[0] == "teleport": para("Enter  to the great hall's teleporter", lin(gold), f_line)
                elif p_[0] == "slash": para("Enter  choose the weapon it goes on", lin(gold), f_line)
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
    # (mistward: the pointer too, as ARDHUD writes it with the generator's bMouseUI)
    if tabs or slpick:
        d.text((ax + pd + tin, fy + 52 * K), ("Q E or click  tabs      1-0 or right click  quick slot      T  take its slash off      Enter or click  use      wheel  scroll      I or Tab  close" if tabs else
                                              "W S / pointer  select      Enter or click  put it on      Backspace  back      Tab  close"), font=f_small, fill=lin((0.70, 0.68, 0.62)))
        top.alpha_composite(o); return
    d.text((ax + pd + tin, fy + 52 * K), (("W S / pointer  select     Enter or click  mend it     wheel  scroll     Backspace  back     Tab  close" if picking else
                                           "W S / pointer  select      Enter or click  wield or use      wheel  scroll      I or Tab  close") if M5 else
                                          ("W S / arrows / wheel  select      Enter or E  mend it      Backspace  back      I or Tab  close" if picking else
                                           "W S / arrows / wheel  select      Enter or E  wield or use      I or Tab  close")), font=f_small, fill=lin((0.70, 0.68, 0.62)))
    top.alpha_composite(o)
def craft_panel(top, r, t, ua, me):
    """ARDHUD::DrawCrafting: the anvil's panel; the recipes on the left (CAN MAKE where she has everything), the chosen one on
    the right: its picture, what it mends, each part with what she carries of it against what it takes"""
    gold, dim, have_c, lack_c = (1.0, 0.82, 0.35), (0.70, 0.68, 0.62), (0.55, 0.95, 0.55), (1.0, 0.5, 0.4)
    le = last_at(CRAFTL, t); lines = le["lines"] if le else []; cur = r["craft"][1]
    o = Image.new("RGBA", top.size, (0, 0, 3, int(140 * ua))); d = ImageDraw.Draw(o, "RGBA")
    rh, pw, pd, ph = 40 * K, 1000 * K, 22 * K, (700 if S5 else 640) * K
    ax, ay = (W * K - pw) / 2, max(40 * K, (H * K - ph) / 2); bx, by = ax + pw, ay + ph
    if UI and UI.has("panel_wide"): UI.board(o, "panel_wide", (ax, ay), (bx, by), 44 * K); d = ImageDraw.Draw(o, "RGBA")
    else: d.rectangle((ax, ay, bx, by), fill=lin((0.035, 0.04, 0.055), 0.94), outline=lin((0.75, 0.65, 0.45), 0.9), width=2 * K)
    divider = bool(UI and UI.has("divider")); plate = bool(UI and UI.has("button")); tin = 24 * K if (UI and UI.has("panel_wide")) else 0
    d.text((ax + pd + tin, ay + 16 * K), "THE ANVIL", font=f_title, fill=lin(INK))
    d.text((bx - pd - tin, ay + 22 * K), "make repair items  ·  break down the weapons you found" if S5 else "make repair items from your materials", font=f_line, fill=lin(gold), anchor="ra")
    d.text((bx - pd - tin, ay + 56 * K), "in play the game pauses while it is open", font=f_tiny, fill=lin(dim), anchor="ra")
    lx, lw = ax + pd, pw * 0.42 - pd; y = ay + 80 * K
    d.text((lx, y), sc("RECIPES"), font=fl_small, fill=lin(dim)); y += 26 * K
    if divider: UI.fit(o, "divider", (lx - 8 * K, y - 18 * K), (lx + lw + 8 * K, y + 12 * K)); d = ImageDraw.Draw(o, "RGBA")
    y += 4 * K
    parsed = [x.split("|") for x in lines]
    fit = max(4, int((ph - 80 * K - 30 * K - 40 * K - 120 * K) // rh)); first = max(0, min(cur - fit // 2, len(lines) - fit)) if len(lines) > fit else 0
    brk_head = False
    for i, p_ in enumerate(parsed):
        if len(p_) < 3 or not first <= i < first + fit: continue
        if p_[0] == "breakdown":
            # (level 5: the weapons she found, to break down, under the recipes: ARDHUD::DrawCrafting)
            if not brk_head:
                brk_head = True; y += 8 * K
                d.text((lx, y), sc("BREAK DOWN"), font=fl_small, fill=lin(dim)); y += 26 * K
                if divider: UI.fit(o, "divider", (lx - 8 * K, y - 18 * K), (lx + lw + 8 * K, y + 12 * K)); d = ImageDraw.Draw(o, "RGBA")
                y += 4 * K
            on, drawn = i == cur, len(p_) > 3 and p_[3] == "1"
            if on:
                if plate:
                    UI.nine(o, "button", (lx - 4 * K, y - 4 * K), (lx + lw + 4 * K, y + rh), UI.height_px("button", rh + 4 * K), (1.25, 1.05, 0.7, 1)); d = ImageDraw.Draw(o, "RGBA")
                    d.rectangle((lx, y, lx + lw, y + rh - 4 * K), outline=lin(gold), width=2 * K)
                else: d.rectangle((lx, y, lx + lw, y + rh - 4 * K), fill=lin((0.36, 0.27, 0.10), 0.95), outline=lin(gold), width=2 * K)
            ix = 0; ic = wicon(p_[1]) if p_[2].startswith("w") else iicon(p_[1])
            if ic and UI.has(ic): ix = rh; UI.fit(o, ic, (lx + 8 * K, y - 2 * K), (lx + 4 * K + rh, y + rh - 2 * K)); d = ImageDraw.Draw(o, "RGBA")
            d.text((lx + 12 * K + ix, y + 8 * K), p_[1], font=f_line, fill=(255, 255, 255, 255) if on else lin((0.86, 0.84, 0.78)))
            d.text((lx + lw - 12 * K, y + 11 * K), sc("IN YOUR HANDS" if drawn else "BREAK DOWN"), font=fl_tiny, fill=lin(dim if drawn else gold), anchor="ra")
            y += rh; continue
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
    if len(lines) > fit: d.text((lx + 12 * K, y + 6 * K), "%d more above,  %d more below" % (first, len(lines) - first - fit), font=f_tiny, fill=lin(dim))
    if 0 <= cur < len(parsed) and len(parsed[cur]) >= 5 and parsed[cur][0] == "breakdown":
        # (a weapon to break down: what it gives, against what she carries)
        p_ = parsed[cur]; ic = wicon(p_[1]) if p_[2].startswith("w") else iicon(p_[1])
        if ic and UI.has(ic):
            sz = 104 * K
            UI.fit(o, "slot", (rx, ry), (rx + sz, ry + sz)); UI.fit(o, ic, (rx + 16 * K, ry + 14 * K), (rx + sz - 16 * K, ry + sz - 14 * K)); d = ImageDraw.Draw(o, "RGBA")
            d.text((rx + sz + 16 * K, ry + sz / 2), p_[1].upper(), font=f_head, fill=(255, 255, 255, 255), anchor="lm"); ry += sz + 12 * K
        else: d.text((rx, ry), p_[1].upper(), font=f_head, fill=(255, 255, 255, 255)); ry += 46 * K
        d.text((rx, ry), sc("IT BREAKS DOWN INTO"), font=fl_tiny, fill=lin(dim)); ry += 24 * K
        have = {x.split("|")[1]: int(x.split("|")[2]) for x in (last_at(LINES, t) or {"lines": []})["lines"] if x.startswith("component|")}
        for g_ in p_[4].split(";"):
            if ":" not in g_: continue
            nm_, ct_ = g_.split(":", 1)
            d.text((rx, ry), "%s  x %s" % (nm_, ct_), font=f_small, fill=lin((0.86, 0.84, 0.78)))
            d.text((rx + rw - 16 * K, ry + K), "you have %d" % have.get(nm_, 0), font=f_tiny, fill=lin(dim), anchor="ra"); ry += 27 * K
        ry += 12 * K
        d.text((rx, ry), "It is in your hands: draw another weapon first" if p_[3] == "1" else "Enter  break it down (it is gone)", font=f_small, fill=lin(dim if p_[3] == "1" else gold))
    elif 0 <= cur < len(parsed) and len(parsed[cur]) >= 3:
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
    d.text((ax + pd + tin, fy + 52 * K), "W S / arrows / wheel  select      Enter or E  make it" + (" / break it down" if S5 else "") + "      F, Backspace or Tab  close", font=f_small, fill=lin(dim))
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
    out.append((0.8, t_map - 0.1, "THE " + HNAME.upper(), ["  ·  ".join(hj.get("abilities", [])), "%s  ·  %d hit points" % (wear_txt, hj.get("health", 0))], acc))
    if maps_:
        out.append((maps_[0]["t"], close(maps_[0]), "M  ·  THE BIG MAP:  TIERS AND ANVILS", ["each room she has found is written with its tier: this set is tier 1, the 8 round it tier 2, then 16, 24, 32",
                    "the small anvil: one in every forge, at least one in every set of rooms (here, in the great hall): F there makes repair items"], gold))
    tc0 = next((e["t"] for e in EV if e["kind"] == "to_chest"), None); tc1 = CHESTS[0]["t"] if CHESTS else None
    if tc0 is not None and tc1 is not None:
        out.append((tc0, tc1 - 0.35, "THE FIRES ARE QUIETER", ["the crackle of the torches, braziers and hearths is about 8 dB lower than in the earlier reels",
                    "measured in the game's own output 2.5 m from a torch: -8.7 dB (853's fire step)"], (255, 200, 150)))
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
    if X5:
        # (run5x: her fights, the tiers' part: the card, the sealed grating, the tier opening, tier 3 generated, its map)
        for i, e in enumerate(FIGHTS):
            if CARD and CARD[0] - 0.2 <= e["t"] <= CARD[1]: continue
            end = next((k["t"] for k in KILLS if k["t"] > e["t"]), e["t"] + 6.0) + 1.2
            if i + 1 < len(FIGHTS): end = min(end, FIGHTS[i + 1]["t"] - 0.1)
            tr = max(abs(e["section"][0]), abs(e["section"][1])) + 1
            lm = LAST_M if (LAST_M and abs(LAST_M["t"] - e["t"]) < 0.5) else None
            l2 = ("tier 2's last set: one monster left in it" if lm else "a monster of tier %d: its hit points and blows grow with the tier of its set" % tr)
            l3 = ("when it falls every set of tier 2 is cleared and tier 3 opens" if lm else lured(e) or WHO.get(HERO, ""))
            out.append((e["t"], end, "%s  ·  TIER %d" % (e["monster"].replace("_", " ").upper(), tr), ["%.0f hit points, %.0f damage a blow  ·  she has %.0f" % (e["its_hit_points"], e["its_damage"], C["max_health"]), l2, l3], gold))
        if CARD:
            t_lm = LAST_M["t"] if LAST_M else CARD[1] + 6.0
            out.append((CARD[1] - 0.2, t_lm, "A SEALED GRATING  ·  TIER 2 TO TIER 3", ["the ways out of a tier are barred until all of its sets are cleared:",
                        "every room walked into, every chest and trunk opened, every monster killed  ·  under the minimap: each tier's sets cleared"], (255, 200, 120)))
        if OPENED:
            out.append((OPENED["t"], OPENED["t"] + 4.4, OPENED["text"], ["the last set of tier 2 cleared: the gratings toward tier 3 are gone",
                        "tier 3's 16 sets open tier 4's 24, and those open tier 5, the last: past it stand walls"], (255, 200, 120)))
            g3 = next((e for e in GENS if e["t"] > OPENED["t"]), None)
            if g3: out.append((max(g3["t"], OPENED["t"] + 4.5), max(g3["t"], OPENED["t"] + 4.5) + 4.2, ("" if LETTERS else "▲ ") + "TIER 3 IS GENERATED AS SHE NEARS IT",
                               ["a set of 252 m x 252 m: stronger monsters, and the table's weapons and armour of tier 3 in its chests", "never saved: a new dungeon every time"], lin(CYAN)[:3]))
        for e in [x for x in maps_ if CARD and x["t"] > CARD[1]]:
            out.append((e["t"], close(e), "M  ·  THE BIG MAP IN TIER 3", ["the rooms she has found, each written with its tier", "the sealed ways show as red crosses until their tier opens"], gold))
    return out
def r_arm_at(t):
    """the set she wore at t (the rows' arm)"""
    return row(int(t * FPS)).get("arm", "None")
C5CAPS = None
def mist_mark(d, x, y, kind, s_, ua):
    """ARDHUD::MistMark: 7 a boss (a red ring with a crown), 8 a guarded ring (a gold ring, a red dot), 9 her things (a gold
    sack), 10 a teleporter (a blue ring), 11 a trap she has seen (a red X)"""
    rr = s_ * 1.6; d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(0, 0, 0, int(130 * ua)))
    if kind == 7:
        d.ellipse((x - s_, y - s_, x + s_, y + s_), outline=lin((1.0, 0.2, 0.15), ua), width=max(2, int(s_ * 0.35)))
        pts = [(x - s_ * 0.8, y - s_ * 0.9), (x - s_ * 0.5, y - s_ * 1.6), (x - s_ * 0.15, y - s_ * 1.05), (x, y - s_ * 1.75), (x + s_ * 0.15, y - s_ * 1.05), (x + s_ * 0.5, y - s_ * 1.6), (x + s_ * 0.8, y - s_ * 0.9)]
        d.polygon(pts, fill=lin((1.0, 0.82, 0.3), ua))
    elif kind == 8:
        d.ellipse((x - s_, y - s_, x + s_, y + s_), outline=lin((1.0, 0.84, 0.35), ua), width=max(2, int(s_ * 0.38)))
        q = s_ * 0.38; d.ellipse((x - q, y - q, x + q, y + q), fill=lin((1.0, 0.2, 0.15), ua))
    elif kind == 9:
        d.ellipse((x - s_ * 0.85, y - s_ * 0.55, x + s_ * 0.85, y + s_ * 1.0), fill=lin((0.95, 0.72, 0.25), ua))
        d.polygon([(x - s_ * 0.35, y - s_ * 0.55), (x + s_ * 0.35, y - s_ * 0.55), (x + s_ * 0.2, y - s_ * 1.0), (x - s_ * 0.2, y - s_ * 1.0)], fill=lin((0.8, 0.55, 0.18), ua))
    elif kind == 10:
        d.ellipse((x - s_, y - s_, x + s_, y + s_), outline=lin((0.4, 0.75, 1.0), ua), width=max(2, int(s_ * 0.38)))
        q = s_ * 0.3; d.ellipse((x - q, y - q, x + q, y + q), fill=lin((0.7, 0.9, 1.0), ua))
    elif kind == 11:
        for a0, b0 in (((x - s_, y - s_), (x + s_, y + s_)), ((x - s_, y + s_), (x + s_, y - s_))): d.line((a0, b0), fill=lin((1.0, 0.25, 0.2), ua), width=max(2, int(s_ * 0.4)))
MW_KEY = ((7, "a boss"), (8, "a ring you never found, guarded"), (9, "your dropped things"), (10, "a teleporter"), (11, "a trap you have seen"))
CARDS = [e for e in EV if e["kind"] == "card"]
MW_CARD = 3.0
def has_tile(q, X, Y):
    """(mistward) a shaped room's tile: its mask (row by row) says where it has floor"""
    if len(q) > 6 and q[6]:
        wq = q[2] - q[0]; i = (Y - q[1]) * wq + (X - q[0])
        return 0 <= i < len(q[6]) and q[6][i] != 0
    return True
M5CAPS = None
def m5_caps():
    """(mistward, 815's run5m) the captions of the castle's reel, each from what the record says happened"""
    out = []; gold = (255, 226, 150); warm = (255, 200, 120); cyan = lin(CYAN)[:3]
    hj = HJ.get(HERO, {}); acc = tuple(int(255 * v) for v in hj.get("accent", (1.0, 0.94, 0.84)))
    ev = lambda k: [e for e in EV if e["kind"] == k]
    first = min([e["t"] for e in EV if e["kind"] in ("to_chest", "chest", "inventory", "hold", "craft_open", "card", "disarm", "trap_spot") and e["t"] > 1.0] + [6.0])
    who = {"Warrior": "a shield on her arm now: found, put on and off, broken down at the anvil",
           "Mage": "a torch she makes at the anvil and carries in her left hand",
           "Warlock": "the castle's rooms of other shapes, its teleporters, and what happens when she falls",
           "Rogue": "she sees the castle's traps and disarms them"}[HERO]
    out.append((0.8, first - 0.1, "THE %s IN MISTWARD CASTLE" % HNAME.upper(), ["level 5's dungeon in five themed tiers: the stone dungeon, the castle keep, the dwarven halls, then all three",
                who, "upper left: the frame rate the game shows (in this render its own tick; in play the test measured 36 to 41)"], acc))
    for e in CHESTS:
        fd = next((x for x in FOUND if x["t"] >= e["t"] - 0.05), None); held = fd.get("items", []) if fd else []
        out.append((e["t"] - 0.3, e["t"] + 2.4, "F  ·  A CHEST: IT STAYS OPEN", ["it held %d things: %s" % (len(held), ", ".join(x.lower() for x in held[:4]) + (" ..." if len(held) > 4 else "")),
                    "in the castle an opened container stays open, also when its set of rooms is built again"], gold))
    for e in ev("f_again"):
        out.append((e["t"], e["t"] + 2.2, "F  AGAIN:  NOTHING", ["the open chest is not shut again, and F no longer offers it" + (": it names \"%s\" instead" % e["describe"] if e.get("describe") else ""),
                    "the chest's lid stays up (%d %% open)" % round(100 * e.get("open_alpha", 1.0))], gold))
    for e in INVS:
        u = next((x for x in USED if x["t"] >= e["t"]), None)
        if not u: continue
        cl = inv_closed_after(u["t"]); nxt = next((x["t"] for x in EV if x["t"] > u["t"] + 0.2 and x["kind"] in ("inventory", "quiet", "craft_open", "card", "lure")), cl + 5.0)
        nm = u["entry"].split("|")[1] if "|" in u["entry"] else ""; it = ITEMS.get(nm, {})
        if e.get("why") == "shield":
            out.append((e["t"], cl, "I  ·  ENTER  ·  SHIELDS", ["her inventory has a SHIELDS heading: each shield she carries, several of one kind each with its own durability",
                        "she takes up the %s" % nm.lower()], gold))
            out.append((cl, nxt - 0.05, nm.upper(), ["damage reduction %d / 10: a blow takes %d%% less  ·  speed %d / 10: she moves %d%% slower" % (it.get("dr", 0), round(it.get("amount", 0) * 100), it.get("sr", 0), round(it.get("slower", 0) * 100)),
                        "durability %d: it loses what it takes off her blows and breaks at 0  ·  on her arm with a one-handed weapon only" % it.get("durability", 0)], cyan))
        elif e.get("why") == "torch":
            out.append((e["t"], cl, "I  ·  ENTER  ·  THE TORCH", ["the torch is in her inventory under its own heading", "Enter lights it"], gold))
            out.append((cl, nxt - 0.05, "THE TORCH, LIT", ["in her left hand, its flame and its light going with her",
                        "it takes her left hand: the Warrior's shield is slung while it burns  ·  every hero can carry one"], cyan))
        elif e.get("why") == "teleport":
            tl = next((x for x in ev("teleported") if x["t"] >= u["t"]), None)
            out.append((e["t"], cl, "I  ·  ENTER  ·  TELEPORT RING II", ["the ring she took up from tier 2's teleporter", "used from the inventory"], gold))
            out.append((cl, nxt - 0.05, "TO THE GREAT HALL'S TELEPORTER", ["the ring carries her to the first tier's pad%s" % (" (%.1f m from it)" % tl["m_from_pad1"] if tl else ""),
                        "there F takes her back to any tier whose ring she holds (G picks which)"], cyan))
    co = ev("craft_open")
    for e in co:
        cw = next((x for x in ev("craft_want") if x["t"] >= e["t"]), None); cr = next((x for x in ev("crafted") if x["t"] >= e["t"]), None)
        out.append((e["t"], (cw["t"] + 1.0) if cw else e["t"] + 3.0, "F  ·  THE ANVIL:  ITS LISTS IN ALPHABETICAL ORDER", ["the recipes A to Z, then what she can break down, A to Z: " +
                    ", ".join(x.split("|")[1].lower() for x in (cw["lines"] if cw else [])[:7]) + " ...",
                    "in play the panel pauses the game; for the reel the world goes on and the monsters leave her be"], gold))
        if cr:
            out.append((cr["t"] - 1.2, cr["t"] + 2.6, "ENTER  ·  " + ("BREAK DOWN THE " + cr["item"].upper() if cr["line_kind"] == "breakdown" else cr["item"].upper() + " MADE"),
                        [cr["message"], ("a shield breaks down as weapons do: by what it is made of (metal or wood) and its tier" if cr["line_kind"] == "breakdown" else
                                         "2 wood (any kind), 2 straw rope, 1 oils, used up")], cyan))
    for e in [x for x in EV if x["kind"] == "given"]:
        out.append((e["t"], e["t"] + 2.4, "THE REEL GIVES HER %s" % ("THE TORCH'S MATERIALS AND A BAG OF OTHERS" if e.get("why") == "torch" else "A SHIELD" if e.get("why") == "shield" else "THINGS"),
                    [", ".join("%d %s" % (n_, k_.lower()) for k_, n_ in list(e["items"].items())[:8]) + (" ..." if len(e["items"]) > 8 else ""), "in play they come from the containers"], warm))
    for e in ev("hold"):
        h1 = next((x for x in ev("held") if x["t"] >= e["t"] and x.get("key") == e["key"]), None)
        out.append((e["t"], (h1["t"] + 1.4) if h1 else e["t"] + 2.5, "HOLDING %s:  THE LIST WALKS" % e["key"].upper(), ["a key held moves the cursor on by itself: after a third of a second, then a line every 0.08 s",
                    ("%d lines in %.1f s" % (h1["lines"], h1["seconds"])) if h1 else ""], gold))
    blocks = [e for e in EV if e["kind"] == "mw_shield_block"]
    if blocks:
        f0 = next((f for f in FIGHTS if f["t"] <= blocks[0]["t"]), None)
        b_ = blocks[:3]
        out.append((blocks[0]["t"] - 0.1, blocks[-1]["t"] + 2.4, "THE %s TAKES ITS SHARE" % (b_[0].get("shield") or "SHIELD").upper(),
                    ["  ·  ".join("a blow of %.1f: the shield took %.1f, %.1f reached her" % (x["before"], x["took"], x["reached"]) for x in b_[:2]),
                     "the shield loses what it takes: its durability falls by it, and at 0 it breaks"], cyan))
    for e in ev("tier2"):
        out.append((e["t"] + MW_CARD, e["t"] + MW_CARD + 4.0, e["notice"] or "TIER 2 IS OPEN", ["a tier opens once the tier before has 50 % of its rooms explored, monsters killed and chests looted",
                    "then a boss and 3 to 6 monsters of the new tier wait in a room she has seen (not hers): on the maps"], warm))
    for e in ev("at_boss"):
        out.append((e["t"] + MW_CARD + 4.0, e["t"] + MW_CARD + 8.0, "THE BOSS:  %s" % e["boss"].replace("_", " ").upper(), ["the strongest kind of tier 2, bigger, three times its hit points, its blows 1.6 times as hard",
                    "%.0f m off, in a room of the start set she has explored" % e["m"]], (255, 150, 120)))
    for e in ev("at_ring"):
        out.append((e["t"] + MW_CARD + 4.0, e["t"] + MW_CARD + 8.0, "A RING SHE NEVER FOUND:  %s" % e["ring"].upper(), ["the magic potency ring of the tier before (1 or 2), not found when the tier opened:",
                    "put in a room she has seen and guarded by 4 monsters of the new tier; the maps mark it"], (255, 150, 120)))
    for e in [x for x in EV if x["kind"] == "map" and x.get("open")]:
        e1 = next((x["t"] for x in EV if x["kind"] == "map" and not x.get("open") and x["t"] > e["t"]), e["t"] + 3.0)
        out.append((e["t"], e1, "M  ·  THE BIG MAP:  MISTWARD CASTLE", ["its marks: a crowned red ring for a boss, a gold ring for a guarded ring, a sack for her things,",
                    "a blue ring for a teleporter, a red X for a trap she has seen  ·  a far boss or ring sits at the edge, the way to it"], gold))
    for e in ev("cell_open"):
        out.append((e["t"], e["t"] + 4.4, "F  ·  A PRISONER SET FREE", [e.get("message") or "the prisoner thanks her", "the prisoner gives her a thing of the tier, walks out and is gone  ·  the castle keep's cells (tier 2)"], cyan))
    for e in ev("breakout"):
        out.append((e["t"], e["t"] + 4.0, "A CAGED MONSTER BREAKS OUT", ["a cell may hold a monster: it unlocks its cell itself as she comes near, and comes for her", "the castle keep: tier 2's look"], (255, 150, 120)))
    for e in ev("shape"):
        out.append((e["t"], e["t"] + 3.2, {"dome": "A DOMED ROOM", "step pyramid": "A STEPPED PYRAMID", "circle": "A ROUND ROOM"}.get(e["shape"], e["shape"].upper()),
                    ["rooms of other shapes: round, octagonal, hexagonal, triangular, L, T, U, a diamond; ceilings in domes, pyramids, steps",
                     "about 60 % of the castle's rooms; the maps draw their shapes"], gold))
    for e in ev("pad"):
        out.append((e["t"], e["t"] + 2.6, "F  ·  %s" % ("TIER 2'S TELEPORTER:  ITS RING" if e.get("tier") == 2 else "THE GREAT HALL'S TELEPORTER:  BACK TO TIER 2"),
                    [e.get("what", ""), "a teleporter in the great hall and in each tier's first set of rooms, its ring lying on it" if e.get("tier") == 2 else
                     "it takes her to the pad of a tier whose ring she holds"], cyan))
    for e in ev("hp_set"):
        out.append((e["t"], e["t"] + 3.0, "THE REEL TAKES HER HIT POINTS DOWN", ["to %.0f: a fight she loses" % e["hp"], "to show what happens when she falls"], warm))
    for e in ev("fell"):
        pl = next((x for x in EV if x["kind"] == "mw_piles" and x["t"] >= e["t"] - 2.0), None)
        things = pl["things"][-1] if pl and pl.get("things") else []          # (her pile: the newest)
        out.append((e["t"], e["t"] + 5.0, "SHE FALLS:  HER THINGS STAY WHERE SHE FELL", ["%d things in a pile: %s" % (len(things), ", ".join(x.lower() for x in things[:5]) + (" ..." if len(things) > 5 else "")),
                    "each shown as its picture over it, with a Loot Drops effect; the maps mark it; she comes back in the great hall with what her hero started with"], (255, 150, 120)))
    for e in ev("took_back"):
        out.append((e["t"], e["t"] + 3.4, "F  ·  HER THINGS TAKEN UP", [e.get("message", ""), "each as worn as it was"], cyan))
    for e in ev("disarm"):
        d1 = next((x for x in ev("disarmed") if x["t"] >= e["t"]), None)
        out.append((e["t"], (d1["t"] + 1.6) if d1 else e["t"] + 3.0, "F  ·  DISARMING", ["the Rogue alone sees traps (from 8 m: the message, the map's red X) and disarms them: F, then a moment's stillness",
                    (d1.get("message") if d1 else "") or "it may go off if she fumbles it"], cyan))
    st = ev1("start")
    if HERO == "Rogue" and st and st.get("trap"):
        sp = next((x for x in MSGS if "spot a trap" in x["text"]), None)
        if sp: out.append((sp["t"], sp["t"] + 2.6, "SHE SPOTS A TRAP", [sp["text"], "pits, darts, deadfalls, crushers, snares; glyphs, wards, emanations, cursed stones; chains, lingering traps, teleport traps"], gold))
    for e in ev("onto"):
        tr = next((x for x in EV if x["kind"] == "mw_trap" and x["t"] >= e["t"]), None)
        out.append((e["t"], (tr["t"] + 3.0) if tr else e["t"] + 4.0, "THE REEL WALKS HER ONTO A TRAP:  %s" % e["trap"].upper(), ["one she has seen: what a trap does to whoever steps on it",
                    ("it went off: %s" % tr.get("label", "")) if tr else ""], warm))
    for e in ev("ring_taken"):
        out.append((e["t"], e["t"] + 3.4, "THE RING TAKEN", ["the guards fallen, the ring is hers: the map's mark goes", "if every container of that room was open already, it lies on the floor (F takes it)"], cyan))
    for i, e in enumerate(FIGHTS):
        end = next((k["t"] for k in KILLS if k["t"] > e["t"]), e["t"] + 6.0) + 1.2
        if i + 1 < len(FIGHTS): end = min(end, FIGHTS[i + 1]["t"] - 0.1)
        tr = max(abs(e["section"][0]), abs(e["section"][1])) + 1
        boss = any(b["boss"] == e["monster"] for b in ev("at_boss")) and e["its_hit_points"] > 250
        out.append((e["t"], end, ("BOSS  %s  ·  OF TIER %d" % (e["monster"].replace("_", " ").upper(), tr + 1)) if boss else "%s  ·  TIER %d" % (e["monster"].replace("_", " ").upper(), tr), ["%.0f hit points, %.0f damage a blow  ·  she has %.0f" % (e["its_hit_points"], e["its_damage"], C["max_health"]),
                    lured(e) or ("its tier's strength: a boss three times its kind's" if boss else "the monsters' strength follows the tier of their set")], gold))
    return out

MA_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "martial_arts", "martial_arts.json")
def mw3_caps(ev, gold, cyan, warm):
    """(mistward, 815's mw3_martial: the Martial Artist, the user's of 2026-10-28 and 2026-10-29) her captions"""
    out = []
    chi = {c_["name"]: c_ for c_ in json.load(open(MA_JSON, encoding="utf-8"))["chi"]}
    def cl(t0): return inv_closed_after(t0 + 0.1)
    g_ = next((x for x in ev("given")), None)
    if g_: out.append((g_["t"], g_["t"] + 2.6, "THE REEL TEACHES HER ALL TEN CHI ATTACKS", ["she starts with two; each tier boss she slays teaches her two more: the reel gives her the other eight at once",
                        "with her fists that makes eleven attacks: the quick bar grows past ten slots"], warm))
    for e in [x for x in ev("inventory") if x.get("why") == "quickbar"]:
        b3 = next((x for x in ev("bar") if x.get("why") == "dash_in_3"), None); bd = next((x for x in ev("bar") if x.get("why") == "dodge_at_end"), None)
        t1 = b3["t"] if b3 else cl(e["t"])
        out.append((e["t"], t1, "I  ·  HER WEAPONS AND ABILITIES", ["each chi attack's picture shows its look: wind, lightning, fire, smoke, stars, rings, rods, fireworks, a meteor, chain lightning",
                    "her abilities, Dash and Dodge, go on the quick bar only if she puts them there"], gold))
        if b3:
            t2 = bd["t"] - 1.6 if bd else b3["t"] + 3.0
            out.append((b3["t"], t2, "3  ·  DASH INTO QUICK SLOT 3", ["a number puts the row under the cursor in that slot; the one there (the Side Kick) moves to a free slot", "its own number again takes it off the bar, and it stays off"], gold))
        if bd:
            out.append((bd["t"] - 1.6, cl(e["t"]), "D-PAD  ·  Y  ·  DODGE AFTER THE LAST SLOT", ["the D-pad chooses the slot (one past the last makes a new one), Y puts it there", "%d slots now: past the tenth, no number key; the D-pad reaches them" % len([s_ for s_ in bd["slots"] if s_ != "None"])], gold))
    dp = [x for x in ev("bar") if x.get("why") == "dpad"]
    ch = ev("chi")
    if dp:
        t1 = min([x["t"] for x in ch] + [dp[-1]["t"] + 1.5])
        run_ = [x for x in dp if x["t"] < t1]
        if run_: out.append((run_[0]["t"] - 0.6, run_[-1]["t"] + 1.2, "D-PAD RIGHT  ·  EVERY SLOT OF THE BAR", ["it steps through all %d slots, the last too: past the tenth the bar's ten pictures scroll" % len([s_ for s_ in run_[-1]["slots"] if s_ != "None"]),
                    "an ability on the way is made ready, not made: the attack button makes it"], gold))
    for e in ch:
        e1 = next((x for x in ev("chi_done") if x["t"] >= e["t"] and x["name"] == e["name"]), None); c_ = chi.get(e["name"], {})
        out.append((e["t"] - 0.4, (e1["t"] + 0.8) if e1 else e["t"] + 2.4, "CHI  ·  %s" % e["name"].upper(), [c_.get("effect", "").replace("Chi: ", ""),
                    ("%d damage (%s to the monster it struck)" % (round(e["damage"]), nice((e1 or {}).get("lost", 0))) if (e1 or {}).get("lost", 0) > 0 else "%d damage  ·  this one missed: the monster moved off" % round(e["damage"]))
                    + "  ·  %d mana  ·  the reel fills her mana before each" % e.get("mana", 0)], cyan))
    for e in ev("ability"):
        out.append((e["t"] - 0.8, e["t"] + 1.8, "%s FROM THE QUICK BAR" % e["name"].upper(), [e.get("how", ""), "made: %s" % ("yes" if e.get("made") else "no")], cyan))
    return out

def mw4_caps():
    """(mistward, 815's run5m4: the user's list of 2026-10-30) the six heroes in combat at all five tiers: the captions, each from
    what the record says happened"""
    out = []; gold = (255, 226, 150); warm = (255, 200, 120); cyan = lin(CYAN)[:3]; red = (255, 150, 120)
    hj = HJ.get(HERO, {}); acc = tuple(int(255 * v) for v in hj.get("accent", (1.0, 0.94, 0.84)))
    ev = lambda k: [e for e in EV if e["kind"] == k]
    THEME = {"Castle": "the castle keep", "Dwarf": "the dwarven halls", "None": "the stone dungeon", "": "the stone dungeon"}
    st = ev1("start")
    first = min([e["t"] for e in EV if e["kind"] in ("given", "card", "fight", "inventory", "summoned") and e["t"] > 0.8] + [5.0])
    who = {"Warrior": "tiers 1 and 2: her sword and shield; a dead monster's parts; tier 2's new rooms",
           "Mage": "tier 3: her spells, a scroll of a spell beyond her mana",
           "Warlock": "tier 2: a curse, a lash and her sword",
           "Rogue": "tier 3: the crossbow, the daggers, her roll",
           "MartialArtist": "tier 4: her chi attacks, then her fists",
           "Summoner": "tiers 1 and 5: the new hero, Summoner4: she calls fighters to her side, a stronger kind for each tier"}.get(HERO, "")
    out.append((0.8, first - 0.1, "THE %s IN MISTWARD CASTLE" % HNAME.upper(), [who, "%d hit points%s  ·  monsters killed leave their parts floating over them (F takes them)" %
                (C["max_health"], ("  ·  %d mana" % C.get("max_mana", 0)) if C.get("max_mana") else "")], acc))
    for e in ev("given"):
        it = e.get("items", {})
        if e.get("why") == "tomes" or any(k.startswith("Tome of ") for k in it):
            txt = ", ".join(k.replace("Tome of ", "").lower() for k in it); line2 = "a tome teaches its spell to a hero who learns its type"
        elif e.get("why") == "scroll":
            # (the spell's cost from the table the game is built from (858's spells.json), her pool from the record: the PR
            # review's find, the numbers had been typed in)
            ms_ = next((s_ for s_ in json.load(open(os.path.join(os.path.dirname(SRC), "random_dungeon_magic5", "spells.json"), encoding="utf-8"))["spells"]
                        if s_["name"] == "Meteor Storm"), {}).get("mana", 0)
            pool_ = C.get("max_mana", 0)
            txt = "a scroll of Meteor Storm"; line2 = "a scroll casts its spell once at no mana: Meteor Storm costs %d, %s her pool of %d" % (
                ms_, ("twice" if pool_ and abs(ms_ / pool_ - 2) < 0.01 else "%.1f times" % (ms_ / pool_)) if pool_ else "more than", pool_)
        elif e.get("why") == "sword":
            txt = "a sword"; line2 = "she starts with the worst weapon she can wield (the dagger): the arming sword, one-handed, her shield on her arm with it"
        elif "summonings" in it:
            txt = "the four summonings four tier bosses would"; line2 = "she starts with Summon Tier 1; each tier boss she slays gives her the next"
        elif "chi attacks" in it:
            txt = "the eight chi attacks four tier bosses would"; line2 = "she starts with two; each tier boss she slays teaches her two more"
        else: txt = ", ".join("%s %s" % (v, k.lower()) for k, v in it.items()); line2 = "in play they come from containers and bosses"
        out.append((e["t"], e["t"] + 2.4, "THE REEL GIVES HER %s" % txt.upper(), [line2, ""], warm))
    for e in ev("card"):
        lnd = next((x for x in EV if x["kind"] in ("landed", "tier2") and x["t"] >= e["t"] - 0.05), None)
        if lnd and lnd["kind"] == "landed":
            out.append((e["t"] + MW_CARD, e["t"] + MW_CARD + 3.6, "TIER %d  ·  %s" % (lnd["tier"], THEME.get(lnd.get("theme", ""), lnd.get("theme", "")).upper()),
                        ["a set of rooms generated as she arrives: %d monsters of tier %d (%s, %d hit points, %d a blow, before her)" % (lnd.get("monsters", 0), lnd["tier"],
                         lnd["title"].lower(), lnd["its_hit_points"], lnd["its_damage"]), "the monsters' strength follows their tier"], gold))          # (no typed numbers: the review's find)
    for e in ev("tier2"):
        out.append((e["t"] + MW_CARD, e["t"] + MW_CARD + 3.4, e.get("notice") or "TIER 2 IS OPEN", ["a tier opens once the tier before has 50 % of its rooms explored, monsters killed and chests looted",
                    "the reel's shortcut cleared the start set; a boss waits in a room she has seen"], warm))
    for e in ev("new_terrain"):
        out.append((e["t"], e["t"] + 4.0, "NEW TERRAIN:  TIER %d, %s" % (e["tier"], THEME.get(e.get("theme", ""), e.get("theme", "")).upper()),
                    ["the next set of rooms is generated as she comes (%.0f m from its hallway): its rooms, furniture, chests, traps and monsters" % e.get("her_m", 0),
                     "made from the session's seed: the same set every time she comes back"], cyan))
    for e in ev("summoned"):
        a = (e.get("allies") or [{}])[0]
        out.append((e["t"] - 1.0, e["t"] + 2.2, "%s  ·  %s" % (e["spell"].upper(), e.get("monster_kind", "").replace("_", " ").upper()),
                    ["%s answers her call (%d of %d she may lead)  ·  %s hit points, %s a blow: as strong as a monster of its own tier" % (e.get("monster_kind", "").replace("_", " ").lower(), e["now"], e["most"],
                     a.get("hp", "?"), a.get("damage", "?")), "each summoning takes half her mana (%d): the reel fills her mana before each" % round(C.get("max_mana", 0) / 2)], cyan))
    for e in ev("scroll_read"):
        d_ = next((x for x in ev("scroll_done") if x["t"] >= e["t"]), None)
        # (what the strikes did only once they are done: from the reading on it said "1 killed" while her kills read 0)
        out.append((e["t"], d_["t"] if d_ else e["t"] + 5.0, "ENTER  ·  THE SCROLL OF METEOR STORM", [e.get("message", ""),
                    "its strikes fall round the monster she faces  ·  her mana %d" % e.get("mana_before", 0)], cyan))
        if d_:
            out.append((d_["t"], d_["t"] + 3.0, "THE SCROLL OF METEOR STORM", ["%d hit points taken off the monsters there, %d killed" % (d_["lost"], d_["killed"]),
                        "her mana %d before and after: a scroll casts at no mana" % d_["mana_after"]], cyan))
    for e in ev("chi"):
        e1 = next((x for x in ev("chi_done") if x["t"] >= e["t"] and x["name"] == e["name"]), None)
        out.append((e["t"] - 0.3, (e1["t"] + 0.6) if e1 else e["t"] + 2.0, "CHI  ·  %s" % e["name"].upper(), ["%d damage%s  ·  %d mana (the reel fills her mana before each)" % (round(e["damage"]),
                    (": %s taken off the %s" % (nice((e1 or {}).get("lost", 0)), e["monster"].replace("_", " ").lower())) if (e1 or {}).get("lost") else "", e.get("mana", 0)), ""], cyan))
    for e in ev("harvest_taken"):
        th = next((x for x in ev("to_harvest") if x["t"] <= e["t"]), None)
        out.append((e["t"] - 1.6, e["t"] + 2.4, "F  ·  A DEAD MONSTER'S PARTS", [e.get("message", ""), "an essence of its tier or below, its kind's part, now and then a material: potions and scrolls are made of them at an anvil"], cyan))
    blocks = ev("mw_shield_block")
    if blocks:
        b_ = blocks[0]
        out.append((b_["t"] - 0.1, b_["t"] + 2.4, "THE %s TAKES ITS SHARE" % (b_.get("shield") or "SHIELD").upper(), ["a blow of %.1f: the shield took %.1f, %.1f reached her" % (b_["before"], b_["took"], b_["reached"]),
                    "the shield loses what it takes: at 0 it breaks"], cyan))
    heals = ev("healed")
    if heals:
        out.append((heals[0]["t"], heals[0]["t"] + 3.0, "THE REEL FILLS HER HIT POINTS", ["%d to %d: the higher tiers' blows end a run in a few (it does so again whenever they fall under three quarters)" % (heals[0]["was"], heals[0]["now"]),
                    "in play she would wear armour and rings found by then"], warm))
    for e in ev("set_down"):
        out.append((e["t"] + MW_CARD - 0.2, e["t"] + MW_CARD + 2.6, "ON TO THE NEXT SET OF ROOMS", ["a set is 252 m across: the reel sets her down %.0f m before the hallway out (it was %d m by the way)" % (e["to_portal_m"], e["was_way_m"]),
                    "the set beyond is generated as she comes"], warm))
    for i, e in enumerate(FIGHTS):
        end = next((k["t"] for k in KILLS if k["t"] > e["t"]), e["t"] + 6.0) + 1.0
        if i + 1 < len(FIGHTS): end = min(end, FIGHTS[i + 1]["t"] - 0.1)
        tr = e.get("tier") or (max(abs(e["section"][0]), abs(e["section"][1])) + 1)
        kl = next((k for k in KILLS if k["t"] > e["t"] and k["t"] <= end + 0.1 and k["monster"] == e["monster"]), None)
        out.append((e["t"], end, "%s  ·  TIER %d" % (e["monster"].replace("_", " ").upper(), tr), ["%.0f hit points, %.0f damage a blow  ·  she has %.0f" % (e["its_hit_points"], e["its_damage"], C["max_health"]),
                    ("killed in %.1f s" % kl["seconds"]) if kl else (lured(e) or "the monsters' strength follows their tier")], gold))
    return out

def mw2_caps():
    """(mistward, 815's run5m2: the user's third list) the captions, each from what the record says happened"""
    out = []; gold = (255, 226, 150); warm = (255, 200, 120); cyan = lin(CYAN)[:3]; red = (255, 150, 120)
    hj = HJ.get(HERO, {}); acc = tuple(int(255 * v) for v in hj.get("accent", (1.0, 0.94, 0.84)))
    ev = lambda k: [e for e in EV if e["kind"] == k]
    nxt = lambda t0, kinds: min([e["t"] for e in EV if e["t"] > t0 + 0.2 and e["kind"] in kinds] + [t0 + 6.0])
    st = ev1("start")
    first = min([e["t"] for e in EV if e["kind"] in ("inventory", "card", "to_chest", "vault", "outlined") and e["t"] > 0.8] + [5.0])
    who = {"Warrior": "she starts with the worst weapon she can wield and the worst shield, no armour; she blocks; a boss's slash goes on her weapons",
           "Mage": "the inventory in five tabs; a shrine's blessing; fountains of mana and healing",
           "Warlock": "a vault and its key; a fountain of speed; the arena",
           "Rogue": "a trap she has seen is outlined in red; the trap gauntlet; the throne room's usurper",
           "MartialArtist": "her chi attacks' looks on her fists and legs and their pictures; a quick bar of any length, the D-pad through all of it; her abilities on it"}[HERO]
    out.append((0.8, first - 0.1, "THE %s IN MISTWARD CASTLE" % HNAME.upper(), ["new: " + who, "eight kinds of rooms of their own in every tier: shrines, three fountains, arenas, trap gauntlets, vaults, throne rooms"], acc))
    inv = ev("inventory"); tabs = ev("tab")
    for e in inv:
        cl = inv_closed_after(e["t"] + 0.1)
        if e.get("why") == "start_gear" and st:
            out.append((e["t"], e["t"] + 2.9, "I  ·  HER WEAPONS:  THE DAGGER", ["the Warrior starts with the worst weapon she can wield: the dagger, 11 a blow",
                        "hers for good: it never breaks, and it stays with her when she falls"], gold))
            out.append((e["t"] + 2.9, cl, "E  ·  THE ARMOUR TAB:  %s" % (st.get("shield") or "").upper(), ["and the worst shield, on her arm with a one-handed weapon; no armour",
                        "the inventory's tabs: weapons, armour (shields too), potions and food, crafting, magic  ·  Q / E, LB / RB or a click"], gold))
        elif e.get("why") == "tabs":
            g_ = next((x for x in ev("given") if x["t"] <= e["t"]), None)
            out.append((e["t"], cl, "I  ·  THE INVENTORY'S FIVE TABS", ["E (RB) the next tab, Q (LB) the one before, or a click on it: weapons, armour, potions and food, crafting, magic",
                        ("the reel gave her: " + ", ".join("%d %s" % (n_, k_.lower()) for k_, n_ in g_["items"].items())) if g_ else "each tab's count on it"], gold))
        elif e.get("why") == "slot":
            sl = next((x for x in ev("slot") if x["t"] >= e["t"]), None)
            out.append((e["t"], cl, "I  ·  2  ·  QUICK SLOT 2", ["in the inventory a number puts the weapon under the cursor in that slot (the gamepad: Y, the D-pad choosing the slot)",
                        ("her slots now: " + ", ".join("%d %s" % ((k_ + 1) % 10, x.lower()) for k_, x in enumerate(sl["slots"]) if x != "None")) if sl else ""], gold))
        elif e.get("why") == "slash":
            on = next((x for x in ev("slash_on") if x["t"] >= e["t"]), None); sd_ = SLASHES.get(e.get("slash", ""), {})
            out.append((e["t"], cl, "I  ·  MAGIC  ·  ENTER  ·  THE %s" % e.get("slash", "").upper(), ["Enter on a slash, then on the weapon it goes on: %s" % ((on or {}).get("message") or ""),
                        "+%d %s on every hit; %s  ·  T takes it off again, for another weapon" % (round(sd_.get("bonus", 0)), sd_.get("type", "").lower(), sd_.get("text", ""))], cyan))
    if HERO == "MartialArtist": out.extend(mw3_caps(ev, gold, cyan, warm))
    for e in ev("pickup"):
        out.append((e["t"], e["t"] + 2.4, "F  ·  FROM AN ARMORY'S TABLE", [e.get("message", ""), "the armories' tables hold weapons and shields of the set's tier: F takes one and it is gone from the table"], gold))
    dr = ev("draw")
    if dr:
        out.append((dr[0]["t"] - 0.2, dr[-1]["t"] + 1.4, "1 - 0:  HER QUICK SLOTS", ["  ·  ".join("%s %s" % (x["key"], x["weapon"].lower()) for x in dr) + "  ·  the D-pad left / right steps through them",
                    "with a one-handed weapon her shield is on her arm (in hand: %s)" % ("yes" if dr[0].get("shield_in_hand") else "no")], gold))
    for e in [x for x in ev("block") if x.get("on")]:
        e1 = next((x for x in ev("block") if not x.get("on") and x["t"] > e["t"]), None)
        out.append((e["t"], (e1["t"] + 1.8) if e1 else e["t"] + 4.0, "RIGHT MOUSE (LT) HELD:  THE BLOCK", ["%d blows on the raised shield: it takes its share + 30 %% (%d %% of each)" % ((e1 or {}).get("blocked", 0), round((e1 or {}).get("share", 0) * 100)),
                    "she walks at half speed meanwhile, and the shield wears five times as fast (%.1f off the last blow)" % (e1 or {}).get("wear", 0)], cyan))
    for e in ev("hp_down"):
        sh_ = 2.6 if any(x["kind"] == "at_throne" and abs(x["t"] - e["t"]) < 0.5 for x in EV) else 0.0          # (after the usurper's own caption)
        out.append((e["t"] + MW_CARD + sh_, e["t"] + MW_CARD + sh_ + 3.6, "THE REEL TAKES ITS HIT POINTS DOWN", ["%s: %d to %d" % (e["monster"].replace("_", " ").lower(), e["was"], e["now"]), e["why"]], warm))
    for e in ev("slash_found"):
        for s_ in e["slashes"]:
            sd_ = SLASHES.get(s_, {})
            out.append((e["t"], e["t"] + 4.0, "A SLASH:  THE %s" % s_.upper(), ["a slain boss (or a throne room's usurper) gives a slash of its tier: tier %d's  ·  +%d %s on every hit" % (sd_.get("tier", 0), round(sd_.get("bonus", 0)), sd_.get("type", "").lower()),
                        "%s  ·  the Warrior's weapons only, bows and crossbows too" % sd_.get("text", "")], cyan))
    procs = [x for x in ev("slash_proc") if x["effect"] not in ("prismatic",)]
    if procs and ev("slash_on"):
        p0 = next((x for x in procs if x["t"] > ev("slash_on")[0]["t"]), None)
        if p0:
            sd_ = SLASHES.get(ev("slash_on")[0].get("slash", ""), {})
            out.append((p0["t"] - 0.3, p0["t"] + 3.6, "THE %s STRIKES" % ev("slash_on")[0].get("slash", "").upper(), ["its look plays on each swing and its burst on each hit: the Stylized Slashes pack's", "+%d %s, and %s" % (round(sd_.get("bonus", 0)), sd_.get("type", "").lower(), sd_.get("text", ""))], cyan))
    for e in ev("worn_set"):
        out.append((e["t"], e["t"] + 1.6, "THE REEL GIVES HER THE PLATE ARMOUR", ["a set with a helmet: 12 of the 27 sets have one", "found on the mesh: the parts her head bone moves"], warm))
    hl = ev("helmet")
    for e in hl:
        out.append((e["t"], e["t"] + 2.0, "H  ·  THE HELMET %s" % ("HIDDEN" if e.get("hidden") else "SHOWN"), ["H, or its line in the armour tab, hides the worn set's helmet and shows it again",
                    "its share of the blows stays the same"], gold))
    for e in ev("shrine"):
        out.append((e["t"], e["t"] + 3.6, "F  ·  THE SHRINE:  %s" % (e.get("blessing") or "").upper(), [e.get("message", ""), "one of three blessings for 90 s: might (+25 % damage), the bulwark (25 % less from blows), swiftness (+20 % speed)  ·  once"], cyan))
    for e in ev("fountain"):
        w_ = e.get("which")
        out.append((e["t"], e["t"] + 3.6, "F  ·  %s" % {"heal": "THE HEALING FOUNTAIN", "mana": "THE FOUNTAIN OF MANA", "speed": "THE FOUNTAIN OF SPEED"}.get(w_, "A FOUNTAIN"),
                    [e.get("message", ""), {"heal": "60 % of her hit points back, once: then it is dry", "mana": "her mana full again, once: then it is dry", "speed": "30 % faster for 45 s, once: then it is dry"}.get(w_, "")], cyan))
    for e in ev("hp_set"):
        out.append((e["t"] + MW_CARD, e["t"] + MW_CARD + 2.6, "THE REEL TAKES HER HIT POINTS DOWN", ["to %.0f, to show the fountain" % e["hp"], ""], warm))
    for e in ev("vault"):
        if e.get("step") == "locked":
            out.append((e["t"], e["t"] + 3.0, "F  ·  THE VAULT IS LOCKED", [e.get("message", ""), "a vault's chests hold things of the tier above its own"], gold))
        else:
            out.append((e["t"], e["t"] + 3.0, "F  ·  HER KEY OPENS THE VAULT", [e.get("message", "") or "the key is used up", "the vault stays open"], cyan))
    for e in ev("key"):
        out.append((e["t"] - 1.2, e["t"] + 2.2, "ITS KEY, IN A CHEST", ["one chest or trunk of another room of the same set holds it", "she has %d" % e.get("has", 0)], gold))
    ar = ev1("arena")
    if ar:
        aw = ev1("arena_won")
        out.append((ar["t"], ar["t"] + 4.0, "THE ARENA:  ITS DOORS SHUT", ["%d of its doors open now: none until three waves are beaten" % ar.get("doors_open", 0), "each wave 2 + the tier's monsters, at the room's far side"], red))
        if aw: out.append((aw["t"], aw["t"] + 4.0, "THE ARENA IS WON", ["its doors unlock: she can open them again", "its prize lies in the middle: three things of its tier"], cyan))
    for e in ev("prize"):
        out.append((e["t"], e["t"] + 3.0, "F  ·  THE ARENA'S PRIZE", [e.get("message", ""), "three things of its tier"], gold))
    for e in ev("outlined"):
        out.append((e["t"] - 1.8, e["t"] + 2.4, "THE ROGUE SEES THE TRAPS: OUTLINED IN RED", ["%d of the gauntlet's traps within her 8 m: each plate drawn over in red, a red disc at its reach, a red glow" % e.get("n", 0),
                    "the other heroes see no trap: nothing is outlined for them"], red))
    for e in ev("disarm"):
        d1 = next((x for x in ev("disarmed") if x["t"] >= e["t"]), None)
        out.append((e["t"], (d1["t"] + 1.6) if d1 else e["t"] + 3.0, "F  ·  DISARMING", [(d1 or {}).get("message", "") or "it may go off if she fumbles it", "the trap gauntlet: a corridor of traps with a chest at its far end"], cyan))
    for e in ev("mw_trap"):
        said = next((x["text"] for x in MSGS if e["t"] - 0.05 <= x["t"] <= e["t"] + 1.0 and x["text"].startswith("A ") and len(x["text"]) > 30), "")
        out.append((e["t"], e["t"] + 3.2, "A TRAP:  %s" % (e.get("label") or "").upper(), [said or "she stepped on one on her way", "she had not disarmed it: on her way to the chest she stepped on it"], red))
    for e in ev("at_throne"):
        out.append((e["t"] + MW_CARD, e["t"] + MW_CARD + 4.0, "THE THRONE ROOM'S USURPER", ["%s on the dais: a boss of its tier" % e["usurper"].replace("_", " ").lower(), "slain, it gives a slash (the Warrior's weapons take it)"], red))
    for e in ev("usurper"):
        out.append((e["t"], e["t"] + 3.0, e.get("notice") or "THE USURPER IS SLAIN", ["the throne room is won", ""], cyan))
    for i, e in enumerate(FIGHTS):
        end = next((k["t"] for k in KILLS if k["t"] > e["t"]), e["t"] + 6.0) + 1.2
        if i + 1 < len(FIGHTS): end = min(end, FIGHTS[i + 1]["t"] - 0.1)
        tr = max(abs(e["section"][0]), abs(e["section"][1])) + 1
        out.append((e["t"], end, "%s  ·  TIER %d" % (e["monster"].replace("_", " ").upper(), tr), ["%.0f hit points, %.0f damage a blow  ·  she has %.0f" % (e["its_hit_points"], e["its_damage"], C["max_health"]),
                    lured(e) or "the monsters' strength follows the tier of their set"], gold))
    return out

def mw_hud(o, d, r, t, ua, mapo):
    """(mistward) what the castle's HUD adds: the frame rate (upper left), the castle's name over the minimap, what F would
    do near her, the disarm bar, the fallen banner"""
    fps = r.get("fps", 0.0)
    if fps > 0:
        # (as ARDHUD draws it since 2026-10-27: in the corner over the controls, larger, on a dark framed plate, green / amber /
        # red by the rate)
        s_ = "%d FPS  ·  %.1f MS" % (round(fps), 1000.0 / fps); tw = d.textlength(s_, font=fl_fps); mg = 44 * K
        x0, y0, x1, y1 = mg, mg - 6 * K, mg + tw + 24 * K, mg + 34 * K
        blend_box(o, (x0, y0, x1, y1), 4 * K, (3, 3, 4, int(215 * ua))); d = ImageDraw.Draw(o, "RGBA")
        d.rectangle((x0, y0, x1, y1), outline=lin((0.75, 0.65, 0.45), 0.9 * ua), width=max(1, int(1.5 * K)))
        fc = (0.55, 1.0, 0.6) if fps >= 50 else (1.0, 0.85, 0.35) if fps >= 30 else (1.0, 0.4, 0.3)
        d.text((x0 + 12 * K, (y0 + y1) / 2), s_, font=fl_fps, fill=lin(fc, ua), anchor="lm")
    if not mapo:
        P = 300 * K; mg = 24 * K
        text_c(d, (W * K - mg - P / 2, 8 * K), sc((C.get("game_title") or "").upper()), fl_small, lin((1.0, 0.84, 0.45), ua), "mt")
    near = r.get("near", "")
    if near and not r.get("inv", [0])[0] and not r.get("craft", [0])[0] and not r.get("dead"):
        s_ = "[F]  " + near; tw = d.textlength(s_, font=f_line); y_ = H * K * 0.72
        blend_box(o, (W * K / 2 - tw / 2 - 16 * K, y_ - 6 * K, W * K / 2 + tw / 2 + 16 * K, y_ + 38 * K), 8 * K, (8, 8, 10, int(160 * ua))); d = ImageDraw.Draw(o, "RGBA")
        d.text((W * K / 2, y_), s_, font=f_line, fill=lin((0.95, 0.92, 0.82), ua), anchor="ma")
    dis = r.get("dis", -1.0)
    if dis is not None and dis >= 0:
        bw, bh = 360 * K, 18 * K; x0, y0 = W * K / 2 - bw / 2, H * K * 0.72 + 50 * K
        d.rectangle((x0 - 2 * K, y0 - 2 * K, x0 + bw + 2 * K, y0 + bh + 2 * K), fill=(0, 0, 0, int(180 * ua)))
        d.rectangle((x0, y0, x0 + bw * dis, y0 + bh), fill=lin((0.95, 0.8, 0.3), ua))
        text_c(d, (W * K / 2, y0 + bh + 6 * K), "disarming  %d%%" % round(dis * 100), f_small, lin(INK, ua), "mt")
    if r.get("dead"):
        text_c(d, (W * K / 2, H * K * 0.45), "YOU HAVE FALLEN", f_title, lin((1.0, 0.3, 0.25), ua))
        text_c(d, (W * K / 2, H * K * 0.45 + 60 * K), "your things lie where you fell: back to the great hall...", f_line, lin(INK, ua))
    return d
# ---------------------------------------------------------------- run5s: the spells, rings, monsters by tier, corpses and menu reel
SPELLS = {s_["name"]: s_ for s_ in C.get("spells", [])}
SPELL_EV = [e for e in EV if e["kind"] == "spell"]; MENU_EV = [e for e in EV if e["kind"] == "menu"]
GIVEN = [e for e in EV if e["kind"] == "given"]; RING_ON = ev1("ring_on"); BROKEN = ev1("broken_down"); CORPSE = [e for e in EV if e["kind"] == "corpse"]
RAISE = ev1("raise"); EMPTY0, EMPTY1 = ev1("empty_pick"), ev1("empty_opened"); VOLS = [e for e in EV if e["kind"] == "volume"]
if S5 and JUMP and LANDED: CARD = (JUMP["t"], LANDED["t"] + 3.0)                       # (run5s: the card over the jump into tier 3)
def nice(v): return ("%.1f" % v).rstrip("0").rstrip(".")
def hotbar(o, r, t, ua):
    """ARDHUD::DrawHotbar: a slot for each of her first ten weapons and spells, bottom middle; the one in hand framed in
    gold, a cooldown's share shaded from the top with its seconds, the mana a cast takes (red when she has less)"""
    d = ImageDraw.Draw(o, "RGBA"); WL = weapons_at(t)
    along = [k_ for k_, w_ in enumerate(WL) if w_.get("alongside")] if MW2 else []          # (after the ten: a spell cast alongside, key E)
    n = 10 + len(along) if MW2 else min(len(WL), 10)
    if n <= 0: return
    qs_ = r.get("qs", [])
    # (mw3, the user's of 2026-10-29: the bar's ten slots in sight from "qf", abilities ("@Dash") in slots, more each way)
    qf = max(0, min(r.get("qf", 0), max(0, len(qs_) - 10))) if MW2 else 0
    slot_label = slot_lab
    def slot_weapon(i):
        """(run5m2) the weapon of a quick slot: the one drawn if it has that name, else the first of the name"""
        if not MW2: return i
        if i >= 10: return along[i - 10]
        nm_ = qs_[qf + i] if qf + i < len(qs_) else "None"
        if nm_.startswith("@"): return -2
        if nm_ in ("", "None"): return -1
        if 0 <= r["w"] < len(WL) and WL[r["w"]]["name"] == nm_: return r["w"]
        return next((k_ for k_, w_ in enumerate(WL) if w_["name"] == nm_ and not w_.get("alongside")), -1)
    S_, gp = 64 * K, 8 * K; tw_ = n * S_ + (n - 1) * gp; x0, y0 = (W * K - tw_) / 2, H * K - S_ - 26 * K
    cds = r.get("cd", []); mana = r.get("mana", 0.0); atk = r.get("atki", -1)
    slot = bool(UI and UI.has("slot"))
    if MW2 and len(qs_) > 10:
        if qf > 0: d.text((x0 - 10 * K, y0 + S_ / 2), "< %d" % qf, font=ft_small, fill=lin((1.0, 0.82, 0.35), ua), anchor="rm")
        if len(qs_) - qf - 10 > 0: d.text((x0 + tw_ + 10 * K, y0 + S_ / 2), "%d >" % (len(qs_) - qf - 10), font=ft_small, fill=lin((1.0, 0.82, 0.35), ua), anchor="lm")
    for si in range(n):
        i = slot_weapon(si)
        a, b = (x0 + si * (S_ + gp), y0), (x0 + si * (S_ + gp) + S_, y0 + S_)
        q_ = qf + si
        if i == -2:
            # (an ability on the bar: its picture, lit while ready)
            ab_ = qs_[q_]; on = r.get("ra", "None") == ab_
            if slot: UI.nine(o, "slot", a, b, 12 * K / max(UI.L["slot"]["border"][0] * UI.img["slot"].size[0], 1), (1.15, 1.05, 0.85, ua) if on else (0.62, 0.62, 0.62, ua)); d = ImageDraw.Draw(o, "RGBA")
            ic = "ability_" + ab_[1:].lower()
            if UI and UI.has(ic): UI.fit(o, ic, (a[0] + 8 * K, a[1] + 8 * K), (b[0] - 8 * K, b[1] - 8 * K), ((1.0, 1.0, 1.0) if on else (0.75, 0.75, 0.75)) + (ua,)); d = ImageDraw.Draw(o, "RGBA")
            if on: d.rectangle((a[0] + 1, a[1] + 1, b[0] - 1, b[1] - 1), outline=lin((0.55, 0.85, 1.0), 0.95 * ua), width=int(2.5 * K))
            d.text((a[0] + 5 * K, a[1] + 2 * K), slot_label(q_), font=ft_tiny, fill=lin((1.0, 0.82, 0.35) if q_ < 10 else (0.6, 0.55, 0.4), ua)); continue
        if i < 0:
            # (an empty quick slot: dim, its number)
            if slot: UI.nine(o, "slot", a, b, 12 * K / max(UI.L["slot"]["border"][0] * UI.img["slot"].size[0], 1), (0.35, 0.35, 0.35, ua)); d = ImageDraw.Draw(o, "RGBA")
            else: d.rectangle((*a, *b), fill=lin((0.04, 0.04, 0.05), 0.6 * ua))
            d.text((a[0] + 5 * K, a[1] + 2 * K), slot_label(q_) if MW2 else str((si + 1) % 10), font=ft_tiny, fill=lin((0.6, 0.55, 0.4), ua)); continue
        wd = WL[i]; on = (atk == i) if wd.get("alongside") else (i == r["w"] and r.get("ra", "None") == "None")
        cd = cds[i] if i < len(cds) else 0.0; nomana = wd.get("mana", 0) > 0 and mana < wd["mana"]
        if slot:
            sp = 12 * K / max(UI.L["slot"]["border"][0] * UI.img["slot"].size[0], 1)
            UI.nine(o, "slot", a, b, sp, (1.15, 1.05, 0.85, ua) if on else (0.62, 0.62, 0.62, ua)); d = ImageDraw.Draw(o, "RGBA")
        else: d.rectangle((*a, *b), fill=lin((0.06, 0.06, 0.08), 0.85 * ua))
        ic = wd.get("icon") if (UI and wd.get("icon") and UI.has(wd.get("icon"))) else wicon(wd["name"])
        tint = (1.0, 0.45, 0.4) if nomana else ((1.0, 1.0, 1.0) if on else (0.75, 0.75, 0.75))
        if ic and UI.has(ic): UI.fit(o, ic, (a[0] + 8 * K, a[1] + 8 * K), (b[0] - 8 * K, b[1] - 8 * K), tint + (ua,)); d = ImageDraw.Draw(o, "RGBA")
        else:
            ab = "".join(w_[:1].upper() for w_ in wd["name"].split()[:3])
            d.text(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), ab, font=ft_small, fill=lin(tint, ua), anchor="mm")
        cdmax = wd.get("cooldown", 0) or 0
        if cd > 0 and cdmax > 0:
            fr = max(0.0, min(1.0, cd / cdmax))
            d.rectangle((a[0], a[1], b[0], a[1] + (b[1] - a[1]) * fr), fill=(0, 0, 0, int(158 * ua)))
            d.text(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), "%d" % math.ceil(cd), font=ft_small, fill=lin((1.0, 0.9, 0.6), ua), anchor="mm")
        if on: d.rectangle((a[0] + 1, a[1] + 1, b[0] - 1, b[1] - 1), outline=lin((1.0, 0.82, 0.35), 0.95 * ua), width=int(2.5 * K))
        d.text((a[0] + 5 * K, a[1] + 2 * K), "E" if wd.get("alongside") else (slot_label(q_) if MW2 else str((si + 1) % 10)), font=ft_tiny, fill=lin((1.0, 0.82, 0.35) if not (MW2 and q_ >= 10) else (0.6, 0.55, 0.4), ua))
        if MW2 and wd.get("slash"):
            sc_ = SLASHES.get(wd["slash"], {}).get("color", [0.4, 0.9, 1.0])
            d.rectangle((a[0] + 6 * K, b[1] - 7 * K, b[0] - 6 * K, b[1] - 3 * K), fill=lin(sc_, 0.95 * ua))
        if wd.get("mana", 0) > 0: d.text((b[0] - 5 * K, b[1] - 3 * K), "%d" % wd["mana"], font=f_tiny, fill=lin((1.0, 0.4, 0.35) if nomana else (0.6, 0.75, 1.0), ua), anchor="rd")
    if MW2 and r.get("ra", "None") not in ("None", ""):
        text_c(d, (W * K / 2, y0 - 6 * K), sc("%s READY  \u00b7  THE ATTACK BUTTON MAKES IT" % r["ra"][1:].upper()), fl_small, lin((0.6, 0.88, 1.0), ua), "mb")
    elif 0 <= r["w"] < len(WL):
        qc_ = r.get("qc", -1)
        s_ = WL[r["w"]]["name"].upper() + (("    (slot %s of %d: the D-pad)" % (slot_label(qc_), len(qs_)) if qc_ >= 0 else "") if MW2 and len(qs_) > 10 else ("    (%d more: the wheel)" % (len(WL) - 10) if len(WL) > 10 and not MW2 else ""))
        text_c(d, (W * K / 2, y0 - 6 * K), sc(s_), fl_small, lin(INK, ua), "mb")
def buff_chips(o, d, bx, top, ua, buffs):
    """(level 5) her spells on her and what the monsters did to her: a chip each, right to left (ARDHUD::DrawCombat)"""
    x = bx
    for bl in buffs:
        q = bl.split("|")
        if len(q) < 3: continue
        good = q[2] == "1"; s_ = sc("%s  %ds" % (q[0], math.ceil(float(q[1])))); tw = d.textlength(s_, font=fl_tiny)
        c0 = (x - tw - 16 * K, top - 30 * K)
        d.rectangle((c0[0], c0[1], x, top), fill=lin((0.16, 0.12, 0.30) if good else (0.32, 0.08, 0.08), 0.85 * ua), outline=lin((0.75, 0.6, 1.0) if good else (1.0, 0.4, 0.3), ua), width=K)
        d.text((c0[0] + 8 * K, c0[1] + 6 * K), s_, font=fl_tiny, fill=(255, 255, 255, int(255 * ua))); x = c0[0] - 8 * K
def menu_panel(top, r, t, ua):
    """ARDHUD::DrawMenu: Esc's menu over the game: the four volumes as sliders, Resume, Choose another hero, Quit"""
    o = Image.new("RGBA", top.size, (0, 0, 3, int(158 * ua))); d = ImageDraw.Draw(o, "RGBA")
    me = last_at([e for e in EV if e["kind"] == "menu_lines"], t); lines = me["lines"] if me and me["lines"] else []
    vols = r.get("menu", [0, 0, [1, 1, 1, 1]])[2]; cur = r.get("menu", [0, 0])[1]
    if not lines: lines = ["volume|Overall volume|1", "volume|Action sounds|1", "volume|Environment sounds|1", "volume|Music|1", "button|Resume", "button|Choose another hero", "button|Quit"]
    pw, rh, pd = 760 * K, 58 * K, 34 * K; ph = 120 * K + rh * len(lines) + 26 * K + 70 * K
    ax, ay = (W * K - pw) / 2, (H * K - ph) / 2; bx, by = ax + pw, ay + ph
    if UI and UI.has("panel_wide"): UI.board(o, "panel_wide", (ax, ay), (bx, by), 44 * K); d = ImageDraw.Draw(o, "RGBA")
    else: d.rectangle((ax, ay, bx, by), fill=lin((0.035, 0.04, 0.055), 0.95), outline=lin((0.75, 0.65, 0.45), 0.9), width=2 * K)
    gold, dim = (1.0, 0.82, 0.35), (0.70, 0.68, 0.62)
    text_c(d, (W * K / 2, ay + 22 * K), "PAUSED", f_title, lin(INK), "mt", False)
    y = ay + 100 * K; plate = bool(UI and UI.has("button"))
    for i, ln in enumerate(lines):
        p_ = ln.split("|")
        if len(p_) < 2: continue
        on = i == cur
        if i == 4: y += 26 * K
        r0, r1 = (ax + pd, y), (bx - pd, y + rh - 10 * K)
        if on:
            if plate: UI.nine(o, "button", (r0[0] - 4 * K, r0[1] - 4 * K), (r1[0] + 4 * K, r1[1] + 4 * K), UI.height_px("button", r1[1] - r0[1] + 8 * K), (1.25, 1.05, 0.7, 1)); d = ImageDraw.Draw(o, "RGBA")
            else: d.rectangle((*r0, *r1), fill=lin((0.36, 0.27, 0.10), 0.95))
            d.rectangle((*r0, *r1), outline=lin(gold), width=2 * K)
        if p_[0] == "volume":
            v = vols[i] if i < len(vols) else float(p_[2])
            d.text((r0[0] + 14 * K, r0[1] + 12 * K), p_[1], font=f_line, fill=(255, 255, 255, 255) if on else lin((0.86, 0.84, 0.78)))
            t0, t1 = (r0[0] + 300 * K, (r0[1] + r1[1]) / 2 - 4 * K), (r1[0] - 90 * K, (r0[1] + r1[1]) / 2 + 4 * K)
            d.rectangle((*t0, *t1), fill=lin((0.08, 0.08, 0.10), 0.95)); d.rectangle((t0[0], t0[1], t0[0] + (t1[0] - t0[0]) * v, t1[1]), fill=lin((0.85, 0.62, 0.25)))
            d.rectangle((*t0, *t1), outline=lin((0.75, 0.65, 0.45), 0.9), width=K)
            kx = t0[0] + (t1[0] - t0[0]) * v; d.rectangle((kx - 7 * K, t0[1] - 9 * K, kx + 7 * K, t1[1] + 9 * K), fill=lin(gold if on else (0.85, 0.82, 0.75)))
            d.text((r1[0] - 14 * K, r0[1] + 13 * K), "%d%%" % round(v * 100), font=fl_small, fill=lin(gold if on else dim), anchor="ra")
        else:
            text_c(d, ((r0[0] + r1[0]) / 2, r0[1] + 11 * K), p_[1].upper(), ft_small, (255, 255, 255, 255) if on else lin((0.86, 0.84, 0.78)), "mt", False)
        y += rh
    text_c(d, (W * K / 2, by - 48 * K), "W S  choose      A D  volume      Enter  press      mouse  click or drag      Esc  back to the game", f_tiny, lin(dim), "mt", False)
    top.alpha_composite(o)
def spell_line(nm):
    s_ = SPELLS.get(nm)
    if not s_: return nm.lower()
    return "%s (%s): %s" % (nm, s_["type"], s_["effect"][:1].lower() + s_["effect"][1:])
def s5_caps():
    """(run5s) the captions of the spells, rings, monsters and menu reel, each from what the record says happened"""
    out = []; gold, warn = (255, 226, 150), (255, 200, 120)
    hj = HJ.get(HERO, {}); acc = tuple(int(255 * v) for v in hj.get("accent", (1.0, 0.94, 0.84)))
    learns = C.get("learns", []); rk = C.get("ring_kinds", [])
    RK = {"magic": "magic potency (+% mana)", "health": "hp potency (+% hit points)", "dexterity": "dexterity (+% ranged damage)"}
    t_end0 = (EMPTY0["t"] - 0.1) if EMPTY0 else 4.5
    out.append((0.8, max(t_end0, 3.6), "THE " + HNAME.upper(), [("she learns spells from tomes: " + ", ".join(learns)) if learns else "she learns no spells: a tome stays in her bag",
                "her rings: " + (" and ".join(RK.get(k, k) for k in rk) if rk else "none")], acc))
    if EMPTY0:
        e1 = EMPTY1["t"] if EMPTY1 else EMPTY0["t"] + 6.0
        out.append((EMPTY0["t"], e1 + 3.0, "F  ·  A %s THAT HOLDS NOTHING" % EMPTY0.get("ckind", "container").upper(),
                    ["one container in three holds anything (the test: 33.7% of 6,000); then 1 to 6 things as before",
                     "an empty one says so: \"Empty: nothing inside\"  ·  the great hall's chests always hold their tier's armour"], gold))
    for e in [x for x in CHESTS if not EMPTY1 or x["t"] > EMPTY1["t"] + 0.5]:
        fd = next((x for x in FOUND if x["t"] >= e["t"] - 0.05), None); held = fd.get("items", []) if fd else []
        out.append((e["t"] - 0.3, e["t"] + 2.6, "F  ·  A CHEST OF THE GREAT HALL", ["it held %d things: %s" % (len(held), ", ".join(x.lower() for x in held[:5])), "what comes in a container follows its tier: these are tier 1's"], gold))
    gr = [e for e in GIVEN if e.get("why") in ("ring", "breakdown")]; gt = [e for e in GIVEN if e.get("why") == "tomes"]
    if gr:
        nxt = gt[0]["t"] if gt else gr[-1]["t"] + 3.0
        rn = [k for e in gr for k in e["items"]]
        out.append((gr[0]["t"], nxt - 0.05, "THE REEL GIVES HER " + " AND ".join(x.upper() for x in rn),
                    ["rings are found in containers by tier, rarity 25: potency 1 and 2 in tier 1 ... 9 and 10 in tier 5 (+10% to +100%)",
                     "here one of tier 5's, to show its whole effect" + ("  ·  the two-handed sword: tier 1's, given for its new cuts" if any("Sword" in x for x in rn) else "")], warn))
    if gt:
        ln = [e for e in gt if e.get("learned")]; kept = [e for e in gt if not e.get("learned")]
        sp = [list(e["items"])[0][8:] for e in ln]
        e_ = INVS[0]["t"] if INVS else gt[-1]["t"] + 3.0
        out.append((gt[0]["t"], e_ - 0.05, "THE REEL GIVES HER %d TOME%s" % (len(gt), "S" if len(gt) > 1 else ""),
                    [("learned at once, each a weapon of hers now (keys 1 to 0): " + ", ".join(x.lower() for x in sp)) if sp else "she learns none of them",
                     ("kept in her bag, not learned: " + ", ".join(list(e["items"])[0][8:].lower() for e in kept) + ("  (she learns only " + " and ".join(learns) + ")" if learns else "")) if kept else
                     "a tome is found in a container (weight 25); its spell is drawn by the room's tier from the spells' mana"], warn))
    for e in INVS:
        u = next((x for x in USED if x["t"] >= e["t"]), None)
        if not u: continue
        cl = inv_closed_after(u["t"]); nxt = next((x["t"] for x in EV if x["t"] > u["t"] + 0.2 and x["kind"] in ("inventory", "fight", "lure", "craft_open", "menu", "jump")), cl + 5.0)
        if e.get("why") == "ring" and RING_ON:
            it = ITEMS.get(RING_ON["ring"], {}); l1 = []
            if RING_ON["hp"][1] != RING_ON["hp"][0]: l1.append("hit points %d to %d" % (RING_ON["hp"][0], RING_ON["hp"][1]))
            if RING_ON["mana"][1] != RING_ON["mana"][0]: l1.append("mana %d to %d" % (RING_ON["mana"][0], RING_ON["mana"][1]))
            if RING_ON.get("crossbow") and RING_ON["crossbow"][1] != RING_ON["crossbow"][0]: l1.append("a crossbow bolt %s to %s" % (nice(RING_ON["crossbow"][0]), nice(RING_ON["crossbow"][1])))
            out.append((e["t"], u["t"], "I  ·  RINGS", ["her rings are under their own heading; one of each kind is worn (rings of a kind do not add up)", "she goes down the list to the %s" % RING_ON["ring"].lower()], gold))
            out.append((u["t"], nxt - 0.05, "ENTER  ·  %s WORN  ·  +%d%%" % (RING_ON["ring"].upper(), round(it.get("amount", 0) * 100)), ["  ·  ".join(l1) or "worn",
                        "what she has goes up with it: a ring put on adds its part"], lin(CYAN)[:3]))
        elif e.get("why") == "refused":
            it = ITEMS.get(e.get("item", ""), {}); sp_ = it.get("spell", ""); s_ = SPELLS.get(sp_, {})
            out.append((cl, min(nxt - 0.05, cl + 4.0), "I  ·  ENTER  ·  " + u["message"].upper(), ["the %s teaches %s, a %s spell: the %s learns %s" % (e.get("item", "").lower(), sp_.lower(), s_.get("type", "?"), HERO.lower(),
                        ("only " + " and ".join(learns)) if learns else "none"), "it stays in her bag under TOMES THE %s CANNOT LEARN" % HERO.upper()], (255, 170, 130)))
    for e in [x for x in INVS if x.get("why") == "wield"]:
        u = next((x for x in USED if x["t"] >= e["t"]), None)
        if not u: continue
        cl = inv_closed_after(u["t"]); nm = e.get("weapon", ""); wd = next((w_ for w_ in weapons_at(u["t"] + 0.1) if w_["name"] == nm), {})
        out.append((cl, cl + 5.5, "I  ·  ENTER  ·  " + nm.upper(), ["a two-handed sword: speed %d / 10, damage %d / 10, %s a blow" % (wd.get("speed", 0), wd.get("rating", 0), nice(wd.get("damage", 0))),
                    "her two-handed cuts made again in Blender: the forearms kept out of her body (they went 4-10 cm in; now 1.5 cm at most)"], gold))
    for i, e in enumerate(FIGHTS):
        end = next((k["t"] for k in KILLS if k["t"] > e["t"]), e["t"] + 6.0) + 1.0
        if i + 1 < len(FIGHTS): end = min(end, FIGHTS[i + 1]["t"] - 0.1)
        tr = tier_of(e["section"]); title = e.get("title") or e["monster"].replace("_", " ")
        # (the spells cast in it: bolts are casts of her spell weapons, the rest released spells)
        sps = [x[1] for x in sorted([(x["t"], x["weapon"]) for x in CASTS if e["t"] - 0.2 <= x["t"] <= end and x.get("weapon") in SPELLS] +
                                    [(x["t"], x["name"]) for x in SPELL_EV if e["t"] - 0.2 <= x["t"] <= end])]
        l1 = "%.0f hit points, %.0f damage a blow  ·  she has %.0f" % (e["its_hit_points"], e["its_damage"], row(int(e["t"] * FPS))["mhp"])
        if sps:
            uniq = list(dict.fromkeys(sps))
            l2 = "her spells: " + ",  ".join("%s %s" % (x.lower(), nice(SPELLS.get(x, {}).get("damage", 0)) if SPELLS.get(x, {}).get("damage") else "") for x in uniq).replace(" ,", ",")
            l3 = "  ·  ".join(spell_line(x) for x in uniq[:2] if SPELLS.get(x, {}).get("kind") not in ("bolt",)) or "each spell: its own effects from the Magic Projectiles, Toon Explosions and Stylized Shields packs"
        else:
            wd = next((w_ for w_ in weapons_at(e["t"] + 0.05) if w_["name"] == e.get("weapon")), None) or {}
            l2 = "in her hands: the %s, %s a %s" % ((e.get("weapon") or "").lower(), nice(e.get("damage", wd.get("damage", 0)) or 0), "shot" if wd.get("ranged") else "blow")
            l3 = "monsters of tier %d: the gallery's of that tier, in their own colours; hit points and blows grow with the tier" % tr
        if e.get("ability") and e["ability"] not in ("NONE", "None") and tr >= 3:
            l3 = "its blows carry %s (tier 3 and up): %s" % (e["ability"].lower(), {"POISON": "poison eats her hit points", "WEAKEN": "her blows lose a share", "SLOW": "she moves slower"}.get(e["ability"], ""))
        if lured(e): l3 = lured(e)
        out.append((e["t"], end, "%s  ·  TIER %d" % (title.upper(), tr), [l1, l2, l3], gold))
    for e in CORPSE[:1]:
        out.append((e["t"], e["t"] + 3.0, "THE DEAD STAY", ["a monster killed lies where it fell, still, for good: it no longer sinks away",
                    "a set of rooms generated again lays its dead where they lay  ·  Raise Dead and Corpse Explosion use them"], (220, 220, 230)))
    if RAISE:
        al = ev1("allies")
        nr = RAISE.get("raised") or (al["n"] if al else 1)
        out.append((RAISE["t"], RAISE["t"] + 5.5, "RAISE DEAD  ·  %d MANA" % SPELLS.get("Raise Dead", {}).get("mana", 0), [("%d of the dead near her rise where they fell" % nr if nr > 1 else "the %s rises from where it fell" % (RAISE.get("title") or RAISE.get("monster", "")).lower()) +
                    ": her allies for %d s (green bars)" % SPELLS.get("Raise Dead", {}).get("duration", 0),
                    "it fights the monsters at her side  ·  an ally's kills are not counted as hers"], (160, 255, 170)))
    if BROKEN:
        co = ev1("craft_open")
        if co: out.append((co["t"], BROKEN["t"], "F  ·  THE ANVIL  ·  BREAK DOWN", ["under the recipes: the weapons she found, each to break down into materials by its type",
                           "she goes down to the %s" % BROKEN["weapon"].lower()], gold))
        new = [x for x in BROKEN.get("components", []) if x not in BROKEN.get("before", [])]
        out.append((BROKEN["t"], BROKEN["t"] + 3.4, "ENTER  ·  THE %s BROKEN DOWN" % BROKEN["weapon"].upper(), [BROKEN.get("message", ""),
                    "blades give steel, iron and leather strips; bows timber, glue and rope; crossbows hardwood, steel and epoxy: for repair items"], lin(CYAN)[:3]))
    mo = [e for e in MENU_EV if e.get("open")]
    if mo:
        mc = next((e["t"] for e in MENU_EV if not e.get("open") and e["t"] > mo[0]["t"]), mo[0]["t"] + 8.0)
        v0 = VOLS[0] if VOLS else None
        out.append((mo[0]["t"], (v0["t"] - 0.6) if v0 else mc, "ESC  ·  THE MENU", ["in play it pauses the game (for the reel the world goes on); in the editor Esc reaches the game: the editor's stop is Shift+Esc",
                    "four volumes: overall, action sounds, environment sounds, music  ·  back to the hero choice  ·  quit"], gold))
        if v0:
            out.append((v0["t"] - 0.6, mc + 0.5, "A D  ·  THE MUSIC  %d%%" % round(v0["value"] * 100), ["the music falls with its slider in the game's own mix (the reel's sound)  ·  the test: environment at 50%, a torch 6.1 dB quieter",
                        "then back to 100%; the volumes are kept for the next session"], gold))
    if LANDED:
        out_t = LANDED["t"] + 3.0
        out.append((out_t, out_t + 4.5, "A SET OF TIER 3", ["for the reel she was put here behind the card: her hit points and mana full again",
                    "%s  ·  %.0f hit points, %.0f a blow" % ((LANDED.get("title") or LANDED.get("monster", "")).upper(), LANDED.get("its_hit_points", 0), LANDED.get("its_damage", 0)) +
                    (("  ·  its blows carry %s" % LANDED["ability"].lower()) if LANDED.get("ability") not in (None, "NONE") else "")], gold))
    # (an affliction on her: the first time a monster's ability takes hold)
    bad = next(((f / FPS, x) for f in sorted(ROWS) for x in ROWS[f].get("buffs", []) if x.split("|")[-1] == "0"), None)
    if bad:
        nm = bad[1].split("|")[0]
        out.append((bad[0], bad[0] + 4.0, nm, ["a tier-3 monster's blow: %s" % {"POI": "poison eats her hit points every second", "WEA": "her blows lose a share", "SLO": "she moves slower"}.get(nm[:3], nm.lower()),
                    "a chip over her panel with the seconds left  ·  Dispel Hex (protection) ends it"], (255, 150, 120)))
    for e in [x for x in EV if x["kind"] == "map" and x.get("open")]:
        e1 = next((x["t"] for x in EV if x["kind"] == "map" and not x.get("open") and x["t"] > e["t"]), e["t"] + 3.6)
        out.append((e["t"], e1, "M  ·  THE BIG MAP", ["the rooms of this set are written TIER 3; the great hall's set, far to the west, tier 1",
                    "its monsters are few and far apart: she sets out for the next one"], gold))
    me = next((x for x in SPELL_EV if x["name"] == "Meteor Storm"), None)
    if me:
        out.append((me["t"], me["t"] + 5.0, "METEOR STORM  ·  %d MANA" % SPELLS["Meteor Storm"]["mana"], ["meteors fall on the area for %d s; with the ring her 200 mana is just enough" % SPELLS["Meteor Storm"]["duration"],
                    "cooldown %d s: the slot darkens from the top and counts down" % SPELLS["Meteor Storm"]["cooldown"]], (255, 180, 120)))
    return out
S5CAPS = None
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
        # (level 5: the gallery's name; cursed, slowed or burning: a mark after it)
        nm_ = (mo[13] if len(mo) > 13 and mo[13] else mo[1].replace("_", " ")).upper()
        mk_ = "".join(s_ for s_, on_ in (("  CURSED", len(mo) > 14 and mo[14]), ("  SLOWED", len(mo) > 15 and mo[15]), ("  BURNING", len(mo) > 16 and mo[16])) if on_)
        text_c(d, (s[0], y0 - 4 * K), sc("%s  %.0f%s" % (nm_, mo[5], mk_)), fl_small, lin(INK, A(1.0)), "mb")
    # ---- level 5: her allies (green bars, the time they have left)
    for al in r.get("ally", []):
        s = project(r, (al[1], al[2], al[3] + al[6] + 34.0))
        if not s or not (0 < s[0] < W * K and 0 < s[1] < H * K): continue
        bw, bh, fr = 96 * K, 8 * K, al[4] / max(al[5], 1.0); x0, y0 = s[0] - bw / 2, s[1] - bh
        d.rectangle((x0 - 2, y0 - 2, x0 + bw + 2, y0 + bh + 2), fill=lin((0.02, 0.02, 0.02), A(0.8)))
        d.rectangle((x0, y0, x0 + bw * fr, y0 + bh), fill=lin((0.25, 0.85, 0.35), A(1.0)))
        text_c(d, (s[0], y0 - 4 * K), sc(("ALLY  %s  %ds" % (al[0].upper(), math.ceil(al[7]))) if al[7] > 0 else "ALLY  %s" % al[0].upper()), fl_small, lin((0.6, 1.0, 0.65), A(1.0)), "mb")
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
        # (level 5: her spells on her and the monsters' afflictions: a row of chips above the potions')
        if r.get("buffs"): buff_chips(o, d, bx, ay - 8 * K - up - (40 * K if ex < bx else 0), ua, r["buffs"])
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
            # (two lines start under the key's word: at 19 the Summoner's "wheel" ran into "SUMMON TIER 3"; ARDHUD the same)
            d.text(((sx0 + sx1) / 2, sy0 + ((24 + 13 * li) if len(nl) > 1 else 26) * K), sc(x), font=fn_, fill=tc, anchor="mm")
        dmg = ("%.0f damage  ·  %.0f mana" % (wd["damage"], wd["mana"])) if wd.get("mana") else ("%.1f damage" % wd["damage"] if abs(wd["damage"] - round(wd["damage"])) > 0.05 else "%.0f damage" % wd["damage"])
        if dur: dmg = ("%.0f" % wd["damage"]) + "  ·  " + dur if total_w > 3 else dmg + "  ·  " + dur
        fd_ = f_tiny; wdm = d.textlength(dmg, font=f_tiny)
        if LETTERS and wdm > sw - 8 * K: fd_ = fit_font("Alegreya-500", 15.5, max(0.6, (sw - 8 * K) / wdm))
        d.text(((sx0 + sx1) / 2, sy0 + (55 if len(nl) > 1 else 48) * K), dmg, font=fd_, fill=lin((1.0, 0.9, 0.6), A(1.0)) if on else tc, anchor="mm")
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
    menu_open = S5 and r.get("menu", [0])[0] == 1; craft_open = r.get("craft", [0])[0] == 1
    if S5:
        # (run5s: the number keys draw a weapon or ready a spell; Esc opens the menu)
        dig = kh if (len(kh) == 1 and kh.isdigit()) else ""
        caps = [("W", mv != "" or kh == "w"), ("A", kh == "a"), ("S", kh == "s"), ("D", kh == "d"), ("SHIFT", mv == "run"), (dig or "1-0", bool(dig))]
        caps += [("E", kh == "e")] if HERO == "Mage" else [("LMB", kh == "lmb")] + ([("E", kh == "e")] if HERO == "Warlock" else [])
        caps += [("I", kh == "i" or inv_open)] + ([("ENTER", kh == "enter")] if (inv_open or craft_open or menu_open) else []) + [("F", kh == "f" or craft_open), ("ESC", kh == "esc" or menu_open)]
    if MW2:
        # (run5m2: the quick slots' 1 - 0, the Warrior's block (RMB) and helmet (H), the inventory's tabs (Q / E))
        dig = kh if (len(kh) == 1 and kh.isdigit()) else ""
        caps = [("W", mv != "" or kh == "w"), ("A", False), ("S", kh == "s"), ("D", False), ("SHIFT", mv == "run"), (dig or "1-0", bool(dig))]
        caps += [("E", kh == "e")] if HERO == "Mage" else [("LMB", kh == "lmb")] + ([("RMB", kh == "rmb" or r.get("blk", 0) == 1)] if HERO == "Warrior" else [])
        caps += [("I", kh == "i" or inv_open)] + ([("Q", kh == "q_tab"), ("E", kh == "e_tab"), ("ENTER", kh == "enter")] if inv_open else [])
        caps += [("F", kh == "f")] + ([("H", kh == "h")] if HERO == "Warrior" else []) + [("M", kh == "m" or mapo)]
    kw = {"SHIFT": 112, "LMB": 76, "RMB": 76, "ENTER": 100, "ESC": 76, "1-0": 64}; gap = 8 * K; total = sum(kw.get(c, 52) * K for c, _ in caps) + gap * (len(caps) - 1) + 24 * K
    kx = bx - 16 * K - total; ky = ay - 100 * K - (up + 6 * K if ext else 0)     # (above the effect chips)
    d.rounded_rectangle((kx - 14 * K, ky - 52 * K, kx + total + 14 * K, ky + 64 * K), 14 * K, fill=(12, 11, 9, int(150 * ua)))
    k0x = kx
    for i, (c, on) in enumerate(caps):
        w_ = kw.get(c, 52) * K
        if c == "SHIFT": kx += 24 * K
        d.rounded_rectangle((kx, ky, kx + w_, ky + 52 * K), 9 * K, fill=(238, 214, 150, int(255 * ua)) if on else (60, 58, 54, int(220 * ua)), outline=(255, 236, 180, int(255 * ua)) if on else (120, 112, 98, int(200 * ua)), width=2 * K)
        d.text((kx + w_ / 2, ky + 26 * K), c, font=ft_small if c in ("SHIFT", "LMB", "RMB", "ENTER", "ESC", "1-0") else f_head, fill=(28, 24, 18, int(255 * ua)) if on else (210, 204, 190, int(230 * ua)), anchor="mm")
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
    if S5:
        wl_ = weapons_at(t)
        if kh in ("e", "lmb"):
            ai = r.get("atki", -1); ai = ai if 0 <= ai < len(wl_) else r["w"]
            wn_ = wl_[ai] if 0 <= ai < len(wl_) else None
            if wn_ and wn_.get("spell") and not wn_.get("ranged"): lab = "cast " + wn_["name"]
        elif len(kh) == 1 and kh.isdigit():
            i_ = (int(kh) - 1) % 10
            if i_ < len(wl_): lab = ("ready " + wl_[i_]["name"]) if (wl_[i_].get("spell") and not wl_[i_].get("ranged")) else "draw the " + wl_[i_]["name"].lower()
        elif kh == "esc": lab = "open the menu" if menu_open else "close the menu"
        elif menu_open and kh in ("a", "d", "s", "w"): lab = {"a": "volume down", "d": "volume up", "s": "down the menu", "w": "up the menu"}[kh]
        elif craft_open and kh == "enter": lab = "break it down"
        elif craft_open and kh == "s": lab = "down the list"
    if MW2:
        qs_ = r.get("qs", [])
        if len(kh) == 1 and kh.isdigit():
            i_ = (int(kh) - 1) % 10; nm_ = qs_[i_] if i_ < len(qs_) else ""
            lab = ("into quick slot %s" % kh) if inv_open else (("draw the " + nm_.lower()) if nm_ not in ("", "None") else "an empty quick slot")
        elif kh == "rmb": lab = "block with the shield"
        elif kh == "e_tab": lab = "the next tab"
        elif kh == "q_tab": lab = "the tab before"
        elif kh == "h": lab = "hide or show the helmet"
    if lab: text_c(d, ((k0x + kx) / 2, ky - 24 * K), lab, f_line, (244, 240, 228, int(240 * ua)))
    # ---- the banner when a section is generated (the weapons reel: not the sets the reel made behind its card)
    for e in GENS:
        age = t - e["t"]
        if W5 and JUMP and AT_GRATING and JUMP["t"] - 0.1 <= e["t"] <= AT_GRATING["t"] + 0.5: continue
        if K5 and CARD and CARD[0] - 0.1 <= e["t"] <= CARD[1] + 0.5: continue
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
    # (run5s: the hotbar; Esc's menu over the HUD, the reel's captions over it)
    if (S5 or MW2) and not mapo and not r.get("inv", [0])[0] and not r.get("craft", [0])[0]: hotbar(o, r, t, ua); d = ImageDraw.Draw(o, "RGBA")
    if S5 and r.get("menu", [0])[0]: menu_panel(o, r, t, ua); d = ImageDraw.Draw(o, "RGBA")
    # ---- the reel's own: title, captions (bottom left)
    a = fade(t, 0.3, 4.6)
    if a > 0 and M5:
        d.text((44 * K, 50 * K), "mistward_castle", font=f_title, fill=(255, 255, 255, int(235 * a)), stroke_width=2 * K, stroke_fill=(0, 0, 0, int(140 * a)))
        d.text((46 * K, 94 * K), "Mistward Castle  \u00b7  the %s, chosen in the menu  \u00b7  %s" % (HNAME.lower(), ({"Warrior": "tiers 1 and 2: sword and shield, a harvest, new terrain", "Mage": "tier 3: her spells, a scroll", "Warlock": "tier 2: curse, lash and sword",
               "Rogue": "tier 3: crossbow, daggers, the roll", "MartialArtist": "tier 4: her chi attacks", "Summoner": "tiers 1 and 5: her summoned fighters"} if MW4 else {"Warrior": "her start gear, an armory's table, quick slots, the block, a boss's slash, the helmet",
               "Mage": "the inventory's tabs, a shrine, fountains of mana and healing", "Warlock": "the vault and its key, a fountain of speed, the arena",
               "Rogue": "a seen trap outlined in red, the trap gauntlet, the throne room", "MartialArtist": "her chi attacks' looks, a quick bar of any length, her abilities on it"} if MW2 else {"Warrior": "shields, the anvil, a boss", "Mage": "the torch, the prison's cells",
               "Warlock": "rooms of other shapes, teleporters, her things where she falls", "Rogue": "traps, a guarded ring"})[HERO]), font=f_sub, fill=(232, 236, 240, int(225 * a)), stroke_width=2 * K, stroke_fill=(0, 0, 0, int(140 * a)))
    elif a > 0:
        d.text((44 * K, 34 * K), "random_dungeonmagic_level" + ("" if LV == "1" else LV), font=f_title, fill=(255, 255, 255, int(235 * a)), stroke_width=2 * K, stroke_fill=(0, 0, 0, int(140 * a)))
        d.text((46 * K, 86 * K), ("procedural dungeon  \u00b7  the %s, chosen in the menu  \u00b7  spells from tomes, rings, monsters by tier, the dead stay, the menu" % HERO.lower() if S5 else
                                  "procedural dungeon  \u00b7  the %s, chosen in the menu  \u00b7  the map, chests, armour, the anvil, fights, new rooms tier by tier" % HERO.lower() if X5 else
                 "procedural dungeon  \u00b7  the %s, chosen in the menu  \u00b7  armour by its table, loot by tier, repair items made at anvils" % HERO.lower() if C5 else
                                  "procedural dungeon  \u00b7  the %s, chosen in the menu  \u00b7  %s" % (HNAME.lower(), WHO[HERO].replace("the %s " % HERO, "she ", 1)) if Q5 else
                                  "procedural dungeon  \u00b7  the warrior, chosen in the menu  \u00b7  a weapons table and five tiers of rooms" if W5 else
                                  "procedural dungeon  \u00b7  the summoner, chosen in the menu  \u00b7  five armour sets to find and wear" if L5 else
                                  ("procedural dungeon  \u00b7  the %s, chosen in the menu  \u00b7  %s" % (HNAME.lower(), HJ[HERO]["starts_with"].lower())) if L4 else
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
        caps.append((0.8, (INVS[0]["t"] if INVS else 30.0) if L5 else min(t_first - 0.2, t_chest - 0.4, (GENS[0]["t"] if GENS else 99) - 0.2), "THE " + HNAME.upper(), ["  ·  ".join(hj["abilities"]),
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
    if S5:
        global S5CAPS
        if S5CAPS is None: S5CAPS = s5_caps()
        caps = S5CAPS
    if M5:
        global M5CAPS
        if M5CAPS is None: M5CAPS = mw4_caps() if MW4 else mw2_caps() if MW2 else m5_caps()
        caps = M5CAPS
    lift = 96 if (S5 or MW2) else 0          # (run5s, run5m2: the captions and the heard lines above the hotbar)
    # (one caption at a time, in the one place: the one that began last; an earlier one still running shows again after it)
    live = [cp for cp in caps if fade(t, cp[0], cp[1]) > 0]
    for t0, t1, head, lines, c in ([max(live, key=lambda cp: cp[0])] if live else []):
        k = fade(t, t0, t1)
        if k <= 0: continue
        dn = 44 if (K5 and mapo) else 0           # (run5c: under the big map's key while the map is open)
        y = (H - 62 - 36 - 34 * len(lines) + dn - lift) * K
        wd = max([d.textlength(head, font=f_head)] + [d.textlength(s, font=f_line) for s in lines])
        blend_box(o, (32 * K, y - 14 * K, 60 * K + wd, (H - 48 + dn * 0.7 - lift) * K), 12 * K, (12, 11, 9, int(180 * k))); d = ImageDraw.Draw(o, "RGBA")
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
    y = (H - 252 - lift) * K
    for s, k in reversed(lines[-4:]):
        if k <= 0: continue
        tw = d.textlength(s, font=f_line)
        blend_box(o, (32 * K, y - 19 * K, 96 * K + tw, y + 19 * K), 10 * K, (12, 11, 9, int(150 * k))); d = ImageDraw.Draw(o, "RGBA")
        d.text((48 * K, y), "\u266a", font=f_note, fill=(150, 220, 255, int(255 * k)), anchor="lm"); d.text((80 * K, y), s, font=f_line, fill=(236, 240, 244, int(245 * k)), anchor="lm")
        y -= 44 * K
    if M5: d = mw_hud(o, d, r, t, ua, mapo)
    if L4: l4_panels(o, r, t, ua); d = ImageDraw.Draw(o, "RGBA")
    if M5:
        cd = last_at(CARDS, t)
        if cd and cd["t"] - 0.35 <= t <= cd["t"] + MW_CARD + 0.5:
            k = max(0.0, min(1.0, (t - cd["t"] + 0.35) / 0.35, (cd["t"] + MW_CARD + 0.5 - t) / 0.5))
            d.rectangle((0, 0, W * K, H * K), fill=(4, 4, 6, int(255 * k)))
            text_c(d, (W * K / 2, H * K * 0.40), cd["text"], f_title, (255, 214, 140, int(255 * k)))
            if cd.get("sub"): text_c(d, (W * K / 2, H * K * 0.40 + 90 * K), cd["sub"], f_line, (236, 236, 240, int(235 * k)))
    if W5 and not M5 and CARD and CARD[0] - 0.35 <= t <= CARD[1] + 0.5:
        # (the card over the reel's shortcut: what the generator's debug clear did, said as it is)
        k = max(0.0, min(1.0, (t - CARD[0] + 0.35) / 0.35, (CARD[1] + 0.5 - t) / 0.5))
        d.rectangle((0, 0, W * K, H * K), fill=(4, 4, 6, int(255 * k)))
        text_c(d, (W * K / 2, H * K * 0.36), "TIER 3" if S5 else "TIER 2", f_title, (255, 214, 140, int(255 * k)))
        for i, s_ in enumerate(["the eight sets round the great hall's set: tier 2",
                                "for the reel she is put in one of them, generated as she arrives",
                                "its rooms are written TIER 2 on the maps"] if (C5 and not X5) else
                               ["the sixteen sets round tier 2: tier 3, open once every set of tiers 1 and 2 is cleared",
                                "for the reel she is put in one of them, generated as she arrives, with her hit points and mana full",
                                "its monsters are tier 3's: stronger, and their blows carry poison, weakness or slowness"] if S5 else
                               ["tier 2 opens once the start set is cleared, tier 3 once all of tier 2's eight sets are: every room, chest and monster",
                                "for the reel the generator's debug clear does the start set, seven of tier 2's and all but one monster of the eighth",
                                "she stands in the eighth, at a grating into tier 3"] if X5 else
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
    if RESUME and os.path.exists(os.path.join(dst, f"rdm{'' if LV == '1' else LV}{'mw2' if MW2 else ''}{HERO.lower() if L4 else ''}hud.{i:04d}.png")): continue
    im = Image.open(p).convert("RGBA")
    if im.size != (W, H): im = im.resize((W, H), Image.LANCZOS)
    Image.alpha_composite(im, overlay(i)).convert("RGB").save(os.path.join(dst, f"rdm{'' if LV == '1' else LV}{'mw2' if MW2 else ''}{HERO.lower() if L4 else ''}hud.{i:04d}.png"), compress_level=1)
print("wrote", len(range(0, len(frames), step)), "frames to", dst)
