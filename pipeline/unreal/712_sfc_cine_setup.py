"""sf-city-level_Cine (700 cine copy) showcase setup:
- BP_SFC_Fem5Demo (/Game/SFCityLevel/Blueprints): child of BP_SFC_Fem5Character (36 cm capsule, foot IK) that walks a
  scripted path on the level-sequence clock (SeqT: sequence player time, else game time, so Simulate and MRQ match).
  Path<A|C|D>(T) = piecewise-linear knot positions (generated from KNOTS below); each tick she steers at the point 0.4 s
  ahead: AddMovementInput scale = distance / (RUN * 0.4), which settles on the knot speed with no lag (walk 118, run 377).
  Instance-editable: Which (0 A, 1 C, 2 D), ShowFrom / ShowTo (hidden outside, so only one of her is on screen),
  JumpAt (-1 = never).
- three demo actors (cuts teleport her between locations): A boulevard -> Noodle Bar, C the bridge road (jump), D the
  Monolith plaza -> Excavation Lab.
- the Noodle Bar and lab front doors open on the sequence clock (AutoOpenAt); MoviePipelineGameMode (no player pawn).
Times are sequence seconds (713 records her in Simulate, 714 keys the cameras from that recording)."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
V = unreal.Vector
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert w.get_path_name().startswith("/Game/SFCityLevel/Maps/sf-city-level_Cine."), w.get_path_name()
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_current_level_by_name("sf-city-level_Cine")
RUN = 376.7
# (sequence time, x, y): she stands at the first knot until the second knot's time
KNOTS = {
    "A": [(0.0, -13600, -52500), (1.0, -13600, -52500), (4.1, -12550, -52937), (5.5, -12400, -53000),     # run up the boulevard, walk
          (8.9, -12000, -53000), (11.4, -12000, -53300)],                                                    # through the door, to the bar
    "C": [(0.0, -15000, -65400), (10.0, -15000, -65400), (16.6, -15000, -65400 - RUN * 6.6)],               # run toward the Monolith
    "D": [(0.0, -19300, -93400), (14.8, -19300, -93400), (17.7, -20380, -93400), (20.85, -20750, -93400)],  # run to the lab, walk in
}
ACTORS = [("Demo_A_Boulevard", 0, "A", 0.0, 10.6, -1.0, 32.0), ("Demo_C_Bridge", 1, "C", 10.4, 15.6, 12.9, 61.6),
          ("Demo_D_Lab", 2, "D", 15.4, 21.0, -1.0, -50.0)]          # label, Which, path, ShowFrom, ShowTo, JumpAt, floor z
DOORS = {"NoodleBar_FrontDoor": 4.8, "ExcavationLab_FrontDoor": 16.3}
G = "/Game/SFCityLevel/Blueprints"; PATH = f"{G}/BP_SFC_Fem5Demo"
if not eal.does_asset_exist(PATH):
    f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.load_asset(f"{G}/BP_SFC_Fem5Character").generated_class())
    at.create_asset("BP_SFC_Fem5Demo", G, unreal.Blueprint, f)
bp = unreal.load_asset(PATH); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
cdo = unreal.get_default_object(bp.generated_class())
for nm, typ in (("Which", "float"), ("ShowFrom", "float"), ("ShowTo", "float"), ("JumpAt", "float"), ("Jumped", "bool")):
    try: cdo.get_editor_property(nm)
    except Exception:
        T.add_variable(bp, nm, typ)
        if nm != "Jumped": T.set_variable_instance_editable(bp, nm, True)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
graphs = lambda: {x.get_name(): x for x in T.list_graphs(bp)}
def path_expr(knots, axis):
    """nested selects: constant before the first moving knot, linear between knots, constant after the last"""
    e = f"{knots[-1][axis]:.1f}"
    for (t0, *p0), (t1, *p1) in reversed(list(zip(knots, knots[1:]))):
        a, b = p0[axis - 1], p1[axis - 1]; s = (b - a) / (t1 - t0)
        seg = f"{a:.1f}" if abs(s) < 1e-6 else f"(+ {a:.1f} (* (- T {t0:.3f}) {s:.4f}))"
        e = f"(select (< T {t1:.3f}) {seg} {e})"
    return f"(select (< T {knots[0][0]:.3f}) {knots[0][1 if axis == 1 else 2]:.1f} {e})"
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
  (if (> s 0.08)
    (Pawn|Input|AddMovementInput :WorldDirection (Math|Vector|Normalize d) :ScaleValue (select (> s 1.0) 1.0 s))))""", (("Target", "vector"),), ())}
for k, kn in KNOTS.items():
    FUNCS["Path" + k] = (f"""
(fn Path{k} (T)
  (return (Math|Vector|MakeVector {path_expr(kn, 1)} {path_expr(kn, 2)} 0.0)))""", (("T", "float"),), (("Out", "vector"),))
for name, (code, ins, outs) in FUNCS.items():
    assert code.count("(") == code.count(")"), name
    if name in graphs(): T.remove_function_graph(bp, name); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    g = T.add_function_graph(bp, name)
    for p, t in ins: T.add_function_param(g, p, t, True)
    for p, t in outs: T.add_function_param(g, p, t, False)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    g = graphs()[name]
    T.write_graph_dsl(g, code); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert len(T.read_graph_dsl(g).strip().splitlines()) > 1, name + ": empty body, see LogScript"
TICK = """
(event EventTick (DeltaSeconds)
  (bind t (CallFunction|SeqT))
  (Rendering|SetActorHiddenInGame :bNewHidden (or (< t (Variables|Default|GetShowFrom)) (> t (Variables|Default|GetShowTo))))
  (bind tl (+ t 0.4))
  (CallFunction|Steer :Target (select (< (Variables|Default|GetWhich) 0.5) (CallFunction|PathA :T tl) (select (< (Variables|Default|GetWhich) 1.5) (CallFunction|PathC :T tl) (CallFunction|PathD :T tl))))
  (if (and (>= (Variables|Default|GetJumpAt) 0.0) (and (> t (Variables|Default|GetJumpAt)) (not (Variables|Default|GetJumped))))
    (Character|Jump)
    (Variables|Default|SetJumped true))
  (if (and (Variables|Default|GetJumped) (> t (+ (Variables|Default|GetJumpAt) 0.3)))
    (Character|StopJumping)))
"""
assert TICK.count("(") == TICK.count(")")
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
for n in T.find_nodes(g, ""):
    if any(str(p.name) == "DeltaSeconds" for p in T.get_node_infos([n])[0].output_pins): T.delete_node(n)
T.write_graph_dsl(g, TICK)
ok = unreal.BlueprintEditorLibrary.compile_blueprint(bp); eal.save_loaded_asset(bp, only_if_is_dirty=False)
d = " ".join(T.read_graph_dsl(g).split()); assert "Steer" in d and "SetActorHiddenInGame" in d, "tick graph empty: see LogScript"
print("BP compile", ok)
# ---- level
ws = w.get_world_settings(); ws.set_editor_property("default_game_mode", unreal.load_class(None, "/Script/MovieRenderPipelineCore.MoviePipelineGameMode"))
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith("Demo_"): eas.destroy_actor(a)
for lab, which, k, s0, s1, jump, fz in ACTORS:
    kn = KNOTS[k]; p0 = kn[0]; p1 = next(q for q in kn if (q[1], q[2]) != (p0[1], p0[2]))
    yaw = unreal.MathLibrary.find_look_at_rotation(V(p0[1], p0[2], 0), V(p1[1], p1[2], 0)).yaw
    a = eas.spawn_actor_from_class(bp.generated_class(), V(p0[1], p0[2], fz + 98), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
    a.set_actor_label(lab); a.set_folder_path("SFC/Cine")
    a.set_editor_property("auto_possess_ai", unreal.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED)
    a.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.DISABLED)
    for nm, v in (("Which", float(which)), ("ShowFrom", s0), ("ShowTo", s1), ("JumpAt", jump)): a.set_editor_property(nm, v)
    print(lab, "at", [round(v) for v in (a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z)], "yaw", round(yaw))
for a in eas.get_all_level_actors():
    if a.get_actor_label() in DOORS: a.set_editor_property("AutoOpenAt", DOORS[a.get_actor_label()]); print("door", a.get_actor_label(), "opens at", DOORS[a.get_actor_label()])
    l = a.get_actor_location()                                       # lab chairs in front of shot D's camera (713): hidden in this copy
    if a.get_actor_label() == "LabChair" and abs(l.y + 93545) < 30: a.set_actor_hidden_in_game(True); print("hidden", a.get_actor_label(), l)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
print("saved")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
