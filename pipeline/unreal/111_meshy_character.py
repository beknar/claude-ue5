"""BP_MeshyCharacter: template third-person character with the Meshy biped, retargeted locomotion AnimBP,
walk/run speeds matched to her clips, action montages on keys, idle variety, movement lock during moves."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
PATH = "/Game/Meshy/Game/BP_MeshyCharacter"
if eal.does_asset_exist(PATH): eal.delete_asset(PATH)
parent = unreal.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", parent.generated_class())
bp = at.create_asset("BP_MeshyCharacter", "/Game/Meshy/Game", unreal.Blueprint, f)
H = {str(lib.get_variable_name(lib.get_data(h))): h for h in sds.k2_gather_subobject_data_for_blueprint(bp)}
def obj(h): return lib.get_object_for_blueprint(lib.get_data(h), bp)
mesh = obj(H["Mesh"])
mesh.set_skeletal_mesh_asset(unreal.load_asset("/Game/Meshy/Character/SK_Meshy_Biped"))
ABP = "/Game/Meshy/Locomotion/Anims/ABP_Unarmed_Meshy1" if eal.does_asset_exist("/Game/Meshy/Locomotion/Anims/ABP_Unarmed_Meshy1") else "/Game/Meshy/Locomotion/Anims/ABP_Unarmed_Meshy"
print("anim BP", ABP)
mesh.set_editor_property("anim_class", eal.load_blueprint_class(ABP))
mesh.set_editor_property("relative_location", unreal.Vector(0, 0, -86.0))
mesh.set_editor_property("relative_rotation", unreal.Rotator(pitch=0, yaw=-90, roll=0))
mesh.set_editor_property("visibility_based_anim_tick_option", unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
cap = obj(H["CapsuleComponent"]); cap.set_editor_property("capsule_half_height", 86.0); cap.set_editor_property("capsule_radius", 28.0)
cm = obj(H["CharacterMovement"])
for k, v in {"max_walk_speed": 430.0, "max_acceleration": 1100.0, "braking_deceleration_walking": 900.0, "ground_friction": 6.0,
             "jump_z_velocity": 420.0, "air_control": 0.3, "rotation_rate": unreal.Rotator(pitch=0, yaw=480, roll=0),
             "min_analog_walk_speed": 0.0}.items():
    cm.set_editor_property(k, v)
boom = obj(H["CameraBoom"])
boom.set_editor_property("target_arm_length", 340.0); boom.set_editor_property("socket_offset", unreal.Vector(0, 35, 40))
boom.set_editor_property("enable_camera_lag", True); boom.set_editor_property("camera_lag_speed", 9.0)
for name, typ in (("ActionLockUntil", "float"), ("IdleTimer", "float"), ("IdleVariantActive", "bool"), ("IdleVariantUntil", "float")):
    T.add_variable(bp, name, typ)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)

def fn(name, params, code):
    g = T.add_function_graph(bp, name)
    for p in params: T.add_function_param(g, p, "float", True)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    g = [x for x in T.list_graphs(bp) if x.get_name() == name][0]
    T.write_graph_dsl(g, code); print("==", name, "\n", T.read_graph_dsl(g)[:600])
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
NOW = "(Utilities|Time|GetGameTimeinSeconds)"
fn("BeginAction", ["Len"], f"""
(fn BeginAction (Len)
  (Variables|Default|SetIdleVariantActive false)
  (Variables|Default|SetIdleTimer 0.0)
  (Variables|Default|SetActionLockUntil (+ {NOW} (* Len 0.85))))""")
fn("BeginIdleVariant", ["Len"], f"""
(fn BeginIdleVariant (Len)
  (Variables|Default|SetIdleVariantActive true)
  (Variables|Default|SetIdleVariantUntil (+ {NOW} (- Len 0.3))))""")
M = lambda c: f'"/Game/Meshy/Anims/AM_Meshy_{c}.AM_Meshy_{c}"'
fn("PlayIdleVariant", [], f"""
(fn PlayIdleVariant ()
  (switch int (Math|Random|RandomIntegerinRange 0 3)
    (:0 (CallFunction|BeginIdleVariant :Len (Animation|PlayAnimMontage :AnimMontage {M('Idle_4')})))
    (:1 (CallFunction|BeginIdleVariant :Len (Animation|PlayAnimMontage :AnimMontage {M('Idle_6')})))
    (:2 (CallFunction|BeginIdleVariant :Len (Animation|PlayAnimMontage :AnimMontage {M('Idle_7')})))
    (:Default (CallFunction|BeginIdleVariant :Len (Animation|PlayAnimMontage :AnimMontage {M('Idle_5')})))))""")
# movement: walk = 140/430 of max speed, Shift = run; frozen while a move plays
mg = T.add_function_graph(bp, "MoveScale")
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
mg = [x for x in T.list_graphs(bp) if x.get_name() == "MoveScale"][0]
print("MoveScale override entry:", T.read_graph_dsl(mg)[:200])
T.write_graph_dsl(mg, f"""
(fn MoveScale (X Y)
  (bind s (select (Input|EnhancedActionValues|IA_Sprint) 1.0 0.326))
  (bind k (select (< {NOW} (Variables|Default|GetActionLockUntil)) 0.0 (/ s (Math|Float|Max(Float) (Math|Float|Sqrt (+ (* X X) (* Y Y))) 1.0))))
  (return (* X k) (* Y k)))""")
print("== MoveScale\n", T.read_graph_dsl(mg)[:500])
unreal.BlueprintEditorLibrary.compile_blueprint(bp)

g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
for n in T.find_nodes(g, ""):
    i = T.get_node_infos([n])[0]
    if any(str(p.name) == "DeltaSeconds" for p in i.output_pins): T.delete_node(n)
GROUNDED = "(< (Math|Float|Abs (.z (Transformation|GetVelocity))) 5.0)"
def action(ia, clip):
    return f"""
(event Input|EnhancedActionEvents|{ia} (ActionValue ElapsedSeconds TriggeredSeconds InputAction)
  (if (and (>= {NOW} (Variables|Default|GetActionLockUntil)) {GROUNDED})
    (CallFunction|BeginAction :Len (Animation|PlayAnimMontage :AnimMontage {M(clip)}))))"""
code = "".join(action(ia, c) for ia, c in (("IA_Jab", "Left_Jab_from_Guard"), ("IA_Hook", "Left_Short_Hook_from_Guard"),
       ("IA_Punch", "Boxing_Guard_Prep_Straight_Punch"), ("IA_Sweep", "Leg_Sweep"), ("IA_Kick", "Step_Step_Turn_Kick"),
       ("IA_TurnLeft", "Idle_Turn_Left"), ("IA_TurnRight", "Idle_Turn_Right"), ("IA_Stroll", "walking_2")))
code += f"""
(event Input|EnhancedActionEvents|IA_IdleAnim (ActionValue ElapsedSeconds TriggeredSeconds InputAction)
  (if (and (not (Variables|Default|GetIdleVariantActive)) (and (>= {NOW} (Variables|Default|GetActionLockUntil)) (< (Math|Vector|VectorLengthXY (Transformation|GetVelocity)) 3.0)))
    (CallFunction|PlayIdleVariant)))

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
"""
T.write_graph_dsl(g, code)
print("== EventGraph\n", T.read_graph_dsl(g)[:3000])
print("compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp))
eal.save_loaded_asset(bp)
