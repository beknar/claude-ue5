"""random_dungeonmagic_level5 test: the Summoner, the armour she finds and wears, up to six items a container
(play-in-editor; 828 with -lv 5 starts it). Steps (plan, comma separated):
  select   (the menu level random_dungeonmagic_level5_select) five heroes, the Summoner last; Left from the first
           shows her and only her figure; Enter opens random_dungeonmagic_level5?Hero=Summoner, where her pawn is
           BP_RDM5_Summoner3Character with her hit points and mana
  loot     (the dungeon) the great hall's containers hold the five sets between them, each once, and no other
           container of the start section or of a generated one holds any; every container of the start section
           holds 1 to 6 items, and over 6000 more containers each count from 1 to 6 comes about a sixth of the time;
           F by a great hall container opens it and gives everything on its list (the FOUND list too), the others
           opened give theirs, she carries exactly what they held, opened again they give nothing
  wear     (the dungeon) with the keys (I, S / W to the set, Enter) each set goes on: one set's meshes on her at a
           time, following her body (leader pose), her armour the set's share; Enter again takes it off; the
           Mage given a set cannot wear it (it was not made for her)
  follow   (the dungeon) in plate armour she runs and casts: skinned on the CPU as drawn, the armour's vertices
           keep their distance to her body's nearest vertices (median, 95th percentile against the same armour
           left in its reference pose on her, which falls behind her limbs)
  damage   (the dungeon) a monster's blows on her without armour and in each set: what reached her is the blow
           less the set's share, and her hit points fell by that
  ui       (the dungeon) a great hall container's FOUND plaque with its first item's picture; the inventory with
           all 33 potions and foods besides the armour scrolls: at the top the armour's pictures are not drawn, at
           the bottom they are, each set's picture; HighResShots of each
Writes SourceArt/random_dungeon_magic5/test_<tag>.json and logs "RDM5TEST done | <tag> | ok / FAILED | ...". Args: plan tag"""
import unreal, sys, json, math, os, time
__keep__ = True
TAG = sys.argv[2] if len(sys.argv) > 2 else "t"
V = unreal.Vector; GS = unreal.GameplayStatics
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
OUT = os.path.join(SA, "random_dungeon_magic5")
HJ = json.load(open(os.path.join(OUT, "summoner_hero.json"), encoding="utf-8"))
AJ = json.load(open(os.path.join(SA, "summoner3", "armour.json"), encoding="utf-8"))
SETS = [s["title"] for s in AJ["sets"]]
LEVEL = "random_dungeonmagic_level5"
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
G = {"w": UES.get_game_world()}
assert G["w"] is not None, "PIE is not running"
PLAN = [s.strip() for s in (sys.argv[1] if len(sys.argv) > 1 else "loot,wear,follow,damage,ui").split(",") if s.strip()]
R = {"tag": TAG, "plan": PLAN, "level": G["w"].get_path_name().split(".")[-1], "steps": []}
def refresh():
    w = UES.get_game_world(); G["w"] = w
    if w is None: return False
    gens = GS.get_all_actors_of_class(w, unreal.RDDungeonGenerator); G["gen"] = gens[0] if gens else None
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
    t0 = time.time()
    while time.time() - t0 < sec: yield
def press(name, hold=0.12, sim=None):
    sim = sim or (lambda k, d: cb().simulate_key(k, d))
    sim(key(name), True); yield from rwait(hold); sim(key(name), False); yield from rwait(0.1)
def step_result(name, ok, **kw):
    R["steps"].append({"step": name, "ok": bool(ok), **kw})
    unreal.log(f"RDM5TEST step {name}: {'ok' if ok else 'FAILED'} {json.dumps(kw, ensure_ascii=False)[:1800]}")
def alive(m):
    try: return m is not None and unreal.SystemLibrary.is_valid(m) and not m.is_dead()
    except Exception: return False
def start_monsters(): return [m for m in G["gen"].get_monsters() if alive(m) and m.get_editor_property("section").get_editor_property("coord") == unreal.IntPoint(0, 0)]
def clear(a, b, ignore):
    h = unreal.SystemLibrary.line_trace_single(G["w"], a, b, unreal.TraceTypeQuery.ECC_VISIBILITY, False, ignore, unreal.DrawDebugTrace.NONE, True)
    return h is None or not h.to_tuple()[0]
def stand_off(m, gap):
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
    g = G["gen"]
    if on:
        if "aggro" not in G: G["aggro"] = (g.get_editor_property("aggro_distance"), g.get_editor_property("lose_distance"))
        g.set_editor_property("aggro_distance", 0.0); g.set_editor_property("lose_distance", 1.0)
    elif "aggro" in G: a_, l_ = G.pop("aggro"); g.set_editor_property("aggro_distance", a_); g.set_editor_property("lose_distance", l_)
def restart():
    """the dungeon back to its start (fixed seed), her as the Summoner with nothing found"""
    G["gen"].restart_play(0); yield from wait(0.8); refresh()
    c = cb(); c.set_scripted_only(False); return c
def hud_art():
    h = G["pc"].get_hud() if G.get("pc") else None
    return sorted(str(n) for n in h.get_art_drawn()) if h else []
def shot(name):
    unreal.SystemLibrary.execute_console_command(G["w"], f"HighResShot 1920x1080 filename=rdm5_{TAG}_{name}")
    R.setdefault("shots", []).append(f"rdm5_{TAG}_{name}.png")
def lines(c): return [str(l) for l in c.get_inventory_lines()]
def cursor_to(c, i):
    while c.get_inventory_cursor() < i: yield from press("S")
    while c.get_inventory_cursor() > i: yield from press("W")

# ------------------------------------------------------------------------------------------------ the menu
def step_select():
    s = G["sel"]; assert s, "open random_dungeonmagic_level5_select for the select step"
    sim = lambda k, d: G["sel"].simulate_key(k, d)
    yield from wait(0.6)
    names = [str(h.name) for h in s.heroes]
    first = str(s.get_hero_name())
    yield from press("Left", sim=sim); yield from wait(0.2)
    shown = [s.is_figure_shown(i) for i in range(len(names))]
    pick = str(s.get_hero_name()); target = str(s.target_level)
    shot("menu_summoner"); yield from rwait(1.5)
    sim(key("Enter"), True)
    opened = ""; G["traveling"] = True; t0 = time.time(); arrived = False
    while time.time() - t0 < 60:
        yield
        try:
            if unreal.SystemLibrary.is_valid(s) and s.opened: opened = s.opened
        except Exception: pass
        w = UES.get_game_world()
        if w is not None and w.get_path_name().endswith(LEVEL) and refresh() and G["gen"] is not None and G["pawn"] is not None and G["gen"].get_player_combat():
            arrived = True; break
    G["traveling"] = False
    if arrived: yield from wait(0.5)
    c = cb() if arrived else None
    hero = str(G["gen"].current_hero) if arrived else None
    pawn = G["pawn"].get_class().get_name() if arrived else None
    want_pawn = os.path.basename(HJ["pawn"]) + "_C"
    stats = [c.get_max_health(), c.get_max_mana()] if c else None
    ok = (len(names) == 5 and names[-1] == "Summoner" and first == "Warrior" and pick == "Summoner" and shown == [False] * 4 + [True]
          and target.endswith(LEVEL) and opened.endswith(LEVEL + "?Hero=Summoner") and arrived and hero == "Summoner" and pawn == want_pawn
          and stats == [float(HJ["health"]), float(HJ["mana"])])
    step_result("select", ok, heroes=names, first=first, picked=pick, seen=shown, target=target, opened=opened, dungeon_hero=hero, pawn=pawn,
                want_pawn=want_pawn, health_mana=stats)

# ------------------------------------------------------------------------------------------------ the loot
def step_loot():
    g = G["gen"]; c = yield from restart()
    S0 = unreal.IntPoint(0, 0)
    s0 = g.get_section(S0); n = s0.get_num_containers(); hall = list(g.get_start_room_containers())
    lists = {i: [str(x) for x in g.loot_list_of(S0, i)] for i in range(n)}
    in_hall = [x for i in hall for x in lists[i] if x in SETS]
    elsewhere = [(i, x) for i in range(n) if i not in hall for x in lists[i] if x in SETS]
    lens_start = sorted({len(v) for v in lists.values()})
    # many more containers: the counts 1..6 about a sixth each, never armour
    N = 6000; cnt = {}; arm_more = 0
    for i in range(N):
        l_ = [str(x) for x in g.loot_list_of(S0, 100000 + i)]
        cnt[len(l_)] = cnt.get(len(l_), 0) + 1; arm_more += sum(1 for x in l_ if x in SETS)
    p6 = 1.0 / 6.0; sd = math.sqrt(p6 * (1 - p6) / N)
    worst = max(abs(cnt.get(k, 0) / N - p6) / sd for k in range(1, 7))
    # F by a great hall container
    p = G["pawn"]; fpress = None
    for i in hall:
        cl = s0.get_container_location(i)
        for k in range(16):
            a = k * math.pi / 8; q = V(cl.x + math.cos(a) * 130, cl.y + math.sin(a) * 130, 100)
            if s0.room_at(q) < 0: continue
            d = g.describe_nearest(q, 260.0) or ""
            if not d.startswith("open") or "door" in d: continue
            p.set_actor_location(q, False, True); yield from wait(0.3)
            if s0.get_container_open_alpha(i) > 0.0: break
            f0 = g.items_found; yield from press("F"); yield from wait(0.5)
            # (F opens the one it names: which one it was is the one now open)
            opened = [j for j in hall if s0.get_container_open_alpha(j) > 0.0]
            if opened:
                j = opened[0]
                fpress = {"container": j, "found": g.items_found - f0, "list": lists[j], "found_list": [str(x) for x in g.last_found_list]}
            break
        if fpress: break
    # the rest of the hall, and every other container of the start section
    # (a wardrobe's two doors are one container, the lower index's: opening one opens both, and the other is skipped)
    bad = []; opened_lists = [fpress["list"]] if fpress else []
    for i in range(n):
        if s0.is_target_open(False, i): continue
        f0 = g.items_found; s0.toggle_container(i)
        if i in hall or i % 10 == 0: yield
        got = g.items_found - f0; fl = [str(x) for x in g.last_found_list]
        opened_lists.append(fl if got else [])
        if got != len(lists[i]) or fl != lists[i]: bad.append({"container": i, "found": got, "found_list": fl, "list": lists[i]})
    want = {}
    for v in opened_lists:
        for x in v: want[x] = want.get(x, 0) + 1
    ls = lines(c)
    have = {l.split("|")[1]: int(l.split("|")[2]) for l in ls if l.startswith("item|")}
    have.update({l.split("|")[1]: 1 for l in ls if l.startswith("armour|")})
    # opened again: nothing more
    yield from wait(1.0); i0 = hall[0]; f0 = g.items_found
    s0.toggle_container(i0); yield from wait(1.0); s0.toggle_container(i0); yield from wait(0.5)
    again = g.items_found - f0
    # a section generated in play: no armour
    g.generate_section_now(unreal.IntPoint(1, 0)); t0 = time.time()
    while time.time() - t0 < 30:
        s1 = g.get_section(unreal.IntPoint(1, 0))
        if s1 and not s1.is_building(): break
        yield
    s1 = g.get_section(unreal.IntPoint(1, 0)); n1 = s1.get_num_containers() if s1 else 0
    gen_armour = sum(1 for i in range(n1) for x in g.loot_list_of(unreal.IntPoint(1, 0), i) if str(x) in SETS)
    ok = (len(hall) > 0 and sorted(in_hall) == sorted(SETS) and not elsewhere and lens_start[0] >= 1 and lens_start[-1] <= 6
          and min(cnt) >= 1 and max(cnt) <= 6 and len(cnt) == 6 and worst < 4.5 and arm_more == 0
          and fpress is not None and fpress["found"] == len(fpress["list"]) and fpress["found_list"] == fpress["list"]
          and not bad and have == want and again == 0 and n1 > 0 and gen_armour == 0)
    step_result("loot", ok, containers=n, great_hall=hall, hall_lists={str(i): lists[i] for i in hall}, armour_elsewhere=elsewhere,
                start_counts=lens_start, more=N, counts={str(k): cnt[k] for k in sorted(cnt)}, worst_sd=round(worst, 2), armour_in_more=arm_more,
                by_f=fpress, wrong=bad[:5], wrong_count=len(bad), items_kinds=len(want), carried_matches=have == want, opened_again_gave=again,
                generated_containers=n1, generated_armour=gen_armour)

# ------------------------------------------------------------------------------------------------ wearing
def step_wear():
    g = G["gen"]; c = yield from restart(); quiet(True)
    for t in SETS: c.add_item(t, 1)
    body = G["pawn"].get_component_by_class(unreal.SkeletalMeshComponent)
    amount = {str(it.name): it.amount for it in g.get_editor_property("items") if it.kind == unreal.RDItemKind.ARMOUR}
    want_mesh = {s["title"]: "SK_S3_" + s["key"] for s in AJ["sets"]}
    out = []
    yield from press("I")
    for t in SETS:
        ls = lines(c); i = next(k for k, l in enumerate(ls) if l.startswith("armour|" + t + "|"))
        yield from cursor_to(c, i); ch0 = c.armour_changes
        yield from press("Enter")
        ms = list(c.get_armour_meshes())
        e = {"set": t, "cursor": c.get_inventory_cursor(), "worn": str(c.get_worn_armour()), "armour": round(c.get_armour(), 3), "want": amount.get(t),
             "meshes": [m.skeletal_mesh_asset.get_name() if m.skeletal_mesh_asset else None for m in ms],
             "follows_her": all(m.leader_pose_component == body and m.get_attach_parent() == body for m in ms), "message": str(c.message),
             "line": next(l for l in lines(c) if l.startswith("armour|" + t + "|"))}
        e["ok"] = (e["cursor"] == i and e["worn"] == t and abs(e["armour"] - (amount.get(t) or -1)) < 1e-4 and e["meshes"] == [want_mesh[t]]
                   and e["follows_her"] and e["line"].endswith("|1") and c.armour_changes == ch0 + 1)
        out.append(e)
    # Enter again on the worn set: off
    t = SETS[-1]; yield from press("Enter")
    off = {"worn": str(c.get_worn_armour()), "armour": c.get_armour(), "meshes": len(c.get_armour_meshes()), "message": str(c.message)}
    yield from press("I")
    # the Mage cannot wear it
    ok_sw = g.switch_hero("Mage"); yield from wait(0.6); refresh(); m = cb(); m.add_item(SETS[0], 1)
    mage = {"switched": ok_sw, "wore": m.wear_armour(SETS[0]), "worn": str(m.get_worn_armour()), "meshes": len(m.get_armour_meshes()), "message": str(m.message)}
    g.switch_hero("Summoner"); yield from wait(0.6); refresh(); quiet(False)
    ok = (all(e["ok"] for e in out) and off["worn"] == "None" and off["armour"] == 0.0 and off["meshes"] == 0 and "take off" in off["message"]
          and mage["switched"] and not mage["wore"] and mage["worn"] == "None" and mage["meshes"] == 0 and "not made for" in mage["message"])
    step_result("wear", ok, sets=out, taken_off=off, mage=mage)

def step_follow():
    g = G["gen"]; c = yield from restart(); quiet(True)
    c.add_item(SETS[0], 1); c.wear_armour(SETS[0])
    samples = []
    def measure(what):
        r = list(c.measure_armour_follow(600))
        samples.append({"when": what, "n": int(r[0]) if r else 0, "skin_median": round(r[1], 2) if r else None, "skin_p95": round(r[2], 2) if r else None,
                        "bone_n": int(r[3]) if r else 0, "bone_p95": round(r[4], 3) if r else None, "bone_max": round(r[5], 3) if r else None,
                        "bone_p95_left_in_rest_pose": round(r[6], 2) if r else None})
    yield from wait(0.3); measure("standing")
    sim = lambda k, d: c.simulate_key(k, d)
    sim(key("LeftShift"), True); sim(key("W"), True)
    for k in range(6):
        yield from wait(0.25); measure(f"running {k}")
    sim(key("W"), False); sim(key("LeftShift"), False)
    yield from wait(0.3)
    sim(key("LeftMouseButton"), True); yield from wait(0.15); sim(key("LeftMouseButton"), False)
    for k in range(4):
        yield from wait(0.15); measure(f"casting {k}")
    shot("follow"); yield from rwait(1.5)
    quiet(False)
    # (on her bones within a centimetre, everywhere: a broken bone map or a mesh left in its pose shows by metres; measured
    # 0.09 cm standing and up to 0.48 cm running at 3.4 m/s, growing with her speed; her skin's median within half a
    # centimetre: the armour stays on her)
    moving = [s for s in samples if s["when"] != "standing" and s["n"]]
    ok = (len(moving) == 10 and all(s["bone_n"] > 50 and s["bone_max"] < 1.0 and s["skin_median"] < 0.5 for s in samples)
          and max(s["bone_p95_left_in_rest_pose"] for s in moving) > 10.0)
    step_result("follow", ok, samples=samples)

def step_damage():
    g = G["gen"]; res = []
    for t in [None] + SETS:
        c = yield from restart()
        if t: c.add_item(t, 1); c.wear_armour(t)
        ms = start_monsters(); p = G["pawn"]
        ms.sort(key=lambda m: (m.get_actor_location() - p.get_actor_location()).length())
        for m in ms:
            if stand_off(m, 150): break
        else:
            res.append({"set": t, "error": "no place by a monster"}); continue
        c.set_health(c.get_max_health()); h0, n0 = c.get_health(), c.hits_taken; t0 = now()
        while now() - t0 < 10.0 and c.hits_taken == n0: yield
        yield from wait(0.05)
        e = {"set": t, "armour": round(c.get_armour(), 3), "hits": c.hits_taken - n0, "blow": round(c.last_blow_before, 3), "reached_her": round(c.last_blow_taken, 3),
             "hp_fell": round(h0 - c.get_health(), 3), "monster": m.get_name()}
        e["ok"] = (e["hits"] == 1 and e["blow"] > 0 and abs(e["reached_her"] - e["blow"] * (1 - e["armour"])) < 0.01 and abs(e["hp_fell"] - e["reached_her"]) < 0.01
                   and (t is None) == (e["armour"] == 0.0))
        res.append(e)
    ok = len(res) == 6 and all(e.get("ok") for e in res)
    step_result("damage", ok, blows=res)

def step_ui():
    g = G["gen"]; c = yield from restart(); quiet(True)
    S0 = unreal.IntPoint(0, 0); s0 = g.get_section(S0); hall = list(g.get_start_room_containers())
    icons = {str(i.name): str(i.icon) for i in g.get_editor_property("items")}
    ua = [str(k) for k in g.get_editor_property("ui_art").keys()]
    arm_icons = [icons.get(t) for t in SETS]
    # FOUND: the hall's longest list
    i = max(hall, key=lambda j: len(g.loot_list_of(S0, j)))
    first = str(g.loot_list_of(S0, i)[0]); n_in = len(g.loot_list_of(S0, i))
    s0.toggle_container(i); yield from wait(0.6)
    fd = hud_art(); shot("found"); yield from rwait(1.5)
    found_ok = "banner" in fd and icons.get(first) in fd
    # the inventory with everything: it scrolls (once the FOUND plaque is gone: its picture would count)
    t0 = now()
    while now() - t0 < 12.0 and "banner" in hud_art(): yield
    gone = "banner" not in hud_art()
    for it in g.get_editor_property("items"): c.add_item(it.name, 1)
    yield from press("I"); yield from rwait(0.4)
    top = hud_art(); shot("inventory_top"); yield from rwait(1.5)
    ls = lines(c); yield from cursor_to(c, len(ls) - 1); yield from rwait(0.3)
    bottom = hud_art(); shot("inventory_bottom"); yield from rwait(1.5)
    yield from press("I"); quiet(False)
    ok = (all(a in ua for a in arm_icons) and found_ok and gone and not (set(arm_icons) & set(top)) and set(arm_icons) <= set(bottom)
          and "panel_wide" in bottom)
    step_result("ui", ok, armour_icons=arm_icons, icons_imported=[a in ua for a in arm_icons], found_container=i, found_items=n_in, found_first=first,
                found_drawn=fd, plaque_gone=gone, lines=len(ls), top_drawn=top, bottom_drawn=bottom)

STEPS = {"select": step_select, "loot": step_loot, "wear": step_wear, "follow": step_follow, "damage": step_damage, "ui": step_ui}
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
    os.makedirs(OUT, exist_ok=True); json.dump(R, open(os.path.join(OUT, f"test_{TAG}.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    ok = not R.get("error") and len(R["steps"]) == len(PLAN) and all(s["ok"] for s in R["steps"])
    unreal.log(f"RDM5TEST done | {TAG} | {'ok' if ok else 'FAILED'} | " + " | ".join(f"{s['step']} {'ok' if s['ok'] else 'FAILED'}" for s in R["steps"]) + f" | {R.get('error') or ''}")
    G.clear()
def tick(dt):
    try:
        if UES.get_game_world() is None and not G.get("traveling"): finish("PIE ended"); return
        next(G["gen_"])
    except StopIteration: finish()
    except Exception as e:
        import traceback
        unreal.log_error("RDM5TEST error: " + str(e) + traceback.format_exc()); finish(str(e))
G["gen_"] = run()
G["h"] = unreal.register_slate_post_tick_callback(tick)
print("rdm5 test armed:", PLAN, TAG)
