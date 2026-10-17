"""random_dungeoncombat_level combat test, run in PIE (793_rdc_combat.ps1 starts PIE, arms this and waits for
"RDCTEST done"). Drives the player's combat component and the generator directly (the keys do the same calls) and
checks what happens. Plan = comma separated steps:
  setup     she stands in the middle of the start section with 100 hit points and the first weapon in her hand
  weapons   each of the three weapons: its mesh in her right hand (shield on her left arm where it has one), an attack
            plays over her locomotion (her hand moves, the attack ends), the damage / reach figures; her hand is on
            the weapon's handle (where her hand is, the mesh is round and thin, and its axis passes through the hand)
            and the shield's top is above its point as she stands
  monsters  the start section: share of rooms with a monster (30% wanted), their average hit points and damage against
            hers (must be lower)
  kill[:N]  N times (default 3, a different weapon each time): next to the nearest live monster of the start section,
            she attacks until it is dead: every blow takes the weapon's damage, the kill is counted
  hurt      she stands by a monster without fighting back: it attacks and she loses its damage in hit points
  tier      the section east of the start is generated: its monsters are on a par with her (average hit points ~ hers,
            average damage ~ her average blow)
  death     she is brought to 0: she is down, and after the respawn time stands in the middle with full hit points
  regen     hurt and left alone, her hit points come back
  map       the stylised maps have their data (chests, torches) and M opens / closes the big map; with the tactical maps
            (bTacticalMaps) the big map is an overlay: with it open she walks and the left mouse button attacks
  blood     a blow on a monster throws a burst (drops in the air, spray) from where the monster is, drops land as
            decals; a blow on her throws one from her
  wounds    a monster she hits gets a wound a blow, on its skin, in an overlay material of its own whose parameters
            hold them; the wound moves with it; no other monster (of its kind or any) has a wound or an overlay;
            a pool spreads under it when it dies
  sounds    her footsteps (running and walking sets; no breath set is left), her voice when hurt; a door opening and closing;
            the fire loops take the fires next to her and drop them when she is away; every placed sound is at
            full level beside her and falls to nothing with distance; a monster's roar, hurt and death voice and
            the monsters' footsteps; the rumble of a section being generated
  music     while she wanders: a wandering track over the wandering atmosphere; a monster comes at her: the battle
            track and atmosphere (other files) from the start of the track; the fight over and her away: the wandering
            track again, further on than it was; the next fight has another battle track
  look      what is only seen: flame particles alive at the nearest torch and at a brazier (a light alone counts
            nothing); the broken walls: several pieces in use and none beside or above the same one, in every
            section; the cut face under each container lid is on the wood slot with texture coordinates of its own
  containers  every container of the start section, measured (container_check.py): closed, the lid lies on its body and a
            wardrobe's two doors stand on its front; four of each kind are opened: the lid stands up at the back, the
            doors out in front; closed again, they are back where they were
  walls     the broken walls (wall_check.py): rays from each broken segment's room on a grid over its face end on the
            wall or, through a hole, on the stone plate behind it (never beyond the wall); she pushes and jumps into
            holes low on the wall and stays out (without the plates the same rays went beyond the wall); every
            prison cell is closed all round (rays from its middle meet bars, a door or a wall), its hay pile blocks; dropped below the floor she is put back where she stood
Writes SourceArt/random_dungeon_combat/test_<tag>.json and logs "RDCTEST done | <tag> | ok / FAILED | ...". Args: plan tag"""
import unreal, sys, json, math, os
__keep__ = True
PLAN = [s.strip() for s in (sys.argv[1] if len(sys.argv) > 1 else "setup,weapons,monsters,kill,hurt,tier,death,regen,map,blood,wounds,sounds,music,containers,look,walls").split(",") if s.strip()]
TAG = sys.argv[2] if len(sys.argv) > 2 else "t"
OUT = "E:\\code\\claude-ue5\\claude_ue5\\SourceArt\\random_dungeon_combat"
V = unreal.Vector; GS = unreal.GameplayStatics; ML = unreal.MathLibrary
G = {}; R = {"tag": TAG, "plan": PLAN, "steps": []}
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
assert w is not None, "PIE is not running"
gen = GS.get_all_actors_of_class(w, unreal.RDDungeonGenerator)[0]
pc = GS.get_player_controller(w, 0); pawn = pc.get_controlled_pawn()
G.update({"w": w, "gen": gen, "pc": pc, "pawn": pawn})
def now(): return GS.get_time_seconds(G["w"])
def cb(): return G["gen"].get_player_combat()
def wait(sec):
    t0 = now()
    while now() - t0 < sec: yield
def step_result(name, ok, **kw):
    R["steps"].append({"step": name, "ok": bool(ok), **kw})
    unreal.log(f"RDCTEST step {name}: {'ok' if ok else 'FAILED'} {json.dumps(kw)[:1600]}")
def alive(m):
    try: return m is not None and unreal.SystemLibrary.is_valid(m) and not m.is_dead()
    except Exception: return False
def start_monsters(): return [m for m in G["gen"].get_monsters() if alive(m) and m.get_editor_property("section").get_editor_property("coord") == unreal.IntPoint(0, 0)]
def stand_by(m, gap=150.0):
    """puts her `gap` cm from the monster's capsule, on a walkable tile of its room, facing it"""
    p = G["pawn"]; sec = m.get_editor_property("section"); ml = m.get_actor_location(); rad = m.capsule_component.get_scaled_capsule_radius()
    best = None
    for k in range(16):
        a = k * math.pi / 8; q = V(ml.x + math.cos(a) * (gap + rad + 36), ml.y + math.sin(a) * (gap + rad + 36), ml.z)
        path = sec.find_path_world(q, ml)
        # (the place must be a walkable tile itself: the path search starts from the nearest one, also for a point in a wall)
        if sec.room_at(q) == sec.room_at(ml) and len(path) > 0 and math.hypot(path[0].x - q.x, path[0].y - q.y) < 135.0 and (best is None or len(path) < best[0]): best = (len(path), q)
    if best is None:
        # no such place round it (a narrow hallway): a tile or two along its way to the middle of the dungeon
        way = sec.find_path_world(ml, G["gen"].get_start_room_center())
        best = (0, way[min(2 if gap > 150 else 1, len(way) - 1)]) if len(way) > 1 else (0, V(ml.x + rad + 60, ml.y, ml.z))
    q = best[1]
    p.set_actor_location(V(q.x, q.y, 100.0), False, True)
    yaw = math.degrees(math.atan2(ml.y - q.y, ml.x - q.x)); p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw), True); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-15, yaw=yaw))

def step_setup():
    yield from wait(1.0)
    c = cb(); p = G["pawn"]; s = G["gen"].get_start_room_center(); l = p.get_actor_location()
    d = math.hypot(l.x - s.x, l.y - s.y); half = G["gen"].get_editor_property("section_tiles") * G["gen"].get_editor_property("tile_size") / 2
    wm = c.get_weapon_mesh() if c else None
    ok = c is not None and abs(c.get_health() - 100.0) < 0.5 and c.get_max_health() == 100.0 and d < 300 and math.hypot(s.x, s.y) < 0.2 * half and c.get_weapon_index() == 0 and wm is not None and wm.static_mesh is not None
    step_result("setup", ok, pawn=p.get_class().get_name(), hit_points=c.get_health() if c else None, from_start_room_cm=round(d), start_room_from_section_middle_cm=round(math.hypot(s.x, s.y)),
                weapon=str(c.get_weapon_name()) if c else None, weapons=len(G["gen"].get_editor_property("weapons")), combat=bool(G["gen"].get_editor_property("combat")))
def mesh_verts(m, section=None):
    vs = []
    for s in (range(m.get_num_sections(0)) if section is None else [section]): vs += list(unreal.ProceduralMeshLibrary.get_section_from_static_mesh(m, 0, s)[0])
    return vs
def grip_check(wm, hand):
    """what her hand closes on: the size of the weapon mesh where her hand is, and how far its axis passes from the hand"""
    loc = ML.inverse_transform_location(wm.get_world_transform(), hand); vs = mesh_verts(wm.static_mesh)
    s = [v for v in vs if abs(v.z - loc.z) <= 3.0]
    if not s: return {"hand_at_mesh_z": round(loc.z, 1), "on_handle": False, "why": "her hand is beyond the mesh"}
    ex = max(v.x for v in s) - min(v.x for v in s); ey = max(v.y for v in s) - min(v.y for v in s)
    cx = (max(v.x for v in s) + min(v.x for v in s)) / 2; cy = (max(v.y for v in s) + min(v.y for v in s)) / 2
    off = math.hypot(loc.x - cx, loc.y - cy); zs = [v.z for v in vs]
    return {"hand_at_mesh_z": round(loc.z, 1), "mesh_z": [round(min(zs)), round(max(zs))], "mesh_there_cm": [round(ex, 1), round(ey, 1)], "axis_from_hand_cm": round(off, 1),
            "on_handle": bool(max(ex, ey) < 7.5 and max(ex, ey) < 1.8 * max(min(ex, ey), 0.1) and off < 12.0)}
def step_weapons():
    c = cb(); p = G["pawn"]; out = []; c.set_scripted_only(True)
    wd = G["gen"].get_editor_property("weapons")
    for i, d in enumerate(wd):
        c.select_weapon(i); yield from wait(0.4)
        wm, om = c.get_weapon_mesh(), c.get_off_hand_mesh(); hand = p.mesh.get_socket_location("hand_r")
        held = (wm.get_world_location() - hand).length(); attached = str(wm.get_attach_socket_name())
        grip = grip_check(wm, hand); up = None
        if om.static_mesh and om.is_visible():                       # the shield: its top (mesh +Z, the flat end) above its point
            b = om.static_mesh.get_bounding_box(); tf = om.get_world_transform()
            up = round(ML.transform_location(tf, V(0, 0, b.max.z)).z - ML.transform_location(tf, V(0, 0, b.min.z)).z, 1)
        rel = lambda: ML.inverse_transform_location(p.get_actor_transform(), p.mesh.get_socket_location("hand_r"))
        a0 = rel(); started = c.start_attack(); again = c.start_attack(); moved = 0.0; t0 = now(); mont = False
        while c.is_attacking() and now() - t0 < 5.0:
            moved = max(moved, (rel() - a0).length()); mont = mont or p.mesh.get_anim_instance().is_any_montage_playing(); yield
        secs = now() - t0
        e = {"weapon": str(d.name), "mesh": wm.static_mesh.get_name() if wm.static_mesh else None, "bone": attached, "cm_from_hand": round(held, 1), "shield": om.static_mesh.get_name() if om.static_mesh and om.is_visible() else None,
             "damage": c.get_weapon_damage(), "reach": c.get_weapon_reach(), "attack_started": bool(started), "second_refused": not again, "montage": bool(mont), "hand_moved_cm": round(moved), "attack_seconds": round(secs, 2), "grip": grip, "shield_top_over_point_cm": up}
        e["ok"] = bool(e["mesh"] == d.mesh.get_name() and attached == "hand_r" and held < 130 and started and not again and mont and moved > 25 and 0.3 < secs < 3.0 and (e["shield"] is not None) == (d.off_hand_mesh is not None)
                       and grip["on_handle"] and (up is None or up > 20.0))
        out.append(e); yield from wait(0.3)
    c.select_weapon(0); c.set_scripted_only(False)
    step_result("weapons", len(out) == 3 and all(e["ok"] for e in out), weapons=out)
def step_monsters():
    yield
    gen = G["gen"]; sec = gen.get_section(unreal.IntPoint(0, 0)); ms = start_monsters(); c = cb()
    rooms = [i for i in range(sec.get_num_rooms()) if "unction" not in sec.get_room_kind(i)]
    hp = sum(m.get_max_health() for m in ms) / max(len(ms), 1); dmg = sum(m.get_damage() for m in ms) / max(len(ms), 1); avg = gen.get_average_weapon_damage()
    cov = len(ms) / max(len(rooms), 1)
    ok = len(ms) >= 5 and abs(cov - gen.get_editor_property("monster_coverage")) <= 0.03 and hp < c.get_max_health() * 0.8 and dmg < avg * 0.8 and all(m.get_max_health() > 0 and m.get_damage() > 0 for m in ms)
    step_result("monsters", ok, monsters=len(ms), rooms=len(rooms), coverage=round(cov, 2), wanted=gen.get_editor_property("monster_coverage"), average_hit_points=round(hp, 1), hers=c.get_max_health(),
                average_damage=round(dmg, 1), her_average_blow=round(avg, 1), kinds=sorted({str(m.monster_name) for m in ms}), room_kinds=sorted({sec.get_room_kind(i) for i in range(sec.get_num_rooms())}))
def step_kill(n=3):
    c = cb(); p = G["pawn"]; out = []; c.set_scripted_only(True)
    for k in range(n):
        ms = start_monsters()
        if not ms: out.append({"ok": False, "why": "no live monster"}); break
        l = p.get_actor_location(); m = min(ms, key=lambda q: (q.get_actor_location() - l).length())
        c.revive(False); c.select_weapon(k % 3); name = str(m.monster_name); hp0 = m.get_max_health(); dmg = c.get_weapon_damage()
        stand_by(m, 60.0); yield from wait(0.3)
        k0 = c.kills; blows = 0; steps_ok = True; t0 = now(); hurt0 = c.damage_taken; seen_aggro = False
        while alive(m) and now() - t0 < 60.0:
            h = m.get_health(); n0 = c.hits_landed
            if c.start_attack():
                while c.is_attacking(): yield
                if c.hits_landed > n0:
                    blows += 1
                    if alive(m) and abs((h - m.get_health()) - dmg) > 0.6: steps_ok = False
                else: stand_by(m, 60.0)                 # (it stepped out of reach: close in again)
            seen_aggro = seen_aggro or (alive(m) and m.is_aggro())
            if c.is_dead(): c.revive(False); stand_by(m, 60.0)
            yield
        dead = not alive(m)
        e = {"monster": name, "hit_points": hp0, "weapon": str(c.get_weapon_name()), "damage": dmg, "blows": blows, "blows_needed": math.ceil(hp0 / dmg), "killed": dead, "kills_counted": c.kills - k0, "each_blow_took_the_damage": steps_ok,
             "it_fought_back": seen_aggro, "she_lost": round(c.damage_taken - hurt0), "seconds": round(now() - t0, 1)}
        e["ok"] = bool(dead and c.kills - k0 == 1 and blows == math.ceil(hp0 / dmg) and steps_ok and seen_aggro)
        out.append(e); yield from wait(0.5)
    c.revive(False); c.select_weapon(0); c.set_scripted_only(False)
    step_result("kill", len(out) == n and all(e["ok"] for e in out), fights=out, monsters_killed=G["gen"].get_editor_property("monsters_killed"))
def step_hurt():
    c = cb(); p = G["pawn"]; c.set_scripted_only(True); c.revive(False)
    ms = start_monsters()
    if not ms: step_result("hurt", False, why="no live monster"); return
    l = p.get_actor_location(); m = min(ms, key=lambda q: (q.get_actor_location() - l).length())
    stand_by(m, 40.0); h0 = c.get_health(); a0 = m.attacks_made; l0 = m.hits_landed; t0 = now(); n0 = c.hits_taken
    while now() - t0 < 25.0 and c.hits_taken == n0: yield
    lost = h0 - c.get_health(); t = now() - t0
    ok = lost > 0 and abs(lost - m.get_damage()) < 0.6 and m.hits_landed > l0 and m.is_aggro()
    step_result("hurt", ok, monster=str(m.monster_name), its_damage=m.get_damage(), she_lost=round(lost, 1), its_attacks=m.attacks_made - a0, its_hits=m.hits_landed, seconds=round(t, 1), aggro=bool(m.is_aggro()))
    c.revive(True); c.set_scripted_only(False); yield from wait(0.5)
def step_tier():
    gen = G["gen"]; c = cb(); s = unreal.IntPoint(1, 0)
    made = gen.generate_section_now(s); yield from wait(0.5)
    ms = [m for m in gen.get_monsters() if alive(m) and m.get_editor_property("section").get_editor_property("coord") == s]
    hp = sum(m.get_max_health() for m in ms) / max(len(ms), 1); dmg = sum(m.get_damage() for m in ms) / max(len(ms), 1); avg = gen.get_average_weapon_damage()
    ok = len(ms) >= 5 and 0.75 <= hp / c.get_max_health() <= 1.25 and 0.75 <= dmg / avg <= 1.25
    step_result("tier", ok, section=[1, 0], generated=bool(made) or gen.is_section_generated(s), monsters=len(ms), average_hit_points=round(hp, 1), hers=c.get_max_health(), average_damage=round(dmg, 1), her_average_blow=round(avg, 1),
                rooms=gen.get_section(s).get_num_rooms() if gen.get_section(s) else 0)
def step_death():
    gen = G["gen"]; c = cb(); p = G["pawn"]; c.set_scripted_only(True); c.revive(False)
    sec = gen.get_section(unreal.IntPoint(0, 0)); far = sec.get_room_center(0); p.set_actor_location(V(far.x, far.y, 100.0), False, True); yield from wait(0.3)
    d0 = c.deaths; c.apply_damage(1000.0, None); dead = c.is_dead(); can_attack = c.start_attack(); t0 = now()
    while c.is_dead() and now() - t0 < 12.0: yield
    t = now() - t0; s = gen.get_start_room_center(); l = p.get_actor_location(); back = math.hypot(l.x - s.x, l.y - s.y)
    ok = dead and not can_attack and c.deaths == d0 + 1 and not c.is_dead() and abs(c.get_health() - c.get_max_health()) < 0.5 and back < 200 and abs(t - gen.get_editor_property("respawn_seconds")) < 0.6
    step_result("death", ok, went_down=bool(dead), could_attack_while_down=bool(can_attack), seconds_down=round(t, 1), back_at_the_start_cm=round(back), hit_points=c.get_health())
    c.set_scripted_only(False)
def step_regen():
    gen = G["gen"]; c = cb(); c.revive(True); yield from wait(0.3)
    c.apply_damage(40.0, None); h0 = c.get_health(); yield from wait(gen.get_editor_property("regen_delay") - 1.0); h1 = c.get_health(); yield from wait(4.0); h2 = c.get_health()
    ok = abs(h0 - 60.0) < 0.5 and abs(h1 - h0) < 0.5 and h2 > h1 + 5.0
    step_result("regen", ok, after_the_blow=round(h0, 1), before_the_delay_is_over=round(h1, 1), four_seconds_on=round(h2, 1), per_second=gen.get_editor_property("regen_per_second"))
    c.revive(False)
def step_map():
    gen = G["gen"]; md = gen.get_editor_property("map_data"); m0 = md.get(unreal.IntPoint(0, 0))
    gen.set_map_open(True); yield from wait(0.6); opened = bool(gen.get_editor_property("map_open"))
    # the tactical big map (bTacticalMaps) is an overlay: under it she walks and fights on
    tac = bool(gen.get_editor_property("tactical_maps")); under = {}
    if tac:
        c = cb(); p = G["pawn"]; c.revive(True); c.set_scripted_only(False); k = unreal.Key(); k.set_editor_property("key_name", "LeftMouseButton")
        a = p.get_actor_location(); t0 = now()
        while now() - t0 < 0.8: p.add_movement_input(p.get_actor_forward_vector(), 1.0, True); yield
        n0 = c.attacks_made; c.simulate_key(k, True); yield from wait(0.15); c.simulate_key(k, False); yield from wait(0.3)
        under = {"walked_cm": round((p.get_actor_location() - a).length()), "attacks": c.attacks_made - n0}
        while c.is_attacking(): yield
    gen.set_map_open(False); yield from wait(0.3)
    ok = (bool(gen.get_editor_property("stylized_map")) and m0 is not None and len(m0.rects) > 40 and len(m0.doors) > 20 and len(m0.chests) > 10 and len(m0.torches) > 20 and opened
          and not gen.get_editor_property("map_open") and (not tac or (under["walked_cm"] > 100 and under["attacks"] == 1)))
    step_result("map", ok, stylized=bool(gen.get_editor_property("stylized_map")), tactical=tac, rooms_and_hallways=len(m0.rects) if m0 else 0, doors=len(m0.doors) if m0 else 0, chests=len(m0.chests) if m0 else 0, torches=len(m0.torches) if m0 else 0,
                sections_on_the_map=len(md), opened=opened, with_the_big_map_open=under)

def blow(m, tries=25.0):
    """she strikes until one blow lands on m (the generator: yields); returns nothing, the caller reads the counters"""
    c = cb(); n0 = c.hits_landed; t0 = now(); stand_by(m, 60.0)
    while c.hits_landed == n0 and alive(m) and now() - t0 < tries:
        if c.is_dead(): c.revive(False); stand_by(m, 60.0)
        if not c.is_attacking():
            if (m.get_actor_location() - G["pawn"].get_actor_location()).length() > 330: stand_by(m, 60.0)
            c.start_attack()
        yield
    yield
def step_blood():
    gen = G["gen"]; c = cb(); b = gen.get_blood(); p = G["pawn"]; c.set_scripted_only(True); c.revive(False); c.select_weapon(0)
    ms = start_monsters()
    if b is None or not ms: step_result("blood", False, why="no blood component" if b is None else "no live monster"); return
    m = max(ms, key=lambda q: q.get_health())
    b0, d0, k0 = b.bursts, b.drops_spawned, b.decals_spawned
    yield from blow(m)
    bursts = b.bursts - b0; drops = b.drops_spawned - d0; flying = b.get_active_drops(); sprays = b.get_active_sprays()
    at = b.last_burst_at; near = min((at - m.get_actor_location()).length(), (at - p.get_actor_location()).length())
    yield from wait(2.6)
    landed = b.decals_spawned - k0; marks = b.get_active_decals()
    # she is hit: blood from her
    c.revive(False); ht = c.hits_taken; b1 = b.bursts; t0 = now(); hers = 0; near2 = 1e9
    while now() - t0 < 30.0 and alive(m):
        if c.hits_taken > ht: hers = b.bursts - b1; near2 = (b.last_burst_at - p.get_actor_location()).length(); break
        if (m.get_actor_location() - p.get_actor_location()).length() > 400: stand_by(m, 40.0)
        yield
    ok = bursts >= 1 and drops >= 16 and flying > 0 and sprays > 0 and near < 260 and landed >= 1 and marks >= 1 and hers >= 1 and near2 < 130
    step_result("blood", ok, monster=str(m.monster_name), bursts_on_the_blow=bursts, drops=drops, in_the_air=flying, spray_sprites=sprays, burst_cm_from_the_fight=round(near), decals_after_2_6_s=landed, decals_on_the_floor=marks,
                bursts_when_she_was_hit=hers, that_burst_cm_from_her=round(near2), drop_mesh=str(gen.get_editor_property("blood_drop_mesh").get_name()), decal_materials=len(gen.get_editor_property("blood_decals")))
    c.revive(False); c.set_scripted_only(False)
def step_wounds():
    gen = G["gen"]; c = cb(); b = gen.get_blood(); p = G["pawn"]; c.set_scripted_only(True); c.revive(False); c.select_weapon(0)
    fresh = [m for m in start_monsters() if m.get_num_wounds() == 0]
    if not fresh: step_result("wounds", False, why="no unhurt monster"); return
    # one of a kind that has a second unhurt monster, if there is such a kind (the second must stay as it is)
    kinds = {}
    for m in fresh: kinds.setdefault(str(m.monster_name), []).append(m)
    pairs = [v for v in kinds.values() if len(v) > 1]
    m = max(pairs[0] if pairs else fresh, key=lambda q: q.get_health()); twin = next((q for q in kinds[str(m.monster_name)] if q != m), None)
    hits = 0; locs = []
    for k in range(2):
        if not alive(m) or m.get_health() <= c.get_weapon_damage(): break
        n0 = c.hits_landed; yield from blow(m); hits += c.hits_landed - n0
    mid = m.get_wound_material(); over = m.mesh.get_overlay_material(); n = m.get_num_wounds()
    on_skin = all(m.is_wound_on_skin(i) for i in range(n)); radii = [round(m.get_wound_radius(i), 1) for i in range(n)]
    getv = (getattr(mid, "get_vector_parameter_value", None) or getattr(mid, "k2_get_vector_parameter_value")) if mid else None; gets = (getattr(mid, "get_scalar_parameter_value", None) or getattr(mid, "k2_get_scalar_parameter_value")) if mid else None
    params = [getv("Wound%d" % i) for i in range(n)] if mid else []
    bleed = gets("Bleed") if mid else -1.0; lost = 1.0 - m.get_health() / m.get_max_health()
    d0 = [(m.get_wound_location(i) - m.get_actor_location()).length() for i in range(n)]; a0 = m.get_actor_location()
    yield from wait(1.5)
    d1 = [(m.get_wound_location(i) - m.get_actor_location()).length() for i in range(n)] if alive(m) else d0; moved = (m.get_actor_location() - a0).length() if alive(m) else 0.0
    others = [q for q in G["gen"].get_monsters() if alive(q) and q != m and q.get_health() >= q.get_max_health()]
    clean = all(q.get_num_wounds() == 0 and q.get_wound_material() is None and q.mesh.get_overlay_material() is None for q in others)
    twin_clean = twin is None or (twin.get_num_wounds() == 0 and twin.mesh.get_overlay_material() is None)
    # it dies: a pool under it
    p0 = b.pools_spawned if b else 0; t0 = now()
    while alive(m) and now() - t0 < 40.0: yield from blow(m)
    yield from wait(1.6)
    pools = (b.pools_spawned - p0) if b else 0
    ok = bool(hits >= 1 and n == hits and mid is not None and over == mid and on_skin and all(x.a > 1.0 for x in params) and abs(bleed - lost) < 0.02 and all(x < 260 for x in d0 + d1)
              and len(others) >= 3 and clean and twin_clean and pools == 1)
    step_result("wounds", ok, monster=str(m.monster_name), blows=hits, wounds=n, on_its_skin=on_skin, radius_cm=radii, own_material=mid.get_name() if mid else None, overlay_is_that_material=bool(mid is not None and over == mid),
                parameters_set=[round(x.a, 1) for x in params], bleed=round(bleed, 2), hit_points_lost=round(lost, 2), wound_cm_from_its_middle=[round(x) for x in d0], after_it_moved_cm=round(moved),
                then=[round(x) for x in d1], unhurt_monsters_checked=len(others), none_of_them_has_a_wound_or_overlay=clean, a_second_of_its_kind=str(twin.monster_name) if twin else None, that_one_untouched=twin_clean, pools_when_it_died=pools)
    c.revive(False); c.set_scripted_only(False)
def step_sounds():
    gen = G["gen"]; c = cb(); p = G["pawn"]; c.set_scripted_only(True); out = {}
    cnt = lambda k: gen.get_sound_count(k)
    def total(suffix): return sum(v for k, v in gen.get_sound_counts().items() if str(k).startswith("Monster.") and str(k).endswith(suffix))
    c.revive(True); yield from wait(0.6)
    # her footsteps: running, walking (and nothing of her breath: those sets are gone)
    r0, s0 = cnt("Player.Run"), cnt("Player.Step"); t0 = now()
    while now() - t0 < 2.6: p.add_movement_input(V(1, 0, 0), 1.0); yield
    out["running_steps_in_2_6_s"] = cnt("Player.Run") - r0; yield from wait(0.8); t0 = now()
    while now() - t0 < 2.6: p.add_movement_input(V(-1, 0, 0), 0.45); yield
    out["walking_steps_in_2_6_s"] = cnt("Player.Step") - s0
    out["breath_sets"] = sorted(str(k) for k in gen.get_editor_property("sounds") if "Breath" in str(k)); out["her_sets"] = sorted(str(k) for k in gen.get_editor_property("sounds") if str(k).startswith("Player."))
    ok = out["running_steps_in_2_6_s"] >= 5 and out["walking_steps_in_2_6_s"] >= 3 and not out["breath_sets"] and not hasattr(c, "get_breath_state")
    # her voice
    h0 = cnt("Player.Hurt"); c.apply_damage(5.0, None); yield
    out["hurt_voice"] = cnt("Player.Hurt") - h0; ok = ok and out["hurt_voice"] == 1
    # a door: opening, closing
    sec = gen.get_section(unreal.IntPoint(0, 0)); l = p.get_actor_location()
    doors = [i for i in range(sec.get_num_doors()) if not sec.is_door_cell(i)]
    di = min(doors, key=lambda i: (sec.get_door_location(i) - l).length()); dl = sec.get_door_location(di)
    o0, c0 = cnt("Env.DoorOpen"), cnt("Env.DoorClose")
    what = gen.interact_nearest(V(dl.x, dl.y, l.z), 260.0); yield
    out["door_open"] = cnt("Env.DoorOpen") - o0; yield from wait(1.3)
    gen.interact_nearest(V(dl.x, dl.y, l.z), 260.0); yield
    out["door_close"] = cnt("Env.DoorClose") - c0; out["door"] = what
    ok = ok and out["door_open"] >= 1 and out["door_close"] >= 1
    # the fires: next to a torch its loop plays; back in the middle it does not (when the middle is out of its earshot)
    fires = [(sec.get_fire_point(i), sec.get_fire_kind(i)) for i in range(sec.get_num_fire_points())]
    torches = [q for q, k in fires if k == 0]; s = gen.get_start_room_center()
    tq = max(torches, key=lambda q: (q - s).length()) if torches else None
    if tq is not None:
        best = None
        for k in range(16):
            a = k * math.pi / 8; q = V(tq.x + math.cos(a) * 180, tq.y + math.sin(a) * 180, 100.0)
            n = len(sec.find_path_world(q, s))
            if n > 0 and (best is None or n < best[0]): best = (n, q)
        p.set_actor_location(best[1] if best else V(tq.x, tq.y, 100.0), False, True); yield from wait(0.7)
        loops = gen.get_fire_loops(); out["fire_voices_by_a_torch"] = len(loops); out["nearest_voice_cm_from_that_torch"] = round(min((q - tq).length() for q in loops)) if loops else None
        c.revive(True); yield from wait(0.7)
        loops2 = gen.get_fire_loops(); out["torch_cm_from_the_middle"] = round((tq - s).length()); out["still_playing_from_the_middle"] = any((q - tq).length() < 5 for q in loops2); out["fire_voices_in_the_middle"] = len(loops2)
        ok = ok and 1 <= len(loops) <= gen.get_editor_property("fire_loop_voices") and out["nearest_voice_cm_from_that_torch"] < 5 and ((tq - s).length() < 1500 or not out["still_playing_from_the_middle"])
    out["fires_in_the_start_section"] = {"torch": len(torches), "brazier": sum(1 for q, k in fires if k == 1), "hearth": sum(1 for q, k in fires if k == 2)}
    ok = ok and len(torches) > 20
    # distance: full level beside her, falling to nothing
    lv = {}
    for key, ds in (("Env.Torch", (50, 400, 800, 1200, 1500)), ("Monster.Troll.Roar", (100, 1200, 2400, 3600, 4600)), ("Env.DoorOpen", (100, 1000, 2000, 3000, 3400)), ("Monster.Spider.Step", (100, 600, 1200, 1800, 2000))):
        v = [round(gen.get_sound_level_at(key, d), 3) for d in ds]; lv[key] = dict(zip([str(d) for d in ds], v))
        ok = ok and v[0] == 1.0 and v[-1] <= 0.011 and all(v[i] > v[i + 1] for i in range(len(v) - 1))      # (-40 dB at the end of the falloff; beyond it a sound is not started)
    out["level_at_cm"] = lv; out["flat_sets"] = sorted(str(k) for k, v in gen.get_editor_property("sounds").items() if v.get_editor_property("b2d"))
    # a monster: it notices her and roars, it is hurt, it dies; monsters walk
    ms = [m for m in start_monsters() if m.get_num_wounds() == 0]
    if ms:
        l = p.get_actor_location(); m = min(ms, key=lambda q: (q.get_actor_location() - l).length())
        r0, h0, d0, st0 = total(".Roar"), total(".Hurt"), total(".Death"), total(".Step")
        stand_by(m, 420.0); t0 = now()
        while total(".Roar") == r0 and now() - t0 < 10.0: yield
        out["roar_when_it_noticed_her"] = total(".Roar") - r0
        t0 = now()                                     # it comes to her: its footsteps
        while alive(m) and now() - t0 < 8.0 and (m.get_actor_location() - p.get_actor_location()).length() > 230.0: yield
        out["monster_footsteps"] = total(".Step") - st0
        c.select_weapon(1); t0 = now()                 # (the spear: more than one blow for any of them)
        while alive(m) and now() - t0 < 60.0: yield from blow(m)
        yield from wait(1.2)
        out["monster"] = str(m.monster_name); out["hurt_voices"] = total(".Hurt") - h0; out["death_voices"] = total(".Death") - d0; out["body_falls"] = cnt("Env.BodyFall")
        ok = ok and out["roar_when_it_noticed_her"] >= 1 and out["hurt_voices"] >= 1 and out["death_voices"] == 1 and out["monster_footsteps"] >= 1 and out["body_falls"] >= 1
    else: ok = False; out["monster"] = None
    out["weapon_sounds"] = {k: cnt(k) for k in ("Player.Whoosh", "Player.Attack", "Player.Hit.Sword", "Player.Hit.Spear", "Player.Hit.Axe", "Blood.Splat", "Player.Draw")}
    ok = ok and out["weapon_sounds"]["Player.Whoosh"] >= 1 and out["weapon_sounds"]["Blood.Splat"] >= 1 and (out["weapon_sounds"]["Player.Hit.Spear"] >= 1)
    # a new section: its rumble
    g0 = cnt("Env.Generate"); new = next((s2 for s2 in (unreal.IntPoint(0, -1), unreal.IntPoint(0, 1), unreal.IntPoint(-1, 0), unreal.IntPoint(1, 0)) if not gen.is_section_generated(s2)), None)
    if new is not None: gen.generate_section_now(new); yield from wait(0.5)
    out["generation_rumble"] = cnt("Env.Generate") - g0; ok = ok and out["generation_rumble"] == 1
    out["sound_sets"] = len(gen.get_editor_property("sounds")); out["all_counts"] = {str(k): v for k, v in sorted(gen.get_sound_counts().items(), key=lambda kv: str(kv[0]))}
    step_result("sounds", ok, **out)
    c.revive(True); c.select_weapon(0); c.set_scripted_only(False)

def step_music():
    gen = G["gen"]; c = cb(); p = G["pawn"]; c.set_scripted_only(True); out = {}
    def away(limit=20.0):
        c.revive(True); t0 = now()
        while gen.is_combat_music() and now() - t0 < limit:
            if c.is_dead() or c.get_health() < 40: c.revive(True)
            yield
    def fight():
        ms = [m for m in start_monsters() if m.get_num_wounds() == 0] or start_monsters()
        l = p.get_actor_location(); m = min(ms, key=lambda q: (q.get_actor_location() - l).length())
        stand_by(m, 300.0); t0 = now()
        while not gen.is_combat_music() and now() - t0 < 10.0: yield
        r = {"monster": str(m.monster_name), "seconds_to_the_battle_music": round(now() - t0, 2), "battle": gen.is_combat_music()}
        yield from wait(0.6)
        r.update({"track": gen.get_music_track(), "atmosphere": gen.get_atmosphere_track(), "seconds_into_the_track": round(gen.get_music_position(), 2)})
        c.select_weapon(2); t0 = now()
        while alive(m) and now() - t0 < 60.0: yield from blow(m)
        r["still_battle_at_the_kill"] = gen.is_combat_music(); t0 = now()
        yield from away(); r["seconds_until_wandering_again"] = round(now() - t0, 1)
        return r
    yield from away()
    yield from wait(1.5)
    calm = {"battle": gen.is_combat_music(), "track": gen.get_music_track(), "atmosphere": gen.get_atmosphere_track(), "seconds_into_the_track": round(gen.get_music_position(), 1)}
    n0 = gen.music_shifts
    f1 = yield from fight()
    yield from wait(1.0)
    back = {"battle": gen.is_combat_music(), "track": gen.get_music_track(), "atmosphere": gen.get_atmosphere_track(), "seconds_into_the_track": round(gen.get_music_position(), 1)}
    f2 = yield from fight()
    sets = {str(k): len(v.get_editor_property("sounds")) for k, v in gen.get_editor_property("sounds").items() if str(k).startswith(("Music.", "Atmos."))}
    ok = bool(not calm["battle"] and calm["track"] and calm["atmosphere"] and f1["battle"] and f1["track"] and f1["track"] != calm["track"] and f1["atmosphere"] and f1["atmosphere"] != calm["atmosphere"]
              and f1["seconds_into_the_track"] < 3.0 and f1["still_battle_at_the_kill"] and not back["battle"] and back["track"] == calm["track"] and back["atmosphere"] == calm["atmosphere"]
              and back["seconds_into_the_track"] > calm["seconds_into_the_track"] and f2["battle"] and f2["track"] not in ("", f1["track"], calm["track"]) and gen.music_shifts - n0 == 4
              and sets.get("Music.Explore", 0) >= 1 and sets.get("Music.Combat", 0) >= 2 and sets.get("Atmos.Explore", 0) >= 1 and sets.get("Atmos.Combat", 0) >= 1)
    step_result("music", ok, wandering=calm, first_fight=f1, wandering_again=back, second_fight=f2, shifts=gen.music_shifts - n0, sets=sets, hold_seconds=gen.get_editor_property("combat_music_hold"),
                music_volume=gen.get_editor_property("music_volume"))
    c.revive(True); c.select_weapon(0); c.set_scripted_only(False)

def step_look():
    gen = G["gen"]; p = G["pawn"]; c = cb(); c.set_scripted_only(True); c.revive(True)
    sec = gen.get_section(unreal.IntPoint(0, 0)); home = gen.get_start_room_center(); out = {}
    # flames: beside the nearest torch and the nearest brazier (far effects are asleep)
    for kind, name in ((0, "torch"), (1, "brazier")):
        pts = [sec.get_fire_point(i) for i in range(sec.get_num_fire_points()) if sec.get_fire_kind(i) == kind]
        q = min(pts, key=lambda v: math.hypot(v.x - home.x, v.y - home.y)); d = V(home.x - q.x, home.y - q.y, 0); n = max(d.length(), 1.0)
        p.set_actor_location(V(q.x + d.x / n * 250.0, q.y + d.y / n * 250.0, 100.0), False, True); yield from wait(2.5)
        out[name] = {"at": [round(q.x), round(q.y), round(q.z)], "effects": sec.get_num_effects_near(q, 60.0), "particles": sec.get_effect_particles_near(q, 60.0)}
    p.set_actor_location(V(home.x, home.y, 100.0), False, True)
    # broken walls, in every section there is
    walls = []
    for co in gen.get_section_coords():
        s = gen.get_section(co); cnt = {str(k): v for k, v in s.get_wall_piece_counts().items()}
        rough = {k: v for k, v in cnt.items() if k.startswith("Wall_Rough")}
        walls.append({"section": [co.x, co.y], "rough": rough, "repeats": s.get_wall_repeats(),
                      "ok": bool(s.get_wall_repeats() == 0 and (not rough or (len(rough) >= 4 and max(rough.values()) < 0.4 * sum(rough.values()))))})
    # the cut face under a lid: on the wood slot, with texture coordinates that span it
    lids = []
    for n in ("SM_barrel_01_lid", "SM_barrel_02_lid", "SM_crate_01_lid", "SM_crate_02_lid"):
        m = unreal.load_asset("/Game/Castle/Interactive/Meshes/" + n); slots = [(str(s.material_slot_name), s.material_interface.get_name() if s.material_interface else None) for s in m.static_materials]
        e = {"mesh": n, "slots": slots, "ok": False}
        if len(slots) >= 2 and m.get_num_sections(0) >= 2:
            r = unreal.ProceduralMeshLibrary.get_section_from_static_mesh(m, 0, 1); vs, uv = list(r[0]), list(r[3]); b = m.get_bounding_box()
            e.update({"cut_vertices": len(vs), "cut_z_max": round(max(v.z for v in vs), 2), "cut_spans_cm": [round(max(v.x for v in vs) - min(v.x for v in vs)), round(max(v.y for v in vs) - min(v.y for v in vs))],
                      "uv_span": [round(max(u.x for u in uv) - min(u.x for u in uv), 2), round(max(u.y for u in uv) - min(u.y for u in uv), 2)]})
            e["ok"] = bool(slots[1][0] == "Interior" and slots[1][1] and slots[1][1] != slots[0][1] and e["cut_z_max"] < 0.1 and e["cut_spans_cm"][0] > 0.9 * (b.max.x - b.min.x)
                           and e["cut_spans_cm"][1] > 0.9 * (b.max.y - b.min.y) and min(e["uv_span"]) > 0.3)
        lids.append(e)
    ok = all(out[k]["effects"] >= 1 and out[k]["particles"] > 0 for k in out) and all(x["ok"] for x in walls) and any(x["rough"] for x in walls) and all(x["ok"] for x in lids)
    step_result("look", ok, flames=out, walls=walls, lids=lids)
    c.set_scripted_only(False)

def step_containers():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import container_check as CC; import importlib; importlib.reload(CC)       # (the editor keeps modules: an edited one must be reloaded)
    sec = G["gen"].get_section(unreal.IntPoint(0, 0))
    rows = CC.measure(sec); by = CC.summary(rows); f0 = CC.faults(rows)
    all_closed = all(e["closed"] == e["n"] for e in by.values())
    picks = CC.sample(sec, rows, 4)
    for i in picks: sec.toggle_container(i)
    yield from wait(3.5)
    rows1 = CC.measure(sec); n_open = sum(e["open"] for e in CC.summary(rows1).values()); f1 = CC.faults(rows1)
    for i in picks: sec.toggle_container(i)
    yield from wait(3.5)
    rows2 = CC.measure(sec); by2 = CC.summary(rows2); f2 = CC.faults(rows2)
    closed_again = all(e["closed"] == e["n"] for e in by2.values())
    ok = len(rows) > 0 and all_closed and not f0 and n_open == len(picks) and len(picks) >= 4 and not f1 and closed_again and not f2
    step_result("containers", ok, containers=len(rows), by_body={k: e["n"] for k, e in by.items()}, closed_faults=len(f0), opened=len(picks), fully_open=n_open,
                open_faults=len(f1), closed_again=closed_again, closed_again_faults=len(f2), examples=(f0 + f1 + f2)[:6])

def step_walls():
    """the broken walls (wall_check.py): what is seen of every broken segment of the start section from its room (the wall,
    or the backing through a hole: never beyond the wall), she cannot get into a hole by pushing or jumping, and dropped
    below the floor she is put back where she stood"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import wall_check as WC; import importlib; importlib.reload(WC)       # (the editor keeps modules: an edited one must be reloaded)
    c = cb(); p = G["pawn"]; gen = G["gen"]; c.revive(True); c.set_scripted_only(True); yield from wait(0.5)
    secs = [gen.get_section(unreal.IntPoint(0, 0))]; ign = [p] + list(gen.get_monsters())
    r0 = WC.rays(G["w"], secs, ign, without_backing=True); r0.pop("spots")          # (what was seen before: the holes go right through)
    r = WC.rays(G["w"], secs, ign); ce = WC.cells(G["w"], secs, ign)
    wi = yield from WC.walk_in(G["w"], p, r.pop("spots"), wait, now)
    c.revive(True); fl = yield from WC.fall(gen, p, wait)
    ok = r["segments"] > 0 and r0["leak"] > 0 and r["hole"] > 0 and r["leak"] == 0 and wi["ok"] and fl["ok"] and ce["ok"]
    step_result("walls", ok, **r, without_backing={k: r0[k] for k in ("segments", "rays", "face", "hole", "leak")}, walk_in=wi, fall=fl, cells=ce)
    c.revive(True); c.set_scripted_only(False)

STEPS = {"look": step_look, "containers": step_containers, "music": step_music, "setup": step_setup, "weapons": step_weapons, "monsters": step_monsters, "kill": step_kill, "hurt": step_hurt, "tier": step_tier, "death": step_death, "regen": step_regen, "map": step_map,
         "blood": step_blood, "wounds": step_wounds, "sounds": step_sounds, "walls": step_walls}
def run():
    for s in PLAN:
        name, _, arg = s.partition(":")
        yield from (STEPS[name](int(arg)) if arg else STEPS[name]())
        yield from wait(0.3)
def finish(err=None):
    unreal.unregister_slate_post_tick_callback(G["h"])
    R["error"] = err
    try:
        c = cb(); R.update({"kills": c.kills, "attacks": c.attacks_made, "hits": c.hits_landed, "deaths": c.deaths, "damage_dealt": c.damage_dealt, "damage_taken": c.damage_taken})
    except Exception as e: R["error"] = (err or "") + " / " + str(e)
    os.makedirs(OUT, exist_ok=True); json.dump(R, open(os.path.join(OUT, f"test_{TAG}.json"), "w"), indent=1)
    ok = not R.get("error") and len(R["steps"]) == len(PLAN) and all(s["ok"] for s in R["steps"])
    unreal.log(f"RDCTEST done | {TAG} | {'ok' if ok else 'FAILED'} | " + " | ".join(f"{s['step']} {'ok' if s['ok'] else 'FAILED'}" for s in R["steps"]) + f" | {R.get('error') or ''}")
    G.clear()
def tick(dt):
    try:
        if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is None: finish("PIE ended"); return
        next(G["gen_"])
    except StopIteration: finish()
    except Exception as e:
        import traceback
        unreal.log_error("RDCTEST error: " + str(e) + traceback.format_exc()); finish(str(e))
G["gen_"] = run()
G["h"] = unreal.register_slate_post_tick_callback(tick)
print("combat test armed:", PLAN, TAG)
