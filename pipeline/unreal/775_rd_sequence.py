"""LS_RD_Showcase (20 s @ 30 fps) in random_dungeon_level_Cine: one continuous camera move (a single camera cut: MRQ
warms up at every cut, which would stall her), keyed from cine_demo_path.json (774 recording of 773):
  0 -  4 s   chapel: three-quarter front view, swinging round behind her as the chapel door opens ahead
  4 - 10 s   low chase through the doorway, the hallway and into the prison cells (camera rises inside the prison)
 10 - 15 s   the prison's far door opens and the next section generates beyond it (border curtain rising, ~11.3 s);
             back down to doorway height, through the hallway and the glowing border
 15 - 20 s   into the new section's crypt (camera through its doorway at ~17 s), then craning up and to the side
The camera sits at (azimuth, distance, z) from her smoothed position (Catmull-Rom through KEYS) and looks at a point F
ahead of her along +X at height tz. Checks every 0.02 s: through each doorway (1.4 m arch) the camera is within 45 cm of
the lane and below 1.95 m; in hallways within 1 m of the lane and below the 4 m ceiling; inside geometry (start section)."""
import json, math, bisect, statistics, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
at = unreal.AssetToolsHelpers.get_asset_tools(); V = unreal.Vector
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert w.get_path_name().startswith("/Game/RandomDungeon/Maps/random_dungeon_level_Cine."), w.get_path_name()
FPS, DUR, RUN, X0, GO, LANE = 30, 20.0, 376.7, 7300.0, 0.3, 7350.0
R = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon\cine_demo_path.json"))
rows = R["rows"]; ts = [r[0] for r in rows]
LAG = statistics.median(r[0] - (GO + (r[1] - X0) / RUN) for r in rows if r[5] > 360 and 8000 < r[1] < 12000)
def P(t):
    t = min(max(t + LAG, ts[0]), ts[-1]); i = min(max(1, bisect.bisect_left(ts, t)), len(ts) - 1)
    a, b = rows[i - 1], rows[i]; u = 0 if ts[i] == ts[i - 1] else (t - ts[i - 1]) / (ts[i] - ts[i - 1])
    return V(*[a[j] + (b[j] - a[j]) * u for j in (1, 2, 3)])
def Ps(t, wdt=0.6, n=9):
    acc = V(0, 0, 0)
    for k in range(n): acc = acc + P(t - wdt / 2 + wdt * k / (n - 1)) * (1.0 / n)
    return acc
# t, azimuth (deg, from her to the camera; 180 = behind), distance, camera z (world), look-ahead F, look z
KEYS = [(0.0, 25, 420, 190, -60, 130), (1.2, 40, 430, 200, 0, 120), (2.6, 100, 430, 215, 300, 120), (3.8, 176, 400, 182, 900, 120),
        (4.6, 180, 380, 172, 1500, 110), (8.4, 180, 390, 172, 1500, 110), (10.0, 180, 450, 290, 2000, 100), (12.0, 180, 430, 250, 2500, 120),
        (13.2, 180, 400, 172, 2500, 120), (17.3, 180, 400, 172, 1500, 115), (18.6, 196, 430, 285, 1200, 100), (20.0, 205, 470, 340, 900, 90)]
def spline(t):
    k = KEYS; i = max(0, min(len(k) - 2, bisect.bisect_right([q[0] for q in k], t) - 1))
    p0, p1, p2, p3 = k[max(i - 1, 0)], k[i], k[i + 1], k[min(i + 2, len(k) - 1)]
    u = min(max((t - p1[0]) / (p2[0] - p1[0]), 0.0), 1.0)
    return [0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * u + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * u * u + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * u ** 3)
            for j in range(1, 6)]
def cam(t):
    p = Ps(t); az, d, z, F, tz = spline(t); ca, sa = math.cos(math.radians(az)), math.sin(math.radians(az))
    return V(p.x + d * ca, p.y + d * sa, z), V(p.x + F, p.y, tz)
# ---- clearance checks (doorways on the lane, hallway segments)
DOORS = [8700, 9900, 12000, 13200, 15900]
HALLS = [(8700, 9900), (12000, 13200), (15900, 16500)]
problems = []
for k in range(int(DUR * 50) + 1):
    t = k * 0.02; c, _ = cam(t)
    for dx in DOORS:
        if abs(c.x - dx) < 70 and (abs(c.y - LANE) > 45 or c.z > 195): problems.append(f"{t:.2f}s doorway {dx}: cam y {c.y - LANE:+.0f} z {c.z:.0f}")
    for a, b in HALLS:
        if a < c.x < b and (abs(c.y - LANE) > 100 or c.z > 370): problems.append(f"{t:.2f}s hallway {a}-{b}: cam y {c.y - LANE:+.0f} z {c.z:.0f}")
demo = next(a for a in eas.get_all_level_actors() if a.get_actor_label() == "Demo_RD_Fem5")
OT = [unreal.ObjectTypeQuery.ECC_WORLD_STATIC, unreal.ObjectTypeQuery.ECC_WORLD_DYNAMIC]
for k in range(int(DUR * 5) + 1):
    t = k * 0.2; c, _ = cam(t)
    # (doorways: the editor copy has its doors shut; the clearance rule above covers them)
    if c.x < 12550 and min(abs(c.x - dx) for dx in DOORS) > 80 and unreal.SystemLibrary.sphere_overlap_actors(w, c, 25.0, OT, None, [demo]): problems.append(f"{t:.1f}s camera inside geometry at ({c.x:.0f},{c.y:.0f},{c.z:.0f})")
# ---- camera + sequence
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith("RDCam_"): eas.destroy_actor(a)
c = eas.spawn_actor_from_class(unreal.CineCameraActor, V(0, 0, 0)); c.set_actor_label("RDCam_Oner"); c.set_folder_path("RandomDungeon/Cine")
cc = c.get_cine_camera_component()
fb = cc.get_editor_property("filmback"); fb.sensor_width = 36.0; fb.sensor_height = 20.25; cc.set_editor_property("filmback", fb)
cc.set_editor_property("current_focal_length", 20.0); cc.set_editor_property("current_aperture", 4.0)
fs = cc.get_editor_property("focus_settings"); fs.focus_method = unreal.CameraFocusMethod.TRACKING
tf = fs.get_editor_property("tracking_focus_settings"); tf.set_editor_property("actor_to_track", demo); tf.set_editor_property("relative_offset", V(0, 0, 40))
fs.set_editor_property("tracking_focus_settings", tf); fs.set_editor_property("smooth_focus_changes", True); fs.set_editor_property("focus_smoothing_interp_speed", 6.0)
cc.set_editor_property("focus_settings", fs)
path = "/Game/RandomDungeon/Cinematics/LS_RD_Showcase"
if eal.does_asset_exist(path): eal.delete_asset(path)
seq = at.create_asset("LS_RD_Showcase", "/Game/RandomDungeon/Cinematics", unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
seq.set_display_rate(unreal.FrameRate(FPS, 1)); NF = int(round(DUR * FPS)); seq.set_playback_start(0); seq.set_playback_end(NF)
b = seq.add_possessable(c); tr = b.add_track(unreal.MovieScene3DTransformTrack); sec = tr.add_section(); sec.set_range(0, NF)
ch = sec.get_all_channels(); prev = None
for k in range(int(DUR * 10) + 1):
    t = k * 0.1; p, q = cam(t); r = unreal.MathLibrary.find_look_at_rotation(p, q); yaw = r.yaw
    if prev is not None:
        while yaw - prev > 180: yaw -= 360
        while yaw - prev < -180: yaw += 360
    prev = yaw
    for chn, v in zip(ch[:6], (p.x, p.y, p.z, 0.0, r.pitch, yaw)):
        kk = chn.add_key(unreal.FrameNumber(int(round(t * FPS))), v)
        try: kk.set_interpolation_mode(unreal.RichCurveInterpMode.RCIM_CUBIC)
        except Exception: pass
cut = seq.add_track(unreal.MovieSceneCameraCutTrack); cs = cut.add_section(); cs.set_range(0, NF)
cs.set_camera_binding_id(seq.get_binding_id(b) if hasattr(seq, "get_binding_id") else b.get_binding_id())
eal.save_loaded_asset(seq)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print("sequence", path, "frames", NF, "| LAG %.2f s" % LAG)
for t in (0, 2.6, 4, 8, 10, 11.3, 13, 15, 17, 20):
    p, _ = cam(t); h = Ps(t); print(f"  {t:4.1f}s her ({h.x:.0f},{h.y:.0f}) cam ({p.x:.0f},{p.y:.0f},{p.z:.0f})")
print("camera checks:", "ok" if not problems else f"{len(problems)} problems\n  " + "\n  ".join(problems[:25]))
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
