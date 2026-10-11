"""BP_JRPG<CH>Character: an animated Tripo character on the template third-person character, playing ITS OWN clips (610/615):
WASD walk (her Walk), Shift run (her Run), Space jump (template jump/fall/land, retargeted), mouse camera. Walk / run speeds =
her measured stance-foot speeds (SourceArt/jrpg_<ch>/speeds.txt), so the feet don't slide. BP_JRPG<CH>GameMode spawns her; it is
set as L_Meshy_Meadow's game mode.  Args: CH [half_height_cm]"""
import sys, unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
CH = sys.argv[1] if len(sys.argv) > 1 else "Fem5"; HALF = float(sys.argv[2]) if len(sys.argv) > 2 else 82.5
G = "/Game/JRPG/Game"; PATH = f"{G}/BP_JRPG{CH}Character"
WALK, RUN = [float(v) for v in open(r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_" + CH.lower() + r"\speeds.txt").read().split()]
if eal.does_asset_exist(PATH): eal.delete_asset(PATH)
f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter").generated_class())
bp = at.create_asset(f"BP_JRPG{CH}Character", G, unreal.Blueprint, f)
H = {str(lib.get_variable_name(lib.get_data(h))): h for h in sds.k2_gather_subobject_data_for_blueprint(bp)}
obj = lambda h: lib.get_object_for_blueprint(lib.get_data(h), bp)
mesh = obj(H["Mesh"])
mesh.set_skeletal_mesh_asset(unreal.load_asset(f"/Game/JRPG/Character/SK_JRPG_{CH}"))
mesh.set_editor_property("anim_class", eal.load_blueprint_class(f"/Game/JRPG/{CH}Locomotion/ABP_Unarmed_{CH}"))
mesh.set_editor_property("relative_location", unreal.Vector(0, 0, -(HALF + 2.2)))        # CharacterMovement floats the capsule ~2.2 cm
mesh.set_editor_property("relative_rotation", unreal.Rotator(pitch=0, yaw=-90, roll=0))
mesh.set_editor_property("visibility_based_anim_tick_option", unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
cap = obj(H["CapsuleComponent"]); cap.set_editor_property("capsule_half_height", HALF); cap.set_editor_property("capsule_radius", 28.0)
cm = obj(H["CharacterMovement"])
for k, v in {"max_walk_speed": RUN, "max_acceleration": 1200.0, "braking_deceleration_walking": 1000.0, "ground_friction": 7.0,
             "jump_z_velocity": 450.0, "air_control": 0.3, "rotation_rate": unreal.Rotator(pitch=0, yaw=480, roll=0), "min_analog_walk_speed": 0.0}.items():
    cm.set_editor_property(k, v)
boom = obj(H["CameraBoom"])
boom.set_editor_property("target_arm_length", 320.0); boom.set_editor_property("socket_offset", unreal.Vector(0, 35, 45))
boom.set_editor_property("enable_camera_lag", True); boom.set_editor_property("camera_lag_speed", 9.0)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
graphs = lambda: {x.get_name(): x for x in T.list_graphs(bp)}
T.add_function_graph(bp, "MoveScale"); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
T.write_graph_dsl(graphs()["MoveScale"], f"""
(fn MoveScale (X Y)
  (bind k (/ (select (Input|EnhancedActionValues|IA_Sprint) 1.0 {WALK / RUN:.4f}) (Math|Float|Max(Float) (Math|Float|Sqrt (+ (* X X) (* Y Y))) 1.0)))
  (return (* X k) (* Y k)))""")
print("MoveScale:", " ".join(T.read_graph_dsl(graphs()["MoveScale"]).split())[:160])
print("compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp)); eal.save_loaded_asset(bp)
GM = f"{G}/BP_JRPG{CH}GameMode"
if eal.does_asset_exist(GM): eal.delete_asset(GM)
gm = eal.duplicate_asset("/Game/Soldier/Game/BP_SoldierGameMode", GM)
unreal.get_default_object(gm.generated_class()).set_editor_property("default_pawn_class", bp.generated_class())
unreal.BlueprintEditorLibrary.compile_blueprint(gm); eal.save_loaded_asset(gm)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level("/Game/Meshy/Maps/L_Meshy_Meadow")
ws = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_world_settings()
ws.set_editor_property("default_game_mode", unreal.load_asset(GM).generated_class())
les.save_current_level(); print("L_Meshy_Meadow game mode ->", ws.get_editor_property("default_game_mode").get_name(), f"| walk {WALK:.1f} / run {RUN:.1f} cm/s")
