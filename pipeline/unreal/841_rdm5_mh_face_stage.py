"""random_dungeonmagic_level5, the Summoner's MetaHuman face: the second face reel's stage and sequence (30 s). Builds
/Game/RandomDungeon/Maps/L_RDM5_MHFaceStudio (the first face reel's studio, 835's: the cyclorama, the portrait light, a
fixed exposure) with the Summoner as an ARDFacePuppet carrying her MetaHuman face (rdm5_mh_face.py: the face mesh on her,
its brows and lashes, her cut-away body material; the expressions as control curves), and the Level Sequence
/Game/RandomDungeon/Cinematics/LS_RDM5_MHFaces: her clips (idle, casts, flinch, death) and her expressions keyed as the
puppet's properties, each coming in and going as the game's cue for it does (face.json's cues):
   0.0- 2.8  at rest: blinking, looking about       14.0-16.8  PAIN      she is hit (her flinch)
   2.8- 5.6  JOY       she finds something          16.8-19.8  SHOUT     a cast with her whole voice
   5.6- 8.2  SURPRISE  a door opens on her           19.8-22.2  DISGUST   what is in the barrel
   8.2-11.2  FOCUS     a cast of the fire            22.2-24.6  FEAR      her hit points run low
  11.2-14.0  ANGER     a monster comes at her        24.6-27.0  SAD       a companion falls
                                                     27.0-30.0  DEATH     her eyes shut, she falls
The first reel (835, LS_RDM5_Faces, her own face) is left as it was: this one has a level and a sequence of its own.
Writes SourceArt/summoner/reel_plan_mh.json (the captions for the overlay). No frame without a clip ("animation on every
frame"). Idempotent. Args: [exposure bias]"""
import json, math, os, sys, importlib, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rdm5_mh_face as MF
importlib.reload(MF)
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
V = unreal.Vector; Rot = unreal.Rotator
LEVEL = "/Game/RandomDungeon/Maps/L_RDM5_MHFaceStudio"; SEQ = "/Game/RandomDungeon/Cinematics/LS_RDM5_MHFaces"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
PLAN = SA + r"\summoner\reel_plan_mh.json"
FACE = json.load(open(SA + r"\summoner\face.json")); SP = json.load(open(SA + r"\random_dungeon_magic5\spell.json"))
FPS = 30; DUR = 30.0; NF = int(DUR * FPS); TAG = unreal.Name("rdm5mhface")
EASE = 0.12
L = lambda p: unreal.load_asset(p.split(".")[0])
def clip_len(p): return unreal.AnimationLibrary.get_sequence_length(L(p))
IDLE = "/Game/JRPG/SummonerAnims/AS_Summoner_Idle"
CAST = [c["clip"] for c in SP["casts"]]; HIT = [c["hit"] for c in SP["casts"]]
FLINCH, DEATH = SP["flinch"], SP["death"]
# ---------------------------------------------------------------- the level (835's studio)
if eal.does_asset_exist(LEVEL): unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
else: les.new_level(LEVEL)
w = ues.get_editor_world(); assert w.get_path_name().startswith(LEVEL + "."), w.get_path_name()
for a in eas.get_all_level_actors():
    if TAG in a.tags or a.get_class().get_name() in ("StaticMeshActor", "RDFacePuppet", "RectLight", "PointLight", "SkyLight", "PostProcessVolume", "CineCameraActor", "ExponentialHeightFog", "DirectionalLight"):
        eas.destroy_actor(a)
def spawn(cls, loc, rot=(0, 0, 0), label=None, tags=()):
    a = eas.spawn_actor_from_class(cls, V(*loc), Rot(pitch=rot[0], yaw=rot[1], roll=rot[2])); assert a, cls
    a.tags = [TAG] + [unreal.Name(t) for t in tags]
    if label: a.set_actor_label(label)
    return a
def mesh_actor(path, loc, rot=(0, 0, 0), label=None, scale=1.0):
    a = spawn(unreal.StaticMeshActor, loc, rot, label); a.static_mesh_component.set_static_mesh(L(path)); a.set_actor_scale3d(V(scale, scale, scale))
    a.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE); return a
def aim(a, target): a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(a.get_actor_location(), V(*target)), False)
mesh_actor("/Game/Fig4/Studio/Meshes/SM_Cyclorama/StaticMeshes/SM_Cyclorama", (0, 0, 0), label="Cyclorama")
def rect(label, loc, target, wdt, hgt, cd, temp, barn=45, att=3000):
    a = spawn(unreal.RectLight, loc, label=label); c = a.light_component
    for k, v in (("intensity_units", unreal.LightUnits.CANDELAS), ("intensity", cd), ("source_width", wdt), ("source_height", hgt), ("barn_door_angle", barn),
                 ("barn_door_length", 30), ("use_temperature", True), ("temperature", temp), ("attenuation_radius", att)):
        c.set_editor_property(k, v)
    aim(a, target); return a
rect("Key", (-170, 260, 260), (0, 0, 150), 120, 90, 230, 5300)
rect("Fill", (240, 300, 170), (0, 0, 140), 200, 160, 70, 6200, barn=10)
rl = rect("Rim_L", (-260, -220, 230), (-20, 0, 150), 40, 160, 260, 7800, barn=60); rl.light_component.set_editor_property("use_temperature", False); rl.light_component.set_editor_property("light_color", unreal.Color(150, 120, 255, 255))
rr = rect("Rim_R", (260, -220, 230), (20, 0, 150), 40, 160, 240, 7800, barn=60); rr.light_component.set_editor_property("use_temperature", False); rr.light_component.set_editor_property("light_color", unreal.Color(110, 200, 255, 255))
rect("Back_Wash", (0, 500, 520), (0, -300, 100), 500, 260, 30, 4600, barn=20)
sky = spawn(unreal.SkyLight, (0, 0, 500), label="Sky"); sc = sky.light_component
sc.set_editor_property("intensity", 0.15); sc.set_editor_property("lower_hemisphere_is_black", True); sc.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)
ppv = spawn(unreal.PostProcessVolume, (0, 0, 100), label="PPV"); ppv.set_editor_property("unbound", True); s = ppv.settings
EXPOSURE = float(sys.argv[1]) if len(sys.argv) > 1 else -3.5
for k, v in (("dynamic_global_illumination_method", unreal.DynamicGlobalIlluminationMethod.LUMEN), ("reflection_method", unreal.ReflectionMethod.LUMEN),
             ("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL), ("auto_exposure_apply_physical_camera_exposure", False), ("auto_exposure_bias", EXPOSURE),
             ("bloom_intensity", 0.35), ("vignette_intensity", 0.45), ("film_grain_intensity", 0.03)):
    try: s.set_editor_property("override_" + k, True)
    except Exception: pass
    s.set_editor_property(k, v)
ppv.set_editor_property("settings", s)
# ---------------------------------------------------------------- the Summoner with her MetaHuman face
pup = spawn(unreal.RDFacePuppet, (0, 0, 0), (0, 0, 0), "Summoner", ("rdm5mhface_puppet",))
mc = pup.mesh; mc.set_skeletal_mesh_asset(L("/Game/JRPG/Character/SK_JRPG_Summoner"))
mc.set_editor_property("visibility_based_anim_tick_option", unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
mf, info = MF.meta_face()
pup.face.set_editor_property("channels", MF.channels()); pup.face.set_editor_property("meta_face", mf)
# ---------------------------------------------------------------- the sequence
if eal.does_asset_exist(SEQ):
    seq = unreal.load_asset(SEQ)
    for bd in seq.get_bindings(): bd.remove()
    for trk in seq.get_tracks(): seq.remove_track(trk)
else: seq = at.create_asset(SEQ.split("/")[-1], "/Game/RandomDungeon/Cinematics", unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
seq.set_display_rate(unreal.FrameRate(FPS, 1)); seq.set_playback_start(0); seq.set_playback_end(NF)
TICKS = seq.get_tick_resolution().numerator / seq.get_tick_resolution().denominator
F = lambda t: int(round(t * FPS))
B = {}
def bind(a):
    if a.get_name() not in B: B[a.get_name()] = seq.add_possessable(a)
    return B[a.get_name()]
def bridge(items):
    """(663's) no frame without a clip: an action clip plays on into the pause after it as far as it has frames, then its
    last frame is held"""
    out = []
    for i, (t0, t1, clip, rate, off) in enumerate(items):
        nxt = items[i + 1][0] if i + 1 < len(items) else None
        if nxt is None: out.append((t0, t1, clip, rate, off)); continue
        n = clip_len(clip); last = n - 0.05
        if (t1 - t0) * rate > n - off: out.append((t0, max(t1, nxt), clip, rate, off)); continue
        end = min(nxt, max(t0 + EASE, t0 + (last - off) / rate - EASE))
        if F(end) >= F(nxt): end = nxt
        out.append((t0, end, clip, rate, off))
        if end < nxt: out.append((end, nxt, clip, 0.0001, last))
    return out
def animate(a, items):
    """(663's) items one after another, each blending into the next over EASE, each section on a row of its own"""
    items = bridge(items)
    t = bind(a).add_track(unreal.MovieSceneSkeletalAnimationTrack)
    EF = int(round(EASE * FPS)); rows = []; made = []
    for i, (t0, t1, clip, rate, off) in enumerate(items):
        f0, f1 = F(t0), F(t1) + (EF if i < len(items) - 1 else 0)
        row = next((r for r, e in enumerate(rows) if e <= f0), len(rows))
        if row == len(rows): rows.append(f1)
        else: rows[row] = f1
        s = t.add_section(); s.set_row_index(row); s.set_range(f0, f1); made.append((s, f0, f1))
        p = s.get_editor_property("params"); p.set_editor_property("animation", L(clip))
        pr = unreal.MovieSceneTimeWarpVariant(); pr.set_fixed_play_rate(rate); p.set_editor_property("play_rate", pr)
        if off: p.set_editor_property("first_loop_start_frame_offset", unreal.FrameNumber(int(off * TICKS)))
        s.set_editor_property("params", p)
        e = unreal.MovieSceneEasingSettings(); n_ = int(round(EF * TICKS / FPS))
        e.import_text("(bManualEaseIn=%s,ManualEaseInDuration=%d,bManualEaseOut=%s,ManualEaseOutDuration=%d)" % (i > 0, n_ if i > 0 else 0, i < len(items) - 1, n_ if i < len(items) - 1 else 0))
        s.set_editor_property("easing", e)
    for s, f0, f1 in made: s.set_range(f0, f1)
# ---- her clips
T_CAST = [8.5, 17.1]; T_FLINCH = 14.3; T_DEATH = 27.45
items = [(0.0, T_CAST[0], IDLE, 1.0, 0.0)]
ce = T_CAST[0] + clip_len(CAST[0]) - 0.1
items += [(T_CAST[0], ce, CAST[0], 1.0, 0.0), (ce, T_FLINCH, IDLE, 1.0, 0.0)]
fe = T_FLINCH + clip_len(FLINCH) - 0.1
items += [(T_FLINCH, fe, FLINCH, 1.0, 0.0), (fe, T_CAST[1], IDLE, 1.0, 0.0)]
c2 = T_CAST[1] + clip_len(CAST[2]) - 0.1
items += [(T_CAST[1], c2, CAST[2], 1.0, 0.0), (c2, T_DEATH, IDLE, 1.0, 0.0)]
dl = clip_len(DEATH)
items += [(T_DEATH, min(DUR, T_DEATH + dl - 0.05), DEATH, 1.0, 0.0)]
if T_DEATH + dl - 0.05 < DUR: items += [(T_DEATH + dl - 0.05, DUR, DEATH, 0.0001, dl - 0.05)]
animate(pup, items)
# ---- her face: each expression a float track on the puppet, keyed as the game's cue would bring it in and out
CUE = FACE["cues"]
NAMES = ("Joy", "Anger", "Pain", "Fear", "Shout", "Focus", "Blink", "Dead", "Surprise", "Sad", "Disgust", "Effort", "LookRight", "LookUp")
keys = {n: [(0.0, 0.0)] for n in NAMES}
def cue(ch, t, weight=1.0, fin=0.12, hold=0.5, fout=0.3):
    keys[ch] += [(t - 0.001, 0.0), (t + fin, weight), (t + fin + hold, weight), (t + fin + hold + fout, 0.0)]
def held(ch, t0, t1, weight, fin, fout):
    keys[ch] += [(t0, 0.0), (t0 + fin, weight), (t1, weight), (t1 + fout, 0.0)]
def blink(t): cue("Blink", t, 1.0, 0.07, 0.05, 0.12)
def look(t0, t1, right, up, fin=0.18):
    """the eyes turn to (right, up) and back"""
    keys["LookRight"] += [(t0, 0.0), (t0 + fin, right), (t1, right), (t1 + fin, 0.0)]
    keys["LookUp"] += [(t0, 0.0), (t0 + fin, up), (t1, up), (t1 + fin, 0.0)]
for t in (0.9, 2.45, 8.0, 11.0, 19.6, 24.4): blink(t)
look(1.15, 1.75, 0.7, 0.1); look(1.95, 2.35, -0.6, -0.15)                 # (she looks about: right, then left)
cue("Joy", 3.0, 1.0, CUE["Loot"]["in"] * 2.0, 1.9, CUE["Loot"]["out"] * 1.5)
cue("Surprise", 5.85, 1.0, 0.1, 1.2, 0.6); look(5.85, 7.3, 0.0, 0.25, 0.1)
cue("Focus", T_CAST[0] + HIT[0] - CUE["Cast"]["in"] - 0.35, 1.0, CUE["Cast"]["in"] + 0.2, CUE["Cast"]["hold"] + 0.8, CUE["Cast"]["out"] + 0.2)
held("Anger", 11.35, 13.6, CUE["Fight"]["weight"] + 0.15, CUE["Fight"]["in"], 0.35)
cue("Pain", T_FLINCH + 0.03, 1.0, CUE["Hurt"]["in"], CUE["Hurt"]["hold"] + 0.9, CUE["Hurt"]["out"] + 0.2)
cue("Shout", T_CAST[1] + HIT[2] - 0.25, 1.0, 0.2, 1.0, 0.35)
cue("Disgust", 20.05, 0.95, 0.25, 1.3, 0.45); look(20.05, 21.4, -0.25, -0.35, 0.15)
held("Fear", 22.45, 24.25, 0.95, 0.35, 0.3); look(22.6, 23.4, 0.55, 0.05, 0.08); look(23.5, 24.2, -0.5, 0.05, 0.08)
held("Sad", 24.85, 26.7, 0.95, 0.5, 0.35); look(24.95, 26.7, 0.0, -0.45, 0.4)
keys["Dead"] += [(T_DEATH - 0.5, 0.0), (T_DEATH - 0.5 + CUE["Death"]["in"], 1.0), (DUR, 1.0)]       # (her eyes shut, then she falls)
b = bind(pup)
for ch, ks in keys.items():
    prop = {"LookRight": "LookRight", "LookUp": "LookUp"}.get(ch, ch)
    trk = b.add_track(unreal.MovieSceneFloatTrack); trk.set_property_name_and_path(prop, prop)
    sec = trk.add_section(); sec.set_range(0, NF); c = sec.get_all_channels()[0]
    for t, v in sorted(ks):
        fr = max(0.0, t) * FPS; k = c.add_key(unreal.FrameNumber(int(math.floor(fr))), float(v), fr - math.floor(fr))
        k.set_interpolation_mode(unreal.RichCurveInterpMode.RCIM_LINEAR)
# ---------------------------------------------------------------- cameras
def camera(label, keys_, focal, focus_z):
    cam = spawn(unreal.CineCameraActor, keys_[0][1], label=label); cc = cam.get_cine_camera_component()
    fb = cc.get_editor_property("filmback"); fb.sensor_width = 36.0; fb.sensor_height = 20.25; cc.set_editor_property("filmback", fb)
    cc.set_editor_property("current_focal_length", focal); cc.set_editor_property("current_aperture", 8.0)
    fs = cc.get_editor_property("focus_settings"); fs.focus_method = unreal.CameraFocusMethod.DISABLE; cc.set_editor_property("focus_settings", fs)
    bb = bind(cam); t = bb.add_track(unreal.MovieScene3DTransformTrack); s_ = t.add_section(); s_.set_range(0, NF); ch_ = s_.get_all_channels()
    for tt, pos, lk in keys_:
        r = unreal.MathLibrary.find_look_at_rotation(V(*pos), V(*lk))
        for c_, v in zip(ch_[:6], (pos[0], pos[1], pos[2], 0.0, r.pitch, r.yaw)):
            k = c_.add_key(unreal.FrameNumber(F(tt)), v); k.set_interpolation_mode(unreal.RichCurveInterpMode.RCIM_CUBIC)
    return bb
# (her MetaHuman eyes stand at about 155 cm in the idle, 6 cm in front of her head bone: the close shots aim a little below them)
EZ = 155.0; EY = 11.0
def close(label, t0, t1, side=0.0, d0=120.0, d1=100.0, up=1.0):
    return (t0, t1, camera(label, [(t0, (side * d0, EY + d0, EZ + up), (0, EY, EZ - 4)), (t1, (side * d1 * 0.9, EY + d1, EZ + up), (0, EY, EZ - 4))], 85.0, EZ))
cams = [
    (0.0, 2.8, camera("Cam_Rest", [(0.0, (0, 230, EZ + 6), (0, EY, EZ - 6)), (2.8, (0, 140, EZ + 2), (0, EY, EZ - 5))], 85.0, EZ)),
    close("Cam_Joy", 2.8, 5.6, side=-0.45),
    close("Cam_Surprise", 5.6, 8.2, side=0.25, d0=110, d1=95),
    (8.2, 11.2, camera("Cam_Focus", [(8.2, (55, 200, 156), (0, EY, 146)), (11.2, (45, 165, 157), (0, EY, 148))], 70.0, 150.0)),
    close("Cam_Anger", 11.2, 14.0, side=0.0, d0=115, d1=92),
    close("Cam_Pain", 14.0, 16.8, side=0.42, d0=118, d1=104),
    (16.8, 19.8, camera("Cam_Shout", [(16.8, (-55, 195, 157), (0, EY, 147)), (19.8, (-42, 165, 157), (0, EY, 149))], 70.0, 150.0)),
    close("Cam_Disgust", 19.8, 22.2, side=-0.3, d0=112, d1=98),
    close("Cam_Fear", 22.2, 24.6, side=0.0, d0=125, d1=100, up=3.0),
    close("Cam_Sad", 24.6, 27.0, side=0.35, d0=110, d1=96, up=2.0),
    (27.0, T_DEATH + 0.55, camera("Cam_DeathFace", [(27.0, (0, EY + 115, EZ + 2), (0, EY, EZ - 5)), (T_DEATH + 0.55, (0, EY + 108, EZ - 2), (0, -10, EZ - 14))], 85.0, EZ)),
    (T_DEATH + 0.55, DUR, camera("Cam_Fall", [(T_DEATH + 0.55, (-60, 260, 175), (0, -60, 70)), (DUR, (-50, 235, 165), (0, -110, 25))], 35.0, 60.0)),
]
cut = seq.add_track(unreal.MovieSceneCameraCutTrack)
for t0, t1, bb in cams:
    cs = cut.add_section(); cs.set_range(F(t0), F(t1)); cs.set_camera_binding_id(seq.get_binding_id(bb))
def coverage():
    import re
    bad = []
    for bb in seq.get_bindings():
        for trk in bb.get_tracks():
            if not isinstance(trk, unreal.MovieSceneSkeletalAnimationTrack): continue
            secs = []
            for s_ in trk.get_sections():
                p = s_.get_editor_property("params"); et = s_.get_editor_property("easing").export_text()
                g = lambda k: re.search(k + r"=(\w+)", et).group(1)
                ein = int(g("ManualEaseInDuration")) * FPS / TICKS if g("bManualEaseIn") == "True" else 0.0
                eout = int(g("ManualEaseOutDuration")) * FPS / TICKS if g("bManualEaseOut") == "True" else 0.0
                clip = p.get_editor_property("animation"); rate = p.get_editor_property("play_rate").to_fixed_play_rate()
                secs.append((s_.get_start_frame(), s_.get_end_frame(), ein, eout, clip.get_name(), rate,
                             p.get_editor_property("first_loop_start_frame_offset").value / TICKS, unreal.AnimationLibrary.get_sequence_length(clip)))
            low = [f for f in range(NF) if sum((min(1.0, (f + 0.5 - f0) / ei) if ei else 1.0) * (min(1.0, (f1 - f - 0.5) / eo) if eo else 1.0)
                                               for f0, f1, ei, eo, *_ in secs if f0 <= f + 0.5 < f1) < 0.98]
            over = [(nm, f0) for f0, f1, ei, eo, nm, rate, off, n in secs if (f1 - f0) * rate < n * FPS and off + (f1 - f0) / FPS * rate > n + 0.005 and "Idle" not in nm]
            if low or over: bad.append(f"{bb.get_display_name()}: {len(low)} frames under full weight from {low[:1]}, past clip end {over[:2]}")
    return bad
uncovered = coverage()
for line in uncovered: print("RDM5MHFACE coverage", line)
eal.save_loaded_asset(seq, False)
pup.set_actor_hidden_in_game(False)
les.save_current_level()
caps = [(0.3, 2.7, "THE SUMMONER", ["her face is a MetaHuman now: Epic's preset Aera in her colouring, under her own hair",
                                     "RigLogic moves 858 blend shapes and the face's joints from FACS control curves"]),
        (3.0, 5.5, "JOY", ["she finds something in a chest", "AU 6 + 12: the cheeks raised, the lip corners pulled up"]),
        (5.8, 8.1, "SURPRISE", ["a door opens on her", "AU 1 + 2 + 5 + 26: brows raised, lids up, the jaw dropped"]),
        (8.4, 11.1, "FOCUS", ["a cast of the fire", "AU 4 + 7 + 24: brows drawn down, lids tightened, lips pressed"]),
        (11.4, 13.9, "ANGER", ["a monster comes at her", "AU 4 + 5 + 7 + 23: brows down and together, a glare, lips tight"]),
        (14.2, 16.7, "PAIN", ["she is hit", "AU 4 + 6 + 7 + 9 + 10 + 43: the face screwed up, the eyes closing"]),
        (17.0, 19.7, "SHOUT", ["a cast with her whole voice", "AU 4 + 10 + 16 + 27: the jaw wide, the neck straining"]),
        (20.0, 22.1, "DISGUST", ["what is in the barrel", "AU 9 + 10 + 15: the nose wrinkled, the upper lip raised"]),
        (22.4, 24.5, "FEAR", ["her hit points run low", "AU 1 + 2 + 4 + 5 + 20: brows up and drawn, the lips stretched"]),
        (24.8, 26.9, "SADNESS", ["", "AU 1 + 4 + 15 + 17: the inner brows raised, the mouth's corners down"]),
        (27.2, 29.8, "DEATH", ["her eyes shut, the jaw slack", "in play: hurt, cast, loot, a fight, low health and death each show their own"])]
json.dump({"fps": FPS, "seconds": DUR, "captions": [{"t0": a, "t1": b_, "head": h, "lines": [x for x in l if x]} for a, b_, h, l in caps],
           "casts": [round(t + h, 3) for t, h in zip(T_CAST, (HIT[0], HIT[2]))], "flinch": T_FLINCH, "death": T_DEATH, "exposure": EXPOSURE,
           "face": info}, open(PLAN, "w"), indent=1)
print(f"RDM5MHFACE stage saved {LEVEL} | sequence {SEQ} {NF} frames | {len(cams)} shots | {sum(len(v) for v in keys.values())} face keys | animation on every frame: {'yes' if not uncovered else 'NO'} | plan {PLAN}")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
