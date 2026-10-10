"""BP_SoldierCharacter: Dystopia Soldier 02 on the template third-person character. WASD walk (02_Walk, 90 cm/s),
Shift run (Run_Fast, 410 cm/s), Space jump; idle flourishes (Idle_02/03) after 8 s still; sequence-clocked showcase
routine for the cinematic copy (bAutoDemo)."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
PATH = "/Game/Soldier/Game/BP_SoldierCharacter"
WALK, RUN = 90.0, 410.0
if eal.does_asset_exist(PATH): eal.delete_asset(PATH)
f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter").generated_class())
bp = at.create_asset("BP_SoldierCharacter", "/Game/Soldier/Game", unreal.Blueprint, f)
H = {str(lib.get_variable_name(lib.get_data(h))): h for h in sds.k2_gather_subobject_data_for_blueprint(bp)}
obj = lambda h: lib.get_object_for_blueprint(lib.get_data(h), bp)
mesh = obj(H["Mesh"])
mesh.set_skeletal_mesh_asset(unreal.load_asset("/Game/Soldier/Character/SK_Dystopia_Soldier_02"))
mesh.set_editor_property("anim_class", eal.load_blueprint_class("/Game/Soldier/Locomotion/Anims/ABP_Unarmed_Soldier"))
mesh.set_editor_property("relative_location", unreal.Vector(0, 0, -92.0))
mesh.set_editor_property("relative_rotation", unreal.Rotator(pitch=0, yaw=-90, roll=0))
mesh.set_editor_property("visibility_based_anim_tick_option", unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
cap = obj(H["CapsuleComponent"]); cap.set_editor_property("capsule_half_height", 92.0); cap.set_editor_property("capsule_radius", 32.0)
cm = obj(H["CharacterMovement"])
for k, v in {"max_walk_speed": RUN, "max_acceleration": 1000.0, "braking_deceleration_walking": 900.0, "ground_friction": 6.0,
             "jump_z_velocity": 440.0, "air_control": 0.3, "rotation_rate": unreal.Rotator(pitch=0, yaw=420, roll=0), "min_analog_walk_speed": 0.0}.items():
    cm.set_editor_property(k, v)
boom = obj(H["CameraBoom"])
boom.set_editor_property("target_arm_length", 360.0); boom.set_editor_property("socket_offset", unreal.Vector(0, 40, 50))
boom.set_editor_property("enable_camera_lag", True); boom.set_editor_property("camera_lag_speed", 9.0)
for name, typ in (("ActionLockUntil", "float"), ("IdleTimer", "float"), ("IdleVariantActive", "bool"), ("IdleVariantUntil", "float"),
                  ("bAutoDemo", "bool"), ("DemoStartTime", "float"), ("DJump", "bool"), ("DReload", "bool"), ("DShot", "bool")):
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
M = lambda c: f'"/Game/Soldier/Anims/AM_Soldier_{c}.AM_Soldier_{c}"'
fn("BeginAction", ["Len"], f"""
(fn BeginAction (Len)
  (Variables|Default|SetIdleVariantActive false)
  (Variables|Default|SetIdleTimer 0.0)
  (Variables|Default|SetActionLockUntil (+ {NOW} (* Len 0.9))))""")
fn("BeginIdleVariant", ["Len"], f"""
(fn BeginIdleVariant (Len)
  (Variables|Default|SetIdleVariantActive true)
  (Variables|Default|SetIdleVariantUntil (+ {NOW} (- Len 0.3))))""")
fn("PlayIdleVariant", [], f"""
(fn PlayIdleVariant ()
  (switch int (Math|Random|RandomIntegerinRange 0 1)
    (:0 (CallFunction|BeginIdleVariant :Len (Animation|PlayAnimMontage :AnimMontage {M('Idle_02')})))
    (:Default (CallFunction|BeginIdleVariant :Len (Animation|PlayAnimMontage :AnimMontage {M('Idle_03')})))))""")
fn("DoAction", ["Which"], f"""
(fn DoAction (Which)
  (if (and (>= {NOW} (Variables|Default|GetActionLockUntil)) {GROUNDED})
    (if (< Which 0.5)
      (CallFunction|BeginAction :Len (Animation|PlayAnimMontage :AnimMontage {M('02_Reload')}))
      (else
        (CallFunction|BeginAction :Len (Animation|PlayAnimMontage :AnimMontage {M('02_Shot')}))))))""")
wr = WALK / RUN
mg = T.add_function_graph(bp, "MoveScale"); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
T.write_graph_dsl(graphs()["MoveScale"], f"""
(fn MoveScale (X Y)
  (bind s (select (Input|EnhancedActionValues|IA_Sprint) 1.0 {wr:.4f}))
  (bind k (select (< {NOW} (Variables|Default|GetActionLockUntil)) 0.0 (/ s (Math|Float|Max(Float) (Math|Float|Sqrt (+ (* X X) (* Y Y))) 1.0))))
  (return (* X k) (* Y k)))""")
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
# showcase routine (demo time): idle 0-2, walk 2-5, run 5-9 (jump 7.0), walk 9-10.2, stop; reload 11.0, flamethrower 13.7
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
  (if (and (> T 11.0) (not (Variables|Default|GetDReload)))
    (CallFunction|DoAction :Which 0.0)
    (Variables|Default|SetDReload true))
  (if (and (> T 13.7) (not (Variables|Default|GetDShot)))
    (CallFunction|DoAction :Which 1.0)
    (Variables|Default|SetDShot true)))""")
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
for name in ("PlayIdleVariant", "DoAction", "DemoStep", "MoveScale"):
    print("==", name, T.read_graph_dsl(graphs()[name])[:160].replace("\n", " "))
print("tick:", "EventTick" in T.read_graph_dsl(g))
print("compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp)); eal.save_loaded_asset(bp)
