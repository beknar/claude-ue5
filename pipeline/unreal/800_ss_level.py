"""starship_level: outer space, a 5 km x 5 km x 5 km combat area with a space fighter (C++ in Source/claude_ue5/SS:
ASSFighter / ASSArena / ASSTarget / ASSMissile / ASSPlayerController / ASSHUD / ASSGameMode). This script builds
- materials (/Game/Starship/Materials): M_SS_Bolt (cannon bolts: unlit glow), M_SS_Blast (explosion flash: an additive
  ball with the parameters Alpha and Color), MI_SS_Planet_* / MI_SS_Atmosphere (the kit's planet materials with this
  level's sun direction);
- the level /Game/Starship/Maps/starship_level: Spaceship_Kit's star sphere, sun and planets, a sun light with a faint
  fill from the planet's side, a sky light, a post process volume (fixed exposure, bloom), game mode SSGameMode;
- SS_Arena (ASSArena, the middle of the area) with the explosion / impact effects;
- SS_Fighter (ASSFighter): the fighter, a kitbash of pack meshes only, in the style of a Colonial Viper. Red_Echo's small
  white-and-red delta ship is the fuselage with its two engines; added to it: stub wings (the cargo ship's wing with
  its fan and position lights), a third engine on the back with a tail fin (Spaceship_Kit reactor and panel), twin
  cannons on the wing tips (Spaceship_Kit turret barrels), four missiles under the wings (the military drone's
  grenade, also the mesh of the fired missile), and blue engine flames (Spaceship_Kit's reactor flame) whose length
  follows the throttle;
- effects (/Game/Starship/FX): contrails for the fighter's engines, its missiles and the drones: copies of the library's
  ribbon trail (Medieval_Weapons P_ArrowTrail) tuned by USSFXLibrary. Explosions are StarterContent's P_Explosion.
801 adds the station, the clutter and the targets. Re-run 800 then 801 after changing the fighter or the level.
Args: [fighter] (only rebuild the fighter and the arena's effects in the open starship_level)"""
import sys, math, unreal
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); MEL = unreal.MaterialEditingLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
V = unreal.Vector; Rot = unreal.Rotator
MAP = "/Game/Starship/Maps/starship_level"; MATS = "/Game/Starship/Materials"; TAG = "ss_level"
HALF = 250000.0                               # half the side of the combat cube (cm)
START = V(-150000.0, -60000.0, 20000.0)       # the start corner, 1.6 km from the station (801 hangs the gate course on it and moves the fighter to its first gate)
L = unreal.load_asset
def mesh(path):
    m = L(path); assert m, path; return m

# ---------------------------------------------------------------- materials
def fresh(name):
    p = f"{MATS}/{name}"
    if eal.does_asset_exist(p): return L(p), False
    return at.create_asset(name, MATS, unreal.Material, unreal.MaterialFactoryNew()), True
def bolt_material():
    m, new = fresh("M_SS_Bolt")
    MEL.delete_all_material_expressions(m)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    col = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -500, 0); col.set_editor_property("parameter_name", "Color")
    col.set_editor_property("default_value", unreal.LinearColor(1.0, 0.30, 0.08, 1.0))
    k = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -500, 250); k.set_editor_property("parameter_name", "Glow"); k.set_editor_property("default_value", 90.0)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -250, 100)
    MEL.connect_material_expressions(col, "", mul, "A"); MEL.connect_material_expressions(k, "", mul, "B")
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); eal.save_loaded_asset(m, only_if_is_dirty=False)
    assert MEL.get_statistics(m).num_pixel_shader_instructions > 0, "M_SS_Bolt failed to compile"
    return m
def blast_material():
    """a glowing ball: brightest where it faces the viewer, nothing at its rim; Alpha fades it out"""
    m, new = fresh("M_SS_Blast")
    MEL.delete_all_material_expressions(m)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    node = lambda cls, x, y: MEL.create_material_expression(m, cls, x, y)
    col = node(unreal.MaterialExpressionVectorParameter, -900, 0); col.set_editor_property("parameter_name", "Color"); col.set_editor_property("default_value", unreal.LinearColor(1.0, 0.55, 0.2, 1.0))
    al = node(unreal.MaterialExpressionScalarParameter, -900, 250); al.set_editor_property("parameter_name", "Alpha"); al.set_editor_property("default_value", 1.0)
    k = node(unreal.MaterialExpressionScalarParameter, -900, 400); k.set_editor_property("parameter_name", "Glow"); k.set_editor_property("default_value", 5.0)
    fr = node(unreal.MaterialExpressionFresnel, -900, 560); fr.set_editor_property("exponent", 1.0); fr.set_editor_property("base_reflect_fraction", 0.0)
    om = node(unreal.MaterialExpressionOneMinus, -700, 560); MEL.connect_material_expressions(fr, "", om, "")
    pw = node(unreal.MaterialExpressionPower, -520, 560); pw.set_editor_property("const_exponent", 4.0); MEL.connect_material_expressions(om, "", pw, "Base")
    m1 = node(unreal.MaterialExpressionMultiply, -520, 100); MEL.connect_material_expressions(col, "", m1, "A"); MEL.connect_material_expressions(al, "", m1, "B")
    m2 = node(unreal.MaterialExpressionMultiply, -340, 250); MEL.connect_material_expressions(m1, "", m2, "A"); MEL.connect_material_expressions(k, "", m2, "B")
    m3 = node(unreal.MaterialExpressionMultiply, -160, 400); MEL.connect_material_expressions(m2, "", m3, "A"); MEL.connect_material_expressions(pw, "", m3, "B")
    MEL.connect_material_property(m3, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); eal.save_loaded_asset(m, only_if_is_dirty=False)
    assert MEL.get_statistics(m).num_pixel_shader_instructions > 0, "M_SS_Blast failed to compile"
    return m
M_BOLT, M_BLAST = bolt_material(), blast_material()
print("materials: M_SS_Bolt, M_SS_Blast")

# ---------------------------------------------------------------- effects: contrails
# The library's ribbon trail (the VR template's arrow trail in Medieval_Weapons: one particle every 2.5 m of movement,
# joined into a camera-facing ribbon) copied and tuned for width, colour and how long it lingers. A particle system's
# emitters cannot be reached from Python, so the tuning is done by USSFXLibrary.
def trail(name, size, color, life):
    p = f"/Game/Starship/FX/{name}"
    if not eal.does_asset_exist(p): assert eal.duplicate_asset("/Game/Medieval_Weapons/VFX/P_ArrowTrail", p), p
    ps = L(p)
    n = unreal.SSFXLibrary.tune_particle_system(ps, size, unreal.LinearColor(*color), life, None)
    assert n >= 4, f"{name}: only {n} modules tuned"
    eal.save_loaded_asset(ps, only_if_is_dirty=False)
    return ps
P_CONTRAIL = trail("P_SS_Contrail", 12.0, (0.25, 0.6, 1.6, 0.12), 0.34)        # the fighter's engines: blue-white
P_MISSILE_TRAIL = trail("P_SS_MissileTrail", 30.0, (4.0, 2.0, 0.8, 0.4), 1.3)  # a missile: long and warm
P_DRONE_TRAIL = trail("P_SS_DroneTrail", 45.0, (5.0, 1.0, 0.4, 0.35), 0.8)      # the target drones: red
print("effects: P_SS_Contrail, P_SS_MissileTrail, P_SS_DroneTrail (from P_ArrowTrail)")

# ---------------------------------------------------------------- level
ONLY_FIGHTER = "fighter" in sys.argv
if eal.does_asset_exist(MAP):
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
else:
    assert not ONLY_FIGHTER, "starship_level does not exist yet"
    les.new_level(MAP)
w = ues.get_editor_world(); assert w.get_path_name().startswith(MAP + "."), w.get_path_name()
def spawn(cls, loc, rot=None, label=None, folder="Starship/Space"):
    a = eas.spawn_actor_from_class(cls, loc, rot or Rot()); a.tags = [TAG]
    if label: a.set_actor_label(label)
    a.set_folder_path(folder); return a
def static(path, loc, rot=None, scale=1.0, label=None, folder="Starship/Space", material=None, collision=False, shadow=False):
    a = spawn(unreal.StaticMeshActor, loc, rot, label, folder); c = a.static_mesh_component
    c.set_static_mesh(mesh(path)); a.set_actor_scale3d(V(scale, scale, scale) if not isinstance(scale, unreal.Vector) else scale)
    if material: c.set_material(0, L(material))
    c.set_collision_profile_name("BlockAll" if collision else "NoCollision"); c.set_cast_shadow(shadow)
    return a
if not ONLY_FIGHTER:
    for a in eas.get_all_level_actors():
        if isinstance(a, unreal.WorldSettings) or a.get_class().get_name() == "Brush": continue
        eas.destroy_actor(a)
    K = "/Game/Spaceship_Kit/"
    # the stars (a sphere far outside everything), the sun and the planets: backdrop only
    static(K + "Sky_system/Asset/SM_SkySphere_desert", V(0, 0, 0), scale=9000.0, label="Stars", material=K + "Sky_system/Material/MI_stars")
    # the sun stands behind the fighter's start, so the station is seen lit; the planet hangs behind the station
    SUN = V(-0.62, -0.42, 0.52).normal()
    static(K + "Meshes/Planet/SM_Sun", SUN * 30000000.0, scale=170.0, label="Sun", material=K + "Materials/Planet/MI_sun")
    PLANET = V(0.55, 0.62, -0.5).normal() * 6200000.0
    def lit(name, parent, k):
        """the kit's planet materials shade themselves from a Light_direction parameter (toward the sun, world space):
        an instance of each with this level's sun"""
        p = f"{MATS}/{name}"
        mi = L(p) if eal.does_asset_exist(p) else at.create_asset(name, MATS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(mi, L(K + "Materials/Planet/" + parent))
        MEL.set_material_instance_vector_parameter_value(mi, "Light_direction", unreal.LinearColor(SUN.x * k, SUN.y * k, SUN.z * k, 1.0))
        MEL.update_material_instance(mi); eal.save_loaded_asset(mi, only_if_is_dirty=False)
        return p
    static(K + "Meshes/Planet/SM_planet", PLANET, None, 700.0, "Planet", material=lit("MI_SS_Planet_01", "MI_planet_01", 0.5))
    static(K + "Meshes/Planet/SM_planet", PLANET, None, 704.0, "Planet_Atmosphere", material=lit("MI_SS_Atmosphere", "MI_atmosphere", 1.0))
    static(K + "Meshes/Planet/SM_planet", V(0.75, -0.6, 0.3).normal() * 22000000.0, None, 330.0, "Moon", material=lit("MI_SS_Planet_02", "MI_planet_02", 0.5))
    static(K + "Meshes/Planet/SM_planet", V(-0.85, 0.5, 0.16).normal() * 26000000.0, None, 210.0, "Far_Planet", material=lit("MI_SS_Planet_03", "MI_planet_03", 0.5))
    sun = spawn(unreal.DirectionalLight, V(0, 0, 0), (SUN * -1.0).rotator(), "Sun_Light", "Starship/Lights")
    lc = sun.light_component; lc.set_editor_property("intensity", 9.0); lc.set_editor_property("light_color", unreal.Color(r=255, g=246, b=232, a=255))
    lc.set_editor_property("light_source_angle", 0.6); lc.set_editor_property("dynamic_shadow_distance_movable_light", 400000.0)
    # light off the planet: a dim bluish fill on the sides the sun does not reach (no shadows)
    fill = spawn(unreal.DirectionalLight, V(0, 0, 0), (PLANET.normal() * -1.0).rotator(), "Planet_Shine", "Starship/Lights")
    fc = fill.light_component; fc.set_editor_property("intensity", 2.2); fc.set_editor_property("light_color", unreal.Color(r=150, g=185, b=255, a=255)); fc.set_editor_property("cast_shadows", False)
    sky = spawn(unreal.SkyLight, V(0, 0, 0), label="SkyLight", folder="Starship/Lights"); sl = sky.light_component
    sl.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE); sl.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    sl.set_editor_property("cubemap", L(K + "Textures/T_hdri/T_hdri_1")); sl.set_editor_property("intensity", 1.3)
    ppv = spawn(unreal.PostProcessVolume, V(0, 0, 0), label="PostProcess", folder="Starship/Lights"); ppv.set_editor_property("unbound", True)
    s = ppv.settings
    s.override_auto_exposure_method = True; s.auto_exposure_method = unreal.AutoExposureMethod.AEM_HISTOGRAM
    s.override_auto_exposure_min_brightness = True; s.auto_exposure_min_brightness = 0.5
    s.override_auto_exposure_max_brightness = True; s.auto_exposure_max_brightness = 0.5
    s.override_auto_exposure_bias = True; s.auto_exposure_bias = 0.0
    s.override_bloom_intensity = True; s.bloom_intensity = 0.9
    s.override_vignette_intensity = True; s.vignette_intensity = 0.3
    s.override_motion_blur_amount = True; s.motion_blur_amount = 0.25
    ppv.set_editor_property("settings", s)
    arena = spawn(unreal.SSArena, V(0, 0, 0), label="SS_Arena", folder="Starship")
    arena.set_editor_property("half_extent", HALF)
    ws = w.get_world_settings(); ws.set_editor_property("default_game_mode", unreal.SSGameMode); ws.set_editor_property("enable_world_bounds_checks", False)
arena = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.SSArena))
for k, v in (("explosion_ps", L("/Game/Feather/Demo/StarterContent/Particles/P_Explosion")), ("explosion_fx_size", 420.0),
             ("impact_fx", L("/Niagara/DefaultAssets/Templates/Systems/DirectionalBurst")), ("impact_fx_scale", 3.0),
             ("blast_mesh", mesh("/Engine/BasicShapes/Sphere")), ("blast_material", M_BLAST), ("drone_trail_fx", None), ("drone_trail_ps", P_DRONE_TRAIL)):
    arena.set_editor_property(k, v)

# ---------------------------------------------------------------- the fighter: a kitbash in the ship frame (+X forward, +Y right, +Z up; cm)
def T(loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0):
    """rot = (pitch, yaw, roll) or a Rotator; scale a number or (x, y, z)"""
    sc = V(*scale) if isinstance(scale, (tuple, list)) else V(scale, scale, scale)
    return unreal.Transform(V(*loc), rot if isinstance(rot, unreal.Rotator) else Rot(roll=rot[2], pitch=rot[0], yaw=rot[1]), sc)
def AXES(x, y, z):
    """the rotation that takes the mesh's +X, +Y, +Z to these ship directions"""
    return unreal.MathLibrary.make_rotation_from_axes(V(*x), V(*y), V(*z))
def part(path, loc, rot=(0, 0, 0), scale=1.0, flame=False, rail=-1, material=None, centered=False):
    """centered: loc is where the middle of the mesh's bounds goes (else its pivot)"""
    tr = T(loc, rot, scale)
    if centered:
        off = unreal.MathLibrary.transform_location(T((0, 0, 0), rot, scale), mesh(path).get_bounds().origin)
        tr = T((loc[0] - off.x, loc[1] - off.y, loc[2] - off.z), rot, scale)
    p = unreal.SSPart(); p.set_editor_property("mesh", mesh(path)); p.set_editor_property("transform", tr)
    p.set_editor_property("flame", flame); p.set_editor_property("rail", rail)
    if material: p.set_editor_property("material", L(material))
    return p
HULL = "/Game/Red_Echo/Meshes/Ship/SM_ship_flying"; WING = "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Cargo_modules/SM_wing"; KIT = "/Game/Spaceship_Kit/Meshes/Ship_parts/"
GUN = KIT + "SM_turret_top"; FLAME = KIT + "SM_reactor_FX"; POD = KIT + "SM_reactor_left"; PANEL = "/Game/Spaceship_Kit/Meshes/Floor/SM_pannel_04"
MISSILE = "/Game/Military_Drone/Mesh/SM_Military_Drone_01_Separate_Grenade_02"
FIGHTER = {"parts": [], "muzzles": [], "rails": [], "thrusters": []}
FIGHTER["parts"] = [
    part(HULL, (-97, 0, -10), (0, -90, 0), 0.45),
    # stub wings (left as modelled, right mirrored)
    part(WING, (-150, -105, -6), (0, -90, 0), (0.042, 0.042, 0.02)),
    part(WING, (-150, 105, -6), (0, 90, 0), (0.042, -0.042, 0.02)),
    # third engine on the back, with a tail fin (a floor panel on edge)
    part(POD, (-330, -47, 62), (0, -90, 0), 0.085),
    part(PANEL, (-350, 0, 138), AXES((0, 0, 1), (1, 0, 0), (0, 1, 0)), (1.5, 0.62, 2.0), centered=True),
    # wing-tip cannons
    part(GUN, (-215, -385, 4), (0, -90, 0), 0.24, centered=True),
    part(GUN, (-215, 385, 4), (0, -90, 0), 0.24, centered=True),
    # missiles under the wings
    part(MISSILE, (-150, -200, -46), (0, -90, 0), 9.0, rail=0, centered=True),
    part(MISSILE, (-150, 200, -46), (0, -90, 0), 9.0, rail=1, centered=True),
    part(MISSILE, (-150, -280, -46), (0, -90, 0), 9.0, rail=2, centered=True),
    part(MISSILE, (-150, 280, -46), (0, -90, 0), 9.0, rail=3, centered=True),
    # engine flames
    part(FLAME, (-440, -150, 0), (0, -90, 0), (0.18, 0.22, 0.18), flame=True),
    part(FLAME, (-440, 150, 0), (0, -90, 0), (0.18, 0.22, 0.18), flame=True),
    part(FLAME, (-420, 0, 90), (0, -90, 0), (0.16, 0.2, 0.16), flame=True),
]
FIGHTER["muzzles"] = [(-140, -385, 10), (-140, 385, 10)]
FIGHTER["rails"] = [(-150, -200, -46), (-150, 200, -46), (-150, -280, -46), (-150, 280, -46)]
FIGHTER["thrusters"] = [(-460, -150, 0), (-460, 150, 0), (-440, 0, 90)]
FIGHTER["missile_xf"] = T((0, 0, 0), (0, -90, 0), 9.0)
FIGHTER["missile_flame_xf"] = T((-80, 0, 0), (0, -90, 0), (0.07, 0.1, 0.07))
FIGHTER["radius"] = 330.0
# (801 moves the fighter onto the first gate's axis: when only the fighter is rebuilt it stays where it is)
at = (START, Rot(roll=0, pitch=-4, yaw=math.degrees(math.atan2(-START.y, -START.x))))
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.SSFighter):
        if ONLY_FIGHTER: at = (a.get_actor_location(), a.get_actor_rotation())
        eas.destroy_actor(a)
f = spawn(unreal.SSFighter, at[0], at[1], "SS_Fighter", "Starship")
for k, v in (("parts", FIGHTER["parts"]), ("cannon_muzzles", [V(*p) for p in FIGHTER["muzzles"]]), ("missile_rails", [V(*p) for p in FIGHTER["rails"]]),
             ("thrusters", [V(*p) for p in FIGHTER["thrusters"]]), ("thruster_fx", None), ("thruster_ps", P_CONTRAIL),
             ("bolt_mesh", mesh("/Engine/BasicShapes/Cylinder")), ("bolt_material", M_BOLT),
             ("missile_mesh", mesh(MISSILE)), ("missile_mesh_transform", FIGHTER["missile_xf"]), ("missile_trail_fx", None), ("missile_trail_ps", P_MISSILE_TRAIL),
             ("missile_flame_mesh", mesh(FLAME)), ("missile_flame_transform", FIGHTER["missile_flame_xf"]), ("hull_radius", FIGHTER["radius"]), ("camera_distance", 1150.0), ("camera_height", 330.0)):
    f.set_editor_property(k, v)
print(f"fighter: {len(FIGHTER['parts'])} parts, {len(FIGHTER['muzzles'])} cannon muzzles, {len(FIGHTER['rails'])} missile rails, {len(FIGHTER['thrusters'])} thrusters at", f.get_actor_location())
les.save_current_level()
print("saved", MAP)
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
