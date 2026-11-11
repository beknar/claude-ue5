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
The bodies (blender_numpy): the Rogue: martialartist3_retarget.py -- Rogue.glb SourceArt/jrpg_rogue Rogue2.glb --maker
rogue_clips,weapon5_clips --tag Rogue --carry Stab1,Stab2,Stab3,Shoot,RollF,RollB,W5_Bow --own --inplace Walk,Run --noskin
--name Rogue2 --env W5_CLIPS=Bow --env W5_HERO=Rogue, then tripo_build.py on Rogue2_Animated.glb (SK_JRPG_Rogue Rogue 170 -).
The Summoner: summoner5_idle.py (Summoner5.glb -> Summoner5_Idle.glb), summoner5_cloak.py (-> Summoner5_Cloak.glb: the cloak
baked while her walk and run still carry her, so it billows with her speed), then martialartist3_retarget.py --
Summoner4.glb SourceArt/jrpg_summoner4 Summoner5_Cloak.glb --maker summoner4_clips --tag Summoner4 --carry
CastBolt,Summon1,Summon2,Summon3,Summon4,Summon5,Stab1,Stab2,Stab3,Hit_to_body_01 --own --inplace Walk,Run --noskin --name
Summoner5, tripo_build.py on Summoner5_Animated.glb (SK_JRPG_Summoner4 Summoner4 168 -).
In the editor: clean, 600 <CH> glb, 610 / 615 / 620, the armour (the Rogue: 849 heroes, summoner3_armour.py, 851), 913 rider,
rig, then 819 (her character's MoveScale made an override again and her new walk / run speeds baked in).
Args: steps [Hero]"""
import os, sys, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); AL = unreal.AnimationLibrary
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
STEPS = [a for a in sys.argv[1:] if not a.startswith("-")]
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

print("918 " + " | ".join(REPORT))
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
