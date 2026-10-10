import unreal
p = unreal.ConformTargetParams()
print(p.to_dict())
for n in dir(unreal):
    if "Conform" in n and ("Settings" in n or "Params" in n or "Options" in n):
        try:
            print(n, getattr(unreal, n)().to_dict())
        except Exception as e:
            print(n, "?", e)
