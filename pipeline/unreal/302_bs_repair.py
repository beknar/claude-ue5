"""Repair + persist blendspace samples (an in-place sample swap is not marked dirty, so save_loaded_asset skipped it and an
editor restart reverted it):
- FF2: her own clips (idle 0 / Walk 300 / Run 600 grid positions)
- FF : samples lost when the retarget was re-run -> re-point each to <template sample name>_FF (same order as the template)
Saves with only_if_is_dirty=False and verifies after reloading the package from disk."""
import unreal
eal = unreal.EditorAssetLibrary
def samples(bs): return list(bs.get_editor_property("sample_data"))
def ypos(s): return float(s.export_text().split("Y=")[1].split(",")[0])
def persist(path, assign):
    bs = unreal.load_asset(path); smp = samples(bs)
    for i in range(len(smp)):
        s = smp[i]; s.set_editor_property("animation", assign(i, s)); smp[i] = s
    bs.modify(); bs.set_editor_property("sample_data", smp)
    print(path.split("/")[-1], "save", eal.save_loaded_asset(bs, only_if_is_dirty=False))
    unreal.EditorLoadingAndSavingUtils.reload_packages([unreal.load_package(path)])
    bs = unreal.load_asset(path)
    print("  on disk:", sorted({f"{s.get_editor_property('animation').get_name() if s.get_editor_property('animation') else None}@{ypos(s):.0f}" for s in samples(bs)}))
A = lambda n: unreal.load_asset(f"/Game/FF2/Anims/AS_FF2_{n}")
idle, walk, run = A("Idle"), A("Walk"), A("Run")
persist("/Game/FF2/Locomotion/Anims/BS_Idle_Walk_Run_FF2", lambda i, s: idle if ypos(s) < 1 else (walk if ypos(s) < 450 else run))
tmpl = samples(unreal.load_asset("/Game/Characters/Mannequins/Anims/Unarmed/BS_Idle_Walk_Run"))
def ff(i, s):
    name = tmpl[i].get_editor_property("animation").get_name() + "_FF"
    a = unreal.load_asset(f"/Game/FF/Locomotion/Anims/{name}")
    if a is None: print("  missing", name)
    return a
persist("/Game/FF/Locomotion/Anims/BS_Idle_Walk_Run_FF", ff)
