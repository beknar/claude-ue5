import unreal
names = [n for n in dir(unreal) if n.startswith("MaterialExpressionSubstrate")]
print("EXPR:", names)
for n in ("MaterialExpressionSubstrateSlabBSDF", "MaterialExpressionSubstrateVerticalLayering",
          "MaterialExpressionSubstrateHorizontalMixing", "MaterialExpressionSubstrateHazinessToSecondaryRoughness"):
    c = getattr(unreal, n, None)
    if c:
        o = unreal.new_object(c)
        print(n, [p for p in dir(o) if not p.startswith("_") and p not in dir(unreal.MaterialExpression)][:40])
for n in ("SpecularProfile", "SubsurfaceProfile", "SpecularProfileFactory", "SubstrateSpecularProfile"):
    print(n, hasattr(unreal, n))
sp = getattr(unreal, "SpecularProfile", None)
if sp:
    o = unreal.new_object(sp)
    print("SpecularProfile props:", o.get_editor_property("settings") if hasattr(o, "settings") else dir(o)[:60])
m = unreal.Material()
print("Material props sample:", [p for p in ("enable_tessellation", "displacement_scaling", "displacement_fade_range", "used_with_skeletal_mesh", "used_with_nanite") ])
for p in ("enable_tessellation", "displacement_scaling", "used_with_nanite", "used_with_skeletal_mesh"):
    try:
        print(" ", p, m.get_editor_property(p))
    except Exception as e:
        print(" ", p, "ERR", e)
