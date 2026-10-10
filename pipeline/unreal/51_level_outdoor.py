"""Outdoor meadow level (args: level_path [cine]). Playable by default; "cine" adds the AI demo Fig4 instead of a PlayerStart. Nanite terrain + grass + rocks, sun/sky/atmosphere/clouds/fog,
Lumen + MegaLights PPV, PlayerStart, GameMode spawning BP_Fig4Character (WASD, mouse camera, Space jump, Shift run)."""
import json, math, sys, unreal
LEVEL = sys.argv[1] if len(sys.argv) > 1 else "/Game/Fig4/Maps/L_Fig4_Meadow"
CINE = "cine" in sys.argv[2:]
OPT = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)       # pawn=/Game/.../BP_X  gm=/Game/.../BP_XGameMode
PAWN = OPT.get("pawn", "/Game/Fig4/Game/BP_Fig4Character")
W = "/Game/Fig4/World/Meshes"
PL = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\terrain\placements.json"))
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
eal = unreal.EditorAssetLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()
def tolerant(fn, *a):
    try: return fn(*a)
    except RuntimeError as e: print("(non-fatal)", str(e).splitlines()[0][:140])

if eal.does_asset_exist(LEVEL):
    tolerant(les.load_level, LEVEL)
    for a in eas.get_all_level_actors(): eas.destroy_actor(a)
else:
    tolerant(les.new_level, LEVEL)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
print("world:", world.get_path_name())
assert world.get_path_name().startswith(LEVEL + "."), "editor is not on " + LEVEL

def spawn(cls_or_asset, loc, rot=(0, 0, 0), label=None, scale=None):
    r = unreal.Rotator(pitch=rot[0], yaw=rot[1], roll=rot[2])
    if isinstance(cls_or_asset, str):
        a = tolerant(eas.spawn_actor_from_object, unreal.load_asset(cls_or_asset), unreal.Vector(*loc), r)
    else:
        a = tolerant(eas.spawn_actor_from_class, cls_or_asset, unreal.Vector(*loc), r)
    if a is None: raise RuntimeError(f"spawn failed for {cls_or_asset}")
    if label: a.set_actor_label(label)
    if scale: a.set_actor_scale3d(unreal.Vector(*scale))
    return a

# ---- ground ----
ter = spawn(f"{W}/SM_Terrain/StaticMeshes/SM_Terrain", (0, 0, 0), label="Terrain")
ter.static_mesh_component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
# verify heightfield orientation against the real collision
def trace_z(x, y):
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 20000), unreal.Vector(x, y, -20000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    if hit is None: return None
    t = hit.to_tuple()
    return t[4].z if t[0] or t[1] else None    # (blocking_hit, initial_overlap, time, distance, location, ...)
for px, py, pz in PL["probe"]:
    print("probe", px, py, "predicted", round(pz, 1), "trace", trace_z(px, py))

rock_meshes = {k: unreal.load_asset(f"{W}/SM_Rock_{k}/StaticMeshes/SM_Rock_{k}") for k in "ABC"}
for i, r in enumerate(PL["rocks"]):
    a = spawn(f"{W}/SM_Rock_{r['mesh']}/StaticMeshes/SM_Rock_{r['mesh']}", (r["x"], r["y"], r["z"]),
              (r["pitch"], r["yaw"], r["roll"]), label=f"Rock_{i:02d}", scale=(r["s"],) * 3)
    a.set_folder_path("Rocks")

def add_comp(actor, cls, name):
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sds.k2_gather_subobject_data_for_instance(actor)
    p = unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=cls, blueprint_context=None)
    h, fail = sds.add_new_subobject(p)
    if fail and str(fail): print("add comp:", fail)
    comps = [c for c in actor.get_components_by_class(cls)]
    return comps[-1]
grass_actor = spawn(unreal.Actor, (0, 0, 0), label="Grass")
root = add_comp(grass_actor, unreal.SceneComponent, "Root")
hism = add_comp(grass_actor, unreal.HierarchicalInstancedStaticMeshComponent, "GrassHISM")
hism.set_static_mesh(unreal.load_asset(f"{W}/SM_GrassClump/StaticMeshes/SM_GrassClump"))
hism.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
hism.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
hism.set_editor_property("affect_distance_field_lighting", False)   # DF shadows of thin blades render as blocks
hism.set_editor_property("affect_dynamic_indirect_lighting", False)
xf = []
for x, y, z, yaw, s in PL["grass"]:
    xf.append(unreal.Transform(unreal.Vector(x, y, z), unreal.Rotator(0, yaw, 0), unreal.Vector(s, s, s * 1.1)))
CH = 5000
for i in range(0, len(xf), CH):
    hism.add_instances(xf[i:i + CH], False, True)
print("grass instances", hism.get_instance_count())

# ---- sky, sun, atmosphere ----
sun = spawn(unreal.DirectionalLight, (0, 0, 2000), (-24, 205, 0), label="Sun")
sc = sun.light_component
sc.set_editor_property("intensity", 10.0)
sc.set_editor_property("use_temperature", True); sc.set_editor_property("temperature", 5200)
sc.set_editor_property("atmosphere_sun_light", True)
sc.set_editor_property("light_source_angle", 0.53)
sc.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
try: sc.set_editor_property("cast_cloud_shadows", True)
except Exception: pass
spawn(unreal.SkyAtmosphere, (0, 0, 0), label="SkyAtmosphere")
sky = spawn(unreal.SkyLight, (0, 0, 1500), label="SkyLight")
skc = sky.light_component
skc.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
skc.set_editor_property("real_time_capture", True)
skc.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)
fog = spawn(unreal.ExponentialHeightFog, (0, 0, -200), label="HeightFog")
fc = fog.component
def setp(obj, names, val):
    for n in names:
        try: obj.set_editor_property(n, val); return n
        except Exception: pass
    print("no property", names)
setp(fc, ["fog_density"], 0.012); setp(fc, ["fog_height_falloff"], 0.15)
setp(fc, ["enable_volumetric_fog", "volumetric_fog", "b_enable_volumetric_fog"], True)
setp(fc, ["volumetric_fog_scattering_distribution"], 0.6)
setp(fc, ["volumetric_fog_extinction_scale"], 0.6)
spawn(unreal.VolumetricCloud, (0, 0, 0), label="Clouds")

ppv = spawn(unreal.PostProcessVolume, (0, 0, 0), label="PPV_Outdoor")
ppv.set_editor_property("unbound", True)
s = ppv.settings
def ov(name, val):
    try: s.set_editor_property("override_" + name, True)
    except Exception: pass
    try: s.set_editor_property(name, val)
    except Exception as e: print("pp", name, e)
ov("dynamic_global_illumination_method", unreal.DynamicGlobalIlluminationMethod.LUMEN)
ov("reflection_method", unreal.ReflectionMethod.LUMEN)
ov("lumen_scene_lighting_quality", 1.5); ov("lumen_scene_detail", 1.5); ov("lumen_final_gather_quality", 1.5)
ov("mega_lights", True)
ov("auto_exposure_method", unreal.AutoExposureMethod.AEM_HISTOGRAM)
ov("auto_exposure_bias", -0.2)
ov("auto_exposure_min_brightness", -1.0); ov("auto_exposure_max_brightness", 14.0)
ov("bloom_intensity", 0.4)
ov("vignette_intensity", 0.3)
ov("film_grain_intensity", 0.0)
ov("white_temp", 6300.0)
ppv.set_editor_property("settings", s)

# ---- player ----
start_z = PL["start_z"] + 110
if not CINE:
    spawn(unreal.PlayerStart, (0, 0, start_z), (0, 0, 0), label="PlayerStart")
else:
    demo = spawn(unreal.EditorAssetLibrary.load_blueprint_class(PAWN), (0, 0, PL["start_z"] + 88), label="Fig4_Demo")
    demo.set_editor_property("auto_possess_ai", unreal.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED)
    demo.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.DISABLED)
    demo.set_editor_property("bAutoDemo", True); demo.set_editor_property("DemoStartTime", 1.5)
    # the MRQ spectator spawns at a PlayerStart; without one it lands on the demo at the origin and props her up
    spawn(unreal.PlayerStart, (0, -6000, 3000), label="SpectatorStart")
GM = OPT.get("gm", "/Game/Fig4/Game/BP_Fig4GameMode")
if not eal.does_asset_exist(GM):
    f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.EditorAssetLibrary.load_blueprint_class("/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode"))
    at.create_asset(GM.rsplit("/", 1)[1], GM.rsplit("/", 1)[0], unreal.Blueprint, f)
gm_bp = unreal.load_asset(GM)
gm_cls = gm_bp.generated_class()
unreal.get_default_object(gm_cls).set_editor_property("default_pawn_class", unreal.EditorAssetLibrary.load_blueprint_class(PAWN))
unreal.BlueprintEditorLibrary.compile_blueprint(gm_bp); eal.save_loaded_asset(gm_bp)
world.get_world_settings().set_editor_property("default_game_mode", gm_cls)

les.save_current_level()
print("LEVEL saved", LEVEL, "start_z", start_z)
