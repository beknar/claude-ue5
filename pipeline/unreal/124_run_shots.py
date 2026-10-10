import sys, unreal, time
SCALE = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
TAG = sys.argv[2] if len(sys.argv) > 2 else "run"
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(w, 0); pawn = pc.get_controlled_pawn()
pawn.get_component_by_class(unreal.SpringArmComponent).set_editor_property("target_arm_length", 260.0)
pawn.get_component_by_class(unreal.SpringArmComponent).set_editor_property("enable_camera_lag", False)
S = {"t0": time.time(), "k": 0}
def tick(dt):
    t = time.time() - S["t0"]
    pc.set_control_rotation(unreal.Rotator(pitch=-5, yaw=90, roll=0))
    if t < 4.6: pawn.add_movement_input(unreal.Vector(1, 0, 0), SCALE)
    if S["k"] < 5 and t > 2.0 + 0.5 * S["k"]:
        unreal.SystemLibrary.execute_console_command(w, f"HighResShot 960x540 filename={TAG}_{S['k']}"); S["k"] += 1
    if t > 5: unreal.unregister_slate_post_tick_callback(S["h"])
S["h"] = unreal.register_slate_post_tick_callback(tick)
