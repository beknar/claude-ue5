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
  poi7    (2026-11-09, 912) the points of interest: the seconds between them along 14 lines of the world's model, a 150 s
          run in play (what met her never 40 s apart), each use made with F
  secondary9 (2026-11-09, 911) a wild place's Hallowed Stone taken and not laid again, the lairs' monsters' Seraph Feathers,
          the Martial Artist's Water Walk over a lake
  wild25  (2026-11-09, 910) lairs and spawn points of six tiers along the roads, Brokenspire to Heaven: each monster of its
          place's tier and of a kind whose wild band holds it, the kinds changing along the way
Writes SourceArt/wilderness/test_<tag>.json and logs "WILDTEST done | <tag> | ok / FAILED | ...". Args: plan tag"""
import unreal, sys, json, math, os, time
__keep__ = True
TAG = sys.argv[2] if len(sys.argv) > 2 else "t"
V = unreal.Vector; GS = unreal.GameplayStatics
TOWN_ID = 1 << 30   # (a town's place id: FRDWildWorld::TownIdBase + its index)
OUT = r"E:\code\claude-ue5\claude_ue5\SourceArt\wilderness"
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


STEPS = {"poi7": step_poi7, "secondary9": step_secondary9, "wild25": step_wild25, "world": step_world, "look": step_look, "stream": step_stream, "towns": step_towns, "gate": step_gate, "map": step_map, "places": step_places, "travel": step_travel, "save": step_save, "memprobe": step_memprobe,
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
