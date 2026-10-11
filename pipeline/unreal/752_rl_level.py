"""random_level (/Game/RandomLevel/Maps/random_level): procedural medieval town (C++ ARTTownGenerator, Source/claude_ue5/RT).
- level: sun + sky atmosphere + sky light + clouds + height fog, post process; a far ground plane (MI_RT_FarGround, z -240 just under the lowest terrain,
  80 km) so the horizon never shows the void beyond the generated cells (and catches anything that would fall)
- generator at the origin, configured from SourceArt/random_level/templates.json (750 docks buildings + 750b Sherwood
  cabins) and the scatter lists below (Sherwood trees / grass / rocks / tents / props, Medieval Docks foliage, carts,
  barrels, well, market stalls, Village Collection hay / logs / carts); solid props without collision are dropped
- BuildStartSquare(): the 500 m x 500 m start square (fixed seed) is generated in the editor and saved with the level
- PlayerStart on the origin crossroads (middle of the start square); BP_RL_GameMode -> BP_SFC_Fem5Character (jrpg-fem5-tripo,
  36 cm capsule, foot IK, all her animations). Tag 'rl_level' on the static actors.
Args: [no_build]"""
import sys, json, math, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); V = unreal.Vector
MAP = "/Game/RandomLevel/Maps/random_level"
TAG = unreal.Name("rl_level")
T = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\random_level\templates.json"))
# ---------------------------------------------------------------- assets by name
ar = unreal.AssetRegistryHelpers.get_asset_registry()
NAMES = {}
for root in ("/Game/Hive_Sherwood/Meshes", "/Game/Hivemind/Medieval_Docks", "/Game/Village_Collection", "/Game/Castle/Furniture/Kit"):
    for ad in ar.get_assets_by_path(root, recursive=True):
        if str(ad.asset_class_path.asset_name) == "StaticMesh": NAMES.setdefault(str(ad.asset_name), str(ad.package_name))
def mesh(n):
    p = NAMES.get(n)
    if not p: print("  missing mesh", n); return None
    return unreal.load_asset(p)
def has_collision(m):
    bs = m.get_editor_property("body_setup")
    if not bs: return False
    if bs.get_editor_property("collision_trace_flag") == unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE: return True
    g = bs.get_editor_property("agg_geom")
    return any(len(g.get_editor_property(k)) for k in ("sphere_elems", "box_elems", "sphyl_elems", "convex_elems", "tapered_capsule_elems"))
dropped = []
def items(spec, collision, cull=0.0):
    out = []
    for n, wgt, smin, smax, rad in spec:
        m = mesh(n)
        if not m: continue
        if collision and not has_collision(m): dropped.append(n); continue
        it = unreal.RTScatterItem(); it.mesh = m; it.weight = wgt; it.scale = unreal.Vector2D(smin, smax); it.collision = collision
        it.cull_distance = cull; it.radius = rad; out.append(it)
    return out
TREES = items([("SM_EuropeanBeech_L_01", 1, .8, 1.1, 380), ("SM_EuropeanBeech_L_02", 1, .8, 1.1, 380), ("SM_EuropeanBeech_L_03", 1, .8, 1.1, 380),
               ("SM_EuropeanBeech_M_01", 1.2, .8, 1.2, 280), ("SM_SilverFir_L_01", .6, .8, 1.1, 300), ("SM_SilverFir_M_01", .6, .8, 1.2, 250),
               ("SM_EuropeanBeech_XS_01", .8, .9, 1.2, 200), ("SM_Tree", .8, .8, 1.1, 300)], True)
BUSHES = items([("SM_Bush_02", 1, .7, 1.2, 80), ("SM_EagleFern_M_01", 1, .8, 1.3, 70), ("SM_EagleFern_S_01", 1, .8, 1.3, 50), ("SM_WildCarrot_M_01", .7, .8, 1.2, 50)], False, 9000.0)
GRASS = items([("SM_Grass_2", 1, .8, 1.3, 25), ("SM_Grass_3", 1, .8, 1.3, 25), ("SM_WildGrass_S_01", 1, .8, 1.3, 25), ("SM_WildGrass_S_02", 1, .8, 1.3, 25),
               ("SM_WildGrass_M_02", .8, .8, 1.2, 30), ("SM_WildGrass_M_01", .8, .8, 1.2, 30)], False, 6000.0)
ROCKS = items([("SM_Rock_01", 1, .5, .9, 0), ("SM_Rock_02", 1, .5, .9, 0), ("SM_Rock_03", 1, .5, .9, 0), ("SM_Small_Rock_A", 1, .8, 1.2, 0), ("SM_Small_Rock_B", 1, .8, 1.2, 0)], True)
YARD = items([("SM_Barrel_01", 2, .9, 1.1, 0), ("SM_Wooden_Box", 1.5, .9, 1.1, 0), ("SM_Wooden_Box_A", 1, .9, 1.1, 0), ("SM_Wood_A", 1, .9, 1.1, 0),
              ("SM_WoodHolder", .7, .9, 1.1, 0), ("SM_Dummy_01", .3, 1, 1, 0), ("SM_HaySquare_SM_HaySquare", 1, .9, 1.1, 0), ("SM_WoodenCart", .6, 1, 1, 0),
              ("SM_WoodLog_Var1", .8, .9, 1.1, 0), ("SM_WoodLog_Var2", .8, .9, 1.1, 0), ("SM_AleCart", .4, 1, 1, 0), ("SM_Cart_01", .5, 1, 1, 0),
              ("SM_Cart_Small", .5, 1, 1, 0), ("SM_Sack_01", .8, 1, 1, 0), ("SM_WoodBox", .8, 1, 1, 0), ("SM_Bucket", .5, 1, 1, 0)], True)
MARKET = items([("SM_Barrel_01", 2, .9, 1.1, 0), ("SM_Sack_01", 1.5, 1, 1, 0), ("SM_Sack_02", 1.5, 1, 1, 0), ("SM_Large_Keg", .8, 1, 1, 0),
                ("SM_Market_Cart_01", .8, 1, 1, 0), ("SM_Ship_Cargo_01", .8, 1, 1, 0), ("SM_Ship_Cargo_02", .8, 1, 1, 0), ("SM_Wooden_Box", 1, 1, 1, 0),
                ("SM_WoodenStand_Small", .6, 1, 1, 0), ("SM_Table_Small", .5, 1, 1, 0)], True)
TENTS = items([("SM_Tent_A", 1, 1, 1, 0), ("SM_Tent_B", 1, 1, 1, 0), ("SM_Tent_C", 1, 1, 1, 0), ("SM_Tent_D", 1, 1, 1, 0)], True)
WELLS = items([("SM_Well", 1, 1, 1, 0)], True)
print("scatter: trees", len(TREES), "bushes", len(BUSHES), "grass", len(GRASS), "rocks", len(ROCKS), "yard", len(YARD), "market", len(MARKET), "tents", len(TENTS), "wells", len(WELLS), "| dropped (no collision):", dropped)
# ---------------------------------------------------------------- templates
KIND = {"chest": unreal.RTAddKind.CHEST, "trunk": unreal.RTAddKind.TRUNK, "wardrobe": unreal.RTAddKind.WARDROBE, "washstand": unreal.RTAddKind.WASHSTAND}
WEIGHT = {"05": 1.0, "06": 0.5, "03": 0.8, "cabin_A": 0.5, "cabin_B": 0.5, "cabin_C": 0.5}
templates = []
for k, t in T.items():
    if not t.get("entry"): print("  skip", k, "(no entrance)"); continue
    bt = unreal.RTBuildingTemplate()
    bt.name = k; bt.purpose = t["purpose"]
    if t.get("level"): bt.level = unreal.load_asset(t["level"])
    else: bt.actor_class = unreal.EditorAssetLibrary.load_blueprint_class(t["actor_class"])
    bt.bounds_min = unreal.Vector2D(t["lo"][0], t["lo"][1]); bt.bounds_max = unreal.Vector2D(t["hi"][0], t["hi"][1])
    bt.floor_z = t["floor_z"]; bt.entry_mid = unreal.Vector2D(*t["entry"]["mid"]); bt.entry_out = unreal.Vector2D(*t["entry"]["out"])
    bt.weight = WEIGHT.get(k, 1.0)
    doors = []
    for d in t["doors"]:
        if "closed_yaw" not in d: continue
        dd = unreal.RTDoorDef(); dd.mesh = unreal.load_asset(d["mesh"]); dd.location = V(*d["loc"]); dd.source_yaw = d["rot"][1]; dd.closed_yaw = d["closed_yaw"]
        dd.scale = V(*d["scale"]); dd.exterior = d.get("exterior", False); doors.append(dd)
    bt.doors = doors
    lids = []
    for l in t["lids"]:
        ld = unreal.RTLidDef(); ld.mesh = unreal.load_asset(l["mesh"])
        ld.transform = unreal.Transform(V(*l["loc"]), unreal.Rotator(roll=l["rot"][2], pitch=l["rot"][0], yaw=l["rot"][1]), V(*l["scale"])); lids.append(ld)
    bt.lids = lids
    adds = []
    for a in t["adds"]:
        ad = unreal.RTAddition(); ad.kind = KIND[a["kind"]]; ad.location = V(*a["loc"]); ad.yaw = a["yaw"]; adds.append(ad)
    bt.additions = adds
    bt.paths = [unreal.RTPath(points=[unreal.Vector2D(p[0], p[1]) for p in path]) for path in t["paths"]]
    templates.append(bt)
    print("  template", k, t["purpose"], "doors", len(doors), "lids", len(lids), "adds", len(adds), "paths", len(t["paths"]))
# ---------------------------------------------------------------- game mode
G = "/Game/RandomLevel/Blueprints"; GM = f"{G}/BP_RL_GameMode"
if not eal.does_asset_exist(GM): eal.duplicate_asset("/Game/SFCityLevel/Blueprints/BP_SFC_GameMode", GM)
gm = unreal.load_asset(GM); pawn = unreal.load_asset("/Game/SFCityLevel/Blueprints/BP_SFC_Fem5Character")
unreal.get_default_object(gm.generated_class()).set_editor_property("default_pawn_class", pawn.generated_class())
unreal.BlueprintEditorLibrary.compile_blueprint(gm); eal.save_loaded_asset(gm, only_if_is_dirty=False)
# ---------------------------------------------------------------- level
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if eal.does_asset_exist(MAP):
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
else:
    les.new_level(MAP)
w = ues.get_editor_world(); assert w.get_path_name().startswith(MAP + "."), w.get_path_name()
for a in eas.get_all_level_actors():
    if a.get_class().get_name() in ("WorldSettings", "Brush") or isinstance(a, unreal.WorldSettings): continue
    eas.destroy_actor(a)
def spawn(cls, loc, rot=None, label=None):
    a = eas.spawn_actor_from_class(cls, loc, rot or unreal.Rotator()); a.tags = [TAG]
    if label: a.set_actor_label(label)
    a.set_folder_path("RandomTown/Environment"); return a
sun = spawn(unreal.DirectionalLight, V(0, 0, 8000), unreal.Rotator(roll=0, pitch=-38, yaw=-35), "Sun")
lc = sun.light_component; lc.set_editor_property("intensity", 9.0); lc.set_editor_property("atmosphere_sun_light", True)
lc.set_editor_property("light_source_angle", 1.0)
spawn(unreal.SkyAtmosphere, V(0, 0, 0), label="SkyAtmosphere")
sky = spawn(unreal.SkyLight, V(0, 0, 600), label="SkyLight"); sky.light_component.set_editor_property("real_time_capture", True)
sky.light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
spawn(unreal.VolumetricCloud, V(0, 0, 0), label="Clouds")
fog = spawn(unreal.ExponentialHeightFog, V(0, 0, 200), label="HeightFog")
fc = fog.component; fc.set_editor_property("fog_density", 0.012); fc.set_editor_property("fog_height_falloff", 0.12)
fc.set_editor_property("start_distance", 9000.0)
ppv = spawn(unreal.PostProcessVolume, V(0, 0, 0), label="PostProcess"); ppv.set_editor_property("unbound", True)
far = spawn(unreal.StaticMeshActor, V(0, 0, -240), label="FarGround")      # (terrain never goes below -233: only a small step at the town edge)
far.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Plane")); far.set_actor_scale3d(V(8000, 8000, 1))   # 8 km: land to the horizon
far.static_mesh_component.set_material(0, unreal.load_asset("/Game/RandomLevel/Materials/MI_RT_FarGround"))
H0 = unreal.RTTownGenerator.terrain_height(0.0, 0.0)
ps = spawn(unreal.PlayerStart, V(0, 0, H0 + 100), unreal.Rotator(roll=0, pitch=0, yaw=0), "RT_PlayerStart")
ws = w.get_world_settings(); ws.set_editor_property("default_game_mode", gm.generated_class()); ws.set_editor_property("kill_z", -5000.0)
gen = spawn(unreal.RTTownGenerator, V(0, 0, 0), label="RT_TownGenerator"); gen.set_folder_path("RandomTown")
gen.set_editor_property("templates", templates)
gen.set_editor_property("ground_material", unreal.load_asset("/Game/RandomLevel/Materials/M_RT_Ground"))
for k, v in (("trees", TREES), ("bushes", BUSHES), ("grass", GRASS), ("rocks", ROCKS), ("yard_props", YARD), ("market_props", MARKET), ("tents", TENTS), ("wells", WELLS)):
    gen.set_editor_property(k, v)
gen.set_editor_property("market_stalls", [unreal.EditorAssetLibrary.load_blueprint_class(f"/Game/Hivemind/Medieval_Docks/Blueprints/BP_MarketStand_0{i}") for i in (1, 2, 3)])
for k, n in (("chest_body", "SM_Kit_ChestBody"), ("chest_lid", "SM_Kit_ChestLid"), ("trunk_body", "SM_Kit_TrunkBody"), ("trunk_lid", "SM_Kit_TrunkLid"),
             ("wardrobe_body", "SM_Kit_WardrobeBody"), ("wardrobe_door_l", "SM_Kit_WardrobeDoorL"), ("wardrobe_door_r", "SM_Kit_WardrobeDoorR"), ("washstand", "SM_Kit_Washstand")):
    gen.set_editor_property(k, mesh(n))
print("ground at origin", round(H0, 1), "| templates", len(templates))
if "no_build" not in sys.argv:
    gen.build_start_square()
    cells = gen.get_cell_coords()
    nb = sum(len(gen.get_buildings_in_cell(c)) for c in cells)
    print("start square:", len(cells), "cells,", nb, "buildings,", sum(gen.get_cell(c).get_editor_property("num_instances") for c in cells), "instances")
les.save_current_level()
print("saved", MAP)
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
