"""random_dungeoncombat_level combat test, run in PIE (793_rdc_combat.ps1 starts PIE, arms this and waits for
"RDCTEST done"). Drives the player's combat component and the generator directly (the keys do the same calls) and
checks what happens. Plan = comma separated steps:
  setup     she stands in the middle of the start section with 100 hit points and the first weapon in her hand
  weapons   each of the three weapons: its mesh in her right hand (shield on her left arm where it has one), an attack
            plays over her locomotion (her hand moves, the attack ends), the damage / reach figures
  monsters  the start section: share of rooms with a monster (30% wanted), their average hit points and damage against
            hers (must be lower)
  kill[:N]  N times (default 3, a different weapon each time): next to the nearest live monster of the start section,
            she attacks until it is dead: every blow takes the weapon's damage, the kill is counted
  hurt      she stands by a monster without fighting back: it attacks and she loses its damage in hit points
  tier      the section east of the start is generated: its monsters are on a par with her (average hit points ~ hers,
            average damage ~ her average blow)
  death     she is brought to 0: she is down, and after the respawn time stands in the middle with full hit points
  regen     hurt and left alone, her hit points come back
  map       the stylised maps have their data (chests, torches) and M opens / closes the big map
Writes SourceArt/random_dungeon_combat/test_<tag>.json and logs "RDCTEST done | <tag> | ok / FAILED | ...". Args: plan tag"""
import unreal, sys, json, math, os
__keep__ = True
PLAN = [s.strip() for s in (sys.argv[1] if len(sys.argv) > 1 else "setup,weapons,monsters,kill,hurt,tier,death,regen,map").split(",") if s.strip()]
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
    unreal.log(f"RDCTEST step {name}: {'ok' if ok else 'FAILED'} {json.dumps(kw)[:400]}")
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
        if sec.room_at(q) == sec.room_at(ml) and sec.room_at(q) >= 0 and len(path) > 0 and (best is None or len(path) < best[0]): best = (len(path), q)
    q = best[1] if best else V(ml.x + gap + rad + 36, ml.y, ml.z)
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
def step_weapons():
    c = cb(); p = G["pawn"]; out = []; c.set_scripted_only(True)
    wd = G["gen"].get_editor_property("weapons")
    for i, d in enumerate(wd):
        c.select_weapon(i); yield from wait(0.4)
        wm, om = c.get_weapon_mesh(), c.get_off_hand_mesh(); hand = p.mesh.get_socket_location("hand_r")
        held = (wm.get_world_location() - hand).length(); attached = str(wm.get_attach_socket_name())
        rel = lambda: ML.inverse_transform_location(p.get_actor_transform(), p.mesh.get_socket_location("hand_r"))
        a0 = rel(); started = c.start_attack(); again = c.start_attack(); moved = 0.0; t0 = now(); mont = False
        while c.is_attacking() and now() - t0 < 5.0:
            moved = max(moved, (rel() - a0).length()); mont = mont or p.mesh.get_anim_instance().is_any_montage_playing(); yield
        secs = now() - t0
        e = {"weapon": str(d.name), "mesh": wm.static_mesh.get_name() if wm.static_mesh else None, "bone": attached, "cm_from_hand": round(held, 1), "shield": om.static_mesh.get_name() if om.static_mesh and om.is_visible() else None,
             "damage": c.get_weapon_damage(), "reach": c.get_weapon_reach(), "attack_started": bool(started), "second_refused": not again, "montage": bool(mont), "hand_moved_cm": round(moved), "attack_seconds": round(secs, 2)}
        e["ok"] = bool(e["mesh"] == d.mesh.get_name() and attached == "hand_r" and held < 130 and started and not again and mont and moved > 25 and 0.3 < secs < 3.0 and (e["shield"] is not None) == (d.off_hand_mesh is not None))
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
    gen.set_map_open(True); yield from wait(0.6); opened = bool(gen.get_editor_property("map_open")); gen.set_map_open(False); yield from wait(0.3)
    ok = bool(gen.get_editor_property("stylized_map")) and m0 is not None and len(m0.rects) > 40 and len(m0.doors) > 20 and len(m0.chests) > 10 and len(m0.torches) > 20 and opened and not gen.get_editor_property("map_open")
    step_result("map", ok, stylized=bool(gen.get_editor_property("stylized_map")), rooms_and_hallways=len(m0.rects) if m0 else 0, doors=len(m0.doors) if m0 else 0, chests=len(m0.chests) if m0 else 0, torches=len(m0.torches) if m0 else 0,
                sections_on_the_map=len(md), opened=opened)

STEPS = {"setup": step_setup, "weapons": step_weapons, "monsters": step_monsters, "kill": step_kill, "hurt": step_hurt, "tier": step_tier, "death": step_death, "regen": step_regen, "map": step_map}
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
