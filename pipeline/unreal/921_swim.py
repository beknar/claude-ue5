"""Swimming (the user's of 2026-11-12: "create swimming animations for all current playable classes that are found in the choose a
hero menu. create a splash sound for when a player falls into the water or is swimming. have water displacement and a wake for
when the player moves through the water"), on brokenspire. Steps (name them, comma-separated; all by default):
  clips    the "92 Animations For Warrior" pack's treading idle (Anim_Idle_Swim) and in-place swim loop (Anim_Swim) on its UE4
           mannequin, retargeted onto each hero's rig as 913's rider clips are (an IK rig on the pack's mannequin, a retargeter per
           hero onto IK_JRPG_<rig>_Auto) into /Game/RandomDungeon/Swim/Anims/<rig>; their root locked
  sounds   the water's sounds from SourceArt/brokenspire/water.json (Player.Splash, Player.Swim, Player.Wade), converted first by
           `python pipeline/blender_numpy/rdc_sound_prep.py claude_ue5/SourceArt/brokenspire/water.json claude_ue5/SourceArt/brokenspire/audio_water`,
           imported into /Game/RandomDungeon/Audio/Water and added to the level's Sounds (the rest of the table kept)
  level    brokenspire's SwimClips by hero, the ripples' parameter collection (887 materials makes MPC_RD_Water and the water's
           material that reads it), the swimming's numbers
C++ first (RD/RDSwim.cpp); then `887_wilderness.py materials` (the water's ripples). Args: [clips,sounds,level]"""
import os, sys, json, unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()
STEPS = [s for a in sys.argv[1:] for s in a.split(",") if s] or ["clips", "sounds", "level"]
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
MAP = "/Game/RandomDungeon/Maps/brokenspire"
RIGS = "/Game/RandomDungeon/Swim/Rigs"; ANIMS = "/Game/RandomDungeon/Swim/Anims"
# (the hero menu's six and their rigs, and the retarget onto them: hero_rigs.py, shared with 913 and 922)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hero_rigs, importlib
importlib.reload(hero_rigs)
HERO_RIG = hero_rigs.HERO_RIG
SRC = "/Game/Animations_Warrior"
SWIM = {"Idle": f"{SRC}/Animations/Without_Weapon/Anim_Idle_Swim", "Swim": f"{SRC}/Animations/Without_Weapon/Anim_Swim"}
REPORT = []


def generator():
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."):
        les.load_level(MAP); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


if "clips" in STEPS:
    clips = {k: unreal.load_asset(p) for k, p in SWIM.items()}
    assert all(clips.values()), f"the pack's swim clips: {clips}"
    src_mesh = unreal.load_asset(f"{SRC}/Mesh/SK_Mannequin"); assert src_mesh, "the pack's mannequin"
    for hero, (ch, made, why) in hero_rigs.retarget_onto_heroes(src_mesh, list(SWIM.values()), RIGS, ANIMS, "Swim", "SWIM").items():
        REPORT.append(f"clips {hero}: {why}" if why else f"clips {hero} ({ch}): {[a.get_name().rsplit('_' + ch, 1)[0] + f' {a.get_play_length():.2f} s' for a in made]}")

if "sounds" in STEPS:
    aud = os.path.join(SA, "brokenspire", "audio_water")
    idx = os.path.join(aud, "index.json")
    assert os.path.exists(idx), "run rdc_sound_prep.py SourceArt/brokenspire/water.json SourceArt/brokenspire/audio_water first"
    I = json.load(open(idx, encoding="utf-8"))
    J = json.load(open(os.path.join(SA, "brokenspire", "water.json"), encoding="utf-8"))
    dest = "/Game/RandomDungeon/Audio/Water"
    if not eal.does_directory_exist(dest): eal.make_directory(dest)
    g = generator()
    snd = g.get_editor_property("sounds")
    for key, spec in J["sets"].items():
        waves = []
        for f in I.get(key, {}).get("files", []):
            t = unreal.AssetImportTask(); t.set_editor_property("filename", os.path.join(aud, f)); t.set_editor_property("destination_path", dest)
            t.set_editor_property("destination_name", "SW_" + f[:-4]); t.set_editor_property("replace_existing", True); t.set_editor_property("automated", True)
            at.import_asset_tasks([t])
            w = unreal.load_asset(f"{dest}/SW_{f[:-4]}")
            if w: w.set_editor_property("looping", False); eal.save_loaded_asset(w, False); waves.append(w)
        if not waves: REPORT.append(f"sounds: no files for {key}"); continue
        # (every field of the set, as 797 writes them: 890's music left the placed sets' radii at their defaults)
        s = unreal.RDSoundSet(); s.set_editor_property("sounds", waves)
        s.set_editor_property("volume", float(spec.get("volume", 1.0))); s.set_editor_property("pitch", float(spec.get("pitch", 1.0)))
        s.set_editor_property("pitch_variation", float(spec.get("pitch_var", 0.05))); s.set_editor_property("inner_radius", float(spec.get("inner", 200.0)))
        s.set_editor_property("falloff_distance", float(spec.get("falloff", 2500.0))); s.set_editor_property("b2d", bool(spec.get("flat", False)))
        snd[unreal.Name(key)] = s
    g.set_editor_property("sounds", snd); g.modify(); les.save_current_level()
    REPORT.append("sounds: " + ", ".join(f"{k} {len(snd[unreal.Name(k)].sounds)}" for k in J["sets"] if unreal.Name(k) in snd))
    del g, snd

if "level" in STEPS:
    g = generator()
    sc = {}
    for hero, ch in HERO_RIG.items():
        r = unreal.RDSwimClips()
        for k, p in SWIM.items():
            r.set_editor_property(k.lower(), unreal.load_asset(f"{ANIMS}/{ch}/{p.rsplit('/', 1)[-1]}_{ch}"))
        sc[hero] = r
    g.set_editor_property("swim_clips", sc)
    mpc = unreal.load_asset("/Game/RandomDungeon/Wild/MPC_RD_Water")
    g.set_editor_property("water_ripples", mpc)
    g.modify(); les.save_current_level()
    missing = [h for h, r in sc.items() if not r.get_editor_property("idle") or not r.get_editor_property("swim")]
    REPORT.append(f"level: swim clips for {sorted(sc)} (missing {missing}), ripples {mpc.get_name() if mpc else 'MISSING (887 materials first)'}")
    del g

print("921 " + " | ".join(REPORT))
import gc; gc.collect()
