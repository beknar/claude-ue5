"""random_dungeon_level_Cine (Save As copy of random_dungeon_level after 770) demo-reel setup:
- BP_RD_Fem5Demo (/Game/RandomDungeon/Blueprints): child of BP_SFC_Fem5Character that runs a scripted path on the
  level-sequence clock (SeqT: sequence player time, else game time, so Simulate and Movie Render Queue match); each tick
  she steers at the path point 0.4 s ahead (as 754).
- Demo_RD_Fem5 runs east along the y = 7350 lane of the start section: chapel -> hallway -> prison cells -> the east edge
  hallway, across the border into the next section (generated as the prison's far door opens ahead of her, about 11.3 s).
- RD_DungeonGenerator follows her (TrackedActor) with a fixed session seed; doors open by themselves in front of her
  (TrackedAutoDoorDistance), monsters don't body-block her; trigger 12 m ahead so the curtain rises on camera.
- MoviePipelineGameMode (no player pawn). Times are sequence seconds (774 records her and the generation, 775 keys the camera)."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
V = unreal.Vector
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert w.get_path_name().startswith("/Game/RandomDungeon/Maps/random_dungeon_level_Cine."), w.get_path_name()
RUN = 376.7
SEED = 20261012
Y, X0, GO, DUR = 7350.0, 7300.0, 0.3, 20.5
# (sequence time, x, y): she stands at the first knot until the second knot's time, then runs east
KNOTS = [(0.0, X0, Y), (GO, X0, Y), (DUR, X0 + (DUR - GO) * RUN, Y)]
G = "/Game/RandomDungeon/Blueprints"; PATH = f"{G}/BP_RD_Fem5Demo"
if not eal.does_asset_exist(PATH):
    f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.load_asset("/Game/SFCityLevel/Blueprints/BP_SFC_Fem5Character").generated_class())
    at.create_asset("BP_RD_Fem5Demo", G, unreal.Blueprint, f)
bp = unreal.load_asset(PATH); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
graphs = lambda: {x.get_name(): x for x in T.list_graphs(bp)}
def path_expr(knots, axis):
    """nested selects: constant before the first moving knot, linear between knots, constant after the last"""
    e = f"{knots[-1][axis]:.1f}"
    for (t0, *p0), (t1, *p1) in reversed(list(zip(knots, knots[1:]))):
        a, b = p0[axis - 1], p1[axis - 1]; s = (b - a) / (t1 - t0)
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
  (if (> s 0.08)
    (Pawn|Input|AddMovementInput :WorldDirection (Math|Vector|Normalize d) :ScaleValue (select (> s 1.0) 1.0 s))))""", (("Target", "vector"),), ()),
    "Path": (f"""
(fn Path (T)
  (return (Math|Vector|MakeVector {path_expr(KNOTS, 1)} {path_expr(KNOTS, 2)} 0.0)))""", (("T", "float"),), (("Out", "vector"),))}
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
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith("Demo_") or isinstance(a, unreal.PlayerStart): eas.destroy_actor(a)
gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
a = eas.spawn_actor_from_class(bp.generated_class(), V(X0, Y, 100), unreal.Rotator(roll=0, pitch=0, yaw=0))
a.set_actor_label("Demo_RD_Fem5"); a.set_folder_path("RandomDungeon/Cine")
a.set_editor_property("auto_possess_ai", unreal.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED)
a.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.DISABLED)
for k, v in (("tracked_actor", a), ("fixed_session_seed", SEED), ("trigger_distance", 1200.0), ("safety_distance", 1200.0),
             ("tracked_auto_door_distance", 800.0), ("monsters_block_pawns", False), ("unload_section_distance", 0)):
    gen.set_editor_property(k, v)
print("Demo_RD_Fem5 at", a.get_actor_location(), "| generator tracks", gen.get_editor_property("tracked_actor").get_actor_label(), "seed", SEED)
print("knots", [(round(t, 2), round(x), round(y)) for t, x, y in KNOTS], "| border x 12600 at %.1f s" % (GO + (12600 - X0) / RUN))
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
print("saved")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
