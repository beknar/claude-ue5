import unreal
eal = unreal.EditorAssetLibrary
D = "/Game/Fig4/Locomotion/Heels/"
new = unreal.load_asset(D + "HR_AS_MH_Neutral_Run_Loop_F")
old = unreal.load_asset(D + "H_AS_MH_Neutral_Run_Loop_F")
refs = eal.find_package_referencers_for_asset(D + "H_AS_MH_Neutral_Run_Loop_F", False)
print("referencers", refs)
print("consolidate", eal.consolidate_assets(new, [old]))
for r in refs:
    a = eal.load_asset(r)
    if a: eal.save_loaded_asset(a, False)
abp = unreal.load_asset("/Game/Fig4/Locomotion/Anims/ABP_Unarmed_Fig4")
unreal.BlueprintEditorLibrary.compile_blueprint(abp); eal.save_loaded_asset(abp)
bs = unreal.load_asset("/Game/Fig4/Locomotion/Anims/BS_Idle_Walk_Run_Fig4")
print([s for s in bs.get_editor_property("sample_data").__iter__()][:1] and bs.export_text()[:0])
print("refs to HR", eal.find_package_referencers_for_asset(D + "HR_AS_MH_Neutral_Run_Loop_F", False))
