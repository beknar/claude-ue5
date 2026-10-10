"""IK rigs (auto) for Quinn and fig4's MetaHuman body, a retargeter, then batch-retarget the
template locomotion AnimBP (+ blendspace, idle/walk/jog/jump clips) onto the MetaHuman skeleton."""
import unreal
at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary
D = "/Game/Fig4/Locomotion"
src_mesh = unreal.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple")
tgt_mesh = unreal.load_asset("/Game/MetaHumans/Fig4/Body/SKM_MHC_Fig4_Final_BodyMesh")

def ik_rig(name, mesh):
    path = f"{D}/Rigs/{name}"
    if eal.does_asset_exist(path): eal.delete_asset(path)
    rig = at.create_asset(name, f"{D}/Rigs", unreal.IKRigDefinition, unreal.IKRigDefinitionFactory())
    c = unreal.IKRigController.get_controller(rig)
    c.set_skeletal_mesh(mesh)
    ok = c.apply_auto_generated_retarget_definition()
    try: c.apply_auto_fbik()
    except Exception as e: print("fbik:", str(e)[:60])
    chains = [str(ch.chain_name) for ch in c.get_retarget_chains()]
    print(name, "auto retarget def:", ok, "root:", c.get_retarget_root(), "chains:", len(chains))
    eal.save_loaded_asset(rig); return rig

src_rig = ik_rig("IK_Quinn_Auto", src_mesh)
tgt_rig = ik_rig("IK_Fig4_Auto", tgt_mesh)
rpath = f"{D}/Rigs/RTG_Quinn_To_Fig4"
if eal.does_asset_exist(rpath): eal.delete_asset(rpath)
rtg = at.create_asset("RTG_Quinn_To_Fig4", f"{D}/Rigs", unreal.IKRetargeter, unreal.IKRetargetFactory())
rc = unreal.IKRetargeterController.get_controller(rtg)
try: rc.add_default_ops()
except Exception as e: print("default ops:", str(e)[:80])
rc.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, src_rig)
rc.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
try:
    rc.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, src_mesh); rc.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET, tgt_mesh)
except Exception as e: print("preview mesh:", str(e)[:80])
try: rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
except Exception as e: print("assign ops:", str(e)[:80])
rc.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
try: rc.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
except Exception as e: print("align:", str(e)[:80])
eal.save_loaded_asset(rtg)
print("retargeter ready")

abp = unreal.EditorAssetLibrary.find_asset_data("/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed")
res = unreal.IKRetargetBatchOperation.duplicate_and_retarget([abp], src_mesh, tgt_mesh, rtg, "", "", "", "_Fig4", True)
print("retargeted:", [str(r.package_name) for r in res])
