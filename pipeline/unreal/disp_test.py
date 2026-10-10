import unreal
mel = unreal.MaterialEditingLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()
path = "/Game/Fig4/Materials/_tmp_disp"
if unreal.EditorAssetLibrary.does_asset_exist(path):
    unreal.EditorAssetLibrary.delete_asset(path)
m = at.create_asset("_tmp_disp", "/Game/Fig4/Materials", unreal.Material, unreal.MaterialFactoryNew())
c = mel.create_material_expression(m, unreal.MaterialExpressionConstant, 0, 0)
fm = unreal.MaterialProperty.MP_FRONT_MATERIAL
print("front value", fm.value, "wpo", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET.value)
for off in (1, 2):
    try:
        p = unreal.MaterialProperty.cast(fm.value + off)
        ok = mel.connect_material_property(c, "", p)
        back = mel.get_material_property_input_node(m, p)
        print("offset", off, "prop", p, "connect", ok, "readback", back)
    except Exception as e:
        print("offset", off, "ERR", e)
unreal.EditorAssetLibrary.delete_asset(path)
