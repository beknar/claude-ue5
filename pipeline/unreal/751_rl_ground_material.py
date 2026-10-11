"""random_level ground material /Game/RandomLevel/Materials/M_RT_Ground (for ARTCell's procedural terrain mesh):
world-aligned layers - grass (Sherwood T_Grass) with forest-floor patches (low-frequency noise), packed dirt around
buildings (vertex colour G), cobbled streets (vertex colour R, Docks T_Cobble), small rocks on slopes (normal z) -
plus a macro brightness variation. Sampler types follow each texture's compression / sRGB setting; all samples use\nshared wrap samplers (17 textures > 16 sampler slots)."""
import unreal
MEL = unreal.MaterialEditingLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary
D = "/Game/RandomLevel/Materials"; P = f"{D}/M_RT_Ground"
if eal.does_asset_exist(P): eal.delete_asset(P)
m = at.create_asset("M_RT_Ground", D, unreal.Material, unreal.MaterialFactoryNew())
S = "/Game/Hive_Sherwood/Textures/"; C = "/Game/Hivemind/Medieval_Docks/Textures/Cobbles/"
LAYERS = {   # name: (basecolor, normal, orm, tile cm)
    "grass": (S + "T_Grass_BC", S + "T_Grass_N", S + "T_Grass_ORM", 350.0),
    "forest": (S + "T_ForestFloor_BC", S + "T_ForestFloor_N", S + "T_ForestFloor_ORM", 420.0),
    "dirt": (S + "T_Ground_BC", S + "T_Ground_N", S + "T_Ground_ORM", 300.0),
    "cobble": (C + "T_Cobble_Basecolour", C + "T_Cobble_Normal", C + "T_Cobble_ORMH", 260.0),
    "rocks": (S + "T_SmallRocks_BC", S + "T_SmallRocks_N", S + "T_SmallRocks_ORM", 320.0),
}
X = [0]
def node(cls, x=None, y=0):
    X[0] += 1
    return MEL.create_material_expression(m, cls, -1600 + (x if x is not None else 0), y)
def sampler_type(t):
    comp = t.get_editor_property("compression_settings"); srgb = t.get_editor_property("srgb")
    if t.get_editor_property("virtual_texture_streaming"):                 # (the Docks cobble textures are VT)
        if comp == unreal.TextureCompressionSettings.TC_NORMALMAP: return unreal.MaterialSamplerType.SAMPLERTYPE_VIRTUAL_NORMAL
        return unreal.MaterialSamplerType.SAMPLERTYPE_VIRTUAL_COLOR if srgb else unreal.MaterialSamplerType.SAMPLERTYPE_VIRTUAL_LINEAR_COLOR
    if comp == unreal.TextureCompressionSettings.TC_NORMALMAP: return unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
    if comp in (unreal.TextureCompressionSettings.TC_GRAYSCALE, unreal.TextureCompressionSettings.TC_ALPHA): return unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE if not srgb else unreal.MaterialSamplerType.SAMPLERTYPE_GRAYSCALE
    if comp == unreal.TextureCompressionSettings.TC_MASKS: return unreal.MaterialSamplerType.SAMPLERTYPE_MASKS
    if not srgb: return unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
    return unreal.MaterialSamplerType.SAMPLERTYPE_COLOR
wp = node(unreal.MaterialExpressionWorldPosition, -1400, 0)
xy = node(unreal.MaterialExpressionComponentMask, -1250, 0); xy.set_editor_property("r", True); xy.set_editor_property("g", True); xy.set_editor_property("b", False)
MEL.connect_material_expressions(wp, "", xy, "")
def uv(tile, y):
    d = node(unreal.MaterialExpressionDivide, -1100, y); d.set_editor_property("const_b", tile)
    MEL.connect_material_expressions(xy, "", d, "A"); return d
def tex(path, u, y):
    t = unreal.load_asset(path); s = node(unreal.MaterialExpressionTextureSample, -900, y)
    s.set_editor_property("texture", t); s.set_editor_property("sampler_type", sampler_type(t)); s.set_editor_property("sampler_source", unreal.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS)
    MEL.connect_material_expressions(u, "", s, "UVs"); return s
L = {}
y = -1200
for k, (bc, n, orm, tile) in LAYERS.items():
    u = uv(tile, y); L[k] = (tex(bc, u, y), tex(n, u, y + 200), tex(orm, u, y + 400)); y += 650
def lerp3(a, b, alpha, out_pin_a="", out_pin_b="", y=0, x=-500):
    l = node(unreal.MaterialExpressionLinearInterpolate, x, y)
    MEL.connect_material_expressions(a, out_pin_a, l, "A"); MEL.connect_material_expressions(b, out_pin_b, l, "B"); MEL.connect_material_expressions(alpha, "", l, "Alpha")
    return l
# masks
vc = node(unreal.MaterialExpressionVertexColor, -900, 2200)
road = node(unreal.MaterialExpressionComponentMask, -700, 2200); road.set_editor_property("r", True); road.set_editor_property("g", False); road.set_editor_property("b", False); road.set_editor_property("a", False)
dirt = node(unreal.MaterialExpressionComponentMask, -700, 2300); dirt.set_editor_property("r", False); dirt.set_editor_property("g", True); dirt.set_editor_property("b", False); dirt.set_editor_property("a", False)
MEL.connect_material_expressions(vc, "", road, ""); MEL.connect_material_expressions(vc, "", dirt, "")
# VertexMasks (1): the cell meshes paint roads / dirt in vertex colour; MI_RT_FarGround sets 0 (plain meshes are white)
vm = node(unreal.MaterialExpressionScalarParameter, -900, 2360); vm.set_editor_property("parameter_name", "VertexMasks"); vm.set_editor_property("default_value", 1.0)
masked = []
for k, src in enumerate((road, dirt)):
    mm = node(unreal.MaterialExpressionMultiply, -600, 2200 + k * 100)
    MEL.connect_material_expressions(src, "", mm, "A"); MEL.connect_material_expressions(vm, "", mm, "B"); masked.append(mm)
road, dirt = masked
nz = node(unreal.MaterialExpressionVertexNormalWS, -900, 2450)
nzm = node(unreal.MaterialExpressionComponentMask, -750, 2450); nzm.set_editor_property("r", False); nzm.set_editor_property("g", False); nzm.set_editor_property("b", True)
MEL.connect_material_expressions(nz, "", nzm, "")
slope = node(unreal.MaterialExpressionSmoothStep, -600, 2450); slope.set_editor_property("const_min", 0.93); slope.set_editor_property("const_max", 0.80)
MEL.connect_material_expressions(nzm, "", slope, "Value")
# forest patches: low-frequency macro texture
mac = node(unreal.MaterialExpressionTextureSample, -900, 2650)
mt = unreal.load_asset("/Engine/EngineMaterials/T_Default_MacroVariation"); mac.set_editor_property("texture", mt); mac.set_editor_property("sampler_type", sampler_type(mt)); mac.set_editor_property("sampler_source", unreal.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS)
MEL.connect_material_expressions(uv(9000.0, 2650), "", mac, "UVs")
patch = node(unreal.MaterialExpressionSmoothStep, -650, 2650); patch.set_editor_property("const_min", 0.45); patch.set_editor_property("const_max", 0.65)
MEL.connect_material_expressions(mac, "R", patch, "Value")
mac2 = node(unreal.MaterialExpressionTextureSample, -900, 2850); mac2.set_editor_property("texture", mt); mac2.set_editor_property("sampler_type", sampler_type(mt)); mac2.set_editor_property("sampler_source", unreal.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS)
MEL.connect_material_expressions(uv(2300.0, 2850), "", mac2, "UVs")
bright = node(unreal.MaterialExpressionLinearInterpolate, -650, 2850); bright.set_editor_property("const_a", 0.82); bright.set_editor_property("const_b", 1.12)
MEL.connect_material_expressions(mac2, "G", bright, "Alpha")
outs = {}
for ch, pin in (("bc", ""), ("n", ""), ("orm", "")):
    i = {"bc": 0, "n": 1, "orm": 2}[ch]; yy = {"bc": -300, "n": 300, "orm": 900}[ch]
    a = lerp3(L["grass"][i], L["forest"][i], patch, y=yy, x=-450)
    b = lerp3(a, L["rocks"][i], slope, y=yy + 60, x=-350)
    c = lerp3(b, L["dirt"][i], dirt, y=yy + 120, x=-250)
    d = lerp3(c, L["cobble"][i], road, y=yy + 180, x=-150)
    outs[ch] = d
mul = node(unreal.MaterialExpressionMultiply, -50, -300)
MEL.connect_material_expressions(outs["bc"], "", mul, "A"); MEL.connect_material_expressions(bright, "", mul, "B")
MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_BASE_COLOR)
MEL.connect_material_property(outs["n"], "", unreal.MaterialProperty.MP_NORMAL)
rg = node(unreal.MaterialExpressionComponentMask, -50, 900); rg.set_editor_property("r", False); rg.set_editor_property("g", True); rg.set_editor_property("b", False)
ao = node(unreal.MaterialExpressionComponentMask, -50, 1000); ao.set_editor_property("r", True); ao.set_editor_property("g", False); ao.set_editor_property("b", False)
MEL.connect_material_expressions(outs["orm"], "", rg, ""); MEL.connect_material_expressions(outs["orm"], "", ao, "")
MEL.connect_material_property(rg, "", unreal.MaterialProperty.MP_ROUGHNESS)
MEL.connect_material_property(ao, "", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
MEL.recompile_material(m); eal.save_loaded_asset(m)
FP = f"{D}/MI_RT_FarGround"
if not eal.does_asset_exist(FP):
    f_ = unreal.MaterialInstanceConstantFactoryNew(); at.create_asset("MI_RT_FarGround", D, unreal.MaterialInstanceConstant, f_)
mi = unreal.load_asset(FP); MEL.set_material_instance_parent(mi, m); MEL.set_material_instance_scalar_parameter_value(mi, "VertexMasks", 0.0)
eal.save_loaded_asset(mi, only_if_is_dirty=False)
st = MEL.get_statistics(m)
print("M_RT_Ground compiled: pixel instructions", st.num_pixel_shader_instructions, "| samplers", st.num_samplers)
