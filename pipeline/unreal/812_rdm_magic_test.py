"""random_dungeonmagic_level and random_dungeonmagic_level2 test, run in PIE (813_rdm_magic.ps1 starts PIE, arms this
and waits for "RDMTEST done"); the level is the one PIE plays. Drives the caster's combat component, the keys and the
generator and measures what happens. Plan = comma separated steps:
  setup     the pawn is the level's caster (random_dungeonmagic_level: BP_RDM_CasterCharacter, SK_JRPG_Caster, her one
            weapon the fire spell and nothing in her hands; random_dungeonmagic_level2: BP_RDM2_DarkCasterCharacter,
            SK_JRPG_DarkCaster, the sword in her right hand and the fire spell cast alongside it from her left) in the
            middle of the start section with 100 hit points
  keys      the keys, pressed as on the keyboard (through her player controller): W walks her at her walk speed, Left
            Shift + W runs her at her run speed (both measured from her travel), A / S / D move her the way they should;
            the cast keys (level 1: E and the left mouse button; level 2: E and the right mouse button) each cast one
            bolt, and in level 2 the left mouse button swings the sword (no bolt); her character has no handler for the
            other actions the input context puts on those keys
  cast      9 m from a monster she can see: one cast. The charge's particles burn at her casting hand while she winds up;
            the cast clip plays (her hand moves); at the release a bolt leaves her hand, flies at the spell's speed
            (measured between frames), with particles alive around it, and bursts on that monster: it loses the spell's
            damage, particles burn where it burst, the light is out a moment later; the charge, cast and burst sounds
            are played once each
  nothing   no monster within the spell's reach: she does not turn, the bolt flies straight on and bursts on a wall or at
            the end of its reach, nobody is hurt
  far       a monster 18 m away (beyond the reach): not taken as the target
  kill[:N]  N times: from 9 m from the nearest live monster of the start section she casts until it is dead: each bolt
            that bursts on it takes the spell's damage, the kill is counted, the bolts needed match its hit points
  sword[:N] (level 2) N times: beside the nearest live monster of the start section she cuts with the sword until it is
            dead: every blow takes the sword's damage, the kill is counted
  dual      (level 2) a cast while the sword is drawn: the sword stays in her right hand all through it, the charge burns
            at her left hand, the bolt leaves from it; right after, the sword swings
  tier      the section east of the start is generated: its monsters are on a par with her (hit points ~ hers, damage
            ~ her average blow)
Writes SourceArt/random_dungeon_magic[2]/test_<tag>.json and logs "RDMTEST done | <tag> | ok / FAILED | ...". Args: plan tag"""
import unreal, sys, json, math, os
__keep__ = True
TAG = sys.argv[2] if len(sys.argv) > 2 else "t"
V = unreal.Vector; GS = unreal.GameplayStatics; ML = unreal.MathLibrary
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
assert w is not None, "PIE is not running"
LEVELS = {"random_dungeonmagic_level": {"pawn": "BP_RDM_CasterCharacter_C", "mesh": "SK_JRPG_Caster", "ch": "Caster", "dual": False, "out": "random_dungeon_magic",
                                        "bps": ("/Game/JRPG/Game/BP_JRPGCasterCharacter", "/Game/RandomDungeon/Blueprints/BP_RDM_CasterCharacter"), "cast_keys": ("E", "LeftMouseButton"),
                                        "plan": "setup,keys,cast,nothing,far,kill:3,tier"},
          "random_dungeonmagic_level2": {"pawn": "BP_RDM2_DarkCasterCharacter_C", "mesh": "SK_JRPG_DarkCaster", "ch": "DarkCaster", "dual": True, "out": "random_dungeon_magic2",
                                         "bps": ("/Game/JRPG/Game/BP_JRPGDarkCasterCharacter", "/Game/RandomDungeon/Blueprints/BP_RDM2_DarkCasterCharacter"), "cast_keys": ("E", "RightMouseButton"),
                                         "plan": "setup,keys,cast,dual,nothing,far,kill:2,sword:2,tier"}}
LV = LEVELS[w.get_path_name().split(".")[-1].replace("UEDPIE_0_", "")]
PLAN = [s.strip() for s in (sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "all" else LV["plan"]).split(",") if s.strip()]
OUT = "E:\\code\\claude-ue5\\claude_ue5\\SourceArt\\" + LV["out"]
G = {}; R = {"tag": TAG, "plan": PLAN, "level": w.get_path_name().split(".")[-1], "steps": []}
gen = GS.get_all_actors_of_class(w, unreal.RDDungeonGenerator)[0]
pc = GS.get_player_controller(w, 0); pawn = pc.get_controlled_pawn()
G.update({"w": w, "gen": gen, "pc": pc, "pawn": pawn})
def now(): return GS.get_time_seconds(G["w"])
def cb(): return G["gen"].get_player_combat()
def spell_index(): return next(i for i, d in enumerate(G["gen"].get_editor_property("weapons")) if d.spell)
def spell(): return G["gen"].get_editor_property("weapons")[spell_index()]
def cast(c): return c.start_spell() if LV["dual"] else c.start_attack()
def wait(sec):
    t0 = now()
    while now() - t0 < sec: yield
def step_result(name, ok, **kw):
    R["steps"].append({"step": name, "ok": bool(ok), **kw})
    unreal.log(f"RDMTEST step {name}: {'ok' if ok else 'FAILED'} {json.dumps(kw)[:1800]}")
def alive(m):
    try: return m is not None and unreal.SystemLibrary.is_valid(m) and not m.is_dead()
    except Exception: return False
def start_monsters(): return [m for m in G["gen"].get_monsters() if alive(m) and m.get_editor_property("section").get_editor_property("coord") == unreal.IntPoint(0, 0)]
def v3(v): return [round(v.x), round(v.y), round(v.z)]
def clear(a, b, ignore):
    """no wall between two points (monsters and she do not count)"""
    h = unreal.SystemLibrary.line_trace_single(G["w"], a, b, unreal.TraceTypeQuery.ECC_VISIBILITY, False, ignore, unreal.DrawDebugTrace.NONE, True)
    return h is None or not h.to_tuple()[0]
def stand_off(m, gap):
    """puts her `gap` cm from the monster in its room, where she can see it and the camera has room behind her"""
    p = G["pawn"]; sec = m.get_editor_property("section"); ml = m.get_actor_location(); room = sec.room_at(ml)
    ign = [p] + list(G["gen"].get_monsters()); best = None
    for k in range(32):
        a = k * math.pi / 16; q = V(ml.x + math.cos(a) * gap, ml.y + math.sin(a) * gap, ml.z)
        if room >= 0 and sec.room_at(q) != room: continue
        path = sec.find_path_world(q, ml)
        if not len(path) or math.hypot(path[0].x - q.x, path[0].y - q.y) > 135.0: continue
        if not clear(V(q.x, q.y, 150), V(ml.x, ml.y, ml.z + 20), ign): continue
        best = q; break
    if best is None: return False
    p.set_actor_location(V(best.x, best.y, 100.0), False, True)
    yaw = math.degrees(math.atan2(ml.y - best.y, ml.x - best.x)); p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw), True)
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-12, yaw=yaw))
    return True

def step_setup():
    yield from wait(1.0)
    c = cb(); p = G["pawn"]; s = G["gen"].get_start_room_center(); l = p.get_actor_location()
    wd = list(G["gen"].get_editor_property("weapons")); wm = c.get_weapon_mesh() if c else None
    sk = p.mesh.get_skeletal_mesh_asset() if hasattr(p.mesh, "get_skeletal_mesh_asset") else p.mesh.skeletal_mesh
    if LV["dual"]:
        held = wm is not None and wm.static_mesh is not None and wm.is_visible() and str(wm.get_attach_socket_name()) == "hand_r"
        arms = len(wd) == 2 and not wd[0].spell and wd[1].spell and wd[1].alongside and str(wd[1].spell_bone) == "hand_l" and c.get_weapon_index() == 0 and c.get_alongside_spell() == 1 and held
    else: arms = len(wd) == 1 and wd[0].spell and c.is_spell() and (wm is None or wm.static_mesh is None or not wm.is_visible())
    ok = (c is not None and p.get_class().get_name() == LV["pawn"] and sk.get_name() == LV["mesh"] and abs(c.get_health() - 100.0) < 0.5 and math.hypot(l.x - s.x, l.y - s.y) < 300 and arms)
    step_result("setup", ok, pawn=p.get_class().get_name(), mesh=sk.get_name(), in_her_right_hand=wm.static_mesh.get_name() if wm is not None and wm.static_mesh is not None and wm.is_visible() else None, hit_points=c.get_health() if c else None, weapons=[str(d.name) for d in wd], spell=bool(c.is_spell()) if c else None,
                from_start_room_cm=round(math.hypot(l.x - s.x, l.y - s.y)), title=G["gen"].get_editor_property("player_title"), keys=G["gen"].get_editor_property("controls_hint"))

def step_keys():
    import editor_toolset.toolsets.blueprint as BT
    sub = [s for s in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if "LocalPlayer" in s.get_path_name()][0]
    move = unreal.load_asset("/Game/Input/Actions/IA_Move"); sprint = unreal.load_asset("/Game/Input/Actions/IA_Sprint")
    # (the keys are measured below by pressing them; has_mapping_context of the editor's local player says False in
    # PIE although its mappings are what moves her, so it is only reported)
    imc0 = unreal.load_asset("/Game/Input/IMC_Default"); active = bool(sub.has_mapping_context(imc0))
    maps0 = imc0.get_editor_property("default_key_mappings").get_editor_property("mappings")
    keys = lambda a: sorted(str(m.key.get_editor_property("key_name")) for m in maps0 if m.action == a)
    mk, sk = keys(move), keys(sprint)
    # what her character reacts to (her Blueprint and its parents): no other action may take E or the left mouse button
    handled = set()
    for bp_path in ("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter",) + LV["bps"]:
        bp = unreal.load_asset(bp_path)
        for g in BT.BlueprintTools.list_graphs(bp):
            for n in BT.BlueprintTools.find_nodes(g, ""):
                tid = str(BT.BlueprintTools.get_node_infos([n])[0].type_id)
                if "IA_" in tid: handled.add(tid.split("IA_")[-1])
    imc = unreal.load_asset("/Game/Input/IMC_Default")
    on_spell_keys = sorted({str(m.action.get_name()) for m in imc.get_editor_property("default_key_mappings").get_editor_property("mappings") if str(m.key.get_editor_property("key_name")) in ("E", "LeftMouseButton", "RightMouseButton")})
    clash = [a for a in on_spell_keys if a.replace("IA_", "") in handled]
    # the keys pressed as on the keyboard (through her player controller): W walks her, Left Shift + W runs her, each of
    # A / S / D moves her the way it should (camera to the east: A north, S west, D south), E and the left mouse cast
    p = G["pawn"]; c = cb(); c.revive(True); c.set_scripted_only(False); yield from wait(0.5)
    s = G["gen"].get_start_room_center(); key = lambda n: (lambda k: (k.set_editor_property("key_name", n), k)[1])(unreal.Key())
    G["pc"].set_ignore_look_input(True); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-12, yaw=0))
    speeds = {}; heading = {}
    for name, held in (("walk", ["W"]), ("run", ["LeftShift", "W"]), ("A", ["A"]), ("S", ["S"]), ("D", ["D"])):
        p.set_actor_location(V(s.x, s.y, 100.0), False, True); yield from wait(0.6)
        for k in held: c.simulate_key(key(k), True)
        yield from wait(0.8)
        a = p.get_actor_location(); t0 = now(); yield from wait(1.0); b = p.get_actor_location(); t1 = now()
        for k in reversed(held): c.simulate_key(key(k), False)
        speeds[name] = round(math.hypot(b.x - a.x, b.y - a.y) / max(t1 - t0, 1e-3), 1); heading[name] = round(math.degrees(math.atan2(b.y - a.y, b.x - a.x)))
        yield from wait(0.8)
    casts = {}
    for k in LV["cast_keys"] + (("LeftMouseButton",) if LV["dual"] else ()):
        yield from wait(1.2); n0 = c.attacks_made; b0 = c.bolts_cast
        c.simulate_key(key(k), True); yield from wait(0.2); c.simulate_key(key(k), False)
        t0 = now()
        while c.is_attacking() and now() - t0 < 3.0: yield
        casts[k] = {"attacks": c.attacks_made - n0, "bolts": c.bolts_cast - b0}
    G["pc"].set_ignore_look_input(False)
    walk, runs = [float(x) for x in open(r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_" + LV["ch"].lower() + r"\speeds.txt").read().split()]
    want = {"walk": 0, "run": 0, "A": -90, "S": 180, "D": 90}
    dirs_ok = all(abs((heading[n] - want[n] + 180) % 360 - 180) < 15 for n in want)
    ok = (all(k in mk for k in ("W", "A", "S", "D")) and "LeftShift" in sk and not clash and abs(speeds["walk"] - walk) < 0.15 * walk and abs(speeds["run"] - runs) < 0.15 * runs and dirs_ok
          and all(v["attacks"] == 1 and v["bolts"] == (0 if (LV["dual"] and k == "LeftMouseButton") else 1) for k, v in casts.items()))
    step_result("keys", ok, context_active=active, move_keys=mk, run_keys=sk, actions_on_E_and_left_mouse=on_spell_keys, her_handlers=sorted(handled), clash=clash,
                walk_cm_s=speeds["walk"], her_walk=walk, run_cm_s=speeds["run"], her_run=runs, speeds=speeds, headings_deg=heading, wanted_headings=want, attacks_by_key=casts)

def cast_at(m, gap=900.0, label="cast"):
    """one cast at m from `gap` cm; measures the charge, the flight, the burst"""
    c = cb(); p = G["pawn"]; gen = G["gen"]; c.set_scripted_only(True); c.revive(False)
    if not stand_off(m, gap): return {"ok": False, "why": "no place to stand"}
    yield from wait(0.4)
    d = spell(); hb = str(d.spell_bone)
    hp0 = m.get_health(); n0 = (c.bolts_cast, c.bolts_on_monsters, c.bolts_elsewhere); snd0 = {k: gen.get_sound_count(k) for k in ("Player.Charge.Fire", "Player.Cast.Fire", "Player.Hit.Fire")}
    rel = lambda: ML.inverse_transform_location(p.get_actor_transform(), p.mesh.get_socket_location(hb))
    a0 = rel(); started = cast(c); target = c.get_last_target(); t0 = now()
    charge = 0; moved = 0.0; mont = False; track = []; near_bolt = 0; launched_at = None
    while now() - t0 < 4.0:
        hand = p.mesh.get_socket_location(hb); moved = max(moved, (rel() - a0).length()); mont = mont or p.mesh.get_anim_instance().is_any_montage_playing()
        if c.is_charging(): charge = max(charge, c.get_spell_particles(hand, 120.0)[0])
        bs = c.get_bolts()
        if bs:
            if launched_at is None: launched_at = now() - t0
            track.append((now(), bs[0])); near_bolt = max(near_bolt, c.get_spell_particles(bs[0], 150.0)[0])
        if c.bolts_on_monsters + c.bolts_elsewhere > n0[1] + n0[2]: break
        yield
    burst_at = c.last_burst_at; yield from wait(0.15)
    burst_particles = c.get_spell_particles(burst_at, 300.0)[0]
    sp = [(track[k + 1][1] - track[k][1]).length() / max(track[k + 1][0] - track[k][0], 1e-4) for k in range(len(track) - 1)]
    speed = sorted(sp)[len(sp) // 2] if sp else 0.0
    yield from wait(0.6)
    e = {"monster": str(m.monster_name), "gap_cm": round(gap), "hand": hb, "started": bool(started), "target_is_it": target == m, "montage": bool(mont), "hand_moved_cm": round(moved),
         "charge_particles": charge, "bolt_left_at_s": round(launched_at, 2) if launched_at is not None else None, "bolt_speed_cm_s": round(speed), "spell_speed": d.bolt_speed,
         "particles_round_the_bolt": near_bolt, "on_monster": c.bolts_on_monsters - n0[1], "elsewhere": c.bolts_elsewhere - n0[2], "flown_cm": round(c.last_bolt_flown),
         "it_lost": round(hp0 - m.get_health(), 1) if alive(m) else round(hp0, 1), "damage": d.damage, "burst_particles": burst_particles, "burst_at": v3(burst_at),
         "sounds": {k: gen.get_sound_count(k) - snd0[k] for k in snd0}}
    e["ok"] = bool(started and target == m and mont and moved > 25 and charge > 0 and launched_at is not None and abs(speed - d.bolt_speed) < 0.1 * d.bolt_speed and near_bolt > 0
                   and e["on_monster"] == 1 and abs(min(hp0, d.damage) - (hp0 - (m.get_health() if alive(m) else 0.0))) < 0.6 and burst_particles > 0 and all(v == 1 for v in e["sounds"].values()))
    c.set_scripted_only(False)
    return e

def step_cast():
    ms = start_monsters(); p = G["pawn"]; l = p.get_actor_location(); e = None
    for m in sorted(ms, key=lambda q: (q.get_actor_location() - l).length())[:6]:
        g = cast_at(m)
        try:
            while True: next(g); yield
        except StopIteration as s: e = s.value
        if e.get("why") != "no place to stand": break
    e = e or {"ok": False, "why": "no monster"}
    step_result("cast", e.pop("ok"), **e)

def step_nothing():
    c = cb(); p = G["pawn"]; gen = G["gen"]; c.set_scripted_only(True); c.revive(False)
    sec = gen.get_section(unreal.IntPoint(0, 0)); d = spell(); spot = None
    for i in range(sec.get_num_rooms()):
        q = sec.get_room_center(i)
        if all((m.get_actor_location() - q).length() > d.reach + 400 for m in gen.get_monsters() if alive(m)): spot = q; break
    if spot is None: step_result("nothing", False, why="no room without a monster within reach"); return
    p.set_actor_location(V(spot.x, spot.y, 100.0), False, True); p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=37.0), True); yield from wait(0.5)
    yaw0 = p.get_actor_rotation().yaw; n0 = (c.bolts_on_monsters, c.bolts_elsewhere, c.hits_landed); dmg0 = c.damage_dealt
    cast(c); target = c.get_last_target(); t0 = now(); f = p.get_actor_forward_vector(); first = None
    while now() - t0 < 4.0 and c.bolts_elsewhere == n0[1] and c.bolts_on_monsters == n0[0]:
        bs = c.get_bolts()
        if bs and first is None: first = bs[0]
        yield
    burst = c.last_burst_at; frm = c.last_bolt_from
    dev = 0.0
    if first is not None:
        dv = V(burst.x - frm.x, burst.y - frm.y, 0).normal(); dev = math.degrees(math.acos(max(-1.0, min(1.0, dv.x * f.x + dv.y * f.y))))
    ok = target is None and abs(p.get_actor_rotation().yaw - yaw0) < 1.0 and c.bolts_elsewhere == n0[1] + 1 and c.damage_dealt == dmg0 and dev < 5.0 and c.last_bolt_flown <= d.reach + 160
    step_result("nothing", ok, target=None if target is None else target.get_name(), turned_deg=round(p.get_actor_rotation().yaw - yaw0, 1), off_her_heading_deg=round(dev, 1), flown_cm=round(c.last_bolt_flown), reach=d.reach,
                damage_dealt=round(c.damage_dealt - dmg0, 1))
    c.set_scripted_only(False); yield from wait(1.0)

def step_far():
    c = cb(); p = G["pawn"]; gen = G["gen"]; c.set_scripted_only(True); d = spell(); done = None
    for m in start_monsters():
        sec = m.get_editor_property("section"); ml = m.get_actor_location()
        for k in range(16):
            a = k * math.pi / 8; q = V(ml.x + math.cos(a) * 1800, ml.y + math.sin(a) * 1800, ml.z)
            pth = sec.find_path_world(q, ml)
            if len(pth) and math.hypot(pth[0].x - q.x, pth[0].y - q.y) < 135 and all((o.get_actor_location() - q).length() > d.reach + 300 for o in gen.get_monsters() if alive(o) and o != m):
                done = (m, q); break
        if done: break
    if not done: step_result("far", False, why="no place 18 m from a monster with none nearer"); c.set_scripted_only(False); return
    m, q = done; p.set_actor_location(V(q.x, q.y, 100.0), False, True)
    p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=math.degrees(math.atan2(m.get_actor_location().y - q.y, m.get_actor_location().x - q.x))), True); yield from wait(0.4)
    dist = (m.get_actor_location() - p.get_actor_location()).length(); cast(c); target = c.get_last_target()
    while c.is_attacking(): yield
    step_result("far", target is None and dist > d.reach + 200, monster=str(m.monster_name), distance_cm=round(dist), reach=d.reach, target=None if target is None else target.get_name())
    c.set_scripted_only(False); yield from wait(1.5)

def step_kill(n=3):
    c = cb(); p = G["pawn"]; out = []; d = spell()
    for k in range(n):
        ms = start_monsters()
        if not ms: out.append({"ok": False, "why": "no live monster"}); break
        l = p.get_actor_location(); placed = None
        for m in sorted(ms, key=lambda q: (q.get_actor_location() - l).length())[:8]:
            c.revive(False)
            if stand_off(m, 900.0): placed = m; break
        if placed is None: out.append({"ok": False, "why": "no place to stand"}); break
        m = placed; c.set_scripted_only(True); yield from wait(0.3)
        name = str(m.monster_name); hp0 = m.get_max_health(); k0 = c.kills; casts = 0; direct = 0; each_ok = True; t0 = now(); hurt0 = c.damage_taken
        while alive(m) and now() - t0 < 40.0:
            if not c.is_attacking():
                h = m.get_health(); n0 = c.bolts_on_monsters; tg = None
                if cast(c):
                    casts += 1; tg = c.get_last_target()
                    while c.is_attacking() or len(c.get_bolts()) > 0: yield
                    if c.bolts_on_monsters > n0 and tg == m:
                        direct += 1
                        lost = h - (m.get_health() if alive(m) else 0.0)
                        if abs(lost - min(h, d.damage)) > 0.6 and abs(lost - min(h, d.damage * 1.5)) > 0.6: each_ok = False     # (a splash from a burst on its neighbour may add half)
            if c.is_dead(): c.revive(False)
            yield
        dead = not alive(m)
        e = {"monster": name, "hit_points": hp0, "casts": casts, "bolts_on_it": direct, "bolts_needed": math.ceil(hp0 / d.damage), "killed": dead, "kills_counted": c.kills - k0, "each_bolt_took_the_damage": each_ok,
             "she_lost": round(c.damage_taken - hurt0), "seconds": round(now() - t0, 1)}
        e["ok"] = bool(dead and c.kills - k0 >= 1 and each_ok and direct <= math.ceil(hp0 / d.damage))        # (a burst may kill a neighbour too)
        out.append(e); c.set_scripted_only(False); yield from wait(0.6)
    c.revive(True)
    step_result("kill", len(out) == n and all(e["ok"] for e in out), fights=out, monsters_killed=G["gen"].get_editor_property("monsters_killed"))

def step_sword(n=2):
    """the sword: beside the monster, cut until it is down"""
    c = cb(); p = G["pawn"]; out = []; c.set_scripted_only(True); d = G["gen"].get_editor_property("weapons")[0]
    for k in range(n):
        ms = start_monsters()
        if not ms: out.append({"ok": False, "why": "no live monster"}); break
        l = p.get_actor_location(); placed = None
        for m in sorted(ms, key=lambda q: (q.get_actor_location() - l).length())[:8]:
            c.revive(False)
            if stand_off(m, m.capsule_component.get_scaled_capsule_radius() + 110.0): placed = m; break
        if placed is None: out.append({"ok": False, "why": "no place to stand"}); break
        m = placed; yield from wait(0.3)
        name = str(m.monster_name); hp0 = m.get_max_health(); k0 = c.kills; blows = 0; each = True; t0 = now(); b0 = c.bolts_cast
        while alive(m) and now() - t0 < 40.0:
            h = m.get_health(); n0 = c.hits_landed
            if c.start_attack():
                while c.is_attacking(): yield
                if c.hits_landed > n0:
                    blows += 1
                    if alive(m) and abs((h - m.get_health()) - d.damage) > 0.6: each = False
                else: stand_off(m, m.capsule_component.get_scaled_capsule_radius() + 110.0)
            if c.is_dead(): c.revive(False)
            yield
        dead = not alive(m)
        e = {"monster": name, "hit_points": hp0, "weapon": str(d.name), "damage": d.damage, "blows": blows, "blows_needed": math.ceil(hp0 / d.damage), "killed": dead, "kills_counted": c.kills - k0,
             "each_blow_took_the_damage": each, "bolts_cast": c.bolts_cast - b0, "seconds": round(now() - t0, 1)}
        e["ok"] = bool(dead and c.kills - k0 >= 1 and each and blows <= math.ceil(hp0 / d.damage) and c.bolts_cast == b0)
        out.append(e); yield from wait(0.6)
    c.revive(True); c.set_scripted_only(False)
    step_result("sword", len(out) == n and all(e["ok"] for e in out), fights=out)

def step_dual():
    """a cast with the sword drawn: the sword stays in her right hand, the fire comes from the left; then a cut"""
    c = cb(); p = G["pawn"]; c.set_scripted_only(True); c.revive(True); yield from wait(0.6)
    wm = c.get_weapon_mesh(); n0 = (c.attacks_made, c.bolts_cast); d = spell(); held = True; charge_l = 0; charge_r = 0; idx = []
    ok_cast = c.start_spell(); t0 = now()
    while now() - t0 < 2.0:
        held = held and wm.is_visible() and wm.static_mesh is not None and str(wm.get_attach_socket_name()) == "hand_r" and (wm.get_world_location() - p.mesh.get_socket_location("hand_r")).length() < 130.0
        if c.is_charging():
            charge_l = max(charge_l, c.get_spell_particles(p.mesh.get_socket_location("hand_l"), 90.0)[0]); charge_r = max(charge_r, c.get_spell_particles(p.mesh.get_socket_location("hand_r"), 40.0)[0])
        if c.is_attacking(): idx.append(c.get_attack_index())
        if not c.is_attacking() and c.bolts_cast > n0[1]: break
        yield
    frm = c.last_bolt_from; dl = (frm - p.mesh.get_socket_location("hand_l")).length()
    yield from wait(0.3)
    ok_cut = c.start_attack(); cut_idx = c.get_attack_index(); b1 = c.bolts_cast
    while c.is_attacking(): yield
    ok = (ok_cast and held and charge_l > 0 and set(idx) == {spell_index()} and c.bolts_cast >= n0[1] + 1 and ok_cut and cut_idx == 0 and c.bolts_cast == b1 and c.get_weapon_index() == 0)
    step_result("dual", ok, cast_started=bool(ok_cast), sword_held_all_through=held, charge_particles_left_hand=charge_l, attack_weapon_while_casting=sorted(set(idx)),
                bolt_from_left_hand_cm=round(dl), cut_started=bool(ok_cut), cut_weapon=cut_idx, bolts_by_the_cut=c.bolts_cast - b1)
    c.set_scripted_only(False)

def step_tier():
    gen = G["gen"]; c = cb(); s = unreal.IntPoint(1, 0)
    made = gen.generate_section_now(s); yield from wait(0.5)
    ms = [m for m in gen.get_monsters() if alive(m) and m.get_editor_property("section").get_editor_property("coord") == s]
    hp = sum(m.get_max_health() for m in ms) / max(len(ms), 1); dmg = sum(m.get_damage() for m in ms) / max(len(ms), 1); avg = gen.get_average_weapon_damage()
    ok = len(ms) >= 5 and 0.75 <= hp / c.get_max_health() <= 1.25 and 0.75 <= dmg / avg <= 1.25
    step_result("tier", ok, section=[1, 0], monsters=len(ms), average_hit_points=round(hp, 1), hers=c.get_max_health(), average_damage=round(dmg, 1), spell_damage=round(avg, 1))

STEPS = {"setup": step_setup, "keys": step_keys, "cast": step_cast, "nothing": step_nothing, "far": step_far, "kill": step_kill, "tier": step_tier, "sword": step_sword, "dual": step_dual}
def run():
    for s in PLAN:
        name, _, arg = s.partition(":")
        yield from (STEPS[name](int(arg)) if arg else STEPS[name]())
        yield from wait(0.3)
def finish(err=None):
    unreal.unregister_slate_post_tick_callback(G["h"])
    R["error"] = err
    try:
        c = cb(); R.update({"kills": c.kills, "casts": c.attacks_made, "bolts": c.bolts_cast, "bolts_on_monsters": c.bolts_on_monsters, "bolts_elsewhere": c.bolts_elsewhere, "deaths": c.deaths,
                            "damage_dealt": c.damage_dealt, "damage_taken": c.damage_taken})
        c.set_scripted_only(False)
    except Exception as e: R["error"] = (err or "") + " / " + str(e)
    os.makedirs(OUT, exist_ok=True); json.dump(R, open(os.path.join(OUT, f"test_{TAG}.json"), "w"), indent=1)
    ok = not R.get("error") and len(R["steps"]) == len(PLAN) and all(s["ok"] for s in R["steps"])
    unreal.log(f"RDMTEST done | {TAG} | {'ok' if ok else 'FAILED'} | " + " | ".join(f"{s['step']} {'ok' if s['ok'] else 'FAILED'}" for s in R["steps"]) + f" | {R.get('error') or ''}")
    G.clear()
def tick(dt):
    try:
        if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is None: finish("PIE ended"); return
        next(G["gen_"])
    except StopIteration: finish()
    except Exception as e:
        import traceback
        unreal.log_error("RDMTEST error: " + str(e) + traceback.format_exc()); finish(str(e))
G["gen_"] = run()
G["h"] = unreal.register_slate_post_tick_callback(tick)
print("magic test armed:", PLAN, TAG)
