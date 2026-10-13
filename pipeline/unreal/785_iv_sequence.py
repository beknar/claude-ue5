"""LS_IV_Showcase (30 s @ 30 fps) in random_isometric_village_level_Cine: the game's own isometric view (orthographic,
pitch -35.264, yaw 45 plus the view turns of Q / E) as one continuous shot (a single camera cut: MRQ warms up at every
cut, which would stall her), keyed from cine_demo_path.json (784 recording of 783) and cine_route.json (783):
  0 -  3 s   starts wide over the market square (fountain, stalls, the church, villagers) and glides out to her house on
             the first ring street while closing in; she is inside (roof and camera-side walls cut away, the fire lit)
  3 -  4 s   Q: the view turns 45 degrees to the left; the cutaway follows (other walls come off)
  4 - 11 s   she walks out of her door and runs out along the main road between the houses; E turns the view back
 11 - 19 s   the view widens before the next section is generated ahead of her (the border curtain rises and the scan
             wave crosses the new part); she runs on across the border
 19 - 25 s   she stops a few metres into the new part: the big map (drawn by the reel overlay, as M in play); E turns
             the view, and the map with it
 25 - 30 s   on into the new part of the village, seen along the road; the view widens once more at the end
The camera looks at a point that follows her smoothed position; its position, its yaw and its orthographic width are
keyed every frame, and so is the generator's ViewYawOffset (the cutaway and the maps use it, as the player controller
sets it in play). A turn takes 0.45 s here, eased (0.19 s at constant speed in play).
Writes SourceArt/random_isometric_village/cine_camera.json (width, focus, view yaw offset, turns, map window) for the
reel overlay."""
import json, math, bisect, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
at = unreal.AssetToolsHelpers.get_asset_tools(); V = unreal.Vector
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert w.get_path_name().startswith("/Game/RandomIsoVillage/Maps/random_isometric_village_level_Cine."), w.get_path_name()
FPS, DUR, DIST = 30, 30.0, 12000.0
SRC = "E:\\code\\claude-ue5\\claude_ue5\\SourceArt\\random_isometric_village\\"
R = json.load(open(SRC + "cine_demo_path.json")); RT = json.load(open(SRC + "cine_route.json"))
rows = R["rows"]; ts = [r[0] for r in rows]
PITCH, YAW = R["iso_pitch"], R["iso_yaw"]
HOLD, T_TRIG, (MAP0, MAP1) = RT["hold"], RT["trigger"], RT["map"]
T_GEN = R["events"][0]["built_at"] if R["events"] else T_TRIG + 1.0
def P(t):
    t = min(max(t, ts[0]), ts[-1]); i = min(max(1, bisect.bisect_left(ts, t)), len(ts) - 1)
    a, b = rows[i - 1], rows[i]; u = 0 if ts[i] == ts[i - 1] else (t - ts[i - 1]) / (ts[i] - ts[i - 1])
    return V(a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u, 0.0)
def Ps(t, wdt=0.9, n=13):
    acc = V(0, 0, 0)
    for k in range(n): acc = acc + P(t - wdt / 2 + wdt * k / (n - 1)) * (1.0 / n)
    return acc
smooth = lambda u: max(0.0, min(1.0, u)) ** 2 * (3 - 2 * max(0.0, min(1.0, u)))
# she stands while the map is open (in play she cannot move then)
moving = [r for r in rows if MAP0 <= r[0] <= MAP1 and r[5] > 8]
assert not moving, f"she moves while the map is open: {moving[0]}"
GLIDE = 2.7                                  # from the square to her house
def focus(t):
    k = smooth((t - 0.25) / (GLIDE - 0.25))
    p = Ps(t)
    return V(p.x * k, p.y * k, 60.0)
# the view turns: (time, steps of 45 degrees; +1 = Q, the camera yaw grows)
STEP, TURN = 45.0, 0.45
TURNS = [(3.0, 1), (HOLD + 3.3, -1), (MAP0 + 1.9, -1)]
def yaw_off(t): return sum(n * STEP * smooth((t - t0) / TURN) for t0, n in TURNS)
# orthographic width (cm across the frame): time -> width, eased between the keys
WIDTH = [(0.0, 5600), (GLIDE, 1900), (HOLD + 1.8, 2000), (T_TRIG - 2.5, 2500), (T_TRIG - 0.1, 4700), (T_TRIG + 5.2, 4700), (MAP0 - 0.6, 3200), (MAP1 + 0.4, 3200), (27.4, 3300), (30.0, 4800)]
assert all(b[0] > a[0] + 0.3 for a, b in zip(WIDTH, WIDTH[1:])), WIDTH
def width(t):
    for (t0, w0), (t1, w1) in zip(WIDTH, WIDTH[1:]):
        if t <= t1: return w0 + (w1 - w0) * smooth((t - t0) / (t1 - t0))
    return WIDTH[-1][1]
# ---- camera + sequence
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith("IVCam_"): eas.destroy_actor(a)
gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.IVVillageGenerator))
c = eas.spawn_actor_from_class(unreal.CineCameraActor, V(0, 0, 0), unreal.Rotator(roll=0, pitch=PITCH, yaw=YAW)); c.set_actor_label("IVCam_Oner"); c.set_folder_path("IsoVillage/Cine")
cc = c.get_cine_camera_component()
cc.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC); cc.set_editor_property("ortho_width", float(WIDTH[0][1]))
cc.set_editor_property("constrain_aspect_ratio", False)
fs = cc.get_editor_property("focus_settings"); fs.focus_method = unreal.CameraFocusMethod.DISABLE; cc.set_editor_property("focus_settings", fs)
path = "/Game/RandomIsoVillage/Cinematics/LS_IV_Showcase"
if eal.does_asset_exist(path): eal.delete_asset(path)
seq = at.create_asset("LS_IV_Showcase", "/Game/RandomIsoVillage/Cinematics", unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
seq.set_display_rate(unreal.FrameRate(FPS, 1)); NF = int(round(DUR * FPS)); seq.set_playback_start(0); seq.set_playback_end(NF)
def keys(chn, f):
    for k in range(NF + 1):
        kk = chn.add_key(unreal.FrameNumber(k), float(f(k / FPS)))
        try: kk.set_interpolation_mode(unreal.RichCurveInterpMode.RCIM_LINEAR)
        except Exception: pass
def cam(t):
    d = unreal.Rotator(roll=0, pitch=PITCH, yaw=YAW + yaw_off(t)).get_forward_vector()
    return focus(t) - d * DIST
b = seq.add_possessable(c); tr = b.add_track(unreal.MovieScene3DTransformTrack); sec = tr.add_section(); sec.set_range(0, NF)
ch = sec.get_all_channels()
for chn, f in zip(ch[:6], (lambda t: cam(t).x, lambda t: cam(t).y, lambda t: cam(t).z, lambda t: 0.0, lambda t: PITCH, lambda t: YAW + yaw_off(t))): keys(chn, f)
# the zoom: the camera component's orthographic width
cb = seq.add_possessable(cc)
try: cb.set_parent(b)
except Exception as e: print("  (component binding parent:", e, ")")
wt = cb.add_track(unreal.MovieSceneFloatTrack); wt.set_property_name_and_path("OrthoWidth", "OrthoWidth")
ws = wt.add_section(); ws.set_range(0, NF); keys(ws.get_all_channels()[0], width)
# the generator's view yaw (SetViewYawOffset): which walls are cut away
gb = seq.add_possessable(gen)
gt = gb.add_track(unreal.MovieSceneFloatTrack); gt.set_property_name_and_path("ViewYawOffset", "ViewYawOffset")
gs = gt.add_section(); gs.set_range(0, NF); keys(gs.get_all_channels()[0], yaw_off)
cut = seq.add_track(unreal.MovieSceneCameraCutTrack); cs = cut.add_section(); cs.set_range(0, NF)
cs.set_camera_binding_id(seq.get_binding_id(b) if hasattr(seq, "get_binding_id") else b.get_binding_id())
eal.save_loaded_asset(seq)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print("sequence", path, "frames", NF, "| next section triggered at %.2f s (built %.2f s in Simulate) | map %.2f-%.2f s | turns %s" % (T_TRIG, T_GEN, MAP0, MAP1, TURNS))
for t in (0, 1.5, 3, 3.5, 5, 8, T_TRIG, T_GEN, MAP0, MAP1, 27, 30):
    h = Ps(t); f = focus(t); print(f"  {t:5.2f}s her ({h.x:.0f},{h.y:.0f}) focus ({f.x:.0f},{f.y:.0f}) width {width(t):.0f} view {yaw_off(t):+.0f}")
json.dump({"width": [round(width(k / FPS)) for k in range(NF + 1)], "focus": [[round(focus(k / FPS).x), round(focus(k / FPS).y)] for k in range(NF + 1)],
           "yaw_off": [round(yaw_off(k / FPS), 2) for k in range(NF + 1)], "fps": FPS, "turns": TURNS, "turn_time": TURN, "map": [MAP0, MAP1], "t_trigger": T_TRIG, "hold": HOLD},
          open(SRC + "cine_camera.json", "w"))
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
