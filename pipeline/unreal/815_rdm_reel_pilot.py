"""random_dungeonmagic_level and random_dungeonmagic_level2 demo reel: the pilot and the recorder (generalised from 795; the
level is the one the render or PIE plays). Plays the caster (girl-caster-tripo; level 2: the dark caster,
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
Writes SourceArt/random_dungeon_magic[2]/cine_render.json (rehearse: cine_rehearsal.json) and logs "RDMREEL saved".
Keeps its namespace (tick callback); a pilot left armed by an earlier run is dropped. Args: [render|rehearse] [seconds] [level 2: "2"]"""
import unreal, sys, json, math, os
__keep__ = True
MODE = sys.argv[1] if len(sys.argv) > 1 else "render"
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 45.0
FPS = 30; SEED = 20261015
CAST_GAP = 950.0            # she stops this far (cm, to the monster's capsule) and casts
_lv = ""
for _w in unreal.ObjectIterator(unreal.World):
    if "random_dungeonmagic_level2" in _w.get_name(): _lv = "2"
L2 = (sys.argv[3] == "2") if len(sys.argv) > 3 else _lv == "2"           # (the argument wins: the editor may have the other level open)
OUT = "E:\\code\\claude-ue5\\claude_ue5\\SourceArt\\random_dungeon_magic" + ("2" if L2 else "") + "\\" + ("cine_render.json" if MODE == "render" else "cine_rehearsal.json")
SPEEDS = r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_" + ("darkcaster" if L2 else "caster") + r"\speeds.txt"
V = unreal.Vector; Rot = unreal.Rotator; GS = unreal.GameplayStatics; IP = unreal.IntPoint
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
G = {}
S = {"rows": {}, "events": [], "segs": [], "maps": [], "saved": False, "seg": "", "note": {}, "hp": {}, "mapsig": {}, "disc": {}, "snd": {}, "bursts": 0, "music": None, "casts": 0, "bolts": 0}
if getattr(unreal, "_rdm_reel", None) is not None:
    try: unreal.unregister_slate_post_tick_callback(unreal._rdm_reel)
    except Exception: pass
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
        if (m.is_aggro() and d < 1500.0) or (d < 1500.0 and sees(l, m)):          # (the spell reaches 14 m: she takes on what she sees that far)
            if best is None or d < best[0]: best = (d, m)
    return best[1] if best else None
def chests_of(c):
    md = G["gen"].get_editor_property("map_data").get(c)
    return [V(q.x, q.y, 100.0) for q in md.chests] if md else []          # (the map keeps them as 2D points)

def stand_by_chest(at, frm):
    """where to stand to open the chest at `at`: a spot 1 m or so from it that she can walk to from `frm` and from which
    F reaches that chest (the nearest door or container there is it); None when there is none"""
    gen = G["gen"]; best = None
    for r in (100.0, 140.0):
        for k in range(12):
            a = k * math.pi / 6; q = V(at.x + math.cos(a) * r, at.y + math.sin(a) * r, 100.0)
            what = str(gen.describe_nearest(q, 200.0))
            if not what.startswith("open") or "door" in what: continue
            pts = path(frm, q)
            if len(pts) and d2(pts[-1], q) < 160.0 and (best is None or len(pts) < best[0]): best = (len(pts), q)
    return best[1] if best else None

def open_chest(at, stand=None):
    """walks to a chest, opens it (F) and looks at it a moment"""
    gen = G["gen"]; stand = stand or stand_by_chest(at, loc())
    if stand is None: event("chest_missed", why="no place to stand"); return
    route = Route(path(loc(), stand) + [stand]); t0 = T(); stuck = 0.0; last = loc()
    event("to_chest", at=[round(at.x), round(at.y)], stand=[round(stand.x), round(stand.y)])
    while T() - t0 < 9.0:
        l = loc()
        if d2(l, stand) < 45.0: break
        move(route.target(90.0), run=d2(l, stand) > 600.0); doors(); camera(side=-22.0, pitch=-24.0, rate=90.0)
        stuck = stuck + G["el"] if d2(loc(), last) < 40.0 * G["el"] else 0.0; last = loc()
        if stuck > 0.8:
            stuck = 0.0; G["chest_repaths"] = G.get("chest_repaths", 0) + 1
            if G["chest_repaths"] > 2: break
            route = Route(path(loc(), stand) + [stand]); event("repath")
        yield
    G["chest_repaths"] = 0
    l = loc(); what = str(gen.describe_nearest(l, 200.0))
    if what.startswith("open") and "door" not in what and d2(l, at) < 260.0:
        G["heading"] = yaw_to(l, at); G["pawn"].set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), False)
        gen.interact_nearest(l, 200.0); event("chest", what=what, at=[round(at.x), round(at.y)]); G["key_hit"] = "f"; G["keys_t"] = T()
        t1 = T()
        while T() - t1 < 1.3: camera(side=-30.0, pitch=-26.0, rate=70.0); yield
    else: event("chest_missed", what=what)

def fight(m):
    """the fire spell from range: she closes in until she can see it within the spell's reach, then casts until it is down"""
    c = G["combat"]; p = G["pawn"]; n = G["fights"]; G["fights"] += 1
    name = str(m.monster_name); hp0 = m.get_max_health(); h0 = c.get_health(); t0 = T(); b0 = c.hits_landed; k0 = c.kills
    event("fight", monster=name, its_hit_points=hp0, its_damage=m.get_damage(), section=[m.get_editor_property("section").get_editor_property("coord").x, 0],
          from_m=round((d2(loc(), m.get_actor_location())) / 100.0, 1))
    route = None; rt = -9.0; casts = 0; reach = G["gen"].get_editor_property("weapons")[0].reach
    while alive(m) and not c.is_dead() and T() - t0 < 16.0 and T() < DUR + 1.0:
        l = loc(); ml = m.get_actor_location(); gap = d2(l, ml) - m.capsule_component.get_scaled_capsule_radius()
        G["heading"] = yaw_to(l, ml)
        if not c.is_attacking():
            face = lambda: p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=turn(p.get_actor_rotation().yaw, yaw_to(l, ml), 720.0 * G["el"])), False)
            if L2 and gap < reach - 10.0:
                face()                                            # (the sword: close enough)
                if c.start_attack(): G["key_hit"] = "lmb"; G["keys_t"] = T()
            elif gap > CAST_GAP or not sees(l, m) or (L2 and casts >= 2):
                if route is None or T() - rt > 0.7: route = Route(path(l, ml)); rt = T()
                move(route.target() if len(route.p) > 1 and gap > 400.0 else ml, run=True); doors()
            else:
                face()
                if c.start_spell() if L2 else c.start_attack(): G["key_hit"] = "e"; G["keys_t"] = T(); casts += 1
        camera(side=(30.0 if n % 2 == 0 else -30.0) if wide_here() else 8.0, pitch=-15.0 if wide_here() else -25.0, rate=80.0)
        yield
    G["last_fight"] = T()
    if not alive(m): event("kill", monster=name, casts=c.attacks_made - G.get("casts0", 0), blows=c.hits_landed - b0, seconds=round(T() - t0, 2), she_lost=round(max(0.0, h0 - c.get_health())), its_hit_points=hp0)
    else: event("left", monster=name)
    t1 = T()
    while T() - t1 < 0.5: camera(side=18.0, rate=70.0); yield

def run():
    gen, pc, p = G["gen"], G["pc"], G["pawn"]
    seg("start")
    while T() <= 0.0 or G["combat"] is None:
        camera(rate=1e6); yield
    # (RestartPlay puts the start section's monsters back over a few frames, the old ones still there for a frame or
    # two: the choice below waits half a second for them)
    def start_count(): return sum(1 for q in gen.get_monsters() if alive(q) and q.get_editor_property("section").get_editor_property("coord") == IP(0, 0))
    while T() < 0.5 or (start_count() < 10 and T() < 1.2):
        camera(rate=1e6); yield
    # ---- the way east: from the middle of the start section to the hallway that leaves its east edge
    sec0 = gen.get_section(IP(0, 0)); half = gen.get_editor_property("section_tiles") * gen.get_editor_property("tile_size") / 2.0
    trig = half - gen.get_editor_property("trigger_distance")
    ways = [list(sec0.find_path_world(gen.get_start_room_center(), q)) for q in sec0.get_portal_points() if q.x > half - 400.0]
    way = min([x for x in ways if len(x) > 10], key=len); portal = way[-1]
    # a chest near that way, 5 to 26 m before the line, a short walk from it (the chests stay where they are; the
    # monsters wander): she is set down two tiles from it and opens it, then goes for the monster nearest to her then
    best = None; prey0 = None
    for ch in chests_of(IP(0, 0)):
        i = min(range(len(way)), key=lambda j: d2(way[j], ch))
        if not (trig - 2600.0 <= way[i].x <= trig - 500.0): continue
        pts = list(sec0.find_path_world(way[i], ch))
        if not 2 <= len(pts) <= 7: continue
        stand = stand_by_chest(ch, way[i])
        if stand is None: continue
        if best is None or len(pts) < best[0]: best = (len(pts), i, pts, ch, stand)
    event("pick", chest=None if best is None else [round(best[3].x), round(best[3].y)])
    if best is not None:
        _, k0, pts, chest0, stand0 = best; st = pts[max(0, len(pts) - 3)]
    else:
        k0 = next(i for i, q in enumerate(way) if q.x >= trig - 2500.0); chest0 = None; stand0 = None; st = way[k0]
    route = Route(way[k0:] + [V(portal.x + 300.0 * k, portal.y, portal.z) for k in range(1, 6)])
    p.set_actor_location(V(st.x, st.y, 100.0), False, True); G["heading"] = yaw_to(st, chest0 if chest0 else way[min(k0 + 3, len(way) - 1)])
    p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), True)
    S["note"].update({"start": [round(st.x), round(st.y)], "trigger_x": round(trig), "portal": [round(portal.x), round(portal.y)], "chest": [round(chest0.x), round(chest0.y)] if chest0 else None})
    event("start", at=S["note"]["start"], to_the_line_m=round((trig - st.x) / 100.0, 1))
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
        seg("fight"); G["casts0"] = G["combat"].attacks_made; yield from fight(prey[1])
    seg("walk"); stuck = 0.0; last = loc(); new_route = False; east = route.p[route.i:]; hunted = False; chest1_done = False
    def onward():
        back = path(loc(), portal)
        return Route(back + east[-5:]) if len(back) > 1 else Route(east)
    route = onward()
    while True:
        m = threat()
        if m is None and T() - G.get("last_fight", -99.0) > 10.0 and T() < DUR - 8.0 and T() - G.get("hunt_t", -9.0) > 2.0:
            # no fight for a while: the nearest monster within 14 tiles of way (it is then fought from range)
            G["hunt_t"] = T(); best = None
            for q in gen.get_monsters():
                if not alive(q) or d2(q.get_actor_location(), loc()) > 4500.0: continue
                pts = path(loc(), q.get_actor_location())
                if 1 < len(pts) <= 14 and (best is None or len(pts) < best[0]): best = (len(pts), q)
            if best is not None: event("hunt", monster=str(best[1].monster_name), way_m=best[0] * 3); m = best[1]
        if m is not None:
            seg("fight"); G["casts0"] = G["combat"].attacks_made; yield from fight(m); seg("walk"); stuck = 0.0; last = loc()
            here = gen.world_to_section(loc())
            if here.x == 0: route = onward()
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
        if here.x >= 1 and not new_route and gen.get_section(IP(1, 0)) is not None and not gen.get_section(IP(1, 0)).is_building():
            new_route = True; l = loc(); sec1 = gen.get_section(IP(1, 0))
            ms = [q for q in gen.get_monsters() if alive(q) and q.get_editor_property("section") == sec1]
            if ms:
                q = min(ms, key=lambda a: d2(a.get_actor_location(), l)); pts = list(sec1.find_path_world(l, q.get_actor_location()))
                if 1 < len(pts) <= 25: route = Route(pts); event("into_new_section", toward=str(q.monster_name), way_m=round(len(pts) * 3))
        if route.done() and here.x == 0: route = onward()
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
def sample():
    gen, pc, p, c = G["gen"], G["pc"], G["pawn"], G["combat"]; cm = pc.player_camera_manager; l = p.get_actor_location(); cr = cm.get_camera_rotation()
    mons = []
    for m in gen.get_monsters():
        try:
            ml = m.get_actor_location()
            if d2(ml, l) > 3200.0: continue
            mons.append([m.get_name(), str(m.monster_name), round(ml.x), round(ml.y), round(ml.z), round(m.get_health(), 1), m.get_max_health(), int(m.is_aggro()), int(m.is_dead()),
                         round(m.capsule_component.get_scaled_capsule_half_height()), int(m.is_attacking()), m.get_num_wounds()])
        except Exception: pass
    # the keys that do what she does now: W (and Shift while she runs), E as she casts, F as she opens
    sp = p.get_velocity().length(); keys = G.get("key_hit", "") if T() - G.get("keys_t", -9.0) < 0.5 else ""
    moving = "run" if sp > 0.5 * (WALK + RUN) else ("walk" if sp > 40.0 else "")
    return {"t": round(T(), 4), "p": r3(l), "yaw": round(p.get_actor_rotation().yaw, 1), "sp": round(p.get_velocity().length()), "hp": round(c.get_health(), 1), "mhp": c.get_max_health(), "w": c.get_weapon_index(),
            "kills": c.kills, "atk": round(c.get_attack_time(), 3), "charging": int(c.is_charging()), "bolts": [r3(b) for b in c.get_bolts()], "dead": int(c.is_dead()),
            "cp": r3(cm.get_camera_location()), "cr": [round(cr.pitch, 3), round(cr.yaw, 3), round(cr.roll, 3)], "fov": round(cm.get_fov_angle(), 2), "seg": S["seg"],
            "sections": len(gen.get_section_coords()), "mon": mons, "keys": keys, "moving": moving, "fire": round(min([d2(q, l) for q in gen.get_fire_loops()] or [-1.0]))}
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
        S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "cast" if wn == "Fire" else "cut", "weapon": wn, "target": tg.get_name() if tg else None,
                            "m": round(d2(p.get_actor_location(), tg.get_actor_location()) / 100.0, 1) if tg else None})       # (how far she cast from)
    if c.bolts_cast > S["bolts"]: S["bolts"] = c.bolts_cast; S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "bolt", "from": r3(c.last_bolt_from)})
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
    msg = "%d frames | %d casts, %d bolts, %d bursts | %d kills (%s) | chests %d | doors %d | sections %d (%s) | she was hit %d times, %s hit points left | blood bursts %d" % (
        len(rows), len(ev("cast")), len(ev("bolt")), len(ev("burst")), len(ev("kill")), ", ".join("%s in %d casts" % (e["monster"], e["casts"]) for e in ev("kill")), len(ev("chest")), len(ev("door")),
        last.get("sections", 0), " ".join("%s@%.1f" % (e["kind"], e["t"]) for e in S["events"] if e["kind"] in ("generated", "into_new_section", "chest", "fight", "kill")),
        sum(1 for e in ev("hit") if e["on_player"]), last.get("hp"), len(ev("blood")))
    (unreal.log_error if why else unreal.log)(("RDMREEL failed: %s | " % why if why else "RDMREEL saved ") + msg)
def stop(why=None):
    unreal.unregister_slate_post_tick_callback(unreal._rdm_reel); unreal._rdm_reel = None
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
            wd = next(d for d in gen.get_editor_property("weapons") if d.spell)
            G["const"] = {"level": 2 if L2 else 1, "weapons": [{"name": str(d.name), "damage": d.damage, "reach": d.reach, "spell": bool(d.spell)} for d in gen.get_editor_property("weapons")], "tile": gen.get_editor_property("tile_size"),
                          "section_tiles": gen.get_editor_property("section_tiles"), "max_health": G["combat"].get_max_health(), "average_blow": gen.get_average_weapon_damage(),
                          "start_tier": [gen.get_monster_health(IP(0, 0)), gen.get_monster_damage(IP(0, 0))], "runtime_tier": [gen.get_monster_health(IP(1, 0)), gen.get_monster_damage(IP(1, 0))],
                          "spell": {"name": str(wd.name), "damage": wd.damage, "reach": wd.reach, "speed": wd.bolt_speed, "splash": wd.bolt_splash}, "walk": WALK, "run": RUN,
                          "title": gen.get_editor_property("player_title"), "hint": gen.get_editor_property("controls_hint")}
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
