"""PIE probe (player pawn): idle 0-2 s, walk 2-6 s, run 6-10.5 s along +X. Each tick the four sole points (heel/toe,
carried by foot_/ball_) are traced against the ground -> lowest sole gap (floating) and world speed of the planted
contact point (sliding). Logs 'CONTACT' summaries per phase."""
import json, time, unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(w, 0); pawn = pc.get_controlled_pawn()
mesh = pawn.get_editor_property("mesh")
SO = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\ff2_anime\soles.json"))
ref = unreal.AnimPoseExtensions.get_reference_pose(mesh.get_skeletal_mesh_asset().get_editor_property("skeleton"))
PTS = []
for s in ("l", "r"):
    for nm in ("heel", "toe"):
        b = f"foot_{s}" if nm == "heel" else f"ball_{s}"
        rest = unreal.AnimPoseExtensions.get_bone_pose(ref, b, unreal.AnimPoseSpaces.WORLD)
        PTS.append(((s, nm), b, rest.inverse_transform_location(unreal.Vector(*SO[s][nm])), SO[s][nm][2]))
eis = list(unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem))[-1]
move, sprint = unreal.load_asset("/Game/Input/Actions/IA_Move"), unreal.load_asset("/Game/Input/Actions/IA_Sprint")
def ground(p):
    hit = unreal.SystemLibrary.line_trace_single(w, unreal.Vector(p.x, p.y, p.z + 60), unreal.Vector(p.x, p.y, p.z - 200),
                                                 unreal.TraceTypeQuery.ECC_VISIBILITY, False, [pawn], unreal.DrawDebugTrace.NONE, True)
    t = hit.to_tuple(); return t[4].z if (t[0] or t[1]) else p.z
S = {"t0": time.time(), "prev": None, "ph": {}}
def phase(t): return "idle" if t < 2 else ("walk" if t < 6 else ("run" if t < 10.5 else None))
def tick(dt):
    t = time.time() - S["t0"]
    pc.set_control_rotation(unreal.Rotator(pitch=-8, yaw=0, roll=0))
    if 2.0 < t < 10.5: eis.inject_input_vector_for_action(move, unreal.Vector(0, 1, 0), [], [])
    if 6.0 < t < 10.5: eis.inject_input_vector_for_action(sprint, unreal.Vector(1, 0, 0), [], [])
    ph = phase(t)
    if ph is None:
        unreal.unregister_slate_post_tick_callback(S["h"])
        out = []
        for k, v in S["ph"].items():
            g = sorted(v["gap"]); sl = sorted(v["slip"])
            dts = sorted(v["dt"]); sp = sorted(v["spd"])
            out.append(f"{k}: dt med {1000*dts[len(dts)//2]:.0f} ms max {1000*dts[-1]:.0f} ms, pawn speed med {sp[len(sp)//2]:.0f} | gap p10 {g[len(g)//10]:.1f} med {g[len(g)//2]:.1f} p90 {g[9*len(g)//10]:.1f} | slip med {sl[len(sl)//2] if sl else 0:.0f} p75 {sl[3*len(sl)//4] if sl else 0:.0f} cm/s (n={len(sl)})")
        unreal.log("CONTACT " + " || ".join(out)); return
    cur = {}
    for key, bone, lp, rz in PTS:
        p = mesh.get_socket_transform(bone, unreal.RelativeTransformSpace.RTS_WORLD).transform_location(lp)
        cur[key] = (p, p.z - rz - ground(p), p.z - rz)
    lo = min(cur, key=lambda k: cur[k][2])           # planted = lowest in the pose (not smallest ground gap: bumps fool that)
    d = S["ph"].setdefault(ph, {"gap": [], "slip": [], "dt": [], "spd": []})
    if t - (2.0 if ph == "walk" else 6.0 if ph == "run" else 0) > 1.0:      # skip the acceleration second
        d["gap"].append(cur[lo][1]); d["dt"].append(dt); vv = pawn.get_velocity(); d["spd"].append((vv.x ** 2 + vv.y ** 2) ** 0.5)
        if S["prev"] and S["prev"][0] == lo and dt > 0:
            v = cur[lo][0] - S["prev"][1]; d["slip"].append(((v.x ** 2 + v.y ** 2) ** 0.5) / dt)
    S["prev"] = (lo, cur[lo][0])
S["h"] = unreal.register_slate_post_tick_callback(tick)
