"""BP_Fig4Character auto-demo (for the cinematic): when bAutoDemo, follow the trail and perform
idle 0-2 s, walk 2-6.5 s, run 6.5-13 s (jump at 9.5 s), walk 13-15 s, then stop. Clock = game time - DemoStartTime."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
bp = unreal.load_asset("/Game/Fig4/Game/BP_Fig4Character")
have = [str(v) for v in T.list_variables(bp)]
for name, typ in (("bAutoDemo", "bool"), ("DemoStartTime", "float"), ("bDemoJumped", "bool")):
    if name not in have:
        T.add_variable(bp, name, typ)
        if name != "bDemoJumped": T.set_variable_instance_editable(bp, name, True)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
print([str(x) for x in T.find_node_types(g, "Demo")])
for n in T.find_nodes(g, ""):
    i = T.get_node_infos([n])[0]
    if any(str(p.name) == "DeltaSeconds" for p in i.output_pins): T.delete_node(n)
code = """
(event EventTick (DeltaSeconds)
  (if (Variables|Default|GetAutoDemo)
    (bind t (- (Utilities|Time|GetGameTimeinSeconds) (Variables|Default|GetDemoStartTime)))
    (bind loc (Transformation|GetActorLocation))
    (bind px (.x loc))
    (bind a (/ px 2500.0))
    (bind side (+ (* 0.16 (Math|Trig|Cos(Radians) a)) (* (- (* 400.0 (Math|Trig|Sin(Radians) a)) (.y loc)) 0.002)))
    (bind dir (Math|Vector|Normalize (Math|Vector|MakeVector 1.0 side 0.0)))
    (bind s (select (< t 2.0) 0.0 (select (< t 6.5) 0.383 (select (< t 13.0) 1.0 (select (< t 15.0) 0.383 0.0)))))
    (Pawn|Input|AddMovementInput :WorldDirection dir :ScaleValue s)
    (if (and (> t 9.5) (not (Variables|Default|GetDemoJumped)))
      (Character|Jump)
      (Variables|Default|SetDemoJumped true))
    (if (> t 9.8)
      (Character|StopJumping))))
"""
T.write_graph_dsl(g, code)
print(T.read_graph_dsl(g))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_loaded_asset(bp)
