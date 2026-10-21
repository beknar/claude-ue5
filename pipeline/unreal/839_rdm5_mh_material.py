"""random_dungeonmagic_level5, the Summoner's MetaHuman face, her side: M_JRPG_Summoner_MH, her own material (base colour,
metal-rough, normal: M_JRPG_Summoner's textures) with her own face taken away where the MetaHuman's head is. The mask
(summoner_mh_prep.py's T_Summoner_MH_Mask, her texture's UV space): red, her face, ears and neck skin and the face's small
pieces (eyes, lashes, brows): cut out (masked blend); green, the hair painted on her skull and her collar: pushed out along
the normal by PushCm (world position offset), so that they lie over the MetaHuman's scalp and neck instead of in them.
The generator gives it to her body when a face mesh is set (FaceMeshMaterial); SK_JRPG_Summoner keeps its own material.
Args: <prep_dir> (where summoner_mh_prep.py wrote T_Summoner_MH_Mask.png)"""
import os, sys, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, mat_lib as L
importlib.reload(L)
mel, eal = L.mel, L.eal
PREP = sys.argv[1]
CH = "Summoner"
mask = L.import_texture(os.path.join(PREP, "T_Summoner_MH_Mask.png"), "/Game/JRPG/Textures/Face", "linear")
mask.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)   # (a masks texture: the sampler type must match it, or the material does not compile)
mask.set_editor_property("srgb", False)
# (bilinear, with mip levels: the mask itself gives a hidden face's every texel to it. Nearest-texel sampling made the
#  collar's edge a staircase, and no mip levels with never-stream made the masked material cut her whole body away)
mask.set_editor_property("filter", unreal.TextureFilter.TF_DEFAULT)
mask.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
mask.set_editor_property("never_stream", False)
eal.save_loaded_asset(mask)
T = {r: unreal.load_asset(f"/Game/JRPG/Textures/T_{CH}_{r}") for r in ("Color", "Normal", "MetalRough")}
path = f"/Game/JRPG/Materials/M_JRPG_{CH}_MH"
m = L.new_material(path)
m.set_editor_property("use_material_attributes", True); m.set_editor_property("two_sided", True)
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED); m.set_editor_property("opacity_mask_clip_value", 0.5)
S = unreal.MaterialSamplerType
mma = L.expr(m, unreal.MaterialExpressionMakeMaterialAttributes, 300, 0)
col = L.tex_sample(m, T["Color"], -700, -400)
tint = L.vector(m, "AlbedoTint", (1.0, 1.0, 1.0), -700, -650)
alb = L.mul(m, col, tint, -300, -400, a_out="RGB"); L.link(alb, "", mma, "BaseColor")
mr = L.tex_sample(m, T["MetalRough"], -700, -100, sampler=S.SAMPLERTYPE_MASKS); L.link(mr, "B", mma, "Metallic"); L.link(mr, "G", mma, "Roughness")
nm = L.tex_sample(m, T["Normal"], -700, 150, sampler=S.SAMPLERTYPE_NORMAL); L.link(nm, "RGB", mma, "Normal")
L.link(L.scalar(m, "Specular", 0.4, -300, 250), "", mma, "Specular")
mk = L.tex_sample(m, mask, -700, 450, sampler=S.SAMPLERTYPE_MASKS)
inv = L.expr(m, unreal.MaterialExpressionOneMinus, -350, 450); L.link(mk, "R", inv, "")
L.link(inv, "", mma, "OpacityMask")
push = L.scalar(m, "PushCm", 0.6, -700, 700)
nrm = L.expr(m, unreal.MaterialExpressionVertexNormalWS, -700, 800)
g = L.mul(m, mk, push, -350, 650, a_out="G")
wpo = L.mul(m, nrm, g, -150, 750)
L.link(wpo, "", mma, "WorldPositionOffset")
mel.connect_material_property(mma, "", unreal.MaterialProperty.MP_MATERIAL_ATTRIBUTES)
m.set_editor_property("used_with_skeletal_mesh", True)
m.set_editor_property("used_with_morph_targets", True)      # (her mesh keeps the old face's shapes: without the flag the game drew her with the default material)
unreal.log("RDM5MH compiling the body material (the 'Failed to compile' lines above this one are its half-built states)")
L.finish(m)
st = mel.get_statistics(m)
print("RDM5MH material", path, "| pixel instructions", st.num_pixel_shader_instructions, "| mask", mask.get_path_name())
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
