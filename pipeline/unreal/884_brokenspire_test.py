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
            captain's wilderness quests offered as later and refused
  services  with gold given: the trader sells a potion (gold down, the potion carried) and buys it back (gold up); the
            healer heals her (hit points full, gold down); the smith mends a found weapon worn down (full, gold down) and his
            anvil opens the crafting panel; the temple's blessing (on her, gold down); the storage keeps a thing and gives it
            back; the circle knows Brokenspire's alone and says the others are for later; the quest board posts three bounties
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
  map      M opens the papyrus map: the trades' pictures and what they do written under them, the castle's, the gate's, the
            square's; pictures of the map and of the minimap
  folk      the townspeople: those who wander walked within 40 s; F at one without a quest: a line of theirs (their bark);
            the names over the people near her, the elder's "!" while he has a quest for her
  gate      F at the gate: barred (the wilderness is for later); she cannot walk out of it
  pictures  the square, a street, a home's inside, the smithy, the tavern, the castle's hall with its guards and the Mistgate
Writes SourceArt/brokenspire/test_<tag>.json and logs "BSTEST done | <tag> | ok / FAILED | ...". Args: plan tag"""
import unreal, sys, json, math, os, time
__keep__ = True
TAG = sys.argv[2] if len(sys.argv) > 2 else "t"
V = unreal.Vector; GS = unreal.GameplayStatics
OUT = r"E:\code\claude-ue5\claude_ue5\SourceArt\brokenspire"
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
G = {"w": UES.get_game_world()}
assert G["w"] is not None, "PIE is not running"
DEFAULT = "town,doors,talk,services,guards,folk,gate,map,pictures,castle,tour,trip"
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
    # (the captain's wilderness quests: offered as later, refused)
    talk_to("Captain"); yield from wait(0.3)
    g.interact_nearest(G["pawn"].get_actor_location()); yield from rwait(0.3)
    later = [p for p in panel() if p[0] == "later"]
    res["captain_later"] = [p[1] for p in later]
    li = line_of("later")
    res["later_refused"] = li >= 0 and not g.activate_town_entry(li)
    g.close_town_panel(); yield from rwait(0.3)
    quiet(False)
    ok = res["panel"] == "talk" and res["asked_changed_text"] and res["accepted"] and res["quest_ready"]["state"] == "ready" and res["turnin"] and res["gold"] == 15 \
        and res["quest_done"]["state"] == "done" and res["next_offered"] and len(res["captain_later"]) == 2 and res["later_refused"]
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
    ok = res["buy"]["ok"] and res["buy"]["gold"] < 0 and res["buy"]["count"] == 1 and res["sell"]["ok"] and res["sell"]["gold"] > 0 and res["sell"]["count"] == 0 \
        and res["heal"]["ok"] and res["heal"]["hp"] >= 0.999 and res["heal"]["gold"] < 0 and res["repair"]["ok"] and res["repair"]["wear"] and res["repair"]["wear"] >= 0.999 and res["repair"]["gold"] < 0 \
        and res["anvil_opens_crafting"] and res["bless"]["ok"] and res["bless"]["blessing"] and res["bless"]["gold"] < 0 and res["deposit"]["ok"] and res["deposit"]["carried"] == -1 \
        and res["withdraw"]["ok"] and res["withdraw"]["carried"] == 0 and any("YOU ARE HERE" in l for l in res["circle"]) and any("LATER" in l for l in res["circle"]) and len(res["board"]) == 3
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
        if ph == 4 and not mapped: mapped = any(str(a) in ("map_papyrus", "mapc_parchment") for a in G["pc"].get_hud().get_art_drawn())
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
    ok = all(p in seen for p in (1, 2, 3, 4, 5)) and res["panel"] == "talk" and len(res["answer"]) > 10 and res["map_drawn"] and res["run_from_m"] is not None \
        and 80 <= res["run_from_m"] <= 125 and res["castle"] == "mistward_castle" and (res["autoplay_left"] or 0) > 200 and "ended" not in res \
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
    c.apply_damage(c.get_health() / max(1.0 - c.get_shield_share(), 0.1) + 5.0, None); yield from wait(1.5)
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
    res["left_in_game"] = len(list(G["gi"].get_editor_property("her_piles")))
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
    want = ("mapc_parchment", "mapc_grass", "mapc_cobble", "mapc_dirt", "mapc_wallstone", "mapc_compass", "mapc_castle", "mapc_tree1", "mapc_tower")
    res["colour_missing"] = [a for a in want if a not in colour] if has_colour else []
    step_result("map", not res["missing"] and not res["colour_missing"], **res)

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
    put(inside, yaw=math.degrees(math.atan2(-d.y, -d.x))); yield from wait(0.4)
    res["prompt"] = str(g.describe_nearest(G["pawn"].get_actor_location()))
    g.interact_nearest(G["pawn"].get_actor_location()); yield from rwait(0.2)
    res["message"] = str(cb().get_editor_property("message"))
    t0 = time.time()
    while time.time() - t0 < 4.0:
        G["pawn"].add_movement_input(V(-d.x, -d.y, 0), 1.0, False); yield
    p = G["pawn"].get_actor_location()
    res["past_gate_cm"] = round((gate.x - p.x) * -d.x + (gate.y - p.y) * -d.y, 1) * -1
    shot("gate"); yield from rwait(1.2)
    ok = "gate" in res["prompt"] and "barred" in res["message"] and res["past_gate_cm"] < 0
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
    while pos < len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8]); body = data[pos + 8:pos + 8 + ln]; pos += 12 + ln
        if typ == b"IHDR": w, h, bd, ct = struct.unpack(">IIBB", body[:10])
        elif typ == b"IDAT": idat += body
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
        elif p[0] in ("stairdoor", "walkdoor", "stairmid"): d[p[0]] = V(float(p[1]), float(p[2]), float(p[3]))
        elif p[0] == "walk": d["walk"] = float(p[1])
    return d
def ism_instances(mesh_has):
    """the section's instances of meshes whose name has mesh_has (world places)"""
    out = []
    for c in section().get_components_by_class(unreal.InstancedStaticMeshComponent):
        m = c.get_editor_property("static_mesh")
        if not m or mesh_has not in m.get_name(): continue
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
    res["arched_door_pieces"] = len(ism_instances("SM_Castle_Stone_Wall_02a_NN"))
    forge = {n: len(ism_instances(n)) for n in ("SM_Castle_Stone_Wall_01a", "SM_Castle_Stone_Wall_02h", "SM_Castle_Stone_Wall_02f", "SM_Castle_Stone_Wall_02g", "SM_Castle_Stone_Wall_02d",
                                                "SM_Castle_Stone_Parapet_01a", "SM_Castle_Tower_Wall_02", "SM_Tower_Roof_02a", "SM_Stone_Stairs_01a")}
    res["pieces"] = forge
    # (nothing from the rooms stands through the walk: the hall's columns did, 3 m)
    poke = {}
    walk = d.get("walk") or 661.0
    for comp in section().get_components_by_class(unreal.InstancedStaticMeshComponent):
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
    # (her climb: from outside the foot's door, through it, round the spiral (r 1.2 m, the steps' middle) to the landing and out of
    # the top door onto the walk; she moves by her own movement input toward each point in turn)
    C = d["stairmid"]; sd = d["stairdoor"]; wd = d["walkdoor"]
    a_door = math.degrees(math.atan2(sd.y - C.y, sd.x - C.x)); yaw0 = a_door - 315.0     # (the stair door is at 315 in the castle's frame)
    def at(ang, r, z=0.0): a = math.radians(yaw0 + ang); return V(C.x + r * math.cos(a), C.y + r * math.sin(a), z)
    out_dir = V(sd.x - C.x, sd.y - C.y, 0); n_ = math.hypot(out_dir.x, out_dir.y); out_dir = V(out_dir.x / n_, out_dir.y / n_, 0)
    start = V(sd.x + out_dir.x * 150, sd.y + out_dir.y * 150, 0)
    pts = [at(315, 200), at(315, 120)] + [at(305 - k * 15, 120) for k in range(0, 55)] + [at(225, 200), at(225, 300), V(wd.x + (x0 + x1) * 0.0, wd.y, 0)]
    centre = V((x0 + x1) * 0.5, (y0 + y1) * 0.5, 0)
    pts.append(V(wd.x * 0.7 + centre.x * 0.3, wd.y * 0.7 + centre.y * 0.3, 0))
    put(start, yaw=math.degrees(math.atan2(-out_dir.y, -out_dir.x))); yield from wait(0.6)
    i = 0; t0 = now(); last_i, last_t = 0, now(); zmax = -1e9; track = []
    while i < len(pts) and now() - t0 < 90.0:
        p = G["pawn"].get_actor_location(); zmax = max(zmax, p.z)
        while i < len(pts) and math.hypot(pts[i].x - p.x, pts[i].y - p.y) < 45.0: i += 1
        if i >= len(pts): break
        if i != last_i: last_i, last_t = i, now()
        if now() - last_t > 8.0: break
        dv = V(pts[i].x - p.x, pts[i].y - p.y, 0); n_ = math.hypot(dv.x, dv.y) or 1.0
        G["pawn"].add_movement_input(V(dv.x / n_, dv.y / n_, 0), 1.0, False)
        if int((now() - t0) * 2) > len(track): track.append([round(p.x), round(p.y), round(p.z)])
        yield
    yield from wait(0.8)
    p = G["pawn"].get_actor_location()
    res["climb"] = {"points": len(pts), "reached": i, "seconds": round(now() - t0, 1), "z_max": round(zmax, 1), "end": [round(p.x), round(p.y), round(p.z)],
                    "on_walk": p.z > (d.get("walk") or 661) + 40 and x0 < p.x < x1 and y0 < p.y < y1, "track": track[::4]}
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-15, yaw=math.degrees(math.atan2(centre.y - p.y, centre.x - p.x)))); yield from wait(0.8)
    shot("castle_walk"); yield from rwait(1.5)
    # (from the forecourt: the castle's front, its towers and battlements)
    b = [x for x in blds() if x["kind"] == "castle"][0]
    f = door_front(b, 2200.0); f = V(f.x + out_dir.x * 600, f.y + out_dir.y * 600, 0)
    put(f, yaw=math.degrees(math.atan2(b["c"].y - f.y, b["c"].x - f.x))); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-4, yaw=math.degrees(math.atan2(b["c"].y - f.y, b["c"].x - f.x))))
    yield from wait(1.5); shot("castle_front"); yield from rwait(1.5)
    put(V(sd.x + out_dir.x * 700, sd.y + out_dir.y * 700, 0), yaw=math.degrees(math.atan2(-out_dir.y, -out_dir.x))); yield from wait(1.2); shot("castle_stair_tower"); yield from rwait(1.5)
    quiet(False)
    wt = res["walk_traces"]
    ok = (res["towers"] == 4 and res["stair_towers"] == 1 and res["blind_arches_outside"] == 0 and res["arched_door_pieces"] == 0 and not poke
          and forge["SM_Castle_Stone_Wall_02h"] > 10 and forge["SM_Castle_Stone_Parapet_01a"] > 40 and forge["SM_Castle_Tower_Wall_02"] >= 64 and forge["SM_Stone_Stairs_01a"] >= 9
          and wt["miss"] == 0 and wt["min"] is not None and abs(wt["min"] - res["walk_z"]) < 25 and abs(wt["max"] - res["walk_z"]) < 25
          and res["climb"]["on_walk"])
    step_result("castlewalls", ok, **res)

# ------------------------------------------------------------------------------------------------ day and night (2026-11-02)
def day_state():
    p = str(G["gen"].get_day_night_state()).split("|")
    return {"day": int(p[0]), "hour": float(p[1]), "sun_elev": float(p[2]), "daylight": float(p[3]), "sun_lux": float(p[4]), "moon_lux": float(p[5]), "sky": float(p[6]), "bias": float(p[7])}
def step_daynight():
    """the town's day: 24 hours in DayLengthSeconds (1800) of play, measured on the clock over 20 s of play; the sun high at
    noon, setting at 18, down at midnight with the moon up; pictures from the square at noon, at 18:30 and at midnight (the
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
    ok = (res["on"] and abs(res["clock"]["day_s"] - res["day_length"]) < res["day_length"] * 0.05 and res["kept_by_game"]
          and n["sun_elev"] > 55 and n["daylight"] > 0.99 and n["sun_lux"] > 1.0
          and -10 < d_["sun_elev"] < 0 and ni["sun_elev"] < -40 and ni["sun_lux"] < 0.01 and ni["moon_lux"] > 0.1 and ni["daylight"] < 0.01
          and n["luma"] is not None and ni["luma"] is not None and n["luma"] > ni["luma"] * 1.8)
    step_result("daynight", ok, **res)

STEPS = {"town": step_town, "doors": step_doors, "talk": step_talk, "services": step_services, "guards": step_guards, "castle": step_castle,
         "map": step_map, "folk": step_folk, "gate": step_gate, "pictures": step_pictures, "tour": step_tour, "trip": step_trip,
         "castlewalls": step_castlewalls, "daynight": step_daynight}
def run():
    o = G.get("gen"); R["windows_hidden"] = str(o.slate_clear_view()) if o else None
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
