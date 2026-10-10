import unreal
mel = unreal.MaterialEditingLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()
path = "/Game/Fig4/Materials/_tmp_pins"
if unreal.EditorAssetLibrary.does_asset_exist(path):
    unreal.EditorAssetLibrary.delete_asset(path)
m = at.create_asset("_tmp_pins", "/Game/Fig4/Materials", unreal.Material, unreal.MaterialFactoryNew())
e = mel.create_material_expression(m, unreal.MaterialExpressionMakeMaterialAttributes, 0, 0)
print("MMA inputs:", list(mel.get_material_expression_input_names(e)))
unreal.EditorAssetLibrary.delete_asset(path)
