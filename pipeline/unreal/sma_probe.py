"""Read-only probe of SetMaterialAttributes (no mutation of attribute arrays)."""
import unreal
e = unreal.new_object(unreal.MaterialExpressionSetMaterialAttributes)
for p in ("attribute_set_types", "inputs", "pre_edit_attribute_set_types"):
    try:
        print(p, "->", e.get_editor_property(p))
    except Exception as ex:
        print(p, "ERR", ex)
g = unreal.GuidLibrary.parse_string_to_guid("5973A03E13A74E0892D0CEDDF2936CF8")
print("guid parse:", g, unreal.GuidLibrary.is_valid(g[0] if isinstance(g, tuple) else g))
print("has ExpressionInput:", hasattr(unreal, "ExpressionInput"))
