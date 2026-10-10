import unreal
eal = unreal.EditorAssetLibrary
root = eal.list_assets("/Game", recursive=False)
moved = []
for a in root:
    n = a.split(".")[-1]
    if n.endswith("_Fig4"):
        dst = f"/Game/Fig4/Locomotion/Anims/{n}"
        if eal.does_asset_exist(dst): eal.delete_asset(dst)
        ok = eal.rename_asset(a.split(".")[0], dst); moved.append((n, ok))
print("moved:", moved)
print("ABP exists:", eal.does_asset_exist("/Game/Fig4/Locomotion/Anims/ABP_Unarmed_Fig4"))
bs = unreal.load_asset("/Game/Fig4/Locomotion/Anims/BS_Idle_Walk_Run_Fig4")
print("BS type", type(bs).__name__, "skeleton", bs.get_editor_property("skeleton").get_name())
try:
    params = bs.get_editor_property("blend_parameters")
    print("axes", [(p.display_name, p.min, p.max) for p in params])
except Exception as e:
    print("axes?", str(e)[:80])
try:
    samples = bs.get_editor_property("sample_data")
    for s in samples: print("  sample", s.animation.get_name() if s.animation else None, s.sample_value)
except Exception as e:
    print("samples?", str(e)[:80])
