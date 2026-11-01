"""mistward_castle: the list of 2026-10-31b (docs/improvements5.txt; RD/RDMistward5.cpp, RDCeilings.cpp, RDHUD.cpp,
RDHeroSelect.cpp). On the castle's generator ("Mistward5"):
- bMonsterRanged   SourceArt/mistward/monsters5.json's 28 kinds shoot from afar in their own theme: medium (8 m) or long
                   (15 m) from 3 m out, a share of their blow (0.55 / 0.4), a wait of 2.2 / 3.0 times their blows' interval;
                   their shot, muzzle and hit are Magic Projectiles Vol. 4 / 5 systems of one name; their clip their own Shout
                   or Shot clip, else their first attack (released at its blow's time). Shots sound as Player.Whoosh and land
                   as Player.Hit.Crossbow (Monster.Shot, Monster.ShotHit)
- bNameOnlyBars    each kind's meaningful name (monsters5.json's names) as its Title; the bar shows the name only. The summon
                   spells' lines name the new names
- bArenaLock       no way out of an arena being fought
- bArenaCrowd      townsfolk (NPC_Characters_Pack, 10 meshes) along its walls: their idle, the crowd clips
                   (SourceArt/mistward_crowd/SK_NPC_Crowd_Clips.fbx, blender_numpy/crowd_clips.py: Clap, Cheer) imported onto
                   the pack's UE4 mannequin skeleton; a smoke puff (ToonExplosion Vol. 1) as they come and go; their sounds
                   (blender_numpy/crowd_sounds.py -> SourceArt/mistward/audio5: Env.Arena.Crowd / Cheer / Clap)
- bAutoplayMode    autoplay (-Autoplay=<seconds>, ?Autoplay=); its menu (mistward_castle_select) gets AUTOPLAY over START
- bCeilingStyles   rooms' ceilings raised, beamed (Medieval Castle's beam wood), domed and vaulted; the start section is
                   built again so its saved ceilings have them
random_dungeonmagic_level5 is not touched. Saves both maps; ends on mistward_castle.
Args: none, or "noimport" (the clips and sounds are not imported again)."""
import gc, json, os, sys, unreal

MAP = "/Game/RandomDungeon/Maps/mistward_castle"; SEL = MAP + "_select"
PROJ = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
SA = os.path.join(PROJ, "SourceArt")
J = json.load(open(os.path.join(SA, "mistward", "monsters5.json"), encoding="utf-8"))
CROWD_FBX = os.path.join(SA, "mistward_crowd", "SK_NPC_Crowd_Clips.fbx")
AUDIO = os.path.join(SA, "mistward", "audio5")
D = "/Game/RandomDungeon/Mistward5"
SKEL = "/Game/NPC_Characters_Pack/Demoscene_UE4/Mesh/UE4_Mannequin_Skeleton"
IMPORT = "noimport" not in sys.argv
eal = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
VOL = {"V4": "/Game/MagicProjectilesVol4/Particles/NiagaraSystems", "V5": "/Game/MagicProjectilesVol5/Particles/NiagaraSystems"}


def open_map(m):
    if not ues.get_editor_world().get_path_name().startswith(m + "."): les.load_level(m)


def fx(key, role):
    """'V5:PoisonDart01' -> NS_<Role>_PoisonDart01 (Vol. 5 keeps them in Projectiles / Muzzles / Hits)"""
    vol, name = key.split(":")
    sub = {"Projectile": "Projectiles", "Muzzle": "Muzzles", "Hit": "Hits"}[role] if vol == "V5" else ""
    p = f"{VOL[vol]}/{sub + '/' if sub else ''}NS_{role}_{name}"
    a = unreal.load_asset(p)
    assert a or role == "Muzzle", p          # (Vol. 4's rocks have no muzzle system)
    return a


# ---- the crowd's clips, onto the townsfolk's skeleton
skel = unreal.load_asset(SKEL)
clips = {}
if IMPORT:
    o = unreal.FbxImportUI()
    o.set_editor_property("import_mesh", False); o.set_editor_property("import_as_skeletal", True)
    o.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
    o.set_editor_property("skeleton", skel); o.set_editor_property("import_animations", True)
    o.set_editor_property("import_materials", False); o.set_editor_property("import_textures", False)
    t = unreal.AssetImportTask(); t.filename = CROWD_FBX; t.destination_path = D + "/_ClipImport"
    t.automated = True; t.replace_existing = True; t.save = True; t.options = o
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    for p in t.imported_object_paths:
        a = unreal.load_asset(p)
        if isinstance(a, unreal.AnimSequence):
            clip = p.split(".")[-1].split("_")[-1]          # (..._root_root_Clap -> Clap)
            dst = f"{D}/Crowd/AS_Crowd_{clip}"
            if eal.does_asset_exist(dst): eal.delete_asset(dst)
            eal.rename_asset(p.split(".")[0], dst)
    for p in eal.list_assets(D + "/_ClipImport", recursive=True): eal.delete_asset(p.split(".")[0])
    eal.delete_directory(D + "/_ClipImport")
# (Interchange takes the FBX at 25 frames a second: the frames are all there, 20 % slow. The clip plays at the length
# Blender built it to: crowd_clips.json's)
CJ = json.load(open(os.path.join(SA, "mistward_crowd", "crowd_clips.json"), encoding="utf-8"))
for c in ("Clap", "Cheer"):
    clips[c] = unreal.load_asset(f"{D}/Crowd/AS_Crowd_{c}")
    assert clips[c], c
    rate = clips[c].get_play_length() / float(CJ[c]["length"])
    clips[c].set_editor_property("rate_scale", rate); eal.save_loaded_asset(clips[c], only_if_is_dirty=False)
    print(f"879 crowd clip {c}: {unreal.AnimationLibrary.get_num_frames(clips[c])} frames, {clips[c].get_play_length():.2f} s at rate {rate:.3f} -> "
          f"{clips[c].get_play_length() / rate:.2f} s (built {CJ[c]['length']} s), skeleton {clips[c].get_editor_property('skeleton').get_name()}")
idle = unreal.load_asset("/Game/NPC_Characters_Pack/Demoscene_UE4/Animations/ThirdPersonIdle")
meshes = [unreal.load_asset(f"/Game/NPC_Characters_Pack/Mesh/NPC_Character_{i:02d}/Mesh_UE4/Full/SK_NPC_Character_{i:02d}_Full_{v}") for i in range(1, 6) for v in ("01", "02")]
meshes = [m for m in meshes if m]

# ---- the audience's sounds
index = json.load(open(os.path.join(AUDIO, "index.json"), encoding="utf-8"))
if IMPORT:
    tasks = []
    for key, e in index.items():
        for f in e["files"]:
            t = unreal.AssetImportTask()
            t.set_editor_property("filename", os.path.join(AUDIO, f["file"])); t.set_editor_property("destination_path", D + "/Audio")
            t.set_editor_property("destination_name", os.path.splitext(f["file"])[0])
            t.set_editor_property("automated", True); t.set_editor_property("replace_existing", True); t.set_editor_property("save", True)
            tasks.append(t)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

# ---- the menu: AUTOPLAY
open_map(SEL)
sel = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDHeroSelect))
sel.set_editor_property("autoplay_button", True); sel.modify(); les.save_current_level()
said = f"879 {SEL.split('/')[-1]}: autoplay button {sel.get_editor_property('autoplay_button')}, lengths {list(sel.get_editor_property('autoplay_lengths'))}"
del sel

# ---- the castle
open_map(MAP)
gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
snd = gen.get_editor_property("sounds")
SETS = {"Env.Arena.Crowd": (0.9, 900.0, 7000.0), "Env.Arena.Cheer": (1.0, 900.0, 7000.0), "Env.Arena.Clap": (0.85, 900.0, 7000.0)}
for key, (vol, inner, fall) in SETS.items():
    waves = [unreal.load_asset(f"{D}/Audio/{os.path.splitext(f['file'])[0]}") for f in index[key]["files"]]
    assert all(waves), key
    rs = unreal.RDSoundSet()
    rs.set_editor_property("sounds", waves); rs.set_editor_property("volume", vol); rs.set_editor_property("pitch", 1.0)
    rs.set_editor_property("pitch_variation", 0.04); rs.set_editor_property("inner_radius", inner); rs.set_editor_property("falloff_distance", fall)
    snd[unreal.Name(key)] = rs
for key, like in (("Monster.Shot", "Player.Whoosh"), ("Monster.ShotHit", "Player.Hit.Crossbow")):
    src = snd[unreal.Name(like)]
    rs = unreal.RDSoundSet()
    for p in ("sounds", "volume", "pitch", "pitch_variation", "inner_radius", "falloff_distance"): rs.set_editor_property(p, src.get_editor_property(p))
    rs.set_editor_property("volume", src.get_editor_property("volume") * 0.8); rs.set_editor_property("b2d", False)
    snd[unreal.Name(key)] = rs
gen.set_editor_property("sounds", snd)

# ---- names and shots
names = J["names"]; ranged = J["ranged"]
defs = list(gen.get_editor_property("monsters")); renamed = {}; shooting = []
for d in defs:
    k = str(d.get_editor_property("name"))
    old = str(d.get_editor_property("title"))
    if k in names:
        d.set_editor_property("title", names[k]); renamed[old] = names[k]
    d.set_editor_property("shoots", False)
    r = ranged.get(k)
    if not r: continue
    kind = r["range"]
    d.set_editor_property("shoots", True)
    d.set_editor_property("ranged_range", float(J["ranges"][kind])); d.set_editor_property("ranged_min", float(J["ranges"]["min"]))
    d.set_editor_property("ranged_damage", float(J["damage"][kind]))
    d.set_editor_property("ranged_cooldown", float(J["cooldown"][kind]) * d.get_editor_property("attack_interval"))
    d.set_editor_property("ranged_speed", float(J["speed"][kind]))
    d.set_editor_property("ranged_fx", fx(r["fx"], "Projectile")); d.set_editor_property("ranged_muzzle_fx", fx(r["fx"], "Muzzle")); d.set_editor_property("ranged_hit_fx", fx(r["fx"], "Hit"))
    d.set_editor_property("ranged_fx_scale", float(r.get("scale", 1.0)))
    d.set_editor_property("ranged_theme", r["theme"])
    # (its own Shout or Shot clip from its attacks' folder, else its first attack released at that blow's time)
    atk = list(d.get_editor_property("attacks")); hit = list(d.get_editor_property("hit_times"))
    clip, rel = None, 0.45
    if atk:
        folder = atk[0].get_path_name().rsplit("/", 1)[0]
        for p in sorted(eal.list_assets(folder, recursive=False)):
            n = p.split(".")[-1]
            if any(t in n for t in ("Shout", "Shot", "Attack_Fire")) and isinstance(unreal.load_asset(p.split(".")[0]), unreal.AnimSequence):
                clip = unreal.load_asset(p.split(".")[0]); break
        if not clip:
            clip = atk[0]; rel = (hit[0] / max(atk[0].get_play_length(), 0.1)) if hit else 0.45
    d.set_editor_property("ranged_clip", clip); d.set_editor_property("ranged_release", float(min(max(rel, 0.1), 0.9)))
    shooting.append((k, names.get(k, k), kind, r["fx"], clip.get_name() if clip else None, round(d.get_editor_property("ranged_cooldown"), 2)))
missing = [k for k in ranged if k not in [str(d.get_editor_property("name")) for d in defs]]
assert not missing, missing
gen.set_editor_property("monsters", defs)
# (the summon spells' lines name the monsters by their new names)
spells = list(gen.get_editor_property("spells")); relined = 0
for s in spells:
    if s.get_editor_property("kind") != unreal.RDSpellKind.SUMMON: continue
    e = str(s.get_editor_property("effect"))
    for old, new in renamed.items():
        if f"calls {old} (" in e: e = e.replace(f"calls {old} (", f"calls {new} ("); relined += 1
    s.set_editor_property("effect", e)
gen.set_editor_property("spells", spells)

# ---- the switches and the audience
for p in ("monster_ranged", "name_only_bars", "arena_lock", "arena_crowd", "autoplay_mode", "ceiling_styles"): gen.set_editor_property(p, True)
gen.set_editor_property("crowd_meshes", meshes); gen.set_editor_property("crowd_idle", idle)
gen.set_editor_property("crowd_claps", [clips["Clap"]]); gen.set_editor_property("crowd_cheers", [clips["Cheer"]])
gen.set_editor_property("crowd_appear_fx", unreal.load_asset("/Game/ToonExplosionVol1/Particles/NiagaraSystems/NS_SmokePuff_01") or
                        next((unreal.load_asset(a.split(".")[0]) for a in eal.list_assets("/Game/ToonExplosionVol1", recursive=True) if a.split(".")[-1] == "NS_SmokePuff_01"), None))
gen.set_editor_property("crowd_appear_fx_scale", 0.6)
gen.set_editor_property("ceiling_beam_material", unreal.load_asset("/Game/Medieval_Castle/CastleKit/Wood_Structures/Materials/MI_Wood_BeaMI_01a"))
gen.modify()
gen.build_start_section()          # (the saved start section, its ceilings as the styles say)
les.save_current_level()
print(said)
print("879 mistward_castle: " + " | ".join(f"{p} {gen.get_editor_property(p)}" for p in ("monster_ranged", "name_only_bars", "arena_lock", "arena_crowd", "autoplay_mode", "ceiling_styles")))
print(f"879 crowd: {len(gen.get_editor_property('crowd_meshes'))} meshes, idle {idle.get_name() if idle else None}, puff {gen.get_editor_property('crowd_appear_fx').get_name() if gen.get_editor_property('crowd_appear_fx') else None}")
print(f"879 names: {sum(1 for d in gen.get_editor_property('monsters') if str(d.get_editor_property('title')) in names.values())} of {len(defs)} kinds; summon lines renamed {relined}")
print(f"879 shooters: {len(shooting)}")
for s in shooting: print("   ", s)
print("879 sounds: " + ", ".join(f"{k} {len(gen.get_editor_property('sounds')[unreal.Name(k)].get_editor_property('sounds'))}" for k in list(SETS) + ["Monster.Shot", "Monster.ShotHit"]))
del gen, defs, spells, snd, meshes, clips, idle, skel
gc.collect()
