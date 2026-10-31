"""random_dungeonmagic_level, random_dungeonmagic_level2 and random_dungeonmagic_level3 demo reel: the pilot and the recorder
(generalised from 795; the level is the one the render or PIE plays). Plays the caster (girl-caster-tripo; level 2: the dark caster,
girl-darkcaster-tripo, with a sword in her right hand and fire from her left) through the dungeon with the calls the keys make (movement input at her walk or run speed, the
combat component's cast, the generator's F on doors and chests), turns the game's own third-person camera, and records
the play for the overlay (pipeline/blender_numpy/rdm_reel_overlay.py: the Movie Render Queue does not draw the HUD). The
record holds every sound the game played, every blood burst, every bolt in the air, the chests and doors she opened, the
music changes.
  render    (default) arm it right before 816: it waits for the render's world and LS_RDM_Showcase and starts with frame 0
  rehearse  the PIE session that is running now, in real time (the HUD is on)
On the first frame the dungeon is put back to its start (ARDDungeonGenerator.RestartPlay with a fixed session seed, so
the section generated during the reel is the same every time) and she is set down on the way to the east edge of the
start section, a few metres from a chest by that way. She walks to the chest and opens it, runs to the nearest monster
and burns it down with the fire spell from range, runs east (opening the doors in her way), crosses the line where the
next section is generated, runs into the new section, fights what is there and opens a chest there if there is time.
In level 2 a fight is fire and steel: two bolts from range, then she closes in and finishes it with the sword (a monster
that comes at her first meets the sword).
In level 3 (the Rogue) a fight is the crossbow and the daggers: up to two bolts from range (2 draws it), then the daggers
(1) and she closes in and stabs; when the monster swings at her up close she rolls back out of it (B), twice a fight at
most. The record then also has her rolls, the blows that missed her in a roll, and what the tactical minimap marks
(chests and trunks not looted yet, the hallway exits toward sections she has not seen, the strongest monsters).
In level 4 (the choice of hero) the hero is an argument and the pilot puts her in place of the level's default one
(ARDDungeonGenerator.SwitchHero, while the render warms up); she fights as in her own level (the Warrior closes in with
the sword; the Mage casts, dark fire first; the Warlock and the Rogue as in levels 2 and 3), goes the way the argument
says (east, north, west or south: the hallway leaving that edge of the start section, the next section that way), with
a session seed of her own, opens the containers she passes as the Rogue does (what each held goes into her inventory),
and after her first fight opens the inventory and uses what helps her (a healing potion or food when she is hurt, a
mana potion when her mana is down, else the next weapon). After that she opens the big map (M) for 4 s and walks on
under it (a fight closes it). The inventory does not pause the game in the reel (the
combat component's bInventoryPausesGame): the Movie Render Queue renders a world that goes on. The record then also
has her mana, the potions and food on her, what she found, the inventory as it was shown and what it said, and whether
the big map is open. The level is rendered without ?Hero=: the pilot sets rd.HeroMenu 0 when it is armed (else the
level would open its menu) and 1 again when it stops.
In level 5 (the Summoner and the armour, run5) the level 4 machinery records, and the plan is the armour's: she opens
the great hall's containers (up to six things each; the five armour sets are in them), then in the inventory puts on
each set in turn (I, S / W down and up the list to it, Enter, I), and after each the camera goes round her while she
stands, to show it on her; last she goes back to the plate armour and lets the nearest monster of the start section
come at her before she burns it down (its blows land on the plate: the record has each blow before her armour and what
reached her). The record also has the set she wears and every container's whole list.
Level 5 with the way "weapons" (the weapons and tiers reel, run5w; the hero the Warrior, who wields every weapon of the table;
a session seed whose great hall chests hold a two-handed sword and a bow): she opens the hall's chests that hold weapons,
wields the two-handed sword from the inventory (the camera round her) and fights with it, then the bow from range; a
found blade started at 3 of its durability breaks on her third hit. Then, behind a card ("jump"), the reel's shortcut:
tier 2's eight sets generated, seven cleared outright and the eighth all but the monster nearest its grating into tier 3
(the generator's DebugClearSection); she walks up to the grating (its prompt), kills that monster ("TIER 3 IS OPEN": the
gratings go) and walks on through into tier 3, which is generated ahead of her. The record also has her weapons as they
change (found, worn, broken), the tier panel's numbers, a seal's prompt near her, the tiers' notices, the sealed passages.
Level 5 with the way "heroes" (the four heroes' weapons reel, run5h; Warrior, Mage, Warlock or Rogue, every one with the
same session seed, so the great hall's chests hold the same weapons for each and the rules of who wields what show): the
hall's chests with weapons as in run5w, then her own part (who wears what: 856; the chests also hold the plate armour,
the orc veteran's (both heavy) and the tiefling's (light)): the Warrior puts on the plate armour (she wears all), wields
the two-handed sword and the bow and kills with each in it; the Mage wields none of the table's weapons (Enter on the
sword: refused) and wears no armour (refused), fights with her spells and drinks a mana potion; the Warlock is refused the
plate armour (heavy: she wears light and medium), puts on the tiefling's, wields a found short sword started at 3 of its
durability and fights until it breaks; the Rogue (short blades and ranged weapons only, light armour only) is refused the
two-handed sword and the plate armour, puts on the tiefling's, wields the found dagger and kills with it, then the bow,
and takes the tiers' part of run5w (its last 24 s). The record also has, for each item, the heroes it fits. For her fights (not the chests, the inventory or
the tiers' part) the monsters notice her from REEL_AGGRO cm instead of the game's AggroDistance (the "lure" event says
so; put back after): the great hall's nearest monsters are 35 to 57 m off by the way, and the renders showed her running
empty hallways after them for the rest of her run; lured, they come to her in the hall.
Level 5 with the way "craft" (the armour table, loot and crafting reel, run5c; Warrior, Mage, Warlock or Rogue, the same
session seed for each): she starts in the great hall by its anvil; the big map shows each room's tier and the anvil; she
opens the hall's containers that hold the set her hero wears (the tier-1 sets: the Templar's for the Warrior, the Eastern
Knight's for the Warlock, the Desert Hero's for the Rogue; the Mage is refused it) and one more, puts the set on (its
ratings, durability and the speed it costs), fights (lured), and the reel wears the set down (the Warrior's to 0: worn
out, half its share; the others' to 60: the "wear_set" event, said by the caption); at the anvil (F) the crafting panel,
down to her recipe (the Warrior a patch kit, the Warlock a whetstone, the Rogue a slickstone, the Mage leather strips),
the reel gives her what it lacks ("given", said by the caption), she makes it, then in the inventory mends the set with
it (Enter, the repair list, Enter; the Mage: nothing to mend). Behind a card ("jump"), a room of a tier-2 set of rooms:
the minimap and the big map write tier 2. The record also has the crafting panel's and the repair list's lines, her
armour's durability and slowing, the anvils on the maps.
Level 5 with the way "spells" (the spells, rings, monsters by tier, corpses and menu reel, run5s; Warrior, Mage, Warlock or
Rogue, the same session seed for each): she starts in the great hall by its anvil; the reel gives her a ring of tier 5 (her
hero's kind: hit points for the Warrior, mana for the Mage and the Warlock, ranged damage for the Rogue) and tomes (S5_WANT:
a tome she can learn is learned as she takes it, one she cannot says so); the ring on from the inventory; the Warrior also
a two-handed sword and a Viking shortsword, which she breaks down at the anvil (F, the panel's BREAK DOWN part); a container
of the start section that holds nothing (it says so); fights, lured, until 24 s before the end (the Warrior with the
two-handed sword, then Esc's menu: the music slider down to 40 % and up again (the volumes put back as they were, the
menu saves them); the Mage a ward, frost, lightning and fire, then Raise Dead by a corpse and a fight beside the raised;
the Warlock a curse and her sword, then Shadow Lash; the Rogue the crossbow with the ring); the camera turns to a corpse
left where it fell; behind a card a tier-3 set (S5_ABILITY: by a monster whose blows carry slowness, weakness or poison;
the Mage by the one with most others round it, for Meteor Storm), her hit points and mana full, the monster's first two
blows let land (what they carry shows) before she fights; its corpse; the big map; on to the next monster however far.
The menu does not pause the game in the reel (bMenuPausesGame off until the pilot stops). The record also has each
monster's gallery name and marks (cursed, slowed, burning), her allies, her spells' cooldowns, her buffs and afflictions,
the menu's lines, cursor and volumes, the spells released, the spell table.
Writes SourceArt/random_dungeon_magic[2|3]/cine_render.json (level 4: random_dungeon_magic4/cine_<hero>.json; level 5:
random_dungeon_magic5/cine_summoner.json, the way "heroes" cine_quartet_<hero>.json, "craft" cine_craft_<hero>.json,
"spells" cine_spells_<hero>.json; rehearse: cine_rehearsal.json, "spells" cine_rehearsal_spells_<hero>.json) and
logs "RDMREEL saved".
Keeps its namespace (tick callback); a pilot left armed by an earlier run is dropped.
In real time (rehearse) the monsters come at her differently every run; the queue repeats a run exactly. A fight is left
for the next monster when its monster keeps away (3 s no nearer, or 10 m off after 8 s), and turned on another that is on
her and nearer; the weapons reel's tiers part keeps its last 24 s.
Level 5 with the way "grip" (the two-handed grip close up, run5g; the Warrior): she stands in the great hall's middle,
facing the way with most room, with the Plate Knight's Sword (given, then drawn); the game's camera, its boom shortened to
165 cm, aimed 38 cm higher and its view narrowed to 40 degrees, looks at her from the front; her three two-handed cuts
(W5_TwoHand1-3) at full speed, then the same three at a third of the speed (her own time dilation: the world's does not
slow a Movie Render Queue render);
the monsters near her are moved off and leave her be. Writes cine_grip_<hero>.json.
mistward_castle (level "mw", the way "mistward": run5m; the user's list of 2026-10-26, docs/improvements.txt), each hero with a
session seed of her own: the Warrior opens a great hall chest that holds a shield (it stays open; F again does nothing),
puts the shield on from the inventory, breaks down her Heater Shield at the anvil (its lists in alphabetical order), lets two
blows land on the shield in a fight; then (a card: the reel's shortcut, the start set cleared by the generator but a fifth
of its monsters) tier 1 at 50 % opens tier 2, a boss waits in a room she has seen (the big map's mark), and she fights it.
The Mage is given the torch's materials and a bag of others (said), holds S in the inventory (the list walks), makes the
torch at the anvil and lights it; then (a card) in tier 2's castle keep she sets a prisoner free (F at the cell door: thanks,
a thing, the prisoner walks off) and a caged monster breaks out as she comes near. The Warlock is shown rooms of other shapes
in the start set (cards: a dome, a stepped pyramid, a round room), then (a card) tier 2's first set's teleporter: F takes its
ring, the ring used carries her to the great hall's pad, F there back; a fight she loses (the reel takes her hit points
down, said): her things in a pile where she fell (their pictures, the Loot Drops effect), back on her feet; (a card) F at the
pile takes them up. The Rogue sees a trap from 8 m, disarms it (F), walks onto another (said); then (a card) tier 1 at 50 %:
the magic potency ring she never found lies guarded in a room she has seen (the big map), the guards fought, the ring taken.
The record also has the frame rate the game shows, her shield (worn, in her hand), the torch, what F would do near her, the
disarm bar, the castle's map marks (a boss, a guarded ring, her things, a teleporter, a trap she has seen), each room's
shape (the map's masks) and the traps, teleports, prisoners and deaths as events. Writes SourceArt/mistward/cine_mw_<hero>.json.
Args: [render|rehearse] [seconds] [level: "2", "3", "4", "5" or "mw"] [level 4: hero] [level 4: east|north|west|south; level 5:
weapons, heroes, craft, spells or grip; mw: mistward] [session seed]"""
import unreal, sys, json, math, os
__keep__ = True
MODE = sys.argv[1] if len(sys.argv) > 1 else "render"
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 45.0
FPS = 30; SEED = 20261015
CAST_GAP = 950.0            # she stops this far (cm, to the monster's capsule) and casts
_lv = "1"
for _w in unreal.ObjectIterator(unreal.World):
    for _n in ("2", "3", "4", "5"):
        if _w.get_name().endswith("random_dungeonmagic_level" + _n): _lv = _n
    if _w.get_name().endswith("mistward_castle"): _lv = "mw"
LV = sys.argv[3] if len(sys.argv) > 3 else _lv           # (the argument wins: the editor may have another level open)
MW = LV == "mw"                                          # (mistward_castle: level 5's Save As copy)
L5 = LV == "5" or MW; L4 = LV == "4" or L5                # (level 5 is level 4's Save As copy: its machinery, the armour's plan)
HERO = sys.argv[4] if len(sys.argv) > 4 else ("Summoner" if L5 else "Rogue")
WAY = sys.argv[5] if len(sys.argv) > 5 else "east"
W5H = L5 and WAY == "heroes"            # (level 5: the four heroes' weapons reel: run5h)
W5C = L5 and WAY == "craft"             # (level 5: the armour table, loot and crafting reel: run5c)
W5X = L5 and WAY == "caps"              # (level 5: the four heroes' capabilities reel: run5x)
W5S = L5 and WAY == "spells"            # (level 5: the spells, rings, monsters by tier, corpses and menu reel: run5s)
W5G = L5 and WAY == "grip"              # (level 5: the two-handed grip close up: run5g)
W5W2 = L5 and WAY == "chop2"            # (level 5: Warrior2's chop test, Warrior2 alone (861 placed her): run5w2)
W5M = MW and WAY == "mistward"          # (mistward_castle: the four heroes and the castle's rules: run5m)
W5M2 = MW and WAY in ("mistward2", "mistward3", "mistward4")        # (mistward_castle: the third list (docs/improvements2.txt): run5m2; "mistward3": the same with the Martial Artist (mw3_martial); "mistward4": its recording, run5m4's plan)
W5M3 = MW and WAY == "mistward3"
W5M4 = MW and WAY == "mistward4"         # (the user's list of 2026-10-30: the six heroes in combat at all five tiers: run5m4)
W5R = L5 and WAY in ("weapons", "heroes", "craft", "spells", "caps", "mistward", "mistward2", "mistward3", "mistward4")       # (level 5: the weapons and tiers reels: run5w, run5h; their recording; run5c's and run5s's too)
W5K = W5C or W5S or W5X or W5M or W5M2  # (the crafting panel's and the repair list's recording)
DX, DY = {"east": (1, 0), "north": (0, 1), "west": (-1, 0), "south": (0, -1)}.get(WAY, (1, 0))
# (level 4: the hero fights as in her own level)
L2, L3 = LV == "2" or (L4 and HERO == "Warlock"), LV == "3" or (L4 and HERO == "Rogue")
MELEE = L4 and HERO == "Warrior"
CHESTS = L3 or L4                  # (she opens the containers she passes)
if L4: SEED += 101 * ["Warrior", "Mage", "Warlock", "Rogue", "Summoner", "MartialArtist"].index(HERO) + 7
if len(sys.argv) > 6: SEED = int(sys.argv[6])        # (level 4: a session seed of the reel's choosing: what the containers on her way hold)
OUT = ("E:\\code\\claude-ue5\\claude_ue5\\SourceArt\\mistward\\" + (("cine_mw4_%s.json" if W5M4 else "cine_mw3_%s.json" if W5M3 else "cine_mw2_%s.json" if W5M2 else "cine_mw_%s.json") if MODE == "render" else ("cine_mw4_rehearsal_%s.json" if W5M4 else "cine_mw3_rehearsal_%s.json" if W5M3 else "cine_mw2_rehearsal_%s.json" if W5M2 else "cine_mw_rehearsal_%s.json")) % HERO.lower()) if MW else "E:\\code\\claude-ue5\\claude_ue5\\SourceArt\\random_dungeon_magic" + ("" if LV == "1" else LV) + "\\" + (
    ((f"cine_quartet_{HERO.lower()}.json" if W5H else f"cine_craft_{HERO.lower()}.json" if W5C else f"cine_spells_{HERO.lower()}.json" if W5S else f"cine_grip_{HERO.lower()}.json" if W5G else f"cine_caps_{HERO.lower()}.json" if W5X else "cine_chop2_warrior2.json" if W5W2 else f"cine_{HERO.lower()}.json") if L4 else "cine_render.json")
    if MODE == "render" else ("cine_rehearsal_spells_%s.json" % HERO.lower() if W5S else "cine_rehearsal.json"))
SPEEDS = r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_" + ({"Warrior": "fem5", "Mage": "caster", "Warlock": "darkcaster", "Rogue": "rogue", "Summoner": "summoner4" if MW else "summoner3", "MartialArtist": "martialartist"}[HERO] if L4 else
                                                             {"1": "caster", "2": "darkcaster", "3": "rogue"}[LV]) + r"\speeds.txt"
def along(v): return v.x * DX + v.y * DY
V = unreal.Vector; Rot = unreal.Rotator; GS = unreal.GameplayStatics; IP = unreal.IntPoint
NEXT = IP(DX, DY)                  # (the section generated ahead of her)
def in_start(s): return s.x == 0 and s.y == 0
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
G = {}
S = {"rows": {}, "events": [], "segs": [], "maps": [], "saved": False, "seg": "", "note": {}, "hp": {}, "mapsig": {}, "disc": {}, "snd": {}, "bursts": 0, "music": None, "casts": 0, "bolts": 0,
     "rolls": 0, "dodged": 0, "poi_static": {}, "tier": {}}
if getattr(unreal, "_rdm_reel", None) is not None:
    try: unreal.unregister_slate_post_tick_callback(unreal._rdm_reel)
    except Exception: pass
# (level 4 rendered without ?Hero= would open its menu: rd.HeroMenu 0 until the pilot stops)
if L4: unreal.SystemLibrary.execute_console_command(None, "rd.HeroMenu 0")
WALK, RUN = [float(x) for x in open(SPEEDS).read().split()]
def T(): return G["t"]
def loc(): return G["pawn"].get_actor_location()
def event(kind, **kw):
    S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": kind, **kw})
    unreal.log("RDMREEL %6.2f s  %s %s" % (T(), kind, json.dumps(kw)[:200]))
def seg(name):
    S["seg"] = name; S["segs"].append({"name": name, "t": round(max(T(), 0.0), 3)}); unreal.log("RDMREEL %6.2f s  == %s" % (T(), name))
def alive(m):
    try: return m is not None and unreal.SystemLibrary.is_valid(m) and not m.is_dead()
    except Exception: return False
def d2(a, b): return math.hypot(a.x - b.x, a.y - b.y)
def yaw_to(a, b): return math.degrees(math.atan2(b.y - a.y, b.x - a.x))
def turn(cur, want, step):
    d = (want - cur + 180.0) % 360.0 - 180.0
    return cur + max(-step, min(step, d))
def sees(a, m):
    """no wall between her hand height and the monster (the spell needs that)"""
    ml = m.get_actor_location()
    h = unreal.SystemLibrary.line_trace_single(G["w"], V(a.x, a.y, a.z + 50), V(ml.x, ml.y, ml.z + 20), unreal.TraceTypeQuery.ECC_VISIBILITY, False, [G["pawn"]] + list(G["gen"].get_monsters()), unreal.DrawDebugTrace.NONE, True)
    return h is None or not h.to_tuple()[0]

# ---------------------------------------------------------------- her hands and feet
def move(to, run=True):
    """movement input toward a point: full input is her run (the character's top speed); a walk is the walk's share of it,
    as the move key without Shift gives"""
    l = loc(); d = V(to.x - l.x, to.y - l.y, 0.0)
    if d.length() > 1.0: G["pawn"].add_movement_input(d.normal(), 1.0 if run else WALK / RUN, False); G["heading"] = yaw_to(l, to)
def doors():
    """F on a closed door in her way (not on the containers)"""
    gen = G["gen"]; l = loc()
    if T() - G.get("door_t", -9.0) < 0.8: return
    what = str(gen.describe_nearest(l, 230.0))
    if what.startswith("open") and "door" in what:
        G["door_t"] = T(); gen.interact_nearest(l, 230.0); event("door", at=[round(l.x), round(l.y)])
def camera(side=0.0, pitch=-17.0, rate=110.0):
    """the third-person camera comes round behind where she is heading (side: degrees off that, in a fight)"""
    want = G.get("heading", 0.0) + side
    G["cam_yaw"] = turn(G.get("cam_yaw", want), want, rate * G["el"])
    G["cam_pitch"] = turn(G.get("cam_pitch", pitch), pitch, 40.0 * G["el"])
    G["pc"].set_control_rotation(Rot(roll=0.0, pitch=G["cam_pitch"], yaw=G["cam_yaw"]))
class Route:
    """tile centres to walk along: the point a little ahead of her on the line through them"""
    def __init__(self, pts): self.p = pts; self.i = 0
    def target(self, look=170.0):
        l = loc()
        while self.i < len(self.p) - 1 and d2(l, self.p[self.i]) < look: self.i += 1
        return self.p[self.i]
    def done(self): return self.i >= len(self.p) - 1 and d2(loc(), self.p[-1]) < 120.0
def sweep_clear(a, b, r=40.0):
    """a body-sized ball rolls from a to b without meeting a wall or furniture (her knees to her chest)"""
    h = unreal.SystemLibrary.sphere_trace_single_for_objects(G["w"], V(a.x, a.y, 75.0), V(b.x, b.y, 75.0), r,
        [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1, unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY2], False, [G["pawn"]] + list(G["gen"].get_monsters()), unreal.DrawDebugTrace.NONE, True)
    return h is None or not h.to_tuple()[0]
def pulled(route):
    """(level 5) the route's farthest point a few ahead that she can walk straight to: the tile path's steps cut short
    (in the great hall it went 27 m round a corner between two chests 6.5 m apart)"""
    l = loc(); n = len(route.p)
    route.i = min(range(route.i, min(n, route.i + 8)), key=lambda j: d2(l, route.p[j]) - 0.01 * j)
    for j in range(min(n - 1, route.i + 7), route.i, -1):
        if sweep_clear(l, route.p[j]): return route.p[j]
    return route.target(90.0)
def section_of(l): return G["gen"].get_section(G["gen"].world_to_section(l))
def path(a, b):
    sec = section_of(a)
    return list(sec.find_path_world(a, b)) if sec else []
def wide_here():
    l = loc(); sec = section_of(l)
    return sec is not None and sec.room_at(l) >= 0 and "unction" not in sec.get_room_kind(sec.room_at(l))
REEL_AGGRO = 4500.0
def lure(on=True):
    """(run5h) her fights: the monsters notice her from REEL_AGGRO cm (on) or from the game's own distance again (off)"""
    gen = G["gen"]
    if "aggro0" not in G: G["aggro0"] = (gen.get_editor_property("aggro_distance"), gen.get_editor_property("lose_distance"))
    a0, l0 = G["aggro0"]
    gen.set_editor_property("aggro_distance", REEL_AGGRO if on else a0); gen.set_editor_property("lose_distance", max(l0, REEL_AGGRO + 1500.0) if on else l0)
    event("lure", on=on, aggro_cm=REEL_AGGRO if on else a0, game_aggro_cm=a0)
def threat():
    """the monster to fight: one that is after her, or one she can see within the spell's reach"""
    l = loc(); best = None
    for m in G["gen"].get_monsters():
        if not alive(m): continue
        ml = m.get_actor_location(); d = d2(l, ml)
        if abs(ml.z - l.z) > 300: continue
        if (m.is_aggro() and d < 1500.0) or (d < 1500.0 and sees(l, m)):          # (the spell reaches 14 m, the crossbow 26: she takes on what she sees within 15)
            if best is None or d < best[0]: best = (d, m)
    return best[1] if best else None
def chests_of(c):
    md = G["gen"].get_editor_property("map_data").get(c)
    return [V(q.x, q.y, 100.0) for q in md.chests] if md else []          # (the map keeps them as 2D points)

def clear_line(a, b):
    """nothing in the way between two points at her knee height (walls, furniture)"""
    h = unreal.SystemLibrary.line_trace_single(G["w"], V(a.x, a.y, 50.0), V(b.x, b.y, 50.0), unreal.TraceTypeQuery.ECC_VISIBILITY, False, [G["pawn"]] + list(G["gen"].get_monsters()), unreal.DrawDebugTrace.NONE, True)
    return h is None or not h.to_tuple()[0]
def stand_by_chest(at, frm, tol=160.0):
    """where to stand to open the chest at `at`: a spot 1 m or so from it that she can walk to from `frm` and from which
    F reaches that chest (the nearest door or container there is it); None when there is none. The path ends on a tile's
    centre: within `tol` of the spot (more for a chest against a wall, with nothing between that centre and the spot)"""
    gen = G["gen"]; best = None
    for r in (100.0, 140.0):
        for k in range(12):
            a = k * math.pi / 6; q = V(at.x + math.cos(a) * r, at.y + math.sin(a) * r, 100.0)
            what = str(gen.describe_nearest(q, 200.0))
            if not what.startswith("open") or "door" in what: continue
            pts = path(frm, q)
            if not len(pts): continue
            gap = d2(pts[-1], q)
            if (gap < 160.0 or (gap < tol and clear_line(pts[-1], q))) and (best is None or (len(pts), gap) < best[0]): best = ((len(pts), gap), q)
    return best[1] if best else None

def open_chest(at, stand=None):
    """walks to a chest, opens it (F) and looks at it a moment"""
    gen = G["gen"]; stand = stand or stand_by_chest(at, loc())
    if stand is None: event("chest_missed", why="no place to stand"); return
    route = Route(path(loc(), stand) + [stand]); t0 = T(); stuck = 0.0; last = loc()
    event("to_chest", at=[round(at.x), round(at.y)], stand=[round(stand.x), round(stand.y)])
    while T() - t0 < (16.0 if L5 else 9.0):             # (level 5: across the great hall, 25 m and more)
        l = loc()
        if d2(l, stand) < 45.0: break
        # (level 5: close enough already when F names a container and the chest is within its reach)
        if L5 and d2(l, at) < 175.0 and str(gen.describe_nearest(l, 200.0)).startswith("open") and "door" not in str(gen.describe_nearest(l, 200.0)): break
        if L5 and not G.get("quiet"):
            # (a monster that comes at her on the way is dealt with first; then on to the chest (not while the reel has them leave her be))
            m = threat()
            if m is not None:
                # (run5h: with the weapon in her hands, as her later fights; the Mage with her spells)
                tf = T(); seg("fight"); G["casts0"] = G["combat"].attacks_made; yield from (fight_w(m) if (W5H and HERO != "Mage") else fight(m)); seg("chest")
                t0 += T() - tf; route = Route(path(loc(), stand) + [stand]); last = loc(); continue
        move(pulled(route) if L5 else route.target(90.0), run=d2(l, stand) > (150.0 if CHESTS else 600.0)); doors(); camera(side=-22.0, pitch=-24.0, rate=90.0)
        stuck = stuck + G["el"] if d2(loc(), last) < 40.0 * G["el"] else 0.0; last = loc()
        if stuck > 0.8:
            stuck = 0.0; G["chest_repaths"] = G.get("chest_repaths", 0) + 1
            if G["chest_repaths"] > 2: break
            route = Route(path(loc(), stand) + [stand]); event("repath")
        yield
    G["chest_repaths"] = 0
    l = loc(); what = str(gen.describe_nearest(l, 200.0))
    # (a door she opened on the way can swing nearer to the spot than the chest, or she stopped just short of F's reach:
    # a step or two toward the chest)
    t2 = T()
    while ("door" in what or not what) and T() - t2 < 1.4 and d2(l, at) > 80.0:
        move(at, run=False); camera(side=-22.0, pitch=-24.0, rate=90.0); yield
        l = loc(); what = str(gen.describe_nearest(l, 200.0))
    if what.startswith("open") and "door" not in what and d2(l, at) < 260.0:
        G["heading"] = yaw_to(l, at); G["pawn"].set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), False)
        gen.interact_nearest(l, 200.0); event("chest", what=what, at=[round(at.x), round(at.y)]); G["key_hit"] = "f"; G["keys_t"] = T()
        t1 = T()
        while T() - t1 < 1.3: camera(side=-30.0, pitch=-26.0, rate=70.0); yield
    else: event("chest_missed", what=what)

def fight(m, take=0):
    """the fire spell from range: she closes in until she can see it within the spell's reach, then casts until it is down
    (take: level 5, in armour: she stands her ground until that many of its blows have landed on her, then casts)"""
    c = G["combat"]; p = G["pawn"]; n = G["fights"]; G["fights"] += 1
    name = str(m.monster_name); hp0 = m.get_max_health(); h0 = c.get_health(); t0 = T(); b0 = c.hits_landed; k0 = c.kills
    event("fight", monster=name, its_hit_points=hp0, its_damage=m.get_damage(), section=[m.get_editor_property("section").get_editor_property("coord").x, m.get_editor_property("section").get_editor_property("coord").y],
          from_m=round((d2(loc(), m.get_actor_location())) / 100.0, 1), armour=str(c.get_worn_armour()) if L5 else None, take=take,
          **({"weapon": "Dark Fire", "spells": True} if (W5H and HERO == "Mage") else {}))     # (run5h's Mage: dark fire first, then fire)
    route = None; rt = -9.0; casts = 0; reach = G["gen"].get_editor_property("weapons")[0].reach
    mage = L4 and HERO in ("Mage", "Summoner")
    taken0 = c.hits_taken; waited = None
    while alive(m) and not c.is_dead() and T() - t0 < 16.0 + (8.0 if take else 0.0) and T() < DUR + 1.0:
        l = loc(); ml = m.get_actor_location(); gap = d2(l, ml) - m.capsule_component.get_scaled_capsule_radius()
        G["heading"] = yaw_to(l, ml)
        if not c.is_attacking():
            face = lambda: p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=turn(p.get_actor_rotation().yaw, yaw_to(l, ml), 720.0 * G["el"])), False)
            holding = take and c.hits_taken - taken0 < take and gap < CAST_GAP and sees(l, m)
            if holding:
                # (she waits for it: once it is after her it comes; if it has not noticed her in 3 s, a cast wakes it)
                waited = waited if waited is not None else T()
                face()
                if not m.is_aggro() and T() - waited > 3.0 and casts == 0 and c.start_attack(): G["key_hit"] = "e"; G["keys_t"] = T(); casts += 1
            elif (L2 or MELEE) and gap < reach - 10.0:
                face()                                            # (the sword: close enough)
                if c.start_attack(): G["key_hit"] = "lmb"; G["keys_t"] = T()
            elif MELEE or gap > CAST_GAP or not sees(l, m) or (L2 and casts >= 2):
                if route is None or T() - rt > 0.7: route = Route(path(l, ml)); rt = T()
                move(route.target() if len(route.p) > 1 and gap > (400.0 if not MELEE else 260.0) else ml, run=True); doors()
            else:
                face()
                if mage:
                    # (the Mage: dark fire first (2), then fire (1) while her mana lasts)
                    want = 1 if casts == 0 else 0
                    if c.get_weapon_index() != want: c.select_weapon(want); key_hit(str(want + 1))
                if c.start_spell() if L2 else c.start_attack(): G["key_hit"] = "e"; G["keys_t"] = T(); casts += 1
        camera(side=(30.0 if n % 2 == 0 else -30.0) if wide_here() else 8.0, pitch=-15.0 if wide_here() else -25.0, rate=80.0)
        yield
    G["last_fight"] = T()
    if not alive(m): event("kill", monster=name, casts=c.attacks_made - G.get("casts0", 0), blows=c.hits_landed - b0, seconds=round(T() - t0, 2), she_lost=round(max(0.0, h0 - c.get_health())), its_hit_points=hp0)
    else: event("left", monster=name)
    t1 = T()
    while T() - t1 < 0.5: camera(side=18.0, rate=70.0); yield

def key_hit(k): G["key_hit"] = k; G["keys_t"] = T()
def fight3(m):
    """(level 3) the crossbow from range, then the daggers; a roll back out of a blow up close"""
    c = G["combat"]; p = G["pawn"]; n = G["fights"]; G["fights"] += 1
    name = str(m.monster_name); hp0 = m.get_max_health(); h0 = c.get_health(); t0 = T(); b0 = c.hits_landed
    event("fight", monster=name, its_hit_points=hp0, its_damage=m.get_damage(), section=[m.get_editor_property("section").get_editor_property("coord").x, m.get_editor_property("section").get_editor_property("coord").y],
          from_m=round((d2(loc(), m.get_actor_location())) / 100.0, 1))
    wd = G["gen"].get_editor_property("weapons"); reach = wd[0].reach; xbow = next(i for i, d in enumerate(wd) if d.spell)
    route = None; rt = -9.0; shots = 0; rolls = 0; phase = "bolts"; last_roll = -9.0; gap_shot = 1600.0     # (the crossbow reaches 26 m: she shoots from 16)
    while alive(m) and not c.is_dead() and T() - t0 < 16.0 and T() < DUR + 1.0:
        l = loc(); ml = m.get_actor_location(); gap = d2(l, ml) - m.capsule_component.get_scaled_capsule_radius()
        G["heading"] = yaw_to(l, ml)
        face = lambda: p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=turn(p.get_actor_rotation().yaw, yaw_to(l, ml), 720.0 * G["el"])), False)
        if c.is_rolling(): camera(side=24.0 if wide_here() else 8.0, pitch=-16.0 if wide_here() else -25.0, rate=80.0); yield; continue
        # its blow is coming and she is in reach of it: a roll back (she keeps her eyes on it)
        if m.is_attacking() and gap < 230.0 and rolls < 1 and T() - last_roll > 1.5:
            face()
            if c.start_roll(V(l.x - ml.x, l.y - ml.y, 0.0)):             # (away from it: behind her, a roll backward)
                rolls += 1; last_roll = T(); key_hit("b"); event("roll", monster=name, gap_cm=round(gap), back=bool(c.is_rolling_back())); yield; continue
        if not c.is_attacking():
            if phase == "bolts" and (shots >= 2 or (gap < 330.0 and shots >= 1) or (gap < 200.0)):
                phase = "daggers"
                if c.get_weapon_index() != 0: c.select_weapon(0); key_hit("1")
            if phase == "bolts":
                if c.get_weapon_index() != xbow: c.select_weapon(xbow); key_hit("2")
                if gap > gap_shot or not sees(l, m):
                    if route is None or T() - rt > 0.7: route = Route(path(l, ml)); rt = T()
                    move(route.target() if len(route.p) > 1 and gap > 400.0 else ml, run=True); doors()
                else:
                    face()
                    if c.start_attack(): key_hit("lmb"); shots += 1
            elif gap < reach - 10.0:
                face()
                if c.start_attack(): key_hit("lmb")
            else:
                if route is None or T() - rt > 0.5: route = Route(path(l, ml)); rt = T()
                move(route.target() if len(route.p) > 1 and gap > 400.0 else ml, run=True); doors()
        camera(side=(30.0 if n % 2 == 0 else -30.0) if wide_here() else 8.0, pitch=-15.0 if wide_here() else -25.0, rate=80.0)
        yield
    G["last_fight"] = T()
    if not alive(m): event("kill", monster=name, casts=shots, blows=c.hits_landed - b0, seconds=round(T() - t0, 2), she_lost=round(max(0.0, h0 - c.get_health())), its_hit_points=hp0, rolls=rolls)
    else: event("left", monster=name)
    t1 = T()
    while T() - t1 < 0.5: camera(side=18.0, rate=70.0); yield

def inventory_beat():
    """(level 4) after her first fight she opens the inventory (I), goes down it (S) to what helps her now and uses it
    (Enter): a healing potion or food when she is hurt, a mana potion when her mana is down, a speed potion, else the
    next weapon; with none of these she looks down the list. Then she closes it."""
    c = G["combat"]; gen = G["gen"]
    kinds = {str(it.name): str(it.kind.name).lower() for it in gen.get_editor_property("items")}
    lines = list(c.get_inventory_lines()); want = None; why = ""
    items = [(i, x.split("|")[1]) for i, x in enumerate(lines) if x.startswith("item|")]
    hurt = c.get_health() < c.get_max_health() - 0.5
    low = c.get_max_mana() > 0.0 and c.get_mana() < c.get_max_mana() - 1.0
    for pref, cond in (("healing", hurt), ("food", hurt), ("mana", low), ("speed", True)):
        if want is None and cond:
            for i, n in items:
                if kinds.get(n) == pref: want, why = i, pref; break
    if want is None:
        for i, d in enumerate(gen.get_editor_property("weapons")):
            if not d.alongside and i != c.get_weapon_index(): want, why = i, "weapon"; break
    event("inventory", lines=lines, want=want, why=why, hp=round(c.get_health(), 1), mana=round(c.get_mana(), 1))
    c.set_inventory_open(True); key_hit("i")
    t0 = T()
    while T() - t0 < 0.9: yield
    if want is not None:
        while c.get_inventory_cursor() != want and T() - t0 < 6.0:
            c.move_inventory_cursor(1 if want > c.get_inventory_cursor() else -1); key_hit("s")
            t1 = T()
            while T() - t1 < 0.45: yield
        t1 = T()
        while T() - t1 < 0.35: yield
        ok = c.use_inventory_entry(); key_hit("enter")
        event("used", entry=lines[want], ok=bool(ok), message=str(c.message), hp=round(c.get_health(), 1), mana=round(c.get_mana(), 1))
        t1 = T()
        while T() - t1 < 1.8: yield
    else:
        for k in range(min(3, len(lines) - 1)):
            c.move_inventory_cursor(1); key_hit("s"); t1 = T()
            while T() - t1 < 0.5: yield
    c.set_inventory_open(False); key_hit("i")
    t1 = T()
    while T() - t1 < 0.3: yield

def pause(sec, cam=None):
    t0 = T()
    while T() - t0 < sec:
        if cam: cam()
        yield
def orbit(sec, side0, sweep, pitch=-10.0, ease=True):
    """(level 5) the camera goes round her while she stands: from `side0` degrees off the way she faces (180: in front of
    her, looking at her) through `sweep` degrees, eased in and out (or at an even rate)"""
    face = G["pawn"].get_actor_rotation().yaw; t0 = T(); p0 = G.get("cam_pitch", pitch)
    while T() - t0 < sec:
        k = min(1.0, (T() - t0) / sec); s = (0.5 - 0.5 * math.cos(math.pi * k)) if ease else k
        G["cam_yaw"] = face + side0 + sweep * s; G["cam_pitch"] = p0 + (pitch - p0) * min(1.0, k * 3.0)
        G["pc"].set_control_rotation(Rot(roll=0.0, pitch=G["cam_pitch"], yaw=G["cam_yaw"])); yield
def swing_to(side, sec=0.8, pitch=-14.0):
    """(level 5) the camera eases to `side` degrees off the way she faces"""
    face = G["pawn"].get_actor_rotation().yaw; y0 = G.get("cam_yaw", face); d = (face + side - y0 + 180.0) % 360.0 - 180.0
    yield from orbit(sec, y0 - face, d, pitch)
def wear(name, k):
    """(level 5) I, down or up the list to the set (S / W), Enter, a moment with WORN on it, I"""
    c = G["combat"]
    lines = [str(x) for x in c.get_inventory_lines()]
    want = next((i for i, x in enumerate(lines) if x.startswith("armour|" + name + "|")), None)
    event("inventory", lines=lines, want=want, why="armour", hp=round(c.get_health(), 1), mana=round(c.get_mana(), 1))
    c.set_inventory_open(True); key_hit("i")
    yield from pause(0.7)
    while want is not None and c.get_inventory_cursor() != want:
        down = want > c.get_inventory_cursor(); far = abs(want - c.get_inventory_cursor()) > 3
        c.move_inventory_cursor(1 if down else -1); key_hit("s" if down else "w")
        yield from pause(0.11 if far else 0.32)
    yield from pause(0.35)
    ok = c.use_inventory_entry(); key_hit("enter")
    event("used", entry=lines[want] if want is not None else "", ok=bool(ok), message=str(c.message), hp=round(c.get_health(), 1), mana=round(c.get_mana(), 1))
    yield from pause(0.9)
    c.set_inventory_open(False); key_hit("i")
    yield from pause(0.15)
def run5():
    """(level 5) the great hall's containers, every armour set put on in turn with the camera round her, then a monster's
    blows on her in the plate armour"""
    gen, p, c = G["gen"], G["pawn"], G["combat"]
    seg("start")
    while T() <= 0.0 or G["combat"] is None:
        camera(rate=1e6); yield
    def start_count(): return sum(1 for q in gen.get_monsters() if alive(q) and q.get_editor_property("section").get_editor_property("coord") == IP(0, 0))
    while T() < 0.5 or (start_count() < 10 and T() < 1.2):
        camera(rate=1e6); yield
    c = G["combat"]; s0 = gen.get_section(IP(0, 0)); hall = list(gen.get_start_room_containers())
    S["note"]["hall"] = {str(i): [str(x) for x in gen.loot_list_of(IP(0, 0), i)] for i in hall}
    centre = gen.get_start_room_center()
    # the shortest way through the hall's containers; she starts 4 m from the first, toward the middle of the hall, facing it
    import itertools
    cl = {i: s0.get_container_location(i) for i in hall}
    tour = list(min(itertools.permutations(hall), key=lambda o: sum(d2(cl[o[k]], cl[o[k + 1]]) for k in range(len(o) - 1))))
    f0 = cl[tour[0]]; tow = V(centre.x - f0.x, centre.y - f0.y, 0.0)
    st = V(f0.x + tow.normal().x * 400.0, f0.y + tow.normal().y * 400.0, 100.0) if tow.length() > 1 else V(centre.x, centre.y, 100.0)
    p.set_actor_location(st, False, True)
    G["heading"] = yaw_to(st, f0); p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), True)
    G["cam_yaw"] = G["heading"] - 22.0; G["cam_pitch"] = -24.0
    event("start", at=[round(st.x), round(st.y)], hall=hall, tour=tour, way="great hall")
    yield from pause(0.6, lambda: camera(side=-22.0, pitch=-24.0, rate=1e6))
    # ---- the great hall's containers, in that order (one that F opened on the way is not gone back to)
    seg("chest")
    for i in tour:
        if s0.is_target_open(False, i): continue
        at = cl[i]; st_ = stand_by_chest(at, loc(), tol=450.0)
        if st_ is None: event("chest_missed", why="no place to stand", container=i); continue
        yield from open_chest(at, st_)
        yield from pause(0.5, lambda: camera(side=-30.0, pitch=-26.0, rate=70.0))
    # ---- hurt on the way: the inventory first for what heals her (level 4's beat: a potion or food)
    if c.get_health() < c.get_max_health() * 0.7:
        seg("inventory"); yield from inventory_beat()
    # ---- to an open spot of the hall first: the camera goes round her there (by the walls it went through the banners,
    # which have no collision for its arm to stop on)
    def open_spot():
        """the nearest point of her room with 4.2 m clear all round (16 directions)"""
        l = loc(); room = s0.room_at(l)
        cands = sorted((V(l.x + gx * 150.0, l.y + gy * 150.0, 100.0) for gx in range(-10, 11) for gy in range(-10, 11)), key=lambda q: d2(q, l))
        for q in cands:
            if s0.room_at(q) != room: continue
            if all(sweep_clear(q, V(q.x + math.cos(a) * 420.0, q.y + math.sin(a) * 420.0, 100.0), 30.0) for a in [k * math.pi / 8 for k in range(16)]) and len(path(l, q)):
                return q
        return None
    def go_open():
        sec = section_of(loc())
        if sec is None or sec.room_at(loc()) < 0: return
        spot = open_spot() if sec == s0 else None
        event("to_open_spot", at=[round(spot.x), round(spot.y)] if spot else None)
        if spot is None: return
        seg("walk"); route = Route(path(loc(), spot) + [spot]); t1 = T()
        while d2(loc(), spot) > 60.0 and T() - t1 < 12.0:
            m = threat()
            if m is not None:
                seg("fight"); G["casts0"] = c.attacks_made; yield from fight(m); seg("walk"); route = Route(path(loc(), spot) + [spot])
            move(pulled(route), run=d2(loc(), spot) > 300.0); camera(side=-20.0, pitch=-18.0, rate=90.0); yield
    yield from go_open()
    # ---- every set on her in turn, the camera round her after each
    seg("armour")
    order = [str(x).split("|")[1] for x in c.get_inventory_lines() if str(x).startswith("armour|")]
    plate = next((n for n in order if n.startswith("Plate")), order[0] if order else None)
    plan = order + ([plate] if order and order[-1] != plate else [])
    yield from swing_to(150.0, 0.9)
    for k, name in enumerate(plan):
        for _ in range(3):
            m = threat()
            if m is None: break
            # (the first monster after her once she wears a set lands its blows on the armour)
            tk = 0 if G.get("took") or str(c.get_worn_armour()) == "None" else 2
            seg("fight"); G["casts0"] = c.attacks_made; yield from fight(m, take=tk); seg("armour")
            if tk: G["took"] = True
        if c.get_health() < c.get_max_health() * 0.6:
            seg("inventory"); yield from inventory_beat(); seg("armour")
        yield from wear(name, k)
        # (round her: the first time all the way, then a wide arc, alternately left and right)
        s0_, sw_ = (150.0, 360.0) if k == 0 else ((120.0, 120.0) if k % 2 else (240.0, -120.0))
        yield from swing_to(s0_, 0.5, -9.0)
        yield from orbit(4.4 if k == 0 else 3.0, s0_, sw_, -8.0 if k == 0 else (-10.0 if k % 2 else -6.0))
    # ---- in the plate armour: the nearest monster of the start section comes at her; its blows land on the plate
    seg("walk")
    mine = gen.get_section(IP(0, 0)); prey = None
    m = threat()
    if m is not None: prey = (0, m)
    for q in ([] if prey else gen.get_monsters()):
        if not alive(q) or q.get_editor_property("section") != mine: continue
        pts = path(loc(), q.get_actor_location())
        if 1 < len(pts) <= (30 if not G.get("took") else 12) and (prey is None or len(pts) < prey[0]): prey = (len(pts), q)
    if prey is not None:
        event("hunt", monster=str(prey[1].monster_name), way_m=prey[0] * 3)
        seg("fight"); G["casts0"] = c.attacks_made; yield from fight(prey[1], take=0 if G.get("took") else 2); G["took"] = True
    # ---- to the end: round her in an open spot, a little at a time (a monster that comes at her is fought, in the plate)
    yield from go_open()
    seg("armour"); k = 0
    while True:
        m = threat()
        if m is not None:
            seg("fight"); G["casts0"] = c.attacks_made; yield from fight(m, take=0 if G.get("took") else 2); G["took"] = True; seg("armour"); k = 0
        if k == 0: yield from swing_to(150.0, 0.9, -10.0)
        yield from orbit(2.0, 150.0 + 30.0 * k, 30.0, -10.0, ease=False); k += 1

def fight_w(m, take=0):
    """(the weapons reel) with the weapon in her hands: in reach for a blade, from up to 15 m for a bow or a crossbow (the
    weapon may break on the way: then with the one she draws). take (run5c): up close she stands her ground until that
    many of its blows have landed on her (or 5 s went by), then fights"""
    c = G["combat"]; p = G["pawn"]; gen = G["gen"]; n = G["fights"]; G["fights"] += 1
    name = str(m.monster_name); hp0 = m.get_max_health(); h0 = c.get_health(); t0 = T(); b0 = c.hits_landed
    wd0 = gen.get_editor_property("weapons")[c.get_weapon_index()]
    event("fight", monster=name, its_hit_points=hp0, its_damage=m.get_damage(), section=[m.get_editor_property("section").get_editor_property("coord").x, m.get_editor_property("section").get_editor_property("coord").y],
          from_m=round((d2(loc(), m.get_actor_location())) / 100.0, 1), weapon=str(wd0.name), damage=round(c.get_damage_of(c.get_weapon_index()), 1),
          **({"title": str(m.title), "ability": str(m.ability.name), "tier": m.tier, "take": take} if W5S else {}))
    route = None; rt = -9.0; best, tbest = 1e9, T(); switched = False; taken0 = c.hits_taken; held = None
    while alive(m) and not c.is_dead() and T() - t0 < (24.0 if W5H else 18.0) and T() < G.get("until", DUR + 1.0):
        wd = gen.get_editor_property("weapons")[c.get_weapon_index()]; ranged = bool(wd.spell); reach = wd.reach
        l = loc(); ml = m.get_actor_location(); gap = d2(l, ml) - m.capsule_component.get_scaled_capsule_radius()
        # (run5h: how near by the way she has to go, not straight across: round a wall the straight gap does not shrink)
        prog = gap if not W5H else (None if route is None else d2(l, route.p[0]) + sum(d2(route.p[k], route.p[k + 1]) for k in range(len(route.p) - 1)) if len(route.p) > 1 else gap)
        if prog is not None and prog < best - 100.0: best, tbest = prog, T()
        o = threat()
        if o is not None and o != m and o.is_aggro() and d2(l, o.get_actor_location()) + 200.0 < d2(l, ml): switched = True; break      # (another one is on her, nearer: that one first)
        G["heading"] = yaw_to(l, ml)
        if not c.is_attacking():
            face = lambda: p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=turn(p.get_actor_rotation().yaw, yaw_to(l, ml), 720.0 * G["el"])), False)
            if take and c.hits_taken - taken0 < take and (gap < 260.0 or W5S) and (held is None or T() - held < (6.0 if W5S else 5.0)):
                # (her armour takes its blows; run5s: she holds fire until they land, what they carry shows)
                held = held if held is not None else T(); face()
            # (the Martial Artist's chi: a bolt with a range of its own (4 m): refused from farther, so she closes in to 3.3 m)
            elif (ranged and gap < (330.0 if wd.bolt_range > 0 else 1500.0) and sees(l, m)) or (not ranged and gap < reach - 10.0):
                face()
                # (run5h: a bow or crossbow shoots where she faces: only once she faces it (a monster behind her took
                # every arrow into the wall in front of her))
                off = abs((yaw_to(l, ml) - p.get_actor_rotation().yaw + 180.0) % 360.0 - 180.0)
                if not (W5H and ranged and off > 10.0) and c.start_attack(): key_hit("lmb")
            else:
                if route is None or T() - rt > 0.6: route = Route(path(l, ml)); rt = T()
                move(route.target() if len(route.p) > 1 and gap > 300.0 else ml, run=True); doors()
        camera(side=(28.0 if n % 2 == 0 else -28.0) if wide_here() else 8.0, pitch=-14.0 if wide_here() else -25.0, rate=80.0)
        yield
        # (run5h: only "no nearer by her way for 3 s": the monsters near the hall were 35 to 50 m off by the way)
        if (T() - tbest > 3.0 or (not W5H and T() - t0 > 8.0 and gap > 1000.0)) and c.hits_landed == b0 and gap > 600.0: break      # (one that keeps away (3 s no nearer, or 10 m off after 8 s): another, not a chase through the rooms; 5 s gave up on more than it saved)
    G["last_fight"] = T()
    if not alive(m): event("kill", monster=name, casts=c.attacks_made - G.get("casts0", 0), blows=c.hits_landed - b0, seconds=round(T() - t0, 2), she_lost=round(max(0.0, h0 - c.get_health())), its_hit_points=hp0)
    else:
        event("left", monster=name, switched=switched)
        if not switched: G.setdefault("skip", set()).add(m.get_name())
    yield from pause(0.6, lambda: camera(side=18.0, rate=70.0))
def wield(name, prefix="weapon", why="wield"):
    """(the weapons reels) I, down the list to the weapon (S), Enter, a moment, I (run5h: an item too, prefix "item")"""
    c = G["combat"]
    lines = [str(x) for x in c.get_inventory_lines()]
    want = next((i for i, x in enumerate(lines) if x == prefix + "|" + name or x.startswith(prefix + "|" + name + "|")), None)
    event("inventory", lines=lines, want=want, why=why, **({"weapon": name} if prefix == "weapon" else {"item": name}), hp=round(c.get_health(), 1), mana=round(c.get_mana(), 1))
    c.set_inventory_open(True); key_hit("i")
    yield from pause(0.9)
    while want is not None and c.get_inventory_cursor() != want:
        down = want > c.get_inventory_cursor(); far = W5H and abs(want - c.get_inventory_cursor()) > 3
        c.move_inventory_cursor(1 if down else -1); key_hit("s" if down else "w")
        yield from pause(0.12 if far else 0.32)          # (run5h: a long way down or up the list goes faster)
    yield from pause(0.6)
    ok = c.use_inventory_entry(); key_hit("enter")
    event("used", entry=lines[want] if want is not None else "", ok=bool(ok), message=str(c.message), hp=round(c.get_health(), 1), mana=round(c.get_mana(), 1))
    yield from pause(1.6)
    c.set_inventory_open(False); key_hit("i")
    yield from pause(0.2)
def nearest_monster(sec_coord=None, max_steps=40, max_len=1e9):
    """the nearest live monster she has a way to (of one section, or any): by the way's length (its points are its
    corners, not its tiles), at most max_len cm"""
    best = None; l = loc()
    for q in G["gen"].get_monsters():
        if not alive(q) or q.get_name() in G.get("skip", ()): continue
        if sec_coord is not None and q.get_editor_property("section").get_editor_property("coord") != sec_coord: continue
        pts = path(l, q.get_actor_location())
        if not 1 < len(pts) <= max_steps: continue
        ln = d2(l, pts[0]) + sum(d2(pts[k], pts[k + 1]) for k in range(len(pts) - 1))
        if ln <= max_len and (best is None or ln < best[0]): best = (ln, q)
    return best[1] if best else None
def fights_w(kills=1, tries=4, steps=40):
    """(the weapons reel) fights with the weapon in hand until it has killed `kills` monsters (one that keeps away is
    left for the next nearest)"""
    c = G["combat"]; k0 = sum(1 for e in S["events"] if e["kind"] == "kill")
    for _ in range(tries):
        if T() > G.get("until", 1e9) - 6.0: return
        # (run5h, lured: one coming at her is waited for a moment where she stands, before she sets out after the nearest)
        if W5H and "aggro0" in G and threat() is None:
            tw = T()
            while threat() is None and T() - tw < 2.5 and T() < G.get("until", 1e9) - 6.0:
                camera(side=25.0, pitch=-12.0, rate=25.0); yield
        m = threat() or nearest_monster(IP(0, 0), 60)
        if m is None: return
        # (run5h's Mage: her spells, dark fire first: level 4's fight)
        seg("fight"); G["casts0"] = c.attacks_made; yield from (fight(m) if (W5H and HERO == "Mage") else fight_w(m)); seg("weapon")
        if sum(1 for e in S["events"] if e["kind"] == "kill") - k0 >= kills or c.get_health() < c.get_max_health() * 0.4: return
def refuse(prefix, name):
    """(run5h) I, down the list to a thing her hero cannot use (a weapon she cannot wield: a "carried" row; armour not
    made for her), a moment on it (the panel says why), Enter (refused: what the game says), a moment, I"""
    c = G["combat"]
    lines = [str(x) for x in c.get_inventory_lines()]
    want = next((i for i, x in enumerate(lines) if x.startswith(prefix + "|" + name + "|")), None)
    event("inventory", lines=lines, want=want, why="refused", item=name, what=prefix, hp=round(c.get_health(), 1), mana=round(c.get_mana(), 1))
    if want is None: return
    c.set_inventory_open(True); key_hit("i")
    yield from pause(0.8)
    while c.get_inventory_cursor() != want:
        down = want > c.get_inventory_cursor(); far = abs(want - c.get_inventory_cursor()) > 3
        c.move_inventory_cursor(1 if down else -1); key_hit("s" if down else "w")
        yield from pause(0.12 if far else 0.3)
    yield from pause(1.4)
    ok = c.use_inventory_entry(); key_hit("enter")
    event("used", entry=lines[want], ok=bool(ok), message=str(c.message), hp=round(c.get_health(), 1), mana=round(c.get_mana(), 1))
    yield from pause(2.2)
    c.set_inventory_open(False); key_hit("i")
    # (a moment with it shut: the reel's caption says why (the open inventory covers the captions))
    yield from pause(2.8, lambda: camera(side=25.0, pitch=-12.0, rate=25.0))
def hall():
    """(the weapons reels) she starts in the great hall by the first of its chests that hold weapons and opens them by the
    shortest round; returns what she found, by the table's type"""
    gen, p = G["gen"], G["pawn"]
    seg("start")
    while T() <= 0.0 or G["combat"] is None:
        camera(rate=1e6); yield
    def start_count(): return sum(1 for q in gen.get_monsters() if alive(q) and q.get_editor_property("section").get_editor_property("coord") == IP(0, 0))
    while T() < 0.5 or (start_count() < 10 and T() < 1.2):
        camera(rate=1e6); yield
    c = G["combat"]; s0 = gen.get_section(IP(0, 0)); hall = list(gen.get_start_room_containers())
    c.set_inventory_open(False)
    # (where the start section's monsters are now)
    S["note"]["start_monsters"] = [[str(q.monster_name), round(q.get_actor_location().x), round(q.get_actor_location().y)] for q in gen.get_monsters()
                                   if alive(q) and q.get_editor_property("section").get_editor_property("coord") == IP(0, 0)]
    kinds = {str(it.name): str(it.kind.name).lower() for it in gen.get_editor_property("items")}
    lists = {i: [str(x) for x in gen.loot_list_of(IP(0, 0), i)] for i in hall}
    S["note"]["hall"] = {str(i): v for i, v in lists.items()}
    with_w = [i for i in hall if any(kinds.get(x) == "weapon" for x in lists[i])] or hall
    import itertools
    cl = {i: s0.get_container_location(i) for i in with_w}; centre = gen.get_start_room_center()
    tour = list(min(itertools.permutations(with_w), key=lambda o: sum(d2(cl[o[k]], cl[o[k + 1]]) for k in range(len(o) - 1))))
    f0 = cl[tour[0]]; tow = V(centre.x - f0.x, centre.y - f0.y, 0.0)
    st = V(f0.x + tow.normal().x * 400.0, f0.y + tow.normal().y * 400.0, 100.0) if tow.length() > 1 else V(centre.x, centre.y, 100.0)
    p.set_actor_location(st, False, True); G["heading"] = yaw_to(st, f0); p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), True)
    G["cam_yaw"] = G["heading"] - 22.0; G["cam_pitch"] = -24.0
    event("start", at=[round(st.x), round(st.y)], hall=hall, tour=tour, way="great hall, the chests with weapons")
    yield from pause(0.6, lambda: camera(side=-22.0, pitch=-24.0, rate=1e6))
    seg("chest")
    for i in tour:
        if s0.is_target_open(False, i): continue
        st_ = stand_by_chest(cl[i], loc(), tol=450.0)
        if st_ is None: event("chest_missed", why="no place to stand", container=i); continue
        yield from open_chest(cl[i], st_)
        yield from pause(0.4, lambda: camera(side=-30.0, pitch=-26.0, rate=70.0))
    # what she found, by the table's type (the item's looks line starts with it)
    looks = {str(it.name): str(it.looks) for it in gen.get_editor_property("items")}
    found = [str(x.name) for x in gen.get_editor_property("weapons") if str(x.item) not in ("", "None")]
    if W5H:
        # (run5h: every weapon the chests gave, hers to wield or not, in the order found)
        found = []
        for e in S["events"]:
            if e["kind"] == "found":
                for x in e.get("items", []):
                    if kinds.get(x) == "weapon" and x not in found: found.append(x)
    two = [n_ for n_ in found if looks.get(n_, "").startswith("two handed")]
    ranged = [n_ for n_ in found if looks.get(n_, "").startswith("ranged")]
    melee = [n_ for n_ in found if n_ not in two and n_ not in ranged]
    event("found_weapons", two_handed=two, ranged=ranged, melee=melee)
    return {"found": found, "two": two, "ranged": ranged, "melee": melee, "looks": looks,
            "carried": [x.split("|")[1] for x in c.get_inventory_lines() if str(x).startswith("carried|")]}
def run5w():
    """(level 5, the weapons and tiers reel; the Warrior, who wields every weapon of the table) the great hall's chests
    that hold weapons, a two-handed sword wielded from the inventory and a fight with it, the bow and a fight from range,
    a weapon that breaks; then tier 2's last set: its sealed grating into tier 3, the last monster, the tier opening, and
    on into tier 3"""
    gen, p = G["gen"], G["pawn"]
    f = yield from hall(); c = G["combat"]
    two, ranged, melee, found = f["two"], f["ranged"], f["melee"], f["found"]
    # ---- a two-handed sword from the inventory, shown round her, and a fight with it
    seg("weapon")
    first = (two or melee or found or [None])[0]
    # (the tiers' part needs its last 24 s: what comes before it is cut short as the time goes; fights stop at the deadline)
    jump_by = DUR - 24.0; G["until"] = jump_by
    if first:
        yield from wield(first)
        yield from swing_to(150.0, 0.7, -9.0); yield from orbit(3.2, 150.0, 200.0, -8.0)
    yield from fights_w(1, 4, 25)
    # ---- the bow, and a fight from range
    if ranged and T() < jump_by - 18.0:
        yield from wield(ranged[0])
        yield from swing_to(120.0, 0.6, -9.0); yield from orbit(2.4, 120.0, 120.0, -8.0)
        yield from fights_w(1, 4, 60)
    # ---- a weapon that breaks (the reel starts it at 3 of its durability: a hit takes 1 off)
    brk = (melee or two or [None])[0]
    if brk and brk in [str(x.name) for x in gen.get_editor_property("weapons")] and T() < jump_by - 14.0:
        if str(c.get_weapon_name()) != brk: yield from wield(brk)
        i = c.get_weapon_index(); c.set_weapon_wear(i, 3.0); event("wear_set", weapon=brk, wear=3.0, durability=c.get_weapon_durability(i))
        while c.weapons_broken == 0 and T() < jump_by - 3.0:
            m = threat() or nearest_monster(IP(0, 0), 60)
            if m is None: break
            seg("fight"); G["casts0"] = c.attacks_made; yield from fight_w(m); seg("weapon")
        if c.weapons_broken: event("broke", weapon=str(c.last_broken), now=str(c.get_weapon_name()))
        yield from pause(1.2, lambda: camera(side=20.0, rate=70.0))
        # (the two-handed sword again: the list has no broken blade now)
        if first and first != brk and first in [str(x.name) for x in gen.get_editor_property("weapons")] and T() < jump_by - 4.0: yield from wield(first)
    yield from tiers_part()
def tiers_part():
    """(the weapons reels' last 24 s) behind a card, tier 2's eight sets generated, seven cleared outright and the eighth
    all but its last monster (the generator's debug clear); her at its grating into tier 3, that monster killed, the tier
    opening, and on into tier 3, generated ahead of her, to one of its monsters (endless: the run's end stops it)"""
    gen, p, c = G["gen"], G["pawn"], G["combat"]
    G["until"] = DUR + 1.0
    # ---- later: tier 2's eight sets (the reel's shortcut, behind a card: seven cleared outright, the eighth all but its
    # last monster, by the generator's debug clear), her at the eighth's grating into tier 3
    seg("jump"); event("jump")
    ring = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
    for xy in ring:
        if not gen.is_section_generated(IP(*xy)): gen.generate_section_now(IP(*xy))
    yield
    # (run5x: the start set too: since 2026-10-24 tier 2 opens only once it is cleared, and tier 3 only after tier 2)
    if W5X: gen.debug_clear_section(IP(0, 0), 0, V(0, 0, 0))
    for xy in ring[1:]: gen.debug_clear_section(IP(*xy), 0, V(0, 0, 0))
    s10 = gen.get_section(IP(1, 0)); pts, kinds_ = s10.get_seal_points()
    east = [b for b, k in zip(list(pts), list(kinds_)) if k == 1 and b.x > s10.get_section_min().x + 20000.0]
    b = min(east, key=lambda q: abs(q.y - (s10.get_section_min().y + 12600.0))) if east else None
    gen.debug_clear_section(IP(1, 0), 1, b if b else V(0, 0, 0))
    if b is None: event("no_grating"); return
    out = V(1, 0, 0); st = V(b.x - 450.0, b.y, 100.0)
    p.set_actor_location(st, False, True); G["heading"] = 0.0; p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=0.0), True)
    G["cam_yaw"] = -18.0; G["cam_pitch"] = -14.0; c.set_health(c.get_max_health())
    event("at_grating", at=[round(b.x), round(b.y)])
    yield from pause(3.4, lambda: camera(side=-18.0, pitch=-14.0, rate=1e6))       # (the overlay's card is over this until 3.0 s)
    seg("tiers")
    t0 = T()
    while T() - t0 < 1.6: move(V(b.x - 120.0, b.y, 100.0), run=False); camera(side=-18.0, pitch=-12.0, rate=60.0); yield
    yield from pause(2.4, lambda: camera(side=-30.0, pitch=-10.0, rate=40.0))
    # the set's last monster
    m = next((q for q in gen.get_monsters() if alive(q) and q.get_editor_property("section").get_editor_property("coord") == IP(1, 0)), None)
    if W5X and m is not None:
        # (run5x: fought in the room nearest the grating: in the hallway by it the camera, behind her as she faced a
        # monster coming down the hallway, was pushed into her against the grating and the walls)
        rooms = [i for i in range(s10.get_num_rooms()) if "unction" not in s10.get_room_kind(i)]
        if rooms:
            rc_ = min((s10.get_room_center(i) for i in rooms), key=lambda q: d2(q, b)); rc_ = V(rc_.x, rc_.y, 100.0)
            event("to_room", at=[round(rc_.x), round(rc_.y)])
            ag_ = (gen.get_editor_property("aggro_distance"), gen.get_editor_property("lose_distance")); G["quiet"] = True
            gen.set_editor_property("aggro_distance", 0.0); gen.set_editor_property("lose_distance", 1.0)
            yield from to_point(rc_, 8.0, 150.0)
            gen.set_editor_property("aggro_distance", ag_[0]); gen.set_editor_property("lose_distance", ag_[1]); G["quiet"] = False
    if m is not None:
        event("last_monster", monster=str(m.monster_name), m=round(d2(loc(), m.get_actor_location()) / 100.0))
        seg("fight"); G["casts0"] = c.attacks_made; yield from (fight(m) if HERO == "Mage" else fight_w(m)); seg("tiers")
    yield from pause(1.5, lambda: camera(side=15.0, rate=60.0))
    # back to the grating, gone now, and on into tier 3
    route = Route(path(loc(), V(b.x - 120.0, b.y, 100.0)) + [V(b.x + 600.0, b.y, 100.0), V(b.x + 2400.0, b.y, 100.0)])
    t3 = gen.world_to_section(V(b.x + 600.0, b.y, 100.0)); hunted = False
    while True:
        m = threat()
        if m is None and not hunted and loc().x > b.x + 1200.0 and gen.is_section_generated(t3) and not gen.get_section(t3).is_building():
            # (in tier 3: the nearest of its monsters, stronger than tier 2's)
            m = nearest_monster(t3, 40); hunted = True
            if m is not None: event("tier3_monster", monster=str(m.monster_name), m=round(d2(loc(), m.get_actor_location()) / 100.0))
        if m is not None: seg("fight"); G["casts0"] = c.attacks_made; yield from (fight(m) if HERO == "Mage" else fight_w(m)); seg("tiers")
        if W5X and not G.get("map3") and hunted and m is None and loc().x > b.x + 1500.0:
            # (run5x: the big map once in tier 3: its rooms written TIER 3)
            G["map3"] = True; gen.set_map_open(True); key_hit("m"); event("map", open=True)
            yield from pause(2.8, lambda: camera(side=-10.0, pitch=-15.0, rate=40.0))
            gen.set_map_open(False); key_hit("m"); event("map", open=False)
        if W5X and loc().x > b.x - 260.0 and not (gen.is_section_generated(t3) and not gen.get_section(t3).is_building()):
            # (run5x: she waits at the opened grating until the set beyond is built: walking on, the camera went into the
            # hallway while the set was still being built over frames and the whole picture was the void for a second)
            if not G.get("waited"): G["waited"] = True; event("wait_built", section=[t3.x, t3.y])
            camera(side=-10.0, pitch=-15.0, rate=60.0); yield; continue
        move(pulled(route), run=True); doors(); camera(side=-10.0, pitch=-15.0, rate=80.0); yield

def linger():
    """(run5h) to the end of her run: what comes at her, else the nearest monster of the start square while there is
    time for a fight, else she stands with the camera easing round her (endless: the run's end stops it)"""
    c = G["combat"]
    while True:
        m = threat()
        if m is None and T() < DUR - 8.0: m = nearest_monster(IP(0, 0), 60, 3000.0)
        if m is not None:
            seg("fight"); G["casts0"] = c.attacks_made
            yield from (fight(m) if HERO == "Mage" else fight_w(m)); seg("weapon"); continue
        yield from pause(0.5, lambda: camera(side=40.0, pitch=-11.0, rate=12.0))
def heaviest_armour(weights, lightest=False):
    """(run5h) the heaviest (or lightest) set she carries of those weights"""
    gen = G["gen"]; order = {"light": 0, "medium": 1, "heavy": 2}
    wt = {str(it.name): str(it.armour_weight.name).lower() for it in gen.get_editor_property("items") if it.kind == unreal.RDItemKind.ARMOUR}
    have = [str(x).split("|")[1] for x in G["combat"].get_inventory_lines() if str(x).startswith("armour|")]
    cand = [n_ for n_ in have if wt.get(n_) in weights]
    if not cand: return None
    return (min if lightest else max)(cand, key=lambda n_: order[wt[n_]])
def run5h():
    """(level 5, the four heroes' weapons reel) the great hall's chests that hold weapons (the same seed for every hero:
    the same weapons), then what the rules let her hero do with them (the weapons table's "who": the Warrior and the
    Warlock wield every weapon, the Rogue short blades and ranged weapons, the Mage none; armour is fitted to the
    Summoner only)"""
    gen = G["gen"]
    f = yield from hall(); c = G["combat"]
    looks = f["looks"]
    kind_of = lambda n_: looks.get(n_, "").split("  ")[0]
    two, ranged = f["two"], f["ranged"]
    short = [n_ for n_ in f["found"] if kind_of(n_) == "short blades"]
    swords = [n_ for n_ in f["found"] if kind_of(n_) in ("short sword", "one handed sword", "curved and eastern sword")]
    tiers = HERO == "Rogue"
    G["until"] = DUR - 29.0 if tiers else DUR + 1.0       # (the Rogue's run ends with the bow drawn and the tiers' part: its last 29 s)
    seg("weapon")
    if HERO == "Warrior":
        # the heaviest set the chests gave (she wears all armour), shown round her; then the two-handed sword and the
        # bow, a kill with each
        arm = heaviest_armour(["light", "medium", "heavy"])
        if arm:
            yield from wield(arm, "armour", "armour")
            yield from swing_to(150.0, 0.7, -9.0); yield from orbit(3.0, 150.0, 200.0, -8.0)
        if two:
            yield from wield(two[0])
            yield from swing_to(150.0, 0.7, -9.0); yield from orbit(3.0, 150.0, 200.0, -8.0)
        lure()
        yield from fights_w(1, 4, 25)
        if ranged and T() < DUR - 12.0:
            yield from wield(ranged[0])
            yield from swing_to(120.0, 0.6, -9.0); yield from orbit(2.2, 120.0, 110.0, -8.0)
            yield from fights_w(1, 4, 60)
    elif HERO == "Mage":
        # none of the table's weapons: Enter on one says so; her spells, and a mana potion when her mana is down
        nm = (two or swords or ranged or short or [None])[0]
        if nm: yield from refuse("carried", nm)
        arm = heaviest_armour(["light", "medium", "heavy"], lightest=True)       # (she wears none: Enter says so)
        if arm: yield from refuse("armour", arm)
        lure()
        yield from fights_w(1, 4)
        mp = next((str(x).split("|")[1] for x in c.get_inventory_lines() if str(x).startswith("item|") and "Mana" in str(x)), None)
        if mp and c.get_mana() < c.get_max_mana() - 1.0 and T() < DUR - 6.0: yield from wield(mp, "item", "item")
    elif HERO == "Warlock":
        # a found short sword, started at 3 of its durability: it breaks on her third hit
        brk = (swords or two or [None])[0]
        no = heaviest_armour(["heavy"])
        if no: yield from refuse("armour", no)
        arm = heaviest_armour(["light", "medium"])
        if arm:
            yield from wield(arm, "armour", "armour")
            yield from swing_to(140.0, 0.6, -9.0); yield from orbit(2.4, 140.0, 140.0, -8.0)
        if brk:
            yield from wield(brk)
            yield from swing_to(140.0, 0.6, -9.0); yield from orbit(2.4, 140.0, 140.0, -8.0)
            i = c.get_weapon_index(); c.set_weapon_wear(i, 3.0); event("wear_set", weapon=brk, wear=3.0, durability=c.get_weapon_durability(i))
            lure()
            while c.weapons_broken == 0 and T() < DUR - 3.0:
                m = threat() or nearest_monster(IP(0, 0), 60)
                if m is None: break
                seg("fight"); G["casts0"] = c.attacks_made; yield from fight_w(m); seg("weapon")
            if c.weapons_broken: event("broke", weapon=str(c.last_broken), now=str(c.get_weapon_name()))
            yield from pause(1.2, lambda: camera(side=20.0, rate=70.0))
    elif HERO == "Rogue":
        # the two-handed sword is not hers (Enter says so); the dagger she found and a kill with it; the bow; the tiers
        nm = (two or swords or [None])[0]
        if nm: yield from refuse("carried", nm)
        no = heaviest_armour(["medium", "heavy"])
        if no: yield from refuse("armour", no)
        arm = heaviest_armour(["light"])
        if arm: yield from wield(arm, "armour", "armour")
        if short:
            yield from wield(short[0])
            yield from swing_to(140.0, 0.6, -9.0); yield from orbit(2.4, 140.0, 140.0, -8.0)
            lure()
            yield from fights_w(1, 4, 40)
            lure(False)                                  # (the tiers' part as the weapons and tiers reel has it)
        if ranged: yield from wield(ranged[0])         # (tier 2's last monster and tier 3's from range: the knife does 11 a blow)
        yield from tiers_part()
    G["until"] = DUR + 1.0
    yield from linger()

CRAFT_SET = {"Warrior": "Templar\u2019s Armour", "Warlock": "Eastern Knight\u2019s Armour", "Rogue": "Desert Hero\u2019s Armour", "Mage": "Templar\u2019s Armour"}
CRAFT_RECIPE = {"Warrior": "Patch Kit", "Warlock": "Whetstone", "Rogue": "Slickstone", "Mage": "Leather Strips"}
def to_point(at, sec=10.0, near=60.0):
    """(run5c) walks to `at` by her section's tile path (one coming at her on the way is fought, unless the monsters are
    quiet: then she walks on)"""
    route = Route(path(loc(), at) + [at]); t0 = T()
    while d2(loc(), at) > near and T() - t0 < sec:
        m = None if G.get("quiet") else threat()
        if m is not None and m.is_aggro():
            tf = T(); seg("fight"); G["casts0"] = G["combat"].attacks_made
            if W5S: yield from s5_fight(m, ["Frost Shard", "Fire"] if HERO == "Mage" else None)
            else: yield from (fight(m) if HERO == "Mage" else fight_w(m))
            seg(S["seg_back"])
            route = Route(path(loc(), at) + [at]); t0 += T() - tf
        move(pulled(route), run=d2(loc(), at) > 250.0); doors(); camera(side=-20.0, pitch=-18.0, rate=90.0); yield
def repair_beat(c, lines, want, recipe, pick):
    """(run5c) I, down to the repair item, Enter: the repair list; down to her set, Enter: mended; I"""
    event("inventory", lines=lines, want=want, why="repair", item=recipe, hp=round(c.get_health(), 1), mana=round(c.get_mana(), 1))
    c.set_inventory_open(True); key_hit("i")
    yield from pause(0.8)
    while want is not None and c.get_inventory_cursor() != want:
        down = want > c.get_inventory_cursor(); far = abs(want - c.get_inventory_cursor()) > 3
        c.move_inventory_cursor(1 if down else -1); key_hit("s" if down else "w"); yield from pause(0.12 if far else 0.32)
    yield from pause(1.4)
    ok = c.use_inventory_entry(); key_hit("enter")
    event("used", entry=lines[want] if want is not None else "", ok=bool(ok), message=str(c.message), hp=round(c.get_health(), 1), mana=round(c.get_mana(), 1))
    yield from pause(1.4)
    if c.is_picking_repair():
        rl = [str(x) for x in c.get_repair_lines()]; ti = next((i for i, x in enumerate(rl) if x.startswith("armour|" + pick + "|")), 0)
        while c.get_repair_cursor() != ti: c.move_repair_cursor(1); key_hit("s"); yield from pause(0.35)
        yield from pause(1.0)
        b = c.get_armour_wear(pick); ok = c.repair_entry(-1); key_hit("enter")
        event("repaired", set=pick, ok=bool(ok), before=b, after=c.get_armour_wear(pick), durability=c.get_armour_durability(pick), message=str(c.message), share=round(c.get_armour(), 3))
        yield from pause(2.0)
    c.set_inventory_open(False); key_hit("i")
def run5c():
    """(level 5, the armour table, loot and crafting reel) see the docstring: way "craft" """
    gen, p = G["gen"], G["pawn"]
    seg("start")
    while T() <= 0.0 or G["combat"] is None:
        camera(rate=1e6); yield
    def start_count(): return sum(1 for q in gen.get_monsters() if alive(q) and q.get_editor_property("section").get_editor_property("coord") == IP(0, 0))
    while T() < 0.5 or (start_count() < 10 and T() < 1.2):
        camera(rate=1e6); yield
    c = G["combat"]; c.set_inventory_open(False); c.set_crafting_open(False); G["until"] = DUR + 1.0
    s0 = gen.get_section(IP(0, 0)); centre = gen.get_start_room_center(); hall_room = s0.room_at(centre)
    anvil = next((a for a in s0.get_anvil_points() if s0.room_at(a) == hall_room), None)
    hall = list(gen.get_start_room_containers())
    lists = {i: [str(x) for x in gen.loot_list_of(IP(0, 0), i)] for i in hall}
    S["note"]["hall"] = {str(i): v for i, v in lists.items()}
    pick = CRAFT_SET[HERO]; recipe = CRAFT_RECIPE[HERO]
    # ---- the start: by the hall's anvil, facing it
    a0 = anvil or centre; tow = V(centre.x - a0.x, centre.y - a0.y, 0.0)
    st = V(a0.x + tow.normal().x * 520.0, a0.y + tow.normal().y * 520.0, 100.0) if tow.length() > 1 else V(a0.x + 520.0, a0.y, 100.0)
    p.set_actor_location(st, False, True); G["heading"] = yaw_to(st, a0); p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), True)
    G["cam_yaw"] = G["heading"] - 25.0; G["cam_pitch"] = -20.0
    event("start", at=[round(st.x), round(st.y)], anvil=[round(a0.x), round(a0.y)] if anvil else None, hall=hall, way="great hall, by its anvil")
    yield from pause(3.0, lambda: camera(side=-25.0, pitch=-20.0, rate=40.0))
    # ---- the big map: each room's tier, the anvil
    seg("map"); gen.set_map_open(True); key_hit("m"); event("map", open=True)
    yield from pause(4.2, lambda: camera(side=-25.0, pitch=-20.0, rate=20.0))
    gen.set_map_open(False); key_hit("m"); event("map", open=False)
    # ---- the hall's containers that hold her set, and the nearest other
    seg("chest")
    with_set = [i for i in hall if pick in lists[i]]
    others = sorted((i for i in hall if i not in with_set), key=lambda i: d2(loc(), s0.get_container_location(i)))
    tour = (with_set[:1] + others[:1]) or others[:2]
    tour.sort(key=lambda i: d2(loc(), s0.get_container_location(i)))
    event("tour", containers=tour, lists={str(i): lists[i] for i in tour})
    for i in tour:
        if s0.is_target_open(False, i): continue
        at = s0.get_container_location(i); st_ = stand_by_chest(at, loc(), tol=450.0)
        if st_ is None: event("chest_missed", why="no place to stand", container=i); continue
        S["seg_back"] = "chest"; yield from open_chest(at, st_)
        yield from pause(0.4, lambda: camera(side=-30.0, pitch=-26.0, rate=70.0))
    if c.get_item_count(pick) == 0: c.add_item(pick, 1); event("given", items={pick: 1}, why="armour")
    # ---- her set on (the Mage: refused), the camera round her
    seg("armour")
    if HERO == "Mage": yield from refuse("armour", pick)
    else:
        yield from wield(pick, "armour", "armour")
        yield from swing_to(150.0, 0.6, -9.0); yield from orbit(2.6, 150.0, 200.0, -8.0)
    # (in play the crafting panel and the inventory pause the game; the reel's world goes on: from here to the jump the
    # monsters leave her be, the "quiet" event, said by the caption)
    if "aggro0" not in G: G["aggro0"] = (gen.get_editor_property("aggro_distance"), gen.get_editor_property("lose_distance"))
    gen.set_editor_property("aggro_distance", 0.0); gen.set_editor_property("lose_distance", 1.0); event("quiet", on=True); G["quiet"] = True
    # ---- the reel wears the set down (the Warrior's to 0: worn out)
    if HERO != "Mage":
        seg("wear"); w = 0.0 if HERO == "Warrior" else 60.0; before = c.get_armour_wear(pick)
        c.set_armour_wear(pick, w)
        event("wear_set", set=pick, before=before, wear=w, durability=c.get_armour_durability(pick), share=round(c.get_armour(), 3))
        yield from pause(1.0, lambda: camera(side=20.0, rate=60.0))
    # ---- to the anvil, F: the crafting panel; down to her recipe; given what it lacks; made
    seg("craft"); S["seg_back"] = "craft"
    stand = None
    if anvil is not None:
        for r_ in (150.0, 190.0):
            for k in range(16):
                q = V(anvil.x + math.cos(k * math.pi / 8) * r_, anvil.y + math.sin(k * math.pi / 8) * r_, 100.0)
                if s0.room_at(q) == hall_room and str(gen.describe_nearest(q, 260.0)) == "use the anvil" and len(path(loc(), q)):
                    if stand is None or d2(loc(), q) < d2(loc(), stand): stand = q
            if stand: break
    if stand is not None: yield from to_point(stand, 15.0, 45.0)
    G["heading"] = yaw_to(loc(), anvil) if anvil else G["heading"]; p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), False)
    yield from pause(0.4, lambda: camera(side=-35.0, pitch=-22.0, rate=70.0))
    said = str(gen.interact_nearest(loc(), 260.0)); key_hit("f"); event("craft_open", what=said, open=bool(c.is_crafting_open()))
    yield from pause(1.4)
    ri = next((i for i, x in enumerate(c.get_craft_lines()) if str(x).split("|")[1] == recipe), 0)
    while c.get_craft_cursor() != ri:
        c.move_craft_cursor(1 if ri > c.get_craft_cursor() else -1); key_hit("s"); yield from pause(0.4)
    yield from pause(1.8)
    rc = next(r_ for r_ in gen.get_editor_property("recipes") if str(r_.item) == recipe)
    give = {}
    for pt in rc.parts:
        have = sum(c.get_item_count(k_) for k_ in pt.any_of)
        if have < pt.count:
            kinds_ = [str(k_) for k_ in pt.any_of]; lack = pt.count - have
            for j, k_ in enumerate(kinds_):        # (wood of any kind: spread over its kinds)
                n_ = lack // len(kinds_) + (1 if j < lack % len(kinds_) else 0)
                if n_: give[k_] = give.get(k_, 0) + n_
    for k_, n_ in give.items(): c.add_item(k_, n_)
    event("given", items=give, why="craft", recipe=recipe)
    yield from pause(2.0)
    ok = c.craft_entry(); key_hit("enter"); event("crafted", item=recipe, ok=bool(ok), message=str(c.message), have=c.get_item_count(recipe))
    yield from pause(1.8)
    c.set_crafting_open(False); key_hit("f")
    yield from pause(0.6, lambda: camera(side=20.0, rate=60.0))
    # ---- the inventory: the repair item, the repair list, the set mended (the Mage wears no armour: no repair beat)
    if HERO == "Mage": want = None
    seg("repair") if HERO != "Mage" else None
    lines = [str(x) for x in c.get_inventory_lines()]
    want = next((i for i, x in enumerate(lines) if x.startswith("repair|" + recipe + "|")), None) if HERO != "Mage" else None
    if HERO != "Mage":
        yield from repair_beat(c, lines, want, recipe, pick)
    yield from pause(1.6, lambda: camera(side=25.0, pitch=-12.0, rate=25.0))
    # ---- behind a card: a room of a tier-2 set of rooms (its tier on the maps)
    seg("jump"); event("jump")
    a0_, l0_ = G["aggro0"]; gen.set_editor_property("aggro_distance", a0_); gen.set_editor_property("lose_distance", l0_); event("quiet", on=False); G["quiet"] = False
    S1 = IP(1, 0)
    if not gen.is_section_generated(S1): gen.generate_section_now(S1)
    yield
    s1 = gen.get_section(S1); t0 = T()
    while (s1 is None or s1.is_building()) and T() - t0 < 6.0: yield; s1 = gen.get_section(S1)
    rooms = [i for i in range(s1.get_num_rooms()) if s1.get_room_kind(i) != "Hallway junction"] if s1 else []
    mn = s1.get_section_min() if s1 else V(0, 0, 0)
    rooms.sort(key=lambda i: s1.get_room_center(i).x - mn.x + 0.3 * abs(s1.get_room_center(i).y - centre.y))
    land = None
    for i in rooms:
        q = s1.get_room_center(i); q = V(q.x, q.y, 100.0)
        if sweep_clear(q, V(q.x + 300.0, q.y, 100.0), 40.0): land = q; break
    if land is None and rooms: q = s1.get_room_center(rooms[0]); land = V(q.x, q.y, 100.0)
    if land is not None:
        p.set_actor_location(land, False, True); G["heading"] = 0.0; p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=0.0), True)
        G["cam_yaw"] = -20.0; G["cam_pitch"] = -16.0; c.set_health(c.get_max_health())
    event("landed", at=[round(land.x), round(land.y)] if land else None, section=[1, 0], tier=gen.tier_of(S1))
    yield from pause(3.4, lambda: camera(side=-20.0, pitch=-16.0, rate=1e6))        # (the overlay's card is over this until 3.0 s)
    seg("tier2")
    t1 = T()
    while T() - t1 < 1.8: move(V(loc().x + 400.0, loc().y, 100.0), run=False); camera(side=-20.0, pitch=-14.0, rate=60.0); yield
    gen.set_map_open(True); key_hit("m"); event("map", open=True)
    yield from pause(4.0, lambda: camera(side=-20.0, pitch=-14.0, rate=20.0))
    gen.set_map_open(False); key_hit("m"); event("map", open=False)
    # ---- a fight in tier 2 (lured): the blows that reach her wear the mended set down, 1 each
    seg("fight"); lure()
    tw = T()
    while threat() is None and T() - tw < 5.0: camera(side=25.0, pitch=-12.0, rate=25.0); yield
    for _ in range(4):
        m = threat() or nearest_monster(S1, 40, 3000.0) or nearest_monster(None, 40, 3000.0)
        if m is None: break
        first = not any(e["kind"] == "blow_on_her" for e in S["events"])
        G["casts0"] = c.attacks_made; yield from (fight(m, take=2 if first else 0) if HERO == "Mage" else fight_w(m, take=2 if first else 0))
    yield from linger()

# ---------------------------------------------------------------- run5s: spells, rings, monsters by tier, corpses, the menu
# (what each hero is given by the reel when the containers on her way do not hold it: said by the captions)
S5_WANT = {"Warrior": {"ring": "HP Potency Ring 10", "tomes": ["Tome of Fire Bolt"], "two": "Plate Knight's Sword"},
           "Mage": {"ring": "Magic Potency Ring 10", "tomes": ["Tome of Ash Ward", "Tome of Frost Shard", "Tome of Chain Lightning", "Tome of Fireball", "Tome of Raise Dead", "Tome of Meteor Storm"]},
           "Warlock": {"ring": "Magic Potency Ring 10", "tomes": ["Tome of Curse of Frailty", "Tome of Shadow Lash", "Tome of Ash Ward"]},
           "Rogue": {"ring": "Dexterity Ring 10", "tomes": ["Tome of Frost Shard"]}}
# (the tier-3 monster she meets after the card: one whose blows carry the ability her part shows)
S5_ABILITY = {"Warrior": "Slow", "Mage": None, "Warlock": "Weaken", "Rogue": "Poison"}
S5_PLAN = {"Mage": ["Ash Ward", "Frost Shard", "Chain Lightning", "Fireball", "Fire"], "Warlock": ["Curse of Frailty"], "Mage3": ["Meteor Storm", "Fireball", "Chain Lightning", "Frost Shard", "Fire"]}
SELF_KINDS = ("WARD", "SKIN", "MIRROR", "VEIL", "RUNE", "PACT", "SANCTUM", "DISPEL", "RAISE", "KNIGHT", "NOVA")
def wi_of(name):
    return next((i for i, d in enumerate(G["gen"].get_editor_property("weapons")) if str(d.name) == name), None)
def spell_kind(wi):
    d = G["gen"].get_editor_property("weapons")[wi]; sp = G["gen"].get_editor_property("spells")
    return str(sp[d.spell_index].kind.name) if 0 <= d.spell_index < len(sp) else ""
def draw(wi):
    """the key that draws weapon wi (1 to 0)"""
    c = G["combat"]
    if wi is not None and c.get_weapon_index() != wi: c.select_weapon(wi); key_hit(str((wi + 1) % 10))
def fight_s(m, plan, max_t=20.0, then_sword=False, take=0):
    """(run5s) spells by her plan, in order: each cast once (one on cooldown or wanting mana is passed over), the last
    over and over; a spell cast on herself (a ward, the dead raised) needs no sight of it; then_sword: after the plan the
    Warlock draws her sword (1) and finishes it"""
    c = G["combat"]; p = G["pawn"]; gen = G["gen"]; n = G["fights"]; G["fights"] += 1
    name = str(m.monster_name); hp0 = m.get_max_health(); h0 = c.get_health(); t0 = T(); b0 = c.hits_landed
    event("fight", monster=name, title=str(m.title), its_hit_points=hp0, its_damage=m.get_damage(), ability=str(m.ability.name), tier=m.tier,
          section=[m.get_editor_property("section").get_editor_property("coord").x, m.get_editor_property("section").get_editor_property("coord").y],
          from_m=round((d2(loc(), m.get_actor_location())) / 100.0, 1), spells=plan, sword=then_sword)
    k = 0; route = None; rt = -9.0; ws = gen.get_editor_property("weapons"); taken0 = c.hits_taken; held = None
    while alive(m) and not c.is_dead() and T() - t0 < max_t and T() < G.get("until", DUR + 1.0):
        l = loc(); ml = m.get_actor_location(); gap = d2(l, ml) - m.capsule_component.get_scaled_capsule_radius()
        o = threat()
        if o is not None and o != m and o.is_aggro() and d2(l, o.get_actor_location()) + 200.0 < d2(l, ml): m = o; continue     # (one nearer on her: that one)
        G["heading"] = yaw_to(l, ml)
        face = lambda: p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=turn(p.get_actor_rotation().yaw, yaw_to(l, ml), 720.0 * G["el"])), False)
        if not c.is_attacking():
            if then_sword and k >= len(plan):
                # (the Warlock: the sword now; fire from her left hand when it is far)
                draw(0)
                if take and c.hits_taken - taken0 < take and gap < 260.0 and (held is None or T() - held < 5.0):
                    held = held if held is not None else T(); face()          # (she lets its blows land: what they carry shows)
                elif gap < ws[0].reach - 10.0: face(); c.start_attack() and key_hit("lmb")
                else:
                    if route is None or T() - rt > 0.6: route = Route(path(l, ml)); rt = T()
                    move(route.target() if len(route.p) > 1 and gap > 300.0 else ml, run=True); doors()
            else:
                nm = plan[min(k, len(plan) - 1)]; wi = wi_of(nm)
                if wi is None: k += 1; yield; continue
                wd = ws[wi]; kind = spell_kind(wi)
                if (c.get_cooldown_left(wi) > 0.0 or c.get_mana() < wd.mana_cost) and k < len(plan) - 1: k += 1; yield; continue
                if c.get_mana() < wd.mana_cost:
                    # (the last of her plan wants more mana than she has: she waits for it, facing the monster)
                    face(); camera(side=20.0, pitch=-14.0, rate=40.0); yield; continue
                near = 360.0 if kind == "LASH" else CAST_GAP
                if kind in SELF_KINDS or (gap < near and sees(l, m)):
                    face(); draw(wi)
                    if c.start_attack(): key_hit("lmb" if HERO == "Warlock" else "e"); k += 1
                else:
                    if route is None or T() - rt > 0.7: route = Route(path(l, ml)); rt = T()
                    move(route.target() if len(route.p) > 1 and gap > 400.0 else ml, run=True); doors()
        camera(side=(28.0 if n % 2 == 0 else -28.0) if wide_here() else 8.0, pitch=-14.0 if wide_here() else -25.0, rate=80.0)
        yield
    G["last_fight"] = T()
    if not alive(m): event("kill", monster=name, casts=c.attacks_made - G.get("casts0", 0), blows=c.hits_landed - b0, seconds=round(T() - t0, 2), she_lost=round(max(0.0, h0 - c.get_health())), its_hit_points=hp0)
    else: event("left", monster=name)
    yield from pause(0.5, lambda: camera(side=18.0, rate=70.0))
def s5_fight(m, plan=None, take=0):
    """(run5s) her kind of fight: the Mage her plan of spells, the Warlock a curse then the sword, the Warrior and the
    Rogue the weapon in hand (take: up close she lets that many of its blows land first)"""
    G["casts0"] = G["combat"].attacks_made; seg("fight")
    if HERO == "Mage": yield from fight_s(m, plan or S5_PLAN["Mage"])
    elif HERO == "Warlock" and plan: yield from fight_s(m, plan, then_sword=True, take=take)
    else: yield from fight_w(m, take=take)
def s5_fights(kills, plan_for=lambda i: None, tries=12, until=None):
    """(run5s) fights (lured) until `kills` monsters fell or the time for them is up (a fight still on then stops)"""
    c = G["combat"]; k0 = sum(1 for e in S["events"] if e["kind"] == "kill"); u0 = G.get("until", DUR + 1.0)
    if until is not None: G["until"] = until + 1.5
    try:
        yield from s5_fights_(kills, plan_for, tries, until, k0)
    finally: G["until"] = u0
def s5_fights_(kills, plan_for, tries, until, k0):
    for i in range(tries):
        if until is not None and T() > until - 4.0: return
        tw = T()
        while threat() is None and T() - tw < 2.0: camera(side=25.0, pitch=-12.0, rate=25.0); yield
        # (none on her yet: the nearest by her way, up to 80 m; she sets out after it, lured it comes too)
        m = threat() or nearest_monster(None, 110, 8000.0)
        if m is None: event("no_monster"); return
        yield from s5_fight(m, plan_for(i))
        if sum(1 for e in S["events"] if e["kind"] == "kill") - k0 >= kills: return
def look_at_corpse(sec=2.2):
    """(run5s) the last one killed lies where it fell: the camera turns to it"""
    gen = G["gen"]; l = loc()
    cs = list(gen.get_corpses_near(l, 2500.0))
    if not cs: return
    cp = min(cs, key=lambda q: d2(l, q.get_actor_location())); cl = cp.get_actor_location()
    event("corpse", monster=str(cp.monster_name), title=str(cp.title), at=[round(cl.x), round(cl.y)], m=round(d2(l, cl) / 100.0, 1), corpses=len(cs))
    G["heading"] = yaw_to(l, cl)
    yield from pause(sec, lambda: camera(side=0.0, pitch=-24.0, rate=60.0))
def empty_container():
    """(run5s) the nearest container of the start section on her way that holds nothing (two in three do), opened"""
    gen = G["gen"]; s0 = gen.get_section(IP(0, 0)); l = loc(); hall = set(gen.get_start_room_containers()); best = None
    for i in range(s0.get_num_containers()):
        if i in hall or s0.is_target_open(False, i) or len(gen.loot_list_of(IP(0, 0), i)): continue
        at = s0.get_container_location(i)
        if d2(at, l) > 2600.0: continue
        pts = path(l, at)
        if not 1 < len(pts) <= 14: continue
        if best is None or len(pts) < best[0]: best = (len(pts), i, at)
    if best is None: event("no_empty"); return
    _, i, at = best
    st_ = stand_by_chest(at, loc(), tol=450.0)
    if st_ is None: event("chest_missed", why="no place to stand", container=i); return
    event("empty_pick", container=i, ckind=str(s0.get_container_kind(i)), at=[round(at.x), round(at.y)])
    S["seg_back"] = "chest"; yield from open_chest(at, st_)
    event("empty_opened", container=i, ckind=str(s0.get_container_kind(i)), message=str(G["combat"].message))
    yield from pause(0.6, lambda: camera(side=-25.0, pitch=-22.0, rate=60.0))
def hall_chests(wanted, n=2):
    """(run5s) the great hall's containers that hold what her part needs (by the loot lists), the nearest first"""
    gen = G["gen"]; s0 = gen.get_section(IP(0, 0)); hall = list(gen.get_start_room_containers())
    lists = {i: [str(x) for x in gen.loot_list_of(IP(0, 0), i)] for i in hall}
    S["note"]["hall"] = {str(i): v for i, v in lists.items()}
    pick = [i for i in hall if any(w(x) for x in lists[i] for w in wanted)]
    pick.sort(key=lambda i: d2(loc(), s0.get_container_location(i)))
    event("tour", containers=pick[:n], lists={str(i): lists[i] for i in pick[:n]})
    for i in pick[:n]:
        if s0.is_target_open(False, i): continue
        at = s0.get_container_location(i); st_ = stand_by_chest(at, loc(), tol=450.0)
        if st_ is None: event("chest_missed", why="no place to stand", container=i); continue
        S["seg_back"] = "chest"; yield from open_chest(at, st_)
        yield from pause(0.4, lambda: camera(side=-30.0, pitch=-26.0, rate=70.0))
def give(items, why):
    """(run5s) what the reel gives her (the captions say so), one at a time: a tome she can learn is learned at once"""
    c = G["combat"]; got = {}
    for nm in items:
        if c.get_item_count(nm) > 0 or (nm.startswith("Tome of ") and c.knows_spell(nm[8:])): continue
        c.add_item(nm, 1); got[nm] = 1
        event("given", items={nm: 1}, why=why, message=str(c.message), learned=bool(nm.startswith("Tome of ") and c.knows_spell(nm[8:])))
        yield from pause(0.75, lambda: camera(side=-20.0, pitch=-16.0, rate=40.0))
    return got
def menu_beat():
    """(run5s) Esc: the menu over the game (paused in play; the reel's world goes on, the monsters quiet meanwhile); down to
    the music, its slider down to 40 % and the music falls with it; up again to 100 %; down past the buttons; Esc"""
    gen = G["gen"]; vol0 = [gen.get_user_volume(i) for i in range(4)]; G["vol0"] = vol0
    gen.set_menu_open(True); key_hit("esc"); event("menu", open=True, lines=[str(x) for x in gen.get_menu_lines()], pauses=bool(gen.get_editor_property("menu_pauses_game")))
    yield from pause(0.9)
    for _ in range(3): gen.move_menu_cursor(1); key_hit("s"); yield from pause(0.3)
    yield from pause(0.3)
    for _ in range(12): gen.step_menu_value(-1); key_hit("a"); yield from pause(0.1)
    event("volume", line=3, value=round(gen.get_user_volume(3), 2)); yield from pause(1.9)
    for _ in range(12): gen.step_menu_value(1); key_hit("d"); yield from pause(0.06)
    event("volume", line=3, value=round(gen.get_user_volume(3), 2)); yield from pause(0.4)
    for _ in range(3): gen.move_menu_cursor(1); key_hit("s"); yield from pause(0.35)
    yield from pause(0.7)
    for i in range(4): gen.set_user_volume(i, vol0[i])          # (as it was: the menu saves the volumes for the next session)
    gen.set_menu_open(False); key_hit("esc"); event("menu", open=False)
    yield from pause(0.4)
def breakdown_beat(weapon):
    """(run5s) F at the hall's anvil: the panel's BREAK DOWN part; down to the weapon; Enter: it is gone, its materials in
    her bag"""
    gen, p, c = G["gen"], G["pawn"], G["combat"]
    s0 = gen.get_section(IP(0, 0)); centre = gen.get_start_room_center(); hall_room = s0.room_at(centre)
    anvil = next((a for a in s0.get_anvil_points() if s0.room_at(a) == hall_room), None)
    if anvil is None: event("no_anvil"); return
    stand = None
    for r_ in (150.0, 190.0):
        for k in range(16):
            q = V(anvil.x + math.cos(k * math.pi / 8) * r_, anvil.y + math.sin(k * math.pi / 8) * r_, 100.0)
            if s0.room_at(q) == hall_room and str(gen.describe_nearest(q, 260.0)) == "use the anvil" and len(path(loc(), q)):
                if stand is None or d2(loc(), q) < d2(loc(), stand): stand = q
        if stand: break
    S["seg_back"] = "craft"
    if stand is not None: yield from to_point(stand, 14.0, 45.0)
    G["heading"] = yaw_to(loc(), anvil); p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), False)
    yield from pause(0.3, lambda: camera(side=-35.0, pitch=-22.0, rate=70.0))
    said = str(gen.interact_nearest(loc(), 260.0)); key_hit("f"); event("craft_open", what=said, open=bool(c.is_crafting_open()))
    yield from pause(1.0)
    ri = next((i for i, x in enumerate(c.get_craft_lines()) if str(x).startswith("breakdown|" + weapon + "|")), None)
    while ri is not None and c.get_craft_cursor() != ri:
        far = abs(ri - c.get_craft_cursor()) > 3
        c.move_craft_cursor(1 if ri > c.get_craft_cursor() else -1); key_hit("s"); yield from pause(0.14 if far else 0.36)
    yield from pause(1.8)
    before = {str(x).split("|")[1]: str(x) for x in c.get_inventory_lines() if str(x).startswith("component|")}
    ok = c.craft_entry(); key_hit("enter")
    event("broken_down", weapon=weapon, ok=bool(ok), message=str(c.message), components=[str(x) for x in c.get_inventory_lines() if str(x).startswith("component|")], before=list(before.values()))
    yield from pause(2.2)
    c.set_crafting_open(False); key_hit("f")
    yield from pause(0.4, lambda: camera(side=20.0, rate=60.0))
def tier3_jump(ability):
    """(run5s) behind a card: a room of a tier-3 set, by one of its monsters whose blows carry `ability` (any for None);
    her hit points and mana full again (the card: later)"""
    gen, p, c = G["gen"], G["pawn"], G["combat"]
    seg("jump"); event("jump")
    if "aggro0" not in G: G["aggro0"] = (gen.get_editor_property("aggro_distance"), gen.get_editor_property("lose_distance"))
    gen.set_editor_property("aggro_distance", 0.0); gen.set_editor_property("lose_distance", 1.0)          # (nobody comes at her behind the card)
    S3 = IP(2, 0)
    if not gen.is_section_generated(S3): gen.generate_section_now(S3)
    yield
    s3 = gen.get_section(S3); t0 = T()
    while (s3 is None or s3.is_building()) and T() - t0 < 8.0: yield; s3 = gen.get_section(S3)
    yield from pause(0.4)
    ms = [m for m in (s3.spawned_monsters if s3 else []) if alive(m) and not m.is_ally()]
    want = [m for m in ms if ability is None or str(m.ability.name).lower() == ability.lower()]
    # (the Mage: the monster with the most others round it, for the meteors)
    if ability is None and ms: want = sorted(ms, key=lambda m: -sum(1 for q in ms if d2(q.get_actor_location(), m.get_actor_location()) < 1200.0))
    land = None; tgt = None
    for m in want[:6]:
        ml = m.get_actor_location()
        for r_ in (1000.0, 800.0, 1200.0, 650.0):
            for k in range(12):
                q = V(ml.x + math.cos(k * math.pi / 6) * r_, ml.y + math.sin(k * math.pi / 6) * r_, 100.0)
                if s3.room_at(q) < 0 or not clear_line(q, ml) or not sweep_clear(q, V(q.x + 10.0, q.y, 100.0), 45.0): continue
                land, tgt = q, m; break
            if land: break
        if land: break
    if land is None: event("no_landing", ability=ability); return None
    p.set_actor_location(land, False, True); G["heading"] = yaw_to(land, tgt.get_actor_location()); p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), True)
    G["cam_yaw"] = G["heading"] - 20.0; G["cam_pitch"] = -16.0; c.set_health(c.get_max_health()); c.set_mana(c.get_max_mana())
    event("landed", at=[round(land.x), round(land.y)], section=[2, 0], tier=gen.tier_of(S3), monster=str(tgt.monster_name), title=str(tgt.title), ability=str(tgt.ability.name),
          its_hit_points=tgt.get_max_health(), its_damage=tgt.get_damage(), power=round(tgt.ability_power, 2))
    yield from pause(3.4, lambda: camera(side=-20.0, pitch=-16.0, rate=1e6))        # (the overlay's card is over this until 3.0 s)
    seg("tier3")
    return tgt
def run5s():
    """(level 5, the spells, rings, monsters and menu reel) see the docstring: way "spells" """
    gen, p = G["gen"], G["pawn"]
    seg("start")
    while T() <= 0.0 or G["combat"] is None:
        camera(rate=1e6); yield
    def start_count(): return sum(1 for q in gen.get_monsters() if alive(q) and q.get_editor_property("section").get_editor_property("coord") == IP(0, 0))
    while T() < 0.5 or (start_count() < 10 and T() < 1.2):
        camera(rate=1e6); yield
    c = G["combat"]; c.set_inventory_open(False); c.set_crafting_open(False); G["until"] = DUR + 1.0
    gen.set_editor_property("menu_pauses_game", False)
    s0 = gen.get_section(IP(0, 0)); centre = gen.get_start_room_center(); hall_room = s0.room_at(centre)
    anvil = next((a for a in s0.get_anvil_points() if s0.room_at(a) == hall_room), None)
    want = S5_WANT[HERO]
    # ---- the start: in the great hall, by its anvil
    a0 = anvil or centre; tow = V(centre.x - a0.x, centre.y - a0.y, 0.0)
    st = V(a0.x + tow.normal().x * 520.0, a0.y + tow.normal().y * 520.0, 100.0) if tow.length() > 1 else V(a0.x + 520.0, a0.y, 100.0)
    p.set_actor_location(st, False, True); G["heading"] = yaw_to(st, a0); p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), True)
    G["cam_yaw"] = G["heading"] - 25.0; G["cam_pitch"] = -20.0
    event("start", at=[round(st.x), round(st.y)], anvil=[round(a0.x), round(a0.y)] if anvil else None, way="great hall, by its anvil",
          learns=[str(x.name) for h_ in gen.get_editor_property("heroes") if str(h_.name) == HERO for x in h_.learns],
          ring_kinds=[str(x.name) for h_ in gen.get_editor_property("heroes") if str(h_.name) == HERO for x in h_.ring_kinds])
    yield from pause(2.6, lambda: camera(side=-25.0, pitch=-20.0, rate=40.0))
    # ---- what the reel gives (said by the captions): a ring of tier 5, tomes (one she cannot learn says so as she takes
    # it); the Warrior a two-handed sword and a weapon to break down
    seg("given")
    yield from give([want["ring"]] + ([want["two"], "Viking Shortsword"] if HERO == "Warrior" else []), "ring")
    yield from give(want["tomes"], "tomes")
    # ---- the ring on, from the inventory
    seg("ring"); h0, m0 = c.get_max_health(), c.get_max_mana(); xb0 = None
    if HERO == "Rogue":
        xi = next((i for i, d in enumerate(gen.get_editor_property("weapons")) if d.spell and d.bolt_mesh), None); xb0 = c.get_damage_of(xi) if xi is not None else None
    yield from wield(want["ring"], "ring", "ring")
    ev_ = {"ring": want["ring"], "hp": [h0, c.get_max_health()], "mana": [m0, c.get_max_mana()]}
    if xb0 is not None: ev_["crossbow"] = [round(xb0, 1), round(c.get_damage_of(xi), 1)]
    event("ring_on", **ev_)
    yield from pause(1.6, lambda: camera(side=-20.0, pitch=-14.0, rate=30.0))
    if HERO == "Warrior":
        # ---- the anvil she stands by: the spare weapon broken down into materials
        seg("craft"); yield from breakdown_beat("Viking Shortsword")
    # ---- a container that holds nothing (one in three holds anything)
    seg("chest"); yield from empty_container()
    lure()
    if HERO == "Warrior":
        # ---- the two-handed sword (its cuts made again: the forearms clear of her body), a fight with it
        seg("weapon"); yield from wield(want["two"])
        yield from swing_to(150.0, 0.6, -9.0); yield from orbit(2.8, 150.0, 200.0, -8.0)
        yield from s5_fights(1, until=DUR - 31.0); yield from look_at_corpse()          # (one kill: the first monster may be 30 m off)
        # ---- Esc: the menu (the monsters quiet meanwhile: in play it pauses the game)
        gen.set_editor_property("aggro_distance", 0.0); gen.set_editor_property("lose_distance", 1.0); event("quiet", on=True); G["quiet"] = True
        seg("menu"); yield from menu_beat()
        G["quiet"] = False
    elif HERO == "Mage":
        # ---- her new spells in a fight: a ward on her, then frost, lightning, fire
        yield from s5_fights(99, until=DUR - 40.0); yield from look_at_corpse(1.6)
        # ---- the dead raised: Raise Dead by a corpse, the ally fights for her
        cs = list(gen.get_corpses_near(loc(), 3000.0)); wr = wi_of("Raise Dead")
        if cs and wr is not None:
            cp = min(cs, key=lambda q: d2(loc(), q.get_actor_location())); cl = cp.get_actor_location()
            if d2(loc(), cl) > 280.0: S["seg_back"] = "raise"; yield from to_point(V(cl.x, cl.y, 100.0), 6.0, 240.0)
            seg("raise"); G["heading"] = yaw_to(loc(), cl); p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), False)
            draw(wr); yield from pause(0.3)
            if c.get_mana() < gen.get_editor_property("weapons")[wr].mana_cost:
                tw = T()
                while c.get_mana() < gen.get_editor_property("weapons")[wr].mana_cost and T() - tw < 12.0: camera(side=30.0, pitch=-14.0, rate=20.0); yield
            ok = c.start_attack(); key_hit("e")
            yield from pause(1.2, lambda: camera(side=35.0, pitch=-14.0, rate=40.0))
            event("raise", ok=bool(ok), monster=str(cp.monster_name), title=str(cp.title), message=str(c.message), raised=len(gen.get_allies()))
            yield from pause(1.4, lambda: camera(side=35.0, pitch=-14.0, rate=40.0))
            n_al = len(gen.get_allies()); event("allies", n=n_al, names=[str(a.title) for a in gen.get_allies()])
            yield from s5_fights(99, lambda i: ["Frost Shard", "Fire"], until=DUR - 24.0)
    elif HERO == "Warlock":
        # ---- the curse, then the sword; Shadow Lash on the next
        yield from s5_fights(1, lambda i: ["Curse of Frailty"], until=DUR - 34.0); yield from look_at_corpse(1.6)
        yield from s5_fights(99, lambda i: [["Shadow Lash"], ["Curse of Frailty"]][i % 2], until=DUR - 24.0)
    else:
        # ---- the crossbow with the dexterity ring
        draw(next((i for i, d in enumerate(gen.get_editor_property("weapons")) if d.spell and d.bolt_mesh), 0))
        yield from s5_fights(99, until=DUR - 24.0); yield from look_at_corpse(1.6)
    # ---- behind a card: tier 3
    m = yield from tier3_jump(S5_ABILITY[HERO])
    G["until"] = DUR + 1.0; lure(); event("quiet", on=False)
    if m is not None:
        if HERO == "Mage": G["casts0"] = c.attacks_made; seg("fight"); yield from fight_s(m, S5_PLAN["Mage3"], max_t=30.0)
        elif HERO == "Warlock": yield from s5_fight(m, ["Curse of Frailty"], take=2)
        else: yield from s5_fight(m, take=2)
    # ---- its corpse; the big map: the rooms of this set written T3; then on to the next of its monsters, however far
    yield from look_at_corpse(1.4)
    seg("map"); gen.set_map_open(True); key_hit("m"); event("map", open=True)
    yield from pause(3.6, lambda: camera(side=-20.0, pitch=-14.0, rate=20.0))
    gen.set_map_open(False); key_hit("m"); event("map", open=False); seg("tier3")
    while True:
        m = threat() or nearest_monster(None, 400, 60000.0)
        if m is None: yield from pause(0.5, lambda: camera(side=40.0, pitch=-11.0, rate=12.0)); continue
        if HERO == "Mage": G["casts0"] = c.attacks_made; seg("fight"); yield from fight_s(m, ["Fireball", "Frost Shard", "Fire"])
        else: yield from s5_fight(m)

# ---------------------------------------------------------------- run5g: the two-handed grip, close and from the front
GRIP_CUTS = ["a diagonal cut, from over her right shoulder down to her left", "an overhead chop, raised over her head, down in front of her",
             "a horizontal sweep, from her right round to her left, turned at the waist"]
def run5g():
    """(level 5, the two-handed grip close up) the Warrior in the great hall with the Plate Knight's Sword, the camera
    close in front of her (her upper body); her three cuts at full speed, then the same three at a third of the speed;
    the monsters leave her be. (Level 5 now wields a two-handed sword with her sword's clips and no shield: the cuts
    are those.)"""
    gen, p = G["gen"], G["pawn"]
    seg("start")
    while T() <= 0.0 or G["combat"] is None:
        yield
    def start_count(): return sum(1 for q in gen.get_monsters() if alive(q) and q.get_editor_property("section").get_editor_property("coord") == IP(0, 0))
    while T() < 0.5 or (start_count() < 10 and T() < 1.2):
        yield
    c = G["combat"]; c.set_inventory_open(False); c.set_crafting_open(False)
    G["aggro0"] = (gen.get_editor_property("aggro_distance"), gen.get_editor_property("lose_distance"))
    gen.set_editor_property("aggro_distance", 0.0); gen.set_editor_property("lose_distance", 1.0); event("quiet", on=True)
    # (her place: the hall's middle, facing the way with the most room in front of her (the camera stands there))
    centre = gen.get_start_room_center(); st = V(centre.x, centre.y, 100.0); best = None
    for k in range(16):
        yaw = 22.5 * k; d = V(math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0.0)
        room = next((r_ for r_ in (600.0, 450.0, 300.0, 200.0) if sweep_clear(st, V(st.x + d.x * r_, st.y + d.y * r_, 100.0), 60.0)), 0.0)
        if best is None or room > best[0]: best = (room, yaw)
    face = best[1]
    for q in gen.get_monsters():                 # (none near her: a cut turns her to a monster in its reach)
        if alive(q) and d2(q.get_actor_location(), st) < 900.0: q.set_actor_location(V(st.x - 1500.0, st.y, q.get_actor_location().z), False, True)
    p.set_actor_location(st, False, True); p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=face), True)
    # (the sword: given, then drawn: a found weapon joins her weapons)
    c.add_item("Plate Knight's Sword", 1)
    wi = next((i for i, d in enumerate(gen.get_editor_property("weapons")) if str(d.name) == "Plate Knight's Sword"), None)
    if wi is not None: c.select_weapon(wi)
    wd = gen.get_editor_property("weapons")[wi] if wi is not None else None
    clips = [str(a.get_name()) for a in wd.attacks] if wd else []
    # (the camera: the game's own, its boom shortened and its view narrowed, turned to look at her from the front)
    boom = next(iter(p.get_components_by_class(unreal.SpringArmComponent)), None); cam = next(iter(p.get_components_by_class(unreal.CameraComponent)), None)
    # (Warrior3's slash bends her deep and raises the sword over her head: her whole body in the shot, as Warrior2's chop
    # test learned; the older cuts close on her upper body)
    deep = any("Slash" in x and "Warrior3" in x for x in clips)
    if boom:
        G["boom0"] = (boom.target_arm_length, boom.do_collision_test, boom.socket_offset, boom.target_offset)
        boom.target_arm_length = 360.0 if deep else 165.0; boom.do_collision_test = False; boom.socket_offset = V(0.0, 0.0, 0.0); boom.target_offset = V(0.0, 0.0, 0.0 if deep else 38.0)
    if cam: G["fov0"] = cam.field_of_view; cam.field_of_view = 50.0 if deep else 40.0
    G["grip_cam"] = (face + 180.0, -10.0 if deep else -7.0)
    event("start", at=[round(st.x), round(st.y)], face=round(face, 1), room_m=best[0] / 100.0, weapon=wd and str(wd.name), clips=clips, way="the Plate Knight's Sword, close up")
    seg("grip")
    yield from pause(1.6)
    # (slowed: her own time dilation (her animation and her attack's clock); the world's did not slow the render)
    for speed in (1.0, 1.0 / 3.0):
        p.set_editor_property("custom_time_dilation", speed); event("speed", speed=round(speed, 3))
        yield from pause(0.3)
        for k in range(3):
            p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=face), True)
            ok = c.start_attack(); key_hit("lmb")
            clip = clips[k % len(clips)] if clips else ""   # (the two-handed cuts' words only for those clips: level 5 wields it as a sword)
            event("cut", n=k, clip=clip, what=GRIP_CUTS[k] if "TwoHand" in clip else "", speed=round(speed, 3), ok=bool(ok))
            t0 = T()
            while c.is_attacking() and T() - t0 < 4.0 / speed: p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=face), True); yield
            yield from pause(0.45)
        yield from pause(0.6)
    p.set_editor_property("custom_time_dilation", 1.0); event("speed", speed=1.0)
    save()
    while True: yield

# ---------------------------------------------------------------- run5w2: Warrior2's chop test
def run5w2():
    """(level 5, the chop test of ai models/Warrior2.glb: the user's, Warrior2 alone) her own chop on her own rig, the
    Plate Knight's Sword in her right hand (861 placed her and the sword, hidden, tagged RDM5_Warrior2 / _Sword): she
    stands where the hero would in the great hall's middle (the hero hidden, her camera close in front as run5g's, a
    wider: her whole body, the sword raised over her head and brought down low as she bends); the whole clip at its own speed, then its swing (chop.json's
    'swing') at a third of it; the game's whoosh 0.16 s before each blow as for the heroes' swings; the monsters leave
    her be. Writes cine_chop2_warrior2.json"""
    gen, p = G["gen"], G["pawn"]
    C2 = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_warrior2\chop.json"))
    seg("start")
    while T() <= 0.0 or G["combat"] is None:
        yield
    def start_count(): return sum(1 for q in gen.get_monsters() if alive(q) and q.get_editor_property("section").get_editor_property("coord") == IP(0, 0))
    while T() < 0.5 or (start_count() < 10 and T() < 1.2):
        yield
    c = G["combat"]; c.set_inventory_open(False); c.set_crafting_open(False)
    G["aggro0"] = (gen.get_editor_property("aggro_distance"), gen.get_editor_property("lose_distance"))
    gen.set_editor_property("aggro_distance", 0.0); gen.set_editor_property("lose_distance", 1.0); event("quiet", on=True)
    centre = gen.get_start_room_center(); st = V(centre.x, centre.y, 100.0); best = None
    for k in range(16):
        yaw = 22.5 * k; d = V(math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0.0)
        room = next((r_ for r_ in (600.0, 450.0, 300.0, 200.0) if sweep_clear(st, V(st.x + d.x * r_, st.y + d.y * r_, 100.0), 60.0)), 0.0)
        if best is None or room > best[0]: best = (room, yaw)
    face = best[1]
    for q in gen.get_monsters():
        if alive(q) and d2(q.get_actor_location(), st) < 1500.0: q.set_actor_location(V(st.x - 2500.0, st.y, q.get_actor_location().z), False, True)
    p.set_actor_location(st, False, True); p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=face), True)
    yield
    w2 = next(iter(GS.get_all_actors_with_tag(G["w"], "RDM5_Warrior2")), None); sw = next(iter(GS.get_all_actors_with_tag(G["w"], "RDM5_Warrior2Sword")), None)
    if w2 is None or sw is None: event("error", what="861 has not placed Warrior2"); save("no Warrior2 in the level"); return
    sk = w2.skeletal_mesh_component; anim = unreal.load_asset("/Game/JRPG/Warrior2Anims/AS_Warrior2_Chop"); L = unreal.AnimationLibrary.get_sequence_length(anim)
    w2.set_actor_transform(p.mesh.get_world_transform(), False, True)
    w2.set_actor_hidden_in_game(False); sw.set_actor_hidden_in_game(False); p.set_actor_hidden_in_game(True)
    sk.play_animation(anim, False); sk.set_position(0.0, False); sk.stop()
    boom = next(iter(p.get_components_by_class(unreal.SpringArmComponent)), None); cam = next(iter(p.get_components_by_class(unreal.CameraComponent)), None)
    if boom:
        G["boom0"] = (boom.target_arm_length, boom.do_collision_test, boom.socket_offset, boom.target_offset)
        boom.target_arm_length = 360.0; boom.do_collision_test = False; boom.socket_offset = V(0.0, 0.0, 0.0); boom.target_offset = V(0.0, 0.0, 0.0)
    if cam: G["fov0"] = cam.field_of_view; cam.field_of_view = 50.0
    G["grip_cam"] = (face + 180.0, -10.0)
    event("start", at=[round(st.x), round(st.y)], face=round(face, 1), room_m=best[0] / 100.0, weapon="Plate Knight's Sword", clips=[anim.get_name()],
          way="Warrior2's chop test", clip_s=round(L, 3), chop=C2)
    seg("chop2")
    yield from pause(1.6)
    for part, speed, a, b in (("whole", 1.0, 0.0, L), ("swing", 1.0 / 3.0, C2["swing"][0], C2["swing"][1])):
        sk.play_animation(anim, False); sk.set_position(a, False); sk.set_play_rate(speed)
        event("cut", n=0 if part == "whole" else 1, clip=anim.get_name(), part=part, speed=round(speed, 3), ok=True, start_s=round(a, 3), end_s=round(b, 3))
        t0 = T(); whoosh = False
        while T() - t0 < (b - a) / speed:
            if not whoosh and T() - t0 >= (C2["blow"] - a) / speed - 0.16:
                whoosh = True; event("whoosh", heard=bool(gen.play_sound_at("Player.Whoosh", w2.get_actor_location())))
            yield
        sk.stop(); event("held", part=part)
        yield from pause(0.7)
    save()
    while True: yield

# ---------------------------------------------------------------- run5x: the four heroes' capabilities
def run5x():
    """(level 5, the four heroes' capabilities reel, way "caps"; Warrior, Mage, Warlock or Rogue, the same session seed for
    each) run5c's start by the great hall's anvil and its big map (the rooms' tiers, the anvil); two of the hall's
    containers (one with the set her hero wears); the set on, the camera round her (the Mage refused); at the anvil her
    recipe (what it lacks given, said by the caption) made; a fight (lured), her own weapons or spells; then the tiers'
    part of the weapons reels (tiers_part: behind a card tier 2's sets generated and cleared by the generator's debug
    clear but the last monster of one, at its grating into tier 3, the monster killed, the gratings gone, tier 3 generated
    ahead of her as she walks in, a fight there). The rules hold: who wields and wears what (her inventory refuses the
    rest), a tier opens only once the one before is cleared, the containers hold their tiers' items"""
    gen, p = G["gen"], G["pawn"]
    seg("start")
    while T() <= 0.0 or G["combat"] is None:
        camera(rate=1e6); yield
    def start_count(): return sum(1 for q in gen.get_monsters() if alive(q) and q.get_editor_property("section").get_editor_property("coord") == IP(0, 0))
    while T() < 0.5 or (start_count() < 10 and T() < 1.2):
        camera(rate=1e6); yield
    c = G["combat"]; c.set_inventory_open(False); c.set_crafting_open(False); G["until"] = DUR - 30.0
    s0 = gen.get_section(IP(0, 0)); centre = gen.get_start_room_center(); hall_room = s0.room_at(centre)
    anvil = next((a for a in s0.get_anvil_points() if s0.room_at(a) == hall_room), None)
    hall_ = list(gen.get_start_room_containers())
    lists = {i: [str(x) for x in gen.loot_list_of(IP(0, 0), i)] for i in hall_}
    S["note"]["hall"] = {str(i): v for i, v in lists.items()}
    pick = CRAFT_SET[HERO]; recipe = CRAFT_RECIPE[HERO]
    # ---- the start: by the hall's anvil, facing it; the big map
    a0 = anvil or centre; tow = V(centre.x - a0.x, centre.y - a0.y, 0.0)
    st = V(a0.x + tow.normal().x * 520.0, a0.y + tow.normal().y * 520.0, 100.0) if tow.length() > 1 else V(a0.x + 520.0, a0.y, 100.0)
    p.set_actor_location(st, False, True); G["heading"] = yaw_to(st, a0); p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), True)
    G["cam_yaw"] = G["heading"] - 25.0; G["cam_pitch"] = -20.0
    event("start", at=[round(st.x), round(st.y)], anvil=[round(a0.x), round(a0.y)] if anvil else None, hall=hall_, way="great hall, by its anvil")
    yield from pause(2.0, lambda: camera(side=-25.0, pitch=-20.0, rate=40.0))
    seg("map"); gen.set_map_open(True); key_hit("m"); event("map", open=True)
    yield from pause(3.3, lambda: camera(side=-25.0, pitch=-20.0, rate=20.0))
    gen.set_map_open(False); key_hit("m"); event("map", open=False)
    # ---- two of the hall's containers: one with her set, the nearest other
    seg("chest")
    with_set = [i for i in hall_ if pick in lists[i]]
    others = sorted((i for i in hall_ if i not in with_set), key=lambda i: d2(loc(), s0.get_container_location(i)))
    tour = (with_set[:1] + others[:1]) or others[:2]
    tour.sort(key=lambda i: d2(loc(), s0.get_container_location(i)))
    event("tour", containers=tour, lists={str(i): lists[i] for i in tour})
    for i in tour:
        if s0.is_target_open(False, i): continue
        at = s0.get_container_location(i); st_ = stand_by_chest(at, loc(), tol=450.0)
        if st_ is None: event("chest_missed", why="no place to stand", container=i); continue
        S["seg_back"] = "chest"; yield from open_chest(at, st_)
        yield from pause(0.3, lambda: camera(side=-30.0, pitch=-26.0, rate=70.0))
    if c.get_item_count(pick) == 0: c.add_item(pick, 1); event("given", items={pick: 1}, why="armour")
    # ---- her set on (the Mage: refused), the camera round her
    seg("armour")
    if HERO == "Mage": yield from refuse("armour", pick)
    else:
        yield from wield(pick, "armour", "armour")
        yield from swing_to(150.0, 0.5, -9.0); yield from orbit(1.9, 150.0, 200.0, -8.0)
    # (the crafting panel pauses the game in play; the reel's world goes on: the monsters leave her be meanwhile)
    if "aggro0" not in G: G["aggro0"] = (gen.get_editor_property("aggro_distance"), gen.get_editor_property("lose_distance"))
    gen.set_editor_property("aggro_distance", 0.0); gen.set_editor_property("lose_distance", 1.0); event("quiet", on=True); G["quiet"] = True
    # ---- to the anvil, F: her recipe; given what it lacks; made
    seg("craft"); S["seg_back"] = "craft"; stand = None
    if anvil is not None:
        for r_ in (150.0, 190.0):
            for k in range(16):
                q = V(anvil.x + math.cos(k * math.pi / 8) * r_, anvil.y + math.sin(k * math.pi / 8) * r_, 100.0)
                if s0.room_at(q) == hall_room and str(gen.describe_nearest(q, 260.0)) == "use the anvil" and len(path(loc(), q)):
                    if stand is None or d2(loc(), q) < d2(loc(), stand): stand = q
            if stand: break
    if stand is not None: yield from to_point(stand, 15.0, 45.0)
    G["heading"] = yaw_to(loc(), anvil) if anvil else G["heading"]; p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), False)
    yield from pause(0.4, lambda: camera(side=-35.0, pitch=-22.0, rate=70.0))
    said = str(gen.interact_nearest(loc(), 260.0)); key_hit("f"); event("craft_open", what=said, open=bool(c.is_crafting_open()))
    yield from pause(1.2)
    ri = next((i for i, x in enumerate(c.get_craft_lines()) if str(x).split("|")[1] == recipe), 0)
    while c.get_craft_cursor() != ri:
        c.move_craft_cursor(1 if ri > c.get_craft_cursor() else -1); key_hit("s"); yield from pause(0.35)
    yield from pause(1.4)
    rc = next(r_ for r_ in gen.get_editor_property("recipes") if str(r_.item) == recipe)
    give = {}
    for pt in rc.parts:
        have = sum(c.get_item_count(k_) for k_ in pt.any_of)
        if have < pt.count:
            kinds_ = [str(k_) for k_ in pt.any_of]; lack = pt.count - have
            for j, k_ in enumerate(kinds_):
                n_ = lack // len(kinds_) + (1 if j < lack % len(kinds_) else 0)
                if n_: give[k_] = give.get(k_, 0) + n_
    for k_, n_ in give.items(): c.add_item(k_, n_)
    event("given", items=give, why="craft", recipe=recipe)
    yield from pause(1.8)
    ok = c.craft_entry(); key_hit("enter"); event("crafted", item=recipe, ok=bool(ok), message=str(c.message), have=c.get_item_count(recipe))
    yield from pause(1.6)
    c.set_crafting_open(False); key_hit("f")
    yield from pause(0.5, lambda: camera(side=20.0, rate=60.0))
    # ---- a fight in the great hall's set (lured): her own weapons or spells
    a0_, l0_ = G["aggro0"]; gen.set_editor_property("aggro_distance", a0_); gen.set_editor_property("lose_distance", l0_); event("quiet", on=False); G["quiet"] = False
    seg("fight"); lure()
    tw = T()
    while threat() is None and T() - tw < 4.0: camera(side=25.0, pitch=-12.0, rate=25.0); yield
    m = threat() or nearest_monster(IP(0, 0), 60)
    if m is not None and T() < DUR - 34.0:
        G["casts0"] = c.attacks_made; yield from (fight(m) if HERO == "Mage" else fight_w(m))
    lure(False)
    # ---- the tiers: behind a card the start set cleared too (tier 2 opens only once it is: the rule of 2026-10-24) and
    # tier 2's sets but one monster; a grating into tier 3, on into tier 3 as it is generated
    while T() < DUR - 30.0: camera(side=30.0, pitch=-11.0, rate=15.0); yield
    yield from tiers_part()

# ---------------------------------------------------------------- run5m: Mistward Castle (the user's list of 2026-10-26)
def mw_card(text, sub=""):
    """(run5m) the reel skips ahead: a card over the picture says what changed (the overlay draws it for MW_CARD s)"""
    seg("jump"); event("card", text=text, sub=sub)
MW_CARD = 3.0
def mw_set(at, face_to=None, yaw=None, side=-22.0, pitch=-20.0):
    """(run5m) she is put at `at` (on the floor), facing a point or a way; the camera behind her at once"""
    p = G["pawn"]; p.set_actor_location(V(at.x, at.y, 100.0), False, True)
    G["heading"] = yaw if yaw is not None else (yaw_to(at, face_to) if face_to is not None else G.get("heading", 0.0))
    p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), True)
    G["cam_yaw"] = G["heading"] + side; G["cam_pitch"] = pitch
def mw_quiet(on):
    """(run5m) the monsters leave her be (the crafting panel and the inventory pause the game in play; the reel's world goes on)"""
    gen = G["gen"]
    if "aggro0" not in G: G["aggro0"] = (gen.get_editor_property("aggro_distance"), gen.get_editor_property("lose_distance"))
    a0, l0 = G["aggro0"]
    gen.set_editor_property("aggro_distance", 0.0 if on else a0); gen.set_editor_property("lose_distance", 1.0 if on else l0)
    G["quiet"] = on; event("quiet", on=on)
def mw_start():
    gen = G["gen"]
    seg("start")
    while T() <= 0.0 or G["combat"] is None:
        camera(rate=1e6); yield
    def start_count(): return sum(1 for q in gen.get_monsters() if alive(q) and q.get_editor_property("section").get_editor_property("coord") == IP(0, 0))
    while T() < 0.5 or (start_count() < 10 and T() < 1.2):
        camera(rate=1e6); yield
    c = G["combat"]; c.set_inventory_open(False); c.set_crafting_open(False)
    # (the monsters leave her be until a fight of the plan's: the great hall's came at her on the way to its first chest)
    mw_quiet(True)
    S["note"]["fps_note"] = "the frame rate the game shows is its own tick's: in a render the queue steps it at the reel's rate"
def mw_hall():
    gen = G["gen"]; s0 = gen.get_section(IP(0, 0)); centre = gen.get_start_room_center(); room = s0.room_at(centre)
    anvil = next((a for a in s0.get_anvil_points() if s0.room_at(a) == room), None)
    return s0, centre, room, anvil
def mw_anvil(anvil, room):
    """(run5m) to the hall's anvil and F: the crafting panel"""
    gen, c = G["gen"], G["combat"]; s0 = gen.get_section(IP(0, 0)); stand = None
    for r_ in (150.0, 190.0):
        for k in range(16):
            q = V(anvil.x + math.cos(k * math.pi / 8) * r_, anvil.y + math.sin(k * math.pi / 8) * r_, 100.0)
            if s0.room_at(q) == room and str(gen.describe_nearest(q, 260.0)) == "use the anvil" and len(path(loc(), q)):
                if stand is None or d2(loc(), q) < d2(loc(), stand): stand = q
        if stand: break
    if stand is not None: yield from to_point(stand, 12.0, 45.0)
    G["heading"] = yaw_to(loc(), anvil); G["pawn"].set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), False)
    yield from pause(0.4, lambda: camera(side=-35.0, pitch=-22.0, rate=70.0))
    said = str(gen.interact_nearest(loc(), 260.0)); key_hit("f"); event("craft_open", what=said, open=bool(c.is_crafting_open()))
    yield from pause(1.6)
def mw_craft_line(kind, name):
    """(run5m) the crafting panel's cursor down (S) to a line, then Enter"""
    c = G["combat"]
    lines = [str(x).split("|") for x in c.get_craft_lines()]
    i = next((k for k, x in enumerate(lines) if x[0] == kind and x[1] == name), None)
    event("craft_want", line_kind=kind, name=name, index=i, lines=["|".join(x[:2]) for x in lines])
    if i is None: return False
    while c.get_craft_cursor() != i:
        c.move_craft_cursor(1 if i > c.get_craft_cursor() else -1); key_hit("s" if i > c.get_craft_cursor() else "w"); yield from pause(0.3)
    yield from pause(1.2)
    ok = c.craft_entry(); key_hit("enter"); event("crafted", item=name, line_kind=kind, ok=bool(ok), message=str(c.message))
    yield from pause(2.0)
    return ok
def mw_open_tier2(leave=0):
    """(run5m) the reel's shortcut, said by its card: the start set cleared by the generator's debug clear (`leave` monsters
    left: still 50 % or more killed); tier 2 opens"""
    gen = G["gen"]
    gen.debug_clear_section(IP(0, 0), leave, gen.get_start_room_center())
    # (the tally right after a restart can still be counting: the clear again every half second until the tier opens)
    t0 = T(); t1 = T()
    while not gen.is_tier_open(2) and T() - t0 < 4.0:
        if T() - t1 > 0.5: t1 = T(); gen.debug_clear_section(IP(0, 0), leave, gen.get_start_room_center())
        yield
    event("tier2", open=bool(gen.is_tier_open(2)), notice=str(gen.tier_notice), encounters=[str(x) for x in gen.get_encounter_lines()])
def mw_encounters():
    out = []
    for l in G["gen"].get_encounter_lines():
        p_ = str(l).split("|"); out.append({"kind": p_[0], "at": V(float(p_[1]), float(p_[2]), float(p_[3])), "name": p_[4], "rest": p_[5:]})
    return out
def mw_near_point(at, dist, sec=None):
    """a floor point `dist` from `at` in the same room, she can walk from to it (by the tile path)"""
    sec = sec or section_of(at); room = sec.room_at(at); best = None
    for k in range(24):
        a = k * math.pi / 12; q = V(at.x + math.cos(a) * dist, at.y + math.sin(a) * dist, 100.0)
        if room >= 0 and sec.room_at(q) != room: continue
        pts = list(sec.find_path_world(q, at))
        # (the way clear up to 1.2 m short of it: a ring in a chest is in the chest, and a sweep to it always struck the chest)
        short = at + (q - at) * (min(120.0, dist * 0.5) / max(dist, 1.0))
        if len(pts) and d2(pts[0], q) < 140.0 and sweep_clear(q, V(short.x, short.y, 100.0), 30.0):
            return q
    return None
def mw_map(sec=3.0):
    gen = G["gen"]; gen.set_map_open(True); key_hit("m"); event("map", open=True)
    yield from pause(sec, lambda: camera(side=-15.0, pitch=-15.0, rate=20.0))
    gen.set_map_open(False); key_hit("m"); event("map", open=False)

def run5m():
    """(mistward_castle, the user's list of 2026-10-26; the four heroes, each her own session seed) what each hero can do now,
    and the castle's new rules (see the module docstring)"""
    yield from mw_start()
    gen, c, p = G["gen"], G["combat"], G["pawn"]
    s0, centre, room, anvil = mw_hall()
    S["note"]["themes"] = {t: gen.get_theme_name(IP(t - 1, 0)) for t in range(1, 6)}
    yield from {"Warrior": mw_warrior, "Mage": mw_mage, "Warlock": mw_warlock, "Rogue": mw_rogue}[HERO](s0, centre, room, anvil)
    while True: yield from pause(0.5, lambda: camera(side=30.0, pitch=-12.0, rate=12.0))

def mw_warrior(s0, centre, room, anvil):
    """the Warrior: a hall chest with a shield in it (the seed's): opened, it stays open; the found shield on her arm from the
    inventory; at the anvil (its lists in alphabetical order) her Heater Shield broken down; a fight, two blows let land on
    the shield; then tier 1 at 50 %: tier 2 opens, a boss waits (the big map's marks) and she goes for it"""
    gen, c, p = G["gen"], G["combat"], G["pawn"]
    kinds = {str(it.name): str(it.kind.name).lower() for it in gen.get_editor_property("items")}
    hall_ = list(gen.get_start_room_containers()); lists = {i: [str(x) for x in gen.loot_list_of(IP(0, 0), i)] for i in hall_}
    S["note"]["hall"] = {str(i): v for i, v in lists.items()}
    with_sh = [i for i in hall_ if any(kinds.get(x) == "shield" for x in lists[i])]
    ch = (with_sh or hall_)[0]; at = s0.get_container_location(ch)
    st = stand_by_chest(at, centre, tol=450.0) or V(at.x + 200, at.y, 100)
    q = V(st.x + (st.x - at.x) * 2.5, st.y + (st.y - at.y) * 2.5, 100.0)
    mw_set(q if s0.room_at(q) == room else st, face_to=at)
    event("start", at=[round(loc().x), round(loc().y)], chest=ch, holds=lists[ch], way="great hall, a chest with a shield")
    yield from pause(2.6, lambda: camera(side=-22.0, pitch=-20.0, rate=40.0))
    seg("chest"); yield from open_chest(at, st)
    yield from pause(0.8, lambda: camera(side=-30.0, pitch=-26.0, rate=70.0))
    # (F again: nothing to close, nothing offered)
    what = str(gen.describe_nearest(loc(), 200.0)); gen.interact_nearest(loc(), 200.0); key_hit("f")
    event("f_again", describe=what, open_alpha=round(s0.get_container_open_alpha(ch), 2))
    yield from pause(2.2, lambda: camera(side=-40.0, pitch=-24.0, rate=40.0))
    found = next((x for x in lists[ch] if kinds.get(x) == "shield"), None)
    if found is None:
        found = "Village Shield (blue and white)"; c.add_item(found, 1); event("given", items={found: 1}, why="shield")
    # ---- the found shield on her arm (from the inventory), the camera round her
    seg("shield"); yield from wield(found, "shield", "shield")
    yield from swing_to(120.0, 0.6, -9.0); yield from orbit(2.4, 120.0, 140.0, -8.0)
    # ---- at the anvil: the lists in alphabetical order; her Heater Shield broken down
    mw_quiet(True); seg("craft"); S["seg_back"] = "craft"
    if anvil is not None:
        yield from mw_anvil(anvil, room)
        yield from mw_craft_line("breakdown", "Heater Shield")
        c.set_crafting_open(False); key_hit("f")
    yield from pause(0.4)
    mw_quiet(False)
    # ---- a fight (lured): two blows let land on her shield
    mw_quiet(False); seg("fight"); lure(); G["until"] = DUR - 27.0; tw = T()
    while threat() is None and T() - tw < 4.0: camera(side=25.0, pitch=-12.0, rate=25.0); yield
    m = threat() or nearest_monster(IP(0, 0), 60)
    if m is not None: G["casts0"] = c.attacks_made; yield from fight_w(m, take=2)
    lure(False)
    while T() < DUR - 26.0: camera(side=30.0, pitch=-11.0, rate=15.0); yield
    # ---- tier 1 at 50 %: tier 2 opens, a boss waits
    G["until"] = DUR + 1.0; lure(False); mw_quiet(True)
    mw_card("TIER 1 AT 50 %", "the reel's shortcut: the start set cleared by the generator but for a little under half of its monsters")
    n_mon = sum(1 for q_ in gen.get_monsters() if alive(q_) and q_.get_editor_property("section").get_editor_property("coord") == IP(0, 0) and q_.get_editor_property("spawn_index") >= 0)
    yield from mw_open_tier2(leave=max(0, int(n_mon * 0.45)))
    boss = next((e for e in mw_encounters() if e["kind"] == "boss"), None)
    if boss is not None:
        stand = mw_near_point(boss["at"], 1300.0) or mw_near_point(boss["at"], 900.0)
        if stand is not None: mw_set(stand, face_to=boss["at"], side=-18.0, pitch=-14.0)
        event("at_boss", boss=boss["name"], m=round(d2(loc(), boss["at"]) / 100.0, 1))
    c.set_health(c.get_max_health())
    yield from pause(MW_CARD + 0.2, lambda: camera(side=-18.0, pitch=-14.0, rate=1e6))
    seg("boss"); yield from mw_map(3.0)
    mw_quiet(False); lure()
    while True:
        m = threat() or (nearest_monster(None, 40, 3000.0) if T() < DUR - 3.0 else None)
        if m is None: yield from pause(0.5, lambda: camera(side=20.0, rate=20.0)); continue
        G["casts0"] = c.attacks_made; yield from fight_w(m)

def mw_mage(s0, centre, room, anvil):
    """the Mage: by the anvil, with the torch's materials and a bag of others (given, said): the inventory walked by holding S;
    the torch made at the anvil, lit from the inventory; then tier 2's castle keep: a prisoner set free, a caged monster
    breaking out"""
    gen, c, p = G["gen"], G["combat"], G["pawn"]
    a0 = anvil or centre; tow = V(centre.x - a0.x, centre.y - a0.y, 0.0)
    st = V(a0.x + tow.normal().x * 520.0, a0.y + tow.normal().y * 520.0, 100.0) if tow.length() > 1 else V(a0.x + 520.0, a0.y, 100.0)
    mw_set(st, face_to=a0, side=-25.0, pitch=-20.0)
    event("start", at=[round(st.x), round(st.y)], way="great hall, by its anvil")
    yield from pause(2.6, lambda: camera(side=-25.0, pitch=-20.0, rate=40.0))
    give = {"Hardwood": 1, "Timber": 1, "Straw Rope": 2, "Oils": 1}
    for it in [i for i in gen.get_editor_property("items") if i.kind == unreal.RDItemKind.COMPONENT][:14]: give.setdefault(str(it.name), 1)
    for k_, n_ in give.items(): c.add_item(k_, n_)
    event("given", items=give, why="torch")
    # ---- the inventory: holding S walks the list
    mw_quiet(True); seg("inventory")
    c.set_inventory_open(True); key_hit("i"); yield from pause(1.0)
    ks = unreal.Key(); ks.set_editor_property("key_name", "S"); kw_ = unreal.Key(); kw_.set_editor_property("key_name", "W")
    # (a held key is the game's own input: the pilot's scripted-only mode, which leaves her keys to the pilot, is off for it)
    c.set_scripted_only(False)
    c0 = c.get_inventory_cursor(); c.simulate_key(ks, True); event("hold", key="s"); t0 = T()
    while T() - t0 < 1.6: G["key_hit"] = "s"; G["keys_t"] = T(); yield
    c.simulate_key(ks, False); event("held", key="s", lines=c.get_inventory_cursor() - c0, seconds=1.6)
    yield from pause(0.8)
    c0 = c.get_inventory_cursor(); c.simulate_key(kw_, True); event("hold", key="w"); t0 = T()
    while T() - t0 < 1.2: G["key_hit"] = "w"; G["keys_t"] = T(); yield
    c.simulate_key(kw_, False); event("held", key="w", lines=c0 - c.get_inventory_cursor(), seconds=1.2)
    c.set_scripted_only(True)
    yield from pause(0.6); c.set_inventory_open(False); key_hit("i"); yield from pause(0.4)
    # ---- the torch made at the anvil, lit
    seg("craft"); S["seg_back"] = "craft"
    if anvil is not None:
        yield from mw_anvil(anvil, room)
        yield from mw_craft_line("recipe", "Torch")
        c.set_crafting_open(False); key_hit("f"); yield from pause(0.4)
    seg("torch"); yield from wield("Torch", "torch", "torch")
    yield from swing_to(140.0, 0.6, -9.0); yield from orbit(2.4, 140.0, 120.0, -8.0)
    mw_quiet(False)
    # ---- tier 2, the castle keep: a prisoner's cell and a caged monster's
    mw_card("TIER 2: THE CASTLE KEEP'S PRISON", "the reel's shortcut: the start set cleared by the generator; tier 2's sets generated")
    yield from mw_open_tier2(0)
    pick = None
    for xy in [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (-1, 1), (-1, -1), (1, -1)]:
        sc_ = IP(*xy)
        if not gen.is_section_generated(sc_): gen.generate_section_now(sc_)
        S_ = gen.get_section(sc_)
        cells = [str(x).split("|") for x in S_.get_cell_lines()]
        pr = [x for x in cells if x[2] == "1" and x[3] == "0"]; mo = [x for x in cells if x[2] == "2" and x[3] == "0"]
        dd = lambda a_, b_: math.hypot(float(a_[4]) - float(b_[4]), float(a_[5]) - float(b_[5]))
        # (a prisoner with no caged monster within 6.5 m (one would break out as she frees the prisoner), and a monster's cell
        # 9 m or more from it: the nearest such pair)
        pr = [a_ for a_ in pr if all(dd(a_, b_) > 650.0 for b_ in mo)]
        pairs = [(a_, b_) for a_ in pr for b_ in mo if dd(a_, b_) >= 900.0]
        if pairs:
            best = min(pairs, key=lambda ab: dd(*ab)); pick = (S_, best[0], best[1]); break
    if pick is None:
        event("no_cells"); yield from pause(MW_CARD); return
    S_, pr, mo = pick
    door = S_.get_door_location(int(pr[1])); cell = V(float(pr[4]), float(pr[5]), 0.0)
    a = math.atan2(door.y - cell.y, door.x - cell.x); st = V(door.x + math.cos(a) * 110, door.y + math.sin(a) * 110, 100.0)
    mw_set(st, face_to=cell, side=-28.0, pitch=-16.0); c.set_health(c.get_max_health())
    event("at_cell", section=[S_.coord.x, S_.coord.y], cell=int(pr[0]), theme=gen.get_theme_name(S_.coord))
    mw_quiet(True)
    yield from pause(MW_CARD + 1.0, lambda: camera(side=-28.0, pitch=-16.0, rate=1e6))
    seg("cell")
    said = str(gen.describe_nearest(loc(), 260.0)); r_ = str(gen.interact_nearest(loc(), 260.0)); key_hit("f")
    event("cell_open", what=said, did=r_, freed=gen.prisoners_freed, message=str(c.message))
    yield from pause(4.5, lambda: camera(side=-50.0, pitch=-14.0, rate=18.0))
    # ---- the caged monster's cell: it opens as she comes near (the others leave her be until it does)
    mdoor = S_.get_door_location(int(mo[1])); mcell = V(float(mo[4]), float(mo[5]), 0.0)
    a = math.atan2(mdoor.y - mcell.y, mdoor.x - mcell.x); toward = V(mdoor.x + math.cos(a) * 110, mdoor.y + math.sin(a) * 110, 100.0)
    seg("walk"); b0 = gen.cell_breakouts; yield from to_point(toward, 6.0, 80.0)
    t0 = T()
    while gen.cell_breakouts == b0 and T() - t0 < 2.0: camera(side=-20.0, pitch=-14.0, rate=40.0); yield
    event("breakout", n=gen.cell_breakouts - b0)
    m = min((q for q in gen.get_monsters() if alive(q)), key=lambda q: d2(q.get_actor_location(), mcell), default=None)
    mw_quiet(False)
    # (a few steps back into the room: she fights it in the open, not against the bars)
    back = V(mdoor.x + math.cos(a) * 520, mdoor.y + math.sin(a) * 520, 100.0); t0 = T()
    while d2(loc(), back) > 80.0 and T() - t0 < 1.6: move(back, run=True); camera(side=150.0, pitch=-14.0, rate=90.0); yield
    G["heading"] = yaw_to(loc(), mcell); p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), False)
    while True:
        if m is not None and alive(m): G["casts0"] = c.attacks_made; seg("fight"); yield from fight(m)
        m = threat()
        if m is None: yield from pause(0.5, lambda: camera(side=20.0, rate=20.0))

def mw_warlock(s0, centre, room, anvil):
    """the Warlock: rooms of other shapes (a dome, a stepped pyramid, a round room) in the start set; then tier 2: its first
    set's teleporter with its ring (F takes it), the ring used (back to the great hall's pad), the pad (back to tier 2);
    a fight there that she loses (the reel takes her hit points down, said): her things in a pile where she fell, back on
    her feet in the great hall; later, at the pile, F takes them up"""
    gen, c, p = G["gen"], G["combat"], G["pawn"]
    # (the nearest chest of the great hall first: what she finds is what she will drop when she falls)
    hall_ = list(gen.get_start_room_containers()); ch = min(hall_, key=lambda i: d2(s0.get_container_location(i), centre)) if hall_ else None
    at = s0.get_container_location(ch) if ch is not None else centre
    st = stand_by_chest(at, centre, tol=450.0) if ch is not None else None
    mw_set(st if st else V(centre.x, centre.y, 100.0), face_to=at)
    event("start", at=[round(loc().x), round(loc().y)], way="great hall, its nearest chest")
    yield from pause(2.4, lambda: camera(side=-20.0, pitch=-18.0, rate=40.0))
    if st is not None: seg("chest"); yield from open_chest(at, st); yield from pause(0.8, lambda: camera(side=-30.0, pitch=-26.0, rate=70.0))
    mw_quiet(True)
    shown = 0
    for want, title in (("dome", "A DOMED ROOM"), ("step pyramid", "A STEPPED PYRAMID OF A CEILING"), ("circle", "A ROUND ROOM")):
        rm = next((i for i in range(s0.get_num_rooms()) if str(s0.get_room_shape(i)) == want), None)
        if rm is None: continue
        rc = s0.get_room_center(rm)
        mw_card(title, "in the start set: a room of another shape (the castle's rooms: round, octagonal, triangular, L, T, U, domes, pyramids)")
        mw_set(V(rc.x - 250, rc.y, 100.0), yaw=0.0, side=180.0, pitch=8.0)
        yield from pause(MW_CARD, lambda: camera(side=180.0, pitch=8.0, rate=1e6))
        seg("shape"); event("shape", shape=want, room=rm)
        yield from orbit(3.2, 180.0, 70.0, 22.0)
        shown += 1
        if shown >= 3 or T() > 22.0: break
    # ---- tier 2's first set's teleporter
    mw_card("TIER 2: ITS FIRST SET'S TELEPORTER", "the reel's shortcut: the start set cleared by the generator, tier 2 opened")
    yield from mw_open_tier2(0)
    if not gen.is_section_generated(IP(1, 0)): gen.generate_section_now(IP(1, 0))
    yield
    pads = {int(k): v for k, v in gen.pads.items()}
    if 2 not in pads: event("no_pad"); yield from pause(MW_CARD); return
    st = mw_near_point(pads[2], 420.0) or V(pads[2].x - 420, pads[2].y, 100)
    mw_set(st, face_to=pads[2], side=-25.0, pitch=-18.0)
    yield from pause(MW_CARD + 0.2, lambda: camera(side=-25.0, pitch=-18.0, rate=1e6))
    seg("pad"); yield from to_point(V(pads[2].x, pads[2].y, 100.0), 4.0, 70.0)
    said = str(gen.describe_nearest(loc(), 260.0)); r_ = str(gen.interact_nearest(loc(), 260.0)); key_hit("f")
    event("pad", what=said, did=r_, tier=2)
    yield from pause(1.8, lambda: camera(side=-40.0, pitch=-20.0, rate=40.0))
    ring = next((str(i.name) for i in gen.get_editor_property("items") if i.kind == unreal.RDItemKind.TELEPORT and i.teleport_tier == 2), "Teleport Ring II")
    n0 = gen.teleports
    yield from wield(ring, "teleport", "teleport")
    event("teleported", to=1, n=gen.teleports - n0, m_from_pad1=round(d2(loc(), pads[1]) / 100.0, 1))
    yield from pause(2.4, lambda: camera(side=-30.0, pitch=-20.0, rate=40.0))
    said = str(gen.describe_nearest(loc(), 260.0)); r_ = str(gen.interact_nearest(loc(), 260.0)); key_hit("f")
    event("pad", what=said, did=r_, tier=1, m_from_pad2=round(d2(loc(), pads[2]) / 100.0, 1))
    yield from pause(2.2, lambda: camera(side=-30.0, pitch=-18.0, rate=40.0))
    mw_quiet(False)
    # ---- a fight she loses: her things where she fell
    seg("fight"); lure()
    c.set_health(c.get_max_health() * 0.12); event("hp_set", hp=round(c.get_health(), 1), why="the reel takes her hit points down: a fight she loses")
    deaths0 = c.deaths; fell_at = None
    while c.deaths == deaths0 and T() < DUR - 14.0:
        m = threat() or nearest_monster(None, 40, 4000.0)
        if m is None: yield from pause(0.3, lambda: camera(side=20.0, rate=30.0)); continue
        G["casts0"] = c.attacks_made; yield from fight_w(m, take=2)          # (she stands her ground until its blows land)
    lure(False)
    if c.deaths > deaths0:
        fell_at = loc(); seg("dead"); event("fell", at=[round(fell_at.x), round(fell_at.y)], piles=len([x for x in gen.loot_piles if x]))
        mw_quiet(True)
        while c.is_dead(): camera(side=60.0, pitch=-30.0, rate=10.0); yield
        yield from pause(1.6, lambda: camera(side=20.0, pitch=-16.0, rate=40.0))
        pile = next((x for x in gen.loot_piles if x and x.hers), None)
        if pile is not None:
            mw_card("LATER: BACK WHERE SHE FELL", "the reel takes her there")
            pl = pile.get_actor_location(); st = mw_near_point(pl, 260.0) or V(pl.x - 260, pl.y, 100)
            mw_set(st, face_to=pl, side=-30.0, pitch=-22.0)
            yield from pause(MW_CARD + 0.2, lambda: camera(side=-30.0, pitch=-22.0, rate=1e6))
            seg("pile"); yield from to_point(V(pl.x, pl.y, 100.0), 3.0, 90.0)
            said = str(gen.describe_nearest(loc(), 260.0)); r_ = str(gen.interact_nearest(loc(), 260.0)); key_hit("f")
            event("took_back", what=said, did=r_, message=str(c.message))
        mw_quiet(False)

def mw_rogue(s0, centre, room, anvil):
    """the Rogue: a trap seen from 8 m (its mark on the map), disarmed with F; another walked onto (said); then tier 1 at
    50 %: tier 2 opens, and the magic potency ring she never found lies guarded in a room she has seen: the big map's mark, the
    guards fought, the ring taken"""
    gen, c, p = G["gen"], G["combat"], G["pawn"]
    traps = []
    for l in gen.get_trap_lines():
        q = str(l).split("|")
        if q[0] == "0" and q[1] == "0" and q[8] == "0": traps.append({"i": int(q[2]), "name": q[3], "at": V(float(q[5]), float(q[6]), float(q[7]))})
    traps.sort(key=lambda t_: d2(t_["at"], centre))
    first = next((t_ for t_ in traps if t_["name"] in ("Pit", "Snare", "Darts", "Deadfall")), traps[0] if traps else None)
    if first is None: event("no_traps"); return
    st = None
    for dist in (1100.0, 1000.0, 900.0):
        for k in range(24):
            a = k * math.pi / 12; q = V(first["at"].x + math.cos(a) * dist, first["at"].y + math.sin(a) * dist, 100.0)
            pts = path(q, first["at"])
            if 1 < len(pts) and d2(pts[0], q) < 140.0: st = q; break
        if st: break
    mw_set(st or V(first["at"].x - 1000, first["at"].y, 100), face_to=first["at"])
    event("start", at=[round(loc().x), round(loc().y)], trap=first["name"], m=round(d2(loc(), first["at"]) / 100.0, 1))
    mw_quiet(True)
    yield from pause(2.4, lambda: camera(side=-22.0, pitch=-20.0, rate=40.0))
    # ---- toward it: she sees it (8 m), stops by it, F: disarmed
    seg("trap"); route = Route(path(loc(), first["at"])); t0 = T()
    while d2(loc(), first["at"]) > 190.0 and T() - t0 < 8.0:
        move(pulled(route), run=False); doors(); camera(side=-20.0, pitch=-20.0, rate=60.0); yield
    G["heading"] = yaw_to(loc(), first["at"]); p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), False)
    yield from pause(0.8, lambda: camera(side=-35.0, pitch=-24.0, rate=50.0))
    said = str(gen.describe_nearest(loc(), 260.0)); r_ = str(gen.interact_nearest(loc(), 260.0)); key_hit("f")
    event("disarm", what=said, did=r_)
    t0 = T()
    while T() - t0 < gen.disarm_seconds + 0.6: camera(side=-40.0, pitch=-26.0, rate=20.0); yield
    event("disarmed", n=gen.traps_disarmed, message=str(c.message))
    yield from pause(1.0)
    # ---- another, walked onto (the reel's choice, said)
    pref = ("Glyph", "Darts", "Deadfall", "Snare", "Cursed", "Pit")
    others = sorted((t_ for t_ in traps if t_ is not first and t_["name"] != first["name"]), key=lambda t_: (pref.index(t_["name"]) if t_["name"] in pref else 9, d2(t_["at"], first["at"])))
    other = others[0] if others else None
    if other is not None:
        # (behind a card: 4 m from another trap of the start set, which she walks onto (the reel's choice, said))
        mw_card("ANOTHER TRAP", "the reel walks her onto it: what a trap does to whoever steps on it")
        st2 = mw_near_point(other["at"], 420.0) or V(other["at"].x - 420.0, other["at"].y, 100.0)
        mw_set(st2, face_to=other["at"], side=-30.0, pitch=-20.0)
        yield from pause(MW_CARD + 0.4, lambda: camera(side=-30.0, pitch=-20.0, rate=1e6))
        seg("trap2"); event("onto", trap=other["name"], why="the reel walks her onto a trap she has seen")
        route = Route([V(other["at"].x, other["at"].y, 100.0)]); t0 = T()
        while d2(loc(), other["at"]) > 40.0 and T() - t0 < 4.0: move(other["at"], run=False); camera(side=-30.0, pitch=-20.0, rate=60.0); yield
        yield from pause(3.0, lambda: camera(side=-40.0, pitch=-22.0, rate=30.0))
    c.set_health(c.get_max_health()); mw_quiet(False)
    # ---- tier 1 at 50 %: the guarded ring
    mw_card("TIER 1 AT 50 %", "the reel's shortcut: the start set cleared by the generator but for a little under half of its monsters")
    n_mon = sum(1 for q_ in gen.get_monsters() if alive(q_) and q_.get_editor_property("section").get_editor_property("coord") == IP(0, 0) and q_.get_editor_property("spawn_index") >= 0)
    yield from mw_open_tier2(leave=max(0, int(n_mon * 0.45)))
    # (the ring is put a tick after the tier opens; at 50 % the tier opened at the first clear, in the same tick, and the run
    # went on without it)
    t0 = T(); ring = None
    while ring is None and T() - t0 < 2.0:
        yield; ring = next((e for e in mw_encounters() if e["kind"] == "ring"), None)
    if ring is not None:
        # (nearer where the room is small: the castle's small chambers are 9 to 12 m across, and a stand point 10 m off in the
        # room did not exist: she was left 88 m away)
        st = next((q_ for q_ in (mw_near_point(ring["at"], d_) for d_ in (1400.0, 1000.0, 700.0, 450.0, 300.0)) if q_ is not None), None)
        if st is not None: mw_set(st, face_to=ring["at"], side=-20.0, pitch=-16.0)
        event("at_ring", ring=ring["name"], m=round(d2(loc(), ring["at"]) / 100.0, 1))
    yield from pause(MW_CARD + 0.2, lambda: camera(side=-20.0, pitch=-16.0, rate=1e6))
    seg("ring"); yield from mw_map(3.0)
    lure()
    while ring is not None and T() < DUR - 6.0:
        guards = [q_ for q_ in gen.get_monsters() if alive(q_) and d2(q_.get_actor_location(), ring["at"]) < 2200.0]
        m = threat() or (min(guards, key=lambda q_: d2(q_.get_actor_location(), loc())) if guards else None)
        if m is None: break
        G["casts0"] = c.attacks_made; seg("fight"); yield from fight3(m)
    lure(False)
    if ring is not None and T() < DUR - 4.0:
        seg("ring")
        pile = next((x for x in gen.loot_piles if x and not x.hers), None)
        if pile is not None:
            pl = pile.get_actor_location(); yield from to_point(V(pl.x, pl.y, 100.0), 6.0, 90.0)
            r_ = str(gen.interact_nearest(loc(), 260.0)); key_hit("f"); event("ring_taken", did=r_, has=c.get_item_count(ring["name"]))
        else:
            yield from open_chest(ring["at"]); event("ring_taken", did="chest", has=c.get_item_count(ring["name"]))

# ---------------------------------------------------------------- run5m2: the third list (docs/improvements2.txt)
def mw2_key(name, hold=0.12, label=None):
    """a key pressed as the game takes it (the pilot's scripted-only mode off for the press): the inventory's tabs, the
    quick slots, the slash list, H"""
    c = G["combat"]; k = unreal.Key(); k.set_editor_property("key_name", name)
    c.set_scripted_only(False); c.simulate_key(k, True); key_hit(label or name.lower())
    yield from pause(hold)
    c.simulate_key(k, False); c.set_scripted_only(True)
    yield from pause(0.08)
NUMS = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Zero"]
def mw2_inv(tab, why, **kw):
    """I, then E to the tab"""
    c = G["combat"]
    event("inventory", lines=[str(x) for x in c.get_inventory_lines()], why=why, tab=tab, hp=round(c.get_health(), 1), mana=round(c.get_mana(), 1), **kw)
    if not c.is_inventory_open(): c.set_inventory_open(True); key_hit("i"); yield from pause(0.9)
    n = 0
    while c.get_inventory_tab() != tab and n < 6:
        yield from mw2_key("E", label="e_tab"); n += 1
        event("tab", tab=c.get_inventory_tab()); yield from pause(0.7)
def mw2_cursor(prefix, name):
    """the cursor down or up the tab's list to a line (S / W)"""
    c = G["combat"]; lines = [str(x) for x in c.get_inventory_lines()]
    want = next((i for i, x in enumerate(lines) if x.startswith(prefix + "|" + name + "|") or x == prefix + "|" + name), None)
    while want is not None and c.get_inventory_cursor() != want:
        down = want > c.get_inventory_cursor(); c.move_inventory_cursor(1 if down else -1); key_hit("s" if down else "w"); yield from pause(0.32)
    return want
def mw2_close():
    c = G["combat"]; c.set_inventory_open(False); key_hit("i"); yield from pause(0.3)
def mw2_rooms(kind=None, coord=None):
    out = []
    for l in G["gen"].get_special_room_lines():
        q = str(l).split("|")
        r = {"s": IP(int(q[0]), int(q[1])), "room": int(q[2]), "kind": q[3], "at": V(float(q[4]), float(q[5]), float(q[6])), "done": int(q[7])}
        if (kind is None or r["kind"] == kind) and (coord is None or (r["s"].x == coord[0] and r["s"].y == coord[1])): out.append(r)
    return out
def mw2_beside(at, room, sec, want=("shrine", "fountain", "take the", "unlock", "vault"), radii=(150.0, 190.0, 230.0, 120.0)):
    """a floor point beside a fixture, in its room, from which F names it"""
    gen = G["gen"]
    for r_ in radii:
        for k in range(16):
            q = V(at.x + math.cos(k * math.pi / 8) * r_, at.y + math.sin(k * math.pi / 8) * r_, 100.0)
            if sec.room_at(q) != room: continue
            dn = str(gen.describe_nearest(q, 280.0))
            if any(dn == w_ or (not w_.startswith("take the ") and w_ in dn) for w_ in want): return q
    return None
def mw2_go(target, room, sec, card, sub, want, approach=520.0, walk=True):
    """behind a card, she is put a few metres from a fixture in its room; she walks to it (walk False: she is put beside it)"""
    st = mw2_beside(target, room, sec, want)
    far = (mw_near_point(target, approach, sec) or mw_near_point(target, approach * 0.7, sec)) if walk else None
    if card: mw_card(card, sub)
    mw_set(far or st or V(target.x - 400, target.y, 100.0), face_to=target, side=-22.0, pitch=-18.0)
    yield from pause((MW_CARD + 0.3) if card else 0.3, lambda: camera(side=-22.0, pitch=-18.0, rate=1e6))
    if st is not None and walk: yield from to_point(st, 8.0, 40.0)
    G["heading"] = yaw_to(loc(), target); G["pawn"].set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), False)
    yield from pause(0.5, lambda: camera(side=-30.0, pitch=-20.0, rate=60.0))
def mw2_f(kind, **kw):
    gen, c = G["gen"], G["combat"]
    said = str(gen.describe_nearest(loc(), 280.0)); did = str(gen.interact_nearest(loc(), 280.0)); key_hit("f")
    event(kind, what=said, did=did, message=str(c.message), hp=round(c.get_health(), 1), mhp=c.get_max_health(), mana=round(c.get_mana(), 1),
          blessing=str(c.get_blessing()), speed=round(walk_speed_now(), 1), **kw)
    return did
def walk_speed_now(): return G["pawn"].get_editor_property("character_movement").get_editor_property("max_walk_speed")
def mw2_tier2(sets=None):
    """the reel's shortcut (said by its card): the start set cleared by the generator, tier 2 open, its sets generated"""
    gen = G["gen"]
    yield from mw_open_tier2(0)
    for xy in (sets or [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (-1, 1), (-1, -1), (1, -1)]):
        if not gen.is_section_generated(IP(*xy)): gen.generate_section_now(IP(*xy))
        yield
def mw2_hit_down(m, share, why):
    """the reel takes a monster's hit points down (said)"""
    hp = m.get_health(); m.apply_damage(hp * share, None); event("hp_down", monster=str(m.monster_name), was=round(hp), now=round(m.get_health()), why=why)

def run5m2():
    """(mistward_castle, the user's third list of 2026-10-27) each hero's new things and the castle's new rooms"""
    yield from mw_start()
    gen, c, p = G["gen"], G["combat"], G["pawn"]
    s0, centre, room, anvil = mw_hall()
    S["note"]["special_rooms"] = [str(x) for x in gen.get_special_room_lines()]
    yield from {"Warrior": mw2_warrior, "Mage": mw2_mage, "Warlock": mw2_warlock, "Rogue": mw2_rogue, "MartialArtist": mw3_martial}[HERO](s0, centre, room, anvil)
    # (to the end: whatever comes at her is fought (left idle, a boss's band killed the Rogue in a rehearsal))
    mw_quiet(False)
    while True:
        m = threat()
        if m is None or not m.is_aggro(): yield from pause(0.5, lambda: camera(side=30.0, pitch=-12.0, rate=12.0)); continue
        G["casts0"] = c.attacks_made
        yield from (fight(m) if HERO == "Mage" else fight3(m) if HERO == "Rogue" else fight_w(m))

def mw2_warrior(s0, centre, room, anvil):
    """the Warrior: what she starts with (the inventory's tabs: the Dagger, the worst shield, no armour); a sword taken from
    an armory's table (F); it goes into quick slot 2 (the key 2 in the inventory), 1 and 2 draw; she blocks two blows with
    the right mouse button held; tier 2's boss (its hit points taken down by the reel, said) slain: a slash, put on her
    sword from the inventory, and a fight with it; a set of armour (given, said): H hides and shows its helmet"""
    gen, c, p = G["gen"], G["combat"], G["pawn"]
    mw_set(V(centre.x + 250, centre.y + 150, 100.0), yaw=200.0, side=-25.0, pitch=-16.0)
    event("start", at=[round(loc().x), round(loc().y)], way="great hall", weapons=[str(w.name) for w in gen.get_editor_property("weapons")], shield=str(c.get_worn_shield()), armour=str(c.get_worn_armour()))
    yield from pause(2.4, lambda: camera(side=-25.0, pitch=-16.0, rate=40.0))
    # ---- what she starts with: the weapons tab (the Dagger), the armour tab (the worst shield, no armour)
    seg("inventory"); yield from mw2_inv(0, "start_gear"); yield from pause(2.2)
    yield from mw2_key("E", label="e_tab"); event("tab", tab=c.get_inventory_tab()); yield from pause(2.4)
    for _ in range(3): yield from mw2_key("E", label="e_tab"); event("tab", tab=c.get_inventory_tab()); yield from pause(0.6)
    yield from mw2_key("E", label="e_tab"); event("tab", tab=c.get_inventory_tab()); yield from pause(0.5)
    yield from mw2_close()
    # ---- an armory's table: the nearest one-handed sword lying on it
    picks = [str(x).split("|") for x in gen.get_pickup_lines()]
    kinds = {str(it.name): it for it in gen.get_editor_property("items")}
    swords = [q for q in picks if q[0] == "0" and q[1] == "0" and q[7] == "0" and q[8] == "1" and kinds.get(q[3]) and str(kinds[q[3]].kind.name) == "WEAPON"
              and any(w in q[3] for w in ("Sword", "Sabre", "Shortsword", "Axe"))]
    pk = min(swords, key=lambda q: math.hypot(float(q[4]) - centre.x, float(q[5]) - centre.y)) if swords else None
    if pk:
        at = V(float(pk[4]), float(pk[5]), 0.0); rm = s0.room_at(at)
        yield from mw2_go(at, rm, s0, "AN ARMORY'S TABLE", "in the start set: its tables hold weapons and shields of the set's tier", ("take the " + pk[3].lower(),), 380.0, walk=False)          # (F must name this sword there: beside it lie shields too)
        seg("pickup"); did = mw2_f("pickup", item=pk[3])
        yield from pause(2.2, lambda: camera(side=-40.0, pitch=-26.0, rate=40.0))
        # ---- quick slot 2: the inventory's weapons tab, the sword's row, the key 2
        seg("slots"); yield from mw2_inv(0, "slot", item=pk[3]); yield from mw2_cursor("weapon", pk[3]); yield from pause(0.8)
        yield from mw2_key("Two", label="2"); event("slot", item=pk[3], slots=[str(x) for x in c.get_quick_slots()]); yield from pause(1.6)
        yield from mw2_close()
        for k_, lab in (("Two", "2"), ("One", "1"), ("Two", "2")):
            yield from mw2_key(k_, label=lab); event("draw", key=lab, weapon=str(c.get_weapon_name()), shield_in_hand=bool(c.is_shield_in_hand())); yield from pause(1.3, lambda: camera(side=-35.0, pitch=-14.0, rate=40.0))
    # ---- a fight: she blocks two blows (the right mouse button held), then fights
    mw_quiet(False); seg("fight"); lure(); G["until"] = DUR - 34.0; tw = T()
    while threat() is None and T() - tw < 4.0: camera(side=25.0, pitch=-12.0, rate=25.0); yield
    m = threat() or nearest_monster(IP(0, 0), 60)
    if m is not None:
        # (she closes in (it may hang back); the shield goes up once it is in reach of her, and stays up for two of its blows)
        t0 = T(); route = None; rt = -9.0
        while alive(m) and d2(loc(), m.get_actor_location()) - m.capsule_component.get_scaled_capsule_radius() > 140.0 and T() - t0 < 8.0:
            if route is None or T() - rt > 0.6: route = Route(path(loc(), m.get_actor_location())); rt = T()
            move(route.target() if len(route.p) > 1 else m.get_actor_location(), run=True); doors()
            camera(side=30.0, pitch=-12.0, rate=60.0); yield
        b0 = c.blocked_hits; c.set_blocking(True); key_hit("rmb"); event("block", on=True, monster=str(m.monster_name)); t0 = T()
        while c.blocked_hits - b0 < 2 and T() - t0 < 9.0 and alive(m):
            ml = m.get_actor_location()
            G["heading"] = yaw_to(loc(), ml); p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), False)
            if d2(loc(), ml) - m.capsule_component.get_scaled_capsule_radius() > 160.0: move(ml, run=False)          # (blocking, at half speed)
            G["key_hit"] = "rmb"; G["keys_t"] = T(); camera(side=35.0, pitch=-12.0, rate=60.0); yield
        c.set_blocking(False); event("block", on=False, blocked=c.blocked_hits - b0, share=round(c.last_shield_share, 3), wear=round(c.last_shield_wear, 2))
        G["casts0"] = c.attacks_made; yield from fight_w(m)
    lure(False)
    # ---- tier 2's boss: slain, a slash
    G["until"] = DUR + 1.0; mw_quiet(True)
    mw_card("TIER 2 OPENS: ITS BOSS", "the reel's shortcut: the start set cleared by the generator; the boss's hit points taken down to a fifth")
    yield from mw2_tier2([])
    boss = next((e for e in mw_encounters() if e["kind"] == "boss" and "USURPER" not in "|".join(e["rest"])), None)
    bm = None
    if boss is not None:
        stand = mw_near_point(boss["at"], 900.0) or mw_near_point(boss["at"], 600.0)
        if stand is not None: mw_set(stand, face_to=boss["at"], side=-18.0, pitch=-14.0)
        bm = min((q for q in gen.get_monsters() if alive(q) and q.boss), key=lambda q: d2(q.get_actor_location(), boss["at"]), default=None)
        if bm is not None: mw2_hit_down(bm, 0.8, "the reel takes the boss down to a fifth of its hit points")
        event("at_boss", boss=boss["name"], m=round(d2(loc(), boss["at"]) / 100.0, 1))
    c.set_health(c.get_max_health())
    yield from pause(MW_CARD + 0.2, lambda: camera(side=-18.0, pitch=-14.0, rate=1e6))
    mw_quiet(False); lure(); seg("boss"); g0 = len(gen.slashes_given)
    if bm is not None:
        G["casts0"] = c.attacks_made; G["until"] = DUR - 20.0
        while alive(bm) and T() < DUR - 20.0:
            yield from fight_w(bm)
            o = threat()
            if o is not None and o != bm and alive(bm): yield from fight_w(o)
    lure(False); mw_quiet(True); G["until"] = DUR + 1.0
    got = [str(x) for x in gen.slashes_given][g0:]
    event("slash_given", slashes=got, notice=str(gen.tier_notice))
    yield from pause(2.6, lambda: camera(side=-30.0, pitch=-18.0, rate=40.0))
    # ---- the slash on the weapon in her hands: the magic tab, Enter, the weapon, Enter
    if got:
        seg("slash"); yield from mw2_inv(0, "slash", slash=got[0]); yield from mw2_key("Q", label="q_tab"); event("tab", tab=c.get_inventory_tab()); yield from pause(0.8)
        yield from mw2_cursor("slash", got[0]); yield from pause(0.8)
        ok = c.use_inventory_entry(); key_hit("enter"); event("slash_pick", ok=bool(ok), lines=[str(x) for x in c.get_slash_lines()]); yield from pause(1.4)
        want = next((i for i, x in enumerate(str(y) for y in c.get_slash_lines()) if x.split("|")[1] == str(c.get_weapon_index())), 0)
        # (the cursor moved as S moves it: in a render the pointer, resting over the list, took the key's moves back)
        n_ = 0
        while c.is_picking_slash() and c.get_slash_cursor() != want and n_ < 8: c.move_slash_cursor(1); key_hit("s"); n_ += 1; yield from pause(0.35)
        yield from pause(0.8); ok = c.slash_entry(-1); key_hit("enter")
        event("slash_on", ok=bool(ok), weapon=str(c.get_weapon_name()), slash=got[0], message=str(c.message)); yield from pause(1.8)
        yield from mw2_close()
        # ---- a fight with it
        mw_quiet(False); lure(); seg("fight"); p0 = dict((str(k), v) for k, v in c.slash_procs.items())
        G["until"] = DUR - 9.0
        while T() < DUR - 9.0:
            m = threat() or nearest_monster(None, 40, 3000.0)
            if m is None: yield from pause(0.4, lambda: camera(side=20.0, rate=20.0)); continue
            G["casts0"] = c.attacks_made; yield from fight_w(m)
            if any(v > p0.get(str(k), 0) for k, v in c.slash_procs.items()) and not alive(m): break
        event("slash_procs", procs={str(k): v for k, v in c.slash_procs.items()}, bonus=round(c.slash_bonus_dealt, 1))
        lure(False)
    # ---- a set with a helmet (given, said): H hides it and shows it again
    G["until"] = DUR + 1.0; mw_quiet(True)
    arm = "Plate Armour"; c.add_item(arm, 1); event("given", items={arm: 1}, why="helmet")
    c.wear_armour(arm); event("worn_set", set=arm, helmet=[str(x) for x in c.get_helmet_lines()])
    yield from orbit(1.6, 150.0, 40.0, -6.0)
    seg("helmet"); yield from mw2_key("H", label="h"); event("helmet", hidden=bool(c.is_helmet_hidden())); yield from orbit(2.2, 190.0, -30.0, -6.0)
    yield from mw2_key("H", label="h"); event("helmet", hidden=bool(c.is_helmet_hidden())); yield from orbit(1.8, 160.0, 30.0, -6.0)

def mw2_mage(s0, centre, room, anvil):
    """the Mage: the inventory's five tabs (her things given, said); the start set's shrine (a blessing); a fight; its fountain
    of mana; tier 2 (the reel's shortcut): a healing fountain"""
    gen, c, p = G["gen"], G["combat"], G["pawn"]
    mw_set(V(centre.x - 200, centre.y + 120, 100.0), yaw=30.0, side=-25.0, pitch=-16.0)
    event("start", at=[round(loc().x), round(loc().y)], way="great hall")
    give = {"Small Healing Potion": 2, "Small Mana Potion": 2, "Bread": 1, "Iron Ingot": 3, "Timber": 2, "Whetstone": 1}
    rings = [str(i.name) for i in gen.get_editor_property("items") if i.kind == unreal.RDItemKind.RING and "Magic" in str(i.name)]
    if rings: give[rings[0]] = 1
    for k_, n_ in give.items(): c.add_item(k_, n_)
    event("given", items=give, why="tabs")
    yield from pause(2.2, lambda: camera(side=-25.0, pitch=-16.0, rate=40.0))
    seg("inventory"); yield from mw2_inv(0, "tabs"); yield from pause(1.6)
    for _ in range(4): yield from mw2_key("E", label="e_tab"); event("tab", tab=c.get_inventory_tab()); yield from pause(1.5)
    yield from mw2_key("Q", label="q_tab"); event("tab", tab=c.get_inventory_tab()); yield from pause(1.2)
    yield from mw2_close()
    # ---- the shrine
    sh = next(iter(mw2_rooms("Shrine", (0, 0))), None)
    if sh:
        yield from mw2_go(sh["at"], sh["room"], s0, "A SHRINE", "a room of the start set: pray at it (F) for a blessing", ("shrine",))
        seg("shrine"); mw2_f("shrine"); yield from pause(2.6, lambda: camera(side=-50.0, pitch=-30.0, rate=40.0))          # (a turn to her front put the camera into her: the fixture stops the boom)
    # ---- a fight (lured), then the fountain of mana
    mw_quiet(False); seg("fight"); lure(); G["until"] = DUR - 22.0
    while T() < DUR - 26.0 and c.get_mana() > c.get_max_mana() * 0.35:
        m = threat() or nearest_monster(IP(0, 0), 60)
        if m is None: yield from pause(0.4, lambda: camera(side=20.0, rate=20.0)); continue
        G["casts0"] = c.attacks_made; yield from fight(m)
    lure(False); mw_quiet(True)
    mf = next(iter(mw2_rooms("Fountain of mana", (0, 0))), None)
    if mf:
        yield from mw2_go(mf["at"], mf["room"], s0, "A FOUNTAIN OF MANA", "a room of the start set: once, her mana full again", ("fountain",))
        seg("fountain"); mw2_f("fountain", which="mana"); yield from pause(2.4, lambda: camera(side=-50.0, pitch=-30.0, rate=40.0))
    # ---- tier 2: a healing fountain
    t_card = T(); mw_card("TIER 2: A HEALING FOUNTAIN", "the reel's shortcut: the start set cleared by the generator, tier 2's sets generated; her hit points taken down (said)")
    yield from mw2_tier2()
    hf = next((r for r in mw2_rooms("Healing fountain") if not (r["s"].x == 0 and r["s"].y == 0)), None) or next(iter(mw2_rooms("Healing fountain")), None)
    if hf:
        sec = gen.get_section(hf["s"])
        c.set_health(c.get_max_health() * 0.3); event("hp_set", hp=round(c.get_health(), 1), why="the reel takes her hit points down: to show the fountain")
        st = mw2_beside(hf["at"], hf["room"], sec, ("fountain",)) or V(hf["at"].x - 200, hf["at"].y, 100.0)
        mw_set(st, face_to=hf["at"], side=-22.0, pitch=-18.0)
        # (the drink after the card: in the render the sets were generated at once and she drank behind it)
        while T() < t_card + MW_CARD + 0.4: camera(side=-22.0, pitch=-18.0, rate=1e6); yield
        yield from pause(1.4, lambda: camera(side=-28.0, pitch=-18.0, rate=40.0))
        seg("fountain"); mw2_f("fountain", which="heal"); yield from pause(2.6, lambda: camera(side=-50.0, pitch=-30.0, rate=40.0))
    mw_quiet(False); lure()
    while T() < DUR - 1.0:
        m = threat() or nearest_monster(None, 40, 3000.0)
        if m is None: yield from pause(0.4, lambda: camera(side=20.0, rate=20.0)); continue
        G["casts0"] = c.attacks_made; yield from fight(m)

def mw2_warlock(s0, centre, room, anvil):
    """the Warlock: the start set's vault (locked: F says so), its key from a chest of another room, the vault opened and
    a chest of it; the fountain of speed; the arena (its doors shut behind her, three waves, the prize)"""
    gen, c, p = G["gen"], G["combat"], G["pawn"]
    va = next(iter(mw2_rooms("Vault", (0, 0))), None)
    if va:
        doors = list(s0.get_room_doors(va["room"]))
        rc = s0.get_room_center(va["room"])
        dl = min((s0.get_door_location(i) for i in doors), key=lambda q: d2(q, centre)) if doors else rc
        out = V(dl.x + (dl.x - rc.x) / max(d2(dl, rc), 1.0) * 200.0, dl.y + (dl.y - rc.y) / max(d2(dl, rc), 1.0) * 200.0, 100.0)
        # (a stand point outside the vault from which F names its door, with room behind her for the camera: straight out
        # from the door a wall stood close behind her and the camera was pressed into her cape)
        for r_ in (200.0, 240.0, 170.0, 280.0):
            got = None
            for k in range(16):
                q = V(dl.x + math.cos(k * math.pi / 8) * r_, dl.y + math.sin(k * math.pi / 8) * r_, 100.0)
                if s0.room_at(q) == va["room"] or "vault" not in str(gen.describe_nearest(q, 280.0)): continue
                bk = V(q.x - dl.x, q.y - dl.y, 0.0); bk = bk * (1.0 / max(bk.length(), 1.0))
                if sweep_clear(q, V(q.x + bk.x * 380.0, q.y + bk.y * 380.0, 100.0), 35.0): got = q; break
            if got is not None: out = got; break
        # (at the vault's door: F names it there (walking up through other doors, F once took a door she had passed))
        mw_set(out, face_to=dl, side=-20.0, pitch=-34.0)
        event("start", at=[round(loc().x), round(loc().y)], way="the start set's vault", near=str(gen.describe_nearest(loc(), 280.0)))
        yield from pause(2.6, lambda: camera(side=-20.0, pitch=-34.0, rate=40.0))
        seg("vault")
        mw2_f("vault", step="locked"); yield from pause(2.6, lambda: camera(side=-35.0, pitch=-18.0, rate=30.0))
        # ---- its key, in a chest of another room of the set
        kc = [i for i in range(s0.get_num_containers()) if "Vault Key" in [str(x) for x in gen.loot_list_of(IP(0, 0), i)]]
        if kc:
            at = s0.get_container_location(kc[0]); st = stand_by_chest(at, at, tol=450.0)
            if st is not None:
                mw_card("ITS KEY", "in a chest of another room of the same set of rooms (the reel takes her there)")
                far = mw_near_point(at, 520.0) or st
                mw_set(far, face_to=at, side=-22.0, pitch=-18.0)
                yield from pause(MW_CARD + 0.3, lambda: camera(side=-22.0, pitch=-18.0, rate=1e6))
                seg("chest"); yield from open_chest(at, st)
                event("key", has=c.get_item_count("Vault Key"))
                yield from pause(1.6, lambda: camera(side=-30.0, pitch=-22.0, rate=40.0))
        mw_card("BACK AT THE VAULT", "the reel takes her back to its door")
        mw_set(out, face_to=dl, side=-20.0, pitch=-34.0)
        yield from pause(MW_CARD + 0.3, lambda: camera(side=-20.0, pitch=-34.0, rate=1e6))
        seg("vault"); mw2_f("vault", step="open", key_left=c.get_item_count("Vault Key")); yield from pause(1.6, lambda: camera(side=-25.0, pitch=-16.0, rate=40.0))
        vc = [i for i in range(s0.get_num_containers()) if s0.room_at(s0.get_container_location(i)) == va["room"]]
        if vc:
            at = min((s0.get_container_location(i) for i in vc), key=lambda q: d2(q, dl)); st = stand_by_chest(at, loc(), tol=450.0)
            if st is not None: seg("chest"); yield from open_chest(at, st); yield from pause(1.2, lambda: camera(side=-30.0, pitch=-22.0, rate=40.0))
    # ---- the fountain of speed
    sf = next(iter(mw2_rooms("Fountain of speed", (0, 0))), None)
    if sf:
        yield from mw2_go(sf["at"], sf["room"], s0, "A FOUNTAIN OF SPEED", "a room of the start set: once, 30 % faster for a while", ("fountain",))
        seg("fountain"); mw2_f("fountain", which="speed"); yield from pause(1.8, lambda: camera(side=-50.0, pitch=-30.0, rate=40.0))
    # ---- the arena: she steps in, its doors shut, three waves
    ar = next(iter(mw2_rooms("Arena", (0, 0))), None)
    if ar:
        rc = s0.get_room_center(ar["room"]); doors = list(s0.get_room_doors(ar["room"]))
        dl = min((s0.get_door_location(i) for i in doors), key=lambda q: d2(q, rc)) if doors else rc
        inside = V(dl.x + (rc.x - dl.x) * 0.25, dl.y + (rc.y - dl.y) * 0.25, 100.0)
        outside = V(dl.x - (rc.x - dl.x) / max(d2(rc, dl), 1.0) * 300.0, dl.y - (rc.y - dl.y) / max(d2(rc, dl), 1.0) * 300.0, 100.0)
        mw_card("THE ARENA", "a room of the start set: its doors shut behind her until three waves of monsters are beaten")
        mw_set(outside, face_to=rc, side=-15.0, pitch=-14.0); c.set_health(c.get_max_health())
        yield from pause(MW_CARD + 0.3, lambda: camera(side=-15.0, pitch=-14.0, rate=1e6))
        mw_quiet(False); seg("arena"); yield from to_point(V(rc.x, rc.y, 100.0), 8.0, 200.0)
        t0 = T()
        while gen.get_arena_wave() < 0 and T() - t0 < 3.0: camera(side=30.0, pitch=-14.0, rate=30.0); yield
        event("arena", begun=gen.get_arena_wave() >= 0, doors_open=sum(1 for i in doors if s0.is_target_open(True, i)))
        def arena_foe():
            # (one of the arena's own (spawned at its far side, not yet after her), else whoever is after her)
            ms = [q for q in gen.get_monsters() if alive(q) and s0.room_at(q.get_actor_location()) == ar["room"]]
            return threat() or (min(ms, key=lambda q: d2(q.get_actor_location(), loc())) if ms else None)
        while T() < DUR - 6.0 and md_get(gen.room_uses, "arena_won") == 0:
            m = arena_foe()
            if m is None: yield from pause(0.3, lambda: camera(side=25.0, pitch=-14.0, rate=30.0)); continue
            G["casts0"] = c.attacks_made; yield from fight_w(m)
            event("arena_wave", wave=gen.get_arena_wave(), left=gen.get_arena_left())
        event("arena_won", won=md_get(gen.room_uses, "arena_won"), doors_open=sum(1 for i in doors if s0.is_target_open(True, i)))
        pile = next((x for x in gen.loot_piles if x and not x.hers), None)
        if pile is not None and T() < DUR - 3.0:
            pl = pile.get_actor_location(); seg("prize"); yield from to_point(V(pl.x, pl.y, 100.0), 4.0, 90.0)
            r_ = str(gen.interact_nearest(loc(), 260.0)); key_hit("f"); event("prize", did=r_, message=str(c.message))
def md_get(m, k):
    try: return {str(a): b for a, b in m.items()}.get(k, 0)
    except Exception: return 0

def mw2_rogue(s0, centre, room, anvil):
    """the Rogue: a trap seen from 8 m outlined in red (its plate, a disc at its reach, a red glow); the trap gauntlet: its
    traps outlined as she sees them, one disarmed, its chest at the far end; tier 2 (the reel's shortcut): the throne room's
    usurper (its hit points taken down, said)"""
    gen, c, p = G["gen"], G["combat"], G["pawn"]
    gt = next(iter(mw2_rooms("Trap gauntlet", (0, 0))), None)
    traps = []
    for l in gen.get_trap_lines():
        q = str(l).split("|")
        if q[0] == "0" and q[1] == "0" and q[8] == "0": traps.append({"i": int(q[2]), "name": q[3], "at": V(float(q[5]), float(q[6]), float(q[7])), "room": int(q[10]) if len(q) > 10 else -1})
    # ---- a trap of the gauntlet seen from its door: outlined as she comes within 8 m
    room_t = [t_ for t_ in traps if gt and t_["room"] == gt["room"]]
    if not gt or not room_t: event("no_gauntlet"); return
    rc = s0.get_room_center(gt["room"]); doors = list(s0.get_room_doors(gt["room"]))
    dl = min((s0.get_door_location(i) for i in doors), key=lambda q: d2(q, centre)) if doors else rc
    back = V(dl.x - (rc.x - dl.x) / max(d2(rc, dl), 1.0) * 700.0, dl.y - (rc.y - dl.y) / max(d2(rc, dl), 1.0) * 700.0, 100.0)
    if s0.room_at(back) < 0 and not len(path(back, dl)): back = V(dl.x - (rc.x - dl.x) / max(d2(rc, dl), 1.0) * 300.0, dl.y - (rc.y - dl.y) / max(d2(rc, dl), 1.0) * 300.0, 100.0)
    mw_set(back, face_to=rc, side=-15.0, pitch=-20.0); mw_quiet(True)
    event("start", at=[round(loc().x), round(loc().y)], way="the trap gauntlet's door", traps=len(room_t))
    yield from pause(2.4, lambda: camera(side=-15.0, pitch=-20.0, rate=40.0))
    seg("trap"); yield from to_point(V(dl.x, dl.y, 100.0), 6.0, 60.0)
    t0 = T()
    while T() - t0 < 2.2: camera(side=-10.0, pitch=-28.0, rate=40.0); yield
    seen = [t_ for t_ in [str(x).split("|") for x in gen.get_trap_lines()] if t_[0] == "0" and t_[1] == "0" and t_[9] == "1"]
    event("outlined", n=len(seen), names=[x[3] for x in seen])
    # ---- the nearest of them disarmed (F)
    first = min(room_t, key=lambda t_: d2(t_["at"], loc()))
    st = V(first["at"].x + (loc().x - first["at"].x) / max(d2(loc(), first["at"]), 1.0) * 170.0, first["at"].y + (loc().y - first["at"].y) / max(d2(loc(), first["at"]), 1.0) * 170.0, 100.0)
    yield from to_point(st, 5.0, 30.0)
    G["heading"] = yaw_to(loc(), first["at"]); p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), False)
    yield from pause(0.6, lambda: camera(side=-35.0, pitch=-26.0, rate=50.0))
    said = str(gen.describe_nearest(loc(), 260.0)); r_ = str(gen.interact_nearest(loc(), 260.0)); key_hit("f")
    event("disarm", what=said, did=r_)
    t0 = T()
    while T() - t0 < gen.disarm_seconds + 0.6: camera(side=-40.0, pitch=-26.0, rate=20.0); yield
    event("disarmed", n=gen.traps_disarmed, message=str(c.message))
    # ---- its chest at the far end (the reel's way round the others: the tile path)
    ch = [i for i in range(s0.get_num_containers()) if s0.room_at(s0.get_container_location(i)) == gt["room"]]
    if ch:
        at = s0.get_container_location(ch[0]); st = stand_by_chest(at, loc(), tol=450.0)
        if st is not None: seg("chest"); yield from open_chest(at, st); yield from pause(1.4, lambda: camera(side=-30.0, pitch=-22.0, rate=40.0))
    # ---- tier 2: the throne room's usurper
    mw_card("TIER 2: A THRONE ROOM", "the reel's shortcut: the start set cleared by the generator, tier 2's sets generated; the usurper's hit points taken down (said)")
    yield from mw2_tier2()
    th = next(iter(mw2_rooms("Throne room")), None)
    us = next((e for e in mw_encounters() if "USURPER" in "|".join(e["rest"])), None)
    if th and us:
        sec = gen.get_section(th["s"]); um = min((q for q in gen.get_monsters() if alive(q) and q.boss), key=lambda q: d2(q.get_actor_location(), us["at"]), default=None)
        if um is not None: mw2_hit_down(um, 0.8, "the reel takes the usurper down to a fifth of its hit points")
        stand = mw_near_point(us["at"], 1100.0, sec) or mw_near_point(us["at"], 800.0, sec)
        if stand is not None: mw_set(stand, face_to=th["at"], side=-15.0, pitch=-12.0)
        event("at_throne", usurper=us["name"], label="|".join(us["rest"]), m=round(d2(loc(), us["at"]) / 100.0, 1))
        c.set_health(c.get_max_health())
        yield from pause(MW_CARD + 0.3, lambda: camera(side=-15.0, pitch=-12.0, rate=1e6))
        seg("throne"); yield from orbit(2.4, -20.0, 40.0, -12.0)
        mw_quiet(False); lure()
        while um is not None and alive(um) and T() < DUR - 5.0:
            G["casts0"] = c.attacks_made; seg("fight"); yield from fight3(um)
            o = threat()
            if o is not None and o != um and alive(um): yield from fight3(o)
        lure(False)
        event("usurper", slain=not alive(um) if um is not None else None, notice=str(gen.tier_notice), uses=md_get(gen.room_uses, "usurper"))

def mw3_slots(why):
    c = G["combat"]; event("bar", why=why, slots=[str(x) for x in c.get_quick_slots()], first=c.get_quick_first(), cursor=c.get_quick_cursor(),
                          ready=str(c.get_ready_ability()), weapon=str(c.get_weapon_name()))
def mw3_cast(name, near=300.0):
    """(mw3) one chi attack (drawn from the bar) at the nearest monster: she closes to within `near` (a chi reaches 4 m),
    faces it, strikes; the reel fills her mana first (said by the caption)"""
    gen, c, p = G["gen"], G["combat"], G["pawn"]
    # (a caged monster, behind its cell's bars, is out of her sight: a chi at it is refused)
    G.setdefault("skip", set()).update(q.get_name() for q in gen.get_monsters() if alive(q) and q.caged)
    m = threat()
    if m is not None and m.get_name() in G.get("skip", ()): m = None          # (one left before: caged, out of her sight)
    # (in the great hall: the lured come to her there (a chase into the hallways put the camera in her hair); only after 5 s
    # with nobody she goes for the nearest, 25 m at most)
    t5 = T()
    while m is None and T() - t5 < 5.0:
        camera(side=25.0, pitch=-13.0, rate=25.0); yield
        m = threat()
        if m is not None and m.get_name() in G.get("skip", ()): m = None
    m = m or nearest_monster(IP(0, 0), 60, 2500.0)
    if m is None: return False
    t0 = T(); route = None; rt = -9.0
    while alive(m) and T() - t0 < 6.0:
        l = loc(); ml = m.get_actor_location(); gap = d2(l, ml) - m.capsule_component.get_scaled_capsule_radius()
        if gap < near: break
        if route is None or T() - rt > 0.6: route = Route(path(l, ml)); rt = T()
        move(route.target() if len(route.p) > 1 and gap > 300.0 else ml, run=True); doors()
        camera(side=30.0, pitch=-13.0, rate=70.0); yield
    if not alive(m): return False
    ml = m.get_actor_location(); G["heading"] = yaw_to(loc(), ml); p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), False)
    c.set_mana(c.get_max_mana()); h0 = m.get_health(); a0 = c.attacks_made
    ok = c.start_attack(); key_hit("lmb")
    if not ok:
        # (refused: no monster she can see within its 4 m (a pillar between): closer, then once more)
        t2 = T()
        while alive(m) and T() - t2 < 4.0 and (d2(loc(), m.get_actor_location()) - m.capsule_component.get_scaled_capsule_radius() > 140.0 or not sees(loc(), m)):
            move(m.get_actor_location(), run=True); doors(); camera(side=30.0, pitch=-13.0, rate=70.0); yield
        if not alive(m): return False
        # (she faces it over a few frames, the camera behind her, and tries again every quarter second)
        for _ in range(6):
            t3 = T()
            while T() - t3 < 0.25:
                ml = m.get_actor_location(); G["heading"] = yaw_to(loc(), ml); p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), False)
                camera(side=20.0, pitch=-13.0, rate=200.0); yield
            if not alive(m): return False
            c.set_mana(c.get_max_mana()); ok = c.start_attack(); key_hit("lmb")
            if ok: break
        if not ok:
            # (still refused: one she cannot see (a caged monster behind its bars): left for another)
            G.setdefault("skip", set()).add(m.get_name()); event("chi_refused", name=name, monster=str(m.monster_name), msg=str(c.message)); return False
    event("chi", name=name, ok=bool(ok), msg=str(c.message), drawn=str(c.get_weapon_name()), attacking=bool(c.is_attacking()), gap=round(d2(loc(), m.get_actor_location()), 0), dz=round(m.get_actor_location().z - loc().z, 0), monster=str(m.monster_name), damage=round(c.get_damage_of(c.get_weapon_index()), 1), mana=round(gen.get_editor_property("weapons")[c.get_weapon_index()].mana_cost))
    # (the camera from her front right while the move plays: its look is on her fists and legs)
    t1 = T(); wide = wide_here()
    while (c.is_attacking() or T() - t1 < 0.3) and T() - t1 < 2.5:
        # (from her front right where there is room; in a hallway from behind and above her, as a fight's camera)
        camera(side=125.0, pitch=-10.0, rate=140.0) if wide else camera(side=8.0, pitch=-25.0, rate=80.0); yield
    event("chi_done", name=name, lost=round(h0 - (m.get_health() if alive(m) else 0.0), 1), killed=not alive(m))
    yield from pause(0.5, lambda: camera(side=60.0, pitch=-12.0, rate=60.0))
    return True
def mw3_to(name):
    """(mw3) her number key for a slot of the first ten; past the tenth the D-pad right until the bar's chosen slot draws
    `name` (an ability on the way is made ready and passed)"""
    c = G["combat"]; n = 0
    qs = [str(x) for x in c.get_quick_slots()]
    if name in qs and qs.index(name) < 10:
        k = qs.index(name); yield from mw2_key(NUMS[k], label=str((k + 1) % 10)); mw3_slots("key"); yield from pause(0.3); return
    while (str(c.get_weapon_name()) != name or str(c.get_ready_ability()) != "None") and n < 16:
        yield from mw2_key("Gamepad_DPad_Right", label="dpad_right"); n += 1; mw3_slots("dpad"); yield from pause(0.25)
def mw3_martial(s0, centre, room, anvil):
    """the Martial Artist (the user's of 2026-10-28 and 2026-10-29): the reel teaches her the eight chi attacks four tier
    bosses would (said); the inventory's weapons tab (the chi attacks' pictures, her abilities); Dash put in quick slot 3
    (the key 3), Dodge on a new slot after the last (the D-pad to it, Y): thirteen slots; outside the D-pad steps through
    all of them, the ten pictures scrolling; each of her ten chi attacks drawn from the bar in turn and struck at a lured
    monster (the reel fills her mana before each, said), its look on her fists and legs; Dash made from the bar (ready on
    the D-pad, RB) and Dodge; her fists to the end"""
    gen, c, p = G["gen"], G["combat"], G["pawn"]
    mw_set(V(centre.x + 250, centre.y + 150, 100.0), yaw=200.0, side=-25.0, pitch=-16.0)
    event("start", at=[round(loc().x), round(loc().y)], way="great hall", weapons=[str(w.name) for w in gen.get_editor_property("weapons")])
    yield from pause(2.2, lambda: camera(side=-25.0, pitch=-16.0, rate=40.0))
    got = gen.unlock_hero_weapons(8)
    event("given", items={"chi attacks": 8}, why="the reel teaches her the eight chi attacks four tier bosses would", unlocked=[str(w.name) for w in gen.get_editor_property("weapons")])
    yield from pause(1.2); mw3_slots("taught")
    # ---- the inventory: her weapons and abilities; Dash into slot 3, Dodge after the last
    seg("inventory"); yield from mw2_inv(0, "quickbar"); yield from pause(2.4)
    yield from mw2_cursor("ability", "Dash"); yield from pause(1.0)
    yield from mw2_key("Three", label="3"); mw3_slots("dash_in_3"); yield from pause(2.0)
    yield from mw2_cursor("ability", "Dodge"); yield from pause(0.8)
    end = len(c.get_quick_slots()); n = 0
    while c.get_assign_slot() != end and n < 24: yield from mw2_key("Gamepad_DPad_Right", label="dpad_right"); n += 1; yield from pause(0.12)
    yield from pause(0.6); yield from mw2_key("Gamepad_FaceButton_Top", label="y"); mw3_slots("dodge_at_end"); yield from pause(2.0)
    yield from mw2_close()
    # ---- the D-pad through the whole bar: the pictures scroll past the tenth
    seg("dpad"); yield from mw2_key("One", label="1"); mw3_slots("one"); yield from pause(0.6)
    for _ in range(len([x for x in c.get_quick_slots() if str(x) != "None"])):
        yield from mw2_key("Gamepad_DPad_Right", label="dpad_right"); mw3_slots("dpad"); yield from pause(0.55, lambda: camera(side=-20.0, pitch=-14.0, rate=30.0))
    # ---- the ten chi attacks in turn, from the bar, at lured monsters; Dash and Dodge from the bar between
    mw_quiet(False); lure(); seg("chi")
    chis = [str(w.name) for w in gen.get_editor_property("weapons") if w.spell]
    for k, nm in enumerate(chis):
        if T() > DUR - 14.0: break
        yield from mw3_to(nm)
        tries = 0
        while tries < 3 and not (yield from mw3_cast(nm)): tries += 1; yield from pause(0.5)
        if k == 3:
            # (Dash: its slot's number (3) makes it at once, at a monster ahead (tried again if she was still in a move))
            d0 = c.dashes
            for _ in range(4):
                while c.is_attacking() or c.is_rolling(): yield
                m = threat() or nearest_monster(IP(0, 0), 60)
                if m is not None: G["heading"] = yaw_to(loc(), m.get_actor_location()); p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), False)
                yield from mw2_key("Three", label="3"); yield from pause(0.3)
                if c.dashes > d0: break
            event("ability", name="Dash", made=c.dashes - d0, how="its slot's number, 3")
            yield from pause(1.4, lambda: camera(side=40.0, pitch=-12.0, rate=60.0))
        if k == 6:
            # (Dodge: on the last slot, past the ten shown: the D-pad left from the first comes round to it, then RB)
            while c.is_attacking() or c.is_rolling(): yield
            yield from mw2_key("One", label="1"); yield from mw2_key("Gamepad_DPad_Left", label="dpad_left"); mw3_slots("dodge_ready"); yield from pause(0.6)
            r0 = c.rolls
            for _ in range(4):
                if str(c.get_ready_ability()) != "@Dodge": yield from mw2_key("Gamepad_DPad_Left", label="dpad_left")
                yield from mw2_key("Gamepad_RightShoulder", label="rb"); yield from pause(0.3)
                if c.rolls > r0: break
            event("ability", name="Dodge", made=c.rolls - r0, how="ready on the D-pad, then RB")
            yield from pause(1.2, lambda: camera(side=40.0, pitch=-12.0, rate=60.0))
    # ---- her fists to the end
    yield from mw2_key("One", label="1"); mw3_slots("fists"); seg("fists")
    while T() < DUR - 1.0:
        m = threat() or nearest_monster(IP(0, 0), 60)
        if m is None: yield from pause(0.4, lambda: camera(side=20.0, rate=20.0)); continue
        G["casts0"] = c.attacks_made; yield from fight_w(m)
    lure(False)

# ---------------------------------------------------------------- mistward4: the six heroes in combat at all five tiers (the user's of 2026-10-30)
def mw4_tiers(upto):
    """(mw4) the reel's shortcut, said by its card: tiers 2 to `upto` open (ARDDungeonGenerator.DebugOpenTiers)"""
    gen = G["gen"]; n = gen.debug_open_tiers(upto, False)
    event("tiers_open", upto=upto, opened=n, notice=str(gen.tier_notice))
def mw4_land(xy, card, sub):
    """(mw4) behind a card: the set of rooms at xy generated now (its tier's look and monsters); she is set down in one of its
    rooms 8 to 12 m from one of its monsters, with a clear line to it; her hit points and mana full (the card says so)"""
    gen, p, c = G["gen"], G["pawn"], G["combat"]
    mw_quiet(True); mw_card(card, sub)
    S_ = IP(*xy)
    # (the generator drops the sets far from her: she is held over the set's middle while it is built (a set 4 away was
    # dropped as soon as it was made), then set down in it)
    size = gen.get_editor_property("section_tiles") * gen.get_editor_property("tile_size")
    hold = V(xy[0] * size, xy[1] * size, 400.0); G["lift_from"] = loc()
    p.set_actor_location(hold, False, True); p.get_editor_property("character_movement").set_editor_property("gravity_scale", 0.0)
    yield
    if not gen.is_section_generated(S_): gen.generate_section_now(S_)
    sx = gen.get_section(S_); t0 = T()
    while (sx is None or sx.is_building()) and T() - t0 < 10.0:
        p.set_actor_location(hold, False, True); p.get_editor_property("character_movement").stop_movement_immediately(); yield; sx = gen.get_section(S_)
    p.get_editor_property("character_movement").set_editor_property("gravity_scale", 1.0)
    ms = [m for m in (sx.spawned_monsters if sx else []) if alive(m) and not m.is_ally() and not m.caged]
    land = tgt = None
    for m in ms[:8]:
        ml = m.get_actor_location()
        for r_ in (1000.0, 800.0, 1200.0, 650.0):
            for k in range(12):
                q = V(ml.x + math.cos(k * math.pi / 6) * r_, ml.y + math.sin(k * math.pi / 6) * r_, 100.0)
                if sx.room_at(q) < 0 or not clear_line(q, ml) or not sweep_clear(q, V(q.x + 10.0, q.y, 100.0), 45.0): continue
                land, tgt = q, m; break
            if land: break
        if land: break
    if land is None:
        # (no landing (the set unbuilt, or no point with a clear line): back where she was lifted from, the monsters let loose
        # again (the PR review's find: she was left in the air and the monsters quiet))
        event("no_landing", section=list(xy))
        p.set_actor_location(V(G.get("lift_from", loc()).x, G.get("lift_from", loc()).y, 100.0), False, True)
        mw_quiet(False); lure()
        return None
    mw_set(land, face_to=tgt.get_actor_location(), side=-20.0, pitch=-16.0)
    c.set_health(c.get_max_health()); c.set_mana(c.get_max_mana())
    event("landed", at=[round(land.x), round(land.y)], section=list(xy), tier=gen.tier_of(S_), theme=str(gen.get_theme_name(S_)), monster=str(tgt.monster_name),
          title=str(tgt.title), its_hit_points=tgt.get_max_health(), its_damage=tgt.get_damage(), monsters=len(ms))
    yield from pause(MW_CARD + 0.3, lambda: camera(side=-20.0, pitch=-16.0, rate=1e6))
    mw_quiet(False); lure()
    return tgt
def mw4_walk_on(dx=None, dy=None, sec=18.0):
    """(mw4) she leaves her set by a hallway toward a set next to it that is open and not made yet (the nearest such way out;
    or the side dx, dy): the game generates it as she comes (new terrain), and she walks into it; a monster that comes at her
    on the way is fought"""
    gen = G["gen"]; here = gen.world_to_section(loc()); sx = gen.get_section(here)
    pts = list(sx.get_portal_points()) if sx else []
    if not pts: event("no_way_on"); return
    # (each side's hallways out: the one she has the shortest way to (the set's tile path), to a set not generated yet whose
    # tier is open)
    best = None
    for ddx, ddy in ([(dx, dy)] if dx is not None else [(1, 0), (-1, 0), (0, 1), (0, -1)]):
        n_ = IP(here.x + ddx, here.y + ddy)
        if gen.is_section_generated(n_) or not gen.is_tier_open(gen.tier_of(n_)): continue
        top = max(q.x * ddx + q.y * ddy for q in pts)
        for q in pts:
            if q.x * ddx + q.y * ddy < top - 400.0: continue
            w_ = list(sx.find_path_world(loc(), q))
            if len(w_) > 1 and (best is None or len(w_) < len(best[3])): best = (ddx, ddy, q, w_)
    if best is None: event("no_way_on", portals=len(pts)); return
    dx, dy, portal, way = best; nxt = IP(here.x + dx, here.y + dy)
    if len(way) > 12:
        # (a set is 252 m across: far from its way out, a card sets her down 30 m before it, on her way there)
        mw_quiet(True); mw_card("ON TO THE NEXT SET OF ROOMS", "the reel sets her down by the hallway out of this one")
        st = way[-10]; mw_set(st, face_to=way[-6], side=-15.0, pitch=-15.0)
        event("set_down", at=[round(st.x), round(st.y)], to_portal_m=round(d2(st, portal) / 100.0, 1), was_way_m=len(way) * 3)
        yield from pause(MW_CARD + 0.3, lambda: camera(side=-15.0, pitch=-15.0, rate=1e6))
        mw_quiet(False); lure()
        way = list(sx.find_path_world(loc(), portal)) or way[-10:]
    was = bool(gen.is_section_generated(nxt))
    event("walk_on", to=[nxt.x, nxt.y], tier=gen.tier_of(nxt), theme=str(gen.get_theme_name(nxt)), generated_before=was, way_m=len(way) * 3)
    route = Route(way + [V(portal.x + 300.0 * k * dx, portal.y + 300.0 * k * dy, portal.z) for k in range(1, 6)])
    t0 = T(); gen_t = None; stuck = 0.0; last = loc()
    seg("walk_on")
    while T() - t0 < sec:
        if gen_t is None and gen.is_section_generated(nxt):
            gen_t = T(); event("new_terrain", coord=[nxt.x, nxt.y], tier=gen.tier_of(nxt), theme=str(gen.get_theme_name(nxt)), her_m=round(d2(loc(), portal) / 100.0, 1))
        w = gen.world_to_section(loc())
        if w.x == nxt.x and w.y == nxt.y and gen_t is not None and route.done(): break
        m = mw4_threat()
        if m is not None and m.is_aggro():
            tf = T(); yield from mw4_fight(m); t0 += T() - tf          # (the fight's time is not the walk's)
            back = list(sx.find_path_world(loc(), portal)) if section_of(loc()) == sx else []
            route = Route(back + route.p[-5:]) if len(back) > 1 else Route(route.p[route.i:]); continue
        move(route.target(), run=True); doors(); camera(side=-15.0, pitch=-15.0, rate=60.0)
        stuck = stuck + G["el"] if d2(loc(), last) < 60.0 * G["el"] else 0.0; last = loc()
        if stuck > 1.2:
            stuck = 0.0; ps = path(loc(), route.p[-1])
            if len(ps) > 1: route = Route(ps); event("repath")
        yield
    event("walked_on", into=[nxt.x, nxt.y], inside=bool(gen.world_to_section(loc()).x == nxt.x and gen.world_to_section(loc()).y == nxt.y))
def mw4_heal():
    """(mw4) the reel fills her hit points when they are low (said: the higher tiers' blows end a run in a few)"""
    c = G["combat"]
    if c.get_health() < 0.75 * c.get_max_health():
        h = c.get_health(); c.set_health(c.get_max_health()); event("healed", was=round(h), now=round(c.get_max_health()))
MW4_PLAN = {"Mage": ["Frost Shard", "Chain Lightning", "Dark Fire", "Fire"], "Warlock": ["Curse of Frailty", "Shadow Lash", "Fire"]}
def mw4_cast_summons(names, most=9):
    """(mw4, the Summoner) each summoning of `names` she has, in turn (at most `most` casts), toward the monster ahead: the
    reel fills her mana before each (said: a summoning takes half her pool)"""
    gen, c, p = G["gen"], G["combat"], G["pawn"]; done = 0
    for nm in names:
        if done >= most: return
        wi = wi_of(nm)
        if wi is None: continue
        sp = gen.get_editor_property("spells")[gen.get_editor_property("weapons")[wi].spell_index]
        if gen.count_summoned(nm) >= sp.count: continue
        while c.is_attacking(): yield
        m = threat() or nearest_monster(None, 60, 3000.0)
        if m is not None: G["heading"] = yaw_to(loc(), m.get_actor_location()); p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), False)
        c.set_mana(c.get_max_mana()); event("mana_full", why=nm)
        draw(wi); n0 = gen.count_summoned(nm); ok = c.start_attack(); key_hit("lmb"); done += 1
        t1 = T()
        while (c.is_attacking() or T() - t1 < 0.4) and T() - t1 < 3.0: camera(side=150.0, pitch=-10.0, rate=120.0) if wide_here() else camera(side=10.0, pitch=-22.0, rate=80.0); yield
        al = [a for a in gen.get_allies() if str(a.summon_spell) == nm]
        event("summoned", spell=nm, ok=bool(ok), now=gen.count_summoned(nm), was=n0, most=sp.count, monster_kind=str(sp.summon_kind), message=str(c.message),
              allies=[{"monster": str(a.monster_name), "hp": round(a.get_max_health()), "damage": round(a.get_damage(), 1)} for a in al][:1])
        yield from pause(0.6, lambda: camera(side=60.0, pitch=-12.0, rate=60.0))
def mw4_spells(m, plan, then_sword=False, max_t=16.0):
    """(mw4) the Mage's and the Warlock's fight: each spell of her plan in turn (one on cooldown or wanting mana passed over,
    the last over and over), cast when the monster is within 12 m (in the rehearsal fight_s's sight test failed a whole fight
    in the dwarven halls, at 0.8 m: she cast nothing); the Warlock then her sword"""
    c = G["combat"]; p = G["pawn"]; gen = G["gen"]; G["fights"] += 1
    name = str(m.monster_name); hp0 = m.get_max_health(); h0 = c.get_health(); t0 = T(); b0 = c.hits_landed; k = 0; route = None; rt = -9.0
    event("fight", monster=name, title=str(m.title), its_hit_points=hp0, its_damage=m.get_damage(), ability=str(m.ability.name), tier=m.tier,
          section=[m.get_editor_property("section").get_editor_property("coord").x, m.get_editor_property("section").get_editor_property("coord").y],
          from_m=round((d2(loc(), m.get_actor_location())) / 100.0, 1), spells=plan, sword=then_sword)
    while alive(m) and not c.is_dead() and T() - t0 < max_t and T() < G.get("until", DUR + 1.0):
        l = loc(); ml = m.get_actor_location(); gap = d2(l, ml) - m.capsule_component.get_scaled_capsule_radius()
        G["heading"] = yaw_to(l, ml)
        if not c.is_attacking():
            p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=turn(p.get_actor_rotation().yaw, yaw_to(l, ml), 720.0 * G["el"])), False)
            ws = gen.get_editor_property("weapons")
            if then_sword and k >= len(plan):
                draw(0)
                if gap < ws[0].reach - 10.0: c.start_attack() and key_hit("lmb")
                else:
                    if route is None or T() - rt > 0.6: route = Route(path(l, ml)); rt = T()
                    move(route.target() if len(route.p) > 1 and gap > 300.0 else ml, run=True); doors()
            elif gap < 1200.0 and sees(l, m):          # (one in the next room within 12 m: her bolts burst on the wall between (the rehearsal))
                nm = plan[min(k, len(plan) - 1)]; wi = wi_of(nm)
                if wi is None or ((c.get_cooldown_left(wi) > 0.0 or c.get_mana() < ws[wi].mana_cost) and k < len(plan) - 1): k += 1; yield; continue
                if c.get_mana() >= ws[wi].mana_cost:
                    draw(wi)
                    if c.start_attack(): key_hit("lmb" if HERO == "Warlock" else "e"); k += 1
                elif then_sword: k = len(plan)          # (out of mana: her sword now)
            else:
                if route is None or T() - rt > 0.6: route = Route(path(l, ml)); rt = T()
                move(route.target() if len(route.p) > 1 and gap > 400.0 else ml, run=True); doors()
        camera(side=28.0 if wide_here() else 8.0, pitch=-14.0 if wide_here() else -25.0, rate=80.0)
        yield
        # (no nearer for 4 s and none of her spells cast (no way round to it): another one)
        if gap < G.get("mw4_best", (None, 1e9))[1] - 100.0 or G.get("mw4_best", (None,))[0] != m.get_name(): G["mw4_best"] = (m.get_name(), gap, T())
        if T() - G["mw4_best"][2] > 4.0 and c.attacks_made == G.get("casts0", 0): G.setdefault("skip", set()).add(m.get_name()); break
    G["last_fight"] = T()
    if not alive(m): event("kill", monster=name, casts=c.attacks_made - G.get("casts0", 0), blows=c.hits_landed - b0, seconds=round(T() - t0, 2), she_lost=round(max(0.0, h0 - c.get_health())), its_hit_points=hp0)
    else: event("left", monster=name)
    yield from pause(0.5, lambda: camera(side=18.0, rate=70.0))
def mw4_chi(m, n=3):
    """(mw4, the Martial Artist) up to `n` of her chi attacks in turn (each drawn by its number), each within 3.3 m of the
    monster (a chi reaches 4 m); the reel fills her mana before each (said)"""
    gen, c, p = G["gen"], G["combat"], G["pawn"]
    chis = [i for i, w in enumerate(gen.get_editor_property("weapons")) if w.spell]
    for _ in range(n):
        if not alive(m) or not chis: return
        k = G.setdefault("chi_k", 0); G["chi_k"] = k + 1; wi = chis[k % len(chis)]; nm = str(gen.get_editor_property("weapons")[wi].name)
        t0 = T(); route = None; rt = -9.0
        while alive(m) and T() - t0 < 6.0:
            l = loc(); ml = m.get_actor_location(); gap = d2(l, ml) - m.capsule_component.get_scaled_capsule_radius()
            if gap < 300.0 and sees(l, m): break
            if route is None or T() - rt > 0.6: route = Route(path(l, ml)); rt = T()
            move(route.target() if len(route.p) > 1 and gap > 300.0 else ml, run=True); doors(); camera(side=30.0, pitch=-13.0, rate=70.0); yield
        if not alive(m): return
        while c.is_attacking(): yield
        G["heading"] = yaw_to(loc(), m.get_actor_location()); p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), False)
        draw(wi); c.set_mana(c.get_max_mana()); h0 = m.get_health()
        ok = c.start_attack(); key_hit("lmb")
        event("chi", name=nm, ok=bool(ok), msg=str(c.message), monster=str(m.monster_name), damage=round(c.get_damage_of(wi), 1), mana=round(gen.get_editor_property("weapons")[wi].mana_cost))
        t1 = T(); wide = wide_here()
        while (c.is_attacking() or T() - t1 < 0.3) and T() - t1 < 2.5:
            camera(side=125.0, pitch=-10.0, rate=140.0) if wide else camera(side=8.0, pitch=-25.0, rate=80.0); yield
        event("chi_done", name=nm, lost=round(h0 - (m.get_health() if alive(m) else 0.0), 1), killed=not alive(m))
def mw4_fight(m):
    """(mw4) her kind of fight: the Warrior her sword and shield, the Rogue the crossbow, the daggers and the roll, the Mage and
    the Warlock their plans of spells (the Warlock then her sword), the Martial Artist her chi attacks then her fists, the
    Summoner her summonings first, then fire with her summoned at her side"""
    c = G["combat"]; G["casts0"] = c.attacks_made; mw4_heal(); seg("fight")
    if HERO == "Mage": yield from mw4_spells(m, MW4_PLAN["Mage"])
    elif HERO == "Warlock": yield from mw4_spells(m, MW4_PLAN["Warlock"], then_sword=True)
    elif HERO == "Rogue": yield from fight3(m)
    elif HERO == "Summoner":
        yield from mw4_cast_summons(G.get("summons", ["Summon Tier 1"]), most=1)
        if alive(m): yield from fight(m)
    elif HERO == "MartialArtist":
        yield from mw4_chi(m)
        if alive(m): draw(0); yield from fight_w(m)
    else: yield from fight_w(m)
def mw4_threat():
    """(mw4) threat(), but not a caged monster (behind its cell's bars) nor one she could not reach before (her spells burst on a
    wall a whole fight in the rehearsal): those are left out"""
    gen = G["gen"]; G.setdefault("skip", set()).update(q.get_name() for q in gen.get_monsters() if alive(q) and q.caged)
    l = loc(); best = None
    for m in gen.get_monsters():
        if not alive(m) or m.get_name() in G["skip"]: continue
        ml = m.get_actor_location(); d = d2(l, ml)
        if abs(ml.z - l.z) > 300: continue
        if (m.is_aggro() and d < 1500.0) or (d < 1500.0 and sees(l, m)):
            if best is None or d < best[0]: best = (d, m)
    return best[1] if best else None
def mw4_fights(kills, until):
    """(mw4) lured fights until `kills` fell or the time is up"""
    c = G["combat"]; k0 = sum(1 for e in S["events"] if e["kind"] == "kill"); u0 = G.get("until", DUR + 1.0); G["until"] = until + 1.5
    try:
        for _ in range(12):
            if T() > until - 3.0: return
            tw = T()
            while threat() is None and T() - tw < 2.0: camera(side=25.0, pitch=-12.0, rate=25.0); yield
            m = mw4_threat() or nearest_monster(None, 90, 6000.0)
            if m is None: event("no_monster"); return
            yield from mw4_fight(m)
            if sum(1 for e in S["events"] if e["kind"] == "kill") - k0 >= kills: return
    finally: G["until"] = u0
def mw4_harvest():
    """(mw4) the nearest harvest over a dead monster: she walks to it and F takes its parts (they float there until then)"""
    gen, c = G["gen"], G["combat"]
    # (a near one: a long walk to it ate the reel; within 30 m: in the render the Warrior chased her second monster 18 m
    #  from the first one's pile, and 10 m found none)
    piles = [q for q in gen.loot_piles if q and q.harvest and d2(q.get_actor_location(), loc()) < 3000.0]
    if not piles: event("no_harvest"); return
    q = min(piles, key=lambda x: d2(x.get_actor_location(), loc())); at = q.get_actor_location()
    event("to_harvest", things=[str(x) for x in q.things], tier=q.tier, m=round(d2(at, loc()) / 100.0, 1))
    seg("harvest"); yield from to_point(V(at.x, at.y, 100.0), 10.0, 110.0)
    G["heading"] = yaw_to(loc(), at); G["pawn"].set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), False)
    yield from pause(0.8, lambda: camera(side=-40.0, pitch=-24.0, rate=60.0))
    said = str(gen.describe_nearest(loc(), 260.0)); did = str(gen.interact_nearest(loc(), 260.0)); key_hit("f")
    event("harvest_taken", what=said, did=did, message=str(c.message))
    yield from pause(2.2, lambda: camera(side=-30.0, pitch=-20.0, rate=40.0))
def mw4_start(centre, yaw=200.0):
    mw_set(V(centre.x + 250, centre.y + 150, 100.0), yaw=yaw, side=-25.0, pitch=-16.0)
    event("start", at=[round(loc().x), round(loc().y)], way="great hall", weapons=[str(w.name) for w in G["gen"].get_editor_property("weapons")],
          hp=G["combat"].get_max_health(), mana=G["combat"].get_max_mana())
    yield from pause(2.0, lambda: camera(side=-25.0, pitch=-16.0, rate=40.0))
def mw4_warrior(s0, centre, room, anvil):
    """the Warrior (tiers 1 and 2): lured fights in the great hall with her sword and shield; a dead monster's harvest taken;
    tier 2 opens (the start set cleared, a card); she walks east into tier 2's first set, generated as she comes"""
    yield from mw4_start(centre)
    # (she starts with the dagger: the reel gives her a sword, one-handed, her shield on her arm with it)
    yield from give(["Arming Sword"], "sword"); yield from wield("Arming Sword", "weapon", "sword")
    mw_quiet(False); lure(); seg("tier1")
    # (the harvest right after her first kill, by its pile: taken after the second fight, she had chased that one 17 m off
    #  and the walk back left her 1 kill in the whole run)
    yield from mw4_fights(1, DUR * 0.3)
    yield from mw4_harvest()
    yield from mw4_fights(1, DUR * 0.42)
    mw_quiet(True); mw_card("TIER 2 OPENS", "the reel's shortcut: the start set cleared by the generator")
    yield from mw_open_tier2(0); yield from pause(MW_CARD + 0.3, lambda: camera(side=-20.0, pitch=-16.0, rate=30.0))
    mw_quiet(False); lure()
    yield from mw4_walk_on()
    seg("tier2"); yield from mw4_fights(3, DUR - 1.0)
def mw4_rogue(s0, centre, room, anvil):
    """the Rogue (tier 3): behind a card a tier-3 set (the dwarven halls); the crossbow, the daggers, her roll; she walks on
    north into the next set, generated as she comes"""
    yield from mw4_start(centre)
    mw4_tiers(3)
    yield from mw4_land((2, 0), "TIER 3:  THE DWARVEN HALLS", "the reel opens tiers 2 and 3 and sets her down in a set of rooms generated now")
    seg("tier3"); yield from mw4_fights(2, DUR * 0.6)
    yield from mw4_walk_on()
    yield from mw4_fights(3, DUR - 1.0)
def mw4_mage(s0, centre, room, anvil):
    """the Mage (tier 3): the reel gives her two tomes (Frost Shard, Chain Lightning) and a scroll of Meteor Storm (a spell
    beyond her mana: a scroll casts it at none); behind a card a tier-3 set; her spells, the scroll read at a group"""
    yield from mw4_start(centre)
    yield from give(["Tome of Frost Shard", "Tome of Chain Lightning"], "tomes")
    G["combat"].add_item("Scroll of Meteor Storm", 1); event("given", items={"Scroll of Meteor Storm": 1}, why="scroll", message=str(G["combat"].message))
    yield from pause(1.0)
    mw4_tiers(3)
    tgt = yield from mw4_land((-2, 0), "TIER 3:  THE MAGE'S SPELLS", "the reel opens tiers 2 and 3 and sets her down in a set of rooms generated now")
    seg("tier3")
    # (the scroll first: Meteor Storm at the monster she was set down facing (its strikes fall round it))
    gen, c = G["gen"], G["combat"]
    ms = [q for q in gen.get_monsters() if alive(q) and d2(q.get_actor_location(), loc()) < 2500.0]
    if alive(tgt):
        m = tgt
        G["heading"] = yaw_to(loc(), m.get_actor_location()); G["pawn"].set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), False)
        yield from pause(0.4)
        h = {q.get_name(): q.get_health() for q in ms}; m0 = c.get_mana()
        ok = c.read_scroll("Scroll of Meteor Storm"); key_hit("enter")
        event("scroll_read", scroll="Scroll of Meteor Storm", ok=bool(ok), message=str(c.message), mana_before=round(m0), monsters=len(ms))
        yield from pause(5.5, lambda: camera(side=-150.0, pitch=-20.0, rate=40.0))
        lost = sum(max(0.0, v - (q.get_health() if alive(q) else 0.0)) for q in ms for k_, v in h.items() if q.get_name() == k_)
        event("scroll_done", lost=round(lost), killed=sum(1 for q in ms if not alive(q)), mana_after=round(c.get_mana()))
    yield from mw4_fights(2, DUR * 0.55)
    yield from mw4_walk_on()
    yield from mw4_fights(3, DUR - 1.0)
def mw4_warlock(s0, centre, room, anvil):
    """the Warlock (tier 4): the reel gives her two tomes (Curse of Frailty, Shadow Lash); behind a card a tier-4 set; the
    curse and the lash, then her sword; she walks on into the next set"""
    yield from mw4_start(centre)
    yield from give(["Tome of Curse of Frailty", "Tome of Shadow Lash"], "tomes")
    mw4_tiers(2)
    yield from mw4_land((1, 1), "TIER 2:  CURSE, LASH AND SWORD", "the reel opens tier 2 and sets her down in a set of rooms generated now")
    seg("tier2"); yield from mw4_fights(2, DUR * 0.6)
    yield from mw4_walk_on()
    yield from mw4_fights(3, DUR - 1.0)
def mw4_martial(s0, centre, room, anvil):
    """the Martial Artist (tier 4): the reel teaches her the eight chi attacks four bosses would; behind a card a tier-4 set;
    a chi attack from the bar at each monster, then her fists; she walks on into the next set"""
    yield from mw4_start(centre)
    gen = G["gen"]; gen.unlock_hero_weapons(8)
    event("given", items={"chi attacks": 8}, why="the reel teaches her the eight chi attacks four tier bosses would", unlocked=[str(w.name) for w in gen.get_editor_property("weapons")])
    yield from pause(1.2)
    mw4_tiers(4)
    yield from mw4_land((0, 3), "TIER 4:  CHI", "the reel opens tiers 2 to 4 and sets her down in a set of rooms generated now")
    seg("tier4"); yield from mw4_fights(3, DUR * 0.6)
    yield from mw4_walk_on()
    yield from mw4_fights(4, DUR - 1.0)
def mw4_summoner(s0, centre, room, anvil):
    """the Summoner (tiers 1 and 5): in the great hall Summon Tier 1, two soldiers, and a lured fight beside them with fire;
    the reel gives her the four summonings four tier bosses would; behind a card a tier-5 set: the gunners, an orc, an alien
    warrior and a spider called (the reel fills her mana before each: each takes half her pool), and the fight"""
    yield from mw4_start(centre)
    gen = G["gen"]; G["summons"] = ["Summon Tier 1"]
    mw_quiet(False); lure(); seg("tier1")
    yield from mw4_cast_summons(["Summon Tier 1", "Summon Tier 1"])
    yield from mw4_fights(1, DUR * 0.3)
    gen.unlock_hero_weapons(4)
    event("given", items={"summonings": 4}, why="the reel gives her the four summonings four tier bosses would", unlocked=[str(w.name) for w in gen.get_editor_property("weapons")])
    yield from pause(1.4)
    mw4_tiers(5)
    yield from mw4_land((4, 0), "TIER 5:  HER SUMMONED", "the reel opens tiers 2 to 5 and sets her down in a set of rooms generated now")
    seg("tier5")
    yield from mw4_cast_summons(["Summon Tier 2", "Summon Tier 3", "Summon Tier 4", "Summon Tier 5"])
    G["summons"] = ["Summon Tier 5", "Summon Tier 4", "Summon Tier 3", "Summon Tier 2"]
    yield from mw4_fights(2, DUR * 0.72)
    yield from mw4_walk_on()
    yield from mw4_fights(4, DUR - 1.0)
def run5m4():
    """(mistward_castle, the user's list of 2026-10-30) the six heroes in combat at all five tiers"""
    yield from mw_start()
    gen, c = G["gen"], G["combat"]
    s0, centre, room, anvil = mw_hall()
    yield from {"Warrior": mw4_warrior, "Mage": mw4_mage, "Warlock": mw4_warlock, "Rogue": mw4_rogue, "MartialArtist": mw4_martial, "Summoner": mw4_summoner}[HERO](s0, centre, room, anvil)
    while True:
        m = mw4_threat()
        if m is None or not m.is_aggro(): yield from pause(0.5, lambda: camera(side=30.0, pitch=-12.0, rate=12.0)); continue
        yield from mw4_fight(m)

def run():
    gen, pc, p = G["gen"], G["pc"], G["pawn"]
    if W5M4:
        yield from run5m4(); return
    if W5M:
        yield from run5m(); return
    if W5M2:
        yield from run5m2(); return
    if W5X:
        yield from run5x(); return
    if W5W2:
        yield from run5w2(); return
    if W5G:
        yield from run5g(); return
    if W5S:
        yield from run5s(); return
    if W5C:
        yield from run5c(); return
    if W5H:
        yield from run5h(); return
    if W5R:
        yield from run5w(); return
    if L5:
        yield from run5(); return
    seg("start")
    while T() <= 0.0 or G["combat"] is None:
        camera(rate=1e6); yield
    # (RestartPlay puts the start section's monsters back over a few frames, the old ones still there for a frame or
    # two: the choice below waits half a second for them)
    def start_count(): return sum(1 for q in gen.get_monsters() if alive(q) and q.get_editor_property("section").get_editor_property("coord") == IP(0, 0))
    while T() < 0.5 or (start_count() < 10 and T() < 1.2):
        camera(rate=1e6); yield
    # ---- the way out (east, or the level 4 hero's way): from the middle of the start section to the hallway that leaves that edge
    sec0 = gen.get_section(IP(0, 0)); half = gen.get_editor_property("section_tiles") * gen.get_editor_property("tile_size") / 2.0
    trig = half - gen.get_editor_property("trigger_distance")
    ways = [list(sec0.find_path_world(gen.get_start_room_center(), q)) for q in sec0.get_portal_points() if along(q) > half - 400.0]
    way = min([x for x in ways if len(x) > 10], key=len); portal = way[-1]
    # a chest near that way, 5 to 26 m before the line, a short walk from it (the chests stay where they are; the
    # monsters wander): she is set down two tiles from it and opens it, then goes for the monster nearest to her then
    best = None; prey0 = None
    for ch in chests_of(IP(0, 0)):
        i = min(range(len(way)), key=lambda j: d2(way[j], ch))
        if not (trig - 2600.0 <= along(way[i]) <= trig - 500.0): continue
        pts = list(sec0.find_path_world(way[i], ch))
        if not 2 <= len(pts) <= 7: continue
        stand = stand_by_chest(ch, way[i])
        if stand is None: continue
        if best is None or len(pts) < best[0]: best = (len(pts), i, pts, ch, stand)
    event("pick", chest=None if best is None else [round(best[3].x), round(best[3].y)])
    if best is not None:
        _, k0, pts, chest0, stand0 = best; st = pts[max(0, len(pts) - 3)]
    else:
        k0 = next(i for i, q in enumerate(way) if along(q) >= trig - 2500.0); chest0 = None; stand0 = None; st = way[k0]
    route = Route(way[k0:] + [V(portal.x + 300.0 * k * DX, portal.y + 300.0 * k * DY, portal.z) for k in range(1, 6)])
    p.set_actor_location(V(st.x, st.y, 100.0), False, True); G["heading"] = yaw_to(st, chest0 if chest0 else way[min(k0 + 3, len(way) - 1)])
    p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), True)
    S["note"].update({"start": [round(st.x), round(st.y)], "trigger_x": round(trig), "portal": [round(portal.x), round(portal.y)], "chest": [round(chest0.x), round(chest0.y)] if chest0 else None})
    event("start", at=S["note"]["start"], to_the_line_m=round((trig - along(st)) / 100.0, 1), way=WAY)
    G["cam_yaw"] = G["heading"] - 22.0; G["cam_pitch"] = -24.0
    t_set = T()
    while T() < max(0.9, t_set + 0.3):
        camera(side=-22.0, pitch=-24.0, rate=1e6); yield
    if chest0 is not None:
        seg("chest"); yield from open_chest(chest0, stand0)
    # the start section's monster nearest to her now (by the way there), if it is not far
    mine = section_of(loc()); prey = None
    for q in gen.get_monsters():
        if not alive(q) or q.get_editor_property("section") != mine: continue
        pts = path(loc(), q.get_actor_location())
        if 1 < len(pts) <= 18 and (prey is None or len(pts) < prey[0]): prey = (len(pts), q)
    if prey is not None:
        event("hunt", monster=str(prey[1].monster_name), way_m=prey[0] * 3)
        seg("fight"); G["casts0"] = G["combat"].attacks_made; yield from (fight3 if L3 else fight)(prey[1])
    seg("walk"); stuck = 0.0; last = loc(); new_route = False; east = route.p[route.i:]; hunted = False; chest1_done = False
    def onward():
        back = path(loc(), portal)
        return Route(back + east[-5:]) if len(back) > 1 else Route(east)
    route = onward()
    while True:
        # (level 4: the inventory once, after her first fight with two things found, or later with one)
        if L4 and not G.get("inv_done") and T() < DUR - 6.0:
            n_items = sum(1 for x in G["combat"].get_inventory_lines() if x.startswith("item|"))
            if n_items >= 1 and ((G["fights"] >= 1 and n_items >= 2) or T() > 24.0):
                G["inv_done"] = True; seg("inventory"); yield from inventory_beat(); seg("walk"); stuck = 0.0; last = loc()
        m = threat()
        if m is None and T() - G.get("last_fight", -99.0) > 10.0 and T() < DUR - 8.0 and T() - G.get("hunt_t", -9.0) > 2.0:
            # no fight for a while: the nearest monster within 14 tiles of way (it is then fought from range)
            G["hunt_t"] = T(); best = None
            for q in gen.get_monsters():
                if not alive(q) or d2(q.get_actor_location(), loc()) > 4500.0: continue
                pts = path(loc(), q.get_actor_location())
                if 1 < len(pts) <= 14 and (best is None or len(pts) < best[0]): best = (len(pts), q)
            if best is not None: event("hunt", monster=str(best[1].monster_name), way_m=best[0] * 3); m = best[1]
        # (level 4: the big map (M) once, for 4 s, while she walks on: after her first fight and the inventory; a fight closes it)
        if L4 and G.get("map_until") is not None and (T() >= G["map_until"] or m is not None):
            G["map_until"] = None; gen.set_map_open(False); key_hit("m"); event("map", open=0)
        if (L4 and not G.get("map_done") and m is None and T() < DUR - 5.0 and T() - G.get("last_fight", -99.0) > 1.5
                and (G.get("inv_done") or T() > 22.0) and (G["fights"] >= 1 or T() > 26.0)):
            G["map_done"] = True; G["map_until"] = T() + 4.0; gen.set_map_open(True); key_hit("m"); event("map", open=1)
        if m is not None:
            seg("fight"); G["casts0"] = G["combat"].attacks_made; yield from (fight3 if L3 else fight)(m); seg("walk"); stuck = 0.0; last = loc()
            here = gen.world_to_section(loc())
            if in_start(here) and CHESTS and not G.get("chest_on_way") and T() < DUR - 16.0:
                # (level 3 and 4: a container on the way out after the first fight: the reel opens more than one)
                l = loc(); chs = []
                for q in chests_of(here):
                    if d2(q, l) > 1500.0 or along(q) < along(l) - 200.0: continue             # (close by, and on the way out)
                    st = stand_by_chest(q, l)
                    if st is not None and len(path(l, st)) <= 5: chs.append((len(path(l, st)), q, st))
                if chs: G["chest_on_way"] = True; _, q, st = min(chs, key=lambda x: x[0]); seg("chest"); yield from open_chest(q, st); seg("walk")
            if in_start(here): route = onward()
            elif not chest1_done and T() < DUR - 5.0:
                # in the new section, after the fight: a chest near her, if there is one
                l = loc(); chs = []
                for q in chests_of(here):
                    if d2(q, l) > 2500.0: continue
                    st = stand_by_chest(q, l)
                    if st is not None and len(path(l, st)) <= 8: chs.append((len(path(l, st)), q, st))
                if chs: chest1_done = True; _, q, st = min(chs, key=lambda x: x[0]); seg("chest"); yield from open_chest(q, st); seg("walk")
            continue
        here = gen.world_to_section(loc())
        if False:
            # the start section: the nearest monster near her (a match for her spell from range)
            hunted = True; mine = section_of(loc()); best = None
            for q in gen.get_monsters():
                if not alive(q) or q.get_editor_property("section") != mine: continue
                pts = path(loc(), q.get_actor_location())
                if 1 < len(pts) <= 26 and (best is None or len(pts) < len(best[1])): best = (q, pts)
            if best is not None: event("hunt", monster=str(best[0].monster_name), way_m=len(best[1]) * 3); route = Route(best[1])
        if here.x == NEXT.x and here.y == NEXT.y and not new_route and gen.get_section(NEXT) is not None and not gen.get_section(NEXT).is_building():
            if CHESTS and not chest1_done:
                # (level 3: a container in the new section first, if one is a few steps away)
                chest1_done = True; l = loc(); chs = []
                for q in chests_of(here):
                    if d2(q, l) > 1500.0: continue
                    st = stand_by_chest(q, l)
                    if st is not None and len(path(l, st)) <= 5: chs.append((len(path(l, st)), q, st))
                if chs: _, q, st = min(chs, key=lambda x: x[0]); seg("chest"); yield from open_chest(q, st); seg("walk"); continue
            new_route = True; l = loc(); sec1 = gen.get_section(NEXT)
            ms = [q for q in gen.get_monsters() if alive(q) and q.get_editor_property("section") == sec1]
            if ms:
                q = min(ms, key=lambda a: d2(a.get_actor_location(), l)); pts = list(sec1.find_path_world(l, q.get_actor_location()))
                if 1 < len(pts) <= 25: route = Route(pts); event("into_new_section", toward=str(q.monster_name), way_m=round(len(pts) * 3))
        if route.done() and in_start(here): route = onward()
        if CHESTS and not G.get("chest_on_way") and G["fights"] > 0 and T() < DUR - 16.0 and T() - G.get("chest_look", -9.0) > 0.5:
            # (level 3: on the way east, a container she passes within 11 m: she turns aside and opens it)
            G["chest_look"] = T(); l = loc(); chs = []
            for q in chests_of(here):
                if d2(q, l) > 1100.0: continue
                st = stand_by_chest(q, l)
                if st is not None and len(path(l, st)) <= 6: chs.append((len(path(l, st)), q, st))
            if chs:
                G["chest_on_way"] = True; _, q, st = min(chs, key=lambda x: x[0]); seg("chest"); yield from open_chest(q, st); seg("walk")
                route = onward() if in_start(gen.world_to_section(loc())) else route; continue
        move(route.target(), run=True); doors(); camera()
        stuck = stuck + G["el"] if d2(loc(), last) < 60.0 * G["el"] else 0.0; last = loc()
        if stuck > 1.2:
            stuck = 0.0; pts = path(loc(), route.p[-1])
            if len(pts) > 1: route = Route(pts); event("repath")
        yield

# ---------------------------------------------------------------- the recorder
def r3(v): return [round(v.x, 1), round(v.y, 1), round(v.z, 1)]
def snap_maps():
    md = G["gen"].get_editor_property("map_data")
    for c, m in md.items():
        key = "%d,%d" % (c.x, c.y); sig = (len(m.rects), len(m.chests), len(m.torches))
        if S["mapsig"].get(key) != sig:
            S["mapsig"][key] = sig
            S["maps"].append({"t": round(max(T(), 0.0), 3), "coord": [c.x, c.y], "rects": [[r.min.x, r.min.y, r.max.x, r.max.y, r.kind.name, int(r.corridor)] + ([list(r.mask), str(r.shape)] if MW and len(r.mask) else []) for r in m.rects],
                              "doors": [[round(d.x), round(d.y)] for d in m.doors], "chests": [[round(d.x), round(d.y)] for d in m.chests], "torches": [[round(d.x), round(d.y)] for d in m.torches]})
        disc = [i for i, r in enumerate(m.rects) if r.discovered]
        if S["disc"].get(key) != disc:
            S["disc"][key] = disc; S["events"].append({"t": round(max(T(), 0.0), 3), "frame": G["frame"], "kind": "discovered", "coord": [c.x, c.y], "rects": disc})
def tier(m):
    """a monster's section's average hit points (the tactical map marks those above 1.25 x it)"""
    k = m.get_editor_property("section").get_editor_property("coord"); key = (k.x, k.y)
    if key not in S["tier"]: S["tier"][key] = G["gen"].get_monster_health(k)
    return S["tier"][key]
def pois(l, rad=5200.0):
    """what the tactical minimap marks near her (ARDHUD::GatherPois): chests and trunks not looted yet [x, y, 2], and the
    hallway exits whose next section has nothing discovered [x, y, 3] (the overlay keeps the chests in rooms she has seen)"""
    gen = G["gen"]; out = []; md = gen.get_editor_property("map_data")
    for k in gen.get_section_coords():
        sec = gen.get_section(k); key = (k.x, k.y)
        if sec is None or sec.is_building(): continue
        if key not in S["poi_static"]:
            ch = [(i, sec.get_container_location(i)) for i in range(sec.get_num_containers()) if sec.get_container_kind(i) in ("chest", "trunk")]
            half = gen.get_editor_property("section_tiles") * 0.5; ts = gen.get_editor_property("tile_size")
            mid = ((k.x * gen.get_editor_property("section_tiles")) * ts, (k.y * gen.get_editor_property("section_tiles")) * ts)
            ex = []
            for q in sec.get_portal_points():
                dx, dy = q.x - mid[0], q.y - mid[1]
                nxt = (k.x + (1 if dx > 0 else -1), k.y) if abs(dx) > abs(dy) else (k.x, k.y + (1 if dy > 0 else -1))
                ex.append((q, nxt))
            S["poi_static"][key] = (ch, ex)
        ch, ex = S["poi_static"][key]
        for i, q in ch:
            if d2(q, l) < rad and not sec.is_container_looted(i): out.append([round(q.x), round(q.y), 2])
        if W5K:
            for q in sec.get_anvil_points():
                if d2(q, l) < rad: out.append([round(q.x), round(q.y), 6])
        for q, nxt in ex:
            if d2(q, l) > rad: continue
            # (level 5's tiers: a hallway into a tier not open yet, or out of the last one, is sealed: a red cross)
            if W5R and gen.get_seal_kind(k, IP(*nxt)) > 0: out.append([round(q.x), round(q.y), 5]); continue
            m = md.get(IP(*nxt))
            if m is None or not any(r.discovered for r in m.rects): out.append([round(q.x), round(q.y), 3])
    if MW: out += mw_marks(l, rad)
    return out
def mw_marks(l, rad):
    """(mistward) ARDHUD::GatherPois's marks: 7 a boss (alive), 8 a guarded ring (until she has it or its container is
    opened), 9 her things, 10 a teleporter, 11 a trap she has seen"""
    gen = G["gen"]; c = G["combat"]; out = []
    for e in gen.get_encounter_lines():
        q = str(e).split("|"); x, y = float(q[1]), float(q[2])
        if math.hypot(x - l.x, y - l.y) > rad: continue
        if q[0] == "boss" and q[5] == "1": out.append([round(x), round(y), 7])
        elif q[0] == "ring" and len(q) >= 9 and c.get_item_count(q[4]) == 0 and (int(q[5]) < 0 or not gen.is_container_looted(IP(int(q[7]), int(q[8])), int(q[5]))): out.append([round(x), round(y), 8])
    for pl in gen.loot_piles:
        if pl and pl.hers and d2(pl.get_actor_location(), l) < rad: out.append([round(pl.get_actor_location().x), round(pl.get_actor_location().y), 9])
    for k, v in gen.pads.items():
        if d2(v, l) < rad: out.append([round(v.x), round(v.y), 10])
    for e in gen.get_trap_lines():
        q = str(e).split("|")
        if q[9] == "1" and q[8] == "0" and math.hypot(float(q[5]) - l.x, float(q[6]) - l.y) < rad: out.append([round(float(q[5])), round(float(q[6])), 11])
    return out
def sample():
    gen, pc, p, c = G["gen"], G["pc"], G["pawn"], G["combat"]; cm = pc.player_camera_manager; l = p.get_actor_location(); cr = cm.get_camera_rotation()
    mons = []
    for m in gen.get_monsters():
        try:
            ml = m.get_actor_location()
            if d2(ml, l) > 3200.0: continue
            mons.append([m.get_name(), str(m.monster_name), round(ml.x), round(ml.y), round(ml.z), round(m.get_health(), 1), m.get_max_health(), int(m.is_aggro()), int(m.is_dead()),
                         round(m.capsule_component.get_scaled_capsule_half_height()), int(m.is_attacking()), m.get_num_wounds(), int(m.get_max_health() > 1.25 * tier(m))]
                        # (run5s: the gallery's name, and the marks after it: cursed, slowed, burning)
                        + ([str(m.title), int(m.get_curse_share() > 0.0), int(m.get_slow_share() > 0.0), int(m.is_burning())] if W5S else []))
        except Exception: pass
    allies = []
    if W5S:
        for m in gen.get_allies():
            try:
                ml = m.get_actor_location()
                if d2(ml, l) > 3200.0: continue
                allies.append([str(m.title) or str(m.monster_name), round(ml.x), round(ml.y), round(ml.z), round(m.get_health(), 1), m.get_max_health(), round(m.capsule_component.get_scaled_capsule_half_height()),
                               round(m.get_ally_time_left(), 1)])
            except Exception: pass
    # the keys that do what she does now: W (and Shift while she runs), E as she casts, F as she opens
    sp = p.get_velocity().length(); keys = G.get("key_hit", "") if T() - G.get("keys_t", -9.0) < 0.5 else ""
    moving = "run" if sp > 0.5 * (WALK + RUN) else ("walk" if sp > 40.0 else "")
    return {"t": round(T(), 4), "p": r3(l), "yaw": round(p.get_actor_rotation().yaw, 1), "sp": round(p.get_velocity().length()), "hp": round(c.get_health(), 1), "mhp": c.get_max_health(), "w": c.get_weapon_index(),
            "kills": c.kills, "atk": round(c.get_attack_time(), 3), "charging": int(c.is_charging()), "bolts": [r3(b) for b in c.get_bolts()], "dead": int(c.is_dead()),
            "cp": r3(cm.get_camera_location()), "cr": [round(cr.pitch, 3), round(cr.yaw, 3), round(cr.roll, 3)], "fov": round(cm.get_fov_angle(), 2), "seg": S["seg"],
            "sections": len(gen.get_section_coords()), "mon": mons, "keys": keys, "moving": moving, "fire": round(min([d2(q, l) for q in gen.get_fire_loops()] or [-1.0])),
            "rolling": int(c.is_rolling()), "pois": pois(l) if gen.get_editor_property("tactical_maps") and G["frame"] % 3 == 0 else None,
            **({"mana": round(c.get_mana(), 1), "mmana": c.get_max_mana(), "inv": [int(c.is_inventory_open()), c.get_inventory_cursor()], "spb": round(c.get_speed_bonus(), 3),
                "rg": round(c.get_regen_per_second(), 2), "mapo": int(gen.get_editor_property("map_open"))} if L4 else {}),
            **({"arm": str(c.get_worn_armour()), "armv": round(c.get_armour(), 3)} if L5 else {}),
            **({"armw": [c.get_armour_wear(c.get_worn_armour()), c.get_armour_durability(c.get_worn_armour())], "slow": round(c.get_armour_slow(), 3),
                "craft": [int(c.is_crafting_open()), c.get_craft_cursor()], "rep": [int(c.is_picking_repair()), c.get_repair_cursor(), str(c.get_repair_item())],
                "tierhere": gen.tier_of(gen.world_to_section(l))} if W5K else {}),
            **({"cd": [round(c.get_cooldown_left(i), 2) for i in range(len(gen.get_editor_property("weapons")))], "buffs": [str(x) for x in c.get_buff_lines()],
                "menu": [int(gen.is_menu_open()), gen.get_menu_cursor(), [round(gen.get_user_volume(i), 2) for i in range(4)]], "ally": allies, "atki": c.get_attack_index()} if W5S else {}),
            **(tier_row(l) if W5R else {}),
            **({"fps": round(gen.get_fps(), 1), "sh": str(c.get_worn_shield()) if str(c.get_worn_shield()) != "None" else "", "shin": int(c.is_shield_in_hand()),
                "torch": int(c.is_torch_held()), "dis": round(gen.get_disarm_progress(), 2), "near": str(gen.describe_nearest(l, 260.0)), "held": int(c.is_held()),
                "msg": str(c.message), "mapo": int(gen.get_editor_property("map_open"))} if MW else {}),
            **({"tab": c.get_inventory_tab(), "tabn": tab_counts(c) if c.is_inventory_open() else None, "qs": [str(x) for x in c.get_quick_slots()], "asl": c.get_assign_slot(), "qf": c.get_quick_first(), "qc": c.get_quick_cursor(), "ra": str(c.get_ready_ability()),
                "blk": int(c.is_blocking()), "buffs": [str(x) for x in c.get_buff_lines()], "slp": [int(c.is_picking_slash()), c.get_slash_cursor(), str(c.get_slash_item())],
                "helm": int(c.is_helmet_hidden()), "aw": gen.get_arena_wave(), "al": gen.get_arena_left()} if W5M2 else {})}
def tab_counts(c):
    """(run5m2) the inventory's lines per tab, as its tab strip counts them"""
    n = [0, 0, 0, 0, 0]
    for l in c.get_all_inventory_lines():
        k = str(l).split("|")[0]
        n[0 if k in ("weapon", "carried", "ability") else 1 if k in ("armour", "shield", "torch", "helmet") else 2 if k == "item" else 3 if k in ("component", "repair") else 4] += 1
    return n
def tier_row(l):
    """(the weapons and tiers reel) what the HUD's tier panel shows (ARDHUD::DrawTiers) and a seal's prompt near her"""
    gen = G["gen"]; s = gen.world_to_section(l); t_ = gen.tier_of(s)
    r_ = gen.get_section_progress(s); ok, pr = r_ if isinstance(r_, tuple) else (r_ is not None, r_)          # (None: a set with no record yet (mw4's jump, held over it while it is built))
    ok = bool(ok) and pr is not None
    near = str(gen.describe_nearest(l, 260.0))
    out = {"tier": [t_, gen.get_tier_cleared(t_), gen.tier_size(t_), pr.rooms_explored if ok else -1, pr.rooms if ok else -1, pr.chests_looted if ok else -1, len(pr.chests) if ok else -1,
                    len(pr.killed) if ok else -1, pr.monsters if ok else -1, int(pr.cleared) if ok else 0, gen.get_open_tiers(), gen.max_tier],
           "seal": "" if near else str(gen.describe_seal_near(l, 450.0))}
    # (mistward: the share rule's line, as ARDHUD::DrawTiers writes it: the open tier's counts against what it needs)
    share = gen.get_editor_property("tier_open_share")
    if share < 1.0 and gen.get_open_tiers() < gen.max_tier:
        r2 = gen.get_tier_tally(gen.get_open_tiers())
        if r2 is not None:
            ok2, d2_, a2_ = r2 if isinstance(r2, tuple) and len(r2) == 3 else (True,) + tuple(r2)
            out["tally"] = [round(share, 3), [d2_.x, d2_.y, d2_.z], [a2_.x, a2_.y, a2_.z]] if ok2 else [round(share, 3)]
        else: out["tally"] = [round(share, 3)]
    return out
def hits():
    c = G["combat"]; p = G["pawn"]; now = {}
    for m in G["gen"].get_monsters():
        try: now[m.get_name()] = (m.get_health(), m.get_actor_location(), m.capsule_component.get_scaled_capsule_half_height())
        except Exception: pass
    for k, (h, ml, hh) in now.items():
        old = S["hp"].get(k)
        if old is not None and h < old - 0.01: S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "hit", "amount": round(old - h), "at": [round(ml.x), round(ml.y), round(ml.z + hh)], "on_player": 0})
        S["hp"][k] = h
    h = c.get_health(); old = S["hp"].get("__her")
    if old is not None and h < old - 0.01:
        l = p.get_actor_location(); S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "hit", "amount": round(old - h), "at": [round(l.x), round(l.y), round(l.z + 90)], "on_player": 1})
    S["hp"]["__her"] = h
    if c.attacks_made > S["casts"]:
        S["casts"] = c.attacks_made; tg = c.get_last_target()
        wi = c.get_attack_index(); wdx = G["gen"].get_editor_property("weapons")[wi] if wi >= 0 else None; wn = str(wdx.name) if wdx else ""
        S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "cast" if (wdx is not None and wdx.spell) else "cut", "weapon": wn, "target": tg.get_name() if tg else None,
                            "m": round(d2(p.get_actor_location(), tg.get_actor_location()) / 100.0, 1) if tg else None})       # (how far she cast from)
    if c.rolls > S["rolls"]: S["rolls"] = c.rolls; S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "rolled", "back": int(c.is_rolling_back())})
    if c.dodged_hits > S["dodged"]: S["dodged"] = c.dodged_hits; S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "dodged"})
    if c.bolts_cast > S["bolts"]: S["bolts"] = c.bolts_cast; S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "bolt", "from": r3(c.last_bolt_from)})
    if L4:
        # (level 4: what a container gave, what the inventory shows and says, a cast refused for want of mana)
        g = G["gen"]
        if g.items_found > S.get("found", 0):
            S["found"] = g.items_found; S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "found", "item": str(g.last_found), "items": [str(x) for x in g.last_found_list]})
        if L5:
            # (level 5: the set she has on, and each blow on her before and after her armour)
            wa = str(c.get_worn_armour())
            if wa != S.get("worn", "None"):
                S["worn"] = wa; S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "worn", "set": None if wa == "None" else wa, "armour": round(c.get_armour(), 3),
                                                    "meshes": [m_.skeletal_mesh_asset.get_name() for m_ in c.get_armour_meshes() if m_.skeletal_mesh_asset]})
            if c.hits_taken > S.get("taken", 0):
                S["taken"] = c.hits_taken; S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "blow_on_her", "before": round(c.last_blow_before, 2), "reached": round(c.last_blow_taken, 2),
                                                               "armour": round(c.get_armour(), 3), "set": None if wa == "None" else wa})
        lines = list(c.get_inventory_lines())
        if lines != S.get("lines"): S["lines"] = lines; S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "lines", "lines": lines})
        if W5S:
            # (run5s: each spell as it is released, what the spells did on her side, the menu's lines)
            rel = {str(k): v for k, v in c.spells_released.items()}
            for k, v in rel.items():
                if v > S.setdefault("rel", {}).get(k, 0): S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "spell", "name": k, "n": v})
            S["rel"] = rel
            sig = (c.ward_blocks, c.reflected, c.evaded, len(g.get_allies()), c.spells_learned)
            if sig != S.get("ssig"):
                S["ssig"] = sig; S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "spell_state", "ward_blocks": sig[0], "reflected": sig[1], "evaded": sig[2], "allies": sig[3], "learned": sig[4]})
            ml_ = [str(x) for x in g.get_menu_lines()] if g.is_menu_open() else []
            if ml_ != S.get("menul"): S["menul"] = ml_; S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "menu_lines", "lines": ml_})
        if W5K:
            # (the crafting panel's and the repair list's lines as they change)
            cl = [str(x) for x in c.get_craft_lines()] if c.is_crafting_open() else []
            if cl != S.get("craftl"): S["craftl"] = cl; S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "craft_lines", "lines": cl})
            rl = [str(x) for x in c.get_repair_lines()] if c.is_picking_repair() else []
            if rl != S.get("repl"): S["repl"] = rl; S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "repair_lines", "lines": rl})
            if W5M2:
                sl = [str(x) for x in c.get_slash_lines()] if c.is_picking_slash() else []
                if sl != S.get("slashl"): S["slashl"] = sl; S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "slash_lines", "lines": sl})
                sg = [str(x) for x in g.slashes_given]
                if sg != S.get("sgiven", []): S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "slash_found", "slashes": sg[len(S.get("sgiven", [])):]}); S["sgiven"] = sg
                pr = {str(k): v for k, v in c.slash_procs.items()}
                for k, v in pr.items():
                    if v > S.setdefault("procs", {}).get(k, 0): S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "slash_proc", "effect": k, "n": v})
                S["procs"] = pr
        if W5R:
            # (the weapons reel: her weapons as they are now (found ones join, broken ones go, wear goes down), the tiers' notices)
            ws_ = g.get_editor_property("weapons")
            wl = [{"name": str(d.name), "damage": round(c.get_damage_of(i), 2), "base_damage": d.damage, "reach": d.reach, "spell": bool(d.spell), "alongside": bool(d.alongside),
                   "mana": d.mana_cost, "ranged": bool(d.spell and d.bolt_mesh), "wear": c.get_weapon_wear(i), "durability": d.durability, "speed": d.speed_rating,
                   "rating": d.damage_rating, "type": str(d.weapon_type), "rate": round(d.play_rate, 3), **({"slash": str(d.slash) if str(d.slash) != "None" else ""} if W5M2 else {}),
                   **({"spell_index": d.spell_index, "cooldown": d.cooldown, "icon": str(d.icon)} if W5S else {})} for i, d in enumerate(ws_)]
            sig = [(w_["name"], w_["wear"], w_["damage"], w_.get("slash", "")) for w_ in wl]          # (a ring changes the damage too; run5m2: a slash put on)
            if sig != S.get("wsig"): S["wsig"] = sig; S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "weapons", "list": wl})
            tn = str(g.tier_notice)
            if tn != S.get("tnotice", ""): S["tnotice"] = tn; S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "tier_notice", "text": tn})
        if str(c.message) != S.get("msg", ""): S["msg"] = str(c.message); S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "message", "text": S["msg"]})
        if MW:
            # (mistward: the traps, teleports, cells, the shield's blows, deaths and the piles, as they happen)
            mw = (g.traps_triggered, g.traps_disarmed, g.trap_hits, g.teleports, g.prisoners_freed, g.cell_breakouts, c.shield_blocks, c.deaths, len([x for x in g.loot_piles if x]), str(c.get_worn_shield()), int(c.is_torch_held()))
            old = S.get("mwsig")
            if old is not None and mw != old:
                names = ["trap", "disarmed", "trap_hit", "teleport", "freed", "breakout", "shield_block", "died", "piles", "shield", "torch"]
                for k_, a_, b_ in zip(names, old, mw):
                    if a_ == b_: continue
                    ev = {"t": round(T(), 3), "frame": G["frame"], "kind": "mw_" + k_, "now": b_, "was": a_}
                    if k_ == "trap": ev["label"] = str(g.last_trap)
                    if k_ == "shield_block": ev.update({"took": round(c.last_shield_took, 2), "before": round(c.last_blow_before, 2), "reached": round(c.last_blow_taken, 2), "shield": str(c.get_worn_shield())})
                    if k_ == "piles": ev["things"] = [[str(x) for x in pl.things] for pl in g.loot_piles if pl]; ev["pictures"] = [pl.pictures for pl in g.loot_piles if pl]
                    S["events"].append(ev)
            S["mwsig"] = mw
        if c.casts_refused > S.get("refused", 0): S["refused"] = c.casts_refused; S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "no_mana"})
    n = c.bolts_on_monsters + c.bolts_elsewhere
    if n > S.get("bursts_n", 0): S["bursts_n"] = n; S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "burst", "at": r3(c.last_burst_at), "flown_m": round(c.last_bolt_flown / 100.0, 1)})
def heard():
    gen = G["gen"]; now = {str(k): v for k, v in gen.get_sound_counts().items()}
    for k, v in now.items():
        if v > S["snd"].get(k, 0): S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "sound", "key": k, "n": v - S["snd"].get(k, 0)})
    S["snd"] = now
    mu = (int(gen.is_combat_music()), str(gen.get_music_track()), str(gen.get_atmosphere_track()))
    if mu != S["music"] and mu[1]:
        S["music"] = mu; S["events"].append({"t": round(max(T(), 0.0), 3), "frame": G["frame"], "kind": "music", "battle": mu[0], "track": mu[1], "atmosphere": mu[2]})
    b = gen.get_blood()
    if b is not None and b.bursts != S["bursts"]:
        if b.bursts > S["bursts"]:
            at = b.last_burst_at; S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "blood", "at": [round(at.x), round(at.y), round(at.z)], "from_her_cm": round(d2(at, loc())), "bursts": b.bursts})
        S["bursts"] = b.bursts
def save(why=None):
    if S["saved"]: return
    S["saved"] = True
    rows = [dict(S["rows"][k][len(S["rows"][k]) // 2], frame=k) for k in sorted(S["rows"])]
    out = {"fps": FPS, "mode": MODE, "seed": SEED, "rows": rows, "events": S["events"], "segs": S["segs"], "maps": S["maps"], "note": S["note"], "const": G.get("const", {}), "error": why}
    os.makedirs(os.path.dirname(OUT), exist_ok=True); json.dump(out, open(OUT, "w"), separators=(",", ":"))
    ev = lambda k: [e for e in S["events"] if e["kind"] == k]
    last = rows[-1] if rows else {}
    msg = "%d frames | %d casts, %d cuts, %d bolts, %d bursts | %d rolls, %d blows dodged | %d kills (%s) | chests %d | doors %d | sections %d (%s) | she was hit %d times, %s hit points left | blood bursts %d" % (
        len(rows), len(ev("cast")), len(ev("cut")), len(ev("bolt")), len(ev("burst")), len(ev("rolled")), len(ev("dodged")), len(ev("kill")), ", ".join("%s in %d casts" % (e["monster"], e["casts"]) for e in ev("kill")), len(ev("chest")), len(ev("door")),
        last.get("sections", 0), " ".join("%s@%.1f" % (e["kind"], e["t"]) for e in S["events"] if e["kind"] in ("generated", "into_new_section", "chest", "fight", "kill")),
        sum(1 for e in ev("hit") if e["on_player"]), last.get("hp"), len(ev("blood")))
    (unreal.log_error if why else unreal.log)(("RDMREEL failed: %s | " % why if why else "RDMREEL saved ") + msg)
def stop(why=None):
    unreal.unregister_slate_post_tick_callback(unreal._rdm_reel); unreal._rdm_reel = None
    # (level 4: the menu first again, for Play in the editor)
    if L4: unreal.SystemLibrary.execute_console_command(None, "rd.HeroMenu 1")
    try: save(why)
    finally:
        try:
            if G.get("combat") is not None and ues.get_game_world() is not None:
                G["combat"].set_scripted_only(False); G["pc"].set_ignore_look_input(False)
                if L4: G["combat"].set_inventory_open(False)          # (left open, it keeps her from attacking in the next run)
                if L5: G["combat"].set_crafting_open(False)
                if W5S:
                    # (the menu shut, pausing the game again as in play; the volumes as they were: the menu saves them)
                    G["gen"].set_menu_open(False); G["gen"].set_editor_property("menu_pauses_game", True)
                    for i, v in enumerate(G.get("vol0", [])): G["gen"].set_user_volume(i, v)
                if "aggro0" in G: G["gen"].set_editor_property("aggro_distance", G["aggro0"][0]); G["gen"].set_editor_property("lose_distance", G["aggro0"][1])
                if W5G or W5W2:
                    # (the game's own speed and camera again)
                    G["pawn"].set_editor_property("custom_time_dilation", 1.0)
                    boom = next(iter(G["pawn"].get_components_by_class(unreal.SpringArmComponent)), None); cam = next(iter(G["pawn"].get_components_by_class(unreal.CameraComponent)), None)
                    if boom and "boom0" in G: boom.target_arm_length, boom.do_collision_test, boom.socket_offset, boom.target_offset = G["boom0"]
                    if cam and "fov0" in G: cam.field_of_view = G["fov0"]
        except Exception: pass
        G.clear()
def body():
    w = ues.get_game_world()
    if "gen" not in G:
        if w is None: return
        gens = GS.get_all_actors_of_class(w, unreal.RDDungeonGenerator); pc = GS.get_player_controller(w, 0); pawn = pc.get_controlled_pawn() if pc else None
        if not gens or pawn is None: return
        if L4 and str(gens[0].current_hero) != HERO:
            # (level 4: her hero in place of the level's default one, while the render warms up)
            if gens[0].get_player_combat() is not None and not S.get("switched"): S["switched"] = bool(gens[0].switch_hero(HERO)); unreal.log("RDMREEL hero %s: %s" % (HERO, S["switched"]))
            return
        if L4 and gens[0].get_player_combat() is None: return
        player = None
        if MODE == "render":
            lsa = GS.get_all_actors_of_class(w, unreal.LevelSequenceActor)
            if not lsa or lsa[0].get_editor_property("sequence_player") is None: return
            player = lsa[0].get_editor_property("sequence_player")
        G.update({"w": w, "gen": gens[0], "pc": pc, "pawn": pawn, "combat": None, "player": player, "t": -1.0, "frame": -1, "el": 1.0 / 60.0, "going": False, "wt": GS.get_time_seconds(w),
                  "w0": GS.get_time_seconds(w) + 1.5, "fights": 0, "sec_n": 1})
        pc.set_ignore_look_input(True)
        G["run"] = run()
        unreal.log("RDMREEL armed (%s), %.0f s" % (MODE, DUR))
    if w is None: stop(None if G["t"] >= DUR - 0.05 else "the world ended at %.2f s" % G["t"]); return
    if S["saved"]: return
    gen = G["gen"]; wt = GS.get_time_seconds(G["w"]); G["el"] = max(wt - G["wt"], 1e-4); G["wt"] = wt
    if G["combat"] is None:
        G["combat"] = gen.get_player_combat()
        if G["combat"] is not None:
            G["combat"].set_scripted_only(True)
            if L4: G["combat"].set_editor_property("inventory_pauses_game", False)
            wd = next((d for d in gen.get_editor_property("weapons") if d.spell), None) or gen.get_editor_property("weapons")[0]
            G["const"] = {"level": 5 if MW else int(LV), "mistward": MW, "game_title": str(gen.get_editor_property("dungeon_title")), "tactical": bool(gen.get_editor_property("tactical_maps")), "roll_distance": gen.get_editor_property("roll_distance"),
                          "stylized_minimap_m": 84.0, "weapons": [{"name": str(d.name), "damage": d.damage, "reach": d.reach, "spell": bool(d.spell)} for d in gen.get_editor_property("weapons")], "tile": gen.get_editor_property("tile_size"),
                          "section_tiles": gen.get_editor_property("section_tiles"), "max_health": G["combat"].get_max_health(), "average_blow": gen.get_average_weapon_damage(),
                          "start_tier": [gen.get_monster_health(IP(0, 0)), gen.get_monster_damage(IP(0, 0))], "runtime_tier": [gen.get_monster_health(IP(1, 0)), gen.get_monster_damage(IP(1, 0))],
                          "spell": {"name": str(wd.name), "damage": wd.damage, "reach": wd.reach, "speed": wd.bolt_speed, "splash": wd.bolt_splash}, "walk": WALK, "run": RUN,
                          "title": gen.get_editor_property("player_title"), "hint": gen.get_editor_property("controls_hint")}
            if L4:
                c_ = G["combat"]; ws_ = gen.get_editor_property("weapons")
                G["const"].update({"hero": HERO, "way": WAY, "seed": SEED, "max_mana": c_.get_max_mana(), "mana_per_second": gen.get_editor_property("mana_per_second"),
                                   "weapons": [{"name": str(d.name), "damage": round(c_.get_damage_of(i), 2), "base_damage": d.damage, "reach": d.reach, "spell": bool(d.spell),
                                                "alongside": bool(d.alongside), "mana": d.mana_cost, "ranged": bool(d.spell and d.bolt_mesh)} for i, d in enumerate(ws_)],
                                   "melee_bonus": gen.get_editor_property("melee_bonus"), "ranged_bonus": gen.get_editor_property("ranged_bonus"),
                                   "items": [{"name": str(it.name), "kind": str(it.kind.name).lower(), "amount": it.amount, "seconds": it.seconds, "looks": str(it.looks),
                                              **({"fits": [str(x.hero) for x in it.fits if len(x.meshes)], "wielded_by": [str(x.hero) for x in it.weapon_fits],
                                                    "weight": str(it.armour_weight.name).lower(), "durability": it.durability, "slower": it.slower, "dr": it.damage_rating,
                                                    "sr": it.speed_rating, "type": str(it.armour_type)} if L5 else {}),
                                              **({"ring_kind": str(it.ring_kind.name).lower(), "spell": str(it.spell)} if W5S else {})} for it in gen.get_editor_property("items")],
                                   # (run5s: the spell table, for the inventory's and the captions' lines)
                                   "spells": [{"name": str(s_.name), "type": str(s_.get_editor_property("type").name).lower(), "kind": str(s_.get_editor_property("kind").name).lower(), "effect": str(s_.effect), "mana": s_.mana,
                                               "cooldown": s_.cooldown, "duration": s_.duration, "damage": s_.damage, "tier": s_.tier} for s_ in gen.get_editor_property("spells")] if W5S else [],
                                   "learns": [str(x.name).lower() for h_ in gen.get_editor_property("heroes") if str(h_.name) == str(gen.get_editor_property("current_hero")) for x in h_.learns] if W5S else [],
                                   "ring_kinds": [str(x.name).lower() for h_ in gen.get_editor_property("heroes") if str(h_.name) == str(gen.get_editor_property("current_hero")) for x in h_.ring_kinds] if W5S else [],
                                   "recipes": [{"item": str(r_.item), "parts": [[str(p_.label), int(p_.count), [str(k_) for k_ in p_.any_of]] for p_ in r_.parts]}
                                               for r_ in gen.get_editor_property("recipes")] if L5 else [],
                                   # (level 5: the weights of armour her hero wears)
                                   "wears": [str(x.name).lower() for h_ in gen.get_editor_property("heroes") if str(h_.name) == str(gen.get_editor_property("current_hero")) for x in h_.wears] if L5 else None,
                                   "keys": list(gen.get_editor_property("controls_keys")), "pad": list(gen.get_editor_property("controls_pad")), "rogue_controls": bool(gen.get_editor_property("rogue_controls")),
                                   "slashes": [{"name": str(s_.name), "tier": s_.tier, "bonus": s_.bonus, "type": str(s_.get_editor_property("type")), "text": str(s_.text),
                                                "color": [round(s_.color.r, 3), round(s_.color.g, 3), round(s_.color.b, 3)]} for s_ in gen.get_editor_property("slashes")] if W5M2 else []})
    if MODE == "render":
        sec = unreal.TimeManagementLibrary.conv_qualified_frame_time_to_seconds(G["player"].get_current_time())
        start = not G["going"] and sec > 1e-4 and G["combat"] is not None
        if not G["going"] and not start: G["w0"] = wt
        G["t"] = wt - G["w0"]; G["frame"] = int(sec * FPS + 1e-3)
    else:
        start = not G["going"] and wt >= G["w0"] and G["combat"] is not None
        G["t"] = wt - G["w0"]; G["frame"] = int(math.floor(G["t"] * FPS))
    if start:
        G["going"] = True; gen.set_frame_budget(1.0e6); gen.restart_play(SEED); S["hp"].clear(); S["snd"] = {}; S["bursts"] = 0; S["music"] = None
        S["casts"] = G["combat"].attacks_made; S["bolts"] = G["combat"].bolts_cast; S["bursts_n"] = G["combat"].bolts_on_monsters + G["combat"].bolts_elsewhere
        S["rolls"] = G["combat"].rolls; S["dodged"] = G["combat"].dodged_hits
        if L4: S["found"] = gen.items_found; S["refused"] = G["combat"].casts_refused
        if L5: S["worn"] = "None"; S["taken"] = G["combat"].hits_taken
        if W5R: S["wsig"] = None; S["tnotice"] = ""
        if W5K: S["craftl"] = None; S["repl"] = None
        if W5M2: S["slashl"] = None; S["sgiven"] = [str(x) for x in gen.slashes_given]; S["procs"] = {str(k): v for k, v in G["combat"].slash_procs.items()}
        if W5S: S["rel"] = {str(k): v for k, v in G["combat"].spells_released.items()}; S["ssig"] = None; S["menul"] = None
    next(G["run"])
    if W5M4 and G.get("combat") is not None and T() > 0.0 and not G["combat"].is_dead(): mw4_heal()          # (every frame: tier 3 to 5's blows killed her between two checks)
    if (W5G or W5W2) and "grip_cam" in G: G["pc"].set_control_rotation(Rot(roll=0.0, pitch=G["grip_cam"][1], yaw=G["grip_cam"][0]))       # (run5g: the camera in front of her)
    if G["going"] and G["combat"] is not None:
        hits(); heard()
        n = len(gen.get_section_coords())
        if n != G["sec_n"]:
            G["sec_n"] = n; l = loc(); event("generated", sections=n, she_is_at=[round(l.x), round(l.y)], monsters=len(gen.get_monsters()))
        if G["frame"] >= 0 and G["t"] >= 0.0:
            if G["frame"] not in S["rows"] and G["frame"] % 6 == 0: snap_maps()
            S["rows"].setdefault(G["frame"], []).append(sample())
    if MODE != "render" and G["t"] >= DUR: stop()
    elif MODE == "render" and G["t"] >= DUR + 0.4: save()
def tick(dt):
    try: body()
    except StopIteration: stop("the pilot ran out")
    except Exception as e:
        import traceback
        unreal.log_error("RDMREEL error: " + str(e) + traceback.format_exc()); stop(str(e))
unreal._rdm_reel = unreal.register_slate_post_tick_callback(tick)
print("reel pilot armed:", MODE, DUR)
