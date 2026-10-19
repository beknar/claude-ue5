"""random_dungeonmagic_level4 test (play-in-editor; 828 starts it). Steps (plan, comma separated):
  select    (the menu level random_dungeonmagic_level4_select) the Warrior is shown first and only her figure (with her
            weapons) is seen; the turntable turns at its rate and she with it; D / the right arrow / the D-pad show the next
            hero, A / the left arrow the one before, round the end; the shown hero's figure is the only one seen; Enter
            on the Rogue opens random_dungeonmagic_level4?Hero=Rogue, where her pawn is the Rogue's and the generator
            plays her
  heroes    (the dungeon) each hero in turn (SwitchHero): her pawn class and mesh, hit points and mana (full), her
            weapons (names as heroes.json; the first drawn, its meshes in her hands), each weapon's damage with her bonus
            (melee for blows, ranged for a crossbow's bolts, none for magic), her inventory lists her weapons, her
            controls list the inventory key, B rolls for the Rogue only
  inventory I opens it and the game stands still (no game time passes over a second); S moves the cursor; Enter
            wields the Rogue's crossbow (in her hands, the daggers on her thighs) and drinks a potion under it (hit points
            up by its share); Tab closes it and time goes on; the gamepad's Start opens it, B closes it; the Warlock's
            fire is 'always at hand' (Enter does not draw it)
  mana      the Mage casts fire (left mouse): her mana drops by its cost; dark fire (2) by its own; with less than a
            cast's cost the cast is refused (no attack, counted, the message says so); from 0 her mana comes back at her
            rate; the Warlock's fire (E) takes its cost from her 60
  bonus     blows and bolts on a monster of the start section: the Warrior's sword takes its damage + 30 %, the
            Warlock's the sword's own, the Rogue's crossbow bolt its damage + 30 %, her daggers their own
  loot      every container of the start section opened once gives one item (the one LootOf names) into her inventory,
            F by a closed chest too; opened again it gives nothing; the containers of a section generated in play give
            nothing; over 20000 containers the items come in the shares of their rarity
  potions   each healing potion restores its share of her hit points, each mana potion (the Mage) its share of her mana; a
            mana potion is refused by the Warrior (no mana) and a healing potion at full hit points
  food      bread restores 1 % of her hit points a second for 10 s and stops; the steak 9 %; two foods add up
  speed     running (W, run mode) she reaches her speed; under a large speed potion 30 % more, measured from where she
            goes; the bonus ends after its 30 s; in an attack she is slowed under it too
  noregen   hurt and left alone for 9 s her hit points stay where they are (the magic levels' come back after 6 s)
  menufirst (828 starts play on random_dungeonmagic_level4 itself with rd.HeroMenu 1; first in a plan, before menuui and
            select) the dungeon played without ?Hero= opened its menu (831's MenuLevel): play is in the menu level, the
            turntable shows the Warrior, there is no generator; select then goes on from there
  menuui    (the menu, before select) each hero's card drawn with the painted pieces (830): board, framed bars and fills,
            dividers, plates, arrows, a slot with the picture of each of her weapons and spells (the HUD's GetArtDrawn);
            a HighResShot of each card
  map       (the dungeon) M opens the big map in the minimap's painted style (board, plaque, compass, the key's divider;
            no minimap ring); she walks a second along a clear line with it open; M closes it and the ring is back;
            HighResShots
  ui        (the dungeon) each hero's status panel with the painted board, bars (mana only when she has it), weapon slots
            with her weapons' pictures, the minimap's ring; the effect chips' pictures; FOUND on the plaque with the item's
            picture; the inventory's board, dividers, plate and pictures; HighResShots of each
Writes SourceArt/random_dungeon_magic4/test_<tag>.json and logs "RDM4TEST done | <tag> | ok / FAILED | ...". Args: plan tag"""
import unreal, sys, json, math, os, time
__keep__ = True
TAG = sys.argv[2] if len(sys.argv) > 2 else "t"
V = unreal.Vector; GS = unreal.GameplayStatics
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon_magic4"
HJ = json.load(open(SA + r"\heroes.json")); IJ = json.load(open(SA + r"\items.json"))
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
G = {"w": UES.get_game_world()}
assert G["w"] is not None, "PIE is not running"
PLAN = [s.strip() for s in (sys.argv[1] if len(sys.argv) > 1 else "heroes,inventory,mana,bonus,loot,potions,food,speed,noregen").split(",") if s.strip()]
R = {"tag": TAG, "plan": PLAN, "level": G["w"].get_path_name().split(".")[-1], "steps": []}
def refresh():
    """the game world and what the steps use (again after the menu opened the dungeon)"""
    w = UES.get_game_world(); G["w"] = w
    if w is None: return False
    gens = GS.get_all_actors_of_class(w, unreal.RDDungeonGenerator)
    G["gen"] = gens[0] if gens else None
    sels = GS.get_all_actors_of_class(w, unreal.RDHeroSelect); G["sel"] = sels[0] if sels else None
    G["pc"] = GS.get_player_controller(w, 0); G["pawn"] = G["pc"].get_controlled_pawn() if G["pc"] else None
    return True
refresh()
def now(): return GS.get_time_seconds(G["w"])
def cb(): return G["gen"].get_player_combat()
def key(n): k = unreal.Key(); k.set_editor_property("key_name", n); return k
def wait(sec):
    t0 = now()
    while now() - t0 < sec: yield
def rwait(sec):
    """real seconds (the game's clock stands while it is paused)"""
    t0 = time.time()
    while time.time() - t0 < sec: yield
def press(name, hold=0.12, sim=None):
    sim = sim or (lambda k, d: cb().simulate_key(k, d))
    sim(key(name), True); yield from rwait(hold); sim(key(name), False); yield from rwait(0.1)
def step_result(name, ok, **kw):
    R["steps"].append({"step": name, "ok": bool(ok), **kw})
    unreal.log(f"RDM4TEST step {name}: {'ok' if ok else 'FAILED'} {json.dumps(kw)[:1800]}")
def alive(m):
    try: return m is not None and unreal.SystemLibrary.is_valid(m) and not m.is_dead()
    except Exception: return False
def start_monsters(): return [m for m in G["gen"].get_monsters() if alive(m) and m.get_editor_property("section").get_editor_property("coord") == unreal.IntPoint(0, 0)]
def hero_json(n): return next(h for h in HJ["heroes"] if h["name"] == n)
def switch(name):
    """another hero takes her place; she gets her combat component the next tick"""
    ok = G["gen"].switch_hero(name)
    yield from wait(0.6)
    refresh(); c = cb()
    if c: c.set_scripted_only(False)
    return ok and c is not None and str(G["gen"].current_hero) == name
def clear(a, b, ignore):
    h = unreal.SystemLibrary.line_trace_single(G["w"], a, b, unreal.TraceTypeQuery.ECC_VISIBILITY, False, ignore, unreal.DrawDebugTrace.NONE, True)
    return h is None or not h.to_tuple()[0]
def stand_off(m, gap):
    """her `gap` cm from the monster in its room, where she sees it (812's)"""
    p = G["pawn"]; sec = m.get_editor_property("section"); ml = m.get_actor_location(); room = sec.room_at(ml)
    ign = [p] + list(G["gen"].get_monsters())
    for k in range(32):
        a = k * math.pi / 16; q = V(ml.x + math.cos(a) * gap, ml.y + math.sin(a) * gap, ml.z)
        if room >= 0 and sec.room_at(q) != room: continue
        path = sec.find_path_world(q, ml)
        if not len(path) or math.hypot(path[0].x - q.x, path[0].y - q.y) > 135.0: continue
        if not clear(V(q.x, q.y, 150), V(ml.x, ml.y, ml.z + 20), ign): continue
        p.set_actor_location(V(q.x, q.y, 100.0), False, True)
        yaw = math.degrees(math.atan2(ml.y - q.y, ml.x - q.x)); p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw), True)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-12, yaw=yaw))
        return True
    return False
def quiet(on):
    """the monsters do not notice her (a step that measures her hit points or her running: a blow or a monster in the
    way spoils it); their aggro distance back afterwards"""
    g = G["gen"]
    # (and one already after her gives up: LoseDistance 1 cm)
    if on:
        if "aggro" not in G: G["aggro"] = (g.get_editor_property("aggro_distance"), g.get_editor_property("lose_distance"))
        g.set_editor_property("aggro_distance", 0.0); g.set_editor_property("lose_distance", 1.0)
    elif "aggro" in G: a_, l_ = G.pop("aggro"); g.set_editor_property("aggro_distance", a_); g.set_editor_property("lose_distance", l_)
def weapon_bonus(d, h):
    return h["melee_bonus"] if not d.spell else (h["ranged_bonus"] if d.bolt_mesh else 0.0)

# ------------------------------------------------------------------------------------------------ the menu
def step_select():
    s = G["sel"]; assert s, "open random_dungeonmagic_level4_select for the select step"
    sim = lambda k, d: G["sel"].simulate_key(k, d)
    yield from wait(0.5)
    names = [str(h.name) for h in s.heroes]
    shown = lambda: [s.is_figure_shown(i) for i in range(len(names))]
    first = (str(s.get_hero_name()), shown(), [len(f.get_attached_actors()) for f in s.figures])
    # the turntable turns, and she with it
    t0, a0, y0 = now(), s.get_turned(), s.figures[0].get_actor_rotation().yaw
    yield from wait(2.0)
    dt, da = now() - t0, s.get_turned() - a0
    yf, yp = s.figures[0].get_actor_rotation().yaw, s.turntable.get_actor_rotation().yaw
    turn = {"rate": round(da / dt, 1), "want": s.turn_rate, "figure_yaw_moved": round((yf - y0) % 360.0, 1), "with_turntable": abs(((yf - yp) + 180) % 360 - 180) < 0.5}
    seq = []
    for k, want in (("D", 1), ("Right", 2), ("A", 1), ("Left", 0), ("Left", 3), ("Gamepad_DPad_Right", 0), ("D", 1), ("D", 2), ("D", 3)):
        yield from press(k, sim=sim); yield from wait(0.1)
        seq.append({"key": k, "index": s.get_index(), "want": want, "only_that_one_seen": shown() == [i == want for i in range(len(names))]})
    keys_ok = all(e["index"] == e["want"] and e["only_that_one_seen"] for e in seq)
    pick = str(s.get_hero_name())
    # Enter: the menu opens the dungeon a tick later and is gone with its world (the key is not let go: there is no menu then)
    sim(key("Enter"), True)
    opened = ""
    G["traveling"] = True; t0 = time.time(); arrived = False
    while time.time() - t0 < 60:
        yield
        try:
            if unreal.SystemLibrary.is_valid(s) and s.opened: opened = s.opened
        except Exception: pass
        w = UES.get_game_world()
        if w is not None and w.get_path_name().endswith("random_dungeonmagic_level4") and refresh() and G["gen"] is not None and G["pawn"] is not None and G["gen"].get_player_combat():
            arrived = True; break
    G["traveling"] = False
    if arrived: yield from wait(0.5)
    hero = str(G["gen"].current_hero) if arrived else None
    pawn = G["pawn"].get_class().get_name() if arrived else None
    want_pawn = os.path.basename(hero_json("Rogue")["pawn"]) + "_C"
    ok = (first[0] == "Warrior" and first[1] == [True, False, False, False] and abs(turn["rate"] - turn["want"]) < 1.0 and turn["with_turntable"] and keys_ok
          and pick == "Rogue" and opened.endswith("random_dungeonmagic_level4?Hero=Rogue") and arrived and hero == "Rogue" and pawn == want_pawn)
    step_result("select", ok, heroes=names, first=first[0], first_seen=first[1], weapons_on_figures=first[2], turn=turn, keys=seq, picked=pick, opened=opened,
                dungeon_hero=hero, pawn=pawn, want_pawn=want_pawn)

# ------------------------------------------------------------------------------------------------ the dungeon
def step_heroes():
    out = []; allok = True
    for h in HJ["heroes"]:
        sw = yield from switch(h["name"])
        c = cb(); p = G["pawn"]; g = G["gen"]
        sk = p.mesh.get_skeletal_mesh_asset() if hasattr(p.mesh, "get_skeletal_mesh_asset") else p.mesh.skeletal_mesh
        wd = list(g.get_editor_property("weapons"))
        names = [str(d.name) for d in wd]
        dmg = [{"weapon": str(d.name), "is": round(c.get_damage_of(i), 2), "want": round(d.damage * (1.0 + weapon_bonus(d, h)), 2)} for i, d in enumerate(wd)]
        wm, om = c.get_weapon_mesh(), c.get_off_hand_mesh()
        held = {"right": wm.static_mesh.get_name() if wm and wm.static_mesh and wm.is_visible() else None, "left": om.static_mesh.get_name() if om and om.static_mesh and om.is_visible() else None}
        hands_ok = (held["right"] == (wd[0].mesh.get_name() if wd[0].mesh else None)) and (held["left"] == (wd[0].off_hand_mesh.get_name() if wd[0].off_hand_mesh else None))
        r0 = c.rolls; yield from press("B"); yield from wait(1.2); rolled = c.rolls - r0
        e = {"hero": h["name"], "switched": sw, "pawn": p.get_class().get_name(), "want_pawn": os.path.basename(h["pawn"]) + "_C", "mesh": sk.get_name(),
             "hp": [c.get_health(), c.get_max_health(), h["health"]], "mana": [c.get_mana(), c.get_max_mana(), h["mana"]],
             "weapons": names, "want_weapons": [x["name"] for x in h["weapons"]], "drawn": c.get_weapon_index(), "held": held, "damage": dmg,
             "inventory": list(c.get_inventory_lines()), "rogue_controls": g.get_editor_property("rogue_controls"), "roll_clip": bool(g.get_editor_property("roll_clip")),
             "inventory_key": any("inventory" in l for l in g.get_editor_property("controls_keys")) and any("inventory" in l for l in g.get_editor_property("controls_pad")),
             "b_rolls": rolled}
        e["ok"] = (sw and e["pawn"] == e["want_pawn"] and abs(c.get_max_health() - h["health"]) < 0.01 and abs(c.get_health() - h["health"]) < 0.01
                   and abs(c.get_max_mana() - h["mana"]) < 0.01 and abs(c.get_mana() - h["mana"]) < 0.5 and names == e["want_weapons"] and c.get_weapon_index() == 0 and hands_ok
                   and all(abs(x["is"] - x["want"]) < 0.01 for x in dmg) and e["inventory"] == [f"weapon|{n}" for n in names]
                   and e["rogue_controls"] == bool(h.get("rogue")) and e["roll_clip"] == bool(h.get("rogue")) and e["inventory_key"] and rolled == (1 if h.get("rogue") else 0))
        allok &= e["ok"]; out.append(e)
    step_result("heroes", allok, heroes=out)

def step_inventory():
    yield from switch("Rogue")
    c = cb(); c.add_item("Small Healing Potion", 1); c.set_health(50.0)
    paused = lambda: GS.is_game_paused(G["w"])
    yield from press("I")
    o1 = (c.is_inventory_open(), paused())
    t0 = now(); yield from rwait(1.0); still = now() - t0
    yield from press("S"); cur1 = c.get_inventory_cursor()
    yield from press("Enter")
    xb = c.get_weapon_index() == 1; wm = c.get_weapon_mesh(); hx = c.get_holster_mesh(0, False)
    wield = {"weapon": str(c.get_weapon_name()), "in_hand": wm.static_mesh.get_name() if wm and wm.static_mesh and wm.is_visible() else None,
             "daggers_carried": bool(hx and hx.is_visible()), "message": c.message}
    yield from press("S"); cur2 = c.get_inventory_cursor()
    hp0 = c.get_health(); yield from press("Enter"); hp1 = c.get_health()
    drank = {"hp": [hp0, hp1], "potions_left": c.get_item_count("Small Healing Potion"), "message": c.message, "lines": list(c.get_inventory_lines())}
    yield from press("Tab")
    o2 = (c.is_inventory_open(), paused()); t0 = now(); yield from rwait(0.6); moving = now() - t0
    yield from press("Gamepad_Special_Right"); o3 = (c.is_inventory_open(), paused())
    yield from press("Gamepad_FaceButton_Right"); o4 = (c.is_inventory_open(), paused())
    # the Warlock's fire is cast alongside: always at hand, not drawn
    yield from switch("Warlock"); c = cb()
    yield from press("I"); yield from press("S"); yield from press("Enter")
    fire = {"cursor": c.get_inventory_cursor(), "drawn": c.get_weapon_index(), "message": c.message}
    yield from press("I"); o5 = (c.is_inventory_open(), paused())
    ok = (o1 == (True, True) and still < 0.01 and cur1 == 1 and xb and wield["in_hand"] is not None and wield["daggers_carried"]
          and cur2 == 2 and abs(hp1 - hp0 - 10.0) < 0.01 and drank["potions_left"] == 0
          and o2 == (False, False) and moving > 0.3 and o3 == (True, True) and o4 == (False, False)
          and fire["cursor"] == 1 and fire["drawn"] == 0 and "always at hand" in fire["message"] and o5 == (False, False))
    step_result("inventory", ok, opened=o1, game_seconds_while_open=round(still, 4), cursor_after_S=cur1, wield=wield, cursor_on_potion=cur2, drank=drank,
                closed_by_tab=o2, game_seconds_after=round(moving, 2), pad_start=o3, pad_b=o4, warlock_fire=fire, closed_by_i=o5)

def cast_and_measure(c, k, rate):
    """what a cast took: the mana gone, plus what came back meanwhile (her rate x the game time; none while full)"""
    m0, a0, t0 = c.get_mana(), c.attacks_made, now()
    yield from press(k, hold=0.15)
    m1, a1, t1 = c.get_mana(), c.attacks_made, now()
    yield from wait(1.6)
    back = rate * (t1 - t0) if m1 < c.get_max_mana() else 0.0
    return {"key": k, "mana": [round(m0, 2), round(m1, 2)], "spent": round(m0 - m1 + back, 2), "attacks": a1 - a0}
def step_mana():
    yield from switch("Mage"); c = cb(); h = hero_json("Mage")
    full = c.get_mana(); rate = h["mana_per_second"]
    f1 = yield from cast_and_measure(c, "LeftMouseButton", rate)
    yield from press("Two"); df_drawn = str(c.get_weapon_name())
    f2 = yield from cast_and_measure(c, "LeftMouseButton", rate)
    c.set_mana(5.0); r0 = c.casts_refused
    f3 = yield from cast_and_measure(c, "LeftMouseButton", 0.0); refused = {"attacks": f3["attacks"], "refused": c.casts_refused - r0, "message": c.message}
    c.set_mana(0.0); t0 = now(); yield from wait(5.0); regen = c.get_mana() / (now() - t0)
    yield from switch("Warlock"); c = cb()
    f4 = yield from cast_and_measure(c, "E", hero_json("Warlock")["mana_per_second"])
    cost = {x["name"]: x["mana"] for hh in HJ["heroes"] for x in hh["weapons"] if hh["name"] in ("Mage", "Warlock")}
    # (her mana comes back while the cast goes on: a few hundredths)
    ok = (abs(full - h["mana"]) < 0.01 and f1["attacks"] == 1 and abs(f1["spent"] - 8) < 0.2 and df_drawn == "Dark Fire" and f2["attacks"] == 1 and abs(f2["spent"] - 14) < 0.2
          and refused["attacks"] == 0 and refused["refused"] >= 1 and "Not enough mana" in refused["message"] and abs(regen - h["mana_per_second"]) < 0.1
          and f4["attacks"] == 1 and abs(f4["spent"] - 10) < 0.2 and abs(f4["mana"][0] - 60) < 0.5)
    step_result("mana", ok, mage_full=full, fire=f1, dark_fire_drawn=df_drawn, dark_fire=f2, too_little=refused, regen_per_second=round(regen, 3), want_regen=h["mana_per_second"],
                warlock_fire=f4, costs=cost)

def blow(hero, weapon_index, gap):
    """a blow or bolt of that weapon on the nearest live monster of the start section: the damage it dealt"""
    c = cb(); G["gen"].restart_play(0); yield from wait(0.8); refresh(); c = cb(); c.set_scripted_only(True)
    if weapon_index != c.get_weapon_index(): c.select_weapon(weapon_index)
    ms = start_monsters(); p = G["pawn"]
    ms.sort(key=lambda m: (m.get_actor_location() - p.get_actor_location()).length())
    for m in ms:
        if stand_off(m, gap): break
    else: return {"hero": hero, "error": "no place by a monster"}
    yield from wait(0.3)
    d0, h0 = c.damage_dealt, c.hits_landed
    started = c.start_attack(); t0 = now()
    while now() - t0 < 3.0 and c.hits_landed == h0: yield
    yield from wait(0.2)
    c.set_scripted_only(False)
    return {"hero": hero, "weapon": str(c.get_weapon_name()), "started": started, "dealt": round(c.damage_dealt - d0, 2), "hits": c.hits_landed - h0, "monster": m.get_name()}
def step_bonus():
    res = []
    for hero, wi, gap in (("Warrior", 0, 120), ("Warlock", 0, 120), ("Rogue", 1, 700), ("Rogue", 0, 110)):
        yield from switch(hero)
        h = hero_json(hero); d = list(G["gen"].get_editor_property("weapons"))[wi]
        r = yield from blow(hero, wi, gap)
        r["want"] = round(d.damage * (1.0 + weapon_bonus(d, h)), 2); res.append(r)
    # (a blow lands in full on every monster in its arc; a bolt bursts on one and splashes half on those beside it)
    def right(r):
        n = r.get("hits", 0)
        if n < 1: return False
        return abs(r["dealt"] - r["want"] * n) < 0.05 or abs(r["dealt"] - r["want"] * (1 + 0.5 * (n - 1))) < 0.05
    ok = all(right(r) for r in res)
    step_result("bonus", ok, blows=res)

def step_loot():
    yield from switch("Warrior"); c = cb(); g = G["gen"]
    g.restart_play(0); yield from wait(0.8); refresh(); c = cb()
    s0 = g.get_section(unreal.IntPoint(0, 0)); n = s0.get_num_containers()
    # F by a closed container: the first one with a free spot beside it from which F names it
    p = G["pawn"]; fpress = None
    for i in range(n):
        cl = s0.get_container_location(i)
        for k in range(16):
            a = k * math.pi / 8; q = V(cl.x + math.cos(a) * 130, cl.y + math.sin(a) * 130, 100)
            if s0.room_at(q) < 0: continue
            path = s0.find_path_world(q, g.get_start_room_center())
            if not len(path) or math.hypot(path[0].x - q.x, path[0].y - q.y) > 135.0: continue
            if not g.describe_nearest(q, 260.0).startswith("open"): continue
            if (g.describe_nearest(q, 260.0) or "").find("door") >= 0: continue
            p.set_actor_location(q, False, True); yield from wait(0.3)
            f0 = g.items_found; yield from press("F"); yield from wait(0.4)
            fpress = {"container": i, "found": g.items_found - f0, "item": str(g.last_found), "opened": round(s0.get_container_open_alpha(i), 2)}
            break
        if fpress: break
    # every container once
    got = []; bad = []
    for i in range(n):
        if s0.get_container_open_alpha(i) > 0.0: continue
        f0 = g.items_found; s0.toggle_container(i); yield from wait(0.05)
        found = g.items_found - f0; want = str(g.loot_of(unreal.IntPoint(0, 0), i))
        got.append(str(g.last_found))
        if found != 1 or str(g.last_found) != want: bad.append({"container": i, "found": found, "item": str(g.last_found), "want": want})
    carried = sum(int(l.split("|")[2]) for l in c.get_inventory_lines() if l.startswith("item|"))
    # opened again: nothing more
    yield from wait(1.0); i0 = 0; f0 = g.items_found
    s0.toggle_container(i0); yield from wait(1.0); s0.toggle_container(i0); yield from wait(0.5)
    again = g.items_found - f0
    # a section generated in play: nothing
    g.generate_section_now(unreal.IntPoint(1, 0)); t0 = time.time()
    while time.time() - t0 < 30:
        s1 = g.get_section(unreal.IntPoint(1, 0))
        if s1 and not s1.is_building(): break
        yield
    s1 = g.get_section(unreal.IntPoint(1, 0)); f0 = g.items_found; n1 = s1.get_num_containers() if s1 else 0
    for i in range(n1):
        if s1.get_container_open_alpha(i) <= 0.0: s1.toggle_container(i); yield
    gen_found = g.items_found - f0; gen_loot = sum(1 for i in range(n1) if str(g.loot_of(unreal.IntPoint(1, 0), i)) != "None")
    # the shares over many containers against the rarity
    N = 20000; cnt = {}
    for i in range(N): nm = str(g.loot_of(unreal.IntPoint(0, 0), 100000 + i)); cnt[nm] = cnt.get(nm, 0) + 1
    tot = sum(it["rarity"] for it in IJ["items"]); worst = 0.0; chi = 0.0; shares = []
    for it in IJ["items"]:
        pexp = it["rarity"] / tot; o = cnt.get(it["name"], 0) / N; sd = math.sqrt(pexp * (1 - pexp) / N)
        worst = max(worst, abs(o - pexp) / sd); chi += (cnt.get(it["name"], 0) - N * pexp) ** 2 / (N * pexp)
        shares.append([it["name"], round(o * 100, 2), round(pexp * 100, 2)])
    ok = (fpress is not None and fpress["found"] == 1 and fpress["opened"] > 0.0 and n > 0 and len(bad) == 0 and len(got) > 0 and carried == g.items_found and again == 0
          and n1 > 0 and gen_found == 0 and gen_loot == 0 and worst < 4.5 and set(cnt) <= {it["name"] for it in IJ["items"]})
    step_result("loot", ok, containers=n, by_f=fpress, opened=len(got), items=got, wrong=bad, carried=carried, found=g.items_found, opened_again_gave=again,
                generated_section_containers=n1, generated_found=gen_found, generated_loot=gen_loot, samples=N, worst_sd=round(worst, 2), chi2=round(chi, 1), dof=len(IJ["items"]) - 1, shares=shares)

def step_potions():
    yield from switch("Warrior"); c = cb(); hp = c.get_max_health(); out = []; ok = True
    for it in IJ["items"]:
        if it["kind"] != "healing": continue
        c.add_item(it["name"], 1); c.set_health(hp * 0.1); h0 = c.get_health()
        used = c.use_item(it["name"]); h1 = c.get_health()
        want = min(hp, h0 + hp * it["amount"]) - h0
        out.append([it["name"], round(h1 - h0, 2), round(want, 2), used]); ok &= used and abs(h1 - h0 - want) < 0.01
    c.add_item("Small Healing Potion", 1); c.set_health(hp); full_refused = not c.use_item("Small Healing Potion") and c.get_item_count("Small Healing Potion") == 1
    c.add_item("Small Mana Potion", 1); warrior_mana_refused = not c.use_item("Small Mana Potion") and c.get_item_count("Small Mana Potion") == 1
    yield from switch("Mage"); c = cb(); mp = c.get_max_mana(); mout = []
    for it in IJ["items"]:
        if it["kind"] != "mana": continue
        c.add_item(it["name"], 1); c.set_mana(0.0); m0 = c.get_mana()
        used = c.use_item(it["name"]); m1 = c.get_mana()
        mout.append([it["name"], round(m1 - m0, 2), round(mp * it["amount"], 2), used]); ok &= used and abs(m1 - m0 - mp * it["amount"]) < 0.05
    ok &= full_refused and warrior_mana_refused
    step_result("potions", ok, healing=out, mana=mout, refused_at_full_hp=full_refused, warrior_mana_refused=warrior_mana_refused)

def regen_over(c, sec):
    h0, t0, k0 = c.get_health(), now(), c.hits_taken
    yield from wait(sec)
    return (c.get_health() - h0) / (now() - t0), c.hits_taken - k0
def step_food():
    yield from switch("Warrior"); c = cb(); hp = c.get_max_health()
    # (somewhere quiet: the middle of the start section's great hall, the monsters put back where they started)
    quiet(True); G["gen"].restart_play(0); yield from wait(0.8); refresh(); c = cb(); quiet(True)
    c.add_item("Bread", 2); c.add_item("Fish", 1); c.add_item("Well Done Steak", 1)
    c.set_health(hp * 0.2); c.use_item("Bread")
    r1, k1 = yield from regen_over(c, 4.0)
    yield from wait(6.5); r_after, k2 = yield from regen_over(c, 2.0)
    c.set_health(hp * 0.2); c.use_item("Bread"); c.use_item("Fish")
    r2, k3 = yield from regen_over(c, 3.0)
    yield from wait(8.0)
    c.set_health(hp * 0.05); c.use_item("Well Done Steak")
    r3, k4 = yield from regen_over(c, 3.0)
    hit = k1 + k2 + k3 + k4
    ok = hit == 0 and abs(r1 - 0.01 * hp) < 0.02 and abs(r_after) < 1e-3 and abs(r2 - 0.03 * hp) < 0.05 and abs(r3 - 0.09 * hp) < 0.1
    quiet(False)
    step_result("food", ok, bread_hp_per_s=round(r1, 3), want=0.01 * hp, after_10s=round(r_after, 4), bread_and_fish=round(r2, 3), want_both=0.03 * hp, steak=round(r3, 3), want_steak=round(0.09 * hp, 2), hits_taken=hit)

def clear_line():
    """a start and a way across the great hall along which a capsule meets nothing for 11 m (pillars, furniture, monsters)"""
    p = G["pawn"]; g = G["gen"]
    s0 = g.get_section(unreal.IntPoint(0, 0)); ctr = g.get_start_room_center(); room = s0.room_at(ctr)
    mn, mx = s0.get_room_bounds(room)
    along_x = (mx.x - mn.x) >= (mx.y - mn.y)
    for off in (0, 100, -100, 200, -200, 300, -300, 400, -400, 500, -500, 600, -600):
        a = V(mn.x + 150, ctr.y + off, 100) if along_x else V(ctr.x + off, mn.y + 150, 100)
        b = V(a.x + 1100, a.y, 100) if along_x else V(a.x, a.y + 1100, 100)
        hit = unreal.SystemLibrary.capsule_trace_single(G["w"], a, b, 40.0, 60.0, unreal.TraceTypeQuery.ECC_VISIBILITY, False, [p], unreal.DrawDebugTrace.NONE, True)
        if hit is None or not hit.to_tuple()[0]: return a, (0.0 if along_x else 90.0), (mx.x - mn.x) if along_x else (mx.y - mn.y)
    return None, 0.0, 0.0
def run_speed(sec=1.8):
    """her speed over the last half second of a run along a clear line across the hall (W held, run mode)"""
    p = G["pawn"]; c = cb()
    start, yaw, hall = clear_line()
    if start is None: return 0.0, 0.0
    p.set_actor_location(start, False, True); p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw), True)
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-10, yaw=yaw)); c.set_run_mode(True)
    yield from wait(0.4)
    c.simulate_key(key("W"), True)
    yield from wait(sec - 0.5)
    a, t0 = p.get_actor_location(), now()
    yield from wait(0.5)
    b, t1 = p.get_actor_location(), now()
    c.simulate_key(key("W"), False); yield from wait(0.6)
    return math.hypot(b.x - a.x, b.y - a.y) / (t1 - t0), hall
def step_speed():
    yield from switch("Warrior"); c = cb(); quiet(True); G["gen"].restart_play(0); yield from wait(0.8); refresh(); c = cb(); quiet(True)
    base_max = c.get_base_walk_speed()
    v0, hall = yield from run_speed()
    c.add_item("Large Speed Potion", 1); c.use_item("Large Speed Potion"); tp = now()
    bonus = c.get_speed_bonus(); mx1 = G["pawn"].character_movement.max_walk_speed
    v1, _ = yield from run_speed()
    # in an attack she is slowed under it too, and back to the potion's speed after
    c.start_attack(); yield from wait(0.1); slowed = G["pawn"].character_movement.max_walk_speed
    yield from wait(1.6); after_attack = G["pawn"].character_movement.max_walk_speed
    left = 30.0 - (now() - tp); mid_bonus = c.get_speed_bonus()
    while now() - tp < 30.5: yield
    end_bonus = c.get_speed_bonus(); mx2 = G["pawn"].character_movement.max_walk_speed
    ok = (abs(bonus - 0.3) < 1e-4 and abs(mx1 - base_max * 1.3) < 0.5 and abs(v1 / v0 - 1.3) < 0.05 and abs(slowed - base_max * 1.3 * 0.12) < 0.5
          and abs(after_attack - base_max * 1.3) < 0.5 and abs(mid_bonus - 0.3) < 1e-4 and end_bonus == 0.0 and abs(mx2 - base_max) < 0.5 and v0 > 300)
    quiet(False)
    step_result("speed", ok, base_max_speed=round(base_max, 1), run_speed=round(v0, 1), with_potion=round(v1, 1), ratio=round(v1 / v0, 3), bonus=bonus,
                max_speed_with_potion=round(mx1, 1), in_attack=round(slowed, 1), after_attack=round(after_attack, 1), seconds_left_then=round(left, 1), bonus_then=mid_bonus,
                after_30s=[end_bonus, round(mx2, 1)], hall_cm=round(hall))

def step_noregen():
    yield from switch("Rogue"); c = cb(); quiet(True); G["gen"].restart_play(0); yield from wait(0.8); refresh(); c = cb(); quiet(True)
    c.set_health(50.0); k0 = c.hits_taken; h0 = c.get_health()
    yield from wait(9.0)
    h1 = c.get_health()
    ok = c.hits_taken == k0 and abs(h1 - h0) < 1e-3 and G["gen"].get_editor_property("regen_per_second") == 0.0
    quiet(False)
    step_result("noregen", ok, before=h0, after_9s=h1, hits_taken=c.hits_taken - k0, regen_per_second=G["gen"].get_editor_property("regen_per_second"))

# ------------------------------------------------------------------------------------------------ the painted interface
def hud_art():
    h = G["pc"].get_hud() if G.get("pc") else None
    return sorted(str(n) for n in h.get_art_drawn()) if h else []
def shot(name):
    unreal.SystemLibrary.execute_console_command(G["w"], f"HighResShot 1920x1080 filename=rdm4_{TAG}_{name}")
    R.setdefault("shots", []).append(f"rdm4_{TAG}_{name}.png")
def step_menuui():
    """(the menu) each hero's card is drawn with the painted pieces: the board, the framed hit point and mana bars with
    their fills, the dividers, the plates under the names and START, the arrows; a picture of each for the eye"""
    s = G["sel"]; assert s, "open random_dungeonmagic_level4_select for the menuui step"
    sim = lambda k, d: G["sel"].simulate_key(k, d)
    have = sorted(str(k) for k in s.get_editor_property("ui_art").keys())
    want = {"panel", "button", "arrow", "bar_health", "fill_health", "bar_mana", "fill_mana", "divider"}
    out = []
    yield from wait(0.6)
    for i in range(len(s.heroes)):
        yield from wait(0.6)                            # (the card fades in over 0.35 s)
        # (and her weapons' and spells' pictures in their slots)
        h = s.heroes[s.get_index()]; wi = {str(w.icon) for w in h.weapons}
        d = hud_art(); out.append({"hero": str(s.get_hero_name()), "drawn": d, "weapon_icons": sorted(wi), "missing": sorted((want | wi | {"slot"}) - set(d))})
        shot(f"menu_{out[-1]['hero']}"); yield from rwait(1.5)
        yield from press("D", sim=sim)
    yield from wait(0.5)
    ok = want <= set(have) and all(not o["missing"] for o in out) and str(s.get_hero_name()) == out[0]["hero"]
    step_result("menuui", ok, pieces=have, cards=out)
def step_ui():
    """(the dungeon) for each hero the status panel's board, the framed bars and their fills (mana only for those who have
    it), the weapon slots with her weapons' pictures and the minimap's ring are drawn; with a speed potion and food in her
    the effects' pictures; a container's item shows on the FOUND plaque with its picture; the open inventory has the board,
    the dividers, the lit plate, the pictures of her weapons and of what she carries; a picture of each for the eye"""
    g = G["gen"]; ua = g.get_editor_property("ui_art")
    pieces = sorted(str(k) for k in ua.keys())
    textures = all(ua[k].texture is not None for k in ua.keys())
    item_icons = {str(i.name): str(i.icon) for i in g.get_editor_property("items")}
    heroes = []
    quiet(True)
    for h in ("Warrior", "Mage", "Warlock", "Rogue"):
        yield from switch(h); quiet(True); c = cb()
        yield from wait(0.5)
        icons = [str(w.icon) for w in g.get_editor_property("weapons")]
        want = {"panel_wide", "bar_health", "fill_health", "slot", "minimap_ring"} | set(icons) | ({"bar_mana", "fill_mana"} if c.get_max_mana() > 0 else set())
        d = hud_art()
        heroes.append({"hero": h, "weapon_icons": icons, "drawn": d, "missing": sorted(want - set(d)),
                       "mana_bar_without_mana": c.get_max_mana() <= 0 and "bar_mana" in d})
        shot(f"hud_{h}"); yield from rwait(1.5)
    # (the Rogue) a speed potion drunk and bread eaten: their pictures on the effect chips
    c = cb(); c.set_health(c.get_max_health() * 0.5)
    for n in ("Large Speed Potion", "Bread"): c.add_item(n, 1); c.use_item(n)
    yield from wait(0.3)
    chips = hud_art(); shot("chips"); yield from rwait(1.5)
    # a container's item: FOUND on the plaque with the item's picture
    s0 = g.get_section(unreal.IntPoint(0, 0)); found = None
    for i in range(s0.get_num_containers()):
        if str(g.loot_of(unreal.IntPoint(0, 0), i)) == "None" or s0.get_container_open_alpha(i) > 0.0: continue
        f0 = g.items_found; s0.toggle_container(i); yield from wait(0.05)
        if g.items_found > f0: found = str(g.last_found); break
    yield from wait(0.6)
    fd = hud_art(); shot("found"); yield from rwait(1.5)
    found_ok = found is not None and "banner" in fd and item_icons.get(found, "None") in fd
    # the inventory (it pauses the game: real time)
    for n in ("Small Healing Potion", "Fish"): c.add_item(n, 1)
    yield from press("I"); yield from rwait(0.5)
    inv = hud_art(); shot("inventory"); yield from rwait(1.5)
    carried = [str(n) for n in c.get_inventory_lines()]
    want_inv = {"panel_wide", "divider", "button", "slot", "w_daggers", "w_crossbow", item_icons["Small Healing Potion"], item_icons["Fish"]}
    yield from press("I")
    quiet(False)
    ok = (textures and not [x for x in heroes if x["missing"] or x["mana_bar_without_mana"]] and {"chip_speed", "chip_regen"} <= set(chips)
          and found_ok and want_inv <= set(inv) and all(v != "None" for v in item_icons.values()))
    step_result("ui", ok, pieces=pieces, textures=textures, item_icons=item_icons, heroes=heroes, chips=chips, found=found, found_drawn=fd,
                inventory_drawn=inv, inventory_missing=sorted(want_inv - set(inv)), carried=carried)

def step_menufirst():
    """(828 started play on random_dungeonmagic_level4 itself, rd.HeroMenu 1) the dungeon played without ?Hero= opened its
    menu: play is in random_dungeonmagic_level4_select, the menu's turntable is there, no dungeon generator; the menu
    opens the dungeon with the hero chosen (the select step goes on from here)"""
    yield from wait(0.5)
    refresh()
    s = G.get("sel"); world = G["w"].get_path_name().split(".")[-1]
    cvar = unreal.SystemLibrary.get_console_variable_int_value("rd.HeroMenu")
    # (what play began in, from the log: the editor's world copied for play last, and the generator's line after it; the
    # editor world itself is not to be had from Python during play)
    lines = open(os.path.join(unreal.Paths.project_log_dir(), "claude_ue5.log"), encoding="utf-8", errors="replace").read().splitlines()
    made = [i for i, l in enumerate(lines) if "Created PIE world by copying editor world from" in l]
    played = lines[made[-1]].split("editor world from ")[-1].split(".")[0].split("/")[-1] if made else None
    menu_line = next((l.split("RDHERO ")[-1] for l in lines[made[-1]:] if "RDHERO no hero chosen" in l), None) if made else None
    ok = (played == "random_dungeonmagic_level4" and menu_line is not None and world == "random_dungeonmagic_level4_select" and s is not None
          and G.get("gen") is None and str(s.get_hero_name()) == "Warrior" and str(s.target_level).endswith("random_dungeonmagic_level4") and cvar == 1)
    step_result("menufirst", ok, played=played, generator_said=menu_line, now_in=world, menu=s is not None, generator=G.get("gen") is not None,
                shown=str(s.get_hero_name()) if s else None, target=str(s.target_level) if s else None, hero_menu_cvar=cvar)
def step_map():
    """(the dungeon) M opens the big map in the minimap's painted style: the board, the plaque, the compass, the key's
    divider, no minimap ring; she walks with it open (W, a second); M closes it and the minimap's ring is back"""
    g = G["gen"]; c = cb(); quiet(True)
    # (at the start of a clear line across the great hall, facing along it: the walk meets nothing)
    start, yaw, _ = clear_line()
    if start is not None:
        G["pawn"].set_actor_location(start, False, True); G["pawn"].set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw), True)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-10, yaw=yaw))
    yield from wait(0.5)
    before = hud_art()
    yield from press("M"); yield from wait(0.4)
    opened = bool(g.get_editor_property("map_open")); d = hud_art()
    shot("map"); yield from rwait(1.5)
    p0 = G["pawn"].get_actor_location(); c.set_run_mode(True)
    c.simulate_key(key("W"), True); yield from wait(1.0); c.simulate_key(key("W"), False)
    moved = (G["pawn"].get_actor_location() - p0).length()
    shot("map_walked"); yield from rwait(1.5)
    yield from press("M"); yield from wait(0.4)
    closed = not g.get_editor_property("map_open"); after = hud_art()
    quiet(False)
    want = {"panel_wide", "banner", "compass", "divider"}
    ok = ("minimap_ring" in before and opened and want <= set(d) and "minimap_ring" not in d and moved > 150.0 and closed and "minimap_ring" in after and "compass" not in after)
    step_result("map", ok, opened=opened, drawn=d, missing=sorted(want - set(d)), walked_cm=round(moved), closed=closed, after=after)

STEPS = {"select": step_select, "heroes": step_heroes, "inventory": step_inventory, "mana": step_mana, "bonus": step_bonus, "loot": step_loot,
         "potions": step_potions, "food": step_food, "speed": step_speed, "noregen": step_noregen, "menuui": step_menuui, "ui": step_ui,
         "menufirst": step_menufirst, "map": step_map}
def run():
    for s in PLAN:
        yield from STEPS[s]()
        yield from rwait(0.3)
def finish(err=None):
    unreal.unregister_slate_post_tick_callback(G["h"])
    R["error"] = err
    try:
        c = cb() if G.get("gen") else None
        if c: c.set_scripted_only(False); c.set_inventory_open(False)
        if G.get("gen"): quiet(False)
    except Exception as e: R["error"] = (err or "") + " / " + str(e)
    os.makedirs(SA, exist_ok=True); json.dump(R, open(os.path.join(SA, f"test_{TAG}.json"), "w"), indent=1)
    ok = not R.get("error") and len(R["steps"]) == len(PLAN) and all(s["ok"] for s in R["steps"])
    unreal.log(f"RDM4TEST done | {TAG} | {'ok' if ok else 'FAILED'} | " + " | ".join(f"{s['step']} {'ok' if s['ok'] else 'FAILED'}" for s in R["steps"]) + f" | {R.get('error') or ''}")
    G.clear()
def tick(dt):
    try:
        if UES.get_game_world() is None and not G.get("traveling"): finish("PIE ended"); return
        next(G["gen_"])
    except StopIteration: finish()
    except Exception as e:
        import traceback
        unreal.log_error("RDM4TEST error: " + str(e) + traceback.format_exc()); finish(str(e))
G["gen_"] = run()
G["h"] = unreal.register_slate_post_tick_callback(tick)
print("rdm4 test armed:", PLAN, TAG)
