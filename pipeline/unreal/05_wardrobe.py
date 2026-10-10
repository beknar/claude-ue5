"""Add eyebrows + peach fuzz grooms to the character and set their colour parameters.
Args: asset_path"""
import sys, unreal
ch = unreal.load_asset(sys.argv[1])
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
ITEMS = [
    ("Eyebrows", "/MetaHumanCharacter/Optional/Grooms/Bindings/Eyebrows/WI_Eyebrows_M_Natural.WI_Eyebrows_M_Natural",
     {"Melanin": 0.92, "Redness": 0.15, "Roughness": 0.4}),
    ("Peachfuzz", "/MetaHumanCharacter/Optional/Grooms/Bindings/Peachfuzz/WI_Peachfuzz_M_Thin.WI_Peachfuzz_M_Thin",
     {"Melanin": 0.25}),
]
coll = ch.internal_collection
keys = {}
for slot, path, _ in ITEMS:
    wi = unreal.load_asset(path)
    key = coll.try_add_item_from_wardrobe_item(slot, wi)
    coll.default_instance.try_add_slot_selection(unreal.MetaHumanPipelineSlotSelection(slot_name=slot, selected_item=key))
    keys[slot] = key
    print("added", slot, key)
if not (mhs.is_object_added_for_editing(ch) or mhs.try_add_object_to_edit(ch)):
    raise RuntimeError("cannot edit")
mhs.assemble_for_preview(character=ch)
for slot, path, params in ITEMS:
    ip = coll.default_instance.get_instance_parameters(item_path=unreal.MetaHumanPaletteItemPath(item_key=keys[slot]))
    names = [p.name for p in ip]
    print(slot, "params:", names)
    for p in ip:
        if str(p.name) in params:
            p.set_float(value=params[str(p.name)]); print("  set", p.name, params[str(p.name)])
unreal.EditorAssetLibrary.save_loaded_asset(ch, only_if_is_dirty=False)
print("WARDROBE done")
