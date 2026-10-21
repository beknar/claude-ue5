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
Writes SourceArt/random_dungeon_magic[2|3]/cine_render.json (level 4: random_dungeon_magic4/cine_<hero>.json; level 5:
random_dungeon_magic5/cine_summoner.json; rehearse: cine_rehearsal.json) and logs "RDMREEL saved".
Keeps its namespace (tick callback); a pilot left armed by an earlier run is dropped.
Args: [render|rehearse] [seconds] [level: "2", "3", "4" or "5"] [level 4: hero] [level 4: east|north|west|south]"""
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
DX, DY = {"east": (1, 0), "north": (0, 1), "west": (-1, 0), "south": (0, -1)}[WAY]
# (level 4: the hero fights as in her own level)
L2, L3 = LV == "2" or (L4 and HERO == "Warlock"), LV == "3" or (L4 and HERO == "Rogue")
MELEE = L4 and HERO == "Warrior"
CHESTS = L3 or L4                  # (she opens the containers she passes)
if L4: SEED += 101 * ["Warrior", "Mage", "Warlock", "Rogue", "Summoner"].index(HERO) + 7
if len(sys.argv) > 6: SEED = int(sys.argv[6])        # (level 4: a session seed of the reel's choosing: what the containers on her way hold)
OUT = "E:\\code\\claude-ue5\\claude_ue5\\SourceArt\\random_dungeon_magic" + ("" if LV == "1" else LV) + "\\" + (
    (f"cine_{HERO.lower()}.json" if L4 else "cine_render.json") if MODE == "render" else "cine_rehearsal.json")
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
                tf = T(); seg("fight"); G["casts0"] = G["combat"].attacks_made; yield from fight(m); seg("chest")
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
          from_m=round((d2(loc(), m.get_actor_location())) / 100.0, 1), armour=str(c.get_worn_armour()) if L5 else None, take=take)
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

def run():
    gen, pc, p = G["gen"], G["pc"], G["pawn"]
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
        for q, nxt in ex:
            if d2(q, l) > rad: continue
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
                         round(m.capsule_component.get_scaled_capsule_half_height()), int(m.is_attacking()), m.get_num_wounds(), int(m.get_max_health() > 1.25 * tier(m))])
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
            **({"arm": str(c.get_worn_armour()), "armv": round(c.get_armour(), 3)} if L5 else {})}
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
        wi = c.get_attack_index(); wn = str(G["gen"].get_editor_property("weapons")[wi].name) if wi >= 0 else ""
        S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "cast" if wn in ("Fire", "Dark Fire", "Crossbow") else "cut", "weapon": wn, "target": tg.get_name() if tg else None,
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
            if G.get("combat") is not None and ues.get_game_world() is not None: G["combat"].set_scripted_only(False); G["pc"].set_ignore_look_input(False)
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
                                   "items": [{"name": str(it.name), "kind": str(it.kind.name).lower(), "amount": it.amount, "seconds": it.seconds, "looks": str(it.looks)} for it in gen.get_editor_property("items")],
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
    next(G["run"])
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
