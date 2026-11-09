"""Heaven, the modern city in its shield (the user's list of 2026-11-08b, docs/improvements9.txt, its fourth phase: "a modern
city that is surrounded by a shimmering shield. it is characterized by modern skyscrapers, office buildings, modern shops,
modern streets, modern vehicles navigating the streets ... the outside and entrance of the dungeon is a foreboding research
facility called 'Kratos Aurorim Research, LLC'"): one of the wilderness's towns on the brokenspire level, planned as a modern
city (C++: the generator's TownPlan 5 for the town FRDWildWorld places south-west of Kethrys Spire; RDTownPlan.cpp's bModern,
RDHeaven.cpp). Its town section's theme is "Heaven": a piece the town asks for is "Heaven.<name>" where this script made one.
This script gives the brokenspire level's generator:
- two materials of its own (/Game/RandomDungeon/Heaven): M_HV_Surface (a colour, metal, roughness and glow: concrete, glass,
  steel, asphalt, paving, light panels as its instances) and M_HV_Shield (the shield: translucent, its edge glowing)
- the city's pieces made here from boxes merged into meshes (/Game/RandomDungeon/Heaven/Meshes), each in the frame of the piece
  it stands for (measured 2026-11-09: the house kit's walls about their line, the door's leaf along +Y from its hinge, the
  town wall's courses 114 cm thick and 311 cm high): "Modern.*" (the buildings' walls, windows, glass walls, doorways, glass
  doors, floors, pillars, flat roofs, parapets, roof plant), "Lab.*" (the research facility's glass walls, doorway, floor,
  light-panel ceiling, roof, the dark glass block over it, the security door), "Heaven.Road" and "Heaven.Paving", and the
  wall and its towers in concrete and glass ("Heaven.Town.CityWall", ...Slit, ...Win, ...Door, ...Parapet, ...CastleRoof)
- the cars: Vehicles_Vol1's civilian cars, taxi, police car and bus, each blueprint's parts merged into one mesh
  ("Heaven.Car_1".."Heaven.Car_6")
- the packs' pieces: SpaceColony2086's tower floors and rooftop (a tower's floors over its lobby), the street light, bench, bus
  stop, hydrant and bin of Mod_Building_01 / City_Assets_Kit, the shield's sphere (StylizedShieldsVol1's hexagon sphere)
- the fortress's level for the town (TownDungeons["Heaven"]: heaven_fortress, 909)
- its people and quests from SourceArt/heaven/city.json: townsfolk and quests of the town "Heaven" (those of another run of
  this script replaced; the other towns' kept)
Run after 882 / 886 / 890 / 892 / 894 / 896 / 906. C++ first (build_cpp.ps1). Args: [rebuild] (makes the merged meshes again)"""
import os, sys, json, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); eal = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools()
V = unreal.Vector
MAP = "/Game/RandomDungeon/Maps/brokenspire"
DUNGEON = "/Game/RandomDungeon/Maps/heaven_fortress"
HV = "/Game/RandomDungeon/Heaven"; HVM = HV + "/Meshes"
SA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "claude_ue5", "SourceArt", "heaven"))
D = json.load(open(os.path.join(SA, "city.json"), encoding="utf-8"))
TOWN = D["town"]
REBUILD = "rebuild" in sys.argv[1:]
YAW = {"+x": 0.0, "-x": 180.0, "+y": -90.0, "-y": 90.0}
missing = []
P = {}

w = ues.get_editor_world()
if not w.get_path_name().startswith(MAP + "."): les.load_level(MAP)


def load(p):
    m = unreal.load_asset(p)
    if m is None: missing.append(p)
    return m


# ---------------------------------------------------------------- the materials
def master():
    path = HV + "/M_HV_Surface"
    if eal.does_asset_exist(path): return unreal.load_asset(path)
    m = AT.create_asset("M_HV_Surface", HV, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("used_with_instanced_static_meshes", True)
    col = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -700, -200)
    col.set_editor_property("parameter_name", "Color"); col.set_editor_property("default_value", unreal.LinearColor(0.5, 0.5, 0.5, 1.0))
    met = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -700, 0)
    met.set_editor_property("parameter_name", "Metallic"); met.set_editor_property("default_value", 0.0)
    rou = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -700, 120)
    rou.set_editor_property("parameter_name", "Roughness"); rou.set_editor_property("default_value", 0.6)
    glo = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -700, 260)
    glo.set_editor_property("parameter_name", "Glow"); glo.set_editor_property("default_value", 0.0)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -400, 260)
    MEL.connect_material_expressions(col, "", mul, "A"); MEL.connect_material_expressions(glo, "", mul, "B")
    MEL.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(met, "", unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(rou, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    print("HV1 compiling M_HV_Surface")
    MEL.recompile_material(m); eal.save_loaded_asset(m, False)
    return m


def shield_master():
    path = HV + "/M_HV_Shield"
    if eal.does_asset_exist(path): return unreal.load_asset(path)
    m = AT.create_asset("M_HV_Shield", HV, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    m.set_editor_property("used_with_static_lighting", False)
    fr = MEL.create_material_expression(m, unreal.MaterialExpressionFresnel, -800, 0)
    fr.set_editor_property("exponent", 2.2); fr.set_editor_property("base_reflect_fraction", 0.0)
    col = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -800, -250)
    col.set_editor_property("parameter_name", "Color"); col.set_editor_property("default_value", unreal.LinearColor(0.35, 0.75, 1.0, 1.0))
    glo = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -800, -100)
    glo.set_editor_property("parameter_name", "Glow"); glo.set_editor_property("default_value", 2.5)
    # (the shimmer: the glow breathing a little with time)
    tm = MEL.create_material_expression(m, unreal.MaterialExpressionTime, -1000, 250)
    sn = MEL.create_material_expression(m, unreal.MaterialExpressionSine, -800, 250); sn.set_editor_property("period", 6.0)
    MEL.connect_material_expressions(tm, "", sn, "")
    k1 = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -800, 380); k1.set_editor_property("r", 0.2)
    sh = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -600, 300)
    MEL.connect_material_expressions(sn, "", sh, "A"); MEL.connect_material_expressions(k1, "", sh, "B")
    one = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -600, 420); one.set_editor_property("r", 1.0)
    br = MEL.create_material_expression(m, unreal.MaterialExpressionAdd, -450, 320)
    MEL.connect_material_expressions(sh, "", br, "A"); MEL.connect_material_expressions(one, "", br, "B")
    f2 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -600, 0)
    MEL.connect_material_expressions(fr, "", f2, "A"); MEL.connect_material_expressions(glo, "", f2, "B")
    k2 = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -600, 120); k2.set_editor_property("r", 0.12)
    f3 = MEL.create_material_expression(m, unreal.MaterialExpressionAdd, -450, 60)
    MEL.connect_material_expressions(f2, "", f3, "A"); MEL.connect_material_expressions(k2, "", f3, "B")
    em = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -300, -100)
    MEL.connect_material_expressions(col, "", em, "A"); MEL.connect_material_expressions(f3, "", em, "B")
    em2 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -150, -50)
    MEL.connect_material_expressions(em, "", em2, "A"); MEL.connect_material_expressions(br, "", em2, "B")
    MEL.connect_material_property(em2, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    k3 = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -600, 560); k3.set_editor_property("r", 0.5)
    op = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -450, 520)
    MEL.connect_material_expressions(fr, "", op, "A"); MEL.connect_material_expressions(k3, "", op, "B")
    k4 = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -450, 640); k4.set_editor_property("r", 0.03)
    op2 = MEL.create_material_expression(m, unreal.MaterialExpressionAdd, -300, 560)
    MEL.connect_material_expressions(op, "", op2, "A"); MEL.connect_material_expressions(k4, "", op2, "B")
    MEL.connect_material_property(op2, "", unreal.MaterialProperty.MP_OPACITY)
    print("HV1 compiling M_HV_Shield")
    MEL.recompile_material(m); eal.save_loaded_asset(m, False)
    return m


SURF = master(); SHIELD = shield_master()


def mi(name, rgb, metal=0.0, rough=0.6, glow=0.0):
    path = HV + "/" + name
    if not eal.does_asset_exist(path): AT.create_asset(name, HV, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    m = unreal.load_asset(path); MEL.set_material_instance_parent(m, SURF)
    MEL.set_material_instance_vector_parameter_value(m, "Color", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    MEL.set_material_instance_scalar_parameter_value(m, "Metallic", metal)
    MEL.set_material_instance_scalar_parameter_value(m, "Roughness", rough)
    MEL.set_material_instance_scalar_parameter_value(m, "Glow", glow)
    MEL.update_material_instance(m); eal.save_loaded_asset(m, False)
    return m


MAT = {"stone": mi("MI_HV_Stone", (0.2, 0.21, 0.23), 0.0, 0.7), "brick": mi("MI_HV_Brick", (0.36, 0.17, 0.12), 0.0, 0.85),
       "concrete": mi("MI_HV_Concrete", (0.5, 0.5, 0.48), 0.0, 0.85), "dark": mi("MI_HV_DarkConcrete", (0.16, 0.17, 0.19), 0.0, 0.8),
       "glass": mi("MI_HV_Glass", (0.025, 0.05, 0.075), 1.0, 0.06), "steel": mi("MI_HV_Steel", (0.13, 0.14, 0.16), 0.85, 0.32),
       "white": mi("MI_HV_White", (0.82, 0.84, 0.86), 0.0, 0.45), "asphalt": mi("MI_HV_Asphalt", (0.045, 0.045, 0.05), 0.0, 0.92),
       "paving": mi("MI_HV_Paving", (0.42, 0.41, 0.39), 0.0, 0.85), "roof": mi("MI_HV_Roof", (0.3, 0.3, 0.31), 0.0, 0.9),
       "panel": mi("MI_HV_LightPanel", (0.9, 0.95, 1.0), 0.0, 0.5, 6.0), "red": mi("MI_HV_RedLight", (1.0, 0.06, 0.04), 0.0, 0.5, 12.0),
       "warm": mi("MI_HV_WarmGlass", (0.06, 0.05, 0.03), 0.9, 0.1, 0.0)}
SHIELD_MI = SHIELD

# ---------------------------------------------------------------- meshes from boxes
CUBE = load("/Engine/BasicShapes/Cube")


def boxes(name, parts):
    """a mesh merged from boxes (x0, x1, y0, y1, z0, z1, material key), its pivot the world's origin; made again with 'rebuild'"""
    path = f"{HVM}/{name}"
    if eal.does_asset_exist(path) and not REBUILD: return unreal.load_asset(path)
    if eal.does_asset_exist(path):
        eal.delete_asset(path)
    acts = []
    for (x0, x1, y0, y1, z0, z1, mk) in parts:
        a = eas.spawn_actor_from_object(CUBE, V((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        a.set_actor_scale3d(V(max(x1 - x0, 0.2) / 100.0, max(y1 - y0, 0.2) / 100.0, max(z1 - z0, 0.2) / 100.0))
        a.static_mesh_component.set_material(0, MAT[mk])
        acts.append(a)
    o = unreal.MergeStaticMeshActorsOptions()
    # (the merge puts "SM_" before the name it is given)
    o.set_editor_property("base_package_name", f"{HVM}/{name[3:]}"); o.set_editor_property("destroy_source_actors", True); o.set_editor_property("spawn_merged_actor", False)
    ms = o.get_editor_property("mesh_merging_settings")
    ms.set_editor_property("pivot_type", unreal.MeshMergePivotType.WORLD_ORIGIN); ms.set_editor_property("merge_physics_data", True)
    ms.set_editor_property("merge_materials", False); ms.set_editor_property("generate_light_map_uv", False)
    o.set_editor_property("mesh_merging_settings", ms)
    unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).merge_static_mesh_actors(acts, o)
    for a in acts:
        try: a.destroy_actor()
        except Exception: pass
    m = unreal.load_asset(path)
    if m is None: missing.append(path)
    # (a merge makes its mesh in memory only: saved, or it is gone at the next start (884 heaven's hv3 found none))
    else: eal.save_loaded_asset(m, False)
    return m


def raw_piece(key, mesh, size=None, collision=True, material=None, hinge=None):
    """a piece in its mesh's own frame (the meshes made here are made in their piece's frame)"""
    if mesh is None: return None
    p = unreal.RDPiece(); p.mesh = mesh; p.adjust = unreal.Transform()
    b = mesh.get_bounding_box()
    p.size = V(*size) if size else V(b.max.x - b.min.x, b.max.y - b.min.y, b.max.z - b.min.z)
    p.collision = collision
    if material is not None: p.material = material
    if hinge is not None: p.hinge = V(*hinge)
    P[key] = p
    return p


def corners(b): return [V(x, y, z) for x in (b.min.x, b.max.x) for y in (b.min.y, b.max.y) for z in (b.min.z, b.max.z)]


def piece(key, path, front="+x", mode="center", scale=(1, 1, 1), collision=True, material=None):
    """894's normalisation: center: XY centred, bottom z 0; raw: rotation only"""
    m = load(path) if isinstance(path, str) else path
    if m is None: return None
    if isinstance(scale, (int, float)): scale = (scale,) * 3
    rot = unreal.Rotator(roll=0.0, pitch=0.0, yaw=YAW[front])
    t0 = unreal.Transform(V(0, 0, 0), rot, V(*scale))
    pts = [unreal.MathLibrary.transform_location(t0, c) for c in corners(m.get_bounding_box())]
    mn = V(min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)); mx = V(max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))
    tx, ty, tz = -(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z
    if mode == "raw": tx = ty = tz = 0.0
    if mode == "pole": tx = ty = 0.0; tz = -mn.z
    p = unreal.RDPiece(); p.mesh = m
    p.adjust = unreal.Transform(V(tx, ty, tz), rot, V(*scale))
    p.size = V(mx.x - mn.x, mx.y - mn.y, mx.z - mn.z); p.collision = collision
    if material is not None: p.material = material
    P[key] = p
    return p


# ---------------------------------------------------------------- the buildings ("Modern.*", the house kit's frame: +X out of the
# wall's line, a segment's middle at y 0, a storey 300 high)
H = 151.0
raw_piece("Modern.Wall", boxes("SM_HV_Wall", [(-20, 20, -H, H, 0, 300, "concrete"), (20, 23, -H, H, 96, 104, "dark")]), size=(40, 300, 300))
raw_piece("Modern.WallWindow", boxes("SM_HV_Window", [(-20, 20, -H, H, 0, 90, "concrete"), (-20, 20, -H, H, 262, 300, "concrete"),
                                                         (-20, 20, -H, -122, 90, 262, "concrete"), (-20, 20, 122, H, 90, 262, "concrete"),
                                                         (-4, 4, -122, 122, 90, 262, "glass"), (-7, 7, -4, 4, 90, 262, "steel"), (-7, 7, -122, 122, 174, 180, "steel")]), size=(40, 300, 300))
raw_piece("Modern.WallWindow2", boxes("SM_HV_GlassWall", [(-20, 20, -H, H, 0, 18, "dark"), (-20, 20, -H, H, 284, 300, "dark"),
                                                          (-10, 10, -H, -146, 18, 284, "steel"), (-10, 10, 146, H, 18, 284, "steel"),
                                                          (-4, 4, -146, 146, 18, 284, "glass"), (-8, 8, -3, 3, 18, 284, "steel")]), size=(40, 300, 300))
raw_piece("Modern.Doorway", boxes("SM_HV_Doorway", [(-20, 20, -H, -60, 0, 300, "concrete"), (-20, 20, 60, H, 0, 300, "concrete"),
                                                    (-20, 20, -60, 60, 224, 300, "concrete"), (-22, 22, -64, -58, 0, 228, "steel"), (-22, 22, 58, 64, 0, 228, "steel"),
                                                    (-22, 22, -64, 64, 222, 230, "steel")]), size=(40, 300, 300))
# (the glass door's leaf: in its pivot's frame, from the hinge along +Y (AddTownDoor), as House Forge's door 107 x 214)
raw_piece("Modern.Door", boxes("SM_HV_Door", [(-4, 4, 1, 7, 0, 213, "steel"), (-4, 4, 99, 105, 0, 213, "steel"), (-4, 4, 7, 99, 0, 8, "steel"),
                                              (-4, 4, 7, 99, 205, 213, "steel"), (-2, 2, 7, 99, 8, 205, "glass"), (-9, 9, 88, 92, 90, 130, "steel")]),
          size=(12, 107, 214), hinge=(-13, 54, 2))
raw_piece("Modern.Floor", boxes("SM_HV_Floor", [(-H, H, -H, H, -30, 2, "white")]), size=(300, 300, 30))
raw_piece("Modern.Pillar", boxes("SM_HV_Pillar", [(-24, 24, -24, 24, 0, 300, "dark")]), size=(48, 48, 300))
raw_piece("Modern.Roof", boxes("SM_HV_Roof", [(-H, H, -H, H, 0, 24, "roof")]), size=(300, 300, 24), collision=False)
raw_piece("Modern.Parapet", boxes("SM_HV_Parapet", [(-22, 8, -H, H, 0, 105, "concrete"), (-24, 10, -H, H, 105, 112, "steel")]), size=(30, 300, 112), collision=False)
raw_piece("Modern.RoofUnit", boxes("SM_HV_RoofUnit", [(-110, 110, -80, 80, 0, 130, "steel"), (-60, 60, -60, 60, 130, 150, "dark")]), collision=False)

# (two more facings, by the building's seed (RDTownPlan.cpp's Style 8 and 9): dark stone, brick red; the same shapes)
for setn, wall, band in (("Modern2", "stone", "steel"), ("Modern3", "brick", "concrete")):
    sfx = setn[-1]
    raw_piece(f"{setn}.Wall", boxes(f"SM_HV{sfx}_Wall", [(-20, 20, -H, H, 0, 300, wall), (20, 23, -H, H, 96, 104, band)]), size=(40, 300, 300))
    raw_piece(f"{setn}.WallWindow", boxes(f"SM_HV{sfx}_Window", [(-20, 20, -H, H, 0, 90, wall), (-20, 20, -H, H, 262, 300, wall), (-20, 20, -H, -122, 90, 262, wall),
                                                                 (-20, 20, 122, H, 90, 262, wall), (-4, 4, -122, 122, 90, 262, "glass"), (-7, 7, -4, 4, 90, 262, "steel"),
                                                                 (-7, 7, -122, 122, 174, 180, "steel")]), size=(40, 300, 300))
    raw_piece(f"{setn}.WallWindow2", boxes(f"SM_HV{sfx}_GlassWall", [(-20, 20, -H, H, 0, 18, wall), (-20, 20, -H, H, 284, 300, wall), (-10, 10, -H, -146, 18, 284, "steel"),
                                                                     (-10, 10, 146, H, 18, 284, "steel"), (-4, 4, -146, 146, 18, 284, "glass"), (-8, 8, -3, 3, 18, 284, "steel")]), size=(40, 300, 300))
    raw_piece(f"{setn}.Doorway", boxes(f"SM_HV{sfx}_Doorway", [(-20, 20, -H, -60, 0, 300, wall), (-20, 20, 60, H, 0, 300, wall), (-20, 20, -60, 60, 224, 300, wall),
                                                               (-22, 22, -64, -58, 0, 228, "steel"), (-22, 22, 58, 64, 0, 228, "steel"), (-22, 22, -64, 64, 222, 230, "steel")]), size=(40, 300, 300))
    raw_piece(f"{setn}.Parapet", boxes(f"SM_HV{sfx}_Parapet", [(-22, 8, -H, H, 0, 105, wall), (-24, 10, -H, H, 105, 112, "steel")]), size=(30, 300, 112), collision=False)
    for part in ("Door", "Floor", "Pillar", "Roof", "RoofUnit"): P[f"{setn}.{part}"] = P[f"Modern.{part}"]

# ---------------------------------------------------------------- the research facility ("Lab.*", the dungeon's frame: the room's face
# +X, a wall's middle on its edge)
raw_piece("Lab.Wall", boxes("SM_HV_LabWall", [(-15, 15, -H, H, 0, 30, "dark"), (-5, 5, -H, H, 30, 290, "glass"), (-15, 15, -H, H, 290, 300, "steel"),
                                               (-9, 9, -H, -146, 30, 290, "steel"), (-9, 9, 146, H, 30, 290, "steel")]), size=(30, 300, 300))
raw_piece("Lab.Doorway", boxes("SM_HV_LabDoorway", [(-15, 15, -H, -60, 0, 300, "dark"), (-15, 15, 60, H, 0, 300, "dark"), (-15, 15, -60, 60, 224, 300, "dark"),
                                                     (-17, 17, -64, 64, 222, 230, "steel")]), size=(30, 300, 300))
raw_piece("Lab.Floor", boxes("SM_HV_LabFloor", [(-H, H, -H, H, -20, 2, "white")]), size=(300, 300, 22))
raw_piece("Lab.Ceil", boxes("SM_HV_LabCeil", [(-H, H, -H, H, 0, 12, "white"), (-70, 70, -70, 70, -2, 0, "panel")]), size=(300, 300, 12), collision=False)
raw_piece("Lab.Roof", boxes("SM_HV_LabRoof", [(-H, H, -H, H, 0, 22, "roof")]), size=(300, 300, 22), collision=False)
raw_piece("Lab.Block", boxes("SM_HV_Block", [(-50, 50, -50, 50, 0, 100, "glass")]), size=(100, 100, 100), collision=False)
raw_piece("Lab.Gate", boxes("SM_HV_Vault", [(-30, 10, -170, -110, 0, 340, "dark"), (-30, 10, 110, 170, 0, 340, "dark"), (-30, 10, -170, 170, 300, 340, "dark"),
                                            (-14, 0, -110, 110, 0, 300, "steel"), (-16, -14, -110, 110, 286, 294, "red"), (-16, -14, -3, 3, 0, 286, "dark")]), collision=False)

# ---------------------------------------------------------------- the streets
raw_piece("Heaven.Road", boxes("SM_HV_Road", [(-H, H, -H, H, 0, 2, "asphalt")]), size=(300, 300, 2), collision=False)
raw_piece("Heaven.Paving", boxes("SM_HV_Paving", [(-H, H, -H, H, 0, 3, "paving")]), size=(300, 300, 3), collision=False)

# ---------------------------------------------------------------- the wall and its towers: concrete and glass in the castle
# kit's boxes (Town.CityWall x -57..57 y -158..158 z 0..311, the parapet 0..235, the tower's door 112 x 240)
W = 158.0
raw_piece("Heaven.Town.CityWall", boxes("SM_HV_CityWall", [(-57, 57, -W, W, 0, 110, "concrete"), (-8, 8, -W, W, 110, 300, "glass"), (-10, 10, -W, -150, 110, 300, "steel"),
                                                            (-10, 10, 150, W, 110, 300, "steel"), (-57, 57, -W, W, 300, 311, "steel")]), size=(114, 315, 311))
raw_piece("Heaven.Town.CityWallSlit", P["Heaven.Town.CityWall"].mesh, size=(114, 315, 311))
raw_piece("Heaven.Town.CityWallWin", P["Heaven.Town.CityWall"].mesh, size=(114, 315, 311))
raw_piece("Heaven.Town.CityWallDoor", boxes("SM_HV_CityWallDoor", [(-57, 57, -W, -56, 0, 311, "concrete"), (-57, 57, 56, W, 0, 311, "concrete"), (-57, 57, -56, 56, 240, 311, "concrete")]),
          size=(114, 315, 311), collision=False)
raw_piece("Heaven.Town.Parapet", boxes("SM_HV_Rail", [(-5, 5, -W, W, 100, 108, "steel"), (-4, 4, -W, -150, 0, 108, "steel"), (-4, 4, -4, 4, 0, 108, "steel")]), size=(10, 315, 108), collision=False)
raw_piece("Heaven.Town.CastleRoof", boxes("SM_HV_Slab", [(-152, 152, -H, H, 0, 21, "concrete")]), size=(305, 303, 21))
raw_piece("Heaven.Town.CWall", P["Heaven.Town.CityWall"].mesh, size=(114, 315, 311))


def refit(key, src, design, collision=False):
    """a piece of Heaven's own filling the box another piece fills (its adjusted bounds), made by design(mn, mx)"""
    gs = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator)).get_editor_property("pieces")
    s = gs.get(unreal.Name(src))
    if not s or not s.mesh: missing.append(src); return None
    bb = s.mesh.get_bounding_box()
    ts = [unreal.MathLibrary.transform_location(s.adjust, c) for c in corners(bb)]
    mn = (min(q.x for q in ts), min(q.y for q in ts), min(q.z for q in ts)); mx = (max(q.x for q in ts), max(q.y for q in ts), max(q.z for q in ts))
    print("HV1 refit", key, "in", src, [round(v) for v in mn], [round(v) for v in mx])
    return raw_piece(key, boxes("SM_HV_" + key.split(".")[-1], design(mn, mx)), size=(mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2]), collision=collision)


# (the wall's towers: a flat steel roof and a mast with its red light in place of the cone)
refit("Heaven.Town.TowerRoof", "Town.TowerRoof", lambda mn, mx: [(mn[0], mx[0], mn[1], mx[1], mn[2], mn[2] + 30, "steel"),
                                                                    ((mn[0] + mx[0]) / 2 - 8, (mn[0] + mx[0]) / 2 + 8, (mn[1] + mx[1]) / 2 - 8, (mn[1] + mx[1]) / 2 + 8, mn[2], mn[2] + 600, "steel"),
                                                                    ((mn[0] + mx[0]) / 2 - 18, (mn[0] + mx[0]) / 2 + 18, (mn[1] + mx[1]) / 2 - 18, (mn[1] + mx[1]) / 2 + 18, mn[2] + 600, mn[2] + 636, "red")])

# ---------------------------------------------------------------- the furniture: the rooms' own (the town's furnishing asks for it by
# name; Heaven's theme takes these), each laid with its long side where the piece it stands for has its (Y, or X for a bed)
def furn(key, path, long_y=True, collision=True):
    m = load(path)
    if m is None: return None
    b = m.get_bounding_box(); bx, by = b.max.x - b.min.x, b.max.y - b.min.y
    front = ("+y" if bx > by else "+x") if long_y else ("+x" if bx >= by else "+y")
    return piece(key, m, front=front, collision=collision)


OE = "/Game/Office_Environment/Assets/"; OK = "/Game/Office_Asset_Kit/Assets/"; SB = "/Game/Seating_Bedding_Kit/Assets/"
furn("Heaven.Desk", OE + "MM00406_Office_Desk/SM_MM00406_Office_Desk")
furn("Heaven.Chair", OE + "MM00043-PC_Chair/SM_MM43_PC_Chair")
furn("Heaven.Bookshelf", OK + "MM00456_Book_Shelving/SM_MM00456_Book_Shelve_Long_fbx")
furn("Heaven.Bookshelf2", OE + "MM00405_Storage_Shelving/SM_MM00405_Storage_Shelving")
furn("Heaven.CandleStand", OE + "MM00267_Planters/SM_MM00267_Planters_Freestanding_1")
furn("Heaven.TableLong", OE + "MM00849_Lunch_Tables/SM_MM00849_Lunch_Tables_Big")
furn("Heaven.TableSmall", OE + "MM00438_Cocktail_Table/SM_MM00438_Cocktail_Table")
furn("Heaven.Bench", SB + "MM00465_Sofa_Bench/SM_MM00465_Sofa_Bench_fbx")
furn("Heaven.Bed", SB + "MM00452_Bed/SM_MM00452-Bed", long_y=False)
furn("Heaven.ShelfRack", OE + "MM00395_Shelving/SM_MM00395_Shelving")
furn("Heaven.PrepTable", OE + "MM00480_Kitchen_F/SM_MM00480_BottomShelf_Big_02")
furn("Heaven.BreadOven", OE + "MM00483_Fridge/SM_MM00483_Fridge")

# ---------------------------------------------------------------- the packs' pieces
SC = "/Game/SpaceColony2086/Meshes/"
piece("Heaven.TowerMid", SC + "SM_Module03_Tower01_MiddleFloors01", collision=False)
piece("Heaven.TowerTop", SC + "SM_Module03_Tower01_Rooftop01", collision=False)
sl = load("/Game/Mod_Building_01/Assets/MM00284_Exterior_Light/SM_MM00284_Exterior_Light_Streetlight")
if sl:
    bb = sl.get_bounding_box()
    # (its arm out over the street: the arm along the mesh's longer side, away from its pole at the origin)
    arm = "+y" if (bb.max.y - bb.min.y) > (bb.max.x - bb.min.x) else "+x"
    if arm == "+y" and -bb.min.y > bb.max.y: arm = "-y"
    if arm == "+x" and -bb.min.x > bb.max.x: arm = "-x"
    piece("Heaven.StreetLight", sl, front=arm, mode="pole")
    print("HV1 street light: its arm", arm, "bounds y", round(bb.min.y), round(bb.max.y), "x", round(bb.min.x), round(bb.max.x))
CK = "/Game/City_Assets_Kit/Assets/"
piece("Heaven.Bench", CK + "MM00015-Street_Bench/SM_MM00015-Street_Bench_fbx", front="+y")
piece("Heaven.BusStop", CK + "MM00274_Bus_Stop/SM_MM00274_Bus_Stop_fbx", front="+y")
piece("Heaven.Hydrant", CK + "MM00281_Fire_Hydrant/SM_MM00281_Fire_Hydrant")
piece("Heaven.Bin", CK + "MM00278_Trashcan_1/SM_MM00278_Trashcan_1_fbx")
piece("Heaven.TrafficLight", CK + "MM00277_Traffic_Light/SM_MM00277_Traffic_Light_fbx")
piece("Heaven.Dome", "/Game/StylizedShieldsVol1/Models/SM_Sphere_Hexagons_01", mode="raw", collision=False, material=SHIELD_MI)


# ---------------------------------------------------------------- the cars: each blueprint's parts merged into one mesh
def car_mesh(name, bp_path):
    path = f"{HVM}/{name}"
    if eal.does_asset_exist(path) and not REBUILD: return unreal.load_asset(path)
    if eal.does_asset_exist(path): eal.delete_asset(path)
    cls = unreal.EditorAssetLibrary.load_blueprint_class(bp_path)
    if cls is None: missing.append(bp_path); return None
    bp = eas.spawn_actor_from_class(cls, V(0, 0, 0), unreal.Rotator(0, 0, 0))
    acts = []
    for c in bp.get_components_by_class(unreal.StaticMeshComponent):
        m = c.get_editor_property("static_mesh")
        if not m or not c.is_visible(): continue
        a = eas.spawn_actor_from_object(m, c.get_world_location(), c.get_world_rotation())
        a.set_actor_scale3d(c.get_world_scale())
        for k, mat in enumerate(c.get_materials()): a.static_mesh_component.set_material(k, mat)
        acts.append(a)
    bp.destroy_actor()
    if not acts: missing.append(bp_path + " (no parts)"); return None
    o = unreal.MergeStaticMeshActorsOptions()
    # (the merge puts "SM_" before the name it is given)
    o.set_editor_property("base_package_name", f"{HVM}/{name[3:]}"); o.set_editor_property("destroy_source_actors", True); o.set_editor_property("spawn_merged_actor", False)
    ms = o.get_editor_property("mesh_merging_settings")
    ms.set_editor_property("pivot_type", unreal.MeshMergePivotType.WORLD_ORIGIN); ms.set_editor_property("merge_physics_data", True)
    ms.set_editor_property("merge_materials", False); ms.set_editor_property("generate_light_map_uv", False)
    o.set_editor_property("mesh_merging_settings", ms)
    unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).merge_static_mesh_actors(acts, o)
    for a in acts:
        try: a.destroy_actor()
        except Exception: pass
    m = unreal.load_asset(path)
    if m: eal.save_loaded_asset(m, False)
    print("HV1 car", name, "from", bp_path.split("/")[-1], "parts", len(acts), "made" if m else "FAILED")
    return m


VB = "/Game/Vehicles_Vol1/Blueprints/"
CARS = [("SM_HV_Car_1", VB + "BP_MM00588-Civilian_Car_01"), ("SM_HV_Car_2", VB + "BP_MM00582-Civilian_Car_02"), ("SM_HV_Car_3", VB + "BP_MM00589-Civilian_Car_03"),
        ("SM_HV_Car_4", VB + "BP_MM00588-Civilian_TAXI"), ("SM_HV_Car_5", VB + "BP_MM00617-Police_Car"), ("SM_HV_Car_6", VB + "BP_MM00598-Bus_01")]
CAR_FRONT = "+y"           # (the cars' long side is their Y; which way is front is looked at in 884 heaven's picture)
for k, (nm, bp) in enumerate(CARS):
    m = car_mesh(nm, bp)
    if m: piece(f"Heaven.Car_{k + 1}", m, front=CAR_FRONT)

# ---------------------------------------------------------------- into the generator
g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
pieces = g.get_editor_property("pieces")
for k in [k for k in pieces.keys() if str(k).startswith(("Modern.", "Lab.", "Heaven."))]: pieces.pop(k)
for k, v in P.items(): pieces[k] = v
g.set_editor_property("pieces", pieces)
td = g.get_editor_property("town_dungeons"); td[TOWN] = DUNGEON; g.set_editor_property("town_dungeons", td)
print("HV1 pieces:", len(P), "| missing:", missing)

# ---------------------------------------------------------------- its people and quests (906's way)
clips = {}
def pack_clips(pack):
    if pack not in clips:
        a = f"/Game/{pack}/Demoscene_UE5/Animations/"
        idle = unreal.load_asset(a + "MM_Idle"); walk = unreal.load_asset(a + "MM_Walk_InPlace"); speed = 150.0
        fwd = unreal.load_asset(a + "MM_Walk_Fwd")
        if fwd:
            n = unreal.AnimationLibrary.get_num_frames(fwd)
            dd = unreal.AnimationLibrary.get_bone_pose_for_frame(fwd, "root", n - 1, False).translation - unreal.AnimationLibrary.get_bone_pose_for_frame(fwd, "root", 0, False).translation
            if dd.length() > 50: speed = dd.length() / fwd.get_play_length()
            dst = f"/Game/RandomDungeon/Anims/Town/AS_{pack}_WalkLocked"
            if not eal.does_asset_exist(dst): eal.duplicate_asset(fwd.get_path_name().split(".")[0], dst)
            wl = unreal.load_asset(dst)
            if wl:
                wl.set_editor_property("force_root_lock", True); wl.set_editor_property("enable_root_motion", False)
                eal.save_loaded_asset(wl, False)
                walk = wl
        clips[pack] = (idle, walk, speed)
    return clips[pack]
defs = []
for t in D["townsfolk"]:
    mesh = unreal.load_asset(f"/Game/{t['pack']}/{t['mesh']}")
    idle, walk, speed = pack_clips(t["pack"])
    if not (mesh and idle):
        print("  MISSING townsperson", t["name"], t["mesh"], "mesh" if not mesh else "idle"); missing.append(t["name"]); continue
    x = unreal.RDTownsfolkDef()
    x.set_editor_property("parts", [])
    for k, v in (("name", t["name"]), ("role", getattr(unreal.RDTownRole, t["role"].upper())), ("town", TOWN), ("title", t["title"]), ("calling", t.get("calling", "")),
                 ("mesh", mesh), ("idle", idle), ("walk", walk), ("walk_clip_speed", speed), ("walk_speed", 120.0),
                 ("scale", float(t.get("scale", 1.0))), ("mesh_yaw", -90.0), ("mesh_z", 0.0), ("count", int(t.get("count", 1))), ("lines", t.get("lines", [])), ("topics", t.get("topics", []))):
        x.set_editor_property(k, v)
    defs.append(x)
quests = []
for q in D["quests"]:
    x = unreal.RDQuestDef()
    for k, v in (("id", q["id"]), ("giver", q["giver"]), ("town", TOWN), ("title", q["title"]), ("offer", q["offer"]), ("done", q.get("done", "")), ("goal", q["goal"]),
                 ("count", int(q.get("count", 1))), ("gold", int(q.get("gold", 0))), ("reward_item", q.get("reward", "None")), ("after", q.get("after", "None")), ("hint", q.get("hint", ""))):
        x.set_editor_property(k, v)
    quests.append(x)
keep_f = [d_ for d_ in g.get_editor_property("townsfolk") if str(d_.get_editor_property("town")) != TOWN]
keep_q = [q_ for q_ in g.get_editor_property("quests") if str(q_.get_editor_property("town")) != TOWN]
g.set_editor_property("townsfolk", keep_f + defs); g.set_editor_property("quests", keep_q + quests)
print("HV1", len(defs), "townsfolk of", len(D["townsfolk"]), "|", len(quests), "quests | kept", len(keep_f), "townsfolk and", len(keep_q), "quests of other towns | missing:", missing)
les.save_current_level()
print("HV1 saved", ues.get_editor_world().get_path_name())
import gc
del g, pieces, defs, quests, keep_f, keep_q, td
gc.collect()
