"""BP_Door / BP_Container: AutoOpenAt (instance editable, default -1 = off). When >= 0 the actor opens itself once the
level-sequence clock (or game time without a sequence) passes it - used by the castle showcase cinematic.
Only the tick graph + a SeqTime function are (re)written; placed instances keep working."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary
NOW = "(Utilities|Time|GetGameTimeinSeconds)"
SEQ = f"""
(fn SeqTime ()
  (bind lsa (Utilities|Casting|CastToLevelSequenceActor :Object (Actor|GetActorOfClass :ActorClass "/Script/LevelSequence.LevelSequenceActor"))
    (:then
      (return (Utilities|TimeManagement|QualifiedFrameTimeToSeconds (Sequencer|Player|GetCurrentTime :self (Class|LevelSequenceActor|GetSequencePlayer :self lsa)))))
    (:CastFailed
      (return {NOW}))))"""     # no sequence (Simulate): game time = sequence time
AUTO = """
  (if (>= (Variables|Default|GetAutoOpenAt) 0.0)
    (if (>= (CallFunction|SeqTime) (Variables|Default|GetAutoOpenAt))
      (Variables|Default|SetOpen true)))"""
def prompt(P):
    return f"""
  (bind show (CallFunction|Targeted))
  (Rendering|SetVisibility :self {P} :bNewVisibility show)
  (if show
    (Transformation|SetWorldRotation :self {P} :NewRotation (Math|Rotator|FindLookatRotation :Start (Transformation|GetWorldLocation :self {P}) :Target (Camera|GetCameraLocation :self (Game|GetPlayerCameraManager :PlayerIndex 0)))))"""
TICKS = {
 "BP_Door": """
(event EventTick (DeltaSeconds)""" + AUTO + """
  (Variables|Default|SetAngle (Math|Interpolation|FInterpTo :Current (Variables|Default|GetAngle) :Target (select (Variables|Default|GetOpen) (Variables|Default|GetOpenYaw) 0.0) :DeltaTime DeltaSeconds :InterpSpeed 3.2))
  (Transformation|SetRelativeRotation :self (Variables|Default|GetLeaf) :NewRotation (Math|Rotator|MakeRotator :Roll 0.0 :Pitch 0.0 :Yaw (Variables|Default|GetAngle)))
  (if (or (Variables|Default|GetOpen) (> (* (Variables|Default|GetAngle) (Variables|Default|GetAngle)) 4.0))
    (Collision|SetCollisionResponsetoChannel :self (Variables|Default|GetLeaf) :Channel "ECC_Pawn" :NewResponse "ECR_Ignore")
    (else
      (Collision|SetCollisionResponsetoChannel :self (Variables|Default|GetLeaf) :Channel "ECC_Pawn" :NewResponse "ECR_Block")))""" + prompt("(Variables|Default|GetPrompt)") + ")\n",
 "BP_Container": """
(event EventTick (DeltaSeconds)""" + AUTO + """
  (Variables|Default|SetAngle (Math|Interpolation|FInterpTo :Current (Variables|Default|GetAngle) :Target (select (Variables|Default|GetOpen) (Variables|Default|GetOpenRoll) 0.0) :DeltaTime DeltaSeconds :InterpSpeed 4.0))
  (Transformation|SetRelativeRotation :self (Variables|Default|GetLid) :NewRotation (Math|Rotator|MakeRotator :Roll (Variables|Default|GetAngle) :Pitch 0.0 :Yaw 0.0))""" + prompt("(Variables|Default|GetPrompt)") + ")\n"}
for name, tick in TICKS.items():
    bp = unreal.load_asset(f"/Game/Castle/Interactive/Blueprints/{name}")
    cdo = unreal.get_default_object(bp.generated_class())
    try: cdo.get_editor_property("AutoOpenAt"); has = True
    except Exception: has = False
    if not has:
        T.add_variable(bp, "AutoOpenAt", "float"); T.set_variable_instance_editable(bp, "AutoOpenAt", True)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    gs = {x.get_name(): x for x in T.list_graphs(bp)}
    if "SeqTime" not in gs:
        fg = T.add_function_graph(bp, "SeqTime"); T.add_function_param(fg, "Out", "float", False); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        gs = {x.get_name(): x for x in T.list_graphs(bp)}
    assert SEQ.count("(") == SEQ.count(")") and tick.count("(") == tick.count(")")
    T.write_graph_dsl(gs["SeqTime"], SEQ); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert len(T.read_graph_dsl(gs["SeqTime"]).strip().splitlines()) > 1, name + " SeqTime empty"
    g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    for n in T.find_nodes(g, ""):
        if any(str(p.name) == "DeltaSeconds" for p in T.get_node_infos([n])[0].output_pins): T.delete_node(n)
    T.write_graph_dsl(g, tick)
    ok = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.get_default_object(bp.generated_class()).set_editor_property("AutoOpenAt", -1.0)
    eal.save_loaded_asset(bp, only_if_is_dirty=False)
    d = " ".join(T.read_graph_dsl(g).split())
    print(name, "compile", ok, "| tick has AutoOpenAt:", "GetAutoOpenAt" in d, "| SetAngle:", "SetAngle" in d, "| input event:", "EnhancedInputAction" in d)
