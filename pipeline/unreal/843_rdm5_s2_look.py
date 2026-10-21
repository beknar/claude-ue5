"""random_dungeonmagic_level5, Summoner2, step 2: MHC_Summoner2's look (842 fitted her shape), matched to her two photos
(ai models/Summoner2-sample1.jpg, -sample2.jpg) as SourceArt/summoner2/look.json gives it: the skin's tone and its accents
(rosy cheeks, lips, nose), no freckles, dark brown eyes, long curled lashes, the makeup (a little foundation, a thin
liner, apple blush, a coral-red lip tint), and the grooms: long straight hair with a fringe (WI_Hair_L_StraightBangs), brows,
peach fuzz. The groom colours are material instances of their own (MetaHuman's wardrobe parameters are not reachable from
Python here): MI_Summoner2_Hair (MetaHuman's MI_Hair: near-black roots, an ombre to magenta below), MI_Summoner2_Brows,
MI_Summoner2_Lashes, each with a _Cards and a _Helmet twin, in /Game/JRPG/MetaHuman/Summoner2/Materials; 844 gives them
to the built grooms.
Args: [character asset name, default MHC_Summoner2]"""
import json, sys, unreal
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\summoner2"
L = json.load(open(SA + r"\look.json"))
eal = unreal.EditorAssetLibrary
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
NAME = sys.argv[1] if len(sys.argv) > 1 else "MHC_Summoner2"
ch = unreal.load_asset("/Game/JRPG/MetaHuman/" + NAME); assert ch, "run 842 first"
LC = lambda c: unreal.LinearColor(c[0], c[1], c[2], c[3] if len(c) > 3 else 1.0)
# ---- grooms: the wardrobe items (a re-run keeps the ones already there)
col = ch.internal_collection
have = {str(col.get_item_slot_name(k)): k for k in col.get_all_item_keys()}
for slot, g in L["grooms"].items():
    wi = unreal.load_asset(g["item"]); assert wi, g["item"]
    keys = list(col.get_item_keys_for_wardrobe_item(wi)) if hasattr(col, "get_item_keys_for_wardrobe_item") else []
    key = keys[0] if keys else col.try_add_item_from_wardrobe_item(slot, wi)
    col.default_instance.try_add_slot_selection(unreal.MetaHumanPipelineSlotSelection(slot_name=slot, selected_item=key))
assert mhs.is_object_added_for_editing(ch) or mhs.try_add_object_to_edit(ch), "cannot edit " + NAME
try:
    ss = ch.skin_settings; sk = ss.skin; S = L["skin"]
    sk.u, sk.v = S["u"], S["v"]; sk.roughness = S["roughness"]
    sk.face_texture_index, sk.body_texture_index = S["face_texture_index"], S["body_texture_index"]
    sk.show_top_underwear = S["show_top_underwear"]
    ss.skin = sk
    fr = ss.freckles; fr.mask = getattr(unreal.MetaHumanCharacterFrecklesMask, L["freckles"]); ss.freckles = fr
    acc = ss.accents
    for region, v in L["accents"].items():
        a = getattr(acc, region)
        for k, x in v.items(): setattr(a, k, x)
        setattr(acc, region, a)
    ss.accents = acc
    res = ss.desired_texture_sources_resolutions; enum_t = type(res.face_albedo)
    best = next(getattr(enum_t, n) for n in ("RES8K", "RES4K", "RES2K") if hasattr(enum_t, n))
    for f in ("face_albedo", "face_normal", "face_cavity", "face_animated_maps", "body_albedo", "body_normal", "body_cavity", "body_masks"): setattr(res, f, best)
    ss.desired_texture_sources_resolutions = res
    ch.preview_material_type = unreal.MetaHumanCharacterSkinPreviewMaterial.EDITABLE
    mhs.commit_skin_settings(ch, ss)
    es = ch.eyes_settings; E = L["eyes"]
    for side in ("eye_left", "eye_right"):
        e = getattr(es, side); ir = e.iris
        ir.primary_color_u, ir.primary_color_v = E["primary_color_u"], E["primary_color_v"]
        ir.secondary_color_u, ir.secondary_color_v = E["secondary_color_u"], E["secondary_color_v"]
        ir.global_saturation = E["global_saturation"]; ir.pattern = getattr(unreal.MetaHumanCharacterEyesIrisPattern, E["pattern"])
        e.iris = ir; pu = e.pupil; pu.dilation = E["dilation"]; e.pupil = pu
        setattr(es, side, e)
    mhs.commit_eyes_settings(ch, es)
    hm = ch.head_model_settings; el = hm.eyelashes; La = L["lashes"]
    el.type = getattr(unreal.MetaHumanCharacterEyelashesType, La["type"]); el.melanin = La["melanin"]; el.redness = La["redness"]; el.enable_grooms = True
    hm.eyelashes = el; mhs.commit_head_model_settings(ch, hm)
    mk = ch.makeup_settings; M = L["makeup"]
    fd = mk.foundation; f = M["foundation"]; fd.apply_foundation = f["apply"]; fd.color = LC(f["color"]); fd.intensity = f["intensity"]; fd.roughness = f["roughness"]; fd.concealer = f["concealer"]; mk.foundation = fd
    ey = mk.eyes; f = M["eyes"]; ey.type = getattr(unreal.MetaHumanCharacterEyeMakeupType, f["type"]); ey.primary_color = LC(f["color"]); ey.opacity = f["opacity"]; ey.roughness = f["roughness"]; mk.eyes = ey
    bl = mk.blush; f = M["blush"]; bl.type = getattr(unreal.MetaHumanCharacterBlushMakeupType, f["type"]); bl.color = LC(f["color"]); bl.intensity = f["intensity"]; bl.roughness = f["roughness"]; mk.blush = bl
    lp = mk.lips; f = M["lips"]; lp.type = getattr(unreal.MetaHumanCharacterLipsMakeupType, f["type"]); lp.color = LC(f["color"]); lp.opacity = f["opacity"]; lp.roughness = f["roughness"]; lp.metalness = f["metalness"]; mk.lips = lp
    mhs.commit_makeup_settings(ch, mk)
    mhs.assemble_for_preview(character=ch)
    eal.save_loaded_asset(ch, only_if_is_dirty=False)
    print("S2LOOK skin", (sk.u, sk.v), "| lashes", el.type, "| makeup", ey.type, bl.type, lp.type, "| grooms", list(L["grooms"]))
finally:
    if mhs.is_object_added_for_editing(ch): mhs.remove_object_to_edit(ch)
# ---- the groom materials
MD = "/Game/JRPG/MetaHuman/Summoner2/Materials"
at = unreal.AssetToolsHelpers.get_asset_tools(); mel = unreal.MaterialEditingLibrary
# each in three: the strands' (MI_Hair), the cards' (MI_Hair_Cards) and the helmet's (MI_Hair_Helmet), the groom's own
# slots of the same names (844 gives them to the built grooms)
for name, key in (("MI_Summoner2_Hair", "hair_material"), ("MI_Summoner2_Brows", "brow_material"), ("MI_Summoner2_Lashes", "lash_material")):
    spec = L[key]
    for suffix in ("", "_Cards", "_Helmet"):
        p = f"{MD}/{name}{suffix}"
        # (updated in place when there: the built grooms use them, 844)
        mi = unreal.load_asset(p) if eal.does_asset_exist(p) else at.create_asset(name + suffix, MD, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mel.clear_all_material_instance_parameters(mi)
        mel.set_material_instance_parent(mi, unreal.load_asset("/MetaHumanCharacter/Materials/MI_Hair" + suffix))
        for k, v in spec.get("scalars", {}).items(): mel.set_material_instance_scalar_parameter_value(mi, k, float(v))
        for k, v in spec.get("vectors", {}).items(): mel.set_material_instance_vector_parameter_value(mi, k, LC(v))
        mel.update_material_instance(mi); eal.save_loaded_asset(mi, only_if_is_dirty=False)
    print("S2LOOK material", f"{MD}/{name}(_Cards, _Helmet)", spec.get("scalars"), spec.get("vectors", {}))
