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
           Mage given a set cannot wear it (she wears no armour)
  heroarmour (the dungeon) each of the four heroes given all five sets: the weights her card allows go on (856: the
           Warrior light, medium and heavy, the Warlock light and medium, the Rogue light, the Mage none), with the fit
           made for her (SK_<her mesh>_<set>) on her body as leader; the others are refused and the message says why (the
           weight, or that she wears no armour); in her heaviest set she runs and the armour stays on her bones (as follow);
           a picture of each in it, from in front
  follow   (the dungeon) in plate armour she runs and casts: skinned on the CPU as drawn, the armour's vertices
           keep their distance to her body's nearest vertices (median, 95th percentile against the same armour
           left in its reference pose on her, which falls behind her limbs)
  damage   (the dungeon) a monster's blows on her without armour and in each set: what reached her is the blow
           less the set's share, and her hit points fell by that
  ui       (the dungeon) a great hall container's FOUND plaque with its first item's picture; the inventory with
           all 33 potions and foods besides the armour scrolls: at the top the armour's pictures are not drawn, at
           the bottom they are, each set's picture; HighResShots of each
  tiers    (the dungeon) the five tiers (855: MaxTier 5): a section's tier is its ring plus one (8, 16, 24, 32 sections
           round the start); at the start tiers 1 and 2 are open. One set of tier 2 cleared as she would clear it: walked
           into room by room (explored only once she is in each), every chest and trunk opened, every monster killed: it
           counts as cleared ("SET CLEARED"). Tier 3 is not generated past it; its hallways into tier 3 are sealed: a
           capsule is stopped at the grating and she, walking at it for 2.5 s, stays on her side of the border; the seal
           says what opens it. The set dropped and generated again has no monsters (her kills stay killed) and is still
           cleared. The other seven sets cleared (the debug clear): "TIER 3 IS OPEN", the gratings go, walking on she gets
           tier 3 generated. Tiers 3 and 4 cleared: tier 5 opens; a tier 5 section's hallways out of the dungeon are
           walled (they lead to tier 6, which is never allowed)
  tierloot the containers of each tier (2500 each, any section of it): a weapon only in its tiers (the table's), every
           weapon of a tier found, their share of what is found as their weights say (within 4.5 sd)
  weapons  each hero given all 29 weapons: the ones her card allows join her weapons (Warrior, Warlock: all; Rogue: short
           blades and ranged), the others stay in her pack as weapons she cannot wield (the Mage and the Summoner: all,
           and using one says she cannot); each one drawn: its mesh in her hand with its handle's grip point within 7 cm
           of her palm, its damage (8 + 3 x rating, her bonus), its attack's length (the table's speed: 1.6 - (speed - 1)
           x 1.05 / 9 s); a two-handed sword at the blow has her left palm on the hilt below the right; a blow that lands
           takes 1 off its durability, and at 0 it breaks: gone from her weapons, her first one drawn, "broke"; pictures
           from in front of her (the face camera, her alone) at the blow
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
    # (855's weapons: the Summoner cannot wield them, so she carries them as items: "carried|<name>|<count>")
    have.update({l.split("|")[1]: int(l.split("|")[2]) for l in ls if l.startswith("carried|")})
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
          and mage["switched"] and not mage["wore"] and mage["worn"] == "None" and mage["meshes"] == 0 and "wears no armour" in mage["message"])
    step_result("wear", ok, sets=out, taken_off=off, mage=mage)

HERO_MESH = {"Warrior": "Fem5", "Mage": "Caster", "Warlock": "DarkCaster", "Rogue": "Rogue"}
def step_heroarmour():
    """each hero tries on all five sets: the weights she wears go on with her own fit, the others are refused with why;
    her heaviest set stays on her bones as she runs"""
    g = G["gen"]; HJ4 = {h["name"]: h for h in json.load(open(os.path.join(SA, "random_dungeon_magic4", "heroes.json"), encoding="utf-8"))["heroes"]}
    weight = {s["title"]: s["weight"] for s in AJ["sets"]}; skey = {s["title"]: s["key"] for s in AJ["sets"]}
    order = {"light": 0, "medium": 1, "heavy": 2}; res = {}
    for h in ("Warrior", "Mage", "Warlock", "Rogue"):
        c = yield from restart(); quiet(True)
        ok_sw = g.switch_hero(h); yield from wait(0.6); refresh(); c = cb(); quiet(True)
        body = G["pawn"].get_component_by_class(unreal.SkeletalMeshComponent)
        for t in SETS: c.add_item(t, 1)
        wears = HJ4[h]["wears"]; tries = []
        for t in SETS:
            if str(c.get_worn_armour()) != "None": c.wear_armour(str(c.get_worn_armour()))      # (off first: a wrong one must not stay on)
            wore = bool(c.wear_armour(t)); ms = list(c.get_armour_meshes())
            e = {"set": t, "weight": weight[t], "wore": wore, "worn": str(c.get_worn_armour()), "message": str(c.message),
                 "meshes": [m.skeletal_mesh_asset.get_name() if m.skeletal_mesh_asset else None for m in ms],
                 "follows_her": all(m.leader_pose_component == body and m.get_attach_parent() == body for m in ms)}
            allowed = weight[t] in wears
            e["ok"] = (wore and e["worn"] == t and e["meshes"] == ["SK_%s_%s" % (HERO_MESH[h], skey[t])] and e["follows_her"]) if allowed else \
                      (not wore and e["worn"] == "None" and not e["meshes"]
                       and (("wears no armour" in e["message"]) if not wears else ("wears only" in e["message"] and weight[t] in e["message"])))
            tries.append(e)
        # her heaviest set, running: on her bones within a centimetre
        heavy = max((t for t in SETS if weight[t] in wears), key=lambda t: order[weight[t]], default=None)
        follow = None
        if heavy:
            if str(c.get_worn_armour()) != heavy: c.wear_armour(heavy)
            yield from wait(0.3)
            sim = lambda k, d: c.simulate_key(k, d); sim(key("LeftShift"), True); sim(key("W"), True)
            rs = []
            for k in range(4):
                yield from wait(0.25); r = list(c.measure_armour_follow(600)); rs.append(r)
            sim(key("W"), False); sim(key("LeftShift"), False); yield from wait(0.4)
            follow = {"set": heavy, "bone_max": round(max(r[5] for r in rs), 3) if all(rs) else None, "skin_median": round(max(r[1] for r in rs), 2) if all(rs) else None,
                      "bone_n": min(int(r[3]) for r in rs) if all(rs) else 0}
            # a picture of her in it, from in front
            p = G["pawn"]; l = p.get_actor_location(); yaw = p.get_actor_rotation().yaw
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=yaw + 180.0)); yield from wait(0.5)
            shot("armour_" + h); yield from rwait(1.5)
        res[h] = {"switched": bool(ok_sw), "wears": wears, "tries": tries, "follow": follow,
                  "ok": bool(ok_sw) and all(e["ok"] for e in tries) and (follow is None or (follow["bone_n"] > 50 and follow["bone_max"] < 1.0 and follow["skin_median"] < 0.5))
                        and (heavy is not None) == bool(wears)}
    g.switch_hero("Summoner"); yield from wait(0.6); refresh(); quiet(False)
    step_result("heroarmour", all(v["ok"] for v in res.values()), heroes=res)

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
        # (a second blow may land before the reading: her hit points then fell by two of them)
        e["ok"] = (e["hits"] in (1, 2) and e["blow"] > 0 and abs(e["reached_her"] - e["blow"] * (1 - e["armour"])) < 0.01 and abs(e["hp_fell"] - e["reached_her"] * e["hits"]) < 0.01
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
    # (down to the last armour row: with 855's weapons the list ends with the ones she cannot wield)
    ls = lines(c); yield from cursor_to(c, max(i for i, l in enumerate(ls) if l.startswith("armour|"))); yield from rwait(0.3)
    bottom = hud_art(); shot("inventory_bottom"); yield from rwait(1.5)
    yield from press("I"); quiet(False)
    ok = (all(a in ua for a in arm_icons) and found_ok and gone and not (set(arm_icons) & set(top)) and set(arm_icons) <= set(bottom)
          and "panel_wide" in bottom)
    step_result("ui", ok, armour_icons=arm_icons, icons_imported=[a in ua for a in arm_icons], found_container=i, found_items=n_in, found_first=first,
                found_drawn=fd, plaque_gone=gone, lines=len(ls), top_drawn=top, bottom_drawn=bottom)

# ------------------------------------------------------------------------------------------------ the weapons table, the tiers
W5 = json.load(open(os.path.join(OUT, "weapons_table.json"), encoding="utf-8"))
W5F = json.load(open(os.path.join(OUT, "weapon_frames.json"), encoding="utf-8"))["weapons"]
wkey = lambda name: "".join(ch for ch in name.title() if ch.isalnum())
def cycle(speed): return 1.6 - (speed - 1) * 1.05 / 9.0
I2 = unreal.IntPoint
def out_tuple(r):
    """(a UFUNCTION's return value, its out parameter) as Python gives them: a bool function that returns false gives None"""
    if r is None: return (False, None)
    return r if isinstance(r, tuple) else (True, r)
def progress(S):
    ok, p = out_tuple(G["gen"].get_section_progress(S))
    if not ok: return None
    return {"tier": p.tier, "rooms": p.rooms, "explored": p.rooms_explored, "chests": len(p.chests), "looted": p.chests_looted, "monsters": p.monsters,
            "killed": len(p.killed), "cleared": p.cleared}
def built(S, sec=40.0):
    t0 = time.time()
    while time.time() - t0 < sec:
        s = G["gen"].get_section(S)
        if s and not s.is_building(): return s
        yield
    return None
def make_and_clear(S):
    """a section generated now and cleared at once (the debug clear: its rooms explored, its chests looted, its monsters gone)"""
    g = G["gen"]
    if not g.is_section_generated(S): g.generate_section_now(S)
    yield from built(S)                     # (one generated as she walked by may still be being built)
    ok = g.debug_clear_section(S); yield
    return ok
def seals(s):
    pts, kinds = s.get_seal_points()          # (the points returned, the kinds as the out parameter)
    return list(zip(list(pts), list(kinds)))
def seal_out(s, b):
    """the way out of section s through the border point b (the axis it is on)"""
    mn = s.get_section_min(); size = G["gen"].tile_size * G["gen"].section_tiles
    cx, cy = mn.x + size / 2, mn.y + size / 2; dx, dy = b.x - cx, b.y - cy
    return V(1 if dx > 0 else -1, 0, 0) if abs(dx) > abs(dy) else V(0, 1 if dy > 0 else -1, 0)

def step_tiers():
    g = G["gen"]; c = yield from restart(); quiet(True); p = G["pawn"]
    res = {"max_tier": g.max_tier, "open_at_start": g.get_open_tiers(),
           "tiers_of": [g.tier_of(I2(*xy)) for xy in ((0, 0), (1, 0), (-1, 1), (2, -1), (3, 3), (4, 0), (5, 0))],
           "sizes": [g.tier_size(t) for t in range(1, 6)],
           "allowed_at_start": [g.is_section_allowed(I2(*xy)) for xy in ((1, 0), (1, 1), (2, 0), (4, 0), (5, 0))]}
    # one set of tier 2 cleared as she would: every room walked into, every chest and trunk opened, every monster killed
    S = I2(1, 0); g.generate_section_now(S); s = yield from built(S)
    before = progress(S)
    rooms = [i for i in range(s.get_num_rooms()) if s.get_room_kind(i) != "Hallway junction"]
    c.set_health(c.get_max_health())
    for i in rooms:
        rc = s.get_room_center(i); p.set_actor_location(V(rc.x, rc.y, 100.0), False, True); yield from wait(0.06)
    after_rooms = progress(S)
    for i in range(s.get_num_containers()):
        if s.get_container_kind(i) in ("chest", "trunk") and not s.is_container_looted(i): s.toggle_container(i)
    yield from wait(0.1); after_chests = progress(S)
    kills0 = g.monsters_killed
    for m in list(s.spawned_monsters):
        if alive(m): m.apply_damage(1.0e6, p)
    yield from wait(0.3); after = progress(S)
    res.update({"set_before": before, "after_rooms": after_rooms, "after_chests": after_chests, "after_kills": after, "monsters_killed": g.monsters_killed - kills0,
                "notice": str(g.tier_notice), "tier2_cleared": g.get_tier_cleared(2)})
    # tier 3 stays shut: nothing generated past her set, its hallways sealed; the seal stops a body and stops her walking
    near = [(b, k) for b, k in seals(s)]
    res["seals_of_set"] = {"grating": sum(1 for _, k in near if k == 1), "wall": sum(1 for _, k in near if k == 2),
                           "into": sorted({str(g.tier_of(g.world_to_section(b + seal_out(s, b) * 200.0))) for b, _ in near})}
    res["tier3_generated"] = g.is_section_generated(I2(2, 0))
    blocked = walked_out = None
    if near:
        b, _ = next(((b, k) for b, k in near if seal_out(s, b).x > 0), near[0]); out = seal_out(s, b)
        a0 = V(b.x - out.x * 150, b.y - out.y * 150, 110.0); a1 = V(b.x + out.x * 150, b.y + out.y * 150, 110.0)
        h = unreal.SystemLibrary.capsule_trace_single(G["w"], a0, a1, 34.0, 80.0, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [p], unreal.DrawDebugTrace.NONE, True)
        hit = h.to_tuple() if h else None
        blocked = {"hit": bool(hit and hit[0]), "at_cm_from_border": round((hit[4].x - b.x) * out.x + (hit[4].y - b.y) * out.y, 1) if hit and hit[0] else None}
        p.set_actor_location(V(b.x - out.x * 260, b.y - out.y * 260, 100.0), False, True)
        yaw = math.degrees(math.atan2(out.y, out.x)); p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw), True); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-10, yaw=yaw))
        yield from wait(0.2)
        sim = lambda k, d: c.simulate_key(k, d)
        sim(key("W"), True); yield from wait(2.5); sim(key("W"), False)
        q = p.get_actor_location(); walked_out = round((q.x - b.x) * out.x + (q.y - b.y) * out.y, 1)
        shot("tier_seal"); yield from rwait(1.5)
        res["seal_prompt"] = str(g.describe_seal_near(q, 450.0))
    res.update({"seal_blocks_a_body": blocked, "walked_past_the_border_cm": walked_out})
    # the set generated again (dropped and made anew): her kills stay killed, it stays cleared
    p.set_actor_location(V(0, 0, 100.0), False, True); yield from wait(0.3)
    g.reload_section(S); s = yield from built(S)
    res["regenerated"] = {"monsters": len(s.spawned_monsters) if s else None, "progress": progress(S)}
    # the other seven sets of tier 2: tier 3 opens, the seals toward it go; walking on, tier 3 is generated
    for xy in ((1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)):
        yield from make_and_clear(I2(*xy))
    res["after_tier2"] = {"cleared": g.get_tier_cleared(2), "open": g.get_open_tiers(), "notice": str(g.tier_notice), "tier3_allowed": g.is_section_allowed(I2(2, 0))}
    p.set_actor_location(V(s.get_section_min().x + 12000, s.get_section_min().y + 12600, 100.0), False, True); yield from wait(0.5)
    s = G["gen"].get_section(S) or (yield from built(S))
    res["seals_of_set_after"] = sum(1 for _, k in seals(s) if k == 1) if s else None
    t0 = time.time(); p.set_actor_location(V(s.get_section_min().x + 24500, s.get_section_min().y + 12600, 100.0), False, True)
    while time.time() - t0 < 40 and not g.is_section_generated(I2(2, 0)): yield
    res["tier3_generated_when_near"] = g.is_section_generated(I2(2, 0))
    # tiers 3 and 4 cleared (the debug clear): tier 5 opens, and nothing past it is ever made
    for t in (3, 4):
        r = t - 1; failed = []
        for x in range(-r, r + 1):
            for y in range(-r, r + 1):
                if max(abs(x), abs(y)) != r: continue
                ok_ = yield from make_and_clear(I2(x, y))
                if not ok_: failed.append({"set": [x, y], "generated": g.is_section_generated(I2(x, y)), "progress": progress(I2(x, y))})
        res[f"after_tier{t}"] = {"cleared": g.get_tier_cleared(t), "open": g.get_open_tiers(), "notice": str(g.tier_notice), "not_cleared": failed}
    g.generate_section_now(I2(4, 0)); s4 = yield from built(I2(4, 0))
    sl = seals(s4) if s4 else []
    res["tier5_section"] = {"walls": sum(1 for _, k in sl if k == 2), "gratings": sum(1 for _, k in sl if k == 1),
                            "walls_lead_to_tier": sorted({g.tier_of(g.world_to_section(b + seal_out(s4, b) * 200.0)) for b, k in sl if k == 2}),
                            "tier6_allowed": g.is_section_allowed(I2(5, 0)), "seal_kind_east": g.get_seal_kind(I2(4, 0), I2(5, 0))}
    p.set_actor_location(V(0, 0, 100.0), False, True); quiet(False)
    a = res["after_kills"]; ar = res["after_rooms"]
    ok = (res["max_tier"] == 5 and res["open_at_start"] == 2 and res["tiers_of"] == [1, 2, 2, 3, 4, 5, 6] and res["sizes"] == [1, 8, 16, 24, 32]
          and res["allowed_at_start"] == [True, True, False, False, False]
          and res["set_before"] and not res["set_before"]["cleared"] and ar["explored"] == ar["rooms"] and not ar["cleared"]
          and a["cleared"] and a["looted"] == a["chests"] and a["killed"] == a["monsters"] and res["monsters_killed"] == a["monsters"] and "SET CLEARED" in res["notice"]
          and res["seals_of_set"]["grating"] > 0 and res["seals_of_set"]["into"] == ["3"] and not res["tier3_generated"]
          and blocked and blocked["hit"] and walked_out is not None and walked_out < 0 and "Sealed" in res.get("seal_prompt", "")
          and res["regenerated"]["monsters"] == 0 and res["regenerated"]["progress"]["cleared"]
          and res["after_tier2"]["cleared"] == 8 and res["after_tier2"]["open"] == 3 and res["after_tier2"]["notice"] == "TIER 3 IS OPEN" and res["after_tier2"]["tier3_allowed"]
          and res["seals_of_set_after"] == 0 and res["tier3_generated_when_near"]
          and res["after_tier3"]["cleared"] == 16 and res["after_tier3"]["open"] == 4 and res["after_tier4"]["cleared"] == 24 and res["after_tier4"]["open"] == 5
          and res["tier5_section"]["walls"] > 0 and res["tier5_section"]["walls_lead_to_tier"] == [6] and not res["tier5_section"]["tier6_allowed"]
          and res["tier5_section"]["seal_kind_east"] == 2)
    step_result("tiers", ok, **res)

def step_tierloot():
    """what each tier's containers hold: a weapon only in the tiers of its rooms; potions and food everywhere; the
    weapons' share as their weights say"""
    g = G["gen"]; c = yield from restart()
    wt = {w["name"]: set(w["tiers"]) for w in W5["weapons"]}
    items = [it for it in g.get_editor_property("items") if it.weight > 0]
    res = {}; ok = True; N = 2500
    for t in range(1, 6):
        S = I2(t - 1, 0); cnt = {}; wrong = set(); n = 0; nw = 0
        for i in range(N):
            for x in g.loot_list_of(S, 300000 + i):
                x = str(x); n += 1
                if x in wt:
                    nw += 1; cnt[x] = cnt.get(x, 0) + 1
                    if t not in wt[x]: wrong.add(x)
            if i % 250 == 0: yield
        inw = sum(it.weight for it in items if (not it.tiers or t in list(it.tiers)) and str(it.name) in wt)
        alls = sum(it.weight for it in items if not it.tiers or t in list(it.tiers))
        share, want = nw / max(n, 1), inw / alls
        sd = math.sqrt(want * (1 - want) / max(n, 1))
        e = {"items": n, "weapons": sorted(cnt), "want": sorted(k for k, v in wt.items() if t in v), "wrong_tier": sorted(wrong),
             "weapon_share": round(share, 4), "expected": round(want, 4), "sd_off": round(abs(share - want) / sd, 2)}
        e["ok"] = e["weapons"] == e["want"] and not wrong and e["sd_off"] < 4.5
        ok = ok and e["ok"]; res[f"tier{t}"] = e
    step_result("tierloot", ok, **res)

def step_weapons():
    g = G["gen"]; c = yield from restart(); quiet(True)
    rules = W5["rules"]["who"]; out = {}; shots_ = []
    cams = [a for a in GS.get_all_actors_of_class(G["w"], unreal.SceneCapture2D) if a.actor_has_tag("RDM5_WeaponCam")]
    cam = cams[0] if cams else None
    shot_dir = os.path.join(unreal.Paths.project_saved_dir(), "W5Test", TAG)
    def front_shot(name, dist=300.0, height=30.0):
        """her alone, unlit (the colour as painted: the great hall is lit by torches), from her front-right and her right side"""
        if not cam: return
        p = G["pawn"]; l = p.get_actor_location(); f = p.get_actor_forward_vector(); r = p.get_actor_right_vector()
        cc = cam.capture_component2d
        cc.set_editor_property("primitive_render_mode", unreal.SceneCapturePrimitiveRenderMode.PRM_USE_SHOW_ONLY_LIST)
        cc.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_BASE_COLOR)
        for view, way in (("front", f * 0.85 + r * 0.5), ("side", r)):
            at_ = l + way.normal() * dist + V(0, 0, height)
            cam.set_actor_location(at_, False, True)
            d = l + V(0, 0, 20) - at_; cam.set_actor_rotation(unreal.Rotator(roll=0, pitch=math.degrees(math.atan2(d.z, math.hypot(d.x, d.y))), yaw=math.degrees(math.atan2(d.y, d.x))), True)
            cc.clear_show_only_components(); cc.show_only_actor_components(p, True); cc.capture_scene()
            unreal.RenderingLibrary.export_render_target(G["w"], cc.texture_target, shot_dir, f"{name}_{view}.png"); shots_.append(f"{name}_{view}.png")
    def palm_local(body, bone):
        """her palm point on the hand bone (the grips' place: 6.5 cm along the forearm, 2.5 below, in her reference pose)"""
        ref = unreal.AnimPoseExtensions.get_reference_pose(body.skeletal_mesh_asset.skeleton)
        bp = lambda n: unreal.AnimPoseExtensions.get_bone_pose(ref, n, unreal.AnimPoseSpaces.WORLD)
        h = bp(bone); s_ = bone[-1]; fore = (h.translation - bp(f"lowerarm_{s_}").translation).normal()
        return unreal.MathLibrary.inverse_transform_location(h, h.translation + fore * 6.5 + V(0, 0, -2.5))
    for hero in ("Warrior", "Warlock", "Rogue", "Mage", "Summoner"):
        if str(g.current_hero) != hero: g.switch_hero(hero); yield from wait(0.6); refresh()
        c = cb(); quiet(True); body = G["pawn"].mesh
        n0 = len(g.weapons)
        for w in W5["weapons"]: c.add_item(w["name"], 1)
        took = [str(x.name) for x in g.weapons][n0:]
        carried = sorted(l.split("|")[1] for l in lines(c) if l.startswith("carried|"))
        allowed = rules[hero]
        want = [w["name"] for w in W5["weapons"] if allowed == "all" or w["type"] in allowed]
        e = {"took": len(took), "carried": len(carried), "took_right": took == want, "carried_right": carried == sorted(w["name"] for w in W5["weapons"] if w["name"] not in want)}
        if not took:
            msg_ok = not c.use_item(W5["weapons"][0]["name"]) and "cannot wield" in str(c.message)
            e["refused"] = msg_ok; out[hero] = e; continue
        pr = palm_local(body, "hand_r"); pl = palm_local(body, "hand_l")
        hands, nums = [], []
        for wi, name in enumerate(took):
            i = n0 + wi; wd = g.weapons[i]; fr = W5F[wkey(name)]; w = next(x for x in W5["weapons"] if x["name"] == name)
            c.select_weapon(i); yield
            comp = c.get_weapon_mesh(); bone = str(wd.hand_bone)
            xf = comp.get_world_transform(); grip = xf.transform_location(V(*fr["origin"]))
            palm = body.get_socket_transform(bone, unreal.RelativeTransformSpace.RTS_WORLD).transform_location(pl if bone == "hand_l" else pr)
            bonus = (g.melee_bonus if not wd.get_editor_property("spell") else g.ranged_bonus)
            h = {"weapon": name, "mesh_ok": comp.static_mesh == wd.mesh, "bone": bone, "grip_to_palm_cm": round((grip - palm).length(), 1),
                 "damage": round(c.get_damage_of(i), 2), "want_damage": round((8 + 3 * w["damage"]) * (1 + bonus), 2), "durability": c.get_weapon_durability(i), "wear": c.get_weapon_wear(i)}
            # the attacks' length (each of her clips at the weapon's rate: their mean is the table's speed) and, for two
            # hands, the left palm on the hilt at each blow
            lens = []; offs = []; alongs = []
            for k in range(len(wd.attacks)):
                if not c.start_attack(): break
                lens.append(c.get_attack_length())
                hit_at = (wd.hit_times[k] - (wd.attack_starts[k] if len(wd.attack_starts) > k else 0.0)) / wd.play_rate
                yield from wait(hit_at)
                if w["type"] == "two handed sword":
                    xf = comp.get_world_transform(); o_ = xf.transform_location(V(*fr["origin"])); x_ = xf.transform_direction(V(*fr["x"])).normal()
                    lp = body.get_socket_transform("hand_l", unreal.RelativeTransformSpace.RTS_WORLD).transform_location(pl)
                    tt = (lp - o_).dot(x_); alongs.append(round(tt, 1)); offs.append(round((lp - (o_ + x_ * tt)).length(), 1))
                if k == 0 and (wi == 0 or name in ("Katana", "Plate Knight's Sword", "Ursag's Horn Blade", "Kukri", "Longbow", "Viking Bow", "Crossbow", "Dwarf Crossbow")):
                    front_shot(f"{hero}_{wkey(name)}")
                t0 = now()
                while c.is_attacking() and now() - t0 < 3.0: yield
                yield from wait(0.12)
            if lens: h["attack_s"] = round(sum(lens) / len(lens), 3); h["attacks"] = len(lens); h["want_s"] = round(cycle(w["speed"]), 3)
            if offs: h["left_palm_off_hilt_cm"] = max(offs); h["left_palm_along_hilt_cm"] = alongs
            hands.append(h)
        # a blow that lands takes 1 off; at 0 it breaks and she draws her first weapon
        i = n0; name = took[0]; c.select_weapon(i); yield
        ms = start_monsters(); ms.sort(key=lambda m: (m.get_actor_location() - G["pawn"].get_actor_location()).length())
        brk = {"weapon": name}
        gap = 110 if not g.weapons[i].get_editor_property("spell") else 600
        def by_a_monster():
            """next to the nearest monster of the start section, facing it (a quiet monster wanders off between blows)"""
            ms_ = start_monsters(); ms_.sort(key=lambda m: (m.get_actor_location() - G["pawn"].get_actor_location()).length())
            return any(stand_off(m, gap) for m in ms_)
        by_a_monster()
        c.set_weapon_wear(i, 2.0); h0 = c.hits_landed; b0 = c.weapons_broken
        t0 = now()
        while now() - t0 < 6.0 and c.hits_landed == h0:
            if not c.is_attacking(): c.start_attack()
            yield
        yield from wait(0.3); brk["wear_after_one"] = c.get_weapon_wear(i) if str(g.weapons[i].name) == name else None
        t0 = now(); h1 = c.hits_landed
        while now() - t0 < 10.0 and c.weapons_broken == b0:
            if str(c.get_weapon_name()) == name and not c.is_attacking():
                if c.hits_landed == h1 and now() - t0 > 1.5: by_a_monster(); t0b = now()
                c.start_attack()
            yield
        yield from wait(0.2)
        brk.update({"broke": c.weapons_broken - b0, "last_broken": str(c.last_broken), "still_carried": name in [str(x.name) for x in g.weapons], "now_in_hand": str(c.get_weapon_name()),
                    "message": str(c.message)})
        e.update({"hands": hands, "break": brk})
        out[hero] = e
    quiet(False)
    def hero_ok(hero, e):
        if not e["took_right"] or not e["carried_right"]: return False
        if not e.get("hands"): return e.get("refused", False)
        for h in e["hands"]:
            if not (h["mesh_ok"] and h["grip_to_palm_cm"] < 7.0 and abs(h["damage"] - h["want_damage"]) < 0.01 and abs(h.get("attack_s", -9) - h.get("want_s", 9)) < 0.03): return False
            if "left_palm_off_hilt_cm" in h and not (h["left_palm_off_hilt_cm"] < 4.0 and all(-14.0 < a < -2.0 for a in h["left_palm_along_hilt_cm"])): return False
        b = e["break"]
        return b.get("wear_after_one") == 1.0 and b["broke"] == 1 and b["last_broken"] == b["weapon"] and not b["still_carried"] and b["now_in_hand"] != b["weapon"] and "broke" in b["message"]
    ok = all(hero_ok(h, e) for h, e in out.items()) and len(out) == 5
    R.setdefault("shots", []).extend(shots_)
    step_result("weapons", ok, heroes=out, front_shots=shots_)

STEPS = {"select": step_select, "loot": step_loot, "wear": step_wear, "heroarmour": step_heroarmour, "follow": step_follow, "damage": step_damage, "ui": step_ui,
         "tiers": step_tiers, "tierloot": step_tierloot, "weapons": step_weapons}
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
