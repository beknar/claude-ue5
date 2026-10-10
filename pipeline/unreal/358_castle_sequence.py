"""LS_Castle_Showcase (26.3 s @ 30 fps) in castle_level_Cine, keyed from castle_demo_path.json (demo t = seq t - 1.5):
 A   0.0- 5.5   exterior, behind her at the bakery door: the door swings open, she walks in
 B   5.5- 9.5   bakery from the far corner: oven, kneading tables and bread shelves, she walks into the room
 C   9.5-13.3   tavern hall: sweeping dolly past the laid tables (plates, tankards, candles), loft and stairs
 D  13.3-17.5   tavern dormitory: slow push-in on three beds, their foot chests open left to right (356 TOUR)
 E  17.5-21.05  manor hall: the cupboard under the stairs and the chest by the wall open (356 TOUR)
 F 21.05-26.3   river: tracking from mid-stream as she sprints through the water, jumps, lands (splashes)"""
import json, math, bisect, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()
FPS, LEAD, RS = 30, 1.5, 8.1                       # RS = river shift in 353's DemoStepCastle
rows = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\terrain\castle_demo_path.json"))["rows"]
ts = [r[0] for r in rows]
def P(t):
    t = min(max(t, ts[0]), ts[-1]); i = min(max(1, bisect.bisect_left(ts, t)), len(ts) - 1)
    a, b = rows[i - 1], rows[i]; u = 0 if b[0] == a[0] else (t - a[0]) / (b[0] - a[0])
    return unreal.Vector(*[a[k] + (b[k] - a[k]) * u for k in (1, 2, 3)])
def Ps(t, lo, hi, w=0.8, n=9):          # smoothed inside one segment (no blending across the teleport)
    acc = unreal.Vector(0, 0, 0)
    for k in range(n):
        acc = acc + P(min(max(t - w / 2 + w * k / (n - 1), lo), hi)) * (1.0 / n)
    return acc
V = unreal.Vector
def ease(s, s0, s1):
    u = min(max((s - s0) / (s1 - s0), 0.0), 1.0); return u * u * (3 - 2 * u)
def lerp(a, b, u): return a + (b - a) * u
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert "castle_level_Cine" in w.get_path_name()
demo = next(a for a in eas.get_all_level_actors() if a.get_actor_label() == "FF2_Demo")
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith("CastleCam_"): eas.destroy_actor(a)
def camera(label, focal, interior=False, focus=None):
    c = eas.spawn_actor_from_class(unreal.CineCameraActor, V(0, 0, 0)); c.set_actor_label(label)
    cc = c.get_cine_camera_component()
    fb = cc.get_editor_property("filmback"); fb.sensor_width = 36.0; fb.sensor_height = 20.25; cc.set_editor_property("filmback", fb)
    cc.set_editor_property("current_focal_length", focal); cc.set_editor_property("current_aperture", 4.0 if focus is None else 5.6)
    fs = cc.get_editor_property("focus_settings")
    if focus is None:                     # follow her
        fs.focus_method = unreal.CameraFocusMethod.TRACKING
        tf = fs.get_editor_property("tracking_focus_settings"); tf.set_editor_property("actor_to_track", demo); tf.set_editor_property("relative_offset", V(0, 0, 40))
        fs.set_editor_property("tracking_focus_settings", tf); fs.set_editor_property("smooth_focus_changes", True); fs.set_editor_property("focus_smoothing_interp_speed", 6.0)
    else:                                 # camera-only furniture shots: fixed focus on the subject
        fs.focus_method = unreal.CameraFocusMethod.MANUAL; fs.set_editor_property("manual_focus_distance", focus)
    cc.set_editor_property("focus_settings", fs)
    if interior:
        pp = cc.get_editor_property("post_process_settings")
        for k, v in (("auto_exposure_min_brightness", -3.0), ("auto_exposure_max_brightness", 1.0), ("auto_exposure_bias", 0.6),
                     ("auto_exposure_speed_up", 25.0), ("auto_exposure_speed_down", 25.0)):
            pp.set_editor_property("override_" + k, True); pp.set_editor_property(k, v)
        cc.set_editor_property("post_process_settings", pp); cc.set_editor_property("post_process_blend_weight", 1.0)
    return c
A0, A1, B1, C1, D1, E1, DUR = 0.0, 5.5, 9.5, 13.3, 17.5, 21.05, 26.3
cams = {"A": camera("CastleCam_A_Door", 35.0), "B": camera("CastleCam_B_Bakery", 24.0, True),
        "C": camera("CastleCam_C_Tavern", 24.0, True, focus=900.0), "D": camera("CastleCam_D_Dormitory", 28.0, True, focus=520.0),
        "E": camera("CastleCam_E_Manor", 24.0, True, focus=480.0), "F": camera("CastleCam_F_River", 40.0)}
path = "/Game/Castle/Cinematics/LS_Castle_Showcase"
if eal.does_asset_exist(path): eal.delete_asset(path)
seq = at.create_asset("LS_Castle_Showcase", "/Game/Castle/Cinematics", unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
seq.set_display_rate(unreal.FrameRate(FPS, 1)); NF = int(round(DUR * FPS)); seq.set_playback_start(0); seq.set_playback_end(NF)
def key_cam(cam, s0, s1, pos_fn, tgt_fn, step=0.2):
    b = seq.add_possessable(cam); tr = b.add_track(unreal.MovieScene3DTransformTrack); sec = tr.add_section(); sec.set_range(0, NF)
    ch = sec.get_all_channels(); prev = None; t = max(0.0, s0 - 0.4)
    while t <= min(DUR, s1 + 0.4) + 1e-6:
        p = pos_fn(t); q = tgt_fn(t); r = unreal.MathLibrary.find_look_at_rotation(p, q); yaw = r.yaw
        if prev is not None:
            while yaw - prev > 180: yaw -= 360
            while yaw - prev < -180: yaw += 360
        prev = yaw; f = unreal.FrameNumber(int(round(t * FPS)))
        for c, v in zip(ch[:6], (p.x, p.y, p.z, 0.0, r.pitch, yaw)):
            k = c.add_key(f, v)
            try: k.set_interpolation_mode(unreal.RichCurveInterpMode.RCIM_CUBIC)
            except Exception: pass
        t += step
    return b
d = lambda s: s - LEAD                                               # sequence -> demo time
# A: behind/right of her outside the bakery door, slow push toward the doorway
posA = lambda s: V(1290 + 170 * ease(s, A0, A1), -1330 - 60 * ease(s, A0, A1), 178 - 10 * ease(s, A0, A1))
tgtA = lambda s: Ps(d(s), -1.5, 4.7) + V(30, 0, 25)
# B: open corner of the bakery, she walks diagonally in toward the camera; oven / tables / shelves behind her
posB = lambda s: V(2770 - 70 * ease(s, A1, B1), -860 - 20 * ease(s, A1, B1), 215)
tgtB = lambda s: Ps(d(s), 3.6, 9.0) * 0.8 + V(2300, -1450, 60) * 0.2 + V(0, 0, 15)
# C: tavern hall, dolly along the hall while panning across the tables
posC = lambda s: lerp(V(1300, 1950, 560), V(1300, 2700, 560), ease(s, B1, C1))
tgtC = lambda s: lerp(V(300, 2500, 400), V(300, 2150, 400), ease(s, B1, C1))
# D: dormitory, push in on the bed-foot chests
posD = lambda s: lerp(V(200, 2235, 805), V(190, 2380, 795), ease(s, C1, D1))
tgtD = lambda s: lerp(V(175, 2860, 700), V(170, 2850, 690), ease(s, C1, D1))
# E: manor hall, slow push toward the stair wall (cupboard left, chest right)
posE = lambda s: lerp(V(2640, 2380, 545), V(2770, 2380, 520), ease(s, D1, E1))
tgtE = lambda s: V(3200, 2380, 420)
# F: mid-stream, east of her and a little ahead, at hip height above the water
def posF(s):
    p = Ps(d(s), 11.55 + RS, 17.5 + RS, w=1.2)
    return V(p.x + 430, p.y + 170, 95 + 0.25 * max(0.0, p.z - 35))
tgtF = lambda s: Ps(d(s), 11.55 + RS, 17.5 + RS, w=0.6) + V(0, 25, 10)
SHOTS = [("A", A0, A1, posA, tgtA), ("B", A1, B1, posB, tgtB), ("C", B1, C1, posC, tgtC), ("D", C1, D1, posD, tgtD),
         ("E", D1, E1, posE, tgtE), ("F", E1, DUR, posF, tgtF)]
cut = seq.add_track(unreal.MovieSceneCameraCutTrack)
for k, s0, s1, pf, tf in SHOTS:
    b = key_cam(cams[k], s0, s1, pf, tf)
    cs = cut.add_section(); cs.set_range(int(round(s0 * FPS)), int(round(s1 * FPS)))
    cs.set_camera_binding_id(seq.get_binding_id(b) if hasattr(seq, "get_binding_id") else b.get_binding_id())
eal.save_loaded_asset(seq)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print("sequence", path, "frames", NF, "cuts at", [s[1] for s in SHOTS[1:]])
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
