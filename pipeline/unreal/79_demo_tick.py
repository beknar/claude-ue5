"""Temporarily log the demo clock (sequence time / game time) each tick."""
import sys, unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
DEBUG = "off" not in sys.argv
bp = unreal.load_asset("/Game/Fig4/Game/BP_Fig4Character")
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
for n in T.find_nodes(g, ""):
    i = T.get_node_infos([n])[0]
    if any(str(p.name) == "DeltaSeconds" for p in i.output_pins): T.delete_node(n)
for n in T.find_nodes(g, ""):
    i = T.get_node_infos([n])[0]
    if not str(i.type_id).startswith("AddEvent") and "Event" not in str(i.type_id): T.delete_node(n)
dbg = '(Development|PrintString :InString (Utilities|String|Append :A "DEMOCLOCK seq " :B (Utilities|String|Append :A (Utilities|String|ToString(Float) st) :B (Utilities|String|ToString(Float) (.z (Transformation|GetActorLocation))))) :bPrintToScreen false :bPrintToLog true)' if DEBUG else ""
T.write_graph_dsl(g, f"""
(event EventTick (DeltaSeconds)
  (if (Variables|Default|GetAutoDemo)
    (bind lsa (Utilities|Casting|CastToLevelSequenceActor :Object (Actor|GetActorOfClass :ActorClass "/Script/LevelSequence.LevelSequenceActor"))
      (:then
        (bind st (Utilities|TimeManagement|QualifiedFrameTimeToSeconds (Sequencer|Player|GetCurrentTime :self (Class|LevelSequenceActor|GetSequencePlayer :self lsa))))
        {dbg}
        (CallFunction|DemoStep :T (- st (Variables|Default|GetDemoStartTime))))
      (:CastFailed
        (CallFunction|DemoStep :T (- (Utilities|Time|GetGameTimeinSeconds) (Variables|Default|GetDemoStartTime)))))))
""")
print(T.read_graph_dsl(g)[:1500])
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_loaded_asset(bp)
