"""Apply fig4's measured body (from the conformed v9) to the fresh parametric MHC_Fig4_Final.
Iterating an unreal.Array yields struct copies, so the edited copies are collected and passed back."""
import sys, unreal
OVER = dict((k, float(v)) for k, v in (kv.split("=") for kv in sys.argv[1].split(","))) if len(sys.argv) > 1 and sys.argv[1] != "none" else {}
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
src = unreal.load_asset("/Game/Fig4/MetaHuman/MHC_Fig4v9")
dst = unreal.load_asset("/Game/Fig4/MetaHuman/MHC_Fig4_Final")
for c in (src, dst):
    if not (mhs.is_object_added_for_editing(c) or mhs.try_add_object_to_edit(c)):
        raise RuntimeError("edit")
targets = {str(c.name): c.target_measurement for c in mhs.get_body_constraints(character=src, scale_measurement_ranges_with_height=False)}
mhs.remove_object_to_edit(src)
targets.update(OVER)
SKIP = {"Fat", "Muscularity"}            # let the measurements drive these
edited = []
for c in mhs.get_body_constraints(character=dst, scale_measurement_ranges_with_height=False):
    n = str(c.name)
    if n in targets and n not in SKIP:
        c.is_active = True
        c.target_measurement = targets[n]
    else:
        c.is_active = False
    edited.append(c)
mhs.set_body_constraints(character=dst, body_constraints=edited)
mhs.commit_body_state(character=dst)
unreal.MetaHumanGeneratorSubsystemWrapper.reset_neck_to_body(dst)
unreal.EditorAssetLibrary.save_loaded_asset(dst, only_if_is_dirty=False)
got = {str(c.name): round(c.target_measurement, 1) for c in mhs.get_body_constraints(character=dst, scale_measurement_ranges_with_height=False)}
for k in ("Height", "Chest", "Underbust", "Waist", "Hip", "Thigh", "Across Shoulder", "Masculine/Feminine", "Fat", "Muscularity"):
    print(f"{k:20s} target {targets.get(k, 0):7.1f}  got {got.get(k)}")
# refresh the preview actor beside her
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if "MHC_Fig4_Final" in a.get_actor_label():
        eas.destroy_actor(a)
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([dst])
p = mhs.spawn_meta_human_actor(dst)
p.set_actor_location(unreal.Vector(-120, 0, 6), False, False)
