"""Furniture for castle_level interiors:
- Kit (SourceArt/castle_furniture/*.fbx, procedural): -> /Game/Castle/Furniture/Kit. Slot-name materials: pack MIs for Wood/Planks/
  Stone/Bark/Plaster, M_KitColor instances for the rest (colour, roughness, metallic, emissive, straw-style noise).
- Megascans (Saloon_Interior pack, period-neutral pieces): -> /Game/Castle/Furniture/Scans with M_Scan instances (4K jpgs capped at 2K).
Collision: complex-as-simple on furniture, none on small table items / flames."""
import os, sys, json, glob, importlib, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mat_lib as L
importlib.reload(L)
eal = unreal.EditorAssetLibrary; mel = unreal.MaterialEditingLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
KIT = r"E:\code\claude-ue5\claude_ue5\SourceArt\castle_furniture"
SCAN = r"I:\game assets\epicgames media packs\VaultCache\FabLibrary\Saloon_Interior-57991a62\fbx\high\saloon_interior_high_extracted"
D = "/Game/Castle/Furniture"; MP = "/Game/Medieval_Fantasy_Village/Materials"
# ---------- materials
mc = L.new_material(f"{D}/Materials/M_KitColor")
col = L.vector(mc, "Color", (0.5, 0.5, 0.5), -900, -200)
noise = L.expr(mc, unreal.MaterialExpressionNoise, -1100, 100, scale=0.08, levels=3, output_min=0.0, output_max=1.0)
na = L.scalar(mc, "NoiseAmount", 0.0, -1100, 300)
mix = L.expr(mc, unreal.MaterialExpressionLinearInterpolate, -700, 100, const_a=1.0); L.link(noise, "", mix, "B"); L.link(na, "", mix, "Alpha")
# noise in [0,1] -> brightness factor 0.55..1.15 where NoiseAmount = 1
nb = L.expr(mc, unreal.MaterialExpressionMultiply, -550, 100); L.link(mix, "", nb, "A"); nb.set_editor_property("const_b", 1.0)
bc = L.expr(mc, unreal.MaterialExpressionMultiply, -400, -100); L.link(col, "", bc, "A"); L.link(nb, "", bc, "B")
mel.connect_material_property(bc, "", unreal.MaterialProperty.MP_BASE_COLOR)
mel.connect_material_property(L.scalar(mc, "Roughness", 0.7, -400, 200), "", unreal.MaterialProperty.MP_ROUGHNESS)
mel.connect_material_property(L.scalar(mc, "Metallic", 0.0, -400, 300), "", unreal.MaterialProperty.MP_METALLIC)
em = L.expr(mc, unreal.MaterialExpressionMultiply, -400, 420); L.link(bc, "", em, "A"); L.link(L.scalar(mc, "Emissive", 0.0, -600, 480), "", em, "B")
mel.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
L.finish(mc)
def mi(name, c, rough=0.7, metal=0.0, emis=0.0, noise_amt=0.0):
    p = f"{D}/Materials/MI_{name}"
    if eal.does_asset_exist(p): eal.delete_asset(p)
    m = at.create_asset(f"MI_{name}", f"{D}/Materials", unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(m, mc)
    mel.set_material_instance_vector_parameter_value(m, "Color", unreal.LinearColor(*c, 1.0))
    for k, v in (("Roughness", rough), ("Metallic", metal), ("Emissive", emis), ("NoiseAmount", noise_amt)): mel.set_material_instance_scalar_parameter_value(m, k, v)
    eal.save_loaded_asset(m); return m
MAT = {"Wood": unreal.load_asset(f"{MP}/MI_wood"), "Planks": unreal.load_asset(f"{MP}/Props/MI_porch"), "Stone": unreal.load_asset(f"{MP}/Props/MI_rock_01"),
       "Bark": unreal.load_asset(f"{MP}/MI_tree_bark"), "Plaster": unreal.load_asset(f"{MP}/Props/MI_side_wall"),
       "Iron": mi("Iron", (0.06, 0.06, 0.065), 0.45, 0.9), "Straw": mi("Straw", (0.42, 0.31, 0.13), 0.95, 0, 0, 1.0),
       "Ember": mi("Ember", (1.0, 0.28, 0.04), 0.9, 0, 1.5, 1.0), "Flame": mi("Flame", (1.0, 0.55, 0.12), 1.0, 0, 1.2),      # tuned: brighter bloomed into streaks indoors
       "Linen": mi("Linen", (0.78, 0.74, 0.64), 0.9), "WoolRed": mi("WoolRed", (0.38, 0.05, 0.04), 0.95, 0, 0, 0.4),
       "WoolGreen": mi("WoolGreen", (0.1, 0.22, 0.08), 0.95, 0, 0, 0.4), "WoolBlue": mi("WoolBlue", (0.07, 0.12, 0.3), 0.95, 0, 0, 0.4),
       "WoolBrown": mi("WoolBrown", (0.25, 0.15, 0.08), 0.95, 0, 0, 0.4), "Fur": mi("Fur", (0.2, 0.13, 0.08), 1.0, 0, 0, 1.0),
       "Bread": mi("Bread", (0.42, 0.22, 0.08), 0.75, 0, 0, 0.5), "Cheese": mi("Cheese", (0.8, 0.6, 0.22), 0.6), "Apple": mi("Apple", (0.45, 0.04, 0.03), 0.35),
       "Clay": mi("Clay", (0.45, 0.22, 0.12), 0.7, 0, 0, 0.3), "Wax": mi("Wax", (0.85, 0.8, 0.66), 0.5), "Stew": mi("Stew", (0.18, 0.08, 0.03), 0.2),
       "Dough": mi("Dough", (0.86, 0.8, 0.66), 0.8), "Rope": mi("Rope", (0.33, 0.27, 0.16), 0.95, 0, 0, 0.5)}
SMALL = ("Tankard", "Goblet", "Bowl", "Bread", "Cheese", "AppleBasket", "Candles", "CandleStick", "FryingPan", "Rug", "FurRug", "Chandelier")
def static_import(fbx, dest, name):
    o = unreal.FbxImportUI(); o.set_editor_property("import_mesh", True); o.set_editor_property("import_as_skeletal", False)
    o.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    o.set_editor_property("import_materials", False); o.set_editor_property("import_textures", False)
    sd = o.get_editor_property("static_mesh_import_data"); sd.set_editor_property("combine_meshes", True)
    sd.set_editor_property("auto_generate_collision", False); sd.set_editor_property("generate_lightmap_u_vs", False)
    t = unreal.AssetImportTask(); t.filename = fbx; t.destination_path = dest; t.destination_name = name
    t.automated = True; t.replace_existing = True; t.save = True; t.options = o
    at.import_asset_tasks([t]); return unreal.load_asset(f"{dest}/{name}")
def collision(sm, on):
    bs = sm.get_editor_property("body_setup")
    if bs:
        bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE if on else unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
        sm.set_editor_property("body_setup", bs)
kit = json.load(open(os.path.join(KIT, "kit.json"))); kit.pop("_hinges", None)
for name in sorted(kit):
    sm = static_import(os.path.join(KIT, name + ".fbx"), f"{D}/Kit", name)
    for i, s in enumerate(sm.static_materials):
        slot = str(s.material_slot_name).split(".")[0]
        if slot in MAT: sm.set_material(i, MAT[slot])
        else: print("  no material for", name, slot)
    collision(sm, not any(k in name for k in SMALL))
    eal.save_loaded_asset(sm, only_if_is_dirty=False)
print("kit imported", len(kit))
KIT_ONLY = "kitonly" in sys.argv[1:]
# ---------- Megascans
ms = L.new_material(f"{D}/Materials/M_Scan")
tb = unreal.load_asset("/Engine/EngineResources/DefaultTexture")
S = unreal.MaterialSamplerType
bcs = L.tex_sample(ms, tb, -800, -300, param="BaseColor")
nrm = L.tex_sample(ms, unreal.load_asset("/Engine/EngineMaterials/DefaultNormal"), -800, 0, sampler=S.SAMPLERTYPE_NORMAL, param="Normal")
rgh = L.tex_sample(ms, tb, -800, 300, sampler=S.SAMPLERTYPE_LINEAR_COLOR, param="Roughness")
mel.connect_material_property(bcs, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
mel.connect_material_property(nrm, "RGB", unreal.MaterialProperty.MP_NORMAL)
mel.connect_material_property(rgh, "R", unreal.MaterialProperty.MP_ROUGHNESS)
L.finish(ms)
SCANS = {"tl0vafqfa": "BarrelA", "tl3ifacfa": "BarrelB", "tltvai3fa": "BarrelC", "tmgmfeefa": "BarrelSmall", "tmgpcg2fa": "BarrelD", "tmrveaeda": "BarrelE",
         "uc2ichvqx": "BarrelF", "udlmcdhqx": "BarrelSmallB", "udmmfbpqx": "KegStand", "uc1kebzfa": "RoundTable", "ukphdffaw": "SquareTable",
         "ukikajmaw": "ChairA", "ukipagtbw": "ChairWindsor", "uknjbb2bw": "ChairB", "uknkaffaw": "ChairC", "udehcidiw": "Antlers", "udzrbfmfa": "Horseshoe",
         "ufzjadyga": "Saddle", "ugciag2ga": "WagonWheel", "ugygfhdva": "Jug", "ulejaaxga": "Trunk", "vfyqcj2ga": "Bucket", "vlwmahl": "WallShelf",
         "xixlcj1mw": "Plate", "wldocam": "Book", "ufzueazdw": "BarCounter", "vkbhcbg": "LongBeam", "ufbpadjdw": "Balustrade"}
def tex(path, kind):
    tx = L.import_texture(path, f"{D}/Scans/Textures", kind)
    tx.set_editor_property("max_texture_size", 2048); eal.save_loaded_asset(tx); return tx
for aid, nm in ({} if KIT_ONLY else SCANS).items():
    folder = os.path.join(SCAN, aid)
    sm = static_import(os.path.join(folder, aid + ".fbx"), f"{D}/Scans", f"SM_Scan_{nm}")
    jp = {k: next(iter(glob.glob(os.path.join(folder, f"*_{k}.jpg"))), None) for k in ("BaseColor", "Normal", "Roughness")}
    p = f"{D}/Scans/MI_Scan_{nm}"
    if eal.does_asset_exist(p): eal.delete_asset(p)
    m = at.create_asset(f"MI_Scan_{nm}", f"{D}/Scans", unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(m, ms)
    for k, kind in (("BaseColor", "color"), ("Normal", "normal"), ("Roughness", "linear")):
        if jp[k]: mel.set_material_instance_texture_parameter_value(m, k, tex(jp[k], kind))
    eal.save_loaded_asset(m)
    for i in range(len(sm.static_materials)): sm.set_material(i, m)
    collision(sm, nm not in ("Plate", "Book", "Horseshoe", "Jug", "Antlers"))
    eal.save_loaded_asset(sm, only_if_is_dirty=False)
    b = sm.get_bounding_box(); e = b.max - b.min
    print(f"scan {nm}: {e.x:.0f}x{e.y:.0f}x{e.z:.0f} min z {b.min.z:.0f}")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
