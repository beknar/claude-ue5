"""World-aligned (triplanar) materials for the sf-city-level structures: scaled cube walls would stretch ordinary UVs.
M_SFC_WorldAligned (Engine WorldAlignedTexture / WorldAlignedNormal; params BaseColorTex, NormalTex, TileSize, Roughness,
Metallic, Tint) + instances from the Open World Science fiction City textures, and M_SFC_Glow (unlit-looking emissive strips:
Color, Strength) + instances. All in /Game/SFCityLevel/Materials."""
import unreal
eal = unreal.EditorAssetLibrary; mel = unreal.MaterialEditingLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
D = "/Game/SFCityLevel/Materials"; T = "/Game/Mega_City/Textures/"
def fresh(name, cls, fac):
    p = f"{D}/{name}"
    if eal.does_asset_exist(p): eal.delete_asset(p)
    return at.create_asset(name, D, cls, fac)
m = fresh("M_SFC_WorldAligned", unreal.Material, unreal.MaterialFactoryNew())
WAT = unreal.load_asset("/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture")
WAN = unreal.load_asset("/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedNormal")
E = lambda cls, x, y: mel.create_material_expression(m, cls, x, y)
bc = E(unreal.MaterialExpressionTextureObjectParameter, -900, -200); bc.set_editor_property("parameter_name", "BaseColorTex")
bc.set_editor_property("texture", unreal.load_asset(T + "T_metal_plate/T_tiled_metal_Nexus_D"))
nt = E(unreal.MaterialExpressionTextureObjectParameter, -900, 200); nt.set_editor_property("parameter_name", "NormalTex")
nt.set_editor_property("texture", unreal.load_asset(T + "T_metal_plate/T_tiled_metal_Nexus_N")); nt.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
ts = E(unreal.MaterialExpressionScalarParameter, -900, 50); ts.set_editor_property("parameter_name", "TileSize"); ts.set_editor_property("default_value", 300.0)
c1 = E(unreal.MaterialExpressionMaterialFunctionCall, -500, -200); c1.set_material_function(WAT)
c2 = E(unreal.MaterialExpressionMaterialFunctionCall, -500, 200); c2.set_material_function(WAN)
for c in (c1, c2): mel.connect_material_expressions(ts, "", c, "TextureSize")
mel.connect_material_expressions(bc, "", c1, "TextureObject"); mel.connect_material_expressions(nt, "", c2, "TextureObject")
tint = E(unreal.MaterialExpressionVectorParameter, -500, -400); tint.set_editor_property("parameter_name", "Tint"); tint.set_editor_property("default_value", unreal.LinearColor(1, 1, 1, 1))
mul = E(unreal.MaterialExpressionMultiply, -250, -250)
mel.connect_material_expressions(c1, "XYZ Texture", mul, "A"); mel.connect_material_expressions(tint, "", mul, "B")
mel.connect_material_property(mul, "", unreal.MaterialProperty.MP_BASE_COLOR)
mel.connect_material_property(c2, "XYZ Texture", unreal.MaterialProperty.MP_NORMAL)
for nm, dv, y, prop in (("Roughness", 0.5, 50, unreal.MaterialProperty.MP_ROUGHNESS), ("Metallic", 0.4, 150, unreal.MaterialProperty.MP_METALLIC)):
    p = E(unreal.MaterialExpressionScalarParameter, -250, y); p.set_editor_property("parameter_name", nm); p.set_editor_property("default_value", dv)
    mel.connect_material_property(p, "", prop)
mel.recompile_material(m); eal.save_loaded_asset(m)
print("M_SFC_WorldAligned compiles:", mel.get_statistics(m).num_pixel_shader_instructions > 0)
INST = {  # name: (basecolor, normal, tile, roughness, metallic, tint)
    "MI_SFC_WallPanel": ("T_metal_plate/T_tiled_metal_Nexus_D", "T_metal_plate/T_tiled_metal_Nexus_N", 300.0, 0.45, 0.5, (0.85, 0.87, 0.9)),
    "MI_SFC_WallDark": ("T_metal_plate/T_tiled_metal_Nexus_D_02", "T_metal_plate/T_tiled_metal_Nexus_N_02", 300.0, 0.5, 0.6, (0.42, 0.44, 0.5)),
    "MI_SFC_Floor": ("T_floor_01/T_floor_01_basecolor", "T_floor_01/T_floor_01_normal", 220.0, 0.35, 0.2, (0.8, 0.8, 0.82)),
    "MI_SFC_FloorDark": ("T_floor/T_floor_D1", "T_floor/T_floor_N", 250.0, 0.4, 0.3, (0.45, 0.45, 0.5)),
    "MI_SFC_Ceiling": ("T_tiling_metal/T_tiling_metal_D", "T_tiling_metal/T_tiling_metal_N", 260.0, 0.55, 0.5, (0.6, 0.62, 0.66)),
    "MI_SFC_Concrete": ("T_wall_concrete/T_wall_concrete_D", "T_wall_concrete/T_wall_concrete_N", 450.0, 0.85, 0.0, (0.75, 0.75, 0.78)),
    "MI_SFC_Trim": ("T_trim_02/T_trim_02_D", "T_trim_02/T_trim_02_N", 160.0, 0.4, 0.7, (0.55, 0.55, 0.6)),
}
for name, (b, n, tile, rough, metal, tc) in INST.items():
    mi = fresh(name, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew()); mel.set_material_instance_parent(mi, m)
    mel.set_material_instance_texture_parameter_value(mi, "BaseColorTex", unreal.load_asset(T + b))
    mel.set_material_instance_texture_parameter_value(mi, "NormalTex", unreal.load_asset(T + n))
    for k, v in (("TileSize", tile), ("Roughness", rough), ("Metallic", metal)): mel.set_material_instance_scalar_parameter_value(mi, k, v)
    mel.set_material_instance_vector_parameter_value(mi, "Tint", unreal.LinearColor(*tc, 1)); eal.save_loaded_asset(mi)
# glow strips / light panels
g = fresh("M_SFC_Glow", unreal.Material, unreal.MaterialFactoryNew())
col = mel.create_material_expression(g, unreal.MaterialExpressionVectorParameter, -600, 0); col.set_editor_property("parameter_name", "Color")
col.set_editor_property("default_value", unreal.LinearColor(0.2, 0.7, 1.0, 1))
stv = mel.create_material_expression(g, unreal.MaterialExpressionScalarParameter, -600, 200); stv.set_editor_property("parameter_name", "Strength"); stv.set_editor_property("default_value", 8.0)
mu = mel.create_material_expression(g, unreal.MaterialExpressionMultiply, -300, 100)
mel.connect_material_expressions(col, "", mu, "A"); mel.connect_material_expressions(stv, "", mu, "B")
mel.connect_material_property(mu, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
bk = mel.create_material_expression(g, unreal.MaterialExpressionConstant3Vector, -300, -150); bk.set_editor_property("constant", unreal.LinearColor(0.02, 0.02, 0.02, 1))
mel.connect_material_property(bk, "", unreal.MaterialProperty.MP_BASE_COLOR)
mel.recompile_material(g); eal.save_loaded_asset(g); print("M_SFC_Glow compiles:", mel.get_statistics(g).num_pixel_shader_instructions > 0)
for name, c, s in (("MI_SFC_GlowCyan", (0.15, 0.75, 1.0), 10.0), ("MI_SFC_GlowPink", (1.0, 0.15, 0.6), 10.0), ("MI_SFC_GlowWarm", (1.0, 0.75, 0.45), 6.0),
                   ("MI_SFC_GlowWhite", (0.9, 0.95, 1.0), 5.0), ("MI_SFC_GlowRed", (1.0, 0.08, 0.05), 10.0)):
    mi = fresh(name, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew()); mel.set_material_instance_parent(mi, g)
    mel.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(*c, 1)); mel.set_material_instance_scalar_parameter_value(mi, "Strength", s)
    eal.save_loaded_asset(mi)
print("instances:", sorted(p.split("/")[-1].split(".")[0] for p in eal.list_assets(D, recursive=False)))
