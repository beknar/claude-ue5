"""Copy v9's face model coefficients (her identity) onto the seated final face; commit."""
import unreal
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
aes = unreal.get_editor_subsystem(unreal.AssetEditorSubsystem)
src = unreal.load_asset("/Game/Fig4/MetaHuman/MHC_Fig4v9")
dst = unreal.load_asset("/Game/Fig4/MetaHuman/MHC_Fig4_Final")
for c in (src, dst):
    if not (mhs.is_object_added_for_editing(c) or mhs.try_add_object_to_edit(c)):
        raise RuntimeError("edit")
cs = list(mhs.get_face_model_coefficients(src))
cd = list(mhs.get_face_model_coefficients(dst))
print("coeffs", len(cs), len(cd), "src[:6]", [round(x, 3) for x in cs[:6]], "dst[:6]", [round(x, 3) for x in cd[:6]])
lm_before = mhs.get_face_landmarks(dst)
mhs.remove_face_rig(dst)
mhs.set_face_model_coefficients(dst, cs)
lm_after = mhs.get_face_landmarks(dst)
import math
dz = sum(b.z - a.z for a, b in zip(lm_before, lm_after)) / max(len(lm_after), 1)
print("landmarks", len(lm_after), "mean dz after setting coeffs:", round(dz, 2))
mhs.commit_face_state(dst)
mhs.remove_object_to_edit(src)
unreal.EditorAssetLibrary.save_loaded_asset(dst, only_if_is_dirty=False)
aes.close_all_editors_for_asset(dst)
mhs.remove_object_to_edit(dst)
aes.open_editor_for_assets([dst])
