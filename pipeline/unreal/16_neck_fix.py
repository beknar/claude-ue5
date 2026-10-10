"""Blend the face's neck into the parametric body and commit it (removes the collar seam)."""
import unreal
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
ch = unreal.load_asset("/Game/Fig4/MetaHuman/MHC_Fig4_Final")
if not (mhs.is_object_added_for_editing(ch) or mhs.try_add_object_to_edit(ch)):
    raise RuntimeError("edit")
mhs.remove_face_rig(ch)
unreal.MetaHumanGeneratorSubsystemWrapper.reset_neck_to_body(ch)
mhs.commit_face_state(ch)
unreal.EditorAssetLibrary.save_loaded_asset(ch, only_if_is_dirty=False)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if "PreviewActor" in a.get_actor_label():
        eas.destroy_actor(a)
p = mhs.spawn_meta_human_actor(ch)
p.set_actor_location(unreal.Vector(-150, 0, 6), False, False)
print("neck reset committed; preview at -150")
