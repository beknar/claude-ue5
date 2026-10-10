"""Studio assets: cyclorama + plinth meshes (Nanite), concrete with Nanite tessellation
displacement, black lacquer plinth (Substrate vertical layering + specular profile)."""
import os, sys, importlib, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mat_lib as L
importlib.reload(L)

SRC = r"E:\code\claude-ue5\claude_ue5\SourceArt\studio"
D = "/Game/Fig4/Studio"

# meshes
tasks = []
for f in ("SM_Cyclorama.glb", "SM_Plinth.glb"):
    t = unreal.AssetImportTask(); t.filename = os.path.join(SRC, f); t.destination_path = D + "/Meshes"
    t.automated = True; t.replace_existing = True; t.save = True; tasks.append(t)
L.at.import_asset_tasks(tasks)
meshes = {}
for t in tasks:
    for p in t.imported_object_paths:
        if isinstance(unreal.load_asset(p), unreal.StaticMesh):
            meshes[os.path.basename(t.filename).split(".")[0]] = p
print("meshes", meshes)

# textures
T = {}
for name, kind in (("T_Concrete_BC", "color"), ("T_Concrete_R", "linear"), ("T_Concrete_N", "normal"),
                   ("T_Concrete_H", "height16"), ("T_SP_Leather", "color"), ("T_SP_Patent", "color")):
    T[name] = L.import_texture(os.path.join(SRC, "tex", name + ".png"), D + "/Textures", kind)

# Substrate specular profiles (shared with the outfit)
L.specular_profile(D + "/Profiles/SP_Leather", T["T_SP_Leather"])
sp_patent = L.specular_profile(D + "/Profiles/SP_Patent", T["T_SP_Patent"])

# --- concrete cyclorama: tessellated + displaced (legacy attributes -> auto Substrate) ---
m = L.new_material(D + "/Materials/M_Concrete_Cyc")
m.set_editor_property("use_material_attributes", True)
m.set_editor_property("enable_tessellation", True)
ds = m.get_editor_property("displacement_scaling"); ds.magnitude = 0.8; ds.center = 0.5
m.set_editor_property("displacement_scaling", ds)
uv = L.expr(m, unreal.MaterialExpressionTextureCoordinate, -1400, 0, u_tiling=1.0, v_tiling=1.0)
bc = L.tex_sample(m, T["T_Concrete_BC"], -1100, -300, uv=uv, param="BaseColorTex")
tint = L.vector(m, "Tint", (0.62, 0.62, 0.64), -1100, -500)
bcm = L.mul(m, bc, tint, -800, -350, "RGB", "")
r = L.tex_sample(m, T["T_Concrete_R"], -1100, -50, uv=uv, sampler=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
n = L.tex_sample(m, T["T_Concrete_N"], -1100, 200, uv=uv, sampler=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
h = L.tex_sample(m, T["T_Concrete_H"], -1100, 450, uv=uv, sampler=unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE)
mma = L.expr(m, unreal.MaterialExpressionMakeMaterialAttributes, -400, 0)
L.link(bcm, "", mma, "BaseColor"); L.link(r, "R", mma, "Roughness"); L.link(n, "RGB", mma, "Normal")
L.link(h, "R", mma, "Displacement")
spec = L.expr(m, unreal.MaterialExpressionConstant, -700, 100, r=0.5); L.link(spec, "", mma, "Specular")
L.mel.connect_material_property(mma, "", unreal.MaterialProperty.MP_MATERIAL_ATTRIBUTES)
L.finish(m)

# --- black lacquer plinth: clear coat (Substrate slab) vertically layered over black base -----
p = L.new_material(D + "/Materials/M_Lacquer_Plinth")
base_alb = L.const3(p, (0.012, 0.012, 0.014), -900, -200)
base_r = L.scalar(p, "BaseRoughness", 0.35, -900, -50)
base = L.slab(p, -500, -200, Diffuse_Albedo=base_alb, Roughness=base_r)
coat_r = L.scalar(p, "CoatRoughness", 0.03, -900, 150)
coat_f0 = L.const3(p, (0.04, 0.04, 0.04), -900, 250)
coat_alb = L.const3(p, (0, 0, 0), -900, 350)
coat = L.slab(p, -500, 200, Diffuse_Albedo=coat_alb, F0=coat_f0, Roughness=coat_r)
coat.set_editor_property("specular_profile", sp_patent)
thick = L.scalar(p, "CoatThickness", 0.02, -900, 450)
vl = L.expr(p, unreal.MaterialExpressionSubstrateVerticalLayering, -200, 0)
L.link(coat, "", vl, "Top"); L.link(base, "", vl, "Bottom"); L.link(thick, "", vl, "Top Thickness")
L.mel.connect_material_property(vl, "", unreal.MaterialProperty.MP_FRONT_MATERIAL)
L.finish(p)

# assign + Nanite
cyc = L.enable_nanite(meshes["SM_Cyclorama"]); cyc.set_material(0, m); L.eal.save_loaded_asset(cyc)
pl = L.enable_nanite(meshes["SM_Plinth"]); pl.set_material(0, p); L.eal.save_loaded_asset(pl)
print("STUDIO assets done")
