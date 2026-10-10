"""BP_FF2Character: animated Tripo anime female on the template third-person character. WASD walk (Walk, 100 cm/s),
Shift run (Run, 350 cm/s), Space jump (Jump clip in the air); 1/LMB Box, 2/RMB Cast spell, 3 Shoot, 4 Dance
(Shoot/Dance are long: no movement lock, cancelled by moving or jumping); sequence-clocked showcase routine (bAutoDemo)."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
PATH = "/Game/FF2/Game/BP_FF2Character"
WALK, RUN, HALF = 102.3, 337.0, 83.0       # locked stance speeds after 286_ff2_foot_fix
if eal.does_asset_exist(PATH): eal.delete_asset(PATH)
f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter").generated_class())
bp = at.create_asset("BP_FF2Character", "/Game/FF2/Game", unreal.Blueprint, f)
H = {str(lib.get_variable_name(lib.get_data(h))): h for h in sds.k2_gather_subobject_data_for_blueprint(bp)}
obj = lambda h: lib.get_object_for_blueprint(lib.get_data(h), bp)
mesh = obj(H["Mesh"])
mesh.set_skeletal_mesh_asset(unreal.load_asset("/Game/FF2/Character/SK_FF2_Anime"))
mesh.set_editor_property("anim_class", eal.load_blueprint_class("/Game/FF2/Locomotion/Anims/ABP_Unarmed_FF2"))
mesh.set_editor_property("relative_location", unreal.Vector(0, 0, -HALF - 2.2))     # CharacterMovement keeps the capsule ~2.2 cm above the floor
mesh.set_editor_property("relative_rotation", unreal.Rotator(pitch=0, yaw=-90, roll=0))
mesh.set_editor_property("visibility_based_anim_tick_option", unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
cap = obj(H["CapsuleComponent"]); cap.set_editor_property("capsule_half_height", HALF); cap.set_editor_property("capsule_radius", 28.0)
cm = obj(H["CharacterMovement"])
for k, v in {"max_walk_speed": RUN, "max_acceleration": 1100.0, "braking_deceleration_walking": 900.0, "ground_friction": 7.0,
             "jump_z_velocity": 470.0, "air_control": 0.3, "rotation_rate": unreal.Rotator(pitch=0, yaw=480, roll=0), "min_analog_walk_speed": 0.0}.items():
    cm.set_editor_property(k, v)
boom = obj(H["CameraBoom"])
boom.set_editor_property("target_arm_length", 330.0); boom.set_editor_property("socket_offset", unreal.Vector(0, 35, 45))
boom.set_editor_property("enable_camera_lag", True); boom.set_editor_property("camera_lag_speed", 9.0)
for name, typ in (("ActionLockUntil", "float"), ("LongActive", "bool"), ("bAutoDemo", "bool"), ("DemoStartTime", "float"),
                  ("DJump", "bool"), ("DBox", "bool"), ("DCast", "bool")):
    T.add_variable(bp, name, typ)
    if name in ("bAutoDemo", "DemoStartTime"): T.set_variable_instance_editable(bp, name, True)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
graphs = lambda: {x.get_name(): x for x in T.list_graphs(bp)}
def fn(name, params, code):
    assert code.count("(") == code.count(")"), name
    if name not in graphs():
        g = T.add_function_graph(bp, name)
        for p in params: T.add_function_param(g, p, "float", True)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    T.write_graph_dsl(graphs()[name], code); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    body = T.read_graph_dsl(graphs()[name]); assert len(body.strip().splitlines()) > 1, f"{name} body empty (see LogScript)"
NOW = "(Utilities|Time|GetGameTimeinSeconds)"
GROUNDED = "(< (Math|Vector|VectorLengthSquared (* (Transformation|GetVelocity) (Math|Vector|MakeVector 0.0 0.0 1.0))) 25.0)"
PM = lambda c: f'(Animation|PlayAnimMontage :AnimMontage "/Game/FF2/Anims/AM_FF2_{c}.AM_FF2_{c}")'
fn("BeginAction", ["Len"], f"""
(fn BeginAction (Len)
  (Variables|Default|SetLongActive false)
  (Variables|Default|SetActionLockUntil (+ {NOW} (* Len 0.92))))""")
fn("BeginLong", ["Len"], f"""
(fn BeginLong (Len)
  (Variables|Default|SetLongActive true))""")
chain = f"(else (CallFunction|BeginLong :Len {PM('Dance')}))"     # elif nests as the last form of the previous branch
chain = f"(elif (< Which 2.5) (CallFunction|BeginLong :Len {PM('Shoot')}) {chain})"
chain = f"(elif (< Which 1.5) (CallFunction|BeginAction :Len {PM('CastSpell')}) {chain})"
fn("DoAction", ["Which"], f"""
(fn DoAction (Which)
  (if (and (>= {NOW} (Variables|Default|GetActionLockUntil)) {GROUNDED})
    (if (< Which 0.5) (CallFunction|BeginAction :Len {PM('Box')}) {chain})))""")
wr = WALK / RUN
T.add_function_graph(bp, "MoveScale"); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
T.write_graph_dsl(graphs()["MoveScale"], f"""
(fn MoveScale (X Y)
  (bind s (select (Input|EnhancedActionValues|IA_Sprint) 1.0 {wr:.4f}))
  (bind k (select (< {NOW} (Variables|Default|GetActionLockUntil)) 0.0 (/ s (Math|Float|Max(Float) (Math|Float|Sqrt (+ (* X X) (* Y Y))) 1.0))))
  (return (* X k) (* Y k)))""")
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
# showcase routine (demo time): idle 0-2, walk 2-5, run 5-9 (jump 7.0), walk 9-10.2, stop; Box 10.6, Cast spell 12.9
fn("DemoStep", ["T"], f"""
(fn DemoStep (T)
  (bind loc (Transformation|GetActorLocation))
  (bind a (/ (.x loc) 2500.0))
  (bind side (+ (* 0.16 (Math|Trig|Cos(Radians) a)) (* (- (* 400.0 (Math|Trig|Sin(Radians) a)) (.y loc)) 0.002)))
  (bind dir (Math|Vector|Normalize (Math|Vector|MakeVector 1.0 side 0.0)))
  (bind s (select (< T 2.0) 0.0 (select (< T 5.0) {wr:.4f} (select (< T 9.0) 1.0 (select (< T 10.2) {wr:.4f} 0.0)))))
  (Pawn|Input|AddMovementInput :WorldDirection dir :ScaleValue s)
  (if (and (> T 7.0) (not (Variables|Default|GetDJump)))
    (Character|Jump)
    (Variables|Default|SetDJump true))
  (if (> T 7.3)
    (Character|StopJumping))
  (if (and (> T 10.6) (not (Variables|Default|GetDBox)))
    (CallFunction|DoAction :Which 0.0)
    (Variables|Default|SetDBox true))
  (if (and (> T 12.9) (not (Variables|Default|GetDCast)))
    (CallFunction|DoAction :Which 1.0)
    (Variables|Default|SetDCast true)))""")
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
for n in T.find_nodes(g, ""):
    if any(str(p.name) == "DeltaSeconds" for p in T.get_node_infos([n])[0].output_pins): T.delete_node(n)
tick = f"""
(event EventTick (DeltaSeconds)
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
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
def info(n): return T.get_node_infos([n])[0]
def pin(i, name, out):
    for p in (i.output_pins if out else i.input_pins):
        if str(p.name) == name: return p.pin_id
    raise KeyError(name)
for k, (ia, which) in enumerate((("IA_Jab", 0), ("IA_Hook", 1), ("IA_Punch", 2), ("IA_Sweep", 3))):
    ev = T.create_node(g, f"Input|EnhancedActionEvents|{ia}", unreal.IntPoint(-1200, 1600 + 220 * k))
    call = T.create_node(g, "CallFunction|DoAction", unreal.IntPoint(-750, 1600 + 220 * k))
    T.connect_pins(pin(info(ev), "Started", True), pin(info(call), "execute", False))
    T.set_pin_value(pin(info(call), "Which", False), f"{which}.0")
nodes = [str(info(n).type_id) for n in T.find_nodes(g, "")]
print("events:", sum("EnhancedActionEvents" in t for t in nodes), "DoAction calls:", sum("DoAction" in t for t in nodes),
      "tick:", any("EventTick" in t for t in nodes), "StopAnimMontage:", "StopAnimMontage" in T.read_graph_dsl(g))
print("DoAction:", " ".join(T.read_graph_dsl(graphs()["DoAction"]).split())[:400])
print("compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp)); eal.save_loaded_asset(bp)
GM = "/Game/FF2/Game/BP_FF2GameMode"
if eal.does_asset_exist(GM): eal.delete_asset(GM)
gm = eal.duplicate_asset("/Game/Soldier/Game/BP_SoldierGameMode", GM)
unreal.get_default_object(gm.generated_class()).set_editor_property("default_pawn_class", bp.generated_class())
unreal.BlueprintEditorLibrary.compile_blueprint(gm); eal.save_loaded_asset(gm)
print("game mode pawn:", unreal.get_default_object(unreal.load_asset(GM).generated_class()).get_editor_property("default_pawn_class").get_name())
