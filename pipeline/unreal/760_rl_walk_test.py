"""random_level walk test (armed while Play-In-Editor runs; 761 starts PIE, arms this and waits for 'RLWALK done'):
drives the player (jrpg-fem5-tripo) through the procedural town and checks generation and clipping.
1. fresh session: only the 4 start cells exist (the generated town is never kept between plays)
2. expansion runs: from the origin crossroads she runs N m along a street (+x, -y, -x, +y). The cells ahead must be
   generated before she gets to them (each new cell: when it appeared, how far ahead of her), the ground under her
   must always be a generated cell's terrain (never the far plane), and its buildings must stream in their interiors.
3. building visits (generated and start cells, every purpose): from the street in front of the entrance she walks to the
   door, through it (the door must open as she comes: alpha > 0.6 in the doorway), along an interior path over the
   entry floor and back; the nearest container is opened (as the F key would) and every container of the building
   is opened and closed by script (lids / doors must reach open and shut).
Checks every 0.1 s: capsule penetration (a capsule thinner than hers overlapping static / dynamic geometry), mesh
clipping (trace from her capsule axis out to head / hands / fingertips / elbows / knees hitting visible geometry first),
feet below the ground (> 4 cm), off the generated ground, falls (> 1.5 s airborne), stuck (no progress for 6 s).
4. edge lines (line:x0:y0:x1:y1, metres): running along the town's edge street, parallel to the edge (half the street
   lies in the next cell): the generator's edge safety must create the cells across before she gets there.
Args: plan tag   plan = comma list of steps: expand:+x:400 | visit:new:6 | visit:start:8 | line:250:-200:250:200 | home
Results -> SourceArt/random_level/walk_<tag>.json"""
import sys, json, math, time, unreal
PLAN, TAGN = sys.argv[1].split(","), sys.argv[2]
__keep__ = True
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_level"
V = unreal.Vector; SL = unreal.SystemLibrary
OT = [unreal.ObjectTypeQuery.ECC_WORLD_STATIC, unreal.ObjectTypeQuery.ECC_WORLD_DYNAMIC]
CLIP_BONES = ("head", "hand_l", "hand_r", "middle_03_l", "middle_03_r", "lowerarm_l", "lowerarm_r", "calf_l", "calf_r", "spine_03")
FEET = ("foot_l", "foot_r", "ball_l", "ball_r")
S = {"t0": time.time(), "pawn": None, "events": [], "counts": {}, "checks": 0, "step": -1, "task": None, "log": [], "visited": set(),
     "cells_seen": {}, "new_cells": [], "start_cells": None, "last": 0.0}
def ev(kind, **kw):
    S["counts"][kind] = S["counts"].get(kind, 0) + 1
    if S["counts"][kind] <= 30: S["events"].append(dict(kind=kind, t=round(time.time() - S["t0"], 1), task=S["task"]["name"] if S["task"] else None, **kw))
def note(msg):
    S["log"].append(f"{time.time() - S['t0']:.0f}s {msg}"); unreal.log("RLWALK " + msg)
def finish(msg):
    unreal.unregister_slate_post_tick_callback(S["h"]); unreal._rlwalk_active = False
    out = {"plan": PLAN, "msg": msg, "seconds": round(time.time() - S["t0"], 1), "counts": S["counts"], "events": S["events"], "log": S["log"],
           "checks": S["checks"], "start_cells": sorted(S["start_cells"] or []), "new_cells": S["new_cells"], "cells_end": S.get("cells_end")}
    json.dump(out, open(SA + rf"\walk_{TAGN}.json", "w"), indent=1)
    unreal.log(f"RLWALK done | {TAGN} | {msg} | counts {S['counts']} | checks {S['checks']} | new cells {len(S['new_cells'])} | {out['seconds']} s")
    S.update(pawn=None, cm=None, mesh=None, gen=None, task=None, w=None)
def tick(dt):
    try: step(dt)
    except Exception as e:
        import traceback; finish("aborted: " + traceback.format_exc()[-400:])
def lbl(a):
    try: return a.get_actor_label()
    except Exception: return a.get_name() if a else "?"
def checks():
    w, pawn, cm, mesh = S["w"], S["pawn"], S["cm"], S["mesh"]
    S["checks"] += 1
    l = pawn.get_actor_location(); name = S["task"]["name"] if S["task"] else ""
    hits = [a for a in (SL.capsule_overlap_actors(w, l, 24.0, 76.0, OT, None, [pawn]) or []) if a is not pawn]
    if hits: ev("capsule_penetration", at=[round(l.x), round(l.y), round(l.z)], actors=sorted({lbl(a) for a in hits})[:4])
    for b in CLIP_BONES:
        p = mesh.get_socket_location(b); o = V(l.x, l.y, min(l.z + 70, max(l.z - 70, p.z)))
        L = (p - o).length()
        if L < 2: continue
        r = SL.line_trace_single(w, o, p, unreal.TraceTypeQuery.ECC_VISIBILITY, True, [pawn], unreal.DrawDebugTrace.NONE, True)
        if r and r.to_tuple()[0]:
            t = r.to_tuple(); depth = L - (t[4] - o).length()
            if depth > 2.0: ev("mesh_clip", bone=b, depth=round(depth, 1), at=[round(p.x), round(p.y), round(p.z)], actor=lbl(t[9]) if t[9] else "?")
    g = SL.line_trace_single(w, l, l - V(0, 0, 600), unreal.TraceTypeQuery.ECC_VISIBILITY, True, [pawn], unreal.DrawDebugTrace.NONE, True)
    gt = g.to_tuple() if g else None
    if not (gt and gt[0]): ev("no_ground", at=[round(l.x), round(l.y), round(l.z)])
    elif lbl(gt[9]) == "FarGround": ev("off_generated_ground", at=[round(l.x), round(l.y), round(l.z)])
    if not cm.is_falling():
        S["air"] = 0.0
        for b in FEET:
            p = mesh.get_socket_location(b)
            r = SL.line_trace_single(w, p + V(0, 0, 45), p - V(0, 0, 60), unreal.TraceTypeQuery.ECC_VISIBILITY, True, [pawn], unreal.DrawDebugTrace.NONE, True)
            if r and r.to_tuple()[0]:
                gz = r.to_tuple()[4].z
                if p.z < gz - 4.0: ev("foot_below_ground", bone=b, depth=round(gz - p.z, 1), at=[round(p.x), round(p.y), round(gz)], on=lbl(r.to_tuple()[9]))
    else:
        S["air"] = S.get("air", 0.0) + 0.1
        if S["air"] > 1.5 and not S.get("air_flag"): ev("fall", at=[round(l.x), round(l.y), round(l.z)]); S["air_flag"] = True
    if S["air"] == 0.0: S["air_flag"] = False
    # doors of the building being visited: open while she is in its doorway
    b = S["task"].get("bld") if S["task"] else None
    if b:
        for i in range(b.get_num_doors()):
            dl = b.get_door_location(i)
            if abs(dl.z - l.z) < 120 and math.hypot(dl.x - l.x, dl.y - l.y) < 70:
                a = b.get_door_open_alpha(i); S["task"]["door_max"] = max(S["task"].get("door_max", 0.0), a)
                if a < 0.6: ev("door_not_open", building=lbl(b), door=i, alpha=round(a, 2))
    # generation bookkeeping
    cells = S["gen"].get_cell_coords()
    for c in cells:
        k = (c.x, c.y)
        if k not in S["cells_seen"]:
            S["cells_seen"][k] = time.time()
            if S["start_cells"] is not None and k not in S["start_cells"]:
                cs = S["gen"].get_property("cell_size") if False else 25000.0
                # distance from her to that cell (0 = inside it)
                dx = max(c.x * cs - l.x, 0, l.x - (c.x + 1) * cs); dy = max(c.y * cs - l.y, 0, l.y - (c.y + 1) * cs)
                S["new_cells"].append({"cell": list(k), "t": round(time.time() - S["t0"], 1), "her": [round(l.x), round(l.y)], "dist_m": round(math.hypot(dx, dy) / 100, 1), "task": name})
    here = S["gen"].world_to_cell(l)
    if not S["gen"].is_cell_generated(here): ev("in_ungenerated_cell", cell=[here.x, here.y], at=[round(l.x), round(l.y)])
def tp(p):
    pawn = S["pawn"]
    if not pawn.teleport(p, pawn.get_actor_rotation()): pawn.set_actor_location(p, False, True)
    S["cm"].stop_movement_immediately()
def start_task(spec):
    kind = spec.split(":")[0]
    if kind == "expand":
        _, d, dist = spec.split(":"); dist = float(dist) * 100
        dx, dy = {"+x": (1, 0), "-x": (-1, 0), "+y": (0, 1), "-y": (0, -1)}[d]
        gz = S["gen"].ground_height_at(0.0, 0.0)
        tp(V(0, 0, gz + 100))
        S["task"] = {"name": spec, "kind": "walk", "pts": [V(dx * dist, dy * dist, 0)], "i": 0, "speed": 1.0, "t": time.time(), "best": 1e12, "tb": time.time()}
        note(f"{spec}: running {dist / 100:.0f} m along the street")
    elif kind == "visit":
        _, where, n = spec.split(":"); n = int(n)
        cells = [(c.x, c.y) for c in S["gen"].get_cell_coords()]
        cells = [c for c in cells if (c in S["start_cells"]) == (where == "start")]
        blds = []
        for c in cells: blds += [b for b in S["gen"].get_buildings_in_cell(unreal.IntPoint(c[0], c[1])) if b.get_num_interior_paths() > 0 and lbl(b) not in S["visited"]]
        order = {"tavern": 0, "home": 1, "store": 2, "cabin": 3, "workshop": 4}
        picked, seen_p = [], {}
        for b in sorted(blds, key=lambda b: (order.get(str(b.get_purpose()), 9), lbl(b))):
            p = str(b.get_purpose())
            if seen_p.get(p, 0) >= max(1, n // 3): continue
            picked.append(b); seen_p[p] = seen_p.get(p, 0) + 1
            if len(picked) >= n: break
        S["queue"] = picked + S.get("queue", [])
        note(f"{spec}: {len(picked)} buildings ({', '.join(str(b.get_template_name()) for b in picked)})")
        S["task"] = None
    elif kind == "line":
        # line:x0:y0:x1:y1 (m) - e.g. along the start square's edge street, parallel to the edge: the edge-street safety
        # must generate the cells across before she could step off the generated ground
        x0, y0, x1, y1 = [float(v) * 100 for v in spec.split(":")[1:]]
        tp(V(x0, y0, S["gen"].ground_height_at(x0, y0) + 100))
        S["task"] = {"name": spec, "kind": "walk", "pts": [V(x1, y1, 0)], "i": 0, "speed": 1.0, "t": time.time(), "best": 1e12, "tb": time.time()}
        note(f"{spec}: running from ({x0 / 100:.0f}, {y0 / 100:.0f}) to ({x1 / 100:.0f}, {y1 / 100:.0f}) m")
    elif kind == "home":
        gz = S["gen"].ground_height_at(0.0, 0.0); tp(V(0, 0, gz + 100)); S["task"] = None
def start_visit(b):
    S["visited"].add(lbl(b))
    street, outside, inside = b.get_entry()
    path = b.get_interior_path(0) if b.get_num_interior_paths() else []
    tp(V(street.x, street.y, street.z + 110))
    pts = [outside, inside] + list(path)
    back = list(reversed(pts[1:-1])) + [outside]
    S["task"] = {"name": f"visit {lbl(b)} ({b.get_purpose()})", "kind": "visit", "bld": b, "pts": pts, "back": back, "i": 0, "speed": 0.45, "t": time.time(),
                 "best": 1e12, "tb": time.time(), "phase": "in", "ready": b.is_interior_ready(), "inside_z": inside.z}
def step(dt):
    now = time.time()
    if S["pawn"] is None:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        pc = unreal.GameplayStatics.get_player_controller(w, 0) if w else None
        p = pc.get_controlled_pawn() if pc else None
        gens = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.RTTownGenerator) if w else []
        if p is None or not gens:
            if now - S["t0"] > 90: finish("no pawn / generator")
            return
        S.update(w=w, pawn=p, cm=p.get_component_by_class(unreal.CharacterMovementComponent), mesh=p.get_component_by_class(unreal.SkeletalMeshComponent), gen=gens[0])
        S["start_cells"] = {(c.x, c.y) for c in gens[0].get_cell_coords()}
        note(f"session start: {len(S['start_cells'])} cells {sorted(S['start_cells'])}, seed {gens[0].get_editor_property('session_seed')}")
        if len(S["start_cells"]) != 4: ev("start_not_square", cells=sorted(S["start_cells"]))
        S["wait_until"] = now + 6.0
        return
    if now < S.get("wait_until", 0): return
    if now - S["last"] >= 0.1: S["last"] = now; checks()
    t = S["task"]
    if t is None:
        if S.get("queue"):
            start_visit(S["queue"].pop(0)); return
        S["step"] += 1
        if S["step"] >= len(PLAN):
            S["cells_end"] = sorted([c.x, c.y] for c in S["gen"].get_cell_coords()); finish("ok"); return
        start_task(PLAN[S["step"]]); S["wait_until"] = now + 1.0; return
    pawn = S["pawn"]; l = pawn.get_actor_location()
    if t["i"] >= len(t["pts"]):
        if t["kind"] == "visit" and t["phase"] == "in":
            # walk up to the nearest container on this floor (if any) and open it as the F key does
            b = t["bld"]; best = None
            for i in range(b.get_num_containers()):
                cl = b.get_container_location(i)
                if abs(cl.z - l.z) < 160:
                    dd = math.hypot(cl.x - l.x, cl.y - l.y)
                    if best is None or dd < best[0]: best = (dd, i, cl)
            t["phase"] = "approach"; t["near_target"] = best[2] if best and best[0] < 900 else None; t["ta"] = now; t["best"] = 1e12; t["tb"] = now
            if t["near_target"] is None: t["phase"] = "press"
            return
        if t["kind"] == "visit" and t["phase"] == "approach":
            cl = t["near_target"]; d = V(cl.x - l.x, cl.y - l.y, 0)
            if d.length() < 150 or now - t["tb"] > 4.0 or now - t["ta"] > 15:
                t["phase"] = "press"; return
            if d.length() < t["best"] - 10: t["best"] = d.length(); t["tb"] = now
            pawn.add_movement_input(d.normal(), 0.35, False); return
        if t["kind"] == "visit" and t["phase"] == "press":
            b = t["bld"]
            k = b.toggle_nearest_container(l, 220.0)
            t["near"] = (k, b.get_container_kind(k)) if k >= 0 else None
            # then every other container by script (a wardrobe's two doors open together: toggle it once)
            skip = {k}
            if k >= 0 and b.get_container_kind(k) == "wardrobe": skip.add(k + 1)
            if k >= 0 and b.get_container_kind(k) == "wardrobe_r": skip.add(k - 1)
            for i in range(b.get_num_containers()):
                if i in skip or b.get_container_kind(i) == "wardrobe_r": continue
                b.toggle_container(i)
            t["phase"] = "cont"; t["tc"] = now
            return
        if t["kind"] == "visit" and t["phase"] == "cont":
            if now - t["tc"] < 1.6: return
            b = t["bld"]; n = b.get_num_containers(); opened = sum(1 for i in range(n) if b.get_container_open_alpha(i) > 0.95)
            if opened < n: ev("container_not_open", building=lbl(b), opened=opened, of=n)
            for i in range(n):
                if b.get_container_kind(i) != "wardrobe_r": b.toggle_container(i)
            t["containers"] = (opened, n); t["phase"] = "out"; t["pts"] = t["back"]; t["i"] = 0; t["tb"] = now; t["best"] = 1e12
            return
        if t["kind"] == "visit":
            b = t["bld"]; n = b.get_num_containers(); shut = sum(1 for i in range(n) if b.get_container_open_alpha(i) < 0.05)
            if shut < n: ev("container_not_shut", building=lbl(b), shut=shut, of=n)
            # (only when the entrance has a door: an open doorway, e.g. template 02, has none near it)
            st_, out_, in_ = b.get_entry(); em = V((out_.x + in_.x) / 2, (out_.y + in_.y) / 2, in_.z)
            has_entry_door = any((b.get_door_location(i) - em).length() < 260 for i in range(b.get_num_doors()))
            if has_entry_door and t.get("door_max", 0.0) < 0.6: ev("entry_door_never_opened", building=lbl(b))
            note(f"{t['name']}: done in {now - t['t']:.0f}s, door max {t.get('door_max', '-')}, containers open {t.get('containers')}, near container {t.get('near')}, interior ready {b.is_interior_ready()}")
        else:
            cs = 25000.0
            note(f"{t['name']}: done in {now - t['t']:.0f}s at {[round(l.x), round(l.y)]}, cells now {S['gen'].get_num_cells()}")
        S["task"] = None; return
    tgt = t["pts"][t["i"]]
    d = V(tgt.x - l.x, tgt.y - l.y, 0); dist = d.length()
    if dist < (55 if t["kind"] == "visit" else 120):
        t["i"] += 1; t["best"] = 1e12; t["tb"] = now; return
    if dist < t["best"] - 15: t["best"] = dist; t["tb"] = now
    elif now - t["tb"] > 6.0:
        ev("stuck", at=[round(l.x), round(l.y), round(l.z)], target=[round(tgt.x), round(tgt.y)], dist=round(dist))
        t["i"] += 1; t["best"] = 1e12; t["tb"] = now; return
    speed = t["speed"] if not (t["kind"] == "visit" and t["i"] == 0) else 0.8
    pawn.add_movement_input(d.normal(), speed, False)
if getattr(unreal, "_rlwalk_active", False):          # (761 retries the arm call while PIE starts: never run two walkers)
    print("walk test armed (already running)")
else:
    unreal._rlwalk_active = True
    S["h"] = unreal.register_slate_post_tick_callback(tick)
    print("walk test armed:", PLAN, TAGN)
