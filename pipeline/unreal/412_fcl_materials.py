"""World-aligned (triplanar) lining materials for fantasy_castle_level interiors: scaled kit panels would stretch ordinary UVs.
M_FCL_WorldAligned (Engine WorldAlignedTexture / WorldAlignedNormal functions; params BaseColorTex, NormalTex, TileSize, Roughness, Tint)
and instances in /Game/FantasyCastleLevel/Materials."""
import unreal
eal = unreal.EditorAssetLibrary; mel = unreal.MaterialEditingLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
D = "/Game/FantasyCastleLevel/Materials"; MP = f"{D}/M_FCL_WorldAligned"
if eal.does_asset_exist(MP): eal.delete_asset(MP)
m = at.create_asset("M_FCL_WorldAligned", D, unreal.Material, unreal.MaterialFactoryNew())
WAT = unreal.load_asset("/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture")
WAN = unreal.load_asset("/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedNormal")
bc = mel.create_material_expression(m, unreal.MaterialExpressionTextureObjectParameter, -900, -200)
bc.set_editor_property("parameter_name", "BaseColorTex"); bc.set_editor_property("texture", unreal.load_asset("/Game/FantasyCastle/Texture/T_CastleWall_BC"))
nt = mel.create_material_expression(m, unreal.MaterialExpressionTextureObjectParameter, -900, 200)
nt.set_editor_property("parameter_name", "NormalTex"); nt.set_editor_property("texture", unreal.load_asset("/Game/FantasyCastle/Texture/T_CastleWall_N"))
nt.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
ts = mel.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -900, 50); ts.set_editor_property("parameter_name", "TileSize"); ts.set_editor_property("default_value", 300.0)
c1 = mel.create_material_expression(m, unreal.MaterialExpressionMaterialFunctionCall, -500, -200); c1.set_material_function(WAT)
c2 = mel.create_material_expression(m, unreal.MaterialExpressionMaterialFunctionCall, -500, 200); c2.set_material_function(WAN)
for c in (c1, c2): mel.connect_material_expressions(ts, "", c, "TextureSize")
mel.connect_material_expressions(bc, "", c1, "TextureObject"); mel.connect_material_expressions(nt, "", c2, "TextureObject")
tint = mel.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -500, -400); tint.set_editor_property("parameter_name", "Tint")
tint.set_editor_property("default_value", unreal.LinearColor(1, 1, 1, 1))
mul = mel.create_material_expression(m, unreal.MaterialExpressionMultiply, -250, -250)
mel.connect_material_expressions(c1, "XYZ Texture", mul, "A"); mel.connect_material_expressions(tint, "", mul, "B")
mel.connect_material_property(mul, "", unreal.MaterialProperty.MP_BASE_COLOR)
mel.connect_material_property(c2, "XYZ Texture", unreal.MaterialProperty.MP_NORMAL)
rg = mel.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -250, 50); rg.set_editor_property("parameter_name", "Roughness"); rg.set_editor_property("default_value", 0.85)
mel.connect_material_property(rg, "", unreal.MaterialProperty.MP_ROUGHNESS)
mel.recompile_material(m); eal.save_loaded_asset(m)
ok = mel.get_statistics(m).num_pixel_shader_instructions > 0; print("M_FCL_WorldAligned compiles:", ok)
T = "/Game/FantasyCastle/Texture/"; L = "/Game/Medieval_Lake_Village/Textures/"
def lake(n):
    for p in eal.list_assets("/Game/Medieval_Lake_Village/Textures", recursive=True):
        if p.split("/")[-1].split(".")[0] == n: return p.split(".")[0]
INST = {"MI_FCL_CastleWall": (T + "T_CastleWall_BC", T + "T_CastleWall_N", 320.0, 0.85, (1, 1, 1)),
        "MI_FCL_CastleFloor": (T + "T_Slate_Flooring_BC", T + "T_Slate_Flooring_N", 240.0, 0.7, (0.9, 0.88, 0.85)),
        "MI_FCL_Plaster": (T + "T_Plaster_Wall_BC", T + "T_Plaster_Wall_N", 260.0, 0.9, (1, 0.97, 0.92)),
        "MI_FCL_StoneBlock": (T + "T_Stone_Wall_BC", T + "T_Stone_Wall_N", 280.0, 0.85, (1, 1, 1)),
        "MI_FCL_WoodCeiling": (lake("T_Weathered_Wood_BC"), lake("T_Weathered_Wood_N"), 220.0, 0.8, (0.75, 0.65, 0.55)),
        "MI_FCL_WoodFloor": (lake("T_BridgeFloor_BC"), lake("T_BridgeFloor_N"), 260.0, 0.75, (1, 1, 1))}
for name, (b, n, tile, rough, tintc) in INST.items():
    p = f"{D}/{name}"
    if eal.does_asset_exist(p): eal.delete_asset(p)
    mi = at.create_asset(name, D, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, m)
    mel.set_material_instance_texture_parameter_value(mi, "BaseColorTex", unreal.load_asset(b))
    mel.set_material_instance_texture_parameter_value(mi, "NormalTex", unreal.load_asset(n))
    mel.set_material_instance_scalar_parameter_value(mi, "TileSize", tile); mel.set_material_instance_scalar_parameter_value(mi, "Roughness", rough)
    mel.set_material_instance_vector_parameter_value(mi, "Tint", unreal.LinearColor(*tintc, 1))
    eal.save_loaded_asset(mi); print(name, b.split("/")[-1], n.split("/")[-1], tile)
