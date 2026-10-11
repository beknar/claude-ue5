"""BP_FF2Character movement for rugged levels (fantasy_castle_level's pack terrain is triangle-collision rock with lips, road
curbs and spline seams): max step height 45 -> 60 cm, walkable floor angle 44.8 -> 50 deg. Saved on the class defaults."""
import unreal
bp = unreal.load_asset("/Game/FF2/Game/BP_FF2Character")
cdo = unreal.get_default_object(bp.generated_class())
cm = cdo.get_editor_property("character_movement")
cm.modify()
cm.set_editor_property("max_step_height", 60.0)
cm.set_walkable_floor_angle(50.0)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
cm = unreal.get_default_object(bp.generated_class()).get_editor_property("character_movement")
print("step", cm.get_editor_property("max_step_height"), "floor angle", round(cm.get_walkable_floor_angle(), 1))
