"""BP_Fig4Character: the template third-person character driving fig4's MetaHuman body with the
heel-stance locomotion AnimBP, plus face (MetaHuman component), outfit and strand grooms."""
import unreal
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lib = unreal.SubobjectDataBlueprintFunctionLibrary
PATH = "/Game/Fig4/Game/BP_Fig4Character"
if eal.does_asset_exist(PATH): eal.delete_asset(PATH)
parent = unreal.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", parent.generated_class())
bp = at.create_asset("BP_Fig4Character", "/Game/Fig4/Game", unreal.Blueprint, f)

def handles():
    return {str(lib.get_variable_name(lib.get_data(h))): h for h in sds.k2_gather_subobject_data_for_blueprint(bp)}
def obj(h): return lib.get_object_for_blueprint(lib.get_data(h), bp)
def add(parent_h, cls, name):
    p = unreal.AddNewSubobjectParams(parent_handle=parent_h, new_class=cls, blueprint_context=bp)
    h, fail = sds.add_new_subobject(p)
    sds.rename_subobject(h, unreal.Text(name))
    return h

H = handles(); print("inherited:", list(H.keys()))
FACE_MESH = unreal.load_asset("/Game/MetaHumans/Fig4/Face/SKM_MHC_Fig4_Final_FaceMesh")
BODY_MESH = unreal.load_asset("/Game/MetaHumans/Fig4/Body/SKM_MHC_Fig4_Final_BodyMesh")
abp = unreal.EditorAssetLibrary.load_blueprint_class("/Game/Fig4/Locomotion/Anims/ABP_Unarmed_Fig4")
mesh = obj(H["Mesh"])
mesh.set_skeletal_mesh_asset(BODY_MESH)
mesh.set_editor_property("anim_class", abp)
mesh.set_editor_property("relative_location", unreal.Vector(0, 0, -86.0))
mesh.set_editor_property("relative_rotation", unreal.Rotator(pitch=0, yaw=-90, roll=0))
mesh.set_editor_property("visibility_based_anim_tick_option", unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
cap = obj(H["CapsuleComponent"])
cap.set_editor_property("capsule_half_height", 86.0); cap.set_editor_property("capsule_radius", 28.0)

face_h = add(H["Mesh"], unreal.SkeletalMeshComponent, "Face")
face = obj(face_h); face.set_skeletal_mesh_asset(FACE_MESH)
face.set_editor_property("anim_class", unreal.EditorAssetLibrary.load_blueprint_class("/Game/MetaHumans/Common/Face/ABP_Face"))
outfit_h = add(H["Mesh"], unreal.SkeletalMeshComponent, "Outfit")
outfit = obj(outfit_h); outfit.set_skeletal_mesh_asset(unreal.load_asset("/Game/Fig4/Outfit/fig4_outfit_skinned"))
outfit.set_editor_property("anim_class", unreal.EditorAssetLibrary.load_blueprint_class("/Game/MetaHumans/Common/Animation/ABP_Clothing_PostProcess"))
add(H[list(H.keys())[0]], unreal.MetaHumanComponentUE, "MetaHuman")

binds = sorted(a for a in eal.list_assets("/Game/Fig4/Hair", recursive=False) if "Binding" in a.split(".")[-1])
grooms = [("Hair", "/Game/Fig4/Hair/GR_Fig4_Hair", binds[-1].split(".")[0], "/Game/Fig4/Hair/MI_Fig4_Hair"),
          ("Eyebrows", "/Game/MetaHumans/Fig4/Grooms/Eyebrows_M_Natural", "/Game/MetaHumans/Fig4/Grooms/Eyebrows_M_Natural_Binding", None),
          ("Eyelashes", "/Game/MetaHumans/Fig4/Grooms/Eyelashes_L_Curl", "/Game/MetaHumans/Fig4/Grooms/Eyelashes_L_Curl_Binding", None),
          ("Fuzz", "/Game/MetaHumans/Fig4/Grooms/Peachfuzz_M_Thin", "/Game/MetaHumans/Fig4/Grooms/Peachfuzz_M_Thin_Binding", None)]
for name, g, b, m in grooms:
    gh = add(face_h, unreal.GroomComponent, name)
    gc = obj(gh)
    gc.set_editor_property("groom_asset", unreal.load_asset(g)); gc.set_editor_property("binding_asset", unreal.load_asset(b))
    if m: gc.set_editor_property("override_materials", [unreal.load_asset(m)])
cm = obj(H["CharacterMovement"])
for k, v in {"max_walk_speed": 180.0, "max_acceleration": 900.0, "braking_deceleration_walking": 700.0,
             "ground_friction": 6.0, "jump_z_velocity": 430.0, "air_control": 0.3, "rotation_rate": unreal.Rotator(pitch=0, yaw=420, roll=0)}.items():
    try: cm.set_editor_property(k, v)
    except Exception as e: print("move", k, str(e)[:60])
boom = obj(H["CameraBoom"])
boom.set_editor_property("target_arm_length", 360.0)
boom.set_editor_property("socket_offset", unreal.Vector(0, 35, 45))
boom.set_editor_property("enable_camera_lag", True); boom.set_editor_property("camera_lag_speed", 9.0)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
eal.save_loaded_asset(bp)
print("components:", list(handles().keys()))
