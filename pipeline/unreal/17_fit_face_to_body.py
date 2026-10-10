"""Fit the face state onto the current parametric body (seats the head on the neck) and commit."""
import unreal
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
ch = unreal.load_asset("/Game/Fig4/MetaHuman/MHC_Fig4_Final")
if not (mhs.is_object_added_for_editing(ch) or mhs.try_add_object_to_edit(ch)):
    raise RuntimeError("edit")
mhs.remove_face_rig(ch)
ok = mhs.fit_face_state_from_body_with_eyes_teeth_template(ch, None, None, None, True)
print("fit face to body:", ok)
mhs.commit_face_state(ch)
unreal.EditorAssetLibrary.save_loaded_asset(ch, only_if_is_dirty=False)
