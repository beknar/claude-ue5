"""Re-solve the body parametrically from its own (conformed) measurements, removing conform
artifacts. Args: asset_path [name=value,...] overrides"""
import sys, unreal
ch = unreal.load_asset(sys.argv[1])
over = dict(kv.split("=") for kv in sys.argv[2].split(",")) if len(sys.argv) > 2 and sys.argv[2] != "none" else {}
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
if not (mhs.is_object_added_for_editing(ch) or mhs.try_add_object_to_edit(ch)):
    raise RuntimeError("cannot edit")
cons = mhs.get_body_constraints(ch)
new = []
for c in cons:
    n = str(c.name)
    c.is_active = True
    if n in over:
        c.target_measurement = float(over[n])
    new.append(c)
    print(f"{n:24s} {c.target_measurement:7.2f}")
mhs.set_body_constraints(character=ch, body_constraints=new)
mhs.commit_body_state(character=ch)
unreal.MetaHumanGeneratorSubsystemWrapper.reset_neck_to_body(ch)
unreal.EditorAssetLibrary.save_loaded_asset(ch, only_if_is_dirty=False)
after = {str(c.name): round(c.target_measurement, 1) for c in mhs.get_body_constraints(ch)}
print("AFTER", after)
