import sys, unreal
ch = unreal.load_asset(sys.argv[1])
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
if not (mhs.is_object_added_for_editing(ch) or mhs.try_add_object_to_edit(ch)):
    raise RuntimeError("cannot edit")
cons = mhs.get_body_constraints(ch)
for c in cons:
    print(c.to_dict() if hasattr(c, "to_dict") else c)
print("fixed_body_type", ch.fixed_body_type)
