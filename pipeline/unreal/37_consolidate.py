"""Point ABP_Unarmed_Fig4 / BS_Idle_Walk_Run_Fig4 at the heel-stance clips (MetaHuman mocap for
idle/walk/run) and move the blendspace's walk/run rows to the clips' natural speeds."""
import re, unreal
eal = unreal.EditorAssetLibrary
A = "/Game/Fig4/Locomotion/Anims/"; H = "/Game/Fig4/Locomotion/Heels/"
pairs = {"MF_Unarmed_Walk_Fwd_Fig4": "H_AS_MH_Neutral_Walk_Loop_F",
         "MF_Unarmed_Jog_Fwd_Fig4": "H_AS_MH_Neutral_Run_Loop_F",
         "MM_Idle_Fig4": "H_AS_MH_Neutral_Stand_Idle_Loop"}
for a in eal.list_assets(H, recursive=False):
    n = a.split(".")[-1]
    if n.startswith("H_M") and n[2:] not in pairs:
        pairs[n[2:]] = n
for old, new in pairs.items():
    if not eal.does_asset_exist(A + old) or not eal.does_asset_exist(H + new):
        print("skip", old, new); continue
    ok = eal.consolidate_assets(unreal.load_asset(H + new), [unreal.load_asset(A + old)])
    print("consolidated", old, "->", new, ok)
for a in eal.list_assets(H, recursive=False):
    o = unreal.load_asset(a.split(".")[0])
    if isinstance(o, unreal.AnimSequence):
        o.set_editor_property("enable_root_motion", False)
        eal.save_loaded_asset(o)

WALK, RUN = 180.0, 470.0
bs = unreal.load_asset(A + "BS_Idle_Walk_Run_Fig4")
samples = bs.get_editor_property("sample_data")
new = []
for s in samples:
    t = s.export_text()
    t = re.sub(r"Y=300\.000000", f"Y={WALK:.6f}", t); t = re.sub(r"Y=600\.000000", f"Y={RUN:.6f}", t)
    s2 = unreal.BlendSample(); s2.import_text(t); new.append(s2)
bs.set_editor_property("sample_data", new)
params = bs.get_editor_property("blend_parameters")
p1 = params[1]; t = p1.export_text().replace("Max=600.000000", f"Max={RUN:.6f}"); p1.import_text(t)
params[1] = p1; bs.set_editor_property("blend_parameters", params)
eal.save_loaded_asset(bs)
for s in bs.get_editor_property("sample_data")[:3] + bs.get_editor_property("sample_data")[9:10]:
    print(" ", re.search(r"Animation=([^,]+)", s.export_text()).group(1)[-50:], re.search(r"SampleValue=\(([^)]*)\)", s.export_text()).group(1))
abp = unreal.load_asset(A + "ABP_Unarmed_Fig4")
unreal.BlueprintEditorLibrary.compile_blueprint(abp)
eal.save_loaded_asset(abp)
print("ABP compiled")
