"""random_dungeonmagic_level5, Summoner2, step 6: her characters and game mode.
- BP_JRPGSummoner2Character (/Game/JRPG/Game): the template third-person character (as 620 makes the JRPG characters) with
  her MetaHuman body (SKM_MHC_Summoner2_BodyMesh) playing ABP_Unarmed_S2 (846: the mannequin's locomotion retargeted onto
  her, its DefaultSlot for the casts); her capsule for her height (160 cm); walk / run speeds from 846's speeds.txt (the
  clips' own: the brisk walk 2.6 m/s, the jog 5.2 m/s) in a MoveScale as 620's. Her face, hair and bikini are not on it:
  the dungeon generator's FaceMeta (848) gives her pawn a face component that makes them in play.
- BP_RDM5_Summoner2Character (/Game/RandomDungeon/Blueprints): her dungeon character, a child of it with the Mage's 36 cm
  capsule radius (as 833's Summoner). Run 819 after this (her RunMode and MoveScale for the casters' controls).
- BP_RDM5S2_GameMode: BP_RD_GameMode with her as the pawn (848 sets it on the level).
Args: none"""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
D = "/Game/JRPG/MetaHuman/Summoner2"
HALF = 80.0
WALK, RUN = [float(v) for v in open(SA + r"\summoner2\speeds.txt").read().split()]
G = "/Game/JRPG/Game"; PATH = f"{G}/BP_JRPGSummoner2Character"
CHILD = "/Game/RandomDungeon/Blueprints/BP_RDM5_Summoner2Character"; GM = "/Game/RandomDungeon/Blueprints/BP_RDM5S2_GameMode"
for p in (GM, CHILD, PATH):
    if eal.does_asset_exist(p): eal.delete_asset(p)
f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter").generated_class())
bp = at.create_asset("BP_JRPGSummoner2Character", G, unreal.Blueprint, f)
H = {str(lib.get_variable_name(lib.get_data(h))): h for h in sds.k2_gather_subobject_data_for_blueprint(bp)}
obj = lambda h: lib.get_object_for_blueprint(lib.get_data(h), bp)
mesh = obj(H["Mesh"])
mesh.set_skeletal_mesh_asset(unreal.load_asset(f"{D}/Body/SKM_MHC_Summoner2_BodyMesh"))
mesh.set_editor_property("anim_class", eal.load_blueprint_class(f"{D}/Locomotion/ABP_Unarmed_S2"))
mesh.set_editor_property("relative_location", unreal.Vector(0, 0, -(HALF + 2.2)))       # CharacterMovement floats the capsule ~2.2 cm
mesh.set_editor_property("relative_rotation", unreal.Rotator(pitch=0, yaw=-90, roll=0))  # (the MetaHuman faces +Y)
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
print("S2CHAR compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp)); eal.save_loaded_asset(bp)
f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", bp.generated_class())
ch = at.create_asset("BP_RDM5_Summoner2Character", "/Game/RandomDungeon/Blueprints", unreal.Blueprint, f)
unreal.BlueprintEditorLibrary.compile_blueprint(ch)
unreal.get_default_object(ch.generated_class()).get_component_by_class(unreal.CapsuleComponent).set_editor_property("capsule_radius", 36.0)
unreal.BlueprintEditorLibrary.compile_blueprint(ch); eal.save_loaded_asset(ch, only_if_is_dirty=False)
gm = eal.duplicate_asset("/Game/RandomDungeon/Blueprints/BP_RD_GameMode", GM)
unreal.get_default_object(gm.generated_class()).set_editor_property("default_pawn_class", ch.generated_class())
unreal.BlueprintEditorLibrary.compile_blueprint(gm); eal.save_loaded_asset(gm, only_if_is_dirty=False)
cdo = unreal.get_default_object(unreal.load_asset(GM).generated_class())
print("S2CHAR", PATH, "| child", CHILD, "| game mode", GM, "-> pawn", cdo.get_editor_property("default_pawn_class").get_name(),
      "hud", cdo.get_editor_property("hud_class").get_name(), f"| walk {WALK:.1f} / run {RUN:.1f} cm/s, capsule {HALF:.0f} cm half height")
