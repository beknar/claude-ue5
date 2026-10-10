"""Substrate materials for fig4's outfit + Nanite on the skinned outfit mesh."""
import os, sys, importlib, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mat_lib as L
importlib.reload(L)
TEX = r"E:\code\claude-ue5\claude_ue5\SourceArt\fig4\tex"
D = "/Game/Fig4/Outfit"
grainN = L.import_texture(os.path.join(TEX, "T_LeatherGrain_N.png"), D + "/Textures", "normal")
grainR = L.import_texture(os.path.join(TEX, "T_LeatherGrain_R.png"), D + "/Textures", "linear")
lace = L.import_texture(os.path.join(TEX, "T_Lace_Mask.png"), D + "/Textures", "linear")
sp_leather = unreal.load_asset("/Game/Fig4/Studio/Profiles/SP_Leather")
sp_patent = unreal.load_asset("/Game/Fig4/Studio/Profiles/SP_Patent")
MS = unreal.MaterialSamplerType

def skinned(m):
    m.set_editor_property("used_with_skeletal_mesh", True)
    m.set_editor_property("used_with_nanite", True)

def leather(path, albedo, tiling, rough_scale, haze_w, profile, haze_r=0.32):
    m = L.new_material(path); skinned(m)
    uv = L.expr(m, unreal.MaterialExpressionTextureCoordinate, -1500, 0, u_tiling=tiling, v_tiling=tiling)
    n = L.tex_sample(m, grainN, -1200, 200, uv=uv, sampler=MS.SAMPLERTYPE_NORMAL)
    r = L.tex_sample(m, grainR, -1200, -100, uv=uv, sampler=MS.SAMPLERTYPE_MASKS)
    rs = L.scalar(m, "RoughnessScale", rough_scale, -1200, -250)
    rr = L.mul(m, r, rs, -900, -150, "R", "")
    alb = L.vector(m, "Albedo", albedo, -900, -400)
    f0 = L.const3(m, (0.045, 0.045, 0.045), -900, -300)
    haze = L.scalar(m, "HazeRoughness", haze_r, -900, 350); hw = L.scalar(m, "HazeWeight", haze_w, -900, 450)
    s = L.slab(m, -500, 0, Diffuse_Albedo=alb, F0=f0, Roughness=rr, Normal=(n, "RGB"),
               Second_Roughness=haze, Second_Roughness_Weight=hw)
    s.set_editor_property("specular_profile", profile)
    L.mel.connect_material_property(s, "", unreal.MaterialProperty.MP_FRONT_MATERIAL)
    L.finish(m); return m

m_dress = leather(D + "/Materials/M_Fig4_Dress", (0.16, 0.010, 0.016), 14.0, 1.3, 0.15, sp_leather, 0.32)
m_choker = leather(D + "/Materials/M_Fig4_Choker", (0.012, 0.011, 0.012), 30.0, 0.9, 0.12, sp_leather, 0.30)

# patent heels: clear coat vertically layered over a black lacquered base
m = L.new_material(D + "/Materials/M_Fig4_Shoes"); skinned(m)
base = L.slab(m, -500, -200, Diffuse_Albedo=L.const3(m, (0.008, 0.008, 0.009), -900, -250), Roughness=L.scalar(m, "BaseRoughness", 0.22, -900, -150))
coat = L.slab(m, -500, 200, Diffuse_Albedo=L.const3(m, (0, 0, 0), -900, 150), F0=L.const3(m, (0.045, 0.045, 0.045), -900, 250),
              Roughness=L.scalar(m, "CoatRoughness", 0.025, -900, 350))
coat.set_editor_property("specular_profile", sp_patent)
vl = L.expr(m, unreal.MaterialExpressionSubstrateVerticalLayering, -200, 0)
L.link(coat, "", vl, "Top"); L.link(base, "", vl, "Bottom"); L.link(L.scalar(m, "CoatThickness", 0.015, -900, 450), "", vl, "Top Thickness")
L.mel.connect_material_property(vl, "", unreal.MaterialProperty.MP_FRONT_MATERIAL)
L.finish(m); m_shoes = m

# stockings: sheer white nylon (skin shows through at facing angles), fabric fuzz sheen, lace band
m = L.new_material(D + "/Materials/M_Fig4_Stockings"); skinned(m)
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
m.set_editor_property("two_sided", True)
uv2 = L.expr(m, unreal.MaterialExpressionTextureCoordinate, -1700, 600, coordinate_index=1, u_tiling=1.0, v_tiling=1.0)
lace_scale = L.expr(m, unreal.MaterialExpressionConstant2Vector, -1700, 750, r=9.0, g=9.0 / 0.075)
lace_uv = L.mul(m, uv2, lace_scale, -1500, 650)        # 9 repeats round the leg, band 7.5 cm tall
lace_uv2 = L.expr(m, unreal.MaterialExpressionComponentMask, -1350, 650, r=True, g=True, b=False, a=False)
L.link(lace_uv, "", lace_uv2, "")
lm = L.tex_sample(m, lace, -1150, 650, uv=lace_uv2, sampler=MS.SAMPLERTYPE_MASKS)
vcomp = L.expr(m, unreal.MaterialExpressionComponentMask, -1350, 900, r=False, g=True, b=False, a=False)
L.link(uv2, "", vcomp, "")
# opacity = saturate(lace + (v - 0.075) * 1000): lace inside the 7.5 cm band, solid below it
sub = L.expr(m, unreal.MaterialExpressionSubtract, -1100, 900, const_b=0.075)
L.link(vcomp, "", sub, "A")
k = L.expr(m, unreal.MaterialExpressionMultiply, -950, 900, const_b=1000.0); L.link(sub, "", k, "A")
add = L.expr(m, unreal.MaterialExpressionAdd, -800, 800); L.link(lm, "R", add, "A"); L.link(k, "", add, "B")
band = L.expr(m, unreal.MaterialExpressionSaturate, -650, 800); L.link(add, "", band, "")
L.mel.connect_material_property(band, "", unreal.MaterialProperty.MP_OPACITY_MASK)
fres = L.expr(m, unreal.MaterialExpressionFresnel, -1100, -200, exponent=1.6, base_reflect_fraction=0.45)
alb = L.expr(m, unreal.MaterialExpressionLinearInterpolate, -800, -250)
L.link(L.const3(m, (0.72, 0.52, 0.45), -1100, -400), "", alb, "A")      # skin seen through the knit
L.link(L.const3(m, (0.80, 0.80, 0.78), -1100, -320), "", alb, "B")      # white nylon
L.link(fres, "", alb, "Alpha")
s = L.slab(m, -450, 0, Diffuse_Albedo=alb, F0=L.const3(m, (0.03, 0.03, 0.03), -800, -50),
           Roughness=L.scalar(m, "Roughness", 0.62, -800, 50),
           Fuzz_Amount=L.scalar(m, "FuzzAmount", 0.75, -800, 150),
           Fuzz_Color=L.const3(m, (0.92, 0.92, 0.94), -800, 250),
           Fuzz_Roughness=L.scalar(m, "FuzzRoughness", 0.45, -800, 350))
L.mel.connect_material_property(s, "", unreal.MaterialProperty.MP_FRONT_MATERIAL)
L.finish(m); m_stock = m

# assign by slot name + Nanite on the skinned outfit
sk = unreal.load_asset("/Game/Fig4/Outfit/fig4_outfit_skinned")
mats = sk.get_editor_property("materials")
want = {"dress": m_dress, "stocking": m_stock, "shoe": m_shoes, "choker": m_choker}
new = []
for sm in mats:
    nm = str(sm.get_editor_property("material_slot_name")).lower()
    for k, v in want.items():
        if k in nm:
            sm.set_editor_property("material_interface", v)
    new.append(sm); print("slot", nm, "->", sm.get_editor_property("material_interface").get_name() if sm.get_editor_property("material_interface") else None)
sk.set_editor_property("materials", new)
try:
    ns = sk.get_editor_property("nanite_settings"); ns.set_editor_property("enabled", True)
    sk.set_editor_property("nanite_settings", ns); print("Nanite enabled on outfit")
except Exception as e:
    print("nanite:", e)
L.eal.save_loaded_asset(sk)
