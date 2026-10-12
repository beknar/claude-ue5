"""LS_IV_Showcase (30 s @ 30 fps) in random_isometric_village_level_Cine: the game's own isometric view (orthographic,
yaw 45, pitch -35.264: the camera never turns) as one continuous shot (a single camera cut: MRQ warms up at every cut,
which would stall her), keyed from cine_demo_path.json (784 recording of 783):
  0 -  3 s   starts wide over the market square (fountain, stalls, the church) and glides out to her house on the first
             ring street while closing in; she is inside (roof and camera-side walls cut away, the fire lit)
  3 - 13 s   she walks out of her door and runs out along the main road between the houses
 13 - 23 s   the view widens before the next section is generated ahead of her (about 15 s: the border curtain rises
             and the scan wave crosses the new part), she runs on to the border
 23 - 30 s   across the border into the new part of the village; the view widens once more at the end
The camera looks at a point that follows her smoothed position; only its position and its orthographic width are keyed."""
import json, math, bisect, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
at = unreal.AssetToolsHelpers.get_asset_tools(); V = unreal.Vector
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert w.get_path_name().startswith("/Game/RandomIsoVillage/Maps/random_isometric_village_level_Cine."), w.get_path_name()
FPS, DUR, DIST = 30, 30.0, 12000.0
R = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\random_isometric_village\cine_demo_path.json"))
rows = R["rows"]; ts = [r[0] for r in rows]
PITCH, YAW = R["iso_pitch"], R["iso_yaw"]
T_GEN = R["events"][0]["built_at"] if R["events"] else 15.0
def P(t):
    t = min(max(t, ts[0]), ts[-1]); i = min(max(1, bisect.bisect_left(ts, t)), len(ts) - 1)
    a, b = rows[i - 1], rows[i]; u = 0 if ts[i] == ts[i - 1] else (t - ts[i - 1]) / (ts[i] - ts[i - 1])
    return V(a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u, 0.0)
def Ps(t, wdt=0.9, n=13):
    acc = V(0, 0, 0)
    for k in range(n): acc = acc + P(t - wdt / 2 + wdt * k / (n - 1)) * (1.0 / n)
    return acc
smooth = lambda u: max(0.0, min(1.0, u)) ** 2 * (3 - 2 * max(0.0, min(1.0, u)))
GLIDE = 2.9                                  # from the square to her house
def focus(t):
    k = smooth((t - 0.25) / (GLIDE - 0.25))
    p = Ps(t)
    return V(p.x * k, p.y * k, 60.0)
# orthographic width (cm across the frame): time -> width, eased between the keys
WIDTH = [(0.0, 5600), (GLIDE, 1900), (4.4, 2000), (min(7.5, T_GEN - 3.4), 2600), (T_GEN - 2.6, 2700), (T_GEN - 0.2, 4700), (T_GEN + 4.5, 4700), (T_GEN + 8.0, 3000), (27.6, 3000), (30.0, 4400)]
WIDTH = [k for i, k in enumerate(WIDTH) if i == 0 or k[0] > max(q[0] for q in WIDTH[:i]) + 0.3]      # (keys in time order whatever T_GEN is)
def width(t):
    for (t0, w0), (t1, w1) in zip(WIDTH, WIDTH[1:]):
        if t <= t1: return w0 + (w1 - w0) * smooth((t - t0) / (t1 - t0))
    return WIDTH[-1][1]
D = unreal.Rotator(roll=0, pitch=PITCH, yaw=YAW).get_forward_vector()
# ---- camera + sequence
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith("IVCam_"): eas.destroy_actor(a)
c = eas.spawn_actor_from_class(unreal.CineCameraActor, V(0, 0, 0), unreal.Rotator(roll=0, pitch=PITCH, yaw=YAW)); c.set_actor_label("IVCam_Oner"); c.set_folder_path("IsoVillage/Cine")
cc = c.get_cine_camera_component()
cc.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC); cc.set_editor_property("ortho_width", float(WIDTH[0][1]))
cc.set_editor_property("constrain_aspect_ratio", False)
fs = cc.get_editor_property("focus_settings"); fs.focus_method = unreal.CameraFocusMethod.DISABLE; cc.set_editor_property("focus_settings", fs)
path = "/Game/RandomIsoVillage/Cinematics/LS_IV_Showcase"
if eal.does_asset_exist(path): eal.delete_asset(path)
seq = at.create_asset("LS_IV_Showcase", "/Game/RandomIsoVillage/Cinematics", unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
seq.set_display_rate(unreal.FrameRate(FPS, 1)); NF = int(round(DUR * FPS)); seq.set_playback_start(0); seq.set_playback_end(NF)
b = seq.add_possessable(c); tr = b.add_track(unreal.MovieScene3DTransformTrack); sec = tr.add_section(); sec.set_range(0, NF)
ch = sec.get_all_channels()
for k in range(int(DUR * 10) + 1):
    t = k * 0.1; p = focus(t) - D * DIST
    for chn, v in zip(ch[:6], (p.x, p.y, p.z, 0.0, PITCH, YAW)):
        kk = chn.add_key(unreal.FrameNumber(int(round(t * FPS))), v)
        try: kk.set_interpolation_mode(unreal.RichCurveInterpMode.RCIM_CUBIC)
        except Exception: pass
# the zoom: the camera component's orthographic width
cb = seq.add_possessable(cc)
try: cb.set_parent(b)
except Exception as e: print("  (component binding parent:", e, ")")
wt = cb.add_track(unreal.MovieSceneFloatTrack); wt.set_property_name_and_path("OrthoWidth", "OrthoWidth")
ws = wt.add_section(); ws.set_range(0, NF); wch = ws.get_all_channels()[0]
for k in range(int(DUR * 10) + 1):
    t = k * 0.1; kk = wch.add_key(unreal.FrameNumber(int(round(t * FPS))), float(width(t)))
    try: kk.set_interpolation_mode(unreal.RichCurveInterpMode.RCIM_CUBIC)
    except Exception: pass
cut = seq.add_track(unreal.MovieSceneCameraCutTrack); cs = cut.add_section(); cs.set_range(0, NF)
cs.set_camera_binding_id(seq.get_binding_id(b) if hasattr(seq, "get_binding_id") else b.get_binding_id())
eal.save_loaded_asset(seq)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print("sequence", path, "frames", NF, "| generation at %.2f s" % T_GEN)
for t in (0, 1.5, 3, 5, 10, T_GEN, 20, 23.1, 27, 30):
    h = Ps(t); f = focus(t); print(f"  {t:5.2f}s her ({h.x:.0f},{h.y:.0f}) focus ({f.x:.0f},{f.y:.0f}) width {width(t):.0f}")
json.dump({"width": [[round(k * 0.1, 1), round(width(k * 0.1))] for k in range(int(DUR * 10) + 1)],
           "focus": [[round(k * 0.1, 1), round(focus(k * 0.1).x), round(focus(k * 0.1).y)] for k in range(int(DUR * 10) + 1)], "t_gen": T_GEN},
          open(r"E:\code\claude-ue5\claude_ue5\SourceArt\random_isometric_village\cine_camera.json", "w"))
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
