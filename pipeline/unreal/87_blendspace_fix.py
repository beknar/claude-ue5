"""BS_Idle_Walk_Run_Fig4: no grid snapping (it had pushed the walk samples to 235), fine speed grid,
walk samples at 180 cm/s (MetaHuman walk pace), run at 470."""
import unreal
bs = unreal.load_asset("/Game/Fig4/Locomotion/Anims/BS_Idle_Walk_Run_Fig4")
params = bs.get_editor_property("blend_parameters")
new_params = []
for i, p in enumerate(params):
    t = p.export_text()
    t = t.replace("bSnapToGrid=True", "bSnapToGrid=False")
    if "Speed" in t:
        import re
        t = re.sub(r"GridNum=\d+", "GridNum=47", t)
    q = unreal.BlendParameter(); q.import_text(t); new_params.append(q)
bs.set_editor_property("blend_parameters", new_params)
samples = []
for s in bs.get_editor_property("sample_data"):
    t = s.export_text().replace("Y=235.000000", "Y=180.000000")
    n = unreal.BlendSample(); n.import_text(t); samples.append(n)
bs.set_editor_property("sample_data", samples)
try: bs.validate_sample_data() if hasattr(bs, "validate_sample_data") else None
except Exception as e: print("validate", e)
bs.modify(); bs.post_edit_change() if hasattr(bs, "post_edit_change") else None
unreal.EditorAssetLibrary.save_loaded_asset(bs)
bs = unreal.load_asset("/Game/Fig4/Locomotion/Anims/BS_Idle_Walk_Run_Fig4")
for p in bs.get_editor_property("blend_parameters"): print(p.export_text())
print(sorted({s.export_text().split("SampleValue=")[1][:40] for s in bs.get_editor_property("sample_data")}))
