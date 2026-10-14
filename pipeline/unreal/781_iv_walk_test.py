"""random_isometric_village_level walk test (run during PIE): drives the player over the village's nav paths.
Plan (comma separated):
  input         the 8 movement directions: scripted keyboard-style input and scripted left-stick deflections (off-axis
                angles must snap to the nearest of 8 directions; half deflection walks, full runs); the camera never turns
  rotate        Q / E (RotateView): four steps left, six right, two left; after each the camera must stand at the new
                yaw (same pitch), "up" must walk her away from the camera, and the view ends where it started
  houses:N[:turn]  visit the N nearest houses not yet visited: walk to the door, F (must open), step in (the roof and the
                camera-side walls must be cut away), walk to up to 2 containers and F each (must open), walk out again
                (the cutaway must be restored). With :turn the view is turned through all 8 directions while she is
                inside: after each step exactly the walls facing the camera must be hidden
  villagers[:S] every generated section must have its villagers (the generator's coverage x its buildings); watched for
                S seconds (default 20): they must walk, and never stand on a blocked nav cell
  zoom:min|max|default|<cm>   set the orthographic view width (min must be a close view of her: <= 600)
  expand:+x|-x|+y|-y   walk along a road across that edge of the generated village: the next section must generate
                (time, frames, buildings, unreachable doors / containers are logged), then walk 15 m into it
  home          back to the middle of the square
  shot:name     HighResShot;  map:name  open the M map, HighResShot, close it
Reports falls, stuck spots, doors / containers opened, cutaways, sections, frame times. At the end every container of
every section is measured (container_check.py): a closed lid lies on its body, a closed wardrobe's doors stand on its
front, an opened lid stands up at the back, opened doors out in front.
Args: plan tag   -> SourceArt/random_isometric_village/walk_<tag>.json and a log line "IVWALK done | <tag> | ..."
"""
import unreal, sys, json, math, time, os
PLAN = sys.argv[1].split(","); TAG = sys.argv[2]
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
W = ues.get_game_world()
assert W is not None, "PIE not running"
GEN = unreal.GameplayStatics.get_actor_of_class(W, unreal.IVVillageGenerator)
PC = unreal.GameplayStatics.get_player_controller(W, 0)
V = unreal.Vector
SS = GEN.get_editor_property("section_size")
R = {"tag": TAG, "plan": PLAN, "rotate": {}, "villagers": {}, "falls": 0, "stuck": 0, "doors_opened": 0, "doors_failed": 0, "containers_opened": 0, "containers_failed": 0, "cut_ok": 0, "cut_failed": 0,
     "houses": [], "sections": [], "events": [], "frame_ms": [], "gen_frame_ms": [], "shots": [], "input": {}}
def log(msg):
    R["events"].append(msg); unreal.log("IVWALK " + msg)
def pawn(): return PC.get_controlled_pawn()
def sec_at(p): return GEN.get_section(GEN.world_to_section(p))
S = {"step": 0, "mode": None, "path": [], "wait": 0.0, "last": None, "since": 0.0, "t0": time.time(), "door_cool": 0.0, "sub": None, "visited": set()}
def shot(name):
    unreal.SystemLibrary.execute_console_command(W, f"HighResShot 1600x900 filename=iv_{TAG}_{name}"); R["shots"].append(f"iv_{TAG}_{name}.png"); log(f"shot {name}")
def go(to):
    p = pawn().get_actor_location()
    pts = list(GEN.find_path(p, to, 400000))
    S["path"] = pts[1:] if len(pts) > 1 else pts
    S["last"] = None; S["since"] = 0.0
    return len(pts) > 0
def road_point(center, lateral_axis, span=2500.0, near=None):
    """a walkable point on a road near `center`, searched along one axis"""
    best = None
    for k in range(-int(span / 100), int(span / 100) + 1):
        q = V(center.x + (k * 100.0 if lateral_axis == 0 else 0.0), center.y + (k * 100.0 if lateral_axis == 1 else 0.0), 0)
        d, _t = GEN.road_distance(unreal.Vector2D(q.x, q.y))
        if d < -50 and GEN.is_walkable(q):
            ref = near or center; s = (q.x - ref.x) ** 2 + (q.y - ref.y) ** 2
            if best is None or s < best[0]: best = (s, q)
    return best[1] if best else None
def next_step():
    S["step"] += 1; S["sub"] = None
    if S["step"] > len(PLAN): finish(); return
    st = PLAN[S["step"] - 1]; S["mode"] = st; log(f"step {st}")
    if st == "input": S["sub"] = {"k": 0, "t": 0.0, "p0": None}
    elif st == "rotate": S["sub"] = {"k": 0, "t": 0.0, "phase": "turn", "off": 0}
    elif st.startswith("villagers"): S["sub"] = {"t": 0.0, "dur": float(st.split(":")[1]) if ":" in st else 20.0, "start": None}
    elif st.startswith("zoom:"):
        a = st.split(":")[1]; mn, mx = PC.get_editor_property("min_ortho_width"), PC.get_editor_property("max_ortho_width")
        wd = mn if a == "min" else mx if a == "max" else 2500.0 if a == "default" else float(a)
        PC.set_editor_property("ortho_width", wd); R["zoom"] = {"min": mn, "max": mx, "set": wd, "ok": mn <= 600.0}; log(f"zoom: view width {wd:.0f} cm (min {mn:.0f}, max {mx:.0f})"); S["wait"] = 1.0
    elif st.startswith("houses:"): S["sub"] = {"left": int(st.split(":")[1]), "phase": "pick", "turn": st.endswith(":turn")}
    elif st.startswith("expand:"): S["sub"] = {"phase": "edge", "ax": st.split(":")[1]}
    elif st == "home":
        if not go(V(0, 0, 0)): log("home: no path")
    elif st.startswith("shot:"): shot(st.split(":")[1]); S["wait"] = 2.0
    elif st.startswith("map:"): GEN.set_map_open(True); S["wait"] = 1.2; S["mapshot"] = st.split(":")[1]
def finish():
    fm = sorted(R["frame_ms"]); gm = sorted(R["gen_frame_ms"])
    R["frame_stats"] = {"median": fm[len(fm) // 2] if fm else 0, "p99": fm[int(len(fm) * 0.99)] if fm else 0, "max": fm[-1] if fm else 0,
                        "gen_median": gm[len(gm) // 2] if gm else 0, "gen_max": gm[-1] if gm else 0}
    R.pop("frame_ms"); R.pop("gen_frame_ms")
    b, v, n = GEN.get_village_stats(); R["village"] = {"buildings": b, "visited": v, "sections": n}
    R["sections_final"] = [(c.x, c.y) for c in GEN.get_section_coords()]
    # where the lids and wardrobe doors are (every container as it stands now: the opened ones open, the rest closed)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import container_check as CC; import importlib; importlib.reload(CC)       # (the editor keeps modules: an edited one must be reloaded)
    R["container_fit"] = fit = CC.check_all([GEN.get_section(c) for c in GEN.get_section_coords()])
    for x in fit["faults"][:8]: unreal.log("IVWALK CONTAINER FIT " + x)
    out = os.path.join(r"E:\code\claude-ue5\claude_ue5\SourceArt\random_isometric_village", f"walk_{TAG}.json"); os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(R, open(out, "w"), indent=1)
    inp = R["input"]; inp_ok = (not inp) or (inp.get("failed", 1) == 0)
    rot, vil = R["rotate"], R["villagers"]
    PC.rotate_view(-int(round((PC.get_view_yaw() - 45.0) / 45.0)))            # leave the view as it started
    ok = (R["falls"] == 0 and R["doors_failed"] == 0 and R["containers_failed"] == 0 and not fit["faults"] and fit["containers"] > 0 and R["cut_failed"] == 0 and inp_ok and rot.get("failed", 0) == 0
          and vil.get("ok", True) and R.get("zoom", {}).get("ok", True))
    unreal.log(f"IVWALK done | {TAG} | {'ok' if ok else 'ISSUES'} | falls {R['falls']} stuck {R['stuck']} | doors {R['doors_opened']} (failed {R['doors_failed']}) containers {R['containers_opened']} (failed {R['containers_failed']}) | lids and doors in place {fit['containers'] - len(fit['faults'])}/{fit['containers']} ({fit['open']} open) "
               f"| cutaway {R['cut_ok']} (failed {R['cut_failed']}) | houses {len(R['houses'])} | input {inp.get('passed', '-')}/{inp.get('tests', '-')} | rotate {rot.get('passed', '-')}/{rot.get('tests', '-')} | villagers {vil.get('summary', '-')} | sections {R['sections_final']} | village {R['village']} | frames {R['frame_stats']}")
    PC.set_scripted_move(unreal.Vector2D(0, 0), False); PC.set_scripted_stick(unreal.Vector2D(0, 0))
    unreal.unregister_slate_post_tick_callback(S["h"])
def tick(dt):
    try: _tick(dt)
    except Exception as e:
        import traceback
        unreal.log_error(f"IVWALK error {e} {traceback.format_exc()}"); unreal.unregister_slate_post_tick_callback(S["h"])
# ---- the input tests start from open ground on the square (nothing within 4.5 m); a villager walking into her way
# only means that test's distance / direction is not judged
def clear_spot():
    if S.get("clear") is None:
        best = None
        for r in range(400, 2400, 200):
            for k in range(16):
                c = V(r * math.cos(k * math.pi / 8), r * math.sin(k * math.pi / 8), 0)
                if GEN.is_walkable(c) and all(GEN.is_walkable(V(c.x + q * math.cos(b * math.pi / 4), c.y + q * math.sin(b * math.pi / 4), 0)) for q in (150, 300, 450) for b in range(8)): best = c; break
            if best: break
        S["clear"] = best or V(0, 0, 0); log(f"input tests at ({S['clear'].x:.0f},{S['clear'].y:.0f})")
    return S["clear"]
def to_clear(L):
    c = clear_spot(); p = pawn(); q = V(c.x, c.y, L.z); p.teleport(q, p.get_actor_rotation()); return q
def villager_near(L, r=240.0):
    return any(math.hypot(v.get_actor_location().x - L.x, v.get_actor_location().y - L.y) < r for v in GEN.get_villagers())
# ---- the 8 directions: (scripted source, screen x, screen y, expected index, expected run)
C45 = math.sqrt(0.5)
def expected_dir(i):
    a = math.radians(45.0 * i); up = (C45, C45); right = (-C45, C45)
    return (up[0] * math.cos(a) + right[0] * math.sin(a), up[1] * math.cos(a) + right[1] * math.sin(a))
INPUT_TESTS = []
for i in (0, 4, 2, 6, 1, 5, 3, 7):
    a = math.radians(45.0 * i); INPUT_TESTS.append(("key", round(math.sin(a)), round(math.cos(a)), i, True))
for i, off, mag in ((0, 14, 1.0), (4, -17, 1.0), (2, 20, 1.0), (6, -12, 1.0), (1, 15, 0.95), (5, -15, 1.0), (3, 10, 0.5), (7, -10, 0.55), (0, 0, 0.2)):
    a = math.radians(45.0 * i + off); INPUT_TESTS.append(("stick", math.sin(a) * mag, math.cos(a) * mag, i if mag > 0.3 else -1, mag >= 0.8))
def do_input(dt, L):
    s = S["sub"]
    if s["k"] >= len(INPUT_TESTS):
        PC.set_scripted_move(unreal.Vector2D(0, 0), False); PC.set_scripted_stick(unreal.Vector2D(0, 0))
        R["input"]["passed"] = R["input"].get("passed", 0); R["input"]["failed"] = R["input"].get("failed", 0); R["input"]["tests"] = len(INPUT_TESTS)
        rot = PC.get_iso_camera().get_actor_rotation(); R["input"]["camera"] = [round(rot.pitch, 3), round(rot.yaw, 3), round(rot.roll, 3)]
        log(f"input: {R['input']}"); next_step(); return
    src, sx, sy, ei, run = INPUT_TESTS[s["k"]]
    if s["p0"] is None:
        s["p0"] = to_clear(L); s["t"] = 0.0; s["idx"] = None; s["scale"] = None
        if src == "key": PC.set_scripted_stick(unreal.Vector2D(0, 0)); PC.set_scripted_move(unreal.Vector2D(sx, sy), False)
        else: PC.set_scripted_move(unreal.Vector2D(0, 0), False); PC.set_scripted_stick(unreal.Vector2D(sx, sy))
        return
    s["t"] += dt
    if 0.25 < s["t"] < 0.6: s["idx"] = PC.get_move_direction_index(); s["scale"] = PC.get_move_scale()
    if s["t"] < 0.8: return
    PC.set_scripted_move(unreal.Vector2D(0, 0), False); PC.set_scripted_stick(unreal.Vector2D(0, 0))
    if s["t"] < 1.15: return                                              # brake before the next one
    d = L - s["p0"]; dist = math.hypot(d.x, d.y); ok = True; why = ""
    rot = PC.get_iso_camera().get_actor_rotation()
    if abs(rot.yaw - 45.0) > 0.01 or abs(rot.pitch + 35.264) > 0.01: ok = False; why += " camera turned"
    if ei < 0:
        if dist > 15: ok = False; why += f" moved {dist:.0f} cm inside the dead zone"
    else:
        ex = expected_dir(ei); ang = math.degrees(math.acos(max(-1.0, min(1.0, (d.x * ex[0] + d.y * ex[1]) / max(dist, 1e-3)))))
        if s["idx"] != ei: ok = False; why += f" index {s['idx']} != {ei}"
        if dist < 25 or ang > 4.0:
            if villager_near(L): R["input"]["deflected"] = R["input"].get("deflected", 0) + 1; log("input: a villager in her way, distance / direction not judged")
            else: ok = False; why += f" moved {dist:.0f} cm, {ang:.1f} deg off"
        if (s["scale"] or 0) > 0.9 and not run: ok = False; why += " ran at half deflection"
        if (s["scale"] or 0) < 0.9 and run: ok = False; why += " walked at full deflection"
    R["input"]["passed" if ok else "failed"] = R["input"].get("passed" if ok else "failed", 0) + 1
    log(f"input {src} ({sx:+.2f},{sy:+.2f}) -> dir {s['idx']} scale {(s['scale'] or 0):.2f} moved {dist:.0f} cm: {'ok' if ok else 'FAILED' + why}")
    s["k"] += 1; s["p0"] = None
# ---- turning the view
TURNS = [1, 1, 1, 1, -1, -1, -1, -1, -1, -1, 1, 1]
def ang_diff(a, b): return abs((a - b + 180.0) % 360.0 - 180.0)
def do_rotate(dt, L):
    s = S["sub"]; rr = R["rotate"]
    if s["k"] >= len(TURNS):
        rr["tests"] = len(TURNS); rr.setdefault("passed", 0); rr.setdefault("failed", 0); rr["final_yaw"] = round(PC.get_view_yaw(), 3)
        if ang_diff(PC.get_view_yaw(), 45.0) > 0.01: rr["failed"] += 1; log("rotate: the view did not end where it started")
        log(f"rotate: {rr}"); next_step(); return
    s["t"] += dt
    if s["phase"] == "turn":
        PC.rotate_view(TURNS[s["k"]]); s["off"] += TURNS[s["k"]]; s["phase"] = "turning"; s["t"] = 0.0; return
    if s["phase"] == "turning":
        if PC.is_view_turning() and s["t"] < 3.0: return
        s["phase"] = "walk"; s["t"] = 0.0; s["p0"] = to_clear(L); PC.set_scripted_move(unreal.Vector2D(0, 1), True); return
    if s["phase"] == "walk":
        if s["t"] < 0.7: return
        PC.set_scripted_move(unreal.Vector2D(0, 0), False)
        want = 45.0 + 45.0 * s["off"]; rot = PC.get_iso_camera().get_actor_rotation(); d = L - s["p0"]; dist = math.hypot(d.x, d.y)
        fw = (math.cos(math.radians(want)), math.sin(math.radians(want)))
        off = math.degrees(math.acos(max(-1.0, min(1.0, (d.x * fw[0] + d.y * fw[1]) / max(dist, 1e-3)))))
        ok = True; why = ""
        if ang_diff(rot.yaw, want) > 0.05 or abs(rot.pitch + 35.264) > 0.01: ok = False; why += f" camera at yaw {rot.yaw:.2f} pitch {rot.pitch:.2f}, wanted yaw {want % 360:.0f}"
        if ang_diff(GEN.get_view_yaw(), want) > 0.05: ok = False; why += f" generator view yaw {GEN.get_view_yaw():.2f}"
        up = PC.screen_to_world_direction(unreal.Vector2D(0, 1), True)
        if up.x * fw[0] + up.y * fw[1] < 0.9995: ok = False; why += f" 'up' maps to ({up.x:.2f},{up.y:.2f}), not the camera's forward"
        # (something in her way - a stall, a villager - stops her short: only a walk that got somewhere is judged)
        if dist > 45 and off > 4.0 and not villager_near(L): ok = False; why += f" 'up' moved her {dist:.0f} cm, {off:.1f} deg off the camera's forward"
        rr["passed" if ok else "failed"] = rr.get("passed" if ok else "failed", 0) + 1
        log(f"rotate {TURNS[s['k']]:+d} -> yaw {rot.yaw:.1f}: {'ok' if ok else 'FAILED' + why}")
        s["k"] += 1; s["phase"] = "rest"; s["t"] = 0.0; return
    if s["phase"] == "rest" and s["t"] > 0.35: s["phase"] = "turn"
# ---- the villagers
def do_villagers(dt, L):
    s = S["sub"]; vv = R["villagers"]
    if s["start"] is None:
        secs = []; ok = True
        for c in GEN.get_section_coords():
            sc = GEN.get_section(c)
            if sc is None or sc.is_building(): continue
            rec = {"coord": (c.x, c.y), "buildings": sc.get_num_buildings(), "villagers": sc.get_num_villagers(), "wanted": sc.get_wanted_villagers()}
            rec["per_building"] = round(rec["villagers"] / max(rec["buildings"], 1), 3); secs.append(rec)
            if rec["villagers"] != rec["wanted"] or rec["wanted"] != math.floor(GEN.get_editor_property("villager_coverage") * rec["buildings"] + 0.5): ok = False; log(f"VILLAGERS: section {rec}")
        vs = list(GEN.get_villagers())
        s["start"] = {v.get_name(): v.get_actor_location() for v in vs}; s["blocked"] = 0; s["samples"] = 0; s["next"] = 0.0; s["walking_max"] = 0
        names = {}
        for v in vs: names[str(v.get_editor_property("villager_name"))] = names.get(str(v.get_editor_property("villager_name")), 0) + 1
        vv.update({"sections": secs, "count": len(vs), "counts_ok": ok, "models": names}); log(f"villagers: {len(vs)} in {len(secs)} sections {[(r['coord'], r['villagers'], r['buildings']) for r in secs]}"); return
    s["t"] += dt; s["next"] -= dt
    if s["next"] <= 0:
        s["next"] = 0.5; vs = list(GEN.get_villagers()); walking = 0
        for v in vs:
            p = v.get_actor_location(); s["samples"] += 1; walking += 1 if v.is_walking() else 0
            if not GEN.is_walkable(p):
                s["blocked"] += 1
                if s["blocked"] <= 5: log(f"VILLAGER {v.get_editor_property('villager_name')} on a blocked cell at ({p.x:.0f},{p.y:.0f})")
        s["walking_max"] = max(s["walking_max"], walking)
    if s["t"] < s["dur"]: return
    vs = list(GEN.get_villagers()); moved = 0; far = 0.0; trips = 0; repaths = 0
    for v in vs:
        p0 = s["start"].get(v.get_name()); p = v.get_actor_location(); trips += v.get_editor_property("trips_done"); repaths += v.get_editor_property("repaths")
        if p0 is not None:
            d = math.hypot(p.x - p0.x, p.y - p0.y); far = max(far, d); moved += 1 if d > 100 else 0
    np_, nf_, ms_, mx_ = (GEN.get_editor_property(k) for k in ("villager_paths", "villager_path_fails", "villager_path_ms", "villager_path_max_ms"))
    vv["paths"] = {"searches": np_, "none_found": nf_, "mean_ms": round(ms_ / max(np_, 1), 2), "max_ms": round(mx_, 2)}
    vv.update({"moved": moved, "farthest_cm": round(far), "walking_at_once_max": s["walking_max"], "blocked_samples": s["blocked"], "samples": s["samples"], "trips_done": trips, "repaths": repaths, "seconds": s["dur"]})
    vv["ok"] = bool(vv["counts_ok"] and vv["count"] > 0 and moved > 0 and s["blocked"] == 0)
    vv["summary"] = f"{vv['count']} ({moved} moved, {s['blocked']} blocked samples){'' if vv['ok'] else ' FAILED'}"
    log(f"villagers after {s['dur']:.0f} s: {vv['summary']}, farthest {far:.0f} cm, up to {s['walking_max']} walking at once, {trips} trips done, {repaths} given up, paths {vv['paths']}"); next_step()
def follow(dt, L, speed=1.0):
    """walk the current path; True while still walking"""
    if not S["path"]: return False
    p = pawn(); tgt = S["path"][0]; to = V(tgt.x - L.x, tgt.y - L.y, 0)
    if to.length() < 55:
        S["path"].pop(0); S["since"] = 0.0; S["last"] = L; return bool(S["path"])
    p.add_movement_input(to.normal(), speed)
    if S["last"] is None or (L - S["last"]).length() > 35: S["last"] = L; S["since"] = 0.0
    else: S["since"] += dt
    # a closed door in the way (paths may cut through a house with two doors): F
    S["door_cool"] -= dt
    if S["since"] > 0.35 and S["door_cool"] <= 0 and GEN.describe_nearest(L, 230.0) in ("open door", "open church door"):
        GEN.interact_nearest(L, 230.0); S["door_cool"] = 2.0; R["doors_opened"] += 1; S["since"] = 0.0
    if S["since"] > 4.0:
        R["stuck"] += 1; log(f"STUCK at ({L.x:.0f},{L.y:.0f}) going to ({tgt.x:.0f},{tgt.y:.0f}): near '{GEN.describe_nearest(L, 300.0)}'")
        if R["stuck"] <= 4: shot(f"stuck{R['stuck']}")
        p.teleport(V(tgt.x, tgt.y, L.z + 15), p.get_actor_rotation()); S["since"] = 0.0
    return True
def straight(dt, L, to_pt, tol=45.0, speed=0.8):
    d = V(to_pt.x - L.x, to_pt.y - L.y, 0)
    if d.length() < tol: return False
    pawn().add_movement_input(d.normal(), speed); return True
def do_houses(dt, L):
    s = S["sub"]; ph = s["phase"]
    if ph == "pick":
        if s["left"] <= 0: next_step(); return
        sec = sec_at(L); best = None
        for c in GEN.get_section_coords():
            sc = GEN.get_section(c)
            if sc is None or sc.is_building(): continue
            for i in range(sc.get_num_buildings()):
                if (c.x, c.y, i) in S["visited"]: continue
                o, inn = sc.get_building_entry(i); d = (o.x - L.x) ** 2 + (o.y - L.y) ** 2
                if best is None or d < best[0]: best = (d, sc, i, o, inn, (c.x, c.y, i))
        if best is None: log("houses: none left"); next_step(); return
        _, sc, i, o, inn, key = best; S["visited"].add(key)
        s.update({"sec": sc, "i": i, "out": o, "in": inn, "conts": list(sc.get_building_containers(i))[:2], "t": 0.0, "rec": {"kind": sc.get_building_kind(i), "style": sc.get_building_style(i), "containers": []}})
        if not go(o): log(f"house {i} {sc.get_building_kind(i)}: no path to its door"); R["doors_failed"] += 1; s["left"] -= 1; return
        s["phase"] = "to_door"; log(f"to {sc.get_building_kind(i)} {i} ({len(S['path'])} points)"); return
    sc, i = s["sec"], s["i"]
    if ph == "to_door":
        if follow(dt, L): return
        if straight(dt, L, s["out"], 35.0): return
        d = sc.get_building_door(i)
        if d >= 0 and sc.get_door_open_alpha(d) < 0.5:
            what = GEN.describe_nearest(L, 260.0)
            if what != "open door" and what != "open church door": log(f"house {i}: prompt at the door is '{what}'")
            GEN.interact_nearest(L, 260.0)
        s["phase"] = "door_wait"; s["t"] = 0.0; return
    if ph == "door_wait":
        s["t"] += dt
        if s["t"] < 1.3: return
        d = sc.get_building_door(i); a = sc.get_door_open_alpha(d) if d >= 0 else 1.0
        if a > 0.5: R["doors_opened"] += 1
        else: R["doors_failed"] += 1; log(f"DOOR FAILED {sc.get_building_kind(i)} {i} alpha {a:.2f} at ({L.x:.0f},{L.y:.0f})")
        s["phase"] = "enter"; s["t"] = 0.0; return
    if ph == "enter":
        s["t"] += dt
        if straight(dt, L, s["in"], 40.0) and s["t"] < 6.0: return
        if s["t"] >= 6.0:
            R["stuck"] += 1; log(f"STUCK in the doorway of {sc.get_building_kind(i)} {i} at ({L.x:.0f},{L.y:.0f})")
            if R["stuck"] <= 4: shot(f"stuck{R['stuck']}")
            pawn().teleport(V(s["in"].x, s["in"].y, L.z + 10), pawn().get_actor_rotation())
        s["phase"] = "inside"; s["t"] = 0.0; return
    if ph == "inside":
        s["t"] += dt
        if s["t"] < 0.6: return
        cur, cs = GEN.get_current_building()
        ok = cur == i and sc.is_building_cut(i) and sc.is_building_roof_hidden(i)
        R["cut_ok" if ok else "cut_failed"] += 1
        if not ok: log(f"CUTAWAY FAILED in {sc.get_building_kind(i)} {i}: current {cur}, cut {sc.is_building_cut(i)}, roof hidden {sc.is_building_roof_hidden(i)}")
        if len(R["houses"]) < 3: shot(f"inside{len(R['houses']) + 1}")
        s["phase"] = "turning" if s.get("turn") else "cont_pick"; s["t"] = 0.0; s["tk"] = 0; s["tph"] = 0; return
    if ph == "turning":
        # the view goes once round in 8 steps: after each, exactly the walls facing the camera are cut away
        s["t"] += dt
        if s["tph"] == 0: PC.rotate_view(1); s["tph"] = 1; s["t"] = 0.0; return
        if PC.is_view_turning() or s["t"] < 0.45: return
        walls = [(sc.is_building_wall_hidden(i, wl), sc.is_building_wall_near(i, wl)) for wl in (1, 2, 3, 4)]
        ok = all(h == nr for h, nr in walls) and any(h for h, _ in walls) and not all(h for h, _ in walls) and sc.is_building_roof_hidden(i)
        R["cut_ok" if ok else "cut_failed"] += 1; s["rec"].setdefault("turns", []).append([round(PC.get_view_yaw() % 360), [int(h) for h, _ in walls]])
        if not ok: log(f"CUTAWAY FAILED in {sc.get_building_kind(i)} {i} at view yaw {PC.get_view_yaw():.0f}: walls (hidden, facing camera) {walls}, roof hidden {sc.is_building_roof_hidden(i)}")
        if s["tk"] in (1, 3, 5) and len(R["houses"]) < 1: shot(f"turn{s['tk']}")
        s["tk"] += 1; s["tph"] = 0
        if s["tk"] >= 8: s["phase"] = "cont_pick"; s["t"] = 0.0
        return
    if ph == "cont_pick":
        if not s["conts"]:
            go(s["in"]); s["phase"] = "leave"; return
        k = s["conts"].pop(0); s["k"] = k
        st = sc.get_container_stand_point(k)
        if not go(st): log(f"container {k} ({sc.get_container_kind(k)}) in {sc.get_building_kind(i)} {i}: no path to it"); R["containers_failed"] += 1; return
        s["phase"] = "cont_go"; return
    if ph == "cont_go":
        if follow(dt, L, 0.7): return
        s["phase"] = "cont_step"; s["t"] = 0.0; return
    if ph == "cont_step":
        # the last step up to it (F takes the nearest thing: stand closer to this one than to its neighbours)
        k = s["k"]; q = sc.get_container_location(k); s["t"] += dt
        if s["t"] < 0.7 and math.hypot(q.x - L.x, q.y - L.y) > 85.0 and straight(dt, L, q, 60.0, 0.5): return
        what = GEN.describe_nearest(L, 260.0)
        if not what.startswith("open "):
            R["containers_skipped"] = R.get("containers_skipped", 0) + 1; log(f"container {k} skipped: the nearest thing here is already open ('{what}')"); s["phase"] = "cont_pick"; return
        GEN.interact_nearest(L, 260.0); s["what"] = what; s["phase"] = "cont_wait"; s["t"] = 0.0; return
    if ph == "cont_wait":
        s["t"] += dt
        if s["t"] < 1.3: return
        k = s["k"]; a = sc.get_container_open_alpha(k)
        if a > 0.5: R["containers_opened"] += 1; s["rec"]["containers"].append(sc.get_container_kind(k))
        else:
            # F took something nearer (another container): that one must have opened instead
            if GEN.describe_nearest(L, 260.0).startswith("close "): R["containers_opened"] += 1; s["rec"]["containers"].append(s["what"][5:] + "*")
            else: R["containers_failed"] += 1; log(f"CONTAINER FAILED {sc.get_container_kind(k)} {k} in {sc.get_building_kind(i)} {i} at ({L.x:.0f},{L.y:.0f}): prompt '{s['what']}', alpha {a:.2f}")
        s["phase"] = "cont_pick"; return
    if ph == "leave":
        if follow(dt, L, 0.8): return
        if straight(dt, L, s["in"], 40.0): return
        s["phase"] = "out"; s["t"] = 0.0; return
    if ph == "out":
        s["t"] += dt
        if straight(dt, L, s["out"], 45.0) and s["t"] < 6.0: return
        if s["t"] >= 6.0:
            R["stuck"] += 1; log(f"STUCK leaving {sc.get_building_kind(i)} {i} at ({L.x:.0f},{L.y:.0f})")
            pawn().teleport(V(s["out"].x, s["out"].y, L.z + 10), pawn().get_actor_rotation())
        s["phase"] = "left"; s["t"] = 0.0; return
    if ph == "left":
        s["t"] += dt
        if s["t"] < 0.6: return
        if sc.is_building_cut(i) or sc.is_building_roof_hidden(i): R["cut_failed"] += 1; log(f"CUTAWAY NOT RESTORED after leaving {sc.get_building_kind(i)} {i}")
        R["houses"].append(s["rec"]); s["left"] -= 1; s["phase"] = "pick"; return
def do_expand(dt, L):
    s = S["sub"]; ph = s["phase"]; ax = s["ax"]
    d = {"+x": V(1, 0, 0), "-x": V(-1, 0, 0), "+y": V(0, 1, 0), "-y": V(0, -1, 0)}[ax]; lat = 1 if ax[1] == "x" else 0
    if ph == "edge":
        # the outermost generated section in that direction on her row / column, and a road crossing its edge
        c = GEN.world_to_section(L)
        while GEN.is_section_generated(unreal.IntPoint(c.x + int(d.x), c.y + int(d.y))): c = unreal.IntPoint(c.x + int(d.x), c.y + int(d.y))
        edge = V(c.x * SS + d.x * (SS * 0.5 - 250), c.y * SS + d.y * (SS * 0.5 - 250), 0)
        if lat == 1: edge.y = L.y if abs(L.y - c.y * SS) < SS * 0.5 else c.y * SS
        else: edge.x = L.x if abs(L.x - c.x * SS) < SS * 0.5 else c.x * SS
        q = road_point(edge, lat, SS * 0.45, L) or edge
        s.update({"c": c, "next": unreal.IntPoint(c.x + int(d.x), c.y + int(d.y)), "q": q, "n0": GEN.get_editor_property("sections_generated"), "t": 0.0})
        if not go(q): log(f"expand {ax}: no path to the edge at ({q.x:.0f},{q.y:.0f})"); next_step(); return
        s["phase"] = "to_edge"; log(f"expand {ax}: to the edge of section ({c.x},{c.y}) at ({q.x:.0f},{q.y:.0f}), {len(S['path'])} points"); return
    if ph == "to_edge":
        if not s.get("seen") and GEN.is_section_generated(s["next"]):
            s["seen"] = True; s["seen_at"] = (L.x, L.y); log(f"section ({s['next'].x},{s['next'].y}) started generating with her at ({L.x:.0f},{L.y:.0f})")
        sec2 = GEN.get_section(s["next"])
        if s.get("seen") and not s.get("done") and sec2 is not None and not sec2.is_building():
            s["done"] = True; s["shot_t"] = 0.5
        if s.get("shot_t") is not None:
            s["shot_t"] -= dt
            if s["shot_t"] <= 0: s["shot_t"] = None; shot(f"reveal{len(R['sections']) + 1}")
        if follow(dt, L): return
        s["phase"] = "wait"; s["t"] = 0.0; return
    if ph == "wait":
        s["t"] += dt
        sec2 = GEN.get_section(s["next"])
        if sec2 is None or sec2.is_building():
            if s["t"] > 25: log(f"expand {ax}: section ({s['next'].x},{s['next'].y}) never appeared"); next_step()
            return
        q2 = road_point(s["q"] + d * 1750.0, lat, 2500.0, s["q"] + d * 1750.0)
        rec = {"coord": (s["next"].x, s["next"].y), "buildings": sec2.get_num_buildings(), "doors": sec2.get_num_doors(), "containers": sec2.get_num_containers(),
               "ms": round(sec2.get_editor_property("generate_ms")), "instances": sec2.get_editor_property("num_instances"),
               "unreachable": sec2.count_unreachable_doors(q2 or (s["q"] + d * 600.0))}
        R["sections"].append(rec); log(f"entered section {rec}")
        if q2 is None or not go(q2): log(f"expand {ax}: no road path into the new section"); next_step(); return
        s["phase"] = "into"; return
    if ph == "into":
        if s.get("shot_t") is not None:
            s["shot_t"] -= dt
            if s["shot_t"] <= 0: s["shot_t"] = None; shot(f"reveal{len(R['sections'])}")
        if follow(dt, L): return
        next_step(); return
def _tick(dt):
    if ues.get_game_world() is None: unreal.unregister_slate_post_tick_callback(S["h"]); return
    p = pawn()
    if p is None: return
    (R["gen_frame_ms"] if GEN.is_building_section() else R["frame_ms"]).append(round(dt * 1000, 1))
    if time.time() - S["t0"] > 1500: log("time limit"); finish(); return
    L = p.get_actor_location()
    if L.z < -50: R["falls"] += 1; log(f"FELL at ({L.x:.0f},{L.y:.0f},{L.z:.0f})"); p.teleport(V(L.x, L.y, 150), p.get_actor_rotation())
    if S["wait"] > 0:
        S["wait"] -= dt
        if S["wait"] <= 0 and S.get("mapshot"):
            hud = PC.get_hud(); log(f"map: {hud.get_last_map_building_count()} buildings drawn, {hud.get_last_map_label_count()} labelled")
            shot("map_" + S["mapshot"]); S["mapshot"] = None; S["wait"] = 1.5; S["closemap"] = True
        elif S["wait"] <= 0 and S.get("closemap"): S["closemap"] = False; GEN.set_map_open(False); next_step()
        elif S["wait"] <= 0: next_step()
        return
    st = S["mode"]
    if st is None: next_step(); return
    if st == "input": do_input(dt, L); return
    if st == "rotate": do_rotate(dt, L); return
    if st.startswith("villagers"): do_villagers(dt, L); return
    if st.startswith("houses:"): do_houses(dt, L); return
    if st.startswith("expand:"): do_expand(dt, L); return
    if st == "home":
        if follow(dt, L): return
        next_step(); return
    next_step()
S["h"] = unreal.register_slate_post_tick_callback(tick)
__keep__ = True
print("walk test armed", TAG, PLAN)
