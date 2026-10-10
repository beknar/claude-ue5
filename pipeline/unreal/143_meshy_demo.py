"""Showcase auto-demo for BP_MeshyCharacter (cinematic copy only: bAutoDemo). Clock = playing Level Sequence time
(else game time) minus DemoStartTime. Demo time: idle 0-2, walk 2-5, run 5-8, sprint 8-10.5 (jump 9.2),
walk 10.5-11.6, stop; jab 12.2, hook 13.8, kick 15.4."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary
bp = unreal.load_asset("/Game/Meshy/Game/BP_MeshyCharacter")
have = [str(v) for v in T.list_variables(bp)]
for name, typ in (("bAutoDemo", "bool"), ("DemoStartTime", "float"), ("DJump", "bool"), ("DJab", "bool"), ("DHook", "bool"), ("DKick", "bool")):
    if name not in have:
        T.add_variable(bp, name, typ)
        if name in ("bAutoDemo", "DemoStartTime"): T.set_variable_instance_editable(bp, name, True)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
gs = lambda: {x.get_name(): x for x in T.list_graphs(bp)}
if "DemoStep" not in gs():
    fg = T.add_function_graph(bp, "DemoStep"); T.add_function_param(fg, "T", "float", True)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
T.write_graph_dsl(gs()["DemoStep"], """
(fn DemoStep (T)
  (bind loc (Transformation|GetActorLocation))
  (bind a (/ (.x loc) 2500.0))
  (bind side (+ (* 0.16 (Math|Trig|Cos(Radians) a)) (* (- (* 400.0 (Math|Trig|Sin(Radians) a)) (.y loc)) 0.002)))
  (bind dir (Math|Vector|Normalize (Math|Vector|MakeVector 1.0 side 0.0)))
  (bind s (select (< T 2.0) 0.0 (select (< T 5.0) 0.241 (select (< T 8.0) 0.741 (select (< T 10.5) 1.0 (select (< T 11.6) 0.241 0.0))))))
  (Pawn|Input|AddMovementInput :WorldDirection dir :ScaleValue s)
  (if (and (> T 9.2) (not (Variables|Default|GetDJump)))
    (Character|Jump)
    (Variables|Default|SetDJump true))
  (if (> T 9.5)
    (Character|StopJumping))
  (if (and (> T 12.2) (not (Variables|Default|GetDJab)))
    (CallFunction|ActJab)
    (Variables|Default|SetDJab true))
  (if (and (> T 13.8) (not (Variables|Default|GetDHook)))
    (CallFunction|ActHook)
    (Variables|Default|SetDHook true))
  (if (and (> T 15.4) (not (Variables|Default|GetDKick)))
    (CallFunction|ActKick)
    (Variables|Default|SetDKick true)))""")
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
print(T.read_graph_dsl(gs()["DemoStep"])[:1500])
# Tick: demo branch first, idle variety otherwise (input-event nodes are left untouched)
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
for n in T.find_nodes(g, ""):
    if any(str(p.name) == "DeltaSeconds" for p in T.get_node_infos([n])[0].output_pins): T.delete_node(n)
for n in T.find_nodes(g, ""):      # orphans of the previous Tick body (keep events, input wiring and Act calls)
    t = str(T.get_node_infos([n])[0].type_id)
    # compiled calls to own functions report "|Act_Jab", not "CallFunction|ActJab" - keep both forms
    if not (t.startswith("AddEvent") or "Event" in t or "EnhancedActionEvents" in t or t.startswith("CallFunction|Act") or "|Act_" in t): T.delete_node(n)
NOW = "(Utilities|Time|GetGameTimeinSeconds)"
GROUNDED = "(< (Math|Vector|VectorLengthSquared (* (Transformation|GetVelocity) (Math|Vector|MakeVector 0.0 0.0 1.0))) 25.0)"
T.write_graph_dsl(g, f"""
(event EventTick (DeltaSeconds)
  (if (Variables|Default|GetAutoDemo)
    (bind lsa (Utilities|Casting|CastToLevelSequenceActor :Object (Actor|GetActorOfClass :ActorClass "/Script/LevelSequence.LevelSequenceActor"))
      (:then
        (CallFunction|DemoStep :T (- (Utilities|TimeManagement|QualifiedFrameTimeToSeconds (Sequencer|Player|GetCurrentTime :self (Class|LevelSequenceActor|GetSequencePlayer :self lsa))) (Variables|Default|GetDemoStartTime))))
      (:CastFailed
        (CallFunction|DemoStep :T (- {NOW} (Variables|Default|GetDemoStartTime)))))
    (else
      (bind spd (Math|Vector|VectorLengthXY (Transformation|GetVelocity)))
      (if (Variables|Default|GetIdleVariantActive)
        (if (or (> spd 5.0) (> {NOW} (Variables|Default|GetIdleVariantUntil)))
          (if (> spd 5.0)
            (Animation|StopAnimMontage))
          (Variables|Default|SetIdleVariantActive false))
        (elif (and (< spd 3.0) (and {GROUNDED} (>= {NOW} (Variables|Default|GetActionLockUntil))))
          (Variables|Default|SetIdleTimer (+ (Variables|Default|GetIdleTimer) DeltaSeconds))
          (if (> (Variables|Default|GetIdleTimer) 8.0)
            (Variables|Default|SetIdleTimer 0.0)
            (CallFunction|PlayIdleVariant))
          (else
            (Variables|Default|SetIdleTimer 0.0)))))))
""")
print("compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp)); eal.save_loaded_asset(bp)
print(T.read_graph_dsl(g)[:2200])
