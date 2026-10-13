"""starship_level demo reel: the pilot and the recorder. Flies SS_Fighter through the player controller's scripted
keyboard and mouse (W / S, A / D, Shift, the mouse for the nose, both buttons: the same code as the real devices), moves
the camera (the chase camera, turned round the fighter for the opening and the end, and two fixed fly-by cameras) and
records the flight for the overlay (pipeline/blender_numpy/ss_reel_overlay.py).
  render    (default) arm it right before 806: it waits for the Movie Render Queue's world and LS_SS_Showcase, holds the
            fighter at the start through the warm-up and starts with frame 0, where it has the arena spawn every
            target again from its seed. From there the render steps the game at a fixed rate, so the same flight
            comes out of the preview and of the final render.
  rehearse  the PIE session that is running now, in real time (a quick look at what the pilot does; the HUD is on)
The flight (30 s): the engines light at the start, the six ring tunnels of the gate course (the last two seen from a
fly-by camera, with a roll), a hard turn back into the asteroid field beside them with the cannons, missiles and
cannons on the target drones, a pass between the station's hub and its pylons past the second fly-by camera, and out.
Writes SourceArt/starship/cine_render.json (rehearse: cine_rehearsal.json) and logs "SSREEL saved" (or "SSREEL failed").
Keeps its namespace (tick callback); a pilot left armed by an earlier run is dropped. Args: [render|rehearse] [seconds]"""
import unreal, sys, json, math, os
__keep__ = True
MODE = sys.argv[1] if len(sys.argv) > 1 else "render"
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
FPS = 30
OUT = "E:\\code\\claude-ue5\\claude_ue5\\SourceArt\\starship\\" + ("cine_render.json" if MODE == "render" else "cine_rehearsal.json")
V = unreal.Vector; V2 = unreal.Vector2D; Rot = unreal.Rotator; ML = unreal.MathLibrary; GS = unreal.GameplayStatics; SL = unreal.SystemLibrary
TQ = unreal.TraceTypeQuery.ECC_VISIBILITY; NODRAW = unreal.DrawDebugTrace.NONE
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
G = {}; IN = {}
S = {"rows": {}, "events": [], "segs": [], "saved": False, "view": "chase", "seg": "", "note": {}}
if getattr(unreal, "_ss_reel", None) is not None:
    try: unreal.unregister_slate_post_tick_callback(unreal._ss_reel)
    except Exception: pass
# ---- the level (800 / 801): the start corner, the gate course hung on it, the first asteroid field
START = V(-150000.0, -60000.0, 20000.0)
TO = (V(0, 0, 0) - START).normal(); SIDE = TO.cross(V(0, 0, 1)).normal(); UP = SIDE.cross(TO).normal()
def gate(i):
    return START + TO * (22000.0 + i * 13000.0) + SIDE * (math.sin(i * 1.3) * 7000.0) + UP * (math.cos(i * 0.9) * 5000.0 + 2000.0)
GATES = [gate(i) for i in range(7)]                 # (the seventh is where the sixth points)
FIELD = START + TO * 52000.0 + SIDE * 24000.0
MUZZLE = 385.0                                      # the cannons' distance from the nose line (800)
T_OPEN, T_CANNON, T_STATION = 0.9, 13.6, 21.6      # the engines light / the cannon run ends / the drones end at these times (s)

def T(): return G["t"]
def loc(): return G["f"].get_actor_location()
def vel(): return G["f"].get_velocity()
def event(kind, **kw):
    S["events"].append({"t": round(T(), 3), "frame": G["frame"], "kind": kind, **kw})
    unreal.log("SSREEL %6.2f s  %s %s" % (T(), kind, json.dumps(kw)[:200]))
def seg(name):
    S["seg"] = name; S["segs"].append({"name": name, "t": round(max(T(), 0.0), 3), "frame": max(G["frame"], 0)})
    unreal.log("SSREEL %6.2f s  == %s" % (T(), name))
def alive(t):
    try: return t is not None and SL.is_valid(t) and t.is_alive()
    except Exception: return False
def smooth(x): x = min(1.0, max(0.0, x)); return x * x * (3.0 - 2.0 * x)
def lerp(a, b, u): return a + (b - a) * u

# ---------------------------------------------------------------- the hands: mouse and keys
def local_dir(p):
    f = G["f"]; return ML.inverse_transform_direction(f.get_actor_transform(), (p - f.get_actor_location()).normal())
def aim_error(p):
    d = local_dir(p); return math.degrees(math.atan2(d.y, d.x)), math.degrees(math.atan2(d.z, math.hypot(d.x, d.y)))
def steer(p, gain=0.8, cap=None, hand=90.0):
    """the mouse: moves the aim point to `gain` x the angle from the nose to p (the fighter closes it at AimGain x the
    gap). `hand` = the most the mouse is moved in a tick, counts. The movement is given in counts, not as a rate: the
    render's ticks are not all the same length. Returns the angle from the nose to p."""
    yaw, pitch = aim_error(p)
    wx, wy = yaw * gain, pitch * gain; m = math.hypot(wx, wy); cap = cap or G["max_aim"] * 0.95
    if m > cap: wx, wy = wx * cap / m, wy * cap / m
    a = G["f"].get_aim(); k = 0.8 / G["sens"]
    cx, cy = (wx - a.x) * k, (wy - a.y) * k; m = math.hypot(cx, cy)
    if m > hand: cx, cy = cx * hand / m, cy * hand / m
    IN["mouse"] = (cx, cy)
    return math.hypot(yaw, pitch)
def throttle(want):
    t = G["f"].get_throttle()
    if abs(t - want) >= 0.03: IN["w" if t < want else "s"] = True
def level(strength=1.0, up=None):
    """A / D in short taps (each a whole frame long): rolls the fighter until `up` (the world's up) is over its canopy"""
    if G["frame"] != G.get("roll_frame"):
        G["roll_frame"] = G["frame"]; G["roll_key"] = None
        f = G["f"]; u = ML.inverse_transform_direction(f.get_actor_transform(), up or V(0, 0, 1))
        err = math.degrees(math.atan2(u.y, u.z)) if math.hypot(u.y, u.z) >= 0.35 else 0.0
        if abs(err) >= 5.0:
            G["roll_acc"] = G.get("roll_acc", 0.0) + min(1.0, abs(err) / 70.0) * strength
            if G["roll_acc"] >= 1.0: G["roll_acc"] -= 1.0; G["roll_key"] = "d" if err > 0 else "a"
    if G.get("roll_key"): IN[G["roll_key"]] = True
def trace(a, b, radius=0.0):
    f = G["f"]
    h = SL.sphere_trace_single(G["w"], a, b, radius, TQ, True, [f], NODRAW, True) if radius > 0 else SL.line_trace_single(G["w"], a, b, TQ, True, [f], NODRAW, True)
    t = h.to_tuple() if h else None
    return t if t and t[0] else None
def sight(target):
    t = trace(loc(), target.get_actor_location()); return t is None or t[9] == target
def avoid(p, target=None, look=1.5):
    """what is in the way (other than `target`) is flown round: the point to steer at, and whether something was"""
    l = loc(); v = vel(); sp = v.length()
    if sp < 500.0: return p, False
    # along the flight, along the nose (where the flight is swinging to) and toward the point steered at
    vn = v.normal(); reach = sp * look + 2500.0; t = None
    for d in (vn, G["f"].get_actor_forward_vector(), (p - l).normal()):
        h = trace(l, l + d * min(reach, max((p - l).length(), 4000.0)) if d is not vn else l + d * reach, 520.0)
        if h is not None and h[9] != target and (t is None or h[3] < t[3]): t = h
    if t is None: return p, False
    n = t[7] if t[7].length() > 0.5 else (l - t[5]).normal()
    side = n - vn * n.dot(vn)
    if side.length() < 0.05: side = G["f"].get_actor_up_vector()
    if t[3] < sp * 0.8: IN["s"] = True; IN["w"] = False
    return l + (vn * 0.6 + side.normal()).normal() * 30000.0, True
class Path:
    """a polyline flown by steering at the point `look` cm ahead of where the fighter is along it"""
    def __init__(self, pts):
        self.p = pts; self.i = 0; self.cum = [0.0]
        for a, b in zip(pts, pts[1:]): self.cum.append(self.cum[-1] + (b - a).length())
    def arc(self):
        l = loc()
        while True:
            a, b = self.p[self.i], self.p[self.i + 1]; L = self.cum[self.i + 1] - self.cum[self.i]; s = (l - a).dot((b - a).normal())
            if s > L and self.i < len(self.p) - 2: self.i += 1; continue
            return self.cum[self.i] + max(0.0, s)
    def at(self, arc):
        i = 0
        while i < len(self.p) - 2 and arc > self.cum[i + 1]: i += 1
        a, b = self.p[i], self.p[i + 1]; return a + (b - a).normal() * (arc - self.cum[i])
    def ahead(self, look): return self.at(self.arc() + look)
    def arc_of(self, k): return self.cum[k]
    def arc_near(self, q): return self.cum[min(range(len(self.p)), key=lambda i: (self.p[i] - q).length())]
def spline(c, n=14):
    """a smooth curve through the points (Catmull-Rom), n samples a span"""
    out = []
    for i in range(len(c) - 1):
        p0, p1 = c[i], c[i + 1]; m0 = (p1 - c[i - 1]) * 0.5 if i > 0 else p1 - p0; m1 = (c[i + 2] - p0) * 0.5 if i + 2 < len(c) else p1 - p0
        for k in range(n):
            s = k / n; s2 = s * s; s3 = s2 * s
            out.append(p0 * (2 * s3 - 3 * s2 + 1) + m0 * (s3 - 2 * s2 + s) + p1 * (-2 * s3 + 3 * s2) + m1 * (s3 - s2))
    return out + [c[-1]]
def lead(t):
    f = G["f"]; l = loc(); p = t.get_actor_location(); rel = t.get_velocity() - f.get_velocity()
    for _ in range(3): p = t.get_actor_location() + rel * ((p - l).length() / G["bolt"])
    return p
def zoom(cam, wide=58.0, tele=9.0, frame=1700.0):
    """the field of view of a fly-by camera's zoom lens: it holds the fighter at about the same size as it comes"""
    return max(tele, min(wide, 2.0 * math.degrees(math.atan(frame / max((loc() - cam).length(), 1.0)))))
def view(name, cut=False):
    if S["view"] != name: S["view"] = name; event("view", view=name, cut=cut)

# ---------------------------------------------------------------- the flight
def course_distance(p):
    """how far p is from the centre line of the gate course"""
    best = 1e9
    for a, b in zip(GATES, GATES[1:]):
        ab = b - a; s = max(0.0, min(1.0, (p - a).dot(ab) / ab.dot(ab))); best = min(best, (p - (a + ab * s)).length())
    return best
def pick_rock(skip):
    f, ar = G["f"], G["ar"]; l = loc(); fw = f.get_actor_forward_vector(); best = None; bs = 1e9
    for t in ar.get_targets():
        if t in skip or t.kind != unreal.SSTargetKind.ASTEROID: continue
        rad = t.get_radius()
        if not 480.0 <= rad <= 1800.0: continue
        p = t.get_actor_location(); d = (p - l).length()
        if not 9000.0 < d < 70000.0 or (p - FIELD).length() > 26000.0 or course_distance(p) < 14000.0: continue        # (not one tucked in beside the tunnels)
        ang = math.degrees(math.acos(max(-1.0, min(1.0, fw.dot((p - l).normal())))))
        if ang > 75.0: continue
        s = ang * 1.1 + d / 1100.0 - rad / 45.0
        if s < bs and sight(t): bs = s; best = t
    return best
def pick_drone(skip):
    f, ar = G["f"], G["ar"]; l = loc(); fw = f.get_actor_forward_vector(); best = None; bs = 1e9
    for t in G["drones"]:
        if t in skip or not alive(t): continue
        p = t.get_actor_location(); d = (p - l).length()
        if d < 25000.0 or p.length() < 95000.0: continue                # (not one that is right on top of us or in among the station)
        ang = math.degrees(math.acos(max(-1.0, min(1.0, fw.dot((p - l).normal())))))
        s = d / 1000.0 + ang * 0.9 + p.length() / 2500.0                # near, ahead, and toward the station (where the flight ends)
        if course_distance(p) < 16000.0: s += 60.0                      # (not one that is in among the tunnels)
        if s < bs and (s + 50.0 < bs or sight(t)): bs = s if sight(t) else s + 50.0; best = t
    return best
def run():
    f, pc, ar = G["f"], G["pc"], G["ar"]
    # ---- the start: the fighter stands (S through the warm-up), the camera off its nose; the engines light
    seg("open"); S["view"] = "orbit"
    f.set_chase_camera(Rot(roll=0, pitch=-10, yaw=152), 1000.0, 40.0); f.snap_camera()
    while T() < T_OPEN:
        IN["s"] = f.get_throttle() > 0.001
        f.set_chase_camera(Rot(roll=0, pitch=-10, yaw=lerp(152.0, 138.0, max(0.0, T()) / T_OPEN)), 1000.0, 40.0)
        yield
    event("engines")
    # ---- the gate course: six ring tunnels, each pointing at the next (a bent pipe, 59 m inside radius). The camera
    # comes round behind the fighter; the last two tunnels are seen from a fly-by camera past their end, with a roll
    d0 = (GATES[1] - GATES[0]).normal(); d5 = (GATES[6] - GATES[5]).normal()         # (the fighter starts on the first tunnel's axis)
    path = Path(spline([loc(), GATES[0] - d0 * 10000.0] + GATES[:6] + [GATES[5] + d5 * 14000.0, GATES[5] + d5 * 40000.0]))
    ag = [path.arc_near(g) for g in GATES[:6]]
    cam = GATES[5] + d5 * 8600.0 + d5.cross(V(0, 0, 1)).normal() * -1500.0 + V(0, 0, 420.0)
    watch = 0; roll_until = -1.0; named = False; passed = 0
    while path.arc() < ag[5] + 24000.0:
        a = path.arc(); u = smooth((T() - T_OPEN) / 1.7)
        if watch == 0: f.set_chase_camera(Rot(roll=0, pitch=lerp(-10.0, 0.0, u), yaw=lerp(138.0, 0.0, u)), lerp(1000.0, 1150.0, u), lerp(40.0, 330.0, u))
        if u >= 1.0 and watch == 0: view("chase")
        if not named and a > ag[0] - 9000.0: named = True; seg("gates")
        while passed < 6 and a > ag[passed]:
            g = GATES[passed]; ax = (GATES[passed + 1] - g).normal(); r = loc() - g
            event("gate", n=passed, off_axis_m=round((r - ax * r.dot(ax)).length() / 100.0, 1), speed=round(f.get_speed() / 100.0)); passed += 1
        steer(path.ahead(4800.0), 0.85); IN["w"] = True; IN["shift"] = a > ag[4]
        if watch == 0 and a > ag[3] + 4500.0: watch = 1; view("watch", True); roll_until = T() + 2.4
        if watch == 1: f.set_watch_camera(True, cam, zoom(cam), 0.03)
        if watch == 1 and (loc() - cam).dot(d5) > f.get_speed() * 0.3:
            watch = 2; f.set_chase_camera(Rot(roll=0, pitch=0, yaw=0), 1150.0, 330.0); f.set_watch_camera(False, cam); f.snap_camera(); view("chase", True)
        if T() < roll_until: IN["d"] = True
        elif watch != 1: level()
        yield
    if watch == 1: f.set_watch_camera(False, cam); f.snap_camera()
    view("chase"); f.set_chase_camera(Rot(roll=0, pitch=0, yaw=0), 1150.0, 330.0)
    # ---- cannons: a hard turn back into the asteroid field beside the gates
    seg("cannons"); skip = set(); n0 = ar.asteroids_destroyed
    while T() < T_CANNON:
        t = pick_rock(skip)
        if t is None:
            q, _ = avoid(FIELD); steer(q, 0.8); throttle(0.6); level(); yield; continue
        t0 = T(); s0 = f.shots_fired; rad = t.get_radius(); held = 0.0; h0 = f.shots_hit; sh = f.shots_fired
        while T() < T_CANNON and alive(t) and T() - t0 < 2.4 and held < 0.5 and f.shots_fired - sh < 9:
            d = (t.get_actor_location() - loc()).length(); aim = lead(t)
            if f.shots_hit != h0: h0 = f.shots_hit; sh = f.shots_fired          # (nine bolts in a row past it: another target)
            # the cannons are 3.85 m either side of the nose and cross 900 m out: at a small rock close by the nose is
            # put off to one side, so that one cannon's line goes through its middle
            gap = MUZZLE * (1.0 - d / G["conv"])
            if rad < gap + 200.0: aim = aim + f.get_actor_right_vector() * gap
            q, blocked = avoid(aim, None if d < rad + 4500.0 + f.get_speed() * 0.4 else t)
            off = steer(q, 0.85)
            held = held + G["dt"] if blocked else 0.0                    # (something in the way for half a second: another target)
            IN["lmb"] = (not blocked) and d < 90000.0 and off < max(0.55, math.degrees(math.atan2(rad * 0.7, d)))
            throttle(0.6 if d > 30000.0 else 0.4); level(0.6)
            yield
        if alive(t): skip.add(t)
        else: event("kill", what="asteroid", radius_m=round(rad / 100.0, 1), shots=f.shots_fired - s0, seconds=round(T() - t0, 2))
    S["note"]["asteroids_in_cannon_run"] = ar.asteroids_destroyed - n0
    # ---- missiles (and cannons) on the target drones
    seg("missiles"); skip = set(); n0 = ar.drones_destroyed
    while T() < T_STATION:
        t = pick_drone(skip)
        if t is None:
            q, _ = avoid(V(0, 0, 60000.0)); steer(q, 0.6); throttle(0.8); level(); yield; continue
        t0 = T(); m0 = f.missiles_fired; last = -9.0; cyc = -9.0; press = -1.0; name = str(t.type_name)
        event("target", name=name, range_m=round((t.get_actor_location() - loc()).length() / 100.0))
        while T() < T_STATION and alive(t) and T() - t0 < 6.5:
            p = t.get_actor_location(); d = (p - loc()).length(); lk = f.get_locked_target(); nose = math.hypot(*aim_error(p))
            q, blocked = avoid(f.get_lead_point() if lk == t and d < 150000.0 else p, t)
            off = steer(q, 0.85)
            if lk != t and nose < 9.0 and T() - cyc > 0.35: f.cycle_target(); cyc = T()             # (Tab until it is the one)
            if lk == t and nose < 9.0 and d < 230000.0 and f.get_missiles_ready() > 0 and T() - last > (1.3 if f.missiles_fired - m0 < 2 else 9.0) and not blocked and sight(t):
                press = T() + 0.1; last = T(); event("missile", name=name, range_m=round(d / 100.0))
            IN["rmb"] = T() < press
            IN["lmb"] = lk == t and (not blocked) and off < 0.8 and d < 120000.0
            IN["shift"] = d > 120000.0
            throttle(1.0 if d > 70000.0 else 0.5); level(0.7)
            yield
        if alive(t): skip.add(t)
        else: event("kill", what="drone", name=name, missiles=f.missiles_fired - m0, seconds=round(T() - t0, 2))
    S["note"]["drones_in_missile_run"] = ar.drones_destroyed - n0
    # ---- the station: between the hub and the pylons, past the second fly-by camera, then out toward the planet
    seg("station"); l = loc(); best = None
    for k in range(6):
        th = math.radians(45.0 + 60.0 * k); n = V(math.cos(th), math.sin(th), 0.0)
        for s in (1.0, -1.0):
            u = V(-math.sin(th), math.cos(th), 0.0) * s; Q = n * 20500.0 + V(0, 0, 6500.0); E = Q - u * 90000.0
            w_ = (E - l); hit = min(((l + w_ * (i / 12.0)) * V(1, 1, 0)).length() for i in range(13)) < 75000.0          # (the way to the entry must not cross the station)
            cost = w_.length() + (200000.0 if hit else 0.0) + 40000.0 * (1.0 - f.get_actor_forward_vector().dot(w_.normal()))
            if best is None or cost < best[0]: best = (cost, Q, u, n)
    _, Q, u, n = best
    path = Path([l, Q - u * 90000.0, Q - u * 30000.0, Q + u * 45000.0, Q + u * 400000.0])
    cam = Q + n * 15000.0 + V(0, 0, 1200.0)                         # (150 m outside the fighter's way: it crosses the view with the hub behind it)
    event("pass", entry_m=round((Q - u * 90000.0 - l).length() / 100.0))
    watch = 0; t_out = None
    while True:
        a = path.arc(); sp = f.get_speed(); along = (loc() - Q).dot(u)
        q = path.ahead(9000.0)
        if a < path.arc_of(1) - 5000.0 or along > 50000.0: q, _ = avoid(q)
        steer(q, 0.75); IN["w"] = True; IN["shift"] = True
        if watch == 0 and along > -sp * 1.25: watch = 1; view("watch", True)
        if watch == 1: f.set_watch_camera(True, cam, zoom(cam, 30.0, 10.0, 3200.0), 0.02)
        if watch == 1 and along > sp * 0.85:
            watch = 2; t_out = T(); f.set_watch_camera(False, cam); f.set_chase_camera(Rot(roll=0, pitch=0, yaw=0), 1150.0, 330.0); f.snap_camera(); view("chase", True)
        if watch == 2:
            # the end: the camera comes round the fighter to look back along its wake at the station
            if S["seg"] != "end" and T() - t_out > 0.35: seg("end"); S["view"] = "orbit"; event("view", view="orbit", cut=False)
            k = smooth((T() - t_out - 0.35) / 2.0)
            # (under afterburner the arm's lag holds the camera 6.5 m back along the flight: in front of the fighter that is 6.5 m nearer)
            f.set_chase_camera(Rot(roll=0, pitch=lerp(0.0, -8.0, k), yaw=lerp(0.0, -150.0, k)), lerp(1150.0, 1650.0, k), lerp(330.0, 90.0, k))
        level()
        yield

# ---------------------------------------------------------------- the recorder
def r3(v): return [round(v.x, 1), round(v.y, 1), round(v.z, 1)]
def rr(r): return [round(r.pitch, 3), round(r.yaw, 3), round(r.roll, 3)]
def sample():
    f, pc, ar = G["f"], G["pc"], G["ar"]; cm = pc.player_camera_manager; lk = f.get_locked_target(); a = f.get_aim(); tr = f.get_turn_rates()
    row = {"t": round(T(), 4), "p": r3(f.get_actor_location()), "r": rr(f.get_actor_rotation()), "sp": round(f.get_speed()), "th": round(f.get_throttle(), 3), "bo": bool(f.is_boosting()),
           "hull": round(f.get_hull(), 1), "mis": f.get_missiles_ready(), "rel": round(f.get_missile_reload_left(), 2), "sf": f.shots_fired, "sh": f.shots_hit, "mf": f.missiles_fired,
           "sc": ar.score, "ad": ar.asteroids_destroyed, "dd": ar.drones_destroyed, "col": f.collisions, "dead": bool(f.is_destroyed()),
           "cp": r3(cm.get_camera_location()), "cr": rr(cm.get_camera_rotation()), "fov": round(cm.get_fov_angle(), 2), "aim": [round(a.x, 2), round(a.y, 2)], "rate": [round(tr.x, 1), round(tr.y, 1)],
           "view": S["view"], "seg": S["seg"], "in": [int(bool(IN.get(k))) for k in ("w", "s", "a", "d", "shift", "lmb", "rmb")] + [round(IN.get("mouse", (0, 0))[0], 1), round(IN.get("mouse", (0, 0))[1], 1)],
           "lock": None, "dr": [r3(t.get_actor_location()) for t in G["drones"] if alive(t)]}
    if alive(lk):
        row["lock"] = {"p": r3(lk.get_actor_location()), "rad": round(lk.get_radius()), "name": str(lk.type_name) if lk.kind == unreal.SSTargetKind.DRONE else "ASTEROID", "lead": r3(f.get_lead_point()),
                       "hp": round(lk.health / max(lk.max_health, 1.0), 2)}
    return row
def save(why=None):
    if S["saved"]: return
    S["saved"] = True
    rows = []
    for k in sorted(S["rows"]):
        lst = S["rows"][k]; rows.append(dict(lst[len(lst) // 2], frame=k))                     # (the middle sub-sample of each frame)
    last = rows[-1] if rows else {}
    out = {"fps": FPS, "mode": MODE, "rows": rows, "events": S["events"], "segs": S["segs"], "note": S["note"], "const": G.get("const", {}), "error": why}
    os.makedirs(os.path.dirname(OUT), exist_ok=True); json.dump(out, open(OUT, "w"), separators=(",", ":"))
    kills = [e for e in S["events"] if e["kind"] == "kill"]
    msg = "%d frames | %d asteroids, %d drones destroyed | %d shots, %d hits, %d missiles | %d collisions | hull %s | %s" % (
        len(rows), sum(1 for e in kills if e["what"] == "asteroid"), sum(1 for e in kills if e["what"] == "drone"), last.get("sf", 0), last.get("sh", 0), last.get("mf", 0), last.get("col", 0),
        last.get("hull"), " ".join("%s@%.1f" % (s["name"], s["t"]) for s in S["segs"]))
    (unreal.log_error if why else unreal.log)(("SSREEL failed: %s | " % why if why else "SSREEL saved ") + msg)
def stop(why=None):
    unreal.unregister_slate_post_tick_callback(unreal._ss_reel); unreal._ss_reel = None
    try: save(why)
    finally:
        try:
            if G.get("w") is not None and ues.get_game_world() is not None:
                G["pc"].clear_scripted(); G["pc"].set_scripted_only(False); G["f"].set_watch_camera(False, V(0, 0, 0)); G["f"].set_chase_camera(Rot(roll=0, pitch=0, yaw=0), 1150.0, 330.0)
        except Exception: pass
        G.clear()
def body():
    w = ues.get_game_world()
    if "f" not in G:
        if w is None: return
        pc = GS.get_player_controller(w, 0); f = pc.get_controlled_pawn() if pc else None
        if not isinstance(f, unreal.SSFighter): return
        player = None
        if MODE == "render":
            lsa = GS.get_all_actors_of_class(w, unreal.LevelSequenceActor)
            if not lsa or lsa[0].get_editor_property("sequence_player") is None: return
            player = lsa[0].get_editor_property("sequence_player")
        ar = f.get_arena()
        G.update({"w": w, "pc": pc, "f": f, "ar": ar, "player": player, "t": -1.0, "frame": -1, "dt": 1.0 / 60.0, "going": False, "w0": GS.get_time_seconds(w) + 1.5, "drones": [], "drones_at": -9.0,
                  "max_aim": f.get_editor_property("max_aim"), "sens": pc.get_editor_property("mouse_sensitivity") * pc.get_editor_property("mouse_scale"), "bolt": f.get_editor_property("bolt_speed"), "conv": f.get_editor_property("convergence")})
        G["const"] = {"max_speed": f.get_editor_property("max_speed"), "boost_speed": f.get_editor_property("boost_speed"), "max_hull": f.get_editor_property("max_hull"),
                      "rails": len(f.get_editor_property("missile_rails")), "convergence": f.get_editor_property("convergence"), "mouse_sensitivity": G["sens"], "max_aim": G["max_aim"],
                      "mouse_rates": [f.get_editor_property("mouse_yaw_rate"), f.get_editor_property("mouse_pitch_rate")], "stick_rates": [f.get_editor_property("yaw_rate"), f.get_editor_property("pitch_rate")]}
        pc.set_scripted_only(True)                 # (the real mouse must not fly the fighter)
        f.relaunch(0.0); G["col"] = 0                # (it stands at the start until the first frame)
        G["gen"] = run()
        unreal.log("SSREEL armed (%s), %.0f s" % (MODE, DUR))
    if w is None: stop(None if G["t"] >= DUR - 0.05 else "the world ended at %.2f s" % G["t"]); return
    if S["saved"]: return
    wt = GS.get_time_seconds(G["w"]); G["dt"] = max(GS.get_world_delta_seconds(G["w"]), 1e-4)
    if MODE == "render":
        sec = unreal.TimeManagementLibrary.conv_qualified_frame_time_to_seconds(G["player"].get_current_time())
        start = not G["going"] and sec > 1e-4
        if not G["going"] and not start: G["w0"] = wt
        G["t"] = wt - G["w0"]; G["frame"] = int(sec * FPS + 1e-3)
    else:
        start = not G["going"] and wt >= G["w0"]
        G["t"] = wt - G["w0"]; G["frame"] = int(math.floor(G["t"] * FPS))
    if start:
        # the first frame: every target is spawned again from the arena's seed and the fighter stands at the start. How
        # long the world ran before the render began differs from run to run (the drones fly meanwhile); from here on
        # the game is stepped at the render's fixed rate, so every render is the same flight
        G["going"] = True; G["ar"].restart(); G["f"].relaunch(0.0); G["col"] = 0; G["drones_at"] = -9.0
    if wt - G["drones_at"] > 0.3:
        G["drones_at"] = wt; G["drones"] = [t for t in G["ar"].get_targets() if t.kind == unreal.SSTargetKind.DRONE]
    IN.clear()
    if G["t"] < DUR + 0.5: next(G["gen"])
    if G["f"].collisions != G["col"]:
        G["col"] = G["f"].collisions; l = loc(); k = min(range(6), key=lambda i: (GATES[i] - l).length())
        event("collision", at=r3(l), gate=k, gate_m=round((GATES[k] - l).length() / 100.0), station_m=round(l.length() / 100.0), hull=round(G["f"].get_hull()))
    pc = G["pc"]
    pc.set_scripted_keys(bool(IN.get("w")), bool(IN.get("s")), bool(IN.get("a")), bool(IN.get("d")), bool(IN.get("shift")))
    pc.add_scripted_mouse_counts(V2(*IN.get("mouse", (0.0, 0.0)))); pc.set_scripted_buttons(bool(IN.get("lmb")), bool(IN.get("rmb")))
    if G["frame"] >= 0 and G["t"] >= 0.0:
        S["rows"].setdefault(G["frame"], []).append(sample())
    if MODE != "render" and G["t"] >= DUR: stop()
    elif MODE == "render" and G["t"] >= DUR + 0.4: save()
def tick(dt):
    try: body()
    except Exception as e:
        import traceback
        unreal.log_error("SSREEL error: " + str(e) + traceback.format_exc()); stop(str(e))
unreal._ss_reel = unreal.register_slate_post_tick_callback(tick)
print("reel pilot armed:", MODE, DUR)
