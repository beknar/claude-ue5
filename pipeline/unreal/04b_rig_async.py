"""Start auto-rigging non-blocking with progress UI (lets the editor run Epic's login flow)."""
import sys, unreal
ch = unreal.load_asset(sys.argv[1])
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([ch])
added = mhs.is_object_added_for_editing(ch) or mhs.try_add_object_to_edit(ch)
print("editing:", added)
rr = unreal.MetaHumanCharacterAutoRiggingRequestParams(); rr.blocking = False; rr.report_progress = True
rr.rig_type = unreal.MetaHumanRigType.JOINTS_AND_BLEND_SHAPES
mhs.request_auto_rigging(ch, rr)
print("auto-rig request started")
