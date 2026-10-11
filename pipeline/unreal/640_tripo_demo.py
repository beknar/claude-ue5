"""Showcase routine for BP_JRPG<CH>Character (cinematic copy only: bAutoDemo) + L_Meshy_Meadow_Cine set up with her as the demo actor.
Demo time T (sequence clock - DemoStartTime when a LevelSequenceActor plays, else game time):
  idle 0-3.5, walk 3.5-7.5, run 7.5-12.5 (jump 10.0), walk 12.5-14.0, stop -> idle to the end. Path follows the meadow trail
(same steering as the soldier / Meshy showcases). Args: CH"""
import sys, unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary; eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
CH = sys.argv[1] if len(sys.argv) > 1 else "Fem5"
bp = unreal.load_asset(f"/Game/JRPG/Game/BP_JRPG{CH}Character")
WALK, RUN = [float(v) for v in open(r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_" + CH.lower() + r"\speeds.txt").read().split()]
wr = WALK / RUN
cdo = unreal.get_default_object(bp.generated_class())
def has(n):
    try: cdo.get_editor_property(n); return True
    except Exception: return False
for name, typ in (("bAutoDemo", "bool"), ("DemoStartTime", "float"), ("DJump", "bool")):
    if not has(name): T.add_variable(bp, name, typ)
    if name in ("bAutoDemo", "DemoStartTime"): T.set_variable_instance_editable(bp, name, True)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
graphs = lambda: {x.get_name(): x for x in T.list_graphs(bp)}
if "DemoStep" not in graphs():
    g = T.add_function_graph(bp, "DemoStep"); T.add_function_param(g, "T", "float", True); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
code = f"""
(fn DemoStep (T)
  (bind loc (Transformation|GetActorLocation))
  (bind a (/ (.x loc) 2500.0))
  (bind side (+ (* 0.16 (Math|Trig|Cos(Radians) a)) (* (- (* 400.0 (Math|Trig|Sin(Radians) a)) (.y loc)) 0.002)))
  (bind dir (Math|Vector|Normalize (Math|Vector|MakeVector 1.0 side 0.0)))
  (bind s (select (< T 3.5) 0.0 (select (< T 7.5) {wr:.4f} (select (< T 12.5) 1.0 (select (< T 14.0) {wr:.4f} 0.0)))))
  (Pawn|Input|AddMovementInput :WorldDirection dir :ScaleValue s)
  (if (and (> T 10.0) (not (Variables|Default|GetDJump)))
    (Character|Jump)
    (Variables|Default|SetDJump true))
  (if (> T 10.3)
    (Character|StopJumping)))"""
assert code.count("(") == code.count(")")
T.write_graph_dsl(graphs()["DemoStep"], code); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
assert len(T.read_graph_dsl(graphs()["DemoStep"]).strip().splitlines()) > 1, "DemoStep empty"
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
for n in T.find_nodes(g, ""):
    if any(str(p.name) == "DeltaSeconds" for p in T.get_node_infos([n])[0].output_pins): T.delete_node(n)
NOW = "(Utilities|Time|GetGameTimeinSeconds)"
tick = f"""
(event EventTick (DeltaSeconds)
  (if (Variables|Default|GetAutoDemo)
    (bind lsa (Utilities|Casting|CastToLevelSequenceActor :Object (Actor|GetActorOfClass :ActorClass "/Script/LevelSequence.LevelSequenceActor"))
      (:then
        (CallFunction|DemoStep :T (- (Utilities|TimeManagement|QualifiedFrameTimeToSeconds (Sequencer|Player|GetCurrentTime :self (Class|LevelSequenceActor|GetSequencePlayer :self lsa))) (Variables|Default|GetDemoStartTime))))
      (:CastFailed
        (CallFunction|DemoStep :T (- {NOW} (Variables|Default|GetDemoStartTime)))))))
"""
assert tick.count("(") == tick.count(")")
T.write_graph_dsl(g, tick)
print("BP compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp), "| tick:", "DemoStep" in T.read_graph_dsl(g)); eal.save_loaded_asset(bp, only_if_is_dirty=False)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level("/Game/Meshy/Maps/L_Meshy_Meadow_Cine")
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Fig4_Demo": eas.destroy_actor(a)
demo = eas.spawn_actor_from_class(bp.generated_class(), unreal.Vector(0, 0, 90), unreal.Rotator(pitch=0, yaw=0, roll=0))
demo.set_actor_label("Fig4_Demo")                                      # (label the camera scripts look for)
demo.set_editor_property("auto_possess_ai", unreal.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED)
demo.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.DISABLED)
demo.set_editor_property("bAutoDemo", True); demo.set_editor_property("DemoStartTime", 1.5)
les.save_current_level()
print("cine demo actor:", demo.get_class().get_name(), demo.get_editor_property("bAutoDemo"), demo.get_editor_property("DemoStartTime"))
