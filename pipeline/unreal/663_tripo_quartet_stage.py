"""Tripo quartet showcase: the trio showcase (660) with the Rogue: one 78 s reel of the four animated Tripo characters
(Warrior = jrpg-fem5-tripo, Mage = girl-caster-tripo, Warlock = girl-darkcaster-tripo, Rogue). Builds
/Game/JRPG/Maps/L_Tripo_Quartet_Showcase (the same studio, plinth and light rig as the trio's) and the Level Sequence
/Game/JRPG/Cinematics/LS_Tripo_Quartet_Showcase:
   0-3 s    the four side by side
   3-21     Fem5: turntable, then the sword, spear and axe on a troll (as in the trio)
   21-39    the caster: turntable, then six casts at a mutant
   39-57    the dark caster: turntable, two casts at a daemon, which walks up to her and falls to her sword
   57-75    the Rogue: turntable (daggers drawn, the crossbow on her back), then a horned beast swings at her, she rolls
            back out of its blow, draws the crossbow and puts two bolts in it, draws the daggers as it comes on and kills
            it with three strikes
   75-78    the four again
The weapons she does not hold hang where the game carries them (822's holsters: the crossbow across her back, the daggers
on her thighs); the bolt lies on the crossbow until the shot and again once she has reloaded. The roll is her clip in
place while the sequence moves her back the game's RollDistance over 0.82 of the clip (RDCombat's constant force). The
bolts, their trails and the impacts are not in the sequence: the pilot (661 quartet) moves the two bolt actors placed
here (tags trio_bolt_0 / 1) from the crossbow's muzzle to the beast at the crossbow's speed while the queue renders, and
spawns the fire of the casters as for the trio. Times: SourceArt/tripo_quartet/plan.json (with the captions for the
overlay). Reads the monsters from random_dungeoncombat_level's generator, so that level is opened first. Idempotent
(actors tagged `trio`, the sequence rebuilt). Args: none"""
import json, math, os, unreal
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
V = unreal.Vector; Rot = unreal.Rotator
LEVEL = "/Game/JRPG/Maps/L_Tripo_Quartet_Showcase"; SEQ = "/Game/JRPG/Cinematics/LS_Tripo_Quartet_Showcase"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
PLAN = SA + r"\tripo_quartet\plan.json"
FPS = 30; DUR = 78.0; NF = int(DUR * FPS); TAG = unreal.Name("trio")
EASE = 0.12                  # seconds two animation sections blend over
# ---------------------------------------------------------------- data: monsters, weapons, clips
COMBAT = "/Game/RandomDungeon/Maps/random_dungeoncombat_level"
if not ues.get_editor_world().get_path_name().startswith(COMBAT + "."): unreal.EditorLoadingAndSavingUtils.load_map(COMBAT)
gen = unreal.GameplayStatics.get_all_actors_of_class(ues.get_editor_world(), unreal.RDDungeonGenerator)[0]
MON = {}
for d in gen.get_editor_property("monsters"):
    if str(d.name) in ("Troll", "Mutant", "Daemon", "Horned"):
        b = d.mesh.get_bounds()
        MON[str(d.name)] = {"mesh": d.mesh.get_path_name(), "idle": d.idle.get_path_name(), "walk": d.walk.get_path_name(), "walk_speed": d.walk_clip_speed,
                            "hit": d.get_hit.get_path_name(), "death": d.death.get_path_name(), "zmin": b.origin.z - b.box_extent.z, "radius": d.capsule_radius,
                            "attack": d.attacks[0].get_path_name() if d.attacks else None, "attack_hit": d.hit_times[0] if d.hit_times else 0.0}
ROLL_DIST = gen.get_editor_property("roll_distance")
del gen
W1 = json.load(open(SA + r"\random_dungeon_combat\weapons.json"))
SP = json.load(open(SA + r"\random_dungeon_magic\spell.json"))
W2 = json.load(open(SA + r"\random_dungeon_magic2\weapons.json"))
W3 = json.load(open(SA + r"\random_dungeon_magic3\weapons.json"))
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
rog = skel("/Game/JRPG/Character/SK_JRPG_Rogue", (0, 0, 0), 0, "Rogue", ("trio_rogue",))
def xf(d): return unreal.Transform(V(*d["loc"]), Rot(roll=d["rot"][0], pitch=d["rot"][1], yaw=d["rot"][2]), V(*d["scale"]))
def held(path, owner, bone, grip, label, tags=()):
    a = mesh_actor(path, (0, 0, 0), label=label, tags=tags); a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    a.attach_to_component(owner.skeletal_mesh_component, bone, unreal.AttachmentRule.SNAP_TO_TARGET, unreal.AttachmentRule.SNAP_TO_TARGET, unreal.AttachmentRule.KEEP_WORLD, False)
    a.set_actor_relative_transform(xf(grip), False, False); return a
WP = {}
for name in W1["order"]:
    e = W1["weapons"][name]
    WP[name] = [held(e["mesh"], fem, e["hand_bone"], e["grip"], f"Fem5_{name}")]
    if e["shield"]: WP[name].append(held(e["shield"], fem, e["shield_bone"], e["shield_grip"], f"Fem5_{name}_Shield"))
dsw = W2["weapons"]["Sword"]; dark_sword = held(dsw["mesh"], dark, dsw["hand_bone"], dsw["grip"], "Dark_Sword")
# the Rogue's weapons: each in her hands and where she carries it (822's grips and holsters)
RD, RC = W3["weapons"]["Daggers"], W3["weapons"]["Crossbow"]
r_dag = [held(RD["mesh"], rog, RD["hand_bone"], RD["grip"], "Rogue_Dagger_R"), held(RD["off_mesh"], rog, RD["off_bone"], RD["off_grip"], "Rogue_Dagger_L")]
r_dag_h = [held(RD["mesh"], rog, RD["holster_bone"], RD["holster"], "Rogue_Dagger_R_Holster"), held(RD["off_mesh"], rog, RD["off_holster_bone"], RD["off_holster"], "Rogue_Dagger_L_Holster")]
r_xb = held(RC["mesh"], rog, RC["hand_bone"], RC["grip"], "Rogue_Crossbow", ("trio_rogue_crossbow",))
r_xb_h = held(RC["mesh"], rog, RC["holster_bone"], RC["holster"], "Rogue_Crossbow_Holster")
loaded = mesh_actor(RC["bolt_mesh"], (0, 0, 0), label="Rogue_Loaded_Bolt"); loaded.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
loaded.attach_to_component(r_xb.static_mesh_component, "", unreal.AttachmentRule.SNAP_TO_TARGET, unreal.AttachmentRule.SNAP_TO_TARGET, unreal.AttachmentRule.KEEP_WORLD, False)
loaded.set_actor_relative_transform(xf(RC["loaded_xf"]), False, False)
OFF = (0.0, 4000.0, 0.0)          # (where a hidden actor waits: far off the stage, behind the cameras)
bolts = []
for i in range(2):                # (the pilot moves them: Python cannot spawn actors into the render's world)
    b_ = mesh_actor(RC["bolt_mesh"], OFF, label=f"Rogue_Bolt_{i}", tags=(f"trio_bolt_{i}",)); b_.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    b_.static_mesh_component.set_editor_property("cast_shadow", False); bolts.append(b_)
mons = {}
for n in ("Troll", "Mutant", "Daemon", "Horned"):
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
def bridge(items):
    """no frame without a clip: a frame that no section covers shows the T-pose (it did, in every pause between two casts,
    shots or blows). An action clip (one that does not loop: idles and walks do) plays on into the pause after it and the
    blend into the next clip as far as it has frames, and its last frame is held from there (a section past the end of its
    clip starts it again)."""
    out = []
    for i, (t0, t1, clip, rate, off) in enumerate(items):
        nxt = items[i + 1][0] if i + 1 < len(items) else None
        if nxt is None: out.append((t0, t1, clip, rate, off)); continue
        n = clip_len(clip); last = n - 0.05        # (a frame and a half of margin: both ends are rounded to frames)
        if (t1 - t0) * rate > n - off: out.append((t0, max(t1, nxt), clip, rate, off)); continue        # (a loop: it covers the pause itself)
        end = min(nxt, max(t0 + EASE, t0 + (last - off) / rate - EASE))
        if F(end) >= F(nxt): end = nxt                    # (a hold under a frame long: none, or this one's blend out ends a frame off the next one's blend in)
        out.append((t0, end, clip, rate, off))
        if end < nxt: out.append((end, nxt, clip, 0.0001, last))
    return out
def animate(a, items):
    """items: (t0, t1, clip path, play rate, start offset s) one after another; each section blends into the next over EASE"""
    items = bridge(items)
    t = bind(a).add_track(unreal.MovieSceneSkeletalAnimationTrack)
    EF = int(round(EASE * FPS)); rows = []; made = []     # (a blend of whole frames, ending EF after the frame the next section starts on: one section's
    for i, (t0, t1, clip, rate, off) in enumerate(items):  # blend out and the next one's blend in then sum to 1; a frame apart they dipped to 0.83)
        f0, f1 = F(t0), F(t1) + (EF if i < len(items) - 1 else 0)
        row = next((r for r, e in enumerate(rows) if e <= f0), len(rows))       # (two sections on one row must not overlap: Unreal trims one)
        if row == len(rows): rows.append(f1)
        else: rows[row] = f1
        s = t.add_section(); s.set_row_index(row)
        s.set_range(f0, f1); made.append((s, f0, f1))
        p = s.get_editor_property("params"); p.set_editor_property("animation", L(clip))
        pr = unreal.MovieSceneTimeWarpVariant(); pr.set_fixed_play_rate(rate); p.set_editor_property("play_rate", pr)      # (5.8: the play rate is a time warp)
        if off: p.set_editor_property("first_loop_start_frame_offset", unreal.FrameNumber(int(off * TICKS)))
        s.set_editor_property("params", p)
        e = unreal.MovieSceneEasingSettings(); n_ = int(round(EF * TICKS / FPS))        # (set as text: one of the two flags is not reachable by name from Python)
        e.import_text("(bManualEaseIn=%s,ManualEaseInDuration=%d,bManualEaseOut=%s,ManualEaseOutDuration=%d)" % (i > 0, n_ if i > 0 else 0, i < len(items) - 1, n_ if i < len(items) - 1 else 0))
        s.set_editor_property("easing", e)
    for s, f0, f1 in made:              # (a section followed by one of the same clip (its hold) came out ending where that one starts: the ranges again, checked)
        s.set_range(f0, f1)
    for s, f0, f1 in made:
        if (s.get_start_frame(), s.get_end_frame()) != (f0, f1): print("QUARTET section range", a.get_actor_label(), (f0, f1), "is", (s.get_start_frame(), s.get_end_frame()))
P0, PZ = (0, -40), 6.0            # the plinth's middle, its top
events = []; caps = []
def turntable(t0, t1):
    """on the plinth, one full turn from facing the camera (linear between the keys)"""
    return [(t0, (P0[0], P0[1], PZ), 0.0, "l"), (t1 - 1.0 / FPS, (P0[0], P0[1], PZ), 360.0 * (1.0 - 1.0 / (FPS * (t1 - t0))))]      # (the last key a frame before the next jump)
# ---- intro / outro: the four in a row in front of the plinth, facing the camera (a Tripo character faces +Y at yaw 0)
ROW = {"fem": ((-270, 70, 0), 0.0), "cas": ((-90, 70, 0), 0.0), "dark": ((90, 70, 0), 0.0), "rog": ((270, 70, 0), 0.0)}
SEG = {"fem": (3.0, 21.0), "cas": (21.0, 39.0), "dark": (39.0, 57.0), "rog": (57.0, 75.0)}; TT = 7.0; OUT0 = 75.0
# ---- Fem5: turntable, then the three weapons on the troll
ACT = (-120, 160, 0)
place(fem, [(0.0, ROW["fem"][0], 0.0)] + turntable(3.0, 10.0) + [(10.0, ACT, -90.0), (21.0, OFF, 0.0), (OUT0, ROW["fem"][0], 0.0)])
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
items.append((tcur, DUR, idle_f, 1.0, 0.0))
animate(fem, items)
fem_end = tcur
vis_w["Sword"] = [(0.0, vis_w["Sword"][0][1])] + [(fem_end, DUR)]       # (sword and shield in the turntable, the intro and the outro too)
for name, acts in WP.items():
    for a in acts: visibility(a, vis_w[name])
visibility(fem, [(0.0, 21.0), (OUT0, DUR)])
caps += [(3.2, 9.8, "WARRIOR", ["the player of the procedural levels  \u00b7  her own idle, walk and run"]),
         (10.2, fem_end + 0.3, "SWORD  \u00b7  SPEAR  \u00b7  AXE", ["the attack clips of three Fab animation packs, retargeted to her  \u00b7  the weapons of random_dungeoncombat_level"])]
# the troll: across from her, a flinch at every blow, death at the last
TROLL = (ACT[0] + 150, ACT[1], -MON["Troll"]["zmin"])          # (its hit clips knock it back: it stands close)
place(mons["Troll"], [(0.0, OFF, 0), (10.0, TROLL, 90.0), (21.0, OFF, 0)])
visibility(mons["Troll"], [(10.0, 21.0)])
def reactions(m, start, end, hits, dies=True, walk=None, attack=None):
    """idle, a flinch at each hit, death at the last one (it lies still till the end); walk = (t0, t1) of a walk after
    the hits before it; attack = (t0, t1) of its attack clip"""
    d = MON[m]; it = []; t = start; hl = clip_len(d["hit"]); dl = clip_len(d["death"])
    plan = [("hit", h) for h in hits] + ([("walk", walk[0])] if walk else []) + ([("attack", attack[0])] if attack else [])
    plan.sort(key=lambda p: p[1]); n_hits = len(hits); seen = 0
    for kind, h in plan:
        if h > t: it.append((t, h, d["idle"], 1.0, 0.0))
        if kind == "attack":
            it.append((h, attack[1], d["attack"], 1.0, 0.0)); t = attack[1]; continue
        if kind == "walk":
            it.append((h, walk[1], d["walk"], 1.0, 0.0)); t = walk[1]; continue
        seen += 1; last = dies and seen == n_hits
        if last:
            it.append((h, h + dl - 0.05, d["death"], 1.0, 0.0)); it.append((h + dl - 0.05, end, d["death"], 0.0001, max(0.0, dl - 0.06))); t = end; break
        nxt = min([p[1] for p in plan if p[1] > h] + [end])
        it.append((h, min(h + hl, nxt), d["hit"], 1.0, 0.0)); t = min(h + hl, nxt)
    if t < end: it.append((t, end, d["idle"], 1.0, 0.0))
    animate(mons[m], it)
reactions("Troll", 0.0, DUR, troll_hits)
# ---- the caster: turntable, then six casts at the mutant
CAS_A, MUT = (-330, 160, 0), (330, 160, -MON["Mutant"]["zmin"])
place(cas, [(0.0, ROW["cas"][0], 0.0), (3.0, OFF, 0.0)] + turntable(21.0, 28.0) + [(28.0, CAS_A, -90.0), (39.0, OFF, 0.0), (OUT0, ROW["cas"][0], 0.0)])
idle_c = "/Game/JRPG/CasterAnims/AS_Caster_Idle"
items = [(0.0, 28.6, idle_c, 1.0, 0.0)]; tcur = 28.6; mut_hits = []
dist = abs(MUT[0] - CAS_A[0]) - MON["Mutant"]["radius"] - 30.0
for k in [0, 1, 2, 0, 2, 1]:
    c = SP["casts"][k]; dur = c["end"] / SP["rate"]; rel = tcur + c["hit"] / SP["rate"]
    items.append((tcur, tcur + dur, c["clip"], SP["rate"], 0.0))
    events.append({"kind": "cast", "who": "trio_caster", "hand": SP["bone"], "charge": round(tcur + 0.05, 3), "release": round(rel, 3), "target": "trio_mutant"})
    mut_hits.append(rel + dist / SP["bolt_speed"]); tcur += dur + 0.35
items.append((tcur, DUR, idle_c, 1.0, 0.0)); animate(cas, items); cas_end = tcur
place(mons["Mutant"], [(0.0, OFF, 0), (28.0, MUT, 90.0), (39.0, OFF, 0)]); visibility(mons["Mutant"], [(28.0, 39.0)]); visibility(cas, [(0.0, 3.0), (21.0, 39.0), (OUT0, DUR)])
reactions("Mutant", 0.0, DUR, mut_hits)
caps += [(21.2, 27.8, "MAGE", ["her own walk and run  \u00b7  an idle and three casts made for her in Blender (caster_clips.py)"]),
         (28.2, cas_end + 0.3, "FIRE SPELL", ["sparks gather on her hand, the bolt leaves at the release and bursts on the mutant  \u00b7  the fire effects of docs/magic.md"])]
# ---- the dark caster: turntable, two casts at the daemon, it walks up, the sword
DARK_A, DAE0 = (-330, 160, 0), (330, 160, -MON["Daemon"]["zmin"])
place(dark, [(0.0, ROW["dark"][0], 0.0), (3.0, OFF, 0.0)] + turntable(39.0, 46.0) + [(46.0, DARK_A, -90.0), (57.0, OFF, 0.0), (OUT0, ROW["dark"][0], 0.0)])
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
DAE1 = (DARK_A[0] + 140, DAE0[1], DAE0[2]); dwalk_t0 = dae_hits[-1] + 0.55; dwalk_t1 = dwalk_t0 + (DAE0[0] - DAE1[0]) / MON["Daemon"]["walk_speed"]
items.append((tcur, dwalk_t1, idle_d, 1.0, 0.0)); tcur = dwalk_t1
for k in (0, 1, 2):
    a_ = sw["attacks"][k]; dur = a_["end"] / sw["rate"]
    items.append((tcur, tcur + dur, a_["clip"], sw["rate"], 0.0)); dae_hits.append(tcur + a_["hit"] / sw["rate"]); tcur += dur + 0.08
items.append((tcur, DUR, idle_d, 1.0, 0.0)); animate(dark, items); dark_end = tcur
place(mons["Daemon"], [(0.0, OFF, 0), (46.0, DAE0, 90.0), (dwalk_t0, DAE0, 90.0, "l"), (dwalk_t1, DAE1, 90.0), (57.0, OFF, 0)])        # (linear only while it walks)
visibility(mons["Daemon"], [(46.0, 57.0)]); visibility(dark, [(0.0, 3.0), (39.0, 57.0), (OUT0, DUR)]); visibility(dark_sword, [(0.0, 3.0), (39.0, 57.0), (OUT0, DUR)])
reactions("Daemon", 0.0, DUR, dae_hits, walk=(dwalk_t0, dwalk_t1))
caps += [(39.2, 45.8, "WARLOCK", ["her own idle, walk and run  \u00b7  the right hand closed on the sword's hilt in every clip"]),
         (46.2, dark_end + 0.3, "FIRE AND STEEL", ["two casts from her left hand, then three cuts of the sword in her right  \u00b7  all made for her in Blender (darkcaster_clips.py)"])]
# ---- the Rogue: turntable, the beast's swing and her roll, two bolts, three dagger strikes
RA = 64.0                                                    # her fight starts
R0 = (100, 160, 0); R1 = (R0[0] - ROLL_DIST, R0[1], 0)        # where she stands, where the roll takes her
HZ = -MON["Horned"]["zmin"]; H0 = (R0[0] + 170, 160, HZ); H1 = (R1[0] + 150, 160, HZ)
idle_r = "/Game/JRPG/RogueAnims/AS_Rogue_Idle"
roll_len = clip_len(W3["roll"]["back"]); roll_move = roll_len * 0.82          # (RDCombat::StartRoll: the force lasts 0.82 of the clip)
h_att0 = RA + 0.4; h_blow = h_att0 + MON["Horned"]["attack_hit"]; h_att1 = h_att0 + min(clip_len(MON["Horned"]["attack"]), MON["Horned"]["attack_hit"] + 1.0)
roll0 = h_blow - 0.3                                          # (the blow lands within the roll's dodge window)
items = [(0.0, roll0, idle_r, 1.0, 0.0), (roll0, roll0 + roll_len, W3["roll"]["back"], 1.0, 0.0)]
tcur = roll0 + roll_len; draw_xb = tcur + 0.1
items.append((tcur, tcur + 0.25, idle_r, 1.0, 0.0)); tcur += 0.25
shot = RC["attacks"][0]; hor_hits = []; shots = []
dist = abs(H0[0] - R1[0]) - MON["Horned"]["radius"] - 30.0
for i in range(2):
    rel = tcur + shot["hit"]
    items.append((tcur, tcur + shot["end"], shot["clip"], 1.0, 0.0)); shots.append((tcur, rel, tcur + shot["end"]))
    events.append({"kind": "bolt", "who": "trio_rogue", "weapon": "trio_rogue_crossbow", "bolt": f"trio_bolt_{i}", "release": round(rel, 3), "target": "trio_horned"})
    hor_hits.append(rel + dist / RC["bolt_speed"]); tcur += shot["end"] + 0.3
draw_dag = tcur + 0.15
walk_t0 = hor_hits[-1] + 0.8; walk_t1 = walk_t0 + (H0[0] - H1[0]) / MON["Horned"]["walk_speed"]
items.append((tcur, walk_t1, idle_r, 1.0, 0.0)); tcur = walk_t1
for k in (0, 1, 2):
    a_ = RD["attacks"][k]; dur = a_["end"] / RD["rate"]
    items.append((tcur, tcur + dur, a_["clip"], RD["rate"], 0.0)); hor_hits.append(tcur + a_["hit"] / RD["rate"]); tcur += dur + 0.08
items.append((tcur, DUR, idle_r, 1.0, 0.0)); animate(rog, items); rog_end = tcur
place(rog, [(0.0, ROW["rog"][0], 0.0), (3.0, OFF, 0.0)] + turntable(57.0, 64.0) +
      [(RA, R0, -90.0), (roll0, R0, -90.0, "l"), (roll0 + roll_move, R1, -90.0), (OUT0, ROW["rog"][0], 0.0)])
visibility(rog, [(0.0, 3.0), (57.0, DUR)])
dag_in = [(0.0, 3.0), (57.0, draw_xb), (draw_dag, DUR)]; xb_in = [(draw_xb, draw_dag)]
for a in r_dag: visibility(a, dag_in)
for a in r_dag_h: visibility(a, xb_in)
visibility(r_xb, xb_in); visibility(r_xb_h, dag_in)
visibility(loaded, [(draw_xb, shots[0][1]), (shots[0][2], shots[1][1]), (shots[1][2], draw_dag)])      # (on the rail until the release, back once reloaded)
place(mons["Horned"], [(0.0, OFF, 0), (RA, H0, 90.0), (walk_t0, H0, 90.0, "l"), (walk_t1, H1, 90.0), (OUT0, OFF, 0)])
visibility(mons["Horned"], [(RA, OUT0)])
reactions("Horned", 0.0, DUR, hor_hits, walk=(walk_t0, walk_t1), attack=(h_att0, h_att1))
caps += [(57.2, 63.8, "ROGUE", ["her own walk and run  \u00b7  an idle, three dagger strikes, a crossbow shot and a roll made for her in Blender (rogue_clips.py)"]),
         (RA + 0.2, rog_end + 0.3, "ROLL  \u00b7  CROSSBOW  \u00b7  DAGGERS", ["she rolls back out of the blow, two bolts, then three strikes  \u00b7  the weapons of random_dungeonmagic_level3"])]
caps += [(OUT0 + 0.2, DUR - 0.1, "FOUR TRIPO CHARACTERS", ["Warrior  \u00b7  Mage  \u00b7  Warlock  \u00b7  Rogue"])]
# the plinth turns with each turntable
pk = [(0.0, (P0[0], P0[1], 0.0), 0.0)]
for c0 in (3.0, 21.0, 39.0, 57.0): pk += [(c0, (P0[0], P0[1], 0.0), 0.0, "l"), (c0 + TT - 1.0 / FPS, (P0[0], P0[1], 0.0), 360.0 * (1.0 - 1.0 / (FPS * TT)))]
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
# (the Warlock's and the Rogue's close shots look from the left of the pair, into the backdrop: the trio's from the right saw past its left edge)
cams = []
cams.append((0.0, 3.0, camera("Cam_Intro", [(0.0, (0, 780, 170), (0, 0, 105)), (3.0, (0, 720, 160), (0, 0, 105))], 28.0, cas)))
for key, ch_, t0 in (("fem", fem, 3.0), ("cas", cas, 21.0), ("dark", dark, 39.0), ("rog", rog, 57.0)):
    cams.append((t0, t0 + TT, camera(f"Cam_TT_{key}", [(t0, (0, 400, 112), (P0[0], P0[1], 92)), (t0 + TT, (0, 330, 118), (P0[0], P0[1], 95))], 40.0, ch_)))
mid_f = (ACT[0] + TROLL[0]) / 2.0; mid_d = (DARK_A[0] + DAE1[0]) / 2.0; mid_r0 = (R1[0] + H0[0]) / 2.0; mid_r1 = (R1[0] + H1[0]) / 2.0
cams.append((10.0, 21.0, camera("Cam_Act_fem", [(10.0, (mid_f + 140, 640, 185), (mid_f, 160, 110)), (21.0, (mid_f + 90, 600, 175), (mid_f, 160, 110))], 30.0, fem)))
cams.append((28.0, 39.0, camera("Cam_Act_cas", [(28.0, (-60, 690, 200), (0, 160, 110)), (39.0, (-20, 660, 190), (0, 160, 110))], 22.0, cas)))
cams.append((46.0, 57.0, camera("Cam_Act_dark", [(46.0, (-60, 690, 200), (0, 160, 110)), (dwalk_t0, (-60, 690, 200), (0, 160, 110)), (dwalk_t1, (mid_d - 110, 590, 180), (mid_d, 160, 110)),
                                                  (57.0, (mid_d - 70, 560, 175), (mid_d, 160, 110))], 22.0, dark)))
cams.append((RA, OUT0, camera("Cam_Act_rog", [(RA, (mid_r0 + 40, 700, 200), (mid_r0, 160, 110)), (walk_t0, (mid_r0 + 40, 700, 200), (mid_r0, 160, 110)),
                                               (walk_t1, (mid_r1 - 110, 590, 180), (mid_r1, 160, 110)), (OUT0, (mid_r1 - 70, 560, 175), (mid_r1, 160, 110))], 22.0, rog)))
cams.append((OUT0, DUR, camera("Cam_Outro", [(OUT0, (0, 680, 160), (0, 0, 105)), (DUR, (0, 760, 175), (0, 0, 105))], 28.0, cas)))
cut = seq.add_track(unreal.MovieSceneCameraCutTrack)
for t0, t1, b in cams:
    cs = cut.add_section(); cs.set_range(F(t0), F(t1)); cs.set_camera_binding_id(seq.get_binding_id(b) if hasattr(seq, "get_binding_id") else b.get_binding_id())
def coverage():
    """read back from the sequence: each animated actor's frames whose section weights (ease in x ease out, linear) sum
    below 0.98 (it shows its T-pose there), and the action sections that play past the end of their clip"""
    import re
    bad = []
    for b in seq.get_bindings():
        for trk in b.get_tracks():
            if not isinstance(trk, unreal.MovieSceneSkeletalAnimationTrack): continue
            secs = []
            for s in trk.get_sections():
                p = s.get_editor_property("params"); et = s.get_editor_property("easing").export_text()     # (bManualEaseOut is not reachable by name)
                g = lambda k: re.search(k + r"=(\w+)", et).group(1)
                ein = int(g("ManualEaseInDuration")) * FPS / TICKS if g("bManualEaseIn") == "True" else 0.0
                eout = int(g("ManualEaseOutDuration")) * FPS / TICKS if g("bManualEaseOut") == "True" else 0.0
                clip = p.get_editor_property("animation"); rate = p.get_editor_property("play_rate").to_fixed_play_rate()
                secs.append((s.get_start_frame(), s.get_end_frame(), ein, eout, clip.get_name(), rate,
                             p.get_editor_property("first_loop_start_frame_offset").value / TICKS, unreal.AnimationLibrary.get_sequence_length(clip)))
            low = [f for f in range(NF) if sum((min(1.0, (f + 0.5 - f0) / ei) if ei else 1.0) * (min(1.0, (f1 - f - 0.5) / eo) if eo else 1.0)
                                               for f0, f1, ei, eo, *_ in secs if f0 <= f + 0.5 < f1) < 0.98]
            over = [(nm, f0) for f0, f1, ei, eo, nm, rate, off, n in secs if (f1 - f0) * rate < n * FPS and off + (f1 - f0) / FPS * rate > n + 0.005]
            if low or over: bad.append(f"{b.get_display_name()}: {len(low)} frames under full weight from {low[:1]}, past clip end {over[:2]}")
    return bad
uncovered = coverage()
for line in uncovered: print("QUARTET coverage", line)
eal.save_loaded_asset(seq, False)
les.save_current_level()
os.makedirs(os.path.dirname(PLAN), exist_ok=True)
json.dump({"fps": FPS, "seconds": DUR, "events": events, "captions": [{"t0": a, "t1": b, "head": h, "lines": l} for a, b, h, l in caps],
           "segments": {"fem5": SEG["fem"], "caster": SEG["cas"], "dark": SEG["dark"], "rogue": SEG["rog"]},
           "spell": {k: SP[k] for k in ("bolt_speed", "bolt", "bolt_scale", "charge", "charge_scale", "burst", "burst_scale", "burst_flame", "burst_flame_scale", "burst_flame_seconds", "light_cd")},
           "crossbow": {"speed": RC["bolt_speed"], "muzzle": RC["muzzle"], "bolt_xf": RC["bolt_xf"], "trail": RC["trail"], "trail_scale": RC["trail_scale"],
                        "hit_fx": RC["hit_fx"], "hit_scale": RC["hit_scale"]},
           "rogue": {"roll": [round(roll0, 3), round(roll0 + roll_len, 3)], "roll_move": round(roll_move, 3), "roll_distance": ROLL_DIST, "blow": round(h_blow, 3),
                     "dodge": [round(roll0 + 0.05 * roll_len, 3), round(roll0 + 0.75 * roll_len, 3)], "crossbow_drawn": [round(draw_xb, 3), round(draw_dag, 3)],
                     "shots": [[round(x, 3) for x in s_] for s_ in shots], "walk": [round(walk_t0, 3), round(walk_t1, 3)]},
           "hits": {"troll": [round(x, 3) for x in troll_hits], "mutant": [round(x, 3) for x in mut_hits], "daemon": [round(x, 3) for x in dae_hits],
                    "horned": [round(x, 3) for x in hor_hits]}}, open(PLAN, "w"), indent=1)
print(f"QUARTET stage saved {LEVEL} | sequence {SEQ} {NF} frames | Fem5 blows {len(troll_hits)} (to {fem_end:.1f} s), caster casts {sum(1 for e in events if e['who'] == 'trio_caster')} (to {cas_end:.1f} s),"
      f" dark to {dark_end:.1f} s | Rogue: blow {h_blow:.2f} in roll {roll0:.2f}-{roll0 + roll_len:.2f}, bolts {[s_[1] for s_ in shots]}, walk {walk_t0:.1f}-{walk_t1:.1f}, to {rog_end:.1f} s | {len(cams)} shots | animation on every frame: {'yes' if not uncovered else 'NO, ' + str(len(uncovered)) + ' actors'} | plan {PLAN}")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
