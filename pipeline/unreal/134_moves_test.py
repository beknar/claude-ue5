import unreal, time
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(w, 0); pawn = pc.get_controlled_pawn()
arm = pawn.get_component_by_class(unreal.SpringArmComponent)
arm.set_editor_property("target_arm_length", 280.0); arm.set_editor_property("enable_camera_lag", False)
# (start, function or None, shot offset, name)
PLAN = [(1.0, "JUMP", 0.35, "runjump"), (4.0, "Act_Jab", 0.6, "jab"), (6.5, "Act_Hook", 0.55, "hook"),
        (9.0, "Act_Punch", 2.2, "punch"), (13.5, "Act_Sweep", 1.0, "sweep"), (16.5, "Act_Kick", 0.9, "kick"),
        (19.5, "Act_TurnLeft", 0.5, "turnL"), (21.5, "Act_TurnRight", 0.6, "turnR"), (23.5, "Act_Stroll", 0.6, "stroll")]
S = {"t0": time.time(), "done": set(), "log": []}
def tick(dt):
    t = time.time() - S["t0"]
    pc.set_control_rotation(unreal.Rotator(pitch=-5, yaw=pawn.get_actor_rotation().yaw + 90, roll=0))
    if t < 1.6: pawn.add_movement_input(pawn.get_actor_forward_vector(), 1.0)
    for start, fn, off, name in PLAN:
        if t >= start and ("c" + name) not in S["done"]:
            S["done"].add("c" + name); y0 = pawn.get_actor_rotation().yaw
            if fn == "JUMP": pawn.jump()
            else: pawn.call_method(fn)
            S["log"].append(f"{name}@{t:.1f} yaw0={y0:.0f}")
        if t >= start + off and ("s" + name) not in S["done"]:
            S["done"].add("s" + name); v = pawn.get_velocity()
            S["log"].append(f"{name} shot yaw={pawn.get_actor_rotation().yaw:.0f} vz={v.z:.0f} loc=({pawn.get_actor_location().x:.0f},{pawn.get_actor_location().y:.0f})")
            unreal.SystemLibrary.execute_console_command(w, f"HighResShot 960x540 filename=mv_{name}")
        if fn == "JUMP" and t > start + 0.2: pawn.stop_jumping()
    if t > 25.5: unreal.unregister_slate_post_tick_callback(S["h"]); unreal.log("MOVES " + " | ".join(S["log"]))
S["h"] = unreal.register_slate_post_tick_callback(tick)
