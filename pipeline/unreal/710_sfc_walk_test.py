"""sf-city-level walk test, part 2 (PIE, armed while Play-In-Editor runs): drives the player (jrpg-fem5-tripo) and checks for
clipping and falls. Results -> SourceArt/sf_city/walk_<tag>.json, log line 'WALKTEST done | ...'.
Args: route i0 i1 tag   - run the planned route (709) from waypoint i0 to i1 (teleports to i0 first), running speed
      probes k0 k1 tag  - edge probes: start just inside a barrier wall, run into it and jump twice; she must end on walkable
                          ground of the level (stopped by the wall, or slid down onto a lower reachable floor), never below
                          the walkable minimum, with no fall-guard catch (wedges the guard released are reported)
Teleports use the engine's Teleport (moves the actor out of walls if it doesn't fit), like the game would.
Checks (every 0.1 s): capsule penetration (a capsule 4 cm thinner than hers overlapping static / dynamic geometry), mesh
clipping (spheres on head / hands / fingertips / elbows / knees overlapping visible geometry - invisible walls excluded),
feet below the visible ground (> 4 cm), falls (> 1.2 s airborne on the route), dropping below the walkable minimum, doors
not open while she is in the doorway, fall-guard catches, and stuck legs (no progress for 6 s: teleported on, reported)."""
import sys, json, math, time, unreal
MODE, A0, A1, TAGN = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\sf_city"
PLAN = json.load(open(SA + r"\walk_plan.json")); ROUTE, LABELS = PLAN["route"], PLAN["labels"]; ZMIN = PLAN["zmin"]
RCH = json.load(open(SA + r"\reach.json")); RST, RX0, RY0 = RCH["step"], RCH["x0"], RCH["y0"]; RZ = {}
for _c in RCH["cells"]: RZ.setdefault((_c[0], _c[1]), []).append(_c[2])
RCH = None
def walkable_here(l):
    """her floor (capsule centre - 85) is one of 708's reachable levels within 1 m of where she stands"""
    i, j = int(round((l.x - RX0) / RST)), int(round((l.y - RY0) / RST))
    return any(abs(z - (l.z - 85)) < 70 for a in (-1, 0, 1) for b in (-1, 0, 1) for z in RZ.get((i + a, j + b), ()))
def tp(pawn, p):
    """teleport like the game does (engine finds a non-overlapping spot); plain move only if that fails"""
    if not pawn.teleport(p, pawn.get_actor_rotation()): pawn.set_actor_location(p, False, True)
V = unreal.Vector; SL = unreal.SystemLibrary
OT = [unreal.ObjectTypeQuery.ECC_WORLD_STATIC, unreal.ObjectTypeQuery.ECC_WORLD_DYNAMIC]
CLIP_BONES = ("head", "hand_l", "hand_r", "middle_03_l", "middle_03_r", "lowerarm_l", "lowerarm_r", "calf_l", "calf_r", "spine_03")
FEET = ("foot_l", "foot_r", "ball_l", "ball_r")
S = {"t0": time.time(), "pawn": None, "phase": "wait", "acc": 0.0, "events": [], "counts": {}, "i": A0, "best": 1e9, "tb": 0.0,
     "fall": 0.0, "fell_flag": False, "k": A0, "pt": 0.0, "probe": [], "last_log": 0.0, "frames": 0, "checks": 0}
def ev(kind, **kw):
    S["counts"][kind] = S["counts"].get(kind, 0) + 1
    if S["counts"][kind] <= 40: S["events"].append(dict(kind=kind, t=round(time.time() - S["t0"], 1), **kw))
def actors_of(r):
    if r is None: return []
    if isinstance(r, tuple): r = r[-1]
    try: return list(r)
    except TypeError: return []
def visible(a):
    if a is None or a.is_hidden(): return False
    tags = [str(t) for t in a.tags]
    return not ("sfc_safety" in tags or (a.get_actor_label().startswith("RoadWall") if hasattr(a, "get_actor_label") else False))
def finish(msg):
    unreal.unregister_slate_post_tick_callback(S["h"])
    g = S.get("guard"); catches = g.get_editor_property("Catches") if g else None; unst = g.get_editor_property("Unsticks") if g else None
    out = {"mode": MODE, "range": [A0, A1], "msg": msg, "seconds": round(time.time() - S["t0"], 1), "counts": S["counts"], "events": S["events"],
           "probes": S["probe"], "guard_catches": catches, "guard_unsticks": unst, "checks": S["checks"], "pawn": S.get("pawn_info")}
    json.dump(out, open(SA + rf"\walk_{TAGN}.json", "w"), indent=1)
    unreal.log(f"WALKTEST done | {TAGN} | {msg} | counts {S['counts']} | guard catches {catches} unsticks {unst} | checks {S['checks']} | {out['seconds']} s")
    S.update(pawn=None, cm=None, mesh=None, doors=[], guard=None)        # drop actor references before PIE ends
def tick(dt):
    try: step(dt)
    except Exception as e: finish("aborted: " + repr(e)[:160])
def checks(w, pawn, cm, mesh, label):
    S["checks"] += 1
    l = pawn.get_actor_location()
    # capsule penetration
    hits = [a for a in actors_of(SL.capsule_overlap_actors(w, l, 24.0, 76.0, OT, None, [pawn])) if a is not pawn]
    if hits: ev("capsule_penetration", at=[round(l.x), round(l.y), round(l.z)], actors=sorted({a.get_actor_label() for a in hits})[:4], wp=label)
    # mesh clipping into visible geometry: a visibility trace from her capsule axis (at the bone's height) out to the bone
    # must not hit anything first - works for triangle-mesh collision too, where a buried sphere overlaps nothing.
    # (invisible walls ignore the visibility channel)
    for b in CLIP_BONES:
        p = mesh.get_socket_location(b); o = V(l.x, l.y, min(l.z + 70, max(l.z - 70, p.z)))
        L = (p - o).length()
        if L < 2: continue
        r = SL.line_trace_single(w, o, p, unreal.TraceTypeQuery.ECC_VISIBILITY, True, [pawn], unreal.DrawDebugTrace.NONE, True)
        if r and r.to_tuple()[0]:
            t = r.to_tuple(); depth = L - (t[4] - o).length()
            if depth > 2.0: ev("mesh_clip", bone=b, depth=round(depth, 1), at=[round(p.x), round(p.y), round(p.z)], actor=t[9].get_actor_label() if t[9] else "?", wp=label)
    # feet vs visible ground (only while on the ground)
    if not cm.is_falling():
        for b in FEET:
            p = mesh.get_socket_location(b)
            r = SL.line_trace_single(w, p + V(0, 0, 45), p - V(0, 0, 60), unreal.TraceTypeQuery.ECC_VISIBILITY, True, [pawn], unreal.DrawDebugTrace.NONE, True)
            if r and r.to_tuple()[0]:
                gz = r.to_tuple()[4].z
                if p.z < gz - 4.0: ev("foot_below_ground", bone=b, depth=round(gz - p.z, 1), at=[round(p.x), round(p.y), round(gz)], wp=label)
    # doors: open while she is in a doorway
    for d in S["doors"]:
        rel = d.get_actor_transform().inverse_transform_location(l)
        if abs(rel.x) < 110 and abs(rel.y) < 45 and abs(rel.z - 95) < 80 and d.get_editor_property("Alpha") < 0.6:
            ev("door_not_open", door=d.get_actor_label(), alpha=round(d.get_editor_property("Alpha"), 2), wp=label)
    if l.z < ZMIN - 300: ev("below_world", at=[round(l.x), round(l.y), round(l.z)], wp=label)
def step(dt):
    now = time.time(); S["frames"] += 1
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if S["pawn"] is None:
        pc = unreal.GameplayStatics.get_player_controller(w, 0) if w else None
        pawn = pc.get_controlled_pawn() if pc else None
        if pawn is None:
            if now - S["t0"] > 90: finish("no pawn after 90 s")
            return
        S["pawn"] = pawn; S["cm"] = pawn.get_component_by_class(unreal.CharacterMovementComponent); S["mesh"] = pawn.get_component_by_class(unreal.SkeletalMeshComponent)
        cap = pawn.get_component_by_class(unreal.CapsuleComponent)
        S["pawn_info"] = {"class": pawn.get_class().get_name(), "mesh": S["mesh"].get_skeletal_mesh_asset().get_name(),
                          "capsule": [cap.get_scaled_capsule_radius(), cap.get_scaled_capsule_half_height()]}
        acts = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor)
        S["doors"] = [a for a in acts if a.get_class().get_name() == "BP_SciFiDoor_C"]
        S["guard"] = next((a for a in acts if a.get_class().get_name() == "BP_SFC_FallGuard_C"), None)
        S["t0"] = now; S["phase"] = "go"; S["setup"] = now
        if MODE == "route":
            p = ROUTE[A0]; tp(pawn, V(p[0], p[1], p[2] + 100)); S["cm"].stop_movement_immediately()
        return
    pawn, cm, mesh = S["pawn"], S["cm"], S["mesh"]
    if now - S["setup"] < 1.0: return                                     # settle after spawn / teleport
    l = pawn.get_actor_location()
    S["acc"] += dt
    label = LABELS[S["i"]] if MODE == "route" and S["i"] < len(LABELS) else (f"probe {S['k']}" if MODE == "probes" else "")
    settling = (MODE == "probes" and (not S["pt"] or now - S["pt"] < 0.6)) or now - S.get("tp", 0.0) < 0.6      # just teleported
    if S["acc"] >= 0.1 and not settling: S["acc"] = 0.0; checks(w, pawn, cm, mesh, label or f"wp{S['i']}")
    if cm.is_falling(): S["fall"] += dt
    else: S["fall"] = 0.0; S["fell_flag"] = False
    if MODE == "route":
        if S["fall"] > 1.2 and not S["fell_flag"]: S["fell_flag"] = True; ev("long_fall", at=[round(l.x), round(l.y), round(l.z)], wp=label)
        if S["i"] >= min(A1, len(ROUTE)): finish(f"route {A0}..{S['i']} complete"); return
        tx, ty, tz = ROUTE[S["i"]]; d = math.hypot(tx - l.x, ty - l.y)
        if d < 75:
            S["i"] += 1; S["best"] = 1e9; S["tb"] = now
            if LABELS[S["i"] - 1]: unreal.log(f"WALKTEST reached {LABELS[S['i'] - 1]} (wp {S['i'] - 1}) t={now - S['t0']:.0f}s z={l.z:.0f}")
            return
        if d < S["best"] - 25: S["best"] = d; S["tb"] = now
        if now - S["tb"] > 6.0:
            ev("stuck", wp=S["i"], label=LABELS[S["i"]], at=[round(l.x), round(l.y), round(l.z)], dist=round(d))
            tp(pawn, V(tx, ty, tz + 100)); cm.stop_movement_immediately(); S["tb"] = now; S["best"] = 1e9; S["tp"] = now; return
        pawn.add_movement_input(V((tx - l.x) / d, (ty - l.y) / d, 0), 1.0, True)
    else:                                                                 # edge probes
        if S["k"] >= min(A1, len(PLAN["probes"])): finish(f"probes {A0}..{S['k']} done"); return
        pr = PLAN["probes"][S["k"]]; t = now - S["pt"] if S["pt"] else None
        ax = 0 if pr["axis"] == "x" else 1; dsgn = pr["dir"][0] if ax == 0 else pr["dir"][1]
        if t is None:
            sx, sy, sz = pr["start"]; tp(pawn, V(sx, sy, sz + 100)); cm.stop_movement_immediately()
            g = S["guard"]; S["g0"] = (g.get_editor_property("Catches"), g.get_editor_property("Unsticks")) if g else (0, 0)
            pawn.get_controller().set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=math.degrees(math.atan2(pr["dir"][1], pr["dir"][0]))))
            S["pt"] = now; S["pmax"] = -1e9; S["pzmin"] = 1e9; return
        if t < 0.5: return
        past = ((l.x if ax == 0 else l.y) - pr["plane"]) * dsgn                # > 0: beyond the wall plane
        S["pmax"] = max(S["pmax"], past); S["pzmin"] = min(S["pzmin"], l.z)
        if t < 3.4: pawn.add_movement_input(V(pr["dir"][0], pr["dir"][1], 0), 1.0, True)
        if 0.9 < t < 1.1 or 1.9 < t < 2.1: pawn.jump()
        else: pawn.stop_jumping()
        if t > 3.4: pawn.stop_jumping()
        if t > 7.5 or (t > 4.2 and not cm.is_falling()):                     # judge once she has landed (or after 7.5 s)
            # pass = still on walkable ground of the level (stopped at the wall, or slid down onto a lower reachable floor),
            # never below the walkable minimum and no fall-guard catch. Wedges the guard had to release are reported.
            g = S["guard"]; g1 = (g.get_editor_property("Catches"), g.get_editor_property("Unsticks")) if g else (0, 0)
            catches, unsticks = g1[0] - S["g0"][0], g1[1] - S["g0"][1]
            on_floor = walkable_here(l) and not cm.is_falling()
            ok = catches == 0 and S["pzmin"] > ZMIN - 300 + 85 and (on_floor or unsticks > 0)
            S["probe"].append({"k": S["k"], "ok": ok, "stopped_at_wall": S["pmax"] < -20, "max_past_plane": round(S["pmax"], 1), "min_z": round(S["pzmin"]),
                               "floor_z": round(pr["z"]), "end": [round(l.x), round(l.y), round(l.z)], "on_walkable_floor": on_floor, "guard_catches": catches,
                               "unsticks": unsticks, "start": pr["start"]})
            if not ok: ev("probe_fail", k=S["k"], max_past_plane=round(S["pmax"], 1), min_z=round(S["pzmin"]), floor_z=round(pr["z"]), catches=catches, end=[round(l.x), round(l.y), round(l.z)])
            if unsticks: ev("wedge_unstuck", k=S["k"], at=[round(l.x), round(l.y), round(l.z)])
            S["k"] += 1; S["pt"] = 0.0
    if now - S["last_log"] > 30: S["last_log"] = now; unreal.log(f"WALKTEST progress {TAGN} i={S['i']} k={S['k']} at ({l.x:.0f},{l.y:.0f},{l.z:.0f}) counts {S['counts']}")
__keep__ = True                                   # (ue_exec: keep this namespace, the tick callback uses it)
S["h"] = unreal.register_slate_post_tick_callback(tick)
print("walk test armed:", MODE, A0, A1, TAGN)
