"""LS_JRPG_<CH>_Showcase (20 s @ 30 fps) in L_Meshy_Meadow_Cine (generalised 189_soldier_sequence.py): a tracking cine camera keyed
from the recorded demo path (<ch>_demo_path.json, 640 routine) - front 3/4 on the idle, side tracking through walk / run / jump,
then a swing round to a front-on hero angle as she slows and settles back into her idle.  Args: CH [half_height]"""
import json, math, bisect, sys, unreal
CH = sys.argv[1] if len(sys.argv) > 1 else "Fem5"; HALF = float(sys.argv[2]) if len(sys.argv) > 2 else 82.5
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
eal = unreal.EditorAssetLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()
FPS, DUR = 30, 20.0
LEAD = 1.5          # demo routine starts 1.5 s into the sequence (BP DemoStartTime) so the character has settled
rows = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\terrain" + "\\" + CH.lower() + "_demo_path.json"))
ts = [r[0] for r in rows]
def P(t):
    t = min(max(t, ts[0]), ts[-1]); i = max(1, bisect.bisect_left(ts, t)); i = min(i, len(ts) - 1)
    a, b = rows[i - 1], rows[i]; u = 0 if b[0] == a[0] else (t - a[0]) / (b[0] - a[0])
    return [a[k] + (b[k] - a[k]) * u for k in (1, 2, 3)]
def Ps(t, w=0.6, n=9):          # smoothed path (box filter) for a steady camera
    s = [0, 0, 0]
    for k in range(n):
        p = P(t - w / 2 + w * k / (n - 1)); s = [s[j] + p[j] / n for j in range(3)]
    return s
# (time, forward offset, side offset (+Y = sun side), height above ground)
KEYS = [(-1.5, 420, 300, 145), (2.5, 380, 340, 145), (4.5, 280, 420, 135), (7.0, 200, 480, 125),
        (9.0, 150, 540, 118), (10.2, 110, 560, 105), (11.4, 140, 530, 120), (12.6, 230, 460, 132),
        (14.0, 320, 330, 138), (15.6, 360, 190, 138), (17.0, 360, 80, 140), (18.5, 330, 30, 142)]
def off(t):
    for (t0, *a), (t1, *b) in zip(KEYS, KEYS[1:]):
        if t <= t1:
            u = max(0.0, (t - t0) / (t1 - t0)); u = u * u * (3 - 2 * u)
            return [a[j] + (b[j] - a[j]) * u for j in range(3)]
    return KEYS[-1][1:]

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
def ground(x, y):
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 20000), unreal.Vector(x, y, -20000),
                                                 unreal.TraceTypeQuery.ECC_VISIBILITY, True, [], unreal.DrawDebugTrace.NONE, True)
    t = hit.to_tuple() if hit else None
    return t[4].z if t and (t[0] or t[1]) else 0.0

for a in eas.get_all_level_actors():
    if a.get_actor_label() in ("Cam_Track",): eas.destroy_actor(a)
demo = [a for a in eas.get_all_level_actors() if a.get_actor_label() == "Fig4_Demo"][0]
assert "Fem" in demo.get_class().get_name(), demo.get_class().get_name()
cam = eas.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(300, 400, 150))
cam.set_actor_label("Cam_Track")
cc = cam.get_cine_camera_component()
fb = cc.get_editor_property("filmback"); fb.sensor_width = 36.0; fb.sensor_height = 20.25; cc.set_editor_property("filmback", fb)
cc.set_editor_property("current_focal_length", 45.0); cc.set_editor_property("current_aperture", 2.8)
fs = cc.get_editor_property("focus_settings")
fs.focus_method = unreal.CameraFocusMethod.TRACKING
tf = fs.get_editor_property("tracking_focus_settings")
tf.set_editor_property("actor_to_track", demo); tf.set_editor_property("relative_offset", unreal.Vector(0, 0, 50))
fs.set_editor_property("tracking_focus_settings", tf)
fs.set_editor_property("smooth_focus_changes", True); fs.set_editor_property("focus_smoothing_interp_speed", 6.0)
cc.set_editor_property("focus_settings", fs)

path = f"/Game/JRPG/Cinematics/LS_JRPG_{CH}_Showcase"
if eal.does_asset_exist(path):
    seq = unreal.load_asset(path)
    for bd in seq.get_bindings(): bd.remove()
    for trk in (seq.get_tracks() if hasattr(seq, "get_tracks") else seq.get_master_tracks()):
        seq.remove_track(trk) if hasattr(seq, "remove_track") else seq.remove_master_track(trk)
else:
    seq = at.create_asset(f"LS_JRPG_{CH}_Showcase", "/Game/JRPG/Cinematics", unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
seq.set_display_rate(unreal.FrameRate(FPS, 1))
seq.set_tick_resolution(unreal.FrameRate(24000, 1))   # keep the default (a custom 3000 broke MRQ timing)
NF = int(DUR * FPS)
seq.set_playback_start(0); seq.set_playback_end(NF)
b = seq.add_possessable(cam)
tr = b.add_track(unreal.MovieScene3DTransformTrack)
sec = tr.add_section(); sec.set_range(0, NF)
ch = sec.get_all_channels()          # loc x,y,z, rot x(roll),y(pitch),z(yaw), scale x,y,z
tick_per_frame = 1   # add_key defaults to display-rate frames
prev_yaw = None; n = 0
STEP = 0.25
t = 0.0
while t <= DUR + 1e-6:
    p = Ps(t - LEAD); o = off(t - LEAD)
    cx, cy = p[0] + o[0], p[1] + o[1]
    g = ground(cx, cy)
    feet_z = p[2] - (HALF + 2.2)
    cz = max(feet_z + o[2], g + 70.0)
    tgt = unreal.Vector(p[0], p[1], feet_z + 92.0)      # mid body: full figure in a 45 mm frame
    rot = unreal.MathLibrary.find_look_at_rotation(unreal.Vector(cx, cy, cz), tgt)
    yaw = rot.yaw
    if prev_yaw is not None:
        while yaw - prev_yaw > 180: yaw -= 360
        while yaw - prev_yaw < -180: yaw += 360
    prev_yaw = yaw
    f = unreal.FrameNumber(int(round(t * FPS)) * tick_per_frame)
    for c, v in zip(ch[:6], (cx, cy, cz, 0.0, rot.pitch, yaw)):
        k = c.add_key(f, v)
        try: k.set_interpolation_mode(unreal.RichCurveInterpMode.RCIM_CUBIC)
        except Exception: pass
    n += 1; t += STEP
cut = seq.add_track(unreal.MovieSceneCameraCutTrack)
cs = cut.add_section(); cs.set_range(0, NF)
cs.set_camera_binding_id(seq.get_binding_id(b) if hasattr(seq, "get_binding_id") else b.get_binding_id())
eal.save_loaded_asset(seq)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print("sequence", path, "frames", NF, "keys", n, "tick/frame", tick_per_frame)
