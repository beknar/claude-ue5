"""starship_level flight test, run in PIE (803_ss_flight.ps1 starts PIE, arms this and waits for "SSFLIGHT done").
Flies the fighter through the player controller's scripted inputs (the same code paths as the keyboard, the mouse and an
Xbox controller) and checks what happens. Plan = comma separated steps:
  input        every control on its own from the start point: W / S throttle, A / D roll, mouse left / right / up / down
               (and that the nose stops when the mouse does), the buttons (cannons, missile, afterburner), then the same
               on the controller (left stick, right stick, RT, LT, A)
  agile        the mouse turns the fighter like a fighter: a fast hand reaches the mouse turn rates (well above the
               stick's), a quarter turn takes well under a second, a slow hand still gives fine control, the chase
               camera keeps the fighter in view through it, and the stick's turn rates are what they were
  camera       the view is a chase camera behind and above the fighter; zooming moves it
  cannon[:N]   N times: pick an asteroid in sight, fly at it, shoot it with the cannons until it is destroyed (default 3)
  missile[:N]  N times: turn on a target drone, lock it, fire missiles until it is destroyed (default 2)
  edge         fly out of the 5 km cube: the fighter must be turned back and come inside again
  collide      fly into a big asteroid: it must bounce off (hull damage), not end up inside it, and fly on
  tour[:S]     S seconds round the station on autopilot (frame times with everything in view; default 20)
Writes SourceArt/starship/flight_<tag>.json and logs "SSFLIGHT done | <tag> | ok / FAILED | ...". Args: plan tag"""
import unreal, sys, json, math, os
__keep__ = True
PLAN = [s.strip() for s in (sys.argv[1] if len(sys.argv) > 1 else "input,agile,camera,cannon,missile,edge,collide").split(",") if s.strip()]
TAG = sys.argv[2] if len(sys.argv) > 2 else "t"
OUT = "E:\\code\\claude-ue5\\claude_ue5\\SourceArt\\starship"
V = unreal.Vector; V2 = unreal.Vector2D; ML = unreal.MathLibrary; GS = unreal.GameplayStatics
G = {}; R = {"tag": TAG, "plan": PLAN, "steps": [], "frames": []}
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
assert w is not None, "PIE is not running"
pc = GS.get_player_controller(w, 0); f = pc.get_controlled_pawn()
assert isinstance(f, unreal.SSFighter), "the player does not fly an SSFighter"
ar = f.get_arena(); assert ar, "no arena"
G.update({"w": w, "pc": pc, "f": f, "ar": ar, "dt": 0.016})
DZ = pc.get_editor_property("stick_dead_zone")
pc.set_scripted_only(True)                    # the real mouse must not fly the fighter during the test
def now(): return GS.get_time_seconds(G["w"])
def alive(t):
    try: return t is not None and unreal.SystemLibrary.is_valid(t) and t.is_alive()
    except Exception: return False
def clear(): G["pc"].clear_scripted()
def stick_for(frac):
    """raw stick deflection that gives this fraction of the turn rate (inverse of the controller's dead zone + curve)"""
    a = min(1.0, abs(frac))
    if a < 0.01: return 0.0
    u = (-0.45 + math.sqrt(0.2025 + 2.2 * a)) / 1.1
    return math.copysign(DZ + u * (1 - DZ), frac)
def local_dir(p):
    f = G["f"]; return ML.inverse_transform_direction(f.get_actor_transform(), (p - f.get_actor_location()).normal())
def aim_error(p):
    d = local_dir(p); return math.degrees(math.atan2(d.y, d.x)), math.degrees(math.atan2(d.z, math.hypot(d.x, d.y)))
def fly_at(p, throttle=0.0, fire=False, missile=False, boost=False, gain=10.0, target=None):
    """controller only: right stick toward p, left stick for the throttle wanted (-1..1 change). Whatever is in the way
    (other than `target`) is flown round: the stick goes to the side its surface faces."""
    f = G["f"]; l = f.get_actor_location(); v = f.get_velocity(); sp = v.length()
    if sp > 500.0:
        h = unreal.SystemLibrary.sphere_trace_single(G["w"], l, l + v.normal() * (sp * 1.7 + 2500.0), 520.0, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [f], unreal.DrawDebugTrace.NONE, True)
        t = h.to_tuple() if h else None
        if t and t[0] and t[9] != target:
            n = t[7] if t[7].length() > 0.5 else (l - t[5]).normal()
            side = n - v.normal() * n.dot(v.normal())
            if side.length() < 0.05: side = f.get_actor_up_vector()
            p = l + (v.normal() * 0.6 + side.normal()).normal() * 30000.0
            fire = False; boost = False
            if t[3] < sp * 0.9: throttle = -1.0
    yaw, pitch = aim_error(p)
    G["pc"].set_scripted_pad(V2(0.0, stick_for(throttle)), V2(stick_for(yaw / gain), stick_for(pitch / gain)), 1.0 if missile else 0.0, 1.0 if fire else 0.0, boost)
    return math.hypot(yaw, pitch)
def hold_throttle(want):
    t = G["f"].get_throttle(); return 0.0 if abs(t - want) < 0.04 else (1.0 if t < want else -1.0)
def wait(sec):
    t0 = now()
    while now() - t0 < sec: yield
def until_alive():
    while G["f"].is_destroyed(): yield
    yield from wait(0.3)
def sight(target, ignore_extra=()):
    """is the way from the fighter to the target clear (the first thing a ray hits is the target itself)"""
    f = G["f"]; a = f.get_actor_location(); b = target.get_actor_location()
    h = unreal.SystemLibrary.line_trace_single(G["w"], a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [f], unreal.DrawDebugTrace.NONE, True)
    if not h: return True
    t = h.to_tuple(); return (not t[0]) or t[9] == target
def step_result(name, ok, **kw):
    R["steps"].append({"step": name, "ok": bool(ok), **kw})
    unreal.log(f"SSFLIGHT step {name}: {'ok' if ok else 'FAILED'} {json.dumps(kw)[:300]}")

# ---------------------------------------------------------------- input: every control on its own
def step_input():
    f, pc = G["f"], G["pc"]
    vmax = f.get_editor_property("max_speed")
    def snap():
        return {"thr": f.get_throttle(), "fwd": f.get_actor_forward_vector(), "right": f.get_actor_right_vector(), "up": f.get_actor_up_vector(), "shots": f.shots_fired, "missiles": f.missiles_fired,
                "speed": f.get_speed()}
    K = lambda w_=False, s=False, a=False, d=False, b=False: (lambda: pc.set_scripted_keys(w_, s, a, d, b))
    M = lambda x, y: (lambda: pc.set_scripted_mouse(V2(x, y)))
    B = lambda l, r: (lambda: pc.set_scripted_buttons(l, r))
    P = lambda l=(0, 0), r=(0, 0), lt=0.0, rt=0.0, a=False: (lambda: pc.set_scripted_pad(V2(*l), V2(*r), lt, rt, a))
    tests = [  # name, apply, seconds, value(before, after), passes(value)
        ("key W: throttle up", K(w_=True), 0.8, lambda a, b: b["thr"] - a["thr"], lambda v: v > 0.3),
        ("key S: throttle down", K(s=True), 0.5, lambda a, b: b["thr"] - a["thr"], lambda v: v < -0.2),
        ("key D: roll right", K(d=True), 0.5, lambda a, b: b["right"].z, lambda v: v < -0.3),
        ("key A: roll left", K(a=True), 0.5, lambda a, b: b["right"].z, lambda v: v > 0.3),
        ("mouse right: nose right", M(500, 0), 1.0, lambda a, b: b["fwd"].dot(a["right"]), lambda v: v > 0.25),
        ("mouse left: nose left", M(-500, 0), 1.0, lambda a, b: b["fwd"].dot(a["right"]), lambda v: v < -0.25),
        ("mouse up: nose up", M(0, 500), 1.0, lambda a, b: b["fwd"].dot(a["up"]), lambda v: v > 0.25),
        ("mouse down: nose down", M(0, -500), 1.0, lambda a, b: b["fwd"].dot(a["up"]), lambda v: v < -0.25),
        ("left button: cannons", B(True, False), 0.6, lambda a, b: b["shots"] - a["shots"], lambda v: v >= 5),
        ("right button: missile", B(False, True), 0.3, lambda a, b: b["missiles"] - a["missiles"], lambda v: v >= 1),
        ("Shift: afterburner", K(w_=True, b=True), 3.0, lambda a, b: b["speed"] / vmax, lambda v: v > 1.25),
        ("pad left stick up: throttle up", P(l=(0, 1)), 0.8, lambda a, b: b["thr"] - a["thr"], lambda v: v > 0.3),
        ("pad left stick down: throttle down", P(l=(0, -1)), 0.5, lambda a, b: b["thr"] - a["thr"], lambda v: v < -0.2),
        ("pad left stick right: roll right", P(l=(1, 0)), 0.5, lambda a, b: b["right"].z, lambda v: v < -0.3),
        ("pad left stick left: roll left", P(l=(-1, 0)), 0.5, lambda a, b: b["right"].z, lambda v: v > 0.3),
        ("pad right stick right: nose right", P(r=(1, 0)), 0.8, lambda a, b: b["fwd"].dot(a["right"]), lambda v: v > 0.4),
        ("pad right stick left: nose left", P(r=(-1, 0)), 0.8, lambda a, b: b["fwd"].dot(a["right"]), lambda v: v < -0.4),
        ("pad right stick up: nose up", P(r=(0, 1)), 0.8, lambda a, b: b["fwd"].dot(a["up"]), lambda v: v > 0.4),
        ("pad right stick down: nose down", P(r=(0, -1)), 0.8, lambda a, b: b["fwd"].dot(a["up"]), lambda v: v < -0.4),
        ("pad RT: cannons", P(rt=1.0), 0.6, lambda a, b: b["shots"] - a["shots"], lambda v: v >= 5),
        ("pad LT: missile", P(lt=1.0), 0.3, lambda a, b: b["missiles"] - a["missiles"], lambda v: v >= 1),
        ("pad A: afterburner", P(l=(0, 1), a=True), 3.0, lambda a, b: b["speed"] / vmax, lambda v: v > 1.25),
        ("pad stick inside the dead zone: nothing", P(l=(DZ * 0.8, DZ * 0.8), r=(DZ * 0.8, -DZ * 0.8)), 0.6, lambda a, b: abs(b["thr"] - a["thr"]) + (1 - b["fwd"].dot(a["fwd"])) + abs(b["right"].z - a["right"].z), lambda v: v < 0.01),
    ]
    out = []; passed = 0
    for name, apply, sec, value, good in tests:
        clear(); f.respawn(); yield from wait(0.45)
        a = snap(); apply(); yield from wait(sec); b = snap(); clear()
        v = value(a, b); ok = bool(good(v)); passed += ok
        out.append({"test": name, "value": round(float(v), 3), "ok": ok})
        if "pad" in name and name.split(":")[0] != "pad stick inside the dead zone" and not pc.is_using_gamepad(): out[-1]["ok"] = False; out[-1]["note"] = "not seen as a gamepad"; passed -= ok
    # the nose stops when the mouse does (it only closes the gap to the aim point)
    # (a small turn and a short wait: the first gate's rim is 170 m ahead, and bouncing off it would turn the nose)
    clear(); f.respawn(); yield from wait(0.4); c0 = f.collisions
    pc.set_scripted_mouse(V2(240, 90)); yield from wait(0.5); pc.set_scripted_mouse(V2(0, 0)); yield from wait(0.7)
    d0 = f.get_actor_forward_vector(); yield from wait(0.4); d1 = f.get_actor_forward_vector()
    drift = math.degrees(math.acos(max(-1.0, min(1.0, d0.dot(d1))))); ok = drift < 1.0 and f.get_aim().length() < 1.0 and f.collisions == c0; passed += ok
    out.append({"test": "mouse still: nose still", "value": round(drift, 2), "ok": bool(ok), "collisions": f.collisions - c0})
    clear(); f.respawn(); yield from wait(0.3)
    step_result("input", passed == len(out), passed=passed, tests=len(out), failed=[o for o in out if not o["ok"]], all=out)

def step_agile():
    f, pc = G["f"], G["pc"]; cm = pc.player_camera_manager
    sens = pc.get_editor_property("mouse_sensitivity") * pc.get_editor_property("mouse_scale")
    my, mp, sy, sp_ = (f.get_editor_property(k) for k in ("mouse_yaw_rate", "mouse_pitch_rate", "yaw_rate", "pitch_rate"))
    def turn(apply, sec, axis):
        """peak turn rate, degrees turned, seconds to the first 90 degrees, and the widest the fighter got from the middle of the view"""
        clear(); f.respawn(); yield from wait(0.5)
        d0 = f.get_actor_forward_vector(); t0 = now(); peak = 0.0; t90 = None; off = 0.0; ang = 0.0; prev = d0
        apply()
        while now() - t0 < sec:
            r = f.get_turn_rates(); peak = max(peak, abs(r.x if axis == 0 else r.y))
            d = f.get_actor_forward_vector(); ang += math.degrees(math.acos(max(-1.0, min(1.0, d.dot(prev))))); prev = d
            if t90 is None and ang >= 90.0: t90 = now() - t0
            c = cm.get_camera_rotation().get_forward_vector().dot((f.get_actor_location() - cm.get_camera_location()).normal())
            off = max(off, math.degrees(math.acos(max(-1.0, min(1.0, c)))))
            yield
        clear(); G["turn"] = {"peak": round(peak, 1), "turned": round(ang, 1), "t90": None if t90 is None else round(t90, 2), "view_off": round(off, 1)}
    out = {}
    # a fast hand (20000 counts a second: an 800 dpi mouse at 64 cm/s), yaw then pitch
    yield from turn(lambda: pc.set_scripted_mouse(V2(20000, 0)), 1.0, 0); out["mouse_fast_yaw"] = G["turn"]
    yield from turn(lambda: pc.set_scripted_mouse(V2(0, 20000)), 1.0, 1); out["mouse_fast_pitch"] = G["turn"]
    # a slow hand: the nose turns at the hand's own rate (counts x sensitivity)
    yield from turn(lambda: pc.set_scripted_mouse(V2(300, 0)), 1.5, 0); out["mouse_slow_yaw"] = G["turn"]; slow_want = 300 * sens
    # the stick, full over: what it was
    yield from turn(lambda: pc.set_scripted_pad(V2(0, 0), V2(1, 0), 0.0, 0.0, False), 1.2, 0); out["stick_yaw"] = G["turn"]
    yield from turn(lambda: pc.set_scripted_pad(V2(0, 0), V2(0, 1), 0.0, 0.0, False), 1.2, 1); out["stick_pitch"] = G["turn"]
    clear(); f.respawn(); yield from wait(0.3)
    half_v = math.degrees(math.atan(math.tan(math.radians(f.get_editor_property("base_fov") / 2.0)) * 9.0 / 16.0))
    ok = (out["mouse_fast_yaw"]["peak"] > my * 0.93 and out["mouse_fast_pitch"]["peak"] > mp * 0.93 and (out["mouse_fast_yaw"]["t90"] or 9) < 0.75 and (out["mouse_fast_pitch"]["t90"] or 9) < 0.75
          and abs(out["mouse_slow_yaw"]["peak"] - slow_want) < slow_want * 0.15 and out["stick_yaw"]["peak"] <= sy + 0.5 and out["stick_pitch"]["peak"] <= sp_ + 0.5
          and out["stick_yaw"]["peak"] > sy * 0.95 and max(o["view_off"] for o in out.values()) < half_v)
    step_result("agile", ok, mouse_rates=[my, mp], stick_rates=[sy, sp_], degrees_per_count=sens, slow_hand_wanted=round(slow_want, 1), half_view_deg=round(half_v, 1), **out)

def step_camera():
    f, pc = G["f"], G["pc"]; cm = pc.player_camera_manager
    def cam_local(): return ML.inverse_transform_location(f.get_actor_transform(), cm.get_camera_location())
    def along(): return cm.get_camera_rotation().get_forward_vector().dot(f.get_actor_forward_vector())
    # in a turn the camera lags: the fighter swings across the view and comes back (done first and quickly: the gate
    # course begins 170 m ahead of the start, and bouncing about in it would spoil the measurement)
    clear(); f.respawn(); yield from wait(0.6); n0 = f.collisions
    pc.set_scripted_pad(V2(0, 0), V2(1, 0), 0.0, 0.0, False); yield from wait(0.6)
    lag = along(); clear(); yield from wait(1.1)
    back = along(); bumped = f.collisions - n0
    clear(); f.respawn(); yield from wait(1.2)
    c0 = cam_local(); vt = pc.get_view_target() == f; look = along()
    f.zoom_camera(3.0); yield from wait(1.5); c1 = cam_local(); f.zoom_camera(-3.0); yield from wait(1.0)
    ok = vt and c0.x < -500 and c0.z > 100 and abs(c0.y) < 60 and look > 0.97 and c1.x < c0.x - 300 and lag < 0.995 and back > 0.995 and bumped == 0
    step_result("camera", ok, view_target_is_fighter=bool(vt), behind_cm=round(-c0.x), above_cm=round(c0.z), side_cm=round(c0.y), looks_along_nose=round(look, 3), zoomed_out_behind_cm=round(-c1.x),
                lag_in_turn=round(lag, 4), settles=round(back, 4), collisions=bumped)

# ---------------------------------------------------------------- weapons
def lead(t):
    f = G["f"]; l = f.get_actor_location(); p = t.get_actor_location(); rel = t.get_velocity() - f.get_velocity(); bs = f.get_editor_property("bolt_speed")
    for _ in range(3): p = t.get_actor_location() + rel * ((p - l).length() / bs)
    return p
def step_cannon(n=3):
    f, ar = G["f"], G["ar"]; done = []
    for k in range(n):
        clear(); yield from until_alive()
        l = f.get_actor_location(); fw = f.get_actor_forward_vector()
        cands = [t for t in ar.get_targets() if t.kind == unreal.SSTargetKind.ASTEROID and 300 <= t.get_radius() <= 1300 and 15000 < (t.get_actor_location() - l).length() < 140000 and sight(t)]
        if not cands: done.append({"ok": False, "why": "no asteroid in sight"}); break
        t = min(cands, key=lambda c: (c.get_actor_location() - l).length() * (2.0 - fw.dot((c.get_actor_location() - l).normal())))
        name = t.get_actor_label(); rad = t.get_radius(); d0 = (t.get_actor_location() - l).length(); s0, h0 = f.shots_fired, f.shots_hit; t0 = now(); st = "timeout"
        while now() - t0 < 40.0:
            if not alive(t): st = "destroyed"; break
            if f.is_destroyed(): st = "fighter destroyed"; break
            d = (t.get_actor_location() - f.get_actor_location()).length()
            err = aim_error(lead(t)); off = math.hypot(*err)
            # close in, then hold off and shoot; break away when too close
            want = 0.75 if d > 60000 else 0.35 if d > 22000 else 0.0
            fly_at(lead(t), hold_throttle(want), fire=(off < max(0.8, math.degrees(math.atan2(rad * 0.6, d))) and d < 110000), target=t)
            yield
        clear()
        done.append({"ok": st == "destroyed", "target": name, "radius": round(rad), "from_m": round(d0 / 100), "seconds": round(now() - t0, 1), "shots": f.shots_fired - s0, "hits": f.shots_hit - h0, "end": st})
        # turn away from the debris before the next one
        t1 = now(); away = f.get_actor_location() + f.get_actor_right_vector() * 50000 + f.get_actor_up_vector() * 20000
        while now() - t1 < 2.0: fly_at(away, hold_throttle(0.6)); yield
    clear()
    step_result("cannon", len(done) == n and all(d["ok"] for d in done), kills=done)
def step_missile(n=2):
    f, ar = G["f"], G["ar"]; done = []
    for k in range(n):
        clear(); yield from until_alive()
        l = f.get_actor_location()
        drones = [t for t in ar.get_targets() if t.kind == unreal.SSTargetKind.DRONE]
        if not drones: done.append({"ok": False, "why": "no drone"}); break
        t = min(drones, key=lambda c: (c.get_actor_location() - l).length())
        name = t.get_actor_label(); d0 = (t.get_actor_location() - l).length(); m0 = f.missiles_fired; t0 = now(); st = "timeout"; locked_at = None; last = -9.0
        while now() - t0 < 70.0:
            if not alive(t): st = "destroyed"; break
            if f.is_destroyed(): st = "fighter destroyed"; break
            p = t.get_actor_location(); d = (p - f.get_actor_location()).length()
            off = fly_at(p, hold_throttle(0.9 if d > 120000 else 0.55 if d > 40000 else 0.2), boost=d > 200000, target=t)
            lk = f.get_locked_target()
            if lk != t and off < 8.0 and d < 440000 and now() - last > 0.4: f.cycle_target(); last = now()        # (Tab until it is the one)
            if lk == t and locked_at is None: locked_at = now() - t0
            if lk == t and off < 9.0 and d < 300000 and sight(t) and now() - last > 1.6 and f.get_missiles_ready() > 0:
                G["pc"].set_scripted_pad(V2(0, 0), V2(0, 0), 1.0, 0.0, False); last = now()                       # LT
            yield
        clear()
        done.append({"ok": st == "destroyed", "target": name, "from_m": round(d0 / 100), "seconds": round(now() - t0, 1), "locked_after_s": None if locked_at is None else round(locked_at, 1),
                     "missiles": f.missiles_fired - m0, "end": st})
        yield from wait(1.0)
    step_result("missile", len(done) == n and all(d["ok"] for d in done), kills=done)

# ---------------------------------------------------------------- the edge of the area, collisions, a tour
def step_edge():
    f, ar = G["f"], G["ar"]; clear(); yield from until_alive()
    c = ar.get_actor_location(); l = f.get_actor_location(); half = ar.get_editor_property("half_extent")
    # the nearest face, straight out through it
    d = l - c; axis = max(range(3), key=lambda i: abs((d.x, d.y, d.z)[i])); sgn = 1.0 if (d.x, d.y, d.z)[axis] >= 0 else -1.0
    out = [l.x, l.y, l.z]; out[axis] = (c.x, c.y, c.z)[axis] + sgn * (half + 200000.0); out = V(*out)
    t0 = now(); tb0 = f.turn_backs; maxout = 0.0; st = "never left"; t_ret = None
    while now() - t0 < 90.0:
        o = ar.distance_outside(f.get_actor_location()); maxout = max(maxout, o)
        if f.turn_backs > tb0:
            if t_ret is None: t_ret = now()
            # hands off: the fighter must come back by itself (the player keeps pushing outward)
            fly_at(out, 1.0)
            if not f.is_returning() and ar.is_inside(f.get_actor_location(), 0.0): st = "back inside"; break
            st = "outside, turning back"
        else: fly_at(out, 1.0, boost=True)
        yield
    clear()
    step_result("edge", st == "back inside" and maxout > 0, end=st, farthest_outside_m=round(maxout / 100), seconds_to_return=None if t_ret is None else round(now() - t_ret, 1), total_s=round(now() - t0, 1))
def step_collide():
    f, w_ = G["f"], G["w"]; clear(); yield from until_alive()
    yield from wait(3.2)                           # (launch protection over)
    l = f.get_actor_location()
    rocks = [a for a in GS.get_all_actors_of_class(w_, unreal.StaticMeshActor) if a.get_actor_label().startswith("Asteroid_")]
    def r_of(a): o, e = a.get_actor_bounds(False); return o, max(e.x, e.y, e.z)
    rocks = [a for a in rocks if 3000 < r_of(a)[1] and sight(a)]
    if not rocks: step_result("collide", False, why="no big asteroid in sight"); return
    a = min(rocks, key=lambda q: (q.get_actor_location() - l).length()); o, rr = r_of(a)
    c0, h0, r0 = f.collisions, f.get_hull(), f.respawns; t0 = now(); st = "timeout"; speed_hit = 0.0
    while now() - t0 < 120.0:
        d = (o - f.get_actor_location()).length()
        if f.collisions > c0: st = "hit"; break
        speed_hit = f.get_speed()
        fly_at(o, hold_throttle(0.9 if d > rr + 60000 else 0.4), boost=d > rr + 150000, target=a)
        yield
    clear(); hull_after = f.get_hull(); t1 = now(); moved = 0.0; p1 = f.get_actor_location(); hits_after = 0
    # afterwards: hands off for 3 s; it must be flying free (not grinding along the rock or stuck inside it)
    while now() - t1 < 3.0: yield
    moved = (f.get_actor_location() - p1).length(); hits_after = f.collisions - c0
    h = unreal.SystemLibrary.line_trace_single(w_, f.get_actor_location(), f.get_actor_location() + V(0, 0, 1), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [f], unreal.DrawDebugTrace.NONE, True)
    ok = st == "hit" and (hull_after < h0 or f.respawns > r0) and moved > 2000 and hits_after <= 4
    step_result("collide", ok, target=a.get_actor_label(), rock_radius_m=round(rr / 100), end=st, speed_at_hit=round(speed_hit), hull_before=round(h0), hull_after=round(hull_after), destroyed=f.respawns > r0,
                moved_after_cm=round(moved), collisions=hits_after, seconds=round(t1 - t0, 1))
def step_tour(sec=20.0):
    f, ar = G["f"], G["ar"]; clear(); yield from until_alive(); c = ar.get_actor_location(); t0 = now(); c0 = f.collisions; n0 = len(R["frames"])
    # get to a ring round the station, then follow it
    while now() - t0 < sec + 40.0:
        l = f.get_actor_location(); d = l - c; ang = math.atan2(d.y, d.x) + 0.35
        p = c + V(math.cos(ang) * 80000.0, math.sin(ang) * 80000.0, 30000.0 * math.sin(ang * 2.0))
        fly_at(p, hold_throttle(0.8))
        if now() - t0 > sec and (l - c).length() < 110000: break
        yield
    clear(); fr = sorted(R["frames"][n0:])
    step_result("tour", f.collisions - c0 <= 1 and len(fr) > 30, seconds=round(now() - t0, 1), collisions=f.collisions - c0, frame_ms_median=round(fr[len(fr) // 2] * 1000, 1) if fr else None,
                frame_ms_p95=round(fr[int(len(fr) * 0.95)] * 1000, 1) if fr else None)

STEPS = {"input": step_input, "agile": step_agile, "camera": step_camera, "cannon": step_cannon, "missile": step_missile, "edge": step_edge, "collide": step_collide, "tour": step_tour}
def run():
    yield from wait(1.0)
    for s in PLAN:
        name, _, arg = s.partition(":")
        yield from (STEPS[name](float(arg) if name == "tour" else int(arg)) if arg else STEPS[name]())
        G["f"].respawn() if name in ("edge", "collide") else None
        yield from wait(0.5)
def finish(err=None):
    unreal.unregister_slate_post_tick_callback(G["h"])
    try:
        f, ar = G["f"], G["ar"]; fr = sorted(R["frames"])
        R.update({"error": err, "frame_ms_median": round(fr[len(fr) // 2] * 1000, 1) if fr else None, "shots": f.shots_fired, "hits": f.shots_hit, "missiles": f.missiles_fired, "collisions": f.collisions,
                  "respawns": f.respawns, "turn_backs": f.turn_backs, "score": ar.score, "asteroids_destroyed": ar.asteroids_destroyed, "drones_destroyed": ar.drones_destroyed,
                  "targets_left": {"asteroids": ar.count_targets(unreal.SSTargetKind.ASTEROID), "drones": ar.count_targets(unreal.SSTargetKind.DRONE), "containers": ar.count_targets(unreal.SSTargetKind.CONTAINER)}})
        G["pc"].clear_scripted(); G["pc"].set_scripted_only(False)
    except Exception as e: R["error"] = (err or "") + " / " + str(e)
    del R["frames"]
    os.makedirs(OUT, exist_ok=True); json.dump(R, open(os.path.join(OUT, f"flight_{TAG}.json"), "w"), indent=1)
    ok = not R.get("error") and len(R["steps"]) == len(PLAN) and all(s["ok"] for s in R["steps"])
    unreal.log(f"SSFLIGHT done | {TAG} | {'ok' if ok else 'FAILED'} | " + " | ".join(f"{s['step']} {'ok' if s['ok'] else 'FAILED'}" for s in R["steps"]) + f" | frame {R.get('frame_ms_median')} ms | {R.get('error') or ''}")
    G.clear()
def tick(dt):
    try:
        if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is None: finish("PIE ended"); return
        G["dt"] = dt; R["frames"].append(dt)
        next(G["gen"])
    except StopIteration: finish()
    except Exception as e:
        import traceback
        unreal.log_error("SSFLIGHT error: " + str(e) + traceback.format_exc()); finish(str(e))
G["gen"] = run()
G["h"] = unreal.register_slate_post_tick_callback(tick)
print("flight test armed:", PLAN, TAG)
