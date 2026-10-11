"""BP_JRPGFem1Character: the Meshy JRPG girl on the template third-person character, driven entirely by the Dystopia Soldier's
retargeted animation set (510). Same controls as BP_SoldierCharacter - WASD walk, Shift run (Run_Fast), Space jump, idle
flourishes (Idle_02/03) after 8 s standing still - plus the soldier's action clips on the number keys:
1/LMB fire (02_Shot), 2/RMB reload (02_Reload), 3 Attack_01, 4 Attack_02, 5 Get_Hit, 6 idle flourish.
Walk/run speeds = her measured stance-foot speeds (SourceArt/jrpg_fem1/speeds.txt). BP_JRPGFem1GameMode spawns her; it is set
as L_Meshy_Meadow's game mode."""
import sys, unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
SET = sys.argv[1] if len(sys.argv) > 1 else "soldier"         # soldier (510) | ff (540: the FF anime showcase set)
CH = sys.argv[2] if len(sys.argv) > 2 else "Fem1"              # Fem1 | Fem3
FSX = "_JRPGFF" if CH == "Fem1" else f"_JRPG{CH}FF"; FSD = "/Game/JRPG/FFSet" if CH == "Fem1" else f"/Game/JRPG/FFSet_{CH}"
G = "/Game/JRPG/Game"; PATH = G + f"/BP_JRPG{CH}Character"
assert SET in ("soldier", "ff"), SET
WALK, RUN = [float(v) for v in open(r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_" + CH.lower() + r"\speeds" + ("_ff" if SET == "ff" else "") + ".txt").read().split()]
ABP = f"{FSD}/ABP_Unarmed{FSX}" if SET == "ff" else "/Game/JRPG/Anims/ABP_Unarmed_Soldier_JRPG"
HALF = {"Fem1": 85.0, "Fem3": 84.0, "Fem4": 84.0}[CH]                     # half her height
if eal.does_asset_exist(PATH): eal.delete_asset(PATH)
f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter").generated_class())
bp = at.create_asset(f"BP_JRPG{CH}Character", G, unreal.Blueprint, f)
H = {str(lib.get_variable_name(lib.get_data(h))): h for h in sds.k2_gather_subobject_data_for_blueprint(bp)}
obj = lambda h: lib.get_object_for_blueprint(lib.get_data(h), bp)
mesh = obj(H["Mesh"])
mesh.set_skeletal_mesh_asset(unreal.load_asset(f"/Game/JRPG/Character/SK_JRPG_{CH}"))
mesh.set_editor_property("anim_class", eal.load_blueprint_class(ABP))
mesh.set_editor_property("relative_location", unreal.Vector(0, 0, -(HALF + 2.2)))        # CharacterMovement floats the capsule ~2.2 cm
mesh.set_editor_property("relative_rotation", unreal.Rotator(pitch=0, yaw=-90, roll=0))
mesh.set_editor_property("visibility_based_anim_tick_option", unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
cap = obj(H["CapsuleComponent"]); cap.set_editor_property("capsule_half_height", HALF); cap.set_editor_property("capsule_radius", 28.0)
cm = obj(H["CharacterMovement"])
for k, v in {"max_walk_speed": RUN, "max_acceleration": 1000.0, "braking_deceleration_walking": 900.0, "ground_friction": 6.0,
             "jump_z_velocity": 440.0, "air_control": 0.3, "rotation_rate": unreal.Rotator(pitch=0, yaw=420, roll=0), "min_analog_walk_speed": 0.0}.items():
    cm.set_editor_property(k, v)
boom = obj(H["CameraBoom"])
boom.set_editor_property("target_arm_length", 330.0); boom.set_editor_property("socket_offset", unreal.Vector(0, 35, 45))
boom.set_editor_property("enable_camera_lag", True); boom.set_editor_property("camera_lag_speed", 9.0)
for name, typ in (("ActionLockUntil", "float"), ("IdleTimer", "float"), ("IdleVariantActive", "bool"), ("IdleVariantUntil", "float"),
                  ("bAutoDemo", "bool"), ("DemoStartTime", "float")):
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
    assert len(T.read_graph_dsl(graphs()[name]).strip().splitlines()) > 1, name + " empty (see LogScript)"
NOW = "(Utilities|Time|GetGameTimeinSeconds)"
GROUNDED = "(< (Math|Vector|VectorLengthSquared (* (Transformation|GetVelocity) (Math|Vector|MakeVector 0.0 0.0 1.0))) 25.0)"
M = lambda c: f'"/Game/JRPG/Anims/AM_Soldier_{c}_JRPG.AM_Soldier_{c}_JRPG"'
MF = lambda c: f'"{FSD}/AM{FSX}_{c}.AM{FSX}_{c}"'
ACTS = ([MF("Attack_01"), MF("Attack_02"), MF("Attack_03"), MF("Dash"), MF("ChargedAttack")] if SET == "ff"
        else [M("02_Shot"), M("02_Reload"), M("Attack_01"), M("Attack_02"), M("Get_Hit")])
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
    (:Default (CallFunction|BeginIdleVariant :Len (Animation|PlayAnimMontage :AnimMontage {M('Idle_03')})))))""") if SET == "soldier" else fn("PlayIdleVariant", [], """
(fn PlayIdleVariant ()
  (Variables|Default|SetIdleTimer 0.0))""")                                       # the FF set has no idle flourishes
fn("DoAction", ["Which"], f"""
(fn DoAction (Which)
  (if (and (>= {NOW} (Variables|Default|GetActionLockUntil)) {GROUNDED})
    (if (< Which 0.5)
      (CallFunction|BeginAction :Len (Animation|PlayAnimMontage :AnimMontage {ACTS[0]}))
      (elif (< Which 1.5)
        (CallFunction|BeginAction :Len (Animation|PlayAnimMontage :AnimMontage {ACTS[1]}))
        (elif (< Which 2.5)
          (CallFunction|BeginAction :Len (Animation|PlayAnimMontage :AnimMontage {ACTS[2]}))
          (elif (< Which 3.5)
            (CallFunction|BeginAction :Len (Animation|PlayAnimMontage :AnimMontage {ACTS[3]}))
            (elif (< Which 4.5)
              (CallFunction|BeginAction :Len (Animation|PlayAnimMontage :AnimMontage {ACTS[4]}))
              (else
                (CallFunction|PlayIdleVariant)))))))))""")
wr = WALK / RUN
T.add_function_graph(bp, "MoveScale"); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
T.write_graph_dsl(graphs()["MoveScale"], f"""
(fn MoveScale (X Y)
  (bind s (select (Input|EnhancedActionValues|IA_Sprint) 1.0 {wr:.4f}))
  (bind k (select (< {NOW} (Variables|Default|GetActionLockUntil)) 0.0 (/ s (Math|Float|Max(Float) (Math|Float|Sqrt (+ (* X X) (* Y Y))) 1.0))))
  (return (* X k) (* Y k)))""")
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
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
      (if (> (Variables|Default|GetIdleTimer) {8.0 if SET == "soldier" else 1e9})
        (Variables|Default|SetIdleTimer 0.0)
        (CallFunction|PlayIdleVariant))
      (else
        (Variables|Default|SetIdleTimer 0.0)))))
""")
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
def info(n): return T.get_node_infos([n])[0]
def pin(i, name, out):
    for p in (i.output_pins if out else i.input_pins):
        if str(p.name) == name: return p.pin_id
    raise KeyError(name)
for k, (ia, which) in enumerate((("IA_Jab", 0), ("IA_Hook", 1), ("IA_Punch", 2), ("IA_Sweep", 3), ("IA_Kick", 4), ("IA_IdleAnim", 5))):
    ev = T.create_node(g, f"Input|EnhancedActionEvents|{ia}", unreal.IntPoint(-1200, 1600 + 220 * k))
    call = T.create_node(g, "CallFunction|DoAction", unreal.IntPoint(-750, 1600 + 220 * k))
    T.connect_pins(pin(info(ev), "Started", True), pin(info(call), "execute", False))
    T.set_pin_value(pin(info(call), "Which", False), f"{which}.0")
for name in ("DoAction", "PlayIdleVariant", "MoveScale"):
    print("==", name, T.read_graph_dsl(graphs()[name])[:150].replace("\n", " "))
nodes = [str(info(n).type_id) for n in T.find_nodes(g, "")]
print("events:", sum("EnhancedActionEvents" in t for t in nodes), "DoAction calls:", sum("DoAction" in t for t in nodes), "tick:", any("EventTick" in t for t in nodes))
print("compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp)); eal.save_loaded_asset(bp)
GM = G + f"/BP_JRPG{CH}GameMode"
if eal.does_asset_exist(GM): eal.delete_asset(GM)
gm = eal.duplicate_asset("/Game/Soldier/Game/BP_SoldierGameMode", GM)
unreal.get_default_object(gm.generated_class()).set_editor_property("default_pawn_class", bp.generated_class())
unreal.BlueprintEditorLibrary.compile_blueprint(gm); eal.save_loaded_asset(gm)
print("game mode pawn:", unreal.get_default_object(unreal.load_asset(GM).generated_class()).get_editor_property("default_pawn_class").get_name())
# L_Meshy_Meadow spawns her
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level("/Game/Meshy/Maps/L_Meshy_Meadow")
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(); ws = w.get_world_settings()
print("level game mode was", ws.get_editor_property("default_game_mode"))
ws.set_editor_property("default_game_mode", unreal.load_asset(GM).generated_class())
les.save_current_level(); print("L_Meshy_Meadow game mode ->", ws.get_editor_property("default_game_mode").get_name(),
                               "| player starts", len([a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if isinstance(a, unreal.PlayerStart)]))
print(f"walk {WALK:.1f} / run {RUN:.1f} cm/s")
