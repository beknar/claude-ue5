"""BP_FF2Character castle showcase route (DemoMode 1, river shifted by RS for the interior tour): idle at house_02's door (door auto-opens), walk in and across the room
to the barrel near the door wall (it auto-opens), then cut to the river: sprint 13 m upstream through the water with a jump.
DemoMode 0 keeps the meadow routine (DemoStep). Rewrites the tick to dispatch via RunDemo(T)."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary
bp = unreal.load_asset("/Game/FF2/Game/BP_FF2Character")
cdo0 = unreal.get_default_object(bp.generated_class())
def has_var(n):
    try: cdo0.get_editor_property(n); return True
    except Exception: return False
for name, typ in (("DemoMode", "float"), ("DTele", "bool"), ("DJump2", "bool")):
    if not has_var(name): T.add_variable(bp, name, typ)
T.set_variable_instance_editable(bp, "DemoMode", True)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
graphs = lambda: {x.get_name(): x for x in T.list_graphs(bp)}
def fn(name, params, code):
    assert code.count("(") == code.count(")"), name
    if name not in graphs():
        g = T.add_function_graph(bp, name)
        for p in params: T.add_function_param(g, p, "float", True)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    T.write_graph_dsl(graphs()[name], code); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert len(T.read_graph_dsl(graphs()[name]).strip().splitlines()) > 1, f"{name} empty (see LogScript)"
WR = 102.3 / 337.0
RS = 8.1                       # river shift: the showcase cuts to furnished interiors (camera only) between the bakery and the river
WX, WY = 2250.0, -950.0        # walk into the open middle of the bakery (clear of the wall shelves and the loft posts)
TT, R0, R1, J0, J1 = (round(t + RS, 2) for t in (11.5, 11.8, 15.6, 13.6, 13.9))
def toward(x, y): return f"(Math|Vector|Normalize (Math|Vector|MakeVector (- {x} (.x loc)) (- {y} (.y loc)) 0.0))"
def dist(x, y): return f"(Math|Vector|VectorLengthXY (Math|Vector|MakeVector (- {x} (.x loc)) (- {y} (.y loc)) 0.0))"
fn("DemoStepCastle", ["T"], f"""
(fn DemoStepCastle (T)
  (bind loc (Transformation|GetActorLocation))
  (if (and (>= T 1.2) (< T 4.2))
    (Pawn|Input|AddMovementInput :WorldDirection {toward(1965.0, -1505.0)} :ScaleValue {WR:.4f}))
  (if (and (>= T 4.2) (< T 11.0))
    (if (> {dist(WX, WY)} 20.0)
      (Pawn|Input|AddMovementInput :WorldDirection {toward(WX, WY)} :ScaleValue {WR:.4f})))
  (if (and (>= T {TT}) (not (Variables|Default|GetDTele)))
    (Variables|Default|SetDTele true)
    (Transformation|SetActorLocation :NewLocation (Math|Vector|MakeVector -4380.0 -3650.0 45.0) :bSweep false :bTeleport true)
    (Transformation|SetActorRotation :NewRotation (Math|Rotator|MakeRotator :Roll 0.0 :Pitch 0.0 :Yaw 90.0) :bTeleportPhysics true))
  (if (and (>= T {R0}) (< T {R1}))
    (Pawn|Input|AddMovementInput :WorldDirection (Math|Vector|MakeVector 0.0 1.0 0.0) :ScaleValue 1.0))
  (if (and (> T {J0}) (not (Variables|Default|GetDJump2)))
    (Character|Jump)
    (Variables|Default|SetDJump2 true))
  (if (> T {J1})
    (Character|StopJumping)))""")
fn("RunDemo", ["T"], """
(fn RunDemo (T)
  (if (> (Variables|Default|GetDemoMode) 0.5)
    (CallFunction|DemoStepCastle :T T)
    (else
      (CallFunction|DemoStep :T T))))""")
NOW = "(Utilities|Time|GetGameTimeinSeconds)"
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
for n in T.find_nodes(g, ""):
    if any(str(p.name) == "DeltaSeconds" for p in T.get_node_infos([n])[0].output_pins): T.delete_node(n)
tick = f"""
(event EventTick (DeltaSeconds)
  (CallFunction|WaterStep :DT DeltaSeconds)
  (if (Variables|Default|GetAutoDemo)
    (bind lsa (Utilities|Casting|CastToLevelSequenceActor :Object (Actor|GetActorOfClass :ActorClass "/Script/LevelSequence.LevelSequenceActor"))
      (:then
        (CallFunction|RunDemo :T (- (Utilities|TimeManagement|QualifiedFrameTimeToSeconds (Sequencer|Player|GetCurrentTime :self (Class|LevelSequenceActor|GetSequencePlayer :self lsa))) (Variables|Default|GetDemoStartTime))))
      (:CastFailed
        (CallFunction|RunDemo :T (- {NOW} (Variables|Default|GetDemoStartTime)))))
    (else
      (if (and (Variables|Default|GetLongActive) (> (Math|Vector|VectorLength (Transformation|GetVelocity)) 5.0))
        (Animation|StopAnimMontage)
        (Variables|Default|SetLongActive false)))))
"""
assert tick.count("(") == tick.count(")")
T.write_graph_dsl(g, tick)
print("compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp)); eal.save_loaded_asset(bp, only_if_is_dirty=False)
d = T.read_graph_dsl(g)
print("tick: WaterStep", "WaterStep" in d, "| RunDemo", "RunDemo" in d, "| input events", d.count("EnhancedInputAction"))
print("castle step:", " ".join(T.read_graph_dsl(graphs()["DemoStepCastle"]).split())[:200])
