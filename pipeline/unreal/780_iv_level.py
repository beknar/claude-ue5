"""random_isometric_village_level (/Game/RandomIsoVillage/Maps/random_isometric_village_level): procedural nucleated
village seen from a fixed isometric camera (C++ AIVVillageGenerator / AIVSection / AIVPlayerController / AIVHUD,
Source/claude_ue5/IV). Packs: House Forge modular house kit (HouseForge_01: thatch / timber / stone walls, roofs, doors)
and its Viking village props, the castle furniture kit and castle_level's openable barrels / crates, Medieval Docks
(counters, kegs, market stalls, well, sacks, trees), Village / Castle / War Camp collections, Modular Church props
(pews, candelabra, statue, gravestones), Sherwood and Old Windmill foliage.
- pieces: every mesh normalised to the village frame (front +X, footprint centred, floor at z 0; see FIVPiece). The
  house kit shares one pivot convention (walls run 3 m along -Y from their pivot with the outside on -X, roofs rise
  toward -X from the eave, foundations cover -3 m..0 on X and Y): the Adjust transforms below bring them to
  "wall centred on its segment, outside +X", "roof cell-centred, eave on +X", "floor tile centred".
- materials: M_IV_Ground (grass + trodden earth / cobbles / tilled soil / lush grass by vertex colour, world aligned),
  M_IV_Silhouette (post process: her silhouette where something stands between her and the camera, custom depth)
- level: sun + sky light + sky atmosphere, post process (fixed exposure, Lumen), a grass plane to the horizon and an
  invisible floor at z 0 (the village is flat: every section's ground mesh is visual only)
- BP_IV_GameMode: BP_SFC_Fem5Character (jrpg-fem5-tripo) + IVPlayerController (isometric camera, WASD / Xbox pad) + IVHUD
- generator at the origin + the 250 m start section built with a fixed seed (saved); PlayerStart in the middle of the square
- reveal materials: random_level's M_RT_RevealPP / M_RT_RevealCurtain (753)
Args: [no_build] [materials_only]"""
import sys, json, math, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); MEL = unreal.MaterialEditingLibrary; V = unreal.Vector
MAP = "/Game/RandomIsoVillage/Maps/random_isometric_village_level"
TAG = unreal.Name("iv_level")
MODULE, WALL_H, FLOOR_Z = 300.0, 300.0, 22.0
HF = "/Game/HouseForge_01/Meshes/"; VK = "/Game/HouseForge_01/Viking_Village_Props/Meshes/"
KIT = "/Game/Castle/Furniture/Kit/"; INT = "/Game/Castle/Interactive/Meshes/"; DK = "/Game/Hivemind/Medieval_Docks/Static_Meshes/"
FOL = "/Game/Hivemind/Medieval_Docks/Scanned_Foliage/Foliage/"; SH = "/Game/Hive_Sherwood/Meshes/"
VC = "/Game/Village_Collection/Props/"; CC = "/Game/Castle_Collection/Props/"; MC = "/Game/Modular_Church/Props/"; WC = "/Game/WarCamp_Collection/Props/"
def load(p):
    m = unreal.load_asset(p)
    if m is None: print("  MISSING mesh", p)
    return m
YAW = {"+x": 0.0, "-x": 180.0, "+y": -90.0, "-y": 90.0}
def corners(b):
    return [V(x, y, z) for x in (b.min.x, b.max.x) for y in (b.min.y, b.max.y) for z in (b.min.z, b.max.z)]
def piece(m, front="+y", mode="center", scale=(1, 1, 1), collision=True, hinge=None, moving=None, moving2=None, hinge2=None,
          size=None, shift=(0, 0, 0), actor=None):
    """mesh frame -> village frame: the mesh's `front` side turns to +X. modes: center (XY centred, bottom z 0),
    raw (rotation only: meshes sharing one pivot), back (back at x 0, Y centred, bottom z 0)"""
    if isinstance(m, str): m = load(m)
    if m is None: return None
    if isinstance(scale, (int, float)): scale = (scale,) * 3
    sc = V(*scale); rot = unreal.Rotator(roll=0.0, pitch=0.0, yaw=YAW[front])
    t0 = unreal.Transform(V(0, 0, 0), rot, sc)
    pts = [unreal.MathLibrary.transform_location(t0, c) for c in corners(m.get_bounding_box())]
    mn = V(min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)); mx = V(max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))
    tx, ty, tz = -(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z
    if mode == "raw": tx = ty = tz = 0.0
    elif mode == "back": tx = -mn.x
    t = unreal.Transform(V(tx + shift[0], ty + shift[1], tz + shift[2]), rot, sc)
    p = unreal.IVPiece()
    if actor is not None: p.actor_class = actor
    else: p.mesh = m
    p.adjust = t
    p.size = V(*size) if size else V(mx.x - mn.x, mx.y - mn.y, mx.z - mn.z)
    p.collision = collision
    if hinge is not None: p.hinge = unreal.MathLibrary.transform_location(t, V(*hinge))
    if hinge2 is not None: p.hinge2 = unreal.MathLibrary.transform_location(t, V(*hinge2))
    if moving is not None: p.moving = load(moving) if isinstance(moving, str) else moving
    if moving2 is not None: p.moving2 = load(moving2) if isinstance(moving2, str) else moving2
    return p
P = {}
def add(name, *a, **k):
    p = piece(*a, **k)
    if p is not None: P[name] = p
    return p
def fixed(name, path, loc=(0, 0, 0), yaw=0.0, scale=(1, 1, 1), size=None, collision=True):
    """a kit piece with an explicit Adjust (location after rotation), see the docstring"""
    m = load(path)
    if m is None: return None
    p = unreal.IVPiece(); p.mesh = m
    p.adjust = unreal.Transform(V(*loc), unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw), V(*scale))
    b = m.get_bounding_box(); p.size = V(*size) if size else V(b.max.x - b.min.x, b.max.y - b.min.y, b.max.z - b.min.z)
    p.collision = collision; P[name] = p
    return p
# ---------------------------------------------------------------- house kit: three styles
H = MODULE / 2
STYLES = {  # style: (folder, prefix, wall names, door mesh, door bottom below its pivot, hinge (wall frame: x inward < 0, y, z above the floor), wall z, gable offset out)
    "Timber": ("Wood/", "SM_Wood_", {"Wall": "Wall", "WallWindow": "WallWindow", "WallWindow2": "WallWindowLarge", "Doorway": "Doorway"}, "Wood/SM_Wood_Door", 114.0, (-9.8, 53.3, 2.3), 0.0, 19.0),
    "Stone": ("Stone/", "SM_Stone_", {"Wall": "Wall", "WallWindow": "WallWindow", "WallWindow2": "WallWindow_Arc", "Doorway": "Doorway"}, "Stone/SM_Reinforced_Door", 114.0, (-13.0, 54.0, 2.0), 0.0, 19.0),
    "Thatch": ("Primitive/", "SM_Primitive_", {"Wall": "Wall_V2", "WallWindow": "WallWindow", "WallWindow2": "WallWindow_V2", "Doorway": "Doorway"}, "Primitive/SM_Primitive_Door", 147.0, (-2.6, 58.1, -28.5), -13.0, 40.0),
}
for style, (folder, pre, walls, door, door_drop, hinge, wall_z, gable_out) in STYLES.items():
    b = HF + folder + pre
    fl = load((HF + "Wood/SM_Wood_" if style == "Thatch" else b) + "Foundation")
    fixed(f"{style}_Floor", fl.get_path_name().split(".")[0], loc=(H, H, -fl.get_bounding_box().max.z + 2.0), size=(MODULE, MODULE, 30))
    for k, n in walls.items(): fixed(f"{style}_{k}", b + n, loc=(0, -H, wall_z), yaw=180.0, size=(40, MODULE, WALL_H))
    fixed(f"{style}_Pillar", b + "Pillar_01", loc=(0, 0, wall_z), size=(50, 50, WALL_H))
    fixed(f"{style}_Roof", b + "Roof", loc=(H, H, wall_z), collision=False, size=(MODULE, MODULE, MODULE))
    fixed(f"{style}_RoofTrim", b + "RoofOverhang", loc=(H, H, wall_z), collision=False)
    endl, endr = ("RoofEnd_L", "RoofEnd_R") if style != "Stone" else ("Roof_End_L", "Roof_End_R")
    fixed(f"{style}_RoofEndL", b + endl, loc=(H, H, wall_z), collision=False)
    fixed(f"{style}_RoofEndR", b + endr, loc=(H, -H, wall_z), collision=False)
    tri = b if style != "Stone" else HF + "Stone/SM_"
    fixed(f"{style}_GableNeg", tri + "Wall_Tri_L", loc=(gable_out, 0, wall_z), yaw=180.0, collision=False)
    fixed(f"{style}_GablePos", tri + "Wall_Tri_R", loc=(gable_out, 0, wall_z), yaw=180.0, collision=False)
    # corner piece (eaves on its +X and -Y sides, the outer corner at (0, -3 m)): turned so the outer corner points to +X +Y
    fixed(f"{style}_CornerOut", b + "RoofCorner_Out", loc=(-H, H, wall_z), yaw=90.0, collision=False)
    # door leaf: hinge at the origin on its bottom edge, spanning +Y (the thatch door is mirrored like the kit's own houses)
    d = fixed(f"{style}_Door", HF + door, loc=(0, 0, door_drop), yaw=180.0, scale=(-1, 1, 1) if style == "Thatch" else (1, 1, 1))
    d.hinge = V(*hinge); d.size = V(12, 107, 214)
# ---------------------------------------------------------------- furniture (castle kit: front +y)
for n, m, kw in (("Bed", "SM_Kit_BedSingle", {}), ("Bed2", "SM_Kit_BedDouble", {}), ("Stool", "SM_Kit_Stool", {}), ("TableLong", "SM_Kit_TableLong", {}),
                 ("TableSmall", "SM_Kit_TableSmall", {}), ("Altar", "SM_Kit_TableLong", {}), ("PrepTable", "SM_Kit_PrepTable", {}), ("ToolBoard", "SM_Kit_ToolBoard", {}),
                 ("Shelf", "SM_Kit_ShelfRack", {}), ("Anvil", "SM_Kit_Anvil", {}), ("Fireplace", "SM_Kit_Fireplace", {"scale": (0.8, 0.8, 0.88)}),
                 ("BreadOven", "SM_Kit_BreadOven", {"scale": 0.85}), ("Bench", "SM_Kit_Bench", {}), ("QuenchTub", "SM_Kit_QuenchTub", {}), ("Firewood", "SM_Kit_Firewood", {}),
                 ("Coal", "SM_Kit_Firewood", {"scale": 0.8}), ("HayPile", "SM_Kit_HayPile", {"scale": 0.8}), ("HayBale", "SM_Kit_HayBale", {}), ("Trough", "SM_Kit_Trough", {}),
                 ("StallPartition", "SM_Kit_StallPartition", {"scale": (0.6, 1, 0.8)}), ("Pitchfork", "SM_Kit_Pitchfork", {"collision": False}),
                 ("Ladder", "SM_Kit_Ladder", {"collision": False}), ("Rug", "SM_Kit_Rug", {"collision": False}), ("Rug2", "SM_Kit_FurRug", {"collision": False}),
                 ("Candle", "SM_Kit_CandleStick", {"collision": False}), ("Bowl", "SM_Kit_Bowl", {"collision": False}), ("Bread", "SM_Kit_BreadLoaf", {"collision": False}),
                 ("Bread2", "SM_Kit_BreadRound", {"collision": False}), ("Cheese", "SM_Kit_Cheese", {"collision": False}), ("Tankard", "SM_Kit_Tankard", {"collision": False})):
    add(n, KIT + m, front="+y", **kw)
add("Forge", HF + "Misc/SM_Forge", front="+x")
add("Counter", DK + "Props/Furniture/SM_Counter_01", front="+x"); add("Keg", DK + "Props/SM_Large_Keg", front="+x")
add("TableRound", DK + "Props/Furniture/Round_SM_Table_Round", front="+x"); add("Chair", VK + "Props/WoodChairKit/SM_WoodChair_01a", front="+x")
add("Sack", DK + "Props/SM_Sack_01", front="+x"); add("Sack2", DK + "Props/SM_Sack_02", front="+x")
add("WeaponStand", DK + "Props/SM_WeaponStand", front="+x"); add("Hammer", DK + "Props/SM_Hammer", front="+x", collision=False)
add("FoodStand", VK + "Props/FoodStorage/SM_FoodStorage_01a", front="+x"); add("FoodStand2", VK + "Props/FoodStorage/SM_FoodStorage_02a", front="+x")
add("FoodStand3", VK + "Props/BoxStorage/SM_BoxStorage_01a", front="+x", scale=0.8)
add("Planks", SH + "SM_Wooden_Planks_B", front="+x", scale=0.6); add("Logs", VK + "Props/WoodLogs/sm_WoodLog_01d", front="+y")
add("Bucket", VC + "SM_WoodWaterBucket/Meshes/FBX/SM_WoodWaterBucket", front="+x"); add("Crib", VC + "SM_House_BabyCrib/Meshes/FBX/SM_House_BabyCrib_SM_House_BabyCrib", front="+x")
add("ArmorStand", VC + "SM_House_OldArmorStand/Meshes/FBX/SM_House_OldArmorStand", front="+x")
add("Balance", CC + "SM_Balance/Meshes/FBX/SM_Balance", front="+x", collision=False, scale=0.7)
add("Bookshelf", CC + "SM_WoodBookshelf/Meshes/FBX/SM_WoodBookshelf", front="+y", scale=(0.7, 0.8, 0.85)); add("Dresser", CC + "SM_Castle_Dresser/Meshes/FBX/SM_Castle_Dresser_SM_Castle_Dresser", front="+y")
add("Throne", CC + "SM_Castle_Throne/Meshes/FBX/SM_Castle_Throne_SM_Castle_Throne", front="+y", scale=0.85)
add("Pew", MC + "SM_Chapel_Bench/Meshes/FBX/SM_Chapel_Bench_SM_Chapel_Bench", front="+x", scale=(1, 0.9, 1))
add("Candelabrum", MC + "SM_Chapel_Candelabrum/Meshes/FBX/SM_Chapel_Candelabrum_SM_Chapel_Candelabrum_Base", front="+x", scale=0.8)
add("Statue", MC + "SM_Chapel_Statue/Meshes/FBX/SM_Chapel_Statue", front="+x", scale=0.6)
# ---------------------------------------------------------------- containers (all open with F)
add("Chest", KIT + "SM_Kit_ChestBody", front="+y", moving=KIT + "SM_Kit_ChestLid", hinge=(0, -26, 45))
add("Trunk", KIT + "SM_Kit_TrunkBody", front="+y", moving=KIT + "SM_Kit_TrunkLid", hinge=(0, -31, 50))
add("Wardrobe", KIT + "SM_Kit_WardrobeBody", front="+y", moving=KIT + "SM_Kit_WardrobeDoorL", hinge=(-53, 30, 8), moving2=KIT + "SM_Kit_WardrobeDoorR", hinge2=(53, 30, 8))
CJ = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\castle_interactive\interactive.json"))["containers"]
for n, src in (("Barrel", "SM_barrel_01"), ("Barrel2", "SM_barrel_02"), ("Crate", "SM_crate_01"), ("Crate2", "SM_crate_02")):
    h = CJ[src]["hinge"]
    front = ("-y" if h[1] > 0 else "+y") if abs(h[1]) >= abs(h[0]) else ("-x" if h[0] > 0 else "+x")
    add(n, INT + f"{src}_body", front=front, moving=INT + f"{src}_lid", hinge=tuple(h))
# ---------------------------------------------------------------- outdoors
add("Well", VC + "SM_OldWell/Meshes/FBX/SM_OldWell_SM_OldWell_Stone", front="+x", mode="raw", size=(180, 180, 280))      # stone ring and its winch: two meshes, one pivot
add("WellRoof", VC + "SM_OldWell/Meshes/FBX/SM_OldWell_SM_OldWell_Wood", front="+x", mode="raw", collision=False)
add("MarketCross", CC + "SM_Fountain/Meshes/FBX/SM_Fountain", front="+x")
for i in (1, 2, 3):
    add(f"Stall{i}", DK + "Props/Market/SM_Market_Stand_01", front="-y", mode="raw", actor=eal.load_blueprint_class(f"/Game/Hivemind/Medieval_Docks/Blueprints/BP_MarketStand_0{i}"))
add("Cart", VC + "SM_WoodenCart/Meshes/FBX/SM_WoodenCart", front="+y"); add("Cart2", VC + "SM_WoodWagons_Var/Meshes/FBX/SM_WoodWagons_Var2", front="+x")
add("HayStack", VC + "SM_HayPile/Meshes/SM_HayPile_SM_HayPile_hay", front="+x", scale=0.8)
add("WoodPile", SH + "SM_WoodHolder", front="+y"); add("ChopBlock", WC + "SM_Outskirts_CuttedWoodTrunk/Meshes/FBX/SM_Outskirts_CuttedWoodTrunk_SM_Outskirts_CuttedWoodTrunk", front="+x", scale=0.7)
add("Fence", VC + "SM_PlantationFence/Meshes/FBX/SM_PlantationFence", front="+y")
add("Sign", VK + "Props/SignBoard/SM_SignBoard_02a", front="+x"); add("TorchPost", SH + "SM_Torch_02", front="+x", scale=1.5)
add("NoticeBoard", VC + "SM_WantedBoard/Meshes/FBX/SM_WantedBoard_Wood", front="+y")
add("Scarecrow", WC + "SM_Garrison_Dummy/Meshes/FBX/SM_Garrison_Dummy", front="+y")
add("Pumpkins", VK + "Props/FoodKit_01a/SM_FoodKitPumpkins_01a", front="+x", scale=1.5, collision=False)
add("Plant", FOL + "WildCarot/Meshes/SM_WildCarrot_S_01", front="+x", scale=0.6, collision=False); add("Plant2", FOL + "EagleFern/Meshes/SM_EagleFern_S_02", front="+x", scale=0.7, collision=False)
for i in range(1, 6): add(f"Grave{i}", MC + f"SM_Graveyard/Meshes/FBX/SM_Graveyard_Var{i}", front="+y")
B_ = FOL + "EuropeanBeech/Meshes/SM_EuropeanBeech_"
for n, m in (("Tree1", B_ + "L_01"), ("Tree2", B_ + "M_01"), ("Tree3", B_ + "L_02"), ("Tree4", B_ + "M_01"), ("Fruit", B_ + "S_02"), ("Fruit2", B_ + "S_01"),
             ("Conifer", FOL + "SilverFir/Meshes/SM_SilverFir_M_01"), ("Conifer2", FOL + "SilverFir/Meshes/SM_SilverFir_S_01")):
    add(n, m, front="+x", mode="raw")
P["Fruit"].adjust = unreal.Transform(V(0, 0, 0), unreal.Rotator(), V(1.6, 1.6, 1.6)); P["Fruit"].size = V(260, 240, 320)
for n, m, s in (("Bush1", SH + "SM_Bush_02", 1.6), ("Bush2", FOL + "EagleFern/Meshes/SM_EagleFern_M_01", 1.0), ("Bush3", FOL + "EagleFern/Meshes/SM_EagleFern_S_01", 1.2),
                ("Grass1", SH + "SM_Grass_2", 0.8), ("Grass2", SH + "SM_Grass_3", 0.8), ("Grass3", SH + "SM_WildGrass_S_01", 0.7), ("Grass4", SH + "SM_WildGrass_S_02", 0.8),
                ("Flower1", "/Game/Old_Windmill/Meshes/Flower/SM_flower_clump_01", 0.8), ("Flower2", "/Game/Old_Windmill/Meshes/Flower/SM_flower_clump_03", 0.8),
                ("Flower3", "/Game/Old_Windmill/Meshes/Flower/SM_flower_clump_04", 0.8), ("Flower", "/Game/Old_Windmill/Meshes/Flower/SM_flower_clump_01", 0.8),
                ("Rock1", SH + "SM_Rock_01", 0.4), ("Rock2", SH + "SM_Rock_02", 0.4), ("Rock3", SH + "SM_Rock_03", 0.35)):
    add(n, m, front="+x", mode="raw", scale=s, collision=False)
print("pieces:", len(P), sorted(P))
effects = {"HearthFire": unreal.load_asset("/Game/MysticDungeon/VFX/P_TorchFire")}

# ---------------------------------------------------------------- materials
D = "/Game/RandomIsoVillage/Materials"
def fresh(name):
    """rebuilt in place (the levels reference these materials)"""
    p = f"{D}/{name}"
    if eal.does_asset_exist(p):
        m = unreal.load_asset(p); MEL.delete_all_material_expressions(m); return m
    return at.create_asset(name, D, unreal.Material, unreal.MaterialFactoryNew())
def sampler_type(t):
    comp = t.get_editor_property("compression_settings"); srgb = t.get_editor_property("srgb")
    if t.get_editor_property("virtual_texture_streaming"):
        if comp == unreal.TextureCompressionSettings.TC_NORMALMAP: return unreal.MaterialSamplerType.SAMPLERTYPE_VIRTUAL_NORMAL
        return unreal.MaterialSamplerType.SAMPLERTYPE_VIRTUAL_COLOR if srgb else unreal.MaterialSamplerType.SAMPLERTYPE_VIRTUAL_LINEAR_COLOR
    if comp == unreal.TextureCompressionSettings.TC_NORMALMAP: return unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
    if comp in (unreal.TextureCompressionSettings.TC_GRAYSCALE, unreal.TextureCompressionSettings.TC_ALPHA): return unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE if not srgb else unreal.MaterialSamplerType.SAMPLERTYPE_GRAYSCALE
    if comp == unreal.TextureCompressionSettings.TC_MASKS: return unreal.MaterialSamplerType.SAMPLERTYPE_MASKS
    return unreal.MaterialSamplerType.SAMPLERTYPE_COLOR if srgb else unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
def ground_material():
    m = fresh("M_IV_Ground")
    S = "/Game/Hive_Sherwood/Textures/"; C = "/Game/Hivemind/Medieval_Docks/Textures/Cobbles/"
    LAYERS = {"grass": (S + "T_Grass_BC", S + "T_Grass_N", S + "T_Grass_ORM", 380.0), "lush": (S + "T_ForestFloor_BC", S + "T_ForestFloor_N", S + "T_ForestFloor_ORM", 430.0),
              "dirt": (S + "T_Ground_BC", S + "T_Ground_N", S + "T_Ground_ORM", 320.0), "cobble": (C + "T_Cobble_Basecolour", C + "T_Cobble_Normal", C + "T_Cobble_ORMH", 260.0)}
    node = lambda cls, x, y: MEL.create_material_expression(m, cls, x, y)
    wp = node(unreal.MaterialExpressionWorldPosition, -3000, 0)
    xy = node(unreal.MaterialExpressionComponentMask, -2850, 0); xy.set_editor_property("r", True); xy.set_editor_property("g", True); xy.set_editor_property("b", False)
    MEL.connect_material_expressions(wp, "", xy, "")
    def uv(tile, y):
        d = node(unreal.MaterialExpressionDivide, -2700, y); d.set_editor_property("const_b", tile); MEL.connect_material_expressions(xy, "", d, "A"); return d
    def tex(path, u, y):
        t = unreal.load_asset(path); s = node(unreal.MaterialExpressionTextureSample, -2500, y)
        s.set_editor_property("texture", t); s.set_editor_property("sampler_type", sampler_type(t)); s.set_editor_property("sampler_source", unreal.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS)
        MEL.connect_material_expressions(u, "", s, "UVs"); return s
    L = {}; y = -1200
    for k, (bc, n, orm, tile) in LAYERS.items():
        u = uv(tile, y); L[k] = (tex(bc, u, y), tex(n, u, y + 200), tex(orm, u, y + 400)); y += 650
    def lerp(a, b, alpha, x, yy):
        l = node(unreal.MaterialExpressionLinearInterpolate, x, yy)
        MEL.connect_material_expressions(a, "", l, "A"); MEL.connect_material_expressions(b, "", l, "B"); MEL.connect_material_expressions(alpha, "", l, "Alpha"); return l
    vc = node(unreal.MaterialExpressionVertexColor, -2500, 2000)
    vm = node(unreal.MaterialExpressionScalarParameter, -2500, 2200); vm.set_editor_property("parameter_name", "VertexMasks"); vm.set_editor_property("default_value", 1.0)
    def mask(pin, yy):
        mm = node(unreal.MaterialExpressionMultiply, -2250, yy); MEL.connect_material_expressions(vc, pin, mm, "A"); MEL.connect_material_expressions(vm, "", mm, "B"); return mm
    dirt, cobble, soil, lush = mask("R", 2000), mask("G", 2080), mask("B", 2160), mask("A", 2240)
    # macro variation: brightness and patches of the second grass
    mt = unreal.load_asset("/Engine/EngineMaterials/T_Default_MacroVariation")
    def macro(tile, yy):
        s = node(unreal.MaterialExpressionTextureSample, -2500, yy); s.set_editor_property("texture", mt); s.set_editor_property("sampler_type", sampler_type(mt))
        s.set_editor_property("sampler_source", unreal.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS); MEL.connect_material_expressions(uv(tile, yy), "", s, "UVs"); return s
    mac, mac2 = macro(7000.0, 2500), macro(1900.0, 2700)
    patch = node(unreal.MaterialExpressionSmoothStep, -2250, 2500); patch.set_editor_property("const_min", 0.5); patch.set_editor_property("const_max", 0.72)
    MEL.connect_material_expressions(mac, "R", patch, "Value")
    lushmax = node(unreal.MaterialExpressionMax, -2100, 2400); MEL.connect_material_expressions(patch, "", lushmax, "A"); MEL.connect_material_expressions(lush, "", lushmax, "B")
    bright = node(unreal.MaterialExpressionLinearInterpolate, -2250, 2700); bright.set_editor_property("const_a", 0.84); bright.set_editor_property("const_b", 1.12)
    MEL.connect_material_expressions(mac2, "G", bright, "Alpha")
    soil_tint = node(unreal.MaterialExpressionConstant3Vector, -1500, -700); soil_tint.set_editor_property("constant", unreal.LinearColor(0.42, 0.30, 0.20, 1))
    outs = {}
    for i, ch in enumerate(("bc", "n", "orm")):
        yy = -300 + i * 600
        a = lerp(L["grass"][i], L["lush"][i], lushmax, -1900, yy)
        # tilled soil: the earth layer, darker and browner
        if ch == "bc":
            dk = node(unreal.MaterialExpressionMultiply, -1700, yy + 320); MEL.connect_material_expressions(L["dirt"][i], "", dk, "A"); MEL.connect_material_expressions(soil_tint, "", dk, "B")
            sm = node(unreal.MaterialExpressionMultiply, -1550, yy + 320); MEL.connect_material_expressions(dk, "", sm, "A"); sm.set_editor_property("const_b", 2.2)
            b = lerp(a, sm, soil, -1400, yy + 60)
        else:
            b = lerp(a, L["dirt"][i], soil, -1400, yy + 60)
        c = lerp(b, L["dirt"][i], dirt, -1150, yy + 120)
        outs[ch] = lerp(c, L["cobble"][i], cobble, -900, yy + 180)
    mul = node(unreal.MaterialExpressionMultiply, -600, -300)
    MEL.connect_material_expressions(outs["bc"], "", mul, "A"); MEL.connect_material_expressions(bright, "", mul, "B")
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(outs["n"], "", unreal.MaterialProperty.MP_NORMAL)
    rg = node(unreal.MaterialExpressionComponentMask, -600, 900); rg.set_editor_property("r", False); rg.set_editor_property("g", True); rg.set_editor_property("b", False)
    ao = node(unreal.MaterialExpressionComponentMask, -600, 1000); ao.set_editor_property("r", True); ao.set_editor_property("g", False); ao.set_editor_property("b", False)
    MEL.connect_material_expressions(outs["orm"], "", rg, ""); MEL.connect_material_expressions(outs["orm"], "", ao, "")
    MEL.connect_material_property(rg, "", unreal.MaterialProperty.MP_ROUGHNESS); MEL.connect_material_property(ao, "", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.recompile_material(m); eal.save_loaded_asset(m)
    st = MEL.get_statistics(m); assert st.num_pixel_shader_instructions > 0, "M_IV_Ground failed to compile"
    fp = f"{D}/MI_IV_FarGround"
    if not eal.does_asset_exist(fp): at.create_asset("MI_IV_FarGround", D, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi = unreal.load_asset(fp); MEL.set_material_instance_parent(mi, m); MEL.set_material_instance_scalar_parameter_value(mi, "VertexMasks", 0.0)
    eal.save_loaded_asset(mi, only_if_is_dirty=False)
    print("M_IV_Ground compiled: pixel instructions", st.num_pixel_shader_instructions, "| samplers", st.num_samplers)
    return m, mi
def silhouette_material():
    """post process: on her pixels (custom stencil 1; needs r.CustomDepth=3) where her custom depth lies behind the
    scene depth she is hidden: draw her shape in a warm tint"""
    m = fresh("M_IV_Silhouette")
    m.set_editor_property("material_domain", unreal.MaterialDomain.MD_POST_PROCESS)
    m.set_editor_property("blendable_location", unreal.BlendableLocation.BL_SCENE_COLOR_AFTER_TONEMAPPING)
    node = lambda cls, x, y: MEL.create_material_expression(m, cls, x, y)
    def st(i, y):
        s = node(unreal.MaterialExpressionSceneTexture, -900, y); s.set_editor_property("scene_texture_id", i); return s
    code = """
float3 c = Scene.rgb;
float hid = (Stencil.r > 0.5 && Custom.r > Depth.r + 12.0) ? 1.0 : 0.0;
float3 tint = lerp(Col.rgb, c, 0.35);
return lerp(c, tint, hid * Col.a);
"""
    cu = node(unreal.MaterialExpressionCustom, -300, 0); cu.set_editor_property("code", code); cu.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    ins = []
    for nm in ("Scene", "Depth", "Custom", "Stencil", "Col"):
        ci = unreal.CustomInput(); ci.set_editor_property("input_name", nm); ins.append(ci)
    cu.set_editor_property("inputs", ins)
    col = node(unreal.MaterialExpressionVectorParameter, -900, 300); col.set_editor_property("parameter_name", "Color"); col.set_editor_property("default_value", unreal.LinearColor(1.0, 0.45, 0.7, 0.75))
    assert MEL.connect_material_expressions(st(unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0, -300), "Color", cu, "Scene")
    assert MEL.connect_material_expressions(st(unreal.SceneTextureId.PPI_SCENE_DEPTH, -100), "Color", cu, "Depth")
    assert MEL.connect_material_expressions(st(unreal.SceneTextureId.PPI_CUSTOM_DEPTH, 100), "Color", cu, "Custom")
    assert MEL.connect_material_expressions(st(unreal.SceneTextureId.PPI_CUSTOM_STENCIL, 200), "Color", cu, "Stencil")
    assert MEL.connect_material_expressions(col, "RGBA", cu, "Col")
    MEL.connect_material_property(cu, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); eal.save_loaded_asset(m)
    s = MEL.get_statistics(m); assert s.num_pixel_shader_instructions > 0, "M_IV_Silhouette failed to compile"
    print("M_IV_Silhouette compiled: pixel instructions", s.num_pixel_shader_instructions)
    return m
ground, far_ground = ground_material()
silhouette = silhouette_material()
if "materials_only" in sys.argv: raise SystemExit

# ---------------------------------------------------------------- game mode (fem5 + isometric controller + village HUD)
G = "/Game/RandomIsoVillage/Blueprints"; GM = f"{G}/BP_IV_GameMode"
if not eal.does_asset_exist(GM): eal.duplicate_asset("/Game/RandomLevel/Blueprints/BP_RL_GameMode", GM)
gm = unreal.load_asset(GM); cdo = unreal.get_default_object(gm.generated_class())
cdo.set_editor_property("default_pawn_class", unreal.load_asset("/Game/SFCityLevel/Blueprints/BP_SFC_Fem5Character").generated_class())
cdo.set_editor_property("hud_class", unreal.IVHUD); cdo.set_editor_property("player_controller_class", unreal.IVPlayerController)
unreal.BlueprintEditorLibrary.compile_blueprint(gm); eal.save_loaded_asset(gm, only_if_is_dirty=False)
# ---------------------------------------------------------------- level
if eal.does_asset_exist(MAP):
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
else:
    les.new_level(MAP)
w = ues.get_editor_world(); assert w.get_path_name().startswith(MAP + "."), w.get_path_name()
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.WorldSettings) or a.get_class().get_name() == "Brush": continue
    eas.destroy_actor(a)
def spawn(cls, loc, rot=None, label=None, folder="IsoVillage/Environment"):
    a = eas.spawn_actor_from_class(cls, loc, rot or unreal.Rotator()); a.tags = [TAG]
    if label: a.set_actor_label(label)
    a.set_folder_path(folder); return a
# the camera looks north-east (+X +Y): the sun comes from behind the viewer's left, so both walls facing the camera
# are lit (one more than the other) and shadows fall away to the right
sun = spawn(unreal.DirectionalLight, V(0, 0, 8000), unreal.Rotator(roll=0, pitch=-48, yaw=68), "Sun")
lc = sun.light_component; lc.set_editor_property("intensity", 7.5); lc.set_editor_property("atmosphere_sun_light", True); lc.set_editor_property("light_source_angle", 1.2)
lc.set_editor_property("light_color", unreal.Color(r=255, g=244, b=226, a=255))
atm = spawn(unreal.SkyAtmosphere, V(0, 0, 0), label="SkyAtmosphere")
# no aerial perspective: at cinematic quality it is ray-marched per pixel as if the view were a perspective one and
# paints a blue dome over the bottom of the orthographic frame
atm.get_component_by_class(unreal.SkyAtmosphereComponent).set_editor_property("aerial_pespective_view_distance_scale", 0.0)
sky = spawn(unreal.SkyLight, V(0, 0, 600), label="SkyLight"); sky.light_component.set_editor_property("real_time_capture", True)
sky.light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE); sky.light_component.set_editor_property("intensity", 2.5)
ppv = spawn(unreal.PostProcessVolume, V(0, 0, 0), label="PostProcess"); ppv.set_editor_property("unbound", True)
s = ppv.settings
# exposure fixed: daylight outside, and the cut-away interiors keep their own firelit look
s.override_auto_exposure_method = True; s.auto_exposure_method = unreal.AutoExposureMethod.AEM_HISTOGRAM
s.override_auto_exposure_min_brightness = True; s.auto_exposure_min_brightness = 0.3
s.override_auto_exposure_max_brightness = True; s.auto_exposure_max_brightness = 0.3
s.override_auto_exposure_bias = True; s.auto_exposure_bias = 0.4
s.override_bloom_intensity = True; s.bloom_intensity = 0.25
s.override_vignette_intensity = True; s.vignette_intensity = 0.25
s.override_dynamic_global_illumination_method = True; s.dynamic_global_illumination_method = unreal.DynamicGlobalIlluminationMethod.LUMEN
s.override_reflection_method = True; s.reflection_method = unreal.ReflectionMethod.LUMEN
s.override_motion_blur_amount = True; s.motion_blur_amount = 0.0
ppv.set_editor_property("settings", s)
plane = unreal.load_asset("/Engine/BasicShapes/Plane")
far = spawn(unreal.StaticMeshActor, V(0, 0, -6), label="FarGround")
far.static_mesh_component.set_static_mesh(plane); far.set_actor_scale3d(V(8000, 8000, 1)); far.static_mesh_component.set_material(0, far_ground)
far.static_mesh_component.set_collision_profile_name("NoCollision"); far.static_mesh_component.set_cast_shadow(False)
floor = spawn(unreal.StaticMeshActor, V(0, 0, 0), label="Floor")      # what she walks on: invisible, everywhere
floor.static_mesh_component.set_static_mesh(plane); floor.set_actor_scale3d(V(8000, 8000, 1)); floor.set_actor_hidden_in_game(True)
floor.static_mesh_component.set_collision_profile_name("BlockAll"); floor.static_mesh_component.set_cast_shadow(False); floor.static_mesh_component.set_visibility(False)
gen = spawn(unreal.IVVillageGenerator, V(0, 0, 0), label="IV_VillageGenerator", folder="IsoVillage")
for k, v in (("pieces", P), ("effects", effects), ("ground_material", ground), ("silhouette_material", silhouette), ("module", MODULE), ("wall_height", WALL_H), ("floor_height", FLOOR_Z),
             ("reveal_post_material", unreal.load_asset("/Game/RandomLevel/Materials/M_RT_RevealPP")), ("reveal_curtain_material", unreal.load_asset("/Game/RandomLevel/Materials/M_RT_RevealCurtain")),
             ("reveal_duration", 7.0),
             # generate when the edge of the village is about to come on screen (she sees some 17 m along the world axes)
             ("trigger_distance", 2000.0), ("safety_distance", 1300.0)):
    gen.set_editor_property(k, v)
ws = w.get_world_settings(); ws.set_editor_property("default_game_mode", gm.generated_class()); ws.set_editor_property("kill_z", -3000.0)
if "no_build" not in sys.argv:
    gen.build_start_section()
    sec = gen.get_section(unreal.IntPoint(0, 0))
    kinds = {}
    for i in range(sec.get_num_buildings()): kinds[sec.get_building_kind(i)] = kinds.get(sec.get_building_kind(i), 0) + 1
    print("start section:", sec.get_num_buildings(), "buildings,", sec.get_num_doors(), "doors,", sec.get_num_containers(), "container parts,",
          sec.get_editor_property("num_instances"), "instances,", sec.get_editor_property("num_lights"), "lights,", round(sec.get_editor_property("generate_ms")), "ms")
    print("buildings by kind:", kinds)
    print("unreachable doors / containers from the square:", sec.count_unreachable_doors(V(0, 0, 0)))
ps = spawn(unreal.PlayerStart, V(0, 0, 110), unreal.Rotator(roll=0, pitch=0, yaw=45), "IV_PlayerStart")
les.save_current_level()
print("saved", MAP)
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
