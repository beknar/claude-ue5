import unreal
mel = unreal.MaterialEditingLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()
def s32(v): return v - (1 << 32) if v >= (1 << 31) else v
def guid(a, b, c, d):
    g = unreal.Guid()
    for k, v in zip("abcd", (a, b, c, d)):
        try:
            g.set_editor_property(k, v)
        except Exception:
            g.set_editor_property(k, s32(v))
    return g
FRONT = guid(0x5973A03E, 0x13A74E08, 0x92D0CEDD, 0xF2936CF8)
DISP = guid(0x199A7166, 0xC67041DC, 0xA68EAD0D, 0x7017D0AD)
print("guids", FRONT, DISP)
path = "/Game/Fig4/Materials/_tmp_sma"
if unreal.EditorAssetLibrary.does_asset_exist(path):
    unreal.EditorAssetLibrary.delete_asset(path)
m = at.create_asset("_tmp_sma", "/Game/Fig4/Materials", unreal.Material, unreal.MaterialFactoryNew())
m.set_editor_property("use_material_attributes", True)
sma = mel.create_material_expression(m, unreal.MaterialExpressionSetMaterialAttributes, -300, 0)
print("sma props:", [p for p in dir(sma) if "attr" in p.lower()])
sma.set_editor_property("attribute_set_types", [FRONT, DISP])
print("sma inputs:", list(mel.get_material_expression_input_names(sma)))
slab = mel.create_material_expression(m, unreal.MaterialExpressionSubstrateSlabBSDF, -600, 0)
c = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -600, 200)
names = list(mel.get_material_expression_input_names(sma))
print("connect slab", mel.connect_material_expressions(slab, "", sma, names[1]))
print("connect disp", mel.connect_material_expressions(c, "", sma, names[2]))
print("connect out", mel.connect_material_property(sma, "", unreal.MaterialProperty.MP_MATERIAL_ATTRIBUTES))
mel.recompile_material(m)
unreal.EditorAssetLibrary.delete_asset(path)
