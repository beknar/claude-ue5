"""Tripo trio showcase: one 60 s reel of the three animated Tripo characters (jrpg-fem5-tripo, girl-caster-tripo,
girl-darkcaster-tripo). Builds /Game/JRPG/Maps/L_Tripo_Trio_Showcase (the photo studio's cyclorama and lacquer plinth, a
light rig for a turntable and a duel) and the Level Sequence /Game/JRPG/Cinematics/LS_Tripo_Trio_Showcase:
   0-3 s    the three side by side
   3-21     Fem5: 7 s turning on the plinth (her idle), then 11 s against a troll with the three weapons of
            random_dungeoncombat_level (sword and shield, spear and shield, axe: her retargeted attack clips; the troll
            flinches at every blow and dies at the last)
   21-39    the caster: turntable, then six casts at a mutant 6.5 m away (each bolt hits it; it dies at the last)
   39-57    the dark caster: turntable, then two left-hand casts at a daemon, which walks up to her and falls to her sword
   57-60    the three again
Characters and monsters are skeletal mesh actors played by the sequence's animation tracks (sections blended into each
other), shown and hidden by visibility tracks, moved by stepped transform keys; the weapons are static mesh actors on
their hands with the grips of 790 / 817. The fire is not in the sequence: the pilot (661) spawns it while the queue
renders, at the times this script writes to SourceArt/tripo_trio/plan.json (with the captions for the overlay). The
blow / release times are the measured ones of 790, 810 and 817; a bolt's flight time is the distance over its speed.
Reads the monsters (meshes, idle / walk / hit / death clips, walk speed) from random_dungeoncombat_level's generator, so
that level is opened first. Idempotent (actors tagged `trio`, the sequence rebuilt). Args: none"""
import json, math, os, unreal
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
V = unreal.Vector; Rot = unreal.Rotator
LEVEL = "/Game/JRPG/Maps/L_Tripo_Trio_Showcase"; SEQ = "/Game/JRPG/Cinematics/LS_Tripo_Trio_Showcase"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
PLAN = SA + r"\tripo_trio\plan.json"
FPS = 30; DUR = 60.0; NF = int(DUR * FPS); TAG = unreal.Name("trio")
EASE = 0.12                  # seconds two animation sections blend over
# ---------------------------------------------------------------- data: monsters, weapons, clips
COMBAT = "/Game/RandomDungeon/Maps/random_dungeoncombat_level"
if not ues.get_editor_world().get_path_name().startswith(COMBAT + "."): unreal.EditorLoadingAndSavingUtils.load_map(COMBAT)
gen = unreal.GameplayStatics.get_all_actors_of_class(ues.get_editor_world(), unreal.RDDungeonGenerator)[0]
MON = {}
for d in gen.get_editor_property("monsters"):
    if str(d.name) in ("Troll", "Mutant", "Daemon"):
        b = d.mesh.get_bounds()
        MON[str(d.name)] = {"mesh": d.mesh.get_path_name(), "idle": d.idle.get_path_name(), "walk": d.walk.get_path_name(), "walk_speed": d.walk_clip_speed,
                            "hit": d.get_hit.get_path_name(), "death": d.death.get_path_name(), "zmin": b.origin.z - b.box_extent.z, "radius": d.capsule_radius}
del gen
W1 = json.load(open(SA + r"\random_dungeon_combat\weapons.json"))
SP = json.load(open(SA + r"\random_dungeon_magic\spell.json"))
W2 = json.load(open(SA + r"\random_dungeon_magic2\weapons.json"))
L = lambda p: unreal.load_asset(p.split(".")[0])
def clip_len(p): return unreal.AnimationLibrary.get_sequence_length(L(p))
# ---------------------------------------------------------------- the level
if eal.does_asset_exist(LEVEL): unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
else: les.new_level(LEVEL)
w = ues.get_editor_world(); assert w.get_path_name().startswith(LEVEL + "."), w.get_path_name()
for a in eas.get_all_level_actors():
    if TAG in a.tags or a.get_class().get_name() in ("StaticMeshActor", "SkeletalMeshActor", "RectLight", "PointLight", "SkyLight", "PostProcessVolume", "CineCameraActor", "ExponentialHeightFog"):
        eas.destroy_actor(a)
def spawn(cls, loc, rot=(0, 0, 0), label=None, tags=()):
    a = eas.spawn_actor_from_class(cls, V(*loc), Rot(pitch=rot[0], yaw=rot[1], roll=rot[2])); assert a, cls
    a.tags = [TAG] + [unreal.Name(t) for t in tags]
    if label: a.set_actor_label(label)
    return a
def mesh_actor(path, loc, rot=(0, 0, 0), label=None, scale=1.0, tags=()):
    a = spawn(unreal.StaticMeshActor, loc, rot, label, tags); a.static_mesh_component.set_static_mesh(L(path)); a.set_actor_scale3d(V(scale, scale, scale))
    a.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE); return a
def aim(a, target): a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(a.get_actor_location(), V(*target)), False)
mesh_actor("/Game/Fig4/Studio/Meshes/SM_Cyclorama/StaticMeshes/SM_Cyclorama", (0, 0, 0), label="Cyclorama")
plinth = mesh_actor("/Game/Fig4/Studio/Meshes/SM_Plinth/StaticMeshes/SM_Plinth", (0, -40, 0), label="Plinth")
def rect(label, loc, target, wdt, hgt, cd, temp, barn=45, att=3000):
    a = spawn(unreal.RectLight, loc, label=label); c = a.light_component
    for k, v in (("intensity_units", unreal.LightUnits.CANDELAS), ("intensity", cd), ("source_width", wdt), ("source_height", hgt), ("barn_door_angle", barn),
                 ("barn_door_length", 30), ("use_temperature", True), ("temperature", temp), ("attenuation_radius", att)):
        c.set_editor_property(k, v)
    aim(a, target); return a
rect("Key", (-380, 520, 420), (0, 60, 110), 160, 120, 260, 5400)
rect("Fill", (460, 560, 220), (0, 60, 100), 220, 180, 55, 5800, barn=10)
rect("Rim_L", (-420, -320, 300), (-60, 60, 130), 40, 200, 300, 6800, barn=60)
rect("Rim_R", (420, -320, 300), (60, 60, 130), 40, 200, 280, 6800, barn=60)
rect("Top", (0, -80, 420), (0, -40, 100), 80, 60, 70, 5000)
rect("Floor_Wash", (0, 700, 520), (0, 100, 0), 400, 200, 40, 4800, barn=20)
sky = spawn(unreal.SkyLight, (0, 0, 500), label="Sky"); sc = sky.light_component
sc.set_editor_property("intensity", 0.18); sc.set_editor_property("lower_hemisphere_is_black", True); sc.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)
ppv = spawn(unreal.PostProcessVolume, (0, 0, 100), label="PPV"); ppv.set_editor_property("unbound", True); s = ppv.settings
for k, v in (("dynamic_global_illumination_method", unreal.DynamicGlobalIlluminationMethod.LUMEN), ("reflection_method", unreal.ReflectionMethod.LUMEN),
             ("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL), ("auto_exposure_apply_physical_camera_exposure", False), ("auto_exposure_bias", -1.5),
             ("bloom_intensity", 0.45), ("vignette_intensity", 0.4), ("film_grain_intensity", 0.05)):
    try: s.set_editor_property("override_" + k, True)
    except Exception: pass
    s.set_editor_property(k, v)
ppv.set_editor_property("settings", s)
spell_light = spawn(unreal.PointLight, (0, 0, -500), label="Spell_Light", tags=("trio_spell_light",)); lc = spell_light.light_component
lc.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS); lc.set_editor_property("intensity", 0.0); lc.set_editor_property("attenuation_radius", 1400.0)
lc.set_editor_property("light_color", unreal.Color(255, 140, 50, 255)); lc.set_editor_property("cast_shadows", False); lc.set_mobility(unreal.ComponentMobility.MOVABLE)
# ---------------------------------------------------------------- characters, weapons, monsters
def skel(path, loc, yaw, label, tags=(), scale=1.0):
    a = spawn(unreal.SkeletalMeshActor, loc, (0, yaw, 0), label, tags); c = a.skeletal_mesh_component
    c.set_skeletal_mesh_asset(L(path)) if hasattr(c, "set_skeletal_mesh_asset") else c.set_editor_property("skeletal_mesh", L(path))
    c.set_editor_property("visibility_based_anim_tick_option", unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
    a.set_actor_scale3d(V(scale, scale, scale)); return a
fem = skel("/Game/JRPG/Character/SK_JRPG_Fem5", (0, 0, 0), 0, "Fem5", ("trio_fem5",))
cas = skel("/Game/JRPG/Character/SK_JRPG_Caster", (0, 0, 0), 0, "Caster", ("trio_caster",))
dark = skel("/Game/JRPG/Character/SK_JRPG_DarkCaster", (0, 0, 0), 0, "DarkCaster", ("trio_dark",))
def xf(d): return unreal.Transform(V(*d["loc"]), Rot(roll=d["rot"][0], pitch=d["rot"][1], yaw=d["rot"][2]), V(*d["scale"]))
def held(path, owner, bone, grip, label):
    a = mesh_actor(path, (0, 0, 0), label=label); a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    a.attach_to_component(owner.skeletal_mesh_component, bone, unreal.AttachmentRule.SNAP_TO_TARGET, unreal.AttachmentRule.SNAP_TO_TARGET, unreal.AttachmentRule.KEEP_WORLD, False)
    a.set_actor_relative_transform(xf(grip), False, False); return a
WP = {}
for name in W1["order"]:
    e = W1["weapons"][name]
    WP[name] = [held(e["mesh"], fem, e["hand_bone"], e["grip"], f"Fem5_{name}")]
    if e["shield"]: WP[name].append(held(e["shield"], fem, e["shield_bone"], e["shield_grip"], f"Fem5_{name}_Shield"))
dsw = W2["weapons"]["Sword"]; dark_sword = held(dsw["mesh"], dark, dsw["hand_bone"], dsw["grip"], "Dark_Sword")
mons = {}
for n in ("Troll", "Mutant", "Daemon"):
    mons[n] = skel(MON[n]["mesh"], (0, 0, -MON[n]["zmin"]), 0, n, ("trio_" + n.lower(),))
# ---------------------------------------------------------------- the sequence
if eal.does_asset_exist(SEQ):
    # (emptied, not deleted: a sequence still loaded cannot be made again under its name)
    seq = unreal.load_asset(SEQ)
    for bd in seq.get_bindings(): bd.remove()
    for trk in (seq.get_tracks() if hasattr(seq, "get_tracks") else seq.get_master_tracks()):
        seq.remove_track(trk) if hasattr(seq, "remove_track") else seq.remove_master_track(trk)
else: seq = at.create_asset(SEQ.split("/")[-1], "/Game/JRPG/Cinematics", unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
seq.set_display_rate(unreal.FrameRate(FPS, 1)); seq.set_playback_start(0); seq.set_playback_end(NF)
TICKS = seq.get_tick_resolution().numerator / seq.get_tick_resolution().denominator
F = lambda t: int(round(t * FPS))
B = {}
def bind(a):
    if a.get_name() not in B: B[a.get_name()] = seq.add_possessable(a)
    return B[a.get_name()]
def visibility(a, spans):
    """the actor is seen only within the given (t0, t1) spans"""
    t = bind(a).add_track(unreal.MovieSceneVisibilityTrack); s = t.add_section(); s.set_range(0, NF); ch = s.get_all_channels()[0]
    ch.add_key(unreal.FrameNumber(0), False)
    for t0, t1 in spans: ch.add_key(unreal.FrameNumber(F(t0)), True); ch.add_key(unreal.FrameNumber(F(t1)), False)
def place(a, keys, smooth=False):
    """(time, (x, y, z), yaw[, "l"]) keys: stepped (a jump to the next key), or linear to the next key where the key says
    "l" (or all of them when smooth)"""
    t = bind(a).add_track(unreal.MovieScene3DTransformTrack); s = t.add_section(); s.set_range(0, NF); ch = s.get_all_channels()
    for key in keys:
        tt, (x, y, z), yaw = key[:3]; lin = smooth or (len(key) > 3 and key[3] == "l")
        for c, v in zip(ch[:6], (x, y, z, 0.0, 0.0, yaw)):
            k = c.add_key(unreal.FrameNumber(F(tt)), v)
            k.set_interpolation_mode(unreal.RichCurveInterpMode.RCIM_LINEAR if lin else unreal.RichCurveInterpMode.RCIM_CONSTANT)
        for c in ch[6:9]: c.add_key(unreal.FrameNumber(F(tt)), a.get_actor_scale3d().x).set_interpolation_mode(unreal.RichCurveInterpMode.RCIM_CONSTANT)
def animate(a, items):
    """items: (t0, t1, clip path, play rate, start offset s) one after another; each section blends into the next over EASE"""
    t = bind(a).add_track(unreal.MovieSceneSkeletalAnimationTrack)
    for i, (t0, t1, clip, rate, off) in enumerate(items):
        s = t.add_section(); s.set_row_index(i % 2)
        s.set_range(F(t0), F(t1 + (EASE if i < len(items) - 1 else 0.0)))
        p = s.get_editor_property("params"); p.set_editor_property("animation", L(clip))
        pr = unreal.MovieSceneTimeWarpVariant(); pr.set_fixed_play_rate(rate); p.set_editor_property("play_rate", pr)      # (5.8: the play rate is a time warp)
        if off: p.set_editor_property("first_loop_start_frame_offset", unreal.FrameNumber(int(off * TICKS)))
        s.set_editor_property("params", p)
        e = unreal.MovieSceneEasingSettings(); n_ = int(EASE * TICKS)        # (set as text: one of the two flags is not reachable by name from Python)
        e.import_text("(bManualEaseIn=%s,ManualEaseInDuration=%d,bManualEaseOut=%s,ManualEaseOutDuration=%d)" % (i > 0, n_ if i > 0 else 0, i < len(items) - 1, n_ if i < len(items) - 1 else 0))
        s.set_editor_property("easing", e)
OFF = (0.0, 4000.0, 0.0)          # (where a hidden actor waits: far off the stage)
P0, PZ = (0, -40), 6.0            # the plinth's middle, its top
events = []; caps = []
def turntable(t0, t1):
    """on the plinth, one full turn from facing the camera (linear between the keys)"""
    return [(t0, (P0[0], P0[1], PZ), 0.0, "l"), (t1 - 1.0 / FPS, (P0[0], P0[1], PZ), 360.0 * (1.0 - 1.0 / (FPS * (t1 - t0))))]      # (the last key a frame before the next jump)
# ---- intro / outro: the three in a row, facing the camera (a Tripo character faces +Y at yaw 0)
ROW = {"fem": ((-190, 40, 0), 0.0), "cas": ((P0[0], P0[1], PZ), 0.0), "dark": ((190, 40, 0), 0.0)}
SEG = {"fem": (3.0, 21.0), "cas": (21.0, 39.0), "dark": (39.0, 57.0)}; TT = 7.0
# ---- Fem5: turntable, then the three weapons on the troll
ACT = (-120, 160, 0)
place(fem, [(0.0, ROW["fem"][0], 0.0)] + turntable(3.0, 10.0) + [(10.0, ACT, -90.0), (21.0, OFF, 0.0), (57.0, ROW["fem"][0], 0.0)])
idle_f = "/Game/JRPG/Fem5Anims/AS_Fem5_Idle"
items = [(0.0, 10.0 + 0.6, idle_f, 1.0, 0.0)]; tcur = 10.6; troll_hits = []; vis_w = {n: [] for n in WP}
order = [("Sword", [0, 1, 2]), ("Spear", [0, 1]), ("Axe", [0, 1, 2])]
for wname, which in order:
    e = W1["weapons"][wname]; ws = tcur
    for k in which:
        a_ = e["attacks"][k]; dur = a_["end"] / e["rate"]
        items.append((tcur, tcur + dur, a_["clip"], e["rate"], 0.0)); troll_hits.append(tcur + a_["hit"] / e["rate"]); tcur += dur + 0.08
    items.append((tcur, tcur + 0.45, idle_f, 1.0, 0.0)); tcur += 0.45
    vis_w[wname].append((ws - 0.2 if wname != "Sword" else 0.0, tcur))
items.append((tcur, 60.0, idle_f, 1.0, 0.0))
animate(fem, items)
fem_end = tcur
vis_w["Sword"] = [(0.0, vis_w["Sword"][0][1])] + [(fem_end, 60.0)]       # (sword and shield in the turntable, the intro and the outro too)
for name, acts in WP.items():
    for a in acts: visibility(a, vis_w[name])
visibility(fem, [(0.0, 21.0), (57.0, 60.0)])
caps += [(3.2, 9.8, "JRPG-FEM5-TRIPO", ["the player of the procedural levels  \u00b7  her own idle, walk and run"]),
         (10.2, fem_end + 0.3, "SWORD  \u00b7  SPEAR  \u00b7  AXE", ["the attack clips of three Fab animation packs, retargeted to her  \u00b7  the weapons of random_dungeoncombat_level"])]
# the troll: across from her, a flinch at every blow, death at the last
TROLL = (ACT[0] + 150, ACT[1], -MON["Troll"]["zmin"])          # (its hit clips knock it back: it stands close)
place(mons["Troll"], [(0.0, OFF, 0), (10.0, TROLL, 90.0), (21.0, OFF, 0)])
visibility(mons["Troll"], [(10.0, 21.0)])
def reactions(m, start, end, hits, dies=True, walk=None):
    """idle, a flinch at each hit, death at the last one (it lies still till the end); walk = (t0, t1) of a walk"""
    d = MON[m]; it = []; t = start; hl = clip_len(d["hit"]); dl = clip_len(d["death"])
    if walk:
        it.append((t, walk[0], d["idle"], 1.0, 0.0)); it.append((walk[0], walk[1], d["walk"], 1.0, 0.0)); t = walk[1]
    for i, h in enumerate(hits):
        last = dies and i == len(hits) - 1
        if h > t: it.append((t, h, d["idle"], 1.0, 0.0))
        if last:
            it.append((h, h + dl - 0.05, d["death"], 1.0, 0.0)); it.append((h + dl - 0.05, end, d["death"], 0.0001, max(0.0, dl - 0.06))); t = end; break
        nxt = hits[i + 1] if i + 1 < len(hits) else end
        it.append((h, min(h + hl, nxt), d["hit"], 1.0, 0.0)); t = min(h + hl, nxt)
    if t < end: it.append((t, end, d["idle"], 1.0, 0.0))
    animate(mons[m], it)
reactions("Troll", 0.0, 60.0, troll_hits)
# ---- the caster: turntable, then six casts at the mutant
CAS_A, MUT = (-330, 160, 0), (330, 160, -MON["Mutant"]["zmin"])
place(cas, [(0.0, ROW["cas"][0], 0.0), (3.0, OFF, 0.0)] + turntable(21.0, 28.0) + [(28.0, CAS_A, -90.0), (39.0, OFF, 0.0), (57.0, ROW["cas"][0], 0.0)])
idle_c = "/Game/JRPG/CasterAnims/AS_Caster_Idle"
items = [(0.0, 28.6, idle_c, 1.0, 0.0)]; tcur = 28.6; mut_hits = []
dist = abs(MUT[0] - CAS_A[0]) - MON["Mutant"]["radius"] - 30.0
for k in [0, 1, 2, 0, 2, 1]:
    c = SP["casts"][k]; dur = c["end"] / SP["rate"]; rel = tcur + c["hit"] / SP["rate"]
    items.append((tcur, tcur + dur, c["clip"], SP["rate"], 0.0))
    events.append({"kind": "cast", "who": "trio_caster", "hand": SP["bone"], "charge": round(tcur + 0.05, 3), "release": round(rel, 3), "target": "trio_mutant"})
    mut_hits.append(rel + dist / SP["bolt_speed"]); tcur += dur + 0.35
items.append((tcur, 60.0, idle_c, 1.0, 0.0)); animate(cas, items); cas_end = tcur
place(mons["Mutant"], [(0.0, OFF, 0), (28.0, MUT, 90.0), (39.0, OFF, 0)]); visibility(mons["Mutant"], [(28.0, 39.0)]); visibility(cas, [(0.0, 3.0), (21.0, 39.0), (57.0, 60.0)])
reactions("Mutant", 0.0, 60.0, mut_hits)
caps += [(21.2, 27.8, "GIRL-CASTER-TRIPO", ["her own walk and run  \u00b7  an idle and three casts made for her in Blender (caster_clips.py)"]),
         (28.2, cas_end + 0.3, "FIRE SPELL", ["sparks gather on her hand, the bolt leaves at the release and bursts on the mutant  \u00b7  the fire effects of docs/magic.md"])]
# ---- the dark caster: turntable, two casts at the daemon, it walks up, the sword
DARK_A, DAE0 = (-330, 160, 0), (330, 160, -MON["Daemon"]["zmin"])
place(dark, [(0.0, ROW["dark"][0], 0.0), (3.0, OFF, 0.0)] + turntable(39.0, 46.0) + [(46.0, DARK_A, -90.0), (57.0, ROW["dark"][0], 0.0)])
idle_d = "/Game/JRPG/DarkCasterAnims/AS_DarkCaster_Idle"
fire = W2["weapons"]["Fire"]; sw = W2["weapons"]["Sword"]
items = [(0.0, 46.6, idle_d, 1.0, 0.0)]; tcur = 46.6; dae_hits = []
dist = abs(DAE0[0] - DARK_A[0]) - MON["Daemon"]["radius"] - 30.0
for k in (0, 1):
    c = fire["casts"][k]; dur = c["end"] / fire["rate"]; rel = tcur + c["hit"] / fire["rate"]
    items.append((tcur, tcur + dur, c["clip"], fire["rate"], 0.0))
    events.append({"kind": "cast", "who": "trio_dark", "hand": fire["bone"], "charge": round(tcur + 0.05, 3), "release": round(rel, 3), "target": "trio_daemon"})
    dae_hits.append(rel + dist / fire["bolt_speed"]); tcur += dur + 0.3
# it walks up to her: from 6.6 m to sword's reach
DAE1 = (DARK_A[0] + 140, DAE0[1], DAE0[2]); walk_t0 = dae_hits[-1] + 0.55; walk_t1 = walk_t0 + (DAE0[0] - DAE1[0]) / MON["Daemon"]["walk_speed"]
items.append((tcur, walk_t1, idle_d, 1.0, 0.0)); tcur = walk_t1
for k in (0, 1, 2):
    a_ = sw["attacks"][k]; dur = a_["end"] / sw["rate"]
    items.append((tcur, tcur + dur, a_["clip"], sw["rate"], 0.0)); dae_hits.append(tcur + a_["hit"] / sw["rate"]); tcur += dur + 0.08
items.append((tcur, 60.0, idle_d, 1.0, 0.0)); animate(dark, items); dark_end = tcur
place(mons["Daemon"], [(0.0, OFF, 0), (46.0, DAE0, 90.0), (walk_t0, DAE0, 90.0, "l"), (walk_t1, DAE1, 90.0), (57.0, OFF, 0)])        # (linear only while it walks)
visibility(mons["Daemon"], [(46.0, 57.0)]); visibility(dark, [(0.0, 3.0), (39.0, 60.0)]); visibility(dark_sword, [(0.0, 3.0), (39.0, 60.0)])
reactions("Daemon", 0.0, 60.0, dae_hits, walk=(walk_t0, walk_t1))
caps += [(39.2, 45.8, "GIRL-DARKCASTER-TRIPO", ["her own idle, walk and run  \u00b7  the right hand closed on the sword's hilt in every clip"]),
         (46.2, dark_end + 0.3, "FIRE AND STEEL", ["two casts from her left hand, then three cuts of the sword in her right  \u00b7  all made for her in Blender (darkcaster_clips.py)"])]
caps += [(57.2, 59.9, "THREE TRIPO CHARACTERS", ["jrpg-fem5-tripo  \u00b7  girl-caster-tripo  \u00b7  girl-darkcaster-tripo"])]
# the plinth turns with each turntable
pk = [(0.0, (P0[0], P0[1], 0.0), 0.0)]
for c0 in (3.0, 21.0, 39.0): pk += [(c0, (P0[0], P0[1], 0.0), 0.0, "l"), (c0 + TT - 1.0 / FPS, (P0[0], P0[1], 0.0), 360.0 * (1.0 - 1.0 / (FPS * TT)))]
place(plinth, pk)
# ---------------------------------------------------------------- cameras
def camera(label, keys, focal, focus_actor):
    cam = spawn(unreal.CineCameraActor, keys[0][1], label=label); cc = cam.get_cine_camera_component()
    fb = cc.get_editor_property("filmback"); fb.sensor_width = 36.0; fb.sensor_height = 20.25; cc.set_editor_property("filmback", fb)
    cc.set_editor_property("current_focal_length", focal); cc.set_editor_property("current_aperture", 4.0)
    fs = cc.get_editor_property("focus_settings"); fs.focus_method = unreal.CameraFocusMethod.TRACKING
    tf = fs.get_editor_property("tracking_focus_settings"); tf.set_editor_property("actor_to_track", focus_actor); tf.set_editor_property("relative_offset", V(0, 0, 100))
    fs.set_editor_property("tracking_focus_settings", tf); fs.set_editor_property("smooth_focus_changes", True); cc.set_editor_property("focus_settings", fs)
    b = bind(cam); t = b.add_track(unreal.MovieScene3DTransformTrack); s = t.add_section(); s.set_range(0, NF); ch = s.get_all_channels()
    for tt, pos, look in keys:
        r = unreal.MathLibrary.find_look_at_rotation(V(*pos), V(*look))
        for c, v in zip(ch[:6], (pos[0], pos[1], pos[2], 0.0, r.pitch, r.yaw)):
            k = c.add_key(unreal.FrameNumber(F(tt)), v); k.set_interpolation_mode(unreal.RichCurveInterpMode.RCIM_CUBIC)
    return b
shots = []
shots.append((0.0, 3.0, camera("Cam_Intro", [(0.0, (0, 760, 170), (0, 0, 105)), (3.0, (0, 700, 160), (0, 0, 105))], 32.0, cas)))
for key, ch_, t0 in (("fem", fem, 3.0), ("cas", cas, 21.0), ("dark", dark, 39.0)):
    shots.append((t0, t0 + TT, camera(f"Cam_TT_{key}", [(t0, (0, 400, 112), (P0[0], P0[1], 92)), (t0 + TT, (0, 330, 118), (P0[0], P0[1], 95))], 40.0, ch_)))
mid_f = (ACT[0] + TROLL[0]) / 2.0; mid_d = (DARK_A[0] + DAE1[0]) / 2.0
shots.append((10.0, 21.0, camera("Cam_Act_fem", [(10.0, (mid_f + 140, 640, 185), (mid_f, 160, 110)), (21.0, (mid_f + 90, 600, 175), (mid_f, 160, 110))], 30.0, fem)))
shots.append((28.0, 39.0, camera("Cam_Act_cas", [(28.0, (-60, 690, 200), (0, 160, 110)), (39.0, (-20, 660, 190), (0, 160, 110))], 22.0, cas)))
shots.append((46.0, 57.0, camera("Cam_Act_dark", [(46.0, (-60, 690, 200), (0, 160, 110)), (walk_t0, (-60, 690, 200), (0, 160, 110)), (walk_t1, (mid_d + 110, 590, 180), (mid_d, 160, 110)),
                                                   (57.0, (mid_d + 70, 560, 175), (mid_d, 160, 110))], 22.0, dark)))
shots.append((57.0, 60.0, camera("Cam_Outro", [(57.0, (0, 640, 160), (0, 0, 105)), (60.0, (0, 720, 175), (0, 0, 105))], 32.0, cas)))
cut = seq.add_track(unreal.MovieSceneCameraCutTrack)
for t0, t1, b in shots:
    cs = cut.add_section(); cs.set_range(F(t0), F(t1)); cs.set_camera_binding_id(seq.get_binding_id(b) if hasattr(seq, "get_binding_id") else b.get_binding_id())
eal.save_loaded_asset(seq, False)
les.save_current_level()
os.makedirs(os.path.dirname(PLAN), exist_ok=True)
json.dump({"fps": FPS, "seconds": DUR, "events": events, "captions": [{"t0": a, "t1": b, "head": h, "lines": l} for a, b, h, l in caps],
           "segments": {"fem5": SEG["fem"], "caster": SEG["cas"], "dark": SEG["dark"]},
           "spell": {k: SP[k] for k in ("bolt_speed", "bolt", "bolt_scale", "charge", "charge_scale", "burst", "burst_scale", "burst_flame", "burst_flame_scale", "burst_flame_seconds", "light_cd")},
           "hits": {"troll": [round(x, 3) for x in troll_hits], "mutant": [round(x, 3) for x in mut_hits], "daemon": [round(x, 3) for x in dae_hits]}}, open(PLAN, "w"), indent=1)
print(f"TRIO stage saved {LEVEL} | sequence {SEQ} {NF} frames | Fem5 blows {len(troll_hits)} (to {fem_end:.1f} s), caster casts {sum(1 for e in events if e['who'] == 'trio_caster')} (to {cas_end:.1f} s),"
      f" dark: casts 2, walk {walk_t0:.1f}-{walk_t1:.1f} s, cuts 3 (to {dark_end:.1f} s) | {len(shots)} shots | plan {PLAN}")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
