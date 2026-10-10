"""BP_FFCharacter: Tripo anime female on the template third-person character. WASD walk (285 cm/s), Shift run (570 cm/s),
Space jump; unarmed moves on keys (1/LMB Attack_01, 2/RMB Attack_02, 3 Attack_03, 4 Dash, 5 Charged attack);
sequence-clocked showcase routine for the cinematic copy (bAutoDemo)."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
PATH = "/Game/FF/Game/BP_FFCharacter"
WALK, RUN, HALF = 285.0, 570.0, 83.0
if eal.does_asset_exist(PATH): eal.delete_asset(PATH)
f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter").generated_class())
bp = at.create_asset("BP_FFCharacter", "/Game/FF/Game", unreal.Blueprint, f)
H = {str(lib.get_variable_name(lib.get_data(h))): h for h in sds.k2_gather_subobject_data_for_blueprint(bp)}
obj = lambda h: lib.get_object_for_blueprint(lib.get_data(h), bp)
mesh = obj(H["Mesh"])
mesh.set_skeletal_mesh_asset(unreal.load_asset("/Game/FF/Character/SK_FF_Anime"))
mesh.set_editor_property("anim_class", eal.load_blueprint_class("/Game/FF/Locomotion/Anims/ABP_Unarmed_FF"))
mesh.set_editor_property("relative_location", unreal.Vector(0, 0, -HALF))
mesh.set_editor_property("relative_rotation", unreal.Rotator(pitch=0, yaw=-90, roll=0))
mesh.set_editor_property("visibility_based_anim_tick_option", unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
cap = obj(H["CapsuleComponent"]); cap.set_editor_property("capsule_half_height", HALF); cap.set_editor_property("capsule_radius", 28.0)
cm = obj(H["CharacterMovement"])
for k, v in {"max_walk_speed": RUN, "max_acceleration": 1400.0, "braking_deceleration_walking": 1100.0, "ground_friction": 7.0,
             "jump_z_velocity": 460.0, "air_control": 0.3, "rotation_rate": unreal.Rotator(pitch=0, yaw=500, roll=0), "min_analog_walk_speed": 0.0}.items():
    cm.set_editor_property(k, v)
boom = obj(H["CameraBoom"])
boom.set_editor_property("target_arm_length", 330.0); boom.set_editor_property("socket_offset", unreal.Vector(0, 35, 45))
boom.set_editor_property("enable_camera_lag", True); boom.set_editor_property("camera_lag_speed", 9.0)
for name, typ in (("ActionLockUntil", "float"), ("bAutoDemo", "bool"), ("DemoStartTime", "float"), ("DJump", "bool"),
                  ("DA1", "bool"), ("DA2", "bool"), ("DA3", "bool"), ("DCharge", "bool")):
    T.add_variable(bp, name, typ)
    if name in ("bAutoDemo", "DemoStartTime"): T.set_variable_instance_editable(bp, name, True)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
graphs = lambda: {x.get_name(): x for x in T.list_graphs(bp)}
def fn(name, params, code):
    if name not in graphs():
        g = T.add_function_graph(bp, name)
        for p in params: T.add_function_param(g, p, "float", True)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    T.write_graph_dsl(graphs()[name], code); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
NOW = "(Utilities|Time|GetGameTimeinSeconds)"
GROUNDED = "(< (Math|Vector|VectorLengthSquared (* (Transformation|GetVelocity) (Math|Vector|MakeVector 0.0 0.0 1.0))) 25.0)"
M = lambda c: f'"/Game/FF/Anims/AM_FF_{c}.AM_FF_{c}"'
fn("BeginAction", ["Len"], f"""
(fn BeginAction (Len)
  (Variables|Default|SetActionLockUntil (+ {NOW} (* Len 0.9))))""")
fn("DoAction", ["Which"], f"""
(fn DoAction (Which)
  (if (and (>= {NOW} (Variables|Default|GetActionLockUntil)) {GROUNDED})
    (if (< Which 0.5)
      (CallFunction|BeginAction :Len (Animation|PlayAnimMontage :AnimMontage {M('Attack_01')}))
      (elif (< Which 1.5)
        (CallFunction|BeginAction :Len (Animation|PlayAnimMontage :AnimMontage {M('Attack_02')})))
      (elif (< Which 2.5)
        (CallFunction|BeginAction :Len (Animation|PlayAnimMontage :AnimMontage {M('Attack_03')})))
      (elif (< Which 3.5)
        (CallFunction|BeginAction :Len (Animation|PlayAnimMontage :AnimMontage {M('Dash')})))
      (else
        (CallFunction|BeginAction :Len (Animation|PlayAnimMontage :AnimMontage {M('ChargedAttack')}))))))""")
wr = WALK / RUN
T.add_function_graph(bp, "MoveScale"); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
T.write_graph_dsl(graphs()["MoveScale"], f"""
(fn MoveScale (X Y)
  (bind s (select (Input|EnhancedActionValues|IA_Sprint) 1.0 {wr:.4f}))
  (bind k (select (< {NOW} (Variables|Default|GetActionLockUntil)) 0.0 (/ s (Math|Float|Max(Float) (Math|Float|Sqrt (+ (* X X) (* Y Y))) 1.0))))
  (return (* X k) (* Y k)))""")
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
# showcase routine (demo time): idle 0-2, walk 2-5, run 5-8.2 (jump 6.8), walk 8.2-9.4, stop;
# Attack_01 10.4, Attack_02 11.5, Attack_03 12.7, charged attack 14.6
fn("DemoStep", ["T"], f"""
(fn DemoStep (T)
  (bind loc (Transformation|GetActorLocation))
  (bind a (/ (.x loc) 2500.0))
  (bind side (+ (* 0.16 (Math|Trig|Cos(Radians) a)) (* (- (* 400.0 (Math|Trig|Sin(Radians) a)) (.y loc)) 0.002)))
  (bind dir (Math|Vector|Normalize (Math|Vector|MakeVector 1.0 side 0.0)))
  (bind s (select (< T 2.0) 0.0 (select (< T 5.0) {wr:.4f} (select (< T 8.2) 1.0 (select (< T 9.4) {wr:.4f} 0.0)))))
  (Pawn|Input|AddMovementInput :WorldDirection dir :ScaleValue s)
  (if (and (> T 6.8) (not (Variables|Default|GetDJump)))
    (Character|Jump)
    (Variables|Default|SetDJump true))
  (if (> T 7.1)
    (Character|StopJumping))
  (if (and (> T 10.4) (not (Variables|Default|GetDA1)))
    (CallFunction|DoAction :Which 0.0)
    (Variables|Default|SetDA1 true))
  (if (and (> T 11.5) (not (Variables|Default|GetDA2)))
    (CallFunction|DoAction :Which 1.0)
    (Variables|Default|SetDA2 true))
  (if (and (> T 12.7) (not (Variables|Default|GetDA3)))
    (CallFunction|DoAction :Which 2.0)
    (Variables|Default|SetDA3 true))
  (if (and (> T 14.6) (not (Variables|Default|GetDCharge)))
    (CallFunction|DoAction :Which 4.0)
    (Variables|Default|SetDCharge true)))""")
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
for n in T.find_nodes(g, ""):
    if any(str(p.name) == "DeltaSeconds" for p in T.get_node_infos([n])[0].output_pins): T.delete_node(n)
T.write_graph_dsl(g, f"""
(event EventTick (DeltaSeconds)
  (if (Variables|Default|GetAutoDemo)
    (bind lsa (Utilities|Casting|CastToLevelSequenceActor :Object (Actor|GetActorOfClass :ActorClass "/Script/LevelSequence.LevelSequenceActor"))
      (:then
        (CallFunction|DemoStep :T (- (Utilities|TimeManagement|QualifiedFrameTimeToSeconds (Sequencer|Player|GetCurrentTime :self (Class|LevelSequenceActor|GetSequencePlayer :self lsa))) (Variables|Default|GetDemoStartTime))))
      (:CastFailed
        (CallFunction|DemoStep :T (- {NOW} (Variables|Default|GetDemoStartTime)))))))
""")
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
# input: Started -> DoAction(Which)
def info(n): return T.get_node_infos([n])[0]
def pin(i, name, out):
    for p in (i.output_pins if out else i.input_pins):
        if str(p.name) == name: return p.pin_id
    raise KeyError(name)
for k, (ia, which) in enumerate((("IA_Jab", 0), ("IA_Hook", 1), ("IA_Punch", 2), ("IA_Sweep", 3), ("IA_Kick", 4))):
    ev = T.create_node(g, f"Input|EnhancedActionEvents|{ia}", unreal.IntPoint(-1200, 1600 + 220 * k))
    call = T.create_node(g, "CallFunction|DoAction", unreal.IntPoint(-750, 1600 + 220 * k))
    T.connect_pins(pin(info(ev), "Started", True), pin(info(call), "execute", False))
    T.set_pin_value(pin(info(call), "Which", False), f"{which}.0")
for name in ("DoAction", "DemoStep", "MoveScale"):
    print("==", name, T.read_graph_dsl(graphs()[name])[:140].replace("\n", " "))
nodes = [str(info(n).type_id) for n in T.find_nodes(g, "")]
print("events:", sum("EnhancedActionEvents" in t for t in nodes), "DoAction calls:", sum("DoAction" in t for t in nodes), "tick:", any("EventTick" in t for t in nodes))
print("compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp)); eal.save_loaded_asset(bp)
# game mode using this pawn
GM = "/Game/FF/Game/BP_FFGameMode"
if eal.does_asset_exist(GM): eal.delete_asset(GM)
gm = eal.duplicate_asset("/Game/Soldier/Game/BP_SoldierGameMode", GM)
unreal.get_default_object(gm.generated_class()).set_editor_property("default_pawn_class", bp.generated_class())
unreal.BlueprintEditorLibrary.compile_blueprint(gm); eal.save_loaded_asset(gm)
gm = unreal.load_asset(GM)
print("game mode pawn:", unreal.get_default_object(gm.generated_class()).get_editor_property("default_pawn_class"))
