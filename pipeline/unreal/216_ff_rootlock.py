"""Retargeted template locomotion clips carry root motion that the AnimBP plays straight into the mesh (pelvis runs
metres ahead of the capsule). Lock the root on every locomotion clip; montage clips (attacks, dash) keep root motion
so the CharacterMovement component extracts it."""
import unreal
eal = unreal.EditorAssetLibrary
for p in ("/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd", "/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_01"):
    a = unreal.load_asset(p)
    print("source", a.get_name(), "root motion", a.get_editor_property("enable_root_motion"), "force lock", a.get_editor_property("force_root_lock"),
          "lock", a.get_editor_property("root_motion_root_lock"))
KEEP = ("MM_Attack", "MM_ChargedAttack", "MM_Dash")
n = 0
for p in eal.list_assets("/Game/FF/Locomotion/Anims", recursive=False):
    a = unreal.load_asset(p)
    if not isinstance(a, unreal.AnimSequence) or any(k in p for k in KEEP): continue
    a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True)
    a.set_editor_property("root_motion_root_lock", unreal.RootMotionRootLock.REF_POSE)
    eal.save_loaded_asset(a); n += 1
print("root-locked", n, "clips")
