"""LS_RL_Showcase (20 s @ 30 fps) in random_level_Cine: one continuous camera move (a single camera cut, so Movie Render
Queue warms up once and her run never pauses), keyed from cine_demo_path.json (755 recording of 754):
  0 -  5 s  chase behind her down the y = 200 m street, booming back and up to 15 m and looking far ahead: the cells
            beyond the east edge of town generate (about 1.1 s; curtain across the street end, scan waves)
  5 -  8 s  orbit round the crossroads as she turns north: the cells north of town generate (about 6.1 s)
  8 - 11.5  descend into a low chase up the x = 200 m street toward the new cells
 11.5 - 15.5  low three-quarter chase from behind her right
 15.5 - 20  crane up behind her as she crosses the north edge street into the new cell (0, 1)
The camera sits at (azimuth, distance, height) from her (smoothed) position, Catmull-Rom through KEYS, and looks over
her at a point F ahead (tz above her capsule centre). Her positions are the recording shifted by LAG (Simulate starts
her late after a start-up hitch; MRQ warms up first), estimated from the straight east leg. Checks every 0.2 s that the
camera is not inside geometry and sees her (all camera positions are over the start square, which exists in the editor)."""
import json, math, bisect, statistics, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
at = unreal.AssetToolsHelpers.get_asset_tools(); V = unreal.Vector
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert w.get_path_name().startswith("/Game/RandomLevel/Maps/random_level_Cine."), w.get_path_name()
FPS, DUR, RUN, X0, GO = 30, 20.0, 376.7, 17700.0, 0.3       # (754: she leaves (X0, 200 m) at GO s)
R = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\random_level\cine_demo_path.json"))
rows = R["rows"]; ts = [r[0] for r in rows]
LAG = statistics.median(r[0] - (GO + (r[1] - X0) / RUN) for r in rows if r[5] > 360 and 18000 < r[1] < 19500)
def P(t):
    t = min(max(t + LAG, ts[0]), ts[-1]); i = min(max(1, bisect.bisect_left(ts, t)), len(ts) - 1)
    a, b = rows[i - 1], rows[i]; u = 0 if ts[i] == ts[i - 1] else (t - ts[i - 1]) / (ts[i] - ts[i - 1])
    return V(*[a[j] + (b[j] - a[j]) * u for j in (1, 2, 3)])
def Ps(t, wdt=0.8, n=11):
    acc = V(0, 0, 0)
    for k in range(n): acc = acc + P(t - wdt / 2 + wdt * k / (n - 1)) * (1.0 / n)
    return acc
# t: azimuth (deg, direction from her to the camera), distance, height over her capsule centre, look-ahead F, tz
KEYS = [(0.0, 175, 650, 120, 400, 30), (0.9, 175, 750, 160, 1200, 0), (3.0, 174, 1900, 850, 6000, -500),
        (5.0, 180, 2100, 1150, 5500, -500), (8.0, 262, 2200, 1300, 5500, -500), (11.5, 280, 800, 200, 2500, 0),
        (15.5, 298, 650, 160, 400, 30), (19.0, 276, 1150, 700, 3000, -400), (20.0, 274, 1250, 780, 3200, -400)]
def spline(t):
    """Catmull-Rom through KEYS (end keys repeated)"""
    k = KEYS; i = max(0, min(len(k) - 2, bisect.bisect_right([q[0] for q in k], t) - 1))
    p0, p1, p2, p3 = k[max(i - 1, 0)], k[i], k[i + 1], k[min(i + 2, len(k) - 1)]
    u = min(max((t - p1[0]) / (p2[0] - p1[0]), 0.0), 1.0)
    out = []
    for j in range(1, 6):
        a, b, c, d = p0[j], p1[j], p2[j], p3[j]
        out.append(0.5 * ((2 * b) + (-a + c) * u + (2 * a - 5 * b + 4 * c - d) * u * u + (-a + 3 * b - 3 * c + d) * u ** 3))
    return out
def cam(t):
    p = Ps(t); az, b, h, F, tz = spline(t); ca, sa = math.cos(math.radians(az)), math.sin(math.radians(az))
    return p + V(b * ca, b * sa, h), p + V(-ca * F, -sa * F, tz)
demo = next(a for a in eas.get_all_level_actors() if a.get_actor_label() == "Demo_RL_Fem5")
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith("RLCam_"): eas.destroy_actor(a)
# set dressing (this copy only): start-square trees within 35 m of the camera and 24 deg of its view direction
gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RTTownGenerator))
tree_meshes = {it.mesh.get_path_name() for it in gen.get_editor_property("trees") if it.mesh}
removed = []
for cell in [a for a in eas.get_all_level_actors() if isinstance(a, unreal.RTCell)]:
    for h in cell.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent):
        sm = h.get_editor_property("static_mesh")
        if not sm or sm.get_path_name() not in tree_meshes: continue
        drop = set()
        for i in range(h.get_instance_count()):
            l = h.get_instance_transform(i, True).translation; pt = (l.x, l.y)
            for k in range(int(DUR * 4) + 1):
                p, q = cam(k * 0.25)
                dv = math.atan2(q.y - p.y, q.x - p.x); dt_ = math.atan2(pt[1] - p.y, pt[0] - p.x)
                ang = abs((math.degrees(dt_ - dv) + 180) % 360 - 180); dist = math.hypot(pt[0] - p.x, pt[1] - p.y)
                if ang < 24 and dist < 3500: drop.add(i); break
        for i in sorted(drop, reverse=True):
            l = h.get_instance_transform(i, True).translation; removed.append(f"{h.get_editor_property('static_mesh').get_name()} ({l.x:.0f},{l.y:.0f})")
            h.remove_instance(i)
        if drop: cell.modify()
print("trees removed from the camera's sight line:", len(removed), removed)
c = eas.spawn_actor_from_class(unreal.CineCameraActor, V(0, 0, 0)); c.set_actor_label("RLCam_Oner"); c.set_folder_path("RandomTown/Cine")
cc = c.get_cine_camera_component()
fb = cc.get_editor_property("filmback"); fb.sensor_width = 36.0; fb.sensor_height = 20.25; cc.set_editor_property("filmback", fb)
cc.set_editor_property("current_focal_length", 24.0); cc.set_editor_property("current_aperture", 5.6)
fs = cc.get_editor_property("focus_settings"); fs.focus_method = unreal.CameraFocusMethod.TRACKING
tf = fs.get_editor_property("tracking_focus_settings"); tf.set_editor_property("actor_to_track", demo); tf.set_editor_property("relative_offset", V(0, 0, 40))
fs.set_editor_property("tracking_focus_settings", tf); fs.set_editor_property("smooth_focus_changes", True); fs.set_editor_property("focus_smoothing_interp_speed", 6.0)
cc.set_editor_property("focus_settings", fs)
path = "/Game/RandomLevel/Cinematics/LS_RL_Showcase"
if eal.does_asset_exist(path): eal.delete_asset(path)
seq = at.create_asset("LS_RL_Showcase", "/Game/RandomLevel/Cinematics", unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
seq.set_display_rate(unreal.FrameRate(FPS, 1)); NF = int(round(DUR * FPS)); seq.set_playback_start(0); seq.set_playback_end(NF)
OT = [unreal.ObjectTypeQuery.ECC_WORLD_STATIC, unreal.ObjectTypeQuery.ECC_WORLD_DYNAMIC]
problems = []
b = seq.add_possessable(c); tr = b.add_track(unreal.MovieScene3DTransformTrack); sec = tr.add_section(); sec.set_range(0, NF)
ch = sec.get_all_channels(); prev = None
for k in range(int(DUR * 5) + 1):
    t = k * 0.2; p, q = cam(t); r = unreal.MathLibrary.find_look_at_rotation(p, q); yaw = r.yaw
    if prev is not None:
        while yaw - prev > 180: yaw -= 360
        while yaw - prev < -180: yaw += 360
    prev = yaw
    for chn, v in zip(ch[:6], (p.x, p.y, p.z, 0.0, r.pitch, yaw)):
        kk = chn.add_key(unreal.FrameNumber(int(round(t * FPS))), v)
        try: kk.set_interpolation_mode(unreal.RichCurveInterpMode.RCIM_CUBIC)
        except Exception: pass
    if unreal.SystemLibrary.sphere_overlap_actors(w, p, 30.0, OT, None, [demo]): problems.append(f"{t:.1f}s camera inside geometry at {p}")
    hit = unreal.SystemLibrary.line_trace_single(w, p, P(t) + V(0, 0, 40), unreal.TraceTypeQuery.ECC_VISIBILITY, False, [demo], unreal.DrawDebugTrace.NONE, True)
    if hit and hit.to_tuple()[0]:
        h = hit.to_tuple()[9]; problems.append(f"{t:.1f}s view blocked by {h.get_actor_label() if h else '?'}")
cut = seq.add_track(unreal.MovieSceneCameraCutTrack); cs = cut.add_section(); cs.set_range(0, NF)
cs.set_camera_binding_id(seq.get_binding_id(b) if hasattr(seq, "get_binding_id") else b.get_binding_id())
eal.save_loaded_asset(seq)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print("sequence", path, "frames", NF, "| LAG %.2f s" % LAG)
for t in (0, 1.1, 3, 5, 6.1, 8, 12, 16, 19, 20):
    p, q = cam(t); h = Ps(t); print(f"  {t:4.1f}s her ({h.x:.0f},{h.y:.0f}) cam ({p.x:.0f},{p.y:.0f},{p.z:.0f})")
print("camera checks:", "ok" if not problems else "\n  " + "\n  ".join(problems))
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
