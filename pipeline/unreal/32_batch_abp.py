import unreal
inp = unreal.IKRetargetBatchOperationInputs()
print("inputs fields:", list(inp.to_dict().keys()))
src_mesh = unreal.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple")
tgt_mesh = unreal.load_asset("/Game/MetaHumans/Fig4/Body/SKM_MHC_Fig4_Final_BodyMesh")
rtg = unreal.load_asset("/Game/Fig4/Locomotion/Rigs/RTG_Quinn_To_Fig4")
abp = unreal.EditorAssetLibrary.find_asset_data("/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed")
vals = {"assets_to_retarget": [abp], "source_mesh": src_mesh, "target_mesh": tgt_mesh, "ik_retarget_asset": rtg,
        "retargeter": rtg, "suffix": "_Fig4", "include_referenced_assets": True, "overwrite_existing_files": True,
        "export_animations": False}
for k, v in vals.items():
    try: inp.set_editor_property(k, v)
    except Exception as e: print("skip", k, str(e)[:60])
print(inp.to_dict())
res = unreal.IKRetargetBatchOperation.run_batch_retarget(inp)
print("retargeted:", [str(r.package_name) for r in res])
