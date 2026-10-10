import unreal
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
for n in ("commit_face_state", "commit_body_state", "fit_face_state_from_body_with_eyes_teeth_template", "remove_face_rig"):
    print(n, (getattr(mhs, n).__doc__ or "")[:500].replace("\n", " | "))
