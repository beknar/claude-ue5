"""BP_FF2Character water splashes: WaterStep(DT) each tick. Water height = the pack's BP_water actor (looked up once).
In water = soles more than 3 cm below the surface. A foot strike (ball_ bone drops through 7 cm above the soles) spawns
BP_Splash at that foot on the surface, scaled by speed (0.55..1.35); landing from a jump in water spawns a 1.8x splash."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary
bp = unreal.load_asset("/Game/FF2/Game/BP_FF2Character")
cdo0 = unreal.get_default_object(bp.generated_class())
def has_var(n):
    try: cdo0.get_editor_property(n); return True
    except Exception: return False
for name, typ in (("WaterZ", "float"), ("WaterChecked", "bool"), ("PrevLZ", "float"), ("PrevRZ", "float"), ("WasFalling", "bool")):
    if not has_var(name): T.add_variable(bp, name, typ)
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
SPLASH = '"/Game/Castle/Interactive/Blueprints/BP_Splash.BP_Splash_C"'
WATER = '"/Game/Medieval_Fantasy_Village/Blueprint/Water/BP_water.BP_water_C"'
fn("SpawnSplash", ["X", "Y", "S"], f"""
(fn SpawnSplash (X Y S)
  (Game|SpawnActorfromClass :Class {SPLASH} :SpawnTransform (Math|Transform|MakeTransform :Location (Math|Vector|MakeVector X Y (+ (Variables|Default|GetWaterZ) 0.5)) :Rotation (Math|Rotator|MakeRotator :Roll 0.0 :Pitch 0.0 :Yaw (Math|Random|RandomFloatinRange 0.0 360.0)) :Scale (Math|Vector|MakeVector S S S))))""")
fn("WaterStep", ["DT"], f"""
(fn WaterStep (DT)
  (if (not (Variables|Default|GetWaterChecked))
    (Variables|Default|SetWaterChecked true)
    (Variables|Default|SetWaterZ -1000000.0)
    (bind w (Actor|GetActorOfClass :ActorClass {WATER}))
    (bind wz (.z (Transformation|GetActorLocation :self w)))
    (Variables|Default|SetWaterZ (select (< (* wz wz) 0.000001) -1000000.0 wz)))
  (bind base (- (.z (Transformation|GetActorLocation)) 85.2))
  (bind inwater (> (Variables|Default|GetWaterZ) (+ base 3.0)))
  (bind spd (Math|Vector|VectorLengthXY (Transformation|GetVelocity)))
  (bind s (Math|Float|Clamp(Float) :Value (+ 0.55 (/ spd 420.0)) :Min 0.55 :Max 1.35))
  (bind pl (Transformation|GetSocketLocation :self (Variables|Character|GetMesh) :InSocketName "ball_l"))
  (bind pr (Transformation|GetSocketLocation :self (Variables|Character|GetMesh) :InSocketName "ball_r"))
  (bind lz (- (.z pl) base))
  (bind rz (- (.z pr) base))
  (bind falling (Movement|IsFalling :self (Variables|Character|GetCharacterMovement)))
  (if (and inwater (and (> (Variables|Default|GetPrevLZ) 7.0) (<= lz 7.0)))
    (CallFunction|SpawnSplash :X (.x pl) :Y (.y pl) :S s))
  (if (and inwater (and (> (Variables|Default|GetPrevRZ) 7.0) (<= rz 7.0)))
    (CallFunction|SpawnSplash :X (.x pr) :Y (.y pr) :S s))
  (if (and inwater (and (Variables|Default|GetWasFalling) (not falling)))
    (CallFunction|SpawnSplash :X (.x (Transformation|GetActorLocation)) :Y (.y (Transformation|GetActorLocation)) :S 1.8))
  (Variables|Default|SetPrevLZ lz)
  (Variables|Default|SetPrevRZ rz)
  (Variables|Default|SetWasFalling falling))""")
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
        (CallFunction|DemoStep :T (- (Utilities|TimeManagement|QualifiedFrameTimeToSeconds (Sequencer|Player|GetCurrentTime :self (Class|LevelSequenceActor|GetSequencePlayer :self lsa))) (Variables|Default|GetDemoStartTime))))
      (:CastFailed
        (CallFunction|DemoStep :T (- {NOW} (Variables|Default|GetDemoStartTime)))))
    (else
      (if (and (Variables|Default|GetLongActive) (> (Math|Vector|VectorLength (Transformation|GetVelocity)) 5.0))
        (Animation|StopAnimMontage)
        (Variables|Default|SetLongActive false)))))
"""
assert tick.count("(") == tick.count(")")
T.write_graph_dsl(g, tick)
print("compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp)); eal.save_loaded_asset(bp, only_if_is_dirty=False)
dsl = T.read_graph_dsl(g)
print("tick has WaterStep:", "WaterStep" in dsl, "| DemoStep:", "DemoStep" in dsl, "| input events:", dsl.count("EnhancedInputAction"))
print("WaterStep:", " ".join(T.read_graph_dsl(graphs()["WaterStep"]).split())[:240])
