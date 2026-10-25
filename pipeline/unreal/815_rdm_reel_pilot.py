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
Args: [render|rehearse] [seconds] [level: "2", "3", "4" or "5"] [level 4: hero] [level 4: east|north|west|south; level 5:
weapons, heroes, craft, spells or grip] [session seed]"""
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
LV = sys.argv[3] if len(sys.argv) > 3 else _lv           # (the argument wins: the editor may have another level open)
L5 = LV == "5"; L4 = LV == "4" or L5                     # (level 5 is level 4's Save As copy: its machinery, the armour's plan)
HERO = sys.argv[4] if len(sys.argv) > 4 else ("Summoner" if L5 else "Rogue")
WAY = sys.argv[5] if len(sys.argv) > 5 else "east"
W5H = L5 and WAY == "heroes"            # (level 5: the four heroes' weapons reel: run5h)
W5C = L5 and WAY == "craft"             # (level 5: the armour table, loot and crafting reel: run5c)
W5S = L5 and WAY == "spells"            # (level 5: the spells, rings, monsters by tier, corpses and menu reel: run5s)
W5G = L5 and WAY == "grip"              # (level 5: the two-handed grip close up: run5g)
W5R = L5 and WAY in ("weapons", "heroes", "craft", "spells")       # (level 5: the weapons and tiers reels: run5w, run5h; their recording; run5c's and run5s's too)
W5K = W5C or W5S                        # (the crafting panel's and the repair list's recording)
DX, DY = {"east": (1, 0), "north": (0, 1), "west": (-1, 0), "south": (0, -1)}.get(WAY, (1, 0))
# (level 4: the hero fights as in her own level)
L2, L3 = LV == "2" or (L4 and HERO == "Warlock"), LV == "3" or (L4 and HERO == "Rogue")
MELEE = L4 and HERO == "Warrior"
CHESTS = L3 or L4                  # (she opens the containers she passes)
if L4: SEED += 101 * ["Warrior", "Mage", "Warlock", "Rogue", "Summoner"].index(HERO) + 7
if len(sys.argv) > 6: SEED = int(sys.argv[6])        # (level 4: a session seed of the reel's choosing: what the containers on her way hold)
OUT = "E:\\code\\claude-ue5\\claude_ue5\\SourceArt\\random_dungeon_magic" + ("" if LV == "1" else LV) + "\\" + (
    ((f"cine_quartet_{HERO.lower()}.json" if W5H else f"cine_craft_{HERO.lower()}.json" if W5C else f"cine_spells_{HERO.lower()}.json" if W5S else f"cine_grip_{HERO.lower()}.json" if W5G else f"cine_{HERO.lower()}.json") if L4 else "cine_render.json")
    if MODE == "render" else ("cine_rehearsal_spells_%s.json" % HERO.lower() if W5S else "cine_rehearsal.json"))
SPEEDS = r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_" + ({"Warrior": "fem5", "Mage": "caster", "Warlock": "darkcaster", "Rogue": "rogue", "Summoner": "summoner3"}[HERO] if L4 else
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
        if L5:
            # (a monster that comes at her on the way is dealt with first; then on to the chest)
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
            elif (ranged and gap < 1500.0 and sees(l, m)) or (not ranged and gap < reach - 10.0):
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
    if m is not None:
        event("last_monster", monster=str(m.monster_name), m=round(d2(loc(), m.get_actor_location()) / 100.0))
        seg("fight"); G["casts0"] = c.attacks_made; yield from fight_w(m); seg("tiers")
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
        if m is not None: seg("fight"); G["casts0"] = c.attacks_made; yield from fight_w(m); seg("tiers")
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
    if boom:
        G["boom0"] = (boom.target_arm_length, boom.do_collision_test, boom.socket_offset, boom.target_offset)
        boom.target_arm_length = 165.0; boom.do_collision_test = False; boom.socket_offset = V(0.0, 0.0, 0.0); boom.target_offset = V(0.0, 0.0, 38.0)
    if cam: G["fov0"] = cam.field_of_view; cam.field_of_view = 40.0
    G["grip_cam"] = (face + 180.0, -7.0)
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

def run():
    gen, pc, p = G["gen"], G["pc"], G["pawn"]
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
            S["maps"].append({"t": round(max(T(), 0.0), 3), "coord": [c.x, c.y], "rects": [[r.min.x, r.min.y, r.max.x, r.max.y, r.kind.name, int(r.corridor)] for r in m.rects],
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
            **(tier_row(l) if W5R else {})}
def tier_row(l):
    """(the weapons and tiers reel) what the HUD's tier panel shows (ARDHUD::DrawTiers) and a seal's prompt near her"""
    gen = G["gen"]; s = gen.world_to_section(l); t_ = gen.tier_of(s)
    r_ = gen.get_section_progress(s); ok, pr = r_ if isinstance(r_, tuple) else (True, r_)
    near = str(gen.describe_nearest(l, 260.0))
    return {"tier": [t_, gen.get_tier_cleared(t_), gen.tier_size(t_), pr.rooms_explored if ok else -1, pr.rooms if ok else -1, pr.chests_looted if ok else -1, len(pr.chests) if ok else -1,
                     len(pr.killed) if ok else -1, pr.monsters if ok else -1, int(pr.cleared) if ok else 0, gen.get_open_tiers(), gen.max_tier],
            "seal": "" if near else str(gen.describe_seal_near(l, 450.0))}
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
        if W5R:
            # (the weapons reel: her weapons as they are now (found ones join, broken ones go, wear goes down), the tiers' notices)
            ws_ = g.get_editor_property("weapons")
            wl = [{"name": str(d.name), "damage": round(c.get_damage_of(i), 2), "base_damage": d.damage, "reach": d.reach, "spell": bool(d.spell), "alongside": bool(d.alongside),
                   "mana": d.mana_cost, "ranged": bool(d.spell and d.bolt_mesh), "wear": c.get_weapon_wear(i), "durability": d.durability, "speed": d.speed_rating,
                   "rating": d.damage_rating, "type": str(d.weapon_type), "rate": round(d.play_rate, 3),
                   **({"spell_index": d.spell_index, "cooldown": d.cooldown, "icon": str(d.icon)} if W5S else {})} for i, d in enumerate(ws_)]
            sig = [(w_["name"], w_["wear"], w_["damage"]) for w_ in wl]          # (a ring changes the damage too)
            if sig != S.get("wsig"): S["wsig"] = sig; S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "weapons", "list": wl})
            tn = str(g.tier_notice)
            if tn != S.get("tnotice", ""): S["tnotice"] = tn; S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "tier_notice", "text": tn})
        if str(c.message) != S.get("msg", ""): S["msg"] = str(c.message); S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "message", "text": S["msg"]})
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
                if W5G:
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
            G["const"] = {"level": int(LV), "tactical": bool(gen.get_editor_property("tactical_maps")), "roll_distance": gen.get_editor_property("roll_distance"),
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
                                   "keys": list(gen.get_editor_property("controls_keys")), "pad": list(gen.get_editor_property("controls_pad")), "rogue_controls": bool(gen.get_editor_property("rogue_controls"))})
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
        if W5S: S["rel"] = {str(k): v for k, v in G["combat"].spells_released.items()}; S["ssig"] = None; S["menul"] = None
    next(G["run"])
    if W5G and "grip_cam" in G: G["pc"].set_control_rotation(Rot(roll=0.0, pitch=G["grip_cam"][1], yaw=G["grip_cam"][0]))       # (run5g: the camera in front of her)
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
