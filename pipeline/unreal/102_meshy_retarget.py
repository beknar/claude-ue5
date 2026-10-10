"""IK rig for the Meshy biped, Quinn -> Meshy retargeter, and a batch retarget of the template locomotion
AnimBP (+ its blendspace and jump/fall/land clips) onto the Meshy skeleton -> /Game/Meshy/Locomotion."""
import unreal
at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary
D = "/Game/Meshy/Locomotion"
src_mesh = unreal.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple")
tgt_mesh = unreal.load_asset("/Game/Meshy/Character/SK_Meshy_Biped")
src_rig = unreal.load_asset("/Game/Fig4/Locomotion/Rigs/IK_Quinn_Auto")
path = f"{D}/Rigs/IK_Meshy_Auto"
if eal.does_asset_exist(path): eal.delete_asset(path)
rig = at.create_asset("IK_Meshy_Auto", f"{D}/Rigs", unreal.IKRigDefinition, unreal.IKRigDefinitionFactory())
c = unreal.IKRigController.get_controller(rig)
c.set_skeletal_mesh(tgt_mesh)
print("auto retarget def:", c.apply_auto_generated_retarget_definition(), "root:", c.get_retarget_root())
try: c.apply_auto_fbik()
except Exception as e: print("fbik:", str(e)[:60])
print("chains:", [(str(ch.chain_name), str(ch.start_bone.bone_name) if hasattr(ch, "start_bone") else "", str(ch.end_bone.bone_name) if hasattr(ch, "end_bone") else "") for ch in c.get_retarget_chains()])
eal.save_loaded_asset(rig)
rpath = f"{D}/Rigs/RTG_Quinn_To_Meshy"
if eal.does_asset_exist(rpath): eal.delete_asset(rpath)
rtg = at.create_asset("RTG_Quinn_To_Meshy", f"{D}/Rigs", unreal.IKRetargeter, unreal.IKRetargetFactory())
rc = unreal.IKRetargeterController.get_controller(rtg)
rc.add_default_ops()
rc.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, rig)
rc.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, src_mesh); rc.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET, tgt_mesh)
rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.TARGET, rig)
rc.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
try: rc.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
except Exception as e: print("align:", str(e)[:80])
eal.save_loaded_asset(rtg)
inp = unreal.IKRetargetBatchOperationInputs()
inp.set_editor_property("assets_to_retarget", [eal.find_asset_data("/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed")])
inp.set_editor_property("source_mesh", src_mesh); inp.set_editor_property("target_mesh", tgt_mesh)
inp.set_editor_property("ik_retarget_asset", rtg); inp.set_editor_property("suffix", "_Meshy")
inp.set_editor_property("target_path", f"{D}/Anims"); inp.set_editor_property("include_referenced_assets", True)
inp.set_editor_property("overwrite_existing_files", True)
res = [str(r.package_name) for r in unreal.IKRetargetBatchOperation.run_batch_retarget(inp)]
print("retargeted:", res)
for p in res:
    if not p.startswith(D + "/Anims/"):
        name = p.split("/")[-1]
        print("move", p, eal.rename_asset(p, f"{D}/Anims/{name}"))
