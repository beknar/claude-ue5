import unreal
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
ch = unreal.load_asset("/Game/Fig4/MetaHuman/MHC_Fig4_Final")
if not (mhs.is_object_added_for_editing(ch) or mhs.try_add_object_to_edit(ch)):
    raise RuntimeError("edit")
print("fixed_body_type", ch.fixed_body_type)
def show(tag, scale):
    cs = mhs.get_body_constraints(character=ch, scale_measurement_ranges_with_height=scale)
    print(tag, {str(c.name): (round(c.target_measurement, 1), c.is_active) for c in cs if str(c.name) in ("Height", "Chest", "Waist", "Masculine/Feminine")})
    return cs
cs = show("before", False)
for c in cs:
    if str(c.name) == "Masculine/Feminine": c.is_active = True; c.target_measurement = 1.2
    if str(c.name) == "Height": c.is_active = True; c.target_measurement = 156.0
mhs.set_body_constraints(character=ch, body_constraints=cs)
show("after set", False)
mhs.commit_body_state(character=ch)
show("after commit", False)
