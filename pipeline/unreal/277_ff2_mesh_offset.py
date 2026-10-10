"""BP_FF2Character: drop the mesh 2.2 cm below the capsule bottom (CharacterMovement floats the capsule ~2.2 cm)."""
import unreal
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
bp = unreal.load_asset("/Game/FF2/Game/BP_FF2Character")
H = {str(lib.get_variable_name(lib.get_data(h))): h for h in sds.k2_gather_subobject_data_for_blueprint(bp)}
mesh = lib.get_object_for_blueprint(lib.get_data(H["Mesh"]), bp)
mesh.set_editor_property("relative_location", unreal.Vector(0, 0, -85.2))
print("compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp)); unreal.EditorAssetLibrary.save_loaded_asset(bp)
print("mesh rel", unreal.get_default_object(bp.generated_class()).get_editor_property("mesh").get_editor_property("relative_location"))
