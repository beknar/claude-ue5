"""random_dungeon_level walk test (run during PIE): drives the player over the dungeon's tile paths, pressing F
(ARDDungeonGenerator.InteractNearest) at closed doors and next to containers, and walks out through the edge
hallways so new sections generate. Reports falls, stuck spots, doors / containers opened (verified by their open
alpha), sections generated (and how long they took), monster wandering, frame times; screenshots on request.
At the end every container of every section is measured (container_check.py): a closed lid lies on its body, a closed
wardrobe's doors stand on its front, an opened lid stands up at the back, opened doors out in front.
Plan (comma separated): rooms:N (visit N random rooms of the current section, opening one container in each),
expand:+x|-x|+y|-y (walk out through that edge's hallway into the next section), home (back to the great hall),
shot:name (HighResShot), map:name (open the M map, HighResShot, close it).
Args: plan tag   -> SourceArt/random_dungeon/walk_<tag>.json and a log line "RDWALK done | <tag> | ..."
"""
import unreal, sys, json, math, random, time, os
PLAN = sys.argv[1].split(","); TAG = sys.argv[2]
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
W = ues.get_game_world()
assert W is not None, "PIE not running"
GEN = unreal.GameplayStatics.get_actor_of_class(W, unreal.RDDungeonGenerator)
PC = unreal.GameplayStatics.get_player_controller(W, 0)
V = unreal.Vector
rng = random.Random(7)
R = {"tag": TAG, "plan": PLAN, "falls": 0, "stuck": 0, "doors_opened": 0, "doors_failed": 0, "containers_opened": 0, "containers_failed": 0,
     "rooms_visited": [], "sections": [], "events": [], "frame_ms": [], "gen_frame_ms": [], "shots": []}
def log(msg):
    R["events"].append(msg); unreal.log("RDWALK " + msg)
def pawn(): return PC.get_controlled_pawn()
def section_at(p): return GEN.get_section(GEN.world_to_section(p))
S = {"step": 0, "path": [], "mode": None, "t": 0.0, "last": None, "since": 0.0, "wait": 0.0, "target": None, "cont": None, "cont_t": 0.0,
     "door_cool": 0.0, "goal_room": None, "expand": None, "rooms_left": 0, "t0": time.time(), "dt_prev": None, "mon0": None}
def plan_path(to):
    p = pawn().get_actor_location(); sec = section_at(p)
    if sec is None: return []
    pts = list(sec.find_path_world(p, to))
    return pts[1:] if len(pts) > 1 else pts
def next_step():
    S["step"] += 1
    if S["step"] > len(PLAN): finish(); return
    st = PLAN[S["step"] - 1]; S["mode"] = st; log(f"step {st}")
    if st.startswith("rooms:"): S["rooms_left"] = int(st.split(":")[1]); pick_room()
    elif st.startswith("expand:"):
        ax = st.split(":")[1]; p = pawn().get_actor_location(); sec = section_at(p)
        ports = list(sec.get_portal_points())
        key = {"+x": lambda q: q.x, "-x": lambda q: -q.x, "+y": lambda q: q.y, "-y": lambda q: -q.y}[ax]
        best = max(key(q) for q in ports); cand = [q for q in ports if key(q) > best - 50]
        port = min(cand, key=lambda q: (q.x - p.x) ** 2 + (q.y - p.y) ** 2)
        S["expand"] = (ax, port, GEN.get_editor_property("sections_generated")); S["path"] = plan_path(port); S["target"] = None
        log(f"expand {ax} via portal ({port.x:.0f},{port.y:.0f}), path {len(S['path'])}")
    elif st == "home": S["path"] = plan_path(GEN.get_start_room_center())
    elif st.startswith("shot:"): shot(st.split(":")[1]); S["wait"] = 2.0
    elif st.startswith("map:"):
        GEN.set_map_open(True)
        S["wait"] = 1.0; S["mapshot"] = st.split(":")[1]
def shot(name):
    unreal.SystemLibrary.execute_console_command(W, f"HighResShot 1600x900 filename=rd_{TAG}_{name}"); R["shots"].append(f"rd_{TAG}_{name}.png"); log(f"shot {name}")
def pick_room():
    p = pawn().get_actor_location(); sec = section_at(p)
    if S["rooms_left"] <= 0 or sec is None: S["path"] = []; S["goal_room"] = None; return
    n = sec.get_num_rooms(); here = sec.room_at(p)
    for _ in range(30):
        i = rng.randrange(n)
        if i == here or sec.get_room_kind(i) == "Hallway junction": continue
        tiles = list(sec.get_room_free_tiles(i))
        if not tiles: continue
        S["goal_room"] = (sec, i); S["path"] = plan_path(sec.get_room_center(i) if sec.room_at(sec.get_room_center(i)) == i and any(abs(t.x - sec.get_room_center(i).x) < 151 and abs(t.y - sec.get_room_center(i).y) < 151 for t in tiles) else tiles[len(tiles) // 2])
        if S["path"]: log(f"to room {i} {sec.get_room_kind(i)} ({len(S['path'])} tiles)"); return
    S["rooms_left"] = 0
def room_container():
    """a container of the goal room: walk next to it and press F"""
    sec, i = S["goal_room"]; mn, mx = sec.get_room_bounds(i)
    best = None
    for c in range(sec.get_num_containers()):
        q = sec.get_container_location(c)
        if mn.x <= q.x <= mx.x and mn.y <= q.y <= mx.y and sec.get_container_open_alpha(c) < 0.01 and not sec.get_container_kind(c).endswith("_r"):
            d = (q - pawn().get_actor_location()).length()
            if best is None or d < best[0]: best = (d, c, q)
    return best
def finish():
    p = pawn()
    mons = GEN.get_monsters()
    moved = 0
    for m in mons:
        k = m.get_path_name()
        if S["mon0"] and k in S["mon0"] and (m.get_actor_location() - S["mon0"][k]).length() > 300: moved += 1
    R["monsters"] = {"count": len(mons), "moved_3m": moved, "trips": sum(m.get_editor_property("trips_done") for m in mons), "repaths": sum(m.get_editor_property("repaths") for m in mons)}
    d, g = GEN.get_discovery_stats(); R["discovered"] = [d, g]
    fm = sorted(R["frame_ms"]); gm = sorted(R["gen_frame_ms"])
    R["frame_stats"] = {"median": fm[len(fm) // 2] if fm else 0, "p99": fm[int(len(fm) * 0.99)] if fm else 0, "max": fm[-1] if fm else 0,
                        "gen_median": gm[len(gm) // 2] if gm else 0, "gen_max": gm[-1] if gm else 0}
    R.pop("frame_ms"); R.pop("gen_frame_ms")
    R["sections_final"] = [(c.x, c.y) for c in GEN.get_section_coords()]
    # where the lids and wardrobe doors are (every container as it stands now: the opened ones open, the rest closed)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import container_check as CC; import importlib; importlib.reload(CC)       # (the editor keeps modules: an edited one must be reloaded)
    R["container_fit"] = fit = CC.check_all([GEN.get_section(c) for c in GEN.get_section_coords()])
    for x in fit["faults"][:8]: unreal.log("RDWALK CONTAINER FIT " + x)
    out = os.path.join(r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon", f"walk_{TAG}.json"); os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(R, open(out, "w"), indent=1)
    ok = R["falls"] == 0 and R["doors_failed"] == 0 and R["containers_failed"] == 0 and not fit["faults"] and fit["containers"] > 0
    unreal.log(f"RDWALK done | {TAG} | {'ok' if ok else 'ISSUES'} | falls {R['falls']} stuck {R['stuck']} | doors {R['doors_opened']} (failed {R['doors_failed']}) containers {R['containers_opened']} (failed {R['containers_failed']}) | lids and doors in place {fit['containers'] - len(fit['faults'])}/{fit['containers']} ({fit['open']} open) | rooms {len(R['rooms_visited'])} | sections {R['sections_final']} | monsters {R['monsters']} | frames {R['frame_stats']} | discovered {d}/{g}")
    unreal.unregister_slate_post_tick_callback(S["h"])
def tick(dt):
    try: _tick(dt)
    except Exception as e:
        unreal.log_error(f"RDWALK error {e}"); unreal.unregister_slate_post_tick_callback(S["h"])
def _tick(dt):
    if ues.get_game_world() is None: unreal.unregister_slate_post_tick_callback(S["h"]); return
    p = pawn()
    if p is None: return
    if S["mon0"] is None: S["mon0"] = {m.get_path_name(): m.get_actor_location() for m in GEN.get_monsters()}
    building = any(GEN.get_section(c).is_building() for c in GEN.get_section_coords() if GEN.get_section(c))
    (R["gen_frame_ms"] if building else R["frame_ms"]).append(round(dt * 1000, 1))
    S["t"] += dt
    if time.time() - S["t0"] > 900: log("time limit"); finish(); return
    L = p.get_actor_location()
    if L.z < -50: R["falls"] += 1; log(f"FELL at ({L.x:.0f},{L.y:.0f},{L.z:.0f})"); p.set_actor_location(V(L.x, L.y, 150), False, True)
    if S["wait"] > 0:
        S["wait"] -= dt
        if S["wait"] <= 0 and S.get("mapshot"): shot("map_" + S["mapshot"]); S["mapshot"] = None; S["wait"] = 1.5; S["closemap"] = True
        elif S["wait"] <= 0 and S.get("closemap"):
            S["closemap"] = False
            GEN.set_map_open(False)
            next_step()
        elif S["wait"] <= 0: next_step()
        return
    if S["mode"] is None: next_step(); return
    # container interaction in progress
    if S["cont"] is not None:
        sec, c, q = S["cont"]
        to = q - L; to.z = 0
        if to.length() > 150 and S["cont_t"] < 6:
            p.add_movement_input(to.normal(), 0.6); S["cont_t"] += dt; return
        if S["cont_t"] >= 0:
            GEN.interact_nearest(L, 260.0); S["cont_t"] = -1.2; return
        S["cont_t"] += dt
        if S["cont_t"] < 0: return
        a = sec.get_container_open_alpha(c)
        if a > 0.5: R["containers_opened"] += 1; log(f"opened {sec.get_container_kind(c)} {c} (alpha {a:.2f})")
        else: R["containers_failed"] += 1; log(f"CONTAINER FAILED {sec.get_container_kind(c)} {c} at ({q.x:.0f},{q.y:.0f}) alpha {a:.2f}")
        S["cont"] = None; S["rooms_left"] -= 1; pick_room(); return
    # closed door within reach: press F (and check it opens)
    S["door_cool"] -= dt
    what = GEN.describe_nearest(L, 230.0)
    if S["door_cool"] <= 0 and what.startswith("open") and "door" in what and S["path"]:
        GEN.interact_nearest(L, 230.0); S["door_cool"] = 1.6; S["door_check"] = (1.2, L)
    if S.get("door_check"):
        t, L0 = S["door_check"]; t -= dt
        if t <= 0:
            what2 = GEN.describe_nearest(L0, 230.0)
            if what2.startswith("close"): R["doors_opened"] += 1
            else: R["doors_failed"] += 1; log(f"DOOR FAILED near ({L0.x:.0f},{L0.y:.0f}): {what2}")
            S["door_check"] = None
        else: S["door_check"] = (t, L0)
        if t > 0.5: return            # let it swing first
    # follow the path
    if S["path"]:
        tgt = S["path"][0]; to = V(tgt.x - L.x, tgt.y - L.y, 0)
        if to.length() < 90:
            S["path"].pop(0); S["since"] = 0.0; S["last"] = L; return
        p.add_movement_input(to.normal(), 1.0)
        if S["last"] is None or (L - S["last"]).length() > 40: S["last"] = L; S["since"] = 0.0
        else: S["since"] += dt
        if S["since"] > 5.0:
            md = min([(m.get_actor_location() - L).length() for m in GEN.get_monsters()] or [1e9])
            R["stuck"] += 1; log(f"STUCK at ({L.x:.0f},{L.y:.0f}) going to ({tgt.x:.0f},{tgt.y:.0f}): near '{GEN.describe_nearest(L, 300.0)}', nearest monster {md:.0f} cm")
            if R["stuck"] <= 3: shot(f"stuck{R['stuck']}")
            p.set_actor_location(V(tgt.x, tgt.y, L.z + 20), False, True); S["since"] = 0.0
        return
    # path done
    st = S["mode"]
    if st.startswith("rooms:"):
        if S["goal_room"] is None: next_step(); return
        sec, i = S["goal_room"]
        if S.get("cont_pending"):
            best = S.pop("cont_pending"); S["cont"] = (sec, best[1], best[2]); S["cont_t"] = 0.0; return
        R["rooms_visited"].append(sec.get_room_kind(i))
        best = room_container()
        if best:
            # walk to the free tile next to it first, then step up to it
            q = best[2]; tiles = list(sec.get_room_free_tiles(i))
            if tiles:
                near = min(tiles, key=lambda t: (t.x - q.x) ** 2 + (t.y - q.y) ** 2)
                S["path"] = plan_path(near)
            S["cont_pending"] = best
            if not S["path"]: S.pop("cont_pending"); S["cont"] = (sec, best[1], best[2]); S["cont_t"] = 0.0
            return
        log(f"room {i} {sec.get_room_kind(i)}: no closed container"); S["rooms_left"] -= 1; pick_room()
        if not S["path"]: next_step()
        return
    if st.startswith("expand:"):
        ax, port, n0 = S["expand"]
        d = {"+x": V(1, 0, 0), "-x": V(-1, 0, 0), "+y": V(0, 1, 0), "-y": V(0, -1, 0)}[ax]
        if S["target"] is None:
            # past the border: keep walking 9 m (3 tiles) along the hallway into the next section
            S["target"] = port + d * 900.0; S["exp_t"] = 0.0
        tgt = S["target"]; to = V(tgt.x - L.x, tgt.y - L.y, 0)
        S["exp_t"] += dt
        sec2 = GEN.get_section(GEN.world_to_section(tgt))
        if sec2 is None or sec2.is_building():
            if S["exp_t"] > 20: log("expand: next section never appeared"); next_step()
            return            # wait at the border for the section
        if to.length() > 90 and S["exp_t"] < 30: p.add_movement_input(to.normal(), 1.0); return
        c = GEN.world_to_section(tgt); R["sections"].append((c.x, c.y)); log(f"entered section ({c.x},{c.y}): {sec2.get_num_rooms()} rooms, reachable {sec2.count_reachable_rooms()}, monsters {len(sec2.get_editor_property('spawned_monsters'))}")
        next_step(); return
    next_step()
S["h"] = unreal.register_slate_post_tick_callback(tick)
__keep__ = True
print("walk test armed", TAG, PLAN)
