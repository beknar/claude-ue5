"""The wilderness's test (the user's spec of 2026-11-03, docs/wilderness.txt; C++ RD/RDWild*.cpp), in play on brokenspire.
Steps:
  world   the world made (its seed, how long); the towns where the spec puts them: Brokenspire mid-south, Ashenreach in the
          continent's middle north of it, Graymourne on the north coast mid-way across, Vel Morrath east of Brokenspire near
          its coast but not on it (the coast measured by walking out until the sea); every template of the spec in the
          biome regions; rivers, lakes, roads between the towns; pictures of the continent and of 40 km round Brokenspire
  look    each template visited (her put on the nearest of its regions, the chunks round her made): a picture of her view,
          what the world has under her (its biome, height, snow, sand, water), the plants and rocks of the chunks there
Writes SourceArt/wilderness/test_<tag>.json and logs "WILDTEST done | <tag> | ok / FAILED | ...". Args: plan tag"""
import unreal, sys, json, math, os, time
__keep__ = True
TAG = sys.argv[2] if len(sys.argv) > 2 else "t"
V = unreal.Vector; GS = unreal.GameplayStatics
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
    b = T.get("Brokenspire"); a = T.get("Ashenreach"); gm = T.get("Graymourne"); vm = T.get("Vel Morrath")
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
        chk["velmorrath_east"] = vm["y"] - b["y"] > 60000 and abs(vm["x"] - b["x"]) < 25000
        chk["velmorrath_near_coast_not_on_it"] = res["velmorrath_sea_east_m"] is not None and 2000 < res["velmorrath_sea_east_m"] < 20000 and int(s["water"]) == 0
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
    ok = st.get("ready") == 1 and all(chk.values()) and len(chk) == 6 and not res["missing_templates"] and res["rivers"] >= 8 and res["lakes"] >= 5 and len(res["roads"]) >= 4
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
        p = str(l).split("|"); out.append({"x": int(p[0]), "y": int(p[1]), "inst": int(p[2]), "tris": int(p[3]), "near": int(p[4]), "col": int(p[5]), "monsters": int(p[6]), "props": int(p[7]), "near_hism": int(p[8])})
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
    quiet(False)
    ok = (res["at_start"]["section"] == 1 and res["far"]["section"] == 0 and res["folk_far"] == 0 and res["back"]["section"] == 1 and res["folk_back"] > 0
          and res["vm_near"]["name"] == "Vel Morrath" and res["vm_in"]["in_walls"] == 1 and res["minimap_outside"] and not res["minimap_inside_wild"]
          and res["vm_folk"] > 0 and not any(r in res["vm_roles"] for r in ("Elder", "Scholar", "Captain")) and not res["vm_titles_brokenspire"])
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
    g.set_map_open(False); yield from rwait(0.5)
    res["revealed_here"] = g.wild_revealed_at(900.0, -700.0); res["revealed_far"] = g.wild_revealed_at(150000.0, 100000.0)
    quiet(False)
    ok = (res["minimap_drawn"] and res["open"]["tiles"] > 0 and res["revealed_here"] and not res["revealed_far"]
          and res["map_continent"]["level"] <= 2 and res["open"]["level"] >= 8 and any(a in res["map_continent_drawn"] for a in ("wmap_town", "wmap_city")))
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
    quiet(False)
    chase = [v for v in res["visits"] if "monster_m" in v]
    ok = len(want) >= 6 and all(v["found"] for v in res["visits"]) and all(v["props"] > 0 for v in res["visits"]) and (not chase or all(v["monster_m"][1] < v["monster_m"][0] for v in chase))
    step_result("places", ok, **res)
def dist2(a, b): return math.hypot(a.x - b.x, a.y - b.y)


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
    ti = 1000003 if G.get("vm_found") else 1000000
    ok_t = g.wild_fast_travel(ti); yield from rwait(3.0)
    res["town_travel"] = ok_t; res["town_after"] = town_state()
    # refused in a fight: at a lair with its monsters after her
    lairs = [p_ for p_ in places_near(0, 0, 40000) if p_["kind"] == "lair"]
    if lairs:
        l = min(lairs, key=lambda q: math.hypot(q["x"], q["y"]))
        g.wild_put_her(l["x"] - 12.0, l["y"]); yield from wait_chunks(30, 50)
        quiet(False); yield from wait(3.0)
        res["combat"] = g.is_wild_combat()
        res["refused"] = not g.wild_fast_travel(1000000); res["refusal"] = map_state()["refusal"]
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
    g.set_menu_open(False)
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
    ok = (res["saved"] and res["info"] and any("Save the game" in l for l in res["menu"]) and any("Load a game" in l for l in res["menu"]) and res["load"]
          and res["back_m"] < 10 and res["gold_after"] == res["gold_before"] and res["found_after"] >= res["found_before"] and res["revealed_after"] >= res["revealed_before"] * 0.95)
    step_result("save", ok, **res)

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

STEPS = {"world": step_world, "look": step_look, "stream": step_stream, "towns": step_towns, "gate": step_gate, "map": step_map, "places": step_places, "travel": step_travel, "save": step_save, "memprobe": step_memprobe}
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
        next(G["gen_"])
    except StopIteration: finish()
    except Exception as e:
        import traceback
        unreal.log_error("WILDTEST error: " + str(e) + traceback.format_exc()); finish(str(e))
G["gen_"] = run()
G["h"] = unreal.register_slate_post_tick_callback(tick)
print("wilderness test armed:", PLAN, TAG)
