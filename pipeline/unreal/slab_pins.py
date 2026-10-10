import unreal
mel = unreal.MaterialEditingLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()
path = "/Game/Fig4/Materials/_tmp_pins"
if unreal.EditorAssetLibrary.does_asset_exist(path):
    unreal.EditorAssetLibrary.delete_asset(path)
m = at.create_asset("_tmp_pins", "/Game/Fig4/Materials", unreal.Material, unreal.MaterialFactoryNew())
for cls in (unreal.MaterialExpressionSubstrateSlabBSDF, unreal.MaterialExpressionSubstrateVerticalLayering,
            unreal.MaterialExpressionSubstrateHazinessToSecondaryRoughness, unreal.MaterialExpressionSubstrateHorizontalMixing):
    e = mel.create_material_expression(m, cls, 0, 0)
    print(cls.__name__, "inputs:", list(mel.get_material_expression_input_names(e)))
print([p for p in dir(unreal.MaterialProperty) if "FRONT" in p or "DISPLACEMENT" in p or "OPACITY" in p])
unreal.EditorAssetLibrary.delete_asset(path)
