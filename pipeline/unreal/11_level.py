"""Build L_Fig4_Studio: cyclorama, plinth, fig4, studio lighting, MegaLights bulb wall, PPV, camera."""
import math, unreal
LEVEL = "/Game/Fig4/Maps/L_Fig4_Studio"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
eal = unreal.EditorAssetLibrary
def tolerant(fn, *a):
    """Engine warnings logged during a call surface as RuntimeError; the call itself completes."""
    try:
        return fn(*a)
    except RuntimeError as e:
        print("(non-fatal)", str(e).splitlines()[0][:140])

if eal.does_asset_exist(LEVEL):
    tolerant(les.load_level, LEVEL)
    for a in eas.get_all_level_actors():
        eas.destroy_actor(a)
else:
    tolerant(les.new_level, LEVEL)
print("world:", unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name())

def spawn(cls_or_asset, loc, rot=(0, 0, 0), label=None, scale=None):
    r = unreal.Rotator(pitch=rot[0], yaw=rot[1], roll=rot[2])
    if isinstance(cls_or_asset, str):
        a = tolerant(eas.spawn_actor_from_object, unreal.load_asset(cls_or_asset), unreal.Vector(*loc), r)
    else:
        a = tolerant(eas.spawn_actor_from_class, cls_or_asset, unreal.Vector(*loc), r)
    if a is None:
        raise RuntimeError(f"spawn failed for {cls_or_asset}")
    if label: a.set_actor_label(label)
    if scale: a.set_actor_scale3d(unreal.Vector(*scale))
    return a

def aim(a, target):
    rot = unreal.MathLibrary.find_look_at_rotation(a.get_actor_location(), unreal.Vector(*target))
    a.set_actor_rotation(rot, False)

spawn("/Game/Fig4/Studio/Meshes/SM_Cyclorama/StaticMeshes/SM_Cyclorama", (0, 0, 0), label="Cyclorama")
spawn("/Game/Fig4/Studio/Meshes/SM_Plinth/StaticMeshes/SM_Plinth", (0, 0, 0), label="Plinth")
fig = spawn(unreal.EditorAssetLibrary.load_blueprint_class("/Game/MetaHumans/Fig4/BP_Fig4"), (0, 0, 6), label="Fig4")

def rect(label, loc, target, w, h, intensity, temp, barn=45, megalights=True):
    a = spawn(unreal.RectLight, loc, label=label)
    c = a.light_component
    c.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
    c.set_editor_property("intensity", intensity)
    c.set_editor_property("source_width", w); c.set_editor_property("source_height", h)
    c.set_editor_property("barn_door_angle", barn); c.set_editor_property("barn_door_length", 30)
    c.set_editor_property("use_temperature", True); c.set_editor_property("temperature", temp)
    c.set_editor_property("attenuation_radius", 2000)
    try: c.set_editor_property("allow_mega_lights", megalights)
    except Exception: pass
    aim(a, target)
    return a

FACE = (0, 0, 150)
rect("Key_Softbox", (-170, 210, 235), (0, 0, 140), 120, 90, 110, 5400)
rect("Fill_Scrim", (240, 230, 150), (0, 0, 120), 200, 180, 18, 5600, barn=10)
rect("Rim_L", (-190, -170, 190), (0, 0, 140), 25, 160, 160, 6500, barn=60)
rect("Rim_R", (190, -170, 190), (0, 0, 140), 25, 160, 140, 6500, barn=60)
rect("Hair_Top", (0, -90, 330), (0, 0, 165), 60, 40, 60, 5000)

# MegaLights: 12 x 8 warm bulbs on a curved frame behind her, each casting shadows
bulb_mesh = unreal.load_asset("/Engine/BasicShapes/Sphere")
bulb_mat_path = "/Game/Fig4/Studio/Materials/M_Bulb"
if not eal.does_asset_exist(bulb_mat_path):
    at = unreal.AssetToolsHelpers.get_asset_tools()
    bm = at.create_asset("M_Bulb", "/Game/Fig4/Studio/Materials", unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    col = mel.create_material_expression(bm, unreal.MaterialExpressionConstant3Vector, -400, 0)
    col.set_editor_property("constant", unreal.LinearColor(60.0, 30.0, 9.0, 1))
    unlit = mel.create_material_expression(bm, unreal.MaterialExpressionSubstrateUnlitBSDF, -150, 0)
    mel.connect_material_expressions(col, "", unlit, "Emissive Color")
    mel.connect_material_property(unlit, "", unreal.MaterialProperty.MP_FRONT_MATERIAL)
    mel.recompile_material(bm); eal.save_loaded_asset(bm)
bulb_mat = unreal.load_asset(bulb_mat_path)
n = 0
for row in range(8):
    for col in range(12):
        ang = math.radians(-55 + 110 * col / 11)
        R = 330
        x, y = R * math.sin(ang), -R * math.cos(ang) - 40
        z = 40 + row * 38 + (12 if col % 2 else 0)
        pl = spawn(unreal.PointLight, (x, y, z), label=f"Bulb_{row}_{col}")
        c = pl.light_component
        c.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
        c.set_editor_property("intensity", 1.6)
        c.set_editor_property("source_radius", 1.2)
        c.set_editor_property("attenuation_radius", 600)
        c.set_editor_property("use_temperature", True); c.set_editor_property("temperature", 2700)
        try: c.set_editor_property("allow_mega_lights", True)
        except Exception: pass
        bulb = spawn(unreal.StaticMeshActor, (x, y, z), label=f"BulbMesh_{row}_{col}", scale=(0.03, 0.03, 0.03))
        smc = bulb.static_mesh_component
        smc.set_static_mesh(bulb_mesh); smc.set_material(0, bulb_mat)
        smc.set_editor_property("cast_shadow", False)
        pl.attach_to_actor(bulb, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
                           unreal.AttachmentRule.KEEP_WORLD, False)
        n += 1
print("bulbs", n)

sky = spawn(unreal.SkyLight, (0, 0, 400), label="Ambient_Sky")
sc = sky.light_component
sc.set_editor_property("intensity", 0.15)
sc.set_editor_property("lower_hemisphere_is_black", True)
sc.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)

ppv = spawn(unreal.PostProcessVolume, (0, 0, 100), label="PPV_Studio")
ppv.set_editor_property("unbound", True)
s = ppv.settings
def ov(name, val):
    try:
        s.set_editor_property("override_" + name, True)
    except Exception:
        pass
    s.set_editor_property(name, val)
ov("dynamic_global_illumination_method", unreal.DynamicGlobalIlluminationMethod.LUMEN)
ov("reflection_method", unreal.ReflectionMethod.LUMEN)
ov("lumen_scene_lighting_quality", 2.0)
ov("lumen_scene_detail", 2.0)
ov("lumen_final_gather_quality", 2.0)
ov("lumen_reflection_quality", 2.0)
try:
    ov("lumen_ray_lighting_mode", unreal.LumenRayLightingModeOverride.HIT_LIGHTING_FOR_REFLECTIONS)
except Exception as e:
    print("ray lighting mode:", e)
try:
    ov("mega_lights", True)
except Exception as e:
    print("megalights pp:", e)
ov("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
ov("auto_exposure_apply_physical_camera_exposure", False)
ov("auto_exposure_bias", 9.5)
ov("bloom_intensity", 0.35)
ov("vignette_intensity", 0.35)
ov("film_grain_intensity", 0.08)
ov("scene_fringe_intensity", 0.15)
ppv.set_editor_property("settings", s)

cam = spawn(unreal.CineCameraActor, (0, 360, 128), label="Cam_Hero")
aim(cam, (0, 0, 108))
cc = cam.get_cine_camera_component()
fb = cc.get_editor_property("filmback"); fb.sensor_width = 36.0; fb.sensor_height = 24.0
cc.set_editor_property("filmback", fb)
cc.set_editor_property("current_focal_length", 50.0)
cc.set_editor_property("current_aperture", 2.8)
fs = cc.get_editor_property("focus_settings")
fs.focus_method = unreal.CameraFocusMethod.MANUAL; fs.manual_focus_distance = 360.0
cc.set_editor_property("focus_settings", fs)

les.save_current_level()
print("LEVEL saved", LEVEL)
