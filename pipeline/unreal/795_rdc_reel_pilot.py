"""random_dungeoncombat_level demo reel: the pilot and the recorder. Plays jrpg-fem5-tripo through the dungeon with the
calls the keys make (movement input, the combat component's attack and weapon functions, the generator's F on doors),
turns the game's own third-person camera, and records the play for the overlay
(pipeline/blender_numpy/rdc_reel_overlay.py: the Movie Render Queue does not draw the HUD). The record also holds every
sound the game played (by occasion), every blood burst and the wounds each monster in view carries.
  render    (default) arm it right before 796: it waits for the render's world and LS_RDC_Showcase and starts with frame 0
  rehearse  the PIE session that is running now, in real time (the HUD is on)
On the first frame the dungeon is put back to its start (ARDDungeonGenerator.RestartPlay with a fixed session seed, so
the section generated during the reel is the same every time) and she is set down on the hallway to the east edge,
12 m before the line where the next section is generated (or, when a monster stands by that hallway, a little before it). From there she goes east: she fights what comes at her (a
different weapon each fight: sword, spear, axe; she lets the first monster strike first), opens the doors in her way,
crosses the line (the section generates), walks into the new section and fights there.
Writes SourceArt/random_dungeon_combat/cine_render.json (rehearse: cine_rehearsal.json) and logs "RDCREEL saved".
Keeps its namespace (tick callback); a pilot left armed by an earlier run is dropped. Args: [render|rehearse] [seconds]"""
import unreal, sys, json, math, os
__keep__ = True
MODE = sys.argv[1] if len(sys.argv) > 1 else "render"
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 45.0
FPS = 30; SEED = 20261013
HUNTS, HUNT_UNTIL, HUNT_TILES = 2, 15.0, 14          # before she goes east: this many fights at most, not after this time (s), monsters within this many tiles of way
OUT = "E:\\code\\claude-ue5\\claude_ue5\\SourceArt\\random_dungeon_combat\\" + ("cine_render.json" if MODE == "render" else "cine_rehearsal.json")
V = unreal.Vector; Rot = unreal.Rotator; GS = unreal.GameplayStatics; IP = unreal.IntPoint
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
G = {}
S = {"rows": {}, "events": [], "segs": [], "maps": [], "saved": False, "seg": "", "note": {}, "hp": {}, "mapsig": {}, "disc": {}, "snd": {}, "bursts": 0}
if getattr(unreal, "_rdc_reel", None) is not None:
    try: unreal.unregister_slate_post_tick_callback(unreal._rdc_reel)
    except Exception: pass
def T(): return G["t"]
def loc(): return G["pawn"].get_actor_location()
def event(kind, **kw):
    S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": kind, **kw})
    unreal.log("RDCREEL %6.2f s  %s %s" % (T(), kind, json.dumps(kw)[:200]))
def seg(name):
    S["seg"] = name; S["segs"].append({"name": name, "t": round(max(T(), 0.0), 3)}); unreal.log("RDCREEL %6.2f s  == %s" % (T(), name))
def alive(m):
    try: return m is not None and unreal.SystemLibrary.is_valid(m) and not m.is_dead()
    except Exception: return False
def d2(a, b): return math.hypot(a.x - b.x, a.y - b.y)
def yaw_to(a, b): return math.degrees(math.atan2(b.y - a.y, b.x - a.x))
def turn(cur, want, step):
    d = (want - cur + 180.0) % 360.0 - 180.0
    return cur + max(-step, min(step, d))

# ---------------------------------------------------------------- her hands and feet
def move(to, scale=1.0):
    l = loc(); d = V(to.x - l.x, to.y - l.y, 0.0)
    if d.length() > 1.0: G["pawn"].add_movement_input(d.normal(), scale, False); G["heading"] = yaw_to(l, to)
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
    pts = list(sec.find_path_world(a, b)) if sec else []
    return pts
def threat():
    """the monster to fight: one that is after her, or one right by her way"""
    l = loc(); best = None
    for m in G["gen"].get_monsters():
        if not alive(m): continue
        ml = m.get_actor_location(); d = d2(l, ml)
        if abs(ml.z - l.z) > 300: continue
        if (m.is_aggro() and d < 1100.0) or d < 520.0:
            if best is None or d < best[0]: best = (d, m)
    return best[1] if best else None

def fight(m):
    c = G["combat"]; p = G["pawn"]; n = G["fights"]; G["fights"] += 1
    c.select_weapon(n % 3)
    name = str(m.monster_name); hp0 = m.get_max_health(); h0 = c.get_health(); t0 = T(); b0 = c.hits_landed
    guard = (1.3, 2.6, 0.5)[min(n, 2)]; ht0 = c.hits_taken   # she lets it strike first: the first two fights until it has (or this long), the last hardly
    event("fight", monster=name, weapon=str(c.get_weapon_name()), its_hit_points=hp0, its_damage=m.get_damage(), section=[m.get_editor_property("section").get_editor_property("coord").x, 0])
    seen = None
    while alive(m) and not c.is_dead() and T() - t0 < 14.0 and T() < DUR + 1.0:
        l = loc(); ml = m.get_actor_location(); gap = d2(l, ml) - m.capsule_component.get_scaled_capsule_radius() - 36.0
        reach = c.get_weapon_reach()
        G["heading"] = yaw_to(l, ml)
        if gap > reach * 0.72 and not c.is_attacking(): move(ml, 1.0 if gap > reach + 150.0 else 0.55); doors()
        elif not c.is_attacking():
            # in reach: she turns to it (the attack does so too) and strikes
            p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=turn(p.get_actor_rotation().yaw, yaw_to(l, ml), 540.0 * G["el"])), False)
            if seen is None: seen = T()
            if T() - seen >= guard or c.hits_taken > ht0: c.start_attack()
        # in a room the camera comes round to the side of the fight; in a hallway (3 m wide) it stays behind her, higher
        sec = section_of(l); wide = sec is not None and sec.room_at(l) >= 0 and "unction" not in sec.get_room_kind(sec.room_at(l))
        camera(side=(38.0 if n % 2 == 0 else -38.0) if wide else 10.0, pitch=-14.0 if wide else -27.0, rate=75.0)
        yield
    if not alive(m): event("kill", monster=name, weapon=str(c.get_weapon_name()), blows=c.hits_landed - b0, seconds=round(T() - t0, 2), she_lost=round(max(0.0, h0 - c.get_health())), its_hit_points=hp0)
    else: event("left", monster=name)
    t1 = T()
    while T() - t1 < 0.45: camera(side=20.0, rate=75.0); yield          # (a breath before she moves on)
def run():
    gen, pc, p = G["gen"], G["pc"], G["pawn"]
    seg("start")
    while T() <= 0.0 or G["combat"] is None:
        camera(rate=1e6); yield
    # ---- the way east: from the middle of the start section to the hallway that leaves its east edge
    sec0 = gen.get_section(IP(0, 0)); half = gen.get_editor_property("section_tiles") * gen.get_editor_property("tile_size") / 2.0
    trig = half - gen.get_editor_property("trigger_distance")
    # (of the three hallways that leave the east edge, the one with the shortest way from the middle)
    ways = [list(sec0.find_path_world(gen.get_start_room_center(), q)) for q in sec0.get_portal_points() if q.x > half - 400.0]
    way = min([x for x in ways if len(x) > 10], key=len); portal = way[-1]
    assert len(way) > 10, "no way to the east edge"
    k0 = next(i for i, q in enumerate(way) if q.x >= trig - 1200.0)
    # she is set down a dozen metres before the monster nearest to this way (so the first fight comes at once), at most
    # 45 m and at least 9 m before the line
    near = None
    for q in gen.get_monsters():
        if not alive(q): continue
        ql = q.get_actor_location(); i = min(range(len(way)), key=lambda j: d2(way[j], ql))
        if trig - 4500.0 <= way[i].x <= trig + 1800.0 and d2(way[i], ql) < 2700.0 and (near is None or d2(way[i], ql) < near[0]): near = (d2(way[i], ql), i, str(q.monster_name))
    if near is not None:
        k0 = min(max(next(i for i, q in enumerate(way) if q.x >= trig - 4500.0), near[1] - 5), next(i for i, q in enumerate(way) if q.x >= trig - 1200.0)); S["note"]["first"] = near[2]
    route = Route(way[k0:] + [V(portal.x + 300.0 * k, portal.y, portal.z) for k in range(1, 6)])
    p.set_actor_location(V(way[k0].x, way[k0].y, 100.0), False, True); G["heading"] = yaw_to(way[k0], way[min(k0 + 3, len(way) - 1)])
    p.set_actor_rotation(Rot(roll=0.0, pitch=0.0, yaw=G["heading"]), True)
    S["note"].update({"start": [round(way[k0].x), round(way[k0].y)], "trigger_x": round(trig), "portal": [round(portal.x), round(portal.y)]})
    event("start", at=S["note"]["start"], to_the_line_m=round((trig - way[k0].x) / 100.0, 1))
    # a moment standing (the title), the camera behind her, then she sets off
    G["cam_yaw"] = G["heading"]; G["cam_pitch"] = -17.0
    while T() < 0.9:
        camera(rate=1e6)
        if T() > 0.5: move(route.target(), 1.0)
        yield
    seg("walk"); stuck = 0.0; last = loc(); new_route = False; east = route.p[route.i:]; prey = None; prey_t = -9.0; hunting = False
    def onward():
        # the way east again from wherever the fight left her
        back = path(loc(), portal)
        return Route(back + east[-5:]) if len(back) > 1 else Route(east)
    while True:
        m = threat()
        if m is not None:
            seg("fight"); yield from fight(m); seg("walk"); stuck = 0.0; last = loc(); prey = None; hunting = False
            if gen.world_to_section(loc()).x == 0: route = onward()
            continue
        here = gen.world_to_section(loc())
        if (here.x == 0 and G["fights"] < HUNTS and T() < HUNT_UNTIL) or (here.x >= 1 and new_route):
            # the start section's monsters near her first (they are no match for her), and in the new section whatever
            # is nearest (those are): she goes and finds them
            if T() - prey_t > 1.0:
                prey_t = T(); best = None; mine = section_of(loc())
                for q in gen.get_monsters():
                    if not alive(q) or q.get_editor_property("section") != mine: continue
                    pts = path(loc(), q.get_actor_location())
                    if 1 < len(pts) <= (HUNT_TILES if here.x == 0 else 40) and (best is None or len(pts) < len(best[1])): best = (q, pts)
                if best is not None:
                    if not hunting or prey != best[0]: event("hunt", monster=str(best[0].monster_name), way_m=len(best[1]) * 3)
                    prey = best[0]; route = Route(best[1]); hunting = True
                elif hunting and here.x == 0: hunting = False; route = onward()
        elif hunting and here.x == 0: hunting = False; route = onward()
        if here.x >= 1 and not new_route and gen.get_section(IP(1, 0)) is not None and not gen.get_section(IP(1, 0)).is_building():
            # in the new section: toward the nearest monster of it (they are a match for her)
            new_route = True; l = loc(); sec1 = gen.get_section(IP(1, 0))
            ms = [q for q in gen.get_monsters() if alive(q) and q.get_editor_property("section") == sec1]
            if ms:
                q = min(ms, key=lambda a: d2(a.get_actor_location(), l)); pts = list(sec1.find_path_world(l, q.get_actor_location()))
                if len(pts) > 1: route = Route(pts); event("into_new_section", toward=str(q.monster_name), way_m=round(len(pts) * 3))
        move(route.target(), 1.0); doors(); camera()
        # stuck on a door leaf or a corner: the way again from where she is
        stuck = stuck + G["el"] if d2(loc(), last) < 60.0 * G["el"] else 0.0; last = loc()
        if stuck > 1.2:
            stuck = 0.0; pts = path(loc(), route.p[-1])
            if len(pts) > 1: route = Route(pts); event("repath")
        yield

# ---------------------------------------------------------------- the recorder
def r3(v): return [round(v.x, 1), round(v.y, 1), round(v.z, 1)]
def snap_maps():
    """the map data as the HUD has it: a section's rooms when it appears (again when its chests and torches are in), and the rooms she has discovered"""
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
    return {"t": round(T(), 4), "p": r3(l), "yaw": round(p.get_actor_rotation().yaw, 1), "sp": round(p.get_velocity().length()), "hp": round(c.get_health(), 1), "mhp": c.get_max_health(), "w": c.get_weapon_index(),
            "kills": c.kills, "atk": round(c.get_attack_time(), 3), "dead": int(c.is_dead()), "cp": r3(cm.get_camera_location()), "cr": [round(cr.pitch, 3), round(cr.yaw, 3), round(cr.roll, 3)],
            "fov": round(cm.get_fov_angle(), 2), "seg": S["seg"], "sections": len(gen.get_section_coords()), "mon": mons,
            "fire": round(min([d2(q, l) for q in gen.get_fire_loops()] or [-1.0]))}           # (the nearest fire that has a voice: cm, -1 none)
def hits():
    """the blows, from the hit points that went: a number floats up from each (as the HUD shows)"""
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
        unreal.log("RDCREEL %6.2f s  she is hit for %d (%d left)" % (T(), round(old - h), round(h)))
    S["hp"]["__her"] = h
def heard():
    """what was played since the last tick (the generator counts every sound by its occasion), and the blood bursts"""
    gen = G["gen"]; now = {str(k): v for k, v in gen.get_sound_counts().items()}
    for k, v in now.items():
        if v > S["snd"].get(k, 0): S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "sound", "key": k, "n": v - S["snd"].get(k, 0)})
    S["snd"] = now
    b = gen.get_blood()
    if b is not None and b.bursts != S["bursts"]:
        if b.bursts > S["bursts"]:
            at = b.last_burst_at; S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": "blood", "at": [round(at.x), round(at.y), round(at.z)], "from_her_cm": round(d2(at, loc())), "bursts": b.bursts})
        S["bursts"] = b.bursts
def save(why=None):
    if S["saved"]: return
    S["saved"] = True
    rows = [dict(S["rows"][k][len(S["rows"][k]) // 2], frame=k) for k in sorted(S["rows"])]           # (the middle sub-sample of each frame)
    out = {"fps": FPS, "mode": MODE, "seed": SEED, "rows": rows, "events": S["events"], "segs": S["segs"], "maps": S["maps"], "note": S["note"], "const": G.get("const", {}), "error": why}
    os.makedirs(os.path.dirname(OUT), exist_ok=True); json.dump(out, open(OUT, "w"), separators=(",", ":"))
    kills = [e for e in S["events"] if e["kind"] == "kill"]; last = rows[-1] if rows else {}
    snd = {}
    for e in S["events"]:
        if e["kind"] == "sound":
            k = e["key"].split("."); k = "Monster." + k[-1] if k[0] == "Monster" and len(k) == 3 else e["key"]; snd[k] = snd.get(k, 0) + e["n"]
    wounds = max([q[11] for r in rows for q in r["mon"] if len(q) > 11] or [0])
    msg = "%d frames | %d kills (%s) | she was hit %d times, %s hit points left | %d sections | %d doors | %s | %d blood bursts, %d of them hers | most wounds on one monster %d | sounds %s" % (
        len(rows), len(kills), ", ".join("%s with the %s" % (e["monster"], e["weapon"].lower()) for e in kills), sum(1 for e in S["events"] if e["kind"] == "hit" and e["on_player"]), last.get("hp"),
        last.get("sections", 0), sum(1 for e in S["events"] if e["kind"] == "door"), " ".join("%s@%.1f" % (e["kind"], e["t"]) for e in S["events"] if e["kind"] in ("generated", "into_new_section")),
        sum(1 for e in S["events"] if e["kind"] == "blood"), sum(1 for e in S["events"] if e["kind"] == "blood" and e["from_her_cm"] < 60), wounds, json.dumps(dict(sorted(snd.items()))))
    (unreal.log_error if why else unreal.log)(("RDCREEL failed: %s | " % why if why else "RDCREEL saved ") + msg)
def stop(why=None):
    unreal.unregister_slate_post_tick_callback(unreal._rdc_reel); unreal._rdc_reel = None
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
        pc.set_ignore_look_input(True)             # (the real mouse must not turn the camera)
        G["run"] = run()
        unreal.log("RDCREEL armed (%s), %.0f s" % (MODE, DUR))
    if w is None: stop(None if G["t"] >= DUR - 0.05 else "the world ended at %.2f s" % G["t"]); return
    if S["saved"]: return
    gen = G["gen"]; wt = GS.get_time_seconds(G["w"]); G["el"] = max(wt - G["wt"], 1e-4); G["wt"] = wt
    if G["combat"] is None:
        G["combat"] = gen.get_player_combat()
        if G["combat"] is not None:
            G["combat"].set_scripted_only(True)
            G["const"] = {"weapons": [{"name": str(d.name), "damage": d.damage, "reach": d.reach} for d in gen.get_editor_property("weapons")], "tile": gen.get_editor_property("tile_size"),
                          "section_tiles": gen.get_editor_property("section_tiles"), "max_health": G["combat"].get_max_health(), "average_blow": gen.get_average_weapon_damage(),
                          "start_tier": [gen.get_monster_health(IP(0, 0)), gen.get_monster_damage(IP(0, 0))], "runtime_tier": [gen.get_monster_health(IP(1, 0)), gen.get_monster_damage(IP(1, 0))]}
    if MODE == "render":
        sec = unreal.TimeManagementLibrary.conv_qualified_frame_time_to_seconds(G["player"].get_current_time())
        start = not G["going"] and sec > 1e-4 and G["combat"] is not None
        if not G["going"] and not start: G["w0"] = wt
        G["t"] = wt - G["w0"]; G["frame"] = int(sec * FPS + 1e-3)
    else:
        start = not G["going"] and wt >= G["w0"] and G["combat"] is not None
        G["t"] = wt - G["w0"]; G["frame"] = int(math.floor(G["t"] * FPS))
    if start:
        # the first frame: the dungeon as it is when play begins, with a fixed seed for what is generated from here on
        G["going"] = True; gen.set_frame_budget(1.0e6); gen.restart_play(SEED); S["hp"].clear(); S["snd"] = {}; S["bursts"] = 0
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
        unreal.log_error("RDCREEL error: " + str(e) + traceback.format_exc()); stop(str(e))
unreal._rdc_reel = unreal.register_slate_post_tick_callback(tick)
print("reel pilot armed:", MODE, DUR)
