"""random_dungeoncombat_level: sound. Imports the WAV files prepared by pipeline/blender_numpy/rdc_sound_prep.py
(claude_ue5/SourceArt/random_dungeon_combat/audio, listed in its index.json) into /Game/RandomDungeon/Audio and fills
the generator from claude_ue5/SourceArt/random_dungeon_combat/sounds.json:
  Sounds     one FRDSoundSet per occasion ("Player.Hurt", "Monster.Troll.Roar", "Env.DoorOpen", "Env.Torch"...): its
             sound waves, volume, pitch and pitch variation, and how it fades with distance (inner radius, falloff;
             "flat" sets are not placed in the world: her own steps and voice, the music and atmosphere layers)
  SoundVolume  the manifest's master_volume; MusicVolume its music_volume (on the Music.* and Atmos.* sets)
  Monsters   each kind's SoundSet (which "Monster.<set>.*" it uses) and StepLength (ground covered per footstep)
Run with random_dungeoncombat_level open, after the C++ build. Idempotent: the waves are imported over the old ones,
waves that are no longer in the index are deleted. Args: none (or "noimport": only the generator data)."""
import gc, json, os, sys, unreal

SRC = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "SourceArt", "random_dungeon_combat")
DEST = "/Game/RandomDungeon/Audio"
eal = unreal.EditorAssetLibrary
man = json.load(open(os.path.join(SRC, "sounds.json"), encoding="utf-8"))
index = json.load(open(os.path.join(SRC, "audio", "index.json"), encoding="utf-8"))
IMPORT = "noimport" not in sys.argv

w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
gens = list(unreal.GameplayStatics.get_all_actors_of_class(w, unreal.RDDungeonGenerator))
assert len(gens) == 1 and gens[0].get_editor_property("combat"), "open random_dungeoncombat_level"
gen = gens[0]

wanted = {}
for key, e in index.items():
    for f in e["files"]: wanted[os.path.splitext(f)[0]] = (key, os.path.join(SRC, "audio", f))
if IMPORT:
    tasks = []
    for name, (key, path) in sorted(wanted.items()):
        t = unreal.AssetImportTask()
        t.set_editor_property("filename", path); t.set_editor_property("destination_path", DEST); t.set_editor_property("destination_name", name)
        t.set_editor_property("automated", True); t.set_editor_property("replace_existing", True); t.set_editor_property("save", False)
        tasks.append(t)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    # waves of an earlier run that are gone from the index
    for p in eal.list_assets(DEST, recursive=False):
        n = p.split("/")[-1].split(".")[0]
        if n not in wanted: eal.delete_asset(p.split(".")[0]); print("removed", n)

sounds = {}; missing = []; nwaves = 0
for key, s in man["sets"].items():
    waves = []
    for f in index.get(key, {}).get("files", []):
        wave = unreal.load_asset(DEST + "/" + os.path.splitext(f)[0])
        if not wave: missing.append(f); continue
        if IMPORT:
            wave.set_editor_property("looping", bool(s.get("loop")))
            eal.save_loaded_asset(wave, only_if_is_dirty=False)
        waves.append(wave)
    if not waves: missing.append(key); continue
    rs = unreal.RDSoundSet()
    rs.set_editor_property("sounds", waves)
    rs.set_editor_property("volume", float(s.get("volume", 1.0)))
    rs.set_editor_property("pitch", float(s.get("pitch", 1.0)))
    rs.set_editor_property("pitch_variation", float(s.get("pitch_var", 0.05)))
    rs.set_editor_property("inner_radius", float(s.get("inner", 200.0)))
    rs.set_editor_property("falloff_distance", float(s.get("falloff", 2500.0)))
    rs.set_editor_property("b2d", bool(s.get("flat", False)))
    sounds[unreal.Name(key)] = rs; nwaves += len(waves)
gen.modify()
gen.set_editor_property("sounds", sounds)
gen.set_editor_property("sound_volume", float(man.get("master_volume", 1.0)))
gen.set_editor_property("music_volume", float(man.get("music_volume", 1.0)))

# the monsters' voices and step lengths (struct arrays are copies: the whole array is set again)
defs = list(gen.get_editor_property("monsters")); named = 0
for d in defs:
    m = man["monsters"].get(str(d.get_editor_property("name")))
    if not m: missing.append("monster " + str(d.get_editor_property("name"))); continue
    d.set_editor_property("sound_set", unreal.Name(m["set"])); d.set_editor_property("step_length", float(m["step_length"])); named += 1
    for part in ("Step", "Idle", "Roar", "Attack", "Hurt", "Death"):
        if "Monster.%s.%s" % (m["set"], part) not in man["sets"]: missing.append("Monster.%s.%s" % (m["set"], part))
gen.set_editor_property("monsters", defs)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
back = gen.get_editor_property("sounds")
print("RDCSOUNDS ok | %d sets, %d waves, %d monster kinds with a voice | generator has %d sets | missing: %s" % (len(sounds), nwaves, named, len(back), missing or "none"))
del gen, gens, w, sounds, defs, back
gc.collect()
