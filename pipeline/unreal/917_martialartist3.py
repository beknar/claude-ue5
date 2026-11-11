"""The Martial Artist on MartialArtist3 (the user's of 2026-11-10: "use the new model MartialArtist3.glb and use its animations for
the moves and abilities of the martial artist character"). ai models/MartialArtist3.glb is a Tripo body with a rig of its own
(80 bones: five spine bones, two neck bones, twist bones, metacarpals; every bone of MartialArtist2's by its name) and her
clips on it (blender_numpy/martialartist3_retarget.py: MartialArtist2's clips and martialartist_clips.py's, the same names and
timing). Her assets keep their names, so every map's Martial Artist (her mesh, clips, pawn, armour) takes her; what follows
her rig is made again. Steps (both by default, or name one):
  clean  (before 600) her old rig's assets deleted: her mesh and skeleton (an import onto a skeleton of other bones merges them
         and keeps the old rest pose), her clips, 610's locomotion, her flinch and death, the horse's rider clips for her, her
         armour fits; refused while a map of the game is open (it would be saved without them)
  rig    (after 600 / 610 / 615 / 620, 851 and 913 rider) her flinch and death retargeted onto her rig (ma_rig.py, as 872's),
         her dungeon character put back on 620's, and on every map of the game where she is: her knife grips from her new
         hands, her fists' and knives' blows measured on her new clips, her weapons' flinch and death; nothing else of her hero
         (the later stages' numbers stay)
The order: blender_numpy/tripo_build.py on MartialArtist3.glb (no clip maker; it writes SK_JRPG_MartialArtist.glb too), 917
clean, 600 MartialArtist glb (that GLB through Interchange's glTF import: the FBX imports misread her thighs), 610 / 615 / 620
MartialArtist 82.5 keepmeadow, 849 heroes MartialArtist, summoner3_armour.py --hero MartialArtist (the seven sets), 851 MartialArtist (the
seven), 913 rider, 917 rig, 819. Args: [clean] [rig]"""
import json, os, sys, importlib, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ma_rig as MR
importlib.reload(MR)
eal = unreal.EditorAssetLibrary; ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
CH = HERO = "MartialArtist"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
SRC = os.path.join(SA, "jrpg_martialartist")
MAPS = "/Game/RandomDungeon/Maps/"
GAME_MAPS = ("mistward_castle", "martial_arts", "brokenspire", "vel_morrath", "war_engine", "sewers", "kethrys_spire", "heaven_fortress")
STEPS = [a for a in sys.argv[1:] if a in ("clean", "rig")] or ["clean", "rig"]
MESH = f"/Game/JRPG/Character/SK_JRPG_{CH}"
REPORT = []

if "clean" in STEPS:
    w = ues.get_editor_world(); wn = w.get_name() if w else ""
    assert wn not in GAME_MAPS and wn != "mistward_castle_select", f"open an empty level first (now {wn}): a map of the game saved without her assets loses them"
    mesh = unreal.load_asset(MESH)
    sko = mesh.get_editor_property("skeleton") if mesh else None
    skel = sko.get_path_name().split(".")[0] if sko else f"/Game/JRPG/Character/SK_JRPG_{CH}_Skeleton"     # (a mesh can have lost it)
    phys = mesh.get_editor_property("physics_asset") if mesh else None
    gone = 0
    # (what refers to her skeleton or mesh first, then the mesh, its physics and the skeleton)
    for folder in (f"/Game/JRPG/{CH}Anims", f"/Game/JRPG/{CH}Locomotion", f"/Game/RandomDungeon/Horse/Anims/{CH}", f"/Game/JRPG/HeroArmour/{CH}"):
        for p in eal.list_assets(folder, recursive=True):
            if eal.delete_asset(p.split(".")[0]): gone += 1
    for n in MR.FLINCH_DEATH:
        p = f"{MR.ANIMS}/{n}_{CH}"
        if eal.does_asset_exist(p) and eal.delete_asset(p): gone += 1
    for p in (MESH, phys.get_path_name().split(".")[0] if phys else None, skel):
        if p and eal.does_asset_exist(p) and eal.delete_asset(p): gone += 1
    REPORT.append(f"clean: {gone} assets of her old rig deleted; mesh left {eal.does_asset_exist(MESH)}, skeleton left {bool(skel) and eal.does_asset_exist(skel)}")

if "rig" in STEPS:
    mesh = unreal.load_asset(MESH); rig = unreal.load_asset(f"/Game/JRPG/Rigs/IK_JRPG_{CH}_Auto")
    assert mesh and rig, "600-620 for MartialArtist first"
    DATA = json.load(open(os.path.join(SA, "martial_arts", "martial_arts.json"), encoding="utf-8"))
    RTIMES = json.load(open(os.path.join(SRC, "times.json")))
    FR = json.load(open(os.path.join(SA, "random_dungeon_magic5", "weapon_frames.json"), encoding="utf-8"))["weapons"]
    WT = json.load(open(os.path.join(SA, "random_dungeon_magic5", "weapons_table.json"), encoding="utf-8"))
    flinch, death = MR.flinch_death(mesh, rig)
    chbp = MR.character_bp()
    GR = MR.Grips(mesh, FR, RTIMES["grip_tilt"]["dagger"])
    knife_r, knife_l = GR.dagger_grip("r"), GR.dagger_grip("l")
    # (her blows on her new clips: each fists clip played whole, its blow where a hand or foot is fastest; each stab where its
    # hands are, after its wind-up)
    fist_hit = {}
    for n in DATA["fists"]["clips"]:
        a = MR.clip(n); L, hit = MR.fastest(a, ["hand_l", "hand_r", "foot_l", "foot_r"]); fist_hit[a.get_path_name()] = (round(L, 3), round(hit, 3))
    stab_hit = {}
    for n, hands in (("Stab1", ["hand_r"]), ("Stab2", ["hand_l"]), ("Stab3", ["hand_r", "hand_l"])):
        a = MR.clip(n); L, hit = MR.fastest(a, hands, RTIMES["Stabs"][n]["wind"]); stab_hit[a.get_path_name()] = (round(L, 3), round(hit, 3))
    REPORT.append(f"rig: flinch {flinch.get_name()}, death {death.get_name()}, character {chbp.get_name()}; fists {[v for v in fist_hit.values()]}; stabs {[v[1] for v in stab_hit.values()]}")
    key = lambda name: "".join(c for c in name.title() if c.isalnum())
    knife_keys = {key(w["name"]) for w in WT["weapons"] if w["type"] in DATA["knife_types"]}

    def remeasure(wd, table, say=True):
        """a weapon's blows on her new clips (one blow a clip, as she plays them); True if it is one of hers"""
        ats = list(wd.attacks)
        if not ats or not all(a and a.get_path_name() in table for a in ats): return False
        old = [round(x, 3) for x in wd.hit_times]
        wd.hit_times = [table[a.get_path_name()][1] for a in ats]
        if table is fist_hit: wd.attack_ends = [table[a.get_path_name()][0] for a in ats]
        else: wd.attack_ends = [round(min(table[a.get_path_name()][0], table[a.get_path_name()][1] + 0.24), 3) for a in ats]
        if say: REPORT.append(f"   {str(wd.name)}: blows {old} -> {list(wd.hit_times)}")
        return True

    chi_seen = {}
    MATIMES = json.load(open(os.path.join(SRC, "ma_times.json")))
    def chi_check(wd):
        """a chi attack keeps its hit time (martialartist_clips.py's ma_times.json): martialartist3_retarget.py writes a frame
        for each of the source clip's, so the clip must be as long as the clip maker's, within a frame (PR #45's review: only
        the fists and knives were measured again). (Her striking bone's fastest moment or farthest reach is no measure of a
        chi's blow: a chain of punches or a kick's wind-up is faster earlier, and her feet stand 80 cm from her pelvis)"""
        ats = list(wd.attacks)
        if not wd.spell or not ats or not ats[0]: return
        p = ats[0].get_path_name()
        if p in chi_seen: return
        clip = p.split(".")[-1].replace(f"AS_{CH}_", ""); t = MATIMES.get(clip)
        chi_seen[p] = (str(wd.name), round(ats[0].get_play_length(), 3), t and round(float(t["length"]), 3), t and float(t["hit"]), round(list(wd.hit_times)[0], 3) if list(wd.hit_times) else None)

    def do_map(m):
        """her rig's parts on one map's generator (in a function: its actors are let go when it returns)"""
        if not ues.get_editor_world().get_path_name().startswith(MAPS + m + "."): les.load_level(MAPS + m)
        gen = next((a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator)), None)
        heroes = list(gen.get_editor_property("heroes")) if gen else []
        h = next((x for x in heroes if str(x.name) == HERO), None)
        if not h: REPORT.append(f"{m}: no Martial Artist"); return
        REPORT.append(f"{m}:")
        nw = 0
        for lst in ("weapons", "locked_weapons", "later_weapons"):
            try: ws = list(h.get_editor_property(lst))
            except Exception: continue
            for wd in ws:
                wd.get_hit = flinch; wd.death = death; nw += 1
                if not remeasure(wd, fist_hit): chi_check(wd)
            h.set_editor_property(lst, ws)
        h.pawn_class = chbp.generated_class()
        gen.set_editor_property("heroes", heroes)
        items = list(gen.get_editor_property("items")); nk = 0
        for it in items:
            if it.kind != unreal.RDItemKind.WEAPON: continue
            fits = list(it.weapon_fits); changed = False
            for f in fits:
                if str(f.hero) != HERO: continue
                wd = f.weapon; wd.get_hit = flinch; wd.death = death
                k = key(str(it.name).split(" ", 1)[1] if str(it.name).split(" ", 1)[0] in ("Fine", "Masterwork", "Exalted", "Celestial") else str(it.name))
                if k in knife_keys and k in FR:
                    wd.grip = GR.mapped(knife_r, k, "r"); wd.off_hand_grip = GR.mapped(knife_l, k, "l"); nk += 1
                    remeasure(wd, stab_hit, say=False)
                f.weapon = wd; changed = True
            if changed: it.weapon_fits = fits
        gen.set_editor_property("items", items)
        gen.modify(); les.save_current_level()
        REPORT.append(f"   {nw} of her weapons, {nk} knife fits regripped")

    import gc
    for m in GAME_MAPS:
        if not eal.does_asset_exist(MAPS + m): REPORT.append(f"{m}: no map"); continue
        do_map(m)
        # (nothing of this map may be held when the next one loads: "Old world ... not cleaned up by garbage collection while
        # loading new map" is a fatal error (it took the editor down when the generator was still in a variable here))
        gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    les.load_level(MAPS + "mistward_castle")
    off = [v[0] for v in chi_seen.values() if v[2] is None or abs(v[1] - v[2]) > 1.0 / 24 + 0.005 or v[4] is None or abs(v[4] - v[3]) > 0.005]
    REPORT.append(f"chi: {len(chi_seen)} clips (name, its length, the clip maker's, the hit there, the weapon's hit) {list(chi_seen.values())}; "
                  f"{len(off)} off by more than a frame or not at the clip maker's hit {off}")

print("917 " + " | ".join(REPORT))
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
