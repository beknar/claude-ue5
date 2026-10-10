"""Wire Enhanced Input events (Started) to per-move functions on BP_MeshyCharacter."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary
bp = unreal.load_asset("/Game/Meshy/Game/BP_MeshyCharacter")
NOW = "(Utilities|Time|GetGameTimeinSeconds)"
GROUNDED = "(< (Math|Vector|VectorLengthSquared (* (Transformation|GetVelocity) (Math|Vector|MakeVector 0.0 0.0 1.0))) 25.0)"
M = lambda c: f'"/Game/Meshy/Anims/AM_Meshy_{c}.AM_Meshy_{c}"'
MOVES = (("IA_Jab", "Left_Jab_from_Guard"), ("IA_Hook", "Left_Short_Hook_from_Guard"), ("IA_Punch", "Boxing_Guard_Prep_Straight_Punch"),
         ("IA_Sweep", "Leg_Sweep"), ("IA_Kick", "Step_Step_Turn_Kick"), ("IA_TurnLeft", "Idle_Turn_Left"),
         ("IA_TurnRight", "Idle_Turn_Right"), ("IA_Stroll", "walking_2"), ("IA_IdleAnim", None))
graphs = lambda: {x.get_name(): x for x in T.list_graphs(bp)}
print("call ids:", [str(x) for x in T.find_node_types(unreal.BlueprintEditorLibrary.find_event_graph(bp), "Act_")][:12])
print("len ids:", [str(x) for x in T.find_node_types(unreal.BlueprintEditorLibrary.find_event_graph(bp), "VectorLength")][:8])
print("PlayIdleVariant:", T.read_graph_dsl(graphs()["PlayIdleVariant"])[:400])
for ia, clip in MOVES:
    name = "Act_" + ia[3:]
    if name not in graphs(): T.add_function_graph(bp, name)
    if clip:
        code = f"""
(fn {name} ()
  (if (and (>= {NOW} (Variables|Default|GetActionLockUntil)) {GROUNDED})
    (CallFunction|BeginAction :Len (Animation|PlayAnimMontage :AnimMontage {M(clip)}))))"""
    else:
        code = f"""
(fn {name} ()
  (if (and (not (Variables|Default|GetIdleVariantActive)) (and (>= {NOW} (Variables|Default|GetActionLockUntil)) (< (Math|Vector|VectorLengthXY (Transformation|GetVelocity)) 3.0)))
    (CallFunction|PlayIdleVariant)))"""
    T.write_graph_dsl(graphs()[name], code)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
for ia, _ in MOVES:
    print("Act_" + ia[3:], "->", T.read_graph_dsl(graphs()["Act_" + ia[3:]])[:160].replace("\n", " "))
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
for n in T.find_nodes(g, ""):                      # clear previous wiring
    t = str(T.get_node_infos([n])[0].type_id)
    if "EnhancedActionEvents" in t or t.startswith("CallFunction|Act"): T.delete_node(n)
for n in T.find_nodes(g, ""):
    if any(str(p.name) == "DeltaSeconds" for p in T.get_node_infos([n])[0].output_pins): T.delete_node(n)
T.write_graph_dsl(g, f"""
(event EventTick (DeltaSeconds)
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
        (Variables|Default|SetIdleTimer 0.0)))))
""")
def pin(info, name, out):
    for p in (info.output_pins if out else info.input_pins):
        if str(p.name) == name: return p.pin_id
    raise KeyError(f"{name}: {[str(p.name) for p in (info.output_pins if out else info.input_pins)]}")
for k, (ia, _) in enumerate(MOVES):
    ev = T.create_node(g, f"Input|EnhancedActionEvents|{ia}", unreal.IntPoint(0, 400 + 260 * k))
    call = T.create_node(g, f"CallFunction|Act{ia[3:]}", unreal.IntPoint(450, 400 + 260 * k))
    ei, ci = T.get_node_infos([ev])[0], T.get_node_infos([call])[0]
    T.connect_pins(pin(ei, "Started", True), pin(ci, "execute", False))
    print("wired", ia, [str(p.name) for p in ei.output_pins][:6])
print("compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp))
eal.save_loaded_asset(bp)
print(T.read_graph_dsl(g)[:2500])
