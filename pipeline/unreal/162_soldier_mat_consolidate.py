"""The FBX import auto-creates blank M_Soldier_* materials in /Game/Soldier/Character (named after the FBX slots) and the mesh
ends up using them. Point the mesh slots at the textured /Game/Soldier/Materials versions, then delete the blanks."""
import unreal
eal = unreal.EditorAssetLibrary
D = "/Game/Soldier"
sk = unreal.load_asset(f"{D}/Character/SK_Dystopia_Soldier_02")
mats = {k: unreal.load_asset(f"{D}/Materials/M_Soldier_{k}") for k in ("Body", "Details", "FireGun")}
new = []                                                   # struct elements are copies: build fresh ones
for s in sk.get_editor_property("materials"):
    sn = str(s.get_editor_property("material_slot_name"))
    key = "FireGun" if "FireGun" in sn else ("Body" if "Body" in sn else "Details")
    n = unreal.SkeletalMaterial(material_interface=mats[key], material_slot_name=sn)
    new.append(n)
sk.set_editor_property("materials", new)
sk.modify(); eal.save_loaded_asset(sk, only_if_is_dirty=False)
for k in mats:
    blank = f"{D}/Character/M_Soldier_{k}"
    if eal.does_asset_exist(blank): print("delete", blank, eal.delete_asset(blank))
sk = unreal.load_asset(f"{D}/Character/SK_Dystopia_Soldier_02")
print([(str(s.material_slot_name), s.material_interface.get_path_name() if s.material_interface else None) for s in sk.get_editor_property("materials")])
