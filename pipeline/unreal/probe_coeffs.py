import unreal
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
for n in ("get_face_model_coefficients", "set_face_model_coefficients", "get_face_landmarks", "translate_face_landmarks", "fit_state_to_target_vertices"):
    print(n, (getattr(mhs, n).__doc__ or "")[:700].replace("\n", " | "))
    print()
