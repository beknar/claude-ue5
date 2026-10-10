"""Set fig4's skin, eyes, lashes and makeup on MHC_Fig4. Args: skin_u skin_v face_tex_idx body_tex_idx"""
import sys, unreal

U, V = float(sys.argv[1]), float(sys.argv[2])
FACE_IDX, BODY_IDX = int(sys.argv[3]), int(sys.argv[4])
ch = unreal.load_asset("/Game/Fig4/MetaHuman/MHC_Fig4_Final")
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
aes = unreal.get_editor_subsystem(unreal.AssetEditorSubsystem)
if not (mhs.is_object_added_for_editing(ch) or mhs.try_add_object_to_edit(ch)):
    raise RuntimeError("cannot edit")
try:
    ss = ch.skin_settings
    sk = ss.skin
    sk.u, sk.v = U, V
    sk.face_texture_index, sk.body_texture_index = FACE_IDX, BODY_IDX
    sk.roughness = 0.95
    sk.show_top_underwear = False
    sk.fingernail_tint_color = unreal.LinearColor(0.35, 0.02, 0.03, 1); sk.fingernail_tint_intensity = 0.85
    sk.fingernail_roughness = 0.15
    ss.skin = sk
    fr = ss.freckles; fr.mask = unreal.MetaHumanCharacterFrecklesMask.NONE; ss.freckles = fr
    acc = ss.accents
    lips = acc.lips; lips.redness = 0.55; lips.saturation = 0.5; acc.lips = lips
    cheeks = acc.cheeks; cheeks.redness = 0.55; acc.cheeks = cheeks
    ss.accents = acc
    res = ss.desired_texture_sources_resolutions
    best = None
    for name in ("RES8K", "RES4K", "RES2K"):
        enum_t = type(res.face_albedo)
        if hasattr(enum_t, name):
            best = getattr(enum_t, name); break
    for f in ("face_albedo", "face_normal", "face_cavity", "face_animated_maps",
              "body_albedo", "body_normal", "body_cavity", "body_masks"):
        setattr(res, f, best)
    ss.desired_texture_sources_resolutions = res
    print("texture res", best)
    ch.preview_material_type = unreal.MetaHumanCharacterSkinPreviewMaterial.EDITABLE
    mhs.commit_skin_settings(ch, ss)

    es = ch.eyes_settings
    for side in ("eye_left", "eye_right"):
        e = getattr(es, side)
        iris = e.iris
        iris.primary_color_u, iris.primary_color_v = 0.12, 0.30      # dark warm brown-grey
        iris.secondary_color_u, iris.secondary_color_v = 0.08, 0.22
        iris.global_saturation = 0.9
        e.iris = iris
        pup = e.pupil; pup.dilation = 1.05; e.pupil = pup
        sc = e.sclera; sc.vascularity_intensity = 0.25; e.sclera = sc
        setattr(es, side, e)
    mhs.commit_eyes_settings(ch, es)

    hm = ch.head_model_settings
    el = hm.eyelashes
    el.type = unreal.MetaHumanCharacterEyelashesType.LONG_CURL
    el.melanin = 0.95; el.redness = 0.1; el.enable_grooms = True
    hm.eyelashes = el
    mhs.commit_head_model_settings(ch, hm)

    mk = ch.makeup_settings
    eyes = mk.eyes
    eyes.type = unreal.MetaHumanCharacterEyeMakeupType.THIN_LINER
    eyes.primary_color = unreal.LinearColor(0.02, 0.012, 0.01, 1); eyes.opacity = 0.75; eyes.roughness = 0.6
    mk.eyes = eyes
    lips_mk = mk.lips
    lips_mk.type = unreal.MetaHumanCharacterLipsMakeupType.NATURAL
    lips_mk.color = unreal.LinearColor(0.62, 0.10, 0.10, 1); lips_mk.opacity = 0.38
    lips_mk.roughness = 0.22; lips_mk.metalness = 0.0
    mk.lips = lips_mk
    bl = mk.blush
    bl.type = unreal.MetaHumanCharacterBlushMakeupType.APPLE
    bl.color = unreal.LinearColor(0.5, 0.08, 0.1, 1); bl.intensity = 0.18
    mk.blush = bl
    fd = mk.foundation; fd.apply_foundation = True; fd.color = unreal.LinearColor(0.80, 0.62, 0.55, 1)
    fd.intensity = 0.35; fd.roughness = 0.55; fd.concealer = 0.4
    mk.foundation = fd
    mhs.commit_makeup_settings(ch, mk)
    unreal.EditorAssetLibrary.save_loaded_asset(ch, only_if_is_dirty=False)
    print("LOOK applied", U, V, FACE_IDX, BODY_IDX)
finally:
    pass
