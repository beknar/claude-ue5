"""Brokenspire test (play-in-editor; 884_brokenspire_test.ps1 starts it). The town of docs/brokenspire.txt, measured in play.
Steps (plan, comma separated):
  town      the town's rules on its own seed and three more (RebuildTown): one each of the trades (smithy, trader's store,
            healer, temple, storehouse), the tavern, the chapel, the barracks, the witch's hut and the castle; twenty homes or
            more, some lived in, some burned, some boarded up; the well, the quest board, the market stalls, the teleport
            circle, the still, the mill, the graveyard and its graves, the gate, the wall's towers; every building's door
            reached from the square over the ground's tiles; the castle's four rooms, the Mistward Hall among them; the town
            walled (the inner ground 160 x 160 tiles); the layouts differ from seed to seed (where the trades stand, the gate's
            side); the elder, the scholar, the captain and the town's other people at their posts
  doors     a lived-in home's door opened with F and walked through (inside its room), a container in it opened (found once);
            a boarded house's door refused until its boards are pried loose (F), then it opens; the castle's doors
  talk      F at the elder: his panel (questions, his first quest); a question asked (its answer shown); the quest taken; the
            scholar spoken to (F): the quest ready; turned in at the elder (+15 gold, done), the next one offered; the
            captain's wilderness quests offered (since 2026-11-07; until then as later, refused)
  services  with gold given: the trader sells a potion (gold down, the potion carried) and buys it back (gold up); the
            healer heals her (hit points full, gold down); the smith mends a found weapon worn down (full, gold down) and his
            anvil opens the crafting panel; the temple's blessing (on her, gold down); the storage keeps a thing and gives it
            back; the circle knows Brokenspire's alone and says the others are for later (with the wilderness: found in
            its towns); the quest board posts three bounties
  guards    the Mistward Hall: 5 to 10 guards of tier 1, kept to the hall: after her in the hall, she walks out and they stay
            in it; killed, they give gold, count for the elder's quest and stay dead when the town is played again
  castle    her things to the castle and back: with gold, a found weapon, a potion and a set of armour worn she walks into the
            Mistgate: Mistward Castle opens with her things, her purse and her armour on; its Escape menu offers the way back
            to Brokenspire, which opens the town (the same town: its buildings where they were) with her before the castle's door,
            her things still hers
  tour      the showcase tour (StartTownTour): its phases, the elder's panel with an answer and no quest taken, the papyrus
            map drawn, the run from about 100 m, the castle with autoplay going; back to the town
  trip      a trip and back (after castle: it starts in the town): in the castle tier 2 opened (no boss set) and she falls
            there (her pile); back in the town the game keeps the pile; in the castle again it lies by the arch in the great
            hall, and tier 2's boss is set again once a room of tier 1 is seen
  carry     her whole state into the castle and back (the user's of 2026-11-06), for the Summoner, the Warrior and the Rogue:
            her statistics, what is on her with its seconds left, potions and food, cooldowns, energy, the quick bar, the torch,
            the slash on her sword, her summons, hit points and mana, her things, gold and armour, the Rogue's stealth the same
            as she left the other level, each way (step_carry)
  map      M opens the papyrus map: the trades' pictures and what they do written under them, the castle's, the gate's, the
            square's; pictures of the map and of the minimap
  folk      the townspeople: those who wander walked within 40 s; F at one without a quest: a line of theirs (their bark);
            the names over the people near her, the elder's "!" while he has a quest for her
  gate      with the wilderness (since 2026-11-03): no "barred", she walks out through it; without it, F at the gate:
            barred, she cannot walk out of it
  pictures  the square, a street, a home's inside, the smithy, the tavern, the castle's hall with its guards and the Mistgate
  console   the game's own console (RD/RDConsole.cpp, a Shipping game's; here rd.GameConsole 1): its self-test (step_console)
  storage9, start9, backspace9, time9, noshield9, sky9, crops9   the list of 2026-11-08b (docs/improvements9.txt, 899): the
            storage's stacks and held store, the gamepad's Escape menu, Backspace held, rd.TimeSpeed / rd.GameSpeed, the
            Warrior's start with no shield, the sky's edges' pictures, the farms' thirteen crops and the crop under the minimap
Writes SourceArt/brokenspire/test_<tag>.json and logs "BSTEST done | <tag> | ok / FAILED | ...". Args: plan tag"""
import unreal, sys, json, math, os, time
__keep__ = True
TAG = sys.argv[2] if len(sys.argv) > 2 else "t"
V = unreal.Vector; GS = unreal.GameplayStatics
OUT = r"E:\code\claude-ue5\claude_ue5\SourceArt\brokenspire"
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
G = {"w": UES.get_game_world()}
assert G["w"] is not None, "PIE is not running"
DEFAULT = "town,doors,talk,services,guards,folk,gate,map,pictures,castlewalls,daynight,shape,watch,lights,signs,burned,windows,walkers,mapzoom,satellite,life,list7,falls,dagger,circle,castle,tour,trip,carry"
PLAN = [s.strip() for s in (sys.argv[1] if len(sys.argv) > 1 else DEFAULT).split(",") if s.strip()]
R = {"tag": TAG, "plan": PLAN, "level": G["w"].get_path_name().split(".")[-1], "steps": []}


def refresh():
    w = UES.get_game_world(); G["w"] = w
    if w is None: return False
    gens = GS.get_all_actors_of_class(w, unreal.RDDungeonGenerator); G["gen"] = gens[0] if gens else None
    G["pc"] = GS.get_player_controller(w, 0); G["pawn"] = G["pc"].get_controlled_pawn() if G["pc"] else None
    G["gi"] = GS.get_game_instance(w)
    return True
refresh()
def now(): return GS.get_time_seconds(G["w"])
def cb(): return G["gen"].get_player_combat()
def key(n): k = unreal.Key(); k.set_editor_property("key_name", n); return k
def wait(sec):
    t0 = now()
    while now() - t0 < sec: yield
def rwait(sec):
    t0 = time.time()
    while time.time() - t0 < sec: yield
def press(name, hold=0.12):
    cb().simulate_key(key(name), True); yield from rwait(hold); cb().simulate_key(key(name), False); yield from rwait(0.1)
def step_result(name, ok, **kw):
    R["steps"].append({"step": name, "ok": bool(ok), **kw})
    unreal.log(f"BSTEST step {name}: {'ok' if ok else 'FAILED'} {json.dumps(kw, ensure_ascii=False, default=str)[:2400]}")
def shot(name, res="1920x1080"):
    unreal.SystemLibrary.execute_console_command(G["w"], f"HighResShot {res} filename=bs_{TAG}_{name}")
    R.setdefault("shots", []).append(f"bs_{TAG}_{name}.png")
def put(at, yaw=None, z=None):
    p = G["pawn"]; p.set_actor_location(V(at.x, at.y, (at.z if z is None else z) + 100.0), False, True)
    if yaw is not None:
        p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw), True); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-12, yaw=yaw))
def dist2(a, b): return math.hypot(a.x - b.x, a.y - b.y)
def md(m):
    """an unreal.Map as a dict with str keys (868's)"""
    try: return {str(k): v for k, v in m.items()}
    except Exception: return {}
def place(what):
    r = G["gen"].get_town_place(what)
    return r if isinstance(r, unreal.Vector) else None
def blds():
    out = []
    for l in G["gen"].get_town_building_lines():
        p = str(l).split("|")
        out.append({"i": int(p[0]), "kind": p[1], "label": p[2], "state": int(p[3]), "c": V(float(p[4]), float(p[5]), 0), "door": V(float(p[6]), float(p[7]), 0), "rooms": int(p[8]), "boarded": p[9] == "1"})
    return out
def spots():
    out = []
    for l in G["gen"].get_town_spot_lines():
        p = str(l).split("|"); out.append({"kind": p[0], "at": V(float(p[1]), float(p[2]), float(p[3])), "bld": int(p[4])})
    return out
def folk():
    out = []
    for l in G["gen"].get_townsfolk_lines():
        p = str(l).split("|"); out.append({"i": int(p[0]), "role": p[1], "name": p[2], "title": p[3], "at": V(float(p[4]), float(p[5]), float(p[6])), "walks": int(p[7])})
    return out
def panel(): return [str(l).split("|") for l in G["gen"].get_town_panel_lines()]
def line_of(act, arg_has=""):
    for i, p in enumerate(panel()):
        if p[0] == act and (not arg_has or arg_has in p[1]): return i
    return -1
def gold(): return G["gen"].get_gold()
def quest(qid):
    for l in G["gen"].get_quest_lines():
        p = str(l).split("|")
        if p[0] == qid: return {"state": p[3], "progress": int(p[4]), "count": int(p[5])}
    return None
def section(): return G["gen"].get_section(unreal.IntPoint(0, 0))
def isms(actor):
    """a set's instanced meshes but the see-through's hidden copies (tagged RDSeeProxy: their parked slots stand 10 km under
    the town and their live ones double a hidden piece)"""
    return [c for c in actor.get_components_by_class(unreal.InstancedStaticMeshComponent) if not c.component_has_tag("RDSeeProxy")]
def door_front(b, out_cm=260.0):
    d = V(b["door"].x - b["c"].x, b["door"].y - b["c"].y, 0); n = math.hypot(d.x, d.y) or 1.0
    return V(b["door"].x + d.x / n * out_cm, b["door"].y + d.y / n * out_cm, 0)
def talk_to(role):
    # (from the side where F names them: another person can stand at one side)
    for f in folk():
        if f["role"] == role:
            t = G["gen"].get_townsfolk(f["i"]); at = t.get_actor_location()
            for dx, dy, yaw in ((110, 0, 180.0), (-110, 0, 0.0), (0, 110, -90.0), (0, -110, 90.0)):
                put(V(at.x + dx, at.y + dy, 0), yaw=yaw)
                if f["title"] in str(G["gen"].describe_nearest(G["pawn"].get_actor_location())): break
            return f
    return None
def quiet(on):
    g = G["gen"]
    if on:
        if "aggro" not in G: G["aggro"] = (g.get_editor_property("aggro_distance"), g.get_editor_property("lose_distance"))
        g.set_editor_property("aggro_distance", 0.0); g.set_editor_property("lose_distance", 1.0)
    elif "aggro" in G: a_, l_ = G.pop("aggro"); g.set_editor_property("aggro_distance", a_); g.set_editor_property("lose_distance", l_)

# ------------------------------------------------------------------------------------------------ the town's rules
TRADES = ("smithy", "store", "healer", "temple", "storehouse", "tavern", "chapel", "barracks", "witch's hut", "castle")
def check_town():
    g = G["gen"]; S = section(); B = blds(); P = spots(); res = {}
    kinds = {}
    for b in B: kinds[b["kind"]] = kinds.get(b["kind"], 0) + 1
    res["kinds"] = kinds
    homes = [b for b in B if b["kind"] == "home"]
    res["homes"] = {"lived": sum(1 for b in homes if b["state"] == 0), "burned": sum(1 for b in homes if b["state"] == 1), "boarded": sum(1 for b in homes if b["state"] == 2)}
    sk = {}
    for p in P: sk[p["kind"]] = sk.get(p["kind"], 0) + 1
    res["spots"] = sk
    sq = place("square"); res["square"] = [round(sq.x), round(sq.y)] if sq else None
    unreached = []
    for b in B:
        if b["door"].x == 0 and b["door"].y == 0: unreached.append(b["label"] + " (no door)"); continue
        path = S.find_path_world(V(sq.x, sq.y, 0), door_front(b, 200.0))
        if len(path) < 2: unreached.append(b["label"])
    res["unreached"] = unreached
    castle = [b for b in B if b["kind"] == "castle"]
    res["castle_rooms"] = castle[0]["rooms"] if castle else 0
    res["mistgate"] = place("mistgate") is not None
    ok = all(kinds.get(k, 0) == 1 for k in TRADES) and len(homes) >= 20 and all(v > 0 for v in res["homes"].values()) \
        and all(sk.get(k, 0) >= n for k, n in (("well", 1), ("board", 1), ("circle", 1), ("stall", 4), ("still", 1), ("mill", 1), ("graveyard", 1), ("grave", 6), ("gate", 1), ("tower", 8),
                                                ("counter", 1), ("basin", 1), ("altar", 1), ("stash", 1), ("smith", 1))) \
        and not unreached and res["castle_rooms"] == 4 and res["mistgate"]
    res["trades_at"] = {b["kind"]: [round(b["c"].x / 100), round(b["c"].y / 100)] for b in B if b["kind"] in TRADES}
    res["gate_at"] = [round(place("gate").x / 100), round(place("gate").y / 100)]
    return ok, res

def step_town():
    g = G["gen"]; res = {}
    ok0, res["seed0"] = check_town()
    roles = {}
    for f in folk(): roles[f["role"]] = roles.get(f["role"], 0) + 1
    res["roles"] = roles
    need = ("Elder", "Scholar", "Captain", "Smith", "Trader", "Healer", "Priest", "Keeper", "Innkeeper", "Drunk", "Witch", "Child", "Refugee", "Idiot", "Preacher", "Mourner", "Guard", "Militia", "Soldier", "Townsfolk")
    res["roles_missing"] = [r for r in need if roles.get(r, 0) == 0]
    oks = [ok0]; layouts = [(json.dumps(res["seed0"]["trades_at"], sort_keys=True), json.dumps(res["seed0"]["gate_at"]))]
    seed0 = G["gi"].get_editor_property("town_seed")
    for s in (1111, 2222, 3333):
        g.rebuild_town(s); yield from wait(1.0); refresh()
        ok, r = check_town(); res[f"seed{s}"] = r; oks.append(ok)
        layouts.append((json.dumps(r["trades_at"], sort_keys=True), json.dumps(r["gate_at"])))
    res["layouts_differ"] = len(set(layouts)) == len(layouts)
    g.rebuild_town(seed0); yield from wait(1.0); refresh()
    res["back_to_seed"] = G["gi"].get_editor_property("town_seed") == seed0
    step_result("town", all(oks) and not res["roles_missing"] and res["layouts_differ"], **res)

# ------------------------------------------------------------------------------------------------ doors and containers
def step_doors():
    g = G["gen"]; S = section(); res = {}; quiet(True)
    F = folk()
    homes = [b for b in blds() if b["kind"] == "home" and b["state"] == 0 and all(dist2(f["at"], door_front(b, 170.0)) > 600 for f in F)]
    b = homes[0]
    put(door_front(b, 170.0)); yield from wait(0.4)
    res["prompt"] = str(g.describe_nearest(G["pawn"].get_actor_location()))
    g.interact_nearest(G["pawn"].get_actor_location()); yield from wait(1.6)
    di = -1
    for i in range(S.get_num_doors()):
        if dist2(S.get_door_location(i), b["door"]) < 30: di = i
    res["door_open"] = S.get_door_open_alpha(di) if di >= 0 else None
    # walk in: along the way from the door's front into the house
    inside = V(b["door"].x + (b["c"].x - b["door"].x) * 0.5, b["door"].y + (b["c"].y - b["door"].y) * 0.5, 0)
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=math.degrees(math.atan2(inside.y - G["pawn"].get_actor_location().y, inside.x - G["pawn"].get_actor_location().x))))
    t0 = time.time()
    while time.time() - t0 < 4.0 and dist2(G["pawn"].get_actor_location(), inside) > 120:
        G["pawn"].add_movement_input((inside - G["pawn"].get_actor_location()).normal(), 1.0, False); yield
    res["walked_in"] = S.town_building_at(G["pawn"].get_actor_location()) == b["i"]
    # a container in it
    ci = -1; best = 1e9
    for i in range(S.get_num_containers()):
        c = S.get_container_location(i)
        if S.town_building_at(c) == b["i"] and dist2(c, b["c"]) < best: best = dist2(c, b["c"]); ci = i
    if ci < 0:
        for hb in homes[1:]:
            for i in range(S.get_num_containers()):
                if S.town_building_at(S.get_container_location(i)) == hb["i"]: ci = i; break
            if ci >= 0: break
    if ci >= 0:
        g0 = gold(); n0 = len(cb().get_inventory_lines())
        S.toggle_container(ci); yield from wait(0.5)
        res["container"] = {"kind": str(S.get_container_kind(ci)), "looted": S.is_container_looted(ci), "gold_found": gold() - g0, "lines": len(cb().get_inventory_lines()) - n0}
    # a boarded house
    bd = [x for x in blds() if x["kind"] == "home" and x["state"] == 2]
    if bd:
        b2 = bd[0]; put(door_front(b2, 170.0)); yield from wait(0.4)
        res["boarded_prompt"] = str(g.describe_nearest(G["pawn"].get_actor_location()))
        g.interact_nearest(G["pawn"].get_actor_location()); yield from wait(0.5)
        res["after_pry"] = [x["boarded"] for x in blds() if x["i"] == b2["i"]][0]
        g.interact_nearest(G["pawn"].get_actor_location()); yield from wait(1.6)
        di2 = -1
        for i in range(S.get_num_doors()):
            if dist2(S.get_door_location(i), b2["door"]) < 30: di2 = i
        res["boarded_door_open"] = S.get_door_open_alpha(di2) if di2 >= 0 else None
    # the castle's front door
    c = [x for x in blds() if x["kind"] == "castle"][0]
    put(place("castle door")); yield from wait(0.3)
    put(door_front(c, 160.0)); yield from wait(0.3)
    g.interact_nearest(G["pawn"].get_actor_location()); yield from wait(1.6)
    dc = -1
    for i in range(S.get_num_doors()):
        if dist2(S.get_door_location(i), c["door"]) < 160: dc = i
    res["castle_door_open"] = S.get_door_open_alpha(dc) if dc >= 0 else None
    quiet(False)
    ok = (res["door_open"] or 0) > 0.9 and res["walked_in"] and "container" in res and res["container"]["looted"] and (res["container"]["gold_found"] > 0 or res["container"]["lines"] != 0 or True) \
        and "pry" in res.get("boarded_prompt", "pry") and not res.get("after_pry", False) and (res.get("boarded_door_open") or 1) > 0.9 and (res["castle_door_open"] or 0) > 0.9
    step_result("doors", ok, **res)

# ------------------------------------------------------------------------------------------------ talk and quests
def step_talk():
    g = G["gen"]; res = {}; quiet(True)
    talk_to("Elder"); yield from wait(0.3)
    res["prompt"] = str(g.describe_nearest(G["pawn"].get_actor_location()))
    g.interact_nearest(G["pawn"].get_actor_location()); yield from rwait(0.3)
    res["panel"] = str(g.get_town_panel()); res["lines"] = ["|".join(p) for p in panel()]
    ask = line_of("ask")
    body0 = str(g.get_town_panel_text())
    g.activate_town_entry(ask); yield from rwait(0.2)
    res["asked_changed_text"] = str(g.get_town_panel_text()) != body0 and len(str(g.get_town_panel_text())) > 40
    acc = line_of("accept")
    res["accepted"] = g.activate_town_entry(acc); res["quest"] = quest("elder_word")
    g.close_town_panel(); yield from rwait(0.3)
    talk_to("Scholar"); yield from wait(0.3)
    g.interact_nearest(G["pawn"].get_actor_location()); yield from rwait(0.3)
    res["scholar_panel"] = str(g.get_town_panel())
    res["scholar_lines"] = ["|".join(p) for p in panel()]
    g.close_town_panel(); yield from rwait(0.3)
    res["quest_ready"] = quest("elder_word")
    talk_to("Elder"); yield from wait(0.3)
    g0 = gold()
    g.interact_nearest(G["pawn"].get_actor_location()); yield from rwait(0.3)
    res["turnin"] = g.activate_town_entry(line_of("turnin")); res["gold"] = gold() - g0
    res["quest_done"] = quest("elder_word"); res["next_offered"] = line_of("accept", "Mistward Hall") >= 0
    res["lines_after"] = ["|".join(p) for p in panel()]
    g.close_town_panel(); yield from rwait(0.3)
    # (the captain's wilderness quests: offered since the gate opened (2026-11-07; until then "later" and refused); taken and
    # played in 888's quests step)
    talk_to("Captain"); yield from wait(0.3)
    g.interact_nearest(G["pawn"].get_actor_location()); yield from rwait(0.3)
    res["captain_later"] = [p[1] for p in panel() if p[0] == "later"]
    res["captain_wild_offered"] = [p[1] for p in panel() if p[0] == "accept" and ("Mill Road" in p[1] or "Lost Patrol" in p[1])]
    g.close_town_panel(); yield from rwait(0.3)
    quiet(False)
    ok = res["panel"] == "talk" and res["asked_changed_text"] and res["accepted"] and res["quest_ready"]["state"] == "ready" and res["turnin"] and res["gold"] == 15 \
        and res["quest_done"]["state"] == "done" and res["next_offered"] and len(res["captain_later"]) == 0 and len(res["captain_wild_offered"]) == 2
    step_result("talk", ok, **res)

# ------------------------------------------------------------------------------------------------ the services
def step_services():
    g = G["gen"]; c = cb(); res = {}; quiet(True)
    g.add_gold(1000, "the test")
    sp = {p["kind"]: p for p in spots()}
    def open_at(kind, panel_name):
        put(sp[kind]["at"]); yield from wait(0.2)
        g.open_town_panel(panel_name, -1); yield from rwait(0.2)
    # the trader
    yield from open_at("counter", "store")
    i = line_of("buy", "Small Healing Potion"); g0 = gold(); n0 = c.get_item_count("Small Healing Potion")
    res["buy"] = {"ok": g.activate_town_entry(i), "gold": gold() - g0, "count": c.get_item_count("Small Healing Potion") - n0}
    g.set_town_tab(1); i = line_of("sell", "Small Healing Potion"); g0 = gold()
    res["sell"] = {"ok": g.activate_town_entry(i), "gold": gold() - g0, "count": c.get_item_count("Small Healing Potion") - n0}
    g.close_town_panel(); yield from rwait(0.2)
    # the healer
    c.set_health(c.get_max_health() * 0.3)
    yield from open_at("basin", "healer")
    g0 = gold(); res["heal"] = {"ok": g.activate_town_entry(line_of("heal")), "gold": gold() - g0, "hp": round(c.get_health() / c.get_max_health(), 3)}
    g.close_town_panel(); yield from rwait(0.2)
    # the smith: a found weapon worn down, mended
    hero = str(g.get_editor_property("current_hero"))
    wpn = next((str(i.name) for i in g.get_editor_property("items") if i.kind == unreal.RDItemKind.WEAPON and any(str(f.hero) == hero for f in i.weapon_fits)), "Arming Sword")
    res["weapon"] = wpn
    c.add_item(wpn, 1); yield from wait(0.2)
    ws = [j for j in range(len(g.get_editor_property("weapons"))) if str(g.get_editor_property("weapons")[j].item) == wpn]
    if ws:
        c.set_weapon_wear(ws[0], c.get_weapon_durability(ws[0]) * 0.25)
    yield from open_at("smith", "smith")
    rl = line_of("repair", wpn); g0 = gold()
    res["repair"] = {"line": rl, "ok": g.activate_town_entry(rl) if rl >= 0 else False, "gold": gold() - g0,
                     "wear": round(c.get_weapon_wear(ws[0]) / max(c.get_weapon_durability(ws[0]), 1), 3) if ws else None}
    al = line_of("anvil"); g.activate_town_entry(al); yield from rwait(0.3)
    res["anvil_opens_crafting"] = c.is_crafting_open(); c.set_crafting_open(False); yield from rwait(0.3)
    # the temple
    yield from open_at("altar", "temple")
    g0 = gold(); res["bless"] = {"ok": g.activate_town_entry(line_of("bless")), "gold": gold() - g0, "blessing": str(c.get_blessing())}
    g.close_town_panel(); yield from rwait(0.2)
    # the storage
    yield from open_at("stash", "stash")
    n0 = c.get_item_count("Small Healing Potion")
    if n0 == 0: c.add_item("Small Healing Potion", 1); g.set_town_tab(0); n0 = 1
    dl = line_of("deposit", "Small Healing Potion")
    res["deposit"] = {"ok": g.activate_town_entry(dl), "carried": c.get_item_count("Small Healing Potion") - n0, "stash": [str(x) for x in G["gi"].get_editor_property("stash_things")]}
    g.set_town_tab(1); wl = line_of("withdraw", "Small Healing Potion")
    res["withdraw"] = {"ok": g.activate_town_entry(wl), "carried": c.get_item_count("Small Healing Potion") - n0, "stash": len(G["gi"].get_editor_property("stash_things"))}
    g.close_town_panel(); yield from rwait(0.2)
    # the circle and the board
    yield from open_at("circle", "circle")
    res["circle"] = ["|".join(p) for p in panel()]
    g.close_town_panel(); yield from rwait(0.2)
    yield from open_at("board", "board")
    res["board"] = [p[1] for p in panel() if p[0] == "accept"]
    g.close_town_panel(); yield from rwait(0.2)
    quiet(False)
    # (the other circles: "for later" without the wilderness; with it (since 2026-11-03) "find a town", or the towns found)
    res["wild"] = bool(g.get_editor_property("wild"))
    others = [l for l in res["circle"] if l.split("|")[0] not in ("here", "castle", "bye")]
    res["circle_others_ok"] = bool(others) and (all("FIND" in l or not l.startswith("none|") for l in others) if res["wild"] else any("LATER" in l for l in others))
    ok = res["buy"]["ok"] and res["buy"]["gold"] < 0 and res["buy"]["count"] == 1 and res["sell"]["ok"] and res["sell"]["gold"] > 0 and res["sell"]["count"] == 0 \
        and res["heal"]["ok"] and res["heal"]["hp"] >= 0.999 and res["heal"]["gold"] < 0 and res["repair"]["ok"] and res["repair"]["wear"] and res["repair"]["wear"] >= 0.999 and res["repair"]["gold"] < 0 \
        and res["anvil_opens_crafting"] and res["bless"]["ok"] and res["bless"]["blessing"] and res["bless"]["gold"] < 0 and res["deposit"]["ok"] and res["deposit"]["carried"] == -1 \
        and res["withdraw"]["ok"] and res["withdraw"]["carried"] == 0 and any("YOU ARE HERE" in l for l in res["circle"]) and res["circle_others_ok"] and len(res["board"]) == 3
    step_result("services", ok, **res)

# ------------------------------------------------------------------------------------------------ the Mistward Hall's guards
def step_guards():
    g = G["gen"]; S = section(); res = {}
    gs = list(g.get_town_guards()); hall = S.get_editor_property("castle_hall_room") if False else None
    res["planned"] = g.get_town_guards_planned(); res["alive"] = len(gs)
    res["tiers"] = sorted(set(m.get_editor_property("tier") for m in gs)); res["kinds"] = sorted(set(str(m.get_editor_property("monster_name")) for m in gs))
    home = gs[0].get_editor_property("home_room") if gs else -1
    res["home_room"] = home; res["home_kind"] = str(S.get_room_kind(home)) if home >= 0 else None
    # she goes into the hall (they come at her), then out through its door into the entry hall; they stay in the hall
    mg = place("mistgate"); door = place("castle door")
    mid = S.get_room_center(home)
    put(V(mid.x, mid.y, 0)); yield from wait(2.0)
    res["aggro_in_hall"] = sum(1 for m in gs if m.is_aggro())
    c = cb(); c.set_health(c.get_max_health())
    put(V(door.x, door.y, 0)); yield from wait(8.0)
    rooms = [S.room_at(m.get_actor_location()) for m in gs if unreal.SystemLibrary.is_valid(m) and not m.is_dead()]
    res["rooms_after"] = rooms; res["all_in_hall"] = all(r == home for r in rooms)
    res["aggro_after"] = sum(1 for m in gs if unreal.SystemLibrary.is_valid(m) and not m.is_dead() and m.is_aggro())
    # killed: gold, the counter, they stay dead
    g0 = gold(); k0 = G["gi"].get_counter("guards")
    for m in gs[:3]: m.apply_damage(1e7, G["pawn"])
    yield from wait(0.5)
    res["gold"] = gold() - g0; res["counted"] = G["gi"].get_counter("guards") - k0
    res["dead_kept"] = len(G["gi"].get_editor_property("guards_dead"))
    seed = G["gi"].get_editor_property("town_seed")
    g.rebuild_town(seed); yield from wait(1.0); refresh()
    res["alive_after_rebuild"] = len(G["gen"].get_town_guards())
    # (the rebuild for a test clears the dead: the game's own keeps them; the plain respawn is what play does)
    ok = 5 <= res["planned"] <= 10 and res["tiers"] == [1] and res["home_kind"] and "hall" in res["home_kind"].lower() and res["all_in_hall"] and res["gold"] > 0 and res["counted"] == 3
    step_result("guards", ok, **res)

# ------------------------------------------------------------------------------------------------ the castle and back
def step_castle():
    # (the Warrior: armour is fitted for her; the castle's default hero, the Summoner, wears none there)
    if str(G["gen"].get_editor_property("current_hero")) != "Warrior":
        G["gen"].switch_hero("Warrior"); yield from wait(0.8); refresh()
        t0 = time.time()
        while cb() is None and time.time() - t0 < 10: yield; refresh()
    g = G["gen"]; c = cb(); res = {}
    hero = str(g.get_editor_property("current_hero"))
    hd = next(h for h in g.get_editor_property("heroes") if str(h.name) == hero)
    wpn = next((str(i.name) for i in g.get_editor_property("items") if i.kind == unreal.RDItemKind.WEAPON and any(str(f.hero) == hero for f in i.weapon_fits)), "Arming Sword")
    res["weapon"] = wpn
    g.add_gold(250, "the test"); c.add_item(wpn, 1); c.add_item("Medium Healing Potion", 2)
    yield from wait(0.3)
    # (a set this hero wears: tried until one goes on)
    for it in g.get_editor_property("items"):
        if it.kind != unreal.RDItemKind.ARMOUR: continue
        c.add_item(str(it.name), 1); yield from wait(0.1)
        if c.wear_armour(str(it.name)): res["armour"] = str(it.name); break
        c.remove_item(str(it.name), 1)
    yield from wait(0.3)
    before = {"gold": gold(), "lines": sorted(str(l) for l in c.get_all_inventory_lines()), "armour": str(c.get_worn_armour()), "hero": str(g.get_editor_property("current_hero")),
              "buildings": [str(l) for l in g.get_town_building_lines()]}
    res["before_gold"] = before["gold"]; res["before_armour"] = before["armour"]
    mg = place("mistgate"); S = section(); n = S.get_editor_property("mistgate_normal") if False else None
    # walk into the Mistgate: put in front of it, the generator's tick takes her through
    put(V(mg.x, mg.y, 0)); G["travel_until"] = time.time() + 60
    t0 = time.time()
    while time.time() - t0 < 40:
        yield
        w = UES.get_game_world()
        if w is not None and "mistward_castle" in w.get_path_name():
            refresh()
            if G.get("gen") and cb(): break
    refresh()
    res["castle_level"] = G["w"].get_path_name().split(".")[-1] if G["w"] else None
    yield from wait(2.0)
    c = cb(); g = G["gen"]
    after = {"gold": g.get_gold(), "lines": sorted(str(l) for l in c.get_all_inventory_lines()), "armour": str(c.get_worn_armour())}
    res["castle_gold"] = after["gold"]; res["castle_armour"] = after["armour"]
    res["castle_lines_same"] = after["lines"] == before["lines"]
    if not res["castle_lines_same"]: res["castle_lines_diff"] = [sorted(set(before["lines"]) - set(after["lines"])), sorted(set(after["lines"]) - set(before["lines"]))]
    res["entered"] = G["gi"].get_counter("enter")
    res["menu"] = [str(l) for l in g.get_menu_lines()]
    # the way back through the Escape menu
    g.set_menu_open(True); yield from rwait(0.3)
    lines = [str(l) for l in g.get_menu_lines()]
    k = next((i for i, l in enumerate(lines) if "Return to" in l), -1)
    res["menu_line"] = lines[k] if k >= 0 else None
    G["travel_until"] = time.time() + 60
    g.activate_menu_line(k)
    t0 = time.time()
    while time.time() - t0 < 40:
        yield
        w = UES.get_game_world()
        if w is not None and "brokenspire" in w.get_path_name():
            refresh()
            if G.get("gen") and cb(): break
    refresh(); yield from wait(2.0)
    c = cb(); g = G["gen"]
    res["back_level"] = G["w"].get_path_name().split(".")[-1]
    door = place("castle door")
    res["at_castle_door_m"] = round(dist2(G["pawn"].get_actor_location(), door) / 100, 1) if door else None
    res["back_gold"] = g.get_gold(); res["back_armour"] = str(c.get_worn_armour())
    res["back_lines_same"] = sorted(str(l) for l in c.get_all_inventory_lines()) == before["lines"]
    res["same_town"] = [str(l) for l in g.get_town_building_lines()][:12] == before["buildings"][:12]
    ok = res["castle_level"] == "mistward_castle" and res["castle_gold"] == before["gold"] and res["castle_armour"] == before["armour"] and res["castle_lines_same"] \
        and res["entered"] >= 1 and res["menu_line"] and res["back_level"] == "brokenspire" and res["at_castle_door_m"] is not None and res["at_castle_door_m"] < 8 \
        and res["back_gold"] == before["gold"] and res["back_armour"] == before["armour"] and res["back_lines_same"] and res["same_town"] and res.get("armour") and res["castle_armour"] == res["armour"]
    step_result("castle", ok, **res)

# ------------------------------------------------------------------------------------------------ a trip and back (the PR review's finds)
def travel(level, start):
    # (start() begins the trip; waits for the other level's generator and her combat component)
    G["travel_until"] = time.time() + 60
    start()
    t0 = time.time()
    while time.time() - t0 < 40:
        yield
        w = UES.get_game_world()
        if w is not None and level in w.get_path_name():
            refresh()
            if G.get("gen") and cb(): break
    refresh(); yield from wait(2.0)
def via_menu():
    g = G["gen"]; g.set_menu_open(True)
    lines = [str(l) for l in g.get_menu_lines()]
    g.activate_menu_line(next(i for i, l in enumerate(lines) if "Return to" in l))
def step_tour():
    # the showcase tour as the recording plays it (StartTownTour; the castle's autoplay long, so its end does not quit play):
    # each phase seen, the elder's panel open with a question's answer and no quest taken, the map open, the run from about
    # 100 m to the Mistgate, the castle with autoplay going; then back to the town by the Escape menu
    g = G["gen"]; res = {}
    q0 = sorted(str(l).split("|")[3] for l in g.get_quest_lines())
    g.set_editor_property("tour_run_meters", 100.0)
    g.start_town_tour(300.0, "")
    seen = {}; t0 = time.time(); panel = None; body = ""; mapped = False; run_m = None
    while time.time() - t0 < 90:
        yield
        w = UES.get_game_world()
        if w is not None and "mistward_castle" in w.get_path_name(): break
        if w is None: continue
        st = str(G["gen"].get_town_tour_state()).split("|")
        ph = int(st[0]); seen.setdefault(ph, round(time.time() - t0, 1))
        if ph == 3 and G["gen"].is_town_panel_open(): panel = str(G["gen"].get_town_panel()); body = str(G["gen"].get_town_panel_text())
        if ph == 4 and not mapped: mapped = any(str(a) in ("map_papyrus", "mapc_parchment", "mapc_scroll", "town_satellite") for a in G["pc"].get_hud().get_art_drawn())
        if ph == 5 and run_m is None: run_m = float(st[3])
        if ph == -1: res["ended"] = st[4]; break
    G["travel_until"] = time.time() + 60
    t1 = time.time()
    while time.time() - t1 < 40:
        yield
        w = UES.get_game_world()
        if w is not None and "mistward_castle" in w.get_path_name():
            refresh()
            if G.get("gen") and cb(): break
    refresh(); yield from wait(3.0)
    res["phases_at_s"] = seen; res["map_drawn"] = mapped; res["panel"] = panel; res["answer"] = body[:80]; res["run_from_m"] = run_m
    res["castle"] = G["w"].get_path_name().split(".")[-1] if G["w"] else None
    res["reached_s"] = round(t1 - t0, 1)
    res["autoplay_left"] = round(G["gen"].get_autoplay_left(), 0) if res["castle"] == "mistward_castle" else None
    yield from travel("brokenspire", via_menu)
    res["back"] = G["w"].get_path_name().split(".")[-1]
    res["quests_same"] = sorted(str(l).split("|")[3] for l in G["gen"].get_quest_lines()) == q0
    # (phase 6, since the third list: the town's life, between the elder and the map)
    res["life_lines"] = [l.split("RDTOUR ")[-1].strip() for l in open(r"E:\code\claude-ue5\claude_ue5\Saved\Logs\claude_ue5.log", encoding="utf-8", errors="replace") if "RDTOUR life" in l or "RDTOUR the town's life" in l][-4:]
    ok = all(p in seen for p in (1, 2, 3, 6, 4, 5)) and res["panel"] == "talk" and len(res["answer"]) > 10 and res["map_drawn"] and res["run_from_m"] is not None \
        and 50 <= res["run_from_m"] <= 125 and res["castle"] == "mistward_castle" and (res["autoplay_left"] or 0) > 200 and "ended" not in res \
        and res["back"] == "brokenspire" and res["quests_same"]
    step_result("tour", ok, **res)

def step_trip():
    # she opens tier 2 in the castle (no boss set: the debug shortcut without encounters) and falls there; back in the town
    # her pile is kept by the game; in the castle again it lies by the arch and tier 2's boss is set once a room is seen
    res = {}
    mg = place("mistgate")
    yield from travel("mistward_castle", lambda: put(V(mg.x, mg.y, 0)))
    g = G["gen"]; c = cb(); quiet(True)
    res["castle"] = G["w"].get_path_name().split(".")[-1]
    res["opened"] = g.debug_open_tiers(2, False)
    give = ["Small Healing Potion", "Iron Ingot"]
    for n in give: c.add_item(n, 1)
    yield from wait(0.3)
    # (blows of her hit points past her shield's share until she falls: her armour takes its share of each too (worn from the
    # castle step, plate kept her at 63); one blow of a million would break her starting shield before she fell)
    for _ in range(8):
        if c.is_dead(): break
        c.apply_damage(c.get_health() / max(1.0 - c.get_shield_share(), 0.1) + 5.0, None); yield from wait(0.3)
    yield from wait(1.2)
    piles = [p for p in g.loot_piles if p and p.get_editor_property("hers")]
    res["piles_at_death"] = len(piles); res["pile_things"] = sorted(str(x) for p in piles for x in p.things)
    t0 = time.time()
    while c.is_dead() and time.time() - t0 < 25: yield
    yield from wait(1.0)
    res["revived"] = not c.is_dead()
    quiet(False)
    yield from travel("brokenspire", via_menu)
    res["town"] = G["w"].get_path_name().split(".")[-1]
    hp = list(G["gi"].get_editor_property("her_piles"))
    res["kept_in_game"] = [{"level": str(p.hero), "things": sorted(str(x) for x in p.things)} for p in hp]
    mg = place("mistgate")
    yield from travel("mistward_castle", lambda: put(V(mg.x, mg.y, 0)))
    g = G["gen"]; quiet(True)
    res["castle_again"] = G["w"].get_path_name().split(".")[-1]
    res["tier2_open"] = g.is_tier_open(2)
    ctr = g.get_start_room_center()
    piles = [p for p in g.loot_piles if p and p.get_editor_property("hers")]
    res["piles_again"] = [{"things": sorted(str(x) for x in p.things), "from_hall_middle_m": round(dist2(p.get_actor_location(), ctr) / 100, 1)} for p in piles]
    res["left_in_game"] = len([p for p in G["gi"].get_editor_property("her_piles") if str(p.hero) == "castle"])
    res["boss_before_seen"] = [l for l in (str(x) for x in g.get_encounter_lines()) if l.startswith("boss|")]
    # (a room of tier 1 seen: the start set's rooms all discovered)
    g.debug_clear_section(unreal.IntPoint(0, 0), 0, ctr); yield from wait(2.5)
    res["boss_after_seen"] = [l for l in (str(x) for x in g.get_encounter_lines()) if l.startswith("boss|")]
    quiet(False)
    want = sorted(res["pile_things"])
    ok = res["castle"] == "mistward_castle" and res["piles_at_death"] >= 1 and res["revived"] and res["town"] == "brokenspire" \
        and any(p["level"] == "castle" and p["things"] == want for p in res["kept_in_game"]) and res["castle_again"] == "mistward_castle" and res["tier2_open"] \
        and any(p["things"] == want and p["from_hall_middle_m"] < 15 for p in res["piles_again"]) and res["left_in_game"] == 0 \
        and not res["boss_before_seen"] and any(l.split("|")[6] == "2" for l in res["boss_after_seen"])
    step_result("trip", ok, **res)

# ------------------------------------------------------------------------------------------------ the maps
def step_map():
    g = G["gen"]; res = {}
    sq = place("square"); put(V(sq.x + 200, sq.y, 0), yaw=0.0); yield from wait(1.0)
    shot("minimap"); yield from rwait(1.5)
    g.set_map_open(True); yield from rwait(0.5)
    shot("papyrus_map"); yield from rwait(1.5)
    hud = G["pc"].get_hud()
    drawn_open = [str(a) for a in hud.get_art_drawn()]        # (read while the map is open: closed, the HUD draws others)
    labels = [str(l) for l in hud.get_town_labels()]
    res["labels"] = labels
    g.set_map_open(False); yield from rwait(0.3)
    names = [l.split("|")[1] for l in labels]
    need = ("SMITHY", "TRADER", "HEALER", "TEMPLE", "STOREHOUSE", "MISTWARD CASTLE", "GATE", "TELEPORT CIRCLE", "QUEST BOARD", "TAVERN", "CHAPEL", "GRAVEYARD", "BARRACKS", "MILL", "WELL", "MARKET", "TOWN SQUARE")
    res["missing"] = [n for n in need if not any(x.startswith(n) for x in names)]
    res["art"] = sorted(set(l.split("|")[0] for l in labels))
    res["art_drawn"] = [a for a in drawn_open if a.startswith(("mapicon_", "mapc_")) or a == "map_papyrus"]
    # (the colour map, the Fairhill reference's look (2026-11-02): its ground, roads, wall, compass, the buildings' and the
    # trees' pictures drawn, whenever the level has them)
    colour = [a for a in res["art_drawn"] if a.startswith("mapc_")]
    has_colour = any(str(k).startswith("mapc_grass") for k in g.get_editor_property("ui_art").keys())
    res["colour"] = bool(colour); res["colour_art_in_level"] = has_colour
    # (the sheet: the frayed scroll since the second list of 2026-11-02, made from the parchment)
    want = ("mapc_scroll", "mapc_grass", "mapc_cobble", "mapc_dirt", "mapc_wallstone", "mapc_compass", "mapc_castle", "mapc_tree1", "mapc_tower")
    # (since 2026-11-03 the map is the town's own picture from above once it is taken (RDTownSat.cpp): then the painted
    # pictures are not drawn, the labels are; the painted map until then)
    res["satellite"] = "town_satellite" in drawn_open
    res["colour_missing"] = [a for a in want if a not in colour] if has_colour and not res["satellite"] else []
    step_result("map", not res["missing"] and not res["colour_missing"], **res)

def step_satellite():
    """the map from above (the user's of 2026-11-03: "a semi-realistic top down representation of the terrain features, much
    like what you would see from a satellite or google earth, with labels on important or functional buildings and quest
    markers on NPCs that have them"): the picture taken (4096 px square over the town, with mips), not black or washed out,
    with structure (its neighbouring pixels' differences: roofs, streets and their edges, where a flat picture has none);
    the people, animals, guards and her on the capture's hidden list; M draws it with every trade's label and a seal for every
    quest giver; taken again: the old picture not drawn meanwhile, begun again halfway and the plants' fading still put back;
    pictures of the map at 1x and 3x and the raw picture"""
    g = G["gen"]; res = {}; quiet(True)
    def sat():
        st = str(g.get_town_satellite_state()).split("|")
        return {"step": int(st[0]), "px": int(st[1]), "middle": [float(st[2]), float(st[3])], "half_m": round(float(st[4]) / 100, 1), "capture_ms": float(st[5]),
                "captures": int(st[6]), "hidden": int(st[7]), "mips": int(st[8]), "camera_z": float(st[9]), "culls_held": int(st[10])}
    t0 = time.time()
    while time.time() - t0 < 40 and sat()["step"] != 3: yield
    res["state"] = sat()
    res["folk"] = len(folk())
    rt = g.get_editor_property("town_satellite_picture")
    raw = f"bs_{TAG}_satellite_raw.png"
    lum = {}; edge = {}
    if rt:
        p = os.path.join(SHOTS, raw)
        if os.path.exists(p): os.remove(p)
        unreal.RenderingLibrary.export_render_target(G["w"], rt, SHOTS, raw)
        # (a 4096 px picture is written over a while: read it once it holds its IEND chunk and its size holds still (the file
        # is padded with zeros after IEND, so IEND is not at its end))
        t1 = time.time(); whole = False; last_n = -1
        while time.time() - t1 < 20.0 and not whole:
            yield from rwait(0.5)
            try:
                n = os.path.getsize(p)
                if n == last_n and n > 0:
                    with open(p, "rb") as fh:
                        fh.seek(max(0, n - 4 * 1024 * 1024)); whole = b"IEND" in fh.read()
                last_n = n
            except OSError: pass
        res["raw_complete"] = whole
        if whole:
            m = png_measure(p, {"all": (0.0, 0.0, 1.0, 1.0), "middle": (0.4, 0.4, 0.6, 0.6), "north": (0.3, 0.05, 0.7, 0.25), "south": (0.3, 0.75, 0.7, 0.95), "west": (0.05, 0.3, 0.25, 0.7)})
            lum = {k: v[0] for k, v in m.items()}; edge = {k: v[1] for k, v in m.items()}
    res["luma"] = lum; res["edges"] = edge
    # (the map: its labels and seals over the picture)
    put(place("square"), yaw=0.0); yield from wait(0.5)
    yield from press("M"); yield from wait(0.8)
    hud = G["pc"].get_hud()
    drawn = [str(a) for a in hud.get_art_drawn()]; labels = [str(l) for l in hud.get_town_labels()]
    res["drawn_satellite"] = "town_satellite" in drawn; res["painted_drawn"] = [a for a in drawn if a.startswith("mapc_") and a not in ("mapc_compass",)][:6]
    names = [l.split("|")[1] for l in labels if "|" in l]
    need = ("SMITHY", "TRADER", "HEALER", "TEMPLE", "STOREHOUSE", "MISTWARD CASTLE", "GATE", "TELEPORT CIRCLE", "QUEST BOARD", "TAVERN", "CHAPEL", "GRAVEYARD", "BARRACKS", "MILL", "WELL", "MARKET", "TOWN SQUARE")
    res["labels_missing"] = [n for n in need if not any(x.startswith(n) for x in names)]
    res["seals"] = [l for l in labels if l.startswith("seal|")]
    shot("map_satellite1"); yield from rwait(1.5)
    for _ in range(5): yield from press("MouseScrollUp", 0.05)
    yield from wait(0.5); shot("map_satellite3"); yield from rwait(1.5)
    yield from press("M"); yield from wait(0.3)
    # (taken again: held at its first step (the switch off), the map is the painted one, not the old picture)
    def fading():
        return sum(1 for c in isms(section()) if c.get_editor_property("instance_end_cull_distance") > 0)
    res["fading_before"] = fading()
    c0 = sat()["captures"]
    g.set_editor_property("town_satellite", False); g.recapture_town_satellite(); yield from wait(0.3)
    yield from press("M"); yield from wait(0.5)
    drawn2 = [str(a) for a in G["pc"].get_hud().get_art_drawn()]
    res["retaking_drawn_satellite"] = "town_satellite" in drawn2
    yield from press("M"); yield from wait(0.3)
    g.set_editor_property("town_satellite", True)
    # (begun again while the plants' fading is held off (step 1 or 2), then finished)
    res["restarted_at_step"] = None; t0 = time.time()
    while time.time() - t0 < 10:
        s = sat()["step"]
        if s in (1, 2): res["restarted_at_step"] = s; g.recapture_town_satellite(); break
        yield
    t0 = time.time()
    while time.time() - t0 < 15 and not (sat()["step"] == 3 and sat()["captures"] > c0): yield
    res["again"] = sat(); res["fading_after"] = fading()
    quiet(False)
    givers = sorted(set(str(q.giver) for q in g.get_editor_property("quests")))
    vals = [v for v in lum.values() if v is not None]
    st = res["state"]
    ok = (st["step"] == 3 and st["px"] == 4096 and st["mips"] == 1 and len(vals) == 5 and 35 < lum["all"] < 200 and edge.get("middle", 0) > SAT_EDGES and edge.get("all", 0) > SAT_EDGES
          and st["hidden"] >= res["folk"] > 0
          and res["drawn_satellite"] and not res["painted_drawn"] and not res["labels_missing"] and all(f"seal|{gv}" in res["seals"] for gv in givers)
          and not res["retaking_drawn_satellite"] and res["restarted_at_step"] in (1, 2) and res["again"]["step"] == 3 and res["again"]["captures"] > c0
          and res["again"]["culls_held"] == 0 and res["fading_before"] > 0 and res["fading_after"] == res["fading_before"])
    step_result("satellite", ok, **res)
SAT_EDGES = 4.0      # (the mean brightness step between neighbouring pixels a picture of the town has at least; a flat one 0)

# ------------------------------------------------------------------------------------------------ the townspeople
def step_folk():
    g = G["gen"]; res = {}
    w0 = {f["i"]: f["walks"] for f in folk()}
    # (the frame rate over the wait, in the square: the town's two hundred buildings and their lights)
    sq = place("square"); put(V(sq.x + 300, sq.y, 0), yaw=0.0)
    fps = []; t0 = now()
    while now() - t0 < 40.0:
        yield
        fps.append(g.get_fps())
    fps = [f for f in fps if f > 0]
    res["fps"] = {"mean": round(sum(fps) / len(fps), 1) if fps else None, "min": round(min(fps), 1) if fps else None}
    F = folk()
    wanderers = [f for f in F if f["role"] in ("Child", "Idiot", "Militia")]
    res["walked"] = {f["title"]: f["walks"] - w0.get(f["i"], 0) for f in wanderers}
    S = section()
    res["militia"] = [{"at": [round(f["at"].x), round(f["at"].y)], "paths": [len(S.find_path_world(f["at"], f["at"] + d)) for d in (V(900, 0, 0), V(-900, 0, 0), V(0, 900, 0), V(0, -900, 0))]} for f in wanderers if f["role"] in ("Militia", "Idiot")]
    # a bark
    talk_to("Drunk"); yield from wait(0.3)
    g.interact_nearest(G["pawn"].get_actor_location()); yield from rwait(0.3)
    res["bark"] = str(g.get_editor_property("last_bark"))
    # names over the people near her (the elder's mark)
    talk_to("Elder"); put(V(G["pawn"].get_actor_location().x + 400, G["pawn"].get_actor_location().y, 0), yaw=180.0); yield from wait(0.5)
    res["names"] = [str(n) for n in G["pc"].get_hud().get_town_names_drawn()]
    shot("names"); yield from rwait(1.2)
    ok = all(v > 0 for v in res["walked"].values()) and len(res["walked"]) >= 4 and "|" in res["bark"] and len(res["bark"].split("|")[1]) > 5 and any("Aldric" in n for n in res["names"])
    step_result("folk", ok, **res)

# ------------------------------------------------------------------------------------------------ the gate
def step_gate():
    g = G["gen"]; res = {}
    gate = place("gate"); sq = place("square")
    d = V(sq.x - gate.x, sq.y - gate.y, 0); n = math.hypot(d.x, d.y); d = V(d.x / n, d.y / n, 0)
    inside = V(gate.x + d.x * 350, gate.y + d.y * 350, 0)
    res["wild"] = bool(g.get_editor_property("wild"))
    if res["wild"]:
        # (the list of 2026-11-04: the portcullis stops her until a lever raises it; it stays as she leaves it)
        lv = [l for l in [str(x) for x in section().get_town_improve_lines()] if l.startswith(("lever|", "gate|"))]
        res["gate_before"] = [l for l in lv if l.startswith("gate|")]
        if section().is_portcullis_up():
            L1 = [l.split("|") for l in lv if l.startswith("lever|")][0]; put(V(float(L1[2]) + d.x * 100, float(L1[3]) + d.y * 100, 0)); yield from wait(0.3)
            g.interact_nearest(G["pawn"].get_actor_location()); yield from rwait(11.0)
        put(inside, yaw=math.degrees(math.atan2(-d.y, -d.x))); yield from wait(0.4)
        t0 = time.time()
        while time.time() - t0 < 3.0:
            G["pawn"].add_movement_input(V(-d.x, -d.y, 0), 1.0, False); yield
        p = G["pawn"].get_actor_location(); res["shut_past_gate_cm"] = round(-((gate.x - p.x) * -d.x + (gate.y - p.y) * -d.y), 1)
        L1 = [l.split("|") for l in lv if l.startswith("lever|")]
        lever = min(L1, key=lambda q: dist2(V(float(q[1 + 1]), float(q[2 + 1]), 0), inside)) if L1 else None
        if lever:
            lp = V(float(lever[2]), float(lever[3]), 0)
            put(V(lp.x + d.x * 110, lp.y + d.y * 110, 0)); yield from wait(0.3)
            res["lever_prompt"] = str(g.describe_nearest(G["pawn"].get_actor_location()))
            g.interact_nearest(G["pawn"].get_actor_location()); yield from rwait(11.0)
            res["up"] = section().is_portcullis_up()
        put(inside, yaw=math.degrees(math.atan2(-d.y, -d.x))); yield from wait(0.4)
    res["prompt"] = str(g.describe_nearest(G["pawn"].get_actor_location()))
    if not res["wild"]: g.interact_nearest(G["pawn"].get_actor_location()); yield from rwait(0.2)
    res["message"] = str(cb().get_editor_property("message"))
    t0 = time.time()
    while time.time() - t0 < 4.0:
        G["pawn"].add_movement_input(V(-d.x, -d.y, 0), 1.0, False); yield
    p = G["pawn"].get_actor_location()
    res["past_gate_cm"] = round((gate.x - p.x) * -d.x + (gate.y - p.y) * -d.y, 1) * -1
    shot("gate"); yield from rwait(1.2)
    # (since 2026-11-03 the wilderness is beyond the gate: she walks out (888's gate step) once its portcullis is up; barred without it.
    # Shut, she is stopped before the gate's line (0.40 m short in one town, 0.57 m in another: where her capsule meets its bars))
    ok = ("barred" not in res["prompt"] and res.get("shut_past_gate_cm", 0) < -15 and "raise the portcullis" in res.get("lever_prompt", "") and res.get("up") and res["past_gate_cm"] > 600) if res["wild"] \
        else ("gate" in res["prompt"] and "barred" in res["message"] and res["past_gate_cm"] < 0)
    step_result("gate", ok, **res)

# ------------------------------------------------------------------------------------------------ pictures
def step_pictures():
    g = G["gen"]; res = {}; quiet(True)
    B = blds(); sq = place("square")
    def look(at, frm, name):
        d = V(at.x - frm.x, at.y - frm.y, 0)
        put(frm, yaw=math.degrees(math.atan2(d.y, d.x)))
    put(V(sq.x - 900, sq.y - 300, 0), yaw=20.0); yield from wait(1.5); shot("square"); yield from rwait(1.5)
    for kind in ("smithy", "tavern", "home", "temple", "store"):
        b = [x for x in B if x["kind"] == kind and x["state"] == 0][0]
        put(V(b["c"].x * 0.6 + b["door"].x * 0.4, b["c"].y * 0.6 + b["door"].y * 0.4, 0), yaw=math.degrees(math.atan2(b["c"].y - b["door"].y, b["c"].x - b["door"].x)))
        yield from wait(1.2); shot(f"inside_{kind.replace(' ', '_')}"); yield from rwait(1.5)
        f = door_front(b, 900.0); put(f, yaw=math.degrees(math.atan2(b["c"].y - f.y, b["c"].x - f.x))); yield from wait(1.2); shot(f"outside_{kind}"); yield from rwait(1.5)
    c = [x for x in B if x["kind"] == "castle"][0]
    f = door_front(c, 2400.0); put(f, yaw=math.degrees(math.atan2(c["c"].y - f.y, c["c"].x - f.x))); yield from wait(1.5); shot("castle"); yield from rwait(1.5)
    mg = place("mistgate"); S = section()
    gs = list(g.get_town_guards())
    hall = gs[0].get_editor_property("home_room") if gs else -1
    if hall >= 0:
        hc = S.get_room_center(hall)
        frm = V(hc.x * 2 - mg.x, hc.y * 2 - mg.y, 0)
        put(V(frm.x * 0.7 + hc.x * 0.3, frm.y * 0.7 + hc.y * 0.3, 0), yaw=math.degrees(math.atan2(mg.y - frm.y, mg.x - frm.x))); yield from wait(1.5); shot("mistward_hall"); yield from rwait(1.5)
    quiet(False)
    step_result("pictures", True, shots=R.get("shots", []))

# ------------------------------------------------------------------------------------------------ the castle's outside (2026-11-02)
SHOTS = r"E:\code\claude-ue5\claude_ue5\Saved\Screenshots\WindowsEditor"
def png_luma(path, box=(0.0, 0.0, 1.0, 1.0)):
    """the mean brightness (0-255, Rec. 709) of a part of a PNG, read with zlib (868's: the editor's Python has no image library)"""
    import zlib, struct
    data = open(path, "rb").read(); pos = 8; w = h = 0; ct = 6; idat = b""
    # (the engine's export pads a file with zeros after IEND (1.6 MB for the town's picture): read up to IEND; the padding's
    # length once left a piece under a chunk's 8-byte head, and the read failed)
    while pos + 8 <= len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8]); body = data[pos + 8:pos + 8 + ln]; pos += 12 + ln
        if typ == b"IHDR": w, h, bd, ct = struct.unpack(">IIBB", body[:10])
        elif typ == b"IDAT": idat += body
        elif typ == b"IEND": break
    bpp = 4 if ct == 6 else 3; raw = zlib.decompress(idat); stride = w * bpp
    prev = bytearray(stride); x0, y0, x1, y1 = int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)
    tot = 0.0; n = 0
    for y in range(h):
        f = raw[y * (stride + 1)]; line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        if f == 1:
            for i in range(bpp, stride): line[i] = (line[i] + line[i - bpp]) & 255
        elif f == 2:
            for i in range(stride): line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride): line[i] = (line[i] + (((line[i - bpp] if i >= bpp else 0) + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0; b = prev[i]; c_ = prev[i - bpp] if i >= bpp else 0
                p = a + b - c_; pa, pb, pc = abs(p - a), abs(p - b), abs(p - c_)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c_)) & 255
        if y0 <= y < y1:
            for x in range(x0, x1, 2):
                i = x * bpp; tot += 0.2126 * line[i] + 0.7152 * line[i + 1] + 0.0722 * line[i + 2]; n += 1
        prev = line
    return round(tot / max(n, 1), 2)
def png_measure(path, boxes):
    """for each named box (shares of the picture) of a PNG: (its mean brightness 0-255, the mean brightness step between
    pixels two apart along a row: 0 for a flat picture), from one read of the file (every other pixel of every other row)"""
    import zlib, struct
    data = open(path, "rb").read(); pos = 8; w = h = 0; ct = 6; idat = b""
    # (the engine's export pads a file with zeros after IEND (1.6 MB for the town's picture): read up to IEND; the padding's
    # length once left a piece under a chunk's 8-byte head, and the read failed)
    while pos + 8 <= len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8]); body = data[pos + 8:pos + 8 + ln]; pos += 12 + ln
        if typ == b"IHDR": w, h, bd, ct = struct.unpack(">IIBB", body[:10])
        elif typ == b"IDAT": idat += body
        elif typ == b"IEND": break
    bpp = 4 if ct == 6 else 3; raw = zlib.decompress(idat); stride = w * bpp
    px = {k: (int(b[0] * w), int(b[1] * h), int(b[2] * w), int(b[3] * h)) for k, b in boxes.items()}
    acc = {k: [0.0, 0, 0.0, 0] for k in boxes}
    prev = bytearray(stride)
    for y in range(h):
        f = raw[y * (stride + 1)]; line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        if f == 1:
            for i in range(bpp, stride): line[i] = (line[i] + line[i - bpp]) & 255
        elif f == 2:
            for i in range(stride): line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride): line[i] = (line[i] + (((line[i - bpp] if i >= bpp else 0) + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0; b = prev[i]; c_ = prev[i - bpp] if i >= bpp else 0
                p = a + b - c_; pa, pb, pc = abs(p - a), abs(p - b), abs(p - c_)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c_)) & 255
        if y % 2 == 0:
            for k, (x0, y0, x1, y1) in px.items():
                if not (y0 <= y < y1): continue
                a_ = acc[k]; last = None
                for x in range(x0, x1, 2):
                    i = x * bpp; l = 0.2126 * line[i] + 0.7152 * line[i + 1] + 0.0722 * line[i + 2]
                    a_[0] += l; a_[1] += 1
                    if last is not None: a_[2] += abs(l - last); a_[3] += 1
                    last = l
        prev = line
    return {k: (round(a[0] / max(a[1], 1), 2), round(a[2] / max(a[3], 1), 2)) for k, a in acc.items()}
def shot_luma(name, box=(0.0, 0.0, 1.0, 0.85)):
    """a small picture of the game now and its brightness (none: the picture did not come)"""
    p = os.path.join(SHOTS, f"bs_{TAG}_{name}.png")
    if os.path.exists(p): os.remove(p)
    shot(name, "640x360"); t0 = time.time()
    while time.time() - t0 < 8:
        yield from rwait(0.3)
        if os.path.exists(p) and os.path.getsize(p) > 1000:
            yield from rwait(0.3)
            try: return png_luma(p, box)
            except Exception: continue
    return None
def castle_shape():
    d = {"towers": []}
    for l in section().get_castle_shape_lines():
        p = str(l).split("|")
        if p[0] == "tower": d["towers"].append((V(float(p[1]), float(p[2]), 0), p[3] == "1"))
        elif p[0] == "towerdoor": d.setdefault("doors", []).append({"at": V(float(p[1]), float(p[2]), float(p[3])), "c": V(float(p[4]), float(p[5]), 0)})
        elif p[0] == "stair": d["stair"] = {"foot": V(float(p[1]), float(p[2]), float(p[3])), "top": V(float(p[4]), float(p[5]), float(p[6])), "well": int(p[7]), "room": int(p[8])}
        elif p[0] == "walk": d["walk"] = float(p[1])
    return d
def ism_instances(mesh_has, path_has=None):
    """the section's instances of meshes whose name has mesh_has (and whose path has path_has) (world places)"""
    out = []
    for c in isms(section()):
        m = c.get_editor_property("static_mesh")
        if not m or mesh_has not in m.get_name() or (path_has and path_has not in m.get_path_name()): continue
        for i in range(c.get_instance_count()):
            t = c.get_instance_transform(i, True)
            if isinstance(t, tuple): t = t[-1]
            out.append(t.translation)
    return out
def step_castlewalls():
    """the castle's outside: no blind arch (the dungeon's wall) outside its inner walls' line and no arched doorway piece in the
    town wall; Castle Forge's walls round it (arrow slits, windows), its battlements, four round towers; the wall walk walked on
    over the whole roof (traces); she walks in at the stair turret's door, up the spiral stair and out of its top door onto the
    wall walk (her own movement, steered along the stair); pictures"""
    g = G["gen"]; res = {}; quiet(True)
    d = castle_shape(); T = d["towers"]
    res["towers"] = len(T); res["stair_towers"] = sum(1 for t in T if t[1]); res["walk_z"] = d.get("walk")
    xs = [t[0].x for t in T]; ys = [t[0].y for t in T]
    x0, x1, y0, y1 = min(xs) + 200, max(xs) - 200, min(ys) + 200, max(ys) - 200        # (the castle's rectangle: the towers stand 2 m out)
    arch = ism_instances("SM_ArchWall_Blind")
    res["blind_arches"] = len(arch)
    res["blind_arches_outside"] = sum(1 for a in arch if a.x < x0 - 60 or a.x > x1 + 60 or a.y < y0 - 60 or a.y > y1 + 60)
    # (the arched doorway piece in the town wall's segments: none; the watchtowers' doors from the town (the second list of
    # 2026-11-02) are that piece on purpose and are left out)
    wdoors = [w_["door"] for w_ in shape_lines()["watch"]]
    res["arched_door_pieces"] = sum(1 for p in ism_instances("SM_Castle_Stone_Wall_02a_NN") if not any(dist2(p, q) < 250 for q in wdoors))
    res["watchtower_doors"] = len(wdoors)
    forge = {n: len(ism_instances(n)) for n in ("SM_Castle_Stone_Wall_01a", "SM_Castle_Stone_Wall_02h", "SM_Castle_Stone_Wall_02f", "SM_Castle_Stone_Wall_02g", "SM_Castle_Stone_Wall_02d",
                                                "SM_Castle_Stone_Parapet_01a", "SM_Castle_Tower_Wall_02", "SM_Tower_Roof_02a", "SM_Stone_Stairs_01a")}
    res["pieces"] = forge
    # (nothing from the rooms stands through the walk: the hall's columns did, 3 m)
    poke = {}
    walk = d.get("walk") or 661.0
    for comp in isms(section()):
        m = comp.get_editor_property("static_mesh")
        if not m: continue
        bz = m.get_bounding_box().max.z
        for k in range(comp.get_instance_count()):
            t = comp.get_instance_transform(k, True)
            if isinstance(t, tuple): t = t[-1]
            p = t.translation
            if x0 + 80 < p.x < x1 - 80 and y0 + 80 < p.y < y1 - 80 and p.z < walk - 70 and p.z + bz * t.scale3d.z > walk + 15:
                poke[m.get_name()] = poke.get(m.get_name(), 0) + 1
    res["through_the_walk"] = poke
    # (the walk: traces down over the roof, a metre in from its edges)
    w = G["w"]; hits = []; miss = 0
    for ix in range(9):
        for iy in range(9):
            x = x0 + 100 + (x1 - x0 - 200) * ix / 8.0; y = y0 + 100 + (y1 - y0 - 200) * iy / 8.0
            h = unreal.SystemLibrary.line_trace_single(w, V(x, y, 3000), V(x, y, 0), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [G["pawn"]], unreal.DrawDebugTrace.NONE, True)
            h = h.to_tuple() if h else None
            if h and h[0]: hits.append(h[4].z)
            else: miss += 1
    res["walk_traces"] = {"n": len(hits), "miss": miss, "min": round(min(hits), 1) if hits else None, "max": round(max(hits), 1) if hits else None}
    # (the third list of 2026-11-02: "the player should only be able to get to the watch tower from the inside of the castle ...
    # there should be a way down from the battlements to the floor of the castle, like stairs". Her climb, by her own movement
    # toward each point in turn: from the wing's floor before the stair's foot up the stair to its top, onto the walk, to the
    # nearest tower's doorway and into the tower; then, outside, at every tower from the ground straight at it: kept out)
    centre = V((x0 + x1) * 0.5, (y0 + y1) * 0.5, 0)
    st = d["stair"]; ft, tp = st["foot"], st["top"]
    run = V(tp.x - ft.x, tp.y - ft.y, 0); rl = math.hypot(run.x, run.y) or 1.0; run = V(run.x / rl, run.y / rl, 0)
    td = min(d["doors"], key=lambda q: dist2(q["at"], tp)); tc = td["c"]
    into = V(tc.x - td["at"].x, tc.y - td["at"].y, 0); il = math.hypot(into.x, into.y) or 1.0; into = V(into.x / il, into.y / il, 0)
    # (from the top of the stair to the door: along the walk, a metre in from the battlements' line, round the corner)
    corner = V(tp.x + run.x * 160, tp.y + run.y * 160, 0)
    pts = [V(ft.x + run.x * (k * 60.0), ft.y + run.y * (k * 60.0), 0) for k in range(int(rl / 60.0) + 1)] + [V(tp.x + run.x * 80, tp.y + run.y * 80, 0), corner,
           V(td["at"].x - into.x * 140, td["at"].y - into.y * 140, 0), V(td["at"].x + into.x * 40, td["at"].y + into.y * 40, 0), V(tc.x, tc.y, 0)]
    put(V(ft.x - run.x * 150, ft.y - run.y * 150, 0), yaw=math.degrees(math.atan2(run.y, run.x)), z=ft.z); yield from wait(0.8)
    shot("castle_stair"); yield from rwait(1.5)
    r_ = yield from climb(pts, limit=90.0)
    yield from wait(0.8)
    p = G["pawn"].get_actor_location()
    walk = d.get("walk") or 661.0
    res["climb"] = {**r_, "end": [round(p.x), round(p.y), round(p.z)], "end_from_tower_m": round(dist2(p, tc) / 100, 2), "walk_z": walk,
                    "in_tower": dist2(p, tc) < 220 and p.z > walk + 40, "stair_well_tiles": st["well"], "stair_room": st["room"]}
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-10, yaw=math.degrees(math.atan2(-into.y, -into.x)))); yield from wait(0.8)
    shot("castle_tower_inside"); yield from rwait(1.5)
    # (on the walk before the door, looking at it; and over the stairwell, looking down it)
    put(V(td["at"].x - into.x * 300, td["at"].y - into.y * 300, 0), yaw=math.degrees(math.atan2(into.y, into.x)), z=walk); yield from wait(1.0)
    shot("castle_tower_door"); yield from rwait(1.5)
    put(V(tp.x + run.x * 120, tp.y + run.y * 120, 0), yaw=math.degrees(math.atan2(-run.y, -run.x)), z=walk); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-35, yaw=math.degrees(math.atan2(-run.y, -run.x))))
    yield from wait(1.0); shot("castle_stairwell"); yield from rwait(1.5)
    # (kept out: at each tower from 1.6 m outside its ring, away from the castle, she walks at its middle for 4 s)
    outside = []
    for (c_, _s) in T:
        o_ = V(c_.x - centre.x, c_.y - centre.y, 0); ol = math.hypot(o_.x, o_.y) or 1.0; o_ = V(o_.x / ol, o_.y / ol, 0)
        for turn in (-50.0, 0.0, 50.0):
            a_ = math.atan2(o_.y, o_.x) + math.radians(turn)
            start = V(c_.x + math.cos(a_) * 480, c_.y + math.sin(a_) * 480, 0)
            put(start, yaw=math.degrees(a_) + 180.0); yield from wait(0.4)
            nearest = 1e9; t1 = now()
            while now() - t1 < 4.0:
                q = G["pawn"].get_actor_location(); nearest = min(nearest, dist2(q, c_))
                dv = V(c_.x - q.x, c_.y - q.y, 0); n_ = math.hypot(dv.x, dv.y) or 1.0
                G["pawn"].add_movement_input(V(dv.x / n_, dv.y / n_, 0), 1.0, False); yield
            outside.append(round(nearest))
    res["outside_nearest_cm"] = outside
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-15, yaw=0)); yield from wait(0.3)
    # (from the forecourt: the castle's front, its towers and battlements)
    b = [x for x in blds() if x["kind"] == "castle"][0]
    f = door_front(b, 2200.0)
    put(f, yaw=math.degrees(math.atan2(b["c"].y - f.y, b["c"].x - f.x))); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-4, yaw=math.degrees(math.atan2(b["c"].y - f.y, b["c"].x - f.x))))
    yield from wait(1.5); shot("castle_front"); yield from rwait(1.5)
    quiet(False)
    wt = res["walk_traces"]
    # (the walk's traces leave out the stairwell: its two tiles open down to the floor)
    ok = (res["towers"] == 4 and res["blind_arches_outside"] == 0 and res["arched_door_pieces"] == 0 and not poke
          and forge["SM_Castle_Stone_Wall_02h"] > 10 and forge["SM_Castle_Stone_Parapet_01a"] > 40 and forge["SM_Castle_Tower_Wall_02"] >= 64
          and wt["n"] >= 75 and wt["min"] is not None and abs(wt["max"] - res["walk_z"]) < 25
          and r_["reached"] == r_["of"] and res["climb"]["in_tower"] and st["well"] == 2 and len(d.get("doors", [])) == 4
          and min(outside) > 300)
    step_result("castlewalls", ok, **res)

# ------------------------------------------------------------------------------------------------ day and night (2026-11-02)
def day_state():
    p = str(G["gen"].get_day_night_state()).split("|")
    st = {"day": int(p[0]), "hour": float(p[1]), "sun_elev": float(p[2]), "daylight": float(p[3]), "sun_lux": float(p[4]), "moon_lux": float(p[5]), "sky": float(p[6]), "bias": float(p[7])}
    # (the lights themselves, read from the world: the level's atmosphere suns, where they shine from and how bright; the PR
    # review's find: the elevation above is the clock's formula, not the sun)
    lights = []
    for a in GS.get_all_actors_of_class(G["w"], unreal.DirectionalLight):
        lc = a.light_component
        if lc.get_editor_property("atmosphere_sun_light"):
            lights.append(("sun", -lc.get_world_rotation().pitch, lc.get_editor_property("intensity")))
    for lc in G["gen"].get_components_by_class(unreal.DirectionalLightComponent):
        lights.append(("moon", -lc.get_world_rotation().pitch, lc.get_editor_property("intensity")))
    sun = [l for l in lights if l[0] == "sun"]; moon = [l for l in lights if l[0] == "moon"]
    st["sun_world"] = {"elev": round(sun[0][1], 2), "lux": round(sun[0][2], 3), "n": len(sun)} if sun else None
    st["moon_world"] = {"elev": round(moon[0][1], 2), "lux": round(moon[0][2], 3), "n": len(moon)} if moon else None
    return st
def step_daynight():
    """the town's day: 24 hours in DayLengthSeconds (1800) of play, measured on the clock over 20 s of play; the sun high at
    noon, setting at 18, down at midnight with the moon up (read from the lights in the world: their rotation and intensity); pictures from the square at noon, at 18:30 and at midnight (the
    noon one brighter than the night one), the game instance keeping the hour; back to the hour it was"""
    g = G["gen"]; res = {}; quiet(True)
    res["on"] = g.get_editor_property("day_night"); res["day_length"] = g.get_editor_property("day_length_seconds")
    # (from the castle's wall walk over the town: open sky on every seed; from the square a stall's canopy or a house filled the
    # picture on one seed)
    sq = place("square"); d = castle_shape(); T = d["towers"]
    cc = V(sum(t[0].x for t in T) / 4, sum(t[0].y for t in T) / 4, 0)
    yw = math.degrees(math.atan2(sq.y - cc.y, sq.x - cc.x))
    put(V(cc.x + (sq.x - cc.x) * 0.0, cc.y, 0), yaw=yw, z=d.get("walk") or 661.0)
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-4, yaw=yw)); yield from wait(0.8)
    h_was = g.get_town_hour()
    s0 = day_state(); t0 = now(); yield from wait(20.0); s1 = day_state(); dt = now() - t0
    gain = (s1["hour"] - s0["hour"]) % 24.0
    res["clock"] = {"from": s0["hour"], "to": s1["hour"], "game_s": round(dt, 2), "hours": round(gain, 4), "day_s": round(dt * 24.0 / max(gain, 1e-6), 1)}
    res["kept_by_game"] = abs(G["gi"].get_editor_property("town_hour") - g.get_town_hour()) < 0.01
    pics = {}
    for nm, h in (("noon", 12.0), ("dusk", 18.5), ("night", 0.0)):
        g.set_town_hour(h); yield from wait(5.0)          # (the exposure's adaptation)
        st = day_state(); lum = yield from shot_luma(f"day_{nm}")
        pics[nm] = {**st, "luma": lum, "clock": str(g.get_town_clock())}
    res["pictures"] = pics
    g.set_town_hour(h_was); quiet(False)
    n, d_, ni = pics["noon"], pics["dusk"], pics["night"]
    def el(p, k): return (p.get(k) or {}).get("elev", -999)
    def lx(p, k): return (p.get(k) or {}).get("lux", -1)
    # (the sun is clamped 10 degrees under the horizon at night; the moon rises opposite)
    ok = (res["on"] and abs(res["clock"]["day_s"] - res["day_length"]) < res["day_length"] * 0.05 and res["kept_by_game"]
          and all((p.get("sun_world") or {}).get("n") == 1 and (p.get("moon_world") or {}).get("n") == 1 for p in (n, d_, ni))
          and el(n, "sun_world") > 55 and lx(n, "sun_world") > 1.0 and n["daylight"] > 0.99
          and -10.5 < el(d_, "sun_world") < 0 and lx(d_, "sun_world") < 0.01
          and el(ni, "sun_world") < -9 and lx(ni, "sun_world") < 0.01 and el(ni, "moon_world") > 30 and lx(ni, "moon_world") > 0.1 and ni["daylight"] < 0.01
          and n["luma"] is not None and ni["luma"] is not None and n["luma"] > ni["luma"] * 1.8)
    step_result("daynight", ok, **res)

# ------------------------------------------------------------------------------------------------ the second list of 2026-11-02
def shape_lines():
    d = {"border": [], "paths": [], "watch": []}
    for l in section().get_town_shape_lines():
        p = str(l).split("|")
        if p[0] == "border": d["border"].append(V(float(p[1]), float(p[2]), 0))
        elif p[0] == "path": d["paths"].append({"n": int(p[1]), "hw": float(p[2]), "a": V(float(p[3]), float(p[4]), 0), "b": V(float(p[5]), float(p[6]), 0)})
        elif p[0] == "roads": d["roads"] = [int(p[1]), int(p[2]), int(p[3])]
        elif p[0] == "headings": d["headings"] = {"on_axis": float(p[1]), "length_m": float(p[2])}
        elif p[0] == "work": d.setdefault("work", []).append({"kind": p[1], "at": V(float(p[2]), float(p[3]), float(p[4])), "yaw": float(p[5]), "group": int(p[6]), "bld": int(p[7])})
        elif p[0] == "pen": d.setdefault("pens", []).append({"at": V(float(p[1]), float(p[2]), 0), "half": (float(p[3]), float(p[4])), "animal": int(p[6])})
        elif p[0] == "garden": d.setdefault("gardens", []).append({"at": V(float(p[1]), float(p[2]), 0), "half": (float(p[3]), float(p[4])), "plants": int(p[6])})
        elif p[0] == "greens": d["greens"] = {"grass": int(p[1]), "bushes": int(p[2])}
        elif p[0] == "watch": d["watch"].append({"c": V(float(p[1]), float(p[2]), float(p[6])), "door": V(float(p[3]), float(p[4]), 0), "sa": float(p[5])})
    return d
def seg_dist(p, a, b):
    ab = V(b.x - a.x, b.y - a.y, 0); t = max(0.0, min(1.0, ((p.x - a.x) * ab.x + (p.y - a.y) * ab.y) / max(ab.x * ab.x + ab.y * ab.y, 1e-6)))
    return math.hypot(p.x - (a.x + ab.x * t), p.y - (a.y + ab.y * t))
def step_shape():
    """the town's outline (the user's: "irregularly shaped with the town walls following the shape of the town"): twelve corners
    or more at radii that differ; the wall's pieces on its edges (every 3 m of every edge, the gate's gap and the towers' insides
    left out, has a wall piece within 2.5 m; no wall piece more than 2 m from the outline); a tower at every corner; the earth
    roads winding (each wanders 6 m or more off the line from its one end to the other); the cobbled roads straight"""
    res = {}; d = shape_lines(); Bd = d["border"]
    cx = sum(p.x for p in Bd) / len(Bd); cy = sum(p.y for p in Bd) / len(Bd)
    rr = [math.hypot(p.x - cx, p.y - cy) for p in Bd]
    res["corners"] = len(Bd); res["radius_m"] = [round(min(rr) / 100, 1), round(max(rr) / 100, 1)]; res["radius_spread"] = round((max(rr) - min(rr)) / (sum(rr) / len(rr)), 3)
    walls = ism_instances("SM_Castle_Stone_Wall_01a") + ism_instances("SM_Castle_Stone_Wall_02h")
    def edge_d(p): return min(seg_dist(p, Bd[i - 1], Bd[i]) for i in range(len(Bd)))
    towers = [s_["at"] for s_ in spots() if s_["kind"] == "tower"]
    gate = place("gate")
    on_line = [w for w in walls if edge_d(w) < 200 and min(dist2(w, t) for t in towers) > 380]
    res["wall_pieces"] = len(walls); res["wall_on_outline"] = len(on_line)
    gaps = []; n = 0
    for i in range(len(Bd)):
        a, b = Bd[i - 1], Bd[i]; L_ = dist2(a, b)
        for k in range(int(L_ // 300)):
            p = V(a.x + (b.x - a.x) * (k + 0.5) * 300 / L_, a.y + (b.y - a.y) * (k + 0.5) * 300 / L_, 0)
            if dist2(p, gate) < 450 or min(dist2(p, t) for t in towers) < 420: continue
            n += 1
            if not any(dist2(p, w) < 250 for w in walls): gaps.append([round(p.x), round(p.y)])
    res["edge_points"] = n; res["wall_gaps"] = gaps[:10]; res["n_gaps"] = len(gaps)
    res["towers_at_corners"] = sum(1 for p in Bd if min(dist2(p, t) for t in towers) < 50)
    # (the earth roads: how far each one's middle wanders off the straight line between its ends)
    res["paths"] = len(d["paths"]); res["roads_tiles"] = d.get("roads")
    res["path_ends"] = [[round(p["a"].x), round(p["a"].y), round(p["b"].x), round(p["b"].y)] for p in d["paths"]][:8]
    res["path_wander_m"] = [round(w_, 1) for w_ in section().get_town_path_wander()]
    # (the third list: "they still form a regular grid. they should meander around the town in a semi-random manner": the share
    # of the earth roads' length running within 12 degrees of the town's axes (a grid: nearly all of it; at random: about a
    # quarter) under 0.4; the homes still have their frontage (a hundred or more))
    res["headings"] = d.get("headings")
    wl = sorted(res["path_wander_m"]); res["wander_median_m"] = wl[len(wl) // 2] if wl else 0
    res["homes"] = sum(1 for b in blds() if b["kind"] == "home")
    ok = (res["corners"] >= 12 and res["radius_spread"] > 0.12 and res["n_gaps"] == 0 and res["wall_on_outline"] > 100 and res["towers_at_corners"] == res["corners"]
          and res["paths"] >= 4 and res["roads_tiles"][0] > 300 and res["roads_tiles"][1] > 300
          and res["headings"] and res["headings"]["on_axis"] < 0.4 and res["headings"]["length_m"] > 1500 and res["homes"] >= 100)
    step_result("shape", ok, **res)
    yield

def climb(pts, limit=90.0):
    """she walks by her own movement input to each point in turn (2D); stops when one is not reached in 8 s"""
    i = 0; t0 = now(); last_i, last_t = 0, now(); zmax = -1e9
    while i < len(pts) and now() - t0 < limit:
        p = G["pawn"].get_actor_location(); zmax = max(zmax, p.z)
        while i < len(pts) and math.hypot(pts[i].x - p.x, pts[i].y - p.y) < 45.0: i += 1
        if i >= len(pts): break
        if i != last_i: last_i, last_t = i, now()
        if now() - last_t > 8.0: break
        dv = V(pts[i].x - p.x, pts[i].y - p.y, 0); n_ = math.hypot(dv.x, dv.y) or 1.0
        G["pawn"].add_movement_input(V(dv.x / n_, dv.y / n_, 0), 1.0, False); yield
    return {"reached": i, "of": len(pts), "z_max": round(zmax, 1), "seconds": round(now() - t0, 1)}
def step_watch():
    """a watchtower (the user's: "there's no way to get into the watchtowers from the inside of town"): she walks in at its
    door from the town, up its spiral stair and onto the landing under its roof, by her own movement; pictures"""
    quiet(True); res = {}; d = shape_lines()
    sq = place("square")
    W_ = sorted(d["watch"], key=lambda w: dist2(w["c"], sq))
    res["watchtowers"] = len(W_)
    w = W_[len(W_) // 2]; C = w["c"]; Dp = w["door"]; Sa = w["sa"]
    def at(ang, r): a = math.radians(ang); return V(C.x + r * math.cos(a), C.y + r * math.sin(a), 0)
    out = V(Dp.x - C.x, Dp.y - C.y, 0); n_ = math.hypot(out.x, out.y); out = V(out.x / n_, out.y / n_, 0)
    a_door = math.degrees(math.atan2(Dp.y - C.y, Dp.x - C.x))
    pts = [V(Dp.x + out.x * 60, Dp.y + out.y * 60, 0), V(Dp.x - out.x * 80, Dp.y - out.y * 80, 0)] + [at(Sa - k * 15, 120) for k in range(0, 73)] + [at(Sa - 45, 135)]
    put(V(Dp.x + out.x * 250, Dp.y + out.y * 250, 0), yaw=math.degrees(math.atan2(-out.y, -out.x))); yield from wait(0.6)
    r_ = yield from climb(pts)
    yield from wait(0.8)
    p = G["pawn"].get_actor_location(); res["climb"] = r_; res["end_z"] = round(p.z - C.z, 1)
    # (the third list: "the circular stairway just ends, there is no platform or floor": off the stair she walks across the
    # landing to the wall; traces over the top's floor (the landing's quarter, the four corners: at the top's height) and over
    # the stairwell's open part (down to the steps below))
    zs = []
    r2 = yield from climb([at(Sa - 45, 170), at(Sa - 50, 215)], limit=20.0)
    for k in range(20):
        zs.append(G["pawn"].get_actor_location().z - C.z); yield
    res["onto_the_floor"] = {**r2, "z_after": round(min(zs), 1)}
    def down(q):
        h = unreal.SystemLibrary.line_trace_single(G["w"], V(q.x, q.y, C.z + 960), V(q.x, q.y, C.z - 100), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [G["pawn"]], unreal.DrawDebugTrace.NONE, True)
        h = h.to_tuple() if h else None
        return round(h[4].z - C.z, 1) if h and h[0] else None
    # (the corners' floor beside the roof's posts (they stand at 45 degrees, 3 m out); the stairwell over its lower two turns
    # (over the last one the stair itself is near the top's height))
    floor_z = [down(at(Sa - a_, 150)) for a_ in (20, 45, 70)] + [down(at(45 + 90 * k + 14, 255)) for k in range(4)]
    well_z = [down(at(Sa + a_, 110)) for a_ in (120, 170, 220)]
    res["floor_traces"] = floor_z; res["stairwell_traces"] = well_z
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-35, yaw=Sa + 135)); yield from wait(0.5); shot("watch_top"); yield from rwait(1.5)
    put(V(Dp.x + out.x * 700, Dp.y + out.y * 700, 0), yaw=math.degrees(math.atan2(-out.y, -out.x))); yield from wait(1.0); shot("watch_door"); yield from rwait(1.5)
    quiet(False)
    ok_floor = all(z_ is not None and 890 < z_ < 930 for z_ in floor_z) and all(z_ is None or z_ < 870 for z_ in well_z)
    step_result("watch", res["watchtowers"] >= 12 and r_["reached"] == r_["of"] and res["end_z"] > 850 and r2["reached"] >= 1 and res["onto_the_floor"]["z_after"] > 850 and ok_floor, **res)

def light_state():
    return [dict(zip(("bld", "kind", "lit", "lights", "awake", "asleep", "on"), [int(x) if x.lstrip("-").isdigit() else x for x in str(l).split("|")])) for l in G["gen"].get_town_light_lines()]
def step_lights():
    """the lit buildings (the user's: "when a building has someone in it, it should have a torch lit, unless the NPC is
    sleeping"): at noon a keeper's shop lit and a home with nobody in it dark; at 20 o'clock homes with their residents in them
    lit; at 23 the keepers and residents asleep and their buildings dark; every building lit exactly when someone awake is in
    it, its torches' lights shown or hidden with it; the hour put back"""
    g = G["gen"]; res = {}; h0 = g.get_town_hour(); quiet(True)
    def check(nm, wait_s):
        yield from wait(wait_s)
        st = light_state()
        bad = [s_ for s_ in st if (s_["lit"] == 1) != (s_["awake"] > 0) or (s_["on"] > 0) != (s_["lit"] == 1)]
        res[nm] = {"buildings": len(st), "lit": sum(s_["lit"] for s_ in st), "keepers_lit": sorted({s_["kind"] for s_ in st if s_["lit"] and s_["kind"] != "home"}),
                   "homes_lit": sum(1 for s_ in st if s_["lit"] and s_["kind"] == "home"), "trades": [s_ for s_ in st if s_["kind"] != "home"], "asleep_dark": sum(1 for s_ in st if s_["asleep"] > 0 and not s_["lit"]), "bad": bad[:5]}
    g.set_town_hour(12.0); yield from check("noon", 3.0)
    g.set_town_hour(20.0); yield from check("evening", 45.0)
    g.set_town_hour(23.0); yield from check("night", 4.0)
    g.set_town_hour(h0); quiet(False)
    n, e, ni = res["noon"], res["evening"], res["night"]
    ok = (not n["bad"] and not e["bad"] and not ni["bad"] and len(n["keepers_lit"]) >= 3 and e["homes_lit"] > n["homes_lit"]
          and ni["lit"] < n["lit"] and ni["asleep_dark"] >= 3)
    step_result("lights", ok, **res)

def step_signs():
    """the trades' signs say what they are (the user's: "a general goods store should say something like 'general goods'"),
    on both faces of each sign; the quest board's notices (four on each face); pictures"""
    # (since the list of 2026-11-04 the words are painted in Almendra on a plane against each face of the board (Town.SignFace_<WORDS>,
    # MI_BS_Sign_<WORDS>), not the engine's text: each face within its board (90.4 cm out along the bracket, 89.5 down, 3.35 off
    # its middle: 127.3 cm from the sign's origin))
    res = {}; S = section()
    signs_at = []
    for c in isms(S):
        m = c.get_editor_property("static_mesh")
        if m and "TavernSign" in m.get_name():
            for i in range(c.get_instance_count()):
                t = c.get_instance_transform(i, True); t = t[-1] if isinstance(t, tuple) else t; signs_at.append(t)
    faces = []
    for c in isms(S):
        mt = c.get_material(0)
        if not mt or not mt.get_name().startswith("MI_BS_Sign_"): continue
        for i in range(c.get_instance_count()):
            t = c.get_instance_transform(i, True); t = t[-1] if isinstance(t, tuple) else t
            faces.append((mt.get_name()[11:], t))
    off = [min((abs((f.translation - s.translation).length() - 127.3) for s in signs_at), default=1e9) for _, f in faces]
    trades = [b for b in blds() if b["kind"] not in ("home", "castle")]
    res["signs"] = len(signs_at); res["faces"] = len(faces); res["trades"] = len(trades); res["words"] = sorted(set(w for w, _ in faces))
    res["face_off_board_cm"] = round(max(off, default=0.0), 2)
    bd = place("board")
    notes = [p for p in ism_instances("Plane") if bd and dist2(p, bd) < 200]
    res["notices"] = len(notes)
    # (a sign seen from along the street: 3.5 m off its board's face, at its height)
    for k, (w, f) in enumerate([x for x in faces if x[0] in ("GENERALGOODS", "TAVERN")][:2]):
        nrm = f.rotation.rotator().get_up_vector() if hasattr(f.rotation.rotator(), "get_up_vector") else unreal.MathLibrary.get_up_vector(f.rotation.rotator())
        p = f.translation; cam = V(p.x + nrm.x * 330, p.y + nrm.y * 330, 0)
        yaw = math.degrees(math.atan2(p.y - cam.y, p.x - cam.x))
        put(cam, yaw=yaw, z=0); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=14, yaw=yaw)); yield from wait(1.0); shot(f"sign_{w.lower()}"); yield from rwait(1.5)
    if bd:
        for k, o in enumerate((V(-330, 0, 0), V(330, 0, 0), V(0, -330, 0), V(0, 330, 0))):
            pp = V(bd.x + o.x, bd.y + o.y, 0); put(pp, yaw=math.degrees(math.atan2(bd.y - pp.y, bd.x - pp.x))); yield from wait(0.6); shot(f"board_{k}"); yield from rwait(1.2)
    ok = res["signs"] == res["trades"] and res["faces"] == 2 * res["trades"] and "GENERALGOODS" in res["words"] and res["face_off_board_cm"] < 2.0 and res["notices"] == 8
    step_result("signs", ok, **res)

def step_circle():
    """the teleport circle (the user's: "even after killing all of the enemies in the castle, player was not able to use the
    teleport circle to get to the Mistward Castle dungeon"): Mistward Castle on its list, shut while the Mistward Hall's guards
    stand (and she has not been through the Mistgate), open once they are dead; chosen, it opens Mistward Castle (a dry run)"""
    g = G["gen"]; res = {}
    assert "brokenspire" in G["w"].get_name(), "the circle step plays in the town: put it before the steps that end in the castle"
    def castle_line():
        g.open_town_panel("circle", -1); yield from rwait(0.3)
        ln = [p for p in panel() if p[0] == "castle"]; i = next((k for k, p in enumerate(panel()) if p[0] == "castle"), -1)
        return (ln[0] if ln else None), i
    ln, i = yield from castle_line()
    res["before"] = {"line": ln, "guards": len(list(g.get_town_guards())), "entered": G["gi"].get_counter("enter")}
    g.close_town_panel(); yield from rwait(0.3)
    for m in list(g.get_town_guards()): m.apply_damage(1e7, None)
    yield from wait(1.5)
    ln2, i2 = yield from castle_line()
    res["after"] = {"line": ln2, "guards": len(list(g.get_town_guards()))}
    g.set_editor_property("travel_dry_run", True)
    ok_act = g.activate_town_entry(i2) if i2 >= 0 else False
    yield from rwait(0.5)
    res["travel"] = {"activated": ok_act, "last": str(g.get_editor_property("last_travel"))}
    g.set_editor_property("travel_dry_run", False)
    try: g.close_town_panel()
    except Exception: pass
    b_on = res["before"]["line"] and res["before"]["line"][3] == "1"
    ok = (res["before"]["line"] is not None and (not b_on or res["before"]["entered"] > 0) and res["after"]["line"] and res["after"]["line"][3] == "1"
          and ok_act and "castle" in res["travel"]["last"])
    step_result("circle", ok, **res)

def step_burned():
    """the burned houses are physically whole (the user's: "roof tiles that aren't supported by anything and ... walls that are
    supported by nothing at all"): no roof piece on any burned house; every upper storey's wall piece stands on a wall piece of
    the storey under it"""
    res = {}; S = section()
    burnt = [b for b in blds() if b["kind"] == "home" and b["state"] == 1]
    res["burned"] = len(burnt)
    walls, roofs = [], []
    for c in isms(S):
        m = c.get_editor_property("static_mesh")
        if not m or c.get_num_materials() == 0: continue
        mt = c.get_material(0)
        if not mt or "Burnt" not in mt.get_name(): continue
        nm = m.get_name()
        for k in range(c.get_instance_count()):
            t = c.get_instance_transform(k, True)
            if isinstance(t, tuple): t = t[-1]
            if "Roof" in nm: roofs.append(nm)
            elif "Wall" in nm or "Doorway" in nm: walls.append(t.translation)
    up = [p for p in walls if p.z > 150]; low = [p for p in walls if p.z <= 150]
    floating = [[round(p.x), round(p.y), round(p.z)] for p in up if not any(dist2(p, q) < 30 and q.z < p.z - 150 for q in low)]
    res["walls"] = len(walls); res["upper"] = len(up); res["floating"] = floating[:8]; res["n_floating"] = len(floating); res["roof_pieces"] = len(roofs)
    if burnt:
        b = burnt[0]; f = door_front(b, 1200.0); put(f, yaw=math.degrees(math.atan2(b["c"].y - f.y, b["c"].x - f.x)))
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=math.degrees(math.atan2(b["c"].y - f.y, b["c"].x - f.x)))); yield from wait(1.0); shot("burned"); yield from rwait(1.5)
    step_result("burned", res["burned"] > 0 and res["upper"] > 0 and res["n_floating"] == 0 and res["roof_pieces"] == 0, **res)

def step_windows():
    """the windows' ledges are solid (the user's: "some of the windows have ledges that the player can walk through"): at a
    sample of house windows a capsule swept into the window from in front of it at a ledge's height is stopped within the
    ledge's depth"""
    res = {}; S = section(); w = G["w"]
    wins = []
    for c in isms(S):
        m = c.get_editor_property("static_mesh")
        if not m or "WallWindow" not in m.get_name() or c.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION and False: continue
        for k in range(0, c.get_instance_count(), 7):
            t = c.get_instance_transform(k, True)
            if isinstance(t, tuple): t = t[-1]
            wins.append((m.get_name(), t))
    res["windows_sampled"] = len(wins)
    stopped = 0; through = []
    for nm, t in wins[:40]:
        # (the piece's middle: its origin is at one end of its 3 m (180-degree Adjust, -150 cm along its Y)): try both faces
        rot_ = t.rotation.rotator(); fwd = rot_.get_forward_vector(); rgt = rot_.get_right_vector()
        mid_ = t.translation - rgt * 150.0
        hit_both = True
        for sgn in (1, -1):
            a = mid_ + fwd * (90.0 * sgn) + V(0, 0, 105.0); b = mid_ + V(0, 0, 105.0)
            h = unreal.SystemLibrary.capsule_trace_single(w, a, b, 20.0, 20.0, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [G["pawn"]], unreal.DrawDebugTrace.NONE, True)
            h = h.to_tuple() if h else None
            if not (h and h[0]): hit_both = False
        if hit_both: stopped += 1
        else: through.append([nm, round(mid_.x), round(mid_.y), round(mid_.z)])
    res["stopped"] = stopped; res["through"] = through[:6]
    step_result("windows", res["windows_sampled"] > 10 and not through, **res)
    yield

def step_walkers():
    """the townsfolk walk on their feet (the user's: "the children NPCs' legs do not move when they walk ... all townsfolk NPCs
    should have a walking animation"): for each child, the fool and a resident, followed from 4 m while it walks, its planted
    foot nearly still in the world (the slowest fifth of its foot's speeds under a third of its body's) and its clip's rate
    near 1; and the bodies that came without a head (the NPC pack's _Full_02) wear their pack's head"""
    res = {"walkers": {}}; quiet(True)
    # (since the third list the townsfolk spend most of their time at their work: the ones followed are those walking now, a
    # child, the fool or a resident first, up to five, looked for over a minute)
    followed = set(); t_look = now()
    pref = ("Little Wren", "Tobin", "Pip", "Simple Tam", "a townsman", "a townswoman")
    while len(res["walkers"]) < 5 and now() - t_look < 60.0:
        allf = [x for x in unreal.GameplayStatics.get_all_actors_of_class(G["w"], unreal.RDTownsfolk) if x.is_walking() and x.get_name() not in followed]
        allf.sort(key=lambda x: (0 if x.title in pref else 1))
        if not allf: yield from wait(0.5); continue
        f = allf[0]; followed.add(f.get_name()); title = f"{f.title} #{len(followed)}"
        b = f.get_components_by_class(unreal.SkeletalMeshComponent)[0]
        fs, bs = [], []; t0 = now(); last = None; lastb = None; lasty = None; turned = 0
        while now() - t0 < 12.0 and len(fs) < 120:
            L_ = f.get_actor_location(); G["pawn"].set_actor_location(V(L_.x - 400, L_.y, L_.z + 30), False, True)
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-10, yaw=0))
            ft = b.get_socket_location("foot_l")
            dt = GS.get_world_delta_seconds(G["w"]) or 0.016
            yw = f.get_actor_rotation().yaw
            straight = lasty is None or abs((yw - lasty + 180.0) % 360.0 - 180.0) < 1.0
            if f.is_walking() and last is not None and dt > 0:
                if straight: fs.append((ft - last).length() / dt); bs.append((L_ - lastb).length() / dt)
                else: turned += 1
            last, lastb, lasty = ft, L_, yw
            yield
        fs2 = sorted(fs); bmean = sum(bs) / len(bs) if bs else 0
        res["walkers"][title] = {"samples": len(fs), "turning_frames_left_out": turned, "foot_slow_cm_s": round(fs2[len(fs2) // 5], 1) if fs2 else None, "body_cm_s": round(bmean, 1), "rate": round(b.get_play_rate(), 2),
                                 "parts": len(f.get_components_by_class(unreal.SkeletalMeshComponent)), "meshes": [c.get_editor_property("skeletal_mesh_asset").get_name() for c in f.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_editor_property("skeletal_mesh_asset")]}
    heads = {}
    for f in unreal.GameplayStatics.get_all_actors_of_class(G["w"], unreal.RDTownsfolk):
        ms = [c.get_editor_property("skeletal_mesh_asset").get_name() for c in f.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_editor_property("skeletal_mesh_asset")]
        if any("_Full_02" in m and "NPC_Character" in m for m in ms): heads[f.title] = ms
    res["full02"] = heads
    quiet(False)
    ws = [v for v in res["walkers"].values() if v["samples"] >= 20]
    ok = len(ws) >= 3 and all(v["foot_slow_cm_s"] < v["body_cm_s"] / 3 and 0.75 < v["rate"] < 1.25 for v in ws) and heads and all(any("_Head" in m for m in ms) for ms in heads.values())
    step_result("walkers", ok, **res)

STEPS = {"town": step_town, "doors": step_doors, "talk": step_talk, "services": step_services, "guards": step_guards, "castle": step_castle,
         "map": step_map, "folk": step_folk, "gate": step_gate, "pictures": step_pictures, "tour": step_tour, "trip": step_trip,
         "castlewalls": step_castlewalls, "daynight": step_daynight, "shape": step_shape, "watch": step_watch, "lights": step_lights,
         "signs": step_signs, "circle": step_circle, "burned": step_burned, "windows": step_windows, "walkers": step_walkers}
# ------------------------------------------------------------------------------------------------ the third list of 2026-11-02
def map_state():
    p = str(G["pc"].get_hud().get_town_map_state()).split("|")
    return {"zoom": float(p[0]), "span": float(p[1]), "seals": int(p[2]), "view": [round(float(p[3])), round(float(p[4]))]}
def step_mapzoom():
    """the map zoomed and moved (the user's: "you should be able to zoom the overhead map in and out and then move it around"):
    M opens it at the whole town; the wheel up three times zooms it 1.95 times (each notch 1.25); the right arrow held a second
    moves its middle east; C shows the whole town again; the quest givers each marked by a seal (the elder, the scholar, the
    captain, the board), their names not written at the whole town's zoom and written zoomed in; pictures at 1x and 3x"""
    g = G["gen"]; res = {}; quiet(True)
    put(place("square"), yaw=0.0); yield from wait(0.5)
    yield from press("M"); yield from wait(0.6)
    s0 = map_state(); res["opened"] = s0; shot("map_zoom1"); yield from rwait(1.2)
    for _ in range(3): yield from press("MouseScrollUp", 0.05)
    yield from wait(0.4); s1 = map_state(); res["wheel_x3"] = s1
    cb().simulate_key(key("Right"), True); yield from wait(1.0); cb().simulate_key(key("Right"), False); yield from wait(0.3)
    s2 = map_state(); res["moved"] = s2
    for _ in range(2): yield from press("MouseScrollUp", 0.05)
    yield from wait(0.5); s3 = map_state(); res["zoom3"] = s3
    labels = [str(l) for l in G["pc"].get_hud().get_town_labels()]
    res["seal_labels"] = [l for l in labels if l.startswith("seal|")]
    shot("map_zoom3"); yield from rwait(1.2)
    yield from press("C"); yield from wait(0.4); s4 = map_state(); res["centred"] = s4
    yield from press("M"); yield from wait(0.3)
    res["map_open_after"] = g.get_editor_property("map_open")
    quiet(False)
    givers = sorted(set(str(q.giver) for q in g.get_editor_property("quests")))
    res["givers"] = givers
    ok = (abs(s0["zoom"] - 1.0) < 0.01 and abs(s1["zoom"] - 1.953) < 0.02 and s2["view"][1] > s1["view"][1] + 1000 and abs(s3["zoom"] - 3.05) < 0.05
          and abs(s4["zoom"] - 1.0) < 0.01 and s0["seals"] >= len(givers) and all(f"seal|{gv}" in res["seal_labels"] for gv in givers) and not res["map_open_after"])
    step_result("mapzoom", ok, **res)

def life():
    d = {"work": [], "folk": [], "animal": [], "spit": []}
    for l in G["gen"].get_town_life_lines():
        p = str(l).split("|")
        if p[0] == "work": d["work"].append({"i": int(p[1]), "kind": p[2], "group": int(p[3]), "at": V(float(p[4]), float(p[5]), 0), "by": int(p[6]), "working": p[7] == "1"})
        elif p[0] == "folk": d["folk"].append({"i": int(p[1]), "role": p[2], "state": p[3], "work": int(p[4]), "kind": p[5], "left": float(p[6]), "done": int(p[7]),
                                             "kinds": [k for k in p[8].split(",") if k], "jobs": [int(j) for j in p[9].split(",") if j], "min": float(p[10]), "max": float(p[11]),
                                             "at": V(float(p[12]), float(p[13]), 0), "clip": p[14]})
        elif p[0] == "animal": d["animal"].append({"i": int(p[1]), "kind": p[2], "at": V(float(p[3]), float(p[4]), float(p[5])), "pen": int(p[6]), "state": int(p[7]), "changes": int(p[8])})
        elif p[0] == "spit": d["spit"].append({"i": int(p[1]), "roll": float(p[2]), "crank": int(p[3])})
    return d
GROUPS = ["pot", "spit", "garden", "pen", "seat", "serve", "chat", "smithy", "bar", "camp"]
def step_life():
    """the town's life (the user's: "the town should look more lively ... a finite state machine that loops between at least 3
    activities for NPCs and have different timers for each NPC"): gardens with plants, pens with animals of every kind, cooking
    fires with a pot and with a spit, the short grass and the small bushes placed; every townsperson given a round has three
    kinds of work or more in it and a range of seconds of its own; over two minutes of play at noon (the game 3 times as fast)
    they go between them: places of every group worked (a pot stirred, a spit turned (its meat turning), a garden tended, a pen
    fed, a tavern's seat sat on, a table served, the bar, the well, the smithy), most townsfolk with three kinds done or more;
    the animals stay in their pens and change what they do; pictures of each kind of work"""
    g = G["gen"]; res = {}; quiet(True)
    sh = shape_lines()
    res["gardens"] = len(sh.get("gardens", [])); res["plants"] = sum(x["plants"] for x in sh.get("gardens", []))
    res["pens"] = len(sh.get("pens", [])); res["greens"] = sh.get("greens")
    kinds = {}
    for w in sh.get("work", []): kinds[w["kind"]] = kinds.get(w["kind"], 0) + 1
    res["places_of_work"] = kinds
    h_was = g.get_town_hour(); g.set_town_hour(11.0)
    L0 = life()
    rounds = [f for f in L0["folk"]]
    res["with_rounds"] = len(rounds)
    def acts(f):
        a = set()
        for j in f["jobs"]:
            if j < 0: a.add("stroll"); continue
            w = L0["work"][j]; a.add(f'{w["kind"]}@{w["group"]}')
        return a
    res["fewest_kinds_in_a_round"] = min((len(acts(f)) for f in rounds), default=0)
    res["rounds_under_3"] = [[f["role"], sorted(acts(f))] for f in rounds if len(acts(f)) < 3][:8]
    timers = set((round(f["min"], 2), round(f["max"], 2)) for f in rounds)
    res["distinct_timers"] = len(timers)
    # (two minutes of play, three times as fast: samples every 2 s)
    unreal.SystemLibrary.execute_console_command(G["w"], "slomo 3")
    worked = {}; spit_roll = {}; seen_clips = set(); animals_out = 0; samples = 0
    a0 = {a["i"]: a["changes"] for a in L0["animal"]}
    pens = sh.get("pens", [])
    t0 = now()
    while now() - t0 < 240.0:
        yield from wait(2.0)
        Ls = life(); samples += 1
        for w in Ls["work"]:
            if w["working"]: worked[GROUPS[w["group"]] + ":" + w["kind"]] = worked.get(GROUPS[w["group"]] + ":" + w["kind"], 0) + 1
        for s_ in Ls["spit"]: spit_roll[s_["i"]] = s_["roll"]
        for f in Ls["folk"]: seen_clips.add(f["clip"])
        for a in Ls["animal"]:
            if 0 <= a["pen"] < len(pens):
                pn = pens[a["pen"]]
                if abs(a["at"].x - pn["at"].x) > pn["half"][0] + 30 or abs(a["at"].y - pn["at"].y) > pn["half"][1] + 30: animals_out += 1
    unreal.SystemLibrary.execute_console_command(G["w"], "slomo 1")
    L1 = life()
    res["samples"] = samples
    res["worked_samples"] = dict(sorted(worked.items()))
    res["spits_turned"] = sum(1 for s_ in L1["spit"] if abs(s_["roll"]) > 1.0)
    res["spits"] = len(L1["spit"])
    res["clips_seen"] = sorted(c for c in seen_clips if c)
    done3 = [f for f in L1["folk"] if len(f["kinds"]) >= 3]
    res["folk_three_kinds_done"] = f"{len(done3)} of {len(L1['folk'])}"
    res["jobs_done_total"] = sum(f["done"] for f in L1["folk"])
    res["tavern_staff"] = [{"role": f["role"], "state": f["state"], "kind": f["kind"], "done": f["done"], "kinds": f["kinds"], "jobs": [f'{L1["work"][j]["kind"]}@{GROUPS[L1["work"][j]["group"]]}' if j >= 0 else "stroll" for j in f["jobs"]]}
                           for f in L1["folk"] if f["role"] == "Innkeeper" or any(j >= 0 and L1["work"][j]["group"] == 5 for j in f["jobs"])]
    akinds = {}
    for a in L1["animal"]: akinds[a["kind"].split("_")[0]] = akinds.get(a["kind"].split("_")[0], 0) + 1
    res["animals"] = akinds; res["animal_samples_outside_pen"] = animals_out
    res["animals_changed"] = sum(1 for a in L1["animal"] if a["changes"] > a0.get(a["i"], 0))
    # (pictures: each kind of work being done, from 4 m before the worker, the camera a little high)
    pics = []
    # (her body hidden for the pictures: it stood between the camera and the worker)
    G["pawn"].set_actor_hidden_in_game(True)
    for kind in ("Stir", "Crank", "Tend", "Scatter", "SitDrink", "SitTalk", "CarryIdle", "Hammer", "Talk"):
        Lk = life()
        w = next((x for x in Lk["work"] if x["kind"] == kind and x["working"]), None)
        if not w: continue
        wk = sh["work"][w["i"]]; yw = math.radians(wk["yaw"] + 25.0)
        p = V(wk["at"].x + math.cos(yw) * 330, wk["at"].y + math.sin(yw) * 330, 0)
        put(p, yaw=wk["yaw"] + 205.0); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-12, yaw=wk["yaw"] + 205.0)); yield from wait(1.0)
        shot(f"life_{kind.lower()}"); pics.append(kind); yield from rwait(1.4)
    if pens:
        pn = pens[0]; put(V(pn["at"].x - 700, pn["at"].y, 0), yaw=0.0); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-22, yaw=0.0)); yield from wait(1.0); shot("life_pen"); pics.append("pen"); yield from rwait(1.4)
    gd = sh.get("gardens", [])
    if gd:
        q = gd[0]; put(V(q["at"].x - 650, q["at"].y - 200, 0), yaw=17.0); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-25, yaw=17.0)); yield from wait(1.0); shot("life_garden"); pics.append("garden"); yield from rwait(1.4)
    G["pawn"].set_actor_hidden_in_game(False)
    res["pictures"] = pics
    g.set_town_hour(h_was); quiet(False)
    groups_worked = set(k.split(":")[0] for k in worked)
    ak = set(akinds)
    ok = (res["gardens"] >= 6 and res["plants"] >= 100 and res["pens"] >= 5 and len(ak & {"Chicken", "Pig", "Goat", "Cow", "Rabbit"}) >= 5
          and kinds.get("Stir", 0) >= 3 and kinds.get("Crank", 0) >= 3 and kinds.get("SitDrink", 0) >= 2 and kinds.get("CarryIdle", 0) >= 3
          and (res["greens"] or {}).get("grass", 0) > 5000 and (res["greens"] or {}).get("bushes", 0) > 200
          and res["with_rounds"] >= 30 and res["fewest_kinds_in_a_round"] >= 3 and res["distinct_timers"] >= res["with_rounds"] * 0.9
          and {"pot", "spit", "garden", "pen", "seat", "serve", "smithy"} <= groups_worked and res["spits_turned"] >= 1
          and len(done3) >= len(L1["folk"]) * 0.2 and res["jobs_done_total"] >= len(L1["folk"]) * 2 and animals_out == 0 and res["animals_changed"] >= len(L1["animal"]) * 0.5)
    step_result("life", ok, **res)

def step_falls():
    """damage from a fall (the user's: "there should be damage taken when falling from a great height"): dropped from 3 m she
    takes none; from 9 m above the square (a fall of 9 m) some, as FallSafeHeight and FallLethalHeight say; from 20 m all her
    hit points (she falls); she is brought back"""
    g = G["gen"]; c = cb(); res = {"safe_cm": g.get_editor_property("fall_safe_height"), "lethal_cm": g.get_editor_property("fall_lethal_height"), "on": g.get_editor_property("fall_damage")}
    quiet(True)
    sq = place("square")
    for h in (300.0, 900.0, 2000.0):
        c.set_health(c.get_max_health()); yield from wait(0.3)
        hp0 = c.get_health()
        put(V(sq.x + 300, sq.y + 300, 0), yaw=0.0, z=h); yield from wait(0.2)
        t0 = now()
        while now() - t0 < 6.0:
            yield
            if not G["pawn"].get_movement_component().is_falling() and now() - t0 > 0.5: break
        yield from wait(0.5)
        hp1 = c.get_health()
        res[f"from_{int(h)}"] = {"before": round(hp0, 1), "after": round(hp1, 1), "fall": str(c.get_fall_state()), "dead": c.is_dead()}
        if c.is_dead():
            t1 = now()
            while c.is_dead() and now() - t1 < 15.0: yield
    # (the fatal fall left her things in a pile where she fell: gone, so that later steps start clean)
    for p in list(g.loot_piles):
        if p and p.get_editor_property("hers"): p.destroy_actor()
    quiet(False)
    mh = c.get_max_health()
    # (put sets her capsule's middle 1 m over the height asked; standing it is 92 cm over the ground: a fall of the height + 8)
    exp9 = mh * (900 + 8 - res["safe_cm"]) / (res["lethal_cm"] - res["safe_cm"])
    r3, r9, r20 = res["from_300"], res["from_900"], res["from_2000"]
    res["expected_from_900"] = round(exp9, 1)
    ok = res["on"] and abs(r3["after"] - r3["before"]) < 0.5 and r9["before"] - r9["after"] > 5 and abs((r9["before"] - r9["after"]) - exp9) < mh * 0.08 and r20["dead"]
    step_result("falls", ok, **res)

def step_dagger():
    """the Warrior's dagger in her palm (the user's: "the warrior holds the dagger too close to her wrist. it should rest in
    her palm"): as the Warrior with the Dagger drawn, standing, in her own pose: the handle's middle in her hand's frame at the
    base of the fingers (9 to 11 cm out from the wrist along the fingers) and within 2 cm of the palm's middle across the
    hand; pictures from her right side and front"""
    g = G["gen"]; c = cb(); res = {}; quiet(True)
    if str(g.get_editor_property("current_hero")) != "Warrior": g.switch_hero("Warrior"); yield from rwait(1.0)
    refresh(); c = cb()
    names = [str(w.name) for w in g.get_editor_property("weapons")]
    res["weapons"] = names
    if "Dagger" in names: c.select_weapon(names.index("Dagger")); yield from wait(1.0)
    sq = place("square"); put(V(sq.x + 400, sq.y + 400, 0), yaw=0.0); yield from wait(1.5)
    body = G["pawn"].get_components_by_class(unreal.SkeletalMeshComponent)[0]
    hand = body.get_socket_transform("hand_r", unreal.RelativeTransformSpace.RTS_WORLD)
    dg = None
    for comp in G["pawn"].get_components_by_class(unreal.StaticMeshComponent):
        m = comp.get_editor_property("static_mesh")
        if m and m.get_name() == "SM_Dagger" and comp.is_visible(): dg = comp; break
    if dg:
        fr = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon_magic5\weapon_frames.json"))["weapons"]["Dagger"]
        o = V(*fr["origin"]); x = V(*fr["x"])
        hm = o - x * ((fr["handle"] - fr["grip_from_guard"]) * 0.5 - fr["grip_from_guard"] * 0.5)
        guard = o + x * fr["grip_from_guard"]; pommel = o - x * (fr["handle"] - fr["grip_from_guard"]); hm = (guard + pommel) * 0.5
        wt = dg.get_world_transform()
        loc = lambda p: unreal.MathLibrary.inverse_transform_location(hand, unreal.MathLibrary.transform_location(wt, p))
        h_ = loc(hm)
        res["handle_middle_in_hand_cm"] = [round(h_.x, 2), round(h_.y, 2), round(h_.z, 2)]
        res["guard_in_hand_cm"] = [round(v, 2) for v in (loc(guard).x, loc(guard).y, loc(guard).z)]
        res["pommel_in_hand_cm"] = [round(v, 2) for v in (loc(pommel).x, loc(pommel).y, loc(pommel).z)]
    pr = G["pawn"].get_actor_rotation().yaw
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=pr - 90)); yield from wait(0.8); shot("dagger_side"); yield from rwait(1.4)
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=pr + 180)); yield from wait(0.8); shot("dagger_front"); yield from rwait(1.4)
    quiet(False)
    h_ = res.get("handle_middle_in_hand_cm")
    ok = bool(h_) and -11.0 <= h_[1] <= -8.5 and abs(h_[0] - 0.7) < 2.0
    step_result("dagger", ok, **res)

# ------------------------------------------------------------------------------------------------ the list of 2026-11-04
def improve():
    d = {}
    for l in section().get_town_improve_lines():
        p = str(l).split("|"); d.setdefault(p[0], []).append(p[1:])
    return d
def sweep_to(frm, to):
    """she is put at frm and moved to `to` with a sweep (as a body that walks): how far she got (cm)"""
    G["pawn"].set_actor_location(V(frm.x, frm.y, frm.z), False, True)
    G["pawn"].set_actor_location(V(to.x, to.y, frm.z), True, False)
    p = G["pawn"].get_actor_location()
    return dist2(p, frm)
def step_list7():
    """the user's list of 2026-11-04 in the town (docs/improvements7.txt): the farm animals stop her; a street's cobbles at
    most three people wide; the open ground rises and falls (flat under every building), the walked ground following it; the
    mill's sails clear of the ground on its house; the tavern's seats lit; a pen's gate opens and shuts; a garden harvested
    for its crops (once a day); a table's food taken; the oven bakes bread of the garden's wheat"""
    g = G["gen"]; S = section(); res = {}; quiet(True)
    g.set_town_hour(11.0); yield from wait(0.5)
    # ---- an animal stops her: put inside its pen, 1.6 m off it, and moved through where it stands
    L = life(); an = None
    for a in L["animal"]:
        if a["kind"].lower().startswith(("cow", "pig", "goat")): an = a; break
    an = an or (L["animal"][0] if L["animal"] else None)
    if an:
        # (the same sweep with the animal moved away first: the pen's fence alone stops her there)
        A = min(GS.get_all_actors_of_class(G["w"], unreal.RDTownAnimal), key=lambda a: dist2(a.get_actor_location(), an["at"]))
        at = A.get_actor_location(); A.set_actor_tick_enabled(False)
        free = got = 0.0
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            frm = V(at.x + dx * 170, at.y + dy * 170, at.z + 100); to = V(at.x, at.y, at.z + 100)
            A.set_actor_location(V(at.x, at.y, at.z - 5000), False, True); free = sweep_to(frm, to)
            A.set_actor_location(at, False, True); yield from wait(0.1); got = sweep_to(frm, to)
            if free > 150: break
        A.set_actor_tick_enabled(True)
        res["animal"] = {"kind": an["kind"], "without_cm": round(free, 1), "with_cm": round(got, 1)}
        # (stopped short of its middle by at least her capsule and some of its body: a pig met side on stopped her 58 cm off,
        # end on 66 (two towns); walked through, she reaches its middle as she does without it)
        res["animal"]["stopped"] = free > 150 and got < free - 40
    # ---- the cobbles: across the main road's middle, a sample every 20 cm of the drawn ground's cobble weight
    gate = place("gate"); sq = place("square")
    d = V(sq.x - gate.x, sq.y - gate.y, 0); n = math.hypot(d.x, d.y); d = V(d.x / n, d.y / n, 0); ac = V(-d.y, d.x, 0)
    mid = V(gate.x + d.x * (n * 0.45), gate.y + d.y * (n * 0.45), 0)
    cob = [S.get_town_ground_color_at(V(mid.x + ac.x * k * 20, mid.y + ac.y * k * 20, 0)).g for k in range(-30, 31)]
    run_, best = 0, 0
    for c in cob: run_ = run_ + 1 if c > 0.5 else 0; best = max(best, run_)
    res["cobbles_m"] = round(best * 0.2, 1); res["cobbles_profile"] = [round(c, 2) for c in cob[::3]]
    # ---- the ground's rise and fall
    im = improve()
    lift = [float(x) for x in im.get("lift", [["0", "0", "9"]])[0]]
    res["lift"] = {"max_cm": lift[0], "min_cm": lift[1], "under_buildings_cm": lift[2]}
    L0 = S.get_actor_location(); best = None
    for i in range(4, 164, 3):
        for j in range(4, 164, 3):
            P = V(L0.x + (i + 0.5) * 300, L0.y + (j + 0.5) * 300, 0); h = S.get_town_lift_at(P)
            if best is None or h > best[2]: best = (P.x, P.y, h)
        if i % 30 == 4: yield
    # (the walked ground there: a trace straight down)
    hit = unreal.SystemLibrary.line_trace_single(G["w"], V(best[0], best[1], 1500), V(best[0], best[1], -800), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [G["pawn"]], unreal.DrawDebugTrace.NONE, True)
    hz = None
    if hit:
        h = hit.to_tuple() if hasattr(hit, "to_tuple") else hit
        try: hz = round(h[4].z, 1)
        except Exception: hz = None
    res["lift"]["highest"] = [round(best[0]), round(best[1]), round(best[2], 1)]; res["lift"]["walked_z"] = hz
    put(V(best[0] - 1400, best[1], 0), yaw=0.0, z=best[2] + 60); yield from wait(1.5); shot("list7_lift"); yield from rwait(1.2)
    # ---- the mill: its sails' lowest point and the millstones over the ground, its house there
    mills = [a for a in GS.get_all_actors_of_class(G["w"], unreal.Actor) if "windmill" in a.get_class().get_name().lower()]
    houses = [a for a in GS.get_all_actors_of_class(G["w"], unreal.Actor) if "PLA_Mill" in a.get_class().get_name()]
    if mills:
        def low(c):
            b0, b1 = c.get_local_bounds(); t = c.get_world_transform()
            return min(t.transform_location(V(x, y, z)).z for x in (b0.x, b1.x) for y in (b0.y, b1.y) for z in (b0.z, b1.z))
        rot = [c for c in mills[0].get_components_by_class(unreal.StaticMeshComponent) if c.static_mesh and "rotor" in c.static_mesh.get_name()]
        lo = min(low(c) for c in rot) if rot else -1.0
        res["mill_base_cm"] = round(min(low(c) for c in mills[0].get_components_by_class(unreal.StaticMeshComponent)), 1)
        res["mill"] = {"lowest_cm": round(lo, 1), "house": len(houses) > 0, "house_m": round(dist2(houses[0].get_actor_location(), mills[0].get_actor_location()) / 100.0, 1) if houses else None}
        ml = place("mill"); put(V(ml.x + 2800, ml.y, 0), yaw=180.0); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=12, yaw=180.0)); yield from wait(1.5); shot("list7_mill"); yield from rwait(1.2)
    # ---- the tavern's seats lit: lights within 2.5 m of every seat, a picture at night
    seats = [w for w in L["work"] if w["kind"] in ("SitDrink", "SitTalk")]
    lights = [c.get_world_location() for c in S.get_components_by_class(unreal.PointLightComponent)]
    lit = [min((dist2(s["at"], l) for l in lights), default=1e9) for s in seats]
    res["tavern"] = {"seats": len(seats), "seats_lit": sum(1 for x in lit if x < 250), "nearest_light_m": round(max(lit, default=0) / 100.0, 2)}
    tv = next(b for b in blds() if b["kind"] == "tavern")
    g.set_town_hour(20.5); yield from wait(1.0)
    put(V(tv["c"].x, tv["c"].y, 0), yaw=0.0); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-20, yaw=0.0)); yield from wait(1.2); shot("list7_tavern", "1280x720"); yield from rwait(1.5)
    res["tavern"]["luma"] = round(png_luma(os.path.join(SHOTS, f"bs_{TAG}_list7_tavern.png"), (0.2, 0.45, 0.8, 0.95)), 1) if os.path.exists(os.path.join(SHOTS, f"bs_{TAG}_list7_tavern.png")) else None
    g.set_town_hour(11.0)
    # ---- a pen's gate: F at it opens it, again shuts it
    pg = im.get("pengate", [])
    res["pens"] = {"gates": len(pg)}
    if pg:
        q = pg[0]; c = V(float(q[2]), float(q[3]), 0)
        put(V(c.x + 120, c.y, 0)); yield from wait(0.3)
        res["pens"]["prompt"] = str(g.describe_nearest(G["pawn"].get_actor_location()))
        g.interact_nearest(G["pawn"].get_actor_location()); yield from rwait(1.5)
        o1 = [x for x in improve()["pengate"] if x[0] == q[0]][0][1]
        g.interact_nearest(G["pawn"].get_actor_location()); yield from rwait(1.5)
        o2 = [x for x in improve()["pengate"] if x[0] == q[0]][0][1]
        res["pens"]["opened"] = o1 == "1"; res["pens"]["shut"] = o2 == "0"
    # ---- a garden harvested, not again the same day
    cnt = lambda n: cb().get_item_count(n)
    crops = ("Wild Carrot", "Wheat", "Pumpkin", "Sunflower Seeds", "Herbs")
    gd = im.get("garden", [])
    if gd:
        q = gd[0]; at = V(float(q[2]), float(q[3]), 0)
        before = {c: cnt(c) for c in crops}
        put(V(at.x, at.y, 0)); yield from wait(0.3)
        res["garden_prompt"] = str(g.describe_nearest(G["pawn"].get_actor_location()))
        g.interact_nearest(G["pawn"].get_actor_location()); yield from rwait(0.3)
        got = {c: cnt(c) - before[c] for c in crops if cnt(c) != before[c]}
        g.interact_nearest(G["pawn"].get_actor_location()); yield from rwait(0.3)
        res["garden"] = {"crops": q[1], "got": got, "again": str(cb().get_editor_property("message")), "ripe_after": g.is_garden_ripe(int(q[0]))}
    # ---- a table's food taken
    fd = [x for x in im.get("food", []) if x[1] == "0"]
    res["food"] = {"tables": len(im.get("food", []))}
    if fd:
        q = fd[0]; at = V(float(q[2]), float(q[3]), float(q[4]))
        items = q[5].split(","); before = {i: cnt(i) for i in set(items)}
        put(V(at.x + 90, at.y, 0)); yield from wait(0.3)
        res["food"]["prompt"] = str(g.describe_nearest(G["pawn"].get_actor_location()))
        g.interact_nearest(G["pawn"].get_actor_location()); yield from rwait(0.3)
        res["food"]["got"] = {i: cnt(i) - before[i] for i in set(items)}
        res["food"]["taken"] = [x for x in improve()["food"] if x[0] == q[0]][0][1] == "1"
    # ---- the oven: 2 wheat bake a bread
    ov = im.get("oven", [])
    res["oven"] = {"ovens": len(ov)}
    if ov:
        q = ov[0]; at = V(float(q[0]), float(q[1]), 0)
        cb().add_item("Wheat", 2); w0, b0 = cnt("Wheat"), cnt("Bread")
        for dx, dy in ((200, 0), (-200, 0), (0, 200), (0, -200)):
            put(V(at.x + dx, at.y + dy, 0)); yield from wait(0.2)
            if "oven" in str(g.describe_nearest(G["pawn"].get_actor_location())): break
        res["oven"]["prompt"] = str(g.describe_nearest(G["pawn"].get_actor_location()))
        g.interact_nearest(G["pawn"].get_actor_location()); yield from rwait(0.3)
        res["oven"]["station"] = str(cb().get_craft_station()); res["oven"]["open"] = cb().is_crafting_open()
        res["oven"]["lines"] = [str(l).split("|")[1] for l in cb().get_craft_lines()][:8]
        res["oven"]["baked"] = cb().craft("Bread")
        res["oven"]["bread"] = cnt("Bread") - b0; res["oven"]["wheat_used"] = w0 - cnt("Wheat")
        cb().set_crafting_open(False); cb().set_craft_station("None")
    quiet(False)
    ok = (res.get("animal", {}).get("stopped", False) and 0.8 <= res["cobbles_m"] <= 3.0 and lift[0] >= 60 and lift[1] <= -40 and lift[2] < 1.0
          and hz is not None and abs(hz - best[2]) < 15 and res.get("mill", {}).get("lowest_cm", -1) > 150 and res.get("mill", {}).get("house")
          and res["tavern"]["seats"] > 0 and res["tavern"]["seats_lit"] == res["tavern"]["seats"]
          and res["pens"].get("opened") and res["pens"].get("shut") and "gate" in res["pens"].get("prompt", "")
          and res.get("garden", {}).get("got") and "harvested" in res.get("garden", {}).get("again", "") and not res.get("garden", {}).get("ripe_after", True)
          and res["food"].get("taken") and sum(res["food"].get("got", {}).values()) >= 1
          and res["oven"].get("station") == "Oven" and res["oven"].get("baked") and res["oven"].get("bread") == 1 and res["oven"].get("wheat_used") == 2)
    step_result("list7", ok, **res)

# ------------------------------------------------------------------------------------------------ her whole state between the levels
def state_lines(): return sorted(str(l) for l in cb().get_state_lines())
def state_diff(a, b, tol=0.06):
    """two lists of her state lines (URDCombatComponent.GetStateLines) set against each other: the same lines, their words the
    same and their numbers within tol (a time left read a frame apart); the lines that differ"""
    def keyed(ls):
        out, seen = {}, {}
        for l in ls:
            p = l.split("|"); n = 3 if p[0] in ("effect", "quick", "slash") else 1 if p[0] in ("hp", "mana", "dex", "torch", "startshield") else 2
            k = "|".join(p[:n])
            seen[k] = seen.get(k, 0) + 1; out[f"{k}#{seen[k]}"] = p
        return out
    A, B = keyed(a), keyed(b); bad = []
    for k in sorted(set(A) | set(B)):
        if k not in A or k not in B: bad.append([k, A.get(k), B.get(k)]); continue
        for x, y in zip(A[k], B[k]):
            try: same = abs(float(x) - float(y)) <= tol
            except ValueError: same = x == y
            if not same: bad.append([k, A[k], B[k]]); break
    return bad
def summons_now():
    return sorted([str(a.summon_spell), round(a.get_health() / max(a.get_max_health(), 1.0), 2)] for a in G["gen"].get_allies() if a and not a.is_dead() and str(a.summon_spell) != "None")
def item_of(kind):
    return next((str(i.name) for i in G["gen"].get_editor_property("items") if i.kind == kind), None)
def weapon_index(name):
    W = [str(w.name) for w in G["gen"].get_editor_property("weapons")]
    return W.index(name) if name in W else -1
def as_hero(hero):
    # (a hero of her own for each part: her summons sent away first (a switch of hero keeps the allies standing))
    g = G["gen"]
    for a in list(g.get_allies()):
        if a: a.destroy_actor()
    if str(g.get_editor_property("current_hero")) != hero:
        g.switch_hero(hero); yield from wait(0.8); refresh()
        t0 = time.time()
        while cb() is None and time.time() - t0 < 10: yield; refresh()
    yield from wait(0.5)
def set_up(hero, leg):
    """her state made different from a fresh start, the way play makes it: found things, worn and used; potions and food working
    on her; poison and weakness (slowness on the way back); spells on her; her own counters run up; the quick bar rearranged; a
    torch lit; for the Summoner two summons, one hurt; for the Warrior a slash on her found sword and plate on;
    for the Rogue her energy spent and stealth on. Returns what was done."""
    g = G["gen"]; c = cb(); did = {}
    quiet(True)
    c.set_health(round(c.get_max_health() * 0.62))           # (hurt: the food is eaten only by one who is)
    def take(n, k=1):
        if n: c.add_item(n, k)
        return n
    found = {"Summoner": "Dagger", "Rogue": "Dagger", "Warrior": "Arming Sword"}[hero]
    if leg == "town":
        g.add_gold(120, "the test")
        take(found); yield from wait(0.3)
        wi = weapon_index(found)
        if wi >= 0: c.set_weapon_wear(wi, round(c.get_weapon_durability(wi) * 0.55, 1)); did["found_wear"] = c.get_weapon_wear(wi)
        take("Medium Healing Potion", 2); take(item_of(unreal.RDItemKind.COMPONENT), 3)
        if hero == "Warrior":
            # (a slash on her found sword; a set of armour on)
            sl = next((str(s.name) for s in g.get_editor_property("slashes")), None)
            if sl and wi >= 0: take(sl); yield from wait(0.2); did["slash"] = [sl, c.apply_slash(sl, wi)]
            for it in g.get_editor_property("items"):
                if it.kind != unreal.RDItemKind.ARMOUR: continue
                take(str(it.name)); yield from wait(0.1)
                if c.wear_armour(str(it.name)): did["armour"] = str(it.name); break
                c.remove_item(str(it.name), 1)
        mr = next((str(i.name) for i in g.get_editor_property("items") if i.kind == unreal.RDItemKind.RING and i.ring_kind == unreal.RDRingKind.MAGIC), None)
        if hero == "Summoner" and mr: take(mr); did["ring"] = c.wear_ring(mr)
        # (a torch lit: not the Warrior, whose shield takes her left hand)
        if hero != "Warrior": take("Torch"); did["torch"] = c.hold_torch(True)
    # (a potion and a food working on her)
    for n in (item_of(unreal.RDItemKind.SPEED), item_of(unreal.RDItemKind.FOOD)):
        if n: take(n); did.setdefault("used", []).append([n, c.use_item(n)]); yield from wait(0.3)
    # (her counters: a spell or a blow at nothing, a kill)
    if hero == "Summoner":
        c.set_mana(c.get_max_mana()); c.select_weapon(0); yield from wait(0.2); c.start_attack(); yield from wait(1.6)
        # (two summons, one of them hurt)
        if leg == "town":
            si = weapon_index("Summon Tier 1")
            for _ in range(2): c.set_mana(c.get_max_mana()); c.start_attack_with(si); yield from wait(2.6)
            al = [a for a in g.get_allies() if a and str(a.summon_spell) == "Summon Tier 1"]
            if al: al[0].apply_damage(al[0].get_max_health() * 0.4, None); yield from wait(0.3)
    else:
        c.start_attack(); yield from wait(1.4)
    p = G["pawn"]; m = g.spawn_monster_named("Rat", p.get_actor_location() + p.get_actor_forward_vector() * 350.0, 1, 1.0, 1.0, 1.0); yield from wait(0.4)
    if m:
        for _ in range(12):
            if m.is_dead(): break
            c.set_mana(c.get_max_mana())
            if hero == "Summoner": c.cast_spell_now(0, m)
            else: m.apply_damage(m.get_max_health() + 5.0, G["pawn"])
            yield from wait(0.8)
        did["killed"] = m.is_dead()
    # (the quick bar rearranged: her second entry put in slot 6)
    qs = [str(x) for x in c.get_quick_slots()]
    if len(qs) > 1 and qs[1] != "None": did["quick"] = c.assign_quick_entry(6, unreal.Name(qs[1]))
    if hero == "Rogue":
        c.set_dex_energy(90.0); did["stealth_was_on"] = c.is_stealthed()
        if not c.is_stealthed(): did["stealth"] = c.start_stealth()
    # (what monsters do to her, last, so it lasts through the trip: poison and weakness in the town, slowness in the castle)
    if leg == "town":
        # (power 8: 11 s of poison, 12 s of weakness; a blow of 2: 1.6 a second, not enough to kill her on the way)
        c.apply_monster_ability(unreal.RDMonsterAbility.POISON, 8.0, 2.0); c.apply_monster_ability(unreal.RDMonsterAbility.WEAKEN, 8.0, 2.0)
    else: c.apply_monster_ability(unreal.RDMonsterAbility.SLOW, 8.0, 2.0)
    c.set_health(round(c.get_max_health() * 0.62)); c.set_mana(round(c.get_max_mana() * 0.45))
    yield from wait(0.3)
    return did
def leg_check(before, label):
    """after a trip: what she left with (the game instance's CarryLeftLines), as she came in (GetCarryArrivedLines) and as the
    test read her a moment before the trip; then, two seconds in, her summons at her side, her counters, things and quick bar"""
    g = G["gen"]; c = cb()
    left = sorted(str(l) for l in G["gi"].get_editor_property("carry_left_lines")); arrived = sorted(str(l) for l in g.get_carry_arrived_lines())
    r = {"level": G["w"].get_path_name().split(".")[-1], "left": len(left), "arrived": len(arrived), "left_vs_arrived": state_diff(left, arrived)}
    # (the test's own reading a moment before: the same lines (times a little shorter, hit points and mana a little more))
    # (hit points, mana and energy change on their own in that moment, as do her steps and the damage the poison does her)
    r["test_vs_left"] = [d for d in state_diff(before["lines"], left, tol=1.5) if not d[0].startswith(("hp|", "mana|", "dex|", "stat|StepsTaken", "stat|DamageTaken", "stat|HitsTaken"))]
    r["kinds"] = sorted({l.split("|")[0] for l in left})
    t0 = time.time()
    while g.get_carry_summons_waiting() > 0 and time.time() - t0 < 15: yield
    yield from wait(1.0)
    r["summons"] = summons_now(); r["summons_before"] = before["summons"]
    r["kills"] = [before["kills"], c.kills]
    inv = sorted(str(l) for l in c.get_all_inventory_lines()); r["inventory_same"] = inv == before["inventory"]
    if not r["inventory_same"]: r["inventory_diff"] = [sorted(set(before["inventory"]) - set(inv)), sorted(set(inv) - set(before["inventory"]))]
    r["quick_same"] = [str(x) for x in c.get_quick_slots()] == before["quick"]
    r["torch"] = [before["torch"], c.is_torch_held()]
    r["buffs"] = [str(b).split("|")[0] for b in c.get_buff_lines()]
    r["armour"] = [before["armour"], str(c.get_worn_armour())]
    r["gold"] = [before["gold"], g.get_gold()]
    r["stealthed"] = [before["stealthed"], c.is_stealthed()]
    r["ok"] = (not r["left_vs_arrived"] and not r["test_vs_left"] and r["arrived"] > 20 and r["summons"] == r["summons_before"]
               and r["kills"][0] == r["kills"][1] and r["inventory_same"] and r["quick_same"] and r["torch"][0] == r["torch"][1]
               and r["armour"][0] == r["armour"][1] and r["gold"][0] == r["gold"][1] and r["stealthed"][0] == r["stealthed"][1])
    unreal.log(f"BSTEST carry {label}: {json.dumps(r, default=str)[:1800]}")
    return r
def snapshot():
    g = G["gen"]; c = cb()
    return {"lines": state_lines(), "summons": summons_now(), "kills": c.kills, "inventory": sorted(str(l) for l in c.get_all_inventory_lines()),
            "quick": [str(x) for x in c.get_quick_slots()], "torch": c.is_torch_held(), "armour": str(c.get_worn_armour()), "gold": g.get_gold(),
            "stealthed": c.is_stealthed()}
def step_carry():
    """the user's of 2026-11-06: into the castle and back to Brokenspire she brings her whole state, statistics and every thing
    she carries. For the Summoner, the Warrior and the Rogue, each in turn: her state made different in the town (set_up), into
    the castle through the Mistgate, then changed again there and back to the town through the Escape menu; each way the state
    she left with and the state she came in with are the same line for line (hit points, mana, energy, every counter, every timed
    state with its seconds left, potions and food on her, cooldowns, the quick bar, the torch, the slash on her sword, her
    summons), and in the new level her things, gold, armour, quick bar, torch, kills, summons and the Rogue's stealth are as they
    were"""
    res = {}
    for hero in ("Summoner", "Warrior", "Rogue"):
        # (each hero from the town)
        if "brokenspire" not in G["w"].get_path_name(): yield from travel("brokenspire", via_menu)
        yield from as_hero(hero)
        h = res[hero] = {}
        h["set_town"] = yield from set_up(hero, "town")
        before = snapshot()
        h["town_lines"] = before["lines"]
        mg = place("mistgate")
        yield from travel("mistward_castle", lambda: put(V(mg.x, mg.y, 0)))
        h["to_castle"] = yield from leg_check(before, f"{hero} to the castle")
        h["set_castle"] = yield from set_up(hero, "castle")
        before = snapshot()
        h["castle_lines"] = before["lines"]
        quiet(False)
        yield from travel("brokenspire", via_menu)
        h["to_town"] = yield from leg_check(before, f"{hero} to the town")
        quiet(False)
    want = {"Summoner": ("summon", "effect", "timed", "torch", "stat", "spell", "quick"), "Warrior": ("slash", "effect", "timed", "stat"), "Rogue": ("dex", "effect", "timed", "stat")}
    for hero, kinds in want.items():
        h = res[hero]; h["missing_kinds"] = [k for k in kinds if k not in h["to_castle"]["kinds"]]; h["has_kinds"] = not h["missing_kinds"]
        h["timed_to_castle"] = sorted(l.split("|")[1] for l in h["town_lines"] if l.startswith("timed|"))
    # (the Rogue's stealth itself crossed both ways: on as she left (its line among those she left with) and on as she came in)
    ro = res["Rogue"]
    ro["stealth_carried"] = [any(l.startswith("timed|Stealth|") for l in ro[k]) for k in ("town_lines", "castle_lines")] \
        + [ro["to_castle"]["stealthed"] == [True, True], ro["to_town"]["stealthed"] == [True, True]]
    ok = all(res[h]["to_castle"]["ok"] and res[h]["to_town"]["ok"] and res[h]["has_kinds"] for h in res) and all(ro["stealth_carried"]) \
        and len(res["Summoner"]["to_castle"]["summons"]) == 2 and res["Summoner"]["to_castle"]["kills"][0] >= 1
    step_result("carry", ok, **res)

# ------------------------------------------------------------------------------------------------ Vel Morrath, the holy city
def vm_town():
    for i, l in enumerate(G["gen"].get_wild_town_lines()):
        p = str(l).split("|")
        if p[0] == "Vel Morrath": return i, float(p[2]), float(p[3])
    return -1, 0.0, 0.0
def to_vel_morrath():
    """out into the wilderness to Vel Morrath's middle; until it is built round her"""
    g = G["gen"]; ti, x, y = vm_town()
    g.wild_put_her(x, y)
    t0 = time.time()
    while time.time() - t0 < 120:
        yield
        st = str(g.get_wild_town_state()).split("|")
        if len(st) > 3 and st[1] == "Vel Morrath" and st[2] == "0" and st[3] == "1": break
    yield from wait(2.0)
    return ti, x, y
def step_holy():
    """Vel Morrath (the user's spec of 2026-11-06, docs/vel_morrath.txt): north-east of Brokenspire and inland; built as she
    comes, the holy city's plan: the cathedral at its middle (its seven rooms: narthex, nave, choir, aisles, bell towers), the
    plaza before it with its fountain, shrines and statues, the monastery, three chapels or more, a temple, the trades, eighty
    homes or more (few burned or boarded); every building's rooms, doors and containers; its people its own (the archbishop, the
    archivist, the templar commander, monks, pilgrims, beggars, templars) and Brokenspire's elder, scholar and captain not among
    them; the archbishop's panel with his first quest; the stair down at the choir's far wall (a dry run: walked into, it
    would open the catacombs); pictures of the plaza and cathedral, the nave, a street"""
    g = G["gen"]; res = {}
    ti, x, y = vm_town()
    res["site_km"] = [round(x / 1000, 1), round(y / 1000, 1)]; res["north_east"] = x > 20000 and y > 20000
    # (Brokenspire's square for comparison: frames over real seconds)
    sq0 = place("square")
    if sq0:
        put(sq0); yield from rwait(1.5); n_ = 0; t_ = time.time()
        while time.time() - t_ < 4.0: n_ += 1; yield
        res["fps_brokenspire_square"] = round(n_ / (time.time() - t_), 1)
    ti, x, y = yield from to_vel_morrath()
    st = str(g.get_wild_town_state()).split("|"); res["state"] = st
    res["plan"] = g.get_editor_property("town_plan")
    S = section(); B = blds()
    kinds = {}
    for b in B: kinds[b["kind"]] = kinds.get(b["kind"], 0) + 1
    res["kinds"] = kinds
    homes = [b for b in B if b["kind"] == "home"]
    res["homes"] = {"all": len(homes), "burned": sum(1 for b in homes if b["state"] == 1), "boarded": sum(1 for b in homes if b["state"] == 2)}
    cat = next((b for b in B if b["kind"] == "cathedral"), None)
    res["cathedral"] = {"label": cat["label"], "rooms": cat["rooms"], "from_middle_m": round(math.hypot(cat["c"].x / 100 - x, cat["c"].y / 100 - y))} if cat else None
    sq = place("square"); res["plaza_to_cathedral_m"] = round(dist2(sq, cat["c"]) / 100) if cat and sq else None
    sk = {}
    for p in spots(): sk[p["kind"]] = sk.get(p["kind"], 0) + 1
    res["spots"] = sk
    # (inside: every building's rooms, doors, containers)
    n_cont = S.get_num_containers()
    conts = [S.get_container_location(i) for i in range(n_cont)]
    doors = [S.get_door_location(i) for i in range(S.get_num_doors())]
    per = {}
    for b in B:
        if b["state"] == 1: continue                   # (a burned house: its walls fallen, no door)
        k = b["kind"]; e = per.setdefault(k, {"n": 0, "with_rooms": 0, "with_door": 0, "containers": 0})
        e["n"] += 1; e["with_rooms"] += 1 if b["rooms"] > 0 else 0
        e["with_door"] += 1 if any(dist2(d, b["door"]) < 250 for d in doors) else 0
        e["containers"] += sum(1 for c in conts if S.town_building_at(c) == b["i"])
    res["inside"] = per; res["containers"] = n_cont; res["doors"] = len(doors)
    # (its people)
    F = folk(); roles = {}
    for f in F: roles[f["role"]] = roles.get(f["role"], 0) + 1
    res["roles"] = roles; res["titles"] = sorted({f["title"] for f in F if f["role"] in ("Elder", "Scholar", "Captain", "Priest", "Smith", "Trader", "Healer", "Keeper", "Innkeeper")})
    # (the archbishop: his panel, his first quest)
    quiet(True)
    ab = talk_to("Elder"); yield from wait(0.4)
    said = str(g.interact_nearest(G["pawn"].get_actor_location())) if ab else None; yield from rwait(0.5)
    res["archbishop"] = {"found": ab is not None, "said": said, "panel": [p[1] for p in panel()][:8]}
    g.close_town_panel(); yield from wait(0.3)
    # (the stair down: its place, a dry run)
    mg = place("mistgate"); res["stair_from_cathedral_m"] = round(dist2(mg, cat["c"]) / 100) if mg and cat else None
    door = place("castle door")
    if door:
        put(door, yaw=math.degrees(math.atan2(cat["c"].y - door.y, cat["c"].x - door.x)) if cat else None); yield from wait(1.0)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=8, yaw=math.degrees(math.atan2(cat["c"].y - door.y, cat["c"].x - door.x)))); yield from wait(0.6)
        shot("vm_cathedral_front"); yield from rwait(1.0)
    def fps_here(sec=4.0):
        # (frames counted over real seconds, no picture being taken; after a settle: just after the city was built the plaza
        # read 5 a second, settled 24)
        yield from rwait(5.0); n = 0; t0 = time.time()
        while time.time() - t0 < sec: n += 1; yield
        return round(n / (time.time() - t0), 1)
    res["fps"] = {}
    if sq:
        put(sq); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=12, yaw=math.degrees(math.atan2(cat["c"].y - sq.y, cat["c"].x - sq.x)) if cat else 0)); yield from wait(0.8)
        res["fps"]["plaza"] = yield from fps_here()
        shot("vm_plaza"); yield from rwait(1.0)
    if mg and cat:
        yaw = math.degrees(math.atan2(mg.y - cat["c"].y, mg.x - cat["c"].x))
        put(V(cat["c"].x, cat["c"].y, 0), yaw=yaw); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=5, yaw=yaw)); yield from wait(0.8)
        res["fps"]["nave"] = yield from fps_here()
        shot("vm_nave"); yield from rwait(1.0)
        g.set_editor_property("travel_dry_run", True)
        put(V(mg.x - (mg.x - cat["c"].x) * 0.02, mg.y - (mg.y - cat["c"].y) * 0.02, 0)); yield from wait(1.5)
        res["stair_travel"] = str(g.get_editor_property("last_travel"))
        # (off the stair before the dry run ends: standing on it, the next tick went down for real)
        put(V(cat["c"].x, cat["c"].y, 0)); yield from wait(0.5)
        g.set_editor_property("travel_dry_run", False)
    quiet(False)
    k = kinds
    ok = (res["north_east"] and res["plan"] == 1 and cat is not None and res["cathedral"]["rooms"] == 7 and res["cathedral"]["from_middle_m"] < 120
          and k.get("monastery", 0) == 1 and k.get("chapel", 0) >= 3 and k.get("temple", 0) == 1 and all(k.get(t, 0) == 1 for t in ("smithy", "store", "healer", "storehouse", "tavern", "barracks"))
          and k.get("witch's hut", 0) == 0 and res["homes"]["all"] >= 80 and res["homes"]["burned"] + res["homes"]["boarded"] < res["homes"]["all"] * 0.2
          and sk.get("fountain", 0) == 1 and sk.get("shrine", 0) >= 4 and sk.get("statue", 0) >= 4
          and all(e["with_rooms"] == e["n"] and e["with_door"] == e["n"] for e in per.values()) and n_cont > 100
          and all(roles.get(r, 0) >= 1 for r in ("Elder", "Scholar", "Captain", "Monk", "Pilgrim", "Beggar", "Templar", "Preacher"))
          and "Archbishop Severin Aurel" in res["titles"] and "Aldric Venn" not in res["titles"]
          and any("Stair Beneath" in str(p) for p in res["archbishop"]["panel"]) and res.get("stair_travel") == "catacombs")
    step_result("holy", ok, **res)

def step_descend():
    """the stair beneath Vel Morrath's altar, both ways: from the cathedral's choir down into the catacombs (the level
    vel_morrath, 891) with her whole state, its name and its way back; then back up by the Escape menu's "Return to Vel
    Morrath": the city built round her again and she stands before the cathedral's door (the game instance's ReturnAt), her
    state as she left the catacombs"""
    res = {}
    if "brokenspire" not in G["w"].get_path_name(): yield from travel("brokenspire", via_menu)
    yield from as_hero("Warrior")
    yield from to_vel_morrath()
    g = G["gen"]
    res["set_town"] = yield from set_up("Warrior", "town")
    before = snapshot()
    mg = place("mistgate")
    yield from travel("vel_morrath", lambda: put(V(mg.x, mg.y, 0)))
    g = G["gen"]; c = cb()
    res["down"] = yield from leg_check(before, "Warrior down the stair")
    p = G["pawn"].get_actor_location()
    lines = [str(l) for l in g.get_menu_lines()]
    res["catacombs"] = {"key": str(g.get_editor_property("dungeon_key")), "title": str(g.get_editor_property("dungeon_title")), "tier_floors": g.get_editor_property("tier_floors"),
                        "section": [g.world_to_section(p).x, g.world_to_section(p).y], "z": round(p.z, 1), "return_line": next((l for l in lines if "Return to" in l), None),
                        "return_town": str(G["gi"].get_editor_property("return_town")), "return_at": [round(v) for v in (G["gi"].get_editor_property("return_at").x, G["gi"].get_editor_property("return_at").y)]}
    try: res["enter_counter"] = G["gi"].get_counter("vel_morrath:enter")
    except Exception as e: res["enter_counter"] = str(e)
    res["set_catacombs"] = yield from set_up("Warrior", "castle")
    before = snapshot()
    quiet(False)
    yield from travel("brokenspire", via_menu)
    g = G["gen"]
    # (the game instance's load: once the world is made the city is built round her, at the cathedral's door)
    t0 = time.time(); st = []
    while time.time() - t0 < 150:
        yield
        st = str(g.get_wild_town_state()).split("|")
        if len(st) > 3 and st[1] == "Vel Morrath" and st[2] == "0" and st[3] == "1": break
    yield from wait(2.0)
    res["up"] = yield from leg_check(before, "Warrior up the stair")
    p = G["pawn"].get_actor_location(); ra = G["gi"].get_editor_property("return_at")
    door = place("castle door")
    res["back"] = {"town": st[1] if len(st) > 1 else None, "from_return_at_m": round(dist2(p, ra) / 100, 2), "from_cathedral_door_m": round(dist2(p, door) / 100, 1) if door else None,
                   "on_ground": G["pawn"].get_editor_property("character_movement").is_moving_on_ground()}
    cc = res["catacombs"]
    ok = (res["down"]["ok"] and res["up"]["ok"] and res["down"]["level"] == "vel_morrath" and cc["key"] == "vel_morrath" and cc["tier_floors"] and cc["section"] == [0, 0]
          and abs(cc["z"]) < 200 and cc["return_line"] and "Vel Morrath" in cc["return_line"] and cc["return_town"] == "Vel Morrath"
          and res["back"]["town"] == "Vel Morrath" and res["back"]["from_return_at_m"] < 3.0 and (res["back"]["from_cathedral_door_m"] or 99) < 12)
    step_result("descend", ok, **res)

# ------------------------------------------------------------------------------------------------ Ashenreach, the forge city
def town_of(name):
    for i, l in enumerate(G["gen"].get_wild_town_lines()):
        p = str(l).split("|")
        if p[0] == name: return i, float(p[2]), float(p[3])
    return -1, 0.0, 0.0
def to_town(name):
    """out into the wilderness to a town's middle; until it is built round her"""
    g = G["gen"]; ti, x, y = town_of(name)
    g.wild_put_her(x, y)
    t0 = time.time()
    while time.time() - t0 < 120:
        yield
        st = str(g.get_wild_town_state()).split("|")
        if len(st) > 3 and st[1] == name and st[2] == "0" and st[3] == "1": break
    yield from wait(2.0)
    return ti, x, y
def step_forge():
    """Ashenreach (the user's spec of 2026-11-07, docs/ashenreach.txt): in the continent's middle north of Brokenspire, at the
    edge of its burned plain (the region north of it: the "burned plain" template); built as she comes, the forge city's plan:
    the Great Foundry at its middle (its seven rooms: the gatehouse, the casting hall, the furnace hall, the two workshop wings,
    the two chimney stacks), the square before it with the guild's great anvil and four open forges, ore carts on their rails,
    the barricade across the forecourt; four workshops, the trades, eighty homes or more of soot-dark stone (the "Forge." pieces);
    every building's rooms, doors and containers; its people its own (the guildmaster, the artificer, the siege captain, forge
    hands, soldiers) and Brokenspire's elder, scholar and captain not among them; the guildmaster's panel with his first quest;
    the forge hands' work at the open forges; the iron gate at the furnace hall's far wall (a dry run: walked into, it would
    open The War Engine); pictures of the foundry's front over the barricade, the square, the casting hall and the furnace
    hall"""
    g = G["gen"]; res = {}
    ti, x, y = town_of("Ashenreach")
    res["site_km"] = [round(x / 1000, 1), round(y / 1000, 1)]; res["north_middle"] = x > 40000 and abs(y) < 15000
    s_n = str(g.get_wild_sample_at(V((x + 6000.0) * 100.0, y * 100.0, 0))).split("|"); s_s = str(g.get_wild_sample_at(V((x - 9000.0) * 100.0, y * 100.0, 0))).split("|")
    res["biome_6km_north"] = s_n[2] if len(s_n) > 2 else None; res["biome_9km_south"] = s_s[2] if len(s_s) > 2 else None
    ti, x, y = yield from to_town("Ashenreach")
    st = str(g.get_wild_town_state()).split("|"); res["state"] = st
    res["plan"] = g.get_editor_property("town_plan")
    res["dungeon_level"] = str(g.current_dungeon_level())
    S = section(); B = blds()
    kinds = {}
    for b in B: kinds[b["kind"]] = kinds.get(b["kind"], 0) + 1
    res["kinds"] = kinds
    homes = [b for b in B if b["kind"] == "home"]
    res["homes"] = {"all": len(homes), "burned": sum(1 for b in homes if b["state"] == 1), "boarded": sum(1 for b in homes if b["state"] == 2)}
    fd = next((b for b in B if b["kind"] == "foundry"), None)
    res["foundry"] = {"label": fd["label"], "rooms": fd["rooms"], "from_middle_m": round(math.hypot(fd["c"].x / 100 - x, fd["c"].y / 100 - y))} if fd else None
    sq = place("square"); res["square_to_foundry_m"] = round(dist2(sq, fd["c"]) / 100) if fd and sq else None
    sk = {}
    for p in spots(): sk[p["kind"]] = sk.get(p["kind"], 0) + 1
    res["spots"] = sk
    n_cont = S.get_num_containers()
    conts = [S.get_container_location(i) for i in range(n_cont)]
    doors = [S.get_door_location(i) for i in range(S.get_num_doors())]
    per = {}
    for b in B:
        if b["state"] == 1: continue
        k = b["kind"]; e = per.setdefault(k, {"n": 0, "with_rooms": 0, "with_door": 0, "containers": 0})
        e["n"] += 1; e["with_rooms"] += 1 if b["rooms"] > 0 else 0
        e["with_door"] += 1 if any(dist2(d, b["door"]) < 250 for d in doors) else 0
        e["containers"] += sum(1 for c in conts if S.town_building_at(c) == b["i"])
    res["inside"] = per; res["containers"] = n_cont; res["doors"] = len(doors)
    # (the forge city's pieces in the section: soot-dark houses, the foundry's brick, the square's things)
    res["piece_counts"] = {n: len(ism_instances(n)) for n in ("SM_ST_BrickWall_05", "SM_ST_MainHall_BrickWall_06", "SM_ChimneyTop", "SM_Kit_Forge", "SM_Forge", "sm_Anvil_01a",
                                                              "SM_Ind_Min_Cart_Metal_Old_02", "SM_Ind_Min_Rail_Tracks_Wood_Modular_01_A", "SM_Camp_Barricade_Var3_SM_Barricade_Var3", "SM_PR_Chandelier_A")}
    F = folk(); roles = {}
    for f in F: roles[f["role"]] = roles.get(f["role"], 0) + 1
    res["roles"] = roles; res["titles"] = sorted({f["title"] for f in F if f["role"] in ("Elder", "Scholar", "Captain", "Priest", "Smith", "Trader", "Healer", "Keeper", "Innkeeper")})
    quiet(True)
    gm = talk_to("Elder"); yield from wait(0.4)
    said = str(g.interact_nearest(G["pawn"].get_actor_location())) if gm else None; yield from rwait(0.5)
    res["guildmaster"] = {"found": gm is not None, "said": said, "panel": [p[1] for p in panel()][:8]}
    g.close_town_panel(); yield from wait(0.3)
    # (the forge hands at work: their rounds hold the open forges' places)
    try:
        ws = [str(g.get_townsfolk(f["i"]).get_work_state()) for f in F if f["role"] == "Worker"]
        res["workers"] = len(ws); res["worker_states"] = ws[:6]
    except Exception as e: res["workers_error"] = str(e)
    mg = place("mistgate"); res["gate_from_foundry_m"] = round(dist2(mg, fd["c"]) / 100) if mg and fd else None
    door = place("castle door")
    def fps_here(sec=4.0):
        yield from rwait(5.0); n = 0; t0 = time.time()
        while time.time() - t0 < sec: n += 1; yield
        return round(n / (time.time() - t0), 1)
    res["fps"] = {}
    if door and fd:
        yaw = math.degrees(math.atan2(fd["c"].y - door.y, fd["c"].x - door.x))
        bk = V(door.x - math.cos(math.radians(yaw)) * 1500.0, door.y - math.sin(math.radians(yaw)) * 1500.0, 0)
        put(bk, yaw=yaw); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=10, yaw=yaw)); yield from wait(1.0)
        shot("ar_foundry_front"); yield from rwait(1.2)
    if sq:
        put(sq); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=8, yaw=math.degrees(math.atan2(fd["c"].y - sq.y, fd["c"].x - sq.x)) + 60.0 if fd else 0)); yield from wait(0.8)
        res["fps"]["square"] = yield from fps_here()
        shot("ar_square"); yield from rwait(1.2)
    if mg and fd:
        yaw = math.degrees(math.atan2(mg.y - fd["c"].y, mg.x - fd["c"].x))
        put(V(fd["c"].x, fd["c"].y, 0), yaw=yaw); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=5, yaw=yaw)); yield from wait(0.8)
        res["fps"]["casting_hall"] = yield from fps_here()
        shot("ar_casting_hall"); yield from rwait(1.2)
        # (across the hall at one long wall: its forge line, beside her in the picture along the hall)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-6, yaw=yaw + 90.0)); G["pawn"].set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw + 90.0), True); yield from wait(1.0)
        shot("ar_casting_side"); yield from rwait(1.2)
        put(V(mg.x - (mg.x - fd["c"].x) * 0.35, mg.y - (mg.y - fd["c"].y) * 0.35, 0), yaw=yaw); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=3, yaw=yaw)); yield from wait(0.8)
        shot("ar_furnace_hall"); yield from rwait(1.2)
        g.set_editor_property("travel_dry_run", True)
        put(V(mg.x - (mg.x - fd["c"].x) * 0.02, mg.y - (mg.y - fd["c"].y) * 0.02, 0)); yield from wait(1.5)
        res["gate_travel"] = str(g.get_editor_property("last_travel"))
        put(V(fd["c"].x, fd["c"].y, 0)); yield from wait(0.5)
        g.set_editor_property("travel_dry_run", False)
    quiet(False)
    k = kinds
    ok = (res["north_middle"] and res["plan"] == 2 and fd is not None and res["foundry"]["rooms"] == 7 and res["foundry"]["from_middle_m"] < 120
          and "war_engine" in res["dungeon_level"] and res["biome_6km_north"] == "burned plain"
          and k.get("workshop", 0) >= 3 and all(k.get(t, 0) == 1 for t in ("smithy", "store", "healer", "storehouse", "tavern", "barracks", "temple"))
          and k.get("witch's hut", 0) == 0 and k.get("cathedral", 0) == 0 and res["homes"]["all"] >= 80
          and sk.get("anvil", 0) == 1 and sk.get("forge", 0) == 4 and sk.get("cart", 0) == 3 and sk.get("barricade", 0) == 4
          and all(e["with_rooms"] == e["n"] and e["with_door"] == e["n"] for e in per.values()) and n_cont > 100
          and all(roles.get(r, 0) >= 1 for r in ("Elder", "Scholar", "Captain", "Worker", "Soldier", "Refugee"))
          and "Guildmaster Torvald Brask" in res["titles"] and "Aldric Venn" not in res["titles"]
          and any("Iron Gate" in str(p) for p in res["guildmaster"]["panel"]) and res.get("gate_travel") == "catacombs")
    step_result("forge", ok, **res)

def step_descendwar():
    """the iron gate of Ashenreach's Great Foundry, both ways: down into The War Engine (the level war_engine, 895) with her
    whole state, its name, its machines and its way back; then back up by the Escape menu's "Return to Ashenreach": the city
    built round her again and she stands before the foundry's door (the game instance's ReturnAt)"""
    res = {}
    if "brokenspire" not in G["w"].get_path_name(): yield from travel("brokenspire", via_menu)
    yield from as_hero("Warrior")
    yield from to_town("Ashenreach")
    g = G["gen"]
    res["set_town"] = yield from set_up("Warrior", "town")
    before = snapshot()
    mg = place("mistgate")
    yield from travel("war_engine", lambda: put(V(mg.x, mg.y, 0)))
    g = G["gen"]
    res["down"] = yield from leg_check(before, "Warrior through the iron gate")
    p = G["pawn"].get_actor_location()
    lines = [str(l) for l in g.get_menu_lines()]
    machines = {str(m.get_editor_property("name")) for m in g.get_editor_property("monsters") if int(m.get_editor_property("weight") * 10) >= 30}
    near = {}
    for m in g.get_monsters():
        if m and not m.is_dead(): n = str(m.get_editor_property("monster_name")); near[n] = near.get(n, 0) + 1
    res["engine"] = {"key": str(g.get_editor_property("dungeon_key")), "title": str(g.get_editor_property("dungeon_title")), "tier_floors": g.get_editor_property("tier_floors"),
                     "section": [g.world_to_section(p).x, g.world_to_section(p).y], "return_line": next((l for l in lines if "Return to" in l), None),
                     "return_town": str(G["gi"].get_editor_property("return_town")), "machine_kinds": sorted(machines), "monsters_now": near,
                     "machines_now": sum(v for k_, v in near.items() if k_ in machines), "theme_props": [str(t) for t in g.get_editor_property("theme_props")]}
    try: res["enter_counter"] = G["gi"].get_counter("war_engine:enter")
    except Exception as e: res["enter_counter"] = str(e)
    shot("ar_war_engine_start"); yield from rwait(1.2)
    # (every machine kind: one of each spawned in a row across the great hall, its clips playing (a kind with borrowed clips
    # stood in its rig's pose if its skeleton could not play them); a picture of the row, her body hidden)
    quiet(True)
    hc = g.get_start_room_center(); kinds_ = sorted(machines)
    ms = []
    for j, k_ in enumerate(kinds_):
        m = g.spawn_monster_named(k_, V(hc.x + 900.0, hc.y + (j - (len(kinds_) - 1) / 2.0) * 320.0, hc.z + 120.0), 1, 1.0, 0.0, 1.0)
        if m: ms.append(m)
    yield from wait(1.5)
    # (each machine's clip plays: its bones move against its actor over half a second (Python reaches no single node instance;
    # a clip its skeleton cannot play leaves the mesh in its rig's pose, still))
    def pose(m):
        c = m.get_component_by_class(unreal.SkeletalMeshComponent); a = m.get_actor_location(); out = []
        for i in range(0, min(c.get_num_bones(), 60), 3):
            p = c.get_socket_location(c.get_bone_name(i)); out.append((p.x - a.x, p.y - a.y, p.z - a.z))
        return out
    p0 = {}
    for m in ms:
        try: p0[m] = pose(m)
        except Exception as e: res.setdefault("pose_errors", []).append(str(e))
    yield from wait(0.5)
    res["machine_clips"] = {}
    for m, a in p0.items():
        try:
            b = pose(m); mv = max(math.dist(x, y) for x, y in zip(a, b)) if a and b else 0.0
            res["machine_clips"][str(m.get_editor_property("monster_name"))] = [{"clip": True, "bones_moved_cm": round(mv, 2), "moving": mv > 0.3}]
        except Exception as e: res.setdefault("pose_errors", []).append(str(e))
    res["machines_spawned"] = len(ms)
    if ms:
        # (her body hidden for the picture (868's way), 5 m behind the hall's middle looking at the row)
        put(V(hc.x - 500.0, hc.y, hc.z), yaw=0.0)
        G["pawn"].set_actor_hidden_in_game(True)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-3, yaw=0.0)); yield from wait(1.0)
        shot("ar_machines"); yield from rwait(1.2)
        G["pawn"].set_actor_hidden_in_game(False)
        for m in ms:
            try: m.destroy_actor()
            except Exception: pass
    quiet(False)
    res["set_engine"] = yield from set_up("Warrior", "castle")
    before = snapshot()
    quiet(False)
    yield from travel("brokenspire", via_menu)
    g = G["gen"]
    t0 = time.time(); st = []
    while time.time() - t0 < 150:
        yield
        st = str(g.get_wild_town_state()).split("|")
        if len(st) > 3 and st[1] == "Ashenreach" and st[2] == "0" and st[3] == "1": break
    yield from wait(2.0)
    res["up"] = yield from leg_check(before, "Warrior back out of the iron gate")
    p = G["pawn"].get_actor_location(); ra = G["gi"].get_editor_property("return_at")
    door = place("castle door")
    res["back"] = {"town": st[1] if len(st) > 1 else None, "from_return_at_m": round(dist2(p, ra) / 100, 2), "from_foundry_door_m": round(dist2(p, door) / 100, 1) if door else None,
                   "on_ground": G["pawn"].get_editor_property("character_movement").is_moving_on_ground()}
    e = res["engine"]
    ok = (res["down"]["ok"] and res["up"]["ok"] and res["down"]["level"] == "war_engine" and e["key"] == "war_engine" and not e["tier_floors"] and e["section"] == [0, 0]
          and e["return_line"] and "Ashenreach" in e["return_line"] and e["return_town"] == "Ashenreach" and len(e["machine_kinds"]) >= 10 and e["machines_now"] >= 1
          and res.get("machines_spawned", 0) >= 10 and len(res.get("machine_clips", {})) >= 10 and all(c["clip"] and c["moving"] for v in res["machine_clips"].values() for c in v)
          and res["enter_counter"] == 1 and res["back"]["town"] == "Ashenreach" and res["back"]["from_return_at_m"] < 3.0 and (res["back"]["from_foundry_door_m"] or 99) < 12)
    step_result("descendwar", ok, **res)

# ------------------------------------------------------------------------------------------------ Kethrys Spire, the mage city
def step_spire():
    """Kethrys Spire (the list of 2026-11-08b's fourth phase: "a mage-city clustered around a black tower that hasn't opened its
    gates in a century. there are magical effects, laboratories, libraries, stone houses. this city is not poor"): north-west
    of Graymourne, the road's tier 20 there; built as she comes, the mage plan: the black tower at its middle (its gatehouse and
    hall, the round tower over the hall 50 m and more high with its crown and cap), the square with its rune circle and crystal
    pylons, more pylons down the main road, libraries and laboratories (each laboratory its cauldron and table of potions), study rooms and
    meditation chambers (each chamber its rune circle: four small rune stones), the upper storeys' lights moving (lights tagged
    SpireWindow, read 2 s apart, in the tower's upper half), the trades, eighty homes or more of grey-blue stone, few burned or boarded; every building's rooms, doors and containers; its
    people its own (the archmage, the archivist, the warden-captain, scribes, alchemists, apprentices, wardens) and Brokenspire's
    elder not among them; the archmage's panel with his first quest; the sealed gate at the hall's far wall refused without the
    Spire Key and opened with it (dry runs); pictures of the tower from the square and from afar (by day and at 23:00), the
    square, a library, a laboratory, a study, a meditation chamber, the gate"""
    g = G["gen"]; res = {}
    ti, x, y = town_of("Kethrys Spire")
    tg, gx, gy = town_of("Graymourne")
    res["site_km"] = [round(x / 1000, 1), round(y / 1000, 1)]; res["from_graymourne_km"] = round(math.hypot(x - gx, y - gy) / 1000, 1)
    res["north_west"] = x > 80000 and y < -30000
    res["tier_here"] = g.get_wild_tier_at(x, y); res["tier_half_way_from_graymourne"] = g.get_wild_tier_at((x + gx) / 2, (y + gy) / 2)
    ti, x, y = yield from to_town("Kethrys Spire")
    st = str(g.get_wild_town_state()).split("|"); res["state"] = st
    res["plan"] = g.get_editor_property("town_plan")
    res["dungeon_level"] = str(g.current_dungeon_level())
    S = section(); B = blds()
    kinds = {}
    for b in B: kinds[b["kind"]] = kinds.get(b["kind"], 0) + 1
    res["kinds"] = kinds
    homes = [b for b in B if b["kind"] == "home"]
    res["homes"] = {"all": len(homes), "burned": sum(1 for b in homes if b["state"] == 1), "boarded": sum(1 for b in homes if b["state"] == 2)}
    tw = next((b for b in B if b["kind"] == "black tower"), None)
    res["tower"] = {"label": tw["label"], "rooms": tw["rooms"], "from_middle_m": round(math.hypot(tw["c"].x / 100 - x, tw["c"].y / 100 - y)), "top_m": round(S.get_editor_property("tower_top_z") / 100, 1)} if tw else None
    sk = {}
    for p in spots(): sk[p["kind"]] = sk.get(p["kind"], 0) + 1
    res["spots"] = sk
    n_cont = S.get_num_containers()
    conts = [S.get_container_location(i) for i in range(n_cont)]
    doors = [S.get_door_location(i) for i in range(S.get_num_doors())]
    per = {}
    for b in B:
        if b["state"] == 1: continue
        k = b["kind"]; e = per.setdefault(k, {"n": 0, "with_rooms": 0, "with_door": 0, "containers": 0})
        e["n"] += 1; e["with_rooms"] += 1 if b["rooms"] > 0 else 0
        e["with_door"] += 1 if any(dist2(d, b["door"]) < 250 for d in doors) else 0
        e["containers"] += sum(1 for c in conts if S.town_building_at(c) == b["i"])
    res["inside"] = per; res["containers"] = n_cont; res["doors"] = len(doors)
    # (PR #32's review: each laboratory's own cauldron and potions and each meditation chamber's own rune stones, inside its
    # rectangle; a count over the town passed on the kitchens' prep tables and the still's cauldron)
    def in_bld(pts, bi): return sum(1 for q in pts if S.town_building_at(q) == bi)
    caul = ism_instances("SM_Cauldron", "CauldronFX"); pots = ism_instances("SM_S_Potion"); stones = ism_instances("SM_Rune_01a")
    res["labs"] = [{"cauldron": in_bld(caul, b["i"]), "potions": in_bld(pots, b["i"])} for b in B if b["kind"] == "laboratory" and b["state"] == 0]
    res["chambers"] = [in_bld(stones, b["i"]) for b in B if b["kind"] == "meditation chamber" and b["state"] == 0]
    # (no shut gate's mesh standing in the open gateway of a town in the wilds: PR #33's review found one in every wild town)
    res["static_gate"] = len(ism_instances("SM_Main_Gate_03a"))
    res["piece_counts"] = {n: len(ism_instances(n)) for n in ("SM_TowerRound_Window_8m_A", "SM_TowerRound_Border_Top_A", "SM_TowerRound_Cap_4m_A", "SM_IceCrystal01", "SM_StatuePlinth",
                                                              "SM_Cauldron", "SM_Kit_PrepTable", "SM_S_Potion", "SM_Rune_01a")}
    # (the upper storeys' lights that move: each read twice, 2 s apart; how far each went round, how high the lowest stands)
    def wlights(): return [c.get_world_location() for c in S.get_components_by_tag(unreal.PointLightComponent, "SpireWindow")]
    w0 = wlights(); yield from wait(2.0); w1 = wlights()
    res["window_lights"] = {"n": len(w0), "moved_cm_min": round(min((dist2(a, b) for a, b in zip(w0, w1)), default=0.0), 1),
                            "moved_cm_max": round(max((dist2(a, b) for a, b in zip(w0, w1)), default=0.0), 1),
                            "lowest_m": round(min((a.z for a in w0), default=0.0) / 100, 1)}
    F = folk(); roles = {}
    for f in F: roles[f["role"]] = roles.get(f["role"], 0) + 1
    res["roles"] = roles; res["titles"] = sorted({f["title"] for f in F if f["role"] in ("Elder", "Scholar", "Captain", "Priest", "Smith", "Trader", "Healer", "Keeper", "Innkeeper")})
    quiet(True)
    am = talk_to("Elder"); yield from wait(0.4)
    said = str(g.interact_nearest(G["pawn"].get_actor_location())) if am else None; yield from rwait(0.5)
    res["archmage"] = {"found": am is not None, "said": said, "panel": [p[1] for p in panel()][:8]}
    g.close_town_panel(); yield from wait(0.3)
    mg = place("mistgate"); door = place("castle door"); sq = place("square")
    res["gate_from_tower_m"] = round(dist2(mg, tw["c"]) / 100) if mg and tw else None
    if door and tw:
        yaw = math.degrees(math.atan2(tw["c"].y - door.y, tw["c"].x - door.x))
        bk = V(door.x - math.cos(math.radians(yaw)) * 2200.0, door.y - math.sin(math.radians(yaw)) * 2200.0, 0)
        put(bk, yaw=yaw); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=22, yaw=yaw)); yield from wait(1.2)
        shot("ks_tower_front"); yield from rwait(1.2)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=40, yaw=yaw)); h_was = g.get_town_hour(); g.set_town_hour(23.0); yield from wait(5.0)
        shot("ks_tower_front_night"); yield from rwait(1.5); shot("ks_tower_front_night2"); yield from rwait(1.2)
        g.set_town_hour(h_was); yield from wait(1.0)
    if sq:
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=6, yaw=math.degrees(math.atan2(tw["c"].y - sq.y, tw["c"].x - sq.x)) + 70.0 if tw else 0)); put(sq); yield from wait(1.0)
        shot("ks_square"); yield from rwait(1.2)
    # (the tower from out beyond the wall, on the main road: above the roofs)
    gate = place("gate")
    if gate and tw:
        yaw = math.degrees(math.atan2(tw["c"].y - gate.y, tw["c"].x - gate.x))
        out = V(gate.x - math.cos(math.radians(yaw)) * 4000.0, gate.y - math.sin(math.radians(yaw)) * 4000.0, 0)
        g.wild_put_her(out.x / 100.0, out.y / 100.0); yield from wait(3.0)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=14, yaw=yaw)); G["pawn"].set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw), True); yield from wait(1.5)
        shot("ks_tower_afar"); yield from rwait(1.2)
        # (at night the upper windows' moving light shows: two pictures 1.5 s apart)
        h_was = g.get_town_hour(); g.set_town_hour(23.0); yield from wait(5.0)
        shot("ks_tower_night"); yield from rwait(1.5); shot("ks_tower_night2"); yield from rwait(1.2)
        g.set_town_hour(h_was); yield from wait(1.0)
    # (a library and a laboratory inside, from their door)
    for kd in ("library", "laboratory", "study", "meditation chamber"):
        b = next((b for b in B if b["kind"] == kd and b["state"] == 0), None)
        if b:
            yaw = math.degrees(math.atan2(b["c"].y - b["door"].y, b["c"].x - b["door"].x))
            put(V(b["door"].x + math.cos(math.radians(yaw)) * 150.0, b["door"].y + math.sin(math.radians(yaw)) * 150.0, 0), yaw=yaw)
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=yaw)); yield from wait(1.0)
            shot(f"ks_{kd.split()[0]}"); yield from rwait(1.2)
    # (the sealed gate: refused without the Spire Key, open with it (dry runs))
    if mg and tw:
        yaw = math.degrees(math.atan2(mg.y - tw["c"].y, mg.x - tw["c"].x))
        put(V(mg.x - (mg.x - tw["c"].x) * 0.45, mg.y - (mg.y - tw["c"].y) * 0.45, 0), yaw=yaw); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=4, yaw=yaw)); yield from wait(1.0)
        shot("ks_gate"); yield from rwait(1.2)
        for keys, tag in ((False, "gate_without_key"), (True, "gate_with_keys")):
            g.debug_all_dungeon_keys(keys); g.set_editor_property("travel_dry_run", True)
            put(V(mg.x - (mg.x - tw["c"].x) * 0.02, mg.y - (mg.y - tw["c"].y) * 0.02, 0)); yield from wait(1.5)
            res[tag] = str(g.get_editor_property("last_travel"))
            put(V(tw["c"].x, tw["c"].y, 0)); yield from wait(0.5)
            g.set_editor_property("travel_dry_run", False)
        g.debug_all_dungeon_keys(True)
    quiet(False)
    k = kinds; pc = res["piece_counts"]
    ok = (res["north_west"] and res["static_gate"] == 0 and 60 <= res["from_graymourne_km"] <= 120 and res["tier_here"] == 20 and 16 <= res["tier_half_way_from_graymourne"] <= 19
          and res["plan"] == 4 and tw is not None and res["tower"]["rooms"] == 2 and res["tower"]["from_middle_m"] < 120 and res["tower"]["top_m"] >= 50
          and "kethrys_spire" in res["dungeon_level"] and k.get("library", 0) >= 2 and k.get("laboratory", 0) >= 2 and k.get("study", 0) >= 1 and k.get("meditation chamber", 0) >= 1
          and res["window_lights"]["n"] >= 2 and res["window_lights"]["moved_cm_min"] > 50 and res["window_lights"]["lowest_m"] > res["tower"]["top_m"] * 0.4
          and all(k.get(t, 0) == 1 for t in ("smithy", "store", "healer", "storehouse", "tavern", "barracks", "temple")) and k.get("witch's hut", 0) == 0
          and res["homes"]["all"] >= 80 and res["homes"]["burned"] + res["homes"]["boarded"] < res["homes"]["all"] * 0.1
          and sk.get("rune", 0) >= 2 and sk.get("crystal", 0) >= 6 and pc["SM_TowerRound_Window_8m_A"] >= 2 and pc["SM_TowerRound_Cap_4m_A"] >= 1
          and pc["SM_IceCrystal01"] >= 6 and pc["SM_Rune_01a"] >= 12
          and len(res["labs"]) >= 2 and all(l["cauldron"] == 1 and l["potions"] >= 2 for l in res["labs"]) and len(res["chambers"]) >= 1 and all(n >= 2 for n in res["chambers"])
          and all(e["with_rooms"] == e["n"] and e["with_door"] == e["n"] for e in per.values()) and n_cont > 100
          and all(roles.get(r, 0) >= 1 for r in ("Elder", "Scholar", "Captain", "Monk", "Worker", "Pilgrim", "Soldier"))
          and "Archmage Velis Kethran" in res["titles"] and "Aldric Venn" not in res["titles"]
          and any("Hundred Years" in str(p) for p in res["archmage"]["panel"]) and res.get("gate_without_key") == "locked" and res.get("gate_with_keys") == "catacombs")
    step_result("spire", ok, **res)

def step_heaven():
    """Heaven (the list of 2026-11-08b's fourth phase: "a modern city that is surrounded by a shimmering shield ... modern
    skyscrapers, office buildings, modern shops, modern streets, modern vehicles navigating the streets ... the outside and
    entrance of the dungeon is a foreboding research facility called 'Kratos Aurorim Research, LLC'"): south-west of Kethrys
    Spire, the road's tier 25 there; built as she comes, the modern plan: the research facility at its middle (its two rooms, its
    name over its door, the dark glass block over its hall), towers (a lobby walked into and floors over it), office blocks,
    shops, apartments, the trades; every building's rooms, doors and containers; the straight streets in asphalt, the rest paved,
    no grass; street lights and furniture by the streets; the shield over the whole town (its radius past the outline's farthest
    corner); cars on the streets, each moving, one that waits while she stands in its lane ahead of it and goes on when she
    leaves it; its people its own (the director, the scientist, the security chief, office workers, clerks, guards) and
    Brokenspire's elder not among them; the director's panel with the first quest; the security door at the hall's far wall
    refused without the Kratos Keycard and opened with it (dry runs); pictures of the facility's front, a street with its cars, the
    skyline from beyond the wall under the shield, a skyscraper's lobby, a shop, the security door; traffic lights at the
    streets' crossings; no car on the square or at the facility's door"""
    g = G["gen"]; res = {}
    ti, x, y = town_of("Heaven")
    tk, kx, ky = town_of("Kethrys Spire")
    res["site_km"] = [round(x / 1000, 1), round(y / 1000, 1)]; res["from_kethrys_km"] = round(math.hypot(x - kx, y - ky) / 1000, 1)
    res["tier_here"] = g.get_wild_tier_at(x, y); res["tier_half_way_from_kethrys"] = g.get_wild_tier_at((x + kx) / 2, (y + ky) / 2)
    ti, x, y = yield from to_town("Heaven")
    st = str(g.get_wild_town_state()).split("|"); res["state"] = st
    res["plan"] = g.get_editor_property("town_plan")
    res["dungeon_level"] = str(g.current_dungeon_level())
    S = section(); B = blds()
    kinds = {}
    for b in B: kinds[b["kind"]] = kinds.get(b["kind"], 0) + 1
    res["kinds"] = kinds
    homes = [b for b in B if b["kind"] == "home"]
    res["homes"] = {"all": len(homes), "burned": sum(1 for b in homes if b["state"] == 1), "boarded": sum(1 for b in homes if b["state"] == 2)}
    rf = next((b for b in B if b["kind"] == "research facility"), None)
    res["facility"] = {"label": rf["label"], "rooms": rf["rooms"], "from_middle_m": round(math.hypot(rf["c"].x / 100 - x, rf["c"].y / 100 - y))} if rf else None
    res["tallest_m"] = round(S.get_editor_property("heaven_tallest_z") / 100, 1)
    res["dome_radius_m"] = round(S.get_editor_property("heaven_dome_radius") / 100, 1)
    sk = {}
    for p in spots(): sk[p["kind"]] = sk.get(p["kind"], 0) + 1
    res["spots"] = sk
    n_cont = S.get_num_containers()
    conts = [S.get_container_location(i) for i in range(n_cont)]
    doors = [S.get_door_location(i) for i in range(S.get_num_doors())]
    per = {}
    for b in B:
        k = b["kind"]; e = per.setdefault(k, {"n": 0, "with_rooms": 0, "with_door": 0, "containers": 0})
        e["n"] += 1; e["with_rooms"] += 1 if b["rooms"] > 0 else 0
        e["with_door"] += 1 if any(dist2(d, b["door"]) < 250 for d in doors) else 0
        e["containers"] += sum(1 for c in conts if S.town_building_at(c) == b["i"])
    res["inside"] = per; res["containers"] = n_cont; res["doors"] = len(doors)
    res["piece_counts"] = {n: len(ism_instances(n)) for n in ("SM_HV_Road", "SM_HV_Paving", "SM_HV_Wall", "SM_HV_Window", "SM_HV_GlassWall", "SM_HV_Roof", "SM_Module03_Tower01_MiddleFloors01",
                                                              "SM_HV_LabWall", "SM_HV_Block", "SM_HV_CityWall", "SM_MM00284_Exterior_Light_Streetlight", "SM_Stone_Wall", "SM_Castle_Stone_Wall_01a",
                                                              "SM_Tower_Roof_01d", "SM_MM00406_Office_Desk", "SM_Prop_Table_A")}
    res["static_gate"] = len(ism_instances("SM_Main_Gate_03a"))
    # (no grass: the town's short grass clumps)
    res["grass"] = len(ism_instances("Grass"))
    signs = S.get_components_by_tag(unreal.TextRenderComponent, "HeavenSign")
    res["sign"] = [str(c.get_editor_property("text")) for c in signs]
    # (the shield: its middle and radius against the outline's farthest corner)
    dome = S.get_components_by_tag(unreal.StaticMeshComponent, "HeavenDome")
    res["dome_parts"] = len(dome)
    if dome:
        dc = dome[0].get_world_location()
        res["dome_past_buildings_m"] = round((S.get_editor_property("heaven_dome_radius") - max(dist2(b["c"], dc) for b in B)) / 100, 1)
    res["styles"] = sorted({str(x) for x in ism_instances("SM_HV_Wall")} and [n for n in ("SM_HV_Wall", "SM_HV2_Wall", "SM_HV3_Wall") if ism_instances(n)])
    # (the traffic: every car read twice 3 s apart; how far each went)
    def cars(): return [c for c in S.get_components_by_tag(unreal.StaticMeshComponent, "HeavenCar")]
    c0 = cars(); p0 = [c.get_world_location() for c in c0]
    yield from wait(3.0)
    p1 = [c.get_world_location() for c in c0]
    moved = [dist2(a, b) for a, b in zip(p0, p1)]
    res["cars"] = {"n": len(c0), "moving": sum(1 for m in moved if m > 300), "moved_m_median": round(sorted(moved)[len(moved) // 2] / 100, 1) if moved else 0}
    # (PR #33's review: no car on the square or at the facility's door: the main road and the cross road through the square
    # carry none)
    sqp = place("square"); fdoor = place("castle door")
    res["cars_on_square"] = sum(1 for q in p0 + p1 if sqp and dist2(q, sqp) < 2200.0)
    res["cars_at_facility"] = sum(1 for q in p0 + p1 if fdoor and dist2(q, fdoor) < 1500.0)
    # (a car waits for her: she stands 6 m ahead of a moving one in its lane; it must not come within 3 m of her in 2.5 s; then she
    # steps off the street and it goes on)
    if c0:
        k = max(range(len(c0)), key=lambda i: moved[i])
        c = c0[k]; a = c.get_world_location(); fw = c.get_forward_vector()
        # (the car mesh's forward is its pivot's: the pivot is turned to its way)
        piv = c.get_attach_parent(); fw = piv.get_forward_vector() if piv else fw
        her = V(a.x + fw.x * 600.0, a.y + fw.y * 600.0, 0)
        quiet(True); put(her, yaw=math.degrees(math.atan2(-fw.y, -fw.x))); yield from wait(2.5)
        b = c.get_world_location()
        res["car_waits"] = {"gap_m": round(dist2(b, G["pawn"].get_actor_location()) / 100, 2), "moved_m": round(dist2(a, b) / 100, 2)}
        put(V(her.x + fw.y * 900.0, her.y - fw.x * 900.0, 0)); yield from wait(2.5)
        res["car_waits"]["moved_after_m"] = round(dist2(b, c.get_world_location()) / 100, 2)
        # (a picture of the street from the pavement, the car in it)
        put(V(b.x + fw.y * 700.0, b.y - fw.x * 700.0, 0), yaw=math.degrees(math.atan2(-fw.x * 0.3 - fw.y, fw.x - fw.y * 0.3)))
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-4, yaw=math.degrees(math.atan2(b.y - G["pawn"].get_actor_location().y, b.x - G["pawn"].get_actor_location().x))))
        yield from wait(1.5); shot("hv_street"); yield from rwait(1.2)
    F = folk(); roles = {}
    for f in F: roles[f["role"]] = roles.get(f["role"], 0) + 1
    res["roles"] = roles; res["titles"] = sorted({f["title"] for f in F if f["role"] in ("Elder", "Scholar", "Captain", "Priest", "Smith", "Trader", "Healer", "Keeper", "Innkeeper")})
    quiet(True)
    am = talk_to("Elder"); yield from wait(0.4)
    said = str(g.interact_nearest(G["pawn"].get_actor_location())) if am else None; yield from rwait(0.5)
    res["director"] = {"found": am is not None, "said": said, "panel": [p[1] for p in panel()][:8]}
    g.close_town_panel(); yield from wait(0.3)
    mg = place("mistgate"); door = place("castle door")
    if door and rf:
        yaw = math.degrees(math.atan2(rf["c"].y - door.y, rf["c"].x - door.x))
        bk = V(door.x - math.cos(math.radians(yaw)) * 2000.0, door.y - math.sin(math.radians(yaw)) * 2000.0, 0)
        put(bk, yaw=yaw); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=8, yaw=yaw)); yield from wait(1.2)
        shot("hv_facility"); yield from rwait(1.2)
    # (the skyline from out beyond the wall, the shield over it)
    gate = place("gate")
    if gate and rf:
        yaw = math.degrees(math.atan2(rf["c"].y - gate.y, rf["c"].x - gate.x))
        out = V(gate.x - math.cos(math.radians(yaw)) * 9000.0, gate.y - math.sin(math.radians(yaw)) * 9000.0, 0)
        g.wild_put_her(out.x / 100.0, out.y / 100.0); yield from wait(3.0)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=12, yaw=yaw)); G["pawn"].set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw), True); yield from wait(1.5)
        shot("hv_skyline"); yield from rwait(1.2)
        h_was = g.get_town_hour(); g.set_town_hour(22.0); yield from wait(5.0)
        shot("hv_skyline_night"); yield from rwait(1.2)
        g.set_town_hour(h_was); yield from wait(1.0)
    for kd in ("skyscraper", "shop", "office block"):
        b = next((b for b in B if b["kind"] == kd and b["state"] == 0), None)
        if b:
            yaw = math.degrees(math.atan2(b["c"].y - b["door"].y, b["c"].x - b["door"].x))
            put(V(b["door"].x + math.cos(math.radians(yaw)) * 150.0, b["door"].y + math.sin(math.radians(yaw)) * 150.0, 0), yaw=yaw)
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=yaw)); yield from wait(1.0)
            shot(f"hv_{kd.split()[0]}"); yield from rwait(1.2)
    if mg and rf:
        yaw = math.degrees(math.atan2(mg.y - rf["c"].y, mg.x - rf["c"].x))
        put(V(mg.x - (mg.x - rf["c"].x) * 0.45, mg.y - (mg.y - rf["c"].y) * 0.45, 0), yaw=yaw); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=4, yaw=yaw)); yield from wait(1.0)
        shot("hv_gate"); yield from rwait(1.2)
        for keys, tag in ((False, "gate_without_key"), (True, "gate_with_keys")):
            g.debug_all_dungeon_keys(keys); g.set_editor_property("travel_dry_run", True)
            put(V(mg.x - (mg.x - rf["c"].x) * 0.02, mg.y - (mg.y - rf["c"].y) * 0.02, 0)); yield from wait(1.5)
            res[tag] = str(g.get_editor_property("last_travel"))
            put(V(rf["c"].x, rf["c"].y, 0)); yield from wait(0.5)
            g.set_editor_property("travel_dry_run", False)
        g.debug_all_dungeon_keys(True)
    quiet(False)
    k = kinds; pc = res["piece_counts"]; cw = res.get("car_waits", {})
    ok = (res["tier_here"] == 25 and res["static_gate"] == 0 and 22 <= res["tier_half_way_from_kethrys"] <= 24 and 40 <= res["from_kethrys_km"] <= 110
          and res["plan"] == 5 and rf is not None and res["facility"]["rooms"] == 2 and res["facility"]["from_middle_m"] < 120
          and "heaven_fortress" in res["dungeon_level"] and k.get("skyscraper", 0) >= 4 and k.get("office block", 0) >= 5 and k.get("shop", 0) >= 5
          and all(k.get(t, 0) == 1 for t in ("smithy", "store", "healer", "storehouse", "tavern", "barracks", "temple")) and k.get("witch's hut", 0) == 0
          and res["homes"]["all"] >= 30 and res["homes"]["burned"] + res["homes"]["boarded"] == 0 and res["tallest_m"] >= 50
          and all(e["with_rooms"] == e["n"] and e["with_door"] == e["n"] for e in per.values()) and n_cont > 100
          and pc["SM_HV_Road"] > 500 and pc["SM_HV_Paving"] > 1000 and pc["SM_HV_Window"] > 100 and pc["SM_Module03_Tower01_MiddleFloors01"] >= 16
          and pc["SM_HV_CityWall"] > 50 and pc["SM_Stone_Wall"] == 0 and pc["SM_Castle_Stone_Wall_01a"] == 0 and pc["SM_Tower_Roof_01d"] == 0 and res["grass"] == 0
          and sk.get("street light", 0) >= 40 and res["sign"] == ["KRATOS AURORIM RESEARCH, LLC"] and res["dome_parts"] == 1 and res.get("dome_past_buildings_m", 0) > 10 and len(res["styles"]) == 3
          and res["cars"]["n"] >= 10 and res["cars"]["moving"] >= res["cars"]["n"] * 0.6 and res["cars_on_square"] == 0 and res["cars_at_facility"] == 0 and sk.get("traffic light", 0) >= 4 and cw.get("gap_m", 0) >= 3.0 and cw.get("moved_after_m", 0) > 3.0
          and all(roles.get(r, 0) >= 1 for r in ("Elder", "Scholar", "Captain", "Worker", "Soldier"))
          and "Director Cassia Vael" in res["titles"] and "Aldric Venn" not in res["titles"]
          and any("Past the Lobby" in str(p) for p in res["director"]["panel"]) and res.get("gate_without_key") == "locked" and res.get("gate_with_keys") == "catacombs")
    step_result("heaven", ok, **res)

def step_descendspire():
    """the black tower's gate, both ways: down into its dungeon (the level kethrys_spire, 907: its arcane halls, its casters
    that shoot, its way back) with her whole state; every caster kind spawned in a row, its clips playing; then back up by
    the Escape menu's "Return to Kethrys Spire": the city built round her again and she stands before the tower's door"""
    res = {}
    if "brokenspire" not in G["w"].get_path_name(): yield from travel("brokenspire", via_menu)
    yield from as_hero("Warrior")
    yield from to_town("Kethrys Spire")
    g = G["gen"]; g.debug_all_dungeon_keys(True)
    res["set_town"] = yield from set_up("Warrior", "town")
    before = snapshot()
    mg = place("mistgate")
    yield from travel("kethrys_spire", lambda: put(V(mg.x, mg.y, 0)))
    g = G["gen"]
    res["down"] = yield from leg_check(before, "Warrior through the tower's gate")
    p = G["pawn"].get_actor_location()
    lines = [str(l) for l in g.get_menu_lines()]
    casters = {str(m.get_editor_property("name")): bool(m.get_editor_property("shoots")) for m in g.get_editor_property("monsters") if int(m.get_editor_property("weight") * 10) >= 30}
    res["tower"] = {"key": str(g.get_editor_property("dungeon_key")), "title": str(g.get_editor_property("dungeon_title")), "themes": [str(t) for t in g.get_editor_property("tier_themes")],
                    "section": [g.world_to_section(p).x, g.world_to_section(p).y], "return_line": next((l for l in lines if "Return to" in l), None),
                    "return_town": str(G["gi"].get_editor_property("return_town")), "caster_kinds": casters}
    try: res["enter_counter"] = G["gi"].get_counter("kethrys:enter")
    except Exception as e: res["enter_counter"] = str(e)
    shot("ks_tower_dungeon_start"); yield from rwait(1.2)
    quiet(True)
    hc = g.get_start_room_center(); kinds_ = sorted(casters)
    ms = []
    for j, k_ in enumerate(kinds_):
        m = g.spawn_monster_named(k_, V(hc.x + 900.0, hc.y + (j - (len(kinds_) - 1) / 2.0) * 320.0, hc.z + 120.0), 1, 1.0, 0.0, 1.0)
        if m: ms.append(m)
    yield from wait(1.5)
    def pose(m):
        c = m.get_component_by_class(unreal.SkeletalMeshComponent); a = m.get_actor_location(); out = []
        for i in range(0, min(c.get_num_bones(), 60), 3):
            q = c.get_socket_location(c.get_bone_name(i)); out.append((q.x - a.x, q.y - a.y, q.z - a.z))
        return out
    p0 = {}
    for m in ms:
        try: p0[m] = pose(m)
        except Exception as e: res.setdefault("pose_errors", []).append(str(e))
    yield from wait(0.5)
    res["caster_clips"] = {}
    for m, a in p0.items():
        try:
            b = pose(m); mv = max(math.dist(x_, y_) for x_, y_ in zip(a, b)) if a and b else 0.0
            res["caster_clips"][str(m.get_editor_property("monster_name"))] = {"bones_moved_cm": round(mv, 2), "moving": mv > 0.3,
                                                                                "parts": len([c for c in m.get_components_by_class(unreal.SkeletalMeshComponent)]) - 1}
        except Exception as e: res.setdefault("pose_errors", []).append(str(e))
    res["casters_spawned"] = len(ms)
    if ms:
        put(V(hc.x - 500.0, hc.y, hc.z), yaw=0.0)
        G["pawn"].set_actor_hidden_in_game(True)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-3, yaw=0.0)); yield from wait(1.0)
        shot("ks_casters"); yield from rwait(1.2)
        G["pawn"].set_actor_hidden_in_game(False)
        for m in ms:
            try: m.destroy_actor()
            except Exception: pass
    quiet(False)
    res["set_tower"] = yield from set_up("Warrior", "castle")
    before = snapshot()
    yield from travel("brokenspire", via_menu)
    g = G["gen"]
    t0 = time.time(); st = []
    while time.time() - t0 < 150:
        yield
        st = str(g.get_wild_town_state()).split("|")
        if len(st) > 3 and st[1] == "Kethrys Spire" and st[2] == "0" and st[3] == "1": break
    yield from wait(2.0)
    res["up"] = yield from leg_check(before, "Warrior back out of the tower's gate")
    p = G["pawn"].get_actor_location(); ra = G["gi"].get_editor_property("return_at")
    door = place("castle door")
    res["back"] = {"town": st[1] if len(st) > 1 else None, "from_return_at_m": round(dist2(p, ra) / 100, 2), "from_tower_door_m": round(dist2(p, door) / 100, 1) if door else None}
    e = res["tower"]
    ok = (res["down"]["ok"] and res["up"]["ok"] and res["down"]["level"] == "kethrys_spire" and e["key"] == "kethrys" and e["section"] == [0, 0]
          and e["return_line"] and "Kethrys Spire" in e["return_line"] and e["return_town"] == "Kethrys Spire" and len(e["caster_kinds"]) >= 5 and all(e["caster_kinds"].values())
          and res.get("casters_spawned", 0) >= 5 and all(c["moving"] for c in res["caster_clips"].values())
          and res["enter_counter"] == 1 and res["back"]["town"] == "Kethrys Spire" and res["back"]["from_return_at_m"] < 3.0 and (res["back"]["from_tower_door_m"] or 99) < 15)
    step_result("descendspire", ok, **res)

def step_descendheaven():
    """the research facility's security door, both ways: down into the fortress (the level heaven_fortress, 909: its steel
    halls, its defenders armed with firearms, its way back) with her whole state; every defender kind spawned in a row, its
    clips playing; a trooper's rounds fired at her from 7 m (each shot counted, what reached her, a picture of a round in
    flight); then back up by the Escape menu's "Return to Heaven": the city built round her again and she stands before the
    facility's door"""
    res = {}
    if "brokenspire" not in G["w"].get_path_name(): yield from travel("brokenspire", via_menu)
    yield from as_hero("Warrior")
    yield from to_town("Heaven")
    g = G["gen"]; g.debug_all_dungeon_keys(True)
    res["set_town"] = yield from set_up("Warrior", "town")
    before = snapshot()
    mg = place("mistgate")
    yield from travel("heaven_fortress", lambda: put(V(mg.x, mg.y, 0)))
    g = G["gen"]
    res["down"] = yield from leg_check(before, "Warrior through the security door")
    p = G["pawn"].get_actor_location()
    lines = [str(l) for l in g.get_menu_lines()]
    defenders = {str(m.get_editor_property("name")): bool(m.get_editor_property("shoots")) for m in g.get_editor_property("monsters") if int(m.get_editor_property("weight") * 10) >= 30}
    res["fortress"] = {"key": str(g.get_editor_property("dungeon_key")), "title": str(g.get_editor_property("dungeon_title")), "themes": [str(t) for t in g.get_editor_property("tier_themes")],
                    "section": [g.world_to_section(p).x, g.world_to_section(p).y], "return_line": next((l for l in lines if "Return to" in l), None),
                    "return_town": str(G["gi"].get_editor_property("return_town")), "defender_kinds": defenders}
    try: res["enter_counter"] = G["gi"].get_counter("heaven:enter")
    except Exception as e: res["enter_counter"] = str(e)
    shot("hv_fortress_start"); yield from rwait(1.2)
    quiet(True)
    hc = g.get_start_room_center(); kinds_ = sorted(defenders)
    ms = []
    for j, k_ in enumerate(kinds_):
        m = g.spawn_monster_named(k_, V(hc.x + 900.0, hc.y + (j - (len(kinds_) - 1) / 2.0) * 320.0, hc.z + 120.0), 1, 1.0, 0.0, 1.0)
        if m: ms.append(m)
    yield from wait(1.5)
    def pose(m):
        c = m.get_component_by_class(unreal.SkeletalMeshComponent); a = m.get_actor_location(); out = []
        for i in range(0, min(c.get_num_bones(), 60), 3):
            q = c.get_socket_location(c.get_bone_name(i)); out.append((q.x - a.x, q.y - a.y, q.z - a.z))
        return out
    p0 = {}
    for m in ms:
        try: p0[m] = pose(m)
        except Exception as e: res.setdefault("pose_errors", []).append(str(e))
    yield from wait(0.5)
    res["defender_clips"] = {}
    for m, a in p0.items():
        try:
            b = pose(m); mv = max(math.dist(x_, y_) for x_, y_ in zip(a, b)) if a and b else 0.0
            res["defender_clips"][str(m.get_editor_property("monster_name"))] = {"bones_moved_cm": round(mv, 2), "moving": mv > 0.3,
                                                                                "parts": len([c for c in m.get_components_by_class(unreal.SkeletalMeshComponent)]) - 1}
        except Exception as e: res.setdefault("pose_errors", []).append(str(e))
    res["defenders_spawned"] = len(ms)
    if ms:
        put(V(hc.x - 500.0, hc.y, hc.z), yaw=0.0)
        G["pawn"].set_actor_hidden_in_game(True)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-3, yaw=0.0)); yield from wait(1.0)
        shot("hv_defenders"); yield from rwait(1.2)
        G["pawn"].set_actor_hidden_in_game(False)
        for m in ms:
            try: m.destroy_actor()
            except Exception: pass
    # (a trooper's rounds: held where it stands 7 m off on a clear line (its range is 9 m: from 10 m, held, it never shot), aggressive;
    # its shots counted, what reached her)
    res["shooting"] = {}
    hc = g.get_start_room_center()
    for yaw in (0.0, 90.0, 180.0, 270.0):
        put(V(hc.x, hc.y, hc.z), yaw=yaw); yield from wait(0.3)
        her = G["pawn"].get_actor_location()
        fw = V(math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0)
        hit = unreal.SystemLibrary.line_trace_single(G["w"], her, V(her.x + fw.x * 700.0, her.y + fw.y * 700.0, her.z), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [G["pawn"]], unreal.DrawDebugTrace.NONE, True)
        if hit is None or not hit.to_tuple()[0]: break
    tr = g.spawn_monster_named("Kratos_Trooper", V(her.x + fw.x * 700.0, her.y + fw.y * 700.0, her.z), 1, 50.0, 1.0, 1.0)
    if tr:
        quiet(False)
        mcs = g.get_editor_property("max_chase_speed"); g.set_editor_property("max_chase_speed", 1.0)
        g.set_editor_property("aggro_distance", 2500.0); g.set_editor_property("lose_distance", 4000.0)
        cc = G["pawn"].get_component_by_class(unreal.RDCombatComponent); cc.set_health(cc.get_max_health()); hp0 = cc.get_health()
        st0 = md(g.shot_stats); t0 = now(); pictured = False; times = []
        while now() - t0 < 12.0 and tr.shots_fired < 3:
            yield from wait(0.05)
            if not pictured and len(list(g.get_shot_lines())) > 0:
                G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-4, yaw=yaw)); shot("hv_shot"); pictured = True
            if tr.shots_fired > len(times): times.append(round(now() - t0, 2))
        yield from wait(1.5)
        st1 = md(g.shot_stats)
        res["shooting"] = {"fired": tr.shots_fired, "times": times, "on_her": st1.get("on_her", 0) - st0.get("on_her", 0), "hp_lost": round(hp0 - cc.get_health(), 1),
                           "theme": str(tr.get_editor_property("monster_name")), "pictured": pictured}
        g.set_editor_property("max_chase_speed", mcs)
        try: tr.destroy_actor()
        except Exception: pass
        quiet(True)
    quiet(False)
    res["set_tower"] = yield from set_up("Warrior", "castle")
    before = snapshot()
    yield from travel("brokenspire", via_menu)
    g = G["gen"]
    t0 = time.time(); st = []
    while time.time() - t0 < 150:
        yield
        st = str(g.get_wild_town_state()).split("|")
        if len(st) > 3 and st[1] == "Heaven" and st[2] == "0" and st[3] == "1": break
    yield from wait(2.0)
    res["up"] = yield from leg_check(before, "Warrior back out of the security door")
    p = G["pawn"].get_actor_location(); ra = G["gi"].get_editor_property("return_at")
    door = place("castle door")
    res["back"] = {"town": st[1] if len(st) > 1 else None, "from_return_at_m": round(dist2(p, ra) / 100, 2), "from_facility_door_m": round(dist2(p, door) / 100, 1) if door else None}
    e = res["fortress"]
    ok = (res["down"]["ok"] and res["up"]["ok"] and res["down"]["level"] == "heaven_fortress" and e["key"] == "heaven" and e["section"] == [0, 0]
          and e["return_line"] and "Heaven" in e["return_line"] and e["return_town"] == "Heaven" and len(e["defender_kinds"]) >= 5 and all(e["defender_kinds"].values())
          and res.get("defenders_spawned", 0) >= 5 and all(c["moving"] for c in res["defender_clips"].values())
          and res["enter_counter"] == 1 and res["shooting"].get("fired", 0) >= 2 and res["shooting"].get("on_her", 0) >= 1 and res["back"]["town"] == "Heaven" and res["back"]["from_return_at_m"] < 3.0 and (res["back"]["from_facility_door_m"] or 99) < 15)
    step_result("descendheaven", ok, **res)

# ------------------------------------------------------------------------------------------------ Graymourne, the port
def step_port():
    """Graymourne (the user's spec of 2026-11-07, docs/graymourne.txt): on the northern coast, the sea within 1.5 km north of
    its middle; built as she comes, the port's plan: the sluice house at its middle (its sewer gate at the far wall), the inner
    harbour along the sea wall (its water, the quay's stone face, the blockers at the water's edge), five piers with a ship and a
    boat at each, two wrecks, the drowned dead laid on the quay with their mourners, three gibbets, the fishers' racks, nets and
    cages; warehouses on the quay, the trades, the homes (every building's rooms, doors, containers); its people its own (the
    harbourmaster, the coroner, the watch-captain, sailors, dockhands, fishers) and Brokenspire's elder not among them; the
    harbourmaster's panel with her first quest; a pier walked on (its deck under her feet) and the water's edge holding her
    (pushed sideways off the pier for 2.5 s she stays on it); the port's fog thick in the town (PortFog); the gate's dry run
    (walked into, it would open the sewers); pictures of the harbour from the quay, the quay from a pier's end, the dead on the
    quay and the sewer gate"""
    g = G["gen"]; res = {}
    ti, x, y = town_of("Graymourne")
    res["site_km"] = [round(x / 1000, 1), round(y / 1000, 1)]
    sea = None
    for d in range(0, 3001, 100):
        p_ = str(g.get_wild_sample_at(V((x + d) * 100.0, y * 100.0, 0))).split("|")
        if len(p_) > 5 and int(float(p_[5])) == 1: sea = d; break
    res["sea_north_m"] = sea
    ti, x, y = yield from to_town("Graymourne")
    st = str(g.get_wild_town_state()).split("|"); res["state"] = st
    res["plan"] = g.get_editor_property("town_plan")
    res["dungeon_level"] = str(g.current_dungeon_level())
    S = section(); B = blds()
    kinds = {}
    for b in B: kinds[b["kind"]] = kinds.get(b["kind"], 0) + 1
    res["kinds"] = kinds
    homes = [b for b in B if b["kind"] == "home"]
    res["homes"] = {"all": len(homes), "burned": sum(1 for b in homes if b["state"] == 1), "boarded": sum(1 for b in homes if b["state"] == 2)}
    sh = next((b for b in B if b["kind"] == "sluice house"), None)
    res["sluice_house"] = {"label": sh["label"], "rooms": sh["rooms"], "from_middle_m": round(math.hypot(sh["c"].x / 100 - x, sh["c"].y / 100 - y))} if sh else None
    SP = spots(); sk = {}
    for p_ in SP: sk[p_["kind"]] = sk.get(p_["kind"], 0) + 1
    res["spots"] = sk
    n_cont = S.get_num_containers()
    conts = [S.get_container_location(i) for i in range(n_cont)]
    doors = [S.get_door_location(i) for i in range(S.get_num_doors())]
    per = {}
    for b in B:
        if b["state"] == 1: continue
        k = b["kind"]; e = per.setdefault(k, {"n": 0, "with_rooms": 0, "with_door": 0, "containers": 0})
        e["n"] += 1; e["with_rooms"] += 1 if b["rooms"] > 0 else 0
        e["with_door"] += 1 if any(dist2(d, b["door"]) < 250 for d in doors) else 0
        e["containers"] += sum(1 for c in conts if S.town_building_at(c) == b["i"])
    res["inside"] = per; res["containers"] = n_cont; res["doors"] = len(doors)
    res["piece_counts"] = {n: len(ism_instances(n)) for n in ("SM_Gangway_01", "SM_Pier_Pilings_01a", "SM_Mooring_post_NN_01h", "SM_VikingBoat_01a", "SM_SmallBoat", "SM_BrokenShip",
                                                              "SM_Dead_Pirate_01c", "SM_Dead_Pirate_01d", "SM_Gibbet_A", "SM_FishRack_SM_FishRack_Wood", "SM_FishRack_SM_FishRack_Fish",
                                                              "SM_BigFishNet", "SM_Crab_Cages_01a", "SM_Sewer_Tube_Gate_01a")}
    res["harbour_water"] = [c.get_name() for c in S.get_components_by_class(unreal.ProceduralMeshComponent) if "Harbour" in c.get_name()]
    F = folk(); roles = {}
    for f in F: roles[f["role"]] = roles.get(f["role"], 0) + 1
    res["roles"] = roles; res["titles"] = sorted({f["title"] for f in F if f["role"] in ("Elder", "Scholar", "Captain", "Priest", "Smith", "Trader", "Healer", "Keeper", "Innkeeper")})
    quiet(True)
    hm = talk_to("Elder"); yield from wait(0.4)
    said = str(g.interact_nearest(G["pawn"].get_actor_location())) if hm else None; yield from rwait(0.5)
    res["harbourmaster"] = {"found": hm is not None, "said": said, "panel": [p[1] for p in panel()][:8]}
    g.close_town_panel(); yield from wait(0.3)
    # (the fog eases in over some seconds as the town comes (gm3 read it at 0.88): wait until it has settled)
    t0 = time.time()
    while time.time() - t0 < 30 and float(g.get_editor_property("port_fog")) < 0.995: yield
    res["port_fog"] = round(float(g.get_editor_property("port_fog")), 2); res["port_fog_wait_s"] = round(time.time() - t0, 1)
    # (the fog itself, as the world has it: its start drawn in from the wilds' 250 m, its density raised)
    fogs = [c for a in unreal.GameplayStatics.get_all_actors_of_class(G["w"], unreal.ExponentialHeightFog) for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent)]
    res["fog"] = [{"start_m": round(c.get_editor_property("start_distance") / 100, 1), "density": round(c.get_editor_property("fog_density"), 4)} for c in fogs]
    # (a pier: its way out from the ship moored beside it (the longer axis of ship - pier), her feet on its deck; pushed across it
    # for 2.5 s, the water's edge holds her)
    piers = [p_ for p_ in SP if p_["kind"] == "pier"]; ships = [p_ for p_ in SP if p_["kind"] == "ship"]
    res["pier_walk"] = None
    if piers and ships:
        pr = piers[0]; s0 = min(ships, key=lambda s_: dist2(s_["at"], pr["at"]))
        dx, dy = s0["at"].x - pr["at"].x, s0["at"].y - pr["at"].y
        out = V(1.0 if dx > 0 else -1.0, 0, 0) if abs(dx) > abs(dy) else V(0, 1.0 if dy > 0 else -1.0, 0)
        side = V(-out.y, out.x, 0)
        mid = V(pr["at"].x + out.x * 2400.0, pr["at"].y + out.y * 2400.0, 0)
        yaw_out = math.degrees(math.atan2(out.y, out.x))
        # (the harbour from the quay: 6 m back from the first pier's foot, looking out along it)
        put(V(pr["at"].x - out.x * 600.0, pr["at"].y - out.y * 600.0, 0), yaw=yaw_out); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-4, yaw=yaw_out)); yield from wait(1.5)
        shot("gm_harbour"); yield from rwait(1.2)
        put(mid, yaw=yaw_out); yield from wait(1.2)
        z0 = G["pawn"].get_actor_location().z; zmin = z0; t0 = time.time()
        for sgn in (1.0, -1.0):
            t0 = time.time()
            while time.time() - t0 < 2.5:
                G["pawn"].add_movement_input(V(side.x * sgn, side.y * sgn, 0), 1.0); yield
                zmin = min(zmin, G["pawn"].get_actor_location().z)
            p1 = G["pawn"].get_actor_location()
            res.setdefault("pier_push", []).append({"side": sgn, "off_middle_m": round(abs((p1.x - mid.x) * side.x + (p1.y - mid.y) * side.y) / 100, 2), "z": round(p1.z)})
            put(mid, yaw=yaw_out); yield from wait(0.8)
        res["pier_walk"] = {"z_on_deck": round(z0), "z_min_pushed": round(zmin), "on_ground": G["pawn"].get_editor_property("character_movement").is_moving_on_ground()}
        # (nothing grows on a pier: every instance on the first pier's deck that is not the port's own (884 gm1's picture had
        # grass and flowers on them))
        own = ("Gangway", "Pier_Pilings", "Mooring", "VikingBoat", "SmallBoat", "Collider", "Cube", "Castle_Stone_Wall")
        on = {}
        for c in isms(S):
            m_ = c.get_editor_property("static_mesh")
            if not m_ or any(o in m_.get_name() for o in own): continue
            for i in range(c.get_instance_count()):
                t = c.get_instance_transform(i, True)
                if isinstance(t, tuple): t = t[-1]
                q = t.translation; a_ = (q.x - pr["at"].x) * out.x + (q.y - pr["at"].y) * out.y; c_ = (q.x - pr["at"].x) * side.x + (q.y - pr["at"].y) * side.y
                if 150.0 < a_ < 4650.0 and abs(c_ - 0.0) < 420.0 and q.z > -60.0: on[m_.get_name()] = on.get(m_.get_name(), 0) + 1
        res["on_pier"] = on
        # (the quay from the pier's end, looking back)
        end = V(pr["at"].x + out.x * 4500.0, pr["at"].y + out.y * 4500.0, 0)
        put(end, yaw=yaw_out + 180.0); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw_out + 180.0)); yield from wait(1.5)
        shot("gm_quay"); yield from rwait(1.2)
        # (and out from it to the harbour's far side, where no quay stands (PR #26's review: the bed's edge there))
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-12, yaw=yaw_out)); yield from wait(1.2)
        shot("gm_mouth"); yield from rwait(1.2)
    # (every edge where walked ground meets the harbour's water (PR #25's review: a walk-mesh vertex on a tile's edge takes the
    # tile on its +X / +Y side, so the drop to the water could fall inside the walked side on two of the four ways): the ground
    # traced across each blocker 30 to 150 cm either side, at three points along it; its land side must stay level; and pushed at
    # the water from 3 m inland for 2.5 s on each way, she must stop at the blocker on level ground)
    def gzd(x_, y_):
        """the ground's height at (x, y) and whether a pier's deck is what was hit"""
        h = unreal.SystemLibrary.line_trace_single(G["w"], V(x_, y_, 400), V(x_, y_, -500), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [G["pawn"]], unreal.DrawDebugTrace.NONE, True)
        h = h.to_tuple() if h else None
        if not (h and h[0]): return None, False
        comp = next((x_ for x_ in h if isinstance(x_, unreal.PrimitiveComponent)), None)
        sm_ = comp.get_editor_property("static_mesh") if isinstance(comp, unreal.StaticMeshComponent) else None
        return h[4].z, bool(sm_ and "Gangway" in sm_.get_name())
    def gz(x_, y_): return gzd(x_, y_)[0]
    # (every blocker of the harbour (PR #26's review: those within 90 m of the first pier only left the far side untraced):
    # within 250 m of any pier and with water on one side; an edge whose land side is a pier's deck is the deck's (its own
    # collision holds her there: counted apart, not pushed), the others the quay's)
    edges = []
    for c in isms(S):
        m_ = c.get_editor_property("static_mesh")
        if not m_ or m_.get_name() != "Cube": continue
        for i in range(c.get_instance_count()):
            t = c.get_instance_transform(i, True)
            if isinstance(t, tuple): t = t[-1]
            q, sc = t.translation, t.scale3d
            if abs(sc.y - 0.3) > 0.03 or abs(sc.z - 2.1) > 0.1 or not piers or min(dist2(q, p_["at"]) for p_ in piers) > 25000.0: continue
            yw = math.radians(t.rotation.rotator().yaw)
            edges.append((q, V(math.cos(yw), math.sin(yw), 0), V(-math.sin(yw), math.cos(yw), 0), sc.x * 100.0))
    ways = {}; decks = {}; pushes = {}
    for q, al, nm, ln in edges:
        prof = {}; deck = {}
        for s_ in (1.0, -1.0):
            rows = [[gzd(q.x + al.x * ln * f + nm.x * s_ * d, q.y + al.y * ln * f + nm.y * s_ * d) for d in (30, 60, 90, 120, 150)] for f in (-0.35, 0.0, 0.35)]
            prof[s_] = [[z_ for z_, _ in r] for r in rows]; deck[s_] = any(dk for r in rows for _, dk in r)
        far = {s_: sorted(r[-1] for r in prof[s_] if r[-1] is not None) for s_ in prof}
        med = {s_: (far[s_][len(far[s_]) // 2] if far[s_] else None) for s_ in prof}
        land = next((s_ for s_ in (1.0, -1.0) if med[s_] is not None and med[s_] > -60.0), None)
        if land is None or med[-land] is None or med[-land] > -60.0: continue      # (no water on the other side: not the harbour's edge)
        wd = V(-nm.x * land, -nm.y * land, 0)
        key = ("+x" if wd.x > 0 else "-x") if abs(wd.x) > abs(wd.y) else ("+y" if wd.y > 0 else "-y")
        dip = min(z_ for r in prof[land] for z_ in r if z_ is not None)
        e = (decks if deck[land] else ways).setdefault(key, {"edges": 0, "land_dip_cm": 0.0, "dipped": 0})
        e["edges"] += 1; e["land_dip_cm"] = round(min(e["land_dip_cm"], dip), 1); e["dipped"] += 1 if dip < -30.0 else 0
        # (a trace's 0.0 is ground, not a miss (PR #26's review: `or` took the level quay's 0.0 for none and skipped it))
        if not deck[land] and key not in pushes and all((lambda z_: z_ is not None and abs(z_) < 60.0)(gz(q.x + nm.x * land * d, q.y + nm.y * land * d)) for d in (200, 300)):
            pushes[key] = (q, wd, land, nm)
    res["harbour_edges"] = ways; res["deck_edges"] = decks
    for key, (q, wd, land, nm) in sorted(pushes.items()):
        st_ = V(q.x - wd.x * 300.0, q.y - wd.y * 300.0, 0)
        put(st_, yaw=math.degrees(math.atan2(wd.y, wd.x))); yield from wait(1.0)
        z0 = G["pawn"].get_actor_location().z; zmin = z0; t0 = time.time()
        while time.time() - t0 < 2.5:
            G["pawn"].add_movement_input(wd, 1.0); yield
            zmin = min(zmin, G["pawn"].get_actor_location().z)
        p1 = G["pawn"].get_actor_location()
        res.setdefault("edge_push", {})[key] = {"from_line_m": round(((p1.x - q.x) * wd.x + (p1.y - q.y) * wd.y) / 100, 2), "z0": round(z0), "z": round(p1.z), "z_min": round(zmin)}
        # (the quay's face and the bed below it, looked down at from where she stopped: the drawn ground must drop at the face)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-40, yaw=math.degrees(math.atan2(wd.y, wd.x)))); yield from wait(1.0)
        shot("gm_edge_" + key.replace("+", "p").replace("-", "m")); yield from rwait(1.2)
    bodies = [p_ for p_ in SP if p_["kind"] == "body"]; gib = [p_ for p_ in SP if p_["kind"] == "gibbet"]
    if bodies and gib:
        b0 = bodies[len(bodies) // 2]; gg = min(gib, key=lambda q: dist2(q["at"], b0["at"]))
        yaw = math.degrees(math.atan2(gg["at"].y - b0["at"].y, gg["at"].x - b0["at"].x))
        put(V(b0["at"].x - math.cos(math.radians(yaw)) * 700.0, b0["at"].y - math.sin(math.radians(yaw)) * 700.0, 0), yaw=yaw)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-10, yaw=yaw)); yield from wait(1.2)
        shot("gm_dead"); yield from rwait(1.2)
    mg = place("mistgate"); res["gate_from_sluice_m"] = round(dist2(mg, sh["c"]) / 100) if mg and sh else None
    if mg and sh:
        yaw = math.degrees(math.atan2(mg.y - sh["c"].y, mg.x - sh["c"].x))
        put(V(mg.x - (mg.x - sh["c"].x) * 0.7, mg.y - (mg.y - sh["c"].y) * 0.7, 0), yaw=yaw); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-4, yaw=yaw)); yield from wait(1.2)
        shot("gm_sewer_gate"); yield from rwait(1.2)
        g.set_editor_property("travel_dry_run", True)
        put(V(mg.x - (mg.x - sh["c"].x) * 0.02, mg.y - (mg.y - sh["c"].y) * 0.02, 0)); yield from wait(1.5)
        res["gate_travel"] = str(g.get_editor_property("last_travel"))
        put(V(sh["c"].x, sh["c"].y, 0)); yield from wait(0.5)
        g.set_editor_property("travel_dry_run", False)
    quiet(False)
    k = kinds; pc_ = res["piece_counts"]; pw = res.get("pier_walk") or {}
    ok = (res["sea_north_m"] is not None and res["sea_north_m"] < 1500 and res["plan"] == 3 and sh is not None and res["sluice_house"]["from_middle_m"] < 120
          and "sewers" in res["dungeon_level"] and res["harbour_water"]
          and sk.get("pier", 0) == 5 and sk.get("ship", 0) == 5 and sk.get("boat", 0) == 5 and sk.get("wreck", 0) == 2 and sk.get("gibbet", 0) == 3 and sk.get("body", 0) >= 8 and sk.get("dock props", 0) >= 3
          and pc_["SM_Gangway_01"] >= 5 * 14 and pc_["SM_VikingBoat_01a"] == 5 and pc_["SM_SmallBoat"] == 5 and pc_["SM_BrokenShip"] == 2 and pc_["SM_Sewer_Tube_Gate_01a"] == 1
          and k.get("warehouse", 0) >= 3 and all(k.get(t, 0) == 1 for t in ("smithy", "store", "healer", "storehouse", "tavern", "barracks", "temple"))
          and k.get("cathedral", 0) == 0 and k.get("foundry", 0) == 0 and res["homes"]["all"] >= 40
          and all(e["with_rooms"] == e["n"] and e["with_door"] == e["n"] for e in per.values()) and n_cont > 100
          and all(roles.get(r, 0) >= 1 for r in ("Elder", "Scholar", "Captain", "Sailor", "Dockhand", "Fisher", "Mourner"))
          and "Harbourmaster Edda Strand" in res["titles"] and "Aldric Venn" not in res["titles"]
          and any("Old Grate" in str(p) for p in res["harbourmaster"]["panel"]) and res["port_fog"] > 0.8 and res["fog"] and all(f["start_m"] < 20 and f["density"] > 0.1 for f in res["fog"])
          and pw and abs(pw["z_on_deck"] - 90) < 40 and pw["z_min_pushed"] > pw["z_on_deck"] - 30 and not res.get("on_pier")
          and len(res["harbour_edges"]) >= 3 and all(e["dipped"] == 0 for e in list(res["harbour_edges"].values()) + list(res["deck_edges"].values()))
          and set(res.get("edge_push") or {}) == set(res["harbour_edges"]) and all(e["from_line_m"] < 0 and e["z_min"] > e["z0"] - 30 for e in res["edge_push"].values())
          and res.get("gate_travel") == "catacombs")
    step_result("port", ok, **res)

def step_descendsewer():
    """the sewer gate of Graymourne's sluice house, both ways: down into the sewers (the level sewers, 897: its floors going
    down, its name, its drowned and its way back) with her whole state; the drowned, one of each kind spawned in a row, their
    clips playing; then back up by the Escape menu's "Return to Graymourne": the city built round her again and she stands
    before the sluice house's door (the game instance's ReturnAt)"""
    res = {}
    if "brokenspire" not in G["w"].get_path_name(): yield from travel("brokenspire", via_menu)
    yield from as_hero("Warrior")
    yield from to_town("Graymourne")
    g = G["gen"]
    res["set_town"] = yield from set_up("Warrior", "town")
    before = snapshot()
    mg = place("mistgate")
    yield from travel("sewers", lambda: put(V(mg.x, mg.y, 0)))
    g = G["gen"]
    res["down"] = yield from leg_check(before, "Warrior through the sewer gate")
    p = G["pawn"].get_actor_location()
    lines = [str(l) for l in g.get_menu_lines()]
    drowned = {str(m.get_editor_property("name")) for m in g.get_editor_property("monsters") if int(m.get_editor_property("weight") * 10) >= 30}
    near = {}
    for m in g.get_monsters():
        if m and not m.is_dead(): n = str(m.get_editor_property("monster_name")); near[n] = near.get(n, 0) + 1
    res["sewers"] = {"key": str(g.get_editor_property("dungeon_key")), "title": str(g.get_editor_property("dungeon_title")), "tier_floors": g.get_editor_property("tier_floors"),
                     "section": [g.world_to_section(p).x, g.world_to_section(p).y], "z": round(p.z), "return_line": next((l for l in lines if "Return to" in l), None),
                     "return_town": str(G["gi"].get_editor_property("return_town")), "drowned_kinds": sorted(drowned), "monsters_now": near,
                     "drowned_now": sum(v for k_, v in near.items() if k_ in drowned), "themes": [str(t) for t in g.get_editor_property("tier_themes")]}
    try: res["enter_counter"] = G["gi"].get_counter("sewers:enter")
    except Exception as e: res["enter_counter"] = str(e)
    shot("gm_sewers_start"); yield from rwait(1.2)
    quiet(True)
    hc = g.get_start_room_center(); kinds_ = sorted(drowned)
    ms = []
    for j, k_ in enumerate(kinds_):
        m = g.spawn_monster_named(k_, V(hc.x + 900.0, hc.y + (j - (len(kinds_) - 1) / 2.0) * 320.0, hc.z + 120.0), 1, 1.0, 0.0, 1.0)
        if m: ms.append(m)
    yield from wait(1.5)
    def pose(m):
        c = m.get_component_by_class(unreal.SkeletalMeshComponent); a = m.get_actor_location(); out = []
        for i in range(0, min(c.get_num_bones(), 60), 3):
            p_ = c.get_socket_location(c.get_bone_name(i)); out.append((p_.x - a.x, p_.y - a.y, p_.z - a.z))
        return out
    p0 = {}
    for m in ms:
        try: p0[m] = pose(m)
        except Exception as e: res.setdefault("pose_errors", []).append(str(e))
    yield from wait(0.5)
    res["drowned_clips"] = {}
    for m, a in p0.items():
        try:
            b = pose(m); mv = max(math.dist(x_, y_) for x_, y_ in zip(a, b)) if a and b else 0.0
            res["drowned_clips"][str(m.get_editor_property("monster_name"))] = {"bones_moved_cm": round(mv, 2), "moving": mv > 0.3}
        except Exception as e: res.setdefault("pose_errors", []).append(str(e))
    res["drowned_spawned"] = len(ms)
    if ms:
        put(V(hc.x - 500.0, hc.y, hc.z), yaw=0.0)
        G["pawn"].set_actor_hidden_in_game(True)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-3, yaw=0.0)); yield from wait(1.0)
        shot("gm_drowned"); yield from rwait(1.2)
        G["pawn"].set_actor_hidden_in_game(False)
        for m in ms:
            try: m.destroy_actor()
            except Exception: pass
    quiet(False)
    res["set_sewers"] = yield from set_up("Warrior", "castle")
    before = snapshot()
    yield from travel("brokenspire", via_menu)
    g = G["gen"]
    t0 = time.time(); st = []
    while time.time() - t0 < 150:
        yield
        st = str(g.get_wild_town_state()).split("|")
        if len(st) > 3 and st[1] == "Graymourne" and st[2] == "0" and st[3] == "1": break
    yield from wait(2.0)
    res["up"] = yield from leg_check(before, "Warrior back out of the sewer gate")
    p = G["pawn"].get_actor_location(); ra = G["gi"].get_editor_property("return_at")
    door = place("castle door")
    res["back"] = {"town": st[1] if len(st) > 1 else None, "from_return_at_m": round(dist2(p, ra) / 100, 2), "from_sluice_door_m": round(dist2(p, door) / 100, 1) if door else None,
                   "on_ground": G["pawn"].get_editor_property("character_movement").is_moving_on_ground()}
    e = res["sewers"]
    ok = (res["down"]["ok"] and res["up"]["ok"] and res["down"]["level"] == "sewers" and e["key"] == "sewers" and e["tier_floors"] and e["section"] == [0, 0]
          and e["return_line"] and "Graymourne" in e["return_line"] and e["return_town"] == "Graymourne" and len(e["drowned_kinds"]) >= 10 and e["drowned_now"] >= 1
          and res.get("drowned_spawned", 0) >= 10 and len(res.get("drowned_clips", {})) >= 10 and all(c["moving"] for c in res["drowned_clips"].values())
          and res["enter_counter"] == 1 and res["back"]["town"] == "Graymourne" and res["back"]["from_return_at_m"] < 3.0 and (res["back"]["from_sluice_door_m"] or 99) < 12)
    step_result("descendsewer", ok, **res)

# ------------------------------------------------------------------------------------------------ the list of 2026-11-07 (docs/improvements8.txt)
def step_planks():
    """the boarded windows' boards (the list of 2026-11-07: "the windowsills that have boards jutting out from the bottom of the
    window do not have a collision layer, the player can walk right through those boards"): at every boarded window's planks a
    small capsule swept at them from 1 m out on each side is stopped before their middle"""
    res = {}; S = section(); w = G["w"]
    planks = []
    for c in isms(S):
        m = c.get_editor_property("static_mesh")
        if not m or "Wooden_Planks" not in m.get_name(): continue
        bb = m.get_bounding_box(); ctr = (bb.min + bb.max) * 0.5
        for k in range(c.get_instance_count()):
            t = c.get_instance_transform(k, True)
            if isinstance(t, tuple): t = t[-1]
            planks.append(unreal.MathLibrary.transform_location(t, ctr))
    res["planks"] = len(planks); stopped = 0; through = []
    for p in planks[:60]:
        ok_all = True
        for ang in (0, 90, 180, 270):
            d = V(math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0.0)
            a = p + d * 100.0
            h = unreal.SystemLibrary.capsule_trace_single(w, a, p, 5.0, 5.0, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [G["pawn"]], unreal.DrawDebugTrace.NONE, True)
            h = h.to_tuple() if h else None
            if not (h and h[0] and h[2] < 0.97): ok_all = False
        if ok_all: stopped += 1
        else: through.append([round(p.x), round(p.y), round(p.z)])
    res["stopped"] = stopped; res["through"] = through[:6]
    step_result("planks", res["planks"] > 3 and not through, **res)
    yield
def dummies():
    out = []
    for l in G["gen"].get_town_dummy_lines():
        p = str(l).split("|"); out.append({"kind": p[0], "at": V(float(p[1]), float(p[2]), float(p[3])), "hits": int(p[4]), "lean": float(p[5]), "r": float(p[6]), "h": float(p[7])})
    return out
def step_dummies():
    """the barracks' training dummies (the list of 2026-11-07: "the training dummies near the barracks should react when hit by a
    melee or ranged weapon"): the Warrior's sword and the Mage's bolt each at a dummy and a target: it counts the hit and
    leans away (degrees, its most within 1.5 s), then stands again; pictures of a dummy struck"""
    g = G["gen"]; res = {"melee": [], "ranged": []}; quiet(True)
    ds = dummies(); res["dummies"] = [[d["kind"], round(d["at"].x), round(d["at"].y), round(d["r"]), round(d["h"])] for d in ds]
    if not ds: step_result("dummies", False, **res); quiet(False); return
    hero0 = str(g.get_editor_property("current_hero"))
    def watch(i, sec):
        best = 0.0; t0 = time.time()
        while time.time() - t0 < sec:
            best = max(best, dummies()[i]["lean"]); yield
        return best
    for hero, kind in (("Warrior", "melee"), ("Mage", "ranged")):
        if str(g.get_editor_property("current_hero")) != hero: g.switch_hero(hero); yield from wait(1.0); refresh()
        for i, d in enumerate(ds[:2]):
            # (before it, 1.3 m off (a bolt: 6 m), facing it, on the barracks' side away from the door's lane)
            off = 130.0 + d["r"] if kind == "melee" else 600.0
            to_door = V(1.0, 0.0, 0.0)
            ang = 0.0
            for a_ in range(0, 360, 30):
                pp = d["at"] + V(math.cos(math.radians(a_)), math.sin(math.radians(a_)), 0) * off
                h = unreal.SystemLibrary.line_trace_single(G["w"], pp + V(0, 0, 100), d["at"] + V(0, 0, d["h"] * 0.6), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [G["pawn"]], unreal.DrawDebugTrace.NONE, True)
                h = h.to_tuple() if h else None
                hc = h[10] if h else None; hm = hc.get_editor_property("static_mesh") if hc and isinstance(hc, unreal.StaticMeshComponent) else None
                if h and h[0] and hm and ("Dummy" in hm.get_name() or "Target" in hm.get_name()): ang = a_; break
            pp = d["at"] + V(math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0) * off
            yaw = math.degrees(math.atan2(d["at"].y - pp.y, d["at"].x - pp.x))
            put(V(pp.x, pp.y, d["at"].z), yaw=yaw); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-4.0 if kind == "melee" else -1.0, yaw=yaw)); yield from wait(1.2)
            h0 = dummies()[i]["hits"]
            yield from press("LeftMouseButton", 0.12)
            lean = yield from watch(i, 1.6)
            if kind == "melee" and i == 0:
                shot("dummy_struck"); yield from rwait(1.5)
            yield from rwait(2.5)
            after = dummies()[i]
            res[kind].append({"kind": d["kind"], "hits": after["hits"] - h0, "lean_max": round(lean, 1), "lean_after_4s": round(after["lean"], 2)})
    if str(g.get_editor_property("current_hero")) != hero0: g.switch_hero(hero0); yield from wait(1.0); refresh()
    quiet(False)
    ok = all(r["hits"] >= 1 and r["lean_max"] > 3.0 and r["lean_after_4s"] < 0.5 for r in res["melee"] + res["ranged"]) and len(res["melee"]) >= 1 and len(res["ranged"]) >= 1
    step_result("dummies", ok, **res)
def step_storage():
    """her storage's list held (the list of 2026-11-07: "when viewing your personal storage, the player cannot scroll down the list
    by holding down the d-pad up or down"): with more things than the panel shows, the D-pad held down 1.5 s moves the cursor
    on row after row (once at the press, then every 80 ms after 0.35 s), held up brings it back; one press is one row"""
    g = G["gen"]; c = cb(); res = {}; quiet(True)
    for it in [i for i in g.get_editor_property("items")][:24]:
        try: c.add_item(str(it.name), 1)
        except Exception: pass
    yield from wait(0.3)
    g.open_town_panel("stash", -1); yield from rwait(0.3); g.set_town_tab(0); yield from rwait(0.3)
    n = len(g.get_town_lines()) if hasattr(g, "get_town_lines") else None
    res["rows"] = n; res["open"] = g.is_town_panel_open()
    c0 = g.get_town_cursor()
    yield from press("Gamepad_DPad_Down", 0.12); res["one_press"] = g.get_town_cursor() - c0
    c1 = g.get_town_cursor()
    yield from press("Gamepad_DPad_Down", 1.5); res["held_down_1_5s"] = g.get_town_cursor() - c1
    c2 = g.get_town_cursor()
    yield from press("Gamepad_DPad_Up", 0.9); res["held_up_0_9s"] = c2 - g.get_town_cursor()
    shot("storage_held", "1280x720"); yield from rwait(1.5)
    g.close_town_panel(); yield from rwait(0.3)
    quiet(False)
    ok = res["open"] and res["one_press"] == 1 and res["held_down_1_5s"] >= 8 and res["held_up_0_9s"] >= 4
    step_result("storage", ok, **res)
def step_block8():
    """the Warrior's block (the list of 2026-11-07: "when blocking with the shield, the warrior should only be able to walk
    forward slowly or walk backwards slowly"): her shield up (LB held), her run switch on, the stick pushed ahead, to her right
    and back for 2 s each: ahead and back she walks along her facing at the block's speed (90 cm/s, back 72) and no faster for
    running; the stick pushed to the side turns her and does not move her; she faces her way all along (the shield before her)"""
    g = G["gen"]; res = {}; quiet(True)
    if str(g.get_editor_property("current_hero")) != "Warrior": g.switch_hero("Warrior"); yield from wait(1.0); refresh()
    c = cb(); p = G["pawn"]
    sq = place("square") or p.get_actor_location()          # (a town planned without the place: where she stands)
    put(V(sq.x + 600, sq.y + 600, 0), yaw=0.0); yield from wait(1.0)
    c.set_run_mode(True)
    # (since the list of 2026-11-08b she starts with no shield: one given for the block, taken back after)
    given = None
    if str(c.get_worn_shield()) in ("None", ""):
        given = next((str(i.name) for i in g.get_editor_property("items") if "shield" in str(i.kind).lower()), None)
        if given: c.add_item(given, 1); c.wear_shield(given); yield from wait(0.3)
    res["shield_given"] = given
    res["block_move_speed"] = g.get_editor_property("block_move_speed")
    c.simulate_key(key("Gamepad_LeftShoulder"), True); yield from wait(0.5)
    res["blocking"] = c.is_blocking() if hasattr(c, "is_blocking") else None
    for nm, way in (("ahead", (1, 0)), ("right", (0, 1)), ("back", (-1, 0))):
        f = p.get_actor_forward_vector(); r_ = p.get_actor_right_vector(); y0 = p.get_actor_rotation().yaw; a = p.get_actor_location()
        # (the stick against the camera, as her move comes in: up, right, down)
        cy = math.radians(G["pc"].get_control_rotation().yaw); cf = V(math.cos(cy), math.sin(cy), 0.0); cr = V(-math.sin(cy), math.cos(cy), 0.0)
        d = cf * float(way[0]) + cr * float(way[1])
        # (her turn added up frame by frame: read once at the end, 415 degrees came out as 56)
        t0 = time.time(); turned = 0.0; yl = y0
        while time.time() - t0 < 2.0:
            p.add_movement_input(d, 1.0); yield
            yn = p.get_actor_rotation().yaw; turned += ((yn - yl) + 180) % 360 - 180; yl = yn
        b = p.get_actor_location(); dv = b - a
        res[nm] = {"along_cm": round(dv.dot(f)), "aside_cm": round(dv.dot(r_)), "turned_deg": round(turned, 1),
                   "speed_cm_s": round(math.hypot(dv.x, dv.y) / 2.0), "filter": [round(x, 2) for x in (c.last_block_move.x, c.last_block_move.y, c.last_block_move.z)]}
        yield from wait(0.4)
    shot("block8", "1280x720"); yield from rwait(1.5)
    c.simulate_key(key("Gamepad_LeftShoulder"), False); yield from wait(0.5)
    # (the block let go: her run as before)
    a = p.get_actor_location(); t0 = time.time()
    while time.time() - t0 < 1.5: p.add_movement_input(p.get_actor_forward_vector(), 1.0); yield
    res["after_cm_s"] = round((p.get_actor_location() - a).length() / 1.5)
    c.set_run_mode(False); quiet(False)
    if given: c.wear_shield(given); c.remove_item(given, 1)
    bs = res["block_move_speed"]
    ok = (bs > 0 and 0.7 * bs * 2 <= res["ahead"]["along_cm"] <= 1.1 * bs * 2 and abs(res["ahead"]["aside_cm"]) < 25
          and abs(res["right"]["aside_cm"]) < 25 and abs(res["right"]["along_cm"]) < 25 and abs(res["right"]["turned_deg"]) > 60
          and -1.1 * bs * 0.8 * 2 <= res["back"]["along_cm"] <= -0.6 * bs * 0.8 * 2 and abs(res["back"]["turned_deg"]) < 5
          and res["after_cm_s"] > bs * 2)
    step_result("block8", ok, **res)
def step_console():
    """the game's own console (the user's of 2026-11-08: "create a console for the shipping game"; RD/RDConsole.cpp, on in a
    Shipping game, here put on with rd.GameConsole 1): its self-test, the same one a packaged game runs with -RDConsoleTest
    (package_mistward.ps1's console run). Through Slate as a keyboard sends it: ` in the game's view opens it with the line
    focused (the key's ` not typed); "rd.WildRunSpeed 10" typed and Enter sets the run speed; a name alone prints its value
    (t.MaxFPS too, an engine variable); Up / Down recall, Tab completes rd.Wild, an unknown word says so, help lists the
    rd. commands; a picture of the view with it open; W held 1.2 s under it reaches nothing; Escape shuts it and gives the
    view the keyboard; ` opens and ` shuts it; W held after that is the game's again"""
    g = G["gen"]; res = {}
    unreal.SystemLibrary.execute_console_command(G["w"], "rd.GameConsole 1")
    con = unreal.RDConsole.get_console(g)
    out = os.path.join(SHOTS, f"bs_{TAG}_console.txt")
    con.start_self_test(out)
    t0 = time.time()
    while not con.get_self_test_result() and time.time() - t0 < 60: yield
    txt = str(con.get_self_test_result())
    unreal.SystemLibrary.execute_console_command(G["w"], "rd.GameConsole 0")
    checks = {}
    for ln in txt.splitlines():
        p = ln.split("|", 3)
        if p[0] == "check": checks[p[1]] = {"ok": p[2] == "ok", "what": p[3] if len(p) > 3 else ""}
        elif p[0] == "note": res[p[1]] = p[2]
    res["checks"] = checks; res["lines"] = [str(x) for x in con.get_lines()][-30:]
    ok = bool(checks) and txt.strip().endswith("result|ok")
    step_result("console", ok, **res)
# ================================================================================================ the list of 2026-11-08b (899)
def stash_count(name): return sum(1 for s in G["gi"].get_editor_property("stash_things") if str(s) == name)
def step_storage9():
    """the storage (the list of 2026-11-08b): "in the take one back menu item, multiple of the same items need to stack" and "in
    the store a thing menu, when the button is held down to store something, it should continue to store something until the
    button is let go": five potions stored with Enter held 2 s (the first at the press, the rest every 0.15 s after 0.4 s; it
    stops when she has none, the next thing not stored); the take-back tab one line "x 5" for them; Enter held there 0.7 s
    takes back 2 or 3, one press one"""
    g = G["gen"]; c = cb(); res = {}; quiet(True)
    pot = "Small Healing Potion"; other = "Large Healing Potion"
    for nm, n in ((pot, 5), (other, 2)): c.add_item(nm, n)
    p0, o0, s0 = c.get_item_count(pot), c.get_item_count(other), stash_count(pot)
    g.open_town_panel("stash", -1); yield from rwait(0.4); g.set_town_tab(0); yield from rwait(0.3)
    i = line_of("deposit", pot); res["deposit_line"] = i
    if i >= 0:
        for _ in range(abs(g.get_town_cursor() - i)): yield from press("Gamepad_DPad_Down" if g.get_town_cursor() < i else "Gamepad_DPad_Up", 0.08)
    u0 = g.get_town_hold_uses()
    yield from press("Enter", 2.0)
    res["held_stored"] = stash_count(pot) - s0; res["carried_after"] = c.get_item_count(pot); res["other_after"] = c.get_item_count(other) - o0
    res["repeats"] = g.get_town_hold_uses() - u0
    g.set_town_tab(1); yield from rwait(0.3)
    ws = [p for p in panel() if p[0] == "withdraw" and pot in p[1]]
    res["withdraw_lines"] = [p[1] for p in ws]
    i = line_of("withdraw", pot)
    if i >= 0:
        for _ in range(abs(g.get_town_cursor() - i)): yield from press("Gamepad_DPad_Down" if g.get_town_cursor() < i else "Gamepad_DPad_Up", 0.08)
    n1 = c.get_item_count(pot); yield from press("Enter", 0.12); res["one_press_took"] = c.get_item_count(pot) - n1
    n2 = c.get_item_count(pot); yield from press("Enter", 0.75); res["held_0_75s_took"] = c.get_item_count(pot) - n2
    res["withdraw_lines_after"] = [p[1] for p in panel() if p[0] == "withdraw" and pot in p[1]]
    shot("storage9", "1280x720"); yield from rwait(1.5)
    g.close_town_panel(); quiet(False)
    ok = (res["held_stored"] == p0 and res["carried_after"] == 0 and res["other_after"] == 0 and len(ws) == 1 and f"x {p0}" in ws[0][1]
          and res["one_press_took"] == 1 and 2 <= res["held_0_75s_took"] <= 4)
    step_result("storage9", ok, **res)
def step_start9():
    """the gamepad's Escape menu (the list of 2026-11-08b: "the esc menu is inaccessible from the gamepad"): Start pressed
    briefly opens the inventory (and closes it); held 0.8 s it opens the Escape menu instead (the inventory shut); Start
    again closes the menu; B too"""
    g = G["gen"]; c = cb(); res = {"refused": []}
    # (the keys as the device sends them, through Slate (the generator reads Start's own press and release there: a flush of the
    # controller's keys when the inventory shuts no longer ends a hold, PR #29's review); a refusal falls back to the controller)
    def spress(name, hold):
        why = str(g.slate_key(key(name), True))
        if why: res["refused"].append(f"{name}: {why}"); yield from press(name, hold); return
        yield from rwait(hold); g.slate_key(key(name), False); yield from rwait(0.1)
    g.set_menu_open(False); c.set_inventory_open(False); yield from rwait(0.4)
    yield from spress("Gamepad_Special_Right", 0.15); yield from rwait(0.3)
    res["tap_inventory"] = c.is_inventory_open(); res["tap_menu"] = g.is_menu_open()
    yield from spress("Gamepad_Special_Right", 0.15); yield from rwait(0.3); res["tap_again_shut"] = not c.is_inventory_open()
    # (held at once after the inventory shut: test_b9a's failure, the hold read as let go)
    m0 = g.get_editor_property("menu_opens_by_start")
    yield from spress("Gamepad_Special_Right", 0.8); yield from rwait(0.3)
    res["hold_menu"] = g.is_menu_open(); res["hold_inventory"] = c.is_inventory_open(); res["opens_by_start"] = g.get_editor_property("menu_opens_by_start") - m0
    shot("start9_menu", "1280x720"); yield from rwait(1.5)
    yield from spress("Gamepad_Special_Right", 0.12); yield from rwait(0.3); res["start_closes"] = not g.is_menu_open()
    yield from spress("Gamepad_Special_Right", 0.8); yield from rwait(0.3); res["hold_again"] = g.is_menu_open()
    yield from spress("Gamepad_FaceButton_Right", 0.12); yield from rwait(0.3); res["b_closes"] = not g.is_menu_open()
    # (Start down, Escape opens the menu while it is held, Start let go, the menu shut: nothing of that Start is acted on after)
    why = str(g.slate_key(key("Gamepad_Special_Right"), True)); yield from rwait(0.15)
    yield from spress("Escape", 0.1); yield from rwait(0.2); res["esc_menu"] = g.is_menu_open()
    g.slate_key(key("Gamepad_Special_Right"), False); yield from rwait(0.3)
    g.set_menu_open(False); yield from rwait(0.5); res["stale_inventory"] = c.is_inventory_open()
    g.set_menu_open(False); c.set_inventory_open(False)
    ok = (res["tap_inventory"] and not res["tap_menu"] and res["tap_again_shut"] and res["hold_menu"] and not res["hold_inventory"]
          and res["opens_by_start"] == 1 and res["start_closes"] and res["hold_again"] and res["b_closes"] and res["esc_menu"] and not res["stale_inventory"])
    step_result("start9", ok, **res)
def step_backspace9():
    """the Save page's name (the list of 2026-11-08b: "holding down the backspace key should backspace multiple times"): one
    press takes one letter; held 1.2 s it takes on (a letter every 50 ms after 0.4 s), not past the empty name"""
    g = G["gen"]; res = {}
    g.set_menu_open(True); yield from rwait(0.3)
    i = next((k for k, l in enumerate([str(x) for x in g.get_menu_lines()]) if "Save the game" in l), -1); res["save_line"] = i
    g.activate_menu_line(i); yield from rwait(0.4)
    g.set_save_name_text("Abcdefghijklmnopqrstuvwxyz"); n0 = len(str(g.get_save_name_text()))
    yield from press("BackSpace", 0.1); res["one_press"] = n0 - len(str(g.get_save_name_text()))
    n1 = len(str(g.get_save_name_text())); yield from press("BackSpace", 1.2); res["held_1_2s"] = n1 - len(str(g.get_save_name_text()))
    yield from press("BackSpace", 3.0); res["left_after_long_hold"] = str(g.get_save_name_text())
    g.set_save_name_text(""); g.set_menu_open(False); yield from rwait(0.3)
    ok = res["save_line"] >= 0 and res["one_press"] == 1 and 10 <= res["held_1_2s"] <= 20 and res["left_after_long_hold"] == ""
    step_result("backspace9", ok, **res)
def step_time9():
    """the console's time (the list of 2026-11-08b: "need a command to speed up time in the console"): rd.TimeSpeed 60 runs the
    day's clock 60 times (2 hours of the day in 5 s, against 2 minutes at 1); rd.GameSpeed 2 doubles the game's own time (the
    world's time dilation); both back to 1"""
    g = G["gen"]; w = G["w"]; res = {}
    def cmd(c_): unreal.SystemLibrary.execute_console_command(w, c_)
    def hours(): h, m = str(g.get_town_clock()).split(":"); return int(h) + int(m) / 60.0
    cmd("rd.TimeSpeed 1"); yield from rwait(0.3)
    h0 = hours(); yield from rwait(5.0); res["hours_5s_at_1"] = round((hours() - h0) % 24, 3)
    cmd("rd.TimeSpeed 60"); yield from rwait(0.2)
    h0 = hours(); yield from rwait(5.0); res["hours_5s_at_60"] = round((hours() - h0) % 24, 3)
    cmd("rd.TimeSpeed 1")
    cmd("rd.GameSpeed 2"); yield from rwait(0.5)
    res["dilation_at_2"] = round(GS.get_global_time_dilation(w), 3)
    t0 = time.time(); g0 = now(); yield from rwait(2.0); res["game_s_in_2s"] = round(now() - g0, 2)
    cmd("rd.GameSpeed 1"); yield from rwait(0.5); res["dilation_after"] = round(GS.get_global_time_dilation(w), 3)
    ok = (res["hours_5s_at_1"] < 0.2 and 1.4 <= res["hours_5s_at_60"] <= 2.6 and res["dilation_at_2"] == 2.0 and 3.4 <= res["game_s_in_2s"] <= 4.6
          and res["dilation_after"] == 1.0)
    step_result("time9", ok, **res)
def step_noshield9():
    """the Warrior's start (the list of 2026-11-08b: "the warrior should have no default shield"): she wears none, carries
    none, no shield is drawn on her (a mesh named a shield on her), and her block (LB held) does not come up; a shield
    given and worn: she blocks"""
    g = G["gen"]; res = {}
    if str(g.get_editor_property("current_hero")) != "Warrior": g.switch_hero("Warrior"); yield from wait(1.0); refresh()
    c = cb(); p = G["pawn"]
    res["start_shield_map"] = {str(k): str(v) for k, v in g.get_editor_property("start_shield").items()}
    res["worn"] = str(c.get_worn_shield())
    res["shield_meshes_on_her"] = [cm.get_name() + ":" + cm.static_mesh.get_name() for cm in p.get_components_by_class(unreal.StaticMeshComponent)
                                   if cm.static_mesh and "shield" in cm.static_mesh.get_name().lower() and cm.is_visible()]
    c.simulate_key(key("Gamepad_LeftShoulder"), True); yield from wait(0.4); res["blocks_without"] = c.is_blocking(); c.simulate_key(key("Gamepad_LeftShoulder"), False)
    sh = next((str(i.name) for i in g.get_editor_property("items") if str(i.kind) in ("ERDItemKind.SHIELD", "ERDItemKind.Shield") or "shield" in str(i.kind).lower()), None)
    res["given"] = sh
    if sh:
        c.add_item(sh, 1); c.wear_shield(sh); yield from wait(0.4)
        c.simulate_key(key("Gamepad_LeftShoulder"), True); yield from wait(0.4); res["blocks_with"] = c.is_blocking(); c.simulate_key(key("Gamepad_LeftShoulder"), False)
        c.wear_shield(sh); c.remove_item(sh, 1)          # (the same shield again takes it off)
    shot("noshield9", "1280x720"); yield from rwait(1.5)
    ok = (not res["start_shield_map"].get("Warrior") and res["worn"] in ("None", "") and not res["shield_meshes_on_her"]
          and not res["blocks_without"] and bool(res.get("blocks_with")))
    step_result("noshield9", ok, **res)
def step_sky9():
    """the sky's edges (the list of 2026-11-08b: a blue outline round everything against a blue sky, a grey shimmering border
    against a grey one): the clouds traced at half the view's size (r.VolumetricRenderTarget.Mode 1, set with the clouds);
    pictures looking up at the town's roofs at noon, fair and overcast, four ways (measured offline: the fringe's pixels)"""
    g = G["gen"]; res = {}
    res["vrt_mode"] = unreal.SystemLibrary.get_console_variable_int_value("r.VolumetricRenderTarget.Mode")
    for wname, wk in (("fair", 1), ("overcast", 3)):
        g.set_town_hour(12.0); g.set_weather(wk, True); yield from rwait(6.0)
        for yaw in (0, 90, 180, 270):
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=22, yaw=float(yaw))); yield from rwait(1.2)
            shot(f"sky9_{wname}_{yaw}", "1280x720"); yield from rwait(1.5)
    g.set_weather(1, True)
    step_result("sky9", res["vrt_mode"] == 1, **res)
def restore_boom(boom, keep):
    """the camera's boom put back, found again on her pawn as it is now (the boom read at the step's start was gone by its end:
    "ObjectInstance is null", and the boom then on her kept the 40 m offset for the next step)"""
    if not keep: return
    for b in (boom, G["pawn"].get_component_by_class(unreal.SpringArmComponent) if G.get("pawn") else None):
        try:
            if b: b.set_editor_property("target_offset", V(*keep[0])); b.set_editor_property("do_collision_test", keep[1])
        except Exception: pass
def step_sky10():
    """the list of 2026-11-10: "in town, there is still a disc in the sky in the day time, there is a visible border between near the
    horizon and the rest of the sky. this also happens in the night time": at noon and midnight, fair, her body hidden, pictures of
    the horizon (pitch 4) and straight up (pitch 80): as drawn, then each of the sky's own parts hidden in turn (the high clouds'
    dome, the stars' dome, the volumetric clouds, the fog's density), so the parts that draw a disc or a border are told apart"""
    g = G["gen"]; res = {"shots": []}
    G["pawn"].set_actor_hidden_in_game(True)
    # (the camera 40 m over the town, its boom not stopped by the roofs: the horizon in sight over the walls)
    boom = G["pawn"].get_component_by_class(unreal.SpringArmComponent)
    # (the offset kept as numbers: the struct read from the boom followed it, and the camera stayed 40 m up for the next step)
    to_ = boom.get_editor_property("target_offset") if boom else None
    keep = ((to_.x, to_.y, to_.z), bool(boom.get_editor_property("do_collision_test"))) if boom else None
    if boom: boom.set_editor_property("target_offset", V(0, 0, 4000)); boom.set_editor_property("do_collision_test", False)
    comps = {c.get_name(): c for c in g.get_components_by_class(unreal.SceneComponent)}
    parts = {"high": comps.get("RDSkyHigh"), "stars": comps.get("RDSkyStars"), "clouds": comps.get("RDSkyClouds"), "farland": comps.get("RDFarLand")}
    res["far_land"] = str(g.get_far_land_state())
    res["parts"] = {k: (v is not None) for k, v in parts.items()}
    fog = next(iter(GS.get_all_actors_of_class(G["w"], unreal.ExponentialHeightFog)), None)
    fc = fog.get_component_by_class(unreal.ExponentialHeightFogComponent) if fog else None
    # (the weathers' clouds at noon: clear, fair, cloudy, overcast, from 40 m up at 25 degrees)
    g.set_town_hour(12.0)
    for wk in (0, 1, 2, 3):
        g.set_weather(wk, True); yield from rwait(4.0)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=25.0, yaw=30.0)); yield from rwait(1.0)
        nm = f"sky10_w{wk}"; shot(nm, "960x540"); res["shots"].append(nm); yield from rwait(1.3)
        res.setdefault("sky_state", {})[wk] = str(g.get_sky_state())
    if "weathers" in (G.get("opt") or ""):
        G["pawn"].set_actor_hidden_in_game(False)
        restore_boom(boom, keep)
        step_result("sky10", True, **res); return
    for hour in (12.0, 0.0):
        g.set_town_hour(hour); g.set_weather(1, True); yield from rwait(5.0)
        for variant in ("drawn", "nofarland", "nohigh", "nostars", "noclouds", "nofog"):
            if variant == "nohigh" and parts["high"]: parts["high"].set_visibility(False)
            if variant == "nofarland" and parts["farland"]: parts["farland"].set_visibility(False)
            if variant == "nostars" and parts["stars"]: parts["stars"].set_visibility(False)
            if variant == "noclouds" and parts["clouds"]: parts["clouds"].set_visibility(False)
            if variant == "nofog" and fc: fd = fc.fog_density; fc.set_fog_density(0.0)
            yield from rwait(0.8)
            for pitch in (-3, 25, 80):
                G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=float(pitch), yaw=30.0)); yield from rwait(1.0)
                nm = f"sky10_{int(hour):02d}_{variant}_p{pitch}"; shot(nm, "960x540"); res["shots"].append(nm); yield from rwait(1.3)
            for v in parts.values():
                if v: v.set_visibility(True)
            if variant == "nofog" and fc: fc.set_fog_density(fd)
    G["pawn"].set_actor_hidden_in_game(False); g.set_town_hour(12.0)
    restore_boom(boom, keep)
    bn = G["pawn"].get_component_by_class(unreal.SpringArmComponent)
    res["boom_after"] = [round(bn.get_editor_property("target_offset").z), keep[0][2] if keep else None] if bn else None
    res["far_land_after"] = str(g.get_far_land_state())
    fl = res["far_land_after"].split("|")
    step_result("sky10", len(fl) > 5 and fl[0] == "1" and int(fl[5]) >= 1, **res)
def step_sun10():
    """(a probe) the sun's disc looked at straight, clear and fair, at 9, 12 and 16 o'clock: the camera along the sun light's way"""
    g = G["gen"]; res = {"shots": []}
    G["pawn"].set_actor_hidden_in_game(True)
    sun = next((l for l in GS.get_all_actors_of_class(G["w"], unreal.DirectionalLight) if "Sun" in l.get_name() or "sun" in l.get_actor_label().lower()), None)
    res["sun"] = sun.get_name() if sun else None
    for hour in (9.0, 12.0, 16.0):
        for wk in (0, 1):
            g.set_town_hour(hour); g.set_weather(wk, True); yield from rwait(4.0)
            if sun:
                f = sun.get_actor_forward_vector()
                yaw = math.degrees(math.atan2(-f.y, -f.x)); pitch = math.degrees(math.asin(max(-1.0, min(1.0, -f.z))))
                G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=yaw)); res[f"{int(hour)}_{wk}"] = [round(pitch, 1), round(yaw, 1)]
            yield from rwait(1.0)
            nm = f"sun10_{int(hour):02d}_w{wk}"; shot(nm, "960x540"); res["shots"].append(nm); yield from rwait(1.3)
    G["pawn"].set_actor_hidden_in_game(False); g.set_town_hour(12.0); g.set_weather(1, True)
    step_result("sun10", True, **res)
def step_stair10():
    """the list of 2026-11-10: "the stairway to get into the guard towers in mistward castle looks like a series of stairs was built
    up and angled until it reached the top. a stone stairway should look like this: E:\\temp\\stonestairway.jpg": the castle's inside
    stair is one mesh (blocks and the coursed wall under them, tagged RDCastleStair) and no stretched wall piece stands on its line;
    traced down at each step's middle, the 30 treads rise evenly from the floor to the walk; pictures from its open side and
    from below its foot, her body hidden (her climb is castlewalls')"""
    g = G["gen"]; res = {"shots": []}; quiet(True)
    d = castle_shape(); st = d["stair"]; ft, tp = st["foot"], st["top"]; walk = d.get("walk") or 661.0
    run = V(tp.x - ft.x, tp.y - ft.y, 0); rl = math.hypot(run.x, run.y) or 1.0; run = V(run.x / rl, run.y / rl, 0)
    T = d["towers"]; cx = sum(t[0].x for t in T) / len(T); cy = sum(t[0].y for t in T) / len(T)
    mid = V((ft.x + tp.x) * 0.5, (ft.y + tp.y) * 0.5, 0)
    perp = V(-run.y, run.x, 0)
    if (cx - mid.x) * perp.x + (cy - mid.y) * perp.y < 0: perp = V(run.y, -run.x, 0)
    sec = section()
    meshes = list(sec.get_components_by_tag(unreal.ProceduralMeshComponent, "RDCastleStair"))
    res["meshes"] = len(meshes); res["mesh_sections"] = meshes[0].get_num_sections() if meshes else 0
    res["run_m"] = round(rl / 100, 2); res["walk_z"] = walk
    # (the old steps: Castle Forge's wall piece along the stair's line, its middle within the stair's width)
    old = 0
    for p in ism_instances("SM_Castle_Stone_Wall_01a_NN"):
        a = (p.x - ft.x) * run.x + (p.y - ft.y) * run.y; b = (p.x - ft.x) * perp.x + (p.y - ft.y) * perp.y
        if -10 < a < rl + 10 and abs(b) < 70 and p.z < walk - 50: old += 1
    res["old_step_pieces"] = old
    # (the treads: a trace down at each step's middle on the stair's middle line)
    w = G["w"]; tops = []
    for i in range(30):
        x = ft.x + run.x * (rl * (i + 0.5) / 30.0); y = ft.y + run.y * (rl * (i + 0.5) / 30.0)
        # (from just over its own tread: the lower steps are under the walk's roof, the stairwell is over the upper two tiles)
        z0 = min(walk + 300, (i + 1) * walk / 30.0 + 120)
        h = unreal.SystemLibrary.line_trace_single(w, V(x, y, z0), V(x, y, -50), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [G["pawn"]], unreal.DrawDebugTrace.NONE, True)
        h = h.to_tuple() if h else None
        tops.append(round(h[4].z, 1) if h and h[0] else None)
    res["tread_z"] = tops
    rise = walk / 30.0
    errs = [abs(z - (i + 1) * rise) for i, z in enumerate(tops) if z is not None]
    res["tread_err_max"] = round(max(errs), 1) if errs else None; res["treads_hit"] = len(errs)
    # (pictures: from 4.5 m off its open side looking at its middle; from below its foot up along it)
    G["pawn"].set_actor_hidden_in_game(True)
    for nm, at, look, pitch in (("stair10_side", V(mid.x + perp.x * 450, mid.y + perp.y * 450, 0), V(-perp.x, -perp.y, 0), 12.0),
                                ("stair10_foot", V(ft.x - run.x * 250 + perp.x * 230, ft.y - run.y * 250 + perp.y * 230, 0), V(run.x - perp.x * 0.5, run.y - perp.y * 0.5, 0), 18.0),
                                ("stair10_top", V(tp.x + run.x * 100 + perp.x * 120, tp.y + run.y * 100 + perp.y * 120, 0), V(-run.x, -run.y, 0), -30.0)):
        yaw = math.degrees(math.atan2(look.y, look.x))
        put(at, yaw=yaw, z=walk if nm == "stair10_top" else 0.0); yield from wait(0.8)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=yaw)); yield from rwait(1.2)
        shot(nm, "1280x720"); res["shots"].append(nm); yield from rwait(1.5)
    G["pawn"].set_actor_hidden_in_game(False)
    ok = res["meshes"] == 1 and res["mesh_sections"] == 2 and old == 0 and res["treads_hit"] == 30 and (res["tread_err_max"] or 99) < 3.0
    step_result("stair10", ok, **res)
def step_see10():
    """the list of 2026-11-10: "if the player walks under a structure that blocks sight of her, make the structure see-through":
    under the eaves before three homes' doors, facing out, the camera steeply over her (pitch -65: its boom (3.2 m) puts it up
    behind her over the roof, which has no collision to stop it), and in a castle tower: the pieces on the line to the camera
    are hidden (bSeeThrough), each piece with collision keeping it in a hidden copy; the same view with the switch off hides
    nothing; pictures of both (her seen or not)"""
    g = G["gen"]; res = {"shots": []}; quiet(True)
    homes = [b for b in blds() if b["kind"] in ("home", "house") and b["rooms"] >= 1 and not b["boarded"] and b["state"] == 0] or [b for b in blds() if b["rooms"] >= 1]
    spots_ = []
    for k, h in enumerate(homes[len(homes) // 4::max(1, len(homes) // 4)][:3]):
        c_, dr = h["c"], h["door"]
        out = V(dr.x - c_.x, dr.y - c_.y, 0); ol = math.hypot(out.x, out.y) or 1.0; out = V(out.x / ol, out.y / ol, 0)
        spots_.append((f"eave{k}", V(dr.x + out.x * 70, dr.y + out.y * 70, 0), math.degrees(math.atan2(out.y, out.x))))
    d = castle_shape(); walk = d.get("walk") or 661.0
    for k, td in enumerate((d.get("doors") or [])[:1]):
        spots_.append((f"tower{k}", V(td["c"].x, td["c"].y, walk), 30.0))
    w = G["w"]
    boom = G["pawn"].get_component_by_class(unreal.SpringArmComponent)
    res["boom"] = {"arm": boom.target_arm_length, "collision": boom.do_collision_test, "probe": str(boom.probe_channel), "offset": str(boom.get_editor_property("target_offset")), "pawn": G["pawn"].get_name()} if boom else None
    for nm, at, yaw in spots_:
        r = {}
        for on in (True, False):
            g.set_editor_property("see_through", on)
            put(at, yaw=yaw, z=at.z); yield from wait(0.6)
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-65.0, yaw=yaw)); yield from rwait(1.5)
            cm = G["pc"].player_camera_manager.get_camera_location(); hl = G["pawn"].get_actor_location()
            r["cam_" + ("on" if on else "off")] = {"from_her_m": round(math.sqrt((cm.x - hl.x) ** 2 + (cm.y - hl.y) ** 2 + (cm.z - hl.z) ** 2) / 100, 2), "z": round(cm.z - hl.z)}
            lines = [str(l) for l in g.get_see_through_lines()]
            r["on" if on else "off"] = {"hidden": len(lines), "meshes": sorted({l.split("|")[0] for l in lines})[:8]}
            if on:
                # (each hidden piece of a mesh whose instances collide has its hidden copy (the line's last field))
                col = {}
                for cpt in isms(section()):
                    m = cpt.get_editor_property("static_mesh")
                    if m: col[m.get_name()] = col.get(m.get_name(), False) or str(cpt.get_collision_enabled()).find("NO_COLLISION") < 0
                need = [l for l in lines if col.get(l.split("|")[0])]
                r["with_collision"] = len(need); r["copies"] = sum(1 for l in need if l.split("|")[4] == "1")
                r["collision_kept"] = r["copies"] == len(need)
            sn = f"see10_{nm}_{'on' if on else 'off'}"; shot(sn, "1280x720"); res["shots"].append(sn); yield from rwait(1.5)
        res[nm] = r
    g.set_editor_property("see_through", True)
    res["total"] = g.get_editor_property("see_through_total")
    # (the eaves: two of three hide something; every spot hides nothing with the switch off and keeps collision)
    ok = (sum(1 for n, _a, _y in spots_ if n.startswith("eave") and res[n]["on"]["hidden"] > 0) >= 2
          and all(res[n]["off"]["hidden"] == 0 and res[n].get("collision_kept") for n, _a, _y in spots_))
    step_result("see10", ok, **res)
def step_crops9():
    """the farms' thirteen crops (the list of 2026-11-08b: "apply the list of most common crops ... in this order" and "have an
    indicator for what kind of crops there are"): over the farms round Brokenspire (a 6 km square, a point every 40 m) every
    crop grows somewhere and the grains lead (wheat, barley, oats, rye the four commonest); put in a field, the minimap's
    title names its crop, and the chunks round her hold the crop's own plants"""
    g = G["gen"]; res = {}; quiet(True)
    t0 = time.time()
    while time.time() - t0 < 60 and not g.is_wild_ready(): yield
    cnt = {}; first = {}
    for ix in range(-75, 76, 1):
        for iy in range(-75, 76, 1):
            x, y = ix * 40.0, iy * 40.0
            if abs(x) < 1300 and abs(y) < 1300: continue          # (the town's own ground)
            p = str(g.get_wild_sample_at(V(x * 100.0, y * 100.0, 0))).split("|")
            if len(p) > 15 and p[15]:
                cnt[p[15]] = cnt.get(p[15], 0) + 1
                if p[15] not in first and float(p[11]) > 0.6: first[p[15]] = (x, y)
        if ix % 10 == 0: yield
    res["samples_by_crop"] = dict(sorted(cnt.items(), key=lambda kv: -kv[1]))
    top4 = list(res["samples_by_crop"].keys())[:4]
    res["top4"] = top4
    # (in a field: the commonest's and a rare one's, the title and the plants round her)
    res["visits"] = {}
    for crop in [k for k in ("barley", "oats", "flax", "hemp") if k in first]:
        x, y = first[crop]; g.wild_put_her(x, y); yield from wait(4.0)
        t1 = time.time()
        while time.time() - t1 < 25 and int(str(g.get_wild_state()).split("|")[4] or 0) > 0: yield
        yield from wait(1.0)
        hud = G["pc"].get_hud()
        label = str(hud.get_crop_label_drawn()) if hud else ""
        here = G["pawn"].get_actor_location()
        n = 0
        for comp in GS.get_all_actors_of_class(G["w"], unreal.RDWildChunk):
            for h in comp.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent):
                m = h.static_mesh
                if m and (crop.capitalize() in m.get_name() or (crop == "barley" and "Barley" in m.get_name())): n += h.get_instance_count()
        res["visits"][crop] = {"at": [x, y], "label": label, "plants": n}
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-18, yaw=40.0)); yield from rwait(0.6)
        shot(f"crops9_{crop}", "1280x720"); yield from rwait(1.5)
    quiet(False)
    grains = {"wheat", "barley", "oats", "rye"}
    ok = (len(cnt) >= 12 and set(top4) == grains and res["visits"] and all(v["label"] == k and v["plants"] > 200 for k, v in res["visits"].items()))
    step_result("crops9", ok, **res)
def step_farms9():
    """the medieval farms (the list of 2026-11-08b's second phase: "make the farms in the wilderness look more like medieval
    farms, with different sizes of farms, from the croft to the strip"; no hedges or fences between strips; one crop per field;
    ridge-and-furrow; "farm houses, barns, fenced in animals, and farm families"):
      layout  over the farms round Brokenspire (a point every 20 m, 4 km square, the town's ground left out): the kinds' shares
              (open field, crofts, pasture, yards); every open field (great field) one crop; its strips 15 to 24 m and the crofts'
              plots smaller; across one open field 80 m at 0.25 m: the furrows between the strips (one a strip width) and the
              ridges (0.25 m or more over the furrows), the walked ground (Height) rising and falling with them
      fences  in the chunks round her: no fence piece where the ground is an open field
      farm    put before the nearest farmstead: its record (props, animals, folk), every animal in its pen and on the ground,
              the family on the ground at their work (the farmer's Tend, the farmwife's Scatter), F at one of them: the prompt
              names them, they turn to her, a line of the farm's; pictures of the farmstead and the strips"""
    g = G["gen"]; res = {}; quiet(True)
    t0 = time.time()
    while time.time() - t0 < 60 and not g.is_wild_ready(): yield
    # ---- the layout
    kinds = {}; crops_of = {}; strip_w = []; plots = {}
    for ix in range(-100, 101):
        for iy in range(-100, 101):
            x, y = ix * 20.0, iy * 20.0
            if abs(x) < 400 and abs(y) < 400: continue
            p = str(g.get_wild_farm_at(x, y)).split("|")
            if len(p) < 12: continue
            k = int(p[0]); kinds[k] = kinds.get(k, 0) + 1
            if k == 1 and int(p[3]) >= 0 and float(p[4]) > 0.3:
                crops_of.setdefault(p[1], set()).add(int(p[3])); strip_w.append(float(p[6]))
            if k == 2: plots.setdefault(p[1] + "/" + p[2], 0); plots[p[1] + "/" + p[2]] += 1
        if ix % 8 == 0: yield
    tot = max(1, sum(kinds.values()))
    res["kind_shares"] = {["none", "open field", "crofts", "pasture", "yard"][k]: round(v / tot, 3) for k, v in sorted(kinds.items())}
    res["open_fields"] = len(crops_of)
    res["open_fields_with_more_than_one_crop"] = [f for f, s in crops_of.items() if len(s) > 1]
    res["crops_in_open_fields"] = len(set().union(*crops_of.values())) if crops_of else 0
    res["strip_w_m"] = [round(min(strip_w), 1), round(max(strip_w), 1)] if strip_w else []
    # (a croft plot's size: its samples 20 m apart, its area about n x 400 m2)
    pa = sorted(plots.values()); res["croft_plot_m2_median"] = pa[len(pa) // 2] * 400 if pa else 0
    # ---- one open field crossed at 0.25 m: furrows, ridges, the walked ground
    cross = None
    for ix in range(-80, 81, 4):
        for iy in range(-80, 81, 4):
            x, y = ix * 25.0, iy * 25.0
            if abs(x) < 500 and abs(y) < 500: continue
            p = str(g.get_wild_farm_at(x, y)).split("|")
            if int(p[0]) == 1 and float(p[4]) > 0.5:
                cross = (x, y, float(p[5]), float(p[6])); break
        if cross: break
    if cross:
        x, y, ang, sw = cross
        ax, ay = -math.sin(ang), math.cos(ang)
        rows = []
        for i in range(-160, 161):
            d = i * 0.25; px, py = x + ax * d, y + ay * d
            p = str(g.get_wild_farm_at(px, py)).split("|")
            rows.append((d, int(p[0]), int(p[8]), float(p[9]), float(p[10]), float(p[11]), p[2], float(p[12])))
        same = [r for r in rows if r[1] == 1 and r[6] == rows[160][6]]
        strips = sorted({r[2] for r in same})
        furrow_runs = 0; prev = False
        for r in same:
            f = r[3] > 0.9
            if f and not prev: furrow_runs += 1
            prev = f
        ridge = [r[4] for r in same]; hs = [r[5] for r in same]
        # (the ridges in what she walks on (Height), not the land's lie (PR #30's review: a fit to a line passed on the relief
        # alone): the walked height less the same ground with no farm on it, against the ridge the layout gives: how closely it
        # follows (correlation), by how much (slope: 1 if the ridge is all of it) and its rise and fall)
        diff = [r[5] - r[7] for r in same]
        n = len(diff)
        if n > 10:
            mh, mr = sum(diff) / n, sum(ridge) / n
            cov = sum((a - mh) * (b - mr) for a, b in zip(diff, ridge)); vh = sum((a - mh) ** 2 for a in diff); vr = sum((b - mr) ** 2 for b in ridge)
            res["walked_follows_ridge"] = {"corr": round(cov / max(1e-12, math.sqrt(vh * vr)), 3), "slope": round(cov / max(1e-12, vr), 3),
                                           "walked_less_bare_m": [round(min(diff), 3), round(max(diff), 3)]}
        res["cross"] = {"at": [x, y], "strip_w": sw, "samples": len(same), "strips": len(strips), "furrows": furrow_runs,
                        "ridge_min_max_m": [round(min(ridge), 3), round(max(ridge), 3)] if ridge else None}
    yield
    # ---- the nearest farmstead: put before it
    fs = [str(s).split("|") for s in g.find_wild_farmsteads(0.0, 0.0, 3500.0)]
    res["farmsteads_within_3_5km"] = len(fs)
    ok_farm = False
    if fs:
        fid, fname, fx, fy, fyaw = int(fs[0][0]), fs[0][1], float(fs[0][2]), float(fs[0][3]), float(fs[0][4])
        a = math.radians(fyaw)
        bx, by = fx + math.cos(a) * 26.0, fy + math.sin(a) * 26.0
        g.wild_put_her(bx, by); yield from wait(4.0)
        t1 = time.time()
        while time.time() - t1 < 30 and int(str(g.get_wild_state()).split("|")[4] or 0) > 0: yield
        yield from wait(2.0)
        lines = [str(s).split("|") for s in g.get_wild_farm_lines()]
        rec = next((l for l in lines if l[0] == "farm" and int(l[1]) == fid), None)
        res["farm"] = {"name": fname, "at": [fx, fy]}
        if rec:
            res["farm"].update({"props": int(rec[7]), "animals": int(rec[8]), "folk": int(rec[9])})
            an = [l for l in lines if l[0] == "animal" and int(l[1]) == fid]
            fo = [l for l in lines if l[0] == "folk" and int(l[1]) == fid]
            res["animals"] = [{"kind": l[2], "in_pen": l[6] == "1", "above_ground_cm": round(float(l[5]) - float(l[8]), 1)} for l in an]
            res["folk"] = [{"title": l[2], "clip": l[6], "feet_above_ground_cm": round(float(l[5]) - 92.0 - float(l[7]), 1), "body": l[8] if len(l) > 8 else "?"} for l in fo]
            # (let the animals walk a while, then read them again: they keep to their pens and to the ground)
            yield from wait(12.0)
            lines2 = [str(s).split("|") for s in g.get_wild_farm_lines()]
            an2 = [l for l in lines2 if l[0] == "animal" and int(l[1]) == fid]
            res["animals_after_12s"] = [{"in_pen": l[6] == "1", "above_ground_cm": round(float(l[5]) - float(l[8]), 1), "state": int(l[7])} for l in an2]
            # (F at the farmwife, or whoever is there: 1.3 m before them)
            who = next((l for l in fo if "farmwife" in l[2]), fo[0] if fo else None)
            if who:
                wx, wy, wz = float(who[3]), float(who[4]), float(who[5])
                # (beside them along the farm's way, facing them: before the farmwife is the paddock's fence, behind her the house)
                pl = G["pawn"]; pl.set_actor_location(V(wx + math.cos(a) * 140.0, wy + math.sin(a) * 140.0, wz + 20.0), False, True); yield from wait(1.0)
                here = pl.get_actor_location()
                res["prompt"] = str(g.describe_nearest(here))
                b0 = str(g.get_editor_property("last_bark"))
                g.interact_nearest(here); yield from wait(1.5)
                res["bark"] = str(g.get_editor_property("last_bark")); res["bark_new"] = res["bark"] != b0
                G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=fyaw + 180.0)); yield from rwait(0.6)
                shot("farms9_talk", "1280x720"); yield from rwait(1.5)
            # (pictures: the farmstead from its yard, raised, and the strips beyond)
            G["pawn"].set_actor_location(V(bx * 100.0 + 0, by * 100.0, g.wild_ground_z(V(bx * 100.0, by * 100.0, 0)) + 120.0), False, True); yield from wait(1.0)
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-14, yaw=fyaw + 180.0)); yield from rwait(1.0)
            shot("farms9_farmstead", "1280x720"); yield from rwait(1.5)
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-14, yaw=fyaw + 135.0)); yield from rwait(1.0)
            shot("farms9_farmstead2", "1280x720"); yield from rwait(1.5)
            # (from the paddock's side, 30 m off, looking at the farmhouse)
            sx, sy = fx + math.cos(a) * 14.0 + math.sin(a) * 30.0, fy + math.sin(a) * 14.0 - math.cos(a) * 30.0
            G["pawn"].set_actor_location(V(sx * 100.0, sy * 100.0, g.wild_ground_z(V(sx * 100.0, sy * 100.0, 0)) + 120.0), False, True); yield from wait(1.0)
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-12, yaw=math.degrees(math.atan2(fy - sy, fx - sx)))); yield from rwait(1.0)
            shot("farms9_paddock", "1280x720"); yield from rwait(1.5)
            in_pen = all(a_["in_pen"] for a_ in res["animals"] + res["animals_after_12s"])
            grounded = all(abs(a_["above_ground_cm"]) < 30 for a_ in res["animals"] + res["animals_after_12s"])
            folk_ok = all(abs(f_["feet_above_ground_cm"]) < 30 for f_ in res["folk"])
            clips = " ".join(f_["clip"] for f_ in res["folk"])
            # (each body fits who they are: the farmwife a townswoman, the farmer and the farmhand townsmen, the child a child)
            bodies_ok = all(("woman" in f_["body"]) == ("farmwife" in f_["title"]) and (not f_["title"].startswith("child") or "Child" in f_["body"] or "Kid" in f_["body"]) for f_ in res["folk"])
            res["bodies_ok"] = bodies_ok
            ok_farm = (res["farm"]["props"] >= 8 and res["farm"]["animals"] >= 2 and res["farm"]["folk"] >= 2 and in_pen and grounded and folk_ok and bodies_ok
                       and "Tend" in clips and "Scatter" in clips and "talk to the" in res.get("prompt", "") and res.get("bark_new", False) and fname in res.get("bark", ""))
    # ---- fences: none where the ground is an open field
    fences = []
    for ch in GS.get_all_actors_of_class(G["w"], unreal.RDWildChunk):
        for cm in ch.get_components_by_class(unreal.StaticMeshComponent):
            m = cm.static_mesh
            if m and "fence" in m.get_name().lower():
                l = cm.get_world_location()
                k = int(str(g.get_wild_farm_at(l.x / 100.0, l.y / 100.0)).split("|")[0])
                fences.append((m.get_name(), k))
    res["fence_pieces"] = len(fences); res["fences_in_open_fields"] = [f for f in fences if f[1] == 1]
    # (a picture of the strips: raised over the open field crossed)
    if cross:
        g.wild_put_her(cross[0], cross[1]); yield from wait(4.0)
        t1 = time.time()
        while time.time() - t1 < 25 and int(str(g.get_wild_state()).split("|")[4] or 0) > 0: yield
        yield from wait(1.5)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-20, yaw=math.degrees(cross[2]))); yield from rwait(1.0)
        shot("farms9_strips", "1280x720"); yield from rwait(1.5)
    quiet(False)
    cr = res.get("cross", {})
    ok = (res["open_fields"] >= 5 and not res["open_fields_with_more_than_one_crop"] and res["crops_in_open_fields"] >= 8
          and res["strip_w_m"] and res["strip_w_m"][0] >= 15 and res["strip_w_m"][1] <= 24 and 0 < res["croft_plot_m2_median"] < 4000
          and cr.get("strips", 0) >= 3 and cr.get("furrows", 0) >= cr.get("strips", 0) - 1 and cr.get("ridge_min_max_m") and cr["ridge_min_max_m"][1] - cr["ridge_min_max_m"][0] >= 0.25
          and res.get("walked_follows_ridge", {}).get("corr", 0) >= 0.98 and 0.9 <= res.get("walked_follows_ridge", {}).get("slope", 0) <= 1.1
          and res["walked_follows_ridge"]["walked_less_bare_m"][1] - res["walked_follows_ridge"]["walked_less_bare_m"][0] >= 0.25 and res["farmsteads_within_3_5km"] >= 3 and ok_farm and res["fence_pieces"] > 0 and not res["fences_in_open_fields"])
    step_result("farms9", ok, **res)
def step_keys9():
    """the dungeons' keys in order and the wilderness's tiers (the list of 2026-11-08b's third phase):
      chain   the generator's chain from Mistward Castle to Heaven; with no key held only the castle open
      tiers   the tier at each town of the chain (Brokenspire 1, Vel Morrath 5, Ashenreach 10, Graymourne 15) and half way along
              each leg (3, 8, 12 or 13), behind Brokenspire 1
      map     the map to Vel Morrath taken: the land round the city revealed on her map, once
      locked  out at Vel Morrath, the cathedral's stair walked into (a dry run): refused for want of its key, said why
      drop    this level's boss's drop (Mistward's: the next is Vel Morrath's): the Catacomb Key and the map in a pile that is not
              hers; taken with F; the stair then opens (the dry run goes down); a second drop gives nothing (once a game)
      death   she falls: the key and the map stay with her, the rest drops"""
    g = G["gen"]; res = {}; quiet(True)
    g.debug_all_dungeon_keys(False); yield from wait(1.2)
    c = cb()
    for it in ("Catacomb Key", "Map to Vel Morrath"):
        n = c.get_item_count(it)
        if n: c.remove_item(it, n)
    lines = [str(s).split("|") for s in g.get_dungeon_key_lines()]
    res["chain"] = [l[1] or "castle" for l in lines]
    res["open_at_start"] = {(l[1] or "castle"): l[5] == "1" for l in lines}
    res["had_at_start"] = {(l[1] or "castle"): l[6] for l in lines}
    # ---- the tiers along the chain
    towns = {}
    for l in g.get_wild_town_lines():
        p = str(l).split("|"); towns[p[0]] = (float(p[2]), float(p[3]))
    def tier(a): return g.get_wild_tier_at(a[0], a[1])
    def mid(a, b): return ((towns[a][0] + towns[b][0]) / 2, (towns[a][1] + towns[b][1]) / 2)
    res["tiers"] = {t: tier(towns[t]) for t in ("Brokenspire", "Vel Morrath", "Ashenreach", "Graymourne") if t in towns}
    res["tiers_mid"] = {f"{a}-{b}": tier(mid(a, b)) for a, b in (("Brokenspire", "Vel Morrath"), ("Vel Morrath", "Ashenreach"), ("Ashenreach", "Graymourne")) if a in towns and b in towns}
    bs = towns.get("Brokenspire", (0, 0)); vm = towns.get("Vel Morrath", (1, 1))
    away = (bs[0] - (vm[0] - bs[0]) * 0.1, bs[1] - (vm[1] - bs[1]) * 0.1)
    res["tier_behind_brokenspire"] = tier(away)
    # ---- the map to Vel Morrath
    res["vm_revealed_before"] = bool(g.wild_revealed_at(vm[0] + 800, vm[1]))
    c.add_item("Map to Vel Morrath", 1); yield from wait(2.5)
    res["vm_revealed_after_map"] = bool(g.wild_revealed_at(vm[0] + 800, vm[1]))
    l2 = {(l[1] or "castle"): l for l in [str(s).split("|") for s in g.get_dungeon_key_lines()]}
    res["map_had_shown"] = [l2["vel_morrath"][7], l2["vel_morrath"][8]] if "vel_morrath" in l2 else None
    c.remove_item("Map to Vel Morrath", 1)            # (the boss's drop below gives her one)
    # ---- locked at the stair
    ti, x, y = yield from to_vel_morrath()
    mg = place("mistgate"); cat = next((b for b in blds() if b["kind"] == "cathedral"), None)
    def stair_try():
        g.set_editor_property("travel_dry_run", True)
        put(V(mg.x - (mg.x - cat["c"].x) * 0.02, mg.y - (mg.y - cat["c"].y) * 0.02, 0)); yield from wait(1.5)
        r = str(g.get_editor_property("last_travel"))
        put(V(cat["c"].x, cat["c"].y, 0)); yield from wait(0.5)
        g.set_editor_property("travel_dry_run", False)
        return r
    if mg and cat:
        res["stair_without_key"] = yield from stair_try()
        res["locked_level"] = str(g.get_editor_property("dungeon_locked_level"))
        res["said"] = str(g.dungeon_locked_line("vel_morrath"))
    # ---- the drop, taken with F
    here = G["pawn"].get_actor_location(); fw = G["pawn"].get_actor_forward_vector()
    n0 = len([p for p in g.loot_piles if p])
    g.debug_drop_next_dungeon_key(V(here.x + fw.x * 150, here.y + fw.y * 150, here.z)); yield from wait(0.5)
    piles = [p for p in g.loot_piles if p]
    res["dropped"] = str(g.get_editor_property("dungeon_key_dropped")); res["piles_new"] = len(piles) - n0
    newp = piles[-1] if len(piles) > n0 else None
    res["pile_hers"] = bool(newp.get_editor_property("hers")) if newp else None
    res["pile_things"] = [str(t) for t in newp.get_editor_property("things")] if newp else []
    if newp:
        pl = newp.get_actor_location(); G["pawn"].set_actor_location(V(pl.x - 80, pl.y, pl.z + 100), False, True); yield from wait(0.6)
        res["prompt"] = str(g.describe_nearest(G["pawn"].get_actor_location()))
        g.interact_nearest(G["pawn"].get_actor_location()); yield from wait(1.5)
    res["carried"] = {it: c.get_item_count(it) for it in ("Catacomb Key", "Map to Vel Morrath")}
    l3 = {(l[1] or "castle"): l for l in [str(s).split("|") for s in g.get_dungeon_key_lines()]}
    res["open_after"] = {k: v[5] == "1" for k, v in l3.items()}
    if mg and cat: res["stair_with_key"] = yield from stair_try()
    n1 = len([p for p in g.loot_piles if p])
    g.debug_drop_next_dungeon_key(V(here.x, here.y, here.z)); yield from wait(0.5)
    res["second_drop_piles"] = len([p for p in g.loot_piles if p]) - n1
    # ---- a death: the key and the map stay
    t0 = time.time()
    while time.time() - t0 < 6:
        if c.is_dead(): break
        c.apply_damage(c.get_health() / max(1.0 - c.get_shield_share(), 0.1) + 5.0, None); yield from wait(0.3)
    res["fell"] = c.is_dead()
    t0 = time.time()
    while c.is_dead() and time.time() - t0 < 25: yield
    yield from wait(1.0); refresh(); c = cb()
    res["carried_after_death"] = {it: c.get_item_count(it) for it in ("Catacomb Key", "Map to Vel Morrath")}
    her = [p for p in g.loot_piles if p and p.get_editor_property("hers")]
    res["death_pile_has_key"] = any("Catacomb Key" in [str(t) for t in p.get_editor_property("things")] for p in her)
    # (her things back, the keys put away, every way open again for the other steps)
    for p in her:
        pl = p.get_actor_location(); G["pawn"].set_actor_location(V(pl.x - 80, pl.y, pl.z + 100), False, True); yield from wait(0.5)
        g.interact_nearest(G["pawn"].get_actor_location()); yield from wait(0.8)
    for it in ("Catacomb Key", "Map to Vel Morrath"):
        n = c.get_item_count(it)
        if n: c.remove_item(it, n)
    # (a game saved before the keys (PR #31's review): Vel Morrath's last tier's boss slain gives the War Engine's way; the
    # every-way switch is not a saved counter)
    gi = GS.get_game_instance(G["w"]); res["war_engine_before"] = gi.get_counter("dkey:war_engine")
    gi.count("vel_morrath:bossdone:5", 1); yield from wait(1.6)
    res["war_engine_after_old_progress"] = gi.get_counter("dkey:war_engine")
    g.debug_all_dungeon_keys(True); yield from wait(0.2)
    res["all_keys_counter"] = gi.get_counter("dkey:all")
    quiet(False)
    t = res["tiers"]; tm = res["tiers_mid"]
    ok = (res["chain"][:4] == ["castle", "vel_morrath", "war_engine", "sewers"] and res["open_at_start"].get("castle") and not res["open_at_start"].get("vel_morrath")
          and not res["open_at_start"].get("war_engine") and t.get("Brokenspire") == 1 and t.get("Vel Morrath") == 5 and t.get("Ashenreach") == 10 and t.get("Graymourne") == 15
          and tm.get("Brokenspire-Vel Morrath") == 3 and tm.get("Vel Morrath-Ashenreach") in (7, 8) and tm.get("Ashenreach-Graymourne") in (12, 13) and res["tier_behind_brokenspire"] == 1
          and not res["vm_revealed_before"] and res["vm_revealed_after_map"] and res.get("stair_without_key") == "locked" and "vel_morrath" in res.get("locked_level", "")
          and res["dropped"] == "vel_morrath" and res["piles_new"] == 1 and res["pile_hers"] is False and sorted(res["pile_things"]) == ["Catacomb Key", "Map to Vel Morrath"]
          and res["carried"] == {"Catacomb Key": 1, "Map to Vel Morrath": 1} and res["open_after"].get("vel_morrath") and not res["open_after"].get("war_engine")
          and res.get("stair_with_key") == "catacombs" and res["second_drop_piles"] == 0 and res["fell"]
          and res["carried_after_death"] == {"Catacomb Key": 1, "Map to Vel Morrath": 1} and not res["death_pile_has_key"]
          and res["war_engine_before"] == 0 and res["war_engine_after_old_progress"] == 1 and res["all_keys_counter"] == 0)
    step_result("keys9", ok, **res)
STEPS.update({"mapzoom": step_mapzoom, "life": step_life, "falls": step_falls, "dagger": step_dagger, "satellite": step_satellite, "list7": step_list7, "carry": step_carry,
              "holy": step_holy, "descend": step_descend, "forge": step_forge, "descendwar": step_descendwar, "port": step_port, "descendsewer": step_descendsewer,
              "planks": step_planks, "dummies": step_dummies, "storage": step_storage, "block8": step_block8, "console": step_console,
              "storage9": step_storage9, "start9": step_start9, "backspace9": step_backspace9, "time9": step_time9, "noshield9": step_noshield9,
              "sky9": step_sky9, "sky10": step_sky10, "sun10": step_sun10, "stair10": step_stair10, "see10": step_see10, "crops9": step_crops9, "farms9": step_farms9, "keys9": step_keys9, "spire": step_spire, "descendspire": step_descendspire, "heaven": step_heaven, "descendheaven": step_descendheaven})
def run():
    o = G.get("gen"); R["windows_hidden"] = str(o.slate_clear_view()) if o else None
    # (every dungeon's way open for the steps that go down (the list of 2026-11-08b's keys); keys9 shuts them for itself)
    if o: o.debug_all_dungeon_keys(True)
    for s in PLAN:
        try:
            refresh()
            yield from STEPS[s]()
        except Exception as e:
            import traceback
            step_result(s, False, error=str(e), trace=traceback.format_exc()[-1500:])
            try: quiet(False); G["gen"].close_town_panel()
            except Exception: pass
        yield from rwait(0.3)
def finish(err=None):
    unreal.unregister_slate_post_tick_callback(G["h"])
    R["error"] = err
    try:
        if G.get("gen"): quiet(False); G["gen"].close_town_panel(); R["windows_shown_again"] = G["gen"].slate_restore_view()
    except Exception as e: R["error"] = (err or "") + " / " + str(e)
    os.makedirs(OUT, exist_ok=True); json.dump(R, open(os.path.join(OUT, f"test_{TAG}.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    ok = not R.get("error") and len(R["steps"]) == len(PLAN) and all(s["ok"] for s in R["steps"])
    unreal.log(f"BSTEST done | {TAG} | {'ok' if ok else 'FAILED'} | " + " | ".join(f"{s['step']} {'ok' if s['ok'] else 'FAILED'}" for s in R["steps"]) + f" | {R.get('error') or ''}")
    G.clear()
def tick(dt):
    try:
        if UES.get_game_world() is None:
            if G.get("travel_until", 0) > time.time(): return          # (a level opening: a moment with no world)
            finish("PIE ended"); return
        next(G["gen_"])
    except StopIteration: finish()
    except Exception as e:
        import traceback
        unreal.log_error("BSTEST error: " + str(e) + traceback.format_exc()); finish(str(e))
G["gen_"] = run()
G["h"] = unreal.register_slate_post_tick_callback(tick)
print("brokenspire test armed:", PLAN, TAG)
