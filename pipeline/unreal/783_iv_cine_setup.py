"""random_isometric_village_level_Cine (Save As copy of random_isometric_village_level after 780) demo-reel setup:
- BP_IV_Fem5Demo (/Game/RandomIsoVillage/Blueprints): child of BP_SFC_Fem5Character that follows a scripted path on the
  level-sequence clock (SeqT: sequence player time, else game time, so Simulate and Movie Render Queue match); each tick
  she steers at the path point 0.4 s ahead (as 773). Her mesh renders custom depth (stencil 1) for the silhouette.
- Route (from the village plan and the nav grid of the rebuilt start section): she stands in a house by one of the three
  main roads on the outside of the first ring street, walks out of its door (doors open for her), runs out along the main
  road, across the border of the start section (the next section generates ahead of her), stops a few metres into the
  new part while the big map is open (as in play: she cannot move with the map open) and runs on.
  The main road that leaves the start section soonest is used. Knots (time, x, y), the time the next section is
  triggered and the map window are written to SourceArt/random_isometric_village/cine_route.json for 785.
- IV_VillageGenerator follows her (TrackedActor) with a fixed session seed; doors open for her within 3.2 m; the next
  section is generated 30 m before the border, so the border is on screen when the reveal starts (785 widens the view).
- Villagers as in the playable level (786), but they do not block her: her walk is scripted.
- MoviePipelineGameMode (no player pawn). 784 records her and the generation in Simulate, 785 keys the camera."""
import unreal, json, math, os
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
V = unreal.Vector
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert w.get_path_name().startswith("/Game/RandomIsoVillage/Maps/random_isometric_village_level_Cine."), w.get_path_name()
RUN, WALK = 376.7, 150.0
SEED = 20261013
HOLD, DUR = 4.2, 31.0        # she waits inside while the camera comes over from the square and the view is turned; path length in seconds
TRIGGER = 3000.0             # the next section is generated this far before the border
MAP_AFTER, MAP_PAUSE = 8.9, 5.6   # she stops this long after the trigger (the reveal takes 7 s) and stands this long: the big map
gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.IVVillageGenerator))
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith("Demo_") or isinstance(a, unreal.PlayerStart): eas.destroy_actor(a)
gen.set_editor_property("tracked_actor", None)
gen.build_start_section()                     # same seed, same village: gives this session its nav grid
sec = gen.get_section(unreal.IntPoint(0, 0)); SS = gen.get_editor_property("section_size")
d2 = lambda a, b: math.hypot(a.x - b.x, a.y - b.y)
# ---- the three main roads as polylines from the square outward (bands 0..3: all inside the fixed part of the plan)
def main_poly(i0):
    pts = []
    for b in range(4):
        idx = [i for i in range(gen.spoke_count(b)) if gen.is_main_spoke(b, i)]
        i = i0 if b == 0 else min(idx, key=lambda k: d2(gen.spoke_point(b, k, 0.0), pts[-1]))
        pts += [gen.spoke_point(b, i, k / 12.0) for k in range(13)]
    return pts
def exit_len(pts):
    L = 0.0
    for a, b in zip(pts, pts[1:]):
        L += d2(a, b)
        if max(abs(b.x), abs(b.y)) > SS / 2: return L
    return 1e9
polys = [main_poly(i) for i in range(gen.spoke_count(0)) if gen.is_main_spoke(0, i)]
poly = min(polys, key=exit_len)
r = lambda p: math.hypot(p.x, p.y)
# ---- her house: the nearest door to the road just outside the first ring street
ring1 = gen.ring_radius(1, math.atan2(poly[13].y, poly[13].x))
best = None
for i in range(sec.get_num_buildings()):
    o, inn = sec.get_building_entry(i)
    if not (ring1 + 200 < r(V(o.x, o.y, 0)) < ring1 + 2600) or sec.get_building_kind(i) not in ("Cottage", "Farmhouse"): continue
    k = min(range(len(poly)), key=lambda j: d2(poly[j], o))
    if best is None or d2(poly[k], o) < best[0]: best = (d2(poly[k], o), i, o, inn, k)
_, bi, out_pt, in_pt, k0 = best
c = sec.get_building_center(bi)
dirn = V(c.x - in_pt.x, c.y - in_pt.y, 0).normal()
start = in_pt + dirn * 110.0
if not gen.is_walkable(start): start = in_pt + dirn * 40.0
# from the door to the road (nav path), then out along the road
k1 = next(j for j in range(k0, len(poly)) if r(poly[j]) > r(V(out_pt.x, out_pt.y, 0)) + 500)
link = list(gen.find_path(V(out_pt.x, out_pt.y, 0), V(poly[k1].x, poly[k1].y, 0), 400000))
assert link, "no path from the door to the road"
route = [(start.x, start.y, WALK), (in_pt.x, in_pt.y, WALK), (out_pt.x, out_pt.y, WALK)] + [(p.x, p.y, RUN) for p in link[1:]] + [(p.x, p.y, RUN) for p in poly[k1 + 1:]]
# drop points closer than 60 cm, then time the knots: HOLD, walking to the door, running from there
pts = [route[0]]
for p in route[1:]:
    if math.hypot(p[0] - pts[-1][0], p[1] - pts[-1][1]) > 60: pts.append(p)
KNOTS = [(0.0, pts[0][0], pts[0][1]), (HOLD, pts[0][0], pts[0][1])]; t = HOLD
for a, b in zip(pts, pts[1:]):
    t += math.hypot(b[0] - a[0], b[1] - a[1]) / b[2]
    KNOTS.append((t, b[0], b[1]))
def when(reach):
    """time at which she is first `reach` cm from the middle of the start section along an axis (linear in a segment)"""
    for (t0, x0, y0), (t1, x1, y1) in zip(KNOTS, KNOTS[1:]):
        m0, m1 = max(abs(x0), abs(y0)), max(abs(x1), abs(y1))
        if m0 <= reach < m1: return t0 + (t1 - t0) * (reach - m0) / (m1 - m0)
    raise AssertionError("the route does not leave the start section")
t_trig = when(SS / 2 - TRIGGER)
# the stop for the map: a knot at t_stop, the same place again MAP_PAUSE later, everything after it that much later
t_stop = t_trig + MAP_AFTER
i = next(k for k in range(1, len(KNOTS)) if KNOTS[k][0] > t_stop)
(t0, x0, y0), (t1, x1, y1) = KNOTS[i - 1], KNOTS[i]; u = (t_stop - t0) / (t1 - t0)
stop = (x0 + (x1 - x0) * u, y0 + (y1 - y0) * u)
KNOTS = KNOTS[:i] + [(t_stop, *stop), (t_stop + MAP_PAUSE, *stop)] + [(k[0] + MAP_PAUSE, k[1], k[2]) for k in KNOTS[i:]]
cross = when(SS / 2)
KNOTS = [k for n, k in enumerate(KNOTS) if n == 0 or KNOTS[n - 1][0] <= DUR]
assert KNOTS[-1][0] >= DUR - 0.5, f"route too short: {KNOTS[-1][0]:.1f} s"
# she steers at the point 0.4 s ahead: she has come to rest 0.72 s after t_stop and sets off 0.4 s early
MAP = (t_stop + 0.85, t_stop + MAP_PAUSE - 0.55)
print(f"house {bi} {sec.get_building_kind(bi)} {sec.get_building_style(bi)} at r {r(c) / 100:.0f} m | {len(KNOTS)} knots, {KNOTS[-1][0]:.1f} s | next section triggered at {t_trig:.1f} s "
      f"| crosses the border at {cross:.1f} s | stops at {t_stop:.1f} s ({stop[0]:.0f},{stop[1]:.0f}), map {MAP[0]:.1f}-{MAP[1]:.1f} s | ends at ({KNOTS[-1][1]:.0f},{KNOTS[-1][2]:.0f})")
OUT = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_isometric_village"; os.makedirs(OUT, exist_ok=True)
json.dump({"knots": KNOTS, "house": bi, "house_center": [c.x, c.y], "hold": HOLD, "trigger": t_trig, "cross": cross, "stop": t_stop, "map": MAP, "run": RUN},
          open(os.path.join(OUT, "cine_route.json"), "w"))
# ---- demo character
G = "/Game/RandomIsoVillage/Blueprints"; PATH = f"{G}/BP_IV_Fem5Demo"
if not eal.does_asset_exist(PATH):
    f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.load_asset("/Game/SFCityLevel/Blueprints/BP_SFC_Fem5Character").generated_class())
    at.create_asset("BP_IV_Fem5Demo", G, unreal.Blueprint, f)
bp = unreal.load_asset(PATH); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
graphs = lambda: {x.get_name(): x for x in T.list_graphs(bp)}
def path_expr(knots, axis):
    """nested selects: constant before the first knot, linear between knots, constant after the last"""
    e = f"{knots[-1][axis]:.1f}"
    for (t0, *p0), (t1, *p1) in reversed(list(zip(knots, knots[1:]))):
        a, b = p0[axis - 1], p1[axis - 1]; s = (b - a) / max(t1 - t0, 1e-4)
        seg = f"{a:.1f}" if abs(s) < 1e-6 else f"(+ {a:.1f} (* (- T {t0:.3f}) {s:.4f}))"
        e = f"(select (< T {t1:.3f}) {seg} {e})"
    return f"(select (< T {knots[0][0]:.3f}) {knots[0][axis]:.1f} {e})"
FUNCS = {"SeqT": ("""
(fn SeqT ()
  (bind lsa (Utilities|Casting|CastToLevelSequenceActor :Object (Actor|GetActorOfClass :ActorClass "/Script/LevelSequence.LevelSequenceActor"))
    (:then
      (return (Utilities|TimeManagement|QualifiedFrameTimeToSeconds (Sequencer|Player|GetCurrentTime :self (Class|LevelSequenceActor|GetSequencePlayer :self lsa)))))
    (:CastFailed
      (return (Utilities|Time|GetGameTimeinSeconds)))))""", (), (("Out", "float"),)),
    "Steer": (f"""
(fn Steer (Target)
  (bind loc (Transformation|GetActorLocation))
  (bind d (Math|Vector|MakeVector (- (.x Target) (.x loc)) (- (.y Target) (.y loc)) 0.0))
  (bind s (/ (Math|Vector|VectorLength d) {RUN * 0.4:.2f}))
  (if (> s 0.06)
    (Pawn|Input|AddMovementInput :WorldDirection (Math|Vector|Normalize d) :ScaleValue (select (> s 1.0) 1.0 s))))""", (("Target", "vector"),), ()),
    "Path": (f"""
(fn Path (T)
  (return (Math|Vector|MakeVector {path_expr(KNOTS, 1)} {path_expr(KNOTS, 2)} 0.0)))""", (("T", "float"),), (("Out", "vector"),))}
for name, (code, ins, outs) in FUNCS.items():
    assert code.count("(") == code.count(")"), name
    if name in graphs(): T.remove_function_graph(bp, name); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    g = T.add_function_graph(bp, name)
    for p, ty in ins: T.add_function_param(g, p, ty, True)
    for p, ty in outs: T.add_function_param(g, p, ty, False)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    g = graphs()[name]
    T.write_graph_dsl(g, code); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert len(T.read_graph_dsl(g).strip().splitlines()) > 1, name + ": empty body, see LogScript"
TICK = """
(event EventTick (DeltaSeconds)
  (CallFunction|Steer :Target (CallFunction|Path :T (+ (CallFunction|SeqT) 0.4))))
"""
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
for n in T.find_nodes(g, ""):
    if any(str(p.name) == "DeltaSeconds" for p in T.get_node_infos([n])[0].output_pins): T.delete_node(n)
T.write_graph_dsl(g, TICK)
ok = unreal.BlueprintEditorLibrary.compile_blueprint(bp); eal.save_loaded_asset(bp, only_if_is_dirty=False)
assert "Steer" in " ".join(T.read_graph_dsl(g).split()), "tick graph empty: see LogScript"
print("BP compile", ok)
# ---- level
ws = w.get_world_settings(); ws.set_editor_property("default_game_mode", unreal.load_class(None, "/Script/MovieRenderPipelineCore.MoviePipelineGameMode"))
yaw0 = math.degrees(math.atan2(in_pt.y - start.y, in_pt.x - start.x))
a = eas.spawn_actor_from_class(bp.generated_class(), V(start.x, start.y, 115), unreal.Rotator(roll=0, pitch=0, yaw=yaw0))
a.set_actor_label("Demo_IV_Fem5"); a.set_folder_path("IsoVillage/Cine")
a.set_editor_property("auto_possess_ai", unreal.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED)
a.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.DISABLED)
a.mesh.set_render_custom_depth(True); a.mesh.set_custom_depth_stencil_value(1)
for k, v in (("tracked_actor", a), ("fixed_session_seed", SEED), ("trigger_distance", TRIGGER), ("safety_distance", 1300.0),
             ("tracked_auto_door_distance", 320.0), ("unload_section_distance", 0)):
    gen.set_editor_property(k, v)
_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "786_iv_villagers.py")
exec(compile(open(_p, encoding="utf-8").read(), _p, "exec"), {"__name__": "iv_villagers", "ARGS": ["noblock", "nosave"]})
print("Demo_IV_Fem5 at", a.get_actor_location(), "| generator tracks", gen.get_editor_property("tracked_actor").get_actor_label(), "seed", SEED)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
print("saved")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
