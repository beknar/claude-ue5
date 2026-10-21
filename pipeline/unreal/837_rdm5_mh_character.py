"""random_dungeonmagic_level5, the Summoner's MetaHuman face, step 1: the MetaHuman Character MHC_Summoner
(/Game/JRPG/MetaHuman). Her own face is an anime face painted on a skull twice a human face's height: the MetaHuman
conform fitted to it (her head, or her face alone, with her eyelids tracked on a portrait) came out a grotesque, a huge
cranium over a small face, or a lopsided flat one. So the face is Epic's preset Aera (of the 30 presets the young, round,
soft face with a small nose and chin closest to hers; mixing in a share of the conform only narrowed her eyes), with her
colouring: blond brows (a groom: WI_Eyebrows_M_SlightArch, melanin low), dark lashes with a curl (the preset's), amber
eyes, pale skin. Her own hair (the GLB's bangs, twin tails and the hair painted on her skull) stays on her and covers the
MetaHuman's bald scalp (838). 838 rigs it (Epic's cloud service, joints and blend shapes) and builds it. Args: none"""
import unreal
DIR, NAME, PRESET = "/Game/JRPG/MetaHuman", "MHC_Summoner", "/MetaHumanCharacter/Optional/Presets/Aera"
BROWS = "/MetaHumanCharacter/Optional/Grooms/Bindings/Eyebrows/WI_Eyebrows_M_SlightArch"
BROW_PARAMS = {"Melanin": 0.12, "Redness": 0.35}
path = f"{DIR}/{NAME}"
eal = unreal.EditorAssetLibrary
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if "PreviewActor" in a.get_actor_label(): eas.destroy_actor(a)
if eal.does_asset_exist(path):
    old = unreal.load_asset(path)
    if mhs.is_object_added_for_editing(old): mhs.remove_object_to_edit(old)
    unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(old)
    del old
    assert eal.delete_asset(path), "could not delete the old " + path
ch = eal.duplicate_asset(PRESET, path); assert ch, "duplicate " + PRESET
# the brows: a groom in the Eyebrows slot
col = ch.internal_collection
wi = unreal.load_asset(BROWS); assert wi, BROWS
key = col.try_add_item_from_wardrobe_item("Eyebrows", wi)
col.default_instance.try_add_slot_selection(unreal.MetaHumanPipelineSlotSelection(slot_name="Eyebrows", selected_item=key))
assert mhs.try_add_object_to_edit(ch), "cannot edit " + path
try:
    mhs.assemble_for_preview(character=ch)
    params = col.default_instance.get_instance_parameters(item_path=unreal.MetaHumanPaletteItemPath(item_key=key))
    names = [str(p.name) for p in params]
    for p in params:
        if str(p.name) in BROW_PARAMS: p.set_float(value=BROW_PARAMS[str(p.name)])
    print("RDM5MH brows", BROWS.split("/")[-1], "parameters", names)
    # lashes: dark brown, a little lighter than black (her drawn lashes are dark brown)
    hm = ch.head_model_settings; lashes = hm.eyelashes
    lashes.melanin = 0.55; lashes.redness = 0.3; hm.eyelashes = lashes
    mhs.commit_head_model_settings(ch, hm)
    # eyes: amber (her painted irises are golden brown); the preset's iris pattern and palette point a little warmer
    es = ch.eyes_settings
    for side in ("eye_left", "eye_right"):
        e = getattr(es, side); ir = e.iris
        ir.primary_color_u = 0.80; ir.primary_color_v = 0.20; ir.secondary_color_u = 0.93; ir.secondary_color_v = 0.12
        ir.global_saturation = 1.6; e.iris = ir; setattr(es, side, e)
    mhs.commit_eyes_settings(ch, es)
    ch.preview_material_type = unreal.MetaHumanCharacterSkinPreviewMaterial.EDITABLE
    eal.save_loaded_asset(ch, only_if_is_dirty=False)
    print("RDM5MH CHARACTER", path, "from", PRESET.split("/")[-1], "| lashes", hm.eyelashes.type, "| skin", ch.skin_settings.skin.u, ch.skin_settings.skin.v)
finally:
    if mhs.is_object_added_for_editing(ch): mhs.remove_object_to_edit(ch)
