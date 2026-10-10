"""Cloud steps on the final character: texture synthesis then auto-rig. Args: asset_path step(textures|rig|both)"""
import sys, time, unreal
path, step = sys.argv[1], sys.argv[2]
ch = unreal.load_asset(path)
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
if not (mhs.is_object_added_for_editing(ch) or mhs.try_add_object_to_edit(ch)):
    raise RuntimeError("cannot edit")
try:
    if step in ("textures", "both"):
        t = time.time()
        req = unreal.MetaHumanCharacterTextureRequestParams(); req.blocking = True; req.report_progress = False
        mhs.request_texture_sources(ch, req)
        print(f"textures requested ({time.time()-t:.0f}s); has_high_resolution_textures={ch.has_high_resolution_textures}")
        print("synth info:", ch.synthesized_face_textures_info)
    if step in ("rig", "both"):
        t = time.time()
        rr = unreal.MetaHumanCharacterAutoRiggingRequestParams(); rr.blocking = True; rr.report_progress = False
        rr.rig_type = unreal.MetaHumanRigType.JOINTS_AND_BLEND_SHAPES
        mhs.request_auto_rigging(ch, rr)
        print(f"auto-rig requested ({time.time()-t:.0f}s)")
    unreal.EditorAssetLibrary.save_loaded_asset(ch, only_if_is_dirty=False)
finally:
    if mhs.is_object_added_for_editing(ch):
        mhs.remove_object_to_edit(ch)
