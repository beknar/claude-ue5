"""M_Meshy_Substrate: one Substrate slab driven by the baked Meshy textures plus derived masks
(R skin -> subsurface MFP, G cloth -> fuzz, B dark hair/nylon -> second specular lobe). Nanite on the skeletal mesh."""
import os, sys, importlib, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mat_lib as L
importlib.reload(L)
mel = L.mel
SRC = r"E:\code\claude-ue5\claude_ue5\SourceArt\meshy_biped"
D = "/Game/Meshy"
mask_tex = L.import_texture(os.path.join(SRC, "T_Meshy_Masks.png"), D + "/Textures", "linear")
bc_t = unreal.load_asset(D + "/Textures/texture_0")
n_t = unreal.load_asset(D + "/Textures/texture_0_normal")
mr_t = unreal.load_asset(D + "/Textures/texture_0_metallic-texture_0_roughness")
path = D + "/Materials/M_Meshy_Substrate"
if L.eal.does_asset_exist(path):
    m = unreal.load_asset(path); mel.delete_all_material_expressions(m)
else:
    m = L.new_material(path)
m.set_editor_property("two_sided", True)
S = unreal.MaterialSamplerType
uv = L.expr(m, unreal.MaterialExpressionTextureCoordinate, -2200, 0)
bc = L.tex_sample(m, bc_t, -1900, -400, uv=uv)
mr = L.tex_sample(m, mr_t, -1900, -100, uv=uv, sampler=S.SAMPLERTYPE_MASKS)
nm = L.tex_sample(m, n_t, -1900, 200, uv=uv, sampler=S.SAMPLERTYPE_NORMAL)
mk = L.tex_sample(m, mask_tex, -1900, 500, uv=uv, sampler=S.SAMPLERTYPE_MASKS)
def op(cls, a, b, x, y, ao="", bo=""):
    e = L.expr(m, cls, x, y)
    if isinstance(a, (int, float)): e.set_editor_property("const_a", a)
    else: L.link(a, ao, e, "A")
    if isinstance(b, (int, float)): e.set_editor_property("const_b", b)
    else: L.link(b, bo, e, "B")
    return e
def lerp(a, b, t, x, y, ao="", bo="", to=""):
    e = L.expr(m, unreal.MaterialExpressionLinearInterpolate, x, y)
    L.link(a, ao, e, "A"); L.link(b, bo, e, "B"); L.link(t, to, e, "Alpha"); return e
tint = L.vector(m, "AlbedoTint", (1.0, 1.0, 1.0), -1600, -550)
alb = op(unreal.MaterialExpressionMultiply, bc, tint, -1450, -450, "RGB", "")
metal = mr                                                       # B channel
diffuse = op(unreal.MaterialExpressionMultiply, alb, op(unreal.MaterialExpressionSubtract, 1.0, mr, -1450, -250, "", "B"), -1250, -400)
f0 = lerp(L.const3(m, (0.04, 0.04, 0.04), -1450, -150), alb, mr, -1250, -200, "", "", "B")
rough = op(unreal.MaterialExpressionAdd, op(unreal.MaterialExpressionMultiply, mr, L.scalar(m, "RoughnessScale", 0.95, -1600, -50), -1450, -50, "G", ""), L.scalar(m, "RoughnessBias", 0.08, -1600, 50), -1250, -50)
rough = L.expr(m, unreal.MaterialExpressionSaturate, -1100, -50); L.link(op(unreal.MaterialExpressionAdd, op(unreal.MaterialExpressionMultiply, mr, 0.95, -1450, -50, "G", ""), 0.08, -1300, -50), "", rough, "")
# subsurface: skin mean free path (cm), masked
mfp = op(unreal.MaterialExpressionMultiply, L.vector(m, "SkinMFP", (0.42, 0.16, 0.08), -1600, 650), mk, -1250, 600, "", "R")
# cloth fuzz
fuzz_amt = op(unreal.MaterialExpressionMultiply, mk, L.scalar(m, "FuzzAmount", 0.45, -1600, 800), -1250, 780, "G", "")
fuzz_col = L.expr(m, unreal.MaterialExpressionSaturate, -1100, 880); L.link(op(unreal.MaterialExpressionMultiply, alb, 1.25, -1250, 880), "", fuzz_col, "")
# sheen lobe on hair / nylon
sec_w = op(unreal.MaterialExpressionMultiply, mk, L.scalar(m, "SheenWeight", 0.35, -1600, 1000), -1250, 1000, "B", "")
s = L.slab(m, -700, 0, Diffuse_Albedo=diffuse, F0=f0, Roughness=rough, Normal=(nm, "RGB"),
           SSS_MFP=mfp, Fuzz_Amount=fuzz_amt, Fuzz_Color=fuzz_col, Fuzz_Roughness=L.scalar(m, "FuzzRoughness", 0.5, -1100, 980),
           Second_Roughness=L.scalar(m, "SheenRoughness", 0.16, -1100, 1080), Second_Roughness_Weight=sec_w)
mel.connect_material_property(s, "", unreal.MaterialProperty.MP_FRONT_MATERIAL)
for flag in ("used_with_skeletal_mesh", "used_with_nanite"):
    try: m.set_editor_property(flag, True)
    except Exception as e: print(flag, e)
L.finish(m)
sk = unreal.load_asset(D + "/Character/SK_Meshy_Biped")
mats = sk.get_editor_property("materials")
for i in range(len(mats)):
    mats[i].set_editor_property("material_interface", m)
sk.set_editor_property("materials", mats)
try:
    ns = sk.get_editor_property("nanite_settings"); ns.set_editor_property("enabled", True)
    sk.set_editor_property("nanite_settings", ns); print("Nanite on skeletal mesh")
except Exception as e: print("nanite", e)
L.eal.save_loaded_asset(sk)
print("material slots", len(mats), "->", m.get_path_name())
