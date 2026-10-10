"""Demo routine clocked by the playing Level Sequence (MRQ) when present, else game time - DemoStartTime."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
bp = unreal.load_asset("/Game/Fig4/Game/BP_Fig4Character")
graphs = {x.get_name(): x for x in T.list_graphs(bp)}
if "DemoStep" not in graphs:
    fg = T.add_function_graph(bp, "DemoStep")
    T.add_function_param(fg, "T", "float", True)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    graphs = {x.get_name(): x for x in T.list_graphs(bp)}
T.write_graph_dsl(graphs["DemoStep"], """
(fn DemoStep (T)
  (bind loc (Transformation|GetActorLocation))
  (bind a (/ (.x loc) 2500.0))
  (bind side (+ (* 0.16 (Math|Trig|Cos(Radians) a)) (* (- (* 400.0 (Math|Trig|Sin(Radians) a)) (.y loc)) 0.002)))
  (bind dir (Math|Vector|Normalize (Math|Vector|MakeVector 1.0 side 0.0)))
  (bind s (select (< T 2.0) 0.0 (select (< T 6.5) 0.383 (select (< T 13.0) 1.0 (select (< T 15.0) 0.383 0.0)))))
  (Pawn|Input|AddMovementInput :WorldDirection dir :ScaleValue s)
  (if (and (> T 9.5) (not (Variables|Default|GetDemoJumped)))
    (Character|Jump)
    (Variables|Default|SetDemoJumped true))
  (if (> T 9.8)
    (Character|StopJumping)))
""")
print(T.read_graph_dsl(graphs["DemoStep"]))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
for n in T.find_nodes(g, ""):
    i = T.get_node_infos([n])[0]
    if any(str(p.name) == "DeltaSeconds" for p in i.output_pins): T.delete_node(n)
for n in T.find_nodes(g, ""):   # orphaned nodes from the old tick body
    i = T.get_node_infos([n])[0]
    if not str(i.type_id).startswith("AddEvent") and "Event" not in str(i.type_id): T.delete_node(n)
T.write_graph_dsl(g, """
(event EventTick (DeltaSeconds)
  (if (Variables|Default|GetAutoDemo)
    (bind lsa (Utilities|Casting|CastToLevelSequenceActor :Object (Actor|GetActorOfClass :ActorClass "/Script/LevelSequence.LevelSequenceActor"))
      (:then
        (CallFunction|DemoStep :T (Utilities|TimeManagement|QualifiedFrameTimeToSeconds (Sequencer|Player|GetCurrentTime :self (Class|LevelSequenceActor|GetSequencePlayer :self lsa)))))
      (:CastFailed
        (CallFunction|DemoStep :T (- (Utilities|Time|GetGameTimeinSeconds) (Variables|Default|GetDemoStartTime)))))))
""")
print(T.read_graph_dsl(g))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_loaded_asset(bp)
