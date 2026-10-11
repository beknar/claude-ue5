"""LS_SFC_Showcase (20 s @ 30 fps) in sf-city-level_Cine, cameras keyed from cine_demo_path.json (713 recording of 712):
 A  0.0- 7.6  boulevard: crane down from above the street onto her as she runs up to the Noodle Bar; the blast door rises,
              she walks in
 B  7.6-10.6  inside the bar from the far corner: she enters, turns and walks toward the camera (booths and neon behind)
 C 10.6-15.6  the bridge road: tracking her run from ahead (city behind), round to her side through the jump, then back
              in front of her (the bridge receding to the city)
 D 15.6-20.0  inside the Excavation Lab from the south-west consoles (712 hides the chairs): the door rises, she runs up and walks in; the relic glows behind her
Checks that no camera key sits inside geometry and that she is visible from the camera (visibility trace)."""
import json, bisect, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
at = unreal.AssetToolsHelpers.get_asset_tools(); V = unreal.Vector
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert w.get_path_name().startswith("/Game/SFCityLevel/Maps/sf-city-level_Cine."), w.get_path_name()
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_current_level_by_name("sf-city-level_Cine")
FPS, DUR = 30, 20.0
R = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\sf_city\cine_demo_path.json"))
rows = R["rows"]; ts = [r[0] for r in rows]; IDX = {k: i + 1 for i, k in enumerate(R["labels"])}
def P(lab, t):
    k = IDX[lab]; t = min(max(t, ts[0]), ts[-1]); i = min(max(1, bisect.bisect_left(ts, t)), len(ts) - 1)
    a, b = rows[i - 1][k], rows[i][k]; u = 0 if ts[i] == ts[i - 1] else (t - ts[i - 1]) / (ts[i] - ts[i - 1])
    return V(*[a[j] + (b[j] - a[j]) * u for j in range(3)])
def Ps(lab, t, wdt=0.6, n=9):
    acc = V(0, 0, 0)
    for k in range(n): acc = acc + P(lab, t - wdt / 2 + wdt * k / (n - 1)) * (1.0 / n)
    return acc
def ease(s, s0, s1):
    u = min(max((s - s0) / (s1 - s0), 0.0), 1.0); return u * u * (3 - 2 * u)
def lerp(a, b, u): return a + (b - a) * u
demos = {a.get_actor_label(): a for a in eas.get_all_level_actors() if a.get_actor_label().startswith("Demo_")}
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith("SFCCam_"): eas.destroy_actor(a)
def camera(label, focal, track):
    c = eas.spawn_actor_from_class(unreal.CineCameraActor, V(0, 0, 0)); c.set_actor_label(label); c.set_folder_path("SFC/Cine")
    cc = c.get_cine_camera_component()
    fb = cc.get_editor_property("filmback"); fb.sensor_width = 36.0; fb.sensor_height = 20.25; cc.set_editor_property("filmback", fb)
    cc.set_editor_property("current_focal_length", focal); cc.set_editor_property("current_aperture", 4.0)
    fs = cc.get_editor_property("focus_settings"); fs.focus_method = unreal.CameraFocusMethod.TRACKING
    tf = fs.get_editor_property("tracking_focus_settings"); tf.set_editor_property("actor_to_track", demos[track]); tf.set_editor_property("relative_offset", V(0, 0, 40))
    fs.set_editor_property("tracking_focus_settings", tf); fs.set_editor_property("smooth_focus_changes", True); fs.set_editor_property("focus_smoothing_interp_speed", 6.0)
    cc.set_editor_property("focus_settings", fs)
    pp = cc.get_editor_property("post_process_settings")            # adapt exposure fast after a cut (interior <-> exterior)
    for k, v in (("auto_exposure_speed_up", 20.0), ("auto_exposure_speed_down", 20.0)):
        pp.set_editor_property("override_" + k, True); pp.set_editor_property(k, v)
    cc.set_editor_property("post_process_settings", pp); cc.set_editor_property("post_process_blend_weight", 1.0)
    return c
A, C, D = "Demo_A_Boulevard", "Demo_C_Bridge", "Demo_D_Lab"
A0, A1, B1, C1, D1 = 0.0, 7.6, 10.6, 15.6, DUR
cams = {"A": camera("SFCCam_A_Boulevard", 28.0, A), "B": camera("SFCCam_B_Bar", 22.0, A), "C": camera("SFCCam_C_Bridge", 32.0, C),
        "D": camera("SFCCam_D_Lab", 22.0, D)}
path = "/Game/SFCityLevel/Cinematics/LS_SFC_Showcase"
if eal.does_asset_exist(path): eal.delete_asset(path)
seq = at.create_asset("LS_SFC_Showcase", "/Game/SFCityLevel/Cinematics", unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
seq.set_display_rate(unreal.FrameRate(FPS, 1)); NF = int(round(DUR * FPS)); seq.set_playback_start(0); seq.set_playback_end(NF)
OT = [unreal.ObjectTypeQuery.ECC_WORLD_STATIC, unreal.ObjectTypeQuery.ECC_WORLD_DYNAMIC]
problems = []
def check(label, s, p, lab):
    if unreal.SystemLibrary.sphere_overlap_actors(w, p, 15.0, OT, None, list(demos.values())): problems.append(f"{label} {s:.1f}s inside geometry at {p}")
    q = P(lab, s) + V(0, 0, 40)
    r = unreal.SystemLibrary.line_trace_single(w, p, q, unreal.TraceTypeQuery.ECC_VISIBILITY, False, list(demos.values()), unreal.DrawDebugTrace.NONE, True)
    if r and r.to_tuple()[0]:
        h = r.to_tuple()[9]; problems.append(f"{label} {s:.1f}s view blocked by {h.get_actor_label() if h else '?'}")
def key_cam(k, s0, s1, pos_fn, tgt_fn, lab, step=0.2):
    cam = cams[k]; b = seq.add_possessable(cam); tr = b.add_track(unreal.MovieScene3DTransformTrack); sec = tr.add_section(); sec.set_range(0, NF)
    ch = sec.get_all_channels(); prev = None; t = max(0.0, s0 - 0.4)
    while t <= min(DUR, s1 + 0.4) + 1e-6:
        p = pos_fn(t); q = tgt_fn(t); r = unreal.MathLibrary.find_look_at_rotation(p, q); yaw = r.yaw
        if prev is not None:
            while yaw - prev > 180: yaw -= 360
            while yaw - prev < -180: yaw += 360
        prev = yaw; f = unreal.FrameNumber(int(round(t * FPS)))
        for c, v in zip(ch[:6], (p.x, p.y, p.z, 0.0, r.pitch, yaw)):
            kk = c.add_key(f, v)
            try: kk.set_interpolation_mode(unreal.RichCurveInterpMode.RCIM_CUBIC)
            except Exception: pass
        if s0 <= t <= s1 and abs(t * 5 - round(t * 5)) < 1e-6 and round(t * 5) % 5 == 0: check(k, t, p, lab)
        t += step
    return b
# A: crane down from 3.4 m over the street SW of the bar door onto her (the skyline behind her); ends low beside the door
posA = lambda s: lerp(V(-12950, -53780, 340), V(-12720, -53480, 160), ease(s, 0.0, 5.0))
tgtA = lambda s: Ps(A, s) + V(0, 0, 60 - 20 * ease(s, 0.0, 5.0))
# B: far (south-west) corner of the bar, slow push-in; she enters left, turns and walks toward the camera
posB = lambda s: lerp(V(-12070, -53690, 185), V(-12055, -53620, 180), ease(s, A1, B1))
tgtB = lambda s: Ps(A, s, 0.8) + V(0, 0, 25)
# C: offsets from her (x side, y along the bridge: she runs -Y, z above her capsule centre)
def offC(s):
    keys = [(10.2, 330, -560, 55), (11.8, 420, -330, 45), (13.0, 460, -40, 35), (14.4, 330, -380, 50), (15.8, 60, -540, 60)]
    for (t0, *a), (t1, *b) in zip(keys, keys[1:]):
        if s <= t1:
            u = ease(s, t0, t1); return V(*[a[j] + (b[j] - a[j]) * u for j in range(3)])
    return V(*keys[-1][1:])
def posC(s):
    p = Ps(C, s, 1.0); p.z = 150.0 + (p.y + 65400) * -0.0035     # (ignore the jump: steady height along the deck slope)
    return p + offC(s)
tgtC = lambda s: Ps(C, s, 0.8) + V(0, 0, 15)
# D: inside the lab from between the consoles on the south wall: the door left, the glowing relic behind where she stops;
#    slow push-in, aim from the doorway onto her
RELIC = V(-20848, -93040, 60)
posD = lambda s: lerp(V(-21065, -93665, 170), V(-20995, -93620, 158), ease(s, C1, D1))
tgtD = lambda s: lerp(lerp(V(-20515, -93400, 95), Ps(D, s, 0.8) + V(0, 0, 10), 0.3 + 0.6 * ease(s, 17.6, 19.2)), RELIC, 0.3 * ease(s, 18.8, 20.0))
SHOTS = [("A", A0, A1, posA, tgtA, A), ("B", A1, B1, posB, tgtB, A), ("C", B1, C1, posC, tgtC, C), ("D", C1, D1, posD, tgtD, D)]
cut = seq.add_track(unreal.MovieSceneCameraCutTrack)
for k, s0, s1, pf, tf, lab in SHOTS:
    b = key_cam(k, s0, s1, pf, tf, lab)
    cs = cut.add_section(); cs.set_range(int(round(s0 * FPS)), int(round(s1 * FPS)))
    cs.set_camera_binding_id(seq.get_binding_id(b) if hasattr(seq, "get_binding_id") else b.get_binding_id())
eal.save_loaded_asset(seq)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print("sequence", path, "frames", NF, "cuts at", [s[1] for s in SHOTS[1:]])
print("camera checks:", "ok" if not problems else "\n  " + "\n  ".join(problems))
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
