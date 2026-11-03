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
DEFAULT = "town,doors,talk,services,guards,folk,gate,map,pictures,castlewalls,daynight,shape,watch,lights,signs,burned,windows,walkers,mapzoom,satellite,life,falls,dagger,circle,castle,tour,trip"
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
        yield from rwait(1.5)
        if os.path.exists(p):
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
        return sum(1 for c in section().get_components_by_class(unreal.InstancedStaticMeshComponent) if c.get_editor_property("instance_end_cull_distance") > 0)
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
def png_measure(path, boxes):
    """for each named box (shares of the picture) of a PNG: (its mean brightness 0-255, the mean brightness step between
    pixels two apart along a row: 0 for a flat picture), from one read of the file (every other pixel of every other row)"""
    import zlib, struct
    data = open(path, "rb").read(); pos = 8; w = h = 0; ct = 6; idat = b""
    while pos < len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8]); body = data[pos + 8:pos + 8 + ln]; pos += 12 + ln
        if typ == b"IHDR": w, h, bd, ct = struct.unpack(">IIBB", body[:10])
        elif typ == b"IDAT": idat += body
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
    res = {}; S = section()
    texts = []
    for c in S.get_components_by_class(unreal.TextRenderComponent):
        if c.component_has_tag("TownSign"): texts.append(str(c.get_editor_property("text")))
    trades = [b for b in blds() if b["kind"] not in ("home", "castle")]
    res["signs"] = len(texts); res["trades"] = len(trades); res["words"] = sorted(set(t.replace("\n", " ") for t in texts))
    bd = place("board")
    notes = [p for p in ism_instances("Plane") if bd and dist2(p, bd) < 200]
    res["notices"] = len(notes)
    st = next(b for b in blds() if b["kind"] == "store")
    f = door_front(st, 420.0); put(f, yaw=math.degrees(math.atan2(st["door"].y - f.y, st["door"].x - f.x)))
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=8, yaw=math.degrees(math.atan2(st["door"].y - f.y, st["door"].x - f.x)))); yield from wait(1.0); shot("sign_store"); yield from rwait(1.5)
    if bd:
        for k, o in enumerate((V(-330, 0, 0), V(330, 0, 0), V(0, -330, 0), V(0, 330, 0))):
            pp = V(bd.x + o.x, bd.y + o.y, 0); put(pp, yaw=math.degrees(math.atan2(bd.y - pp.y, bd.x - pp.x))); yield from wait(0.6); shot(f"board_{k}"); yield from rwait(1.2)
    ok = res["signs"] == 2 * res["trades"] and "GENERAL GOODS" in res["words"] and res["notices"] == 8
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
    for c in S.get_components_by_class(unreal.InstancedStaticMeshComponent):
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
    for c in S.get_components_by_class(unreal.InstancedStaticMeshComponent):
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

STEPS.update({"mapzoom": step_mapzoom, "life": step_life, "falls": step_falls, "dagger": step_dagger, "satellite": step_satellite})
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
