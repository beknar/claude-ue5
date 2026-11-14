"""The wilderness's test (the user's spec of 2026-11-03, docs/wilderness.txt; C++ RD/RDWild*.cpp), in play on brokenspire.
Steps:
  world   the world made (its seed, how long); the towns where the spec puts them: Brokenspire mid-south, Ashenreach in the
          continent's middle north of it, Graymourne on the north coast mid-way across, Vel Morrath north-east of Brokenspire
          and inland (the user's of 2026-11-06: "to the east, but not on the coast"; no sea within 20 km east of it, walked
          out); every template of the spec in the
          biome regions; rivers, lakes, roads between the towns; pictures of the continent and of 40 km round Brokenspire
  look    each template visited (her put on the nearest of its regions, the chunks round her made): a picture of her view,
          what the world has under her (its biome, height, snow, sand, water), the plants and rocks of the chunks there
  build7  (2026-11-07) the chunks made in steps against in one go, the same flight twice: the game thread's making a frame,
          the frames' times, every chunk the same both ways
  quests  (2026-11-07) the captain's two wilderness quests: their places, taken, played (the den's pack, the patrol's
          remains), turned in
  horse9  (2026-11-09, 913) the stable by Brokenspire's gate, the horse bought, mounted with F, her speed on it against on foot
          on the plains, the gallop under her, off with F; pictures of her riding
  ruins12 (2026-11-12, 924 ruins) the twenty kinds of ruins: each among the world's ruins, the nearest of each visited (its
          pieces, its chest, its guardians), a picture of each (ruins12=<kind>+<kind> for some)
  lairs12 (2026-11-12, 924 lairs) the lairs hidden behind something: each cover among the world's lairs, the nearest of each
          visited: its monsters inside it, how many sight lines to them its pieces block from 30 m and 15 m, woken they come
          out to her by its opening; a picture of each (lairs12=<cover>+<cover> for some)
  sites12 (2026-11-12, 924 sites) the 34 structures: each among the world's structures, every quest among them; the nearest of
          each visited (pieces, chest, guards, prisoners freed with F, a trap stepped on, the giver, the beast's walk), a picture
          (sites12=<kind>+<kind> for some; run in three batches)
  quests12 (2026-11-12, 924 quests) the 25 quests, each at its nearest structure, played through as a player does; its gold
          paid (quests12=<quest>+<quest> for some; run in batches)
  gait12  (2026-11-12, 915) the horse's walk, canter and gallop ridden on the plains: each gait's clip, rate and strides a
          second, its hooves measured in the world (no slide while down), her rider clip by the gait; pictures from the side
  poi7    (2026-11-09, 912) the points of interest: the seconds between them along 14 lines of the world's model, a 150 s
          run in play (what met her never 40 s apart), each use made with F
  secondary9 (2026-11-09, 911) a wild place's Hallowed Stone taken and not laid again, the lairs' monsters' Seraph Feathers,
          the Martial Artist's Water Walk over a lake
  list12  (2026-11-12, 923) the list of 2026-11-12's first phase: gold in the inventory, the map's scroll cut, the mouse on
          the big map (pick, click to travel, wheel, drag), rd.MapTeleport (refused unrevealed; the wilds, the town), the saves as
          a screen of cards
  wild25  (2026-11-09, 910) lairs and spawn points of six tiers along the roads, Brokenspire to Heaven: each monster of its
          place's tier and of a kind whose wild band holds it, the kinds changing along the way
Writes SourceArt/wilderness/test_<tag>.json and logs "WILDTEST done | <tag> | ok / FAILED | ...". Args: plan tag"""
import unreal, sys, json, math, os, time
__keep__ = True
TAG = sys.argv[2] if len(sys.argv) > 2 else "t"
V = unreal.Vector; GS = unreal.GameplayStatics
TOWN_ID = 1 << 30   # (a town's place id: FRDWildWorld::TownIdBase + its index)
OUT = r"E:\code\claude-ue5\claude_ue5\SourceArt\wilderness"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
SHOTS = r"E:\code\claude-ue5\claude_ue5\Saved\Screenshots\WindowsEditor"
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
G = {"w": UES.get_game_world()}
assert G["w"] is not None, "PIE is not running"
DEFAULT = "world,look,stream,towns,gate,map,places,travel,save"
PLAN = [s.strip() for s in (sys.argv[1] if len(sys.argv) > 1 else DEFAULT).split(",") if s.strip()]
R = {"tag": TAG, "plan": PLAN, "level": G["w"].get_path_name().split(".")[-1], "steps": []}
SPEC = ["grasslands", "meadows", "farms", "savannahs", "hills", "mountains", "tundras", "plains", "pine forests", "temperate autumn forests", "marshes", "wetlands",
        "mountains and peaks", "volcanoes", "coastal regions", "arctic regions", "canyons", "mesas", "canyon networks", "cold steppes", "highland moorland",
        "boreal pine forest", "temperate aspen", "volcanic tundra", "geothermal caldera", "glacial", "taigas", "rocky coastal"]


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
    unreal.log(f"WILDTEST step {name}: {'ok' if ok else 'FAILED'} {json.dumps(kw, ensure_ascii=False, default=str)[:2400]}")
def shot(name, res="1920x1080"):
    unreal.SystemLibrary.execute_console_command(G["w"], f"HighResShot {res} filename=wd_{TAG}_{name}")
    R.setdefault("shots", []).append(f"wd_{TAG}_{name}.png")
def put(at, yaw=None, z=None):
    p = G["pawn"]; p.set_actor_location(V(at.x, at.y, (at.z if z is None else z) + 100.0), False, True)
    if yaw is not None:
        p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw), True); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-12, yaw=yaw))
def place(what):
    r = G["gen"].get_town_place(what)
    return r if isinstance(r, unreal.Vector) else None
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
def quiet(on):
    g = G["gen"]
    if on: G["aggro"] = (g.get_editor_property("aggro_distance"), g.get_editor_property("lose_distance")); g.set_editor_property("aggro_distance", 0.0); g.set_editor_property("lose_distance", 1.0)
    elif "aggro" in G: g.set_editor_property("aggro_distance", G["aggro"][0]); g.set_editor_property("lose_distance", G["aggro"][1])
def state():
    p = str(G["gen"].get_wild_state()).split("|")
    if len(p) < 13: return {"ready": 0}
    k = ["ready", "seed", "init_s", "chunks", "in_flight", "built", "dropped", "max_active", "compute_ms", "build_ms_max", "revealed", "found", "towns", "wild_ticks", "gen_ticks", "paused", "menu", "panel"]
    return {a: (float(b) if "." in b else int(b)) for a, b in zip(k, p)}
def sample(x_m, y_m):
    p = str(G["gen"].get_wild_sample_at(V(x_m * 100.0, y_m * 100.0, 0))).split("|")
    k = ["h", "z", "biome", "biome2", "w1", "water", "water_m", "rock", "snow", "sand", "road", "field", "canopy", "lava", "tier"]
    return {a: (b if a in ("biome", "biome2") else float(b)) for a, b in zip(k, p)}
def towns():
    out = {}
    for l in G["gen"].get_wild_town_lines():
        p = str(l).split("|"); out[p[0]] = {"kind": p[1], "x": float(p[2]), "y": float(p[3]), "h": float(p[4]), "style": int(p[5])}
    return out
def wait_ready(sec=60):
    t0 = time.time()
    while time.time() - t0 < sec and not state().get("ready"): yield
def watching(inner, bag):
    """run a waiting generator, keeping every new line of the HUD's message as it goes (the HUD shows only the latest)"""
    for _ in inner:
        try: m = str(cb().message)
        except Exception: m = ""
        if m and (not bag or bag[-1] != m): bag.append(m)
        yield
def wait_chunks(sec=40, need=60):
    t0 = time.time()
    while time.time() - t0 < sec:
        s = state()
        if s.get("in_flight", 1) == 0 and s.get("chunks", 0) >= need: break
        yield
    yield from rwait(0.5)


# ------------------------------------------------------------------------------------------------ the world
CONT = {"xs": -80000.0, "xn": 220000.0, "yw": -150000.0, "ye": 150000.0}
def sea_along(x, y, dx, dy, max_m, step=100.0):
    """metres walked from (x, y) along (dx, dy) until the sea (water kind 1), or None"""
    d = 0.0
    while d <= max_m:
        if int(sample(x + dx * d, y + dy * d)["water"]) == 1: return d
        d += step
    return None
def step_world():
    g = G["gen"]; res = {}
    yield from wait_ready(90)
    st = state(); res["state"] = st
    T = towns(); res["towns"] = T
    W = CONT["xn"] - CONT["xs"]
    b = T.get("Brokenspire"); a = T.get("Ashenreach"); gm = T.get("Graymourne"); vm = T.get("Vel Morrath"); ks = T.get("Kethrys Spire"); hv = T.get("Heaven")
    chk = {}
    if b:
        chk["brokenspire_mid_south"] = 0.15 < (b["x"] - CONT["xs"]) / W < 0.42 and abs(b["y"]) < 0.15 * W
    if a and b:
        mid = ((CONT["xs"] + CONT["xn"]) / 2, 0.0)
        chk["ashenreach_middle"] = math.hypot(a["x"] - mid[0], a["y"] - mid[1]) < 25000
        chk["ashenreach_north_of_brokenspire"] = a["x"] - b["x"] > 30000 and abs(a["y"] - b["y"]) < 15000
    if gm:
        res["graymourne_sea_north_m"] = sea_along(gm["x"], gm["y"], 1, 0, 6000)
        chk["graymourne_north_coast"] = gm["x"] > (CONT["xs"] + CONT["xn"]) / 2 + 70000 and abs(gm["y"]) < 40000 and res["graymourne_sea_north_m"] is not None and res["graymourne_sea_north_m"] < 1500
    if vm and b:
        res["velmorrath_sea_east_m"] = sea_along(vm["x"], vm["y"], 0, 1, 30000, 250.0)
        s = sample(vm["x"], vm["y"])
        # (since 2026-11-06 the holy city: north-east of Brokenspire, inland)
        chk["velmorrath_north_east"] = vm["y"] - b["y"] > 40000 and vm["x"] - b["x"] > 30000
        chk["velmorrath_inland"] = (res["velmorrath_sea_east_m"] is None or res["velmorrath_sea_east_m"] > 20000) and int(s["water"]) == 0
    if ks and gm:
        # (the list of 2026-11-08b: Kethrys Spire north-west of Graymourne, inland, 60 to 120 km from it; PR #32's review)
        res["kethrys_from_graymourne_km"] = round(math.hypot(ks["x"] - gm["x"], ks["y"] - gm["y"]) / 1000.0, 1)
        chk["kethrys_north_west_inland"] = ks["x"] < gm["x"] and ks["y"] < gm["y"] - 30000 and 60 <= res["kethrys_from_graymourne_km"] <= 120 and int(sample(ks["x"], ks["y"])["water"]) == 0
    if hv and ks:
        # (the list of 2026-11-08b: Heaven past Kethrys Spire, south-west of it, inland, 40 to 110 km from it)
        res["heaven_from_kethrys_km"] = round(math.hypot(hv["x"] - ks["x"], hv["y"] - ks["y"]) / 1000.0, 1)
        chk["heaven_past_kethrys_inland"] = hv["x"] < ks["x"] and hv["y"] < ks["y"] and 40 <= res["heaven_from_kethrys_km"] <= 110 and int(sample(hv["x"], hv["y"])["water"]) == 0
    res["checks"] = chk
    # the templates' census
    bl = {}
    for l in g.get_wild_biome_lines():
        p = str(l).split("|"); bl[p[0]] = {"cells": int(p[1]), "x": float(p[2]), "y": float(p[3]), "km": float(p[4])}
    res["biomes"] = bl
    res["missing_templates"] = [n for n in SPEC if bl.get(n, {}).get("cells", 0) == 0]
    feats = [str(l) for l in g.get_wild_feature_lines()]
    res["rivers"] = sum(1 for f in feats if f.startswith("river|")); res["lakes"] = sum(1 for f in feats if f.startswith("lake|"))
    res["roads"] = [f for f in feats if f.startswith("road|")]
    res["river_lengths_km"] = sorted([float(f.split("|")[2]) for f in feats if f.startswith("river|")], reverse=True)[:8]
    # pictures of the continent and of Brokenspire's surroundings
    for nm, px, box in (("continent", 1600, (CONT["xs"], CONT["yw"], CONT["xn"], CONT["ye"])), ("around", 1200, (-20000, -20000, 20000, 20000)), ("near", 1000, (-2500, -2500, 2500, 2500))):
        p = os.path.join(SHOTS, f"wd_{TAG}_map_{nm}.png")
        t0 = time.time(); ok = g.wild_debug_map(p, px, box[0], box[1], box[2], box[3], False)
        res[f"map_{nm}"] = {"ok": ok, "s": round(time.time() - t0, 1)}
        yield
    # (the places' ids: a place's id once reached the towns' range in the northern cells (x 62 and on), and those places were
    # taken for towns: no fast travel there, not on the map; one cell's were exactly towns 0 to 7)
    ids = {}
    for cx, cy in ((190000, -40000), (200000, 30000), (60000, 0), (-20000, 20000)):
        for l in g.get_wild_places_near(V(cx * 100.0, cy * 100.0, 0), 12000.0):
            p = str(l).split("|"); ids.setdefault(int(p[0]), set()).add((p[1], p[2]))
    res["place_ids"] = {"count": len(ids), "north": sum(1 for i, v in ids.items() if any(k not in ("town", "city") for k, _ in v) and i >= 62 << 14),
                        "town_range_not_towns": sorted(i for i, v in ids.items() if i >= TOWN_ID and any(k not in ("town", "city") for k, _ in v))[:5],
                        "shared": sorted(i for i, v in ids.items() if len(v) > 1)[:5]}
    pid = res["place_ids"]
    ok = st.get("ready") == 1 and all(chk.values()) and len(chk) == 6 + (1 if ks else 0) + (1 if hv and ks else 0) and not res["missing_templates"] and res["rivers"] >= 8 and res["lakes"] >= 5 and len(res["roads"]) >= 4 + (1 if ks else 0) + (1 if hv else 0) \
        and pid["count"] > 20 and pid["north"] > 0 and not pid["town_range_not_towns"] and not pid["shared"]
    step_result("world", ok, **res)


def step_look():
    g = G["gen"]; res = {"visits": {}}; quiet(True)
    yield from wait_ready(90)
    bl = {}
    for l in g.get_wild_biome_lines():
        p = str(l).split("|"); bl[p[0]] = (float(p[2]), float(p[3]))
    pick = [s for s in (G.get("look_only") or SPEC) if s in bl]
    for name in pick:
        x, y = bl[name]
        # (a land point of that biome near its region's site)
        best = None
        for r in (0, 400, 900, 1600, 2500, 3500):
            for k in range(12 if r else 1):
                a = k * math.pi / 6
                px, py = x + r * math.cos(a), y + r * math.sin(a)
                s = sample(px, py)
                if s["biome"] != name or int(s["water"]) != 0: continue
                # (walkable: a steep slope slides her down it, a fall that kills)
                hs = [sample(px + dx, py + dy)["h"] for dx, dy in ((4, 0), (-4, 0), (0, 4), (0, -4))]
                if max(abs(h - s["h"]) for h in hs) < 2.2: best = (px, py, s); break
            if best: break
        if not best: res["visits"][name] = {"found": False}; continue
        px, py, s = best
        g.wild_put_her(px, py)
        yield from wait_chunks(35, 50)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=(hash(name) % 360)))
        yield from rwait(1.5)
        shot("look_" + name.replace(" ", "_"), "1280x720"); yield from rwait(1.2)
        if not res.get("basecolor_shot"):
            # (the first: also the ground's albedo itself, the base colour buffer, no light, exposure or fog)
            cmd = lambda c: unreal.SystemLibrary.execute_console_command(G["w"], c)
            cmd("r.BufferVisualizationTarget BaseColor"); cmd("ShowFlag.VisualizeBuffer 1"); yield from rwait(0.6)
            shot("look_" + name.replace(" ", "_") + "_basecolor", "1280x720"); yield from rwait(1.5)
            cmd("ShowFlag.VisualizeBuffer 0"); yield from rwait(0.3)
            res["basecolor_shot"] = name
        lines = [str(l).split("|") for l in g.get_wild_chunk_lines()]
        fps = []
        for _ in range(30): yield; fps.append(g.get_fps())
        res["visits"][name] = {"found": True, "at": [round(px), round(py)], "sample": s, "chunks": len(lines), "instances": sum(int(l[2]) for l in lines),
                               "trees": sum(int(l[9]) for l in lines if len(l) > 9), "state": state(),
                               "fps": round(sum(fps) / len(fps), 1), "pawn": G["pc"].get_controlled_pawn() is not None}
    quiet(False)
    # (a biome whose table has plants seen from afar (trees, bushes, rocks: no "n" in their flags) must have some in the
    # chunks round her, and one whose table has trees some trees: a canopy factor once took every tree of the open
    # biomes, the savannah's acacias too, while their bushes and rocks kept the total up)
    far, trees = {}, {}
    try:
        with open(os.path.join(OUT, "biomes.json"), encoding="utf-8") as f: bj = json.load(f)
        for b in (bj.get("biomes", bj) if isinstance(bj, dict) else bj):
            fl = [e for e in b.get("foliage", []) if "n" not in (e[4] if len(e) > 4 else "") and float(e[2]) > 0]
            far[b["name"]] = [e[0].split("/")[-1] for e in fl]
            trees[b["name"]] = [e[0].split("/")[-1] for e in fl if e[1] == "tree"]
    except Exception as e: res["far_error"] = str(e)
    for name, v in res["visits"].items():
        if v.get("found"):
            v["far_kinds"] = far.get(name, []); v["tree_kinds"] = trees.get(name, [])
            v["far_ok"] = (v["instances"] > 0 or not v["far_kinds"]) and (v.get("trees", 0) > 0 or not v["tree_kinds"])
    ok = all(v.get("found") and v.get("pawn") and v["state"].get("chunks", 0) >= 56 and v.get("far_ok", False) for v in res["visits"].values()) and len(res["visits"]) == len(pick) and not res.get("far_error")
    step_result("look", ok, **res)


# ------------------------------------------------------------------------------------------------ streaming, memory
def chunks():
    out = []
    for l in G["gen"].get_wild_chunk_lines():
        p = str(l).split("|"); out.append({"x": int(p[0]), "y": int(p[1]), "inst": int(p[2]), "tris": int(p[3]), "near": int(p[4]), "col": int(p[5]), "monsters": int(p[6]), "props": int(p[7]), "near_hism": int(p[8]),
                                           "trees": int(p[9]) if len(p) > 9 else 0, "making": int(p[10]) if len(p) > 10 else 0})
    return out
def gc_mem():
    unreal.SystemLibrary.collect_garbage()
    return round(G["gen"].get_memory_mb(), 0)
def fly(on):
    cm = G["pawn"].get_component_by_class(unreal.CharacterMovementComponent)
    cm.set_movement_mode(unreal.MovementMode.MOVE_FLYING if on else unreal.MovementMode.MOVE_WALKING)
def hover_at(x, y, over=300.0):
    z = sample(x, y)["z"] + over
    G["pawn"].set_actor_location(V(x * 100.0, y * 100.0, z), False, True)
def step_stream():
    g = G["gen"]; res = {}; quiet(True)
    yield from wait_ready(90)
    sx, sy = 3200.0, 2600.0
    g.wild_put_her(sx, sy); yield from wait_chunks(40, 56)
    yield from rwait(2.0); res["mem_start"] = gc_mem(); s0 = state()
    fly(True)
    mx = 0; viol = 0; samples = []
    cm = g.get_editor_property("wild_chunk_m"); drop = g.get_editor_property("wild_drop_m")
    for leg in (1, -1):
        for k in range(61):
            y = sy + (k if leg > 0 else 60 - k) * 100.0
            hover_at(sx, y); yield from rwait(0.3)
            cs = chunks(); mx = max(mx, len(cs))
            for c in cs:
                cx, cy = (c["x"] + 0.5) * cm, (c["y"] + 0.5) * cm
                if abs(cx - sx) > drop + 1 or abs(cy - y) > drop + 1: viol += 1
            if k % 15 == 0: samples.append({"y": y, "chunks": len(cs), "near": sum(c["near"] for c in cs), "mem": round(g.get_memory_mb())})
        if leg > 0: res["mem_far"] = gc_mem()
    fly(False)
    g.wild_put_her(sx, sy); yield from wait_chunks(30, 56); yield from rwait(2.0)
    res["mem_back"] = gc_mem(); s1 = state()
    res["max_chunks"] = mx; res["outside_square"] = viol; res["samples"] = samples
    res["dropped"] = s1["dropped"] - s0["dropped"]; res["built"] = s1["built"] - s0["built"]
    res["active_km2_max"] = round(mx * cm * cm / 1e6, 2)
    res["compute_ms"] = s1["compute_ms"]; res["build_ms_max"] = s1["build_ms_max"]
    quiet(False)
    # (the 2 km square: a chunk is made when its middle is within 1 km of her on both axes, dropped past 1.125 km: 9 x 9 at most)
    ok = mx <= 81 and viol == 0 and res["dropped"] >= 60 and res["built"] >= 60 and res["mem_back"] - res["mem_start"] < 700
    step_result("stream", ok, **res)


# ------------------------------------------------------------------------------------------------ the towns
def town_state():
    p = str(G["gen"].get_wild_town_state()).split("|")
    k = ["idx", "name", "loading", "section", "dist_m", "build_s", "loaded", "dropped", "in_walls", "ox", "oy", "home"]
    return {a: (b if a == "name" else float(b)) for a, b in zip(k, p)}
def wait_town(sec, cond):
    t0 = time.time()
    while time.time() - t0 < sec and not cond(town_state()): yield
def drawn(): return [str(a) for a in G["pc"].get_hud().get_art_drawn()]
def step_towns():
    g = G["gen"]; res = {}; quiet(True)
    yield from wait_ready(90)
    T = towns(); b = T["Brokenspire"]; vm = T["Vel Morrath"]
    # Brokenspire: in its square (loaded first: an earlier step may have left it), then 2.3 km off (dropped), then back to 1.2 km (built again)
    if town_state()["section"] != 1 or town_state()["name"] != "Brokenspire":
        g.wild_put_her(900.0, 0.0); yield from wait_town(90, lambda s: s["section"] == 1 and s["loading"] == 0 and s["name"] == "Brokenspire")
    sq = place("square")
    if sq: put(sq, yaw=0.0)
    yield from wait(1.0)
    res["at_start"] = town_state(); res["folk_start"] = len(folk())
    g.wild_put_her(2300.0, 0.0); yield from wait_town(20, lambda s: s["section"] == 0)
    yield from rwait(1.0)
    res["far"] = town_state(); res["folk_far"] = len(folk()); res["mem_far"] = gc_mem()
    g.wild_put_her(1200.0, 0.0); yield from wait_town(90, lambda s: s["section"] == 1 and s["loading"] == 0)
    yield from rwait(1.0)
    res["back"] = town_state(); res["folk_back"] = len(folk())
    # Vel Morrath: 1.3 km west of it (built as she comes), then in its walls
    g.wild_put_her(vm["x"], vm["y"] - 1300.0); yield from wait_town(120, lambda s: s["name"] == "Vel Morrath" and s["section"] == 1 and s["loading"] == 0)
    yield from rwait(1.0)
    res["vm_near"] = town_state()
    res["minimap_outside"] = "wild_minimap" in drawn()
    sq2 = place("square")
    if sq2: put(sq2, yaw=0.0)
    yield from wait(1.5)
    res["vm_in"] = town_state(); res["minimap_inside_wild"] = "wild_minimap" in drawn()
    F = folk(); res["vm_folk"] = len(F)
    res["vm_roles"] = sorted(set(f["role"] for f in F))
    res["vm_titles_brokenspire"] = [f["title"] for f in F if "Brokenspire" in f["title"]][:5]
    res["vm_titles_own"] = [f["title"] for f in F if "Vel Morrath" in f["title"]][:5]
    res["vm_square"] = [round(sq2.x), round(sq2.y)] if sq2 else None
    BS_NOTABLES = {t_["title"] for t_ in json.load(open(os.path.join(os.path.dirname(OUT), "brokenspire", "town.json"), encoding="utf-8"))["townsfolk"]
                   if t_.get("role") in ("Elder", "Scholar", "Captain")}
    res["vm_notables"] = sorted({f["title"] for f in F if f["role"] in ("Elder", "Scholar", "Captain")})
    quiet(False)
    ok = (res["at_start"]["section"] == 1 and res["far"]["section"] == 0 and res["folk_far"] == 0 and res["back"]["section"] == 1 and res["folk_back"] > 0
          and res["vm_near"]["name"] == "Vel Morrath" and res["vm_in"]["in_walls"] == 1 and res["minimap_outside"] and not res["minimap_inside_wild"]
          and res["vm_folk"] > 0 and not res["vm_titles_brokenspire"]
          # (Vel Morrath, a city since 2026-11-06, has an archbishop, an archivist and a commander of its own: none of them
          # Brokenspire's elder, scholar or captain)
          and not any(f["title"] in BS_NOTABLES for f in F) and "Elder" in res["vm_roles"])
    G["vm_found"] = True
    step_result("towns", ok, **res)


def step_gate():
    """the gate open (the wilderness beyond it): no 'barred', she walks out through it"""
    g = G["gen"]; res = {}; quiet(True)
    yield from wait_ready(90)
    if town_state()["name"] != "Brokenspire" or town_state()["section"] != 1:
        g.wild_put_her(600.0, 600.0); g.load_wild_town(0, True); yield from rwait(1.0)
    gate = place("gate"); sq = place("square")
    if not gate or not sq: step_result("gate", False, error="no gate or square"); return
    d = V(sq.x - gate.x, sq.y - gate.y, 0); n = math.hypot(d.x, d.y); d = V(d.x / n, d.y / n, 0)
    inside = V(gate.x + d.x * 350, gate.y + d.y * 350, 0)
    # (the list of 2026-11-04: the portcullis is raised with a lever by the gate first)
    S = g.get_section(unreal.IntPoint(0, 0))
    if S and not S.is_portcullis_up():
        lv = [str(l).split("|") for l in S.get_town_improve_lines() if str(l).startswith("lever|")]
        if lv:
            q = min(lv, key=lambda q: math.hypot(float(q[2]) - inside.x, float(q[3]) - inside.y))
            put(V(float(q[2]) + d.x * 110, float(q[3]) + d.y * 110, 0)); yield from wait(0.4)
            res["lever"] = str(g.interact_nearest(G["pawn"].get_actor_location())); yield from rwait(11.0)
        res["raised"] = S.is_portcullis_up()
    put(inside, yaw=math.degrees(math.atan2(-d.y, -d.x))); yield from wait(0.5)
    res["prompt"] = str(g.describe_nearest(G["pawn"].get_actor_location(), 600.0))
    t0 = time.time()
    while time.time() - t0 < 5.0:
        G["pawn"].add_movement_input(V(-d.x, -d.y, 0), 1.0, False); yield
    p = G["pawn"].get_actor_location()
    res["past_gate_m"] = round(((p.x - gate.x) * -d.x + (p.y - gate.y) * -d.y) / 100.0, 1)
    yield from rwait(0.5)
    res["in_walls_after"] = town_state()["in_walls"]
    shot("gate_out", "1280x720"); yield from rwait(1.2)
    quiet(False)
    ok = res["past_gate_m"] > 6 and "barred" not in res["prompt"] and res["in_walls_after"] == 0
    step_result("gate", ok, **res)


# ------------------------------------------------------------------------------------------------ the map
def map_state():
    p = str(G["gen"].get_wild_map_state()).split("|")
    k = ["cx", "cy", "mpp", "level", "tiles", "asked", "tile_ms", "hover", "hover_name", "made", "refusal", "last_travel"]
    return {a: (b if a in ("hover_name", "refusal", "last_travel") else float(b)) for a, b in zip(k, p)}
def step_map():
    g = G["gen"]; res = {}; quiet(True)
    yield from wait_ready(90)
    g.wild_put_her(900.0, -700.0); yield from wait_chunks(30, 50); yield from rwait(1.5)
    res["minimap_drawn"] = "wild_minimap" in drawn()
    shot("minimap", "1280x720"); yield from rwait(1.0)
    g.set_map_open(True); yield from rwait(1.0)
    t0 = time.time()
    while time.time() - t0 < 20 and map_state()["asked"] > 0: yield
    yield from rwait(0.5)
    res["open"] = map_state(); res["drawn"] = [a for a in drawn() if a.startswith(("wild_", "wmap_", "mapc_"))]
    shot("map_near", "1600x900"); yield from rwait(1.5)
    for nm, mpp, cx, cy in (("map_region", 60.0, 2000.0, 0.0), ("map_country", 160.0, 40000.0, 20000.0), ("map_continent", 330.0, 70000.0, 0.0)):
        g.set_wild_map_view(cx, cy, mpp)
        t0 = time.time()
        while time.time() - t0 < 25 and map_state()["asked"] > 0: yield
        yield from rwait(1.0)
        res[nm] = map_state(); res[nm + "_drawn"] = [a for a in drawn() if a.startswith("wmap_")]
        shot(nm, "1600x900"); yield from rwait(1.5)
    # (the fog's picture while the map is dragged: 40 frames, a few metres each, at the region's scale, and a little zoom; it was
    # made again in every one of them)
    g.set_wild_map_view(2000.0, 0.0, 60.0); yield from rwait(0.5)
    b0 = g.get_editor_property("wild_fog_builds")
    for k in range(40):
        g.set_wild_map_view(2000.0 + k * 40.0, k * 25.0, 60.0 * (1.0 + 0.004 * k)); yield
    res["fog_drag"] = {"frames": 40, "builds": g.get_editor_property("wild_fog_builds") - b0}
    g.set_map_open(False); yield from rwait(0.5)
    res["revealed_here"] = g.wild_revealed_at(900.0, -700.0); res["revealed_far"] = g.wild_revealed_at(150000.0, 100000.0)
    quiet(False)
    ok = (res["minimap_drawn"] and res["open"]["tiles"] > 0 and res["revealed_here"] and not res["revealed_far"]
          and res["map_continent"]["level"] <= 2 and res["open"]["level"] >= 8 and any(a in res["map_continent_drawn"] for a in ("wmap_town", "wmap_city"))
          and res["fog_drag"]["builds"] <= 3)
    step_result("map", ok, **res)


# ------------------------------------------------------------------------------------------------ the list of 2026-11-12, phase 1
def map_frame():
    p = str(G["gen"].get_map_frame()).split("|")
    return {"kind": int(p[0]), "cx": float(p[1]), "cy": float(p[2]), "vx": float(p[3]), "vy": float(p[4]), "k": float(p[5]),
            "a": (float(p[6]), float(p[7])), "b": (float(p[8]), float(p[9]))}
def to_screen(f, wx, wy):
    """a world point (cm) on the big map as last drawn: C + (W.Y - Vw.Y, Vw.X - W.X) x K"""
    return (f["cx"] + (wy - f["vy"]) * f["k"], f["cy"] + (f["vx"] - wx) * f["k"])
def to_world(f, sx, sy): return (f["vx"] - (sy - f["cy"]) / f["k"], f["vy"] + (sx - f["cx"]) / f["k"])
def v2(p): return unreal.Vector2D(float(p[0]), float(p[1]))
def slate_click(p, map_click=True):
    """a click through Slate at p; on a big map, again (up to three times) when the map took no click: the real mouse resting
    over the play window drags the game's pointer to itself when the screen changes (the rules' "the real mouse over the game's
    view"), and the press became a drag (RDMAPPOINTER's log)"""
    g = G["gen"]; why = ""
    for k in range(3 if map_click else 1):
        n0 = g.get_editor_property("map_clicks")
        g.slate_mouse_move(v2(p)); yield from rwait(0.05)
        why = str(g.slate_mouse_button(v2(p), key("LeftMouseButton"), True)); yield from rwait(0.08)
        why = why or str(g.slate_mouse_button(v2(p), key("LeftMouseButton"), False)); yield from rwait(0.3)
        if not map_click or g.get_editor_property("map_clicks") > n0: break
        R.setdefault("click_retries", 0); R["click_retries"] += 1
    return why
def wait_tiles(sec=20):
    t0 = time.time()
    while time.time() - t0 < sec and map_state()["asked"] > 0: yield
    yield from rwait(0.5)
def step_list12():
    """the user's list of 2026-11-12 (docs/improvements12.txt), its first phase (RD/RDList12.cpp, 923 scrollcut):
    - gold in the inventory in the wilds (its picture, the purse's icon drawn);
    - the wilds' map: two pictures of the same screen with the map moved far between them, for blender_numpy/l12_scroll_check.py
      (past the scroll's torn edge, in its holes and between its threads nothing may change: the map is not drawn there);
    - the mouse on it: the pointer up while it is open and down after; the place under the pointer picked (Brokenspire's mark),
      a click there travels to it (through Slate, as the device sends it); the wheel zooms about the pointer (the world point
      under it stays); a drag moves the map and travels nowhere;
    - rd.MapTeleport: a click refused while the map is not revealed; revealed, a click 2 km off puts her there; in Brokenspire's
      walls, the town's map: a click on the square puts her on it;
    - the Escape menu's Load page and the saves to save over as a screen of cards: three a row, a card picked with a click (the
      save over chosen, back on the Save page), the keys moving by a card and a row"""
    g = G["gen"]; res = {}; quiet(True)
    yield from wait_ready(90)
    g.wild_put_her(900.0, -700.0); yield from wait_chunks(30, 50); yield from rwait(1.0)
    pc = G["pc"]
    # ---- gold in the inventory (the wilds)
    g.add_gold(123, "test"); cb().set_inventory_open(True); yield from rwait(1.0)
    res["inventory"] = {"gold": g.get_gold(), "icon_drawn": "icon_gold" in drawn()}
    shot("l12_inventory", "1280x720"); yield from rwait(1.2)
    cb().set_inventory_open(False); yield from rwait(0.5)
    # ---- the map: the cut, the pointer, a place picked under it, a click to travel there
    T = towns(); b = T["Brokenspire"]
    g.set_map_open(True); yield from rwait(0.6)
    g.set_wild_map_view(b["x"] + 2500.0, b["y"] - 1500.0, 12.0); yield from wait_tiles()
    f = map_frame()
    res["map"] = {"frame_kind": f["kind"], "pointer_up": bool(pc.get_editor_property("show_mouse_cursor")), "edge_drawn": "mapc_scroll_edge" in drawn()}
    R.setdefault("frames", {})["l12_map_cut"] = f
    shot("l12_map_cut", "1280x720"); yield from rwait(1.5)
    # (the same screen with the map far away (other tiles under the sheet): blender_numpy/l12_scroll_check.py compares the two
    # pictures: where the scroll's edge is neither parchment nor its open middle nothing may change (only the backdrop is there),
    # inside the map must)
    g.set_wild_map_view(b["x"] + 40000.0, b["y"] + 30000.0, 160.0); yield from wait_tiles()
    shot("l12_map_cut2", "1280x720"); yield from rwait(1.5)
    g.set_wild_map_view(b["x"] + 2500.0, b["y"] - 1500.0, 12.0); yield from wait_tiles(10)
    f = map_frame()
    sb = to_screen(f, b["x"] * 100.0, b["y"] * 100.0)
    why = str(g.slate_mouse_move(v2((sb[0] + 40, sb[1] + 40)))); yield from rwait(0.2)
    why = why or str(g.slate_mouse_move(v2(sb))); yield from rwait(0.5)
    ms = map_state()
    for _ in range(2):
        if int(ms["hover"]) >= 0: break
        g.slate_mouse_move(v2((sb[0] + 30, sb[1] + 30))); yield from rwait(0.1); g.slate_mouse_move(v2(sb)); yield from rwait(0.5); ms = map_state()
        R.setdefault("click_retries", 0); R["click_retries"] += 1
    bid = next((int(float(p[0])) for p in [str(l).split("|") for l in g.get_wild_places_near(V(b["x"] * 100.0, b["y"] * 100.0, 0), 300)] if p[1] in ("town", "city")), -1)
    res["pick"] = {"slate": why, "at": [round(sb[0]), round(sb[1])], "hover": int(ms["hover"]), "hover_name": ms["hover_name"], "brokenspire_id": bid,
                   "centre_far": round(math.hypot(sb[0] - f["cx"], sb[1] - f["cy"]))}
    # (PR #54's review: the keys or the pad moving the map hand the pick back to the cross: an arrow held, Brokenspire no longer
    # picked under the resting pointer)
    cb().simulate_key(key("Up"), True); yield from rwait(0.3); cb().simulate_key(key("Up"), False); yield from rwait(0.4)
    res["pick"]["after_keys_hover"] = int(map_state()["hover"])
    f = map_frame()          # (the arrow moved the map: its frame now)
    # (the wheel about the pointer: the world point under it before and after)
    pw = (f["cx"] + 180.0, f["cy"] - 120.0); wb = to_world(f, *pw)
    g.slate_mouse_move(v2(pw)); yield from rwait(0.2)
    why2 = str(g.slate_wheel(v2(pw), 1.0)); yield from rwait(0.5)
    f2 = map_frame(); wa = to_world(f2, *pw)
    res["wheel"] = {"slate": why2, "k_before": f["k"], "k_after": f2["k"], "moved_under_pointer_m": round(math.hypot(wa[0] - wb[0], wa[1] - wb[1]) / 100.0, 1),
                    "m_a_pixel": round(1.0 / f2["k"] / 100.0, 2)}
    # (a drag: the map moves, nothing is travelled to)
    c0 = (map_state()["cx"], map_state()["cy"]); lc0 = str(g.get_editor_property("last_map_click"))
    d0 = (f2["cx"] - 150.0, f2["cy"] + 60.0)
    g.slate_mouse_move(v2(d0)); yield from rwait(0.1)
    g.slate_mouse_button(v2(d0), key("LeftMouseButton"), True); yield from rwait(0.1)
    for k in range(1, 9):
        g.slate_mouse_move(v2((d0[0] + 15 * k, d0[1]))); yield from rwait(0.05)
    g.slate_mouse_button(v2((d0[0] + 120, d0[1])), key("LeftMouseButton"), False); yield from rwait(0.4)
    c1 = (map_state()["cx"], map_state()["cy"])
    res["drag"] = {"moved_m": round(math.hypot(c1[0] - c0[0], c1[1] - c0[1])), "clicked": str(g.get_editor_property("last_map_click")) != lc0}
    def click_world(view, wx, wy):
        """a click on the big map at the world point (cm), the view set again (a wild map) and the point found on the screen anew
        before each try: a press the real mouse dragged away panned the map, and the same pixel was then 8 km off"""
        why = ""
        for k in range(3):
            if view: g.set_wild_map_view(*view); yield from wait_tiles(5)
            else: yield from rwait(0.2)
            s = to_screen(map_frame(), wx, wy); n0 = g.get_editor_property("map_clicks")
            g.slate_mouse_move(v2(s)); yield from rwait(0.3)
            why = yield from slate_click(s, False)
            if g.get_editor_property("map_clicks") > n0: break
            R.setdefault("click_retries", 0); R["click_retries"] += 1
        return why
    def click_logic(view, wx, wy):
        """the click's outcome at the world point's screen point, ClickMapAt called with it (the real mouse over the play window
        pulls the game's pointer to itself and spoils Slate's clicks: the pointer's own path is measured by the travel click)"""
        if view: g.set_wild_map_view(*view); yield from wait_tiles(5)
        else: yield from rwait(0.3)
        s = to_screen(map_frame(), wx, wy); g.click_map_at(v2(s)); yield from rwait(0.3)
        return s
    # (the click on the place: back over Brokenspire, the pointer on it, a click)
    why3 = yield from click_world((b["x"] + 2500.0, b["y"] - 1500.0, 12.0), b["x"] * 100.0, b["y"] * 100.0); yield from rwait(1.5)
    res["travel_click"] = {"slate": why3, "last_click": str(g.get_editor_property("last_map_click")), "map_open": bool(g.get_editor_property("map_open")),
                           "in_walls": bool(g.is_in_town_walls(G["pawn"].get_actor_location()))}
    yield from rwait(1.0)
    res["pointer_after"] = bool(pc.get_editor_property("show_mouse_cursor"))
    # ---- rd.MapTeleport: refused unrevealed, then a click 2 km out; then the town's map
    ex = lambda c: unreal.SystemLibrary.execute_console_command(G["w"], c)
    ex("rd.RevealMap off"); ex("rd.MapTeleport")
    g.wild_put_her(b["x"] + 600.0, b["y"]); yield from wait_chunks(30, 40); yield from rwait(0.6)
    g.set_map_open(True); yield from rwait(0.4)
    tv = (b["x"] + 1500.0, b["y"] + 1000.0, 14.0); tw = (b["x"] + 2200.0, b["y"] + 1400.0)
    yield from click_logic(tv, tw[0] * 100.0, tw[1] * 100.0)
    refused = str(g.get_editor_property("last_map_click"))
    ex("rd.RevealMap"); yield from rwait(0.4)
    n0 = g.get_editor_property("map_teleports")
    yield from click_logic(tv, tw[0] * 100.0, tw[1] * 100.0); yield from rwait(2.0)
    hp = G["pawn"].get_actor_location()
    res["teleport"] = {"refused": refused, "click": str(g.get_editor_property("last_map_click")), "teleports": g.get_editor_property("map_teleports") - n0,
                       "off_target_m": round(math.hypot(hp.x / 100.0 - tw[0], hp.y / 100.0 - tw[1]), 1), "map_open": bool(g.get_editor_property("map_open"))}
    # (PR #54's review: out at sea there is nothing to stand on: 3 km past the nearest coast, the click refused, she not moved)
    seas = [(d, dx, dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) for d in [sea_along(b["x"], b["y"], dx, dy, 120000.0, 500.0)] if d is not None]
    if seas:
        d, dx, dy = min(seas); sw = (b["x"] + dx * (d + 3000.0), b["y"] + dy * (d + 3000.0))
        g.set_map_open(True); yield from rwait(0.4); before = G["pawn"].get_actor_location()
        yield from click_logic((sw[0], sw[1], 14.0), sw[0] * 100.0, sw[1] * 100.0); yield from rwait(1.0)
        res["sea"] = {"click": str(g.get_editor_property("last_map_click")), "moved_m": round(dist2(G["pawn"].get_actor_location(), before) / 100.0, 1),
                      "water": int(sample(*sw)["water"])}
        g.set_map_open(False); yield from rwait(0.3)
    else: res["sea"] = None
    # (the town's map, inside Brokenspire's walls: a click on the square)
    ex("rd.GoTo brokenspire"); yield from rwait(4.0)
    sq = place("square")
    g.set_map_open(True); yield from rwait(1.0)
    f = map_frame(); res["town_map_kind"] = f["kind"]
    if sq and f["kind"] == 2:
        yield from click_logic(None, sq.x, sq.y); yield from rwait(1.5)
        hp = G["pawn"].get_actor_location()
        res["town_teleport"] = {"click": str(g.get_editor_property("last_map_click")), "off_square_m": round(dist2(hp, sq) / 100.0, 1)}
    else: res["town_teleport"] = None
    g.set_map_open(False); ex("rd.MapTeleport off"); ex("rd.RevealMap off"); yield from rwait(0.5)
    # ---- the Escape menu's saves as cards
    made = []
    # (PR #54's review: the test's saves are taken away whatever happens: a failure between left them in the player's Load list)
    try:
        for nm in ("Test12 A", "Test12 B", "Test12 C", "Test12 D"):
            slot = "save_test12_" + nm[-1].lower()          # (the menu lists save_* slots only)
            if g.save_game_now(slot, "test", nm): made.append(slot)
        g.set_menu_open(True); yield from rwait(0.4)
        lines = [str(l) for l in g.get_menu_lines()]
        g.activate_menu_line(next(i for i, l in enumerate(lines) if l.startswith("button|Save the game"))); yield from rwait(0.3)
        lines = [str(l) for l in g.get_menu_lines()]
        g.activate_menu_line(next(i for i, l in enumerate(lines) if l.startswith("choice|Save over"))); yield from rwait(0.6)
        boxes = [[float(x) for x in str(s).split("|")] for s in g.get_menu_boxes()]
        lines4 = [str(l) for l in g.get_menu_lines()]
        cols = len(set(round(bx[0]) for bx in boxes[:-1])); rows = len(set(round(bx[1]) for bx in boxes[:-1]))
        shot("l12_save_grid", "1280x720"); yield from rwait(1.2)
        # (the keys: right a card, down a row)
        g.move_menu_grid(1, 0); c_r = g.get_menu_cursor(); g.move_menu_grid(0, 1); c_d = g.get_menu_cursor()
        # (a click on the third card, "Test12 ..." (the first is "a new save"))
        pick = next((i for i, l in enumerate(lines4) if "Test12" in l), -1)
        bx = boxes[pick] if pick >= 0 else None
        why4 = (yield from slate_click(((bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2), False)) if bx else "no card"
        res["grid"] = {"page": 4, "cards": len(boxes) - 1, "columns": cols, "rows": rows, "lines": lines4[:6], "cursor_right": c_r, "cursor_down": c_d,
                       "slate": why4, "after_page": g.get_menu_page(), "last_action": str(g.get_editor_property("last_menu_action")), "picked_line": lines4[pick] if pick >= 0 else None}
        # (the Load page as cards too)
        g.set_menu_open(False); yield from rwait(0.3); g.set_menu_open(True); yield from rwait(0.3)
        lines = [str(l) for l in g.get_menu_lines()]
        g.activate_menu_line(next(i for i, l in enumerate(lines) if l.startswith("button|Load a game"))); yield from rwait(0.6)
        lb = [[float(x) for x in str(s).split("|")] for s in g.get_menu_boxes()]
        res["load_grid"] = {"cards": len(lb) - 1, "columns": len(set(round(bx[0]) for bx in lb[:-1])), "grid_page": bool(g.is_menu_grid_page())}
        shot("l12_load_grid", "1280x720"); yield from rwait(1.2)
    finally:
        try: g.set_menu_open(False)
        except Exception: pass
        for s in made: GS.delete_game_in_slot(s, 0)
    yield from rwait(0.3)
    quiet(False)
    I, M, P, W, D, TR, TP = res["inventory"], res["map"], res["pick"], res["wheel"], res["drag"], res["travel_click"], res["teleport"]
    ok = (I["gold"] >= 123 and I["icon_drawn"]
          and M["frame_kind"] == 1 and M["pointer_up"] and M["edge_drawn"]
          and P["hover"] == P["brokenspire_id"] and P["centre_far"] > 40 and P["after_keys_hover"] != P["brokenspire_id"]
          and res["sea"] is not None and res["sea"]["click"].startswith("refused") and res["sea"]["moved_m"] < 1 and res["sea"]["water"] == 1
          and W["k_after"] > W["k_before"] and W["moved_under_pointer_m"] <= 3 * W["m_a_pixel"]
          and D["moved_m"] > 50 and not D["clicked"]
          and TR["last_click"].startswith("travelled") and not TR["map_open"] and not res["pointer_after"]
          and TP["refused"].startswith("refused: reveal") and TP["teleports"] == 1 and TP["off_target_m"] < 25 and not TP["map_open"]
          and res["town_teleport"] is not None and res["town_teleport"]["click"].startswith("teleported") and res["town_teleport"]["off_square_m"] < 6
          and res["grid"]["columns"] == 3 and res["grid"]["rows"] >= 2 and res["grid"]["cursor_right"] == 1 and res["grid"]["cursor_down"] == 4
          and res["grid"]["after_page"] == 3 and res["grid"]["last_action"].startswith("over:")
          and res["load_grid"]["grid_page"] and res["load_grid"]["columns"] == 3)
    step_result("list12", ok, **res)


# ------------------------------------------------------------------------------------------------ places, monsters
def places_near(x, y, r):
    out = []
    for l in G["gen"].get_wild_places_near(V(x * 100.0, y * 100.0, 0), r):
        p = str(l).split("|"); out.append({"id": int(p[0]), "kind": p[1], "name": p[2], "x": float(p[3]), "y": float(p[4]), "h": float(p[5]), "tier": int(p[6]), "found": int(p[7])})
    return out
def step_places():
    g = G["gen"]; res = {"visits": []}; quiet(True)
    yield from wait_ready(90)
    near = [p for p in places_near(0, 0, 30000) if p["kind"] not in ("town", "city")]
    res["census"] = {k: sum(1 for p in near if p["kind"] == k) for k in sorted(set(p["kind"] for p in near))}
    want = []
    for k in ("camp", "ruins", "ritual", "house", "village", "cave", "lair", "spawn"):
        c = [p for p in near if p["kind"] == k]
        if c: want.append(min(c, key=lambda p: math.hypot(p["x"], p["y"])))
    found = []
    for p in want:
        g.wild_put_her(p["x"] - 45.0, p["y"]); yield from wait_chunks(30, 50); yield from rwait(0.6)
        # (to it: 45 m off, then beside it)
        hover = sample(p["x"] - 20.0, p["y"])
        G["pawn"].set_actor_location(V((p["x"] - 20.0) * 100.0, p["y"] * 100.0, hover["z"] + 120.0), False, True)
        yield from rwait(1.2)
        now_found = [q for q in places_near(p["x"], p["y"], 5) if q["id"] == p["id"]]
        cs = chunks(); cm = g.get_editor_property("wild_chunk_m")
        mine = [c for c in cs if c["x"] == math.floor(p["x"] / cm) and c["y"] == math.floor(p["y"] / cm)]
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-10, yaw=0.0)); yield from rwait(0.5)
        shot("place_" + p["kind"], "1280x720"); yield from rwait(1.2)
        v = {"kind": p["kind"], "name": p["name"], "found": bool(now_found and now_found[0]["found"]), "props": mine[0]["props"] if mine else -1, "monsters": mine[0]["monsters"] if mine else -1}
        if p["kind"] in ("lair", "spawn") and v["monsters"] > 0:
            # (its monsters notice her and come at her over open ground)
            quiet(False); yield from wait(0.5)
            def nearest():
                d = 1e9
                for m in g.get_monsters():
                    if m and not m.is_dead(): d = min(d, dist2(m.get_actor_location(), G["pawn"].get_actor_location()))
                return d
            d0 = nearest(); yield from wait(5.0); d1 = nearest()
            v["monster_m"] = [round(d0 / 100.0, 1), round(d1 / 100.0, 1)]
            v["aggro"] = g.is_wild_combat()
            quiet(True); cb().set_health(cb().get_max_health())
        res["visits"].append(v)
        if v["found"]: found.append(p)
    G["found_places"] = found
    # (a monster killed stays dead when its chunk is made again: one of the spawn point's killed, the chunks dropped and made
    # again round it; the lair (the travel step's) is left alone. They were made again in full, gold and counters and all)
    sp = [p for p in want if p["kind"] == "spawn"]
    if sp:
        p = sp[0]
        def at_place():
            return [m for m in g.get_monsters() if m and not m.is_dead() and dist2(m.get_actor_location(), V(p["x"] * 100.0, p["y"] * 100.0, 0)) < 2500.0]
        g.wild_drop_all(); g.wild_put_her(p["x"] - 45.0, p["y"]); yield from wait_chunks(30, 50); yield from rwait(0.8)
        n0 = len(at_place())
        if n0: at_place()[0].apply_damage(1e7, G["pawn"]); yield from rwait(1.0)
        g.wild_drop_all(); g.wild_put_her(p["x"] - 45.0, p["y"]); yield from wait_chunks(30, 50); yield from rwait(0.8)
        res["killed_stays"] = {"place": p["name"], "before": n0, "after": len(at_place())}
    quiet(False)
    chase = [v for v in res["visits"] if "monster_m" in v]
    ok = len(want) >= 6 and all(v["found"] for v in res["visits"]) and all(v["props"] > 0 for v in res["visits"]) and (not chase or all(v["monster_m"][1] < v["monster_m"][0] for v in chase)) \
        and (not sp or (res["killed_stays"]["before"] >= 2 and res["killed_stays"]["after"] == res["killed_stays"]["before"] - 1))
    step_result("places", ok, **res)
def dist2(a, b): return math.hypot(a.x - b.x, a.y - b.y)
def step_wild25():
    """the rebalance to tier 25 (910): the monsters met in the wilds by the tiers of the roads, Brokenspire to Heaven: lairs and
    spawn points of six tiers (round 2, 7, 12, 17, 22, 25) visited; every monster there is of its place's tier and of a kind
    whose wild band holds it (the castle's kinds in 1-10, the War Engine's 11-15, the drowned 16-20, the casters 21-25, the
    defenders 23-25), and the kinds change along the way"""
    g = G["gen"]; res = {"visits": []}; quiet(True)
    yield from wait_ready(90)
    band = {str(d.name): (d.wild_tier_min, d.wild_tier_max) for d in g.get_editor_property("monsters")}
    res["bands"] = {k: v for k, v in band.items() if v[1] > 0 and v[0] < 99}
    T = towns(); cand = []
    for tn in ("Brokenspire", "Vel Morrath", "Ashenreach", "Graymourne", "Kethrys Spire", "Heaven"):
        t = T.get(tn)
        if not t: continue
        for p in places_near(t["x"], t["y"], 25000):
            if p["kind"] in ("lair", "spawn") and all(q["id"] != p["id"] for q in cand): cand.append(p)
    res["tiers_found"] = sorted({p["tier"] for p in cand})
    picks = []
    for want in (2, 7, 12, 17, 22, 25):
        c = sorted(cand, key=lambda p: (abs(p["tier"] - want), p["id"]))
        if c and c[0] not in picks: picks.append(c[0])
    for p in picks:
        g.wild_drop_all(); g.wild_put_her(p["x"] - 45.0, p["y"]); yield from wait_chunks(30, 50); yield from rwait(1.0)
        at = V(p["x"] * 100.0, p["y"] * 100.0, 0)
        ms = [m for m in g.get_monsters() if m and not m.is_dead() and not m.is_ally() and dist2(m.get_actor_location(), at) < 4000.0]
        kinds = sorted({str(m.monster_name) for m in ms})
        v = {"name": p["name"], "kind": p["kind"], "tier": p["tier"], "monsters": len(ms), "kinds": kinds, "tiers": sorted({m.tier for m in ms}),
             "out_of_band": [k for k in kinds if not (band.get(k, (0, 0))[0] <= p["tier"] <= band.get(k, (0, 0))[1])],
             "hp": round(sum(m.get_max_health() for m in ms) / max(len(ms), 1))}
        res["visits"].append(v)
    g.wild_drop_all(); g.wild_put_her(0.0, 0.0); yield from wait_chunks(30, 40)
    quiet(False)
    vs = [v for v in res["visits"] if v["monsters"] > 0]
    ok = (len(res["visits"]) >= 5 and len(vs) >= 5 and all(not v["out_of_band"] and v["tiers"] == [v["tier"]] for v in vs)
          and max(v["tier"] for v in vs) >= 20 and len({tuple(v["kinds"]) for v in vs}) >= 4)
    step_result("wild25", ok, **res)


def step_secondary9():
    """the sixth phase's materials and the water walk in the wilds (911, RD/RDSecondary.cpp): a ruin's, ritual site's or cave's
    Hallowed Stone lies at it, F takes it, and it is not laid again when its chunk is made again; the wilds' monsters drop Seraph
    Feathers (the lairs' monsters killed: their feathers counted against the kills); the Martial Artist walks on a lake: put on
    its shore facing it, Water Walk made, she runs over the water at its face (never under it) for its length, then is off it"""
    g = G["gen"]; res = {}; quiet(True)
    yield from wait_ready(90)
    stone = str(g.get_editor_property("hallowed_stone_item")); feather = str(g.get_editor_property("seraph_feather_item"))
    def piles_near(x, y, r_m, thing):
        out = []
        for p in g.get_editor_property("loot_piles"):
            if not p or not unreal.SystemLibrary.is_valid(p): continue
            l = p.get_actor_location()
            if math.hypot(l.x / 100.0 - x, l.y / 100.0 - y) < r_m and thing in [str(t) for t in p.things]: out.append(p)
        return out
    # ---- a Hallowed Stone
    near = [p for p in places_near(0, 0, 25000) if p["kind"] in ("ruins", "ritual", "cave")]
    st = {"places": len(near)}
    if near:
        p = min(near, key=lambda q: math.hypot(q["x"], q["y"]))
        g.wild_drop_all(); g.wild_put_her(p["x"] - 6.0, p["y"]); yield from wait_chunks(30, 50); yield from rwait(1.0)
        ps = piles_near(p["x"], p["y"], 15.0, stone); st["place"] = p["name"]; st["piles"] = len(ps)
        if ps:
            at = ps[0].get_actor_location()
            G["pawn"].set_actor_location(V(at.x - 90.0, at.y, at.z + 100.0), False, True); yield from rwait(0.6)
            n0 = cb().get_item_count(stone)
            yield from press("F"); yield from rwait(0.6)
            st["taken"] = cb().get_item_count(stone) - n0
            g.wild_drop_all(); g.wild_put_her(p["x"] - 6.0, p["y"]); yield from wait_chunks(30, 50); yield from rwait(1.0)
            st["laid_again"] = len(piles_near(p["x"], p["y"], 15.0, stone))
    res["stone"] = st
    # ---- Seraph Feathers from the lairs' monsters
    fe = {"kills": 0, "feathers": 0, "lairs": []}
    lairs = sorted([p for p in places_near(0, 0, 25000) if p["kind"] in ("lair", "spawn")], key=lambda q: math.hypot(q["x"], q["y"]))
    for p in lairs[:3]:
        g.wild_drop_all(); g.wild_put_her(p["x"] - 45.0, p["y"]); yield from wait_chunks(30, 50); yield from rwait(1.0)
        at = V(p["x"] * 100.0, p["y"] * 100.0, 0)
        ms = [m for m in g.get_monsters() if m and not m.is_dead() and not m.is_ally() and dist2(m.get_actor_location(), at) < 4000.0]
        f0 = len(piles_near(p["x"], p["y"], 45.0, feather))
        for m in ms: m.apply_damage(1e7, G["pawn"])
        yield from rwait(1.0)
        got = len(piles_near(p["x"], p["y"], 45.0, feather)) - f0
        fe["kills"] += len(ms); fe["feathers"] += got; fe["lairs"].append({"name": p["name"], "kills": len(ms), "feathers": got})
        cb().set_health(cb().get_max_health())
        if fe["feathers"] >= 2: break
    res["feathers"] = fe
    # ---- the water walk: the Martial Artist on the nearest lake's shore
    ww = {}
    lakes = []
    for f in g.get_wild_feature_lines():
        q = str(f).split("|")
        if q[0] == "lake": lakes.append((float(q[1]), float(q[2]), float(q[3])))
    T = towns(); keep = [(t["x"], t["y"]) for t in T.values()]
    lakes = [k for k in lakes if all(math.hypot(k[0] - x, k[1] - y) > 2500 for x, y in keep)]
    lakes.sort(key=lambda k: math.hypot(k[0], k[1]))
    if lakes:
        lx, ly, lr = lakes[0]; ww["lake"] = [round(lx), round(ly), round(lr)]
        # (out from its middle until dry land, ten rays: the first shore with water 12 m on toward the middle)
        shore = None
        for k in range(10):
            a = k * math.pi / 5.0; dx, dy = math.cos(a), math.sin(a)
            for d in range(int(lr * 0.4), int(lr * 1.6), 5):
                s_ = sample(lx + dx * d, ly + dy * d)
                if int(s_["water"]) == 0 and s_["lava"] < 0.5:
                    inner = sample(lx + dx * (d - 14), ly + dy * (d - 14))
                    if int(inner["water"]) != 0 and inner["water_m"] > inner["h"] + 0.5: shore = (lx + dx * (d + 2), ly + dy * (d + 2), -dx, -dy)
                    break
            if shore: break
        ww["shore"] = [round(shore[0]), round(shore[1])] if shore else None
        if shore:
            if str(g.get_editor_property("current_hero")) != "MartialArtist": g.switch_hero("MartialArtist"); yield from rwait(1.0); refresh(); g = G["gen"]
            t0 = time.time()
            while cb() is None and time.time() - t0 < 10: yield; refresh()
            g.wild_drop_all(); g.wild_put_her(shore[0], shore[1]); yield from wait_chunks(30, 50); yield from rwait(1.0)
            yaw = math.degrees(math.atan2(shore[3], shore[2]))
            G["pawn"].set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw), True); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-10, yaw=yaw))
            c = cb(); c.set_secondary_rank("WaterWalk", 1, "None"); yield from rwait(0.3)
            ww["used"] = c.use_secondary("WaterWalk"); ww["says"] = str(c.message)
            zs = []; p0 = G["pawn"].get_actor_location(); hh = G["pawn"].capsule_component.get_scaled_capsule_half_height()
            t0 = time.time()
            while time.time() - t0 < 6.0:
                G["pawn"].add_movement_input(V(shore[2], shore[3], 0), 1.0, False)
                l = G["pawn"].get_actor_location(); s_ = sample(l.x / 100.0, l.y / 100.0)
                if c.is_secondary_on("WaterWalk") and int(s_["water"]) != 0 and s_["water_m"] > s_["h"] + 0.3: zs.append(round((l.z - hh) - (s_["z"] + (s_["water_m"] - s_["h"]) * 100.0), 1))          # (her feet over the water's face)
                yield
            ww.update({"walked_cm": round(c.last_move_length), "moved_cm": round(dist2(G["pawn"].get_actor_location(), p0)), "over_water_samples": len(zs),
                       "feet_over_water_cm": [min(zs), max(zs)] if zs else None, "on_after": c.is_secondary_on("WaterWalk")})
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-15, yaw=yaw + 180)); yield from rwait(0.3)
    res["water"] = ww
    g.wild_drop_all(); g.wild_put_her(0.0, 0.0); yield from wait_chunks(30, 40)
    if str(g.get_editor_property("current_hero")) != "Warrior": g.switch_hero("Warrior"); yield from rwait(1.0); refresh()
    quiet(False)
    ok_s = st.get("piles", 0) >= 1 and st.get("taken") == 1 and st.get("laid_again") == 0
    ok_f = fe["kills"] >= 3 and fe["feathers"] >= 1
    ok_w = bool(ww.get("used")) and ww.get("walked_cm", 0) >= 800 and ww.get("over_water_samples", 0) > 20 and ww["feet_over_water_cm"] and ww["feet_over_water_cm"][0] > -25 and not ww.get("on_after")
    step_result("secondary9", ok_s and ok_f and ok_w, stone_ok=ok_s, feathers_ok=ok_f, water_ok=ok_w, **res)


def step_poi7():
    """the seventh phase's points of interest (912, RD/RDWildPoi.cpp, FRDWildWorld::PoisIn): (a) on the world's model, along
    eight lines out of Brokenspire and six through other regions (2 km each), every point of interest or place within 75 m
    of the way: the seconds between them at her run of 3.5 m/s (most under 40), many kinds, each line its region's mix;
    (b) in play, a 150 s run off the roads: what met her (something within 45 m, a director's encounter) never more than 40 s
    apart; (c) each use made with F where it stands: a pile taken, a blessing, a rest, a story, a milestone's ways"""
    g = G["gen"]; res = {}; quiet(True)
    yield from wait_ready(90)
    RUN = 3.5
    def along(x0, y0, dx, dy, length):
        seen = {}
        for k in range(0, int(length) + 1, 250):
            for p in places_near(x0 + dx * k, y0 + dy * k, 320):
                t = (p["x"] - x0) * dx + (p["y"] - y0) * dy; d = abs((p["x"] - x0) * dy - (p["y"] - y0) * dx)
                if -30 <= t <= length + 30 and d <= 75: seen[p["id"]] = (t, p["kind"])
                if d <= 400: CANDS[p["id"]] = p
        ts = sorted(v[0] for v in seen.values())
        gaps = [b - a for a, b in zip([0.0] + ts, ts + [length])]
        sec = sorted(x / RUN for x in gaps)
        return {"n": len(ts), "kinds": sorted({v[1] for v in seen.values()}), "p50_s": round(sec[len(sec) // 2], 1) if sec else None,
                "p90_s": round(sec[int(len(sec) * 0.9)], 1) if sec else None, "max_s": round(sec[-1], 1) if sec else None, "secs": sec}
    lines = {}; CANDS = {}
    T = towns(); b = T.get("Brokenspire", {"x": 0.0, "y": 0.0})
    for k in range(8):
        a = k * math.pi / 4.0; dx, dy = math.cos(a), math.sin(a)
        lines[f"brokenspire_{k * 45}"] = along(b["x"] + dx * 1200, b["y"] + dy * 1200, dx, dy, 2000.0)
    bl = {}
    for l in g.get_wild_biome_lines():
        p = str(l).split("|"); bl[p[0]] = (float(p[2]), float(p[3]))
    for bn in ("marshes", "pine forests", "mountains", "savannahs", "tundras", "volcanoes"):
        if bn in bl: lines[bn] = along(bl[bn][0] - 1000, bl[bn][1], 1.0, 0.0, 2000.0)
    # (PR #36's review: the cells north of 165.8 km and east of 95.8 km had none (11 bits a cell): a line from each town there)
    for tn, t in T.items():
        if t["x"] > 165000 or t["y"] > 95000:
            d_ = math.hypot(b["x"] - t["x"], b["y"] - t["y"]) or 1.0; dx, dy = (b["x"] - t["x"]) / d_, (b["y"] - t["y"]) / d_
            lines["from_" + tn.lower().replace(" ", "_")] = along(t["x"] + dx * 1500, t["y"] + dy * 1500, dx, dy, 2000.0)
    allsec = sorted(s for v in lines.values() for s in v["secs"])
    kinds = sorted({k for v in lines.values() for k in v["kinds"]})
    for v in lines.values(): v.pop("secs")
    res["model"] = {"lines": lines, "p50_s": round(allsec[len(allsec) // 2], 1), "p90_s": round(allsec[int(len(allsec) * 0.9)], 1), "max_s": round(allsec[-1], 1), "kinds": kinds}
    # ---- (b) a run in play
    x0, y0 = b["x"] - 1800.0, b["y"] + 900.0
    g.wild_drop_all(); g.wild_put_her(x0, y0); yield from wait_chunks(30, 50); yield from rwait(1.0)
    n0 = len([str(l) for l in g.get_wild_encounter_lines()]) - 1
    t0 = now()
    yield from run_her((-0.8, 0.6), 150.0)
    ev = [str(l).split("|") for l in g.get_wild_encounter_lines()][n0:-1]
    times = [float(e[0]) for e in ev if float(e[0]) >= t0]
    gaps = [round(b_ - a_, 1) for a_, b_ in zip([t0] + times, times + [now()])]
    state = str(g.get_wild_encounter_lines()[-1]).split("|")
    res["run"] = {"seconds": round(now() - t0, 1), "events": len(times), "met": sum(1 for e in ev if e[1] == "met"), "near": sorted({e[2] for e in ev if e[1] == "near"}),
                  "max_gap_s": max(gaps) if gaps else None, "gaps": gaps[:40], "state": state, "moved_m": round(math.hypot(G["pawn"].get_actor_location().x / 100 - x0, G["pawn"].get_actor_location().y / 100 - y0))}
    # ---- (c) the uses
    uses = {}
    near = [p for p in CANDS.values() if p["kind"] in ("abandoned_camp", "lost_body", "herb_patch", "ore_vein", "grave", "cairn", "wayshrine", "milestone", "broken_wagon", "standing_stones", "hermit_hut", "ruined_wall")]
    want = {}
    for p in sorted(near, key=lambda q: math.hypot(q["x"] - b["x"], q["y"] - b["y"])):
        use = {"abandoned_camp": "loot", "lost_body": "loot", "broken_wagon": "loot", "herb_patch": "loot", "ore_vein": "loot", "grave": "lore", "cairn": "lore", "ruined_wall": "lore",
               "wayshrine": "heal", "hermit_hut": "heal", "milestone": "milestone", "standing_stones": "buff"}[p["kind"]]
        if use not in want: want[use] = p
    for use, p in want.items():
        g.wild_drop_all(); g.wild_put_her(p["x"] - 6.0, p["y"]); yield from wait_chunks(30, 50); yield from rwait(1.0)
        c = cb()
        if use == "loot":
            piles = [x for x in g.get_editor_property("loot_piles") if x and unreal.SystemLibrary.is_valid(x) and math.hypot(x.get_actor_location().x / 100 - p["x"], x.get_actor_location().y / 100 - p["y"]) < 6]
            if not piles: uses[use] = {"kind": p["kind"], "piles": 0}; continue
            at = piles[0].get_actor_location(); things = [str(t) for t in piles[0].things]
            G["pawn"].set_actor_location(V(at.x - 90.0, at.y, at.z + 100.0), False, True); yield from rwait(0.5)
            n_before = {t: c.get_item_count(t) for t in set(things)}
            yield from press("F"); yield from rwait(0.6)
            uses[use] = {"kind": p["kind"], "things": things, "gained": {t: c.get_item_count(t) - n_before[t] for t in n_before}}
            g.wild_drop_all(); g.wild_put_her(p["x"] - 6.0, p["y"]); yield from wait_chunks(30, 50); yield from rwait(1.0)
            uses[use]["laid_again"] = len([x for x in g.get_editor_property("loot_piles") if x and unreal.SystemLibrary.is_valid(x) and math.hypot(x.get_actor_location().x / 100 - p["x"], x.get_actor_location().y / 100 - p["y"]) < 6])
        else:
            z = G["pawn"].get_actor_location().z
            G["pawn"].set_actor_location(V(p["x"] * 100.0 - 150.0, p["y"] * 100.0, z), False, True); yield from rwait(0.5)
            if use == "heal": c.set_health(c.get_max_health() * 0.5)
            prompt = str(g.describe_nearest(G["pawn"].get_actor_location(), 400.0))
            yield from press("F"); yield from rwait(0.5)
            uses[use] = {"kind": p["kind"], "prompt": prompt, "says": str(c.message), "blessing": str(c.get_blessing()), "hp_share": round(c.get_health() / c.get_max_health(), 2)}
    res["uses"] = uses
    g.wild_drop_all(); g.wild_put_her(b["x"], b["y"]); yield from wait_chunks(30, 40)
    quiet(False)
    m = res["model"]; r = res["run"]
    # (the world's spacing alone: half the gaps under 40 s, every line some; the 40 s itself is play's, with the director (b))
    ok_m = m["p50_s"] <= 40 and len(m["kinds"]) >= 15 and all(v["n"] >= 5 for v in m["lines"].values()) and sum(1 for v in m["lines"].values() if len(v["kinds"]) >= 4) >= len(m["lines"]) - 2
    ok_r = r["events"] >= 4 and r["max_gap_s"] is not None and r["max_gap_s"] <= 40.5
    ok_u = (uses.get("loot", {}).get("things") and all(v > 0 for v in uses["loot"]["gained"].values()) and uses["loot"].get("laid_again") == 0
            and ("lore" not in uses or len(uses["lore"]["says"]) > 20) and ("milestone" not in uses or "km" in uses["milestone"]["says"])
            and ("heal" not in uses or uses["heal"]["hp_share"] == 1.0) and ("buff" not in uses or uses["buff"]["blessing"] not in ("", "None"))
            and len(uses) >= 3)
    step_result("poi7", ok_m and ok_r and ok_u, model_ok=ok_m, run_ok=ok_r, uses_ok=bool(ok_u), **res)


def step_horse9():
    """the ridable horse (913, RD/RDHorse.cpp; the list of 2026-11-08b's eighth phase): Brokenspire's stable by the gate with the
    stable's horse standing at it; bought there (its price in gold taken, hers kept in the game instance) and come to her side;
    F beside it mounts her (her pelvis on its saddle, her hero's rider clip playing, no blow from the saddle); on the plains she
    runs HorseDef.SpeedMul times as fast mounted as on foot, the horse galloping under her; F gets her off (her speed back);
    pictures of her riding from the side and from behind"""
    g = G["gen"]; res = {}; quiet(True)
    yield from wait_ready(90)
    def hs():
        p = str(g.get_horse_state()).split("|")
        k = ["owned", "spawned", "mounted", "x", "y", "z", "clip", "rate", "speed", "saddle_z", "pelvis_z", "rider", "stable_horse", "pelvis_off_xy"]
        return {a: (b if a in ("clip", "rider") else float(b)) for a, b in zip(k, p)}
    # ---- the stable
    st = [s for s in spots() if s["kind"] == "stable"]
    res["stable_spots"] = len(st)
    if not st: quiet(False); step_result("horse9", False, **res); return
    at = st[0]["at"]
    # (on its town side: toward the town's middle, away from the wall and the gate's guards)
    n_ = math.hypot(at.x, at.y) or 1.0
    G["pawn"].set_actor_location(V(at.x - at.x / n_ * 250.0, at.y - at.y / n_ * 250.0, at.z + 100.0), False, True); yield from rwait(1.5)
    res["stable_at"] = [round(at.x), round(at.y)]
    res["before"] = hs(); res["prompt"] = str(g.describe_nearest(G["pawn"].get_actor_location(), 450.0))
    g.add_gold(5000, "the test"); g0 = g.get_gold(); price = g.horse_price_now()
    g.open_town_panel("stable", -1); yield from rwait(0.3)
    lines = [str(l) for l in g.get_town_panel_lines()]
    k = next((i for i, l in enumerate(lines) if l.startswith("buyhorse|")), -1)
    res["bought"] = g.activate_town_entry(k) if k >= 0 else False; yield from rwait(1.0)
    res["gold_taken"] = g0 - g.get_gold(); res["price"] = price; res["after_buy"] = hs()
    res["gi_owned"] = G["gi"].get_editor_property("horse_owned")
    try: g.close_town_panel()
    except Exception: pass
    # ---- out on the plains: on foot, then mounted
    xy = clear_spot("plains"); g.wild_put_her(*xy); yield from wait_chunks(30, 50); yield from rwait(1.0)
    g.call_horse(); yield from rwait(0.8)
    # (on foot as mounted, once up to speed: the last 2.5 s of a 4 s run (the list of 2026-11-12's run read 3.25 m/s over the whole
    # run, its start in it, against 19.44 mounted measured up to speed: 5.98 for 5.5))
    t0 = time.time(); p0 = None; tf = 0.0
    for _ in run_her((1.0, 0.3), 4.0):
        if p0 is None and time.time() - t0 >= 1.5: p0 = G["pawn"].get_actor_location(); tf = time.time()
        yield
    p1 = G["pawn"].get_actor_location()
    foot = math.hypot(p1.x - p0.x, p1.y - p0.y) / 100.0 / max(time.time() - tf, 0.1) if p0 else 0.0
    yield from rwait(0.6)
    g.call_horse(); yield from rwait(0.5)
    hp_ = hs(); d_ = math.hypot(hp_["x"] - G["pawn"].get_actor_location().x, hp_["y"] - G["pawn"].get_actor_location().y)
    # (the list of 2026-11-10, "the player can walk through the horse": she walks straight at its middle for 3 s and stops at its
    # side; the nearest she comes to its middle is kept (its box's half width and her capsule's radius, about 60 cm); then back)
    hz = g.get_editor_property("horse")
    res["blocking_before_mount"] = hz.is_blocking() if hz else None
    q0 = G["pawn"].get_actor_location(); hc = V(hp_["x"], hp_["y"], q0.z)
    dmin = 1e9; t0 = time.time()
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-12, yaw=math.degrees(math.atan2(hc.y - q0.y, hc.x - q0.x))))
    while time.time() - t0 < 3.0:
        q = G["pawn"].get_actor_location(); dv = V(hc.x - q.x, hc.y - q.y, 0.0)
        G["pawn"].add_movement_input(dv, 1.0); dmin = min(dmin, math.hypot(dv.x, dv.y)); yield
    res["walk_into_horse"] = {"start_cm": round(d_), "nearest_cm": round(dmin)}
    G["pawn"].set_actor_location(q0, False, True); yield from rwait(0.5)
    res["horse_at_cm"] = round(d_); res["mount_prompt"] = str(g.describe_nearest(G["pawn"].get_actor_location(), 400.0))
    yield from press("F"); yield from rwait(1.0)
    m = hs(); res["mounted"] = m; res["attack_refused"] = not cb().start_attack()
    hz = g.get_editor_property("horse"); res["blocking_mounted"] = hz.is_blocking() if hz else None
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=G["pawn"].get_actor_rotation().yaw + 90)); yield from rwait(0.6); shot("horse_idle", "1280x720"); yield from rwait(1.0)
    # (her speed mounted once the horse is up to it: the last 3 s of a 6 s run (the list of 2026-11-10: at 5.5 times her speed the
    # gallop takes a couple of seconds to reach it; over the whole run it read 5.04))
    run = []
    t0 = time.time(); pm = None; tm = 0.0
    for _ in run_her((1.0, 0.3), 6.0):
        if time.time() - t0 > 2.0 and len(run) < 6: run.append(hs())
        if pm is None and time.time() - t0 >= 3.0: pm = G["pawn"].get_actor_location(); tm = time.time()
        yield
    p1 = G["pawn"].get_actor_location(); t1 = time.time()
    mounted = math.hypot(p1.x - pm.x, p1.y - pm.y) / 100.0 / max(t1 - tm, 0.1) if pm else 0.0
    res["riding"] = run[-1] if run else None
    # (pictures: from the side as she gallops, then from behind)
    for nm, yawoff in (("horse_side", 90.0), ("horse_back", 0.0)):
        t0 = time.time()
        while time.time() - t0 < 1.2: G["pawn"].add_movement_input(V(1.0, 0.3, 0.0), 1.0); yield
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-10, yaw=math.degrees(math.atan2(0.3, 1.0)) + yawoff))
        G["pawn"].add_movement_input(V(1.0, 0.3, 0.0), 1.0); shot(nm, "1280x720"); yield from rwait(1.2)
    res["speed_m_s"] = {"foot": round(foot, 2), "mounted": round(mounted, 2), "ratio": round(mounted / max(foot, 0.01), 2), "want": round(g.get_editor_property("horse_def").speed_mul, 2)}
    yield from press("F"); yield from rwait(0.8)
    res["after_dismount"] = hs()
    # (away from the horse left beside her: run the way it stands, its box (on once she is 2 m clear) stopped her (2026-11-10, the
    # Tripo horse set down the way she ran: 0.03 m/s))
    ha = res["after_dismount"]; p0 = G["pawn"].get_actor_location()
    aw = (p0.x - ha["x"], p0.y - ha["y"]); n_ = math.hypot(*aw) or 1.0
    yield from run_her((aw[0] / n_, aw[1] / n_), 3.0); p1 = G["pawn"].get_actor_location()
    # (her own speed back, not the saddle's (5.5 times): within a fifth of her speed on foot, the way away from the horse is other ground
    # than the way she was measured on (2.93 against 3.46 m/s uphill))
    res["speed_m_s"]["after"] = round(math.hypot(p1.x - p0.x, p1.y - p0.y) / 100.0 / 3.0, 2)
    # (PR #37's review: a death in the saddle gets her off and keeps her death clip (it was stopped with the rider's: she stood up))
    g.call_horse(); yield from rwait(0.5); g.mount_horse(); yield from rwait(0.8)
    c_ = cb(); c_.apply_damage(c_.get_health() * 10.0 + 500.0, None); yield from wait(1.2)
    ai = G["pawn"].mesh.get_anim_instance()
    res["death"] = {"dead": c_.is_dead(), "mounted": hs()["mounted"], "montage": bool(ai and ai.is_any_montage_playing())}
    t0 = time.time()
    while cb().is_dead() and time.time() - t0 < 20: yield
    yield from rwait(1.0)
    g.wild_drop_all(); g.wild_put_her(0.0, 0.0); yield from wait_chunks(30, 40)
    quiet(False)
    b = res["before"]; a = res["after_buy"]; mt = res["mounted"]; rd = res["riding"] or {}; sp = res["speed_m_s"]
    ok = (b["stable_horse"] == 1 and b["owned"] == 0 and "horse" in res["prompt"] and res["bought"] and res["gold_taken"] == res["price"] > 0
          and a["owned"] == 1 and a["spawned"] == 1 and res["gi_owned"]
          and mt["mounted"] == 1 and abs(mt["pelvis_z"] - mt["saddle_z"] - 14.0) < 15 and mt["pelvis_off_xy"] < 15 and (rd.get("pelvis_off_xy", 99) < 15) and mt["rider"] not in ("", "None") and res["attack_refused"]
          and rd.get("clip") == "run" and abs(sp["ratio"] - sp["want"]) < 0.35 and res["after_dismount"]["mounted"] == 0 and abs(sp["after"] - sp["foot"]) < max(0.4, 0.2 * sp["foot"])
          and res["death"]["dead"] and res["death"]["mounted"] == 0 and res["death"]["montage"]
          # (the list of 2026-11-10: blocked by it standing, not while ridden; at least five times her speed)
          and res["blocking_before_mount"] is True and res["blocking_mounted"] is False and res["walk_into_horse"]["nearest_cm"] > 35
          and sp["ratio"] >= 5.0)
    step_result("horse9", ok, **res)


def win_min(ts, vals, half):
    """each sample's least value over the samples within `half` seconds of it (a sliding window: two pointers and a deque of
    candidates, so a long record is not walked once a sample)"""
    from collections import deque
    out = [0.0] * len(vals); q = deque(); hi = 0; lo = 0
    for i in range(len(vals)):
        while hi < len(vals) and ts[hi] <= ts[i] + half:
            while q and vals[q[-1]] >= vals[hi]: q.pop()
            q.append(hi); hi += 1
        while q and ts[q[0]] < ts[i] - half: q.popleft()
        out[i] = vals[q[0]]
    return out


class _NotMounted(Exception):
    """gait12: the horse was not under her"""


def step_gait12():
    """the horse's gaits (the list of 2026-11-12: "horses when either walking or galloping move in an unnatural manner - redo their
    animations so that they move like real horses"; farm_animals.py's real_gait, RDHorse.cpp's PlayFor): ridden on the plains at
    three speeds (a slow walk, her walk: a canter, her run: the gallop), the horse's clip, its rate and strides a second, and each
    hoof measured in the world: while a hoof is down (its lowest few cm against the horse's own feet) it must not slide (the old
    clips played past their rates' limits and slid 39 % and 69 % of the speed); her rider clip by the gait; pictures from the side.
    Times are the game's: the gallop is measured with the game slowed (its stance lasts 3 frames at 50 a second: PR #55's review,
    at a slower editor's frame rate no two frames would have fallen in one stance)"""
    g = G["gen"]; res = {}; quiet(True)
    yield from wait_ready(90)
    w = G["w"]; gi = G["gi"]; owned0 = gi.get_editor_property("horse_owned")
    # (the owned flag is the game instance's, saved: put back whatever happens (PR #55's review), with the game's speed)
    try:
        gi.set_editor_property("horse_owned", True)
        xy = clear_spot("plains"); g.wild_put_her(*xy); yield from wait_chunks(30, 50); yield from rwait(1.0)
        g.call_horse(); yield from rwait(0.8); g.mount_horse(); yield from rwait(1.0)
        hz = g.get_editor_property("horse")
        res["mounted"] = bool(hz and g.is_mounted())
        if not res["mounted"]: raise _NotMounted()
        body = hz.get_editor_property("body")
        HOOVES = ("hoof_front_l", "hoof_front_r", "hoof_rear_l", "hoof_rear_r")
        hd = g.get_editor_property("horse_def")
        res["def"] = {"canter": bool(hd.canter), "walk_clip": round(hd.walk_clip_speed), "canter_clip": round(hd.canter_clip_speed),
                      "run_clip": round(hd.run_clip_speed), "canter_from": round(hd.canter_from), "gallop_from": round(hd.gallop_from)}
        # (the plains' way: straight on, a little to the side of where the spot finder looked)
        dxy = (1.0, 0.3); n_ = math.hypot(*dxy); dxy = (dxy[0] / n_, dxy[1] / n_)
        def gt(): return unreal.GameplayStatics.get_time_seconds(w)
        def ride(name, scale, run, slow=1.0, sec_up=2.0, sec=3.0, pic=None):
            cb().set_run_mode(run)
            d = V(dxy[0], dxy[1], 0.0)
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-10, yaw=math.degrees(math.atan2(dxy[1], dxy[0]))))
            t0 = time.time(); rows = []; clips = []; shot_done = False
            # (up to speed at the game's own pace, then the measured stretch at `slow`: `sec` seconds of the game's time)
            while time.time() - t0 < sec_up: G["pawn"].add_movement_input(d, scale); yield
            unreal.GameplayStatics.set_global_time_dilation(w, slow)
            g0 = gt()
            while gt() - g0 < sec:
                G["pawn"].add_movement_input(d, scale)
                h = hz.get_actor_location(); vel = G["pawn"].get_velocity()
                rows.append((gt(), h, [body.get_socket_location(b) for b in HOOVES], vel.length(),
                             hz.get_actor_rotation().yaw, math.degrees(math.atan2(vel.y, vel.x))))
                clips.append((str(hz.get_editor_property("clip_now")), hz.get_editor_property("rate_now"), hz.get_strides_a_second(),
                              str(g.get_horse_state()).split("|")[11]))
                yield
            unreal.GameplayStatics.set_global_time_dilation(w, 1.0)
            # (the picture from her side after the measured stretch: the camera turned under the measure would turn her and the horse)
            if pic:
                G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=math.degrees(math.atan2(dxy[1], dxy[0])) + 90.0))
                t1 = time.time()
                while time.time() - t1 < 1.4:
                    G["pawn"].add_movement_input(d, scale)
                    if not shot_done and time.time() - t1 >= 0.6: shot(pic, "1280x720"); shot_done = True
                    yield
            # each hoof: down while within 2 cm of its lowest over the 0.3 s round it, against the horse's feet (the ground under the
            # hoof and under her differ along a ride); its slide between two frames both down, along the horse and across it
            ts = [r[0] for r in rows]
            slides = []; along = []; across = []; downs = 0
            for k in range(len(HOOVES)):
                rel = [r[2][k].z - r[1].z for r in rows]
                lo = win_min(ts, rel, 0.15)
                for i in range(1, len(rows)):
                    if rel[i] < lo[i] + 2.0 and rel[i - 1] < lo[i] + 2.0:
                        dt = ts[i] - ts[i - 1]
                        # (two frames further apart than half the gallop's stance can be two stances: at 16 frames a second the
                        # first run read a hoof's next landing as a slide of the horse's whole speed)
                        if dt <= 0 or dt > 0.035: continue
                        a, b = rows[i - 1][2][k], rows[i][2][k]
                        dx, dy = b.x - a.x, b.y - a.y; yw = math.radians(rows[i][4])
                        slides.append(math.hypot(dx, dy) / dt); downs += 1
                        along.append(abs(dx * math.cos(yw) + dy * math.sin(yw)) / dt); across.append(abs(-dx * math.sin(yw) + dy * math.cos(yw)) / dt)
            offs = sorted(abs((r[4] - r[5] + 180.0) % 360.0 - 180.0) for r in rows if r[3] > 50.0)
            along.sort(); across.sort(); slides.sort()
            sp = sorted(r[3] for r in rows)
            speed = sp[len(sp) // 2] if sp else 0.0
            cn = [c[0] for c in clips]
            main = max(set(cn), key=cn.count) if cn else ""
            rates = sorted(c[1] for c in clips if c[0] == main); st = sorted(c[2] for c in clips if c[0] == main)
            dts = sorted(ts[i] - ts[i - 1] for i in range(1, len(ts)))
            res[name] = {"speed_cm_s": round(speed), "clip": main, "clip_share": round(cn.count(main) / max(len(cn), 1), 2),
                         "rate": round(rates[len(rates) // 2], 2) if rates else None, "strides_a_second": round(st[len(st) // 2], 2) if st else None,
                         "game_speed": slow, "frames": len(rows), "frame_ms_game": round(1000.0 * dts[len(dts) // 2], 1) if dts else None,
                         "hoof_down_pairs": downs,
                         "slide_median_cm_s": round(slides[len(slides) // 2]) if slides else None,
                         "slide_share": round(slides[len(slides) // 2] / max(speed, 1.0), 3) if slides else None,
                         "slide_along_cm_s": round(along[len(along) // 2]) if along else None, "slide_across_cm_s": round(across[len(across) // 2]) if across else None,
                         "facing_off_deg": [round(offs[len(offs) // 2], 1), round(offs[-1], 1)] if offs else None,
                         "rider": max(set(c[3] for c in clips), key=[c[3] for c in clips].count) if clips else ""}
        # (her speeds by the stick's share: Python's move input passes by her character's MoveScale, the walk / run switch's, so the
        # first run's "walk" with the switch off went at her full speed (1944 cm/s); a tenth, a third and the whole of her speed are a
        # walk, her walk (about 5.5 times hers on foot: a canter) and her run)
        yield from ride("walk", 0.1, False)
        yield from ride("canter", 0.33, False, pic="gait12_canter")
        yield from ride("gallop", 1.0, True, slow=0.4, pic="gait12_gallop")
        cb().set_run_mode(False)
        g.dismount_horse(); yield from rwait(0.5)
    except _NotMounted:
        pass
    finally:
        unreal.GameplayStatics.set_global_time_dilation(w, 1.0)
        gi.set_editor_property("horse_owned", owned0)
        if g.is_mounted(): g.dismount_horse()
        quiet(False)
    g.wild_drop_all(); g.wild_put_her(0.0, 0.0); yield from wait_chunks(30, 40)
    ok = res.get("mounted", False)
    if ok:
        wk, c, r = res["walk"], res["canter"], res["gallop"]
        def good(x, clip):
            return (x["clip"] == clip and x["clip_share"] >= 0.9 and x["hoof_down_pairs"] >= 6 and x["slide_share"] is not None and x["slide_share"] < 0.15)
        ok = (res["def"]["canter"] and good(wk, "walk") and good(c, "canter") and good(r, "run")
              # (each near its own rate: the clip made for the speed it is ridden at)
              and 0.6 <= (c["rate"] or 0) <= 1.6 and 0.6 <= (r["rate"] or 0) <= 1.8
              and wk["rider"] == "walk" and c["rider"] == "canter" and r["rider"] == "run")
    step_result("gait12", ok, **res)


def step_ruins12():
    """the list of 2026-11-12's third phase (924 ruins, RD/RDWildRuin12.cpp): "have at least 20 kinds of ruins" and the twenty the
    list names. Every kind among the world's ruins within 150 km of Brokenspire (CountWildRuins); then the nearest ruin of each kind
    (ruins12=<kind>+<kind> for some) visited: she is put 45 m before its front, the chunks round her made, and what was laid read
    (its pieces, where they stand, its containers, its guardians: GetWildRuinLines), its chest found among the wild boxes, a picture
    of it from where she stands, then she is moved to 20 m: a line the HUD showed over the visit names it. It passes when every
    kind is laid with 3 pieces or more, none gone, none standing over the ground by more than its part raised it, none laid to
    collide that stops nothing, its chest, its guards standing (none inside a piece) and the line naming it"""
    g = G["gen"]; res = {"kinds": {}}; quiet(True)
    yield from wait_ready(90)
    kinds = [str(k.get_editor_property("name")) for k in g.get_editor_property("wild_ruin_kinds")]
    res["table"] = len(kinds)
    res["counts"] = {str(l).split("|")[0]: int(str(l).split("|")[1]) for l in g.count_wild_ruins(0.0, 0.0, 150.0)}
    want = G.get("look_only") or kinds
    try:
        for kd in want:
            r = {}
            f = str(g.find_wild_ruin(kd, 0.0, 0.0, 150.0))
            if not f: res["kinds"][kd] = {"found": False}; continue
            rid, cx, cy, yw, nm = f.split("|", 4); rid = int(rid); cx = float(cx); cy = float(cy); yw = float(yw)
            r.update({"found": True, "id": rid, "at_km": [round(cx / 1000.0, 2), round(cy / 1000.0, 2)], "name": nm})
            # (her place: 45 m out before its front (its yaw's way: the rock-cut temple was pictured from behind its rock; at 32 m the
            # castle's keep stood round the camera), else the first way round whose ground is dry, looking at its middle)
            # (and gentle: put on the canyons' terraces by the sand-buried city she fell 12 m and died)
            def gentle(x, y):
                s0 = sample(x, y)
                if s0["water"]: return False
                return all(abs(sample(x + dx, y + dy)["h"] - s0["h"]) < 1.2 for dx, dy in ((3, 0), (-3, 0), (0, 3), (0, -3)))
            spot = None
            for rr in (45.0, 55.0, 40.0):
                for a in [yw + d_ for d_ in (0, 45, -45, 90, -90, 135, -135, 180)]:
                    sx, sy = cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a))
                    if gentle(sx, sy): spot = (sx, sy); break
                if spot: break
            spot = spot or (cx + 45.0, cy)
            msgs = []
            try: cb().set_editor_property("message", "")
            except Exception: pass
            g.wild_put_her(*spot); yield from watching(wait_chunks(30, 50), msgs); yield from watching(rwait(2.0), msgs)
            lines = [str(l).split("|") for l in g.get_wild_ruin_lines()]
            mine = next((p for p in lines if int(p[1]) == rid), None)
            r["laid"] = {"kind": mine[2], "pieces": int(mine[6]), "boxes": int(mine[7]), "guards": int(mine[8])} if mine else None
            # (its guards as they stand: the living ones of its place, and those inside one of its pieces' boxes)
            r["guards_standing"] = int(mine[11]) if mine and len(mine) > 12 else -1
            r["guards_in_a_piece"] = int(mine[12]) if mine and len(mine) > 12 else -1
            # (each piece where it stands: its distance from the middle and its bottom against the ground under its middle)
            pcs = [str(l).split("|") for l in g.get_wild_ruin_piece_lines(rid)]
            dists = sorted(math.hypot(float(q[1]) / 100.0 - cx, float(q[2]) / 100.0 - cy) for q in pcs if q[0] != "gone")
            offs = sorted((float(q[3]) - float(q[5])) for q in pcs if q[0] != "gone")
            r["pieces_m_from_middle"] = [round(dists[0], 1), round(dists[len(dists) // 2], 1), round(dists[-1], 1)] if dists else None
            r["bottom_over_ground_cm"] = [round(offs[0]), round(offs[len(offs) // 2]), round(offs[-1])] if offs else None
            r["pieces_gone"] = sum(1 for q in pcs if q[0] == "gone")
            # (no piece stands over the ground under its middle by more than its part raised it (its bottom goes on the lowest ground
            # under its corners, less its sink); the houses laid as the villages lay theirs (lift -1) are not measured so)
            r["floating"] = sorted(set(q[0] for q in pcs if q[0] != "gone" and len(q) > 7 and float(q[7]) >= 0 and float(q[3]) - float(q[5]) > float(q[7]) + 2.0))
            # (a piece laid to collide that stops nothing is walked through: every one must stop her)
            r["walked_through"] = sorted(set(q[0] for q in pcs if len(q) > 6 and q[6] == "0"))
            r["solid"] = sum(1 for q in pcs if len(q) > 6 and q[6] == "1")
            boxes, _f, _b = box_lines()
            r["chests"] = sum(1 for b in boxes if (3 << 40) <= b["key"] < (4 << 40) and math.hypot(b["x"] / 100.0 - cx, b["y"] / 100.0 - cy) < 40.0)
            mons = [m for m in GS.get_all_actors_of_class(G["w"], unreal.RDMonster) if unreal.SystemLibrary.is_valid(m)]
            r["monsters_within_20m"] = sum(1 for m in mons if math.hypot(m.get_actor_location().x / 100.0 - cx, m.get_actor_location().y / 100.0 - cy) < 20.0)
            # (the camera at its middle 3 m over its ground, the chunks round her made: on a slope a fixed pitch looked into the hill)
            yield from watching(wait_chunks(20, 50), msgs)
            p = G["pawn"].get_actor_location(); gz = sample(cx, cy)["z"]
            dh = math.hypot(cx * 100.0 - p.x, cy * 100.0 - p.y)
            pitch = max(-25.0, min(12.0, math.degrees(math.atan2(gz + 300.0 - (p.z + 200.0), dh)) - 4.0))
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=math.degrees(math.atan2(cy * 100.0 - p.y, cx * 100.0 - p.x))))
            yield from watching(rwait(1.5), msgs); shot(f"ruins12_{kd}", "1280x720"); yield from watching(rwait(1.2), msgs)
            # (the message as she comes within 30 m: she is moved to dry ground 20 to 28 m from its middle (her own way first; the
            # submerged town's middle lies 12 m out in the water), else into the water 20 m out; every line the HUD showed over the
            # visit is kept (its discovery, said with its kind, may come at 32 m, and a fall's line after it))
            a0 = math.degrees(math.atan2(spot[1] - cy, spot[0] - cx)); near = None
            for rr in (20.0, 24.0, 28.0):
                for a in [a0 + d_ for d_ in (0, 30, -30, 60, -60, 90, -90, 120, -120, 150, -150, 180)]:
                    tx, ty = cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a))
                    if not sample(tx, ty)["water"]: near = (tx, ty); break
                if near: break
            if not near: near = (cx + (spot[0] - cx) * 20.0 / math.hypot(spot[0] - cx, spot[1] - cy), cy + (spot[1] - cy) * 20.0 / math.hypot(spot[0] - cx, spot[1] - cy))
            s20 = sample(*near)
            z20 = s20["z"] + (max(0.0, s20["water_m"] - s20["h"]) * 100.0 if s20["water"] else 0.0)
            # (on whatever stands there, as she would come to it: put on the ground under a dune piece she was pushed out over it and
            # fell 9 m, and the fall's message hid the ruin's)
            hit = unreal.SystemLibrary.line_trace_single(G["w"], V(near[0] * 100.0, near[1] * 100.0, z20 + 3000.0), V(near[0] * 100.0, near[1] * 100.0, z20 - 300.0),
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [G["pawn"]], unreal.DrawDebugTrace.NONE, True)
            ht = hit.to_tuple() if hit else None
            if ht and ht[0]: z20 = max(z20, ht[4].z)
            G["pawn"].set_actor_location(V(near[0] * 100.0, near[1] * 100.0, z20 + 100.0), False, True); yield from watching(rwait(1.6), msgs)
            r["told_from_m"] = round(math.hypot(near[0] - cx, near[1] - cy), 1)
            r["told"] = " | ".join(msgs)
            r["title"] = mine[3] if mine else ""
            res["kinds"][kd] = r
    finally:
        quiet(False)
    g.wild_drop_all(); g.wild_put_her(0.0, 0.0); yield from wait_chunks(30, 40)
    seen = [k for k, v in res["kinds"].items() if v.get("found")]
    ok = res["table"] >= 20 and all(res["counts"].get(k, 0) > 0 for k in kinds) \
        and all(v.get("found") and v.get("laid") and v["laid"]["kind"] == k and v["laid"]["pieces"] >= 3 and v["chests"] >= 1
                and v["title"] and v["title"] in v["told"] and not v["walked_through"] and not v["floating"] and v["pieces_gone"] == 0
                and v["guards_standing"] >= v["laid"]["guards"] and v["guards_in_a_piece"] == 0 for k, v in res["kinds"].items()) \
        and len(seen) == len(want)
    step_result("ruins12", ok, **res)


def step_lairs12():
    """the list of 2026-11-12's fourth phase (924 lairs, RD/RDWildLair12.cpp): "monster lairs ... should be hiding behind something,
    a stand of trees, a ruin, a cave, an abandoned house, an earth berm". Every cover among the world's lairs within 150 km of
    Brokenspire (CountWildLairs); then the nearest lair of each cover (lairs12=<cover>+<cover> for some) visited with the monsters
    quiet: what was laid round it (no piece laid to collide that stops nothing, none over the ground by more than its part
    raised it), its monsters within its circle, and how hidden they are: sight lines from an eye 1.7 m up at 16 points 30 m round
    it (and 15 m) to each monster's legs, chest and head, traced against the cover's own pieces (WildLairSight; the lines its
    pieces left open that something else blocks are counted apart); a picture from 30 m out on its closed side. Then the
    monsters woken with her 18 m out before its opening (and nearer to her by 3 m), then off to its side: each time one comes out
    past its walls within 20 s (the time is recorded); between the two she goes 60 m off and how many are home again after 25 s is recorded. Of each
    cover the nearest lair on gentle ground (its den's ground within 2 m over 8 m)"""
    g = G["gen"]; res = {"covers": {}}; quiet(True)
    yield from wait_ready(90)
    covers = [str(k.get_editor_property("name")) for k in g.get_editor_property("wild_lair_covers")]
    res["table"] = len(covers)
    res["counts"] = {str(l).split("|")[0]: int(str(l).split("|")[1]) for l in g.count_wild_lairs(0.0, 0.0, 150.0)}
    want = G.get("look_only") or covers
    def gentle(x, y):
        s0 = sample(x, y)
        if s0["water"]: return False
        return all(abs(sample(x + dx, y + dy)["h"] - s0["h"]) < 1.2 for dx, dy in ((3, 0), (-3, 0), (0, 3), (0, -3)))
    def nearest():
        d = 1e9
        for m in g.get_monsters():
            if m and not m.is_dead(): d = min(d, dist2(m.get_actor_location(), G["pawn"].get_actor_location()))
        return d / 100.0
    try:
        for cv in want:
            r = {}
            # (the nearest whose den's ground rises or falls 2 m at most within 8 m: on a canyon's terraces she was set down a storey
            # over the den and fell to her death, and on a mountain's face its monsters could not reach her; those are in TODO)
            f = str(g.find_wild_lair(cv, 0.0, 0.0, 150.0, 2.0))
            if not f: res["covers"][cv] = {"found": False}; continue
            lid, cx, cy, yw, nm = f.split("|", 4); lid = int(lid); cx = float(cx); cy = float(cy); yw = float(yw)
            r.update({"found": True, "id": lid, "at_km": [round(cx / 1000.0, 2), round(cy / 1000.0, 2)], "name": nm})
            # (she stands 45 m out on its closed side (behind it), on gentle dry ground, while its chunks are made)
            spot = None
            for rr in (45.0, 55.0):
                for a in [yw + 180 + d_ for d_ in (0, 30, -30, 60, -60, 90, -90)]:
                    sx, sy = cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a))
                    if gentle(sx, sy): spot = (sx, sy); break
                if spot: break
            spot = spot or (cx - 45.0, cy)
            g.wild_put_her(*spot); yield from wait_chunks(30, 50); yield from rwait(2.0)
            lines = [str(l).split("|") for l in g.get_wild_lair_lines()]
            mine = next((p for p in lines if int(p[1]) == lid), None)
            r["laid"] = {"cover": mine[2], "pieces": int(mine[5]), "exit": [float(mine[6]), float(mine[7])], "reach_m": float(mine[10]) if len(mine) > 10 else 0.0} if mine else None
            # (its den: its place, or moved off a steep slope (a harpy lair on a mountain's face): measured from where it was laid)
            if mine:
                r["den_moved_m"] = round(math.hypot(float(mine[3]) - cx, float(mine[4]) - cy), 1)
                cx, cy = float(mine[3]), float(mine[4])
            pcs = [str(l).split("|") for l in g.get_wild_lair_piece_lines(lid)]
            r["pieces_gone"] = sum(1 for q in pcs if q[0] == "gone")
            # (each kind of piece: how many, its bottom and top over the ground under its middle, the lowest and highest (cm))
            kinds_ = {}
            for q in pcs:
                if q[0] == "gone": continue
                kinds_.setdefault(q[0], []).append((float(q[3]) - float(q[5]), float(q[4]) - float(q[5])))
            r["pieces"] = {k_: [len(v_), round(min(b for b, _t in v_)), round(max(t_ for _b, t_ in v_))] for k_, v_ in kinds_.items()}
            r["walked_through"] = sorted(set(q[0] for q in pcs if len(q) > 6 and q[6] == "0"))
            r["floating"] = sorted(set(q[0] for q in pcs if q[0] != "gone" and len(q) > 7 and float(q[7]) >= 0 and float(q[3]) - float(q[5]) > float(q[7]) + 2.0))
            mons = [m for m in g.get_monsters() if m and not m.is_dead() and math.hypot(m.get_actor_location().x / 100.0 - cx, m.get_actor_location().y / 100.0 - cy) < 25.0]
            r["monsters_m_from_middle"] = sorted(round(math.hypot(m.get_actor_location().x / 100.0 - cx, m.get_actor_location().y / 100.0 - cy), 1) for m in mons)
            r["cover_r_m"] = round(mons[0].get_editor_property("cover_r") / 100.0, 1) if mons else 0.0
            sb, sl, sm, so = [int(x) for x in str(g.wild_lair_sight(lid, 30.0, 16)).split("|")]
            r["sight_30m"] = {"blocked": sb, "lines": sl, "monsters": sm, "else_blocked": so, "hidden": round(sb / sl, 2) if sl else 0.0}
            sb2, sl2, _m2, so2 = [int(x) for x in str(g.wild_lair_sight(lid, 15.0, 16)).split("|")]
            r["sight_15m"] = {"blocked": sb2, "lines": sl2, "else_blocked": so2, "hidden": round(sb2 / sl2, 2) if sl2 else 0.0}
            # (a picture from 30 m on its closed side, looking at its middle: of the ways round its closed half, the first from which
            # a line from her eye to its middle meets nothing but the cover's own pieces (the region's rocks and trees are the chunk's
            # instanced plants: on the mountains a boulder of the region's filled the view))
            gz0 = sample(cx, cy)["z"]; pick = None
            for a in [yw + 180 + d_ for d_ in (0, 25, -25, 50, -50, 75, -75, 100, -100)]:
                px, py = cx + 30.0 * math.cos(math.radians(a)), cy + 30.0 * math.sin(math.radians(a))
                sp = sample(px, py)
                if sp["water"]: continue
                hit = unreal.SystemLibrary.line_trace_single(G["w"], V(px * 100.0, py * 100.0, sp["z"] + 250.0), V(cx * 100.0, cy * 100.0, gz0 + 150.0),
                                                             unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [G["pawn"]], unreal.DrawDebugTrace.NONE, True)
                ht = hit.to_tuple() if hit else None
                comp = ht[10] if ht and ht[0] else None
                # (an earth bank is a procedural mesh too, but drawn: the ground's collision is hidden, its drawn ground named Ground)
                bank = isinstance(comp, unreal.ProceduralMeshComponent) and comp.is_visible() and comp.get_name() not in ("Ground", "Water")
                piece = isinstance(comp, unreal.StaticMeshComponent) and not isinstance(comp, unreal.InstancedStaticMeshComponent)
                if comp is None or bank or piece:
                    pick = (px, py, sp); break
                pick = pick or (px, py, sp)
            if pick:
                G["pawn"].set_actor_location(V(pick[0] * 100.0, pick[1] * 100.0, pick[2]["z"] + 120.0), False, True); yield from rwait(1.0)
            p = G["pawn"].get_actor_location(); gz = sample(cx, cy)["z"]
            pitch = max(-25.0, min(12.0, math.degrees(math.atan2(gz + 150.0 - (p.z + 200.0), math.hypot(cx * 100.0 - p.x, cy * 100.0 - p.y))) - 4.0))
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=math.degrees(math.atan2(cy * 100.0 - p.y, cx * 100.0 - p.x))))
            yield from rwait(1.5); shot(f"lairs12_{cv}", "1280x720"); yield from rwait(1.2)
            # (woken: she stands 18 m out, before its opening and then off to its side; its monsters must come out to her past its
            # walls (its reach), not stall against them (PR #57's review: 3 m nearer passed monsters stuck inside a ruin's wall))
            def outside():
                return max([math.hypot(m.get_actor_location().x / 100.0 - cx, m.get_actor_location().y / 100.0 - cy) for m in g.get_monsters()
                            if m and not m.is_dead() and math.hypot(m.get_actor_location().x / 100.0 - cx, m.get_actor_location().y / 100.0 - cy) < 40.0] or [0.0])
            if mine and mons:
                ex, ey = r["laid"]["exit"]; reach = r["laid"]["reach_m"]
                ga = math.degrees(math.atan2(ey - cy, ex - cx))
                h0 = sample(cx, cy)["h"]
                def trial_spot(a_deg):
                    # (gentle dry ground 16 to 22 m out near the way asked, within 3 m of the den's height)
                    for dd in (0, 15, -15, 30, -30, 45, -45):
                        for rr in (18.0, 16.0, 20.0, 22.0):
                            x_, y_ = cx + math.cos(math.radians(a_deg + dd)) * rr, cy + math.sin(math.radians(a_deg + dd)) * rr
                            if gentle(x_, y_) and abs(sample(x_, y_)["h"] - h0) < 3.0: return (x_, y_, a_deg + dd)
                    return (cx + math.cos(math.radians(a_deg)) * 18.0, cy + math.sin(math.radians(a_deg)) * 18.0, a_deg)
                for tag, off in (("woken", 0.0), ("woken_side", 90.0)):
                    fx, fy, fdeg = trial_spot(ga + off); fa = math.radians(fdeg)
                    r[tag + "_way_deg"] = round(fdeg - ga, 0)
                    g.wild_put_her(fx, fy); yield from rwait(0.8)
                    cb().set_health(cb().get_max_health()); quiet(False)
                    # (until one is out past its walls, 20 s at most: the ghouls walk 1 m a second, the harpies run)
                    d0 = nearest(); t0 = time.time(); far = 0.0
                    while time.time() - t0 < 20.0:
                        # (her hit points kept up: a pack of ghouls killed her in 20 s and she woke in a town)
                        yield from wait(0.5); far = outside(); cb().set_health(cb().get_max_health())
                        if far > reach: break
                    d1 = nearest()
                    r[tag + "_s"] = round(time.time() - t0, 1)
                    quiet(True); cb().set_health(cb().get_max_health())
                    r[tag + "_m"] = [round(d0, 1), round(d1, 1)]
                    r[tag + "_out_m"] = round(far, 1)
                    if tag == "woken":
                        # (she goes 60 m off (the game's own placing: set down by the sample's height in a wetland she fell out of
                        # the world and its chunks were made again): they lose her and go home by its opening, in time for the side's)
                        g.wild_put_her(cx + math.cos(fa) * 60.0, cy + math.sin(fa) * 60.0); yield from wait(25.0)
                        back = [m for m in g.get_monsters() if m and not m.is_dead() and math.hypot(m.get_editor_property("home_at").x / 100.0 - cx, m.get_editor_property("home_at").y / 100.0 - cy) < 5.0]
                        r["home_after_20s"] = sum(1 for m in back if math.hypot(m.get_actor_location().x / 100.0 - cx, m.get_actor_location().y / 100.0 - cy) < reach)
                        r["monsters"] = len(back)
            res["covers"][cv] = r
    finally:
        quiet(False)
    g.wild_drop_all(); g.wild_put_her(0.0, 0.0); yield from wait_chunks(30, 40)
    seen = [k for k, v in res["covers"].items() if v.get("found")]
    ok = res["table"] >= 6 and all(res["counts"].get(k, 0) > 0 for k in covers) and len(seen) == len(want) \
        and all(v.get("laid") and v["laid"]["cover"] == k and v["laid"]["pieces"] >= 3 and not v["walked_through"] and not v["floating"]
                and v["pieces_gone"] == 0 and v["sight_30m"]["monsters"] >= 1 and v["sight_30m"]["hidden"] >= 0.6
                and max(v["monsters_m_from_middle"] or [99]) <= v["cover_r_m"] + 0.5
                and v.get("woken_m") and v["woken_m"][1] < v["woken_m"][0] - 3.0 and v["woken_out_m"] > v["laid"]["reach_m"]
                and v.get("woken_side_m") and v["woken_side_out_m"] > v["laid"]["reach_m"]
                for k, v in res["covers"].items())
    step_result("lairs12", ok, **res)


def step_sites12():
    """the list of 2026-11-12's fifth phase (924 sites, RD/RDWildSite12.cpp): the structures that hold its quests ("cave system,
    canyon or gorge, cliff face or aerie ... a titan's carcass ... a rift or portal scar"; "those structures can have containers,
    traps, hold prisoners"). Every kind among the world's structures within 150 km of Brokenspire (CountWildSites, and every
    quest among them); then the nearest of each kind (sites12=<kind>+<kind> for some) visited: she is put 45 m before its front on
    gentle ground, the chunks made, and what was laid read: its pieces (none walked through, none over the ground by more than
    its part raised it, none gone), its chest, its guards standing (none inside a piece), its prisoners and traps, its quest's
    giver; a picture from where she stands; a prisoner freed with F (the cage gone, gold given), a trap stepped on (a wound and
    a slow); the living beast walks its round"""
    g = G["gen"]; res = {"kinds": {}}; quiet(True)
    yield from wait_ready(90)
    kinds = [str(k.get_editor_property("name")) for k in g.get_editor_property("wild_site_kinds")]
    res["table"] = len(kinds)
    cnt = {}
    for l in g.count_wild_sites(0.0, 0.0, 150.0):
        a_, b_ = str(l).rsplit("|", 1); cnt[a_] = int(b_)
    res["counts"] = {k: v for k, v in cnt.items() if not k.startswith("quest:")}
    res["quests"] = {k[6:]: v for k, v in cnt.items() if k.startswith("quest:")}
    want = G.get("look_only") or kinds
    def gentle(x, y):
        s0 = sample(x, y)
        if s0["water"]: return False
        return all(abs(sample(x + dx, y + dy)["h"] - s0["h"]) < 1.2 for dx, dy in ((3, 0), (-3, 0), (0, 3), (0, -3)))
    try:
        for kd in want:
            r = {}
            f = str(g.find_wild_site(kd, "None", 0.0, 0.0, 150.0))
            if not f: res["kinds"][kd] = {"found": False}; continue
            sid, cx, cy, yw, nm = f.split("|", 4); sid = int(sid); cx = float(cx); cy = float(cy); yw = float(yw)
            r.update({"found": True, "id": sid, "at_km": [round(cx / 1000.0, 2), round(cy / 1000.0, 2)], "name": nm})
            spot = None
            for rr in (45.0, 55.0, 38.0):
                for a in [yw + d_ for d_ in (0, 40, -40, 80, -80, 120, -120, 180)]:
                    sx, sy = cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a))
                    if gentle(sx, sy): spot = (sx, sy); break
                if spot: break
            spot = spot or (cx + 45.0, cy)
            msgs = []
            try: cb().set_editor_property("message", "")
            except Exception: pass
            g.wild_put_her(*spot); yield from watching(wait_chunks(30, 50), msgs); yield from watching(rwait(2.0), msgs)
            lines = [str(l).split("|") for l in g.get_wild_site_lines()]
            mine = next((p for p in lines if int(p[1]) == sid), None)
            if mine:
                r["laid"] = {"kind": mine[2], "pieces": int(mine[6]), "boxes": int(mine[7]), "guards_standing": int(mine[8]), "guards_in_a_piece": int(mine[9]),
                             "prisoners": int(mine[10]), "traps": int(mine[12])}
            K = next((k for k in g.get_editor_property("wild_site_kinds") if str(k.get_editor_property("name")) == kd), None)
            r["table"] = {"guards": K.get_editor_property("guards"), "prisoners": K.get_editor_property("prisoners"), "traps": K.get_editor_property("traps")} if K else {}
            pcs = [str(l).split("|") for l in g.get_wild_site_piece_lines(sid)]
            r["pieces_gone"] = sum(1 for q in pcs if q[0] == "gone")
            r["walked_through"] = sorted(set(q[0] for q in pcs if len(q) > 6 and q[6] == "0"))
            r["floating"] = sorted(set(q[0] for q in pcs if q[0] != "gone" and len(q) > 7 and float(q[7]) >= 0 and float(q[3]) - float(q[5]) > float(q[7]) + 2.0))
            boxes, _f, _b = box_lines()
            r["chests"] = sum(1 for b in boxes if (5 << 40) <= b["key"] < (6 << 40) and math.hypot(b["x"] / 100.0 - cx, b["y"] / 100.0 - cy) < 70.0)
            folk = [str(l).split("|") for l in g.get_wild_quest_folk_lines(sid)]
            r["giver"] = next((q[1] for q in folk if q[0] == "giver"), "")
            # (the picture: the camera at its middle 3 m up, a clear line found as for the lairs)
            ax, ay, up = cx, cy, 300.0
            if kd == "beastback":
                # (the beast walks its round 45 m about the middle: she stands 40 m off the beast itself, the camera on it)
                bl = [str(l).split("|") for l in g.get_wild_beast_lines() if str(l).split("|")[1] == str(sid)]
                if bl:
                    ax, ay, up = float(bl[0][2]) / 100.0, float(bl[0][3]) / 100.0, 450.0
                    p = G["pawn"].get_actor_location(); dx, dy = p.x / 100.0 - ax, p.y / 100.0 - ay; dl = math.hypot(dx, dy) or 1.0
                    sx, sy = ax + dx / dl * 40.0, ay + dy / dl * 40.0
                    G["pawn"].set_actor_location(V(sx * 100.0, sy * 100.0, sample(sx, sy)["z"] + 100.0), False, True); yield from watching(rwait(0.8), msgs)
            gz0 = sample(ax, ay)["z"]
            p = G["pawn"].get_actor_location()
            pitch = max(-25.0, min(12.0, math.degrees(math.atan2(gz0 + up - (p.z + 200.0), math.hypot(ax * 100.0 - p.x, ay * 100.0 - p.y))) - 4.0))
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=math.degrees(math.atan2(ay * 100.0 - p.y, ax * 100.0 - p.x))))
            yield from watching(rwait(1.5), msgs); shot(f"sites12_{kd}", "1280x720"); yield from watching(rwait(1.0), msgs)
            # (a prisoner freed: she is put by it and presses F)
            things = [str(l).split("|") for l in g.get_wild_site_thing_lines(sid)]
            pr = [t_ for t_ in things if t_[0] == "prisoner" and t_[3] == "0"]
            if pr:
                px_, py_ = float(pr[0][1]), float(pr[0][2])
                gold0 = g.get_gold() if hasattr(g, "get_gold") else 0
                # (on the cage's outer side, away from the structure's middle and its chest)
                ox, oy = px_ / 100.0 - cx, py_ / 100.0 - cy; ol = math.hypot(ox, oy) or 1.0
                qx, qy = px_ / 100.0 + ox / ol * 1.5, py_ / 100.0 + oy / ol * 1.5
                G["pawn"].set_actor_location(V(qx * 100.0, qy * 100.0, sample(qx, qy)["z"] + 100.0), False, True); yield from rwait(0.6)
                r["free_f"] = str(g.interact_nearest(G["pawn"].get_actor_location())); yield from watching(rwait(0.8), msgs)
                after = [str(l).split("|") for l in g.get_wild_site_thing_lines(sid)]
                r["freed"] = sum(1 for t_ in after if t_[0] == "prisoner" and t_[3] == "1")
                r["gold_from_prisoner"] = (g.get_gold() - gold0) if hasattr(g, "get_gold") else None
            # (a trap stepped on: her hit points and the trap's count)
            tr = [t_ for t_ in things if t_[0] == "trap"]
            if tr:
                tx_, ty_ = float(tr[0][1]), float(tr[0][2])
                cb().set_health(cb().get_max_health()); hp0 = cb().get_health(); n0 = cb().get_editor_property("traps_hurt")
                G["pawn"].set_actor_location(V(tx_, ty_, sample(tx_ / 100.0, ty_ / 100.0)["z"] + 100.0), False, True); yield from watching(rwait(1.2), msgs)
                r["trap"] = {"hurt": cb().get_editor_property("traps_hurt") - n0, "hp_lost": round(hp0 - cb().get_health(), 1)}
                cb().set_health(cb().get_max_health())
            if kd == "beastback":
                b0 = [str(l).split("|") for l in g.get_wild_beast_lines() if str(l).split("|")[1] == str(sid)]
                yield from rwait(3.0)
                b1 = [str(l).split("|") for l in g.get_wild_beast_lines() if str(l).split("|")[1] == str(sid)]
                r["beast_moved_m"] = round(math.hypot(float(b1[0][2]) - float(b0[0][2]), float(b1[0][3]) - float(b0[0][3])) / 100.0, 2) if b0 and b1 else None
                # (which way it faces: its body to its head bone, against the way it moved; within 30 degrees)
                if b0 and b1 and len(b1[0]) > 7:
                    mvx, mvy = float(b1[0][2]) - float(b0[0][2]), float(b1[0][3]) - float(b0[0][3])
                    hx, hy = float(b1[0][6]) - float(b1[0][2]), float(b1[0][7]) - float(b1[0][3])
                    r["beast_head_off_deg"] = round(abs((math.degrees(math.atan2(hy, hx) - math.atan2(mvy, mvx)) + 180.0) % 360.0 - 180.0), 1)
            r["told"] = " | ".join(msgs)
            res["kinds"][kd] = r
            g.wild_drop_all(); yield from rwait(0.5)
    finally:
        quiet(False)
    g.wild_put_her(0.0, 0.0); yield from wait_chunks(30, 40)
    seen = [k for k, v in res["kinds"].items() if v.get("found")]
    def good(k, v):
        L = v.get("laid") or {}; T = v.get("table") or {}
        return (L.get("kind") == k and L.get("pieces", 0) >= 3 and v["chests"] >= 1 and not v["walked_through"] and not v["floating"] and v["pieces_gone"] == 0
                and L.get("guards_standing", -1) >= T.get("guards", 0) and L.get("guards_in_a_piece", 1) == 0 and L.get("prisoners", -1) >= T.get("prisoners", 0)
                and L.get("traps", -1) >= T.get("traps", 0) and v["giver"] != "" and (T.get("prisoners", 0) == 0 or v.get("freed", 0) >= 1)
                and (T.get("traps", 0) == 0 or (v.get("trap") or {}).get("hurt", 0) >= 1) and (k != "beastback" or ((v.get("beast_moved_m") or 0) > 1.0 and v.get("beast_head_off_deg") is not None and v["beast_head_off_deg"] <= 30.0)))
    res["failed"] = [k for k, v in res["kinds"].items() if v.get("found") and not good(k, v)]
    ok = res["table"] >= 34 and all(res["counts"].get(k, 0) > 0 for k in kinds) and len(seen) == len(want) and not res["failed"] and len(res["quests"]) >= 25
    step_result("sites12", ok, **res)


def step_quests12():
    """the list of 2026-11-12's fifth phase (924 quests, RD/RDWildQuest12.cpp): its 25 quests, each at the nearest structure that
    holds it (quests12=<quest>+<quest> for some), played through as a player does: F on its giver (the quest taken), then each
    stage by its own means: F on the one to talk to (or one side of a choice), coming to its point, its monsters killed (blows of
    the game's own damage), its things taken with F (at night for the moonbloom: the clock moved), a beast beaten down and bound,
    a wild horse walked up to three times, someone walked home while they follow her (the game sped up), a place held against
    its waves, medicine brought to a town in time, a storm weathered in a shelter; each stage's line and its twist read as it
    comes; done when the quest says so, its gold paid"""
    g = G["gen"]; res = {"quests": {}}; quiet(True)
    yield from wait_ready(90)
    quests = [str(q.get_editor_property("name")) for q in g.get_editor_property("wild_quests")]
    res["table"] = len(quests)
    want = G.get("look_only") or quests
    W = G["w"]
    def con(c): unreal.SystemLibrary.execute_console_command(W, c)
    def run_line(sid):
        for l in g.get_wild_quest_run_lines():
            p_ = str(l).split("|")
            if int(p_[1]) == sid: return p_
        return None
    def put(x, y): G["pawn"].set_actor_location(V(x * 100.0, y * 100.0, sample(x, y)["z"] + 110.0), False, True)
    def go(x, y, msgs):
        # (a point more than 1.5 km off: put there by the game, its chunks made, as a journey would; else stepped to)
        p_ = G["pawn"].get_actor_location()
        if math.hypot(p_.x / 100.0 - x, p_.y / 100.0 - y) > 1500.0:
            g.wild_put_her(x, y); yield from watching(wait_chunks(30, 50), msgs); yield from watching(rwait(1.5), msgs)
        else: put(x, y)
    def folk(sid): return [str(l).split("|") for l in g.get_wild_quest_folk_lines(sid)]
    def stage_things(sid): return [str(l).split("|") for l in g.get_wild_quest_thing_lines(sid)]
    def kill_near(x, y, rr=60.0):
        n_ = 0
        for m in g.get_monsters():
            if m and not m.is_dead() and math.hypot(m.get_actor_location().x / 100.0 - x, m.get_actor_location().y / 100.0 - y) < rr:
                m.apply_damage(1e7, G["pawn"]); n_ += 1
        return n_
    try:
        for qn in want:
            r = {"stages": []}
            f = str(g.find_wild_site("None", qn, 0.0, 0.0, 150.0))
            if not f: res["quests"][qn] = {"found": False}; continue
            sid, cx, cy, yw, nm = f.split("|", 4); sid = int(sid); cx = float(cx); cy = float(cy)
            r.update({"found": True, "site": sid, "at_km": [round(cx / 1000.0, 2), round(cy / 1000.0, 2)], "structure": nm})
            msgs = []
            try: cb().set_editor_property("message", "")
            except Exception: pass
            gold0 = g.get_gold()
            if qn == "tame":
                # (a bay bought before (the stable's own state: bHorseOwned), so the tamed grey is her second mount)
                gi_ = unreal.GameplayStatics.get_game_instance(W)
                gi_.set_editor_property("horse_owned", True); gi_.set_editor_property("tamed_only", False); gi_.set_editor_property("ride_tamed", False)
            g.wild_put_her(cx + 12.0, cy); yield from watching(wait_chunks(30, 50), msgs); yield from watching(rwait(1.5), msgs)
            # (the giver: F beside them)
            gv = next((q for q in folk(sid) if q[0] == "giver"), None)
            if not gv: r["error"] = "no giver"; res["quests"][qn] = r; continue
            G["pawn"].set_actor_location(V(float(gv[2]) + 140.0, float(gv[3]), float(gv[4]) + 20.0), False, True); yield from rwait(0.5)
            r["take_f"] = str(g.interact_nearest(G["pawn"].get_actor_location())); yield from watching(rwait(0.8), msgs)
            t0 = time.time(); last = None; tries = 0
            while time.time() - t0 < 240.0:
                L = run_line(sid)
                if not L: break
                st = int(L[3])
                if st >= 90: break
                do, px, py = L[4], float(L[8]), float(L[9])
                # (a stage not begun yet has no point: wait for the game's tick (a begun stage's (0, 0) is Brokenspire's, a town goal))
                if len(L) > 15 and L[15] == "0":
                    # (a stage is begun within 4 km of the structure or its point: far off (at a ruin 12 km away, the giver's
                    # stage next) she goes back to the structure, as a player would)
                    p_ = G["pawn"].get_actor_location()
                    if math.hypot(p_.x / 100.0 - cx, p_.y / 100.0 - cy) > 3500.0: yield from go(cx + 12.0, cy, msgs)
                    yield from rwait(0.4); continue
                if (st, do) != last:
                    last = (st, do); tries = 0
                    r["stages"].append({"stage": st, "do": do, "hint": L[14], "point_m_from_site": round(math.hypot(px - cx, py - cy), 1)})
                tries += 1
                if tries > 40: r["stuck"] = {"stage": st, "do": do, "line": L}; break
                cb().set_health(cb().get_max_health())
                if do == "goto" or do == "survive":
                    yield from go(px, py, msgs)
                    # (the storm's two minutes in the shelter, the game four times as fast)
                    if do == "survive": con("rd.GameSpeed 4"); tries -= 0.9; r["stages"][-1]["weather"] = g.get_weather()
                    yield from watching(rwait(1.0), msgs)
                elif do in ("talk", "choose", "deliver"):
                    if do == "deliver":
                        g.wild_put_her(px + 30.0, py); yield from watching(wait_chunks(30, 40), msgs); yield from watching(rwait(2.0), msgs)
                        continue
                    role = "b" if (do == "choose" and qn in ("clearing",)) else "a" if do == "choose" else None
                    fl = folk(sid)
                    who = next((q for q in fl if (role and q[0] == role)), None) if role else None
                    if not who:
                        # (the one this stage names: the newest that is not the giver, else the giver)
                        who = next((q for q in reversed(fl) if q[0] != "giver" and q[0] not in ("a", "b")), None) if do == "talk" else None
                        if do == "talk" and (not who or "giver" in L[14].lower() or any(w_ in L[14].lower() for w_ in ("tell", "report", "bring the", "speak with the spirit"))):
                            who = next((q for q in fl if q[0] == "giver"), who)
                    if not who: yield from rwait(0.5); continue
                    G["pawn"].set_actor_location(V(float(who[2]) + 140.0, float(who[3]), float(who[4]) + 20.0), False, True); yield from rwait(0.5)
                    r["stages"][-1]["f"] = str(g.interact_nearest(G["pawn"].get_actor_location()))
                    if do == "choose": r["choice"] = role
                    yield from watching(rwait(0.8), msgs)
                elif do == "kill":
                    yield from go(px + 10.0, py, msgs); yield from watching(rwait(1.2), msgs)
                    r["stages"][-1]["killed"] = r["stages"][-1].get("killed", 0) + kill_near(px, py); yield from watching(rwait(1.0), msgs)
                elif do in ("collect", "rite", "cleanse"):
                    # (PR #58's review: a stage laid again lays only what is left: one moonbloom taken, she goes 5 km off (the
                    # stage cleared) and back (laid again): none while away, the two left when back, none doubled)
                    if qn == "ingredient" and "relaid" not in r and int(L[5]) == 1:
                        yield from go(cx + 5000.0, cy, msgs); yield from watching(rwait(2.0), msgs)
                        away = len([t_ for t_ in stage_things(sid) if t_[0] == "thing"])
                        yield from go(cx + 12.0, cy, msgs); yield from watching(rwait(2.0), msgs)
                        r["relaid"] = {"away_things": away, "back_left": len([t_ for t_ in stage_things(sid) if t_[0] == "thing" and t_[4] == "0"]),
                                       "back_all": len([t_ for t_ in stage_things(sid) if t_[0] == "thing"])}
                        continue
                    th = [t_ for t_ in stage_things(sid) if t_[0] == "thing" and t_[4] == "0"]
                    if not th:
                        # (the rite's or the cleansing's guardians come once its thing is taken)
                        kill_near(px, py, 40.0); yield from watching(rwait(1.0), msgs); continue
                    if "night" in L[14].lower(): con("rd.Time 23"); yield from rwait(0.6)
                    if "dawn" in L[14].lower(): con("rd.Time 6"); yield from rwait(0.6)
                    tx_, ty_, tz_ = float(th[0][1]), float(th[0][2]), float(th[0][3])
                    G["pawn"].set_actor_location(V(tx_ + 120.0, ty_, tz_ + 110.0), False, True); yield from rwait(0.5)
                    r["stages"][-1].setdefault("f", []).append(str(g.interact_nearest(G["pawn"].get_actor_location())))
                    yield from watching(rwait(0.8), msgs)
                elif do == "capture":
                    mo = [t_ for t_ in stage_things(sid) if t_[0] == "monster" and t_[4] == "0"]
                    if not mo: yield from rwait(0.6); continue
                    m = min((m_ for m_ in g.get_monsters() if m_ and not m_.is_dead()), key=lambda m_: math.hypot(m_.get_actor_location().x - float(mo[0][1]), m_.get_actor_location().y - float(mo[0][2])), default=None)
                    if m is None: yield from rwait(0.6); continue
                    if m.get_health() > m.get_max_health() * 0.3: m.apply_damage(m.get_health() - m.get_max_health() * 0.2, G["pawn"]); yield from rwait(0.4)
                    l_ = m.get_actor_location()
                    G["pawn"].set_actor_location(V(l_.x + 150.0, l_.y, l_.z + 30.0), False, True); yield from rwait(0.3)
                    r["stages"][-1]["f"] = str(g.interact_nearest(G["pawn"].get_actor_location())); yield from watching(rwait(0.8), msgs)
                elif do == "tame":
                    hz = next((t_ for t_ in stage_things(sid) if t_[0] == "horse"), None)
                    if not hz: yield from rwait(0.6); continue
                    G["pawn"].set_actor_location(V(float(hz[1]) + 200.0, float(hz[2]), float(hz[3]) + 120.0), False, True); yield from rwait(1.2)
                    r["stages"][-1].setdefault("f", []).append(str(g.interact_nearest(G["pawn"].get_actor_location()))); yield from watching(rwait(1.2), msgs)
                elif do == "escort":
                    # (she walks toward the end in short steps, the game three times as fast, the one escorted following; an ambush
                    # killed as it comes)
                    con("rd.GameSpeed 3"); fl = folk(sid)
                    p_ = G["pawn"].get_actor_location()
                    dx, dy = px * 100.0 - p_.x, py * 100.0 - p_.y; dd = math.hypot(dx, dy)
                    step = min(500.0, dd)
                    if dd > 50.0: G["pawn"].set_actor_location(V(p_.x + dx / dd * step, p_.y + dy / dd * step, sample((p_.x + dx / dd * step) / 100.0, (p_.y + dy / dd * step) / 100.0)["z"] + 110.0), False, True)
                    yield from watching(rwait(1.2), msgs)
                    r["stages"][-1]["ambush_killed"] = r["stages"][-1].get("ambush_killed", 0) + kill_near(p_.x / 100.0, p_.y / 100.0, 40.0)
                    tries -= 0.8
                elif do == "defend":
                    con("rd.GameSpeed 4"); put(px + 5.0, py)
                    yield from watching(rwait(1.5), msgs)
                    r["stages"][-1]["killed"] = r["stages"][-1].get("killed", 0) + kill_near(px, py, 50.0)
                    tries -= 0.9
                else:
                    yield from rwait(0.6)
            con("rd.GameSpeed 1"); con("rd.Weather auto")
            L = run_line(sid)
            r["end_stage"] = int(L[3]) if L else None
            r["gold"] = g.get_gold() - gold0
            if qn == "tame":
                # (the tamed horse a second mount: hers and out, and with a bought one the stable swaps them and back)
                gi = unreal.GameplayStatics.get_game_instance(W)
                r["tamed"] = {"horses_tamed": gi.get_editor_property("horses_tamed"), "ride_tamed": gi.get_editor_property("ride_tamed"),
                              "tamed_only": gi.get_editor_property("tamed_only"), "owned": gi.get_editor_property("horse_owned")}
                if not r["tamed"]["tamed_only"]:
                    r["tamed"]["swap"] = [bool(g.swap_horse()), gi.get_editor_property("ride_tamed"), bool(g.swap_horse()), gi.get_editor_property("ride_tamed")]
            r["told"] = msgs[-12:]
            res["quests"][qn] = r
            g.wild_drop_all(); yield from rwait(0.5)
    finally:
        quiet(False); con("rd.GameSpeed 1"); con("rd.Weather auto")
    g.wild_put_her(0.0, 0.0); yield from wait_chunks(30, 40)
    def tamed_ok(v):
        T = v.get("tamed")
        if T is None: return True
        return T["horses_tamed"] >= 1 and T["ride_tamed"] and T["owned"] and (T["tamed_only"] or T.get("swap") == [True, False, True, True])
    def relaid_ok(v):
        R_ = v.get("relaid")
        return R_ is None or (R_["away_things"] == 0 and R_["back_left"] == 2 and R_["back_all"] == 2)
    res["failed"] = [k for k, v in res["quests"].items() if not (v.get("found") and v.get("end_stage") == 90 and v.get("gold", 0) > 0 and tamed_ok(v) and relaid_ok(v))]
    ok = res["table"] >= 25 and not res["failed"] and len(res["quests"]) == len(want)
    step_result("quests12", ok, **res)


def step_list10w():
    """the list of 2026-11-10 in the wilds: rd.Weather typed at the console sets the weather at once and holds it (storm, then fog,
    then auto lets it go); rd.GoTo ashenreach puts her at Ashenreach's gate with the city built round her, rd.GoTo brokenspire
    back; an ambush (only its kind left roaming, the director's gap 2 s) comes at her from 45-70 m, beyond its noticing distance,
    while she stands still: its monsters hunt her and close in"""
    g = G["gen"]; res = {}
    yield from wait_ready(90)
    w = G["w"]
    # ---- the weather
    unreal.SystemLibrary.execute_console_command(w, "rd.Weather storm"); yield from rwait(0.5)
    res["storm"] = {"weather": g.get_weather(), "held": g.get_editor_property("weather_held"), "sky": str(g.get_sky_state())}
    unreal.SystemLibrary.execute_console_command(w, "rd.Weather fog"); yield from rwait(0.5)
    res["fog"] = {"weather": g.get_weather(), "held": g.get_editor_property("weather_held")}
    unreal.SystemLibrary.execute_console_command(w, "rd.Weather auto"); yield from rwait(0.5)
    res["auto"] = {"weather": g.get_weather(), "held": g.get_editor_property("weather_held")}
    # ---- rd.GoTo
    unreal.SystemLibrary.execute_console_command(w, "rd.GoTo ashenreach")
    t0 = time.time(); ts = {}
    while time.time() - t0 < 90:
        yield from rwait(1.0); ts = town_state()
        if ts.get("name") == "Ashenreach" and ts.get("loading", 1) == 0 and ts.get("section", 0) == 1: break
    p = G["pawn"].get_actor_location()
    tw = towns().get("Ashenreach") or {}
    res["goto"] = {"town": ts.get("name"), "loaded": ts.get("section"), "secs": round(time.time() - t0, 1),
                   "from_site_m": round(math.hypot(p.x / 100.0 - tw.get("x", 0.0), p.y / 100.0 - tw.get("y", 0.0)), 1) if tw else None}
    unreal.SystemLibrary.execute_console_command(w, "rd.GoTo brokenspire")
    t0 = time.time()
    while time.time() - t0 < 60:
        yield from rwait(1.0); ts = town_state()
        if ts.get("name") == "Brokenspire" and ts.get("section", 0) == 1: break
    res["back"] = ts.get("name")
    # ---- an ambush
    xy = clear_spot("plains"); g.wild_put_her(*xy); yield from wait_chunks(30, 50); yield from rwait(1.0)
    c = cb(); c.set_health(c.get_max_health())
    hunters = []; t0 = time.time()
    while time.time() - t0 < 40 and not hunters:
        g.force_wild_encounter("roam_ambush")
        yield from rwait(1.5)
        hunters = [m for m in GS.get_all_actors_of_class(w, unreal.RDMonster) if m.get_editor_property("hunting") and not m.is_dead()]
    me = G["pawn"].get_actor_location()
    track = []
    if hunters:
        t1 = time.time()
        while time.time() - t1 < 12:
            c.set_health(c.get_max_health())
            ds = [dist2(m.get_actor_location(), me) / 100.0 for m in hunters if unreal.SystemLibrary.is_valid(m) and not m.is_dead()]
            if ds: track.append(round(min(ds), 1))
            if ds and min(ds) < 4.0: break
            yield from rwait(0.5)
    res["ambush"] = {"hunters": len(hunters), "track_m": track[:30], "aggro_m": g.get_editor_property("wild_aggro_distance") / 100.0}
    for m in hunters:
        if unreal.SystemLibrary.is_valid(m): m.destroy_actor()
    g.wild_drop_all(); g.wild_put_her(0.0, 0.0); yield from wait_chunks(30, 40)
    am = res["ambush"]
    ok = (res["storm"]["weather"] == 5 and res["storm"]["held"] and res["fog"]["weather"] == 7 and res["fog"]["held"] and not res["auto"]["held"]
          and res["goto"]["town"] == "Ashenreach" and res["goto"]["loaded"] == 1 and (res["goto"]["from_site_m"] or 9999) < 1600 and res["back"] == "Brokenspire"
          # (they come straight at her from beyond their noticing distance at their own chase speed (a slow kind: 1.5 m/s), the
          # distance falling at every sample: 10 m or more in 12 s)
          and am["hunters"] > 0 and len(am["track_m"]) >= 10 and am["track_m"][0] > am["aggro_m"]
          and (min(am["track_m"]) < 6.0 or (am["track_m"][0] - am["track_m"][-1] >= 10.0 and all(b_ <= a_ + 0.3 for a_, b_ in zip(am["track_m"], am["track_m"][1:])))))
    step_result("list10w", ok, **res)


# ------------------------------------------------------------------------------------------------ fast travel
def step_travel():
    g = G["gen"]; res = {}; quiet(True)
    yield from wait_ready(90)
    fp = G.get("found_places") or []
    if not fp:
        for p in places_near(0, 0, 20000):
            if p["kind"] not in ("town", "city"): g.wild_put_her(p["x"] - 20.0, p["y"]); yield from wait_chunks(20, 40); yield from rwait(1.0); fp = [p]; break
    tgt = fp[-1]
    g.wild_put_her(500.0, -900.0); yield from wait_chunks(30, 50); yield from rwait(1.0)
    # from the map: the place under the cross, F
    g.set_map_open(True); yield from rwait(0.5)
    g.set_wild_map_view(tgt["x"], tgt["y"], 20.0); yield from rwait(1.5)
    res["hover"] = map_state()["hover"]; res["hover_name"] = map_state()["hover_name"]
    yield from press("F"); yield from rwait(3.0)
    p = G["pawn"].get_actor_location()
    res["after"] = map_state(); res["from_place_m"] = round(math.hypot(p.x / 100.0 - tgt["x"], p.y / 100.0 - tgt["y"]), 1)
    # a town (Vel Morrath, found in the towns step; else Brokenspire)
    ti = TOWN_ID + 3 if G.get("vm_found") else TOWN_ID
    ok_t = g.wild_fast_travel(ti); yield from rwait(3.0)
    res["town_travel"] = ok_t; res["town_after"] = town_state()
    # refused in a fight: at a lair with its monsters after her
    lairs = [p_ for p_ in places_near(0, 0, 40000) if p_["kind"] == "lair"]
    if lairs:
        l = min(lairs, key=lambda q: math.hypot(q["x"], q["y"]))
        g.wild_put_her(l["x"] - 12.0, l["y"]); yield from wait_chunks(30, 50)
        quiet(False); yield from wait(3.0)
        res["combat"] = g.is_wild_combat()
        res["refused"] = not g.wild_fast_travel(TOWN_ID); res["refusal"] = map_state()["refusal"]
        quiet(True); cb().set_health(cb().get_max_health())
    quiet(False)
    ok = (res["hover"] == tgt["id"] and res["after"]["last_travel"] == tgt["name"] and res["from_place_m"] < 80 and res["town_travel"] and res["town_after"]["section"] == 1
          and (not lairs or (res["combat"] and res["refused"] and "enemies" in res["refusal"])))
    step_result("travel", ok, **res)


# ------------------------------------------------------------------------------------------------ save and load
def save_state():
    p = str(G["gen"].get_save_state()).split("|")
    return {"written": int(p[0]), "slot": p[1], "why": p[2], "arrived": int(p[3])}
def step_save():
    g = G["gen"]; res = {}; quiet(True)
    yield from wait_ready(90)
    g.wild_put_her(-2600.0, 1800.0); yield from wait_chunks(30, 50); yield from rwait(1.0)
    at = G["pawn"].get_actor_location()
    res["gold_before"] = g.get_gold(); res["found_before"] = state()["found"]; res["revealed_before"] = state()["revealed"]
    res["saved"] = g.save_game_now("save", "test"); res["info"] = str(g.get_save_info("save"))
    # the menu's lines: Save, Load, its page of two
    g.set_menu_open(True); yield from rwait(0.3)
    res["menu"] = [str(l) for l in g.get_menu_lines()]
    # (the list of 2026-11-04: "there is no way to name your own save": the Save page, a name typed with the keys, Enter)
    save_i = next(i for i, l in enumerate(res["menu"]) if "Save the game" in l)
    g.activate_menu_line(save_i); yield from rwait(0.3)
    res["save_page"] = [str(l) for l in g.get_menu_lines()]
    g.set_save_name_text("Test Sav")
    for k in ("E", "SpaceBar", "Seven"): yield from press(k)
    res["typed"] = str(g.get_save_name_text())
    yield from press("Enter"); yield from rwait(0.5)
    res["slots"] = [str(s) for s in g.get_save_slots()]
    g.set_menu_open(False); yield from rwait(0.2); g.set_menu_open(True); yield from rwait(0.2)
    load_i = next(i for i, l in enumerate([str(x) for x in g.get_menu_lines()]) if "Load a game" in l)
    g.activate_menu_line(load_i); yield from rwait(0.3)
    res["load_page"] = [str(l) for l in g.get_menu_lines()]
    g.set_menu_open(False)
    res["named_ok"] = res["typed"] == "Test Save 7" and any(s.startswith("save_test_save_7_") and "|Test Save 7|" in s for s in res["slots"]) and any("Test Save 7" in l for l in res["load_page"]) \
        and any(l.startswith("text|Name|") for l in res["save_page"])
    # something changed after the save, then the save loaded
    g.add_gold(250, "test"); g.wild_put_her(-1000.0, 1000.0); yield from rwait(1.0)
    G["travel_until"] = time.time() + 60
    res["load"] = g.load_game_from("save")
    t0 = time.time()
    while time.time() - t0 < 60:
        yield
        if UES.get_game_world() is None: continue
        refresh()
        if G.get("gen") and G["gen"].is_wild_ready() and int(str(G["gen"].get_save_state()).split("|")[3]) >= 1: break
    yield from rwait(3.0); refresh(); g = G["gen"]
    p = G["pawn"].get_actor_location()
    res["back_m"] = round(math.hypot(p.x - at.x, p.y - at.y) / 100.0, 1); res["gold_after"] = g.get_gold()
    res["found_after"] = state()["found"]; res["revealed_after"] = state()["revealed"]; res["save_state"] = save_state()
    G["travel_until"] = 0
    quiet(False)
    ok = (res["saved"] and res["info"] and any("Save the game" in l for l in res["menu"]) and any("Load a game" in l for l in res["menu"]) and res["load"] and res["named_ok"]
          and res["back_m"] < 10 and res["gold_after"] == res["gold_before"] and res["found_after"] >= res["found_before"] and res["revealed_after"] >= res["revealed_before"] * 0.95)
    step_result("save", ok, **res)

# ------------------------------------------------------------------------------------------------ the list of 2026-11-04
SHOT_DIR = SHOTS
def png_stats(path, box):
    """mean and standard deviation of the luma (0-255) of a part of a PNG (zlib only: the editor's Python has no image library)"""
    import zlib, struct
    data = open(path, "rb").read(); pos = 8; w = h = 0; ct = 6; idat = b""
    while pos + 8 <= len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8]); body = data[pos + 8:pos + 8 + ln]; pos += 12 + ln
        if typ == b"IHDR": w, h, bd, ct = struct.unpack(">IIBB", body[:10])
        elif typ == b"IDAT": idat += body
        elif typ == b"IEND": break
    bpp = 4 if ct == 6 else 3; raw = zlib.decompress(idat); stride = w * bpp
    prev = bytearray(stride); x0, y0, x1, y1 = int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)
    vals = []; i = 0
    for y in range(h):
        f = raw[i]; line = bytearray(raw[i + 1:i + 1 + stride]); i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0; b = prev[x]; c = prev[x - bpp] if x >= bpp else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                p_ = a + b - c; pa, pb, pc = abs(p_ - a), abs(p_ - b), abs(p_ - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        prev = line
        if y0 <= y < y1 and y % 4 == 0:
            for x in range(x0, x1, 4):
                o = x * bpp; vals.append(0.2126 * line[o] + 0.7152 * line[o + 1] + 0.0722 * line[o + 2])
    m = sum(vals) / max(len(vals), 1)
    return m, (sum((v - m) ** 2 for v in vals) / max(len(vals), 1)) ** 0.5
def png_grid(path, box, nx, ny):
    """the mean luma of each of nx x ny cells over a part of a PNG (one decoding)"""
    import zlib, struct
    data = open(path, "rb").read(); pos = 8; w = h = 0; ct = 6; idat = b""
    while pos + 8 <= len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8]); body = data[pos + 8:pos + 8 + ln]; pos += 12 + ln
        if typ == b"IHDR": w, h, bd, ct = struct.unpack(">IIBB", body[:10])
        elif typ == b"IDAT": idat += body
        elif typ == b"IEND": break
    bpp = 4 if ct == 6 else 3; raw = zlib.decompress(idat); stride = w * bpp
    prev = bytearray(stride); x0, y0, x1, y1 = int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)
    S = [[0.0] * nx for _ in range(ny)]; N = [[0] * nx for _ in range(ny)]; i = 0
    for y in range(h):
        f = raw[i]; line = bytearray(raw[i + 1:i + 1 + stride]); i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0; b = prev[x]; c = prev[x - bpp] if x >= bpp else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                p_ = a + b - c; pa, pb, pc = abs(p_ - a), abs(p_ - b), abs(p_ - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        prev = line
        if y0 <= y < y1 and y % 2 == 0:
            gy = min(ny - 1, (y - y0) * ny // max(y1 - y0, 1))
            for x in range(x0, x1, 4):
                o = x * bpp; gx = min(nx - 1, (x - x0) * nx // max(x1 - x0, 1))
                S[gy][gx] += 0.2126 * line[o] + 0.7152 * line[o + 1] + 0.0722 * line[o + 2]; N[gy][gx] += 1
    return [[S[j][k] / max(N[j][k], 1) for k in range(nx)] for j in range(ny)]
def sky_edge(path):
    """the sky's sharpest change from one strip to the next down a picture of the horizon (the upper 42 %), taken where three
    columns in four agree (an arc's edge spans the picture; a tree or a blade of grass does not)"""
    g_ = png_grid(path, (0.05, 0.0, 0.95, 0.42), 24, 40)
    best = 0.0
    for j in range(39):
        d = sorted(abs(g_[j + 1][k] - g_[j][k]) for k in range(24))
        best = max(best, d[int(0.75 * 23)])
    return round(best, 1)
def sky_state():
    p = str(G["gen"].get_sky_state()).split("|")
    k = ["weather", "cover", "rain", "wind", "fog", "snowing", "changes", "next_s", "clouds", "stars", "moon", "fog_cutoff_m", "rain_on", "snow_on", "wind_fx"]
    return {a: (b if a == "weather" else float(b)) for a, b in zip(k, p)}
def step_sky7():
    """the sky (the list's "clouds of different sizes and types, ... the sun if it's daytime, the moon if it's night time, stars
    if it's night if there's no cloud cover"; "when it's night time, there is no moonlight or starlight"; "no wind of weather
    effects"): the fog no longer over the sky; the noon sky not one grey (pictures measured); the clouds' cover changes the
    light; at night with a clear sky the stars and the moon, the moonlit ground not black; rain falling round her, snow in the
    cold; a new weather in its 4 to 9 minutes"""
    g = G["gen"]; res = {}; quiet(True)
    yield from wait_ready(90)
    g.wild_put_her(9000.0, -4000.0); yield from wait_chunks(35, 50); yield from rwait(1.0)
    st = sky_state(); res["begin"] = st
    def pic(name, pitch, yaw=30.0, box=(0.0, 0.0, 1.0, 0.45)):
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=yaw)); shot(name, "960x540")
        return os.path.join(SHOT_DIR, f"wd_{TAG}_{name}.png"), box
    g.set_town_hour(12.0); g.set_weather(1, True); yield from rwait(3.0)
    p_noon = pic("sky7_noon", 30.0); yield from rwait(1.5)
    sun_fair = float(str(g.get_day_night_state()).split("|")[4])
    g.set_weather(3, True); yield from rwait(2.0)
    sun_over = float(str(g.get_day_night_state()).split("|")[4]); p_over = pic("sky7_overcast", 30.0); yield from rwait(1.5)
    g.set_town_hour(0.5); g.set_weather(0, True); yield from rwait(3.0)
    night = sky_state(); p_night = pic("sky7_night", 40.0); yield from rwait(1.5)
    p_ground = pic("sky7_night_ground", -10.0, box=(0.0, 0.6, 1.0, 0.95)); yield from rwait(1.5)
    g.set_town_hour(11.0); g.set_weather(4, True); yield from rwait(3.0)
    rain = sky_state(); p_rain = pic("sky7_rain", 0.0, box=(0.0, 0.1, 1.0, 0.6)); yield from rwait(1.5)
    g.set_weather(0, True); yield from rwait(2.0); p_dry = pic("sky7_dry", 0.0, box=(0.0, 0.1, 1.0, 0.6)); yield from rwait(1.5)
    # (snow: in a cold biome the rain is snow)
    bl = {}
    for l in g.get_wild_biome_lines():
        q = str(l).split("|"); bl[q[0]] = (float(q[2]), float(q[3]))
    if "arctic regions" in bl:
        g.wild_put_her(*bl["arctic regions"]); yield from wait_chunks(35, 50); yield from rwait(1.0)
        g.set_weather(4, True); yield from rwait(2.5)
        res["snow"] = sky_state(); pic("sky7_snow", 0.0); yield from rwait(1.5)
    g.set_weather(1, True); g.set_town_hour(10.0)
    yield from rwait(1.0)
    S = {}
    for nm, (pth, box) in (("noon", p_noon), ("overcast", p_over), ("night", p_night), ("night_ground", p_ground), ("rain", p_rain), ("dry", p_dry)):
        if os.path.exists(pth): S[nm] = [round(x, 1) for x in png_stats(pth, box)]
    res["pictures"] = S; res["sun_lux"] = {"fair": sun_fair, "overcast": sun_over}; res["night"] = night; res["rain"] = rain
    quiet(False)
    ok = (st["clouds"] == 1 and st["fog_cutoff_m"] >= 1000 and 240 <= st["next_s"] + 0.0 <= 560 and sun_over < sun_fair * 0.5
          and night["stars"] > 0.5 and night["moon"] > 0.5 and rain["rain_on"] == 1
          and S.get("noon", [0, 0])[1] > 6.0 and S.get("night_ground", [0])[0] > 6.0 and res.get("snow", {}).get("snow_on", 0) == 1)
    step_result("sky7", ok, **res)

def life_lines():
    out = {"animal": [], "swarm": [], "counts": None}
    for l in G["gen"].get_wild_life_lines():
        p = str(l).split("|")
        if p[0] == "animal": out["animal"].append({"kind": p[1], "at": V(float(p[2]), float(p[3]), float(p[4])), "state": int(p[5]), "flee": float(p[6]), "fled": int(p[7])})
        elif p[0] == "swarm": out["swarm"].append({"name": p[1], "layer": int(p[5])})
        elif p[0] == "counts": out["counts"] = [int(x) for x in p[1:]]
    return out
def step_life7():
    """the animals and insects of each biome (the list's: "those animals should flee from the player if the player gets too close
    (1-3 meters)"): round her in three biomes some animals of the kinds that live there and insects or birds; an animal comes
    within its own flee distance of her (1 to 3 m) and runs: off at its run, metres away"""
    g = G["gen"]; res = {"visits": {}}; quiet(True)
    yield from wait_ready(90)
    bl = {}
    for l in g.get_wild_biome_lines():
        q = str(l).split("|"); bl[q[0]] = (float(q[2]), float(q[3]))
    g.set_town_hour(11.0); g.set_weather(1, True)
    for name in ("meadows", "taigas", "grasslands"):
        if name not in bl: continue
        g.wild_put_her(*bl[name]); yield from wait_chunks(35, 50)
        t0 = time.time()
        while time.time() - t0 < 25:
            yield
            L = life_lines()
            if len(L["animal"]) >= 3 and len(L["swarm"]) >= 2: break
        L = life_lines()
        res["visits"][name] = {"animals": sorted(set(a["kind"] for a in L["animal"])), "n": len(L["animal"]), "swarms": sorted(set(s["name"] for s in L["swarm"]))}
        shot(f"life7_{name.replace(' ', '_')}", "960x540"); yield from rwait(1.2)
    # (an animal she walks up to)
    p = G["pawn"].get_actor_location(); fwd = G["pawn"].get_actor_forward_vector()
    a = g.spawn_wild_animal_at("Deer", V(p.x + fwd.x * 700, p.y + fwd.y * 700, 0))
    yield from rwait(1.0)
    fl = {}
    if a:
        fd = a.get_flee_distance(); ap = a.get_actor_location()
        put(V(ap.x - fwd.x * (fd + 120), ap.y - fwd.y * (fd + 120), ap.z), z=ap.z); yield from rwait(1.0)
        s_far = a.get_state()
        put(V(ap.x - fwd.x * (fd - 30), ap.y - fwd.y * (fd - 30), ap.z), z=ap.z); yield from rwait(2.0)
        fl = {"flee_cm": round(fd, 1), "state_far": s_far, "state_near": a.get_state(), "fled": a.get_times_fled(), "ran_m": round(dist2(a.get_actor_location(), ap) / 100.0, 1)}
        shot("life7_flee", "960x540"); yield from rwait(1.0)
    res["flee"] = fl
    g.set_town_hour(0.5); yield from rwait(8.0); res["night_swarms"] = sorted(set(s["name"] for s in life_lines()["swarm"])); g.set_town_hour(11.0)
    quiet(False)
    vs = [v for v in res["visits"].values()]
    ok = (len(vs) >= 2 and all(v["n"] >= 1 for v in vs) and sum(len(v["swarms"]) > 0 for v in vs) >= 2 and fl.get("state_far") != 3 and fl.get("fled", 0) >= 1
          and 100 <= fl.get("flee_cm", 0) <= 300 and fl.get("ran_m", 0) > 3 and any("Fireflies" in n or "Flies" in n for n in res["night_swarms"]))
    step_result("life7", ok, **res)

def step_ground7():
    """the land (the list's: "all of the ground terrain in the wilderness is uniformly flat. there should be natural hills, dips,
    ridges, berms"; "the transition between terrain types is too abrupt and looks like a straight line"; "the different terrain
    types are in regular squares and grids on the map"; "the road ... is not visible in the wilderness"; "the biome's name
    should also be visible under the mini map"): over 300 m in six regions the ground rises and falls at short and long scales;
    the blend between two regions takes kilometres; a farm's fields along a line are of many lengths (a grid's are two); the
    road wide enough to be seen; the region's name under the minimap"""
    g = G["gen"]; res = {"relief": {}}; quiet(True)
    yield from wait_ready(90)
    bl = {}
    for l in g.get_wild_biome_lines():
        q = str(l).split("|"); bl[q[0]] = (float(q[2]), float(q[3]))
    # (a region's nearest cell to Brokenspire can be a town's own, whose ground is levelled to 1.15 km on purpose: the line
    # is moved out until it is 1.4 km from every town and still in the region)
    tl = [(t["x"], t["y"]) for t in towns().values()]
    def clear_of_towns(x, y):
        return all(math.hypot(x - a, y - b) > 1400.0 and math.hypot(x + 300.0 - a, y - b) > 1400.0 for a, b in tl)
    res["lines"] = {}
    for name in ("grasslands", "plains", "farms", "meadows", "temperate aspen", "tundras"):
        if name not in bl: continue
        x, y = bl[name]
        if not clear_of_towns(x, y):
            a, b = min(tl, key=lambda t: math.hypot(x - t[0], y - t[1]))
            dx, dy = x - a, y - b; n = math.hypot(dx, dy) or 1.0
            found = None
            for ang in range(0, 360, 30):
                ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
                ux, uy = (dx / n) * ca - (dy / n) * sa, (dx / n) * sa + (dy / n) * ca
                for r in range(1500, 4001, 250):
                    px, py = a + ux * r, b + uy * r
                    if clear_of_towns(px, py) and sample(px, py)["biome"] == name and sample(px + 300.0, py)["biome"] == name:
                        found = (px, py); break
                if found: break
            if not found: continue
            x, y = found
        res["lines"][name] = [round(x), round(y)]
        hs = [sample(x + k * 5.0, y)["h"] for k in range(61)]
        dif = [abs(hs[k + 1] - hs[k]) for k in range(60)]
        # (short scale: what is left after a 60 m running mean)
        mean = [sum(hs[max(0, k - 6):k + 7]) / len(hs[max(0, k - 6):k + 7]) for k in range(61)]
        res["relief"][name] = {"range_m": round(max(hs) - min(hs), 2), "short_m": round(max(abs(h - m) for h, m in zip(hs, mean)), 2), "max_step_5m": round(max(dif), 2)}
        yield
    # (the blend: the first region's weight along 8 km from a region's middle outward)
    if "farms" in bl:
        x, y = bl["farms"]
        w = [sample(x + k * 250.0, y) for k in range(33)]
        res["blend"] = [(round(s["w1"], 2), s["biome"]) for s in w[::2]]
        ch = [k for k in range(32) if w[k]["biome"] != w[k + 1]["biome"]]
        mixed = [s for s in w if s["w1"] < 0.85]
        res["blend_mixed_km"] = round(len(mixed) * 0.25, 2)
    # (the fields along a 2 km line: their lengths)
    fx, fy = bl.get("farms", (0.0, 0.0))
    runs, cur = [], 0
    for k in range(400):
        f = sample(fx + k * 5.0, fy + 300.0)["field"] > 0.5
        if f: cur += 5
        elif cur: runs.append(cur); cur = 0
    import statistics
    res["fields"] = {"n": len(runs), "mean_m": round(statistics.mean(runs), 1) if runs else 0, "cv": round(statistics.pstdev(runs) / statistics.mean(runs), 2) if len(runs) > 2 else 0}
    # (the road outside Brokenspire's gate: across it, where it is a road; the town loaded for its gate)
    if town_state()["name"] != "Brokenspire" or town_state()["section"] != 1:
        g.wild_put_her(600.0, 600.0); g.load_wild_town(0, True); yield from rwait(1.0)
    # (the roads leave the gate and wind off toward the next town: on rings round the gate, where a road crosses, its width
    # across it (the narrowest of 18 ways through the crossing's middle))
    gate = place("gate")
    if gate:
        gx, gy = gate.x / 100.0, gate.y / 100.0
        best, cross = 0.0, []
        for rad in (400.0, 650.0):
            steps = int(2 * math.pi * rad / 1.0)
            on = [sample(gx + rad * math.cos(2 * math.pi * k / steps), gy + rad * math.sin(2 * math.pi * k / steps))["road"] > 0.5 for k in range(steps)]
            k = 0
            while k < steps:
                if on[k] and not on[k - 1]:
                    e = k
                    while on[e % steps] and e - k < steps: e += 1
                    m = (k + e - 1) / 2.0; a = 2 * math.pi * m / steps
                    cx, cy = gx + rad * math.cos(a), gy + rad * math.sin(a)
                    wid = 1e9
                    for j in range(18):
                        t = math.pi * j / 18; ux, uy = math.cos(t), math.sin(t)
                        cnt = 1
                        for sgn in (1, -1):
                            q = 1
                            while q < 60 and sample(cx + sgn * ux * q * 0.25, cy + sgn * uy * q * 0.25)["road"] > 0.5: q += 1; cnt += 1
                        wid = min(wid, cnt * 0.25)
                    cross.append([rad, round(cx), round(cy), wid]); best = max(best, wid)
                    k = e
                else:
                    k += 1
            yield
        res["road_m"] = best; res["road_crossings"] = cross
    # (the region's name under the minimap)
    g.wild_put_her(*bl.get("meadows", (9000.0, -4000.0))); yield from wait_chunks(35, 50); yield from rwait(1.5)
    res["minimap_label"] = str(G["pc"].get_hud().get_biome_label_drawn())
    shot("ground7_minimap", "1280x720"); yield from rwait(1.2)
    quiet(False)
    rl = list(res["relief"].values())
    ok = (len(rl) >= 5 and sum(1 for r in rl if r["range_m"] > 4.0 and r["short_m"] > 0.6) >= 4 and all(r["max_step_5m"] < 4.0 for r in rl)
          and res.get("blend_mixed_km", 0) >= 1.0 and res["fields"]["n"] >= 6 and res["fields"]["cv"] > 0.3 and res.get("road_m", 0) >= 4.0
          and "MEADOWS" in res["minimap_label"])
    step_result("ground7", ok, **res)

def step_music7():
    """the music (the list's: "after 5-10 minutes, the music should change to another appropriate song for the scene"): the
    wilds' set out there, the town's in its walls; when its time comes a new track of the scene's set"""
    g = G["gen"]; res = {}
    yield from wait_ready(90)
    g.set_town_hour(11.0)
    g.wild_put_her(9000.0, -4000.0); yield from wait_chunks(30, 40); yield from rwait(6.0)
    s1 = str(g.get_music_scene()).split("|"); t1 = str(g.get_music_track())
    g.rotate_music_now(); yield from rwait(7.0)
    s2 = str(g.get_music_scene()).split("|"); t2 = str(g.get_music_track())
    res["wild"] = {"scene": s1[0], "track": t1, "rotations": int(s1[1]), "next_in_s": float(s1[2]) - now()}
    res["rotated"] = {"scene": s2[0], "track": t2, "rotations": int(s2[1]), "next_in_s": float(s2[2]) - now()}
    g.wild_put_her(600.0, 600.0); g.load_wild_town(0, True); yield from rwait(2.0)
    sq = place("square")
    if sq: put(sq); yield from rwait(6.0)
    res["town"] = str(g.get_music_scene()).split("|")[0]
    ok = (res["wild"]["scene"].startswith("Music.Wild") and res["rotated"]["rotations"] == res["wild"]["rotations"] + 1 and t2 != t1 and t2
          and 290 <= res["rotated"]["next_in_s"] <= 610 and res["town"].startswith("Music.Town"))
    step_result("music7", ok, **res)

def step_memprobe():
    """(a probe: memory after teleports far apart, each building its chunks anew; a memreport at the end)"""
    g = G["gen"]; res = {"runs": []}; quiet(True)
    yield from wait_ready(90)
    pts = [(9000, -4000), (30000, 20000), (-20000, -15000), (60000, -30000), (15000, 50000), (-40000, 10000), (80000, 5000), (5000, -60000)]
    for x, y in pts:
        g.wild_put_her(float(x), float(y)); yield from wait_chunks(40, 56); yield from rwait(1.0)
        yield from rwait(2.5)
        m = gc_mem(); s = state()
        res["runs"].append({"at": [x, y], "mem": m, "committed": round(g.get_memory_mb(True)), "chunks": s["chunks"], "built": s["built"], "dropped": s["dropped"], "tiles": map_state()["tiles"], "monsters": len(g.get_monsters())})
    unreal.SystemLibrary.execute_console_command(G["w"], "memreport -full")
    yield from rwait(8.0)
    quiet(False)
    step_result("memprobe", True, **res)

# ------------------------------------------------------------------------------------------------ the chunks made in steps
def build_stats(reset=False):
    p = str(G["gen"].get_wild_build_stats(reset)).split("|")
    parts = {}
    for kv in (p[5].split(",") if len(p) > 5 and p[5] else []):
        k, _, v = kv.partition("="); parts[k] = float(v)
    return {"streamed": int(p[0]), "step_ms_max": float(p[1]), "frame_build_ms_max": float(p[2]), "chunk_ms_max": float(p[3]), "building": int(p[4]), "parts": parts,
            "trims": int(p[7]) if len(p) > 7 else None}
def step_build7():
    """(2026-11-07, TODO's "a chunk's making stutters": one chunk made in a frame took 45 to 72 ms.) The same flight over new
    ground twice from the same start, the chunks made in one go each (the old way) and in steps: what making took of each
    frame on the game thread, the longest step and part, the frames' own times (the test's tick), and every chunk made the
    same both ways (instances, triangles, trees, props, its grass round her)"""
    g = G["gen"]; res = {"modes": {}}; quiet(True)
    yield from wait_ready(90)
    sx, sy = 3200.0, -9000.0
    res["budget_ms"] = g.get_editor_property("wild_build_budget_ms")
    made = {}
    for mode in (False, True):
        name = "steps" if mode else "whole"
        g.set_editor_property("wild_build_steps", mode)
        g.wild_drop_all(); g.wild_put_her(sx, sy); yield from wait_chunks(40, 56); yield from rwait(1.5)
        build_stats(True)
        fly(True); G["rec"] = []
        for k in range(97):      # (2.4 km north-east at 100 m/s: 25 m every 0.25 s)
            hover_at(sx + k * 10.0, sy + k * 23.0); yield from rwait(0.25)
        t0 = time.time()
        while time.time() - t0 < 30 and state()["in_flight"] > 0: yield
        rec = G.pop("rec"); yield from rwait(0.5)
        dts = sorted(d * 1000.0 for d, _ in rec)
        # (each long frame against what the counters say happened between the tick before and this one: a chunk finished, a
        # step of making, chunks dropped, the memory's collection asked or trimmed)
        rows = []
        for d, s in rec:
            p = s.split("|")
            th = tuple(float(x) for x in p[10:14]) if len(p) >= 14 else (0.0, 0.0, 0.0, 0.0)
            rows.append((d * 1000.0, int(p[0]), int(p[6]), int(p[7]), int(p[8]), int(p[9])) + th)
        long_ = []
        for i in range(1, len(rows)):
            if rows[i][0] <= 50.0: continue
            a, b = rows[i - 1], rows[i]
            why = [w for w, k in (("chunk done", 1), ("making", 2), ("trim", 3), ("dropped", 4)) if b[k] != a[k]]
            if b[5] != a[5]: why.append(f"trim stage {a[5]}->{b[5]}")
            long_.append({"ms": round(b[0], 1), "why": why or ["nothing of the chunks"]})
        st = build_stats(); cs = chunks(); fly(False)
        st["long_frames"] = long_[:30]
        st["long_without_making"] = sum(1 for x in long_ if "making" not in x["why"])
        # (s2: most long frames came with no chunk work at all (the editor's own, the new ground drawn); what making costs a
        # frame is the frames with making against those without. A frame's work shows in the tick after it or the one after
        # that (the test's tick is Slate's, the frame's drawing comes after it): both lags)
        # (and each thread's time in those frames, stat unit's: the game thread, the render thread, the RHI, the GPU)
        def mean(v): return round(sum(v) / len(v), 1) if v else None
        for lag in (0, 1):
            mk, no = [], []
            for i in range(1 + lag, len(rows)):
                (mk if rows[i - lag][2] != rows[i - lag - 1][2] else no).append(rows[i])
            if mk and no:
                a = sorted(r[0] for r in mk); b = sorted(r[0] for r in no)
                st[f"lag{lag}"] = {"making_frames": len(mk), "mean_ms": mean(a), "others_mean_ms": mean(b), "excess_ms": round(mean(a) - mean(b), 1),
                                   "p90_ms": round(a[int(len(a) * 0.9)], 1), "others_p90_ms": round(b[int(len(b) * 0.9)], 1),
                                   "threads_making": {k: mean([r[6 + j] for r in mk]) for j, k in enumerate(("game", "render", "rhi", "gpu"))},
                                   "threads_others": {k: mean([r[6 + j] for r in no]) for j, k in enumerate(("game", "render", "rhi", "gpu"))}}
        st["long_threads"] = [dict(zip(("ms", "game", "render", "rhi", "gpu"), (round(r[0], 1),) + tuple(round(x, 1) for x in r[6:10]))) for r in rows if r[0] > 50.0][:20]
        st["excess_ms"] = max(st.get(f"lag{l}", {}).get("excess_ms", 0.0) for l in (0, 1))
        made[name] = {f"{c['x']},{c['y']}": (c["inst"], c["tris"], c["trees"], c["props"], c["monsters"], c["near_hism"]) for c in cs}
        st["frames"] = len(dts); st["frame_ms_p50"] = round(dts[len(dts) // 2], 1) if dts else None
        st["frame_ms_p99"] = round(dts[min(len(dts) - 1, int(len(dts) * 0.99))], 1) if dts else None
        st["frame_ms_max"] = round(dts[-1], 1) if dts else None
        st["frames_over_50ms"] = sum(1 for d in dts if d > 50.0); st["frames_over_100ms"] = sum(1 for d in dts if d > 100.0)
        st["chunks"] = len(cs); st["making_after"] = sum(1 for c in cs if c.get("making"))
        res["modes"][name] = st
    g.set_editor_property("wild_build_steps", True)
    both = sorted(set(made["whole"]) & set(made["steps"]))
    res["compared_chunks"] = len(both)
    res["differ"] = [{"at": k, "whole": made["whole"][k], "steps": made["steps"][k]} for k in both if made["whole"][k] != made["steps"][k]][:8]
    quiet(False)
    W, S = res["modes"]["whole"], res["modes"]["steps"]
    # (s1-s4: a streamed chunk's making measured 12 to 16 ms at most in one go, not the 45 to 72 of the look step's records,
    # which were chunks she is put on (cooked at once). The frames with making were 12 to 16 ms longer than those without both
    # ways: stat unit's threads (s4) put it in the drawing (the render thread 40-62 ms against 29-33, the GPU 33-59 against
    # 28-31: the new ground drawn), not in the game thread's making. Judged on what the steps change, the game thread: the
    # longest step and the most making in a frame against a whole chunk's; the frames' and threads' times are recorded)
    ok = (W["streamed"] >= 40 and S["streamed"] >= 40 and res["compared_chunks"] >= 40 and not res["differ"] and S["making_after"] == 0
          and S["step_ms_max"] <= 0.6 * W["chunk_ms_max"] and S["frame_build_ms_max"] <= 0.75 * W["chunk_ms_max"])
    step_result("build7", ok, **res)


# ------------------------------------------------------------------------------------------------ the captain's quests
def wq():
    out = {}
    for l in G["gen"].get_wild_quest_lines():
        p = str(l).split("|")
        out[p[0]] = {"id": int(p[1]), "name": p[2], "x": float(p[3]), "y": float(p[4]), "kind": p[5], "n": int(p[6]), "killed": int(p[7]), "progress": int(p[8]),
                     "rx": float(p[9]), "ry": float(p[10]), "yaw": float(p[11]), "shown": int(p[12])}
    return out
def quest_of(qid):
    for l in G["gen"].get_quest_lines():
        p = str(l).split("|")
        if p[0] == qid: return {"state": p[3], "progress": int(p[4]), "count": int(p[5]), "hint": p[6]}
    return None
def panel(): return [str(l).split("|") for l in G["gen"].get_town_panel_lines()]
def line_of(act, has=""):
    for i, p in enumerate(panel()):
        if p[0] == act and has in p[1]: return i
    return -1
def at_captain():
    """her before Brokenspire's captain, his panel opened by F (884's talk_to)"""
    g = G["gen"]
    for f in folk():
        if f["role"] != "Captain": continue
        at = g.get_townsfolk(f["i"]).get_actor_location()
        for dx, dy, yaw in ((110, 0, 180.0), (-110, 0, 0.0), (0, 110, -90.0), (0, -110, 90.0)):
            put(V(at.x + dx, at.y + dy, 0), yaw=yaw)
            if f["title"] in str(g.describe_nearest(G["pawn"].get_actor_location())): break
        g.interact_nearest(G["pawn"].get_actor_location())
        return str(g.get_town_panel()) == "talk"
    return False
def road_within(x, y, max_m=150.0):
    """metres from (x, y) to the nearest road (a sample with road > 0.3), rings of 5 m"""
    for r in range(0, int(max_m) + 1, 5):
        for k in range(24 if r else 1):
            a = k * math.pi / 12.0
            if sample(x + math.cos(a) * r, y + math.sin(a) * r)["road"] > 0.3: return r
    return None
def monsters_near(x, y, r_m):
    return [m for m in G["gen"].get_monsters() if m and not m.is_dead() and dist2(m.get_actor_location(), V(x * 100.0, y * 100.0, 0)) < r_m * 100.0]
def to_brokenspire():
    g = G["gen"]
    g.wild_fast_travel(TOWN_ID); yield from rwait(2.0)
    t0 = time.time()
    while time.time() - t0 < 40 and not any(f["role"] == "Captain" for f in folk()): yield
    yield from rwait(1.0)
def step_quests():
    """(2026-11-07) the captain's "Wolves on the Mill Road" and "The Lost Patrol": their places (beside the roads north and to Vel
    Morrath, on dry ground, past the town's level ground), taken at the captain (on the map, named, not found: no travel
    there), the den's four killed (three, the chunks made again: the three stay dead, the fourth killed: done), the patrol
    found at the watchtower's door (not from 10 m), both turned in for their gold; pictures of the den and the tower"""
    g = G["gen"]; res = {}; quiet(True)
    yield from wait_ready(90)
    Q = wq(); res["places"] = Q
    den, tw = Q.get("wild:wolves"), Q.get("wild:patrol")
    assert den and tw, "no quest places"
    for k, p in (("den", den), ("tower", tw)):
        s = sample(p["x"], p["y"])
        res[k] = {"from_brokenspire_km": round(math.hypot(p["x"], p["y"]) / 1000.0, 2), "water": s["water"], "h": round(s["h"], 1), "biome": s["biome"], "road_m": road_within(p["x"], p["y"])}
    # taken at the captain
    yield from to_brokenspire()
    res["captain_panel"] = at_captain(); yield from rwait(0.3)
    res["offered"] = [p[1] for p in panel() if p[0] == "accept"]
    res["accept_wolves"] = g.activate_town_entry(line_of("accept", "Mill Road")); yield from rwait(0.2)
    res["accept_patrol"] = g.activate_town_entry(line_of("accept", "Lost Patrol")); yield from rwait(0.2)
    g.close_town_panel(); yield from rwait(0.3)
    res["taken"] = {q: quest_of(q) for q in ("captain_wolves", "captain_patrol")}
    Q = wq(); res["on_map"] = {k: v["shown"] for k, v in Q.items()}
    res["travel_refused"] = not g.wild_fast_travel(den["id"]); res["refusal"] = map_state()["refusal"]
    # the den: its pack of four
    fw = (math.cos(math.radians(den["yaw"])), math.sin(math.radians(den["yaw"])))
    g.wild_put_her(den["x"] + fw[0] * 30.0, den["y"] + fw[1] * 30.0); yield from wait_chunks(30, 50); yield from rwait(1.0)
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-15, yaw=den["yaw"] + 180.0)); yield from rwait(0.6)
    shot("quest_den", "1280x720"); yield from rwait(1.2)
    pack = monsters_near(den["x"], den["y"], 15.0)
    res["den_pack"] = {"alive": len(pack), "kinds": sorted(set(str(m.get_editor_property("monster_name")) for m in pack))}
    for m in pack[:3]: m.apply_damage(1e7, G["pawn"])
    yield from rwait(1.0)
    res["after_three"] = {"progress": wq()["wild:wolves"]["progress"], "killed": wq()["wild:wolves"]["killed"], "quest": quest_of("captain_wolves")}
    g.wild_drop_all(); g.wild_put_her(den["x"] + fw[0] * 30.0, den["y"] + fw[1] * 30.0); yield from wait_chunks(30, 50); yield from rwait(1.0)
    left = monsters_near(den["x"], den["y"], 15.0); res["again_alive"] = len(left)
    for m in left: m.apply_damage(1e7, G["pawn"])
    yield from rwait(1.0)
    res["after_all"] = {"progress": wq()["wild:wolves"]["progress"], "killed": wq()["wild:wolves"]["killed"], "quest": quest_of("captain_wolves")}
    # the watchtower: the remains before its doorway
    fw = (math.cos(math.radians(tw["yaw"])), math.sin(math.radians(tw["yaw"])))
    g.wild_put_her(tw["rx"] + fw[0] * 30.0, tw["ry"] + fw[1] * 30.0); yield from wait_chunks(30, 50); yield from rwait(1.0)
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=tw["yaw"] + 180.0)); yield from rwait(0.6)
    shot("quest_tower", "1280x720"); yield from rwait(1.2)
    res["tower_guards"] = len(monsters_near(tw["x"], tw["y"], 15.0))
    cm = g.get_editor_property("wild_chunk_m")
    mine = [c for c in chunks() if c["x"] == math.floor(tw["x"] / cm) and c["y"] == math.floor(tw["y"] / cm)]
    res["tower_props"] = mine[0]["props"] if mine else -1
    for m in monsters_near(tw["x"], tw["y"], 15.0): m.apply_damage(1e7, G["pawn"])
    yield from rwait(0.5)
    def stand(d):
        z = sample(tw["rx"] + fw[0] * d, tw["ry"] + fw[1] * d)["z"]
        G["pawn"].set_actor_location(V((tw["rx"] + fw[0] * d) * 100.0, (tw["ry"] + fw[1] * d) * 100.0, z + 110.0), False, True)
    stand(10.0); yield from rwait(1.0)
    res["patrol_at_10m"] = wq()["wild:patrol"]["progress"]
    stand(2.5); yield from rwait(1.0)
    res["patrol_at_2_5m"] = wq()["wild:patrol"]["progress"]; res["patrol_quest"] = quest_of("captain_patrol")
    # turned in
    yield from to_brokenspire()
    g0 = g.get_gold()
    res["captain_again"] = at_captain(); yield from rwait(0.3)
    res["turnin_lines"] = [p[1] for p in panel() if p[0] == "turnin"]
    for _ in range(2):
        i = line_of("turnin")
        if i >= 0: g.activate_town_entry(i); yield from rwait(0.2)
    g.close_town_panel(); yield from rwait(0.3)
    res["gold"] = g.get_gold() - g0
    res["done"] = {q: quest_of(q)["state"] for q in ("captain_wolves", "captain_patrol")}
    res["on_map_after"] = {k: v["shown"] for k, v in wq().items()}
    quiet(False)
    ok = (1.7 <= res["den"]["from_brokenspire_km"] <= 4.6 and res["den"]["water"] == 0 and res["den"]["road_m"] is not None and 30 <= res["den"]["road_m"] <= 90
          and 2.9 <= res["tower"]["from_brokenspire_km"] <= 6.2 and res["tower"]["water"] == 0
          and res["captain_panel"] and res["accept_wolves"] and res["accept_patrol"] and all(v and v["state"] == "taken" for v in res["taken"].values())
          and all(v == 1 for v in res["on_map"].values()) and res["travel_refused"]
          and res["den_pack"]["alive"] == 4 and res["after_three"]["progress"] == 0 and res["after_three"]["killed"] == 3
          and res["again_alive"] == 1 and res["after_all"]["progress"] == 1 and res["after_all"]["quest"]["state"] == "ready"
          and res["tower_guards"] == 3 and res["tower_props"] > 10 and res["patrol_at_10m"] == 0 and res["patrol_at_2_5m"] == 1 and res["patrol_quest"]["state"] == "ready"
          and res["gold"] == 320 and all(v == "done" for v in res["done"].values()) and all(v == 0 for v in res["on_map_after"].values()))
    step_result("quests", ok, **res)


# ------------------------------------------------------------------------------------------------ the list of 2026-11-07 (docs/improvements8.txt)
def biome_lines():
    bl = {}
    for l in G["gen"].get_wild_biome_lines():
        q = str(l).split("|"); bl[q[0]] = (float(q[2]), float(q[3]))
    return bl
def clear_spot(name, rmin=1500, rmax=5000):
    """a point of the region 1.4 km or more from every town (a town's ground is level on purpose)"""
    bl = biome_lines()
    if name not in bl: return None
    x, y = bl[name]; tl = [(t["x"], t["y"]) for t in towns().values()]
    for r in [0] + list(range(rmin, rmax + 1, 500)):
        for ang in range(0, 360, 45):
            px, py = x + math.cos(math.radians(ang)) * r, y + math.sin(math.radians(ang)) * r
            if all(math.hypot(px - a, py - b) > 1400.0 for a, b in tl) and sample(px, py)["biome"] == name and sample(px, py)["water"] == 0:
                return (px, py)
    return None
# ------------------------------------------------------------------------------------------------ the list of 2026-11-10's sixth phase
def wild_houses():
    out, doors = [], []
    for l in G["gen"].get_wild_house_lines():
        p = str(l).split("|")
        if p[0] == "house": out.append({"x": float(p[3]), "y": float(p[4]), "z": float(p[5]), "doors": int(p[6]), "furniture": int(p[7]), "lit": p[8] == "1", "floor": float(p[9]), "of": p[10], "hx": float(p[11]), "hy": float(p[12]), "yaw": float(p[13])})
        elif p[0] == "door": doors.append({"x": float(p[1]), "y": float(p[2]), "z": float(p[3]), "alpha": float(p[4]), "to": float(p[5])})
    return out, doors
def in_house(h, q, pad=0.0):
    a = math.radians(-h["yaw"]); dx, dy = q.x - h["x"], q.y - h["y"]
    lx, ly = dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)
    return abs(lx) <= h["hx"] + pad and abs(ly) <= h["hy"] + pad
def walk_to(pt, sec=6.0, near=60.0):
    t0 = time.time()
    while time.time() - t0 < sec:
        q = G["pawn"].get_actor_location(); dv = V(pt.x - q.x, pt.y - q.y, 0); n_ = math.hypot(dv.x, dv.y)
        if n_ < near: return True
        G["pawn"].add_movement_input(V(dv.x / n_, dv.y / n_, 0), 1.0, False); yield
    return False
def plants_in(h):
    """the plants' instances standing in a house's room (every chunk's foliage, the near grass too)"""
    n = 0; r = max(h["hx"], h["hy"]) * 1.5
    box = unreal.Box(min=V(h["x"] - r, h["y"] - r, h["z"] - 3000), max=V(h["x"] + r, h["y"] + r, h["z"] + 3000))
    for c in GS.get_all_actors_of_class(G["w"], unreal.RDWildChunk):
        for hm in c.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent):
            for i in hm.get_instances_overlapping_box(box, True) or []:
                t = hm.get_instance_transform(i, True)
                t = t[1] if isinstance(t, tuple) else t
                if t and in_house(h, t.translation, -10.0): n += 1
    return n
def step_houses10():
    """"the buildings in the wilderness do not have an interior and there is no way to get inside or climb any stairs on the outside":
    at a lone house or a village and at a farmstead: each house laid with its doors, furniture and lamp; she opens a door by F from
    outside (it swings open), walks in by her own movement, stands on its floor inside its room (her feet within 15 cm of the floor),
    no plant stands in the room; a picture inside; she walks out and shuts it"""
    g = G["gen"]; res = {"visits": []}; quiet(True)
    yield from wait_ready(90)
    near = sorted([p for p in places_near(0, 0, 25000) if p["kind"] in ("house", "village")], key=lambda p: math.hypot(p["x"], p["y"]))
    fs = [str(x).split("|") for x in g.find_wild_farmsteads(0.0, 0.0, 3500.0)]
    goals = [(p["kind"], p["name"], p["x"], p["y"]) for p in near[:2]] + [("farmstead", f[1], float(f[2]), float(f[3])) for f in fs[:1]]
    for kind, name, x, y in goals:
        v = {"kind": kind, "name": name}
        g.wild_drop_all(); g.wild_put_her(x - 40.0, y); yield from wait_chunks(30, 50); yield from rwait(2.0)
        hs, ds = wild_houses()
        hs = [h for h in hs if math.hypot(h["x"] / 100.0 - x, h["y"] / 100.0 - y) < 60.0 and h["doors"] > 0]
        v["houses"] = len(hs)
        if not hs: res["visits"].append(v); continue
        h = min(hs, key=lambda h: math.hypot(h["x"] / 100.0 - x, h["y"] / 100.0 - y)); v["house"] = {k: h[k] for k in ("of", "doors", "furniture", "lit", "floor")}
        d = min(ds, key=lambda d: math.hypot(d["x"] - h["x"], d["y"] - h["y"]) if math.hypot(d["x"] - h["x"], d["y"] - h["y"]) < max(h["hx"], h["hy"]) * 1.6 else 1e9)
        out = V(d["x"] - h["x"], d["y"] - h["y"], 0); n_ = math.hypot(out.x, out.y) or 1.0; out = V(out.x / n_, out.y / n_, 0)
        # (3.5 m out, past the steps a house on a slope has before its door (up to six, 2.5 m), then up to the door)
        st = V(d["x"] + out.x * 350, d["y"] + out.y * 350, 0)
        put(st, yaw=math.degrees(math.atan2(-out.y, -out.x)), z=g.wild_ground_z(st)); yield from rwait(0.8)
        v["to_door"] = yield from walk_to(V(d["x"] + out.x * 110, d["y"] + out.y * 110, 0), 6.0, 40.0)
        yield from rwait(0.3)
        v["prompt"] = str(g.describe_nearest(G["pawn"].get_actor_location()))
        v["f"] = str(g.interact_nearest(G["pawn"].get_actor_location())); yield from rwait(1.6)
        _hs, ds2 = wild_houses(); dn = min(ds2, key=lambda e: math.hypot(e["x"] - d["x"], e["y"] - d["y"])); v["door_open"] = dn["alpha"]
        # (in by her own movement: through the door, then to the room's middle)
        r1 = yield from walk_to(V(d["x"] - out.x * 150, d["y"] - out.y * 150, 0), 6.0)
        r2 = yield from walk_to(V(h["x"], h["y"], 0), 6.0, 90.0)
        yield from rwait(0.6)
        q = G["pawn"].get_actor_location(); hh = G["pawn"].get_component_by_class(unreal.CapsuleComponent).get_scaled_capsule_half_height()
        v["walked_in"] = [r1, r2]; v["inside"] = in_house(h, q); v["feet_over_floor_cm"] = round(q.z - hh - h["floor"], 1)
        v["plants_in_room"] = plants_in(h)
        # (a picture of the room from her place, the camera's way the back wall)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-20, yaw=math.degrees(math.atan2(-out.y, -out.x)))); yield from rwait(1.2)
        sn = f"houses10_{len(res['visits'])}_{kind}"; shot(sn, "1280x720"); v["shot"] = sn; yield from rwait(1.5)
        # (out again and shut)
        yield from walk_to(V(d["x"] + out.x * 170, d["y"] + out.y * 170, 0), 8.0)
        v["f_shut"] = str(g.interact_nearest(G["pawn"].get_actor_location())); yield from rwait(1.6)
        _hs, ds3 = wild_houses(); v["door_after"] = min(ds3, key=lambda e: math.hypot(e["x"] - d["x"], e["y"] - d["y"]))["alpha"]
        res["visits"].append(v)
    g.wild_drop_all(); g.wild_put_her(0.0, 0.0); yield from wait_chunks(30, 40)
    quiet(False)
    done = [v for v in res["visits"] if "house" in v]
    ok = len(done) >= 2 and any(v["kind"] == "farmstead" for v in done) and all(
        v["house"]["furniture"] >= 5 and v["house"]["lit"] and "open the door" in v["prompt"] and v["door_open"] > 0.95 and v["inside"]
        and abs(v["feet_over_floor_cm"]) < 15 and v["plants_in_room"] == 0 and v["door_after"] < 0.05 for v in done)
    step_result("houses10", ok, **res)

def step_tower10():
    """the Old Watchtower climbed: she walks in at its doorway from the road, up its spiral by her own movement to the second storey's
    top, onto its floor (it holds her there); a picture from the top"""
    g = G["gen"]; res = {}; quiet(True)
    yield from wait_ready(90)
    tw = wq().get("wild:patrol")
    assert tw, "no tower"
    yaw = tw["yaw"]; fw = (math.cos(math.radians(yaw)), math.sin(math.radians(yaw)))
    g.wild_drop_all(); g.wild_put_her(tw["x"] + fw[0] * 25.0, tw["y"] + fw[1] * 25.0); yield from wait_chunks(30, 50); yield from rwait(2.0)
    tl = [str(l).split("|") for l in g.get_wild_tower_lines()]
    tl = [t for t in tl if math.hypot(float(t[1]) / 100.0 - tw["x"], float(t[2]) / 100.0 - tw["y"]) < 20.0]
    res["tower_lines"] = tl[-1:] if tl else None
    if not tl: quiet(False); step_result("tower10", False, **res); return
    t = tl[-1]; C = V(float(t[1]), float(t[2]), 0); gf, top, pieces, dyaw = float(t[3]), float(t[4]), int(t[5]), float(t[6])
    def at(ang, r): a = math.radians(ang); return V(C.x + r * math.cos(a), C.y + r * math.sin(a), 0)
    door = at(dyaw, 300.0); sa = dyaw - 22.0
    put(at(dyaw, 650.0), yaw=dyaw + 180.0, z=g.wild_ground_z(at(dyaw, 650.0))); yield from rwait(1.0)
    pts = [at(dyaw, 380.0), at(dyaw, 180.0)] + [at(sa - k * 15, 120) for k in range(0, 6 * pieces + 1)] + [at(sa - pieces * 90 - 45, 135)]
    t0 = time.time(); i = 0; zmax = -1e9; last = time.time(); li = 0
    while i < len(pts) and time.time() - t0 < 90:
        q = G["pawn"].get_actor_location(); zmax = max(zmax, q.z)
        while i < len(pts) and math.hypot(pts[i].x - q.x, pts[i].y - q.y) < 45.0: i += 1
        if i >= len(pts): break
        if i != li: li, last = i, time.time()
        if time.time() - last > 8.0: break
        dv = V(pts[i].x - q.x, pts[i].y - q.y, 0); n_ = math.hypot(dv.x, dv.y) or 1.0
        G["pawn"].add_movement_input(V(dv.x / n_, dv.y / n_, 0), 1.0, False); yield
    hh = G["pawn"].get_component_by_class(unreal.CapsuleComponent).get_scaled_capsule_half_height()
    yield from rwait(1.0)
    q = G["pawn"].get_actor_location()
    res["climb"] = {"reached": i, "of": len(pts), "feet_z_max_over_floor": round(zmax - hh - gf, 1), "top_over_floor": round(top - gf, 1)}
    res["feet_after_over_top"] = round(q.z - hh - top, 1)
    # (PR #43's review: the third storey's two quarters left standing hold her: she walks at the middle of their wall from the top's
    # floor for 3 s and stays inside the ring, on the floor)
    kept = float(t[8]) if len(t) > 8 else None
    if kept is not None and kept > -1e5:
        wall = at(kept + 90.0, 420.0); t1 = time.time()
        while time.time() - t1 < 3.0:
            q = G["pawn"].get_actor_location(); dv = V(wall.x - q.x, wall.y - q.y, 0); n_ = math.hypot(dv.x, dv.y) or 1.0
            G["pawn"].add_movement_input(V(dv.x / n_, dv.y / n_, 0), 1.0, False); yield
        q = G["pawn"].get_actor_location()
        res["pushed_at_wall"] = {"from_middle_cm": round(math.hypot(q.x - C.x, q.y - C.y)), "feet_over_top": round(q.z - hh - top, 1)}
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-25, yaw=dyaw)); yield from rwait(0.8)
    shot("tower10_top", "1280x720"); yield from rwait(1.5)
    put(at(dyaw, 900.0), yaw=dyaw + 180.0, z=g.wild_ground_z(at(dyaw, 900.0))); yield from rwait(1.2); shot("tower10_door", "1280x720"); yield from rwait(1.5)
    g.wild_drop_all(); g.wild_put_her(0.0, 0.0); yield from wait_chunks(30, 40)
    quiet(False)
    pw = res.get("pushed_at_wall")
    step_result("tower10", res["climb"]["reached"] == res["climb"]["of"] and abs(res["feet_after_over_top"]) < 30 and pieces >= 4
                and pw is not None and pw["from_middle_cm"] < 290 and abs(pw["feet_over_top"]) < 30, **res)

def step_farms10():
    """"the small farm holdings should be noted on the large map": a farmstead she walks past is found (said so) and is on the big map:
    its place under the map's cross names it; a picture of the map"""
    g = G["gen"]; res = {}; quiet(True)
    yield from wait_ready(90)
    fs = [str(x).split("|") for x in g.find_wild_farmsteads(0.0, 0.0, 3500.0)]
    assert fs, "no farmstead"
    f = fs[0]; fid, fx, fy = int(f[0]), float(f[2]), float(f[3]); res["farmstead"] = f[1]
    g.set_map_open(True); yield from rwait(0.4); g.set_wild_map_view(fx, fy, 20.0); yield from rwait(1.2)
    res["hover_before"] = map_state()["hover"]
    g.set_map_open(False); yield from rwait(0.3)
    g.wild_drop_all(); g.wild_put_her(fx - 30.0, fy); yield from wait_chunks(30, 50); yield from rwait(2.5)
    g.set_map_open(True); yield from rwait(0.4); g.set_wild_map_view(fx, fy, 20.0); yield from rwait(1.5)
    ms = map_state(); res["hover_after"] = ms["hover"]; res["hover_name"] = ms["hover_name"]
    shot("farms10_map", "1280x720"); yield from rwait(1.5)
    g.set_map_open(False); yield from rwait(0.3)
    g.wild_drop_all(); g.wild_put_her(0.0, 0.0); yield from wait_chunks(30, 40)
    quiet(False)
    step_result("farms10", res["hover_before"] != fid and res["hover_after"] == fid and f[1] in res["hover_name"], **res)

def last_found(): return [str(x) for x in G["gen"].get_editor_property("last_found_list")]
def box_lines():
    """the wild containers ("box"), the designed farms ("farm11") and their buildings ("fbld") (GetWildBoxLines)"""
    boxes, farms, blds = [], {}, []
    for l in G["gen"].get_wild_box_lines():
        p = str(l).split("|")
        if p[0] == "box": boxes.append({"kind": p[1], "x": float(p[2]), "y": float(p[3]), "z": float(p[4]), "alpha": float(p[5]), "looted": p[6] == "1", "key": int(p[7])})
        elif p[0] == "farm11": farms[int(p[1])] = {"design": int(p[2]), "buildings": int(p[3]), "boxes": int(p[4])}
        elif p[0] == "fbld": blds.append({"farm": int(p[1]), "kind": p[2], "x": float(p[3]), "y": float(p[4]), "floor": float(p[5]), "nx": int(p[6]), "ny": int(p[7]),
                                          "yaw": float(p[8]), "dx": float(p[9]), "dy": float(p[10]), "furniture": int(p[11]), "boxes": int(p[12])})
    return boxes, farms, blds
def step_farms11():
    """the list of 2026-11-11's fourth phase (919 farms, RD/RDWildFarm11.cpp): the farmsteads near Brokenspire each built from a design
    of their own (their designs told apart); at the first: every building has its door (F opens it, she walks in by her own movement
    and stands on its floor inside its walls, a picture inside the house and the barn), its furniture and containers; a chest
    opened by F gives her food (her things counted, the container open and kept looted: F passes it by after), a garden harvested
    gives its crops; the farm's animals stay in their pens; then every one of the designs built in turn at a spot near her and
    measured (its buildings with a door, furniture and containers; its gardens and animals) and taken away again"""
    g = G["gen"]; res = {"visits": []}; quiet(True)
    yield from wait_ready(90)
    nd = len(g.get_editor_property("farm_designs")); res["designs"] = nd
    fs = [str(x).split("|") for x in g.find_wild_farmsteads(0.0, 0.0, 6000.0)]
    res["farmsteads"] = len(fs)
    seen = {}
    for k, f in enumerate(fs[:3]):
        fid, fx, fy = int(f[0]), float(f[2]), float(f[3])
        g.wild_drop_all(); g.wild_put_her(fx - 30.0, fy); yield from wait_chunks(30, 50); yield from rwait(3.0)
        boxes, farms, blds = box_lines()
        fm = farms.get(fid); mine = [b for b in blds if b["farm"] == fid]
        v = {"name": f[1], "design": fm["design"] if fm else None, "buildings": len(mine), "kinds": sorted(b["kind"] for b in mine),
             "boxes": fm["boxes"] if fm else 0, "furniture_min": min((b["furniture"] for b in mine), default=0)}
        seen[fid] = v["design"]
        if k == 0 and mine:
            # ---- every building: F at its door, in by her own movement, on its floor
            v["walks"] = []
            hs, ds = wild_houses()
            for b in mine:
                a = math.radians(b["yaw"]); out = V(math.cos(a), math.sin(a), 0)
                hx = b["nx"] * 150.0; hy = b["ny"] * 150.0
                h = {"x": b["x"], "y": b["y"], "hx": hx - 30.0, "hy": hy - 30.0, "yaw": b["yaw"]}
                st = V(b["dx"] + out.x * 330, b["dy"] + out.y * 330, 0)
                put(st, yaw=math.degrees(math.atan2(-out.y, -out.x)), z=g.wild_ground_z(st)); yield from rwait(0.8)
                w = {"kind": b["kind"], "furniture": b["furniture"], "boxes": b["boxes"]}
                w["to_door"] = yield from walk_to(V(b["dx"] + out.x * 115, b["dy"] + out.y * 115, 0), 6.0, 40.0)
                yield from rwait(0.3)
                w["prompt"] = str(g.describe_nearest(G["pawn"].get_actor_location()))
                w["f"] = str(g.interact_nearest(G["pawn"].get_actor_location())); yield from rwait(1.6)
                _h, ds2 = wild_houses(); dn = min(ds2, key=lambda e: math.hypot(e["x"] - b["dx"], e["y"] - b["dy"])); w["door_open"] = round(dn["alpha"], 2)
                r1 = yield from walk_to(V(b["dx"] - out.x * 160, b["dy"] - out.y * 160, 0), 6.0)
                r2 = yield from walk_to(V(b["x"], b["y"], 0), 6.0, 90.0)
                yield from rwait(0.5)
                q = G["pawn"].get_actor_location(); hh = G["pawn"].get_component_by_class(unreal.CapsuleComponent).get_scaled_capsule_half_height()
                w["walked_in"] = [r1, r2]; w["inside"] = in_house(h, q); w["feet_over_floor_cm"] = round(q.z - hh - b["floor"], 1)
                if b["kind"] in ("house", "barn") and not any(x["kind"] == b["kind"] and "shot" in x for x in v["walks"]):
                    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-15, yaw=math.degrees(math.atan2(-out.y, -out.x)))); yield from rwait(1.2)
                    w["shot"] = f"farms11_{b['kind']}"; shot(w["shot"], "1280x720"); yield from rwait(1.5)
                v["walks"].append(w)
            # ---- a chest (or another store of the house) opened: her food; then F passes it by
            boxes, _f, _b = box_lines()
            hb = next((b for b in mine if b["kind"] == "house"), mine[0])
            inb = [x for x in boxes if not x["looted"] and in_house({"x": hb["x"], "y": hb["y"], "hx": hb["nx"] * 150.0, "hy": hb["ny"] * 150.0, "yaw": hb["yaw"]}, V(x["x"], x["y"], 0))]
            ch = next((x for x in inb if x["kind"] == "chest"), inb[0] if inb else None)
            if ch:
                c = cb(); n0 = g.get_editor_property("wild_box_things")
                to = V(hb["x"] - ch["x"], hb["y"] - ch["y"], 0); n_ = math.hypot(to.x, to.y) or 1.0
                at = V(ch["x"] + to.x / n_ * 110, ch["y"] + to.y / n_ * 110, 0)
                put(at, yaw=math.degrees(math.atan2(-to.y, -to.x)), z=hb["floor"]); yield from rwait(0.8)
                lines0 = {str(l) for l in c.get_all_inventory_lines()}
                v["box_prompt"] = str(g.describe_nearest(G["pawn"].get_actor_location()))
                v["box_f"] = str(g.interact_nearest(G["pawn"].get_actor_location())); yield from rwait(1.5)
                boxes2, _f, _b = box_lines(); b2 = min(boxes2, key=lambda x: math.hypot(x["x"] - ch["x"], x["y"] - ch["y"]))
                v["box"] = {"kind": ch["kind"], "things": g.get_editor_property("wild_box_things") - n0, "alpha": round(b2["alpha"], 2), "looted": b2["looted"],
                            "new_lines": sorted({str(l) for l in c.get_all_inventory_lines()} - lines0)[:6], "found": last_found()}
                v["box_prompt_after"] = str(g.describe_nearest(G["pawn"].get_actor_location()))
                shot("farms11_chest", "1280x720"); yield from rwait(1.5)
            # ---- a garden harvested
            gd = next((x for x in boxes if x["kind"] == "garden" and not x["looted"]), None)
            if gd:
                n0 = g.get_editor_property("wild_box_things")
                put(V(gd["x"], gd["y"], 0), z=g.wild_ground_z(V(gd["x"], gd["y"], 0))); yield from rwait(0.8)
                v["garden_prompt"] = str(g.describe_nearest(G["pawn"].get_actor_location()))
                v["garden_f"] = str(g.interact_nearest(G["pawn"].get_actor_location())); yield from rwait(1.0)
                v["garden"] = {"things": g.get_editor_property("wild_box_things") - n0, "found": last_found()}
                G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-25, yaw=0)); yield from rwait(0.8); shot("farms11_garden", "1280x720"); yield from rwait(1.5)
            # ---- the animals in their pens after a while
            yield from rwait(6.0)
            al = [str(l).split("|") for l in g.get_wild_farm_lines() if str(l).startswith(f"animal|{fid}|")]
            v["animals"] = len(al); v["animals_in_pens"] = sum(1 for a in al if a[6] == "1")
            # ---- the yard from above it
            put(V(fx * 100.0 - 4200.0, fy * 100.0, 0), yaw=0.0, z=g.wild_ground_z(V(fx * 100.0 - 4200.0, fy * 100.0, 0)))
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-10, yaw=0)); yield from rwait(1.0); shot("farms11_yard", "1280x720"); yield from rwait(1.5)
        res["visits"].append(v)
    # ---- every design, built in turn near the first farm and taken away again
    res["built"] = {}
    if fs:
        fx, fy = float(fs[0][2]), float(fs[0][3])
        sx, sy = fx + 90.0, fy
        g.wild_drop_all(); g.wild_put_her(sx - 45.0, sy); yield from wait_chunks(30, 50); yield from rwait(2.0)
        for d in range(nd):
            fid = g.spawn_farm_design_at(d, sx, sy, 0.0)
            yield from rwait(0.15)
            boxes, farms, blds = box_lines()
            fm = farms.get(fid, {}); mine = [b for b in blds if b["farm"] == fid]
            hs, _ds = wild_houses()
            al = [str(l).split("|") for l in g.get_wild_farm_lines() if str(l).startswith(f"animal|{fid}|")]
            kinds = sorted(b["kind"] for b in mine)
            gardens = sum(1 for x in boxes if x["kind"] == "garden" and math.hypot(x["x"] / 100.0 - sx, x["y"] / 100.0 - sy) < 40.0)
            res["built"][d] = {"id": fid, "kinds": kinds, "boxes": fm.get("boxes", 0), "furniture_min": min((b["furniture"] for b in mine), default=0),
                               "animals": len(al), "gardens": gardens}
            if d in (0, nd // 2, nd - 1):
                put(V(sx * 100.0 - 4200.0, sy * 100.0, 0), yaw=0.0, z=g.wild_ground_z(V(sx * 100.0 - 4200.0, sy * 100.0, 0)))
                G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-10, yaw=0)); yield from rwait(1.0); shot(f"farms11_design{d}", "1280x720"); yield from rwait(1.5)
            res["built"][d]["removed"] = g.remove_wild_farm(fid)
            yield
    g.wild_drop_all(); g.wild_put_her(0.0, 0.0); yield from wait_chunks(30, 40)
    quiet(False)
    vs = [v for v in res["visits"] if v.get("design") is not None]
    v0 = res["visits"][0] if res["visits"] else {}
    walks = v0.get("walks", [])
    built = res["built"]
    res["designs_seen"] = sorted(set(seen.values()))
    ok = (nd >= 50 and len(vs) >= 3 and len(set(v["design"] for v in vs)) == len(vs)
          and all("house" in v["kinds"] and "barn" in v["kinds"] and v["furniture_min"] >= 5 and v["boxes"] >= 6 for v in vs)
          and walks and all("open the door" in w["prompt"] and w["door_open"] > 0.95 and w["inside"] and abs(w["feet_over_floor_cm"]) < 15 for w in walks)
          and v0.get("box", {}).get("things", 0) >= 1 and v0["box"]["looted"] and v0["box"]["alpha"] > 0.95 and "open the" in v0.get("box_prompt", "") and "open the " + v0["box"]["kind"] not in v0.get("box_prompt_after", "")
          and v0.get("garden", {}).get("things", 0) >= 1 and "harvest the garden" in v0.get("garden_prompt", "")
          and v0.get("animals", 0) >= 2 and v0["animals_in_pens"] == v0["animals"]
          and len(built) == nd and all(b["id"] and "house" in b["kinds"] and "barn" in b["kinds"] and b["furniture_min"] >= 5 and b["boxes"] >= 6 and b["gardens"] >= 1 and b["animals"] >= 1 and b["removed"] for b in built.values()))
    step_result("farms11", ok, **res)

def w11_lines():
    out = {"folk": [], "herd": 0}
    for l in G["gen"].get_wild11_lines():
        p = str(l).split("|")
        if p[0] == "leaves": out["leaves"] = {"on": p[1] == "1", "biome": p[2], "fx": p[3] == "1", "x": float(p[4]), "y": float(p[5]), "z": float(p[6])}
        elif p[0] == "folk": out["folk"].append({"title": p[1], "x": float(p[2]), "y": float(p[3]), "given": p[4] == "1"})
        elif p[0] == "herd": out["herd"] = int(p[1])
    return out
def instances_near(at, r, pred):
    """the chunks' instances within r cm of a point whose mesh's name passes pred: [(mesh name, x, y, material name)]"""
    out = []; box = unreal.Box(min=V(at.x - r, at.y - r, at.z - 5000), max=V(at.x + r, at.y + r, at.z + 5000))
    for c in GS.get_all_actors_of_class(G["w"], unreal.RDWildChunk):
        for hm in c.get_components_by_class(unreal.InstancedStaticMeshComponent):
            sm = hm.static_mesh
            if not sm or not pred(sm.get_name()): continue
            mat = hm.get_material(0); mn = mat.get_name() if mat else ""
            for i in hm.get_instances_overlapping_box(box, True) or []:
                t = hm.get_instance_transform(i, True); t = t[1] if isinstance(t, tuple) else t
                if t and math.hypot(t.translation.x - at.x, t.translation.y - at.y) <= r: out.append((sm.get_name(), t.translation.x, t.translation.y, mn))
    return out
def step_meadows11():
    """the list of 2026-11-11's fifth phase, the meadows (920 meadows, leaves; FRDWildWorld::Grove): in a meadow far from the towns,
    the beeches within 250 m in clusters and strips with clearings between (counted on a 20 m grid: most cells bare, the counts far
    more bunched than at random, some cells dense, a bare 80 m square), the debris there (stumps, logs, branches, leaf piles), the
    grass on its swaying material, the leaves blown before the camera; each leaves candidate pictured before her (the choice's
    screening), and pictures of the meadow"""
    g = G["gen"]; res = {}; quiet(True)
    yield from wait_ready(90)
    sp = clear_spot("meadows")
    assert sp, "no meadow"
    res["spot"] = [round(sp[0]), round(sp[1])]
    g.wild_drop_all(); g.wild_put_her(sp[0], sp[1]); yield from wait_chunks(40, 60); yield from rwait(4.0)
    L = G["pawn"].get_actor_location()
    trees = instances_near(L, 25000, lambda n: "EuropeanBeech_M" in n)
    res["trees_250m"] = len(trees)
    # (a 20 m grid over the 500 m square round her: how bunched the trees are)
    cells = {}
    for _, x, y, _m in trees: cells[(int((x - L.x) // 2000), int((y - L.y) // 2000))] = cells.get((int((x - L.x) // 2000), int((y - L.y) // 2000)), 0) + 1
    n_cells = 25 * 25; counts = [cells.get((i, j), 0) for i in range(-12, 13) for j in range(-12, 13)]
    mean = sum(counts) / n_cells; var = sum((c - mean) ** 2 for c in counts) / n_cells
    res["bare_share"] = round(sum(1 for c in counts if c == 0) / n_cells, 3); res["dispersion"] = round(var / mean, 2) if mean > 0 else None; res["max_cell"] = max(counts)
    # (a bare 80 m square: four by four cells of none)
    res["bare_80m_square"] = any(all(cells.get((i + a, j + b), 0) == 0 for a in range(4) for b in range(4)) for i in range(-12, 10) for j in range(-12, 10))
    deb = instances_near(L, 10000, lambda n: any(k in n for k in ("Stump", "Log", "WoodLog", "Branch", "Leaf_Pile")))
    kinds = {}
    for n, *_ in deb: k = "stump" if "Stump" in n else "log" if "Log" in n else "leaves" if "Leaf" in n else "branch"; kinds[k] = kinds.get(k, 0) + 1
    res["debris_100m"] = kinds
    grass = instances_near(L, 1500, lambda n: n == "SM_Grass_2")
    res["grass_near"] = len(grass); res["grass_materials"] = sorted({m for *_x, m in grass})
    res["wind"] = str(g.get_editor_property("wind_collection").get_name()) if g.get_editor_property("wind_collection") else None
    yield from rwait(1.0)
    res["leaves"] = w11_lines().get("leaves")
    # (pictures: the meadow round her each way)
    for k, yaw in enumerate((0, 120, 240)):
        put(V(L.x, L.y, 0), yaw=yaw, z=g.wild_ground_z(V(L.x, L.y, 0))); yield from rwait(1.2); shot(f"meadows11_{k}", "1280x720"); yield from rwait(1.4)
    # (the leaves candidates, each before her for a picture, then gone)
    res["screen"] = []
    MJ = json.load(open(os.path.join(SA, "wilderness", "meadows11.json"), encoding="utf-8"))
    # (each alone as the game's own leaves: the one blowing taken away first (the first screening's red blew in every picture))
    for k, path in enumerate(MJ["leaves"]["candidates"]):
        g.set_wild_leaves_fx(unreal.load_asset(path)); yield from rwait(4.0)
        shot(f"leaves11_{k}", "1280x720"); yield from rwait(1.4)
        res["screen"].append({"fx": path.split("/")[-3] + "/" + path.rsplit("/", 1)[-1], "shot": f"leaves11_{k}", "on": w11_lines().get("leaves", {}).get("on")})
    g.set_wild_leaves_fx(unreal.load_asset(MJ["leaves"]["fx"])); yield from rwait(1.0)
    g.wild_drop_all(); g.wild_put_her(0.0, 0.0); yield from wait_chunks(30, 40)
    quiet(False)
    lv = res["leaves"] or {}
    ok = (res["trees_250m"] >= 40 and res["bare_share"] > 0.6 and (res["dispersion"] or 0) > 2.0 and res["max_cell"] >= 4 and res["bare_80m_square"]
          and all(kinds.get(k, 0) > 0 for k in ("stump", "log", "branch", "leaves"))
          and res["grass_near"] > 50 and res["grass_materials"] and all(m.endswith("_Wind") for m in res["grass_materials"])
          and lv.get("on") and lv.get("biome") == "meadows")
    step_result("meadows11", ok, **res)

def step_events11():
    """the list of 2026-11-11's fifth phase, the director's new kinds (920 events, RD/RDWild11.cpp): each forced ahead of her in turn:
    a point of interest laid (its kind of her region, said in the engagements), a herd (the wild animals made), a person on the way
    (she walks to them, speaks: they give her their gift, and do not give twice); pictures of a few"""
    g = G["gen"]; res = {"kinds": {}}; quiet(True)
    yield from wait_ready(90)
    sp = clear_spot("meadows")
    g.wild_drop_all(); g.wild_put_her(sp[0], sp[1]); yield from wait_chunks(40, 60); yield from rwait(3.0)
    EJ = json.load(open(os.path.join(SA, "wilderness", "events11.json"), encoding="utf-8"))
    def lines(): return [str(l) for l in g.get_wild_encounter_lines()]
    for k, e in enumerate(EJ["kinds"]):
        name = e["name"]
        # (her own spot again, facing a new way each time: the encounter comes 45-70 m ahead)
        put(V(sp[0] * 100.0, sp[1] * 100.0, 0), yaw=k * 27.0 % 360, z=g.wild_ground_z(V(sp[0] * 100.0, sp[1] * 100.0, 0))); yield from rwait(0.6)
        # (the lines from now on, by their time: the list keeps its last 400)
        t0 = now(); w0 = w11_lines(); folk0 = len(w0["folk"])
        g.force_wild_encounter(name); yield from rwait(2.5)
        new = [l for l in lines() if l.split("|")[0].replace(".", "", 1).isdigit() and float(l.split("|")[0]) >= t0 - 0.05]
        r = {"met": any(f"|met|{name}|" in l for l in new), "placed": [l.split("|")[2] for l in new if "|placed|" in l]}
        w1 = w11_lines(); r["herd"] = w1["herd"] - w0["herd"]; r["folk_new"] = len(w1["folk"]) - folk0
        if e.get("folk") and r["folk_new"] > 0:
            fk = w1["folk"][-1]
            c = cb(); lines0 = {str(x) for x in c.get_all_inventory_lines()}; gold0 = g.get_gold()
            to = V(fk["x"] - sp[0] * 100.0, fk["y"] - sp[1] * 100.0, 0); n_ = math.hypot(to.x, to.y) or 1.0
            st = V(fk["x"] - to.x / n_ * 150, fk["y"] - to.y / n_ * 150, 0)
            put(st, yaw=math.degrees(math.atan2(to.y, to.x)), z=g.wild_ground_z(st)); yield from rwait(0.8)
            # (a pile in reach takes F first, as the game's rule says (an earlier kind's things laid here: the refugee's first F took
            # one): taken up before the person is spoken to)
            r["piles_taken"] = 0
            while r["piles_taken"] < 4 and str(g.describe_nearest(G["pawn"].get_actor_location())).startswith("take up"):
                g.interact_nearest(G["pawn"].get_actor_location()); r["piles_taken"] += 1; yield from rwait(0.5)
            lines0 = {str(x) for x in c.get_all_inventory_lines()}; gold0 = g.get_gold()
            r["prompt"] = str(g.describe_nearest(G["pawn"].get_actor_location()))
            r["f"] = str(g.interact_nearest(G["pawn"].get_actor_location())); yield from rwait(0.6)
            r["new_things"] = sorted({str(x) for x in c.get_all_inventory_lines()} - lines0)[:5]; r["gold"] = g.get_gold() - gold0
            r["f_again"] = str(g.interact_nearest(G["pawn"].get_actor_location())); yield from rwait(0.4)
            r["given"] = any(f["given"] for f in w11_lines()["folk"] if f["title"] == fk["title"])
            if "shot" not in res: shot("events11_folk", "1280x720"); res["shot"] = True; yield from rwait(1.4)
        if e.get("animals") and r["herd"] > 0 and "herd_shot" not in res: yield from rwait(0.5); shot("events11_herd", "1280x720"); res["herd_shot"] = True; yield from rwait(1.4)
        res["kinds"][name] = r
        yield from rwait(0.5)
    g.wild_drop_all(); g.wild_put_her(0.0, 0.0); yield from wait_chunks(30, 40)
    quiet(False)
    ks = res["kinds"]
    def good(e):
        r = ks.get(e["name"], {})
        if not r.get("met"): return False
        if e.get("place"): return len(r["placed"]) == 1 and r["placed"][0] in e["place"].split(",")
        if e.get("animals"): return r["herd"] >= 1
        if e.get("folk"): return r["folk_new"] == 1 and r.get("f") == "gift" and (len(r.get("new_things", [])) > 0 or r.get("gold", 0) > 0) and r.get("given") and r.get("f_again") != "gift"
        return True
    res["good"] = {e["name"]: good(e) for e in EJ["kinds"]}
    step_result("events11", all(res["good"].values()), **res)

def step_travellers10():
    """the wilds' liveliness: travellers on a road near her (by day walking along it, 2 or 3 together), she talks to one (a line);
    at night they camp beside the road round a fire and sit; in the morning they walk on; pictures"""
    g = G["gen"]; res = {}; quiet(True)
    yield from wait_ready(90)
    h0 = g.get_town_hour(); g.set_town_hour(10.0)
    # (beside a road: the captain's den lies beside the road north (its place is the world's; a ring of samples 100 m apart missed
    # every road, a few metres wide))
    den = wq().get("wild:wolves")
    rd = (den["x"], den["y"]) if den else (900.0, 0.0)
    res["road_at"] = rd
    g.wild_drop_all(); g.wild_put_her(rd[0], rd[1]); yield from wait_chunks(30, 50); yield from rwait(1.0)
    res["forced"] = g.force_wild_travellers(); yield from rwait(1.5)
    def grp():
        out = []
        for l in g.get_wild_traveller_lines():
            p = str(l).split("|")
            if p[0] == "group": out.append({"x": float(p[2]), "y": float(p[3]), "z": float(p[4]), "folk": int(p[5]), "camped": p[6] == "1", "walking": int(p[7]), "to": p[9], "bits": int(p[13])})
        return out
    G0 = grp(); res["groups"] = len(G0)
    if not G0: g.set_town_hour(h0); quiet(False); step_result("travellers10", False, **res); return
    g0 = G0[0]; p0 = V(g0["x"], g0["y"], 0); yield from rwait(6.0)
    g1 = grp()[0]; res["walked_m"] = round(math.hypot(g1["x"] - p0.x, g1["y"] - p0.y) / 100.0, 1); res["walking"] = g1["walking"]; res["to"] = g1["to"]
    # (to them: a word)
    lead = V(g1["x"], g1["y"], g1["z"])
    G["pawn"].set_actor_location(V(lead.x + 150, lead.y, lead.z + 20), False, True); yield from rwait(0.3)
    res["prompt"] = str(g.describe_nearest(G["pawn"].get_actor_location()))
    res["f"] = str(g.interact_nearest(G["pawn"].get_actor_location())); res["said"] = str(g.get_editor_property("last_bark"))
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-12, yaw=180.0)); yield from rwait(0.8); shot("travellers10_road", "1280x720"); yield from rwait(1.5)
    # (night: camped)
    g.set_town_hour(22.5); yield from rwait(14.0)
    g2 = grp(); res["night"] = g2[0] if g2 else None
    if g2:
        c = g2[0]; cp = None
        for l in g.get_wild_traveller_lines():
            p = str(l).split("|")
            if p[0] == "group": cp = V(float(p[10]), float(p[11]), float(p[12])); break
        res["sitting"] = [str(l).split("|")[6] for l in g.get_wild_traveller_lines() if str(l).startswith("folk|")]
        if cp:
            G["pawn"].set_actor_location(V(cp.x + 650, cp.y, cp.z + 100), False, True); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-20, yaw=180.0)); yield from rwait(1.5)
            shot("travellers10_camp", "1280x720"); yield from rwait(1.5)
    g.set_town_hour(8.0); yield from rwait(6.0)
    g3 = grp(); res["morning"] = g3[0] if g3 else None
    g.set_town_hour(h0); quiet(False)
    ok = res["forced"] and 2 <= g0["folk"] <= 3 and res["walked_m"] > 3 and res["walking"] >= 1 and "talk to" in res["prompt"] and res["f"] == "bark" and len(res["said"].split("|", 1)[-1]) > 5 \
        and res["night"] and res["night"]["camped"] and res["night"]["bits"] >= 2 and any("Sit" in x for x in res.get("sitting", [])) and res["morning"] and not res["morning"]["camped"]
    step_result("travellers10", ok, **res)

def step_cities25():
    """the list of 2026-11-10's seventh phase ("test the re-balanced changes in each city and dungeon"): in each of the six cities, the
    town loaded round her (checked, not only waited for), the game's tier set to 1, 5, 7, 8, 10 and 25 (the dungeons' tiers opened, as
    saved: the castle's, Vel Morrath's, Heaven's; put back in a finally):
      - the store sells nothing of a tier past the game's (by each item's own tiers), and the Mage the scrolls of the game's last two
        tiers (by each scroll's own tiers: 910 lays them again in every band);
      - a stronger healing or mana potion is never cheaper than a weaker one, at every tier;
      - past tier 5 what is used up (potions, food, scrolls, repair, torches) grows as the gold a kill pays (tier 5's x the price
        table over 8: x 2.19 at 10, x 23.1 at 25), within a gold; the horse and the temple's blessing by the price table (x 17.5, x 185);
      - in Brokenspire a potion bought at tier 7 (the gold taken as shown) and sold once tier 8 opens pays back less than it cost;
      - the healer's price for half her hit points (her maxima as the tier makes them, her mana full) grows past tier 5 as the
        kills' gold (her hit points grow too: a point is priced down by her growth)"""
    g = G["gen"]; res = {"cities": {}}; quiet(True)
    yield from wait_ready(90)
    gi = G["gi"] if G.get("gi") else GS.get_game_instance(G["w"])
    chain = [str(l).split("|")[0] for l in g.get_editor_property("dungeon_chain")]
    res["chain"] = chain
    USED = ("HEALING", "MANA", "SPEED", "FOOD", "SCROLL", "REPAIR", "TORCH")
    IT = {}
    for it in g.get_editor_property("items"):
        k = str(it.kind).split(".")[-1].split(":")[0]; ts = list(it.tiers)
        IT[str(it.name)] = (k, ts, float(it.amount))
    def kind(n): return IT.get(n, ("", [], 0.0))[0]
    def low(n): ts = IT.get(n, ("", [], 0.0))[1]; return min(ts) if ts else 1
    # (what the game instance holds, copied as plain lists: the map's values are not kept by reference)
    c0 = list(gi.get_editor_property("castle_tiers"))
    d0 = {str(k): list(v.get_editor_property("tiers")) for k, v in gi.get_editor_property("dungeons").items()}
    def set_tiers(per):
        ds = gi.get_editor_property("dungeons")
        for k in list(ds.keys()):
            if str(k) not in per: per[str(k)] = []
        for k, ts in per.items():
            v = ds[k] if k in ds else unreal.RDDungeonSave()
            v.set_editor_property("tiers", ts); ds[k] = v
        gi.set_editor_property("dungeons", ds)
    def set_tier(t):
        """the game's tier t by what is opened: the castle's 1-5, else the chain's dungeon whose band holds it (Vel Morrath 6-10, Heaven's
        first two 24-25)"""
        if t <= 5: gi.set_editor_property("castle_tiers", list(range(1, t + 1))); set_tiers({})
        else:
            gi.set_editor_property("castle_tiers", [1, 2, 3, 4, 5])
            set_tiers({"vel_morrath": list(range(1, t - 4))} if t <= 10 else {chain[-1]: [1, 2]})
    def table(t): return [1, 2, 3.5, 5.5, 8][t - 1] if t <= 5 else 8.0 * 1.17 ** (min(t, 25) - 5)
    def lines_of(kind_, tab=0):
        if not g.open_town_panel(kind_, -1): return None
        g.set_town_tab(tab)
        L = [str(l).split("|") for l in g.get_town_panel_lines()]
        g.close_town_panel(); return L
    def buys_of(st): return {b[1]: int(b[2].split()[0]) for b in st if b[0] == "buy" and b[2].split()[0].isdigit()}
    TIERS = (1, 5, 7, 8, 10, 25)
    try:
        T = towns()
        for name in ("Brokenspire", "Vel Morrath", "Ashenreach", "Graymourne", "Kethrys Spire", "Heaven"):
            t = T.get(name)
            if not t: res["cities"][name] = {"bad": ["not found"]}; continue
            g.wild_drop_all(); g.wild_put_her(t["x"], t["y"] - 1300.0)
            yield from wait_town(150, lambda s_: s_["name"] == name and s_["section"] == 1 and s_["loading"] == 0)
            ts_ = town_state()
            if not (ts_["name"] == name and ts_["section"] == 1 and ts_["loading"] == 0):
                res["cities"][name] = {"bad": [f"not loaded in 150 s: {ts_}"]}; continue
            r = {"tiers": {}}; bad = []
            for tier in TIERS:
                set_tier(tier); yield from rwait(0.4)
                cb().refresh_maxima(); cb().set_mana(cb().get_max_mana()); cb().set_health(cb().get_max_health() * 0.5); yield from rwait(0.2)
                row = {"game_tier": g.get_game_tier(), "horse": g.horse_price_now()}
                buys = buys_of(lines_of("store") or []); row["prices"] = buys; row["stock"] = len(buys)
                row["past_tier"] = [n for n in buys if low(n) > tier]
                # (a stronger potion of a kind never cheaper: by each potion's own amount)
                for k in ("HEALING", "MANA"):
                    ps = sorted(((IT[n][2], p, n) for n, p in buys.items() if kind(n) == k))
                    row.setdefault("inversions", []).extend(f"{a[2]} {a[1]} > {b[2]} {b[1]}" for a, b in zip(ps, ps[1:]) if b[0] > a[0] and b[1] < a[1])
                te = lines_of("temple") or []
                bl = [b for b in te if b[0] == "bless"]; row["bless"] = int(bl[0][2].split()[0]) if bl and bl[0][2].split()[0].isdigit() else None
                he = lines_of("healer") or []
                hl = [b for b in he if b[0] == "heal"]; row["heal_half"] = int(hl[0][2].split()[0]) if hl and hl[0][2].split()[0].isdigit() else None
                row["max_health"] = round(cb().get_max_health(), 1)
                r["tiers"][str(tier)] = row
                if row["game_tier"] != tier: bad.append(f"game tier {row['game_tier']} for {tier}")
                if row["past_tier"]: bad.append(f"items past tier {tier}: {row['past_tier'][:3]}")
                if row["inversions"]: bad.append(f"a stronger potion cheaper at {tier}: {row['inversions'][:3]}")
            set_tier(1); yield from rwait(0.3); cb().refresh_maxima(); cb().set_health(cb().get_max_health())
            t1, t5 = r["tiers"]["1"], r["tiers"]["5"]
            for tier in (10, 25):
                tr = r["tiers"][str(tier)]; w_ = table(tier)
                if t1["horse"] and abs(tr["horse"] / t1["horse"] - w_) / w_ > 0.03: bad.append(f"horse {t1['horse']}->{tr['horse']} at {tier}")
                if t1["bless"] and tr["bless"] and abs(tr["bless"] / t1["bless"] - w_) / w_ > 0.03: bad.append(f"blessing {t1['bless']}->{tr['bless']} at {tier}")
                # (the used-up things as the kills' gold: tier 5's price x table(tier) / 8, within a gold for the rounding)
                gw = table(tier) / 8.0; off = []
                for n, p5 in t5["prices"].items():
                    if kind(n) in USED and n in tr["prices"] and abs(tr["prices"][n] - p5 * gw) > 1.0 + 0.01 * p5 * gw: off.append(f"{n} {p5}->{tr['prices'][n]} (x {gw:.2f})")
                if off: bad.append(f"not as the kills' gold at {tier}: {off[:3]}")
                r[f"used_up_x{tier}"] = gw
                if t5["heal_half"] and tr["heal_half"] and abs(tr["heal_half"] - t5["heal_half"] * gw) > 1.0 + 0.02 * t5["heal_half"] * gw:
                    bad.append(f"healer {t5['heal_half']}->{tr['heal_half']} at {tier} (x {gw:.2f})")
            if name == "Brokenspire":
                # (a potion bought at tier 7 and sold after tier 8 opens: the gold as the game moves it)
                set_tier(7); yield from rwait(0.3); g.add_gold(100000, "test")
                if g.open_town_panel("store", -1):
                    g.set_town_tab(0)
                    L = [str(l).split("|") for l in g.get_town_panel_lines()]
                    hb = sorted((int(b[2].split()[0]), i, b[1]) for i, b in enumerate(L) if b[0] == "buy" and kind(b[1]) == "HEALING" and b[2].split()[0].isdigit())
                    if hb:
                        price, ix, item = hb[-1]; n0 = cb().get_item_count(item); g0 = g.get_gold()
                        g.activate_town_entry(ix); yield from rwait(0.3)
                        paid = g0 - g.get_gold(); got = cb().get_item_count(item) - n0
                        g.close_town_panel(); set_tier(8); yield from rwait(0.3)
                        sold = None
                        if g.open_town_panel("store", -1):
                            g.set_town_tab(1)
                            L = [str(l).split("|") for l in g.get_town_panel_lines()]
                            si = [i for i, b in enumerate(L) if b[0] == "sell" and b[1].split("  x ")[0] == item]
                            if si:
                                g1 = g.get_gold(); g.activate_town_entry(si[0]); yield from rwait(0.3); sold = g.get_gold() - g1
                            g.close_town_panel()
                        r["trade"] = {"item": item, "shown": price, "paid": paid, "got": got, "sold_at_8": sold}
                        if paid != price or got != 1: bad.append(f"bought {item}: shown {price}, paid {paid}, got {got}")
                        if sold is None or sold >= paid: bad.append(f"bought at 7 for {paid}, sold at 8 for {sold}")
                    else: bad.append("no healing potion to buy at tier 7")
                g.add_gold(-g.get_gold(), "test")
                # (the scrolls, for a hero who reads them: the Mage's, of the game's last two tiers by their own tiers)
                h0 = str(g.get_editor_property("current_hero")); g.switch_hero("Mage"); yield from rwait(1.5); refresh(); g = G["gen"]
                r["mage_scrolls"] = {}
                for tier in (5, 10, 25):
                    set_tier(tier); yield from rwait(0.4)
                    sc = [n for n in buys_of(lines_of("store") or []) if kind(n) == "SCROLL"]
                    r["mage_scrolls"][str(tier)] = sc
                    if not sc: bad.append(f"no scrolls for the Mage at tier {tier}")
                    old = [n for n in sc if not any(tier - 1 <= x <= tier for x in IT[n][1])]
                    if old: bad.append(f"scrolls not of tiers {tier - 1}-{tier} at {tier}: {old[:3]}")
                g.switch_hero(h0); yield from rwait(1.5); refresh(); g = G["gen"]
            for row in r["tiers"].values(): row["prices"] = {n: p for n, p in row["prices"].items() if kind(n) in ("HEALING", "SCROLL")}
            r["bad"] = bad
            res["cities"][name] = r
    finally:
        gi.set_editor_property("castle_tiers", c0)
        ds = gi.get_editor_property("dungeons")
        for k in list(ds.keys()):
            if str(k) not in d0: ds.pop(k)
        gi.set_editor_property("dungeons", ds); set_tiers(dict(d0))
        if cb(): cb().refresh_maxima(); cb().set_health(cb().get_max_health())
        quiet(False)
    g.wild_drop_all(); g.wild_put_her(0.0, 0.0); yield from wait_chunks(30, 40)
    ok = len(res["cities"]) == 6 and all(not v["bad"] for v in res["cities"].values())
    step_result("cities25", ok, **res)

def run_her(dir_xy, sec, rec=None, every=0.1):
    """her run along a way (her move input each frame, her run switch on), a record of her feet against the drawn ground"""
    p = G["pawn"]; cbc = cb(); cbc.set_run_mode(True)
    d = V(dir_xy[0], dir_xy[1], 0.0); t0 = time.time(); tn = 0.0
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-15, yaw=math.degrees(math.atan2(dir_xy[1], dir_xy[0]))))
    while time.time() - t0 < sec:
        p.add_movement_input(d, 1.0)
        if rec is not None and time.time() - t0 >= tn:
            tn += every
            l = p.get_actor_location(); cm = p.get_editor_property("character_movement")
            hh = p.get_editor_property("capsule_component").get_scaled_capsule_half_height()
            s = sample(l.x / 100.0, l.y / 100.0)
            fl = cm.get_editor_property("current_floor"); hr = fl.get_editor_property("hit_result").to_tuple()
            comp = hr[10]; act = hr[9]
            rec.append({"t": round(time.time() - t0, 2), "x": round(l.x), "y": round(l.y), "feet": round(l.z - hh, 1), "ground": round(s["z"], 1),
                        "water": int(s["water"]), "falling": bool(cm.is_falling()), "floor": (comp.get_name() if comp else None), "floor_actor": (act.get_name() if act else None),
                        "floor_dist": round(fl.get_editor_property("floor_dist"), 1), "speed": round(p.get_velocity().length(), 0)})
        yield
def step_rain8():
    """the rain (the list of 2026-11-07: "the rain does not look like raindrops, instead they look like white rods"): the drops
    are streaks standing up, about 26 cm by 1 cm, each two crossed planes (one faces the camera from any way), soft and
    see-through; the field keeps the world's axes; pictures by day and at dusk"""
    g = G["gen"]; res = {}; quiet(True)
    yield from wait_ready(90)
    sp = clear_spot("grasslands") or (9000.0, -4000.0)
    g.wild_put_her(*sp); yield from wait_chunks(35, 50); yield from rwait(1.0)
    g.set_town_hour(11.0); g.set_weather(4, True); yield from rwait(4.0)
    res["sky"] = sky_state()
    for nm, pitch, hour in (("rain8_day", 0.0, 11.0), ("rain8_up", 25.0, 11.0), ("rain8_dusk", 0.0, 19.3)):
        g.set_town_hour(hour); yield from rwait(1.5)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=40.0)); yield from rwait(0.5); shot(nm, "1920x1080"); yield from rwait(2.0)
    # (the drops' own transforms: a streak's height over its width, all facing one way)
    for c in g.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent):
        if c.get_instance_count() > 3000 and c.is_visible():
            ts = [c.get_instance_transform(i, True) for i in range(0, 50)]
            # (each drop two crossed upright planes at one place, one facing the world's X and one its Y; the field not turned
            # with the camera (PR #27's review: turned with it, the rain stood still on the screen as she looked round))
            fw = [t.rotation.get_axis_z() for t in ts]          # (a plane's face: its local Z)
            res["drops"] = {"count": c.get_instance_count(), "scale0": [round(v, 4) for v in (ts[0].scale3d.x, ts[0].scale3d.y, ts[0].scale3d.z)],
                            "up_share": round(sum(1 for t in ts if abs(t.rotation.rotator().pitch) > 80.0) / len(ts), 2),
                            "pairs_crossed": sum(1 for k in range(0, 50, 2) if (ts[k].translation - ts[k + 1].translation).length() < 0.5
                                                 and abs(fw[k].x * fw[k + 1].x + fw[k].y * fw[k + 1].y) < 0.05) / 25.0,
                            "field_yaw": round(c.get_world_rotation().yaw, 1), "camera_yaw": round(G["pc"].get_control_rotation().yaw, 1)}
    g.set_weather(1, True); g.set_town_hour(11.0); quiet(False)
    dr = res.get("drops", {})
    ok = res["sky"]["rain_on"] == 1 and dr.get("up_share", 0) == 1.0 and 0.2 <= dr.get("scale0", [0])[0] <= 0.4 and dr.get("scale0", [0, 1])[1] < 0.02 \
        and dr.get("pairs_crossed", 0) == 1.0 and abs(dr.get("field_yaw", 999)) < 1.0
    step_result("rain8", ok, **res)
def step_sky8():
    """the sky overhead (the list of 2026-11-07: "the sky when looking straight up looks like a giant circle of white that is not
    continuous with the rest of the sky"): pictures straight up and half way up, clear, cloudy and overcast; the zenith's
    picture measured ring by ring out from its middle (a disc's edge is a jump between two rings)"""
    g = G["gen"]; res = {"rings": {}}; quiet(True)
    yield from wait_ready(90)
    sp = clear_spot("grasslands") or (9000.0, -4000.0)
    g.wild_put_her(*sp); yield from wait_chunks(35, 50); yield from rwait(1.0)
    fogs = GS.get_all_actors_of_class(G["w"], unreal.ExponentialHeightFog)
    fc = fogs[0].get_component_by_class(unreal.ExponentialHeightFogComponent) if fogs else None
    res["fog"] = {"cutoff_m": round(fc.get_editor_property("fog_cutoff_distance") / 100.0) if fc else None, "falloff": fc.get_editor_property("fog_height_falloff") if fc else None,
                  "density": fc.get_editor_property("fog_density") if fc else None}
    # (probes: "sky8=nocutoff+falloff30" pictures the fog without its cutoff, or falling off with height (falloff30: 0.030), beside the level's own)
    variants = [("base", None)] + ([(v, v) for v in G.pop("look_only", [])])
    # (the camera looking up is under her: her body and the HUD hidden for these pictures)
    G["pawn"].set_actor_hidden_in_game(True)
    hud = G["pc"].get_hud(); hud.set_editor_property("show_hud", False)
    for wk, wname in ((1, "fair"), (3, "overcast"), (4, "rain")):
        g.set_town_hour(12.0); g.set_weather(wk, True); yield from rwait(3.0)
        for vn, v in variants:
            undo = None
            if v == "nocutoff" and fc: undo = ("fog_cutoff_distance", fc.get_editor_property("fog_cutoff_distance")); fc.set_fog_cutoff_distance(0.0)
            if v and v.startswith("cut") and fc: undo = ("fog_cutoff_distance", fc.get_editor_property("fog_cutoff_distance")); fc.set_fog_cutoff_distance(float(v[3:]) * 100000.0)
            if v and v.startswith("falloff") and fc: undo = ("fog_height_falloff", fc.get_editor_property("fog_height_falloff")); fc.set_fog_height_falloff(float(v[7:] or "20") / 1000.0)
            yield from rwait(0.8)
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=89.0, yaw=10.0)); yield from rwait(0.6)
            nm = f"sky8_{wname}_{vn}_up"; shot(nm, "960x960"); yield from rwait(1.8)
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=35.0, yaw=10.0)); yield from rwait(0.6)
            shot(f"sky8_{wname}_{vn}_mid", "1280x720"); yield from rwait(1.8)
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=2.0, yaw=10.0)); yield from rwait(0.6)
            shot(f"sky8_{wname}_{vn}_low", "1280x720"); yield from rwait(1.8)
            lp = os.path.join(SHOT_DIR, f"wd_{TAG}_sky8_{wname}_{vn}_low.png")
            if os.path.exists(lp): res.setdefault("edges", {})[f"{wname}_{vn}"] = sky_edge(lp)
            pth = os.path.join(SHOT_DIR, f"wd_{TAG}_{nm}.png")
            if os.path.exists(pth):
                rings = []
                for k in range(8):
                    r0, r1 = k / 16.0, (k + 1) / 16.0
                    vals = [png_stats(pth, (0.5 - r1, 0.5 - r1, 0.5 + r1, 0.5 - r0))[0], png_stats(pth, (0.5 - r1, 0.5 + r0, 0.5 + r1, 0.5 + r1))[0]]
                    rings.append(round(sum(vals) / 2.0, 1))
                res["rings"][f"{wname}_{vn}"] = rings
            if undo and fc: fc.set_editor_property(undo[0], undo[1])
    G["pawn"].set_actor_hidden_in_game(False); hud.set_editor_property("show_hud", True)
    g.set_weather(1, True); quiet(False)
    # (a disc's edge: the biggest jump between two neighbouring rings, against the ring's own level)
    jumps = {k: round(max(abs(r[i + 1] - r[i]) for i in range(len(r) - 1)), 1) for k, r in res["rings"].items()}
    res["jumps"] = jumps
    # (the level's own sky, in each weather: no edge across it; 888 w8i measured 52 in the rain with the 6 km cutoff, 7.4 without)
    ed = res.get("edges", {})
    ok = len(jumps) >= 3 and all(v < 12.0 for k, v in jumps.items() if k.endswith("_base")) and len([k for k in ed if k.endswith("_base")]) >= 3 \
        and all(v < 15.0 for k, v in ed.items() if k.endswith("_base")) and res["fog"]["cutoff_m"] >= 100000
    step_result("sky8", ok, **res)
def step_fields8():
    """the farms (the list of 2026-11-07: "the farm terrain should have regular lines of crops, like corn, cabbages, potatoes,
    pumpkins ... not barren or have only grass"; "the different colors of the farm terrain look like abrupt banding"): in the
    farms the chunks round her hold the crops planted in rows (corn, cabbage, potato, pumpkin, sunflower, wheat); along 400 m
    the ground's colour changes by little from one 2 m step to the next (no hard edges); pictures near, from above and far"""
    g = G["gen"]; res = {}; quiet(True)
    yield from wait_ready(90)
    sp = clear_spot("farms")
    if not sp: step_result("fields8", False, error="no farms"); quiet(False); return
    # (a field's middle near there)
    best = None
    for dx in range(-400, 401, 40):
        for dy in range(-400, 401, 40):
            s = sample(sp[0] + dx, sp[1] + dy)
            if s["field"] > 0.95 and s["road"] == 0 and (best is None or abs(dx) + abs(dy) < best[2]): best = (sp[0] + dx, sp[1] + dy, abs(dx) + abs(dy))
    if best: sp = (best[0], best[1])
    res["at"] = [round(sp[0]), round(sp[1])]
    g.set_town_hour(11.0); g.set_weather(1, True)
    g.wild_put_her(*sp); yield from wait_chunks(40, 50); yield from rwait(3.0)
    # (what the chunks round her hold: instances by mesh)
    counts = {}
    for ch in GS.get_all_actors_of_class(G["w"], unreal.RDWildChunk):
        if ch.get_actor_location().distance(G["pawn"].get_actor_location()) > 40000: continue
        for c in ch.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent):
            m = c.get_editor_property("static_mesh")
            if m: counts[m.get_name()] = counts.get(m.get_name(), 0) + c.get_instance_count()
    crops = {k: v for k, v in counts.items() if any(t in k for t in ("Wheat", "Corn", "Cabbage", "Potato", "Pumpkin", "Sunflower"))}
    res["crops"] = crops
    # (the frame rate looking across the fields, against the open grassland's (the crops are tens of thousands of instances))
    def fps_for(sec):
        fs = []; t1 = time.time()
        while time.time() - t1 < sec:
            f = g.get_fps()
            if f > 0: fs.append(f)
            yield
        return round(sum(fs) / max(len(fs), 1), 1)
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=20.0)); yield from rwait(2.0)
    res["fps_fields"] = yield from fps_for(5.0)
    gs = clear_spot("grasslands")
    if gs:
        g.wild_put_her(*gs); yield from wait_chunks(40, 50); yield from rwait(2.0)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=20.0)); yield from rwait(2.0)
        res["fps_grasslands"] = yield from fps_for(5.0)
        g.wild_put_her(*sp); yield from wait_chunks(40, 50); yield from rwait(2.0)
    # (the ground's colour along a line: no step between neighbours as big as a field's change used to be)
    cols = []
    for k in range(200):
        cols.append(str(g.get_wild_sample_at(V((sp[0] + k * 2.0 - 200.0) * 100.0, sp[1] * 100.0, 0))))
    res["fields_on_line"] = sum(1 for k in range(199) if (float(cols[k].split("|")[11]) > 0.5) != (float(cols[k + 1].split("|")[11]) > 0.5))
    for nm, pitch, z in (("fields8_near", -20.0, 0.0), ("fields8_low", -35.0, 600.0), ("fields8_far", -8.0, 2500.0)):
        p = G["pawn"]; l = p.get_actor_location()
        if z > 0: p.set_actor_location(V(l.x, l.y, l.z + z), False, True); p.get_editor_property("character_movement").set_movement_mode(unreal.MovementMode.MOVE_FLYING)
        for yaw in (20.0, 200.0):
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=yaw)); yield from rwait(1.2); shot(f"{nm}_{int(yaw)}", "1920x1080"); yield from rwait(2.0)
        if z > 0: p.get_editor_property("character_movement").set_movement_mode(unreal.MovementMode.MOVE_WALKING); g.wild_put_her(*sp); yield from rwait(2.0)
    quiet(False)
    ok = sum(1 for v in crops.values() if v > 0) >= 1 and sum(crops.values()) > 500
    step_result("fields8", ok, **res)
def step_perf8():
    """the crops' cost (the list of 2026-11-07's fields): the frame rate in the open grassland, then in the farms looking across
    the fields with their crops, then the same view with the crops hidden (one session, the same camera)"""
    g = G["gen"]; res = {}; quiet(True)
    yield from wait_ready(90)
    g.set_town_hour(11.0); g.set_weather(1, True)
    def fps_for(sec):
        fs = []; t1 = time.time()
        while time.time() - t1 < sec:
            f = g.get_fps()
            if f > 0: fs.append(f)
            yield
        return round(sum(fs) / max(len(fs), 1), 1)
    def crop_hisms(on, kinds=("Wheat", "Corn", "Cabbage", "Potato", "Pumpkin", "Sunflower")):
        n = 0
        for ch in GS.get_all_actors_of_class(G["w"], unreal.RDWildChunk):
            for c in ch.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent):
                m = c.get_editor_property("static_mesh")
                if m and any(t in m.get_name() for t in ("Wheat", "Corn", "Cabbage", "Potato", "Pumpkin", "Sunflower")):
                    v = on and any(t in m.get_name() for t in kinds); c.set_visibility(v); n += c.get_instance_count() if v else 0
        return n
    gs = clear_spot("grasslands")
    if gs:
        g.wild_put_her(*gs); yield from wait_chunks(40, 50); yield from rwait(3.0)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=20.0)); yield from rwait(2.0)
        res["fps_grasslands"] = yield from fps_for(6.0)
    fs = clear_spot("farms")
    g.wild_put_her(*fs); yield from wait_chunks(40, 50); yield from rwait(3.0)
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=20.0)); yield from rwait(2.0)
    res["fps_farms_crops"] = yield from fps_for(6.0)
    res["crop_instances"] = crop_hisms(False); yield from rwait(1.0)
    res["fps_farms_no_crops"] = yield from fps_for(6.0)
    for k_ in ("Wheat", "Corn", "Cabbage", "Potato", "Pumpkin", "Sunflower"):
        n_ = crop_hisms(True, (k_,)); yield from rwait(1.0)
        f_ = yield from fps_for(4.0)
        res[f"fps_only_{k_.lower()}"] = [n_, f_]
    crop_hisms(True)
    # (running across them: the frames' times, the farms' chunks made as she comes against the grassland's)
    def run_frames(sec):
        p = G["pawn"]; cb().set_run_mode(True); ts = []; t1 = time.time(); last = t1
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=0.0))
        while time.time() - t1 < sec:
            p.add_movement_input(V(1.0, 0.0, 0.0), 1.0); yield
            n_ = time.time(); ts.append(n_ - last); last = n_
        ts = ts[1:]
        return {"frames": len(ts), "mean_ms": round(1000 * sum(ts) / max(len(ts), 1), 1), "over_50ms": sum(1 for x in ts if x > 0.05), "over_100ms": sum(1 for x in ts if x > 0.1), "max_ms": round(1000 * max(ts or [0]), 0)}
    for nm, spot in (("farms", fs), ("grasslands", gs)):
        if not spot: continue
        g.set_wild_run_speed(5.0)
        g.wild_put_her(*spot); yield from wait_chunks(40, 50); yield from rwait(2.0)
        r_ = yield from run_frames(15.0)
        res[f"run_{nm}_5x"] = r_
        g.set_wild_run_speed(1.0)
    quiet(False)
    step_result("perf8", True, **res)
def step_ground8():
    """her feet on the ground (the list of 2026-11-07: "when stepping off from a higher level of terrain, the character looks like
    she is walking or running on air instead of dropping"; "at many points in the wilderness, the character is not on the
    ground and appears to be running in the air"): she runs 12 s in each of six regions; every 0.1 s her feet against the
    drawn ground under her, what she stands on (the floor's component) and whether she falls; pictures where her feet are
    farthest over the ground"""
    g = G["gen"]; res = {"runs": {}}; quiet(True)
    yield from wait_ready(90)
    g.set_town_hour(11.0); g.set_weather(1, True)
    worst = []
    for name in ("grasslands", "hills", "farms", "temperate autumn forests", "marshes", "mountains"):
        sp = clear_spot(name)
        if not sp: continue
        g.wild_put_her(*sp); yield from wait_chunks(40, 50); yield from rwait(1.5)
        rec = []
        for ang in (0.0, 120.0, 240.0):
            yield from run_her((math.cos(math.radians(ang)), math.sin(math.radians(ang))), 4.0, rec)
        over = [r for r in rec if not r["water"] and r["feet"] - r["ground"] > 20.0]
        floors = {}
        for r in over: floors[str(r["floor"])] = floors.get(str(r["floor"]), 0) + 1
        res["runs"][name] = {"samples": len(rec), "over_20cm": len(over), "max_over": max([r["feet"] - r["ground"] for r in rec if not r["water"]] or [0]),
                             "falling": sum(1 for r in rec if r["falling"]), "floors_over": floors,
                             "worst": sorted(over, key=lambda r: r["ground"] - r["feet"])[:4]}
        for r in sorted(over, key=lambda r: r["ground"] - r["feet"])[:1]: worst.append((name, r))
        yield
    # (a picture at each region's worst place: her put there, the camera from her side)
    for name, r in worst[:4]:
        G["pawn"].set_actor_location(V(r["x"], r["y"], r["feet"] + 100.0), False, True); yield from rwait(1.5)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-10, yaw=90.0)); yield from rwait(0.8); shot(f"ground8_{name.replace(' ', '_')}", "1280x720"); yield from rwait(1.8)
    quiet(False)
    tot = sum(v["samples"] for v in res["runs"].values()); bad = sum(v["over_20cm"] for v in res["runs"].values())
    res["share_over_20cm"] = round(bad / max(tot, 1), 3)
    ok = tot > 300 and res["share_over_20cm"] < 0.02
    step_result("ground8", ok, **res)
def step_animals8():
    """the wild animals hunted (the list of 2026-11-07: "player should be able to kill the animals wandering in the wilderness and
    get appropriate crafting materials from them. animals should respawn after they've been killed at regular intervals"): a
    deer and a wolf put before her: her blows and bolts hurt them (their hit points fall, struck they run), killed each falls
    on its side and its things lie by it (a harvest pile of its kind's materials, taken with F); while the kind's wait lasts
    no other of it comes; the body goes in time"""
    g = G["gen"]; res = {"kills": {}}; quiet(True)
    yield from wait_ready(90)
    sp = clear_spot("grasslands") or (9000.0, -4000.0)
    g.set_town_hour(11.0); g.set_weather(1, True)
    g.wild_put_her(*sp); yield from wait_chunks(40, 50); yield from rwait(1.5)
    def life():
        out = []
        for l in g.get_wild_life_lines():
            p = str(l).split("|")
            if p[0] == "animal": out.append({"kind": p[1], "at": V(float(p[2]), float(p[3]), float(p[4])), "state": int(p[5]), "hp": float(p[8]) if len(p) > 8 else -1, "dead": int(p[9]) if len(p) > 9 else 0})
        return out
    k0 = g.get_editor_property("animals_killed")
    hero0 = str(g.get_editor_property("current_hero"))
    # (the wait made short for the test: 45 s (the level's own is 120))
    wait0 = g.get_editor_property("wild_animal_respawn_seconds"); g.set_editor_property("wild_animal_respawn_seconds", 45.0)
    # (the hero's own weapons: the Summoner's fire bolts at the deer and the wolf, the Warrior's sword at the hare)
    for kind, hero in (("Deer", hero0), ("Wolf", hero0), ("Hare", "Warrior")):
        if str(g.get_editor_property("current_hero")) != hero: g.switch_hero(hero); yield from rwait(1.5); refresh()
        p = G["pawn"]; l = p.get_actor_location(); fw = p.get_actor_forward_vector()
        a = g.spawn_wild_animal_at(kind, V(l.x + fw.x * 120.0, l.y + fw.y * 120.0, l.z))
        if not a: res["kills"][kind] = {"error": "not spawned"}; continue
        hp0 = a.get_health(); blows = 0; t0 = time.time(); hp_after_first = None
        # (her own attack, again and again; the animal put back before her between blows (it runs off when struck))
        def hold_before(sec):
            t1 = time.time()
            while time.time() - t1 < sec and not a.is_dead():
                l = p.get_actor_location(); fw = p.get_actor_forward_vector()
                a.set_actor_location(V(l.x + fw.x * 120.0, l.y + fw.y * 120.0, a.get_actor_location().z), False, True)
                yield
        while not a.is_dead() and time.time() - t0 < 25.0:
            cb().set_mana(cb().get_max_mana())
            yield from hold_before(0.2)
            cb().simulate_key(key("LeftMouseButton"), True); yield from hold_before(0.12); cb().simulate_key(key("LeftMouseButton"), False)
            blows += 1
            yield from hold_before(1.3)
            if hp_after_first is None and a.get_health() < hp0: hp_after_first = a.get_health()
        dead = a.is_dead()
        drops = [str(x) for x in g.get_editor_property("last_animal_drops")] if dead else []
        res.setdefault("alive_at_kill", {})[kind] = sum(1 for x in life() if x["kind"] == kind and not x["dead"])
        yield from rwait(1.0)
        res["kills"][kind] = {"hp0": hp0, "hp_after_first_blow": hp_after_first, "blows": blows, "dead": dead, "drops": drops,
                              "lying_roll": round(abs(a.get_component_by_class(unreal.SkeletalMeshComponent).get_world_rotation().roll), 1) if dead else None}
        if dead:
            # (on its side, measured by the body's axes: its length still along its facing and level, its back's up turned
            # sideways; a roll about the mesh's own X tipped a kind turned -90 onto its nose, with the same roll: PR #27's review)
            bm = a.get_component_by_class(unreal.SkeletalMeshComponent); af = a.get_actor_forward_vector()
            fv, rv, uv = bm.get_forward_vector(), bm.get_right_vector(), bm.get_up_vector()
            ln = fv if abs(fv.x * af.x + fv.y * af.y) >= abs(rv.x * af.x + rv.y * af.y) else rv
            res["kills"][kind]["length_z"] = round(abs(ln.z), 2); res["kills"][kind]["up_z"] = round(abs(uv.z), 2)
        if dead:
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-25, yaw=p.get_actor_rotation().yaw)); yield from rwait(0.8); shot(f"animals8_{kind.lower()}_dead", "1280x720"); yield from rwait(1.8)
        # (her things: the harvest by it, taken with F)
        if dead:
            bl_ = a.get_actor_location(); ml = p.get_actor_location()
            p.set_actor_location(V(bl_.x + (ml.x - bl_.x) * 0.3, bl_.y + (ml.y - bl_.y) * 0.3, ml.z), False, True); yield from rwait(0.5)
        got0 = {d: cb().get_item_count(d) for d in set(drops)}
        try: res["kills"][kind]["f_names"] = str(g.describe_nearest(p.get_actor_location()))
        except Exception as e_: res["kills"][kind]["f_names"] = f"? {e_}"
        yield from press("F", 0.1); yield from rwait(0.8)
        res["kills"][kind]["taken"] = {d: cb().get_item_count(d) - got0[d] for d in got0}
    res["killed"] = g.get_editor_property("animals_killed") - k0
    # (the kinds killed wait: none of them comes again within the wait; each kind's place is held empty and freed on time)
    res["respawn_wait_s"] = g.get_editor_property("wild_animal_respawn_seconds")
    def pending():
        return [(str(l).split("|")[1], float(str(l).split("|")[2])) for l in g.get_wild_life_lines() if str(l).startswith("respawn|")]
    res["pending_after_kills"] = [[k_, round(s_)] for k_, s_ in pending()]
    # (the places freed when the wait is over)
    t_ = time.time(); freed_at = None
    while time.time() - t_ < 70.0 and freed_at is None:
        if not pending(): freed_at = round(time.time() - t_, 1)
        yield from rwait(1.0)
    res["places_freed_after_s"] = freed_at
    # (a deer of the wild's own (the test's are extra to its count): killed, no deer comes while its place waits; after it
    # another comes, as they come round her (60 to 150 m off))
    if str(g.get_editor_property("current_hero")) != hero0: g.switch_hero(hero0); yield from rwait(1.5); refresh()
    p = G["pawn"]; nat = None; t_ = time.time()
    while nat is None and time.time() - t_ < 40.0:
        here = p.get_actor_location()
        ds_ = sorted([x for x in life() if x["kind"] == "Deer" and not x["dead"]], key=lambda x: (x["at"] - here).length())
        if ds_: nat = ds_[0]
        else: yield from rwait(1.0)
    rw = {}
    if nat:
        target = None
        for a_ in GS.get_all_actors_of_class(G["w"], unreal.RDWildAnimal):
            if not a_.is_dead() and (a_.get_actor_location() - nat["at"]).length() < 5.0: target = a_
        if target:
            al = target.get_actor_location()
            p.set_actor_location(V(al.x - 800.0, al.y, al.z + 100.0), False, True); p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=0.0), True)
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-5, yaw=0.0)); yield from rwait(1.0)
            n_ = 0
            # (held before her as the test's own (struck, a deer runs off faster than her bolts' reach): what is measured
            # here is its place, not the chase)
            def hold_t(sec):
                t1 = time.time()
                while time.time() - t1 < sec and not target.is_dead():
                    l = p.get_actor_location(); fw = p.get_actor_forward_vector()
                    target.set_actor_location(V(l.x + fw.x * 300.0, l.y + fw.y * 300.0, target.get_actor_location().z), False, True)
                    yield
            while not target.is_dead() and n_ < 10:
                cb().set_mana(cb().get_max_mana())          # (the kills before spent her mana)
                yield from hold_t(0.2)
                cb().simulate_key(key("LeftMouseButton"), True); yield from hold_t(0.12); cb().simulate_key(key("LeftMouseButton"), False)
                yield from hold_t(1.4); n_ += 1
            rw["killed"] = target.is_dead(); rw["casts"] = n_
            deer = lambda: sum(1 for x in life() if x["kind"] == "Deer" and not x["dead"])
            rw["deer_after_kill"] = deer(); rw["waiting"] = [[k_, round(s_)] for k_, s_ in pending()]
            yield from rwait(20.0); rw["deer_at_20s"] = deer()
            t_ = time.time(); came = None
            while time.time() - t_ < 70.0 and came is None:
                if deer() > rw["deer_after_kill"]: came = round(20.0 + time.time() - t_, 1)
                yield from rwait(1.0)
            rw["another_came_after_s"] = came
    res["wild_deer"] = rw
    g.set_editor_property("wild_animal_respawn_seconds", wait0)
    quiet(False)
    ok = all(v.get("dead") and v.get("drops") and v.get("hp_after_first_blow") is not None and sum(v.get("taken", {}).values()) == len(v["drops"])
             and v.get("length_z", 1) < 0.3 and v.get("up_z", 1) < 0.3 for v in res["kills"].values()) \
        and res["killed"] >= 3 and len(res["pending_after_kills"]) >= 3 and res["places_freed_after_s"] is not None \
        and rw.get("killed") and rw.get("deer_at_20s", 99) <= rw.get("deer_after_kill", -1) and rw.get("another_came_after_s") is not None and rw["another_came_after_s"] >= 40.0
    step_result("animals8", ok, **res)
def step_speed8():
    """her run speed for testing (the list of 2026-11-07: "a console command that allows the character to choose how fast to run
    in the wilderness ... 1x / 5x / 10x / 15x / 20x / 30x / 40x"): rd.WildRunSpeed 10 then 40 typed at the console, her run
    measured over 4 s each, on the ground the whole way (no fall reset); back to 1"""
    g = G["gen"]; res = {}; quiet(True)
    yield from wait_ready(90)
    sp = clear_spot("plains") or clear_spot("grasslands") or (9000.0, -4000.0)
    g.wild_put_her(*sp); yield from wait_chunks(40, 50); yield from rwait(1.5)
    fr0 = g.get_editor_property("fall_resets") if hasattr(g, "fall_resets") else None
    for k in (1, 10, 40):
        unreal.SystemLibrary.execute_console_command(G["w"], f"rd.WildRunSpeed {k}"); yield from rwait(0.6)
        a = G["pawn"].get_actor_location(); rec = []
        yield from run_her((1.0, 0.3), 4.0, rec, every=0.25)
        b = G["pawn"].get_actor_location()
        res[f"x{k}"] = {"applied": g.get_wild_run_applied(), "m_per_s": round(math.hypot(b.x - a.x, b.y - a.y) / 100.0 / 4.0, 1),
                        "max_over_ground": max([r["feet"] - r["ground"] for r in rec] or [0]), "held": g.get_editor_property("wild_run_held")}
        yield from rwait(1.0)
    unreal.SystemLibrary.execute_console_command(G["w"], "rd.WildRunSpeed 1"); yield from rwait(0.5)
    res["after"] = g.get_wild_run_applied()
    quiet(False)
    b1 = res["x1"]["m_per_s"]
    ok = res["x10"]["applied"] == 10 and res["x40"]["applied"] == 40 and res["after"] == 1 and b1 > 2.0 \
        and res["x10"]["m_per_s"] > b1 * 6 and res["x40"]["m_per_s"] > b1 * 20
    step_result("speed8", ok, **res)


STEPS = {"list12": step_list12, "gait12": step_gait12, "ruins12": step_ruins12, "lairs12": step_lairs12, "sites12": step_sites12, "quests12": step_quests12, "farms11": step_farms11, "meadows11": step_meadows11, "events11": step_events11, "list10w": step_list10w, "horse9": step_horse9, "houses10": step_houses10, "cities25": step_cities25, "tower10": step_tower10, "farms10": step_farms10, "travellers10": step_travellers10, "poi7": step_poi7, "secondary9": step_secondary9, "wild25": step_wild25, "world": step_world, "look": step_look, "stream": step_stream, "towns": step_towns, "gate": step_gate, "map": step_map, "places": step_places, "travel": step_travel, "save": step_save, "memprobe": step_memprobe,
         "sky7": step_sky7, "life7": step_life7, "ground7": step_ground7, "music7": step_music7, "build7": step_build7, "quests": step_quests,
         "rain8": step_rain8, "sky8": step_sky8, "fields8": step_fields8, "ground8": step_ground8, "animals8": step_animals8, "speed8": step_speed8, "perf8": step_perf8}
def run():
    o = G.get("gen"); R["windows_hidden"] = str(o.slate_clear_view()) if o else None
    for s in PLAN:
        # (a step's own list: "look=pine forests+glacial")
        name, _, arg = s.partition("=")
        if arg: G["look_only"] = [a_.replace("_", " ") for a_ in arg.split("+")]
        try:
            refresh()
            yield from STEPS[name]()
        except Exception as e:
            import traceback
            step_result(name, False, error=str(e), trace=traceback.format_exc()[-1500:])
            try: quiet(False)
            except Exception: pass
        yield from rwait(0.3)
def finish(err=None):
    unreal.unregister_slate_post_tick_callback(G["h"])
    R["error"] = err
    try:
        if G.get("gen"): quiet(False); R["windows_shown_again"] = G["gen"].slate_restore_view()
    except Exception as e: R["error"] = (err or "") + " / " + str(e)
    os.makedirs(OUT, exist_ok=True); json.dump(R, open(os.path.join(OUT, f"test_{TAG}.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    ok = not R.get("error") and len(R["steps"]) == len(PLAN) and all(s["ok"] for s in R["steps"])
    unreal.log(f"WILDTEST done | {TAG} | {'ok' if ok else 'FAILED'} | " + " | ".join(f"{s['step']} {'ok' if s['ok'] else 'FAILED'}" for s in R["steps"]) + f" | {R.get('error') or ''}")
    G.clear()
def tick(dt):
    try:
        if UES.get_game_world() is None:
            if G.get("travel_until", 0) > time.time(): return
            finish("PIE ended"); return
        if "rec" in G: G["rec"].append((dt, str(G["gen"].get_wild_build_stats(False))))
        next(G["gen_"])
    except StopIteration: finish()
    except Exception as e:
        import traceback
        unreal.log_error("WILDTEST error: " + str(e) + traceback.format_exc()); finish(str(e))
G["gen_"] = run()
G["h"] = unreal.register_slate_post_tick_callback(tick)
print("wilderness test armed:", PLAN, TAG)
