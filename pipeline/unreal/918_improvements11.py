"""The user's list of 2026-11-11 (docs/improvements11.txt), in phases (the user's choices: memory improvements11-plan).
Steps (name them; several in one run):
  maidle   the Martial Artist's new Idle (martialartist_clips.py's `calm`: hands on her hips, the foot's tap, the shoulders'
           roll, the looks, the toe rises; 9 s) into her own AS_MartialArtist_Idle, nothing else of her touched ("the other
           animations should not be affected at all"): tripo_build.py's SK_JRPG_MartialArtist.glb imported through Interchange
           onto her skeleton (animations only) into a scratch folder, and the Idle's frames and bone tracks copied into the
           asset in place, so her AnimBP and blend space keep pointing at it; checked bone by bone against the import, the
           scratch folder deleted. Before it: martialartist3_retarget.py (the clips) and tripo_build.py on MartialArtist3.glb.
  clean <Hero>  (before 600) a hero's old body deleted for a new one (Rogue: Rogue2.glb; Summoner: Summoner5): her mesh,
           skeleton and physics, her clips, 610's locomotion, the horse's rider clips for her, her armour fits, and what
           822 / 855 / 876 made on her skeleton (her flinch and death, the Rogue's bow clip); refused while a map of the game
           is open (917 clean's way: a map saved without them loses them). Her assets keep their names: every map's hero,
           items and menu take the new body without being written
  rig <Hero>    (after 600 / 610 / 615 / 620, the armour and 913 rider) what follows her rig, from her new reference pose and
           clips (never copied from the old body's): her flinch (her own Hit_to_body_01: Rogue2's, the Summoner's carried
           from Summoner4) and her death (Animations_Warrior's Dead_1 retargeted), her dungeon character put back on 620's;
           on every map of the game where she is: her weapons' grips, holsters and blows (the Rogue's daggers and
           crossbow, 822's measures; the Summoner's knives), her found weapons' fits (855's knives, bows and crossbows) and
           her torch; on the hero menu the same in its hero copies and the weapons it holds on her
The list's second phase (C++ RD/RDList11.cpp first):
  noshield11  every found weapon's fit (any hero), the heroes' weapons (all three lists) and the level's without a shield mesh in
           the off hand, on every map of the game ("when the warrior puts on a shield ... then takes it off, her default
           appears on her arm again": 105 found swords' fits held SM_Shield_1)
  basic    the Martial Artist's "Fists" labelled "Basic Attacks" (FRDWeaponDef::Label: the HUD's; the name stays the key) and her
           controls' "switch basic attacks / chi", on every map and the hero menu (872 and martial_arts.json carry it too)
  guards   (brokenspire) the guards' strikes: the Dwarf pack's Anim_Warrior_Attack_1-4 retargeted onto the NPC_Characters
           pack's Manny (every guard's skeleton takes it as compatible), their hit times (the right hand's fastest after
           0.3 s); each guard, militiaman, soldier, captain and templar its pack's sword (Knight_0N's, the Vikings a knight's;
           Heaven's none: bare-handed) and its grip from the Manny's reference pose
The bodies (blender_numpy): the Rogue: summoner5_cloak.py -- Rogue2.glb SourceArt/jrpg_rogue/Rogue2_Cloak.glb --hero Rogue2
(her cloak's own bones, as the Summoner's: Tripo had skinned it to her arms, and her Shoot drew it forward; the user's of
2026-11-12), then martialartist3_retarget.py -- Rogue.glb SourceArt/jrpg_rogue Rogue2_Cloak.glb --maker
rogue_clips,weapon5_clips --tag Rogue --carry Stab1,Stab2,Stab3,Shoot,RollF,RollB,W5_Bow --own --inplace Walk,Run --noskin
--name Rogue2 --env W5_CLIPS=Bow --env W5_HERO=Rogue, then tripo_build.py on Rogue2_Animated.glb (SK_JRPG_Rogue Rogue 170 -).
The Summoner: summoner5_idle.py (Summoner5.glb -> Summoner5_Idle.glb), summoner5_cloak.py (-> Summoner5_Cloak.glb: the cloak
baked while her walk and run still carry her, so it billows with her speed), then martialartist3_retarget.py --
Summoner4.glb SourceArt/jrpg_summoner4 Summoner5_Cloak.glb --maker summoner4_clips --tag Summoner4 --carry
CastBolt,Summon1,Summon2,Summon3,Summon4,Summon5,Stab1,Stab2,Stab3,Hit_to_body_01 --own --inplace Walk,Run --noskin --name
Summoner5, tripo_build.py on Summoner5_Animated.glb (SK_JRPG_Summoner4 Summoner4 168 -).
In the editor: clean, 600 <CH> glb, 610 / 615 / 620, the armour (the Rogue: 849 heroes, summoner3_armour.py, 851), 913 rider, 921 clips (the swim clips on her skeleton),
rig, then 819 (her character's MoveScale made an override again and her new walk / run speeds baked in).
The list's third phase (C++ RD/RDList11c.cpp first; after 910 and 905, which rebuild the made-up spells and the tome spells'
places; from SourceArt/balance/list11_spells.json; on every map of the game):
  cantrip  the casters' Fire at no mana, labelled "Fire Bolt (cantrip)" (its damage grows with her tier as every spell's)
  spells3  Starfall's, Singularity's and Soul Rend's looks (the packs' systems by name), every spell's element by a word of its
           name, the Warlock's thirteen curses (OnlyHeroes, their CurseEffect, place, mana) and their tomes
  slashes3 ten more slashes for the Warrior (two a tier, trails on her blade) and their items
  casts3   the three casts (blender_numpy/spell_casts11.py through tripo_build.py into SourceArt/spell11_clips/<CH>) imported
           onto the Mage's, the Warlock's and the Summoner's skeletons, and named in their heroes' SpellClips
  icons3 <dir>  the curses' and Starfall's and Singularity's pictures (spell_<name>.png, rdm4_ui_gen.py / rdm4_ui_cut.py)
Args: steps [Hero | dir], several steps space- or comma-separated   (maidle | clean <Hero> | rig <Hero> | noshield11 | basic |
guards | cantrip | spells3 | slashes3 | casts3 | icons3 <dir>)"""
import os, sys, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); AL = unreal.AnimationLibrary
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
STEPS = [s for a in sys.argv[1:] if not a.startswith("-") for s in (a.split(",") if not os.path.isabs(a) else [a])]
REPORT = []


def import_clips(src, skel_path, tmp, pipe_name, fps=24):
    """the GLB's clips onto an existing skeleton (Interchange's glTF path, animations only) into `tmp`: {clip name: asset}"""
    PD = "/Game/JRPG/Pipelines"; pp = f"{PD}/{pipe_name}"
    if eal.does_directory_exist(tmp): eal.delete_directory(tmp)
    if eal.does_asset_exist(pp): eal.delete_asset(pp)
    pipe = at.duplicate_asset(pipe_name, PD, unreal.load_asset("/Interchange/Pipelines/DefaultAssetsPipeline"))
    cs = pipe.get_editor_property("common_skeletal_meshes_and_animations_properties")
    # (a sub-object of the pipeline's own: set in place (the pipeline's property is read-only))
    cs.set_editor_property("skeleton", unreal.load_asset(skel_path)); cs.set_editor_property("import_only_animations", True)
    # (sampled at the clips' own 24 a second: Interchange takes a glTF clip at 30, and an asset at 24 cannot be set to 30
    # ("not a multiple or factor"); copied at 24, the 9 s idle had played 11.25 s)
    ap = pipe.get_editor_property("animation_pipeline")
    ap.set_editor_property("use30_hz_to_bake_bone_animation", False); ap.set_editor_property("custom_bone_animation_sample_rate", fps)
    eal.save_loaded_asset(pipe, only_if_is_dirty=False)
    params = unreal.ImportAssetParameters(); params.is_automated = True; params.override_pipelines = [unreal.SoftObjectPath(pipe.get_path_name())]
    mgr = unreal.InterchangeManager.get_interchange_manager_scripted()
    mgr.import_asset(tmp, unreal.InterchangeManager.create_source_data(src), params)
    out = {}
    for q in eal.list_assets(tmp, recursive=True):
        x = unreal.load_asset(q.split(".")[0])
        if isinstance(x, unreal.AnimSequence): out[x.get_name()] = x
    return out


def clip_fps(a):
    """a clip's frames a second, from its own frame count and length"""
    return AL.get_num_frames(a) / a.get_play_length()


def quat_deg(a, b):
    """the angle between two turns, degrees"""
    import math
    d = abs(a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w)
    return math.degrees(2.0 * math.acos(min(1.0, d)))


def copy_clip(src, dst):
    """src's frames and bone tracks into dst in place (dst keeps its path, its users and its settings)"""
    names = [str(n) for n in AL.get_animation_track_names(src)]
    n = AL.get_num_frames(src)
    # (the import is sampled at the asset's own rate (import_clips' fps): the frames go across one for one, so a rate
    # that differs would play the clip faster or slower)
    fps_s, fps_d = clip_fps(src), clip_fps(dst)
    assert abs(fps_s - fps_d) < 0.05, ("the import's rate is not the asset's", fps_s, fps_d)
    ctrl = dst.controller
    ctrl.open_bracket(unreal.Text("new clip"), True)
    ctrl.set_number_of_frames(unreal.FrameNumber(n), True)
    old = [str(x) for x in AL.get_animation_track_names(dst)]
    for b in old:
        if b not in names: ctrl.remove_bone_track(b, True)
    # (every frame's local pose of every bone, read from the import: its raw track data came back empty for some bones)
    keys = {b: ([], [], []) for b in names}
    for f in range(n + 1):
        for b, t in zip(names, AL.get_bone_poses_for_frame(src, names, f, False)):
            keys[b][0].append(t.translation); keys[b][1].append(t.rotation); keys[b][2].append(t.scale3d)
    for b in names:
        if b not in old: ctrl.add_bone_track(b, True)
        ctrl.set_bone_track_keys(b, *keys[b], True)
    ctrl.close_bracket(True)
    eal.save_loaded_asset(dst, only_if_is_dirty=False)
    # (checked: every bone's place and turn at a few frames, the copy against the import)
    worst_cm = worst_deg = 0.0
    for f in sorted({0, n // 4, n // 2, 3 * n // 4, n}):
        a = AL.get_bone_poses_for_frame(src, names, f, False); b = AL.get_bone_poses_for_frame(dst, names, f, False)
        for ta, tb in zip(a, b):
            worst_cm = max(worst_cm, (ta.translation - tb.translation).length()); worst_deg = max(worst_deg, quat_deg(ta.rotation, tb.rotation))
    # (its frame count is not read back: in the session that copied it, get_num_frames gave the old clip's (58) until a
    # restart; the poses read the new data)
    assert worst_cm < 0.1 and worst_deg < 0.1, ("the copy is not the import", worst_cm, worst_deg)
    return n, len(names), worst_cm, worst_deg


if "maidle" in STEPS:
    CH = "MartialArtist"; DST = f"/Game/JRPG/{CH}Anims/AS_{CH}_Idle"
    dst = unreal.load_asset(DST); assert dst, DST
    before = dst.get_play_length()
    others = {q.split(".")[0]: unreal.load_asset(q.split(".")[0]).get_play_length() for q in eal.list_assets(f"/Game/JRPG/{CH}Anims", recursive=False) if not q.split(".")[0].endswith("_Idle")}
    tmp = "/Game/JRPG/_IdleImport"
    fps = round(clip_fps(dst))
    got = import_clips(os.path.join(SA, "jrpg_martialartist", "SK_JRPG_MartialArtist.glb"), f"/Game/JRPG/Character/SK_JRPG_{CH}_Skeleton", tmp, f"PL_{CH}_Clips", fps)
    idle = next((a for k, a in got.items() if k.endswith("Idle")), None)
    assert idle, ("no Idle among", sorted(got))
    n, nb, worst, worst_deg = copy_clip(idle, dst)
    for k in list(got): got[k] = None
    idle = None
    eal.delete_directory(tmp)
    after = unreal.load_asset(DST).get_play_length()
    same = sum(1 for p, L in others.items() if abs(unreal.load_asset(p).get_play_length() - L) < 1e-4)
    REPORT.append(f"maidle: {DST} {before:.3f} s -> {after:.3f} s ({n} frames, {nb} bone tracks; the copy against the import at most {worst:.4f} cm, {worst_deg:.4f} deg); "
                  f"her other clips untouched: {same} of {len(others)} the same length")

# ---------------------------------------------------------------- a hero's new body (Rogue2, Summoner5)
import json, importlib
import ma_rig as MR
importlib.reload(MR)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MAPS = "/Game/RandomDungeon/Maps/"
GAME_MAPS = ("mistward_castle", "martial_arts", "brokenspire", "vel_morrath", "war_engine", "sewers", "kethrys_spire", "heaven_fortress")
# (the game's last tier, tier25.json's count (PR #59's review: one number, not a 30 here); a spell's picture's name (icons3's and
# spells3's one rule))
TIER_COUNT = json.load(open(os.path.join(SA, "balance", "tier25.json"), encoding="utf-8"))["tiers"]["count"]
def pic_name(n): return "spell_" + "_".join("".join(ch if ch.isalnum() else " " for ch in n.lower()).split())
MENU = "mistward_castle_select"
BODIES = {
    "Rogue": {"ch": "Rogue", "anims": "/Game/RandomDungeon/Magic3/Anims", "rigs": "/Game/RandomDungeon/Magic3/Rigs", "tag": "RDM3",
              "child": "BP_RDM3_RogueCharacter", "radius": 36.0,
              "extra": ["/Game/RandomDungeon/Magic3/Anims/Anim_Warrior_Get_Hit_1_Rogue", "/Game/RandomDungeon/Magic3/Anims/Anim_Warrior_Dead_1_Rogue",
                        "/Game/RandomDungeon/Magic5/Anims/Rogue/AS_Rogue_W5_Bow"]},
    "Summoner": {"ch": "Summoner4", "anims": "/Game/RandomDungeon/Summoner4/Anims", "rigs": "/Game/RandomDungeon/Summoner4/Rigs", "tag": "SU4",
                 "child": "BP_SU4_SummonerCharacter", "radius": 30.0,
                 "extra": ["/Game/RandomDungeon/Summoner4/Anims/Anim_Warrior_Dead_1_Summoner4"]},
}
HERO = next((a for a in sys.argv[1:] if a in BODIES), None)
DAGGER_MESH = "/Game/Medieval_Weapons/Meshes/VOL2/SM_Dagger"; XBOW_MESH = "/Game/Medieval_Weapons/Meshes/VOL2/SM_Crossbow"
BOW_DST = "/Game/RandomDungeon/Magic5/Anims/Rogue/AS_Rogue_W5_Bow"
STABS = (("Stab1", ["hand_r"]), ("Stab2", ["hand_l"]), ("Stab3", ["hand_r", "hand_l"]))

if "clean" in STEPS:
    assert HERO, "clean <Rogue | Summoner>"
    cfg = BODIES[HERO]; CH = cfg["ch"]; MESH = f"/Game/JRPG/Character/SK_JRPG_{CH}"
    w = ues.get_editor_world(); wn = w.get_name() if w else ""
    assert wn not in GAME_MAPS and wn != MENU and not wn.startswith("random_dungeon"), f"open an empty level first (now {wn}): a map saved without her assets loses them"
    mesh = unreal.load_asset(MESH)
    sko = mesh.get_editor_property("skeleton") if mesh else None
    skel = sko.get_path_name().split(".")[0] if sko else f"/Game/JRPG/Character/SK_JRPG_{CH}_Skeleton"
    phys = mesh.get_editor_property("physics_asset") if mesh else None
    gone = 0
    for folder in (f"/Game/JRPG/{CH}Anims", f"/Game/JRPG/{CH}Locomotion", f"/Game/RandomDungeon/Horse/Anims/{CH}", f"/Game/JRPG/HeroArmour/{CH}"):
        for p in eal.list_assets(folder, recursive=True):
            if eal.delete_asset(p.split(".")[0]): gone += 1
    # (610's IK rig and retargeter too: left, they would pass rig's check though 610 had not been run on the new body)
    RIGS = [f"/Game/JRPG/Rigs/IK_JRPG_{CH}_Auto", f"/Game/JRPG/Rigs/RTG_Quinn_To_JRPG_{CH}"]
    for p in cfg["extra"] + RIGS + [MESH, phys.get_path_name().split(".")[0] if phys else None, skel]:
        if p and eal.does_asset_exist(p) and eal.delete_asset(p): gone += 1
    REPORT.append(f"clean {HERO}: {gone} assets of her old body deleted; mesh left {eal.does_asset_exist(MESH)}, skeleton left {eal.does_asset_exist(skel)}")

if "rig" in STEPS:
    assert HERO, "rig <Rogue | Summoner>"
    cfg = BODIES[HERO]; CH = cfg["ch"]
    mesh = unreal.load_asset(f"/Game/JRPG/Character/SK_JRPG_{CH}"); rig = unreal.load_asset(f"/Game/JRPG/Rigs/IK_JRPG_{CH}_Auto")
    assert mesh and rig, f"600-620 for {CH} first"
    rm = unreal.IKRigController.get_controller(rig).get_skeletal_mesh()
    assert rm and rm.get_path_name() == mesh.get_path_name(), (f"IK_JRPG_{CH}_Auto is not on her mesh: 610 again", rm)
    RT = json.load(open(os.path.join(SA, f"jrpg_{CH.lower()}", "times.json")))
    FR = json.load(open(os.path.join(SA, "random_dungeon_magic5", "weapon_frames.json"), encoding="utf-8"))["weapons"]
    BY_MESH = {}
    for k_, f_ in FR.items(): BY_MESH.setdefault(f_["mesh"].split(".")[0], k_)
    flinch = MR.clip("Hit_to_body_01", CH)
    (death,) = MR.flinch_death(mesh, rig, ch=CH, anims=cfg["anims"], rigs=cfg["rigs"], clips=["Anim_Warrior_Dead_1"], tag=cfg["tag"])
    chbp = MR.character_bp(CH, cfg["child"], cfg["radius"])
    GR = MR.Grips(mesh, FR, RT["grip_tilt"]["dagger"])
    dag = {"r": GR.dagger_grip("r"), "l": GR.dagger_grip("l")}
    stab = {}
    for n, hands in STABS:
        a = MR.clip(n, CH); L, hit = MR.fastest(a, hands, RT["Stabs"][n]["wind"]); stab[a.get_path_name()] = (round(L, 3), round(hit, 3))
    xbow = GR.crossbow_grip(RT["grip_tilt"].get("crossbow", 45.0)) if HERO == "Rogue" else None
    hol = {"r": GR.holster_thigh("r"), "l": GR.holster_thigh("l")} if HERO == "Rogue" else None
    BACK_BONE = "spine_05"; hol_back = GR.holster_back(BACK_BONE) if HERO == "Rogue" else None
    if HERO == "Rogue":
        # (her bow clip: 600 imported it among her clips; where 855's fits point)
        src = f"/Game/JRPG/{CH}Anims/AS_{CH}_W5_Bow"
        if eal.does_asset_exist(src):
            if eal.does_asset_exist(BOW_DST): eal.delete_asset(BOW_DST)
            eal.rename_asset(src, BOW_DST)
        bow = unreal.load_asset(BOW_DST); assert bow, BOW_DST
        bow.set_editor_property("enable_root_motion", False); bow.set_editor_property("force_root_lock", True); eal.save_loaded_asset(bow, False)
    REPORT.append(f"rig {HERO}: flinch {flinch.get_name()}, death {death.get_name()}, character {chbp.get_name()}; stabs {[v[1] for v in stab.values()]} of {[v[0] for v in stab.values()]}")
    torch_cache = {}

    kept = {}

    def kept_grip(k, mp):
        """a weapon whose mesh weapon_frames.json does not know: its old grip stays, and the report says so"""
        kept[f"{k} {mp.split('/')[-1]}"] = kept.get(f"{k} {mp.split('/')[-1]}", 0) + 1

    def kind_of(wd):
        ats = [a.get_path_name() for a in wd.attacks if a]
        if any(p in stab for p in ats): return "knife"
        if any(p.endswith("_Shoot") for p in ats): return "crossbow"
        if any(p.split(".")[0] == BOW_DST for p in ats): return "bow"
        return None

    def regrip(wd):
        """one of her weapons on her new body; -> its kind (None: a spell, left as it is)"""
        wd.get_hit = flinch; wd.death = death
        k = kind_of(wd); mp = wd.mesh.get_path_name().split(".")[0] if wd.mesh else ""
        if k == "knife":
            if mp == DAGGER_MESH: wd.grip = dag["r"]; wd.off_hand_grip = dag["l"]
            else:
                key = BY_MESH.get(mp)
                if key: wd.grip = GR.mapped(dag["r"], key, "r"); wd.off_hand_grip = GR.mapped(dag["l"], key, "l")
                else: kept_grip(k, mp)
            # (an empty slot in the attacks is passed over, as kind_of does)
            ats = [a.get_path_name() if a else "" for a in wd.attacks]
            wd.hit_times = [stab[p][1] if p in stab else h for p, h in zip(ats, list(wd.hit_times))]
            wd.attack_ends = [round(min(stab[p][0], stab[p][1] + 0.24), 3) if p in stab else e for p, e in zip(ats, list(wd.attack_ends))]
            if hol and str(wd.holster_bone) not in ("", "None"): wd.holster_grip = hol["r"]
            if hol and str(wd.off_hand_holster_bone) not in ("", "None"): wd.off_hand_holster_grip = hol["l"]
        elif k == "crossbow":
            if mp == XBOW_MESH and xbow: wd.grip = xbow
            elif BY_MESH.get(mp): wd.grip = GR.found("crossbow", BY_MESH[mp])
            else: kept_grip(k, mp)
            if hol_back and str(wd.holster_bone) not in ("", "None"): wd.holster_bone = BACK_BONE; wd.holster_grip = hol_back
        elif k == "bow":
            if BY_MESH.get(mp): wd.grip = GR.found("bow", BY_MESH[mp])
            else: kept_grip(k, mp)
        return k

    def torch_of(wd):
        m = wd.off_hand_mesh
        if not m: return None
        p = m.get_path_name()
        if p not in torch_cache: torch_cache[p] = GR.torch_grip(m)
        return torch_cache[p]

    def do_map(m):
        """her rig's parts on one map (in a function: its actors are let go when it returns)"""
        if not ues.get_editor_world().get_path_name().startswith(MAPS + m + "."): les.load_level(MAPS + m)
        gen = next((a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator)), None)
        heroes = list(gen.get_editor_property("heroes")) if gen else []
        h = next((x for x in heroes if str(x.name) == HERO), None)
        if not h: REPORT.append(f"{m}: no {HERO}"); return None
        kinds = {}
        for lst in ("weapons", "locked_weapons", "later_weapons"):
            try: ws = list(h.get_editor_property(lst))
            except Exception: continue
            for wd in ws:
                k = regrip(wd); kinds[str(k)] = kinds.get(str(k), 0) + 1
            h.set_editor_property(lst, ws)
        h.pawn_class = chbp.generated_class()
        gen.set_editor_property("heroes", heroes)
        items = list(gen.get_editor_property("items")); nf = {}; other = {}
        for it in items:
            fits = list(it.weapon_fits); changed = False
            for f in fits:
                if str(f.hero) != HERO: continue
                wd = f.weapon
                if it.kind == unreal.RDItemKind.WEAPON: k = regrip(wd) or "weapon?"
                elif it.kind == unreal.RDItemKind.TORCH and torch_of(wd): wd.off_hand_grip = torch_of(wd); k = "torch"
                else: k = str(it.kind).split(".")[-1].split(":")[0]; other[k] = other.get(k, 0) + 1; continue
                f.weapon = wd; changed = True; nf[k] = nf.get(k, 0) + 1
            if changed: it.weapon_fits = fits
        # (the ankh (914's): its grip is her torch's, moved by the torch mesh's grip point a fifth of the way up its handle)
        tfit = next((f.weapon for it in items if it.kind == unreal.RDItemKind.TORCH for f in it.weapon_fits if str(f.hero) == HERO), None)
        if tfit and tfit.off_hand_mesh:
            tb = tfit.off_hand_mesh.get_bounding_box(); lo_, hi_ = tb.min.z, tb.max.z
            gp = unreal.Vector((tb.min.x + tb.max.x) / 2, (tb.min.y + tb.max.y) / 2, lo_ + (hi_ - lo_) * 0.22)
            ga = unreal.MathLibrary.compose_transforms(unreal.Transform(gp, unreal.Rotator(0, 0, 0), unreal.Vector(1, 1, 1)), tfit.off_hand_grip)
            for it in items:
                if it.kind != unreal.RDItemKind.LIGHT: continue
                fits = list(it.weapon_fits)
                for f in fits:
                    if str(f.hero) == HERO: wd = f.weapon; wd.off_hand_grip = ga; f.weapon = wd; nf["light"] = nf.get("light", 0) + 1; other.pop("LIGHT", None)
                it.weapon_fits = fits
        gen.set_editor_property("items", items)
        gen.modify(); les.save_current_level()
        REPORT.append(f"{m}: her weapons {kinds}, fits regripped {nf}, fits of other kinds left {other}")
        return h.export_text()

    import gc
    castle = None
    for m in GAME_MAPS:
        if not eal.does_asset_exist(MAPS + m): REPORT.append(f"{m}: no map"); continue
        t = do_map(m)
        if m == "mistward_castle": castle = t
        gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")

    def do_menu(text):
        """the hero menu: her copy's weapons as the castle's now are, and the meshes it holds on her figure"""
        les.load_level(MAPS + MENU)
        src = unreal.RDHeroDef(); src.import_text(text)
        by = {}
        for lst in ("weapons", "locked_weapons"):
            for wd in src.get_editor_property(lst): by[str(wd.name)] = wd
        sel = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDHeroSelect))
        hs = list(sel.get_editor_property("heroes")); n = 0; hero = None
        for h in hs:
            if str(h.name) != HERO: continue
            for lst in ("weapons", "locked_weapons"):
                ws = list(h.get_editor_property(lst))
                for wd in ws:
                    s_ = by.get(str(wd.name))
                    if not s_: continue
                    for k in ("grip", "off_hand_grip", "holster_bone", "holster_grip", "off_hand_holster_bone", "off_hand_holster_grip", "get_hit", "death", "hit_times", "attack_ends"):
                        wd.set_editor_property(k, s_.get_editor_property(k))
                    n += 1
                h.set_editor_property(lst, ws)
            h.pawn_class = chbp.generated_class(); hero = h
        sel.set_editor_property("heroes", hs)
        # (the meshes 826 holds on her figure: each weapon's hand or holster, its bone and grip as her copy now says)
        acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
        fig = acts.get(f"Hero_{HERO}"); moved = 0
        if fig and hero:
            c = fig.skeletal_mesh_component
            for wd in hero.weapons:
                for what, bone, grip in ((f"{wd.name}_Hand", wd.hand_bone, wd.grip), (f"{wd.name}_OffHand", wd.off_hand_bone, wd.off_hand_grip),
                                         (f"{wd.name}_Carried", wd.holster_bone, wd.holster_grip), (f"{wd.name}_OffCarried", wd.off_hand_holster_bone, wd.off_hand_holster_grip)):
                    a = acts.get(f"Hero_{HERO}_{what}")
                    if not a or str(bone) in ("", "None"): continue
                    a.attach_to_component(c, bone, unreal.AttachmentRule.SNAP_TO_TARGET, unreal.AttachmentRule.SNAP_TO_TARGET, unreal.AttachmentRule.KEEP_WORLD, False)
                    a.set_actor_relative_transform(grip, False, False); moved += 1
        les.save_current_level()
        REPORT.append(f"{MENU}: {n} of her weapons in its copy, {moved} meshes on her figure put where her grips now are")

    REPORT.append(f"grips kept from her old body (mesh not in weapon_frames.json): {kept or 'none'}")
    if castle: do_menu(castle)
    gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    les.load_level(MAPS + "mistward_castle")

# ---------------------------------------------------------------- the list's second phase
def each_map(maps, fn, what):
    """fn(gen) on each map that has a generator, saved; its report"""
    for m in maps:
        if not eal.does_asset_exist(MAPS + m): REPORT.append(f"{what} {m}: no map"); continue
        if not ues.get_editor_world().get_path_name().startswith(MAPS + m + "."): les.load_level(MAPS + m)
        gen = next((a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator)), None)
        if not gen: REPORT.append(f"{what} {m}: no generator"); continue
        r = fn(gen)
        gen.modify(); les.save_current_level()
        REPORT.append(f"{what} {m}: {r}")
        gen = None
        import gc; gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")


def is_shield(mesh): return bool(mesh) and "shield" in mesh.get_name().lower()


if "noshield11" in STEPS:
    # ("when the warrior puts on a shield in inventory, then takes it off, her default appears on her arm again": 899 and 914 took
    # the shield meshes off her hero's weapons and the level's, but every found sword's fit (855's) still had the old built-in
    # SM_Shield_1 in its off hand, shown once no shield is worn. Every hero's, every list)
    def noshield11(g):
        def strip(ws):
            n = 0; out = []
            for w in ws:
                if is_shield(w.get_editor_property("off_hand_mesh")): w.set_editor_property("off_hand_mesh", None); n += 1
                out.append(w)
            return out, n
        items = list(g.get_editor_property("items")); fits_n = 0
        for it in items:
            if it.kind != unreal.RDItemKind.WEAPON: continue
            fits = list(it.weapon_fits); ch = False
            for f in fits:
                wd = f.weapon
                if is_shield(wd.off_hand_mesh): wd.off_hand_mesh = None; f.weapon = wd; ch = True; fits_n += 1
            if ch: it.weapon_fits = fits
        g.set_editor_property("items", items)
        heroes = list(g.get_editor_property("heroes")); hn = 0
        for h in heroes:
            for lst in ("weapons", "locked_weapons", "later_weapons"):
                try: ws = list(h.get_editor_property(lst))
                except Exception: continue
                ws, k = strip(ws); h.set_editor_property(lst, ws); hn += k
        g.set_editor_property("heroes", heroes)
        lw, ln = strip(list(g.get_editor_property("weapons"))); g.set_editor_property("weapons", lw)
        left = sum(1 for it in g.get_editor_property("items") if it.kind == unreal.RDItemKind.WEAPON for f in it.weapon_fits if is_shield(f.weapon.off_hand_mesh))
        return f"shield meshes off {fits_n} found weapons' fits, {hn} of the heroes' weapons, {ln} of the level's; left {left}"
    each_map(GAME_MAPS, noshield11, "noshield11")

if "basic" in STEPS:
    # ("the martial artist's default attacks without chi should be labeled as 'Basic Attacks'": the weapon keeps its name
    # "Fists" (the key of saves, the quick bar, the tables); FRDWeaponDef::Label is what the HUD shows)
    LABEL = "Basic Attacks"
    def label_ws(ws):
        n = 0
        for w in ws:
            if str(w.name) == "Fists": w.set_editor_property("label", LABEL); n += 1
        return ws, n
    def fix_hero(h):
        n = 0
        for lst in ("weapons", "locked_weapons", "later_weapons"):
            try: ws = list(h.get_editor_property(lst))
            except Exception: continue
            ws, k = label_ws(ws); h.set_editor_property(lst, ws); n += k
        # (her controls' lines: "switch fists / chi")
        t = h.export_text()
        if "switch fists / chi" in t: h.import_text(t.replace("switch fists / chi", "switch basic attacks / chi")); n += 100
        return n
    def basic(g):
        heroes = list(g.get_editor_property("heroes")); hn = 0
        for h in heroes:
            if str(h.name) == "MartialArtist": hn += fix_hero(h)
        g.set_editor_property("heroes", heroes)
        lw, ln = label_ws(list(g.get_editor_property("weapons"))); g.set_editor_property("weapons", lw)
        return f"her weapons labelled {hn % 100}{' and her controls' if hn >= 100 else ''}, the level's {ln}"
    each_map(GAME_MAPS, basic, "basic")
    les.load_level(MAPS + MENU)
    sel = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDHeroSelect))
    hs = list(sel.get_editor_property("heroes")); n = 0
    for h in hs:
        if str(h.name) == "MartialArtist": n += fix_hero(h)
    sel.set_editor_property("heroes", hs); les.save_current_level(); sel = None
    REPORT.append(f"basic {MENU}: {n % 100} labelled")

if "guards" in STEPS:
    # ("when an ambush from outside town ... makes it into town, the guards should fight it": none of the NPC packs has a strike;
    # the Dwarf pack's warrior attacks (its UE4 mannequin) retargeted onto the NPC_Characters pack's Manny, which every guard's
    # skeleton (Knights_Pack, Vikings, NPC_Distopia) lists as compatible (914 sleep); each guard's own pack's sword in hand)
    TD = "/Game/RandomDungeon/Anims/Town/Guard"; TR = "/Game/RandomDungeon/Anims/Town/Rigs"
    src_mesh = unreal.load_asset("/Game/Dwarf_Pack/Mesh/SK_Mannequin"); assert src_mesh
    tgt_mesh = unreal.load_asset("/Game/NPC_Characters_Pack/Demoscene_UE5/Mesh/SKM_Manny")
    if not tgt_mesh:
        sk = "/Game/NPC_Characters_Pack/Demoscene_UE5/Mesh/SKM_Manny_Skeleton"
        tgt_mesh = next((unreal.load_asset(p.split(".")[0]) for p in eal.list_assets("/Game/NPC_Characters_Pack/Demoscene_UE5/Mesh", recursive=True)
                         if isinstance(unreal.load_asset(p.split(".")[0]), unreal.SkeletalMesh) and unreal.load_asset(p.split(".")[0]).skeleton.get_path_name().startswith(sk)), None)
    assert tgt_mesh, "no mesh on the NPC pack's Manny skeleton"
    def mk(cls, fac, name, folder):
        p = f"{folder}/{name}"
        if eal.does_asset_exist(p): eal.delete_asset(p)
        return at.create_asset(name, folder, cls, fac) or unreal.load_asset(p)
    def auto_rig(name, mesh):
        r = mk(unreal.IKRigDefinition, unreal.IKRigDefinitionFactory(), name, TR)
        c = unreal.IKRigController.get_controller(r); c.set_skeletal_mesh(mesh); c.apply_auto_generated_retarget_definition()
        try: c.apply_auto_fbik()
        except Exception: pass
        eal.save_loaded_asset(r); return r
    srig = auto_rig("IK_Guard_DwarfSource", src_mesh); trig = auto_rig("IK_Guard_NPCManny", tgt_mesh)
    rtg = mk(unreal.IKRetargeter, unreal.IKRetargetFactory(), "RTG_Guard_Dwarf_To_NPCManny", TR)
    rc = unreal.IKRetargeterController.get_controller(rtg); rc.add_default_ops()
    rc.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, srig); rc.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, trig)
    rc.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, src_mesh); rc.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET, tgt_mesh)
    rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, srig); rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.TARGET, trig)
    rc.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
    rm = rc.get_op_controller(rc.get_index_of_op_by_name("Root Motion"))
    rm.set_source_root_bone("root"); rm.set_target_root_bone("root"); rm.set_target_pelvis_bone("pelvis")
    try: rc.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
    except Exception as e: print("GUARD align", e)
    eal.save_loaded_asset(rtg)
    CLIPS = ["Anim_Warrior_Attack_1", "Anim_Warrior_Attack_2", "Anim_Warrior_Attack_3", "Anim_Warrior_Attack_4"]
    if eal.does_directory_exist(TD):
        for p in eal.list_assets(TD, recursive=False): eal.delete_asset(p.split(".")[0])
    inp = unreal.IKRetargetBatchOperationInputs()
    inp.set_editor_property("assets_to_retarget", [eal.find_asset_data(f"/Game/Dwarf_Pack/Animations/1With_Weapon/{c}") for c in CLIPS])
    inp.set_editor_property("source_mesh", src_mesh); inp.set_editor_property("target_mesh", tgt_mesh)
    inp.set_editor_property("ik_retarget_asset", rtg); inp.set_editor_property("suffix", "_Guard")
    inp.set_editor_property("target_path", TD); inp.set_editor_property("include_referenced_assets", False)
    inp.set_editor_property("overwrite_existing_files", True)
    unreal.IKRetargetBatchOperation.run_batch_retarget(inp)
    strikes, hits = [], []
    for c in CLIPS:
        a = unreal.load_asset(f"{TD}/{c}_Guard"); assert a, c
        a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True); eal.save_loaded_asset(a, False)
        # (its blow: the right hand's fastest moment after the first 0.3 s (the raise))
        L, hit = MR.fastest(a, ["hand_r"], 0.3)
        strikes.append(a); hits.append(round(hit, 3))
    # (the sword in the hand: its pommel at the mesh's origin, the blade up its +Z; held as a dagger is held (ma_rig's hand
    # frame on the NPC Manny's reference pose), its crossguard along the knuckles)
    APE = unreal.AnimPoseExtensions; ML = unreal.MathLibrary
    ref = APE.get_reference_pose(tgt_mesh.skeleton)
    def bone(n): return APE.get_bone_pose(ref, n, unreal.AnimPoseSpaces.WORLD)
    hand = bone("hand_r"); h = hand.translation
    fore = (h - bone("lowerarm_r").translation).normal()
    along = (bone("middle_01_r").translation - h).normal()
    th = bone("thumb_01_r").translation - h; th = th - along * th.dot(along); th = (th - fore * th.dot(fore)).normal()
    palm = h + fore * 7.0 + (bone("middle_01_r").translation - h) * 0.25
    SWORDS = {"Knight_01": "/Game/Knights_Pack/Meshes/Knight_01/Weapons/SM_Knight_01_Sword", "Knight_02": "/Game/Knights_Pack/Meshes/Knight_02/Weapons/SM_Knight_02_Sword",
              "Knight_03": "/Game/Knights_Pack/Meshes/Knight_03/Weapon/SM_Knight_03_Sword", "Knight_04": "/Game/Knights_Pack/Meshes/Knight_01/Weapons/SM_Knight_01_Sword",
              "Knight_05": "/Game/Knights_Pack/Meshes/Knight_05/Weapon/SM_Knight_05_Sword", "Viking": "/Game/Knights_Pack/Meshes/Knight_02/Weapons/SM_Knight_02_Sword"}
    GRIP_Z = 9.0
    def grip_of(sw):
        bb = sw.get_bounding_box(); gx = (bb.max.x - bb.min.x) > (bb.max.y - bb.min.y)
        # (the guard's long axis on the mesh (x or y) along the hand's knuckles, the blade along the thumb)
        rot = ML.make_rot_from_zx(th, along) if gx else ML.make_rot_from_zy(th, along)
        return ML.make_relative_transform(unreal.Transform(palm - ML.get_up_vector(rot) * GRIP_Z, rot, V(1, 1, 1)), hand)
    V = unreal.Vector
    FIGHT = ("GUARD", "MILITIA", "SOLDIER", "CAPTAIN", "TEMPLAR")
    def guards(g):
        g.set_editor_property("town_guard_strikes", strikes); g.set_editor_property("town_guard_hit_times", hits)
        g.set_editor_property("town_guards_fight", True)
        defs = list(g.get_editor_property("townsfolk")); n = 0; bare = []; by = {}
        for d in defs:
            if str(d.role).split(".")[-1].split(":")[0].upper() not in FIGHT: continue
            mp = d.mesh.get_path_name() if d.mesh else ""
            key = next((k for k in SWORDS if k in mp), None)
            if key:
                sw = unreal.load_asset(SWORDS[key]); d.set_editor_property("guard_weapon", sw); d.set_editor_property("guard_grip", grip_of(sw)); by[key] = by.get(key, 0) + 1
            else:
                d.set_editor_property("guard_weapon", None); bare.append(str(d.name))
            n += 1
        g.set_editor_property("townsfolk", defs)
        return f"{n} fighters ({by}; bare-handed {bare}), strikes {[a.get_name() for a in strikes]} hit at {hits}"
    each_map(("brokenspire",), guards, "guards")

# ---------------------------------------------------------------- the list's third phase: spells, curses, slashes
L11 = None
FX_PACKS = ("MagicProjectilesVol5", "MagicProjectilesVol4", "VortexNiagaraFX", "AbsorbtionFX", "Aura", "AbstractFX", "EnergySourceFX", "ShockWaves", "WeaponSlashFX")
_FX = {}


def fx(name):
    """a Niagara system by its asset name, searched in the packs (the first pack that has it)"""
    if not name: return None
    if name in _FX: return _FX[name]
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for pk in FX_PACKS:
        for a in ar.get_assets_by_path("/Game/" + pk, recursive=True):
            if str(a.asset_name) == name:
                _FX[name] = unreal.load_asset(str(a.package_name)); return _FX[name]
    raise RuntimeError(f"no system {name} in {FX_PACKS}")


def copy_struct(cls, src):
    c = cls(); c.import_text(src.export_text()); return c


if any(s in STEPS for s in ("cantrip", "spells3", "slashes3", "icons3")):
    L11 = json.load(open(os.path.join(SA, "balance", "list11_spells.json"), encoding="utf-8"))

if "cantrip" in STEPS:
    # ("the base cantrip at tier 1 for every caster is the fire bolt. it costs no mana and it scales in damage per tier": the
    # casters' starting Fire; its damage grows with her tier as every spell's does (TierSpellMul))
    C = L11["cantrip"]
    def cantrip_hero(h):
        n = 0
        if str(h.name) not in C["heroes"]: return 0
        for lst in ("weapons", "locked_weapons", "later_weapons"):
            try: ws = list(h.get_editor_property(lst))
            except Exception: continue
            for w in ws:
                if str(w.name) == C["weapon"]:
                    w.set_editor_property("mana_cost", 0.0); w.set_editor_property("mana_share", 0.0); w.set_editor_property("label", C["label"]); n += 1
            h.set_editor_property(lst, ws)
        return n
    def cantrip(g):
        heroes = list(g.get_editor_property("heroes")); n = sum(cantrip_hero(h) for h in heroes)
        g.set_editor_property("heroes", heroes)
        ws = list(g.get_editor_property("weapons")); k = 0
        for w in ws:
            if str(w.name) == C["weapon"] and str(g.get_editor_property("default_hero")) in C["heroes"]: w.set_editor_property("mana_cost", 0.0); w.set_editor_property("mana_share", 0.0); w.set_editor_property("label", C["label"]); k += 1
        g.set_editor_property("weapons", ws)
        return f"{n} heroes' fire bolts at no mana, the level's {k}"
    each_map(GAME_MAPS, cantrip, "cantrip")
    les.load_level(MAPS + MENU)
    sel = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDHeroSelect))
    hs = list(sel.get_editor_property("heroes")); n = sum(cantrip_hero(h) for h in hs)
    sel.set_editor_property("heroes", hs); les.save_current_level(); sel = None
    REPORT.append(f"cantrip {MENU}: {n}")

if "spells3" in STEPS:
    # (Starfall, Singularity and Soul Rend looks of their own; every spell's element; the Warlock's thirteen curses and their tomes)
    def light(s, v): s.set_editor_property("light_color", unreal.LinearColor(v[0], v[1], v[2], 1.0)); s.set_editor_property("light_intensity", float(v[3]))
    ELEM = {w.lower(): e for e, ws in L11["elements"].items() for w in ws}
    def element_of(name):
        for w in str(name).replace("'", "").split():
            if w.lower() in ELEM: return ELEM[w.lower()]
        return None
    def spells3(g):
        spells = list(g.get_editor_property("spells")); by = {str(s.name): i for i, s in enumerate(spells)}
        looked = []
        for nm, lk in L11["looks"].items():
            if nm not in by: continue
            s = spells[by[nm]]
            for k, fld in (("cast", "cast_fx"), ("bolt", "bolt_fx"), ("impact", "impact_fx"), ("area", "area_fx")):
                if k in lk: s.set_editor_property(fld, fx(lk[k]))
            for fld in ("cast_fx_scale", "bolt_fx_scale", "impact_fx_scale", "area_fx_scale"): s.set_editor_property(fld, 1.0)
            if "area_every" in lk: s.set_editor_property("area_every", float(lk["area_every"]))
            s.set_editor_property("use_colors", bool(lk.get("colors", False)))
            if "light" in lk: light(s, lk["light"])
            spells[by[nm]] = s; looked.append(nm)
        # (the curses: Curse of Frailty's struct as their base (the curse kind, its sound), updated in place on a second run)
        base = spells[by["Curse of Frailty"]]
        made = []
        for k, c in enumerate(L11["curses"]):
            s = copy_struct(unreal.RDSpellDef, spells[by[c["name"]]]) if c["name"] in by else copy_struct(unreal.RDSpellDef, base)
            slot = int(c["slot"]); tier = (slot - 1) % 5 + 1
            for fld, v in (("name", c["name"]), ("number", 401 + k), ("type", unreal.RDSpellType.CURSE), ("kind", unreal.RDSpellKind.CURSE), ("effect", c["text"]),
                           ("mana", float(12 + 6 * slot)), ("cooldown", float(c["cooldown"])), ("duration", float(c["duration"])), ("drop_chance", 0.0),
                           ("tier", tier), ("slot", slot), ("damage", 0.0), ("reach", 1400.0), ("radius", float(c.get("radius", 0))), ("amount", float(c["amount"])),
                           ("count", int(c.get("count", 0))), ("curse_effect", getattr(unreal.RDCurseEffect, c["effect"].upper())), ("only_heroes", ["Warlock"]),
                           ("element", "shadow"), ("icon", s.get_editor_property("icon") if c["name"] in by else "None"), ("use_colors", False)):
                s.set_editor_property(fld, v)
            s.set_editor_property("cast_fx", fx(c["cast"])); s.set_editor_property("impact_fx", fx(c["impact"])); s.set_editor_property("area_fx", fx(c["mark"]))
            for fld, v in (("cast_fx_scale", 1.0), ("impact_fx_scale", 1.0), ("area_fx_scale", 0.8), ("area_every", 0.0)): s.set_editor_property(fld, v)
            if c["name"] in by: spells[by[c["name"]]] = s
            else: by[c["name"]] = len(spells); spells.append(s)
            made.append(c["name"])
        # (every spell's element, by a word of its name; the curses' none for Elemental Ruin's choice)
        ne = 0
        for i, s in enumerate(spells):
            if str(s.name) in made: s.set_editor_property("element", "None"); spells[i] = s; continue
            e = element_of(s.name); s.set_editor_property("element", e or "None"); spells[i] = s; ne += 1 if e else 0
        # (the pictures icons3 made, kept: a curse keeps its own (above); Starfall and Singularity, made again by 910 from Meteor Storm
        # and Void Rift, take theirs again from the level's art when it has them)
        ua = g.get_editor_property("ui_art")
        for i, s in enumerate(spells):
            if str(s.name) in ("Starfall", "Singularity"):
                pn = pic_name(str(s.name))
                if unreal.Name(pn) in ua: s.set_editor_property("icon", pn); spells[i] = s
        g.set_editor_property("spells", spells)
        # (their tomes: Curse of Frailty's tome copied, in the game's tier of its place)
        items = list(g.get_editor_property("items")); names = {str(it.name): i for i, it in enumerate(items)}
        src = items[names["Tome of Curse of Frailty"]]; nt = 0
        for c in L11["curses"]:
            t = copy_struct(unreal.RDItemDef, items[names["Tome of " + c["name"]]] if ("Tome of " + c["name"]) in names else src)
            t.set_editor_property("name", "Tome of " + c["name"]); t.set_editor_property("spell", c["name"]); t.set_editor_property("tiers", [min(int(c["slot"]), TIER_COUNT)])
            if ("Tome of " + c["name"]) in names: items[names["Tome of " + c["name"]]] = t
            else: names[t.get_editor_property("name")] = len(items); items.append(t)
            nt += 1
        g.set_editor_property("items", items)
        return f"looks {looked}; curses {len(made)} (spells {len(spells)}), their tomes {nt}; {ne} spells with an element"
    each_map(GAME_MAPS, spells3, "spells3")

if "slashes3" in STEPS:
    # ("the warrior earns 1 slash per tier ... 30 slashes, and currently there are only 20": ten more, two to each tier, the
    # Weapon Slash pack's trails on her blade, Magic Projectiles' unused hits)
    def slashes3(g):
        sl = list(g.get_editor_property("slashes")); by = {str(s.name): i for i, s in enumerate(sl)}
        items = list(g.get_editor_property("items")); names = {str(it.name): i for i, it in enumerate(items)}
        src_item = {}
        for it in items:
            if it.kind == unreal.RDItemKind.SLASH: src_item.setdefault(int(sl[by[str(it.name)]].tier) if str(it.name) in by else 0, it)
        for e in L11["slashes"]:
            s = copy_struct(unreal.RDSlashDef, sl[by[e["name"]]]) if e["name"] in by else unreal.RDSlashDef()
            for fld, v in (("name", e["name"]), ("tier", int(e["tier"])), ("bonus", float(e["bonus"])), ("type", e["type"]), ("effect", getattr(unreal.RDSlashEffect, e["effect"].upper())),
                           ("amount", float(e.get("amount", 0))), ("seconds", float(e.get("seconds", 0))), ("radius", float(e.get("radius", 0))), ("count", int(e.get("count", 0))),
                           ("text", e["text"]), ("color", unreal.LinearColor(*e["color"], 1.0)), ("trail", True), ("fx_scale", 1.0), ("impact_fx_scale", 1.0)):
                s.set_editor_property(fld, v)
            s.set_editor_property("fx", fx(e["fx"])); s.set_editor_property("impact_fx", fx(e["impact"]))
            if e["name"] in by: sl[by[e["name"]]] = s
            else: by[e["name"]] = len(sl); sl.append(s)
            # (its item, as a slash of its tier is)
            base = src_item.get(int(e["tier"])) or next(iter(src_item.values()))
            t = copy_struct(unreal.RDItemDef, items[names[e["name"]]] if e["name"] in names else base)
            t.set_editor_property("name", e["name"])
            if e["name"] in names: items[names[e["name"]]] = t
            else: names[e["name"]] = len(items); items.append(t)
        g.set_editor_property("slashes", sl); g.set_editor_property("items", items)
        per = {}
        for s in sl: per[int(s.tier)] = per.get(int(s.tier), 0) + 1
        return f"{len(sl)} slashes, by tier {dict(sorted(per.items()))}"
    each_map(GAME_MAPS, slashes3, "slashes3")

if "casts3" in STEPS:
    # ("need new animation and visual for starfall / singularity / soul rend": blender_numpy/spell_casts11.py's three casts, made by
    # tripo_build.py on each caster's own body into SourceArt/spell11_clips/<CH> (the Warlock's arms lengthened as her build's),
    # imported onto her skeleton: the Mage's and the Warlock's FBX (855's way), the Summoner's GLB (her body came in so: 917's note,
    # the FBX misread an 80-bone rig's thighs); her hero's SpellClips on every map)
    CASTERS = {"Mage": "Caster", "Warlock": "DarkCaster", "Summoner": "Summoner4"}
    SPELL_OF = {"Cast_Starfall": "Starfall", "Cast_Singularity": "Singularity", "Cast_SoulRend": "Soul Rend"}
    AD = "/Game/RandomDungeon/Spells11/Anims"
    got_all = {}
    for hero, ch in CASTERS.items():
        d = os.path.join(SA, "spell11_clips", ch)
        times = json.load(open(os.path.join(d, "spell_casts11_times.json")))
        tmp = f"{AD}/_import_{ch}"
        if eal.does_directory_exist(tmp): eal.delete_directory(tmp)
        skel_path = f"/Game/JRPG/Character/SK_JRPG_{ch}_Skeleton" if ch == "Summoner4" else unreal.load_asset(f"/Game/JRPG/Character/SK_JRPG_{ch}").get_editor_property("skeleton").get_path_name().split(".")[0]
        if ch == "Summoner4":
            imported = import_clips(os.path.join(d, f"SK_JRPG_{ch}.glb"), skel_path, tmp, f"PL_{ch}_Spells11", 24)
        else:
            o = unreal.FbxImportUI()
            o.set_editor_property("import_mesh", False); o.set_editor_property("import_as_skeletal", True)
            o.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
            o.set_editor_property("skeleton", unreal.load_asset(skel_path)); o.set_editor_property("import_animations", True)
            o.set_editor_property("import_materials", False); o.set_editor_property("import_textures", False)
            t = unreal.AssetImportTask(); t.filename = os.path.join(d, f"SK_JRPG_{ch}_Clips.fbx"); t.destination_path = tmp; t.automated = True; t.replace_existing = True; t.save = True; t.options = o
            at.import_asset_tasks([t])
            imported = {}
            for q in eal.list_assets(tmp, recursive=True):
                x = unreal.load_asset(q.split(".")[0])
                if isinstance(x, unreal.AnimSequence): imported[x.get_name()] = x
        got = {}
        for clip in SPELL_OF:
            src = next((a for k, a in imported.items() if k.endswith(clip)), None)
            assert src, (ch, clip, sorted(imported))
            dst = f"{AD}/{ch}/AS_{ch}_{clip}"
            if eal.does_asset_exist(dst): eal.delete_asset(dst)
            eal.rename_asset(src.get_path_name().split(".")[0], dst); a = unreal.load_asset(dst)
            a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True); eal.save_loaded_asset(a, False)
            got[clip] = (a, times[clip]["release"], round(a.get_play_length(), 3))
        imported = None
        for q in eal.list_assets(tmp, recursive=True): eal.delete_asset(q.split(".")[0])
        eal.delete_directory(tmp)
        got_all[hero] = got
        REPORT.append(f"casts3 {ch}: " + ", ".join(f"{k} {v[2]} s (release {v[1]})" for k, v in got.items()))

    def casts3(g):
        heroes = list(g.get_editor_property("heroes")); n = 0
        for h in heroes:
            hc = got_all.get(str(h.name))
            if not hc: continue
            m = {}
            for clip, (a, hit, L) in hc.items():
                sc_ = unreal.RDSpellClip(); sc_.set_editor_property("clip", a); sc_.set_editor_property("hit", float(hit)); sc_.set_editor_property("end", float(L))
                m[SPELL_OF[clip]] = sc_
            h.set_editor_property("spell_clips", m); n += len(m)
        g.set_editor_property("heroes", heroes)
        return f"{n} spell clips on the casters"
    each_map(GAME_MAPS, casts3, "casts3")

if "icons3" in STEPS:
    # (the curses' pictures and Starfall's and Singularity's own (they showed Meteor Storm's and Void Rift's), painted by
    # blender_numpy/rdm4_ui_gen.py and cut by rdm4_ui_cut.py --export into <dir>: each spell_<name>.png a UI texture
    # /Game/RandomDungeon/UI/T_RDM4_spell_<name> (877's way), an entry of that name in every map's UIArt, the spell's Icon)
    k_ = STEPS.index("icons3")
    D3 = STEPS[k_ + 1] if len(STEPS) > k_ + 1 else ""
    assert os.path.isdir(D3), "918 icons3: give the folder of the cut pictures (spell_<name>.png)"
    WANT = {n: pic_name(n) for n in [c["name"] for c in L11["curses"]] + ["Starfall", "Singularity"]}
    lost = [p for p in WANT.values() if not os.path.exists(os.path.join(D3, p + ".png"))]
    assert not lost, f"918 icons3: no picture for {lost} in {D3}"
    DEST = "/Game/RandomDungeon/UI"; tasks = []
    for p in WANT.values():
        t = unreal.AssetImportTask()
        t.set_editor_property("filename", os.path.join(D3, p + ".png")); t.set_editor_property("destination_path", DEST)
        t.set_editor_property("destination_name", "T_RDM4_" + p); t.set_editor_property("replace_existing", True)
        t.set_editor_property("automated", True); t.set_editor_property("save", False); tasks.append(t)
    at.import_asset_tasks(tasks)
    TEX = {}
    for p in WANT.values():
        a = unreal.load_asset(f"{DEST}/T_RDM4_{p}")
        assert a, f"918 icons3: {p} was not imported"
        a.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
        a.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
        a.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        a.set_editor_property("never_stream", True); a.set_editor_property("srgb", True)
        a.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP); a.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
        eal.save_loaded_asset(a, False); TEX[p] = a
    def icons3(g):
        ua = g.get_editor_property("ui_art")
        for p, a in TEX.items():
            art = unreal.RDUIArt(); art.set_editor_property("texture", a)
            art.set_editor_property("border", unreal.Vector4(0, 0, 0, 0)); art.set_editor_property("inner", unreal.Vector4(0, 0, 1, 1))
            ua[unreal.Name(p)] = art
        g.set_editor_property("ui_art", ua)
        spells = list(g.get_editor_property("spells")); n = 0
        for i, s in enumerate(spells):
            if str(s.name) in WANT: s.set_editor_property("icon", WANT[str(s.name)]); spells[i] = s; n += 1
        g.set_editor_property("spells", spells)
        return f"{len(TEX)} pictures, {n} spells' icons"
    each_map(GAME_MAPS, icons3, "icons3")
    TEX = None

print("918 " + " | ".join(REPORT))
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
